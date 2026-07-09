"""Load the Form 8941 spec — Credit for Small Employer Health Insurance Premiums (§45R).

GREENFIELD authoring 2026-07-08 (the 1120-S ATS Scenario 6 RS gap; lookup/8941 was 404).
Sources verified VERBATIM this date:
  * f8941.pdf 2025 face (in-hand, tts resources/irs_forms/2025/f8941.pdf, manifest-hashed) —
    every line number, threshold ($33,000 line 9 / $67,000 line 3 / 25 FTE line 2), the
    50%/35% split, and the line-16 entity routing text below are read off that face.
  * i8941 2025 (fetched irs.gov/pub/irs-pdf/i8941.pdf 2026-07-08, 30 pp) — Worksheets 1-7
    mechanics, the excluded-individuals list, the seasonal-≤120-day rule, the 2,080-hour FTE
    rule, the round-down-to-$1,000 wage rule, and the "Premium Deduction Reduced" passage.

KEN RULINGS (2026-07-08, in-session):
  1. Line 5 (small-group-market average premium) = PREPARER-ENTERED from the i8941
     county table; the table itself is NOT encoded (annually-churning per-county data).
     D_8941_003 flags a missing line 5.
  2. §280C premium-deduction interplay = DIAGNOSTIC-ONLY v1 (D_8941_004): the preparer
     enters the already-reduced premium expense (the ATS S6 Attachment-1 presentation);
     the engine never silently mutates a book number.

⚠ SOURCE SELF-CONTRADICTION (flagged, not resolved — REVIEW_QUEUE 2026-07-08): the 2025
face says line 9 engages when line 3 exceeds $33,000 (and line 3 stops the credit at
$67,000+), but the 2025 i8941 Worksheet 6 computes the reduction with $33,300
("Subtract $33,300 from line 3 … Divide line 4 by $33,300"). The spec encodes each figure
exactly where its own source puts it (face-verbatim trigger; instructions-verbatim math)
and D_8941_005 flags returns in the $33,000-$67,000 band for hand-verification.

⚠ ATS SCENARIO-6 KEY ERROR (flagged for Ken/e-help — this spec encodes the LAW): the S6
key (WorkNAllDay: L7 63,767, 13 FTEs) prints line 8 = 12,753 — which is the Worksheet-5
REDUCTION (63,767 × 3/15), not the credit after reduction. §45R(d)(3)(A) and the 2025
Worksheet 5 line 6 ("Subtract line 5 from line 1") give line 8 = 63,767 − 12,753 = 51,014.
Scenario F8941-T1 pins the statutory 51,014 on the S6 inputs; F8941-T2 documents the key's
arithmetic as printed. The tts S6 build decision (law vs key) is a Ken/e-help call.
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

READY_TO_SEED = True  # Ken's four S6 rulings 2026-07-08 cover the judgment calls.

FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1  # New form — no prior RS row (lookup returned 404).
# Every eligible-small-employer lane Sherpa carries. Destination differs by
# entity (R-8941-DEST): 1120S/1065 stop at line 16 → Schedule K; 1040/1120
# continue to Form 3800 Part III line 4h.
FORM_ENTITY_TYPES = ["1120S", "1065", "1040", "1120"]
FORM_STATUS = "draft"


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("8941", "Form 8941 — Credit for Small Employer Health Insurance Premiums (§45R)"),
    ("sehi_credit", "§45R small-employer health-insurance credit — SHOP, FTE/wage phaseouts, credit period"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRC_45R",
        "source_type": "statute", "source_rank": "primary_official", "jurisdiction_code": "FED",
        "title": "IRC §45R — Employee Health Insurance Expenses of Small Employers",
        "citation": "26 U.S.C. §45R", "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:45R%20edition:prelim)",
        "current_status": "active", "is_substantive_authority": True, "is_filing_authority": False,
        "trust_score": 10.0, "requires_human_review": True,
        "notes": "50% (35% tax-exempt) of the lesser of premiums paid or the average-premium benchmark; "
                 "phased out by FTEs over 10 (÷15) and average wages over the indexed dollar amount; "
                 "2-consecutive-tax-year credit period for years after 2013.",
        "topics": ["sehi_credit"],
        "excerpts": [
            {"excerpt_label": "§45R(d)(3) — the two phaseout fractions",
             "location_reference": "§45R(c),(d)(3)",
             "excerpt_text": (
                 "The credit is reduced (but not below zero) by the sum of (A) an amount which bears the "
                 "same ratio to the credit as the number of full-time equivalent employees in excess of "
                 "10 bears to 15, and (B) an amount which bears the same ratio to the credit as the "
                 "average annual wages in excess of the dollar amount bears to that dollar amount "
                 "(§45R(d)(3)). NOTE the direction: the RATIO amounts are REDUCTIONS — the allowed "
                 "credit is what remains (the ATS S6 key inverts this; see the loader docstring)."),
             "summary_text": "Reduction = credit × (FTE−10)/15 + credit × (wages−$amt)/$amt; allowed = credit − reductions.",
             "is_key_excerpt": True},
        ],
    },
    {
        "source_code": "IRC_280C_45R",
        "source_type": "statute", "source_rank": "primary_official", "jurisdiction_code": "FED",
        "title": "IRC §280C — No double benefit: premium deduction reduced by the §45R credit",
        "citation": "26 U.S.C. §280C", "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:280C%20edition:prelim)",
        "current_status": "active", "is_substantive_authority": True, "is_filing_authority": False,
        "trust_score": 10.0, "requires_human_review": True,
        "notes": "i8941 2025 'Premium Deduction Reduced' (verbatim): 'You must reduce your deduction for "
                 "the cost of providing health insurance coverage to your employees by the amount of any "
                 "credit for small employer health insurance premiums allowed with respect to the "
                 "coverage.' Ken ruling 2026-07-08: diagnostic-only v1 (D_8941_004).",
        "topics": ["sehi_credit"],
        "excerpts": [],
    },
    {
        "source_code": "IRS_2025_8941_FORM",
        "source_type": "form", "source_rank": "primary_official", "jurisdiction_code": "FED",
        "title": "Form 8941 (2025) — Credit for Small Employer Health Insurance Premiums",
        "citation": "Form 8941 (2025)", "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f8941.pdf",
        "current_status": "active", "is_substantive_authority": False, "is_filing_authority": True,
        "trust_score": 9.5, "requires_human_review": False,
        "notes": "2025 face (in-hand, manifest-hashed). Line 2 stop at 25+ FTEs; line 3 stop at $67,000+ "
                 "average wages; line 7 = 50%/35%; line 8 engages when line 2 > 10; line 9 engages when "
                 "line 3 > $33,000; line 16 entity routing text verbatim in R-8941-DEST.",
        "topics": ["8941"],
        "excerpts": [
            {"excerpt_label": "Line 16 routing (2025 face, verbatim)",
             "location_reference": "Form 8941 (2025) line 16",
             "excerpt_text": (
                 "Add lines 12 and 15. Cooperatives, estates, and trusts, go to line 17. Tax-exempt "
                 "small employers, skip lines 17 and 18 and go to line 19. Partnerships and S "
                 "corporations, stop here and report this amount on Schedule K. All others, stop here "
                 "and report this amount on Form 3800, Part III, line 4h."),
             "summary_text": "S corps/partnerships stop at 16 → Schedule K; others → 3800 Part III 4h.",
             "is_key_excerpt": True},
        ],
    },
    {
        "source_code": "IRS_2025_8941_INSTR",
        "source_type": "official_instruction", "source_rank": "primary_official", "jurisdiction_code": "FED",
        "title": "Instructions for Form 8941 (2025)",
        "citation": "i8941 (2025)", "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i8941.pdf",
        "current_status": "active", "is_substantive_authority": True, "is_filing_authority": True,
        "trust_score": 9.5, "requires_human_review": False,
        "notes": "Fetched 2026-07-08 (30 pp). Worksheets 1-7; excluded individuals; seasonal rule; "
                 "2,080-hour FTE rule; round-down wage rule. ⚠ Worksheet 6 computes with $33,300 while "
                 "the face line 9 triggers at $33,000 — source self-contradiction, flagged (D_8941_005).",
        "topics": ["8941", "sehi_credit"],
        "excerpts": [
            {"excerpt_label": "Worksheet 5 (FTE phaseout, verbatim structure)",
             "location_reference": "i8941 (2025), Worksheet 5",
             "excerpt_text": (
                 "1. Enter the amount from Form 8941, line 7. 2. Enter the number from Form 8941, line "
                 "2. 3. Subtract 10 from line 2. 4. Divide line 3 by 15. Enter the result as a decimal "
                 "(rounded to at least 3 places). 5. Multiply line 1 by line 4. 6. Subtract line 5 from "
                 "line 1. Report this amount on Form 8941, line 8."),
             "summary_text": "Line 8 = L7 − L7×(FTE−10)/15 — the SUBTRACTION result, not the reduction.",
             "is_key_excerpt": True},
            {"excerpt_label": "Worksheet 6 (wage phaseout, verbatim structure — note $33,300)",
             "location_reference": "i8941 (2025), Worksheet 6",
             "excerpt_text": (
                 "1. Enter the amount from Form 8941, line 8. 2. Enter the amount from Form 8941, line "
                 "7. 3. Enter the amount from Form 8941, line 3. 4. Subtract $33,300 from line 3. 5. "
                 "Divide line 4 by $33,300. Enter the result as a decimal (rounded to at least 3 "
                 "places). 6. Multiply line 2 by line 5. 7. Subtract line 6 from line 1. Report this "
                 "amount on Form 8941, line 9."),
             "summary_text": "Line 9 = L8 − L7×((L3−33,300)/33,300); the face trigger says >$33,000 — discrepancy.",
             "is_key_excerpt": True},
            {"excerpt_label": "Excluded individuals (verbatim list)",
             "location_reference": "i8941 (2025), 'Individuals Considered Employees'",
             "excerpt_text": (
                 "The following individuals aren't considered employees when you figure this credit: the "
                 "owner of a sole proprietorship; a partner in a partnership; a shareholder who owns "
                 "(after applying the section 318 constructive ownership rules) more than 2% of an S "
                 "corporation; a shareholder who owns (after §318) more than 5% of a corporation that "
                 "isn't an S corporation; a person who owns more than 5% of the capital or profits "
                 "interest in any other business that isn't a corporation; family members (or household "
                 "dependents) of any of the above. Seasonal employees who worked 120 or fewer days are "
                 "excluded from FTE and average-wage computations, but premiums paid on their behalf "
                 "count toward the credit."),
             "summary_text": "Owners/partners/>2% S-corp shareholders/family excluded; seasonal ≤120 days out of FTE/wages only.",
             "is_key_excerpt": True},
            {"excerpt_label": "Premium Deduction Reduced (verbatim)",
             "location_reference": "i8941 (2025), 'Premium Deduction Reduced'",
             "excerpt_text": (
                 "You must reduce your deduction for the cost of providing health insurance coverage to "
                 "your employees by the amount of any credit for small employer health insurance "
                 "premiums allowed with respect to the coverage."),
             "summary_text": "§280C no-double-benefit — the premium deduction shrinks by the allowed credit.",
             "is_key_excerpt": True},
        ],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_8941_FORM", "8941", "governs"),
    ("IRS_2025_8941_INSTR", "8941", "governs"),
    ("IRC_45R", "8941", "governs"),
    ("IRC_280C_45R", "8941", "informs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM SPEC
# ═══════════════════════════════════════════════════════════════════════════

P_IDENTITY = {
    "form_number": "8941",
    "form_title": "Form 8941 — Credit for Small Employer Health Insurance Premiums",
    "notes": ("§45R credit, TY2025. v1 boundaries (Ken rulings 2026-07-08): line 5 average "
              "premium = preparer-entered (no county-table encode); §280C deduction reduction "
              "= diagnostic-only; worksheet ROLLUP totals are the v1 inputs (a per-employee "
              "Worksheet-1 grid is a future input leg — the rules encode the worksheet math "
              "so the rollups can be computed when that leg lands)."),
}

P_FACTS: list[dict] = [
    # Header gates
    {"fact_key": "f8941_shop_marketplace", "label": "Line A — premiums paid through a SHOP Marketplace (or an exception applies)?",
     "data_type": "boolean", "required": True, "sort_order": 1,
     "notes": "No → STOP, do not file (face verbatim). Exceptions: certain counties without SHOP plans (Notice 2018-27, extended); Hawaii waiver = no credit."},
    {"fact_key": "f8941_marketplace_id", "label": "Line A — Marketplace Identifier (if any)", "data_type": "string", "sort_order": 2},
    {"fact_key": "f8941_alt_ein", "label": "Line B — EIN used for employment taxes, if different", "data_type": "string", "sort_order": 3},
    {"fact_key": "f8941_prior_credit_used", "label": "Line C — a return for a year after 2013 and before 2024 included an 8941 with line A Yes and line 12 positive?",
     "data_type": "boolean", "required": True, "sort_order": 4,
     "notes": "Yes → STOP (the 2-consecutive-tax-year credit period is used up) unless the entity files only to report a line-15 pass-through credit."},
    {"fact_key": "f8941_is_tax_exempt", "label": "Tax-exempt eligible small employer?", "data_type": "boolean", "default_value": "false", "sort_order": 5,
     "notes": "Drives the 35% (vs 50%) line-7 percentage and the line 19/20 payroll-tax cap → Form 990-T."},
    # Worksheet rollups (v1 preparer-entered; per-employee grid = future input leg)
    {"fact_key": "f8941_employee_count", "label": "Line 1 — individuals employed who are considered employees (Worksheet 1 col (a))",
     "data_type": "integer", "required": True, "sort_order": 10,
     "notes": "EXCLUDES owners, partners, >2% S-corp shareholders (§318), >5% other owners, and their family members/dependents. Seasonal ≤120 days excluded here and from wages/FTEs (but their premiums count on line 4)."},
    {"fact_key": "f8941_fte_count", "label": "Line 2 — full-time equivalent employees (Worksheet 2 line 3)",
     "data_type": "integer", "required": True, "sort_order": 11,
     "notes": "Total hours of service (capped at 2,080 per employee) ÷ 2,080, rounded DOWN to a whole number. 25 or more → credit = 0."},
    {"fact_key": "f8941_total_wages", "label": "Worksheet 3 line 1 — total wages paid to considered employees",
     "data_type": "decimal", "sort_order": 12},
    {"fact_key": "f8941_avg_annual_wages", "label": "Line 3 — average annual wages (Worksheet 3 line 3; multiple of $1,000)",
     "data_type": "decimal", "sort_order": 13,
     "notes": "total_wages ÷ FTEs, rounded DOWN to the next-lowest multiple of $1,000. $67,000 or more → credit = 0 (2025 face)."},
    {"fact_key": "f8941_premiums_paid", "label": "Line 4 — premiums paid under a qualifying arrangement (Worksheet 4 col (b))",
     "data_type": "decimal", "required": True, "sort_order": 14,
     "notes": "Qualifying arrangement = generally a uniform ≥50% employer share of each enrolled employee's premium. State subsidies paid to you do NOT reduce this; subsidies paid to the insurer COUNT as paid by you (i8941 verbatim)."},
    {"fact_key": "f8941_avg_premium_smallgroup", "label": "Line 5 — premiums at the small-group-market average (Worksheet 4 col (c)) — PREPARER-ENTERED",
     "data_type": "decimal", "required": True, "sort_order": 15,
     "notes": "Ken ruling 2026-07-08: preparer enters this from the i8941 average-premium table for the employee's county; the table is not encoded."},
    {"fact_key": "f8941_state_subsidies", "label": "Line 10 — state premium subsidies paid and state tax credits available",
     "data_type": "decimal", "default_value": "0", "sort_order": 16},
    {"fact_key": "f8941_enrolled_count", "label": "Line 13 — employees for whom premiums were paid (Worksheet 4 col (a))",
     "data_type": "integer", "sort_order": 17},
    {"fact_key": "f8941_enrolled_fte", "label": "Line 14 — FTEs of the line-13 employees (Worksheet 7 line 3; minimum 1)",
     "data_type": "integer", "sort_order": 18,
     "notes": "Enrolled hours ÷ 2,080 rounded down; if the result is less than one, enter 1 (i8941 Worksheet 7 verbatim)."},
    {"fact_key": "f8941_passthrough_credit", "label": "Line 15 — credit from partnerships, S corporations, cooperatives, estates, trusts",
     "data_type": "decimal", "default_value": "0", "sort_order": 19,
     "notes": "K-1 (1065) box 15 code BA; K-1 (1120-S) box 13 code BA; K-1 (1041) box 13 code G; 1099-PATR box 12 (i8941 2025 verbatim). ⚠ the ATS S6 K-1 prints the PRE-2023-style code P — the K1_1120S spec's box-13 code table governs the issuer side."},
    {"fact_key": "f8941_payroll_taxes", "label": "Line 19 — payroll taxes (tax-exempt employers only)",
     "data_type": "decimal", "default_value": "0", "sort_order": 20,
     "notes": "Federal income tax + Medicare withheld plus employer Medicare for the calendar year; caps the refundable credit at line 20 → Form 990-T Part III line 6f."},
]

P_RULES: list[dict] = [
    {"rule_id": "R-8941-ELIG", "title": "Eligibility gates (lines A, C, 2, 3)", "rule_type": "validation",
     "precedence": 1, "sort_order": 1,
     "formula": ("line A No → STOP (do not file). line C Yes → STOP unless filing only for a line-15 "
                 "pass-through credit (then line 12 must be empty). FTEs ≥ 25 → skip 3-11, line 12 = 0. "
                 "Average annual wages ≥ $67,000 → skip 4-11, line 12 = 0."),
     "inputs": ["f8941_shop_marketplace", "f8941_prior_credit_used", "f8941_fte_count", "f8941_avg_annual_wages"],
     "outputs": [],
     "description": ("Face-verbatim gates. The 2-consecutive-tax-year credit period (years after 2013): a "
                     "prior positive-line-12 8941 on a return for a year after 2013 and before 2024 "
                     "exhausts the period for 2025 (an unbroken 2024→2025 pair is the only live path)."),
    },
    {"rule_id": "R-8941-WAGES", "title": "Worksheets 2/3 — FTEs and average annual wages", "rule_type": "calculation",
     "precedence": 2, "sort_order": 2,
     "formula": ("FTEs (line 2) = floor(total hours of service, each employee capped at 2,080, ÷ 2,080). "
                 "Average annual wages (line 3) = floor_to_$1,000(total_wages ÷ FTEs)."),
     "inputs": ["f8941_total_wages", "f8941_fte_count"],
     "outputs": ["f8941_avg_annual_wages"],
     "description": ("i8941 Worksheets 2-3 verbatim: hours capped at 2,080 per employee; seasonal ≤120-day "
                     "employees excluded from hours and wages; the average rounds DOWN to the next-lowest "
                     "multiple of $1,000 (round $32,999 to $32,000)."),
    },
    {"rule_id": "R-8941-CREDIT", "title": "Lines 6-7 — tentative credit", "rule_type": "calculation",
     "precedence": 3, "sort_order": 3,
     "formula": "L6 = min(L4, L5); L7 = L6 × (0.35 if tax-exempt else 0.50).",
     "inputs": ["f8941_premiums_paid", "f8941_avg_premium_smallgroup", "f8941_is_tax_exempt"],
     "outputs": [],
     "description": "The benchmark cap: premiums count only up to what the small-group-market average premium would have cost (line 5, preparer-entered per the Ken ruling)."},
    {"rule_id": "R-8941-FTEPHASE", "title": "Line 8 — FTE phaseout (Worksheet 5)", "rule_type": "calculation",
     "precedence": 4, "sort_order": 4,
     "formula": "If L2 ≤ 10: L8 = L7. Else: L8 = L7 − L7 × ((L2 − 10) / 15)  [decimal rounded to ≥3 places].",
     "inputs": ["f8941_fte_count"],
     "outputs": [],
     "description": ("§45R(d)(3)(A) + i8941 Worksheet 5 verbatim: the ratio amount is a REDUCTION; line 8 "
                     "is the subtraction result. ⚠ The ATS 1120-S Scenario 6 key prints the REDUCTION "
                     "(12,753 on 63,767 @ 13 FTEs) as line 8 — an inversion of the statute; this spec "
                     "encodes the law (line 8 = 51,014 on those inputs). See scenarios T1/T2."),
    },
    {"rule_id": "R-8941-WAGEPHASE", "title": "Line 9 — average-wage phaseout (Worksheet 6)", "rule_type": "calculation",
     "precedence": 5, "sort_order": 5,
     "formula": ("If L3 ≤ $33,000 (face trigger): L9 = L8. Else: L9 = L8 − L7 × ((L3 − 33,300) / 33,300) "
                 "[i8941 Worksheet 6 figures, verbatim]."),
     "inputs": ["f8941_avg_annual_wages"],
     "outputs": [],
     "description": ("⚠ SOURCE SELF-CONTRADICTION (unresolved; D_8941_005): the 2025 face triggers this "
                     "phaseout above $33,000 and zeroes the credit at $67,000 (line 3), while the 2025 "
                     "i8941 Worksheet 6 subtracts and divides by $33,300. Encoded exactly as each source "
                     "states; hand-verify any return in the band until the IRS reconciles the figures."),
    },
    {"rule_id": "R-8941-STATE", "title": "Lines 10-12 — state subsidy cap", "rule_type": "calculation",
     "precedence": 6, "sort_order": 6,
     "formula": "L11 = max(0, L4 − L10); L12 = min(L9, L11).",
     "inputs": ["f8941_state_subsidies"],
     "outputs": [],
     "description": "The credit can never exceed the premiums actually borne after state premium subsidies and available state credits."},
    {"rule_id": "R-8941-DEST", "title": "Lines 13-20 — counts and entity destinations", "rule_type": "routing",
     "precedence": 7, "sort_order": 7,
     "formula": ("If L12 > 0: report L13 (enrolled employees) + L14 (their FTEs, min 1). L16 = L12 + L15. "
                 "1120-S → Schedule K line 13g (K-1 box 13); 1065 → Schedule K line 15 (K-1 box 15); "
                 "cooperatives/estates/trusts → L17/L18 → Form 3800 Part III 4h; tax-exempt → L19/L20 "
                 "(smaller of L16 or payroll taxes) → Form 990-T Part III 6f; all others (1040/1120) → "
                 "Form 3800 Part III line 4h."),
     "inputs": ["f8941_enrolled_count", "f8941_enrolled_fte", "f8941_passthrough_credit",
                "f8941_is_tax_exempt", "f8941_payroll_taxes"],
     "outputs": [],
     "description": ("Face-verbatim line-16 routing: 'Partnerships and S corporations, stop here and "
                     "report this amount on Schedule K. All others, stop here and report this amount on "
                     "Form 3800, Part III, line 4h.' The general business credit character rides §38."),
    },
    {"rule_id": "R-8941-280C", "title": "§280C — premium deduction reduced by the credit (diagnostic-only v1)",
     "rule_type": "validation", "precedence": 8, "sort_order": 8,
     "formula": "insurance-premium deduction must be reduced by the allowed §45R credit — VERIFIED BY DIAGNOSTIC (D_8941_004), never auto-adjusted.",
     "inputs": [],
     "outputs": [],
     "description": ("i8941 verbatim: 'You must reduce your deduction for the cost of providing health "
                     "insurance coverage to your employees by the amount of any credit … allowed.' Ken "
                     "ruling 2026-07-08: the preparer enters the already-reduced expense (the ATS S6 "
                     "Attachment-1 presentation — 'This amount has been reduced by the premium "
                     "deduction.'); the engine flags, never silently mutates a book number."),
    },
]

P_LINES: list[dict] = [
    {"line_number": "A", "description": "Line A — premiums through a SHOP Marketplace (or exception)? Yes → Marketplace Identifier; No → STOP, do not file", "line_type": "input", "source_facts": ["f8941_shop_marketplace", "f8941_marketplace_id"]},
    {"line_number": "B", "description": "Line B — EIN used to report employment taxes, if different", "line_type": "input", "source_facts": ["f8941_alt_ein"]},
    {"line_number": "C", "description": "Line C — prior 8941 (tax year after 2013, before 2024) with line A Yes and positive line 12? Yes → STOP (credit period used)", "line_type": "input", "source_facts": ["f8941_prior_credit_used"]},
    {"line_number": "1", "description": "Line 1 — individuals employed who are considered employees (Worksheet 1 col (a))", "line_type": "input", "source_facts": ["f8941_employee_count"]},
    {"line_number": "2", "description": "Line 2 — FTEs (Worksheet 2 line 3); 25 or more → skip 3-11, enter -0- on line 12", "line_type": "input", "source_facts": ["f8941_fte_count"], "source_rules": ["R-8941-WAGES", "R-8941-ELIG"]},
    {"line_number": "3", "description": "Line 3 — average annual wages (Worksheet 3 line 3; a multiple of $1,000); $67,000 or more → skip 4-11, enter -0- on line 12", "line_type": "calculated", "source_facts": ["f8941_avg_annual_wages"], "source_rules": ["R-8941-WAGES", "R-8941-ELIG"]},
    {"line_number": "4", "description": "Line 4 — premiums paid under a qualifying arrangement (Worksheet 4 col (b))", "line_type": "input", "source_facts": ["f8941_premiums_paid"]},
    {"line_number": "5", "description": "Line 5 — premiums at the small-group-market average premium (Worksheet 4 col (c)) — preparer-entered from the i8941 county table", "line_type": "input", "source_facts": ["f8941_avg_premium_smallgroup"]},
    {"line_number": "6", "description": "Line 6 — smaller of line 4 or line 5", "line_type": "calculated", "source_rules": ["R-8941-CREDIT"]},
    {"line_number": "7", "description": "Line 7 — line 6 × 50% (35% for tax-exempt small employers)", "line_type": "calculated", "source_rules": ["R-8941-CREDIT"]},
    {"line_number": "8", "description": "Line 8 — if line 2 ≤ 10, line 7; otherwise Worksheet 5 line 6 (line 7 less the FTE-phaseout reduction)", "line_type": "calculated", "source_rules": ["R-8941-FTEPHASE"]},
    {"line_number": "9", "description": "Line 9 — if line 3 ≤ $33,000, line 8; otherwise Worksheet 6 line 7 (line 8 less the wage-phaseout reduction)", "line_type": "calculated", "source_rules": ["R-8941-WAGEPHASE"]},
    {"line_number": "10", "description": "Line 10 — state premium subsidies paid and state tax credits available", "line_type": "input", "source_facts": ["f8941_state_subsidies"]},
    {"line_number": "11", "description": "Line 11 — line 4 minus line 10 (not below zero)", "line_type": "calculated", "source_rules": ["R-8941-STATE"]},
    {"line_number": "12", "description": "Line 12 — smaller of line 9 or line 11", "line_type": "calculated", "source_rules": ["R-8941-STATE"]},
    {"line_number": "13", "description": "Line 13 — employees included on line 1 for whom premiums were paid (Worksheet 4 col (a)); only if line 12 > 0", "line_type": "input", "source_facts": ["f8941_enrolled_count"]},
    {"line_number": "14", "description": "Line 14 — FTEs of the line-13 employees (Worksheet 7 line 3; minimum 1)", "line_type": "input", "source_facts": ["f8941_enrolled_fte"]},
    {"line_number": "15", "description": "Line 15 — credit from partnerships, S corporations, cooperatives, estates, and trusts (K-1 codes: 1065 15-BA / 1120-S 13-BA / 1041 13-G; 1099-PATR box 12)", "line_type": "input", "source_facts": ["f8941_passthrough_credit"]},
    {"line_number": "16", "description": "Line 16 — add lines 12 and 15. Partnerships and S corporations STOP: report on Schedule K (1120-S K13g / 1065 K15). All others → Form 3800 Part III line 4h", "line_type": "total", "source_rules": ["R-8941-DEST"], "destination_form": "1120-S Schedule K line 13g / 1065 Schedule K line 15 / Form 3800 Part III 4h"},
    {"line_number": "17", "description": "Line 17 — amount allocated to cooperative patrons or estate/trust beneficiaries", "line_type": "input"},
    {"line_number": "18", "description": "Line 18 — cooperatives/estates/trusts: line 16 minus line 17 → Form 3800 Part III line 4h", "line_type": "calculated", "source_rules": ["R-8941-DEST"], "destination_form": "Form 3800 Part III 4h"},
    {"line_number": "19", "description": "Line 19 — payroll taxes paid (tax-exempt small employers only)", "line_type": "input", "source_facts": ["f8941_payroll_taxes"]},
    {"line_number": "20", "description": "Line 20 — tax-exempt: smaller of line 16 or line 19 → Form 990-T Part III line 6f", "line_type": "total", "source_rules": ["R-8941-DEST"], "destination_form": "Form 990-T Part III 6f"},
]

P_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_8941_001", "title": "Line A No — do not file", "severity": "error",
     "condition": "f8941_shop_marketplace == false AND any 8941 amount entered",
     "message": "Form 8941 line A is No — the form cannot be filed (no SHOP-Marketplace coverage and no exception). Remove the 8941 entries or establish the county-exception (Notice 2018-27) / other exception."},
    {"diagnostic_id": "D_8941_002", "title": "Line C Yes — credit period exhausted", "severity": "error",
     "condition": "f8941_prior_credit_used == true AND line 12 > 0",
     "message": "A positive-line-12 Form 8941 was filed for a year after 2013 and before 2024 — the 2-consecutive-tax-year credit period is used up. Line 12 must be empty; only a line-15 pass-through credit may be reported."},
    {"diagnostic_id": "D_8941_003", "title": "Line 5 average premium missing", "severity": "warning",
     "condition": "f8941_premiums_paid > 0 AND f8941_avg_premium_smallgroup in (0, blank)",
     "message": "Enter line 5 — the premiums at the small-group-market average premium for the employees' counties (i8941 average-premium table). The credit cannot compute without it (line 6 = smaller of 4 or 5)."},
    {"diagnostic_id": "D_8941_004", "title": "§280C — reduce the premium deduction by the credit", "severity": "warning",
     "condition": "line 12 > 0",
     "message": "The §45R credit was computed: the deduction for employee health-insurance premiums must be REDUCED by the allowed credit (i8941 'Premium Deduction Reduced'). Confirm the premium expense entered is already net of the credit — the engine never adjusts it automatically (Ken ruling 2026-07-08)."},
    {"diagnostic_id": "D_8941_005", "title": "Wages in the $33,000-$67,000 band — source discrepancy", "severity": "warning",
     "condition": "f8941_avg_annual_wages > 33000 AND f8941_avg_annual_wages < 67000",
     "message": "The 2025 form face triggers the wage phaseout above $33,000 while the 2025 i8941 Worksheet 6 computes with $33,300 — the sources disagree. Hand-verify line 9 for this return (the spec encodes each figure where its source puts it)."},
    {"diagnostic_id": "D_8941_006", "title": "Excluded-individuals reminder", "severity": "info",
     "condition": "f8941_employee_count > 0",
     "message": "Line 1 and the FTE/wage worksheets EXCLUDE owners, partners, more-than-2% S corporation shareholders (§318 attribution), more-than-5% other owners, and their family members/dependents. Seasonal employees (≤120 days) are excluded from FTEs and wages but their premiums count."},
]

P_SCENARIOS: list[dict] = [
    {"scenario_name": "F8941-T1 — ATS S6 inputs, STATUTORY math (the law this spec encodes)",
     "scenario_type": "normal", "sort_order": 1,
     "inputs": {"shop_marketplace": True, "marketplace_id": "01-FFE", "prior_credit_used": False,
                "employee_count": 16, "fte_count": 13, "avg_annual_wages": 27000,
                "premiums_paid": 127534, "avg_premium_smallgroup": 200705,
                "state_subsidies": 0, "passthrough_credit": 0, "is_tax_exempt": False},
     "expected_outputs": {"line6": 127534, "line7": 63767, "line8": 51014, "line9": 51014,
                          "line11": 127534, "line12": 51014, "line16": 51014},
     "notes": ("WorkNAllDay Inc (ATS 1120-S Scenario 6) inputs. L6 = min(127,534, 200,705); L7 = 63,767; "
               "WS5 reduction = 63,767 × (13−10)/15 = 12,753.4 → L8 = 63,767 − 12,753 = 51,014 "
               "(§45R(d)(3)(A) + i8941 WS5 line 6 verbatim); wages 27,000 ≤ 33,000 → L9 = L8; L12 = "
               "min(51,014, 127,534) = 51,014 → Schedule K 13g.")},
    {"scenario_name": "F8941-T2 — the ATS S6 KEY as printed (documents the apparent key error)",
     "scenario_type": "edge_case", "sort_order": 2,
     "inputs": {"same_as": "F8941-T1"},
     "expected_outputs": {"key_line8": 12753, "key_line12": 12753, "key_k13g": 12753,
                          "key_k1_box13": "6377/6376 code P"},
     "notes": ("AS PRINTED in ty25-f1120s-ats-scenario06: line 8 = 12,753 — exactly the Worksheet-5 "
               "REDUCTION (63,767 × 3/15), i.e., the phaseout fraction applied as the ALLOWED amount. "
               "That inverts §45R(d)(3)(A) ('reduced BY an amount which bears the same ratio…'). Also: "
               "the K-1 box 13 prints pre-2023-style code P where i8941 line-15 cross-references code "
               "BA. The tts S6 build must NOT bend compute to this key (the ats-answer-keys precedent); "
               "law-vs-key at upload time = Ken/e-help decision.")},
    {"scenario_name": "F8941-T3 — 25-FTE and $67,000 stops; 10-FTE/$33,000 no-phaseout edges",
     "scenario_type": "edge_case", "sort_order": 3,
     "inputs": {"cases": [
         {"fte_count": 25, "expected_line12": 0},
         {"avg_annual_wages": 67000, "expected_line12": 0},
         {"fte_count": 10, "avg_annual_wages": 33000, "premiums_paid": 10000,
          "avg_premium_smallgroup": 12000, "expected_line7": 5000, "expected_line8": 5000,
          "expected_line9": 5000}]},
     "expected_outputs": {"boundary_behavior": "face-verbatim"},
     "notes": "Face verbatim: 25+ FTEs or $67,000+ wages → -0- on line 12; exactly 10 FTEs / exactly $33,000 → NO phaseout (the triggers are 'more than 10' / 'more than $33,000')."},
    {"scenario_name": "F8941-T4 — state subsidy caps the credit at net premiums",
     "scenario_type": "normal", "sort_order": 4,
     "inputs": {"fte_count": 8, "avg_annual_wages": 30000, "premiums_paid": 20000,
                "avg_premium_smallgroup": 30000, "state_subsidies": 12000, "is_tax_exempt": False},
     "expected_outputs": {"line7": 10000, "line9": 10000, "line11": 8000, "line12": 8000},
     "notes": "L7 = 20,000 × 50% = 10,000; L11 = 20,000 − 12,000 = 8,000; L12 = min(10,000, 8,000) = 8,000."},
]

P_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-8941-ELIG", "IRS_2025_8941_FORM", "primary", "Lines A/C stop text; line 2/3 skip-to-zero text"),
    ("R-8941-ELIG", "IRS_2025_8941_INSTR", "secondary", "Credit period + Line C exception for pass-through-only filings"),
    ("R-8941-WAGES", "IRS_2025_8941_INSTR", "primary", "Worksheets 2-3: 2,080-hour FTE rule; round-down-to-$1,000 wages"),
    ("R-8941-CREDIT", "IRS_2025_8941_FORM", "primary", "Lines 6-7: smaller-of + 50%/35%"),
    ("R-8941-CREDIT", "IRC_45R", "secondary", "§45R(b) average-premium benchmark cap"),
    ("R-8941-FTEPHASE", "IRC_45R", "primary", "§45R(d)(3)(A) — reduction ratio (FTE−10)/15"),
    ("R-8941-FTEPHASE", "IRS_2025_8941_INSTR", "secondary", "Worksheet 5 verbatim (line 8 = the subtraction result)"),
    ("R-8941-WAGEPHASE", "IRS_2025_8941_INSTR", "primary", "Worksheet 6 verbatim ($33,300 subtract/divide)"),
    ("R-8941-WAGEPHASE", "IRS_2025_8941_FORM", "secondary", "Face line 9 trigger $33,000 / line 3 stop $67,000 — the discrepancy pair"),
    ("R-8941-STATE", "IRS_2025_8941_FORM", "primary", "Lines 10-12"),
    ("R-8941-DEST", "IRS_2025_8941_FORM", "primary", "Line 16 routing text verbatim (Schedule K / 3800 4h)"),
    ("R-8941-DEST", "IRS_2025_8941_INSTR", "secondary", "Line 15 K-1 code cross-references; lines 17-20"),
    ("R-8941-280C", "IRS_2025_8941_INSTR", "primary", "'Premium Deduction Reduced' verbatim"),
    ("R-8941-280C", "IRC_280C_45R", "secondary", "§280C no-double-benefit"),
]

FLOW_ASSERTIONS: list[dict] = [
    # ACTIVE 2026-07-08: the tts 8941 unit landed (compute_8941 + K13g flow +
    # K-1 code BA + IRS8941 doc mapper; S6 unit 1) — both assertions live.
    {"assertion_id": "FA-8941-01", "assertion_type": "reconciliation",
     "entity_types": ["1120S", "1065", "1040", "1120"], "status": "active",
     "title": "Credit chain: L6=min(4,5); L7=L6×pct; L8/L9 phaseouts are REDUCTIONS; L12=min(L9,L11)",
     "description": ("Validates R-8941-CREDIT/FTEPHASE/WAGEPHASE/STATE. Bug it catches: applying the "
                     "§45R(d)(3) ratio as the allowed credit instead of the reduction (the ATS S6 key's "
                     "inversion)."),
     "definition": {"kind": "reconciliation", "form": "8941",
                    "formula": ("L6=min(L4,L5); L7=L6*(0.35 if exempt else 0.5); "
                                "L8=L7 if FTE<=10 else L7-L7*((FTE-10)/15); "
                                "L9=L8 if wages<=33000 else L8-L7*((wages-33300)/33300); "
                                "L11=max(0,L4-L10); L12=min(L9,L11)")},
     "sort_order": 1},
    {"assertion_id": "FA-8941-02", "assertion_type": "flow_assertion",
     "entity_types": ["1120S"], "status": "active",
     "title": "1120-S: line 16 → Schedule K line 13g → K-1 box 13 (Σ owners == K13g)",
     "description": "Validates R-8941-DEST on the S-corp lane. Bug it catches: the credit reaching 3800 at entity level, or the K-1 split not reconciling to K13g.",
     "definition": {"kind": "flow_assertion", "form": "8941",
                    "checks": [{"source_line": "16", "must_write_to": ["SCH_K_1120S.13g"]}]},
     "sort_order": 2},
]


class Command(BaseCommand):
    help = "Load the Form 8941 spec (§45R small-employer health-insurance credit)."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad Form 8941 spec (§45R credit)\n"))
        self._load_topics()
        sources = self._load_sources()
        form = self._upsert_form(P_IDENTITY)
        self._upsert_facts(form, P_FACTS)
        rules = self._upsert_rules(form, P_RULES)
        self._upsert_authority_links(rules, sources, P_RULE_LINKS)
        self._upsert_lines(form, P_LINES)
        self._upsert_diagnostics(form, P_DIAGNOSTICS)
        self._upsert_tests(form, P_SCENARIOS)
        self._upsert_form_links(sources)
        self._load_flow_assertions()
        self._report_totals()

    def _guard_against_hollow_seed(self):
        empty = [name for name, block in [
            ("P_FACTS", P_FACTS), ("P_RULES", P_RULES), ("P_LINES", P_LINES),
            ("P_DIAGNOSTICS", P_DIAGNOSTICS), ("P_SCENARIOS", P_SCENARIOS),
            ("P_RULE_LINKS", P_RULE_LINKS), ("FLOW_ASSERTIONS", FLOW_ASSERTIONS),
        ] if not block]
        if not READY_TO_SEED or empty:
            still_empty = "\n  ".join(f"- {n}" for n in empty) or "(all populated)"
            raise CommandError(
                f"\nREFUSING TO SEED Form 8941.\nREADY_TO_SEED = {READY_TO_SEED}\n"
                f"Empty blocks:\n  {still_empty}\n")

    def _load_topics(self):
        for code, name in AUTHORITY_TOPICS:
            AuthorityTopic.objects.update_or_create(topic_code=code, defaults={"topic_name": name})
        self.stdout.write(f"Topics: {len(AUTHORITY_TOPICS)} in batch")

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

    def _upsert_form(self, identity: dict) -> TaxForm:
        form, created = TaxForm.objects.update_or_create(
            form_number=identity["form_number"], jurisdiction=FORM_JURISDICTION,
            tax_year=FORM_TAX_YEAR, version=FORM_VERSION,
            defaults={"form_title": identity["form_title"], "entity_types": FORM_ENTITY_TYPES,
                      "status": FORM_STATUS, "notes": identity["notes"]})
        self.stdout.write(f"{'Created' if created else 'Updated'} Form {identity['form_number']}")
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
        self.stdout.write(f"  {len(FLOW_ASSERTIONS)} flow assertions (active)")

    def _report_totals(self):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(f"TaxForms: {TaxForm.objects.count()} | FlowAssertions: {FlowAssertion.objects.count()}")
        form = TaxForm.objects.filter(form_number="8941").order_by("-version").first()
        if form:
            uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
            self.stdout.write("Form 8941: all rules cited" if not uncited
                              else self.style.WARNING(f"Form 8941 uncited rules: {len(uncited)}"))
