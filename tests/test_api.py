from datetime import datetime
import json
import pytest

from mock_alchemy.mocking import UnifiedAlchemyMagicMock

from quarry.web.models.query import Query
from quarry.web.models.star import Star
from quarry.web.models.queryrevision import QueryRevision
from quarry.web.models.queryrun import QueryRun
from quarry.web.models.user import User
from quarry.web.user import get_preferences


# @pytest.mark.usefixtures([mocker, client])
class TestApi:
    @pytest.fixture(autouse=True)
    def setup_method(self, mocker, client):
        # mock_alchemy is not great at understanding post data;
        #  to work around we use string IDs rather than int IDs
        #  so it can match with the string that it gets from a POST
        self.user_id = "MyUserID"
        self.query_id = "66"
        self.rev_id = "88"
        self.run_id = 44
        self.star_id = "22"
        self.resultset_id = 1
        self.connection_id = 1
        self.format = "json"
        self.complete_status = 4
        self.complete_status_msg = "complete"

        self.client = client

        # Fake DB handler that anticipates upcoming queries:
        u = User(id=self.user_id, username="test user", wiki_uid="Test user")
        q = Query(
            id=self.query_id,
            description="fake query entry",
            user=u,
            user_id=self.user_id,
            title="a query with a grand title",
            last_touched=datetime.utcnow(),
        )
        r = QueryRevision(id=self.rev_id, latest_run_id=self.run_id, query=q)
        qr = QueryRun(
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
        # One of each type of object we'll be asked for
        self.db_session.add(u)
        self.db_session.add(qr)
        self.db_session.add(r)
        self.db_session.add(q)
        self.db_session.add(s)

        mocker.patch(
            "quarry.web.connections.Connections.session",
            new_callable=mocker.PropertyMock(return_value=self.db_session),
        )

        # Simulate being logged in and authorized
        with self.client.session_transaction() as flask_sess:
            flask_sess["user_id"] = "MyUserID"
            flask_sess["preferences"] = {"breakfast": "waffles", "lunch": "tacos"}

    def test_unstar_query(self, mocker):
        response = self.client.post(
            "/api/query/unstar", data=dict(query_id=self.query_id)
        )
        self.db_session.assert_has_calls([mocker.call.query(Star)])
        self.db_session.assert_has_calls([mocker.call.get(self.query_id)])
        self.db_session.assert_has_calls([mocker.call.delete(Star)])
        assert response.status_code == 200

        response = self.client.post("/api/query/unstar", data=dict(query_id="invalid"))
        assert response.status_code == 404

        mocker.patch("quarry.web.api.get_user", return_value=None)
        response = self.client.post(
            "/api/query/unstar", data=dict(query_id=self.query_id)
        )
        assert response.status_code == 403

    def test_star_query(self, mocker):
        response = self.client.post(
            "/api/query/star", data=dict(query_id=self.query_id)
        )
        assert response.status_code == 200
        self.db_session.assert_has_calls([mocker.call.query(Query)])
        self.db_session.assert_has_calls([mocker.call.get(self.query_id)])

        response = self.client.post("/api/query/star", data=dict(query_id="invalid"))
        assert response.status_code == 404

        mocker.patch("quarry.web.api.get_user", return_value=None)
        response = self.client.post(
            "/api/query/star", data=dict(query_id=self.query_id)
        )
        assert response.status_code == 403

    def test_set_meta(self, mocker):
        # Before we modify things, establish the baseline
        query = self.db_session.query(Query).get(self.query_id)
        assert (query.title) != "new title"
        assert (query.description) != "new description"
        assert not query.published

        # Set metadata
        response = self.client.post(
            "/api/query/meta",
            data=dict(
                query_id=self.query_id,
                title="new title",
                description="new description",
                published=1,
            ),
        )
        assert response.status_code == 200
        self.db_session.assert_has_calls([mocker.call.query(Query)])
        self.db_session.filter.assert_has_calls([mocker.call(User.id == "MyUserID")])
        result_dict = json.loads(response.data.decode("utf8"))
        assert result_dict["id"] == self.query_id

        # Let's check if the modified record is in there now
        query = self.db_session.query(Query).get(self.query_id)
        assert (query.title) == "new title"
        assert (query.description) == "new description"
        assert query.published

        # And test the auth check
        mocker.patch("quarry.web.api.get_user", return_value=None)
        response = self.client.post(
            "/api/query/meta", data=dict(query_id=self.query_id)
        )
        assert response.status_code == 401

    def test_run_query(self, mocker):
        # We don't actually want to delay, but we /do/ want to return a task id.
        class fake_task:
            @property
            def task_id(self):
                return "task_id"

        mocker.patch("celery.app.task.Task.delay", return_value=fake_task())

        # The route will create new QueryRun object
        mocker.patch(
            "quarry.web.models.queryrun.QueryRun.id",
            new_callable=mocker.PropertyMock(return_value=self.run_id),
        )

        response = self.client.post(
            "/api/query/run",
            data=dict(
                query_id=self.query_id, query_database="mywiki", text="show tables;"
            ),
        )
        assert response.status_code == 200
        result_dict = json.loads(response.data.decode("utf8"))
        assert result_dict["qrun_id"] == self.run_id
        self.db_session.assert_has_calls([mocker.call.query(Query)])

    def test_stop_query(self, mocker):
        response = self.client.post(
            "/api/query/stop", data=dict(qrun_id=self.run_id, query_database="mywiki")
        )
        assert response.status_code == 200
        result_dict = json.loads(response.data.decode("utf8"))
        assert result_dict["stopped"]

        mocker.patch("quarry.web.api.get_user", return_value=None)
        response = self.client.post(
            "/api/query/stop", data=dict(qrun_id=self.run_id, query_database="mywiki")
        )
        assert response.status_code == 401

    def test_pref_get(self, mocker):
        response = self.client.get("/api/preferences/get/breakfast")

        assert response.status_code == 200
        result_dict = json.loads(response.data.decode("utf8"))
        print(result_dict)
        assert result_dict["key"] == "breakfast"
        assert result_dict["value"] == "waffles"

        mocker.patch("quarry.web.api.get_user", return_value=None)
        response = self.client.post(
            "/api/query/stop", data=dict(qrun_id=self.run_id, query_database="mywiki")
        )
        assert response.status_code == 401

    def test_pref_set(self, mocker):
        response = self.client.get("/api/preferences/set/dinner/gumbo")
        assert response.status_code == 201
        result_dict = json.loads(response.data.decode("utf8"))
        print(result_dict)
        assert result_dict["key"] == "dinner"
        assert result_dict["success"] == ""
        assert get_preferences()["dinner"] == "gumbo"

        mocker.patch("quarry.web.api.get_user", return_value=None)
        response = self.client.get("/api/preferences/set/dinner/gumbo")
        assert response.status_code == 401

    def test_get_dbs(self, mocker):
        response = self.client.get("/api/dbs")
        assert response.status_code == 200
        result_dict = json.loads(response.data.decode("utf8"))
        print(result_dict)
        assert result_dict["dbs"] == []
