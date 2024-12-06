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

    def __init__(self, id: int, env: PkmBattleEnv, parent: MCTSNode = None, actions: list[int] = None, is_simulated=False):
        self.id = id
        self.env: PkmBattleEnv = env
        self.parent: MCTSNode = parent
        self.actions = actions
        self.children: list[MCTSNode] = []
        self.utility_playouts = 0
        self.total_playouts = 0
        self.is_leaf = True
        self.is_simulated = is_simulated
    
    def get_actions_combinations(self) -> list[list[int,int]]:
        '''
        Generates a list with all the combinations of the actions of the first team as type int (move_id field) with the \
        actions of the second one.

        Returns:
        The list with all the combinations (= the index of the move in the list of the 4 moves of the pkm).
        '''
        my_team = self.env.teams[0]
        opp_team = self.env.teams[1]
        actions_pkm1 = my_team.active.moves
        actions_pkm2 = opp_team.active.moves
        combinations_list = []
        for i in range(len(actions_pkm1)):
            for j in range(len(actions_pkm2)):
                combinations_list.append([i,j])
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

    def __init__(self, player_index: int, env: PkmBattleEnv, enable_print: bool):
        self.node_counter = 1
        self.root: MCTSNode = MCTSNode(id=self.node_counter, env=env)
        self.player_index = player_index
        self.enable_print = enable_print

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
            next_node = node.children[0] # first initialization
            for n in node.children:
                if UCB1(n) > UCB1(next_node):
                    next_node = n
            node = next_node
        if self.enable_print:
            print(f'Selected: {node.id}')
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
        actions_comb_list: list[list[int,int]] = node.get_actions_combinations()
        # Case of number of expansions too high
        max_branching_factor = len(actions_comb_list)
        if n_expansions > max_branching_factor:
            n_expansions = max_branching_factor
        #actions_comb_list = kb.filter_actions(actions_comb_list, cadinality=n_expansions)
        # Generates "n_expansions" children nodes
        rand_gen_indexes = []
        while len(rand_gen_indexes) != n_expansions:
            index = np.random.randint(0,max_branching_factor)
            if index not in rand_gen_indexes:
                rand_gen_indexes.append(index)
                next_env, _, _, _, _ = node.env.step(actions_comb_list[index])
                self.node_counter += 1
                node.children.append(
                    MCTSNode(
                        id=self.node_counter,
                        env=next_env[self.player_index],
                        parent=node,
                        actions=actions_comb_list[index]
                    )
                )
        node.is_leaf = False
        if self.enable_print:
            print(f'Expanded {n_expansions} nodes: {node.id} -> {[n.id for n in node.children]}')
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
            self.node_counter += 1
            n.children.append(
                MCTSNode(
                    id=self.node_counter,
                    env=next_env[self.player_index],
                    parent=n,
                    actions=actions_comb_list[index],
                    is_simulated=True
                )
            )
            return n.children[0]
        # For each leaf perform a random simulation
        return_nodes: list[MCTSNode] = []
        for node in leafs:
            while True:
                node = get_next_node(node)
                # Case of termination node
                if node.env.winner != -1:
                    return_nodes.append(node)
                    break
        # Case of print
        if self.enable_print:
            print(f'Simulation phase: returned nodes {[n.id for n in return_nodes]} respectively won by {[n.env.winner for n in return_nodes]}')
        return return_nodes

    def backpropagation(self, nodes: list[MCTSNode]) -> None:
        '''
        Implements the Backpropagation phase, which updates the evaluation of the nodes from the starting one to the root.

        Params:
        - nodes: the nodes from which the backpropagation starts.
        '''
        # Case of print
        if self.enable_print:
            print('Backpropagation phase')
        # Performs a backpropagation for each termination node
        for node in nodes:
            update_value = 1 if self.player_index == node.env.winner else 0
            backprop_nodes: list[MCTSNode] = []
            # Backpropagation pass
            while True:
                # Case of root node
                if node.parent is None:
                    node.backpropagation_update(update_value)
                    backprop_nodes.append(node)
                    break
                # Case of node generated by the simulation
                if node.is_simulated:
                    parent_node = node.parent
                    parent_node.children.remove(node)
                    del node
                    node = parent_node
                    continue
                # Update of the node's values
                node.backpropagation_update(update_value)
                backprop_nodes.append(node)
                node = node.parent
            # Case of print
            if self.enable_print:
                path_utility_list = [str(str(n.id)+':'+str(n.utility_playouts)+'/'+str(n.total_playouts)) for n in backprop_nodes]
                print(f'Backpropagated {len(backprop_nodes)} nodes: {path_utility_list}')




class MCTSPlayer(BattlePolicy):
    '''
    Agent which uses the Monte Carlo Tree Search (MCTS) approach as policy to choose the actions.
    '''

    def __init__(self, name: str, player_index: int, enable_print=False):
        super().__init__()
        self.name = name
        self.player_index = player_index
        self.enable_print = enable_print
    
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
        tree = MonteCarloTreeSearch(
            player_index=self.player_index,
            env=state_copy,
            enable_print=self.enable_print
        )
        if self.enable_print:
            print(f'Simulation phase for player {self.player_index}')
        # Perform N simulations
        for i in range(N):
            if self.enable_print:
                print(f'Player: {self.player_index}\nSimulation: {i+1}/{N}')
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
        return best_node.actions[0]








