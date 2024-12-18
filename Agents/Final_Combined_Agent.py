from vgc.behaviour import BattlePolicy
from vgc.datatypes.Constants import TYPE_CHART_MULTIPLIER
from vgc.datatypes.Objects import GameState, Weather, PkmMove, Pkm, PkmTeam
from vgc.datatypes.Types import PkmType, WeatherCondition
from Agents.Logic_Agent import KnowledgeBase
from Agetns.MTCS.MTCSBattlePolicies import MTCSNode, MTCSBattlePolicy, MonteCarloTreeSearch
from copy import deepcopy

import math

class CombinedPolicy(BattlePolicy):

  def __init__(self):
        super().__init__()  # Call the BattlePolicy constructor
        self.kb = KnowledgeBase()  # KnowledgeBase initialization 
        self.n_switches = 0

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
        my_switch = my_team.party[1:]
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
        #take the four best actions
        top_4_values = sorted(actions_priority, reverse=True)[:4]
        top_4_indices = [actions_priority.index(value) for value in top_3_values]

        my_pkms_not_fainted = my_team.get_not_fainted()
        opp_pkms_not_fainted = opp_team.get_not_fainted()
    
        if len(my_pkms_not_fainted) == 1 and len(opp_pkms_not_fainted) == 1:
          # START MINIMAX
        else:
          # START MTCS

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
