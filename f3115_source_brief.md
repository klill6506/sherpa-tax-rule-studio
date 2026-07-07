# Source Brief — IRS Form 3115 (Application for Change in Accounting Method), TY2025

**WO-23 · SPINE S-16, 10th (the LAST S-16 item) · Ken's specialty (§481(a) depreciation catch-up)**
**Prepared 2026-07-06 · verbatim-verified against fetched primary sources (never training memory).**

Every load-bearing item is marked **[VERIFIED]** (read directly off a fetched primary-source PDF/statute)
or **[UNVERIFIED]** (could not read off a primary source — flagged, not guessed).

---

## A. Provenance

| Item | Value | Status |
|---|---|---|
| **Form 3115 revision** | **Rev. December 2022** (footer "Form 3115 (Rev. 12-2022)", Cat. No. 19280E) | **[VERIFIED]** f3115.pdf p.1 |
| **Instructions revision** | **Rev. December 2022** (i3115), Cat. No. 63215H | **[VERIFIED]** i3115.pdf p.1 |
| **Master procedural Rev. Proc.** | **Rev. Proc. 2015-13, 2015-5 I.R.B. 419** (automatic + non-automatic), as clar./mod. by 2015-33, 2021-34, 2021-26, 2017-59 | **[VERIFIED]** i3115 header |
| **Current List of Automatic Changes (TY2025)** | **Rev. Proc. 2025-23, 2025-24 I.R.B.** — supersedes-in-part Rev. Proc. 2024-23. Effective for Forms 3115 filed on/after **June 9, 2025**, year of change ending on/after Oct 31, 2024 | **[VERIFIED]** rp-25-23.pdf; the i3115 (12-2022) names "2022-14 or any successor" — 2025-23 is that successor |
| **OBBBA (P.L. 119-21) impact** | **NONE to the 3115 procedural machinery or §481(a).** OBBBA changed substantive depreciation *amounts* (100% bonus permanent post-1/19/2025; new §168(n) QPP; §179 $2.5M/$4M) — NOT §446, §481, Rev. Proc. 2015-13's spread/de minimis, or the form layout. Flag: an impermissible bonus/MACRS method is still corrected via DCN 7 + §481(a); OBBBA changes the *correct number*, not the mechanism | **[VERIFIED]** (absent from all sources read) |

**Re-verify each season:** the Form 3115 REVISION (revised irregularly, not annually) + the current
automatic-change Rev. Proc. (the DCN list updates ~annually; 2024-23 → 2025-23 chain).

---

## B. Form structure (Rev. 12-2022)

**Page 1 header** — "type of accounting method change" boxes (**Depreciation or Amortization** / Financial
Products / Other) + applicant-type boxes (Individual, Corporation, Partnership, S corporation, CFC…). **[VERIFIED]**

### Part I — Information for Automatic Change Request
- **Line 1** — "Enter the applicable **designated automatic accounting method change number ('DCN')**… **Enter only one DCN**, except as provided… If the requested change has no DCN, check 'Other'." (slots 1a(1)–(12) + 1b Other). **[VERIFIED]**
- **Line 2** — do the eligibility rules restrict automatic filing? If Yes, attach explanation. **[VERIFIED]**
- **Line 3** — all required info/statements provided per the List of Automatic Changes. **[VERIFIED]**

### Part II — Information for All Requests
- **Line 6a** — federal return(s) under examination (6b–6d exam details). **[VERIFIED]**
- **Line 7a/7b** — audit protection + category boxes (not under exam / method not before director / 3-month window / negative adjustment / 120-day / CAP / other). **[VERIFIED]**
- **Line 11a** — **the 5-year rule:** requested or made this change within any of the **5 tax years ending with the year of change**? **[VERIFIED]**
- **Line 13** — changing OVERALL method? If Yes → Schedule A. **[VERIFIED]**
- **Line 14** — present/proposed method description (14b present, 14c proposed, 14d present overall). **[VERIFIED]**
- **Line 19a** — 3-yr gross receipts (for §263A/§460/§471/cash↔accrual). **[VERIFIED]**

### Part III — Information for Non-Automatic Change Request
- Line 20 (described as automatic elsewhere) · 21 (docs) · 22 (reasons) · 23 (consolidated members) · **Line 24a user fee** (per Rev. Proc. 2023-1 App. A, PAY.gov; **no user fee for automatic changes**). **[VERIFIED]**

