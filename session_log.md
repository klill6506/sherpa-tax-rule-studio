# Rule Studio — Session Log
*One entry per session that touches Rule Studio. Newest first.
Created 2026-06-10 during the 1040 campaign Phase 0 state audit (this file did not previously exist).*

---

## 2026-06-15 — Form 5695 (residential energy credits §25D+§25C, Phase 2 third common form) spec leg — SEEDED + EXPORTED ✅
- **Ken approved the review walk in-session ("Approved — seed it, include render")** — the §25D 30% +
  fuel-cell $500/½kW cap + carryforward + tax limit; the §25C caps ($1,200 aggregate + $250/$500 doors
  / $600 windows / $600-per-item / $150 audit + the separate $2,000 heat-pump group, max $3,200); the
  OBBBA termination after 2025. Ken's 2 scope decisions: both parts with caps modeled; model the
  tax-liability limit + the §25D carryforward. Render INCLUDED (full 6-leg build).
- `load_1040_5695.py` + `check_5695_integrity.py` ALL CHECKS PASS (independent re-type of credit_25d/
  credit_25c + all 8 numeric scenarios; loader & gate share no math). Guard verified REFUSING. Fix:
  the loader was missing the FormRule import (NameError on first seed) → added.
- Flipped READY_TO_SEED → seeded: **FORM_5695** (21 facts / 4 rules / 15 lines / 6 diagnostics / 9
  scenarios / 7 cited links) + 6 flow assertions. **RS DB →57 forms, FA →182.** All rules cited. 3
  sources (i5695 / IRC §25D / IRC §25C).
- **KEY:** TY2025-only — OBBBA terminates BOTH credits after 12/31/2025 (D_5695_2026 RED for 2026+).
  §25D → Sch 3 5a (carries forward); §25C → Sch 3 5b (no carryforward, excess lost). The Credit Limit
  Worksheet ordering is simplified in v1 (i5695 requires_human_review). Deferred: joint occupancy,
  QM-PIN/CEE-tier qualification, per-door/window itemization.
- Deployed export verified HTTP 200 (`lookup/FORM_5695/export/`); committed to tts-tax-app as canonical
  `server/specs/5695_spec.json` + 6 FA staged in `flow_assertions_1040_5695_pending.json` (active 1040
  gate stays 171).
- Next (tts-tax-app): the 6 build legs — seed (FORM_5695 FormDef + ~21 e5695_* Taxpayer facts, the
  Sch-A/8889 return-level precedent) → compute (`compute_5695.py` → Sch 3 5a/5b; in the Sch-3 credit
  block, needs tax liability for the Credit Limit Worksheet) → render (download f5695.pdf) → input →
  diagnostics → assertions → tag `1040-form-5695-complete`.

## 2026-06-14 — Form 1099-G (unemployment, Phase 2 second common form) spec leg — SEEDED + EXPORTED ✅
- **Ken approved the review walk in-session ("Approved — seed it; no render form")** — §85
  full inclusion (NO exclusion for 2025/2026; the 2020 ARPA $10,200 was COVID-only), the
  same-year-repayment netting on Sch 1 line 7 (the "Repaid" literal), box 4 → 1040 line 25b,
  the §1341 prior-year-repayment RED, the box-5/6/7/9 RED, box 2 stays in STATE_REFUND.
- `load_1040_1099g.py` + `check_1099g_integrity.py` ALL CHECKS PASS (independent re-type of
  max(0, box1−repaid) summed + the box-4 aggregation + a "no exclusion ever applied" invariant
  + the 7 scenarios; loader & gate share no math). Guard verified REFUSING before the flip.
- Flipped READY_TO_SEED → seeded: **FORM_1099G** (10 facts / 4 rules / 7 lines / 5 diagnostics
  / 7 scenarios / 5 cited links) + 6 flow assertions. **RS DB →56 forms, FA →176.** All rules
  cited. 3 sources (IRC §85 / 2025 i1040 Sch 1 Line 7 / Pub 525).
- **KEY:** NO year-keyed constants — §85 full inclusion is identical for 2025/2026; the only
  year-sensitivity is the form line numbers (2025 i1040 Sch 1 Line 7 source = requires_human_review,
  re-verify the 2026 1099-G box layout + line 7 number ~Dec 2026). Ken's scope decisions:
  Form1099G doc model; same-year netting computed + §1341 RED; v1 box 1+4 only + other-boxes RED.
- Deployed export verified HTTP 200 (`lookup/FORM_1099G/export/`); committed to tts-tax-app as
  canonical `server/specs/1099g_spec.json` + 6 FA staged in `flow_assertions_1040_1099g_pending.json`
  (active 1040 gate stays 165).
