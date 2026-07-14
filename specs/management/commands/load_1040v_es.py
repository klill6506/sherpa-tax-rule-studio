"""Load the 1040-V / 1040-ES voucher-pair spec (1040-V 2025 · 1040-ES 2026).
Payment-cluster draft-to-gate batch order 3 (tts s77; plan filed tts REVIEW_QUEUE s76). Greenfield
(gaps re-confirmed 404 on 2026-07-13: lookup/1040V + lookup/1040ES).

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
The PAPER complements of the s76 EFW unit. Form 1040-V rides a check/money-order payment of the
TY2025 balance due; the 2026 Form 1040-ES vouchers carry quarterly estimates paid by check during
2026. Print-only — the electronic halves (IRSPayment / IRSESPayment) already e-file. The pair is
specced together because the load-bearing content is the same class: EXTERNALLY-DEFINED MAILING
ADDRESSES that go stale (the 2553 address-drift precedent), and this pair carries a THREE-WAY trap —
the V chart, the ES chart, and the return address are all different (GA: V -> Charlotte Box 1214,
ES -> Charlotte Box 1300; the ES package explicitly says never the Form-1040-instructions address).

v1 SCOPE — PROPOSED (Gate-1 walk W1-W4 AWAITING KEN; see f1040v_es_source_brief.md):
W1. 1040-V mechanics: check-payers only (online/EFW -> no voucher; an EFW-elected return SUPPRESSES
    the V — the double-payment guard); voucher lines 1-4; check-prep rules ($100M cap, no staples,
    payable-to, memo line, no cash by mail).
W2. 1040-ES required-annual-payment test as diagnostics: the $1,000 gate; smaller-of 90% expected
    vs 100%/110% prior (2025 AGI > $150,000 / $75,000 MFS); farmer-fisher 66-2/3% + the Jan-15 /
    Mar-1 alternatives; the no-prior-liability exception.
W3. Dates + voucher mechanics: Apr 15 / Jun 15 / Sep 15, 2026 + Jan 15, 2027 (Feb-1 full-pay skip;
    the SAME four dates the s76 IRSESPayment fixes per FPYMT-088-11 — a debited quarter suppresses
    its paper voucher); joint-voucher bars (NRA spouse / decree / different years / RDP-civil-union);
    the overpayment-credit box exclusion; postmark = USPS processing date.
W4. The THREE-WAY address charts (year-watched, pinned per state incl. both GA rows); USPS-only
    P.O.-box caution; Guam/USVI bona-fide split. entity_types ['1040']; print-only (both).

CARRIED [UNVERIFIED]: none — verbatim vs Form 1040-V (2025, Created 12/22/25) + Form 1040-ES (2026,
Feb 12, 2026). Year-watch: BOTH address charts, the $150,000/110% thresholds (statutory but
package-restated), the due-date calendar (weekend/holiday shifts), the cash-retail limit.

SAFETY GUARD — READY_TO_SEED stayed False until Gate-1 approval. APPROVED: Ken, 2026-07-14 (s83 approve-all, WO-28/29/30/31/32 together; walk recommendations adopted as filed).
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

READY_TO_SEED = True  # FLIPPED 2026-07-14 — Ken approved Gate-1 in-session (s83 approve-all across WO-28/29/30/31/32; recommendations adopted as filed).

FORM_JURISDICTION = "federal"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1040"]

# ── Verified constants (f1040v_es_source_brief.md) ──
ES_DUE_DATES = ("2026-04-15", "2026-06-15", "2026-09-15", "2027-01-15")  # = the s76 FPYMT-088-11 dates
ES_Q4_SKIP_FILE_BY = "2027-02-01"       # file the 2026 return by Feb 1, 2027 + pay in full -> skip Jan 15
ES_FARMER_FILE_BY = "2027-03-01"        # farmer/fisher: file by Mar 1, 2027 + pay in full -> no estimates
ES_OWE_GATE = 1_000                     # general rule (1): expected owe >= $1,000 after withholding/credits
SAFE_HARBOR_PCT = 0.90                  # general rule (2a)
PRIOR_YEAR_PCT = 1.00                   # general rule (2b)
PRIOR_YEAR_PCT_HIGH = 1.10              # 2025 AGI > $150,000 ($75,000 MFS-2026)
HIGH_AGI_THRESHOLD = 150_000
HIGH_AGI_THRESHOLD_MFS = 75_000
FARMER_PCT = 2.0 / 3.0                  # 66-2/3% replaces 90% for qualifying farmers/fishers
CHECK_MAX = 100_000_000                 # no single check >= $100 million
CASH_RETAIL_DAILY_MAX = 1_000           # retail cash option: $1,000/day/transaction (acipayonline.com)

# The three-way address trap (year-watched; GA pinned on BOTH charts).
V_ADDRESSES = {
    "south": "Internal Revenue Service, P.O. Box 1214, Charlotte, NC 28201-1214",       # AL FL GA LA MS NC SC TN TX
    "other": "Internal Revenue Service, P.O. Box 931000, Louisville, KY 40293-1000",
    "foreign": "Internal Revenue Service, P.O. Box 1303, Charlotte, NC 28201-1303",
}
V_SOUTH_STATES = {"AL", "FL", "GA", "LA", "MS", "NC", "SC", "TN", "TX"}
ES_ADDRESSES = {
    "west_south": "Internal Revenue Service, P.O. Box 1300, Charlotte, NC 28201-1300",
    "northeast_midwest": "Internal Revenue Service, P.O. Box 931100, Louisville, KY 40293-1100",
    "foreign": "Internal Revenue Service, P.O. Box 1303, Charlotte, NC 28201-1303",
    "guam_bona_fide": "Department of Revenue and Taxation, Government of Guam, P.O. Box 23607, GMF, GU 96921",
    "usvi_bona_fide": "Virgin Islands Bureau of Internal Revenue, 6115 Estate Smith Bay, Suite 225, St. Thomas, VI 00802",
}
ES_CHARLOTTE_STATES = {"AL", "AK", "AZ", "CA", "CO", "FL", "GA", "HI", "ID", "KS", "LA", "MI", "MS",
                       "MT", "NE", "NV", "NM", "NC", "ND", "OH", "OR", "PA", "SC", "SD", "TN", "TX",
                       "UT", "WA", "WY"}
ES_LOUISVILLE_STATES = {"AR", "CT", "DE", "DC", "IL", "IN", "IA", "KY", "ME", "MD", "MA", "MN", "MO",
                        "NH", "NJ", "NY", "OK", "RI", "VT", "VA", "WV", "WI"}


def _v_needed(balance_due, paying_by_check, efw_elected) -> bool:
    """1040-V rides ONLY a check/money-order payment of a balance due. Online payers 'don't complete
    this form', and an EFW-elected return (the s76 IRSPayment) suppresses the voucher — printing both
    invites a double payment."""
    return bool(float(balance_due or 0) > 0 and paying_by_check and not efw_elected)


def _v_address(state, is_foreign) -> str:
    """The 2025 1040-V chart (year-watched). GA -> Charlotte Box 1214."""
    if is_foreign:
        return V_ADDRESSES["foreign"]
    return V_ADDRESSES["south"] if str(state).upper() in V_SOUTH_STATES else V_ADDRESSES["other"]


def _es_address(state, is_foreign) -> str:
    """The 2026 1040-ES chart (year-watched) — NOT the V chart, NOT the return address.
    GA -> Charlotte Box 1300 (one P.O.-box digit from the V's 1214 — the drift trap)."""
    if is_foreign:
        return ES_ADDRESSES["foreign"]
    s = str(state).upper()
    if s in ES_CHARLOTTE_STATES:
        return ES_ADDRESSES["west_south"]
    if s in ES_LOUISVILLE_STATES:
        return ES_ADDRESSES["northeast_midwest"]
    return ES_ADDRESSES["foreign"]


def _required_annual_payment(expected_tax, prior_year_tax, prior_year_agi, mfs, farmer_fisher) -> float:
    """The general-rule (2) amount: the smaller of 90% (66-2/3% farmer/fisher) of the expected 2026
    tax, or 100% (110% when 2025 AGI exceeds $150,000 / $75,000 MFS; the 110% arm never applies to
    farmers/fishers) of the 2025 tax."""
    current_arm = float(expected_tax) * (FARMER_PCT if farmer_fisher else SAFE_HARBOR_PCT)
    threshold = HIGH_AGI_THRESHOLD_MFS if mfs else HIGH_AGI_THRESHOLD
    high = float(prior_year_agi) > threshold and not farmer_fisher
    prior_arm = float(prior_year_tax) * (PRIOR_YEAR_PCT_HIGH if high else PRIOR_YEAR_PCT)
    return min(current_arm, prior_arm)


def _estimates_required(expected_owe_after_wh, withholding_and_credits, rap, prior_year_no_liability) -> bool:
    """Estimates are required when BOTH: expected owe >= $1,000 AND withholding+credits < the
    required annual payment — unless the full-12-month no-2025-liability exception applies."""
    if prior_year_no_liability:
        return False
    return float(expected_owe_after_wh) >= ES_OWE_GATE and float(withholding_and_credits) < float(rap)


def _joint_voucher_barred(spouse_nra, divorce_decree, different_tax_years, rdp_civil_union) -> bool:
    """Joint estimated payments are barred: nonresident-alien spouse; separated under a decree of
    divorce or separate maintenance; different tax years; and RDP/civil-union partners can never pay
    jointly (not marriages under state law)."""
    return bool(spouse_nra or divorce_decree or different_tax_years or rdp_civil_union)


def _q4_skippable(files_2026_return_by_feb1, pays_full_balance_with_return) -> bool:
    """The Jan 15, 2027 payment is unnecessary when the 2026 return is filed by Feb 1, 2027 with the
    entire balance paid."""
    return bool(files_2026_return_by_feb1 and pays_full_balance_with_return)


def _voucher_amount(check_payment, overpayment_credited) -> float:
    """The voucher box carries ONLY the check amount — a credited prior-year overpayment reduces what
    must be sent but never appears in the box."""
    del overpayment_credited  # reduces the remittance upstream; never enters the box
    return float(check_payment or 0)


def _check_splits_required(amount) -> int:
    """No single check >= $100,000,000 — count the checks needed under the cap."""
    amt = float(amount or 0)
    if amt < CHECK_MAX:
        return 1
    n = int(amt // (CHECK_MAX - 1)) + (1 if amt % (CHECK_MAX - 1) else 0)
    return max(n, 2)


AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("vouchers_1040", "1040-V / 1040-ES payment vouchers: check-only mechanics, the EFW/ES-debit "
     "suppression ties, the required-annual-payment test, due dates, joint-voucher bars, and the "
     "three-way year-watched address charts."),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_F1040V", "source_type": "federal_form", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Form 1040-V (2025) — Payment Voucher for Individuals",
        "citation": "Form 1040-V (2025), Cat. No. 20975C, OMB 1545-0074 (Created 12/22/25)",
        "issuer": "Internal Revenue Service", "official_url": "https://www.irs.gov/pub/irs-pdf/f1040v.pdf",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.5, "topics": ["vouchers_1040"],
        "excerpts": [{
            "excerpt_label": "1040-V purpose + check-prep + mailing chart (2025 verbatim substance)",
            "excerpt_text": (
                "What Is Form 1040-V? It's a statement you send with your check or money order for any "
                "balance due on the 'Amount you owe' line of your 2025 Form 1040, 1040-SR, or 1040-NR. "
                "Line 3: enter the amount you are paying by check or money order; if paying online at "
                "www.irs.gov/Payments, don't complete this form. How To Prepare Your Payment: make your "
                "check or money order payable to 'United States Treasury'; don't send cash (retail cash "
                "option: maximum $1,000 per day per transaction, register first at www.acipayonline.com); "
                "enter your daytime phone number and your SSN (ITIN wherever an SSN is requested; joint "
                "returns use the first SSN) and '2025 Form 1040', '2025 Form 1040-SR', or '2025 Form "
                "1040-NR' on the check; enter the amount like $ XXX.XX without dashes or lines. No checks "
                "of $100 million or more accepted — spread the payment over two or more checks each under "
                "$100 million. Don't staple or otherwise attach your payment or Form 1040-V to your return "
                "or to each other — just put them loose in the envelope. Check-conversion notice: the IRS "
                "may use the check's information to make a one-time electronic funds transfer. Mailing "
                "Address for Payments: Alabama, Florida, Georgia, Louisiana, Mississippi, North Carolina, "
                "South Carolina, Tennessee, Texas -> Internal Revenue Service, P.O. Box 1214, Charlotte, NC "
                "28201-1214. [All other states] -> Internal Revenue Service, P.O. Box 931000, Louisville, "
                "KY 40293-1000. A foreign country, American Samoa, or Puerto Rico (or excluding income "
                "under section 933), or APO/FPO, or Form 2555 or 4563, or dual-status alien or nonpermanent "
                "resident of Guam or the U.S. Virgin Islands -> Internal Revenue Service, P.O. Box 1303, "
                "Charlotte, NC 28201-1303."
            ),
            "summary_text": "1040-V = check/MO only (online payers skip it); payable 'United States Treasury'; SSN + '2025 Form 1040' memo; $100M single-check cap; no staples; GA and the south -> Charlotte Box 1214, everyone else Louisville 931000, foreign -> Charlotte 1303 (year-watched).",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "IRS_F1040ES", "source_type": "federal_form", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Form 1040-ES (2026) — Estimated Tax for Individuals",
        "citation": "Form 1040-ES (2026), Catalog Number 11340T (Feb 12, 2026) — package with worksheet + 4 payment vouchers",
        "issuer": "Internal Revenue Service", "official_url": "https://www.irs.gov/pub/irs-pdf/f1040es.pdf",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.5, "topics": ["vouchers_1040"],
        "excerpts": [{
            "excerpt_label": "Who must pay + the safe-harbor percentages (2026 package verbatim)",
            "excerpt_text": (
                "General Rule: in most cases, you must pay estimated tax for 2026 if both of the following "
                "apply. 1. You expect to owe at least $1,000 in tax for 2026, after subtracting your "
                "withholding and refundable credits. 2. You expect your withholding and refundable credits "
                "to be less than the smaller of: a. 90% of the tax to be shown on your 2026 tax return, or "
                "b. 100% of the tax shown on your 2025 tax return (your 2025 tax return must cover all 12 "
                "months). Exception: you don't have to pay estimated tax for 2026 if you were a U.S. "
                "citizen or resident alien for all of 2025 and you had no tax liability for the full "
                "12-month 2025 tax year (total tax was zero or no return required). Farming and fishing: "
                "if at least two-thirds of your gross income for 2025 or 2026 is from farming or fishing, "
                "substitute 66-2/3% for 90%. Higher income taxpayers: if your adjusted gross income for "
                "2025 was more than $150,000 ($75,000 if your filing status for 2026 is married filing "
                "separately), substitute 110% for 100%; if at least two-thirds of gross income is from "
                "farming or fishing, this rule doesn't apply."
            ),
            "summary_text": "Required-annual-payment: owe >= $1,000 AND withholding+credits < smaller of 90% expected (66-2/3% farmer) or 100%/110% prior (110% when 2025 AGI > $150,000 / $75,000 MFS; never for farmers); no-prior-liability exception (full 12-month year).",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "Due dates + joint bars + voucher mechanics (2026 package verbatim substance)",
            "excerpt_text": (
                "Payment Due Dates: pay all by April 15, 2026, or in four equal amounts — 1st April 15, "
                "2026; 2nd June 15, 2026; 3rd Sept. 15, 2026; 4th Jan. 15, 2027. You don't have to make "
                "the January 15, 2027 payment if you file your 2026 tax return by February 1, 2027, and "
                "pay the entire balance due with your return. Farming/fishing alternatives: pay all by "
                "January 15, 2027, or file the 2026 return by March 1, 2027 and pay the total tax due. "
                "Fiscal-year: 15th day of the 4th, 6th, and 9th months + the 1st month following; weekend/"
                "holiday -> next business day. Postmark rule: the U.S. postmark date is the payment date — "
                "recent USPS clarification: the postmarked date is the date the piece is PROCESSED at a "
                "facility, which may not be the drop-off date. More than four payments allowed (copy an "
                "unused voucher). You can't make joint estimated tax payments if you or your spouse is a "
                "nonresident alien, you are separated under a decree of divorce or separate maintenance, "
                "or you and your spouse have different tax years; registered domestic partnerships and "
                "civil unions cannot make joint estimated payments. Voucher mechanics: complete and send "
                "the voucher ONLY if paying by check or money order; spouses planning separate returns "
                "file separate vouchers; enter in the box ONLY the amount you are sending by check — take "
                "a credited 2025 overpayment into account but don't include it in the box; enter '2026 "
                "Form 1040-ES' and your SSN on the check (joint = the first SSN on the return); names/"
                "SSNs in return order; ITIN wherever an SSN is requested; no checks of $100 million or "
                "more; name change -> attach a statement to the 2026 return listing the payments and the "
                "prior names/SSNs; preprinted vouchers: correct errors, cross out a deceased or divorced "
                "spouse; address change -> Form 8822."
            ),
            "summary_text": "Dates Apr 15 / Jun 15 / Sep 15 2026 + Jan 15 2027 (Feb-1 full-pay skip; farmer Jan-15/Mar-1 options; fiscal-year pattern); postmark = USPS processing date; joint bars (NRA/decree/different years/RDP); check-only vouchers; the overpayment-credit box exclusion; $100M cap.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "The ES mailing chart — NOT the return address (2026 verbatim substance)",
            "excerpt_text": (
                "Where To File Your Estimated Tax Payment Voucher if Paying by Check or Money Order: mail "
                "the voucher and check to the address for the place where you live. Do not mail your tax "
                "return to this address or send an estimated tax payment without a payment voucher. Also, "
                "DO NOT mail your estimated tax payments to the address shown in the Form 1040 "
                "instructions. Caution: only the USPS can deliver to P.O. boxes — you can't use a private "
                "delivery service. Alabama, Alaska, Arizona, California, Colorado, Florida, GEORGIA, "
                "Hawaii, Idaho, Kansas, Louisiana, Michigan, Mississippi, Montana, Nebraska, Nevada, New "
                "Mexico, North Carolina, North Dakota, Ohio, Oregon, Pennsylvania, South Carolina, South "
                "Dakota, Tennessee, Texas, Utah, Washington, Wyoming -> Internal Revenue Service, P.O. Box "
                "1300, Charlotte, NC 28201-1300. Arkansas, Connecticut, Delaware, District of Columbia, "
                "Illinois, Indiana, Iowa, Kentucky, Maine, Maryland, Massachusetts, Minnesota, Missouri, "
                "New Hampshire, New Jersey, New York, Oklahoma, Rhode Island, Vermont, Virginia, West "
                "Virginia, Wisconsin -> Internal Revenue Service, P.O. Box 931100, Louisville, KY "
                "40293-1100. Foreign country, American Samoa, Puerto Rico (section 933), APO/FPO, Form "
                "2555 or 4563, dual-status alien, nonpermanent resident of Guam or USVI -> Internal "
                "Revenue Service, P.O. Box 1303, Charlotte, NC 28201-1303. Guam bona fide residents -> "
                "Department of Revenue and Taxation, Government of Guam, P.O. Box 23607, GMF, GU 96921. "
                "U.S. Virgin Islands bona fide residents -> Virgin Islands Bureau of Internal Revenue, "
                "6115 Estate Smith Bay, Suite 225, St. Thomas, VI 00802. Bona fide residents prepare "
                "separate vouchers for income tax (territorial address) and self-employment tax (the "
                "non-bona-fide address)."
            ),
            "summary_text": "The ES chart differs from BOTH the V chart and the return address (the package says so explicitly). GA -> Charlotte Box 1300 (the V uses 1214). USPS-only for the P.O. boxes; Guam/USVI bona-fide residents split income-tax vs SE-tax vouchers.",
            "is_key_excerpt": True,
        }],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_F1040V", "1040V", "governs"), ("IRS_F1040ES", "1040ES", "governs"),
]


# ── Form 1040-V ──
V_FACTS: list[dict] = [
    {"fact_key": "balance_due", "label": "The 'Amount you owe' on the 2025 return (1040 line 37)", "data_type": "decimal", "required": False, "sort_order": 1},
    {"fact_key": "paying_by_check", "label": "Client pays the balance by check/money order (online payers skip the V)", "data_type": "boolean", "required": False, "sort_order": 2},
    {"fact_key": "efw_elected", "label": "EFW direct debit elected (s76 IRSPayment) — SUPPRESSES the voucher", "data_type": "boolean", "required": False, "sort_order": 3},
    {"fact_key": "check_amount", "label": "V line 3 — amount paid by check/money order", "data_type": "decimal", "required": False, "sort_order": 4},
    {"fact_key": "state_of_residence", "label": "State (selects the V chart row; GA -> Charlotte Box 1214)", "data_type": "string", "required": False, "sort_order": 5},
    {"fact_key": "foreign_or_territory", "label": "Foreign/AS/PR-933/APO-FPO/2555/4563/dual-status (both charts -> Charlotte 1303)", "data_type": "boolean", "required": False, "sort_order": 6},
]

V_RULES: list[dict] = [
    {"rule_id": "R-V-USE", "title": "1040-V only rides a check payment (EFW/online suppress it)", "rule_type": "routing",
     "formula": "print the V iff balance_due > 0 AND paying_by_check AND NOT efw_elected. Online payment ('don't complete this form') and the s76 EFW election both suppress — printing a voucher next to a scheduled debit invites a DOUBLE payment",
     "inputs": ["balance_due", "paying_by_check", "efw_elected"], "outputs": ["v_needed"], "sort_order": 1,
     "description": "W1. Lines 1-4 (SSN order = return order; ITIN wherever an SSN is asked; amount; name/address). The packet emits the voucher only on the check path."},
    {"rule_id": "R-V-CHECK", "title": "Check-prep mechanics ($100M cap, no staples, payable-to, memo)", "rule_type": "validation",
     "formula": "payable 'United States Treasury'; never cash by mail (retail cash: $1,000/day/transaction, acipayonline.com); daytime phone + SSN/ITIN + '2025 Form 1040[-SR/-NR]' on the check; amount $XXX.XX no dashes; single check < $100,000,000 (split otherwise); payment + voucher LOOSE in the envelope (no staples); the IRS may convert the check to a one-time EFT",
     "inputs": ["check_amount"], "outputs": ["check_prep_ok"], "sort_order": 2,
     "description": "W1. Print-blurb guidance the preparer letter mirrors; the $100M cap is the one hard validation."},
    {"rule_id": "R-V-MAIL", "title": "The 2025 V mailing chart (year-watched)", "rule_type": "routing",
     "formula": "AL FL GA LA MS NC SC TN TX -> Charlotte, P.O. Box 1214. All other states -> Louisville, P.O. Box 931000. Foreign/AS/PR-933/APO-FPO/2555/4563/dual-status/Guam-USVI-nonpermanent -> Charlotte, P.O. Box 1303. NOT the ES chart, NOT the return-only address",
     "inputs": ["state_of_residence", "foreign_or_territory"], "outputs": ["v_mailing_address"], "sort_order": 3,
     "description": "W4. GA files the V at Charlotte Box 1214 — the ES voucher goes to Box 1300. The three-way drift is the reason this pair is specced."},
]

V_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-V-USE", "IRS_F1040V", "primary", "'What Is Form 1040-V?' + the online-payer skip"),
    ("R-V-CHECK", "IRS_F1040V", "primary", "How To Prepare Your Payment + the $100M cap"),
    ("R-V-MAIL", "IRS_F1040V", "primary", "Mailing Address for Payments chart (2025)"),
]

V_LINES: list[dict] = [
    {"line_number": "V1", "description": "V line 1 — SSN (joint = first SSN on the return; ITIN allowed)", "line_type": "input", "sort_order": 1},
    {"line_number": "V2", "description": "V line 2 — spouse SSN (joint returns)", "line_type": "input", "sort_order": 2},
    {"line_number": "V3", "description": "V line 3 — amount paid by check/money order", "line_type": "input", "source_facts": ["check_amount"], "source_rules": ["R-V-USE"], "sort_order": 3},
    {"line_number": "V4", "description": "V line 4 — name(s)/address exactly as on the return (+foreign spaces)", "line_type": "input", "sort_order": 4},
    {"line_number": "V_CALC_NEED", "description": "Computed voucher emission (check path only; EFW suppresses)", "line_type": "calculated", "source_rules": ["R-V-USE"], "sort_order": 5},
    {"line_number": "V_CALC_ADDR", "description": "Computed V mailing address (2025 chart; year-watched)", "line_type": "calculated", "source_rules": ["R-V-MAIL"], "sort_order": 6},
]

V_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_V_EFWCONFL", "title": "EFW elected — the 1040-V is suppressed", "severity": "warning",
     "condition": "efw_elected and paying_by_check both set",
     "message": "This return schedules an electronic funds withdrawal for the balance due (the Payments-tab EFW card). The 1040-V voucher is suppressed — mailing a check on top of a scheduled debit double-pays. Clear the EFW election if the client wants to pay by mail.", "notes": "W1. The s76 IRSPayment tie."},
    {"diagnostic_id": "D_V_ONLINE", "title": "Paying online — no 1040-V needed", "severity": "info",
     "condition": "balance due paid electronically",
     "message": "If paying online at irs.gov/Payments (Online Account, Direct Pay, EFTPS, or card), don't complete Form 1040-V — the voucher exists only for check/money-order remittances.", "notes": "W1."},
    {"diagnostic_id": "D_V_100M", "title": "Single check of $100 million or more", "severity": "error",
     "condition": "check_amount >= 100,000,000",
     "message": "The IRS can't accept a single check (including a cashier's check) of $100,000,000 or more. Spread the payment over two or more checks each under $100 million, or pay electronically (no limit).", "notes": "W1."},
    {"diagnostic_id": "D_V_PREP", "title": "Check preparation + no-staple rule", "severity": "info",
     "condition": "informational on print",
     "message": "Make the check payable to 'United States Treasury' (never cash by mail; in-person retail cash caps at $1,000/day via acipayonline.com). Write the daytime phone, SSN (first-listed for joint; ITIN where applicable), and '2025 Form 1040' (or -SR/-NR) on it; amount as $XXX.XX with no dashes. Don't staple the payment or voucher to the return or each other — loose in the envelope.", "notes": "W1."},
    {"diagnostic_id": "D_V_ADDR", "title": "1040-V mailing address (year-watched; not the ES address)", "severity": "info",
     "condition": "informational on print",
     "message": "Mail the 2025 return + payment + 1040-V per the V chart: AL/FL/GA/LA/MS/NC/SC/TN/TX to Charlotte (P.O. Box 1214); all other states to Louisville (P.O. Box 931000); foreign/territory/APO-FPO/2555/4563/dual-status to Charlotte (P.O. Box 1303). This is NOT the 1040-ES chart (GA estimates go to Box 1300) — verify against the current-year form before printing mailing instructions.", "notes": "W4. Year-watched."},
]