### Part IV — Section 481(a) Adjustment
- **Line 25** — **cut-off basis?** If Yes, attach explanation and **do NOT complete lines 26–29** (cut-off = no §481(a) adjustment). **[VERIFIED]**
- **Line 26** — **"Enter the section 481(a) adjustment. Indicate whether the adjustment is an increase (+) or a decrease (−) in income."** **[VERIFIED]**
- **Line 27** — remaining portion of a §481(a) adjustment from a PRIOR change. **[VERIFIED]**
- **Line 28** — **election to take the ENTIRE amount in the year of change?** boxes: **$50,000 de minimis election** / **eligible acquisition transaction election**. **[VERIFIED]**
- **Line 29** — related-party portion. **[VERIFIED]**
- *No explicit "years of spread" input field* — the 1-vs-4-year spread is a RULE applied to the signed Line-26 amount, controlled by sign + the Line-28 election. **[VERIFIED by absence]**

### Schedule A — Change in Overall Method (cash↔accrual)
Part I Line 1 present/proposed (Cash/Accrual/Hybrid). **Line 2 worksheet** (as of close of preceding year):
`2a` AR (income accrued not received) · `2b` advance payments (received before earned) · `2c` AP (expenses
accrued not paid) · `2d` prepaid expenses previously deducted · `2e` supplies on hand previously deducted ·
`2f` inventory previously deducted/not reported (→ Sch D Part II) · `2g` other · **`2h` = net §481(a) =
combine 2a–2g (+/−); also enter on Part IV Line 26.** **[VERIFIED]**

### Schedule E — Change in Depreciation or Amortization (Ken's path)
Per item/class of property. **[all VERIFIED off f3115.pdf p.8]**
- **L1** CLADR (Reg. 1.167(a)-11)? · **L2** depreciation required to be capitalized (§263A)? · **L3** election made (§168(f)(1), §168(i)(4), **§179**, §179C, Reg. 1.168(i)-8(d))?
- **L4a** attach statement: property **description, type, placed-in-service year, use** + credits/basis adj. · 4b residential rental · 4c public-utility.
- **L5** present-method treatment (depreciable/inventory/supplies/§263(a)/expensed). · **L6** if not now depreciable, facts for the proposed change.
- **L7 (present AND proposed):** `7a` Code section (e.g. §168(g)) · `7b` asset class from **Rev. Proc. 87-56** (MACRS) · `7c` facts supporting the class · `7d` **method** incl. Code section (e.g. "200% DB under §168(b)(1)") · `7e` **useful life / recovery period / amortization period** · `7f` **convention** · `7g` **bonus (§168(k)/(l)/(m)) claimed?** · `7h` single / multiple / general asset account.

### Schedules B / C / D — structure only (direct-entry)
B = §451 advance payments / AFS income-inclusion; C = LIFO; D = long-term contracts §460 / inventory valuation / §263A. **[VERIFIED they exist]**

---

## C. Compute heart — §481(a) mechanics (cited)

- **§481(a) (statute):** adjustments "necessary solely by reason of the change **in order to prevent amounts from being duplicated or omitted**" — the cumulative old-vs-new difference as of the **beginning of the year of change**. **[VERIFIED law.cornell.edu/uscode/text/26/481]**
- **§446(e) (consent):** must "secure the consent of the Secretary" before computing under the new method — Form 3115 is that consent. **[VERIFIED /26/446]**
- **Spread (Rev. Proc. 2015-13 §7.03(1), verbatim):** "the §481(a) adjustment period is **one taxable year (year of change) for a negative** §481(a) adjustment and **four taxable years (year of change and next three) for a positive** §481(a) adjustment… a taxpayer must take a positive §481(a) adjustment into account **ratably**." **[VERIFIED rp-15-13.pdf]**
  - Under-exam override: positive period = **2 years** unless a Line-7b category applies. **[VERIFIED i3115]**
