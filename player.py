import pandas as pd
from math import exp, factorial
from datetime import datetime, timedelta

class Player:
    latest = 2018
    season_length = 38
    assistPoints = 3
    yellowPoints = -1
    redPoints = -3
    owngoalPoints = -2
    plus60Points = 2
    sub60Points = 1

    def __init__(self, data, overview, fixtures):
        self.latest = Player.latest
        self.gameweeks = Player.season_length
        self._convert_data_to_attr(data)
        self.matches = self._extract_matches(fixtures)
        self.overview = self._extract_overview(overview)
        self.games_played = self._get_games_played()
        self.goalsPerMatch = self.actual_goals_per_match()
        self.assistsPerMatch = self.assists_per_match()
        self.Position = self.actual_position()
        self.probability_of_appearance()
        self.cards()
        self.calc_own_goals()
        self.assistPoints = Player.assistPoints
        self.yellowPoints = Player.yellowPoints
        self.redPoints = Player.redPoints
        self.owngoalPoints = Player.owngoalPoints
        self.plus60Points = Player.plus60Points
        self.sub60Points = Player.sub60Points

    def _convert_data_to_attr(self, data):
        """Converts data (dict) to object attributes"""
        for k, v in data.items():
            setattr(self, k, v)

    def _extract_overview(self, df):
        """extracts apps, subs and goals per season and
        saves as dictionary, in YM# (Year Minus) format"""
        dct = {}
        try:
            for season in df.Season.unique():
                season_int = int(season[:4])
                ym = 'ym{}'.format(self.latest - season_int)
                Season = df[df.Season == season]
                apps = sum(Season.Apps)
                subs = sum(Season.Subs)
                goals = sum(Season.Goals)
                dct[ym] = (apps, subs, goals)
        except AttributeError:
            season = df.Season
            season_int = int(season[:4])
            ym = 'ym{}'.format(self.latest - season_int)
            apps = df.Apps
            subs = df.Subs
            goals = df.Goals
            dct[ym] = (apps, subs, goals)
        return dct
        

    def _extract_matches(self, df):
        # df.set_index('id', inplace=True)
        mask = (df['team_h'] == self.team) | (df['team_a'] == self.team)
        return df[mask].to_dict('index')

    def _get_games_played(self):
        count = 0
        for k, v in self.matches.items():
            if v['finished'] == 'true':
                count += 1
        return count
    

    def aggregate_overview_stats(self, seasons=['ym0','ym1']):
        """
        Input: 
        - seasons -- seasons to aggregate (list)
        - self.overview -- all season data (dict)
    
        Returns dict containing:
        - sum of appearances (apps)
        - sum of substitutions (subs)
        - sum of goals (goals)
        - calculated sum of missed appearances (missed)
        """
        dct = {'apps': 0, 'subs': 0, 'missed': 0, 'goals': 0}
        for ym in self.overview.keys():                
            if ym in seasons:
                apps, subs, goals = self.overview[ym]
                if ym == 'ym0':
                    missed = self.games_played - apps
                else:
                    missed = self.season_length - apps
                if dct['apps'] + apps > 38:
                    continue
                dct['apps'] += apps
                dct['subs'] += subs
                dct['missed'] += missed
                dct['goals'] += goals
                    
        return dct

    def probAppearance(self, match_id):
        return self.matches[match_id]['probAppearance']

    def probability_of_appearance(self):
        agg = self.aggregate_overview_stats()
        apps = agg['apps']
        subs = agg['subs']
        missed = agg['missed']
        total = apps + missed
        chance, return_date = self.check_news()
        app_rate = apps / total if total != 0 else 0
        self.appRate = app_rate
        sub_rate = subs / total if total != 0 else 0
        start_rate = (apps - subs) / total if total != 0 else 0
        for k,v in self.matches.items(): 
            kickoff_time = self.matches[k]['kickoff_time']
            kickoff_date = kickoff_time.split('T')[0]
            kickoff = datetime.strptime(kickoff_date, '%Y-%m-%d')
            prob = chance if kickoff < return_date else 1
            self.matches[k]['probAppearance'] = prob * app_rate
            self.matches[k]['probSub'] = prob * sub_rate
            self.matches[k]['probStart'] = prob * start_rate

    def check_news(self):
        today = datetime.today()
        chance = self.chance_of_playing_next_round / 100
        status = self.status
        return_date = lambda weeks: today + timedelta(weeks=weeks)
        if status == 'i':    # injury with unknown return date
            return (chance, return_date(4))
        elif status == 'u':  # transferred or on loan (0%)
            return (chance, return_date(52))
        elif status == 'd':  # chance of playing
            return (chance, return_date(2))
        elif status == 'n':
            return (chance, return_date(15))
        elif status == 's':
            return (chance, return_date(3))
        else:
            return (100, today)

        
    @staticmethod
    def poisson(l, x, eq='eq'):
        """
        Maps probability to poisson distribution

        Input:
        - l -- lambda representing rate
        - x -- target value from which to determine probability
        - eq -- equality in relation to x ('eq','gte','lte')

        Returns probability (float from 0 to 1)
        """
        f = lambda x,l: exp(-l) * l**x / factorial(x)
        if eq == 'eq':
            return f(x,l)
        elif eq == 'lte':
            return sum([f(X,l) for X in range(x+1)])
        elif eq == 'gte':
            return 1 - sum([f(X,l) for X in range(x)])
            

    def cards(self):
        """
        Determines probabilities for getting red/yellow cards

        Lumps all yellow and red cards together, then uses Poisson
        Distribution to determine probability of getting 1 or 2 cards.
        2 cards can be assumed to be the equivilent of a Red card.
        """
        yellows = getattr(self, 'Yellow Cards')
        reds = getattr(self, 'Red Cards')
        total = yellows + reds

        try:
            l = total / self.Appearances
        except ZeroDivisionError:
            l = 0
        self.P_red = self.poisson(l, 2)
        self.P_yellow = self.poisson(l, 1)

    def calc_own_goals(self):
        """
        Determines probability for scoring an own goal
        """
        own = getattr(self, 'Own Goals')
        try:
            P_ownGoal = own / self.Appearances
        except ZeroDivisionError:
            P_ownGoal = 0
        self.P_ownGoal = P_ownGoal
        
    def actual_goals_per_match(self):
        delattr(self, 'Goals Per Match')
        try:
            return self.Goals / self.Appearances
        except ZeroDivisionError:
            return 0

    def assists_per_match(self):
        try:
            return self.Assists / self.Appearances
        except ZeroDivisionError:
            return 0

    def actual_position(self):
        positions = {1: 'GoalKeeper',
                     2: 'Defender',
                     3: 'Midfielder',
                     4: 'Forward'}
        return positions[self.element_type]
        

    def probability_of_goals(self, match_id, weight, X=3):
        l = self.goalsPerMatch * weight
        f = self.poisson
        probGoalScored = [(x, f(l,x)) for x in range(X+1)]
        return probGoalScored

    def add_match_data(self, match_id, key, data):
        self.matches[match_id][key] = data

    def get_match_data(self, match_id, key):
        return self.matches[match_id][key]

    def _resolve(self, *funcs):
        for match_id, match in self.matches.items():
            if match['finished'] == True:
                continue
            points = sum([f(match) for f in funcs])
            points *= match['probAppearance']
            self.matches[match_id]['initialPoints'] = points

    def time_played(self, match):
        """estimate over/under 60mins based on whether started match 
        or was a sub"""
        start = match['probStart'] * self.plus60Points
        sub = match['probSub'] * self.sub60Points
        return start + sub

    def goal_assists(self, match):
        return match['assistRate'] * self.assistPoints

    def card_points(self, _):
        reds = self.P_red * self.redPoints
        yellows = self.P_yellow * self.yellowPoints
        return reds + yellows     
        
    def own_goal_points(self, _):
        return self.P_ownGoal * self.owngoalPoints

    def goal_points(self, match):
        P = lambda x: self.poisson(match['goalRate'], x)
        return self.goalPoints * sum([P(x)*x for x in [1,2,3,4,5]])
            
    def clean_sheet(self, match):
        return self.poisson(match['probConcede'], 0) * self.cleanPoints

    def conceded(self, match):
        return self.poisson(match['probConcede'], 2, eq='gte') \
                                                    * self.concededPoints 

    def resolve_BPS(self, match_id):
        match = self.matches[match_id]
        initial = match['initialPoints']
        rank = match['BPSrank']
        bps = 0 if rank > 3 else 4 - rank
        # improved by spreading BPS across players
        bps *= self.probAppearance(match_id)
        match['finalPoints'] = initial + bps

    def _calculate_BPS(self, *funcs):
        for match_id, match in self.matches.items():
            if match['finished'] == True:
                continue
            points = sum([f(match) for f in funcs])
            points *= match['probAppearance']
            self.matches[match_id]['bonusPoints'] = points

    def BPS_goal_points(self, match):
        P = lambda x: self.poisson(match['goalRate'], x)
        return self.BPSgoalPoints * sum([P(x)*x for x in [1,2,3,4,5]])

    def BPS_clean_sheet(self, match):
        return self.poisson(match['probConcede'], 0) * self.BPScleanPoints


