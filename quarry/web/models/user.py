from sqlalchemy import Column, Integer, String
import db


class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))

    def __repr__(self):
        return '<User(id=%d, name="%s")' % (
            self.id, self.name
        )
