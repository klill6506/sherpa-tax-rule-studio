# AL Form 40 (Alabama Individual Income Tax) — Source Brief (TY2025)

*Prepared 2026-07-04 to kick off the **AL Form 40** authoring campaign (August RS state track,
"AL Form 40 — ⚠ federal income tax deduction quirk — budget Ken's longest walk"). TRANSCRIPTION
AID / reconcile map — **NOT a spec and NOT authorization to seed.** Per D-1, authored FRESH from
AL DOR primary sources, reconciled against the tts state compute, each mismatch a logged Ken
adjudication. Constants VERIFIED against the FINAL 2025 AL DOR PDFs (research agent, 2026-07-04);
§10 flags the few that need a last look. This is the **3rd state individual spec** (GA Form 500,
SC1040 precede it; `load_sc1040.py` + `load_ga500_form_500.py` are the structural precedents).*

---

## 1. Primary sources (all revenue.alabama.gov, TY2025 final)

- **Form 40 (blank)** — `25f40blk.pdf` (watermark `*25000140*`, "Jan 1 – Dec 31, 2025") —
  https://www.revenue.alabama.gov/wp-content/uploads/2026/01/25f40blk.pdf
- **Form 40 Booklet** (instructions + tax tables pp. 25-30 + worksheets p. 31) — `25f40bk.pdf`
  (updated Jan 2026) — https://www.revenue.alabama.gov/wp-content/uploads/2026/01/25f40bk.pdf
