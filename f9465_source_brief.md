# Form 9465 Source Brief — Installment Agreement Request
*Research pass 2026-07-13 (tts s77 / payment-cluster draft-to-gate batch order 1). Gap re-confirmed
2026-07-13: `lookup/9465/export/` = 404.*

## Authoritative sources (all fetched/verified 2026-07-13)

| Source | Revision | Verified how |
|---|---|---|
| Form 9465 face | **Rev. September 2020** (Cat. No. 14842Y, OMB 1545-0074) | f9465.pdf downloaded from irs.gov/pub/irs-pdf 2026-07-13, pymupdf text extraction |
| Instructions | **i9465 Rev. July 2024** ("For use with Form 9465 (Rev. September 2020)", Cat. No. 58607N) | i9465.pdf same pass |
| About page | Recent Developments: **"None at this time"**; current revisions confirmed 0920 + 07/2024 | irs.gov/forms-pubs/about-form-9465 fetched 2026-07-13 |
| Live fee schedule | irs.gov/payments/payment-plans-installment-agreements, **page reviewed 28-Jun-2026** | fetched 2026-07-13 — confirms the printed July-1-2024 table is STILL current |
| MeF business rules | 1040_Business_Rules_2025v5.3.csv (local, tts docs/mef) — the F9465-* family | grepped 2026-07-13 |
| MeF schema | IRS9465.xsd, `2025v5.3/InstallmentAgreement/9465/` — included by ReturnData1040 (`IRS9465` element, slot ~2273) | parsed 2026-07-13 |

**Fee-schedule currency check (the s67 stale-fee class):** search surfaced **T.D. 10045
(91 FR 20902, Apr. 20, 2026)** amending 26 CFR Part 300 — post-dating the printed i9465 table.
Cross-checked against the IRS's live payment-plan fee page (reviewed 28-Jun-2026, i.e. AFTER the
T.D.): the installment-agreement fees are UNCHANGED ($22/$69/$107/$178; low-income DDIA waiver /
$43; revision $89/$43/$10-OPA) — the T.D.'s Part-300 changes ride other user-fee sections
(search context: enrolled-agent enrollment fees). Cornell LII's §300.1 text is STALE (2016-era
$225/$149 tier — do not cite it). **YEAR-KEYED: re-verify the fee table each January against the
live payments page.**

## Face structure (Rev. 9-2020, verbatim)

**Header:** "This request is for Form(s) (for example, Form 1040 or Form 941)" + "Enter tax
year(s) or period(s) involved". Attach to the FRONT of the return when filing together.

