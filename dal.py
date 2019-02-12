from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db_model import Base, Player

engine = create_engine('sqlite:///C:\\Users\\HomePC\\PycharmProjects\\soccer_scraper\\player_data.db', echo=True)

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()

def add_player(player_data):
    new_player = Player(player_data)
    session.add(new_player)
    session.commit()