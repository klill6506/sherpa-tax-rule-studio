# Form 4868 — Source Brief (RS draft-to-gate, tts s78)

*Drafted 2026-07-14 (autonomous, the s67 recipe — BUILD_ORDER "next NEW item: 4868, separate
MeF family, spec-first gap check"). Gap confirmed 2026-07-14: `lookup/4868/export/` = 404.*

## Sources (all fetched/verified 2026-07-14)

| Source | Vintage | How verified |
|---|---|---|
| **Form 4868 (2025)** — Application for Automatic Extension of Time To File U.S. Individual Income Tax Return | 2025 revision, "Created 10/1/25", Cat. No. 13141W, OMB 1545-0074 — a self-contained 4-page form+instructions document (there is NO separate i4868) | Fresh irs.gov download (`f4868.pdf`), pymupdf full-text extraction |
| **About Form 4868 page** | Page reviewed/updated 30-Mar-2026 | WebFetch sweep — **Recent Developments: "None at this time"**; current revision = 2025 |
| **MeF 4868 package 2026v1.0** | Released May 28 2026, "Final Schema Version Rl10A Drop 1", TaxYear **2026** — `4868_2026v1.0.zip` already in tts `docs/mef/schemas/2026v1.0/` | XSDs read directly (Return4868 / ReturnHeader4868 / ReturnData4868 / IRS4868); business-rules PDF (05-07-2026, 7 pp) extracted verbatim |

## The headline structural finding — a SEPARATE MeF family

Form 4868 is **not** a ReturnData1040 document (unlike 9465/8888). It is its **own MeF
submission type**: `ReturnTypeCd` enum = "4868", its own `Return4868.xsd` /
`ReturnHeader4868.xsd` / `ReturnData4868.xsd`. The tts leg is therefore a **new submission
builder**, not a new document slot in the 1040 builder.

**ReturnData4868 content model (complete):**
1. `IRS4868` (required) — SIX face elements only: TotalTaxLiabilityAmt (L4),
   TotalPaymentsAmt (L5), BalanceDueAmt (L6), TaxpayerIsPayingAmt (L7), TaxpayerAbroadInd
   (L8 checkbox), NonresWithNoWagesSubjToWhInd (L9 checkbox) — ALL minOccurs=0.
2. `IRSPayment` (0..unbounded) — the SAME record tts s76 built (CorporateIncomeTax/Common
   dependency; FPYMT-129 limits to one instance in practice).
3. `IRSESPayment` (0..4) — the s76 ES record, per IndividualIncomeTax/Common.
4. BinaryAttachment / GeneralDependencySmall — declared in the XSD **but R0000-195 (Active)
   rejects any submission containing a binary attachment**. Refusal-encoded.

**ReturnHeader4868 (the signature story — the biggest behavioral finding):**
- Filer block: PrimarySSN + PrimaryNameControlTxt required; SpouseSSN/SpouseNameControlTxt
  optional; NameLine1Txt; USAddress|ForeignAddress choice; InCareOfNm.
- Signature groups are ALL minOccurs=0 (SelfSelectPINGrp, PractitionerPINGrp via
  OriginatorGrp, PINTypeCd, JuratDisclosureCd, signature PINs/dates).
- **R0000-098-01: a PIN/signature is required ONLY when an IRSPayment or IRSESPayment record
  is present.** A no-payment e-filed 4868 needs NO signature at all — matching the paper
  face, which has NO signature line. With a spouse SSN + payment: R0000-099 adds the spouse
  PIN. The full per-PIN-type ladders are R0000-670/-671 (Self-Select Practitioner),
  -681/-682 (Self-Select On-Line), -697/-698 (Practitioner).
- **JuratDisclosureCd enum (exactly two values):** "Form 4868" and "Form 4868 with
  Practitioner PIN and EFW". Mapping (F4868-007/-008/-009): payment present + PINTypeCd
  Self-Select Practitioner or Self-Select On-Line → "Form 4868"; Practitioner → "Form 4868
  with Practitioner PIN and EFW".

## The F4868-* business-rule set (TY2026v1.0, all Active)

- **F4868-001-02** — filed after TaxPeriodEndDate and on or before the due date, UNLESS the
  line 8 or line 9 box is checked (timeliness arm 1).
- **F4868-002-01** — with line 8/9 checked: on or before the extended due date for taxpayers
  out of the country (June 15) (timeliness arm 2).
- **F4868-003-01** — SpouseSSN present → NameLine1Txt must contain an ampersand (the joint
  name rule; converse R0000-123: ampersand → SpouseSSN required).
- **F4868-007/-008/-009** — the jurat ladder above.
- **FPYMT-052-02** — **the EFW tie: IRSPayment PaymentAmt must EQUAL Form 4868
  TaxpayerIsPayingAmt (line 7)** — the 4868's analogue of the 9465's F9465-019-02.
- **FPYMT-050-01 / -051-01** — RequestedPaymentDt ≤ due date (or ≤ extended OOC due date
  when line 8/9 checked), not more than 5 days before the received date.
- **FPYMT-045/-086/-087/-088-11/-129, IND-900** (duplicate-extension reject), IND-002/-052,
  R0000-092/-093 (SSN/ITIN ranges, no ATIN), R0000-114/-115 (calendar-year period pins),
  R0000-125/-126/-127 (NameLine1 less-than-sign format), R0000-195 (no binary attachments).

**⚠ FLAGGED ANOMALY — FPYMT-088-11 in this package lists the 2026-calendar ES dates**
(04/15/2026 · 06/15/2026 · 09/15/2026 · 01/15/2027). A TY2026 4868 is filed Jan–Apr 2027
(after the 12/31/2026 period end per F4868-001), so every listed date would be >5 days
before the received date and FPYMT-086 would reject it — the published list appears to be a
stale carryover in this early drop (Rl10A Drop 1) and should be re-pulled at a later drop.
Encoded as year-keyed data, NOT hard-pinned. Do not resolve by guessing — walk item.

**⚠ VERSION SEAM (walk item):** the current published face is the **2025** revision (TY2025
extension, due 4/15/2026 — that window is already past); the local MeF package is
**TY2026v1.0** (the extension the Jan-2027 season actually files, due 4/15/2027). The spec
anchors the 2025 face verbatim (facts/lines/instructions text) with the TY2026 MeF channel
(identical structure; the six IRS4868 elements are revision-stable), and every dated
constant is year-keyed. The TY2026 face publishes ~Oct 2026 (the 2025 face was created
10/1/25) — re-verify then (the s48 face-drift class).

## Face + instructions findings (2025 revision, verbatim)

- **Purpose:** 6 more months (4 if "out of the country" and a U.S. citizen or resident) to
  file Form 1040, 1040-SR, 1040-NR, or 1040-SS. For calendar 2025: to **October 15, 2026**.
- **709 rider:** an extension of the income tax return ALSO extends Form 709/709-NA for
  2025 — but NOT the time to pay gift/GST tax (that's Form 8892). (709 is on Ken's mission
  list — this rider is the 4868↔709 seam.)
- **Qualifying trio:** (1) properly estimate 2025 tax liability using available information,
  (2) enter that estimate on line 4, (3) file by the due date. **"If we later find that the
  estimate wasn't reasonable, the extension will be null and void."**
- **Extension of time to FILE, never to PAY:** interest runs on any unpaid tax from the due
  date; late-payment penalty ½% per month (max 25%) — **reasonable-cause safe harbor: at
  least 90% of the actual tax paid by the due date through withholding/estimates/4868
  payment, AND the remainder paid with the return.**
- **Late-FILING penalty** (on the return, if filed after the extended date): 5% per month,
  max 25%; **minimum $525** (adjusted for inflation — YEAR-KEYED, TY2025 figure printed on
  the face) or 100% of the balance if smaller, when >60 days late.
- **No signature line. No reason required.** "We'll contact you only if your request is
  denied." Don't file if: you want the IRS to figure the tax, or you're under a court order
  to file by the due date.
- **Line math:** L4 = expected total tax (1040 line 24 / 1040-SS Part I line 7; zero →
  enter -0-). L5 = expected total payments (1040 line 33 **excluding Schedule 3 line 10**;
  1040-SS Part I line 12 excluding line 9); **don't include the line-7 payment on line 5.**
  L6 = L4 − L5, **"If line 5 is more than line 4, enter -0-"** (floor at zero). L7 = amount
  paying (can be less than L6 — extension still valid; pay to limit interest).
- **Credit claiming:** the 4868 payment lands on **Schedule 3, line 10** (1040/1040-SR/
  1040-NR) or 1040-SS Part I line 9. Joint 4868 → later separate returns: split in ANY
  agreed amounts. Separate 4868s → later joint return: sum both.
- **Line 8 (out of the country):** on the due date living outside the US/PR with main place
  of work outside US/PR, OR in military/naval service outside US/PR. Automatic 2 months to
  **June 15, 2026** (file+pay, no form needed); the 4868 adds 4 more → Oct 15. Eligible
  even if physically present in the US/PR on the due date. Bona-fide-residence/physical-
  presence waiters use Form 2350 instead.
- **Line 9 (1040-NR):** no wages subject to U.S. withholding → return due **June 15,
  2026**; the 4868's 6 months run from that due date (→ Dec 15, 2026 — DERIVED from the
  face's "we can't extend more than 6 months" + the June-15 due date; the face prints only
  the Oct-15-for-most parenthetical; i1040-NR states Dec 15. Walk note.)
