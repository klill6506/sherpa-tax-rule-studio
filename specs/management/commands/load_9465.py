"""Load the Form 9465 spec — Installment Agreement Request (Rev. September 2020 / i9465 Rev. July 2024).
Payment-cluster draft-to-gate batch order 1 (tts s77; plan filed tts REVIEW_QUEUE s76). Greenfield
(gap re-confirmed 404 on 2026-07-13).

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
Form 9465 requests a monthly installment agreement for tax the client can't pay in full. Attached to
the FRONT of the 1040 or filed standalone. UNLIKE 2553/2848 this form HAS a MeF channel: IRS9465 is a
ReturnData1040 document (2025v5.3 InstallmentAgreement family) — the tts leg is print + MeF document.
The e-file gate is narrow: balance <= $50,000, no payroll deduction, proposed payment >= line 10 —
everything else refuses to paper (the F9465-* business rules encode each arm verbatim). The s76 EFW
interplay is F9465-019-02: line 8 must EQUAL the IRSPayment record's PaymentAmt when both are present.

v1 SCOPE — PROPOSED (Gate-1 walk W1-W4 AWAITING KEN; see f9465_source_brief.md):
W1. Face math + the minimum-payment gate: 7=5+6, 9=7-8, line 10 = line 9 / 72 (encoded as
    whole-dollar CEILING — the "full pay within 72 months" test; the face states no rounding,
    flagged as a convention); payment day 1-28; the 11a/11b/can't-increase ladder (433-F arms).
W2. Agreement-type router as diagnostics: guaranteed (<=$10k + 5-yr compliance + 3-yr full pay),
    streamlined (<=$25k, or $25,001-50k WITH direct debit or payroll deduction), >$50k / below-
    minimum -> Form 433-F paper paths; OPA-is-cheaper info.
W3. The e-file gate (MeF F9465-* rules verbatim): >$50k / payroll-deduction / can't-increase /
    below-minimum REFUSE; phone required; 13a/13b pairing; 13c-vs-routing conflict; 11a!=11b;
    the $25,001-50k band is effectively direct-debit-or-refuse in e-file (payroll can't transmit);
    line 8 == IRSPayment PaymentAmt when an EFW record rides the same return.
W4. Fee schedule (July-1-2024 table VERIFIED CURRENT 2026-07-13 vs the live IRS payments page
    reviewed 28-Jun-2026; YEAR-KEYED): OPA $22 DD / $69 other; 9465-channel $107 DD / $178 other;
    payroll $178; low-income (AGI <= 250% poverty, Form 13844) DDIA-waived / $43 reduced /
    13c-reimbursed; modify $89/$43/$10-OPA. Part II three-condition gate + spouse-line rules.
    Where-to-file chart (year-watched). entity_types ['1040']; print + MeF document.

CARRIED [UNVERIFIED]: none — verbatim vs Form 9465 Rev. 9-2020 + i9465 Rev. 7-2024 (About page
"None at this time" 2026-07-13) + the live fee page + the 2025v5.3 business rules/XSD. Year-watch:
the fee table (26 CFR 300 amendments — T.D. 10045 Apr-2026 checked, IA fees unchanged), the
where-to-file chart, the OPA thresholds.

SAFETY GUARD — READY_TO_SEED stayed False until Gate-1 approval. APPROVED: Ken, 2026-07-14 (s83 approve-all, WO-28/29/30/31/32 together; walk recommendations adopted as filed).
"""
import math

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from sources.models import (
    AuthorityExcerpt, AuthorityFormLink, AuthoritySource, AuthoritySourceTopic,
    AuthorityTopic, RuleAuthorityLink,
)
from specs.models import (
    FlowAssertion, FormDiagnostic, FormFact, FormLine, FormRule, TaxForm, TestScenario,
)

READY_TO_SEED = True  # FLIPPED 2026-07-14 — Ken approved Gate-1 in-session (s83 approve-all across WO-28/29/30/31/32; recommendations adopted as filed).

FORM_JURISDICTION = "federal"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1040"]

# ── Verified constants (f9465_source_brief.md) ──
EFILE_MAX_BALANCE = 50_000       # F9465-001-03: TotalTaxDueAmt > 50000 -> not e-fileable (paper + 433-F)
STREAMLINED_LOW_MAX = 25_000     # streamlined tier 1 ceiling (no DD requirement)
STREAMLINED_HIGH_MAX = 50_000    # streamlined tier 2 ceiling (DD or payroll deduction required)
GUARANTEED_MAX = 10_000          # §6159(c) guaranteed IA ceiling ("the tax you owe isn't more than $10,000")
FULL_PAY_MONTHS = 72             # line 10 divisor; streamlined must full-pay within 72 months (or CSED if less)
MAX_PAYMENT_DAY = 28             # line 12: "Don't enter a date later than the 28th"
SHORT_TERM_DAYS = 180            # pay-in-full window that avoids the IA fee entirely ($0 short-term plan)
SHORT_TERM_MAX = 100_000         # OPA short-term plan ceiling ("If you owe $100,000 or less")
LOW_INCOME_POVERTY_PCT = 250     # low-income = AGI <= 250% federal poverty guidelines (Form 13844)
USER_FEES = {                    # effective July 1, 2024 — VERIFIED CURRENT 2026-07-13 (YEAR-KEYED)
    ("opa", True): 22, ("opa", False): 69,
    ("form9465", True): 107, ("form9465", False): 178,
}
FEE_PAYROLL_DEDUCTION = 178      # Form 2159 route ("your user fee will be $178 beginning July 1, 2024")
FEE_LOW_INCOME_REDUCED = 43      # low-income non-DD reduced fee (reimbursed on completion if 13c)
FEE_MODIFY = 89                  # modify/terminate ($43 low-income; $10 via OPA reinstate/restructure)
FEE_MODIFY_OPA = 10


def _monthly_minimum(line9_owed) -> int:
    """Line 10 = line 9 / 72, encoded as the whole-dollar CEILING: the smallest whole-dollar payment
    whose 72 installments cover the balance (the streamlined full-pay-within-72-months test). The face
    prints 'Divide the amount on line 9 by 72.0' with no rounding direction — convention flagged in W1."""
    return int(math.ceil(float(line9_owed) / FULL_PAY_MONTHS)) if float(line9_owed) > 0 else 0


def _guaranteed_eligible(owed, five_year_compliant, agrees_full_pay_3yr, unable_to_pay_full) -> bool:
    """§6159(c) guaranteed IA: tax owed <= $10,000 AND past-5-years timely filed/paid with no prior IA
    AND agrees to full pay within 3 years + comply while in effect AND financially unable to pay when due."""
    return bool(float(owed) <= GUARANTEED_MAX and five_year_compliant and agrees_full_pay_3yr and unable_to_pay_full)


def _streamlined_eligible(owed, has_direct_debit, payroll_deduction) -> bool:
    """Streamlined IA: assessed liability <= $25,000; or $25,001-$50,000 AND direct debit or payroll
    deduction. (Full-pay within 72 months / CSED rides the line-10 minimum separately.)"""
    owed = float(owed)
    if owed <= STREAMLINED_LOW_MAX:
        return True
    return owed <= STREAMLINED_HIGH_MAX and bool(has_direct_debit or payroll_deduction)


def _part2_required(defaulted_ia_past_12mo, owed, proposed_below_minimum) -> bool:
    """Part II required only when ALL THREE hold: defaulted on an IA in the past 12 months; owes
    > $25,000 but <= $50,000; and line 11a (or 11b) is less than line 10."""
    owed = float(owed)
    return bool(defaulted_ia_past_12mo and STREAMLINED_LOW_MAX < owed <= STREAMLINED_HIGH_MAX
                and proposed_below_minimum)


def _spouse_lines_required(has_spouse, shares_household_expenses, community_property_state) -> bool:
    """Part II lines 21/22: complete when married AND (live with + share household expenses, or live in
    a community property state) — whether filing MFJ or MFS."""
    return bool(has_spouse and (shares_household_expenses or community_property_state))


def _efile_blockers(owed_total, payroll_deduction, cannot_increase, proposed, revised, minimum,
                    has_phone, routing, account, low_income_no_dd) -> list:
    """The MeF gate, one code per ACTIVE F9465-* reject arm the return would hit. Empty list = e-fileable."""
    blockers = []
    if float(owed_total) > EFILE_MAX_BALANCE:
        blockers.append("F9465-001-03")            # > $50,000 -> paper + 433-F
    if payroll_deduction:
        blockers.append("F9465-026-01")            # payroll deduction -> paper + 2159
    if cannot_increase:
        blockers.append("F9465-037-01")            # can't-increase box -> paper + 433-F
    effective = float(revised) if float(revised or 0) > 0 else float(proposed or 0)
    if float(revised or 0) > 0 and float(revised) < float(minimum):
        blockers.append("F9465-039-01")            # revised below the calculated minimum
    elif effective < float(minimum):
        blockers.append("F9465-027-01")            # proposed below the calculated minimum
    if not has_phone:
        blockers.append("F9465-018-01")            # home or work phone required
    if bool(routing) != bool(account):
        blockers.append("F9465-016-01")            # 13a/13b must pair (016/017 collapse to one arm)
    if routing and low_income_no_dd:
        blockers.append("F9465-040")               # routing present -> 13c must NOT be checked
    if (STREAMLINED_LOW_MAX < float(owed_total) <= STREAMLINED_HIGH_MAX and effective >= float(minimum)
            and not (routing and account) and not payroll_deduction):
        blockers.append("F9465-044")               # the 25k-50k band: DD or payroll, and payroll can't e-file
    return blockers