V_SCENARIOS: list[dict] = [
    {"scenario_name": "1040V-A — GA client pays $2,000 by check: voucher prints, Charlotte Box 1214", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"balance_due": 2000, "paying_by_check": True, "efw_elected": False, "check_amount": 2000,
                "state_of_residence": "GA", "foreign_or_territory": False},
     "expected_outputs": {"v_needed": True, "v_mailing_address_contains": "P.O. Box 1214"},
     "notes": "The house case: Athens GA balance-due client mailing a check — Charlotte 1214 on the V chart (the ES chart would say 1300)."},
    {"scenario_name": "1040V-B — EFW elected: the voucher is suppressed", "scenario_type": "edge", "sort_order": 2,
     "inputs": {"balance_due": 2000, "paying_by_check": False, "efw_elected": True},
     "expected_outputs": {"v_needed": False, "diagnostic": "D_V_EFWCONFL"},
     "notes": "The s76 IRSPayment record schedules the debit — no paper voucher rides the packet (double-payment guard)."},
    {"scenario_name": "1040V-C — $100M check: split required", "scenario_type": "failure", "sort_order": 3,
     "inputs": {"balance_due": 100000000, "paying_by_check": True, "efw_elected": False, "check_amount": 100000000},
     "expected_outputs": {"check_splits_required": 2, "diagnostic": "D_V_100M"},
     "notes": "No single check >= $100,000,000 — two or more checks each under the cap (electronic payments have no limit)."},
]

