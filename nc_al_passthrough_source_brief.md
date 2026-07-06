# NC + AL Pass-Through Batch (WO-13) — Source Brief: D-403 / CD-401S · Form 65 / Form 20S

*Greenfield RS-first authoring brief for the North Carolina + Alabama pass-through entity returns and
their PTETs. Completes the adjacent-state pass-through track (SC done via SC1065/SC1120S/PTET, D-9;
GA via GA-700). Opened 2026-07-05 (Ken: "do the NC + AL"; SPINE S-15). Front-door step: GAP-CHECKED →
research-verified (this file) → Gate-1 scope walk → author.*

**Every fact below verified VERBATIM against FINAL 2025 NCDOR/ALDOR sources by two parallel research
passes (never memory), per the Authoritative-Source Rule.**

---

## Gap-check (live prod, 106 forms, 2026-07-05)
All four pass-through keys GAP. NC has NC_D400(1040) + NC_CD405(1120); AL has AL_FORM_40(1040) +
AL_FORM_20C(1120) — no pass-through returns. Form keys to author: **`NC_D403`**, **`NC_CD401S`**,
**`AL_FORM_65`**, **`AL_FORM_20S`**. Template = `load_sc_passthrough.py` (two forms one loader) + the
SC/GA PTET pattern. Reuses NC/AL conformity + the C-corp depreciation work (CD-405 / AL 20C).

---

## The headline contrast — each state's PTET is DIFFERENT (verify, never clone GA)
| | **NC Taxed PTE** | **AL Electing PTE** |
|---|---|---|
| Statute | §105-131.7 (Taxed S Corp) / §105-154(c) (Taxed Ptnr); S.L. 2021-180 | Act 2021-1; §40-18-160 et seq. |
| Rate (TY2025) | **4.25%** (the individual rate) | **5%** (top individual rate) |
| Base | resident owners' ENTIRE share + nonresident owners' NC-source share | AL taxable income of the PTE (Sch K AL col L1-17), apportioned, × 5% |
| Owner side | **DEDUCTION** — owner removes the income from NC AGI (via NC-PE) | **REFUNDABLE CREDIT** — pro-rata share of the PTE tax (Schedule EPT-C) |
| Election | on the timely-filed D-403/CD-401S; annual; revocable before the due date | **checkbox on Form 65/20S + Form EPT**; annual; needs >50% owner consent |
| Computed on | the return itself (D-403/CD-401S) | **Form EPT** (the 65/20S only REFERENCE it: Form 65 Sch K L23 / Form 20S Sch K L25) |

> ⚠ **AL election-mechanic correction (research caught):** for TY2025 the election is the **Electing-PTE
> checkbox on Form 65/20S + Form EPT** — NOT the old standalone Form PTE-E (MAT). The EPT tax is a
> non-deductible state tax added back on Schedule A (Form 65 Sch A L4 / Form 20S Sch A L1).

---

## NORTH CAROLINA (D-403 partnership + CD-401S S-corp)
Sources: 2025 D-403/D-403A + CD-401S instructions; NCDOR PTE Important Notice (S.L. 2021-180); rates page.
- **Start:** D-403 = federal Form 1065; CD-401S = federal Form 1120-S. NC adjustments via **NC-PE** flow to owners.
- **Taxed PTE:** rate **4.25%** ("imposed at the individual income tax rate"); base = resident owners' entire
  share + nonresident owners' NC-source share; owner side = **DEDUCTION** ("may deduct the amount of the
  taxpayer's share of income from the Taxed PTE to the extent it was included in the Taxed PTE's NC taxable
  income"); nonresident owner of a Taxed PTE need not file (§105-131.7 / §105-154.1).
- **Depreciation (DECOUPLE — same as NC D-400/CD-405):** **85% bonus add-back** (recover 20%/yr over 5 yrs
  starting 2026); **§179 $25,000 / $200,000** (add-back = (federal − NC) × 85%). NC did NOT adopt §168(k) for 2025.
- **Apportionment:** single sales factor, **4 decimals** (§105-130.4).
- **⚠ CD-401S FRANCHISE TAX — YES (S-corps pay it):** Schedule C net-worth franchise, **$1.50/$1,000, first
  $1M cap $500, min $200** (holding cap $150k) — identical to CD-405. **D-403 partnerships pay NO franchise.**
- **Nonresident withholding:** the entity pays NC tax on each nonresident owner's NC-source share at **4.25%**
  (NC-NPA affirmation relieves it).
- **Conformity: IRC as of Jan 1 2023** (OBBBA NOT adopted) — same as NC D-400/CD-405.
- **Due: 15th day of 4th month = April 15, 2026** (both D-403 and CD-401S).
- **[UNVERIFIED — re-pull]** the 2025 D-403A/CD-401S instruction PDFs did not text-extract; exact line numbers
  (partner-schedule lines, Sch C franchise lines, NC-PE add-back lines) confirmed via other NCDOR pages —
  re-open the PDFs to pin exact labels before seeding. Due-date sentence = HIGH-confidence (NC 4th-month pattern).

