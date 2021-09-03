from flask import Response


from quarry.web import output


class fake_reader:
    def listGenerator(lines):
        for line in lines:
            yield line

    def get_rows(self, _resultset_id):
        return fake_reader.listGenerator(
            [
                ["id", "text", "query_database", "query_id"],
                (1, "show tables;", "quarry", 2),
                (2, "select * from query_revision;", "quarry", 5),
            ]
        )


class fake_query:
    id = "fakequery"


class fake_rev:
    id = "fakerev"
    query = fake_query()


class fake_qrun:
    id = ("mockrun",)
    rev = fake_rev()


# Test different formats in get_formatted_response
def test_json():
    reader = fake_reader()
    qrun = fake_qrun()
    formatted_as_json = output.get_formatted_response(
        "json", qrun, reader, "fake_resultset_id"
    )

    assert type(formatted_as_json) is Response
    assert list(formatted_as_json.iter_encoded()) == [
        b'{"meta": {"run_id": ["mockrun"], "rev_id": "fakerev", "query_id": "fakequery"}, "headers": ["id", "text", "query_database", "query_id"], "rows": [[1, "show tables;", "quarry", 2], [2, "select * from query_revision;", "quarry", 5]]}'  # noqa: E501
    ]


def test_json_lines():
    reader = fake_reader()
    qrun = fake_qrun()
    formatted_as_json_lines = output.get_formatted_response(
        "json-lines", qrun, reader, "fake_resultset_id"
    )

    assert type(formatted_as_json_lines) is Response
    assert list(formatted_as_json_lines.iter_encoded()) == [
        b'{"id": 1, "text": "show tables;", "query_database": "quarry", "query_id": 2}',
        b"\n",
        b'{"id": 2, "text": "select * from query_revision;", "query_database": "quarry", "query_id": 5}',
        b"\n",
    ]  # noqa E501


def test_csv():
    reader = fake_reader()
    qrun = fake_qrun()
    formatted_as_csv = output.get_formatted_response(
        "csv", qrun, reader, "fake_resultset_id"
    )

    assert type(formatted_as_csv) is Response
    assert list(formatted_as_csv.iter_encoded()) == [
        b"id,text,query_database,query_id\r\n1,show tables;,quarry,2\r\n2,select * from query_revision;,quarry,5\r\n"
    ]  # noqa: E501


def test_tsv():
    reader = fake_reader()
    qrun = fake_qrun()
    formatted_as_tsv = output.get_formatted_response(
        "tsv", qrun, reader, "fake_resultset_id"
    )

    assert type(formatted_as_tsv) is Response
    assert list(formatted_as_tsv.iter_encoded()) == [
        b"id\ttext\tquery_database\tquery_id\r\n1\tshow tables;\tquarry\t2\r\n2\tselect * from query_revision;\tquarry\t5\r\n"  # noqa: E501
    ]


def test_wikitable():
    reader = fake_reader()
    qrun = fake_qrun()
    formatted_as_wikitable = output.get_formatted_response(
        "wikitable", qrun, reader, "fake_resultset_id"
    )

    assert type(formatted_as_wikitable) is Response
    assert list(formatted_as_wikitable.iter_encoded()) == [
        b'{| class="wikitable"',
        b"\n",
        b"!id!!text!!query_database!!query_id",
        b"\n",
        b"|-",
        b"\n",
        b"|1||show tables;||quarry||2",
        b"\n",
        b"|-",
        b"\n",
        b"|2||select * from query_revision;||quarry||5",
        b"\n",
        b"|}",
        b"\n",
    ]  # noqa: E501


def test_xlsx():
    reader = fake_reader()
    qrun = fake_qrun()
    formatted_as_xlsx = output.get_formatted_response(
        "xlsx", qrun, reader, "fake_resultset_id"
    )

    assert type(formatted_as_xlsx) is Response
    # It's hard to test actual xlsx output because it's a binary format
    #  and seems to include a timestamp.


def test_html():
    reader = fake_reader()
    qrun = fake_qrun()
    formatted_as_html = output.get_formatted_response(
        "html", qrun, reader, "fake_resultset_id"
    )

    assert type(formatted_as_html) is Response
    assert list(formatted_as_html.iter_encoded()) == [
        b"<table>\n",
        b"\n",
        b"<tr>",
        b"\n",
        b'<th scope="col">id</th>',
        b"\n",
        b'<th scope="col">text</th>',
        b"\n",
        b'<th scope="col">query_database</th>',
        b"\n",
        b'<th scope="col">query_id</th>',
        b"\n",
        b"</tr>\n",
        b"\n",
        b"<tr>",
        b"\n",
        b"<td>1</td>",
        b"\n",
        b"<td>show tables;</td>",
        b"\n",
        b"<td>quarry</td>",
        b"\n",
        b"<td>2</td>",
        b"\n",
        b"</tr>\n",
        b"\n",
        b"<tr>",
        b"\n",
        b"<td>2</td>",
        b"\n",
        b"<td>select * from query_revision;</td>",
        b"\n",
        b"<td>quarry</td>",
        b"\n",
        b"<td>5</td>",
        b"\n",
        b"</tr>\n",
        b"\n",
        b"</table>",
        b"\n",
    ]  # noqa: $501


def test_invalid_format():
    reader = fake_reader()
    qrun = fake_qrun()
    formatted_as_invalid = output.get_formatted_response(
        "invalid", qrun, reader, "fake_resultset_id"
    )

    assert type(formatted_as_invalid) is Response
    assert list(formatted_as_invalid.iter_encoded()) == [
        b"Bad file format"
    ]  # noqa: E501