# ── Form 1040-ES ──
ES_FACTS: list[dict] = [
    {"fact_key": "expected_tax_2026", "label": "Expected 2026 total tax (the app's ES engine supplies it)", "data_type": "decimal", "required": False, "sort_order": 1},
    {"fact_key": "expected_withholding_2026", "label": "Expected 2026 withholding + refundable credits", "data_type": "decimal", "required": False, "sort_order": 2},
    {"fact_key": "prior_year_tax", "label": "2025 tax (the 100%/110% arm; the 2025 return must cover 12 months)", "data_type": "decimal", "required": False, "sort_order": 3},
    {"fact_key": "prior_year_agi", "label": "2025 AGI (over $150,000 / $75,000 MFS -> the 110% arm)", "data_type": "decimal", "required": False, "sort_order": 4},
    {"fact_key": "filing_status_mfs_2026", "label": "2026 filing status is MFS (halves the higher-income threshold)", "data_type": "boolean", "required": False, "sort_order": 5},
    {"fact_key": "farmer_fisher", "label": "Two-thirds of 2025 or 2026 gross income from farming/fishing (66-2/3%; Jan-15/Mar-1 options; no 110%)", "data_type": "boolean", "required": False, "sort_order": 6},
    {"fact_key": "prior_year_no_liability", "label": "No 2025 tax liability (full 12-month year, citizen/resident all year) — the exception", "data_type": "boolean", "required": False, "sort_order": 7},
    {"fact_key": "es_q1_amount", "label": "Voucher 1 amount (due April 15, 2026)", "data_type": "decimal", "required": False, "sort_order": 8},
    {"fact_key": "es_q2_amount", "label": "Voucher 2 amount (due June 15, 2026)", "data_type": "decimal", "required": False, "sort_order": 9},
    {"fact_key": "es_q3_amount", "label": "Voucher 3 amount (due Sept. 15, 2026)", "data_type": "decimal", "required": False, "sort_order": 10},
    {"fact_key": "es_q4_amount", "label": "Voucher 4 amount (due Jan. 15, 2027; skippable via the Feb-1 full-pay filing)", "data_type": "decimal", "required": False, "sort_order": 11},
    {"fact_key": "es_debit_quarters", "label": "Quarters scheduled as EFW debits (s76 IRSESPayment) — their paper vouchers are suppressed", "data_type": "string", "required": False, "sort_order": 12},
    {"fact_key": "overpayment_credited", "label": "2025 overpayment credited to 2026 (reduces remittances; NEVER enters the voucher box)", "data_type": "decimal", "required": False, "sort_order": 13},
    {"fact_key": "spouse_nra", "label": "Joint bar — spouse is a nonresident alien", "data_type": "boolean", "required": False, "sort_order": 14},
    {"fact_key": "divorce_decree", "label": "Joint bar — separated under a decree of divorce/separate maintenance", "data_type": "boolean", "required": False, "sort_order": 15},
    {"fact_key": "different_tax_years", "label": "Joint bar — spouses have different tax years", "data_type": "boolean", "required": False, "sort_order": 16},
    {"fact_key": "rdp_civil_union", "label": "Joint bar — registered domestic partnership / civil union (never joint)", "data_type": "boolean", "required": False, "sort_order": 17},
    {"fact_key": "es_state", "label": "State (selects the ES chart row; GA -> Charlotte Box 1300, NOT the V's 1214)", "data_type": "string", "required": False, "sort_order": 18},
    {"fact_key": "es_foreign", "label": "Foreign/territory voucher route (Charlotte 1303; Guam/USVI bona fide -> territorial)", "data_type": "boolean", "required": False, "sort_order": 19},
]

