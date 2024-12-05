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

    def evaluate_game_state(self, game_state):
        # Implementa la tua logica di valutazione qui
        pass

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
    

class MinMaxPlayer(BattlePolicy):
    def __init__(self, depth):
        super().__init__()
        self.depth = depth
        self.minmax = MinMaxBattlePolicy(depth)

    def choose_move(self, game_state: GameState) -> PkmMove:
        return self.minmax.get_best_move(game_state)