import os
import json
import requests
import pandas as pd
from functools import lru_cache

class FantasyData:

    def __init__(self):

        ## set constants ##
        self.base_url = 'https://fantasy.premierleague.com/drf/'
        self.directory = 'DataStore/'
        self.target_urls = {'fixtures': ('fixtures', 'fixtures'),
                            'bootstrap-static': ('bootstrap-static', 'bootstrap_static'),
                            'events': ('event/{}/live', 'gameweek_{:02d}')}


        ## run init methods ##
        self._check_dir_exists()

    def _check_dir_exists(self):
        """
        Ensures the assigned data directory exists, and creates it if not.
        """
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)   


    def _download_data(self, url, loc):
        """
        Downloads data from target url and stores as JSON text file.

        url: url of target data, as a string
        loc: local relative file location, as a string
        Returns: JSON data as string.
        """
        json_text = requests.get(url).text
        with open(loc, 'w+', encoding='utf-8') as f:
            f.write(json_text)
        return json_text

    def _retrieve_data(self, url, loc):
        """
        Attempts to retrieve data locally.
        If cannot be found, downloads data instead.

        url: url of target data, as a string
        loc: local relative file location, as a string
        Returns: JSON data as string.
        """
        try:
            with open(loc, encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return self._download_data(url, loc)

    def _create_url_loc(self, target, *args):
        """
        Extracts target url and file name, and
        combines with base url and directory.
        Any arguments will also get applied, for IDs and Gameweeks.
        Returns: url and loc, as a tuple.
        """
        url, name = self.target_urls[target]
        url = self.base_url + url.format(*args)
        loc = self.directory + name.format(*args)
        return url, loc

    @lru_cache(maxsize=None)
    def _convert_to_df(self, url, loc, json_path=''):
        data = self._retrieve_data(url=url, loc=loc)
        if json_path:
            json_data = json.loads(data)[json_path]
        else:
            json_data = json.loads(data)
        df = pd.DataFrame.from_dict(json_data)
        df.set_index('id', inplace=True)
        return df

    @lru_cache(maxsize=32)
    def _extract_value(self, url, loc, json_path):
        data = self._retrieve_data(url=url, loc=loc)
        value = json.loads(data)[json_path]
        return value

    @lru_cache(maxsize=32)
    def _extract_dict(self, url, loc, json_path):
        data = self._retrieve_data(url=url, loc=loc)
        dct = json.loads(data)[json_path]
        return dct

    @lru_cache(maxsize=None)
    def _extract_elements(self, url, loc):
        data = self._retrieve_data(url=url, loc=loc)
        player_nest = json.loads(data)['elements']
        player_range = range(1, len(player_nest) + 1)

        gw_stats = []

        for pid in player_range:
            stats = player_nest[str(pid)]['stats']
            stats['id'] = pid
            gw_stats.append(stats)
            
        return pd.DataFrame.from_records(gw_stats, index=['id'])

    @property
    def fixtures(self):
        url, loc = self._create_url_loc('fixtures')
        return self._convert_to_df(url, loc)

    def events(self, gameweek=False):
        if not gameweek:
            url, loc = self._create_url_loc('bootstrap-static')
        return self._convert_to_df(url, loc, json_path='events')

    @property
    def player_types(self):
        url, loc = self._create_url_loc('bootstrap-static')
        return self._convert_to_df(url, loc, json_path='element_types')

    @property
    def teams(self):
        url, loc = self._create_url_loc('bootstrap-static')
        return self._convert_to_df(url, loc, json_path='teams')

    @property
    def current_gameweek(self):
        url, loc = self._create_url_loc('bootstrap-static')
        return self._extract_value(url, loc, json_path='current-event')

    @property
    def last_gameweek(self):
        url, loc = self._create_url_loc('bootstrap-static')
        return self._extract_value(url, loc, json_path='last-entry-event')

    @property
    def next_gameweek(self):
        url, loc = self._create_url_loc('bootstrap-static')
        return self._extract_value(url, loc, json_path='next-event')
    
    def players(self, gw=False):
        if not gw:
            url, loc = self._create_url_loc('bootstrap-static')
            return self._convert_to_df(url, loc, json_path='elements')
        elif 0 < gw <= self.last_gameweek:
            url, loc = self._create_url_loc('events', gw)
            return self._extract_elements(url, loc)
        else:
            raise 'Incorrect Gameweek format'
        
    def weekly_breakdown(self, player_id):
        stats_player = []
        for gw in range(1,self.next_gameweek):
            url, loc = self._create_url_loc('events', gw)
            data = self._retrieve_data(url=url, loc=loc)
            player_nest = json.loads(data)['elements']
            stats = player_nest[str(player_id)]['stats']
            stats['gameweek'] = gw
            stats_player.append(stats)
        return pd.DataFrame.from_records(stats_player, index=['gameweek'])

    @property
    def game_settings(self):
        url, loc = self._create_url_loc('bootstrap-static')
        return self._extract_dict(url, loc, json_path='game-settings')

    


    def refresh_all(self):
        """
        Re-downloads all data. Returns nothing.
        """
        self._convert_to_df.cache_clear()  # clears dataframe cache

        url, loc = self._create_url_loc('fixtures')
        self._download_data(url, loc)

        url, loc = self._create_url_loc('bootstrap-static')
        self._download_data(url, loc)



if __name__ == '__main__':
    print('Testing in progress...')
    FPL = FantasyData()
    #FPL.refresh_all()
    assert FPL.fixtures._typ == 'dataframe'
    assert FPL.events()._typ == 'dataframe'
    assert FPL.player_types._typ == 'dataframe'
    assert FPL.teams._typ == 'dataframe'
    assert 0 < FPL.current_gameweek <= 38
    assert 0 < FPL.next_gameweek <= 38
    assert FPL.last_gameweek == 38
    assert FPL.players()._typ == 'dataframe'
    assert FPL.players(gw=1)._typ == 'dataframe'
    assert FPL.weekly_breakdown(123)._typ == 'dataframe'
    assert len(FPL.game_settings) == 2
    print('Testing Complete')



    