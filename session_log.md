# Rule Studio — Session Log
*One entry per session that touches Rule Studio. Newest first.
Created 2026-06-10 during the 1040 campaign Phase 0 state audit (this file did not previously exist).*

---

## 2026-06-11 d — Topic 5 (Retirement Income) specs AUTHORED, READY_TO_SEED=False
- `specs/management/commands/load_1040_retirement.py` authored (Sprint Topic 5).
  Creates TWO TaxForms: **1040_RETIREMENT** (pseudo-form: ~33 facts [full 1099-R
  box surface + SSA-1099 + rollover/QCD/5329-linkage], 12 rules, 27 lines [4a/4b/
  5a/5b/6a/6b aggregation + the 18-line SS Benefits Worksheet], 7 diagnostics,
  14 scenarios) and **5329** (real face Part I: 3 facts, 3 rules, 4 lines, 1
  diagnostic, 3 scenarios). **7 flow assertions** (FA-1040-RET-01..07: 4a/4b &
  5a/5b rosters, 25b extension, 5329 line-4 rate, SS 6b=min(WS16,WS17)+85% cap,
  the statutory SS constants both years, the RED-gate truth table). **4 new
  authority sources** (Form 1099-R, i1099r Table 1 distribution codes, Form 5329,
  i5329 exception list) + 2 new excerpts on IRS_2025_1040_INSTR (the SS worksheet
  verbatim + lines 4a/4b/5a/5b rollover/QCD literals). Rule links 100% cited.
- Sources fetched + text-extracted the same day (tts-tax-app `server/.scratch/`:
  f1099r/i1099r/f5329/i5329-2025.pdf + dumps; SS worksheet from the existing
  i1040gi-2025.pdf p.31). Consolidated brief committed at tts-tax-app
  `server/specs/_topic5_retirement_source_brief.md`.
- **Ken's 5 scope decisions confirmed in-session 2026-06-11** and encoded: v1
  distribution-code set (1,2,3,4,7,8,9,B,D,G,H,Q,S,Y + IRA checkbox; rest RED);
  5329 exceptions 01-12+19 (≥13/99 RED); direct-to-Sch-2 shortcut; rollover/QCD
  preparer-entered; TY2026 statutory constants to confirm at the walk.
