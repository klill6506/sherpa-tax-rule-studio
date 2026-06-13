"""Load the SIMPLIFIED_METHOD spec — the Simplified Method Worksheet
(Form 1040, lines 5a/5b): the taxable portion of a periodic employer-plan
pension recovered against the employee's cost (basis).

NEXT-UP #1 (post Fable-5 sprint). Replaces a LIVE RED in tts-tax-app:
`compute_retirement.doc_needs_simplified_method` → **D_RET_001** fires when a
1099-R has box 2a blank / "taxable amount not determined" WITH basis (box 5 /
box 9b) — the OPM **CSA-1099-R** / TRS pattern. This spec computes the taxable
amount so those common retiree returns flow.

Single form, the `load_1040_schedule_d.py` precedent. The worksheet is a
COMPUTATIONAL pseudo-form (statement page, never a faked IRS face — like
1040_SCHD_WS / 1040_INTDIV). The per-annuity inputs (annuity starting date,
ages, joint/survivor, cost, prior-recovered, months) become new
`RetirementDistribution` fields at the build leg (scope Decision 1).

Constants VERIFIED 2026-06-13 vs IRS Pub 575 (2025) — the two
expected-number-of-payments tables + the boundary dates. Source brief:
tts-tax-app `server/specs/_next1_simplified_method_source_brief.md` (Ken's 7
scope decisions). The 11-line worksheet is reconstructed from the i1040
Simplified Method Worksheet (lines 5a/5b) + Pub 575 — flagged
`requires_human_review=True` (verbatim re-check against the 2025 i1040 at
Ken's walk); the math is independently re-derived in
`check_simplified_method_integrity.py`.

SAFETY GUARD: READY_TO_SEED = False until Ken's in-session review walk
(the verified tables, the boundary dates, the RED-defer enumeration, the
D_RET_001 supersession plan). The command refuses to write until flipped.
"""

from datetime import date

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


# ═══════════════════════════════════════════════════════════════════════════
# SAFETY GUARD — flip ONLY after Ken's in-session review walk.
# ═══════════════════════════════════════════════════════════════════════════

READY_TO_SEED = False


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1040"]


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS (every value cited; never training memory)
# Verified 2026-06-13 vs IRS Pub 575 (2025), "Simplified Method" tables.
# ═══════════════════════════════════════════════════════════════════════════

# Table 1 — single annuitant. Lookup by the annuitant's AGE at the annuity
# starting date. Entries are (inclusive_upper_age, number_of_payments); the
# last bucket (71 and over) uses a sentinel upper bound.
SM_TABLE_1: list[tuple[int, int]] = [
    (55, 360),   # 55 and under
    (60, 310),   # 56–60
    (65, 260),   # 61–65
    (70, 210),   # 66–70
    (200, 160),  # 71 and over
]

# Table 2 — more than one annuitant (joint & survivor). Lookup by the COMBINED
# ages of both annuitants at the annuity starting date.
SM_TABLE_2: list[tuple[int, int]] = [
    (110, 410),  # 110 and under
    (120, 360),  # 111–120
    (130, 310),  # 121–130
    (140, 260),  # 131–140
    (999, 210),  # 141 and over
]

# Boundary dates (STATUTORY, non-indexed):
# - The Simplified Method is in scope for annuity starting dates ON OR AFTER
#   Nov 19, 1996 (i.e., AFTER Nov 18, 1996). Earlier dates use the General Rule
#   (or the pre-1997 single-life Simplified Method) — OUT, RED-defer (D_SM_001).
SM_SIMPLIFIED_START = date(1996, 11, 19)
# - Table 2 (joint & survivor) applies only when the annuity starting date is
#   AFTER 1997 (on/after Jan 1, 1998). A joint annuity starting Nov 19 1996 –
#   Dec 31 1997 uses Table 1 (single-life).
SM_TABLE2_START = date(1998, 1, 1)
# - Annuity starting dates BEFORE 1987 have uncapped cost recovery (no cost
#   cap, no death deduction) — a different regime, OUT, RED-defer (D_SM_002).
SM_PRE1987 = date(1987, 1, 1)


