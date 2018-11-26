from decimal import Decimal
import itertools
from multiprocessing.dummy import Pool as ThreadPool
from time import sleep
from urllib.parse import urljoin

import dateutil.parser as parser
from bs4 import BeautifulSoup
import requests
import urllib3

wiki_base_url = 'https://en.wikipedia.org/wiki/'
# barca_url = wiki_base_url + 'FC_Barcelona'
# la_liga_url = wiki_base_url + 'La_Liga'
uefa_url = wiki_base_url + 'UEFA'
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

EN_DASH = u"\u2013"
CLUB_SECTIONS = ['Clubs', 'Serie_A_clubs', 'Current_clubs', 'Current_members', 'Teams', 'Current_teams_(2018–19)']
SQUAD_SECTIONS = ['Current_squad', 'First-team_squad', 'First_team_squad', 'Current_first-team_squad', 'Players', 'First_team']

birthplace_tuple = (None, None, None)


def get_leagues_by_confederation():
    source = _get(uefa_url)
    page = BeautifulSoup(source.text, 'html.parser')
    league_rows = page.find('span', attrs={'id': 'League_revenues'}).findNext('tbody').find_all('tr')
    league_urls = []
    for tr in league_rows:
        team_link = tr.findNext('a')
        if team_link:
            league_urls.append(urljoin(wiki_base_url, team_link.get('href')))
    return league_urls


def get_league_teams(url):
    source = _get(url)
    page = BeautifulSoup(source.text, 'html.parser')
    teams_urls = _find_teams(page)
    return teams_urls


def get_current_squad_info(team_url):
    source = _get(team_url)
    page = BeautifulSoup(source.text, 'html.parser')
    for id in SQUAD_SECTIONS:
        members_section = page.find('span', attrs={'id': id})
        if members_section and members_section.text:
           break
    members_table = members_section.parent.find_next_sibling('table')
    member_tables = members_table.find_all('table')
    member_cards = [vcard for table in member_tables for vcard in table.find_all(class_='vcard agent')]
    player_urls = get_player_urls(member_cards)
    player_data = []
    for url in player_urls:
        if 'redlink' not in url:
            player_data.append(get_player_info(url))
    return player_data


def get_player_info(player_url):
    source = _get(player_url)
    page = BeautifulSoup(source.text, 'html.parser')
    player_card = page.find('table', class_='infobox vcard')
    player = Player(player_card)
    player._source = []
    return player


def _find_teams(page):
    teams_section = _find_teams_by_stadium(page) or _find_teams_by_manager(page) or _find_teams_in_club_section(page)
    return teams_section

def _find_teams_in_club_section(page):
    teams = None
    for clubs_id in CLUB_SECTIONS:
        section = page.find('span', attrs={'id': clubs_id})
        if section: # and any(id in section['id'] for id in CLUB_SECTIONS):
            teams = section
            break

    if teams:
        teams_urls = []
        teams_rows = teams.findNext('tbody').find_all('tr')
        for tr in teams_rows:
            club_row = tr.find('td')
            if club_row:
                teams_urls.append(urljoin(wiki_base_url, club_row.find('a').get('href')))
        return teams_urls
    return None


def _find_teams_by_stadium(page):
    teams = page.find('span', attrs={'id': 'Stadiums_and_locations'})
    if teams:
        teams_urls = []
        teams_rows = teams.findNext('tbody').find_all('tr')
        for tr in teams_rows:
            td = tr.find('td')
            if td:
                teams_urls.append(urljoin(wiki_base_url, td.find('a').get('href')))
        return teams_urls
    return None

def _find_teams_by_manager(page):
    teams = page.find('caption', text='Current managers\n')
    if teams:
        teams_urls = []
        teams_rows = teams.findNext('tbody').find_all('tr')
        for tr in teams_rows:
            for td in tr.find_all('td'):
                team_link = td.findChild('a', recursive=False)
                if team_link:
                    teams_urls.append(urljoin(wiki_base_url, team_link.get('href')))
                    break
        return teams_urls
    return None

def get_player_urls(current_squad):
    player_urls = []
    for card in current_squad:
        tds = card.find_all('td')
        link = tds[3].find('span').find('a')
        if link:
            href = link.get('href')
            player_urls.append(urljoin(wiki_base_url, href))
    return player_urls


