from flask import Response
import json
import unicodecsv


def get_formatted_response(format, reader, resultset_id):
    if format == 'json':
        return json_formatter(reader, resultset_id)
    elif format == 'csv':
        return separated_formatter(reader, resultset_id, ',')
    elif format == 'tsv':
        return separated_formatter(reader, resultset_id, "\t")


class OneLineRetainer(object):
    def __init__(self):
        self.last_written = None

    def write(self, value):
        self.last_written = value


def separated_formatter(reader, resultset_id, delim=','):
    rows = reader.get_rows(resultset_id)
    retainer = OneLineRetainer()
    writer = unicodecsv.writer(retainer, delimiter=delim)

    def respond():
        for row in rows:
            writer.writerow(row)
            yield retainer.last_written

    return Response(respond(), content_type='text/csv')


def json_formatter(reader, resultset_id):
    rows = list(reader.get_rows(resultset_id))
    header = rows[0]
    del rows[0]
    data = {
        'headers': header,
        'rows': rows
    }
    return Response(json.dumps(data), mimetype='application/json')
