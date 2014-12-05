import numpy as np

# Framework: the game will proceed in phases
# Initialization
# For each mission:
#  until vote is passed:
#  discussion
#  team selection
#  recalculate_opinion
#  discussion
#  vote
#  recalculate_opinion
#  if the vote failed, we go back
#  if the vote failed for the 5th time, fail and start a new mission
#  if the vote passed
#   execute_mission
#   recalculate_opinion
class game_moderator:
    def __init__(self, players, max_iter=None):
        """ Give the game moderator a list of instantiated players """
        self.players = []
        self.n_players = len(players)
        self.n_spies = 1 + (self.n_players-1) // 3 # 5 <= Num_players <= 10
        # randomly choose spies by getting the probability that any player is a spy
        is_res = [True] * (self.n_players - self.n_spies) + [False] * self.n_spies
        np.random.shuffle(is_res)
        #prob_spy = self.n_spies / self.n_players
        #spies_left = self.n_spies
        # reorder players to prevent bias of spies being assigned to earlier players
        np.random.shuffle(players)
        for idx, player in enumerate(players):
            #if ((np.random.rand() < prob_spy) and (spies_left > 0)) or self.n_players-idx <= spies_left:
            #    is_res = False
            #    spies_left -= 1
            player.initialize(is_res[idx], self.n_players, idx)
            self.players.append(player)
        self.missions = self.get_missions()
        self.current_leader = 0
        self.max_iter = max_iter

        spies = [player.idx for player in self.players if not player.faction]
        for player in self.players:
            if not player.faction:
                player.set_spies(spies)

    def get_missions(self):
        """ Returns a list of 5 missions according to the game rules for the given number of players """
        mission_rules = {
        5:[(2,1),(3,1),(2,1),(3,1),(3,1)],
        6:[(2,1),(3,1),(4,1),(3,1),(4,1)],
        7:[(2,1),(3,1),(3,1),(4,2),(4,1)],
        8:[(3,1),(4,1),(4,1),(5,2),(5,1)],
        9:[(3,1),(4,1),(4,1),(5,2),(5,1)],
        10:[(3,1),(4,1),(4,1),(5,2),(5,1)]
        }
        try:
            return mission_rules[self.n_players]
        except KeyError as ke:
            print("Invalid number of players")
            raise

    def run_mission(self, cur_mission, silent=False):
        """ This will actually run the mission index specified """
        n_votes = 0
        prop_team = []
        while (True):
            if not silent:
                print("Voting round %d" % n_votes)
            if n_votes == 6: ## vote limit, fail the mission
                return False
            self.discuss_opinions(self.max_iter)
            prop_team = self.team_select(self.current_leader, cur_mission)
            if not silent:
                for idx in prop_team:
                    print("%d: Is resistance? %s" % (idx, self.players[idx].faction))
            for player in self.players:
                player.cur_leader = self.current_leader
                player.prop_team = prop_team
                player.cur_mission = cur_mission
                player.vote_num = n_votes
            self.recalc_opinions(phase="team_sel", extra=prop_team)
            self.discuss_opinions(self.max_iter)
            vote_passed, votes = self.get_votes(prop_team, cur_mission, n_votes == 5)
            self.recalc_opinions(phase="vote",extra=votes)
            if vote_passed:
                break
            else:
                self.current_leader += 1
                self.current_leader %= self.n_players
                n_votes += 1
        # Once we're out of that loop, we can execute the mission and have players recalculate their opinions
        n_pass, n_fail = self.execute_mission(prop_team)

        # The mission succeeds if less than the number of spies needed to fail the mission
        # had failed the mission
        mission_result = n_fail < cur_mission[1]

        self.recalc_opinions(phase="post_mission",extra=(mission_result, prop_team))
        self.current_leader = (self.current_leader+1) % self.n_players
        return mission_result

    def discuss_opinions(self, n_iter=100):
        """ This function takes each player's perceived opinions and broadcasts them to every player for
        in a random order. If n_iter is not specified, it will try to run until convergence """
        last_opinions = None

        run_to_conv = True if n_iter is None else False
        if n_iter is None:
            n_iter = 0

        shuffled_players = np.arange(self.n_players)

        while run_to_conv or n_iter > 0:
            opinions = []
            is_done = 0

            np.random.shuffle(shuffled_players)

            for p in shuffled_players:
                p_opinion = self.players[p].calc_percv_opinion()

                for player in self.players:
                    if player.idx == p:
                        continue
                    player.calc_real_opinion(p_opinion, p)

            n_iter = abs(int(n_iter) - 1)

    def team_select(self, current_leader, current_mission):
        """ This function just calls the current leader's team_select function, which returns the proposed team"""
        return self.players[current_leader].team_select(current_mission)

    def recalc_opinions(self, phase=None, extra=None):
        """ Goes through each player and calls their recalc_opinions function """
        for player in self.players:
            player.recalc_opinion(self.current_leader, phase, extra)

    def get_votes(self, prop_team, cur_mission, last_vote=False):
        """ Goes through each player to get their vote on the proposed team """
        votes = []
        for player in self.players:
            votes.append(player.vote_on_select(prop_team, cur_mission, last_vote))

        vote_passed = len([x for x in votes if x]) > self.n_players/2
        return vote_passed, votes

    def execute_mission(self, prop_team):
        """ Goes through the proposed team and calls their execute_mission function, then
        collects the responses """
        n_pass, n_fail = 0, 0
        for player in prop_team:
            if self.players[player].execute_mission():
                n_pass += 1
            else:
                n_fail += 1
        return n_pass, n_fail
