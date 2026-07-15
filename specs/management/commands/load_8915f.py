"""Load the Form 8915-F spec — Qualified Disaster Retirement Plan Distributions and Repayments
(Rev. December 2025 form + instructions). Post-payment-cluster draft-to-gate order 2 (tts s79;
BUILD_ORDER "next NEW item: 8915-F — spec-first gap check"). Greenfield (gap confirmed 404 ×2 on
2026-07-14 under both '8915F' and '8915-F').

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
The "forever form" (no more alphabetical 8915s): SECURE 2.0 §331 qualified disaster recovery
distributions. Items A (tax year) + B (disaster year) name the instance; item C = FEMA DR
numbers; item D = coronavirus only. Married = a SEPARATE form per spouse. MeF: IRS8915F is a
ReturnData1040 document (2025v5.3, maxOccurs=6) — the tts leg is inputs + per-disaster compute +
print + MeF document (the s72 recipe). QDDs: $22,000-per-disaster aggregate cap (2021+ disasters;
$100,000 only for item-B-2020), the 179-day distribution period, 3-year income spread (opt-out
boxes 11/22 must MATCH), 3-years-and-1-day repayments, the 10%/25% early-tax WAIVER (never on
5329). Part IV main-home qualified distributions: the -180d/+30d receipt window, the 180-day
repayment period (NOT 179 — the Appendix-D off-by-one class), no spread.

v1 SCOPE — PROPOSED (Gate-1 walk W1-W4 AWAITING KEN; see f8915f_source_brief.md):
W1. The QDD framework: the 3-part test (period + main-home-in-area + economic loss) and the
    any-distribution designation rule (incl. periodic payments and RMDs; plan loan offsets);
    the 179-day period (begins disaster-begin; ends 179d after the LATEST of begin/declaration/
    12-29-2022 — three published date examples pinned); the $22,000 per-disaster ALL-plans cap
    (F8915F-003); the not-QDD list; DR-declared major disasters only.
W2. Part I ladder + spread: 1a-1e incl. the single-new-disaster shortcut (skip to 1e = $22,000);
    the Rev-12-2025 NEW line 5a redesign (5b(a) = sum(2-4(a)) - 5a; 5b(b) = min(5b(a), 1e);
    reasonable-method allocation back to 2-4(b)); line 6 waiver + line 7 excess; the 3-year
    spread ("divided by 3.0" prints NO rounding -> whole-dollar convention FLAGGED, the 9465
    ÷72 class); the 11<->22 box-consistency rule; the death-collapse rule.
W3. Repayments + Parts III/IV: 3 years + 1 day from receipt; report only repayments made before
    filing AND by the due date (later -> next year's form or carryback amend, the Rudy examples
    pinned both directions); can't-repay list (non-spouse beneficiary / RMDs / SEPP); the 8606
    15b/25b ties (lines 18/19, attributable-to-THIS-form); Part IV (hardship-401k/TSA/FTHB-IRA
    only; received within [-180d, +30d] of the disaster; repayable through 180d after the latest
    trigger; NO spread; line 32 additional-tax exposure; unrepaid re-designation as QDD).
W4. E-file + landings: IRS8915F max 6 (identity = the item A/B pair + spouse); year-enum rejects
    (F8915F-001/-002); worksheet lines 12/14/23/25 carry BinaryAttachment refs (the attach-to-
    back e-file mirror); 15 -> 1040 line 5b, 26 -> line 4b, 7 -> normal income; QDDs never on
    5329 (the tts 5329-unit seam). STATED BOUNDARIES: Worksheet 1B/2/3/4/5 internals = the tts
    engine's job; 2020-vintage/coronavirus = income-continuation/repayment arms only; the
    Appendix A/C/D tables derive from the period helpers, never re-encoded.

CARRIED [UNVERIFIED]: none — verbatim vs Form 8915-F (Rev. 12-2025, Created 5/23/25) + i8915f
(Rev. 12-2025, Dec 22 2025, 73 pp) + IRS8915F.xsd 2025v5.3 + the 1040 rules CSV (3 Active
F8915F rules). About page (reviewed 27-Jun-2026) developments ALL target older revisions; the
20-Dec-2024 Appendix-D off-by-one is FIXED in the current tables (and named the failure class
our period helpers pin). Year-watch: item A/B enums roll annually; Appendix C/D supersede.

SAFETY GUARD — READY_TO_SEED stayed False until Gate-1 approval. APPROVED: Ken, 2026-07-14 (s83 approve-all, WO-28/29/30/31/32 together; walk recommendations adopted as filed).
"""
import datetime as _dt

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

# ── Verified constants (f8915f_source_brief.md) ──
QDD_LIMIT = 22_000                 # per disaster, ALL plans aggregate, 2021+ disasters (SECURE 2.0 §331)
QDD_LIMIT_2020 = 100_000           # item B = 2020 vintage only
QDD_PERIOD_DAYS = 179              # distribution period: ends 179d after the latest trigger (Part I)
QD_REPAY_PERIOD_DAYS = 180         # Part IV repayment period: 180d (the Appendix-D off-by-one class)
SECURE20_ENACTED = _dt.date(2022, 12, 29)   # the third "latest of" trigger
QD_WINDOW_BEFORE_DAYS = 180        # Part IV receipt: no more than 180 days BEFORE the disaster's first day
QD_WINDOW_AFTER_DAYS = 30          # ... and no later than 30 days after the last day
REPAY_YEARS = 3                    # QDD repayment: 3 years from the day after receipt ("3 years and 1 day")
SPREAD_YEARS = 3                   # default income spread (divide by 3.0 — rounding convention flagged W2)
MEF_MAX_DOCS = 6                   # IRS8915F maxOccurs=6 in ReturnData1040 2025v5.3
ITEM_A_ENUM = ["2021", "2022", "2023", "2024", "2025", "2026", "2027", "2028"]  # face; XSD choice: 2022-2028 enum + 2021 checkbox
ITEM_B_ENUM = ["2020", "2021", "2022", "2023", "2024", "2025", "2026", "2027"]  # face; XSD choice: 2021-2027 enum + 2020 checkbox
LANDING_OTHER_THAN_IRA = "1040_5B"  # Part II line 15 -> Form 1040 line 5b
LANDING_IRA = "1040_4B"             # Part III line 26 -> Form 1040 line 4b


def _qdd_limit(item_b_year) -> int:
    """$22,000 per disaster for 2021+ disasters; $100,000 only when item B = 2020."""
    return QDD_LIMIT_2020 if int(item_b_year) == 2020 else QDD_LIMIT


def _qdd_period_end(begin_date, declaration_date):
    """Part I qualified disaster distribution period: begins on the disaster beginning date, ends
    179 days after the LATEST of (beginning date, declaration date, 12/29/2022). Published pins:
    DR-4682-WA (11/3/22, 1/12/23) -> 7/10/23; DR-4681 (10/1/22, 12/30/22) -> 6/27/23;
    DR-4685-GA (1/12/23, 1/16/23) -> 7/14/23."""
    latest = max(begin_date, declaration_date, SECURE20_ENACTED)
    return latest + _dt.timedelta(days=QDD_PERIOD_DAYS)


def _qd_repayment_period_end(begin_date, declaration_date):
    """Part IV qualified distribution repayment period: ends 180 days (NOT 179 — the Appendix-D
    off-by-one class) after the latest trigger. Published pins: DR-4682-WA -> 7/11/23;
    DR-4681 -> 6/28/23; DR-4685-GA -> 7/15/23."""
    latest = max(begin_date, declaration_date, SECURE20_ENACTED)
    return latest + _dt.timedelta(days=QD_REPAY_PERIOD_DAYS)


def _line1e(item_b_year, new_disaster_count, repeat_disaster_count, prior_year_qdds):
    """The 1a-1e ladder (col (b)). Single NEW disaster -> skip to 1e = the limit. Otherwise:
    1a = limit x repeat disasters; 1b = prior-year QDDs for those disasters; 1c = 1a - 1b;
    1d = limit x new disasters; 1e = 1c + 1d (the face's own sum). Returns (l1a, l1b, l1c, l1d, l1e)."""
    limit = _qdd_limit(item_b_year)
    if repeat_disaster_count == 0 and new_disaster_count == 1 and not prior_year_qdds:
        return (0, 0, 0, 0, limit)
    l1a = limit * repeat_disaster_count
    l1b = float(prior_year_qdds or 0)
    l1c = l1a - l1b
    l1d = limit * new_disaster_count
    return (l1a, l1b, l1c, l1d, l1c + l1d)


def _line1d_cap_ok(line1d, item_b_year, disaster_count) -> bool:
    """F8915F-003 (Active): 'PriorYrNotRptDistributionAmt' must not be greater than 22000 times
    the number of qualified disasters ($100,000-times for the 2020 vintage)."""
    return float(line1d or 0) <= _qdd_limit(item_b_year) * int(disaster_count)


def _line5b(sum_2_to_4_col_a, line5a_nonqualified, line1e):
    """The Rev-12-2025 three-step: 5b(a) = sum(lines 2-4 col (a)) - 5a; 5b(b) = min(5b(a), 1e).
    Lines 2-4 col (b) then allocate to 5b(b) by any reasonable method. Returns (l5b_a, l5b_b)."""
    l5b_a = max(0.0, float(sum_2_to_4_col_a or 0) - float(line5a_nonqualified or 0))
    return (l5b_a, min(l5b_a, float(line1e or 0)))


def _line7_excess(sum_2_to_4_col_a, line6) -> float:
    """Line 7 = excess of the sum of lines 2-4 col (a) over line 6 — reported as normal IRA/
    pension income per the return instructions; MAY be subject to the additional tax (unlike
    line 6, which is waived)."""
    return max(0.0, float(sum_2_to_4_col_a or 0) - float(line6 or 0))


