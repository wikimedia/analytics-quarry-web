import json
import os
import sqlite3
import codecs
from datetime import datetime
from decimal import Decimal

INITIAL_SQL = """
CREATE TABLE resultsets (id, headers, rowcount)
"""


class SQLiteResultWriter(object):
    def __init__(self, qrun, path_template):
        self.qrun = qrun
        path = path_template % (qrun.rev.query.user.id, qrun.rev.query.id, qrun.id)
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        self.db = sqlite3.connect(path)
        self.db.text_factory = str
        self.db.execute(INITIAL_SQL)
        self.resultset_id = 0
        self._resultsets = []

    def _get_current_resultset_table(self):
        return u"resultset_%s" % self.resultset_id

    def start_resultset(self, columns, rowcount):
        self._resultsets.append({'headers': columns, 'rowcount': rowcount})
        sanitized_columns = [self._quote_identifier(c) for c in columns]
        table_name = self._get_current_resultset_table()
        sql = u"CREATE TABLE %s (__id__ INTEGER PRIMARY KEY, %s)" % (table_name, u', '.join(sanitized_columns))
        self.db.execute(sql)
        self.db.execute(
            u"INSERT INTO resultsets (id, headers, rowcount) VALUES (?, ?, ?)",
            (self.resultset_id, json.dumps(columns), rowcount)
        )
        self.db.commit()
        self.column_count = len(columns)
        self.cur_row_id = 0

    def add_rows(self, rows):
        table_name = self._get_current_resultset_table()
        sanitized_rows = []
        for row in rows:
            sanitized_row = []
            for c in row:
                if isinstance(c, datetime):
                    sanitized_row.append(c.isoformat())
                elif isinstance(c, str):
                    # Hack!
                    sanitized_row.append(c.decode('utf-8', errors='ignore'))
                elif isinstance(c, Decimal):
                    sanitized_row.append(float(c))
                else:
                    sanitized_row.append(c)
            sanitized_rows.append(sanitized_row)
        sql = u"INSERT INTO %s VALUES (NULL, %s)" % (table_name, (u"?," * self.column_count)[:-1])
        self.db.executemany(sql, sanitized_rows)
        self.db.commit()

    def end_resultset(self):
        self.resultset_id += 1

    def close(self):
        self.db.close()

    def get_resultsets(self):
        return self._resultsets

    def _quote_identifier(self, s, errors="ignore"):
        encodable = s.encode("utf-8", errors).decode("utf-8")

        nul_index = encodable.find("\x00")

        if nul_index >= 0:
            error = UnicodeEncodeError("utf-8", encodable, nul_index, nul_index + 1, "NUL not allowed")
            error_handler = codecs.lookup_error(errors)
            replacement, _ = error_handler(error)
            encodable = encodable.replace("\x00", replacement)

        return u'"' + encodable.replace('"', '""') + u'"'


class SQLiteResultReader(object):
    def __init__(self, qrun, path_template):
        self.qrun = qrun
        path = path_template % (qrun.rev.query.user.id, qrun.rev.query.id, qrun.id)
        self.db = sqlite3.connect(path)
        self.db.text_factory = str

    def get_resultsets(self):
        try:
            cur = self.db.cursor()
            cur.execute(u'SELECT id, headers, rowcount FROM resultsets ORDER BY id')
            rows = cur.fetchall()
            return [dict(id=r[0], headers=json.loads(r[1]), rows=r[2]) for r in rows]
        finally:
            cur.close()

    def get_rows(self, resultset_id):
        table_name = 'resultset_%d' % resultset_id
        try:
            cur = self.db.cursor()
            cur.execute(u'SELECT * FROM %s ORDER BY __id__' % table_name)
            yield [c[0] for c in cur.description[1:]]
            rows = cur.fetchmany(10)
            while rows:
                for row in rows:
                    yield row[1:]
                rows = cur.fetchmany(10)
        finally:
            cur.close()
