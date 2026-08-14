from __future__ import annotations


def test_config_endpoint_gone(client):
    res = client.get("/config")
    assert res.status_code == 404
    assert b"API_KEY" not in res.data
    assert b"alphavantage" not in res.data.lower()


def test_home_logout_link_is_logout(client, auth):
    auth.login()
    home = client.get("/home")
    assert home.status_code == 200
    assert b'href="/auth/logout"' in home.data
    assert b"Log out" in home.data
    logged_out = client.get("/auth/logout", follow_redirects=False)
    assert logged_out.status_code == 302
    follow = client.get("/home")
    assert follow.status_code == 302
    assert "/auth/login" in follow.headers["Location"]


def test_admin_user_metrics_requires_login(client):
    res = client.get("/admin/users/1/metrics")
    assert res.status_code == 302
    assert "/auth/login" in res.headers["Location"]


def test_admin_user_metrics_forbidden_for_user(client, auth):
    auth.login()  # alice, role=user
    res = client.get("/admin/users/1/metrics")
    assert res.status_code == 403


def test_admin_pages_ok_for_admin(client, auth):
    auth.login(username="admin", password="adminpass")
    summary = client.get("/admin/summary")
    assert summary.status_code == 200
    assert b"Today" in summary.data
    holdings = client.get("/admin/holdings")
    assert holdings.status_code == 200


def test_register_validates_email_and_username(client):
    res = client.post(
        "/auth/register",
        data={
            "username": "",
            "firstname": "Joe",
            "lastname": "Smith",
            "email": "fakeEmail",
            "password": "myPassword",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"Fill in every field" in res.data or b"email" in res.data.lower()


def test_password_change_requires_current(client, auth):
    auth.login()
    res = client.post(
        "/account/",
        data={
            "intent": "password",
            "current_password": "wrong",
            "password": "newpassword",
            "password_confirm": "newpassword",
        },
        follow_redirects=True,
    )
    assert b"Current password is incorrect" in res.data
    # old password still works
    client.get("/auth/logout")
    again = client.post(
        "/auth/login",
        data={"username": "alice", "password": "alicepass"},
        follow_redirects=True,
    )
    assert again.status_code == 200
    assert b"Portfolio" in again.data or b"Hello" in again.data


def test_search_and_trade_require_login(client):
    assert client.get("/search").status_code == 302
    assert client.get("/trade").status_code == 302
    assert client.get("/metrics/").status_code == 302


def test_login_does_not_require_live_api(client):
    res = client.post(
        "/auth/login",
        data={"username": "alice", "password": "alicepass"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"Equity" in res.data
    assert b"$1,000,000.00" in res.data or b"1,000,000" in res.data


def test_unknown_ticker_search(client, auth):
    auth.login()
    res = client.get("/search/FAKETICKER", follow_redirects=True)
    assert res.status_code == 200
    assert b"not in the fixture universe" in res.data or b"No price" in res.data