ES_RULES: list[dict] = [
    {"rule_id": "R-ES-RAP", "title": "Required annual payment (90% / 100% / 110% / 66-2/3%)", "rule_type": "calculation",
     "formula": "RAP = min(expected_2026_tax * (0.90, or 2/3 for farmer-fisher), prior_year_tax * (1.00, or 1.10 when 2025 AGI > $150,000 ($75,000 MFS-2026) and not farmer-fisher)). Estimates required iff expected owe >= $1,000 AND withholding+credits < RAP, unless the no-2025-liability exception (full 12-month year) applies",
     "inputs": ["expected_tax_2026", "expected_withholding_2026", "prior_year_tax", "prior_year_agi", "filing_status_mfs_2026", "farmer_fisher", "prior_year_no_liability"],
     "outputs": ["required_annual_payment", "estimates_required"], "sort_order": 1,
     "description": "W2. The general rule verbatim. The dollar WORKSHEET (brackets, standard deduction) is the app ES engine's job — the spec owns the test, the dates, and the vouchers."},
    {"rule_id": "R-ES-DATES", "title": "Due dates + the Q4 skip + farmer/fiscal alternatives", "rule_type": "validation",
     "formula": "calendar 2026: Apr 15 / Jun 15 / Sep 15, 2026 / Jan 15, 2027 (= the s76 FPYMT-088-11 EFW dates). Q4 skippable iff the 2026 return files by Feb 1, 2027 AND pays the full balance. Farmer-fisher: all by Jan 15, 2027, or file by Mar 1, 2027 + pay in full (no estimates). Fiscal-year: 15th of the 4th/6th/9th months + the 1st following month; weekend/holiday -> next business day. Postmark = payment date (USPS PROCESSING date, per the recent clarification). More than four payments allowed",
     "inputs": ["es_q1_amount", "es_q2_amount", "es_q3_amount", "es_q4_amount"], "outputs": ["due_dates"], "sort_order": 2,
     "description": "W3. The four fixed dates the app already uses for the ES debit records; the paper vouchers carry the same calendar."},
    {"rule_id": "R-ES-VOUCH", "title": "Voucher mechanics (check-only; box exclusions; joint bars; suppression)", "rule_type": "validation",
     "formula": "complete a voucher ONLY when paying that quarter by check/MO; a quarter scheduled as an EFW debit (s76 IRSESPayment) suppresses its paper voucher; the box carries ONLY the check amount — a credited 2025 overpayment reduces the remittance but never enters the box; spouses planning separate returns file separate vouchers; joint vouchers BARRED when: spouse NRA, divorce/separate-maintenance decree, different tax years, or RDP/civil union; names/SSNs in return order; ITIN wherever an SSN is asked; '2026 Form 1040-ES' + first SSN on the check; single check < $100M; name change -> statement on the 2026 return; address change -> Form 8822",
     "inputs": ["es_debit_quarters", "overpayment_credited", "spouse_nra", "divorce_decree", "different_tax_years", "rdp_civil_union"],
     "outputs": ["voucher_emission", "joint_voucher_barred"], "sort_order": 3,
     "description": "W3. The check-only rule plus the same double-payment guard the 1040-V carries: debit quarters never print vouchers."},
    {"rule_id": "R-ES-MAIL", "title": "The 2026 ES mailing chart — NOT the V chart, NOT the return address", "rule_type": "routing",
     "formula": "AL AK AZ CA CO FL GA HI ID KS LA MI MS MT NE NV NM NC ND OH OR PA SC SD TN TX UT WA WY -> Charlotte, P.O. Box 1300. AR CT DE DC IL IN IA KY ME MD MA MN MO NH NJ NY OK RI VT VA WV WI -> Louisville, P.O. Box 931100. Foreign/AS/PR-933/APO-FPO/2555/4563/dual-status -> Charlotte, P.O. Box 1303. Guam bona fide -> Gov't of Guam (GMF); USVI bona fide -> VI BIR (St. Thomas); bona fide residents split income-tax (territorial) vs SE-tax (federal) vouchers. USPS ONLY for the P.O. boxes (no private delivery). NEVER the Form-1040-instructions address (the package says so verbatim)",
     "inputs": ["es_state", "es_foreign"], "outputs": ["es_mailing_address"], "sort_order": 4,
     "description": "W4. The three-way drift trap: GA = Box 1300 here, Box 1214 on the V, and something else again for the bare return. Year-watched."},
]

