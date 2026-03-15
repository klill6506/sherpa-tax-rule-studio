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
