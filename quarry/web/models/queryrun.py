from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, desc
from sqlalchemy.orm import joinedload
from base import Base
from queryrevision import QueryRevision  # noqa


class QueryRun(Base):
    STATUS_QUEUED = 0
    STATUS_FAILED = 1
    STATUS_RUNNING = 2
    STATUS_KILLED = 3
    STATUS_COMPLETE = 4
    STATUS_SUPERSEDED = 5

    # TODO (phuedx, 2014/08/08): Make this translatable.
    STATUS_MESSAGES = [
        'queued',
        'failed',
        'running',
        'killed',
        'complete',
        'superseded'
    ]

    __tablename__ = 'query_run'

    id = Column(Integer, primary_key=True)
    query_rev_id = Column(Integer, ForeignKey('query_revision.id'))
    status = Column(Integer)
    timestamp = Column(DateTime)
    task_id = Column(String)

    @property
    def status_message(self):
        return QueryRun.STATUS_MESSAGES[self.status]

    # Stick with "augmented" as common language.
    @property
    def augmented_sql(self):
        return "/* Run by Quarry for User %s as qrun id %s */ %s" % (
            self.rev.query.user.username,
            self.id,
            self.rev.text
        )


class QueryRunRepository:
    def __init__(self, session):
        self.session = session

    def get_latest_by_rev(self, rev):
        if rev is None:
            return None

        return self.session.query(QueryRun).filter_by(query_rev_id=rev.id).first()

    def save(self, query_run):
        self.session.add(query_run)

        # Persist the query run immediately.
        self.session.commit()

    def get_latest(self, limit):

        # Eagerly load the associated query revision, query, and user.
        return self.session.query(QueryRun) \
            .options(
                joinedload('rev')
                .joinedload('query')
                .joinedload('user')
            ) \
            .filter(QueryRun.status != QueryRun.STATUS_SUPERSEDED) \
            .order_by(desc(QueryRun.timestamp)) \
            .limit(limit)

    def get_by_id(self, id):
        return self.session.query(QueryRun).filter_by(id=id).first()