def _user_fee(applied_online, has_direct_debit, is_low_income, payroll_deduction) -> int:
    """The July-1-2024 schedule (VERIFIED CURRENT 2026-07-13; YEAR-KEYED). Low-income: DDIA waives the
    fee entirely; otherwise the reduced $43 (reimbursed on completion when 13c is checked)."""
    if is_low_income:
        return 0 if has_direct_debit else FEE_LOW_INCOME_REDUCED
    if payroll_deduction:
        return FEE_PAYROLL_DEDUCTION
    return USER_FEES[("opa" if applied_online else "form9465", bool(has_direct_debit))]


def _payment_day_ok(day) -> bool:
    """Line 12: on or after the 1st, no later than the 28th."""
    return 1 <= int(day) <= MAX_PAYMENT_DAY


def _efw_amount_consistent(payment_with_request, efw_payment_amount) -> bool:
    """F9465-019-02: when an IRS Payment Record (the s76 EFW half) rides the same return, Form 9465
    line 8 'PaymentAmt' must EQUAL the payment record's 'PaymentAmt'."""
    if efw_payment_amount is None:
        return True
    return float(payment_with_request or 0) == float(efw_payment_amount)


AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("ia_9465", "Form 9465 installment agreements: line-10 minimum (72-month), guaranteed/streamlined "
     "tiers, the F9465-* e-file gate incl. the EFW PaymentAmt tie, the July-2024 fee schedule "
     "(year-keyed), Part II three-condition gate, where-to-file."),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_F9465", "source_type": "federal_form", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Form 9465 (Rev. 9-2020) — Installment Agreement Request",
        "citation": "Form 9465 (Rev. September 2020), Cat. No. 14842Y, OMB 1545-0074",
        "issuer": "Internal Revenue Service", "official_url": "https://www.irs.gov/pub/irs-pdf/f9465.pdf",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.5, "topics": ["ia_9465"],
        "excerpts": [{
            "excerpt_label": "Part I face lines 5-14 (Rev. 9-2020 verbatim substance)",
            "excerpt_text": (
                "L5 Enter the total amount you owe as shown on your tax return(s) (or notice(s)). L6 If you "
                "have any additional balances due that aren't reported on line 5, enter the amount here (even "
                "if the amounts are included in an existing installment agreement). L7 Add lines 5 and 6. L8 "
                "Enter the amount of any payment you're making with this request. L9 Amount owed: subtract "
                "line 8 from line 7. L10 Divide the amount on line 9 by 72.0 and enter the result. L11a Enter "
                "the amount you can pay each month. Make your payment as large as possible to limit interest "
                "and penalty charges... If no payment amount is listed on line 11a, a payment will be "
                "determined for you by dividing the balance due on line 9 by 72 months. L11b If the amount on "
                "line 11a is less than the amount on line 10 and you're able to increase your payment to an "
                "amount that is equal to or greater than the amount on line 10, enter your revised monthly "
                "payment. Bullets: If you can't increase your payment on line 11b to more than or equal to the "
                "amount shown on line 10, check the box — also complete and attach Form 433-F. If the amount "
                "on line 11a (or 11b, if applicable) is more than or equal to the amount on line 10 and the "
                "amount you owe is over $25,000 but not more than $50,000, then you don't have to complete "
                "Form 433-F; however, if you don't complete Form 433-F, then you must complete either line 13 "
                "or 14. If the amount on line 9 is greater than $50,000, complete and attach Form 433-F. L12 "
                "Enter the date you want to make your payment each month. Don't enter a date later than the "
                "28th. L13a routing number / L13b account number [ACH authorization: revoke no later than 14 "
                "business days prior to the payment (settlement) date at 1-800-829-1040]. L13c Low-income "
                "taxpayers only: if you're unable to make electronic payments through a debit instrument by "
                "providing your banking information on lines 13a and 13b, check this box and your user fee "
                "will be reimbursed upon completion of your installment agreement. L14 If you want to make "
                "payments by payroll deduction, check this box and attach a completed Form 2159."
            ),
            "summary_text": "Face math 5-10 (line 10 = line 9 / 72.0); the 11a/11b/can't-increase ladder with its three 433-F/13-or-14 bullets; day <= 28; 13a/13b DD + the 14-business-day revocation; 13c low-income reimbursement; 14 payroll deduction (Form 2159).",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "Part II gate + tip box (Rev. 9-2020 verbatim substance)",
            "excerpt_text": (
                "Part II Additional Information — complete this Part only if all three conditions below "
                "apply: 1. You defaulted on an installment agreement in the past 12 months; 2. You owe more "
                "than $25,000 but not more than $50,000; and 3. The amount on line 11a (or 11b, if applicable) "
                "is less than line 10. Note: If you owe more than $50,000, also complete and attach Form "
                "433-F. [Lines 15-27: county of primary residence; marital status + share-household-expenses; "
                "dependents claimed; household members 65 or older; pay frequency (once a week / once every 2 "
                "weeks / once a month / twice a month) + net income per pay period, for taxpayer and (lines "
                "21-22) spouse; vehicles owned; car payments per month; health insurance yes/no, "
                "premiums-deducted yes/no, monthly premium; court-ordered payments yes/no, deducted yes/no, "
                "monthly amount; child or dependent care paid each month.] Tip (page 1): If you owe $50,000 "
                "or less, you may be able to avoid filing Form 9465 and establish an installment agreement "
                "online... the user fee that you pay will be lower than it would be with Form 9465."
            ),
            "summary_text": "Part II required only when ALL THREE: defaulted-within-12-months + owe $25,001-$50,000 + proposed payment below line 10; lines 15-27 household financials; the OPA-is-cheaper tip.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "IRS_I9465", "source_type": "federal_form", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Instructions for Form 9465 (Rev. 7-2024)",
        "citation": "i9465 (Rev. July 2024), Cat. No. 58607N — for use with Form 9465 (Rev. September 2020)",
        "issuer": "Internal Revenue Service", "official_url": "https://www.irs.gov/pub/irs-pdf/i9465.pdf",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.5, "topics": ["ia_9465"],
        "excerpts": [{
            "excerpt_label": "Agreement types — guaranteed / streamlined / PPIA (i9465 7-2024 verbatim)",
            "excerpt_text": (
                "Guaranteed installment agreement. You're eligible for a guaranteed installment agreement if "
                "the tax you owe isn't more than $10,000 and: during the past 5 tax years, you (and your "
                "spouse if filing a joint return) have timely filed all income tax returns and paid any income "
                "tax due, and haven't entered into an installment agreement for the payment of income tax; you "
                "agree to pay the full amount you owe within 3 years and to comply with the tax laws while the "
                "agreement is in effect; and you're financially unable to pay the liability in full when due. "
                "Streamlined installment agreement. Generally, you're eligible for a streamlined installment "
                "agreement if: your assessed tax liability is $25,000 or less (for an individual, in-business "
                "with income tax only, or an out-of-business taxpayer); or your assessed tax liability is "
                "$25,001 to $50,000 (for an individual or an out-of-business sole proprietorship) and you "
                "agree to pay by direct debit or payroll deduction. Your proposed payment amount must pay in "
                "full the assessed tax liability within 72 months or satisfy the liability in full by the "
                "Collection Statute Expiration Date (CSED), whichever is less. The CSED is normally 10 years "
                "from the date of the assessment... Generally, a streamlined installment agreement does not "
                "require a financial statement or a Notice of Federal Tax Lien to be filed. Partial payment "
                "installment agreement (PPIA): an installment agreement that will not pay in full the entire "
                "balance before the CSED... you will be required to complete a financial statement."
            ),
            "summary_text": "Guaranteed: <= $10,000 + 5-year clean compliance + 3-year full pay + unable to pay. Streamlined: <= $25,000, or $25,001-$50,000 with direct debit or payroll deduction; full pay within 72 months or by the CSED. PPIA needs a financial statement.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "User fees + low-income waiver/reimbursement (i9465 7-2024 verbatim)",
            "excerpt_text": (
                "Installment agreement user fees... the fees in effect as of July 1, 2024: Direct debit — $22 "
                "using the online payment application, $107 not using the online payment application. Check, "
                "money order, credit card, or debit card — $69 using the online payment application, $178 not "
                "using the online payment application. Note: if you request a payroll deduction agreement "
                "using Form 2159, your user fee will be $178 beginning July 1, 2024. Low-income taxpayer "
                "reduced installment agreement user fee: if you establish an installment agreement that is not "
                "paid by direct debit, you may qualify to pay a reduced fee of $43 or for a reimbursement of "
                "your fee... A low-income taxpayer is a taxpayer with adjusted gross income, for the most "
                "recent tax year available, at or below 250% of the federal poverty guidelines [Form 13844]. "
                "If you're a low-income taxpayer and you agree to make electronic payments through a debit "
                "instrument by entering into a direct debit installment agreement (DDIA), the IRS will waive "
                "the user fees for the installment agreement. If you're a low-income taxpayer and you're "
                "unable to make electronic payments through a debit instrument by entering into a DDIA, the "
                "IRS will reimburse the reduced $43 user fee that you paid... upon completion of the "
                "installment agreement. Requests to modify or terminate: generally, the fee is $89 to modify "
                "your installment agreement ($43 if you are a low-income taxpayer). However, the user fee is "
                "$10 for installment agreements reinstated or restructured through an OPA."
            ),
            "summary_text": "July-1-2024 table: OPA $22 DD / $69 other; non-OPA $107 DD / $178 other; payroll (2159) $178. Low-income (AGI <= 250% poverty): DDIA waives the fee; non-DD reduced to $43, reimbursed on completion when unable to DD (13c). Modify $89 / $43 low-income / $10 OPA.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "Who files / who doesn't + OPA and short-term alternatives (i9465 7-2024 verbatim substance)",
            "excerpt_text": (
                "Use Form 9465 if you're an individual: who owes income tax on Form 1040 or 1040-SR; who is "
                "or may be responsible for a trust fund recovery penalty; who owes employment taxes (for "
                "example, as reported on Forms 941, 943, or 940) related to a sole proprietor business that "
                "is no longer in operation; or who owes an individual shared responsibility payment under the "
                "Affordable Care Act. Don't use Form 9465 if: you can pay the full amount you owe within 180 "
                "days...; you want to request a payment plan online...; or your business is still operating "
                "and owes employment or unemployment taxes (instead, call the telephone number on your most "
                "recent notice). If you can pay the full amount you owe within 180 days, you can avoid paying "
                "the fee to set up an installment agreement by calling the IRS at 800-829-1040; if you owe "
                "$100,000 or less, you can apply for a short-term payment plan using the OPA application. If "
                "your balance due isn't more than $50,000, you can apply online for a payment plan instead of "
                "filing Form 9465... the user fee that you pay will be lower. Bankruptcy or offer in "
                "compromise: don't file this form. Your request for an installment agreement will be denied "
                "if any required tax returns haven't been filed. Any refund will be applied against the "
                "amount you owe... If you don't make your payments on time or don't timely pay a balance due "
                "on a return you file later, you will be in default on your agreement."
            ),
            "summary_text": "9465 is for individuals (1040 income tax, TFRP, defunct-sole-prop employment tax, SRP). Don't file when payable within 180 days ($0 short-term plan, OPA <= $100,000), when applying via OPA (<= $50,000, cheaper), when the business still operates, or in bankruptcy/OIC. Unfiled returns = denial; refunds offset regardless.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "Line 12 + lines 13a/13b/13c + Part II spouse lines + where-to-file (i9465 7-2024 verbatim substance)",
            "excerpt_text": (
                "Line 12: you can choose the day of each month your payment is due. This can be on or after "
                "the 1st of the month, but no later than the 28th of the month. Line 13a: the routing number "
                "must be nine digits; the first two digits of the routing number must be 01 through 12 or 21 "
                "through 32. Line 13b: the account number can be up to 17 characters (both numbers and "
                "letters). The direct debit from your checking account won't be approved unless you (and your "
                "spouse if filing a joint return) sign Form 9465. Line 13c: low-income taxpayers who are "
                "unable to make electronic payments through a DDIA... are eligible to receive reimbursement of "
                "their installment agreement user fees... If you don't check the box on line 13c (and don't "
                "provide the information on lines 13a and 13b), you're indicating that you're able but "
                "choosing not to make electronic payments by establishing a DDIA; as such, your user fee is "
                "not eligible for reimbursement. Lines 21 and 22: complete... if you are married and meet "
                "either of the following conditions: you live with and share household expenses with your "
                "spouse; you live in a community property state. You should complete lines 21 and 22 whether "
                "your filing status is married filing jointly or married filing separately. Where To File: "
                "attach Form 9465 to the front of your return... If you have already filed your return or "
                "you're filing this form in response to a notice, file Form 9465 by itself with the Internal "
                "Revenue Service Center using the address in the table that applies to you [two charts keyed "
                "on Schedule C/E/F presence, plus the foreign/territory Austin address — e.g. without C/E/F "
                "Georgia files at Doraville GA (P.O. Box 47421, Stop 74); with C/E/F Georgia files at Memphis "
                "TN (P.O. Box 69, Stop 811); foreign/APO/FPO/2555/4563/dual-status -> Austin TX 3651 South "
                "I-H 35, 5501AUSC]."
            ),
            "summary_text": "Day 1-28; RTN 9 digits prefix 01-12/21-32; account <= 17 chars; joint DD needs BOTH signatures; 13c reimbursement vs able-but-choosing-not-to; spouse lines 21/22 when sharing expenses or community property (MFJ or MFS); where-to-file charts keyed on Schedule C/E/F (year-watched).",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "IRS_PAYPLAN", "source_type": "official_guidance", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "IRS.gov — Payment plans; installment agreements (live fee page)",
        "citation": "irs.gov/payments/payment-plans-installment-agreements (page reviewed 28-Jun-2026; fetched 2026-07-13)",
        "issuer": "Internal Revenue Service",
        "official_url": "https://www.irs.gov/payments/payment-plans-installment-agreements",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.0, "topics": ["ia_9465"],
        "excerpts": [{
            "excerpt_label": "Live fee confirmation (page reviewed 28-Jun-2026 — the year-key check)",
            "excerpt_text": (
                "Long-term payment plan (installment agreement) setup fees as shown on the live page: direct "
                "debit $22 online / $107 by phone, mail or in-person; non-direct-debit $69 online / $178 by "
                "phone, mail or in-person. Low-income: direct-debit setup fee waived; non-direct-debit $43 "
                "setup fee which may be reimbursed if certain conditions are met. Short-term plan (180 days "
                "or less): $0 setup fee; apply online when you owe less than $100,000 in combined tax, "
                "penalties and interest. Long-term online threshold: $50,000 or less in combined tax, "
                "penalties and interest. Revising an existing plan: $10 online; $89 by phone/mail/in-person "
                "($43 low-income, may be reimbursed). CHECKED 2026-07-13 against T.D. 10045 (91 FR 20902, "
                "Apr. 20, 2026, amending 26 CFR Part 300): the installment-agreement fees are unchanged — "
                "the printed i9465 (7-2024) table remains current. YEAR-KEYED: re-verify each January."
            ),
            "summary_text": "The live IRS fee page (reviewed 28-Jun-2026) confirms the July-2024 schedule stands in July 2026; T.D. 10045 (Apr-2026 Part-300 amendment) did not touch IA fees. Year-keyed watch.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "MEF_9465_BR", "source_type": "official_guidance", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "MeF 1040 Business Rules TY2025v5.3 — the F9465-* family",
        "citation": "1040_Business_Rules_2025v5.3.csv (IRS MeF package; IRS9465 rides ReturnData1040, InstallmentAgreement family)",
        "issuer": "Internal Revenue Service",
        "official_url": "https://www.irs.gov/e-file-providers/modernized-e-file-mef-schemas-and-business-rules",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.0, "topics": ["ia_9465"],
        "excerpts": [{
            "excerpt_label": "F9465 e-file gate rules (TY2025v5.3 CSV verbatim substance, Active only)",
            "excerpt_text": (
                "F9465-001-03: Form 9465 may not be filed electronically when 'TotalTaxDueAmt' is greater "
                "than 50000 (complete Form 9465 and Form 433-F on paper). F9465-014/-015: line 1 SSNs must "
                "match the return header. F9465-016-01/-017-01: routing and account numbers must both be "
                "present when either is. F9465-018-01: one of home/work phone (domestic or foreign) must have "
                "a value. F9465-019-02: if IRS Payment Record is present in the return, then Form 9465 "
                "'PaymentAmt' must be equal to 'PaymentAmt' in IRS Payment Record. F9465-026-01: not "
                "e-fileable when 'PayrollDeductionAgreementInd' is checked (Form 9465 + Form 2159 on paper). "
                "F9465-027-01: not e-fileable when 'PaymentDueAmt' is less than 'CalculatedMonthlyPymtAmt' "
                "(check the box below line 11b, attach 433-F, mail). F9465-029-02/-030-02/-038-02: attached "
                "to a 1040, 'F9465TaxReturnTypeCd' must not be an employment/excise form; a 1040-type code "
                "requires 'IATaxYrDt' and forbids 'TaxPeriodDetailGrp'. F9465-037-01: "
                "'CanNotIncreasePaymentInd' must not be checked in e-file. F9465-039-01: not e-fileable when "
                "'RevisedMonthlyPaymentAmt' has a value less than 'CalculatedMonthlyPymtAmt'. F9465-040: if "
                "'RoutingTransitNum' has a value, 'NoElectronicPaymentInd' must not be checked. F9465-041: "
                "'TotalBalanceDueAmt' must not be less than 'TaxDueAmt' + 'AdditionalBalanceDueAmt'. "
                "F9465-042: revised >= calculated -> can't-increase must not be checked. F9465-043: "
                "'PaymentDueAmt' and 'RevisedMonthlyPaymentAmt' must not be equal. F9465-044: 'TotalTaxDueAmt' "
                "between 25000 and 50000 with a payment >= calculated requires routing+account values or the "
                "payroll-deduction box (and payroll can't transmit, so the e-file path is direct debit)."
            ),
            "summary_text": "The complete Active F9465-* reject set: the $50k cap, payroll/can't-increase/below-minimum paper-only arms, phone + RTN/account pairing, 13c-vs-routing, 11a != 11b, the 25k-50k DD band, and the EFW tie (line 8 == IRSPayment PaymentAmt).",
            "is_key_excerpt": True,
        }],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_F9465", "9465", "governs"), ("IRS_I9465", "9465", "governs"),
    ("IRS_PAYPLAN", "9465", "governs"), ("MEF_9465_BR", "9465", "governs"),
]


F9465_FACTS: list[dict] = [
    {"fact_key": "request_form_types", "label": "Header — this request is for Form(s) (e.g., 'Form 1040'; employment forms only for a no-longer-operating sole prop)", "data_type": "string", "required": False, "sort_order": 1},
    {"fact_key": "tax_years_periods", "label": "Header — tax year(s) or period(s) involved (e.g., '2025')", "data_type": "string", "required": False, "sort_order": 2},
    {"fact_key": "new_address", "label": "L1b — address is new since the last return (checkbox)", "data_type": "boolean", "required": False, "sort_order": 3},
    {"fact_key": "defunct_business_name", "label": "L2 — business name (must no longer be operating)", "data_type": "string", "required": False, "sort_order": 4},
    {"fact_key": "defunct_business_ein", "label": "L2 — business EIN", "data_type": "string", "required": False, "sort_order": 5},
    {"fact_key": "home_phone", "label": "L3 — home phone + best time to call (one of L3/L4 REQUIRED in e-file)", "data_type": "string", "required": False, "sort_order": 6},
    {"fact_key": "work_phone", "label": "L4 — work phone + ext + best time to call", "data_type": "string", "required": False, "sort_order": 7},
    {"fact_key": "amount_owed_returns", "label": "L5 — total owed per tax return(s)/notice(s) (may span years)", "data_type": "decimal", "required": False, "sort_order": 8},
    {"fact_key": "additional_balances", "label": "L6 — additional balances due not on L5 (even if inside an existing IA)", "data_type": "decimal", "required": False, "sort_order": 9},
    {"fact_key": "payment_with_request", "label": "L8 — payment made with this request (MUST equal the EFW payment record amount when one rides the return — F9465-019-02)", "data_type": "decimal", "required": False, "sort_order": 10},
    {"fact_key": "proposed_monthly_payment", "label": "L11a — proposed monthly payment (blank -> the IRS divides line 9 by 72)", "data_type": "decimal", "required": False, "sort_order": 11},
    {"fact_key": "revised_monthly_payment", "label": "L11b — revised monthly payment (when 11a < line 10 and it can be raised to >= line 10)", "data_type": "decimal", "required": False, "sort_order": 12},
    {"fact_key": "cannot_increase_payment", "label": "L11b checkbox — can't raise the payment to line 10 (attach Form 433-F; NOT e-fileable)", "data_type": "boolean", "required": False, "sort_order": 13},
    {"fact_key": "payment_day", "label": "L12 — monthly payment day (1-28)", "data_type": "integer", "required": False, "sort_order": 14},
    {"fact_key": "dd_routing_number", "label": "L13a — direct-debit routing number (9 digits, prefix 01-12/21-32)", "data_type": "string", "required": False, "sort_order": 15},
    {"fact_key": "dd_account_number", "label": "L13b — direct-debit account number (<= 17 chars)", "data_type": "string", "required": False, "sort_order": 16},
    {"fact_key": "low_income_no_dd", "label": "L13c — low-income, unable to debit-instrument: fee reimbursed on completion (conflicts with 13a in e-file)", "data_type": "boolean", "required": False, "sort_order": 17},
    {"fact_key": "payroll_deduction", "label": "L14 — payroll deduction (attach Form 2159; NOT e-fileable)", "data_type": "boolean", "required": False, "sort_order": 18},
    {"fact_key": "is_low_income", "label": "Low-income taxpayer (AGI <= 250% federal poverty guidelines, most recent year; Form 13844)", "data_type": "boolean", "required": False, "sort_order": 19},
    {"fact_key": "applied_online", "label": "Applied through the Online Payment Agreement (fee tier; the suite files 9465 — OPA is preparer guidance)", "data_type": "boolean", "required": False, "sort_order": 20},
    {"fact_key": "defaulted_ia_past_12mo", "label": "Defaulted on an installment agreement within the past 12 months (Part II condition 1)", "data_type": "boolean", "required": False, "sort_order": 21},
    {"fact_key": "five_year_compliant", "label": "Guaranteed-IA: past 5 years all returns timely filed/paid, no prior income-tax IA (both spouses if joint)", "data_type": "boolean", "required": False, "sort_order": 22},
    {"fact_key": "agrees_full_pay_3yr", "label": "Guaranteed-IA: agrees to pay in full within 3 years + comply while in effect", "data_type": "boolean", "required": False, "sort_order": 23},
    {"fact_key": "unable_to_pay_full", "label": "Guaranteed-IA: financially unable to pay the liability in full when due", "data_type": "boolean", "required": False, "sort_order": 24},
    {"fact_key": "efw_payment_amount", "label": "EFW payment record amount riding the same return (IRSPayment 'PaymentAmt'; None when no record)", "data_type": "decimal", "required": False, "sort_order": 25},
    {"fact_key": "residence_county", "label": "L15 — county of primary residence (Part II)", "data_type": "string", "required": False, "sort_order": 26},
    {"fact_key": "marital_status_married", "label": "L16a — married (single skips 16b)", "data_type": "boolean", "required": False, "sort_order": 27},
    {"fact_key": "shares_household_expenses", "label": "L16b — shares household expenses with spouse", "data_type": "boolean", "required": False, "sort_order": 28},
    {"fact_key": "community_property_state", "label": "Community-property state resident (L21/22 gate arm)", "data_type": "boolean", "required": False, "sort_order": 29},
    {"fact_key": "dependents_count", "label": "L17 — dependents claimable this year", "data_type": "integer", "required": False, "sort_order": 30},
    {"fact_key": "age65_count", "label": "L18 — household members 65 or older", "data_type": "integer", "required": False, "sort_order": 31},
    {"fact_key": "pay_frequency", "label": "L19 — taxpayer pay frequency", "data_type": "choice", "required": False, "sort_order": 32,
     "choices": ["weekly", "biweekly", "monthly", "semimonthly"]},
    {"fact_key": "net_income_per_period", "label": "L20 — taxpayer net income per pay period (take-home)", "data_type": "decimal", "required": False, "sort_order": 33},
    {"fact_key": "spouse_pay_frequency", "label": "L21 — spouse pay frequency (only when the spouse-lines gate holds)", "data_type": "choice", "required": False, "sort_order": 34,
     "choices": ["weekly", "biweekly", "monthly", "semimonthly"]},
    {"fact_key": "spouse_net_income", "label": "L22 — spouse net income per pay period", "data_type": "decimal", "required": False, "sort_order": 35},
    {"fact_key": "vehicles_count", "label": "L23 — vehicles owned", "data_type": "integer", "required": False, "sort_order": 36},
    {"fact_key": "car_payments_count", "label": "L24 — car payments per month", "data_type": "integer", "required": False, "sort_order": 37},
    {"fact_key": "health_insurance", "label": "L25a — has health insurance", "data_type": "boolean", "required": False, "sort_order": 38},
    {"fact_key": "premiums_deducted", "label": "L25b — premiums deducted from paycheck", "data_type": "boolean", "required": False, "sort_order": 39},
    {"fact_key": "monthly_premium", "label": "L25c — monthly health insurance premium (when not paycheck-deducted)", "data_type": "decimal", "required": False, "sort_order": 40},
    {"fact_key": "court_ordered_payments", "label": "L26a — makes court-ordered payments", "data_type": "boolean", "required": False, "sort_order": 41},
    {"fact_key": "court_payments_deducted", "label": "L26b — court-ordered payments deducted from paycheck", "data_type": "boolean", "required": False, "sort_order": 42},
    {"fact_key": "monthly_court_payment", "label": "L26c — court-ordered payments per month (when not deducted)", "data_type": "decimal", "required": False, "sort_order": 43},
    {"fact_key": "child_care_monthly", "label": "L27 — child/dependent care per month (excl. court-ordered support)", "data_type": "decimal", "required": False, "sort_order": 44},
    {"fact_key": "has_schedule_cef", "label": "Any request year filed Schedule C/E/F (selects the standalone where-to-file chart)", "data_type": "boolean", "required": False, "sort_order": 45},
    {"fact_key": "filed_with_return", "label": "Filed attached to the front of the return (vs standalone/notice response)", "data_type": "boolean", "required": False, "sort_order": 46},
]

F9465_RULES: list[dict] = [
    {"rule_id": "R-9465-WHO", "title": "Who files / who doesn't (OPA, short-term, bankruptcy/OIC boundaries)", "rule_type": "routing",
     "formula": "9465 = individuals: 1040 income tax / TFRP / defunct-sole-prop employment tax (941, 943, 940) / ACA SRP. DON'T file when: payable in full within 180 days (short-term plan $0 fee, OPA when < $100,000); applying via OPA (balance <= $50,000, lower fee); business still operating with employment/unemployment tax; bankruptcy or pending/accepted OIC. Unfiled required returns -> request denied; refunds offset regardless",
     "inputs": ["request_form_types", "amount_owed_returns"], "outputs": ["form_routing"], "sort_order": 1,
     "description": "W2. Purpose + boundaries (i9465 Who should/shouldn't use). The OPA tip is preparer guidance the app surfaces as an info diagnostic — the suite itself files the 9465 with the return or prints it."},
    {"rule_id": "R-9465-CALC", "title": "Face math: 7 = 5+6, 9 = 7-8, day 1-28", "rule_type": "calculation",
     "formula": "L7 = L5 + L6; L9 = L7 - L8; L12 payment day >= 1 and <= 28. MeF: TotalBalanceDueAmt >= TaxDueAmt + AdditionalBalanceDueAmt (F9465-041)",
     "inputs": ["amount_owed_returns", "additional_balances", "payment_with_request", "payment_day"],
     "outputs": ["total_balance_due", "amount_owed"], "sort_order": 2,
     "description": "W1. The addition/subtraction chain on the face plus the line-12 day window ('on or after the 1st... no later than the 28th')."},
    {"rule_id": "R-9465-MIN", "title": "Line 10 minimum payment (balance / 72, whole-dollar ceiling)", "rule_type": "calculation",
     "formula": "L10 = ceil(L9 / 72) in whole dollars (the face divides by 72.0 with no stated rounding; ceiling = the smallest whole-dollar payment satisfying full-pay-within-72-months, flagged W1). Blank 11a -> the IRS sets payment = L9 / 72. Streamlined proposals must full-pay within 72 months or by the CSED (10 years from assessment), whichever is less",
     "inputs": ["amount_owed_returns", "additional_balances", "payment_with_request"],
     "outputs": ["monthly_minimum"], "sort_order": 3,
     "description": "W1. The line-10 divisor and its role as the MeF CalculatedMonthlyPymtAmt gate (F9465-027-01/-039-01 compare against it)."},
    {"rule_id": "R-9465-TYPE", "title": "Agreement-type router: guaranteed / streamlined / 433-F paths", "rule_type": "routing",
     "formula": "guaranteed iff L9-basis owed <= 10000 AND five_year_compliant AND agrees_full_pay_3yr AND unable_to_pay_full. streamlined iff owed <= 25000, OR (25000 < owed <= 50000 AND (direct debit OR payroll deduction)). owed > 50000 -> attach Form 433-F (paper). 11a(/11b) < L10 and can't increase -> 433-F. Not full-pay by CSED -> PPIA (financial statement + reviews)",
     "inputs": ["amount_owed_returns", "five_year_compliant", "agrees_full_pay_3yr", "unable_to_pay_full", "dd_routing_number", "payroll_deduction"],
     "outputs": ["guaranteed_eligible", "streamlined_eligible"], "sort_order": 4,
     "description": "W2. The i9465 agreement tiers. Guaranteed = §6159(c) substance as printed; streamlined generally avoids a financial statement and an NFTL."},
    {"rule_id": "R-9465-EFILE", "title": "The MeF e-file gate (F9465-* Active reject arms)", "rule_type": "validation",
     "formula": "REFUSE e-file when: total owed > 50000 (001-03) / payroll_deduction (026-01) / cannot_increase (037-01) / effective payment < L10 (027-01 proposed, 039-01 revised) / no phone (018-01) / routing xor account (016/017) / routing AND 13c (040) / 25k-50k band with payment >= L10 but neither DD pair nor payroll (044). Also: 11a and 11b must not be equal (043); revised >= L10 forbids the can't-increase box (042); line 1 SSNs match the header (014/015); attached-to-1040 type code must be an income form + IATaxYrDt (029/030/038)",
     "inputs": ["amount_owed_returns", "additional_balances", "payroll_deduction", "cannot_increase_payment", "proposed_monthly_payment", "revised_monthly_payment", "home_phone", "work_phone", "dd_routing_number", "dd_account_number", "low_income_no_dd"],
     "outputs": ["efile_blockers"], "sort_order": 5,
     "description": "W3. Every arm is a published Active reject in the TY2025v5.3 CSV; the paper fallback is the form's own 433-F/2159 instruction text. Refusal beats fabrication: the tts extract refuses with the paper path named."},
    {"rule_id": "R-9465-EFW", "title": "EFW interplay: line 8 == IRS Payment Record amount", "rule_type": "reconciliation",
     "formula": "if an IRSPayment record is present in the return (the s76 EFW half), Form 9465 PaymentAmt (line 8) MUST equal the payment record's PaymentAmt (F9465-019-02); no record -> line 8 is the check/voucher payment sent with the request",
     "inputs": ["payment_with_request", "efw_payment_amount"], "outputs": ["efw_consistent"], "sort_order": 6,
     "description": "W3. The one cross-document tie: a 9465 riding a return with electronic-funds-withdrawal must show the SAME with-request payment both places."},
    {"rule_id": "R-9465-FEES", "title": "User-fee schedule (July-1-2024 table; YEAR-KEYED)", "rule_type": "calculation",
     "formula": "fee = OPA? (DD? 22 : 69) : payroll? 178 : (DD? 107 : 178). low-income (AGI <= 250% poverty, Form 13844): DDIA -> WAIVED (0); non-DD -> 43 reduced, REIMBURSED on completion when 13c (unable to DD). modify/terminate 89 (43 low-income; 10 via OPA reinstate/restructure). Verified current 2026-07-13 (live page reviewed 28-Jun-2026; T.D. 10045 checked)",
     "inputs": ["applied_online", "dd_routing_number", "is_low_income", "payroll_deduction", "low_income_no_dd"],
     "outputs": ["user_fee"], "sort_order": 7,
     "description": "W4. The July-2024 table with the low-income waiver ladder. YEAR-KEYED: re-verify each January against the live payments page (the s67 stale-fee class — Cornell's CFR text is 2016-era, do not cite it)."},
    {"rule_id": "R-9465-PART2", "title": "Part II three-condition gate + spouse lines", "rule_type": "validation",
     "formula": "Part II required iff ALL THREE: defaulted_ia_past_12mo AND 25000 < owed <= 50000 AND 11a(/11b) < L10. L21/22 (spouse) required iff married AND (shares_household_expenses OR community_property_state) — MFJ or MFS alike. owed > 50000 -> ALSO attach 433-F",
     "inputs": ["defaulted_ia_past_12mo", "amount_owed_returns", "proposed_monthly_payment", "revised_monthly_payment", "marital_status_married", "shares_household_expenses", "community_property_state"],
     "outputs": ["part2_required", "spouse_lines_required"], "sort_order": 8,
     "description": "W4. The page-2 gate verbatim ('complete this Part only if all three conditions below apply') and the lines-21/22 household-income rule."},
    {"rule_id": "R-9465-FILE", "title": "Filing route: front of the return, or the standalone chart", "rule_type": "routing",
     "formula": "with the return -> attach to the FRONT, address per the return booklet. standalone/notice -> the i9465 chart keyed on Schedule C/E/F presence in any request year (without C/E/F: Andover / Doraville GA / Kansas City; with C/E/F: Holtsville / Memphis TN / Ogden / Philadelphia; foreign, territory, APO/FPO, 2555/4563, dual-status -> Austin TX). Joint returns: BOTH spouses sign (direct debit won't be approved otherwise). Addresses YEAR-WATCHED",
     "inputs": ["filed_with_return", "has_schedule_cef"], "outputs": ["filing_route"], "sort_order": 9,
     "description": "W4. GA without C/E/F files at Doraville (P.O. Box 47421, Stop 74); GA with C/E/F files at Memphis (P.O. Box 69, Stop 811). E-filed 9465s ride the return itself — the chart is the print/standalone path."},
]

F9465_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-9465-WHO", "IRS_I9465", "primary", "Who should/shouldn't use + OPA/short-term alternatives"),
    ("R-9465-WHO", "IRS_PAYPLAN", "secondary", "Live OPA thresholds ($50k long / <$100k short-term)"),
    ("R-9465-CALC", "IRS_F9465", "primary", "Face lines 5-9 + the line-12 day window"),
    ("R-9465-CALC", "MEF_9465_BR", "secondary", "F9465-041 total-balance sum check"),
    ("R-9465-MIN", "IRS_F9465", "primary", "L10 divide-by-72.0 + the 11a/11b ladder"),
    ("R-9465-MIN", "IRS_I9465", "secondary", "72-month/CSED full-pay language"),
    ("R-9465-TYPE", "IRS_I9465", "primary", "Guaranteed/streamlined/PPIA criteria verbatim"),
    ("R-9465-EFILE", "MEF_9465_BR", "primary", "The Active F9465-* reject set"),
    ("R-9465-EFILE", "IRS_F9465", "secondary", "The face's own 433-F/2159 fallback bullets"),
    ("R-9465-EFW", "MEF_9465_BR", "primary", "F9465-019-02 PaymentAmt equality"),
    ("R-9465-FEES", "IRS_I9465", "primary", "July-1-2024 fee table + low-income waiver/reimbursement"),
    ("R-9465-FEES", "IRS_PAYPLAN", "primary", "Live-page fee confirmation (reviewed 28-Jun-2026)"),
    ("R-9465-PART2", "IRS_F9465", "primary", "Part II all-three-conditions banner"),
    ("R-9465-PART2", "IRS_I9465", "secondary", "Lines 21/22 shared-expenses / community-property rule"),
    ("R-9465-FILE", "IRS_I9465", "primary", "Where To File charts + attach-to-front"),
]

F9465_LINES: list[dict] = [
    # Header + Part I
    {"line_number": "HDR_FORMS", "description": "Header — request is for Form(s) (e.g. Form 1040)", "line_type": "input", "source_facts": ["request_form_types"], "sort_order": 1},
    {"line_number": "HDR_PERIODS", "description": "Header — tax year(s)/period(s) involved", "line_type": "input", "source_facts": ["tax_years_periods"], "sort_order": 2},
    {"line_number": "L1A", "description": "L1a — name(s)/SSN(s)/address (+foreign); joint = return order", "line_type": "input", "sort_order": 3},
    {"line_number": "L1B", "description": "L1b — new-address checkbox", "line_type": "input", "source_facts": ["new_address"], "sort_order": 4},
    {"line_number": "L2", "description": "L2 — defunct business name + EIN", "line_type": "input", "source_facts": ["defunct_business_name", "defunct_business_ein"], "sort_order": 5},
    {"line_number": "L3", "description": "L3 — home phone + best time (one of L3/L4 required in e-file)", "line_type": "input", "source_facts": ["home_phone"], "sort_order": 6},
    {"line_number": "L4", "description": "L4 — work phone + ext + best time", "line_type": "input", "source_facts": ["work_phone"], "sort_order": 7},
    {"line_number": "L5", "description": "L5 — total owed per return(s)/notice(s)", "line_type": "input", "source_facts": ["amount_owed_returns"], "sort_order": 8},
    {"line_number": "L6", "description": "L6 — additional balances due", "line_type": "input", "source_facts": ["additional_balances"], "sort_order": 9},
    {"line_number": "L7", "description": "L7 — add lines 5 and 6", "line_type": "calculated", "source_rules": ["R-9465-CALC"], "sort_order": 10},
    {"line_number": "L8", "description": "L8 — payment with this request (== the EFW record amount when present)", "line_type": "input", "source_facts": ["payment_with_request"], "source_rules": ["R-9465-EFW"], "sort_order": 11},
    {"line_number": "L9", "description": "L9 — amount owed (L7 - L8)", "line_type": "calculated", "source_rules": ["R-9465-CALC"], "sort_order": 12},
    {"line_number": "L10", "description": "L10 — L9 / 72 (the minimum-payment gate; whole-dollar ceiling convention)", "line_type": "calculated", "source_rules": ["R-9465-MIN"], "sort_order": 13},
    {"line_number": "L11A", "description": "L11a — proposed monthly payment", "line_type": "input", "source_facts": ["proposed_monthly_payment"], "sort_order": 14},
    {"line_number": "L11B", "description": "L11b — revised monthly payment (>= L10)", "line_type": "input", "source_facts": ["revised_monthly_payment"], "sort_order": 15},
    {"line_number": "L11B_CHK", "description": "L11b checkbox — can't increase to L10 (433-F; not e-fileable)", "line_type": "input", "source_facts": ["cannot_increase_payment"], "source_rules": ["R-9465-EFILE"], "sort_order": 16},
    {"line_number": "L12", "description": "L12 — monthly payment day (1-28)", "line_type": "input", "source_facts": ["payment_day"], "sort_order": 17},
    {"line_number": "L13A", "description": "L13a — routing number (9-digit, prefix 01-12/21-32)", "line_type": "input", "source_facts": ["dd_routing_number"], "sort_order": 18},
    {"line_number": "L13B", "description": "L13b — account number (<= 17 chars)", "line_type": "input", "source_facts": ["dd_account_number"], "sort_order": 19},
    {"line_number": "L13C", "description": "L13c — low-income unable-to-DD reimbursement box", "line_type": "input", "source_facts": ["low_income_no_dd"], "sort_order": 20},
    {"line_number": "L14", "description": "L14 — payroll deduction (Form 2159; not e-fileable)", "line_type": "input", "source_facts": ["payroll_deduction"], "sort_order": 21},
    {"line_number": "SIGN", "description": "Signature(s) — joint returns BOTH sign (DD not approved otherwise)", "line_type": "input", "sort_order": 22},
    # Part II
    {"line_number": "L15", "description": "L15 — county of primary residence", "line_type": "input", "source_facts": ["residence_county"], "sort_order": 23},
    {"line_number": "L16A", "description": "L16a — marital status (single skips 16b)", "line_type": "input", "source_facts": ["marital_status_married"], "sort_order": 24},
    {"line_number": "L16B", "description": "L16b — share household expenses with spouse", "line_type": "input", "source_facts": ["shares_household_expenses"], "sort_order": 25},
    {"line_number": "L17", "description": "L17 — dependents claimable", "line_type": "input", "source_facts": ["dependents_count"], "sort_order": 26},
    {"line_number": "L18", "description": "L18 — household members 65+", "line_type": "input", "source_facts": ["age65_count"], "sort_order": 27},
    {"line_number": "L19", "description": "L19 — pay frequency", "line_type": "input", "source_facts": ["pay_frequency"], "sort_order": 28},
    {"line_number": "L20", "description": "L20 — net income per pay period", "line_type": "input", "source_facts": ["net_income_per_period"], "sort_order": 29},
    {"line_number": "L21", "description": "L21 — spouse pay frequency (gated)", "line_type": "input", "source_facts": ["spouse_pay_frequency"], "source_rules": ["R-9465-PART2"], "sort_order": 30},
    {"line_number": "L22", "description": "L22 — spouse net income per pay period (gated)", "line_type": "input", "source_facts": ["spouse_net_income"], "sort_order": 31},
    {"line_number": "L23", "description": "L23 — vehicles owned", "line_type": "input", "source_facts": ["vehicles_count"], "sort_order": 32},
    {"line_number": "L24", "description": "L24 — car payments per month", "line_type": "input", "source_facts": ["car_payments_count"], "sort_order": 33},
    {"line_number": "L25A", "description": "L25a — health insurance y/n", "line_type": "input", "source_facts": ["health_insurance"], "sort_order": 34},
    {"line_number": "L25B", "description": "L25b — premiums paycheck-deducted y/n", "line_type": "input", "source_facts": ["premiums_deducted"], "sort_order": 35},
    {"line_number": "L25C", "description": "L25c — monthly premium", "line_type": "input", "source_facts": ["monthly_premium"], "sort_order": 36},
    {"line_number": "L26A", "description": "L26a — court-ordered payments y/n", "line_type": "input", "source_facts": ["court_ordered_payments"], "sort_order": 37},
    {"line_number": "L26B", "description": "L26b — court payments paycheck-deducted y/n", "line_type": "input", "source_facts": ["court_payments_deducted"], "sort_order": 38},
    {"line_number": "L26C", "description": "L26c — monthly court-ordered payment", "line_type": "input", "source_facts": ["monthly_court_payment"], "sort_order": 39},
    {"line_number": "L27", "description": "L27 — monthly child/dependent care (excl. court-ordered support)", "line_type": "input", "source_facts": ["child_care_monthly"], "sort_order": 40},
    # Computed
    {"line_number": "CALC_TYPE", "description": "Computed agreement tier (guaranteed / streamlined / 433-F path)", "line_type": "calculated", "source_rules": ["R-9465-TYPE"], "sort_order": 41},
    {"line_number": "CALC_EFILE", "description": "Computed e-file eligibility (empty blocker list = transmittable)", "line_type": "calculated", "source_rules": ["R-9465-EFILE"], "sort_order": 42},
    {"line_number": "CALC_EFW", "description": "Computed EFW consistency (L8 == IRSPayment PaymentAmt)", "line_type": "calculated", "source_rules": ["R-9465-EFW"], "sort_order": 43},
    {"line_number": "CALC_FEE", "description": "Computed user fee (July-2024 schedule; year-keyed)", "line_type": "calculated", "source_rules": ["R-9465-FEES"], "sort_order": 44},
    {"line_number": "CALC_PART2", "description": "Computed Part II requirement (three-condition gate)", "line_type": "calculated", "source_rules": ["R-9465-PART2"], "sort_order": 45},
    {"line_number": "CALC_ROUTE", "description": "Computed filing route (with-return / standalone chart / Austin)", "line_type": "calculated", "source_rules": ["R-9465-FILE"], "sort_order": 46},
]

F9465_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_9465_EFILE50", "title": "Balance over $50,000 — not e-fileable; attach Form 433-F", "severity": "error",
     "condition": "L7 total balance > 50000",
     "message": "Form 9465 may not be filed electronically when the total tax due is greater than $50,000 (MeF F9465-001-03). Complete Form 9465 and Form 433-F, Collection Information Statement, on paper and mail them to the address for your state (see the i9465 Where To File chart).", "notes": "W3. Also the face bullet: line 9 > $50,000 -> attach 433-F."},
    {"diagnostic_id": "D_9465_PAYROLL", "title": "Payroll deduction (box 14) — not e-fileable; attach Form 2159", "severity": "error",
     "condition": "payroll_deduction and e-filing",
     "message": "Form 9465 may not be filed electronically when the payroll-deduction box is checked (MeF F9465-026-01). Complete Form 9465 and Form 2159, Payroll Deduction Agreement (employer signs its portion), on paper and mail them per the Where To File chart.", "notes": "W3."},
    {"diagnostic_id": "D_9465_BELOWMIN", "title": "Proposed payment below the line-10 minimum", "severity": "error",
     "condition": "effective payment (11b else 11a) < line 10",
     "message": "The proposed monthly payment is less than line 10 (the balance divided by 72). E-file rejects this (MeF F9465-027-01/-039-01). Raise line 11a — or enter a revised amount >= line 10 on line 11b — or check the box below line 11b, attach Form 433-F, and file on paper.", "notes": "W1/W3."},
    {"diagnostic_id": "D_9465_NOINCR", "title": "Can't-increase box checked — paper only with Form 433-F", "severity": "error",
     "condition": "cannot_increase_payment",
     "message": "The box below line 11b ('you can't increase your payment to the line-10 amount') makes the request non-e-fileable (MeF F9465-037-01). Complete and attach Form 433-F and mail the request. If a revised payment >= line 10 is entered, the box must NOT be checked (F9465-042).", "notes": "W3."},
    {"diagnostic_id": "D_9465_DDBAND", "title": "$25,001-$50,000 owed — direct debit or payroll deduction required", "severity": "error",
     "condition": "25000 < owed <= 50000 and neither 13a/13b nor box 14",
     "message": "To qualify for a streamlined agreement with a balance over $25,000 but not more than $50,000, you must either complete lines 13a/13b (direct debit) or check box 14 (payroll deduction, Form 2159) — otherwise complete Form 433-F. In e-file the band is direct-debit-only, because payroll-deduction requests can't transmit (MeF F9465-044 + F9465-026-01).", "notes": "W2/W3."},
    {"diagnostic_id": "D_9465_PHONE", "title": "No phone number — e-file requires one", "severity": "error",
     "condition": "neither home nor work phone",
     "message": "One of line 3 (home) or line 4 (work) phone must have a value for an e-filed Form 9465 (MeF F9465-018-01).", "notes": "W3."},
    {"diagnostic_id": "D_9465_DDPAIR", "title": "Routing/account must pair (13a/13b)", "severity": "error",
     "condition": "exactly one of 13a/13b present",
     "message": "Lines 13a and 13b work together: a routing number without an account number (or vice versa) rejects in e-file (MeF F9465-016-01/-017-01). The routing number is nine digits with prefix 01-12 or 21-32; the account number is up to 17 characters.", "notes": "W3."},
    {"diagnostic_id": "D_9465_13CDD", "title": "Line 13c conflicts with banking info", "severity": "error",
     "condition": "low_income_no_dd and dd_routing_number present",
     "message": "Line 13c declares you're UNABLE to make electronic payments through a debit instrument — it can't be checked when lines 13a/13b carry banking information (MeF F9465-040). Choose one: direct debit (13a/13b) or the low-income reimbursement path (13c).", "notes": "W3/W4."},
    {"diagnostic_id": "D_9465_REVEQ", "title": "Lines 11a and 11b must differ", "severity": "error",
     "condition": "11a nonzero and 11b nonzero and equal",
     "message": "Line 11b is a REVISED payment — when both 11a and 11b have values they must not be equal (MeF F9465-043). Leave 11b blank unless raising the proposal to meet line 10.", "notes": "W3."},
    {"diagnostic_id": "D_9465_DAY28", "title": "Payment day after the 28th", "severity": "error",
     "condition": "payment_day > 28 or < 1",
     "message": "Line 12: the monthly payment date can be on or after the 1st of the month but no later than the 28th.", "notes": "W1."},
    {"diagnostic_id": "D_9465_EFWMATCH", "title": "Line 8 must equal the EFW payment record", "severity": "error",
     "condition": "IRSPayment record present and line 8 != its PaymentAmt",
     "message": "This return carries an electronic-funds-withdrawal payment record. Form 9465 line 8 ('payment you're making with this request') must EQUAL the payment record's amount (MeF F9465-019-02) — align the 9465 with the Payments-tab EFW amount, or remove one of them.", "notes": "W3. The s76 IRSPayment interplay."},
    {"diagnostic_id": "D_9465_PART2", "title": "Part II (page 2) required — all three conditions met", "severity": "warning",
     "condition": "defaulted within 12 months AND 25000 < owed <= 50000 AND payment below line 10",
     "message": "Complete Part II: you defaulted on an installment agreement in the past 12 months, owe more than $25,000 but not more than $50,000, and the line-11a/11b amount is less than line 10. Lines 15-27 collect the household financial detail; lines 21/22 (spouse) apply when you share household expenses or live in a community-property state (MFJ or MFS).", "notes": "W4."},
    {"diagnostic_id": "D_9465_OPA", "title": "Online Payment Agreement is cheaper", "severity": "info",
     "condition": "balance <= 50000 (or short-term-payable)",
     "message": "Balances of $50,000 or less can be set up online at IRS.gov/OPA for a lower fee ($22 direct debit / $69 otherwise, vs $107/$178 by form). If the client can pay in full within 180 days and owes less than $100,000, a short-term plan has NO setup fee. Filing the 9465 is still correct when the client wants the agreement requested with the return.", "notes": "W2/W4. Fee table year-keyed."},
    {"diagnostic_id": "D_9465_GUAR", "title": "Guaranteed installment agreement (<= $10,000)", "severity": "info",
     "condition": "owed <= 10000 and compliance conditions attested",
     "message": "The IRS MUST accept this agreement (guaranteed IA): balance <= $10,000, all returns timely filed/paid over the past 5 years with no prior income-tax installment agreement, full payment within 3 years, and inability to pay in full when due. No NFTL is generally filed.", "notes": "W2."},
    {"diagnostic_id": "D_9465_FEE", "title": "User fee summary (year-keyed)", "severity": "info",
     "condition": "informational on print/e-file",
     "message": "Setup fee (July-2024 schedule, verified current Jul-2026): $107 with direct debit / $178 otherwise when filing Form 9465 ($22/$69 via OPA). Low-income taxpayers (AGI <= 250% of the federal poverty guidelines; Form 13844): the fee is WAIVED with direct debit, or reduced to $43 — reimbursed on completion when line 13c is checked. Payroll-deduction agreements cost $178. Interest and the late-payment penalty continue to accrue during the agreement.", "notes": "W4. Re-verify each January (26 CFR 300; the live payments page)."},
    {"diagnostic_id": "D_9465_JOINTSIGN", "title": "Joint return — both spouses must sign", "severity": "warning",
     "condition": "joint return with direct debit or filing",
     "message": "On a joint return BOTH spouses sign Form 9465 — the direct debit won't be approved without both signatures.", "notes": "W4."},
    {"diagnostic_id": "D_9465_ADDRESS", "title": "Standalone filing addresses (year-watched)", "severity": "info",
     "condition": "informational on standalone print",
     "message": "Filed WITH the return: attach Form 9465 to the FRONT. Filed standalone or in response to a notice: use the i9465 chart — keyed on whether any request year filed Schedule C/E/F (e.g., Georgia files at Doraville GA, P.O. Box 47421 Stop 74 without C/E/F, or Memphis TN, P.O. Box 69 Stop 811 with C/E/F); foreign/territory/APO-FPO/Form 2555/4563/dual-status file at Austin TX. Addresses may change — check IRS.gov/Form9465.", "notes": "W4. Year-watched."},
]

F9465_SCENARIOS: list[dict] = [
    {"scenario_name": "9465-A — guaranteed tier: $8,400 owed, $300/month, e-files clean", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"amount_owed_returns": 8400, "additional_balances": 0, "payment_with_request": 0,
                "proposed_monthly_payment": 300, "payment_day": 15, "home_phone": "706-555-0101",
                "five_year_compliant": True, "agrees_full_pay_3yr": True, "unable_to_pay_full": True},
     "expected_outputs": {"monthly_minimum": 117, "guaranteed_eligible": True, "efile_blockers": [], "user_fee": 178},
     "notes": "L10 = ceil(8400/72) = 117; $300 clears it. Guaranteed IA (<= $10k + compliance). No DD -> form-channel fee $178 (the OPA info diagnostic offers $69/$22)."},
    {"scenario_name": "9465-B — streamlined $30,000 with direct debit: e-files", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"amount_owed_returns": 30000, "proposed_monthly_payment": 500, "payment_day": 28,
                "home_phone": "706-555-0102", "dd_routing_number": "061000104", "dd_account_number": "123456789"},
     "expected_outputs": {"monthly_minimum": 417, "streamlined_eligible": True, "efile_blockers": [], "user_fee": 107},
     "notes": "ceil(30000/72) = 417; $500 clears. The $25,001-50,000 band with DD = streamlined; DD pair satisfies F9465-044; day 28 is the boundary-legal value."},
    {"scenario_name": "9465-C — $30,000 with no debit and no payroll: the band refuses", "scenario_type": "failure", "sort_order": 3,
     "inputs": {"amount_owed_returns": 30000, "proposed_monthly_payment": 500, "home_phone": "x"},
     "expected_outputs": {"streamlined_eligible": False, "efile_blockers": ["F9465-044"], "diagnostic": "D_9465_DDBAND"},
     "notes": "Over $25,000: streamlined needs DD or payroll; e-file needs the DD pair (payroll can't transmit). Paper alternative = 433-F or Form 2159."},
    {"scenario_name": "9465-D — $62,000 owed: paper + Form 433-F", "scenario_type": "failure", "sort_order": 4,
     "inputs": {"amount_owed_returns": 62000, "proposed_monthly_payment": 900, "home_phone": "x"},
     "expected_outputs": {"efile_blockers": ["F9465-001-03"], "diagnostic": "D_9465_EFILE50"},
     "notes": "F9465-001-03: > $50,000 never e-files; the face bullet adds the 433-F attachment."},
    {"scenario_name": "9465-E — 11a below line 10, revised 11b clears it", "scenario_type": "edge", "sort_order": 5,
     "inputs": {"amount_owed_returns": 30000, "proposed_monthly_payment": 300, "revised_monthly_payment": 450,
                "home_phone": "x", "dd_routing_number": "061000104", "dd_account_number": "123456789"},
     "expected_outputs": {"monthly_minimum": 417, "efile_blockers": []},
     "notes": "11a 300 < 417 but 11b 450 >= 417 -> transmittable; 450 != 300 satisfies F9465-043; a checked can't-increase box here would trip F9465-042."},
    {"scenario_name": "9465-F — can't-increase box: paper + 433-F", "scenario_type": "failure", "sort_order": 6,
     "inputs": {"amount_owed_returns": 30000, "proposed_monthly_payment": 300, "cannot_increase_payment": True, "home_phone": "x"},
     "expected_outputs": {"efile_blockers_contains": ["F9465-037-01"], "diagnostic": "D_9465_NOINCR"},
     "notes": "F9465-037-01 refuses the box outright; the below-minimum arm (027) rides along. Paper path: 433-F attached."},
    {"scenario_name": "9465-G — payroll deduction: paper + Form 2159", "scenario_type": "failure", "sort_order": 7,
     "inputs": {"amount_owed_returns": 12000, "proposed_monthly_payment": 400, "payroll_deduction": True, "home_phone": "x"},
     "expected_outputs": {"efile_blockers": ["F9465-026-01"], "user_fee": 178, "diagnostic": "D_9465_PAYROLL"},
     "notes": "Box 14 can never transmit; the fee for a Form 2159 payroll agreement is $178."},
    {"scenario_name": "9465-H — EFW interplay: line 8 must equal the IRSPayment amount", "scenario_type": "edge", "sort_order": 8,
     "inputs": {"amount_owed_returns": 9000, "payment_with_request": 1000, "efw_payment_amount": 1000,
                "proposed_monthly_payment": 200, "home_phone": "x"},
     "expected_outputs": {"efw_consistent": True, "monthly_minimum": 112},
     "notes": "F9465-019-02: with the s76 EFW record on the return, line 8 == PaymentAmt (1,000). L9 = 9000-1000 = 8000; L10 = ceil(8000/72) = 112. A mismatched line 8 -> D_9465_EFWMATCH."},
    {"scenario_name": "9465-I — Part II gate: defaulted + band + below-minimum", "scenario_type": "edge", "sort_order": 9,
     "inputs": {"defaulted_ia_past_12mo": True, "amount_owed_returns": 30000, "proposed_monthly_payment": 300},
     "expected_outputs": {"part2_required": True, "diagnostic": "D_9465_PART2"},
     "notes": "All three conditions hold (defaulted-12mo; 25k < owed <= 50k; 300 < 417). Any one absent -> Part II stays off (pinned in the harness)."},
    {"scenario_name": "9465-J — low-income fee ladder", "scenario_type": "edge", "sort_order": 10,
     "inputs": {"is_low_income": True, "amount_owed_returns": 6000, "proposed_monthly_payment": 100},
     "expected_outputs": {"user_fee_ddia": 0, "user_fee_no_dd": 43},
     "notes": "Low-income + DDIA -> fee WAIVED (0). Low-income without DD -> $43 reduced, reimbursed on completion when 13c is checked (unable to DD). Non-low-income OPA tiers pin 22/69 in the harness."},
]

