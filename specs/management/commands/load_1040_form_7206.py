"""Load the FORM_7206 spec — Self-Employed Health Insurance Deduction (§162(l)).

W-2 Unit 3 (2% S-corp shareholder SEHI). Form 7206 (new since TY2023; it replaced
the old SEHI worksheet) computes the §162(l) self-employed-health-insurance
deduction → Schedule 1 (Form 1040) line 17. ONE Form 7206 per trade/business; the
return total is the SUM of every Form 7206's line 14.

KEN'S 2 DECISIONS (2026-06-15, AskUserQuestion):
  (1) author a Form 7206 RS spec (not a bare engine extension).
  (2) fix the existing Schedule C SEHI limit — it caps only at net profit and does
      NOT subtract the ½-SE-tax (line 7) or SE-retirement (line 9) the form requires.

LAW VERIFIED 2026-06-15 against Form 7206 (2025) + i7206 + §162(l):
  TWO PATHS on one form, keyed by whether the business is an S corporation:
    • Schedule C / SE path (lines 4-10): line 4 = this business's net profit; line 6
      = line 4 / line 5 (Σ all net profits, no losses); line 7 = (Sch 1 L15 ½-SE-tax)
      × line 6; line 8 = line 4 − line 7; line 9 = (Sch 1 L16 SEP/SIMPLE) attributable;
      line 10 = line 8 − line 9.  ← the earned-income limit.
    • S-CORPORATION path: line 4 says "If the business is an S corporation, SKIP TO
      LINE 11." Line 11 = "Medicare wages (BOX 5 of Form W-2) from an S corporation in
      which you are a more-than-2% shareholder and in which the insurance plan is
      established." (No ½-SE-tax / SEP reduction — a 2% shareholder pays no SE tax.)
  Line 1 = premiums; line 2 = qualified LTC (age-capped); line 3 = 1 + 2.
  Line 12 = Form 2555 line 45 attributable (v1 = 0, RED-defer).
  Line 13 = (line 10 OR line 11, whichever applies) − line 12.
  Line 14 = min(line 3, line 13) → Schedule 1 line 17.

SAFETY GUARD: READY_TO_SEED stays False until Ken's review walk (the Box-5 earned-
income basis for the 2% shareholder; the Sch C ½-SE/SEP limit fix; LTC + 2555 scope).
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


READY_TO_SEED = True  # FLIPPED 2026-06-15 — Ken approved the review walk ("Approved — seed it").


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_ENTITY_TYPES = ["1040"]
FORM_STATUS = "draft"

# Form 7206 line 2 — qualified LTC premium age caps (2025). Documented for the
# preparer (D_7206_LTC_AGECAP); v1 takes an already-capped LTC amount (no auto-cap).
LTC_AGE_CAPS_2025 = {"<=40": 480, "41-50": 900, "51-60": 1800, "61-70": 4810, "71+": 6020}


# ═══════════════════════════════════════════════════════════════════════════
# THE MATH (the integrity gate re-types this independently; they share no math).
# ═══════════════════════════════════════════════════════════════════════════

from decimal import ROUND_HALF_UP, Decimal  # noqa: E402


def _D(x):
    return Decimal(str(x if x is not None else 0))


def _r0(x):
    return _D(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def compute_7206(premiums=0, ltc=0, *, is_scorp=False, net_profit=0,
                 all_net_profits=0, half_se_tax=0, sep_attributable=0,
                 scorp_box5=0, form2555=0) -> dict:
    """ONE Form 7206 (one trade/business). Line 14 (→ Schedule 1 line 17) =
    min(line 3, line 13). The S-corp path skips lines 4-10 and limits to Box 5."""
    l1 = _D(premiums)
    l2 = _D(ltc)
    l3 = l1 + l2
    l12 = _D(form2555)
    if is_scorp:
        l11 = _D(scorp_box5)
        l13 = l11 - l12
        l14 = min(l3, max(_D(0), l13))
        return {"line3": l3, "line11": l11, "line13": l13, "line14": _r0(l14)}
    # Schedule C / SE path (lines 4-10) — the earned-income limit.
    l4 = _D(net_profit)
    l5 = _D(all_net_profits)
    l6 = (l4 / l5) if l5 > 0 else _D(0)            # ratio (exact)
    l7 = _r0(_D(half_se_tax) * l6)                  # apportioned ½-SE-tax
    l8 = l4 - l7
    l9 = _D(sep_attributable)
    l10 = l8 - l9
    l13 = l10 - l12
    l14 = min(l3, max(_D(0), l13))
    return {"line3": l3, "line4": l4, "line6": l6, "line7": l7, "line8": l8,
            "line9": l9, "line10": l10, "line13": l13, "line14": _r0(l14)}


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("self_employed_health_insurance", "Self-Employed Health Insurance Deduction (§162(l)) — Form 7206 → Schedule 1 line 17; the net-profit / S-corp-Box-5 earned-income limit"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_1040_FORM",
    "IRS_2025_1040_INSTR",
]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_F7206_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Form 7206 — Self-Employed Health Insurance Deduction",
        "citation": "Form 7206 (2025), lines 1-14",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f7206.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.80,
        "requires_human_review": True,
        "notes": (
            "The form face. ONE Form 7206 per trade/business; line 14 = min(line 3 premiums, line 13 "
            "earned-income limit) → Schedule 1 line 17. S-CORP PATH: line 4 'If the business is an S "
            "corporation, skip to line 11'; line 11 = Medicare wages (BOX 5). REQUIRES HUMAN REVIEW: "
            "(a) Box 5 excludes the premium itself (correct 2% W-2 reporting), so the limit is the cash "
            "Medicare wages — only binds when the premium exceeds Box 5 (rare); (b) line 2 LTC age caps "
            "(480/900/1,800/4,810/6,020) are the preparer's responsibility in v1 (no auto-cap); (c) line "
            "12 Form 2555 foreign-earned-income adjustment is RED-deferred (v1 = 0)."
        ),
        "topics": ["self_employed_health_insurance"],
        "excerpts": [
            {
                "excerpt_label": "Line 4 — S corporations skip to line 11",
                "location_reference": "Form 7206 (2025), line 4",
                "excerpt_text": (
                    "Enter your net profit and any other earned income from the trade or business under "
                    "which the insurance plan is established. Don't include Conservation Reserve Program "
                    "payments exempt from self-employment tax. If the business is an S corporation, skip "
                    "to line 11."
                ),
                "summary_text": "S-corp shareholders skip the net-profit/½-SE-tax lines 4-10 and use the Box-5 limit on line 11.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Line 11 — S-corp 2% shareholder limit = Box 5 Medicare wages",
                "location_reference": "Form 7206 (2025), line 11",
                "excerpt_text": (
                    "Enter your Medicare wages (box 5 of Form W-2) from an S corporation in which you are "
                    "a more-than-2% shareholder and in which the insurance plan is established."
                ),
                "summary_text": "The 2% S-corp shareholder earned-income limit is the W-2 Box 5 Medicare wages from that S corporation.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Lines 6-10 + 13-14 — the Sch C earned-income limit and the smaller-of",
                "location_reference": "Form 7206 (2025), lines 5-14",
                "excerpt_text": (
                    "Line 5: total of all net profits. Line 6: divide line 4 by line 5. Line 7: multiply "
                    "Schedule 1 (Form 1040), line 15, deductible part of self-employment tax, by the "
                    "percentage on line 6. Line 8: subtract line 7 from line 4. Line 9: the amount from "
                    "Schedule 1 line 16 (self-employed SEP, SIMPLE, and qualified plans) attributable to "
                    "the same trade or business. Line 10: subtract line 9 from line 8. Line 13: subtract "
                    "line 12 from line 10 or 11, whichever applies. Line 14: enter the smaller of line 3 "
                    "or line 13 here and on Schedule 1 (Form 1040), line 17."
                ),
                "summary_text": "Sch C limit (line 10) = net profit − apportioned ½-SE-tax − SEP/SIMPLE; the deduction (line 14) = min(premiums, limit).",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_F7206_INSTR",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Form 7206 — Self-Employed Health Insurance Deduction",
        "citation": "Instructions for Form 7206 (2025)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/instructions/i7206",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": (
            "A separate Form 7206 per trade/business; the S-corp wages are 'shown as wages on Form W-2.' "
            "Pub 974 governs the SEHI↔PTC iterative when the plan is Marketplace coverage with advance/"
            "claimed premium tax credit."
        ),
        "topics": ["self_employed_health_insurance"],
        "excerpts": [
            {
                "excerpt_label": "One Form 7206 per trade/business; the S-corp wages",
                "location_reference": "i7206 (2025)",
                "excerpt_text": (
                    "If you have more than one health plan during the year and each plan is established "
                    "under a different business, you must use a separate Form 7206 to figure each plan's "
                    "net earnings limit. You received wages in 2025 from an S corporation in which you "
                    "were a more-than-2% shareholder. Health insurance premiums paid or reimbursed by the "
                    "S corporation are shown as wages on Form W-2."
                ),
                "summary_text": "One Form 7206 per business; the 2% S-corp premium is reported as W-2 wages (in Box 1, deductible as SEHI).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Pub 974 — the Marketplace/PTC iterative",
                "location_reference": "i7206 (2025), line 1 caution",
                "excerpt_text": (
                    "See Pub. 974 if the insurance plan was considered to be established under your "
                    "business and was obtained through the Marketplace, and advance payments of the "
                    "premium tax credit were made or you are claiming the premium tax credit."
                ),
                "summary_text": "SEHI + Marketplace/PTC → the Pub 974 iterative (handled by Form 8962 in this app).",
                "is_key_excerpt": False,
            },
        ],
    },
    {
        "source_code": "IRC_162L",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §162(l) — Special rules for health insurance costs of self-employed individuals",
        "citation": "26 U.S.C. §162(l) (deduction for SE health insurance, capped at earned income)",
        "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:162%20edition:prelim)",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": (
            "§162(l)(1) allows the deduction; §162(l)(2)(A) caps it at the taxpayer's earned income "
            "(§401(c)) derived from the trade or business under which the plan is established. A more-"
            "than-2% S-corp shareholder is treated under §1372 as a partner (self-employed) for §162(l); "
            "the S-corp wages are that earned income."
        ),
        "topics": ["self_employed_health_insurance"],
        "excerpts": [
            {
                "excerpt_label": "§162(l)(2)(A) — capped at earned income from the business",
                "location_reference": "26 U.S.C. §162(l)(2)(A)",
                "excerpt_text": (
                    "No deduction shall be allowed under paragraph (1) to the extent that the amount of "
                    "such deduction exceeds the taxpayer's earned income (within the meaning of section "
                    "401(c)) derived by the taxpayer from the trade or business with respect to which the "
                    "plan providing the medical care coverage is established."
                ),
                "summary_text": "The SEHI deduction can't exceed the earned income from the business establishing the plan.",
                "is_key_excerpt": True,
            },
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_F7206_FORM", "FORM_7206", "governs"),
    ("IRS_2025_F7206_INSTR", "FORM_7206", "governs"),
    ("IRC_162L", "FORM_7206", "governs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM: FORM_7206
# ═══════════════════════════════════════════════════════════════════════════

N_IDENTITY = {
    "form_number": "FORM_7206",
    "form_title": "Form 7206 Self-Employed Health Insurance Deduction (§162(l)) (TY2025)",
    "notes": (
        "W-2 Unit 3. ONE Form 7206 per trade/business; the return total → Schedule 1 "
        "line 17 = Σ (each form's line 14). SUPERSEDES the Schedule C spec's R-SC-SEHI "
        "(which capped only at net profit). Two paths: (Sch C/SE) limit = net profit − "
        "apportioned ½-SE-tax (line 7) − SEP/SIMPLE (line 9); (S-corp 2% shareholder) "
        "limit = Box 5 Medicare wages (line 11). Line 14 = min(premiums, limit). v1: "
        "LTC folded into the premium input (preparer-capped); Form 2555 line 12 = 0 "
        "(RED-defer). The Marketplace SEHI↔PTC iterative is owned by Form 8962."
    ),
}

N_FACTS: list[dict] = [
    # ── Inputs (sourced from existing models in the build leg) ──
    {"fact_key": "f7206_premiums", "label": "Line 1 — health insurance premiums under this business/plan",
     "data_type": "decimal", "default_value": "0", "sort_order": 1,
     "notes": ("Sch C path: ScheduleC.sc_sehi_amount. S-corp path: W2Income.two_percent_shareholder_health "
               "(already in W-2 Box 1). v1 folds any qualified LTC (already age-capped) into this amount.")},
    {"fact_key": "f7206_is_scorp", "label": "Is this an S-corporation 2% shareholder plan?",
     "data_type": "boolean", "default_value": "false", "sort_order": 2,
     "notes": "True for a W2Income with two_percent_shareholder_health > 0 → use the Box-5 path (skip to line 11)."},
    {"fact_key": "f7206_scorp_box5", "label": "Line 11 — S-corp Box 5 Medicare wages (earned-income limit)",
     "data_type": "decimal", "default_value": "0", "sort_order": 3,
     "notes": "W2Income.medicare_wages of the S-corp W-2. The 2% shareholder limit. Box 5 already excludes the premium."},
    {"fact_key": "f7206_net_profit", "label": "Line 4 — this business's net profit + other earned income",
     "data_type": "decimal", "default_value": "0", "sort_order": 4,
     "notes": "Sch C path: ScheduleC line 31 for this business. Derived."},
    {"fact_key": "f7206_all_net_profits", "label": "Line 5 — total of ALL net profits (no losses)",
     "data_type": "decimal", "default_value": "0", "sort_order": 5,
     "notes": "Σ positive Schedule C/F/K-1 net profits for the proprietor. Line 6 = line 4 / line 5. Derived."},
    {"fact_key": "f7206_half_se_tax", "label": "Sch 1 line 15 — deductible ½-SE-tax (apportioned by line 6)",
     "data_type": "decimal", "default_value": "0", "sort_order": 6,
     "notes": "Line 7 = this × line 6. From the proprietor's Schedule SE. Derived."},
    {"fact_key": "f7206_sep_attributable", "label": "Line 9 — SEP/SIMPLE/qualified-plan attributable to this business",
     "data_type": "decimal", "default_value": "0", "sort_order": 7,
     "notes": "Sch 1 line 16 attributable to this business. Reduces the earned-income limit. Derived/preparer."},
    {"fact_key": "f7206_form2555", "label": "Line 12 — Form 2555 line 45 attributable (v1 = 0, RED-defer)",
     "data_type": "decimal", "default_value": "0", "sort_order": 8,
     "notes": "Foreign-earned-income exclusion adjustment. RED-deferred in v1 (D_7206_2555)."},
    # ── Outputs ──
    {"fact_key": "f7206_line10", "label": "Line 10 — Sch C earned-income limit (net profit − ½-SE − SEP)",
     "data_type": "decimal", "sort_order": 30, "notes": "OUTPUT (Sch C path). THE FIX vs old R-SC-SEHI."},
    {"fact_key": "f7206_line13", "label": "Line 13 — the applicable earned-income limit",
     "data_type": "decimal", "sort_order": 31, "notes": "OUTPUT. Sch C: line 10 − 2555. S-corp: line 11 − 2555."},
    {"fact_key": "f7206_line14", "label": "Line 14 — this form's SEHI deduction (min of line 3, line 13)",
     "data_type": "decimal", "sort_order": 32, "notes": "OUTPUT. The per-business deduction."},
    {"fact_key": "f7206_sch1_l17", "label": "Schedule 1 line 17 — Σ all Form 7206 line 14",
     "data_type": "decimal", "sort_order": 33, "notes": "OUTPUT. The return total SEHI deduction."},
]

N_RULES: list[dict] = [
    {"rule_id": "R-7206-PREMIUM", "title": "Line 3 — total premiums (line 1 + line 2 LTC)", "rule_type": "calculation",
     "precedence": 1, "sort_order": 1,
     "formula": "line 3 = line 1 (health premiums) + line 2 (qualified LTC, age-capped). v1 folds LTC into line 1.",
     "inputs": ["f7206_premiums"], "outputs": [],
     "description": "The premiums available to deduct, before the earned-income limit."},
    {"rule_id": "R-7206-SCHEDC", "title": "Lines 4-10 — Schedule C earned-income limit", "rule_type": "calculation",
     "precedence": 2, "sort_order": 2,
     "formula": ("Sch C path: line 6 = line 4 (this net profit) / line 5 (Σ all net profits); line 7 = "
                 "(Sch 1 L15 ½-SE-tax) × line 6; line 8 = line 4 − line 7; line 10 = line 8 − line 9 "
                 "(SEP/SIMPLE). THE FIX: the limit subtracts the apportioned ½-SE-tax + SEP, not just net profit."),
     "inputs": ["f7206_net_profit", "f7206_all_net_profits", "f7206_half_se_tax", "f7206_sep_attributable"],
     "outputs": ["f7206_line10"],
     "description": "§162(l)(2)(A) earned income for a sole proprietor = net SE earnings (net profit − ½-SE-tax − SE-retirement)."},
    {"rule_id": "R-7206-SCORP", "title": "Line 11 — S-corp 2% shareholder limit = Box 5 Medicare wages", "rule_type": "calculation",
     "precedence": 3, "sort_order": 3,
     "formula": "S-corp path (skip lines 4-10): line 11 = W-2 Box 5 Medicare wages from the S corporation. line 13 = line 11 − line 12 (2555).",
     "inputs": ["f7206_is_scorp", "f7206_scorp_box5", "f7206_form2555"],
     "outputs": ["f7206_line13"],
     "description": "Form 7206 line 11. A more-than-2% shareholder's earned income is the S-corp Box-5 wages; no ½-SE-tax reduction (no SE tax)."},
    {"rule_id": "R-7206-DEDUCT", "title": "Line 14 — SEHI deduction = min(line 3, line 13) → Sch 1 L17", "rule_type": "calculation",
     "precedence": 4, "sort_order": 4,
     "formula": "line 14 = min(line 3 premiums, max(0, line 13 limit)); Schedule 1 line 17 = Σ all forms' line 14.",
     "inputs": ["f7206_form2555"], "outputs": ["f7206_line14", "f7206_sch1_l17"],
     "description": "The smaller of premiums or the earned-income limit, summed across every trade/business, → Schedule 1 line 17."},
]

N_LINES: list[dict] = [
    {"line_number": "1", "description": "Line 1 — health insurance premiums", "line_type": "input"},
    {"line_number": "2", "description": "Line 2 — qualified long-term care premiums (age-capped)", "line_type": "input"},
    {"line_number": "3", "description": "Line 3 — total premiums (1 + 2)", "line_type": "calculated"},
    {"line_number": "4", "description": "Line 4 — net profit + other earned income (S-corp: skip to 11)", "line_type": "input"},
    {"line_number": "5", "description": "Line 5 — total of all net profits", "line_type": "input"},
    {"line_number": "6", "description": "Line 6 — line 4 ÷ line 5 (apportionment ratio)", "line_type": "calculated"},
    {"line_number": "7", "description": "Line 7 — Sch 1 L15 ½-SE-tax × line 6", "line_type": "calculated"},
    {"line_number": "8", "description": "Line 8 — line 4 − line 7", "line_type": "calculated"},
    {"line_number": "9", "description": "Line 9 — SEP/SIMPLE attributable (Sch 1 L16)", "line_type": "input"},
    {"line_number": "10", "description": "Line 10 — line 8 − line 9 (Sch C earned-income limit)", "line_type": "calculated"},
    {"line_number": "11", "description": "Line 11 — S-corp Box 5 Medicare wages (2% shareholder limit)", "line_type": "input"},
    {"line_number": "12", "description": "Line 12 — Form 2555 line 45 attributable (v1 = 0)", "line_type": "input"},
    {"line_number": "13", "description": "Line 13 — line 10 or 11 (whichever applies) − line 12", "line_type": "calculated"},
    {"line_number": "14", "description": "Line 14 — min(line 3, line 13) → Schedule 1 line 17", "line_type": "total"},
    {"line_number": "sch1_17", "description": "Schedule 1 line 17 — Σ all Form 7206 line 14", "line_type": "total"},
]

N_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_7206_SCORP_NOWAGE", "title": "2% S-corp health premium but no Medicare wages", "severity": "warning",
     "condition": "f7206_is_scorp AND f7206_premiums > 0 AND f7206_scorp_box5 <= 0",
     "message": ("A 2% S-corporation shareholder health premium is present but the W-2 shows no Medicare "
                 "wages (Box 5). The self-employed health insurance deduction is limited to the Box 5 "
                 "Medicare wages, so it is $0. Verify the S-corp W-2 (the premium belongs in Box 1, with "
                 "the regular cash wages in Box 5)."),
     "notes": "Form 7206 line 11 / §162(l)(2)(A). No earned income → no deduction."},
    {"diagnostic_id": "D_7206_SCORP_LIM", "title": "2% S-corp premium exceeds Box 5 wages — partly nondeductible", "severity": "info",
     "condition": "f7206_is_scorp AND f7206_premiums > f7206_scorp_box5 > 0",
     "message": ("The 2% S-corporation health premium exceeds the Box 5 Medicare wages, so the self-"
                 "employed health insurance deduction is capped at the Box 5 wages; the excess is not "
                 "deductible as SEHI (it remains in income)."),
     "notes": "Form 7206 line 14 = min(line 3, line 11)."},
    {"diagnostic_id": "D_7206_SC_LIM", "title": "Schedule C SEHI exceeds the net-earnings limit — partly nondeductible", "severity": "info",
     "condition": "NOT is_scorp AND f7206_premiums > f7206_line10 (net profit − ½-SE-tax − SEP)",
     "message": ("The self-employed health insurance premium exceeds the business's net SE earnings after "
                 "the ½-self-employment-tax and SE-retirement deductions (Form 7206 line 10), so the "
                 "deduction is limited to that amount; the excess is not deductible as SEHI."),
     "notes": "Form 7206 lines 4-10/14. The limit is net profit − ½-SE-tax − SEP, NOT net profit alone."},
    {"diagnostic_id": "D_7206_LTC_AGECAP", "title": "Long-term care premiums — apply the age-based cap", "severity": "info",
     "condition": "qualified LTC premiums are included",
     "message": ("Qualified long-term care premiums are subject to an age-based annual cap (2025: $480 if "
                 "age ≤40, $900 41-50, $1,800 51-60, $4,810 61-70, $6,020 71+). Include only the capped "
                 "amount in the premium — v1 does not apply the cap automatically."),
     "notes": "Form 7206 line 2. v1 = preparer-capped."},
    {"diagnostic_id": "D_7206_2555", "title": "Form 2555 present — line 12 adjustment not modeled", "severity": "warning",
     "condition": "Form 2555 foreign-earned-income exclusion is present",
     "message": ("Form 2555 (foreign earned income exclusion) is present. Form 7206 line 12 reduces the "
                 "earned-income limit by the exclusion attributable to this business — not modeled in v1. "
                 "Verify the SEHI deduction manually."),
     "notes": "Form 7206 line 12. RED-defer."},
    {"diagnostic_id": "D_7206_PTC", "title": "Marketplace coverage — SEHI ↔ PTC iterative (Pub 974)", "severity": "info",
     "condition": "SEHI present AND Marketplace coverage with the premium tax credit",
     "message": ("This SEHI plan is Marketplace coverage with the premium tax credit. The deduction and "
                 "the PTC are interdependent (Pub 974) — Form 8962 re-solves the iterative and rewrites "
                 "Schedule 1 line 17. Make sure the §162(l)/§36B election is set."),
     "notes": "Owned by Form 8962 (f8962_se_sehi). Reads Schedule 1 line 17 source-agnostically."},
]

N_SCENARIOS: list[dict] = [
    # ── S-corp path ──
    {"scenario_name": "SCORP-T1 — premium under Box 5 (full deduction)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "premiums": 8000, "is_scorp": True, "scorp_box5": 60000},
     "expected_outputs": {"f7206_line13": 60000, "f7206_line14": 8000},
     "notes": "min(8,000 premium, 60,000 Box 5) = 8,000."},
    {"scenario_name": "SCORP-T2 — premium over Box 5 (limited)", "scenario_type": "edge_case", "sort_order": 2,
     "inputs": {"tax_year": 2025, "premiums": 15000, "is_scorp": True, "scorp_box5": 10000},
     "expected_outputs": {"f7206_line14": 10000, "D_7206_SCORP_LIM": True},
     "notes": "min(15,000, 10,000) = 10,000; 5,000 nondeductible → D_7206_SCORP_LIM."},
    {"scenario_name": "SCORP-T3 — premium but no Box 5 wages (zero)", "scenario_type": "diagnostic", "sort_order": 3,
     "inputs": {"tax_year": 2025, "premiums": 5000, "is_scorp": True, "scorp_box5": 0},
     "expected_outputs": {"f7206_line14": 0, "D_7206_SCORP_NOWAGE": True},
     "notes": "No Medicare wages → limit 0 → no deduction → D_7206_SCORP_NOWAGE."},
    {"scenario_name": "SCORP-T4 — LTC folded into premium", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"tax_year": 2025, "premiums": 5000, "is_scorp": True, "scorp_box5": 60000},
     "expected_outputs": {"f7206_line3": 5000, "f7206_line14": 5000},
     "notes": "4,000 health + 1,000 capped LTC entered as 5,000 premium; min(5,000, 60,000) = 5,000."},
    # ── Schedule C / SE path (THE FIX) ──
    {"scenario_name": "SC-T5 — limit not binding (full)", "scenario_type": "normal", "sort_order": 5,
     "inputs": {"tax_year": 2025, "premiums": 6000, "net_profit": 50000, "all_net_profits": 50000, "half_se_tax": 4000},
     "expected_outputs": {"f7206_line10": 46000, "f7206_line14": 6000},
     "notes": "limit = 50,000 − 4,000 (½-SE) − 0 = 46,000; min(6,000, 46,000) = 6,000."},
    {"scenario_name": "SC-T6 — premium exceeds limit (THE FIX binds)", "scenario_type": "edge_case", "sort_order": 6,
     "inputs": {"tax_year": 2025, "premiums": 6000, "net_profit": 5000, "all_net_profits": 5000, "half_se_tax": 700},
     "expected_outputs": {"f7206_line10": 4300, "f7206_line14": 4300, "D_7206_SC_LIM": True},
     "notes": "limit = 5,000 − 700 = 4,300; min(6,000, 4,300) = 4,300. OLD code wrongly gave 5,000 (capped at net profit only)."},
    {"scenario_name": "SC-T7 — SEP/SIMPLE reduces the limit", "scenario_type": "edge_case", "sort_order": 7,
     "inputs": {"tax_year": 2025, "premiums": 6000, "net_profit": 50000, "all_net_profits": 50000, "half_se_tax": 4000, "sep_attributable": 44000},
     "expected_outputs": {"f7206_line10": 2000, "f7206_line14": 2000, "D_7206_SC_LIM": True},
     "notes": "limit = 50,000 − 4,000 − 44,000 = 2,000; min(6,000, 2,000) = 2,000."},
    {"scenario_name": "SC-T8 — multi-business apportionment (line 6)", "scenario_type": "edge_case", "sort_order": 8,
     "inputs": {"tax_year": 2025, "premiums": 9500, "net_profit": 10000, "all_net_profits": 50000, "half_se_tax": 5000, "sep_attributable": 0},
     "expected_outputs": {"f7206_line6": "0.2", "f7206_line7": 1000, "f7206_line10": 9000, "f7206_line14": 9000, "D_7206_SC_LIM": True},
     "notes": "line 6 = 10,000/50,000 = 0.2; line 7 = 5,000 × 0.2 = 1,000; limit = 10,000 − 1,000 = 9,000; min(9,500, 9,000) = 9,000."},
]

N_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-7206-PREMIUM", "IRS_2025_F7206_FORM", "primary", "Lines 1-3 premiums"),
    ("R-7206-SCHEDC", "IRS_2025_F7206_FORM", "primary", "Lines 4-10 the net-earnings limit"),
    ("R-7206-SCHEDC", "IRC_162L", "secondary", "§162(l)(2)(A) earned-income cap"),
    ("R-7206-SCORP", "IRS_2025_F7206_FORM", "primary", "Line 11 Box 5 Medicare wages"),
    ("R-7206-SCORP", "IRC_162L", "secondary", "§162(l)/§1372 2% shareholder treated as self-employed"),
    ("R-7206-DEDUCT", "IRS_2025_F7206_FORM", "primary", "Line 14 smaller-of → Sch 1 L17"),
    ("R-7206-DEDUCT", "IRS_2025_F7206_INSTR", "secondary", "One Form 7206 per business; summed to line 17"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-7206-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Line 14 = the smaller of premiums (line 3) or the earned-income limit (line 13)",
     "description": "Validates R-7206-DEDUCT. Bug it catches: the deduction not capped at the earned-income limit (over-deduction).",
     "definition": {"kind": "formula_check", "form": "FORM_7206",
                    "formula": "line14 = min(line3, max(0, line13))"},
     "sort_order": 1},
    {"assertion_id": "FA-1040-7206-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "S-corp 2% shareholder limit = Box 5 Medicare wages (line 11)",
     "description": "Validates R-7206-SCORP. Bug it catches: the S-corp limit taken from net profit, Box 1, or anything but Box 5; the ½-SE-tax wrongly subtracted on the S-corp path.",
     "definition": {"kind": "formula_check", "form": "FORM_7206",
                    "formula": "is_scorp → line13 = scorp_box5 − form2555 (lines 4-10 skipped)"},
     "sort_order": 2},
    {"assertion_id": "FA-1040-7206-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Schedule C limit = net profit − apportioned ½-SE-tax − SEP (line 10)",
     "description": "Validates R-7206-SCHEDC — THE FIX. Bug it catches: the SEHI limit capping at net profit only (not subtracting ½-SE-tax line 7 or SEP line 9).",
     "definition": {"kind": "formula_check", "form": "FORM_7206",
                    "formula": "line10 = net_profit − round((sch1_l15 × net_profit/all_net_profits)) − sep_attributable"},
     "sort_order": 3},
    {"assertion_id": "FA-1040-7206-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Σ Form 7206 line 14 → Schedule 1 line 17",
     "description": "Validates the flow target. Bug it catches: the SEHI deduction not landing on Schedule 1 line 17 (→ 1040 adjustments → AGI); a 2%-S-corp-only return (no Schedule C) failing to write line 17 at all.",
     "definition": {"kind": "flow_assertion", "form": "FORM_7206",
                    "checks": [{"source_line": "14", "must_write_to": ["SCH_1.17"]}]},
     "sort_order": 4},
    {"assertion_id": "FA-1040-7206-05", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "The deduction is floored at 0 (no negative limit, no negative SEHI)",
     "description": "Validates R-7206-DEDUCT. Bug it catches: a negative earned-income limit producing a negative deduction, or a premium with zero Box 5 producing a deduction.",
     "definition": {"kind": "reconciliation", "form": "FORM_7206",
                    "formula": "line14 == min(line3, max(0, line13)) and line14 >= 0"},
     "sort_order": 5},
    {"assertion_id": "FA-1040-7206-06", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Gates — over-limit premiums + zero S-corp wages fire diagnostics",
     "description": "A premium over the limit (Sch C or S-corp) fires the partly-nondeductible info; a 2% premium with zero Box 5 fires the no-wages warning and zero deduction.",
     "definition": {"kind": "gating_check", "form": "FORM_7206", "expect": {"red_fires": True},
                    "blockers": ["scorp_nowage", "scorp_limited", "schedc_limited"]},
     "sort_order": 6},
]


FORMS: list[dict] = [
    {"identity": N_IDENTITY, "facts": N_FACTS, "rules": N_RULES, "lines": N_LINES,
     "diagnostics": N_DIAGNOSTICS, "scenarios": N_SCENARIOS, "rule_links": N_RULE_LINKS},
]


class Command(BaseCommand):
    help = "Load the FORM_7206 spec (Self-Employed Health Insurance Deduction). Refuses until READY_TO_SEED=True."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad FORM_7206 spec (Self-Employed Health Insurance Deduction)\n"))
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
                "\nREFUSING TO SEED FORM_7206: not cleared to seed.\n\n"
                "Gated until Ken's review walk (the Box-5 earned-income basis for the 2%\n"
                "shareholder; the Sch C ½-SE/SEP limit fix; LTC + Form 2555 scope).\n\n"
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
        form = TaxForm.objects.filter(form_number="FORM_7206").first()
        if form:
            uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
            self.stdout.write("FORM_7206: all rules cited" if not uncited
                              else self.style.WARNING(f"FORM_7206 uncited rules: {len(uncited)}"))
