# Source Brief — Form 709, US Gift (and GST) Tax Return (TY2025)

**WO-21 · SPINE S-16 (8th item; the biggest module) · greenfield RS-first**
Research pass 2026-07-06, verbatim vs 2025 i709 + §2001(c). **★ Load-bearing correction: 2025 applicable credit =
$5,541,800** (the brief's $5,389,800 was the 2024 figure). ⚠ Raw f709.pdf face didn't fetch — dollar figures + compute
logic VERIFIED (from i709 + statute); some structural line numbers [UNVERIFIED] (re-verify the PDF face before the tts build).

---

## Sources

| source_code | title | citation |
|---|---|---|
| `IRS_2025_F709` | 2025 Form 709 — US Gift (and GST) Tax Return | Form 709 (2025) — ⚠ exact "Created" date [UNVERIFIED] (PDF face unfetchable); 2025 revision confirmed |
| `IRS_2025_I709` | 2025 Instructions for Form 709 | Instructions for Form 709 (2025), incl. "What's New" + Table for Computing Gift Tax |
| `IRC_2001_2010` | IRC §2001(c) rate schedule; §2010/§2505 unified credit; §2503(b) annual exclusion; §2523(i); §2631 GST; OBBBA §70106 | 26 U.S.C. §2001, §2010, §2503, §2523, §2631; P.L. 119-21 §70106 |

---

## What this is

Form 709 reports (1) taxable **gifts** (gift tax) and (2) inter-vivos **generation-skipping transfers** (GST tax); the
donor files. The gift tax is **unified + cumulative**: tentative tax on ALL lifetime taxable gifts (current + prior),
minus tentative tax on prior gifts, so current gifts are taxed at the top cumulative brackets (40% reached fast); the
**applicable (unified) credit** shelters tax until cumulative taxable gifts exceed the basic exclusion amount (BEA).

---

## ★ Verified 2025 figures (INDEXED — re-verify each season)

| item | 2024 | **2025 (verified)** |
|---|---|---|
| Annual exclusion / donee (§2503(b)) | $18,000 | **$19,000** |
| Basic exclusion amount (BEA) / applicable exclusion (§2010) | $13,610,000 | **$13,990,000** |
| **Applicable (unified) credit** = tentative tax on the BEA | $5,389,800 | **$5,541,800** ✓ ($345,800 + 40%×($13,990,000−$1,000,000)) |
| Annual exclusion — noncitizen spouse (§2523(i)) | $185,000 | **$190,000** |
| GST exemption (§2631) = BEA | $13,610,000 | **$13,990,000** |
| Top gift/GST rate (§2001(c)) | 40% | **40%** |

**★ OBBBA (P.L. 119-21 §70106): does NOT change TY2025.** The 2025 BEA/GST exemption stay **$13,990,000**. OBBBA
**permanently** sets the BEA to **$15,000,000** for gifts made **after 12/31/2025 (2026+)**, indexed thereafter, no
sunset. **Year-key the constants so $15M does not leak into 2025.** (The exact indexed 2026 figure ≥ $15M is not yet
IRS-published — treat $15M as the 2026 statutory floor.)

---

## The §2001(c) rate schedule (statutory, stable — "Table for Computing Gift Tax")

| over | not over | tax on col A | rate on excess |
|---|---|---|---|
| $0 | $10,000 | $0 | 18% |
| $10,000 | $20,000 | $1,800 | 20% |
| $20,000 | $40,000 | $3,800 | 22% |
| $40,000 | $60,000 | $8,200 | 24% |
| $60,000 | $80,000 | $13,000 | 26% |
| $80,000 | $100,000 | $18,200 | 28% |
| $100,000 | $150,000 | $23,800 | 30% |
| $150,000 | $250,000 | $38,800 | 32% |
| $250,000 | $500,000 | $70,800 | 34% |
| $500,000 | $750,000 | $155,800 | 37% |
| $750,000 | $1,000,000 | $248,300 | 39% |
| **$1,000,000** | — | **$345,800** | **40%** |

(§2001(c) statutory text lists intermediate >40% brackets over $1M, but EGTRRA capped the top at 40% — the Form 709
table collapses everything over $1,000,000 to **$345,800 + 40%**. Use the flat 40% top row.)

---

## Structure (schedules + the verified Part 2 compute lines)

⚠ **The 2025 form was RESTRUCTURED** (i709 "What's New": Part I reorganized + foreign-address entries; former lines
12-18 moved to a new **Part III**). Part-1 / Schedule-A-reconciliation / Schedule-D sub-line numbers are **[UNVERIFIED]**
(inferred from instruction text — re-verify the raw PDF face). **Part 2 lines 1-8 ARE verified from the instructions.**

- **Part 1 — General Information** — donor info; **gift-splitting consent (§2513)** + spouse signature; elections.
- **Schedule A — Computation of Taxable Gifts** — Part 1 (gifts subject only to gift tax) / Part 2 (direct skips: gift
  + GST) / Part 3 (indirect skips §2632(c)). Reconciliation: total gifts − **annual exclusions ($19,000/donee)** −
  **marital deduction (§2523)** − **charitable deduction (§2522)** = **taxable gifts** → Part 2 line 1.
- **Part 2 — Tax Computation (VERIFIED lines 1-8):** L1 taxable gifts this period (Sch A) · L2 prior-period taxable
  gifts (Sch B) · **L3 = L1 + L2** · **L4 = tentative tax on L3** (rate schedule) · **L5 = tentative tax on L2** ·
  **L6 = L4 − L5** (tax on current gifts) · **L7 = applicable credit ($5,541,800; + DSUE from Sch C line 5)** · **L8 =
  credit allowable for prior periods (Sch B)**; then credit limitation → gift tax → + GST (Sch D) → balance due.
- **Schedule B — Gifts From Prior Periods** — the cumulative base (prior taxable gifts + prior credit used, col (c) → L8).
- **Schedule C — DSUE / Restored Exclusion** — DSUE from predeceased spouse(s) → Sch C line 5 → Part 2 line 7.
- **Schedule D — GST Tax** — allocate the GST exemption ($13,990,000); **GST tax = 40% × inclusion ratio**, inclusion
  ratio = 1 − (exemption allocated ÷ transfer).

---

## Compute mechanics (for rules/diagnostics)

- **The cumulative engine:** `gift_tax = [tentative(current+prior) − tentative(prior)] − applicable_credit(limited)`.
  2025 credit $5,541,800 shelters tax until cumulative taxable gifts > $13,990,000.
- **Annual exclusion** $19,000/donee (present interests only; future interests reported regardless of amount).
- **Gift-splitting (§2513):** spouses consent → each treats gifts as one-half made → doubles the per-donee exclusion to
  $38,000; both spouses sign.
- **Marital deduction (§2523):** unlimited to a U.S.-citizen spouse; a noncitizen spouse gets the **$190,000** annual
  exclusion instead. **Charitable (§2522):** unlimited to qualified charities.
- **Who must file:** gifts > $19,000/donee; any future-interest gift; gift-splitting spouses; certain transfers — even
  if the credit zeroes the tax. **Due April 15, 2026** (Form 8892 extends filing, NOT payment).
- **GST:** 40% × inclusion ratio; exemption = BEA ($13,990,000).

---

## Proposed scope for the Gate-1 walk (compute vs defer)

1. **Core cumulative gift-tax engine (Part 2)** — compute the §2001(c) tentative-tax function + the L3-L8 cumulative
   computation + the applicable credit ($5,541,800) → gift tax due. The verified heart.
2. **Schedule A — taxable gifts** — compute the reconciliation (gross − annual exclusions − marital − charitable) +
   gift-splitting ($38,000) + the noncitizen-spouse $190,000. Direct-entry the per-gift detail. [UNVERIFIED] recon line #s.
3. **GST (Sch D) + DSUE (Sch C)** — compute the GST 40% × inclusion-ratio mechanic + the DSUE → Part 2 line 7 credit
   increase (structure; direct-entry the DSUE amount / per-transfer detail). [UNVERIFIED] sub-line #s.
4. **OBBBA year-keying + the [UNVERIFIED] caveat + filing diagnostics** — year-key all 2025 constants (BEA/credit/
   exclusion) so 2026's $15M doesn't leak in; carry the [UNVERIFIED] structural-line-number risk as a documented
   caveat (re-verify the PDF face before the tts build); who-must-file / due-date / gift-splitting diagnostics; one `709` form.
