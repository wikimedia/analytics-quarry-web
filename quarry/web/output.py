import json

from flask import Response

from StringIO import StringIO
import unicodecsv
import xlsxwriter


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


def json_line_formatter(reader, resultset_id):
    rows = reader.get_rows(resultset_id)

    def respond():
        headers = None
        for row in rows:
            if headers is None:
                headers = row
                continue
            yield json.dumps(dict(zip(headers, row))) + "\n"

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


def _stringfy(data, encoding='utf-8'):
    if isinstance(data, unicode):
        return data.encode(encoding)
    elif isinstance(data, str):
        return data
    else:
        return str(data)


def wikitable_formatter(reader, resultset_id):
    rows = list(reader.get_rows(resultset_id))
    header = rows[0]
    del rows[0]

    def respond():
        yield '{| class="wikitable"'
        yield '!' + '!!'.join(map(_stringfy, header))

        for row in rows:
            yield '|-'
            yield '|' + '||'.join(map(_stringfy, row))

        yield '|}'

    return Response('\n'.join(list(respond())),
                    content_type='text/plain; charset=utf-8')


def xlsx_formatter(reader, resultset_id):
    rows = reader.get_rows(resultset_id)

    output = StringIO()
    workbook = xlsxwriter.Workbook(output, {'constant_memory': True})
    worksheet = workbook.add_worksheet()

    for row_num, row in enumerate(rows):
        for col_num, cell in enumerate(row):
            if isinstance(cell, str):
                # xlsxwriter expects unicode, but just in case the input is
                # somehow not UTF-8, we replace them to not get an UnicodeError
                # from within xlsxwriter.
                cell = cell.decode('utf-8', 'replace')
            # T175285: xlsx can't do urls longer than 255 chars.
            # We first try writing it with write(), if it fails due to
            # type-specific errors (return code < -1; 0 is success and -1 is
            # generic row/col dimension error), we use write_string to force
            # writing as string type, which has a max of 32767 chars.
            # This only works when cell is a string, however; so only string
            # will use fallback.
            if (worksheet.write(row_num, col_num, cell) < -1 and
                    isinstance(cell, basestring)):
                worksheet.write_string(row_num, col_num, cell)

    workbook.close()
    output.seek(0)

    return Response(output.read(),
                    mimetype='application/vnd.openxmlformats-'
                             'officedocument.spreadsheetml.sheet')
