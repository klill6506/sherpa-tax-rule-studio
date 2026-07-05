"""Source-controlled record of which spec forms Ken has APPROVED for tts handoff.

Why this file exists (reconstructability): a spec's `status` lives in the DB and every
loader seeds it as `draft` (the model default). If approval were set by a one-off DB
edit, it would be lost on any rebuild (`seed_all` re-seeds everything as draft) — i.e.
it would "live only in Supabase", the exact anti-pattern the 2026-07-04 reconstructability
check cleaned up. So approval is recorded HERE, in source control, and applied by the
`approve_specs` management command (which `seed_all` runs as its final phase). Rebuild =
seed_all → statuses restored from this manifest.

Approval semantics: an entry means Ken (CPA) has signed off that the spec is ready to hand
to a coding agent for the tts build. It is a deliberate act — do NOT add a form here without
Ken's explicit approval. `approve_specs` flips DB status draft/review → approved for each.

Format: one dict per approved form.
  - form_number: matches TaxForm.form_number (case-insensitive, bare-number convention).
  - jurisdiction: optional, only to disambiguate if the same form_number exists for two
    jurisdictions (e.g. a federal and a GA form). Omit for the common single case.
  - approved: YYYY-MM-DD Ken signed off.
  - note: short free text (campaign, caveats).

Keep this list alphabetized by form_number for easy diffing.
"""

APPROVED_FORMS: list[dict] = [
    # Populated on Ken's sign-off. Example shape (commented until approved):
    # {"form_number": "4797", "approved": "2026-07-04", "note": "4797 campaign closed; nuance leg DB-verified"},
]
