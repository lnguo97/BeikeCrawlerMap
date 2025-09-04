import json
import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from .models import City


class DatabaseService:
    def __init__(self) -> None:
        db_url = os.getenv('DATABASE_URL') or 'sqlite:///data/beike_house.db'
        engine = create_engine(db_url)
        self.Session = sessionmaker(bind=engine)

    def load_city_info(self) -> None:
        with self.Session() as session:
            if session.query(City.id).count() > 0:
                return
            with open('data/city_list.json') as f:
                city_list = json.load(f)
            for city in city_list:
                session.add(City(**city))
            session.commit()

    

