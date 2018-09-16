import json

from flask import Response, escape

from io import BytesIO
import xlsxwriter
import csv


def get_formatted_response(format, queryrun, reader, resultset_id):
    if format == 'json':
        return json_formatter(queryrun, reader, resultset_id)
    elif format == 'json-lines':
        return json_line_formatter(reader, resultset_id)
    elif format == 'csv':
        return separated_formatter(reader, resultset_id, ',')
    elif format == 'tsv':
        return separated_formatter(reader, resultset_id, "\t")
    elif format == 'wikitable':
        return wikitable_formatter(reader, resultset_id)
    elif format == 'xlsx':
        return xlsx_formatter(reader, resultset_id)
    elif format == 'html':
        return html_formatter(reader, resultset_id)
    return Response('Bad file format', status=400)


class MultipleLinesRetainer(object):  # TODO: generator ?
    def __init__(self):
        self.content = ''

    def write(self, value):
        self.content += value


def separated_formatter(reader, resultset_id, delim=','):
    rows = reader.get_rows(resultset_id)
    retainer = MultipleLinesRetainer()
    csvobject = csv.writer(retainer)
    csvobject.writerows(rows)

    return Response(retainer.content, content_type='text/csv')


def json_line_formatter(reader, resultset_id):
    rows = reader.get_rows(resultset_id)

    def respond():
        headers = None
        for row in rows:
            if headers is None:
                headers = row
                continue
            yield json.dumps(dict(list(zip(headers, row)))) + "\n"

    return Response(respond(), content_type='application/json')


def json_formatter(qrun, reader, resultset_id):
    rows = list(reader.get_rows(resultset_id))
    header = rows[0]
    del rows[0]
    data = {
        'meta': {
            'run_id': qrun.id,
            'rev_id': qrun.rev.id,
            'query_id': qrun.rev.query.id,
        },
        'headers': header,
        'rows': rows
    }
    return Response(json.dumps(data),
                    mimetype='application/json')


def wikitable_formatter(reader, resultset_id):
    rows = list(reader.get_rows(resultset_id))
    header = rows[0]
    del rows[0]

    def respond():
        yield '{| class="wikitable"'
        yield '!' + '!!'.join(map(str, header))

        for row in rows:
            yield '|-'
            yield '|' + '||'.join(map(str, row))

        yield '|}'

    return Response('\n'.join(list(respond())),
                    content_type='text/plain; charset=utf-8')


def xlsx_formatter(reader, resultset_id):
    rows = reader.get_rows(resultset_id)

    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()

    for row_num, row in enumerate(rows):
        for col_num, cell in enumerate(row):
            # T175285: xlsx can't do urls longer than 255 chars.
            # We first try writing it with write(), if it fails due to
            # type-specific errors (return code < -1; 0 is success and -1 is
            # generic row/col dimension error), we use write_string to force
            # writing as string type, which has a max of 32767 chars.
            # This only works when cell is a string, however; so only string
            # will use fallback.
            if (worksheet.write(row_num, col_num, cell) < -1 and
                    isinstance(cell, str)):
                worksheet.write_string(row_num, col_num, cell)

    workbook.close()
    output.seek(0)

    return Response(output.read(),
                    mimetype='application/vnd.openxmlformats-'
                             'officedocument.spreadsheetml.sheet')


def html_formatter(reader, resultset_id):
    rows = list(reader.get_rows(resultset_id))
    header = rows[0]
    del rows[0]

    def respond():
        yield '<table>\n'
        yield '<tr>'
        for col in header:
            yield '<th scope="col">%s</th>' % escape(col)
        yield'</tr>\n'

        for row in rows:
            yield '<tr>'
            for col in row:
                yield '<td>%s</td>' % escape(col)
            yield'</tr>\n'

        yield '</table>'

    return Response('\n'.join(list(respond())),
                    content_type='text/html; charset=utf-8')
