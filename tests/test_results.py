from datetime import datetime
import pytest

from mock_alchemy.mocking import UnifiedAlchemyMagicMock

from quarry.web.models.query import Query
from quarry.web.models.star import Star
from quarry.web.models.queryrevision import QueryRevision
from quarry.web.models.queryrun import QueryRun
from quarry.web.models.user import User
from quarry.web.models.user import UserGroup
from quarry.web import results


class TestResults:
    @pytest.fixture(autouse=True)
    def setup_method(self, mocker, client):
        # mock_alchemy is not great at understanding post data;
        #  to work around we use string IDs rather than int IDs
        #  so it can match with the string that it gets from a POST
        self.user_id = "myuserid"
        self.user_group_id = "77"
        self.user_name = "Test User With_Underscores"
        self.query_id = "66"
        self.rev_id = "88"
        self.run_id = "44"
        self.star_id = "22"
        self.resultset_id = 1
        self.connection_id = 1
        self.format = "json"
        self.complete_status = 4
        self.complete_status_msg = "complete"
        self.resultset_id = 555

        self.client = client

        # Fake DB handler that anticipates upcoming queries:
        ug = UserGroup(id=self.user_group_id, user_id=self.user_id, group_name="root")
        u = User(id=self.user_id, username=self.user_name, wiki_uid="Test user")
        q = Query(
            id=self.query_id,
            description="fake query entry",
            user=u,
            user_id=self.user_id,
            title="a query with a grand title",
            last_touched=datetime.utcnow(),
        )
        r = QueryRevision(id=self.rev_id, latest_run_id=self.run_id, query=q)
        self.qr = QueryRun(
            timestamp=datetime.utcnow(),
            status=self.complete_status,
            id=self.run_id,
            query_rev_id=self.rev_id,
            task_id="task_id",
            extra_info='{ "what_is_this": "extra_info"}',
            rev=r,
        )
        s = Star(
            id=self.star_id,
            user_id=self.user_id,
            timestamp=datetime.utcnow(),
            query_id=self.query_id,
        )

        self.db_session = UnifiedAlchemyMagicMock()

        mocker.patch("sqlite3.connect", return_value=self.db_session)

        # One of each type of object we'll be asked for
        self.db_session.add(u)
        self.db_session.add(ug)
        self.db_session.add(self.qr)
        self.db_session.add(r)
        self.db_session.add(q)
        self.db_session.add(s)

        mocker.patch(
            "quarry.web.connections.Connections.session",
            new_callable=mocker.PropertyMock(return_value=self.db_session),
        )

        # Simulate being logged in and authorized
        with self.client.session_transaction() as flask_sess:
            flask_sess["user_id"] = self.user_id
            flask_sess["preferences"] = {"breakfast": "waffles", "lunch": "tacos"}

        self.path_template = "user_%s/query_%s/qr_%s"

    def test_start_resultset(self, mocker):
        writer = results.SQLiteResultWriter(self.qr, self.path_template)
        writer.cur_row_id = -1
        writer.column_count = -1
        writer.resultset_id = self.resultset_id

        writer.start_resultset(
            ["manny", "moe", '"jack"', b"nulltest\x00".decode("utf8")], 7
        )
        assert writer.column_count == 4
        assert writer.cur_row_id == 0
        self.db_session.assert_has_calls(
            [
                mocker.call(
                    'CREATE TABLE resultset_555 (__id__ INTEGER PRIMARY KEY, "manny", "moe", """jack""", "nulltest")'
                )
            ]
        )

    def test_add_rows(self, mocker):
        writer = results.SQLiteResultWriter(self.qr, self.path_template)
        writer.column_count = 3

        writer.add_rows(
            [["row0arg0", "row0arg1", "row0arg2"], ["row1arg0", "row1arg1", "row1arg2"]]
        )
        self.db_session.assert_has_calls(
            [
                mocker.call(
                    "INSERT INTO resultset_0 VALUES (NULL, ?,?,?)",
                    [
                        ["row0arg0", "row0arg1", "row0arg2"],
                        ["row1arg0", "row1arg1", "row1arg2"],
                    ],
                )
            ]
        )

    def test_get_resultsets(self, mocker):
        reader = results.SQLiteResultReader(self.qr, self.path_template)
        resultsets = reader.get_resultsets()
        assert resultsets == []
        self.db_session.assert_has_calls(
            [mocker.call("SELECT id, headers, rowcount FROM resultsets ORDER BY id")]
        )

    def test_get_rows(self, mocker):
        # FIXME: add some actual data in the return so we can test pagination
        reader = results.SQLiteResultReader(self.qr, self.path_template)
        rows = reader.get_rows(self.resultset_id)
        assert rows is not None