- **De minimis (§7.03(3)(c), verbatim):** "elect a one-year §481(a) adjustment period… for a **positive §481(a) adjustment that is less than $50,000**." (Line 28 box.) **[VERIFIED]**
- **Eligible acquisition transaction (§7.03(3)(d)):** one-year for all positive adjustments if such a transaction occurs in the year of change. **[VERIFIED]**
- **Depreciation catch-up (Rev. Proc. 2025-23 §6.01(5)):** "may result in either a **negative** (decrease in taxable income) **or a positive** (increase)… **equals the difference between the total amount of depreciation taken into account… under the present method** [and the amount allowable under the proposed method] as of the beginning of the year of change." Scope §6.01(1): impermissible method used in **≥ 2 preceding years**; property owned at BOY of change. **DCN = "7"** (§6.01(9)). **[VERIFIED rp-25-23.pdf]**

### Sign convention (load-bearing)
`§481(a) = (depreciation TAKEN under present method) − (depreciation ALLOWABLE under proposed method)` as of
BOY of change. **Under-depreciated** (taken < allowable) → **negative** → decreases income → **1 year**.
**Over-depreciated** (taken > allowable) → **positive** → increases income → **4 years** (or 1 if < $50k + de minimis election; or 2 if under exam).

### Worked example (validation oracle)
$100,000 asset, in service Jan 2022, wrongly 39-yr SL instead of 5-yr MACRS; change year 2025 (impermissible
2022–2024 = ≥2 yrs → DCN 7). Taken (39-yr, 3 yrs) ≈ $7,692; allowable (5-yr MACRS 20/32/19.2%) = $71,200 →
**§481(a) = 7,692 − 71,200 = −$63,508 (negative) → 1 year.** *(MACRS percents from Pub. 946 — **[UNVERIFIED]**
numeric detail; sign/structure/1-year-negative treatment **[VERIFIED]**. Build the real oracle with clean
round numbers so no MACRS-table dependency.)*

### Scope/eligibility diagnostics
Under-exam (L6a) · 5-year rule (L11a) · cut-off vs §481(a) (L25, mutually exclusive with 26–29) · ≥2-year-use for DCN 7. **[all VERIFIED]**

---

## D. Recommended v1 scope (Gate-1 decision points)

**entity_types = ['1040','1065','1120','1120S']** (any taxpayer can file). **[VERIFIED — applicant boxes p.1]**

- **Q1 — §481(a) spread engine → COMPUTE (recommend yes).** Signed Line-26 amount → negative = full year-of-change (1 yr); positive = ratable over 4 yrs (25%/yr); positive < $50k → de minimis 1-year election (Line 28); under-exam positive = 2 yrs. Fully sourced (§7.03).
- **Q2 — Schedule E depreciation catch-up + DCN 7 routing → COMPUTE the catch-up + DCN; direct-entry the 7a–7h method descriptors (recommend yes).** Catch-up = (allowable proposed) − (taken present) as of BOY; classify impermissible→permissible depreciation → DCN 7. Ken's specialty, highest-value compute.
- **Q3 — Schedule A cash↔accrual §481(a) worksheet (2a–2h) → COMPUTE the netting (recommend yes).** Deterministic sum → net §481(a) → Line 26.
- **Q4 — Scope-limitation diagnostics → DIAGNOSTIC-only (recommend yes).** Under-exam, 5-year rule, cut-off vs §481(a), ≥2-year-use. Gate eligibility; produce no number.

---

## E. Ready-to-cite excerpts (AuthorityExcerpt seeds)
Six verbatim blocks captured (see agent research): (1) Form 3115 Part I L1 + Part IV L25/26/28 face;
(2) Schedule E L4a & L7 depreciation grid; (3) Rev. Proc. 2015-13 §7.03(1) spread; (4) §7.03(3)(c) $50k de
minimis; (5) Rev. Proc. 2025-23 §6.01(5)/(9) DCN-7 depreciation catch-up formula; (6) IRC §481(a) statute.

## Authority sources to seed
- `IRS_F3115` — Form 3115 (Rev. 12-2022) — federal_form, primary_official
- `I3115` — Instructions for Form 3115 (Rev. 12-2022) — official_instructions, primary_official
- `REVPROC_2015_13` — master procedural (spread + de minimis) — official_guidance, controlling
- `REVPROC_2025_23` — current List of Automatic Changes (DCN 7) — official_guidance, primary_official
- `IRC_481` — §481(a) + §446(e) statute — statute, controlling