- **No year-keyed constants** (SS §86 thresholds + 5329 10%/25% are statutory
  non-indexed — same both years, unlike Topic 3's breakpoints).
- Verified: `py_compile` clean; `manage.py load_1040_retirement` REFUSES
  (READY_TO_SEED=False, "all populated", exit 1, zero DB writes — imports + guard
  + roster all valid). **RS DB UNCHANGED (still 35 forms).**
- NEXT: (1) write `check_retirement_integrity.py` (independent recompute of the
  SS worksheet + 5329 scenarios — the math-verification gate before the walk);
  (2) Ken's review walk; (3) on approval flip → seed → verify → export canonical
  `retirement_spec.json` + `5329_spec.json` to tts-tax-app + stage flow
  assertions; (4) tts-tax-app build legs.

## 2026-06-11 c — Spine bridge retired (Topic 3 compute leg, Ken-approved narrowing)
- `load_1040_spine.py` edited per the approved D_1040_001-narrowing plan
  (PM #11 pattern, new explicit `_retire_bridge_artifacts` step mirroring
  the Session-14 stub retirement): **R-TAX-07 rule (+1 authority link),
  D_1040_001 diagnostic, DG-1 scenario, and FA-1040-SPINE-15 deleted**;
  R-TAX-01 routing now names the QDCGT worksheet for supported
  preferential-rate paths + the still-blocked overrides
  (D_INTDIV_001..004 / D_1040_003/004); facts 3a/3b/7a + lines 3a/3b
  (now `calculated`) /7a/16 notes updated to the computed-feeder reality.
- `run_spine_check.py` clean (44 rules / 16 diags / 32 scenarios / 15
  assertions, 0 uncited, no dangling links) → loader re-run idempotent
  against the deployed DB (retirement report: rules+links=2, diags=1,
  scenarios=1, FAs=1). **RS DB: 35 forms, FlowAssertions 75; 1040 FA
  export 61 → 60 (SPINE-15 gone, verified).**
- Deployed `lookup/1040/export/` semantically diffed vs the old canonical
  spec: ONLY the intended removals + the 8 narrowed-note items — committed
  to tts-tax-app as the new canonical `server/specs/1040_spine_spec.json`.

## 2026-06-11 b — 1040_INTDIV / SCH_B seeded on Ken's approval
- Review packet walked with Ken in-session (six judgment items incl. the
  WS18/WS21 half-up whole-dollar rounding, both years' breakpoint tables,
  aggregation rosters, diagnostics severities, the 21 scenarios, the
  D_1040_001-narrowing plan). **Approved as authored.**
- `READY_TO_SEED` flipped → `load_1040_intdiv_qdcgt` run clean (no en-route
  fixes). Seeded: 1040_INTDIV (55 facts/17 rules/30 lines/10 diags/15
  scenarios), SCH_B (5/6/10/7/6), 12 flow assertions, 4 new sources + 5 new
  excerpts on existing, 37 links (100% cited). **RS DB: 35 forms,
  FlowAssertions 76.**
- Deployed exports verified (`lookup/1040_INTDIV|SCH_B/export/` — counts +
  both years' breakpoints + the ID-Q9 248 rounding pin + SB-T1 2,375 tie all
  survive the round trip). Committed to tts-tax-app as canonical
  `server/specs/intdiv_spec.json` / `sch_b_spec.json` (`ebfe2d1`).
- `/api/flow-assertions/export/?entity_type=1040` now returns **61** (49 +
  12 INTDIV/SCHB). The 12 are STAGED in tts-tax-app
  (`flow_assertions_1040_intdiv_pending.json`) — wired leg by leg.
- Next: tts-tax-app build legs (seed → compute → render → input →
  diagnostics → assertions; D_1040_001 narrows via load_1040_spine edit at
  the compute leg).

## 2026-06-11 — Topic 3 specs authored (Interest, Dividends & QDCGT), READY_TO_SEED=False
- `specs/management/commands/load_1040_intdiv_qdcgt.py` authored: creates TWO
  TaxForms in one idempotent command. **1040_INTDIV (pseudo-form): 55 facts /
  17 rules / 30 lines / 10 diagnostics / 15 scenarios — 1099-INT/DIV document
  facts + aggregation to 1040 2a/2b/3a/3b/7a + 25b extension + the full
  25-line QDCGT worksheet. SCH_B: 5 facts / 6 rules / 10 lines / 7
  diagnostics / 6 scenarios. 12 flow assertions (FA-1040-INTDIV-01..10,
  FA-1040-SCHB-01..02), 4 new authority sources (Sch B face + instructions,
  1099-INT, 1099-DIV), 5 new excerpts on existing sources (QDCGT worksheet
  verbatim + Exception 1 + line sources on IRS_2025_1040_INSTR; §2.03/§4.03
  breakpoints on RP_2024_40/RP_2025_32), 37 rule links (100% cited).**
- Sources: 2025 f1040sb downloaded into the tts-tax-app manifest (SHA
  recorded); i1040sb (3pp), i1040gi pp.25-26/31/33/37-38, 1099-INT/DIV
  Rev. 1-2024 faces, RP 2024-40 §2.03 + RP 2025-32 §4.03 all transcribed
  positionally the same session (dumps in tts-tax-app server/.scratch/).
- **Year-keyed constants (the only ones):** QDCGT WS6/WS13 breakpoints.
  TY2025 triple-verified (rev proc + worksheet face + prior capture);
  TY2026 from RP 2025-32 §4.03 — incl. the trap that WS13 single ≠ MFS
  (533,400 vs 300,000) while WS6 single == MFS.
- **Six judgment items flagged for Ken** (module docstring + rule
  descriptions): ABP box-11/12 default subtraction, per-doc tax-exempt
  floor, box-10 market-discount inclusion, WS18/WS21 half-up whole-dollar
  rounding (pinned by scenario ID-Q9 247.50→248), the Exception-1
  preparer-assertion fact, 3a override convention for holding-period
  exceptions.
- **Spine supersession documented:** R-TAX-07/D_1040_001 bridge NARROWS to
  D_INTDIV_001/002/003/004 (Sch D required / unasserted 2a / 8814 / 2555);
  spine R-PAY-02 25b roster extends to DIV box 4; 1040 2a/2b/3a/3b become
  computed feeders. D_1040_001 retires at the build leg via spine-loader
  edit (PM #11 pattern) on Ken's approval.
- `check_intdiv_integrity.py` (RS root): structural checks + INDEPENDENT
  recomputation of every scenario — full 25-line worksheet from its own
  bracket/breakpoint transcription (2026 MFJ uppers verified against the
  Ken-blessed compute.py table), boundary-pair checks, rounding-pin
  load-bearing check, cross-fixture SB-T1 == ID-T1 roster tie. ALL CHECKS
  PASS.
- Guard verified: `manage.py load_1040_intdiv_qdcgt` refuses with
  CommandError while READY_TO_SEED=False. No DB writes this session.
- Next: Ken's review walk (packet in the tts-tax-app session) → flip →
  seed → export 1040_INTDIV/SCH_B specs + flow assertions → build legs.

## 2026-06-10 PM #12b — SCH_1/SCH_2/SCH_3 seeded on Ken's approval
- Review packet walked with Ken in-session (totals formulas incl. the Sch 2
  line-20 exclusion, sign conventions, diagnostics severities, 13 scenarios,
  8812 placeholder re-pointing by semantic content). **Approved as authored.**
- `READY_TO_SEED` flipped → `load_1040_sch123` run. One fix en route: the
  IRC_62 excerpt carried `requires_human_review` — **AuthorityExcerpt has no
  such field (source-level only, re-learned from PM #5)**; moved the flag into
  summary_text. Atomic transaction = no partial writes from the failed run.
- Seeded: SCH_1 (69 facts/10 rules/63 lines/6 diags/6 scenarios), SCH_2
  (53/10/45/5/4), SCH_3 (34/8/33/3/4), 13 flow assertions, 36 links (100%
  cited). **RS DB: 33 forms, FlowAssertions 64.**
- Deployed exports verified (`lookup/SCH_1|SCH_2|SCH_3/export/` — counts match,
  R-S2-05 "EXCLUDES L20" + S2-T2 1884 + S1-T2 -21000 survive the round trip).
  Committed to tts-tax-app as canonical `server/specs/sch_{1,2,3}_spec.json`.
- `/api/flow-assertions/export/?entity_type=1040` now returns 49 (13 CTC +
  7 SCH1A + 16 SPINE + 13 SCH123). The 13 are STAGED in tts-tax-app
  (`flow_assertions_1040_sch123_pending.json`) — wired leg by leg.
- Export-format note: spec export top-level keys are `metadata` / `facts` /
  `rules` / `line_map` / `diagnostics` / `tests` / `authority_sources` /
  `state_conformity` (no `form` / `lines` keys).

## 2026-06-10 PM #12 — Schedules 1/2/3 specs authored (Sprint Topic 2), READY_TO_SEED=False
- `specs/management/commands/load_1040_sch123.py` authored: creates THREE TaxForms
  (SCH_1 / SCH_2 / SCH_3, FED TY2025 v1) in one idempotent command.
  **SCH_1: 69 facts / 10 rules / 63 lines / 6 diagnostics / 6 scenarios.
  SCH_2: 53 / 10 / 45 / 5 / 4. SCH_3: 34 / 8 / 33 / 3 / 4.
  13 flow assertions (FA-1040-SCH1-01..04, SCH2-01..05, SCH3-01..04).
  4 new authority sources (3 form faces + IRC_62), 36 rule-authority links
  (100% cited).**
- Sources: 2025 f1040s1/f1040s2/f1040s3 downloaded fresh from irs.gov into
  tts-tax-app's manifest (SHA256 recorded) and transcribed positionally with
  pymupdf the same session. Schedule 3 (2025) is a SINGLE page — manifest
  corrected. Schedule 2 (2025) adds EPE recapture lines 1d/1e/1f/19 (Form 4255).
- Aggregation-form scope: every line direct-entry; computed lines are the face
  sums only (S1: 9/10/25/26 · S2: 1z/3/7/18/21 · S3: 7/8/14/15). NO year-keyed
  constants exist on these forms — the TY2026 faces must be re-verified on
  release (tracker note).
- Load-bearing subtleties encoded: **Sch 2 line 20 (965 installment) is NOT in
  the line-21 sum** (scenario S2-T2 pins 1,884 not 3,884); Sch 1 8a/8d/8s are
  NEGATIVE entries (parentheses); 'combine' lines 10/9 allow negatives (loss
  year scenario pins -21,000); Sch 3 6l (8978) is signed; reserved lines
  S1.22 / S2.10 / S3.6e police-checked.
- Spine supersession documented per rule: 1040 lines 8/10/17/20/23/31 become
  COMPUTED feeders from S1.10/S1.26/S2.3/S3.8/S2.21/S3.15, retiring the spine's
  six direct-entry schedule facts. 8812 placeholder re-pointing (se_tax_total,
  additional_medicare_tax_amount, other_employment_taxes, excess_ss_rrta_withheld,
  deductible_se_tax_half, schedule_3_pre_ctc_credits_total) flagged for Ken in
  the review walk — the 8812 spec's Sch 2/3 line references predate the 2025
  renumbering.
- `check_sch123_integrity.py` (RS root): pre-seed checker — duplicate ids,
  uncited rules, dangling links, choice fields, rule inputs vs declared facts,
  AND independent re-computation of every scenario sum. ALL CHECKS PASS.
- Guard verified: `manage.py load_1040_sch123` refuses with CommandError while
  READY_TO_SEED=False. No DB writes this session.
- Next: Ken's review walk (packet prepared in tts-tax-app session) → flip →
  seed → export SCH_1/SCH_2/SCH_3 specs + flow assertions → tts-tax-app build legs.

## 2026-06-10 PM #11 — D_1040_017 added to the spine spec (digital-asset question)
- Ken approved closing the digital-asset question gap (REVIEW_QUEUE item) in
  tts-tax-app's session Q&A; the spine spec already carried the fact
  (`digital_assets_answer`, choice yes/no, required) but no diagnostic.
- `load_1040_spine.py`: +D_1040_017 "Digital-asset question unanswered"
  (warning; condition `digital_assets_answer is None`). Loader re-run
  (idempotent): 1040 now 17 diagnostics; everything else unchanged
  (45 rules / 91 facts / 72 lines / 33 scenarios / 16 flow assertions).
- Deployed export verified (17 diagnostics, D_1040_017 last); semantic diff vs
  the prior canonical export showed ONLY the added diagnostic. Committed to
  tts-tax-app as `server/specs/1040_spine_spec.json`.
- New helper `run_spine_check.py` (RS root): wraps `check_spine_integrity.py`
  with django.setup() — the checker imports loader modules that touch models
  and can't run bare. (Note: `poetry run python -c` with a MULTILINE script
  silently produces nothing on this Windows box — use wrapper files.)

## 2026-06-10 PM #5b — 1040 SPINE seeded on Ken's approval
- Review packet walked with Ken in-session (constants per year, the Tax Table
  midpoint/half-up convention inference, diagnostics severities, stub
  retirement, 33 scenarios). **Approved as authored.**
- `READY_TO_SEED` flipped → `load_1040_spine` run: stub retired (R001/R002 +
  line_11_agi + line 11), then 91 facts / 45 rules / 72 links / 72 lines /
  16 diagnostics / 33 scenarios / 16 flow assertions. RS DB: 30 forms (1040
  updated in place), FlowAssertions 51, all 1040 rules cited.
- Deployed export verified: `lookup/1040/export/` returns the spine (metadata
  correct, R-TAX-02 present, stub rules absent, TT-5 half-up pin intact).
  Committed to tts-tax-app as `server/specs/1040_spine_spec.json`.
- `/api/flow-assertions/export/?entity_type=1040` now returns 36 (13 CTC +
  7 SCH1A + 16 SPINE). The 16 spine assertions are STAGED in tts-tax-app
  (`flow_assertions_1040_spine_pending.json`) — wired leg by leg as compute lands.

## 2026-06-10 PM #5 — 1040 SPINE spec authored (Sprint Topic 1), READY_TO_SEED=False
- `specs/management/commands/load_1040_spine.py` authored: updates the Session-14
  "1040" stub TaxForm in place into the full spine spec. **45 rules (100% cited,
  72 authority links), 91 facts, 72 lines, 16 diagnostics, 33 scenarios, 16 flow
  assertions (FA-1040-SPINE-01..16), 11 new authority sources.**
- Stub retirement: the loader deletes R001/R002 (re-specified as R-CR-03/R-PAY-06),
  fact `line_11_agi` (→ `agi`), and line "11" (→ 11a/11b) with stdout notes.
- All constants transcribed from primary sources fetched + layout-extracted the
  same day: 2025 f1040.pdf (both pages, line by line); Pub 1040-TT (2025) Tax
  Table + Tax Computation Worksheet; i1040gi (2025) Line 16 routing / std-ded
  exceptions / L37-38 rules; Pub 501 (2025) Tables 6/7/8; RP 2024-40 §2.01;
  RP 2025-32 §4.01/§4.14; OBBBA §70102.
- **Tax Table convention verified, not assumed:** rows are $10/$25/$50 bands
  (0-5→$0; 5-25 by $10; 25-3,000 by $25; 3,000-100,000 by $50); row tax = rate
  schedule at the band MIDPOINT rounded HALF-UP (pinned by published rows
  302.50→303, 357.50→358, and the 99,950-100,000 row across all four columns).
  QSS uses the MFJ column (footnote). ≥$100,000 → TCW ≡ cumulative brackets
  (verified equal at $100,000). The midpoint inference is flagged for Ken's
  explicit blessing in the review packet.
- `check_spine_integrity.py` (repo root): pre-seed content-list checker —
  uncited rules / dangling links / duplicate ids / excerpt+choice field
  validation. Run via `Get-Content check_spine_integrity.py -Raw | poetry run
  python manage.py shell` (or exec in a shell). All checks pass.
- Guard verified: `manage.py load_1040_spine` refuses with CommandError while
  `READY_TO_SEED = False`. No DB writes this session.
- Next: Ken's review walk (packet prepared in tts-tax-app session) → flip →
  seed → export → wire into tts-tax-app compute.

## 2026-06-10 PM — SCH_1A seeded on Ken's approval
- Review packet walked with Ken in-session (constants, rounding directions,
  17 requires_human_review excerpts, diagnostics severities, 5 documented
  v1 deviations in tts-tax-app). **Approved.**
- `READY_TO_SEED` flipped → `load_sch_1a` run: 38 rules, 47 lines, 31 facts,
  6 diagnostics, 21 scenarios, 7 flow assertions, 66 authority links (all
  rules cited). RS DB now 30 forms.
- Export verified via `lookup/SCH_1A/export/`; committed to tts-tax-app as
  the canonical `server/specs/sch_1a_spec.json`. tts-tax-app implemented
  Part IV (car loan) from it the same day — all 21 scenarios green.
- Flow-assertion export note: `/api/flow-assertions/export/?entity_type=1040`
  returns 20 (13 CTC + 7 SCH1A). RS SCH1A-01..04 duplicate locally-wired
  assertions in tts-tax-app; -05/-06/-07 were newly wired there.

## 2026-06-10 — 1040 campaign Phase 0 state audit (read-only)
- No RS code or data changes. Inventoried authored specs vs. the deployed DB.
- Deployed RS DB holds 29 seeded forms (all status=draft). 1040-relevant: SCH_8812
  (1,140 facts/rules — exported + implemented in tts-tax-app), 1040 stub (2 rules:
  L11/19/28), plus business forms reusable at the 1040 level.
- **SCH_1A status confirmed: authored, NOT seeded.** All six parts + 21 test
  scenarios + 7 diagnostics + 8 flow assertions live in
  `specs/management/commands/load_sch_1a.py` with `READY_TO_SEED = False` (line 77).
  Awaiting Ken's review → flip → seed → export → verify (tts-tax-app already
  implements Parts I/II/III/V/VI from Ken's scope docs; Part IV is spec-ahead-of-compute).
- Noted: RS has no per-form `ready_to_seed` DB field — the sentinel is per-loader-command.
- RS root STATUS.md / MEMORY.md / DECISIONS.md are stale (last touched 2026-04-27,
  pre-dating Sessions 14-17). Update them next time RS work happens.

## Backfill — sessions before this log existed (from git history)
- **2026-06-03 (Sessions 16-17):** `load_sch_1a.py` authored — scaffold, all six parts,
  21 scenarios (`4273295`, `0d49a44`, `ab45137`). NOT seeded.
- **2026-05-26 (Session 14):** SCH_8812 (CTC/ACTC) spec authored + seeded + exported
  (`98c2fb2`, `61da16a`); exports in `exports/session14/`.
- **2026-03 (Sessions 6-13):** 1120-S family complete — 29 forms, flow-assertion
  model + API + export endpoint, lookup-by-form-number API.
