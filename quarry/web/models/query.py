from sqlalchemy import Column, Integer, ForeignKey, Unicode, DateTime, Boolean, UnicodeText
from sqlalchemy.orm import relationship
from .base import Base
from .user import User  # noqa


class Query(Base):
    __tablename__ = 'query'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    title = Column(Unicode(1024))
    last_touched = Column(DateTime)
    parent_id = Column(Integer, ForeignKey('query.id'))
    latest_rev_id = Column(Integer, ForeignKey('query_revision.id'))
    published = Column(Boolean, default=False)
    description = Column(UnicodeText)

    # Stick with "rev" as common language.
    revs = relationship('QueryRevision',
                        lazy='dynamic',
                        primaryjoin='Query.id == QueryRevision.query_id',
                        backref='query')
    latest_rev = relationship('QueryRevision',
                              primaryjoin='Query.latest_rev_id == QueryRevision.id',
                              uselist=False)
    parent = relationship('Query',
                          remote_side=[id],
                          uselist=False)

    def to_json(self):
        return {
            'id': self.id,
            'author': self.user.username,
            'title': self.title,
            'timestamp': self.last_touched,
            'parent': self.parent_id,
            'latest_revision': self.latest_rev.id,
            'published': bool(self.published),
            'description': self.description,
        }