class GoalKeeper(Player):
    goalPoints = 6
    cleanPoints = 4
    concededPoints = -1
    
    def __init__(self, data, overview, fixtures):
        super().__init__(data, overview, fixtures)
        self.concededPerMatch = self._calculate_concede_rate()
        self.goalPoints = GoalKeeper.goalPoints
        self.cleanPoints = GoalKeeper.cleanPoints
        self.concededPoints = GoalKeeper.concededPoints
        self.BPSgoalPoints = 12
        self.BPScleanPoints = 12
        
    def _calculate_concede_rate(self):
        conceded = getattr(self, 'Goals Conceded')
        appearances = getattr(self, 'Appearances')
        try:
            return conceded / appearances
        except ZeroDivisionError:
            return 0
    
    def resolve(self):
        self._resolve(self.time_played, 
                      self.goal_assists, 
                      self.card_points,
                      self.own_goal_points,
                      self.goal_points,
                      self.clean_sheet,
                      self.conceded)

    def calculate_BPS(self):
        self._calculate_BPS(self.BPS_goal_points,
                            self.BPS_clean_sheet)

    def __eq__(self, compare):
        if compare == 'GoalKeeper':
            return True
        else:
            return False
        
class Forward(Player):
    goalPoints = 4
    
    def __init__(self, data, overview, fixtures):
        super().__init__(data, overview, fixtures)
        self.goalPoints = Forward.goalPoints
        self.BPSgoalPoints = 24

    def resolve(self):
        self._resolve(self.time_played, 
                      self.goal_assists, 
                      self.card_points,
                      self.own_goal_points,
                      self.goal_points)

    def calculate_BPS(self):
        self._calculate_BPS(self.BPS_goal_points)

    def __eq__(self, compare):
        if compare == 'Forward':
            return True
        else:
            return False

