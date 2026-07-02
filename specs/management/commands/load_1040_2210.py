"""Load the FORM_2210 spec — Underpayment of Estimated Tax (§6654), FULL build.

Phase 2, sixth common form. Ken's 2 scope decisions (2026-06-15): FULL (Part I +
Regular quarterly method + Schedule AI annualized); prior-year inputs as preparer
facts. The §6654 penalty → 1040 line 38.

Part I — required annual payment = min(90% current tax, 100%/110% prior tax); no
penalty if (current tax − withholding) < $1,000. Regular Method — per-period
required installment (l9/4 or the Schedule AI amount) vs payments; every payment
(a dated estimate, or a legacy quarter bucket dated on its due date) applies to
the EARLIEST underpaid installment, and each underpaid amount accrues from its
installment due date to the date it is cured, capped at 4/15/2026, at the §6621
rate (7% through 3/31/2026, 6% for 4/1-4/15/2026). Schedule AI — annualized
installments (factors 4/2.4/1.5/1, applicable % 22.5/45/67.5/90, smaller-of the
regular installment).

LAW VERIFIED 2026-06-15 (brief tts-tax-app server/specs/_2210_source_brief.md):
  $1,000 de-minimis; 90% / 100% / 110% (110% when prior AGI > $150,000 [$75,000
  MFS]); §6621 underpayment rate 7% (2025 + Q1 2026) / 6% (Q2 2026); four periods
  due 4/15, 6/15, 9/15/2025, 1/15/2026.

DATED AMENDMENT 2026-07-01 (Ken scope option 1 — build as designed,
tts-tax-app server/specs/2210_dated_penalty_design.md): the penalty formula now
accrues each underpayment to the DATE CURED (earliest-first application per the
i2210 Penalty Worksheet — "the number of days it remains unpaid (from the
installment due date to the date paid, or April 15, 2026)", excerpt
IRS_2025_F2210_INSTR already on this form) instead of always charging the fixed
due-date→4/15/2026 day count. With payments on the due dates the unified
algorithm reproduces the prior numbers exactly (P-T1..T6 unchanged); dated
payments add the effect (P-T7/P-T8). Withholding stays ¼-spread ON the due dates
(§6654(g) default; the actual-date withholding election remains deferred).

v1 NOTE (requires_human_review): Schedule AI takes the per-period annualized TAX as
a preparer input (t2210_ai_tax_q*) — the full per-period QDCGT/AMT bracket
computation is deferred. Withholding is spread evenly (no actual-date election).

SAFETY GUARD: READY_TO_SEED stays False until Ken's review walk (the safe-harbor +
the regular-method penalty rate periods + Schedule AI + the §6621 rates).
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
# 2026-07-01: the dated-accrual amendment rides the same approval — Ken chose scope
# option 1 ("build as designed") for the federal-payment-dates unit in-session.


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_ENTITY_TYPES = ["1040"]
FORM_STATUS = "draft"

# ── §6654 / §6621 constants (verified) ──
DE_MINIMIS = 1000
PCT_CURRENT = 0.90                 # 90% of current-year tax
HIGH_INCOME_AGI = 150000           # $75,000 if MFS
HIGH_INCOME_AGI_MFS = 75000
PCT_PRIOR_HIGH = 1.10              # 110% prior when high-income
PCT_PRIOR_NORMAL = 1.00
# §6621 underpayment rate for the 2025 penalty period (to 4/15/2026):
RATE_7 = 0.07                      # through 3/31/2026
RATE_6 = 0.06                      # 4/1-4/15/2026
DAYS_7 = [350, 289, 197, 75]       # days at 7% from each due date to 3/31/2026
DAYS_6 = [15, 15, 15, 15]          # days at 6% (4/1-4/15/2026), all periods
# Schedule AI:
AI_FACTOR = [4.0, 2.4, 1.5, 1.0]
AI_PCT = [0.225, 0.45, 0.675, 0.90]


from datetime import date  # noqa: E402
from decimal import ROUND_HALF_UP, Decimal  # noqa: E402

# Dated accrual (2026-07-01 amendment): the four installment due dates, the
# 7%→6% rate boundary, and the accrual cap. DAYS_7/DAYS_6 above are the
# derived due-date→cap day counts (days_at_rates(due, CAP) reproduces them —
# the integrity gate pins that equivalence).
DUE_DATES = [date(2025, 4, 15), date(2025, 6, 15), date(2025, 9, 15), date(2026, 1, 15)]
R7_END = date(2026, 3, 31)         # last calendar day at 7%
CAP_DATE = date(2026, 4, 15)       # accrual stops here (i2210: "or April 15, 2026")


def _D(x):
    return Decimal(str(x if x is not None else 0))


def _r0(x):
    return int(_D(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def penalty_factor(i) -> Decimal:
    """The composite §6621 factor for period i (underpayment outstanding to 4/15/2026)."""
    return (Decimal(DAYS_7[i]) / Decimal("365") * _D(RATE_7)
            + Decimal(DAYS_6[i]) / Decimal("365") * _D(RATE_6))


# ── Pure functions (mirror the RS loader; the integrity gate re-types) ──


def required_annual_payment(current_tax, other_taxes, refundable_credits, withholding,
                            prior_year_tax, prior_year_agi, filing_status, prior_full_year=True) -> dict:
    """Part I. Returns l4/l5/l7/l8/l9 + whether a penalty can apply."""
    l4 = _D(current_tax) + _D(other_taxes) - _D(refundable_credits)
    l5 = _D(_r0(l4 * _D(PCT_CURRENT)))
    l7 = l4 - _D(withholding)
    fs = (filing_status or "single").lower()
    agi_thr = HIGH_INCOME_AGI_MFS if fs == "mfs" else HIGH_INCOME_AGI
    pct = PCT_PRIOR_HIGH if _D(prior_year_agi) > agi_thr else PCT_PRIOR_NORMAL
    # No prior-year safe harbor if the prior year wasn't a full 12-month year with tax.
    l8 = _D(_r0(_D(prior_year_tax) * _D(pct))) if (prior_full_year and _D(prior_year_tax) > 0) else None
    l9 = l5 if l8 is None else min(l5, l8)
    return {"l4": l4, "l5": l5, "l7": l7, "l8": (l8 if l8 is not None else _D(0)),
            "l9": l9, "penalty_possible": l7 >= DE_MINIMIS}


def regular_installments(l9) -> list[Decimal]:
    """The 25% method — four equal required installments."""
    q = _D(l9) / Decimal("4")
    return [q, q, q, q]


def ai_installments(ai_tax, reg_installments) -> list[Decimal]:
    """Schedule AI — annualized installment per period = annualized_tax × applicable% −
    prior required installments; line 27 = the smaller of that or the regular installment."""
    out = []
    prior = Decimal("0")
    for i in range(4):
        annualized = max(Decimal("0"), _D(ai_tax[i]) * _D(AI_PCT[i]) - prior)
        req = min(annualized, _D(reg_installments[i]))
        out.append(req)
        prior += req
    return out


def _as_date(d) -> date:
    """Scenario JSON carries ISO strings; the pure functions accept both."""
    if isinstance(d, date):
        return d
    return date.fromisoformat(str(d))


def days_at_rates(due: date, end: date) -> tuple[int, int]:
    """Chargeable days for an underpayment due `due` and cured `end` (already
    capped at CAP_DATE by the caller): (days at 7%, days at 6%). Simple date
    subtraction — the convention that makes days_at_rates(due, CAP_DATE)
    reproduce DAYS_7[i]/DAYS_6[i] exactly."""
    if end <= due:
        return 0, 0
    d7 = max(0, (min(end, R7_END) - due).days)
    d6 = max(0, (min(end, CAP_DATE) - max(due, R7_END)).days)
    return d7, d6


def _chunk_penalty(due: date, cure: date, amount: Decimal) -> Decimal:
    d7, d6 = days_at_rates(due, min(cure, CAP_DATE))
    return amount * (Decimal(d7) / Decimal("365") * _D(RATE_7)
                     + Decimal(d6) / Decimal("365") * _D(RATE_6))


def regular_penalty(installments, withholding, est_payments, payments_dated=None) -> dict:
    """The §6621 penalty, unified dated algorithm (i2210 Penalty Worksheet):
    withholding is treated as paid ¼ ON each due date (§6654(g) default);
    every payment — a dated (date, amount) pair, or a legacy quarter bucket
    dated on its due date — applies to the EARLIEST still-underpaid
    installment; each underpaid amount accrues from its installment due date
    to the date it is cured, capped at 4/15/2026 (7% through 3/31/2026, 6%
    for 4/1–4/15/2026). A payment on or before the due date cures with zero
    chargeable days. With payments exactly on the due dates this reproduces
    the prior fixed-day formula (P-T1..T6 pin that equivalence).

    Returns the per-installment underpayments AS OF each due date (the Form
    2210 line-25 face value — a later catch-up payment stops the accrual but
    does not erase the underpayment that existed at the due date) + the
    total penalty."""
    if payments_dated:
        payments = [(_as_date(d), _D(a)) for d, a in payments_dated]
    else:
        payments = [(DUE_DATES[i], _D(est_payments[i])) for i in range(4)]
    wh_q = _D(withholding) / Decimal("4")
    events = sorted(
        [(DUE_DATES[i], wh_q) for i in range(4) if wh_q > 0] + payments,
        key=lambda e: e[0],
    )

    remaining = [_D(x) for x in installments]
    applied_on_time = [Decimal("0")] * 4  # applied by the installment's due date
    penalty = Decimal("0")
    for paid_on, amount in events:
        amount = _D(amount)
        for i in range(4):
            if amount <= 0:
                break
            if remaining[i] <= 0:
                continue
            applied = min(amount, remaining[i])
            remaining[i] -= applied
            amount -= applied
            if paid_on <= DUE_DATES[i]:
                applied_on_time[i] += applied
            penalty += _chunk_penalty(DUE_DATES[i], paid_on, applied)
    for i in range(4):
        if remaining[i] > 0:
            penalty += _chunk_penalty(DUE_DATES[i], CAP_DATE, remaining[i])
    underpayments = [
        max(Decimal("0"), _D(installments[i]) - applied_on_time[i])
        for i in range(4)
    ]
    return {"underpayments": underpayments, "penalty": _D(_r0(penalty))}


def compute_2210(current_tax=0, other_taxes=0, refundable_credits=0, withholding=0,
                 prior_year_tax=0, prior_year_agi=0, filing_status="single", prior_full_year=True,
                 est_payments=(0, 0, 0, 0), use_annualized=False, ai_tax=(0, 0, 0, 0),
                 payments_dated=None) -> dict:
    """The full §6654 chain. Returns l9 (required annual payment) + the penalty → 1040 line 38.
    `payments_dated` — [(date|ISO string, amount), ...] — REPLACES the quarter
    buckets when present (the tts FederalEstimatedPayment rows)."""
    p1 = required_annual_payment(current_tax, other_taxes, refundable_credits, withholding,
                                 prior_year_tax, prior_year_agi, filing_status, prior_full_year)
    if not p1["penalty_possible"]:
        return {"l9": p1["l9"], "penalty": Decimal("0"), "no_penalty": True}
    reg = regular_installments(p1["l9"])
    installments = ai_installments(ai_tax, reg) if use_annualized else reg
    pen = regular_penalty(installments, withholding, est_payments, payments_dated)
    return {"l9": p1["l9"], "penalty": pen["penalty"], "underpayments": pen["underpayments"],
            "no_penalty": pen["penalty"] <= 0}


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("estimated_tax_penalty", "Underpayment of estimated tax (§6654) — the required annual payment safe harbors + the §6621 penalty; Form 2210 → 1040 line 38"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_1040_FORM",
    "IRS_2025_1040_INSTR",
]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_F2210_INSTR",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Form 2210 — Underpayment of Estimated Tax",
        "citation": "Instructions for Form 2210 (2025), Parts I-IV + Schedule AI",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/instructions/i2210",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": "Part I safe harbors ($1,000 / 90% / 100% / 110% over $150k AGI), the Regular Method penalty (§6621 7%/6% rate periods to 4/15/2026), and Schedule AI (factors 4/2.4/1.5/1, % 22.5/45/67.5/90). REQUIRES HUMAN REVIEW: Schedule AI takes the per-period annualized TAX as a preparer input (the full per-period bracket/QDCGT computation is deferred); withholding spread evenly; Part II waiver + farmers/fishermen out of v1.",
        "topics": ["estimated_tax_penalty"],
        "excerpts": [
            {
                "excerpt_label": "Part I — the required annual payment + the $1,000 de-minimis",
                "location_reference": "i2210 (2025), Part I lines 4-9",
                "excerpt_text": (
                    "Line 4 is your current-year tax. Line 5 is 90% of line 4. Line 6 is your withholding. If "
                    "line 4 minus line 6 (line 7) is less than $1,000, you don't owe a penalty. Line 8 is your "
                    "prior-year tax, multiplied by 110% if your prior-year AGI was more than $150,000 ($75,000 "
                    "if married filing separately). Line 9, the required annual payment, is the smaller of line "
                    "5 or line 8."
                ),
                "summary_text": "Required annual payment = min(90% current, 100%/110% prior); no penalty if current tax − withholding < $1,000.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "The Regular Method penalty + the §6621 rate",
                "location_reference": "i2210 (2025), Part III + the Penalty Worksheet",
                "excerpt_text": (
                    "The required installment for each period is one-fourth of line 9. The penalty on each "
                    "underpayment is figured as the underpayment times the number of days it remains unpaid "
                    "(from the installment due date to the date paid, or April 15, 2026) divided by 365 times "
                    "the interest rate. The underpayment rate is 7% for days through March 31, 2026, and 6% for "
                    "April 1 through April 15, 2026."
                ),
                "summary_text": "Penalty = underpayment × days/365 × rate (7% to 3/31/2026, 6% to 4/15/2026).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule AI — the annualized income method",
                "location_reference": "i2210 (2025), Schedule AI",
                "excerpt_text": (
                    "Annualize your income for each period by multiplying by 4 (Jan 1-Mar 31), 2.4 (Jan 1-May "
                    "31), 1.5 (Jan 1-Aug 31), and 1 (Jan 1-Dec 31). Figure the tax on each annualized amount and "
                    "multiply by the applicable percentage: 22.5%, 45%, 67.5%, and 90%. The required "
                    "installment is the smaller of this annualized installment or the regular method installment."
                ),
                "summary_text": "AI installment = annualized tax × (22.5/45/67.5/90)% − prior installments; the required installment is the smaller of the AI or regular amount.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_6654",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §6654 — Failure to Pay Estimated Income Tax",
        "citation": "26 U.S.C. §6654 (the addition to tax for underpayment of estimated tax; the §6621 rate)",
        "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:6654%20edition:prelim)",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "§6654: the required annual payment is the lesser of 90% of the current tax or 100% (110% high-income) of the prior; the penalty is the §6621 underpayment rate on each underpaid installment.",
        "topics": ["estimated_tax_penalty"],
        "excerpts": [
            {
                "excerpt_label": "§6654(d) the required annual payment",
                "location_reference": "26 U.S.C. §6654(d)(1)",
                "excerpt_text": (
                    "The required annual payment is the lesser of 90 percent of the tax shown on the return for "
                    "the taxable year, or 100 percent of the tax shown on the return for the preceding taxable "
                    "year (110 percent if the adjusted gross income exceeded $150,000)."
                ),
                "summary_text": "Required annual payment = lesser of 90% current or 100%/110% prior.",
                "is_key_excerpt": True,
            },
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_F2210_INSTR", "FORM_2210", "governs"),
    ("IRC_6654", "FORM_2210", "governs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM: FORM_2210
# ═══════════════════════════════════════════════════════════════════════════

P_IDENTITY = {
    "form_number": "FORM_2210",
    "form_title": "Form 2210 Underpayment of Estimated Tax (§6654) (TY2025)",
    "notes": (
        "Ken's 2 scope decisions 2026-06-15 (FULL build). A return-level FormDefinition "
        "on the 1040 (no sub-model). Part I: required annual payment = min(90% current "
        "tax, 100%/110% prior) — no penalty if current tax − withholding < $1,000. "
        "Regular Method: per-period required installment (line 9 / 4 or the Schedule AI "
        "amount) vs payments (withholding spread 1/4 + the estimated payments); the "
        "penalty on each underpayment accrues to 4/15/2026 at the §6621 rate (7% through "
        "3/31/2026, 6% for 4/1-4/15/2026) → 1040 line 38. Schedule AI: annualized "
        "installments (factors 4/2.4/1.5/1, % 22.5/45/67.5/90, smaller-of the regular). "
        "v1: Schedule AI takes the per-period annualized TAX as a preparer input "
        "(requires_human_review); withholding spread evenly; Part II waiver deferred."
    ),
}

P_FACTS: list[dict] = [
    # ── Part I preparer inputs ──
    {"fact_key": "t2210_prior_year_tax", "label": "Prior-year (2024) total tax",
     "data_type": "decimal", "default_value": "0", "sort_order": 1, "notes": "Line 8 — the 100%/110% safe harbor."},
    {"fact_key": "t2210_prior_year_agi", "label": "Prior-year (2024) AGI",
     "data_type": "decimal", "default_value": "0", "sort_order": 2, "notes": "> $150k ($75k MFS) → 110%."},
    {"fact_key": "t2210_prior_full_year", "label": "Prior year was a full 12-month year with a tax liability?",
     "data_type": "boolean", "default_value": "true", "sort_order": 3, "notes": "No → the 100% safe harbor is unavailable."},
    # ── Schedule AI ──
    {"fact_key": "t2210_use_annualized", "label": "Use the annualized income method (Schedule AI)?",
     "data_type": "boolean", "default_value": "false", "sort_order": 4, "notes": "Uneven income."},
    {"fact_key": "t2210_payments_dated", "label": "Dated federal estimated payments entered?",
     "data_type": "boolean", "default_value": "false", "sort_order": 9,
     "notes": ("Marker: dated (amount, date_paid) payment rows exist (tts FederalEstimatedPayment). When "
               "present they REPLACE the flat quarter buckets; each payment applies earliest-first and "
               "stops that underpayment's accrual on its date (R-2210-REG). §6654-creditable kinds only: "
               "estimate + prior_year_applied (the 1040 line-26 set; an overpayment applied is treated as "
               "paid 4/15 — the i2210 convention; extension/other rows are recorded, never credited). A "
               "dated total that differs from the flat line-26 buckets fires D_2210_DATED.")},
    {"fact_key": "t2210_ai_tax_q1", "label": "Schedule AI — annualized tax, period 1 (Jan-Mar)",
     "data_type": "decimal", "default_value": "0", "sort_order": 5, "notes": "Preparer-computed (v1)."},
    {"fact_key": "t2210_ai_tax_q2", "label": "Schedule AI — annualized tax, period 2 (Jan-May)",
     "data_type": "decimal", "default_value": "0", "sort_order": 6, "notes": "Preparer-computed (v1)."},
    {"fact_key": "t2210_ai_tax_q3", "label": "Schedule AI — annualized tax, period 3 (Jan-Aug)",
     "data_type": "decimal", "default_value": "0", "sort_order": 7, "notes": "Preparer-computed (v1)."},
    {"fact_key": "t2210_ai_tax_q4", "label": "Schedule AI — annualized tax, period 4 (Jan-Dec)",
     "data_type": "decimal", "default_value": "0", "sort_order": 8, "notes": "Preparer-computed (v1)."},
    # ── Outputs ──
    {"fact_key": "t2210_line9", "label": "Required annual payment (line 9)",
     "data_type": "decimal", "sort_order": 30, "notes": "OUTPUT. min(90% current, 100/110% prior)."},
    {"fact_key": "t2210_penalty", "label": "Estimated tax penalty → 1040 line 38",
     "data_type": "decimal", "sort_order": 31, "notes": "OUTPUT. §6621 on the underpayments."},
]

P_RULES: list[dict] = [
    {"rule_id": "R-2210-RAP", "title": "Part I — required annual payment + the $1,000 de-minimis", "rule_type": "calculation",
     "precedence": 1, "sort_order": 1,
     "formula": ("l4 = current_tax + other_taxes − refundable_credits; l5 = round(0.90 × l4); l7 = l4 − "
                 "withholding; if l7 < $1,000 → no penalty. l8 = round(prior_tax × (1.10 if prior_AGI > "
                 "$150k [$75k MFS] else 1.00)) [only if prior was a full year]; l9 = min(l5, l8)."),
     "inputs": ["t2210_prior_year_tax", "t2210_prior_year_agi", "t2210_prior_full_year"],
     "outputs": ["t2210_line9"],
     "description": "§6654(d). The safe harbors."},
    {"rule_id": "R-2210-REG", "title": "Regular Method — dated underpayment accrual + §6621 penalty", "rule_type": "calculation",
     "precedence": 2, "sort_order": 2,
     "formula": ("required installment = l9/4 (or the Schedule AI amount); withholding is treated as paid "
                 "1/4 ON each due date (§6654(g) default); every payment — a dated estimate, or a legacy "
                 "quarter bucket dated on its due date — applies to the EARLIEST still-underpaid "
                 "installment; each underpaid amount accrues from its installment due date to the date it "
                 "is cured, capped at 4/15/2026: penalty += amount × (days@7%/365 × 7% + days@6%/365 × "
                 "6%), 7% through 3/31/2026, 6% for 4/1-4/15/2026; → 1040 line 38. Due dates 4/15/2025, "
                 "6/15/2025, 9/15/2025, 1/15/2026. With payments on the due dates this equals the prior "
                 "fixed-day formula (DAYS_7 = [350,289,197,75], DAYS_6 = [15,15,15,15])."),
     "inputs": ["t2210_use_annualized", "t2210_payments_dated"], "outputs": ["t2210_penalty"],
     "description": ("The §6621 penalty accrues per day from the installment due date to the date paid "
                     "(i2210 Penalty Worksheet, earliest-first; 7% to 3/31/2026, 6% to 4/15/2026).")},
    {"rule_id": "R-2210-AI", "title": "Schedule AI — annualized installments", "rule_type": "calculation",
     "precedence": 3, "sort_order": 3,
     "formula": ("annualized installment[i] = max(0, ai_tax[i] × AI_PCT[i] − Σ prior); AI_PCT = "
                 "[22.5,45,67.5,90]%; the required installment = min(annualized, the regular l9/4). The "
                 "annualized tax per period is a preparer input in v1."),
     "inputs": ["t2210_ai_tax_q1", "t2210_ai_tax_q2", "t2210_ai_tax_q3", "t2210_ai_tax_q4"], "outputs": [],
     "description": "Schedule AI factors 4/2.4/1.5/1; applicable % 22.5/45/67.5/90."},
]

P_LINES: list[dict] = [
    {"line_number": "4", "description": "Line 4 — current year tax", "line_type": "calculated"},
    {"line_number": "5", "description": "Line 5 — 90% of line 4", "line_type": "calculated"},
    {"line_number": "6", "description": "Line 6 — withholding taxes", "line_type": "input"},
    {"line_number": "7", "description": "Line 7 — line 4 − line 6 (< $1,000 → no penalty)", "line_type": "calculated"},
    {"line_number": "8", "description": "Line 8 — prior-year tax (× 110% if high-income)", "line_type": "input"},
    {"line_number": "9", "description": "Line 9 — required annual payment (smaller of 5 or 8)", "line_type": "calculated"},
    {"line_number": "18", "description": "Line 18 — required installment per period (l9/4 or Schedule AI)", "line_type": "calculated"},
    {"line_number": "25", "description": "Line 25 — underpayment per period", "line_type": "calculated"},
    {"line_number": "ai27", "description": "Schedule AI line 27 — annualized required installment", "line_type": "calculated"},
    {"line_number": "19", "description": "Line 19 — the penalty → 1040 line 38", "line_type": "total"},
    {"line_number": "1040_38", "description": "Estimated tax penalty → Form 1040 line 38", "line_type": "total"},
]

P_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_2210_NO_PENALTY", "title": "No estimated tax penalty (safe harbor met)", "severity": "info",
     "condition": "line 7 < $1,000, or payments >= required annual payment",
     "message": ("No §6654 penalty applies — either the balance after withholding is under $1,000, or the "
                 "withholding plus timely estimated payments met the required annual payment (90% of this "
                 "year's tax, or 100%/110% of last year's)."),
     "notes": "§6654 the safe harbors."},
    {"diagnostic_id": "D_2210_PRIOR_YEAR", "title": "Prior-year tax not entered — safe harbor untested", "severity": "warning",
     "condition": "a penalty is computed but prior-year tax is blank",
     "message": ("A penalty is computed but the prior-year tax is blank, so the 100%/110% prior-year safe "
                 "harbor can't be tested — the 90%-of-current path may overstate the required payment. Enter "
                 "the 2024 total tax (and AGI) to use the prior-year safe harbor."),
     "notes": "No silent gap — the prior-year safe harbor is often the lower number."},
    {"diagnostic_id": "D_2210_110", "title": "High income — the 110% prior-year safe harbor applies", "severity": "info",
     "condition": "prior-year AGI > $150,000 ($75,000 MFS)",
     "message": ("Prior-year AGI exceeds $150,000 ($75,000 if married filing separately), so the prior-year "
                 "safe harbor is 110% of the 2024 tax (not 100%)."),
     "notes": "§6654(d)(1)(C)."},
    {"diagnostic_id": "D_2210_AI", "title": "Schedule AI used — verify the per-period tax", "severity": "info",
     "condition": "the annualized income method is used",
     "message": ("The annualized income method (Schedule AI) is used. In this version the per-period annualized "
                 "tax is entered by the preparer — verify each period's tax (including any QDCGT / AMT) before "
                 "relying on the installment amounts."),
     "notes": "v1 simplification (requires_human_review)."},
    {"diagnostic_id": "D_2210_DATED", "title": "Dated payments don't reconcile with 1040 line 26", "severity": "warning",
     "condition": ("dated FederalEstimatedPayment rows exist AND their §6654-creditable total (estimate + "
                   "prior_year_applied) != the flat est_payment_q1..q4 + PY-applied total that feeds 1040 "
                   "line 26"),
     "message": ("Dated federal estimated payments are entered, but their total (estimates + prior-year "
                 "overpayment applied) does not equal the flat quarterly amounts on 1040 line 26. The Form "
                 "2210 penalty uses the DATED payments; line 26 uses the flat amounts — reconcile them so "
                 "the return's payments and the penalty computation tell the same story."),
     "notes": ("No silent gap: line 26 stays on the flat quarter buckets (spine R-PAY-04, out of this "
               "unit's scope); the penalty uses the dated rows when present. A divergence is preparer "
               "error, not a computable choice.")},
    {"diagnostic_id": "D_2210_TY2026", "title": "TY2026 — re-verify the §6621 rates", "severity": "warning",
     "condition": "tax_year == 2026 AND a penalty is computed",
     "message": ("This 2026 return uses the 2025-period §6621 rates (7%/6%), which are INTERIM for a 2026 "
                 "penalty period — re-verify the quarterly underpayment rates from the 2026 Form 2210 (~Dec "
                 "2026)."),
     "notes": "Re-pin the 2026 rates."},
]

P_SCENARIOS: list[dict] = [
    {"scenario_name": "P-T1 — under $1,000 balance → no penalty", "scenario_type": "edge_case", "sort_order": 1,
     "inputs": {"tax_year": 2025, "current_tax": 10000, "withholding": 9500},
     "expected_outputs": {"t2210_penalty": 0},
     "notes": "line 7 = 10,000 − 9,500 = 500 < 1,000 → no penalty."},
    {"scenario_name": "P-T2 — prior-year safe harbor met → no penalty", "scenario_type": "edge_case", "sort_order": 2,
     "inputs": {"tax_year": 2025, "current_tax": 30000, "withholding": 20000, "prior_year_tax": 18000,
                "prior_year_agi": 100000, "est_payments": [0, 0, 0, 0]},
     "expected_outputs": {"t2210_line9": 18000, "t2210_penalty": 0},
     "notes": "l5 = 27,000; l8 = 18,000 (100%); l9 = 18,000; withholding 20,000 ≥ 18,000 → no penalty."},
    {"scenario_name": "P-T3 — full underpayment (no estimates) → penalty", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"tax_year": 2025, "current_tax": 12000, "withholding": 0, "prior_year_tax": 10000,
                "prior_year_agi": 100000, "est_payments": [0, 0, 0, 0]},
     "expected_outputs": {"t2210_line9": 10000, "t2210_penalty": 461},
     "notes": "l5 = 10,800; l8 = 10,000; l9 = 10,000; each installment 2,500 underpaid → 2,500 × (0.069589 + 0.057890 + 0.040247 + 0.016849) = 461."},
    {"scenario_name": "P-T4 — 110% high-income safe harbor", "scenario_type": "edge_case", "sort_order": 4,
     "inputs": {"tax_year": 2025, "current_tax": 50000, "withholding": 30000, "prior_year_tax": 40000,
                "prior_year_agi": 200000, "est_payments": [0, 0, 0, 0]},
     "expected_outputs": {"t2210_line9": 44000},
     "notes": "l5 = 45,000; l8 = 40,000 × 1.10 = 44,000; l9 = min = 44,000."},
    {"scenario_name": "P-T5 — estimated payments cure the underpayment", "scenario_type": "edge_case", "sort_order": 5,
     "inputs": {"tax_year": 2025, "current_tax": 12000, "withholding": 0, "prior_year_tax": 10000,
                "prior_year_agi": 100000, "est_payments": [2500, 2500, 2500, 2500]},
     "expected_outputs": {"t2210_penalty": 0},
     "notes": "l9 = 10,000; each installment 2,500 fully paid each period → no underpayment → no penalty."},
    {"scenario_name": "P-T6 — partial estimates → reduced penalty", "scenario_type": "edge_case", "sort_order": 6,
     "inputs": {"tax_year": 2025, "current_tax": 12000, "withholding": 0, "prior_year_tax": 10000,
                "prior_year_agi": 100000, "est_payments": [2500, 2500, 0, 0]},
     "expected_outputs": {"t2210_penalty": 143},
     "notes": "periods 1-2 paid; periods 3-4 underpaid 2,500 each → 2,500 × (0.040247 + 0.016849) = 143."},
    {"scenario_name": "P-T7 — dated mid-year lump cures earliest-first", "scenario_type": "edge_case", "sort_order": 7,
     "inputs": {"tax_year": 2025, "current_tax": 12000, "withholding": 0, "prior_year_tax": 10000,
                "prior_year_agi": 100000, "payments_dated": [["2025-08-01", 5000]]},
     "expected_outputs": {"t2210_line9": 10000, "t2210_penalty": 217},
     "notes": ("HAND-COMPUTED: installments 2,500 due 4/15/6/15/9/15/25+1/15/26. The 8/1/2025 lump cures "
               "installment 1 after 108 days (2,500×108/365×7% = 51.78) and installment 2 after 47 days "
               "(22.53); installments 3-4 stay unpaid to the cap (100.62 + 42.12). Total 217.05 → 217. "
               "The OLD fixed-day formula could not credit the mid-year cure.")},
    {"scenario_name": "P-T8 — Q4 estimate paid 10 days late", "scenario_type": "edge_case", "sort_order": 8,
     "inputs": {"tax_year": 2025, "current_tax": 12000, "withholding": 0, "prior_year_tax": 10000,
                "prior_year_agi": 100000,
                "payments_dated": [["2025-04-15", 2500], ["2025-06-15", 2500], ["2025-09-15", 2500],
                                    ["2026-01-25", 2500]]},
     "expected_outputs": {"t2210_line9": 10000, "t2210_penalty": 5},
     "notes": ("HAND-COMPUTED: installments 1-3 cured on their due dates (0 days). Installment 4 (due "
               "1/15/2026) cured 1/25/2026 → 10 days @ 7%: 2,500×10/365×7% = 4.79 → 5. The OLD flat "
               "q4 bucket assumed on-time payment → 0 (the understatement this amendment fixes).")},
    {"scenario_name": "P-G1 — no penalty diagnostic", "scenario_type": "diagnostic", "sort_order": 9,
     "inputs": {"tax_year": 2025, "current_tax": 10000, "withholding": 9500},
     "expected_outputs": {"D_2210_NO_PENALTY": True},
     "notes": "line 7 < 1,000 → D_2210_NO_PENALTY."},
    {"scenario_name": "P-G2 — dated payments diverge from line 26", "scenario_type": "diagnostic", "sort_order": 10,
     "inputs": {"tax_year": 2025, "current_tax": 12000, "withholding": 0, "prior_year_tax": 10000,
                "prior_year_agi": 100000, "est_payments": [0, 0, 0, 0],
                "payments_dated": [["2025-04-15", 2500]]},
     "expected_outputs": {"D_2210_DATED": True},
     "notes": ("Dated creditable total 2,500 != the flat line-26 buckets (0) → D_2210_DATED. The penalty "
               "itself uses the dated rows.")},
]

P_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-2210-RAP", "IRC_6654", "primary", "§6654(d) the required annual payment"),
    ("R-2210-RAP", "IRS_2025_F2210_INSTR", "secondary", "Part I lines 4-9"),
    ("R-2210-REG", "IRS_2025_F2210_INSTR", "primary", "Part III + the penalty worksheet (§6621)"),
    ("R-2210-REG", "IRC_6654", "secondary", "§6654(a) the addition to tax"),
    ("R-2210-AI", "IRS_2025_F2210_INSTR", "primary", "Schedule AI the annualized method"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-2210-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Part I required annual payment + the $1,000 de-minimis",
     "description": "Validates R-2210-RAP. Bug it catches: the 90%/100%/110% wrong, the $1,000 de-minimis not stopping, or the smaller-of not applied.",
     "definition": {"kind": "formula_check", "form": "FORM_2210",
                    "formula": "l9 = min(0.90×current, prior×(1.10 if AGI>150k else 1.0)); l7<1000 → no penalty"},
     "sort_order": 1},
    {"assertion_id": "FA-1040-2210-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Regular Method — the §6621 penalty (7%/6% rate periods, dated accrual)",
     "description": "Validates R-2210-REG. Bug it catches: the wrong rate, the rate-period day split at 3/31/2026, or accrual not stopping at min(date cured, 4/15/2026).",
     "definition": {"kind": "formula_check", "form": "FORM_2210",
                    "formula": "penalty = Σ chunks: amount × (days@7/365×0.07 + days@6/365×0.06); days run from the installment due date to min(date cured, 2026-04-15); with due-date payments this equals Σ underpayment_i × (DAYS_7[i]/365×0.07 + DAYS_6[i]/365×0.06)"},
     "sort_order": 2},
    {"assertion_id": "FA-1040-2210-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Payments (withholding/4 on the due dates + estimates) apply earliest-first",
     "description": "Validates R-2210-REG. Bug it catches: withholding not spread on the due dates, payments not applied to the earliest underpaid installment, or the overpayment carry-forward missing.",
     "definition": {"kind": "formula_check", "form": "FORM_2210",
                    "formula": "each payment applies to the EARLIEST still-underpaid installment (date order); underpayment_at_due_i = max(0, installment_i − payments applied on or before due_i)"},
     "sort_order": 3},
    {"assertion_id": "FA-1040-2210-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "The penalty → 1040 line 38",
     "description": "Validates the flow target. Bug it catches: the §6654 penalty not landing on Form 1040 line 38.",
     "definition": {"kind": "flow_assertion", "form": "FORM_2210",
                    "checks": [{"source_line": "19", "must_write_to": ["1040.38"]}]},
     "sort_order": 4},
    {"assertion_id": "FA-1040-2210-05", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "Schedule AI — the annualized installment (smaller-of) + the applicable %",
     "description": "Validates R-2210-AI. Bug it catches: the wrong applicable % (22.5/45/67.5/90), or the smaller-of-regular not applied.",
     "definition": {"kind": "reconciliation", "form": "FORM_2210",
                    "formula": "ai_installment_i = min(max(0, ai_tax_i × pct_i − prior), l9/4); pct = [22.5,45,67.5,90]%"},
     "sort_order": 5},
    {"assertion_id": "FA-1040-2210-06", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Gates — de-minimis + prior-year safe harbor produce zero penalty",
     "description": "A balance under $1,000, or payments meeting the required annual payment, computes zero penalty (D_2210_NO_PENALTY).",
     "definition": {"kind": "gating_check", "form": "FORM_2210", "expect": {"red_fires": True},
                    "blockers": ["de_minimis", "safe_harbor"]},
     "sort_order": 6},
    {"assertion_id": "FA-1040-2210-07", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Dated payments stop accrual on the date paid (earliest-first)",
     "description": ("Validates the 2026-07-01 dated amendment to R-2210-REG. Bug it catches: a dated "
                     "payment not curing the earliest underpayment, accrual continuing past the payment "
                     "date, or a late payment silently treated as on time (P-T7 lump=217, P-T8 late Q4=5, "
                     "P-T6 due-date buckets unchanged=143)."),
     "definition": {"kind": "formula_check", "form": "FORM_2210",
                    "formula": "for each dated payment: apply to the earliest still-underpaid installment; chunk penalty = amount × days(due → min(paid, 2026-04-15)) split 7%/6% at 2026-03-31; paid ≤ due → 0 days"},
     "sort_order": 7},
]


FORMS: list[dict] = [
    {"identity": P_IDENTITY, "facts": P_FACTS, "rules": P_RULES, "lines": P_LINES,
     "diagnostics": P_DIAGNOSTICS, "scenarios": P_SCENARIOS, "rule_links": P_RULE_LINKS},
]


class Command(BaseCommand):
    help = "Load the FORM_2210 spec (Underpayment of Estimated Tax). Refuses until READY_TO_SEED=True."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad FORM_2210 spec (Underpayment of Estimated Tax)\n"))
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
                "\nREFUSING TO SEED FORM_2210: not cleared to seed.\n\n"
                "Gated until Ken's review walk (the safe-harbor + the regular-method penalty\n"
                "rate periods + Schedule AI + the §6621 rates).\n\n"
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
        form = TaxForm.objects.filter(form_number="FORM_2210").first()
        if form:
            uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
            self.stdout.write("FORM_2210: all rules cited" if not uncited
                              else self.style.WARNING(f"FORM_2210 uncited rules: {len(uncited)}"))
