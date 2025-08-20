import pathlib

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base


def connect_databse(db_file: str) -> sessionmaker:
    db_file_path = pathlib.Path(db_file)
    if not db_file_path.parent.exists():
        raise FileNotFoundError(
            f'Database folder {db_file_path.parent} not found'
        )
    engine = create_engine(f'sqlite:///{db_file}')
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)
