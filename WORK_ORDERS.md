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

- **▶ ACTIVE — [WO-09] S-11 · 1041 module · greenfield RS-first · status `GAP-CHECKED → DRAFTING (research)` (opened 2026-07-05).**
  Gap-check run against live prod (96 forms) — **all five authoring surfaces are 404 GAPs**; the module is fully
  greenfield (no `load_1041_*` loaders; the only on-disk `1041` refs are the boundary-diag Sch I note + the *receiving*
  side in `load_1040_schedule_k1.py` where a 1040 imports a trust K-1). Required set from BUILD_ORDER S-11:
  - **Spine** (`1041`) — entity types / 2025 §1(e) rate schedule / §642(b) exemptions → **GAP**
  - **DNI / IDD / Schedule B** (`1041` or `1041_SCHB`) — §643(a) DNI, §651/§661 distribution deduction, tier/separate-share → **GAP**
  - **Schedule G** (`1041_SCHG`) — tax computation, cap-gain rates, §1411 NIIT on trusts/estates → **GAP**
  - **K-1 (Form 1041)** (`SCHEDULE_K1_1041`) — beneficiary distributive shares + character pass-through → **GAP**
  - **GA Form 501** (`GA501`) — Georgia fiduciary income tax return → **GAP**
  - **Schedule I (AMT)** — **RED-defer diagnostic only** (D-2, ruled 2026-07-04; do NOT author the compute).
  - **Next:** research-verify TY2025 authorities VERBATIM vs FINAL IRS/GA sources (2025 Form 1041 + i1041; Sch B/Sch G/
    K-1(1041) + instr; Rev. Proc. 2024-40 inflation figures; §643/§651/§661/§663(b)/§642(b)/§1(e)/§1411; GA DOR Form 501
    + instr) → `f1041_source_brief.md` → Gate-1 scope walk (AskUserQuestion). **Research pass running.**
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
