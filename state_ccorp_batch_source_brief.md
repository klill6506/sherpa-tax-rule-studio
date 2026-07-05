# State C-Corp Batch (WO-12) — Source Brief: SC1120 · AL Form 20C · NC CD-405

*Greenfield RS-first authoring brief for the reuse-state C-corporation returns, extending the federal
1120 module (WO-11). GA's income-tax neighbors AL/NC/SC on the C-corp side. Opened 2026-07-05
(Ken: "state C corp rules", batch the reuse-states). Front-door step: GAP-CHECKED → research-verified
(this file) → Gate-1 scope walk → author.*

**Every fact below verified VERBATIM against FINAL 2025 state DOR sources by three parallel research
passes (never memory), per the Authoritative-Source Rule. Two passes OVERTURNED a premise — noted.**

---

## Gap-check (live prod, 103 forms, 2026-07-05)
All three are GAPs. SC has `SC1120S` (S-corp) but no `SC1120` (C-corp); AL/NC have only their individual
returns (`AL_FORM_40`, `NC_D400`). Each reuses conformity/statute sources already seeded (via
`EXISTING_SOURCES_TO_REFERENCE` or re-declared idempotently by source_code). All start from **federal
taxable income** (federal 1120 L30) — they consume the WO-11 federal 1120 output.

Form keys to author: **`SC1120`**, **`AL_FORM_20C`**, **`NC_CD405`** (one form each).

---

## Common shape (all three)
Federal taxable income → state additions/subtractions (esp. depreciation) → apportionment (single
sales factor) → state taxable income → state NOL → **state income tax rate** → + a **companion tax**
(SC license fee / NC franchise tax; AL none on the return). No entity-level PTET (those are the
pass-through returns, already done for SC).

---

## SC1120 — South Carolina C Corporation (Rev. 7/2/25; SC1120I 2025; SCTIED-2025 Ch.2 Sept 2025)
- **Rate: 5% flat** (Part I L7 "multiply line 6 by 5%"; S.C. Code §12-6-530).
- **Start:** federal taxable income (L1) → Schedule A&B net adjustment (L2) → SC net income (L6) → 5% (L7) →
  Part II license fee → grand total (L30). SC NOL: federal carryforward period, **no carryback** (§12-6-1130(4)).
- **§168(k): SC fully DECOUPLES** (§12-6-50) — add back the federal-vs-SC depreciation difference in the
  placed-in-service year; recover the extra SC depreciation over the remaining life (separate SC schedule;
  different SC basis → Schedule B disposition adjustment). Timing/basis difference, not permanent.
- **§179: SC conforms at its 12/31/2024 IRC level (pre-OBBBA) = $1,250,000 / $3,130,000** for 2025 (DERIVED
  from pre-OBBBA §179 at 2025 indexing — SCDOR prints no figure; matches SC1040/SC1120S). §179 is NOT on the
  §12-6-50 non-adopted list.
- **License fee (Part II L21):** "multiply line 20 [total capital + paid-in surplus] by .001 then add $15
  (min $25 per taxpayer)" (§12-20-50; apportioned per §12-20-60 but the $25 min is not apportioned).
  **Same mechanic as SC1120S.**
- **Apportionment:** single sales factor (Sch H-1, TPP) / gross-receipts ratio (Sch H-2, service) (§12-6-2252/2290).
  **Decimals NOT specified** on the form — do NOT encode a fixed precision.
- **Conformity: IRC through 12/31/2024** (§12-6-40). **Due 15th day of 4th month = April 15, 2026** (SC1120-T extension, file-only).
- **⚠ LIVE WIRE — H.3368 / OBBBA (UNVERIFIED, IN FLUX):** SC has NOT adopted OBBBA as of ~March 2026;
  **H.3368** (pending, not signed) would adopt full OBBBA conformity **retroactive to TY2025**, which would
  flip the §168(k) decouple and §179 to $2.5M/$4M. **SCDOR extended the TY2025 SC filing deadline to Oct 15,
  2026** specifically to await H.3368. Author to CURRENT law (12/31/2024) with a prominent year-keyed flag;
  **re-verify H.3368's status before seeding.**