ES_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-ES-RAP", "IRS_F1040ES", "primary", "General Rule + Special Rules (90/100/110/66-2/3)"),
    ("R-ES-DATES", "IRS_F1040ES", "primary", "Payment Due Dates + skips + fiscal-year + postmark"),
    ("R-ES-VOUCH", "IRS_F1040ES", "primary", "How To Complete/Use the Payment Vouchers + joint bars"),
    ("R-ES-MAIL", "IRS_F1040ES", "primary", "Where To File chart (2026) + the not-the-return-address caution"),
]

ES_LINES: list[dict] = [
    {"line_number": "ES_Q1", "description": "Voucher 1 — due April 15, 2026", "line_type": "input", "source_facts": ["es_q1_amount"], "sort_order": 1},
    {"line_number": "ES_Q2", "description": "Voucher 2 — due June 15, 2026", "line_type": "input", "source_facts": ["es_q2_amount"], "sort_order": 2},
    {"line_number": "ES_Q3", "description": "Voucher 3 — due Sept. 15, 2026", "line_type": "input", "source_facts": ["es_q3_amount"], "sort_order": 3},
    {"line_number": "ES_Q4", "description": "Voucher 4 — due Jan. 15, 2027 (Feb-1 full-pay skip)", "line_type": "input", "source_facts": ["es_q4_amount"], "sort_order": 4},
    {"line_number": "ES_CALC_RAP", "description": "Computed required annual payment (min of the two arms)", "line_type": "calculated", "source_rules": ["R-ES-RAP"], "sort_order": 5},
    {"line_number": "ES_CALC_REQ", "description": "Computed estimates-required flag ($1,000 gate + RAP vs withholding)", "line_type": "calculated", "source_rules": ["R-ES-RAP"], "sort_order": 6},
    {"line_number": "ES_CALC_EMIT", "description": "Computed voucher emission per quarter (check quarters only; debit quarters suppressed)", "line_type": "calculated", "source_rules": ["R-ES-VOUCH"], "sort_order": 7},
    {"line_number": "ES_CALC_ADDR", "description": "Computed ES mailing address (2026 chart; year-watched)", "line_type": "calculated", "source_rules": ["R-ES-MAIL"], "sort_order": 8},
]

