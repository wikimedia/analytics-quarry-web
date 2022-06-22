from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .base import Base


class Star(Base):
    __tablename__ = "star"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    timestamp = Column(DateTime)
    query_id = Column(Integer, ForeignKey("query.id"))

    query = relationship("Query", uselist=False)
    user = relationship("User", uselist=False)