## ALABAMA (Form 65 partnership + Form 20S S-corp)
Sources: ALDOR Electing-PTE pages; Form 65/20S instructions (TY2024 rev, rules reconfirmed for 2025); ALDOR
OBBBA Executive Summary (updated 11/10/2025); Act 2021-1.
- **Start:** Form 65 = federal 1065 (lines 1-22 straight from federal); Form 20S = federal 1120-S (lines 1-21).
- **Electing PTE (Form EPT):** rate **5%** ("applied to the calculated Alabama taxable income"); base = Sch K
  AL-column L1-17 (incl. guaranteed payments), apportioned; owner side = **REFUNDABLE CREDIT** (Schedule
  EPT-C); election = checkbox + Form EPT + >50% consent; EPT computed/paid on **Form EPT** (Form 65 Sch K L23 /
  Form 20S Sch K L25 reference it); EPT added back as a non-deductible state tax (Sch A).
- **Depreciation (CONFORMS — no add-back, same as AL 20C):** §168(k) bonus "Tied to Federal: Yes" (§40-18-15(a)(8));
  §179 $2.5M/$4M "Tied to Federal: Yes" (§40-18-15(a)(21)). §179 flows straight from federal (Form 65 Sch K L12 /
  Form 20S Sch K L11). Only the historical 2008 Stimulus-Act decoupling remains (Sch A).
- **⚠ Conformity is item-by-item, NOT blanket:** AL is rolling (§40-18-1.1) but ALDOR marks several OBBBA items
  "Tied to Federal: No" (§224 tips, §225 OT, enhanced §199A, §174 R&E). For the entity income base, bonus/§179
  DO flow through; do NOT encode a blanket "AL = full conformity" rule.
- **Apportionment:** single sales factor (Act 2021-1), 4 decimals.
- **Composite (Form PTE-C, §40-18-24.2):** 5% on nonresidents' AL-source share (separate filing; Sch K L22);
  PTE-R relief / Schedule NRC-Exempt (QIP) opt-out.
- **Form 20S non-electing entity taxes (Line 32):** ONLY the federal S-corp-level taxes — **LIFO recapture
  (§40-18-161), built-in gains (§40-18-174), excess net passive income (§40-18-175)**; otherwise passes through.
- **Business Privilege Tax = SEPARATE** (Form PPT; repealed for pass-throughs TY2024+) — NOT on Form 65/20S.
- **Due: 15th day of 3rd month = March 15, 2026** (Form 65/20S/EPT/PTE-C) — NO extra month (that's C-corp 20C only).

---

## Reuse map (authority sources)
- **NC:** re-declare `NC_2025_CD405_INSTR` + `NC_GS_105_CORP` (bonus/§179/franchise — as CD-405) + new
  `NC_2025_D403` / `NC_2025_CD401S` form sources + `NC_SL_2021_180` (Taxed PTE). NC constants $25k/$200k, 85%,
  4.25%, franchise ($1.50/$1,000, $500/$200/$150k). Reuse `_nc_franchise` mechanic from CD-405.
- **AL:** re-declare `AL_CODE_40_18` + `AL_2025_20C_INSTR` (conformity — as AL 20C) + new `AL_2025_FORM_65` /
  `AL_2025_FORM_20S` + `AL_ACT_2021_1` (Electing PTE). AL conforms bonus/§179; 5% PTET + composite.

## Carried [UNVERIFIED] / flags (re-verify before seeding)
- **[NC]** exact D-403/CD-401S/NC-PE line numbers (PDFs didn't extract) — re-pull; due-date sentence.
- **[AL]** exact TY2025 Sch K line numbers (25f65instr/25f20sinstr when ALDOR posts) — TY2024 rev used.
- **[AL]** encode OBBBA conformity item-by-item, not blanket.
- Re-verify NC rate (phasing) + AL rate + both PTETs + NC §179/franchise at TY2026.

## Proposed authoring legs (subject to Gate-1 scope walk)
Two loaders: `load_nc_passthrough.py` (`NC_D403` + `NC_CD401S`), `load_al_passthrough.py` (`AL_FORM_65` +
`AL_FORM_20S`). Each: federal start → depreciation delta (NC 85%/§179; AL conforms) → single sales factor →
the PTET (NC 4.25% deduction-side / AL 5% credit-side) + companion (NC franchise on CD-401S / AL composite 5%)
→ owner-side mechanic. Author `READY_TO_SEED=False` → SQLite-validate → Ken review → seed → export = 200.
