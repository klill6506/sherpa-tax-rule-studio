"""Load the North Carolina Form CD-405 spec — C Corporation Tax Return (TY2025).
WO-12, the reuse-state C-corp batch (form 3 of 3). Extends the federal 1120 module (WO-11).

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
NC Form CD-405 is a COMBINED FRANCHISE + INCOME return for C corporations:
  • INCOME TAX: 2.25% (S.B. 105 phase-down) of NC-apportioned net income (federal-TI start + NC
    add/subtract incl. the 85% bonus add-back + §179 $25k/$200k delta -> single sales factor).
  • FRANCHISE TAX: $1.50 per $1,000 (.0015) of NET WORTH (Schedule C), first $1,000,000 capped at
    $500, minimum $200 (holding-company cap $150,000). Base is NET WORTH ONLY — the old three-way
    "greatest of net worth / 55% ad valorem / NC tangible investment" test was repealed effective TY2017.
Reuses the NC D-400 depreciation work (85% add-back + $25k/$200k §179, Jan 1 2023 conformity).

Greenfield: no `NC_CD405` at the 2026-07-05 gap-check (only the individual NC_D400 existed).

═══════════════════════════════════════════════════════════════════════════
v1 SCOPE — LOCKED (Ken's Gate-1 walk 2026-07-05; DECISIONS D-14). See state_ccorp_batch_source_brief.md.
═══════════════════════════════════════════════════════════════════════════
COMPUTES (Q1 full): the 2.25% income tax + the franchise tax (net-worth base, $500 first-$1M cap, $200 min,
holding cap); 85% bonus add-back + §179 $25k/$200k delta; single sales factor; total = income + franchise.

═══════════════════════════════════════════════════════════════════════════
requires_human_review WALK ITEMS (W7-W9)
═══════════════════════════════════════════════════════════════════════════
W7. INCOME RATE = 2.25% for TY2025 (S.B. 105 phase-down: 2.5% 2024 -> 2.25% 2025 -> 2% 2026 -> 0% 2030). CONFIRM.
W8. FRANCHISE TAX — $1.50/$1,000 (.0015) of NET WORTH; first $1,000,000 capped at $500; minimum $200;
    holding-company cap $150,000; base = NET WORTH ONLY (three-way test repealed TY2017). CONFIRM.
W9. DEPRECIATION — 85% bonus add-back (recover 20%/yr over 5 following years); §179 $25,000/$200,000
    (G.S. §105-130.5B). Conformity frozen Jan 1 2023 (OBBBA not adopted). CONFIRM.

═══════════════════════════════════════════════════════════════════════════
CARRIED [UNVERIFIED]: §179 $25k/$200k statute-derived (G.S. §105-130.5B, cross-referenced by the 2025 CD-405
instr); CD-419 extension = 7 months. Re-verify the phasing rate at TY2026 (-> 2%).
═══════════════════════════════════════════════════════════════════════════

SAFETY GUARD — READY_TO_SEED stays False until Ken approves the review walk (W7-W9).
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

# FLIPPED 2026-07-05 — Ken APPROVED ("Seed all three now"): W7 the 2.25% income rate,
# W8 the net-worth franchise tax ($500 first-$1M cap, $200 min, holding cap), W9 the 85%
# bonus add-back + §179 $25k/$200k. Validated (validate_state_ccorp.py, 41/0).
READY_TO_SEED = True

FORM_JURISDICTION = "NC"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1120"]

# Verified constants (state_ccorp_batch_source_brief.md; 2025 CD-405 instr Web 1-26; G.S. §105)
NC_INCOME_RATE = "0.0225"          # S.B. 105 phase-down — 2.25% for TY2025
NC_179_LIMIT = 25000               # G.S. §105-130.5B
NC_179_PHASEOUT = 200000
ADDBACK_PCT = "0.85"               # 85% bonus / §179-excess add-back (recover 20%/yr over 5 yrs)
FRANCHISE_RATE = "0.0015"          # $1.50 per $1,000 of net worth
FRANCHISE_FIRST_TIER = 1000000     # first $1M
FRANCHISE_FIRST_TIER_CAP = 500     # first $1M capped at $500
FRANCHISE_MIN = 200                # minimum franchise tax
FRANCHISE_HOLDING_CAP = 150000     # holding-company maximum


def _nc_franchise(net_worth, is_holding=False) -> float:
    """NC CD-405 franchise tax: $1.50/$1,000 of net worth; first $1M capped at $500; min $200; holding cap $150k."""
    nw = float(net_worth)
    if nw > FRANCHISE_FIRST_TIER:
        fr = FRANCHISE_FIRST_TIER_CAP + (nw - FRANCHISE_FIRST_TIER) * float(FRANCHISE_RATE)
    else:
        fr = min(nw * float(FRANCHISE_RATE), float(FRANCHISE_FIRST_TIER_CAP))
    fr = max(float(FRANCHISE_MIN), fr)
    if is_holding:
        fr = min(fr, float(FRANCHISE_HOLDING_CAP))
    return fr


def _nc_income_tax(fed_ti, additions, subtractions, nol, ratio):
    """NC CD-405 income tax path. Returns (nc_taxable, income_tax)."""
    apportioned = (float(fed_ti) + float(additions) - float(subtractions)) * float(ratio)
    nc_taxable = apportioned - min(float(nol), max(0.0, apportioned))
    return nc_taxable, max(0.0, nc_taxable) * float(NC_INCOME_RATE)


AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("nc_corp_tax", "North Carolina CD-405 C-corporation: combined 2.25% income tax (federal-TI + 85% bonus "
     "add-back + §179 $25k/$200k + single sales factor) and franchise tax ($1.50/$1,000 net worth, $500 "
     "first-$1M cap, $200 min); conformity frozen Jan 1 2023."),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "NC_2025_FORM_CD405", "source_type": "state_form", "source_rank": "primary_official",
        "jurisdiction_code": "NC", "title": "2025 North Carolina Form CD-405 — C Corporation Tax Return",
        "citation": "NC Form CD-405 (2025)", "issuer": "North Carolina Department of Revenue",
        "official_url": "https://www.ncdor.gov/",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.5, "topics": ["nc_corp_tax"],
        "excerpts": [{
            "excerpt_label": "CD-405 income + franchise line flow (2025 verbatim)",
            "excerpt_text": (
                "Combined franchise + income return. Schedule B income tax: NC-apportioned net income × 2.25%. "
                "Schedule G L7 'Federal Taxable Income' (before NOL, IRC as of Jan 1 2023) -> Schedule H "
                "additions/subtractions -> L14 apportionment factor (single sales factor, four decimals). "
                "Schedule C franchise tax: net worth base; '$1.50 per $1,000 (.0015) of the first $1,000,000 of "
                "net worth, with a maximum of $500. If net worth exceeds $1,000,000, multiply the amount over "
                "$1,000,000 by .0015 and add $500. The franchise tax can be no less than $200.' Holding-company "
                "franchise limited to $150,000. Net worth = total assets (before accumulated depreciation) less "
                "total liabilities, per GAAP. (The property and investment franchise bases were repealed "
                "effective TY2017 — net worth is the sole base.)"
            ),
            "summary_text": "CD-405: income 2.25% of apportioned net income; franchise $1.50/$1,000 net worth (first $1M cap $500, min $200, holding cap $150k, net-worth-only base). Single sales factor 4 dec.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "NC_2025_CD405_INSTR", "source_type": "official_instructions", "source_rank": "primary_official",
        "jurisdiction_code": "NC", "title": "2025 NC CD-405 C Corporation Tax Return Instructions (Web 1-26)",
        "citation": "CD-405 Instructions (2025, Web 1-26)", "issuer": "North Carolina Department of Revenue",
        "official_url": "https://www.ncdor.gov/",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.4, "topics": ["nc_corp_tax"],
        "excerpts": [{
            "excerpt_label": "85% bonus add-back + §179 + conformity Jan 1 2023 (CD-405 instr verbatim)",
            "excerpt_text": (
                "'North Carolina did not adopt the ... bonus depreciation provisions in IRC sections 168(k) or "
                "168(n) for property placed in service for tax year 2025. An addition is required for 85% of the "
                "amount of bonus depreciation deducted on the federal return. ... Any amount of the bonus "
                "depreciation added ... may be deducted in five equal installments over your first five taxable "
                "years beginning with the tax return for taxable year 2026.' §179 (G.S. §105-130.5B): NC dollar "
                "limitation $25,000 / investment limitation $200,000; add-back = (federal §179 − NC §179) × 85%, "
                "recovered 20%/yr over 5 years. 'Federal taxable income as defined in the Internal Revenue Code, "
                "effective as of January 1, 2023 (before net operating loss) is the starting point ... any "
                "change made to the Internal Revenue Code after January 1, 2023, including ... OBBBA DO NOT "
                "apply.' Income tax rate: 2.25% (2025). Due 15th day of 4th month; extension CD-419."
            ),
            "summary_text": "NC: 85% bonus add-back (5-yr 20% recovery); §179 $25k/$200k; conformity Jan 1 2023 (OBBBA not adopted); income 2.25%.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "NC_GS_105_CORP", "source_type": "statute", "source_rank": "controlling",
        "jurisdiction_code": "NC", "title": "N.C. Gen. Stat. §105-130.5B (bonus/§179) · §105-122 (franchise) · §105-130.4 (apportionment)",
        "citation": "N.C. Gen. Stat. §105-130.3; §105-130.4; §105-130.5B; §105-122; S.B. 105 (2021)", "issuer": "North Carolina General Assembly",
        "official_url": "https://www.ncleg.gov/",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.2, "topics": ["nc_corp_tax"],
        "excerpts": [{
            "excerpt_label": "Rate phase-down + §179 + franchise net-worth base (substance)",
            "excerpt_text": (
                "§105-130.3 (as amended by S.B. 105, 2021): the corporate income tax rate phases down — 2.5% "
                "(2024), 2.25% (2025), 2% (2026), 1% (2028), 0% (2030). §105-130.5B: the bonus/§179 add-back "
                "(85%, 20%/yr recovery) and the NC §179 $25,000/$200,000 limits (fixed for tax years on/after "
                "2013). §105-130.4: single sales factor apportionment, market-based sourcing. §105-122: the "
                "franchise tax on net worth ($1.50/$1,000, first $1M cap $500, $200 minimum, $150k holding cap); "
                "the property and investment bases were repealed effective for tax years beginning on/after 2017."
            ),
            "summary_text": "§105-130.3 rate 2.25% (2025, S.B. 105 phase-down); §105-130.5B 85% add-back + §179 $25k/$200k; §105-130.4 single sales factor; §105-122 franchise net-worth base.",
            "is_key_excerpt": True,
        }],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("NC_2025_FORM_CD405", "NC_CD405", "governs"), ("NC_2025_CD405_INSTR", "NC_CD405", "governs"),
    ("NC_GS_105_CORP", "NC_CD405", "governs"),
]


F_FACTS: list[dict] = [
    {"fact_key": "federal_taxable_income", "label": "Federal taxable income before NOL — Schedule G L7 (IRC Jan 1 2023)", "data_type": "decimal", "required": False, "sort_order": 1},
    {"fact_key": "federal_bonus_depreciation", "label": "Federal §168(k) bonus depreciation taken (NC 85% add-back, Sch H)", "data_type": "decimal", "required": False, "sort_order": 2,
     "notes": "W9. NC adds back 85% of federal bonus; recovers over 5 years (20%/yr) starting the next tax year."},
    {"fact_key": "federal_section_179", "label": "Federal §179 deduction taken (for the NC §25k/$200k delta)", "data_type": "decimal", "required": False, "sort_order": 3,
     "notes": "W9. NC §179 limit $25,000; add-back = 85% of (federal §179 − NC §179)."},
    {"fact_key": "nc_bonus_recovery", "label": "NC bonus/§179 recovery — 20%/yr installments from prior add-backs (Sch H subtraction)", "data_type": "decimal", "required": False, "sort_order": 4,
     "notes": "W9. Direct-entry the current-year 20% installment of prior years' 85% add-backs."},
    {"fact_key": "nc_additions_other", "label": "Other NC additions — non-NC bond interest, related-member interest, etc. (Sch H)", "data_type": "decimal", "required": False, "sort_order": 5},
    {"fact_key": "nc_subtractions_other", "label": "Other NC subtractions — US-obligation interest, §78/§951A, etc. (Sch H)", "data_type": "decimal", "required": False, "sort_order": 6},
    {"fact_key": "nc_nol_carryover", "label": "NC net operating loss carryover", "data_type": "decimal", "required": False, "sort_order": 7},
    {"fact_key": "is_multistate", "label": "Multistate corporation (apportion)? — if no, NC ratio = 100%", "data_type": "boolean", "required": False, "sort_order": 8},
    {"fact_key": "sales_nc", "label": "Sales within NC (Schedule O numerator, market-based)", "data_type": "decimal", "required": False, "sort_order": 9},
    {"fact_key": "sales_everywhere", "label": "Sales everywhere (Schedule O denominator)", "data_type": "decimal", "required": False, "sort_order": 10},
    {"fact_key": "net_worth", "label": "Net worth — total assets (before accumulated depreciation) less total liabilities (Schedule C, franchise base)", "data_type": "decimal", "required": False, "sort_order": 11},
    {"fact_key": "is_holding_company", "label": "Qualified holding company? (franchise cap $150,000)", "data_type": "boolean", "required": False, "sort_order": 12},
]

F_RULES: list[dict] = [
    {"rule_id": "R-NC405-ADD", "title": "NC additions — 85% bonus + §179 excess add-back (Sch H)", "rule_type": "calculation",
     "formula": "additions = 0.85 * federal_bonus_depreciation + 0.85 * max(0, federal_section_179 - 25000) + nc_additions_other",
     "inputs": ["federal_bonus_depreciation", "federal_section_179", "nc_additions_other"], "outputs": ["additions"], "sort_order": 1,
     "description": "W9. G.S. §105-130.5B. Add back 85% of federal bonus depreciation and 85% of the federal §179 in excess of NC's $25,000 limit. Plus other Schedule H additions."},
    {"rule_id": "R-NC405-SUB", "title": "NC subtractions — bonus/§179 5-year recovery (Sch H)", "rule_type": "calculation",
     "formula": "subtractions = nc_bonus_recovery + nc_subtractions_other",
     "inputs": ["nc_bonus_recovery", "nc_subtractions_other"], "outputs": ["subtractions"], "sort_order": 2,
     "description": "W9. The prior-year 85% add-backs are recovered in five equal installments (20%/yr) starting the following year (direct-entry). Plus other Schedule H subtractions."},
    {"rule_id": "R-NC405-APPORT", "title": "Single sales factor apportionment (4 decimals)", "rule_type": "calculation",
     "formula": "nc_ratio = 1.0 if not is_multistate else round(sales_nc / sales_everywhere, 4)",
     "inputs": ["is_multistate", "sales_nc", "sales_everywhere"], "outputs": ["nc_ratio"], "sort_order": 3,
     "description": "W7. G.S. §105-130.4: single sales factor, market-based sourcing, computed to four decimal places."},
    {"rule_id": "R-NC405-INCOME", "title": "NC income tax — 2.25% (Schedule B)", "rule_type": "calculation",
     "formula": ("apportioned = (federal_taxable_income + additions - subtractions) * nc_ratio ; "
                 "nc_taxable = apportioned - min(nc_nol_carryover, max(0, apportioned)) ; income_tax = max(0, nc_taxable) * 0.0225"),
     "inputs": ["federal_taxable_income", "nc_nol_carryover"], "outputs": ["nc_taxable_income", "income_tax"], "sort_order": 4,
     "description": "W7. G.S. §105-130.3 (S.B. 105 phase-down). Federal TI + NC additions - subtractions, apportioned by the single sales factor, less NC NOL, times 2.25% for TY2025."},
    {"rule_id": "R-NC405-FRANCH", "title": "NC franchise tax — net worth (Schedule C)", "rule_type": "calculation",
     "formula": ("if net_worth > 1000000: fr = 500 + (net_worth - 1000000) * 0.0015 ; else: fr = min(net_worth * 0.0015, 500) ; "
                 "franchise_tax = max(200, fr) ; if is_holding_company: franchise_tax = min(franchise_tax, 150000)"),
     "inputs": ["net_worth", "is_holding_company"], "outputs": ["franchise_tax"], "sort_order": 5,
     "description": "W8. G.S. §105-122. $1.50 per $1,000 (.0015) of net worth; the first $1,000,000 is capped at $500; over $1M adds .0015 × excess + $500; minimum $200; qualified holding company capped at $150,000. Base = NET WORTH ONLY (the three-way test was repealed TY2017)."},
    {"rule_id": "R-NC405-TOTAL", "title": "Total tax — income + franchise", "rule_type": "calculation",
     "formula": "total_tax = income_tax + franchise_tax",
     "inputs": [], "outputs": ["total_tax"], "sort_order": 6,
     "description": "W7/W8. CD-405 is a combined return: total = the 2.25% income tax + the net-worth franchise tax."},
]

F_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-NC405-ADD", "NC_2025_CD405_INSTR", "primary", "85% bonus + §179 add-back"),
    ("R-NC405-ADD", "NC_GS_105_CORP", "secondary", "§105-130.5B"),
    ("R-NC405-SUB", "NC_2025_CD405_INSTR", "primary", "20%/yr 5-year recovery"),
    ("R-NC405-APPORT", "NC_GS_105_CORP", "primary", "§105-130.4 single sales factor"),
    ("R-NC405-INCOME", "NC_2025_FORM_CD405", "primary", "Schedule B 2.25% income tax"),
    ("R-NC405-INCOME", "NC_GS_105_CORP", "secondary", "§105-130.3 phase-down rate"),
    ("R-NC405-FRANCH", "NC_2025_FORM_CD405", "primary", "Schedule C franchise tax"),
    ("R-NC405-FRANCH", "NC_GS_105_CORP", "secondary", "§105-122 net-worth base"),
    ("R-NC405-TOTAL", "NC_2025_FORM_CD405", "primary", "combined franchise + income"),
]

F_LINES: list[dict] = [
    {"line_number": "NC-B", "description": "Schedule B NC income tax (× 2.25%)", "line_type": "calculated", "source_rules": ["R-NC405-INCOME"], "sort_order": 1},
    {"line_number": "NC-14", "description": "Schedule G/O L14 apportionment factor (single sales, 4 dec)", "line_type": "calculated", "source_rules": ["R-NC405-APPORT"], "sort_order": 2},
    {"line_number": "NC-C", "description": "Schedule C franchise tax (net worth)", "line_type": "calculated", "source_rules": ["R-NC405-FRANCH"], "sort_order": 3},
    {"line_number": "NC-TOT", "description": "CD-405 total tax (income + franchise)", "line_type": "calculated", "source_rules": ["R-NC405-TOTAL"], "sort_order": 4},
]

F_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_NC405_RATE", "title": "NC corporate income tax rate = 2.25% (phasing to 0 by 2030)", "severity": "info",
     "condition": "always (informational)",
     "message": "North Carolina's corporate income tax rate is 2.25% for TY2025 under the S.B. 105 (2021) phase-down (2.5% in 2024, 2.25% in 2025, 2% in 2026, 1% in 2028, 0% in 2030). Re-verify the rate each year.",
     "notes": "W7. Year-keyed."},
    {"diagnostic_id": "D_NC405_FRANCH", "title": "NC franchise tax — net-worth base, $200 min, $500 first-$1M cap", "severity": "info",
     "condition": "net_worth > 0",
     "message": "North Carolina imposes a franchise tax of $1.50 per $1,000 (.0015) of net worth (Schedule C): the first $1,000,000 is capped at $500; amounts over $1,000,000 add .0015 × the excess; the minimum is $200; a qualified holding company is capped at $150,000. The base is NET WORTH ONLY — the former three-way 'greatest of' test (net worth / 55% ad valorem / NC tangible investment) was repealed effective tax year 2017.",
     "notes": "W8."},
    {"diagnostic_id": "D_NC405_BONUS", "title": "NC 85% bonus depreciation add-back", "severity": "info",
     "condition": "federal_bonus_depreciation > 0",
     "message": "North Carolina did not adopt IRC §168(k)/§168(n) bonus depreciation for 2025. Add back 85% of the federal bonus depreciation this year; deduct the added-back amount in five equal installments (20%/yr) beginning with the 2026 return (G.S. §105-130.5B).",
     "notes": "W9."},
    {"diagnostic_id": "D_NC405_179", "title": "NC §179 limit = $25,000 / $200,000", "severity": "warning",
     "condition": "federal_section_179 > 25000",
     "message": "North Carolina's §179 limits are $25,000 (dollar) / $200,000 (investment) — far below the federal $2.5M/$4M (G.S. §105-130.5B). Add back 85% of the federal §179 in excess of the NC limit; recover over five years (20%/yr).",
     "notes": "W9."},
    {"diagnostic_id": "D_NC405_APPORT", "title": "NC single sales factor (4 decimals)", "severity": "info",
     "condition": "is_multistate",
     "message": "North Carolina apportions using a single sales factor with market-based sourcing (G.S. §105-130.4), computed to four decimal places.",
     "notes": "W7."},
]

F_SCENARIOS: list[dict] = [
    {"scenario_name": "NC405-A — NC-only corp: 2.25% income + $200 min franchise", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"federal_taxable_income": 400000, "net_worth": 100000},
     "expected_outputs": {"nc_taxable_income": 400000, "income_tax": 9000, "franchise_tax": 200, "total_tax": 9200},
     "notes": "Income 400,000 x 2.25% = 9,000; net worth 100,000 -> min franchise $200; total 9,200."},
    {"scenario_name": "NC405-B — 85% bonus add-back", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"federal_taxable_income": 100000, "federal_bonus_depreciation": 80000, "net_worth": 0},
     "expected_outputs": {"additions": 68000, "nc_taxable_income": 168000, "income_tax": 3780},
     "notes": "85% of 80,000 = 68,000 add-back. 100,000 + 68,000 = 168,000 x 2.25% = 3,780."},
    {"scenario_name": "NC405-C — §179 excess add-back (85% of excess over $25k)", "scenario_type": "edge", "sort_order": 3,
     "inputs": {"federal_taxable_income": 500000, "federal_section_179": 100000, "net_worth": 0},
     "expected_outputs": {"additions": 63750, "nc_taxable_income": 563750, "income_tax": 12684.375},
     "notes": "85% of (100,000 - 25,000) = 63,750 add-back. 500,000 + 63,750 = 563,750 x 2.25% = 12,684.375."},
    {"scenario_name": "NC405-D — franchise: first-$1M cap ($500)", "scenario_type": "edge", "sort_order": 4,
     "inputs": {"net_worth": 500000},
     "expected_outputs": {"franchise_tax": 500},
     "notes": "500,000 × .0015 = 750, capped at $500 on the first $1M -> $500."},
    {"scenario_name": "NC405-E — franchise: over $1M net worth", "scenario_type": "edge", "sort_order": 5,
     "inputs": {"net_worth": 2000000},
     "expected_outputs": {"franchise_tax": 2000},
     "notes": "$500 (first $1M) + 1,000,000 × .0015 = 500 + 1,500 = $2,000."},
    {"scenario_name": "NC405-F — multistate single sales factor", "scenario_type": "edge", "sort_order": 6,
     "inputs": {"federal_taxable_income": 1000000, "is_multistate": True, "sales_nc": 250000, "sales_everywhere": 1000000, "net_worth": 0},
     "expected_outputs": {"nc_ratio": 0.25, "nc_taxable_income": 250000, "income_tax": 5625},
     "notes": "Ratio 0.2500; NC taxable 1,000,000 x 0.25 = 250,000 x 2.25% = 5,625."},
]


FORMS: list[dict] = [
    {
        "identity": {"form_number": "NC_CD405", "form_title": "North Carolina Form CD-405 — C Corporation Tax Return (TY2025)",
                     "notes": "WO-12 (form 3 of 3, DECISIONS D-14). NC combined franchise + income return: INCOME tax 2.25% (S.B. 105 phase-down; federal-TI + 85% bonus add-back + §179 $25k/$200k delta -> single sales factor 4-dec) + FRANCHISE tax ($1.50/$1,000 net worth, first-$1M cap $500, min $200, holding cap $150k, NET-WORTH-ONLY base — three-way test repealed TY2017). Total = income + franchise. Conformity frozen Jan 1 2023 (OBBBA not adopted). Reuses NC D-400 depreciation work."},
        "facts": F_FACTS, "rules": F_RULES, "rule_links": F_RULE_LINKS,
        "lines": F_LINES, "diagnostics": F_DIAGNOSTICS, "scenarios": F_SCENARIOS,
    },
]

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-NC405-INCOME", "title": "NC income tax = 2.25% of apportioned NC net income", "assertion_type": "reconciliation",
     "entity_types": ["1120"], "status": "draft", "sort_order": 1,
     "description": "Federal TI + NC additions (85% bonus/§179 add-back) − subtractions, apportioned by the single sales factor, less NC NOL, times 2.25%.",
     "definition": {"rule": "R-NC405-INCOME", "check": "income_tax = max(0, (fed_ti+add-sub)*ratio - nol) * 0.0225"}},
    {"assertion_id": "FA-NC405-FRANCH", "title": "NC franchise tax from the net-worth schedule", "assertion_type": "reconciliation",
     "entity_types": ["1120"], "status": "draft", "sort_order": 2,
     "description": "$1.50/$1,000 of net worth; first $1M capped at $500; minimum $200; holding-company cap $150,000.",
     "definition": {"rule": "R-NC405-FRANCH", "check": "franchise = max(200, first-$1M-capped-$500 + .0015*excess)"}},
    {"assertion_id": "FA-NC405-TOTAL", "title": "NC total = income tax + franchise tax", "assertion_type": "reconciliation",
     "entity_types": ["1120"], "status": "draft", "sort_order": 3,
     "description": "CD-405 combined total = the 2.25% income tax plus the net-worth franchise tax.",
     "definition": {"rule": "R-NC405-TOTAL", "check": "total_tax = income_tax + franchise_tax"}},
]


class Command(BaseCommand):
    help = "Load the NC CD-405 spec (NC C-corp franchise + income tax, TY2025). Refuses to seed until READY_TO_SEED=True (W7-W9)."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad NC Form CD-405 spec (C Corporation Tax Return)\n"))
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
                "\nREFUSING TO SEED NC_CD405: not cleared to seed.\n\n"
                "Gated until Ken reviews (W7 2.25% income rate; W8 the net-worth franchise tax;\n"
                "W9 the 85% bonus add-back + §179 $25k/$200k) and flips the sentinel.\n\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True)\n\nEmpty:\n  {still_empty}\n"
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
            source, _ = AuthoritySource.objects.update_or_create(source_code=src_data["source_code"], defaults=src_data)
            sources[source.source_code] = source
            for exc in excerpts_data:
                exc = dict(exc)
                AuthorityExcerpt.objects.update_or_create(authority_source=source, excerpt_label=exc["excerpt_label"], defaults=exc)
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
            form_number=identity["form_number"], jurisdiction=FORM_JURISDICTION, tax_year=FORM_TAX_YEAR, version=FORM_VERSION,
            defaults={"form_title": identity["form_title"], "entity_types": FORM_ENTITY_TYPES, "status": FORM_STATUS, "notes": identity["notes"]},
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
                RuleAuthorityLink.objects.get_or_create(form_rule=rule, authority_source=source, defaults={"support_level": level, "relevance_note": note})
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
                AuthorityFormLink.objects.get_or_create(authority_source=source, form_code=form_code, link_type=link_type, defaults={"note": f"{source_code} -> {form_code}"})

    def _load_flow_assertions(self):
        for a in FLOW_ASSERTIONS:
            a = dict(a)
            FlowAssertion.objects.update_or_create(assertion_id=a.pop("assertion_id"), defaults=a)
        self.stdout.write(f"  {len(FLOW_ASSERTIONS)} flow assertions")

    def _report_totals(self):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("NC Form CD-405 loaded.")
        self.stdout.write(f"  NC_CD405: facts {len(F_FACTS)} / rules {len(F_RULES)} / lines {len(F_LINES)} / diag {len(F_DIAGNOSTICS)} / tests {len(F_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}")
        self.stdout.write("=" * 60)
