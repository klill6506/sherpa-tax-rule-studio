# Sherpa Tax Rule Studio

## What This Is
A standalone tax law specification engine. NOT a tax prep app.
Ken (CPA) uses it to author structured, machine-readable rule packages
grounded in cited, versioned authority sources. Output gets handed to
coding agents to implement in tts-tax-app.

## Tech Stack
- Backend: Django 5.2 LTS + Django REST Framework
- Frontend: Vite + React 19 + TypeScript (SPA)
- Styling: Tailwind CSS (no hardcoded hex colors)
- Database: Supabase Postgres (own project, NOT shared with tts-tax-app)
- Serving: Django + WhiteNoise serves React SPA (same origin)
- Python deps: Poetry (Python 3.13)
- JS deps: npm
- Config: python-dotenv

## Project Structure
```
server/          — Django project (settings, urls, wsgi)
specs/           — Django app: form specification models
                   (TaxForm, FormFact, FormRule, FormLine,
                    FormDiagnostic, TestScenario)
sources/         — Django app: authority source models
                   (AuthoritySource, AuthorityExcerpt, AuthorityTopic,
                    RuleAuthorityLink, AuthorityFormLink, AuthorityVersion,
                    JurisdictionConformitySource, SourceFeedDefinition)
client/          — React/Vite/TypeScript SPA
client/src/      — React source code
tests/           — pytest + pytest-django tests
staticfiles/     — WhiteNoise collected static files (gitignored)
```

## Commands
- Backend: `poetry run python manage.py runserver`
- Frontend dev: `cd client && npm run dev`
- Tests: `poetry run pytest`
- Migrations: `poetry run python manage.py makemigrations && poetry run python manage.py migrate`
- Build frontend: `cd client && npm run build`
- Seed data: `poetry run python manage.py seed_sources`

## Database
- Own Supabase project (not shared with tts-tax-app)
- UUID primary keys, created_at/updated_at timestamps
- No firm_id (single-user tool)

## Key Design Principles
- Every rule must be grounded in cited, versioned authority
- Authority linkage via RuleAuthorityLink join table (not freetext)
- Rules with zero authority links should show a warning badge
- Export produces self-contained JSON spec packages

## Boot
- At boot: pull tts-tax-status; read BUILD_ORDER.md (order), SEASON_PLAN.md (gates),
  PRODUCT_MAP.md (scope). BUILD_ORDER is the single source of sequence for both lanes.

## Work Order Process (WORK_ORDERS.md is the RS front-door mechanism)
- `WORK_ORDERS.md` (RS repo root) holds the gap-check, the transition states, and Gate-1
  approval for the CURRENT order only. It does NOT keep its own ordered backlog — it takes
  the next authoring order FROM the BUILD_ORDER SPINE (canonical in tts-tax-status).
- Update WORK_ORDERS.md at EVERY transition (GAP-CHECKED → DRAFTING → AWAITING KEN →
  APPROVED → DISPATCHED → DONE). No silent authoring; the queue is the record.
- Two human gates are non-negotiable: Gate 1 = draft→published spec (Ken); Gate 2 =
  published→compute (the existing gated ingest in tts). A law change or Ken may START a
  draft; nothing CROSSES a gate unattended.

## Color System (Data Entry Fields)
- RED — Error, incomplete, or incorrectly formatted value
- YELLOW — Value pulled from another source (calculated, imported)
- GREEN — Value manually entered by the user

## API Pattern
- All routes under `/api/`
- specs app: `/api/forms/` and nested children (`/api/forms/{id}/facts/`, etc.)
- sources app: `/api/sources/`, `/api/topics/`, `/api/feeds/`, `/api/conformity/`,
  `/api/excerpts/search/`, `/api/rule-links/`, `/api/form-links/`

## Deployment
- Render.com (Virginia)
- build.sh handles full build pipeline
- WhiteNoise for static files, Gunicorn for WSGI
