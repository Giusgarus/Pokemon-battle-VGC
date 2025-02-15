from __future__ import annotations
import numpy as np
from vgc.behaviour import BattlePolicy
from vgc.datatypes.Objects import GameState
from Logic.Logic_Agent import KnowledgeBase
from MCTS.MCTSBattlePolicies import MCTSBattlePolicy
from Combined.Combined_minimax import MiniMaxPlayer
from pyvis.network import Network
from copy import deepcopy
from customtkinter import CTk, CTkButton, CTkRadioButton, CTkLabel
from vgc.engine.PkmBattleEnv import PkmBattleEnv
from vgc.datatypes.Constants import DEFAULT_PKM_N_MOVES, DEFAULT_PARTY_SIZE, TYPE_CHART_MULTIPLIER, DEFAULT_N_ACTIONS
from vgc.datatypes.Types import PkmStat, PkmType, WeatherCondition
import math

class CombinedPolicy(BattlePolicy):
    '''
    Agent which combines MCTS and MiniMax approaches to choose the next action.
    '''

    def __init__(self, player_index: int = 0):
        '''
        Initializes the CombinedPolicy.

        Params:
        - player_index: the index of the player.
        '''
        super().__init__()  # Call the BattlePolicy constructor
        self.kb = KnowledgeBase()  # KnowledgeBase initialization 
        self.n_switches = 0
        self.player_index = player_index

    def set_parameters(self, params: dict):
        '''
        Sets the parameters for the CombinedPolicy.

        Params:
        - params: dictionary containing the parameters.
        '''
        self.params = params

    def get_action(self, g: GameState) -> int:
        '''
        Returns the best action for the current game state using a combination of MCTS and MiniMax.

        Params:
        - g: the current game state.

        Returns:
        The best action ID.
        '''
        # Get the weather information:
        weather = g.weather

        # Get information about my team:
        my_team = g.teams[self.player_index]
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
        opp_team = g.teams[(self.player_index+1)%2]
        opp_active = opp_team.active
        opp_pkm_type = opp_active.type

        # Update the KB facts:
        self.kb.update_facts(my_pkm_type, opp_pkm_type, move_types, move_targets, my_hp, my_max_hp, my_hp_party, my_type_party, weather)

        self.kb.clear_actions_priority()
        self.kb.evaluate()
        actions_priority = self.kb.get_actions_priority()
        # Take the four best actions
        top_4_values = sorted(actions_priority, reverse=True)[:4]
        top_4_indices = [actions_priority.index(value) for value in top_4_values]

        my_pkms_not_fainted = my_team.get_not_fainted()
        opp_pkms_not_fainted = opp_team.get_not_fainted()

        if len(my_pkms_not_fainted) == 0 and len(opp_pkms_not_fainted) == 0:
            # START MINIMAX
            top_2_indices = [top_4_indices[0], top_4_indices[1]] 
            LastPlayer = MiniMaxPlayer(self.player_index, 7)
            return LastPlayer.get_action(g, top_2_indices)
        else:
            # START MCTS
            MCTSPlayer = MCTSBattlePolicy(self.player_index)
            MCTSPlayer.set_parameters(self.params)
            return MCTSPlayer.get_action(g)

