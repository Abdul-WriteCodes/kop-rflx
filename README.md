# Kopt-OS (Reflex rebuild)

A rebuild of Kopt-OS — the Streamlit cooperative-society app — on
[Reflex](https://reflex.dev). Same Google Sheets backend, same features:
org registration, member sign-up, contributions, and loan requests /
approvals / repayments.

## What changed vs. the Streamlit version

- **UI framework**: Reflex compiles to a real React frontend + FastAPI
  backend instead of Streamlit's rerun-the-script model. State updates are
  event-driven, so only the parts of the UI that change actually re-render.
- **No pandas in state**: `sheets.py` now returns plain `list[dict]` instead
  of DataFrames, since that's what Reflex state vars serialize cleanly.
  All the aggregation logic (totals, balances) is still there, just done
  with plain Python.
- **Session handling**: Streamlit's `st.session_state` is replaced by Reflex's
  `rx.State` — each browser tab automatically gets its own isolated state
  instance, so `AuthState` *is* the session.
- **Secrets**: `st.secrets` is replaced by environment variables (`.env` file).
- **Routing**: Streamlit's manual `if role == "admin": ...` branching is
  replaced by real routes — `/`, `/admin`, `/member` — each with its own
  page and state, guarded by `on_load` handlers that redirect unauthenticated
  or wrong-role users back to `/`.

## Project layout

```
kopt_os/
├── kopt_os.py          # App entry point — registers routes/pages
├── sheets.py            # Google Sheets data layer (same tabs/schema as before)
├── styles.py             # Shared colors/spacing constants
├── state/
│   ├── auth.py           # Session, login, registration (base state)
│   ├── admin.py          # Admin dashboard state (inherits AuthState)
│   └── member.py         # Member dashboard state (inherits AuthState)
├── pages/
│   ├── landing.py        # "/" — login / register org / join as member
│   ├── admin.py           # "/admin"
│   └── member.py          # "/member"
└── components/
    └── navbar.py
```

## Setup

### 1. Google Sheet + service account

Same as the original app — see the sheet/service-account steps in your old
`SETUP.md` if you still have it: create a sheet, create a GCP service
account with Sheets + Drive API access, share the sheet with the service
account's email, and download the JSON key.

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```
SHEET_ID=your-sheet-id-from-the-url
GCP_SERVICE_ACCOUNT_FILE=service_account.json   # path to your downloaded key
```

Place your downloaded `service_account.json` in the project root (same
folder as `rxconfig.py`). **Don't commit it.**

For deployment (Railway, Render, Fly, etc.) where you can't easily upload a
file, set `GCP_SERVICE_ACCOUNT_INFO` instead — the entire JSON key file
contents as a single-line env var — and skip `GCP_SERVICE_ACCOUNT_FILE`.

### 3. Install and run

```bash
python -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt
reflex init      # first time only, sets up the frontend
reflex run
```

This starts the backend on `:8000` and frontend on `:3000`. Open
`http://localhost:3000`.

### 4. Deploy

Easiest path is **Reflex Cloud** (`reflex deploy`) since it's built for
exactly this. If you'd rather keep everything self-hosted alongside
BizTrack-OS, any host that can run a long-lived Python + Node process works
(Railway, Render, Fly.io) — just set the same env vars there and run
`reflex run --env prod`.

## Notes / things worth knowing

- All Google Sheets calls are still synchronous network requests, same as
  the original. For a small cooperative (dozens to low hundreds of members)
  this is fine. If it ever becomes a bottleneck, the event handlers in
  `state/admin.py` / `state/member.py` are the place to convert to Reflex
  background tasks (`@rx.event(background=True)`) so slow Sheets calls don't
  block a single user's UI.
- Passwords are still SHA-256 hashed with no salt, matching the original
  app. Fine for an internal MVP; worth upgrading to `bcrypt`/`argon2` before
  this handles real cooperative funds at scale.
- The monthly contributions chart on the member dashboard uses
  `rx.recharts` (bundled with Reflex) instead of Streamlit's `st.bar_chart`.
