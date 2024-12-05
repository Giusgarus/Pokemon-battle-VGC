#Custom serve, numpy bho vediamo
import numpy as np
from customtkinter import CTk, CTkButton, CTkRadioButton, CTkLabel


from vgc.behaviour import BattlePolicy
from vgc.engine.PkmBattleEnv import PkmBattleEnv
from vgc.datatypes.Constants import DEFAULT_PKM_N_MOVES, DEFAULT_PARTY_SIZE, TYPE_CHART_MULTIPLIER, DEFAULT_N_ACTIONS
from vgc.datatypes.Objects import GameState, PkmTeam, PkmMove
from vgc.datatypes.Types import PkmStat, PkmType, WeatherCondition

class Node:
    def __init__(self, env: PkmBattleEnv, parent: Node = None, actions: list[int] = None):
        self.parent: Node = parent
        self.actions = actions
        self.children: list[Node] = []
        self.env: PkmBattleEnv = env
        self.is_leaf = True
    
    def get_actions(self,current_team) -> list[int]:
        team = self.env.teams[current_team]
        actions_pkm = team.active.moves
        actions_list = []
        for i in range(len(actions_pkm)):
                actions_list.append([actions_pkm[i].move_id])
        return actions_list






class MinMaxBattlePolicy:
    def __init__(self, depth):
        self.depth = depth
    '''
    def min(self, game_state, depth, alpha, beta):
        if depth == 0 or game_state.is_game_over():
            return self.evaluate_game_state(game_state)

        min_eval = float('inf')
        for move in game_state.get_possible_moves():
            new_game_state = game_state.apply_move(move)
            eval = self.max(new_game_state, depth - 1, alpha, beta)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

    def max(self, game_state, depth, alpha, beta):
        if depth == 0 or game_state.is_game_over():
            return self.evaluate_game_state(game_state)

        max_eval = float('-inf')
        for move in game_state.get_possible_moves():
            new_game_state = game_state.apply_move(move)
            eval = self.min(new_game_state, depth - 1, alpha, beta)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
        '''

    def evaluate_game_state(self, game_state: GameState) -> float:
        my_team = game_state.teams[0]
        opp_team = game_state.teams[1]

        my_score = 0
        opp_score = 0

        # Considera la salute residua dei Pokémon
        for pkm in my_team.get_pkm_list():
            my_score += pkm.hp / pkm.max_hp
        for pkm in opp_team.get_pkm_list():
            opp_score += pkm.hp / pkm.max_hp

        # Considera il numero di Pokémon rimasti
        my_score += len([pkm for pkm in my_team.pkm_list if pkm.current_hp > 0])
        opp_score += len([pkm for pkm in opp_team.pkm_list if pkm.current_hp > 0])

        # Considera le condizioni di stato
        for pkm in my_team.get_pkm_list():
            if pkm.status != 0:
                my_score -= 0.5
        for pkm in opp_team.get_pkm_list():
            if pkm.status != 0:
                opp_score -= 0.5

        # Considera il vantaggio di tipo
        my_active_pkm = my_team.active
        opp_active_pkm = opp_team.active
        if my_active_pkm and opp_active_pkm:
            my_score += TYPE_CHART_MULTIPLIER[my_active_pkm.type][opp_active_pkm.type]
            opp_score += TYPE_CHART_MULTIPLIER[opp_active_pkm.type][my_active_pkm.type]

        # Considera le condizioni meteorologiche
        if game_state.weather_condition == WeatherCondition.SUNNY:
            my_score += 0.1
        elif game_state.weather_condition == WeatherCondition.RAINY:
            opp_score += 0.1

        return my_score - opp_score
    

    '''
    def get_best_move(self, game_state):
        best_move = None
        best_value = float('-inf')
        alpha = float('-inf')
        beta = float('inf')

        for move in game_state.get_possible_moves():
            new_game_state = game_state.apply_move(move)
            move_value = self.min(new_game_state, self.depth - 1, alpha, beta)
            if move_value > best_value:
                best_value = move_value
                best_move = move
            alpha = max(alpha, move_value)
            if beta <= alpha:
                break

        return best_move
    '''

class MinMaxPlayer(BattlePolicy):
    def __init__(self, depth):
        super().__init__()
        self.depth = depth
        self.minmax = MinMaxBattlePolicy(depth)

    def choose_move(self, game_state: GameState) -> PkmMove:
        return self.minmax.get_best_move(game_state)