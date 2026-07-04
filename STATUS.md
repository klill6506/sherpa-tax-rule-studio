---
type: project-status
project: sherpa-tax-rule-studio
last_updated: 2026-07-04
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

**► ACTIVE (Ken picked 2026-07-03, "knock out 1"): verify the K-1 box 9c pass-through.**
The 2026-07-03 K9c fix (tts `f23dc54`) made `aggregate_dispositions` write the 1065 entity unrecaptured
§1250 gain to Schedule K line **K9c**, and `k1_allocator` (server/apps/returns/k1_allocator.py: `"K9c"`→
box **9c**, LT_CAPITAL category; the box map at ~line 159) distributes it to each partner's K-1. That
downstream allocation was NOT separately re-verified — this task closes it.
- **Where:** tts `server/tests/test_4797_pipeline_leg.py` (the DB stamp). Add 1–2 focused tests using
  `allocate_all_k1s(tr)` (already imported by the sibling `test_1065_se_pipeline_leg.py` via its
  `_k1_by_partner` helper — mirror that pattern: `{e["partner"].name: e["k1_data"] for e in allocate_all_k1s(tr)}`).
- **Scenario:** a 1065 return + a real §1250 disposition that produces a non-zero entity K9c (e.g. the C1
  shape — Improvements, method="NONE" for determinism, prior_depr 100k, cost 400k/sales 500k,
  section_1250_additional_depr 20k → K9c = 80,000), with **2 partners** at, say, 60/40 profit %.
- **Assert:** `_line(tr,"K9c") == 80000.00` (entity), AND each partner's `k1_data["9c"]` = their share
  (48,000 / 32,000); the sum of partner 9c == entity K9c (RECON). Confirm box 9c is allocated by the
  LT-capital/profit-% ratio (check whether k1_allocator uses profit_pct for LT_CAPITAL — read it first).
- **Run:** `poetry run pytest tests/test_4797_pipeline_leg.py -q --reuse-db --timeout=1800` (shared Supabase
  test DB; pooler has been flaky — check for a parallel pytest + drop a stale test_postgres first, memory
  `tts-test-db-collisions`; transient AdminShutdown/Deadlock re-runs clean). On green: commit + push tts,
  update STATUS Known-issues (drop the "not separately re-verified" caveat) + session_log.
- Small unit; no scoping round needed. The RS 4797 spec is unchanged (this is a tts-only verification).

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
   registered; the pinned test FLIPPED; C1-C3 + counterfactual — 40 passed.
   ~~Optional: DB pipeline stamp on the entity-side aggregate~~ **DONE + DB-VERIFIED 2026-07-03
   (tts `08c5382`):** `test_4797_pipeline_leg.py` — real 1065 seed → DepreciationAsset dispositions →
   `compute_return`/`aggregate_dispositions` over the shared test DB. **11/11 green** (6 classification
   C1-C3+QPP+override+KENFLAG, 1 SE-base coupling: C1 ordinary recapture rides 1a→K1, auto-pulled to
   WS2 so WS3a excludes it, 4 diagnostics D_4797_CLASS/_ADDL/_QPP/quiet). Only non-passes were the known
   transient pooler AdminShutdown drops (re-ran clean). **The stamp CAUGHT a confirmed bug — Ken said
   "go ahead", FIXED same session (tts `f23dc54`):** `aggregate_dispositions` was writing the 1065
   unrecaptured §1250 gain to the 1120-S line K8c (silently dropped, never reaching K-1 box 9c); now
   form-branched to K9c. The pinned test flipped from asserting K9c=0 to K9c=80000. Historical note below:
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

- **⚠ PUBLIC MIRROR (2026-07-04):** this `STATUS.md` and `session_log.md` are auto-copied into the
  **public** `klill6506/tts-tax-status` repo (`rule-studio/` subfolder) on every session-close sync,
  even though the RS repo itself is going private. Keep client PII and sensitive firm specifics OUT of
  both files — the `sync_status_mirror.ps1` PII guard only blocks SSN/EFIN shapes, not prose.
