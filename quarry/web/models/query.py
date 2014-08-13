from sqlalchemy import Column, Integer, ForeignKey, Unicode, DateTime
from sqlalchemy.orm import relationship
from base import Base
from user import User  # noqa


class Query(Base):
    __tablename__ = 'query'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    title = Column(Unicode(1024))
    last_touched = Column(DateTime)
    parent_id = Column(Integer)
    latest_rev_id = Column(Integer, ForeignKey('query_revision.id'))

    # Stick with "rev" as common language.
    revs = relationship('QueryRevision',
                        lazy='dynamic',
                        primaryjoin='Query.id == QueryRevision.query_id',
                        backref='query')
    latest_rev = relationship('QueryRevision',
                              primaryjoin='Query.latest_rev_id == QueryRevision.id',
                              uselist=False)


class QueryRepository:
    def __init__(self, session):
        self.session = session

    def save(self, query):
        self.session.add(query)

        # Persist the new user immediately.
        self.session.commit()

    def get_latest(self, limit):
        # Eagerly load the associated query revision, query, and user.
        return self.session.query(Query).limit(limit)

    def get_by_id(self, id):
        return self.session.query(Query).filter_by(id=id).first()
