from __future__ import annotations
from copy import deepcopy
import numpy as np
from vgc.behaviour import BattlePolicy
from vgc.engine.PkmBattleEnv import PkmBattleEnv
from vgc.datatypes.Objects import GameState, PkmTeam, PkmMove
from Logic_Agent import KnowledgeBase
from pyvis.network import Network



def get_pkm_move_name(node: MCTSNode, action: int, player_index: int):
    if action > 3:
        move_name = f'Switch with {action-4}'
    else:
        moves: list[PkmMove] = node.env.teams[player_index].active.moves
        move_name = moves[action].name
    return move_name



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
        self.utility_playouts: float = 0
        self.total_playouts: int = 0
        self.is_leaf = True
        self.is_simulated = is_simulated
    
    def get_top_actions(self, my_team: PkmTeam, opp_team: PkmTeam, number_of_my_top_moves=1, number_of_opp_top_moves=1) -> list[list[int,int]]:
        '''
        Generates a list with all the combinations of the actions of the first team, as the index of the move, \
        with the actions of the second one.

        Returns:
        The list with all the combinations (= the index of the move in the list of the 4 moves of the pkm).

        Params:
        - my_team: is the PkmTeam object of which are considered the top "number_of_my_top_moves" moves.
        - opp_team: is the PkmTeam object of which are considered the top "number_of_opp_top_moves" moves.
        - number_of_my_top_moves: is the number of moves which are considered for "my_team".
        - number_of_opp_top_moves: is the number of moves which are considered for "opp_team".
        '''
        my_pkm = my_team.active
        opp_pkm = opp_team.active
        kb = KnowledgeBase()
        # Retrieve the best moves for me
        kb.update_facts(
            my_pkm_type=my_pkm.type,
            opp_pkm_type=opp_pkm.type,
            move_types=[my_pkm.moves[0].type, my_pkm.moves[1].type],
            move_targets=[opp_pkm.moves[0].type, opp_pkm.moves[1].type,],
            my_hp=my_pkm.hp,
            my_max_hp=my_pkm.max_hp,
            my_hp_party=[my_team.party[0].hp, my_team.party[1].hp],
            my_type_party=[my_team.party[0].type, my_team.party[1].type],
            weather=self.env.weather
        )
        kb.clear_actions_priority()
        kb.evaluate()
        actions_priority = kb.get_actions_priority()
        my_top_actions_priority = sorted(
            [(a,v) for a,v in enumerate(actions_priority)],
            key=lambda x: x[1],
            reverse=True
        )
        my_moves_with_higher_priority = [a for a,v in my_top_actions_priority]
        my_moves_with_higher_priority = my_moves_with_higher_priority[:number_of_my_top_moves]
        # Retrieve the best moves for the opponent
        kb.update_facts(
            my_pkm_type=opp_pkm.type,
            opp_pkm_type=my_pkm.type,
            move_types=[opp_pkm.moves[0].type, opp_pkm.moves[1].type],
            move_targets=[my_pkm.moves[0].type, my_pkm.moves[1].type],
            my_hp=opp_pkm.hp,
            my_max_hp=opp_pkm.max_hp,
            my_hp_party=[opp_team.party[0].hp, opp_team.party[1].hp],
            my_type_party=[opp_team.party[0].type, opp_team.party[1].type],
            weather=self.env.weather
        )
        kb.clear_actions_priority()
        kb.evaluate()
        actions_priority = kb.get_actions_priority()
        opp_top_actions_priority = sorted(
            [(a,v) for a,v in enumerate(actions_priority)],
            key=lambda x: x[1],
            reverse=True
        )
        opp_moves_with_higher_priority = [a for a,v in opp_top_actions_priority]
        opp_moves_with_higher_priority = opp_moves_with_higher_priority[:number_of_opp_top_moves]
        # Compute all the combinations of my best moves and the opponent best moves
        combinations_list = []
        for i in my_moves_with_higher_priority:
            for j in opp_moves_with_higher_priority:
                combinations_list.append([i,j])
        return combinations_list

    def get_all_actions_combinations(self):
        '''
        Generates a list with all the combinations of the actions of the first team with the actions of the second team.
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
    
    def backpropagation_update(self, winner_value: int, player_index: int) -> None:
        '''
        Updated the fields of the node to reflect the result of the simulation passed as parameter.

        Params:
        - winner_value: the value which indentifies the winner in the terminal state (1 if team 0 wins, 0 otherwise).
        '''
        if winner_value == 0:
            hp_residue_percentage = 0
        else:
            hp_residue = sum([pkm.hp for pkm in self.env.teams[player_index].party] + [self.env.teams[player_index].active.hp])
            max_hp = sum([pkm.max_hp for pkm in self.env.teams[player_index].party] + [self.env.teams[player_index].active.max_hp])
            hp_residue_percentage = hp_residue / max_hp
        winrate_weight = 1
        hp_residue_weight = 1 - winrate_weight
        self.utility_playouts += round(number=float((winner_value * winrate_weight) + (hp_residue_percentage * hp_residue_weight)), ndigits=2)
        self.total_playouts += 1
    
    def add_child(self, child: MCTSNode):
        '''
        Add the new child and updates the index of the best child node to be chosen in Selection phase based on the UCB1 formula.

        Params:
        - child: the new child node to be added.
        '''
        self.children.append(child)
        

    



class MonteCarloTreeSearch():
    '''
    Class which handles the Monte Carlo Tree search.
    '''

    def __init__(self, player_index: int, env: PkmBattleEnv, enable_print: bool, enable_tree_visualization=False):
        self.node_counter = 1
        self.kb = KnowledgeBase()
        self.root: MCTSNode = MCTSNode(id=self.node_counter, env=env)
        self.player_index = player_index
        self.enable_print = enable_print
        self.enable_tree_visualization = enable_tree_visualization
        if not self.enable_tree_visualization:
            self.net = None
        else:
            self.net = Network(height="1800px", width="1800px", directed=True)
            self.net.add_node(
                self.root.id,
                label=f'{self.root.utility_playouts}/{self.root.total_playouts}',
                color='#D32F2F'
            )

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
            C = 1.6
            return exploitation_term + (C * exploration_term)
        node = self.root
        while not node.is_leaf:
            best_child = node.children[0]
            for child in node.children:
                if UCB1(child) > UCB1(best_child):
                    best_child = child
            node = best_child
        if self.enable_print:
            print(f'Selected: {node.id}')
        return node

    def expansion(self, node: MCTSNode, number_my_top_moves=1, number_opp_top_moves=1) -> list[MCTSNode]:
        '''
        Implements the Expansion phase used to generate new nodes from the current one.

        Params:
        - node: the node on which perform the expansion.
        - number_of_top_moves: the number of best moves which are used for the expansion (branching factor = number_of_top_moves * 2).

        Returns:
        The list of the children generated from the current node.
        '''
        # Case of no leaf node
        if not node.is_leaf:
            return None, False
        # Retrieve the actions and generate all the possible actions' combinations
        actions_comb_list: list[list[int,int]] = node.get_top_actions(
            my_team=node.env.teams[self.player_index],
            opp_team=node.env.teams[(self.player_index+1)%2],
            number_of_my_top_moves=number_my_top_moves,
            number_of_opp_top_moves=number_opp_top_moves
        )
        # Generates "number_of_top_moves" children nodes
        for actions in actions_comb_list:
            next_env, _, _, _, _ = node.env.step(actions)
            self.node_counter += 1
            # Add the child to the tree
            child = MCTSNode(
                id=self.node_counter,
                env=next_env[self.player_index],
                parent=node,
                actions=actions
            )
            node.add_child(child)
            # Update of the visualization tree
            if self.enable_tree_visualization:
                self.net.add_node(
                    n_id=child.id,
                    label=f'{child.utility_playouts}/{child.total_playouts}',
                    color='#2196F3'
                )
                my_move_name = get_pkm_move_name(
                    node=node,
                    action=actions[self.player_index],
                    player_index=self.player_index
                )
                opp_move_name = get_pkm_move_name(
                    node=node,
                    action=actions[(self.player_index+1)%2],
                    player_index=(self.player_index+1)%2
                )
                self.net.add_edge(
                    source=node.id,
                    to=child.id,
                    label=f'{my_move_name}|{opp_move_name}'
                )
        node.is_leaf = False
        if self.enable_print:
            print(f'Expanded {number_my_top_moves} nodes: {node.id} -> {[n.id for n in node.children]}')
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
            actions_comb_list = n.get_all_actions_combinations()
            index = np.random.randint(0, len(actions_comb_list))
            next_env, _, _, _, _ = n.env.step(actions_comb_list[index])
            self.node_counter += 1
            simulated_child = MCTSNode(
                id=self.node_counter,
                env=next_env[self.player_index],
                parent=n,
                actions=actions_comb_list[index],
                is_simulated=True
            )
            n.add_child(simulated_child)
            # Update the visualization tree
            if self.enable_tree_visualization:
                self.net.add_node(
                    n_id=simulated_child.id,
                    label=f'{node.utility_playouts}/{node.total_playouts}',
                    color='#BBDEFB'
                )
                my_move_name = get_pkm_move_name(
                    node=node,
                    action=actions_comb_list[index][self.player_index],
                    player_index=self.player_index
                )
                opp_move_name = get_pkm_move_name(
                    node=node,
                    action=actions_comb_list[index][(self.player_index+1)%2],
                    player_index=(self.player_index+1)%2
                )
                self.net.add_edge(
                    source=node.id,
                    to=simulated_child.id,
                    label=f'{my_move_name}|{opp_move_name}'
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
            winner_value = 1 if self.player_index == node.env.winner else 0
            backprop_nodes: list[MCTSNode] = []
            # Backpropagation pass
            while True:
                # Update of the node's values
                node.backpropagation_update(winner_value, self.player_index)
                backprop_nodes.append(node)
                # Update the visualization tree
                if self.enable_tree_visualization:
                    for net_node in self.net.nodes:
                        if net_node['id'] == node.id:
                            net_node['label'] = f'{node.utility_playouts}/{node.total_playouts}'
                            break
                # Case of root node
                if node.parent is None:
                    break
                # Case of node generated by the simulation
                if node.is_simulated:
                    parent_node = node.parent
                    parent_node.children.remove(node)
                    #self.net.nodes.remove(node.id)
                    del node
                    node = parent_node
                    continue
                node = node.parent
            # Case of print
            if self.enable_print:
                path_utility_list = [str(str(n.id)+':'+str(n.utility_playouts)+'/'+str(n.total_playouts)) for n in backprop_nodes]
                print(f'Backpropagated {len(backprop_nodes)} nodes: {path_utility_list}')




class MCTSBattlePolicy(BattlePolicy):
    '''
    Agent which uses the Monte Carlo Tree Search (MCTS) approach as policy to choose the actions.
    '''

    def __init__(self, player_index=0, enable_print=False, enable_tree_visualization=False):
        super().__init__()
        self.name = f'Player {player_index}'
        self.player_index = player_index
        self.enable_print = enable_print
        self.enable_tree_visualization = enable_tree_visualization
        self.tree = None
        self.n_switches = 0
    
    def __str__(self):
        print(self.name)
    
    def get_metrics(self):
        return {
            'n_switches': self.n_switches
        }
    
    def generate_tree(self, id: int):
        if self.tree is not None and self.tree.enable_tree_visualization:
            self.tree.net.set_options("""
                var options = {
                "physics": {
                    "enabled": true,
                    "barnesHut": {
                    "gravitationalConstant": -3000,
                    "centralGravity": 0.1,
                    "springLength": 150,
                    "springConstant": 0.04
                    },
                    "minVelocity": 0.75
                }
                }
                """
            )
            self.tree.net.show(f'Agents/MCTS/MCTS_trees/tree_{self.player_index}-{id}.html', notebook=False)
    
    def set_parameters(self, params: dict):
        self.params = params

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
            enable_print=self.enable_print,
            enable_tree_visualization=self.enable_tree_visualization
        )
        # Case of print
        if self.enable_print:
            print(f'Simulation phase for player {self.player_index}')
        # Perform N simulations
        for i in range(N):
            if self.enable_print:
                print(f'Player: {self.player_index}\nSimulation: {i+1}/{N}')
            leaf = tree.selection()
            children = tree.expansion(leaf, number_my_top_moves=2, number_opp_top_moves=3)
            terminal_nodes = tree.simulation(children)
            tree.backpropagation(terminal_nodes)
        # Case of no possible moves
        if tree.root.children == []:
            return None
        # Choose the move
        best_node = tree.root.children[0]
        for child in tree.root.children:
            best_node_utility = best_node.utility_playouts / best_node.total_playouts
            this_node_utility = child.utility_playouts / child.total_playouts
            # Case of switch action skipped if there is a difference between the utility values < HEURISTIC_COND1 (~0.02/0.05)
            if child.actions[self.player_index] > 3 and abs(best_node_utility - this_node_utility) < self.params['HEURISTIC_COND1']:
                continue
            # Case of current node with total number of playouts > HEURISTIC_COND2_1 times the best node's total number of playouts and similar utility values
            if best_node.total_playouts < child.total_playouts and child.total_playouts > self.params['HEURISTIC_COND2_1'] * best_node.total_playouts \
                and abs(this_node_utility - best_node_utility) < self.params['HEURISTIC_COND2_2']:
                best_node = child
                continue
            # Case of child with better utility value
            if this_node_utility > best_node_utility:
                best_node = child
        self.tree = tree
        # Update the number of switches
        if best_node.actions[self.player_index] > 3:
            self.n_switches += 1
        return best_node.actions[self.player_index]