- **SC1120 vs SC1120S (in tool):** C-corp = full 5% on all SC taxable income; reuses SC1120S license fee,
  apportionment, depreciation add-backs, conformity. No ATB/PTET (that's the S-corp).

## AL Form 20C — Alabama Corporation Income Tax (2025 Form 20C `*2500012C*`; 2025 instr; ALDOR OBBBA summary Nov 10 2025)
- **⚠ PREMISE OVERTURNED — the FIT deduction is NOT repealed.** The research pass DISPROVED the assumption
  that Act 2021-1 repealed the C-corp federal income tax deduction. It is **constitutionally protected
  (Amendment 662)** and computed on the 2025 Form 20C: **page-1 L11a "Federal income tax deduction/(refund)
  (from Schedule E)"**, off **Schedule E** (12-line apportioned computation; §40-18-35(a)(2)). Both AL Form 40
  (individuals) and Form 20C keep it. **Must encode L11a + Schedule E.** (Note WHY in the spec so a future
  editor recalling Act 2021-1 doesn't "correct" it away.)
- **Rate: 6.5% flat** (L15 "Alabama Income Tax (6.5% of line 14)"; capped by Amendment 662).
- **Start:** federal taxable income (L1, before federal NOL) → Schedule A additions/subtractions → apportionment
  (L7) → AL income before FIT deduction (L10) → − FIT deduction (L11a) → AL taxable income (L14) → 6.5% (L15).
  NOL = 15-yr carryforward, no carryback (Schedule B).
- **§168(k)/§179: AL fully CONFORMS** (rolling conformity §40-18-1.1; OBBBA flows through). AL bonus = 100%;
  **AL §179 = full federal $2.5M / $4M for 2025.** **NO GA-style depreciation add-back** — the OPPOSITE of
  SC/NC/GA. Only the legacy **2008 Economic Stimulus Act** basis difference decouples (Sch A L21).
- **Real AL decouples (not depreciation):** **GILTI/§951A** (§40-18-35.2 — Sch A L23 subtract §951A, L9 add back
  §250) and **§174/§174A R&E** (§40-18-62 — Sch A L24 deduct full R&E, L10 add back federal amortization).
- **Apportionment: single sales factor** (Schedule D-1, post-Act 2021-1, effective 1/1/2021; throwback repealed).
  Filing statuses 1 (AL-only) / 2 (multistate D-1) / 3 (≤$100k AL sales = 0.25% of sales) / 4 (separate acctg) / 5.
- **Business Privilege Tax = SEPARATE return** (Form CPT), NOT on 20C — only an informational checkbox
  (page-4 Other Info L10). Do NOT compute BPT here.
- **Conformity: rolling/automatic** (§40-18-1.1); OBBBA adopted for 2025 for "tied" items.
- **Due: ONE MONTH after federal = May 15, 2026** (calendar-year; unusual). Extension file-only (Act 2022-53).

## NC CD-405 — North Carolina C Corporation (2025 CD-405 instr Web 1-26; NCDOR rates; G.S. §105)
- **Combined FRANCHISE + INCOME return.**
- **Income tax rate: 2.25%** for TY2025 (S.B. 105 phase-down: 2.5% 2024 → **2.25% 2025** → 2% 2026 → 1% 2028 →
  0% 2030). Applied to NC-apportioned net income (Schedule B).
- **⚠ FRANCHISE TAX — premise corrected — base is NET WORTH ONLY.** $1.50 per $1,000 (.0015) of net worth
  (Schedule C); **first $1,000,000 capped at $500**; over $1M = .0015 × excess + $500; **minimum $200** (no
  maximum except holding-company cap $150,000). The old "greatest of net worth / 55% ad valorem / NC tangible
  investment" three-way test was **repealed effective TY2017** — net worth is the SOLE base for 2025 (G.S. §105-122).
- **Start:** federal taxable income before NOL (Schedule G L7, IRC as of Jan 1 2023) → Schedule H additions/
  subtractions → apportionment (L14) → NC net income → 2.25%.
- **§168(k): NC decouples — 85% add-back** in the placed-in-service year; deduct in **5 equal installments
  (20%/yr)** over the next 5 years (G.S. §105-130.5B; instr p.8). **§179 = $25,000 limit / $200,000 investment**
  (statutory, §105-130.5B); add-back = (federal §179 − NC §179) × **85%**, recovered 20%/yr. Mirrors NC D-400.
- **Apportionment: single sales factor, 4 decimals** (Schedule O; market-based sourcing; §105-130.4).
- **Conformity: IRC as of January 1, 2023** (frozen; OBBBA explicitly NOT adopted for TY2025 — instr p.7).
- **Due: 15th day of 4th month = April 15, 2026** (franchise + income); extension CD-419 (7 months, file-only).

---

## Reuse map (authority sources)
- **SC:** re-declare `SC_ACT63_2025_CONFORMITY` (12/31/2024) + `SC_RR_05_2_DEPR` + a new `SC_2025_SC1120` form
  source + `SC_CODE_12_20_50` (license fee) + `SC_CODE_12_6_530` (rate). SC §179 constants $1.25M/$3.13M (as SC1040/SC1120S).
- **AL:** reuse `AL_CODE_40_18_5`/`AL_CODE_40_18_15` + new `AL_2025_FORM_20C` + `AL_AMEND_662` (FIT deduction) +
  `AL_CODE_40_18_35` (FIT/GILTI). AL §179 = federal (conforms).
- **NC:** reuse `NC_2025_SCHEDULE_S` conformity + new `NC_2025_FORM_CD405` + `NC_GS_105_130_5B` (bonus/§179) +
  `NC_GS_105_122` (franchise). NC §179 constants $25k/$200k, 85% add-back (as NC D-400).

## Carried [UNVERIFIED] / flags (re-verify before seeding)
- **[SC — LIVE WIRE]** H.3368 OBBBA conformity: if enacted, SC §168(k)/§179 flip retroactively for TY2025
  ($2.5M/$4M, no add-back). Filing deadline extended to Oct 15 2026. Author to 12/31/2024 law + prominent flag; RE-VERIFY.
- **[SC]** apportionment decimal precision not printed — do not assert.
- **[SC/NC §179]** $1.25M/$3.13M (SC) and $25k/$200k (NC) are year-keyed / statute-derived — re-verify each season.
- **[AL]** FIT deduction Schedule E consolidated-filer lines 1-5 simplified if the compute is direct-ratio.
- **[NC]** CD-419 extension = 7 months (confirm if extension logic is encoded).
- Re-verify all rates at TY2026 (NC phases to 2%; SC/AL rates; the state §179 tracks).

---

## Proposed authoring legs (subject to Gate-1 scope walk)
Three forms, one loader each: `load_sc1120.py`, `load_al_form20c.py`, `load_nc_cd405.py`. Each: federal-TI start
→ additions/subtractions (depreciation delta where the state decouples) → single-sales-factor apportionment →
state rate → state NOL → companion tax (SC license fee / NC franchise; AL none). Author `READY_TO_SEED=False`
→ SQLite-validate (CharField caps ≤ 20) → Ken review walk → seed → export = 200.
