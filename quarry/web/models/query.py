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