def _spread_amount(taxable, opt_out) -> float:
    """Lines 11/22: the taxable amount spreads over 3 years (amount / 3.0) unless the opt-out box
    is checked (full inclusion this year). The face prints 'divided by 3.0' with NO rounding
    direction — whole-dollar convention FLAGGED in W2 (the 9465 ÷72 class); the pure helper
    returns the raw quotient."""
    t = float(taxable or 0)
    return t if opt_out else t / SPREAD_YEARS


def _optout_boxes_consistent(part2_engaged, box11, part3_engaged, box22) -> bool:
    """'You must check the box on this line if you check the box on line 22' (and vice versa):
    when BOTH Part II and Part III are engaged, the two opt-out boxes must match."""
    if part2_engaged and part3_engaged:
        return bool(box11) == bool(box22)
    return True


def _part_taxable(income_total, repayments) -> float:
    """Lines 15/26: income total minus repayments, floored at -0-."""
    return max(0.0, float(income_total or 0) - float(repayments or 0))


def _repayment_deadline(receipt_date):
    """QDD repayment deadline: 'You have 3 years from the day after the date you received the
    distribution' — amounts paid later than 3 years and 1 day after receipt can't be repayments."""
    day_after = receipt_date + _dt.timedelta(days=1)
    return _dt.date(day_after.year + REPAY_YEARS, day_after.month, day_after.day)


def _qd_receipt_window_ok(receipt_date, disaster_begin, disaster_end) -> bool:
    """Part IV receipt window: 'received no more than 180 days before the first day of the
    disaster and no later than 30 days after the last day of the disaster.'"""
    lo = disaster_begin - _dt.timedelta(days=QD_WINDOW_BEFORE_DAYS)
    hi = disaster_end + _dt.timedelta(days=QD_WINDOW_AFTER_DAYS)
    return lo <= receipt_date <= hi


def _efile_year_blockers(item_a_year, item_b_year, return_tax_year=2025) -> list:
    """The two year-enum rejects, TY2025 arms: F8915F-002-01 (item A must not be 2026/2027/2028)
    and F8915F-001-01 (item B must not be 2026/2027)."""
    blockers = []
    if int(item_a_year) > int(return_tax_year):
        blockers.append("F8915F-002-01")
    if int(item_b_year) > int(return_tax_year):
        blockers.append("F8915F-001-01")
    return blockers


AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("qdd_8915f", "Form 8915-F qualified disaster distributions: the 3-part QDD test, 179/180-day "
     "periods, the $22,000-per-disaster cap, 3-year spread + repayments, Part IV main-home "
     "distributions, the 8606 ties, and the IRS8915F MeF document (max 6)."),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_F8915F", "source_type": "federal_form", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Form 8915-F (Rev. 12-2025) — Qualified Disaster Retirement Plan Distributions and Repayments",
        "citation": "Form 8915-F (Rev. December 2025), Cat. No. 75585Y, Attachment Seq. 915, OMB 1545-0074",
        "issuer": "Internal Revenue Service", "official_url": "https://www.irs.gov/pub/irs-pdf/f8915f.pdf",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.5, "topics": ["qdd_8915f"],
        "excerpts": [{
            "excerpt_label": "Header + items A-D + the separate-spouse rule (Rev. 12-2025 verbatim)",
            "excerpt_text": (
                "Attach to Form 1040, 1040-SR, or 1040-NR. Name. If married, file a separate form for each "
                "spouse required to file Form 8915-F. See instructions. Before you begin: use Form 8915-F for "
                "2021 and later disasters. Also, use it after 2020 for coronavirus-related and other 2020 "
                "disasters instead of Form 8915-E. Major Disaster Declarations at FEMA.gov/disaster/"
                "declarations provides the only qualified disasters and their FEMA numbers for item C. 'This "
                "year' (as used on this form) is the year of the form you check in item A. Item A: tax year "
                "for which you are filing form (check only one box): 2021-2028, Other. Item B: calendar year "
                "in which qualified disaster(s) began (check only one box): 2020-2027, Other. Item C: FEMA "
                "number for each of your qualified disasters for the year checked in item B. Use item D, not "
                "item C, for the coronavirus. Item D: if your only disaster, or one of your disasters, is the "
                "coronavirus, check this box. Don't list the coronavirus in item C. [Charts 1 and 2 route "
                "which lines to use; STOP arms print 'You can't use Form 8915-F.']"
            ),
            "summary_text": "The forever-form identity mechanics: items A/B name the instance, item C = FEMA DR numbers only, item D = coronavirus only; married couples file SEPARATE forms per spouse; Charts 1/2 route line usage.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "Part I: the 1a-1e ladder + the NEW 5a/5b + lines 6-7 (Rev. 12-2025 verbatim)",
            "excerpt_text": (
                "Line 1a(ii): if you checked 2021 or later in both item A and item B (for 2021 and later "
                "disasters, the limit is $22,000, not $100,000, per disaster): if you listed only one disaster "
                "in the Part I Disaster Table and a prior year's Form 8915-F doesn't list that disaster in "
                "item C, skip to line 1e and enter $22,000 there. If you listed only one disaster and a prior "
                "year's Form 8915-F lists that disaster, complete lines 1a through 1e, entering $22,000 on "
                "line 1a. Line 1b: enter the total qualified disaster distributions made to you in prior "
                "year(s) for all disasters in the Part I Disaster Table. Line 1c: subtract line 1b from line "
                "1a. Line 1d: enter $22,000 ($100,000 if you checked 2020 in item B) times the number of "
                "qualified disasters that you entered in the Part I Disaster Table but didn't enter in item C "
                "on a prior year's Form 8915-F. Line 1e: total available qualified disaster distribution "
                "amount for this year — the sum of lines 1c and 1d; if zero, complete lines 2-4 in column (a), "
                "skip line 5, enter -0- on line 6. Line 5a: enter the total distributions from lines 2 through "
                "4 in column (a) that aren't qualified disaster distributions. Line 5b: (1) enter on 5b column "
                "(a) the sum of lines 2-4 column (a) reduced by line 5a; (2) enter on 5b column (b) the "
                "smaller of 5b column (a) or line 1e; (3) allocate lines 2-4 column (b) by any reasonable "
                "method so their sum equals 5b column (b). Line 6: total qualified disaster distributions — "
                "the amount from 5b column (b). The additional tax for early withdrawals is waived for this "
                "amount. Line 7: taxable amount — the excess of the sum of lines 2-4 column (a) over line 6; "
                "report as IRA and/or pension and annuity distributions per your return's instructions."
            ),
            "summary_text": "The single-new-disaster shortcut (1e = $22,000 direct); 1c = 1a-1b; 1d = limit x new disasters; 1e = 1c+1d; the Rev-12-2025 5a/5b redesign (5b(b) = min(5b(a), 1e), reasonable-method allocation); line 6 = waived amount; line 7 = normally-taxed excess.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "Parts II-IV: spread/opt-out, worksheets, the 8606 ties, landings (Rev. 12-2025 verbatim)",
            "excerpt_text": (
                "Line 11: the entire taxable amount on line 10 will be spread over 3 years unless you elect to "
                "have it taxed in this year. If you elect NOT to spread, check this box and enter the amount "
                "from line 10. Otherwise, enter the amount from line 10 divided by 3.0. You must check the box "
                "on this line if you check the box on line 22. Line 12: the amount from Worksheet 2 — your "
                "income for prior years from other-than-IRA qualified disaster distributions; attach your "
                "completed Worksheet 2 to the back of this form. Line 14: total repayment from Worksheet 3; "
                "attach. Line 15: subtract line 14 from line 13; if zero or less, enter -0-; include in the "
                "total on line 5b of this year's Form 1040. Part III before you begin: complete this year's "
                "Form 8606, Nondeductible IRAs, if required. Line 18: the amount from this year's Form 8606, "
                "line 15b — but if you are entering amounts on other Forms 8915-F for this year, only the "
                "amount attributable to Form 8915-F distributions for THIS form. Line 19: same for Form 8606, "
                "line 25b. Line 20: the amount from line 3, column (b); don't include amounts reported on Form "
                "8606. Line 22: [the IRA spread/opt-out — must match line 11]. Line 26: subtract 25 from 24; "
                "include in the total on line 4b of this year's Form 1040. Part IV line 28: total qualified "
                "distributions received this year for the purchase or construction of a main home; if you "
                "included an amount from line 7 on line 28, reduce line 7 by that amount; don't include "
                "amounts on this year's Form 8606, or on line 8 or 20. Line 32: taxable amount = 30 - 31; from "
                "an IRA -> line 4b; from a retirement plan (other than an IRA) -> line 5b. Note: you may be "
                "subject to an additional tax on the amount on line 32."
            ),
            "summary_text": "The 11<->22 opt-out consistency sentence; worksheets 2-5 attach to the back; the 8606 15b/25b attributable-to-this-form ties; the landings (15 -> 1040 5b; 26 -> 4b; 32 -> 4b or 5b with additional-tax exposure).",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "IRS_I8915F", "source_type": "federal_form", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Instructions for Form 8915-F (Rev. 12-2025)",
        "citation": "i8915f (Rev. December 2025), Cat. No. 37509G, dated Dec 22 2025 (73 pp incl. Appendices A-D)",
        "issuer": "Internal Revenue Service", "official_url": "https://www.irs.gov/pub/irs-pdf/i8915f.pdf",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.5, "topics": ["qdd_8915f"],
        "excerpts": [{
            "excerpt_label": "QDD requirements + the designation rule + the not-QDD list (i8915f 12-2025 verbatim)",
            "excerpt_text": (
                "Qualified disaster distributions must meet the following criteria... separately for each of "
                "your disasters in item C. 1. The distribution was made... for 2021 and later disasters, "
                "within the disaster's qualified disaster distribution period. 2. Your main home was located "
                "in a qualified disaster area at any time during the disaster period... The qualified disaster "
                "area is the state, territory, or tribal government in which the disaster occurs. 3. You "
                "sustained an economic loss because of the disaster(s)... examples include (a) loss, damage "
                "to, or destruction of real or personal property; (b) loss related to displacement from your "
                "home; or (c) loss of livelihood due to temporary or permanent layoffs. If (1) through (3) "
                "apply, you can generally designate ANY distribution (including periodic payments and required "
                "minimum distributions) from an eligible retirement plan as a qualified disaster distribution, "
                "regardless of whether the distribution was made on account of a qualified disaster... without "
                "regard to your need or the actual amount of your economic loss. A reduction or offset of your "
                "account balance... to repay a loan can also be designated. A qualified disaster is a disaster "
                "that the President has declared as a major disaster ('DR' FEMA numbers). NOT qualified "
                "disaster distributions: corrective distributions under the section 415 limitations; excess "
                "elective deferrals under 402(g), excess contributions under 401(k), excess aggregate "
                "contributions under 401(m); loans treated as deemed distributions under 72(p); dividends "
                "under 404(k); the cost of current life insurance protection; prohibited allocations under "
                "409(p); permissible withdrawals under 414(w); distributions of premiums for accident or "
                "health insurance. Limit: for each qualified 2021 or later disaster, the total of your "
                "qualified disaster distributions from all plans is limited to $22,000 ($100,000 for each "
                "qualified 2020 disaster). You may allocate the amount among the plans by any reasonable "
                "method. Eligible retirement plan: a qualified pension, profit-sharing, or stock bonus plan "
                "(including a 401(k)); a qualified annuity plan; a tax-sheltered annuity contract; a "
                "governmental section 457 deferred compensation plan; an IRA."
            ),
            "summary_text": "The 3-part QDD test; the any-distribution designation rule (RMDs and periodic payments qualify; loan offsets too); DR-major-declarations only; the 8-item not-QDD list; the $22,000/$100,000 all-plans per-disaster cap with reasonable-method allocation; the eligible-plan list.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "The 179-day distribution period + published date examples (i8915f 12-2025 verbatim)",
            "excerpt_text": (
                "The qualified disaster distribution period for a qualified disaster will begin on the date "
                "the disaster begins and will end 179 days after whichever of the following occurs the latest: "
                "disaster beginning date; disaster declaration date; December 29, 2022. Major disasters "
                "declared on or before December 29, 2022 [that began in 2021 or 2022]: the period ended on "
                "June 26, 2023 — exactly 179 days after December 29, 2022. Example 1: Washington Severe Winter "
                "Storm... (DR-4682-WA) (beginning date November 3, 2022) (declaration date January 12, 2023) — "
                "qualified disaster distributions could be made through July 10, 2023; July 10, 2023, is "
                "exactly 179 days after January 12, 2023. Example 2: Havasupai Tribe Flooding Event (DR-4681) "
                "(beginning October 1, 2022) (declared December 30, 2022) — through June 27, 2023; exactly 179 "
                "days after December 30, 2022. Example 3: Georgia Severe Weather (DR-4685-GA) (beginning "
                "January 12, 2023) (declared January 16, 2023) — through July 14, 2023; exactly 179 days after "
                "January 16, 2023. [Appendix C counts the 179 days.] Generally, a qualified disaster "
                "distribution is included in your income in equal amounts over 3 years, beginning with the "
                "year in which the distribution was made. However, if you elect, you can include the entire "
                "distribution in your income in the year of the distribution. Qualified disaster distributions "
                "aren't subject to the additional 10% tax (or the 25% additional tax for certain distributions "
                "from traditional SIMPLE and Roth SIMPLE IRAs) on early distributions and aren't required to "
                "be reported on Form 5329. However, the amount on line 7 of your Form 8915-F may be subject to "
                "the additional tax. If a taxpayer who spread the income... dies before the last tax year of "
                "that 3-year period, the distribution may no longer be spread over 3 years — the remainder "
                "must be reported on the return of the deceased taxpayer (line 13 and/or line 24). Not "
                "eligible for the 20% capital gain election or the 10-year tax option (Form 4972)."
            ),
            "summary_text": "The 179-day period formula with its three latest-of triggers and THREE published example pins (DR-4682-WA 7/10/23; DR-4681 6/27/23; DR-4685-GA 7/14/23); the 3-year spread default + opt-out; the 10%/25% waiver + never-on-5329 (line 7 excepted); the death-collapse rule; no 4972 options.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "Repayments: 3 years + 1 day, the Rudy carryback examples, exceptions (i8915f 12-2025 verbatim)",
            "excerpt_text": (
                "You can generally repay any portion of a qualified disaster distribution that is eligible for "
                "tax-free rollover treatment to an eligible retirement plan. Your repayment can't be made any "
                "earlier than the day after the date you received the qualified disaster distribution. You "
                "have 3 years from the day after the date you received the distribution to make a repayment; "
                "amounts paid later than 3 years and 1 day after you received the distribution can't be "
                "repayments. The amount of your repayment cannot be more than the amount of the original "
                "distribution. Amounts repaid are treated as a trustee-to-trustee transfer and are not "
                "included in income; for purposes of the one-rollover-per-year limitation for IRAs, a "
                "repayment to an IRA is not considered a rollover. Include on this year's Form 8915-F any "
                "repayments you made before filing this year's return; do not include repayments made later "
                "than the due date (including extensions) — you may report those on next year's return or "
                "carry the repayments back to an earlier year. Example 1: in 2022, Rudy made a qualified 2022 "
                "disaster distribution from their traditional IRA [spread over 3 years]... Rudy made a "
                "repayment in 2024 before timely filing their 2023 return: Rudy includes those repayments on "
                "their 2023 Form 8915-F (2022 disasters); any excess may be carried back to 2022 on an amended "
                "2022 Form 8915-F or forward to 2024. Example 2: same facts except the repayments came after "
                "the due date (including extensions) of Rudy's 2023 return: Rudy cannot include them on the "
                "2023 form — they reduce the 2024 income, and any excess may be carried back on an amended "
                "2022 or 2023 Form 8915-F. Exceptions — you cannot repay: 1. Qualified disaster distributions "
                "received as a beneficiary (other than a surviving spouse); 2. Required minimum distributions; "
                "3. Any distribution (other than from an IRA) that is one of a series of substantially equal "
                "periodic payments made (at least annually) for a period of 10 years or more, your life or "
                "life expectancy, or the joint lives or joint life expectancies of you and your beneficiary."
            ),
            "summary_text": "Repayment mechanics: day-after to 3-years-and-1-day; capped at the original; trustee-to-trustee (not a rollover); this-year inclusion requires before-filing AND by-due-date; later -> forward or carryback amend (both Rudy examples); the three can't-repay exceptions.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "Part IV qualified distributions: requirements, the 180-day repayment period, re-designation (i8915f 12-2025 verbatim)",
            "excerpt_text": (
                "A qualified distribution for the purchase or construction of a main home in a qualified 2021 "
                "or later disaster area must meet ALL of the following: 1. For qualified 2021 disasters, the "
                "first day of the disaster can be no earlier than January 26, 2021 (no restriction for later "
                "disasters). 2. The distribution was a hardship distribution from a 401(k) plan, a hardship "
                "distribution from a tax-sheltered annuity contract, or a qualified first-time homebuyer "
                "distribution from an IRA. 3. The distribution was received no more than 180 days before the "
                "first day of the disaster and no later than 30 days after the last day of the disaster. "
                "4. The distribution was to be used to purchase or construct a main home in the disaster's "
                "qualified disaster area and the main home must not have been purchased or constructed because "
                "of the disaster. A qualified distribution is included in your income in the year of the "
                "distribution; unlike with qualified disaster distributions, the income can't be spread over 3 "
                "years and the repayment period is much shorter than 3 years. The qualified distribution "
                "repayment period for each disaster will begin on the date the disaster begins and will end "
                "180 days after whichever of the following occurs the latest: disaster beginning date; "
                "disaster declaration date; December 29, 2022. Example 1: DR-4682-WA — repaid through July 11, "
                "2023 (exactly 180 days after January 12, 2023). Example 2: DR-4681 — through June 28, 2023. "
                "Example 3: DR-4685-GA — through July 15, 2023. If the qualified distribution (or any portion) "
                "is not repaid on or before the last day of the repayment period, it may be taxable and may be "
                "subject to the additional 10% tax (or the additional 25% tax for certain traditional SIMPLE "
                "and Roth SIMPLE IRAs). Designating: you may be able to designate a qualified distribution as "
                "a qualified disaster distribution if it was not repaid by the period's last day and it can "
                "otherwise be treated as a qualified disaster distribution. [Recent Development 20-Dec-2024: "
                "Appendix D in the Rev. Jan-2024 instructions 'inadvertently provides taxpayers with 1 less "
                "day than is granted for repayments' — corrected in the current tables; the 179-vs-180 "
                "distinction is real and pinned.]"
            ),
            "summary_text": "Part IV: hardship-401(k)/TSA/FTHB-IRA only; the [-180d, +30d] receipt window; full-year income (no spread); the 180-day repayment period (NOT 179 — the IRS's own Appendix D once got this wrong by one day) with three published pins one day after the Part-I pins; unrepaid -> taxable + additional-tax exposure, or re-designate as a QDD.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "MEF_8915F", "source_type": "official_guidance", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "MeF IRS8915F TY2025v5.3 — schema + the F8915F business rules",
        "citation": "IRS8915F.xsd (2025v5.3 Final, released Apr 23 2026; ReturnData1040 slot, maxOccurs=6) + 1040_Business_Rules_2025v5.3.csv",
        "issuer": "Internal Revenue Service",
        "official_url": "https://www.irs.gov/e-file-providers/modernized-e-file-mef-schemas-and-business-rules",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.0, "topics": ["qdd_8915f"],
        "excerpts": [{
            "excerpt_label": "IRS8915F structure + the 3 Active business rules (2025v5.3 verbatim substance)",
            "excerpt_text": (
                "IRS8915F rides ReturnData1040 with maxOccurs=6; each document carries its own PersonNm + SSN "
                "(the separate-spouse-form and multiple-item-B-year instances). Items A/B are XSD choices: "
                "TaxYearFilingFormCd enumerates 2022-2028 (2021 rides OtherTaxYearFilingFormInd, a checkbox "
                "with fixed otherTaxYrCd='2021'); CalendarYrDisasterCd enumerates 2021-2027 (2020 rides "
                "OtherCalendarYrDisasterInd). FEMADisasterDeclarationNum is pattern-locked (NNNN-DR-XX / "
                "DR-NNNN-XX / DR-NNNN; DR and EM prefixes), item C max 20. Part I: FEMADisasterDeclarationGrp "
                "max 20 (number + DisasterDeclarationDt + DisasterBeginDt) + MultipleFEMADisastersInd + "
                "DistributionDt unbounded + the 1a-1e elements (QualifiedDisasterLimitAmt / "
                "PriorYrRptQlfyDistributionsAmt / PriorYrRptDistriAllocationAmt / PriorYrNotRptDistributionAmt "
                "/ TotalCYAvailDistributionsAmt) + lines 2/3/4 as QualifiedRetireDistriGrpType col (a)/(b) "
                "pairs + the 5a/5b group + LimitationDistributionsAmt (6) + TaxableExcessAllocationAmt (7). "
                "Parts II/III: the 8/16 BooleanType gates, OptOutSpreadThreeYrsInd (11/22), "
                "PriorYrSelectedDistriAmt (12/23) and the repayment elements (14/25) each carrying "
                "referenceDocumentId/referenceDocumentName='BinaryAttachment' (the attach-worksheet-to-back "
                "e-file mirror); the 8606 ties NondedIRAQlfyDisasterDistriAmt (18, 8606 line 15b) and "
                "RothIRAQlfyDisasterDistriAmt (19, 8606 line 25b). Part IV: FEMADisasterGrp max 10 (adds "
                "DisasterEndDt) + lines 27-32. Business rules (ALL of the F8915F set, Active): F8915F-001-01 — "
                "'CalendarYrDisasterCd' must not have the value 2026 or 2027 for a return filed for Tax Year "
                "2025. F8915F-002-01 — 'TaxYearFilingFormCd' must not have the value 2026, 2027, or 2028 for "
                "a return filed for Tax Year 2025. F8915F-003 — 'PriorYrNotRptDistributionAmt' in "
                "'TotalDistriAllRetirePlansGrp' must not be greater than 22000 times the number of qualified "
                "disasters."
            ),
            "summary_text": "The full document shape (max 6 instances; per-document name/SSN; item A/B XSD choice mechanics; FEMA pattern locks; worksheet BinaryAttachment refs; the 8606-tie elements; Part IV end dates) and the complete 3-rule Active set incl. the F8915F-003 line-1d cap.",
            "is_key_excerpt": True,
        }],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_F8915F", "8915F", "governs"), ("IRS_I8915F", "8915F", "governs"), ("MEF_8915F", "8915F", "governs"),
]


F8915F_FACTS: list[dict] = [
    {"fact_key": "item_a_tax_year", "label": "Item A — tax year for which the form is filed (2021-2028; names the instance)", "data_type": "string", "required": True, "sort_order": 1},
    {"fact_key": "item_b_disaster_year", "label": "Item B — calendar year the qualified disaster(s) began (2020-2027; sets the $22,000/$100,000 limit)", "data_type": "string", "required": True, "sort_order": 2},
    {"fact_key": "fema_numbers", "label": "Item C — FEMA DR number(s) for the item-B year (max 20; DR majors only; NEVER the coronavirus)", "data_type": "string", "required": False, "sort_order": 3},
    {"fact_key": "coronavirus", "label": "Item D — coronavirus checkbox (repayment/income-continuation arms only; no new distributions after 2020)", "data_type": "boolean", "required": False, "sort_order": 4},
    {"fact_key": "disaster_begin_date", "label": "Per-disaster — FEMA beginning date (starts both periods)", "data_type": "date", "required": False, "sort_order": 5},
    {"fact_key": "disaster_declaration_date", "label": "Per-disaster — FEMA declaration date (a latest-of trigger)", "data_type": "date", "required": False, "sort_order": 6},
    {"fact_key": "disaster_end_date", "label": "Per-disaster — FEMA ending date (Part IV table + the +30d receipt window)", "data_type": "date", "required": False, "sort_order": 7},
    {"fact_key": "distribution_dates", "label": "Part I — date(s) of distribution(s) made this year (each must sit inside the 179-day period)", "data_type": "string", "required": False, "sort_order": 8},
    {"fact_key": "dist_other_than_ira", "label": "L2(a) — this year's distributions from retirement plans other than IRAs", "data_type": "decimal", "required": False, "sort_order": 9},
    {"fact_key": "dist_traditional_ira", "label": "L3(a) — this year's traditional IRA distributions (incl. trad SEP/SIMPLE)", "data_type": "decimal", "required": False, "sort_order": 10},
    {"fact_key": "dist_roth_ira", "label": "L4(a) — this year's Roth IRA distributions (incl. Roth SEP/SIMPLE)", "data_type": "decimal", "required": False, "sort_order": 11},
    {"fact_key": "nonqualified_portion", "label": "L5a(a) — the portion of lines 2-4(a) NOT attributable to qualified disaster distributions (NEW Rev-12-2025 line)", "data_type": "decimal", "required": False, "sort_order": 12},
    {"fact_key": "prior_year_qdds", "label": "L1b — total QDDs taken in prior years for the repeat disasters in the Part I table", "data_type": "decimal", "required": False, "sort_order": 13},
    {"fact_key": "new_disaster_count", "label": "Context — disasters in the Part I table NOT on a prior year's form (drives L1d; F8915F-003 caps it)", "data_type": "integer", "required": False, "sort_order": 14},
    {"fact_key": "repeat_disaster_count", "label": "Context — disasters in the Part I table ALSO on a prior year's form (drives L1a)", "data_type": "integer", "required": False, "sort_order": 15},
    {"fact_key": "cost_of_distributions_p2", "label": "L9 — applicable cost of other-than-IRA distributions", "data_type": "decimal", "required": False, "sort_order": 16},
    {"fact_key": "opt_out_spread_p2", "label": "L11 box — elect NOT to spread the other-than-IRA taxable amount (MUST match L22)", "data_type": "boolean", "required": False, "sort_order": 17},
    {"fact_key": "opt_out_spread_p3", "label": "L22 box — elect NOT to spread the IRA taxable amount (MUST match L11)", "data_type": "boolean", "required": False, "sort_order": 18},
    {"fact_key": "prior_year_income_p2", "label": "L12 — Worksheet 2 prior-year spread income (worksheet attaches to the back; engine-computed)", "data_type": "decimal", "required": False, "sort_order": 19},
    {"fact_key": "prior_year_income_p3", "label": "L23 — Worksheet 4 prior-year spread income (attaches; engine-computed)", "data_type": "decimal", "required": False, "sort_order": 20},
    {"fact_key": "repayments_p2", "label": "L14 — Worksheet 3 repayments of other-than-IRA QDDs (before filing, by the due date, within 3y+1d)", "data_type": "decimal", "required": False, "sort_order": 21},
    {"fact_key": "repayments_p3", "label": "L25 — Worksheet 5 repayments of IRA QDDs", "data_type": "decimal", "required": False, "sort_order": 22},
    {"fact_key": "f8606_line15b", "label": "L18 — this year's Form 8606 line 15b, attributable to THIS form's distributions", "data_type": "decimal", "required": False, "sort_order": 23},
    {"fact_key": "f8606_line25b", "label": "L19 — this year's Form 8606 line 25b, attributable to THIS form", "data_type": "decimal", "required": False, "sort_order": 24},
    {"fact_key": "mainhome_distributions", "label": "L28 — Part IV qualified distributions received this year (hardship-401k/TSA/FTHB-IRA; the [-180d,+30d] window)", "data_type": "decimal", "required": False, "sort_order": 25},
    {"fact_key": "mainhome_cost", "label": "L29 — applicable cost of Part IV distributions", "data_type": "decimal", "required": False, "sort_order": 26},
    {"fact_key": "mainhome_repayments", "label": "L31 — Part IV repayments (within the 180-day repayment period only)", "data_type": "decimal", "required": False, "sort_order": 27},
    {"fact_key": "taxpayer_died_this_year", "label": "Context — taxpayer died before the last spread year (collapses the remaining spread onto this return)", "data_type": "boolean", "required": False, "sort_order": 28},
]

F8915F_RULES: list[dict] = [
    {"rule_id": "R-8915F-WHO", "title": "Who files; the forever-form identity; separate form per spouse", "rule_type": "routing",
     "formula": "File for the item-A year when ANY of: a QDD was made this year; a qualified distribution (Part IV) was received; a prior-year QDD is still spreading (this year within the 3-year period); a repayment was made and the filing window hasn't expired. Items A+B name the instance ('2025 Form 8915-F (2024 disasters)'); one form per item-B year; MARRIED = a separate form per spouse. DON'T use for: 2019 disasters (Form 8915-D); distributions MADE in 2020 (2020 Form 8915-E); coronavirus rides item D only (no new coronavirus distributions after 2020)",
     "inputs": ["item_a_tax_year", "item_b_disaster_year", "fema_numbers", "coronavirus"], "outputs": ["form_required"], "sort_order": 1,
     "description": "W1. The Who Must File four-arm test + the Charts 1/2 STOP routing; the name/SSN ride each document."},
    {"rule_id": "R-8915F-QDD", "title": "The 3-part QDD test + the any-distribution designation rule", "rule_type": "validation",
     "formula": "Per disaster: (1) distribution made within the qualified disaster distribution period; (2) main home in the qualified disaster area (the state/territory/tribal government of the disaster) at any time during the disaster period; (3) economic loss sustained (property loss/damage/destruction, displacement, or lost livelihood). All three -> ANY eligible-plan distribution (incl. periodic payments and RMDs, and plan loan offsets) may be designated a QDD regardless of need or loss amount. Qualified disaster = Presidentially-declared MAJOR ('DR' FEMA numbers only). NOT QDDs: §415 correctives / 402(g)-401(k)-401(m) excesses / 72(p) deemed loans / 404(k) dividends / life-insurance cost / 409(p) allocations / 414(w) withdrawals / accident-health premiums",
     "inputs": ["fema_numbers", "disaster_begin_date", "disaster_declaration_date", "distribution_dates"], "outputs": ["qdd_eligible"], "sort_order": 2,
     "description": "W1. The designation rule is the practitioner surprise: RMDs and ordinary periodic payments qualify once the three tests hold."},
    {"rule_id": "R-8915F-PERIOD", "title": "The 179-day qualified disaster distribution period", "rule_type": "calculation",
     "formula": "period_start = disaster beginning date; period_end = 179 days after the LATEST of (beginning date, declaration date, 2022-12-29). Published pins: DR-4682-WA (11/3/22, 1/12/23) -> 7/10/23; DR-4681 (10/1/22, 12/30/22) -> 6/27/23; DR-4685-GA (1/12/23, 1/16/23) -> 7/14/23. Appendix C is the IRS's own day-count of THIS formula — derive, never re-encode the table",
     "inputs": ["disaster_begin_date", "disaster_declaration_date"], "outputs": ["qdd_period_end"], "sort_order": 3,
     "description": "W1. SECURE 2.0 removed the set ending date — per-disaster calculation only."},
    {"rule_id": "R-8915F-LIMIT", "title": "$22,000 per disaster, ALL plans, across years (F8915F-003)", "rule_type": "validation",
     "formula": "For each 2021+ disaster the total QDDs from all plans is limited to $22,000 ($100,000 for item-B-2020 disasters) — an across-years per-disaster cap allocated among plans by any reasonable method. MeF F8915F-003 (Active): line 1d must not exceed 22000 x the number of qualified disasters",
     "inputs": ["item_b_disaster_year", "new_disaster_count"], "outputs": ["qdd_limit"], "sort_order": 4,
     "description": "W1. The cap is per DISASTER (not per year, not per plan); the 1a-1e ladder meters what remains."},
    {"rule_id": "R-8915F-PART1", "title": "Part I: the 1a-1e ladder + the 5a/5b redesign + lines 6-7", "rule_type": "calculation",
     "formula": "Single NEW disaster (no prior-year listing) -> skip to 1e = $22,000. Else: 1a = limit x repeat disasters; 1b = prior-year QDDs for those; 1c = 1a - 1b; 1d = limit x new disasters; 1e = 1c + 1d (zero -> col (a) only, line 6 = -0-, no Parts II/III amounts). NEW line 5a = the non-QDD portion of sum(2-4(a)); 5b(a) = sum(2-4(a)) - 5a; 5b(b) = min(5b(a), 1e); allocate 2-4(b) by any reasonable method summing to 5b(b). Line 6 = 5b(b) (the 10%/25% early tax is WAIVED on this amount; never on Form 5329). Line 7 = sum(2-4(a)) - 6 -> normal IRA/pension income; MAY owe the additional tax. Worksheet 1B mandatory when: not using it already + >1 plan type + 5b(a) > 1e",
     "inputs": ["dist_other_than_ira", "dist_traditional_ira", "dist_roth_ira", "nonqualified_portion", "prior_year_qdds", "new_disaster_count", "repeat_disaster_count"],
     "outputs": ["line1e", "line5b_b", "line6", "line7"], "sort_order": 5,
     "description": "W2. The Rev-12-2025 redesign (5a is NEW; old 5 -> 5b) — the 2025v5.3 XSD already models it."},
    {"rule_id": "R-8915F-SPREAD", "title": "3-year spread, the opt-out pairing, death-collapse", "rule_type": "calculation",
     "formula": "Default: the Part II line 10 / Part III line 21 taxable amounts spread in equal amounts over 3 years beginning with the distribution year (line 11/22 = amount / 3.0 — the face prints NO rounding; whole-dollar convention FLAGGED). Opt-out: check the box + enter the full amount; 'You must check the box on this line if you check the box on line 22' — the two boxes MUST MATCH when both parts are engaged. Death before the last spread year: the remainder reports on the decedent's final return (line 13/24). Not eligible for Form 4972 options",
     "inputs": ["opt_out_spread_p2", "opt_out_spread_p3", "taxpayer_died_this_year"], "outputs": ["line11", "line22"], "sort_order": 6,
     "description": "W2. The ÷3.0 convention is the walk's rounding flag (the 9465 ÷72 class)."},
    {"rule_id": "R-8915F-REPAY", "title": "QDD repayments: 3 years + 1 day; forward/carryback", "rule_type": "validation",
     "formula": "Repay any rollover-eligible portion to an eligible plan (401(k)/qualified annuity/TSA/governmental 457/IRA); earliest = the day AFTER receipt; deadline = 3 years from the day after receipt (later than 3 years + 1 day = never a repayment); capped at the original distribution; treated as trustee-to-trustee (not income; not a rollover for the IRA one-per-year rule). THIS year's form takes only repayments made before filing AND by the due date incl. extensions; later repayments -> next year's form OR carry back via amended 8915-F/1040-X (both Rudy examples pinned). CANNOT repay: non-spouse-beneficiary QDDs; RMDs; SEPP series (10-yr/life/joint-lives)",
     "inputs": ["repayments_p2", "repayments_p3"], "outputs": ["repayment_valid"], "sort_order": 7,
     "description": "W3. Lines 15/26 = 13-14 / 24-25 floored at -0-; landings 1040 5b / 4b."},
    {"rule_id": "R-8915F-PART3", "title": "Part III: the Form 8606 ties (lines 18/19/20)", "rule_type": "reconciliation",
     "formula": "Before Part III: complete this year's Form 8606 if required. Line 18 = 8606 line 15b, line 19 = 8606 line 25b — each limited to the amount ATTRIBUTABLE TO THIS FORM's distributions when multiple 8915-Fs exist. Line 20 = line 3(b) amounts NOT reported on the 8606. Line 21 = 18 + 19 + 20; 22 spreads (matches 11); 26 = 24 - 25 floored -> 1040 line 4b",
     "inputs": ["f8606_line15b", "f8606_line25b", "dist_traditional_ira"], "outputs": ["line21", "line26"], "sort_order": 8,
     "description": "W3. The 8606 seam — the tts 8606 unit (s75 MeF leg) already produces 15b/25b; the tie is per-form attributable."},
    {"rule_id": "R-8915F-PART4", "title": "Part IV main-home qualified distributions", "rule_type": "validation",
     "formula": "Requirements (ALL): hardship distribution from a 401(k) or TSA, or a first-time-homebuyer IRA distribution; received within [disaster begin - 180 days, disaster end + 30 days]; intended for a main home IN the disaster area that was NOT purchased/constructed because of the disaster (2021 disasters: begin >= 1/26/2021). Income: fully taxable in the distribution year — NO 3-year spread. Repayment: only during the qualified distribution repayment period = begin date through 180 days (NOT 179 — the Appendix-D off-by-one class) after the latest of (begin, declaration, 12/29/2022); pins DR-4682-WA -> 7/11/23, DR-4681 -> 6/28/23, DR-4685-GA -> 7/15/23. 30 = 28 - 29; 32 = 30 - 31 -> 4b (IRA) or 5b (other); line 32 MAY owe the 10%/25% additional tax. Unrepaid + otherwise-QDD-eligible -> may re-designate as a QDD. Line 28 overlap with line 7 reduces line 7",
     "inputs": ["mainhome_distributions", "mainhome_cost", "mainhome_repayments", "disaster_begin_date", "disaster_declaration_date", "disaster_end_date"],
     "outputs": ["line30", "line32", "qd_repay_period_end"], "sort_order": 9,
     "description": "W3. The 179-vs-180 asymmetry between Part I and Part IV periods is deliberate and pinned both ways."},
    {"rule_id": "R-8915F-EFILE", "title": "The MeF document: IRS8915F max 6 + the year-enum rejects", "rule_type": "validation",
     "formula": "IRS8915F rides ReturnData1040 (2025v5.3) maxOccurs=6; each instance carries PersonNm + SSN (separate spouse forms; multiple item-B years under one item A). Item A/B are XSD choices (A: enum 2022-2028 or the 2021 checkbox; B: enum 2021-2027 or the 2020 checkbox). REJECTS (TY2025): F8915F-002-01 item A must not be 2026/2027/2028; F8915F-001-01 item B must not be 2026/2027; F8915F-003 line 1d <= 22000 x disasters. FEMA numbers pattern-locked (NNNN-DR-XX etc.); item C max 20; Part I disaster groups max 20; Part IV groups max 10 (+ end date). Worksheet lines 12/14/23/25 carry BinaryAttachment referenceDocument attributes (the attach-worksheet-to-back e-file mirror)",
     "inputs": ["item_a_tax_year", "item_b_disaster_year", "new_disaster_count"], "outputs": ["efile_blockers"], "sort_order": 10,
     "description": "W4. Landings: 15 -> 1040 line 5b; 26 -> 4b; 7 -> normal income lines; QDDs never generate a 5329 (the tts 5329-unit seam: suppress the early-tax row for line-6 amounts)"},
]

F8915F_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-8915F-WHO", "IRS_I8915F", "primary", "Who Must File + When Should I Not Use + the forever-form naming"),
    ("R-8915F-WHO", "IRS_F8915F", "secondary", "Items A-D + the separate-spouse header rule + Charts 1/2"),
    ("R-8915F-QDD", "IRS_I8915F", "primary", "QDD requirements + the designation rule + the not-QDD list"),
    ("R-8915F-PERIOD", "IRS_I8915F", "primary", "The 179-day formula + the three published date examples"),
    ("R-8915F-LIMIT", "IRS_I8915F", "primary", "The $22,000/$100,000 all-plans limit + reasonable-method allocation"),
    ("R-8915F-LIMIT", "MEF_8915F", "primary", "F8915F-003 (the line-1d cap)"),
    ("R-8915F-PART1", "IRS_F8915F", "primary", "The 1a-1e ladder + the NEW 5a/5b three-step + lines 6-7 verbatim"),
    ("R-8915F-PART1", "IRS_I8915F", "secondary", "Worksheet 1B trigger + the What's New line-5a note"),
    ("R-8915F-SPREAD", "IRS_F8915F", "primary", "Lines 11/22 verbatim incl. the box-matching sentence"),
    ("R-8915F-SPREAD", "IRS_I8915F", "secondary", "3-year spread default + death-collapse + no-4972"),
    ("R-8915F-REPAY", "IRS_I8915F", "primary", "3y+1d mechanics + the Rudy examples + the exceptions list"),
    ("R-8915F-PART3", "IRS_F8915F", "primary", "Lines 17-21 verbatim (the 8606 15b/25b attributable ties)"),
    ("R-8915F-PART4", "IRS_I8915F", "primary", "Qualified distribution requirements + the 180-day repayment period + re-designation"),
    ("R-8915F-PART4", "IRS_F8915F", "secondary", "Part IV face lines 27-32 + the line-7 overlap reduction"),
    ("R-8915F-EFILE", "MEF_8915F", "primary", "IRS8915F.xsd structure + the 3 Active F8915F rules"),
]

F8915F_LINES: list[dict] = [
    {"line_number": "ITEM_A", "description": "Item A — tax year of the form (names the instance)", "line_type": "input", "source_facts": ["item_a_tax_year"], "sort_order": 1},
    {"line_number": "ITEM_B", "description": "Item B — disaster calendar year (sets the limit)", "line_type": "input", "source_facts": ["item_b_disaster_year"], "sort_order": 2},
    {"line_number": "ITEM_C", "description": "Item C — FEMA DR numbers (max 20; never the coronavirus)", "line_type": "input", "source_facts": ["fema_numbers"], "sort_order": 3},
    {"line_number": "ITEM_D", "description": "Item D — coronavirus checkbox", "line_type": "input", "source_facts": ["coronavirus"], "sort_order": 4},
    {"line_number": "L1A", "description": "L1a(b) — limit x repeat disasters (or the $22,000 single-disaster entry)", "line_type": "calculated", "source_rules": ["R-8915F-PART1"], "sort_order": 5},
    {"line_number": "L1B", "description": "L1b(b) — prior-year QDDs for the repeat disasters", "line_type": "input", "source_facts": ["prior_year_qdds"], "sort_order": 6},
    {"line_number": "L1C", "description": "L1c(b) — L1a - L1b", "line_type": "calculated", "source_rules": ["R-8915F-PART1"], "sort_order": 7},
    {"line_number": "L1D", "description": "L1d(b) — limit x NEW disasters (F8915F-003 caps)", "line_type": "calculated", "source_rules": ["R-8915F-PART1", "R-8915F-LIMIT"], "sort_order": 8},
    {"line_number": "L1E", "description": "L1e(b) — total available QDD amount = L1c + L1d", "line_type": "calculated", "source_rules": ["R-8915F-PART1"], "sort_order": 9},
    {"line_number": "L2", "description": "L2(a)/(b) — other-than-IRA distributions / QDD allocation", "line_type": "input", "source_facts": ["dist_other_than_ira"], "sort_order": 10},
    {"line_number": "L3", "description": "L3(a)/(b) — traditional IRA distributions (incl. SEP/SIMPLE)", "line_type": "input", "source_facts": ["dist_traditional_ira"], "sort_order": 11},
    {"line_number": "L4", "description": "L4(a)/(b) — Roth IRA distributions (incl. Roth SEP/SIMPLE)", "line_type": "input", "source_facts": ["dist_roth_ira"], "sort_order": 12},
    {"line_number": "L5A", "description": "L5a(a) — non-QDD portion of lines 2-4(a) (NEW Rev-12-2025)", "line_type": "input", "source_facts": ["nonqualified_portion"], "sort_order": 13},
    {"line_number": "L5B", "description": "L5b(a)/(b) — sum(2-4(a)) - 5a / min with L1e", "line_type": "calculated", "source_rules": ["R-8915F-PART1"], "sort_order": 14},
    {"line_number": "L6", "description": "L6 — total QDDs (early-withdrawal tax WAIVED; never on 5329)", "line_type": "calculated", "source_rules": ["R-8915F-PART1"], "sort_order": 15},
    {"line_number": "L7", "description": "L7 — taxable excess over L6 (normal income; MAY owe the additional tax)", "line_type": "calculated", "source_rules": ["R-8915F-PART1"], "sort_order": 16},
    {"line_number": "L8", "description": "L8 — Part II gate: the L2(b) amount", "line_type": "calculated", "source_rules": ["R-8915F-PART1"], "sort_order": 17},
    {"line_number": "L9", "description": "L9 — applicable cost of other-than-IRA distributions", "line_type": "input", "source_facts": ["cost_of_distributions_p2"], "sort_order": 18},
    {"line_number": "L10", "description": "L10 — L8 - L9 (the other-than-IRA taxable amount)", "line_type": "calculated", "source_rules": ["R-8915F-PART1"], "sort_order": 19},
    {"line_number": "L11", "description": "L11 — spread (÷3.0) or opt-out box (MUST match L22)", "line_type": "calculated", "source_facts": ["opt_out_spread_p2"], "source_rules": ["R-8915F-SPREAD"], "sort_order": 20},
    {"line_number": "L12", "description": "L12 — Worksheet 2 prior-year income (worksheet attaches)", "line_type": "input", "source_facts": ["prior_year_income_p2"], "sort_order": 21},
    {"line_number": "L13", "description": "L13 — L11 + L12", "line_type": "calculated", "source_rules": ["R-8915F-SPREAD"], "sort_order": 22},
    {"line_number": "L14", "description": "L14 — Worksheet 3 repayments (attaches)", "line_type": "input", "source_facts": ["repayments_p2"], "source_rules": ["R-8915F-REPAY"], "sort_order": 23},
    {"line_number": "L15", "description": "L15 — L13 - L14 floored -> 1040 line 5b", "line_type": "calculated", "source_rules": ["R-8915F-REPAY"], "sort_order": 24},
    {"line_number": "L16", "description": "L16 — Part III gate: L3(b)/L4(b) amounts exist", "line_type": "calculated", "source_rules": ["R-8915F-PART3"], "sort_order": 25},
    {"line_number": "L17", "description": "L17 — 8606-required gate", "line_type": "input", "sort_order": 26},
    {"line_number": "L18", "description": "L18 — 8606 line 15b (attributable to THIS form)", "line_type": "input", "source_facts": ["f8606_line15b"], "source_rules": ["R-8915F-PART3"], "sort_order": 27},
    {"line_number": "L19", "description": "L19 — 8606 line 25b (attributable to THIS form)", "line_type": "input", "source_facts": ["f8606_line25b"], "source_rules": ["R-8915F-PART3"], "sort_order": 28},
    {"line_number": "L20", "description": "L20 — L3(b) amounts not on the 8606", "line_type": "calculated", "source_rules": ["R-8915F-PART3"], "sort_order": 29},
    {"line_number": "L21", "description": "L21 — L18 + L19 + L20 (IRA taxable amount)", "line_type": "calculated", "source_rules": ["R-8915F-PART3"], "sort_order": 30},
    {"line_number": "L22", "description": "L22 — spread (÷3.0) or opt-out box (MUST match L11)", "line_type": "calculated", "source_facts": ["opt_out_spread_p3"], "source_rules": ["R-8915F-SPREAD"], "sort_order": 31},
    {"line_number": "L23", "description": "L23 — Worksheet 4 prior-year income (attaches)", "line_type": "input", "source_facts": ["prior_year_income_p3"], "sort_order": 32},
    {"line_number": "L24", "description": "L24 — L22 + L23", "line_type": "calculated", "source_rules": ["R-8915F-SPREAD"], "sort_order": 33},
    {"line_number": "L25", "description": "L25 — Worksheet 5 repayments (attaches)", "line_type": "input", "source_facts": ["repayments_p3"], "source_rules": ["R-8915F-REPAY"], "sort_order": 34},
    {"line_number": "L26", "description": "L26 — L24 - L25 floored -> 1040 line 4b", "line_type": "calculated", "source_rules": ["R-8915F-REPAY"], "sort_order": 35},
    {"line_number": "L27", "description": "L27 — Part IV 8606-reported gate", "line_type": "input", "sort_order": 36},
    {"line_number": "L28", "description": "L28 — main-home qualified distributions received (window-checked; L7 overlap reduces L7)", "line_type": "input", "source_facts": ["mainhome_distributions"], "source_rules": ["R-8915F-PART4"], "sort_order": 37},
    {"line_number": "L29", "description": "L29 — applicable cost", "line_type": "input", "source_facts": ["mainhome_cost"], "sort_order": 38},
    {"line_number": "L30", "description": "L30 — L28 - L29", "line_type": "calculated", "source_rules": ["R-8915F-PART4"], "sort_order": 39},
    {"line_number": "L31", "description": "L31 — repayments within the 180-day period", "line_type": "input", "source_facts": ["mainhome_repayments"], "source_rules": ["R-8915F-PART4"], "sort_order": 40},
    {"line_number": "L32", "description": "L32 — taxable: L30 - L31 -> 4b (IRA) / 5b (other); additional-tax exposure", "line_type": "calculated", "source_rules": ["R-8915F-PART4"], "sort_order": 41},
    {"line_number": "CALC_PERIOD", "description": "Computed per-disaster 179-day distribution period end", "line_type": "calculated", "source_rules": ["R-8915F-PERIOD"], "sort_order": 42},
    {"line_number": "CALC_REPAYEND", "description": "Computed per-disaster 180-day Part IV repayment period end", "line_type": "calculated", "source_rules": ["R-8915F-PART4"], "sort_order": 43},
    {"line_number": "CALC_EFILE", "description": "Computed e-file blockers (year enums + the 1d cap)", "line_type": "calculated", "source_rules": ["R-8915F-EFILE"], "sort_order": 44},
]

F8915F_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_8915F_YRENUM", "title": "Item A/B year not valid for this return year", "severity": "error",
     "condition": "item A > return tax year, or item B > return tax year",
     "message": "For a return filed for tax year 2025, item A must not be 2026-2028 (MeF F8915F-002-01) and item B must not be 2026-2027 (F8915F-001-01). The item A year is the year of the return the form attaches to; the item B year is when the disaster began.", "notes": "W4. Year-keyed — the enums roll annually."},
    {"diagnostic_id": "D_8915F_1DCAP", "title": "Line 1d exceeds the per-disaster limit", "severity": "error",
     "condition": "line 1d > 22000 x the number of qualified disasters ($100,000-times for 2020-vintage)",
     "message": "Line 1d cannot exceed $22,000 times the number of NEW qualified disasters in the Part I table (MeF F8915F-003; $100,000 per disaster only when item B is 2020). Check the disaster count and the limit multiplication.", "notes": "W1/W4."},
    {"diagnostic_id": "D_8915F_OPTOUT", "title": "Lines 11 and 22 opt-out boxes must match", "severity": "error",
     "condition": "both Part II and Part III engaged and exactly one opt-out box checked",
     "message": "The election NOT to spread the taxable amount over 3 years is all-or-nothing across the form: 'You must check the box on this line if you check the box on line 22' (and vice versa). Check both boxes or neither.", "notes": "W2. Face verbatim on both lines."},
    {"diagnostic_id": "D_8915F_PERIOD", "title": "Distribution outside the 179-day disaster period", "severity": "error",
     "condition": "a distribution date is before the disaster beginning date or after the computed period end",
     "message": "A qualified disaster distribution must be made within the disaster's qualified disaster distribution period: from the disaster beginning date through 179 days after the latest of the beginning date, the declaration date, or December 29, 2022. Distributions outside the window are not QDDs (they may still be ordinary distributions on line 7).", "notes": "W1. The period helpers pin the three published examples."},
    {"diagnostic_id": "D_8915F_CVITEMC", "title": "Coronavirus listed in item C", "severity": "error",
     "condition": "a coronavirus entry in item C",
     "message": "Use item D, not item C, for the coronavirus — item C takes only FEMA DR numbers for the item-B year. Coronavirus-related distributions can't be made after 2020; only repayment and spread-income arms remain (face Chart 1).", "notes": "W1."},
    {"diagnostic_id": "D_8915F_NOTDR", "title": "FEMA number is not a major-disaster (DR) declaration", "severity": "error",
     "condition": "an item-C number without the DR prefix (e.g., EM) or not found as a major declaration",
     "message": "A qualified disaster is one the President declared as a MAJOR disaster — the FEMA number includes 'DR'. Emergency declarations (EM) do not qualify. Verify at FEMA.gov/disaster/declarations; if the disaster is not among the major-declaration results, it cannot go on Form 8915-F.", "notes": "W1. (The XSD pattern admits EM strings; the instructions' DR-only rule is the stricter gate.)"},
    {"diagnostic_id": "D_8915F_SPOUSE", "title": "Married — separate Form 8915-F per spouse", "severity": "warning",
     "condition": "one form carrying both spouses' distributions",
     "message": "If married, file a separate Form 8915-F for each spouse required to file one — each form carries its own name and SSN, and the $22,000-per-disaster limit applies per taxpayer. Don't combine spouses' distributions on one form.", "notes": "W4. The MeF document carries per-instance PersonNm/SSN (max 6 documents)."},
    {"diagnostic_id": "D_8915F_8606GATE", "title": "Complete Form 8606 before Part III", "severity": "warning",
     "condition": "Part III engaged with IRA basis and no 8606",
     "message": "Before you begin Part III: complete this year's Form 8606, Nondeductible IRAs, if required. Line 18 takes the Form 8606 line 15b amount and line 19 the line 25b amount — each limited to the portion attributable to THIS Form 8915-F when multiple forms exist.", "notes": "W3. The tts 8606 unit (s75) is the producing seam."},
    {"diagnostic_id": "D_8915F_RPYLATE", "title": "Repayment outside the allowed window", "severity": "error",
     "condition": "a repayment earlier than the day after receipt, later than 3 years + 1 day, or exceeding the original distribution",
     "message": "A qualified disaster distribution repayment can be made no earlier than the day after receipt and no later than 3 years from the day after the distribution was received; it cannot exceed the original distribution. This year's form takes only repayments made before filing AND by the due date (including extensions) — later repayments go on next year's form or carry back via an amended return.", "notes": "W3. The Rudy examples pin both the forward and carryback directions."},
    {"diagnostic_id": "D_8915F_NOREPAY", "title": "This distribution type cannot be repaid", "severity": "error",
     "condition": "repayment claimed against a non-spouse-beneficiary QDD, an RMD, or a SEPP-series distribution",
     "message": "You cannot repay: qualified disaster distributions received as a beneficiary (other than a surviving spouse); required minimum distributions; or non-IRA distributions in a series of substantially equal periodic payments (10-year/life/joint-lives). Remove the repayment or reclassify the distribution.", "notes": "W3."},
    {"diagnostic_id": "D_8915F_QDWINDOW", "title": "Part IV distribution outside the receipt window", "severity": "error",
     "condition": "a main-home distribution received more than 180 days before the disaster's first day or more than 30 days after its last day",
     "message": "A Part IV qualified distribution must be received no more than 180 days before the first day of the disaster and no later than 30 days after the last day of the disaster — and must be a hardship distribution from a 401(k) or tax-sheltered annuity, or a first-time-homebuyer IRA distribution, intended for a main home in the disaster area that wasn't purchased or constructed because of the disaster.", "notes": "W3."},
    {"diagnostic_id": "D_8915F_QDRPYEND", "title": "Part IV repayment after the 180-day period", "severity": "error",
     "condition": "a line-31 repayment dated after the computed qualified distribution repayment period end",
     "message": "Part IV repayments count only during the qualified distribution repayment period: from the disaster beginning date through 180 days after the latest of the beginning date, declaration date, or December 29, 2022. (Note: 180 days — one day LONGER than the Part I distribution period's 179.) An unrepaid qualified distribution is taxable and may owe the 10%/25% additional tax; if it independently meets the QDD tests, it may be re-designated as a qualified disaster distribution instead.", "notes": "W3. The Appendix-D off-by-one class (the IRS's own Jan-2024 table was 1 day short — corrected)."},
    {"diagnostic_id": "D_8915F_WAIVER", "title": "Early-distribution tax waived on line 6 — never on Form 5329", "severity": "info",
     "condition": "line 6 > 0",
     "message": "Qualified disaster distributions (line 6) aren't subject to the 10% additional tax (or the 25% tax for certain SIMPLE-IRA distributions) and aren't reported on Form 5329. The line 7 excess and the Part IV line 32 amount MAY still owe the additional tax — route those through the normal Form 5329 logic.", "notes": "W4. The tts 5329-unit seam: suppress the early-tax row for line-6 amounts only."},
    {"diagnostic_id": "D_8915F_LANDINGS", "title": "Landing lines: 15 -> 1040 5b; 26 -> 4b; 7 -> normal income", "severity": "info",
     "condition": "informational on compute",
     "message": "Include line 15 in Form 1040 line 5b (pensions taxable amount), line 26 in line 4b (IRA taxable amount), and report the line 7 excess as ordinary IRA/pension income per the return instructions. Part IV line 32 lands on 4b (IRA source) or 5b (other plans). Worksheets 2-5, where used, attach to the back of the form (e-file: BinaryAttachment references on lines 12/14/23/25).", "notes": "W4."},
    {"diagnostic_id": "D_8915F_DEATH", "title": "Taxpayer died — spread collapses", "severity": "warning",
     "condition": "taxpayer died before the last spread year with unspread QDD income",
     "message": "If a taxpayer who spread qualified disaster distribution income over 3 years dies before the last year of the period, the remaining income can no longer be spread — report the remainder on the deceased taxpayer's final return (include it in the line 13 and/or line 24 totals).", "notes": "W2."},
]

