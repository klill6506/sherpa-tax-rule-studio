# Form 1120 C-Corporation Module (WO-11 / S-13) — Source Brief

*Greenfield RS-first authoring brief for the C-corporation module: Form 1120 (U.S. Corporation
Income Tax Return) + Georgia Form 600. Opened 2026-07-05 (DECISIONS D-12; Ken: "build 1120").
Front-door step: GAP-CHECKED → research-verified (this file) → Gate-1 scope walk → author.*

**Every fact below verified VERBATIM against FINAL 2025 sources by three parallel research passes
(federal face / IRC statute / GA 600), never memory, per the Authoritative-Source Rule.**

---

## Gap-check (live prod, 100 forms, 2026-07-05)

| Surface | Form key | Status |
|---|---|---|
| Spine — page 1 income/deductions → §11 21% tax | `1120` | **GAP** |
| Schedule C — dividends + §243/§245A DRD | (in spine or `1120_SCHC`) | **GAP** |
| Schedule J — tax computation + payments | (in spine or `1120_SCHJ`) | **GAP** |
| Schedule K — other information | (in spine or `1120_SCHK`) | **GAP** |
| Schedule L — balance sheet | `1120_SCHL` | **GAP** |
| Schedule M-1 / M-2 — book-tax recon / R/E | `1120_M1M2` | **GAP** |
| Georgia Form 600 — income + net worth tax | `GA600` | **GAP** |
| **COVERED — already carry `1120` in entity_types** | `1125A`, `1125E`, `3800`, `4562`, `4797`, `8949`, `7004` | ✅ no authoring |

`1125A` = `['1120S','1065','1120']` (COGS); `1125E` = `['1120S','1120']` (officer comp); `3800`/`4562`/
`4797`/`8949` = `['1120S','1065','1120','1040']`; `7004` = `['1120S','1065','1120']` (extension). Verified live.
Only the S-corp `GA600S` exists — the C-corp `GA600` is a genuine gap.

---

## Authoritative sources (all FINAL 2025)

| Source | Scope | Rev/date |
|---|---|---|
| **Form 1120 (2025)**, OMB 1545-0123 | Page 1 + Sch C/J/K/L/M-1/M-2 (6 pages) | **Created 9/26/25** |
| **i1120 (2025)** | Instructions for Form 1120 (34 pp) | 2025 |
| **IRC §11** | 21% flat corporate rate | Cornell LII |
| **IRC §243 / §245A / §246 / §246A** | DRD %; taxable-income limit; holding period; debt-financed | Cornell LII |
| **IRC §172** | NOL 80% limit / no carryback / indefinite carryforward | Cornell LII |
| **IRC §163(j)** | Business-interest limit; OBBBA EBITDA-basis restoration | Cornell LII + IRS/GT/RSM |
| **IRC §55 / §59** | CAMT 15% AFSI / $1B applicable-corp threshold | Cornell LII |
| **IRC §541/§542 · §531/§535 · §248** | PHC / AET / org-expense amortization | Cornell LII |
| **GA Form 600 (2025)**, O.C.G.A. Title 48 | Income tax + net worth tax + apportionment | **Rev. 07/31/25** |
| **GA IT-611 (2025)** + **GA Form 4562 (2025)** | 5.19% rate; net worth table; §168(k)/§179 non-conformity | IT-611 2025; 4562 Rev. 08/01/25 |

---

## FEDERAL — Form 1120 (2025) verbatim structure

### Page 1 — Income (L1–11)
1a Gross receipts · 1b Returns/allowances · 1c Balance · **2 COGS (Form 1125-A)** · 3 Gross profit ·
**4 Dividends and inclusions (Schedule C L23)** · 5 Interest · 6 Gross rents · 7 Gross royalties ·
**8 Capital gain net income (Sch D)** · **9 Net gain/(loss) Form 4797 Part II L17** · 10 Other income ·
**11 Total income (add L3–10)**.

### Page 1 — Deductions (L12–29)
**12 Compensation of officers (Form 1125-E)** · 13 Salaries/wages · 14 Repairs · 15 Bad debts · 16 Rents ·
17 Taxes/licenses · 18 Interest · 19 Charitable contributions · **20 Depreciation (Form 4562)** · 21 Depletion ·
22 Advertising · 23 Pension · 24 Employee benefit · **25 Energy-efficient commercial buildings (Form 7205)** ·
26 Other deductions · **27 Total deductions (L12–26)** · **28 Taxable income before NOL & special deductions
(L11−L27)** · **29a NOL deduction** · **29b Special deductions (Sch C L24)** · 29c add 29a+29b.

> ⚠ **Line 25 (Form 7205)** exists — no gap between L24 and L26. Structure/direct-entry.