def sm_lookup_payments(table: list[tuple[int, int]], age: int) -> int:
    """The number-of-payments lookup (shared by the loader's traceability and
    the integrity gate re-types it independently)."""
    for upper, payments in table:
        if age <= upper:
            return payments
    return table[-1][1]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY TOPICS / SOURCES
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("pension_annuity_taxation",
     "Taxable portion of pensions/annuities — the Simplified Method (cost recovery), Form 1040 lines 5a/5b"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_1040_FORM",    # 1040 lines 5a/5b
    "IRS_2025_1040_INSTR",   # the Simplified Method Worksheet (lines 5a/5b)
]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_PUB575",
        "source_type": "official_publication",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRS Publication 575 (2025) — Pension and Annuity Income",
        "citation": "Pub. 575 (2025), 'Simplified Method' and Worksheet A",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/publications/p575",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": False,
        "trust_score": 9.30,
        "requires_human_review": False,
        "notes": "The two expected-number-of-payments tables + the boundary dates verified 2026-06-13 from the live Pub 575 (2025).",
        "topics": ["pension_annuity_taxation"],
        "excerpts": [
            {
                "excerpt_label": "Table 1 — single annuitant (number of payments by age)",
                "location_reference": "Pub. 575 (2025), Simplified Method, Table 1",
                "excerpt_text": (
                    "If the annuitant is a single person, the number of anticipated monthly "
                    "payments by age at the annuity starting date is: 55 and under = 360; "
                    "56–60 = 310; 61–65 = 260; 66–70 = 210; 71 and over = 160."
                ),
                "summary_text": "Table 1: ≤55→360, 56-60→310, 61-65→260, 66-70→210, 71+→160. Lookup by annuitant age at the annuity starting date.",
                "is_key_excerpt": True,
                "requires_human_review": False,
            },
            {
                "excerpt_label": "Table 2 — multiple annuitants (number of payments by combined age)",
                "location_reference": "Pub. 575 (2025), Simplified Method, Table 2",
                "excerpt_text": (
                    "If there is more than one annuitant (a joint and survivor annuity), the "
                    "number of anticipated monthly payments by the combined ages at the annuity "
                    "starting date is: 110 and under = 410; 111–120 = 360; 121–130 = 310; "
                    "131–140 = 260; 141 and over = 210."
                ),
                "summary_text": "Table 2 (joint/survivor): combined ≤110→410, 111-120→360, 121-130→310, 131-140→260, 141+→210. Applies when the annuity starting date is after 1997.",
                "is_key_excerpt": True,
                "requires_human_review": False,
            },
            {
                "excerpt_label": "Boundaries + cost cap + death deduction (verbatim summary)",
                "location_reference": "Pub. 575 (2025), Simplified Method / Cost recovery",
                "excerpt_text": (
                    "You must use the Simplified Method if your annuity starting date is after "
                    "November 18, 1996, and the payments are from a qualified plan. For annuity "
                    "starting dates after 1986, the total amount of annuity income you can "
                    "exclude over the years as a recovery of your cost can't exceed your total "
                    "cost. If the annuitant dies before recovering the full cost, the unrecovered "
                    "cost is allowed as an itemized deduction on the decedent's final return. "
                    "Use Table 2 only if the annuity starting date is after 1997 and the payments "
                    "are for the lives of more than one annuitant."
                ),
                "summary_text": "In-scope: start ≥ Nov 19 1996 (before → General Rule, OUT). Post-1986 → cost cap. Death → unrecovered cost is a Schedule A deduction (NEXT-UP #2). Table 2 only post-1997.",
                "is_key_excerpt": True,
                "requires_human_review": False,
            },
        ],
    },
    {
        "source_code": "IRS_2025_1040_SMW",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Form 1040 — Simplified Method Worksheet (Lines 5a and 5b)",
        "citation": "i1040 (2025), 'Simplified Method Worksheet—Lines 5a and 5b'",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/instructions/i1040gi",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.00,
        "requires_human_review": True,
        "notes": "The 11-line worksheet is reconstructed from the i1040 Simplified Method Worksheet + Pub 575 (the IRS instructions page blocked verbatim auto-fetch). REQUIRES HUMAN REVIEW: re-check the line text/order against the 2025 i1040 at Ken's walk. The arithmetic is independently re-derived in check_simplified_method_integrity.py.",
        "topics": ["pension_annuity_taxation"],
        "excerpts": [
            {
                "excerpt_label": "Simplified Method Worksheet lines 1-11 (reconstructed; HUMAN REVIEW)",
                "location_reference": "i1040 (2025), Simplified Method Worksheet, lines 5a/5b",
                "excerpt_text": (
                    "1. Total pension/annuity payments (Form 1099-R, box 1); also enter on Form "
                    "1040, line 5a. 2. Your cost in the plan at the annuity starting date. 3. "
                    "Number from Table 1 (or Table 2 if the annuity starting date was after 1997 "
                    "and payments are for more than one annuitant). 4. Divide line 2 by line 3. "
                    "5. Multiply line 4 by the number of months for which this year's payments "
                    "were made. 6. Amount, if any, recovered tax free in years after 1986 (line "
                    "10 of last year's worksheet). 7. Subtract line 6 from line 2. 8. Smaller of "
                    "line 5 or line 7. 9. Taxable amount: subtract line 8 from line 1 (not less "
                    "than zero); enter on Form 1040, line 5b. 10. Add lines 6 and 8 (amount "
                    "recovered tax free through this year — used next year on line 6). 11. "
                    "Balance of cost to be recovered: subtract line 10 from line 2."
                ),
                "summary_text": "RECONSTRUCTED (human review). Cost ÷ number = per-payment; × months = tax-free candidate; capped at cost remaining; box1 − tax-free = taxable → 5b; the recovered/balance carry to next year.",
                "is_key_excerpt": True,
                "requires_human_review": True,
            },
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_PUB575", "SIMPLIFIED_METHOD", "informs"),
    ("IRS_2025_1040_SMW", "SIMPLIFIED_METHOD", "governs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM: SIMPLIFIED_METHOD
# ═══════════════════════════════════════════════════════════════════════════

SM_IDENTITY = {
    "form_number": "SIMPLIFIED_METHOD",
    "form_title": "Simplified Method Worksheet (Form 1040, lines 5a/5b) — taxable pension via cost recovery (TY2025)",
    "notes": (
        "NEXT-UP #1 (Ken's 7 scope decisions 2026-06-13). Computational pseudo-form "
        "(statement page, never a faked IRS face). Per-annuity: the cost (basis) is "
        "recovered tax-free over the expected number of monthly payments (Table 1 "
        "single-life / Table 2 joint-survivor by combined age); the remainder of "
        "box 1 is taxable -> Form 1040 line 5b. In scope only for annuity starting "
        "dates on/after Nov 19, 1996 (Decision 3) and non-IRA pensions (Decision 7); "
        "pre-1987 (Decision 4), the General Rule, Form 8606 IRA basis, and the "
        "death-unrecovered-cost Schedule A deduction (Decision 6) RED/note-defer. "
        "Supersedes/narrows tts-tax-app D_RET_001 (the box-2a-blank-with-basis blank)."
    ),
}

SM_FACTS: list[dict] = [
    # ── Per-annuity preparer inputs (new RetirementDistribution fields) ──
    {"fact_key": "sm_annuity_start_date", "label": "Annuity starting date (the date the first payment period ended)",
     "data_type": "date", "sort_order": 1,
     "notes": ("PER-ANNUITY INPUT. Drives the in-scope boundary (>= Nov 19, 1996 -> Simplified Method; before "
               "-> D_SM_001 General Rule) and the Table-2 boundary (after 1997). Before 1987 -> D_SM_002.")},
    {"fact_key": "sm_age_at_start", "label": "Annuitant's age at the annuity starting date",
     "data_type": "integer", "sort_order": 2,
     "notes": "PER-ANNUITY INPUT. Table 1 lookup (single-life) or one half of the Table 2 combined age."},
    {"fact_key": "sm_is_joint_survivor", "label": "Joint-and-survivor annuity (payments continue to a survivor)?",
     "data_type": "boolean", "default_value": "false", "sort_order": 3,
     "notes": "PER-ANNUITY INPUT. True + start after 1997 -> Table 2 (combined age). Without sm_survivor_age_at_start -> D_SM_003."},
    {"fact_key": "sm_survivor_age_at_start", "label": "Survivor annuitant's age at the annuity starting date",
     "data_type": "integer", "required": False, "sort_order": 4,
     "notes": "PER-ANNUITY INPUT (nullable). Added to sm_age_at_start for the Table 2 combined-age lookup."},
    {"fact_key": "sm_cost_in_plan", "label": "Cost (basis) in the plan at the annuity starting date",
     "data_type": "decimal", "default_value": "0", "sort_order": 5,
     "notes": ("PER-ANNUITY INPUT. Usually 1099-R box 9b (total employee contributions); box 5 is the current-year "
               "amount, not the total. Worksheet line 2.")},
    {"fact_key": "sm_prior_recovered_tax_free", "label": "Amount recovered tax free in PRIOR years (cumulative, after 1986)",
     "data_type": "decimal", "default_value": "0", "sort_order": 6,
     "notes": ("PER-ANNUITY INPUT (year 2+). The Schedule-D-carryover pattern (Decision 5): last year's worksheet "
               "line 10. Worksheet line 6; caps current-year recovery (line 7 = cost - this).")},
    {"fact_key": "sm_months_paid_this_year", "label": "Number of months payments were received this year",
     "data_type": "integer", "default_value": "12", "sort_order": 7,
     "notes": "PER-ANNUITY INPUT. 12 normally; partial in the first/last year. Worksheet line 5 multiplier."},
    # ── Outputs (written by compute) ──
    {"fact_key": "sm_number_of_payments", "label": "Line 3 — expected number of monthly payments (Table 1/2)", "data_type": "integer", "sort_order": 20,
     "notes": "OUTPUT. Table 1 by sm_age_at_start, or Table 2 by combined age when joint + start after 1997."},
    {"fact_key": "sm_tax_free_per_payment", "label": "Line 4 — tax-free amount per payment (cost / number)", "data_type": "decimal", "sort_order": 21,
     "notes": "OUTPUT. line 2 / line 3, to cents."},
    {"fact_key": "sm_tax_free_this_year", "label": "Line 8 — tax-free amount this year (capped at cost remaining)", "data_type": "decimal", "sort_order": 22,
     "notes": "OUTPUT. min(line 5 = per-payment x months, line 7 = cost - prior-recovered). The cost cap (post-1986)."},
    {"fact_key": "sm_taxable", "label": "Line 9 — taxable amount -> Form 1040 line 5b", "data_type": "decimal", "sort_order": 23,
     "notes": "OUTPUT. max(0, box1 - line 8) -> 1040 line 5b. Supersedes the D_RET_001 blank."},
    {"fact_key": "sm_recovered_through_year", "label": "Line 10 — amount recovered tax free THROUGH this year", "data_type": "decimal", "sort_order": 24,
     "notes": "OUTPUT. line 6 + line 8. Next year's sm_prior_recovered_tax_free (the carryover)."},
    {"fact_key": "sm_balance_of_cost", "label": "Line 11 — balance of cost remaining to recover", "data_type": "decimal", "sort_order": 25,
     "notes": "OUTPUT. line 2 - line 10. Zero -> fully recovered, next year fully taxable (D_SM_004)."},
    {"fact_key": "sm_table_used", "label": "Which payments table was used (1 single-life / 2 joint-survivor)", "data_type": "integer", "sort_order": 26,
     "notes": "OUTPUT. 2 iff sm_is_joint_survivor AND start after 1997; else 1."},
]

SM_RULES: list[dict] = [
    {"rule_id": "R-SM-SCOPE", "title": "In-scope gate: post-Nov-18-1996, non-IRA pension with basis",
     "rule_type": "routing", "precedence": 1, "sort_order": 1,
     "formula": ("Compute iff sm_annuity_start_date >= 1996-11-19 AND NOT ira_sep_simple AND sm_cost_in_plan > 0. "
                 "start < 1996-11-19 -> D_SM_001 (General Rule, no compute); start < 1987-01-01 -> D_SM_002; "
                 "ira_sep_simple -> D_SM_006 (Form 8606)."),
     "inputs": ["sm_annuity_start_date", "sm_cost_in_plan"], "outputs": [],
     "description": ("Decisions 3/4/7. The Simplified Method applies to periodic employer-plan annuities with a "
                     "basis; everything earlier or IRA-sourced RED-defers (no silent gap). Supersedes the "
                     "tts-tax-app D_RET_001 blank when these inputs are present.")},
    {"rule_id": "R-SM-TABLE", "title": "Lines 3 — expected number of payments (Table 1 / Table 2)",
     "rule_type": "calculation", "precedence": 2, "sort_order": 2,
     "formula": ("table = 2 if (sm_is_joint_survivor AND sm_annuity_start_date >= 1998-01-01) else 1. "
                 "Table 1 (single-life) lookup by sm_age_at_start: <=55->360, 56-60->310, 61-65->260, 66-70->210, "
                 ">=71->160. Table 2 lookup by (sm_age_at_start + sm_survivor_age_at_start): <=110->410, 111-120->360, "
                 "121-130->310, 131-140->260, >=141->210."),
     "inputs": ["sm_age_at_start", "sm_is_joint_survivor", "sm_survivor_age_at_start"],
     "outputs": ["sm_number_of_payments", "sm_table_used"],
     "description": "Pub 575 tables (verified). Table 2 requires sm_survivor_age_at_start (else D_SM_003)."},
    {"rule_id": "R-SM-PERPAYMENT", "title": "Line 4 — tax-free amount per payment",
     "rule_type": "calculation", "precedence": 3, "sort_order": 3,
     "formula": "sm_tax_free_per_payment = round(sm_cost_in_plan / sm_number_of_payments, 2).",
     "inputs": ["sm_cost_in_plan"], "outputs": ["sm_tax_free_per_payment"],
     "description": "Worksheet line 4 (line 2 / line 3). Carried to cents."},
    {"rule_id": "R-SM-TAXFREE", "title": "Lines 5-8 — tax-free this year, capped at cost remaining",
     "rule_type": "calculation", "precedence": 4, "sort_order": 4,
     "formula": ("line5 = sm_tax_free_per_payment * sm_months_paid_this_year; line7 = sm_cost_in_plan - "
                 "sm_prior_recovered_tax_free; sm_tax_free_this_year = min(line5, line7)."),
     "inputs": ["sm_months_paid_this_year", "sm_prior_recovered_tax_free", "sm_cost_in_plan"],
     "outputs": ["sm_tax_free_this_year"],
     "description": ("Worksheet lines 5/7/8. The post-1986 cost cap: cumulative tax-free can't exceed cost (line 8 "
                     "= smaller of line 5 or line 7). Always in scope here (pre-1987 RED-defers).")},
    {"rule_id": "R-SM-TAXABLE-5B", "title": "Line 9 — taxable amount -> Form 1040 line 5b",
     "rule_type": "calculation", "precedence": 5, "sort_order": 5,
     "formula": "sm_taxable = max(0, box1_gross - sm_tax_free_this_year) -> Form 1040 line 5b.",
     "inputs": [], "outputs": ["sm_taxable"],
     "description": ("Worksheet line 9 (not less than zero). The cross-form output: it supersedes the D_RET_001 "
                     "blanked 5b column. box1 is the 1099-R gross (R-RET pattern); rollover/QCD already reduce it "
                     "upstream.")},
    {"rule_id": "R-SM-CARRYOVER", "title": "Lines 10-11 — recovered-through-year + balance of cost (carryover)",
     "rule_type": "calculation", "precedence": 6, "sort_order": 6,
     "formula": ("sm_recovered_through_year = sm_prior_recovered_tax_free + sm_tax_free_this_year; "
                 "sm_balance_of_cost = sm_cost_in_plan - sm_recovered_through_year."),
     "inputs": ["sm_prior_recovered_tax_free", "sm_cost_in_plan"],
     "outputs": ["sm_recovered_through_year", "sm_balance_of_cost"],
     "description": ("Worksheet lines 10/11. line 10 is next year's line 6 (Decision 5 carryover). line 11 == 0 -> "
                     "fully recovered (D_SM_004 — next year fully taxable); a positive balance at death is the "
                     "Schedule A deduction (D_SM_005, note-defer).")},
]

SM_LINES: list[dict] = [
    {"line_number": "sm_1", "description": "1 Total pension/annuity payments (1099-R box 1) -> also 1040 line 5a", "line_type": "calculated"},
    {"line_number": "sm_2", "description": "2 Cost in the plan at the annuity starting date", "line_type": "input"},
    {"line_number": "sm_3", "description": "3 Expected number of monthly payments (Table 1 / Table 2)", "line_type": "calculated"},
    {"line_number": "sm_4", "description": "4 Tax-free amount per payment (line 2 / line 3)", "line_type": "calculated"},
    {"line_number": "sm_5", "description": "5 Tax-free candidate this year (line 4 x months received)", "line_type": "calculated"},
    {"line_number": "sm_6", "description": "6 Amount recovered tax free in prior years (after 1986)", "line_type": "input"},
    {"line_number": "sm_7", "description": "7 Cost remaining (line 2 - line 6)", "line_type": "calculated"},
    {"line_number": "sm_8", "description": "8 Tax-free amount this year (smaller of line 5 or line 7)", "line_type": "calculated"},
    {"line_number": "sm_9", "description": "9 Taxable amount (line 1 - line 8, not < 0) -> Form 1040 line 5b", "line_type": "total"},
    {"line_number": "sm_10", "description": "10 Amount recovered tax free through this year (line 6 + line 8)", "line_type": "calculated"},
    {"line_number": "sm_11", "description": "11 Balance of cost to be recovered (line 2 - line 10)", "line_type": "calculated"},
]

SM_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_SM_001", "title": "Annuity starting date before Nov 19, 1996 — General Rule (not supported)", "severity": "error",
     "condition": "sm_annuity_start_date < 1996-11-19",
     "message": ("Not supported — prepare manually: this annuity started before November 19, 1996, so the taxable "
                 "amount is figured under the General Rule (or the pre-1997 single-life Simplified Method), which "
                 "this software does not compute. Use Pub. 939 / the worksheet in the form instructions."),
     "notes": "Decision 3. The in-scope boundary; the live D_RET_001 still owns it (no silent gap)."},
    {"diagnostic_id": "D_SM_002", "title": "Annuity starting date before 1987 — uncapped recovery (not supported)", "severity": "error",
     "condition": "sm_annuity_start_date < 1987-01-01",
     "message": ("Not supported — prepare manually: annuities that started before 1987 recover cost without the "
                 "total-cost cap and have no death deduction (a different regime). Compute the taxable amount "
                 "manually."),
     "notes": "Decision 4. A subset of D_SM_001's range; kept explicit for the no-silent-gap enumeration."},
    {"diagnostic_id": "D_SM_003", "title": "Joint-and-survivor annuity without the survivor's age", "severity": "error",
     "condition": "sm_is_joint_survivor is True AND sm_annuity_start_date >= 1998-01-01 AND sm_survivor_age_at_start is None",
     "message": ("Enter the survivor annuitant's age at the annuity starting date — Table 2 (joint and survivor) "
                 "uses the COMBINED ages of both annuitants. Without it the number of payments can't be looked up."),
     "notes": "Table 2 needs the combined age; a missing survivor age blanks the computation."},
    {"diagnostic_id": "D_SM_004", "title": "Cost fully recovered — next year fully taxable", "severity": "info",
     "condition": "sm_balance_of_cost == 0",
     "message": ("The cost (basis) in this annuity is now fully recovered (balance of cost = 0). Beginning next "
                 "year, the entire payment is taxable — you won't complete this worksheet."),
     "notes": "Worksheet line 11 == 0."},
    {"diagnostic_id": "D_SM_005", "title": "Unrecovered cost at a total distribution — possible final-return deduction", "severity": "info",
     "condition": "sm_balance_of_cost > 0 AND total_distribution (box 2b) is True",
     "message": ("A balance of cost remains unrecovered on a total distribution. If the annuitant has died, the "
                 "unrecovered cost is an itemized deduction on the decedent's final return (Schedule A — not "
                 "computed here; NEXT-UP topic)."),
     "notes": "Decision 6: the death unrecovered-basis deduction note-defers to Schedule A."},
    {"diagnostic_id": "D_SM_006", "title": "IRA/SEP/SIMPLE distribution — Simplified Method not applicable", "severity": "error",
     "condition": "ira_sep_simple is True (box 7 IRA/SEP/SIMPLE checked)",
     "message": ("The Simplified Method is for employer-plan annuities, not IRAs. A traditional-IRA distribution "
                 "with basis is figured on Form 8606 (not built). Prepare manually."),
     "notes": "Decision 7. IRA basis is Form 8606 territory."},
]

SM_SCENARIOS: list[dict] = [
    {"scenario_name": "SM-T1 — single-life, age 66, post-1996", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "sm_annuity_start_date": "2010-01-01", "sm_age_at_start": 66,
                "sm_is_joint_survivor": False, "sm_cost_in_plan": 42000, "sm_prior_recovered_tax_free": 0,
                "sm_months_paid_this_year": 12, "box1_gross": 24000, "ira_sep_simple": False},
     "expected_outputs": {"sm_table_used": 1, "sm_number_of_payments": 210, "sm_tax_free_per_payment": 200.00,
                          "sm_tax_free_this_year": 2400.00, "sm_taxable": 21600.00,
                          "sm_recovered_through_year": 2400.00, "sm_balance_of_cost": 39600.00},
     "notes": "Table 1 age 66 -> 210; 42,000/210 = 200.00/payment x 12 = 2,400 tax free; 24,000 - 2,400 = 21,600 -> 5b."},
    {"scenario_name": "SM-T2 — joint & survivor, combined age 130, post-1997", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"tax_year": 2025, "sm_annuity_start_date": "2012-01-01", "sm_age_at_start": 66,
                "sm_is_joint_survivor": True, "sm_survivor_age_at_start": 64, "sm_cost_in_plan": 62000,
                "sm_prior_recovered_tax_free": 0, "sm_months_paid_this_year": 12, "box1_gross": 30000,
                "ira_sep_simple": False},
     "expected_outputs": {"sm_table_used": 2, "sm_number_of_payments": 310, "sm_tax_free_per_payment": 200.00,
                          "sm_tax_free_this_year": 2400.00, "sm_taxable": 27600.00, "sm_balance_of_cost": 59600.00},
     "notes": "Table 2 combined 130 -> 310; 62,000/310 = 200.00; 30,000 - 2,400 = 27,600 -> 5b."},
    {"scenario_name": "SM-T3 — cost cap binds (final year)", "scenario_type": "edge_case", "sort_order": 3,
     "inputs": {"tax_year": 2025, "sm_annuity_start_date": "2008-01-01", "sm_age_at_start": 66,
                "sm_is_joint_survivor": False, "sm_cost_in_plan": 12600, "sm_prior_recovered_tax_free": 12200,
                "sm_months_paid_this_year": 12, "box1_gross": 5000, "ira_sep_simple": False},
     "expected_outputs": {"sm_number_of_payments": 210, "sm_tax_free_per_payment": 60.00,
                          "sm_tax_free_this_year": 400.00, "sm_taxable": 4600.00,
                          "sm_recovered_through_year": 12600.00, "sm_balance_of_cost": 0.00, "D_SM_004": True},
     "notes": "line5 = 60x12 = 720 but line7 = 12,600-12,200 = 400 caps it; balance 0 -> D_SM_004."},
    {"scenario_name": "SM-T4 — partial first year (7 months), age 71", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"tax_year": 2025, "sm_annuity_start_date": "2025-06-01", "sm_age_at_start": 71,
                "sm_is_joint_survivor": False, "sm_cost_in_plan": 16000, "sm_prior_recovered_tax_free": 0,
                "sm_months_paid_this_year": 7, "box1_gross": 3000, "ira_sep_simple": False},
     "expected_outputs": {"sm_number_of_payments": 160, "sm_tax_free_per_payment": 100.00,
                          "sm_tax_free_this_year": 700.00, "sm_taxable": 2300.00, "sm_balance_of_cost": 15300.00},
     "notes": "Table 1 age 71 -> 160; 16,000/160 = 100.00 x 7 months = 700; 3,000 - 700 = 2,300 -> 5b."},
    {"scenario_name": "SM-G1 — pre-1996 start fires D_SM_001", "scenario_type": "diagnostic", "sort_order": 5,
     "inputs": {"tax_year": 2025, "sm_annuity_start_date": "1995-06-01", "sm_age_at_start": 66,
                "sm_cost_in_plan": 30000, "ira_sep_simple": False},
     "expected_outputs": {"D_SM_001": True},
     "notes": "Before Nov 19, 1996 -> General Rule, RED-defer (no compute)."},
    {"scenario_name": "SM-G2 — joint without survivor age fires D_SM_003", "scenario_type": "diagnostic", "sort_order": 6,
     "inputs": {"tax_year": 2025, "sm_annuity_start_date": "2005-01-01", "sm_age_at_start": 66,
                "sm_is_joint_survivor": True, "sm_survivor_age_at_start": None, "sm_cost_in_plan": 40000,
                "ira_sep_simple": False},
     "expected_outputs": {"D_SM_003": True},
     "notes": "Table 2 needs the combined age."},
    {"scenario_name": "SM-G3 — IRA box fires D_SM_006", "scenario_type": "diagnostic", "sort_order": 7,
     "inputs": {"tax_year": 2025, "sm_annuity_start_date": "2010-01-01", "sm_age_at_start": 66,
                "sm_cost_in_plan": 30000, "ira_sep_simple": True},
     "expected_outputs": {"D_SM_006": True},
     "notes": "IRA basis -> Form 8606, RED-defer."},
]

