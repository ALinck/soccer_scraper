from decimal import Decimal
import re

import dateutil.parser as parser
from bs4 import BeautifulSoup

import api

EN_DASH = u"\u2013"


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
        self.missing_required = False

    def get_first_last_name(self, name):
        name_parts = name.split()
        if len(name_parts) > 1:
            self.first_name = name_parts[0]
            self.last_name = ' '.join(name_parts[1:])
        else:
            self.first_name = name_parts[0]

    def get_player_info(self, session):
        source = api.get(session, self.url)
        page = BeautifulSoup(source, 'html.parser')
        player_card = page.find('table', class_='infobox vcard')
        if player_card:
            try:
                self._get_birthdate(player_card)
                self._get_birthplace(player_card)
                self._get_height(player_card)
                self._get_number(player_card)
                self._get_position(player_card)
                self._get_current_team(player_card)
                self._get_national_team(player_card)
                self._check_required_fields()
            except:
                self.missing_required = True

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
                    birthplace[-i] = self._remove_notation(item)
        self.birth_city, self.birth_state, self.birth_country = birthplace

    def _remove_notation(self, str):
        result = None
        if str:
            result = str.split('[')[0]
        return result

    def _get_height(self, source):
        heights = source.find(text='Height')
        if heights:
            height = heights.findNext('td').text.strip()
            try:
                find_height = re.compile('[12]\.\d{2}')
                found_height = find_height.search(height).group()
                self.height = Decimal(found_height)
            except:
                heights_split = height.replace('(', '')[:height.index(')') - 1].split() if '(' in height else height.split()
                try:
                    if 'm' in heights_split:
                        height_m = heights_split[heights_split.index('m') - 1].split('[')[0].replace(',', '.')
                    elif 'cm' in heights_split:
                        height_m = int(heights_split[heights_split.index('cm') - 1]) / 100
                    elif 'centm' in heights_split:
                        height_m = int(heights_split[heights_split.index('centm') - 1].split('[')[0]) / 100
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
            try:
                self.number = int(number_header.findNext('td').text.strip().split('[')[0])
            except ValueError:
                pass

    def _get_current_team(self, source):
        current_team = source.find(text='Current team')
        if current_team:
            club_team = source.find(text='Current team').findNext('td').text.strip().split('(')[0]
            self.club_team = club_team

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

    def _check_required_fields(self):
        required_fields = [
            self.first_name,
            self.dob,
            self.birth_country,
            self.height,
            self.position,
            self.number,
            self.club_team
        ]
        for item in required_fields:
            if not item:
                self.missing_required = True
                break


    def _to_dict(self):
        result = {
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
        return result