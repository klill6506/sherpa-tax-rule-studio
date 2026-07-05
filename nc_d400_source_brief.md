# NC Form D-400 (North Carolina Individual Income Tax) — Source Brief (TY2025)

*Prepared 2026-07-04 to kick off the **NC D-400** authoring campaign (August RS state track, form 3 —
"NC D-400 next" after SC1040 ✅ + AL Form 40 ✅). TRANSCRIPTION AID / reconcile map — **NOT a spec and
NOT authorization to seed.** Per D-1, authored FRESH from NCDOR primary sources, reconciled against the
tts state compute, each mismatch a logged Ken adjudication. Constants VERIFIED against the FINAL 2025
NCDOR PDFs (research agent, 2026-07-04, all rev "Web-Fill 9-25" / "Form D-401 Web 2025"); §10 flags the
few that need a last look. This is the **4th state individual spec** (GA Form 500, SC1040, AL Form 40
precede it; `load_sc1040.py` + `load_al_form40.py` + `load_ga500_form_500.py` are the structural
precedents).*

---

## 1. Primary sources (all ncdor.gov, TY2025 FINAL)

- **Form D-400** (blank, pages 1-2) — "Web-Fill 9-25", Tax Year 2025 —
  https://www.ncdor.gov/2025-d-400-web-filled-version/open
- **D-400 Schedule S** (Additions & Deductions, pages 1-2) — "Web-Fill 9-25" —
  https://www.ncdor.gov/2025-d-400-schedule-s-web-fill-version/open
- **D-401 Individual Income Tax Instructions** (full 26-page booklet — covers D-400, Schedule S,
  Schedule A, Schedule PN, Schedule PN-1, D-400TC, Schedule AM) — "Form D-401 Web", 2025 —
  https://www.ncdor.gov/2025-d-401-individual-income-tax-instructions/open
- **NCDOR Tax Rate Schedules** page — https://www.ncdor.gov/taxes-forms/individual-income-tax/tax-rate-schedules
- **NCDOR Standard/Itemized Deductions** page — https://www.ncdor.gov/taxes-forms/individual-income-tax/filing-topics/north-carolina-standard-deduction-or-north-carolina-itemized-deductions
- Statutory backing (cited by the booklet, not independently fetched — §10 flag 4): N.C. Gen. Stat.
  **§105-153.7** (flat rate), **§105-153.5** (deductions/child deduction/std deduction),
  **§105-153.6** (bonus/§179 depreciation add-back & recovery), **§105-153.4** (NC taxable income).

---

## 2. Structure — how D-400 flows (verbatim; ✔ starts from FEDERAL AGI — contrast AL's from-scratch)

**KEY: NC starts from FEDERAL ADJUSTED GROSS INCOME (line 6), a FLAT 4.25% rate.** Conformity handled by
Schedule S: **additions** (Part A → line 7) and **deductions** (Part B → line 9). NC's IRC conformity is
frozen at **January 1, 2023** — OBBBA does NOT apply for TY2025 (booklet p.17).

```
PAGE 1
6  Federal AGI (the start)
7  Additions to fed AGI       (Schedule S Part A line 16)
8  = L6 + L7
9  Deductions from fed AGI     (Schedule S Part B line 41)
10 Child deduction            10a = # qualifying children   10b = deduction amount (AGI-banded table)
11 NC Standard OR NC Itemized deduction  (election; itemized from Schedule A line 10)
12 12a = L9 + L10b + L11       12b = L8 − L12a
13 Part-year/NR taxable %      (Schedule PN line 24, as a decimal; MAY exceed 100%, never < 0%)
14 NC Taxable Income           full-year: = L12b ; PY/NR: = L12b × L13
15 NC Income Tax               = L14 × 4.25% (0.0425); if zero or less, 0
PAGE 2
16 Tax credits                (D-400TC Part 3 line 20)
17 = L15 − L16
18 Consumer use tax           (or certify none)
19 = L17 + L18
20 NC tax withheld            20a you / 20b spouse
21 Other payments             21a est / 21b extension / 21c partnership / 21d S corp
22 Additional payments (amended only)   23 = Σ 20a..22
24 Previous refunds (amended only)      25 = L23 − L24
26 26a tax due · 26b penalties · 26c interest · 26d=26b+26c · 26e est-tax underpayment interest
27 Amount Due = 26a + 26d + 26e
28 Overpayment = L25 − L19    29 applied to 2026 est   30-32 contributions   33 = Σ29..32
34 Refund = L28 − L33
```

---

## 3. Flat rate (§105-153.7) — TY2025 = **4.25%** (0.0425)

Booklet p.7 verbatim: *"For tax year 2025, the individual income tax rate is 4.25%."* Form D-400 line 15
verbatim: *"Multiply Line 14 by 4.25% (0.0425)."* Rate schedule: 2024 = 4.50%; **2025 = 4.25%**; after
2025 = 3.99% (further trigger-based reductions possible TY2027+, S.L. 2023-134). ⚠ §10 flag 1 — the single
most year-sensitive constant; year-keyed, re-verify each season.

---