F8915F_SCENARIOS: list[dict] = [
    {"scenario_name": "8915F-A — 2025 disaster, $18,000 401(k) QDD, default spread", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"item_a_tax_year": "2025", "item_b_disaster_year": "2025", "new_disaster_count": 1, "repeat_disaster_count": 0,
                "prior_year_qdds": 0, "dist_other_than_ira": 18000, "dist_traditional_ira": 0, "dist_roth_ira": 0,
                "nonqualified_portion": 0, "opt_out_spread_p2": False},
     "expected_outputs": {"line1e": 22000, "line5b_b": 18000, "line6": 18000, "line7": 0, "line11": 6000, "line15": 6000},
     "notes": "Single NEW disaster -> the 1e = $22,000 shortcut; 5b(b) = min(18,000, 22,000); line 11 = 18,000 / 3.0 = 6,000/yr -> 1040 line 5b. Early-withdrawal tax waived on the full 18,000; no 5329."},
    {"scenario_name": "8915F-B — opt-out: the full $18,000 taxed this year", "scenario_type": "edge", "sort_order": 2,
     "inputs": {"item_a_tax_year": "2025", "item_b_disaster_year": "2025", "dist_other_than_ira": 18000, "opt_out_spread_p2": True, "opt_out_spread_p3": False},
     "expected_outputs": {"line11": 18000, "optout_consistent": True},
     "notes": "Opt-out box on line 11 -> the whole line 10. Part III not engaged, so the unmatched line-22 box is moot (the consistency rule binds only when BOTH parts run)."},
    {"scenario_name": "8915F-C — the 5b cap: $30,000 distributed, one disaster", "scenario_type": "edge", "sort_order": 3,
     "inputs": {"item_a_tax_year": "2025", "item_b_disaster_year": "2025", "new_disaster_count": 1, "repeat_disaster_count": 0,
                "prior_year_qdds": 0, "dist_other_than_ira": 30000, "nonqualified_portion": 0},
     "expected_outputs": {"line1e": 22000, "line5b_b": 22000, "line6": 22000, "line7": 8000},
     "notes": "5b(b) = min(30,000, 22,000) = 22,000 -> line 6; the $8,000 excess rides line 7 as ordinary pension income and MAY owe the 10% additional tax (normal 5329 routing)."},
    {"scenario_name": "8915F-D — two new disasters: line 1d at the F8915F-003 boundary", "scenario_type": "edge", "sort_order": 4,
     "inputs": {"item_a_tax_year": "2025", "item_b_disaster_year": "2025", "new_disaster_count": 2, "repeat_disaster_count": 0, "prior_year_qdds": 0},
     "expected_outputs": {"line1d": 44000, "line1e": 44000, "cap_ok": True},
     "notes": "1d = 22,000 x 2 = 44,000 — exactly at the F8915F-003 cap (compliant); 44,001 would reject. The limit is per disaster, ALL plans, across years."},
    {"scenario_name": "8915F-E — year 2 of the spread: item A 2025, item B 2024, income only", "scenario_type": "normal", "sort_order": 5,
     "inputs": {"item_a_tax_year": "2025", "item_b_disaster_year": "2024", "dist_other_than_ira": 0,
                "prior_year_income_p2": 5000, "repayments_p2": 0},
     "expected_outputs": {"line11": 0, "line13": 5000, "line15": 5000},
     "notes": "No new distributions; line 12 (Worksheet 2) carries the prior-year spread income; 15 = 13 - 14 -> 1040 5b. This is the continuation-year shape most files will take."},
    {"scenario_name": "8915F-F — repayment before filing reduces the spread income", "scenario_type": "normal", "sort_order": 6,
     "inputs": {"item_a_tax_year": "2025", "item_b_disaster_year": "2024", "prior_year_income_p2": 5000, "repayments_p2": 3000},
     "expected_outputs": {"line15": 2000},
     "notes": "15 = 5,000 - 3,000. Repayments made before filing and by the due date (incl. extensions) belong on THIS form; later ones ride next year or carry back (the Rudy Examples 1/2). Floor at -0- if repayments exceed income (excess carries)."},
    {"scenario_name": "8915F-G — IRA QDD with 8606 basis: the 18/19/20 ties", "scenario_type": "edge", "sort_order": 7,
     "inputs": {"item_a_tax_year": "2025", "item_b_disaster_year": "2025", "dist_traditional_ira": 12000,
                "f8606_line15b": 9000, "f8606_line25b": 0, "line20_not_on_8606": 0, "opt_out_spread_p3": False, "opt_out_spread_p2": False},
     "expected_outputs": {"line21": 9000, "line22": 3000},
     "notes": "Basis-bearing IRA QDDs route through the 8606: line 18 = 8606 15b (taxable part only — basis comes out tax-free), line 20 takes only non-8606 amounts. 22 = 9,000 / 3.0 = 3,000 -> line 26 -> 1040 4b."},
    {"scenario_name": "8915F-H — the period math: DR-4682-WA pins both windows", "scenario_type": "edge", "sort_order": 8,
     "inputs": {"disaster_begin_date": "2022-11-03", "disaster_declaration_date": "2023-01-12"},
     "expected_outputs": {"qdd_period_end": "2023-07-10", "qd_repay_period_end": "2023-07-11"},
     "notes": "The published example: 179 days after 1/12/2023 = 7/10/2023 (Part I distributions); 180 days = 7/11/2023 (Part IV repayments). The one-day asymmetry is the Appendix-D off-by-one class — pinned in both directions."},
    {"scenario_name": "8915F-I — Part IV main home: window + repayment", "scenario_type": "edge", "sort_order": 9,
     "inputs": {"item_a_tax_year": "2025", "item_b_disaster_year": "2025", "mainhome_distributions": 15000,
                "mainhome_cost": 0, "mainhome_repayments": 15000},
     "expected_outputs": {"line30": 15000, "line32": 0},
     "notes": "A hardship-401(k)/TSA/FTHB-IRA distribution received within [-180d, +30d] of the disaster, fully repaid within the 180-day period -> line 32 = 0 (no income, no additional tax). Unrepaid -> taxable + 10%/25% exposure, or re-designate as a QDD if the three tests hold."},
    {"scenario_name": "8915F-J — e-file year-enum rejects", "scenario_type": "failure", "sort_order": 10,
     "inputs": {"item_a_tax_year": "2026", "item_b_disaster_year": "2026"},
     "expected_outputs": {"efile_blockers": ["F8915F-002-01", "F8915F-001-01"], "diagnostic": "D_8915F_YRENUM"},
     "notes": "A TY2025 return may not carry item A 2026-2028 or item B 2026-2027 — both published Active rejects."},
]

