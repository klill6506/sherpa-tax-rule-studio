"""Load the FORM_8889 spec — Health Savings Accounts (§223).

Phase 2 (post-sprint), the first common-form build. Form 8889 computes the HSA
DEDUCTION (Part I → Schedule 1 line 13, above-the-line), the TAXABLE HSA
DISTRIBUTION (Part II → Schedule 1 line 8f) + the 20% additional tax (→ Schedule
2 line 17c), and the last-month-rule TESTING-PERIOD FAILURE income (Part III →
Schedule 1 line 8f) + the 10% additional tax (→ Schedule 2 line 17d). One Form
8889 per HSA owner (taxpayer + spouse each file their own).

KEN'S 4 SCOPE DECISIONS (2026-06-14, AskUserQuestion):
  (1) DEDICATED HSA sub-model, one row per OWNER (built in the tts-tax-app seed
      leg) — coverage, own + employer (W-2 box-W) contributions, 1099-SA
      distributions, qualified medical expenses, eligible months / last-month
      flag, the 55+/Medicare flags, the distribution-exception checkbox.
  (2) FULL Part I + II + III. RED-defer: the 6% excess-contribution excise (→
      Form 5329 Part VII), the once-in-lifetime IRA→HSA funding distribution
      (line 10/19), and non-spouse death-of-beneficiary.
  (3) COMPUTE the line-3 monthly proration + the last-month rule.
  (4) TY2025 (verified) + TY2026 (verified limits; re-verify the 2026 form line
      numbers when the final 2026 form posts).

CONSTANTS VERIFIED 2026-06-14 from Form 8889 / i8889 / Pub 969 / Rev. Proc.
2024-25 §2.01 (2025) + Rev. Proc. 2025-19 §2.01 (2026) (brief tts-tax-app
server/specs/_form_8889_source_brief.md):
  - Annual limit self-only / family: 2025 $4,300 / $8,550; 2026 $4,400 / $8,750.
  - 55+ catch-up $1,000 (STATUTORY, not indexed; both years; in the owner's OWN HSA).
  - Flow: line 13 → Sch 1 L13; line 16 + line 20 → Sch 1 L8f; line 17b (20%) →
    Sch 2 L17c; line 21 (10%) → Sch 2 L17d.

Single form, the load_1040_state_refund precedent.

SAFETY GUARD: READY_TO_SEED stays False until Ken's review walk (the §223 limits
+ the proration + the last-month rule + the deduction/distribution/Part-III math).
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


READY_TO_SEED = True  # FLIPPED 2026-06-14 — Ken approved the review walk ("Looks right.").


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_ENTITY_TYPES = ["1040"]
FORM_STATUS = "draft"


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS (§223; the integrity gate re-types) — year-keyed
# ═══════════════════════════════════════════════════════════════════════════

HSA_LIMIT = {
    2025: {"self": 4300, "family": 8550},
    2026: {"self": 4400, "family": 8750},
}
CATCH_UP = 1000          # 55+, statutory (not indexed), both years
DIST_TAX = 0.20          # 20% additional tax on non-qualified distributions
TESTING_TAX = 0.10       # 10% additional tax on a testing-period failure


def annual_limit(year, coverage) -> int:
    table = HSA_LIMIT.get(year, HSA_LIMIT[2025])
    return table["family" if coverage == "family" else "self"]


def _prorate(amount, eligible_months, last_month_rule) -> int:
    """The last-month rule (eligible Dec 1) → the FULL amount; else the monthly
    proration = round(amount × eligible months ÷ 12)."""
    if last_month_rule:
        return amount
    m = max(0, min(12, int(eligible_months)))
    return round(amount * m / 12)


def line3_limit(year, coverage, eligible_months, last_month_rule) -> int:
    return _prorate(annual_limit(year, coverage), eligible_months, last_month_rule)


def catch_up(age_55, eligible_months, last_month_rule) -> int:
    return _prorate(CATCH_UP, eligible_months, last_month_rule) if age_55 else 0


def hsa_deduction(year, coverage, eligible_months, last_month_rule, own_contrib,
                  employer_contrib, age_55, family_alloc=None) -> int:
    """Part I lines 3-13 — the HSA deduction = min(own contributions (line 2), the
    limit after employer contributions (line 12))."""
    line3 = line3_limit(year, coverage, eligible_months, last_month_rule)
    line6 = family_alloc if family_alloc is not None else line3   # the married family split
    line7 = catch_up(age_55, eligible_months, last_month_rule)
    line8 = line6 + line7
    line12 = max(0, line8 - employer_contrib)                     # line 11 = employer (+ line 10 = 0)
    return min(own_contrib, line12)


def taxable_distribution(total_dist, rollovers, qualified_medical) -> int:
    """Part II line 16 — the taxable HSA distribution = max(0, (distributions −
    rollovers) − qualified medical expenses)."""
    line14c = max(0, total_dist - rollovers)
    return max(0, line14c - qualified_medical)


def dist_addl_tax(taxable_dist, exception) -> int:
    """Line 17b — the 20% additional tax (0 when an age-65/death/disability
    exception applies; the amount stays taxable income)."""
    return 0 if exception else round(taxable_dist * DIST_TAX)


def testing_failure_tax(failure_amount) -> int:
    """Line 21 — the 10% additional tax on the Part III testing-period failure."""
    return round(failure_amount * TESTING_TAX)


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("health_savings_account", "Health Savings Accounts (§223) — Form 8889; HSA deduction → Sch 1 L13 / taxable distributions → Sch 1 L8f / 20%-10% tax → Sch 2 L17c-d"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_1040_FORM",
    "IRS_2025_1040_INSTR",
]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_F8889_INSTR",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Form 8889 — Health Savings Accounts (HSAs)",
        "citation": "Instructions for Form 8889 (2025); i8889; Form 8889 Attachment Sequence No. 52; Rev. Proc. 2024-25 / 2025-19 §2.01 limits",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i8889.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": "Part I deduction + the Line-3 Limitation Chart & Worksheet (proration) + the last-month rule + the married split; Part II distributions + the 20% tax; Part III testing-period failure + the 10% tax. REQUIRES HUMAN REVIEW: re-verify the 2026 Form 8889 line numbers when the final 2026 form posts (the limits are locked via Rev. Proc. 2025-19).",
        "topics": ["health_savings_account"],
        "excerpts": [
            {
                "excerpt_label": "§223 limits + the catch-up (2025/2026)",
                "location_reference": "i8889 (2025), line 3 + Rev. Proc. 2024-25/2025-19 §2.01",
                "excerpt_text": (
                    "The 2025 HSA contribution limit is $4,300 for self-only HDHP coverage and $8,550 for "
                    "family coverage; for 2026, $4,400 and $8,750. If you are age 55 or older at the end of "
                    "the year, your limit is increased by $1,000 (the additional contribution amount). The "
                    "last-month rule: if you are an eligible individual on the first day of the last month of "
                    "your tax year (December 1), you are treated as an eligible individual for the entire "
                    "year and may contribute the full annual limit."
                ),
                "summary_text": "2025 $4,300/$8,550; 2026 $4,400/$8,750; +$1,000 at 55+; the last-month rule grants the full limit.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "The deduction + employer contributions (lines 9-13)",
                "location_reference": "i8889 (2025), lines 2/9/12/13",
                "excerpt_text": (
                    "Line 9: employer contributions (and any amount your employer contributed through a "
                    "cafeteria plan) are shown on your W-2 in box 12 with code W. Line 12: subtract line 11 "
                    "(employer contributions) from line 8. Line 13: your HSA deduction is the smaller of line "
                    "2 (the contributions you made) or line 12 — enter it on Schedule 1 (Form 1040), line 13. "
                    "Caution: if line 2 is more than line 13, you may have excess contributions."
                ),
                "summary_text": "Deduction = min(your contributions, line 12 = limit − employer); → Schedule 1 line 13.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Distributions + the 20% / Part III + the 10% (lines 16-21)",
                "location_reference": "i8889 (2025), lines 16/17b/20/21",
                "excerpt_text": (
                    "Line 16: the taxable HSA distribution (distributions minus the unreimbursed qualified "
                    "medical expenses on line 15) is included on Schedule 1 (Form 1040), line 8f. Line 17b: an "
                    "additional 20% tax applies unless the distribution was made after death, disability, or "
                    "age 65 — enter it on Schedule 2 (Form 1040), line 17c. Part III: if you fail the testing "
                    "period for the last-month rule, include the amount on line 20 (Schedule 1, line 8f) and "
                    "pay an additional 10% tax on line 21 (Schedule 2, line 17d)."
                ),
                "summary_text": "Taxable dist (L16) + Part III (L20) → Sch 1 L8f; 20% (L17b) → Sch 2 L17c; 10% (L21) → Sch 2 L17d.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_223",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §223 — Health Savings Accounts",
        "citation": "26 U.S.C. §223 (§223(b) the contribution limits + the catch-up + the last-month rule; §223(f) distributions + the 20% additional tax)",
        "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:223%20edition:prelim)",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "§223(b)(2) the self-only/family limits; §223(b)(3) the $1,000 catch-up; §223(b)(8) the last-month rule + the testing period; §223(f)(4) the 20% additional tax on non-qualified distributions (exceptions: death/disability/age 65).",
        "topics": ["health_savings_account"],
        "excerpts": [
            {
                "excerpt_label": "§223(b)(8) the last-month rule + testing period",
                "location_reference": "26 U.S.C. §223(b)(8)",
                "excerpt_text": (
                    "§223(b)(8)(A): an individual who is an eligible individual during the last month of the "
                    "taxable year is treated as having been an eligible individual during every month of the "
                    "taxable year. §223(b)(8)(B): if the individual is not an eligible individual at all times "
                    "during the testing period (the period beginning with the last month of the taxable year "
                    "and ending on the last day of the 12th month following such month), the amount allowed "
                    "only by reason of the rule is included in gross income, plus an additional 10% tax "
                    "(except by reason of death or disability)."
                ),
                "summary_text": "§223(b)(8): eligible in the last month → full year; fail the testing period → income + 10% tax.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_PUB_969",
        "source_type": "official_guidance",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRS Publication 969 — HSAs and Other Tax-Favored Health Plans",
        "citation": "Pub. 969 (2025) — Health Savings Accounts (the limit worksheet, the married split, the testing period, Medicare, excess contributions)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/p969.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": False,
        "trust_score": 9.00,
        "requires_human_review": True,
        "notes": "The Line-3 Limitation Chart & Worksheet (monthly proration), the married family-coverage split (line 6, default 50/50), the Medicare-enrollment zeroing, and the 6% excess-contribution excise (Form 5329 Part VII — RED-deferred). REQUIRES HUMAN REVIEW: confirm the proration worksheet + the split default.",
        "topics": ["health_savings_account"],
        "excerpts": [
            {
                "excerpt_label": "The married family split + the monthly proration",
                "location_reference": "Pub. 969 (2025), 'Contribution limit' + the Line 3 Limitation Chart",
                "excerpt_text": (
                    "If either spouse has family HDHP coverage, both spouses are treated as having family "
                    "coverage and the family contribution limit is divided equally between them unless they "
                    "agree on a different division. The $1,000 additional (catch-up) amount is not divided — "
                    "each spouse who is 55 or older must make the catch-up contribution to their own HSA. If "
                    "you are not an eligible individual for the entire year and do not use the last-month "
                    "rule, figure the limit as the sum of the monthly contribution limits for the months you "
                    "were an eligible individual (eligibility determined on the first day of each month)."
                ),
                "summary_text": "Family split 50/50 (catch-up NOT shared); proration = Σ monthly limits over eligible months.",
                "is_key_excerpt": True,
            },
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_F8889_INSTR", "FORM_8889", "governs"),
    ("IRC_223", "FORM_8889", "governs"),
    ("IRS_PUB_969", "FORM_8889", "informs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM: FORM_8889
# ═══════════════════════════════════════════════════════════════════════════

F8889_IDENTITY = {
    "form_number": "FORM_8889",
    "form_title": "Form 8889 — Health Savings Accounts (HSAs) (TY2025)",
    "notes": (
        "Ken's 4 scope decisions 2026-06-14 (Phase 2). Real IRS face, ONE per HSA "
        "owner (taxpayer/spouse). Part I: coverage → the §223 limit (line 3, with "
        "the monthly proration + the last-month rule) + the married family split "
        "(line 6) + the $1,000 catch-up (line 7) − employer contributions (line 9, "
        "W-2 box-W) → the HSA deduction (line 13 = min(own, limit) → Schedule 1 "
        "line 13). Part II: distributions − qualified medical = the taxable amount "
        "(line 16 → Schedule 1 line 8f) + the 20% additional tax (line 17b → "
        "Schedule 2 line 17c, with the age-65/death/disability exception). Part III: "
        "the last-month-rule testing-period failure income (line 20 → Schedule 1 "
        "line 8f) + the 10% additional tax (line 21 → Schedule 2 line 17d). "
        "RED-deferred: the 6% excess excise (5329 Part VII), the IRA→HSA funding "
        "distribution, non-spouse death. TY2025 + TY2026."
    ),
}

F8889_FACTS: list[dict] = [
    # ── Inputs (per owner; ride the HSA sub-model in tts-tax-app) ──
    {"fact_key": "hsa_owner", "label": "HSA owner (taxpayer / spouse)",
     "data_type": "string", "default_value": "taxpayer", "sort_order": 1, "notes": "One Form 8889 per owner."},
    {"fact_key": "hsa_coverage_type", "label": "Line 1 — HDHP coverage (self-only / family)",
     "data_type": "string", "default_value": "self", "sort_order": 2, "notes": "self / family."},
    {"fact_key": "hsa_own_contributions", "label": "Line 2 — your own (non-employer) HSA contributions",
     "data_type": "decimal", "default_value": "0", "sort_order": 3, "notes": "Capped by line 12 → the deduction."},
    {"fact_key": "hsa_employer_contributions", "label": "Line 9 — employer contributions (W-2 box 12 code W)",
     "data_type": "decimal", "default_value": "0", "sort_order": 4, "notes": "Reduces the deductible amount."},
    {"fact_key": "hsa_eligible_months", "label": "Eligible months (line-3 proration)",
     "data_type": "integer", "default_value": "12", "sort_order": 5, "notes": "0-12; first-of-month test. Ignored under the last-month rule."},
    {"fact_key": "hsa_last_month_rule", "label": "Last-month rule (eligible on Dec 1)?",
     "data_type": "boolean", "default_value": "false", "sort_order": 6, "notes": "Full annual limit regardless of months."},
    {"fact_key": "hsa_age_55_catchup", "label": "Age 55+ (the $1,000 catch-up)?",
     "data_type": "boolean", "default_value": "false", "sort_order": 7, "notes": "In the owner's OWN HSA; prorated when not all year."},
    {"fact_key": "hsa_family_allocation", "label": "Line 6 — allocated family-limit share (MFJ family)",
     "data_type": "decimal", "default_value": "0", "sort_order": 8, "notes": "The married split; blank = the full line-3 limit."},
    {"fact_key": "hsa_distribution_total", "label": "Line 14a — total distributions (1099-SA box 1)",
     "data_type": "decimal", "default_value": "0", "sort_order": 9, "notes": "Part II."},
    {"fact_key": "hsa_rollovers", "label": "Line 14b — rollovers + timely-withdrawn excess",
     "data_type": "decimal", "default_value": "0", "sort_order": 10, "notes": "Non-taxable."},
    {"fact_key": "hsa_qualified_medical", "label": "Line 15 — unreimbursed qualified medical expenses",
     "data_type": "decimal", "default_value": "0", "sort_order": 11, "notes": "No double-dip with Schedule A."},
    {"fact_key": "hsa_dist_exception", "label": "Line 17a — death / disability / age 65 exception?",
     "data_type": "boolean", "default_value": "false", "sort_order": 12, "notes": "Exempts the 20% (still taxable income)."},
    {"fact_key": "hsa_testing_failure", "label": "Line 18 — testing-period failure income",
     "data_type": "decimal", "default_value": "0", "sort_order": 13, "notes": "Part III; the cross-year failure amount."},
    # ── Outputs ──
    {"fact_key": "hsa_deduction", "label": "Line 13 — HSA deduction → Schedule 1 line 13",
     "data_type": "decimal", "sort_order": 30, "notes": "OUTPUT. min(line 2, line 12)."},
    {"fact_key": "hsa_taxable_dist", "label": "Line 16 — taxable distribution → Schedule 1 line 8f",
     "data_type": "decimal", "sort_order": 31, "notes": "OUTPUT. max(0, 14c − 15)."},
    {"fact_key": "hsa_addl_tax_20", "label": "Line 17b — 20% additional tax → Schedule 2 line 17c",
     "data_type": "decimal", "sort_order": 32, "notes": "OUTPUT. 20% × taxable (0 if exception)."},
    {"fact_key": "hsa_testing_income", "label": "Line 20 — testing-period income → Schedule 1 line 8f",
     "data_type": "decimal", "sort_order": 33, "notes": "OUTPUT. Part III income."},
    {"fact_key": "hsa_addl_tax_10", "label": "Line 21 — 10% additional tax → Schedule 2 line 17d",
     "data_type": "decimal", "sort_order": 34, "notes": "OUTPUT. 10% × line 20."},
]

F8889_RULES: list[dict] = [
    {"rule_id": "R-8889-LIMIT", "title": "Line 3 — the §223 limit (proration + last-month rule)", "rule_type": "calculation",
     "precedence": 1, "sort_order": 1,
     "formula": ("line 3 = annual limit (self $4,300 / family $8,550 for 2025; $4,400 / $8,750 for 2026). "
                 "If the last-month rule applies (eligible Dec 1) → the FULL annual limit; else round(limit × "
                 "eligible months ÷ 12)."),
     "inputs": ["hsa_coverage_type", "hsa_eligible_months", "hsa_last_month_rule"], "outputs": [],
     "description": "§223(b)(2), (b)(8). Decision 3 — the proration + the last-month rule."},
    {"rule_id": "R-8889-FAMILY", "title": "Lines 6-8 — the married split + the catch-up", "rule_type": "calculation",
     "precedence": 2, "sort_order": 2,
     "formula": ("line 6 = the allocated family-limit share (MFJ family; default ½ of line 5, any agreed "
                 "split) else line 5 (= line 3); line 7 = the $1,000 catch-up (55+, prorated, in the owner's "
                 "OWN HSA, NOT split); line 8 = line 6 + line 7."),
     "inputs": ["hsa_family_allocation", "hsa_age_55_catchup"], "outputs": [],
     "description": "§223(b)(3), (b)(5). Pub 969 split (catch-up not shared)."},
    {"rule_id": "R-8889-DEDUCTION", "title": "Lines 9-13 — the HSA deduction → Sch 1 line 13", "rule_type": "calculation",
     "precedence": 3, "sort_order": 3,
     "formula": ("line 9 = employer contributions (W-2 box 12 code W); line 12 = max(0, line 8 − line 9); "
                 "line 13 = min(line 2 (your own contributions), line 12) → Schedule 1 line 13 (an above-the-"
                 "line adjustment). Employer contributions are pre-tax, so they reduce the deduction."),
     "inputs": ["hsa_own_contributions", "hsa_employer_contributions"], "outputs": ["hsa_deduction"],
     "description": "§223(a). Decision 2. The deduction is min(own, the limit after employer)."},
    {"rule_id": "R-8889-DISTRIB", "title": "Lines 14-17b — distributions + the 20% tax", "rule_type": "calculation",
     "precedence": 4, "sort_order": 4,
     "formula": ("line 14c = max(0, distributions − rollovers); line 16 (taxable) = max(0, line 14c − the "
                 "qualified medical expenses on line 15) → Schedule 1 line 8f; line 17b = 20% × line 16 → "
                 "Schedule 2 line 17c, UNLESS the death/disability/age-65 exception (line 17a) applies."),
     "inputs": ["hsa_distribution_total", "hsa_rollovers", "hsa_qualified_medical", "hsa_dist_exception"],
     "outputs": ["hsa_taxable_dist", "hsa_addl_tax_20"],
     "description": "§223(f)(2), (f)(4). The taxable distribution + the 20% additional tax."},
    {"rule_id": "R-8889-TESTING", "title": "Lines 18-21 — the testing-period failure + the 10% tax", "rule_type": "calculation",
     "precedence": 5, "sort_order": 5,
     "formula": ("Part III: line 20 = the last-month-rule testing-period failure income (line 18) + the "
                 "funding-distribution failure (line 19, RED-deferred) → Schedule 1 line 8f; line 21 = 10% × "
                 "line 20 → Schedule 2 line 17d."),
     "inputs": ["hsa_testing_failure"], "outputs": ["hsa_testing_income", "hsa_addl_tax_10"],
     "description": "§223(b)(8)(B). Decision 2 — Part III."},
    {"rule_id": "R-8889-EXCEPTIONS", "title": "RED-deferred (excess / IRA funding / non-spouse death)", "rule_type": "routing",
     "precedence": 6, "sort_order": 6,
     "formula": ("If line 2 > line 13 → D_8889_EXCESS (the 6% excise / Form 5329 Part VII, not computed); a "
                 "qualified IRA→HSA funding distribution → D_8889_FUNDING; a non-spouse death-of-beneficiary "
                 "→ a manual case."),
     "inputs": [], "outputs": [],
     "description": "Decision 2 — the rare cases out of v1 scope."},
]

F8889_LINES: list[dict] = [
    {"line_number": "1", "description": "1 Coverage type (self-only / family)", "line_type": "input"},
    {"line_number": "2", "description": "2 HSA contributions you made (not employer)", "line_type": "input"},
    {"line_number": "3", "description": "3 Contribution limit ($4,300 / $8,550; prorated; last-month rule)", "line_type": "calculated"},
    {"line_number": "4", "description": "4 Archer MSA contributions", "line_type": "input"},
    {"line_number": "5", "description": "5 Line 3 − line 4", "line_type": "calculated"},
    {"line_number": "6", "description": "6 Allocated family-limit share (married split)", "line_type": "input"},
    {"line_number": "7", "description": "7 Additional $1,000 catch-up (age 55+)", "line_type": "calculated"},
    {"line_number": "8", "description": "8 Line 6 + line 7", "line_type": "calculated"},
    {"line_number": "9", "description": "9 Employer contributions (W-2 box 12 code W)", "line_type": "input"},
    {"line_number": "10", "description": "10 Qualified HSA funding distribution (IRA→HSA; RED-deferred)", "line_type": "input"},
    {"line_number": "11", "description": "11 Line 9 + line 10", "line_type": "calculated"},
    {"line_number": "12", "description": "12 Line 8 − line 11 (the available limit)", "line_type": "calculated"},
    {"line_number": "13", "description": "13 HSA deduction = min(line 2, line 12) → Schedule 1 line 13", "line_type": "total"},
    {"line_number": "14a", "description": "14a Total distributions (1099-SA box 1)", "line_type": "input"},
    {"line_number": "14b", "description": "14b Rollovers + timely-withdrawn excess", "line_type": "input"},
    {"line_number": "14c", "description": "14c Line 14a − line 14b", "line_type": "calculated"},
    {"line_number": "15", "description": "15 Unreimbursed qualified medical expenses", "line_type": "input"},
    {"line_number": "16", "description": "16 Taxable HSA distribution (14c − 15) → Schedule 1 line 8f", "line_type": "total"},
    {"line_number": "17a", "description": "17a Exception (death / disability / age 65)?", "line_type": "input"},
    {"line_number": "17b", "description": "17b Additional 20% tax → Schedule 2 line 17c", "line_type": "total"},
    {"line_number": "18", "description": "18 Last-month-rule testing-period failure income", "line_type": "input"},
    {"line_number": "19", "description": "19 Funding-distribution testing failure (RED-deferred)", "line_type": "input"},
    {"line_number": "20", "description": "20 Line 18 + line 19 → Schedule 1 line 8f", "line_type": "total"},
    {"line_number": "21", "description": "21 Additional 10% tax → Schedule 2 line 17d", "line_type": "total"},
]

F8889_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_8889_EXCESS", "title": "Possible excess HSA contribution (6% excise)", "severity": "warning",
     "condition": "line 2 (your contributions) > line 13 (the deduction)",
     "message": ("Your HSA contributions exceed the deductible limit — the excess may be subject to the 6% "
                 "excise tax (Form 5329 Part VII), which is not computed here. Withdraw the excess (plus "
                 "earnings) by the return due date, or report the excise manually."),
     "notes": "Decision 2. The 6% excise is RED-deferred."},
    {"diagnostic_id": "D_8889_FUNDING", "title": "IRA→HSA funding distribution — not computed", "severity": "warning",
     "condition": "line 10 (qualified HSA funding distribution) > 0",
     "message": ("A once-in-lifetime qualified HSA funding distribution from an IRA (§408(d)(9), Form 8889 "
                 "line 10) is indicated. This and its separate testing period are not computed — verify the "
                 "line 11/12 limit and the funding testing period manually (Pub 590-A / Pub 969)."),
     "notes": "Decision 2. RED-deferred."},
    {"diagnostic_id": "D_8889_MEDICARE", "title": "Medicare enrollment ends HSA eligibility", "severity": "warning",
     "condition": "Medicare-enrolled flag set",
     "message": ("Enrollment in Medicare ends HSA eligibility — the contribution limit is zero beginning with "
                 "the first month of Medicare coverage (use the monthly proration). Watch the 6-month "
                 "retroactive Part A rule, which can create a retroactive excess contribution."),
     "notes": "Pub 969. Feeds the proration."},
    {"diagnostic_id": "D_8889_HDHP", "title": "Verify qualifying HDHP coverage", "severity": "info",
     "condition": "the HSA engages",
     "message": ("Confirm the taxpayer was covered by a qualifying high-deductible health plan (HDHP). For "
                 "2026, OBBBA treats bronze/catastrophic Marketplace plans and Direct Primary Care "
                 "arrangements as HDHP-eligible, and the telehealth safe harbor is permanent — verify "
                 "eligibility before claiming the deduction."),
     "notes": "OBBBA 2026 eligibility widening (a diagnostic, not the math)."},
    {"diagnostic_id": "D_8889_TESTING", "title": "Last-month rule — testing period applies", "severity": "info",
     "condition": "hsa_last_month_rule is True",
     "message": ("The last-month rule was used (full annual limit). You must remain HSA-eligible through the "
                 "testing period (ending the last day of the 12th month after this December) or include the "
                 "excess in income + a 10% additional tax (Part III) in the year eligibility is lost."),
     "notes": "§223(b)(8). A forward-looking reminder."},
    {"diagnostic_id": "D_8889_TY2026", "title": "TY2026 — re-verify the form line numbers", "severity": "warning",
     "condition": "tax_year == 2026 AND the HSA engages",
     "message": ("This 2026 return uses the verified 2026 §223 limits ($4,400 / $8,750), but the 2026 Form "
                 "8889 line numbers are not yet locked — re-verify the line mapping against the final 2026 "
                 "form when it posts (~Dec 2026)."),
     "notes": "Decision 4. The 2026 form re-pin."},
]

F8889_SCENARIOS: list[dict] = [
    {"scenario_name": "8889-T1 — deduction, full self-only (2025)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "coverage": "self", "eligible_months": 12, "last_month_rule": False,
                "own_contrib": 4300, "employer_contrib": 0, "age_55": False},
     "expected_outputs": {"hsa_deduction": 4300},
     "notes": "Limit 4,300; min(4,300, 4,300) = 4,300 → Sch 1 L13."},
    {"scenario_name": "8889-T2 — deduction prorated (6 months)", "scenario_type": "edge_case", "sort_order": 2,
     "inputs": {"tax_year": 2025, "coverage": "self", "eligible_months": 6, "last_month_rule": False,
                "own_contrib": 4300, "employer_contrib": 0, "age_55": False},
     "expected_outputs": {"hsa_deduction": 2150},
     "notes": "line 3 = round(4,300 × 6/12) = 2,150; min(4,300, 2,150) = 2,150."},
    {"scenario_name": "8889-T3 — the last-month rule (1 month → full)", "scenario_type": "edge_case", "sort_order": 3,
     "inputs": {"tax_year": 2025, "coverage": "self", "eligible_months": 1, "last_month_rule": True,
                "own_contrib": 4300, "employer_contrib": 0, "age_55": False},
     "expected_outputs": {"hsa_deduction": 4300},
     "notes": "Eligible Dec 1 → the full $4,300 limit regardless of months."},
    {"scenario_name": "8889-T4 — employer contributions reduce the deduction", "scenario_type": "edge_case", "sort_order": 4,
     "inputs": {"tax_year": 2025, "coverage": "self", "eligible_months": 12, "last_month_rule": False,
                "own_contrib": 2000, "employer_contrib": 2000, "age_55": False},
     "expected_outputs": {"hsa_deduction": 2000},
     "notes": "line 12 = 4,300 − 2,000 = 2,300; deduction = min(own 2,000, 2,300) = 2,000."},
    {"scenario_name": "8889-T5 — the $1,000 catch-up (55+)", "scenario_type": "edge_case", "sort_order": 5,
     "inputs": {"tax_year": 2025, "coverage": "self", "eligible_months": 12, "last_month_rule": False,
                "own_contrib": 5300, "employer_contrib": 0, "age_55": True},
     "expected_outputs": {"hsa_deduction": 5300},
     "notes": "line 8 = 4,300 + 1,000 = 5,300; min(5,300, 5,300) = 5,300."},
    {"scenario_name": "8889-T6 — taxable distribution + the 20% tax", "scenario_type": "normal", "sort_order": 6,
     "inputs": {"tax_year": 2025, "total_dist": 3000, "rollovers": 0, "qualified_medical": 2000, "exception": False},
     "expected_outputs": {"hsa_taxable_dist": 1000, "hsa_addl_tax_20": 200},
     "notes": "taxable = 3,000 − 2,000 = 1,000 → Sch 1 L8f; 20% = 200 → Sch 2 L17c."},
    {"scenario_name": "8889-T7 — distribution, age-65 exception (no 20%)", "scenario_type": "edge_case", "sort_order": 7,
     "inputs": {"tax_year": 2025, "total_dist": 3000, "rollovers": 0, "qualified_medical": 2000, "exception": True},
     "expected_outputs": {"hsa_taxable_dist": 1000, "hsa_addl_tax_20": 0},
     "notes": "Still taxable 1,000, but the age-65/death/disability exception → no 20% tax."},
    {"scenario_name": "8889-T8 — Part III testing failure + the 10% tax", "scenario_type": "edge_case", "sort_order": 8,
     "inputs": {"tax_year": 2025, "testing_failure": 1000},
     "expected_outputs": {"hsa_testing_income": 1000, "hsa_addl_tax_10": 100},
     "notes": "line 20 = 1,000 → Sch 1 L8f; 10% = 100 → Sch 2 L17d."},
    {"scenario_name": "8889-T9 — married family split (MFJ)", "scenario_type": "edge_case", "sort_order": 9,
     "inputs": {"tax_year": 2025, "coverage": "family", "eligible_months": 12, "last_month_rule": False,
                "own_contrib": 4275, "employer_contrib": 0, "age_55": False, "family_alloc": 4275},
     "expected_outputs": {"hsa_deduction": 4275},
     "notes": "Family limit 8,550 split 50/50 → line 6 = 4,275; min(4,275, 4,275) = 4,275."},
    {"scenario_name": "8889-T10 — 2026 self-only limit", "scenario_type": "normal", "sort_order": 10,
     "inputs": {"tax_year": 2026, "coverage": "self", "eligible_months": 12, "last_month_rule": False,
                "own_contrib": 4400, "employer_contrib": 0, "age_55": False},
     "expected_outputs": {"hsa_deduction": 4400},
     "notes": "2026 self-only $4,400; min(4,400, 4,400) = 4,400."},
    {"scenario_name": "8889-G1 — excess contribution → warning", "scenario_type": "diagnostic", "sort_order": 11,
     "inputs": {"tax_year": 2025, "coverage": "self", "eligible_months": 12, "last_month_rule": False,
                "own_contrib": 5000, "employer_contrib": 0, "age_55": False},
     "expected_outputs": {"hsa_deduction": 4300, "D_8889_EXCESS": True},
     "notes": "own 5,000 > the 4,300 limit → deduction capped at 4,300; D_8889_EXCESS (the 6% excise is manual)."},
]

F8889_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-8889-LIMIT", "IRC_223", "primary", "§223(b)(2) limits + (b)(8) the last-month rule"),
    ("R-8889-LIMIT", "IRS_2025_F8889_INSTR", "secondary", "The Line-3 Limitation Chart"),
    ("R-8889-FAMILY", "IRS_PUB_969", "primary", "The married split + the catch-up"),
    ("R-8889-FAMILY", "IRC_223", "secondary", "§223(b)(3) the catch-up / (b)(5) the split"),
    ("R-8889-DEDUCTION", "IRS_2025_F8889_INSTR", "primary", "Lines 9-13 → Sch 1 line 13"),
    ("R-8889-DEDUCTION", "IRC_223", "secondary", "§223(a) the deduction"),
    ("R-8889-DISTRIB", "IRC_223", "primary", "§223(f) distributions + the 20% tax"),
    ("R-8889-DISTRIB", "IRS_2025_F8889_INSTR", "secondary", "Lines 14-17b"),
    ("R-8889-TESTING", "IRC_223", "primary", "§223(b)(8)(B) the testing-period failure"),
    ("R-8889-TESTING", "IRS_2025_F8889_INSTR", "secondary", "Part III lines 18-21"),
    ("R-8889-EXCEPTIONS", "IRS_PUB_969", "primary", "The excess excise / funding distribution"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-8889-01", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "The §223 limits (2025 + 2026) + the catch-up",
     "description": "Pins the self-only/family limits 2025 $4,300/$8,550 + 2026 $4,400/$8,750 + the $1,000 catch-up. Bug it catches: a drifted limit or the wrong year.",
     "definition": {"kind": "constants_check", "form": "FORM_8889",
                    "constants": {"self_2025": 4300, "family_2025": 8550, "self_2026": 4400,
                                  "family_2026": 8750, "catch_up": 1000}},
     "sort_order": 1},
    {"assertion_id": "FA-1040-8889-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Deduction = min(own, limit − employer); proration + last-month rule",
     "description": "Validates R-8889-LIMIT + R-8889-DEDUCTION. Bug it catches: employer contributions not subtracted, the proration wrong, or the last-month rule not granting the full limit.",
     "definition": {"kind": "formula_check", "form": "FORM_8889",
                    "formula": "L13 == min(own, max(0, (last_month ? limit : round(limit*m/12)) + catch_up − employer))"},
     "sort_order": 2},
    {"assertion_id": "FA-1040-8889-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Taxable distribution = max(0, dist − medical); 20% unless excepted",
     "description": "Validates R-8889-DISTRIB. Bug it catches: medical not subtracted, or the 20% applied despite the age-65/death/disability exception.",
     "definition": {"kind": "formula_check", "form": "FORM_8889",
                    "formula": "L16 == max(0, (dist − rollovers) − medical); L17b == (exception ? 0 : round(0.20*L16))"},
     "sort_order": 3},
    {"assertion_id": "FA-1040-8889-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Deduction → Sch 1 L13; taxable + Part III income → Sch 1 L8f",
     "description": "Validates the flow. Bug it catches: the HSA deduction not landing on Schedule 1 line 13 (AGI), or the taxable/Part-III income not on line 8f.",
     "definition": {"kind": "flow_assertion", "form": "FORM_8889",
                    "checks": [{"source_line": "13", "must_write_to": ["SCH_1.13"]},
                               {"source_line": "16", "must_write_to": ["SCH_1.8f"]},
                               {"source_line": "20", "must_write_to": ["SCH_1.8f"]}]},
     "sort_order": 4},
    {"assertion_id": "FA-1040-8889-05", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "The 20% / 10% additional taxes → Sch 2 lines 17c / 17d",
     "description": "Validates R-8889-DISTRIB + R-8889-TESTING. Bug it catches: the additional taxes landing on the wrong Schedule 2 line (it is 17c/17d, NOT 13c).",
     "definition": {"kind": "flow_assertion", "form": "FORM_8889",
                    "checks": [{"source_line": "17b", "must_write_to": ["SCH_2.17c"]},
                               {"source_line": "21", "must_write_to": ["SCH_2.17d"]}]},
     "sort_order": 5},
    {"assertion_id": "FA-1040-8889-06", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Gates: excess contribution; TY2026 re-pin",
     "description": "Excess contributions (line 2 > line 13) fire D_8889_EXCESS (the 6% excise is RED-deferred); a 2026 return flags the line-number re-pin.",
     "definition": {"kind": "gating_check", "form": "FORM_8889", "expect": {"red_fires": True},
                    "blockers": ["excess_contribution"]},
     "sort_order": 6},
]


FORMS: list[dict] = [
    {"identity": F8889_IDENTITY, "facts": F8889_FACTS, "rules": F8889_RULES, "lines": F8889_LINES,
     "diagnostics": F8889_DIAGNOSTICS, "scenarios": F8889_SCENARIOS, "rule_links": F8889_RULE_LINKS},
]


class Command(BaseCommand):
    help = "Load the FORM_8889 spec (Health Savings Accounts). Refuses until READY_TO_SEED=True."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad FORM_8889 spec (Health Savings Accounts)\n"))
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
                "\nREFUSING TO SEED FORM_8889: not cleared to seed.\n\n"
                "Gated until Ken's review walk (the §223 limits + the proration + the\n"
                "last-month rule + the deduction/distribution/Part-III math).\n\n"
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
        form = TaxForm.objects.filter(form_number="FORM_8889").first()
        if form:
            uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
            self.stdout.write("FORM_8889: all rules cited" if not uncited
                              else self.style.WARNING(f"FORM_8889 uncited rules: {len(uncited)}"))