ES_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_ES_REQUIRED", "title": "Estimated payments required (general rule met)", "severity": "warning",
     "condition": "expected owe >= $1,000 and withholding+credits < the required annual payment",
     "message": "The client expects to owe at least $1,000 for 2026 after withholding and refundable credits, and withholding falls short of the required annual payment (the smaller of 90% of expected 2026 tax or 100%/110% of 2025 tax). Schedule quarterly estimates — vouchers for check payments, or EFW debits on the Payments tab.", "notes": "W2."},
    {"diagnostic_id": "D_ES_110PCT", "title": "Higher-income safe harbor — 110% of 2025 tax", "severity": "info",
     "condition": "2025 AGI > $150,000 ($75,000 MFS-2026)",
     "message": "Because 2025 AGI exceeds $150,000 ($75,000 for 2026 MFS), the prior-year safe harbor is 110% of the 2025 tax, not 100%. (Farmers/fishers are exempt from the 110% substitution.)", "notes": "W2."},
    {"diagnostic_id": "D_ES_FARMER", "title": "Farmer/fisher alternatives (66-2/3%; Jan 15 / Mar 1)", "severity": "info",
     "condition": "two-thirds of 2025 or 2026 gross income from farming/fishing",
     "message": "Farming/fishing clients substitute 66-2/3% for the 90% arm — and may skip quarterly vouchers entirely by paying all estimated tax by January 15, 2027, or by filing the 2026 return by March 1, 2027 and paying in full.", "notes": "W2/W3."},
    {"diagnostic_id": "D_ES_NOLIAB", "title": "No 2025 liability — no estimates required", "severity": "info",
     "condition": "no tax liability for the full 12-month 2025 year (citizen/resident all year)",
     "message": "No estimated payments are required for 2026: the client was a U.S. citizen or resident for all of 2025 and had no tax liability for the full 12-month 2025 tax year.", "notes": "W2."},
    {"diagnostic_id": "D_ES_Q4SKIP", "title": "January 15 voucher skippable via early filing", "severity": "info",
     "condition": "planning to file the 2026 return by Feb 1, 2027 with full payment",
     "message": "The January 15, 2027 payment isn't required if the 2026 return is filed by February 1, 2027 and the entire balance due is paid with it.", "notes": "W3."},
    {"diagnostic_id": "D_ES_JOINTBAR", "title": "Joint estimated payments barred", "severity": "error",
     "condition": "spouse NRA, divorce/separate-maintenance decree, different tax years, or RDP/civil union",
     "message": "Joint estimated tax payments aren't allowed when either spouse is a nonresident alien, the spouses are separated under a decree of divorce or separate maintenance, or they have different tax years — and registered domestic partners/civil-union partners can never pay jointly. Issue separate vouchers; each takes credit only for their own payments.", "notes": "W3."},
    {"diagnostic_id": "D_ES_OVERPAY", "title": "Credited overpayment never enters the voucher box", "severity": "info",
     "condition": "2025 overpayment credited to 2026",
     "message": "Take the 2025 overpayment credited to 2026 into account when sizing the payments, but do NOT include it in the voucher box — the box carries only the amount actually sent by check or money order.", "notes": "W3."},
    {"diagnostic_id": "D_ES_DEBITED", "title": "EFW-debited quarters print no vouchers", "severity": "info",
     "condition": "es_debit_q1-4 scheduled (the s76 IRSESPayment records)",
     "message": "Quarters scheduled as electronic funds withdrawals (the Payments-tab ES debit fields) e-file as IRSESPayment records at the same statutory dates — their paper vouchers are suppressed to prevent double payment. Print vouchers only for quarters the client pays by check.", "notes": "W3. The s76 tie."},
    {"diagnostic_id": "D_ES_ADDR", "title": "ES mailing address — never the return address (year-watched)", "severity": "warning",
     "condition": "printing ES vouchers with mailing instructions",
     "message": "Mail ES vouchers per the 1040-ES chart ONLY: e.g., Georgia sends estimates to Charlotte, P.O. Box 1300 — NOT the 1040-V's Box 1214 and NOT the Form-1040-instructions return address ('do not mail your estimated tax payments to the address shown in the Form 1040 instructions'). Only USPS delivers to these P.O. boxes — no FedEx/UPS. Verify the chart against the current-year package before printing.", "notes": "W4. The three-way drift trap, year-watched."},
    {"diagnostic_id": "D_ES_POSTMARK", "title": "Postmark = USPS processing date", "severity": "info",
     "condition": "informational on print",
     "message": "A mailed payment is timely if postmarked by the due date — but per the recent USPS clarification, the postmark date is when the piece is PROCESSED at a USPS facility, which may be later than the drop-off. Mail early, or pay electronically for same-day certainty.", "notes": "W3."},
]

