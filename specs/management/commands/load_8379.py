"""Load the Form 8379 spec — Injured Spouse Allocation (Rev. 11-2023).
WO-18, 5th item in the SPINE S-16 federal-forms queue (after 8990 + Schedule H + 4684 + 4952). Greenfield.

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
Form 8379 is an ALLOCATION form (not a tax-computation form). An "injured spouse" is a spouse on a
joint return whose share of the joint overpayment was/will be offset (§6402) against the OTHER spouse's
separate past-due debt (child/spousal support, federal or state tax, state unemployment, or federal
nontax debt like a student loan). Part I is an eligibility decision tree; Part III allocates each
joint-return item between spouses (col a = col b + col c); the IRS then computes the injured spouse's
refund share from the allocation. NOT Form 8857 (innocent spouse = relief from joint LIABILITY).

Confirmed the form is 8379 (Ken's BUILD_ORDER "8679" is a typo — no such IRS form). No annual reissue
(Rev. 11-2023 current; instructions Rev. 11-2024). No OBBBA/law impact — purely procedural.

Greenfield: 8379 not in the 114-form prod set at the 2026-07-06 gap-check.

═══════════════════════════════════════════════════════════════════════════
v1 SCOPE — LOCKED (Ken's Gate-1 walk 2026-07-06; DECISIONS D-20). See f8379_source_brief.md.
═══════════════════════════════════════════════════════════════════════════
COMPUTES: (Q1) Part I decision tree -> is_injured_spouse + stop-reason diagnostics. (Q2) Part III col(a)=(b)+(c)
validation + allocation-rule diagnostics; DO NOT estimate the refund share (IRS computes it). (Q3) 9 community-
property states + the L5-skip override gate. (Q4) 8379-vs-8857 boundary + 3yr/2yr time limit + Part IV + processing
diagnostics. entity_types [1040].

requires_human_review WALK ITEMS (W1-W4):
W1. Eligibility: injured spouse if joint return + debt owed only by spouse + NOT legally obligated + qualifies via
    community-property (L5) / made payments (L6) / EIC-ACTC (L8) / other refundable credit (L9). CONFIRM the tree.
W2. Part III: col (a) amount on joint return = col (b) injured + col (c) other, every line; W-2 income to earner,
    withholding follows income, std deduction 1/2 basic each, dependent credits to claiming spouse, EIC excluded.
    CONFIRM the constraint + allocation rules; the refund share is IRS-computed (NOT estimated here).
W3. Community property: 9 states (AZ/CA/ID/LA/NV/NM/TX/WA/WI); L5 resident skips L6-9; IRS divides per state law.
W4. 8379 (injured) vs 8857 (innocent); file within 3 yrs from filing / 2 yrs from payment (whichever later). CONFIRM.

CARRIED [UNVERIFIED]: none — verbatim vs FINAL Form 8379 Rev. 11-2023 + i8379 Rev. 11-2024 + §6402. Re-verify the
revision each season (the form reissues irregularly, not annually).

SAFETY GUARD — READY_TO_SEED stays False until Ken approves the review walk (W1-W4).
FLIPPED 2026-07-06 — Ken APPROVED ("Approve — flip, seed, export"): W1 the Part I eligibility decision
tree, W2 the Part III col(a)=(b)+(c) constraint + allocation rules (refund share NOT estimated), W3 the
community-property override (9 states), W4 the 8379-vs-8857 boundary + 3yr/2yr time limit. Validated
(scratchpad/validate_8379.py, 29/0).
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
FORM_ENTITY_TYPES = ["1040"]

# ── Verified constants (f8379_source_brief.md; Form 8379 Rev. 11-2023 / i8379 Rev. 11-2024 / §6402) ──
# The nine community-property states (statutory; re-verify if a state changes its regime)
COMMUNITY_PROPERTY_STATES = ["AZ", "CA", "ID", "LA", "NV", "NM", "TX", "WA", "WI"]
FILE_LIMIT_YEARS_FROM_FILING = 3       # 3 years from the return filing (incl. extensions)
FILE_LIMIT_YEARS_FROM_PAYMENT = 2      # or 2 years from the date the tax was paid, whichever is later
# The six offsettable past-due debts (Part I line 3)
OFFSET_DEBT_TYPES = ["federal_tax", "state_income_tax", "state_unemployment", "child_support", "spousal_support", "federal_nontax"]


def _is_injured_spouse(filed_joint, debt_spouse_only, legally_obligated,
                       community_property_resident, made_reported_payments,
                       claimed_eic_actc, claimed_refundable_credit) -> tuple:
    """Part I decision tree -> (is_injured: bool, reason: str). Qualifies by reaching Part II via L5
    (community property) / L6 (made payments) / L8 (EIC or ACTC) / L9 (other refundable credit)."""
    if not filed_joint:
        return (False, "not_joint")                    # L2 No -> STOP
    if not debt_spouse_only:
        return (False, "debt_not_spouse_only")         # L3 No -> STOP
    if legally_obligated:
        return (False, "legally_obligated")            # L4 Yes -> STOP (consider innocent spouse)
    if community_property_resident:
        return (True, "community_property")            # L5 Yes -> skip L6-9 -> Part II
    if made_reported_payments:
        return (True, "made_payments")                 # L6 Yes -> Part II
    if claimed_eic_actc:
        return (True, "eic_actc")                      # L8 Yes -> Part II
    if claimed_refundable_credit:
        return (True, "refundable_credit")             # L9 Yes -> Part II
    return (False, "no_qualifying_path")               # L9 No -> STOP


def _allocation_balances(col_a, col_b, col_c) -> bool:
    """Part III constraint: col (a) amount shown on the joint return = col (b) injured + col (c) other."""
    return round(float(col_a), 2) == round(float(col_b) + float(col_c), 2)


def _std_deduction_half(basic_std_deduction) -> float:
    """Part III line 15: one-half of the BASIC standard deduction to each spouse (50/50)."""
    return round(float(basic_std_deduction) / 2.0, 2)


AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("injured_spouse_allocation", "Form 8379 injured spouse allocation (§6402): Part I eligibility decision tree; "
     "Part III allocation of joint items (col a = b + c); community-property override (9 states); distinct from "
     "Form 8857 innocent spouse. IRS computes the refund share."),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_F8379", "source_type": "federal_form", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Form 8379 (Rev. 11-2023) — Injured Spouse Allocation",
        "citation": "Form 8379 (Rev. November 2023), Cat. No. 62474Q, Attach. Seq. No. 104",
        "issuer": "Internal Revenue Service", "official_url": "https://www.irs.gov/pub/irs-pdf/f8379.pdf",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.6, "topics": ["injured_spouse_allocation"],
        "excerpts": [{
            "excerpt_label": "Part I eligibility decision tree (Rev. 11-2023 verbatim)",
            "excerpt_text": (
                "Part I 'Should You File This Form?': L2 'Did you (or will you) file a joint return?' (No -> Stop, "
                "you are not an injured spouse). L3 'Did (or will) the IRS use the joint overpayment to pay any of "
                "the following legally enforceable past-due debt(s) owed only by your spouse?' - federal tax, state "
                "income tax, state unemployment compensation, child support, spousal support, federal nontax debt "
                "(such as a student loan) (No -> Stop). L4 'Are you legally obligated to pay this past-due amount?' "
                "(Yes -> Stop; you may qualify for innocent spouse relief). L5 'Were you a resident of a community "
                "property state at any time during the tax year?' (Yes -> name the state(s), skip lines 6-9, go to "
                "Part II). L6 'Did you make and report payments, such as federal income tax withholding or estimated "
                "tax payments?' (Yes -> Part II). L7 earned income? L8 'Did (or will) you claim the earned income "
                "credit or additional child tax credit?' (Yes -> Part II). L9 'Did (or will) you claim a refundable "
                "tax credit?' (Yes -> Part II; No -> Stop, you are not an injured spouse)."
            ),
            "summary_text": "Part I: joint return (L2) + debt owed only by spouse (L3) + NOT legally obligated (L4) + qualify via L5 community-property / L6 payments / L8 EIC-ACTC / L9 refundable credit.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "Part III allocation lines + col constraint (Rev. 11-2023 verbatim)",
            "excerpt_text": (
                "Part III 'Allocation Between Spouses of Items on the Joint Return.' Three columns: (a) Amount shown "
                "on joint return, (b) Allocated to injured spouse, (c) Allocated to other spouse - 'Column (a) must "
                "equal columns (b) + (c).' Lines: 13a Income reported on Form(s) W-2; 13b All other income; 14 "
                "Adjustments to income; 15 Standard deduction or itemized deductions; 16 Nonrefundable credits; 17 "
                "Refundable credits (do not include any earned income credit); 18 Other taxes; 19 Federal income tax "
                "withheld; 20 Payments. Part II: L10 names/SSNs in joint-return order + 'if injured spouse, check "
                "here'; L11 refund in both names; L12 different mailing address. Part IV signature (only if filed by "
                "itself)."
            ),
            "summary_text": "Part III cols (a)=(b)+(c): 13a W-2 income, 13b other income, 14 adjustments, 15 std/itemized, 16 nonrefundable credits, 17 refundable (no EIC), 18 other taxes, 19 withholding, 20 payments.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "IRS_I8379", "source_type": "official_instructions", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Instructions for Form 8379 (Rev. 11-2024)",
        "citation": "Instructions for Form 8379 (Rev. November 2024)", "issuer": "Internal Revenue Service",
        "official_url": "https://www.irs.gov/instructions/i8379",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.5, "topics": ["injured_spouse_allocation"],
        "excerpts": [{
            "excerpt_label": "Allocation rules + community property + time limit (i8379 Rev. 11-2024 verbatim substance)",
            "excerpt_text": (
                "Allocate line 13a W-2 income to the spouse who earned it; line 13b other joint income as you "
                "determine. Line 15: 'In columns (b) and (c), include one-half of your basic standard deduction' "
                "(the additional standard deduction for age/blindness goes to the spouse who qualifies). Allocate "
                "the child tax credit, credit for other dependents, child-and-dependent-care, and education credits "
                "to the spouse who would have claimed the qualifying child/relative on a separate return. Line 18: "
                "allocate self-employment tax to the spouse who earned the SE income. Line 19: enter federal income "
                "tax withheld from each spouse's income as shown on Forms W-2/W-2G/1099. The IRS allocates the "
                "earned income credit itself and figures the injured spouse's share of the overpayment. Community "
                "property states: Arizona, California, Idaho, Louisiana, Nevada, New Mexico, Texas, Washington, and "
                "Wisconsin - the IRS divides the joint overpayment based on state community property law (generally "
                "50%, except EIC). File Form 8379 within 3 years from the date the return was filed (including "
                "extensions) or 2 years from the date the tax was paid, whichever is later. Processing: about 14 "
                "weeks (paper with the return), 11 weeks (e-filed with the return), 8 weeks (filed by itself). Form "
                "8379 (injured spouse) is different from Form 8857 (innocent spouse relief from a joint liability)."
            ),
            "summary_text": "W-2 to earner; withholding follows income; std deduction 1/2 basic each; dependent credits to claiming spouse; EIC IRS-allocated. 9 community-property states -> IRS divides per state law. 3yr/2yr limit. 14/11/8-wk processing. 8379 != 8857.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "IRC_6402", "source_type": "statute", "source_rank": "controlling",
        "jurisdiction_code": "US", "title": "IRC §6402(c)-(e) — application of overpayment against past-due debts (Treasury offset)",
        "citation": "26 U.S.C. §6402(c),(d),(e)", "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/6402",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.2, "topics": ["injured_spouse_allocation"],
        "excerpts": [{
            "excerpt_label": "§6402 overpayment offset (verbatim substance)",
            "excerpt_text": (
                "§6402(c): the amount of any overpayment to be refunded is reduced by past-due child support. "
                "§6402(d): reduced by any past-due, legally enforceable debt owed to a federal agency. §6402(e): "
                "reduced by past-due, legally enforceable state income tax obligations. The injured-spouse "
                "administrative procedure lets the non-obligated spouse recover their share of a joint overpayment "
                "applied against the other spouse's separate obligation. (Contrast §6015, innocent spouse relief "
                "from joint and several liability, Form 8857.)"
            ),
            "summary_text": "§6402(c)/(d)/(e) reduce a refund by past-due child support / federal debt / state income tax; injured-spouse procedure recovers the non-obligated spouse's share. Contrast §6015 (Form 8857).",
            "is_key_excerpt": True,
        }],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_F8379", "8379", "governs"), ("IRS_I8379", "8379", "governs"), ("IRC_6402", "8379", "governs"),
]


F8379_FACTS: list[dict] = [
    # Part I — eligibility
    {"fact_key": "filed_joint", "label": "Filed (or will file) a joint return? (L2)", "data_type": "boolean", "required": False, "sort_order": 1},
    {"fact_key": "debt_spouse_only", "label": "Joint overpayment used for a past-due debt owed ONLY by your spouse? (L3)", "data_type": "boolean", "required": False, "sort_order": 2,
     "notes": "Debt types: federal tax / state income tax / state unemployment / child support / spousal support / federal nontax (student loan)."},
    {"fact_key": "legally_obligated", "label": "Are YOU legally obligated to pay this past-due amount? (L4)", "data_type": "boolean", "required": False, "sort_order": 3,
     "notes": "Yes -> STOP, not an injured spouse; may qualify for innocent spouse relief (Form 8857)."},
    {"fact_key": "community_property_resident", "label": "Resident of a community-property state at any time in the tax year? (L5)", "data_type": "boolean", "required": False, "sort_order": 4,
     "notes": "Yes -> skip L6-9, go to Part II; IRS divides the refund per state community-property law."},
    {"fact_key": "community_property_state", "label": "Community-property state(s) (AZ/CA/ID/LA/NV/NM/TX/WA/WI)", "data_type": "string", "required": False, "sort_order": 5},
    {"fact_key": "made_reported_payments", "label": "Made & reported payments (federal withholding or estimated tax)? (L6)", "data_type": "boolean", "required": False, "sort_order": 6},
    {"fact_key": "has_earned_income", "label": "Had earned income (wages, salaries, self-employment)? (L7)", "data_type": "boolean", "required": False, "sort_order": 7},
    {"fact_key": "claimed_eic_actc", "label": "Claimed the earned income credit or additional child tax credit? (L8)", "data_type": "boolean", "required": False, "sort_order": 8},
    {"fact_key": "claimed_refundable_credit", "label": "Claimed a refundable tax credit? (L9)", "data_type": "boolean", "required": False, "sort_order": 9},
    # Part III — representative allocation lines (col a = b + c)
    {"fact_key": "w2_income_joint", "label": "W-2 income shown on the joint return (L13a col a)", "data_type": "decimal", "required": False, "sort_order": 10},
    {"fact_key": "w2_income_injured", "label": "W-2 income allocated to the injured spouse (L13a col b) — the spouse who earned it", "data_type": "decimal", "required": False, "sort_order": 11},
    {"fact_key": "w2_income_other", "label": "W-2 income allocated to the other spouse (L13a col c)", "data_type": "decimal", "required": False, "sort_order": 12},
    {"fact_key": "withholding_joint", "label": "Federal income tax withheld on the joint return (L19 col a)", "data_type": "decimal", "required": False, "sort_order": 13},
    {"fact_key": "withholding_injured", "label": "Withholding allocated to the injured spouse (L19 col b) — follows the income", "data_type": "decimal", "required": False, "sort_order": 14},
    {"fact_key": "withholding_other", "label": "Withholding allocated to the other spouse (L19 col c)", "data_type": "decimal", "required": False, "sort_order": 15},
    {"fact_key": "basic_std_deduction", "label": "Basic standard deduction on the joint return (L15 col a) — split one-half each", "data_type": "decimal", "required": False, "sort_order": 16},
]

F8379_RULES: list[dict] = [
    {"rule_id": "R-8379-ELIG", "title": "Part I eligibility decision tree -> is_injured_spouse", "rule_type": "routing",
     "formula": ("if not filed_joint: (False, not_joint) ; elif not debt_spouse_only: (False, debt_not_spouse_only) ; "
                 "elif legally_obligated: (False, legally_obligated) ; elif community_property_resident: (True, community_property) ; "
                 "elif made_reported_payments: (True, made_payments) ; elif claimed_eic_actc: (True, eic_actc) ; "
                 "elif claimed_refundable_credit: (True, refundable_credit) ; else: (False, no_qualifying_path)"),
     "inputs": ["filed_joint", "debt_spouse_only", "legally_obligated", "community_property_resident", "made_reported_payments", "claimed_eic_actc", "claimed_refundable_credit"],
     "outputs": ["is_injured_spouse", "eligibility_reason"], "sort_order": 1,
     "description": "W1. Part I: an injured spouse (a) filed a joint return, (b) had the overpayment offset to a past-due debt owed ONLY by the spouse, (c) is NOT legally obligated to pay it, and (d) qualifies by reaching Part II via L5 community-property residency, L6 made/reported payments, L8 EIC/ACTC, or L9 another refundable credit. Any earlier fail -> not an injured spouse."},
    {"rule_id": "R-8379-ALLOC", "title": "Part III allocation constraint col (a) = (b) + (c)", "rule_type": "validation",
     "formula": "for each line: col_a == col_b + col_c  (e.g., w2_income_joint == w2_income_injured + w2_income_other ; withholding_joint == withholding_injured + withholding_other)",
     "inputs": ["w2_income_joint", "w2_income_injured", "w2_income_other", "withholding_joint", "withholding_injured", "withholding_other"],
     "outputs": ["allocation_balanced"], "sort_order": 2,
     "description": "W2. Part III: on every allocation line, column (a) amount shown on the joint return must equal column (b) allocated to the injured spouse + column (c) allocated to the other spouse. W-2 income is allocated to the spouse who earned it; federal income tax withheld follows the income it was withheld from. The IRS computes the injured spouse's refund share from the allocation (not estimated here)."},
    {"rule_id": "R-8379-STDDED", "title": "Part III line 15 — standard deduction split 50/50", "rule_type": "calculation",
     "formula": "each_spouse_std = basic_std_deduction / 2",
     "inputs": ["basic_std_deduction"], "outputs": ["std_deduction_half"], "sort_order": 3,
     "description": "W2. Line 15: allocate one-half of the BASIC standard deduction to each spouse (columns (b) and (c)). The additional standard deduction for age/blindness is allocated to the individual spouse who qualifies."},
    {"rule_id": "R-8379-CP", "title": "Community-property override gate (9 states)", "rule_type": "routing",
     "formula": "if community_property_resident (state in AZ/CA/ID/LA/NV/NM/TX/WA/WI): skip L6-9 -> Part II ; IRS divides the joint overpayment per state community-property law (not necessarily the Part III entries)",
     "inputs": ["community_property_resident", "community_property_state"], "outputs": ["community_property_override"], "sort_order": 4,
     "description": "W3. A resident of a community-property state (Arizona, California, Idaho, Louisiana, Nevada, New Mexico, Texas, Washington, Wisconsin) skips the L6-L9 income tests (L5 -> Part II). The IRS divides the joint overpayment based on state community-property law - generally 50% (except EIC) - which may override the taxpayer's Part III allocation."},
]

F8379_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-8379-ELIG", "IRS_F8379", "primary", "Part I L2-9"),
    ("R-8379-ELIG", "IRC_6402", "secondary", "§6402 offset / injured-spouse procedure"),
    ("R-8379-ALLOC", "IRS_F8379", "primary", "Part III cols (a)=(b)+(c)"),
    ("R-8379-ALLOC", "IRS_I8379", "secondary", "allocation rules (W-2 to earner, withholding follows income)"),
    ("R-8379-STDDED", "IRS_I8379", "primary", "line 15 one-half basic standard deduction"),
    ("R-8379-CP", "IRS_I8379", "primary", "community-property states + override"),
]

F8379_LINES: list[dict] = [
    {"line_number": "P1_ELIG", "description": "Part I eligibility -> is_injured_spouse", "line_type": "calculated", "source_rules": ["R-8379-ELIG"], "sort_order": 1},
    {"line_number": "L13a", "description": "W-2 income allocation (col a = b + c)", "line_type": "input", "source_rules": ["R-8379-ALLOC"], "sort_order": 2},
    {"line_number": "L15", "description": "Standard deduction split (one-half each)", "line_type": "calculated", "source_rules": ["R-8379-STDDED"], "sort_order": 3},
    {"line_number": "L19", "description": "Federal income tax withheld allocation (follows income)", "line_type": "input", "source_rules": ["R-8379-ALLOC"], "sort_order": 4},
]

F8379_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_8379_NOTINJURED", "title": "Not an injured spouse — do not file Form 8379", "severity": "warning",
     "condition": "not filed_joint or not debt_spouse_only or (not community_property_resident and not made_reported_payments and not claimed_eic_actc and not claimed_refundable_credit)",
     "message": "Based on Part I you are not an injured spouse: you must have filed a joint return, had the overpayment applied to a past-due debt owed ONLY by your spouse, and either lived in a community-property state, made & reported payments (withholding/estimated), claimed the EIC/additional child tax credit, or claimed another refundable credit. If none apply, do not file Form 8379.",
     "notes": "W1."},
    {"diagnostic_id": "D_8379_8857", "title": "Legally obligated on the debt — this may be innocent spouse (Form 8857)", "severity": "warning",
     "condition": "legally_obligated",
     "message": "If you are legally obligated to pay the past-due amount, you are NOT an injured spouse. Form 8379 (injured spouse) recovers your share of a refund taken for your spouse's SEPARATE debt. If instead you are seeking relief from a joint tax LIABILITY arising from your spouse's erroneous items, that is INNOCENT spouse relief - file Form 8857, not Form 8379.",
     "notes": "W4. The injured-vs-innocent distinction."},
    {"diagnostic_id": "D_8379_ALLOC_BALANCE", "title": "Part III columns must balance: (a) = (b) + (c)", "severity": "error",
     "condition": "w2_income_joint != w2_income_injured + w2_income_other or withholding_joint != withholding_injured + withholding_other",
     "message": "On every Part III line, column (a) 'amount shown on joint return' must equal column (b) 'allocated to injured spouse' + column (c) 'allocated to other spouse'. Reconcile each line so (b) + (c) = (a).",
     "notes": "W2."},
    {"diagnostic_id": "D_8379_WITHHOLDING", "title": "Withholding follows the income it was withheld from", "severity": "info",
     "condition": "withholding_joint > 0",
     "message": "Allocate federal income tax withheld (line 19) to each spouse based on their own Forms W-2/W-2G/1099 - the withholding follows the income it was withheld from. Likewise, allocate W-2 income (line 13a) to the spouse who earned it.",
     "notes": "W2."},
    {"diagnostic_id": "D_8379_STDDED", "title": "Standard deduction is split one-half to each spouse", "severity": "info",
     "condition": "basic_std_deduction > 0",
     "message": "Allocate one-half of the basic standard deduction to each spouse on line 15 (columns (b) and (c)). The additional standard deduction for age 65+/blindness is allocated to the individual spouse who qualifies. Allocate dependent-driven credits (child tax credit, ODC, dependent care, education) to the spouse who would have claimed the dependent on a separate return.",
     "notes": "W2."},
    {"diagnostic_id": "D_8379_CP", "title": "Community-property state — IRS divides the refund per state law", "severity": "warning",
     "condition": "community_property_resident",
     "message": "You indicated residency in a community-property state (Arizona, California, Idaho, Louisiana, Nevada, New Mexico, Texas, Washington, Wisconsin). Skip Part I lines 6-9 and go to Part II. The IRS divides the joint overpayment based on state community-property law (generally 50%, except the EIC) - which may NOT follow your Part III allocation entries.",
     "notes": "W3."},
    {"diagnostic_id": "D_8379_EIC", "title": "Do not allocate the EIC on Part III — the IRS does it", "severity": "info",
     "condition": "claimed_eic_actc",
     "message": "Do not include any earned income credit on Part III line 17 (refundable credits). The IRS allocates the EIC itself based on each spouse's earned income and the number of qualifying children, and figures the injured spouse's share of the overpayment.",
     "notes": "W2."},
    {"diagnostic_id": "D_8379_TIMELIMIT", "title": "File within 3 years of filing / 2 years of payment", "severity": "info",
     "condition": "filed_joint",
     "message": "File Form 8379 within 3 years from the date the joint return was filed (including extensions) OR 2 years from the date the tax was paid, whichever is later. File it with the joint return, with a Form 1040-X, or by itself after learning of the offset. Processing: about 14 weeks (paper with the return), 11 weeks (e-filed with the return), or 8 weeks (filed by itself). Complete Part IV (signature) only if filing by itself.",
     "notes": "W4."},
]

F8379_SCENARIOS: list[dict] = [
    {"scenario_name": "8379-A — qualifies via made/reported payments", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"filed_joint": True, "debt_spouse_only": True, "legally_obligated": False, "made_reported_payments": True},
     "expected_outputs": {"is_injured_spouse": True, "eligibility_reason": "made_payments"},
     "notes": "Joint return + debt owed only by spouse + not legally obligated + made/reported payments (L6) -> injured spouse."},
    {"scenario_name": "8379-B — legally obligated -> not injured (consider 8857)", "scenario_type": "failure", "sort_order": 2,
     "inputs": {"filed_joint": True, "debt_spouse_only": True, "legally_obligated": True},
     "expected_outputs": {"is_injured_spouse": False, "eligibility_reason": "legally_obligated", "diagnostic": "D_8379_8857"},
     "notes": "Legally obligated on the debt (L4 Yes) -> not an injured spouse; may be innocent spouse (Form 8857)."},
    {"scenario_name": "8379-C — debt not owed solely by spouse -> not injured", "scenario_type": "failure", "sort_order": 3,
     "inputs": {"filed_joint": True, "debt_spouse_only": False},
     "expected_outputs": {"is_injured_spouse": False, "eligibility_reason": "debt_not_spouse_only"},
     "notes": "The past-due debt is not owed only by the spouse (L3 No) -> not an injured spouse."},
    {"scenario_name": "8379-D — community-property resident qualifies (skip L6-9)", "scenario_type": "edge", "sort_order": 4,
     "inputs": {"filed_joint": True, "debt_spouse_only": True, "legally_obligated": False, "community_property_resident": True, "community_property_state": "CA"},
     "expected_outputs": {"is_injured_spouse": True, "eligibility_reason": "community_property", "diagnostic": "D_8379_CP"},
     "notes": "California resident (L5 Yes) -> skip L6-9 -> Part II; the IRS divides the refund per CA community-property law."},
    {"scenario_name": "8379-E — Part III columns balance", "scenario_type": "normal", "sort_order": 5,
     "inputs": {"w2_income_joint": 60000, "w2_income_injured": 40000, "w2_income_other": 20000, "withholding_joint": 8000, "withholding_injured": 5000, "withholding_other": 3000, "basic_std_deduction": 30000},
     "expected_outputs": {"allocation_balanced": True, "std_deduction_half": 15000.0},
     "notes": "W-2 60,000 = 40,000 + 20,000; withholding 8,000 = 5,000 + 3,000; standard deduction 30,000 -> 15,000 each."},
    {"scenario_name": "8379-F — Part III imbalance -> error", "scenario_type": "failure", "sort_order": 6,
     "inputs": {"w2_income_joint": 60000, "w2_income_injured": 40000, "w2_income_other": 15000, "withholding_joint": 8000, "withholding_injured": 5000, "withholding_other": 3000},
     "expected_outputs": {"allocation_balanced": False, "diagnostic": "D_8379_ALLOC_BALANCE"},
     "notes": "W-2 60,000 != 40,000 + 15,000 (55,000) -> columns don't balance; fix so (b) + (c) = (a)."},
    {"scenario_name": "8379-G — no qualifying path -> not injured", "scenario_type": "failure", "sort_order": 7,
     "inputs": {"filed_joint": True, "debt_spouse_only": True, "legally_obligated": False, "community_property_resident": False, "made_reported_payments": False, "claimed_eic_actc": False, "claimed_refundable_credit": False},
     "expected_outputs": {"is_injured_spouse": False, "eligibility_reason": "no_qualifying_path"},
     "notes": "Not community property, no payments, no EIC/ACTC, no refundable credit (L9 No) -> not an injured spouse."},
]

FORMS: list[dict] = [
    {
        "identity": {"form_number": "8379", "form_title": "Form 8379 — Injured Spouse Allocation (Rev. 11-2023)",
                     "notes": "WO-18 (SPINE S-16, 5th; DECISIONS D-20). Allocation form (not a tax computation). Part I decision tree -> is_injured_spouse (joint return + debt owed only by spouse + not legally obligated + qualify via L5 community-property / L6 payments / L8 EIC-ACTC / L9 refundable credit). Part III allocates joint items col (a)=(b)+(c) (W-2 to earner, withholding follows income, std deduction 1/2 basic each, dependent credits to claiming spouse, EIC excluded - IRS allocates). Community-property override (AZ/CA/ID/LA/NV/NM/TX/WA/WI) -> L5 skips L6-9, IRS divides per state law. IRS computes the refund share (NOT estimated). 8379 (injured) != 8857 (innocent). File 3yr-from-filing / 2yr-from-payment. entity_types [1040]. Confirmed 8379 (Ken's '8679' is a typo). No OBBBA impact."},
        "facts": F8379_FACTS, "rules": F8379_RULES, "rule_links": F8379_RULE_LINKS,
        "lines": F8379_LINES, "diagnostics": F8379_DIAGNOSTICS, "scenarios": F8379_SCENARIOS,
    },
]

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-8379-ELIG", "title": "Injured-spouse eligibility follows the Part I decision tree", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "draft", "sort_order": 1,
     "description": "is_injured_spouse is True only if filed_joint AND debt_spouse_only AND NOT legally_obligated AND (community-property OR made payments OR EIC/ACTC OR other refundable credit).",
     "definition": {"rule": "R-8379-ELIG", "check": "is_injured_spouse = filed_joint and debt_spouse_only and not legally_obligated and (community_property_resident or made_reported_payments or claimed_eic_actc or claimed_refundable_credit)"}},
    {"assertion_id": "FA-8379-ALLOC", "title": "Part III columns balance: joint (a) = injured (b) + other (c)", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "draft", "sort_order": 2,
     "description": "On each Part III allocation line, the joint-return amount equals the sum of the injured-spouse and other-spouse allocations.",
     "definition": {"rule": "R-8379-ALLOC", "check": "col_a == col_b + col_c for every allocation line"}},
    {"assertion_id": "FA-8379-CP", "title": "Community-property residency skips the income tests", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "draft", "sort_order": 3,
     "description": "A community-property-state resident qualifies via Part I line 5 (skipping lines 6-9); the IRS divides the joint overpayment per state community-property law.",
     "definition": {"rule": "R-8379-CP", "check": "community_property_resident -> qualifies (skip L6-9), IRS divides per state law"}},
]


class Command(BaseCommand):
    help = "Load the Form 8379 spec (Injured Spouse Allocation, Rev. 11-2023). Refuses to seed until READY_TO_SEED=True (W1-W4)."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad Form 8379 spec (Injured Spouse Allocation)\n"))
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
                "\nREFUSING TO SEED FORM 8379: not cleared.\n\n"
                "Gated until Ken reviews (W1 Part I eligibility tree; W2 Part III col(a)=(b)+(c) +\n"
                "allocation rules; W3 community-property override; W4 8379-vs-8857 + time limit) and\n"
                f"flips the sentinel.\n\nREADY_TO_SEED = {READY_TO_SEED}\n\nEmpty:\n  {still}\n"
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
        self.stdout.write("Form 8379 loaded.")
        self.stdout.write(f"  8379: facts {len(F8379_FACTS)} / rules {len(F8379_RULES)} / lines {len(F8379_LINES)} / diag {len(F8379_DIAGNOSTICS)} / tests {len(F8379_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}")
        self.stdout.write("=" * 60)
