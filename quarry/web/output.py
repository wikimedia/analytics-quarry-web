from flask import Response
import json


def get_formatted_response(format, reader, resultset_id):
    if format == 'json':
        return json_formatter(reader, resultset_id)


def json_formatter(reader, resultset_id):
    rows = list(reader.get_rows(resultset_id))
    header = rows[0]
    del rows[0]
    data = {
        'headers': header,
        'rows': rows
    }
    return Response(json.dumps(data), mimetype='application/json')
