import json
from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime,
    String,
    UnicodeText,
)
from sqlalchemy.orm import relationship
from .base import Base
from .queryrevision import QueryRevision  # noqa


class QueryRun(Base):
    STATUS_QUEUED = 0
    STATUS_FAILED = 1
    STATUS_RUNNING = 2
    STATUS_KILLED = 3
    STATUS_COMPLETE = 4
    STATUS_SUPERSEDED = 5
    STATUS_STOPPED = 6

    # TODO (phuedx, 2014/08/08): Make this translatable.
    STATUS_MESSAGES = [
        "queued",
        "failed",
        "running",
        "killed",
        "complete",
        "superseded",
        "stopped",
    ]

    __tablename__ = "query_run"

    id = Column(Integer, primary_key=True)
    query_rev_id = Column(Integer, ForeignKey("query_revision.id"))
    status = Column(Integer)
    timestamp = Column(DateTime)
    task_id = Column(String)
    extra_info = Column(UnicodeText)

    rev = relationship(
        "QueryRevision",
        uselist=False,
        primaryjoin="QueryRevision.id == QueryRun.query_rev_id",
    )

    @property
    def status_message(self):
        return QueryRun.STATUS_MESSAGES[self.status]

    # Stick with "augmented" as common language.
    @property
    def augmented_sql(self):
        meta = {"qrun": self.id, "user": self.rev.query.user.username}
        return "/*%s*/ %s" % (json.dumps(meta), self.rev.text)

    @property
    def runningtime(self):
        return json.loads(self.extra_info or "{}").get("runningtime", "Unknown")

    def to_json(self):
        return {
            "id": self.id,
            "status": self.status_message,
            "timestamp": self.timestamp,
            "extra": json.loads(self.extra_info or "{}"),
        }