SM_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-SM-SCOPE", "IRS_2025_PUB575", "primary", "Annuity-starting-date boundaries (Nov 19 1996 / 1987) + non-IRA scope"),
    ("R-SM-SCOPE", "IRS_2025_1040_SMW", "secondary", "Who must use the Simplified Method"),
    ("R-SM-TABLE", "IRS_2025_PUB575", "primary", "Table 1 (single) / Table 2 (joint, combined age) — number of payments"),
    ("R-SM-PERPAYMENT", "IRS_2025_1040_SMW", "primary", "Worksheet line 4: cost / number of payments"),
    ("R-SM-TAXFREE", "IRS_2025_1040_SMW", "primary", "Worksheet lines 5/7/8 — the cost cap (smaller of)"),
    ("R-SM-TAXFREE", "IRS_2025_PUB575", "secondary", "Post-1986 cost cap (recovery can't exceed cost)"),
    ("R-SM-TAXABLE-5B", "IRS_2025_1040_SMW", "primary", "Worksheet line 9 -> Form 1040 line 5b"),
    ("R-SM-CARRYOVER", "IRS_2025_1040_SMW", "primary", "Worksheet lines 10/11 — recovered-through-year + balance"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-SM-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Number of payments (Table 1/2) + tax-free per payment = cost / number",
     "description": ("Validates R-SM-TABLE/R-SM-PERPAYMENT. Table 1 by age, Table 2 by combined age (joint + after "
                     "1997). Bug it catches: the wrong table (single vs joint), or per-payment not = cost/number."),
     "definition": {"kind": "formula_check", "form": "SIMPLIFIED_METHOD",
                    "formula": "sm_number_of_payments == table_lookup(table_used, age); sm_tax_free_per_payment == round(sm_cost_in_plan / sm_number_of_payments, 2)"},
     "sort_order": 1},
    {"assertion_id": "FA-1040-SM-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Cost cap: tax-free this year = min(per-payment x months, cost - prior recovered)",
     "description": ("Validates R-SM-TAXFREE. The post-1986 cap (line 8 = smaller of line 5 or line 7). Bug it "
                     "catches: recovery exceeding cost (SM-T3 caps at 400, not 720)."),
     "definition": {"kind": "formula_check", "form": "SIMPLIFIED_METHOD",
                    "formula": "sm_tax_free_this_year == min(sm_tax_free_per_payment * sm_months_paid_this_year, sm_cost_in_plan - sm_prior_recovered_tax_free)"},
     "sort_order": 2},
    {"assertion_id": "FA-1040-SM-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Taxable = max(0, box1 - tax-free this year) -> Form 1040 line 5b (supersedes D_RET_001)",
     "description": ("Validates R-SM-TAXABLE-5B. The cross-form output replaces the box-2a-blank blank. Bug it "
                     "catches: a negative taxable, or the result not landing on 5b."),
     "definition": {"kind": "flow_assertion", "form": "SIMPLIFIED_METHOD",
                    "checks": [{"source_line": "sm_9", "must_write_to": ["1040.5b"]}]},
     "sort_order": 3},
    {"assertion_id": "FA-1040-SM-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Carryover identity: recovered-through-year + balance-of-cost == cost",
     "description": ("Validates R-SM-CARRYOVER. line 10 (next year's line 6) + line 11 == line 2. Bug it catches: a "
                     "carryover that doesn't conserve cost (would drift the basis year over year)."),
     "definition": {"kind": "formula_check", "form": "SIMPLIFIED_METHOD",
                    "formula": "sm_recovered_through_year + sm_balance_of_cost == sm_cost_in_plan"},
     "sort_order": 4},
    {"assertion_id": "FA-1040-SM-05", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "Table 1 / Table 2 number-of-payments == Pub 575 verbatim",
     "description": ("Pins both tables (Table 1 single-life by age; Table 2 joint-survivor by combined age) to the "
                     "verified Pub 575 (2025) values. Bug it catches: a transcribed table cell drifting."),
     "definition": {"kind": "constants_check", "form": "SIMPLIFIED_METHOD",
                    "constants": {"table_1": {"55": 360, "60": 310, "65": 260, "70": 210, "71+": 160},
                                  "table_2": {"110": 410, "120": 360, "130": 310, "140": 260, "141+": 210}}},
     "sort_order": 5},
    {"assertion_id": "FA-1040-SM-06", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "RED-defers each leave a RED (no silent gap)",
     "description": ("Pre-Nov-19-1996 (D_SM_001), pre-1987 (D_SM_002), joint-without-survivor-age (D_SM_003), and "
                     "IRA box (D_SM_006) each fire rather than silently computing a wrong number."),
     "definition": {"kind": "gating_check", "form": "SIMPLIFIED_METHOD", "expect": {"red_fires": True},
                    "blockers": ["pre_1996_start", "pre_1987_start", "joint_no_survivor_age", "ira_box"]},
     "sort_order": 6},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORMS registry
