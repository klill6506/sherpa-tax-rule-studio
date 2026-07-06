"""Load the Form 8990 spec — Limitation on Business Interest Expense Under §163(j) (Rev. 12-2025).
WO-14, first of the SPINE S-16 federal-forms queue. Finishes the 1120 module's biggest deferred leg
(the §163(j) gate on Schedule K Q24 routed here); also serves 1065/1120-S/1040.

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
Form 8990 limits the business interest expense deduction to business interest income + 30% of
adjusted taxable income (ATI) + floor plan financing interest (§163(j)(1)). The compute heart is ATI:
OBBBA restored the EBITDA basis for TY2025 — line 11 adds back depreciation, amortization, and
depletion (suspended 2022-2024, reinstated for years after 12/31/2024). Disallowed interest carries
forward indefinitely (§163(j)(2)). Filed by C-corps, partnerships, S-corps, and individuals with
business interest expense, UNLESS the §448(c) small-business exemption applies (avg gross receipts
<= $31M) or the business is an excepted trade/business (§163(j)(7)).

Greenfield: `8990` not in the 92-form federal prod set at the 2026-07-05 gap-check.

═══════════════════════════════════════════════════════════════════════════
v1 SCOPE — LOCKED (Ken's Gate-1 walk 2026-07-05; DECISIONS D-16). See f8990_source_brief.md.
═══════════════════════════════════════════════════════════════════════════
COMPUTES: (Q1) Part I — total BIE (L5); ATI (L22, incl. the L11 EBITDA add-back); 30% limitation (L26);
total limitation (L29 = 30% ATI + BII + floor plan); allowable BIE (L30 = min); disallowed carryforward
(L31, indefinite). (Q2) Part II/III — partnership EBIE (L32) / ETI (L36) / excess BII (L37); S-corp ETI
(L41) / excess BII (L42, no EBIE); Schedule A/B per-owner detail = direct-entry. (Q3) $31M §448(c)
exemption gate + §163(j)(7) excepted-business diagnostic.

requires_human_review WALK ITEMS (W1-W3):
W1. ATI = tentative taxable income + additions (incl. L11 EBITDA add-back — dep/amort/depletion, an
    ADDITION for TY2025 per OBBBA/i8990 "What's New") − reductions. CONFIRM the L11 add-back is live for 2025.
W2. Limitation = business interest income + 30% × ATI + floor plan; allowable = min(total BIE, limit);
    disallowed carries forward INDEFINITELY (§163(j)(2)). CONFIRM the 30% + carryforward.
W3. $31M §448(c) small-business exemption (non-tax-shelter → not required to file); §163(j)(7) excepted
    businesses (electing real-property/farming, utilities, employee services) elect out. CONFIRM.

CARRIED [UNVERIFIED]: OBBBA effective date cited to P.L. 119-21 + i8990 (Cornell §163(j)(8) lags the amendment
dating). TY2026 electively-capitalized-interest character change (years after 12/31/2025) NOT encoded. Re-verify $31M index.

SAFETY GUARD — READY_TO_SEED stays False until Ken approves the review walk (W1-W3).
FLIPPED 2026-07-05 — Ken APPROVED ("Approve — flip, seed, export"): W1 the ATI EBITDA-basis
L11 add-back, W2 the 30% limit + indefinite carryforward, W3 the $31M exemption + §163(j)(7)
excepted businesses. Validated (scratchpad/validate_8990.py, 19/0).
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
FORM_ENTITY_TYPES = ["1120", "1065", "1120S", "1040"]

# Verified constants (f8990_source_brief.md; Form 8990 Rev. 12-2025 / i8990 / §163(j))
LIMIT_PCT = "0.30"                 # §163(j)(1)(B) — 30% of ATI (i8990 L26 "applicable percentage is 30%")
EXEMPT_GROSS_RECEIPTS = 31000000   # §448(c) 2025 small-business exemption (avg annual gross receipts)


def _total_bie(current, carryforward, partner_excess, floor_plan) -> float:
    """Form 8990 Line 5 = total business interest expense."""
    return float(current) + float(carryforward) + float(partner_excess) + float(floor_plan)


def _ati(tentative_ti, additions, reductions) -> float:
    """Line 22 ATI = tentative taxable income + additions (incl. L11 EBITDA add-back) − reductions."""
    return float(tentative_ti) + float(additions) - float(reductions)


def _limitation(bii_total, ati, floor_plan) -> float:
    """Line 29 = business interest income + 30% of ATI + floor plan financing interest."""
    return float(bii_total) + float(LIMIT_PCT) * float(ati) + float(floor_plan)


def _eti(total_bie, bii_total, floor_plan, ati) -> float:
    """Line 36/41 excess taxable income = (L34/L26) × ATI (partnership/S-corp pass-through)."""
    l26 = float(LIMIT_PCT) * float(ati)
    if l26 <= 0:
        return 0.0
    l33 = max(0.0, float(total_bie) - (float(floor_plan) + float(bii_total)))
    l34 = max(0.0, l26 - l33)
    return (l34 / l26) * float(ati)


AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("sec163j_limitation", "Form 8990 §163(j) business-interest limitation: ATI on the OBBBA EBITDA basis "
     "(L11 dep/amort/depletion add-back), 30% ATI + BII + floor-plan limitation, partnership EBIE/ETI + "
     "S-corp ETI pass-through, $31M §448(c) exemption."),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_F8990", "source_type": "federal_form", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Form 8990 (Rev. 12-2025) — Limitation on Business Interest Expense Under Section 163(j)",
        "citation": "Form 8990 (Rev. December 2025), Created 9/9/25", "issuer": "Internal Revenue Service",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f8990.pdf",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.6, "topics": ["sec163j_limitation"],
        "excerpts": [{
            "excerpt_label": "Part I line map — ATI (L11 EBITDA add-back) + 30% limitation (Rev. 12-2025 verbatim)",
            "excerpt_text": (
                "Section I Business Interest Expense: L1 current year business interest expense (excl. floor "
                "plan); L2 disallowed BIE carryforwards from prior years (not a partnership); L3 partner's "
                "excess BIE treated as paid (Sch A); L4 floor plan financing interest; L5 total BIE (add 1-4). "
                "Section II Adjusted Taxable Income: L6 tentative taxable income; additions L7-16 including L9 "
                "§172 NOL, L10 §199A QBI, and L11 'Deduction allowable for depreciation, amortization, or "
                "depletion attributable to a trade or business' (an ADDITION); reductions L17-20 (bracketed); "
                "L21 total reductions; L22 adjusted taxable income = combine L6, L16, L21. Section III Business "
                "Interest Income: L23 current BII; L24 pass-through excess BII; L25 total. Section IV: L26 = 30% "
                "of ATI ('The applicable percentage is 30%'); L27 BII (L25); L28 floor plan (L4); L29 total "
                "(add 26-28); L30 allowable BIE deduction; L31 disallowed BIE = L5 − L29 (if <=0, enter 0)."
            ),
            "summary_text": "8990 Part I: L5 total BIE; L22 ATI (L11 dep/amort/depletion add-back); L26 30% ATI; L29 limit = 30%ATI+BII+floorplan; L30 allowable = min; L31 disallowed carryforward.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "Part II/III pass-through + What's New EBITDA (Rev. 12-2025 verbatim)",
            "excerpt_text": (
                "Part II Partnership Pass-Through Items: L32 excess business interest expense (= L31 EBIE); L33 = "
                "L5 − (L4+L25); L34 = L26 − L33; L35 = L34 ÷ L26 (decimal); L36 excess taxable income = L35 × "
                "L22; L37 excess business interest income = L25 − (L1+L2+L3). Part III S Corporation Pass-Through "
                "Items: L38 = L5 − (L4+L25); L39 = L26 − L38; L40 = L39 ÷ L26; L41 excess taxable income = L40 × "
                "L22; L42 excess business interest income = L25 − (L1+L2+L3). (No EBIE at the S-corp level.) "
                "What's New (i8990): 'P.L. 119-21 (OBBBA) amended section 163(j) to allow an add-back to taxable "
                "income for any deduction allowable for depreciation, amortization, or depletion to determine "
                "ATI for tax years beginning after 2024. Form 8990, line 11 has been revised to reinstate' it. "
                "Small-business exemption: average annual gross receipts of $31 million or less (§448(c), "
                "non-tax-shelter) — not required to file."
            ),
            "summary_text": "Part II partnership EBIE(L32)/ETI(L36)/excess-BII(L37); Part III S-corp ETI(L41)/excess-BII(L42). OBBBA reinstated L11 EBITDA add-back for TY2025. $31M §448(c) exemption.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "IRS_2025_I8990", "source_type": "official_instructions", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Instructions for Form 8990 (Rev. 12-2025)",
        "citation": "Instructions for Form 8990 (Rev. December 2025), dated 21-Jan-2026", "issuer": "Internal Revenue Service",
        "official_url": "https://www.irs.gov/instructions/i8990",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.5, "topics": ["sec163j_limitation"],
        "excerpts": [{
            "excerpt_label": "Who must file + exemption + line 11 (i8990 verbatim)",
            "excerpt_text": (
                "'A taxpayer (including, for example, an individual, corporation, partnership, S corporation) "
                "with business interest expense; a disallowed business interest expense carryforward; or current "
                "year or prior year excess business interest expense must generally file Form 8990, unless an "
                "exclusion from filing applies.' Small-business taxpayers (average annual gross receipts of $31 "
                "million or less for the 3 prior years, §448(c), not a tax shelter) are not required to file. "
                "Line 11 (verbatim): 'Enter the amounts allowable for depreciation, amortization, or depletion "
                "attributable to a trade or business.' Excepted trades or businesses (§163(j)(7)) — electing "
                "real property or farming businesses, certain regulated utilities, and the trade or business of "
                "performing services as an employee — are not subject to the limitation."
            ),
            "summary_text": "Who files: any taxpayer with BIE (unless exempt). $31M §448(c) exemption. L11 = dep/amort/depletion add-back. §163(j)(7) excepted businesses elect out.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "IRC_163J", "source_type": "statute", "source_rank": "controlling",
        "jurisdiction_code": "US", "title": "IRC §163(j) — business interest limitation (30% ATI, EBITDA basis, indefinite carryforward)",
        "citation": "26 U.S.C. §163(j)(1),(2),(7),(8); §448(c); P.L. 119-21 (OBBBA)", "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/163",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.4, "topics": ["sec163j_limitation"],
        "excerpts": [{
            "excerpt_label": "§163(j)(1)/(2)/(7)/(8) + OBBBA EBITDA effective date (verbatim substance)",
            "excerpt_text": (
                "§163(j)(1): the business interest deduction is limited to the sum of (A) business interest "
                "income + (B) 30% of adjusted taxable income + (C) floor plan financing interest. §163(j)(2): "
                "any disallowed business interest is 'treated as business interest paid or accrued in the "
                "succeeding taxable year' (indefinite carryforward). §163(j)(8): ATI is taxable income computed "
                "'without regard to ... any deduction allowable for depreciation, amortization, or depletion' "
                "(EBITDA basis) — RESTORED for tax years beginning after Dec. 31, 2024 by P.L. 119-21 (OBBBA); "
                "cite the effective date to OBBBA + i8990 (the Cornell/OLRC text has not yet ingested the "
                "amendment dating). §163(j)(7): excepted trades/businesses — employee services, electing real "
                "property trade or business, electing farming business, certain regulated utilities. §448(c): "
                "the small-business gross-receipts exemption ($31M for 2025)."
            ),
            "summary_text": "§163(j)(1) 30% ATI + BII + floor plan; (2) indefinite carryforward; (8) EBITDA ATI (OBBBA, post-2024); (7) excepted businesses; §448(c) $31M.",
            "is_key_excerpt": True,
        }],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_F8990", "8990", "governs"), ("IRS_2025_I8990", "8990", "governs"), ("IRC_163J", "8990", "governs"),
]


F8990_FACTS: list[dict] = [
    # Section I — business interest expense
    {"fact_key": "current_bie", "label": "Current-year business interest expense, before the §163(j) limit (L1)", "data_type": "decimal", "required": False, "sort_order": 1},
    {"fact_key": "disallowed_bie_carryforward", "label": "Disallowed BIE carryforward from prior years (L2; N/A to a partnership)", "data_type": "decimal", "required": False, "sort_order": 2},
    {"fact_key": "partner_excess_bie", "label": "Partner's excess BIE treated as paid this year — Schedule A (L3)", "data_type": "decimal", "required": False, "sort_order": 3},
    {"fact_key": "floor_plan_interest", "label": "Floor plan financing interest expense (L4)", "data_type": "decimal", "required": False, "sort_order": 4},
    # Section II — ATI
    {"fact_key": "tentative_taxable_income", "label": "Tentative taxable income (L6)", "data_type": "decimal", "required": False, "sort_order": 5},
    {"fact_key": "dep_amort_depletion", "label": "Depreciation/amortization/depletion allowable to a trade or business — EBITDA add-back (L11)", "data_type": "decimal", "required": False, "sort_order": 6,
     "notes": "W1. OBBBA restored this ADDITION for TY2025 (§163(j)(8); was suspended 2022-2024). The load-bearing ATI item."},
    {"fact_key": "nol_199a_additions", "label": "§172 NOL deduction (L9) + §199A QBI deduction (L10) — ATI add-backs", "data_type": "decimal", "required": False, "sort_order": 7,
     "notes": "Added back because ATI is computed without the NOL/§199A deductions."},
    {"fact_key": "ati_additions_other", "label": "Other ATI additions — non-ATB loss/deduction, non-PTE BIE, pass-through loss, other + partner/S-corp ETI (L7/L8/L12-15)", "data_type": "decimal", "required": False, "sort_order": 8},
    {"fact_key": "ati_reductions", "label": "ATI reductions — non-ATB income/gain, non-PTE BII, pass-through income, other (L17-20, subtracted)", "data_type": "decimal", "required": False, "sort_order": 9},
    # Section III — business interest income
    {"fact_key": "current_bii", "label": "Current-year business interest income (L23)", "data_type": "decimal", "required": False, "sort_order": 10},
    {"fact_key": "passthrough_excess_bii", "label": "Excess business interest income from pass-through entities — Sch A/B (L24)", "data_type": "decimal", "required": False, "sort_order": 11},
    # Exemption / excepted gating
    {"fact_key": "avg_gross_receipts_3yr", "label": "Average annual gross receipts, prior 3 years (§448(c) exemption test)", "data_type": "decimal", "required": False, "sort_order": 12},
    {"fact_key": "is_tax_shelter", "label": "Tax shelter (§448(d)(3))? — disqualifies the small-business exemption", "data_type": "boolean", "required": False, "sort_order": 13},
    {"fact_key": "is_excepted_business", "label": "Excepted trade/business (§163(j)(7)) — electing real-property/farming, utility, employee services?", "data_type": "boolean", "required": False, "sort_order": 14},
    {"fact_key": "filer_entity_type", "label": "Filer type (drives Part II partnership vs Part III S-corp pass-through)", "data_type": "choice", "required": False, "sort_order": 15,
     "choices": ["1120", "1065", "1120S", "1040"]},
]

F8990_RULES: list[dict] = [
    {"rule_id": "R-8990-BIE", "title": "Total business interest expense (L5)", "rule_type": "calculation",
     "formula": "total_bie = current_bie + disallowed_bie_carryforward + partner_excess_bie + floor_plan_interest",
     "inputs": ["current_bie", "disallowed_bie_carryforward", "partner_excess_bie", "floor_plan_interest"], "outputs": ["total_bie"], "sort_order": 1,
     "description": "Form 8990 Section I: L5 total business interest expense = L1 current + L2 prior-year carryforward + L3 partner excess + L4 floor plan."},
    {"rule_id": "R-8990-ATI", "title": "Adjusted taxable income — EBITDA basis (L22)", "rule_type": "calculation",
     "formula": "ati = tentative_taxable_income + (dep_amort_depletion + nol_199a_additions + ati_additions_other) - ati_reductions",
     "inputs": ["tentative_taxable_income", "dep_amort_depletion", "nol_199a_additions", "ati_additions_other", "ati_reductions"], "outputs": ["ati"], "sort_order": 2,
     "description": "W1. Section II: ATI (L22) = tentative taxable income (L6) + additions (L7-16, incl. the L11 dep/amort/depletion add-back restored by OBBBA for TY2025, plus §172 NOL / §199A) − reductions (L17-20). EBITDA basis."},
    {"rule_id": "R-8990-LIMIT", "title": "§163(j) limitation — 30% ATI + BII + floor plan (L29)", "rule_type": "calculation",
     "formula": "bii_total = current_bii + passthrough_excess_bii ; limitation = 0.30 * ati + bii_total + floor_plan_interest",
     "inputs": ["current_bii", "passthrough_excess_bii"], "outputs": ["bii_total", "limitation"], "sort_order": 3,
     "description": "W2. Section IV: L26 = 30% × ATI; L29 total limitation = 30% ATI + business interest income (L25) + floor plan financing (L4)."},
    {"rule_id": "R-8990-ALLOW", "title": "Allowable BIE + disallowed carryforward (L30/L31)", "rule_type": "calculation",
     "formula": "allowable_bie = min(total_bie, limitation) ; disallowed_carryforward = max(0, total_bie - limitation)",
     "inputs": [], "outputs": ["allowable_bie", "disallowed_carryforward"], "sort_order": 4,
     "description": "W2. L30 allowable business interest expense deduction = min(total BIE, limitation). L31 disallowed BIE = L5 − L29 (if ≤0, enter 0) — carries forward INDEFINITELY (§163(j)(2))."},
    {"rule_id": "R-8990-PTE", "title": "Pass-through items — partnership EBIE/ETI, S-corp ETI (Part II/III)", "rule_type": "calculation",
     "formula": ("l26 = 0.30 * ati ; l33 = max(0, total_bie - (floor_plan_interest + bii_total)) ; excess_taxable_income = ((max(0, l26 - l33)) / l26) * ati if l26 > 0 else 0 ; "
                 "excess_bii = max(0, bii_total - (current_bie + disallowed_bie_carryforward + partner_excess_bie)) ; "
                 "partnership: ebie = disallowed_carryforward (L32) ; S-corp: no EBIE"),
     "inputs": ["filer_entity_type"], "outputs": ["excess_taxable_income", "excess_bii", "ebie"], "sort_order": 5,
     "description": "Part II (partnership, L32-37): EBIE (L32=L31), ETI (L36 = (L34/L26)×ATI), excess BII (L37). Part III (S-corp, L38-42): ETI (L41), excess BII (L42) — NO EBIE at the S-corp level. These pass to partners/shareholders for their own §163(j) calc; per-owner Schedule A/B detail = direct-entry."},
    {"rule_id": "R-8990-EXEMPT", "title": "§448(c) small-business exemption gate ($31M)", "rule_type": "routing",
     "formula": "if avg_gross_receipts_3yr <= 31000000 and not is_tax_shelter and not is_excepted_business: NOT required to file 8990 (no limitation) ; excepted business (§163(j)(7)) also not subject",
     "inputs": ["avg_gross_receipts_3yr", "is_tax_shelter", "is_excepted_business"], "outputs": ["exempt_from_filing"], "sort_order": 6,
     "description": "W3. A small-business taxpayer (avg annual gross receipts ≤ $31M for the prior 3 years, §448(c), non-tax-shelter) is NOT required to file Form 8990 — the limitation does not apply. §163(j)(7) excepted trades/businesses (electing real-property/farming, utilities, employee services) also elect out."},
]

F8990_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-8990-BIE", "IRS_2025_F8990", "primary", "Section I L1-5"),
    ("R-8990-ATI", "IRS_2025_F8990", "primary", "Section II L6-22 (L11 EBITDA add-back)"),
    ("R-8990-ATI", "IRC_163J", "secondary", "§163(j)(8) EBITDA basis (OBBBA)"),
    ("R-8990-LIMIT", "IRC_163J", "primary", "§163(j)(1) 30% ATI + BII + floor plan"),
    ("R-8990-LIMIT", "IRS_2025_F8990", "secondary", "Section IV L26-29"),
    ("R-8990-ALLOW", "IRS_2025_F8990", "primary", "L30 allowable / L31 disallowed"),
    ("R-8990-ALLOW", "IRC_163J", "secondary", "§163(j)(2) indefinite carryforward"),
    ("R-8990-PTE", "IRS_2025_F8990", "primary", "Part II/III pass-through items"),
    ("R-8990-EXEMPT", "IRS_2025_I8990", "primary", "$31M §448(c) exemption / §163(j)(7) excepted"),
    ("R-8990-EXEMPT", "IRC_163J", "secondary", "§163(j)(7) excepted trades/businesses"),
]

F8990_LINES: list[dict] = [
    {"line_number": "L5", "description": "Total business interest expense", "line_type": "subtotal", "source_rules": ["R-8990-BIE"], "sort_order": 1},
    {"line_number": "L11", "description": "Depreciation/amortization/depletion add-back (EBITDA basis)", "line_type": "input", "source_facts": ["dep_amort_depletion"], "sort_order": 2},
    {"line_number": "L22", "description": "Adjusted taxable income (ATI)", "line_type": "subtotal", "source_rules": ["R-8990-ATI"], "sort_order": 3},
    {"line_number": "L26", "description": "30% of ATI", "line_type": "calculated", "source_rules": ["R-8990-LIMIT"], "sort_order": 4},
    {"line_number": "L29", "description": "Total §163(j) limitation (30% ATI + BII + floor plan)", "line_type": "calculated", "source_rules": ["R-8990-LIMIT"], "sort_order": 5},
    {"line_number": "L30", "description": "Allowable business interest expense deduction", "line_type": "calculated", "source_rules": ["R-8990-ALLOW"], "sort_order": 6},
    {"line_number": "L31", "description": "Disallowed BIE carryforward (indefinite)", "line_type": "calculated", "source_rules": ["R-8990-ALLOW"], "sort_order": 7},
    {"line_number": "L36", "description": "Excess taxable income (Part II/III pass-through)", "line_type": "calculated", "source_rules": ["R-8990-PTE"], "sort_order": 8},
]

F8990_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_8990_EBITDA", "title": "OBBBA restored the EBITDA add-back (line 11) for TY2025", "severity": "info",
     "condition": "dep_amort_depletion > 0",
     "message": "For tax years beginning after 2024, OBBBA (P.L. 119-21) restored the EBITDA basis for adjusted taxable income: Form 8990 line 11 adds back the depreciation, amortization, and depletion attributable to a trade or business. This was suspended for 2022-2024 (EBIT basis) and increases the 30%-of-ATI interest-deduction headroom. Enter the full dep/amort/depletion on line 11.",
     "notes": "W1."},
    {"diagnostic_id": "D_8990_DISALLOW", "title": "Disallowed business interest carries forward indefinitely", "severity": "info",
     "condition": "disallowed_carryforward > 0",
     "message": "Business interest expense disallowed under §163(j) (line 31) is not lost — it is treated as business interest paid or accrued in the following year and carries forward indefinitely (§163(j)(2)). Track the carryforward to next year's line 2.",
     "notes": "W2."},
    {"diagnostic_id": "D_8990_EXEMPT", "title": "Small-business taxpayer — not required to file (≤ $31M)", "severity": "info",
     "condition": "avg_gross_receipts_3yr <= 31000000 and not is_tax_shelter",
     "message": "A taxpayer with average annual gross receipts of $31,000,000 or less over the prior 3 years (§448(c)) and that is not a tax shelter is a small-business taxpayer — the §163(j) limitation does not apply and Form 8990 is not required. Business interest is fully deductible.",
     "notes": "W3."},
    {"diagnostic_id": "D_8990_EXCEPTED", "title": "§163(j)(7) excepted trade or business — elects out", "severity": "info",
     "condition": "is_excepted_business",
     "message": "An excepted trade or business is not subject to the §163(j) limitation: an electing real property trade or business, an electing farming business, certain regulated utilities, and the trade or business of performing services as an employee (§163(j)(7)). Interest allocable to an excepted business is not limited; allocate interest between excepted and non-excepted activities.",
     "notes": "W3."},
    {"diagnostic_id": "D_8990_EBIE", "title": "Partnership excess business interest expense passes to partners", "severity": "info",
     "condition": "filer_entity_type == 1065 and disallowed_carryforward > 0",
     "message": "A partnership's disallowed business interest is excess business interest expense (EBIE, line 32) that passes through to the partners on Schedule K-1 — the partnership does not carry it forward itself. A partner deducts EBIE only against future excess taxable income / excess business interest income from the same partnership (§163(j)(4)).",
     "notes": "Part II. Per-partner Schedule A allocation = direct-entry."},
]

F8990_SCENARIOS: list[dict] = [
    {"scenario_name": "8990-A — BIE limited (EBITDA add-back gives headroom)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tentative_taxable_income": 1000000, "dep_amort_depletion": 300000, "current_bie": 500000, "current_bii": 20000},
     "expected_outputs": {"total_bie": 500000, "ati": 1300000, "limitation": 410000, "allowable_bie": 410000, "disallowed_carryforward": 90000},
     "notes": "ATI = 1,000,000 + 300,000 EBITDA add-back = 1,300,000; limit = 30%×1.3M + 20,000 BII = 410,000; allowable 410,000; 90,000 disallowed carries forward. (On the old EBIT basis ATI would be 1M, limit 320k, disallowed 180k — the add-back saves 90,000.)"},
    {"scenario_name": "8990-B — fully allowable (BIE under the limit)", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"tentative_taxable_income": 1000000, "dep_amort_depletion": 300000, "current_bie": 200000, "current_bii": 20000},
     "expected_outputs": {"ati": 1300000, "limitation": 410000, "allowable_bie": 200000, "disallowed_carryforward": 0},
     "notes": "Total BIE 200,000 < limit 410,000 -> fully deductible; no carryforward."},
    {"scenario_name": "8990-C — small-business exemption ($31M)", "scenario_type": "edge", "sort_order": 3,
     "inputs": {"avg_gross_receipts_3yr": 20000000, "current_bie": 500000},
     "expected_outputs": {"exempt_from_filing": True, "diagnostic": "D_8990_EXEMPT"},
     "notes": "Avg gross receipts 20M ≤ 31M and not a tax shelter -> not required to file 8990; interest fully deductible."},
    {"scenario_name": "8990-D — partnership excess taxable income (ETI)", "scenario_type": "edge", "sort_order": 4,
     "inputs": {"filer_entity_type": "1065", "tentative_taxable_income": 900000, "dep_amort_depletion": 100000, "current_bie": 60000},
     "expected_outputs": {"ati": 1000000, "excess_taxable_income": 800000},
     "notes": "ATI 1,000,000; L26 300,000; L33 = 60,000 − 0 = 60,000; L34 = 240,000; L35 = 0.8; ETI = 0.8 × 1,000,000 = 800,000 passes to partners."},
    {"scenario_name": "8990-E — partnership EBIE passes to partners", "scenario_type": "edge", "sort_order": 5,
     "inputs": {"filer_entity_type": "1065", "tentative_taxable_income": 100000, "current_bie": 50000},
     "expected_outputs": {"ati": 100000, "limitation": 30000, "disallowed_carryforward": 20000, "diagnostic": "D_8990_EBIE"},
     "notes": "ATI 100,000; limit 30% = 30,000; BIE 50,000 > 30,000 -> 20,000 EBIE (L32) passes to partners on K-1 (partnership does not carry it forward)."},
    {"scenario_name": "8990-F — excepted real property business elects out", "scenario_type": "failure", "sort_order": 6,
     "inputs": {"is_excepted_business": True, "current_bie": 400000},
     "expected_outputs": {"exempt_from_filing": True, "diagnostic": "D_8990_EXCEPTED"},
     "notes": "An electing real property trade or business (§163(j)(7)) is not subject to the limitation; interest allocable to it is not limited."},
]

FORMS: list[dict] = [
    {
        "identity": {"form_number": "8990", "form_title": "Form 8990 — Limitation on Business Interest Expense Under §163(j) (Rev. 12-2025)",
                     "notes": "WO-14 (SPINE S-16 first; DECISIONS D-16). Finishes the 1120 module's §163(j) deferred leg; also 1065/1120-S/1040. Part I: total BIE (L5) -> ATI (L22, incl. the L11 EBITDA add-back — dep/amort/depletion, restored by OBBBA for TY2025) -> 30% limitation (L26) -> total limit (L29 = 30% ATI + BII + floor plan) -> allowable BIE (L30 = min) -> disallowed carryforward (L31, indefinite). Part II partnership EBIE(L32)/ETI(L36)/excess-BII(L37); Part III S-corp ETI(L41)/excess-BII(L42, no EBIE); Sch A/B per-owner = direct-entry. $31M §448(c) exemption gate + §163(j)(7) excepted-business diagnostic. Cite OBBBA effective date to P.L. 119-21 + i8990."},
        "facts": F8990_FACTS, "rules": F8990_RULES, "rule_links": F8990_RULE_LINKS,
        "lines": F8990_LINES, "diagnostics": F8990_DIAGNOSTICS, "scenarios": F8990_SCENARIOS,
    },
]

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-8990-LIMIT", "title": "§163(j) limit = 30% ATI + BII + floor plan; allowable = min", "assertion_type": "reconciliation",
     "entity_types": ["1120", "1065", "1120S", "1040"], "status": "draft", "sort_order": 1,
     "description": "Allowable business interest = min(total BIE, 30% × ATI + business interest income + floor plan financing).",
     "definition": {"rule": "R-8990-ALLOW", "check": "allowable_bie = min(total_bie, 0.30*ati + bii_total + floor_plan)"}},
    {"assertion_id": "FA-8990-ATI", "title": "ATI is EBITDA-basis (line 11 dep/amort/depletion added back) for TY2025", "assertion_type": "reconciliation",
     "entity_types": ["1120", "1065", "1120S", "1040"], "status": "draft", "sort_order": 2,
     "description": "ATI = tentative taxable income + additions incl. the line-11 depreciation/amortization/depletion add-back (OBBBA, post-2024) − reductions.",
     "definition": {"rule": "R-8990-ATI", "check": "ati includes + dep_amort_depletion (L11)"}},
    {"assertion_id": "FA-8990-CF", "title": "Disallowed BIE carries forward indefinitely", "assertion_type": "reconciliation",
     "entity_types": ["1120", "1065", "1120S", "1040"], "status": "draft", "sort_order": 3,
     "description": "Disallowed business interest (L31 = total BIE − limitation, floored at 0) carries forward indefinitely (§163(j)(2)).",
     "definition": {"rule": "R-8990-ALLOW", "check": "disallowed_carryforward = max(0, total_bie - limitation)"}},
]


class Command(BaseCommand):
    help = "Load the Form 8990 spec (§163(j) business-interest limitation, Rev. 12-2025). Refuses to seed until READY_TO_SEED=True (W1-W3)."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad Form 8990 spec (§163(j) business-interest limitation)\n"))
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
                "\nREFUSING TO SEED FORM 8990: not cleared.\n\n"
                "Gated until Ken reviews (W1 ATI EBITDA L11 add-back; W2 30% limit + indefinite\n"
                f"carryforward; W3 $31M exemption + excepted businesses) and flips the sentinel.\n\nREADY_TO_SEED = {READY_TO_SEED}\n\nEmpty:\n  {still}\n"
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
        self.stdout.write("Form 8990 loaded.")
        self.stdout.write(f"  8990: facts {len(F8990_FACTS)} / rules {len(F8990_RULES)} / lines {len(F8990_LINES)} / diag {len(F8990_DIAGNOSTICS)} / tests {len(F8990_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}")
        self.stdout.write("=" * 60)
