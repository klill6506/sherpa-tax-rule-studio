"""Load the FORM_8960 spec — Net Investment Income Tax (§1411).

Phase 2, fifth common form. The 3.8% NIIT on the lesser of net investment income or
the MAGI excess over a statutory threshold → Schedule 2 line 12 → 1040 line 23. A
per-RETURN tax (joint MAGI), so return-level facts (no sub-model).

KEN'S 2 SCOPE DECISIONS (2026-06-15, AskUserQuestion):
  (1) auto-aggregate the clean feeders (interest 1040 2b → line 1, dividends 3b →
      line 2, cap gains line 7 → line 5a) with preparer overrides; the rest preparer.
  (2) the §1411 nuances are preparer adjustments via line 4b (non-§1411 business,
      negative), line 5b (excluded gain), line 6 (CFC/PFIC), line 7 (other mods).

LAW VERIFIED 2026-06-15 (brief tts-tax-app server/specs/_8960_source_brief.md):
  line 8 = investment income; line 12 = line 8 − deductions; line 13 = MAGI (AGI +
  §911); line 15 = max(0, MAGI − threshold); line 16 = min(max(0, line 12), line
  15); line 17 = round(line 16 × 3.8%). Thresholds (statutory, NOT indexed): MFJ/QSS
  $250,000, MFS $125,000, single/HoH $200,000.

SAFETY GUARD: READY_TO_SEED stays False until Ken's review walk (the NIIT formula +
the threshold + the auto-feed/adjustment scope + the MAGI base).
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


READY_TO_SEED = True  # FLIPPED 2026-06-15 — Ken approved the review walk ("Approved — seed it, include render").


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_ENTITY_TYPES = ["1040"]
FORM_STATUS = "draft"

NIIT_RATE = 0.038
NIIT_THRESHOLD = {
    "mfj": 250000, "qss": 250000, "mfs": 125000, "single": 200000, "hoh": 200000,
}


# ═══════════════════════════════════════════════════════════════════════════
# THE MATH (the integrity gate re-types this independently; they share no math).
# ═══════════════════════════════════════════════════════════════════════════

from decimal import ROUND_HALF_UP, Decimal  # noqa: E402


def _D(x):
    return Decimal(str(x if x is not None else 0))


def _r0(x):
    return int(_D(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def threshold(filing_status) -> int:
    return NIIT_THRESHOLD.get((filing_status or "single").lower(), 200000)


def compute_8960(interest=0, dividends=0, annuities=0, rental=0, nonpassive_adj=0,
                 net_gain=0, gain_adj=0, cfc_pfic=0, other_mods=0, inv_interest_exp=0,
                 state_tax=0, misc_exp=0, magi=0, filing_status="single") -> dict:
    """The full §1411 chain. Returns line 8 / 10 / 12 / 13 / 15 / 16 / 17 (NIIT)."""
    line5 = _D(net_gain) - _D(gain_adj)
    line8 = (_D(interest) + _D(dividends) + _D(annuities) + _D(rental) + _D(nonpassive_adj)
             + line5 + _D(cfc_pfic) + _D(other_mods))
    line10 = _D(inv_interest_exp) + _D(state_tax) + _D(misc_exp)
    line12 = line8 - line10
    line13 = _D(magi)
    line15 = max(Decimal("0"), line13 - _D(threshold(filing_status)))
    line16 = min(max(Decimal("0"), line12), line15)
    line17 = _D(_r0(line16 * Decimal(str(NIIT_RATE))))
    return {"line8": line8, "line10": line10, "line12": line12, "line13": line13,
            "line15": line15, "line16": line16, "line17": line17}


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("net_investment_income_tax", "Net Investment Income Tax (§1411) — the 3.8% tax on investment income over the MAGI threshold; Form 8960 → Schedule 2 line 12"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_1040_FORM",
    "IRS_2025_1040_INSTR",
]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_F8960_INSTR",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Form 8960 — Net Investment Income Tax",
        "citation": "Instructions for Form 8960 (2025), Parts I-III",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/instructions/i8960",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": "Part I income (interest/dividends/gains auto-fed; the §1411 adjustments on 4b/5b/6/7 are preparer entries), Part II deductions, Part III the 3.8% on min(NII, MAGI excess). REQUIRES HUMAN REVIEW: estates/trusts out; the net-gain disposition-of-active-interest worksheet + the state-tax allocation ratio are simplified.",
        "topics": ["net_investment_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "Part III — the 3.8% NIIT on the lesser amount",
                "location_reference": "i8960 (2025), Part III, lines 12-17",
                "excerpt_text": (
                    "Line 12 is your net investment income (line 8 minus line 11). Line 13 is your modified "
                    "adjusted gross income. Line 14 is the threshold based on your filing status ($250,000 if "
                    "married filing jointly or qualifying surviving spouse, $125,000 if married filing "
                    "separately, $200,000 otherwise). Line 15 is the excess of line 13 over line 14. Line 16 "
                    "is the smaller of line 12 or line 15. Line 17 is line 16 multiplied by 3.8% — your net "
                    "investment income tax. Enter it on Schedule 2 (Form 1040), line 12."
                ),
                "summary_text": "NIIT = 3.8% × min(net investment income, MAGI − threshold) → Schedule 2 line 12.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part I income + the §1411 adjustments",
                "location_reference": "i8960 (2025), Part I, lines 1-8",
                "excerpt_text": (
                    "Include taxable interest (line 1), dividends (line 2), annuities (line 3), and rental, "
                    "royalty, partnership, S corporation, and trade-or-business income subject to section 1411 "
                    "(line 4a), with a negative adjustment on line 4b for income not subject to section 1411. "
                    "Net gain from the disposition of property is on line 5a, adjusted on lines 5b/5c to remove "
                    "gain not subject to section 1411 (such as gain on a personal residence or property held in "
                    "an active trade or business). Lines 6 and 7 are CFC/PFIC and other modifications."
                ),
                "summary_text": "Investment income = interest + dividends + annuities + §1411 rental/business + net §1411 gain + CFC/PFIC + other; non-§1411 amounts are removed on 4b/5b/6/7.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_1411",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §1411 — Net Investment Income Tax",
        "citation": "26 U.S.C. §1411(a)-(b) (3.8% on the lesser of NII or the MAGI excess over the threshold)",
        "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:1411%20edition:prelim)",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "§1411(a)(1): 3.8% of the lesser of net investment income or the excess of MAGI over the threshold ($250k/$125k/$200k, NOT inflation-indexed).",
        "topics": ["net_investment_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "§1411(a)(1) the tax",
                "location_reference": "26 U.S.C. §1411(a)(1)",
                "excerpt_text": (
                    "There is hereby imposed a tax equal to 3.8 percent of the lesser of net investment income "
                    "for the taxable year, or the excess (if any) of modified adjusted gross income over the "
                    "threshold amount."
                ),
                "summary_text": "3.8% × min(net investment income, MAGI − threshold).",
                "is_key_excerpt": True,
            },
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_F8960_INSTR", "FORM_8960", "governs"),
    ("IRC_1411", "FORM_8960", "governs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM: FORM_8960
# ═══════════════════════════════════════════════════════════════════════════

N_IDENTITY = {
    "form_number": "FORM_8960",
    "form_title": "Form 8960 Net Investment Income Tax (§1411) (TY2025)",
    "notes": (
        "Ken's 2 scope decisions 2026-06-15. A return-level FormDefinition on the "
        "1040 (no sub-model — NIIT is on the joint MAGI). Part I auto-aggregates "
        "interest (1040 2b → line 1), dividends (3b → line 2), and net gain (line 7 "
        "→ line 5a), with preparer overrides; annuities, §1411 rental (4a), the "
        "non-§1411 business adjustment (4b), the excluded-gain adjustment (5b), "
        "CFC/PFIC (6), and other modifications (7) are preparer entries. Part II "
        "deductions (9a/9b/9c). Part III: line 12 net investment income = line 8 − "
        "line 10; line 17 = 3.8% × min(max(0, line 12), MAGI − threshold) → Schedule "
        "2 line 12. MAGI = AGI + §911. Thresholds statutory ($250k/$125k/$200k)."
    ),
}

N_FACTS: list[dict] = [
    # ── Part I overrides (blank/0 = use the auto-feed) ──
    {"fact_key": "e8960_interest_override", "label": "Line 1 taxable interest (override; blank = 1040 2b)",
     "data_type": "decimal", "default_value": "0", "sort_order": 1, "notes": "Auto = 1040 line 2b."},
    {"fact_key": "e8960_dividends_override", "label": "Line 2 dividends (override; blank = 1040 3b)",
     "data_type": "decimal", "default_value": "0", "sort_order": 2, "notes": "Auto = 1040 line 3b."},
    {"fact_key": "e8960_net_gain_override", "label": "Line 5a net gain (override; blank = 1040 line 7)",
     "data_type": "decimal", "default_value": "0", "sort_order": 3, "notes": "Auto = 1040 line 7."},
    # ── Part I preparer entries ──
    {"fact_key": "e8960_annuities", "label": "Line 3 — annuities (non-qualified)",
     "data_type": "decimal", "default_value": "0", "sort_order": 4, "notes": "Investment income."},
    {"fact_key": "e8960_rental", "label": "Line 4a — §1411 rental/royalty/partnership/S-corp",
     "data_type": "decimal", "default_value": "0", "sort_order": 5, "notes": "Passive §1411 income."},
    {"fact_key": "e8960_nonpassive_adjustment", "label": "Line 4b — non-§1411 business adjustment (negative)",
     "data_type": "decimal", "default_value": "0", "sort_order": 6, "notes": "Removes active-business income."},
    {"fact_key": "e8960_gain_adjustment", "label": "Line 5b — excluded gain (residence / active business)",
     "data_type": "decimal", "default_value": "0", "sort_order": 7, "notes": "Subtracted from line 5a."},
    {"fact_key": "e8960_cfc_pfic", "label": "Line 6 — CFC/PFIC adjustments",
     "data_type": "decimal", "default_value": "0", "sort_order": 8, "notes": "Preparer."},
    {"fact_key": "e8960_other_modifications", "label": "Line 7 — other modifications to investment income",
     "data_type": "decimal", "default_value": "0", "sort_order": 9, "notes": "Preparer (can be negative)."},
    # ── Part II deductions ──
    {"fact_key": "e8960_investment_interest_expense", "label": "Line 9a — investment interest expense",
     "data_type": "decimal", "default_value": "0", "sort_order": 10, "notes": "Allocable to investment income."},
    {"fact_key": "e8960_state_tax_allocable", "label": "Line 9b — state/local/foreign income tax allocable",
     "data_type": "decimal", "default_value": "0", "sort_order": 11, "notes": "Allocable + SALT-cap limited."},
    {"fact_key": "e8960_misc_investment_expense", "label": "Line 9c — misc investment expenses",
     "data_type": "decimal", "default_value": "0", "sort_order": 12, "notes": "Preparer."},
    # ── Outputs ──
    {"fact_key": "e8960_line8", "label": "Line 8 — total investment income",
     "data_type": "decimal", "sort_order": 30, "notes": "OUTPUT."},
    {"fact_key": "e8960_line12", "label": "Line 12 — net investment income",
     "data_type": "decimal", "sort_order": 31, "notes": "OUTPUT. Line 8 − deductions."},
    {"fact_key": "e8960_line13", "label": "Line 13 — MAGI",
     "data_type": "decimal", "sort_order": 32, "notes": "OUTPUT. AGI + §911."},
    {"fact_key": "e8960_line16", "label": "Line 16 — smaller of NII or the MAGI excess",
     "data_type": "decimal", "sort_order": 33, "notes": "OUTPUT."},
    {"fact_key": "e8960_line17", "label": "Line 17 — NIIT (3.8%) → Schedule 2 line 12",
     "data_type": "decimal", "sort_order": 34, "notes": "OUTPUT."},
]

N_RULES: list[dict] = [
    {"rule_id": "R-8960-INCOME", "title": "Part I — total investment income (line 8)", "rule_type": "calculation",
     "precedence": 1, "sort_order": 1,
     "formula": ("line 8 = interest(1, auto 2b) + dividends(2, auto 3b) + annuities(3) + rental(4a) + "
                 "nonpassive_adj(4b) + (net_gain(5a, auto line 7) − gain_adj(5b)) + cfc_pfic(6) + other(7)."),
     "inputs": ["e8960_interest_override", "e8960_dividends_override", "e8960_net_gain_override",
                "e8960_annuities", "e8960_rental", "e8960_nonpassive_adjustment", "e8960_gain_adjustment",
                "e8960_cfc_pfic", "e8960_other_modifications"],
     "outputs": ["e8960_line8"],
     "description": "§1411 investment income; non-§1411 amounts removed on 4b/5b/6/7."},
    {"rule_id": "R-8960-NII", "title": "Net investment income (line 12 = line 8 − deductions)", "rule_type": "calculation",
     "precedence": 2, "sort_order": 2,
     "formula": "line 10 = 9a + 9b + 9c; line 12 = line 8 − line 10.",
     "inputs": ["e8960_investment_interest_expense", "e8960_state_tax_allocable", "e8960_misc_investment_expense"],
     "outputs": ["e8960_line12"],
     "description": "Deductions allocable to investment income."},
    {"rule_id": "R-8960-NIIT", "title": "Part III — the 3.8% NIIT", "rule_type": "calculation",
     "precedence": 3, "sort_order": 3,
     "formula": ("line 13 = MAGI (AGI + §911); line 15 = max(0, line 13 − threshold[fs]); line 16 = "
                 "min(max(0, line 12), line 15); line 17 = round(line 16 × 3.8%) → Schedule 2 line 12. "
                 "Threshold MFJ/QSS 250000 / MFS 125000 / single/HoH 200000 (statutory)."),
     "inputs": [], "outputs": ["e8960_line13", "e8960_line16", "e8960_line17"],
     "description": "§1411(a)(1). The tax on the lesser of NII or the MAGI excess."},
]

N_LINES: list[dict] = [
    {"line_number": "1", "description": "Line 1 — taxable interest", "line_type": "input"},
    {"line_number": "2", "description": "Line 2 — dividends", "line_type": "input"},
    {"line_number": "4a", "description": "Line 4a — §1411 rental/royalty/partnership/S-corp", "line_type": "input"},
    {"line_number": "4b", "description": "Line 4b — non-§1411 business adjustment", "line_type": "input"},
    {"line_number": "5a", "description": "Line 5a — net gain from disposition", "line_type": "input"},
    {"line_number": "5b", "description": "Line 5b — excluded gain adjustment", "line_type": "input"},
    {"line_number": "8", "description": "Line 8 — total investment income", "line_type": "calculated"},
    {"line_number": "10", "description": "Line 10 — total deductions (9a+9b+9c)", "line_type": "calculated"},
    {"line_number": "12", "description": "Line 12 — net investment income (8 − 10)", "line_type": "total"},
    {"line_number": "13", "description": "Line 13 — MAGI (AGI + §911)", "line_type": "calculated"},
    {"line_number": "14", "description": "Line 14 — threshold (by filing status)", "line_type": "calculated"},
    {"line_number": "15", "description": "Line 15 — MAGI over threshold (max(0, 13 − 14))", "line_type": "calculated"},
    {"line_number": "16", "description": "Line 16 — smaller of line 12 or line 15", "line_type": "calculated"},
    {"line_number": "17", "description": "Line 17 — NIIT (3.8%) → Schedule 2 line 12", "line_type": "total"},
    {"line_number": "sch2_12", "description": "NIIT → Schedule 2 line 12", "line_type": "total"},
]

N_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_8960_BELOW_THRESH", "title": "MAGI below the NIIT threshold — no NIIT", "severity": "info",
     "condition": "MAGI <= the filing-status threshold",
     "message": ("Modified AGI is at or below the Net Investment Income Tax threshold ($250,000 MFJ/QSS, "
                 "$125,000 MFS, $200,000 otherwise), so no §1411 tax applies regardless of investment income."),
     "notes": "§1411. The common non-taxable case."},
    {"diagnostic_id": "D_8960_NII_LOSS", "title": "Net investment income is zero or a loss — no NIIT", "severity": "info",
     "condition": "line 12 (net investment income) <= 0",
     "message": ("Net investment income (line 12) is zero or a loss after deductions, so no §1411 tax applies "
                 "even though MAGI exceeds the threshold."),
     "notes": "§1411. NIIT is on the lesser amount."},
    {"diagnostic_id": "D_8960_RENTAL", "title": "Rental income — confirm the §1411 classification", "severity": "info",
     "condition": "line 4a rental income is present",
     "message": ("Rental/partnership/S-corporation income is included on line 4a. Confirm whether it is "
                 "subject to §1411 (passive or non-trade-or-business) — income from an active trade or "
                 "business in which you materially participate is removed on line 4b."),
     "notes": "§1411(c)(2) the active-trade-or-business exclusion."},
    {"diagnostic_id": "D_8960_GAIN", "title": "Net gain — exclude residence / active-business gain", "severity": "info",
     "condition": "line 5a net gain is present (auto-fed from 1040 line 7)",
     "message": ("Net gain from the disposition of property (line 5a) was pulled from Form 1040 line 7. "
                 "Remove any gain not subject to §1411 — such as the excluded gain on a personal residence "
                 "or gain on property held in an active trade or business — on line 5b."),
     "notes": "§1411(c)(1)(A)(iii). The §121 / active-business exclusions."},
    {"diagnostic_id": "D_8960_STATE_TAX", "title": "State tax (line 9b) — allocable + SALT-cap limited", "severity": "info",
     "condition": "line 9b state-tax deduction is present",
     "message": ("State, local, and foreign income taxes are deductible on line 9b only to the extent "
                 "allocable to net investment income, and the deduction is limited by the $10,000 SALT cap on "
                 "Schedule A. Enter only the allocable, allowed amount."),
     "notes": "Reg. §1.1411-4(f). The allocation + SALT-cap interaction."},
]

N_SCENARIOS: list[dict] = [
    {"scenario_name": "N-T1 — interest + dividends, NII binds", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "interest": 5000, "dividends": 10000, "magi": 300000, "filing_status": "single"},
     "expected_outputs": {"e8960_line8": 15000, "e8960_line12": 15000, "e8960_line16": 15000, "e8960_line17": 570},
     "notes": "NII 15,000; excess 100,000; min = 15,000; 15,000 × 3.8% = 570."},
    {"scenario_name": "N-T2 — MAGI below threshold → no NIIT", "scenario_type": "edge_case", "sort_order": 2,
     "inputs": {"tax_year": 2025, "interest": 20000, "magi": 150000, "filing_status": "single"},
     "expected_outputs": {"e8960_line16": 0, "e8960_line17": 0},
     "notes": "MAGI 150,000 ≤ 200,000 → line 15 = 0 → no NIIT."},
    {"scenario_name": "N-T3 — MAGI excess binds", "scenario_type": "edge_case", "sort_order": 3,
     "inputs": {"tax_year": 2025, "interest": 50000, "magi": 210000, "filing_status": "single"},
     "expected_outputs": {"e8960_line16": 10000, "e8960_line17": 380},
     "notes": "NII 50,000; excess 10,000; min = 10,000; × 3.8% = 380."},
    {"scenario_name": "N-T4 — deductions reduce NII", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"tax_year": 2025, "interest": 20000, "inv_interest_exp": 3000, "state_tax": 2000, "magi": 300000, "filing_status": "single"},
     "expected_outputs": {"e8960_line8": 20000, "e8960_line12": 15000, "e8960_line17": 570},
     "notes": "20,000 income − 5,000 deductions = 15,000 NII; × 3.8% = 570."},
    {"scenario_name": "N-T5 — net investment loss → no NIIT", "scenario_type": "edge_case", "sort_order": 5,
     "inputs": {"tax_year": 2025, "net_gain": -10000, "interest": 2000, "magi": 300000, "filing_status": "single"},
     "expected_outputs": {"e8960_line12": -8000, "e8960_line16": 0, "e8960_line17": 0},
     "notes": "NII −8,000 (a loss) → line 16 = 0 → no NIIT."},
    {"scenario_name": "N-T6 — MFJ threshold 250,000", "scenario_type": "edge_case", "sort_order": 6,
     "inputs": {"tax_year": 2025, "interest": 40000, "magi": 270000, "filing_status": "mfj"},
     "expected_outputs": {"e8960_line16": 20000, "e8960_line17": 760},
     "notes": "excess 270,000 − 250,000 = 20,000; min(40,000, 20,000) = 20,000; × 3.8% = 760."},
    {"scenario_name": "N-T7 — gain adjustment (exclude residence gain)", "scenario_type": "edge_case", "sort_order": 7,
     "inputs": {"tax_year": 2025, "net_gain": 100000, "gain_adj": 90000, "magi": 300000, "filing_status": "single"},
     "expected_outputs": {"e8960_line8": 10000, "e8960_line17": 380},
     "notes": "net gain 100,000 − 90,000 excluded = 10,000 NII; excess 100,000; min = 10,000; × 3.8% = 380."},
    {"scenario_name": "N-G1 — below threshold → diagnostic", "scenario_type": "diagnostic", "sort_order": 8,
     "inputs": {"tax_year": 2025, "interest": 20000, "magi": 150000, "filing_status": "single"},
     "expected_outputs": {"D_8960_BELOW_THRESH": True},
     "notes": "MAGI < threshold → D_8960_BELOW_THRESH."},
]

N_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-8960-INCOME", "IRS_2025_F8960_INSTR", "primary", "Part I lines 1-8"),
    ("R-8960-INCOME", "IRC_1411", "secondary", "§1411(c) net investment income"),
    ("R-8960-NII", "IRS_2025_F8960_INSTR", "primary", "Part II lines 9-12"),
    ("R-8960-NIIT", "IRC_1411", "primary", "§1411(a)(1) the 3.8% on the lesser amount"),
    ("R-8960-NIIT", "IRS_2025_F8960_INSTR", "secondary", "Part III lines 13-17"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-8960-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Part I total investment income (line 8) + the §1411 adjustments",
     "description": "Validates R-8960-INCOME. Bug it catches: an income component dropped, or the 4b/5b/6/7 adjustments not applied (non-§1411 amounts left in).",
     "definition": {"kind": "formula_check", "form": "FORM_8960",
                    "formula": "line8 = interest + dividends + annuities + 4a + 4b + (5a − 5b) + 6 + 7"},
     "sort_order": 1},
    {"assertion_id": "FA-1040-8960-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Net investment income (line 12 = line 8 − deductions)",
     "description": "Validates R-8960-NII. Bug it catches: the deductions (9a/9b/9c) not subtracted from investment income.",
     "definition": {"kind": "formula_check", "form": "FORM_8960", "formula": "line12 = line8 − (9a + 9b + 9c)"},
     "sort_order": 2},
    {"assertion_id": "FA-1040-8960-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "The 3.8% NIIT on min(NII, MAGI excess); the threshold by filing status",
     "description": "Validates R-8960-NIIT. Bug it catches: the wrong threshold, the rate, or NIIT applied to the full NII when the MAGI excess is smaller.",
     "definition": {"kind": "formula_check", "form": "FORM_8960",
                    "formula": "line17 = round(min(max(0,line12), max(0, MAGI − threshold[fs])) × 0.038)"},
     "sort_order": 3},
    {"assertion_id": "FA-1040-8960-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "NIIT → Schedule 2 line 12",
     "description": "Validates the flow target. Bug it catches: the NIIT not landing on Schedule 2 line 12 (→ 1040 line 23 other taxes).",
     "definition": {"kind": "flow_assertion", "form": "FORM_8960",
                    "checks": [{"source_line": "17", "must_write_to": ["SCH_2.12"]}]},
     "sort_order": 4},
    {"assertion_id": "FA-1040-8960-05", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "Line 16 = the smaller of NII or the MAGI excess (floored at 0)",
     "description": "Validates R-8960-NIIT. Bug it catches: a net investment loss or a below-threshold MAGI producing a positive NIIT.",
     "definition": {"kind": "reconciliation", "form": "FORM_8960",
                    "formula": "line16 == min(max(0, line12), line15)"},
     "sort_order": 5},
    {"assertion_id": "FA-1040-8960-06", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Gates — below-threshold + net-loss produce zero NIIT",
     "description": "A MAGI at/below the threshold, or a net investment loss, fires an info and computes zero NIIT.",
     "definition": {"kind": "gating_check", "form": "FORM_8960", "expect": {"red_fires": True},
                    "blockers": ["below_threshold", "nii_loss"]},
     "sort_order": 6},
]


FORMS: list[dict] = [
    {"identity": N_IDENTITY, "facts": N_FACTS, "rules": N_RULES, "lines": N_LINES,
     "diagnostics": N_DIAGNOSTICS, "scenarios": N_SCENARIOS, "rule_links": N_RULE_LINKS},
]


class Command(BaseCommand):
    help = "Load the FORM_8960 spec (Net Investment Income Tax). Refuses until READY_TO_SEED=True."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad FORM_8960 spec (Net Investment Income Tax)\n"))
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
                "\nREFUSING TO SEED FORM_8960: not cleared to seed.\n\n"
                "Gated until Ken's review walk (the NIIT formula + the threshold + the\n"
                "auto-feed/adjustment scope + the MAGI base).\n\n"
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
        form = TaxForm.objects.filter(form_number="FORM_8960").first()
        if form:
            uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
            self.stdout.write("FORM_8960: all rules cited" if not uncited
                              else self.style.WARNING(f"FORM_8960 uncited rules: {len(uncited)}"))
