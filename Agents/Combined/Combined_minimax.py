from copy import deepcopy
import numpy as np
from customtkinter import CTk, CTkButton, CTkRadioButton, CTkLabel
from typing import Tuple

from vgc.behaviour import BattlePolicy
from vgc.engine.PkmBattleEnv import PkmBattleEnv
from vgc.datatypes.Constants import DEFAULT_PKM_N_MOVES, DEFAULT_PARTY_SIZE, TYPE_CHART_MULTIPLIER, DEFAULT_N_ACTIONS
from vgc.datatypes.Objects import GameState, PkmTeam, PkmMove
from vgc.datatypes.Types import PkmStat, PkmType, WeatherCondition
from vgc.competition.StandardPkmMoves import Struggle


def damage_prediction(move_type: PkmType, pkm_type: PkmType, move_power: float, opp_pkm_type: PkmType,
                    attack_stage: int, defense_stage: int, weather: WeatherCondition) -> float:
    '''
    Predicts the damage of a move based on various factors.

    Params:
    - move_type: the type of the move.
    - pkm_type: the type of the Pokémon using the move.
    - move_power: the power of the move.
    - opp_pkm_type: the type of the opponent Pokémon.
    - attack_stage: the attack stage of the Pokémon.
    - defense_stage: the defense stage of the opponent Pokémon.
    - weather: the current weather condition.

    Returns:
    The predicted damage.
    '''
    stab = 1.5 if move_type == pkm_type else 1.0
    if (move_type == PkmType.WATER and weather == WeatherCondition.RAIN) or (
            move_type == PkmType.FIRE and weather == WeatherCondition.SUNNY):
        weather_modifier = 1.5
    elif (move_type == PkmType.WATER and weather == WeatherCondition.SUNNY) or (
            move_type == PkmType.FIRE and weather == WeatherCondition.RAIN):
        weather_modifier = 0.5
    else:
        weather_modifier = 1.0

    stage_level = attack_stage - defense_stage
    if stage_level >= 0:
        stage_modifier = (stage_level + 2.0) / 2
    else:
        stage_modifier = 2.0 / (abs(stage_level) + 2.0)

    damage = TYPE_CHART_MULTIPLIER[move_type][opp_pkm_type] * stab * weather_modifier * stage_modifier * move_power
    return damage


def simulate_move(game: GameState, move_id: int, player: bool) -> GameState:
    '''
    Simulates a move and returns the new game state.

    Params:
    - game: the current game state.
    - move_id: the ID of the move to simulate.
    - player: the player making the move (0 or 1).

    Returns:
    The new game state after the move.
    '''
    new_g = deepcopy(game)

    if player != 0 and player != 1:
        raise ValueError('Player must be 0 or 1')

    opp_idx = 1 if player == 0 else 0

    my_team = game.teams[player]
    opp_team = game.teams[opp_idx]

    my_active = my_team.active
    opp_active = opp_team.active

    if move_id < DEFAULT_PKM_N_MOVES:
        move = my_active.moves[move_id]
        if move.weather !=0 :
            new_g.weather.condition = move.weather
        elif move.recover !=0 :
            my_active.hp = min(my_active.hp + move.recover, my_active.max_hp)
        else:
            damage = damage_prediction(move.type, my_active.type, move.power, opp_active.type,
                                    my_team.stage[PkmStat.ATTACK], opp_team.stage[PkmStat.DEFENSE], new_g.weather.condition)
            opp_active.hp = max(0, opp_active.hp - damage)
    else:
        switch_id = move_id - DEFAULT_PKM_N_MOVES
        if switch_id < len(my_team.party):
            my_team.active, my_team.party[switch_id] = my_team.party[switch_id], my_team.active

    return new_g


def get_residual_hp(game: GameState, player: bool) -> Tuple[int, int]:
    '''
    Calculates the total residual HP for both teams.

    Params:
    - game: the current game state.
    - player: the player index (0 or 1).

    Returns:
    A tuple containing the total residual HP for both teams.
    '''
    my_team = game.teams[0]
    opp_team = game.teams[1]
    my_tot_hp=0
    for pkm in my_team.get_pkm_list():
        my_tot_hp += pkm.hp

    opp_tot_hp=0
    for pkm in opp_team.get_pkm_list():
        opp_tot_hp += pkm.hp
    return my_tot_hp, opp_tot_hp


