from decimal import Decimal
from urllib.parse import urljoin

import dateutil.parser as parser
from bs4 import BeautifulSoup
import requests
import urllib3

import api
import constants
import teams

# barca_url = wiki_base_url + 'FC_Barcelona'
# la_liga_url = wiki_base_url + 'La_Liga'
uefa_url = constants.WIKI_BASE_URL + 'UEFA'
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

EN_DASH = u"\u2013"
SQUAD_SECTIONS = ['Current_squad', 'First-team_squad', 'First_team_squad', 'Current_first-team_squad', 'Players', 'First_team']

data = {'confederations': {'name': 'UEFA', 'url': uefa_url}}

class FifaData(object):
    def __init__(self):
        self.confederations = {}

class Confederation(object):
    def __init__(self):
        self.name = 'UEFA'
        self.url = uefa_url
        self.leagues = {}

class League(object):
    def __init__(self):
        self.name = ''
        self.url = ''
        self.teams = {}


def get_leagues_by_confederation(session, confederation):
        source = api.get(session, confederation.url)
        page = BeautifulSoup(source, 'html.parser')
        league_rows = page.find('span', attrs={'id': 'League_revenues'}).findNext('tbody').find_all('tr')
        confederation.leagues = _extract_leagues(league_rows)


def _extract_leagues(league_rows):
    results = {}
    for tr in league_rows:
        league_link = tr.findNext('a')
        if league_link:
            league_name = league_link.text
            results[league_name] = League()
            results[league_name].name = league_name
            results[league_name].url = urljoin(constants.WIKI_BASE_URL, league_link.get('href'))
    return results

def get_teams_by_league(session, league):
        league.teams = _get_league_teams(session, league.url)

def _get_league_teams(session, url):
    source = api.get(session, url)
    page = BeautifulSoup(source, 'html.parser')
    return teams.get_teams(page)



def get_current_squad_info(session, team):
    source = api.get(session, team.url)
    page = BeautifulSoup(source, 'html.parser')
    for id in SQUAD_SECTIONS:
        members_section = page.find('span', attrs={'id': id})
        if members_section and members_section.text:
           break
    members_table = members_section.parent.find_next_sibling('table')
    member_tables = members_table.find_all('table')
    member_cards = [vcard for table in member_tables for vcard in table.find_all(class_='vcard agent')]
    players = get_players(member_cards)
    for player in players:
        if 'redlink' not in player.url:
            player.get_player_info(session)
    team.players = players


def get_players(current_squad):
    return [_extract_player_name_and_url(card) for card in current_squad]


def _extract_player_name_and_url(card):
    player = Player()
    tds = card.find_all('td')
    player_name = tds[3].find('span')
    player.get_first_last_name(player_name.text)
    link = player_name.find('a')
    if link:
        href = link.get('href')
        player.url = urljoin(constants.WIKI_BASE_URL, href)
    return player

class Player(object):
    def __init__(self):
        self.url = ''
        self.first_name = ''
        self.last_name = ''
        self.dob = None
        self.birth_city = ''
        self.birth_state = ''
        self.birth_country = ''
        self.national_team = ''
        self.height = None
        self.position = ''
        self.number = None
        self.club_team = ''

    def get_first_last_name(self, name):
        name_parts = name.split()
        if len(name_parts) > 2:
            self.first_name = name_parts[0]
            self.last_name = ' '.join(name_parts[1:])
        elif len(name_parts) == 1:
            self.first_name = name_parts[0]

    def get_player_info(self, session):
        source = api.get(session, self.url)
        page = BeautifulSoup(source, 'html.parser')
        player_card = page.find('table', class_='infobox vcard')
        self._get_birthdate(player_card)
        self._get_birthplace(player_card)
        self._get_height(player_card)
        self._get_number(player_card)
        self._get_position(player_card)
        self._get_current_team(player_card)
        self._get_national_team(player_card)

    def _get_birthdate(self, source):
        dob = source.find('span', class_='bday')
        if dob:
            self.dob = parser.parse(dob.text).date()

    def _get_birthplace(self, source):
        birthplace_source = source.find('td', class_='birthplace')
        birthplace = [None, None, None]
        if birthplace_source:
            birthplace_split = birthplace_source.text.strip().split(', ')
            # Don't currently care about city districts, so this filters them out
            if birthplace_split[-1].strip().lower() not in ['mexico', 'united states'] and len(birthplace_split) > 2:
                birthplace[0], birthplace[2] = birthplace_split[1], birthplace_split[2]
            else:
                for i, item in reversed(list(enumerate(birthplace_split))):
                    birthplace[-i] = _remove_notation(item)
        self.birth_city, self.birth_state, self.birth_country = birthplace

    def _get_height(self, source):
        heights = source.find(text='Height')
        if heights:
            height = heights.findNext('td').text.strip()
            heights_split = height.replace('(', '')[:height.index(')') - 1].split() if '(' in height else height.split()
            try:
                if 'm' in heights_split:
                    height_m = heights_split[heights_split.index('m') - 1].replace(',', '.')
                elif 'cm' in heights_split:
                    height_m = int(heights_split[heights_split.index('cm') - 1]) / 100
                elif 'centm' in heights_split:
                    height_m = int(heights_split[heights_split.index('centm') - 1]) / 100
                else:
                    height_m = [item.split('m')[0] for item in heights_split if 'm' in item][0]
                self.height = Decimal(height_m)
            except ValueError:
                pass

    def _get_position(self, source):
        self.position = source.find(text='Playing position').findNext('td').text.strip()

    def _get_number(self, source):
        number_header = source.find(text='Number')
        if number_header:
            self.number = int(number_header.findNext('td').text.strip().split('[')[0])

    def _get_current_team(self, source):
        current_team = source.find(text='Current team')
        if current_team:
            self.club_team = source.find(text='Current team').findNext('td').text.strip()

    def _get_national_team(self, source):
        header = source.find(text='National team')
        if header:
            next_row = header.findNext('tr')
            while next_row.find('th') and not next_row.find('th').get('colspan'):
                if next_row.text.split()[0].strip()[-1] == EN_DASH:
                    return next_row.text.split()[1].strip()
                next_row = next_row.findNext('tr')
        else:
            return None


    def _to_dict(self):
        return {
            'first_name': self.first_name,
            'last_name': self.last_name,
            'birthdate': self.dob,
            'birth_city': self.birth_city,
            'birth_state': self.birth_state,
            'birth_country': self.birth_country,
            'national_team': self.national_team,
            'height_m': self.height,
            'position': self.position,
            'number': self.number,
            'current_team': self.club_team,
        }


