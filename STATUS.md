---
type: project-status
project: sherpa-tax-rule-studio
last_updated: 2026-04-27
---

# STATUS — sherpa-tax-rule-studio

*The freshest file. Answers "where am I on this project?" Updated at the end of every substantive session.*

---

## Current state

Active spec-authoring tool. RS Supabase holds **76 TaxForms / 341 FlowAssertions**. Newest unit:
`1065_SE` (Form 1065 Schedule K / K-1 line 14a self-employment) seeded + exported 2026-07-01.

## In progress

- [ ] Nothing in flight in Rule Studio. The `1065_SE` handoff is complete (export fetchable).

## Next up

1. **tts-tax-app session (separate repo):** write the `seed_*` loader for `1065_se_spec.json`, seed it,
   then rewrite `compute_self_employment` to fetch it (replaces the silent limited-partner exclusion at
   `k1_allocator.py:223-225` and the independent `K14a = K1 + K4c` at `compute.py:288`). Gated on this export.
2. **14a SE-base sub-spec (RS):** the base itself (i1065 2025 worksheet lines 1a–3a — Form 4797 Part II
   gain/loss adjustment + conditional rental inclusions). **Coupled** with the 4797 §1245-vs-§1250 recapture
   verification (a recapture misclassification propagates into box 14a). Spec §14.

## Blocked / waiting on

Nothing blocking RS. The compute rewrite is intentionally deferred to a tts session (Ken's sequencing).

## Known issues

- `1065_SE` case-law authority (`CASELAW_SE_LP`) sits on a **developing circuit split** and is
  `requires_human_review=True` — **re-verify each filing season** and on any ruling in the pending
  Soroban (2nd Cir.) / Denham (1st Cir.) appeals; an appellate reversal could flip the §6 GA
  include-on-undetermined default.
- Loaders across the repo use free-text `source_type`/`scenario_type` values outside the model enums
  (e.g. `"statute"`); Django doesn't enforce choices at the DB level so they seed fine. `1065_SE` uses
  `"statute"`/`"regulation"`/`"case_law"`/`"official_instructions"` to match established practice.

## Recent wins

- 2026-07-01: `1065_SE` authored, seeded, exported (`1065_se_spec.json`, 38 KB) — 9 rules / 3 diagnostics
  / 10 tests / 7 authorities / 3 flow assertions, all rules cited, FLOW-14A-SE disabled. CFR/USC text
  quoted verbatim from primary sources.
- 2026-07-01 (prior sessions): SCHEDULE_A line 5a state-tax auto-total; FORM_8606 Roth basis tracker.

## Last session recap

*2026-07-01* — Authored the `1065_SE` spec as a faithful translation of the locked
`1065_se_line14a_spec.md`: one per-partner `se_classification` drives component treatment; four locked
decisions (undetermined→active safety net, LLC members on the active/passive axis, passive capital-GP
excluded, active capital-GP included); entity 14a derived bottom-up. Read the three Treasury regs + the
IRC subsections directly from the CFR/U.S. Code and quoted them verbatim (eCFR blocks automated fetches —
used the Cornell LII mirror). Seeded RS Supabase and confirmed `GET /api/forms/lookup/1065_SE/export/`
returns everything. Stopped at the fetchable export per the DoD; the compute rewrite is a separate tts session.