class MiniMaxBattlePolicy:
    
    def __init__(self, depth:int, player: bool, life_value: int = 500):
        '''
        Initializes the MiniMaxBattlePolicy.

        Params:
        - depth: the depth of the minimax search.
        - player: the player index (0 or 1).
        - life_value: the value of life points.
        '''
        self.player = player
        self.depth = depth
        self.life_value = life_value

    def evaluate(self, game: GameState, player: bool) -> float:
        '''
        Evaluates the game state and returns a score.

        Params:
        - game: the current game state.
        - player: the player index (0 or 1).

        Returns:
        The evaluation score.
        '''
        if player != 0 and player != 1:
            raise ValueError('Player must be 0 or 1')

        opp_idx = 1 if player == 0 else 0

        my_team = game.teams[player]
        opp_team = game.teams[opp_idx]

        my_score = 0
        opp_score = 0

        # Consider win conditions
        my_tot_hp, opp_tot_hp = get_residual_hp(game, player)

        if(opp_tot_hp == 0):
            my_score += 2000
        elif(my_tot_hp == 0):
            opp_score += 2000

        # Consider residual health of Pokémon
        for pkm in my_team.get_pkm_list():
            my_score += self.life_value*(pkm.hp / pkm.max_hp)
        for pkm in opp_team.get_pkm_list():
            opp_score += self.life_value*(pkm.hp / pkm.max_hp)

        # Consider the number of remaining Pokémon
        my_score += 500*len([pkm for pkm in my_team.get_pkm_list() if pkm.hp > 0])
        opp_score += 500*len([pkm for pkm in opp_team.get_pkm_list() if pkm.hp > 0])

        # Consider status conditions
        for pkm in my_team.get_pkm_list():
            if pkm.status == 1:
                my_score -= 100
            elif pkm.status == 2:
                my_score -= 150
            elif pkm.status == 3:
                my_score -= 180
            elif pkm.status == 4:
                my_score -= 200
            elif pkm.status == 5:
                my_score -= 200
            elif pkm.status == 6:
                my_score -= 100
        for pkm in opp_team.get_pkm_list():
            if pkm.status == 1:
                opp_score -= 100
            elif pkm.status == 2:
                opp_score -= 150
            elif pkm.status == 3:
                opp_score -= 180
            elif pkm.status == 4:
                opp_score -= 200
            elif pkm.status == 5:
                opp_score -= 200
            elif pkm.status == 6:
                opp_score -= 100

        # Consider type advantage
        my_active_pkm = my_team.active
        opp_active_pkm = opp_team.active
        if my_active_pkm and opp_active_pkm:
            if TYPE_CHART_MULTIPLIER[my_active_pkm.type][opp_active_pkm.type] ==2.:
                my_score += 200
            elif TYPE_CHART_MULTIPLIER[my_active_pkm.type][opp_active_pkm.type] == .5:
                my_score -= 100

            if TYPE_CHART_MULTIPLIER[opp_active_pkm.type][my_active_pkm.type] ==2.:
                opp_score += 200
            elif TYPE_CHART_MULTIPLIER[opp_active_pkm.type][my_active_pkm.type] == .5:
                opp_score -= 100

        # Consider move advantage based on weather conditions for the team
        weather = game.weather
        for i,move in enumerate(my_team.active.moves):
            move_type = move.type
            if weather.condition == 1: # SUNNY
                if move_type == 1: # fire move
                    my_score += 150
                elif move_type == 2: # water move
                    my_score -= 150
            elif weather.condition == 2: # RAIN
                if move_type == 2: # fire move
                    my_score += 150
                elif move_type == 1: # water move
                    my_score -= 150
        # Consider move advantage based on weather conditions for the opponent team
        for i,move in enumerate(opp_team.active.moves):
            move_type = move.type
            if weather.condition == 1: # SUNNY
                if move_type == 1: # fire move
                    opp_score += 150
                elif move_type == 2: # water move
                    opp_score -= 150
            elif weather.condition == 2: # RAIN
                if move_type == 2: # fire move
                    opp_score += 150
                elif move_type == 1: # water move
                    opp_score -= 150
        # Consider type advantage based on weather conditions
        if weather.condition == 3: # SANDSTORM
            if my_team.active.type == 12: # rock Pokémon
                my_score += 150
            else:
                my_score -= 150
            if opp_team.active.type == 12:
                opp_score += 150
            else:
                opp_score -= 150
        elif weather.condition == 4: # HAIL
            if my_team.active.type == 5: # ice Pokémon
                my_score += 150
            else:
                my_score -= 150
            if opp_team.active.type == 5:
                opp_score += 150
            else:
                opp_score -= 150

        return my_score - opp_score

    def mini(self, game: GameState, depth: int, alpha, beta) -> float:
        '''
        Implements the minimization step of the minimax algorithm.

        Params:
        - game: the current game state.
        - depth: the current depth of the search.
        - alpha: the alpha value for alpha-beta pruning.
        - beta: the beta value for alpha-beta pruning.

        Returns:
        The minimum evaluation score.
        '''
        residual_hp = get_residual_hp(game, 0)
        if depth == 0 or residual_hp[1] ==0 or residual_hp[0] == 0:
            return self.evaluate(game, self.player)
        else :
            min_eval = float('inf')
            idx = 0 if self.player == 1 else 1
            for move in range(DEFAULT_PKM_N_MOVES):
                new_game_state = simulate_move(game, move, idx)
                eval = self.max(new_game_state, depth - 1, alpha, beta)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                # Check condition
                if eval <= alpha:
                    break
            return min_eval + self.evaluate(game, self.player)

    def max(self, game: GameState, depth: int, alpha, beta) -> float:
        '''
        Implements the maximization step of the minimax algorithm.

        Params:
        - game: the current game state.
        - depth: the current depth of the search.
        - alpha: the alpha value for alpha-beta pruning.
        - beta: the beta value for alpha-beta pruning.

        Returns:
        The maximum evaluation score.
        '''
        residual_hp = get_residual_hp(game, 0)
        if depth == 0 or residual_hp[1] ==0 or residual_hp[0] == 0:
            return self.evaluate(game, self.player)
        else :
            max_eval = float('-inf')
            idx = 0 if self.player == 0 else 1
            for move in range(DEFAULT_PKM_N_MOVES):
                new_game_state = simulate_move(game, move, idx)
                eval = self.mini(new_game_state, depth - 1, alpha, beta)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                # Check condition
                if beta <= eval:
                    break
            return max_eval +self.evaluate(game, self.player)

    def minimax(self, game: GameState, top2moves: list) -> int:
        '''
        Implements the minimax algorithm to find the best move.

        Params:
        - game: the current game state.
        - top2moves: list of top 2 moves to consider.

        Returns:
        The best move ID.
        '''
        best_move = None
        best_value = float('-inf')
        idx = 0 if self.player == 0 else 1
        for move in top2moves:
            new_game_state = simulate_move(game, move, idx)
            move_value = self.mini(new_game_state, self.depth - 1, float('-inf'), float('inf'))
            if move_value > best_value:
                best_value = move_value
                best_move = move
        return best_move


class MiniMaxPlayer(BattlePolicy):

    def __init__(self, player_index = 0, depth: int = 5):
        '''
        Initializes the MiniMaxPlayer.

        Params:
        - player_index: the index of the player.
        - depth: the depth of the minimax search.
        '''
        self.player_index = player_index
        self.depth = depth
        self.n_switches = 0
        super().__init__()

    def get_action(self, game: GameState,  top2moves: list) -> int:
        '''
        Returns the best action for the current game state.

        Params:
        - game: the current game state.
        - top2moves: list of top 2 moves to consider.

        Returns:
        The best action ID.
        '''
        policy = MiniMaxBattlePolicy(self.depth,self.player_index, 300)
        best_move = policy.minimax(game, top2moves)
        if best_move in [4,5]:
            self.n_switches += 1
        return best_move