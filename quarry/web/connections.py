import pymysql
import redis


class Connections(object):
    def __init__(self, config):
        self.config = config

    @property
    def db(self):
        if not hasattr(self, '_db'):
            self._db = pymysql.connect(
                host=self.config['DB_HOST'],
                db=self.config['DB_NAME'],
                user=self.config['DB_USER'],
                passwd=self.config['DB_PASSWORD'],
                autocommit=True,
                charset='utf8'
            )
        else:
            self._db.ping(reconnect=True)
        return self._db

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
        if hasattr(self, '_db'):
            self._db.close()
        if hasattr(self, '_replica'):
            self._replica.close()
