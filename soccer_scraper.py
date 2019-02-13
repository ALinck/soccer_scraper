from urllib.parse import urljoin

from bs4 import BeautifulSoup
import requests
import urllib3

import api
import constants
import dal
import db_model
import players

# barca_url = wiki_base_url + 'FC_Barcelona'
# la_liga_url = wiki_base_url + 'La_Liga'
uefa_url = constants.WIKI_BASE_URL + 'List_of_top-division_football_clubs_in_UEFA_countries'
concacaf_url = constants.WIKI_BASE_URL + 'List_of_top-division_football_clubs_in_CONCACAF_countries'
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SQUAD_SECTIONS = ['Current_squad', 'Current_Squad', 'Current_players', 'First-team_squad', 'First_team_squad', 'Current_first-team_squad', 'Players', 'First_team', 'Squad']

data = [
    # {'name': 'UEFA', 'url': uefa_url},
    {'name': 'CONCACAF', 'url': concacaf_url}
]


class Confederation(object):
    def __init__(self):
        self.name = ''
        self.url = ''
        self.leagues = {}

    def from_dict(self, conf):
        self.name = conf['name']
        self.url = conf['url']
        return self

class Team(object):
    def __init__(self):
        self.name = ''
        self.url = ''
        self.players = []


def get_teams_by_country(session, conf_url):
    source = api.get(session, conf_url)
    page = BeautifulSoup(source, 'html.parser')
    country_tables = page.find_all('table', attrs={'class': 'wikitable'})
    teams_by_country = {}
    for country in country_tables:
        try:
            country_name = country.find_previous_sibling('h2').findNext('span').text
            team_rows = country.find_all('tr')[1:]
            teams_by_country[country_name] = _extract_teams(team_rows)
        except AttributeError:
            continue
    return teams_by_country

def _extract_teams(team_divs):
    results = []
    for td in team_divs:
        team_link = td.findNext('a')
        if team_link:
            team_name = team_link.text
            team = Team()
            team.name = team_name
            team.url = urljoin(constants.WIKI_BASE_URL, team_link.get('href'))
            results.append(team)
    return results


def get_current_squad_info(session, team):
    source = api.get(session, team.url)
    page = BeautifulSoup(source, 'html.parser')
    for id in SQUAD_SECTIONS:
        members_section = page.find('span', attrs={'id': id})
        if members_section and members_section.text:
           break
    try:
        members_table = members_section.parent.find_next_sibling('table')
        member_tables = members_table.find_all('table')
    except AttributeError:
        with open("failed_team.txt", "a", encoding='utf-8') as file:
            file.write(str(team.url) + '\n')
            return
    member_cards = [vcard for table in member_tables for vcard in table.find_all(class_='vcard agent')]
    players = get_players(member_cards)
    for player in players:
        if player.url and 'redlink' not in player.url:
            player.get_player_info(session)
        else:
            player.missing_required = True
    team.players = players


def get_players(current_squad):
    return [_extract_player_name_and_url(card) for card in current_squad]


def _extract_player_name_and_url(card):
    player = players.Player()
    tds = card.find_all('td')
    player_name = tds[3].find('span')
    player.get_first_last_name(player_name.text)
    link = player_name.find('a')
    if link:
        href = link.get('href')
        player.url = urljoin(constants.WIKI_BASE_URL, href)
    return player


def _remove_notation(str):
    result = None
    if str:
        result = str.split('[')[0]
    return result


def run():
    with requests.Session() as session:
        for conf in data:
            leagues = get_teams_by_country(session, conf['url'])
            for country in leagues.values():
                for team in country:
                    get_current_squad_info(session, team)
                    for player in team.players:
                        dal.add_player(player)
                        # if not player.missing_required:
                        #     with open("player_data.txt", "a", encoding='utf-8') as file:
                        #         file.write(str(player._to_dict()) + '\n')
                        # else:
                        #     if not player.url:
                        #         with open("no_urls.txt", "a", encoding='utf-8') as file:
                        #             file.write(str(player._to_dict()) + '\n')
                        #     else:
                        #         with open("flagged_data.txt", "a", encoding='utf-8') as file:
                        #             file.write(str(player._to_dict()) + '\n')


if __name__ == "__main__":
    db_model.create_db()
    run()





