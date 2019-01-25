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

    def get_player_info(self):
        source = _get(self.url)
        page = BeautifulSoup(source.text, 'html.parser')
        player_card = page.find('table', class_='infobox vcard')
        self._get_birthdate(player_card)
        self._get_birthplace(player_card)
        return player

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

    def get_national_team(self, source):
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