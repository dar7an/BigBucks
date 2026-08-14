from __future__ import annotations

import pytest

from bigbucks import create_app
from bigbucks.db import init_db


@pytest.fixture
def app(tmp_path):
    db_path = tmp_path / "test.db"
    application = create_app(
        {
            "TESTING": True,
            "DATABASE": str(db_path),
            "SECRET_KEY": "test-secret-key-not-dev",
            "WTF_CSRF_ENABLED": False,
            "MARKET_DATA_SOURCE": "fixture",
            "SEED_DEMO_USERS": True,
            "STARTING_CASH": 1_000_000,
            "RISK_FREE_RATE": 0.04,
        }
    )
    with application.app_context():
        init_db()
    yield application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth(client):
    return AuthActions(client)


class AuthActions:
    def __init__(self, client):
        self._client = client

    def register(
        self,
        username="bob",
        firstname="Bob",
        lastname="Smith",
        email="bob@example.com",
        password="bobsmith1",
    ):
        return self._client.post(
            "/auth/register",
            data={
                "username": username,
                "firstname": firstname,
                "lastname": lastname,
                "email": email,
                "password": password,
            },
            follow_redirects=True,
        )

    def login(self, username="alice", password="alicepass"):
        return self._client.post(
            "/auth/login",
            data={"username": username, "password": password},
            follow_redirects=True,
        )

    def logout(self):
        return self._client.get("/auth/logout", follow_redirects=True)
