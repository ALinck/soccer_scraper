from bs4 import BeautifulSoup
import requests

barca_url = 'https://en.wikipedia.org/wiki/FC_Barcelona'

def get_team_members():
    source = requests.get(barca_url, verify=False)
    page = BeautifulSoup(source.text)
    members_section = page.find('span', attrs={'id': 'Current_squad'}).parent
    members_table = members_section.find_next_sibling('table')
    member_tables = members_table.find_all('table')
    member_cards = [vcard for table in member_tables for vcard in table.find_all(class_='vcard agent')]

    players = []
    for card in member_cards:
        player = Player()
        items = card.find_all('td')
        player.number = items[0].text
        player.nationality = items[1].span.a['title']
        player.position = items[2].text
        player.name = items[3].text.split('(')[0].strip()

        players.append(player)

def get_player_info(player_url='https://en.wikipedia.org/wiki/Lionel_Messi', player=None):
    source = requests.get(player_url, verify=False)
    page = BeautifulSoup(source.text)
    player_card = page.find('table', class_='infobox vcard')
    player.dob = player_card.find('span', class_='bday').text



class Player(object):
    def __init(self):
        self.name = None
        self.dob = None
        self.birth_city = None
        self.birth_country = None
        self.nationality = None
        self.height = None
        self.position = None
        self.number = None
        self.club_team = None




get_player_info(player=Player())




