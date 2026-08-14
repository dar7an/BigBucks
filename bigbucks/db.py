"""SQLite connection, schema init, and CLI."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import click
from flask import current_app, g


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        path = Path(current_app.config["DATABASE"])
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path, detect_types=0)
        conn.row_factory = sqlite3.Row
        conn.isolation_level = None  # autocommit; ledger uses explicit BEGIN IMMEDIATE
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        g.db = conn
    return g.db


def close_db(e=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    db = get_db()
    schema = Path(current_app.root_path) / "schema.sql"
    db.executescript(schema.read_text(encoding="utf-8"))
    db.commit()
    from . import fixtures

    fixtures.seed_market(db)
    if current_app.config.get("SEED_DEMO_USERS"):
        fixtures.seed_demo_users(db)


@click.command("init-db")
def init_db_command() -> None:
    """Wipe the SQLite file, recreate tables, and seed fixture prices."""
    init_db()
    click.echo("Initialized the database and seeded fixture market data.")


@click.command("make-admin")
@click.argument("username")
def make_admin_command(username: str) -> None:
    """Grant the admin role to an existing username."""
    db = get_db()
    cur = db.execute(
        "UPDATE users SET role = 'admin' WHERE username = ?", (username,)
    )
    db.commit()
    if cur.rowcount == 0:
        raise click.ClickException(f"No user named {username!r}.")
    click.echo(f"{username} is now an admin.")


def init_app(app) -> None:
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(make_admin_command)
