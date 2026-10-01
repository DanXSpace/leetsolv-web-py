# leetsolv-web

A personal spaced-repetition tracker for LeetCode.

A web app that replaces the [`leetsolv`](https://github.com/eannchen/leetsolv) CLI: it logs LeetCode problems, schedules reviews with leetsolv's exact spaced-repetition algorithm, and adds the things a CLI couldn't — a hosted backend that syncs across devices, LeetCode metadata enrichment, and a read-only share view for a mentor.

## Features

- **Review queue** — due and upcoming problems, with an inline form that re-asks familiarity / memory / importance.
- **Problem log** — search and filter by familiarity, importance, and due status; edit notes; delete.
- **Add by URL** — paste a LeetCode URL and the title, difficulty, and tags are filled in automatically.
- **Dashboard** — familiarity distribution, review activity, and due-over-time.
- **History** — an audit log of every change, with undo.
- **Settings** — tune the scheduler (interval randomization, overdue penalty, queue sizes) and manage a revocable mentor share link.
- **Mentor view** — a read-only link (`/share/<token>`) that shows the whole app, notes included, with owner controls hidden.
- **GitHub OAuth** — single-owner access, pinned to a numeric GitHub id.
- **One-time import** from `~/.leetsolv/` so you can retire the CLI.

## Concepts

- **Problem** — a LeetCode problem you track, identified by its URL, carrying a note and review state.
- **Log** vs **review** — logging a new problem adds it; logging an existing one is a review that reschedules it.
- **Familiarity** (1–5) — how the latest attempt went, from *Struggled* to *Fluent*.
- **Importance** (1–4) — how important the problem is to retain.
- **Memory** — whether the solve relied on recall rather than reasoning (*Reasoned / Partial / Full*).
- **Due** / **Upcoming** — next review today-or-earlier / tomorrow.

Full terminology lives in [`CONTEXT.md`](CONTEXT.md).

## Tech stack

- **Backend** — FastAPI, SQLAlchemy 2, SQLite (Python ≥ 3.12)
- **Frontend** — React 18, Vite, TypeScript
- **Serving** — in production the backend serves the built SPA from the same origin (required for the httponly session cookie)

## Run locally

### Prerequisites

- Python ≥ 3.12
- Node.js ≥ 18

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# export the environment variables (see below), then:
uvicorn app.main:app --reload          # http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev                            # http://localhost:5173, proxies /api -> :8000
```

### Environment variables

The app reads configuration from the environment (there is no `.env` loader). `.env.example` documents every variable; the ones you need for local development are:

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `LEETSOLV_SECRET_KEY` | prod | auto-generated (unstable) | signs the session cookie |
| `LEETSOLV_GITHUB_CLIENT_ID` | yes | — | GitHub OAuth app client id |
| `LEETSOLV_GITHUB_CLIENT_SECRET` | yes | — | GitHub OAuth app secret |
| `LEETSOLV_OWNER_GITHUB_ID` | yes | — | the owner's *numeric* GitHub id |
| `LEETSOLV_BASE_URL` | — | `http://localhost:5173` | public origin, used for the OAuth redirect |
| `LEETSOLV_DATABASE_URL` | — | `sqlite:///./leetsolv.db` | SQLite location |
| `LEETSOLV_DIST_DIR` | — | (unset) | built frontend dir for same-origin serving |
| `LEETSOLV_CORS_ORIGINS` | — | `http://localhost:5173` | comma-separated CORS origins |

For local OAuth, register a GitHub OAuth app with the authorization callback URL `http://localhost:5173/api/auth/callback`, then export:

```bash
export LEETSOLV_GITHUB_CLIENT_ID="..."
export LEETSOLV_GITHUB_CLIENT_SECRET="..."
export LEETSOLV_OWNER_GITHUB_ID="123456"   # your numeric GitHub id
export LEETSOLV_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
```

`LEETSOLV_BASE_URL` can stay at its default for development.

### Tests

```bash
cd backend
pytest
```

## Deploy

The repo ships a multi-stage [`Dockerfile`](Dockerfile) that builds the frontend and runs the backend serving both from one origin. The canonical target is Railway, with the SQLite database on a persistent volume mounted at `/data`. Full step-by-step instructions — GitHub OAuth app, volume, and environment variables — are in [`DEPLOY.md`](DEPLOY.md).

## Import from leetsolv

To migrate from the original leetsolv CLI, run the one-time import against your `~/.leetsolv/` directory:

```bash
cd backend
python -m app.import_cli
```

It reads `questions.json` and `deltas.json`, enriches each problem with LeetCode metadata, and writes the SQLite database. It's safe to re-run (idempotent by URL).

LeetCode metadata is bundled from the [`whiskwhite/leetcode-complete`](https://huggingface.co/datasets/whiskwhite/leetcode-complete) community dataset.

## License

[MIT](LICENSE) © 2026 DanXSpace
