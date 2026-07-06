---
type: project-status
project: sherpa-tax-rule-studio
last_updated: 2026-07-05
---

# STATUS — sherpa-tax-rule-studio

*The freshest file. Answers "where am I on this project?" Updated at the end of every substantive session.*

---

## Current state

Active spec-authoring tool. RS Supabase holds **111 TaxForms / 500 FlowAssertions / 930 FormRules**
(**+WO-14 Form 8990 2026-07-05** — §163(j) business-interest limitation (`8990`, entity_types 1120/1065/1120S/1040);
finishes the 1120 module's biggest deferred leg; Part I ATI on the OBBBA **EBITDA basis** (L11 dep/amort/depletion
add-back, reinstated for TY2025) → 30% limit → allowable + indefinite carryforward; Part II/III partnership EBIE/ETI
+ S-corp ETI; $31M §448(c) exemption gate + §163(j)(7) excepted diagnostic; `lookup/8990/export/` = 200; first of the
SPINE S-16 federal-forms queue; **+WO-13 NC + AL pass-through batch 2026-07-05** — completes the adjacent-state pass-through track (GA-700 +
SC1065/SC1120S + NC + AL): `NC_D403`/`NC_CD401S` (NC Taxed PTE 4.25% + owner DEDUCTION, CD-401S NC franchise,
85% bonus/§179 $25k/$200k, NR withholding 4.25%), `AL_FORM_65`/`AL_FORM_20S` (AL Electing PTE 5% + owner
refundable CREDIT, composite 5%, AL conforms §168(k)/§179, Form 20S Line-32 LIFO/BIG/excess-passive); all 4
seeded/exported (200); **+WO-12 state C-corp batch 2026-07-05** — GA's income-tax neighbors' C-corp returns, extending the 1120
module: `SC1120` (5% + §168(k) decouple/§179 $1.25M/$3.13M + license fee; ⚠ H.3368/OBBBA live-wire flag),
`AL_FORM_20C` (6.5% + constitutional FIT deduction Amendment 662 + AL conforms to §168(k)/§179 + GILTI/§174
decouples), `NC_CD405` (2.25% income S.B. 105 + net-worth franchise tax + 85% bonus add-back/§179 $25k/$200k);
all 3 seeded/exported (`lookup/{SC1120,AL_FORM_20C,NC_CD405}/export/` = 200); **+WO-11 Form 1120 C-corp module 2026-07-05** — the first C-corporation entity type: `1120` compute spine
(page-1 income/deductions → Schedule C DRD 50/65/100% + §246(b) limit/loss exception → §172 NOL 80% → §11 flat
21% tax → Schedule J total tax; §163(j)/CAMT/PHC/AET/§59A/§1062 screen+route), `1120_SCHL` (Schedule L balance +
M-1/M-2 ties + Sch K $250k/$10M-M-3 gates), `GA600` (GA 5.19% income tax + §168(k)/§179 depreciation delta @
verified 2025 $1.25M/$3.13M + single-factor apportionment + net worth tax bracket table); all 3 seeded/exported
(`lookup/{1120,1120_SCHL,GA600}/export/` = 200); 1125-A/1125-E/3800/4562/4797/8949/7004 confirmed already
covering 1120; **+WO-10 Form 5227 2026-07-05** — split-interest trust info return (`5227`): §664(b) four-tier character
engine (tier-level) + accumulation + §664(c)(2) 100% UBTI excise; CRAT/CRUT compute, PIF/CLT/§4947 structure;
`lookup/5227/export/` = 200; **+S-11 1041 MODULE COMPLETE 2026-07-05** — 3 new forms: `1041` spine (page-1 +
Schedule B DNI/IDD engine + Schedule G tax), `SCHEDULE_K1_1041` (beneficiary K-1, full verbatim box codes),
`GA501` (GA fiduciary, resident-only); all 3 seeded/exported (`lookup/{1041,SCHEDULE_K1_1041,GA501}/export/` = 200);
**+S-5 boundary diagnostics 2026-07-05** — new consolidated `ENTITY_BOUNDARY` form; **+S-6 PAL/basis
deepening 2026-07-05** — new Form `461` (§461(l) EBL) + FORM_8582/SCHEDULE_E amendments;
was 94 TaxForms / 449 FA after the SC entity track; was
92 after the delta audit; **+SC1065 + SC1120S seeded 2026-07-05** — the SC pass-through ENTITY track,
adjacent-state extension of GA-700 + PTET; +8 FA, +17 FormRules). **Prod ↔ a fresh `seed_all` rebuild
was 0-delta at the 2026-07-05 delta audit; `load_sc_passthrough` is auto-discovered by `seed_all`
(phase 2, after `load_sc1040`, verified via `--dry-run`), so the two new SC entity forms stay
reconstructable — no orchestrator edit needed.** **Spec approval workflow live (2026-07-04):** 7 approved (the 1065-core
batch) / 85 draft, recorded in `specs/approved_specs.py` + applied by `approve_specs` (reconstructable
via `seed_all` phase 5). **August state track:** SC1040 + Schedule NR ✅, AL Form 40 ✅, and NC D-400 ✅
authored/seeded/exported (forms 1-3 of the state set; next: GA-700 + PTET). **The 1065-core
campaign is COMPLETE (2026-07-04)** — all 6 core forms covered (4 fresh + 8825/4562/3800 confirmed
multi-entity, verified against the live DB incl. actual Sch K routing). Newest: the **1065-core Schedule L +
Schedule B** (`1065_L` / `1065_B`, 2026-07-04) — seeded + exported (both 200); Sch L balance-sheet
(14 == 22 balance check + L21↔M-2 tax-basis tie), Sch B 33 questions with Q4 small-partnership gate +
Q24 §163(j) $31M → Form 8990. Prior same day: the **1065-core Schedule M-1 + M-2** (`1065_M1` /
`1065_M2`) — M-1 line 9 = Analysis line 1, M-2 tax-basis capital. Prior same day (all 200): **Schedule K-1 + allocation** (`SCHEDULE_K1_1065`, full
~200-code K-1 coded-box lists verbatim; CLOSED the box-9c pass-through) and the **Schedule K spine**. Prior same day: the **Schedule K spine** (`1065_PAGE1` + `SCH_K_1065`, both endpoints 200;
the reconcile that authored it CAUGHT + FIXED a tts net-farm compute bug `f61cfec`), and the **S3/S4
MeF ATS unblock campaign** — `4835` (S3), plus `8835` + `8936` + `8936_SCHA` (S4), all authored/seeded/
exported, **all four `lookup/<form>/export/` endpoints return 200** (verified live). Every rule cited;
OBBBA gates verified verbatim off the FINAL 2025 IRS sources. Prior newest on the 1065 track:
`1065_SE` **leg 2** (the 14a SE-base sub-spec, worksheet WS1a–WS5) seeded + exported 2026-07-02. Leg 1
(classification) was built into tts at `a8c7da4`; the leg-2 export is ingested in tts at `e5f2795` with
B1–B7 pinned as pending-skips.

## In progress

- [x] **1065 CORE — SPINE LEG SEEDED + EXPORTED ✅ (Ken: "flip seed export").** Fresh-authored
  2026-07-04 the first campaign unit: `specs/management/commands/load_1065_schedule_k.py` seeds TWO
  forms — **`1065_PAGE1`** (page-1 income/deductions → line 23 ordinary business income → Sch K line 1;
  27 facts / 7 rules / 32 lines / 3 diag / 4 scenarios) and **`SCH_K_1065`** (Schedule K distributive-
  share spine 1-21 + Analysis of Net Income; 40 facts / 11 rules / 38 lines / 4 diag / 7 scenarios / 4
  flow assertions). Grounded in primary IRC quoted verbatim (§702(a)/(b), §703(a)/(b), §704(a)/(b),
  §707(c)) + the brief §4.1/§4.2 FINAL-2025 f1065/i1065 line maps (filing authority). **3 scope decisions
  LOCKED by Ken**: A. K-2/K-3 RED-defer (`D_SCHK_K3`); B. M-3 RED-defer (L/M leg); C. §704(b)/(c)
  structure-only, allocation MATH deferred to `k1_allocator` (`D_SCHK_704C`). **SEEDED** (all rules cited)
  → RS now **84 TaxForms / 404 FlowAssertions**; **EXPORTED** `lookup/{1065_PAGE1,SCH_K_1065}/export/` both
  **HTTP 200** (exports/form_1065_page1/, exports/form_sch_k_1065/). **D-1 reconcile survey DONE**
  → `1065_core_reconcile_log.md` (8 items): 4 MATCH (page-1 L8, K3c, K14a bottom-up, §179→K12), 1 build-GAP
  (1065 Analysis of Net Income — tts has none; K18 is 1120-S-only), 1 ✅ **CONFIRMED+FIXED** (net-farm
  misroute — see below), 2 ⚠ still-open Ken calls (page-1 off-by-one field numbering; box-9c pass-through).
