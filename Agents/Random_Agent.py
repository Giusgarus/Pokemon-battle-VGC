import numpy as np
from vgc.behaviour import BattlePolicy
from vgc.datatypes.Objects import GameState

class RandomPolicy(BattlePolicy):

  def __init__(self, player_index=0):
      self.player_index = player_index
      self.n_switch = 0

  def get_action(self, g: GameState) -> int:

    # Prendo le informazioni sul team: ( pokemon attivo e le sue mosse, pokemon con cui posso fare uno switch )
    my_team = g.teams[self.player_index]
    my_active = my_team.active
    my_active_moves = my_active.moves
    my_switch = my_team.party
    my_actions = my_active_moves + my_switch

    # Do un azione random tra le 4 mosse del pokemon attivo e i due switch con i pokemon in panchina 
    n_moves = len(my_active_moves) 
    n_switch = len(my_switch)
    n_actions = len(my_actions)
    switch_probability = 0.15   # costante di probabilità di uno switch rispettoa usare una mossa

    # Definizione di una distribuzione di probabilità su tutte le azioni che posso fare
    pi = ([(1. - switch_probability) / n_moves] * n_moves) + ([switch_probability / n_switch] * n_switch)

    # scelta random dell'azione con la distribuzione di probabilità definita prima
    random_choice = np.random.choice(n_actions, p=pi)
    if random_choice > 3:
      self.n_switch += 1
    return random_choice

def get_metrics():
  
