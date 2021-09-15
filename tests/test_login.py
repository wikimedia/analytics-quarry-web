import pytest

from mock_alchemy.mocking import UnifiedAlchemyMagicMock


# @pytest.mark.usefixtures([mocker, client])
class TestLogin:
    @pytest.fixture(autouse=True)
    def setup_method(self, mocker, client):
        # mock_alchemy is not great at understanding post data;
        #  to work around we use string IDs rather than int IDs
        #  so it can match with the string that it gets from a POST
        self.client = client

        # Fake DB handler that anticipates upcoming queries:
        self.db_session = UnifiedAlchemyMagicMock()

        mocker.patch(
            "quarry.web.connections.Connections.session",
            new_callable=mocker.PropertyMock(return_value=self.db_session),
        )

        # Simulate being logged in and authorized
        with self.client.session_transaction() as flask_sess:
            flask_sess["user_id"] = "MyUserID"
            flask_sess["request_token"] = "request token"
            flask_sess["preferences"] = {"breakfast": "waffles", "lunch": "tacos"}
            flask_sess["return_to_url"] = "return/to/url"

    def test_login(self, mocker):
        mocker.patch(
            "mwoauth.Handshaker.initiate", return_value=("loginredir", "fake_token")
        )
        response = self.client.get("/login")

        assert response.status_code == 302
        assert response.headers["Location"] == "http://localhost/loginredir"

    def test_oauth_callback(self, mocker):
        print("first try")
        response = self.client.get("/oauth-callback?woopity=bloopity")

        assert response.status_code == 302
        assert response.headers["Location"] == "http://localhost/"

        mocker.patch("mwoauth.Handshaker.complete", return_value=("fake_token"))
        mocker.patch(
            "mwoauth.Handshaker.identify",
            return_value=({"sub": "Test user", "username": "a username"}),
        )
        print("second try")
        response = self.client.get("/oauth-callback?woopity=bloopity")

        assert response.status_code == 302
        assert response.headers["Location"] == "http://localhost/return/to/url"

    def test_logout(self, mocker):
        response = self.client.get("/logout")

        assert response.status_code == 302
        assert response.headers["Location"] == "http://localhost/"
