#Custom serve, numpy bho vediamo
import numpy as np
from customtkinter import CTk, CTkButton, CTkRadioButton, CTkLabel


from vgc.behaviour import BattlePolicy
from vgc.engine.PkmBattleEnv import PkmBattleEnv
from vgc.datatypes.Constants import DEFAULT_PKM_N_MOVES, DEFAULT_PARTY_SIZE, TYPE_CHART_MULTIPLIER, DEFAULT_N_ACTIONS
from vgc.datatypes.Objects import GameState, PkmTeam, PkmMove
from vgc.datatypes.Types import PkmStat, PkmType, WeatherCondition

class MinMaxBattlePolicy:
    def __init__(self, depth):
        self.depth = depth

    def min(self, game_state, depth):
        if depth == 0 or game_state.is_game_over():
            return self.evaluate_game_state(game_state)

        min_eval = float('inf')
        for move in game_state.get_possible_moves():
            new_game_state = game_state.apply_move(move)
            eval = self.minmax(new_game_state, depth - 1, True)
            min_eval = min(min_eval, eval)
        return min_eval


    def max(self, game_state, depth):
        if depth == 0 or game_state.is_game_over():
            return self.evaluate_game_state(game_state)

        max_eval = float('-inf')
        for move in game_state.get_possible_moves():
            new_game_state = game_state.apply_move(move)
            eval = self.minmax(new_game_state, depth - 1, False)
            max_eval = max(max_eval, eval)
        return max_eval

    def evaluate_game_state(self, game_state):
        
        pass

    def get_best_move(self, game_state):
        best_move = None
        best_value = float('-inf')
        for move in game_state.get_possible_moves():
            new_game_state = game_state.apply_move(move)
            move_value = self.minmax(new_game_state, self.depth - 1, False)
            if move_value > best_value:
                best_value = move_value
                best_move = move
        return best_move
    

class MinMaxPlayer(BattlePolicy):
    def __init__(self, depth):
        super().__init__()
        self.depth = depth
        self.minmax = MinMaxBattlePolicy(depth)

    def choose_move(self, game_state: GameState) -> PkmMove:
        return self.minmax.get_best_move(game_state)