- **Fiscal-year taxpayers MUST file a paper 4868.**
- **Estate/trust 1040-NR filers:** EIN on line 2, margin literal "estate"/"trust".
- **ITIN pending:** enter "ITIN TO BE REQUESTED"; the ITIN isn't required for the 4868
  itself.
- **The e-pay alternative (kills the form):** paying electronically (Direct Pay, EFTPS,
  card, wallet) and marking the payment "for an extension" processes the extension
  automatically — "You don't need to file Form 4868." Confirmation-number worksheet line on
  the face.
- **Rounding:** whole-dollar rounding optional but ALL-OR-NOTHING on the form (house
  convention is whole-dollar everywhere — consistent).
- **Don't attach the 4868 to the return; don't attach statements to the 4868** (penalty
  reasonable-cause statements go on the RETURN).

## The address chart (2025 face p.4 — YEAR-WATCHED; the four-way Charlotte trap)

Two columns: **with payment** (IRS P.O. box) vs **without payment** (service center).
- AL FL **GA** LA MS NC SC TN TX → **Charlotte, NC P.O. Box 1302** (28201-1302) / Austin TX
  73301-0045.
- AZ AR NM OK → Louisville KY P.O. Box 931300 (40293-1300) / Austin TX 73301-0045.
- CT DE DC IL IN IA KY ME MD MA MN MO NH NJ NY PA RI VT VA WV WI → Louisville Box 931300 /
  Kansas City MO 64999-0045.
