"""Load the Form 3115 spec — Application for Change in Accounting Method (Rev. December 2022).
WO-23, 10th and LAST item in the SPINE S-16 federal-forms queue. Greenfield. Ken's specialty (§481(a)).

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
Form 3115 is the §446(e) APPLICATION to change a method of accounting — the consent mechanism — carrying the
§481(a) adjustment that prevents income/deductions from being duplicated or omitted on the change. It is NOT a
return computation. Two tracks: AUTOMATIC (Part I, a designated change number "DCN", no user fee, Rev. Proc.
2025-23 List of Automatic Changes) and NON-AUTOMATIC / advance consent (Part III, user fee). The §481(a)
adjustment (Part IV Line 26, signed) is spread by Rev. Proc. 2015-13 §7.03: NEGATIVE = 1 year, POSITIVE = 4
years ratable (de minimis 1 year if < $50,000; 2 years if under exam). Schedule E is the depreciation/
amortization path (impermissible -> permissible method = DCN 7); Schedule A is cash <-> accrual.

Greenfield: 3115 not in the 119-form prod set at the 2026-07-06 gap-check (only on-disk ref = diagnostic text
in load_1120s_complete.py, not an authoring surface).

═══════════════════════════════════════════════════════════════════════════
v1 SCOPE — LOCKED (Ken's Gate-1 walk 2026-07-06; DECISIONS D-25). See f3115_source_brief.md.
═══════════════════════════════════════════════════════════════════════════
COMPUTES: (Q1) the full §481(a) spread engine — signed Line-26 amount -> adjustment period (neg 1 / pos 4 /
de minimis 1 / under-exam 2) + ratable installments. (Q2) the Schedule E depreciation §481(a) catch-up =
(depreciation TAKEN under present method) - (depreciation ALLOWABLE under proposed method) as of BOY of change,
+ DCN 7 routing; the 7a-7h method descriptors = structured direct-entry. (Q3) the Schedule A cash<->accrual
2a-2g netting -> 2h -> Line 26. (Q4) scope-limit DIAGNOSTICS (under-exam L6a / 5-year rule L11a / cut-off vs
§481(a) L25 / DCN-7 >=2-impermissible-years). entity_types ['1040','1065','1120','1120S'].

requires_human_review WALK ITEMS (W1-W4):
W1. Spread engine: negative (or zero) -> 1 year; positive -> 4 years ratable; positive < $50,000 with the de
    minimis election -> 1 year; positive under examination -> 2 years (Rev. Proc. 2015-13 §7.03(1)/(2)/(3)(c)).
W2. Schedule E catch-up + DCN 7: §481(a) = depr_taken_present - depr_allowable_proposed (sign flows into the
    spread engine); automatic depreciation impermissible->permissible routes to DCN 7 (Rev. Proc. 2025-23 §6.01).
W3. Schedule A cash->accrual: net §481(a) = AR - advance payments - AP + prepaids + supplies + inventory + other
    (standard cash->accrual signs; combine 2a-2g -> 2h -> Part IV Line 26).
W4. Scope diagnostics: under-exam changes a positive period to 2 years; the 5-year rule can bar automatic
    eligibility; a cut-off change has NO §481(a) adjustment (L25 suppresses 26-29); DCN 7 needs the impermissible
    method used in >= 2 preceding years.

CARRIED [UNVERIFIED]: none material — verbatim vs FINAL Form 3115 Rev. 12-2022 + i3115 12-2022 + Rev. Proc.
2015-13 §7.03 + Rev. Proc. 2025-23 §6.01 + IRC §446(e)/§481(a). Re-verify EACH SEASON: the FORM REVISION
(reissues irregularly, not annually) + the CURRENT automatic-change Rev. Proc. (DCN list updates ~annually;
2024-23 -> 2025-23 chain). No OBBBA impact on the procedural machinery/§481(a) (OBBBA changed depreciation
AMOUNTS, not §446/§481 or the form).

SAFETY GUARD — READY_TO_SEED stays False until Ken approves the review walk (W1-W4).
FLIPPED 2026-07-06 — Ken APPROVED ("approved"): W1 the §481(a) spread engine (neg 1 / pos 4 / de minimis 1 /
under-exam 2), W2 the Schedule E depreciation catch-up (taken - allowable) + DCN 7 routing, W3 the Schedule A
cash<->accrual 2a-2h netting, W4 the scope diagnostics (under-exam / 5-year / cut-off / DCN-7 >=2-yr / user fee).
Validated (scratchpad/validate_3115.py, 36/0).
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

READY_TO_SEED = True

FORM_JURISDICTION = "federal"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1040", "1065", "1120", "1120S"]  # any taxpayer can file Form 3115

# ── Verified constants (f3115_source_brief.md; Rev. Proc. 2015-13 §7.03 + Rev. Proc. 2025-23 §6.01) ──
DE_MINIMIS_THRESHOLD = 50000          # §7.03(3)(c) — a positive §481(a) adjustment < $50,000 may elect a 1-yr period
POSITIVE_SPREAD_YEARS = 4             # §7.03(1) — positive §481(a) adjustment spread ratably over 4 years
NEGATIVE_SPREAD_YEARS = 1             # §7.03(1) — negative §481(a) adjustment taken entirely in the year of change
UNDER_EXAM_SPREAD_YEARS = 2           # §7.03(2) — positive adjustment period when under examination (default)
DCN_DEPRECIATION_IMPERMISSIBLE = "7"  # Rev. Proc. 2025-23 §6.01(9) — impermissible->permissible depreciation/amortization
DCN7_MIN_IMPERMISSIBLE_YEARS = 2      # §6.01(1) — the impermissible method must have been used in >= 2 preceding years


def _adjustment_period(net_481a, elect_de_minimis=False, is_under_examination=False) -> int:
    """Rev. Proc. 2015-13 §7.03. Negative (or zero) -> 1 year (year of change). Positive -> 4 years ratable,
    unless: the de minimis election applies to a positive adjustment < $50,000 (-> 1 year), or the applicant is
    under examination (-> 2 years). The de minimis election (an affirmative taxpayer election) takes precedence."""
    net = float(net_481a)
    if net <= 0:
        return NEGATIVE_SPREAD_YEARS
    if elect_de_minimis and net < DE_MINIMIS_THRESHOLD:
        return NEGATIVE_SPREAD_YEARS
    if is_under_examination:
        return UNDER_EXAM_SPREAD_YEARS
    return POSITIVE_SPREAD_YEARS


def _spread_installments(net_481a, period) -> list:
    """The §481(a) amount taken into account each year: ratably = net / period (equal installments)."""
    per = round(float(net_481a) / int(period), 2)
    return [per] * int(period)


def _depr_catch_up(depr_taken_present, depr_allowable_proposed) -> float:
    """Schedule E / DCN 7 (Rev. Proc. 2025-23 §6.01(5)). §481(a) = (depreciation TAKEN under the present method)
    - (depreciation ALLOWABLE under the proposed method), measured as of the beginning of the year of change.
    NEGATIVE (under-depreciated -> catch-up deduction, decreases income); POSITIVE (over-depreciated, increases
    income). The sign flows straight into _adjustment_period."""
    return round(float(depr_taken_present) - float(depr_allowable_proposed), 2)


def _schedule_a_net(ar=0, advance_payments=0, ap=0, prepaid_deducted=0, supplies_deducted=0,
                    inventory_deducted=0, other=0) -> float:
    """Schedule A Part I line 2h = combine lines 2a-2g. Standard cash->accrual signs: income not yet recognized
    under cash ADDS (2a AR, 2d prepaids / 2e supplies / 2f inventory previously deducted); deferral/expense items
    SUBTRACT (2b advance payments deferred, 2c AP). 'other' (2g) is entered signed. -> Part IV Line 26."""
    return round(
        float(ar) - float(advance_payments) - float(ap)
        + float(prepaid_deducted) + float(supplies_deducted) + float(inventory_deducted)
        + float(other), 2)


def _dcn_for_change(change_type, change_category):
    """v1 routes ONLY the depreciation impermissible->permissible automatic change to its DCN (7, Rev. Proc.
    2025-23 §6.01). Other automatic changes carry their own DCN (direct-entry); non-automatic changes have no DCN."""
    if change_type == "automatic" and change_category == "depreciation_amortization":
        return DCN_DEPRECIATION_IMPERMISSIBLE
    return None


AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("accounting_method_change_3115", "Form 3115 change in accounting method (§446(e)/§481(a)): automatic (DCN) vs "
     "non-automatic; §481(a) adjustment (neg 1-yr / pos 4-yr / de minimis $50k / under-exam 2-yr); Sch E depreciation "
     "catch-up (DCN 7); Sch A cash<->accrual netting."),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_F3115", "source_type": "federal_form", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Form 3115 (Rev. 12-2022) — Application for Change in Accounting Method",
        "citation": "Form 3115 (Rev. December 2022), Cat. No. 19280E, OMB 1545-0152",
        "issuer": "Internal Revenue Service", "official_url": "https://www.irs.gov/pub/irs-pdf/f3115.pdf",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.5, "topics": ["accounting_method_change_3115"],
        "excerpts": [{
            "excerpt_label": "Part I L1 (DCN) + Part IV L25/26/28 (§481(a) adjustment + elections) — verbatim",
            "excerpt_text": (
                "Part I Information for Automatic Change Request. Line 1: Enter the applicable designated automatic "
                "accounting method change number ('DCN') for the requested automatic change. Enter only one DCN, "
                "except as provided for in guidance published by the IRS. If the requested change has no DCN, check "
                "'Other,' and provide both a description of the change and citation of the IRS guidance providing the "
                "automatic change. Part IV Section 481(a) Adjustment. Line 25: Does published guidance require the "
                "applicant (or permit the applicant and the applicant is electing) to implement the requested change "
                "in method of accounting on a cut-off basis? If 'Yes,' attach an explanation and do not complete "
                "lines 26, 27, 28, and 29 below. Line 26: Enter the section 481(a) adjustment. Indicate whether the "
                "adjustment is an increase (+) or a decrease (-) in income. Line 28: Is the applicant making an "
                "election to take the entire amount of the adjustment into account in the tax year of change? "
                "[boxes] $50,000 de minimis election / Eligible acquisition transaction election."
            ),
            "summary_text": "L1 single-DCN rule; L25 cut-off toggle suppresses L26-29; L26 signed §481(a) (+ increase / - decrease); L28 $50k de minimis + eligible-acquisition elections.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "Schedule E depreciation questions L4a & L7 (present vs proposed) — verbatim",
            "excerpt_text": (
                "Schedule E - Change in Depreciation or Amortization. Line 4a: Attach a statement describing the "
                "property subject to the change. Include the property's description, type, placed-in-service year, "
                "and use in the applicant's trade or business or income-producing activity. Line 7: If the property "
                "is currently treated and/or will be treated as depreciable or amortizable property, provide the "
                "following information for both the present (if applicable) and proposed methods: (a) The Code "
                "section under which the property is or will be depreciated or amortized (for example, section "
                "168(g)); (b) The applicable asset class from Rev. Proc. 87-56 for each asset depreciated under "
                "section 168 (MACRS); (d) The depreciation or amortization method, including the Code section (for "
                "example, 200% declining balance method under section 168(b)(1)); (e) The useful life, recovery "
                "period, or amortization period; (f) The applicable convention; (g) Whether the additional "
                "first-year special depreciation allowance (for example, section 168(k)) was or will be claimed."
            ),
            "summary_text": "Sch E present-vs-proposed grid: Code section, Rev. Proc. 87-56 asset class, method, recovery period, convention, bonus flag — the descriptors behind the depreciation §481(a) catch-up.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "I3115", "source_type": "official_instructions", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Instructions for Form 3115 (Rev. 12-2022)",
        "citation": "Instructions for Form 3115 (Rev. December 2022), Cat. No. 63215H",
        "issuer": "Internal Revenue Service", "official_url": "https://www.irs.gov/pub/irs-pdf/i3115.pdf",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.2, "topics": ["accounting_method_change_3115"],
        "excerpts": [{
            "excerpt_label": "Scope limits: under-exam (L6a), 5-year rule (L11a), user fee (L24a) — substance",
            "excerpt_text": (
                "Line 6a asks whether any of the applicant's federal income tax return(s) are under examination. "
                "Line 11a implements the eligibility rule barring the automatic procedures if the applicant, its "
                "predecessor, or a related party has requested or made a change in the same method within any of the "
                "5 tax years ending with the requested year of change. There is no user fee for an automatic change; "
                "a non-automatic (advance consent) change under Part III requires the user fee (Line 24a) determined "
                "under Rev. Proc. 2023-1 Appendix A, paid through Pay.gov. For a positive §481(a) adjustment of a "
                "taxpayer under examination, the §481(a) adjustment period is generally 2 taxable years unless a "
                "Line 7b audit-protection category (e.g., the 3-month window, 120-day window, method not before the "
                "director, or CAP) applies."
            ),
            "summary_text": "L6a under-exam; L11a 5-year rule bars automatic eligibility; automatic = no user fee, non-automatic = Line 24a user fee; under-exam positive §481(a) period = 2 years.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "REVPROC_2015_13", "source_type": "official_guidance", "source_rank": "controlling",
        "jurisdiction_code": "US", "title": "Rev. Proc. 2015-13 — procedures for changes in accounting method (§481(a) adjustment period)",
        "citation": "Rev. Proc. 2015-13, 2015-5 I.R.B. 419, §7.03 (adjustment period; de minimis)",
        "issuer": "Internal Revenue Service", "official_url": "https://www.irs.gov/pub/irs-drop/rp-15-13.pdf",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.4, "topics": ["accounting_method_change_3115"],
        "excerpts": [{
            "excerpt_label": "§7.03(1) spread + §7.03(3)(c) $50k de minimis — verbatim",
            "excerpt_text": (
                "§7.03(1): Except as otherwise provided ... the section 481(a) adjustment period is one taxable year "
                "(year of change) for a negative section 481(a) adjustment and four taxable years (year of change "
                "and next three taxable years) for a positive section 481(a) adjustment. ... a taxpayer must take a "
                "positive section 481(a) adjustment into account ratably over the section 481(a) adjustment period. "
                "§7.03(3)(c) De minimis election: A taxpayer may elect a one-year section 481(a) adjustment period "
                "(year of change) for a positive section 481(a) adjustment that is less than $50,000. To make this "
                "election, the taxpayer must complete the appropriate line on the Form 3115 and take the entire "
                "section 481(a) adjustment into account in the year of change when it implements the change."
            ),
            "summary_text": "§7.03(1): negative §481(a) = 1 year, positive = 4 years ratable. §7.03(3)(c): positive < $50,000 may elect a 1-year period.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "REVPROC_2025_23", "source_type": "official_guidance", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Rev. Proc. 2025-23 — List of Automatic Changes (DCN 7 depreciation)",
        "citation": "Rev. Proc. 2025-23, 2025-24 I.R.B., §6.01 (impermissible->permissible depreciation, DCN 7)",
        "issuer": "Internal Revenue Service", "official_url": "https://www.irs.gov/pub/irs-drop/rp-25-23.pdf",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.2, "topics": ["accounting_method_change_3115"],
        "excerpts": [{
            "excerpt_label": "§6.01(5) depreciation §481(a) catch-up + §6.01(9) DCN 7 — verbatim substance",
            "excerpt_text": (
                "Section 6.01 applies to a taxpayer that wants to change from an impermissible to a permissible "
                "method of accounting for depreciation or amortization for property owned at the beginning of the "
                "year of change, for which the taxpayer used the impermissible method in at least the two taxable "
                "years immediately preceding the year of change. §6.01(5) Section 481(a) adjustment: Because the "
                "adjusted basis of the property is changed as a result of a method change made under this section "
                "6.01, items are duplicated or omitted; accordingly, this change is made with a section 481(a) "
                "adjustment. This adjustment may result in either a negative section 481(a) adjustment (a decrease in "
                "taxable income) or a positive section 481(a) adjustment (an increase in taxable income), and equals "
                "the difference between the total amount of depreciation taken into account under the taxpayer's "
                "present method and the amount allowable under the proposed method as of the beginning of the year of "
                "change. §6.01(9): The designated automatic accounting method change number for a change under this "
                "section 6.01 is '7.'"
            ),
            "summary_text": "DCN 7 = impermissible->permissible depreciation (used >= 2 preceding years, property owned at BOY); §481(a) = (depreciation taken) - (depreciation allowable) at BOY, may be negative or positive.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "IRC_481", "source_type": "statute", "source_rank": "controlling",
        "jurisdiction_code": "US", "title": "IRC §481(a) adjustments + §446(e) consent",
        "citation": "26 U.S.C. §481(a) (duplication/omission) / §446(e) (Secretary's consent to change)",
        "issuer": "U.S. Congress", "official_url": "https://www.law.cornell.edu/uscode/text/26/481",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.5, "topics": ["accounting_method_change_3115"],
        "excerpts": [{
            "excerpt_label": "§481(a) + §446(e) — verbatim",
            "excerpt_text": (
                "§481(a): In computing the taxpayer's taxable income for any taxable year ... if such computation is "
                "under a method of accounting different from the method under which the taxpayer's taxable income for "
                "the preceding taxable year was computed, then there shall be taken into account those adjustments "
                "which are determined to be necessary solely by reason of the change in order to prevent amounts "
                "from being duplicated or omitted, except there shall not be taken into account any adjustment in "
                "respect of any taxable year to which this section does not apply unless the adjustment is "
                "attributable to a change in the method of accounting initiated by the taxpayer. §446(e): Except as "
                "otherwise expressly provided ... a taxpayer who changes the method of accounting on the basis of "
                "which he regularly computes his income in keeping his books shall, before computing his taxable "
                "income under the new method, secure the consent of the Secretary."
            ),
            "summary_text": "§481(a): a method change takes into account adjustments to prevent duplication/omission. §446(e): must secure the Secretary's consent before computing under the new method (= Form 3115).",
            "is_key_excerpt": True,
        }],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_F3115", "3115", "governs"), ("I3115", "3115", "governs"), ("REVPROC_2015_13", "3115", "governs"),
    ("REVPROC_2025_23", "3115", "governs"), ("IRC_481", "3115", "governs"),
]


F3115_FACTS: list[dict] = [
    {"fact_key": "change_type", "label": "Change type: automatic (Part I, DCN, no user fee) or non-automatic (Part III, user fee)", "data_type": "choice", "required": False, "sort_order": 1,
     "choices": ["automatic", "non_automatic"]},
    {"fact_key": "change_category", "label": "Type of change (page-1 box): depreciation/amortization, overall method, financial products, other", "data_type": "choice", "required": False, "sort_order": 2,
     "choices": ["depreciation_amortization", "overall_method", "financial_products", "other"]},
    {"fact_key": "dcn", "label": "Designated change number (Part I L1) — for an automatic change (enter only one)", "data_type": "text", "required": False, "sort_order": 3},
    {"fact_key": "is_cut_off", "label": "Cut-off basis (L25)? -> NO §481(a) adjustment; do not complete lines 26-29", "data_type": "boolean", "required": False, "sort_order": 4},
    {"fact_key": "net_481a_adjustment", "label": "Net §481(a) adjustment (L26, signed: + increase / - decrease in income)", "data_type": "decimal", "required": False, "sort_order": 5},
    {"fact_key": "elect_de_minimis", "label": "Electing the $50,000 de minimis 1-year period (L28)?", "data_type": "boolean", "required": False, "sort_order": 6},
    {"fact_key": "elect_eligible_acquisition", "label": "Electing the eligible-acquisition-transaction 1-year period (L28)?", "data_type": "boolean", "required": False, "sort_order": 7},
    {"fact_key": "is_under_examination", "label": "Any federal return under examination (L6a)? -> positive §481(a) period becomes 2 years", "data_type": "boolean", "required": False, "sort_order": 8},
    {"fact_key": "prior_change_same_item_5yr", "label": "Requested/made this same change within the 5 tax years ending with the year of change (L11a 5-year rule)?", "data_type": "boolean", "required": False, "sort_order": 9},
    {"fact_key": "depr_taken_present", "label": "Schedule E: depreciation TAKEN under the present (impermissible) method as of BOY of change", "data_type": "decimal", "required": False, "sort_order": 10},
    {"fact_key": "depr_allowable_proposed", "label": "Schedule E: depreciation ALLOWABLE under the proposed (permissible) method as of BOY of change", "data_type": "decimal", "required": False, "sort_order": 11},
    {"fact_key": "impermissible_years_used", "label": "Schedule E: number of preceding years the impermissible method was used (DCN 7 needs >= 2)", "data_type": "integer", "required": False, "sort_order": 12},
    {"fact_key": "sch_a_ar", "label": "Schedule A 2a: accounts receivable (income accrued but not received)", "data_type": "decimal", "required": False, "sort_order": 13},
    {"fact_key": "sch_a_advance_payments", "label": "Schedule A 2b: advance payments (income received/reported before earned) being deferred", "data_type": "decimal", "required": False, "sort_order": 14},
    {"fact_key": "sch_a_ap", "label": "Schedule A 2c: accounts payable (expenses accrued but not paid)", "data_type": "decimal", "required": False, "sort_order": 15},
    {"fact_key": "sch_a_prepaid", "label": "Schedule A 2d: prepaid expenses previously deducted", "data_type": "decimal", "required": False, "sort_order": 16},
    {"fact_key": "sch_a_supplies", "label": "Schedule A 2e: supplies on hand previously deducted", "data_type": "decimal", "required": False, "sort_order": 17},
    {"fact_key": "sch_a_inventory", "label": "Schedule A 2f: inventory previously deducted / not previously reported", "data_type": "decimal", "required": False, "sort_order": 18},
    {"fact_key": "sch_a_other", "label": "Schedule A 2g: other §481(a) items (entered signed)", "data_type": "decimal", "required": False, "sort_order": 19},
]

F3115_RULES: list[dict] = [
    {"rule_id": "R-3115-CATCHUP", "title": "Schedule E depreciation §481(a) catch-up (DCN 7)", "rule_type": "calculation",
     "formula": "sch_e_481a = round(depr_taken_present - depr_allowable_proposed, 2)  # negative = under-depreciated (decrease income); positive = over-depreciated (increase income)",
     "inputs": ["depr_taken_present", "depr_allowable_proposed"], "outputs": ["sch_e_481a_adjustment"], "sort_order": 1,
     "description": "W2. The Schedule E depreciation §481(a) catch-up equals the depreciation TAKEN under the present (impermissible) method minus the depreciation ALLOWABLE under the proposed (permissible) method, measured as of the beginning of the year of change (Rev. Proc. 2025-23 §6.01(5)). A negative result (under-depreciated) decreases income; a positive result (over-depreciated) increases income. The sign flows into the spread engine (R-3115-PERIOD)."},
    {"rule_id": "R-3115-SCHA", "title": "Schedule A cash<->accrual net §481(a) (2a-2h)", "rule_type": "calculation",
     "formula": "net_481a = round(ar - advance_payments - ap + prepaid + supplies + inventory + other, 2)  # combine 2a-2g -> 2h -> Line 26",
     "inputs": ["sch_a_ar", "sch_a_advance_payments", "sch_a_ap", "sch_a_prepaid", "sch_a_supplies", "sch_a_inventory", "sch_a_other"], "outputs": ["sch_a_481a_adjustment"], "sort_order": 2,
     "description": "W3. Schedule A Part I line 2h = combine lines 2a-2g. Standard cash->accrual signs: income not yet recognized under cash ADDS (2a accounts receivable; 2d prepaids / 2e supplies / 2f inventory previously deducted); deferral/expense items SUBTRACT (2b advance payments deferred; 2c accounts payable); 2g other is entered signed. The result flows to Part IV Line 26."},
    {"rule_id": "R-3115-PERIOD", "title": "§481(a) adjustment period (1 neg / 4 pos / de minimis 1 / under-exam 2)", "rule_type": "calculation",
     "formula": "period = 1 if net_481a <= 0 else (1 if (elect_de_minimis and net_481a < 50000) else (2 if is_under_examination else 4))",
     "inputs": ["net_481a_adjustment", "elect_de_minimis", "is_under_examination"], "outputs": ["adjustment_period"], "sort_order": 3,
     "description": "W1. Rev. Proc. 2015-13 §7.03: a negative (or zero) §481(a) adjustment is taken entirely in the year of change (1 year); a positive adjustment is spread ratably over 4 years, EXCEPT a positive adjustment < $50,000 with the de minimis election (§7.03(3)(c)) collapses to 1 year, and a positive adjustment while under examination (§7.03(2)) uses a 2-year period. The de minimis election (an affirmative taxpayer election) takes precedence over the under-exam period."},
    {"rule_id": "R-3115-SPREAD", "title": "Ratable §481(a) installments", "rule_type": "calculation",
     "formula": "installments = [round(net_481a / period, 2)] * period",
     "inputs": ["net_481a_adjustment", "adjustment_period"], "outputs": ["annual_installments"], "sort_order": 4,
     "description": "W1. The §481(a) adjustment is taken into account ratably (equal installments) over the adjustment period: each year's amount = net §481(a) / period. E.g. a positive $100,000 over 4 years = $25,000/year; a negative -$63,508 over 1 year = -$63,508 in the year of change."},
    {"rule_id": "R-3115-DCN", "title": "Automatic depreciation impermissible->permissible routes to DCN 7", "rule_type": "routing",
     "formula": "dcn = '7' if (change_type == 'automatic' and change_category == 'depreciation_amortization') else <the change's own DCN / none for non-automatic>",
     "inputs": ["change_type", "change_category"], "outputs": ["dcn"], "sort_order": 5,
     "description": "W2. An automatic change from an impermissible to a permissible method of accounting for depreciation or amortization is designated change number (DCN) 7 (Rev. Proc. 2025-23 §6.01(9)), entered on Part I line 1. Other automatic changes carry their own DCN (direct-entry); a non-automatic change has no DCN. v1 routes only the DCN-7 depreciation path."},
]

F3115_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-3115-CATCHUP", "REVPROC_2025_23", "primary", "§6.01(5) depreciation §481(a)"),
    ("R-3115-CATCHUP", "IRS_F3115", "secondary", "Schedule E present/proposed"),
    ("R-3115-SCHA", "IRS_F3115", "primary", "Schedule A 2a-2h worksheet"),
    ("R-3115-SCHA", "IRC_481", "secondary", "§481(a) duplication/omission"),
    ("R-3115-PERIOD", "REVPROC_2015_13", "primary", "§7.03(1)/(2)/(3)(c) period"),
    ("R-3115-PERIOD", "IRS_F3115", "secondary", "Part IV L26/L28"),
    ("R-3115-SPREAD", "REVPROC_2015_13", "primary", "§7.03(1) ratable"),
    ("R-3115-DCN", "REVPROC_2025_23", "primary", "§6.01(9) DCN 7"),
    ("R-3115-DCN", "IRS_F3115", "secondary", "Part I line 1 DCN"),
]

F3115_LINES: list[dict] = [
    {"line_number": "P1_DCN", "description": "Part I L1 designated change number (DCN)", "line_type": "calculated", "source_rules": ["R-3115-DCN"], "sort_order": 1},
    {"line_number": "SCHE_CATCHUP", "description": "Schedule E depreciation §481(a) catch-up", "line_type": "calculated", "source_rules": ["R-3115-CATCHUP"], "sort_order": 2},
    {"line_number": "SCHA_2H", "description": "Schedule A 2h net §481(a) (cash<->accrual)", "line_type": "calculated", "source_rules": ["R-3115-SCHA"], "sort_order": 3},
    {"line_number": "L26_481A", "description": "Part IV L26 net §481(a) adjustment (signed)", "line_type": "input", "source_rules": ["R-3115-CATCHUP", "R-3115-SCHA"], "sort_order": 4},
    {"line_number": "PERIOD", "description": "§481(a) adjustment period (years)", "line_type": "calculated", "source_rules": ["R-3115-PERIOD"], "sort_order": 5},
    {"line_number": "SPREAD", "description": "Ratable annual §481(a) installments", "line_type": "calculated", "source_rules": ["R-3115-SPREAD"], "sort_order": 6},
]

F3115_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_3115_NEG_1YR", "title": "Negative §481(a): taken entirely in the year of change", "severity": "info",
     "condition": "net_481a_adjustment < 0",
     "message": "A NEGATIVE §481(a) adjustment (a decrease in taxable income) is taken into account entirely in the year of change - a 1-year period (Rev. Proc. 2015-13 §7.03(1)). No de minimis election is needed. For a depreciation change (Schedule E / DCN 7), a negative adjustment is the under-depreciated catch-up: more depreciation should have been taken, so income decreases.",
     "notes": "W1."},
    {"diagnostic_id": "D_3115_POS_SPREAD", "title": "Positive §481(a): 4-year ratable spread", "severity": "info",
     "condition": "net_481a_adjustment >= 50000 and not is_under_examination",
     "message": "A POSITIVE §481(a) adjustment (an increase in taxable income) of $50,000 or more is taken into account RATABLY over 4 tax years - the year of change plus the next 3 (Rev. Proc. 2015-13 §7.03(1)). Each year's installment = net §481(a) / 4.",
     "notes": "W1."},
    {"diagnostic_id": "D_3115_DEMINIMIS", "title": "Positive §481(a) < $50,000: de minimis 1-year election available", "severity": "info",
     "condition": "net_481a_adjustment > 0 and net_481a_adjustment < 50000",
     "message": "A POSITIVE §481(a) adjustment of less than $50,000 may elect a 1-year adjustment period (take the entire amount into account in the year of change) under the de minimis election, Rev. Proc. 2015-13 §7.03(3)(c) / Form 3115 Line 28. Otherwise the default is a 4-year ratable spread.",
     "notes": "W1."},
    {"diagnostic_id": "D_3115_UNDEREXAM", "title": "Under examination: positive §481(a) period becomes 2 years", "severity": "warning",
     "condition": "is_under_examination and net_481a_adjustment > 0",
     "message": "The applicant has a federal return under examination (Line 6a). For a POSITIVE §481(a) adjustment, the adjustment period is generally 2 tax years (not 4) unless a Line 7b audit-protection category applies (3-month window, 120-day window, method not before the director, or CAP). Being under examination may also restrict eligibility for the automatic change procedures - see Line 7.",
     "notes": "W4."},
    {"diagnostic_id": "D_3115_5YEAR", "title": "5-year rule: prior same-item change may bar automatic eligibility", "severity": "warning",
     "condition": "prior_change_same_item_5yr",
     "message": "The applicant, its predecessor, or a related party requested or made a change in this same method of accounting within one of the 5 tax years ending with the year of change (Line 11a). This eligibility rule generally BARS use of the automatic change procedures for this item - a non-automatic (advance consent) request may be required. Confirm the exception rules in the List of Automatic Changes.",
     "notes": "W4."},
    {"diagnostic_id": "D_3115_CUTOFF", "title": "Cut-off basis: no §481(a) adjustment", "severity": "info",
     "condition": "is_cut_off",
     "message": "This change is implemented on a CUT-OFF basis (Line 25) - only items arising on or after the beginning of the year of change use the new method, so there is NO §481(a) adjustment. Do NOT complete lines 26, 27, 28, and 29. (Cut-off treatment is required or permitted only where the applicable guidance says so.)",
     "notes": "W4. Mutually exclusive with the §481(a) lines."},
    {"diagnostic_id": "D_3115_DCN7_2YR", "title": "DCN 7 requires the impermissible method used >= 2 preceding years", "severity": "warning",
     "condition": "change_category == depreciation_amortization and impermissible_years_used < 2",
     "message": "The automatic depreciation change (DCN 7, Rev. Proc. 2025-23 §6.01) applies only where the impermissible method was used for the property in at least the TWO taxable years immediately preceding the year of change. A method used for only one year is not yet an 'accounting method' - correct it via an amended return (or the 1-year-property rule under §6.01(1)(b)) instead of Form 3115.",
     "notes": "W4."},
    {"diagnostic_id": "D_3115_USERFEE", "title": "User fee: automatic = none; non-automatic = Line 24a", "severity": "info",
     "condition": "change_type == non_automatic",
     "message": "A NON-AUTOMATIC (advance consent) change under Part III requires a user fee (Line 24a) determined under Rev. Proc. 2023-1, Appendix A, paid through Pay.gov, and the Form 3115 is filed with the IRS National Office by the last day of the year of change. An AUTOMATIC change (Part I, with a DCN) has NO user fee and is attached to a timely-filed return with a copy to Ogden.",
     "notes": "W4."},
]

F3115_SCENARIOS: list[dict] = [
    {"scenario_name": "3115-A — depreciation under-depreciated catch-up (negative, 1 year)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"change_type": "automatic", "change_category": "depreciation_amortization", "depr_taken_present": 8000, "depr_allowable_proposed": 72000, "impermissible_years_used": 3},
     "expected_outputs": {"sch_e_481a_adjustment": -64000.0, "dcn": "7", "adjustment_period": 1, "annual_installments": [-64000.0], "diagnostic": "D_3115_NEG_1YR"},
     "notes": "Asset depreciated too slowly (taken 8,000 vs allowable 72,000) -> §481(a) = 8,000 - 72,000 = -64,000 (negative, decreases income) -> DCN 7, taken entirely in the year of change."},
    {"scenario_name": "3115-B — depreciation over-depreciated (positive, 4-year spread)", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"change_type": "automatic", "change_category": "depreciation_amortization", "depr_taken_present": 120000, "depr_allowable_proposed": 20000, "impermissible_years_used": 2, "net_481a_adjustment": 100000},
     "expected_outputs": {"sch_e_481a_adjustment": 100000.0, "dcn": "7", "adjustment_period": 4, "annual_installments": [25000.0, 25000.0, 25000.0, 25000.0], "diagnostic": "D_3115_POS_SPREAD"},
     "notes": "Over-depreciated (taken 120,000 vs allowable 20,000) -> §481(a) = +100,000 (increases income) -> spread ratably over 4 years = 25,000/yr."},
    {"scenario_name": "3115-C — de minimis election (positive < $50,000 -> 1 year)", "scenario_type": "edge", "sort_order": 3,
     "inputs": {"change_type": "automatic", "change_category": "depreciation_amortization", "net_481a_adjustment": 40000, "elect_de_minimis": True},
     "expected_outputs": {"adjustment_period": 1, "annual_installments": [40000.0], "diagnostic": "D_3115_DEMINIMIS"},
     "notes": "A positive $40,000 adjustment (< $50,000) with the de minimis election collapses the 4-year spread to a single year."},
    {"scenario_name": "3115-D — under examination (positive -> 2 years)", "scenario_type": "edge", "sort_order": 4,
     "inputs": {"change_type": "automatic", "change_category": "overall_method", "net_481a_adjustment": 100000, "is_under_examination": True},
     "expected_outputs": {"adjustment_period": 2, "annual_installments": [50000.0, 50000.0], "diagnostic": "D_3115_UNDEREXAM"},
     "notes": "A positive $100,000 adjustment while under examination uses a 2-year period (not 4) = 50,000/yr."},
    {"scenario_name": "3115-E — Schedule A cash->accrual net §481(a) (+120,000)", "scenario_type": "normal", "sort_order": 5,
     "inputs": {"change_type": "automatic", "change_category": "overall_method", "sch_a_ar": 50000, "sch_a_inventory": 80000, "sch_a_prepaid": 10000, "sch_a_ap": 20000},
     "expected_outputs": {"sch_a_481a_adjustment": 120000.0, "adjustment_period": 4},
     "notes": "Cash->accrual: AR 50,000 + inventory 80,000 + prepaid 10,000 - AP 20,000 = net +120,000 -> Line 26; positive, 4-year spread."},
    {"scenario_name": "3115-F — cut-off basis: no §481(a) adjustment", "scenario_type": "edge", "sort_order": 6,
     "inputs": {"change_type": "automatic", "change_category": "other", "is_cut_off": True},
     "expected_outputs": {"diagnostic": "D_3115_CUTOFF"},
     "notes": "A cut-off change (Line 25) has no §481(a) adjustment; lines 26-29 are not completed - only post-change items use the new method."},
    {"scenario_name": "3115-G — DCN 7 needs >= 2 impermissible years", "scenario_type": "failure", "sort_order": 7,
     "inputs": {"change_type": "automatic", "change_category": "depreciation_amortization", "impermissible_years_used": 1},
     "expected_outputs": {"diagnostic": "D_3115_DCN7_2YR"},
     "notes": "The impermissible depreciation method was used only 1 year -> not yet an accounting method; DCN 7 does not apply (use an amended return / the 1-year-property rule)."},
]

FORMS: list[dict] = [
    {
        "identity": {"form_number": "3115", "form_title": "Form 3115 — Application for Change in Accounting Method (Rev. 12-2022)",
                     "notes": "WO-23 (SPINE S-16, 10th and LAST; DECISIONS D-25). The §446(e)/§481(a) method-change application - NOT a return computation. COMPUTES: the §481(a) spread engine (neg 1-yr / pos 4-yr ratable / de minimis $50k 1-yr / under-exam 2-yr, Rev. Proc. 2015-13 §7.03); the Schedule E depreciation catch-up = (depr taken present) - (depr allowable proposed) at BOY + DCN 7 routing (Rev. Proc. 2025-23 §6.01); the Schedule A cash<->accrual 2a-2h netting -> Line 26. Scope limits (under-exam L6a / 5-year rule L11a / cut-off L25 / DCN-7 >=2-yr) = diagnostics. Method descriptors (Sch E 7a-7h) = direct-entry. entity_types [1040,1065,1120,1120S]. Form 3115 Rev. 12-2022 (no annual reissue); no OBBBA impact on the procedural machinery/§481(a). Re-verify the FORM REVISION + the current automatic-change Rev. Proc. each season."},
        "facts": F3115_FACTS, "rules": F3115_RULES, "rule_links": F3115_RULE_LINKS,
        "lines": F3115_LINES, "diagnostics": F3115_DIAGNOSTICS, "scenarios": F3115_SCENARIOS,
    },
]

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-3115-CATCHUP", "title": "Schedule E depreciation §481(a) = taken - allowable", "assertion_type": "reconciliation",
     "entity_types": ["1040", "1065", "1120", "1120S"], "status": "active", "sort_order": 1,
     "description": "The Schedule E depreciation catch-up equals depreciation taken under the present method minus depreciation allowable under the proposed method, as of the beginning of the year of change (DCN 7).",
     "definition": {"rule": "R-3115-CATCHUP", "check": "sch_e_481a = depr_taken_present - depr_allowable_proposed"}},
    {"assertion_id": "FA-3115-SPREAD", "title": "§481(a) period follows sign + elections", "assertion_type": "reconciliation",
     "entity_types": ["1040", "1065", "1120", "1120S"], "status": "active", "sort_order": 2,
     "description": "Adjustment period = 1 for negative; 4 for positive; 1 for positive < $50k with the de minimis election; 2 for positive under examination. Installments are ratable (net / period).",
     "definition": {"rule": "R-3115-PERIOD", "check": "period = 1 if net<=0 else (1 if deminimis&net<50k else (2 if under_exam else 4))"}},
    {"assertion_id": "FA-3115-SCHA", "title": "Schedule A 2h = combine 2a-2g", "assertion_type": "reconciliation",
     "entity_types": ["1040", "1065", "1120", "1120S"], "status": "active", "sort_order": 3,
     "description": "The Schedule A net §481(a) = AR - advance payments - AP + prepaids + supplies + inventory + other (standard cash->accrual signs), flowing to Part IV Line 26.",
     "definition": {"rule": "R-3115-SCHA", "check": "2h = 2a - 2b - 2c + 2d + 2e + 2f + 2g"}},
]


class Command(BaseCommand):
    help = "Load the Form 3115 spec (Application for Change in Accounting Method, Rev. 12-2022). Refuses to seed until READY_TO_SEED=True (W1-W4)."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad Form 3115 spec (Change in Accounting Method)\n"))
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
                "\nREFUSING TO SEED FORM 3115: not cleared.\n\n"
                "Gated until Ken reviews (W1 spread engine; W2 Schedule E catch-up + DCN 7; W3 Schedule A\n"
                "cash<->accrual netting; W4 scope diagnostics) and flips the sentinel.\n\n"
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
        self.stdout.write(f"  {len(FLOW_ASSERTIONS)} flow assertions")

    def _report(self):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("Form 3115 loaded.")
        self.stdout.write(f"  3115: facts {len(F3115_FACTS)} / rules {len(F3115_RULES)} / lines {len(F3115_LINES)} / diag {len(F3115_DIAGNOSTICS)} / tests {len(F3115_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}")
        self.stdout.write("=" * 60)
