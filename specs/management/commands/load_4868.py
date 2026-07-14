"""Load the Form 4868 spec — Application for Automatic Extension of Time To File (2025 revision).
Post-payment-cluster draft-to-gate order (tts s78; BUILD_ORDER "next NEW item: 4868 — separate MeF
family, spec-first gap check"). Greenfield (gap confirmed 404 on 2026-07-14).

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
Form 4868 buys 6 more months to FILE (never to pay) the 1040/1040-SR/1040-NR/1040-SS — to
Oct 15 for calendar-year filers — and rides its OWN MeF submission family (ReturnTypeCd
"4868": Return4868/ReturnHeader4868/ReturnData4868), NOT ReturnData1040. The tts leg is a
print render + a NEW extension submission builder (not a 1040 document slot). ReturnData4868
carries exactly: the six-element IRS4868 + the s76 IRSPayment/IRSESPayment records + (XSD-
declared but R0000-195-REJECTED) binary attachments. The paper face has NO signature line;
e-file needs a PIN ONLY when a payment record rides (R0000-098). The EFW tie is
FPYMT-052-02: IRSPayment PaymentAmt == line 7 (the 4868's F9465-019-02 analogue).

v1 SCOPE — PROPOSED (Gate-1 walk W1-W4 AWAITING KEN; see f4868_source_brief.md):
W1. Face math + qualifying: L6 = max(0, L4-L5) ("If line 5 is more than line 4, enter -0-");
    L4 = expected 1040 line 24 (zero -> enter -0-; unreasonable estimate = extension null and
    void); L5 = expected line 33 EXCLUDING Sch 3 line 10 and the L7 payment; no signature, no
    reason required.
W2. Windows: file after the tax-period end and by 4/15/2026 (F4868-001-02); line 8 (out of
    country) / line 9 (1040-NR no withheld wages) -> by 6/15/2026 (F4868-002-01); extension
    runs to 10/15/2026 (line 9 -> 12/15/2026, DERIVED: 6 months from the June-15 due date —
    the face prints only "October 15, 2026, for most"); fiscal-year taxpayers MUST paper-file;
    the e-pay-marked-extension alternative makes the form unnecessary.
W3. The MeF channel (its OWN family): six-element IRS4868; no-payment-no-signature
    (R0000-098) + the two-value jurat ladder (F4868-007/-008/-009); FPYMT-052-02 line 7 ==
    IRSPayment PaymentAmt; IRSESPayment 0..4; R0000-195 refuses binary attachments; IND-900
    duplicate-extension; F4868-003 joint-ampersand. FLAGGED: the TY2026v1.0 package's
    FPYMT-088-11 still lists the 2026-calendar ES dates (self-contradictory with FPYMT-086
    for a 2027-filed extension — stale early-drop carryover, year-keyed, re-pull later drops);
    and the version seam (2025 face / TY2026 MeF package — the Jan-2027 season vintage).
W4. Penalties + credit + addresses: the 90%-paid reasonable-cause safe harbor; late-pay 0.5%/
    late-file 5%/25% caps/$525 minimum (YEAR-KEYED, printed on the 2025 face); the payment
    lands on Schedule 3 line 10 (joint-then-separate: any agreed split; separate-then-joint:
    sum); the four-row where-to-file chart (GA with payment = Charlotte Box 1302 — the FOURTH
    Charlotte box across the payment cluster: V 1214 / ES 1300 / 4868 1302 / foreign 1303);
    the Form 709/709-NA filing rider (extends filing, never gift-tax payment — Form 8892).

CARRIED [UNVERIFIED]: none — verbatim vs Form 4868 (2025, Created 10/1/25; self-contained
form+instructions, no separate i4868; About page "None at this time" 2026-07-14) + the MeF
4868 2026v1.0 package (XSDs + business-rules PDF read directly from the local
docs/mef/schemas copy). Year-watch: every date constant, the $525 minimum penalty, the
address chart, the FPYMT-088-11 date list, and the TY2026 face when it publishes (~Oct 2026).

SAFETY GUARD — READY_TO_SEED stays False until Ken approves the Gate-1 walk (W1-W4).
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from sources.models import (
    AuthorityExcerpt, AuthorityFormLink, AuthoritySource, AuthoritySourceTopic,
    AuthorityTopic, RuleAuthorityLink,
)
from specs.models import (
    FlowAssertion, FormDiagnostic, FormFact, FormLine, FormRule, TaxForm, TestScenario,
)

READY_TO_SEED = False  # ⟨GATE 1⟩ flips only on Ken's explicit approval of the W1-W4 walk.

FORM_JURISDICTION = "federal"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1040"]

# ── Verified constants (f4868_source_brief.md; ALL dates are the TY2025 calendar — YEAR-KEYED) ──
DUE_DATE = "2026-04-15"            # F4868-001-02 window end; "April 15, 2026, for most people"
OOC_DUE_DATE = "2026-06-15"        # automatic 2-month out-of-country date; also the line-9 1040-NR due date
EXTENDED_DUE = "2026-10-15"        # "October 15, 2026, for most calendar year taxpayers" (6 months)
NR_EXTENDED_DUE = "2026-12-15"     # line 9: 6 months from the June-15 due date (DERIVED — see W2/brief)
PERIOD_END = "2025-12-31"          # F4868-001: file only AFTER the TaxPeriodEndDate
EXTENSION_MONTHS = 6               # "apply for 6 more months (4 if out of the country...)"
OOC_EXTRA_MONTHS = 4               # line 8: "an additional 4 months" on top of the automatic 2
SAFE_HARBOR_PCT = 90               # late-payment reasonable cause: >= 90% paid by the due date + rest with the return
LATE_PAY_PCT_PER_MONTH = 0.5       # "usually 1/2 of 1%... each month or part of a month" (max 25%)
LATE_FILE_PCT_PER_MONTH = 5        # return filed late: "usually 5%... each month" (max 25%)
PENALTY_MAX_PCT = 25
MIN_LATE_FILE_PENALTY = 525        # >60 days late: smaller of $525 (INFLATION-ADJUSTED, year-keyed) or the balance
CREDIT_LINE = "SCH3_10"            # "Form 1040, 1040-SR, or 1040-NR, Schedule 3, line 10" (1040-SS Part I line 9)
ES_MAX_RECORDS = 4                 # ReturnData4868: IRSESPayment maxOccurs=4
JURAT_CODES = {                    # F4868-007/-008/-009 — the ReturnHeader4868 enum has exactly these two values
    "Self-Select Practitioner": "Form 4868",
    "Self-Select On-Line": "Form 4868",
    "Practitioner": "Form 4868 with Practitioner PIN and EFW",
}
# Where-to-file chart (2025 face p.4 — YEAR-WATCHED; USPS-only P.O. boxes).
ADDR_CHARLOTTE_1302 = {"AL", "FL", "GA", "LA", "MS", "NC", "SC", "TN", "TX"}   # with payment
ADDR_LOUISVILLE = {"AZ", "AR", "NM", "OK",
                   "CT", "DE", "DC", "IL", "IN", "IA", "KY", "ME", "MD", "MA", "MN", "MO",
                   "NH", "NJ", "NY", "PA", "RI", "VT", "VA", "WV", "WI",
                   "AK", "CA", "CO", "HI", "ID", "KS", "MI", "MT", "NE", "NV", "ND", "OH",
                   "OR", "SD", "UT", "WA", "WY"}                                # with payment
ADDR_NOPAY_AUSTIN = {"AL", "FL", "GA", "LA", "MS", "NC", "SC", "TN", "TX", "AZ", "AR", "NM", "OK"}
ADDR_NOPAY_KC = {"CT", "DE", "DC", "IL", "IN", "IA", "KY", "ME", "MD", "MA", "MN", "MO",
                 "NH", "NJ", "NY", "PA", "RI", "VT", "VA", "WV", "WI"}
ADDR_NOPAY_OGDEN = {"AK", "CA", "CO", "HI", "ID", "KS", "MI", "MT", "NE", "NV", "ND", "OH",
                    "OR", "SD", "UT", "WA", "WY"}


def _balance_due(line4_tax, line5_payments) -> float:
    """Line 6 = line 4 - line 5, floored at zero: 'If line 5 is more than line 4, enter -0-'."""
    return max(0.0, float(line4_tax or 0) - float(line5_payments or 0))


def _filing_deadline(out_of_country, nr_no_wages) -> str:
    """The LAST day the 4868 itself may be filed: 4/15 normally (F4868-001-02); with the line-8 or
    line-9 box, the out-of-country June-15 date (F4868-002-01)."""
    return OOC_DUE_DATE if (out_of_country or nr_no_wages) else DUE_DATE


def _extended_due_date(out_of_country, nr_no_wages) -> str:
    """Where the extension lands: Oct 15 for calendar filers INCLUDING line 8 (automatic 2 months +
    4 more = the same Oct 15); line 9 (1040-NR due June 15) -> Dec 15, DERIVED as 6 months from the
    June-15 due date (the face prints only the Oct-15-for-most parenthetical; i1040-NR states Dec 15)."""
    if nr_no_wages and not out_of_country:
        return NR_EXTENDED_DUE
    return EXTENDED_DUE


def _filing_window_ok(filed_date, out_of_country, nr_no_wages) -> bool:
    """F4868-001-02/-002-01: after the TaxPeriodEndDate and on or before the applicable deadline.
    Dates compare as ISO strings."""
    return PERIOD_END < str(filed_date) <= _filing_deadline(out_of_country, nr_no_wages)


def _safe_harbor_met(total_tax_actual, paid_by_due_date) -> bool:
    """Late-payment reasonable cause (both prongs printed on the face; this helper tests prong 1):
    at least 90% of the ACTUAL total tax paid by the due date via withholding/estimates/4868 payment.
    Prong 2 (the remainder paid WITH the return) is a filing-time condition."""
    return float(paid_by_due_date or 0) >= (SAFE_HARBOR_PCT / 100.0) * float(total_tax_actual or 0)


def _efw_amount_consistent(line7_paying, efw_payment_amount) -> bool:
    """FPYMT-052-02: when an IRS Payment Record rides the extension, its PaymentAmt must EQUAL
    Form 4868 line 7 (TaxpayerIsPayingAmt). No record -> line 7 is the check/voucher amount."""
    if efw_payment_amount is None:
        return True
    return float(line7_paying or 0) == float(efw_payment_amount)


def _signature_required(has_payment_record) -> bool:
    """R0000-098-01: PINTypeCd + PrimarySignaturePIN are required ONLY when an IRSPayment or
    IRSESPayment record is present. A no-payment e-filed 4868 carries NO signature — matching the
    paper face, which has no signature line at all."""
    return bool(has_payment_record)


def _jurat_code(pin_type) -> str:
    """F4868-007/-008/-009: the JuratDisclosureCd a payment-carrying extension must declare, by
    PINTypeCd. The header enum has exactly two values."""
    return JURAT_CODES[pin_type]


def _joint_name_ok(name_line1, spouse_ssn) -> bool:
    """F4868-003-01: SpouseSSN present -> NameLine1Txt must contain an ampersand. Converse
    R0000-123-01: an ampersand requires the SpouseSSN."""
    has_amp = "&" in str(name_line1 or "")
    if spouse_ssn:
        return has_amp
    return not has_amp


def _mailing_address(state, making_payment, foreign_or_territory=False) -> str:
    """The 2025 chart (p.4), YEAR-WATCHED. Returns a short routing key; the tts print leg renders
    the full address block. Foreign/AS/PR/933/APO-FPO/2555/4563/dual-status -> the Charlotte 1303 /
    Austin 0215 row regardless of state."""
    if foreign_or_territory:
        return "CHARLOTTE_1303" if making_payment else "AUSTIN_0215"
    st = str(state or "").upper()
    if making_payment:
        if st in ADDR_CHARLOTTE_1302:
            return "CHARLOTTE_1302"
        if st in ADDR_LOUISVILLE:
            return "LOUISVILLE_931300"
        return "CHARLOTTE_1303"
    if st in ADDR_NOPAY_AUSTIN:
        return "AUSTIN_0045"
    if st in ADDR_NOPAY_KC:
        return "KANSAS_CITY_0045"
    if st in ADDR_NOPAY_OGDEN:
        return "OGDEN_0045"
    return "AUSTIN_0215"


AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("ext_4868", "Form 4868 automatic extension: file-not-pay, L6 floor math, the OOC/1040-NR "
     "windows, the own-family MeF channel (no-payment-no-signature; FPYMT-052-02 EFW tie), the "
     "90% safe harbor, Sch 3 L10 credit routing, year-watched addresses."),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_F4868", "source_type": "federal_form", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Form 4868 (2025) — Application for Automatic Extension of Time To File",
        "citation": "Form 4868 (2025), Cat. No. 13141W, OMB 1545-0074 (self-contained form + instructions; Created 10/1/25; About page 'None at this time' 2026-07-14)",
        "issuer": "Internal Revenue Service", "official_url": "https://www.irs.gov/pub/irs-pdf/f4868.pdf",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.5, "topics": ["ext_4868"],
        "excerpts": [{
            "excerpt_label": "Purpose / qualifying / file-not-pay (2025 face verbatim)",
            "excerpt_text": (
                "Use Form 4868 to apply for 6 more months (4 if 'out of the country' ... and a U.S. citizen "
                "or resident) to file Form 1040, 1040-SR, 1040-NR, or 1040-SS. Gift and generation-skipping "
                "transfer (GST) tax return (Form 709 or 709-NA): an extension of time to file your 2025 "
                "calendar year income tax return also extends the time to file Form 709 or 709-NA for 2025. "
                "However, it doesn't extend the time to pay any gift and GST tax you may owe for 2025. To "
                "make a payment of gift and GST tax, see Form 8892. Qualifying for the Extension: to get the "
                "extra time, you must: 1. Properly estimate your 2025 tax liability using the information "
                "available to you, 2. Enter your total tax liability on line 4 of Form 4868, and 3. File Form "
                "4868 by the due date of your return. CAUTION: although you aren't required to make a payment "
                "of the tax you estimate as due, Form 4868 doesn't extend the time to pay taxes. If you don't "
                "pay the amount due by the due date, you'll owe interest. You may also be charged penalties. "
                "Any remittance you make with your application for extension will be treated as a payment of "
                "tax. You don't have to explain why you're asking for the extension. We'll contact you only "
                "if your request is denied. Don't file Form 4868 if you want the IRS to figure your tax or "
                "you're under a court order to file your return by the due date. Filing Your Tax Return: you "
                "can file your tax return any time before the extension expires. Don't attach a copy of Form "
                "4868 to your return. Note: if you're a fiscal year taxpayer, you must file a paper Form 4868."
            ),
            "summary_text": "6 months to FILE (4 more if out-of-country), never to pay; the qualifying trio (proper estimate, line 4, filed by the due date); the 709/709-NA filing rider (payment = Form 8892); no reason needed; IRS-figures-tax and court-order bars; fiscal-year = paper only; don't attach to the return.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "Line instructions 4-9 + rounding (2025 face verbatim)",
            "excerpt_text": (
                "Line 4: enter the total tax liability you expect to report on your 2025 Form 1040, 1040-SR, "
                "or 1040-NR, line 24; or Form 1040-SS, Part I, line 7. If you expect this amount to be zero, "
                "enter -0-. CAUTION: make your estimate as accurate as you can with the information you have. "
                "If we later find that the estimate wasn't reasonable, the extension will be null and void. "
                "Line 5: enter the total payments you expect to report on your 2025 Form 1040, 1040-SR, or "
                "1040-NR, line 33 (excluding Schedule 3, line 10); or Form 1040-SS, Part I, line 12 "
                "(excluding Part I, line 9). CAUTION: don't include on line 5 the amount you're paying with "
                "this Form 4868. Line 6: subtract line 5 from line 4. If line 5 is more than line 4, enter "
                "-0-. Line 7: if you find you can't pay the amount shown on line 6, you can still get the "
                "extension. But you should pay as much as you can to limit the amount of interest you'll owe. "
                "Line 8: if you're out of the country on the due date of your return, check the box on line "
                "8. Line 9: if you didn't receive wages subject to U.S. income tax withholding, and your "
                "return is due June 15, 2026, check the box on line 9. Rounding off to whole dollars: you can "
                "round off cents to whole dollars on Form 4868. If you do round to whole dollars, you must "
                "round all amounts. If you're filing Form 1040-NR as an estate or trust, enter your employer "
                "identification number (EIN) instead of an SSN on line 2. In the left margin, next to the "
                "EIN, write 'estate' or 'trust.' If you don't have an ITIN, enter 'ITIN TO BE REQUESTED' "
                "wherever an SSN is requested."
            ),
            "summary_text": "L4 = expected 1040 line 24 (zero -> -0-; unreasonable estimate voids the extension); L5 = expected line 33 EXCLUDING Sch 3 L10 and the L7 payment; L6 = L4-L5 floored at -0-; L7 may be less than L6; L8/L9 checkbox arms; all-or-nothing rounding; estate/trust EIN margin literal; ITIN TO BE REQUESTED.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "Windows: when to file / out of the country / 1040-NR / total time (2025 face verbatim)",
            "excerpt_text": (
                "File Form 4868 by the due date of your Form 1040, 1040-SR, 1040-NR, or 1040-SS. For a 2025 "
                "calendar year return, this is April 15, 2026, for most people. Fiscal year taxpayers file "
                "Form 4868 by the due date of the fiscal year return. Taxpayers who are out of the country: "
                "if, on the due date of your return, you're out of the country (as defined below) and a U.S. "
                "citizen or resident, you're allowed 2 extra months to file your return and pay any amount "
                "due without requesting an extension. Interest will still be charged... If you're out of the "
                "country and file a calendar year income tax return, you can pay the tax and file your return "
                "or this form by June 15, 2026. File this form and be sure to check the box on line 8 if you "
                "need an additional 4 months to file your return. You're out of the country if: you live "
                "outside the United States and Puerto Rico and your main place of work is outside the United "
                "States and Puerto Rico, or you're in military or naval service on duty outside the United "
                "States and Puerto Rico. If you qualify as being out of the country, you'll still be eligible "
                "for the extension even if you're physically present in the United States or Puerto Rico on "
                "the due date of the return. [Bona fide residence / physical presence waiters: file Form 2350 "
                "instead.] Form 1040-NR filers: if you didn't receive wages as an employee subject to U.S. "
                "income tax withholding, and your return is due June 15, 2026, check the box on line 9. Total "
                "Time Allowed: generally, we can't extend the due date of your return for more than 6 months "
                "(October 15, 2026, for most calendar year taxpayers). However, there may be an exception if "
                "you're living out of the country."
            ),
            "summary_text": "Window: by 4/15/2026 (fiscal filers by their own due date, paper only); out-of-country = automatic 2 months (6/15, pay+file), line 8 adds 4 more; the two-bullet OOC definition (physical presence on the due date doesn't disqualify); 2350 for the FEIE-test waiters; line 9 NR June-15 due date; 6-month cap (Oct 15 for most).",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "Penalties + the 90% safe harbor + credit claiming (2025 face verbatim)",
            "excerpt_text": (
                "Interest: you'll owe interest on any tax not paid by the due date of your return, even if "
                "you qualify for the 2-month extension because you were out of the country... Late Payment "
                "Penalty: usually 1/2 of 1% of any tax (other than estimated tax) not paid by the due date of "
                "your return, which is April 15, 2026, for most people. It's charged for each month or part "
                "of a month the tax is unpaid. The maximum penalty is 25%. You're considered to have "
                "reasonable cause for the period covered by this automatic extension if both of the following "
                "requirements have been met: 1. At least 90% of the total tax on your 2025 return is paid on "
                "or before the due date of your return through withholding, estimated tax payments, or "
                "payments made with Form 4868. 2. The remaining balance is paid with your return. Late Filing "
                "Penalty: usually charged if your return is filed after the due date (including extensions)... "
                "usually 5% of the amount due for each month or part of a month your return is late. The "
                "maximum penalty is 25%. If your return is more than 60 days late, the minimum penalty is "
                "$525 (adjusted for inflation) or the balance of the tax due on your return, whichever is "
                "smaller. How To Claim Credit for Payment Made With This Form: when you file your 2025 "
                "return, include the amount of any payment you made with Form 4868 on the appropriate line... "
                "Form 1040, 1040-SR, or 1040-NR, Schedule 3, line 10; Form 1040-SS, Part I, line 9. If you "
                "and your spouse each filed a separate Form 4868 but later file a joint return for 2025, "
                "enter the total paid with both Forms 4868 on the appropriate line of your joint return. If "
                "you and your spouse jointly file Form 4868 but later file separate returns for 2025, you can "
                "enter the total amount paid with Form 4868 on either of your separate returns. Or you and "
                "your spouse can divide the payment in any agreed amounts."
            ),
            "summary_text": "Interest always runs from 4/15; late-pay 0.5%/month max 25% with the two-prong reasonable-cause safe harbor (>= 90% paid by the due date + remainder with the return); late-file 5%/month max 25%, >60-days minimum = smaller of $525 (inflation-adjusted, YEAR-KEYED) or the balance; credit lands on Sch 3 line 10 (1040-SS Part I line 9); joint/separate split rules both directions.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "E-pay alternative + where-to-file chart (2025 face verbatim substance)",
            "excerpt_text": (
                "You don't need to file Form 4868 if you make a payment using our electronic payment options. "
                "The IRS will automatically process an extension of time to file when you pay part or all of "
                "your estimated income tax electronically. [Direct Pay, EFTPS, debit/credit card, digital "
                "wallet; enter the confirmation number on the worksheet line.] Note: if you use an electronic "
                "payment method and indicate the payment is for an extension, you don't have to file Form "
                "4868. Where To File a Paper Form 4868 (2025 chart): making a payment -> Internal Revenue "
                "Service: AL FL GA LA MS NC SC TN TX -> P.O. Box 1302, Charlotte, NC 28201-1302; AZ AR NM OK "
                "and CT DE DC IL IN IA KY ME MD MA MN MO NH NJ NY PA RI VT VA WV WI and AK CA CO HI ID KS MI "
                "MT NE NV ND OH OR SD UT WA WY -> P.O. Box 931300, Louisville, KY 40293-1300. Not making a "
                "payment -> Department of the Treasury, Internal Revenue Service Center: the southern row -> "
                "Austin, TX 73301-0045; the AZ/AR/NM/OK row -> Austin, TX 73301-0045; the northeastern row -> "
                "Kansas City, MO 64999-0045; the western row -> Ogden, UT 84201-0045. A foreign country, "
                "American Samoa, or Puerto Rico, or excluding income under section 933, or APO/FPO, or Form "
                "2555 or 4563, or dual-status alien, or nonpermanent resident of Guam or the U.S. Virgin "
                "Islands -> P.O. Box 1303, Charlotte, NC 28201-1303 USA / Austin, TX 73301-0215 USA. All "
                "foreign estate and trust Form 1040-NR filers -> Charlotte 1303 / Kansas City, MO 64999-0045 "
                "USA. All other Form 1040-NR and 1040-SS filers -> Charlotte 1303 / Austin, TX 73301-0215 "
                "USA. Private delivery services can't deliver items to P.O. boxes. You must use the U.S. "
                "Postal Service to mail any item to an IRS P.O. box address."
            ),
            "summary_text": "An electronic payment marked 'for an extension' IS the extension (no form needed; keep the confirmation number). The four-row year-watched chart: GA-with-payment = Charlotte Box 1302 (the FOURTH Charlotte box in the payment cluster: V 1214 / ES 1300 / 4868 1302 / foreign 1303); no-payment routes to Austin/KC/Ogden; USPS-only P.O. boxes.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "MEF_4868_PKG", "source_type": "official_guidance", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "MeF 4868 package 2026v1.0 — schemas + business rules (its own submission family)",
        "citation": "4868_2026v1.0.zip (Rl10A Drop 1, released May 28 2026; rules PDF 05-07-2026) — local copy docs/mef/schemas/2026v1.0/",
        "issuer": "Internal Revenue Service",
        "official_url": "https://www.irs.gov/e-file-providers/modernized-e-file-mef-schemas-and-business-rules",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.0, "topics": ["ext_4868"],
        "excerpts": [{
            "excerpt_label": "ReturnData4868 + IRS4868 structure (2026v1.0 XSD verbatim substance)",
            "excerpt_text": (
                "Form 4868 is its OWN MeF submission type: ReturnHeader4868 ReturnTypeCd enumerates exactly "
                "'4868'; Return4868.xsd / ReturnData4868.xsd are Extensions-family schemas, not "
                "IndividualIncomeTax. ReturnData content model: IRS4868 (required) + IRSPayment "
                "(0..unbounded; FPYMT-129 limits to one) + IRSESPayment (0..4) + BinaryAttachment/"
                "GeneralDependencySmall (declared, but R0000-195 Active: 'Submission must not contain a "
                "Binary Attachment'). IRS4868Type elements (all optional in schema): TotalTaxLiabilityAmt "
                "(LineNumber 4), TotalPaymentsAmt (5), BalanceDueAmt (6), TaxpayerIsPayingAmt (7), "
                "TaxpayerAbroadInd (8, CheckboxType), NonresWithNoWagesSubjToWhInd (9, CheckboxType). "
                "ReturnHeader4868: Filer block (PrimarySSN + PrimaryNameControlTxt required; SpouseSSN/"
                "SpouseNameControlTxt optional; USAddress|ForeignAddress choice; InCareOfNm); ALL signature "
                "groups minOccurs=0 (SelfSelectPINGrp, PractitionerPINGrp, PINTypeCd, JuratDisclosureCd — "
                "enum exactly 'Form 4868' and 'Form 4868 with Practitioner PIN and EFW' — signature "
                "PINs/dates). The paper face correspondingly has NO signature line."
            ),
            "summary_text": "A separate submission family (ReturnTypeCd '4868'): six-element IRS4868 + the s76 IRSPayment/IRSESPayment(0..4); binary attachments schema-declared but rule-rejected; every header signature element optional — the signature story is rule-driven, not schema-driven.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "F4868-* + payment/signature rules (TY2026v1.0 rules PDF verbatim substance, Active only)",
            "excerpt_text": (
                "F4868-001-02: Form 4868 can only be filed after the 'TaxPeriodEndDate' in the IRS Submission "
                "Manifest and on or before the due date to which the extension applies, unless Line 8 "
                "checkbox or Line 9 checkbox is checked. F4868-002-01: if Line 8 or Line 9 is checked, then "
                "the form can only be filed after 'TaxPeriodEndDate' and on or before the extended due date "
                "for taxpayers out of the country. F4868-003-01: if 'SpouseSSN' has a value, then "
                "'NameLine1Txt' must contain an ampersand (converse R0000-123-01: ampersand -> SpouseSSN "
                "required). F4868-007-01/-009-01: payment record present + PINTypeCd 'Self-Select "
                "Practitioner'/'Self-Select On-Line' -> JuratDisclosureCd must be 'Form 4868'. F4868-008-01: "
                "payment record + PINTypeCd 'Practitioner' -> 'Form 4868 with Practitioner PIN and EFW'. "
                "R0000-098-01: if IRS Payment Record or IRS ES Payment Record is present, then 'PINTypeCd' "
                "and 'PrimarySignaturePIN' must have a value (R0000-099-01 adds the spouse when SpouseSSN "
                "present; the per-PIN-type ladders are R0000-670/-671/-681/-682/-697/-698). FPYMT-052-02: if "
                "IRS Payment Record is present, then 'PaymentAmt' in the IRS Payment Record must be equal to "
                "Form 4868, 'TaxpayerIsPayingAmt'. FPYMT-050-01/-051-01: 'RequestedPaymentDt' on or before "
                "the (extended, when Line 8/9) due date and not more than 5 days prior to the received date. "
                "FPYMT-045-02: ES due dates unique per return. FPYMT-086/-087: ES date within [received-5d, "
                "received+1yr]. FPYMT-088-11 AS PUBLISHED in this package: ES date must be 04/15/2026 or "
                "06/15/2026 or 09/15/2026 or 01/15/2027 — FLAGGED: those are the 2026-calendar dates; a "
                "TY2026 extension files Jan-Apr 2027 (after the 12/31/2026 period end), where every listed "
                "date would trip FPYMT-086 — a stale early-drop carryover; year-keyed, re-pull later drops. "
                "IND-900: Primary SSN must not equal the Primary SSN of any previously accepted extension. "
                "R0000-195: no binary attachments. FPYMT-057-03: PaymentAmt <= 99,999,999. FPYMT-129: at "
                "most one IRSPayment."
            ),
            "summary_text": "The full Active gate: the two timeliness arms; the joint-ampersand rule; the payment-triggered signature/jurat ladder (R0000-098 + F4868-007/8/9); the EFW tie FPYMT-052-02 (PaymentAmt == line 7); payment-date windows; the FLAGGED stale FPYMT-088-11 ES-date list; duplicate-extension IND-900; the binary-attachment refusal.",
            "is_key_excerpt": True,
        }],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_F4868", "4868", "governs"), ("MEF_4868_PKG", "4868", "governs"),
]


F4868_FACTS: list[dict] = [
    {"fact_key": "name_line", "label": "L1 — name(s); joint = both spouses in return order (agent: include agent's name + address)", "data_type": "string", "required": False, "sort_order": 1},
    {"fact_key": "address_block", "label": "L1 — address (correspondence address if different; 8822 actually changes the record)", "data_type": "string", "required": False, "sort_order": 2},
    {"fact_key": "primary_ssn", "label": "L2 — your SSN (estate/trust 1040-NR: EIN + margin 'estate'/'trust'; no ITIN -> 'ITIN TO BE REQUESTED')", "data_type": "string", "required": False, "sort_order": 3},
    {"fact_key": "spouse_ssn", "label": "L3 — spouse's SSN (joint 4868; e-file: name line must carry an ampersand, F4868-003)", "data_type": "string", "required": False, "sort_order": 4},
    {"fact_key": "estimated_total_tax", "label": "L4 — estimate of total 2025 tax liability (expected 1040 line 24 / 1040-SS Part I line 7; zero -> -0-)", "data_type": "decimal", "required": False, "sort_order": 5},
    {"fact_key": "estimated_payments", "label": "L5 — total 2025 payments (expected line 33 EXCLUDING Sch 3 line 10; never includes the L7 payment)", "data_type": "decimal", "required": False, "sort_order": 6},
    {"fact_key": "amount_paying", "label": "L7 — amount you're paying with the extension (may be less than L6; extension still valid)", "data_type": "decimal", "required": False, "sort_order": 7},
    {"fact_key": "out_of_country", "label": "L8 — 'out of the country' checkbox (US citizen/resident; the two-bullet definition)", "data_type": "boolean", "required": False, "sort_order": 8},
    {"fact_key": "nr_no_wages", "label": "L9 — 1040-NR with no wages subject to US withholding (return due June 15)", "data_type": "boolean", "required": False, "sort_order": 9},
    {"fact_key": "fiscal_year_begin", "label": "Header — fiscal year beginning (fiscal filers MUST paper-file)", "data_type": "date", "required": False, "sort_order": 10},
    {"fact_key": "fiscal_year_end", "label": "Header — fiscal year ending", "data_type": "date", "required": False, "sort_order": 11},
    {"fact_key": "filed_date", "label": "Context — the date the 4868 is filed/transmitted (drives the F4868-001/-002 window)", "data_type": "date", "required": False, "sort_order": 12},
    {"fact_key": "efw_payment_amount", "label": "Context — the s76 IRSPayment record amount riding the extension (must == L7, FPYMT-052-02)", "data_type": "decimal", "required": False, "sort_order": 13},
    {"fact_key": "es_debit_quarters", "label": "Context — scheduled IRSESPayment records (0..4; dates year-keyed, see the FPYMT-088-11 flag)", "data_type": "string", "required": False, "sort_order": 14},
    {"fact_key": "pin_type", "label": "Context — e-file PINTypeCd (Practitioner / Self-Select Practitioner / Self-Select On-Line); required only with a payment record", "data_type": "string", "required": False, "sort_order": 15},
    {"fact_key": "epay_confirmation", "label": "Worksheet — electronic-payment confirmation number (an e-payment marked 'extension' REPLACES the form)", "data_type": "string", "required": False, "sort_order": 16},
    {"fact_key": "mailing_state", "label": "Context — state of residence (drives the paper where-to-file chart; year-watched)", "data_type": "string", "required": False, "sort_order": 17},
    {"fact_key": "foreign_or_territory", "label": "Context — foreign/AS/PR/933/APO-FPO/2555/4563/dual-status/Guam-USVI-nonpermanent (the Charlotte-1303 row)", "data_type": "boolean", "required": False, "sort_order": 18},
]

F4868_RULES: list[dict] = [
    {"rule_id": "R-4868-QUAL", "title": "Qualifying trio; extension of time to FILE only", "rule_type": "routing",
     "formula": "Extension granted iff: (1) 2025 liability properly estimated from available information, (2) the estimate entered on L4, (3) filed by the due date. UNREASONABLE estimate -> extension null and void. Extends FILING 6 months (Oct 15) — NEVER payment: interest from the due date always; penalties possible. No signature line, no reason required; denial-only contact. BARS: IRS-figures-your-tax; court-ordered filing date. Don't attach the 4868 to the return. Form 709/709-NA FILING rides the extension (gift/GST payment does NOT — Form 8892)",
     "inputs": ["estimated_total_tax", "filed_date"], "outputs": ["extension_valid"], "sort_order": 1,
     "description": "W1/W4. The face's Qualifying for the Extension trio + the file-not-pay caution + the 709 rider (the 4868<->709 seam for Ken's 709 mission lane)."},
    {"rule_id": "R-4868-CALC", "title": "Face math: L6 = L4 - L5 floored at -0-", "rule_type": "calculation",
     "formula": "L6 = max(0, L4 - L5). L4 = expected 1040 line 24 (1040-SS Part I line 7); expect zero -> enter -0-. L5 = expected 1040 line 33 EXCLUDING Schedule 3 line 10 (1040-SS Part I line 12 excluding line 9); NEVER includes the L7 payment. Whole-dollar rounding optional but all-or-nothing (house convention: whole-dollar)",
     "inputs": ["estimated_total_tax", "estimated_payments"], "outputs": ["balance_due"], "sort_order": 2,
     "description": "W1. The only arithmetic on the face. The L5 exclusion exists because Sch 3 line 10 IS the 4868 payment — including it would double-count."},
    {"rule_id": "R-4868-PAY", "title": "L7 partial payment allowed; the EFW tie", "rule_type": "reconciliation",
     "formula": "L7 may be ANY amount 0..L6+ ('if you find you can't pay the amount shown on line 6, you can still get the extension'). EFW: when an IRSPayment record rides the extension, PaymentAmt MUST EQUAL L7 (FPYMT-052-02); RequestedPaymentDt <= the applicable due date and >= received-date-minus-5-days (FPYMT-050/-051). At most one IRSPayment (FPYMT-129); IRSESPayment 0..4 (dates year-keyed — the FPYMT-088-11 flag)",
     "inputs": ["amount_paying", "efw_payment_amount"], "outputs": ["efw_consistent"], "sort_order": 3,
     "description": "W3. The 4868's analogue of the 9465's F9465-019-02: one payment story across the face and the payment record."},
    {"rule_id": "R-4868-WINDOW", "title": "Filing windows (F4868-001/-002)", "rule_type": "validation",
     "formula": "File AFTER the TaxPeriodEndDate (12/31/2025) and: no boxes -> on or before 4/15/2026; line 8 OR line 9 checked -> on or before 6/15/2026 (the out-of-country extended date). Fiscal-year filers: by the fiscal due date, PAPER ONLY. Disaster relief may extend (irs.gov/DisasterRelief). Dates YEAR-KEYED",
     "inputs": ["filed_date", "out_of_country", "nr_no_wages", "fiscal_year_begin"], "outputs": ["window_ok"], "sort_order": 4,
     "description": "W2. Both MeF timeliness arms verbatim; the fiscal-year paper bar is the face's own Note."},
    {"rule_id": "R-4868-EXTENT", "title": "Where the extension lands (Oct 15 / Dec 15)", "rule_type": "calculation",
     "formula": "Calendar filers: to 10/15/2026 (6 months — 'generally, we can't extend the due date of your return for more than 6 months'). Line 8: the automatic 2 months (6/15) + 4 more via this form = the SAME 10/15. Line 9 (1040-NR due 6/15): 6 months from the June-15 due date -> 12/15/2026 [DERIVED — the face prints only 'October 15, 2026, for most']. Return may be filed ANY time before the extension expires",
     "inputs": ["out_of_country", "nr_no_wages"], "outputs": ["extended_due_date"], "sort_order": 5,
     "description": "W2. The Dec-15 arm is arithmetic on the face's own 6-month cap + the line-9 June-15 due date (i1040-NR states it explicitly); flagged in the walk as the one derived (not printed) date."},
    {"rule_id": "R-4868-OOC", "title": "Out of the country: definition + the automatic 2 months", "rule_type": "routing",
     "formula": "'Out of the country' = (a) live outside US+PR AND main place of work outside US+PR, or (b) military/naval service on duty outside US+PR. On the due date + US citizen/resident -> AUTOMATIC 2 extra months to file AND pay (6/15/2026, no form) — interest still runs from 4/15. Line 8 = the +4-months request on top. Physical presence in the US/PR on the due date does NOT disqualify. Expecting to MEET bona-fide-residence/physical-presence later -> Form 2350 instead (FEIE waiters)",
     "inputs": ["out_of_country"], "outputs": ["ooc_qualifies"], "sort_order": 6,
     "description": "W2. The two-bullet definition verbatim; the automatic-2-months arm exists WITHOUT the 4868 (Pub 54 territory) — the form only adds the 4."},
    {"rule_id": "R-4868-SIGN", "title": "The signature story: payment-triggered only", "rule_type": "validation",
     "formula": "Paper 4868: NO signature line exists. E-file with NO payment records: NO PIN required (all header signature groups optional). E-file WITH IRSPayment/IRSESPayment: PINTypeCd + PrimarySignaturePIN required (R0000-098; spouse adds R0000-099); jurat by PIN type (F4868-007/-008/-009): Self-Select Practitioner / Self-Select On-Line -> 'Form 4868'; Practitioner -> 'Form 4868 with Practitioner PIN and EFW'. Joint e-file: SpouseSSN <-> ampersand in NameLine1 (F4868-003 / R0000-123)",
     "inputs": ["efw_payment_amount", "pin_type", "spouse_ssn", "name_line"], "outputs": ["signature_required", "jurat_code"], "sort_order": 7,
     "description": "W3. The behavioral surprise: an extension without money moves with no signature at all; the moment a debit rides, the full PIN ladder applies."},
    {"rule_id": "R-4868-PEN", "title": "Penalties + the 90% safe harbor (year-keyed $525)", "rule_type": "calculation",
     "formula": "Interest: always, on tax unpaid after 4/15 (even OOC). Late-PAYMENT penalty 0.5%/month (part-months count) max 25% — REASONABLE CAUSE (no penalty) iff BOTH: >= 90% of the ACTUAL 2025 tax paid by the due date (withholding + estimates + the 4868 payment) AND the remainder paid WITH the return. Late-FILING penalty (return after the extended date) 5%/month max 25%; > 60 days late -> minimum = smaller of $525 (inflation-adjusted, YEAR-KEYED TY2025) or 100% of the balance. Penalty statements attach to the RETURN, never the 4868",
     "inputs": ["estimated_total_tax", "estimated_payments", "amount_paying"], "outputs": ["safe_harbor_met"], "sort_order": 8,
     "description": "W4. The two-prong safe harbor verbatim; the $525 minimum is printed on the 2025 face and moves with inflation."},
    {"rule_id": "R-4868-CREDIT", "title": "Credit routing: Schedule 3 line 10 + the joint/separate splits", "rule_type": "reconciliation",
     "formula": "The L7 payment is claimed on the 2025 return: 1040/1040-SR/1040-NR Schedule 3 line 10; 1040-SS Part I line 9. Separate 4868s -> later JOINT return: enter the TOTAL of both. Joint 4868 -> later SEPARATE returns: either return may claim the total, or divide in ANY agreed amounts. (tts: the proforma/carry tie — the extension payment must land on Sch 3 L10 of the season return)",
     "inputs": ["amount_paying"], "outputs": ["sch3_line10_credit"], "sort_order": 9,
     "description": "W4. The cross-form tie the tts leg wires: 4868 L7 -> Sch 3 L10 (YELLOW derive on the return side)."},
    {"rule_id": "R-4868-EFILE", "title": "The MeF channel: its OWN submission family", "rule_type": "validation",
     "formula": "ReturnTypeCd '4868' — a SEPARATE family (Return4868/ReturnHeader4868/ReturnData4868), NOT a ReturnData1040 document: the tts leg builds a new extension submission, not a 1040 slot. ReturnData = IRS4868 (6 elements: L4/L5/L6/L7/L8/L9) + <=1 IRSPayment + <=4 IRSESPayment. REFUSALS: binary attachments (R0000-195, despite the XSD declaring them); duplicate extension per SSN (IND-900); fiscal-year (paper-only per the face). E-PAY ALTERNATIVE: an electronic payment marked 'for an extension' processes the extension with NO form filed (keep the confirmation number). VERSION SEAM: 2025 face / TY2026v1.0 package (the Jan-2027 season vintage) — the FPYMT-088-11 ES-date list in this drop is stale (flagged), re-pull later drops",
     "inputs": ["efw_payment_amount", "es_debit_quarters", "fiscal_year_begin"], "outputs": ["efile_route"], "sort_order": 10,
     "description": "W3. The structural headline: a new submission family. Refusal beats fabrication on every flagged seam."},
    {"rule_id": "R-4868-FILE", "title": "Paper where-to-file (the four-way Charlotte trap; year-watched)", "rule_type": "routing",
     "formula": "WITH payment: AL FL GA LA MS NC SC TN TX -> Charlotte NC Box 1302 (28201-1302); all other states -> Louisville KY Box 931300 (40293-1300). WITHOUT payment: southern + AZ/AR/NM/OK rows -> Austin 73301-0045; northeastern row -> Kansas City 64999-0045; western row -> Ogden 84201-0045. Foreign/AS/PR/933/APO-FPO/2555/4563/dual-status/Guam-USVI-nonpermanent -> Charlotte Box 1303 / Austin 73301-0215 (foreign estate-trust 1040-NR -> KC; other NR/SS -> Austin 0215). USPS ONLY to P.O. boxes (PDS -> street addresses). GA now spans FOUR cluster addresses: V 1214 / ES 1300 / 4868 1302 / foreign 1303. YEAR-WATCHED",
     "inputs": ["mailing_state", "amount_paying", "foreign_or_territory"], "outputs": ["mailing_address"], "sort_order": 11,
     "description": "W4. The s77 three-way voucher trap grows a fourth arm; both rosters are constants and the harness pins the GA divergence."},
]

F4868_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-4868-QUAL", "IRS_F4868", "primary", "Qualifying trio + file-not-pay caution + the 709 rider"),
    ("R-4868-CALC", "IRS_F4868", "primary", "Line 4/5/6 instructions incl. the Sch-3-L10 exclusion and the -0- floor"),
    ("R-4868-PAY", "IRS_F4868", "primary", "Line 7 partial-payment text"),
    ("R-4868-PAY", "MEF_4868_PKG", "primary", "FPYMT-052-02 equality + FPYMT-050/-051 date windows"),
    ("R-4868-WINDOW", "IRS_F4868", "primary", "When To File + the fiscal-year paper Note"),
    ("R-4868-WINDOW", "MEF_4868_PKG", "primary", "F4868-001-02 / F4868-002-01 timeliness arms"),
    ("R-4868-EXTENT", "IRS_F4868", "primary", "Total Time Allowed (6-month cap; Oct-15-for-most)"),
    ("R-4868-OOC", "IRS_F4868", "primary", "The two-bullet out-of-country definition + automatic 2 months"),
    ("R-4868-SIGN", "MEF_4868_PKG", "primary", "R0000-098/-099 + F4868-003/-007/-008/-009 + the all-optional header groups"),
    ("R-4868-PEN", "IRS_F4868", "primary", "Interest / late-payment / late-filing paragraphs + the 90% safe harbor"),
    ("R-4868-CREDIT", "IRS_F4868", "primary", "How To Claim Credit + both joint/separate split rules"),
    ("R-4868-EFILE", "MEF_4868_PKG", "primary", "The own-family XSD structure + R0000-195 + IND-900"),
    ("R-4868-EFILE", "IRS_F4868", "secondary", "Pay Electronically / e-pay-marked-extension alternative"),
    ("R-4868-FILE", "IRS_F4868", "primary", "The p.4 chart verbatim + the USPS-only P.O.-box caution"),
]

F4868_LINES: list[dict] = [
    {"line_number": "L1", "description": "L1 — name(s) + address (joint = return order; agent/correspondence rules)", "line_type": "input", "source_facts": ["name_line", "address_block"], "sort_order": 1},
    {"line_number": "L2", "description": "L2 — your SSN (estate/trust 1040-NR: EIN + margin literal)", "line_type": "input", "source_facts": ["primary_ssn"], "sort_order": 2},
    {"line_number": "L3", "description": "L3 — spouse's SSN (joint; e-file ampersand rule F4868-003)", "line_type": "input", "source_facts": ["spouse_ssn"], "sort_order": 3},
    {"line_number": "L4", "description": "L4 — estimate of total 2025 tax liability (expected 1040 line 24; zero -> -0-)", "line_type": "input", "source_facts": ["estimated_total_tax"], "source_rules": ["R-4868-CALC"], "sort_order": 4},
    {"line_number": "L5", "description": "L5 — total 2025 payments (line 33 excl. Sch 3 L10; never the L7 payment)", "line_type": "input", "source_facts": ["estimated_payments"], "source_rules": ["R-4868-CALC"], "sort_order": 5},
    {"line_number": "L6", "description": "L6 — balance due: L4 - L5, floored at -0-", "line_type": "calculated", "source_rules": ["R-4868-CALC"], "sort_order": 6},
    {"line_number": "L7", "description": "L7 — amount you're paying (== the IRSPayment amount when EFW rides, FPYMT-052-02)", "line_type": "input", "source_facts": ["amount_paying"], "source_rules": ["R-4868-PAY"], "sort_order": 7},
    {"line_number": "L8", "description": "L8 — out-of-country checkbox (US citizen/resident)", "line_type": "input", "source_facts": ["out_of_country"], "source_rules": ["R-4868-OOC"], "sort_order": 8},
    {"line_number": "L9", "description": "L9 — 1040-NR no-withheld-wages checkbox (June-15 due date)", "line_type": "input", "source_facts": ["nr_no_wages"], "sort_order": 9},
    {"line_number": "HDR_FY", "description": "Header — fiscal-year begin/end (fiscal filers = paper only)", "line_type": "input", "source_facts": ["fiscal_year_begin", "fiscal_year_end"], "sort_order": 10},
    {"line_number": "WKS_CONFIRM", "description": "Worksheet — e-payment confirmation number (the no-form extension path)", "line_type": "input", "source_facts": ["epay_confirmation"], "sort_order": 11},
    {"line_number": "CALC_WINDOW", "description": "Computed filing window (F4868-001/-002; deadline by box state)", "line_type": "calculated", "source_rules": ["R-4868-WINDOW"], "sort_order": 12},
    {"line_number": "CALC_EXTDUE", "description": "Computed extended due date (10/15; line-9 12/15 derived)", "line_type": "calculated", "source_rules": ["R-4868-EXTENT"], "sort_order": 13},
    {"line_number": "CALC_SIGN", "description": "Computed signature/jurat requirement (payment-triggered)", "line_type": "calculated", "source_rules": ["R-4868-SIGN"], "sort_order": 14},
    {"line_number": "CALC_HARBOR", "description": "Computed 90% safe-harbor status (late-payment reasonable cause)", "line_type": "calculated", "source_rules": ["R-4868-PEN"], "sort_order": 15},
    {"line_number": "CALC_CREDIT", "description": "Computed Sch 3 L10 credit carry (the season-return tie)", "line_type": "calculated", "source_rules": ["R-4868-CREDIT"], "sort_order": 16},
    {"line_number": "CALC_ROUTE", "description": "Computed paper mailing address (four-row chart; year-watched)", "line_type": "calculated", "source_rules": ["R-4868-FILE"], "sort_order": 17},
]

F4868_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_4868_LATE", "title": "Filed after the deadline — extension invalid", "severity": "error",
     "condition": "filed_date > 4/15/2026 and neither line 8 nor line 9 checked (or > 6/15/2026 with a box)",
     "message": "Form 4868 must be filed by the due date of the return — April 15, 2026 (June 15, 2026 when the line 8 out-of-country or line 9 1040-NR box applies). E-file rejects a late extension (MeF F4868-001-02/-002-01). Disaster relief may extend the date — see IRS.gov/DisasterRelief.", "notes": "W2. Year-keyed dates."},
    {"diagnostic_id": "D_4868_ESTIMATE", "title": "Line 4 estimate must be reasonable", "severity": "warning",
     "condition": "L4 materially below the return's computed line 24 (or blank with computed liability)",
     "message": "The extension is valid only if the line 4 estimate of total tax liability was PROPERLY made from the information available — 'If we later find that the estimate wasn't reasonable, the extension will be null and void.' Enter the best current estimate of 2025 total tax (expected Form 1040 line 24); if you expect zero, enter -0-.", "notes": "W1. When the tts return is computed, L4 should derive YELLOW from live line 24."},
    {"diagnostic_id": "D_4868_L5EXCL", "title": "Line 5 excludes the extension payment itself", "severity": "warning",
     "condition": "L5 appears to include Sch 3 line 10 or the L7 amount",
     "message": "Line 5 is the total payments expected on the 2025 return line 33 EXCLUDING Schedule 3, line 10 — and never includes the amount being paid with this Form 4868 (line 7). Including either double-counts the extension payment.", "notes": "W1."},
    {"diagnostic_id": "D_4868_L6FLOOR", "title": "Line 6 floors at -0-", "severity": "info",
     "condition": "L5 > L4",
     "message": "Payments (line 5) exceed the estimated liability (line 4): line 6 is -0- per the face ('If line 5 is more than line 4, enter -0-'). No payment is needed for a valid extension — line 7 may be zero.", "notes": "W1."},
    {"diagnostic_id": "D_4868_PARTIAL", "title": "Paying less than the balance — interest and penalty exposure", "severity": "warning",
     "condition": "L7 < L6 and the safe harbor not met",
     "message": "The extension extends the time to FILE, not to pay. Interest runs on any tax unpaid after April 15, 2026, and the late-payment penalty (1/2% per month, max 25%) applies unless at least 90% of the actual 2025 tax is paid by the due date (withholding + estimates + this payment) AND the remainder is paid with the return. Pay as much as possible with the extension.", "notes": "W4. The two-prong safe harbor verbatim."},
    {"diagnostic_id": "D_4868_EFWTIE", "title": "Line 7 must equal the EFW payment record", "severity": "error",
     "condition": "IRSPayment record present and L7 != its PaymentAmt",
     "message": "This extension carries an electronic-funds-withdrawal record. Form 4868 line 7 ('amount you're paying') must EQUAL the payment record's amount (MeF FPYMT-052-02) — align the extension with the Payments-tab EFW amount, or remove one of them.", "notes": "W3. The s76 IRSPayment interplay (the 9465's F9465-019-02 analogue)."},
    {"diagnostic_id": "D_4868_SIGN", "title": "Payment rides — PIN and jurat required", "severity": "error",
     "condition": "IRSPayment/IRSESPayment present and PINTypeCd or signature PIN missing",
     "message": "An e-filed Form 4868 with NO payment needs no signature at all — but the moment an electronic-funds-withdrawal or scheduled estimated payment rides the extension, the taxpayer PIN, PIN type, and jurat are required (MeF R0000-098; spouse too on a joint extension, R0000-099). Jurat: 'Form 4868' for Self-Select paths, 'Form 4868 with Practitioner PIN and EFW' for the Practitioner PIN (F4868-007/-008/-009).", "notes": "W3."},
    {"diagnostic_id": "D_4868_JOINTAMP", "title": "Joint extension — name line needs an ampersand", "severity": "error",
     "condition": "spouse SSN present and no '&' in the e-file name line (or '&' without a spouse SSN)",
     "message": "When a spouse SSN is present on an e-filed Form 4868, the filer name line must contain an ampersand joining both names (MeF F4868-003-01); an ampersand without a spouse SSN also rejects (R0000-123-01). Enter both spouses' names in the order they will appear on the return.", "notes": "W3."},
    {"diagnostic_id": "D_4868_DUP", "title": "Duplicate extension for this SSN", "severity": "error",
     "condition": "a previously accepted extension exists for the primary SSN",
     "message": "The IRS rejects a Form 4868 whose primary SSN matches a previously accepted extension (MeF IND-900). If the client (or their other preparer, or an electronic payment marked 'extension') already extended, no second filing is needed — the extension is already in place.", "notes": "W3."},
    {"diagnostic_id": "D_4868_FISCAL", "title": "Fiscal-year filer — paper only", "severity": "error",
     "condition": "fiscal-year dates present and e-file attempted",
     "message": "'If you're a fiscal year taxpayer, you must file a paper Form 4868' — by the due date of the fiscal-year return. The e-file channel refuses fiscal-period extensions (the MeF manifest pins the calendar year, R0000-114/-115).", "notes": "W2."},
    {"diagnostic_id": "D_4868_OOC", "title": "Out of the country — the automatic 2 months + 4 more", "severity": "info",
     "condition": "line 8 checked",
     "message": "Out of the country (living outside the US and Puerto Rico with the main place of work outside both, or on military/naval duty outside both) on the due date, as a US citizen or resident: filing AND payment are automatically extended to June 15, 2026, with no form — interest still runs from April 15. Line 8 requests the additional 4 months (to October 15). Physical presence in the US/PR on the due date does not disqualify. Expecting to meet the bona fide residence or physical presence test later: use Form 2350 instead.", "notes": "W2."},
    {"diagnostic_id": "D_4868_NRA", "title": "Line 9 — 1040-NR June-15 due date", "severity": "info",
     "condition": "line 9 checked",
     "message": "A Form 1040-NR filer with no wages subject to US income tax withholding has a June 15, 2026 due date — file the 4868 by that date; the 6-month extension then runs to December 15, 2026.", "notes": "W2. The Dec-15 date is derived (6 months from June 15); the face prints only 'October 15, 2026, for most'."},
    {"diagnostic_id": "D_4868_CREDIT", "title": "Carry the extension payment to Schedule 3, line 10", "severity": "info",
     "condition": "L7 > 0 and the season return is prepared",
     "message": "The amount paid with Form 4868 is claimed on the 2025 return: Schedule 3, line 10 (Form 1040-SS: Part I, line 9). Separate extensions followed by a joint return: enter the total of both. A joint extension followed by separate returns: either spouse may claim the total, or divide it in any agreed amounts.", "notes": "W4. The tts proforma tie — L7 lands YELLOW on Sch 3 L10."},
    {"diagnostic_id": "D_4868_EPAY", "title": "An electronic payment marked 'extension' replaces the form", "severity": "info",
     "condition": "informational",
     "message": "Paying part or all of the estimated tax electronically (Direct Pay, EFTPS, card, or digital wallet) and marking it 'for an extension' processes the extension automatically — no Form 4868 needs to be filed. Keep the confirmation number with the records (the face has a worksheet line for it).", "notes": "W2/W3."},
    {"diagnostic_id": "D_4868_ADDR", "title": "Paper mailing addresses (year-watched)", "severity": "info",
     "condition": "informational on paper filing",
     "message": "Paper 4868 WITH payment: Georgia (and AL FL LA MS NC SC TN TX) mails to Charlotte, NC P.O. Box 1302 (28201-1302); all other states to Louisville, KY P.O. Box 931300. WITHOUT payment: Austin, Kansas City, or Ogden by state row. Foreign/territory/APO-FPO/Form 2555/4563/dual-status filers: Charlotte Box 1303 / Austin 73301-0215. P.O. boxes are USPS-only — private delivery services need the street addresses (irs.gov/PDSStreetAddresses). NOTE the cluster trap: the 1040-V uses Box 1214, the 1040-ES Box 1300, the 4868 Box 1302 — never interchange. Addresses may change: check IRS.gov/Form4868.", "notes": "W4. Year-watched; the four-way Charlotte divergence pinned in the harness."},
    {"diagnostic_id": "D_4868_NOATTACH", "title": "Nothing attaches to a 4868", "severity": "error",
     "condition": "an attachment rides the extension submission",
     "message": "The extension submission must not contain any binary attachment (MeF R0000-195 — the schema declares the slot but the rule rejects it). Penalty reasonable-cause statements attach to the RETURN, never to Form 4868; and the 4868 itself is never attached to the filed return.", "notes": "W3. Refusal-encoded so no tts surface adds statements to the extension."},
]

F4868_SCENARIOS: list[dict] = [
    {"scenario_name": "4868-A — normal: owes 5,000, pays in full, EFW rides", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"estimated_total_tax": 20000, "estimated_payments": 15000, "amount_paying": 5000,
                "efw_payment_amount": 5000, "filed_date": "2026-04-10", "pin_type": "Practitioner"},
     "expected_outputs": {"balance_due": 5000, "efw_consistent": True, "window_ok": True,
                          "signature_required": True, "jurat_code": "Form 4868 with Practitioner PIN and EFW",
                          "extended_due_date": "2026-10-15"},
     "notes": "L6 = 20,000 - 15,000 = 5,000; EFW == L7 satisfies FPYMT-052-02; payment present -> PIN + the Practitioner jurat; extension lands Oct 15."},
    {"scenario_name": "4868-B — overpaid: L5 > L4 floors L6 at -0-, no signature needed", "scenario_type": "edge", "sort_order": 2,
     "inputs": {"estimated_total_tax": 20000, "estimated_payments": 22000, "amount_paying": 0,
                "efw_payment_amount": None, "filed_date": "2026-04-15"},
     "expected_outputs": {"balance_due": 0, "efw_consistent": True, "window_ok": True, "signature_required": False},
     "notes": "'If line 5 is more than line 4, enter -0-.' No payment record -> NO PIN at all (R0000-098 untriggered); 4/15 exactly is timely (on-or-before)."},
    {"scenario_name": "4868-C — zero liability: L4 = -0-, still a valid extension", "scenario_type": "edge", "sort_order": 3,
     "inputs": {"estimated_total_tax": 0, "estimated_payments": 0, "amount_paying": 0, "filed_date": "2026-03-01"},
     "expected_outputs": {"balance_due": 0, "window_ok": True},
     "notes": "'If you expect this amount to be zero, enter -0-.' The qualifying trio only requires a PROPER estimate — zero is fine when true."},
    {"scenario_name": "4868-D — partial pay 2,000 of 8,000: extension holds, safe harbor missed", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"estimated_total_tax": 40000, "estimated_payments": 32000, "amount_paying": 2000,
                "filed_date": "2026-04-14"},
     "expected_outputs": {"balance_due": 8000, "safe_harbor_met": False, "window_ok": True, "diagnostic": "D_4868_PARTIAL"},
     "notes": "Paid-by-due-date = 32,000 + 2,000 = 34,000 = 85% of 40,000 < 90% -> late-payment penalty exposure (0.5%/month on the 6,000); the extension itself is still valid ('you can still get the extension')."},
    {"scenario_name": "4868-E — the 90% safe harbor met at the boundary", "scenario_type": "edge", "sort_order": 5,
     "inputs": {"estimated_total_tax": 40000, "estimated_payments": 34000, "amount_paying": 2000},
     "expected_outputs": {"safe_harbor_met": True},
     "notes": "36,000 paid = exactly 90% of 40,000 -> 'at least 90%' is met at equality (prong 1); prong 2 (remainder with the return) is a filing-time condition."},
    {"scenario_name": "4868-F — out of country: filed May 20 with line 8, valid", "scenario_type": "edge", "sort_order": 6,
     "inputs": {"estimated_total_tax": 12000, "estimated_payments": 11000, "amount_paying": 1000,
                "out_of_country": True, "filed_date": "2026-05-20"},
     "expected_outputs": {"balance_due": 1000, "window_ok": True, "extended_due_date": "2026-10-15"},
     "notes": "F4868-002-01: with line 8 the window runs to 6/15/2026 — a May-20 filing is timely; the automatic 2 months + 4 more still land on the SAME Oct 15."},
    {"scenario_name": "4868-G — 1040-NR line 9: June window, December landing", "scenario_type": "edge", "sort_order": 7,
     "inputs": {"nr_no_wages": True, "filed_date": "2026-06-15"},
     "expected_outputs": {"window_ok": True, "extended_due_date": "2026-12-15"},
     "notes": "Line 9: the return is due 6/15/2026; the 6-month extension runs from THAT due date -> 12/15/2026 (derived; i1040-NR states it). 6/15 exactly is timely."},
    {"scenario_name": "4868-H — EFW mismatch refuses: L7 3,000 vs record 2,500", "scenario_type": "failure", "sort_order": 8,
     "inputs": {"estimated_total_tax": 10000, "estimated_payments": 7000, "amount_paying": 3000,
                "efw_payment_amount": 2500, "filed_date": "2026-04-01"},
     "expected_outputs": {"efw_consistent": False, "diagnostic": "D_4868_EFWTIE"},
     "notes": "FPYMT-052-02: the IRSPayment PaymentAmt must EQUAL line 7 — 2,500 != 3,000 refuses at extract with the align-or-remove message."},
    {"scenario_name": "4868-I — joint without the ampersand refuses", "scenario_type": "failure", "sort_order": 9,
     "inputs": {"name_line": "KEN EXAMPLE", "spouse_ssn": "400-00-1111", "filed_date": "2026-04-01"},
     "expected_outputs": {"joint_name_ok": False, "diagnostic": "D_4868_JOINTAMP"},
     "notes": "F4868-003-01: SpouseSSN present -> NameLine1Txt must carry '&'. 'KEN & JAN EXAMPLE' passes; the converse (ampersand, no spouse SSN) trips R0000-123-01."},
    {"scenario_name": "4868-J — filed April 20, no boxes: late, extension refused", "scenario_type": "failure", "sort_order": 10,
     "inputs": {"estimated_total_tax": 5000, "estimated_payments": 4000, "filed_date": "2026-04-20"},
     "expected_outputs": {"window_ok": False, "diagnostic": "D_4868_LATE"},
     "notes": "F4868-001-02 rejects after 4/15 without line 8/9. (A payment made electronically and marked 'extension' BY the due date would have processed the extension without the form — D_4868_EPAY.)"},
]

FORMS: list[dict] = [
    {
        "identity": {"form_number": "4868", "form_title": "Form 4868 — Application for Automatic Extension of Time To File (2025)",
                     "notes": "Post-payment-cluster draft-to-gate order (tts s78). 6 months to FILE (never to pay) the 1040/1040-SR/1040-NR/1040-SS -> Oct 15; line 8 out-of-country (auto 2 months to 6/15 + 4 more), line 9 1040-NR June-due (-> Dec 15 derived). OWN MeF submission family (ReturnTypeCd '4868' — Return4868/ReturnHeader4868/ReturnData4868; TY2026v1.0 package local): six-element IRS4868 + <=1 IRSPayment + <=4 IRSESPayment; NO binary attachments (R0000-195); no-payment extensions carry NO signature (R0000-098 triggers the PIN/jurat ladder only when a payment record rides; jurat enum F4868-007/8/9); FPYMT-052-02 EFW tie (PaymentAmt == L7); IND-900 duplicate; F4868-003 joint-ampersand. Face math: L6 = max(0, L4-L5); L4 = expected line 24 (zero -> -0-; unreasonable = null and void); L5 excludes Sch 3 L10 + the L7 payment. Penalties: interest always; late-pay 0.5%/mo max 25% w/ the 90%-paid+rest-with-return safe harbor; late-file 5%/mo max 25%, >60d minimum $525 (YEAR-KEYED). Credit -> Sch 3 L10 (joint/separate splits both directions). 709/709-NA filing rider (payment = 8892). Fiscal-year = paper only. E-pay-marked-extension = no form needed. Where-to-file: GA-with-payment = Charlotte Box 1302 — the FOURTH cluster Charlotte box (V 1214 / ES 1300 / 4868 1302 / foreign 1303), year-watched. FLAGGED: the TY2026v1.0 FPYMT-088-11 ES-date list is a stale early-drop carryover; the 2025-face/TY2026-package version seam (TY2026 face ~Oct 2026). entity_types ['1040']; print + its own MeF submission builder."},
        "facts": F4868_FACTS, "rules": F4868_RULES, "rule_links": F4868_RULE_LINKS,
        "lines": F4868_LINES, "diagnostics": F4868_DIAGNOSTICS, "scenarios": F4868_SCENARIOS,
    },
]

# Staged DRAFT deliberately (the new-FAs-default-ACTIVE trap): the tts build leg activates + writes
# runners + refreshes the export-verbatim mirrors in ONE motion.
FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-4868-L6", "title": "Line 6 = line 4 - line 5, floored at -0-", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "draft", "sort_order": 1,
     "description": "balance_due = max(0, L4 - L5). Pins: (20000, 15000) -> 5000; (20000, 22000) -> 0; (0, 0) -> 0; (40000, 32000) -> 8000. The face's own floor sentence is the authority.",
     "definition": {"rule": "R-4868-CALC", "check": "L6 == max(0, L4 - L5)"}},
    {"assertion_id": "FA-4868-EFW", "title": "Line 7 equals the IRSPayment record amount", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "draft", "sort_order": 2,
     "description": "When the extension submission carries an IRS Payment Record (the s76 EFW half), its PaymentAmt must equal Form 4868 line 7 (FPYMT-052-02). Pins: (5000, 5000) consistent; (3000, 2500) refuses; (anything, None) consistent.",
     "definition": {"rule": "R-4868-PAY", "check": "line7 == IRSPayment.PaymentAmt when the record exists"}},
    {"assertion_id": "FA-4868-CREDIT", "title": "The 4868 payment lands on Schedule 3 line 10", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "draft", "sort_order": 3,
     "description": "A filed extension's line-7 payment must appear on the season return's Schedule 3 line 10 (1040-SS Part I line 9) — the YELLOW derive the tts leg wires; L5 on the extension side must EXCLUDE that same line (the double-count guard).",
     "definition": {"rule": "R-4868-CREDIT", "check": "Sch3 L10 == 4868 L7 (and 4868 L5 excludes Sch3 L10)"}},
]


class Command(BaseCommand):
    help = "Load the Form 4868 spec (Automatic Extension). Refuses to seed until READY_TO_SEED=True (Gate-1 W1-W4)."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad Form 4868 spec (Automatic Extension of Time To File)\n"))
        self._load_topics()
        sources = self._load_sources()
        for spec in FORMS:
            form = self._upsert_form(spec["identity"])
            self._upsert_facts(form, spec["facts"])
            rules = self._upsert_rules(form, spec["rules"])
            self._upsert_links(rules, sources, spec["rule_links"])
            self._upsert_lines(form, spec["lines"])
            self._upsert_diag(form, spec["diagnostics"])
            self._upsert_tests(form, spec["scenarios"])
        self._upsert_form_links(sources)
        self._load_fa()
        self._report()

    def _guard(self):
        empty = []
        for spec in FORMS:
            fn = spec["identity"]["form_number"]
            for key in ("facts", "rules", "lines", "diagnostics", "scenarios", "rule_links"):
                if not spec[key]:
                    empty.append(f"{fn}.{key}")
        if not FLOW_ASSERTIONS:
            empty.append("FLOW_ASSERTIONS")
        if not READY_TO_SEED or empty:
            still = "\n  ".join(f"- {n}" for n in empty) or "(all populated)"
            raise CommandError(
                "\nREFUSING TO SEED FORM 4868: not cleared.\n\n"
                "Gated until Ken approves the Gate-1 walk (W1 face math + qualifying; W2 windows incl. the\n"
                "fiscal-paper bar + the derived Dec-15 arm; W3 the own-family MeF channel + the payment-\n"
                "triggered signature ladder + the EFW tie + the flagged FPYMT-088-11/version seams;\n"
                "W4 penalties/safe harbor + Sch 3 L10 credit + the year-watched chart) and flips the sentinel.\n\n"
                f"READY_TO_SEED = {READY_TO_SEED}\n\nEmpty:\n  {still}\n"
            )

    def _load_topics(self):
        ct = 0
        for code, name in AUTHORITY_TOPICS:
            _, created = AuthorityTopic.objects.update_or_create(topic_code=code, defaults={"topic_name": name})
            ct += 1 if created else 0
        self.stdout.write(f"Topics: {ct} new")

    def _load_sources(self) -> dict:
        sources: dict = {}
        for sd in AUTHORITY_SOURCES:
            sd = dict(sd)
            exc = sd.pop("excerpts", [])
            tcs = sd.pop("topics", [])
            src, _ = AuthoritySource.objects.update_or_create(source_code=sd["source_code"], defaults=sd)
            sources[src.source_code] = src
            for e in exc:
                e = dict(e)
                AuthorityExcerpt.objects.update_or_create(authority_source=src, excerpt_label=e["excerpt_label"], defaults=e)
            for tc in tcs:
                t = AuthorityTopic.objects.filter(topic_code=tc).first()
                if t:
                    AuthoritySourceTopic.objects.get_or_create(authority_source=src, authority_topic=t)
        for code in EXISTING_SOURCES_TO_REFERENCE:
            src = AuthoritySource.objects.filter(source_code=code).first()
            if src:
                sources[code] = src
            else:
                self.stdout.write(self.style.WARNING(f"  (existing source {code} not in this DB — links to it will skip)"))
        self.stdout.write(f"Sources ready: {len(sources)}")
        return sources

    def _upsert_form(self, identity: dict) -> TaxForm:
        form, created = TaxForm.objects.update_or_create(
            form_number=identity["form_number"], jurisdiction=FORM_JURISDICTION, tax_year=FORM_TAX_YEAR, version=FORM_VERSION,
            defaults={"form_title": identity["form_title"], "entity_types": FORM_ENTITY_TYPES, "status": FORM_STATUS, "notes": identity["notes"]},
        )
        self.stdout.write(f"{'Created' if created else 'Updated'} {identity['form_number']} {FORM_ENTITY_TYPES}")
        return form

    def _upsert_facts(self, form, facts):
        for f in facts:
            f = dict(f)
            FormFact.objects.update_or_create(tax_form=form, fact_key=f.pop("fact_key"), defaults=f)
        self.stdout.write(f"  {len(facts)} facts")

    def _upsert_rules(self, form, rules_data) -> dict:
        created = {}
        for r in rules_data:
            r = dict(r)
            rule, _ = FormRule.objects.update_or_create(tax_form=form, rule_id=r.pop("rule_id"), defaults=r)
            created[rule.rule_id] = rule
        self.stdout.write(f"  {len(created)} rules")
        return created

    def _upsert_links(self, rules, sources, rule_links):
        ct = 0
        for rid, sc, lvl, note in rule_links:
            rule, src = rules.get(rid), sources.get(sc)
            if rule and src:
                RuleAuthorityLink.objects.get_or_create(form_rule=rule, authority_source=src, defaults={"support_level": lvl, "relevance_note": note})
                ct += 1
        self.stdout.write(f"  {ct} authority links")

    def _upsert_lines(self, form, lines):
        for ln in lines:
            ln = dict(ln)
            FormLine.objects.update_or_create(tax_form=form, line_number=ln.pop("line_number"), defaults=ln)
        self.stdout.write(f"  {len(lines)} lines")

    def _upsert_diag(self, form, diags):
        for d in diags:
            d = dict(d)
            FormDiagnostic.objects.update_or_create(tax_form=form, diagnostic_id=d.pop("diagnostic_id"), defaults=d)
        self.stdout.write(f"  {len(diags)} diagnostics")

    def _upsert_tests(self, form, scenarios):
        for t in scenarios:
            t = dict(t)
            TestScenario.objects.update_or_create(tax_form=form, scenario_name=t.pop("scenario_name"), defaults=t)
        self.stdout.write(f"  {len(scenarios)} test scenarios")

    def _upsert_form_links(self, sources):
        for sc, fc, lt in AUTHORITY_FORM_LINKS:
            src = sources.get(sc) or AuthoritySource.objects.filter(source_code=sc).first()
            if src:
                AuthorityFormLink.objects.get_or_create(authority_source=src, form_code=fc, link_type=lt, defaults={"note": f"{sc} -> {fc}"})

    def _load_fa(self):
        for a in FLOW_ASSERTIONS:
            a = dict(a)
            FlowAssertion.objects.update_or_create(assertion_id=a.pop("assertion_id"), defaults=a)
        self.stdout.write(f"  {len(FLOW_ASSERTIONS)} flow assertions (staged DRAFT — the tts leg activates)")

    def _report(self):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("Form 4868 loaded.")
        self.stdout.write(f"  4868: facts {len(F4868_FACTS)} / rules {len(F4868_RULES)} / lines {len(F4868_LINES)} / diag {len(F4868_DIAGNOSTICS)} / tests {len(F4868_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}")
        self.stdout.write("=" * 60)