- AK CA CO HI ID KS MI MT NE NV ND OH OR SD UT WA WY → Louisville Box 931300 / Ogden UT
  84201-0045.
- Foreign / AS / PR / §933 exclusion / APO-FPO / 2555 / 4563 / dual-status / Guam-USVI
  nonpermanent → **Charlotte Box 1303** / Austin TX 73301-0215.
- Foreign estate/trust 1040-NR → Charlotte Box 1303 / Kansas City 64999-0045.
- All other 1040-NR/1040-SS → Charlotte Box 1303 / Austin 73301-0215.

**Georgia now mails to FOUR different Charlotte/return addresses across the payment
cluster: 1040-V → Box 1214 · 1040-ES → Box 1300 · 4868-with-payment → Box 1302 · foreign
4868 → Box 1303.** The s77 three-way trap is a four-way trap. USPS-only P.O. boxes; PDS
street addresses via irs.gov/PDSStreetAddresses.

## Proposed v1 scope (the Gate-1 walk skeleton)

- **W1 — face math + qualifying:** L6 = max(0, L4−L5); L4 = expected line 24 (zero → -0-);
  L5 excludes Sch 3 L10 and the L7 payment; the reasonable-estimate null-and-void caution;
  no signature, no reason.
- **W2 — windows:** file after period end, by 4/15/2026 (F4868-001); line 8/9 → by
  6/15/2026 (F4868-002); extension to 10/15 (line 9 → 12/15 derived); fiscal-year = paper;
  disaster note; the e-pay-instead alternative.
- **W3 — the MeF channel (its OWN family):** six-element IRS4868; the no-payment-no-
  signature rule (R0000-098) + the jurat ladder; **FPYMT-052-02 line 7 == IRSPayment
  PaymentAmt (the s76 EFW tie)**; ES records 0..4; no binary attachments; IND-900
  duplicate; the joint-ampersand rule; **the FPYMT-088-11 date anomaly + the TY2026-package
  version seam (both flagged, year-keyed)**.
- **W4 — penalties + credit + addresses:** the 90% safe harbor; ½%/5%/25%/$525 (year-keyed)
  penalty facts; Sch 3 L10 credit routing + the joint/separate split rules; the four-row
  year-watched chart (GA = Charlotte Box **1302**); 709 rider.

entity_types ['1040']; print + its own MeF submission family. tts leg on approval: 4868
print render + the extension submission builder + Sch 3 L10 proforma tie + diagnostics +
FA runners/activate/mirror-refresh.
