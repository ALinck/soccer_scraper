from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import constants
from db_model import Base, Player

engine = create_engine(constants.DB_ENGINE, echo=True)

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()

def add_player(player_data):
    new_player = Player(player_data)
    session.add(new_player)
    session.commit()