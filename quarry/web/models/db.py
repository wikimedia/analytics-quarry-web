from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Model = declarative_base()

engine = create_engine('sqlite:////tmp/hello', echo=True)
Session = sessionmaker(engine)
session = Session()
