# Rule Studio — Session Log
*One entry per session that touches Rule Studio. Newest first.
Created 2026-06-10 during the 1040 campaign Phase 0 state audit (this file did not previously exist).*

---

## 2026-07-08 (evening) — 4797 ENTITY PASS-THROUGH LEG authored + seeded (Ken ruling: "build the full unit")
*The §179-disposition pass-through gap found in the tts S5 mapper build (REVIEW_QUEUE 2026-07-08);
Ken ruled build-the-full-unit on the recommended option. Spec-first — this is the RS leg.*
- **Law verified verbatim 2026-07-08** (live i4797 HTML + i1120s PDF p.15/41 + i1065 PDF p.20/52,
  pymupdf): i4797 "Partnerships and S corporations do not report these transactions on Form 4797,
  4684, 6252, or 8824…"; i1120s line 4 → K-1 box 17 code K + the 8-item PRO-RATA statement list;
  i1065 line 6 → box 20 code L; i1120s M-2 adjustment 1 (AAA increase by income) = the 3a
  other-addition home for the corp-level gain.
- **load_4797 amended** (in-loader — this loader preserves entity_types on every seed):
  NEW rule `R-4797-ENTPASS` (routing; per-property `f4797_sec179_passthrough` excludes the property
  from EVERY 4797 line; outputs `f4797_ent179_gain/price/cost/s179` — the statement dataset +
  the AAA 3a addition) · NEW diagnostic `D_4797_ENTPASS` (info, never-silent) · 2 new facts +
  4 output facts · scenarios F4797-E1/E2 (the ATS S5 Dodge-truck numbers: gain 1,400, statement
  cost 1,000 EXCLUDING §179, §179 1,000) · NEW source `IRS_2025_1065_INSTR` + excerpts on
  `IRS_2025_4797_INSTR`/`IRS_2025_1120S_INSTR` · 2 new FAs `FA-ENT-4797-179` (1120S+1065
  exclusion + Σ pro-rata = entity totals) / `FA-1120S-M2-179` (gain → M-2 3a).
- **KEY-QUIRK NOTE encoded in the rule:** the ATS S5 key prints FULL facts on EACH 50% K-1 and
  2×gain (2,800) on M-2 3a — contradicts the i1120s verbatim "pro rata share" + §1377(a); the
  spec encodes the LAW (pro-rata per owner, gain enters AAA once). Owner-side 1040 reporting
  from K-1 17K facts = stated follow-up unit.
- `check_4797_integrity.py` extended (own transcription of the exclusion) — **ALL CHECKS PASS**
  (33 facts / 9 rules / 15 diagnostics / 22 scenarios / 9 FAs). **Seeded RS Supabase**
  (FlowAssertions 539→541); **deployed export verified** (R-4797-ENTPASS + D_4797_ENTPASS +
  the 6 new facts + E1/E2 all served); tts canonical `server/specs/4797_spec.json` refreshed.
- Pre-existing drift noted, not touched: the export still serves the stale `F4797-G2` scenario
  row (removed from the loader 2026-06-28; seeder can't delete DB rows).

## 2026-07-08 — 1041 flow-assertion family CONSOLIDATED + ACTIVATED (S-11 leg 8a, Ken-approved)
*Ken green-lit the tax-app REVIEW_QUEUE authoring plan ("go ahead with the 1041 FA authoring plan").*
- **Root cause of the "zero 1041 FAs" export:** the 2026-07-05 S-11 authoring HAD staged 10 draft
  FlowAssertions (spine: DNI/IDD/TIERS/EXEMPT/TAX/NIIT · K-1: CHAR/RECON/FINYR/NIIT) — none ever
  activated, and the export serves active-only. The tax-app leg-8 gate build surfaced it.
- **NEW `load_1041_flow_assertions.py` = the single FA home for the 1041 family** (17 active +
  2 staged), transcribed from the approved R-1041-*/R-K1041-* rules (no new tax law): page-1
  chains (TOTINC/ATI/TAXINC/TOTTAX/SETTLE) · Subchapter J core (DNI incl. the corpus-gain
  back-out, IDD smaller-of, §662 TIERS) · §642(b) EXEMPT table · §1(e) RATES + CGRATE 0/15/20
  stacking pins (RP 2024-40) · ESBT 37% · K-1 CHAR/SUM/FINYR · GATE-1041-DEFERS (AMT/bankruptcy
  RED-defers + grantor-no-K-1) · FA-1041-GA501 (state base = federal ATI).
- **Reconciliation:** ids shared with the drafts re-authored + FORCE-ACTIVE (the load_sch_1a
  precedent); FA-K1041-FINYR adopted active (engine-backed); **FA-1041-TAX + FA-K1041-RECON
  DISABLED** (superseded by RATES+CGRATE / SUM — supersession note prepended to description);
  **FA-1041-NIIT + FA-K1041-NIIT stay STAGED** (trust-side 8960 + the box-14H→8960-L7 import
  are unbuilt). FA blocks REMOVED from load_1041_spine / load_1041_schedule_k1 (tombstoned) so
  a reseed can't regress statuses; the k1 loader's hollow-seed guard no longer requires FAs.
- Validated on throwaway SQLite (`scratchpad/validate_1041_fa.py` — 17 active + 2 staged,
  ids ≤ varchar(20), idempotent). **Seeded RS Supabase** (539 total — the 10 drafts updated in
  place + 9 new rows). **Deployed export verified:** `entity_type=1041` serves exactly the 17
  actives.
- tts side (same session): export cached as canonical `server/specs/flow_assertions_1041.json`;
  17 pure runners registered (`_RUNNERS_1041`) exercising compute_1041 / rate_schedule_tax /
  capital_gain_tax / allocate_k1_boxes / compute_ga501; full gate **422 → 440**. → the 1041
  form's last buildable leg closed; S-11 fully ticks on the app side.

## 2026-07-05 — SC1040 spec hygiene fix (promote to active + correct the $50k test pin)
During the tts-app SC1040 build (S-7), two hygiene issues surfaced in `load_sc1040.py`:
- **`FORM_STATUS` `draft` → `active`** — the spec was fully authored + Ken-approved 2026-07-04
  (`READY_TO_SEED = True`), only the status label lagged.
- **Test scenario "SC resident, wages only, single, no dependents" pin corrected** — the
  `expected_outputs` L6 was the rough placeholder string `"SC1040TT lookup (~6% marginal at top;
  ≈ $2,533)"`, which is WRONG. The published **SC1040TT_2025 row for $50,000-$50,050 = $2,360**
  (the table applies the 3-bracket structure to each $50-bracket MIDPOINT: 6%×$50,025 − 642 =
  2359.50 → $2,360 half-up). The tts engine reproduces the published table **138/138 rows, zero
  mismatches** (verified vs the SCDOR PDF). Pin is now numeric `2360` + an explanatory note.
- **Re-seeded RS Supabase** (`manage.py load_sc1040`, idempotent update_or_create) — deployed
  `lookup/SC1040/export/` now returns `status: active` + `L6: 2360` (verified live, HTTP 200).
- No tax-law change; the rules/line_map/diagnostics were already correct (the tts four-leg app was
  built from them). `SC_SCHEDULE_NR` re-seeded alongside (unchanged).

## 2026-07-05 — GA-500 military-exclusion reconciliation debt CLOSED (RS side) — spec authoritative, app over-inclusive
*Picked up the BUILD_ORDER "open reconciliation debt" as a bounded close after S-5/S-6. The debt framed it as
"the app should not stay ahead of the law" — the gap-check + research showed the REVERSE.*
- **Gap-check:** `load_ga500_form_500.py` already fully models the military exclusion — `GA_MILITARY_RIE_BASE
  {2025:17500}` / `GA_MILITARY_RIE_MAX {2025:35000}` + a verbatim IT-511 Sch 1 p3 worksheet excerpt (under-62;
  base $17,500; +$17,500 once GA earned income ≥ $17,501; max $35,000). The RS spec was NOT behind.
- **Research-verified (2025 IT-511 p.21, Form 500 Sch 1 p3, O.C.G.A. §48-7-27(a)(5.1)(A)):** the RS rule is
  correct. The app's 7/5 `min(mret, 35000)` is OVER-inclusive — wrong 3 ways: ignores the under-62 age gate
  (grants it at any age), ignores the earned-income condition on the second $17,500, and the base tranche
  alone caps at $17,500 not $35,000. A 62+ taxpayer's military pay is handled by the GENERAL retirement
  exclusion ($35k 62-64 / $65k 65+), not the military one — the two are age-segregated, never stacked.
- **SB 31 year-keyed find:** GA SB 31 (2025 session) fully exempts military retirement regardless of age/income
  for **taxable years beginning on/after Jan 1, 2026** — does NOT reach TY2025. So the RS spec correctly keeps
  the HB 1064 structure for 2025; the loader's 2026 military placeholder (17,500/35,000) is STALE for TY2026.
- **Resolution (spec-first):** no RS TY2025 spec change (already correct); annotated the loader with a
  year-keyed SB 31 warning (comment only — no seeded field changed, so no reseed); **spawned tts task
  `task_f550dfd2`** to fix the app compute to the worksheet logic. Closed the debt in BUILD_ORDER.
  Reinforces the front-door value: the spec-vs-app reconciliation caught that the APP had drifted, not the spec.

## 2026-07-05 — S-5 boundary diagnostics AUTHORED + SEEDED + EXPORTED (WO-04) — consolidated ENTITY_BOUNDARY form
*Ken opened S-5 right after S-6. Second full front-door loop the same day. PRODUCT_MAP §17: Core never goes
silent at a module boundary — it must DETECT and throw a loud RED diagnostic.*
- **Gap-check finding:** 4 of 5 boundaries already existed as on-form RED-defers (D_L_M3 on 1065_L; D_SCHK_K3
  + D_SCHK_704C on SCH_K_1065; Sch B Q10 §754 on 1065_B). But D_SCHK_K3 was a **blanket "international out of
  scope" flag** — PRODUCT_MAP makes the **DFE determination** ("record WHY K-2/K-3 aren't required") Core season
  one. Real gaps = the K-2/K-3 DFE gate + a multistate-apportionment indicator.
- **Authorities verified (research pass, NOT memory):** M-3 (Instr. Sch. M-3 1065 Rev. 11/2023 = $10M assets /
  $35M receipts / 50% REP; 1120-S Rev. 12/2019 = $10M assets single test); K-2/K-3 DFE 4 criteria (2025 i1065
  K-2/K-3); §704(c)/Treas. Reg. §1.704-3; §754/§743(d)/§734(d) ($250k substantial built-in loss / basis
  reduction); P.L. 86-272 (15 U.S.C. §381). OBBBA changed none of these.
- **Scope (Ken, all recommended):** SHAPE = a **new consolidated `ENTITY_BOUNDARY` form** (single completeness
  critic, not scattered amendments); K-2/K-3 = **COMPUTE the 4-criteria DFE gate** (RED D_EB_K2K3 on fail +
  D_EB_DFE_OK info recording the basis); apportionment = **indicator** (+ P.L. 86-272 note, state-specific);
  M-3/§754/§704(c) = **re-encode with pinned thresholds** (existing on-form flags remain).
- **Authored** `load_entity_boundary.py` — form `ENTITY_BOUNDARY` (entity_types 1065/1120S), 23 facts / 5 rules
  / 5 lines / 6 diagnostics / 10 scenarios / 3 FA. **6 self-owned authority sources** (IRS_2025_M3_1065,
  IRS_2025_M3_1120S, IRS_2025_K2K3_1065, TREAS_REG_704_3, IRC_754_743_734, PL_86_272) so it reconstructs
  standalone (no cross-loader source dependency). Auto-discovered by seed_all phase 2.
- **Validated** on throwaway SQLite (`scratchpad/validate_boundary.py`): form seeded, all rules/diags present,
  ALL rules cited, CharField caps introspected-and-clean, M-3 (both entity branches) + DFE (all-met / K-3-request
  / foreign-tax>$300) logic spot-checked. ALL PASS.
- **Ken review walk → "Approve — flip, seed, export."** Flipped READY_TO_SEED, seeded to prod (95→**96 TaxForms
  / 457 FlowAssertions / 830 FormRules**), verified `lookup/ENTITY_BOUNDARY/export/` = **200**. BUILD_ORDER S-5
  ticked [RS]✅→[APP]⬜, NEXT authoring advanced to S-11 (1041). Explicit-path commits.
- **Caveats carried to the tts build:** (1) M-3 instruction sets aren't reissued annually (1065 Rev 11/2023,
  1120-S Rev 12/2019 control TY2025 — thresholds unchanged; re-confirm each season). (2) B5 apportionment is
  state-specific — P.L. 86-272 is the only federal anchor; per-state nexus thresholds pulled/verified per state.
- **RS authoring spine now clear to S-11:** S-4 (1065 core), S-5 (boundary diagnostics), S-6 (PAL/basis) all DONE.

## 2026-07-05 — S-6 PAL/basis deepening AUTHORED + SEEDED + EXPORTED (WO-03) — first full front-door loop
*Ken opened S-6 through the new front door ("finish the new procedure implementation" → picked S-6 PAL/basis).
The whole WORK_ORDERS pipeline ran once, end-to-end, as designed. No prod risk until the review-walk approval.*
- **Front-door loop (all transitions logged in WORK_ORDERS.md):** GAP-CHECKED (R1-R4 = amendments to the
  existing FORM_8582/SCHEDULE_E; R5 §461(l) = the one real gap) → research-verify (background agent, verbatim
  vs primary sources) → `pal_basis_source_brief.md` → Gate-1 scope walk (4 AskUserQuestion) → author →
  SQLite-validate → Ken review walk → flip + seed + export.
- **Authorities verified (research pass, NOT memory):** R1 self-rental Treas. Reg. §1.469-2(f)(6); R2 PTP IRC
  §469(k); R3 REP §469(c)(7) + Treas. Reg. §1.469-9; R4 at-risk §465 + Reg. §1.469-2T(d)(6) ordering; R5
  §461(l) + Rev. Proc. 2024-40 + i461 (2025). 2025 EBL thresholds **$313,000 / $626,000** (Rev. Proc. 2024-40,
  confirmed verbatim by i461). OBBBA made §461(l) permanent; disallowed EBL → NOL carryover (the "retest"
  alternative was NON-enacted — flagged year-keyed).
- **Scope (Ken, all recommended):** R1+R2 COMPUTE (self-rental net-income recharacterization item-by-item, loss
  stays passive; PTP segregated off-8582, per-PTP, freed on full disposition); R3 REP **upgraded the 2026-06-13
  RED-defer → checkbox + §1.469-9(g) election flag** (D_8582_RE_PRO error→info; the two tests preparer-asserted
  + sanity-checked via D_8582_REP_TESTS; D_8582_REP_MATLPART reminds each un-aggregated rental needs material
  participation); R4 at-risk = diagnostic-only (D_8582_ATRISK, ordering §465→§469→§461(l), route to 6198); R5
  = new Form `461` diagnostic (computes EBL + flags; pinned thresholds; NOL described-not-built).
- **Authored:** R1-R4 amend the HOME loader `load_1040_schedule_e.py` (reconstructable — replays in seed_all
  phase 2); R5 = new `load_1040_form_461.py` (auto-discovered by seed_all). New authorities: TREAS_REG_469,
  IRC_465, IRC_461, IRS_2025_F461_INSTR, REV_PROC_2024_40; §469(k)/§469(c)(7) excerpts added to IRC_469.
- **Validated** on throwaway SQLite (`scratchpad/validate_pal.py`): 3 forms seeded, all new rules/diags present,
  D_8582_RE_PRO upgraded, ALL rules cited, CharField caps introspected-and-clean, EBL math spot-checked. ALL PASS.
- **Ken review walk (W1-W5) → "Approve — flip, seed, export."** Flipped Form 461 `READY_TO_SEED`, seeded both
  loaders to prod (94→**95 TaxForms / 454 FlowAssertions / 825 FormRules**), verified `lookup/{FORM_8582,
  SCHEDULE_E,461}/export/` all **200** (in-process test client, read-only). BUILD_ORDER S-6 ticked [RS]✅→[APP]⬜
  (tts-tax-status), NEXT authoring advanced to S-5. Explicit-path commits (shared worktree).
- **Two caveats carried to the tts build (flagged, not guessed):** (1) Form 461 FACE line-numbering was mapped
  to the §461(l)(3) mechanic (BIZ-INC/BIZ-DED/THRESH/EBL/NOL), NOT the printed 2025 Part I-III positions —
  i461 `requires_human_review`; confirm before the app build. (2) disallowed-EBL→NOL is year-keyed.

## 2026-07-05 — WORK_ORDERS front-door adopted + BUILD_ORDER-driven; caught a cross-session stale "author Schedule K" loop
*Ken + chat were setting up "a more automated orderly process" (the WORK_ORDERS front door) and, across three
prompts, kept instructing "author 1065 core, Schedule K first." A parallel tts/app session was editing the
shared brain concurrently. No spec authored this session — it was process plumbing + a reconciliation fix.*
- **Root finding — the instruction was stale, thrice.** 1065-core RS authoring is COMPLETE (2026-07-04): all
  6 forms seeded+exported (200) — Schedule K spine (`1065_PAGE1`+`SCH_K_1065`), K-1+alloc, M-1/M-2, L/B;
  8825/4562/3800 cover 1065; 7-form batch in `approved_specs.py`. Verified on-disk (`load_1065_*.py` +
  `exports/form_sch_k_1065/`) + live STATUS. Running the gap-check on Schedule K returned "exists (200)" —
  the front door working as designed (it CAUGHT the would-be duplicate). Same over-completion on WO-01 (4835/
  8835/8936 all done) + the four state specs.
- **The drift's source.** BUILD_ORDER.md (canonical in `tts-tax-status`) — placed by the parallel session
  (`b54c111`) — carried a stale `S-4 · 1065 core … untouched beyond SE`, all schedule boxes unticked, and a
  `▶ NEXT authoring = Schedule K [RS/Ken]` line, *despite* a header claiming the marks were reconciled to live
  STATUS. Both sessions inherited the stale line and talked past each other through it.
- **Files placed/edited (RS repo, `9a062cb`):** replaced WORK_ORDERS.md with the provided BUILD_ORDER-driven
  version (front-door MECHANISM only — gap-check + transitions + Gate-1; NO independent backlog, sequence
  lives in the SPINE), reconciled to live STATUS (WO-01 4835 + WO-02 1065-core DONE; SC1040/AL40/NC-D400/GA700
  AUTHORED). CLAUDE.md: boot line (pull tts-tax-status; BUILD_ORDER=order / SEASON_PLAN=gates / PRODUCT_MAP=scope)
  + standing rule "update WORK_ORDERS at every transition; the queue is the record."
- **Fixed the canonical source (tts-tax-status `5c57886`).** BUILD_ORDER S-4 → `[RS]✅→[APP]⬜` (schedules
  ticked DONE 2026-07-04; remaining = issuer-side 1065 K-1 persistence → 1040 import + tts compute build);
  `▶ NEXT authoring` advanced off Schedule K to **S-5 boundary diagnostics / S-6 PAL·basis** (S-6 before the
  regression bed locks). Zip's BUILD_ORDER/PRODUCT_MAP were already committed by the parallel session; left
  SEASON_PLAN.md as re-cut by that session (not replaced).
- **Coordination risk noted:** the tts session is only paused mid-migration; the S-4 fix is on origin so a
  pull-before-edit there carries it, but watch for a re-cut reverting it.
- **Memory:** added `rs-1065-core-done-buildorder-stale` (don't re-author Schedule K; seed SPINE status from
  live STATUS, not draft checkboxes) + MEMORY.md index line. Explicit-path commits throughout (shared worktree).

## 2026-07-05 — 1120-S delta audit COMPLETE (prod ↔ rebuild 0-delta)
*Ken: "lets start the delta audit" (declined a context clear — the audit overlapped fresh GA-700 context).
Closed the deferred reconstructability drift from the 2026-07-04 check. Clear of the parallel session
(explicit-path commits).*
- **Method:** fresh-SQLite `seed_all` rebuild + per-form rule_id diff vs prod (`scratchpad/rebuild_diff.py`,
  `dump_rules.py`, `dump_forms.py`). Dispatched an Explore agent to map the 5-loader 1120-S landscape — but
  its intent verdicts ("R010-18 reproducible", "8283/8949 intentional multi-entity") were **REFUTED by the
  empirical rebuild**; the diff was decisive, not the code-read. Lesson: verify loader-provenance claims
  against an actual rebuild.
- **§A — ORDERING BUG (not orphans).** `load_1120s_full` amends `SCH_K_1120S`/`SCHD_1120S` (adds R010-18/
  R010-12) but ran alphabetically in phase 2 BEFORE its base `load_1120s_specs`; its `.first()` lookup
  returned None → rules silently dropped on rebuild (rebuild had 8/5, prod 17/8). **Fix:** moved it to
  `seed_all` `AMEND_LOADERS` (phase 3) → rebuild reproduces 17/8. **Zero prod change** (prod already had them).
- **§B/§D — LOADER POLLUTION.** `load_1120s_complete` (`_load_8995/8995a/8582/8283`) + `load_1120s_specs`
  (`_load_form_8949`) re-seeded 1040-owned forms with duplicate R001-R00x sets prod never had + fabricated a
  bare `8582`. Confirmed the 1040 primaries own these (multi-entity types set there). **Removed the 5 blocks**
  (466 + 122 lines, assertion-guarded scripts). **Zero prod change** — prod was clean; pollution was rebuild-only.
- **§C-new — 4797 v1 empty stub.** The last prod-vs-rebuild gap (prod 93 rows vs rebuild 92): a 0-rule v1
  version left when the 2026-07-04 check deleted 4797's orphan rules but not the emptied row (export serves
  v2, 8 rules). Ken approved delete → snapshot-backed removal (`remediation_snapshot_4797_v1.json`; v1 also
  carried 19 stale facts/22 lines/5 diag/6 scenarios that cascaded). Prod 93 → **92**.
- **Bonus (DECISIONS D-8) — GA600S content correction.** The GA S-corp spec (`load_remaining_1120s`) had a
  **stale 5.49% PTET rate with a LIVE compute `* 0.0549`** + a **3-factor apportionment formula** — both wrong
  for 2025. Corrected to **5.19%** (Form 600S Rev. 09/11/25) + the **single gross-receipts factor** (§48-7-31),
  verified via the GA-700 research; the PTET scenario `$200K × 5.49% = $10,980` → `× 5.19% = $10,380`. Reseeded;
  `lookup/GA600S/export/` = 200 (R003 `*0.0519`, R005 single-factor, ptet_rate 5.19).
- **RESULT:** prod ↔ a fresh rebuild is **0-delta** — 92 form_numbers, 0 form-set diff, 0 rule-level diff.
  Prod **92 TaxForms / 441 FlowAssertions / 801 FormRules**. Loader fixes committed `5f46311`; docs updated
  (`reconstructability_check.md` banner + Remaining-order item 2 ✅; STATUS Known-issues resolved). The
  standing check (rebuild + diff) is documented for periodic re-run.

## 2026-07-05 — GA Form 700 + PTET AUTHORED + SEEDED + EXPORTED (August state track, form 4 — track COMPLETE)
*Ken picked GA-700 + PTET as the next thread (AskUserQuestion). 1st partnership-entity state spec; GA600S
(S-corp, load_remaining_1120s.py) is the closest GA entity precedent. Clear of the parallel session
(explicit-path commits).*
- **Research (subagent, verbatim from the FINAL 2025 GA DOR sources — Form 700 Rev. 09/11/25; IT-711
  booklet; HB 149 PTET FAQ; Reg. 560-7-3-.03):** flat/PTET rate **5.19%** (2025; 2026→4.99%); PTET (HB 149)
  = annual irrevocable page-1 election, entity-level base (federal taxable income → §48-7-27 → §48-7-31
  apportionment, NOT a resident/nonresident split) × 5.19%; owners exclude via **PTEDED/PTEADD** on Form
  500, no owner credit, credits/NOLs stay with the entity. **Single gross-receipts apportionment** (6
  decimals, since 2008). GA decouples from §168(k)/OBBBA — add back federal depr (Sch 5 L7), subtract GA
  Form 4562 depr (Sch 6 L4); **GA §179 $1.05M/$2.62M**. **4% nonresident withholding** (<$1,000 exempt,
  G-2-A; displaced by PTET). Partnerships exempt from GA net worth tax.
- **Caught two stale values in the existing GA600S loader** (research cross-check): PTET rate **5.49%**
  (should be 5.19%) and **"property/payroll/sales" 3-factor** apportionment (GA is single-factor). GA700
  pins the correct values; GA600S correction logged to DECISIONS D-8 + the 1120-S delta audit.
- **Source brief** `ga700_source_brief.md` + **scope walk** (4 AskUserQuestion, all maximal — DECISIONS
  **D-8**): A full PTET compute; B compute the §179 delta + structure, direct-entry the GA-4562 figures;
  C compute Sch 4 partner allocation + 4% NRW; D direct-entry Sch 10 credits, RED-defer NOL/composite/UET.
- **Authored `load_ga700.py`** (SC1040/NC-D400 pattern). **Validated on throwaway SQLite** via
  `scratchpad/validate_ga.py` (CharField caps clean; all 11 rules cited). **Review walk (W1-W6)** — Jan 1
  2024 conformity (re-verify the 2025 bill), 5.19% rate (+5.75% reg quirk in the RED-deferred UET),
  entity-level PTET base, §179 figures, single-factor apportionment, Sch 4 partner model — all blessed.
  Ken: "Approve — flip, seed, export."
- **SEEDED + EXPORTED:** prod **92 → 93 TaxForms / 436 → 441 FlowAssertions** (+GA700, draft, entity
  ['1065']); `lookup/GA700/export/` = **HTTP 200** (verified live). 22 facts / 11 rules / 20 lines / 10
  diag / 7 tests / 5 FA; 5 GA sources. **The August state track (SC1040/AL-40/NC-D400/GA-700) is COMPLETE.**
  Next: the 1120-S delta audit (incl. the GA600S 5.49%/3-factor correction).

## 2026-07-04 — RS spec cleanup handoff (5 forms brought to parity with tts builds)
*Carried "RS follow-ups" from tts STATUS (twelfth session): tts code is already correct/self-consistent;
this session brought the RS SPECS + the re-exported tts spec mirrors into parity. Ground rules: amend the
HOME loader's data lists + re-run (reconstructable), keep id fields ≤ 20 chars, extend the enumerated
lists. Item 6 (3800 J4 §6417/§6418) = NO ACTION (documented intentional divergence). Clear of the
parallel session (explicit-path commits).*
- **Item 1 — FORM_8911 (Form 3800 now built).** Retired D_8911_004 (FormDiagnostic has no is_active field
  → severity error→info + RETIRED reword, the RS equivalent of tts is_active=False); repointed
  FA-1040-8911-04 from the gating red_fires check to the new flow_check (line 3 → 3800 Part III row 1s →
  Sch 3 line 6a after §38(c)); rewrote R-8911-SCHA-BUS + line 3 + fact notes + metadata + topic + docstring
  from "unbuilt/RED-deferred" to the built flow; dropped the now-retired D_8911_004:True from scenarios
  8911-T6/T7. Historical 2026-07-02 review-walk records left intact. Reseeded; export 200. Commit 14c7b5d.
- **Item 2 — 8936 / 8936_SCHA.** Extended D_8936_004 (on 8936_SCHA) from blank-VIN/PIS to also fire on a
  PIS date not in the return tax year (PIS-year credit); added R-8936-TRANSFER (FORM_8936, cited) — a
  qualifying dealer-transferred credit was received at POS, stops on Sch A (8c/8d/13b/13c), never re-lands
  on Sch 3, only a DENIED transfer repays (Sch 2 1b/1c); + D_8936_008 info + FA-1040-8936-06 (RS home for
  the transfer-STOP). Reseeded; exports 200; FA 435→436. Commit 0deee03.
- **Item 3 — 8949 (via load_1040_schedule_d).** Added D_8949_006 (error) — imported/YELLOW Exception-2
  summary rows start unconfirmed and must be preparer-reviewed pre-file (manual/GREEN untouched) + the
  grounding fact ct_import_confirmed (mirrors tts CapitalTransaction.import_confirmed, mig 0160). The
  loader's retire-stale prune keeps both. Reseeded; export 200. Commit 39dbb10.
- **Item 4 — SCHEDULE_A.** Added scha_qualified_contributions_cash — input-only, drives the line-11
  dotted annotation + the e-file qualifiedContributionsAmt attribute, affects no computed line (tts mig
  0159). Reseeded; export 200. Commit 30f73ff.
