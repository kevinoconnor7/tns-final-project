# This notebook is for working out the details of the overall model we're going to have. The actual model is
# completely abstracted, and serves mostly as a moderator for the AI 'players' submitted to it.

import numpy as np

class basic_player:

    def __init__(self, delta=0.5):
        self.max_opinion_diff = delta

    def initialize(self, faction, n_players, idx):
        self.faction = faction # True for resistance, False for spy
        self.idx = idx
        self.n_players = n_players
        self.spies = []
        self.opinions = self.init_opinions(n_players)
        self.weights = self.init_weights(n_players)
        self.game_history = []
        self.max_opinion_diff = .5
        self.history = []

    def init_opinions(self, n):
        """ Figures out the initial opinions of each n players. Base player does uniformly 0.5 """
        opin = []
        if len(self.spies):
            opin = [1.] * n
            for idx in self.spies:
                opin[idx] = 0.
        else:
            for i in range(n):
                opin.append(np.random.rand()*.2+.4)

        opin[self.idx] = float(self.faction)

        return opin

    def init_weights(self, n):
        """ This function initializes the weights for each player in each opinion network.
        The base player takes care to initialize the weights for their own network to 0 for everyone but itself,
        so it cannot be convinced that it is a spy when it is not a spy. All other networks will have 1/degree
        weights. Weight lists will be recalculated between consensus rounds. """
        weight_lists = []
        for p in range(n):
            if p != self.idx:
                weight_lists.append([1/n]*n)
            else:
                weight_lists.append([0 if i!=self.idx else 1 for i in range(n)])
        return weight_lists


    def calc_real_opinion(self, neighbor_input):
        """ This function is called iteratively during the 'discussion' phase. neighbor_input is going to be a list of
        input vectors and the (perceived) opinions given for each player """
        # The base player is going to use the bounded confidence model if resistance
        # if it's a spy, it should not update its own opinions (as it knows the truth) but
        # instead hold a fake opinion that mirrors its resistance strategy

        # Save what we hear into history
        self.history.append(neighbor_input)

        all_opinions = np.array(neighbor_input).T
        self.weights = []
        for i in range(len(all_opinions)):
            if i == self.idx:
                self.weights.append([0 if i!=self.idx else 1 for z in range(len(all_opinions))])
                continue

            ith_weights = []
            within_range = 0
            for j in range(len(all_opinions[i])):
                if abs(self.opinions[j] - all_opinions[i][j]) <= self.max_opinion_diff:
                    within_range += 1

            for j in range(len(all_opinions[i])):
                if abs(self.opinions[j] - all_opinions[i][j]) <= self.max_opinion_diff:
                    ith_weights.append(1./within_range)
                else:
                    ith_weights.append(0)
            self.weights.append(ith_weights)

        new_opinions = np.array(self.weights)*all_opinions
        old_opinions = self.opinions
        self.opinions = new_opinions.T[self.idx]

        diff_opinions = [abs(old_opinions[i] - self.opinions[i]) for i in range(len(self.opinions))]

        # Return whether we feel okay stopping now
        return max(diff_opinions) < 0.005

    def calc_percv_opinion(self):
        """ Based on self.opinions, other player's (perceived) opinions and the game history,
        come up with an opinion that the player wants others players to perceive. """

        # The base player can simply return their actual opinion if they're resistance, or the
        # aforementioned fake opinion if they're a spy
        if self.faction:
            return self.opinions
        else:
            opin = np.random.rand(len(self.opinions))
            opin[self.idx] = 1
            return opin
            #return [0.5]*len(self.opinions)
        pass

    def team_select(self, mission_details):
        """ This is called iff the player is called on to select other players for a mission. It is given the
        mission details (a tuple of (req_players,n_spies_to_fail)) and outputs a selection of players """
        #TODO implement
        # The base player can disregard all history and just select the players it believes least likely to be
        # spies (if it's resistance). If it's a spy, the player can do the same and choose as many spies as required
        # to fail.
        req_players, n_spies_to_fail = mission_details
        team = None
        if self.faction:
            team = [i[0] for i in sorted(enumerate(self.opinions), key=lambda x:x[1], reverse=True)[:req_players]]
        else:
            # TODO Spies should already know who is a spy so they should select
            # the spy with the lowest detection
            team = [self.idx]
            most_trusted = [i[0] for i in sorted(enumerate(self.opinions), key=lambda x:x[1], reverse=True)]
            most_trusted.remove(self.idx)
            team += most_trusted[:(req_players-1)]
        return team

    def vote_on_select(self, team, mission_details, last_vote=False):
        """ This is called when a leader has selected a team. The player uses the mission details and the
        chosen players, and returns either True (for yes) or False."""
        #TODO implement
        # The base player should just vote no if it believes with a high certainty there is a spy on the team
        # (or yes otherwise) if it's resistance and flip that for a spy.

        if last_vote:
            return True

        req_players, n_spies_to_fail = mission_details

        n_suspected_spies = 0
        n_suspected_resistance = 0

        median_opinion = np.median(self.opinions)

        for i in team:
            if self.opinions[i] < median_opinion:
                n_suspected_spies += 1
            else:
                n_suspected_resistance += 1

        if self.faction:
            return n_suspected_spies == 0
        else:
            return n_suspected_spies >= n_spies_to_fail

    def set_spies(self, spies):
        self.spies = spies
        self.init_opinions(self.n_players)

    def execute_mission(self):
        """ This is called when a player is selected for a mission. A resistance player will always pass
        (return True), however a spy may choose not to fail the mission """
        #TODO implement
        # The resistance part here is pretty trivial
        # If you're a spy, then you can make a choice, but the basic player will just return True for resistance
        # and False for a spy
        return self.faction

    def recalc_opinion(self, current_leader, phase=None, extra=None):
        """ This function recalculates opinions for the phases: team_sel, votes, post_mission """
        if not self.faction:
            return
        #TODO
        if phase=="team_sel":
            #Decrease opinion of leader if you suspect mission contains a spy
            for player in extra:
                if player == self.idx:
                    self.opinions[current_leader] = (self.opinions[current_leader]*1.2)%1
                if player in sorted(self.opinions)[:len(extra)]:
                    self.opinions[current_leader] *= 0.8
        elif phase=="vote":
            #Increase/Decrease opionion of everyone based on whether they voted with/against you
            for player in range(len(extra)):
                if extra[player] == extra[self.idx]:
                    self.opinions[player] = (self.opinions[player]*1.2)%1
                else:
                    self.opinions[player] *= 0.8
        elif phase=="post-mission":
            #Increase/Decrease opinion of everyone on team (and leader) if mission passed/failed.
            if extra[0]:
                for player in extra[1]:
                    self.opinions[player.idx] *= 1.4
                if current_leader not in extra[1]:
                    self.opinions[current_leader.idx] *= 1.4
            else:
                for player in extra[1]:
                    self.opinions[player.idx] *= 0.95
                if current_leader not in extra[1]:
                    self.opinions[current_leader.idx] *= 0.8