- [ ] **✅ tts net-farm bug FIXED this session (`f61cfec`).** The reconcile CAUGHT a confirmed 1065 compute
  bug: `FORMULAS_1065` routed Schedule F net (`F34`) to Schedule K line 11 instead of page-1 line 5 → K1, so
  farm was excluded from ordinary income AND the 14a SE base (SE understatement), with a latent double-count
  if line 5 was also hand-entered. Traced (Explore agent + verified); Ken said "fix now": relocated the
  Schedule F block ahead of page-1 line 8, `("5", F34)` → line 8 → K1, removed `K11←F34`, `seed_1065` line 5
  `is_computed=True`. Regression `TestNetFarmRouting` 3/3 green (shared test DB). Committed index-only (parallel
  S3/S4 8936 WIP left untouched). RS spine was already correct here (net farm → line 5 → K1); no RS change.
- [ ] The **parallel tts session is building S3/S4** off the four RS specs (`4835`, `8835`, `8936`,
  `8936_SCHA` — all `lookup/<form>/export/` = 200). Latest: tts `035223e` "S3 build-ready — 4 mappers."
  RS side done for that campaign (`check_s3s4_integrity.py` 390/390 green).

## Next up

**► SEQUENCE NOW LIVES IN BUILD_ORDER.md (canonical in `tts-tax-status`).** As of 2026-07-05 the
**WORK_ORDERS front door** is live: WORK_ORDERS.md is the RS MECHANISM (gap-check + transitions + Gate-1)
and takes its next authoring order FROM the BUILD_ORDER SPINE — no independent backlog here. At boot, pull
tts-tax-status and reconcile SPINE node status against THIS file + on-disk loaders (never the draft
checkboxes). **As of 2026-07-05 ALL prior RS authoring rocks are DONE** (S-1 1040-ATS · S-4 1065-core ·
S-5 boundary · S-6 PAL/basis · S-7–S-10 states · S-11 1041 · WO-10 5227). **The next RS authoring order is
`[WO-11] S-13 · 1120 C-corp module`** — ADDED 2026-07-05 (DECISIONS D-12), status INTAKE. Ken will prompt
"build 1120"; run the WORK_ORDERS front door from step 1 (gap-check → research-verify → source brief →
Gate-1 scope walk → author). Required set: 1120 spine (§11 21%), Sch C (DRD), Sch J, Sch K/L, M-1/M-2,
1125-A/1125-E, GA Form 600.

