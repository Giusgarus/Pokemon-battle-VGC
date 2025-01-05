import numpy as np
from vgc.behaviour import BattlePolicy
from vgc.datatypes.Objects import GameState

class RandomPolicy(BattlePolicy):
    '''
    Agent which uses a random policy to choose the next action.
    '''

    def __init__(self, player_index=0):
        '''
        Initializes the RandomPolicy.

        Params:
        - player_index: the index of the player.
        '''
        self.player_index = player_index
        self.n_switches = 0

    def get_action(self, g: GameState) -> int:
        '''
        Returns a random action for the current game state.

        Params:
        - g: the current game state.

        Returns:
        The random action ID.
        '''
        # Get information about my team: (active Pokémon and its moves, Pokémon to switch with)
        my_team = g.teams[self.player_index]
        my_active = my_team.active
        my_active_moves = my_active.moves
        my_switch = my_team.party
        my_actions = my_active_moves + my_switch

        # Choose a random action among the 4 moves of the active Pokémon and the two switches with the Pokémon on the bench
        n_moves = len(my_active_moves) 
        n_switch = len(my_switch)
        n_actions = len(my_actions)
        switch_probability = 0.15   # constant probability of a switch compared to using a move

        # Define a probability distribution over all possible actions
        pi = ([(1. - switch_probability) / n_moves] * n_moves) + ([switch_probability / n_switch] * n_switch)

        # Randomly choose an action based on the defined probability distribution
        random_choice = np.random.choice(n_actions, p=pi)
        if random_choice > 3:
            self.n_switches += 1
        return random_choice