ES_SCENARIOS: list[dict] = [
    {"scenario_name": "1040ES-A — GA quarterly vouchers: Charlotte Box 1300 (NOT the V's 1214)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"es_q1_amount": 1000, "es_q2_amount": 1000, "es_q3_amount": 1000, "es_q4_amount": 1000,
                "es_state": "GA", "es_foreign": False},
     "expected_outputs": {"es_mailing_address_contains": "P.O. Box 1300", "due_dates": ["2026-04-15", "2026-06-15", "2026-09-15", "2027-01-15"]},
     "notes": "The address-drift pin: the same GA client mails the V to Box 1214 and the ES vouchers to Box 1300 — one chart never substitutes for the other."},
    {"scenario_name": "1040ES-B — higher-income 110% arm", "scenario_type": "edge", "sort_order": 2,
     "inputs": {"expected_tax_2026": 60000, "prior_year_tax": 40000, "prior_year_agi": 200000, "filing_status_mfs_2026": False, "farmer_fisher": False},
     "expected_outputs": {"required_annual_payment": 44000},
     "notes": "min(90% x 60,000 = 54,000, 110% x 40,000 = 44,000) = 44,000 — the 110% substitution because 2025 AGI 200,000 > 150,000."},
    {"scenario_name": "1040ES-C — farmer: 66-2/3% arm + the Mar-1 option", "scenario_type": "edge", "sort_order": 3,
     "inputs": {"expected_tax_2026": 30000, "prior_year_tax": 28000, "prior_year_agi": 200000, "filing_status_mfs_2026": False, "farmer_fisher": True},
     "expected_outputs": {"required_annual_payment": 20000, "diagnostic": "D_ES_FARMER"},
     "notes": "min(2/3 x 30,000 = 20,000, 100% x 28,000 = 28,000) = 20,000 — and the 110% arm does NOT apply to farmers despite the 200,000 AGI. Alternatives: all by Jan 15, 2027, or file by Mar 1, 2027 + pay in full."},
    {"scenario_name": "1040ES-D — no 2025 liability: exception", "scenario_type": "edge", "sort_order": 4,
     "inputs": {"expected_tax_2026": 5000, "expected_withholding_2026": 0, "prior_year_no_liability": True},
     "expected_outputs": {"estimates_required": False, "diagnostic": "D_ES_NOLIAB"},
     "notes": "Zero 2025 tax for a full 12-month citizen/resident year -> no 2026 estimates regardless of the expected owe."},
    {"scenario_name": "1040ES-E — joint voucher barred (NRA spouse)", "scenario_type": "failure", "sort_order": 5,
     "inputs": {"spouse_nra": True},
     "expected_outputs": {"joint_voucher_barred": True, "diagnostic": "D_ES_JOINTBAR"},
     "notes": "NRA spouse / decree / different years / RDP-civil-union all bar joint payments — separate vouchers, credit follows the payer."},
    {"scenario_name": "1040ES-F — debited quarters suppress their vouchers", "scenario_type": "edge", "sort_order": 6,
     "inputs": {"es_q1_amount": 1000, "es_q2_amount": 1000, "es_q3_amount": 1000, "es_q4_amount": 1000,
                "es_debit_quarters": "q1,q2"},
     "expected_outputs": {"vouchers_printed": ["q3", "q4"], "diagnostic": "D_ES_DEBITED"},
     "notes": "Q1/Q2 e-file as s76 IRSESPayment records at the same dates; only Q3/Q4 print paper vouchers — the double-payment guard, mirrored from the 1040-V/EFW rule."},
    {"scenario_name": "1040ES-G — Q4 skip via the Feb-1 filing", "scenario_type": "edge", "sort_order": 7,
     "inputs": {"es_q4_amount": 1000, "files_by_feb1": True, "pays_full_with_return": True},
     "expected_outputs": {"q4_skippable": True, "diagnostic": "D_ES_Q4SKIP"},
     "notes": "File the 2026 return by Feb 1, 2027 + pay the entire balance -> the Jan 15 voucher is unnecessary."},
]

