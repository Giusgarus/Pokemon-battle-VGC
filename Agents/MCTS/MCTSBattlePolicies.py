from __future__ import annotations
import tkinter
from copy import deepcopy
from threading import Thread, Event
from tkinter import CENTER, DISABLED, NORMAL
from types import CellType
from typing import List

import numpy as np
from customtkinter import CTk, CTkButton, CTkRadioButton, CTkLabel

from vgc.behaviour import BattlePolicy
from vgc.engine.PkmBattleEnv import PkmBattleEnv
from vgc.datatypes.Constants import DEFAULT_PKM_N_MOVES, DEFAULT_PARTY_SIZE, TYPE_CHART_MULTIPLIER, DEFAULT_N_ACTIONS
from vgc.datatypes.Objects import GameState, PkmTeam, PkmMove
from vgc.datatypes.Types import PkmStat, PkmType, WeatherCondition




class MCTSNode:
    '''
    Class representing a node in the Monte Carlo Tree.
    '''

    def __init__(self, env: PkmBattleEnv, parent: MCTSNode = None, actions: list[int] = None):
        self.parent: MCTSNode = parent
        self.actions = actions
        self.children: list[MCTSNode] = []
        self.env: PkmBattleEnv = env
        self.utility_playouts = 0
        self.total_playouts = 0
        self.is_leaf = True
    
    def get_actions_combinations(self) -> list[PkmMove,PkmMove]:
        '''
        Generates a list with all the combinations of the actions (with type PkmMove) of the first team with the \
        actions (still pf type PkmMove) of the second one.

        Returns:
        The list with all the combinations.
        '''
        my_team = self.env.teams[0]
        opp_team = self.env.teams[1]
        actions_pkm1 = my_team.active.moves
        actions_pkm2 = opp_team.active.moves
        combinations_list = []
        for i in range(len(actions_pkm1)):
            for j in range(len(actions_pkm2)):
                combinations_list.append([actions_pkm1[i], actions_pkm2[j]])
        return combinations_list
    
    def backpropagation_update(self, winner_value: int) -> None:
        '''
        Updated the fields of the node to reflect the result of the simulation passed as parameter.

        Params:
        - winner_value: the value which indentifies the winner in the terminal state (1 if team 0 wins, 0 otherwise).
        '''
        self.total_playouts += 1
        self.utility_playouts += winner_value
    