**Part I:** 1a name/SSN/spouse/address (+foreign) · 1b new-address checkbox · 2 business name +
EIN ("must no longer be operating") · 3 home phone + best time · 4 work phone + ext + best time ·
5 total owed per return(s)/notice(s) · 6 additional balances due (even if in an existing IA) ·
7 = 5+6 · 8 payment made with the request · 9 = 7−8 (amount owed) · **10 = line 9 ÷ 72.0** ·
11a proposed monthly payment ("if no payment amount is listed on line 11a, a payment will be
determined for you by dividing the balance due on line 9 by 72 months") · 11b revised payment
(when 11a < line 10 and you can raise it to ≥ line 10) + the **can't-increase checkbox → attach
Form 433-F** · bullets: 11a/11b ≥ line 10 with $25,001-$50,000 owed → must complete line 13 OR 14
(else 433-F); line 9 > $50,000 → 433-F · 12 monthly payment day (**"Don't enter a date later than
the 28th"**) · 13a routing (9-digit, prefix 01-12/21-32) / 13b account (≤17 chars) + the ACH
authorization text (revoke ≥14 business days before settlement, 800-829-1040) · **13c low-income
only: can't-DD checkbox → user fee reimbursed upon completion** · 14 payroll-deduction checkbox →
attach completed Form 2159. Signature: joint returns BOTH must sign (direct debit "won't be
approved unless you (and your spouse if filing a joint return) sign").

**Part II (page 2)** — required only when **ALL THREE**: (1) defaulted on an IA in the past 12
months; (2) owe >$25,000 but ≤$50,000; (3) line 11a (or 11b) < line 10. Lines 15-27: county ·
16a marital / 16b share household expenses · 17 dependents · 18 age-65+ count · 19 pay frequency
(weekly / biweekly / monthly / semimonthly) · 20 net income per pay period · 21/22 spouse
frequency+income (complete iff live-with-and-share-expenses OR community-property state — either
MFJ or MFS) · 23 vehicles · 24 car payments/month · 25a-c health insurance (deducted? premium $) ·
26a-c court-ordered payments · 27 child/dependent care per month.

## Agreement-type criteria (i9465 7-2024, verbatim substance)

- **Guaranteed IA (§6159(c))**: tax owed ≤ $10,000 AND past 5 years all returns timely
  filed/paid + no prior IA AND agree to full pay within 3 years + comply while in effect AND
  financially unable to pay in full when due.
- **Streamlined IA**: assessed liability ≤ $25,000; OR $25,001-$50,000 AND direct debit or
  payroll deduction. Proposed payment must full-pay within **72 months** or by the **CSED**
  (normally 10 years from assessment), whichever is less. No financial statement, generally no
  NFTL.
- **PPIA**: won't full-pay by the CSED → financial statement (433-F) + periodic reviews.
- **Pay-in-full ≤180 days**: don't file 9465 (short-term plan, $0 fee, OPA up to <$100,000).
- **OPA**: balance ≤ $50,000 → apply online instead, lower fee.
- Don't use 9465: business still operating owing employment/unemployment tax; bankruptcy;
  pending/accepted OIC.

## User-fee schedule (effective July 1, 2024 — VERIFIED CURRENT 2026-07-13; year-keyed)

| Channel | Direct debit | Other |
|---|---|---|
| OPA (online) | **$22** | **$69** |
| Form 9465 / phone / mail | **$107** | **$178** |

Payroll deduction (Form 2159) = $178. **Low-income** (AGI ≤ 250% federal poverty guidelines,
most recent year available; Form 13844 if not auto-identified): DDIA → fee **WAIVED**; non-DD →
reduced **$43**, and if unable to DD (box 13c) the $43 is **reimbursed** on completion. Modify/
restructure: $89 ($43 low-income; waive/reimburse rules apply); **$10** when reinstated or
restructured through OPA. Interest + late-payment penalty continue to accrue; refunds offset
against the liability regardless of the IA.

## MeF (the IRS9465 document — e-files WITH the 1040)

`IRS9465` is included by ReturnData1040 (2025v5.3) from the InstallmentAgreement family — the
tts leg is a full print + MeF-document unit (unlike 2553/2848). Schema carries the whole face
incl. Part II elements. Key ACTIVE business rules (1040_Business_Rules_2025v5.3.csv):

- **F9465-001-03**: not e-fileable when `TotalTaxDueAmt` > **50000** (paper 9465 + 433-F).
- **F9465-014/-015**: line 1 SSNs must match the return header.
- **F9465-016-01/-017-01**: 13a/13b routing+account must pair.
- **F9465-018-01**: one of home/work phone (domestic or foreign) REQUIRED.
- **F9465-019-02**: if an IRS Payment Record is present, Form 9465 `PaymentAmt` (line 8) **must
  equal the IRSPayment `PaymentAmt`** — the s76 EFW interplay.
- **F9465-026-01**: `PayrollDeductionAgreementInd` (box 14) NOT e-fileable (paper + 2159).
- **F9465-027-01**: `PaymentDueAmt` (11a) < `CalculatedMonthlyPymtAmt` (line 10) → reject.
- **F9465-029-02/-030-02/-038-02**: attached to 1040 → `F9465TaxReturnTypeCd` must not be an
  employment/excise form; 1040-type code requires `IATaxYrDt`, forbids `TaxPeriodDetailGrp`.
- **F9465-037-01**: `CanNotIncreasePaymentInd` NOT e-fileable.
- **F9465-039-01**: `RevisedMonthlyPaymentAmt` (11b) nonzero and < line 10 → reject.
- **F9465-040**: routing number present → `NoElectronicPaymentInd` (13c) must NOT be checked.
- **F9465-041**: `TotalBalanceDueAmt` (7) ≥ `TaxDueAmt` (5) + `AdditionalBalanceDueAmt` (6).
- **F9465-042**: 11b ≥ line 10 → can't-increase box must NOT be checked.
- **F9465-043**: 11a and 11b nonzero → must not be EQUAL.
- **F9465-044**: owed $25,000-$50,000 with 11a/11b > line 10 → must carry 13a+13b OR the
  payroll box — and since payroll can't e-file (026), the e-file path is effectively
  **direct-debit-or-reject** in that band.

## Line-10 rounding note (flag for Gate-1)

The face says "Divide the amount on line 9 by 72.0" with no stated rounding. The spec encodes
the minimum-payment gate as **ceiling to the whole dollar** (payment × 72 ≥ balance is the
"full pay within 72 months" test; whole-dollar per the suite convention) — flagged in the WO
walk as a convention, not a printed rule.

## Where-to-file chart (standalone filings; i9465 7-2024 — year-watched)

Keyed on whether ANY year in the request had Schedule C/E/F: without C/E/F → Andover MA
(310 Lowell St., Stop 830) / Doraville GA (P.O. Box 47421, Stop 74 — **GA files here**) /
Kansas City MO (Stop P-4 5000); with C/E/F → Holtsville NY / Memphis TN (P.O. Box 69, Stop 811 —
**GA files here**) / Ogden UT / Philadelphia PA; foreign/territory/APO-FPO/2555/4563/dual-status →
Austin TX (3651 South I-H 35, 5501AUSC). Attached-to-return filings just ride the return.

## Boundaries (stated, not built)

- Form 433-F (Collection Information Statement) — referenced, not specced.
- Form 2159 (payroll deduction) — referenced, not specced; not e-fileable anyway.
- Standalone InstallmentAgreement MeF submissions (9465 without a 1040) — out of scope; the
  suite files 9465 WITH the return or prints for mail.
- Business-form type codes (941 etc., defunct sole prop) — print-path only; blocked in e-file
  when attached to a 1040 (F9465-029-02).