### Page 1 — Tax & payments (L30–37)
**30 Taxable income (L28−L29c)** · **31 Total tax (Schedule J LINE 12)** · **32 §1062 first installment (Form 1062
L15)** [OBBBA-new] · **33 Total payments/credits/§1062 (Sch J L23)** · 34 Estimated tax penalty (Form 2220) ·
35 Amount owed · 36 Overpayment · 37 credited-to-2026 / refunded.

### Schedule C — Dividends, Inclusions, and Special Deductions (cols: (a) amount · (b) % · (c) = a×b)
| Line | Category | (b) % |
|---|---|---|
| 1 | <20%-owned domestic (non-debt-financed) | **50** |
| 2 | 20%+-owned domestic (non-debt-financed) | **65** |
| 3 | Certain debt-financed stock (domestic + foreign) | see instr (§246A) |
| 4 | Preferred of <20%-owned public utilities | **23.3** |
| 5 | Preferred of 20%+-owned public utilities | **26.7** |
| 6 | <20%-owned foreign + certain FSCs | **50** |
| 7 | 20%+-owned foreign + certain FSCs | **65** |
| 8 | Wholly owned foreign subsidiaries | **100** |
| 9 | Subtotal (L1–8, subject to §246(b) limit) | — |
| 10 | SBIC domestic dividends | **100** |
| 11 | Affiliated-group members | **100** |
| 12 | Certain FSCs | **100** |
| 13 | §245A foreign-source portion (specified 10%-owned FC) | **100** |
| 14 | Other foreign (not 3/6/7/8/11/12/13, incl. hybrid) | — |
| 16a–c / 17 | Subpart F / GILTI (still labeled "GILTI" on the 2025 form despite OBBBA NCTI rename) | — |
| 18 | Foreign-tax gross-up | — |
| 19–20 | IC-DISC / other dividends | — |
| 21 | Public-utility preferred deduction (col c) | — |
| 22 | **§250 deduction (Form 8993)** (col c) | — |
| **23** | **Total dividends → page 1 L4** (col a, L9–20) | — |
| **24** | **Total special deductions → page 1 L29b** (col c, L9–22) | — |

### Schedule J — Tax Computation and Payment (⚠ single continuous list to L23; NO Part I/II; OBBBA-restructured)
**Tax:** 1a Income tax (= **taxable income × 21%**) · 1b Form 1120-L · 1c §1291 (8621) · 1d §8978 adj · 1e §197(f) ·
**1f base-erosion min tax (Form 8991)** · 1g Form 4255 · 1z other → **2 Total income tax (1a–1z)** ·
**3 CAMT (Form 4626 Part II L13)** · 4 add 2+3 · **5a FTC (1118) · 5b 8834 · 5c GBC (Form 3800) · 5d prior-yr min
tax (8827) · 5e bond (8912) · 5f 8978 adj** · 6 total credits · 7 = L4−L6 · **8 PHC tax (Schedule PH)** ·
9a–9z recapture (LIHC 8611, look-back 8697/8866, §453A(c), §453(l), …) · 10 total · **11a total tax before deferred
(7+8+10) · 11b deferred QEF · 11c deferred LIFO recapture (§1363(d))** · **12 Total tax → page 1 L31**.
**Payments (13–23):** 13 PY overpayment · 14 estimates · 15 Form 4466 · 17 Form 7004 deposit · 18 withholding ·
19 total (13–18) · 20a 2439 / 20b 4136 / 20c ch.3-4 wh / 20z · 21 total · 22a elective payment (Form 3800) /
**22b §1062 (Form 1062 L14)** · **23 Total payments → page 1 L33**.

### Schedule K — Other Information (Q1–Q32, verbatim highlights)
1 accounting method · 2 activity code/product · 3 controlled-group parent · 4a/b ownership by entity/individual (→ Sch G) ·
5a/b corp owns ≥20/50% of another · 6 nondividend distributions >E&P (Form 5452) · 7 ≥25% foreign owner (Form 5472) ·
9 tax-exempt interest amount · 10 shareholders (if ≤100) · **11 NOL forego-carryback election** ·
**12 available NOL carryover from prior years (do NOT reduce by L29a)** · **13 total receipts & assets < $250,000?
(if Yes, skip Sch L/M-1/M-2)** · 14 Schedule UTP · 16 80%+ ownership change · 18 §351 transfer >$1M · **21 §267A
disallowed interest/royalty** · **22 gross receipts ≥$500M in a prior 3 yrs → §59A base erosion (Form 8991)** ·
**23 §163(j) real-property/farming election in effect?** · **24 §163(j)/Form 8990 trigger: (a) pass-through EBIE;
(b) avg gross receipts >$31M (§448(c)) w/ business interest; (c) tax shelter** · 27 digital asset · 28 controlled
group (Sch O) · **29 CAMT: (a) applicable corp §59(k)(1) prior year; (b) applicable current year; (c) §59(k)(3)(A)
safe harbor → Form 4626** · 30 Form 7208 stock-repurchase excise · 31 consolidated ≥$1B + §754-type basis adj ≥$10M.

