import json
import requests
import pandas as pd

class FantasyData:

    def __init__(self):
        self.url = 'https://fantasy.premierleague.com/drf/bootstrap-static'
        self.fixtures_url = 'https://fantasy.premierleague.com/drf/fixtures/'
        self.static = 'DataStore/bootstrap-static.json'
        self.fixtures_loc = 'DataStore/fixtures.json'
        self.dir = 'DataStore/'
        self.json_fixtures = self._get_data('fixtures')
        self.json_players = self._get_data('players')
        self.players(self._get_players())
        self.fixtures(self._get_fixtures())
    
    @staticmethod
    def players(df):
        """
        sets attributes for player data

        example: FantasyData().players.full_names
        returns list of full_names for all players
        """
        full_name = df.first_name + ' ' + df.second_name
        news = df[['web_name', 'news']][df.news != '']
        setattr(FantasyData.players, 'data', df)
        setattr(FantasyData.players, 'columns', list(df.columns))
        setattr(FantasyData.players, 'names', df.web_name)
        setattr(FantasyData.players, 'full_names', full_name)
        setattr(FantasyData.players, 'news', news)

    @staticmethod
    def fixtures(df):
        setattr(FantasyData.fixtures, 'all', df)


    def _save_as_csv(self, name, df):
        """saves df as csv for external analysis"""
        df.to_csv(self.dir + name + '.csv') 

    def refresh(self, url, store):
        """load from url and refresh object"""
        url_text = requests.get(url).text
        with open(store, 'w+', encoding='utf-8') as f:
            f.write(url_text)
        input('write to file')
        self.__init__()

    def refresh_fixtures(self):
        self.refresh(self.fixtures_url, self.fixtures_loc)

    def refresh_players(self):
        self.refresh(self.url, self.static)

    def _get_data(self, dtype):
        """returns FPL data as a Dictionary"""
        if dtype == 'fixtures':
            file = self.fixtures_loc
            url = self.fixtures_url
        elif dtype == 'players':
            file = self.static
            url = self.url
        else:
            raise('Incorrect dtype')
        try:
            with open(file, encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.refresh(url, file)
        
    def _get_players(self):
        """returns FPL player dataframe"""
        df = pd.DataFrame.from_dict(self.json_players['elements'])
        df.set_index('id', inplace=True)
        return df

    def _get_fixtures(self)       :
        df = pd.DataFrame.from_dict(self.json_fixtures)
        df.set_index('id', inplace=True)
        return df


if __name__ == '__main__':
    print('testing in progress...', end=' ')
    FPL = FantasyData()
    assert len(FPL.players.names) > 400
    assert len(FPL.players.columns) > 50
    assert len(FPL.players.news.columns) == 2
    print('Complete')



        





        
    
    