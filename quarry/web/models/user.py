from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from base import Base


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String(255))
    wiki_uid = Column(Integer)
    queries = relationship('Query', backref='user')


class UserRepository:
    def __init__(self, session):
        self.session = session

    def get_by_id(self, id):
        return self.session.query(User).filter_by(id=id).first()

    def get_by_wiki_uid(self, wiki_uid):
        return self.session.query(User).filter_by(wiki_uid=wiki_uid).first()

    def save(self, user):
        self.session.add(user)

        # Persist the new user immediately.
        self.session.commit()

    def get_by_username(self, username):
        return self.session.query(User).filter_by(username=username).first()