**► IMMEDIATE NEXT — open (Ken's pick).** The August RS state INDIVIDUAL track is DONE (**SC1040 ✅ · AL
Form 40 ✅ · NC D-400 ✅ · GA-700 + PTET ✅**), the **1120-S delta audit is COMPLETE ✅**, and the
**adjacent-state ENTITY track has begun** — **SC1065 + SC1120S + SC PTET ✅ (2026-07-05, DECISIONS D-9)**.
Candidate next threads on the adjacent-state entity track (the individual returns for GA's income-tax
neighbors AL/NC/SC are all done; FL/TN have no individual income tax):
  - **SC follow-ups (small):** the SC1120S multi-state Schedule G/E/H apportionment + license-fee
    apportionment + Schedule D Annual Report were RED-deferred in v1 (D-9 Q4) — build if demand warrants.
  - **NC pass-through** (D-403 partnership / CD-401S S-corp + the NC Taxed PTE election) — reuses NC D-400
    conformity (Jan 1 2023 freeze, 85% add-back).
  - **AL pass-through** (Form 65 / 20S + Alabama's Electing PTE tax, Act 2021-1) — reuses AL Form 40 research.
  - **FL F-1120** (corporate income — a NEW C-corp entity type, no 1120 authored yet) or **TN FAE 170**
    (franchise & excise) — the two neighbors with no individual income tax / no PTET.
Other open threads: the **September 1041 authoring wave** (spine → DNI/IDD/Sch B → Sch G/K-1/GA 501;
DECISIONS D-2 RED-defers Sch I AMT); or the tts-side FA gate reconcile deferred from the parity cleanup
(a tts session owns it).
  **State-spec pattern** (for any further state form — `load_sc1040.py` / `load_al_form40.py` /
  `load_nc_d400.py` / `load_ga700.py` + their `*_source_brief.md`):
  1. Research subagent → verify TY2025 VERBATIM against the state DOR final PDFs (never memory).
  2. Source brief → ~4-decision scope walk with Ken (AskUserQuestion).
  3. Author `load_<form>.py` with `READY_TO_SEED=False`; validate on throwaway SQLite (reusable harness
     `scratchpad/validate_nc.py` / `validate_ga.py` — ALSO enforces the CharField caps SQLite ignores:
     `topic_name` ≤ 255; **`rule_id`/`diagnostic_id`/`assertion_id`/`line_number` ≤ 20**).
  4. Ken's review walk → flip guard → seed to prod → verify export = 200 → commit.
  **Use explicit-path git commits, never `git add -A`** — a parallel session shares this working tree
  (memory `rs-shared-worktree-explicit-commits`). Prod is at **94 TaxForms / 449 FAs / 7 approved**.
  For pass-through ENTITY state forms, `load_ga700.py` (partnership + PTET) and `load_sc_passthrough.py`
  (two forms in one loader: SC1065 + SC1120S) are the precedents; verify each state's PTET is NOT a GA
  clone (SC's is a 3% ATB election, annual/non-binding, owner EXCLUSION via I-335 — not GA's 5.19%
  irrevocable PTEDED). Reuse the SC/NC/AL conformity authority sources already seeded by the individual
  loaders via `EXISTING_SOURCES_TO_REFERENCE`.

**► 1065 CORE CAMPAIGN — COMPLETE ✅ (2026-07-04).** `1065_core_source_brief.md` has the gap map (6 forms fresh —
Schedule K spine, K-1 + allocation, M-1/M-2, L, B; 8825/4562/3800 already cover 1065). **Spine leg
(form 1 of 6) DONE 2026-07-04** — `1065_PAGE1` + `SCH_K_1065` seeded + exported (both endpoints 200).
**✅ form 2 of 6 DONE — Schedule K-1 (Form 1065) + allocation engine (`SCHEDULE_K1_1065`).** Seeded +
exported (200), all rules cited. Reconciled against `k1_allocator.py`: encodes the engine's profit/
loss-% allocation + `PartnerAllocation` category overrides; GP + distributions direct; box 9c LT-capital
(CONFIRMED — box-9c pass-through CLOSED); box 14a = `1065_SE` cross-ref. RED-deferred per Decision C:
§704(c) built-in gain (items M/N), §704(b) SEE, §706(d) varying interest, item-L capital roll-forward.
FULL ~200-code coded-box lists (boxes 11/13/14/15/17/18/19/20) transcribed verbatim from the FINAL
i1065sk1.pdf (pp. 33-36, pymupdf) as `IRS_2025_I1065SK1` excerpts. Committed `8673fdd` + the seed.
**✅ form 3 of 6 DONE — Schedule M-1 + M-2 (`1065_M1` / `1065_M2`).** Seeded + exported (both 200), all
rules cited. M-1 line 9 = Analysis line 1 (face verbatim); M-2 tax-basis capital roll-forward. Authored
from the FINAL f1065 page 6 (pymupdf verbatim). Reconcile finding: **tts M2_3 mis-source** (labeled "per
books" data-entry; should tie to Analysis line 1 on a tax-basis M-2) → **spawned tts task `task_4bf72675`**
(coupled to the unbuilt 1065 Analysis compute). Small-partnership exemption (Q4) encoded as a gating fact.
**✅ form 4 of 6 DONE — Schedule L + Schedule B (`1065_L` / `1065_B`).** Seeded + exported (both 200),
all rules cited. Sch L: full BOY/EOY balance sheet (assets 1-14, liab/capital 15-22, a/b contra
sub-lines), computed 14/22 both cols, **R-L-BALANCE (14==22)** + **R-L-21-TIE (partners' capital ↔ M-2
line 9, tax basis)** + small-partnership suppression + M-3 threshold flag. Sch B: all **33 questions**
verbatim, two computed gates — **R-B4-SMALL (Q4 all-four → the `m_schb_q4_small` gate)** + **R-B24-8990
(Q24 §163(j)/§448(c) $31M → Form 8990)**; §754 flag, PR designation, digital asset. Ken walked 4 scope
calls (2026-07-04, all approved): D=author to the 2025 face; **E=§754/§743(b)/§734(b) basis-adjust MATH
RED-defer**; F=M-3/B-1/B-2 RED-defer; G=full a/b Sch L sub-lines. Reconcile (9 items, `1065_core_
reconcile_log.md` L/B section): 2 MATCH (L-totals; tts's DepreciationAsset EOY roll-forward is AHEAD),
**5 tts build-gaps caught** (no balance check; Q4 gate stored-but-dead; no $31M/M-3 threshold; L21↔M-2
not reconciled; **tts Sch L numbered L1-L24 offset one from the face + tts Sch B condensed to 18 vs 33**).
None are RS blockers — the export drives them tts-side.
**► 1065 CORE CAMPAIGN — COMPLETE ✅ (2026-07-04).** Forms 5 & 6 (8825/4562/3800) CONFIRMED to cover
1065 — verified against the LIVE RS DB (not just the brief table): `entity_types` for `3800` =
`['1120S','1065','1120','1040']`, `4562` = `['1120S','1065','1120','1040']`, `8825` = `['1120S','1065']`;
AND the 1065 routing is actually wired, not just entity-tagged — `4562` R004 "§179 flows to Schedule K
(not Page 1)", `8825` R003 "Total net rental → K Line 2" (the exact Sch K line 2 handoff), `3800` GBC
entity-agnostic aggregation. **No fresh authoring needed.** All 6 core forms done: 4 fresh (spine,
K-1+alloc, M-1/M-2, L/B — seeded/exported/200) + 3 pre-existing multi-entity (8825/4562/3800). RS side of
the campaign is CLOSED. What remains are tts-side build items (below) + the optional box-9c DB stamp — none
are RS blockers.
**Two tts-side reconcile items still open (Ken calls, NOT RS blockers):** (1) page-1 off-by-one field
numbering (tts internal deductions=field"21"/ordinary="22" vs the 2025 face 22/23 — map or renumber);
(2) the 1065 Analysis-of-Net-Income build-gap (tts computes none; `R-SCHK-ANALYSIS` is new). Plus the
item-L capital roll-forward gap (M-2 line 1 can't auto-derive) surfaces at the M-2 leg.

**► BOX-9c PASS-THROUGH — CODE-PATH CONFIRMED + CLOSED 2026-07-04 (K-1 leg reconcile).** The K-1
allocation-engine reconcile (this session) traced `k1_allocator`: it reads entity `"K9c"` → writes box
`"9c"` via the **LT_CAPITAL category at `profit_pct`** (exactly the hypothesized ratio; `RECON-9C` in
`SCHEDULE_K1_1065` asserts Σ partner 9c = entity K9c, e.g. 80k @ 60/40 → 48k/32k). The downstream
allocation is verified at the code-path level. **Remaining (optional): the DB stamp** — a focused
`test_4797_pipeline_leg.py` test can ride the eventual K-1 build leg to stamp it end-to-end (spec details
below), but the pass-through itself is no longer an open question.
The 2026-07-03 K9c fix (tts `f23dc54`) made `aggregate_dispositions` write the 1065 entity unrecaptured
§1250 gain to Schedule K line **K9c**, and `k1_allocator` (server/apps/returns/k1_allocator.py: `"K9c"`→
box **9c**, LT_CAPITAL category; the box map at ~line 159) distributes it to each partner's K-1 — now
CONFIRMED. Optional DB-stamp spec:
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

- **⚠ RECONSTRUCTABILITY DRIFT (2026-07-04, `reconstructability_check.md`):** production Supabase
  did NOT cleanly rebuild from the loaders. **FIXED this session:** (1) `seed_all` orchestrator
  (61/61 loaders, 0 problems) — resolves the one hard break (3800 amend ran before its base; now
  amends-last); (2) **prod remediated (Ken "do all safe items"):** deleted the 9 `4797` orphan rules
  (pre-refactor; R007 hardcoded §1250=0, the bug the nuance leg fixed — confirmed superseded) and the
  `1065` empty stub (entity=[], mislabeled "1065_SE") → prod now **88 TaxForms / 420 FlowAssertions**;
  4797 + 1065 now 0-delta, **authority sources 0-delta**. NOTE an initial `FORM_8582`→`8582` rename was
  a MISDIAGNOSIS and was **reverted** — `FORM_8582` (12 rules) is the real passive-loss form (4835
  references it); the bare `8582` is a spurious duplicate that `load_1120s_complete` fabricates.
  ~~**DEFERRED to the August 1120-S delta audit:** stale `8283/8949/8995/8995A`, `SCH_K_1120S`/`SCHD_1120S`
  orphans, the bare-`8582` duplicate.~~ **✅ RESOLVED 2026-07-05 (the delta audit — prod ↔ rebuild now
  0-delta):** §A was an ORDERING bug (`load_1120s_full` amends SCH_K/SCHD but ran before its base — moved to
  `AMEND_LOADERS`, restores R010-18/R010-12, zero prod change); §B/§D was LOADER POLLUTION (removed the
  spurious `_load_8995/8995a/8582/8283` from `load_1120s_complete` + `_load_form_8949` from
  `load_1120s_specs` — prod was already clean); plus a 4797 v1 empty-stub deletion + the GA600S 5.49%/3-factor
  correction (DECISIONS D-8). See `reconstructability_check.md` (top banner) + commit `5f46311`.
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

- 2026-07-05: **FORM 8990 (§163(j) business-interest limitation) AUTHORED + SEEDED + EXPORTED (WO-14) — finishes the 1120 deferred leg; first of the S-16 federal-forms queue.**
  Ken picked a federal-forms queue from the not-built list (8990 → Sch H → 4684 → 4952 → 8379 → 8814 → 8839 → 709 →
  8832 → 3115), recorded in BUILD_ORDER **S-16** + WORK_ORDERS; 8990 done first (pre-context-clear). Research verified
  vs the **FINAL Form 8990 Rev. 12-2025 + i8990** (Created 9/9/25) → `f8990_source_brief.md`. **The load-bearing item:
  line 11 = the EBITDA add-back** (depreciation/amortization/depletion), an ADDITION reinstated by OBBBA for TY2025
  (suspended 2022-24). **Gate-1 (DECISIONS D-16, all recommended):** full Part I compute (ATI EBITDA → 30% limit →
  allowable → indefinite carryforward); Part II/III pass-through formulas (partnership EBIE/ETI + S-corp ETI) with
  direct-entry Sch A/B; $31M §448(c) exemption gate + §163(j)(7) excepted-business diagnostic. `load_8990.py`: 15
  facts / 6 rules / 8 lines / 5 diag / 6 tests / 3 FA; entity_types 1120/1065/1120S/1040. Validated on throwaway
  SQLite (`scratchpad/validate_8990.py`, **19 pass / 0 fail** — incl. the EBIT counterfactual: without the L11 add-back
  the sample's disallowed interest is 180k vs 90k; harness caught a topic_name > 255 cap, trimmed). Ken Gate-1:
  "Approve — flip, seed, export." Seeded → **111 TaxForms / 500 FlowAssertions / 930 FormRules**; `lookup/8990/export/`
  = 200; seed_all reconstructable. Cite OBBBA effective date to P.L. 119-21 + i8990 (Cornell §163(j)(8) lags).
  **Next in the queue: Schedule H** (Household Employment Taxes). BUILD_ORDER S-16 8990 ✅.
- 2026-07-05: **NC + AL PASS-THROUGH BATCH AUTHORED + SEEDED + EXPORTED (WO-13) — completes the adjacent-state pass-through track.**
  Ken: "do the NC + AL". Completes the neighbor pass-through entity coverage (GA-700 + SC1065/SC1120S/PTET done;
  NC + AL were the gaps). Front door: gap-check (all 4 GAP) → 2 parallel research passes (verbatim vs FINAL 2025
  NCDOR/ALDOR) → `nc_al_passthrough_source_brief.md`. **The PTET contrast is the headline (each state differs —
  verify, never clone GA):** NC Taxed PTE = 4.25% (individual rate), owner-side **DEDUCTION** (income out of NC AGI
  via NC-PE); AL Electing PTE = 5% (Form EPT), owner-side **refundable CREDIT** (Sch EPT-C). Research corrections:
  AL election = checkbox on Form 65/20S + Form EPT (not the old PTE-E/MAT); CD-401S DOES compute NC franchise on
  S-corps; AL conforms to §168(k)/§179 (item-by-item). **Gate-1 scope walk (4 AskUserQuestion, all recommended —
  DECISIONS D-15):** full compute both states; encode NC deduction + AL credit; AL Form-20S non-electing taxes
  (LIFO/BIG/excess-passive) = diagnostic+direct-entry; 2 loaders state-paired (AL EPT = referenced compute node).
  **Authored:** `load_nc_passthrough.py` (NC_D403 + NC_CD401S — Taxed PTE 4.25%/deduction, CD-401S net-worth
  franchise, NR withholding 4.25%, 85% bonus/§179 $25k/$200k; reuses CD-405 `_nc_franchise`), `load_al_passthrough.py`
  (AL_FORM_65 + AL_FORM_20S — Electing PTE 5%/credit, composite PTE-C 5%, AL conforms depreciation, Form 20S Line 32
  entity taxes). Validated on throwaway SQLite (`scratchpad/validate_nc_al_pt.py`, **47 pass / 0 fail** — CAUGHT 2
  topic_name > 255 caps, trimmed; NC/AL arithmetic all green; all 16 rules cited). Ken Gate-1: "Approve — flip,
  seed, export." Seeded → **110 TaxForms / 497 FlowAssertions / 924 FormRules**; all 4 exports 200; auto-discovered
  by seed_all. **⚠ [UNVERIFIED]:** exact NC D-403/CD-401S/NC-PE + TY2025 AL Sch K line numbers (PDFs didn't extract)
  — re-pull before the tts app build. **This closes the pre-planned RS spine — net-new RS scope now needs the
  TaxWise forms-usage report or a law change.** BUILD_ORDER S-15 [RS]✅.
- 2026-07-05: **STATE C-CORP BATCH AUTHORED + SEEDED + EXPORTED (WO-12) — SC1120 + AL 20C + NC CD-405, extending the 1120 module.**
  Ken: "state C corp rules", batch the reuse-states (GA's income-tax neighbors AL/NC/SC on the C-corp side; each
  reuses conformity research + consumes the WO-11 federal 1120 output). Front door: gap-check (all 3 GAP) →
  **3 parallel research passes** (verbatim vs FINAL 2025 SCDOR/ALDOR/NCDOR) → `state_ccorp_batch_source_brief.md`.
  **Two premises OVERTURNED by the research** (Authoritative-Source Rule in action): (1) the AL C-corp **federal
  income tax deduction is NOT repealed** — constitutionally protected (Amendment 662), on Form 20C L11a/Sch E;
  (2) the NC franchise tax base is **net-worth-only** (the three-way "greatest of" test was repealed TY2017). Also:
  **AL fully CONFORMS to §168(k)/§179** (no add-back — opposite of SC/NC/GA); the AL decouples are GILTI/§174.
  **Gate-1 scope walk (4 AskUserQuestion, all recommended — DECISIONS D-14):** full compute all three; AL FIT
  deduction = compute apportioned (federal tax × AL ratio); SC = author current 12/31/2024 law + prominent H.3368
  OBBBA-live-wire flag; AL GILTI/§174 = diagnostic + direct-entry. **Authored:** `load_sc1120.py` (SC1120, 5% +
  §168(k) decouple + §179 pre-OBBBA $1.25M/$3.13M + §12-20-50 license fee $15+capital×.001 min $25; reuses SC1120S
  structure), `load_al_form20c.py` (AL_FORM_20C, 6.5% + apportioned FIT deduction + GILTI §40-18-35.2/§174
  §40-18-62; BPT separate; due May 15), `load_nc_cd405.py` (NC_CD405, combined 2.25% income + net-worth franchise
  tax [$500 first-$1M cap, $200 min, $150k holding cap] + 85% bonus/§179 $25k/$200k add-back). Validated on
  throwaway SQLite (`scratchpad/validate_state_ccorp.py`, **41 pass / 0 fail** — SC/AL/NC arithmetic all green,
  caps clean, all 17 rules cited). Ken Gate-1: "Seed all three now." Seeded → **106 TaxForms / 493 FlowAssertions
  / 908 FormRules**; all 3 exports 200; auto-discovered by seed_all. **⚠ SC caveat:** authored to enacted
  12/31/2024 law + D_SC1120_H3368 flag — needs a §179/bonus amend if H.3368 adopts OBBBA retroactively (Ken
  accepted). **Next state C-corp:** FL F-1120 / TN FAE 170 (greenfield). Re-verify all state rates/§179 at TY2026.
- 2026-07-05: **Form 1120 C-CORP MODULE AUTHORED + SEEDED + EXPORTED (WO-11 / S-13) — the first C-corporation entity type.**
  Full front-door run: gap-check (8 gaps; 1125-A/1125-E/3800/4562/4797/8949/7004 confirmed already covering `1120`)
  → **3 parallel research passes** (verbatim vs FINAL 2025 Form 1120 Created 9/26/25 + i1120 + IRC §11/§243/§245A/
  §246/§172/§163(j)/§55/§541/§531 + GA Form 600 Rev. 07/31/25 / IT-611 / GA 4562 Rev. 08/01/25) → `f1120_source_brief.md`.
  Research CAUGHT: OBBBA restructured Schedule J (one list to L23, page-1 total tax = Sch J **L12**, new §1062/Form 1062
  line 32); **§163(j) EBITDA basis RESTORED for TY2025 (OBBBA)** — a stale EBIT assumption would be a TY2025 error;
  **GA §179 2025 = $1.25M/$3.13M** (GA indexes — the $1.05M/$2.62M in CLAUDE.md is the stale 2021 figure).
  **Gate-1 scope walk (4 AskUserQuestion, all recommended — DECISIONS D-13):** form shape = spine + 2; Sch C = domestic
  DRD + §246(b) limit; federal = NOL 80% compute + §163(j)/CAMT/PHC/AET/§1062 screen+route; GA 600 = full (income +
  net worth + depr delta). **Authored 3 forms:** `load_1120_spine.py` (`1120`, 35 facts / 11 rules / 11 lines / 10 diag
  / 8 tests / 4 FA — page-1 → Sch C DRD 50/65/100% + §246(b) loss exception → §172 NOL 80% → §11 21% → Sch J total tax;
  §163(j) >$31M / CAMT $1B / PHC / AET / §59A $500M / §1062 screens), `load_1120_schl.py` (`1120_SCHL`, 27 / 7 / 5 / 5
  / 6 / 3 — Sch L balance L15==L28 + M-1 L10=page-1 L28 + M-2 L8 ties to L25 + Q13 $250k / $10M M-3 gates),
  `load_ga600.py` (`GA600`, 15 / 6 / 6 / 5 / 8 / 3 — GA 5.19% (HB 111) + §168(k)/§179 delta $1.25M/$3.13M + single-factor
  gross-receipts apportionment 6-dec + GA NOL 80% + net worth tax bracket table ≤$100k=$0/max $5,000). Validated on
  throwaway SQLite (`scratchpad/validate_1120.py`, **55 pass / 0 fail** — caps clean 159 checked; all 24 rules cited;
  DRD 50/65/100 + §246(b) limit + loss exception, NOL 80%, 21% tax, Sch L balance/M-1/M-2, GA income + §179 delta +
  net worth table all green). Ken Gate-1: "Approve — flip, seed, export" (W1-W10 blessed). Seeded → **103 TaxForms /
  485 FlowAssertions / 891 FormRules**; all 3 `lookup/{1120,1120_SCHL,GA600}/export/` = 200. Spun off the stale GA §179
  fix (`task_1c8d891e`: CLAUDE.md + GA700/GA600S). **Caveats:** §246(b) combined 50/65 worksheet simplified (single
  limit_pct); §163(j)/CAMT/PHC/AET/§1062 screen+route (compute deferred to 8990/4626/Sch PH/1062); §245A holding period
  is §246(c)(5); TY2026 §163(j) capitalized-interest change not encoded; re-verify all constants at TY2026.
- 2026-07-05: **Form 5227 split-interest module AUTHORED + SEEDED + EXPORTED (WO-10) — the 1041 family is complete.**
  Spun off from the 1041 module (D-10) as its own front-door run: gap-check (all keys GAP) → 3 research passes
  (verbatim vs FINAL 2025 Form 5227 Created 5/7/25 + i5227 Dec 3 2025 + IRC §664/§642(c)/§4947 + Reg §1.664-1(d);
  caught the stale Part IV-A/IV-B layout → flat Part I–IX + Schedule A) → `f5227_source_brief.md` → **Gate-1 scope
  walk (DECISIONS D-11):** CRAT + CRUT COMPUTE the §664(b) four-tier character engine (**tier-level** — ordinary →
  capgain → other → corpus, current + undistributed prior; capital gain one class, no within-Tier-2 rate split) +
  Part II accumulation carryforward with category-isolation netting; §664(c)(2) **100% UBTI excise** (year-keyed
  post-2006 — trust keeps its §664(c)(1) exemption) → Form 4720; Part VIII §4941/4943/4944/4945 screening; PIF/CLT/
  §4947-other = structure + diagnostics; CRT quals (5–50% payout / 10% remainder / 5% exhaustion) = diagnostics
  (funding-time, no §7520/mortality compute). `load_5227.py`: 23 facts / 8 rules / 12 lines / 11 diag / 6 tests / 4 FA;
  all rules cited to 5 sources. Validated on throwaway SQLite (`scratchpad/validate_5227.py`, **20 pass / 0 fail** —
  four-tier ordering, accumulation, UBTI excise, category netting all green). Ken Gate-1: "Approve — flip, seed,
  export." Seeded → **100 TaxForms / 475 FlowAssertions / 867 FormRules**; `lookup/5227/export/` = 200. **Caveats:**
  tier-level (within-Tier-2 rate split deferred); quals diagnostic-only; carried [UNVERIFIED] clauses (§1.664-1(d)(1)(iv)
  netting text, §642(c)(2)/(3), §4947(b)(3) 60%) to re-pull before any deeper compute; SNIIC = proposed reg, not built.
- 2026-07-05: **1041 MODULE COMPLETE (S-11/WO-09) — all 3 legs authored + SEEDED + EXPORTED in one session.**
  The greenfield federal fiduciary module. Ran the full front door: gap-check (all 5 surfaces 404 GAP) →
  4 research passes (verbatim vs FINAL 2025 IRS/GA sources; Rev. Proc. 2025-32 confirmed = TY2026, 2024-40
  governs) → `f1041_source_brief.md` → **Gate-1 scope walk (DECISIONS D-10):** core 4 + ESBT computed;
  grantor=grantor-letter; PIF→Form 5227 (spun off as **WO-10**); bankruptcy=RED-defer; **FULL** distribution
  engine (§662 tiers + §663(c) separate-share + §663(b) 65-day + character); cap-gains-in-DNI = direct-entry +
  3-circumstance §1.643(a)-3(b) diagnostic; **GA 501 resident-only v1**; Sch I AMT = RED-defer (D-2); form keys
  `1041` (spine+SchB+SchG) + `SCHEDULE_K1_1041` + `GA501`. **Leg (a) authored** (`load_1041_spine.py`) —
  one consolidated `1041` form: page-1 income/deductions → ATI (L17) → distribution/exemption block → taxable
  income (L23) → total tax (L24); Schedule B DNI (§643(a)) / IDD (§651/§661 smaller-of-DNI) engine; Schedule G
  (§1(e) 10/24/35/37% rate schedule top $15,650, exemptions $600/$300/$100/QDisT $5,100, cap-gain $3,250/$15,900,
  ESBT L4, §1411 NIIT $15,650 L5). Validated on throwaway SQLite (`scratchpad/validate_1041.py`, **17 pass / 0 fail**
  — CharField caps clean after catching a 290-char topic_name; DNI/IDD/§662-tier/rate-schedule oracles all green).
  Each leg: author `READY_TO_SEED=False` → SQLite-validate → Ken Gate-1 ("Approve — flip, seed, export") → seed → export 200.
  **Leg (a) `1041` spine** (35 facts / 15 rules / 39 lines / 11 diag / 9 tests / 6 FA; `validate_1041.py` 17/0): page-1
  + Sch B DNI (§643(a)) / IDD (§651/§661 smaller-of-DNI) engine + §662 tiers/§663(c) separate-share/§663(b) 65-day;
  Sch G (§1(e) 10/24/35/37% top $15,650, exemptions $600/$300/$100/QDisT $5,100, cap-gain $3,250/$15,900, ESBT L4,
  §1411 NIIT $15,650). **Leg (b) `SCHEDULE_K1_1041`** (29 facts / 7 rules / 17 lines / 6 diag / 6 tests / 4 FA;
  `validate_1041_k1.py` 18/0): beneficiary K-1, boxes 1-8 character retention, box 11 final-year §642(h) gate,
  full verbatim box 9/11/12/13/14 code lists, Σ shares = entity DNI recon. **Leg (c) `GA501`** (19 facts / 7 rules
  / 14 lines / 8 diag / 5 tests / 4 FA; `validate_ga501.py` 16/0): GA fiduciary resident-only, fed 1041 ATI (L17)
  → beneficiary-share-at-L4 (no IDD double-count) → 5.19% → $1,350/$2,700; §168(k)/§179 add-back + Sch 4 nonresident
  RED-deferred. Prod: **99 TaxForms / 471 FlowAssertions / 859 FormRules**; all 3 exports 200. BUILD_ORDER S-11 [RS]✅.
  **Next 1041-family authoring: [WO-10] Form 5227** (split-interest PIF/CRT/CLT, §664 4-tier — own research pass).
  **Caveats:** W4 ESBT = simplified top-rate tax on direct-entered S-portion (full ESBT Tax Worksheet deferred);
  §1062 (OBBBA farmland installment) = structure+flag; GA501 resident-only; re-verify all constants at TY2026.
- 2026-07-05: **GA-500 military-exclusion reconciliation debt CLOSED (RS side) — spec was RIGHT, app was wrong.**
  Closed a BUILD_ORDER "open reconciliation debt." Research-verified (2025 IT-511 p.21 + Form 500 Sch 1 p3 +
  O.C.G.A. §48-7-27(a)(5.1)) that the **RS GA-500 spec is correct and authoritative**: under-62 gate; $17,500
  base + $17,500 only if GA earned income > $17,500; max $35,000; 62+ handled by the general retirement
  exclusion. The **app's 7/5 `min(mret, 35000)` was OVER-inclusive** (ignored the age gate, the earned-income
  condition, and the $17,500 base ceiling) — the app was BEHIND the law, not ahead. No RS TY2025 change needed;
  **tts app fix handed off (`task_f550dfd2`).** Annotated `load_ga500_form_500.py` with a year-keyed **SB 31**
  flag: SB 31 fully exempts military retirement for **TY2026+** (not 2025) — the loader's 2026 military
  placeholder (17,500/35,000) is stale; re-verify the enrolled SB 31 text before the TY2026 build.
- 2026-07-05: **S-5 boundary diagnostics AUTHORED + SEEDED + EXPORTED (WO-04) — consolidated ENTITY_BOUNDARY form.**
  Second full front-door loop (same day as S-6). PRODUCT_MAP §17 mandate: Core never goes silent at a module
  boundary. Gap-check found 4 of 5 boundaries already exist as on-form RED-defers (D_L_M3, D_SCHK_K3,
  D_SCHK_704C, Sch B Q10); the real gaps were the K-2/K-3 **DFE determination** and the **apportionment
  indicator**. Authorities verified verbatim (`boundary_diag_source_brief.md`; research pass): M-3 thresholds
  (i1065 M-3 Rev 11/2023 = $10M assets/$35M receipts/50% REP; i1120S M-3 Rev 12/2019 = $10M assets), the four
  K-2/K-3 DFE criteria (2025 i1065 K-2/K-3), §704(c)/Reg 1.704-3, §754/§743(d)/§734(d) ($250k triggers),
  P.L. 86-272. **Scope (Ken, all recommended):** new **consolidated `ENTITY_BOUNDARY`** form (single season-one
  "completeness critic", entity_types 1065/1120S, 6 self-owned authority sources); **COMPUTE the 4-criteria
  K-2/K-3 DFE gate** (RED `D_EB_K2K3` on fail + `D_EB_DFE_OK` info recording *why* not required); apportionment
  **indicator** (+ P.L. 86-272 shield); **re-encode** M-3/§754/§704(c) with pinned thresholds (existing on-form
  flags stay). Validated on throwaway SQLite (`scratchpad/validate_boundary.py`, ALL PASS — caps clean, all
  rules cited, M-3 + DFE logic spot-checked). Ken: "Approve — flip, seed, export." Seeded → **96 TaxForms /
  457 FlowAssertions / 830 FormRules**; `lookup/ENTITY_BOUNDARY/export/` = 200. BUILD_ORDER S-5 ticked
  [RS]✅→[APP]⬜; NEXT authoring → S-11 1041. **Caveats:** M-3 instr not annually reissued (Rev 11/2023 /
  12/2019 control TY2025 — re-confirm each season); B5 apportionment is state-specific (P.L. 86-272 the only
  federal anchor; per-state thresholds re-verified per state).
- 2026-07-05: **S-6 PAL/basis deepening AUTHORED + SEEDED + EXPORTED (WO-03) — first full front-door loop.**
  The new WORK_ORDERS front door run end-to-end: GAP-CHECKED → research-verify → source brief → Gate-1 scope
  walk → author → SQLite-validate → Ken review walk → seed → export. Authorities verified verbatim
  (`pal_basis_source_brief.md`; research pass): R1 self-rental §1.469-2(f)(6), R2 PTP §469(k), R3 REP
  §469(c)(7)+Reg 1.469-9, R4 at-risk §465/Reg 1.469-2T(d)(6), R5 §461(l)+Rev.Proc.2024-40. **Scope (Ken, all
  recommended):** R1 self-rental (net income non-passive item-by-item, loss stays passive) + R2 PTP (segregated
  off-8582, per-PTP, freed on full disposition) = **COMPUTE** on the FORM_8582/SCHEDULE_E home loader; R3 REP
  **upgraded the old RED-defer → checkbox + §1.469-9(g) aggregation-election flag** (D_8582_RE_PRO error→info;
  two tests preparer-asserted + sanity-checked); R4 at-risk = **diagnostic-only** (ordering §465→§469→§461(l),
  routes to Form 6198); R5 = **new Form `461`** (§461(l) EBL, `load_1040_form_461.py`) computing EBL with pinned
  **2025 thresholds $313,000/$626,000** and flagging it, NOL-conversion described-not-built. Validated on
  throwaway SQLite (`scratchpad/validate_pal.py`, ALL PASS — caps clean, all rules cited, EBL math verified).
  Ken: "Approve — flip, seed, export." Seeded → **95 TaxForms / 454 FlowAssertions / 825 FormRules**; all three
  `lookup/{FORM_8582,SCHEDULE_E,461}/export/` = 200. BUILD_ORDER S-6 ticked [RS]✅→[APP]⬜; NEXT authoring → S-5.
  **Carried caveats:** Form 461 face line-numbering mapped to the §461(l)(3) mechanic (i461 `requires_human_review`
  — confirm the printed Part I-III line numbers before the tts build); disallowed-EBL→NOL is year-keyed (enacted
  TY2025 = NOL conversion; the retest alternative was NOT enacted — re-verify each season).
- 2026-07-05: **WORK_ORDERS front door adopted (BUILD_ORDER-driven) + caught a cross-session stale
  "author Schedule K" loop.** Process-plumbing session (no spec authored). Ken + chat were standing up a
  more orderly authoring process and thrice instructed "author 1065 core, Schedule K first" — but the
  gap-check (step 1 of the front door) returned **exists (200)**: 1065-core RS authoring has been COMPLETE
  since 2026-07-04 (all 6 forms; verified on-disk `load_1065_*.py` + `exports/form_sch_k_1065/` + live
  STATUS). The stale instruction traced to **BUILD_ORDER.md** (canonical in `tts-tax-status`, placed by the
  parallel tts session `b54c111`) carrying an unreconciled `S-4 · 1065 core … untouched beyond SE` +
  `▶ NEXT authoring = Schedule K`. **Fixed the canonical source** (tts-tax-status `5c57886`): S-4 →
  `[RS]✅→[APP]⬜` (schedules ticked; remaining = issuer-side K-1 persistence + tts compute build), NEXT
  advanced to **S-5 boundary diagnostics / S-6 PAL·basis**. **RS repo `9a062cb`:** WORK_ORDERS.md replaced
  with the front-door MECHANISM (gap-check + transitions + Gate-1; no independent backlog — sequence lives
  in the SPINE), reconciled (WO-01 4835 + WO-02 1065-core DONE; SC1040/AL40/NC-D400/GA700 AUTHORED);
  CLAUDE.md boot line + "update WORK_ORDERS at every transition" rule. Memory `rs-1065-core-done-buildorder-stale`
  added. Left SEASON_PLAN.md as re-cut by the parallel session (not replaced).
- 2026-07-05: **SC1065 + SC1120S + SC PTET AUTHORED + SEEDED + EXPORTED — adjacent-state ENTITY track
  begun (DECISIONS D-9).** Ken: "states adjacent to Georgia" → the individual returns for GA's income-tax
  neighbors (AL/NC/SC) were already done, so the frontier is the pass-through ENTITY returns + PTET. Ken
  picked SC. Research pass verified everything vs the FINAL 2025 SCDOR PDFs (I-435 Rev. 1/30/25; SC1065
  Rev. 6/18/25; SC1120S Rev. 6/17/25; I-335 Rev. 6/17/25; SC1120I; §12-6-545) — NEVER memory. The SC PTET
  is the **§12-6-545(G) Active Trade or Business (ATB) elective entity-level tax**: flat **3%** (I-435
  L17) on **active trade/business income ONLY**, an **annual NON-BINDING** page-1 checkbox (contrast GA's
  5.19% irrevocable), owner side an **EXCLUSION not a credit** (I-335 L6 subtracts SC1065 K-1 L14 /
  SC1120S K-1 L13; §12-6-545(G)(3)); entity-taxed ATB also exempt from the 5% nonresident withholding
  (L6 = L1−L2). Scope walk (4 AskUserQuestion, all maximal — D-9): Q1 **BOTH** SC1065 + SC1120S in one
  loader (`load_sc_passthrough.py`); Q2 **COMPUTE** the §168(k) bonus add-back + the §179 delta
  (direct-entry the asset-level SC-4562 figures); Q3 §179 = **indexed $1.25M/$3.13M** (Reading A, pending
  SCDOR confirmation — matches the SC1040 pin); Q4 **COMPUTE** apportionment methods 1&2 (sales-only TPP /
  gross-receipts service, 4 decimals) + the 5% NRW with the full exemption set, RED-defer special/
  individualized apportionment + composite (I-348/I-338) + SC1120S license-fee apportionment + Schedule D.
  SC1120S adds a general **5%** SC income tax on non-ATB net (L9) + the **license fee** (capital × .001 +
  $15, min $25). Validated on throwaway SQLite (`scratchpad/validate_sc.py` — **caught a topic_name 349 >
  255 overflow** SQLite ignores, shortened pre-seed; every rule cited, 0 orphan rules). Ken approved the
  W1-W5 walk ("Approve — flip, seed, export"). Seeded → **94 TaxForms / 449 FlowAssertions**; both
  `lookup/{SC1065,SC1120S}/export/` = 200 (40 KB / 31 KB, facts/rules/line_map/diagnostics/tests all
  present). SC1065: 25 facts / 8 rules / 16 lines / 10 diag / 7 tests; SC1120S: 14 facts / 9 rules / 13
  lines / 6 diag / 6 tests; 8 FA. Reuses the SC conformity sources from `load_sc1040.py`. Auto-discovered
  by `seed_all` (verified `--dry-run`) → reconstructable. `sc1065_source_brief.md`. **W2 live wire:**
  SC H.3368 (pending) would conform SC to OBBBA mid-season → §179 $1.25M/$3.13M → $2.5M/$4M — re-verify.
- 2026-07-05: **1120-S DELTA AUDIT COMPLETE — prod ↔ rebuild now 0-delta.** Closed the deferred
  reconstructability drift. Method: fresh-SQLite `seed_all` rebuild + a per-form rule_id diff vs prod
  (`scratchpad/rebuild_diff.py` + `dump_rules.py`). Findings (all loader-side except one empty-stub delete):
  (§A) `SCH_K_1120S`/`SCHD_1120S` R010-18/R010-12 weren't orphans — `load_1120s_full` *amends* them but ran
  in phase 2 BEFORE its base `load_1120s_specs` (alphabetical), so its `.first()` lookup returned None and
  the rules dropped; **moved it to `AMEND_LOADERS`** (phase 3) → reproduces 17/8, zero prod change. (§B/§D)
  `load_1120s_complete`/`load_1120s_specs` **polluted** the 1040-owned `8283/8949/8995/8995A` with duplicate
  R001-R00x sets + fabricated a bare-`8582`; **removed those blocks** (the 1040 primaries own the forms with
  correct multi-entity types; prod was already clean). (§C-new) deleted the **4797 v1 empty stub** (0 rules,
  snapshot-backed) → prod 93→92 rows. (Bonus, D-8) corrected the **GA600S stale 5.49% PTET rate (live
  `*0.0549`) + 3-factor apportionment** → 5.19% + single gross-receipts (verified via the GA-700 research),
  reseeded. An Explore agent's "R010-18 are reproducible / 8283-8949 intentional" verdicts were REFUTED by
  the empirical rebuild — the diff, not the code-read, was decisive. Verified: 92 form_numbers, 0 form-set
  diff, **0 rule-level diff**. Loader fixes `5f46311`; report banner in `reconstructability_check.md`.
- 2026-07-05: **GA Form 700 + PTET AUTHORED + SEEDED + EXPORTED (August state track, form 4 — track
  COMPLETE).** 1st partnership-entity state spec. Research verified vs the FINAL 2025 GA DOR sources (Form
  700 Rev. 09/11/25; IT-711 booklet; HB 149 PTET FAQ; Reg. 560-7-3-.03). Federal-income start (Sch 8) → GA
  add/subtract (Sch 5/6) → **single gross-receipts apportionment** (Sch 7, 6 decimals) → GA net income
  (Sch 2) → flat **5.19%** tax IF the **PTET election** is made (Sch 1). Scope walk (4 AskUserQuestion, all
  maximal — DECISIONS **D-8**): A **compute the full PTET path** (5.19% entity-level + PTEDED/PTEADD owner
  mechanics — the SALT-cap headline); B **compute the §179 GA-limit delta** ($1.05M/$2.62M, GA didn't adopt
  OBBBA) + model the Sch 5 L7/Sch 6 L4 depreciation add-back/subtract structure, direct-entry the
  asset-level GA-4562 figures; C **compute Sch 4 partner allocation** (resident full / nonresident
  GA-source) + the **4% nonresident withholding** (<$1,000 exempt, displaced by PTET); D direct-entry Sch
  10 credits, RED-defer GA NOL (Sch 9) / composite IT-CR / UET penalty / credit pass-through. Caught the
  **GA600S loader's stale 5.49% rate + 3-factor apportionment** (GA700 pins 5.19% / single-factor; GA600S
  correction logged to the 1120-S delta audit). Conformity Jan 1 2024 (no 2025 bill posted — re-verify).
  Validated on throwaway SQLite (`scratchpad/validate_ga.py`, CharField caps clean). Ken approved the
  W1-W6 walk ("Approve — flip, seed, export"). Seeded → **93 TaxForms / 441 FlowAssertions**;
  `lookup/GA700/export/` = 200. 22 facts / 11 rules / 20 lines / 10 diag / 7 tests / 5 FA, every rule
  cited to 5 GA sources. `ga700_source_brief.md`. **The August state track (SC1040/AL-40/NC-D400/GA-700)
  is now COMPLETE.**
- 2026-07-04: **RS spec cleanup handoff DONE — 5 forms brought to parity with tts builds.** Carried "RS
  follow-ups" from tts STATUS (tts code already correct; RS specs were stale). Amended the HOME loaders
  (reconstructable): (1) **FORM_8911** — retired D_8911_004 (Form 3800 built; error→info + RETIRED, the RS
  equivalent of tts is_active=False), repointed FA-1040-8911-04 to the new flow (line 3 → 3800 row 1s → Sch
  3 6a), rewrote the business-flow rule/line/facts/scenarios off "unbuilt"; (2) **8936/8936_SCHA** —
  extended D_8936_004 to the wrong-PIS-year case, added R-8936-TRANSFER (qualifying transfer STOP, never
  re-lands on Sch 3) + D_8936_008 + FA-1040-8936-06; (3) **8949** — added D_8949_006 (imported-summary
  confirm gate) + ct_import_confirmed fact; (4) **SCHEDULE_A** — added scha_qualified_contributions_cash
  (input-only); (5) **8995** — recorded D_8995_001's retirement (8995-A now computes above-threshold).
  Item 6 (3800 J4 §6417/§6418) = no action (documented divergence). All reseeded, exports 200; prod 92
  TaxForms / 436 FAs. **tts spec mirrors refreshed + committed + pushed** (tts 2ab9dae: 8911/8936/8936_scha/
  8949/schedule_a/8995_spec.json, format-matched per file). Commits 14c7b5d/0deee03/39dbb10/30f73ff/5647024.
  **Deferred to a tts session:** the `flow_assertions_1040.json` FA-gate reconcile (CRLF/hand-managed, feeds
  test_flow_assertions.py; the FA home = the RS loaders is already updated) + running the tts suite to
  reconcile paired seed-leg/count assertions.
- 2026-07-04: **NC D-400 AUTHORED + SEEDED + EXPORTED (August state track, form 3).** 4th state
  individual spec. Research verified vs the FINAL 2025 NCDOR PDFs (Form D-400 + Schedule S rev "Web-Fill
  9-25"; D-401 booklet 2025; §105-153.5/.6/.7). NC starts from **federal AGI** (like GA-500; contrast SC's
  federal-taxable-income start, AL's from-scratch build) at a **flat 4.25%** rate. Scope walk (4
  AskUserQuestion, all maximal/recommended — DECISIONS **D-7**): resident + **Schedule PN** proration
  (L13→L14); **COMPUTE the 85% depreciation add-back** — 85% of federal bonus (Sch S Part A L3) + 85% of
  the §179 excess over NC's **$25k/$200k** limits (L4), direct-entry the 20% prior-year (2020-24) recovery
  installments (the §179 $200k investment phaseout is a diagnostic, not silently computed); **structured
  Part B subtractions** (L18 US-obligation / L19 SS-RR / L20 Bailey / L21 military); direct-entry D-400TC/
  use-tax/contributions, RED-defer Schedule PN-1 / amended lines / L26e underpayment / L39 NC NOL. Also
  computed: the child-deduction AGI-banded table ($3,000→$0), std-ded election (MFS $0 if spouse
  itemizes), NC itemized (Sch A $20k combined cap). Conformity frozen Jan 1 2023 (OBBBA not adopted).
  Validated on throwaway SQLite via `scratchpad/validate_nc.py` (**which caught `D_NCD400_179_PHASEOUT`=21
  > the 20-char `diagnostic_id` cap** pre-seed — shortened to `D_NCD400_179LIMIT`; SQLite doesn't enforce,
  Postgres does). Ken approved the W1-W6 walk in-session ("Approve — flip, seed, export"). Seeded → **92
  TaxForms / 435 FlowAssertions**; `lookup/NC_D400/export/` = 200. `nc_d400_source_brief.md`. Next: GA-700 + PTET.
- 2026-07-04: **AL Form 40 AUTHORED + SEEDED + EXPORTED (August state track, form 2).** 3rd state
  individual spec. Research verified vs the FINAL 2025 AL DOR PDFs (Form 40, booklet incl. the p.31 FIT
  worksheet + p.8 std-ded chart, §40-18-5/§40-18-15). AL builds gross income from scratch (no federal-AGI
  start). Scope walk (4 AskUserQuestion, all recommended): Form 40 full+part-year (40NR RED-defer);
  **computed federal-income-tax deduction** (L12 = (1040 L22 + NIIT) − refundable credits, floored 0,
  PY-apportioned — the AL quirk / "longest walk"); computed sliding-scale std deduction (formula, sidesteps
  the OCR-suspect cell) + dependent exemption; 2/4/5% rate; §414(j)/SS/govt-pension exclusions; direct-entry
  Schedule OC, RED-defer ATP/40NR/NOL. Ken approved the W1-W5 walk ("seed now"). Seeded → **91 TaxForms**;
  `lookup/AL_FORM_40/export/` = 200. `al_form40_source_brief.md`. Commits 1fe6955 + 807af4f. Next: NC D-400.
- 2026-07-04: **SC1040 + Schedule NR AUTHORED + SEEDED + EXPORTED (August state track, form 1).** 2nd
  state individual spec (GA-500 pattern). Two research passes verified everything against the FINAL 2025
  SC DOR PDFs (SC1040 Rev. 4/21/25; SC1040TT Rev. 6/17/25; Sch NR; Act 63/S.507 conformity). MAXIMAL v1
  (DECISIONS D-6): full resident + Schedule NR; **computed §168(k) bonus add-back** (line e); computed
  **§179-excess add-back** (W1 — Ken confirmed SC's pre-OBBBA $1,250,000/$3,130,000, Rev. Proc. 2024-40,
  since SC conforms at 12/31/2024 and did NOT adopt OBBBA); retirement/military/age-65 stack; 44% cap
  gain; SS exempt; $4,930 dependent exemption; child-care + two-wage-earner credits. Schedule NR
  proration → L48 → SC1040 L5. RED-defer I-335/SC4972/catastrophe. Caught a Postgres-only topic_name>255
  overflow (rolled back clean, fixed). Seeded → **90 TaxForms**; both `lookup/{SC1040,SC_SCHEDULE_NR}/
  export/` = 200. `sc1040_source_brief.md` + D-6. Commits a588cc8 + 2fdbc06. Next: AL Form 40.
- 2026-07-04: **draft→approved workflow begun — source-controlled approval + first batch (1065-core 7).**
  July checklist item. `TaxForm.status` already existed; all 88 forms were `draft`. Built a
  **reconstructable** approval mechanism (DECISIONS D-5): `specs/approved_specs.py` manifest +
  `approve_specs` command + `seed_all` phase 5 — approval is source-controlled, NOT a DB edit (a DB-only
  flip would vanish on rebuild, the anti-pattern the recon check just cleaned up). Ken approved the
  1065-core 7 (1065_PAGE1, SCH_K_1065, SCHEDULE_K1_1065, 1065_M1/M2, 1065_L/B) → prod **7 approved / 81
  draft**; held 1065_SE (requires_human_review) + in-flight S3/S4. Verified a fresh `seed_all` restores
  the 7 approvals. Committed `00e6432` + `4a5508b` (explicit-path, clear of the parallel S3/S4 session).
- 2026-07-04: **RS DB reconstructability check DONE + `seed_all` orchestrator built.** July checklist
  item. Built a throwaway SQLite DB, ran every loader via a new `seed_all` command, diffed vs production
  Supabase (form set + per-form rule_ids + entity-model counts). **Verdict: prod does NOT cleanly rebuild.**
  Root cause: no canonical orchestrator + prod mutated incrementally for months, never rebuilt-from-scratch.
  **Fixed (code, zero prod risk):** `specs/management/commands/seed_all.py` — sources → specs → amends →
  flow assertions, **61/61 loaders, 0 problems**; closes the one hard break (`load_1040_form_3800` amend
  ran before its 1120-S base existed → now amends-last → 3800 rebuilds to 12 rules). **4 residual drifts
  logged for Ken** (all prod-data changes — orphaned legacy rules on 4797/SCH_K_1120S/SCHD_1120S; stale
  8283/8949/8995/8995A; `1065` empty stub; and a spurious bare-`8582` loader duplicate). Sources reproduce
  EXACTLY. **Prod remediated (Ken "do all safe items"):** deleted the 9 confirmed-superseded `4797` orphan
  rules + the `1065` empty stub → prod 89→**88 TaxForms** (420 FA intact); an initial `FORM_8582` rename was
  a misdiagnosis and was reverted (it's the real passive-loss form). The rest deferred to the August 1120-S
  delta audit (all `load_1120s_complete/specs`). Full writeup → `reconstructability_check.md`.
- 2026-07-04: **1065-core campaign CLOSED — forms 5 & 6 (8825/4562/3800) confirmed cover 1065.** Verified
  vs the live DB: entity_types carry 1065 AND the routing is wired (4562 "§179 → Schedule K", 8825 "net
  rental → K Line 2"). No fresh authoring. All 6 core forms done.
- 2026-07-04: **1065 core — Schedule L + Schedule B SEEDED + EXPORTED (`1065_L` / `1065_B`).** Form 4 of 6.
  Fresh-authored from the FINAL 2025 f1065 (page 6 Sch L; pages 2-4 Sch B, 33 Qs; pymupdf verbatim) +
  primary IRC (§705 L21↔M-2 tie; §754/§743(b)/§734(b) Q10; §448(c) the $31M behind Q24; §6221(b) Q33 —
  all Cornell LII verbatim). Sch L = full BOY/EOY balance sheet with the balance check (14==22) + the
  tax-basis L21↔M-2 line 9 tie; Sch B = all 33 questions with the Q4 small-partnership gate (feeds
  `m_schb_q4_small` on L/M-1/M-2) + the Q24 §163(j) $31M → Form 8990 gate. Ken walked 4 scope calls
  (AskUserQuestion): E=§754 basis-adjust math RED-defer, D=author to the face, F=M-3/B-1/B-2 RED-defer,
  G=full a/b sub-lines — all approved; "flip seed export". **D-1 reconcile (9 items)** vs tts Schedule L
  totals + `compute_schedule_l()` + `seed_1065` B1-B18 → **caught 5 tts build-gaps** (no balance check;
  Q4 gate stored-but-not-enforced; no $31M/M-3 threshold; L21↔M-2 unreconciled; tts Sch L L1-L24 numbering
  offset one from the 2025 face + tts Sch B condensed to 18 vs the face's 33). Seeded (1065_L: 59 facts /
  6 rules / 28 lines / 5 diag / 5 scenarios; 1065_B: 51 facts / 5 rules / 32 lines / 5 diag / 5 scenarios
  / 4 flow assertions, all cited) → **89 TaxForms / 420 FlowAssertions**; both `lookup/{1065_L,1065_B}/
  export/` = 200 (exports/form_1065_l/, form_1065_b/). Next: 8825/4562/3800 already cover 1065 → campaign
  near-complete.
- 2026-07-04: **1065 core — Schedule M-1 + M-2 SEEDED + EXPORTED (`1065_M1` / `1065_M2`).** Form 3 of 6.
  Authored from the FINAL f1065 page 6 (pymupdf verbatim) + primary IRC (§705 tax-basis capital, §702
  book-tax). M-1: 9 = 5−8 = **Analysis of Net Income line 1** (face verbatim — validates the spine's
  `R-SCHK-ANALYSIS`). M-2 (tax basis): 9 = 5−8; line 3 = Analysis line 1 = M-1 line 9. Reconciled vs tts
  `FORMULAS_1065` M-1/M-2 → surfaced the **M2_3 mis-source** (tts labels line 3 "per books" data-entry;
  a tax-basis M-2 ties it to Analysis line 1 per return) → Ken: "log + spawn tts task" → **`task_4bf72675`**
  (coupled to the unbuilt 1065 Analysis compute + M-1 line 9). Sch B Q4 small-partnership exemption →
  gating fact. Seeded (all cited) → 87 TaxForms; both `lookup/{1065_M1,1065_M2}/export/` = 200. Next: form
  4 (Schedule L + Schedule B).
- 2026-07-04: **1065 core — Schedule K-1 + allocation engine SEEDED + EXPORTED (`SCHEDULE_K1_1065`).**
  Form 2 of 6. Fresh-authored + reconciled against tts `k1_allocator.py` (Explore agent survey): encodes
  the engine's profit/loss-% allocation + `PartnerAllocation` category overrides (Lacerte special
  allocations), GP + distributions direct per-partner, box 9c LT-capital ratio (**CONFIRMED — closes the
  box-9c pass-through**), box 14a = `1065_SE` cross-ref. RED-deferred per Decision C (structure + cited
  authority + gating flag, math deferred): §704(c) built-in gain (items M/N), §704(b) SEE, §706(d) varying
  interest, item-L capital roll-forward (→ M-2 line 1 can't auto-derive). Primary IRC verbatim (§704/
  §706(d)(1)/§752/§705/§707(c)). **Ken: "full ~200-code transcription now"** → downloaded the FINAL
  i1065sk1.pdf + extracted pp. 33-36 via pymupdf → the box 11/13/14/15/17/18/19/20 code lists (A-ZZ)
  encoded VERBATIM as `IRS_2025_I1065SK1` excerpts (source-grounded, not recalled). Seeded (27 facts / 11
  rules / 17 lines / 7 diag / 8 scenarios / 4 flow assertions, all cited) → 85 TaxForms; exported HTTP 200
  (exports/form_schedule_k1_1065/, 80 KB, all 8 code-list excerpts present). Next: form 3 (M-1/M-2).
- 2026-07-04: **1065 core campaign — Schedule K spine SEEDED + EXPORTED (2 forms) + a tts bug fixed.**
  Ken said "go"; walked the 3 season-one scope decisions (K-2/K-3 defer, M-3 defer, §704 structure-only).
  Fresh-authored `load_1065_schedule_k.py` → `1065_PAGE1` (page-1 ordinary business income, line 23 → Sch K
  line 1) + `SCH_K_1065` (distributive-share spine 1-21 + Analysis of Net Income). Primary IRC quoted
  verbatim (§702(a)/(b), §703(a)/(b), §704(a)/(b) fetched this session; §707(c) reused); form-line maps from
  the brief's FINAL-2025 f1065/i1065 verbatim transcription. All rules cited. **D-1 reconcile** vs tts
  compute.py (8 items: 4 match, 1 build-gap, 1 CONFIRMED+FIXED, 2 open Ken calls) → the reconcile **CAUGHT a
  tts net-farm compute bug** (Schedule F net misrouted to Sch K line 11, excluded from K1 + the SE base;
  latent double-count) — Ken: "fix now" → fixed in tts `f61cfec` with a 3-test regression (green). Ken:
  "flip seed export" → **SEEDED** (84 TaxForms / 404 FlowAssertions) + **EXPORTED** (both endpoints HTTP 200,
  exports/form_1065_page1/ + exports/form_sch_k_1065/). Next: form 2 (Schedule K-1 + allocation engine).
- 2026-07-04: **S3/S4 MeF ATS unblock campaign — four specs live, all endpoints 200.** Ken's campaign
  prompt (from a tts Claude): author the four missing specs blocking the last two 1040 MeF ATS scenarios.
  Started from the tts authoring notes as HYPOTHESIS; verified every rule against the FINAL 2025 IRS
  sources (2 parallel subagents read the PDFs verbatim). **`8835`** (§45 renewable electricity production
  credit; before-2025 begin-construction gate; ×5/+10%/+10%; line-15 -> 3800 4e/1f; S4 solar $13,200).
  **`8936` + `8936_SCHA`** (clean vehicle credits 30D/25E/45W; **OBBBA 9/30/2025 acquired-termination**
  per-vehicle gate; MAGI best-of-two-years; used/commercial formulas; routing to Sch3 6f/6m + 3800
  1y/1aa + Sch2 1b/1c). **Schedule A key = `8936_SCHA`** (separate form, 1120S_SCHL convention). **`4835`
  reconciled** (added the S3 ATS vector + resolved the QBI [VERIFY] -> §162-trade/business preparer
  determination). DB: 82 TaxForms / 400 FlowAssertions; exports in `exports/form_{4835,8835,8936,8936_scha}/`.
  Open [VERIFY] carried to the tts build (flagged, not guessed): the S4 tentative EV credit is BLANK on
  the scenario form — do NOT assume $7,500. See D-4.
- 2026-07-04: **`4835` (Form 4835 — Farm Rental Income and Expenses) authored + seeded + exported** —
  pivot from a parallel tts session blocked on the missing 4835 spec (real 404). Source-verified the 2025
  face verbatim (f4835.pdf pages 1-3). Ken walked 4 scope decisions (D-3): the LOSS PATH is FULLY COMPUTED
  for MeF (§465 at-risk / Form 6198 BEFORE §469 passive / Form 8582 $25k special allowance → line 34c →
  Sch E line 40), integrating the EXISTING RS 6198 + FORM_8582 specs; a HARD SE-EXCLUSION invariant
  (§1402(a)(1); contrast Sch F); elections captured+flagged; a material-participation → Schedule F routing
  guard; per-activity multi-instance. `load_1040_form_4835.py`: 54 facts / 11 rules (all cited) / 52 lines /
  8 diagnostics / 12 scenarios / 9 flow assertions. Verified L7 gross = right-column sum; corrected the old
  authority stub's "Sch E Part I" (→ net → line 40, gross → line 42). **`lookup/4835/export/` now returns
  200** (was 404); 90 KB export saved to `exports/form_4835/`. The tts S3 pointer is unblocked.
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
