"""Load the FORM_2441 spec — Child and Dependent Care Expenses (§21) ->
Schedule 3 line 2.

Post-sprint NEXT-UP #5. A nonrefundable §21 credit = an AGI-based applicable
percentage x the qualified care expenses (capped at $3,000 one / $6,000 two+),
earned-income-limited, reduced by employer dependent-care benefits (Part III),
limited by tax liability. Schedule 3 line 2 already exists in tts-tax-app as a
direct-entry feeder (the pre-CTC set), so the cross-form plumbing is ready.

Single form, the `load_1040_form_8880.py` precedent.

CONSTANTS VERIFIED 2026-06-13 (tts-tax-app server/specs/_2441_source_brief.md):
  - 2025 line-8 applicable-% table VERBATIM from the 2025 i2441 worksheet:
    35% <= $15,000, then -1% per $2,000 over $15,000, floor 20% > $43,000.
  - $3,000 (one) / $6,000 (two+) expense caps; the $250/$500-per-month
    student/disabled-spouse deeming — statutory, NON-indexed (fixed since 2003).
  - 2026 = OBBBA-enhanced INTERIM: the top rate 35% -> 50%, a two-tier
    phasedown (50 -> 35 -> 20) with the AGI thresholds DOUBLED for MFJ. The
    exact intermediate step sizes + MFJ thresholds are NOT on a published 2026
    form -> carried as an INTERIM (D_2441_002 re-pin), the SALT-2026/8880-2026
    precedent.

KEN'S CONFIRMED SCOPE (2026-06-13): (1) FORM_2441 on the 1040 + reuse Dependent
+ care_expenses/is_disabled for Part II; (2) a CareProvider sub-model for Part
I; (3) the applicable % computed year-keyed; (4) earned-income limit + the
$250/$500 deeming computed; (5) Part III (W-2 box 10 DCB) computed; (6)
qualifying-person eligibility computed (under-13 DOB OR disabled); (7) credit
nonrefundable, tax-liability-limited -> Schedule 3 line 2.

Source brief: tts-tax-app `server/specs/_2441_source_brief.md`.

SAFETY GUARD: READY_TO_SEED stays False until Ken's review walk (the 2025 table;
the 2026 OBBBA interim schedule; the Part III mechanics; the deeming).
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from sources.models import (
    AuthorityExcerpt,
    AuthorityFormLink,
    AuthoritySource,
    AuthoritySourceTopic,
    AuthorityTopic,
    RuleAuthorityLink,
)
from specs.models import (
    FlowAssertion,
    FormDiagnostic,
    FormFact,
    FormLine,
    FormRule,
    TaxForm,
    TestScenario,
)


READY_TO_SEED = False  # GATED until Ken's review walk (the 2025 table + the 2026 OBBBA interim + Part III + the deeming).


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1040"]


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS (year-keyed; the QDCGT/8880/SchA pattern)
# ═══════════════════════════════════════════════════════════════════════════

_INF = 10 ** 12

# §21 statutory, NON-indexed.
EXPENSE_LIMIT_ONE = 3000
EXPENSE_LIMIT_TWO = 6000
DEEMED_EARNED_ONE = 250   # per month (student/disabled spouse, one qualifying person)
DEEMED_EARNED_TWO = 500   # per month (two or more)

# 2025 line-8 applicable-decimal tiers (upper_bound_inclusive, decimal) —
# VERBATIM from the 2025 i2441 worksheet. 35% <= $15k, -1%/$2k, 20% > $43k.
CDCC_PCT_2025 = [
    (15000, "0.35"), (17000, "0.34"), (19000, "0.33"), (21000, "0.32"),
    (23000, "0.31"), (25000, "0.30"), (27000, "0.29"), (29000, "0.28"),
    (31000, "0.27"), (33000, "0.26"), (35000, "0.25"), (37000, "0.24"),
    (39000, "0.23"), (41000, "0.22"), (43000, "0.21"), (_INF, "0.20"),
]

# 2026 OBBBA INTERIM — top 50% / floor 20%; -1% per $2,000; the AGI thresholds
# DOUBLED for MFJ. Tier 1 (50%) ends at $15k single / $30k MFJ; the second
# phasedown (35% -> 20%) starts at $75k single / $150k MFJ. The intermediate
# step sizes + the precise thresholds are INTERIM (D_2441_002 re-pin).
CDCC_2026_TIER1_TOP = {"other": 15000, "mfj": 30000}
CDCC_2026_TIER2B_START = {"other": 75000, "mfj": 150000}


def _status_key(filing_status: str) -> str:
    return "mfj" if filing_status == "mfj" else "other"


def cdcc_decimal(agi: int, filing_status: str, tax_year: int) -> str:
    """Form 2441 line 8 — the applicable decimal (shared traceability; the
    integrity gate re-types it). 2025 verbatim; 2026 OBBBA interim."""
    import math

    if tax_year <= 2025:
        for upper, dec in CDCC_PCT_2025:
            if agi <= upper:
                return dec
        return "0.20"
    # 2026 interim
    sk = _status_key(filing_status)
    tier1 = CDCC_2026_TIER1_TOP[sk]
    tier2b = CDCC_2026_TIER2B_START[sk]
    if agi <= tier1:
        return "0.50"
    if agi <= tier2b:
        steps = math.ceil((agi - tier1) / 2000)
        return f"{max(0.35, 0.50 - 0.01 * steps):.2f}"
    steps2 = math.ceil((agi - tier2b) / 2000)
    return f"{max(0.20, 0.35 - 0.01 * steps2):.2f}"


def expense_cap(num_qualifying: int) -> int:
    return EXPENSE_LIMIT_TWO if num_qualifying >= 2 else EXPENSE_LIMIT_ONE


def deemed_monthly(num_qualifying: int) -> int:
    return DEEMED_EARNED_TWO if num_qualifying >= 2 else DEEMED_EARNED_ONE


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("child_dependent_care", "Child and Dependent Care Credit (§21) — Form 2441, AGI-% x capped expenses -> Schedule 3 line 2"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_1040_FORM",
    "IRS_2025_1040_INSTR",
]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_F2441_INSTR",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Form 2441 — Child and Dependent Care Expenses",
        "citation": "Instructions for Form 2441 (2025); i2441; Form 2441 Attachment Sequence No. 21",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i2441.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": "The 2025 line-8 applicable-% table + the $3,000/$6,000 caps + the $250/$500 deeming + Part III. REQUIRES HUMAN REVIEW: confirm the line numbers vs the 2025 form.",
        "topics": ["child_dependent_care"],
        "excerpts": [
            {
                "excerpt_label": "Line-8 applicable-% table (2025, verbatim)",
                "location_reference": "i2441 (2025), line 8 worksheet",
                "excerpt_text": (
                    "IF your AGI is Over / But not over THEN the decimal amount is: $0-$15,000 -> .35; "
                    "$15,000-$17,000 -> .34; $17,000-$19,000 -> .33; ... decreasing by .01 for each "
                    "$2,000 ... $41,000-$43,000 -> .21; over $43,000 -> .20. Line 2 expenses are limited "
                    "to $3,000 (one qualifying person) or $6,000 (two or more)."
                ),
                "summary_text": "35% <= $15k, -1% per $2,000, 20% > $43k. Caps $3,000 (one) / $6,000 (two+).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Earned-income limit + the student/disabled deeming (2025)",
                "location_reference": "i2441 (2025), lines 4-6 + 'Earned Income'",
                "excerpt_text": (
                    "Line 5: enter the smallest of line 2 (qualified expenses), line 3 (your earned "
                    "income), or line 4 (your spouse's earned income). If your spouse was a full-time "
                    "student or was disabled, figure their earned income as $250 a month (one qualifying "
                    "person) or $500 a month (two or more)."
                ),
                "summary_text": "Line 5 = smallest of expenses / your earned income / spouse earned income; a student/disabled spouse is deemed $250/$500 per month.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "OBBBA_2026_CDCC",
        "source_type": "official_guidance",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2026,
        "tax_year_end": 2026,
        "title": "OBBBA (2025) — Child and Dependent Care Credit enhancement (2026)",
        "citation": "OBBBA, P.L. 119-21 (July 4, 2025) — §21 applicable-percentage enhancement",
        "issuer": "Congress / IRS",
        "official_url": "https://www.irs.gov/newsroom",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 8.50,
        "requires_human_review": True,
        "notes": "2026 (practitioner-summarized): top rate 35% -> 50%; a two-tier phasedown (50 -> 35 -> 20); AGI thresholds DOUBLED for MFJ. INTERIM — the exact intermediate steps + thresholds re-pin from the 2026 i2441 (~Dec 2026); D_2441_002.",
        "topics": ["child_dependent_care"],
        "excerpts": [
            {
                "excerpt_label": "OBBBA 2026 CDCC enhancement (verbatim summary)",
                "location_reference": "OBBBA §21 provision",
                "excerpt_text": (
                    "Beginning 2026, the maximum applicable percentage of the child and dependent care "
                    "credit increases from 35% to 50%. The 50% applies up to $15,000 AGI ($30,000 joint), "
                    "phases down to 35% in a middle band, and phases down further from 35% to 20% above "
                    "$75,000 AGI ($150,000 joint). The $3,000/$6,000 expense limits are unchanged."
                ),
                "summary_text": "2026: top 50% (<=$15k/$30k MFJ); 50 -> 35 -> 20 two-tier phasedown; 35 -> 20 over $75k/$150k MFJ. Caps unchanged. INTERIM.",
                "is_key_excerpt": True,
            },
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_F2441_INSTR", "FORM_2441", "governs"),
    ("OBBBA_2026_CDCC", "FORM_2441", "informs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM: FORM_2441
# ═══════════════════════════════════════════════════════════════════════════

F2441_IDENTITY = {
    "form_number": "FORM_2441",
    "form_title": "Form 2441 — Child and Dependent Care Expenses (TY2025)",
    "notes": (
        "Ken's 7 scope decisions 2026-06-13 (post-sprint NEXT-UP #5). Real IRS "
        "face, ONE per return -> Schedule 3 line 2. Nonrefundable §21 credit: an "
        "AGI-based applicable percentage (year-keyed: 2025 35%->20%; 2026 OBBBA "
        "50%->35%->20% INTERIM) x the qualified expenses (capped $3,000 one / "
        "$6,000 two+), earned-income-limited (+ the $250/$500 student/disabled "
        "deeming), reduced by Part III employer dependent-care benefits (W-2 box "
        "10), limited by tax liability. Part I providers = a CareProvider "
        "sub-model; Part II qualifying persons reuse Dependent + care_expenses."
    ),
}

F2441_FACTS: list[dict] = [
    # ── Part II inputs (the qualified expenses ride Dependent.care_expenses; the
    #    counts/earned income are derived) ──
    {"fact_key": "f2441_taxpayer_earned_income", "label": "Line 3 (You) — earned income",
     "data_type": "decimal", "default_value": "0", "sort_order": 1,
     "notes": "DERIVED at compute (W-2 wages + SE earnings). Override allowed."},
    {"fact_key": "f2441_spouse_earned_income", "label": "Line 4 (Spouse) — earned income (MFJ)",
     "data_type": "decimal", "default_value": "0", "sort_order": 2, "notes": "DERIVED at compute. MFJ only."},
    {"fact_key": "f2441_spouse_student_or_disabled", "label": "Spouse was a full-time student or disabled?",
     "data_type": "boolean", "default_value": "false", "sort_order": 3,
     "notes": "Decision 4. Triggers the $250/$500-per-month deemed earned income."},
    {"fact_key": "f2441_taxpayer_student_or_disabled", "label": "You were a full-time student or disabled?",
     "data_type": "boolean", "default_value": "false", "sort_order": 4, "notes": "Decision 4 (the MFJ both-deemed case)."},
    {"fact_key": "f2441_deeming_months", "label": "Months the student/disabled spouse condition applied",
     "data_type": "integer", "default_value": "12", "sort_order": 5,
     "notes": "Decision 4. The deemed earned income = $250/$500 x this (max 12)."},
    # ── Part III — dependent care benefits (W-2 box 10) ──
    {"fact_key": "f2441_dcb_benefits", "label": "Line 12 — dependent care benefits (W-2 box 10)",
     "data_type": "decimal", "default_value": "0", "sort_order": 10,
     "notes": "DERIVED from W-2 box 10. Reduces the expense limit (Part III); excess is taxable -> 1040 line 1e."},
    # ── Outputs ──
    {"fact_key": "f2441_qualifying_count", "label": "Number of qualifying persons (under 13 or disabled)",
     "data_type": "integer", "sort_order": 20, "notes": "OUTPUT. Count of Dependent rows with care_expenses + (under-13 DOB OR is_disabled)."},
    {"fact_key": "f2441_expenses_capped", "label": "Line 3 — qualified expenses (capped, less DCB)",
     "data_type": "decimal", "sort_order": 21, "notes": "OUTPUT. min(sum expenses, $3,000/$6,000) - Part III line 31 reduction."},
    {"fact_key": "f2441_earned_income_limit", "label": "Line 6 — smallest of expenses / your / spouse earned income",
     "data_type": "decimal", "sort_order": 22, "notes": "OUTPUT. The earned-income limit (with the deeming)."},
    {"fact_key": "f2441_decimal", "label": "Line 8 — applicable decimal (AGI table)",
     "data_type": "decimal", "sort_order": 23, "notes": "OUTPUT. Year-keyed (2025 / 2026 interim)."},
    {"fact_key": "f2441_taxable_dcb", "label": "Line 26 — taxable dependent care benefits -> 1040 line 1e",
     "data_type": "decimal", "sort_order": 24, "notes": "OUTPUT. DCB over the exclusion limit; added to wages."},
    {"fact_key": "f2441_credit", "label": "Line 11 — the credit -> Schedule 3 line 2",
     "data_type": "decimal", "sort_order": 25, "notes": "OUTPUT. min(line 6 x line 8, the tax-liability cap)."},
]

F2441_RULES: list[dict] = [
    {"rule_id": "R-2441-QUALIFYING", "title": "Qualifying persons — under 13 or disabled", "rule_type": "routing",
     "precedence": 1, "sort_order": 1,
     "formula": ("f2441_qualifying_count = count(Dependent where care_expenses > 0 AND (age < 13 at the time of "
                 "care OR is_disabled)). No qualifying person -> no credit."),
     "inputs": [], "outputs": ["f2441_qualifying_count"],
     "description": "Decision 6. Reuse Dependent DOB + the is_disabled flag (+ care_expenses)."},
    {"rule_id": "R-2441-EXPENSE-CAP", "title": "Line 3 — qualified expenses capped ($3,000 / $6,000)", "rule_type": "calculation",
     "precedence": 2, "sort_order": 2,
     "formula": ("cap = 6000 if f2441_qualifying_count >= 2 else 3000; f2441_expenses_capped = min(sum care_expenses, "
                 "cap) - the Part III DCB reduction (line 31). Statutory, non-indexed."),
     "inputs": [], "outputs": ["f2441_expenses_capped"],
     "description": "Decision 1. $3,000/$6,000 per §21(c)."},
    {"rule_id": "R-2441-EARNED-INCOME", "title": "Lines 4-6 — earned-income limit + the deeming", "rule_type": "calculation",
     "precedence": 3, "sort_order": 3,
     "formula": ("you = f2441_taxpayer_earned_income (W-2+SE); spouse = f2441_spouse_earned_income; a "
                 "student/disabled spouse is DEEMED min(12, f2441_deeming_months) x (500 if count>=2 else 250); "
                 "f2441_earned_income_limit (line 6) = min(f2441_expenses_capped, you, spouse). No earned income "
                 "-> no credit (D_2441_001)."),
     "inputs": ["f2441_taxpayer_earned_income", "f2441_spouse_earned_income", "f2441_spouse_student_or_disabled", "f2441_deeming_months"],
     "outputs": ["f2441_earned_income_limit"],
     "description": "Decision 4. The $250/$500 deeming computed; earned income derived from W-2 + SE."},
    {"rule_id": "R-2441-PERCENTAGE", "title": "Line 8 — the applicable decimal (AGI table, year-keyed)", "rule_type": "calculation",
     "precedence": 4, "sort_order": 4,
     "formula": ("f2441_decimal = cdcc_decimal(1040 line 11 AGI, filing_status, year). 2025: 35% <= $15k, -1% per "
                 "$2,000, 20% > $43k (verbatim). 2026: OBBBA 50% top, two-tier phasedown, MFJ doubled (INTERIM, "
                 "D_2441_002)."),
     "inputs": [], "outputs": ["f2441_decimal"],
     "description": "Decision 3. Year-keyed; 2026 interim re-pin."},
    {"rule_id": "R-2441-PART3-DCB", "title": "Part III — employer dependent care benefits (W-2 box 10)", "rule_type": "calculation",
     "precedence": 5, "sort_order": 5,
     "formula": ("f2441_dcb_benefits (line 12) from W-2 box 10; the exclusion is limited to the smaller of the "
                 "DCB, the earned-income amounts, and $5,000 ($2,500 MFS); the excess f2441_taxable_dcb (line 26) "
                 "-> 1040 line 1e; the excluded/deducted benefits REDUCE the $3,000/$6,000 expense cap (line 31 -> "
                 "line 3)."),
     "inputs": ["f2441_dcb_benefits"], "outputs": ["f2441_taxable_dcb"],
     "description": "Decision 5. $5,000/$2,500 DCB exclusion cap (statutory)."},
    {"rule_id": "R-2441-CREDIT", "title": "Lines 9-11 — credit (tax-liability-limited) -> Schedule 3 line 2", "rule_type": "calculation",
     "precedence": 6, "sort_order": 6,
     "formula": "line9 = f2441_earned_income_limit x f2441_decimal; f2441_credit (line 11) = min(line9, the Credit Limit Worksheet) -> Schedule 3 line 2.",
     "inputs": [], "outputs": ["f2441_credit"],
     "description": "Decision 7. Nonrefundable; the pre-CTC CLW-A read. Schedule 3 line 2 is a direct-entry feeder."},
]

F2441_LINES: list[dict] = [
    {"line_number": "1", "description": "1 (Part I) Care provider(s) — name / address / TIN / amount", "line_type": "input"},
    {"line_number": "2", "description": "2 (Part II) Qualifying person(s) — name / SSN / qualified expenses", "line_type": "input"},
    {"line_number": "3", "description": "3 Qualified expenses (capped $3,000/$6,000, less Part III)", "line_type": "calculated"},
    {"line_number": "4", "description": "4 Your earned income", "line_type": "calculated"},
    {"line_number": "5", "description": "5 Spouse's earned income (MFJ; or the deemed amount)", "line_type": "calculated"},
    {"line_number": "6", "description": "6 Smallest of lines 3, 4, 5", "line_type": "calculated"},
    {"line_number": "7", "description": "7 Amount from Form 1040 line 11 (AGI)", "line_type": "calculated"},
    {"line_number": "8", "description": "8 Applicable decimal from the AGI table", "line_type": "calculated"},
    {"line_number": "9", "description": "9 Multiply line 6 by line 8", "line_type": "calculated"},
    {"line_number": "10", "description": "10 Tax liability limit (Credit Limit Worksheet)", "line_type": "calculated"},
    {"line_number": "11", "description": "11 Credit (smaller of line 9 or 10) -> Schedule 3 line 2", "line_type": "total"},
    {"line_number": "12", "description": "12 (Part III) Dependent care benefits (W-2 box 10)", "line_type": "input"},
    {"line_number": "24", "description": "24 Taxable benefits -> Form 1040 line 1e", "line_type": "calculated"},
    {"line_number": "27", "description": "27 $3,000 (one) / $6,000 (two or more)", "line_type": "calculated"},
    {"line_number": "31", "description": "31 Excludable/deductible benefits reducing the line-3 cap", "line_type": "calculated"},
]

F2441_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_2441_001", "title": "No earned income — no credit", "severity": "info",
     "condition": "f2441_taxpayer_earned_income <= 0 OR (MFJ AND spouse earned income <= 0 and not deemed)",
     "message": ("The Child and Dependent Care Credit requires earned income (both spouses on a joint return, "
                 "unless one was a full-time student or disabled). With no earned income the credit is zero."),
     "notes": "§21(d). The earned-income gate."},
    {"diagnostic_id": "D_2441_002", "title": "TY2026 applicable-% schedule is interim — re-pin", "severity": "info",
     "condition": "tax_year == 2026",
     "message": ("The 2026 child and dependent care credit was enhanced by OBBBA (top rate 50%, a two-tier "
                 "phasedown, MFJ thresholds doubled). The intermediate step sizes + thresholds are interim "
                 "pending the 2026 Form 2441 — re-verify when the IRS releases it (~Dec 2026)."),
     "notes": "The SALT-2026/8880-2026 interim precedent."},
    {"diagnostic_id": "D_2441_003", "title": "Dependent care benefits present — Part III computed", "severity": "info",
     "condition": "f2441_dcb_benefits > 0",
     "message": ("Employer dependent care benefits (W-2 box 10) are present; Part III reduces the expense limit "
                 "and any benefits over the $5,000 ($2,500 MFS) exclusion are added to wages (Form 1040 line 1e)."),
     "notes": "Decision 5."},
    {"diagnostic_id": "D_2441_004", "title": "Care provider TIN missing", "severity": "warning",
     "condition": "a CareProvider row has no EIN/SSN",
     "message": ("A care provider is missing its taxpayer identification number (EIN or SSN). The credit can be "
                 "denied without it unless due diligence is shown — enter the provider's TIN."),
     "notes": "Part I due diligence."},
    {"diagnostic_id": "D_2441_005", "title": "Taxable dependent care benefits added to wages", "severity": "info",
     "condition": "f2441_taxable_dcb > 0",
     "message": ("Dependent care benefits exceed the exclusion limit; the taxable excess is added to Form 1040 "
                 "line 1e (wages)."),
     "notes": "Decision 5; Part III line 26."},
    {"diagnostic_id": "D_2441_006", "title": "Student/disabled-spouse deeming applied", "severity": "info",
     "condition": "f2441_spouse_student_or_disabled is True",
     "message": ("A full-time-student or disabled spouse is deemed to have earned income of $250 (one qualifying "
                 "person) or $500 (two or more) per month — verify the number of months entered."),
     "notes": "Decision 4."},
]

F2441_SCENARIOS: list[dict] = [
    {"scenario_name": "2441-T1 — one child, expenses capped at $3,000, 35% tier", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "filing_status": "single", "agi": 14000, "qualifying_count": 1,
                "care_expenses": 4000, "taxpayer_earned_income": 40000},
     "expected_outputs": {"f2441_expenses_capped": 3000, "f2441_decimal": 0.35, "f2441_credit": 1050},
     "notes": "min(4,000, 3,000) = 3,000; AGI 14,000 <= 15,000 -> 0.35; 3,000 x 0.35 = 1,050 (earned income 40k not binding)."},
    {"scenario_name": "2441-T2 — two+ children, $6,000 cap, 20% floor", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "agi": 80000, "qualifying_count": 2,
                "care_expenses": 7000, "taxpayer_earned_income": 50000, "spouse_earned_income": 30000},
     "expected_outputs": {"f2441_expenses_capped": 6000, "f2441_decimal": 0.20, "f2441_credit": 1200},
     "notes": "min(7,000, 6,000) = 6,000; AGI 80,000 > 43,000 -> 0.20; 6,000 x 0.20 = 1,200."},
    {"scenario_name": "2441-T3 — earned-income limit binds", "scenario_type": "edge_case", "sort_order": 3,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "agi": 30000, "qualifying_count": 1,
                "care_expenses": 3000, "taxpayer_earned_income": 25000, "spouse_earned_income": 2000},
     "expected_outputs": {"f2441_earned_income_limit": 2000, "f2441_decimal": 0.27, "f2441_credit": 540},
     "notes": "line 6 = min(3,000, 25,000, 2,000) = 2,000; AGI 30,000 (29k-31k) -> 0.27; 2,000 x 0.27 = 540."},
    {"scenario_name": "2441-T4 — DCB reduces the expense limit", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "agi": 20000, "qualifying_count": 1,
                "care_expenses": 3000, "dcb_benefits": 2000, "taxpayer_earned_income": 40000, "spouse_earned_income": 40000},
     "expected_outputs": {"f2441_expenses_capped": 1000, "f2441_decimal": 0.32, "f2441_credit": 320},
     "notes": "the $2,000 DCB reduces the $3,000 cap to $1,000; AGI 20,000 (19k-21k) -> 0.32; 1,000 x 0.32 = 320."},
    {"scenario_name": "2441-T5 — 2026 OBBBA top 50% (interim)", "scenario_type": "normal", "sort_order": 5,
     "inputs": {"tax_year": 2026, "filing_status": "single", "agi": 10000, "qualifying_count": 1,
                "care_expenses": 3000, "taxpayer_earned_income": 12000},
     "expected_outputs": {"f2441_decimal": 0.50, "f2441_credit": 1500, "D_2441_002": True},
     "notes": "2026 AGI 10,000 <= 15,000 -> 0.50 (the verified top); 3,000 x 0.50 = 1,500; D_2441_002 interim flag."},
    {"scenario_name": "2441-T6 — student/disabled-spouse deeming", "scenario_type": "normal", "sort_order": 6,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "agi": 24000, "qualifying_count": 2,
                "care_expenses": 6000, "taxpayer_earned_income": 40000, "spouse_earned_income": 0,
                "spouse_student_or_disabled": True, "deeming_months": 12},
     "expected_outputs": {"f2441_earned_income_limit": 6000, "f2441_decimal": 0.30, "D_2441_006": True},
     "notes": "spouse deemed 500 x 12 = 6,000; line 6 = min(6,000, 40,000, 6,000) = 6,000; AGI 24,000 (23k-25k) -> 0.30."},
    {"scenario_name": "2441-G1 — no earned income -> no credit", "scenario_type": "diagnostic", "sort_order": 7,
     "inputs": {"tax_year": 2025, "filing_status": "single", "agi": 20000, "qualifying_count": 1,
                "care_expenses": 3000, "taxpayer_earned_income": 0},
     "expected_outputs": {"f2441_credit": 0, "D_2441_001": True},
     "notes": "no earned income -> line 6 = 0 -> credit 0 (D_2441_001)."},
]

F2441_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-2441-QUALIFYING", "IRS_2025_F2441_INSTR", "primary", "Qualifying person (under 13 / disabled)"),
    ("R-2441-EXPENSE-CAP", "IRS_2025_F2441_INSTR", "primary", "The $3,000/$6,000 expense caps"),
    ("R-2441-EARNED-INCOME", "IRS_2025_F2441_INSTR", "primary", "Lines 4-6 + the $250/$500 deeming"),
    ("R-2441-PERCENTAGE", "IRS_2025_F2441_INSTR", "primary", "Line 8: the 2025 AGI table (verbatim)"),
    ("R-2441-PERCENTAGE", "OBBBA_2026_CDCC", "secondary", "2026 OBBBA 50% top + two-tier phasedown (interim)"),
    ("R-2441-PART3-DCB", "IRS_2025_F2441_INSTR", "primary", "Part III dependent care benefits"),
    ("R-2441-CREDIT", "IRS_2025_F2441_INSTR", "primary", "Lines 9-11: credit -> Schedule 3 line 2"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-2441-01", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "Line 8 decimal == the AGI table (year-keyed)",
     "description": "Pins the 2025 35%->20% table + the 2026 verified endpoints (50% top / 20% floor). Bug it catches: a drifted bracket or the wrong year's schedule.",
     "definition": {"kind": "constants_check", "form": "FORM_2441",
                    "constants": {"top_2025": 0.35, "floor": 0.20, "step_threshold_2025": 15000, "floor_threshold_2025": 43000,
                                  "top_2026": 0.50, "tier1_top_2026_other": 15000, "tier1_top_2026_mfj": 30000}},
     "sort_order": 1},
    {"assertion_id": "FA-1040-2441-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Expense cap: $3,000 (one) / $6,000 (two+), less Part III DCB",
     "description": "Validates R-2441-EXPENSE-CAP. Bug it catches: an uncapped expense (2441-T1 caps 4,000 at 3,000) or the DCB reduction missing.",
     "definition": {"kind": "formula_check", "form": "FORM_2441",
                    "formula": "expenses_capped == min(sum_expenses, 6000 if count>=2 else 3000) - dcb_reduction"},
     "sort_order": 2},
    {"assertion_id": "FA-1040-2441-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Earned-income limit (line 6) = min(expenses, your, spouse) with the deeming",
     "description": "Validates R-2441-EARNED-INCOME. Bug it catches: the limit not binding (2441-T3 -> 2,000) or the $250/$500 deeming missing.",
     "definition": {"kind": "formula_check", "form": "FORM_2441",
                    "formula": "line_6 == min(expenses_capped, taxpayer_earned, spouse_earned_or_deemed); deemed = months x (500 if count>=2 else 250)"},
     "sort_order": 3},
    {"assertion_id": "FA-1040-2441-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Credit = min(line 6 x line 8, tax cap) -> Schedule 3 line 2",
     "description": "Validates R-2441-CREDIT. Bug it catches: a refundable overflow past the tax-liability limit, or the result not landing on Schedule 3 line 2.",
     "definition": {"kind": "flow_assertion", "form": "FORM_2441",
                    "checks": [{"source_line": "11", "must_write_to": ["SCH_3.2"]}]},
     "sort_order": 4},
    {"assertion_id": "FA-1040-2441-05", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Part III: taxable DCB over the exclusion -> 1040 line 1e",
     "description": "Validates R-2441-PART3-DCB. Bug it catches: the $5,000/$2,500 exclusion missing, or the taxable excess not reaching wages.",
     "definition": {"kind": "flow_assertion", "form": "FORM_2441",
                    "checks": [{"source": "Part III dependent care benefits", "must_write_to": ["FORM_2441.24", "1040.1e"]}]},
     "sort_order": 5},
    {"assertion_id": "FA-1040-2441-06", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Gates: no earned income -> no credit; 2026 interim flags",
     "description": "No earned income fires D_2441_001 (credit zeroed); a 2026 return fires D_2441_002 (the interim re-pin).",
     "definition": {"kind": "gating_check", "form": "FORM_2441", "expect": {"red_fires": True},
                    "blockers": ["no_earned_income", "interim_2026"]},
     "sort_order": 6},
]


FORMS: list[dict] = [
    {"identity": F2441_IDENTITY, "facts": F2441_FACTS, "rules": F2441_RULES, "lines": F2441_LINES,
     "diagnostics": F2441_DIAGNOSTICS, "scenarios": F2441_SCENARIOS, "rule_links": F2441_RULE_LINKS},
]


class Command(BaseCommand):
    help = "Load the FORM_2441 spec (Child and Dependent Care Credit). Refuses until READY_TO_SEED=True."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad FORM_2441 spec (Child and Dependent Care Credit)\n"))
        self._load_topics()
        sources = self._load_sources()
        self._load_new_excerpts_on_existing(sources)
        for spec in FORMS:
            form = self._upsert_form(spec["identity"])
            self._upsert_facts(form, spec["facts"])
            rules = self._upsert_rules(form, spec["rules"])
            self._upsert_authority_links(rules, sources, spec["rule_links"])
            self._upsert_lines(form, spec["lines"])
            self._upsert_diagnostics(form, spec["diagnostics"])
            self._upsert_tests(form, spec["scenarios"])
        self._upsert_form_links(sources)
        self._load_flow_assertions()
        self._report_totals()

    def _guard_against_hollow_seed(self):
        empty = []
        for spec in FORMS:
            fn = spec["identity"]["form_number"]
            for key in ("facts", "rules", "lines", "diagnostics", "scenarios", "rule_links"):
                if not spec[key]:
                    empty.append(f"{fn}.{key}")
        if not FLOW_ASSERTIONS:
            empty.append("FLOW_ASSERTIONS")
        if not READY_TO_SEED or empty:
            still_empty = "\n  ".join(f"- {n}" for n in empty) or "(all populated)"
            raise CommandError(
                "\nREFUSING TO SEED FORM_2441: not cleared to seed.\n\n"
                "Gated until Ken's review walk (the 2025 line-8 table; the 2026 OBBBA interim\n"
                "schedule; the Part III dependent-care-benefits mechanics; the $250/$500 deeming).\n\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True)\n\n"
                f"Currently empty / placeholder:\n  {still_empty}\n"
            )

    def _load_topics(self):
        ct = 0
        for code, name in AUTHORITY_TOPICS:
            _, created = AuthorityTopic.objects.update_or_create(topic_code=code, defaults={"topic_name": name})
            ct += 1 if created else 0
        self.stdout.write(f"Topics: {ct} new ({len(AUTHORITY_TOPICS)} in batch)")

    def _load_sources(self) -> dict:
        sources: dict = {}
        for src_data in AUTHORITY_SOURCES:
            src_data = dict(src_data)
            excerpts_data = src_data.pop("excerpts", [])
            topic_codes = src_data.pop("topics", [])
            source, _ = AuthoritySource.objects.update_or_create(
                source_code=src_data["source_code"], defaults=src_data)
            sources[source.source_code] = source
            for exc in excerpts_data:
                exc = dict(exc)
                AuthorityExcerpt.objects.update_or_create(
                    authority_source=source, excerpt_label=exc["excerpt_label"], defaults=exc)
            for tc in topic_codes:
                topic = AuthorityTopic.objects.filter(topic_code=tc).first()
                if topic:
                    AuthoritySourceTopic.objects.get_or_create(authority_source=source, authority_topic=topic)
        for code in EXISTING_SOURCES_TO_REFERENCE:
            src = AuthoritySource.objects.filter(source_code=code).first()
            if src:
                sources[code] = src
        self.stdout.write(f"Sources ready: {len(sources)}")
        return sources

    def _load_new_excerpts_on_existing(self, sources):
        for code, exc in NEW_EXCERPTS_ON_EXISTING:
            src = sources.get(code) or AuthoritySource.objects.filter(source_code=code).first()
            if src:
                exc = dict(exc)
                AuthorityExcerpt.objects.update_or_create(
                    authority_source=src, excerpt_label=exc["excerpt_label"], defaults=exc)

    def _upsert_form(self, identity: dict) -> TaxForm:
        form, created = TaxForm.objects.update_or_create(
            form_number=identity["form_number"], jurisdiction=FORM_JURISDICTION,
            tax_year=FORM_TAX_YEAR, version=FORM_VERSION,
            defaults={"form_title": identity["form_title"], "entity_types": FORM_ENTITY_TYPES,
                      "status": FORM_STATUS, "notes": identity["notes"]})
        self.stdout.write(f"{'Created' if created else 'Updated'} {identity['form_number']}")
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

    def _upsert_authority_links(self, rules, sources, rule_links):
        ct = 0
        for rule_id, source_code, level, note in rule_links:
            rule, source = rules.get(rule_id), sources.get(source_code)
            if rule and source:
                RuleAuthorityLink.objects.get_or_create(
                    form_rule=rule, authority_source=source,
                    defaults={"support_level": level, "relevance_note": note})
                ct += 1
        self.stdout.write(f"  {ct} authority links")

    def _upsert_lines(self, form, lines):
        for ln in lines:
            ln = dict(ln)
            FormLine.objects.update_or_create(tax_form=form, line_number=ln.pop("line_number"), defaults=ln)
        self.stdout.write(f"  {len(lines)} lines")

    def _upsert_diagnostics(self, form, diagnostics):
        for d in diagnostics:
            d = dict(d)
            FormDiagnostic.objects.update_or_create(tax_form=form, diagnostic_id=d.pop("diagnostic_id"), defaults=d)
        self.stdout.write(f"  {len(diagnostics)} diagnostics")

    def _upsert_tests(self, form, scenarios):
        for t in scenarios:
            t = dict(t)
            TestScenario.objects.update_or_create(tax_form=form, scenario_name=t.pop("scenario_name"), defaults=t)
        self.stdout.write(f"  {len(scenarios)} test scenarios")

    def _upsert_form_links(self, sources):
        for source_code, form_code, link_type in AUTHORITY_FORM_LINKS:
            source = sources.get(source_code) or AuthoritySource.objects.filter(source_code=source_code).first()
            if source:
                AuthorityFormLink.objects.get_or_create(
                    authority_source=source, form_code=form_code, link_type=link_type,
                    defaults={"note": f"{source_code} -> {form_code}"})

    def _load_flow_assertions(self):
        for a in FLOW_ASSERTIONS:
            a = dict(a)
            FlowAssertion.objects.update_or_create(assertion_id=a.pop("assertion_id"), defaults=a)
        self.stdout.write(f"  {len(FLOW_ASSERTIONS)} flow assertions")

    def _report_totals(self):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(f"TaxForms: {TaxForm.objects.count()} | FlowAssertions: {FlowAssertion.objects.count()}")
        form = TaxForm.objects.filter(form_number="FORM_2441").first()
        if form:
            uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
            self.stdout.write("FORM_2441: all rules cited" if not uncited
                              else self.style.WARNING(f"FORM_2441 uncited rules: {len(uncited)}"))