## 4. NC Standard Deduction (TY2025) — booklet p.14 (NO age-65/blind add-on; NOT federal amounts)

| Filing status | NC standard deduction |
|---|---|
| Single | **$12,750** |
| MFJ / Qualifying Widow(er) / Surviving Spouse | **$25,500** |
| MFS — spouse does NOT itemize | **$12,750** |
| MFS — spouse itemizes | **$0** |
| Head of Household | **$19,125** |

Verbatim: *"there is no additional NC standard deduction amount for taxpayers who are age 65 or older or
blind"*; *"If you are not eligible for the federal standard deduction, your NC standard deduction is
ZERO."* NC did NOT track the federal standard-deduction increase (set by the General Assembly).

---

## 5. THE DEPRECIATION ADD-BACK — Schedule S (the Ken-cares item; NC decouples from federal bonus/§179)

**Conformity date frozen at Jan 1, 2023; NC did NOT adopt IRC §168(k)/(n) bonus or the increased §179.**

**Part A Line 3 — Bonus depreciation add-back (booklet p.17, verbatim):**
> *"North Carolina did not adopt the bonus depreciation provisions in IRC sections 168(k) or 168(n)...
> You must add **85% of the amount of bonus depreciation deducted on your federal return** to your state
> return... you may deduct 20% of the amount added back in the first five taxable years beginning with
> tax year 2026."*

**Part A Line 4 — §179 add-back (booklet p.17, verbatim):**
> *"North Carolina did not conform to the increased federal expense deduction or increased investment
> limitations... **NC dollar and investment limitations are $25,000 and $200,000, respectively.** You must
> add **85% of the difference** between the IRC section 179 expense deduction using federal limitations
> and the deduction using NC limitations."*

**Part B Lines 23 & 24 — the 20% / 5-year recovery of PRIOR add-backs (booklet p.19):**
> Line 23 (bonus): *"deduct an amount equal to 20% of the bonus depreciation deduction added ... on your
> **2020, 2021, 2022, 2023, and 2024** state tax returns"* — sub-lines 23a=2020 … 23e=2024, total 23f.
> Line 24 (§179): same structure, 24a=2020 … 24e=2024, total 24f.

**Mechanics for the spec:**
- **85%** current-year add-back for BOTH bonus (Part A L3) and §179-excess (Part A L4). NOT 100%.
- **NC §179 limits = $25,000 / $200,000** (vs federal $2,500,000 / $4,000,000; OBBBA not adopted).
- The 5-year 20% recovery of a year-N add-back runs **years N+1 … N+5**. So on the **2025** return the
  recovery installments (L23a-e / L24a-e) are 20% of the **2020-2024** add-backs (2020's is its 5th/final
  installment). The **2025** add-back first recovers on the **2026** return. → Prior-year installments need
  historical records the spec cannot reach: **direct-entry**. Current-year add-back: **computable**.

---

## 6. Child deduction (§105-153.5(a1)) — booklet p.13, AGI-banded per-child × count (L10a → L10b)

Federal AGI (D-400 line 6) selects the band; per-child amount × number of qualifying children (federal
§24 children) = line 10b. Value exactly at a breakpoint falls in the LOWER (higher-deduction) band
("Up to $X" then "Over $X – up to $Y"). Max $3,000/child → $0.

| MFJ / QW / Surviving | HOH | Single / MFS | Per child |
|---|---|---|---|
| ≤ $40,000 | ≤ $30,000 | ≤ $20,000 | $3,000 |
| $40,001-$60,000 | $30,001-$45,000 | $20,001-$30,000 | $2,500 |
| $60,001-$80,000 | $45,001-$60,000 | $30,001-$40,000 | $2,000 |
| $80,001-$100,000 | $60,001-$75,000 | $40,001-$50,000 | $1,500 |
| $100,001-$120,000 | $75,001-$90,000 | $50,001-$60,000 | $1,000 |
| $120,001-$140,000 | $90,001-$105,000 | $60,001-$70,000 | $500 |
| > $140,000 | > $105,000 | > $70,000 | $0 |

---

## 7. Schedule S Part B — the meaningful NC deductions (subtractions from federal AGI)

- **L18 U.S. obligation interest** (Treasury / savings bonds).
- **L19 Social Security / Railroad Retirement** — fully deductible (NC does not tax).
- **L20 Bailey Settlement retirement** — vested NC state/local/federal (incl. military) retirees with
  **5+ yrs creditable service as of Aug 12, 1989** fully deduct. Excludes local §457 / §403(b).
- **L21 U.S. Uniformed Services military retirement** — 20+ yrs (or medical) may deduct retirement pay +
  SBP, if not already under L20. Excludes §61 severance.
- **L22-24 depreciation recovery** (bonus/§179 20% installments — §5), **L34-37** NOL / excess-business-loss
  / business-interest 20% recoveries, **L38 taxed PTE income**, **L39 NC NOL**.

**Part A additions** (besides L3/L4 depreciation): L1 non-NC muni interest, L2 opportunity-fund deferred
gain, L5 S-corp BIG tax, L7 federal NOL, L8 SALT deducted by a PTE, L13 discharged student loan, L14
taxed-PTE loss, etc.