FORMS: list[dict] = [
    {
        "identity": {"form_number": "8915F", "form_title": "Form 8915-F — Qualified Disaster Retirement Plan Distributions and Repayments (Rev. 12-2025)",
                     "notes": "Draft-to-gate order (tts s79). The SECURE 2.0 §331 'forever form': items A/B name the instance (one form per item-B year; married = separate form per spouse); item C = FEMA DR majors only (max 20); item D = coronavirus. QDD = 3-part test (179-day period from disaster begin through 179d after the latest of begin/declaration/12-29-2022; main home in the disaster area; economic loss) -> ANY eligible-plan distribution designatable (incl. RMDs, periodic payments, loan offsets). $22,000/disaster ALL-plans across-years cap ($100,000 for item-B-2020; F8915F-003). Part I: the 1a-1e ladder (single-new-disaster shortcut) + the Rev-12-2025 NEW 5a/5b redesign (5b(b) = min(5b(a), 1e); reasonable-method allocation); L6 = waived amount (never on 5329); L7 = normally-taxed excess. Parts II/III: spread over 3 years (÷3.0 — rounding convention flagged) or matched opt-out boxes 11<->22; worksheets 2-5 attach (BinaryAttachment refs in e-file); the 8606 15b/25b ties; landings 15 -> 1040 5b, 26 -> 4b. Repayments: day-after through 3 years + 1 day; before-filing + by-due-date on THIS form, else forward/carryback (Rudy examples); can't repay non-spouse-beneficiary/RMD/SEPP. Part IV main home: hardship-401k/TSA/FTHB-IRA in [-180d, +30d]; NO spread; 180-day repayment period (NOT 179 — the Appendix-D off-by-one class); 32 -> 4b/5b + additional-tax exposure; re-designation fallback. MeF: IRS8915F rides ReturnData1040 2025v5.3 maxOccurs=6 (per-document name/SSN); rejects F8915F-001/-002 (year enums) + -003 (the 1d cap). Death collapses the spread. entity_types ['1040']; print + MeF document; worksheet internals + Appendix A/C/D tables = engine-derived, never re-encoded."},
        "facts": F8915F_FACTS, "rules": F8915F_RULES, "rule_links": F8915F_RULE_LINKS,
        "lines": F8915F_LINES, "diagnostics": F8915F_DIAGNOSTICS, "scenarios": F8915F_SCENARIOS,
    },
]

