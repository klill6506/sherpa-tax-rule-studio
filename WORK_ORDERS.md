# WORK_ORDERS.md — Rule Studio work queue (the front door)

*Adopted 2026-07-04. This makes RS the TRIGGER: authoring work enters HERE first, is
approved by Ken, and only THEN is the tax-app build dispatched. Reverses the old
spec-last habit (app discovers a missing spec mid-build) into spec-first-by-sequence —
which is the standard the app already enforces and CLAUDE.md already requires.*

***ORDER LIVES IN BUILD_ORDER.md (canonical in `tts-tax-status`), NOT here.** This file is
the RS front-door MECHANISM: it holds the gap-check, the transition states, Gate-1 approval,
and the working detail of the CURRENT order. It takes its next authoring order FROM the
BUILD_ORDER SPINE. Do NOT maintain a second ordered backlog here — that is what drifted
(states showed queued here while DONE in the spine). At session start, reconcile against
BUILD_ORDER + live STATUS before pulling the next order.*

## What this changes (and what it doesn't)
- **Unchanged:** the runtime wiring. Specs still seed→export→home in the app→load via the
  existing gated ingest. No new coupling, no auto-propagation.
- **Changed:** the WORK ORDER. New modules start with a spec-gap check on the RS side; gaps
  are cleared and Ken-approved BEFORE the app build starts. The app stops discovering
  missing specs mid-flight because the question is asked at the top.

## The flow
```
  scope item (Ken) ─┐
                    ├─► THIS QUEUE ─► spec-gap check ─► CC drafts from verified source
  change register ──┘    (intake)     (first step)             │
                                              ⟨GATE 1: Ken approves the spec⟩
                                                      │
                                          spec seeds + exports (RS)
                                                      │
                                          Pushover ping: "ready to dispatch"
                                                      │
                                          app build dispatched (tts session)
                                                      │
                                              ⟨GATE 2: existing gated ingest⟩
                                                      │
                                          compute + flow assertions + regression
```
**Two human gates, non-negotiable.** A tax-law update or Ken may START a draft; nothing
CROSSES a gate unattended. Gate 1 = draft→published spec (Ken). Gate 2 = published→compute
(existing ingest). An update can trigger *authoring*; never *publication* or *computation*.

## Two modes (pick per module)
- **RS-first (default for NEW/greenfield modules):** enumerate the required form set up front,
  gap-check, author + approve all gaps, THEN dispatch the app build. Use for SC/AL/NC, 1041,
  1065 core.
- **Tail-completion (for finishing a huge module, e.g. 1040):** keep the app/ATS discovery
  loop — when testing surfaces a missing spec, it drops back into THIS queue as a new order,
  not a silent stall. This is a feature for unknowable long tails, not the default.

## The spec-gap check (CC runs this as step 1 of any module)
1. Ken (or PRODUCT_MAP scope) names the module's required forms/schedules.
2. For each, check RS coverage: `GET /api/forms/lookup/<FORM>/export/` → 200 = spec exists,
   404 = gap. (Cross-check the RS forms index / session_log.)
3. Write the gap list into this file as an order with status `GAP-CHECKED`.
4. Do NOT start the app build until every gap for that module is `APPROVED`.

## Order format
`[ID] source · module · status · required set → gaps · links/approval`
Statuses: `INTAKE → GAP-CHECKED → DRAFTING → ⏳ AWAITING KEN → APPROVED (seeded/exported)
→ DISPATCHED (app) → ✅ DONE`

---

## ▶ CURRENT ORDER — pulled from the BUILD_ORDER SPINE (canonical in `tts-tax-status`)
*No independent backlog here (see header). Sequence = BUILD_ORDER.md SPINE; statuses seeded
from live STATUS.md per BUILD_ORDER's own rule. Reconciled 2026-07-05.*

