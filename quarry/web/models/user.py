from sqlalchemy import Column, Integer, Unicode
from sqlalchemy.orm import relationship
from base import Base


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(Unicode(255))
    wiki_uid = Column(Integer)
    queries = relationship('Query', backref='user')
