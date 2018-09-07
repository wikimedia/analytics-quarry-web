import pymysql
import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session


class Connections(object):
    def __init__(self, config):
        self.config = config

    @property
    def db_engine(self):
        if not hasattr(self, '_db_engine'):
            url = "mysql+pymysql://%s:%s@%s/%s?charset=utf8" % (
                self.config['DB_USER'],
                self.config['DB_PASSWORD'],
                self.config['DB_HOST'],
                self.config['DB_NAME'],
            )

            # Recycle connections after 10 mins, since mysql does not
            # like it otherwise
            self._db_engine = create_engine(url, pool_recycle=600)

        return self._db_engine

    @property
    def session(self):
        if not hasattr(self, '_session'):
            self._session = scoped_session(
                sessionmaker(bind=self.db_engine)
            )
        return self._session

    @property
    def redis(self):
        if not hasattr(self, '_redis'):
            self._redis = redis.Redis(
                host=self.config['REDIS_HOST'],
                port=self.config['REDIS_PORT'],
                db=self.config['REDIS_DB']
            )
        return self._redis

    @property
    def replica(self):
        if not hasattr(self, '_replica'):
            self._replica = pymysql.connect(
                host=self.config['REPLICA_HOST'],
                db=self.config['REPLICA_DB'],
                user=self.config['REPLICA_USER'],
                passwd=self.config['REPLICA_PASSWORD'],
                port=self.config['REPLICA_PORT'],
                charset='utf8'
            )
        else:
            self._replica.ping(reconnect=True)
        return self._replica

    def close_all(self):
        # Redis doesn't need to be closed
        if hasattr(self, '_replica'):
            self._replica.close()
        if hasattr(self, '_session'):
            self._session.close()
        if hasattr(self, '_db_engine'):
            self._db_engine.dispose()

    def close_session(self):
        if hasattr(self, '_session'):
            self._session.close()
            del self._session
