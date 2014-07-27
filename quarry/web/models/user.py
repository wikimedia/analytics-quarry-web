from flask import g


class User(object):
    def __init__(self, id, username):
        self.id = id
        self.username = username

    @classmethod
    def get_by_id(cls, id):
        try:
            cur = g.conn.cursor()
            cur.execute(
                'SELECT id, username FROM user WHERE id=%s',
                (id, )
            )
            result = cur.fetchone()
        finally:
            cur.close()
        if result is None:
            return None
        return cls(result[0], result[1])

    def save(self):
        try:
            cur = g.conn.cursor()
            cur.execute(
                """INSERT INTO user (id, username) VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE username=%s""",
                (self.id, self.username, self.username)
            )
        finally:
            cur.close()
