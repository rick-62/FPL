
class Squad:

    def __init__(self, name, player_lst):
        self.name = name
        self.allPlayers = player_lst
        self.defenders = self._extract_players('Defender')
        self.forwards = self._extract_players('Forward')
        self.midfielders = self._extract_players('Midfielder')
        self.goalkeepers = self._extract_players('GoalKeeper')
        self.team_name = self._get_team_name()
        self.concedeRate = self._calculate_concedeRate()
        self.goalRate = self._calculate_goalRate()
        
    
    def _get_team_name(self):
        lst = []
        for player in self.allPlayers:
            lst.append(player.Team)
        return max(set(lst), key=lst.count)


    def _extract_players(self, position):
        return [player for player
                in self.allPlayers
                if player == position]

    
    def _calculate_concedeRate(self):
        # quick and dirty
        if self.team_name == 'Wolverhampton Wanderers':
            return 1.85
        elif self.team_name == 'Fulham':
            return 1.41
        elif self.team_name == 'Cardiff City':
            return 1.95

        conceded = [d.concededPerMatch 
                    for d 
                    in self.defenders + self.goalkeepers]
                    
        apps =     [a.appRate
                    for a 
                    in self.defenders + self.goalkeepers]

        total = sum(apps) 
        avg = lambda: sum(conceded) / len([c for c in conceded if c > 0])

        if sum(conceded) == 0:
            return
        elif total == 0:
            return avg()

        f = lambda a,r: r * a / total
        estimate = sum([f(a,r) for a,r in zip(apps, conceded)])

        if estimate < min(conceded) or estimate > max(conceded):
            estimate = avg()

        return estimate

    def _calculate_goalRate(self):
        lst = []
        for player in self.allPlayers:
            goalRate = player.goalsPerMatch
            appRate = player.appRate
            lst.append(goalRate * appRate)

        # quick and dirty
        if self.team_name == 'Wolverhampton Wanderers':
            return 1.03
        elif self.team_name == 'Fulham':
            return 1.15
        elif self.team_name == 'Cardiff City':
            return 0.84

        if sum(lst) == 0:
            return
        else:
            return sum(lst)


        
        
            
            



    

    





    


    