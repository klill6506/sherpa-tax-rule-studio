"""Load the STATE_REFUND spec — State & Local Income Tax Refund Worksheet (§111).

Post-sprint NEXT-UP #9 (the LAST post-sprint item). A prior-year state/local
INCOME-tax refund (Form 1099-G box 2) is taxable on the current year's Schedule 1
line 1 only to the extent it produced a federal tax benefit last year (the §111
tax-benefit rule / Pub 525 recoveries). Real-estate + personal-property tax
refunds + other Schedule A reimbursements → Schedule 1 line 8z. NO IRS AcroForm —
a worksheet in the instructions → render = a statement page.

KEN'S 3 SCOPE DECISIONS (2026-06-14, AskUserQuestion):
  (1) FULL Pub 525 Worksheet 2 + 2a (the SALT-cap recapture via the prior-year
      Sch A 5d/5e + the negative-prior-year-TI reduction + the 8z allocation for
      RE/PP/other recoveries). AMT-year / unused-credits / multi-year-or-joint-
      different / dependent = RED-deferred (a prior-year tax refigure, not automatable).
  (2) Prior-year facts on the Taxpayer (~18 sr_* facts; no new table/RLS).
  (3) TY2025 (2024 verified prior-year std-ded) + TY2026 (2025 interim, re-pin).

CONSTANTS VERIFIED 2026-06-14 from the 2025 i1040 Schedule 1 Line 1 worksheet +
Pub 525 Worksheet 2/2a (brief tts-tax-app server/specs/_state_refund_source_brief.md).
The SALT cap is NOT a compute constant — the worksheet reads the preparer-entered
prior-year Sch A 5d/5e, so only the prior-year standard-deduction table is
year-keyed (to the refund year = current tax_year − 1):
  - 2024 std ded (VERIFIED): single/MFS $14,600, MFJ/QSS $29,200, HoH $21,900;
    age/blind per box $1,950 (single/HoH) / $1,550 (MFJ/MFS/QSS).
  - 2025 std ded (INTERIM, OBBBA): single/MFS $15,750, MFJ/QSS $31,500, HoH $23,625;
    age/blind per box $2,000 (single/HoH) / $1,600 (MFJ/MFS/QSS). requires_human_review.

SAFETY GUARD: READY_TO_SEED stays False until Ken's review walk (the worksheet
math + the SALT-cap recapture + the negative-TI reduction + the std-ded constants).
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


READY_TO_SEED = True  # FLIPPED 2026-06-14 — Ken approved the review walk ("No changes. Continue").


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_ENTITY_TYPES = ["1040"]
FORM_STATUS = "draft"


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS — the prior-year standard deduction (the integrity gate re-types).
# Keyed to the REFUND year (= the current return's tax_year − 1).
# ═══════════════════════════════════════════════════════════════════════════

PY_STD_DEDUCTION = {
    2024: {"single": 14600, "mfs": 14600, "mfj": 29200, "qss": 29200, "hoh": 21900},
    2025: {"single": 15750, "mfs": 15750, "mfj": 31500, "qss": 31500, "hoh": 23625},  # INTERIM
}
PY_AGE_BLIND_PER_BOX = {
    2024: {"single": 1950, "hoh": 1950, "mfj": 1550, "mfs": 1550, "qss": 1550},
    2025: {"single": 2000, "hoh": 2000, "mfj": 1600, "mfs": 1600, "qss": 1600},  # INTERIM
}


def _round0(x) -> int:
    return int(round(x))


def py_standard_deduction(refund_year, filing_status, age_blind_boxes, override=0):
    """The prior-year standard deduction (worksheet lines 5-7). An override (the
    preparer entering the prior-year std ded directly) wins."""
    if override and override > 0:
        return override
    fs = (filing_status or "single").lower()
    basic = PY_STD_DEDUCTION.get(refund_year, PY_STD_DEDUCTION[2024]).get(fs, 0)
    perbox = PY_AGE_BLIND_PER_BOX.get(refund_year, PY_AGE_BLIND_PER_BOX[2024]).get(fs, 0)
    return basic + max(0, int(age_blind_boxes)) * perbox


def worksheet_2a(income_refund, re_pp_refund, py_5d, py_5e):
    """Pub 525 Worksheet 2a — split the benefit-giving recovery between the
    income-tax share (line 1a) and the RE/PP share (line 1b), applying the
    SALT-cap recapture (the prior-year Sch A 5d/5e). Returns (line_1a, line_1b)."""
    a1, a2 = income_refund, re_pp_refund
    a3 = min(a1 + a2, py_5d)                      # cap at the prior-year total SALT
    if py_5d > py_5e:                            # the deduction was cap-limited
        a4 = py_5d - py_5e                       # the part of SALT above the cap
        if a3 <= a4:
            return (0, 0)                        # STOP — the refund sat above the cap
        a5 = a3 - a4                             # the benefit-giving recovery
        a6 = a1 + a2
        if a6 <= 0:
            return (0, 0)
        return (_round0((a1 / a6) * a5), _round0((a2 / a6) * a5))
    # not cap-limited (5d == 5e): the recapture is bypassed (worksheet line 5 blank)
    return (a1, a2)


def worksheet_2(w1a, w1b, w_other, py_itemized, prior_refunded, py_std_ded,
                mfs_spouse_itemized, py_taxable_income):
    """Pub 525 Worksheet 2 — the itemized-vs-standard limit (the §111 difference
    limitation) + the negative-prior-year-TI reduction + the allocation between
    Schedule 1 line 1 (income-tax share) and line 8z (RE/PP + other). Returns
    (taxable_line1, taxable_8z)."""
    w3 = w1a + w1b + w_other
    if w3 <= 0:
        return (0, 0)
    w6 = py_itemized - prior_refunded
    if mfs_spouse_itemized:
        w8 = w6                                  # forced to itemize → full difference
    else:
        w8 = w6 - py_std_ded
    if w8 <= 0:
        return (0, 0)                            # standard >= itemized → no benefit
    w9 = min(w3, w8)
    if py_taxable_income >= 0:
        w11 = w9
    else:
        w11 = max(0, w9 + py_taxable_income)     # the negative-TI reduction
    line1 = _round0(w11 * (w1a / w3))
    line8z = _round0(w11) - line1                # the remainder (RE/PP + other share)
    return (line1, line8z)


def compute_state_refund(refund_year, income_refund, re_pp_refund, other_recoveries,
                         py_5d, py_5e, py_itemized, prior_refunded, py_taxable_income,
                         py_filing_status, py_age_blind_boxes, py_std_override,
                         did_itemize, sales_tax_elected, mfs_spouse_itemized):
    """The full chain. Gates first (didn't itemize / elected sales tax → none
    taxable), then Worksheet 2a + Worksheet 2. Returns (taxable_line1, taxable_8z)."""
    if not did_itemize or sales_tax_elected:
        return (0, 0)
    w1a, w1b = worksheet_2a(income_refund, re_pp_refund, py_5d, py_5e)
    py_std = py_standard_deduction(refund_year, py_filing_status, py_age_blind_boxes, py_std_override)
    return worksheet_2(w1a, w1b, other_recoveries, py_itemized, prior_refunded, py_std,
                       mfs_spouse_itemized, py_taxable_income)


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("state_refund_recovery", "State & local income-tax refund recoveries (§111) — the tax-benefit rule; taxable part → Sch 1 line 1 / RE-PP → line 8z"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_1040_FORM",
    "IRS_2025_1040_INSTR",
]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_SCH1_REFUND_WS",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Form 1040 — State and Local Income Tax Refund Worksheet (Schedule 1, Line 1)",
        "citation": "Instructions for Form 1040 (2025), Schedule 1 Line 1; the State and Local Income Tax Refund Worksheet",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i1040gi.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": "The simple 9-line worksheet + the prior-year std-ded amounts (lines 5-6). REQUIRES HUMAN REVIEW: re-pin the 2025 prior-year std-ded for the TY2026 path from the 2026 worksheet (~Dec 2026); confirm the line 2 (5d/5e) recapture wording.",
        "topics": ["state_refund_recovery"],
        "excerpts": [
            {
                "excerpt_label": "The refund cap + the SALT-cap recapture (lines 1-3)",
                "location_reference": "i1040 (2025), State and Local Income Tax Refund Worksheet, lines 1-3",
                "excerpt_text": (
                    "Line 1: enter the income tax refund from Form(s) 1099-G, but don't enter more than the "
                    "state and local income taxes shown on your prior-year Schedule A, line 5d. Line 2: is the "
                    "amount on Schedule A line 5d more than line 5e? No — enter line 1 on line 3 and go to line "
                    "4. Yes — subtract line 5e from line 5d. Line 3: is line 1 more than line 2? No — none of "
                    "your refund is taxable, stop. Yes — subtract line 2 from line 1."
                ),
                "summary_text": "Refund capped at 5d; if cap-limited (5d>5e) recapture 5d−5e, stop if refund <= recapture; else the benefit-giving part.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "The itemized-vs-standard limit + the prior-year std ded (lines 4-9)",
                "location_reference": "i1040 (2025), worksheet lines 4-9",
                "excerpt_text": (
                    "Line 4: total itemized deductions from your prior-year Schedule A, line 17. Line 5: the "
                    "prior-year standard deduction for your filing status (single/MFS $14,600, MFJ/QSS "
                    "$29,200, HoH $21,900 for 2024). Line 6: number of age-65/blind boxes times $1,550 ($1,950 "
                    "if single or HoH). Line 7: add lines 5 and 6. Line 8: is line 7 less than line 4? No — "
                    "none taxable, stop. Yes — subtract line 7 from line 4. Line 9: enter the smaller of line 3 "
                    "or line 8 on Schedule 1, line 1."
                ),
                "summary_text": "Taxable = min(benefit-recovery, itemized − prior-year std ded); none if standard >= itemized.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Not taxable (the gates)",
                "location_reference": "i1040 (2025), Schedule 1 Line 1",
                "excerpt_text": (
                    "None of your refund is taxable if, in the year you paid the tax, you either didn't itemize "
                    "deductions or elected to deduct state and local general sales taxes instead of state and "
                    "local income taxes."
                ),
                "summary_text": "Didn't itemize OR elected general sales tax → none taxable.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_PUB_525_RECOVERIES",
        "source_type": "official_guidance",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRS Publication 525 (2025) — Itemized Deduction Recoveries (Worksheet 2 + 2a)",
        "citation": "Pub. 525 (2025), Recoveries — Itemized Deduction Recoveries; Worksheet 2 and Worksheet 2a",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/p525.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": False,
        "trust_score": 9.00,
        "requires_human_review": True,
        "notes": "Worksheet 2 (the negative-TI reduction line 10/11 + the line-1/line-8z allocation) + Worksheet 2a (the 1a/1b proration with the SALT-cap recapture). REQUIRES HUMAN REVIEW: the AMT / unused-credit refigure exceptions are NOT modeled (RED-deferred).",
        "topics": ["state_refund_recovery"],
        "excerpts": [
            {
                "excerpt_label": "Worksheet 2 — the negative-TI reduction + the allocation",
                "location_reference": "Pub. 525 (2025), Worksheet 2, lines 9-11 + allocation",
                "excerpt_text": (
                    "Line 9: enter the smaller of line 3 (total recoveries) or line 8 (itemized over standard). "
                    "Line 10: your taxable income for the prior year (Form 1040, line 15; a negative amount is "
                    "entered in brackets). Line 11: if line 10 is zero or more, enter line 9; if line 10 is "
                    "negative, add lines 9 and 10 (but not less than zero). Allocate line 11 between Schedule 1 "
                    "line 1 (the income-tax-refund share) and line 8z (real-estate/personal-property and other "
                    "recoveries) in proportion to lines 1a and 1b+2."
                ),
                "summary_text": "Includible = min(recoveries, itemized−standard), reduced by negative prior-year TI; allocate income-tax share → line 1, the rest → line 8z.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Worksheet 2a — the 1a/1b proration with the cap recapture",
                "location_reference": "Pub. 525 (2025), Worksheet 2a",
                "excerpt_text": (
                    "Worksheet 2a computes Worksheet 2 lines 1a (state/local income tax refund) and 1b (real "
                    "estate + personal property tax refunds): cap the total at the prior-year Schedule A line "
                    "5d; if 5d exceeds 5e (the deduction was limited by the $10,000 SALT cap), the benefit-"
                    "giving recovery is the total minus (5d − 5e), prorated between the income-tax and RE/PP "
                    "refunds by their share of the total."
                ),
                "summary_text": "1a/1b = the cap-recaptured recovery prorated by the income-tax vs RE/PP share.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_111",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §111 — Recovery of Tax Benefit Items",
        "citation": "26 U.S.C. §111(a) (recoveries excluded to the extent they did not reduce tax)",
        "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:111%20edition:prelim)",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "The substantive tax-benefit rule: a recovered amount is excluded from income to the extent the prior deduction did not reduce tax.",
        "topics": ["state_refund_recovery"],
        "excerpts": [
            {
                "excerpt_label": "§111(a) the tax-benefit rule",
                "location_reference": "26 U.S.C. §111(a)",
                "excerpt_text": (
                    "Gross income does not include income attributable to the recovery during the taxable year "
                    "of any amount deducted in any prior taxable year to the extent such amount did not reduce "
                    "the amount of tax imposed."
                ),
                "summary_text": "A recovery is taxable only to the extent the prior deduction reduced tax.",
                "is_key_excerpt": True,
            },
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_SCH1_REFUND_WS", "STATE_REFUND", "governs"),
    ("IRS_PUB_525_RECOVERIES", "STATE_REFUND", "governs"),
    ("IRC_111", "STATE_REFUND", "governs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM: STATE_REFUND
# ═══════════════════════════════════════════════════════════════════════════

SR_IDENTITY = {
    "form_number": "STATE_REFUND",
    "form_title": "State & Local Income Tax Refund Worksheet (Schedule 1, Line 1) (TY2025)",
    "notes": (
        "Ken's 3 scope decisions 2026-06-14 (post-sprint NEXT-UP #9). A worksheet "
        "pseudo-form on the 1040 (no IRS AcroForm — a statement page). The §111 "
        "tax-benefit rule: a prior-year state/local income-tax refund (1099-G box "
        "2) is taxable on Schedule 1 line 1 only to the extent it gave a federal "
        "tax benefit. Full Pub 525 Worksheet 2 + 2a: the SALT-cap recapture (the "
        "prior-year Sch A 5d/5e), the itemized-vs-standard limit, the negative-"
        "prior-year-TI reduction, and the allocation (income-tax → line 1, RE/PP + "
        "other → line 8z). AMT-year / unused-credits / multi-year-or-joint-different "
        "/ dependent are RED-deferred (a manual prior-year refigure). The prior-year "
        "std ded is year-keyed (2024 verified / 2025 interim) to the refund year."
    ),
}

SR_FACTS: list[dict] = [
    # ── Inputs (Worksheet 2a) ──
    {"fact_key": "sr_income_tax_refund", "label": "State/local income-tax refund (1099-G box 2)",
     "data_type": "decimal", "default_value": "0", "sort_order": 1, "notes": "Worksheet 2a line 1 (1a)."},
    {"fact_key": "sr_re_pp_refund", "label": "Real-estate + personal-property tax refunds",
     "data_type": "decimal", "default_value": "0", "sort_order": 2, "notes": "Worksheet 2a line 2 (1b → line 8z)."},
    {"fact_key": "sr_py_sch_a_5d", "label": "Prior-year Schedule A line 5d (total SALT before the cap)",
     "data_type": "decimal", "default_value": "0", "sort_order": 3, "notes": "The refund cap + the recapture."},
    {"fact_key": "sr_py_sch_a_5e", "label": "Prior-year Schedule A line 5e (SALT after the cap)",
     "data_type": "decimal", "default_value": "0", "sort_order": 4, "notes": "5d>5e ⇒ cap-limited."},
    # ── Inputs (Worksheet 2) ──
    {"fact_key": "sr_other_recoveries", "label": "Other Schedule A refunds/reimbursements (→ line 8z)",
     "data_type": "decimal", "default_value": "0", "sort_order": 5, "notes": "Worksheet 2 line 2."},
    {"fact_key": "sr_py_sch_a_17", "label": "Prior-year Schedule A line 17 (total itemized)",
     "data_type": "decimal", "default_value": "0", "sort_order": 6, "notes": "Worksheet 2 line 4."},
    {"fact_key": "sr_py_prior_refunded", "label": "Prior-year amount previously refunded",
     "data_type": "decimal", "default_value": "0", "sort_order": 7, "notes": "Worksheet 2 line 5 (rare)."},
    {"fact_key": "sr_py_taxable_income", "label": "Prior-year taxable income (1040 line 15)",
     "data_type": "decimal", "default_value": "0", "sort_order": 8, "notes": "Worksheet 2 line 10 (negative reduces)."},
    {"fact_key": "sr_py_filing_status", "label": "Prior-year filing status",
     "data_type": "string", "default_value": "single", "sort_order": 9, "notes": "single/mfs/mfj/qss/hoh — the std ded."},
    {"fact_key": "sr_py_age_blind_boxes", "label": "Prior-year age-65/blind boxes (count 0-4)",
     "data_type": "integer", "default_value": "0", "sort_order": 10, "notes": "Worksheet line 6."},
    {"fact_key": "sr_py_std_deduction", "label": "Prior-year standard deduction (override)",
     "data_type": "decimal", "default_value": "0", "sort_order": 11, "notes": "Optional — wins over the computed lines 5-7."},
    # ── Gates ──
    {"fact_key": "sr_py_itemized", "label": "Itemized in the prior year?",
     "data_type": "boolean", "default_value": "false", "sort_order": 12, "notes": "No → none taxable."},
    {"fact_key": "sr_py_sales_tax_elected", "label": "Elected general sales tax (not income tax) in the prior year?",
     "data_type": "boolean", "default_value": "false", "sort_order": 13, "notes": "Yes → none taxable."},
    {"fact_key": "sr_py_mfs_spouse_itemized", "label": "Prior year MFS and spouse itemized?",
     "data_type": "boolean", "default_value": "false", "sort_order": 14, "notes": "Forced itemize → full difference."},
    # ── Exceptions (RED) ──
    {"fact_key": "sr_py_amt", "label": "Subject to AMT in the prior (deduction) year?",
     "data_type": "boolean", "default_value": "false", "sort_order": 15, "notes": "D_SR_AMT — manual refigure."},
    {"fact_key": "sr_py_unused_credits", "label": "Unused tax credits in the prior year?",
     "data_type": "boolean", "default_value": "false", "sort_order": 16, "notes": "D_SR_CREDITS — manual refigure."},
    {"fact_key": "sr_multiyear_or_joint_diff", "label": "Multi-year recovery / jointly-filed-different / dependent?",
     "data_type": "boolean", "default_value": "false", "sort_order": 17, "notes": "D_SR_EXCEPTION — manual."},
    # ── Outputs ──
    {"fact_key": "sr_taxable_line1", "label": "Taxable refund → Schedule 1 line 1",
     "data_type": "decimal", "sort_order": 30, "notes": "OUTPUT. The income-tax share."},
    {"fact_key": "sr_taxable_8z", "label": "Other recovery → Schedule 1 line 8z",
     "data_type": "decimal", "sort_order": 31, "notes": "OUTPUT. RE/PP + other recoveries."},
]

SR_RULES: list[dict] = [
    {"rule_id": "R-SR-GATES", "title": "Not taxable — didn't itemize / elected sales tax", "rule_type": "routing",
     "precedence": 1, "sort_order": 1,
     "formula": "If NOT sr_py_itemized OR sr_py_sales_tax_elected → taxable = 0 (none of the refund is taxable).",
     "inputs": ["sr_py_itemized", "sr_py_sales_tax_elected"], "outputs": [],
     "description": "§111. The deduction gave no benefit (standard taken / sales-tax elected)."},
    {"rule_id": "R-SR-WS2A", "title": "Worksheet 2a — the SALT-cap recapture + the 1a/1b split", "rule_type": "calculation",
     "precedence": 2, "sort_order": 2,
     "formula": ("a3 = min(income + RE/PP, py_5d); if py_5d > py_5e: a4 = py_5d − py_5e; if a3 ≤ a4 → 0; "
                 "else a5 = a3 − a4, 1a = round(income/total × a5), 1b = round(RE-PP/total × a5). Else "
                 "(not cap-limited): 1a = income, 1b = RE/PP."),
     "inputs": ["sr_income_tax_refund", "sr_re_pp_refund", "sr_py_sch_a_5d", "sr_py_sch_a_5e"], "outputs": [],
     "description": "Pub 525 Worksheet 2a. The post-TCJA SALT-cap interaction."},
    {"rule_id": "R-SR-STDDED", "title": "Prior-year standard deduction (lines 5-7)", "rule_type": "calculation",
     "precedence": 3, "sort_order": 3,
     "formula": ("py_std = override if > 0 else PY_STD_DEDUCTION[refund_year][fs] + boxes × "
                 "PY_AGE_BLIND_PER_BOX[refund_year][fs]. refund_year = tax_year − 1. 2024 verified / 2025 interim."),
     "inputs": ["sr_py_filing_status", "sr_py_age_blind_boxes", "sr_py_std_deduction"], "outputs": [],
     "description": "Year-keyed to the refund year. 2025 is INTERIM (D_SR_TY2026_INTERIM)."},
    {"rule_id": "R-SR-WS2", "title": "Worksheet 2 — the §111 limit + negative-TI + allocation", "rule_type": "calculation",
     "precedence": 4, "sort_order": 4,
     "formula": ("w3 = 1a + 1b + other; w8 = (itemized − prior_refunded) − py_std [MFS-spouse-itemized: skip "
                 "py_std]; if w8 ≤ 0 → 0; w9 = min(w3, w8); w11 = w9 if py_TI ≥ 0 else max(0, w9 + py_TI); "
                 "line1 = round(w11 × 1a/w3) → Sch 1 line 1; line8z = round(w11) − line1 → Sch 1 line 8z."),
     "inputs": ["sr_py_sch_a_17", "sr_py_prior_refunded", "sr_py_taxable_income", "sr_other_recoveries",
                "sr_py_mfs_spouse_itemized"],
     "outputs": ["sr_taxable_line1", "sr_taxable_8z"],
     "description": "Pub 525 Worksheet 2. The difference limitation + the negative-TI reduction + the line-1/8z allocation."},
    {"rule_id": "R-SR-EXCEPTIONS", "title": "RED-deferred exceptions (a manual prior-year refigure)", "rule_type": "routing",
     "precedence": 5, "sort_order": 5,
     "formula": ("If sr_py_amt → D_SR_AMT; if sr_py_unused_credits → D_SR_CREDITS; if "
                 "sr_multiyear_or_joint_diff → D_SR_EXCEPTION. The worksheet is NOT computed — prepare manually."),
     "inputs": ["sr_py_amt", "sr_py_unused_credits", "sr_multiyear_or_joint_diff"], "outputs": [],
     "description": "Pub 525 — AMT/credit refigures + multi-year/joint/dependent are out of v1 scope."},
]

SR_LINES: list[dict] = [
    {"line_number": "a1", "description": "2a-1 State/local income-tax refund (1099-G box 2)", "line_type": "input"},
    {"line_number": "a2", "description": "2a-2 Real-estate + personal-property tax refunds", "line_type": "input"},
    {"line_number": "a3", "description": "2a-3 Smaller of (a1 + a2) or prior-year Sch A line 5d", "line_type": "calculated"},
    {"line_number": "a4", "description": "2a-4 SALT-cap recapture (5d − 5e, if 5d > 5e)", "line_type": "calculated"},
    {"line_number": "a5", "description": "2a-5 Benefit-giving recovery (a3 − a4)", "line_type": "calculated"},
    {"line_number": "1a", "description": "WS2-1a Income-tax share (→ line 1)", "line_type": "calculated"},
    {"line_number": "1b", "description": "WS2-1b RE/PP share (→ line 8z)", "line_type": "calculated"},
    {"line_number": "w2", "description": "WS2-2 Other Schedule A recoveries (→ line 8z)", "line_type": "input"},
    {"line_number": "w3", "description": "WS2-3 Total recoveries (1a + 1b + 2)", "line_type": "calculated"},
    {"line_number": "w4", "description": "WS2-4 Prior-year total itemized (Sch A line 17)", "line_type": "input"},
    {"line_number": "w7", "description": "WS2-7 Prior-year standard deduction (basic + age/blind)", "line_type": "calculated"},
    {"line_number": "w8", "description": "WS2-8 Itemized over standard (line 4 − line 7)", "line_type": "calculated"},
    {"line_number": "w9", "description": "WS2-9 Smaller of total recoveries or the difference", "line_type": "calculated"},
    {"line_number": "w10", "description": "WS2-10 Prior-year taxable income (1040 line 15)", "line_type": "input"},
    {"line_number": "w11", "description": "WS2-11 Includible amount (after the negative-TI reduction)", "line_type": "calculated"},
    {"line_number": "sch1_1", "description": "Taxable refund → Schedule 1 line 1", "line_type": "total"},
    {"line_number": "sch1_8z", "description": "Other recovery → Schedule 1 line 8z", "line_type": "total"},
]

SR_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_SR_AMT", "title": "Prior-year AMT — state-refund taxability must be refigured", "severity": "error",
     "condition": "sr_py_amt is True AND a refund is present",
     "message": ("Not supported: you were subject to the Alternative Minimum Tax in the year you deducted the "
                 "state tax. Because state/local taxes are not deductible for the AMT, the refund's taxability "
                 "must be refigured by hand (Pub 525) — prepare this recovery manually."),
     "notes": "Pub 525 AMT refigure. RED-deferred."},
    {"diagnostic_id": "D_SR_CREDITS", "title": "Prior-year unused credits — refigure required", "severity": "error",
     "condition": "sr_py_unused_credits is True AND a refund is present",
     "message": ("Not supported: you had unused tax credits in the year you deducted the state tax. The refund "
                 "is taxable only up to the deduction that actually reduced tax — refigure by hand (Pub 525) "
                 "and prepare this recovery manually."),
     "notes": "Pub 525. RED-deferred."},
    {"diagnostic_id": "D_SR_EXCEPTION", "title": "Multi-year / jointly-filed-different / dependent — manual", "severity": "error",
     "condition": "sr_multiyear_or_joint_diff is True AND a refund is present",
     "message": ("Not supported: a multi-year recovery, a refund from a jointly-filed return when you aren't "
                 "now filing jointly with the same person, or a prior-year dependent situation. Prepare this "
                 "recovery manually (Pub 525)."),
     "notes": "Pub 525 Exception. RED-deferred."},
    {"diagnostic_id": "D_SR_INCOMPLETE", "title": "Refund present but the prior-year inputs are incomplete", "severity": "error",
     "condition": "a refund is present, itemized last year, but prior-year Sch A line 17 (or 5d) is missing",
     "message": ("A state/local income-tax refund is entered and you itemized last year, but the prior-year "
                 "amounts needed to determine taxability are missing (prior-year Schedule A line 17 and lines "
                 "5d/5e). Enter them so the refund is not silently treated as $0 taxable."),
     "notes": "No silent gap — the worksheet needs the prior-year return."},
    {"diagnostic_id": "D_SR_NONE_ITEMIZED", "title": "Refund not taxable — standard deduction / sales-tax election", "severity": "info",
     "condition": "a refund is present AND (NOT sr_py_itemized OR sr_py_sales_tax_elected)",
     "message": ("None of the state/local income-tax refund is taxable because you took the standard deduction "
                 "(or elected general sales tax) in the year you paid the tax — the deduction gave no federal "
                 "tax benefit."),
     "notes": "§111. The common non-taxable case."},
    {"diagnostic_id": "D_SR_8Z", "title": "Real-estate / property-tax recovery routed to line 8z", "severity": "info",
     "condition": "sr_taxable_8z > 0",
     "message": ("Recovered real-estate / personal-property taxes (and other Schedule A reimbursements) are "
                 "taxable on Schedule 1 line 8z, not line 1 — line 1 carries only the state/local income-tax "
                 "refund share."),
     "notes": "Pub 525 allocation."},
    {"diagnostic_id": "D_SR_TY2026_INTERIM", "title": "TY2026 prior-year std-ded constants are interim", "severity": "warning",
     "condition": "tax_year == 2026 AND a refund is present",
     "message": ("This 2026 return uses the 2025 prior-year standard-deduction amounts (OBBBA), which are "
                 "INTERIM until the 2026 worksheet publishes (~Dec 2026). Verify the prior-year standard "
                 "deduction on the recovery worksheet."),
     "notes": "Decision 3. The 2025 std-ded re-pin."},
]

SR_SCENARIOS: list[dict] = [
    {"scenario_name": "SR-T1 — simple taxable refund (no cap)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "income_refund": 1000, "re_pp_refund": 0, "other_recoveries": 0,
                "py_5d": 8000, "py_5e": 8000, "py_itemized": 20000, "prior_refunded": 0, "py_taxable_income": 50000,
                "py_filing_status": "single", "py_age_blind_boxes": 0, "py_std_override": 0,
                "did_itemize": True, "sales_tax_elected": False, "mfs_spouse_itemized": False},
     "expected_outputs": {"sr_taxable_line1": 1000, "sr_taxable_8z": 0},
     "notes": "No cap (5d=5e); 1a=1,000; itemized 20,000 − std 14,600 = 5,400; min(1,000, 5,400) = 1,000 → line 1."},
    {"scenario_name": "SR-T2 — refund entirely above the SALT cap (none taxable)", "scenario_type": "edge_case", "sort_order": 2,
     "inputs": {"tax_year": 2025, "income_refund": 3000, "re_pp_refund": 0, "other_recoveries": 0,
                "py_5d": 15000, "py_5e": 10000, "py_itemized": 25000, "prior_refunded": 0, "py_taxable_income": 50000,
                "py_filing_status": "single", "py_age_blind_boxes": 0, "py_std_override": 0,
                "did_itemize": True, "sales_tax_elected": False, "mfs_spouse_itemized": False},
     "expected_outputs": {"sr_taxable_line1": 0, "sr_taxable_8z": 0},
     "notes": "Cap-limited: recapture 5d−5e = 5,000; refund 3,000 ≤ 5,000 → STOP, the refund sat above the cap."},
    {"scenario_name": "SR-T3 — refund partly above the cap", "scenario_type": "edge_case", "sort_order": 3,
     "inputs": {"tax_year": 2025, "income_refund": 7000, "re_pp_refund": 0, "other_recoveries": 0,
                "py_5d": 15000, "py_5e": 10000, "py_itemized": 25000, "prior_refunded": 0, "py_taxable_income": 50000,
                "py_filing_status": "single", "py_age_blind_boxes": 0, "py_std_override": 0,
                "did_itemize": True, "sales_tax_elected": False, "mfs_spouse_itemized": False},
     "expected_outputs": {"sr_taxable_line1": 2000, "sr_taxable_8z": 0},
     "notes": "Recapture 5,000; benefit recovery 7,000 − 5,000 = 2,000; min(2,000, 25,000−14,600) = 2,000 → line 1."},
    {"scenario_name": "SR-T4 — the itemized-over-standard limit binds", "scenario_type": "edge_case", "sort_order": 4,
     "inputs": {"tax_year": 2025, "income_refund": 5000, "re_pp_refund": 0, "other_recoveries": 0,
                "py_5d": 9000, "py_5e": 9000, "py_itemized": 15000, "prior_refunded": 0, "py_taxable_income": 50000,
                "py_filing_status": "single", "py_age_blind_boxes": 0, "py_std_override": 0,
                "did_itemize": True, "sales_tax_elected": False, "mfs_spouse_itemized": False},
     "expected_outputs": {"sr_taxable_line1": 400, "sr_taxable_8z": 0},
     "notes": "1a=5,000; itemized 15,000 − std 14,600 = 400; min(5,000, 400) = 400 → line 1 (the difference caps it)."},
    {"scenario_name": "SR-T5 — didn't itemize → none taxable", "scenario_type": "edge_case", "sort_order": 5,
     "inputs": {"tax_year": 2025, "income_refund": 2000, "re_pp_refund": 0, "other_recoveries": 0,
                "py_5d": 0, "py_5e": 0, "py_itemized": 0, "prior_refunded": 0, "py_taxable_income": 0,
                "py_filing_status": "single", "py_age_blind_boxes": 0, "py_std_override": 0,
                "did_itemize": False, "sales_tax_elected": False, "mfs_spouse_itemized": False},
     "expected_outputs": {"sr_taxable_line1": 0, "sr_taxable_8z": 0},
     "notes": "Took the standard deduction last year → §111 gate, none taxable."},
    {"scenario_name": "SR-T6 — negative prior-year taxable income reduces it", "scenario_type": "edge_case", "sort_order": 6,
     "inputs": {"tax_year": 2025, "income_refund": 3000, "re_pp_refund": 0, "other_recoveries": 0,
                "py_5d": 9000, "py_5e": 9000, "py_itemized": 20000, "prior_refunded": 0, "py_taxable_income": -1000,
                "py_filing_status": "single", "py_age_blind_boxes": 0, "py_std_override": 0,
                "did_itemize": True, "sales_tax_elected": False, "mfs_spouse_itemized": False},
     "expected_outputs": {"sr_taxable_line1": 2000, "sr_taxable_8z": 0},
     "notes": "min(3,000, 20,000−14,600) = 3,000; negative TI −1,000 → 3,000 + (−1,000) = 2,000 → line 1."},
    {"scenario_name": "SR-T7 — RE/PP recovery allocates to line 8z", "scenario_type": "normal", "sort_order": 7,
     "inputs": {"tax_year": 2025, "income_refund": 1000, "re_pp_refund": 1000, "other_recoveries": 0,
                "py_5d": 10000, "py_5e": 10000, "py_itemized": 20000, "prior_refunded": 0, "py_taxable_income": 50000,
                "py_filing_status": "single", "py_age_blind_boxes": 0, "py_std_override": 0,
                "did_itemize": True, "sales_tax_elected": False, "mfs_spouse_itemized": False},
     "expected_outputs": {"sr_taxable_line1": 1000, "sr_taxable_8z": 1000},
     "notes": "1a=1,000, 1b=1,000; w3=2,000 ≤ 5,400; w11=2,000; line 1 = 2,000×1,000/2,000 = 1,000; line 8z = 1,000."},
    {"scenario_name": "SR-T8 — TY2026 interim (2025 std ded)", "scenario_type": "edge_case", "sort_order": 8,
     "inputs": {"tax_year": 2026, "income_refund": 1000, "re_pp_refund": 0, "other_recoveries": 0,
                "py_5d": 9000, "py_5e": 9000, "py_itemized": 20000, "prior_refunded": 0, "py_taxable_income": 50000,
                "py_filing_status": "single", "py_age_blind_boxes": 0, "py_std_override": 0,
                "did_itemize": True, "sales_tax_elected": False, "mfs_spouse_itemized": False},
     "expected_outputs": {"sr_taxable_line1": 1000, "sr_taxable_8z": 0},
     "notes": "Refund year 2025 → std single 15,750; itemized 20,000 − 15,750 = 4,250; min(1,000, 4,250) = 1,000."},
    {"scenario_name": "SR-G1 — prior-year AMT → RED", "scenario_type": "diagnostic", "sort_order": 9,
     "inputs": {"tax_year": 2025, "income_refund": 2000, "py_amt": True},
     "expected_outputs": {"D_SR_AMT": True},
     "notes": "Prior-year AMT → D_SR_AMT (manual refigure; not computed)."},
]

SR_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-SR-GATES", "IRS_2025_SCH1_REFUND_WS", "primary", "Didn't itemize / sales-tax election"),
    ("R-SR-GATES", "IRC_111", "secondary", "§111 the tax-benefit rule"),
    ("R-SR-WS2A", "IRS_PUB_525_RECOVERIES", "primary", "Worksheet 2a the SALT-cap recapture"),
    ("R-SR-WS2A", "IRS_2025_SCH1_REFUND_WS", "secondary", "The worksheet lines 1-3"),
    ("R-SR-STDDED", "IRS_2025_SCH1_REFUND_WS", "primary", "The prior-year std-ded lines 5-7"),
    ("R-SR-WS2", "IRS_PUB_525_RECOVERIES", "primary", "Worksheet 2 the limit + negative-TI + allocation"),
    ("R-SR-WS2", "IRC_111", "secondary", "§111 taxable only to the extent it reduced tax"),
    ("R-SR-EXCEPTIONS", "IRS_PUB_525_RECOVERIES", "primary", "The AMT/credit/multi-year exceptions"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-SR-01", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "The prior-year standard-deduction constants (2024 + 2025)",
     "description": "Pins the 2024 (verified) + 2025 (interim) prior-year std-ded basic + age/blind amounts. Bug it catches: a drifted std-ded or the wrong refund year.",
     "definition": {"kind": "constants_check", "form": "STATE_REFUND",
                    "constants": {"std_2024_single": 14600, "std_2024_mfj": 29200, "std_2024_hoh": 21900,
                                  "ab_2024_single": 1950, "ab_2024_mfj": 1550,
                                  "std_2025_single": 15750, "std_2025_mfj": 31500}},
     "sort_order": 1},
    {"assertion_id": "FA-1040-SR-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "The SALT-cap recapture (Worksheet 2a) + the §111 gates",
     "description": "Validates R-SR-WS2A + R-SR-GATES. Bug it catches: the recapture not applied (a refund above the cap wrongly taxed), or the didn't-itemize/sales-tax gate not stopping.",
     "definition": {"kind": "formula_check", "form": "STATE_REFUND",
                    "formula": "if 5d>5e: benefit = max(0, min(refund,5d) − (5d−5e)); gate: not itemized/sales-tax → 0"},
     "sort_order": 2},
    {"assertion_id": "FA-1040-SR-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "The itemized-over-standard limit + the negative-TI reduction",
     "description": "Validates R-SR-WS2. Bug it catches: the difference limitation not applied (full refund taxed when itemized barely exceeded standard), or the negative-prior-year-TI reduction missing.",
     "definition": {"kind": "formula_check", "form": "STATE_REFUND",
                    "formula": "taxable = min(recoveries, itemized − py_std); if py_TI<0: + py_TI (floored 0)"},
     "sort_order": 3},
    {"assertion_id": "FA-1040-SR-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Taxable income-tax refund → Sch 1 line 1; RE/PP → Sch 1 line 8z",
     "description": "Validates R-SR-WS2 the allocation. Bug it catches: the income-tax share not landing on Schedule 1 line 1, or RE/PP recoveries leaking onto line 1 instead of line 8z.",
     "definition": {"kind": "flow_assertion", "form": "STATE_REFUND",
                    "checks": [{"source_line": "sch1_1", "must_write_to": ["SCH_1.1"]},
                               {"source_line": "sch1_8z", "must_write_to": ["SCH_1.8z"]}]},
     "sort_order": 4},
    {"assertion_id": "FA-1040-SR-05", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "Worksheet allocation — line 1 + line 8z = the includible amount",
     "description": "Validates R-SR-WS2. Bug it catches: the line-1/line-8z proration not summing to the includible amount (line 11).",
     "definition": {"kind": "reconciliation", "form": "STATE_REFUND",
                    "formula": "sch1_1 + sch1_8z == w11 (the includible recovery)"},
     "sort_order": 5},
    {"assertion_id": "FA-1040-SR-06", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Gates — AMT/credit/multi-year RED; TY2026 interim",
     "description": "The prior-year AMT/credit/multi-year flags fire a RED (manual refigure); a 2026 return flags the interim std-ded constants.",
     "definition": {"kind": "gating_check", "form": "STATE_REFUND", "expect": {"red_fires": True},
                    "blockers": ["prior_year_amt"]},
     "sort_order": 6},
]


FORMS: list[dict] = [
    {"identity": SR_IDENTITY, "facts": SR_FACTS, "rules": SR_RULES, "lines": SR_LINES,
     "diagnostics": SR_DIAGNOSTICS, "scenarios": SR_SCENARIOS, "rule_links": SR_RULE_LINKS},
]


class Command(BaseCommand):
    help = "Load the STATE_REFUND spec (State refund taxability worksheet). Refuses until READY_TO_SEED=True."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad STATE_REFUND spec (State & Local Income Tax Refund Worksheet)\n"))
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
                "\nREFUSING TO SEED STATE_REFUND: not cleared to seed.\n\n"
                "Gated until Ken's review walk (the worksheet math + the SALT-cap recapture\n"
                "+ the negative-TI reduction + the prior-year std-ded constants).\n\n"
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
        form = TaxForm.objects.filter(form_number="STATE_REFUND").first()
        if form:
            uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
            self.stdout.write("STATE_REFUND: all rules cited" if not uncited
                              else self.style.WARNING(f"STATE_REFUND uncited rules: {len(uncited)}"))