---

## 8. NC Itemized Deductions (Schedule A) — booklet p.20 (restricted subset; election on L11)

Only five categories carry over: **(1) home mortgage interest** (§163(h)); **(2) real estate property
tax** (§164, capped $10,000 / $5,000 MFS); **combined mortgage+property-tax cap $20,000** per return;
**(6) charitable** (§170); **(7) medical & dental** (§213, less 7.5% × federal AGI); **(8) repayment of
claim of right**. Total → Schedule A line 10 → D-400 line 11. No other federal Schedule A items allowed.

---

## 9. Part-year / Nonresident (Schedule PN) — same D-400 + Schedule PN

PN allocates income Column A (all-source) vs Column B (NC-source / while-resident). **Line 24 = Col B ÷
Col A** (total income modified by NC adjustments), a **4-decimal** fraction → **D-400 line 13**. Then
**D-400 line 14 = line 12b × line 13** — proration applied AFTER std/itemized + child deduction.
*"The resulting percentage may be greater than 100%, but not less than 0%."* **Schedule PN-1** carries
Schedule-S additions/deductions lacking a dedicated PN line → PN L17e / L19h.

---

## 10. Confidence flags → requires_human_review WALK items (verify before locking)

1. **Flat rate 4.25%** — HIGH (form face + booklet verbatim), but the single most year-sensitive
   constant; year-keyed, re-verify each season (2026 → 3.99%).
2. **85% add-back fraction + $25k/$200k NC §179 limits** — HIGH (booklet p.17 verbatim), but the most
   legislation-sensitive numbers; year-keyed, re-verify each season.
3. **Conformity date = Jan 1, 2023 (OBBBA not adopted)** — load-bearing for the depreciation spec AND the
   std-deduction non-conformity. Booklet says "check the Department's website for any updates to federal
   conformity" — a mid-season conformity update could move items. Re-verify before season close.
4. **Statutory text not independently fetched** — relied on the D-401 booklet's citations to
   §105-153.5/.6/.7 rather than ncleg.gov verbatim. Numbers match the forms (what actually enforces);
   pull statute text as a 2nd pass only if verbatim statutory language is needed. LOW risk.
5. **Standalone Schedule A / PN / PN-1 / D-400TC form PDFs not separately opened** — all line structure
   came from the (line-accurate) booklet; no numeric constants at risk. Fetch the individual PDFs only if
   the exact box layout of Schedule PN's 15 income categories is needed.

---

## 11. Proposed v1 scope (GA-500/SC1040/AL-40 COMPUTES / DIRECT-ENTRY / RED-DEFER framework) — FOR KEN'S WALK

**COMPUTES (proposed):** the resident D-400 (L6→L34); the federal-AGI start + Schedule S Part A/B totals
→ AL AGI-equivalent (L8/L12b); the **child deduction AGI-banded table** (L10); the standard-deduction
election (L11) + NC itemized (Schedule A) computation; the **flat 4.25% tax** (L14→L15); withholding/
payments → refund/due. **Depreciation add-back (§5): COMPUTE the current-year 85% bonus + 85% §179-excess
add-back (Part A L3/L4)**; DIRECT-ENTRY the 20% prior-year recovery installments (L23a-e/L24a-e — need
historical records). **Schedule PN proration** (L13 → L14) if residency scope includes PY/NR.

**DIRECT-ENTRY (line exists, diagnostic prompts):** D-400TC credits (L16); consumer use tax (L18);
contributions (L30-32); the niche Schedule S add/deduct items not modeled (Part A L1/L2/L5/L7/L8/L13/L14;
Part B L25-37/L38/L39); itemized figure if not computed.

**RED-DEFER (each its own "prepare manually" RED):** Schedule PN-1 (other additions/deductions without a
PN line); amended-return lines (L22/L24, Schedule AM); estimated-tax underpayment interest (L26e, Form
D-422); NC NOL (L39).

**Open decisions for the walk (4, AskUserQuestion):**
- **(A) Residency** — resident + Schedule PN (PY/NR proration → L13/L14), or resident-only with PN
  RED-deferred? [SC1040 included Schedule NR; AL Form 40 included part-year natively.]
- **(B) Depreciation add-back** — COMPUTE the current-year 85% bonus + 85% §179-excess add-back (Ken's
  specialty; matches SC1040 D-6 computing §168(k)), direct-entry the 20% prior-year installments; OR full
  direct-entry (GA-500 W1 pattern)?
- **(C) Schedule S retirement deductions** — model L18 (US obligation) / L19 (SS/RR) / L20 (Bailey) / L21
  (military) as structured computed line items, OR collapse Schedule S Part B to a single direct-entry
  total?
- **(D) Credits & niche** — direct-entry D-400TC (L16) + consumer use tax (L18) + contributions; RED-defer
  Schedule PN-1 / amended lines / L26e underpayment / L39 NC NOL — confirm this split.

Plus bless the §10 verify flags (year-keyed rate + 85% add-back; conformity date Jan 1 2023).
