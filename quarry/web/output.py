import csv
import itertools
import json
import types

from flask import Response, escape
from werkzeug.contrib.iterio import IterI
import xlsxwriter


def get_formatted_response(format, queryrun, reader, resultset_id):
    if format == "json":
        return json_formatter(queryrun, reader, resultset_id)
    elif format == "json-lines":
        return json_line_formatter(reader, resultset_id)
    elif format == "csv":
        return separated_formatter(reader, resultset_id, ",")
    elif format == "tsv":
        return separated_formatter(reader, resultset_id, "\t")
    elif format == "wikitable":
        return wikitable_formatter(reader, resultset_id)
    elif format == "xlsx":
        return xlsx_formatter(reader, resultset_id)
    elif format == "html":
        return html_formatter(reader, resultset_id)
    return Response("Bad file format", status=400)


class _JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, types.GeneratorType):
            try:
                first = next(o)
            except StopIteration:
                return []
            else:
                # HACK: Fake a list
                return type(
                    "_FakeList",
                    (list,),
                    {
                        "__iter__": lambda self: itertools.chain((first,), o),
                        "__bool__": lambda self: True,
                    },
                )()
        elif isinstance(o, bytes):
            return o.decode("utf-8")
        else:
            return super().default(o)


def _join_lines(gen):
    for v in gen:
        yield v
        yield "\n"


def _stringify_results(rows):
    for row in rows:
        r = list(row)
        for i, v in enumerate(r):
            if isinstance(v, bytes):
                r[i] = v.decode("utf-8")
        yield r


TEST_CSV_INJECTION_PREFIXS = "=-+@"


def _inner_csv_injection_escape(element):
    """
    Escape possible CSV injection. T209226
    """
    if not isinstance(element, (bytes, str)):
        return element

    # str to convert bytes to unicode
    if str(element).lstrip(" ").startswith("\t"):
        return element

    if element and str(element).lstrip()[0] in TEST_CSV_INJECTION_PREFIXS:
        if isinstance(element, bytes):
            return type(element)(b"\t") + element
        elif isinstance(element, str):
            return type(element)("\t") + element

    return element


def _csv_injection_escape(rows):
    for row in rows:
        r = list(row)
        for i, v in enumerate(r):
            r[i] = _inner_csv_injection_escape(v)
        yield r


def _wikitable_escape(rows):
    for row in rows:
        r = list(row)
        for i, v in enumerate(r):
            if isinstance(v, str):
                r[i] = v.replace("|", "&#124;")
            elif isinstance(v, bytes):
                r[i] = v.replace(b"|", b"&#124;")
        yield r


class _IterI(IterI):
    def write(self, s):
        if s:
            oldpos = self.pos
            super().write(s)

            # flush every 1k pos
            if (self.pos) // 1024 > oldpos // 1024:
                self.flush()


def separated_formatter(reader, resultset_id, delim=","):
    rows = _stringify_results(
        _csv_injection_escape(reader.get_rows(resultset_id))
    )

    mime_type = "text/csv" if delim == "," else "text/tab-separated-values"
    content_type = mime_type + "; charset=utf-8"

    def respond(stream):
        csvobject = csv.writer(stream, delimiter=delim)
        csvobject.writerows(rows)

    return Response(
        _IterI(respond), mimetype=mime_type, content_type=content_type
    )


def json_line_formatter(reader, resultset_id):
    rows = reader.get_rows(resultset_id)

    def respond():
        headers = None
        for row in rows:
            if headers is None:
                headers = row
                continue
            yield json.dumps(
                dict(zip(headers, row)), cls=_JSONEncoder, check_circular=False
            )

    return Response(_join_lines(respond()), mimetype="application/json")


def json_formatter(qrun, reader, resultset_id):
    rows = reader.get_rows(resultset_id)
    header = next(rows)
    data = {
        "meta": {
            "run_id": qrun.id,
            "rev_id": qrun.rev.id,
            "query_id": qrun.rev.query.id,
        },
        "headers": header,
        "rows": rows,
    }

    def respond(stream):
        json.dump(data, stream, cls=_JSONEncoder, check_circular=False)

    return Response(_IterI(respond), mimetype="application/json")


def wikitable_formatter(reader, resultset_id):
    rows = _stringify_results(_wikitable_escape(reader.get_rows(resultset_id)))
    header = next(rows)

    def respond():
        yield '{| class="wikitable"'
        yield "!" + "!!".join(map(str, header))
        for row in rows:
            yield "|-"
            yield "|" + "||".join(map(str, row))

        yield "|}"

    return Response(
        _join_lines(respond()), content_type="text/plain; charset=utf-8"
    )


def xlsx_formatter(reader, resultset_id):
    rows = _stringify_results(
        _csv_injection_escape(
            reader.get_rows(
                resultset_id,
            )
        )
    )

    def respond(stream):
        workbook = xlsxwriter.Workbook(stream, {"constant_memory": True})
        worksheet = workbook.add_worksheet()

        for row_num, row in enumerate(rows):
            for col_num, cell in enumerate(row):
                # T175285: xlsx can't do urls longer than 255 chars.
                # We first try writing it with write(), if it fails due to
                # type-specific errors (return code < -1; 0 is success and -1
                # is generic row/col dimension error), we use write_string to
                # force writing as string type, which has a max of 32767 chars.
                # This only works when cell is a string, however; so only
                # string will use fallback.
                if worksheet.write(row_num, col_num, cell) < -1 and isinstance(
                    cell, str
                ):
                    worksheet.write_string(row_num, col_num, cell)

        workbook.close()

    return Response(
        _IterI(respond),
        mimetype="application/vnd.openxmlformats-"
        "officedocument.spreadsheetml.sheet",
    )


def html_formatter(reader, resultset_id):
    rows = _stringify_results(reader.get_rows(resultset_id))
    header = next(rows)

    def respond():
        yield "<table>\n"
        yield "<tr>"
        for col in header:
            yield '<th scope="col">%s</th>' % escape(col)
        yield "</tr>\n"

        for row in rows:
            yield "<tr>"
            for col in row:
                yield "<td>%s</td>" % escape(col)
            yield "</tr>\n"

        yield "</table>"

    return Response(
        _join_lines(respond()), content_type="text/html; charset=utf-8"
    )
