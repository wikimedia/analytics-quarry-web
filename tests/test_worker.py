from datetime import datetime
import pytest

from mock_alchemy.mocking import UnifiedAlchemyMagicMock

from quarry.web.models.query import Query
from quarry.web.models.queryrevision import QueryRevision
from quarry.web.models.queryrun import QueryRun
from quarry.web.models.user import User
from quarry.web import worker


class Cursor:
    description = "fake fake fake"
    rowcount = 0

    def __init__(self):
        self.called = False
        self.nextsetcalled = False

    def fetchall(self):
        return [["a", "b", "c"], ["1", "2", "3"]]

    def fetchmany(self, _count):
        if not self.called:
            self.called = True
            return [["a", "b", "c"], ["1", "2", "3"], ["you", "and", "me"]]
        else:
            return []

    def nextset(self):
        if not self.nextsetcalled:
            self.nextsetcalled = True
            return [["do", "re", "mi"]]
        else:
            return []

    def close(self):
        pass

    def execute(self, _query):
        pass


class TestWorker:
    @pytest.fixture(autouse=True)
    def setup_method(self, mocker, client):
        self.query_id = 66
        self.rev_id = 88
        self.run_id = 44
        self.resultset_id = 1
        self.connection_id = 1
        self.format = "json"
        self.complete_status = 4
        self.complete_status_msg = "complete"

        self.client = client

        # Fake DB handler that anticipates upcoming queries:
        self.user = User(id="MyUserID", username="test user", wiki_uid="Test user")
        self.query = Query(
            id=self.query_id,
            description="fake query entry",
            user=self.user,
            title="a query with a grand title",
            last_touched=datetime.utcnow(),
        )
        self.revision = QueryRevision(
            id=self.rev_id,
            latest_run_id=self.resultset_id,
            query=self.query,
            text="show tables",
            query_database="fakedb",
        )
        self.queryrun = QueryRun(
            timestamp=datetime.utcnow(),
            status=self.complete_status,
            id=self.run_id,
            query_rev_id=self.rev_id,
            task_id="task_id",
            extra_info='{ "what_is_this": "extra_info"}',
            rev=self.revision,
        )

        self.db_session = UnifiedAlchemyMagicMock()
        self.db_session.cursor = Cursor
        # One of each type of object we'll be asked for
        self.db_session.add(self.user)
        self.db_session.add(self.queryrun)
        self.db_session.add(self.revision)
        self.db_session.add(self.query)

        mocker.patch(
            "quarry.web.connections.Connections.session",
            new_callable=mocker.PropertyMock(return_value=self.db_session),
        )
        mocker.patch("pymysql.connect", return_value=self.db_session)

        # Simulate being logged in and authorized
        with self.client.session_transaction() as flask_sess:
            flask_sess["user_id"] = "MyUserID"
            flask_sess["preferences"] = {"breakfast": "waffles", "lunch": "tacos"}

    def test_run_query(self, mocker):
        mocker.patch("os.makedirs")
        mocker.patch("sqlite3.connect", return_value=self.db_session)

        worker.init()
        worker.run_query(self.run_id)

        # This isn't the full set of queries; comparing the actual session
        #  queries is messy. This should a least make sure that the DB
        #  is getting hit.
        self.db_session.assert_has_calls(
            [
                mocker.call(self.user),
                mocker.call(self.queryrun),
                mocker.call(self.revision),
                mocker.call(self.query),
                mocker.call(QueryRun),
            ]
        )
