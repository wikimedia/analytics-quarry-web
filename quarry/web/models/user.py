from sqlalchemy import Column, Integer, Unicode, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(Unicode(255))
    wiki_uid = Column(Integer)
    queries = relationship('Query', backref='user')

    groups = relationship('UserGroup', backref='user')


class UserGroup(Base):
    __tablename__ = 'user_group'
    """
    Currently used groups:
    - sudo: can become any user
    - blocked: can't run queries
    """
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    group_name = Column(Unicode(255))
