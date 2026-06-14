"""Load the FORM_8962 spec — Premium Tax Credit (§36B) reconciliation.

Post-sprint NEXT-UP #7. Mandatory before live use for marketplace clients.
Reconciles the advance PTC (APTC) paid to the insurer against the actual PTC
computed from final household income. Net PTC -> Schedule 3 line 9; excess-APTC
repayment (limited by Table 5) -> Schedule 2 line 1a. Both feeders already exist
in tts-tax-app.

KEN'S 4 SCOPE DECISIONS (2026-06-14, AskUserQuestion — the comprehensive build):
  (1) FULL MONTHLY method (lines 12-23); (2) COMPUTE the iterative SEHI<->PTC
  (Pub 974); (3) 2025 ONLY, RED-defer 2026 (the ARPA/IRA enhancement expires);
  (4) COMPUTE Part 4 (shared policy allocation) + Part 5 (year-of-marriage alt).

CONSTANTS VERIFIED 2026-06-14 from the 2025 i8962 PDF (cell-by-cell; brief
tts-tax-app server/specs/_8962_ptc_source_brief.md):
  - Line 5 (household income as % of FPL) = TRUNCATE(income/FPL x 100); if > 400
    enter 401 (the 400% cliff is SUSPENDED for 2025 — > 400% is still eligible).
  - Table 2 applicable figure (the required-contribution %): < 150% -> 0.0000;
    150-200% -> +0.0004/point from 0; 200-250% -> +0.0004 from 0.0200; 250-300%
    -> +0.0004 from 0.0400; 300-400% -> +0.00025/point from 0.0600; >= 400% ->
    0.0850. Round to 4 decimals. (Endpoints 0/.02/.04/.06/.085; 175->.0100,
    350->.0725.)
  - Line 8a = ROUND(line 3 x line 7); line 8b = ROUND(line 8a / 12).
  - Monthly (lines 12-23): max premium assistance = max(0, SLCSP(col b) - monthly
    contribution(col c)); PTC(col e) = min(premium(col a), that).
  - Table 5 repayment limitation (2025, by line 5 + filing status): < 200% ->
    $375 single / $750 other; 200-300% -> $975 / $1,950; 300-400% -> $1,625 /
    $3,250; >= 400% -> NO LIMIT (blank). Line 29 = min(line 27 excess, line 28).
  - 2024 FPL (2025 returns use the PRIOR year): 48 states+DC base $15,060 +$5,380/
    person; Alaska $18,810 +$6,730; Hawaii $17,310 +$6,190 (size N = base +
    (N-1) x increment).

Single form, the load_1040_form_2441 precedent.

SAFETY GUARD: READY_TO_SEED stays False until Ken's review walk (Table 2 + the
2024 FPL + Table 5 + the monthly method + the SEHI iterative + Parts 4/5).
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


READY_TO_SEED = False  # Gated until Ken's review walk.


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_ENTITY_TYPES = ["1040"]
FORM_STATUS = "draft"


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS (2025 i8962 PDF, 2026-06-14) — the integrity gate re-types
# ═══════════════════════════════════════════════════════════════════════════

# 2024 Federal Poverty Line (2025 returns use the PRIOR year). (base, increment).
FPL_2024 = {
    "contiguous": (15060, 5380),   # 48 states + DC (Table 1-1)
    "alaska": (18810, 6730),       # Table 1-2
    "hawaii": (17310, 6190),       # Table 1-3
}

# 2025 Table 5 repayment limitation: {band_upper: (single, other)}; >= 400 = no limit.
REPAYMENT_LIMIT_2025 = [
    (200, 375, 750),
    (300, 975, 1950),
    (400, 1625, 3250),
]


def fpl_amount(state_key: str, family_size: int) -> int:
    base, inc = FPL_2024[state_key]
    return base + max(0, family_size - 1) * inc


def fpl_pct(household_income, fpl) -> int:
    """Form 8962 line 5 — TRUNCATE(income / FPL x 100); cap 401 (> 400% eligible)."""
    if fpl <= 0:
        return 0
    pct = int((household_income / fpl) * 100)   # truncation, NOT rounding
    return 401 if pct > 400 else pct


def applicable_figure(line5_pct: int) -> str:
    """Table 2 — the required-contribution decimal, 4 places (verified endpoints/slopes)."""
    p = line5_pct
    if p < 150:
        fig = 0.0
    elif p < 200:
        fig = (p - 150) * 0.0004
    elif p < 250:
        fig = 0.0200 + (p - 200) * 0.0004
    elif p < 300:
        fig = 0.0400 + (p - 250) * 0.0004
    elif p < 400:
        fig = 0.0600 + (p - 300) * 0.00025
    else:
        fig = 0.0850
    return f"{round(fig, 4):.4f}"


def repayment_limit(line5_pct: int, filing_status: str):
    """Table 5 — the repayment cap; None (no limit) at >= 400% FPL."""
    if line5_pct >= 400:
        return None
    single = (filing_status or "").lower() == "single"
    for upper, s, o in REPAYMENT_LIMIT_2025:
        if line5_pct < upper:
            return s if single else o
    return None


def monthly_ptc(premium, slcsp, monthly_contribution):
    """Per-month PTC (cols a/b/c → d/e): min(premium, max(0, SLCSP − contribution))."""
    max_assist = max(0, slcsp - monthly_contribution)
    return min(premium, max_assist)


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("premium_tax_credit", "Premium Tax Credit (§36B) — Form 8962 reconciliation; net PTC → Sch 3 line 9 / excess APTC → Sch 2 line 1a"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_1040_FORM",
    "IRS_2025_1040_INSTR",
]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_F8962_INSTR",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Form 8962 — Premium Tax Credit (PTC)",
        "citation": "Instructions for Form 8962 (2025); i8962; Form 8962 Attachment Sequence No. 73",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i8962.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": "Table 2 applicable figure + the 2024 FPL Tables 1-1/1-2/1-3 + Table 5 repayment limitation + the monthly method. REQUIRES HUMAN REVIEW: confirm the full Table 2 lookup vs the interpolation + the line numbers vs the 2025 form.",
        "topics": ["premium_tax_credit"],
        "excerpts": [
            {
                "excerpt_label": "Line 5 + the applicable figure (2025)",
                "location_reference": "i8962 (2025), lines 5/7 + Table 2",
                "excerpt_text": (
                    "Line 5: divide line 3 by line 4, multiply by 100, and drop any numbers after the "
                    "decimal point; if the result is more than 400, enter 401. For 2025, taxpayers with "
                    "household income over 400% of the federal poverty line may be allowed a PTC. Table 2: "
                    "the applicable figure is 0.0000 below 150%, rising to 0.0200 at 200%, 0.0400 at 250%, "
                    "0.0600 at 300%, and 0.0850 at 400% and above."
                ),
                "summary_text": "Line 5 = trunc(income/FPL x 100), cap 401 (no cliff 2025). Table 2: 0% <150% -> 8.5% at 400%+.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Table 5 repayment limitation (2025)",
                "location_reference": "i8962 (2025), Table 5",
                "excerpt_text": (
                    "IF Form 8962 line 5 is less than 200, enter $375 (single) / $750 (other); at least 200 "
                    "but less than 300, $975 / $1,950; at least 300 but less than 400, $1,625 / $3,250; 400 "
                    "or more, leave line 28 blank. Line 29 = the smaller of line 27 or line 28; enter on "
                    "Schedule 2 (Form 1040), line 1a."
                ),
                "summary_text": "Repayment cap by FPL%/status: 375/750, 975/1,950, 1,625/3,250; no limit >=400%. Line 29 -> Sch 2 line 1a.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "2024 FPL tables (2025 returns)",
                "location_reference": "i8962 (2025), Tables 1-1/1-2/1-3",
                "excerpt_text": (
                    "For 2025 the 2024 federal poverty lines are used. 48 states + DC: family of 1 $15,060, "
                    "add $5,380 per additional person. Alaska: 1 $18,810, +$6,730. Hawaii: 1 $17,310, +$6,190."
                ),
                "summary_text": "2024 FPL: 48-state $15,060/+$5,380; AK $18,810/+$6,730; HI $17,310/+$6,190.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_36B",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §36B — Refundable Credit for Coverage Under a Qualified Health Plan",
        "citation": "26 U.S.C. §36B (premium tax credit; §36B(b) the applicable percentage; §36B(f) reconciliation of advance payments)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/36B",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "The substantive PTC authority: §36B(b)(3)(A) applicable percentage (the ARPA/IRA enhancement through 2025); §36B(c)(1) household income / MAGI; §36B(f)(2) reconciliation + the repayment limitation.",
        "topics": ["premium_tax_credit"],
        "excerpts": [
            {
                "excerpt_label": "§36B(f) reconciliation + repayment limitation",
                "location_reference": "26 U.S.C. §36B(f)(2)",
                "excerpt_text": (
                    "§36B(f)(2)(A): if the advance payments exceed the allowed credit, the tax is increased by "
                    "the excess. §36B(f)(2)(B): the increase is limited (for households under 400% of the "
                    "poverty line) to the applicable dollar amount; the limitation does not apply at or above "
                    "400%. The ARPA/IRA enhanced applicable-percentage table applies through 2025."
                ),
                "summary_text": "§36B(f): reconcile APTC vs PTC; repayment limited under 400% FPL; enhanced table through 2025.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_PUB_974",
        "source_type": "official_guidance",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRS Publication 974 — Premium Tax Credit (the SE health insurance iterative)",
        "citation": "Pub. 974 — Self-Employed Health Insurance Deduction and PTC (the iterative/simplified calculations)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/p974.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": False,
        "trust_score": 9.00,
        "requires_human_review": True,
        "notes": "The SE-health-insurance-deduction <-> PTC circular: the SEHI deduction reduces MAGI which raises PTC which caps the SEHI deduction. The iterative (and simplified) methods. REQUIRES HUMAN REVIEW: confirm the convergence + the simplified-method election.",
        "topics": ["premium_tax_credit"],
        "excerpts": [
            {
                "excerpt_label": "The SEHI <-> PTC iterative calculation",
                "location_reference": "Pub. 974, 'Self-Employed Health Insurance Deduction'",
                "excerpt_text": (
                    "If you are self-employed and claim the SE health insurance deduction for Marketplace "
                    "coverage, the deduction and the PTC are interrelated: the deduction reduces MAGI, which "
                    "may increase the PTC, which reduces the deductible premiums. Use the iterative "
                    "calculation (repeat until the deduction changes by no more than $1) or the simplified "
                    "calculation in this publication."
                ),
                "summary_text": "SEHI deduction <-> PTC loop until the deduction changes by <= $1 (or the simplified method).",
                "is_key_excerpt": True,
            },
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_F8962_INSTR", "FORM_8962", "governs"),
    ("IRC_36B", "FORM_8962", "governs"),
    ("IRS_PUB_974", "FORM_8962", "informs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM: FORM_8962
# ═══════════════════════════════════════════════════════════════════════════

F8962_IDENTITY = {
    "form_number": "FORM_8962",
    "form_title": "Form 8962 — Premium Tax Credit (PTC) (TY2025)",
    "notes": (
        "Ken's 4 scope decisions 2026-06-14 (post-sprint NEXT-UP #7). Real IRS "
        "face, ONE per return. Reconciles APTC vs the actual PTC: household income "
        "MAGI -> FPL% -> applicable figure (Table 2) -> annual/monthly contribution "
        "-> the monthly method (lines 12-23: PTC = min(premium, SLCSP - "
        "contribution)) -> net PTC (line 26 -> Schedule 3 line 9) OR excess APTC "
        "(line 27, repayment-limited by Table 5 -> line 29 -> Schedule 2 line 1a). "
        "v1 = FULL monthly + the iterative SEHI<->PTC (Pub 974) + Part 4 (shared "
        "allocation) + Part 5 (year-of-marriage). 2026 RED-deferred (the ARPA/IRA "
        "enhancement expires after 2025). 1095-A monthly data rides a new model."
    ),
}

F8962_FACTS: list[dict] = [
    # ── Inputs ──
    {"fact_key": "f8962_dependents_magi", "label": "MAGI of dependents required to file",
     "data_type": "decimal", "default_value": "0", "sort_order": 1,
     "notes": "Added to the taxpayer (+spouse) MAGI for household income (line 2b). v1 = preparer fact."},
    {"fact_key": "f8962_state", "label": "State (for the FPL table)",
     "data_type": "string", "default_value": "contiguous", "sort_order": 2,
     "notes": "contiguous / alaska / hawaii -> the 2024 FPL Table 1-1/1-2/1-3."},
    {"fact_key": "f8962_all_year_same", "label": "Same plan/SLCSP/family all 12 months?",
     "data_type": "boolean", "default_value": "false", "sort_order": 3,
     "notes": "Line 10 routing: Yes -> the annual line 11; No -> the monthly lines 12-23."},
    {"fact_key": "f8962_shared_allocation", "label": "Allocating policy amounts (Part 4)?",
     "data_type": "boolean", "default_value": "false", "sort_order": 4,
     "notes": "Decision 4. Part 4 shared policy allocation (divorced/shared 1095-A)."},
    {"fact_key": "f8962_marriage_alt", "label": "Alternative calc for the year of marriage (Part 5)?",
     "data_type": "boolean", "default_value": "false", "sort_order": 5,
     "notes": "Decision 4. Part 5."},
    {"fact_key": "f8962_se_sehi", "label": "Self-employed with Marketplace SE health insurance?",
     "data_type": "boolean", "default_value": "false", "sort_order": 6,
     "notes": "Decision 2. Triggers the Pub 974 SEHI<->PTC iterative."},
    # ── Outputs ──
    {"fact_key": "f8962_household_income", "label": "Line 3 — household income (MAGI)",
     "data_type": "decimal", "sort_order": 20, "notes": "OUTPUT. taxpayer (+spouse) MAGI + dependents' MAGI."},
    {"fact_key": "f8962_fpl", "label": "Line 4 — federal poverty line",
     "data_type": "decimal", "sort_order": 21, "notes": "OUTPUT. 2024 FPL by state + family size."},
    {"fact_key": "f8962_fpl_pct", "label": "Line 5 — household income as % of FPL",
     "data_type": "integer", "sort_order": 22, "notes": "OUTPUT. trunc(line3/line4 x 100), cap 401."},
    {"fact_key": "f8962_applicable_figure", "label": "Line 7 — applicable figure",
     "data_type": "decimal", "sort_order": 23, "notes": "OUTPUT. Table 2 by line 5 (4 decimals)."},
    {"fact_key": "f8962_annual_contribution", "label": "Line 8a — annual contribution amount",
     "data_type": "decimal", "sort_order": 24, "notes": "OUTPUT. round(line3 x line7)."},
    {"fact_key": "f8962_monthly_contribution", "label": "Line 8b — monthly contribution amount",
     "data_type": "decimal", "sort_order": 25, "notes": "OUTPUT. round(line8a / 12)."},
    {"fact_key": "f8962_total_ptc", "label": "Line 24 — total premium tax credit",
     "data_type": "decimal", "sort_order": 26, "notes": "OUTPUT. Σ monthly PTC (or the annual 11e)."},
    {"fact_key": "f8962_aptc", "label": "Line 25 — advance payment of PTC",
     "data_type": "decimal", "sort_order": 27, "notes": "OUTPUT. Σ APTC (col f / 1095-A col C)."},
    {"fact_key": "f8962_net_ptc", "label": "Line 26 — net premium tax credit -> Schedule 3 line 9",
     "data_type": "decimal", "sort_order": 28, "notes": "OUTPUT. line24 - line25 when > 0."},
    {"fact_key": "f8962_excess_aptc", "label": "Line 27 — excess advance PTC",
     "data_type": "decimal", "sort_order": 29, "notes": "OUTPUT. line25 - line24 when > 0."},
    {"fact_key": "f8962_repayment", "label": "Line 29 — excess APTC repayment -> Schedule 2 line 1a",
     "data_type": "decimal", "sort_order": 30, "notes": "OUTPUT. min(line27, Table-5 limit); no limit >= 400%."},
]

F8962_RULES: list[dict] = [
    {"rule_id": "R-8962-FAMILY-SIZE", "title": "Line 1 — tax family size", "rule_type": "calculation",
     "precedence": 1, "sort_order": 1,
     "formula": "line 1 = taxpayer + spouse (if not MFS) + dependents claimed.",
     "inputs": [], "outputs": [], "description": "§36B(d)(1). Drives the FPL lookup."},
    {"rule_id": "R-8962-HOUSEHOLD-INCOME", "title": "Lines 2a/2b/3 — household income (MAGI)", "rule_type": "calculation",
     "precedence": 2, "sort_order": 2,
     "formula": ("line 2a = taxpayer (+spouse) MAGI = AGI + tax-exempt interest (1040 2a) + excluded foreign "
                 "earned income (Form 2555) + non-taxable SS (1040 6a − 6b); line 2b = f8962_dependents_magi; "
                 "line 3 = 2a + 2b."),
     "inputs": ["f8962_dependents_magi"], "outputs": ["f8962_household_income"],
     "description": "§36B(d)(2). The 8962 MAGI add-backs."},
    {"rule_id": "R-8962-FPL", "title": "Line 4 — federal poverty line (2024)", "rule_type": "calculation",
     "precedence": 3, "sort_order": 3,
     "formula": ("line 4 = FPL_2024[state][base] + (family_size − 1) × increment. 48 states $15,060/+$5,380; "
                 "Alaska $18,810/+$6,730; Hawaii $17,310/+$6,190. 2025 returns use the 2024 FPL."),
     "inputs": ["f8962_state"], "outputs": ["f8962_fpl"],
     "description": "PRIOR-year FPL. Verified i8962 Tables 1-1/1-2/1-3."},
    {"rule_id": "R-8962-FPL-PCT", "title": "Line 5 — % of FPL (truncated, cap 401)", "rule_type": "calculation",
     "precedence": 4, "sort_order": 4,
     "formula": "line 5 = TRUNCATE(line 3 / line 4 × 100); if > 400 enter 401. The 400% cliff is SUSPENDED for 2025.",
     "inputs": [], "outputs": ["f8962_fpl_pct"],
     "description": "Truncation (NOT rounding). >400% still eligible (2025)."},
    {"rule_id": "R-8962-APPLICABLE-FIGURE", "title": "Line 7 — applicable figure (Table 2)", "rule_type": "calculation",
     "precedence": 5, "sort_order": 5,
     "formula": ("line 7 = Table 2(line 5): 0.0000 <150%; +0.0004/pt 150-300% (0.0200 at 200, 0.0400 at 250, "
                 "0.0600 at 300); +0.00025/pt 300-400% (0.0850 at 400); 0.0850 >=400%. Round 4 decimals."),
     "inputs": [], "outputs": ["f8962_applicable_figure"],
     "description": "Decision 3 (2025 ARPA/IRA table). 2026 RED-deferred."},
    {"rule_id": "R-8962-CONTRIBUTION", "title": "Lines 8a/8b — contribution amount", "rule_type": "calculation",
     "precedence": 6, "sort_order": 6,
     "formula": "line 8a = ROUND(line 3 × line 7); line 8b = ROUND(line 8a / 12).",
     "inputs": [], "outputs": ["f8962_annual_contribution", "f8962_monthly_contribution"],
     "description": "The required contribution toward premiums."},
    {"rule_id": "R-8962-MONTHLY", "title": "Lines 12-23 — the monthly method", "rule_type": "calculation",
     "precedence": 7, "sort_order": 7,
     "formula": ("Per month (cols a-f): a = 1095-A premium; b = 1095-A SLCSP; c = monthly contribution (line "
                 "8b, or the alt for Part 5); d = max(0, b − c) max premium assistance; e = min(a, d) the "
                 "monthly PTC; f = 1095-A APTC. Decision 1 (full monthly). The annual line 11 = the "
                 "12-equal-months case."),
     "inputs": [], "outputs": [],
     "description": "Decision 1. Per-month PTC."},
    {"rule_id": "R-8962-RECONCILE", "title": "Lines 24-26 — net PTC -> Schedule 3 line 9", "rule_type": "calculation",
     "precedence": 8, "sort_order": 8,
     "formula": ("line 24 = Σ monthly PTC (col e) [or 11e]; line 25 = Σ APTC (col f) [or 11f]; line 26 (net "
                 "PTC) = line 24 − line 25 when > 0 -> Schedule 3 line 9."),
     "inputs": [], "outputs": ["f8962_total_ptc", "f8962_aptc", "f8962_net_ptc"],
     "description": "§36B(f). Net PTC -> Sch 3 line 9 (refundable)."},
    {"rule_id": "R-8962-REPAYMENT", "title": "Lines 27-29 — excess APTC repayment -> Schedule 2 line 1a", "rule_type": "calculation",
     "precedence": 9, "sort_order": 9,
     "formula": ("line 27 (excess APTC) = line 25 − line 24 when > 0; line 28 = Table 5 repayment limit by "
                 "line 5 + filing status (375/750, 975/1,950, 1,625/3,250; blank/no-limit >=400%); line 29 = "
                 "min(line 27, line 28) -> Schedule 2 line 1a."),
     "inputs": [], "outputs": ["f8962_excess_aptc", "f8962_repayment"],
     "description": "§36B(f)(2)(B). Repayment limited under 400% FPL."},
    {"rule_id": "R-8962-SEHI", "title": "SE health insurance <-> PTC iterative (Pub 974)", "rule_type": "calculation",
     "precedence": 10, "sort_order": 10,
     "formula": ("If f8962_se_sehi: loop { SEHI deduction (Sch 1 line 17) → MAGI → PTC → cap the deductible "
                 "premiums at premiums − PTC } until the deduction changes by <= $1. Removes the "
                 "compute_schedule_c.py:374 RED."),
     "inputs": ["f8962_se_sehi"], "outputs": [],
     "description": "Decision 2. Pub 974 iterative."},
    {"rule_id": "R-8962-PART4", "title": "Part 4 — shared policy allocation", "rule_type": "calculation",
     "precedence": 11, "sort_order": 11,
     "formula": ("If f8962_shared_allocation: allocate the 1095-A premium / SLCSP / APTC across tax families "
                 "by the agreed percentages (lines 30-33), per allocation period, before lines 11/12-23."),
     "inputs": ["f8962_shared_allocation"], "outputs": [],
     "description": "Decision 4. Part 4."},
    {"rule_id": "R-8962-PART5", "title": "Part 5 — alternative calculation for the year of marriage", "rule_type": "calculation",
     "precedence": 12, "sort_order": 12,
     "formula": ("If f8962_marriage_alt: compute each spouse's alternative family size + monthly contribution "
                 "for the pre-marriage months (Worksheets III/IV) to reduce excess APTC."),
     "inputs": ["f8962_marriage_alt"], "outputs": [],
     "description": "Decision 4. Part 5."},
    {"rule_id": "R-8962-2026-DEFER", "title": "2026 out of scope (the enhancement expires)", "rule_type": "routing",
     "precedence": 13, "sort_order": 13,
     "formula": ("tax_year == 2026 → D_8962_2026 RED. The ARPA/IRA enhancement (no cliff, the 0-8.5% table) "
                 "expires after 2025; the 2026 method (the 400% cliff + the pre-ARPA table) is legislatively "
                 "uncertain."),
     "inputs": [], "outputs": [],
     "description": "Decision 3. RED-defer 2026."},
]

F8962_LINES: list[dict] = [
    {"line_number": "1", "description": "1 Tax family size", "line_type": "input"},
    {"line_number": "2a", "description": "2a Modified AGI (taxpayer + spouse)", "line_type": "calculated"},
    {"line_number": "2b", "description": "2b Dependents' modified AGI", "line_type": "input"},
    {"line_number": "3", "description": "3 Household income (2a + 2b)", "line_type": "calculated"},
    {"line_number": "4", "description": "4 Federal poverty line (2024, by state + family size)", "line_type": "calculated"},
    {"line_number": "5", "description": "5 Household income as a % of FPL (truncated; 401 if > 400)", "line_type": "calculated"},
    {"line_number": "7", "description": "7 Applicable figure (Table 2)", "line_type": "calculated"},
    {"line_number": "8a", "description": "8a Annual contribution amount (line 3 × line 7)", "line_type": "calculated"},
    {"line_number": "8b", "description": "8b Monthly contribution amount (line 8a / 12)", "line_type": "calculated"},
    {"line_number": "9", "description": "9 Allocating policy amounts (Part 4) or marriage alt (Part 5)?", "line_type": "input"},
    {"line_number": "10", "description": "10 Same monthly amounts all 12 months? (annual vs monthly)", "line_type": "input"},
    {"line_number": "11a", "description": "11a Annual — enrollment premiums", "line_type": "calculated"},
    {"line_number": "11b", "description": "11b Annual — SLCSP premium", "line_type": "calculated"},
    {"line_number": "11c", "description": "11c Annual — monthly contribution (line 8b)", "line_type": "calculated"},
    {"line_number": "11d", "description": "11d Annual — maximum premium assistance (11b − 11c)", "line_type": "calculated"},
    {"line_number": "11e", "description": "11e Annual — premium tax credit (min 11a, 11d)", "line_type": "calculated"},
    {"line_number": "11f", "description": "11f Annual — advance payment of PTC", "line_type": "calculated"},
    {"line_number": "12", "description": "12 January (a premium / b SLCSP / c contribution / d / e PTC / f APTC)", "line_type": "calculated"},
    {"line_number": "13", "description": "13 February (a-f)", "line_type": "calculated"},
    {"line_number": "14", "description": "14 March (a-f)", "line_type": "calculated"},
    {"line_number": "15", "description": "15 April (a-f)", "line_type": "calculated"},
    {"line_number": "16", "description": "16 May (a-f)", "line_type": "calculated"},
    {"line_number": "17", "description": "17 June (a-f)", "line_type": "calculated"},
    {"line_number": "18", "description": "18 July (a-f)", "line_type": "calculated"},
    {"line_number": "19", "description": "19 August (a-f)", "line_type": "calculated"},
    {"line_number": "20", "description": "20 September (a-f)", "line_type": "calculated"},
    {"line_number": "21", "description": "21 October (a-f)", "line_type": "calculated"},
    {"line_number": "22", "description": "22 November (a-f)", "line_type": "calculated"},
    {"line_number": "23", "description": "23 December (a-f)", "line_type": "calculated"},
    {"line_number": "24", "description": "24 Total premium tax credit (Σ 11e or 12e-23e)", "line_type": "calculated"},
    {"line_number": "25", "description": "25 Advance payment of PTC (Σ 11f or 12f-23f)", "line_type": "calculated"},
    {"line_number": "26", "description": "26 Net premium tax credit (24 − 25) → Schedule 3 line 9", "line_type": "total"},
    {"line_number": "27", "description": "27 Excess advance PTC (25 − 24)", "line_type": "calculated"},
    {"line_number": "28", "description": "28 Repayment limitation (Table 5)", "line_type": "calculated"},
    {"line_number": "29", "description": "29 Excess APTC repayment (min 27, 28) → Schedule 2 line 1a", "line_type": "total"},
    {"line_number": "30", "description": "30 Part IV — allocation 1 (policy / SSN / months / premium% / SLCSP% / APTC%)", "line_type": "input"},
    {"line_number": "35", "description": "35 Part V — alternative entries for your SSN (marriage)", "line_type": "input"},
    {"line_number": "36", "description": "36 Part V — alternative entries for spouse's SSN (marriage)", "line_type": "input"},
]

F8962_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_8962_2026", "title": "TY2026 PTC out of scope — the enhancement expires", "severity": "error",
     "condition": "tax_year == 2026 AND a 1095-A is present",
     "message": ("Not supported for 2026: the ARPA/IRA premium-tax-credit enhancement (no 400% cliff, the "
                 "0-8.5% applicable-percentage table) expires after 2025. The 2026 method (the 400% cliff "
                 "returns + the pre-ARPA table) is legislatively uncertain — prepare manually / re-verify "
                 "when the 2026 Form 8962 publishes (~Dec 2026)."),
     "notes": "Decision 3. The 2025-only RED-defer."},
    {"diagnostic_id": "D_8962_NET_PTC", "title": "Net premium tax credit → Schedule 3 line 9", "severity": "info",
     "condition": "f8962_net_ptc > 0",
     "message": ("The actual premium tax credit exceeds the advance payments; the net PTC is a refundable "
                 "credit on Schedule 3 line 9 (Form 1040 line 31)."),
     "notes": "§36B(f)."},
    {"diagnostic_id": "D_8962_REPAYMENT", "title": "Excess advance PTC repayment → Schedule 2 line 1a", "severity": "warning",
     "condition": "f8962_repayment > 0",
     "message": ("Advance PTC exceeded the allowed credit; the excess (limited by Table 5 when household "
                 "income is under 400% of the poverty line) is repaid on Schedule 2 line 1a."),
     "notes": "§36B(f)(2). The repayment."},
    {"diagnostic_id": "D_8962_NO_LIMIT", "title": "Income ≥ 400% FPL — full repayment, no limit", "severity": "warning",
     "condition": "f8962_fpl_pct >= 400 AND f8962_excess_aptc > 0",
     "message": ("Household income is at or above 400% of the federal poverty line, so the excess advance "
                 "PTC repayment is NOT limited by Table 5 — the entire excess is repaid (line 28 blank)."),
     "notes": "§36B(f)(2)(B). No cap >= 400%."},
    {"diagnostic_id": "D_8962_SEHI", "title": "SE health insurance / PTC iterative applied", "severity": "info",
     "condition": "f8962_se_sehi is True",
     "message": ("A self-employed Marketplace SE-health-insurance deduction interacts with the PTC (Pub 974) "
                 "— the deduction and the credit were computed iteratively to convergence. Verify the "
                 "Schedule 1 line 17 deduction + the net PTC."),
     "notes": "Decision 2. Pub 974."},
    {"diagnostic_id": "D_8962_NO_1095A", "title": "Advance PTC present but no Form 1095-A", "severity": "warning",
     "condition": "advance PTC indicated but no Form1095A row",
     "message": ("Advance premium tax credit was paid but no Form 1095-A is entered. Enter the Marketplace "
                 "statement (Form 1095-A) — the PTC cannot be reconciled without it."),
     "notes": "Due diligence."},
]

F8962_SCENARIOS: list[dict] = [
    {"scenario_name": "8962-T1 — net PTC (250% FPL, annual)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "filing_status": "single", "state": "contiguous", "family_size": 1,
                "household_income": 37650, "premium_annual": 7200, "slcsp_annual": 7800, "aptc_annual": 4000},
     "expected_outputs": {"f8962_fpl": 15060, "f8962_fpl_pct": 250, "f8962_applicable_figure": 0.04,
                          "f8962_annual_contribution": 1506, "f8962_total_ptc": 6294, "f8962_net_ptc": 2294},
     "notes": "FPL 15,060; 37,650/15,060=2.50 -> 250; AF 0.0400; contrib 1,506 (8b 126); annual PTC = min(7,200, 7,800−1,506=6,294)=6,294; net = 6,294 − 4,000 = 2,294 -> Sch 3 L9."},
    {"scenario_name": "8962-T2 — excess APTC, repayment limited (332% single)", "scenario_type": "edge_case", "sort_order": 2,
     "inputs": {"tax_year": 2025, "filing_status": "single", "state": "contiguous", "family_size": 1,
                "household_income": 50000, "premium_annual": 6000, "slcsp_annual": 6500, "aptc_annual": 5000},
     "expected_outputs": {"f8962_fpl_pct": 332, "f8962_applicable_figure": 0.068, "f8962_excess_aptc": 1900,
                          "f8962_repayment": 1625},
     "notes": "50,000/15,060=3.32 -> 332; AF 0.0600 + 32×0.00025 = 0.0680; contrib 8a=3,400; PTC = min(6,000, 6,500−3,400=3,100)=3,100; APTC 5,000 → excess 1,900; 300-400 single cap 1,625 binds -> repay 1,625."},
    {"scenario_name": "8962-T3 — over 400% FPL, still eligible (8.5%)", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "state": "contiguous", "family_size": 2,
                "household_income": 90000, "premium_annual": 14000, "slcsp_annual": 15000, "aptc_annual": 6000},
     "expected_outputs": {"f8962_fpl": 20440, "f8962_fpl_pct": 401, "f8962_applicable_figure": 0.085},
     "notes": "90,000/20,440=4.40 -> 401 (>400, no cliff 2025); AF 0.0850; contrib 7,650; PTC = min(14,000, 15,000−7,650=7,350)=7,350; net vs APTC computed in the gate."},
    {"scenario_name": "8962-T4 — applicable figure interpolation (175%)", "scenario_type": "edge_case", "sort_order": 4,
     "inputs": {"tax_year": 2025, "filing_status": "single", "state": "contiguous", "family_size": 1,
                "household_income": 26355},
     "expected_outputs": {"f8962_fpl_pct": 175, "f8962_applicable_figure": 0.01},
     "notes": "26,355/15,060=1.75 -> 175; AF = (175−150)×0.0004 = 0.0100."},
    {"scenario_name": "8962-T5 — repayment cap binds (<200% single -> $375)", "scenario_type": "edge_case", "sort_order": 5,
     "inputs": {"tax_year": 2025, "filing_status": "single", "state": "contiguous", "family_size": 1,
                "household_income": 28000, "premium_annual": 5000, "slcsp_annual": 1000, "aptc_annual": 1000},
     "expected_outputs": {"f8962_fpl_pct": 185, "f8962_applicable_figure": 0.014, "f8962_excess_aptc": 392,
                          "f8962_repayment": 375},
     "notes": "28,000/15,060=1.85 -> 185 (<200 -> single cap 375); AF 0.0140; contrib 8a=392; PTC = min(5,000, max(0, 1,000−392)=608)=608; APTC 1,000 → excess 392; cap 375 binds -> repay 375."},
    {"scenario_name": "8962-G1 — 2026 out of scope -> RED", "scenario_type": "diagnostic", "sort_order": 6,
     "inputs": {"tax_year": 2026, "filing_status": "single", "state": "contiguous", "family_size": 1,
                "household_income": 30000, "premium_annual": 6000, "slcsp_annual": 6500, "aptc_annual": 3000},
     "expected_outputs": {"D_8962_2026": True},
     "notes": "2026 → D_8962_2026 RED (the enhancement expires; out of scope)."},
]

F8962_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-8962-FAMILY-SIZE", "IRC_36B", "primary", "§36B(d)(1) family size"),
    ("R-8962-HOUSEHOLD-INCOME", "IRC_36B", "primary", "§36B(d)(2) household income / MAGI"),
    ("R-8962-HOUSEHOLD-INCOME", "IRS_2025_F8962_INSTR", "secondary", "Lines 2a/2b/3"),
    ("R-8962-FPL", "IRS_2025_F8962_INSTR", "primary", "The 2024 FPL Tables 1-1/1-2/1-3"),
    ("R-8962-FPL-PCT", "IRS_2025_F8962_INSTR", "primary", "Line 5 truncation + the 401 cap"),
    ("R-8962-APPLICABLE-FIGURE", "IRS_2025_F8962_INSTR", "primary", "Table 2 (the applicable figure)"),
    ("R-8962-CONTRIBUTION", "IRS_2025_F8962_INSTR", "primary", "Lines 8a/8b"),
    ("R-8962-MONTHLY", "IRS_2025_F8962_INSTR", "primary", "Lines 12-23 the monthly method"),
    ("R-8962-RECONCILE", "IRC_36B", "primary", "§36B(f) reconciliation → Sch 3 line 9"),
    ("R-8962-REPAYMENT", "IRS_2025_F8962_INSTR", "primary", "Table 5 → line 29 → Sch 2 line 1a"),
    ("R-8962-REPAYMENT", "IRC_36B", "secondary", "§36B(f)(2)(B) the repayment limitation"),
    ("R-8962-SEHI", "IRS_PUB_974", "primary", "The SEHI ↔ PTC iterative"),
    ("R-8962-PART4", "IRS_2025_F8962_INSTR", "primary", "Part IV shared policy allocation"),
    ("R-8962-PART5", "IRS_2025_F8962_INSTR", "primary", "Part V year-of-marriage alternative"),
    ("R-8962-2026-DEFER", "IRC_36B", "secondary", "§36B(b)(3)(A) the enhancement through 2025"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-8962-01", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "The 2024 FPL + Table 5 + the applicable-figure endpoints",
     "description": "Pins the 2024 FPL bases/increments, the Table 5 repayment caps, and the Table 2 endpoints. Bug it catches: a drifted FPL/cap or the wrong year's table.",
     "definition": {"kind": "constants_check", "form": "FORM_8962",
                    "constants": {"fpl_contiguous_base": 15060, "fpl_contiguous_inc": 5380,
                                  "fpl_alaska_base": 18810, "fpl_hawaii_base": 17310,
                                  "repay_single": [375, 975, 1625], "repay_other": [750, 1950, 3250],
                                  "af_200": 0.02, "af_300": 0.06, "af_400": 0.085}},
     "sort_order": 1},
    {"assertion_id": "FA-1040-8962-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Line 5 = truncate(income/FPL×100), cap 401; Table 2 interpolation",
     "description": "Validates R-8962-FPL-PCT + R-8962-APPLICABLE-FIGURE. Bug it catches: rounding instead of truncating, the 400% cliff wrongly applied, or a bad interpolation (175%→0.0100, 250%→0.0400).",
     "definition": {"kind": "formula_check", "form": "FORM_8962",
                    "formula": "line5 == trunc(line3/line4*100) capped 401; line7 == Table2(line5)"},
     "sort_order": 2},
    {"assertion_id": "FA-1040-8962-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Monthly PTC = min(premium, max(0, SLCSP − contribution))",
     "description": "Validates R-8962-MONTHLY. Bug it catches: the contribution not subtracted, or a negative max-assistance not floored at 0.",
     "definition": {"kind": "formula_check", "form": "FORM_8962",
                    "formula": "monthly_ptc == min(premium, max(0, slcsp - monthly_contribution))"},
     "sort_order": 3},
    {"assertion_id": "FA-1040-8962-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Net PTC → Sch 3 line 9; excess repayment → Sch 2 line 1a",
     "description": "Validates R-8962-RECONCILE + R-8962-REPAYMENT. Bug it catches: net PTC not landing on Sch 3 line 9, or the repayment not landing/limited on Sch 2 line 1a.",
     "definition": {"kind": "flow_assertion", "form": "FORM_8962",
                    "checks": [{"source_line": "26", "must_write_to": ["SCH_3.9"]},
                               {"source_line": "29", "must_write_to": ["SCH_2.1a"]}]},
     "sort_order": 4},
    {"assertion_id": "FA-1040-8962-05", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "Repayment limited under 400%; full repayment ≥ 400%",
     "description": "Validates R-8962-REPAYMENT. Bug it catches: the Table 5 cap applied at ≥400% (should be no limit), or the wrong column (single vs other).",
     "definition": {"kind": "reconciliation", "form": "FORM_8962",
                    "formula": "line29 == min(line27, Table5(line5, status)); no cap when line5 >= 400"},
     "sort_order": 5},
    {"assertion_id": "FA-1040-8962-06", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Gates: 2026 RED; SEHI iterative; no-1095-A",
     "description": "A 2026 return fires D_8962_2026 (out of scope); the SE-SEHI flag triggers the Pub 974 iterative (D_8962_SEHI).",
     "definition": {"kind": "gating_check", "form": "FORM_8962", "expect": {"red_fires": True},
                    "blockers": ["tax_year_2026"]},
     "sort_order": 6},
]


FORMS: list[dict] = [
    {"identity": F8962_IDENTITY, "facts": F8962_FACTS, "rules": F8962_RULES, "lines": F8962_LINES,
     "diagnostics": F8962_DIAGNOSTICS, "scenarios": F8962_SCENARIOS, "rule_links": F8962_RULE_LINKS},
]


class Command(BaseCommand):
    help = "Load the FORM_8962 spec (Premium Tax Credit). Refuses until READY_TO_SEED=True."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad FORM_8962 spec (Premium Tax Credit)\n"))
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
                "\nREFUSING TO SEED FORM_8962: not cleared to seed.\n\n"
                "Gated until Ken's review walk (Table 2 + the 2024 FPL + Table 5 + the monthly\n"
                "method + the iterative SEHI<->PTC + Parts 4/5).\n\n"
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
        form = TaxForm.objects.filter(form_number="FORM_8962").first()
        if form:
            uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
            self.stdout.write("FORM_8962: all rules cited" if not uncited
                              else self.style.WARNING(f"FORM_8962 uncited rules: {len(uncited)}"))
