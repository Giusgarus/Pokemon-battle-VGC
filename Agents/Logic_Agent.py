from vgc.behaviour import BattlePolicy
from vgc.datatypes.Constants import TYPE_CHART_MULTIPLIER
from vgc.datatypes.Objects import GameState, Weather, PkmMove, Pkm, PkmTeam
from vgc.datatypes.Types import PkmType, WeatherCondition

import math

class LogicPolicy(BattlePolicy):

  def __init__(self):
        super().__init__()  # Call the BattlePolicy constructor
        self.kb = KnowledgeBase()  # KnowledgeBase initialization 

  def get_action(self, g: GameState) -> int:

        # Get the weather information:
        weather = g.weather

        # Get information about my team:
        my_team = g.teams[0]
        my_active = my_team.active
        my_hp = my_active.hp
        my_max_hp = my_active.max_hp
        my_pkm_type = my_active.type
        my_active_moves = my_active.moves
        move_types = [my_active_moves[0].type, my_active_moves[1].type, my_active_moves[2].type, my_active_moves[3].type]
        move_targets = [my_active_moves[0].target, my_active_moves[1].target, my_active_moves[2].target, my_active_moves[3].target]
        my_switch = my_team.party
        my_hp_party = [my_switch[0].hp, my_switch[1].hp]
        my_type_party = [my_switch[0].type, my_switch[1].type]

        
        # Get information about opponent team:
        opp_team = g.teams[1]
        opp_active = opp_team.active
        opp_pkm_type = opp_active.type

        # update the KB facts:
        self.kb.update_facts(my_pkm_type, opp_pkm_type, move_types, move_targets, my_hp, my_max_hp, my_hp_party, my_type_party, weather)

        self.kb.clear_actions_priority()
        self.kb.evaluate()
        actions_priority = self.kb.get_actions_priority()
        return actions_priority.index(max(actions_priority))