FORMS: list[dict] = [
    {
        "identity": {"form_number": "9465", "form_title": "Form 9465 — Installment Agreement Request (Rev. 9-2020)",
                     "notes": "Payment-cluster batch order 1 (tts s77). Individuals: 1040 income tax / TFRP / defunct-sole-prop employment tax / SRP. Attach to the FRONT of the return, or standalone per the i9465 chart (year-watched; GA = Doraville without Sch C/E/F, Memphis with). HAS a MeF channel: IRS9465 rides ReturnData1040 (InstallmentAgreement family) — the tts leg = print + MeF document. Face math 5-10 (L10 = L9/72, whole-dollar-ceiling convention); the 11a/11b/can't-increase ladder; day 1-28; 13a/13b DD (joint = both sign) / 13c low-income reimbursement / 14 payroll (2159). E-file gate (Active F9465-*): <= $50,000, no payroll, no can't-increase, payment >= L10, phone required, DD pairing, 13c-vs-routing, 11a != 11b, the 25k-50k DD band, line 8 == IRSPayment PaymentAmt (F9465-019-02, the s76 EFW tie). Tiers: guaranteed (<= $10k + 5-yr compliance + 3-yr pay), streamlined (<= $25k, or 25k-50k w/ DD/payroll; 72-month/CSED), else 433-F/PPIA. Fees July-2024 (VERIFIED CURRENT 2026-07-13, YEAR-KEYED): OPA $22/$69, form $107/$178, payroll $178, low-income waived-DDIA/$43/13c-reimbursed; modify $89/$43/$10-OPA. Part II = the three-condition gate (defaulted-12mo + 25k-50k + below-minimum); L21/22 spouse gate. entity_types ['1040']."},
        "facts": F9465_FACTS, "rules": F9465_RULES, "rule_links": F9465_RULE_LINKS,
        "lines": F9465_LINES, "diagnostics": F9465_DIAGNOSTICS, "scenarios": F9465_SCENARIOS,
    },
]