- **NO RENDER LEG** (Ken's call) — 1099-G is an input document (like W-2), not filed with the
  return; the value renders on Schedule 1 (already built). Build legs (tts-tax-app): seed (a
  Form1099G doc model + mig + RLS + FORM_1099G FormDef + CRUD) → compute (`compute_1099g.py` →
  Sch 1 L7 + the 7_repaid literal + 1040 L25b; runs in the pre-formula-pass income feeder block —
  line 7 is INCOME, the compute_state_refund_db precedent) → input → diagnostics → assertions →
  tag `1040-form-1099g-complete`. RED-deferred: §1341 prior-year repayment, boxes 5/6/7/9.

## 2026-06-14 — Form 8889 (HSA, Phase 2 first common form) spec leg — SEEDED + EXPORTED ✅
- **Ken approved the review walk in-session ("Looks right.")** — the §223 limits +
  the catch-up + the deduction (min(own, limit−employer)) + the proration + the
  last-month rule + the married family split + the distribution/20% (with the
  exception) + Part III/10% + the Sch-2-17c/17d flow correction.
- `load_1040_form_8889.py` + `check_8889_integrity.py` ALL CHECKS PASS (independent
  re-type of the §223 limits + the proration + the deduction/distribution/Part-III
  math + the 11 scenarios; loader & gate share no math). Guard verified REFUSING.
- Flipped READY_TO_SEED → seeded: **FORM_8889** (18 facts / 6 rules / 24 lines /
  6 diagnostics / 11 scenarios / 11 cited links) + 6 flow assertions. **RS DB →55
  forms, FA →170.** All rules cited. 3 sources (i8889 / IRC §223 / Pub 969).
- CONSTANTS verified vs Rev. Proc. 2024-25 §2.01 (2025) + 2025-19 §2.01 (2026):
  self-only/family 2025 $4,300/$8,550, 2026 $4,400/$8,750; $1,000 catch-up (55+,
  statutory, both). FLOW: line 13 → Sch 1 L13; line 16 + line 20 → Sch 1 L8f; line
  17b (20%) → **Sch 2 L17c**; line 21 (10%) → **Sch 2 L17d** (corrected from the
  13c premise — both HSA additional taxes live under Sch 2 line 17 "Other").
- Deployed export verified HTTP 200 (`lookup/FORM_8889/export/`); committed to
  tts-tax-app as canonical `server/specs/form_8889_spec.json` + 6 FA staged in
  `flow_assertions_1040_8889_pending.json` (active 1040 gate stays 159).
- Next (tts-tax-app): the 6 build legs — seed (a per-owner **HSA** sub-model + RLS,
  the FORM_8889 FormDef + facts) → compute (`compute_8889.py` → Sch 1 L13/L8f + Sch
  2 L17c/L17d; **runs BEFORE compute_sch123** — L13 is an above-the-line ADJUSTMENT,
  the compute_state_refund_db precedent) → render (f8889.pdf, per-owner copies) →
  input → diagnostics → assertions → tag `1040-form-8889-complete`. RED-deferred:
  the 6% excess excise (5329 Part VII), the IRA→HSA funding distribution, non-spouse
  death. WALK ITEM: re-verify the 2026 Form 8889 line numbers when posted.

## 2026-06-14 — State refund worksheet (NEXT-UP #9, the LAST item) spec leg — SEEDED + EXPORTED ✅
- **Ken approved the review walk in-session ("No changes. Continue")** — the §111
  tax-benefit computation (Pub 525 Worksheet 2 + 2a): the SALT-cap recapture (the
  prior-year Sch A 5d/5e), the itemized-vs-standard difference limit, the negative-
  prior-year-TI reduction, the line-1/line-8z allocation, the §111 gates, the
  prior-year std-ded constants (2024 verified / 2025 interim), and the RED-deferred
  AMT/credit/multi-year exceptions.
- `load_1040_state_refund.py` + `check_state_refund_integrity.py` ALL CHECKS PASS
  (independent re-type of Worksheet 2/2a + the 2024/2025 std-ded + the 9 scenarios;
  loader & gate share no math). Guard verified REFUSING before the flip.
- Flipped READY_TO_SEED → seeded: **STATE_REFUND** (19 facts / 5 rules / 17 lines /
  7 diagnostics / 9 scenarios / 8 cited links) + 6 flow assertions. **RS DB →54
  forms, FA →164.** All rules cited. 3 sources (i1040 Sch 1 worksheet / Pub 525 /
  IRC §111).
- **KEY:** the SALT cap is NOT a compute constant — the worksheet reads the
  preparer-entered prior-year Sch A 5d/5e, so only the prior-year std-ded table is
  year-keyed (to the refund year = tax_year − 1). 2024 verified; 2025 INTERIM
  (requires_human_review, re-pin from the 2026 worksheet ~Dec 2026).
- Taxable income-tax refund → Sch 1 line 1; RE/PP + other recoveries → Sch 1 line 8z.
  NO IRS AcroForm — a statement page (the Simplified Method precedent).
- Deployed export verified HTTP 200 (`lookup/STATE_REFUND/export/`); committed to
  tts-tax-app as canonical `server/specs/state_refund_spec.json` + 6 FA staged in
  `flow_assertions_1040_sr_pending.json` (active 1040 gate stays 153).
- Next (tts-tax-app): the build legs — seed (the 19 sr_* Taxpayer facts + a
  STATE_REFUND FormDef worksheet + serializer) → compute (`compute_state_refund.py`
  → Sch 1 L1 + L8z; runs BEFORE the first formula pass — it's INCOME, feeds 1040
  line 8 / AGI, NOT a credit) → render (statement page) → input → diagnostics →
  assertions → tag `1040-state-refund-complete`. This is the LAST post-sprint item.

## 2026-06-14 — Form 8863 (Education Credits, NEXT-UP #8) spec leg — SEEDED + EXPORTED ✅
- **Ken approved the review walk in-session ("Looks good.")** — the §25A constants
  (AOTC 100%/25% to $4,000 / max $2,500 / 40% refundable $1,000; LLC 20% of
  $10,000 / max $2,000) + the shared phaseout ($90k/$180k ceiling, $10k/$20k
  divisor) + the per-student tiers + the 40% refundable split + the line-7
  kiddie-tax lockout (preparer checkbox, decision 2) + the full Credit Limit
  Worksheet (decision 3) + the MFS/dependent bars + the TY2026 §70606 defer.
- `load_1040_form_8863.py` + `check_8863_integrity.py` ALL CHECKS PASS
  (independent re-type of the §25A tiers + the shared phaseout + the LLC + the
  CLW + the 9 scenarios + the helper fns; loader & gate share no math). Guard
  verified REFUSING before the flip.
- Flipped READY_TO_SEED → seeded: **FORM_8863** (7 facts / 7 rules / 32 lines /
  7 diagnostics / 9 scenarios / 12 cited links) + 6 flow assertions. **RS DB →53
  forms, FA →158.** All rules cited. 3 sources (i8863 / IRC §25A / Pub 970).
- CONSTANTS verified from the published 2025 f8863.pdf (9/23/25) / i8863 / Pub
  970 — all §25A STATUTORY, NOT inflation-indexed (identical 2024/25/26). AOTC
  L8 (40% refundable) → 1040 L29; the nonrefundable education credit L19 (the
  Credit Limit Worksheet) → Schedule 3 L3.
- **varchar(20) lesson — this time a diagnostic_id:** `D_8863_AOTC_INELIGIBLE`
  (22) overflowed FormDiagnostic.diagnostic_id → renamed `D_8863_AOTC_INELIG`
  (18). Added a diagnostic_id length guard to the integrity gate (it already
  guarded rule_id). (`R-8863-AOTC-PHASEOUT` = exactly 20, fits.)
- Deployed export verified HTTP 200 (`lookup/FORM_8863/export/`); committed to
  tts-tax-app as canonical `server/specs/form_8863_spec.json` + 6 FA staged in
  `flow_assertions_1040_8863_pending.json` (active 1040 gate stays 147).
- Next (tts-tax-app): the 6 build legs — seed (a new **EducationStudent** model +
  RLS, the FORM_8863 FormDef + facts; decision 1) → compute (`compute_8863.py`:
  the per-student AOTC + LLC + phaseout + the Credit Limit Worksheet → Sch 3 L3 /
  1040 L29) → render (f8863.pdf downloaded; per-student Part III copies) → input →
  diagnostics → assertions → tag `1040-form-8863-complete`.

## 2026-06-14 — Form 8962 (Premium Tax Credit, NEXT-UP #7) spec leg — SEEDED + EXPORTED ✅
- **Ken approved the review walk in-session ("Looks right")** — Table 2 applicable
  figure (interpolation, verified endpoints) + the 2024 FPL + Table 5 + line-5
  truncation + the monthly method + the iterative SEHI<->PTC + Parts 4/5 + the
  2026 RED-defer + the two requires_human_review flags (the full Table 2 lookup;
  the Pub 974 convergence).
- `load_1040_form_8962.py` + `check_8962_integrity.py` ALL CHECKS PASS (independent
  re-type of the FPL/Table-2/Table-5 math + the 5 helper fns + the 6 scenarios;
  loader & gate share no math). Guard verified REFUSING before the flip.
- Flipped READY_TO_SEED → seeded: **FORM_8962** (17 facts / 13 rules / 38 lines /
  6 diagnostics / 6 scenarios / 15 cited links) + 6 flow assertions. **RS DB →52
  forms, FA →152.** All rules cited. 3 sources (i8962 / IRC §36B / Pub 974).
- CONSTANTS verified cell-by-cell from the 2025 i8962 PDF: line 5 trunc cap 401
  (400% cliff suspended 2025); Table 2 0/.02/.04/.06/.085 (+.0004/pt 150-300%,
  +.00025/pt 300-400%); Table 5 375/975/1,625 single & 750/1,950/3,250 other,
  no-limit >=400%; 2024 FPL 48-state 15,060/+5,380, AK 18,810/+6,730, HI 17,310/
  +6,190. Net PTC L26 -> Sch 3 L9; excess L29 -> Sch 2 L1a.
- Deployed export verified HTTP 200 (`lookup/FORM_8962/export/`); committed to
  tts-tax-app as canonical `server/specs/form_8962_spec.json` + 6 FA staged in
  `flow_assertions_1040_8962_pending.json` (active 1040 gate stays 141).
- rule_id length lesson (again): FormRule.rule_id is varchar(20) —
  R-8962-HOUSEHOLD-INCOME (23) / R-8962-APPLICABLE-FIGURE (24) overflowed; renamed
  -> R-8962-MAGI / R-8962-APPL-FIG.
- Next (tts-tax-app): the 6 build legs — seed (a new Form1095A model + RLS, mig
  0069; FORM_8962 FormDef + facts) → compute (`compute_8962.py`: the MAGI helper +
  the monthly method + the SEHI iterative + Part 4/5 → Sch 3 L9 / Sch 2 L1a; the
  BIGGEST build leg) → render (f8962.pdf downloaded) → input → diagnostics →
  assertions → tag `1040-form-8962-complete`.

## 2026-06-14 — Schedule E (Part I) + Form 8582 (NEXT-UP #6) spec leg — SEEDED + EXPORTED ✅
- **Ken approved the review walk in-session ("Looks good.")** — the $25k/$12,500
  special allowance + the 50%×($150k/$75k−MAGI) phaseout + the MFS amounts + the
  modified-AGI add-back list (NOT §199A) + the v1 simplified-bucket deviations
  (aggregate columns, no per-activity Parts IV/V, RE-pro RED, MFS-together $0,
  §280A vacation-home not applied, partial MAGI add-backs).
- `load_1040_schedule_e.py` seeds BOTH forms (the load_1040_schedule_d 3-form
  precedent); `check_schedule_e_8582_integrity.py` ALL CHECKS PASS (independent
  re-type of the §469(i) constants + the special-allowance helper + both forms'
  scenarios; loader & gate share no math). Guard verified REFUSING before the flip.
- Flipped READY_TO_SEED → seeded: **SCHEDULE_E** (8 facts/4 rules/33 lines/4
  diag/4 scenarios/5 cited links) + **FORM_8582** (17 facts/6 rules/17 lines/6
  diag/7 scenarios/8 cited links) + 6 flow assertions. **RS DB 50→52 forms,
  FA 140→146.** All rules cited.
- **SUPERSESSION:** deleted the old non-standard `form_number="8582"` draft
  (generic R001/D001 ids, wrong line numbering — invented a CRD line 2). The
  re-authored form is the standard `FORM_8582`. The real 2025 structure: 1a-1d
  rental-RE-active / 2a-2d all-other-passive / 3 combine / Part II 4-9 special
  allowance / 10-11 total allowed.
- Deployed exports verified HTTP 200 (`lookup/SCHEDULE_E/export/` +
  `lookup/FORM_8582/export/`); committed to tts-tax-app as canonical
  `server/specs/{schedule_e,form_8582}_spec.json` + 6 FA staged in
  `flow_assertions_1040_sche_8582_pending.json` (active 1040 gate stays 135).
- rule_id length lesson: FormRule.rule_id is varchar(20) — `R-8582-SPECIAL-ALLOWANCE`
  (24) overflowed; renamed → `R-8582-ALLOWANCE`.
- Next (tts-tax-app): the 6 build legs — seed (extend RentalProperty: address/
  active_participation/is_qjv/type-1-8/the two 1099-Qs, migration 0068; route the
  serializer/CRUD by form code) → compute → render → input → diagnostics →
  assertions → tag `1040-schedule-e-8582-complete`.

## 2026-06-13 — Form 8880 (Saver's Credit, roster #9) spec leg — SEEDED + EXPORTED ✅
- **Ken approved the scope walk in-session ("Looks good. Run it.")** — incl. the
  W-2 box-12 elective-deferral auto-derive (qualifying codes D/E/F/G/H/S/AA/BB/EE
  per owner; new tts-tax-app `W2Income.owner` field at the build leg). Authored +
  math-gated + flipped + seeded in one sitting: **RS DB 47 → 48 forms, FA 123 →
  128.** `load_1040_form_8880.py` — FORM_8880 (11 facts / 5 rules / 18 lines /
  6 diagnostics D_8880_001..006 / 7 scenarios / 5 flow assertions FA-1040-8880-01..05
  / 2 new sources). Nonrefundable §25B credit → Schedule 3 line 4 (already a
  direct-entry feeder).
- **Constants:** 2025 line-9 AGI tier table VERBATIM from f8880.pdf (pymupdf);
  2026 TOP cutoffs VERIFIED from the IRS 2026 COLA notice (MFJ $80,500 / HoH
  $60,375 / single-MFS $40,250) + the 2026 intermediate 50%/20% breakpoints
  carried from 2025 as an INTERIM (D_8880_003 re-pin ~Dec 2026 when the 2026 Form
  8880 publishes — the spine derived-2026 precedent). Per-person $2,000 cap + the
  50/20/10% statutory §25B.
- **`check_8880_integrity.py` ALL CHECKS PASS** — independent recompute of all 7
  scenarios (T1 MFJ 50%→2,000 / T2 single 20%→400 / T3 IRA+box12 cap→200 / T4
  distribution-reduces / T5 over-limit→0 / T6 2026-top-cutoff / G1 student-excluded)
  + the tier table cross-checked both years.
- **HUMAN-REVIEW flag:** `IRS_2026_COLA_8880.requires_human_review=True` (the 2026
  intermediate breakpoints are interim). **Canonical `form_8880_spec.json` committed
  to tts-tax-app** + 5 FA-1040-8880 staged. Deployed export verified (HTTP 200).
  Next (tts-tax-app): build legs — seed (W2Income.owner + the 8880 facts + the
  pseudo-form), compute (box-12 derive + tier + credit → Sch 3 L4), render, input,
  diagnostics, assertions.

## 2026-06-13 — NEXT-UP #1 (Simplified Method Worksheet) spec leg — SEEDED + EXPORTED ✅
- **Ken approved the review walk in-session ("Looks good").** Flipped READY_TO_SEED
  + seeded: **RS DB 46 → 47 forms, FlowAssertions 117 → 123** (SIMPLIFIED_METHOD
  created, all rules cited). One seed-fix: `requires_human_review` is an
  AuthoritySource field, NOT an AuthorityExcerpt field — removed from the 4
  excerpt dicts (kept on the SMW source). **Deployed export verified** (HTTP 200,
  `lookup/SIMPLIFIED_METHOD/export/` — 14 facts / 6 rules / 11 lines / 6 diags /
  7 tests). **Canonical `simplified_method_spec.json` committed to tts-tax-app** +
  6 FA-1040-SM staged in `flow_assertions_1040_simplified_method_pending.json`.
  Next (tts-tax-app): build legs seed → compute (supersede D_RET_001) → render →
  input → diagnostics → assertions.
- `load_1040_simplified_method.py` (single form SIMPLIFIED_METHOD, the
  `load_1040_schedule_d.py` precedent). 14 facts / 6 rules / 11 lines (sm_1..sm_11) / 6
  diagnostics (D_SM_001..006) / 7 scenarios / 8 rule_links / 6 flow assertions
  (FA-1040-SM-01..06) / 2 new authority sources (Pub 575 + i1040 SMW).
- Replaces a LIVE tts-tax-app RED: **D_RET_001** (1099-R box-2a-blank-with-basis,
  the OPM/CSA-1099-R pattern). Computes the taxable pension via cost recovery →
  Form 1040 line 5b.
- **Constants VERIFIED vs IRS Pub 575 (2025):** Table 1 single-life (≤55→360 /
  56-60→310 / 61-65→260 / 66-70→210 / 71+→160) + Table 2 joint-survivor by
  COMBINED age (≤110→410 / 111-120→360 / 121-130→310 / 131-140→260 / 141+→210);
  the Nov-19-1996 (in-scope) / 1998 (Table 2) / 1987 (uncapped) boundary dates,
  statutory non-indexed. Ken's 7 scope decisions in tts-tax-app
  `server/specs/_next1_simplified_method_source_brief.md`.
- **`check_simplified_method_integrity.py` ALL CHECKS PASS** — independent retype
  of the 11-line worksheet + both tables (cell-by-cell cross-check) + the scope
  gates; load-bearing pins SM-T1 (single age 66 → 210, taxable 21,600), SM-T2
  (joint combined 130 → 310), SM-T3 (the cost cap binds → balance 0 / D_SM_004),
  SM-T4 (partial 7-month, age 71 → 160).
- **HUMAN-REVIEW flag:** the 11-line worksheet text is RECONSTRUCTED from the
  i1040 Simplified Method Worksheet + Pub 575 (the i1040 instructions page blocked
  verbatim auto-fetch); `IRS_2025_1040_SMW.requires_human_review=True`. Re-check
  the line text/order against the 2025 i1040 at Ken's walk. The ARITHMETIC is
  independently re-derived (the math gate is the real guard).
- **AWAITING Ken's review walk** → flip READY_TO_SEED → seed → export canonical
  `simplified_method_spec.json` to tts-tax-app + stage assertions → build legs
  (seed: new RetirementDistribution fields; compute: supersede D_RET_001; render:
  worksheet statement page; input; diagnostics; assertions). NOT seeded; RS DB
  unchanged. NOTE: RS root STATUS/MEMORY/DECISIONS still stale (Phase-0 note).

## 2026-06-13 — Topic 9 (Schedule D + 8949) spec-authoring leg — AUTHORED, math gate GREEN, NOT seeded
- `load_1040_schedule_d.py` authored (commit `f2c98f0`, 2,123 lines, READY_TO_SEED=False —
  guard verified refusing, zero DB writes): **SCHEDULE_D** (16 facts / 9 rules / 47 lines /
  11 diagnostics / 12 scenarios — the real 2025 face incl. the QOF question, per-box 8949
  totals pairwise A/G->1b..F/L->10, lines 4/5/11/12 direct-entry, carryover facts -> 6/14,
  DIV 2a -> 13, the line-16 -> 1040 7a routing + $3,000/$1,500 §1211(b) limit, the
  17/20/22 worksheet routing), **1040_SCHD_WS** (5/8/85/1/8 — sdtw_1..47 + clc_1..13
  carryover-OUT + w28_1..7 + u1250_1..18, all transcribed verbatim from i1040sd 2025),
  **8949 RE-AUTHOR** (29/5/26/5/6 — the 12-box A-L system incl. 1099-DA digital assets,
  the 18-code column-(f) table as adj_code_* data-list facts, Exception-2 summary rows,
  CapitalTransaction surface; `_retire_stale_8949` drops the thin 1120-S-era draft by
  keep-set; entity_types stays multi-entity). 12 flow assertions FA-1040-SCHD-01..12.
- Primary sources fetched + dumped same day (tts-tax-app server/.scratch/): f1040sd /
  i1040sd (16pp, all four worksheets) / i8949 (13pp, the code table) / f8949 (local copy
  confirmed = the 2025 12-box revision). 4 new AuthoritySources + RP_2025_32 §4.01 excerpt.
- **`check_topic9_integrity.py` ALL CHECKS PASS**: independent retype of the netting/CLC/
  28%/1250/SDTW math + the Tax Table/TCW convention; every scenario pin recomputed
  (SDTW-T1 pins 25% partial-bind 675 / SDTW-T2 28%-cap-no-bind L43=0 / SDTW-T3 28% binds
  28,000 / SDTW-T4 the 1==16 skip + table 3,605); **the SDTW==QDCGT invariant swept over
  13 cases x both years x 5 statuses**; constants cross-checked cell-by-cell incl.
  line-19 == the 24%-bracket tops BOTH years (2026 derived from RP 2025-32 §4.01 —
  walk item 1; HOH $201,750 vs single/MFS $201,775).
- **Sibling supersession edits authored (NOT run — they apply at the post-walk re-run):**
  `load_1040_intdiv_qdcgt.py` — D_INTDIV_001/002 retired (+ `_retire_topic9_superseded`
  deletion helper; ID-T3/G1/G2 + FA-1040-INTDIV-05 re-pointed to the Schedule-D path;
  R-QDCGT-GATE + WS3 gain the Sch-D branch). `load_1040_schedule_c.py` — 8995 L12 gains
  the Schedule D net-capital-gain component (i8995 verbatim); D_8995_002 retired from the
  keep-set (deleted on re-run).
- 10 requires_human_review walk items in the loader docstring. Next: Ken's review walk ->
  flip -> seed -> export canonical specs + staged assertions -> tts-tax-app build legs.

## 2026-06-13 — Topic 9 SEEDED on Ken's approval ("Looks good. Go.")
- `READY_TO_SEED` flipped -> `load_1040_schedule_d` run: SCHEDULE_D (16f/9r/47L/11d/12s)
  + 1040_SCHD_WS (5f/8r/85L/1d/8s) created; **8949 re-authored** (`_retire_stale_8949`
  deleted 38 stale 1120-S-era rows -> 29f/5r/26L/5d/6s, all cited); 12 FA-1040-SCHD.
  **RS DB 44->46 forms, FlowAssertions 105->117.**
- Sibling loaders re-run to apply the supersession edits: `load_1040_intdiv_qdcgt`
  retired **D_INTDIV_001/002** (`_retire_topic9_superseded`; deployed export confirms —
  diags now 003-010); `load_1040_schedule_c` retired **D_8995_002** (deployed export
  confirms — diags 001/003/004/005). Both deployed and round-trip-verified.
- tts-tax-app committed canonical `{schedule_d,1040_schd_ws,8949}_spec.json` + 12 staged
  assertions (`272aeee`). Amended intdiv/8995 canonical re-export DEFERRED to the
  Topic 9 compute leg (the spec-driven scenario tests read those files — re-export in
  lock-step with route_line_16 / compute_8995_db). Next: tts-tax-app build legs.

## 2026-06-12 c — 8995 L11 sourcing amended on Ken's approval (subtract Sch 1-A 13b)

- At the tts-tax-app compute leg the engine flagged that the 8995 spec sources L11
  (taxable income before QBI) as "1040 L11 − L12" verbatim — it did NOT subtract the
  OBBBA Schedule 1-A line-13b deduction, although taxable income now includes 13b.
  **Ken ruled in-session: subtract 13b** (L11 = 1040 L11 − L12 − L13b — every non-QBI
  deduction comes out before the QBI income limitation). Affects the L14 limitation
  cap and the 8995-vs-8995-A threshold boundary on senior/tips/overtime QBI returns.
- `load_1040_schedule_c.py` updated in 3 places (the `qbi_taxable_income_before_qbi`
  fact note, the R-8995-L13-L14 formula + description, the line-11 line_map
  description) and RE-RUN idempotently — **DB counts unchanged** (44 forms, FA 105;
  update-in-place). Deployed export verified (fact/rule/line carry the 13b text;
  counts 13/8/21/5/7). Canonical `8995_spec.json` re-exported + committed in
  tts-tax-app; engine (`compute_8995_db`) + diagnostic (D_8995_001) + tests updated
  the same sitting.

## 2026-06-12 b — Topic 8 (Sch C + SE + 8995 re-author + 8959) REVIEWED + SEEDED on Ken's approval
- Review walk in-session: Ken **APPROVED as authored**. The 4 `requires_human_review`
  walk items accepted as recommended: (1) 2026 MFS 8995 threshold $201,775 as
  published (RP 2025-32 §4.26 rounding artifact, $25 above 'other' — diagnostic
  boundary only); (2) multi-business QBI reduction (½-SE/SEHI/retirement) allocated
  **pro-rata by net SE earnings**; (3) 8995 L12 net capital gain = 1040 L3a +
  cap-gain distributions in v1, net-LT-gain added when Schedule D lands +
  D_8995_002 warning; (4) QBI loss carryforward **supported** in v1. RED-defer
  enumeration confirmed.
- `READY_TO_SEED` flipped → `load_1040_schedule_c` run clean (no en-route fixes).
  **Created SCHEDULE_C** (24 facts/9 rules/56 lines/7 diags/7 scenarios) + **SCHEDULE_SE**
  (17/12/24/4/5) + **8959** (13/6/24/4/5); **8995 RE-AUTHORED** (13/8/21/5/7) — the
  `_retire_stale_8995` step deleted **28 stale stub rows** (10 facts / 11 rules / 1
  line / 3 diags / 3 tests + cascading RuleAuthorityLinks). **14 flow assertions.**
  6 new authority sources + RP 2025-32 §4.26 excerpt, 100% cited. **RS DB: 41 → 44
  forms; FlowAssertions 91 → 105.** Math gate re-run green pre-seed.
- Deployed exports verified (`lookup/SCHEDULE_C|SCHEDULE_SE|8995|8959/export/` HTTP
  200 — counts round-trip 24/9/56/7/7 · 17/12/24/4/5 · 13/8/21/5/7 · 13/6/24/4/5; 8995
  re-author pins survive: R-8995-L15 present, stub R001 / `qualified_business_income`
  GONE, real 17-line face incl. 1i-1v / 17). Committed to tts-tax-app as canonical
  `server/specs/{schedule_c,schedule_se,8995,8959}_spec.json` + the 14 assertions
  STAGED in `flow_assertions_1040_topic8_pending.json` (active 1040 gate untouched at
  86; flow gate 108 passed — no tts-tax-app code touched).
- NEXT: tts-tax-app build legs (seed → compute → render → input → diagnostics →
  assertions per form), starting with build leg 1 — the **multi-business Schedule C FK
  model** (proprietor=taxpayer|spouse) + Schedule SE/8995/8959 models + the
  `seed_schedule_c`/`seed_schedule_se`/`seed_8995`/`seed_8959` commands + the
  f1040sc/f1040sse/f8995(have)/f8959 manifest entries.

## 2026-06-12 — Topic 8 (Schedule C + SE + 8995 re-author + 8959) specs AUTHORED + math gate GREEN (READY_TO_SEED=False)
- `specs/management/commands/load_1040_schedule_c.py` authored (Sprint Topic 8 /
  NEXT-UP #1), commit `aac4a38`. ONE idempotent command (the `load_1040_eic.py`
  4-form precedent) creating FOUR TaxForms from the Topic 8 source brief
  (tts-tax-app `server/specs/_topic8_schedulec_source_brief.md`), 100% cited:
  - **SCHEDULE_C** (24 facts / 9 rules / 56 lines / 7 diags / 7 scenarios / 10
    links): Parts I-V incl. Part III COGS (Decision 1); line-30 simplified home
    office (Decision 2 — min(sqft,300)x$5, gross-income limited to line 29, no
    carryover); per-business (Decision 3); line 13 -> 4562 engine; line 31 ->
    Sch 1 L3 + Sch SE L2. RED-defers: statutory employee, line 32b (6198), 8829.
  - **SCHEDULE_SE** (17/12/24/4/5/13): Part I standard method, per proprietor;
    year-keyed SS wage base (176,100 / 184,500); L12 -> Sch 2 L4, L13 -> Sch 1
    L15 (existing EIC Worksheet-B + 8812 feeder); L6 -> 8959 L8. Part II
    optional + church = RED-defer.
  - **8995** RE-AUTHORED (13/8/21/5/7/10): retires the wrong stub (R001-R005 /
    D001-D003 / lines 1-8 / 3 tests via `_retire_stale_8995`) and writes the
    real 17-line face — per-business QBI reduced by 1/2-SE/SEHI/SE-retirement,
    REIT/PTP component, income limitation -> 1040 L13a; year-keyed threshold
    (above -> 8995-A RED-defer).
  - **8959** (13/6/24/4/5/7, Decision 4): Part I wages + Part II SE (threshold
    REDUCED BY Medicare wages) -> Sch 2 L11; Part V withholding -> 1040 L25c;
    non-indexed thresholds; Part III RRTA RED-defer.
  - **14 flow assertions** (FA-1040-SCHC-01..04, SCHSE-01..03, 8995-01..03,
    8959-01..03, TOPIC8-01 the Sch C -> Sch SE L6 -> 8959 L8 chain).
  - 6 NEW authority sources (Sch C face + i1040sc, Sch SE face, 8995 face +
    re-authored i8995, 8959 face, Topic 751/SSA) + RP 2025-32 §4.26 excerpt on
    the EXISTING RP_2025_32. 4 `requires_human_review` WALK ITEMS flagged in the
    module docstring + rule descriptions: (1) 2026 MFS 8995 threshold $201,775 is
    $25 above 'other' $201,750; (2) multi-business QBI allocation of
    1/2-SE/SEHI/retirement (pro-rata default); (3) net-cap-gain / Schedule-D
    deferral for 8995 L12; (4) QBI loss carryforward in/out.
  - Year-keyed: SE_WAGE_BASE (176,100/184,500), QBI_THRESHOLDS (per status, both
    years). Statutory/non-indexed (NOT year-keyed): SE 92.35/12.4/2.9/50 + $400;
    8959 thresholds + 0.9%/1.45%; 20% QBI rate; home-office $5/300.
- `check_topic8_integrity.py` authored + GREEN (commit `338a373`, the math gate
  before Ken's walk). Carries its OWN re-typed constants + independent
  recomputations of Schedule SE Part I (incl. the W-2-SS-wage cap), the Schedule
  C gross-income/COGS/simplified-home-office chain, the 8995 QBI
  reduction+income-limitation, and the 8959 reduced-threshold math; every
  scenario (SC-T1..T7 / SE-T1..T5 / 8995-T1..T7 / 8959-T1..T5) recomputed and
  matched; loader module constants cross-checked cell-by-cell; load-bearing pins
  (SS cap binds; year-keying load-bearing; 8959 line 11 = threshold - Medicare
  wages; QBI income limit binds; home-office gross-income limit). Found + fixed
  one loader slip (SE-T5 L13 2119.43 -> 2119.44 ROUND_HALF_UP) + one structural
  input typo (8959 ENGAGE). **ALL CHECKS PASS.**
- **Loader REFUSES (READY_TO_SEED=False, "all populated", CommandError, zero DB
  writes). RS DB UNCHANGED (still 41 forms; SCHEDULE_C/SCHEDULE_SE/8959 absent;
  8995 stub NOT yet replaced — the re-author waits for the flip).**
- NEXT: Ken's review walk (in-session) → on approval flip `READY_TO_SEED=True` →
  seed (re-authors 8995) → verify deployed exports → commit canonical
  `server/specs/{schedule_c,schedule_se,8995,8959}_spec.json` to tts-tax-app +
  stage flow assertions → build legs (seed → compute → render → input →
  diagnostics → assertions per form).

## 2026-06-11 g — Topic 7 (EIC + 8867/8862) specs AUTHORED + math gate GREEN (READY_TO_SEED=False)
- `specs/management/commands/load_1040_eic.py` authored (Sprint Topic 7), commit
  `48e1fef`. Creates FOUR TaxForms from the Topic 7 source brief (tts-tax-app
  `server/specs/_topic7_eic_source_brief.md`), the `load_1040_retirement.py`
  precedent, 100% cited:
  - **1040_EIC** (computational pseudo-form): 33 facts / 10 rules / 18 lines /
    16 diagnostics / 16 scenarios / 16 rule_links. Step-5 earned income,
    Worksheet A (non-SE) + mainstream Worksheet B (SE: Sch1 L3 net SE − Sch1 L15
    ½-SE-tax), the EIC Table $50-bracket midpoint×rate ROUND_HALF_UP lookup, the
    lower-of-AGI/earned-income rule, the Pub 596 Worksheet-1 investment-income
    limit, the Rules-for-Everyone + childless eligibility gates → 1040 line 27a.
    **YEAR-KEYED `EIC_PARAMS`** (both years, each verified independently — unlike
    Topic 5's statutory non-indexed constants).
  - **SCHEDULE_EIC** (7/1/7/1/2/1): model-driven per-child face from Dependent rows.
  - **8867** (16/1/12/2/3/1) + **8862** (6/1/6/1/2/1): data-map faces, no compute.
  - **9 flow assertions** FA-1040-EIC-01..09 (27a feeder; the year-keyed §32
    constants_check; the midpoint-table convention; lower-of rule; investment-income
    gate; childless age band; combat-pay election; QSS=other column; the
    eligibility-gate truth table).
  - NEW sources: Pub 596, Schedule EIC, Form 8867, Form 8862. NEW excerpts on the
    EXISTING `RP_2024_40`/`RP_2025_32` (§2.06 EIC, distinct from intdiv's §2.03/§4.03
    QDCGT excerpts) + `IRS_2025_1040_INSTR` (Worksheets A/B + EIC Table).
- `check_eic_integrity.py` authored + GREEN (commit `5051f81`, the math gate before
  Ken's walk). Carries its OWN re-typed §32 tables + EIC Table evaluator (not
  imported from the loader): loader `EIC_PARAMS` cross-checked cell-by-cell both
  years; §32 internal reconciliation within $1 (covers the published TY2026 0-QC
  $664 vs 663.42); the i1040gi midpoint pin 2,475→842 (841.5 ROUND_HALF_UP, not
  truncate); lower-of binds T3→1,663; exact phaseout T2→389; year-keying
  load-bearing (TY2026 3+ 8,231 ≠ TY2025 8,046); MFJ-vs-other column; combat-pay
  election; Worksheet-B SE; the 5 RED-gate fixtures; FA-02/06/08 constants. ALL PASS.
- **Loader REFUSES (READY_TO_SEED=False, "all populated", exit 1, zero DB writes).
  RS DB UNCHANGED (still 37 forms; 1040_EIC/SCHEDULE_EIC/8867/8862 absent).**
- **Ken's review walk — APPROVED in-session.** The one open item (Worksheet-B
  SE-component sourcing) confirmed = `eic_se_net_earnings` ← Sch 1 L3 (net SE) /
  `eic_se_half_deduction` ← Sch 1 L15 (½-SE-tax) per the DoD "Schedule 1
  flowed-or-direct, Schedule C compute NOT required".
- **Flipped `READY_TO_SEED=True` + seeded** (commit `00a550c`): `load_1040_eic`
  created 1040_EIC (33/10/18/16/16) + SCHEDULE_EIC (7/1/7/1/2) + 8867 (16/1/12/2/3)
  + 8862 (6/1/6/1/2), 4 new authority sources + §2.06 EIC excerpts on
  RP_2024_40/RP_2025_32 + Worksheet/EIC-Table excerpts on the 1040 instructions,
  **9 flow assertions**. All 4 forms 100% cited. **RS DB: 37 → 41 forms;
  FlowAssertions 82 → 91.** Math gate re-run green pre-seed.
- Deployed exports verified (`lookup/1040_EIC|SCHEDULE_EIC|8867|8862/export/` HTTP
  200 — counts round-trip + pins EIC-T4 842 / EIC-T9 8231). Committed to tts-tax-app
  as canonical `server/specs/{eic,schedule_eic,8867,8862}_spec.json` + the 9
  assertions STAGED in `flow_assertions_1040_eic_pending.json` (active 1040 gate
  untouched at 77; flow gate 99 passed).
- NEXT: tts-tax-app build legs (seed → compute → render → input → diagnostics →
  assertions), starting with build leg 1 — Dependent + Taxpayer additive migrations
  (EIC reuses Dependent, no new doc model) + seed_1040_eic/schedule_eic/8867/8862 +
  the f1040sei/f8867/f8862 manifest entries.

## 2026-06-11 f — Topic 5 (Retirement) REVIEWED + SEEDED on Ken's approval
- Review walk in-session: Ken **approved** (source citations + SS Benefits
  Worksheet transcription + scope already confirmed). Two walk outcomes:
  (a) **TY2026 §86/5329 constants confirmed NON-INDEXED** — SS base/second-tier
  ($25k/$32k, $9k/$12k) and the 50%/85% rates are statutory §86 (no inflation
  adjustment cross-reference), and the §72(t) 10%/25% rates are statutory; RP
  2025-32 adjusts none — same pattern as Schedule 1-A. So NO `_constants_for_year`
  in this topic. (b) **R-RET-CODE J-wording tightened** — the formula listed
  "J (10%, RED if box2a blank)" among early codes; J/T are OUT of v1 and always
  RED, so the EARLY clause now lists only `1 (10%), S (25%)` and J/T moved to the
  RED-UNSUPPORTED clause; D_RET_003 condition reworded to "{v1 set} (J and T OUT
  of v1 -> always RED)". No math impact (no J/T scenario). Integrity check re-run
  green after the edit.
- `READY_TO_SEED` flipped → `load_1040_retirement` run clean: **Created
  1040_RETIREMENT** (25 facts/8 rules/24 lines/7 diags/18 scenarios) + **5329**
  (3/3/4/1/3), 16 authority links (100% cited), 2 new excerpts on
  IRS_2025_1040_INSTR, **7 flow assertions**. **RS DB: 35 → 37 forms,
  FlowAssertions 75 → 82.**
- Deployed exports verified (`lookup/1040_RETIREMENT|5329/export/` HTTP 200 —
  counts 25/8/24/7/18 + 3/3/4/1/3 survive; SS-3 6b=17,000 / SS-4 15,350 /
  SS-5 8,500 / RET-T4 4b=0 / RET-5329-3 line4=2,500 / F5329-T2 1,200 all
  round-trip). Committed to tts-tax-app as canonical `server/specs/
  retirement_spec.json` + `5329_spec.json`; the 7 assertions STAGED in
  `flow_assertions_1040_retirement_pending.json` (active 1040 gate untouched at
  70; flow gate still 92 passed).
- NEXT: tts-tax-app build legs (seed → compute → render → input → diagnostics →
  assertions), starting with the new **RetirementDistribution** model + the
  SSA-1099 return-level fields + f5329 manifest/field-map.

## 2026-06-11 e — Topic 5 integrity check written + green (math gate before Ken's walk)
- `check_retirement_integrity.py` authored (RS root; mirrors
  `check_intdiv_integrity.py`/`check_sch123_integrity.py`). Validates the authored
  lists WITHOUT touching the DB, then INDEPENDENTLY recomputes every numeric
  scenario from its OWN transcription:
  - **SS Benefits Worksheet (18 lines)** — full re-implementation of i1040gi p.31
    incl. both STOP conditions (line 7, line 9) and the MFS-lived-with-spouse
    short-circuit; verifies SS-1..5 line-by-line (every authored `ws_*` +
    6a/6b), plus the FA-RET-05 invariant (6b ≤ 85%×WS1 and ≤ WS1) on each.
  - **1099-R aggregation** — RET-T1..5 (4a/4b IRA, 5a/5b pension, 25b withholding;
    rollover/QCD per-doc floor; rollover/QCD literal-flag consistency).
  - **Form 5329 Part I** — RET-5329-1..3 (doc-driven early amount + 10%/25%) and
    F5329-T1..3 (direct facts); the direct-to-Sch-2 generation gate (R-5329-03).
  - **RED-gate fixtures** — RET-G1..5 each verified to actually satisfy its
    diagnostic condition (D_RET_001/002/003/004/006).
  - **Load-bearing pins** — 85% cap binding in SS-3; MFS branch ≠ normal path;
    SIMPLE 25% ≠ 10%; FA-1040-RET-06 constants_check matches the independent §86
    values (25k/32k, 9k/12k, 0.50/0.85, years [2025,2026]); J excluded from v1.
  - Structural checks (dup keys/ids/lines, uncited rules, dangling links,
    inputs-are-facts) all clean.
- **ALL CHECKS PASS.** Loader guard still REFUSES (READY_TO_SEED=False, exit 1,
  zero DB writes); **RS DB UNCHANGED (35 forms; 1040_RETIREMENT/5329 absent).**
- ONE packet item surfaced for the walk: R-RET-CODE's formula lists
  "J (10%, RED if box2a blank)" as an early code, but the Ken-confirmed v1 set
  and D_RET_003 exclude J entirely (always RED). Wording to reconcile — no math
  impact (no J scenario).
- NEXT: Ken's review walk → on approval flip READY_TO_SEED → seed → verify →
  export canonical specs + stage flow assertions → tts-tax-app build legs.

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
