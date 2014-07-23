from flask import g


class User(object):
    def __init__(self, id, username):
        self.id = id
        self.username = username

    @classmethod
    def get_by_id(cls, id):
        with g.conn.cursor() as cur:
            cur.execute(
                'SELECT id, username FROM user WHERE id=?',
                (id, )
            )
            result = cur.fetchone()
        if result is None:
            return None
        return cls(result[0], result[1])

    @classmethod
    def save(cls, user):
        with g.conn.cursor() as cur:
            cur.execute(
                """INSERT INTO user (id, username) VALUES (?, ?)
                ON DUPLICATE KEY UPDATE username=?""",
                (user.id, user.username, user.username)
            )