class MonteCarloTreeSearch():
    '''
    Class which handles the Monte Carlo Tree search.
    '''

    def __init__(self, env: PkmBattleEnv):
        self.root: MCTSNode = MCTSNode(env)

    def selection(self) -> MCTSNode:
        '''
        Implements the Selection phase, which consists in follow a path (using the Selection policies) in the tree \
        until a leaf is found. In the children's list of the node, is searched the node which maximizes the UCB1 formula, \
        which is used in the "Upper Confidence bound applied to Trees" (UCT) Selection Policy (to choose a path in the tree).

        Return:
        The leaf found at the end of the path.
        '''
        def UCB1(n: MCTSNode):
            '''
            UCB1(n) = \frac{U(n)}{N(n)} + C \cdot \sqrt{\frac{log(N(n.parent))}{N(n)}}
            (copy and paste the formula here: https://latex.codecogs.com/eqneditor/editor.php)
            '''
            exploitation_term = n.utility_playouts/n.total_playouts
            exploration_term = np.sqrt(np.log(n.parent.total_playouts) / n.total_playouts)
            C = 1.5
            return exploitation_term + (C * exploration_term)
        node = self.root
        while not node.is_leaf:
            next_node = node.children[0]
            for n in node.children:
                if UCB1(n) > UCB1(next_node):
                    next_node = n
            node = next_node
        return node

    def expansion(self, node: MCTSNode, n_expansions=1) -> list[MCTSNode]:
        '''
        Implements the Expansion phase used to generate new nodes from the current one.

        Params:
        - node: the node on which perform the expansion.
        - n_expansions: the number of children that should be expanded from the current node.

        Returns:
        The list of the children generated from the current node.
        '''
        # Case of no leaf node
        if not node.is_leaf:
            return None, False
        # Retrieve the actions and generate all the possible actions' combinations
        actions_comb_list: list[list[PkmMove,PkmMove]] = node.get_actions_combinations()
        # Case of number of expansions too high
        if n_expansions > len(actions_comb_list):
            n_expansions = len(actions_comb_list)
        #actions_comb_list = kb.filter_actions(actions_comb_list, cadinality=n_expansions)
        # Generates "n_expansions" children nodes
        indexes = []
        for _ in range(n_expansions):
            # Generate "n_expansions" indexes to identify the actions
            while True:
                index = np.random.randint(0, len(actions_comb_list))
                if index not in indexes:
                    indexes.append(index)
                if len(indexes) == n_expansions:
                    break
            # Case of child to be created
            
            next_env, _, _, _, _ = node.env.step(actions_comb_list[index])
            node.children.append(
                MCTSNode(
                    env=next_env[0],
                    parent=node,
                    action=actions_comb_list[index][0]
                )
            )
        node.is_leaf = False
        return node.children

    def simulation(self, leafs: list[MCTSNode]) -> None:
        '''
        Implements the Playout's simulation starting from the newly generated nodes to some nodes with terminal state.

        Params:
        - leafs: list of nodes from which the simulation starts.

        Returns:
        The list of nodes having terminal state.
        '''
        def get_next_node(n: MCTSNode) -> MCTSNode:
            '''
            Implements the Playout policy used by the simulation to choose the next node from the current one. In this case the move \
            is randomly generated.\n
            Return:
            The next node chosen for a single step of the simulation.
            '''
            actions_comb_list = n.get_actions_combinations()
            index = np.random.randint(0, len(actions_comb_list))
            next_env, _, _, _, _ = n.env.step(actions_comb_list[index])
            n.children.append(
                MCTSNode(
                    env=next_env[0],
                    parent=n,
                    action=actions_comb_list[index]
                )
            )
            return n.children[0]
        # For each leaf perform a random simulation
        return_nodes = []
        for node in leafs:
            while True:
                node = get_next_node(node)
                # Case of termination node
                if node.env.teams[0].fainted() or node.env.teams[1].fainted():
                    return_nodes.append(node)
                    break
        return return_nodes

    def backpropagation(self, nodes: list[MCTSNode]) -> None:
        '''
        Implements the Backpropagation phase, which updates the evaluation of the nodes from the starting one to the root.

        Params:
        - nodes: the nodes from which the backpropagation starts.
        '''
        # Performs a backpropagation for each termination node
        for node in nodes:
            winner = node.env.winner
            # Backpropagation pass
            while True:
                # Case of root node
                if node.parent is None:
                    node.backpropagation_update(winner)
                    break
                # Case of node generated by the simulation
                if node.is_leaf and node.parent.is_leaf:
                    parent_node = node.parent
                    del node
                    node = parent_node
                    continue
                # Update of the node's values
                node.backpropagation_update(winner)
                node = node.parent





class MCTSPlayer(BattlePolicy):
    '''
    Agent which uses the Monte Carlo Tree Search (MCTS) approach as policy to choose the actions.
    '''

    def __init__(self, name: str):
        super().__init__()
        self.name = name
    
    def __str__(self):
        print(self.name)

    def get_action(self, state: GameState) -> int:
        '''
        Implements the Pure Monte Carlo Tree Search (MCTS) algorithm.

        Params:
        - n: number of simulations to perform.

        Returns:
        The node with higher utility value computed by simulating moves with the MCTS algorithm.
        '''
        # Initializations
        N = 100
        state_copy: GameState = deepcopy(state)
        tree = MonteCarloTreeSearch(state_copy)
        # Perform N simulations
        for _ in range(N):
            leaf = tree.selection()
            children = tree.expansion(leaf, n_expansions=3)
            terminal_nodes = tree.simulation(children)
            tree.backpropagation(terminal_nodes)
        # Case of no possible moves
        if tree.root.children == []:
            return None
        # Choose the move
        best_node = tree.root.children[0]
        for child in tree.root.children:
            best_node_value = best_node.utility_playouts / best_node.total_playouts
            this_node_value = child.utility_playouts / child.total_playouts
            if this_node_value > best_node_value:
                best_node = child
        return best_node.actions








