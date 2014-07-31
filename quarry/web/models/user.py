from flask import g
import pickle


class User(object):
    def __init__(self, id=None, username=None, wiki_id=None):
        self.id = id
        self.username = username
        self.wiki_id = wiki_id

    def serialize(self):
        return pickle.dumps({
            'id': self.id,
            'username': self.username,
            'wiki_id': self.wiki_id
        })

    @classmethod
    def unserialize(cls, json_data):
        data = pickle.loads(json_data)
        return cls(data['id'], data['username'], data['wiki_id'])

    @staticmethod
    def get_cache_key(id):
        cache_version = 1
        return 'user:id:%s:%s' % (cache_version, id, )

    @classmethod
    def get_by_wiki_id(cls, wiki_id):
        try:
            cur = g.conn.cursor()
            cur.execute(
                'SELECT id, username, wiki_id FROM user WHERE wiki_id=%s',
                (wiki_id, )
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
                'SELECT id, username, wiki_id FROM user WHERE id=%s',
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
                """INSERT INTO user (username, wiki_id) VALUES (%s, %s)""",
                (self.username, self.wiki_id)
            )
            self.id = cur.lastrowid
        finally:
            cur.close()
