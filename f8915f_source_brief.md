# Form 8915-F — Source Brief (RS draft-to-gate, tts s79)

*Drafted 2026-07-14 (autonomous, the s67 recipe — BUILD_ORDER "next NEW item: 8915-F,
spec-first gap check"). Gap confirmed 2026-07-14: `lookup/8915F|8915-F/export/` = 404 ×2.*

## Sources (all fetched/verified 2026-07-14)

| Source | Vintage | How verified |
|---|---|---|
| **Form 8915-F** — Qualified Disaster Retirement Plan Distributions and Repayments | **Rev. December 2025** ("Created 5/23/25", Cat. 75585Y, seq. 915) | Fresh irs.gov download, pymupdf full-text |
| **Instructions for Form 8915-F** | **Rev. December 2025** (Cat. 37509G, dated Dec 22, 2025; 73 pp incl. Appendices A-D) | Fresh irs.gov download, pymupdf; targeted verbatim reads |
| **About page + Recent Developments** | Page reviewed 27-Jun-2026 | WebFetch — 4 developments listed, ALL target older revisions (see below) |
| **MeF IRS8915F.xsd TY2025** | 2025v5.3 (Final Schema, released Apr 23 2026); also present in 5.4/2026v1.0 | Local `docs/mef/schemas/2025v5.3/.../Common/IRS8915F/` read in full |
| **F8915F business rules** | 1040_Business_Rules_2025v5.3.csv | Local grep — exactly 3 Active rules |

**⚠ Revision-currency note:** the About page's Recent Developments all reference Rev. Jan
2022/2023/2024 — the LIVE form and instructions are **Rev. December 2025** (both). The
20-Dec-2024 development ("Discrepancy in Appendix D, Rev. Jan 2024") flagged an off-by-one:
Appendix D "inadvertently provides taxpayers with 1 less day than is granted for repayments"
(disasters with start dates Jul-Dec 2024); **corrected in the current tables** — but it names
the exact failure class our helpers must pin (179-day vs 180-day count boundaries).

## What the form is (the "forever form")

Redesigned continuous-use replacement for the alphabetical 8915 series ("Additional
alphabetical Forms 8915... will not be issued"). Items A (tax year filed, 2021-2028+Other)
and B (disaster year, 2020-2027+Other) name the form instance — e.g. "2025 Form 8915-F
(2024 disasters)". Item C = FEMA DR numbers (face shows 6 slots; XSD allows 20; Part I
table + >2-disasters overflow checkbox); item D = coronavirus only (never in item C).
**If married, each spouse files a SEPARATE 8915-F** (the name/SSN ride the document).
Charts 1/2 on the face route which lines to complete; STOP arms when the form can't be
used. Do NOT use for: 2019 disasters (8915-D), distributions MADE in 2020 (8915-E).

## SECURE 2.0 §331 core law (verbatim-verified)

- **Qualified disaster distribution (QDD) requirements** (per disaster): (1) made within
  the disaster's qualified disaster distribution period; (2) main home in the qualified
  disaster area (state/territory/tribal government) at any time during the disaster period;
  (3) sustained an economic loss (property loss/damage, displacement, livelihood). When all
  three hold, **ANY distribution (including periodic payments and RMDs)** from an eligible
  retirement plan can be designated a QDD "regardless of whether the distribution was made
  on account of a qualified disaster," without regard to need or the loss amount. Plan loan
  offsets qualify. Qualified disaster = Presidentially-declared MAJOR disaster ("DR" FEMA
  numbers only, FEMA.gov/disaster/declarations).
- **Qualified disaster distribution period**: begins on the disaster beginning date, ends
  **179 days** after the LATEST of: disaster beginning date · disaster declaration date ·
  December 29, 2022. Published pins: DR-4682-WA (begin 11/3/2022, decl 1/12/2023) → last
  day 7/10/2023; DR-4681 (10/1/2022, 12/30/2022) → 6/27/2023; DR-4685-GA (1/12/2023,
  1/16/2023) → 7/14/2023. Appendix C is the IRS's own day-count table.
- **Limit: $22,000 per disaster** (2021+ disasters), from ALL plans in aggregate — an
  ACROSS-YEARS per-disaster cap, allocated among plans "by any reasonable method." $100,000
  only for 2020-vintage (item B = 2020). **F8915F-003 (Active) pins line 1d ≤ 22000 × the
  number of qualified disasters.**
- **NOT QDDs**: §415 corrective distributions; §402(g)/401(k)/401(m) excesses; §72(p)
  deemed-distribution loans; §404(k) dividends; life-insurance cost; §409(p) prohibited
  allocations; §414(w) permissible withdrawals; accident/health premium distributions.
- **Taxation**: included in income in equal amounts over 3 years beginning with the
  distribution year, UNLESS the taxpayer elects full inclusion (the line 11/22 checkbox;
  **the boxes must MATCH — "You must check the box on this line if you check the box on
  line 22"** and vice versa). **Death before the last spread year collapses the remainder
  onto the decedent's final return** (line 13/24). QDDs are **exempt from the 10%
  additional tax (and the 25% SIMPLE-IRA tax) and are NOT reported on Form 5329**; the
  line 7 excess MAY be subject to it. Not eligible for the Form 4972 20% capital-gain
  election or 10-year option.
- **Repayment**: any portion eligible for tax-free rollover may be repaid to an eligible
  plan (401(k)/qualified annuity/TSA/governmental 457/IRA); earliest = the day AFTER
  receipt; deadline = **3 years from the day after receipt** ("amounts paid later than 3
  years and 1 day after you received the distribution can't be repayments"); capped at the
  original distribution; treated as trustee-to-trustee transfer (not income, not a rollover
  for the one-per-year IRA rule). Report on THIS year's 8915-F only repayments made before
  filing and by the due date incl. extensions; later repayments ride next year's form or
  carry BACK via amended 8915-F/1040-X (the Rudy Examples 1-2 pin both directions).
  CANNOT repay: beneficiary (non-spouse) QDDs · RMDs · SEPP series (10-yr/life/joint).
- **Part IV qualified distribution (main home)**: hardship distribution from a 401(k) or
  TSA, or a first-time-homebuyer IRA distribution; received **no more than 180 days before
  the first day of the disaster and no later than 30 days after the last day**; intended
  for a main home in the disaster area that was NOT purchased/constructed because of the
  disaster. Taxed fully in the distribution year (NO 3-year spread); repayable only during
  the **qualified distribution repayment period** — begins on the disaster beginning date,
  ends **180 days** (not 179 — the Appendix-D off-by-one class) after the latest of
  begin/declaration/12-29-2022. Published pins: DR-4682-WA → 7/11/2023; DR-4681 →
  6/28/2023; DR-4685-GA → 7/15/2023. Unrepaid portions may owe the 10%/25% additional tax
  (line 32 note); an unrepaid qualified distribution that meets the QDD tests may be
  RE-designated as a QDD.

## Face math (Rev. 12-2025 — NEW line 5a redesign)

**What's New**: this revision ADDS line 5a (non-QDD portion of lines 2-4 col (a)); the old
line 5 became **5b**. The 2025v5.3 XSD already models 5a/5b (TotalNonqlfyDisasterDistriAmt /
CYTotalDistributionsAmt / QualifiedDistributionsAmt). Part I ladder:
- **1a-1e** (col (b)): single NEW disaster → skip to 1e = $22,000; repeat disaster →
  1a = limit × repeat-disaster count, 1b = prior-year QDDs for those disasters, 1c = 1a−1b,
  1d = limit × NEW disaster count, **1e = 1c + 1d** (zero → complete 2-4 col (a) only,
  line 6 = -0-, nothing in Parts II/III). Worksheet 1B mandatory when: >1 plan type AND
  5b(a) exceeds 1e (three-condition trigger).
- **2/3/4** col (a) = this year's distributions by bucket (other-than-IRA / traditional
  incl. SEP+SIMPLE / Roth incl. Roth SEP+SIMPLE); **5a(a)** = the non-QDD portion of their
  sum; **5b(a)** = sum(2-4(a)) − 5a; **5b(b) = min(5b(a), 1e)**; then allocate 2-4 col (b)
  by any reasonable method summing to 5b(b).
- **6** = 5b(b) = total QDDs (early-withdrawal additional tax WAIVED); **7** = excess of
  sum(2-4(a)) over 6 → reported as normal IRA/pension income (may feed Part IV; may owe
  the additional tax).
- **Part II (other-than-IRA)**: 8 = 2(b); 9 = applicable cost; 10 = 8−9; 11 = 10 or 10÷3.0
  (opt-out box); 12 = Worksheet 2 prior-year income (**attach the worksheet to the back of
  the form** — the XSD carries BinaryAttachment refs on 12/14/23/25); 13 = 11+12;
  14 = Worksheet 3 repayments; **15 = 13−14 (floor -0-) → 1040 line 5b**.
- **Part III (IRAs)**: 16 gate; 17 8606-required gate; **18 = 8606 line 15b / 19 = 8606
  line 25b** (attributable-to-THIS-form allocation when multiple 8915-Fs); 20 = 3(b) not
  on 8606; 21 = 18+19+20; 22 = spread/opt-out (must match 11); 23 = Worksheet 4;
  24 = 22+23; 25 = Worksheet 5 repayments; **26 = 24−25 (floor -0-) → 1040 line 4b**.
  Before you begin: complete this year's Form 8606 if required.
- **Part IV**: disaster table incl. END date; 27 8606-reported gate; 28 = qualified
  distributions received (reduce line 7 by any overlap; exclude 8606/line-8/line-20
  amounts); 29 cost; 30 = 28−29; 31 repayments; **32 = 30−31 → 4b (IRA) or 5b (other)**;
  may owe the additional tax.

## MeF channel

**IRS8915F is a ReturnData1040 document (2025v5.3), slot ~2014, maxOccurs=6** (multiple
instances: same item A, different item B years; separate spouse forms). Document carries
its own PersonNm + SSN. Items A/B are XSD **choice** structures: TaxYearFilingFormCd enum
2022-2028 (or OtherTaxYearFilingFormInd checkbox with fixed otherTaxYrCd="2021");
CalendarYrDisasterCd enum 2021-2027 (or the 2020 checkbox). FEMA numbers pattern-locked
(`NNNN-DR-XX` / `DR-NNNN-XX` / `DR-NNNN`), item C max 20, Part I disaster groups max 20
(number + declaration date + begin date), Part IV FEMA groups max 10 (+ end date).
CoronavirusInd = item D. Worksheet lines 12/14/23/25 accept referenceDocumentId →
BinaryAttachment (the attach-worksheet-to-back instruction's e-file mirror).

**Business rules (exactly 3 Active):** F8915F-001-01 (CalendarYrDisasterCd must not be
2026/2027 on a TY2025 return) · F8915F-002-01 (TaxYearFilingFormCd must not be
2026/2027/2028 on a TY2025 return) · **F8915F-003 (line 1d ≤ 22000 × number of qualified
disasters)**.

## Proposed v1 scope (the Gate-1 walk skeleton)

- **W1 — the QDD framework**: the 3-part test + the any-distribution designation rule; the
  179-day distribution period (published date pins); the $22,000-per-disaster aggregate
  cap; the not-QDD list; qualified disaster = DR-declared major only.
- **W2 — Part I ladder + spread**: 1a-1e (incl. the single-new-disaster shortcut and
  F8915F-003); the NEW 5a/5b redesign; line 6 waiver + line 7 excess; the 3-year spread
  with the ÷3.0 whole-dollar convention FLAGGED (the 9465 ÷72 class — face prints no
  rounding); the 11↔22 box-consistency rule; death-collapse.
- **W3 — repayments + Parts III/IV**: 3-years-and-1-day; before-filing/due-date inclusion
  + carryback/forward (Rudy pins); the can't-repay list; the 8606 15b/25b ties; Part IV
  (the −180d/+30d receipt window, the 180-day repayment period — the Appendix-D
  off-by-one class pinned, NO spread, 32's additional-tax exposure, re-designation).
- **W4 — e-file + landings**: IRS8915F ReturnData1040 max 6 (multi-instance identity =
  item A/B pair + spouse); the year-enum rejects; worksheet BinaryAttachment refs;
  15 → 1040 5b / 26 → 4b / 7 → normal income; QDDs never on 5329 (the tts 5329-unit seam);
  separate-form-per-spouse. STATED BOUNDARIES: the Worksheet 1B/2/3/4/5 internals stay the
  tts engine's job (the ES-worksheet precedent); 2020-vintage/coronavirus rows =
  repayment/income-continuation arms only (no new 2020 QDDs possible); Appendix A/C/D
  tables are derivable from the period helpers, not re-encoded.

entity_types ['1040']; print + MeF document (the s72 recipe — extract bridge-gated on the
same derivation the print uses). tts leg on approval: inputs + compute (per-disaster
engine) + render + IRS8915F builder + the 4b/5b landing ties + the 5329-waiver seam.