- **▶ ACTIVE — [WO-09] S-11 · 1041 module · greenfield RS-first · status `GAP-CHECKED → research-verified → Gate-1 scope LOCKED → DRAFTING (authoring)` (opened 2026-07-05).**
  Gap-check run against live prod (96 forms) — **all five authoring surfaces are 404 GAPs**; the module is fully
  greenfield (no `load_1041_*` loaders; the only on-disk `1041` refs are the boundary-diag Sch I note + the *receiving*
  side in `load_1040_schedule_k1.py` where a 1040 imports a trust K-1). Required set from BUILD_ORDER S-11:
  - **Spine** (`1041`) — entity types / 2025 §1(e) rate schedule / §642(b) exemptions → **GAP**
  - **DNI / IDD / Schedule B** (`1041` or `1041_SCHB`) — §643(a) DNI, §651/§661 distribution deduction, tier/separate-share → **GAP**
  - **Schedule G** (`1041_SCHG`) — tax computation, cap-gain rates, §1411 NIIT on trusts/estates → **GAP**
  - **K-1 (Form 1041)** (`SCHEDULE_K1_1041`) — beneficiary distributive shares + character pass-through → **GAP**
  - **GA Form 501** (`GA501`) — Georgia fiduciary income tax return → **GAP**
  - **Schedule I (AMT)** — **RED-defer diagnostic only** (D-2, ruled 2026-07-04; do NOT author the compute).
  - **✅ Research-verified** (4 passes, verbatim vs FINAL IRS/GA sources) → **`f1041_source_brief.md`**. Rev. Proc.
    2025-32 confirmed = TY2026 (2024-40 governs TY2025). PDF text dumps cached in `scratchpad/` for excerpt seeding.
  - **✅ Gate-1 scope LOCKED (2026-07-05, DECISIONS D-10):** core 4 + **ESBT** computed; grantor = structure/
    grantor-letter; PIF → routed to the 5227 leg; bankruptcy = RED-defer. **FULL** distribution engine (§662 tiers
    + §663(c) separate-share + §663(b) 65-day + character retention). Cap-gains-in-DNI = direct-entry + 3-circumstance
    diagnostic. **GA 501 resident-only v1** (Sch 4 NR + conformity add-backs deferred). Sch I AMT = RED-defer (D-2).
    K-1 full verbatim codes. Form keys: `1041` (spine+SchB+SchG) + `SCHEDULE_K1_1041` + `GA501`.
  - **➕ Spun off — [WO-10] Form 5227 split-interest trusts** (PIF + CRT/CRAT/CRUT + CLT, §664(b) 4-tier) = its own
    dedicated leg with its own research pass + source brief, AFTER the 1041 core. Enters this queue as a new order when reached.
  - **Authoring legs (this order):** (a) `1041` spine+SchB+SchG · (b) `SCHEDULE_K1_1041` · (c) `GA501`. Each:
    author `READY_TO_SEED=False` → SQLite-validate (CharField caps: rule/diagnostic/assertion_id ≤ 20) → Ken review
    walk → seed → export = 200.
  - **✅ ALL 3 LEGS DONE — S-11 1041 module RS authoring COMPLETE 2026-07-05** (Ken Gate-1 approved each; every
    guard flipped after its review walk). Prod: **99 TaxForms / 471 FlowAssertions / 859 FormRules**.
    - **(a) `1041` spine** — `load_1041_spine.py`; 35 facts / 15 rules / 39 lines / 11 diag / 9 tests / 6 FA;
      `validate_1041.py` 17/0; `lookup/1041/export/` = 200. (page-1 + Sch B DNI/IDD engine + Sch G tax.)
    - **(b) `SCHEDULE_K1_1041`** — `load_1041_schedule_k1.py`; 29 facts / 7 rules / 17 lines / 6 diag / 6 tests /
      4 FA; full verbatim box codes; `validate_1041_k1.py` 18/0; `lookup/SCHEDULE_K1_1041/export/` = 200.
    - **(c) `GA501`** — `load_ga501.py`; 19 facts / 7 rules / 14 lines / 8 diag / 5 tests / 4 FA; resident-only;
      `validate_ga501.py` 16/0; `lookup/GA501/export/` = 200.
  - **Status: ✅ DONE (RS).** Sch I AMT RED-defer (D-2) satisfied via `D_1041_AMT`. **tts app build = the [APP] lane
    (dispatch when CC has a lane).** Next 1041-family authoring order: **[WO-10] Form 5227** split-interest trusts.
