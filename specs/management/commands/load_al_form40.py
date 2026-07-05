"""Load the AL Form 40 spec — Alabama Individual Income Tax Return (TY2025).

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
Alabama Form 40 is the full-year / part-year resident individual income tax
return. UNLIKE GA Form 500 (federal AGI start) and SC1040 (federal taxable
income start), AL Form 40 builds ALABAMA GROSS INCOME FROM SCRATCH — wages
(from AL Schedule W-2), interest/dividends, and other income — reaches Alabama
AGI (line 10), then subtracts four deductions (itemized/standard, the FEDERAL
INCOME TAX DEDUCTION, personal exemption, dependent exemption) to taxable
income, a 2/4/5% graduated tax, credits (Schedule OC), payments → refund/due.

Alabama's signature feature: the **FEDERAL INCOME TAX DEDUCTION (line 12)** —
one of the few states that lets individuals deduct federal income tax. It is a
worksheet, liability-based, separate from the itemized/standard election.

3rd STATE individual spec (GA Form 500, SC1040 precede it; load_sc1040.py +
load_ga500_form_500.py are the structural precedents). Attaches to the child
1040 return in tts via TaxReturn.federal_return / state_returns.

NO prior RS spec exists (lookup/AL_FORM_40/ → 404). NEW form.

═══════════════════════════════════════════════════════════════════════════
v1 SCOPE — LOCKED (Ken's walk 2026-07-04, 4 AskUserQuestion decisions)
See al_form40_source_brief.md §11.
═══════════════════════════════════════════════════════════════════════════
COMPUTES (v1):
  • Full-year + PART-YEAR resident Form 40 (Form 40 covers both natively — no
    separate schedule needed for part-year; Dec A).
  • AL gross income build: wages (Sch W-2) + interest/dividends + other income
    (Part I) → L8 total income; Part II adjustments → L10 Alabama AGI.
  • THE FEDERAL INCOME TAX DEDUCTION (L12) — full worksheet (Dec B): (1040 L22 +
    NIIT Form 8960 L17) − refundable credits (EIC 27a + ACTC 28 + AOC 29 +
    refundable adoption 30 + Form 2439), floored at 0; PART-YEAR APPORTIONMENT =
    federal tax × (AL AGI ÷ federal AGI).
  • The AGI-keyed SLIDING SCALES (Dec C): standard deduction (per-status max −
    step per AGI band, floored) + dependent exemption ($1,000/$500/$300 at
    $50k/$100k AL AGI); personal exemption ($1,500/$3,000).
  • The 2/4/5% graduated tax (L16 → L17); the §414(j)/SS/government-pension
    income EXCLUSIONS (handled at the income build — "do not report").

DIRECT-ENTRY (line exists, diagnostic prompts):                              [Dec D]
  • Schedule OC credits (L18 net / L25 refundable) — incl. Credit for Taxes Paid
    to Other States (needs other-state/MAT data); itemized deduction (L11 Box a);
    Part II niche adjustments not modeled.

RED-DEFERS (each its own "prepare manually" RED — no silent gap):            [Dec D]
  • Form 40NR (nonresident) — D_AL40_40NR.
  • Schedule ATP additional taxes (consumer use / catastrophe savings, L19) +
    penalties (L31) — D_AL40_ATP.
  • Form NOL-85A net operating loss (L17 alternative) — D_AL40_NOL.

═══════════════════════════════════════════════════════════════════════════
requires_human_review WALK ITEMS (for Ken's in-session review before seeding)
═══════════════════════════════════════════════════════════════════════════
W1. STANDARD-DEDUCTION SLIDING SCALE encoded as a FORMULA (per-status max − step
    × ceil(max(0, AGI − max-band-top) / band-size), floored), NOT a transcribed
    cell table — this SIDESTEPS the one OCR-suspect MFJ cell in the booklet
    ($26,500-$26,999 → $8,150). CONFIRM the four (max, step, band, floor,
    max-band-top) tuples reproduce the DOR chart at a couple of AGI points.
W2. RATE SCHEDULE (2/4/5%) sourced from Ala. Code §40-18-5 (Justia) + verified
    arithmetically against the DOR tax table (not a verbatim booklet bracket
    quote). Statute unchanged for 2025. CONFIRM.
W3. FIT DEDUCTION "paid or accrued" (§40-18-15) vs the WORKSHEET. The statute
    frames it as federal tax "paid or accrued"; the Form 40 figure is
    LIABILITY-BASED (current-year 1040 L22 worksheet), no cash/accrual election
    on the resident form. Spec computes the worksheet number; cite §40-18-15 for
    the characterization. CONFIRM this is the right basis for v1.
W4. FIT WORKSHEET FEDERAL LINE NUMBERS (1040 L22; 8960 L17; 27a/28/29/30; 2439)
    are the 2025 layout; the booklet warns federal line numbers "may change."
    CONFIRM the tts federal handoff maps these correctly.
W5. Schedule OC per-credit caps + Form 40NR line map NOT verified (out of v1
    scope — direct-entry OC / RED-defer 40NR). Revisit if either enters scope.

═══════════════════════════════════════════════════════════════════════════
VERIFIED STRUCTURE + CONSTANTS (READ 2026-07-04 from the FINAL 2025 AL DOR PDFs —
NOT memory: Form 40 25f40blk.pdf; Booklet 25f40bk.pdf incl. the p.31 FIT
worksheet + the p.8 std-ded chart + tax tables; Ala. Code §40-18-5 / §40-18-15.
Full source brief: al_form40_source_brief.md.)
═══════════════════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════════════════
SAFETY GUARD — READY_TO_SEED stays False until Ken approves the review walk
(W1-W5) in-session. Until then the command refuses to write to the DB.
DO NOT relax the guard to silence the error.
═══════════════════════════════════════════════════════════════════════════
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

# ═══════════════════════════════════════════════════════════════════════════
# SAFETY GUARD — flip ONLY after Ken's in-session review walk (W1-W5 above).
#
# FLIPPED 2026-07-04 — Ken APPROVED the review walk in-session ("seed + export
# now"): W1 std-deduction sliding-scale formula (verified at several AGI points),
# W2 the §40-18-5 rate (tax-table-confirmed), W3 the FIT worksheet basis, W4 the
# federal handoff line numbers, W5 the OC caps / 40NR defer — all blessed as
# in-spec re-verify flags. Validated on a throwaway DB.
# ═══════════════════════════════════════════════════════════════════════════
READY_TO_SEED = True


FORM_JURISDICTION = "AL"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1040"]


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS (year-keyed; cited in al_form40_source_brief.md; never memory)
# ═══════════════════════════════════════════════════════════════════════════

# Rate schedule (§40-18-5). Brackets by filing-status group. (bracket_top, rate).
AL_RATES_SINGLE: dict[int, list] = {2025: [(500, "0.02"), (3000, "0.04"), (None, "0.05")]}   # single/MFS/HOF
AL_RATES_MFJ: dict[int, list] = {2025: [(1000, "0.02"), (6000, "0.04"), (None, "0.05")]}

# Standard deduction sliding scale (booklet p.8). Per status:
#   {max_ded, max_band_top (AGI at/below which max applies), step, band_size, floor}
#   ded = max(floor, max_ded − step × ceil(max(0, AGI − max_band_top) / band_size))
AL_STD_DED: dict[int, dict] = {2025: {
    "MFJ":    {"max": 8500, "max_band_top": 25999, "step": 175, "band": 500, "floor": 5000},
    "MFS":    {"max": 4250, "max_band_top": 12999, "step": 88,  "band": 250, "floor": 2500},
    "HOF":    {"max": 5200, "max_band_top": 25999, "step": 135, "band": 500, "floor": 2500},
    "single": {"max": 3000, "max_band_top": 25999, "step": 25,  "band": 500, "floor": 2500},
}}

# Personal exemption (form face).
AL_PERSONAL_EXEMPTION: dict[int, dict] = {2025: {"single": 1500, "MFJ": 3000, "MFS": 1500, "HOF": 3000}}

# Dependent exemption sliding scale by AL AGI (booklet): (agi_ceiling, per_dependent).
AL_DEPENDENT_EXEMPTION: dict[int, list] = {2025: [(50000, 1000), (100000, 500), (None, 300)]}

# Severance/downsizing income exclusion cap (TY2020+).
AL_SEVERANCE_EXCLUSION_CAP: dict[int, int] = {2025: 50000}


def _yk(d: dict, year: int):
    return d.get(year) if d.get(year) is not None else d[2025]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY TOPICS / SOURCES
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("al_income_tax", "Alabama Form 40 individual income tax: builds AL gross income from scratch, "
     "the federal income tax deduction (line 12), 2/4/5% graduated rate, sliding-scale standard "
     "deduction + dependent exemption, and §414(j)/SS/government-pension exclusions."),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_1040_FORM",  # the FIT deduction pulls 1040 L22 + 8960 L17 − refundable credits (27a/28/29/30/2439)
]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "AL_2025_FORM_40",
        "source_type": "state_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "AL",
        "title": "2025 Alabama Form 40 — Individual Income Tax Return (Residents & Part-Year Residents)",
        "citation": "Alabama Form 40 (2025), 25f40blk.pdf",
        "issuer": "Alabama Department of Revenue",
        "official_url": "https://www.revenue.alabama.gov/wp-content/uploads/2026/01/25f40blk.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["al_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "Form 40 face (2025) — verified line map",
                "excerpt_text": (
                    "5a AL income tax withheld; 5b Wages (AL Schedule W-2); 6 Interest & dividend "
                    "income; 7 Other income (pg2 Part I L8); 8 Total income (5b-7); 9 Total adjustments "
                    "(pg2 Part II L16); 10 Adjusted gross income = L8 − L9. 11 Itemized OR Standard "
                    "deduction (election); 12 FEDERAL TAX DEDUCTION (see instructions; 'DO NOT ENTER THE "
                    "FEDERAL TAX WITHHELD FROM YOUR W-2(S)'); 13 Personal exemption; 14 Dependent "
                    "exemption (pg2 Part III); 15 Total deductions (11+12+13+14); 16 Taxable income = "
                    "L10 − L15; 17 Income Tax due (tax table / NOL-85A); 18 Net tax (Schedule OC); 19 "
                    "Additional taxes (Sch ATP); 20a/b campaign fund; 21 Total liability; 22 AL "
                    "withholding; 23 estimated/extension; 25 refundable credits (Sch OC F6); 27 total "
                    "payments; 30 AMOUNT YOU OWE; 31 penalties (Sch ATP); 32 overpaid; 35 REFUND."
                ),
                "summary_text": "Form 40 (2025): AL gross income (no federal-AGI start) → AL AGI (L10) → 4 deductions incl. federal tax (L12) → taxable income → 2/4/5% tax → credits → refund/due.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Personal & dependent exemptions (form face + booklet)",
                "excerpt_text": (
                    "Personal exemption (L13): Single $1,500; Married filing joint $3,000; Married "
                    "filing separate $1,500; Head of Family $3,000. Dependent exemption (L14), sliding "
                    "by AL AGI (page 1 line 10): AGI 0-50,000 → $1,000/dependent; 50,001-100,000 → "
                    "$500; over 100,000 → $300. × number of dependents (Part III)."
                ),
                "summary_text": "Personal exemption $1,500/$3,000; dependent exemption sliding $1,000/$500/$300 at $50k/$100k AL AGI.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Income exclusions — 'You DO NOT Report'",
                "excerpt_text": (
                    "Fully excluded from Alabama income: distributions from a Defined Benefit Retirement "
                    "Plan (IRC §414(j)); federal Social Security; US/Alabama government retirement "
                    "(Teachers'/Employees'/Judicial); state income-tax refunds; unemployment; VA/welfare/"
                    "disability; combat pay; certain military allowances; law-enforcement subsistence; up "
                    "to $50,000 severance/downsizing income (TY2020+). NO general age-65 or $6,000 "
                    "retirement exclusion exists in Alabama."
                ),
                "summary_text": "§414(j) defined-benefit pensions + SS + government pensions + state refunds fully excluded (not reported); no general age-65 exclusion.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "AL_2025_FORM_40_BOOKLET",
        "source_type": "state_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "AL",
        "title": "2025 Alabama Form 40 Booklet — Instructions, Tax Tables, Worksheets",
        "citation": "Alabama Form 40 Booklet (2025), 25f40bk.pdf (updated Jan 2026)",
        "issuer": "Alabama Department of Revenue",
        "official_url": "https://www.revenue.alabama.gov/wp-content/uploads/2026/01/25f40bk.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["al_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "Federal Income Tax Deduction Worksheet (booklet p.31, verbatim)",
                "excerpt_text": (
                    "1 Enter the tax as shown on line 22 of 2025 Form 1040/1040-SR/1040-NR. 2 Net "
                    "Investment Income Tax — amount from line 17, 2025 Form 8960. 3 Federal Tax = line 1 "
                    "+ line 2. 4a Earned Income Credit — 1040 line 27a. 4b Additional Child Tax Credit — "
                    "1040 line 28. 4c American Opportunity Credit — 1040 line 29. 4d Refundable Adoption "
                    "Credit — 1040 line 30. 4e Form 2439 credits — Schedule 3 Part II line 13a. 5 = 4a+"
                    "4b+4c+4d+4e. 6 = line 3 − line 5; if negative enter zero; enter on line 12 of Form "
                    "40. Part-year/nonresident + joint-federal/separate-Alabama: apportion the federal "
                    "tax by the ratio of Alabama AGI to federal AGI."
                ),
                "summary_text": "FIT deduction (L12) = (1040 L22 + NIIT 8960 L17) − (EIC 27a + ACTC 28 + AOC 29 + refundable adoption 30 + 2439), floored 0; apportioned AL-AGI/federal-AGI for PY/NR.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Standard deduction chart (booklet p.8) — sliding by AL AGI",
                "excerpt_text": (
                    "Standard deduction phases down as Alabama AGI (line 10) rises, by filing status. "
                    "MFJ: max $8,500 (AGI ≤ $25,999), −$175 per $500 AGI band, floor $5,000 (AGI ≥ "
                    "$35,500). MFS: max $4,250 (≤ $12,999), −$88 per $250 band, floor $2,500 (≥ "
                    "$17,750). Head of Family: max $5,200 (≤ $25,999), −$135 per $500 band, floor $2,500 "
                    "(≥ $35,500). Single: max $3,000 (≤ $25,999), −$25 per $500 band, floor $2,500 (≥ "
                    "$35,500)."
                ),
                "summary_text": "Std ded sliding scale: MFJ $8,500→$5,000; MFS $4,250→$2,500; HOF $5,200→$2,500; Single $3,000→$2,500.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "AL_CODE_40_18_5",
        "source_type": "state_statute",
        "source_rank": "controlling",
        "jurisdiction_code": "AL",
        "title": "Ala. Code §40-18-5 — Individual income tax rates (2/4/5%)",
        "citation": "Ala. Code §40-18-5 (2025)",
        "issuer": "Alabama Legislature",
        "official_url": "https://law.justia.com/codes/alabama/title-40/chapter-18/article-1/section-40-18-5/",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.4,
        "topics": ["al_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "AL graduated rate (2025)",
                "excerpt_text": (
                    "Single / MFS / Head of Family: 2% on the first $500 of taxable income; 4% on the "
                    "next $2,500 (over $500, ≤ $3,000); 5% on taxable income over $3,000. Married filing "
                    "jointly: 2% on the first $1,000; 4% on the next $5,000 (over $1,000, ≤ $6,000); 5% "
                    "over $6,000. No 2025 rate change (verified arithmetically against the DOR tax table)."
                ),
                "summary_text": "2/4/5% brackets: single 500/3000; MFJ 1000/6000.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "AL_CODE_40_18_15",
        "source_type": "state_statute",
        "source_rank": "controlling",
        "jurisdiction_code": "AL",
        "title": "Ala. Code §40-18-15 — Deductions (federal income tax paid or accrued)",
        "citation": "Ala. Code §40-18-15 (2025)",
        "issuer": "Alabama Legislature",
        "official_url": "https://law.justia.com/codes/alabama/title-40/chapter-18/article-1/section-40-18-15/",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.0,
        "topics": ["al_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "Federal income tax deduction — statutory basis",
                "excerpt_text": (
                    "§40-18-15 allows individuals a deduction for federal income taxes paid or accrued "
                    "within the taxable year. The Form 40 mechanical figure is liability-based (the "
                    "current-year 1040 line 22 worksheet); the 'paid or accrued' language is the "
                    "statutory characterization (W3)."
                ),
                "summary_text": "§40-18-15: federal income tax 'paid or accrued' deductible; Form 40 computes it liability-based via the p.31 worksheet.",
                "is_key_excerpt": True,
            },
        ],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("AL_2025_FORM_40", "AL_FORM_40", "governs"),
    ("AL_2025_FORM_40_BOOKLET", "AL_FORM_40", "governs"),
    ("AL_CODE_40_18_5", "AL_FORM_40", "governs"),
    ("AL_CODE_40_18_15", "AL_FORM_40", "governs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM — AL Form 40
# ═══════════════════════════════════════════════════════════════════════════

AL40_FACTS: list[dict] = [
    {"fact_key": "filing_status", "label": "Filing status", "data_type": "choice", "required": True, "sort_order": 1,
     "choices": ["single", "MFJ", "MFS", "HOF"]},
    {"fact_key": "is_part_year", "label": "Part-year resident?", "data_type": "boolean", "required": False, "sort_order": 2,
     "notes": "Form 40 covers part-year (report only income earned while AL resident; FULL exemptions; FIT apportioned)."},
    {"fact_key": "wages_al", "label": "Wages/salaries/tips (AL Schedule W-2)", "data_type": "decimal", "required": False, "sort_order": 10},
    {"fact_key": "interest_dividends", "label": "Interest & dividend income (L6)", "data_type": "decimal", "required": False, "sort_order": 11},
    {"fact_key": "other_income", "label": "Other income (page 2 Part I total, L7)", "data_type": "decimal", "required": False, "sort_order": 12,
     "notes": "Excludes §414(j) defined-benefit pensions, SS, government pensions, state refunds (not reported)."},
    {"fact_key": "total_adjustments", "label": "Total adjustments to income (page 2 Part II, L9)", "data_type": "decimal", "required": False, "sort_order": 13},
    {"fact_key": "deduction_election", "label": "Deduction election (L11)", "data_type": "choice", "required": True, "sort_order": 20, "choices": ["standard", "itemized"]},
    {"fact_key": "itemized_deduction", "label": "Itemized deduction amount (L11 Box a, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 21},
    {"fact_key": "num_dependents", "label": "Number of dependents (Part III)", "data_type": "integer", "required": False, "sort_order": 22},
    # Federal income tax deduction worksheet inputs (L12)
    {"fact_key": "fed_1040_line22", "label": "Federal 1040 line 22 (total tax)", "data_type": "decimal", "required": False, "sort_order": 30,
     "notes": "W4. Includes SE tax + Additional Medicare tax (via Schedule 2)."},
    {"fact_key": "fed_niit_8960_l17", "label": "Federal NIIT (Form 8960 line 17)", "data_type": "decimal", "required": False, "sort_order": 31},
    {"fact_key": "fed_eic_27a", "label": "Federal EIC (1040 line 27a)", "data_type": "decimal", "required": False, "sort_order": 32},
    {"fact_key": "fed_actc_28", "label": "Federal Additional Child Tax Credit (1040 line 28)", "data_type": "decimal", "required": False, "sort_order": 33},
    {"fact_key": "fed_aoc_29", "label": "Federal American Opportunity Credit (1040 line 29)", "data_type": "decimal", "required": False, "sort_order": 34},
    {"fact_key": "fed_refundable_adoption_30", "label": "Federal refundable adoption credit (1040 line 30)", "data_type": "decimal", "required": False, "sort_order": 35},
    {"fact_key": "fed_form_2439", "label": "Federal Form 2439 credits (Sch 3 Part II 13a)", "data_type": "decimal", "required": False, "sort_order": 36},
    {"fact_key": "federal_agi", "label": "Federal AGI (for the part-year FIT apportionment ratio)", "data_type": "decimal", "required": False, "sort_order": 37},
    # Credits / payments
    {"fact_key": "schedule_oc_nonrefundable", "label": "Schedule OC nonrefundable credits (L18, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 40},
    {"fact_key": "schedule_oc_refundable", "label": "Schedule OC refundable credits (L25, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 41},
    {"fact_key": "additional_taxes_atp", "label": "Additional taxes (Schedule ATP, L19, RED-defer)", "data_type": "decimal", "required": False, "sort_order": 42},
    {"fact_key": "al_withholding", "label": "Alabama income tax withheld (L22)", "data_type": "decimal", "required": False, "sort_order": 50},
    {"fact_key": "estimated_extension_payments", "label": "Estimated + extension payments (L23)", "data_type": "decimal", "required": False, "sort_order": 51},
]

AL40_RULES: list[dict] = [
    {"rule_id": "R-AL-INCOME", "title": "AL gross income build → total income (L8) and AL AGI (L10)", "rule_type": "calculation",
     "formula": "L8 = wages_al + interest_dividends + other_income ; L10 = L8 - total_adjustments",
     "inputs": ["wages_al", "interest_dividends", "other_income", "total_adjustments"], "outputs": ["L8", "L10"], "sort_order": 10,
     "description": "AL builds gross income from scratch (no federal-AGI start). §414(j)/SS/government-pension/state-refund income is excluded at source (not in other_income)."},
    {"rule_id": "R-AL-FIT", "title": "Federal income tax deduction (L12) — worksheet + PY apportionment", "rule_type": "calculation",
     "formula": ("fed_tax = fed_1040_line22 + fed_niit_8960_l17 ; "
                 "refundable = fed_eic_27a + fed_actc_28 + fed_aoc_29 + fed_refundable_adoption_30 + fed_form_2439 ; "
                 "L12 = max(0, fed_tax - refundable) ; "
                 "if is_part_year: L12 = round(L12 * (L10 / federal_agi))  [ratio ≤ 1]"),
     "inputs": ["fed_1040_line22", "fed_niit_8960_l17", "fed_eic_27a", "fed_actc_28", "fed_aoc_29",
                "fed_refundable_adoption_30", "fed_form_2439", "is_part_year", "federal_agi"],
     "outputs": ["L12"], "sort_order": 11,
     "description": "Dec B. THE QUIRK. (1040 L22 + NIIT) − refundable credits, floored 0; separate from the L11 election. PY: × (AL AGI ÷ federal AGI). W3: liability-based (worksheet), not cash/accrued."},
    {"rule_id": "R-AL-STD-DED", "title": "Standard deduction (L11) — sliding by AL AGI", "rule_type": "calculation",
     "formula": ("by filing_status {max, max_band_top, step, band, floor}: "
                 "L11 = max(floor, max - step * ceil(max(0, L10 - max_band_top) / band)) ; "
                 "MFJ 8500/25999/175/500/5000 · MFS 4250/12999/88/250/2500 · HOF 5200/25999/135/500/2500 · single 3000/25999/25/500/2500"),
     "inputs": ["filing_status", "L10", "deduction_election"], "outputs": ["L11"], "sort_order": 12,
     "description": "Dec C / W1. Encoded as a formula (sidesteps the OCR-suspect MFJ cell). If deduction_election=itemized, L11 = itemized_deduction instead."},
    {"rule_id": "R-AL-PERS-EXEMPT", "title": "Personal exemption (L13)", "rule_type": "calculation",
     "formula": "L13 = {single:1500, MFJ:3000, MFS:1500, HOF:3000}[filing_status]",
     "inputs": ["filing_status"], "outputs": ["L13"], "sort_order": 13},
    {"rule_id": "R-AL-DEP-EXEMPT", "title": "Dependent exemption (L14) — sliding by AL AGI", "rule_type": "calculation",
     "formula": "per_dep = 1000 if L10<=50000 else (500 if L10<=100000 else 300) ; L14 = per_dep * num_dependents",
     "inputs": ["L10", "num_dependents"], "outputs": ["L14"], "sort_order": 14,
     "description": "Dec C. $1,000 (≤$50k) / $500 ($50k-$100k) / $300 (>$100k) per dependent, by AL AGI."},
    {"rule_id": "R-AL-TAXABLE", "title": "Total deductions (L15) and taxable income (L16)", "rule_type": "calculation",
     "formula": "L15 = L11 + L12 + L13 + L14 ; L16 = max(0, L10 - L15)",
     "inputs": [], "outputs": ["L15", "L16"], "sort_order": 15},
    {"rule_id": "R-AL-TAX", "title": "Income tax (L17) — 2/4/5% graduated", "rule_type": "calculation",
     "formula": ("single/MFS/HOF: 2% to 500, 4% 500-3000, 5% over 3000 ; "
                 "MFJ: 2% to 1000, 4% 1000-6000, 5% over 6000 ; on L16 (per the DOR tax table)"),
     "inputs": ["L16", "filing_status"], "outputs": ["L17"], "sort_order": 16,
     "description": "W2. §40-18-5. Tax table for the exact rounding; brackets as above."},
    {"rule_id": "R-AL-NET-TAX", "title": "Net tax (L18) and total liability (L21)", "rule_type": "calculation",
     "formula": "L18 = max(0, L17 - schedule_oc_nonrefundable) ; L21 = L18 + additional_taxes_atp",
     "inputs": ["schedule_oc_nonrefundable", "additional_taxes_atp"], "outputs": ["L18", "L21"], "sort_order": 17,
     "description": "Dec D: Schedule OC nonrefundable direct-entry; Schedule ATP additional taxes RED-deferred (direct-entry input)."},
    {"rule_id": "R-AL-PAYMENTS", "title": "Total payments (L27) and refund/owe (L30/L35)", "rule_type": "calculation",
     "formula": ("L27 = al_withholding + estimated_extension_payments + schedule_oc_refundable ; "
                 "if L21 > L27: L30 amount owed ; else L35 refund = L27 - L21"),
     "inputs": ["al_withholding", "estimated_extension_payments", "schedule_oc_refundable"], "outputs": ["L27", "L30", "L35"], "sort_order": 18},
]

AL40_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-AL-INCOME", "AL_2025_FORM_40", "primary", "AL gross income build, L8/L10; income exclusions"),
    ("R-AL-FIT", "AL_2025_FORM_40_BOOKLET", "primary", "FIT deduction worksheet p.31 verbatim"),
    ("R-AL-FIT", "AL_CODE_40_18_15", "secondary", "statutory 'paid or accrued' basis (W3)"),
    ("R-AL-STD-DED", "AL_2025_FORM_40_BOOKLET", "primary", "standard deduction sliding chart p.8"),
    ("R-AL-PERS-EXEMPT", "AL_2025_FORM_40", "primary", "personal exemption $1,500/$3,000, form face"),
    ("R-AL-DEP-EXEMPT", "AL_2025_FORM_40", "primary", "dependent exemption sliding $1,000/$500/$300"),
    ("R-AL-TAX", "AL_CODE_40_18_5", "primary", "2/4/5% graduated rate"),
    ("R-AL-INCOME", "AL_2025_FORM_40_BOOKLET", "secondary", "§414(j)/SS/govt-pension exclusions ('do not report')"),
]

AL40_LINES: list[dict] = [
    {"line_number": "5b", "description": "Wages, salaries, tips (AL Schedule W-2)", "line_type": "input", "source_facts": ["wages_al"], "sort_order": 1},
    {"line_number": "6", "description": "Interest & dividend income", "line_type": "input", "source_facts": ["interest_dividends"], "sort_order": 2},
    {"line_number": "7", "description": "Other income (page 2 Part I)", "line_type": "input", "source_facts": ["other_income"], "sort_order": 3},
    {"line_number": "8", "description": "Total income", "line_type": "subtotal", "source_rules": ["R-AL-INCOME"], "sort_order": 4},
    {"line_number": "9", "description": "Total adjustments to income (Part II)", "line_type": "input", "source_facts": ["total_adjustments"], "sort_order": 5},
    {"line_number": "10", "description": "Alabama adjusted gross income (L8 − L9)", "line_type": "subtotal", "source_rules": ["R-AL-INCOME"], "sort_order": 6},
    {"line_number": "11", "description": "Itemized or standard deduction", "line_type": "calculated", "source_rules": ["R-AL-STD-DED"], "sort_order": 7},
    {"line_number": "12", "description": "Federal tax deduction (worksheet)", "line_type": "calculated", "calculation": "R-AL-FIT", "source_rules": ["R-AL-FIT"], "sort_order": 8},
    {"line_number": "13", "description": "Personal exemption", "line_type": "calculated", "source_rules": ["R-AL-PERS-EXEMPT"], "sort_order": 9},
    {"line_number": "14", "description": "Dependent exemption", "line_type": "calculated", "source_rules": ["R-AL-DEP-EXEMPT"], "sort_order": 10},
    {"line_number": "15", "description": "Total deductions (11+12+13+14)", "line_type": "subtotal", "source_rules": ["R-AL-TAXABLE"], "sort_order": 11},
    {"line_number": "16", "description": "Taxable income (L10 − L15)", "line_type": "subtotal", "source_rules": ["R-AL-TAXABLE"], "sort_order": 12},
    {"line_number": "17", "description": "Income tax (2/4/5% tax table)", "line_type": "calculated", "source_rules": ["R-AL-TAX"], "sort_order": 13},
    {"line_number": "18", "description": "Net tax due Alabama (after Schedule OC nonrefundable)", "line_type": "calculated", "source_rules": ["R-AL-NET-TAX"], "sort_order": 14},
    {"line_number": "19", "description": "Additional taxes (Schedule ATP) — RED-defer", "line_type": "input", "source_facts": ["additional_taxes_atp"], "sort_order": 15},
    {"line_number": "21", "description": "Total tax liability", "line_type": "subtotal", "source_rules": ["R-AL-NET-TAX"], "sort_order": 16},
    {"line_number": "25", "description": "Refundable credits (Schedule OC F6) — direct-entry", "line_type": "input", "source_facts": ["schedule_oc_refundable"], "sort_order": 17},
    {"line_number": "27", "description": "Total payments", "line_type": "subtotal", "source_rules": ["R-AL-PAYMENTS"], "sort_order": 18},
    {"line_number": "30", "description": "Amount you owe", "line_type": "total", "source_rules": ["R-AL-PAYMENTS"], "sort_order": 19},
    {"line_number": "35", "description": "Refunded to you", "line_type": "total", "source_rules": ["R-AL-PAYMENTS"], "sort_order": 20},
]

AL40_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_AL40_FIT", "title": "Federal tax deduction is liability-based, not withheld", "severity": "info",
     "condition": "line 12 computed", "message": "L12 = (1040 L22 + NIIT) − refundable credits (EIC/ACTC/AOC/refundable adoption/2439), floored 0. Do NOT use federal tax withheld. Part-year: apportioned by AL AGI ÷ federal AGI.",
     "notes": "The AL quirk; verify the federal handoff maps 1040 L22 (W4)."},
    {"diagnostic_id": "D_AL40_40NR", "title": "Nonresident — file Form 40NR (prepare manually)", "severity": "info",
     "condition": "taxpayer is a nonresident (not part-year resident)", "message": "True nonresidents with AL-source income file Form 40NR, not Form 40. Form 40NR is not computed in v1.",
     "notes": "Dec A RED-defer. Form 40 covers full-year + part-year residents."},
    {"diagnostic_id": "D_AL40_ATP", "title": "Additional taxes / penalties (Schedule ATP) — prepare manually", "severity": "info",
     "condition": "consumer use tax / catastrophe-savings tax / penalties", "message": "Schedule ATP additional taxes (L19) + penalties (L31) are not computed in v1 — prepare Schedule ATP manually.",
     "notes": "Dec D RED-defer."},
    {"diagnostic_id": "D_AL40_NOL", "title": "Net operating loss (Form NOL-85A, L17) — prepare manually", "severity": "info",
     "condition": "AL NOL claimed", "message": "The Form NOL-85A net operating loss alternative to the L17 tax table is not computed in v1.",
     "notes": "Dec D RED-defer."},
    {"diagnostic_id": "D_AL40_EXCLUSIONS", "title": "§414(j) / SS / government-pension income is EXCLUDED (not reported)", "severity": "info",
     "condition": "taxpayer has defined-benefit pension / SS / government pension", "message": "Do NOT include §414(j) defined-benefit pension distributions, Social Security, US/AL government retirement, or state tax refunds in AL income — Alabama fully excludes them (no line; simply omit). No general age-65 exclusion exists.",
     "notes": "AL exclusion regime — a common error is to report these."},
    {"diagnostic_id": "D_AL40_STDDED", "title": "Standard deduction computed by formula (W1)", "severity": "info",
     "condition": "standard deduction elected", "message": "The standard deduction sliding scale is encoded as a formula (max − step×band, floored), reproducing the DOR chart and sidestepping the one OCR-suspect MFJ cell. Verify at a couple of AGI points.",
     "notes": "W1."},
]

AL40_SCENARIOS: list[dict] = [
    {"scenario_name": "Single resident, wages, standard deduction, FIT deduction", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"filing_status": "single", "wages_al": 60000, "deduction_election": "standard", "fed_1040_line22": 6000, "num_dependents": 0, "is_part_year": False},
     "expected_outputs": {"L10": 60000, "L11": 2500, "L12": 6000, "L13": 1500, "L16": 50000},
     "notes": "L10=60000; std ded single at AGI 60000 = floor 2500; L12 FIT = 6000; L13 = 1500; L15 = 2500+6000+1500+0 = 10000; L16 = 60000−10000 = 50000."},
    {"scenario_name": "FIT worksheet with NIIT and refundable credits", "scenario_type": "edge", "sort_order": 2,
     "inputs": {"filing_status": "MFJ", "fed_1040_line22": 12000, "fed_niit_8960_l17": 800, "fed_eic_27a": 0, "fed_actc_28": 2000, "fed_aoc_29": 500, "is_part_year": False},
     "expected_outputs": {"L12": 10300},
     "notes": "fed_tax = 12000 + 800 = 12800; refundable = 2000 + 500 = 2500; L12 = 12800 − 2500 = 10300."},
    {"scenario_name": "FIT part-year apportionment", "scenario_type": "edge", "sort_order": 3,
     "inputs": {"filing_status": "single", "fed_1040_line22": 8000, "is_part_year": True, "federal_agi": 100000, "wages_al": 40000, "interest_dividends": 0, "other_income": 0, "total_adjustments": 0},
     "expected_outputs": {"L10": 40000, "L12": 3200},
     "notes": "L10 (AL AGI) = 40000; ratio = 40000/100000 = 0.40; L12 = 8000 × 0.40 = 3200."},
    {"scenario_name": "MFJ standard deduction mid-slide", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"filing_status": "MFJ", "wages_al": 30000, "deduction_election": "standard"},
     "expected_outputs": {"L11": 6925},
     "notes": "MFJ std ded at AGI 30000: band = ceil((30000−25999)/500) = ceil(8.002) = 9; L11 = 8500 − 175×9 = 6925. (W1: verify the band count vs the DOR chart at $30,000.)"},
    {"scenario_name": "Dependent exemption slide at $100k AGI", "scenario_type": "edge", "sort_order": 5,
     "inputs": {"filing_status": "MFJ", "wages_al": 100000, "num_dependents": 3, "deduction_election": "standard"},
     "expected_outputs": {"L10": 100000, "L14": 1500},
     "notes": "AL AGI 100000 → $500/dep band (≤100000); L14 = 500 × 3 = 1500."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORMS registry + flow assertions
# ═══════════════════════════════════════════════════════════════════════════

FORMS: list[dict] = [
    {
        "identity": {"form_number": "AL_FORM_40", "form_title": "AL Form 40 — Alabama Individual Income Tax Return (TY2025)",
                     "notes": "3rd state individual spec. Builds AL gross income from scratch; the federal income tax deduction (L12) is the defining feature; 2/4/5% rate; sliding-scale std ded + dependent exemption. v1 covers full-year + part-year residents."},
        "facts": AL40_FACTS, "rules": AL40_RULES, "rule_links": AL40_RULE_LINKS,
        "lines": AL40_LINES, "diagnostics": AL40_DIAGNOSTICS, "scenarios": AL40_SCENARIOS,
    },
]

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-AL-FIT", "title": "AL L12 = (1040 L22 + NIIT) − refundable credits", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "draft", "sort_order": 1,
     "description": "Form 40 line 12 reconciles to the federal handoff: (1040 L22 + 8960 L17) − (EIC 27a + ACTC 28 + AOC 29 + refundable adoption 30 + 2439), floored 0.",
     "definition": {"rule": "R-AL-FIT", "check": "L12 = max(0, (1040_L22 + 8960_L17) - refundable)"}},
    {"assertion_id": "FA-AL-FIT-PY", "title": "FIT deduction apportioned for part-year (AL AGI / federal AGI)", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "draft", "sort_order": 2,
     "description": "When is_part_year, L12 = worksheet federal tax × (AL AGI ÷ federal AGI), ratio ≤ 1.",
     "definition": {"rule": "R-AL-FIT", "check": "L12_py = L12 * (L10 / federal_agi)"}},
    {"assertion_id": "FA-AL-NO-FEDAGI", "title": "AL builds gross income from scratch (no federal-AGI start)", "assertion_type": "flow_assertion",
     "entity_types": ["1040"], "status": "draft", "sort_order": 3,
     "description": "Form 40 line 8 total income = wages (AL Sch W-2) + interest/dividends + other income — NOT federal AGI. Federal figures enter only at L12 + specific Part I/II lines.",
     "definition": {"rule": "R-AL-INCOME", "check": "L8 built from AL income items, not federal AGI"}},
    {"assertion_id": "FA-AL-EXCLUSIONS", "title": "§414(j)/SS/government-pension excluded from AL income", "assertion_type": "flow_assertion",
     "entity_types": ["1040"], "status": "draft", "sort_order": 4,
     "description": "Defined-benefit (§414(j)) pensions, Social Security, government pensions, and state refunds are NOT reported in AL income (no add-back/subtract line; simply omitted).",
     "definition": {"check": "these income items excluded at the income build"}},
]


# ═══════════════════════════════════════════════════════════════════════════
# Command
# ═══════════════════════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = (
        "Load the AL Form 40 spec (Alabama Individual Income Tax, TY2025). "
        "Refuses to seed until Ken sets READY_TO_SEED=True after the in-session review walk (W1-W5)."
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad AL Form 40 spec (Alabama Individual Income Tax)\n"))
        self._load_topics()
        sources = self._load_sources()
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
                "\nREFUSING TO SEED AL FORM 40: not cleared to seed.\n\n"
                "Content is authored, but seeding is gated until Ken reviews the packet\n"
                "(W1 the std-deduction sliding-scale formula; W2 the §40-18-5 rate source;\n"
                "W3 the FIT 'paid or accrued' vs worksheet basis; W4 the federal-tax handoff\n"
                "line numbers; W5 Schedule OC caps / Form 40NR) and flips the sentinel.\n\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True to proceed)\n\n"
                f"Currently empty / placeholder:\n  {still_empty}\n\n"
                "To proceed: review the module-level data lists (and al_form40_source_brief.md),\n"
                "then set READY_TO_SEED = True. Idempotent via update_or_create."
            )

    def _load_topics(self):
        ct = 0
        for code, name in AUTHORITY_TOPICS:
            _, created = AuthorityTopic.objects.update_or_create(topic_code=code, defaults={"topic_name": name})
            if created:
                ct += 1
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
                    AuthoritySourceTopic.objects.get_or_create(authority_source=source, authority_topic=topic)
        for code in EXISTING_SOURCES_TO_REFERENCE:
            src = AuthoritySource.objects.filter(source_code=code).first()
            if src:
                sources[code] = src
            else:
                self.stdout.write(self.style.WARNING(f"  existing source {code} NOT FOUND — links to it will be skipped"))
        self.stdout.write(f"Sources ready: {len(sources)}")
        return sources

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
        self.stdout.write("AL Form 40 loaded.")
        self.stdout.write(
            f"  AL_FORM_40: facts {len(AL40_FACTS)} / rules {len(AL40_RULES)} / lines {len(AL40_LINES)} / "
            f"diag {len(AL40_DIAGNOSTICS)} / tests {len(AL40_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}"
        )
        self.stdout.write("=" * 60)
