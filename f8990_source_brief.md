# Form 8990 (WO-14) — Source Brief: §163(j) Business-Interest Limitation

*Greenfield RS-first authoring brief for Form 8990. Finishes the 1120 module's biggest deferred leg
(the §163(j) gate on Sch K Q24 routed here); also serves 1065/1120-S/1040. First of Ken's federal-forms
queue (SPINE S-16). Opened 2026-07-05. Front-door step: GAP-CHECKED → research-verified (this file) →
Gate-1 scope walk → author.*

**Every fact below verified VERBATIM against the FINAL Form 8990 (Rev. 12-2025) + i8990 (Rev. 12-2025)
+ IRC §163(j) (never memory), per the Authoritative-Source Rule.**

---

## Gap-check
`8990` is not in the 92-form federal prod set → GAP. entity_types = **1120 / 1065 / 1120S / 1040** (any
taxpayer with business interest expense subject to the limit files it — i8990 "Who Must File" names
individuals, corporations, partnerships, and S corporations).

## Sources (FINAL)
| Source | Scope | Rev/date |
|---|---|---|
| **Form 8990 (Rev. 12-2025)**, Created 9/9/25 | The limitation form, Parts I–III + Sch A/B | Dec 2025 |
| **i8990 (Rev. 12-2025)**, dated 21-Jan-2026 | Instructions | Dec 2025 |
| **IRC §163(j)** | (1) limit / (2) carryforward / (7) excepted / (8) EBITDA ATI | Cornell LII |
| **P.L. 119-21 (OBBBA)** | Restored the EBITDA add-back for years after 12/31/2024 | i8990 "What's New" |

> **⚠ Cite the OBBBA effective date to P.L. 119-21 + i8990 "What's New", NOT Cornell** — the Cornell/OLRC
> §163(j)(8) text renders EBITDA-basis but has not yet ingested the OBBBA "after 12/31/2024" dating.

---

## The compute heart — Part I (verbatim line map)
**Section I — Business Interest Expense:** L1 current-year BIE (excl. floor plan) · L2 disallowed-BIE
carryforward from prior years (N/A to a partnership) · L3 partner's excess BIE treated as paid (Sch A) ·
L4 floor plan financing interest · **L5 total BIE (add L1–4)**.

**Section II — Adjusted Taxable Income:** L6 tentative taxable income; **Additions (L7–16)** — L7 non-ATB
loss/deduction · L8 BIE not from a pass-through · L9 §172 NOL deduction · L10 §199A QBI deduction ·
**★ L11 "Deduction allowable for depreciation, amortization, or depletion attributable to a trade or
business"** (the OBBBA EBITDA add-back — an ADDITION for TY2025; was suspended/reserved 2022–2024) · L12
pass-through loss/deduction items · L13 other additions · L14 partner ETI (Sch A) · L15 S-corp ETI (Sch B) ·
**L16 total (add L7–15)**; **Reductions (L17–20, bracketed)** — non-ATB income/gain · BII not from a
pass-through · pass-through income/gain · other reductions; **L21 total reductions**; **L22 ATI = combine
L6 + L16 + L21**.

**Section III — Business Interest Income:** L23 current-year BII · L24 pass-through excess BII (Sch A/B) ·
**L25 total BII (L23+L24)**.

**Section IV — 163(j) Limitation:** **L26 = 30% × ATI (L22)** (i8990: "The applicable percentage is 30%") ·
L27 BII (L25) · L28 floor plan (L4) · **L29 total limitation (L26+L27+L28)** · **L30 allowable BIE deduction**
(= min(L5, L29)) · **L31 disallowed BIE carryforward = L5 − L29** (if ≤0, enter 0; carries forward indefinitely).

## Part II — Partnership pass-through items
L32 excess BIE (EBIE = L31) · L33 = L5 − (L4+L25) · L34 = L26 − L33 · L35 = L34 ÷ L26 (decimal) · **L36 excess
taxable income (ETI) = L35 × L22** · L37 excess BII = L25 − (L1+L2+L3).

## Part III — S-corporation pass-through items (parallel to Part II; NO EBIE at S-corp level)
L38 = L5 − (L4+L25) · L39 = L26 − L38 · L40 = L39 ÷ L26 (decimal) · **L41 ETI = L40 × L22** · L42 excess BII =
L25 − (L1+L2+L3).

**Schedule A** (partner's §163(j) excess items, cols a–i) / **Schedule B** (S-corp shareholder's, cols a–d) —
feeders completed BEFORE Part I when the taxpayer is a partner/shareholder of a pass-through.

---

## Statute (§163(j), verbatim substance)
- **(j)(1):** deduction ≤ business interest income + **30% of ATI** + floor plan financing interest.
- **(j)(2):** disallowed business interest "treated as business interest paid or accrued... in the succeeding
  taxable year" → **indefinite carryforward**.
- **(j)(8):** ATI computed "without regard to... any deduction allowable for depreciation, amortization, or
  depletion" → **EBITDA basis** (restored permanently by OBBBA for years after 12/31/2024).
- **(j)(7) excepted trades/businesses (NOT subject to the limit):** employee services; **electing real
  property trade or business**; **electing farming business**; certain **regulated utilities**.

## Who files / exemption
All taxpayers with business interest expense / a disallowed-BIE carryforward / excess BIE file Form 8990,
UNLESS exempt: the **§448(c) small-business exemption = average annual gross receipts ≤ $31,000,000** (prior
3 years, 2025-indexed; non-tax-shelter). Exempt taxpayers do not file. Excepted businesses (§163(j)(7)) elect out.

---

## Carried [UNVERIFIED] / flags
- OBBBA effective date cited to P.L. 119-21 + i8990 (not Cornell, which lags).
- Re-verify at TY2026 ($31M §448(c) index; the 30% is statutory/stable; the Rev. date).

## Proposed authoring leg (subject to Gate-1 scope walk)
One `8990` form (`load_8990.py`): Part I ATI (with the L11 EBITDA add-back) → 30% limitation → allowable BIE +
carryforward; Part II/III pass-through ETI/EBIE/excess-BII; $31M exemption gate + §163(j)(7) excepted-business
diagnostic. entity_types 1120/1065/1120S/1040. Author `READY_TO_SEED=False` → SQLite-validate → Ken review → seed → export.
