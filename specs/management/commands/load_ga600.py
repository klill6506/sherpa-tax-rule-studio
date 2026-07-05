"""Load the Georgia Form 600 spec — Georgia Corporation Tax Return (TY2025).
WO-11 / S-13, the C-corporation module (form 3 of 3 per Gate-1 shape = spine + 2, DECISIONS D-13).

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
Georgia Form 600 is the GA C-corporation return. It imposes TWO taxes:
  • INCOME TAX (Schedule 1): federal taxable income -> GA additions (Sch 4, incl. the §168(k) bonus
    add-back and the §179 excess) -> GA subtractions (Sch 5, the recomputed GA depreciation) ->
    single-factor gross-receipts apportionment (Sch 6, 6 decimals) -> GA taxable income -> GA NOL
    (80% limit) -> flat 5.19% (Sch 1 L10).
  • NET WORTH TAX (Schedule 2): capital stock + paid-in surplus + retained earnings = net worth ->
    ratio -> net worth taxable by GA -> a bracket-table tax (exempt <= $100k; max $5,000 over $22M).
Schedule 3 totals income tax (col A) + net worth tax (col B). Credits (Sch 10) apply against
INCOME tax only, not net worth tax.

Georgia is the GA companion to the federal Form 1120 (`1120` / `1120_SCHL`). The S-corp analog
`GA600S` already exists (entity_types 1120S); this C-corp `GA600` was a genuine gap at the
2026-07-05 WO-11 gap-check.

═══════════════════════════════════════════════════════════════════════════
v1 SCOPE — LOCKED (Ken's Gate-1 walk 2026-07-05; DECISIONS D-13, Q4 = full).
═══════════════════════════════════════════════════════════════════════════
COMPUTES both taxes: the 5.19% income tax (federal-start + §168(k)/§179 depreciation delta +
single-factor apportionment + GA NOL 80%) AND the net worth tax bracket table.

═══════════════════════════════════════════════════════════════════════════
requires_human_review WALK ITEMS (W8-W10)
═══════════════════════════════════════════════════════════════════════════
W8. RATE — GA corporate income tax = flat 5.19% for TY2025 (HB 111; Sch 1 L10 "Line 9 x 5.19%").
    Not prorated; fiscal filers use the start-of-period rate. CONFIRM.
W9. DEPRECIATION DELTA — GA does NOT conform to §168(k): federal bonus = Schedule 4 addition; the
    recomputed GA depreciation = Schedule 5 subtraction. GA §179 for 2025 = $1,250,000 limit /
    $3,130,000 phase-out (GA INDEXES; the $1.05M/$2.62M in CLAUDE.md is the STALE 2021 figure).
    CONFIRM the 2025 GA §179 figures + the add-back/subtract mechanic.
W10. NET WORTH TAX — Schedule 2 bracket table: exempt <= $100,000 = $0; 19 brackets; maximum
    $5,000 over $22,000,000. Credits apply to income tax only, not net worth. CONFIRM the table.

═══════════════════════════════════════════════════════════════════════════
CARRIED [UNVERIFIED] / flags:
  • Conformity date (IRC as of Jan 1 2025, HB 290) corroborated by 3 professional sources; primary
    bill PDF paywalled. OBBBA NOT adopted for TY2025. Re-verify on the next GA conformity bill.
  • ⚠ CLAUDE.md "Verified Rules" GA §179 = $1.05M/$2.62M is STALE (2021). Correct it; re-check
    GA700/GA600S for the same staleness (they cite $1.05M/$2.62M per STATUS notes).
  • Multi-state apportionment beyond single-factor gross receipts (special/individualized methods) =
    RED-defer. Sch 4 nonresident/consolidated (Sch 12) net worth = structure. Re-verify at TY2026.
═══════════════════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════════════════
SAFETY GUARD — READY_TO_SEED stays False until Ken approves the review walk (W8-W10).
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
# SAFETY GUARD — flip ONLY after Ken's in-session review walk (W8-W10 above).
#
# FLIPPED 2026-07-05 — Ken APPROVED ("Approve — flip, seed, export"): W8 the
# 5.19% rate (HB 111) + single-factor gross-receipts apportionment, W9 the
# §168(k)/§179 depreciation delta (verified 2025 GA §179 $1.25M/$3.13M), W10 the
# net worth tax bracket table (<=$100k=$0, max $5,000). Validated on throwaway
# SQLite (scratchpad/validate_1120.py, 55 pass / 0 fail).
# ═══════════════════════════════════════════════════════════════════════════
READY_TO_SEED = True


FORM_JURISDICTION = "GA"  # matches GA500/GA501/GA600S/GA700 (never "georgia")
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1120"]  # GA C-corporation (the S-corp analog is GA600S)


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS (cited in f1120_source_brief.md; 2025 GA DOR sources, never memory)
# ═══════════════════════════════════════════════════════════════════════════
GA_CORP_RATE = "0.0519"            # HB 111 (2025) — 5.19% for TY beginning on/after 1/1/2025
GA_179_LIMIT = 1250000             # 2025 GA Form 4562 (Rev. 08/01/25) — GA indexes; $1.25M for 2025
GA_179_PHASEOUT = 3130000          # 2025 phase-out threshold
GA_NOL_LIMIT_PCT = "0.80"          # GA conforms to the §172 80% NOL limit (Sch 1 L6)
GA_NW_EXEMPT = 100000              # net worth <= $100,000 = $0 tax
GA_NW_MAX = 5000                   # maximum net worth tax (net worth over $22M)

# Net worth tax bracket table (2025 IT-611 p.19). (upper_bound_inclusive, tax); over the last -> GA_NW_MAX.
GA_NET_WORTH_TABLE: list[tuple[int, int]] = [
    (100000, 0), (150000, 125), (200000, 150), (300000, 200), (500000, 250),
    (750000, 300), (1000000, 500), (2000000, 750), (4000000, 1000), (6000000, 1250),
    (8000000, 1500), (10000000, 1750), (12000000, 2000), (14000000, 2500), (16000000, 3000),
    (18000000, 3500), (20000000, 4000), (22000000, 4500),
]


def _net_worth_tax(net_worth) -> int:
    """GA net worth tax from the Schedule 2 bracket table (IT-611 p.19)."""
    nw = float(net_worth)
    for upper, tax in GA_NET_WORTH_TABLE:
        if nw <= upper:
            return tax
    return GA_NW_MAX  # over $22,000,000


def _ga_income_tax(federal_ti, additions, subtractions, nol, ga_ratio):
    """GA income-tax path. Returns (ga_taxable_income, income_tax)."""
    balance = float(federal_ti) + float(additions) - float(subtractions)
    after_nol = balance - min(float(nol), float(GA_NOL_LIMIT_PCT) * max(0.0, balance))
    ga_taxable = after_nol * float(ga_ratio)
    return ga_taxable, max(0.0, ga_taxable) * float(GA_CORP_RATE)


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY TOPICS / SOURCES
# ═══════════════════════════════════════════════════════════════════════════
AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("ga_corp_tax", "Georgia Form 600 C-corporation tax: 5.19% income tax (federal-start + §168(k)/§179 "
     "depreciation add-back/subtract + single-factor gross-receipts apportionment + GA NOL 80%) and the "
     "Schedule 2 net worth tax bracket table (exempt <=$100k, max $5,000)."),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "GA_2025_F600",
        "source_type": "state_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "GA",
        "title": "2025 Georgia Form 600 — Corporation Tax Return",
        "citation": "Georgia Form 600 (Rev. 07/31/25)",
        "issuer": "Georgia Department of Revenue",
        "official_url": "https://dor.georgia.gov/",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["ga_corp_tax"],
        "excerpts": [
            {
                "excerpt_label": "Schedule 1 income tax + Schedule 2 net worth (2025 verbatim)",
                "excerpt_text": (
                    "Schedule 1 Computation of Georgia Taxable Income and Tax: L1 Federal Taxable Income; L2 "
                    "Additions (Schedule 4); L3 Total; L4 Subtractions (Schedule 5); L5 Balance; L6 Georgia NOL "
                    "deduction (Schedule 9; 80% limitation); L7 Georgia Taxable Income; L8 Passive/Capital Loss "
                    "Deduction; L9 GA Taxable Income; L10 'Income Tax Line 9 x 5.19%'. Schedule 2 Computation of "
                    "Net Worth Tax: L1 Total Capital stock issued; L2 Paid in or Capital surplus; L3 Total "
                    "Retained earnings; L4 Net Worth (L1+L2+L3); L5 Ratio (GA & domesticated foreign corp = "
                    "100%; foreign corp = Line 4, Sch 8); L6 Net Worth Taxable by Georgia (L4 x L5); L7 Net "
                    "Worth Tax (from table in instructions). Schedule 3 Computation of Tax Due/Overpayment: cols "
                    "A Income Tax, B Net Worth Tax, C Total. 'Any tax credits from Schedule 10 may be applied "
                    "against income tax liability only, not net worth tax liability.' Schedule 4 Additions: L8 "
                    "Other Additions (federal bonus depreciation add-back). Schedule 5 Subtractions: L4 Other "
                    "Subtractions (Georgia recomputed depreciation). Schedule 6 Apportionment: gross receipts "
                    "factor only, Col C 'DO NOT ROUND / COMPUTE TO SIX DECIMALS'."
                ),
                "summary_text": "Sch 1: fed TI -> +Sch 4 -> -Sch 5 -> GA NOL 80% -> apportion -> L10 5.19%. Sch 2 net worth = capital+paid-in+R/E -> ratio -> table tax. Sch 3 cols A/B/C. Credits vs income tax only.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Net worth tax bracket table (IT-611 p.19 verbatim)",
                "excerpt_text": (
                    "Net Worth Tax table: not exceeding $100,000 = $0; over 100,000-150,000 = $125; 150,000-"
                    "200,000 = $150; 200,000-300,000 = $200; 300,000-500,000 = $250; 500,000-750,000 = $300; "
                    "750,000-1,000,000 = $500; 1,000,000-2,000,000 = $750; 2,000,000-4,000,000 = $1,000; "
                    "4,000,000-6,000,000 = $1,250; 6,000,000-8,000,000 = $1,500; 8,000,000-10,000,000 = $1,750; "
                    "10,000,000-12,000,000 = $2,000; 12,000,000-14,000,000 = $2,500; 14,000,000-16,000,000 = "
                    "$3,000; 16,000,000-18,000,000 = $3,500; 18,000,000-20,000,000 = $4,000; 20,000,000-"
                    "22,000,000 = $4,500; over 22,000,000 = $5,000."
                ),
                "summary_text": "Net worth tax: $0 <=$100k; $125 at $100-150k ... $4,500 at $20-22M; $5,000 over $22M. 19 brackets.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "GA_2025_IT611",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "GA",
        "title": "2025 Georgia IT-611 — Corporation Income Tax Instruction Booklet",
        "citation": "Georgia IT-611 (2025)",
        "issuer": "Georgia Department of Revenue",
        "official_url": "https://dor.georgia.gov/",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.4,
        "topics": ["ga_corp_tax"],
        "excerpts": [
            {
                "excerpt_label": "5.19% rate + single-factor apportionment + conformity (IT-611 verbatim)",
                "excerpt_text": (
                    "'The tax rate for the taxable year beginning on or after January 1, 2025 is 5.19%. The tax "
                    "rate is not prorated but is applicable for the entire tax period. Fiscal filers must use "
                    "the tax rate based on the start of their filing period.' (HB 111, 2025.) 'Georgia income "
                    "tax is 5.19% of the Georgia taxable income.' Apportionment: 'the Georgia apportionment "
                    "ratio shall be computed by applying only the gross receipts factor' (single-factor, six "
                    "decimals; O.C.G.A. §48-7-31). Conformity: IRC as amended and in effect on January 1, 2025 "
                    "(HB 290; O.C.G.A. §48-1-2(14)) — OBBBA (enacted July 4, 2025) NOT adopted for TY2025. Due "
                    "on or before the 15th day of the 4th month (calendar year = April 15, 2026)."
                ),
                "summary_text": "IT-611: 5.19% (HB 111), not prorated; single-factor gross-receipts apportionment, 6 decimals (§48-7-31); conformity Jan 1 2025 (HB 290), OBBBA not adopted; due 4th month 15th.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "GA_2025_F4562",
        "source_type": "state_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "GA",
        "title": "2025 Georgia Form 4562 — Depreciation & Amortization (GA §168(k)/§179 non-conformity)",
        "citation": "Georgia Form 4562 (Rev. 08/01/25)",
        "issuer": "Georgia Department of Revenue",
        "official_url": "https://dor.georgia.gov/",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.3,
        "topics": ["ga_corp_tax"],
        "excerpts": [
            {
                "excerpt_label": "GA §179 2025 + §168(k) non-conformity (verbatim)",
                "excerpt_text": (
                    "'Georgia's I.R.C. Section 179 deduction is ... $1,220,000 for 2024 and $1,250,000 for 2025. "
                    "The related phase out ... is $3,050,000 for 2024 and $3,130,000 for 2025.' Georgia 'has not "
                    "adopted the 30%, 50% and 100% bonus depreciation rules of I.R.C. Section 168(k)' and 'has "
                    "not adopted the Section 179 deduction for certain real property.' Mechanic: compute federal "
                    "depreciation with bonus on the federal 4562; recompute for Georgia without §168(k) and "
                    "using GA's §179 limit on the Georgia 4562; the federal bonus/excess is a Schedule 4 "
                    "addition; the recomputed Georgia depreciation (and later-year catch-up) is a Schedule 5 "
                    "subtraction. (GA indexes §179; the $1,050,000/$2,620,000 figure is the 2021 amount.)"
                ),
                "summary_text": "GA §179 2025 = $1,250,000 / $3,130,000 (GA indexes; $1.05M/$2.62M is 2021). No §168(k) bonus. Bonus = Sch 4 add; GA depreciation = Sch 5 subtract.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "OCGA_CORP",
        "source_type": "statute",
        "source_rank": "controlling",
        "jurisdiction_code": "GA",
        "title": "O.C.G.A. §48-7-31 (apportionment) · §48-13-70 et seq. (net worth tax) · §48-1-2(14) (conformity)",
        "citation": "O.C.G.A. §48-7-31; §48-13-70 et seq.; §48-1-2(14)",
        "issuer": "Georgia General Assembly",
        "official_url": "https://law.justia.com/codes/georgia/title-48/",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.2,
        "topics": ["ga_corp_tax"],
        "excerpts": [
            {
                "excerpt_label": "Single-factor apportionment + net worth tax basis (substance)",
                "excerpt_text": (
                    "O.C.G.A. §48-7-31: Georgia apportions business income by a single gross-receipts factor. "
                    "O.C.G.A. §48-13-70 et seq.: the net worth tax is imposed on domestic corporations on total "
                    "net worth and on foreign corporations on net worth employed within Georgia (apportioned per "
                    "Schedule 8), per the graduated table; exempt at or below $100,000; maximum $5,000. "
                    "O.C.G.A. §48-1-2(14): the Internal Revenue Code is adopted as in effect on the statutory "
                    "conformity date (HB 290 sets January 1, 2025 for TY2025)."
                ),
                "summary_text": "§48-7-31 single-factor gross receipts; §48-13-70 net worth tax (domestic total / foreign apportioned; $100k exempt, $5,000 max); §48-1-2(14) IRC conformity date.",
                "is_key_excerpt": True,
            },
        ],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("GA_2025_F600", "GA600", "governs"),
    ("GA_2025_IT611", "GA600", "governs"),
    ("GA_2025_F4562", "GA600", "governs"),
    ("OCGA_CORP", "GA600", "governs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM — GA600
# ═══════════════════════════════════════════════════════════════════════════
F_FACTS: list[dict] = [
    # ── Income tax (Schedule 1) ──
    {"fact_key": "federal_taxable_income", "label": "Federal taxable income — Form 1120 L30 (Sch 1 L1)", "data_type": "decimal", "required": False, "sort_order": 1,
     "notes": "GA income-tax start. Cross-ref from the federal 1120 spine."},
    {"fact_key": "federal_bonus_depreciation", "label": "Federal §168(k) bonus depreciation taken (GA Schedule 4 add-back)", "data_type": "decimal", "required": False, "sort_order": 2,
     "notes": "W9. GA does NOT conform to §168(k) — federal bonus is a GA addition (asset-level GA-4562 figure)."},
    {"fact_key": "federal_section_179", "label": "Federal §179 deduction taken (for the GA §179 delta)", "data_type": "decimal", "required": False, "sort_order": 3,
     "notes": "W9. GA §179 limit 2025 = $1,250,000. Federal §179 above the GA limit is an addition."},
    {"fact_key": "other_additions", "label": "Other GA additions — state/muni bond interest, non-GA taxes, etc. (Sch 4)", "data_type": "decimal", "required": False, "sort_order": 4},
    {"fact_key": "ga_depreciation_subtraction", "label": "Georgia recomputed depreciation subtraction (Sch 5 L4)", "data_type": "decimal", "required": False, "sort_order": 5,
     "notes": "W9. GA-basis depreciation without §168(k) + later-year catch-up (asset-level GA-4562 figure)."},
    {"fact_key": "other_subtractions", "label": "Other GA subtractions — US-obligation interest, etc. (Sch 5)", "data_type": "decimal", "required": False, "sort_order": 6},
    {"fact_key": "ga_nol_carryover", "label": "Georgia NOL deduction available (Sch 1 L6 / Sch 9; 80% limit)", "data_type": "decimal", "required": False, "sort_order": 7},
    # ── Apportionment (Schedule 6) ──
    {"fact_key": "gross_receipts_georgia", "label": "Gross receipts within Georgia (Sch 6 L1 Col A)", "data_type": "decimal", "required": False, "sort_order": 10},
    {"fact_key": "gross_receipts_everywhere", "label": "Gross receipts everywhere (Sch 6 L1 Col B)", "data_type": "decimal", "required": False, "sort_order": 11},
    {"fact_key": "is_multistate", "label": "Multi-state corporation (apportion)? — if no, GA ratio = 100%", "data_type": "boolean", "required": False, "sort_order": 12},
    # ── Net worth tax (Schedule 2) ──
    {"fact_key": "capital_stock_issued", "label": "Total capital stock issued (Sch 2 L1)", "data_type": "decimal", "required": False, "sort_order": 20},
    {"fact_key": "paid_in_surplus", "label": "Paid-in or capital surplus (Sch 2 L2)", "data_type": "decimal", "required": False, "sort_order": 21},
    {"fact_key": "retained_earnings_nw", "label": "Total retained earnings (Sch 2 L3)", "data_type": "decimal", "required": False, "sort_order": 22},
    {"fact_key": "net_worth_ratio", "label": "Net worth ratio — GA/domesticated = 1.00; foreign = Sch 8 ratio (Sch 2 L5)", "data_type": "decimal", "required": False, "sort_order": 23,
     "notes": "Default 1.00 (domestic/domesticated). Foreign corps apportion net worth via Schedule 8."},
    # ── Credits (Schedule 10) ──
    {"fact_key": "income_tax_credits", "label": "GA income tax credits — Schedule 10 (income tax only)", "data_type": "decimal", "required": False, "sort_order": 30,
     "notes": "W10. Credits apply against INCOME tax only, never the net worth tax."},
]

F_RULES: list[dict] = [
    {"rule_id": "R-GA600-ADD", "title": "Schedule 4 additions — §168(k) bonus + §179 excess (Sch 1 L2)", "rule_type": "calculation",
     "formula": "section_179_excess = max(0, federal_section_179 - 1250000) ; additions = federal_bonus_depreciation + section_179_excess + other_additions",
     "inputs": ["federal_bonus_depreciation", "federal_section_179", "other_additions"], "outputs": ["additions"], "sort_order": 1,
     "description": "W9. GA does not conform to §168(k): federal bonus depreciation is added back (Sch 4 L8). Federal §179 above the GA 2025 limit ($1,250,000) is also an addition. Plus other GA additions (Sch 4)."},
    {"rule_id": "R-GA600-SUB", "title": "Schedule 5 subtractions — GA recomputed depreciation (Sch 1 L4)", "rule_type": "calculation",
     "formula": "subtractions = ga_depreciation_subtraction + other_subtractions",
     "inputs": ["ga_depreciation_subtraction", "other_subtractions"], "outputs": ["subtractions"], "sort_order": 2,
     "description": "W9. The Georgia-basis depreciation recomputed without §168(k) (and using the GA §179 limit), plus later-year catch-up as GA basis depreciates, is a Schedule 5 subtraction. Plus other GA subtractions."},
    {"rule_id": "R-GA600-APPORT", "title": "Single-factor gross-receipts apportionment (Sch 6, 6 decimals)", "rule_type": "calculation",
     "formula": "ga_ratio = 1.0 if not is_multistate else round(gross_receipts_georgia / gross_receipts_everywhere, 6)",
     "inputs": ["is_multistate", "gross_receipts_georgia", "gross_receipts_everywhere"], "outputs": ["ga_ratio"], "sort_order": 3,
     "description": "W8. O.C.G.A. §48-7-31: Georgia apportions by the gross-receipts factor ONLY (single factor), computed to six decimals. A GA-only corporation apportions 100%."},
    {"rule_id": "R-GA600-INCOME", "title": "Georgia income tax — 5.19% (Sch 1 L10)", "rule_type": "calculation",
     "formula": ("balance = federal_taxable_income + additions - subtractions ; "
                 "nol = min(ga_nol_carryover, 0.80 * max(0, balance)) ; ga_taxable = (balance - nol) * ga_ratio ; "
                 "income_tax = max(0, ga_taxable) * 0.0519"),
     "inputs": ["federal_taxable_income", "ga_nol_carryover"], "outputs": ["ga_taxable_income", "income_tax"], "sort_order": 4,
     "description": "W8. Federal taxable income + Sch 4 additions - Sch 5 subtractions - GA NOL (80% of the balance) = GA taxable income, apportioned by the single-factor ratio, times the 5.19% rate (HB 111)."},
    {"rule_id": "R-GA600-NETWRTH", "title": "Net worth tax — Schedule 2 bracket table", "rule_type": "calculation",
     "formula": "net_worth = capital_stock_issued + paid_in_surplus + retained_earnings_nw ; nw_taxable = net_worth * net_worth_ratio ; net_worth_tax = table(nw_taxable) [<=100k=0; max 5000 over 22M]",
     "inputs": ["capital_stock_issued", "paid_in_surplus", "retained_earnings_nw", "net_worth_ratio"], "outputs": ["net_worth", "net_worth_tax"], "sort_order": 5,
     "description": "W10. Net worth (capital stock + paid-in surplus + retained earnings) times the ratio (100% domestic; Sch 8 for foreign) = net worth taxable by GA -> the graduated bracket-table tax (O.C.G.A. §48-13-70; exempt <=$100,000; maximum $5,000 over $22,000,000)."},
    {"rule_id": "R-GA600-TOTAL", "title": "Total tax — Schedule 3 (income tax − credits + net worth tax)", "rule_type": "calculation",
     "formula": "income_tax_net = max(0, income_tax - income_tax_credits) ; total_tax = income_tax_net + net_worth_tax",
     "inputs": ["income_tax_credits"], "outputs": ["total_tax"], "sort_order": 6,
     "description": "W10. Schedule 3 columns A income tax + B net worth tax = C total. Schedule 10 credits reduce the INCOME tax only (not the net worth tax)."},
]

F_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-GA600-ADD", "GA_2025_F4562", "primary", "GA §168(k)/§179 add-back"),
    ("R-GA600-ADD", "GA_2025_F600", "secondary", "Schedule 4 additions"),
    ("R-GA600-SUB", "GA_2025_F4562", "primary", "GA recomputed depreciation subtraction"),
    ("R-GA600-SUB", "GA_2025_F600", "secondary", "Schedule 5 subtractions"),
    ("R-GA600-APPORT", "OCGA_CORP", "primary", "§48-7-31 single-factor gross receipts"),
    ("R-GA600-APPORT", "GA_2025_F600", "secondary", "Schedule 6 six decimals"),
    ("R-GA600-INCOME", "GA_2025_IT611", "primary", "5.19% rate (HB 111)"),
    ("R-GA600-INCOME", "GA_2025_F600", "secondary", "Schedule 1 L1-L10"),
    ("R-GA600-NETWRTH", "GA_2025_F600", "primary", "Schedule 2 + net worth table (IT-611 p.19)"),
    ("R-GA600-NETWRTH", "OCGA_CORP", "secondary", "§48-13-70 net worth tax"),
    ("R-GA600-TOTAL", "GA_2025_F600", "primary", "Schedule 3 cols A/B/C; credits vs income tax only"),
]

F_LINES: list[dict] = [
    {"line_number": "S4-L9", "description": "Schedule 4 total additions (→ Sch 1 L2)", "line_type": "calculated", "source_rules": ["R-GA600-ADD"], "sort_order": 1},
    {"line_number": "S5-L5", "description": "Schedule 5 total subtractions (→ Sch 1 L4)", "line_type": "calculated", "source_rules": ["R-GA600-SUB"], "sort_order": 2},
    {"line_number": "S6-L2", "description": "Schedule 6 Georgia apportionment ratio (6 decimals)", "line_type": "calculated", "source_rules": ["R-GA600-APPORT"], "sort_order": 3},
    {"line_number": "S1-L10", "description": "Schedule 1 L10 Georgia income tax (× 5.19%)", "line_type": "calculated", "source_rules": ["R-GA600-INCOME"], "sort_order": 4},
    {"line_number": "S2-L7", "description": "Schedule 2 L7 Net worth tax (bracket table)", "line_type": "calculated", "source_rules": ["R-GA600-NETWRTH"], "sort_order": 5},
    {"line_number": "S3-C", "description": "Schedule 3 Col C total tax (income + net worth)", "line_type": "calculated", "source_rules": ["R-GA600-TOTAL"], "sort_order": 6},
]

F_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_GA600_BONUS", "title": "GA §168(k) bonus depreciation add-back", "severity": "info",
     "condition": "federal_bonus_depreciation > 0",
     "message": "Georgia does not conform to IRC §168(k) bonus depreciation. The federal bonus depreciation taken is added back on Schedule 4 (Other Additions); the depreciation recomputed for Georgia without bonus is subtracted on Schedule 5. Enter the asset-level figures from the Georgia Form 4562.",
     "notes": "W9."},
    {"diagnostic_id": "D_GA600_179", "title": "GA §179 limit 2025 = $1,250,000 / $3,130,000 (indexed)", "severity": "warning",
     "condition": "federal_section_179 > 1250000",
     "message": "Georgia's §179 deduction limit for 2025 is $1,250,000 with a $3,130,000 investment phase-out (Georgia indexes its §179; it did NOT adopt the OBBBA $2.5M/$4M amounts). Federal §179 above the Georgia limit is added back on Schedule 4. (Note: $1,050,000/$2,620,000 is the stale 2021 figure.)",
     "notes": "W9. Phase-out is a separate diagnostic if investment > $3,130,000."},
    {"diagnostic_id": "D_GA600_APPORT", "title": "Single-factor gross-receipts apportionment (6 decimals)", "severity": "info",
     "condition": "is_multistate",
     "message": "Georgia apportions business income using only the gross-receipts factor (single factor), computed to six decimals (O.C.G.A. §48-7-31). Special or individualized apportionment methods are not modeled in v1.",
     "notes": "W8."},
    {"diagnostic_id": "D_GA600_NWCRED", "title": "Credits apply to income tax only, not net worth tax", "severity": "info",
     "condition": "income_tax_credits > 0 and net_worth_tax > 0",
     "message": "Schedule 10 tax credits may be applied against the Georgia income tax liability ONLY — they cannot reduce the net worth tax. The net worth tax is a separate liability on Schedule 3 column B.",
     "notes": "W10."},
    {"diagnostic_id": "D_GA600_CONFORM", "title": "GA IRC conformity Jan 1 2025 — OBBBA not adopted", "severity": "info",
     "condition": "always (informational)",
     "message": "Georgia conforms to the Internal Revenue Code as in effect on January 1, 2025 (HB 290; O.C.G.A. §48-1-2(14)). OBBBA (enacted July 4, 2025) is NOT adopted for TY2025, and Georgia's standing §168(k)/§179 decoupling applies regardless. Re-verify on the next Georgia conformity bill.",
     "notes": "Conformity flag."},
]

F_SCENARIOS: list[dict] = [
    {"scenario_name": "GA600-A — GA-only corp: 5.19% income tax", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"federal_taxable_income": 200000},
     "expected_outputs": {"ga_taxable_income": 200000, "income_tax": 10380},
     "notes": "GA-only (ratio 100%). 200,000 x 5.19% = 10,380."},
    {"scenario_name": "GA600-B — §168(k) bonus add-back", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"federal_taxable_income": 100000, "federal_bonus_depreciation": 80000, "ga_depreciation_subtraction": 20000},
     "expected_outputs": {"additions": 80000, "subtractions": 20000, "ga_taxable_income": 160000, "income_tax": 8304},
     "notes": "GA adds back 80,000 bonus, subtracts 20,000 GA depreciation: 100,000 + 80,000 - 20,000 = 160,000 x 5.19% = 8,304."},
    {"scenario_name": "GA600-C — §179 excess over the GA limit", "scenario_type": "edge", "sort_order": 3,
     "inputs": {"federal_taxable_income": 500000, "federal_section_179": 2000000},
     "expected_outputs": {"additions": 750000, "ga_taxable_income": 1250000, "income_tax": 64875},
     "notes": "Federal §179 2,000,000 - GA limit 1,250,000 = 750,000 addition. 500,000 + 750,000 = 1,250,000 x 5.19% = 64,875."},
    {"scenario_name": "GA600-D — multi-state single-factor apportionment", "scenario_type": "edge", "sort_order": 4,
     "inputs": {"federal_taxable_income": 1000000, "is_multistate": True, "gross_receipts_georgia": 300000, "gross_receipts_everywhere": 1000000},
     "expected_outputs": {"ga_ratio": 0.3, "ga_taxable_income": 300000, "income_tax": 15570},
     "notes": "Ratio = 300,000/1,000,000 = 0.300000; GA taxable 1,000,000 x 0.30 = 300,000 x 5.19% = 15,570."},
    {"scenario_name": "GA600-E — net worth tax bracket", "scenario_type": "normal", "sort_order": 5,
     "inputs": {"capital_stock_issued": 500000, "paid_in_surplus": 300000, "retained_earnings_nw": 700000, "net_worth_ratio": 1.0},
     "expected_outputs": {"net_worth": 1500000, "net_worth_tax": 750},
     "notes": "Net worth 1,500,000 falls in the 1,000,000-2,000,000 bracket = $750."},
    {"scenario_name": "GA600-F — net worth tax maximum ($5,000 over $22M)", "scenario_type": "edge", "sort_order": 6,
     "inputs": {"capital_stock_issued": 10000000, "paid_in_surplus": 8000000, "retained_earnings_nw": 7000000, "net_worth_ratio": 1.0},
     "expected_outputs": {"net_worth": 25000000, "net_worth_tax": 5000},
     "notes": "Net worth 25,000,000 > 22,000,000 -> maximum $5,000."},
    {"scenario_name": "GA600-G — net worth exempt (<= $100k)", "scenario_type": "edge", "sort_order": 7,
     "inputs": {"capital_stock_issued": 50000, "paid_in_surplus": 30000, "retained_earnings_nw": 15000, "net_worth_ratio": 1.0},
     "expected_outputs": {"net_worth": 95000, "net_worth_tax": 0},
     "notes": "Net worth 95,000 <= 100,000 -> $0 net worth tax."},
    {"scenario_name": "GA600-H — credits offset income tax, not net worth", "scenario_type": "normal", "sort_order": 8,
     "inputs": {"federal_taxable_income": 200000, "capital_stock_issued": 1500000, "net_worth_ratio": 1.0, "income_tax_credits": 5000},
     "expected_outputs": {"income_tax": 10380, "net_worth_tax": 750, "total_tax": 6130},
     "notes": "Income tax 10,380 - 5,000 credit = 5,380; + net worth 750 = 6,130. Credit does NOT reduce the 750 net worth tax."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORMS registry + flow assertions
# ═══════════════════════════════════════════════════════════════════════════
FORMS: list[dict] = [
    {
        "identity": {"form_number": "GA600", "form_title": "Georgia Form 600 — Corporation Tax Return (TY2025)",
                     "notes": "WO-11 / S-13 (form 3 of 3, DECISIONS D-13 Q4 = full). GA C-corporation dual tax: INCOME tax (federal taxable income -> Sch 4 additions incl. §168(k) bonus add-back + §179 excess over the GA $1.25M limit -> Sch 5 GA recomputed-depreciation subtraction -> single-factor gross-receipts apportionment, 6 decimals -> GA NOL 80% -> flat 5.19%, HB 111) AND NET WORTH tax (Schedule 2 bracket table: exempt <=$100k, max $5,000 over $22M). Schedule 3 totals income + net worth; Schedule 10 credits reduce income tax only. Conformity Jan 1 2025 (HB 290), OBBBA not adopted. The S-corp analog is GA600S."},
        "facts": F_FACTS, "rules": F_RULES, "rule_links": F_RULE_LINKS,
        "lines": F_LINES, "diagnostics": F_DIAGNOSTICS, "scenarios": F_SCENARIOS,
    },
]

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-GA600-INCOME", "title": "GA income tax = 5.19% of apportioned GA taxable income", "assertion_type": "reconciliation",
     "entity_types": ["1120"], "status": "draft", "sort_order": 1,
     "description": "Federal taxable income + Sch 4 additions − Sch 5 subtractions − GA NOL (80%), apportioned by the single-factor gross-receipts ratio, times 5.19%.",
     "definition": {"rule": "R-GA600-INCOME", "check": "income_tax = max(0, ((fed_ti + add - sub - nol) * ga_ratio)) * 0.0519"}},
    {"assertion_id": "FA-GA600-NW", "title": "Net worth tax from the Schedule 2 bracket table", "assertion_type": "reconciliation",
     "entity_types": ["1120"], "status": "draft", "sort_order": 2,
     "description": "Net worth (capital stock + paid-in + retained earnings) × ratio → the graduated table; exempt ≤ $100k, maximum $5,000 over $22M.",
     "definition": {"rule": "R-GA600-NETWRTH", "check": "net_worth_tax = table(net_worth * ratio)"}},
    {"assertion_id": "FA-GA600-TOTAL", "title": "Total tax = income tax − credits + net worth tax", "assertion_type": "reconciliation",
     "entity_types": ["1120"], "status": "draft", "sort_order": 3,
     "description": "Schedule 3: income tax (net of Schedule 10 credits) + net worth tax. Credits never reduce the net worth tax.",
     "definition": {"rule": "R-GA600-TOTAL", "check": "total_tax = max(0, income_tax - credits) + net_worth_tax"}},
]


# ═══════════════════════════════════════════════════════════════════════════
# Command
# ═══════════════════════════════════════════════════════════════════════════
class Command(BaseCommand):
    help = (
        "Load the Georgia Form 600 spec (GA C-corporation income + net worth tax, TY2025). "
        "Refuses to seed until Ken sets READY_TO_SEED=True after the review walk (W8-W10)."
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad Georgia Form 600 spec (Corporation Tax Return)\n"))
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
                "\nREFUSING TO SEED FORM GA600: not cleared to seed.\n\n"
                "Content is authored, but seeding is gated until Ken reviews the packet\n"
                "(W8 the 5.19% rate + single-factor apportionment; W9 the §168(k)/§179\n"
                "depreciation delta with the 2025 GA §179 $1.25M/$3.13M figures; W10 the\n"
                "net worth tax bracket table) and flips the sentinel.\n\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True to proceed)\n\n"
                f"Currently empty / placeholder:\n  {still_empty}\n\n"
                "To proceed: review the module-level data lists (and f1120_source_brief.md),\n"
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
        self.stdout.write("Georgia Form 600 loaded.")
        self.stdout.write(
            f"  GA600: facts {len(F_FACTS)} / rules {len(F_RULES)} / lines {len(F_LINES)} / "
            f"diag {len(F_DIAGNOSTICS)} / tests {len(F_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}"
        )
        self.stdout.write("=" * 60)
