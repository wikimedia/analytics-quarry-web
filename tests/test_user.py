from datetime import datetime
import pytest
from sqlalchemy import func

from mock_alchemy.mocking import UnifiedAlchemyMagicMock

from quarry.web.models.query import Query
from quarry.web.models.star import Star
from quarry.web.models.queryrevision import QueryRevision
from quarry.web.models.queryrun import QueryRun
from quarry.web.models.user import User
from quarry.web.models.user import UserGroup


# @pytest.mark.usefixtures([mocker, client])
class TestUser:
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
        self.db_session.add(ug)
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
            flask_sess["user_id"] = self.user_id
            flask_sess["preferences"] = {"breakfast": "waffles", "lunch": "tacos"}

    def test_sudo(self, mocker):
        response = self.client.get("/sudo/%s" % self.user_id)
        self.db_session.filter.assert_has_calls([mocker.call(User.id == self.user_id)])
        self.db_session.assert_has_calls([mocker.call.query(UserGroup)])
        self.db_session.filter.assert_has_calls(
            [
                mocker.call.get(
                    (UserGroup.user_id == self.user_id),
                    (UserGroup.group_name == "sudo"),
                )
            ]
        )
        assert response.headers["Location"] == "http://localhost/"
        assert response.status_code == 302

    def test_user_page(self, mocker):
        mocker.patch("quarry.web.user.get_user", return_value=None)
        response = self.client.get("/%s" % self.user_name)
        test_user_name = self.user_name.replace("_", " ").lower()

        self.db_session.filter.assert_has_calls(
            [mocker.call(func.lower(User.username) == test_user_name)]
        )
        assert response.status_code == 200
