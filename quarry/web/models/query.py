from flask import g
from user import User
import pickle


class Query(object):
    def __init__(self, id=None, user_id=None, latest_rev_id=None, last_touched=None, title=None):
        self.id = id
        self.user_id = user_id
        self.last_touched = last_touched
        self.latest_rev_id = latest_rev_id
        self.title = title

    def serialize(self):
        return pickle.dumps({
            'id': self.id,
            'user_id': self.user_id,
            'last_touched': self.last_touched,
            'latest_rev_id': self.latest_rev_id,
            'title': self.title
        })

    @classmethod
    def unserialize(cls, json_data):
        data = pickle.loads(json_data)
        return cls(**data)

    @staticmethod
    def get_cache_key(id):
        return 'query:id:%s' % (id, )

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
        try:
            cur = g.conn.db.cursor()
            cur.execute(
                'INSERT INTO query (user_id, latest_rev, title) VALUES (%s, %s, %s)',
                (self.user_id, self.latest_rev_id, self.title)
            )
            self.id = cur.lastrowid
        finally:
            cur.close()

    def save(self):
        try:
            cur = g.conn.db.cursor()
            cur.execute(
                'UPDATE query SET latest_rev = %s, title = %s WHERE id = %s',
                (self.latest_rev_id, self.title, self.id)
            )
            g.conn.redis.delete(Query.get_cache_key(self.id))
        finally:
            cur.close()

    @classmethod
    def get_by_id(cls, id):
        query_data = g.conn.redis.get(cls.get_cache_key(id))
        if query_data:
            return Query.unserialize(query_data)
        try:
            cur = g.conn.db.cursor()
            cur.execute(
                """SELECT id, user_id, latest_rev, last_touched, title
                FROM query WHERE id = %s""",
                (id, )
            )
            result = cur.fetchone()
        finally:
            cur.close()
        if result is None:
            return None

        query = cls(result[0], result[1], result[2], result[3], result[4])
        g.conn.redis.set(cls.get_cache_key(id), query.serialize())
        return query


class QueryRevision(object):
    def __init__(self, id=None, text=None, query_id=None, timestamp=None):
        self.id = id
        self.query_id = query_id
        self.text = text
        self.timestamp = timestamp

    def serialize(self):
        return pickle.dumps({
            'id': self.id,
            'query_id': self.query_id,
            'text': self.text,
            'timestamp': self.timestamp
        })

    @classmethod
    def unserialize(cls, data):
        return cls(**pickle.loads(data))

    @staticmethod
    def get_cache_key(id):
        return "queryrev:id:%s" % (id, )

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
        queryrev_data = g.conn.redis.get(QueryRevision.get_cache_key(id))
        if queryrev_data:
            return QueryRevision.unserialize(queryrev_data)
        try:
            cur = g.conn.db.cursor()
            cur.execute(
                """SELECT id, text, query_id, timestamp
                FROM query_revision WHERE id = %s""",
                (id, )
            )
            result = cur.fetchone()
        finally:
            cur.close()
        if result is None:
            return None

        qrev = cls(result[0], result[1], result[2], result[3])
        g.conn.redis.set(QueryRevision.get_cache_key(id), qrev.serialize())
        return qrev

    def save_new(self):
        try:
            cur = g.conn.db.cursor()
            cur.execute(
                "INSERT INTO query_revision (query_id, text) VALUES ( %s, %s )",
                (self.query_id, self.text)
            )
            self.id = cur.lastrowid
        finally:
            cur.close()


