---
type: project-status
project: sherpa-tax-rule-studio
last_updated: 2026-04-27
---

# STATUS — sherpa-tax-rule-studio

*The freshest file. Answers "where am I on this project?" Updated at the end of every substantive session.*

---

## Current state

Active spec-authoring tool. RS Supabase holds **77 TaxForms / 371 FlowAssertions** (other tracks are
seeding too — check the index, not this line, for exact counts). Newest on the 1065 track: `1065_SE`
**leg 2** (the 14a SE-base sub-spec, worksheet WS1a–WS5) seeded + exported 2026-07-02, Ken-approved.
Leg 1 (classification) was built into tts at `a8c7da4`; the leg-2 export is ingested in tts at
`e5f2795` with B1–B7 pinned as pending-skips.

## In progress

- [ ] Nothing in flight on the 1065_SE track in RS. (Other tracks: see FORM_7217 / MeF entries in
  session_log.md — owned by parallel sessions.)

## Next up

1. ~~tts build leg~~ **DONE + DB-VERIFIED 2026-07-02 (tts `dd4ec14` + `ccc8a11`):** SE-base worksheet
   compute live (WS1a–WS5 FormFieldValues; WS1d/WS2 auto-pull page-1 line 6; per-partner base = share
   of WS3a) + `R-SE-NONIND` guard + 3 new diagnostics; B1–B7 un-skipped (57 unit tests, 0 skipped) AND
   **the end-to-end DB pipeline suite `test_1065_se_pipeline_leg.py`: 9/9 green** against the shared
   test DB (real seed → Partner rows → compute_return → diagnostics; the two pooler AdminShutdown
   blips re-ran clean). The 1065_SE unit is fully closed: spec→seed→compute→test→DB-verified.
2. ~~4797 recapture-classification unit~~ **DONE 2026-07-02 (RS `9e38bb2` seeded/exported; tts
   `12725b6` built):** character-based `resolve_recapture_type` (Buildings/Improvements → §1250;
   is_qpp → §1245(a)(3)(G); override for the other (a)(3) exceptions); §1250 ordinary = min(gain,
   line-26a additional depr incl. bonus — i4797 verbatim resolved the bonus-on-QIP question);
   DepreciationAsset +section_1250_additional_depr +is_qpp (mig 0152); 4 new D_4797_* diagnostics
   registered; the pinned test FLIPPED; C1-C3 + counterfactual — 40 passed. Optional: DB pipeline
   stamp on the entity-side aggregate (say the word). Historical note kept below:
   ORIGINAL FINDING — CONFIRMED tts bug —
   `resolve_recapture_type()` (compute.py:1272) classifies by recovery period, so 15-yr QIP/land
   improvements get §1245 full recapture instead of §1250; `test_improvements_15yr_is_1245` pins the
   bug; propagates into box 14a via ws 1d/2. Ken must adjudicate: property-character classifier
   (per-asset determination + diagnostic), 150DB additional-depreciation handling, and whether bonus
   on QIP is §1250(b) additional depreciation (UNVERIFIED — flagged, not guessed).
3. K-1 14b/14c pass-through verification (spec §14.4) — still out of scope.

## Blocked / waiting on

Nothing blocking RS. Item 2 above waits on Ken's scoping (his depreciation-specialty call).

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
