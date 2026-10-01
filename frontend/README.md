# frontend

React + Vite + TypeScript SPA for leetsolv-web.

## Pages

- **Review** (`/`) — due + upcoming queues (priority order), inline review form that re-asks familiarity / memory / importance.
- **Problems** (`/problems`) — list with search + familiarity/importance/due filters, expandable detail (note editing, delete).
- **Add** (`/add`) — add a problem by LeetCode URL.
- **Dashboard** (`/dashboard`) — familiarity distribution, review activity, due-over-time.
- **History** (`/history`) — action log + undo.
- **Settings** (`/settings`) — SRS settings + the revocable mentor share link.
- **`/share/:token`** — read-only mentor view (same app, owner-only controls hidden).

## Auth

GitHub OAuth via the backend. The owner is pinned by `LEETSOLV_OWNER_GITHUB_ID`; anyone else is rejected. The mentor view authenticates through a `?share=` token appended to every API call.

## Develop

```bash
npm install
npm run dev        # http://localhost:5173, proxies /api -> http://localhost:8000
```

Run the backend first (`uvicorn app.main:app` in `../backend`).

## Build

```bash
npm run build      # tsc typecheck + vite build -> dist/
```