### Schedule L — Balance Sheets per Books
Assets **L1–15 (L15 = Total assets)**; Liabilities & shareholders' equity **L16–28 (L28 = Total)**. BOY/EOY cols (a)–(d).
Retained earnings — unappropriated = L25 (ties to M-2).

### Schedule M-1 — Reconciliation of Income per Books with Income per Return (L1–10)
1 net income per books · 2 federal income tax per books · 3 excess capital losses · 4 income taxed not on books ·
5 book expenses not deducted (a depreciation / b charitable / c T&E) · **6 add 1–5** · 7 book income not on return
(tax-exempt interest) · 8 return deductions not on books (a depreciation / b charitable) · 9 add 7+8 ·
**10 income (page 1 L28) = L6 − L9**.

### Schedule M-2 — Analysis of Unappropriated Retained Earnings (= Sch L L25) (L1–8)
1 beginning balance · 2 net income per books · 3 other increases · **4 add 1+2+3** · 5 distributions (a cash / b stock /
c property) · 6 other decreases · 7 add 5+6 · **8 ending balance = L4 − L7**.

---

## FEDERAL — IRC statutory rules (verbatim, TY2025)

- **§11(b): "21 percent of taxable income."** Flat; no brackets. (i1120: "Multiply page 1 line 30 by 21% (0.21)"
  → Sch J L1a.) [The literal "section 11" string was not found in the extracted i1120 text — the 21% *mechanic*
  is verified; cite §11 for the statute.]
- **§243 DRD:** 50% general (§243(a)(1)); **65%** for 20%+-owned (§243(c), by vote AND value); **100%** for
  affiliated-group qualifying dividends (§243(a)(3)/(b), §1504(a)).
- **§246(b) taxable-income limitation:** total DRD ≤ 65% (20%+-owned) / 50% (other) of taxable income computed
  WITHOUT §172/§199A/§243(a)(1)/§250. **Loss exception:** the limit does NOT apply in a year with an NOL (§172).
- **§246(c) holding period:** stock held >45 days in the 91-day window (>90/181 for preference dividends).
- **§246A:** debt-financed portfolio stock reduces the DRD by (50%/65%) × (average indebtedness %).
- **§245A:** 100% deduction of the foreign-source portion of a dividend from a "specified 10%-owned foreign
  corporation." ⚠ **Holding period is §246(c)(5)** (>365 days in a 731-day window), NOT §245A(c) (which defines
  "foreign-source portion").
- **§172 NOL:** post-2017 NOLs limited to **80%** of taxable income (before §172/§199A/§250); **no carryback,
  indefinite carryforward** (§172(b)(1)(A), TCJA §13302). OBBBA did not change corporate NOL mechanics.
- **§163(j):** deduction ≤ business interest income + **30% of ATI** + floor-plan financing. ⚠ **OBBBA restored
  the EBITDA basis** (add back depreciation/amortization/depletion to ATI) **permanently, effective for tax years
  beginning after 12/31/2024 — i.e., TY2025.** A stale 2022–2024 EBIT-basis assumption is a TY2025 ERROR.
  Small-business exemption **$31,000,000** avg gross receipts (§448(c), 2025-indexed; was $30M in 2024);
  tax shelters excluded. Filing vehicle = **Form 8990** (a separate form — defer the compute there, gate on Sch K Q24).
- **§55/§59 CAMT:** 15% of adjusted financial statement income (AFSI) for "applicable corporations" — average
  annual AFSI over the 3-year period > **$1,000,000,000** (§59(k)); effective tax years beginning after 12/31/2022;
  **Form 4626** (Sch J L3, Sch K Q29). RED-defer.
- **§541/§542 PHC:** 20% of undistributed PHC income; income test (≥60% of AGI is PHC income) + ownership test
  (>50% by value held by ≤5 individuals in the last half-year); **Schedule PH** (Sch J L8). RED-defer.
- **§531/§535 AET:** 20% of accumulated taxable income; §535 credit **$250,000** general / **$150,000** personal-
  service corp. IRS-assessed (no return line). RED-defer.
- **§248 org expenses:** immediate deduction = lesser of amount or **$5,000, reduced $-for-$ above $50,000**;
  remainder over **180 months**. (Page-1 "Other deductions" line 26.)
- **§1062 (OBBBA-new):** deferral of tax on sale of qualified farmland to qualified farmers; **Form 1062**
  (page-1 L32/L33, Sch J L22b). Structure + flag / RED-defer (mirrors the 1041 §1062 treatment).

