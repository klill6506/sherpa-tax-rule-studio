# 1040-V / 1040-ES Voucher Pair Source Brief
*Research pass 2026-07-13 (tts s77 / payment-cluster draft-to-gate batch order 3). Gaps re-confirmed
2026-07-13: `lookup/1040V/export/` = 404 · `lookup/1040ES/export/` = 404.*

## Authoritative sources (fetched/verified 2026-07-13, pymupdf extraction)

| Source | Vintage | Notes |
|---|---|---|
| Form 1040-V | **2025** (Created 12/22/25, Cat. No. 20975C) | the voucher for the TY2025 balance due — 2 pages incl. the mailing chart |
| Form 1040-ES package | **2026** (Feb 12, 2026, Cat. No. 11340T) | the estimates a TY2025 client pays DURING 2026 — 16 pages; worksheet + 4 vouchers |

Both print-only. The electronic halves already shipped in tts s76: IRSPayment (EFW balance due)
and IRSESPayment (scheduled quarterly debits) — the vouchers are the PAPER complements, and the
spec ties them: an EFW-elected return suppresses the 1040-V; a debited quarter suppresses that
quarter's ES voucher.

## ⚠⚠ THE ADDRESS TRAP (the 2553 address-drift class, now three-way)

Three DIFFERENT address sets, all year-watched, and the ES package warns explicitly: "do not mail
your estimated tax payments to the address shown in the Form 1040 instructions."

**1040-V chart (2025):**
- AL FL **GA** LA MS NC SC TN TX → IRS, **P.O. Box 1214, Charlotte, NC 28201-1214**
- all other states → IRS, **P.O. Box 931000, Louisville, KY 40293-1000**
- foreign / American Samoa / PR §933 / APO-FPO / 2555 / 4563 / dual-status / Guam-USVI
  nonpermanent → IRS, **P.O. Box 1303, Charlotte, NC 28201-1303**

**1040-ES chart (2026):**
- AL AK AZ CA CO FL **GA** HI ID KS LA MI MS MT NE NV NM NC ND OH OR PA SC SD TN TX UT WA WY →
  IRS, **P.O. Box 1300, Charlotte, NC 28201-1300**
- AR CT DE DC IL IN IA KY ME MD MA MN MO NH NJ NY OK RI VT VA WV WI →
  IRS, **P.O. Box 931100, Louisville, KY 40293-1100**
- foreign/territory/APO-FPO/2555/4563/dual-status → **P.O. Box 1303, Charlotte** (same as V)
- Guam bona fide → Dept. of Revenue and Taxation, Gov't of Guam, P.O. Box 23607, GMF, GU 96921;
  USVI bona fide → VI Bureau of Internal Revenue, 6115 Estate Smith Bay, Suite 225, St. Thomas,
  VI 00802 (bona fide residents split income-tax vs SE-tax vouchers between the two charts).
- USPS-only caution: private delivery services can't serve the P.O. boxes.

GA lands at **1214** for the V and **1300** for the ES — one digit of P.O.-box drift from a wrong
payment posting. This is why the pair gets a spec.

## Form 1040-V (2025) — mechanics

- Purpose: rides a **check/money-order** payment of the "Amount you owe" on the 2025
  1040/1040-SR/1040-NR. Paying online → "don't complete this form."
- Voucher lines: 1 SSN (joint = first SSN on the return) · 2 spouse SSN · 3 amount paid by
  check/MO · 4 name(s)/address (foreign spaces provided).
- Check prep: payable "United States Treasury"; never cash by mail (retail cash option:
  $1,000/day/transaction via acipayonline.com after registering); daytime phone + SSN/ITIN +
  "2025 Form 1040[-SR/-NR]" on the check; amount format $XXX.XX (no dashes); **no single check
  ≥ $100,000,000** (split into multiple); **don't staple** the payment or voucher to the return
  or each other — loose in the envelope.
- Check-as-EFT notice: the IRS may convert the check to a one-time electronic funds transfer.

## Form 1040-ES (2026) — who must pay + dates + voucher mechanics

- **General rule**: estimates required when BOTH (1) expected 2026 owe ≥ **$1,000** after
  withholding/refundable credits AND (2) withholding+credits < smaller of **90%** of 2026 tax or
  **100%** of 2025 tax (12-month-year returns only). **Higher income**: 2025 AGI > **$150,000**
  ($75,000 MFS-2026) → substitute **110%** for the 100% arm (not for farmers/fishers).
  **Farming/fishing** (⅔ of 2025 or 2026 gross income): substitute **66⅔%** for 90%; may instead
  pay ALL by **Jan 15, 2027**, or file the 2026 return by **Mar 1, 2027** and pay in full (no
  estimates required). **Exception**: no 2025 tax liability for a full 12-month year (citizen/
  resident all year) → no estimates required.
- **Due dates (calendar 2026)**: **Apr 15 · Jun 15 · Sep 15, 2026 · Jan 15, 2027**; the Jan-15
  payment is skippable by filing the 2026 return by **Feb 1, 2027** and paying the balance in
  full. Fiscal-year: 15th day of the 4th/6th/9th months + the 1st month following. Postmark =
  payment date — with the NEW USPS clarification: the postmark is when USPS PROCESSES the piece
  at a facility, not the drop-off date. More than four payments allowed (copy an unused voucher).
  These are the same four dates the s76 IRSESPayment records fix per FPYMT-088-11.
- **Voucher mechanics**: complete a voucher ONLY when paying by check/MO; enter only the
  check amount (a credited 2025 overpayment reduces the payment but NEVER goes in the box);
  spouses planning separate returns file separate vouchers; joint-voucher BARS: nonresident-alien
  spouse, decree of divorce/separate maintenance, different tax years — and registered domestic
  partners/civil unions can never pay jointly; joint voucher lists names/SSNs in return order;
  ITIN wherever an SSN is asked; name-change → statement on the front of the 2026 return listing
  payments + prior names/SSNs; "2026 Form 1040-ES" + SSN on the check; $100M cap; preprinted
  vouchers get corrections (cross out a deceased/divorced spouse); address change → Form 8822.

## What the spec does NOT cover (stated boundaries)

- The 2026 Estimated Tax Worksheet math (standard deduction $32,200/$24,150/$16,100, brackets,
  SE worksheet) — the app's own proforma/ES engine computes the amounts; the spec covers the
  REQUIRED-ANNUAL-PAYMENT test, dates, voucher mechanics, and addresses.
- 1040-ES (NR) and the 1040-SS filer worksheet — out of suite scope this season.
- EFTPS/Direct Pay/card mechanics — print blurbs only.
