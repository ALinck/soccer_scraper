from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Date, Integer, String, DECIMAL
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Player(Base):

    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    url = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    dob = Column(Date)
    birth_city = Column(String)
    birth_state = Column(String)
    birth_country = Column(String)
    national_team = Column(String)
    height = Column(DECIMAL)
    position = Column(String)
    number = Column(Integer)
    club_team = Column(String)

    def __init__(self, player_data):
        self.url = player_data.url
        self.first_name = player_data.first_name
        self.last_name = player_data.last_name
        self.dob = player_data.dob
        self.birth_city = player_data.birth_city
        self.birth_state = player_data.birth_state
        self.birth_country = player_data.birth_country
        self.national_team = player_data.national_team
        self.height = player_data.height if player_data.height and player_data.height > 0 else None
        self.position = player_data.position
        self.number = player_data.number
        self.club_team = player_data.club_team


def create_db():
    engine = create_engine('sqlite:///C:\\Users\\HomePC\\PycharmProjects\\soccer_scraper\\player_data.db', echo=True)
    Base.metadata.create_all(engine)