---

## GEORGIA — Form 600 (2025) verbatim

- **Corporate income tax rate TY2025 = 5.19%** (Sch 1 L10 = "Line 9 × 5.19%"). Enacted by **HB 111 (2025)**
  (not HB 1015); rate not prorated; fiscal filers use the start-of-period rate. GA ties the corp rate to the
  individual rate.
- **Schedule 1 flow:** L1 federal taxable income → L2 additions (Sch 4) → L3 → L4 subtractions (Sch 5) → L5 →
  **L6 GA NOL deduction (Sch 9; 80% limitation)** → L7 GA taxable income → L8 passive/capital-loss ded → L9 →
  **L10 income tax = L9 × 5.19%**.
- **Depreciation non-conformity (Ken's specialty — precise):** GA does NOT conform to §168(k). Mechanic:
  (1) federal depreciation WITH bonus on federal 4562; (2) recompute for GA WITHOUT §168(k) and using GA's §179
  limit on **GA Form 4562**; (3) federal bonus/excess = **addition on Schedule 4 Line 8 (Other Additions)**;
  recomputed GA depreciation (and future-year catch-up) = **subtraction on Schedule 5 Line 4 (Other Subtractions)**.
  Later years reverse to a net subtraction as GA basis depreciates.
- **⚠ GA §179 for 2025 = $1,250,000 limit / $3,130,000 phase-out** (2025 GA Form 4562 Rev. 08/01/25, VERBATIM:
  "$1,220,000 for 2024 and $1,250,000 for 2025 … phase out … $3,050,000 for 2024 and $3,130,000 for 2025").
  **GA INDEXES its §179.** The `$1,050,000 / $2,620,000` figure in CLAUDE.md / prior GA notes is the **2021**
  amount — STALE for 2025. Federal (OBBBA) 2025 = $2.5M/$4M; GA decoupled and much lower. **FLAG for Ken +
  check the existing GA700/GA600S specs for the same staleness.**
- **Net worth tax — Schedule 2** (computation) + bracket table (IT-611 p.19): L1 capital stock + L2 paid-in/surplus +
  L3 retained earnings = **L4 net worth**; L5 ratio (GA/dom = 100%; foreign = Sch 8); L6 net worth taxable by GA;
  **L7 net worth tax from table**. **Exempt ≤$100,000 = $0; maximum $5,000 over $22,000,000** (19 brackets;
  e.g. $100k–150k = $125; $1M–2M = $750; $10M–12M = $2,000; $20M–22M = $4,500). O.C.G.A. §48-13-70 et seq.
- **Schedule 3 — Tax Due/Overpayment:** three columns **A income tax · B net worth tax · C total**. Total tax =
  Sch 1 L10 + Sch 2 L7. **Schedule 10 credits apply against INCOME tax only, not net worth tax.**
- **Apportionment — Schedule 6 SINGLE-FACTOR GROSS RECEIPTS** (100% sales factor), **compute to SIX decimals**
  (O.C.G.A. §48-7-31).
- **Conformity: IRC as in effect January 1, 2025** (HB 290; O.C.G.A. §48-1-2(14)). **OBBBA NOT adopted** (enacted
  July 4 2025, after the conformity date); GA §168(k) decoupling stands regardless.
- **Due: 15th day of 4th month** (calendar year = April 15, 2026); GA extension needs the federal ext copy or IT-303.

---

## Carried [UNVERIFIED] / flags (re-verify before any deeper compute leg)
- **[TY2026 §163(j)]** electively-capitalized interest retains character (OBBBA, years after 12/31/2025) — do NOT
  encode for TY2025; note only.
- **[conformity date source]** GA HB 290 Jan 1 2025 corroborated by three professional sources (Deloitte/KPMG/RSM) +
  legislative record; primary bill PDF was paywalled. Re-confirm on the next GA conformity bill.
- **[§11 label]** the 21% mechanic is verbatim from i1120 Sch J L1a; the literal "section 11" citation was not in
  the extracted text — statute cite is by §11 itself.
- Re-verify all constants at TY2026 (rates, §448(c) $31M, GA §179 index, GA rate track, net worth table).

---

## Proposed authoring legs (subject to Gate-1 scope walk)
1. **`1120` federal spine** — page 1 income/deductions + Schedule C (DRD) + Schedule J (tax comp) → total tax.
2. **`1120_SCHL` / recon** — Schedule L balance sheet + M-1 + M-2 (+ Schedule K other-info gates).
3. **`GA600`** — Georgia income tax (5.19% + single-factor apportionment + §168(k)/§179 delta) + net worth tax table.
Each: author `READY_TO_SEED=False` → SQLite-validate (CharField caps rule/diag/assertion/line ≤ 20) → Ken review
walk → seed → export = 200.
