
class Match:

    def __init__(self, match_id, team_H, team_A, all_teams):
        self.match_id = match_id
        self.team_H = team_H
        self.team_A = team_A
        self.all_teams = all_teams
        self.all_teams_concedeRate = self._list_all_teams_concede_rates()
        self.avgConcedeRate = self._average_concede_rate()
        self.homeAdvantage = 0.05     # arbitary
        self.awayDisadvantage = 0.05  # arbitary
        self.team_H_goalRate = 0 
        self.team_A_goalRate = 0
        self.simulate_player_goals()
        self.simulate_conceded()

    def simulate_player_goals(self):
        c_Avg = self.avgConcedeRate
        home = 1 + self.homeAdvantage
        away = 1 - self.awayDisadvantage
        c_Away = self.team_A.concedeRate
        c_Home = self.team_H.concedeRate

        if c_Away == None:
            c_Away = self._max_concede_rate()
        if c_Home == None:
            c_Home = self._max_concede_rate()

        prob_lst = []
        for player in self.team_H.allPlayers:
            goals = player.goalsPerMatch
            assists = player.assistsPerMatch
            matchGoalRate = goals * home * c_Away / c_Avg
            matchAssistRate = assists * home * c_Away / c_Avg
            player.add_match_data(match_id=self.match_id,
                                  key='goalRate',
                                  data=matchGoalRate)
            player.add_match_data(match_id=self.match_id,
                                  key='assistRate',
                                  data=matchAssistRate)
            prob_lst.append(matchGoalRate * player.probAppearance(self.match_id))
        self.team_H_goalRate = sum(prob_lst)

        prob_lst = []
        for player in self.team_A.allPlayers:
            goals = player.goalsPerMatch
            assists = player.assistsPerMatch
            matchGoalRate = goals * away * c_Home / c_Avg
            matchAssistRate = assists * away * c_Away / c_Avg
            player.add_match_data(match_id=self.match_id,
                                  key='goalRate',
                                  data=matchGoalRate)
            player.add_match_data(match_id=self.match_id,
                                  key='assistRate',
                                  data=matchAssistRate)
            prob_lst.append(matchGoalRate * player.probAppearance(self.match_id))
        self.team_A_goalRate = sum(prob_lst)

        if self.team_H_goalRate < 0.5:
            self.team_H_goalRate = self.team_H.goalRate

        if self.team_A_goalRate < 0.5:
            self.team_A_goalRate = self.team_A.goalRate



    def simulate_conceded(self):
        """
        based on liklihood of playing and the probabiolity of scoring
        calc the number of goals actually likely to be conceded by opposing
        team
        if > 2 then -1 for defenders and GK of opposing team
        Can work both ways for teamA and or teamB
        Also used to work out probability of conceding at all
        """
        for player in self.team_H.allPlayers:
            player.add_match_data(match_id=self.match_id, 
                                  key='probConcede', 
                                  data=self.team_A_goalRate)

        for player in self.team_A.allPlayers:
            player.add_match_data(match_id=self.match_id, 
                                  key='probConcede', 
                                  data=self.team_H_goalRate)

    def resolve_BPS(self):
        lst = []

        for player in self.team_H.allPlayers + self.team_A.allPlayers:
            points = player.get_match_data(self.match_id, 'bonusPoints')
            lst.append((points, player))

        lst = sorted(lst, key=lambda x: x[0], reverse=True)

        for i, (points, player) in enumerate(lst, 1):
            player.add_match_data(self.match_id, 'BPSrank', i)
            player.resolve_BPS(self.match_id)
        
    def _list_all_teams_concede_rates(self):
        return [team.concedeRate
                for team 
                in self.all_teams.values()
                if team.concedeRate != None]
        

    def _average_concede_rate(self):
        concede = self.all_teams_concedeRate
        return sum(concede) / len(concede)

    def _max_concede_rate(self):
        return max(self.all_teams_concedeRate)

    def _min_goal_rate(self):
        return min([team.goalRate
                    for team
                    in self.all_teams.values()
                    if team.goalRate != None])



        



    

    