- **Rate statute** — Ala. Code §40-18-5 (2025); **FIT deduction statute** — §40-18-15 ("paid or
  accrued"). Landing: https://www.revenue.alabama.gov/forms/2025-alabama-individual-income-tax-return-residents-part-year-residents/

---

## 2. Structure — how Form 40 flows (verbatim labels; ⚠ builds AL gross income FROM SCRATCH)

**KEY: Alabama does NOT start from federal AGI or federal taxable income.** Form 40 builds Alabama
gross income line-by-line (wages from AL Schedule W-2, interest/dividends, other income), reaches
**Alabama AGI (line 10)**, then subtracts four deductions to taxable income. Conformity differences
are handled by **exclusion** (income simply not reported) or **Part II adjustments**, not an
add-back/subtraction schedule.

```
5b Wages (AL Schedule W-2)   6 Interest & dividends   7 Other income (pg2 Part I L8)
8  Total income (5b..7)      9 Total adjustments (pg2 Part II L16)   10 ALABAMA AGI = L8 − L9
11 Itemized OR Standard deduction (election)     12 FEDERAL TAX DEDUCTION (worksheet, §3)
13 Personal exemption        14 Dependent exemption (pg2 Part III)   15 Total deductions (11+12+13+14)
16 Taxable income = L10 − L15   17 Tax (tax table)   18 Net tax (Schedule OC option)
19 Additional taxes (Sch ATP)  20a/b campaign fund  21 Total liability
22 AL withholding  23 est/extension  25 refundable credits (Sch OC F6)  27 total payments
30 AMOUNT YOU OWE   31 penalties (Sch ATP)   32 overpaid   35 REFUND
```

**Page 2 — Part I other income** (→ L7): alimony, business (Fed Sch C), gain/loss (Sch D),
retirement (Sch RS), rents/royalties/K-1 (Sch E), farm (Fed Sch F), other. **Part II adjustments**
(→ L9): IRA, Keogh/SEP, early-withdrawal penalty, alimony paid, adoption, AL-location moving (Fed
3903), SE health ins, CollegeCounts 529/PACT, HSA, catastrophe savings, home-buyer savings, ABLE,
etc. **Part III dependents** (→ L14): count × the sliding-scale amount (§5).

---

## 3. THE FEDERAL INCOME TAX DEDUCTION — line 12 (the quirk; "longest walk")

**Line 12 "Federal tax deduction"; form warns "DO NOT ENTER THE FEDERAL TAX WITHHELD FROM YOUR
W-2(S)."** It is a **separate deduction from the itemized/standard election (L11)** — AL residents
get it whether they itemize or not. Liability-based, NOT cash/withheld. Booklet worksheet (p.31),
verbatim:

| WS | Text |
|---|---|
| 1 | Tax as shown on **line 22 of 2025 Form 1040/1040-SR/1040-NR** (total tax after nonrefundable credits) |
| 2 | Net Investment Income Tax — **Form 8960 line 17** |
| 3 | Federal Tax = L1 + L2 |
| 4a | Earned Income Credit — 1040 line 27a |
| 4b | Additional Child Tax Credit — 1040 line 28 |
| 4c | American Opportunity Credit — 1040 line 29 |
| 4d | Refundable Adoption Credit — 1040 line 30 |
| 4e | Form 2439 credits — Schedule 3 Part II line 13a |
| 5 | L4a + L4b + L4c + L4d + L4e |
| 6 | **L3 − L5 (if negative, 0) → Form 40 line 12** |

**So: FIT deduction = (1040 L22 + NIIT) − (EIC + ACTC + AOC + refundable adoption + 2439), floored
at 0.** SE tax + Additional Medicare tax are already inside 1040 L22 → **included**. NIIT explicitly
**added**. Refundable credits **subtracted**. OBBBA affects it only indirectly (via 1040 L22).
**Apportioned for part-year/nonresident + joint-federal/separate-AL:** federal tax × (AL AGI ÷
federal AGI) — §8.

---

## 4. TY2025 rate schedule (Ala. Code §40-18-5; verified vs the tax tables)

| Bracket | Single / MFS / HOF | MFJ |
|---|---|---|
| 2% | ≤ $500 | ≤ $1,000 |
| 4% | $500–$3,000 | $1,000–$6,000 |
| 5% | over $3,000 | over $6,000 |

No 2025 rate change (long-standing 2/4/5%). ⚠ §10 flag 2 — sourced from §40-18-5 (Justia) +
arithmetically confirmed against the DOR tax table, not a verbatim booklet bracket quote.

---

## 5. Deductions & exemptions (all AGI-keyed sliding scales — the AL complexity)

**Standard deduction (L11 if elected) — sliding by AL AGI (line 10), booklet p.8:**
| Status | Max (AGI floor) | Step | Min (at AGI) |
|---|---|---|---|
| MFJ | $8,500 (≤$25,999) | −$175 / $500 band | **$5,000** (≥$35,500) |
| MFS | $4,250 (≤$12,999) | −$88 / $250 band | $2,500 (≥$17,750) |
| HOF | $5,200 (≤$25,999) | −$135 / $500 band | $2,500 (≥$35,500) |
| Single | $3,000 (≤$25,999) | −$25 / $500 band | $2,500 (≥$35,500) |
⚠ §10 flag 1 — one OCR-suspect MFJ cell (should be $26,500–$26,999 → $8,150). Verify before lock.
Standalone chart: https://www.revenue.alabama.gov/forms/standard-deduction-chart-40-3/

**Personal exemption (L13)** — Single $1,500 / MFJ $3,000 / MFS $1,500 / HOF $3,000 (verbatim form
face). Full exemption even for part-year residents.

**Dependent exemption (L14) — sliding by AL AGI (line 10):** ≤$50,000 → **$1,000**/dep; $50,001–
$100,000 → **$500**/dep; over $100,000 → **$300**/dep. × number of dependents (Part III).

---

## 6. Income exclusions (NOT add-back/subtract lines — "You DO NOT Report")

Fully excluded from AL income: **defined-benefit (IRC §414(j)) pension distributions** (a major AL
feature — fully exempt); **Social Security**; US/AL government retirement (Teachers'/Employees'/
Judicial); **state income-tax refunds**; unemployment; VA/welfare/disability; combat pay; certain
military allowances; law-enforcement subsistence; up to **$50,000** severance/downsizing (TY2020+).
**NO general age-65 or "$6,000 retirement" exclusion** exists in AL (verified absent) — the
exclusion is specifically §414(j) defined-benefit + government pensions.

---

## 7. Credits — Schedule OC (all credits route through it) + Schedule ATP (additional taxes)

Schedule OC carries ~30 credits (Credit for Taxes Paid to Other States [Sch CR, resident-only, the
main one]; Rural Physician; Adoption; Historic Rehab; Investment/Jobs Act; Accountability Act;
Innovate Alabama; etc.) → line 18 net tax (nonrefundable) / line 25 (refundable, Sec F). Most need
MAT pre-reservation. Per-credit dollar caps live in each OC instruction (⚠ §10 flag 4, not
enumerated). Schedule ATP = consumer use tax + catastrophe-savings tax (L19) + penalties (L31).

---

## 8. Residency

- **Form 40** = full-year residents AND **part-year residents** (part-year report only income earned
  while an AL resident; get the FULL personal + dependent exemption). So Form 40 itself covers PY.
- **Form 40NR** (`25f40nrbk.pdf`) = nonresidents with AL-source income — a **separate form** (line
  map not transcribed — §10 flag 5). PY + NR-source situations file BOTH; exemptions only on the 40.
- **FIT deduction apportioned** for PY/NR + joint-fed/separate-AL: federal tax × (AL AGI ÷ federal
  AGI). Confirmed verbatim.

---

## 9. Federal handoff points

1. **Line 12** — federal income tax liability: 1040 **L22** + Form 8960 L17 (NIIT) − refundable
   credits (EIC 27a, ACTC 28, AOC 29, refundable adoption 30, 2439). Attach federal p.1/p.2/Sch 1.
2. Part I — Fed Sch C (business), Sch D (gains), Sch F (farm); Part II — Fed 3903 (moving).
3. **Wages come from AL Schedule W-2, NOT federal AGI.** AL imports no federal AGI/taxable-income start.

---

## 10. Confidence flags → requires_human_review WALK items (verify before locking)

1. **OCR-suspect MFJ std-ded cell** — extracted "$25,500–$26,999 → $8,150"; by the $500-band
   pattern should be **$26,500–$26,999 → $8,150**. Verify the single cell vs the PDF / the standalone
   chart before hardcoding the MFJ table.
2. **Rate schedule** — 2/4/5% thresholds sourced from §40-18-5 (Justia) + confirmed against the DOR
   tax table, not a verbatim booklet bracket quote. Statute unchanged; confidence high.
3. **"Paid or accrued" (§40-18-15) vs the worksheet** — the statute frames the deduction as federal
   tax "paid or accrued"; the Form 40 **mechanical figure is liability-based** (current-year 1040
   L22 worksheet), no cash/accrual election on the resident form. Cite §40-18-15 for the
   characterization, the worksheet for the computed number.
4. **Per-credit dollar caps** — not in the Form 40 booklet; each lives in its own Schedule OC
   instruction. Not verified (v1 likely direct-entry the OC net).
5. **Form 40NR line map** — not transcribed (only the FIT apportionment ratio confirmed). Needed only
   if 40NR is in v1 scope (decision A).

---

## 11. Proposed v1 scope (GA-500/SC1040 COMPUTES / DIRECT-ENTRY / RED-DEFER framework) — FOR KEN'S WALK

**COMPUTES (proposed):** the resident + part-year Form 40 (L5b→L35); AL gross income build (wages/
interest/other → L8; Part II adjustments → L10 AL AGI); **the federal income tax deduction worksheet
(L12)** + the PY apportionment ratio; the **sliding-scale standard deduction** (L11) + **sliding
dependent exemption** (L14) + personal exemption (L13); the 2/4/5% graduated tax (L16→L17); the
§414(j)/SS/government-pension income exclusions (at the income build); withholding/payments →
refund/due.

**DIRECT-ENTRY (line exists, diagnostic prompts):** Schedule OC credits (L18/L25 net — incl. Credit
for Taxes Paid to Other States); Part II niche adjustments not modeled; itemized deduction figure
(L11 Box a).

**RED-DEFER (each its own "prepare manually" RED):** Form 40NR (if not in v1 — decision A);
Schedule ATP additional taxes + penalties (L19/L31); NOL (Form NOL-85A, L17 alt).

**Open decisions for the walk:** (A) residency — Form 40 (full + part-year) only with 40NR
RED-deferred, or add Form 40NR; (B) the L12 FIT deduction — full worksheet + PY apportionment (the
quirk); (C) the sliding-scale std deduction + dependent exemption — compute the AGI-keyed tables;
(D) Schedule OC credits + Schedule ATP — direct-entry / RED-defer. Plus bless the §10 verify flags.