- ~~tts 1065 unrecaptured-§1250 misroute to K8c~~ **FIXED 2026-07-03 (tts `f23dc54`)** —
  `aggregate_dispositions` now form-branches the unrecaptured-§1250 line (`K9c` for 1065, `K8c` for
  1120-S). NOTE the downstream box-9c partner pass-through (k1_allocator K9c→box 9c) is now fed but was
  not separately re-verified — still nominally out of scope; flag if a 1065 with a §1250 disposition
  shows an unexpected box 9c.
- `1065_SE` case-law authority (`CASELAW_SE_LP`) sits on a **developing circuit split** and is
  `requires_human_review=True` — **re-verify each filing season** and on any ruling in the pending
  Soroban (2nd Cir.) / Denham (1st Cir.) appeals; an appellate reversal could flip the §6 GA
  include-on-undetermined default.
- Loaders across the repo use free-text `source_type`/`scenario_type` values outside the model enums
  (e.g. `"statute"`); Django doesn't enforce choices at the DB level so they seed fine. `1065_SE` uses
  `"statute"`/`"regulation"`/`"case_law"`/`"official_instructions"` to match established practice.

## Recent wins

- 2026-07-04: **cross-repo housekeeping** (Ken's INSTRUCTION FOR CC, no spec/compute) — added the
  `RULE STUDIO AUTHORING TRACK` to tts-tax-app SEASON_CHECKLIST.md (`fde3655`); recorded **D-2 (1041
  Schedule I AMT RED-DEFERRED for season one)** in RS DECISIONS.md (`48e44cc`, cross-refs D-1
  spec-first/reconcile-compute rule); extended `sync_status_mirror.ps1` to mirror RS STATUS.md +
  session_log.md into a `rule-studio/` subfolder of the public tts-tax-status repo; and **created the
  public `klill6506/tts-tax-status` repo** (was 404ing — the carried one-time item). See session_log.
- 2026-07-03: 4797 **nuance leg** (the 3 depreciation nuances) authored + gated + **SEEDED + EXPORTED**
  (RS `03a5606`; TaxForms 78 / FlowAssertions 381). Ken walked 2 decisions (AskUserQuestion): D1 = new
  `f4797_section_1245_exception` field auto-§1245 for (D)/(E)/(F) + `D_4797_1245AG/PETRO/RRGR`; D2 =
  compute line 26a (actual incl. bonus − SL on unreduced basis) where MACRS data present, `D_4797_ADDL`
  the fallback. Law verified verbatim (§1245(a)(3)(D/E/F), §168(i)(13)/(e)(4)/(b)(2)(A), §1250(b)(1)/(3),
  i4797 26a); new `IRC_168` source. Gate ALL PASS (27/8/34/14/20/19). `4797_spec.json` exported to tts.
  **tts BUILD LEG COMPLETE** — sub-leg A (classifier: field + mig 0157 + resolve_recapture_type + 3
  diagnostics) + sub-leg B (engine-computed 26a = actual incl. bonus − SL on unreduced basis;
  _resolve_1250_additional_depr override/compute/fallback; D_4797_ADDL demoted to fallback). **49 unit tests +
  pipeline DB stamp 15/15 green.** Committed tts `98ac1c5` + `be47294` — **now on remote** (the parallel EIC
  `0156` push carried them up; clean linear 0155→0156→0157, deploy-safe). **All three 4797 nuances fully
  closed: spec→seed→export→build→unit→DB-verified, on remote (RS + tts).**
- 2026-07-03: 4797 classification unit **DB-VERIFIED** (tts `08c5382`) — `test_4797_pipeline_leg.py`
  11/11 green end-to-end over the shared test DB; the stamp CAUGHT and (Ken: "go ahead") FIXED the 1065
  unrecaptured-§1250 K8c→K9c misroute (tts `f23dc54`). The 4797 unit is fully closed: spec→seed→compute→test→DB.
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
