import pymysql
import redis
from sqlalchemy import create_engine


class Connections(object):
    def __init__(self, config):
        self.config = config

    @property
    def db_engine(self):
        if not hasattr(self, '_db_engine'):
            url = "mysql+pymysql://%s:%s@%s/%s" % (
                self.config['DB_USER'],
                self.config['DB_PASSWORD'],
                self.config['DB_HOST'],
                self.config['DB_NAME'],
            )

            # By default, encoding (charset above) is 'utf-8'.
            self._db_engine = create_engine(url)

        return self._db_engine

    @property
    def redis(self):
        if not hasattr(self, '_redis'):
            self._redis = redis.StrictRedis(
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