# ACTIVATED 2026-07-15 (tts s89 build leg): the three FAs flipped draft -> active with the
# runners + export-verbatim mirror refresh in ONE motion (the new-FAs-default-ACTIVE trap held
# until the build leg landed).
FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-8915F-CAP", "title": "Line 5b(b) = min(available, 1e); 1d within the F8915F-003 cap", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "active", "sort_order": 1,
     "description": "5b(b) = min(sum(2-4(a)) - 5a, line 1e); line 6 == 5b(b); line 7 == sum(2-4(a)) - 6. Pins: (18000, 0, 22000) -> 18000/0; (30000, 0, 22000) -> 22000/8000. 1d <= limit x new disasters (44,000 boundary pin).",
     "definition": {"rule": "R-8915F-PART1", "check": "5b(b) caps at 1e; 6 = 5b(b); 7 = excess; 1d <= 22000 x disasters"}},
    {"assertion_id": "FA-8915F-SPRD", "title": "Spread thirds + the 11<->22 box consistency", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "active", "sort_order": 2,
     "description": "line 11 = line 10 / 3.0 (or the full amount on opt-out); line 22 = line 21 / 3.0 likewise; when both parts engage, the two opt-out boxes MUST match. Pins: 18000 -> 6000; 9000 -> 3000; opt-out -> full.",
     "definition": {"rule": "R-8915F-SPREAD", "check": "spread = taxable/3 unless opted out; box11 == box22 when both parts run"}},
    {"assertion_id": "FA-8915F-LAND", "title": "Landings: 15 -> 1040 5b; 26 -> 4b; line 6 never on 5329", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "active", "sort_order": 3,
     "description": "Part II line 15 (13 - 14, floored) joins the 1040 line 5b total; Part III line 26 joins 4b; the line 6 amount is exempt from the early-distribution additional tax and generates NO Form 5329 row (line 7 and Part IV line 32 route through normal 5329 logic).",
     "definition": {"rule": "R-8915F-EFILE", "check": "15 -> 5b; 26 -> 4b; 6 suppresses the 5329 early-tax row; 7/32 don't"}},
]


class Command(BaseCommand):
    help = "Load the Form 8915-F spec (Qualified Disaster Distributions). Refuses to seed until READY_TO_SEED=True (Gate-1 W1-W4)."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad Form 8915-F spec (Qualified Disaster Retirement Plan Distributions and Repayments)\n"))
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
                "\nREFUSING TO SEED FORM 8915-F: not cleared.\n\n"
                "Gated until Ken approves the Gate-1 walk (W1 the QDD framework + the 179-day period +\n"
                "the $22,000 cap; W2 the Part I ladder + the 5a/5b redesign + the spread conventions;\n"
                "W3 repayments + the 8606 ties + Part IV incl. the 180-day period; W4 the MeF document\n"
                "max-6 + year-enum rejects + the 4b/5b landings + the 5329-waiver seam) and flips the sentinel.\n\n"
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
        self.stdout.write("Form 8915-F loaded.")
        self.stdout.write(f"  8915F: facts {len(F8915F_FACTS)} / rules {len(F8915F_RULES)} / lines {len(F8915F_LINES)} / diag {len(F8915F_DIAGNOSTICS)} / tests {len(F8915F_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}")
        self.stdout.write("=" * 60)
