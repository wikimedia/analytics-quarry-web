from datetime import datetime
import json
import pytest

from mock_alchemy.mocking import UnifiedAlchemyMagicMock

from quarry.web.models.query import Query
from quarry.web.models.queryrevision import QueryRevision
from quarry.web.models.queryrun import QueryRun
from quarry.web.models.user import User


# @pytest.mark.usefixtures([mocker, client])
class TestRun:
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
        u = User(id="MyUserID", username="test user", wiki_uid="Test user")
        q = Query(
            id=self.query_id,
            description="fake query entry",
            user=u,
            title="a query with a grand title",
            last_touched=datetime.utcnow(),
        )
        r = QueryRevision(id=self.rev_id, latest_run_id=self.resultset_id, query=q)
        qr = QueryRun(
            timestamp=datetime.utcnow(),
            status=self.complete_status,
            id=self.run_id,
            query_rev_id=self.rev_id,
            task_id="task_id",
            extra_info='{ "what_is_this": "extra_info"}',
            rev=r,
        )

        self.db_session = UnifiedAlchemyMagicMock()
        # One of each type of object we'll be asked for
        self.db_session.add(u)
        self.db_session.add(qr)
        self.db_session.add(r)
        self.db_session.add(q)

        mocker.patch(
            "quarry.web.connections.Connections.session",
            new_callable=mocker.PropertyMock(return_value=self.db_session),
        )

        # Simulate being logged in and authorized
        with self.client.session_transaction() as flask_sess:
            flask_sess["user_id"] = "MyUserID"

    def test_run_status(self, mocker):
        response = self.client.get("/run/%d/status" % self.run_id)
        assert response.status_code == 200

        self.db_session.assert_has_calls([mocker.call.query(QueryRun)])
        self.db_session.assert_has_calls([mocker.call.get(self.run_id)])

        result_dict = json.loads(response.data.decode("utf8"))
        assert result_dict["status"] == self.complete_status_msg
        assert result_dict["extra"]["what_is_this"] == "extra_info"

        response = self.client.get("/run/%d/status" % (self.run_id + 1))
        assert response.status_code == 404

    def test_output_result(self, mocker):
        # First 404 test: no such run
        response = self.client.get(
            "/run/%d/output/%d/json" % (self.run_id + 1, self.resultset_id)
        )
        assert response.status_code == 404
        assert response.data == b"No such query_run id"

        # second 404 test: valid run but no resultset found
        response = self.client.get(
            "/run/%d/output/%d/json" % (self.run_id, self.resultset_id)
        )
        assert response.status_code == 404
        assert response.data == b"No such resultset id"

        # now mock the resultset and go for a 200
        def get_rows(_self, _resultset_id):
            for row in ["header", "row0", "row1", "row2"]:
                yield row

        mocker.patch("quarry.web.results.SQLiteResultReader.get_rows", get_rows)

        response = self.client.get(
            "/run/%d/output/%d/json" % (self.run_id, self.resultset_id)
        )
        assert response.status_code == 200

        result_dict = json.loads(response.data.decode("utf8"))
        assert result_dict["meta"]["run_id"] == self.run_id
        assert result_dict["meta"]["rev_id"] == self.rev_id
        assert result_dict["meta"]["query_id"] == self.query_id
        assert result_dict["headers"] == "header"
        assert result_dict["rows"][0] == "row0"
        assert result_dict["rows"][2] == "row2"

    def test_output_run_meta(self, mocker):
        response = self.client.get("/run/%d/meta" % (self.run_id + 1))
        assert response.status_code == 404
        assert response.data == b"No such query run id"

        # Mock out json.dumps because json chokes on the
        #  objects we're getting from mock_alchemy
        mocker.patch("json.dumps")

        response = self.client.get("/run/%d/meta" % self.run_id)
        assert response.status_code == 200
