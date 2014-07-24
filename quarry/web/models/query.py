from flask import g
from user import User


class Query(object):
    def __init__(self, id=None, user_id=None, latest_rev_id=None, last_touched=None):
        self.id = id
        self.user_id = user_id
        self.last_touched = last_touched
        self.latest_rev_id = latest_rev_id

    @property
    def user(self):
        if not hasattr(self, '_user'):
            self._user = User.get_by_id(self.user_id)
        return self._user

    @user.setter
    def user(self, user):
        self._user = user
        self.user_id = user.id

    @property
    def latest_rev(self):
        if not hasattr(self, '_latest_rev'):
            self._latest_rev = QueryRevision.get_by_id(self.latest_rev_id)
        return self._latest_rev

    @latest_rev.setter
    def latest_rev(self, latest_rev):
        self._latest_rev = latest_rev
        self.latest_rev_id = latest_rev.id

    def save_new(self):
        with g.conn.cursor() as cur:
            cur.execute(
                'INSERT INTO query (user_id, latest_rev) VALUES (?, ?)',
                (self.user_id, self.latest_rev_id)
            )
            self.id = cur.lastrowid

    def save(self):
        with g.conn.cursor() as cur:
            cur.execute(
                'UPDATE query SET latest_rev = ? WHERE id = ?',
                (self.latest_rev_id, self.id)
            )

    @classmethod
    def get_by_id(cls, id):
        with g.conn.cursor() as cur:
            cur.execute(
                """SELECT id, user_id, latest_rev, last_touched
                FROM query WHERE id = ?""",
                (id, )
            )
            result = cur.fetchone()
        if result is None:
            return None

        return cls(result[0], result[1], result[2], result[3])


class QueryRevision(object):
    def __init__(self, id=None, text=None, query_id=None, timestamp=None):
        self.id = id
        self.query_id = query_id
        self.text = text
        self.timestamp = timestamp

    @property
    def query(self):
        if not hasattr(self, '_query'):
            self._query = Query.get_by_id(self.query_id)
        return self._query

    @query.setter
    def query(self, value):
        self._query = value
        self.query_id = value.id

    @classmethod
    def get_by_id(cls, id):
        with g.conn.cursor() as cur:
            cur.execute(
                """SELECT id, text, query_id, timestamp
                FROM query_revision WHERE id = ?""",
                (id, )
            )
            result = cur.fetchone()
        if result is None:
            return None

        return cls(result[0], result[1], result[2], result[3])

    def save_new(self):
        with g.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO query_revision (query_id, text) VALUES ( ?, ? )",
                (self.query_id, self.text)
            )
            self.id = cur.lastrowid