class KnowledgeBase:

    # ------------------- KB INITIALIZATION -----------------------
    def __init__(self):
        self.facts = {}  # facts memorizated in dict
        self.rules = [
            self.rule_super_effective,
            self.rule_stab,
            self.rule_weather,
            self.rule_low_hp_switch,
            self.one_pokemon_not_switch,
            self.rule_notsupereffective_switch,
            self.rule_offensive_moves
        ]  # List of rules 
        self.actions_priority = [ 0, 0, 0, 0, 0, 0 ] # List of actions priority

    def clear_actions_priority(self):
        """
        Cleans up the action priority list.
        """

        for i in range(len(self.actions_priority)):
            self.actions_priority[i] = 0
        return None


    # ------------------ RETURN THE RESULT OF THE INFERENCE ENGINE ---------------------
    def get_actions_priority(self):
        """
        Action priority returns.
        """

        return self.actions_priority

    # ------------------ UPDATE CURRENT FACTS -------------------
    def update_facts(self, my_pkm_type: PkmType, opp_pkm_type: PkmType, move_types List[PkmType], 
                      move_targets: List[Int], my_hp: Float, my_max_hp: Float, my_hp_party: List[Float], 
                      my_type_party: List[PkmType], weather: Weather):
        """
        Update facts with current data.
        """

        self.facts = {
            "my_pkm_type": my_pkm_type,
            "opp_pkm_type": opp_pkm_type,
            "move_types": move_types,
            "move_targets": move_targets,
            "my_hp": my_hp,
            "my_max_hp": my_max_hp,
            "my_hp_party": my_hp_party,
            "my_type_party": my_type_party,
            "weather": weather
        }


    # ------------ KB RULES: (Defined as class methods) -----------------
    def rule_super_effective(self, facts: Dict):
        """
        If there is a super effective move, increase priority +2, If there is a non-super effective move, decrease priority -2.
        """
        opp_type = facts["opp_pkm_type"]
        move_types = facts["move_types"]

        for i, move_type in enumerate(move_types):
            multiplier = TYPE_CHART_MULTIPLIER[move_type][opp_type]
            if multiplier > 1:  # Supereffective
                self.actions_priority[i] += 2
            if multiplier < 1: # Not Supereffective
                self.actions_priority[i] -= 2

        return None

    def rule_stab(self, facts: Dict):
        """
        If there is a stab move, increase priority +1.
        """
        my_type = facts["my_pkm_type"]
        move_types = facts["move_types"]

        for i, move_type in enumerate(move_types):
            if my_type == move_type:  # Stab move
                self.actions_priority[i] += 1

        return None

    def rule_weather(self, facts: Dict):
        """
        If there is a move suitable for the weather, increase priority +1, if it is not suitable, decrease by -1.
        """
        weather = facts["weather"]
        move_types = facts["move_types"]

        if weather.condition == 0:
            return None
        
        for i, move_type in enumerate(move_types):
            if weather.condition == 1: # SUNNY
                if move_type == 1: # mossa fuoco
                    self.actions_priority[i] += 1
                if move_type == 2: # mossa acqua 
                    self.actions_priority[i] -= 1
            if weather.condition == 2: # RAIN
                if move_type == 2: # mossa acqua
                    self.actions_priority[i] += 1
                if move_type == 1: # mossa fuoco
                    self.actions_priority[i] -= 1
            if weather.condition == 3: # SANDSTORM
                if move_type == 12: # mossa roccia
                    self.actions_priority[i] += 1
            if weather.condition == 4: # HAIL
                if move_type == 5: # mossa ghiaccio
                    self.actions_priority[i] += 1

        return None

    def rule_low_hp_switch(self, facts: Dict):
        """
        If we have less than 50% life, priority is given to a +1 switch, if we have less than 25% life, +2.
        """

        my_hp = facts["my_hp"]
        my_max_hp = facts["my_max_hp"]
        my_hp_party = facts["my_hp_party"]

        half_hp = math.ceil(my_max_hp / 2)
        quarter_hp = math.ceil(my_max_hp / 4)

        if my_hp <= quarter_hp:
            index_switch = my_hp_party.index(max(my_hp_party))
            if index_switch == 0:
                self.actions_priority[4] += 2
            else:
                self.actions_priority[5] += 2
        elif my_hp <= half_hp:
            index_switch = my_hp_party.index(max(my_hp_party))
            if index_switch == 0:
                self.actions_priority[4] += 1
            else:
                self.actions_priority[5] += 1

        return None

    def one_pokemon_not_switch(self, facts: Dict):
        """
        If we have one pokemon active not switch in every case.
        """

        my_hp_party = facts["my_hp_party"]

        if my_hp_party[0] <=0 and my_hp_party[1] <= 0:
            self.actions_priority[4] -= 10
            self.actions_priority[5] -= 10

        return None

    def rule_notsupereffective_switch(self, facts: Dict):
        """
        If the opposing Pokemon is a super effective type,
        priority is given to the +2 switch with the Benched Pokemon with the highest type advantage.
        """

        opp_type = facts["opp_pkm_type"]
        my_type = facts["my_pkm_type"]
        my_type_party = facts["my_type_party"]

        multiplier = TYPE_CHART_MULTIPLIER[opp_type][my_type]
        if multiplier > 1: # Opponent pokemon supereffective
            multiplier_switch1 = TYPE_CHART_MULTIPLIER[opp_type][my_type_party[0]]
            multiplier_switch2 = TYPE_CHART_MULTIPLIER[opp_type][my_type_party[1]]
            if multiplier_switch2 > multiplier_switch1: # second pokemon have the highest type advantage
                self.actions_priority[5] += 2 
            else:
                self.actions_priority[4] += 2

        return None

    def rule_offensive_moves(self, facts: Dict):
        """
        Priority given to offensive moves, so a +1 if they damage the enemy.
        """

        move_targets = facts["move_targets"]

        for i, move_target in enumerate(move_targets):
            if move_target == 1:  # mossa offensiva
                self.actions_priority[i] += 1

        return None



    # ------------- THE INFERENCE ENGINE -------------------
    def evaluate(self):
        """
        Evaluate the rules and determine the best action.
        """

        for rule in self.rules:
            rule(self.facts)

        return None
