---
type: project-status
project: sherpa-tax-rule-studio
last_updated: 2026-07-04
---

# STATUS — sherpa-tax-rule-studio

*The freshest file. Answers "where am I on this project?" Updated at the end of every substantive session.*

---

## Current state

Active spec-authoring tool. RS Supabase holds **89 TaxForms / 420 FlowAssertions** (other tracks are
seeding too — check the index, not this line, for exact counts). **The 1065-core campaign is COMPLETE
(2026-07-04)** — all 6 core forms covered (4 fresh + 8825/4562/3800 confirmed multi-entity, verified
against the live DB incl. actual Sch K routing). Newest: the **1065-core Schedule L +
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
  does NOT cleanly rebuild from the loaders. **FIXED this session:** the `seed_all` orchestrator
  (61/61 loaders, 0 problems) — resolves the one hard break (3800 amend ran before its base; now
  amends-last). **STILL OPEN — needs Ken (all are prod-data changes):** (A) prod carries orphaned
  legacy rules no loader reproduces — `4797` R001-R008/R010, `SCH_K_1120S` R010-R018, `SCHD_1120S`
  R010-R012 (loaders refactored to new rule_ids; prod never cleaned) → delete if superseded; (B)
  prod STALE vs loaders — `8283`/`8949`/`8995`/`8995A` (loaders ahead) → re-seed (additive, safe);
  (C) `1065` empty stub (entity=[], 0 rules, mislabeled title "1065_SE") lives only in DB → delete;
  (D) `FORM_8582` legacy naming vs the loader's bare `8582` → rename prod row. Authority sources
  reproduce EXACTLY (0 delta). See the report for the remediation order.
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

- 2026-07-04: **RS DB reconstructability check DONE + `seed_all` orchestrator built.** July checklist
  item. Built a throwaway SQLite DB, ran every loader via a new `seed_all` command, diffed vs production
  Supabase (form set + per-form rule_ids + entity-model counts). **Verdict: prod does NOT cleanly rebuild.**
  Root cause: no canonical orchestrator + prod mutated incrementally for months, never rebuilt-from-scratch.
  **Fixed (code, zero prod risk):** `specs/management/commands/seed_all.py` — sources → specs → amends →
  flow assertions, **61/61 loaders, 0 problems**; closes the one hard break (`load_1040_form_3800` amend
  ran before its 1120-S base existed → now amends-last → 3800 rebuilds to 12 rules). **4 residual drifts
  logged for Ken** (all prod-data changes — orphaned legacy rules on 4797/SCH_K_1120S/SCHD_1120S; stale
  8283/8949/8995/8995A; `1065` empty stub; `FORM_8582`→`8582` naming). Sources reproduce EXACTLY. Full
  writeup + remediation order → `reconstructability_check.md`. No prod mutation this session (89/420 intact).
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
