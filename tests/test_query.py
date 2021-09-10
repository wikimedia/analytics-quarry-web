from datetime import datetime
import json
import pytest

from mock_alchemy.mocking import UnifiedAlchemyMagicMock

from quarry.web.models.query import Query
from quarry.web.models.queryrevision import QueryRevision
from quarry.web.models.queryrun import QueryRun
from quarry.web.models.user import User


class TestQuery:
    @pytest.fixture(autouse=True)
    def setup_method(self, mocker, client):
        self.query_id = 66
        self.latest_rev_id = 88
        self.resultset_id = 1
        self.connection_id = 1
        self.format = "json"
        self.running_status = 2
        self.running_status_msg = "running"

        self.client = client

        # Fake DB handler that anticipates upcoming queries:
        u = User(id="MyUserID", username="test user", wiki_uid="Test user")
        r = QueryRevision(
            id=self.latest_rev_id,
            latest_run_id=self.resultset_id,
            latest_run=QueryRun(
                timestamp=datetime.utcnow(), status=self.running_status
            ),
        )
        q = Query(
            id=self.query_id,
            latest_rev=r,
            description="fake query entry",
            user=u,
            title="a query with a grand title",
            last_touched=datetime.utcnow(),
        )

        self.db_session = UnifiedAlchemyMagicMock()
        # One of each type of object we'll be asked for
        self.db_session.add(u)
        self.db_session.add(r)
        self.db_session.add(q)

        mocker.patch(
            "quarry.web.connections.Connections.session",
            new_callable=mocker.PropertyMock(return_value=self.db_session),
        )

        # Simulate being logged in and authorized
        with self.client.session_transaction() as flask_sess:
            flask_sess["user_id"] = "MyUserID"

    def test_new_query(self, mocker):
        with self.client.session_transaction() as flask_sess:
            flask_sess["user_id"] = "MyUserID"

        mocker.patch(
            "quarry.web.models.query.Query.id",
            new_callable=mocker.PropertyMock(return_value=self.query_id),
        )

        response = self.client.get("/query/new")

        assert response.status_code == 302
        assert (
            response.headers["Location"] == "http://localhost/query/%d" % self.query_id
        )

        self.db_session.filter.assert_has_calls([mocker.call(User.id == "MyUserID")])

        # Should redirect to login page if not logged in
        mocker.patch("quarry.web.query.get_user", return_value=None)

        response = self.client.get("/query/new")
        assert response.status_code == 302
        assert response.headers["Location"] == "http://localhost/login?next=/query/new"

    def test_query_show(self, mocker):
        response = self.client.get("/query/%s" % self.query_id)

        assert response.status_code == 200
        assert response.data

        # request an invalid query
        # This test currently fails! T290874
        # response = self.client.get("/query/%s" % 67)
        # assert response.status_code == 404
        # assert response.data

    def test_query_output_redirect(self, mocker):
        response = self.client.get(
            "/query/%s/result/latest/%s/%s"
            % (self.query_id, self.resultset_id, self.format)
        )
        assert response.status_code == 302
        assert response.headers[
            "Location"
        ] == "https://localhost/run/%d/output/%d/json" % (
            self.resultset_id,
            self.resultset_id,
        )

    def test_query_runs_all(self, mocker):
        # We can't properly test pagination because limit() isn't implemented
        #  in our mock query.  We can at least test that multiple records
        #  are returned though.
        u = User(id="MyUserID", username="test user", wiki_uid="Test user")
        for i in range(1, 7):
            r = QueryRevision(
                id=self.latest_rev_id + i,
                latest_run_id=self.resultset_id + i,
                latest_run=QueryRun(
                    timestamp=datetime.utcnow(), status=self.running_status
                ),
            )
            q = Query(
                id=self.query_id + i,
                latest_rev=r,
                description="extra query entry #%d" % i,
                user=u,
                title="extra query entry #%d" % i,
                last_touched=datetime.utcnow(),
            )
            self.db_session.add(q)

        response = self.client.get("/query/runs/all")
        assert b"extra query entry #2" in response.data
        assert b"extra query entry #7" not in response.data
        assert response.status_code == 200

    def test_output_query_meta(self, mocker):
        response = self.client.get("/query/%d/meta" % self.query_id)

        self.db_session.assert_has_calls([mocker.call.query(Query)])
        self.db_session.assert_has_calls([mocker.call.get(self.query_id)])

        assert response.status_code == 200
        result_dict = json.loads(response.data.decode("utf8"))
        assert result_dict["latest_run"]["status"] == self.running_status_msg
        assert result_dict["query"]["id"] == self.query_id
        assert result_dict["latest_rev"]["id"] == self.latest_rev_id

    def test_output_explain(self, mocker):
        pass
        # TODO: this.  Maybe best left for an integration test.

    def test_fork_query(self, mocker):
        mocker.patch(
            "quarry.web.models.query.Query.id",
            new_callable=mocker.PropertyMock(return_value=self.query_id + 1),
        )

        response = self.client.get("/fork/%d" % self.query_id)

        self.db_session.assert_has_calls([mocker.call.query(Query)])
        self.db_session.filter.assert_has_calls(
            [mocker.call(Query.id == self.query_id)]
        )
        self.db_session.assert_has_calls([mocker.call.add(Query)])

        assert response.status_code == 302
        assert response.headers["Location"] == "http://localhost/query/%d" % (
            self.query_id + 1,
        )

    def test_output_rev_meta(self, mocker):
        response = self.client.get("/rev/%d/meta" % self.latest_rev_id)

        self.db_session.assert_has_calls([mocker.call.query(QueryRevision)])
        self.db_session.assert_has_calls([mocker.call.get(self.latest_rev_id)])

        assert response.status_code == 200
        result_dict = json.loads(response.data.decode("utf8"))
        assert result_dict["rev"]["id"] == self.latest_rev_id
        assert result_dict["latest_run"]["status"] == self.running_status_msg