- **▶ ACTIVE — [WO-10] Form 5227 · Split-Interest Trust Information Return · greenfield RS-first · status
  `GAP-CHECKED → DRAFTING (research)` (opened 2026-07-05, spun off from S-11 D-10).**
  Gap-check: all candidate keys (`5227`, `CRAT`, `CRUT`, `POOLED_INCOME_FUND`, `5227_SCHA`) 404 GAP (99 forms);
  greenfield (only on-disk ref = the spine's `D_1041_PIF` routing note). Covers the §664 split-interest family:
  charitable remainder trusts (CRAT §664(d)(1) / CRUT §664(d)(2)), pooled income funds (§642(c)(5)), and
  §4947(a)(2) split-interest trusts; the **§664(b) four-tier character-ordering** of CRT distributions is the
  compute heart. **✅ Research-verified** (3 passes, verbatim vs FINAL 2025 Form 5227 Created 5/7/25 + i5227
  Dec 3 2025 + IRC §664/§642(c)/§4947 + Reg §1.664-1(d)) → **`f5227_source_brief.md`**. Caught the stale
  Part IV-A/IV-B layout (2025 = flat Part I–IX + Schedule A I–V).
  - **✅ Gate-1 scope LOCKED (2026-07-05, DECISIONS D-11):** CRAT + CRUT compute the §664(b) tier engine
    (**tier-level** — ordinary→capgain→other→corpus + accumulation carryforward + category-isolation netting;
    capital gain as ONE class, no within-Tier-2 rate split); PIF/CLT/§4947-other = structure + diagnostics;
    CRT qualification (5–50% payout / 10% remainder / 5% exhaustion) = diagnostic (funding-time, no §7520/
    mortality compute); §664(c)(2) **100% UBTI excise** COMPUTED (year-keyed post-2006) + Form 4720 route +
    Part VIII §4941/4943/4944/4945 screening diagnostics. One consolidated `5227` form.
  - **✅ DONE — seeded + exported 2026-07-05** (Ken Gate-1: "Approve — flip, seed, export"; W1-W4 blessed).
    `load_5227.py`: 23 facts / 8 rules / 12 lines / 11 diag / 6 tests / 4 FA; all rules cited (5 sources);
    SQLite-validated `scratchpad/validate_5227.py` 20/0. Seeded → **100 TaxForms / 475 FlowAssertions / 867 FormRules**;
    `lookup/5227/export/` = 200. **Status: ✅ DONE (RS).** tts app build = [APP] lane. The 1041 family (S-11 + WO-10)
    is now fully authored on the RS side. Carried [UNVERIFIED] clauses noted in the loader for re-pull if a deeper compute leg is scoped.
- **▶ ACTIVE — [WO-11] S-13 · 1120 C-corp module · greenfield RS-first · status `INTAKE → GAP-CHECKED → DRAFTING (research)` (opened 2026-07-05, DECISIONS D-12; Ken: "build 1120").**
  Ken added the **C corporation (Form 1120)** to the season-one plan (a scope-add beyond the original 1040/1120-S/1065/1041
  set — a NEW entity type nothing else covers). Ran the front door from step 1.
  **✅ GAP-CHECK (2026-07-05, live prod 100 forms):** required set (BUILD_ORDER S-13) vs coverage —
  - **Spine** (`1120`, page-1 income L1–11 / deductions L12–29 / taxable income L30 / §11 21% tax L31) → **GAP**
  - **Schedule C** (`1120_SCHC`, dividends + §243/§245A DRD) → **GAP**
  - **Schedule J** (`1120_SCHJ`, tax computation Part I + payments Part II) → **GAP**
  - **Schedule K** (other information) → **GAP**  ·  **Schedule L** (balance sheet) → **GAP**
  - **Schedule M-1 / M-2** (book-tax recon / unappropriated R/E) → **GAP**
  - **GA Form 600** (`GA600`, net income + net worth tax) → **GAP** (only the S-corp `GA600S` exists)
  - **✅ CONFIRMED already cover C-corp `1120`** (no authoring): `1125A` `['1120S','1065','1120']` (COGS),
    `1125E` `['1120S','1120']` (officer comp), `3800`, `4562`, `4797`, `8949`, `7004` — all carry `1120` in entity_types
    (verified live, like the 1065-core 8825/4562/3800 confirmation).
  - **➡ 8 gaps to author.**
  - **✅ RESEARCH-VERIFIED (2026-07-05, 3 parallel passes, verbatim vs FINAL sources) → `f1120_source_brief.md`.**
    Federal face: Form 1120 (2025) **Created 9/26/25**; caught OBBBA restructure — Sch J is now one continuous list
    to L23 (no Part I/II), page-1 total tax = Sch J **L12**; new L25 (Form 7205), L32 (§1062/Form 1062). IRC: §11 21%,
    §243 50/65/100% DRD, §246(b) TI-limit + loss exception, §172 80%/no-carryback/indefinite, **§163(j) EBITDA basis
    RESTORED for TY2025 (OBBBA)** + $31M §448(c), §55 CAMT 15%/$1B/Form 4626, §541 PHC 20%, §531 AET 20%/$250k-$150k.
    GA 600: rate **5.19%** (HB 111), net worth tax **Schedule 2** table (≤$100k=$0, max $5,000 over $22M), single-factor
    gross-receipts (6 dec), conformity Jan 1 2025 (HB 290, OBBBA not adopted). **⚠ GA §179 2025 = $1,250,000/$3,130,000**
    (GA indexes; the $1.05M/$2.62M in CLAUDE.md is the 2021 figure — STALE; flag + check GA700/GA600S).
  - **✅ Gate-1 scope walk APPROVED 2026-07-05 (DECISIONS D-13, all 4 recommended):** form shape = spine + 2
    (`1120` / `1120_SCHL` / `GA600`); Sch C = domestic DRD + §246(b) limit; federal = NOL 80% compute, §163(j)/
    CAMT/PHC/AET/§1062 screen+route; GA 600 = full (income + net worth + depr delta).
  - **✅ AUTHORED + SQLite-VALIDATED 2026-07-05 (READY_TO_SEED=False, awaiting Ken review walk W1-W10):**
    `load_1120_spine.py` (`1120`, 35 facts / 11 rules / 11 lines / 10 diag / 8 tests / 4 FA),
    `load_1120_schl.py` (`1120_SCHL`, 27 / 7 / 5 / 5 / 6 / 3), `load_ga600.py` (`GA600`, 15 / 6 / 6 / 5 / 8 / 3).
    `scratchpad/validate_1120.py` = **55 pass / 0 fail** (caps clean 159 checked; all rules cited; DRD 50/65/100
    + §246(b) limit + loss exception, §172 NOL 80%, §11 21%, Sch L balance/M-1/M-2 ties, GA 5.19% + §179 delta
    + net worth table all green).
  - **✅ DONE — seeded + exported 2026-07-05** (Ken Gate-1: "Approve — flip, seed, export"; W1-W10 blessed).
    Flipped all three guards → seeded to prod → **103 TaxForms**; `lookup/{1120,1120_SCHL,GA600}/export/` all = 200
    (65 KB / 24 KB / 24 KB; facts/rules/line_map/diagnostics all present). Spun off the stale GA §179 fix
    (`task_1c8d891e`: CLAUDE.md $1.05M/$2.62M → $1.25M/$3.13M + re-check GA700/GA600S). **Status: ✅ DONE (RS).**
    tts app build = [APP] lane. Carried [UNVERIFIED] flags noted in the loaders (§11 label, §246(b) combined
    50/65 worksheet, TY2026 §163(j) capitalized-interest) for re-pull if a deeper compute leg is scoped.
    Confirmed covering 1120 (no authoring): 1125-A/1125-E/3800/4562/4797/8949/7004.
- **▶ ACTIVE — [WO-12] State C-corp batch · SC1120 + AL Form 20C + NC CD-405 · greenfield RS-first · status
  `GAP-CHECKED → DRAFTING (research)` (opened 2026-07-05; Ken: "state C corp rules", batch the reuse-states).**
  Extends the federal 1120 module (WO-11) to GA's income-tax neighbors' C-corp returns. **✅ GAP-CHECK (live prod
  103 forms):** all three are GAPs — SC has `SC1120S` (S-corp) but no `SC1120` (C-corp); AL/NC have only their
  individual returns (`AL_FORM_40`, `NC_D400`). Ken picked SC1120 first + BATCH the three reuse-states (each reuses
  conformity sources already seeded: SC ← `load_sc1040`/`load_sc_passthrough`, AL ← `load_al_form40`, NC ←
  `load_nc_d400`; via `EXISTING_SOURCES_TO_REFERENCE`). FL F-1120 / TN FAE 170 = later greenfield orders.
  - **SC1120** — SC C-corp income tax (5% flat) + license fee (capital × .001 + $15, min $25); federal-TI start;
    single-factor apportionment; §168(k)/§179 non-conformity. Reuses SC1120S structure. → **GAP**
  - **AL Form 20C** — AL corporate income tax (6.5%); federal-TI start; apportionment; the AL federal-income-tax
    deduction question (verify C-corp treatment); §168(k)/§179. → **GAP**
  - **NC CD-405** — NC C-corp income tax (phasing down — verify TY2025 rate); federal-TI start; single sales-factor
    apportionment; NC 85% bonus add-back (Jan 1 2023 conformity freeze). → **GAP**
  - **✅ RESEARCH-VERIFIED (2026-07-05, 3 parallel passes, verbatim vs FINAL 2025 sources) → `state_ccorp_batch_source_brief.md`.**
    SC1120 (Rev. 7/2/25): 5% flat + license fee ($15 + capital×.001, min $25) + §168(k) decouple + §179
    $1.25M/$3.13M (12/31/2024 conformity); **⚠ H.3368 OBBBA-pending = live wire, retroactive TY2025 risk, SC
    deadline extended to Oct 15 2026**. AL 20C: 6.5% + **⚠ FIT deduction NOT repealed** (Amendment 662, L11a/Sch E —
    premise overturned) + **AL CONFORMS to §168(k)/§179** (no add-back; GILTI §40-18-35.2 + §174 §40-18-62 are the
    real decouples) + single sales factor; due May 15 (1 mo after federal). NC CD-405: income **2.25%** (S.B. 105
    phase-down) + **franchise tax** ($1.50/$1,000 net worth, first $1M cap $500, min $200, **net-worth-only base** —
    3-way test repealed 2017) + 85% bonus add-back + §179 $25k/$200k + single sales factor 4-dec (Jan 1 2023 conformity).
  - **✅ Gate-1 scope walk APPROVED 2026-07-05 (DECISIONS D-14, all 4 recommended):** full compute all three;
    AL FIT deduction = compute apportioned; SC = author current law + H.3368 flag; AL GILTI/§174 = diagnostic+direct-entry.
  - **✅ AUTHORED + SQLite-VALIDATED 2026-07-05 (READY_TO_SEED=False, awaiting Ken review walk W1-W9):**
    `load_sc1120.py` (`SC1120`, 11 facts / 6 rules / 5 lines / 5 diag / 6 tests / 3 FA), `load_al_form20c.py`
    (`AL_FORM_20C`, 12 / 5 / 5 / 6 / 4 / 2), `load_nc_cd405.py` (`NC_CD405`, 12 / 6 / 4 / 5 / 6 / 3).
    `scratchpad/validate_state_ccorp.py` = **41 pass / 0 fail** (caps clean 88; all rules cited; SC 5%+license+§179,
    AL 6.5%+apportioned FIT+GILTI, NC 2.25%+net-worth franchise table+85% bonus/§179 all green).
  - **✅ DONE — seeded + exported 2026-07-05** (Ken Gate-1: "Seed all three now"; W1-W9 blessed). Flipped all three
    guards → seeded → **106 TaxForms**; `lookup/{SC1120,AL_FORM_20C,NC_CD405}/export/` all = 200 (22/20/19 KB).
    Auto-discovered by `seed_all` (reconstructable). **Status: ✅ DONE (RS).** tts app build = [APP] lane.
    **⚠ SC carried caveat:** authored to the ENACTED 12/31/2024 law + `D_SC1120_H3368` flag; if H.3368 passes
    (adopting OBBBA retroactively for TY2025), SC1120 needs a §179/bonus amend ($2.5M/$4M, drop the add-back) —
    Ken accepted. FL F-1120 / TN FAE 170 = later greenfield orders.
- **▶ ACTIVE — [WO-13] NC + AL pass-through entity batch · greenfield RS-first · status `GAP-CHECKED → DRAFTING
  (research)` (opened 2026-07-05; Ken: "do the NC + AL"; SPINE S-15).** Completes the adjacent-state PASS-THROUGH
  track (SC pass-through done via SC1065/SC1120S/PTET, D-9; the individual + C-corp sides done for AL/NC/SC).
  **✅ GAP-CHECK (live prod 106 forms):** all pass-through keys GAP — NC has NC_D400(1040)+NC_CD405(1120) but no
  D-403/CD-401S; AL has AL_FORM_40(1040)+AL_FORM_20C(1120) but no Form 65/20S. Required set:
  - **NC D-403** (partnership, 1065) + **NC CD-401S** (S-corp, 1120S) + the **NC Taxed PTE** election
  - **AL Form 65** (partnership, 1065) + **AL Form 20S** (S-corp, 1120S) + the **Alabama Electing PTE** tax (Act 2021-1)
  - Reuse: NC 85% bonus/§179 $25k/$200k + Jan 1 2023 conformity (as NC D-400/CD-405); AL conforms §168(k)/§179 +
    GILTI/§174 (as AL 20C). Template = `load_sc_passthrough.py` (two forms one loader) + the SC PTET pattern.
  - ⚠ Each state's PTET DIFFERS — verify, never clone GA: NC Taxed-PTE (rate = individual 4.25% for 2025? owner-side
    DEDUCTION not credit — verify) vs AL Electing-PTE (5%, owner-side CREDIT). NC franchise applies to S-corps (CD-401S).
  - **✅ RESEARCH-VERIFIED (2026-07-05, 2 parallel passes, verbatim vs FINAL 2025 NCDOR/ALDOR) → `nc_al_passthrough_source_brief.md`.**
    **NC Taxed PTE:** 4.25% (individual rate); owner side = **DEDUCTION** (income removed from NC AGI via NC-PE);
    base = resident full + nonresident NC-source; 85% bonus/§179 $25k/$200k decouple; **CD-401S computes NC
    franchise** ($1.50/$1,000, $500 first-$1M cap, $200 min — as CD-405); nonresident withholding 4.25%; conformity
    Jan 1 2023; due Apr 15. **AL Electing PTE:** 5%; owner side = **refundable CREDIT** (Sch EPT-C); computed on
    **Form EPT** (65/20S Sch K L23/L25 reference it); election = checkbox + Form EPT + >50% consent; **AL CONFORMS
    to §168(k)/§179** (no add-back); composite PTE-C 5%; Form 20S non-electing = LIFO/BIG/excess-passive only; BPT
    separate; due Mar 15. ⚠ AL conformity item-by-item (not blanket). [UNVERIFIED] exact NC/AL line numbers (PDFs
    didn't extract) — re-pull before seeding.
  - **✅ Gate-1 scope walk APPROVED 2026-07-05 (DECISIONS D-15, all 4 recommended):** full compute both states;
    encode NC deduction + AL credit; AL non-electing S-corp taxes = diagnostic+direct-entry; 2 loaders state-paired.
  - **✅ AUTHORED + SQLite-VALIDATED 2026-07-05 (READY_TO_SEED=False, awaiting Ken review walk W1-W6):**
    `load_nc_passthrough.py` (`NC_D403` 1065 + `NC_CD401S` 1120S) + `load_al_passthrough.py` (`AL_FORM_65` 1065 +
    `AL_FORM_20S` 1120S). `scratchpad/validate_nc_al_pt.py` = **47 pass / 0 fail** (caught 2 topic_name > 255 caps,
    trimmed; NC Taxed-PTE 4.25%/franchise/NRW/85% add-back + AL Electing-PTE 5%/composite/Line-32 all green; all 16
    rules cited).
  - **✅ DONE — seeded + exported 2026-07-05** (Ken Gate-1: "Approve — flip, seed, export"; W1-W6 blessed). Flipped
    both guards → seeded → **110 TaxForms**; `lookup/{NC_D403,NC_CD401S,AL_FORM_65,AL_FORM_20S}/export/` all = 200.
    Auto-discovered by `seed_all` (reconstructable). **Status: ✅ DONE (RS).** tts app build = [APP] lane. The
    adjacent-state pass-through track is now COMPLETE (GA-700 + SC1065/SC1120S + NC + AL). [UNVERIFIED] exact NC/AL
    line numbers noted for a re-pull. **Post-WO-13: net-new RS scope needs the TaxWise forms-usage report or a law change.**
- **✅ S-5 completed the front-door loop 2026-07-05** (GAP-CHECKED → DRAFTING → AWAITING KEN → seeded/exported).
  New consolidated `ENTITY_BOUNDARY` form (`load_entity_boundary.py`, 6 self-owned sources): B1 M-3 threshold
  (1065 4-prong / 1120-S $10M); B2 K-2/K-3 DFE 4-criteria gate (COMPUTED, RED on fail + D_EB_DFE_OK affirmative
  record); B3 §704(c) indicator; B4 §754/§743(d)/§734(d) ($250k triggers); B5 apportionment (P.L. 86-272).
  SQLite-validated (ALL PASS) → seeded to prod (**96 TaxForms / 457 FlowAssertions**) → `lookup/ENTITY_BOUNDARY/
  export/` = 200. `boundary_diag_source_brief.md`. BUILD_ORDER S-5 ticked [RS]✅→[APP]⬜. Caveats: M-3 instr not
  annual (1065 Rev 11/2023, 1120-S Rev 12/2019); apportionment state-specific (re-verify per state). **Next: tts app dispatch.**
  PRODUCT_MAP scope: wire the Core boundary diagnostics so Core never goes silent when a return crosses into
  module territory. Gap-check (existing vs gap):
  - **M-3 threshold** → EXISTS: `D_L_M3` / `R-L-M3` on 1065_L (≥$10M assets / ≥$35M receipts / ≥50% REP, sourced).
    Verify 1120-S side ($10M) has an equivalent.
  - **§754 / §743(b) / §734(b)** → EXISTS: 1065_B Q10 + `IRC_754` (basis-adjust math RED-deferred). Adequate flag.
  - **§704(c)** → EXISTS: `D_SCHK_704C` structure-only (item M/N). Adequate boundary flag.
  - **K-2/K-3** → PARTIAL: `D_SCHK_K3` is a **blanket "out of scope" RED-defer** — but PRODUCT_MAP makes the
    **DFE determination** ("record WHY K-2/K-3 aren't required") CORE season one. **GAP: the DFE-fail criteria diagnostic.**
  - **Multistate apportionment (beyond-licensed-state)** → **GAP: no indicator found.**
  - (§461(l) boundary = DONE via S-6 Form 461; 1041 Sch I AMT = defer to S-11 per D-2.)
  - **Next:** research-verify (M-3 thresholds 1065+1120S; K-2/K-3 DFE 2025 criteria; §704(c)/§754 triggers;
    apportionment nexus) → source brief → Gate-1 scope walk (incl. the shape: amend existing forms vs a
    consolidated boundary-diagnostics reference). Research pass running.
- **Other open SPINE authoring rock:** S-11 1041 (WO-09, Sept greenfield).
- **✅ S-6 completed the front-door loop 2026-07-05** (GAP-CHECKED → DRAFTING → AWAITING KEN → seeded/exported).
  Scope (Ken-approved, all recommended): R1 self-rental + R2 PTP = COMPUTE; R3 REP = checkbox + §1.469-9(g)
  election flag; R4 at-risk = diagnostic-only (route to 6198); R5 §461(l) = diagnostic, thresholds $313k/$626k.
  Authored: R1-R4 amend `load_1040_schedule_e.py` (FORM_8582/SCHEDULE_E home loader; REP RED-defer→checkbox);
  R5 = new `load_1040_form_461.py` (form `461`). SQLite-validated (`scratchpad/validate_pal.py`, ALL PASS) →
  **seeded to prod (95 TaxForms / 454 FlowAssertions)** → `lookup/{FORM_8582,SCHEDULE_E,461}/export/` all **200**.
  `pal_basis_source_brief.md`. Carried caveats: Form 461 face line-numbering mapped to the §461(l)(3) mechanic
  (i461 `requires_human_review`); disallowed-EBL→NOL year-keyed (re-verify each season). **Next: tts app dispatch.**
  Required set / gap-check (recorded at open):
  - R1 self-rental recharacterization → **amend `FORM_8582`** (home `load_1040_schedule_e.py`, v1 bucket) — exists.
  - R2 PTP per-entity segregation → **amend `FORM_8582`** — exists.
  - R3 REP (real estate professional) tests/checkbox → **amend `FORM_8582` / `SCHEDULE_E`** — exists.
  - R4 at-risk diagnostic → **`6198`** (exists; integrated by 4835) — amendment/diagnostic.
  - R5 §461(l) excess-business-loss diagnostic → **NEW = the one real GAP**; 2025 thresholds need source-pinning (indexed, OBBBA-permanent).
  - **Next:** research-verify authorities (§469 self-rental Reg. 1.469-2(f)(6); §469(k) PTP; §469(c)(7)
    REP; §465 at-risk; §461(l) 2025 thresholds) → source brief → Gate-1 scope walk → author
    `READY_TO_SEED=False` → validate on SQLite → seed → export.
- **Other open SPINE authoring rocks:** S-5 Boundary diagnostics (WO-04); S-11 1041 (WO-09, Sept greenfield).

## Status reconciliation (against live STATUS.md + on-disk loaders, 2026-07-05)
- **[WO-01]** 1040 ATS S3/S4 gaps — **✅ DONE (RS)** · 4835 + 8835 + 8936 (+8936_SCHA) all
  seeded/exported, all four `lookup/<form>/export/` = 200 · tts building S3/S4 mappers (SPINE S-1).
- **[WO-02]** 1065 core — **✅ DONE** · campaign complete 2026-07-04: all 6 forms (Schedule K
  spine `1065_PAGE1`+`SCH_K_1065`, K-1+alloc, M-1/M-2, L/B seeded+exported = 200; 8825/4562/3800
  cover 1065); the 7-form batch is in `approved_specs.py`. *(BUILD_ORDER S-4 still lists these
  unticked + "▶ NEXT authoring = Schedule K" — a stale mark; the canonical file's own "never trust
  a stale mark" rule says correct it. S-4 [RS] = DONE; only [APP] issuer-side K-1 persistence remains.)*
- **[WO-05]** SC1040 (+ Schedule NR) + SC entity (SC1065/SC1120S/PTET) — **🟡 AUTHORED** ·
  seeded/exported = 200; not yet in the approved manifest (SPINE S-7).
- **[WO-06]** AL Form 40 — **🟡 AUTHORED** · `lookup/AL_FORM_40/export/` = 200 (SPINE S-8).
- **[WO-07]** NC D-400 — **🟡 AUTHORED** · `lookup/NC_D400/export/` = 200 (SPINE S-9).
- **[WO-08]** GA-700 + PTET — **🟡 AUTHORED** · `lookup/GA700/export/` = 200 (SPINE S-10; ⚠ app
  build gated behind S-4 — GA partnership numbers depend on the federal 1065 flow).
- **[WO-03] / [WO-04] / [WO-09]** — INTAKE, genuinely open = SPINE **S-6 / S-5 / S-11**.

## ✅ DONE (recent — proves the pipeline)
- 1065 core (Schedule K → K-1 → M-1/M-2 → L/B) — 2026-07-04 · spec→seed→export (all 200).
- 1065 SE (line 14a) — 2026-07-01 · spec→seed→export→build→DB-verified.
- 4797 recapture classification + nuance legs — 2026-07-02 · caught the K8c→K9c misroute.
- GA-500 HB 463 tips/OT exclusions — 2026-07-02.

---

## Maintenance
- Lives in RS repo root + the tts-tax-status mirror (`rule-studio/`). CC boot list.
- The CHANGE_REGISTER (when built) drops triaged law-change items into INTAKE as new orders.
- Completion ping reuses the existing Pushover hook: draft ready → notify Ken → approve.
