from decimal import Decimal
from urllib.parse import urljoin
import urllib3

import dateutil.parser as parser
from bs4 import BeautifulSoup
import requests

barca_url = 'https://en.wikipedia.org/wiki/FC_Barcelona'
wiki_base_url = 'https://en.wikipedia.org/wiki/'
players = ['Lionel_Messi', 'Tim_Howard']

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_current_squad_info():
    source = requests.get(barca_url, verify=False)
    page = BeautifulSoup(source.text)
    members_section = page.find('span', attrs={'id': 'Current_squad'}).parent
    members_table = members_section.find_next_sibling('table')
    member_tables = members_table.find_all('table')
    member_cards = [vcard for table in member_tables for vcard in table.find_all(class_='vcard agent')]
    team = Team(member_cards)
    player_data = []
    for url in team.player_urls:
        player_data.append(get_player_info(url))
    return player_data



def get_player_info(player_url):
    source = requests.get(player_url, verify=False)
    page = BeautifulSoup(source.text)
    player_card = page.find('table', class_='infobox vcard')
    player = Player(player_card)
    return player

class Team(object):
    def __init__(self, current_squad):
        self.current_squad = current_squad
        self.player_urls = self.getPlayerUrls();

    def getPlayerUrls(self):
        player_urls = []
        for card in self.current_squad:
            tds = card.find_all('td')
            href = tds[3].find('a').get('href')
            player_urls.append(urljoin(wiki_base_url, href))
        return player_urls


class Player(object):
    def __init__(self, player_card):
        self._source = player_card
        self.first_name, self.last_name = self.getName()
        self.dob = self.getBirthdate()
        self.birth_city, self.birth_state, self.birth_country = self.getBirthplace()
        self.nationality = self.birth_country
        self.height = self.getHeight()
        self.position = self.getPosition()
        self.number = self.getNumber()
        self.club_team = self.getCurrentTeam()

    def getBirthdate(self):
        dob = self._source.find('span', class_='bday').text
        return parser.parse(dob).date() if dob else None

    def getName(self):
        name = self._source.find('caption').text
        name_parts = name.split()
        # for i, part in enumerate(name_parts):
        #     if part[0].islower():
        #         name_parts[i] = name_parts[i] + ' ' + name_parts[i+1]
        #         name_parts.remove(name_parts[i+1])
        if len(name_parts) > 2:
            name_parts = [name_parts[0], ' '.join(name_parts[1:])]
        elif len(name_parts) == 1:
            name_parts.append(None)
        return name_parts

    def getBirthplace(self):
        birthplace = self._source.find('td', class_='birthplace').text
        birthplace_split = birthplace.strip().split(', ')
        if len(birthplace_split) < 3:
            birthplace_split.insert(1, None)
        return birthplace_split

    def getHeight(self):
        heights = self._source.find(text='Height').findNext('td').text
        heights_split = heights.replace('(', '')[:heights.index(')')-1].split()
        return Decimal(heights_split[heights_split.index('m') - 1])

    def getPosition(self):
        return self._source.find(text='Playing position').findNext('td').text.strip()

    def getNumber(self):
        return int(self._source.find(text='Number').findNext('td').text)

    def getCurrentTeam(self):
        return self._source.find(text='Current team').findNext('td').text.strip()

    def _to_dict(self):
        return {
            'first_name': self.first_name,
            'last_name': self.last_name,
            'birthdate': self.dob,
            'birth_city': self.birth_city,
            'birth_state': self.birth_state,
            'birth_country': self.birth_country,
            'nationality': self.nationality,
            'height_m': self.height,
            'position': self.position,
            'number': self.number,
            'current_team': self.club_team,
        }


# player_data = []
# for player in players:
#     player_info = get_player_info(wiki_base_url + player)
#     player_data.append(player_info._to_dict())
player_data = get_current_squad_info()
for player in player_data:
    print(player._to_dict())

# print(player_data)