# Staged DRAFT deliberately (the new-FAs-default-ACTIVE trap): the tts build leg activates + writes
# runners + refreshes the export-verbatim mirrors in ONE motion.
FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-9465-MIN", "title": "Line 10 minimum = whole-dollar ceiling of balance/72", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "draft", "sort_order": 1,
     "description": "monthly_minimum = ceil(line9 / 72) whole-dollar. Pins: 8400 -> 117; 30000 -> 417; 50000 -> 695; 8000 -> 112; 0 -> 0. The e-file gate compares the 11a/11b effective payment against it (F9465-027-01/-039-01).",
     "definition": {"rule": "R-9465-MIN", "check": "minimum == ceil(balance / 72); effective payment >= minimum for e-file"}},
    {"assertion_id": "FA-9465-EFILE", "title": "E-file gate refuses the paper-only arms", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "draft", "sort_order": 2,
     "description": "Blockers fire exactly per the Active F9465-* set: > $50,000 (001-03) / payroll box (026-01) / can't-increase (037-01) / below-minimum (027-01 or 039-01) / missing phone (018-01) / unpaired 13a-13b (016-01) / 13c with routing (040) / the 25k-50k no-DD band (044). Empty blocker list == transmittable.",
     "definition": {"rule": "R-9465-EFILE", "check": "extract refuses when any Active F9465-* arm trips; refusal names the paper path (433-F / 2159)"}},
    {"assertion_id": "FA-9465-EFW", "title": "Line 8 equals the IRSPayment record amount", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "draft", "sort_order": 3,
     "description": "When the return carries an IRS Payment Record (the s76 EFW half), Form 9465 PaymentAmt (line 8) must equal the record's PaymentAmt (F9465-019-02). Pins: (1000, 1000) consistent; (500, 1000) refuses; (anything, None) consistent.",
     "definition": {"rule": "R-9465-EFW", "check": "line8 == IRSPayment.PaymentAmt when the record exists"}},
]


class Command(BaseCommand):
    help = "Load the Form 9465 spec (Installment Agreement Request). Refuses to seed until READY_TO_SEED=True (Gate-1 W1-W4)."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad Form 9465 spec (Installment Agreement Request)\n"))
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
                "\nREFUSING TO SEED FORM 9465: not cleared.\n\n"
                "Gated until Ken approves the Gate-1 walk (W1 face math + the line-10 ceiling convention;\n"
                "W2 agreement-tier router; W3 the F9465-* e-file gate + the EFW PaymentAmt tie;\n"
                "W4 fee schedule (year-keyed) + Part II gate + where-to-file) and flips the sentinel.\n\n"
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
        self.stdout.write("Form 9465 loaded.")
        self.stdout.write(f"  9465: facts {len(F9465_FACTS)} / rules {len(F9465_RULES)} / lines {len(F9465_LINES)} / diag {len(F9465_DIAGNOSTICS)} / tests {len(F9465_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}")
        self.stdout.write("=" * 60)