class QueryRun(object):
    STATUS_QUEUED = 0
    STATUS_FAILED = 1
    STATUS_RUNNING = 2
    STATUS_KILLED = 3
    STATUS_COMPLETE = 4
    STATUS_SUPERSEDED = 5

    STATUS_MESSAGES = [
        'queued',
        'failed',
        'running',
        'killed',
        'complete',
        'superseded'
    ]

    def __init__(self, id=None, query_rev_id=None, status=None, timestamp=None, task_id=None):
        self.id = id
        self.query_rev_id = query_rev_id
        self.status = status
        self.timestamp = timestamp
        self.task_id = task_id

    def serialize(self):
        return pickle.dumps({
            'id': self.id,
            'query_rev_id': self.query_rev_id,
            'status': self.status,
            'timestamp': self.timestamp,
            'task_id': self.task_id
        })

    @classmethod
    def unserialize(self, json_data):
        return QueryRun(**pickle.loads(json_data))

    @staticmethod
    def get_cache_key(id):
        cache_key = 1
        return "queryrun:%s:id:%s" % (cache_key, id, )

    @property
    def status_message(self):
        return QueryRun.STATUS_MESSAGES[self.status]

    @classmethod
    def get_by_id(cls, id):
        qrun_data = g.conn.redis.get(QueryRun.get_cache_key(id))
        if qrun_data:
            return QueryRun.unserialize(qrun_data)
        try:
            cur = g.conn.db.cursor()
            cur.execute(
                """SELECT id, query_rev_id, status, timestamp, task_id
                FROM query_run WHERE id = %s""",
                (id, )
            )
            result = cur.fetchone()
        finally:
            cur.close()
        if result is None:
            return None

        qrun = cls(result[0], result[1], result[2], result[3], result[4])
        g.conn.redis.set(QueryRun.get_cache_key(id), qrun.serialize())
        return qrun

    def save_new(self):
        try:
            cur = g.conn.db.cursor()
            cur.execute(
                "INSERT INTO query_run (status, query_rev_id, task_id) VALUES (%s, %s, %s)",
                (self.status, self.query_rev_id, self.task_id)
            )
            self.id = cur.lastrowid
        finally:
            cur.close()

    def save(self):
        try:
            cur = g.conn.db.cursor()
            cur.execute(
                "UPDATE query_run RUN SET status=%s, task_id=%s WHERE id=%s",
                (self.status, self.task_id, self.id)
            )
            g.conn.redis.delete(QueryRun.get_cache_key(self.id))
        finally:
            cur.close()

    @property
    def query_rev(self):
        if not hasattr(self, '_query_rev'):
            self._query_rev = QueryRevision.get_by_id(self.query_rev_id)
        return self._query_rev

    @query_rev.setter
    def query_rev(self, value):
        self._query_rev = value
        self.query_rev_id = value.id

    @classmethod
    def get_latest_run(cls, query_rev_id):
        try:
            cur = g.conn.db.cursor()
            cur.execute(
                """SELECT id, query_rev_id, status, timestamp, task_id
                FROM query_run WHERE query_rev_id = %s
                ORDER BY timestamp DESC
                LIMIT 1""",
                (query_rev_id, )
            )
            result = cur.fetchone()
        finally:
            cur.close()
        if result is None:
            return None

        return cls(result[0], result[1], result[2], result[3], result[4])

    @property
    def augmented_sql(self):
        """Adds metadata to the queryrun SQL so labsdb admins can
        find out who ran the query when and for what"""
        if not hasattr(self, '_augmented_sql'):
            self._augmented_sql = "/* Run by Quarry for User %s as qrun id %s */ %s" % \
                (self.query_rev.query.user.username, self.id, self.query_rev.text)
        return self._augmented_sql

    @classmethod
    def get_augmented_list(cls, limit=25):
        results = []
        sql = """
        SELECT
            query_run.id as run_id, query_run.status as status,
            query_run.timestamp as run_timestamp,
            query_revision.id as rev_id, query_revision.text as text,
            query_revision.timestamp as rev_timestamp,
            query.id as query_id, query.user_id as user_id,
            query.last_touched as query_timestamp, query.title as query_title
        FROM
            query_run JOIN query_revision ON query_rev_id = query_revision.id
            JOIN query ON query.id = query_id
        ORDER BY
            query_run.timestamp DESC
        LIMIT %s"""
        try:
            cur = g.conn.db.cursor()
            cur.execute(sql, (limit, ))
            row = cur.fetchone()
            while row is not None:
                q_run = QueryRun(
                    id=row[0],
                    status=row[1],
                    timestamp=row[2]
                )
                q_rev = QueryRevision(
                    id=row[3],
                    text=row[4],
                    timestamp=row[5]
                )
                q = Query(
                    id=row[6],
                    user_id=row[7],
                    last_touched=row[8],
                    title=row[9]
                )
                q.latest_rev = q_rev
                q_rev.query = q
                q_run.query_rev = q_rev
                results.append(q_run)
                row = cur.fetchone()
        finally:
            cur.close()

        return results
