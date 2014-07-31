from flask import g
import pickle


class User(object):
    def __init__(self, id=None, username=None, wiki_uid=None):
        self.id = id
        self.username = username
        self.wiki_uid = wiki_uid

    def serialize(self):
        return pickle.dumps({
            'id': self.id,
            'username': self.username,
            'wiki_uid': self.wiki_uid
        })

    @classmethod
    def unserialize(cls, json_data):
        data = pickle.loads(json_data)
        return cls(data['id'], data['username'], data['wiki_uid'])

    @staticmethod
    def get_cache_key(id):
        cache_version = 1
        return 'user:id:%s:%s' % (cache_version, id, )

    @classmethod
    def get_by_wiki_uid(cls, wiki_uid):
        try:
            cur = g.conn.cursor()
            cur.execute(
                'SELECT id, username, wiki_uid FROM user WHERE wiki_uid=%s',
                (wiki_uid, )
            )
            result = cur.fetchone()
        finally:
            cur.close()
        if result is None:
            return None
        user = cls(result[0], result[1], result[2])
        return user

    @classmethod
    def get_by_id(cls, id):
        user_data = g.redis.get(cls.get_cache_key(id))
        if user_data:
            return User.unserialize(user_data)
        try:
            cur = g.conn.cursor()
            cur.execute(
                'SELECT id, username, wiki_uid FROM user WHERE id=%s',
                (id, )
            )
            result = cur.fetchone()
        finally:
            cur.close()
        if result is None:
            return None
        user = cls(result[0], result[1], result[2])
        g.redis.set(cls.get_cache_key(id), user.serialize())
        return user

    def save_new(self):
        try:
            cur = g.conn.cursor()
            cur.execute(
                """INSERT INTO user (username, wiki_uid) VALUES (%s, %s)""",
                (self.username, self.wiki_uid)
            )
            self.id = cur.lastrowid
        finally:
            cur.close()
