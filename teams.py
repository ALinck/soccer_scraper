from urllib.parse import urljoin

import constants


CLUB_SECTIONS = ['Clubs', 'Serie_A_clubs', 'Current_clubs', 'Current_members', 'Teams', 'Current_teams_(2018–19)']

def get_teams(page):
    teams = {}
    section_found, teams_section = _find_teams_section(page)
    if teams_section:
        if section_found != 'manager':
            teams = _extract_teams(teams_section)
        else:
            teams = _extract_teams_by_manager(teams_section)
    return teams

def _find_teams_section(page):
    possible_teams_sections = [_find_teams_by_stadium, _find_teams_by_manager, _find_teams_in_club_section]
    for section in possible_teams_sections:
        team_section = section(page)
        if team_section:
            return team_section

def _find_teams_in_club_section(page):
    for clubs_id in CLUB_SECTIONS:
        teams_section = page.find('span', attrs={'id': clubs_id})
        if teams_section: # and any(id in section['id'] for id in CLUB_SECTIONS):
            return 'club', teams_section
        return None, teams_section


def _find_teams_by_stadium(page):
    teams_section = page.find('span', attrs={'id': 'Stadiums_and_locations'})
    if teams_section:  # and any(id in section['id'] for id in CLUB_SECTIONS):
        return 'stadium', teams_section
    return None, teams_section

def _find_teams_by_manager(page):
    teams_section = page.find('caption', text='Current managers\n')
    if teams_section:  # and any(id in section['id'] for id in CLUB_SECTIONS):
        return 'manager', teams_section
    return None, teams_section

def _extract_teams_by_manager(teams_section):
    teams = {}
    teams_rows = _get_team_rows(teams_section)
    for tr in teams_rows:
        for td in tr.find_all('td'):
            team_link = td.findChild('a', recursive=False)
            if team_link:
                team = _create_team(team_link)
                teams[team.name] = team
                break
    return teams


def _extract_teams(teams_section):
    teams = {}
    teams_rows = _get_team_rows(teams_section)
    for tr in teams_rows:
        td = tr.find('td')
        if td:
            team_link = td.find('a')
            team = _create_team(team_link)
            teams[team.name] = team
    return teams

def _create_team(team_link):
    team = Team()
    team.name = team_link.text
    team.url = urljoin(constants.WIKI_BASE_URL, team_link.get('href'))
    return team


def _get_team_rows(teams_section):
    return teams_section.findNext('tbody').find_all('tr')



class Team(object):
    def __init__(self):
        self.name = ''
        self.url = ''
        self.players = []
