# North Andhra Livelihoods Survey — Response Dashboard

A FastAPI + React dashboard for C-RAW India's North Andhra Livelihoods Survey:
historical election context, live survey analytics, and the Neutral
Influencer / Volunteer Army tracker, synced from ODK Central with
role-based access control.

Layout on disk: this is a fully self-contained project folder, meant to be
its own git repo —
`dashboard/backend/`, `dashboard/frontend/`, `dashboard/docker-compose.yml`,
`dashboard/.env.example`, plus local copies of everything the app or its docs
depend on: `dashboard/data/retro/` (the ECI election data actually read at
runtime — see Data flow below) and `dashboard/docs/reference/` (files only
referenced in comments/docs for verification, never read by code: the
XLSForm, the field-agent roster PDF, and the XLSForm build script). These are
snapshots, not live-synced — if the source project (`eci/` or
`questionnaire/`, elsewhere in the wider c-rawWork workspace, not part of
this repo) produces updated versions, re-copy them here.

## Before this is production-ready

1. **`backend/app/constituencies_config.py` is filled in** — the 5 PCs
   (Araku, Srikakulam, Vizianagaram, Visakhapatnam, Anakapalli) are mapped to
   their 35 assembly constituencies, cross-verified from two independent
   sources: the XLSForm build script's PC/AC choice list
   (`docs/reference/build_xlsform_v2.py`) and the official `ac_master.csv`
   from the andhra_pradesh_retro MATData export (`data/retro/acs.csv` +
   `pcs.csv` here) — both agree, 35/35. Re-verify against the field-agent
   roster (`docs/reference/combined_pc_locations.pdf.pdf`) if either ever
   diverges.
2. **Verify `backend/app/sync/field_map.py`** against the real XLSForm
   (`docs/reference/North_Andhra_Livelihoods_Survey_ODK.xlsx`) and a real ODK
   Central submission payload. The field paths there are best guesses from
   the project brief, not confirmed against the form.
3. **Confirm the ODK Central form ID** currently deployed (the brief says
   `na_livelihoods_survey_v4` but says to verify in Central).

## Local development

Backend (run from `dashboard/`):
```
cd backend
python -m venv .venv && .venv/Scripts/activate   # or source .venv/bin/activate
pip install -r requirements.txt
# needs a running Postgres -- see docker-compose.yml for the easiest option,
# or point DATABASE_URL (app/config.py) at any local Postgres instance.
python -m app.seed admin@crawindia.com "Admin User" ChangeMe123! admin
python -m app.seed analyst@crawindia.com "Analyst User" ChangeMe123! analyst
python -m app.seed viewer@crawindia.com "Viewer User" ChangeMe123! viewer
python -m etl.load_eci_data
python -m etl.build_ac_boundaries   # only needed again if data/retro/ac_geom.csv changes
uvicorn app.main:app --reload
```

Frontend:
```
cd frontend
npm install
npm run dev
```
Visit http://localhost:5173 and sign in with one of the seeded accounts.

## Production deployment (AWS, same box as ODK Central or a sibling instance)

Run from `dashboard/`:
```
cp .env.example .env   # fill in real values, especially JWT_SECRET and ODK creds
docker compose up -d --build
docker compose exec backend python -m app.seed admin@crawindia.com "Admin User" <strong-password> admin
docker compose exec backend python -m etl.load_eci_data
```

`dashboard/data/` is bind-mounted read-only into the backend container (see
`docker-compose.yml`), so `load_eci_data.py` reads the same files there as in
local dev. `ac_boundaries.geojson` is baked into the frontend image at build
time instead (Vite copies `frontend/public/` as static assets) — regenerate
it with `python -m etl.build_ac_boundaries` on the host *before*
`docker compose up --build` if `data/retro/ac_geom.csv` has changed.

The frontend container listens on host port 8080 over plain HTTP — put it
behind the box's existing reverse proxy/TLS setup (or add one) and restrict
access to VPN/IP-allowlist rather than the open internet, given the PII on
the Influencers/Volunteers page. See the comment block at the top of
`docker-compose.yml`.

## Role-based access control

- **Admin** — full access to all 3 pages, including respondent names and
  phone numbers on the Influencers/Volunteers page, and the only role that
  can export that page as CSV. Every PII view or export is written to the
  `audit_log` table (`backend/app/models.py`).
- **Analyst** — all 3 pages, all charts and the map, but the API never
  returns `contact_name`/`contact_phone_1`/`contact_phone_2` fields to this
  role (`app/auth.py::strip_pii`, enforced server-side, not just hidden in
  the UI).
- **Viewer** — same as Analyst minus any export buttons.

Create/rotate users with `python -m app.seed <email> <name> <password> <role>`.

## Data flow

ODK Central → `backend/app/sync/odk_sync.py` (pyodk, scheduled every
`ODK_SYNC_INTERVAL_MINUTES`, incremental via a submission-update watermark in
the `sync_state` table) → Postgres → FastAPI reads only from Postgres, never
from Central directly on a page load.

ECI historical results → `backend/etl/load_eci_data.py` (one-off, run once
and again whenever `data/retro/` is refreshed from the source
andhra_pradesh_retro export) → Postgres `eci_results` table. Loads both
assembly (AE) results per AC and the real Lok Sabha (GE) results per PC —
these are two different elections, not one derived from the other; the
Retrospective page's "Lok Sabha results" section is the latter.

Election-year electors/turnout are taken from the pre-computed
`constituency_master_*.csv` files, not from `elections.csv`'s own
`total_electors` field, which was found to be unreliable for some rows (see
the docstring in `load_eci_data.py`).

## Map

Page 2's map shows real AC boundary polygons (from
`backend/etl/build_ac_boundaries.py`, which converts
`data/retro/ac_geom.csv`'s WKB geometry into
`frontend/public/ac_boundaries.geojson` — regenerate after refreshing
`data/retro/`) colored by parliamentary constituency, plus respondent
lat/long points (no PII) on top. The map auto-fits to whichever has data:
respondent points if any are loaded, otherwise the boundary extent.
