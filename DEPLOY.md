# Deploying leetsolv-web to Railway

The app is a single FastAPI service that serves both the API and the built
React SPA from one origin (required, because the session cookie is
httponly/same-origin). This guide covers the three manual steps that can't be
scripted from the repo: the GitHub OAuth app, the Railway service + volume,
and the environment variables.

## 1. GitHub OAuth app

1. Go to **GitHub → Settings → Developer settings → OAuth Apps → New OAuth App**.
2. Fill in:
   - **Application name**: `leetsolv-web`
   - **Homepage URL**: your Railway URL (e.g. `https://<app>.up.railway.app`) — use a placeholder now, update after Railway gives you the real URL.
   - **Authorization callback URL**: `https://<app>.up.railway.app/api/auth/callback`
3. Create the app, then copy the **Client ID** and generate a **Client secret**.

Find your numeric owner id (not the username):

```sh
curl -s https://api.github.com/users/<your-username> | jq .id
```

## 2. Railway

1. **New project → Deploy from GitHub repo** → pick `leetsolv-web-py`. The
   `Dockerfile` at the repo root is detected automatically (pinned by
   `railway.json`).
2. **Add a persistent volume** (so the SQLite file survives redeploys):
   ```sh
   railway volume add -m /data
   ```
   (or add it in the service dashboard under *Volumes*). The container writes
   `leetsolv.db` to `/data` via `LEETSOLV_DATABASE_URL`.
3. Add a **public domain** to the service (Settings → Networking → Generate
   Domain) — this becomes your `LEETSOLV_BASE_URL`.

## 3. Environment variables

Set these on the Railway service (or paste `.env.example` and fill it in):

| Variable | Value |
| --- | --- |
| `LEETSOLV_SECRET_KEY` | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `LEETSOLV_GITHUB_CLIENT_ID` | from step 1 |
| `LEETSOLV_GITHUB_CLIENT_SECRET` | from step 1 |
| `LEETSOLV_OWNER_GITHUB_ID` | your numeric GitHub id |
| `LEETSOLV_BASE_URL` | `https://<app>.up.railway.app` |
| `LEETSOLV_DATABASE_URL` | `sqlite:////data/leetsolv.db` |
| `LEETSOLV_DIST_DIR` | `/app/frontend/dist` |

`LEETSOLV_CORS_ORIGINS` is not needed (the frontend and API share an origin).

## 4. Import existing data (one-time)

After the service is up, run the import against the deployed DB. Since the
source `~/.leetsolv/` lives on your machine, do this from a local checkout
with the same database path — or run it once before the volume has data:

```sh
# locally, pointing at a copy of the production DB path is not possible on
# Railway's volume; instead import once via a shell in the container:
railway run python -m app.import_cli --leetsolv-dir /path/to/your/.leetsolv
```

For the common case (a few questions), the simplest is to run the import
locally, then copy the resulting `leetsolv.db` onto the volume:

```sh
cd backend && python -m app.import_cli            # writes ./leetsolv.db
railway volume upload ./leetsolv.db /data/leetsolv.db
```

## Verify

- `https://<app>.up.railway.app/api/health` → `{"ok": true}`
- Visit the root: you should get the login screen, then GitHub OAuth, and
  (as the owner) land in the review queue.
