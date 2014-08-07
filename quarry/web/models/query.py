from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from sqlalchemy.orm import relationship
from base import Base
from user import User  # noqa


class Query(Base):
    __tablename__ = 'query'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    title = Column(String(1024))
    latest_rev_id = Column('latest_rev', Integer)
    last_touched = Column(DateTime)
    parent_id = Column(Integer)

    # Stick with "rev" as common language.
    revs = relationship('QueryRevision', lazy='dynamic', backref='query')


class QueryRepository:
    def __init__(self, session):
        self.session = session

    def save(self, query):
        self.session.add(query)

        # Persist the new user immediately.
        self.session.commit()

    def get_by_id(self, id):
        return self.session.query(Query).filter_by(id=id).first()