class Team(object):
    def __init__(self, current_squad):
        self.current_squad = current_squad
        self.player_urls = self.getPlayerUrls()

    def getPlayerUrls(self):
        player_urls = []
        for card in self.current_squad:
            tds = card.find_all('td')
            link = tds[3].find('span').find('a')
            if link:
                href = link.get('href')
                player_urls.append(urljoin(wiki_base_url, href))
        return player_urls


class Player(object):
    def __init__(self, player_card):
        self._source = player_card
        self.first_name, self.last_name = self.getName()
        self.dob = self.getBirthdate()
        self.birth_city, self.birth_state, self.birth_country = self.getBirthplace()
        self.national_team = self.getNationalTeam()
        self.height = self.getHeight()
        self.position = self.getPosition()
        self.number = self.getNumber()
        self.club_team = self.getCurrentTeam()

    def getBirthdate(self):
        dob = self._source.find('span', class_='bday')
        return parser.parse(dob.text).date() if dob else None

    def getName(self):
        name = self._source.find('caption').text
        name_parts = name.split()
        if len(name_parts) > 2:
            name_parts = [name_parts[0], ' '.join(name_parts[1:])]
        elif len(name_parts) == 1:
            name_parts.append(None)
        return name_parts

    def getBirthplace(self):
        birthplace_source = self._source.find('td', class_='birthplace')
        birthplace = [None, None, None]
        if birthplace_source:
            birthplace_split = birthplace_source.text.strip().split(', ')
            # Don't currently care about city districts, so this filters them out
            if birthplace_split[-1].strip().lower() not in ['mexico', 'united states'] and len(birthplace_split) > 2:
                birthplace[0], birthplace[2] = birthplace_split[1], birthplace_split[2]
            else:
                for i, item in reversed(list(enumerate(birthplace_split))):
                    birthplace[-i] = _remove_notation(item)
        return birthplace

    def getHeight(self):
        heights = self._source.find(text='Height')
        if heights:
            height = heights.findNext('td').text.strip()
            heights_split = height.replace('(', '')[:height.index(')')-1].split() if '(' in height else height.split()
            if 'm' in heights_split:
                height_m = heights_split[heights_split.index('m') - 1].replace(',', '.')
            elif 'cm' in heights_split:
                height_m = int(heights_split[heights_split.index('cm') - 1])/100
            elif 'centm' in heights_split:
                height_m = int(heights_split[heights_split.index('centm') - 1])/100
            else:
                height_m = [item.split('m')[0] for item in heights_split if 'm' in item][0]

            return Decimal(height_m)
        return None

    def getPosition(self):
        return self._source.find(text='Playing position').findNext('td').text.strip()

    def getNumber(self):
        number_header = self._source.find(text='Number')
        return int(number_header.findNext('td').text.strip().split('[')[0]) if number_header else None

    def getCurrentTeam(self):
        current_team = self._source.find(text='Current team')
        return self._source.find(text='Current team').findNext('td').text.strip() if current_team else None

    def getNationalTeam(self):
        header = self._source.find(text='National team')
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

def _remove_notation(str):
    if str and '[' in str:
        i_start = str.index('[')
        return str[:i_start]
    else:
        return str

def _get(url):
    session = requests.Session()
    response = None
    i = 3
    while i > 0:
        try:
            response = session.get(url, verify=False)
            sleep(1)
            break
        except ConnectionError:
            i -= 1
            sleep(2)
    if not i > 0:
        raise ConnectionError(f'Too many attempts to url {url}')
    return response

def multiprocess(func, iter):
    pool = ThreadPool(4)
    result = pool.map(func, iter)
    pool.close()
    pool.join()
    return [item for sublist in result for item in sublist]

# pool = ThreadPool(4)
# player_data = []
# team_urls = []
league_urls = get_leagues_by_confederation()
team_urls = multiprocess(get_league_teams, league_urls)
# for url in league_urls:
#     retrieved_urls = get_league_teams(url)
#     team_urls.extend(retrieved_urls)
#     sleep(1)
player_data = multiprocess(get_current_squad_info, team_urls)
# pool.close()
# pool.join()
# for url in team_urls:
#     player_data.extend(get_current_squad_info(url))

print(f'Found data for {len(player_data)} players on {len(team_urls)} teams in {len(league_urls)} leagues')
with open("player_data.txt", "w") as file:
    for player in player_data:
        file.write(str(player._to_dict()))





