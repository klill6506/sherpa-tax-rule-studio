"""Load the South Carolina Form SC1120 spec — 'C' Corporation Income Tax Return (TY2025).
WO-12, the reuse-state C-corp batch (form 1 of 3). Extends the federal 1120 module (WO-11).

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
SC1120 is South Carolina's C-corporation return: a flat 5% income tax on SC taxable income
(federal-TI start + SC add/subtract + single-factor apportionment) PLUS the annual corporate
license fee ($15 + capital & paid-in surplus × .001, min $25). Reuses the SC1120S structure
(license fee, apportionment, §168(k) decouple, conformity) already in the tool; the C-corp
difference is the full 5% income tax on all SC taxable income (vs the S-corp's ATB/PTET).

Greenfield: no `SC1120` at the 2026-07-05 gap-check (SC1120S exists — the S-corp).

═══════════════════════════════════════════════════════════════════════════
v1 SCOPE — LOCKED (Ken's Gate-1 walk 2026-07-05; DECISIONS D-14). See state_ccorp_batch_source_brief.md.
═══════════════════════════════════════════════════════════════════════════
COMPUTES (Q1 full): 5% income tax (federal-TI + §168(k) bonus decouple add-back + §179 excess over the
SC pre-OBBBA limit -> single-factor apportionment -> SC NOL -> 5%); the license fee ($15 + capital×.001,
min $25); total = income tax + license fee.

═══════════════════════════════════════════════════════════════════════════
requires_human_review WALK ITEMS (W1-W3)
═══════════════════════════════════════════════════════════════════════════
W1. 5% RATE + license fee ($15 + capital×.001, min $25) + federal-TI start. CONFIRM.
W2. DEPRECIATION — SC decouples §168(k) (add back federal-vs-SC difference in year of service, recover
    over remaining life); §179 conforms at the 12/31/2024 level = $1,250,000 / $3,130,000 (pre-OBBBA). CONFIRM.
W3. ⚠ H.3368 LIVE WIRE (Q3) — SC has NOT adopted OBBBA as of ~March 2026; H.3368 (pending, not signed)
    would adopt OBBBA RETROACTIVE to TY2025, flipping §168(k)/§179 ($2.5M/$4M, no add-back). SCDOR extended
    the SC filing deadline to Oct 15 2026 to await it. Authored to CURRENT 12/31/2024 law + a prominent flag.
    RE-VERIFY H.3368's status BEFORE SEEDING SC (AL/NC seed independently). CONFIRM.

═══════════════════════════════════════════════════════════════════════════
CARRIED [UNVERIFIED]: H.3368 enactment (re-verify before seed); SC apportionment decimal precision not
printed (do not assert); §179 $1.25M/$3.13M derived from pre-OBBBA indexing (year-keyed). Re-verify at TY2026.
═══════════════════════════════════════════════════════════════════════════

SAFETY GUARD — READY_TO_SEED stays False until Ken approves the review walk (W1-W3).
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

# ═══════════════════════════════════════════════════════════════════════════
# SAFETY GUARD — flip ONLY after Ken's review walk (W1-W3). ⚠ AND re-verify H.3368 first.
#
# FLIPPED 2026-07-05 — Ken APPROVED ("Seed all three now"): W1 the 5% rate + license fee,
# W2 the §168(k) decouple + §179 $1.25M/$3.13M, W3 the H.3368 live wire (authored to the
# ENACTED 12/31/2024 law with the D_SC1120_H3368 flag; Ken accepts a §179/bonus amend if
# H.3368 passes retroactively). Validated (scratchpad/validate_state_ccorp.py, 41/0).
# ═══════════════════════════════════════════════════════════════════════════
READY_TO_SEED = True


FORM_JURISDICTION = "SC"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1120"]

# Verified constants (state_ccorp_batch_source_brief.md; SC1120 Rev. 7/2/25 / SC1120I 2025 / SCTIED-2025)
SC_RATE = "0.05"                    # §12-6-530 — 5% flat corporate income tax
SC_179_LIMIT = 1250000             # pre-OBBBA (12/31/2024 conformity) 2025 §179 limit — as SC1040/SC1120S
SC_179_PHASEOUT = 3130000          # pre-OBBBA 2025 §179 phaseout
LICENSE_RATE = "0.001"             # §12-20-50 — $1 per $1,000 of capital + paid-in surplus
LICENSE_ADD = 15                   # + $15
LICENSE_MIN = 25                   # minimum $25 per taxpayer (not apportioned)


def _sc_license_fee(capital_and_surplus) -> float:
    """SC1120 Part II license fee: capital×.001 + $15, min $25 (§12-20-50)."""
    return max(float(LICENSE_MIN), float(capital_and_surplus) * float(LICENSE_RATE) + float(LICENSE_ADD))


def _sc_income_tax(fed_ti, additions, subtractions, nol, ratio):
    """SC income-tax path. Returns (sc_taxable, income_tax)."""
    balance = float(fed_ti) + float(additions) - float(subtractions)
    apportioned = balance * float(ratio)
    sc_taxable = apportioned - min(float(nol), max(0.0, apportioned))
    return sc_taxable, max(0.0, sc_taxable) * float(SC_RATE)


AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("sc_corp_tax", "South Carolina SC1120 C-corporation: 5% income tax (federal-TI + §168(k) decouple + "
     "§179 pre-OBBBA $1.25M/$3.13M + single-factor apportionment), the §12-20-50 license fee, and the "
     "H.3368/OBBBA conformity live wire."),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "SC_2025_SC1120", "source_type": "state_form", "source_rank": "primary_official",
        "jurisdiction_code": "SC", "title": "2025 South Carolina SC1120 — 'C' Corporation Income Tax Return",
        "citation": "SC1120 (Rev. 7/2/25)", "issuer": "South Carolina Department of Revenue",
        "official_url": "https://dor.sc.gov/sites/dor/files/forms/SC1120.pdf",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.5, "topics": ["sc_corp_tax"],
        "excerpts": [{
            "excerpt_label": "SC1120 line flow + 5% rate + license fee (Rev. 7/2/25 verbatim)",
            "excerpt_text": (
                "Part I: L1 'Federal taxable income from federal tax return'; L2 'Net adjustment from Schedule "
                "A and B, line 12'; L3 total net income as reconciled; L4 (multistate -> Schedule G line 6); L5 "
                "'South Carolina net operating loss carryover'; L6 'South Carolina net income subject to tax'; L7 "
                "'Tax (multiply line 6 by 5%)'. Part II: L20 'Total capital and paid in surplus'; L21 'License "
                "Fee: multiply line 20 by .001 then add $15 (Fee cannot be less than $25 per taxpayer)'; grand "
                "total (income tax + license fee) on L30. Schedule A&B: additions (taxes measured by income, "
                "federal NOL) and deductions (US-obligation interest, §168(k) depreciation difference) -> L12 "
                "net adjustment -> Part I L2. Apportionment: Schedule H-1 single sales factor (TPP) / H-2 gross "
                "receipts (service). SC NOL: federal carryforward period, no carryback (§12-6-1130(4))."
            ),
            "summary_text": "SC1120: L1 fed TI -> L2 Sch A&B adj -> L6 SC net income -> L7 x 5%; Part II L21 license fee (capital×.001 + $15, min $25); L30 total. Single-factor apportionment.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "SC_2025_SC1120I", "source_type": "official_instructions", "source_rank": "primary_official",
        "jurisdiction_code": "SC", "title": "2025 SC1120I — Instructions for C and S Corporation Income Tax Returns",
        "citation": "SC1120I (2025)", "issuer": "South Carolina Department of Revenue",
        "official_url": "https://dor.sc.gov/sites/dor/files/forms/SC1120I.pdf",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.4, "topics": ["sc_corp_tax"],
        "excerpts": [{
            "excerpt_label": "§168(k) decouple + conformity 12/31/2024 + H.3368 (SC1120I verbatim)",
            "excerpt_text": (
                "'South Carolina does not recognize any of the federal special depreciation allowances, "
                "including bonus depreciation, provided in IRC Section 168(k) through (n)... Add back the "
                "difference between federal depreciation and South Carolina depreciation for the tax year in "
                "which the property was placed in service. You will be able to claim an additional depreciation "
                "deduction for each remaining tax year of the property's depreciable life.' 'What's New?': "
                "'South Carolina recognizes the Internal Revenue Code (IRC) as amended through December 31, "
                "2024, except as otherwise provided' (§12-6-40; non-adopted sections §12-6-50). §179 is NOT on "
                "the §12-6-50 non-adopted list -> SC conforms to §179 at the 12/31/2024 (pre-OBBBA) level = "
                "$1,250,000 limit / $3,130,000 phaseout for 2025. LIVE WIRE: SC had not adopted OBBBA as of "
                "early 2026; H.3368 (pending) would adopt full OBBBA conformity retroactive to TY2025; SCDOR "
                "extended the TY2025 SC filing deadline to October 15, 2026 to await it."
            ),
            "summary_text": "SC decouples §168(k) (year-of-service add-back, recover over life); §179 conforms pre-OBBBA $1.25M/$3.13M; conformity 12/31/2024; H.3368 could flip it retroactively for TY2025.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "SC_ACT63_2025_CONFORMITY", "source_type": "statute", "source_rank": "controlling",
        "jurisdiction_code": "SC", "title": "SC Act 63 of 2025 (S.507) — IRC conformity as amended through 12/31/2024",
        "citation": "S.C. Code Ann. §12-6-40; §12-6-50", "issuer": "South Carolina General Assembly",
        "official_url": "https://www.scstatehouse.gov/",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.3, "topics": ["sc_corp_tax"],
        "excerpts": [{
            "excerpt_label": "SC conformity 12/31/2024 + §12-6-50 non-adopted list (re-declared)",
            "excerpt_text": (
                "§12-6-40: South Carolina conforms to the IRC as amended through December 31, 2024, subject to "
                "the exceptions in §12-6-50. §12-6-50 lists the non-adopted IRC sections — including §168(k) "
                "bonus depreciation and §163(j). §179 is NOT on the non-adopted list, so SC conforms to §179 at "
                "the 12/31/2024 (pre-OBBBA) level. Did NOT adopt OBBBA for TY2025."
            ),
            "summary_text": "§12-6-40 conformity 12/31/2024; §12-6-50 decouples §168(k)/§163(j) but not §179; OBBBA not adopted.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "SC_CODE_CORP", "source_type": "statute", "source_rank": "controlling",
        "jurisdiction_code": "SC", "title": "S.C. Code §12-6-530 (5% rate) · §12-20-50 (license fee) · §12-6-2252 (apportionment)",
        "citation": "S.C. Code Ann. §12-6-530; §12-20-50/60; §12-6-2252/2290", "issuer": "South Carolina General Assembly",
        "official_url": "https://www.scstatehouse.gov/code/title12.php",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.2, "topics": ["sc_corp_tax"],
        "excerpts": [{
            "excerpt_label": "5% rate + license fee + single-sales-factor apportionment (substance)",
            "excerpt_text": (
                "§12-6-530: a 5% income tax on the SC taxable income of a corporation. §12-20-50: an annual "
                "license fee of $15 plus $1 for each $1,000 (or fraction) of capital stock and paid-in surplus, "
                "minimum $25 (§12-20-60 apportions the fee for multistate corps, but the $25 minimum is not "
                "apportioned). §12-6-2252: single sales factor for taxpayers dealing in tangible personal "
                "property; §12-6-2290: gross-receipts ratio for others."
            ),
            "summary_text": "§12-6-530 5% rate; §12-20-50 license fee ($15 + capital×.001, min $25); §12-6-2252 single sales factor.",
            "is_key_excerpt": True,
        }],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("SC_2025_SC1120", "SC1120", "governs"), ("SC_2025_SC1120I", "SC1120", "governs"),
    ("SC_ACT63_2025_CONFORMITY", "SC1120", "governs"), ("SC_CODE_CORP", "SC1120", "governs"),
]


F_FACTS: list[dict] = [
    {"fact_key": "federal_taxable_income", "label": "Federal taxable income — federal 1120 L30 (SC1120 L1)", "data_type": "decimal", "required": False, "sort_order": 1},
    {"fact_key": "federal_bonus_depreciation", "label": "Federal §168(k) bonus depreciation taken (SC add-back, Sch A&B)", "data_type": "decimal", "required": False, "sort_order": 2,
     "notes": "W2. SC decouples §168(k) — add back the federal-vs-SC depreciation difference in the placed-in-service year."},
    {"fact_key": "federal_section_179", "label": "Federal §179 deduction taken (for the SC §179 excess)", "data_type": "decimal", "required": False, "sort_order": 3,
     "notes": "W2. SC §179 limit (pre-OBBBA) = $1,250,000; federal §179 above that is added back."},
    {"fact_key": "sc_additions_other", "label": "Other SC additions — taxes measured by income, federal NOL, etc. (Sch A&B)", "data_type": "decimal", "required": False, "sort_order": 4},
    {"fact_key": "sc_depreciation_recovery", "label": "SC depreciation recovery — extra SC depreciation over the asset life (Sch A&B subtraction)", "data_type": "decimal", "required": False, "sort_order": 5,
     "notes": "W2. The added-back bonus is recovered via SC depreciation over the remaining recovery life."},
    {"fact_key": "sc_subtractions_other", "label": "Other SC subtractions — US-obligation interest, §163(j) interest, etc. (Sch A&B)", "data_type": "decimal", "required": False, "sort_order": 6},
    {"fact_key": "sc_nol_carryover", "label": "SC net operating loss carryover (SC1120 L5; no carryback)", "data_type": "decimal", "required": False, "sort_order": 7},
    {"fact_key": "is_multistate", "label": "Multistate corporation (apportion)? — if no, SC ratio = 100%", "data_type": "boolean", "required": False, "sort_order": 8},
    {"fact_key": "sales_sc", "label": "Sales/gross receipts within SC (Sch H-1/H-2 numerator)", "data_type": "decimal", "required": False, "sort_order": 9},
    {"fact_key": "sales_everywhere", "label": "Sales/gross receipts everywhere (Sch H-1/H-2 denominator)", "data_type": "decimal", "required": False, "sort_order": 10},
    {"fact_key": "capital_and_surplus", "label": "Total capital stock and paid-in surplus (SC1120 Part II L20, license-fee base)", "data_type": "decimal", "required": False, "sort_order": 11},
]

F_RULES: list[dict] = [
    {"rule_id": "R-SC1120-ADD", "title": "SC additions — §168(k) bonus + §179 excess (Sch A&B)", "rule_type": "calculation",
     "formula": "additions = federal_bonus_depreciation + max(0, federal_section_179 - 1250000) + sc_additions_other",
     "inputs": ["federal_bonus_depreciation", "federal_section_179", "sc_additions_other"], "outputs": ["additions"], "sort_order": 1,
     "description": "W2. SC decouples §168(k): federal bonus added back in the placed-in-service year. Federal §179 above the SC pre-OBBBA limit ($1,250,000) added back. Plus other Schedule A&B additions."},
    {"rule_id": "R-SC1120-SUB", "title": "SC subtractions — SC depreciation recovery (Sch A&B)", "rule_type": "calculation",
     "formula": "subtractions = sc_depreciation_recovery + sc_subtractions_other",
     "inputs": ["sc_depreciation_recovery", "sc_subtractions_other"], "outputs": ["subtractions"], "sort_order": 2,
     "description": "W2. The added-back bonus is recovered via extra SC depreciation over the asset's remaining life. Plus other subtractions (US-obligation interest, §163(j) interest SC does not limit)."},
    {"rule_id": "R-SC1120-APPORT", "title": "Single-factor apportionment (Sch H-1/H-2)", "rule_type": "calculation",
     "formula": "sc_ratio = 1.0 if not is_multistate else (sales_sc / sales_everywhere)",
     "inputs": ["is_multistate", "sales_sc", "sales_everywhere"], "outputs": ["sc_ratio"], "sort_order": 3,
     "description": "W1. §12-6-2252 single sales factor (TPP) / §12-6-2290 gross-receipts (service). Decimal precision not specified by SCDOR — not asserted."},
    {"rule_id": "R-SC1120-INCOME", "title": "SC income tax — 5% (SC1120 L7)", "rule_type": "calculation",
     "formula": ("balance = federal_taxable_income + additions - subtractions ; apportioned = balance * sc_ratio ; "
                 "sc_taxable = apportioned - min(sc_nol_carryover, max(0, apportioned)) ; income_tax = max(0, sc_taxable) * 0.05"),
     "inputs": ["federal_taxable_income", "sc_nol_carryover"], "outputs": ["sc_taxable_income", "income_tax"], "sort_order": 4,
     "description": "W1. §12-6-530. Federal TI + SC additions - SC subtractions, apportioned by the single factor, less SC NOL (federal carryforward period, no carryback), times 5%."},
    {"rule_id": "R-SC1120-LICENSE", "title": "SC license fee (Part II L21)", "rule_type": "calculation",
     "formula": "license_fee = max(25, capital_and_surplus * 0.001 + 15)",
     "inputs": ["capital_and_surplus"], "outputs": ["license_fee"], "sort_order": 5,
     "description": "W1. §12-20-50. $15 + $1 per $1,000 of capital stock and paid-in surplus, minimum $25 per taxpayer (the $25 minimum is not apportioned). Same mechanic as SC1120S."},
    {"rule_id": "R-SC1120-TOTAL", "title": "Total tax — income tax + license fee (SC1120 L30)", "rule_type": "calculation",
     "formula": "total_tax = income_tax + license_fee",
     "inputs": [], "outputs": ["total_tax"], "sort_order": 6,
     "description": "W1. SC1120 grand total (L30) = the 5% income tax (Part I) + the corporate license fee (Part II)."},
]

F_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-SC1120-ADD", "SC_2025_SC1120I", "primary", "§168(k) decouple + §179 pre-OBBBA"),
    ("R-SC1120-ADD", "SC_ACT63_2025_CONFORMITY", "secondary", "§12-6-50 non-adopted list"),
    ("R-SC1120-SUB", "SC_2025_SC1120I", "primary", "SC depreciation recovery over life"),
    ("R-SC1120-APPORT", "SC_CODE_CORP", "primary", "§12-6-2252 single sales factor"),
    ("R-SC1120-INCOME", "SC_2025_SC1120", "primary", "L7 5% tax"),
    ("R-SC1120-INCOME", "SC_CODE_CORP", "secondary", "§12-6-530 5% rate"),
    ("R-SC1120-LICENSE", "SC_2025_SC1120", "primary", "Part II L21 license fee"),
    ("R-SC1120-LICENSE", "SC_CODE_CORP", "secondary", "§12-20-50"),
    ("R-SC1120-TOTAL", "SC_2025_SC1120", "primary", "L30 grand total"),
]

F_LINES: list[dict] = [
    {"line_number": "SC-6", "description": "SC1120 L6 SC net income subject to tax", "line_type": "subtotal", "source_rules": ["R-SC1120-INCOME"], "sort_order": 1},
    {"line_number": "SC-7", "description": "SC1120 L7 Income tax (× 5%)", "line_type": "calculated", "source_rules": ["R-SC1120-INCOME"], "sort_order": 2},
    {"line_number": "SC-H", "description": "Schedule H apportionment ratio", "line_type": "calculated", "source_rules": ["R-SC1120-APPORT"], "sort_order": 3},
    {"line_number": "SC-21", "description": "SC1120 Part II L21 License fee", "line_type": "calculated", "source_rules": ["R-SC1120-LICENSE"], "sort_order": 4},
    {"line_number": "SC-30", "description": "SC1120 L30 Total tax (income + license fee)", "line_type": "calculated", "source_rules": ["R-SC1120-TOTAL"], "sort_order": 5},
]

F_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_SC1120_H3368", "title": "⚠ SC conformity live wire — H.3368 could adopt OBBBA retroactively (TY2025)", "severity": "warning",
     "condition": "federal_bonus_depreciation > 0 or federal_section_179 > 1250000",
     "message": "This spec applies SC's ENACTED conformity (IRC as of 12/31/2024): §168(k) bonus is decoupled and §179 is capped at $1,250,000/$3,130,000 (pre-OBBBA). As of early 2026, H.3368 was pending (not signed) and would adopt full OBBBA conformity RETROACTIVELY for TY2025 — which would remove the bonus add-back and raise §179 to $2.5M/$4M. SCDOR extended the TY2025 SC filing deadline to October 15, 2026 to await it. VERIFY H.3368's final status before relying on the depreciation add-back.",
     "notes": "W3. Live wire — re-verify before seeding SC."},
    {"diagnostic_id": "D_SC1120_BONUS", "title": "SC §168(k) bonus depreciation decouple", "severity": "info",
     "condition": "federal_bonus_depreciation > 0",
     "message": "South Carolina does not recognize IRC §168(k) bonus depreciation. Add back the difference between federal and SC depreciation in the year the property is placed in service; recover the added-back amount via extra SC depreciation over the asset's remaining life (maintain a separate SC depreciation schedule and SC basis).",
     "notes": "W2. §12-6-50."},
    {"diagnostic_id": "D_SC1120_179", "title": "SC §179 limit = $1,250,000 / $3,130,000 (pre-OBBBA)", "severity": "warning",
     "condition": "federal_section_179 > 1250000",
     "message": "South Carolina conforms to §179 at its 12/31/2024 IRC level (pre-OBBBA): $1,250,000 limit / $3,130,000 phaseout for 2025 (SCDOR prints no figure — this is derived from the pre-OBBBA indexed amount). Federal §179 above the SC limit is added back. This flips to $2.5M/$4M if H.3368 adopts OBBBA (see D_SC1120_H3368).",
     "notes": "W2/W3."},
    {"diagnostic_id": "D_SC1120_LICENSE", "title": "SC corporate license fee ($15 + capital×.001, min $25)", "severity": "info",
     "condition": "always (informational)",
     "message": "SC imposes an annual corporate license fee: $15 plus $1 per $1,000 (.001) of capital stock and paid-in surplus, minimum $25 per taxpayer (§12-20-50). The fee is apportioned for multistate corporations, but the $25 minimum is not apportioned. It is added to the income tax on the SC1120 grand total.",
     "notes": "W1."},
    {"diagnostic_id": "D_SC1120_APPORT", "title": "SC single-factor apportionment", "severity": "info",
     "condition": "is_multistate",
     "message": "South Carolina apportions using a single sales factor for taxpayers dealing in tangible personal property (Schedule H-1, §12-6-2252) or a gross-receipts ratio for service businesses (Schedule H-2, §12-6-2290). SCDOR does not print a required decimal precision.",
     "notes": "W1."},
]

F_SCENARIOS: list[dict] = [
    {"scenario_name": "SC1120-A — SC-only corp: 5% income tax", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"federal_taxable_income": 200000, "capital_and_surplus": 500000},
     "expected_outputs": {"sc_taxable_income": 200000, "income_tax": 10000, "license_fee": 515, "total_tax": 10515},
     "notes": "SC-only (ratio 100%): 200,000 x 5% = 10,000 income tax; license fee 500,000×.001 + 15 = 515; total 10,515."},
    {"scenario_name": "SC1120-B — §168(k) bonus add-back", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"federal_taxable_income": 100000, "federal_bonus_depreciation": 80000, "sc_depreciation_recovery": 20000, "capital_and_surplus": 100000},
     "expected_outputs": {"additions": 80000, "subtractions": 20000, "sc_taxable_income": 160000, "income_tax": 8000, "license_fee": 115},
     "notes": "Add back 80,000 bonus, recover 20,000 SC depreciation: 100,000 + 80,000 - 20,000 = 160,000 x 5% = 8,000; license 115."},
    {"scenario_name": "SC1120-C — §179 excess over the pre-OBBBA SC limit", "scenario_type": "edge", "sort_order": 3,
     "inputs": {"federal_taxable_income": 500000, "federal_section_179": 2000000, "capital_and_surplus": 0},
     "expected_outputs": {"additions": 750000, "sc_taxable_income": 1250000, "income_tax": 62500, "license_fee": 25},
     "notes": "Federal §179 2,000,000 - SC limit 1,250,000 = 750,000 add-back. 500,000 + 750,000 = 1,250,000 x 5% = 62,500; license fee minimum $25."},
    {"scenario_name": "SC1120-D — multistate single-factor apportionment", "scenario_type": "edge", "sort_order": 4,
     "inputs": {"federal_taxable_income": 1000000, "is_multistate": True, "sales_sc": 300000, "sales_everywhere": 1000000, "capital_and_surplus": 0},
     "expected_outputs": {"sc_ratio": 0.3, "sc_taxable_income": 300000, "income_tax": 15000},
     "notes": "Ratio 300,000/1,000,000 = 0.30; SC taxable 1,000,000 x 0.30 = 300,000 x 5% = 15,000."},
    {"scenario_name": "SC1120-E — license fee minimum ($25)", "scenario_type": "edge", "sort_order": 5,
     "inputs": {"capital_and_surplus": 5000},
     "expected_outputs": {"license_fee": 25},
     "notes": "5,000×.001 + 15 = 20 -> below the $25 minimum -> $25."},
    {"scenario_name": "SC1120-F — SC NOL reduces SC taxable income", "scenario_type": "edge", "sort_order": 6,
     "inputs": {"federal_taxable_income": 300000, "sc_nol_carryover": 100000, "capital_and_surplus": 0},
     "expected_outputs": {"sc_taxable_income": 200000, "income_tax": 10000},
     "notes": "SC NOL 100,000 (federal carryforward period, no carryback) reduces 300,000 to 200,000 x 5% = 10,000."},
]


FORMS: list[dict] = [
    {
        "identity": {"form_number": "SC1120", "form_title": "South Carolina SC1120 — 'C' Corporation Income Tax Return (TY2025)",
                     "notes": "WO-12 (form 1 of 3, DECISIONS D-14). SC C-corp: 5% income tax (federal-TI + §168(k) bonus decouple add-back + §179 excess over the pre-OBBBA $1.25M/$3.13M limit -> single-factor apportionment -> SC NOL -> 5%, §12-6-530) + the §12-20-50 license fee ($15 + capital×.001, min $25); total = income + license fee (L30). Reuses the SC1120S structure. ⚠ H.3368/OBBBA live wire: authored to 12/31/2024 law + D_SC1120_H3368 flag — RE-VERIFY H.3368 before seeding SC (SCDOR extended the SC deadline to Oct 15 2026)."},
        "facts": F_FACTS, "rules": F_RULES, "rule_links": F_RULE_LINKS,
        "lines": F_LINES, "diagnostics": F_DIAGNOSTICS, "scenarios": F_SCENARIOS,
    },
]

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-SC1120-INCOME", "title": "SC income tax = 5% of apportioned SC taxable income", "assertion_type": "reconciliation",
     "entity_types": ["1120"], "status": "draft", "sort_order": 1,
     "description": "Federal TI + SC additions − SC subtractions, apportioned by the single factor, less SC NOL, times 5%.",
     "definition": {"rule": "R-SC1120-INCOME", "check": "income_tax = max(0, ((fed_ti + add - sub) * ratio - nol)) * 0.05"}},
    {"assertion_id": "FA-SC1120-LICENSE", "title": "SC license fee = capital×.001 + $15 (min $25)", "assertion_type": "reconciliation",
     "entity_types": ["1120"], "status": "draft", "sort_order": 2,
     "description": "The corporate license fee = $15 + $1 per $1,000 of capital and paid-in surplus, minimum $25.",
     "definition": {"rule": "R-SC1120-LICENSE", "check": "license_fee = max(25, capital*0.001 + 15)"}},
    {"assertion_id": "FA-SC1120-TOTAL", "title": "SC total = income tax + license fee", "assertion_type": "reconciliation",
     "entity_types": ["1120"], "status": "draft", "sort_order": 3,
     "description": "SC1120 grand total (L30) = the 5% income tax plus the corporate license fee.",
     "definition": {"rule": "R-SC1120-TOTAL", "check": "total_tax = income_tax + license_fee"}},
]


class Command(BaseCommand):
    help = "Load the SC1120 spec (SC C-corp income tax + license fee, TY2025). Refuses to seed until READY_TO_SEED=True (W1-W3 + re-verify H.3368)."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad SC1120 spec (SC C Corporation Income Tax Return)\n"))
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
                "\nREFUSING TO SEED SC1120: not cleared to seed.\n\n"
                "Gated until Ken reviews (W1 5% + license fee; W2 §168(k) decouple + §179 $1.25M;\n"
                "W3 the H.3368 live wire) AND re-verifies H.3368's status, then flips the sentinel.\n\n"
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
        self.stdout.write("SC1120 loaded.")
        self.stdout.write(f"  SC1120: facts {len(F_FACTS)} / rules {len(F_RULES)} / lines {len(F_LINES)} / diag {len(F_DIAGNOSTICS)} / tests {len(F_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}")
        self.stdout.write("=" * 60)
