import numpy as np

from basic_player import basic_player

class weighted_player(basic_player):

    def __init__(self, weight_init='uniform', g=0.5):
        self.weight_strat = weight_init
        self.g = g

    def initialize(self, faction, n_players, idx):
        self.faction = faction # True for resistance, False for spy
        self.idx = idx
        self.n_players = n_players
        self.spies = []
        self.opinions = self.init_opinions(n_players)
        self.weights = self.init_weights(n_players)
        self.game_history = []
        self.history = []

    def calc_real_opinion(self, neighbor_input, neighbor_idx):
        """ Instead of BC, just do a standard ole consensus iteration. We currently just hear one set of opinions from one neighbor,
        so we can just do this in a scalar fashion"""
        for player in range(n_players):
            if player == self.idx:
                continue # We could have something happen to say the weight of the neighbor talking about you, but for now just ignore
            self.opinions[player] = self.g*self.opinions[player] + (1-self.g)*neighbor_input[player]*self.weights[neighbor_idx][player]








