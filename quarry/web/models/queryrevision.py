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
    latest_run_id = Column(Integer, ForeignKey('query_run.id'))

    latest_run = relationship('QueryRun', primaryjoin='QueryRevision.latest_run_id == QueryRun.id', uselist=False)

    def is_allowed(self):
        """Check if given SQL is ok to execute.
        Super minimal and stupid right now, and should never
        be considered 'authoritative'. Will probably always be
        easily cirumventible by dedicated trolls, but should keep
        the merely clueless out

        returns tuple of (actual_reason, public_reason_string)
        """
        if 'information_schema' in self.text.lower():
            # According to springle hitting this db can fuck
            # things up for everyone, and it isn't easy to
            # restrict access to this from mysql
            return ("Hitting information_schema", "Unauthorized access to restricted database")
        return True


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
