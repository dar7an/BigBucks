# BigBucks

Paper trading for a methods course: $1,000,000 virtual cash, a real ledger, Markowitz-style metrics, and SPY comparison charts. It is **not** a brokerage. There are no commissions, taxes, or after-hours prints. Fills are last close, whole shares only.

A fresh clone runs without an Alpha Vantage key. Fixture prices for AAPL, MSFT, NVDA, GOOGL, AMZN, META, and SPY are seeded into SQLite.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional; defaults work for local fixture mode
flask --app bigbucks init-db
flask --app bigbucks run --debug
```

Open http://127.0.0.1:5000

Teaching logins created by `init-db` (change these if you share the machine):

| Username | Password   | Role  |
| -------- | ---------- | ----- |
| alice    | alicepass  | user  |
| admin    | adminpass  | admin |

Grant admin to someone else:

```bash
flask --app bigbucks make-admin alice
```

## Environment

See `.env.example`. Nothing secret is committed.

| Variable | Default | Meaning |
| --- | --- | --- |
| `SECRET_KEY` | `dev-change-me` | Flask session signing. Set a long random value before networking this. |
| `MARKET_DATA_SOURCE` | `fixture` | `fixture` uses seeded history. `alphavantage` uses free `TIME_SERIES_DAILY`. |
| `ALPHA_VANTAGE_API_KEY` | empty | Required only for live mode. Never sent to the browser. |
| `RISK_FREE_RATE` | `0.043` | Annual decimal used in Sharpe (10-year Treasury proxy). |
| `STARTING_CASH` | `1000000` | Virtual cash on registration. |
| `SEED_DEMO_USERS` | `1` | Seed alice/admin on `init-db`. |

Live mode uses the **free** daily series, not premium `TIME_SERIES_DAILY_ADJUSTED`. Adjusted close is stored as close. Quotes and charts always read `historic_prices`; login does not refresh the vendor.

## Formulas

Implemented once in `bigbucks/analytics.py` and used by both the user Metrics page and admin views.

**Daily return** — \(r_t = P_t / P_{t-1} - 1\) on adjusted close, dates sorted ascending.

**Weight** — \(w_i = q_i P_i / \sum q_j P_j\) (mark to market). Cash is excluded from the mix.

**Holding-period return** — \(\prod (1+r_{p,t}) - 1\), not a sum of daily returns.

**Annualized expected return** — \(\mathrm{mean}(r_d) \times 252\).

**Holdings volatility** — \(\sqrt{w'\Sigma w}\) with \(\Sigma = \mathrm{Cov}(r_d)\times 252\) (pandas sample cov, ddof=1). This is the plotted “Your book” point. It is **not** the min-variance mix at the same return.

**Sharpe (annualized)** —

\[
\frac{\mathrm{mean}(r_d) - r_f/252}{\mathrm{std}(r_d, \mathrm{ddof}=1)}\times\sqrt{252}
\]

**Cumulative vs SPY** — \(P_t / P_0 - 1\) on the first overlapping date. Charts are chronological.

**Frontier** — unconstrained two-fund mean-variance (Merton 1972 KKT linear system). Short sales are allowed and labeled.

## Tests

```bash
pytest
```

CI runs the same suite on Python 3.12 (GitHub Actions).

## Architecture

Flask 3 app factory and blueprints, Jinja + one CSS file, SQLite, Werkzeug password hashes, Flask-WTF CSRF, parameterized SQL. Market data: `bigbucks/market.py`. Ledger: `bigbucks/ledger.py`. Math: `bigbucks/analytics.py` + `bigbucks/solver.py`.