# class Player(object):
#     def __init__(self, player_card):
#         self._source = player_card
#         self.first_name, self.last_name = self.getName()
#         self.dob = self.getBirthdate()
#         self.birth_city, self.birth_state, self.birth_country = self.getBirthplace()
#         self.national_team = self.getNationalTeam()
#         self.height = self.getHeight()
#         self.position = self.getPosition()
#         self.number = self.getNumber()
#         self.club_team = self.getCurrentTeam()
#
#     def getBirthdate(self):
#         dob = self._source.find('span', class_='bday')
#         return parser.parse(dob.text).date() if dob else None
#
#     def getName(self):
#         name = self._source.find('caption').text
#         name_parts = name.split()
#         if len(name_parts) > 2:
#             name_parts = [name_parts[0], ' '.join(name_parts[1:])]
#         elif len(name_parts) == 1:
#             name_parts.append(None)
#         return name_parts
#
#     def getBirthplace(self):
#         birthplace_source = self._source.find('td', class_='birthplace')
#         birthplace = [None, None, None]
#         if birthplace_source:
#             birthplace_split = birthplace_source.text.strip().split(', ')
#             # Don't currently care about city districts, so this filters them out
#             if birthplace_split[-1].strip().lower() not in ['mexico', 'united states'] and len(birthplace_split) > 2:
#                 birthplace[0], birthplace[2] = birthplace_split[1], birthplace_split[2]
#             else:
#                 for i, item in reversed(list(enumerate(birthplace_split))):
#                     birthplace[-i] = _remove_notation(item)
#         return birthplace
#
#     def getHeight(self):
#         heights = self._source.find(text='Height')
#         if heights:
#             height = heights.findNext('td').text.strip()
#             heights_split = height.replace('(', '')[:height.index(')')-1].split() if '(' in height else height.split()
#             try:
#                 if 'm' in heights_split:
#                     height_m = heights_split[heights_split.index('m') - 1].replace(',', '.')
#                 elif 'cm' in heights_split:
#                     height_m = int(heights_split[heights_split.index('cm') - 1])/100
#                 elif 'centm' in heights_split:
#                     height_m = int(heights_split[heights_split.index('centm') - 1])/100
#                 else:
#                     height_m = [item.split('m')[0] for item in heights_split if 'm' in item][0]
#                 self.height = Decimal(height_m)
#             except ValueError:
#                 pass
#
#     def getPosition(self):
#         return self._source.find(text='Playing position').findNext('td').text.strip()
#
#     def getNumber(self):
#         number_header = self._source.find(text='Number')
#         return int(number_header.findNext('td').text.strip().split('[')[0]) if number_header else None
#
#     def getCurrentTeam(self):
#         current_team = self._source.find(text='Current team')
#         return self._source.find(text='Current team').findNext('td').text.strip() if current_team else None
#
#     def getNationalTeam(self):
#         header = self._source.find(text='National team')
#         if header:
#             next_row = header.findNext('tr')
#             while next_row.find('th') and not next_row.find('th').get('colspan'):
#                 if next_row.text.split()[0].strip()[-1] == EN_DASH:
#                     return next_row.text.split()[1].strip()
#                 next_row = next_row.findNext('tr')
#         else:
#             return None
#
#
#     def _to_dict(self):
#         return {
#             'first_name': self.first_name,
#             'last_name': self.last_name,
#             'birthdate': self.dob,
#             'birth_city': self.birth_city,
#             'birth_state': self.birth_state,
#             'birth_country': self.birth_country,
#             'national_team': self.national_team,
#             'height_m': self.height,
#             'position': self.position,
#             'number': self.number,
#             'current_team': self.club_team,
#         }

def _remove_notation(str):
    result = None
    if str:
        result = str.split('[')[0]
    return result


def run():
    data = FifaData()
    conf = Confederation()
    data.confederations[conf.name] = conf
    with requests.Session() as session:
        for confederation in data.confederations.values():
            get_leagues_by_confederation(session, confederation)
            for league in confederation.leagues.values():
                get_teams_by_league(session, league)
                for team in league.teams.values():
                    get_current_squad_info(session, team)
                    with open("player_data.txt", "a") as file:
                        for player in team.players:
                            file.write(str(player._to_dict()) + '\n')

    # print(f'Found data for {len(players)} players on {len(teams)} teams in {len(leagues)} leagues')
    with open("player_data.txt", "w+") as file:
        for conf in data.confederations.values():
            print(conf.name)
            for league in conf.leagues.values():
                print(league.name)
                for team in league.teams.values():
                    print(team.name)
                    for player in team.players:
                        file.write(str(player._to_dict()))

if __name__ == "__main__":
    run()





