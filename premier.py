import time
import requests
import re
import pandas as pd
import selenium.webdriver as webdriver
from bs4 import BeautifulSoup

class PremierData:
    numeric_fields = ['Wins', 
                      'Goals Per Match', 
                      'Penalties Scored',
                      'Big Chances Missed', 
                      'Goals',
                      'Losses', 
                      'Appearances', 
                      'Clean Sheets', 
                      'Goals Conceded', 
                      'Own Goals', 
                      'Assists', 
                      'Big Chances Created', 
                      'Yellow Cards', 
                      'Red Cards']

    
    def __init__(self):
        self.player_url = 'https://www.premierleague.com/players/'
        self.indexDir = 'DataStore/players.index.csv' 
        self.statsDir = 'DataStore/players.stats.csv' 
        self.overviewDir = 'DataStore/players.overview.csv'
        self.driver = 'chromedriver'
        self.numeric_fields = PremierData.numeric_fields
        self.df_linkingIndex = self._get_index_data()
        self._get_all_player_stats()

    def refresh(self, which='all', limit=False):
        """load from url and refresh object"""
        if which == 'index' or which =='all':
            self._player_lst = self._fetch_index_data()
            self._convert_index_to_csv(self._player_lst)
        if which =='players' or which =='all':
            self._process_all_player_stats()
        self.__init__()

    def _get_index_data(self):
        """returns PL data as a Dictionary"""
        try:
            df = pd.read_csv(self.indexDir, index_col='player_id')
            return df
        except FileNotFoundError:
            self.refresh(which='index')

    def _convert_index_to_csv(self, player_lst):
        """cleans up fetched index data and saves locally as CSV"""
        dct = {'player_id': [], 'code': []}
        pattern = re.compile(r'players/(\d+)/\S+/')
        for href, FPL_ID in player_lst:
            ID = int(re.search(string=href, pattern=pattern).group(1))
            dct['player_id'].append(ID)
            dct['code'].append(int(FPL_ID[1:]))
        
        df = pd.DataFrame.from_records(dct, index=dct['player_id'])
        del df['player_id']
        df.to_csv(self.indexDir, index_label='player_id')
        
        
    def _fetch_index_data(self):
        """
        1. Visits Premier League players page
        2. Scrolls to the bottom to force all current league players to load
        3. Scrapes all player links and FPL IDs for future linking
        """

        if self.driver == 'chromedriver':
            browser = webdriver.Chrome(executable_path=self.driver)

        browser.get(self.player_url)
        time.sleep(5)  # no rush so giving plenty of time to load

        # Get initial scroll height
        last_height = browser.execute_script(
            "return document.body.scrollHeight")

        # scroll to bottom of page until height of page no longer increases
        while True:
            browser.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")

            time.sleep(0.5)  # Wait to load page

            new_height = browser.execute_script(
                "return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        elements = browser.find_elements_by_class_name('playerName')

        player_lst = []
        for element in elements:
            img_element = element.find_element_by_tag_name('img')
            player_href = element.get_attribute('href')
            FPL_id = img_element.get_attribute('data-player')
            player_lst.append((player_href, FPL_id))
            
        browser.close()

        return player_lst


    def _fetch_player_stats(self, player_id):
        """downloads individual player stats from PL, given url player id"""

        stats_url    = self.player_url + \
                                '{}/player/stats'.format(player_id)

        overview_url = self.player_url + \
                                '{}/player/overview'.format(player_id)
        
        time.sleep(1)  # Prevent accidently bombarding PL with requests
        stats_request = requests.get(stats_url)
        stats_page = stats_request.text
        status_code_stats = stats_request.status_code

        time.sleep(1)  # Prevent accidently bombarding PL with requests 
        overview_request = requests.get(overview_url)  
        overview_page = overview_request.text
        status_code_overview = overview_requests.status_code

        if stats_request != 200 or overview_request != 200:
            input('{}: {} (stats) & {} (overview)'.format(player_id, 
                                                          stats_request, 
                                                          overview_request) )


        return {'stats': stats_page, 'overview': overview_page}


    def _extract_fields_from_stats(self, stats_page, player_id):
        """extracts required fields from downloaded player stats"""

        soup = BeautifulSoup(stats_page, 'html.parser')
        page_text = soup.get_text()
        page_text = page_text.replace('\n', ' ')
        page_text = page_text.replace('\r', ' ')
        
        fields = {'player_id': player_id}

        pattern_1 = r'{}\s+(\d+)'
        for field in self.numeric_fields:
            values = re.findall(pattern=pattern_1.format(field), 
                                flags=re.IGNORECASE, 
                                string=page_text)
            # only certain stats come through for different positions
            fields[field] = 0 if len(values) == 0 else int(values[0])
            
        pattern_2 = r'Club\s{4}(.+?)\s{2}Position\s(.+?)\s'
        club_and_position = re.findall(pattern=pattern_2, 
                                       string=page_text)[0]
        fields['Team'] = club_and_position[0]
        fields['Position'] = club_and_position[1]

        return fields

    def _extract_data_from_overview(self, overview_page, player_id):
        """extracts require data from downloaded player overview"""

        soup = BeautifulSoup(overview_page, 'html.parser')

        tbl = soup.find_all('table')
        df = pd.read_html(str(tbl[-1]))[0]
        del df['Unnamed: 0']
        df.columns = ['Season', 'Club', 'Apps', 'Goals']
        df.dropna(axis=0, how='all', inplace=True)
        df.dropna(axis=0, how='any', inplace=True)

        df[['Apps', 'Subs']] = df['Apps'].str.split('(', 2, expand=True)
        df.Subs = df.Subs.str.replace(')', '').astype(int)
        df.drop_duplicates(inplace=True)
        df.index = [player_id] * len(df)

        return df

    def _get_all_player_stats(self):
        """returns complete overview and stats dataframes"""
        try:
            self.df_allStats = pd.read_csv(self.statsDir, 
                                           index_col='player_id')
            self.df_allOverview = pd.read_csv(self.overviewDir, 
                                              index_col='player_id')
        except FileNotFoundError:
            self.refresh(which='players')

    def _process_all_player_stats(self):
        """loops through index, extracts all player stats and combines"""
        first= True
        for player_id in self.df_linkingIndex.index:
            try:
                print(player_id)
                pages = self._fetch_player_stats(player_id)
                player_stats = self._extract_fields_from_stats(
                    pages['stats'], player_id)
                player_overview = self._extract_data_from_overview(
                    pages['overview'], player_id)
            except (IndexError, ValueError):
                print('error: {}'.format(player_id))
                continue
            if first:
                stats = {k:[v] for k, v in player_stats.items()}
                overview = player_overview
                first = False
            else:
                for k, v in player_stats.items():
                    stats[k].append(v)
                overview = overview.append(player_overview)
        stats = pd.DataFrame.from_records(stats, index=stats['player_id'])
        self._convert_to_csv(self.overviewDir, overview, 'player_id')
        self._convert_to_csv(self.statsDir, stats, 'player_id')
        
    def _convert_to_csv(self, fileDir, df, index_label):
        """converts dataframe to csv"""
        df.to_csv(fileDir, index_label=index_label)            


if __name__ == '__main__':
    PL = PremierData()
    assert len(PL.df_linkingIndex) > 400
    if input('Perform web scrape test (y/n)?  ') == 'y':
        page = PL._fetch_player_stats(13285)
        overview = PL._extract_data_from_overview(page['overview'], 13285)
        stats = PL._extract_fields_from_stats(page['stats'], 13285)
        assert stats['Goals'] < 2000  # avoid mixing up overview and stats

    print('Testing Complete.')








