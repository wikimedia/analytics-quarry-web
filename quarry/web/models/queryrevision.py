from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, desc
from sqlalchemy.orm import relationship
from base import Base
from query import Query  # noqa


class QueryRevision(Base):
    __tablename__ = 'query_revision'

    id = Column(Integer, primary_key=True)
    text = Column(String(4096))
    query_id = Column(Integer, ForeignKey('query.id'))
    timestamp = Column(DateTime)

    runs = relationship('QueryRun', lazy='dynamic', backref='rev')


class QueryRevisionRepository:
    def __init__(self, session):
        self.session = session

    def save(self, query_revision):
        self.session.add(query_revision)

        # Persist the query revision immediately.
        self.session.commit()

    def get_latest_by_query(self, query):
        return self.session.query(QueryRevision) \
            .filter_by(query_id=query.id) \
            .order_by(desc(QueryRevision.timestamp)) \
            .first()