FORMS: list[dict] = [
    {
        "identity": {"form_number": "1040V", "form_title": "Form 1040-V (2025) — Payment Voucher for Individuals",
                     "notes": "Payment-cluster batch order 3a (tts s77). PRINT-ONLY check/money-order voucher for the TY2025 balance due — online payers and EFW-elected returns (the s76 IRSPayment) suppress it (double-payment guard). Lines 1-4; check prep (payable 'United States Treasury', SSN + '2025 Form 1040' memo, $XXX.XX format, $100M single-check cap, retail cash $1,000/day, no staples — loose in the envelope). Mailing chart YEAR-WATCHED and DIFFERENT from the ES chart: AL FL GA LA MS NC SC TN TX -> Charlotte Box 1214; other states -> Louisville Box 931000; foreign/territory/APO-FPO/2555/4563/dual-status -> Charlotte Box 1303. entity_types ['1040']."},
        "facts": V_FACTS, "rules": V_RULES, "rule_links": V_RULE_LINKS,
        "lines": V_LINES, "diagnostics": V_DIAGNOSTICS, "scenarios": V_SCENARIOS,
    },
    {
        "identity": {"form_number": "1040ES", "form_title": "Form 1040-ES (2026) — Estimated Tax for Individuals (voucher set)",
                     "notes": "Payment-cluster batch order 3b (tts s77). PRINT-ONLY quarterly vouchers for the 2026 estimates a TY2025 client pays by check — quarters scheduled as EFW debits (the s76 IRSESPayment records) suppress their paper vouchers. Dates Apr 15 / Jun 15 / Sep 15 2026 + Jan 15 2027 (= FPYMT-088-11; Q4 skippable via the Feb-1 full-pay filing; farmer Jan-15/Mar-1 options; fiscal-year 4th/6th/9th/+1 pattern). Required-annual-payment test: owe >= $1,000 AND withholding < min(90% expected (66-2/3 farmer), 100%/110% prior (110% when 2025 AGI > $150k/$75k MFS, never farmers)); no-2025-liability exception. Voucher mechanics: check-only, overpayment-credit box exclusion, joint bars (NRA/decree/different-years/RDP), $100M cap, postmark = USPS PROCESSING date. Mailing chart YEAR-WATCHED, differs from BOTH the V chart and the return address (GA -> Charlotte Box 1300 vs the V's 1214; 'do not mail... to the address shown in the Form 1040 instructions'); USPS-only P.O. boxes; Guam/USVI bona-fide split. The WORKSHEET math is the app ES engine's job — this spec owns the test, dates, vouchers, addresses. entity_types ['1040']."},
        "facts": ES_FACTS, "rules": ES_RULES, "rule_links": ES_RULE_LINKS,
        "lines": ES_LINES, "diagnostics": ES_DIAGNOSTICS, "scenarios": ES_SCENARIOS,
    },
]

# Staged DRAFT deliberately (the new-FAs-default-ACTIVE trap): the tts build leg activates + writes
# runners + refreshes the export-verbatim mirrors in ONE motion.
FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040V-EFW", "title": "EFW election suppresses the 1040-V voucher", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "draft", "sort_order": 1,
     "description": "The packet emits the 1040-V iff balance due > 0 AND the client pays by check AND efw_elected is False (the s76 IRSPayment record and the paper voucher never coexist). Pins: (2000, check, no-EFW) -> printed; (2000, EFW) -> suppressed.",
     "definition": {"rule": "R-V-USE", "check": "v_needed == (balance_due > 0 and paying_by_check and not efw_elected)"}},
    {"assertion_id": "FA-ES-RAP", "title": "Required annual payment = min(90%/66-2/3% expected, 100%/110% prior)", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "draft", "sort_order": 2,
     "description": "Pins: (60000 expected, 40000 prior, 200000 AGI) -> 44000 (the 110% arm); farmer (30000, 28000, 200000) -> 20000 (66-2/3%, and no 110% for farmers); (60000, 40000, 100000 AGI) -> 40000 (plain 100%).",
     "definition": {"rule": "R-ES-RAP", "check": "rap == min(expected * pct_current, prior * pct_prior) with the farmer/high-AGI substitutions"}},
    {"assertion_id": "FA-ES-QDEBIT", "title": "Debited quarters suppress their paper vouchers", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "draft", "sort_order": 3,
     "description": "A quarter carried on an s76 IRSESPayment record (es_debit_q1-4) prints NO paper voucher; check-paid quarters print theirs at the same four statutory dates (2026-04-15 / 06-15 / 09-15 / 2027-01-15). Pins: debits q1,q2 with four amounts -> vouchers q3,q4 only.",
     "definition": {"rule": "R-ES-VOUCH", "check": "voucher set == quarters with amounts minus debited quarters; dates == the FPYMT-088-11 calendar"}},
]


class Command(BaseCommand):
    help = "Load the 1040-V / 1040-ES voucher-pair spec. Refuses to seed until READY_TO_SEED=True (Gate-1 W1-W4)."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad the 1040-V / 1040-ES voucher-pair spec\n"))
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
                "\nREFUSING TO SEED THE 1040-V/1040-ES PAIR: not cleared.\n\n"
                "Gated until Ken approves the Gate-1 walk (W1 1040-V mechanics + the EFW suppression;\n"
                "W2 the required-annual-payment test; W3 dates + voucher mechanics + the ES-debit\n"
                "suppression; W4 the three-way address charts) and flips the sentinel.\n\n"
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
        self.stdout.write("1040-V / 1040-ES pair loaded.")
        self.stdout.write(f"  1040V: facts {len(V_FACTS)} / rules {len(V_RULES)} / lines {len(V_LINES)} / diag {len(V_DIAGNOSTICS)} / tests {len(V_SCENARIOS)}")
        self.stdout.write(f"  1040ES: facts {len(ES_FACTS)} / rules {len(ES_RULES)} / lines {len(ES_LINES)} / diag {len(ES_DIAGNOSTICS)} / tests {len(ES_SCENARIOS)}")
        self.stdout.write(f"  FA {len(FLOW_ASSERTIONS)}")
        self.stdout.write("=" * 60)