- **Item 5 — 8995 (via load_1040_schedule_c).** Recorded D_8995_001's retirement (8995-A now computes
  every above-threshold + patron return): severity error→info + RETIRED-DORMANT reword; R-8995-SCOPE
  formula/description + docstring + FA-1040-8995-03 from RED-defer → routes to the COMPUTED 8995-A;
  scenario 8995-T5 expected D_8995_001 True→False. Reseeded; export 200. Commit 5647024.
- **tts spec mirrors REFRESHED + COMMITTED + PUSHED** (tts 2ab9dae): re-exported 8911_spec / 8936_spec /
  8936_scha_spec / 8949_spec / schedule_a_spec / 8995_spec into tts-tax-app/server/specs/, format matched
  per file (5 compact from the RS endpoint; 8949 is indent=1/CRLF — regenerated to match, clean 23+/5− diff).
- **DEFERRED to a tts session (flagged, not done):** (1) tts `flow_assertions_1040.json` FA gate reconcile
  (FA-1040-8911-04 update + FA-1040-8936-06 insert) — the file is CRLF/no-trailing-newline/hand-managed
  (its assertion_count already drifts from length) and feeds test_flow_assertions.py; the FA HOME (the RS
  loaders) is updated + committed, so the tts session should regenerate it with its own tooling. Also the
  duplicate `form_8949_spec.json` (export_rule_studio.py 1120-S tool, pretty). (2) Run the tts test suite
  to reconcile any paired seed-leg/diagnostic-count assertions (tts owns the suite + the DB-collision
  playbook). Note: RS FA-1040-8936-05 = "unused personal LOST" (matches tts -05); the transfer STOP is the
  new -06 (the handoff's "-05 pins it" was imprecise).

## 2026-07-04 — NC D-400 AUTHORED + SEEDED + EXPORTED (August state track, form 3)
*Ken: "next up." 4th state individual spec (GA-500/SC1040/AL-40 precedents). NC starts from FEDERAL AGI
(like GA-500) at a FLAT 4.25% rate — simpler than AL; complexity is the Schedule S depreciation add-back
(Ken's specialty) + the child-deduction table. Clear of the parallel session (explicit-path commits).*
- **Research (subagent, verbatim from the FINAL 2025 NCDOR PDFs — Form D-400 + Schedule S rev "Web-Fill
  9-25"; D-401 booklet 2025; cited §105-153.5/.6/.7):** flat **4.25%** (0.0425; TY2026→3.99%); std ded
  $12,750/$25,500/$19,125 (MFS $0 if spouse itemizes; no 65+/blind add-on); federal-AGI start (L6) →
  Sch S Part A additions (L7) / Part B deductions (L9) → child deduction (AGI table $3,000→$0) + std/
  itemized → NC taxable income (L14) → flat tax. **Depreciation:** NC decoupled — add back **85%** of
  federal bonus (Part A L3) + 85% of the §179 excess over NC's **$25k/$200k** limits (L4); 20% recovery
  over 5 years (L23/24 reference 2020-24 add-backs). Conformity frozen **Jan 1 2023** (OBBBA not adopted).
- **Source brief** `nc_d400_source_brief.md` + **scope walk** (4 AskUserQuestion, all maximal — DECISIONS
  **D-7**): A resident + **Schedule PN** proration (L13→L14); B **COMPUTE** the current-year 85% bonus +
  85% §179-excess add-back, direct-entry the prior-year 20% installments (the $200k §179 phaseout is a
  diagnostic, not silently computed); C **structured** Part B subtractions (L18 US-obligation / L19 SS-RR
  / L20 Bailey / L21 military) with eligibility diagnostics; D direct-entry D-400TC/use-tax/contributions,
  RED-defer Schedule PN-1 / amended lines / L26e underpayment / L39 NC NOL.
- **Authored `load_nc_d400.py`** (AL-40/SC1040 pattern). **Validated on throwaway SQLite** via a reusable
  `scratchpad/validate_nc.py` harness that ALSO enforces the Postgres CharField caps SQLite ignores — it
  **CAUGHT `D_NCD400_179_PHASEOUT`=21 > the 20-char `diagnostic_id` cap** pre-seed (shortened to
  `D_NCD400_179LIMIT`), and flagged 3 pure-arithmetic rules with no authority link (grounded them to the
  D-400 face). **Review walk (W1-W6)** — flat rate, 85% add-back + limits, Jan-1-2023 conformity, std
  ded, child table, statute-provenance — all blessed. Ken: "Approve — flip, seed, export."
- **SEEDED + EXPORTED:** prod **91 → 92 TaxForms / 431 → 435 FlowAssertions** (+NC_D400, draft);
  `lookup/NC_D400/export/` = **HTTP 200** (verified live). 29 facts / 11 rules / 21 lines / 8 diag /
  8 tests / 4 flow assertions; 6 sources (5 NC + federal 1040), every rule cited. Next state form: GA-700 + PTET.

## 2026-07-04 — AL Form 40 AUTHORED + SEEDED + EXPORTED (August state track, form 2)
*Ken: "kick off AL Form 40." 3rd state individual spec (GA-500/SC1040 precedents). The checklist
flagged AL's federal-income-tax-deduction quirk as "the longest walk." Clear of the parallel session.*
- **Research (subagent, verbatim from the FINAL 2025 AL DOR PDFs — Form 40 25f40blk, booklet 25f40bk
  incl. the p.31 FIT worksheet + p.8 std-ded chart, §40-18-5/§40-18-15):** AL builds gross income FROM
  SCRATCH (no federal-AGI start; wages from AL Sch W-2). THE QUIRK = federal income tax deduction (L12)
  = (1040 L22 + NIIT 8960 L17) − refundable credits (EIC/ACTC/AOC/refundable adoption/2439), floored 0,
  apportioned AL-AGI/federal-AGI for part-year. 2/4/5% rate; sliding-scale std deduction + dependent
  exemption ($1000/$500/$300); §414(j)/SS/govt-pension fully excluded (no age-65 exclusion).
- **Source brief** `al_form40_source_brief.md` + **scope walk** (4 AskUserQuestion, all recommended):
  A Form 40 (full + part-year) only, 40NR RED-defer; B COMPUTE the full FIT worksheet + PY apportionment;
  C compute the AGI-keyed sliding scales; D direct-entry Schedule OC, RED-defer ATP/40NR/NOL.
- **Authored `load_al_form40.py`** (SC1040/GA-500 pattern). **Review walk (W1-W5):** all handleable
  (no blocking figure) — W1 std-ded encoded as a FORMULA (sidesteps the OCR-suspect MFJ cell, verified
  at several AGI points); W2 rate via §40-18-5 + tax-table-confirmed; W3 FIT worksheet basis (§40-18-15
  cited); W4 federal handoff; W5 OC caps / 40NR deferred. Ken: "seed + export now" → flipped guard.
- **SEEDED + EXPORTED:** prod **90 → 91 TaxForms** (+AL_FORM_40, draft); `lookup/AL_FORM_40/export/` =
  **HTTP 200** (verified live). 22 facts / 9 rules / 20 lines / 6 diag / 5 tests / 4 flow assertions;
  4 cited AL DOR sources. Commits 1fe6955 (author) + 807af4f (seed/export). Next state form: NC D-400.

## 2026-07-04 — SC1040 + Schedule NR AUTHORED + SEEDED + EXPORTED (August state track, form 1)
*Ken: "august." First August RS state item ("SC1040 — CC drafts, Ken walks — GA-500 pattern").
2nd state individual spec (GA-500 is the precedent). Clear of the parallel S3/S4 federal work.*
- **Two research passes (subagents, verbatim from FINAL 2025 SC DOR PDFs):** (1) SC1040 line map +
  the TY2025 rate (6%, down from 6.4%; 3 brackets 0/3/6% at $3,560/$17,830; $642 rate-sched constant),
  additions/subtractions, credits, dependent exemption $4,930; (2) Schedule NR (Col A/B, line-45
  proration, L48→SC1040 L5) + SC depreciation conformity (IRC through 12/31/2024 per Act 63/S.507;
  SC did NOT adopt OBBBA; §168(k) bonus add-back line e / line v verbatim; §179 conforms at pre-OBBBA).
- **Source brief** `sc1040_source_brief.md` + **scope walk** (4 AskUserQuestion, MAXIMAL, DECISIONS
  D-6): A full resident + Schedule NR; B COMPUTE the §168(k) add-back (Ken's depreciation-CPA call,
  diverges from GA-500 direct-entry); C compute the retirement/military/age-65 stack; D RED-defer
  I-335/SC4972/catastrophe, direct-entry SC1040TC.
- **Authored `load_sc1040.py`** (GA-500 pattern; READY_TO_SEED guard). **Review walk (W1-W5):** W1
  §179 — Ken chose COMPUTE + confirmed the pre-OBBBA figures **$1,250,000 / $3,130,000** (Rev. Proc.
  2024-40; SC's 12/31/2024 conformity) → added R-SC-179-ADDBACK (phaseout-aware excess → line e);
  W2-W5 blessed as in-spec re-verify flags. Flipped READY_TO_SEED=True.
- **Caught a Postgres-only bug:** AuthorityTopic.topic_name >255 (SQLite didn't enforce; the atomic
  txn rolled back clean). Shortened → re-seeded.
- **SEEDED + EXPORTED:** prod **88 → 90 TaxForms** (+SC1040 +SC_SCHEDULE_NR, draft status); both
  `lookup/{SC1040,SC_SCHEDULE_NR}/export/` = **HTTP 200** (verified live). SC1040: 32 facts / 15 rules
  / 27 lines / 6 diag / 8 tests; Sch NR: 5/4/9/1/2; 5 flow assertions; 6 cited SC DOR sources.
  Commits a588cc8 (author) + 2fdbc06 (W1 + seed/export). Next August state form: AL Form 40.

## 2026-07-04 — draft→approved workflow: source-controlled approval + first batch (1065-core 7)
*Ken: "the next item, but there's a parallel session so let's not step on it." Next July item =
"begin draft→approved workflow." Stayed clear of the parallel S3/S4 loader work (8835/8936/4835);
used explicit-path commits, not `git add -A` (the 8835-sweep lesson).*
- **State found:** `TaxForm.status` (draft/review/approved/archived) already exists + surfaces in
  serializers/views/export/admin; loaders leave the default → **all 88 forms `draft`** (never exercised).
  No model/migration change (zero collision risk).
- **Design (DECISIONS D-5):** approval is **source-controlled**, reproducible — NOT a DB edit (that
  vanishes on `seed_all` rebuild = the "lives only in Supabase" anti-pattern the recon check cleaned up).
  Built `specs/approved_specs.py` (`APPROVED_FORMS` manifest) + `approve_specs` command (draft/review→
  approved; reports drift both ways) + wired as **`seed_all` phase 5**. (commit `00e6432`)
- **First batch (Ken: "1065-core batch (7)"):** approved 1065_PAGE1, SCH_K_1065, SCHEDULE_K1_1065,
  1065_M1, 1065_M2, 1065_L, 1065_B → prod now **7 approved / 81 draft**. Held 1065_SE (case-law
  requires_human_review) + the in-flight S3/S4 forms. **Verified reconstructable:** a fresh `seed_all`
  restores exactly those 7 approvals via phase 5. (commit `4a5508b`)

## 2026-07-04 — Form 8835 loader homes for the J2/J3/J4 RED-defers + 2 FAs (the S4 arc; the tts session)
- `load_1040_form_8835.py` AMENDED (amend-by-lookup, `update_or_create` — the fa-needs-rs-loader-home
  rule; the 8936 R-8936-TRANSFER precedent). Added the four scope-walk RED-defer diagnostics that the
  tts 8835 unit built this session (Ken's 2026-07-04 J2/J3/J4 rulings + the missing-PIS gap): **D_8835_005**
  mixed 1f/4e routing (whole feed withheld), **D_8835_006** straddle window (facility feed withheld),
  **D_8835_007** passthrough with no PIS date (feed withheld), **D_8835_008** producing facility missing
  its PIS date (excluded). All severity=error, ≤20 chars, bridge-gated in tts on `form_8835_state`; escape
  hatch = the Form 3800 1zz/4z direct entries. Added **FA-1040-8835-05** (the J2/J3/J4 routing gating_check,
  pins the rulings) + **FA-1040-8835-06** (the constants_check — 2025 rate tiers / OBBBA cutoff / ×5 / 10% /
  15% bond cap / 90% EPE / 4-yr window; 2026 NOT pinned). Both transcribed verbatim from the tts gate file
  (the canonical set per Ken's 2026-07-01 "tts file stays canonical" ruling).
- SEEDED to RS Supabase: 8835 now 9 diagnostics (was 5) + 6 flow assertions (was 4); all rules keep authority
  links. DB totals: FlowAssertions 422, FormDiagnostics 533.
- ⏳ Cached tts `server/specs/8835_spec.json` refresh + deployed-export id-level verify FOLLOW the RS Render
  redeploy (this push). tts gate file (`flow_assertions_1040.json`, FA-1040-8835-01..06) is canonical and
  already green (flow gate 397). No id drift expected — the loader block is a verbatim transcription.

---

## 2026-07-04 — RS DB reconstructability check + `seed_all` orchestrator
*Ken picked this July checklist item after the 1065-core close. "fresh DB + all loaders + diff vs
production; if anything lives only in Supabase → fix now."*
- **Method:** throwaway SQLite DB (`DATABASE_URL=sqlite://…`, guarded), ran every loader, diffed the
  rebuilt DB vs production Supabase on form set + per-form rule_ids + all 11 entity-model counts.
- **Found — deploy pipeline gap:** `build.sh` runs only `seed_sources` (feeds + topics). The 89 forms,
  299 authority sources, and 420 flow assertions are ALL seeded by loaders deployment never runs → prod
  was populated by running loaders manually, never verified rebuildable. There was **no orchestrator**.
- **Fixed (code, zero prod risk):** `specs/management/commands/seed_all.py` — sources → specs `load_*`
  → amends → flow assertions, dynamic loader discovery + explicit amends list. Fresh-DB run = **61/61
  loaders, 0 problems**. `--dry-run` prints the plan. Closes the one hard break: `load_1040_form_3800`
  is an amend loader that raised `CommandError` when run (alphabetically) before its 1120-S base 3800
  existed; amends-last → 3800 rebuilds to the full 12 rules.
- **4 residual drifts — logged for Ken (all prod-data changes, NOT touched this session):**
  (A) orphaned legacy rules no loader reproduces — `4797` R001-R008/R010, `SCH_K_1120S` R010-R018,
  `SCHD_1120S` R010-R012 (loaders refactored to new rule_ids; prod never cleaned); (B) prod stale vs
  loaders — `8283`/`8949`/`8995`/`8995A` (re-seed, additive); (C) `1065` empty stub (entity=[], 0 rules,
  mislabeled "1065_SE") lives only in DB; (D) `FORM_8582` vs the loader's bare `8582`. **Authority
  sources reproduce EXACTLY (0 delta).** Full writeup + remediation order → `reconstructability_check.md`.
- **Supersession investigation (Ken chose "investigate orphans first", read-only content diff):**
  `4797` orphans R001-R010 = SUPERSEDED (pre-refactor naive rules; R007 hardcodes §1250 recap = 0, the
  exact bug the nuance leg fixed) → safe to delete. But `SCH_K_1120S` R010-R018 + `SCHD_1120S` R010-R012
  = **NOT superseded** — they encode line-level detail (interest, dividends, meals, distributions, K18
  reconciliation) the current 1120-S loader DROPPED → a loader regression; **do NOT delete, fold into
  the August 1120-S delta audit.** Recorded in `reconstructability_check.md` §A + STATUS Known-issues.
- **Prod remediation executed (Ken: "do all safe items"), snapshot-backed + transactional:** deleted
  the 9 confirmed-superseded `4797` orphan rules (+13 cascaded authority links) and the `1065` empty stub
  (+2 cascaded FormLines) → prod **89 → 88 TaxForms**, 420 FA intact; 4797 + 1065 now 0-delta vs the
  rebuild, **authority sources 0-delta**. **CAUGHT MY OWN MISDIAGNOSIS:** an initial `FORM_8582`→`8582`
  rename was executed, then the re-diff showed the rebuild produces BOTH `FORM_8582` (the real passive-loss
  form, 12 rules, referenced by 4835) AND a spurious bare `8582` from `load_1120s_complete` — so I
  **reverted** the rename immediately (FORM_8582 restored, 12 rules). Investigation also found the four
  "stale" forms EXACTLY match their 1040 primary loaders — the extra rules come from `load_1120s_complete/
  specs`, so item B is 1120-S-loader-entangled too. **All residual drift now traces to the 1120-S loader
  family → deferred to the August 1120-S delta audit** (stale rule sets, SCH_K/SCHD orphans + dropped line
  detail, spurious bare-8582 duplicate). No fresh authoring; report/STATUS corrected. `seed_all` + report
  committed; the prod deletes are live in Supabase.

## 2026-07-04 — 1065 core campaign CLOSED: forms 5 & 6 (8825/4562/3800) coverage confirmed
*Ken: "check the status and continue." STATUS's IMMEDIATE NEXT was: confirm 8825/4562/3800 cover 1065
(likely no fresh authoring). Verified against the LIVE RS DB — not just the brief table.*
- **Entity coverage (live DB query):** `3800` = `['1120S','1065','1120','1040']`, `4562` =
  `['1120S','1065','1120','1040']`, `8825` = `['1120S','1065']` — all three carry `1065`.
- **Routing wiring confirmed (not just tags):** `4562` R004 "§179 flows to Schedule K (not Page 1)"
  (the 1065/1120S §179 pass-through) + R014 line-12 §179; `8825` R003 "Total net rental → K Line 2"
  (the exact 1065 Sch K line 2 handoff); `3800` = 12 rules, entity-agnostic GBC aggregation driven by
  the entity tag. So forms 5 & 6 are genuinely wired for 1065, not merely tagged.
- **Verdict: no fresh authoring.** The 1065-core campaign is COMPLETE — 6/6 forms covered (4 fresh-
  authored this week: spine `1065_PAGE1`+`SCH_K_1065`, K-1 `SCHEDULE_K1_1065`, M-1/M-2 `1065_M1`/`1065_M2`,
  L/B `1065_L`/`1065_B`; + 3 pre-existing multi-entity 8825/4562/3800). RS side CLOSED. No DB change this
  session (verification only) → still **89 TaxForms / 420 FlowAssertions**.
- **Still open (tts-side, NOT RS blockers):** (1) page-1 off-by-one field numbering (tts internal
  deductions="21"/ordinary="22" vs face 22/23); (2) 1065 Analysis-of-Net-Income build-gap (`R-SCHK-ANALYSIS`
  new; ties M-1 line 9 / M-2 line 3 — tts `task_4bf72675`); (3) item-L capital roll-forward (M-2 line 1);
  (4) the 5 Sch L/B build-gaps logged in `1065_core_reconcile_log.md`; (5) optional box-9c DB stamp
  (`test_4797_pipeline_leg.py`). All drive tts-side from the exports.

## 2026-07-04 — 1065 core form 4: Schedule L + Schedule B authored + SEEDED + EXPORTED
*Ken: "continue the 1065-core campaign — form 4 (Schedule L + Schedule B)." Fresh-authored per D-1.*
- **Sourced verbatim** off the FINAL 2025 f1065.pdf (re-downloaded; page 6 = Schedule L, pages 2-4 =
  Schedule B's 33 questions; pymupdf) — confirmed the brief §4.3/§4.1 transcription. Primary IRC fetched
  verbatim off Cornell LII: §754 (Q10 election), §448(c) (the $25M base → $31M inflation-adjusted behind
  Q24 §163(j)), §6221(b) (Q33 audit election out); §705 re-used (L21↔M-2 tax-basis tie).
- **D-1 reconcile** (Explore agent, read-only tts survey): `compute.py` Sch L totals (~L313-329) +
  `compute_schedule_l()` (DepreciationAsset EOY roll-forward) + `seed_1065.py` B1-B18. **9 items logged**
  (`1065_core_reconcile_log.md` L/B section): 2 MATCH (L-totals arithmetic; tts's 9b/12b EOY roll-forward
  is AHEAD), **5 tts build-gaps caught** — (L3) no balance check; (B1) Q4 gate stored-but-not-enforced;
  (B2) no $31M/M-3 threshold; (L4) L21↔M-2 unreconciled; (L2/B3) **tts Sch L numbered L1-L24 offset one
  from the 2025 face** (splits 7a/7b, 19a/19b) + **tts Sch B condensed to 18 questions vs the face's 33**.
- **Scope walk (AskUserQuestion, 4 calls, all approved):** D = author RS to the 2025 face (log the tts
  L1-L24 remap as a build item); **E = §754/§743(b)/§734(b) basis-adjustment MATH RED-defer** (structure +
  cited authority + flag only; Ken's basis-specialty call); F = Schedule M-3 + B-1/B-2/B-3 RED-defer
  (threshold flag + attachment triggers); G = full a/b Sch L sub-lines. → "flip seed export."
- **Authored `load_1065_l_b.py`** (READY_TO_SEED=False → flipped True post-walk): `1065_L` (59 facts / 6
  rules R-L-14/22/BALANCE/21-TIE/EXEMPT/M3 / 28 lines / 5 diag / 5 scenarios) + `1065_B` (51 facts / 5
  rules R-B4-SMALL/B24-8990/B10-754/B33-PR/B30-DIGITAL / 32 lines / 5 diag / 5 scenarios) + 4 flow
  assertions (GATE-SMALL-PTNR-B, RECON-L-BALANCE, RECON-L21-M2, GATE-8990-163J). All rules cited. 6
  authority sources (IRC_705/754/448C/6221 + F1065/I1065 face). Load-bearing computed gates: R-B4-SMALL
  (Q4 all-four → `m_schb_q4_small` suppresses L/M-1/M-2/item F/K-1 item L) + R-B24-8990 (Q24 §163(j) $31M).
- **Seeded + exported:** → **89 TaxForms / 420 FlowAssertions**; both `lookup/{1065_L,1065_B}/export/`
  = HTTP 200 (verified live on 127.0.0.1:8137); exports/form_1065_l/ (48 KB) + form_1065_b/ (51 KB),
  all load-bearing rules + verbatim excerpts present. The 6 fresh 1065-core forms are DONE; 8825/4562/3800
  already cover 1065 → campaign near-complete.

## 2026-07-04 — Form 3800 1040-side AMENDMENT authored + SEEDED (the S4 arc; the tts session)
*Ken: "should you go ahead and build the 3800?" → spec-first. The deployed 3800 spec was the
1120-S-era draft (10-line generic sketch, K-1-box-13 routing — unusable for the 1040/S4 build).*
- **Scope walk (AskUserQuestion, 4 rulings LOCKED, all recommended):** J1 Part III rows = built
  feeders (1f/4e 8835 · 1s 8911 · 1y/1aa 8936) + 1zz/4z catch-alls; J2 passive = per-inflow
  nullable assertion (None → EXCLUDED + D_3800_002 RED; True → col (d) + D_3800_003 RED with the
  line-3/33 escape hatches — 8582-CR manual); J3 carryforward = two direct-entry in-buckets
  (line 4 regular / line 34 specified) + computed CF-out (D_3800_005 + statement; the Part IV
  FIFO grid deferred to the proforma track); J4 §6417/§6418 OUT (D_3800_004 RED).
- **Review walk (W1-W4 approved):** W1 the stale-grid replacement (deleted 1a/1b/1c, overwrote
  2-7/38 with the 2025 face; entity rules R001-R003 KEPT, R004 refreshed in place); W2
  unanswered-passive-excludes; W3 the line-10b list (= the Form 8911 line-6b Ken-approved
  ordering reading, i3800 verbatim); W4 the S4 all-carries outcome (the 8936 personal credit
  absorbs the ~$2,193 tax first via 10b → line 11 = 0 → the ENTIRE $13,200 specified 8835
  credit carries forward, Sch 3 6a blank — F3800-S4 pins it).
- **Authored `load_1040_form_3800.py`** — AMEND-BY-LOOKUP (never creates; preserves
  entity_types ["1120S","1065","1120","1040"]): +13 facts / +8 rules (R-3800-P3-INFLOW/
  P3-TOTALS/P1/P2-TAXLIM/P2-SECB/P2-SECC/ALLOWED/CF-OUT) / 42 face lines (Part III P3-prefixed;
  P3-4e is the S4 row) / +6 diagnostics (D_3800_001-006) / +6 tests (F3800-S4 + T2-T6 incl. the
  T3-vs-T4 §38(c)(4)(A) TMT-zeroing pair) / +5 FAs (FA-1040-3800-01..05). Authority: NEW
  IRS_2025_3800_FORM (9-page 2025 face, sha256 cdfb169a…, verbatim Part I/II/III excerpts);
  NEW excerpts on the EXISTING IRS_2025_3800_INSTR (the 10b list; carryover ordering) + IRC_38
  (§38(c)(4)(A)-(B) verbatim incl. clause (iv)'s 4-year §45 window — fetched off LII).
- **Seeded + verified:** loader run (3 stale lines deleted; totals: forms 84 / rules 726 /
  FAs 409; all 3800 rules cited); deployed export re-fetched 200 — entity_types preserved,
  rules R001-R004 + R-3800-* both present, stale lines gone, line 38 dest SCH_3.6a. Canonical
  `3800_spec.json` cached in tts.
- **Also this session (tts-side):** the FA-1040-8936-01..05 id collision found + fixed — my tts
  gate entries had reused the ids this repo's `load_1040_form_8936.py` had already authored and
  seeded; the tts gate file now carries the RS-canonical five verbatim (extras folded into the
  runners; 5/5 green). NEXT: the tts 3800 unit build (retires D_8911_004, softens D_8936_003),
  then 8835, then the S4 scenario.

---

## 2026-07-04 — 1065 core form 3: Schedule M-1 + M-2 (1065_M1 / 1065_M2) SEEDED + EXPORTED
*Ken: "parallel session is working on 3800, you can start on something different" → form 3; walk (M2_3 + seed).*
- **Authored** `load_1065_m1_m2.py` (two forms) from the FINAL 2025 **f1065 page 6** — downloaded f1065.pdf
  (334 KB) + extracted pp. 5-6 via pymupdf (verbatim M-1/M-2 line maps; page-6 also has Schedule L for form
  4). M-1: 5 = Σ(1-4), 8 = Σ(6-7), **9 = 5−8 = Analysis of Net Income line 1** (face literally labels it so —
  validates the spine's R-SCHK-ANALYSIS). M-2 (tax basis, §705): 5 = Σ(1-4), 8 = Σ(6-7), 9 = 5−8; line 3 =
  Analysis line 1 = M-1 line 9. Primary IRC §705(a)/§702 reused verbatim; f1065 p.6 + i1065 as filing
  authority. All rules cited.
- **Reconcile vs tts `FORMULAS_1065` M-1/M-2 (5 findings):** (1) 🔴 **M2_3 mis-source** — tts labels line 3
  "Net income (loss) per books" + free data-entry (`compute.py` M2_5 sums it raw); the FINAL face line 3 =
  "(see instructions)" = Analysis line 1 on the post-2020 **tax-basis** M-2. Ken: **"log + spawn a tts task"**
  → `spawn_task` `task_4bf72675` (coupled to the unbuilt 1065 Analysis compute + M-1 line 9; the RS spec
  stays correct per current law). (2) M1_9 ties to Analysis line 1 which tts doesn't compute (spine gap #6).
  (3) M2_1 = Σ K-1 item-L begin capital but item-L roll-forward is RED-deferred (K-1 leg) → data-entry.
  (4) tts adds catch-all M1_4c/M1_7b not on the face (benign). (5) Sch B Q4 small-partnership exemption →
  gating fact (shared with L/K-1 item L).
- **Seed + export:** hit a varchar(20) cap on a flow-assertion id (`GATE-SMALL-PARTNERSHIP` = 22 chars →
  atomic rollback, no partial seed) → renamed `GATE-SMALL-PTNR`, re-seeded clean. 1065_M1 (5 rules / 11
  facts / 10 lines / 2 diag / 3 scenarios) + 1065_M2 (6 rules / 12 facts / 11 lines / 3 diag / 3 scenarios)
  + 3 flow assertions, all cited → **87 TaxForms / 416 FlowAssertions**. Both `lookup/{1065_M1,1065_M2}/
  export/` = **HTTP 200** (exports/form_1065_m1/ + form_1065_m2/, ~32 KB each). Committed `0184c0a` (author)
  + this seed. **Form 3 of 6 DONE. Next: form 4 — Schedule L + Schedule B.**

---

## 2026-07-04 — 1065 core form 2: Schedule K-1 + allocation engine (SCHEDULE_K1_1065) SEEDED + EXPORTED
*Ken: "start it" → author form 2; walk (coded-box depth + flip); "full ~200-code transcription now" + "flip seed export".*
- **Reconcile-driven authoring.** Explore agent mapped tts `k1_allocator.py` + `compute_schedule_k1.py`
  read-only. Encoded: per-partner box = entity Sch K line × `profit_pct` (≥0) / `loss_pct` (<0), overridable
  per-category by `PartnerAllocation` (Lacerte special allocations); GP (4a/b/c) + distributions (19a) DIRECT
  per-partner; box 9c = LT_CAPITAL/`profit_pct` (reads K9c → writes box 9c) — **CONFIRMED, closes the box-9c
  pass-through** (RECON-9C: 80k @ 60/40 → 48k/32k); box 14a = the `1065_SE` spec (cross-ref).
- **RED-deferred (Decision C; engine absent):** §704(c) built-in gain (items M/N → D_K1_704C), §704(b) SEE
  (D_K1_SPECIAL_ALLOC), §706(d) varying interest (D_K1_706D), item-L capital roll-forward (D_K1_ITEML — tts
  stores the fields but doesn't compute; **M-2 line 1 can't auto-derive** → M-2 leg). Gap logged: `capital_pct`
  defined but UNUSED by the allocator (D_K1_CAPPCT).
- **Authority:** primary IRC verbatim — §704(a)/(b), §706(d)(1), §752(a)/(b), §705(a) (Cornell LII this
  session); §702(b)/§707(c) reused. **FULL coded-box transcription (Ken decision):** downloaded the FINAL
  i1065sk1.pdf (445 KB, 36 pp), extracted pp. 33-36 "List of Codes" via pymupdf → boxes 11/13/14/15/17/18/19/20
  (every letter A-ZZ) encoded VERBATIM as 8 `IRS_2025_I1065SK1` AuthorityExcerpts (source-grounded, not
  recalled; they ride into the export). WebFetch mangles dense code tables → direct PDF extraction.
- **Seed + export:** READY_TO_SEED=True → SCHEDULE_K1_1065 (27 facts / 11 rules / 19 auth links / 17 lines /
  7 diag / 8 scenarios / 4 flow assertions, all cited) → 85 TaxForms. `lookup/SCHEDULE_K1_1065/export/` =
  **HTTP 200**, exports/form_schedule_k1_1065/ (80 KB; 8 code-list excerpts present). Committed `8673fdd`
  (author) + this seed. **Form 2 of 6 DONE. Next: form 3 — Schedule M-1 / M-2.**

---

## 2026-07-04 — 1065 core campaign KICKOFF: Schedule K spine SEEDED + EXPORTED (+ a tts bug fixed)
*Ken: "go" → author the first of 6 forms; walk (D-1); "dig into net-farm" → "fix now"; "flip seed export".*
- **SEED + EXPORT (Ken: "flip seed export"):** flipped `READY_TO_SEED=True`, ran `load_1065_schedule_k`
  → `1065_PAGE1` (27 facts / 7 rules / 32 lines / 3 diag / 4 scenarios) + `SCH_K_1065` (40 / 11 / 38 / 4 /
  7 + 4 flow assertions), all rules cited → RS **84 TaxForms / 404 FlowAssertions**. Exported via the real
  `form_lookup_export` view (APIRequestFactory): both `lookup/{1065_PAGE1,SCH_K_1065}/export/` = **HTTP 200**,
  saved to `exports/form_1065_page1/` + `exports/form_sch_k_1065/` (51 KB / 70 KB; line_map 32 / 38). Spine
  leg (form 1 of 6) DONE. **Next: form 2 — Schedule K-1 (Form 1065) + the allocation engine** (reconcile
  `k1_allocator` §704 math + `compute_schedule_k1` box map; transcribe the ~200 coded-box lists; close the
  box-9c pass-through).
- **Scope walk (AskUserQuestion, 3 decisions LOCKED):** A. K-2/K-3 international → **RED-defer** (box 16 =
  Schedule K-3-attached checkbox only + `D_SCHK_K3`); B. Schedule M-3 → **RED-defer** (belongs to the L/M
  leg; threshold gating fact there); C. §704(b)/(c) → **encode structure, defer math** (items J/K/L/M/N +
  %-alloc as facts + cited §704 authority + gating flags; special-allocation MATH deferred to tts
  `k1_allocator`; `D_SCHK_704C` surfaces item M/N). All three on the recommended calls.
- **Authored `specs/management/commands/load_1065_schedule_k.py`** (fresh, per D-1) — seeds TWO forms
  mirroring the 1120-S decomposition (`1120S_PAGE1` + `SCH_K_1120S`):
  - **`1065_PAGE1`** — Form 1065 page 1: income 1a-8 (1c=1a−1b; 3=1c−2 COGS←1125-A; 8=Σ3-7; L5←Sch F;
    L6←4797 PtII L17), deductions 9-22 (16c=16a−16b←4562; 22=Σ9-21), **ordinary business income
    line 23 = 8−22 → Sch K line 1** (the handoff, `R-1065P1-23`). 27 facts / 7 rules / 32 lines /
    3 diagnostics / 4 scenarios. ⚠ 2025 face: ordinary income is L23 (NOT 22).
  - **`SCH_K_1065`** — Schedule K distributive-share spine (Total-amount col) lines 1-21 + Analysis of
    Net Income line 1 = (Σ 1-11)−(Σ 12-13e+21). Line 1←page-1 L23; 3c=3a−3b; 4c=4a+4b; 9c←4797;
    14a=the `1065_SE` spec (cross-ref, not recomputed); line 16=K-3 checkbox (RED-defer). ~30 facts /
    11 rules / ~40 lines / 4 diagnostics / 7 scenarios. K→K-1 box map (`R-SCHK-KMAP`) + §704 allocation
    structure (`R-SCHK-ALLOC`) authored as routing rules (per-partner math = the K-1 leg).
  - Authority: **primary IRC quoted VERBATIM** — §702(a)/(a)(8)/(b), §703(a)/(b), §704(a)/(b) (fetched
    2026-07-04 off Cornell LII this session), §707(c) (reused from the vetted 1065_SE load); + FINAL-2025
    **f1065/i1065** line maps as filing authority (`IRS_2025_F1065`/`IRS_2025_I1065`, requires_human_review,
    from the brief §4.1/§4.2 verbatim transcription). 4 flow assertions (RECON-P1-K1, RECON-ANALYSIS,
    INV-K-CHARACTER, GATE-K2K3-DEFER). All rules cited.
- **Validation:** `py_compile` OK; the READY_TO_SEED=False refuse-to-seed guard fires clean ("all
  populated" — nothing hollow, held only on the sentinel). NOT seeded (awaits the walk per D-1).
- **D-1 reconcile survey** (read-only, tts `server/apps/returns/compute.py` entity Sch K block ~L240-298
  + `compute_schedule_k1.py`) → **`1065_core_reconcile_log.md`, 8 items:**
  - ✅ MATCH ×4 — page-1 L8=Σ(3-7) (`:240`); K3c=K3a−K3b (`:284`); K14a bottom-up SE (`:288-292`,
    reconciled this season); §179→K12 for 1065 (`:984`).
  - 🔨 BUILD-GAP ×1 — tts has **no 1065 Analysis of Net Income** compute (`K18` at `:120` is 1120-S income
    reconciliation only); `R-SCHK-ANALYSIS` is new → a tts build item (ties to M-1 L9 / M-2 L3, L/M leg).
  - ⚠ KEN ADJUDICATION ×3 — (a) page-1 **off-by-one field numbering**: tts internal deductions=field"21"
    (Σ9-20), ordinary=field"22"(8−21), K1←"22" vs the 2025 face 22/23 (arithmetic identical; map or
    renumber); (b) **net-farm routing** — tts routes Sch F net (F34)→**Sch K line 11** (`:287`), but the
    face puts net farm on **page-1 line 5**→ord income→K1 — Ken's farm/depreciation call (check
    double-count); (c) **box-9c pass-through** = the STILL-OPEN tts verification (STATUS Next-up).
- **Files:** `load_1065_schedule_k.py` (new), `1065_core_reconcile_log.md` (new), STATUS.md updated.
  Committed `bbe6913`; loader inert (READY_TO_SEED=False) until the walk.
- **🐛 CONFIRMED + FIXED a tts bug the reconcile caught (net-farm misroute).** Ken: "dig into the tts
  net-farm path to confirm double-count" → then "fix now in tts + add test." Traced via an Explore agent
  (which I corrected on one point — it claimed `F34=0` for 1065, conflating the inline `F34=F9−F33` formula
  in `FORMULAS_1065:278` with the 1040-only `compute_schedule_f_family`; verified `seed_1065` seeds the full
  enterable F-block, so `F34` IS computed inline). **Bug:** `FORMULAS_1065` routed `F34` → **Schedule K line
  11** (`compute.py:287`) instead of page-1 line 5 → K1. Two modes: (a) F-block only → farm on K11 not K1 →
  the 14a SE base (reads K1 only) omits it → **SE understatement**; (b) F-block + hand-entered line 5 →
  **double-count**. **Fix (tts `f61cfec`):** relocated the Schedule F block ahead of page-1 line 8; added
  `("5", F34)` so farm flows line 5 → 8 → 22 → **K1** (and the SE base); removed `K11←F34`; `seed_1065` line 5
  `is_computed=True` (YELLOW). Pure-Python sim confirmed routing; `TestNetFarmRouting` (3 tests) **3/3 green**
  over the shared test DB (one AdminShutdown blip re-ran clean, per `tts-test-db-collisions`). **Committed
  INDEX-ONLY** — the parallel S3/S4 session has heavy uncommitted 8936 work in the same `compute.py` (+ models/
  views/serializers/migrations); staged only my FORMULAS_1065 hunks via a filtered patch (`git apply --cached`)
  + the 2 mine-only files, leaving their WIP untouched. Pushed clean (`962be0a..f61cfec`, fast-forward).

---

## 2026-07-04 — Between-session prep: S3/S4 integrity checker + 1065-core source brief (pre-scout for the July campaign)
*Independent RS work while the parallel tts session builds S3/S4 — zero collision.*
- **`check_s3s4_integrity.py`** (committed `a73d424`): pre-seed math+structure gate for 4835/8835/8936/
  8936_SCHA — independent re-derivation of every test-vector's arithmetic (constants re-typed, not
  imported) + id<=20 / all-cited / fact-key-input / no-dupe gates + constants cross-check. **390 checks,
  all green.** Also verified the DEPLOYED Render endpoints match the local seed exactly (4835/8835/8936/
  8936_SCHA — rules/facts/line_map counts identical; the tts consuming contract is live, not just local).
- **`1065_core_source_brief.md`** (this commit): pre-scouted the NEXT campaign (July 1065 core). Gap map
  (6 forms to author fresh — Sch K, K-1+allocation, M-1/M-2, L, B; 8825/4562/3800 already cover 1065),
  the D-1 reconcile targets in tts (`k1_allocator.py` / `compute_schedule_k1.py` / `compute_1065_se.py`,
  read-only survey), and **§4 verbatim FINAL-2025 line maps** (3 research agents read f1065/f1065sk1/
  i1065/i1065sk1 directly): page-1 (ord. income = line 23; tax/pmt 24-32; new direct-deposit 32b-d) +
  Schedule B (33 Qs; Q4 L/M exemption receipts<$250k & assets<$1M; Q10 §754; Q23/24 §163(j) $31M) +
  Schedule K (1-21 + Analysis) + K-1 (Part II items J/K/L/M/N, Part III 1-23) + the K→K-1 coded-box
  mapping + K-2/K-3 split + OBBBA What's New (§174A R&E, §181 box-13 X, §1062 box-20 ZZ). Cross-tie: K-1
  box-15 credit codes AY/AZ/AB carry the 8936/8835 credits I specced this session. NOT authorized to
  seed — D-1 fresh-author + Ken walk when the campaign opens.

## 2026-07-04 — S3/S4 unblock campaign: 8835 + 8936 + Schedule A(8936) authored/seeded/exported; 4835 reconciled — ALL FOUR endpoints 200
*Ken's campaign prompt (from a tts Claude): author the four missing specs so the tax app can build the
last two 1040 MeF ATS scenarios (S3 = 4835; S4 = 8936 + Sch A + 8835). Started from the tts authoring
notes (`server/specs/form_{4835,8936,8835}_authoring_notes.md`) as HYPOTHESIS, verified every rule
against the FINAL 2025 IRS sources (Authoritative-Source Rule).*
- **IRS-source verification (2 parallel subagents, read FINAL 2025 PDFs verbatim):**
  - 8835 (Cat. 14954R, i8835 Cat. 55349M 12/22/25): all §45 resources gate on "construction begins
    before 2025" (no per-resource variance); OBBBA touched ONLY advanced-nuclear energy communities
    (TY after 7/4/25) — NOT the begin-construction gate; §45Y/§48E is a DIFFERENT form (D_8835_004).
    2025 rates $0.006/$0.003 (Fed. Reg. 2025-09366); ×5 (line 9) + 10%/10% (lines 10/11). line 15 ->
    Form 3800 line 4e (within 4-yr PIS window) or 1f. New 2025: 8c PWA -> Form 7220 (D_8835_003).
  - 8936 (Cat. 37751E; Sch A Cat. 93602W 8/21/25; i8936 Cat. 67912V 10/14/25): **OBBBA "acquired after
    September 30, 2025" termination** (25E/30D/45W), restated 4× in the instructions; "acquired" =
    written binding contract + payment (nominal down payment/trade-in counts). MAGI caps UNCHANGED by
    OBBBA (new 150/225/300k; used 75/112.5/150k), **best-of-2024-or-2025** test. Used = lesser $4,000/
    30%, price <= $25k. Commercial = min(15%/30% basis, incremental), $7,500/$40,000. Personal credits
    NONREFUNDABLE and **LOST if unused** (no carryforward); business/commercial -> Form 3800.
- **4835 reconciled** (`load_1040_form_4835.py`, re-seeded): added the S3 ATS vector (Lynette Heather:
  L1=17,035, expenses 5,974 -> L32=11,061 -> Sch E 40/42, nothing to SE) + the [VERIFY-QBI] item resolved
  (R-4835-QBI/D_4835_QBI: crop-share rent is QBI ONLY if it rises to a §162 trade/business / self-rental /
  RP 2019-38 safe harbor — default NOT-QBI, preparer-asserted; cited §199A). Now 55 facts / 12 rules / 13 tests.
- **`load_1040_form_8835.py`** (`8835`, 7 rules all cited / 32 facts / 38 lines / 5 diags / 5 tests / 4 FA):
  §45 credit calc + OBBBA before-2025 gate + ×5/+10%/+10% + line-15 4e/1f routing + S4 solar vector
  ($2,640 -> ×5 -> $13,200 -> 3800 line 4e). New sources IRS_2025_8835_FORM/INSTR, IRC_45. Year-keyed rate table.
- **`load_1040_form_8936.py`** (TWO forms — the Sch F precedent): `8936` (5 rules / 16 facts / 29 lines /
  3 diags / 4 tests) + **`8936_SCHA`** (5 rules / 24 facts / 43 lines / 4 diags / 5 tests / 5 FA). OBBBA
  9/30/2025 per-vehicle gate (D_8936_001, highest precedence); MAGI best-of-two-years; used/commercial
  formulas; routing L8->3800 1y, L13->Sch3 6f, L18->Sch3 6m, L21->3800 1aa, transfer repay new->Sch2 1b/
  used->1c. New sources IRS_2025_8936_FORM/8936SA_FORM/8936_INSTR, IRC_30D_25E_45W.
- **Schedule A (Form 8936) canonical lookup key = `8936_SCHA`** (my call; the 1120S_SCHL convention; the
  key Ken probed). Exposed as a SEPARATE form (own Cat. No. 93602W, Attach. Seq. 69A; per-vehicle) so the
  tts build computes per-vehicle then aggregates to 8936.
- **VERIFIED all four export endpoints return 200** (live server, control 9999 -> 404): 4835, 8835, 8936,
  8936_SCHA. Self-contained exports saved to `exports/form_{4835,8835,8936,8936_scha}/`.
- **Open [VERIFY] carried for the tts build (flagged, not guessed):** the S4 new-vehicle TENTATIVE credit
  is BLANK on the scenario form (seller report) — do NOT assume $7,500; the S3/S4 tests pin gates+routing,
  not the disputed dollar. Also: 8936 line-1a "11a"-vs-11 asymmetry; the 6m credit-ordering (line 11 vs 16);
  8835 line-15 4e window for the S4 solar PIS 9/22/2023. All in the loader headers as walk items.
- RS DB: **82 TaxForms / 400 FlowAssertions**. Recorded **D-4** in DECISIONS.md.

## 2026-07-04 — FORM_4835 (Farm Rental Income and Expenses) authored, seeded, exported — parallel-session 404 CLEARED
*Pivot origin: a parallel tts session's S3 resume pointer needed Form 4835, which had NO RS spec
(GET /api/forms/lookup/4835/export/ 404'd; only an authority stub existed). Ken ruled "start the 4835 spec."*
- **Source-verified** the 2025 Form 4835 face + instructions VERBATIM (f4835.pdf, Cat. No. 13117W, Attach.
  Seq. 37, Created 1/7/26 — read pages 1-3 via the Read tool). New source `IRS_2025_4835_FORM`; 11 existing
  sources referenced (IRC_1402A1/469/465/77/451_EF/263A, 6198/8582/Sch-E instr, Pub 225).
- **Ken walked 4 scope decisions (AskUserQuestion):** (1) LOSS PATH — compute the full path, not RED-defer
  ("this is for MeF testing ... 8582/6198"); (2) SE-exclusion — explicit hard invariant + flow-assertion;
  (3) elections — capture-$-flag + material-participation routing diagnostic; (4) multi-instance per-activity.
  Recorded as **D-3** in DECISIONS.md.
- **`load_1040_form_4835.py`** (READY_TO_SEED guard, flipped on Ken's in-session "approve, flip and seed"):
  form `4835` — 54 facts / 11 rules (ALL cited) / 52 lines / 8 diagnostics / 12 scenarios / 9 flow assertions.
  Verified L7 gross = right-column sum (1+2b+3b+4a+4c+5b+5d+6). Loss path computes §465 at-risk (Form 6198)
  BEFORE §469 passive (Form 8582; $25k active-participation special allowance) → line 34c → Sch E line 40;
  integrates the EXISTING RS 6198 (1120-S loader) + FORM_8582 (Sch E loader) specs, does not re-author them.
  Hand-computed 8582/6198 figures in T3/T4/T5/T6.
- **Flow correction:** the old authority stub said "income → Sch E Part I"; the face is L7 gross → **Sch E
  line 42** (farming/fishing reconciliation), L32 net / L34c loss → **Sch E line 40**. Corrected the stub
  excerpt in `sources/federal_data/forms_supporting.py`.
- **form_number gotcha:** first seeded as `FORM_4835`, but the lookup is `form_number__iexact` with NO
  `FORM_` normalization and the tts pointer requests bare `4835` (matches the 8829/6251/8283 convention) —
  renamed to `4835`, deleted the orphaned row (161 objs cascade + 8 links), re-seeded clean.
- **VERIFIED the 404 is cleared:** `GET /api/forms/lookup/4835/` and `/export/` both return **200** (APIClient,
  localhost host). Export = 90 KB self-contained package (11 rules / 54 facts / 52 line_map / 8 diagnostics /
  12 tests / 11 authority sources), saved to `exports/form_4835/form_4835_spec.json`. The parallel tts session
  can now fetch its spec live and resume S3.
- RS DB: TaxForms 79. Walk items A (8582 special-allowance figures), B (4835 → 8582 active-rental-RE bucket),
  C (SE guard covers the farm-optional gross too) noted in the loader header for the tts build leg.

## 2026-07-04 — Season checklist RS track + D-2 recorded + status-mirror extended to RS (public repo created)
*Cross-repo housekeeping per Ken's "INSTRUCTION FOR CC" — no spec/compute work. Active RS task
(K-1 box 9c pass-through verification) is UNCHANGED and still next-up.*
- **SEASON_CHECKLIST.md (tts-tax-app `fde3655`):** added the `RULE STUDIO AUTHORING TRACK` section
  (Ken rulings D-1/D-2 header; July→Oct–Nov RS authoring plan — 1065 core, state specs, 1041 spine),
  placed before the standing Unplanned-work-log tail. Edited the SOURCE repo only; the public mirror
  is regenerated by the sync script (never hand-edit `tts-tax-status`).
- **DECISIONS.md (RS `48e44cc`):** recorded **D-2 — 1041 Schedule I (AMT) RED-DEFERRED for season one**
  (loud RED diagnostic on AMT indicators; no Schedule I compute built; revisit only if regression demand
  warrants). Real dated entry at the top per the append-at-top convention; cross-refs D-1 (1065 core
  specs authored FRESH from IRS primary sources, existing 35 compute formulas reconciled against each
  spec — never spec-from-code; every mismatch = logged Ken adjudication). `last_updated` → 2026-07-04.
  The two `<Short decision title>` template stubs left below as format examples (didn't delete).
- **sync_status_mirror.ps1 (tts-tax-app):** extended to also mirror RS `STATUS.md` + `session_log.md`
  into a **`rule-studio/` subfolder** of the public `tts-tax-status` mirror (subfolder avoids colliding
  with tts-tax-app's own `STATUS.md`). PII guard refactored to an `Assert-CleanFile` function and now
  covers the RS files too; both verified clean (0 SSN/EFIN hits). PS 5.1 parse-checked.
- **Created the public GitHub repo `klill6506/tts-tax-status`** — it never existed (pushes were 404ing;
  this was the carried "one-time" item in tts STATUS). Public per Ken's explicit call, via the stored
  `klill6506` classic PAT (`repo` scope) — no `gh` installed. The local mirror clone `D:\dev\tts-tax-status`
  already existed; set upstream tracking, pushed. Verified the remote now holds the root planning files +
  `rule-studio/STATUS.md` + `rule-studio/session_log.md`; a fresh sync run reports "already current".
- **⚠ PRIVACY (new standing constraint):** RS `STATUS.md` + `session_log.md` are now **PUBLICLY mirrored**
  (RS repo itself is going private). Keep client PII and sensitive firm specifics OUT of them — the PII
  guard only blocks SSN/EFIN shapes, not prose. Saved to `.claude` auto-memory too.

## 2026-07-03 — 8995A amended: Schedule D patron reduction + capped DPAD COMPUTED (Ken ruling — MeF ATS S2)
- **Ken RULED (AskUserQuestion): "Is this a MeF test scenario? If so build 8995-A Schedule D"** — S2
  (Jones) stipulates ag-co-op patrons who "do not qualify" for QBI; enacted law routes patrons to
  8995-A at ANY income (i8995a 2025 'Who Can Take the Deduction') with the face line-3 skip at/below
  the threshold, and the §199A(b)(7) reduction = min(9% × allocable QBI, 50% × allocable W-2 wages)
  is $0 for a zero-wage business — the ATS key's blank 13a is scenario fiat, documented divergence.
- **Amended `load_1040_form_8995a.py`** (amend-by-lookup, ids stable): +facts `a_business_schd_qbi_alloc`
  / `a_business_schd_wages_alloc` / `a_dpad_199ag`; R-8995A-PATRON reauthored routing→calculation
  (SD2–SD6 chain → L14); R-8995A-SCOPE/P2-COMP/P4-LIMIT amended (patron-at-any-income, L15 floor,
  L38 cap = L33 − L37 face verbatim); +7 SD line-map rows; D_8995A_001/002 REPURPOSED error→info
  (**Ken ruled info**: patron-no-alloc confirm-the-zero; DPAD clipped) + NEW D_8995A_008/009 guards;
  T9 amended + T11–T15 hand-computed (T13 = the S2 below-threshold zero-wage patron, LOAD-BEARING);
  FA-1040-8995A-08 gating_check → formula_check. New authority source IRS_8995A_SCHD_FORM
  (f8995ad Rev 12-2022 verbatim) + patron-rules excerpt on IRS_2025_8995A_INSTR.
- **`check_8995a_integrity.py` extended** (own Sch D/skip/cap transcription) — ALL CHECKS PASS,
  15 scenarios re-derived.
- **Seeded RS Supabase** → deployed export drift = EXACTLY the amendment (24 facts / 11 rules /
  58 lines / 9 diags / 15 tests; old T9 retired) → canonical `8995a_spec.json` refreshed in tts.
- tts build same session (`f10e864`): mig 0158, engine + router + render + FormEditor; the retired
  `D_8995_001` is dormant in rules_schedule_c. Flow gate 381 (FA-08 amended in place).

## 2026-07-03 — 1040_EIC amended: `eic_opt_out` (1040 line 27c) — Ken ruled ACTC-sibling skip-entirely (S2 prep session)
- **Ken RULED (AskUserQuestion): "Skip-entirely, ACTC-sibling"** for the 2025 Form 1040 line 27c
  election ("If you do not want to claim the EIC, check here" — face verbatim, verified against the
  official 2025 f1040 PDF): the election disengages the EIC computation and every D_EIC diagnostic,
  CLEARS line 27a (never compute-then-zero), Schedule EIC does not attach, the 8867 gate stays
  consistent automatically (27a > 0 keying). Needed by ATS Scenario 2 (Jones) — their
  statutory-employee Sch C would otherwise hit the D_EIC_015 RED-defer; the scenario declines via 27c.
- **Amended `load_1040_eic.py`** (commit `e64dbea`): +fact `eic_opt_out` (sort 70), R-EIC-27A formula
  gains the opt-out gate (inputs now ["eic_opt_out"]), +D_EIC_017 (info — the D_8812_014 sibling
  explaining the blank line), +scenario EIC-G6 (opted-out qualifying return → 27a BLANK, only 017
  fires), +FA-1040-EIC-10 (loader-homed; pins the ruling incl. the stale-27a clear).
- **Seeded RS Supabase** (idempotent; FlowAssertions 381 → 382) → **deployed export verified**
  (fact/diag/scenario/rule-gate all present; drift = exactly the 3 additions) → canonical
  `eic_spec.json` refreshed in tts (tests 16 → 17).
- tts build same session: mig 0156, eic_engaged + compute_eic opt-out gates, D_EIC_017 in rules_eic,
  c2_13 render, DoNotClaimEICInd in the MeF mapper, FA gate 380 → 381, topic7 suite extended.

## 2026-07-03 — 4797 NUANCE LEG (the 3 depreciation nuances) authored + gated + SEEDED + EXPORTED (Ken: "go ahead" + 2 decisions)
- Ken: "continue with the three 4797 depreciation nuances" → verified all law verbatim (Cornell LII +
  2025 i4797) BEFORE any code, then walked 2 design decisions (AskUserQuestion):
  - **D1 (nuance 1):** a NEW per-asset classifier field `f4797_section_1245_exception`
    (none / single_purpose_ag / petroleum_storage / railroad_grading) auto-returns §1245 for the
    §1245(a)(3) real-property exceptions (D)/(E)/(F) + a per-exception info diagnostic
    (`D_4797_1245AG` / `D_4797_1245PETRO` / `D_4797_1245RRGR`). (C) §179-realty stays via D_4797_179REAL;
    (G) QPP via is_qpp/D_4797_QPP.
  - **D2 (nuances 2+3):** COMPUTE line 26a = max(0, actual accumulated depr incl. bonus − SL on the
    UNREDUCED basis) in the tts engine where the disposed §1250 asset has the MACRS data — ONE computation
    covering both 150DB land improvements (§168(b)(2)(A)) and bonused QIP; preparer-overridable.
    `D_4797_ADDL` demoted to the FALLBACK gate (fires only when the engine can't compute). Applicable % = 100%.
- **Law (verbatim, verified 2026-07-03):** §1245(a)(3)(D)/(E)/(F) + the §168(i)(13) (livestock enclosure /
  commercial greenhouse) and §168(e)(4) (railroad grading) definitions; §1250(b)(1)/(b)(3) — the (b)(3)
  carve-out is PRE-1976 §168 only, so current MACRS + §168(k) bonus ARE depreciation adjustments (nuance 3
  now statutorily grounded, not just i4797); §168(b)(2)(A) 150DB for 15-yr land improvements; i4797 line 26a
  "do not reduce the basis... to figure straight line". NEW `IRC_168` authority source (4 verbatim excerpts).
- **Authored** into `load_4797.py`: +1 fact (the classifier), R-4797-CHARCLASS + R-4797-ADDLDEPR rewritten
  (updated in place, no new rule ids), +3 info diagnostics, +4 scenarios (N1 ag→§1245 math; N2-N4 the
  exception diagnostics), +IRC_168 source/links, +the i4797 "unreduced basis" clause. `check_4797_integrity.py`
  extended (N-branch validation). **Gate ALL PASS: 27 facts / 8 rules / 34 lines / 14 diagnostics / 20
  scenarios / 19 rule links / 9 sources.** Committed GATED (`03a5606`).
- Ken: **"Approve — seed + export"** → seeded RS Supabase (idempotent; "Updated Form 4797", all rules cited;
  TaxForms 78 / FlowAssertions 381) → exported `4797_spec.json` to tts (facts 27 / diagnostics 14 / tests 21
  [1 pre-existing DB orphan scenario] / sources 14 [all linked]) → verified the new content landed
  (classifier fact, D_4797_1245*, IRC_168, N1-N4).
- **tts build leg — COMPLETE (both sub-legs), committed tts `98ac1c5` (A) + `be47294` (B); push HELD, see below.**
  - **SUB-LEG A (nuance 1, classifier):** DepreciationAsset.section_1245_exception
    (none/single_purpose_ag/petroleum_storage/railroad_grading) + migration 0157; resolve_recapture_type
    returns §1245 for a set (D)/(E)/(F) exception (after override + is_qpp); 3 info diagnostics
    D_4797_1245AG/PETRO/RRGR; test_4797_spec.py +5 classifier tests, _make_asset mock defaults the field 'none'
    (a bare MagicMock attr reads truthy → would force §1245).
  - **SUB-LEG B (nuance 2, engine-computed 26a):** depreciation_engine.calculate_1250_additional_depreciation
    = max(0, accumulated actual incl. bonus − SL-equivalent on the UNREDUCED basis), SL summed via
    _macrs_pct("SL",...) over the holding period + disposal proration (§179 reduces the SL basis, bonus does
    NOT — i4797); returns None when the MACRS data is missing. compute._resolve_1250_additional_depr +
    aggregate_dispositions wiring (preparer non-zero overrides → else engine → else 0). D_4797_ADDL demoted to
    the FALLBACK gate (fires only when the engine can't compute). +5 fast unit tests (hand-verified 10-yr HY
    case: actual 70k − SL 50k = 20k; unreduced-basis; zero-floor; None; resolve override/compute/fallback).
  - **VERIFIED: 49 fast unit tests + the pipeline DB stamp 15/15 green** (single-purpose ag → §1245; 150DB
    computed-26a end-to-end; preparer override; the D/E/F exception diagnostics; D_4797_ADDL fallback on a
    non-computable asset). One transient pooler DEADLOCK (parallel-session DB contention) re-ran clean; one
    stale D_4797_ADDL assertion was CORRECTLY failing (the demotion) → retargeted.
  - **tts push RESOLVED (2026-07-03):** the parallel EIC session committed its `0156_taxpayer_eic_opt_out`
    (`c53e942`) ON TOP of the two 4797 commits in the shared local repo and pushed the whole chain — so
    `98ac1c5` + `be47294` are now on remote main (origin/main == local HEAD, 0 ahead). Migration chain is a
    clean linear 0155→0156→0157 (both files present; 0157 depends on 0156 — Django resolves by the dependency
    graph, not commit order), no merge migration, Render-deploy-safe.
- **DONE — the 4797 nuance unit is fully closed across all three nuances:** spec→seed→export→build→unit→
  DB-verified, all on remote (RS + tts).

---

## 2026-07-03 — FORM 8283 authored + SEEDED (ATS Scenario 2's tax-law form; Ken's walk: J6 RULED warn-only)
- Ken: "go" → the S2 (Form 8283) spec-first unit per the smallest-first ruling. OBBBA check at
  the spec leg: §170(f)(11)/(f)(12) untouched by P.L. 119-21; Rev. 12-2025 form + instructions
  fetched verbatim (i8283 + USC §170(f)(11) via law.cornell.edu).
- **Authored `load_1040_form_8283.py`** (commit `0748f06`): AMENDS the shared "8283" TaxForm BY
  LOOKUP (1120S/1065/1040 entity_types preserved — the rs-amend-shared-form lesson); RETIRES the
  load_1120s_complete placeholder stub (10 facts / 5 unnamed rules / SA-*/SB-1 lines / D001-D003 /
  2 tests — never approved, never seeded to tts). 51 facts / 5 rules (R-8283-FILE/SECTION/SUBST/
  TOTAL/SCHA12) / 49 lines / 13 diagnostics / 13 hand-computed scenarios / 5 loader-homed FA
  (FA-1040-8283-01..05). IRS_2025_8283_INSTR refreshed to Rev. 12-2025 with verbatim excerpts;
  NEW source USC_26_170F11.
- **Ken's review walk (AskUserQuestion): J6 RULED "warn only, feed anyway"** — substantiation
  gaps (§170(f)(11)(C) appraisal, §170(f)(12) vehicle CWA, the attach tier) fire ERROR
  diagnostics while the amount still feeds Schedule A line 12; the withhold recommendation was
  REJECTED (do not re-litigate; FA-04 re-authored to pin the ruling). J2 (nullable capgain
  assertion, default 50% bucket, D_8283_008 warns only when the limitation binds) and J4
  (conservation RED-defer = the ONE feed withhold) as recommended; J1 feeder convention /
  J3 preparer-applied §170(e) reductions / J5 one-row-per-group / J7 wet-ink Parts IV-V +
  PDF-attachment e-file note + the stub retirement all approved. Flipped → seeded RS Supabase
  (FlowAssertions 376→381) → deployed export verified (51 facts, 0 stale ids; entity_types
  intact) → canonical `server/specs/8283_spec.json` exported to tts.
- `check_8283_integrity.py` (new root gate): independent recompute of all 13 scenarios + the
  Pub 526 T6 worksheet + id caps + citation coverage — ALL PASS (re-run after the J6 re-encode).
- **tts build same session — UNIT COMPLETE, tag `1040-form-8283-complete`** (flow gate 375→380;
  DB pipeline 6/6). Detail → tts STATUS.md / form_coverage_tracker.

---

## 2026-07-03 — 4797 classification unit DB-VERIFIED (tts `08c5382`) + NEW confirmed 1065 unrecap-§1250 misroute caught
- Ken: "go" → picked the optional **4797 DB pipeline stamp on the entity-side aggregate** (AskUserQuestion).
- Authored **tts `server/tests/test_4797_pipeline_leg.py`** — real 1065 FormDefinition (`seed_1065`), real
  `DepreciationAsset` disposition rows, real `compute_return` → `aggregate_dispositions` over the shared
  Supabase test DB. **11/11 green** (the only non-passes across runs were the known transient pooler
  AdminShutdown drops — memory `tts-test-db-collisions`; re-ran clean):
  - **TestPipelineClassification (6):** C1 15-yr land improvement 150DB (line 6 ordinary 20k / K10 §1231
    180k — NOT the §1245 100k), C2 SL QIP (ordinary 0 / §1231 200k), C3 bonused QIP (ordinary 280k /
    §1231 70k), `is_qpp` Building → §1245 full recapture (line 6 100k / K10 100k / K9c 0), explicit-1245
    override counterfactual, + the KENFLAG pin. Same numbers as the single-asset unit test, now through
    the production aggregate. Assets use **method=NONE** so `aggregate_depreciation` (runs first and
    overwrites current_depreciation + bonus_amount from the engine) is a no-op — the disposition math is
    deterministic off `prior_depreciation` + line-26a additional depr (a live MACRS tail was inflating
    total_depr by 985 in the first draft; method=NONE + folding C3's bonus into prior_depreciation fixed it).
  - **TestPipelineSEBase (1):** the C1 §1250 ordinary recapture (line 6 = 20k) rides the 1a-chain into K1
    AND is auto-pulled to WS2, so the box-14a SE base (WS3a) excludes it — the exact coupling the
    diagnostics call "misstated through worksheet 1d/2" when the character is wrong.
  - **TestPipelineDiagnostics (4):** `D_4797_CLASS` warns on the auto-§1250 Improvements default,
    `D_4797_ADDL` errors on a 150DB asset with a blank 26a, `D_4797_QPP` info fires, and clean §1245
    equipment stays quiet.
- **⚠ CONFIRMED BUG the stamp caught → Ken: "go ahead" → FIXED same session (tts `f23dc54`):**
  `aggregate_dispositions` was writing the unrecaptured §1250 gain to the hardcoded **`K8c`** (a 1120-S
  line) for BOTH forms. The 1065's own line is **`K9c`** (seed_1065.py:288), which `k1_allocator` sends to
  partner K-1 box 9c — so on a partnership the value was written to a nonexistent line, silently skipped,
  and never reached the K-1. Fix: form-branched the line (`unrecap_1250_line = "K9c" if 1065 else "K8c"`)
  in both the clear-list and the write, exactly like `ordinary_line`/`k_1231_line`; 1120-S path unchanged.
  Flipped `test_unrecaptured_1250_flows_to_k9c_on_1065` from K9c=0 to **K9c=80000** — re-ran green (with
  the prior run, all 11 pipeline tests pass with the fix). Verified the two `test_compute_4797.py` diag
  "failures" seen en route are 1040-path (`_build_return` code=1040 → the fix's `else` branch,
  byte-identical to before) + pooler-storm AdminShutdown drops — NOT a regression. Task chip dismissed.
- **NEXT:** (a) the three 4797 depreciation nuances still await Ken's scoping (property-character vs
  recovery-period edge cases, 150DB land-improvement additional depr, bonus-on-QIP §1250(b)); (b) K-1
  14b/14c still out of scope (§14.4); (c) optionally re-verify the now-fed K-1 box 9c partner pass-through
  (k1_allocator K9c→9c) if it surfaces.

---

## 2026-07-02 — SCHEDULE_SE R-SE-ROUND: per-line whole-dollar rounding (Ken ruled; the S12 REVIEW_QUEUE item) SEEDED + EXPORTED
- **Ken ruled in-session (AskUserQuestion, the recommended option): Schedule SE adopts the
  per-line whole-dollar convention** — the engine's cents-chain (12 = 3,437.44) diverged $1
  from the ATS key / TaxWise per-line math (2,786 + 652 = 3,438) and printed a self-inconsistent
  face (10 + 11 ≠ 12 at whole dollars).
- **Authority**: i1040 "Rounding Off to Whole Dollars" fetched fresh (i1040gi.pdf p.23) and
  quoted VERBATIM as a new excerpt on `IRS_2025_1040_INSTR` (the WebFetch summary paraphrased it
  WRONG — the PDF quote is canonical; [[webfetch-tax-summary-unreliable]] again).
- **Authored** (`load_1040_schedule_c.py` SE section): NEW rule **R-SE-ROUND** (precedence 0 —
  multiplication lines 4a/5b/10/11/13 round their product half-up; sum lines 3/4c/6/8d/12 add
  already-rounded entries; L2 sums cents, rounds the total per the "include cents when adding"
  sentence); L4A/L6/L10/L11/L12/L13 formulas restated with round(); SCHEDSE identity notes;
  **SE-T1..T5 re-pinned whole-dollar** (T5 load-bearing: 4,238 vs cents-chain 4,238.87);
  **FA-1040-SCHSE-02** formula → `round(...,0)` + a rounding constant; rule link R-SE-ROUND →
  IRS_2025_1040_INSTR. `check_topic8_integrity.py` `se_part_i` converted to per-line `dollars()`
  (incl. the three load-bearing sanity re-checks) — **ALL CHECKS PASS**.
- **Seeded RS Supabase** (idempotent; SCHEDULE_SE rules 13→14, all cited). **Deployed export
  verified**: R-SE-ROUND present, L4A formula carries round(), SE-T1 pins whole-dollar, the
  rounding excerpt serves. Canonical `schedule_se_spec.json` refreshed in tts; tts gate file
  `flow_assertions_1040.json` FA-1040-SCHSE-02 synced verbatim (no id drift — amended in place).
- **tts build leg same session**: `compute_schedule_se_lines` per-line `_qd`; S12 re-pinned
  (whole-dollar XML values unchanged); Schedule C/8995/7206 audited — 7206 already per-line,
  Schedule C sums-only, 8995 ×20% lines still cents → flagged to Ken.
- **SAME-SESSION FOLLOW-UP — Ken ruled "build it now": 8995 gains R-8995-ROUND** (RS `bfe1d4f`;
  the identical convention: ×20% lines 5/9/14 round their product, entries round at entry,
  sums/combines operate on rounded entries; **Form 8995-A explicitly stays cents-chained** —
  its own future ruling). Authored: R-8995-ROUND rule + link to the same IRS_2025_1040_INSTR
  excerpt (summary updated to cover both forms); R-8995-L2-L5 / L8-L9 / L13-L14 formulas
  restated; 8995-T2 re-pinned (9,952.20 → 9,952); `check_topic8_integrity.qbi_8995` per-line —
  ALL PASS. Seeded (8995 rules 8→9), deployed export verified, canonical `8995_spec.json`
  refreshed in tts. tts: `compute_8995_lines` + the 1i-1v face-row writes per-line `_qd`; S12
  re-pinned again (QBI 4,322 whole → taxable 102,373.00 / tax 17,436.06 / owe 6,430.06 —
  whole-dollar XML values STILL unchanged). No FA drift (no 8995 FA formula carries a mode).

---

## 2026-07-02 — 1065_SE leg 2: the 14a SE-BASE sub-spec SEEDED + EXPORTED (Ken: "approve and seed") + 4797 §1245/§1250 BUG CONFIRMED
- **Leg 2 (spec §4b/§14.1)** amends `1065_SE` with the ordinary-income SE base per the IRS "Worksheet
  for Figuring Net Earnings (Loss) From Self-Employment" — **text VERIFIED + quoted VERBATIM 2026-07-02
  from the live 2025 i1065 PDF (pymupdf dump, printed p.44-45)**, replacing leg 1's paraphrased excerpts.
- **Authored:** +7 facts (ws 1a/1b/1c/1d/2 inputs + 1e/3a outputs), **+5 rules** (`R-SE-BASE-1B` dealer/
  services-to-occupants rental inclusion [preparer-entered, maid-service-yes/heat-light-trash-no verbatim],
  `R-SE-BASE-1C` other-net-rental K3c inclusion, `R-SE-BASE-4797` Part II line 17 gain-out/loss-back,
  `R-SE-BASE-3A` 1e=1a+1b+1c+1d; 3a=1e−2, `R-SE-NONIND` no box 14a for estates/trusts/corps/exempts/IRAs
  — closes §14.5, now worksheet-3b/4b + Code-A grounded, not inferred), **+13 WS lines** (WS1a-WS5),
  **+3 diagnostics** (`D_SE_RENT1B` warning nudge when K2≠0, `D_SE_4797ORD` error when Part II active but
  1d/2 blank, `D_SE_NONIND` info), **+7 scenarios** (B1-B7 incl. the 3a sign rule B6: −5k−10k=(15k)),
  **+INV-SE-BASE** (active) — FLOW-14A-SE stays disabled. New `check_1065_se_integrity.py` math gate
  (independent re-type of the classification table + worksheet; loader & gate share no math) — ALL PASS.
- Ken walked the 3 design calls (1b preparer-entered+nudge; D_SE_4797ORD hard error until the 4797 engine
  feeds 1d/2; B-scenario values) → **"approve and seed"**. Seeded RS Supabase (idempotent; "Updated
  1065_SE": 18 facts / 14 rules / 25 links / 15 lines / 6 diags / 17 scenarios; **FlowAssertions → 371**,
  all rules cited) → re-exported `1065_se_spec.json` (59 KB) → **tts handoff committed (`e5f2795`)**:
  spec JSON + seed_1065_se EXPECTED bumped (re-ran clean) + test_1065_se_compute_leg partitions B1-B7 as
  NAMED pending-skips (47 passed, 7 skipped) — the base compute + non-individual guard are the next tts
  build leg.
- **⚠ COUPLED VERIFICATION (spec §4b) — REAL BUG CONFIRMED in tts:** `resolve_recapture_type()`
  (tts compute.py:1272-1290) classifies Improvements by RECOVERY PERIOD (life <27.5 → §1245), so a 15-yr
  QIP/land improvement sold at a gain takes FULL ordinary recapture instead of §1250 treatment
  (additional-depreciation-over-SL only; remainder unrecaptured §1250 → K-1 9c) — and
  `test_improvements_15yr_is_1245` PINS the bug. Propagates into box 14a via ws 1d/2. RS 4797 Part III
  math is correct once property_type is known — the defect is the tts auto-classification input.
  **Ken-flagged nuances (his call, NOT decided here):** (1) not all 15-yr is §1250 (single-purpose ag
  structures are §1245) — property character, not life, is the classifier → likely a per-asset
  determination + diagnostic (the se_classification pattern); (2) land improvements at 150DB DO have
  additional depreciation → partial ordinary recapture; (3) whether BONUS on QIP is §1250(b) additional
  depreciation — UNVERIFIED, do not guess. Recommended: its own RS-spec'd unit.
- **NEXT:** (a) tts build leg — base compute (worksheet 1a-3a) + R-SE-NONIND guard, un-skip B1-B7;
  (b) the 4797 recapture-classification RS unit (Ken to scope); (c) K-1 14b/14c still out of scope (§14.4).

---

## 2026-07-02 (MeF track, ATS Scenario 12) — NEW FORM_7217 spec AUTHORED + KEN-APPROVED + SEEDED + EXPORTED
- **Ken approved in-session** (AskUserQuestion, four items): **J1 RULED "wire §731(a)(1) gain to
  Sch D now"** (over the recommended defer) — post-ruling amendment encodes a synthesized
  no-1099-B Form 8949 row (Part I box C ST / Part II box F LT per a NEW holding-period preparer
  assertion `f7217_interest_held_lt`; proceeds = line 5c, basis = line 6; unasserted → feed
  WITHHELD + NEW **D_7217_011** RED; **D_7217_002** re-purposed to the info "auto-reported"
  transparency role; outputs `f7217_8949_st/lt`; scenarios T10/T11 added, G1 re-pinned; FA-04
  reworded + NEW **FA-1040-7217-05**) — the landing verified VERBATIM against the 2025 Partner's
  Instructions for Schedule K-1 (Form 1065) box 19 ("should be reported on Form 8949 and the
  Schedule D"; NEW source **IRS_2025_K1P_INSTR**, also carrying the §737 4797-or-8949 excerpt
  that backs the J3 defer). J2 §731(a)(2)-loss + J3 §737 defers KEPT; J4 rounding / J5
  classification-withhold / J6 securities feeder approved as encoded; the T1 answer-key
  divergence acknowledged.
- **Integrity gate re-run post-amendment: ALL CHECKS PASS** (18 scenarios / 31 facts / 5 rules /
  23 lines / 11 diagnostics / 5 FAs). **Seeded RS Supabase** (FORM_7217 created, TaxForms 78,
  all rules cited). **Deployed export id-verified: PASS** (5/11/23/31/18 exact — NOTE the lookup
  key is `FORM_7217`; the bare-number `7217` 404s). **FA drift check: RS 1040 export 353 vs tts
  gate 348 — delta EXACTLY FA-1040-7217-01..05, zero other drift.** Canonical `7217_spec.json` +
  `flow_assertions_1040_7217_pending.json` → tts `server/specs/` (ASCII-escaped). tts four-leg
  build next. *(Coordination note: a parallel 1065_SE session committed fc93643 mid-unit, which
  swept in this unit's in-flight check_7217_integrity.py J1 edit — content verified intact.)*
- *(Authoring detail below, written pre-ruling — the J1 items superseded per the amendment above.)*
- **Trigger:** ATS Scenario 12 (Sam Gardenia) is the next smallest-first scenario (Ken's 2026-07-02
  ruling); its tax-law form — Form 7217, Partner's Report of Property Distributed by a Partnership
  (§732) — had no RS spec (lookup 404, the process gate). The SEASON_PLAN appendix-4 OBBBA check ran
  at the spec leg: §732 is a basis provision, not a credit — NO sunset; amendment history stops at
  P.L. 106-170 (1999), OBBBA untouched; the Dec-2024 form/instructions revision is current. One
  post-publication development FOUND and encoded: the IRS 2026-04-27 update re-sources lines 3/5a/5b
  to NEW K-1 (1065) box 19 codes for TY2025+ (line 3 ← B/C/G + the A/F securities statement; 5a ←
  A/D/F excl. securities; 5b ← the A/F statement; instructions revision announced for Dec 2026) —
  sourcing hints only, math unchanged.
- **`load_1040_form_7217.py` (NEW):** 28 facts (distribution-level + per-property Part II rows) /
  5 rules (R-7217-FILE per-date+money-only+§751(b)+claim-year screens; -GAIN §731(a)(1) lines 5-8;
  -L9L10 the §732(a)(2)/(b) allocable-basis mechanic incl. the i7217 line-9 §737-include +
  5a-only-subtraction literal reading; -ALLOC the FULL §732(c) waterfall — hot assets at basis
  first (decrease-only tier), other property with (c)(2) increase / (c)(3) decrease; -LOSS the
  §731(a)(2) liquidating-loss detection, the one lawful line-10 ≠ B(e) case) / 23 lines / 10
  diagnostics / **16 HAND-COMPUTED scenarios** (T1 = ATS-12 facts under enacted law — ⚠️ the IRS
  key's own Part II is internally inconsistent (col (e) 4,000 vs its line 10 = 6,000) and lists
  "CASH" as a Part II property; T2/T3 pin the i7217's OWN Examples 1 & 2 verbatim incl. the worked
  100/440/110 waterfall; every (c)(1)(A)/(B), (c)(2)(A)/(B), (c)(3)(A)/(B) branch + gain / loss /
  §737 / securities / unclassified / money-only / claim-year edges) / 4 loader-homed
  FA-1040-7217-01..04. Sources: NEW USC_26_732 + USC_26_731 + IRS_2024_7217_INSTR (incl. the
  box-19 update excerpt) + IRS_2024_7217_FORM, all key passages verbatim, requires_human_review set.
- **Gate:** NEW `check_7217_integrity.py` — an INDEPENDENT §732(c) transcription (statute-direct,
  self-tested against the IRS Example-2 answer before checking the loader) + full per-scenario
  recompute + varchar(20) id guards + structure checks — **ALL CHECKS PASS** (16 scenarios). The
  gate caught one authoring gap live (D_7217_004 unexercised → scenario 7217-G7 added).
- **NOT seeded** — READY_TO_SEED=False; refusal verified. Six judgment items J1-J6 queued for
  Ken's review walk (gain/loss/§737 RED-defers; rounding; classification withhold; securities
  feeder) + the T1 answer-key divergence.
- tts build (PartnershipDistribution + DistributedProperty models, compute_7217, input tab,
  AcroForm render, FA merge, then the Scenario-12 mapper) follows in tts-tax-app after approval.

---

## 2026-07-02 (MeF track, ATS Scenario 13) — NEW FORM_8911 spec AUTHORED + SEEDED + EXPORTED
- **Trigger:** ATS Scenario 13 (Birch) is the next smallest-first scenario unit (Ken's 2026-07-02
  ruling); its tax-law form (8911 + Schedule A) had no RS spec (lookup 404 — the process gate).
  The SEASON_PLAN appendix-4 **OBBBA sunset check ran at this spec leg as required**: §30C(i) as
  amended by P.L. 119-21, fetched VERBATIM (law.cornell.edu + i8911 Rev. 12-2025) — "This section
  shall not apply to any property placed in service after June 30, 2026." → **TY2025 fully live,
  TY2026 HALF-YEAR live (Jan–Jun installs), TY2027+ dead. NOT zero TY2026 value — no S13 re-rule.**
- **Ken approved in-session** (AskUserQuestion, all four judgment items): (1) the line-6b ORDERING
  reading — the verbatim instruction sums Sch 3 "lines 2 through 5, and 7 (reduced by 6a/6b/6k)";
  line 7 literally includes 8911's own 6j → encoded as "all Part-I credits ordered before 8911,
  never its own 6j"; (2) census tract = PREPARER ASSERTION v1 (GEOID 11-digit format validated,
  Appendix A/B NOT adjudicated; unanswered → D_8911_001 RED + excluded, answered No → quiet stop);
  (3) business path computes on the face but RED-defers to the unbuilt Form 3800 (D_8911_004,
  line 3 + K-1 line 2 never land on Sch 3); (4) the T1 enacted-law pins — the IRS ATS-13 answer
  key used the PRE-OBBBA 30,000 MFJ std deduction (tax 162/credit 162); enacted law (31,500) →
  tax 11/credit 11; the engine follows enacted law, ATS acceptance is schema + business rules.
- **`load_1040_form_8911.py` (NEW):** 16 facts (per-property Sch A rows + return-level K-1) /
  5 rules (R-8911-QUALIFY window+claim-year+tract, -SCHA-PERS 30%/$1,000-per-item, -SCHA-BUS
  6%-30%PWA/$100,000 + §179 backout + 1/29/2023 auto-Yes, -TAXLIM L5-L9 with TMT-figured-always
  = FORM_6251 line 9, -SCH3-6J min(L4,L9) + excess LOST) / 35 lines (form + "A-" prefixed Sch A) /
  6 diagnostics / 10 HAND-COMPUTED scenarios (Birch enacted-law exact; $1,000 cap; TMT bite;
  **6/30↔7/1/2026 boundary pair**; tract No vs UNANSWERED; business RED; mixed-use 6%; 6b
  exact-fit; claim-year trap) / 4 loader-homed FA-1040-8911-01..04. Sources: NEW USC_26_30C +
  IRS_2025_8911_INSTR + IRS_2025_8911_FORM, all key passages verbatim, requires_human_review set.
- **Gate:** NEW `check_8911_integrity.py` — independent re-typed constants + full per-scenario
  recompute + the varchar(20) id guards — **ALL CHECKS PASS** (pre- and post-flip).
- **Seeded RS Supabase** (FORM_8911 created; TaxForms 77, FlowAssertions 370 rows). **Deployed
  export verified id-level** (5/6/10/35/16 exact, all ids match). **FA drift check: RS 1040 export
  348 vs tts gate file 344 — delta EXACTLY FA-1040-8911-01..04, zero other drift** either
  direction. Canonical `8911_spec.json` exported to tts `server/specs/`.
- tts build (RefuelingProperty list model, compute_8911, input tab, AcroForm render, FA merge,
  then the Scenario-13 mapper: IRS6251 + IRS8911 + IRS8911ScheduleA) follows in tts-tax-app.

---

## 2026-07-02 (MeF track, later) — R-8959-ENGAGE amendment: Who-Must-File engage gate SEEDED + EXPORTED
- **Trigger:** ATS Scenario 5's W-2 (box 5 = 31,232 / box 6 = 453, a whole-dollar-rounded 452.86)
  made compute put $0.14 on 1040 line 25c — the code's 'line 22 > 0 engages' arm (never in the
  spec) treats ANY box-6 excess as Additional Medicare withholding. The 2025 i8959 Who Must File
  (fetched + quoted VERBATIM, rev. Aug 7 2025) lists FOUR conditions only; a box-6 excess is not
  one — and both spec and code MISSED bullet 1 (any SINGLE W-2 box 5 > $200,000 FLAT — the
  employer-withholding case, e.g. one 210k W-2 on an MFJ return under the 250k threshold).
- **Ken approved in-session** (AskUserQuestion): bullet-1 arm added, line-22 arm removed,
  D_8959_003 engage-gated.
- **`load_1040_schedule_c.py`:** +fact `amt_max_single_w2_medicare_wages`; R-8959-ENGAGE formula =
  the three Who-Must-File arms (RRTA bullets stay RED-deferred); D_8959_003 condition gains
  `form_8959_engaged`; +scenarios 8959-T6 (HAND-COMPUTED: MFJ one 210k W-2 → engages via bullet 1,
  L21 3,045 / L22 = L24 = 90 → 25c; L18 = 0) and 8959-T7 (the Scenario-5 rounding artifact →
  NOT engaged, 25c untouched, D_8959_003 quiet); +NEW source `IRS_2025_8959_INSTR` with the
  verbatim Who-Must-File excerpt + R-8959-ENGAGE link.
- **Gate:** `check_topic8_integrity.py` extended (amt_8959 gained the max-single-W2 engage arm +
  T6/T7 re-derivation blocks) — **ALL CHECKS PASS**.
- **Seeded RS Supabase**; deployed 8959 export verified (only the intended deltas); SIBLING exports
  (SCHEDULE_C / SCHEDULE_SE / 8995) id-diffed vs their tts canonical files — **zero sibling drift**
  (the sibling-spec re-export lesson). Canonical tts `8959_spec.json` replaced.
- tts: `form_8959_engaged` reshaped (max_single_w2 arm, line-22 arm gone) + `max_single_w2_box5`
  shared helper (compute + all three D_8959_* diagnostics — bridge-gate); tests updated (trip-wire
  5→7, engage-gate cases). ATS Scenario 5 re-probe: 22/22 pinned lines match, 25d = 1,754 exactly.

---

## 2026-07-02 (MeF track) — SCH_8812 ACTC opt-out amendment + spine PECF facts SEEDED + EXPORTED
- **Trigger:** MeF ATS Scenario 5 (Bobby Barker) checks the 2025 Form 1040 line-28 box — official
  face verbatim: "Additional child tax credit (ACTC) from Schedule 8812. If you do not want to
  claim the ACTC, check here" (e-file `DoNotClaimACTCInd`, 2025v5.4). compute_8812 had no election.
- **Ken approved in-session** (AskUserQuestion): skip-Part-II-A-entirely semantics (16a–27 zero,
  1040 line 28 = 0; CTC/ODC line 14 → line 19 NEVER touched).
- **`load_1040_ctc.py`:** +fact `actc_opt_out` (return-level election, default false); R017
  formula/inputs gain `AND NOT actc_opt_out`; +D014 (info transparency — elected with QCs
  present); +TS19 (HAND-COMPUTED: HOH, 2 QC, tax 500 → L_14 500 kept, forfeits the 3,400 ACTC);
  +FA-1040-CTC-13 (`conditional_zero`, trigger actc_opt_out — loader-homed, no export drift);
  +verbatim line-28 excerpt on the EXISTING `IRS_2025_1040_FORM` source (LOOKUP-attach, never
  update_or_create over a shared source row) + R017 link. Docstring counts refreshed.
- **`load_1040_spine.py`:** +facts `pecf_primary` / `pecf_spouse` (Presidential Election Campaign
  header boxes — stored, no compute effect; e-file `PECFPrimaryInd`/`PECFSpouseInd`). The
  lived-apart (`mfs_hoh_lived_apart_last_6_months`) and main-home-US (`us_home_more_than_half_year`)
  facts ALREADY existed. Fixed the stale "no blind flag exists in tts" notes (model has both).
- **Seeded RS Supabase** (both loaders; RuleAuthorityLinks 975→971 wobble = the known 1040-stub
  supersession cycle between the two loaders, both link-gates green). **Deployed export verified:**
  SCH_8812 39 facts / 13 diagnostics / 19 tests, R017 amended, TS19 exact; FA export 344 = tts
  gate 343 + exactly FA-1040-CTC-13, zero other drift either direction. Canonical
  `sch_8812_spec.json` + `1040_spine_spec.json` re-exported to tts same sitting.
- tts build (model field, compute gate, input, render, FA merge) follows in tts-tax-app.

---

## 2026-07-02 (later) — GA-500 W7 amendment: HB 463 tips/overtime exclusions SEEDED + EXPORTED
- **Ken approved in-session** (AskUserQuestion ×2: the four scope forks — full unit / per-taxpayer
  cap / assertion+auto-feed / dedicated S1-12a-12b sub-lines — then the seed go-ahead after the
  review-packet walk).
- **The law:** enacted HB 463/AP (signed 2026-05-11; legis.ga.gov doc 249080) §48-7-27(a)(16)
  qualified overtime / (a)(17) cash tips — each ≤$1,750, TY2026-2028, both self-repeal 12/31/2028.
  Verbatim text fetched + quoted (the tts-side statute verification earlier the same day).
- **Loader `load_ga500_form_500.py`:** +6 facts (per-owner tips/OT bases + FT-hourly assertions),
  +rules R-GA500-TIPS / R-GA500-OT (window-gated, PER-TAXPAYER cap, OT assertion gate, W-2-only
  OT source, RAW federal bases — GA has no phaseout), R-GA500-L9-S1 amended (subs run L7-L12b),
  +lines S1-12a/S1-12b, +diagnostics D_GA500_013 (OT-unasserted nudge) / 014 (tips-attestation
  nudge) / 015 (out-of-window error), +scenarios GA500-T15..T18 (HAND-COMPUTED: per-taxpayer caps
  3,500/2,750 → tax 4,179; unasserted-OT zero → 2,246; TY2025 year gate → 2,491; under-cap
  passthrough → 1,672), +FA-GA500-13/14, +4 rule-authority links, W7 walk item documented.
- **HB 463 authority CORRECTED:** the prior summary excerpt WRONGLY dated the std-deduction
  increase 2027; replaced with 5 VERBATIM /AP excerpts (effective date §5-1, strike-and-insert
  rate/std/dep text, both exclusion paragraphs, RIE (xiii)/(xiv) timing); the seed deletes the
  stale excerpt row by its old label (excerpts key on source+label). Source citation/trust
  updated (doc 249080, 10.0).
- **Gate:** `check_ga500_integrity.py` extended (independent re-typing: window helper, per-owner
  caps, S1-13/14 now emitted) — **ALL CHECKS PASS** (constants + helpers + LIC + 18 scenarios).
- **Seeded RS Supabase:** form 500 now 83 facts / 23 rules / 91 lines / 15 diagnostics / 18
  scenarios / 14 FA. Deployed export re-fetched → canonical tts `server/specs/500_spec.json`
  replaced; id-level drift check: only R-GA500-L9-S1 (intended) + two rules' embedded authority
  metadata (the corrected source row) changed — zero content drift otherwise. FA-GA500-13/14
  merged into the tts gate file (341→343 assertions; gate 363→365) — loader homes exist HERE, so
  no export drift (the fa-needs-rs-loader-home rule).

---

## 2026-07-02 — FA drift resolved: RS DB re-synced to the tts canonical gate (export 341 = file 341)
- REVIEW_QUEUE 2026-07-01 item; **Ken chose "re-seed RS now; tts file stays canonical"** (in-session).
- **Root cause:** the 21 missing assertions never had loader homes. FA-1040-2441-07 and the six
  FA-1040-5329-* existed ONLY in the tts gate file (merged there during their units); load_sch_1a.py
  still carried the pre-rename FA-1040-SCH1A-01..07 block. The tts canonical set = the 14 renamed
  FA-SCH1A-* PLUS the retained legacy-id 05/06/07; only 01..04 were superseded.
- **Changes (transcription was MECHANICAL — scripted from the canonical JSON, no re-authoring; all
  21 were already Ken-approved via their tts units):**
  - `load_sch_1a.py` — FLOW_ASSERTIONS block replaced with the canonical 17 (14 FA-SCH1A-* +
    legacy 05/06/07 verbatim); the seed now DISABLES the superseded 01..04 (the export serves
    status="active" only; rows stay auditable) and forces-active everything the block owns.
  - `load_1040_form_2441.py` — +FA-1040-2441-07 (sort 7).
  - **NEW `load_1040_5329.py`** — FA-only loader (six FA-1040-5329-*); documents the boundary:
    no 5329 form spec is authored in RS yet — that remains open work with its own future
    READY_TO_SEED review.
- Seeded RS Supabase (FlowAssertions rows 342→363 incl. disabled); deployed
  `/api/flow-assertions/export/?entity_type=1040` verified by id-level diff: **341 = 341, zero
  drift both directions.** Routine re-exports are clean again. tts gate file untouched.

---

## 2026-07-01 — FORM_2210: dated §6654 accrual amendment SEEDED + EXPORTED
- **Ken chose scope option 1 in-session ("build as designed", tts
  `server/specs/2210_dated_penalty_design.md`)** — that approval covers this amendment + seed
  (the form's READY_TO_SEED was already True from the 2026-06-15 review walk).
- **The change:** R-2210-REG reworded from the fixed due-date→4/15/2026 day count (DAYS_7/DAYS_6
  arrays) to the i2210 Penalty Worksheet rule its own authority excerpt already stated verbatim —
  each payment applies to the EARLIEST still-underpaid installment and the underpayment accrues
  from its due date to the date cured, capped 4/15/2026 (7%→6% split at 3/31/2026). Withholding
  stays ¼-spread ON the due dates (§6654(g) default; the actual-date election remains deferred).
  Loader pure functions rewritten to the unified dated algorithm (`days_at_rates` + earliest-first
  event loop; `underpayments` = the at-due-date face-25 values); `compute_2210` gained
  `payments_dated`. NEW fact `t2210_payments_dated`; NEW scenarios **P-T7 (mid-year lump, 217)** /
  **P-T8 (Q4 paid 1/25/2026, 5)** — both HAND-COMPUTED; P-T1..T6 unchanged (due-date payments
  reproduce the old numbers exactly — the backward-compat pin). FA-02/03 reworded; NEW
  **FA-1040-2210-07** (dated payments stop accrual on the date paid).
- **`check_2210_integrity.py` extended** — its independent transcription now re-types the dated
  algorithm (event loop + its own day counter) + pins the DAYS_7/DAYS_6 equivalence at the cap and
  the zero-days-on-time boundary. **ALL CHECKS PASS** (11 facts / 3 rules / 11 lines / 5 diags /
  9 scenarios / 5 links / 7 FAs).
- Seeded RS Supabase (`update_or_create`; TaxForms 76 unchanged, **FlowAssertions 341→342**).
  Deployed export fetched → canonical **tts `server/specs/2210_spec.json` replaced** (semantic
  diff = exactly ~R-2210-REG, +t2210_payments_dated, +P-T7/P-T8; diagnostics/lines/authorities
  untouched).
- **Same-session follow-ups:** (`9f94b7b`) +diag **D_2210_DATED** (dated-vs-line-26 reconciliation
  warning) + P-G2 scenario + creditable-kind conventions in the fact notes → re-seeded (10 scenarios,
  6 diagnostics) + re-exported. (`0b72b6f`) the tts FA-03 gate caught my pure function blending the
  form's TWO allocations — fixed: FACE line 25 = per-column DATE-WINDOW netting (+overpay carry);
  PENALTY = the earliest-first date-cured worksheet; FA-03 reworded to state both; gate ALL PASS,
  re-seeded (FA text only).
- tts legs shipped same session — tag `1040-2210-dated-payments-complete` (6 DB pipeline tests green,
  incl. the dated-late-Q4 = 4.00 hand-computed pin).

---

## 2026-07-01 — 1065_SE: Schedule K / K-1 line 14a Self-Employment (SECA) SEEDED + EXPORTED
- New form `1065_SE` (entity_type 1065, TY2025, draft) authored from the LOCKED spec
  `tts-tax-app/server/specs/1065_se_line14a_spec.md` (tax-law decisions locked by Ken 2026-07-01;
  faithful translation only — no tax-law calls made here). New loader `load_1065_se.py`, mirrors the
  `load_1040_schedule_k1.py` idiom (READY_TO_SEED guard + hollow-seed guard + single `@transaction.atomic`,
  `update_or_create` throughout → idempotent, no partial writes; a first run tripped varchar(255) on the
  case-law `citation`, shortened, re-ran clean).
- **Governs:** Sch K line 14a + per-partner K-1 box 14 code A. The one modernization vs today's silent
  compute: substitutes a per-partner functional-analysis `se_classification` (active/passive/undetermined)
  for the IRS SE Worksheet's mechanical "limited partner" label at lines 3b/4b (post-*Soroban* an *active*
  limited partner is not a "limited partner, as such" under §1402(a)(13)). Entity 14a derived BOTTOM-UP =
  Σ per-partner box 14a (replaces the independent `K14a = K1 + K4c`). SE base itself OUT OF SCOPE (§14).
- **Authored:** 7 authority sources (IRC §1402 / §702 / §707(c); Treas. Reg. §1.1402(a)-1 & -4; the
  limited-partner case line Renkemeyer/Soroban I+II/Denham/contra-Sirius; IRS i1065 2025 SE Worksheet p.45)
  + 1 topic; 11 facts; **9 rules** (R-SE-CLASS, -DSHARE, -GPSVC, -GPCAP, -DEFAULT, -RENTAL, -PORT, -LOSS,
  -14A-ENT) with **18 RuleAuthorityLinks (all rules cited)**; 2 lines (`K14a`, `14a`); **3 diagnostics**
  (D_SE_UNDET error, D_SE_GPCHAR warning, D_SE_RECON error); **10 tests** (T1–T10, expected 14a locked);
  **3 flow assertions** (RECON-14A + INV-CHAR active; **FLOW-14A-SE seeded status=disabled** = future/inactive).
- **CFR/USC text READ DIRECTLY and quoted VERBATIM 2026-07-01** (Cornell LII mirror; eCFR geo-blocked
  automated fetch): Reg §1.1402(a)-1(a)(2) & (b) [note (a)(2) says "section 702(a)(9)" — the reg's own
  pre-renumbering cross-ref, quoted as-is], Reg §1.1402(a)-4(a), IRC §1402(a)/(a)(1)/(a)(2)/(a)(3)/(a)(13),
  §707(c), §702(a)(8)/(b). Case-law group carries the "verified 2026-07-01 / re-verify each season" note
  (`requires_human_review=True`; developing circuit split, Soroban 2nd Cir. / Denham 1st Cir. appeals pending).
- Seeded RS Supabase (`update_or_create`; **TaxForms 75→76, FlowAssertions 338→341**). Ran dev server →
  `GET /api/forms/lookup/1065_SE/export/` returns HTTP 200 → wrote **`1065_se_spec.json`** (38 KB, repo root):
  9 rules / 3 diagnostics / 10 tests / 7 authority_sources / 2 lines, all rules cited. Active-assertions
  export (`?entity_type=1065`) correctly excludes the disabled FLOW-14A-SE.
- **DoD met; STOPPED as instructed.** The tts `seed_*` loader + `compute_self_employment` rewrite are a
  SEPARATE tts-tax-app session, gated on this export being fetchable (do NOT touch tts compute here).
  Coupled follow-up (spec §4b/§14): the SE-base sub-spec (i1065 worksheet 1a–3a Form-4797/rental
  adjustments) is coupled with the 4797 §1245-vs-§1250 recapture verification.

---

## 2026-07-01 — SCHEDULE_A: line 5a state-income-tax auto-aggregation amendment SEEDED + EXPORTED (Ken go-ahead)
- Ken's UX/bug batch item "state withholding → Schedule A". Ken chose (tts AskUserQuestion) the FULL scope
  (withholding + estimates + prior-year taxes + prior-year extensions, with payment DATES) AND the full RS
  round-trip. Line 5a was a single hand-keyed fact (`scha_salt_income_or_sales`); it now AUTO-TOTALS the
  return's state/local income tax. `load_1040_schedule_a.py` amended:
  - **+4 facts** — `scha_state_income_tax_withheld` (derived Σ doc withholding, YELLOW),
    `scha_state_estimated_payments` + `scha_state_prioryear_tax_paid` (aggregates of a new tts
    `StateIncomeTaxPayment` child table, filtered to date_paid in the tax year),
    `scha_line5a_state_income_total` (the YELLOW auto-total = withheld + estimated + prior-year).
  - **+1 rule** `R-SCHA-5A-STATE` (precedence 2, BEFORE R-SCHA-SALT — it feeds line 5d). Line 5a DEFAULTS to
    the auto-total (YELLOW) unless general sales taxes are elected (`scha_use_sales_tax` → the sales figure)
    or `scha_salt_income_or_sales > 0` is a direct override (GREEN wins). §164 cash-basis: deductible in the
    year PAID (a Q4 estimate paid in January is next year's). Existing rules 2-7 precedence-bumped to 3-8
    (ordering metadata only; no logic drift — confirmed by field-level diff).
  - **+2 diagnostics** — `D_SCHA_010` (info, transparency: 5a auto-totaled from W/E/P; verify complete; note
    that mandatory CA/NJ/NY SDI/UI/family-leave contributions are NOT auto-included), `D_SCHA_011` (info,
    no-silent-gap: a payment dated outside the tax year is excluded from 5a).
  - **+5 scenarios** SCHA-T12..T16 (withholding-only; WH+estimates+prior-year; Jan-paid Q4 excluded;
    direct-entry override GREEN; sales-tax election suppresses). **+2 flow assertions** FA-1040-SCHA-07/08.
  - **+1 authority** `IRS_2025_SCHA_INSTR` — the 2025 Instructions for Schedule A "Line 5a" text, fetched +
    quoted VERBATIM 2026-07-01 (withholding from W-2/W-2G/1099-G/R/MISC/NEC; prior-year tax paid this year;
    estimates incl. a prior-year refund credited forward; mandatory SDI/UI/family-leave; NOT refunds). Linked
    to R-SCHA-5A-STATE (primary) + the form face (secondary).
- **Math is a sum + a §164 date filter — no new numeric constants.** `check_schedule_a_integrity.py` extended
  (independent `ind_line5a_total` / `ind_line5a_final` recompute; D_SCHA_010/011 in DIAG_KEYS) → ALL CHECKS
  PASS (facts 26→30, rules 7→8, diags 9→11, scenarios 12→17, links 10→12, FA 6→8). Seeded RS Supabase
  (`ylqaejdqwuvwpglxnpgv`, idempotent `update_or_create`; FlowAssertions 336→338, TaxForms 74, all rules
  cited) → re-exported `/api/forms/lookup/SCHEDULE_A/export/` → overwrote tts `server/specs/schedule_a_spec.json`
  (semantic diff: ONLY the 4 facts + 1 rule + 2 diags + 5 tests added, 6 precedence bumps; zero content drift).
- **tts build (compute/model/render/input/diagnostics/tests) is the next leg** — the `StateIncomeTaxPayment`
  child model + the withholding aggregation (W2StateEntry rows, else the legacy flat field; 1099-R/INT/DIV,
  1099-G, W-2G) → line 5a. Federal payment-date capture for Form 2210 UET is a SEPARATE next unit (Ken's
  sequencing choice).

---

## 2026-07-01 — FORM_8606: Roth basis tracker (year-over-year line 22/24) amendment SEEDED + EXPORTED (Ken go-ahead)
- Ken's UX/bug batch item "Roth basis tracker — year-over-year Roth contribution basis (8606 Part III only
  captures at distribution)". Ken chose (tts AskUserQuestion) contribution+conversion cumulative scope AND the
  full RS round-trip (compute_8606 is spec-governed). `load_1040_8606.py` amended:
  - **+1 fact** `f8606_roth_cy_contributions` (decimal) — current-year regular Roth contributions. NOT an 8606
    line: a regular Roth contribution needs no 8606, so it's recorded on the per-owner Roth basis tracker
    (tts `RothIRABasis`) and the proforma roll adds it to next year's line-22 basis.
  - **+1 routing rule** `R-8606-ROTHTRACK` — line 22 (contribution basis) + line 24 (conversion basis) are
    SOURCED from the per-owner tracker (opening carryforward, YELLOW), overridable direct-entry (GREEN). The
    year-over-year roll is stated exactly: a distribution recovers contribution basis FIRST tax-free, so
    next line 22 = max(0, l22 − l21) + cy_contributions (l21 = roth_dist − homebuyer); next line 24 =
    max(0, l24 − max(0, l21 − l22)) + this year's conversions (line 8). Cited IRC_408A (§408A(d)(4)) +
    i8606 Part III.
  - **+1 diagnostic** `D_8606_ROTHNOBASIS` (warning) — nonqualified Roth distribution present with zero
    recorded contribution+conversion basis → the whole distribution is taxed as earnings (line 25c); nudge to
    enter the cumulative basis / use the tracker. Closes a silent over-taxation gap. + scenario F-G2.
- **Part III math UNCHANGED** — §408A(d)(4) ordering was already verified/cited; the tracker is a records-keeping
  carryforward, not new law. The roll formula was hand-verified against two worked examples (full + partial basis
  recovery). `check_8606_integrity.py` ALL CHECKS PASS (facts 16→17, rules 4→5, diags 6→7, scenarios 8→9,
  links 6→8; the §408(d) pro-rata + §408A ordering still re-type to the dollar). Seeded RS Supabase
  (`ylqaejdqwuvwpglxnpgv`, idempotent `update_or_create`) → re-exported `/api/forms/lookup/FORM_8606/export/` →
  overwrote tts `server/specs/8606_spec.json` (semantic diff: ONLY the 4 additive items; zero drift on existing
  content). +1 flow assertion `FA-1040-8606-07` (in the FlowAssertion table, 336 total; not in the form export —
  wired tts-side in flow_assertions_1040.json). tts DiagnosticRule rows re-seed on the next Render deploy.

---

## 2026-07-01 — FORM_1116: §904(j) de minimis AUTO-election amendment SEEDED + EXPORTED (Ken go-ahead)
- Ken's UX/bug batch item "foreign-tax de minimis (§904(j))". Ken chose (tts AskUserQuestion) auto-apply +
  opt-out AND the full RS round-trip (the diagnostics are spec-governed). `load_1040_form_1116.py` amended:
  - **+1 fact** `f1116_deminimis_optout` (boolean, return-level opt-out; stored on tts `Taxpayer`, NOT on a
    Form 1116 row — the auto-path must work with no Form 1116 engaged).
  - **`R-1116-ELECT` reworded** — the §904(j) election now applies AUTOMATICALLY when the only foreign tax is
    from 1099-INT/1099-DIV (passive + payee-statement by definition), total ≤ $300/$600, no full Form 1116
    engaged, and not opted out (else the existing manual `elect_simplified`). Same math: min(foreign tax,
    regular tax) → Sch 3 L1, no carryover.
  - **`D_1116_001` reworded** ('available / check the box' → 'applied automatically'); stays info.
  - **+1 diagnostic** `D_1116_009` (warning) — over-ceiling nudge: 1099 foreign tax > ceiling with no Form 1116
    engaged → the credit is unclaimed; file the full Form 1116 or deduct on Sch A. Closes a silent gap.
    App-layer condition (reads the 1099 aggregate + no-Form-1116-row) → no pure compute_1116 scenario.
- **Math UNCHANGED** — the §904(j) conditions were re-verified verbatim vs i1116 + 26 USC §904(j) (no new law).
  `check_1116_integrity.py` ALL CHECKS PASS (facts 19→20, diagnostics 8→9, rules 5, all scenarios recompute to
  the dollar). Seeded RS Supabase (`ylqaejdqwuvwpglxnpgv`, idempotent, `update_or_create`) → re-exported
  `/api/forms/lookup/FORM_1116/export/` → overwrote tts `server/specs/1116_spec.json` (semantic diff: ONLY the
  opt-out fact + D_1116_009 added, D_1116_001 message + R-1116-ELECT text changed; zero drift). tts DiagnosticRule
  rows re-seed on the next Render deploy (build.sh idempotent seed_rules).

---

## 2026-06-30 — Default-to-No due-diligence questions: D_1040_017 + D_SCHB_001 severity amendment SEEDED + EXPORTED (Ken go-ahead)
- Part of Ken's UX/bug batch. Ken chose the "proper RS round-trip now" path (tts AskUserQuestion) after CC
  flagged that the tts code change touched spec-governed diagnostics. Two loaders amended:
  - **`load_1040_spine.py`** — `D_1040_017` (digital-asset question) severity **warning → info**, retitled
    "defaulting to No", message reworded to the confirm-nudge. Unanswered now DEFAULTS to No on the header
    (the No box prints); No is a valid answer so the required question is still answered (matches TaxWise/Lacerte).
  - **`load_1040_intdiv_qdcgt.py`** — `D_SCHB_001` severity **error → info**, condition widened to
    `part_iii_required AND (foreign_account_yes is NULL OR foreign_trust_yes is NULL)` so it now covers BOTH
    7a-1 (foreign account) AND line 8 (foreign trust) — the note always said it should, but the tts code only
    checked 7a-1 (fixed tts-side too). `R-SB-05` description updated: "the face never guesses" → "unanswered
    7a-1 / line 8 DEFAULT to No; D_SCHB_001 (info) reminds to confirm."
- **Both integrity gates GREEN** (`check_spine_integrity.py` all clean, no dup/uncited; `check_intdiv_integrity.py`
  ALL CHECKS PASS — counts unchanged: spine 44 rules/91 facts/16 diags/32 scenarios; SCH_B 5/6/7/6). No new
  facts/rules/lines/diagnostics — pure severity/message/condition edits on existing entries.
- Seeded RS Supabase (`ylqaejdqwuvwpglxnpgv`, idempotent) → re-exported `/api/forms/lookup/1040/export/` +
  `/api/forms/lookup/SCH_B/export/` → overwrote tts `server/specs/1040_spine_spec.json` + `sch_b_spec.json`
  (semantic diff verified: ONLY the two diagnostics + R-SB-05 description changed, zero drift).
- tts side: render defaults (digital-asset + 7a-1/8 null → No box), UI default-No YELLOW selects, `rules_1040.py`
  / `rules_schb.py` severities synced, tests updated. tts DiagnosticRule rows re-seed on the next Render deploy
  (build.sh idempotent seed_rules) — standard for any diagnostic change.

---

## 2026-06-30 — 1040_RETIREMENT: SSA withholding / Medicare / Railroad amendment SEEDED + EXPORTED (Ken go-ahead)
- Part of Ken's Bach-return UX batch (item 1). Ken greenlit the seed in-session. Amended `load_1040_retirement.py`:
  **+4 facts** (`ssa_fed_withheld`→25b, `ssa_medicare_premiums`, `ssa_medicare_destination` schedule_a|sehi,
  `ssa_is_railroad` RRB-1099 SSEB metadata), **+2 rules** (`R-RET-25B-SS` extends the 25b roster; `R-RET-MEDICARE`
  routes Medicare → Sch A line 1 (Pub 502) OR SEHI Sch 1 L17 single-proprietor (Form 7206)), **+D_RET_009** RED
  (Medicare-as-SEHI with multiple businesses or Marketplace/PTC → verify manually), **+2 scenarios** (RET-WH-1,
  RET-MED-1), **+2 flow assertions** (FA-1040-RET-09/10), **+3 rule_links**, **+2 authority sources**
  (`IRS_2025_PUB502`, `IRS_2025_F7206_INSTR`, both verbatim-verified 2026-06-30 against the live IRS text).
- **LAW VERIFIED 2026-06-30** against primary IRS sources (NOT memory — a WebFetch summary first gave a WRONG
  "Medicare not deductible" answer; re-fetched the actual pubs): i1040 line 25b (SSA-1099 box 6 / RRB-1099 box 10
  → 25b); Pub 502 (Part B/D premiums ARE deductible medical; Part A if voluntarily enrolled); Form 7206 instr
  (Medicare premiums qualify as SEHI, capped at net SE profit, not for employer-subsidized months); Pub 915
  (RRB-1099 SSEB Tier 1 pools identically into box-5 → 6a/6b).
- `check_retirement_integrity.py` → **ALL CHECKS PASS** (independent math intact; unique ids; all rules cited).
  Counts: 1040_RETIREMENT 39 facts / 13 rules / 26 lines / 9 diagnostics / 22 scenarios / 18 links; FA 335 total.
- Seeded RS Supabase (`ylqaejdqwuvwpglxnpgv`, idempotent) → re-exported `/api/forms/lookup/1040_RETIREMENT/export/`
  → overwrote tts `server/specs/retirement_spec.json` (verified the 4 facts + 2 rules + D_RET_009 present).
- **NEXT (tts build):** Taxpayer model fields (+migration) → compute (25b += SSA WH; Medicare → Sch A L1 / SEHI
  single-proprietor) → render (SSA vs RRB worksheet label) → React SocialSecuritySection inputs + railroad
  checkbox + Medicare destination select → `rules_retirement.py` D_RET_009 → 2 flow assertions → tests.

---

## 2026-06-29 — 1040_RETIREMENT: SS LUMP-SUM amendment SEEDED + EXPORTED (Ken go-ahead) — unit complete in tts
- Ken gave the in-session **"seed now, then build"** go-ahead. Ran `load_1040_retirement` against RS's own
  Supabase (`ylqaejdqwuvwpglxnpgv`) — idempotent (`update_or_create`); 1040_RETIREMENT now 35 facts / 11 rules /
  26 lines / 8 diagnostics / 20 scenarios / 15 links; FlowAssertions 333 total. DB totals: 74 forms / 1666 facts /
  637 rules / 419 diagnostics. Both integrity gates still report "all rules have authority links."
- Re-exported the deployed lookup endpoint (`/api/forms/lookup/1040_RETIREMENT/export/`) → overwrote the canonical
  tts `server/specs/retirement_spec.json` (now carries the `lse_*` facts/rules/lines + D_RET_008 + the LSE-1/LSE-2
  tests). Verified lse_ws2_21 / lse_ws4_21 / ss_lump_sum_election / R-RET-LSE-WS4 present.
- tts side: re-seeded `1040_RETIREMENT` (added the lse_ws2_21/lse_ws4_21 pseudo-rows to the hardcoded
  `seed_1040_retirement.py`) and built the RENDER + INPUT + DB-test legs. **tts unit COMPLETE — tag
  `1040-ss-lumpsum-complete`.**
- STILL OPEN (RS hygiene): re-seed `load_4797` on the next RS deploy (covers both the 6252 + 8824 amendments; the
  deployed RS DB still has D_4797_003/004 active). The lump-sum amendment is now seeded; the 4797 one is not.

---

## 2026-06-28 — 1040_RETIREMENT amendment: SS LUMP-SUM ELECTION (Pub 915 WS2+WS4) — SPEC + MATH GATE GREEN (seed pending Ken go-ahead)
- **Retiree-hardening cluster, item 1 (D_RET_004).** Ken-directed (tts AskUserQuestion: chose D_RET_004 first +
  the EXPLICIT-TOGGLE election behavior, irrevocable-without-IRS-consent). Amended `load_1040_retirement.py`:
  the Pub 915 Lump-Sum Election is now COMPUTED, no longer the blanket RED-defer.
- **Added to 1040_RETIREMENT:** new authority source `IRS_2025_PUB915` (verbatim Worksheets 1/2/4 + the
  Terry Jackson worked example, `requires_human_review=True`); facts `ss_lump_sum_election` (toggle) + 9
  `lse_*` per-earlier-year facts; rules `R-RET-LSE-WS2` / `R-RET-LSE-WS4` / `R-RET-LSE-ELECT`; lines
  `lse_ws2_21` / `lse_ws4_21`; **D_RET_004 repurposed** (blanket RED → no-silent-gap "earlier-year data
  missing" guard) + new **D_RET_008** (WS1-vs-WS4 comparison/savings, severity adapts tts-side); scenarios
  LSE-1 (Terry, election 2,500 < regular 3,000 → beneficial) + LSE-2 (high earlier-year income → WS4 4,200 >
  WS1 3,000 → not beneficial); `FA-1040-RET-08`.
- **Counts now:** 1040_RETIREMENT 35 facts / 11 rules / 26 lines / 8 diagnostics / 20 scenarios / 15 links;
  flow assertions 8. `check_retirement_integrity.py` extended with an INDEPENDENT WS2/WS4 transcription
  (`_ss_tiers`/`ws2_additional`/`ws4_lse`) + LSE-1/LSE-2 checks + load-bearing benefit pins → **ALL CHECKS PASS**.
- LAW VERIFIED 2026-06-28 vs the actual **Pub 915 (2025) PDF** (pages 10-19, pymupdf dump): Worksheets 1/2/4
  + the Lump-Sum Election method + the filled-in Terry example (reconciles to the dollar).
- **Method:** WS2 (per earlier year, post-1993) refigures that year's taxable benefits WITH the lump-sum
  portion added (L1 = earlier-year box5 + lump-for-year), subtracts the previously-reported taxable benefits
  (already inside AGI), → additional taxable benefits (L21). WS4 re-runs the 2025 worksheet with box5 reduced
  by Σ(pre-2025 lump sums), then adds Σ WS2 L21. Elect (6b = WS4 L21, check 1040 box 6c) only when the toggle
  is on; D_RET_008 surfaces whether it beats WS1. WS3 (pre-1994) RED-deferred (vanishingly rare).
- **READY_TO_SEED stays True** (form already approved+seeded 2026-06-11). The new lump-sum content is NOT yet
  seeded to the RS DB nor re-exported to `tts/server/specs/retirement_spec.json` — **pending Ken's in-session
  seed go-ahead** (he approved the substance; this is the formal flip-equivalent for the amendment).
- **NEXT (tts):** build the unit — `SocialSecurityLumpSum` model + `ss_lump_sum_election` on Taxpayer (migration)
  → `compute_ss_lumpsum.py` (WS2/WS4, supersede 6b) → render statement + 1040 box 6c → input/serializer/CRUD/React
  → `rules_retirement.py` D_RET_004 rewrite + D_RET_008 → flow assertion → tests (LSE-1/LSE-2). D_RET_005
  (IRA-deduction↔SS circular) + D_8606_NO_YEAREND remain the other two cluster items.

---

## 2026-06-28 — FORM 8824 (Like-Kind Exchanges + §1043) — SPEC AUTHORED + INTEGRITY GREEN + SEEDED ✅ (Ken approved)
- **Ken chose (tts AskUserQuestion): "Full incl. Part IV + computed recapture"** — the WHOLE Form 8824.
  New loader `load_8824.py` (form_number "8824", entity_types ['1040'], v1 — lookup was 404, brand-new
  form) in the modern pattern (module-level `compute_8824()` + `FORMS` + `FLOW_ASSERTIONS`) +
  `check_8824_integrity.py` (independent re-typed §1031 math).
- **Form 8824 v1: facts 41 / rules 7 / lines 35 / diagnostics 10 / scenarios 11 / links 14 / 9 flow
  assertions / 6 authority sources.** `check_8824_integrity.py` → **ALL CHECKS PASS** (independently
  recomputed + cross-checked vs the loader AND the i8824 worked examples: Taylor §1245 L21 35000→4797
  L16 / L22 5000→4797 L5; Finley §1250 L21 30000, 25a 131250 / 25b 43750; loss −20000 deferred; §1043
  L37 130000; §1031(f) accel 60000). The gate caught one authored test-value error (T6 L19 50000→80000).
- **Model:** Part III §1031 — §1.1031(d)-2 symmetric liability netting (computed from components),
  L19 realized = L17−L18, L20 = max(0,min(L15,L19)), **COMPUTED** recapture L21 via §1245(b)(4)
  (min(min(depr,L19), L20+(L16−fmv1245))) + §1250(d)(4) (min(addl, max(L20, addl−fmv1250))) → 4797
  line 16; L22 → 4797 line 5 (business §1231 >1yr) / line 16 (ordinary) / Schedule D (capital);
  L23=L21+L22, L24 deferred (a LOSS defers in full, never deducted), L25=(L18+L23)−L15 + 25a/b/c
  proportional. Part II §1031(f) 2-year acceleration (prior-year L24 preparer-asserted). Part IV §1043
  L32/L34/L35→4797 L10/L37/L38 (L35 recapture preparer-asserted per i8824 worksheet method).
- **CLOSES the live Form 4797 D_4797_004 like-kind RED-defer** (L21→4797 L16, L22→4797 L5), same
  pattern the 6252 unit used to retire the 4797↔6252 defer. (D_4797_004 closure = the tts COMPUTE/
  DIAGNOSTICS leg follow-up.)
- **v1 RED-defers (no silent gap):** multi-asset exchange (D_8824_007), §121 main-home combo
  (D_8824_008), personal property (D_8824_009 — post-2017 §1031 is real-property only). 45/180-day
  deferred-exchange deadline diagnostics (D_8824_001/002). **No year-keyed constants** (pure arithmetic
  → TY2026 = TY2025 identical). OBBBA §1062 farmland-gain deferral (Form 1062) is a SEPARATE adjacent
  form, NOT part of 8824 — flagged to Ken, not built.
- LAW VERIFIED 2026-06-28 vs the actual **f8824.pdf (2025, both pages)** + **i8824.pdf (2025, 7 pages,
  incl. the Taylor/Finley liability-netting + §1245(b)(4)/§1250(d)(4) recapture + 25a/b/c examples)** +
  IRC §1031/§1031(f)/§1245(b)(4)/§1250(d)(4)/§1043 + Pub 544.
- **Ken APPROVED the review walk (2026-06-28)** → flipped `READY_TO_SEED=True` → seeded RS DB (TaxForms
  → 74, FlowAssertions → 332; "all rules cited") → exported `tts/server/specs/form_8824_spec.json` (v1)
  + staged `flow_assertions_1040_8824_pending.json` (9 FA).
- **NEXT (tts):** build the 6 legs — COMPUTE (`compute_8824.py`, port of `m.compute_8824`, wired so
  L21→4797 L16 + L22→4797 L5 CLOSE D_4797_004) → RENDER (f8824 PDF already in resources/2025; add
  manifest entry) → DIAGNOSTICS (`rules_8824.py` 10 D_8824_*) → INPUT → ASSERTIONS (9 FA → gate
  347→356). Reuse the 6252/4797 cross-form-feed pattern.
- **RS hygiene carryover (still open from 2026-06-28 6252 session):** `load_4797.py` amended +
  integrity-verified but the deployed RS was NOT re-seeded/re-exported for the 4797 amendments — do that
  on the next RS deploy alongside this 8824 seed (load_4797). (This 8824 seed DID write to the shared
  RS Supabase, so the 8824 export endpoint is live.)

### 2026-06-28 (later, tts 8824 COMPUTE leg) — load_4797.py AMENDED to CLOSE D_4797_004 (twin of the 6252 closure)
- `load_4797.py` `compute_4797` now accepts `like_kind_line5/16/10` feeds (Form 8824: recognized §1231
  gain → Part I line 5; ordinary recapture/gain → Part II line 16; §1043 ordinary → line 10) and no
  longer RED-defers on `has_form_8824`. Marked `D_4797_004` + `f4797_has_form_8824` RETIRED (now
  supported); dropped `form_8824_like_kind` from FA-1040-4797-07's blocker list (only `form_4684_casualty`
  remains). `check_4797_integrity.py` → **ALL CHECKS PASS** (11 scenarios; the additive feed params don't
  touch any existing scenario). 4684 casualty interplay still RED-defers.
- **Pending re-seed now covers BOTH the 6252 AND 8824 4797 amendments** — re-run `load_4797` on the next
  RS deploy (the deployed RS DB still has the old D_4797_003/004-active rows). The canonical tts
  `form_4797_spec.json` was mirrored by hand (D_4797_004 + fact retired-text). No other RS form touched.

## 2026-06-28 — FORM 4797 amended to CLOSE the 6252 RED-defer (tts Form 6252 compute leg)
- During the tts-tax-app Form 6252 (Installment Sale Income) COMPUTE leg, **Ken chose "fully retire the
  flag"** (close the 4797↔6252 RED-defer rather than keep `f4797_has_form_6252` as a manual escape hatch).
- **`load_4797.py` amended** (byte-for-byte twin of the tts `compute_4797`): `compute_4797` now accepts
  `installment_line4/10/15` feeds (§1231 → Part I line 4; ordinary → Part II line 10; ordinary recapture →
  Part II line 15) and no longer RED-defers on `has_form_6252`. Removed the `F4797-G2` (6252 → RED-defer)
  scenario; dropped `form_6252_installment` from FA-1040-4797-07's blocker list; marked the `D_4797_003`
  diagnostic + `f4797_has_form_6252` fact RETIRED (now supported). 4684/8824 interplays still RED-defer.
- **`check_4797_integrity.py` → ALL CHECKS PASS** (now 11 scenarios; the §1231 netting + 5-yr lookback +
  §1245/1250/1252/1254/1255 recapture re-verified). The independent recompute was untouched (existing
  scenarios pass no installment feeds → unchanged).
- **NOT YET re-seeded to the RS Supabase / re-exported via the lookup endpoint** (the loader is the source of
  truth and is integrity-verified; the canonical tts `form_4797_spec.json` was mirrored by hand to match —
  F4797-G2 removed, D_4797_003 + fact retired-text). **Pending hygiene: re-seed `load_4797` + re-export on the
  next RS deploy** so the deployed RS DB matches the amended loader. No other RS form touched.

## 2026-06-27 — FORM 4797 (Sales of Business Property) — SPEC REWRITTEN + INTEGRITY GREEN + SEEDED ✅ (Ken approved)
- **Ken chose (tts AskUserQuestions): the full Form 4797, then "Broad v1"** (Parts I-IV, all five
  recapture sections). REWROTE `load_4797.py` from the old "first form for validation" BaseCommand
  draft to the modern pattern (module-level `compute_4797()` + `FORMS` + `FLOW_ASSERTIONS`), so
  `check_4797_integrity.py` can re-type the math. SHARED form — form_number "4797", entity_types
  ['1120S','1065','1120','1040'] PRESERVED.
- **Form 4797 v2: facts 25 / rules 6 / lines 34 / diagnostics 7 / scenarios 12 / links 12 / 7 flow
  assertions / 8 authority sources.** `check_4797_integrity.py` (independent re-typed recapture math)
  → **ALL CHECKS PASS** (T1 §1245 all-ord 10000 / T2 excess→Sch D 20000 / T5 unrecap §1250 100000 /
  T6 lookback L9 12000 L18b 38000 / T7 §1252 18000 / T8 §179 7000).
- **Broad-v1 math:** §1245 L25b = min(gain, depr); §1250 L26g = applic% × min(gain, 26a add'l depr),
  unrecaptured §1250 = min(gain, depr) − §1250-ord (→ Sch D worksheet, 25%, NOT a 4797 line); §1252/
  1254/1255 = min(gain, section amount) (applic% preparer-entered); §1231 netting + §1231(c) 5-yr
  lookback: L12 ord = min(L7,L8), L9 = max(0,L7−L8) → Schedule D line 11; Part IV §179/§280F L35 →
  Schedule 1 line 4. Routing: L18b + Part IV → Sch 1 L4; L9 → Sch D L11; L18a → Sch A L16 (v1=0).
- **Ken's 3 tax-law calls (approved in-session):** §1231 lookback = preparer-asserted fact (default 0);
  §1250 26a additional depreciation = preparer-entered (default 0 = post-1986 SL); §179/§280F → Sch 1
  L4 + SE-nuance INFO diag (auto SE add-back RED-deferred).
- **v1 RED-defers (no silent gap):** Form 4684 casualty, Form 6252 installment, Form 8824 like-kind.
- Verified Part III structure line-by-line vs the real **f4797.pdf (182 fields)** + i4797 (the field-map
  COMMENTS were wrong: 25a/b=§1245, 26a-g=§1250, 27=§1252, 28=§1254, 29=§1255). Authority: IRC §1231/
  1245/1250/1252/1254/1255 + §1(h)(1)(E) + §179(d)(10)/§280F(b)(2), i4797, Pub 544.
- **SHARED-FORM SEEDING GOTCHA:** the export serves `order_by('-version').first()` = v2; the DB had TWO
  identical old-draft rows (v1+v2). Set FORM_VERSION=2 to update the SERVED row. update_or_create left
  the old draft's children (R001-R010 rules, prefix-less facts, D001-D005, lines 19/26/27, 6 old tests)
  alongside the new → "uncited rules: 9". FIX: PURGED all v2 children then re-seeded clean → "all rules
  cited". (Lesson: amending an existing draft form needs a child-purge, not just update_or_create.)
- **Ken APPROVED the review walk (2026-06-27)** → flipped `READY_TO_SEED=True` → seeded RS DB (TaxForms
  72, FlowAssertions 308→315) → exported `tts/server/specs/form_4797_spec.json` (v2).
- **NEXT (tts):** build the 6 legs — COMPUTE (`compute_4797.py`, port of `m.compute_4797`, wired BEFORE
  Schedule D netting; unrecaptured §1250 → the Topic-9 SDTW worksheet) → RENDER → DIAGNOSTICS → INPUT →
  ASSERTIONS. Reuse the existing `Disposition` model (is_4797 flag) + `resolve_recapture_type`.

---

## 2026-06-26 — FORM 1116 (Foreign Tax Credit) — SPEC AUTHORED + INTEGRITY GREEN + SEEDED ✅ (Ken approved)
- **Ken chose (tts AskUserQuestions): FULL Form 1116, then "Tighter v1 — Passive-only".** New loader
  `load_1040_form_1116.py` (form_number `FORM_1116`) + `check_1116_integrity.py` (independent re-typed
  math gate, the 2210 precedent). RS endpoint was 404 (greenfield, locally authored).
- **FORM_1116: facts 19 / rules 5 / lines 32 / diagnostics 8 / scenarios 10 / links 8 / 7 flow
  assertions / 3 authority sources.** `check_1116_integrity.py` → **ALL CHECKS PASS** (T1 election 250 /
  T2 MFJ 550 / T4 limit-binds 1361 cf 139 / T5 full-credit 1000 cf 0 / T8 L17<=0 → 0 cf 200).
- **Two paths:** Path A — §904(j) election (all passive + payee-statement + foreign tax ≤ $300/$600 →
  credit = min(foreign tax, regular tax) → Sch 3 L1, no carryover). Path B — full Passive §904
  limitation (Part I L7 deduction apportionment → Part III L21 = L20 × L17/L18 → L24 = min(L14,L23) →
  Part IV L35 → Sch 3 L1; carryforward = max(0, L14−L24)). L18 = 1040 line 15 + Sch 1-A line 37 (the
  SENIOR deduction only — verified i1116). L20 = 1040 L16 + Sch 2 L1z.
- **v1 RED-defers (8 diagnostics, no silent gap):** non-passive category, the above-exception QD
  adjustment (foreign QD+gain ≥ $20k OR TI > threshold), Form 2555 reduction, carryover→Schedule B
  (warn), TY2026 threshold re-verify (warn), election-over-ceiling.
- Verified line-by-line vs the real **f1116.pdf (created 9/16/25) + i1116.pdf (Dec 23 2025)**
  (`tts/server/specs/_1116_source_brief.md`). Authority: IRC §901/§904/§904(j), Reg §1.904(b)-1, Pub 514.
- Constants: §904(j) $300/$600 (statutory); adj-exception TI $394,600 MFJ / $197,300 other (2025
  verbatim; 2026 interim = §199A $403,500/$201,750, flagged D_1116_007); adj-exception gain ceiling
  $20,000 (regulatory).
- **Ken APPROVED the review walk (2026-06-26)** → flipped `READY_TO_SEED=True` → seeded the RS DB
  (TaxForms 72, FlowAssertions 308, all rules cited) → exported `tts/server/specs/1116_spec.json`.
- **NEXT (tts):** build the SEED leg (Form1116 model + migration + CRUD + f1116 PDF/manifest) →
  compute → render → input → diagnostics → assertions. Target: Schedule 3 line 1 flips to computed.

---

## 2026-06-25 — FORM 5329 FULL (Parts I–IX) — SPEC AUTHORED + INTEGRITY GREEN ⏳ (NOT seeded — awaiting Ken's review)
- **Ken chose (tts AskUserQuestions): FULL Form 5329 (all Parts I–IX) + DUAL taxpayer/spouse.**
  Expanded the `F5329_*` blocks IN PLACE in `load_1040_retirement.py` (the loader already owns
  form_number "5329"; no 2nd loader — avoids double-ownership). Spec is **owner-agnostic** (one
  logical form); DUAL is a tts-side model concern.
- **5329 form now (was 3/3/4/1/3): facts 37 / rules 12 / lines 58 / diagnostics 4 / scenarios 10
  / links 14.** Added Parts II (edu/ABLE 10%), III–VIII (excess contributions 6% of the smaller of
  total-excess or 12/31 value, prior-year carryforward chain), IX (excess accumulation / missed RMD
  — SECURE 2.0 10% window / 25% other). `R-5329-12` aggregates all parts → Schedule 2 line 8
  (replacing the Part-I-only feeder). Widened the line-2 exception catalog **01–12+19 → 01–23+99**
  (i5329 table, incl. SECURE 2.0 codes 20/22/23); `D_RET_006` flipped from ">12 unsupported" to a
  validity guard (out of 01–23/99); `RET-G5` fixture exception 13→25 (13 is now valid §457).
- **`check_retirement_integrity.py` extended** (`f5329_full` recomputes all 9 parts; F5329-T1..T10
  scenarios incl. capped-vs-uncapped, the 10%/25% split, the all-parts Sch 2 L8 sum; +3 load-bearing
  pins). **ALL CHECKS PASS.**
- Verified line-by-line vs the real **f5329.pdf + i5329.pdf** (2026-06-25;
  `tts/server/specs/_5329_full_source_brief.md`). Authority: IRC §§72(t)/4973/4974, SECURE 2.0 §302,
  Notices 2024-02/2024-55.
- **PENDING:** Ken's review walk → then re-seed the RS DB (run `load_1040_retirement`) → export
  `5329_spec.json` → tts build legs. `READY_TO_SEED` is already True (retirement spec), so the gate
  here is DISCIPLINE: do not run the loader until Ken approves the 5329 expansion.

## 2026-06-25 — FORM 1040-X (Amended Returns) — APPROVED + SEEDED + EXPORTED ✅
- **Ken APPROVED the W1-W6 review walk in-session** (W1 amend-in-place + dedicated as-filed
  baseline / W2 col-B = C−A / W3 refund-owe 17-23 / W4 confirm the deferrals — NOL/GBC
  carrybacks + superseding + multi-form cascades RED-defer / W5 year / W6 Part II required).
  Flipped `READY_TO_SEED=True` → seeded RS DB (12 facts/12 rules/61 lines/8 diag/2 tests/6 FA)
  → exported canonical `tts/server/specs/1040x_spec.json`. Integrity gate ALL PASS. RS `957a9d6`.
- tts compute leg built on the approved spec (compute_1040x + render_1040x + rules_1040x + 6
  FA-1040X merged); full 1040-X suite 343 passed; **tag `1040x-complete`**.

## 2026-06-25 — FORM 1040-X (Amended Returns) — AUTHORED (READY_TO_SEED=False) ⏸️
- **NEW spec `load_1040_form_1040x.py`** (remote-safe spec+scaffold pass; the tax-law
  delta-compute leg waits for Ken). Form 1040-X = a three-column A/B/C delta over a filed
  1040: Column A = original/as-filed (from a frozen `AsFiledBaseline` snapshot, tts side),
  Column C = correct (the amended 1040), Column B = net change (C − A); recompute subtotals
  (3/5/8/11) + amended refund/owe (17-23) + Part II explanation.
- **12 facts / 12 rules / 61 lines / 8 diagnostics / 2 scenarios / 6 FA.** Line set verified
  against the ACTUAL Form 1040-X (Rev. December 2025) PDF — read directly from
  tts/resources/irs_forms/2025/f1040x.pdf (widget dump + text), NOT memory. RED-defers NOL
  carryback (D_1040X_001), GBC carryback (002), superseding (003), missing baseline (005),
  blank explanation (004), other-credit cascades (008).
- **`check_1040x_integrity.py`** — independent recompute (B=C−A + subtotals + refund/owe) re-
  derives both scenarios + structural checks (no dup ids, rule_links resolve, expected_outputs
  reference real lines, id≤20). **ALL CHECKS PASS.** The seed command correctly REFUSES
  (`READY_TO_SEED=False`). W1-W6 review-walk items in the loader docstring for Ken.
- **NOT seeded / NOT exported** — awaiting Ken's review (REVIEW_QUEUE.md). RS `4ba236c`.

---

## 2026-06-25 (later) — GA FORM 500 — page-5 line-number fix + HB 463 TY2026 constants ✅
- **Amended `load_ga500_form_500.py` + `check_ga500_integrity.py`** (the spec was WRONG on the
  page-5 line numbers, verified vs the actual GA-DOR 2025 Form 500 PDF page 5). Corrected to the
  form face: **L42 = UET penalty, L43 = late-payment penalty, L44 = Interest, L45 = AMOUNT DUE
  (= L29 + Σ lines 32-44), L46 = REFUND (= max(0, L30 − Σ lines 31-44))**; added the 10 gift
  check-offs (L32-41) + late-penalty/interest facts. The prior spec mis-keyed UET as "44" and
  never modeled L45. Extended `recompute()` to cover L28-46 + 2 new scenarios (T13 refund / T14
  amount-due). Integrity gate ALL PASS (**14 scenarios**). RS `14e4410`.
- **HB 463 TY2026 standard deduction corrected** (was still $12k/$24k for 2026): GA_STD_DED_MFJ
  [2026] 24000→30000, GA_STD_DED_OTHER[2026] 12000→15000 (loader + integrity). Dependent
  exemption $5,000 was already right. **Effective-year CONFIRMED WITH KEN** (sources conflicted:
  BIP Wealth/BDO = TY2026 vs GBPI = TY2027; Ken chose TY2026 — verify vs the bill text later).
  Scenario T11 recomputed (tax 2994). RS `fd9ebc9`.
- **Re-seeded RS DB** (deleted a stale renamed-T11 orphan first; `manage.py shell`) → **re-exported
  the canonical `tts/server/specs/500_spec.json`** (77 facts / 21 rules / 89 lines / 12 diag / 14
  tests). Deployed export reflects it (same Supabase RS DB). Implemented on the tts side (seed/
  compute/render/diagnostics); GA-500 tag `ga500-complete`.

---

## 2026-06-25 — GA FORM 500 (Georgia Individual Income Tax) — AUTHORED + SEEDED + EXPORTED ✅
- NEW form (Ken's direction after Form 8615 completion). **No prior RS spec** — `lookup/500`,
  `GA_500`, `GA500` all → 404. The **FIRST STATE individual spec** (all prior specs federal).
- **Verified against the GA-DOR 2025 Form 500 (Rev. 07/09/25) + 2025 IT-511 booklet (extracted
  from the actual PDFs, read directly) + O.C.G.A. Title 48 Ch. 7 + HB 111 (TY2025 rate) + HB 463
  "Georgia Economic Growth and Tax Relief Act of 2026" (TY2026), NOT memory.** Georgia Form 500:
  federal AGI (1040 L11) → Schedule 1 GA additions/subtractions (the retirement income exclusion
  is the center of gravity) → standard/itemized deduction → dependent exemption → GA NOL (Sch 4,
  80% limit) → flat tax → credits → withholding → refund/due.
- **v1 scope LOCKED (Ken, 4 AskUserQuestion decisions 2026-06-25 — MAXIMAL):** (1) resident **+
  part-year/nonresident** (Schedule 3 proration); (2) **both** retirement exclusions (standard RIE
  + military); (3) **compute Schedule 4 GA NOL** (Part I/II + 80% limit); (4) credits direct-entry
  **+ compute the Low Income Credit + IND-CR 202 child-care** (50% of the federal §21). The
  §168(k)/§179/OBBBA depreciation difference (Sch 1 L3/L11) = preparer DIRECT-ENTRY in v1 (GA
  conforms to the IRC as of 1/1/2025, NOT OBBBA; engine integration later — W1). RED-defers the UET
  penalty + the multi-year NOL carryover application.
- **CONSTANTS verified:** rate 5.19% (2025, HB 111) / 4.99% (2026, HB 463); std ded $24,000 MFJ /
  $12,000 else (no age-65/blind add-on, no personal exemption — HB 1437); dependent exemption
  $4,000 (2025) / **$5,000 (2026, HB 463 eff. TY2026)**; retirement exclusion $35,000 (62-64/
  disabled) / $65,000 (65+), ≤$5,000 earned; military $17,500 base → $35,000; LIC table
  $26/$20/$14/$8/$5 by FAGI bracket (< $20,000). Std-ded + retirement-exclusion bumps start 2027.
- `load_ga500_form_500.py` = **75 facts / 20 rules / 76 lines / 12 diagnostics / 12 tests / 21
  rule-links / 12 FA / 4 sources** (+ ref IRS_2025_1040_FORM). The project's largest spec.
  `check_ga500_integrity.py` **ALL CHECKS PASS** — constants (2 yrs) + helpers + the LIC table +
  all 12 scenarios (the Form 500 assembly: Sch 1 / RIE std+military / deduction / Sch 3 / NOL 80% /
  flat tax / LIC / child-care) re-derived independently; loader + gate share no math. Full source
  brief: `tts-tax-app/server/specs/_ga500_source_brief.md`.
- **READY_TO_SEED = True** — Ken **APPROVED the review walk in-session 2026-06-25** ("Approve as
  drafted — seed + export"; W1-W6 all blessed). **SEEDED** (`manage.py load_ga500_form_500` →
  Created 500; 75 facts / 20 rules / 21 authority links / 76 lines / 12 diagnostics / 12 tests /
  12 FA / 5 sources). **EXPORTED** the canonical spec → `tts-tax-app/server/specs/500_spec.json`
  (82 KB; facts 75 / rules 20 / line_map 76 / diagnostics 12 / tests 12) + the 12 staged
  `flow_assertions_1040_ga500_pending.json` (FA-GA500-01..12). **NEXT: the tts-tax-app BUILD legs
  (seed model/migration → compute → render → input → diagnostics → assertions) — GA 500 attaches
  to the child 1040 via the `state_returns` FK (the GA-600S precedent).**

---

## 2026-06-24 — FORM 8615 (Kiddie Tax §1(g)) — DRAFTED + GATE PASS — AWAITING KEN'S REVIEW WALK ⏳
- NEW form (Ken chose it after 8829, from a Phase-0 finding that the whole SPRINT_SCOPE
  NEXT-UP federal backlog is already built). **No prior RS spec** — `lookup/8615`,
  `FORM_8615`, `1040_8615` all → 404.
- **Verified against i8615 (2025) + f8615 (read directly) + IRC §1(g) + §63(c)(5)(A) +
  §1(h); 2026 constants from Rev. Proc. 2025-32 §3.02/§3.18 (read the PDF directly), NOT
  memory.** The kiddie tax: Part I net unearned income = min(unearned − $2,700, taxable
  income); Part II tentative tax at the PARENT's rate (tax on net unearned + parent TI +
  other children's net unearned − the parent's tax, allocated by L5 ÷ (L5+L7)); Part III
  child's tax = LARGER of (parent-rate share + child-rate tax on the rest) vs (child-rate
  tax on all) → child's 1040 line 16.
- **Scope LOCKED (Ken, 2 AskUserQuestion decisions 2026-06-24):** (1) parent data =
  preparer-asserted facts on the child's return (no parent-return link in v1); (2) cap-gains
  = FULL QDCGT reuse (`compute_qdcgt_worksheet` + i8615 Line 5 worksheets, parent/child
  `ordinary_tax_fn`), RED-defer ONLY §1250/28% SDTW (+ Schedule J + Form 8814 election).
- **CONSTANTS verified:** §63(c)(5)(A) base = $1,350 BOTH 2025+2026 (unchanged) → line 2 /
  threshold = $2,700 both years. Rate schedules / QDCGT breakpoints REUSE the existing
  year-keyed constants (lines 9/15/17 tax-at-rate values are the reuse; the spec owns the
  §1(g) assembly).
- `load_1040_form_8615.py` = **30 facts / 11 rules / 18 lines / 7 diagnostics / 8 tests /
  16 rule-links / 9 FA**. `check_8615_integrity.py` **ALL CHECKS PASS** (the §1(g) assembly
  + constants + helpers re-derived independently; loader + gate share no math). Full source
  brief: `tts-tax-app/server/specs/_8615_source_brief.md`.
- **READY_TO_SEED = False** — the loader REFUSES to seed (zero DB writes) until Ken's
  in-session review walk (W1 the §1(g) assembly + max(L16,L17); W2 the preparer-asserted
  parent data; W3 the QDCGT-in/SDTW-out boundary; W4 the Line 5 worksheet posture [spec the
  principle, transcribe the WS lines at compute]; W5 the L13 precision; W6 the constants).
  **NEXT: Ken reviews → flip READY_TO_SEED → seed → deploy export → canonical
  `8615_spec.json` + 9 staged FA.**

---

## 2026-06-24 — FORM 8829 (Business Use of Home) — AUTHORED + SEEDED + EXPORTED ✅
- NEW form after the quick-wins bundle (Ken chose Form 8829 home office, then "BROADER:
  build the Schedule A split"). **No prior RS spec** — `lookup/8829/export/` → 404.
- **Verified against the actual 2025 f8829.pdf (read directly) + i8829 (Rev. Mar 4 2026)
  + IRC §280A(c)(5) + §168/Pub 946, NOT memory.** The actual-expense home-office engine:
  Part I business % (area + daycare hours-of-use) → the §280A(c)(5) gross-income limitation
  in 3 ordered tiers (deductible-anyway 9-14 → operating 16-27 → casualty+depreciation
  29-33, each limited to the income remaining; depreciation last → carries over first) →
  line 36 → Schedule C line 30; Part III 39-yr nonresidential mid-month SL depreciation
  (Jan 2.461%…Dec 0.107% first year, 2.564% subsequent); Part IV carryover.
- **Scope LOCKED (Ken, AskUserQuestion "Approve as drafted"):** v1 COMPUTES the RE-tax
  SALT split (lines 11/17) reusing `compute_schedule_a.salt_line5e` (the OBBBA $40k cap +
  $500k-MAGI 30% phasedown) incl. the >$500k circular MAGI↔home-office↔AGI iteration
  (W4 = fixed-point loop). The MORTGAGE Pub-936 split (10/16) stays a preparer fact for
  itemizers (W3 — matches Schedule A; the standard-deduction path is computed). RED-defers
  line-35 → Form 4684 + the multi-business line-36 allocation (W5).
- `load_1040_form_8829.py` (the `load_1040_form_6251` template): **47 facts / 13 rules /
  44 lines / 8 diagnostics / 11 scenarios / 9 FA / 20 authority links / 4 sources** (+ ref
  IRS_2025_1040_FORM). `check_8829_integrity.py` math gate **ALL CHECKS PASS** — the
  depreciation table (12 months + subsequent) + daycare + SALT constants + helpers + all
  11 scenarios re-derived independently (caught + fixed 2 self-authored scenario errors:
  itemizer line 11/17 are col (a) pre-allocated, not col (b) × business %). RS `b933b6e`.
- **Ken APPROVED the review walk in-session ("Approve as drafted")** — W1 §280A tier
  ordering; W2 39-yr nonresidential mid-month depreciation; W3 itemizer-mortgage-split-as-
  input; W4 the MAGI fixed-point loop; W5 casualty/4684; W6 constants reused from Sch A.
  FLIPPED `READY_TO_SEED` → seeded (RS DB: Created 8829) → deployed export verified
  (`lookup/8829/export/` HTTP 200; 47/13/44/8/11) → canonical `server/specs/8829_spec.json`
  committed to tts-tax-app + 9 FA staged in `flow_assertions_1040_8829_pending.json`.
- **Next (tts-tax-app): the 6 build legs (seed → compute → render → input → diagnostics →
  assertions).** Build leg 1 = model fields (Form8829 per Schedule C) + migration + manifest
  f8829 + download PDF + seed_8829 + serializer.

## 2026-06-24 — FORM_2441 — claims_dependent_care claim gate (amend; NOT re-seeded yet)
- tts-tax-app quick-win (Ken chose "amend spec + gate compute"): the per-Dependent
  `claims_dependent_care` checkbox is now the AUTHORITATIVE claim election for the §21
  credit. Previously R-2441-QUALIFYING counted qualifying persons by `care_expenses > 0 +
  (under-13 OR disabled)` only — a qualifying-but-unclaimed dependent computed a credit.
- **Loader amended** (`specs/management/commands/load_1040_form_2441.py`): R-2441-QUALIFYING
  formula/description/inputs now gate on `claims_dependent_care`; NEW `claims_dependent_care`
  fact (boolean, sort 6); NEW diagnostic **D_2441_007** (info) — a qualifying dependent with
  care expenses but not claimed → no credit computed (no silent gap). check_2441_integrity.py
  unaffected (it recomputes the worksheet from `qualifying_count` as input; the gate is upstream).
- **NOT re-seeded / re-exported** this session (no local RS DB run from the tts-tax-app session).
  The canonical `form_2441_spec.json` in tts-tax-app was hand-amended to match the loader and is
  green there (flow gate 282→283, FA-1040-2441-07; 2441 tests 36/36). **TODO next RS deploy:**
  run `load_1040_form_2441` + `check_2441_integrity.py`, re-export `lookup/FORM_2441/export/`,
  and diff against the tts-tax-app canonical spec to confirm zero drift.

## 2026-06-23 — FORM 6251 (Alternative Minimum Tax) — AUTHORED + SEEDED + EXPORTED ✅
- Next Tier-2 unit after 8995-A (Ken chose the AMT engine). **No prior RS spec** —
  `lookup/6251/export/` returned 404 (a genuinely NEW form, not a re-author).
- **Scope LOCKED (Ken, AskUserQuestion): "common-case engine"** — v1 computes the SALT/
  std-deduction add-back (2a) / PAB (2g) / AMT depreciation (2l) / refund (2b) / exemption +
  phaseout / Part II 26-28% TMT / Part III AMT cap-gains → AMT = max(0, TMT − regular tax)
  → Schedule 2 line 2. RED-defers ISO (2i), QSBS (2h), NOL (2e/2f), estates/trusts (2j), the
  exotic preferences (2c/2d/2k/2m/2n/2o-2t/3), and the AMT FTC (line 8).
- **Verified against the actual 2025 f6251.pdf (read directly via pymupdf — Part I 1a-4 incl.
  all 2a-2t, Part II 5-11, Part III 12-40 AMT cap-gains worksheet) + i6251 + IRC §§55-59 +
  OBBBA §70107, NOT memory.** AMTI base (Ken-confirmed): regular taxable income + std-deduction/
  SALT add-back + senior-deduction add-back; QBI retained. Constants both years: 2025
  exemption 88,100/137,000/68,500 @ phaseout 626,350/1,252,700 × 25%; **2026 OBBBA**
  90,100/140,200/70,100 @ **500,000/1,000,000 × 50%** (the phaseout reversion + rate doubling).
- `load_1040_form_6251.py` (the `load_1040_form_8995a` template): **25 facts / 14 rules /
  38 lines / 8 diagnostics (6 RED-defer D_6251_* + AMT-applies info + Part III basis-diff warn) /
  10 scenarios / 9 FA + 25 authority links**. `check_6251_integrity.py` math gate **ALL CHECKS
  PASS** — constants (both years × 3 statuses) + helpers + all 10 scenarios re-derived
  independently (caught + fixed 4 scenario arithmetic errors). RS `b8d3333` (author) + the flip.
- **Ken APPROVED the review walk in-session ("approve and seed")** — W1-W6 blessed as drafted
  (W1 AMTI base; W2 the 2026 OBBBA $90,100/$140,200/$70,100 + $500k/$1M @ 50%; W3 RED-defer scope;
  W4 Part III reuse; W5 line-10 no-Schedule-J; W6 D_AMT_DEFER narrowing). FLIPPED `READY_TO_SEED`
  → seeded (RS DB +1 form `6251`; 25/14/38/8/10/9 + 25 links + 1 topic + 6 sources) → deployed
  export verified (`lookup/6251/export/` HTTP 200, counts + OBBBA $500k + all 8 D_6251_*) →
  canonical `server/specs/6251_spec.json` committed + 9 FA staged in
  `flow_assertions_1040_6251_pending.json`.
- **Next (tts-tax-app): the 6 build legs (seed → compute → render → input → diagnostics →
  assertions).**

## 2026-06-23 — FORM 8995-A (above-threshold QBI) — AUTHORED + SEEDED + EXPORTED ✅
- **Ken APPROVED the review walk in-session ("Approve & seed")** — the next Tier-2 big-ticket
  item after 8582 per-activity (Ken chose 8995-A over the Form 6251 AMT engine). The full
  above-§199A-threshold QBI computation: W-2/UBIA limit, SSTB phase-in, aggregation, loss netting.
- **Verified against the actual 2025 f8995a.pdf (read directly — Parts I-IV exact, 2 pages/111
  widgets) + i8995a (12pp, Schedule A/B/C mechanics), NOT memory.** Locked scope (AskUserQuestion
  2026-06-23): **Parts I-IV + Schedule A (SSTB applicable %) + Schedule B (FULL aggregation engine,
  Ken's choice) + Schedule C (per-business loss netting)** = IN; **Schedule D (patron reduction L14
  + DPAD §199A(g) L38)** = RED-deferred (D_8995A_001/002; ag/hort-coop patrons rare).
- **NEW loader `load_1040_form_8995a.py`** RE-AUTHORS the thin hand-authored `8995A` draft (20
  facts/6 rules/15 mismatched lines) into the real face: **21 facts / 11 rules / 51 lines /
  7 diagnostics / 10 worked scenarios / 9 FA** (FA-1040-8995A-01..09). `_retire_stale_8995a`
  dropped 43 stale draft rows on seed. Standalone loader (touches only 8995A + 1 new topic
  `qbi_above_threshold` + 1 new source `IRS_2025_8995A_FORM` + 3 excerpts on existing
  `IRS_2025_8995A_INSTR`); does NOT touch the simplified 8995 or anything else.
- **Core mechanics (Ken-verified, W1-W7):** (W1) Schedule A applicable% = clamp((ceiling−TI)/range,
  0,1) — the fraction RETAINED, reduces QBI/W-2/UBIA, stacks with the Part III phase-in;
  (W2) Schedule C apportions the total QB loss (current + prior carryforward) pro-rata by QBI across
  positive businesses, adjusted QBI ≤0 ⇒ that biz's W-2/UBIA = 0, net negative → line-6 carryforward;
  (W3) Schedule B full aggregation — combine QBI/W-2/UBIA, ownership/factors PREPARER-ASSERTED,
  none-SSTB ENFORCED (D_8995A_007 error); (W4) patron/DPAD RED-deferred; (W5) line-34 net cap gain =
  qual div + Sch D min(15,16), IDENTICAL to simplified-8995 L12; (W6) phase-in range $50k/$100k MFJ
  STATUTORY NON-INDEXED, ceiling = threshold + range (year-keyed via threshold); (W7) no public
  fillable Schedule A/B/C PDF (irs.gov f8995a.pdf = 2-pp main form only) → schedules authored at the
  COMPUTATIONAL level, exact PDF widget layout verified at the render leg.
- `check_8995a_integrity.py` INDEPENDENT re-derivation (own constants, no shared math) → **ALL 10
  SCENARIOS PASS** (T1 non-SSTB above ceiling/wage binds; T2 in-band phase-in relief 10k→15k;
  T3 SSTB applicable% 50%; T4 SSTB above ceiling→$0; T5 loss netting 100k+(−40k)→60k; T6 income
  limit binds; T7 REIT/PTP only; T8 aggregation 9k→20k; T9 patron RED; T10 TY2026 year-keying).
  Constants cross-checked cell-by-cell + RS varchar(20) id-length guard + line-uniqueness + text pins.
- **Deployed export verified HTTP 200** (`lookup/8995A/export/`: 21/11/51/7/10, all 11 rules + 7
  diagnostics + lines 26/39/A-APPLPCT/SC-1C present). Committed tts-tax-app canonical
  `server/specs/8995a_spec.json` + **9 FA staged** in `flow_assertions_1040_8995a_pending.json`
  (active 1040 gate holds at **264** until the assertions build leg). RS commit `b1d7853` (pushed);
  tts `d737e08` (pushed).
- **NEXT (tts-tax-app build legs):** leg 1 seed (per-business `w2_wages`/`ubia` on ScheduleC/F + 
  `w2_wages`/`ubia`/`is_sstb` on ScheduleK1 — NO such fields exist today; aggregation grouping model +
  Schedule B eligibility facts; additive migration to the shared DB; f8995a manifest; 8995A form def
  seed; serializer CRUD) → compute (`compute_8995a`, replace the D_8995_001 above-threshold blank) →
  render (un-stub f8995a_2025.py + Schedules A/B/C) → input → diagnostics (narrow D_8995_001; add the
  7 D_8995A_*) → assertions (merge 9 FA, gate 264→273, tag `1040-8995a-complete`).

## 2026-06-23 — FORM 8582 PER-ACTIVITY (Parts IV-VIII) — AMENDED + SEEDED + EXPORTED ✅
- **Ken APPROVED the review walk in-session ("Approve — flip & seed")** — the full §469 per-activity
  allocation, extending the 2026-06-14 aggregate Part I-III v1 (tag `1040-schedule-e-8582-complete`).
  **Closes the STATUS Tier-2 "Form 8582 fed by K-1 / Sch C-E-F" gap** (passive K-1/Sch-C/Sch-F losses were
  RED-deferred by `d_k1_passive_loss`; this routes them through 8582's Part V "other passive" bucket).
- **Verified against the actual 2025 f8582.pdf (3 pages, 205 widgets — Parts IV-IX are FILED, not
  "keep for your records") + i8582 (2025), NOT memory.** Locked scope (AskUserQuestion): **Parts IV-VIII**
  (Part IX = losses on 2+ forms / 28%-rate / §1231 RED-deferred — the triggers already defer upstream in
  the K-1 router); **all four activity types feed Part V** (non-active rental + passive K-1 + passive
  Sch C + passive Sch F).
- `load_1040_schedule_e.py` amended ADDITIVELY (FORM_8582 only): **+6 rules** (R-8582-WS-NET / -ALLOC-VI /
  -ALLOC-VII / -ALLOWED-VIII / -CARRYFWD / -MULTIFORM), **+1 fact** (`f8582_line_c`), **+6 lines**
  (C, P4-P8 descriptors), **+1 diagnostic** (`D_8582_MULTIFORM` RED), **+4 scenarios** (PA1/PA2/PA3 worked
  math + PG1 the RED), **+12 rule-links**, **+1 i8582 excerpt** (Parts IV-IX), **+3 FA** (FA-1040-8582-05/06/07).
  FORM_8582 now **18 facts / 12 rules / 23 lines / 7 diag / 11 tests / 20 links / 9 FA** (was 17/6/17/6/7/8/6).
- **Core mechanic (Ken-verified):** line C = (Part I line 3 loss) − (Part II line 9) = total unallowed;
  Part VI allocates line 9 across active-rental losses by loss-ratio; Part VII allocates line C across the
  pool [Part VI col(d) + Part V col(e)] by loss-ratio (Σ = line C); Part VIII allowed = activity loss −
  its unallowed → its own schedule. Conservation: **Σ allowed = line 11 (= line 9 + line 10)**.
- `check_schedule_e_8582_integrity.py` extended with an INDEPENDENT per-activity recompute (no shared
  loader math) → **ALL CHECKS PASS** (PA1 .75/.25 split; PA2 income-offset; PA3 no-allowance + conservation).
- **NEW loader `--only FORM_8582` option** → seeded SCOPED so SCHEDULE_E is untouched (protects the K-1
  router's page-2 spec + the FA-1040-SCHE-01 line-41 repoint). Seed: FORM_8582 Updated (18/12/23/7/11/20,
  7 FA scoped). **Deployed export verified HTTP 200** (`lookup/FORM_8582/export/`: 12 rules incl. the 6 new,
  D_8582_MULTIFORM, PA1/PA2/PA3/PG1). Committed tts-tax-app canonical `server/specs/form_8582_spec.json`
  (re-export) + **3 FA staged** in `flow_assertions_1040_sche_8582_pending.json`.
- **NEXT (tts-tax-app build legs):** seed (per-activity prior-unallowed model field on RentalProperty/
  ScheduleK1/ScheduleC/ScheduleF — migration) → compute (extend `compute_8582.py` per-activity + feed
  Part V from K-1/C/F; allocate back; carryforward) → render (f8582 field map Parts IV-VIII) → input →
  diagnostics (RETIRE `d_k1_passive_loss`; add D_8582_MULTIFORM) → assertions (merge the 3 FA) →
  tag `1040-8582-per-activity-complete`.

## 2026-06-22 — FORM 4562 §179 PRIOR-YEAR CARRYOVER (Part I L10/12/13) — AMENDED + SEEDED + EXPORTED ✅
- **Ken APPROVED the review walk in-session ("Approve & seed")** — the verified L10-L13 wording off the
  2025 Form 4562 PDF; the Line 11 **Individuals** business-income definition; R014/R015 carryover rules;
  D014 proforma-continuity; the 3 instruction excerpts. Flipped `READY_TO_SEED → True` → math gate stayed
  green → **seeded onto the EXISTING 4562 v1** (additive amendment): **facts 19→20, rules 10→12, lines
  24→26, diagnostics 8→9, tests 9→14**; entity_types **['1120S','1065','1120','1040'] UNTOUCHED**.
  **Deployed export verified HTTP 200** (`lookup/4562/export/`; L10/L11/L12/L13 present, L12 calc =
  `min(line_9 + line_10, line_11)`, R014/R015/D014/section_179_carryover_prior present). Committed
  tts-tax-app canonical `server/specs/form_4562_spec.json` (re-export) + **4 FA staged** in
  `flow_assertions_4562_section179_pending.json` (FA-4562-179-01..04).
- **WHY:** the 1040 proforma unit (Tier 1 Item 1) carries a prior-year §179 carryover forward
  (Taxpayer.sec_179_carryover_prior → line 10), which must be consumed (line 12) and any remainder
  re-carried (line 13). The existing 4562 spec was SILENT on lines 10/13 and its line-12 description was
  WRONG ("smaller of line 9 or line 11"). Per the MANDATORY Rule Studio rule + "flag if the spec is silent,
  do not guess" — fetched the spec, found the gap, Ken chose **amend RS spec first, then build inline**
  (AskUserQuestion 2026-06-22). NEW loader `load_4562_section179_carryover.py` AMENDS additively (looks up
  the form, never recreates it).
- **LAW VERIFIED 2026-06-22 — NOT memory:** Form face `resources/irs_forms/2025/f4562.pdf` (pymupdf dump):
  L10 "Carryover of disallowed deduction from line 13 of your 2024 Form 4562"; L11 "Business income
  limitation. Enter the smaller of business income (not less than zero) or line 5"; L12 "Add lines 9 and
  10, but don't enter more than line 11"; L13 "Add lines 9 and 10, less line 12". Instructions
  (irs.gov/instructions/i4562) Line 11 **Individuals**: smaller of L5 or total taxable income from any
  actively-conducted trade/business + **all wages/salaries/tips (Form 1040 line 1a)**, computed without
  §179, the §164(f) ½-SE-tax deduction, or any NOL; MFJ combine both spouses.
- **MATH GATE `check_4562_section179_integrity.py` ALL CHECKS PASS** — independent re-type of
  L12 = min(L9+L10, L11) / L13 = (L9+L10) − L12 over 5 scenarios (fully-absorbed / income-limited→3k carry /
  zero-carryover regression / both-limited→25k carry / zero-income→full carry) + carryover-conservation
  invariant (L12+L13 = L9+L10) + text-pins guarding against reverting L12 to the old wrong formula. Loader
  & gate share no math.
- **TWO BUILD-LEG decisions (downstream — do NOT change this spec):** (a) the line-11 v1 component scope
  for 1040 (recommend Sch C + Sch F net + W-2 wages 1040 L1a; flag K-1 active income / business §1231);
  (b) per-business allocation of a return-level carryover. Decide at the §179-consumption compute leg.
- **Next (tts-tax-app): the proforma build legs** — model/migration (Taxpayer.sec_179_carryover_prior +
  TaxReturn provenance pointer); §179 consumption compute+render (line 11 business-income limit + L12/L13 +
  per-business allocation, renderer.py:1748); 1040 roll-forward `_populate_*_from_prior_year`; UI;
  tests + merge the 4 FA. Design precedent: `_expand_4562` (the prior 4562 authoring) + `load_1040_schedule_f.py`.

## 2026-06-21 — SCHEDULE_J (1040 income averaging) — SEEDED + EXPORTED ✅
- **Ken APPROVED the review walk in-session ("Approve & seed now")** — the 4 requires_human_review walk
  items ruled, ALL matching the authored spec (no edits): Q-A line-4 SDTW REDUCES the current-year Sch D
  net cap gain by 2b (unrecap §1250 by 2c), floored at 0; Q-B line 6 = round_half_up(2a/3); Q-C SDTW
  ordinary lines 44/46 (instr's 34/36 & 42/44 are stale); Q-D D_SJ_ELECT_HIGH = warning. Flipped
  `READY_TO_SEED → True` → math gate stayed green → **seeded: RS DB 65→66 forms, FA 232→240** (SCHEDULE_J
  created; all 20 rules cited). **Deployed export verified HTTP 200** (`lookup/SCHEDULE_J/export/`
  53,036 B; 42 facts/20 rules/25 line_map/5 diagnostics/10 tests/4 sources). Committed tts-tax-app
  canonical `server/specs/schedule_j_spec.json` + **8 FA staged** in
  `flow_assertions_1040_schedule_j_pending.json` (status:active; active 1040 gate stays 249 until the
  assertions build leg).
- **Spec-first probe re-confirmed NO RS Schedule J spec** (SCHEDULE_J / 1040_SCHJ / SCHJ / J / f1040sj
  all 404; RS up, real 404s). Per the MANDATORY Rule Studio rule + Division of Authority: drafted the
  loader for Ken's review — did NOT improvise income-averaging compute.
- **Loader `specs/management/commands/load_1040_schedule_j.py`** — SCHEDULE_J (42 facts / 20 rules / 25
  lines / 5 diagnostics / 10 scenarios / 23 rule_links) + 8 FA. Pre-seed: guard verified REFUSING (zero
  DB writes; id-length ≤20 guards pass). 4 new sources (Sch J form/instr, the Schedule D Tax Worksheet,
  IRC §1301 [requires_human_review]); 2 new topics. NO amendment (single new form).
- **LAW VERIFIED 2026-06-21 against the actual 2025 IRS PDFs (pymupdf dumps) — NOT memory**
  (tts-tax-app `server/specs/_schedule_j_source_brief.md`, sha256s in §1):
  - **23-line chain** (f1040sj): L3=L1−L2a; L4=tax(L3) current-year; L6=round(L2a/3); L7=max(0,L5+L6);
    L11=L9+L6 & L15=L13+L6 (signed); L8/12/16 = base-year tax on L7/L11/L15 (0 when ≤0); L17=4+8+12+16;
    L22=19+20+21; **L23=L18−L22 → 1040 line 16** (route gate, only when elected). Base years (TY2025) =
    2022/23/24; (TY2026) = 2023/24/25.
  - **Base-year RATE SCHEDULES 2022/23/24** (i1040sj pp.4/8/12, all 4 statuses) + **base-year QDCGT**
    (27-line) + **Schedule D Tax Worksheet** (i1040sd — IDENTICAL 47-line structure 2022/23/24/25, only
    3 breakpoint sets differ → ONE year-keyed engine). **KEY override:** base-year tax uses the base-year
    RATE SCHEDULE for the ordinary sub-tax, NEVER the Tax Table. **Stale-cross-ref:** instr cite SDTW
    "34/36"(2022)/"42/44"(2023) but the real worksheets are 44/46 — implement 44/46.
- **MATH GATE `check_schedule_j_integrity.py` ALL CHECKS PASS** — independent re-type of the 23-line
  chain over re-typed rate schedules (SJ-T1: L4=21,647 / L8=6,617 / L12=7,408 / L16=8,253 / L23=31,982 <
  regular 36,047), the negative/floor (SJ-T2 L12=0) + line-6 round-half-up (SJ-T10) + differing-status
  (SJ-T9); loader rate schedules / preferential breakpoints / SDTW mid threshold cross-checked
  cell-by-cell. Loader & gate share no math.
- **v1 SCOPE (Ken-locked 2026-06-21, AskUserQuestion):** IN — the chain + elected farm income incl. net
  capital gain (2b/2c); L4/8/12/16 route rate-schedule/QDCGT/SDTW year-keyed; **build SDTW + base-year
  QDCGT**; base-year amounts DIRECT ENTRY (+ PriorYearReturn pull). RED-defer (each a D_SJ_*):
  prior-Sch-J chaining (D_SJ_CHAIN), zero-or-less Taxable-Income worksheets (D_SJ_NEG_TI warning), Form
  2555/FEI (D_SJ_2555). Plus D_SJ_2A_EXCEED, D_SJ_ELECT_HIGH.
- **WALK ITEMS (requires_human_review, brief §10):** **A — line-4 capital-gain netting** (does the
  current-year SDTW reduce Sch D figures by 2b/2c when 2b>0? recommend yes-reduce floored at 0 —
  LOAD-BEARING, confirm vs §1301/Reg 1.1301-1); B — line-6 rounding (recommend round-half-up whole
  dollar); C — stale SDTW cross-ref (confirm 44/46); D — elect-when-higher warning-only.
- **Next (tts-tax-app): the 6 build legs** — seed (`ScheduleJ` OneToOne model + migration + RLS +
  serializer/CRUD + `seed_schedule_j` + `f1040sj` manifest; merge the 2022/23/24 base-year schedules
  into the spine `TAX_BRACKETS`) → compute (`compute_schedule_j.py`: the 23-line chain + the year-keyed
  rate-schedule/QDCGT/SDTW engines [reuse the Topic-3 QDCGT engine; NEW year-keyed SDTW] + `route_line_16`
  when elected + RED diagnostics) → render (`f1040sj_2025.py` 2-page map + statement pages for the
  base-year worksheets) → input (new `schedule_j` tab; per-base-year cards) → diagnostics
  (`rules_schedule_j.py` — the 5 D_SJ_*) → assertions (merge the 8 FA via `merge_schedule_j_assertions.py`
  + `_run_schj_assertion`; gate 249→257). Design precedent: `load_1040_schedule_f.py` / `compute_intdiv.py`.

## 2026-06-21 — SCHEDULE_F (1040 farm, cash-method v1) + SCHEDULE_SE farm-optional amendment — SEEDED + EXPORTED ✅
- **Ken APPROVED the review walk in-session ("Approve & seed")** + chose Schedule J = **fast-follow**
  (its own form unit). Flipped `READY_TO_SEED → True` → math gate stayed green → **seeded: RS DB
  64→65 forms, FA 224→232** (SCHEDULE_F created; SCHEDULE_SE amended; both forms all-rules-cited).
  **Deployed exports verified HTTP 200** (`lookup/SCHEDULE_F/export/` 49,790 B; `SCHEDULE_SE` 33,791 B
  re-exported); committed tts-tax-app canonical `server/specs/schedule_f_spec.json` + re-committed
  `schedule_se_spec.json` + **8 FA staged** in `flow_assertions_1040_schedule_f_pending.json`
  (status:active; active 1040 gate stays 241 until the assertions build leg).
- **SEED GOTCHA:** `FormDiagnostic.diagnostic_id` is **varchar(20)** — `D_SE_FARMOPT_INELIGIBLE` (23)
  raised `DataError` (atomic rollback, zero partial writes). Renamed → `D_SE_FARMOPT_INELIG` (19) +
  **hardened the math gate** with rule_id/diagnostic_id/line_number ≤20 guards (caught pre-seed next time).
- **Authoring details (below) unchanged.** AUTHORED + MATH-GATED:
- **Spec-first probe re-confirmed NO RS Schedule F spec** (SCHEDULE_F / 1040_SCHF / F / SCHF all 404;
  RS up, real 404s). Per the MANDATORY Rule Studio rule + Division of Authority: drafted the loader
  for Ken's review — did NOT improvise farm-tax compute.
- **NEW loader `specs/management/commands/load_1040_schedule_f.py`** — creates **SCHEDULE_F** (31 facts /
  11 rules / 71 lines / 8 diagnostics / 10 scenarios / 14 rule_links) and **AMENDS SCHEDULE_SE** additively
  (10 facts / 2 rules / 7 lines / 3 diagnostics / 4 scenarios / 3 rule_links — the Part II FARM OPTIONAL
  METHOD + line-1a/1b computed-feeder re-point + narrowed R-SE-OPTIONAL/D_SE_003) + **8 flow assertions
  FA-1040-SCHF-01..08**. `READY_TO_SEED = False` — **guard verified REFUSING (zero DB writes; "(all
  populated)")**. 6 new sources (Sch F form/instr, Pub 225 [requires_human_review], IRC §77 / §451(e)(f) /
  §1402(a)(1)); 2 new topics. RS DB still 64 forms (nothing seeded).
- **LAW VERIFIED 2026-06-21 against the actual 2025 IRS PDFs (pymupdf dumps) — NOT memory**
  (tts-tax-app `server/specs/_schedule_f_source_brief.md`):
  - **Line 9 gross income = 1c + 2 + 3b + 4b + 5a + 5c + 6b + 6d + 7 + 8** (verbatim right-column list;
    includes BOTH 5a [CCC elected] and 5c [forfeiture taxable], NOT 5b). L1c = 1a − 1b. L33 = sum(10..32f).
    **L34 = L9 − L33 → Schedule 1 line 6 (sum farms) + Schedule SE line 1a (per proprietor); CRP → SE 1b.**
    Sch F has NO home-office line. L14 depreciation ← 4562; farm net → 8995 QBI.
  - **Schedule SE Part II farm optional method (2025, off the face):** eligible iff gross farm income ≤
    **$10,860** OR net farm profit < **$7,840**; line 14 max = **$7,240**; line 15 = min(⅔ × gross farm
    income, $7,240) → line 4b. SSA-indexed (NOT in RP 2025-32); **2026 UNPUBLISHED → fires RED
    (D_SE_FARMOPT_2026) + standing re-pin** (the Tax-Table-interim precedent).
- **MATH GATE `check_schedule_f_integrity.py` ALL CHECKS PASS** — independent re-type of the line
  1c/9/33/34 chain (incl. 5a-in-9 / 6a-not-in-9 membership + multi-farm aggregation) + the farm-optional
  ⅔/cap/eligibility/2026-RED; loader & gate share no math; loader constants cross-checked cell-by-cell.
- **v1 SCOPE (Ken-locked):** cash method; per-farm (multi-Schedule-F); farm optional SE IN. **RED-defer
  (no silent gap, each a D_SF_*/D_SE_*):** accrual Part III; CCC §77 / crop-insurance §451(f) / weather
  §451(e) ELECTIONS (capture the $, flag the election); passive loss (line E No → Form 8582); at-risk
  (36b → Form 6198); §461(l). Nonfarm optional / church / clergy SE stay RED (D_SE_003 narrowed).
- **WALK ITEMS (requires_human_review):** A) 2026 farm-optional constants unpublished → 2025 supported,
  2026 RED + re-pin; B) Schedule J bundle-vs-fast-follow; C) Pub 225 narrative definitions / §77 §451
  RED-defer treatment; D) QBI farm-reduction allocation when a proprietor has both a Sch C and a Sch F.
- **Next (tts-tax-app): the 6 build legs** — seed (new per-farm ScheduleF FK model + migration + RLS +
  serializer/CRUD + seed command + manifest; flip Sch 1 L6 + Sch SE L1a computed; extend
  `compute_schedule_se_lines` for Part II farm optional) → compute (`compute_schedule_f.py`: line
  1c/9/33/34 + cross-form routing addends + RED diagnostics; QBI → 8995; depreciation 4562 flow_to) →
  render (un-stub `f1040sf_2025.py` field map — 89 PDF fields; cash-method Parts I/II + line 34; skip
  page 2) → input (un-stub the `schedule_f` React tab; per-farm card UI) → diagnostics (`rules_schedule_f.py`)
  → assertions (merge the 8 FA via `merge_schedule_f_assertions.py` + `_run_schf_assertion`; gate 241→249).
  Then **Schedule J** as the fast-follow (its own RS spec). Design precedent: `load_1040_schedule_c.py`.

## 2026-06-21 — SCHEDULE_K1 (recipient K-1 router, effort #5) + SCHEDULE_E page-2 amendment — SEEDED + EXPORTED ✅
- **Ken approved the review walk in-session ("Approve & seed as authored").** The RECIPIENT-side K-1
  full router (TaxWise/Lacerte model): a 1040 partner (1065 K-1) / S-corp shareholder (1120-S K-1) /
  estate-trust beneficiary (1041 K-1) routing EVERY box to its destination. NEW form **SCHEDULE_K1**
  (31 facts / 11 rules / 21 lines / 10 diagnostics / 12 scenarios / 18 links) + **SCHEDULE_E AMENDED**
  additively with page 2 (Parts II-V lines 27-43; +3 rules R-SCHE-P2-*; +2 diags D_SCHE_REMIC/4835) +
  7 flow assertions FA-1040-K1-01..07. `check_schedule_k1_integrity.py` **ALL CHECKS PASS** (independent
  re-type of the page-2 aggregation + cross-form routing; loader & gate share no math). Guard verified
  REFUSING before the flip (zero DB writes). **RS DB 63→64 forms, FA 217→224.** All rules cited. 6 new
  sources (i1065sk1 / i1120ssk / i1041sk1 / §199A / §1402 / §702-1366-652 conduit), the 3 K-1 instruction
  sources `requires_human_review=True`.
- **LAW VERIFIED 2026-06-21 against the actual 2025 IRS PDFs (pymupdf dumps) + the K-1 instruction
  booklets — NOT memory** (tts-tax-app `server/specs/_schedule_k1_source_brief.md`):
  - **⚠ CORRECTION to the brainstorm design spec:** the summary that flows to Schedule 1 line 5 is
    Schedule E **line 41** ("Combine lines 26, 32, 37, 39, and 40"), NOT line 40 (= Form 4835 farm
    rental) — the brainstorm recalled it wrong. Encoded line 41 = 26+32+37+39+40 → Sch 1 L5.
  - Part II (1065/1120-S) line 28 cols (g) passive loss / (h) passive income / (i) nonpassive loss /
    (j) §179 / (k) nonpassive income → 30/31/32. Part III (1041) line 33 cols (c)/(d)/(e)/(f) → 35/36/37.
  - **§199A codes:** 1065 box **20Z**, 1120-S box **17V**, 1041 box **14I** — all "Section 199A
    information" → Form 8995 (QBI line 2; REIT/PTP line 6). **SE:** 1065 box **14 code A** → Schedule SE;
    "S corporation income isn't subject to self-employment tax" (no S-corp/1041 SE).
- **v1 scope (Ken Decisions 1-6, 2026-06-21):** full router; sources 1065+1120-S+1041; **passive losses
  RED-deferred** (route passive income + all nonpassive; passive loss → RED "limit via 8582 manually");
  §199A → 8995 IN; partnership SE → Sch SE IN. RED-defer (no silent gap, each a D_K1_*): passive loss,
  §1231→4797, 28%/§1250→SDTW, AMT→6251, basis/at-risk (warning), other income, foreign/K-3, PTP (warning),
  REMIC, Form 4835.
- **Deployed exports verified HTTP 200** (`lookup/SCHEDULE_K1/export/` 59,809 B; `SCHEDULE_E` 29,748 B —
  re-exported since amended); committed to tts-tax-app as canonical `server/specs/schedule_k1_spec.json` +
  re-committed `schedule_e_spec.json` + 7 FA staged in `flow_assertions_1040_schedule_k1_pending.json`
  (status:active; active 1040 gate 234 unchanged until the assertions build leg). Source brief
  `server/specs/_schedule_k1_source_brief.md`.
- **WALK ITEMS (requires_human_review, Ken's recommendation accepted):** (1) severity split — passive
  loss=error, basis/at-risk=warning; (2) 1041 boxes 6/7/8 default to material-participation (preparer
  toggles per-K-1); (3) §199A split into two facts (QBI line 2 + REIT/PTP line 6); (4) PTP loss = warning
  (per-PTP netting bounded out of v1).
- **Next (tts-tax-app): the 6 build legs** — seed (new per-entity K-1 recipient model + migration + RLS +
  serializer/CRUD + seed command + manifest) → compute (`compute_schedule_e_p2.py`/extend: K-1 aggregation
  + line-41 summary + cross-form routing addends + RED diagnostics) → render (extend `f1040se_2025.py`
  Parts II/III/V) → input (un-stub `schedule_e_p2`; per-entity K-1 UI) → diagnostics (`rules_schedule_e_p2.py`)
  → assertions (merge 7 FA + `_run_k1_assertion`; **REPOINT FA-1040-SCHE-01 line 26 → line 41**). Design
  doc tts-tax-app `docs/superpowers/specs/2026-06-21-effort5-schedule-e-p2-k1-router-design.md`.

## 2026-06-20 — Form W-2G (certain gambling winnings §61, effort #4) spec leg — SEEDED + EXPORTED ✅
- **Ken approved the review walk in-session ("Approve & seed as recommended").** Flipped
  `READY_TO_SEED → True` → `check_w2g_integrity.py` **ALL CHECKS PASS** → **seeded FORM_W2G** (7 facts /
  2 rules / 6 lines / 2 diagnostics / 5 scenarios / 5 cited links + 5 flow assertions; 4 authority
  sources: IRC §61, IRC §165(d), Instr. W-2G & 5754 box layout, 2025 i1040 Sch 1 L8b + 1040 L25c).
  **RS DB →63 forms, FA →217.** All rules cited. Mirrors the 1099-G vertical (same input-document
  shape, simpler: no repayment netting, no §1341).
- **Deployed export verified HTTP 200** (`lookup/FORM_W2G/export/`, 12,733 bytes); committed to
  tts-tax-app as canonical `server/specs/w2g_spec.json` + 5 FA staged in
  `flow_assertions_1040_w2g_pending.json` (active 1040 gate unchanged until the Part-B assertions leg).
- **Scope (Ken):** (1) pull W-2G into effort #4 WITH compute (a FormW2G doc sub-model → Sch 1 L8b +
  1040 L25c). (2/recommended, confirm at walk) line 8b = Σ box1 + a return-level `other_gambling_winnings`
  (non-W-2G winnings) so 8b is the TOTAL (it backs the Sch A §165(d) loss cap).
- **KEY ROUTING (verified vs IRS, not memory):** box 1 winnings → **Sch 1 line 8b** ("Gambling"); box 4
  federal withholding → **1040 line 25c** ("Other forms") — **NOT 25b** (W-2G is not a 1099). Line 25c is
  a **roster** shared with Form 8959 (additional-Medicare withholding), so the tts-tax-app compute must
  ADD W-2G box 4 to 25c, not clobber the 8959 write (FA-1040-W2G-05 guards this). No render face (input
  document, like 1099-G / W-2). No year-keyed constants (§61 identical 2025/2026).
- **WALK ITEMS (requires_human_review):** confirm the exact 2025/2026 i1040 wording + line numbers (8b,
  25c); confirm the W-2G box numbering vs the target-year revision (box 1/4/15 stable across recent revs).
- **Next:** Ken review walk → flip READY_TO_SEED → seed (RS DB +1 form, FA +5) → verify deployed export →
  commit canonical `server/specs/w2g_spec.json` + stage assertions in `flow_assertions_1040_w2g_pending.json`
  → then tts-tax-app build legs (model 0096+ → serializer/CRUD → compute → diagnostics → input/Misc Income
  page → assertions). Spec/design doc: tts-tax-app `docs/superpowers/specs/2026-06-20-effort4-retirement-misc-reorg-design.md`.

## 2026-06-16 — MINISTER (Minister/Clergy Housing Allowance & SE Tax §107/§1402, W-2 Unit 4) spec leg — SEEDED + EXPORTED ✅
- **Ken approved the review walk in-session ("Looks good. Continue")** — a worksheet-style spec (NOT a
  single IRS form; reconstructed from Pub 517) for the church-employed (common-law-employee) minister's
  DUAL STATUS: income-tax EMPLOYEE (W-2) but SELF-EMPLOYED for SE tax. INCOME TAX (§107): housing/rental
  allowance excluded up to the **least of (designated / used / FRV+utilities)**; the EXCESS → **Form 1040
  line 1h** ("Excess allowance"). SE TAX (§1402(a)(8)): the FULL housing allowance + parsonage FRV go BACK
  into the SE base — **Schedule SE line 2 = wages + housing allowance + parsonage FRV − unreimbursed
  ministerial expenses** (full; no Deason for SE); the EXISTING Topic-8 SE engine applies × 0.9235 + the
  SS cap + ½-SE → Sch 1 L15 + SE → Sch 2 L4. **Form 4361** approved → Schedule SE line 2 = 0.
- LAW VERIFIED 2026-06-16 vs IRS Pub 517 (2025) + IRC §107 + §1402(a)(8)/(c)(4)/(e) (live WebFetch):
  the §107 least-of-three; the §1402(a)(8) housing-in-SE inclusion ("doesn't apply for SE tax purposes",
  Pastor Leslie Adams example $39k+$12k=$51k SE); excess → 1040 1h; W-2 minister wages → Schedule SE
  line 2 (no Schedule C, no FICA); Form 4361 omits ministerial earnings. ½-SE-tax (Sch 1 L15) normal.
- **KEN'S 3 SCOPE DECISIONS (2026-06-16 AskUserQuestion):** (1) v1 = "W-2 minister core" (RED-defer
  Schedule-C ministerial side income, §265/Deason allocation, retired-minister housing, 4361
  adjudication); (2) clergy inputs ON `W2Income` + a person-level `clergy_4361_exempt` Taxpayer fact;
  (3) include one preparer-entered unreimbursed-ministerial-expenses input (full, for SE).
- `load_1040_minister.py` + `check_minister_integrity.py` **ALL CHECKS PASS** (independent re-type of
  the §107 least-of-three + the §1402(a)(8) SE base + the Form 4361 zeroing + all 6 scenarios + the 6
  diagnostic conditions + negative-floor/below-FRV edges; loader & gate share no math). Guard verified
  REFUSING before the flip.
- Flipped READY_TO_SEED → seeded: **MINISTER** (10 facts / 4 rules / 11 lines / 6 diagnostics / 6
  scenarios / 7 links) + 6 flow assertions. **RS DB 61→62 forms, FA 206→212.** All rules cited. 4
  sources (Pub 517 / §107 / §1402 / Form 4361), all `requires_human_review=True`.
- **WALK ITEMS (requires_human_review):** (a) the worksheet line LABELS are reconstructed from the Pub
  517 narrative + examples (PDF worksheet tables don't render in HTML) — the COMPUTATION is math-gated;
  (b) the SE housing component uses the full DESIGNATED allowance (line 2), confirmed vs §1402(a)(8) +
  the Pastor Adams example; (c) reasonable-comp §107 limit NOT modeled (D_MIN_REASONABLE info); (d)
  Form 4361 preparer-asserted, not adjudicated.
- Deployed export verified HTTP 200 (`lookup/MINISTER/export/`, 24,185 bytes; 10/4/11/6/6/4); committed
  to tts-tax-app as canonical `server/specs/minister_spec.json` + 6 FA staged in
  `flow_assertions_1040_minister_pending.json` (active 1040 gate stays 223). Source brief
  `server/specs/_minister_source_brief.md`.
- Next (tts-tax-app): the 6 build legs — seed (clergy fields on W2Income + `clergy_4361_exempt` Taxpayer
  fact + migration) → compute (`compute_minister.py` → 1040 line 1h + a clergy Schedule SE row at line 2
  feeding the existing SE engine) → render (Pub 517 worksheet statement, the SM-statement precedent) →
  input (clergy fields on the W2Screen FieldGrid) → diagnostics (`rules_minister.py`, 6) → assertions
  (merge the 6 FA + `_run_minister_assertion`) → tag `1040-minister-complete`.

## 2026-06-15 — Form 7206 (Self-Employed Health Insurance Deduction §162(l), W-2 Unit 3) spec leg — SEEDED + EXPORTED ✅
- **Ken approved the review walk in-session ("Approved — seed it")** — the §162(l) SEHI deduction
  → Schedule 1 line 17, computed on **Form 7206** (the form that replaced the old SEHI worksheet
  since TY2023). TWO earned-income limit paths on one form: the **Sch C/SE path** (line 10 = net
  profit − apportioned ½-SE-tax line 7 − SEP/SIMPLE line 9) and the **S-corporation 2% shareholder
  path** (line 4 "skip to line 11"; line 11 = **Box 5 Medicare wages**). Line 14 = min(line 3
  premiums, line 13 limit); the return total = Σ each form's line 14. **One Form 7206 per business.**
- LAW VERIFIED 2026-06-15 cell-by-cell from the 2025 Form 7206 PDF (pulled via pymupdf) + i7206 +
  §162(l)(2)(A): the 2% shareholder limit is the **W-2 Box 5** Medicare wages (form line 11 verbatim);
  no ½-SE-tax reduction on the S-corp path (no SE tax). Form 2555 line 12 RED-deferred (v1 = 0); LTC
  line 2 folded into the premium input (preparer age-capped) — no auto-cap, no new model field.
- `load_1040_form_7206.py` + `check_form_7206_integrity.py` **ALL CHECKS PASS** (independent re-type
  of both limit paths + the smaller-of + all 8 scenarios + the 3 limit diagnostics; loader & gate
  share no math). Guard verified REFUSING before the flip.
- **Ken's 2 decisions (AskUserQuestion):** (1) author a Form 7206 RS spec (not a bare engine
  extension); (2) **fix the existing Schedule C SEHI limit** — the old R-SC-SEHI capped only at net
  profit, NOT subtracting the ½-SE-tax / SE-retirement. Scenario **SC-T6** pins the fix (net 5,000 /
  ½-SE 700 / premium 6,000 → deduction **4,300**, was 5,000).
- Flipped READY_TO_SEED → seeded: **FORM_7206** (12 facts / 4 rules / 15 lines / 6 diagnostics / 8
  scenarios / 7 links) + 6 flow assertions. **RS DB 60→61 forms, FA 200→206.** All rules cited. 3
  sources (Form 7206 / i7206 / IRC §162(l)).
- **R-SC-SEHI updated in lock-step (Ken's call):** `load_1040_schedule_c.py` R-SC-SEHI formula +
  description repointed to FORM_7206 (text-only, no count change); Schedule C re-seeded (TaxForms 61,
  FA 206 unchanged).
- Deployed export verified HTTP 200 (`lookup/FORM_7206/export/`, 20,856 bytes; 12/4/15/6/8/3);
  committed to tts-tax-app as canonical `server/specs/7206_spec.json` + 6 FA staged in
  `flow_assertions_1040_7206_pending.json` (active 1040 gate stays 217).
- Next (tts-tax-app): build legs — compute (`compute_7206` replacing `sehi_deduction_for_proprietor`:
  Sch C limit fix + the S-corp Box-5 path; new engage so a no-Schedule-C 2%-shareholder return writes
  Sch 1 L17; the existing 8962 SEHI↔PTC iterative reads line 17 source-agnostically) → diagnostics →
  assertions → tag.

## 2026-06-15 — Form 2210 (underpayment of estimated tax §6654, Phase 2 sixth common form) spec leg — SEEDED + EXPORTED ✅
- **Ken approved the review walk in-session ("Approved — seed it, include render")** — the FULL build:
  Part I safe harbors ($1,000 de-minimis / 90% / 100% / 110% over $150k AGI), the Regular Method
  penalty (§6621 7% through 3/31/2026, 6% for 4/1-4/15/2026 — verified web vs the 2025 Rev. Ruls.),
  and Schedule AI (factors 4/2.4/1.5/1, applicable % 22.5/45/67.5/90, smaller-of). Ken's 2 scope
  decisions: FULL (regular + annualized); prior-year inputs as preparer facts.
- `load_1040_2210.py` + `check_2210_integrity.py` ALL CHECKS PASS (independent re-type of the §6654
  safe harbors + the §6621 penalty day-factors + Schedule AI + all 6 numeric scenarios, AND cross-
  checks the loader's compute_2210; loader & gate share no math). Guard verified REFUSING.
- Flipped READY_TO_SEED → seeded: **FORM_2210** (10 facts / 3 rules / 11 lines / 5 diagnostics / 7
  scenarios / 5 cited links) + 6 flow assertions. **RS DB →60 forms, FA →200.** All rules cited. 2
  sources (i2210 / IRC §6654).
- **KEY:** penalty → 1040 line 38 (already the manual NIIT... no, the est-tax-penalty slot, direct-
  entry → now computed). §6621 penalty day-factors [0.069589, 0.057890, 0.040247, 0.016849] for the 4
  periods (due 4/15, 6/15, 9/15/2025, 1/15/2026). **WALK ITEMS (requires_human_review):** Schedule AI
  takes the per-period annualized TAX as a preparer input (t2210_ai_tax_q*; the full per-period
  bracket/QDCGT/AMT computation deferred); withholding spread evenly (no actual-date election); Part
  II waiver + farmers/fishermen out of v1. TY2026 → re-pin the §6621 rates.
- Deployed export verified HTTP 200 (`lookup/FORM_2210/export/`); committed to tts-tax-app as canonical
  `server/specs/2210_spec.json` + 6 FA staged in `flow_assertions_1040_2210_pending.json` (active 1040
  gate stays 189).
- Next (tts-tax-app): the 6 build legs — seed (~10 t2210_* Taxpayer facts + a FORM_2210 FormDef) →
  compute (`compute_2210.py` → 1040 line 38; reads current tax/withholding/est payments, runs near the
  end of the 1040 pass) → render (f2210.pdf incl. Schedule AI) → input → diagnostics → assertions →
  tag `1040-form-2210-complete`.

## 2026-06-15 — Form 8960 (net investment income tax §1411, Phase 2 fifth common form) spec leg — SEEDED + EXPORTED ✅
- **Ken approved the review walk in-session ("Approved — seed it, include render")** — the 3.8% NIIT
  on min(net investment income, MAGI − threshold); the auto-feed (interest 1040 2b / dividends 3b /
  net gain line 7) + the §1411 adjustments on 4b/5b/6/7; the MAGI = AGI + §911 base; the statutory
  thresholds. Ken's 2 scope decisions: auto-aggregate clean feeders + overrides; §1411 nuances are
  preparer adjustments via 4b/6/7.
- `load_1040_8960.py` + `check_8960_integrity.py` ALL CHECKS PASS (independent re-type of the §1411
  chain + the thresholds + all 7 numeric scenarios; loader & gate share no math). Guard verified REFUSING.
- Flipped READY_TO_SEED → seeded: **FORM_8960** (17 facts / 3 rules / 15 lines / 5 diagnostics / 8
  scenarios / 5 cited links) + 6 flow assertions. **RS DB →59 forms, FA →194.** All rules cited. 2
  sources (i8960 / IRC §1411).
- **KEY:** NIIT = 3.8% × min(max(0, line 12 NII), MAGI − threshold) → Schedule 2 line 12 (already the
  NIIT slot, direct-entry → now computed). Thresholds STATUTORY/non-indexed (MFJ/QSS $250k, MFS $125k,
  single/HoH $200k) — same 2025/2026. MAGI = AGI + §911 (the 8962 base). Return-level facts (no
  sub-model — per-return tax). RED-deferred: estates/trusts, the disposition-of-active-interest
  worksheet, the precise state-tax allocation ratio.
- Deployed export verified HTTP 200 (`lookup/FORM_8960/export/`); committed to tts-tax-app as canonical
  `server/specs/8960_spec.json` + 6 FA staged in `flow_assertions_1040_8960_pending.json` (active 1040
  gate stays 183).
- Next (tts-tax-app): the 6 build legs — seed (~12 e8960_* Taxpayer facts + a FORM_8960 FormDef) →
  compute (`compute_8960.py` → Schedule 2 line 12; auto-feeds interest 2b / dividends 3b / gain line 7;
  MAGI from AGI; runs after AGI final) → render (f8960.pdf) → input → diagnostics → assertions → tag
  `1040-form-8960-complete`.

## 2026-06-15 — Form 8606 (nondeductible IRAs §408(d)+§408A, Phase 2 fourth common form) spec leg — SEEDED + EXPORTED ✅
- **Ken approved the review walk in-session ("Approved — seed it, include render")** — the §408(d)
  pro-rata (nontaxable% = basis / (year-end + distributions + conversions), capped 1.0), the Part II
  conversion taxable (line 18 = line 16 − the line-11 pro-rata basis), the §408A(d)(4) Roth ordering
  (contributions→conversions→earnings), and the 1099-R box-2a SUPERSESSION on line 4b. Ken's 3 scope
  decisions: ALL THREE PARTS; a per-owner Form8606 sub-model; the 8606 supersedes the 1099-R box-2a.
- `load_1040_8606.py` + `check_8606_integrity.py` ALL CHECKS PASS (independent re-type of part_i/
  part_ii/part_iii + all 7 numeric scenarios incl. basis conservation; loader & gate share no math).
  Guard verified REFUSING.
- Flipped READY_TO_SEED → seeded: **FORM_8606** (16 facts / 4 rules / 22 lines / 6 diagnostics / 8
  scenarios / 6 cited links) + 6 flow assertions. **RS DB →58 forms, FA →188.** All rules cited. 3
  sources (i8606 / IRC §408(d) / IRC §408A).
- **KEY:** the 8606 owner-with-basis taxable amount (line 15c + 18 + 25c) drives 1040 line 4b,
  SUPERSEDING the 1099-R box-2a (the Simplified Method precedent — the gross 4a still sums). **WALK
  ITEM:** line 17 = line 11 (the pro-rata; the IRS "line 2 + pre-conversion line 1" plain-language form
  equals line 11 in the no-other-IRA backdoor case — i8606 requires_human_review). RED-deferred:
  disaster distributions, outstanding rollovers, recharacterizations, inherited-IRA basis.
- Deployed export verified HTTP 200 (`lookup/FORM_8606/export/`); committed to tts-tax-app as canonical
  `server/specs/8606_spec.json` + 6 FA staged in `flow_assertions_1040_8606_pending.json` (active 1040
  gate stays 177).
- Next (tts-tax-app): the 6 build legs — seed (a per-owner Form8606 sub-model + mig + RLS + FORM_8606
  FormDef + CRUD) → compute (`compute_8606.py` → 1040 line 4b, superseding the 1099-R IRA box-2a; runs
  in/after compute_retirement_aggregation, re-deriving 4b) → render (f8606.pdf, one copy per owner) →
  input → diagnostics → assertions → tag `1040-form-8606-complete`.

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