# ═══════════════════════════════════════════════════════════════════════════

FORMS: list[dict] = [
    {"identity": SM_IDENTITY, "facts": SM_FACTS, "rules": SM_RULES, "lines": SM_LINES,
     "diagnostics": SM_DIAGNOSTICS, "scenarios": SM_SCENARIOS, "rule_links": SM_RULE_LINKS},
]


class Command(BaseCommand):
    help = "Load the SIMPLIFIED_METHOD spec (NEXT-UP #1). Refuses to seed until READY_TO_SEED=True."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()

        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad SIMPLIFIED_METHOD spec (NEXT-UP #1)\n"))

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

    # ── Safety guard ──────────────────────────────────────────────────────

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
                "\nREFUSING TO SEED SIMPLIFIED_METHOD: not cleared to seed.\n\n"
                "Content is authored, but seeding is gated until Ken's review walk:\n"
                "  - the two payments tables (Pub 575-verified) + the boundary dates\n"
                "  - the reconstructed 11-line worksheet (requires_human_review — re-check\n"
                "    against the 2025 i1040 Simplified Method Worksheet)\n"
                "  - the RED-defer enumeration (D_SM_001..006) + the D_RET_001 supersession\n"
                "  - the 7 scope decisions in the tts-tax-app source brief\n\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True to proceed)\n\n"
                f"Currently empty / placeholder:\n  {still_empty}\n\n"
                "To proceed: review the module-level data lists + run\n"
                "check_simplified_method_integrity.py, then set READY_TO_SEED = True."
            )

    # ── Topics / sources ─────────────────────────────────────────────────

    def _load_topics(self):
        ct = 0
        for code, name in AUTHORITY_TOPICS:
            _, created = AuthorityTopic.objects.update_or_create(
                topic_code=code, defaults={"topic_name": name},
            )
            ct += 1 if created else 0
        self.stdout.write(f"Topics: {ct} new ({len(AUTHORITY_TOPICS)} in batch)")

    def _load_sources(self) -> dict:
        sources: dict = {}
        for src_data in AUTHORITY_SOURCES:
            src_data = dict(src_data)
            excerpts_data = src_data.pop("excerpts", [])
            topic_codes = src_data.pop("topics", [])
            source, _ = AuthoritySource.objects.update_or_create(
                source_code=src_data["source_code"], defaults=src_data,
            )
            sources[source.source_code] = source
            for exc in excerpts_data:
                exc = dict(exc)
                AuthorityExcerpt.objects.update_or_create(
                    authority_source=source, excerpt_label=exc["excerpt_label"], defaults=exc,
                )
            for tc in topic_codes:
                topic = AuthorityTopic.objects.filter(topic_code=tc).first()
                if topic:
                    AuthoritySourceTopic.objects.get_or_create(
                        authority_source=source, authority_topic=topic,
                    )
        for code in EXISTING_SOURCES_TO_REFERENCE:
            src = AuthoritySource.objects.filter(source_code=code).first()
            if src:
                sources[code] = src
        self.stdout.write(f"Sources ready: {len(sources)}")
        return sources

    def _load_new_excerpts_on_existing(self, sources):
        for code, exc in NEW_EXCERPTS_ON_EXISTING:
            src = sources.get(code) or AuthoritySource.objects.filter(source_code=code).first()
            if not src:
                continue
            exc = dict(exc)
            AuthorityExcerpt.objects.update_or_create(
                authority_source=src, excerpt_label=exc["excerpt_label"], defaults=exc,
            )

    # ── Per-form helpers ─────────────────────────────────────────────────

    def _upsert_form(self, identity: dict) -> TaxForm:
        form, created = TaxForm.objects.update_or_create(
            form_number=identity["form_number"], jurisdiction=FORM_JURISDICTION,
            tax_year=FORM_TAX_YEAR, version=FORM_VERSION,
            defaults={"form_title": identity["form_title"], "entity_types": FORM_ENTITY_TYPES,
                      "status": FORM_STATUS, "notes": identity["notes"]},
        )
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
                    defaults={"support_level": level, "relevance_note": note},
                )
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
                    defaults={"note": f"{source_code} -> {form_code}"},
                )

    def _load_flow_assertions(self):
        for a in FLOW_ASSERTIONS:
            a = dict(a)
            FlowAssertion.objects.update_or_create(assertion_id=a.pop("assertion_id"), defaults=a)
        self.stdout.write(f"  {len(FLOW_ASSERTIONS)} flow assertions")

    def _report_totals(self):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("DATABASE TOTALS (after load_1040_simplified_method)")
        self.stdout.write("=" * 60)
        self.stdout.write(f"TaxForms:        {TaxForm.objects.count()}")
        self.stdout.write(f"FlowAssertions:  {FlowAssertion.objects.count()}")
        form = TaxForm.objects.filter(form_number="SIMPLIFIED_METHOD").first()
        if form:
            uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
            if uncited:
                self.stdout.write(self.style.WARNING(f"SIMPLIFIED_METHOD rules with ZERO authority links: {len(uncited)}"))
            else:
                self.stdout.write("SIMPLIFIED_METHOD: all rules cited")