class Midfielder(Player):
    goalPoints = 5
    cleanPoints = 1
    
    def __init__(self, data, overview, fixtures):
        super().__init__(data, overview, fixtures)
        self.goalPoints = Midfielder.goalPoints
        self.cleanPoints = Midfielder.cleanPoints
        self.BPSgoalPoints = 18

    def resolve(self):
        self._resolve(self.time_played, 
                      self.goal_assists, 
                      self.card_points,
                      self.own_goal_points,
                      self.goal_points,
                      self.clean_sheet)
    
    def calculate_BPS(self):
        self._calculate_BPS(self.BPS_goal_points)

    def __eq__(self, compare):
        if compare == 'Midfielder':
            return True
        else:
            return False
      

class Defender(Player):
    goalPoints = 6
    cleanPoints = 4
    concededPoints = -1
    
    def __init__(self, data, overview, fixtures):
        super().__init__(data, overview, fixtures)
        self.concededPerMatch = self._calculate_concede_rate()
        self.goalPoints = Defender.goalPoints
        self.cleanPoints = Defender.cleanPoints
        self.concededPoints = Defender.concededPoints
        self.BPSgoalPoints = 12
        self.BPScleanPoints = 12

    def _calculate_concede_rate(self):
        conceded = getattr(self, 'Goals Conceded')
        appearances = getattr(self, 'Appearances')
        try:
            return conceded / appearances
        except ZeroDivisionError:
            return 0
        

    def resolve(self):
        self._resolve(self.time_played, 
                      self.goal_assists, 
                      self.card_points,
                      self.own_goal_points,
                      self.goal_points,
                      self.clean_sheet,
                      self.conceded)

    def calculate_BPS(self):
        self._calculate_BPS(self.BPS_goal_points,
                            self.BPS_clean_sheet)

    def __eq__(self, compare):
        if compare == 'Defender':
            return True
        else:
            return False