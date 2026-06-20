"""Load the MINISTER spec — Minister/Clergy Housing Allowance & SE Tax (§107 / §1402).

W-2 Unit 4 (minister/clergy). A church-employed (common-law-employee) minister has
DUAL TAX STATUS: an EMPLOYEE for income tax (W-2) but SELF-EMPLOYED for SE tax on
ministerial earnings. This worksheet-style spec is NOT a single IRS form — it
reconstructs the Pub 517 net-self-employment-earnings worksheet and the §107
exclusion comparison, feeding two flow targets:
    • the §107 EXCESS housing/rental allowance → Form 1040 line 1h ("Excess allowance"),
    • the clergy net ministerial earnings → Schedule SE line 2 (the EXISTING SE engine
      then applies × 0.9235, the SS wage-base cap, ½-SE-tax → Sch 1 L15, SE tax → Sch 2 L4).

KEN'S 3 SCOPE DECISIONS (2026-06-16, AskUserQuestion):
  (1) v1 = "W-2 minister core" — cash housing allowance (§107 least-of-three + taxable
      excess), church parsonage FRV, SECA on the clergy base via Schedule SE, and a
      Form 4361 "exemption approved" flag that zeroes ministerial SE tax. RED-DEFER:
      Schedule-C ministerial side income (weddings/funerals), §265 Deason expense
      allocation to tax-free income, retired-minister housing, Form 4361 eligibility
      adjudication.
  (2) the clergy housing inputs live ON W2Income (the minister's church W-2), with a
      person-level Form-4361 election fact on Taxpayer.
  (3) include ONE preparer-entered "unreimbursed ministerial business expenses" input
      that reduces the Schedule SE clergy base (FULL amount — Pub 517: no Deason
      reduction for SE tax).

LAW VERIFIED 2026-06-16 against IRS Pub 517 (2025) + IRC §107 + §1402(a)(8)/(e) +
the Schedule SE clergy instructions:
  INCOME TAX (§107): a minister excludes the housing/parsonage allowance from gross
    income, capped at the LEAST OF (a) the amount actually used to provide a home,
    (b) the amount officially designated in advance, (c) the fair rental value of the
    home incl. furnishings + utilities. Any DESIGNATED amount over that least-of is
    taxable wages on Form 1040 line 1h with the dotted-line note "Excess allowance".
    A church-provided parsonage (in-kind) is excluded at its fair rental value.
  SE TAX (§1402(a)(8) — THE TWIST): "This exclusion applies only for income tax
    purposes. It doesn't apply for SE tax purposes." The FULL housing/rental
    allowance AND parsonage FRV are INCLUDED in net earnings from self-employment.
    A minister's W-2 wages carry NO FICA, so the entire clergy base is subject to
    SECA. Sch SE line 2 = ministerial wages + housing allowance + parsonage FRV −
    allowable unreimbursed ministerial expenses (FULL — no Deason for SE).
  FORM 4361 (§1402(e)): an approved exemption omits MINISTERIAL earnings (and their
    deductions) from net self-employment earnings entirely — no Schedule SE for the
    ministerial income. Irrevocable. Does not cover non-ministerial SE income.
  ½-SE-TAX (Sch 1 L15) is available to a minister identically to any other
    self-employed person — handled by the existing SE engine.

SAFETY GUARD: READY_TO_SEED stays False until Ken's review walk (the §107 least-of-
three; the §1402(a)(8) housing-in-SE inclusion; the Schedule-SE-line-2 feed reusing
the existing SE engine; the Form 4361 zeroing; the v1 RED-defer boundary).
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


READY_TO_SEED = True  # FLIPPED 2026-06-16 — Ken approved the review walk ("Looks good. Continue").


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_ENTITY_TYPES = ["1040"]
FORM_STATUS = "draft"

# The §1402(a)(12) net-earnings multiplier and the §1402(b)(2) SE filing floor are
# NON-INDEXED statutory constants — identical 2025 and 2026. The SS wage-base cap and
# the Additional-Medicare threshold live in the existing SE engine (Schedule SE), not
# here: this worksheet outputs the PRE-0.9235 Schedule SE line-2 amount.
SE_NET_MULTIPLIER = "0.9235"
SE_FILING_FLOOR = 400


# ═══════════════════════════════════════════════════════════════════════════
# THE MATH (the integrity gate re-types this independently; they share no math).
# ═══════════════════════════════════════════════════════════════════════════

from decimal import ROUND_HALF_UP, Decimal  # noqa: E402


def _D(x):
    return Decimal(str(x if x is not None else 0))


def _r0(x):
    return _D(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def compute_minister(wages=0, housing_allowance=0, housing_used=0, housing_frv=0,
                     parsonage_frv=0, unreimbursed_expenses=0,
                     form_4361_exempt=False) -> dict:
    """One minister (one church W-2). Produces the §107 income-tax exclusion + the
    taxable EXCESS (→ 1040 line 1h), and the clergy net ministerial earnings (→
    Schedule SE line 2, PRE-0.9235; the existing SE engine applies the multiplier,
    SS cap, ½-SE-tax, and Sch 2 routing).

    §107 least-of-three needs all three cash-allowance inputs. If a cash allowance is
    present but the amount-used OR the fair rental value is missing, the exclusion is
    NOT determined (set to 0 — conservative/taxable) and `housing_incomplete` flags it
    so the RED diagnostic owns the gap (no silently-wrong exclusion)."""
    w = _D(wages)
    ha = _D(housing_allowance)
    hu = _D(housing_used)
    hf = _D(housing_frv)
    pf = _D(parsonage_frv)
    ue = _D(unreimbursed_expenses)

    # ── Income tax: §107 least-of-three exclusion + the taxable excess ──
    housing_incomplete = ha > 0 and (hu <= 0 or hf <= 0)
    if ha <= 0:
        exclusion = _D(0)
    elif housing_incomplete:
        exclusion = _D(0)               # not determined; D_MIN_HOUSING_INC RED owns it
    else:
        exclusion = min(ha, hu, hf)
    excess = max(_D(0), ha - exclusion)  # → Form 1040 line 1h ("Excess allowance")

    # ── SE tax: §1402(a)(8) — FULL housing/parsonage INCLUDED, expenses subtracted ──
    se_line2 = max(_D(0), w + ha + pf - ue)
    if form_4361_exempt:
        se_line2 = _D(0)                 # §1402(e): ministerial earnings omitted from SE

    return {
        "line5_exclusion": _r0(exclusion),
        "line6_excess": _r0(excess),
        "line9_se_line2": _r0(se_line2),
        "housing_incomplete": housing_incomplete,
    }


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("minister_clergy_tax", "Minister/clergy taxation — §107 housing/parsonage allowance exclusion (income tax) + §1402(a)(8) SECA on wages and housing; §1402(e) Form 4361 SE-tax exemption; the Schedule SE line-2 clergy feed"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_1040_FORM",
    "IRS_2025_1040_INSTR",
]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_PUB517",
        "source_type": "official_publication",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Pub. 517 — Social Security and Other Information for Members of the Clergy and Religious Workers",
        "citation": "IRS Pub. 517 (2025), Housing/parsonage allowance; Figuring net self-employment earnings",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/publications/p517",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": False,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": (
            "The controlling IRS publication for clergy. REQUIRES HUMAN REVIEW: the worksheet line "
            "structure here is RECONSTRUCTED from the publication's narrative + worked examples (the "
            "PDF worksheet tables do not render in the HTML source) — re-check the line labels vs the "
            "2025 Pub 517 PDF worksheets. The COMPUTATION is independently math-gated. Verified from "
            "the publication: (a) §107 exclusion = least of (used / designated / FRV+utilities); "
            "(b) the housing/parsonage allowance IS included for SE tax even though excluded for income "
            "tax ('doesn't apply for SE tax purposes'); (c) excess allowance → Form 1040 line 1h with "
            "'Excess allowance'; (d) a W-2 minister's wages go to Schedule SE line 2 (no Schedule C), "
            "are not FICA-withheld, and remain subject to SE tax; (e) Form 4361 approved → omit "
            "ministerial earnings + deductions from net SE earnings."
        ),
        "topics": ["minister_clergy_tax"],
        "excerpts": [
            {
                "excerpt_label": "§107 least-of-three housing exclusion",
                "location_reference": "Pub 517 (2025), Housing Allowance",
                "excerpt_text": (
                    "A minister who is furnished a home or a rental allowance excludes the smallest of: "
                    "the amount actually used to provide a home; the amount officially designated as a "
                    "rental allowance; or the fair rental value of the home, including furnishings, plus "
                    "the cost of utilities. Any allowance more than the smallest of these is included in "
                    "income."
                ),
                "summary_text": "§107 income-tax exclusion = least of (amount used / designated / FRV+utilities); the excess is taxable.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Housing excluded for income tax but INCLUDED for SE tax",
                "location_reference": "Pub 517 (2025), Self-Employment Tax",
                "excerpt_text": (
                    "This exclusion applies only for income tax purposes. It doesn't apply for SE tax "
                    "purposes. For SE tax, net earnings from self-employment include the fair rental "
                    "value of a parsonage (including utilities) and the rental (housing) allowance "
                    "(including utilities), along with salaries and fees for ministerial services."
                ),
                "summary_text": "The full housing/rental allowance and parsonage FRV are in the SE base even though excluded from income tax.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Excess allowance → Form 1040 line 1h",
                "location_reference": "Pub 517 (2025)",
                "excerpt_text": (
                    "Include this amount in the total on Form 1040 or 1040-SR, line 1h. On the dotted "
                    "line next to line 1h, enter 'Excess allowance' and the amount."
                ),
                "summary_text": "The §107 excess (designated over the least-of) is reported on Form 1040 line 1h as 'Excess allowance'.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "W-2 minister wages → Schedule SE line 2 (no Schedule C, no FICA)",
                "location_reference": "Pub 517 (2025), Common-law employee",
                "excerpt_text": (
                    "Wages earned as a common-law employee of a church are generally subject to "
                    "self-employment tax unless an exemption is requested. Subtract any allowable "
                    "expenses from those wages, include the net amount on line 2 of Schedule SE (Form "
                    "1040), and attach an explanation. Don't complete Schedule C."
                ),
                "summary_text": "A church-employee minister's wages (net of expenses) go directly to Schedule SE line 2 — SECA, not withheld FICA.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Form 4361 approved → omit ministerial earnings from SE",
                "location_reference": "Pub 517 (2025), Exemption From SE Tax",
                "excerpt_text": (
                    "If you have an approved exemption, don't include the income or deductions from "
                    "ministerial services in figuring your net earnings from self-employment. An approved "
                    "exemption only applies to earnings you receive for ministerial services; it doesn't "
                    "apply to any other self-employment income."
                ),
                "summary_text": "An approved Form 4361 removes ministerial earnings from the SE base entirely (ministerial only).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Deason / §265 — income tax only, not SE tax",
                "location_reference": "Pub 517 (2025), Deductions allocable to tax-free income",
                "excerpt_text": (
                    "If you receive a tax-free rental or parsonage allowance, you must allocate a portion "
                    "of the otherwise deductible expenses of your ministry to that tax-free income and you "
                    "can't deduct that portion. This rule doesn't apply to home mortgage interest or real "
                    "estate taxes. Reduce your otherwise deductible expenses only in figuring your income "
                    "tax, not your SE tax."
                ),
                "summary_text": "The §265 allocation to tax-free housing reduces the INCOME-TAX deduction only; SE tax uses the full expenses. (v1 RED-defers the income-tax allocation; employee misc. expenses are suspended through 2025.)",
                "is_key_excerpt": False,
            },
        ],
    },
    {
        "source_code": "IRC_107",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §107 — Rental value of parsonages",
        "citation": "26 U.S.C. §107 (minister of the gospel housing exclusion)",
        "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:107%20edition:prelim)",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": True,
        "notes": (
            "§107(1) excludes the rental value of a home furnished as part of compensation (the in-kind "
            "parsonage); §107(2) excludes a rental allowance to the extent used to rent/provide a home, "
            "capped by the regulations at the fair rental value of the home plus utilities. The "
            "'reasonable compensation' limit is a §107/regulatory overlay (v1 = info diagnostic)."
        ),
        "topics": ["minister_clergy_tax"],
        "excerpts": [
            {
                "excerpt_label": "§107 — parsonage and rental allowance exclusion",
                "location_reference": "26 U.S.C. §107",
                "excerpt_text": (
                    "In the case of a minister of the gospel, gross income does not include (1) the rental "
                    "value of a home furnished to him as part of his compensation; or (2) the rental "
                    "allowance paid to him as part of his compensation, to the extent used by him to rent "
                    "or provide a home and to the extent such allowance does not exceed the fair rental "
                    "value of the home, including furnishings and appurtenances such as a garage, plus the "
                    "cost of utilities."
                ),
                "summary_text": "Excludes the in-kind parsonage value (§107(1)) and the rental allowance used to provide a home, capped at FRV+utilities (§107(2)).",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_1402",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §1402 — Definitions (self-employment); §1402(a)(8) clergy housing; §1402(e) exemption",
        "citation": "26 U.S.C. §1402(a)(8), §1402(c)(4), §1402(e)",
        "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:1402%20edition:prelim)",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": True,
        "notes": (
            "§1402(c)(4) makes the performance of ministerial services a trade or business (self-employment) "
            "even when the minister is a common-law employee; §1402(a)(8) adds the §107 housing/parsonage "
            "value back into net SE earnings; §1402(e) authorizes the Form 4361 exemption. §1402(a)(12) "
            "is the 0.9235 net-earnings multiplier (applied on Schedule SE by the existing engine)."
        ),
        "topics": ["minister_clergy_tax"],
        "excerpts": [
            {
                "excerpt_label": "§1402(a)(8) — housing/parsonage in net SE earnings",
                "location_reference": "26 U.S.C. §1402(a)(8)",
                "excerpt_text": (
                    "The rental value of a home furnished to a minister, or a rental allowance paid to a "
                    "minister (including the value of meals and lodging), shall be included in computing "
                    "net earnings from self-employment, notwithstanding the exclusion of such amounts from "
                    "gross income under section 107."
                ),
                "summary_text": "§1402(a)(8): the §107-excluded housing/parsonage value is added back into the SE base.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§1402(e) — Form 4361 exemption from SE tax",
                "location_reference": "26 U.S.C. §1402(e)",
                "excerpt_text": (
                    "A minister who is conscientiously opposed to, or because of religious principles "
                    "opposed to, the acceptance of public insurance may file an application for an "
                    "exemption from the tax imposed by chapter 2 with respect to services performed as a "
                    "minister. An approved exemption is irrevocable."
                ),
                "summary_text": "§1402(e): an approved Form 4361 exempts ministerial earnings from SE tax; irrevocable.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_F4361",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "Form 4361 — Application for Exemption From Self-Employment Tax for Use by Ministers, Members of Religious Orders and Christian Science Practitioners",
        "citation": "Form 4361",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f4361.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": (
            "The exemption application. Filed by the due date (incl. extensions) of the return for the "
            "SECOND tax year with $400+ net SE earnings any part of which is from ministerial services. "
            "v1 takes a preparer-asserted 'exemption approved' flag — it does NOT adjudicate eligibility "
            "(the two-year window, the conscientious-objection certification) — D_MIN_4361 reminds."
        ),
        "topics": ["minister_clergy_tax"],
        "excerpts": [
            {
                "excerpt_label": "Form 4361 — scope and irrevocability",
                "location_reference": "Form 4361, certification",
                "excerpt_text": (
                    "I certify that I am conscientiously opposed to, or because of my religious principles "
                    "I am opposed to, the acceptance (with respect to services I perform as a minister, "
                    "member of a religious order not under a vow of poverty, or a Christian Science "
                    "practitioner) of any public insurance that makes payments in the event of death, "
                    "disability, old age, or retirement; or that makes payments toward the cost of, or "
                    "provides services for, medical care."
                ),
                "summary_text": "Form 4361 exempts ministerial earnings from SE tax on conscientious/religious grounds; covers only ministerial services.",
                "is_key_excerpt": True,
            },
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_PUB517", "MINISTER", "governs"),
    ("IRC_107", "MINISTER", "governs"),
    ("IRC_1402", "MINISTER", "governs"),
    ("IRS_2025_F4361", "MINISTER", "governs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM: MINISTER
# ═══════════════════════════════════════════════════════════════════════════

N_IDENTITY = {
    "form_number": "MINISTER",
    "form_title": "Minister / Clergy Housing Allowance & SE Tax Worksheet (§107 / §1402) (TY2025)",
    "notes": (
        "W-2 Unit 4. A worksheet-style spec (NOT a single IRS form; reconstructed from Pub 517). "
        "DUAL STATUS: a church-employed minister is an income-tax EMPLOYEE (W-2) but SELF-EMPLOYED "
        "for SE tax. INCOME TAX: §107 excludes the housing/rental allowance up to the least of "
        "(used / designated / FRV+utilities); the EXCESS → Form 1040 line 1h ('Excess allowance'). "
        "SE TAX: §1402(a)(8) puts the FULL housing allowance + parsonage FRV back into the SE base; "
        "Schedule SE line 2 = ministerial wages + housing allowance + parsonage FRV − unreimbursed "
        "ministerial expenses (FULL; no Deason for SE). The EXISTING Schedule SE engine then applies "
        "× 0.9235, the SS wage-base cap, ½-SE-tax → Sch 1 L15, and SE tax → Sch 2 L4. Form 4361 "
        "(approved) zeroes the Schedule SE line-2 ministerial amount. v1 RED-DEFERS: Schedule-C "
        "ministerial side income, the §265/Deason income-tax allocation, retired-minister housing, "
        "and Form 4361 eligibility adjudication (preparer-asserted flag). Constants are non-indexed "
        "(0.9235, $400) → identical 2025/2026; the SS cap lives in the SE engine."
    ),
}

N_FACTS: list[dict] = [
    # ── Inputs (sourced from W2Income + a Taxpayer fact in the build leg) ──
    {"fact_key": "min_wages", "label": "Line 1 — ministerial wages (W-2 Box 1)",
     "data_type": "decimal", "default_value": "0", "sort_order": 1,
     "notes": "W2Income.wages of the is_minister W-2 (cash salary; the housing allowance is NOT in Box 1)."},
    {"fact_key": "min_housing_allowance", "label": "Line 2 — cash housing/rental allowance designated",
     "data_type": "decimal", "default_value": "0", "sort_order": 2,
     "notes": "W2Income clergy field. The amount the church designated/paid for housing (often noted in Box 14). Full amount is in the SE base."},
    {"fact_key": "min_housing_used", "label": "Line 3 — amount actually used to provide a home",
     "data_type": "decimal", "default_value": "0", "sort_order": 3,
     "notes": "§107 least-of-three input. W2Income clergy field."},
    {"fact_key": "min_housing_frv", "label": "Line 4 — fair rental value of home + furnishings + utilities",
     "data_type": "decimal", "default_value": "0", "sort_order": 4,
     "notes": "§107 ceiling. W2Income clergy field."},
    {"fact_key": "min_parsonage_frv", "label": "Line 7 — fair rental value of church-provided parsonage + utilities (in-kind)",
     "data_type": "decimal", "default_value": "0", "sort_order": 5,
     "notes": "§107(1) in-kind home: fully excluded for income tax, included in the SE base. W2Income clergy field (0 if none)."},
    {"fact_key": "min_unreimbursed_expenses", "label": "Line 8 — unreimbursed ministerial business expenses",
     "data_type": "decimal", "default_value": "0", "sort_order": 6,
     "notes": "Reduces the Schedule SE clergy base (FULL — Pub 517: no Deason reduction for SE tax). W2Income clergy field."},
    {"fact_key": "min_4361_exempt", "label": "Form 4361 exemption from SE tax approved?",
     "data_type": "boolean", "default_value": "false", "sort_order": 7,
     "notes": "Person-level Taxpayer fact (clergy_4361_exempt). True → ministerial earnings omitted from SE; preparer-asserted (no eligibility adjudication in v1)."},
    # ── Outputs ──
    {"fact_key": "min_housing_exclusion", "label": "Line 5 — §107 housing exclusion = least of (line 2, 3, 4)",
     "data_type": "decimal", "sort_order": 30, "notes": "OUTPUT (income tax). Substantiation; the excluded amount was never in Box 1."},
    {"fact_key": "min_excess_allowance", "label": "Line 6 — excess allowance = line 2 − line 5 → Form 1040 line 1h",
     "data_type": "decimal", "sort_order": 31, "notes": "OUTPUT (income tax). Taxable 'Excess allowance' on 1040 line 1h."},
    {"fact_key": "min_se_line2", "label": "Line 9 — clergy net ministerial earnings → Schedule SE line 2 (pre-0.9235)",
     "data_type": "decimal", "sort_order": 32, "notes": "OUTPUT (SE tax). = max(0, wages + housing allowance + parsonage FRV − expenses); 0 if Form 4361 approved. The SE engine applies × 0.9235 + the SS cap."},
]

N_RULES: list[dict] = [
    {"rule_id": "R-MIN-EXCL", "title": "Line 5 — §107 housing exclusion = least of (used, designated, FRV+utilities)", "rule_type": "calculation",
     "precedence": 1, "sort_order": 1,
     "formula": "line 5 = min(line 2 designated, line 3 used, line 4 FRV+utilities); income tax only. If line 2 > 0 and (line 3 = 0 or line 4 = 0) the exclusion is NOT determined (= 0, conservative) and D_MIN_HOUSING_INC fires.",
     "inputs": ["min_housing_allowance", "min_housing_used", "min_housing_frv"],
     "outputs": ["min_housing_exclusion"],
     "description": "§107(2): the rental allowance is excludable to the extent used to provide a home, capped at the fair rental value plus utilities."},
    {"rule_id": "R-MIN-EXCESS", "title": "Line 6 — excess allowance → Form 1040 line 1h", "rule_type": "calculation",
     "precedence": 2, "sort_order": 2,
     "formula": "line 6 = max(0, line 2 designated − line 5 exclusion) → Form 1040 line 1h ('Excess allowance').",
     "inputs": ["min_housing_allowance", "min_housing_exclusion"],
     "outputs": ["min_excess_allowance"],
     "description": "Any designated allowance over the §107 least-of-three is taxable wages on Form 1040 line 1h."},
    {"rule_id": "R-MIN-SE", "title": "Line 9 — clergy net SE earnings → Schedule SE line 2 (§1402(a)(8))", "rule_type": "calculation",
     "precedence": 3, "sort_order": 3,
     "formula": "line 9 = max(0, line 1 wages + line 2 housing allowance + line 7 parsonage FRV − line 8 expenses) → Schedule SE line 2 (pre-0.9235). FULL housing in SE; FULL expenses (no Deason for SE).",
     "inputs": ["min_wages", "min_housing_allowance", "min_parsonage_frv", "min_unreimbursed_expenses"],
     "outputs": ["min_se_line2"],
     "description": "§1402(a)(8): the §107-excluded housing/parsonage value is in net SE earnings; the existing SE engine applies × 0.9235, the SS cap, ½-SE-tax (Sch 1 L15), and SE tax (Sch 2 L4)."},
    {"rule_id": "R-MIN-4361", "title": "Form 4361 approved → Schedule SE line 2 ministerial amount = 0 (§1402(e))", "rule_type": "calculation",
     "precedence": 4, "sort_order": 4,
     "formula": "If Form 4361 exemption approved: line 9 (Schedule SE line 2) = 0 — ministerial earnings + deductions omitted from net SE earnings.",
     "inputs": ["min_4361_exempt"], "outputs": ["min_se_line2"],
     "description": "§1402(e): an approved exemption removes ministerial earnings from SE tax entirely (ministerial only; irrevocable)."},
]

N_LINES: list[dict] = [
    {"line_number": "1", "description": "Line 1 — ministerial wages (W-2 Box 1)", "line_type": "input"},
    {"line_number": "2", "description": "Line 2 — cash housing/rental allowance designated", "line_type": "input"},
    {"line_number": "3", "description": "Line 3 — amount actually used to provide a home", "line_type": "input"},
    {"line_number": "4", "description": "Line 4 — fair rental value of home + furnishings + utilities", "line_type": "input"},
    {"line_number": "5", "description": "Line 5 — §107 housing exclusion = min(2, 3, 4)", "line_type": "calculated"},
    {"line_number": "6", "description": "Line 6 — excess allowance = line 2 − line 5 → Form 1040 line 1h", "line_type": "calculated"},
    {"line_number": "7", "description": "Line 7 — parsonage FRV + utilities (in-kind, fully excluded income tax)", "line_type": "input"},
    {"line_number": "8", "description": "Line 8 — unreimbursed ministerial business expenses", "line_type": "input"},
    {"line_number": "9", "description": "Line 9 — clergy net SE earnings = line 1 + line 2 + line 7 − line 8 → Schedule SE line 2", "line_type": "total"},
    {"line_number": "f1040_1h", "description": "Form 1040 line 1h — excess allowance", "line_type": "total"},
    {"line_number": "sch_se_2", "description": "Schedule SE line 2 — clergy net ministerial earnings (pre-0.9235)", "line_type": "total"},
]

N_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_MIN_HOUSING_INC", "title": "Housing allowance present but the §107 inputs are incomplete", "severity": "error",
     "condition": "min_housing_allowance > 0 AND (min_housing_used <= 0 OR min_housing_frv <= 0)",
     "message": ("A clergy housing/rental allowance is present, but the amount actually used to provide a "
                 "home and/or the fair rental value (incl. utilities) is missing. The §107 exclusion is "
                 "the LEAST of (amount designated, amount used, fair rental value), so it can't be "
                 "determined — the allowance is treated as fully taxable until you complete both inputs."),
     "notes": "§107(2) / Pub 517. The exclusion is NOT computed (set to 0, conservative) until all three are entered — no silently-wrong exclusion."},
    {"diagnostic_id": "D_MIN_EXCESS", "title": "Excess housing allowance → Form 1040 line 1h", "severity": "info",
     "condition": "min_excess_allowance > 0",
     "message": ("The designated housing/rental allowance exceeds the §107 limit (least of designated, "
                 "used, fair rental value). The excess is taxable and is reported on Form 1040 line 1h "
                 "with the dotted-line note 'Excess allowance'."),
     "notes": "Pub 517 — excess allowance → 1040 line 1h."},
    {"diagnostic_id": "D_MIN_4361", "title": "Form 4361 exemption applied — ministerial earnings excluded from SE tax", "severity": "warning",
     "condition": "min_4361_exempt is True",
     "message": ("An approved Form 4361 exemption is applied: ministerial wages and the housing/parsonage "
                 "allowance are excluded from self-employment tax. Confirm the IRS-approved Form 4361 is "
                 "on file — the exemption is irrevocable and applies only to ministerial earnings (other "
                 "self-employment income is still subject to SE tax)."),
     "notes": "§1402(e). v1 is preparer-asserted; no eligibility adjudication (the two-year window)."},
    {"diagnostic_id": "D_MIN_SECA", "title": "Clergy wages are subject to SE tax (SECA), not FICA", "severity": "info",
     "condition": "min_se_line2 > 0 (no Form 4361 exemption)",
     "message": ("This minister's W-2 wages plus the housing/parsonage allowance are subject to "
                 "self-employment tax (SECA) on Schedule SE — even though they appear on a W-2 — because "
                 "ministerial wages are not subject to Social Security/Medicare (FICA) withholding."),
     "notes": "§1402(c)(4)/§3121(b)(8). Reassures the preparer that the W-2 → Schedule SE flow is correct."},
    {"diagnostic_id": "D_MIN_REASONABLE", "title": "Housing exclusion limited to reasonable compensation", "severity": "info",
     "condition": "min_housing_exclusion > 0 OR min_parsonage_frv > 0",
     "message": ("The §107 housing/parsonage exclusion is also limited to reasonable compensation for "
                 "ministerial services. Verify the designated allowance is reasonable for the duties "
                 "performed — v1 does not test the reasonable-compensation limit."),
     "notes": "§107 / Treas. Reg. 1.107-1. v1 = preparer responsibility."},
    {"diagnostic_id": "D_MIN_DEASON", "title": "Unreimbursed expenses with tax-free housing — §265 allocation (income tax only)", "severity": "info",
     "condition": "min_unreimbursed_expenses > 0 AND (min_housing_exclusion > 0 OR min_parsonage_frv > 0)",
     "message": ("Unreimbursed ministerial expenses are present with a tax-free housing allowance. The "
                 "full expenses reduce the Schedule SE base (correct for SE tax). For INCOME tax, the "
                 "§265 (Deason) rule would disallow the portion allocable to the tax-free allowance — "
                 "not modeled in v1 (and unreimbursed employee expenses are not itemizable through 2025). "
                 "Schedule-C ministerial side income + the Deason allocation are deferred."),
     "notes": "§265 / Deason. Income tax only; SE uses full expenses. v1 RED-defers the income-tax allocation + Schedule-C side income."},
]

N_SCENARIOS: list[dict] = [
    {"scenario_name": "MIN-T1 — normal (exclusion fully used, no excess)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "wages": 40000, "housing_allowance": 20000, "housing_used": 20000, "housing_frv": 22000},
     "expected_outputs": {"min_housing_exclusion": 20000, "min_excess_allowance": 0, "min_se_line2": 60000},
     "notes": "excl = min(20k,20k,22k) = 20,000; excess 0; SE line 2 = 40k + 20k = 60,000. D_MIN_SECA/REASONABLE info."},
    {"scenario_name": "MIN-T2 — excess allowance (designated over the limit)", "scenario_type": "edge_case", "sort_order": 2,
     "inputs": {"tax_year": 2025, "wages": 40000, "housing_allowance": 25000, "housing_used": 20000, "housing_frv": 22000},
     "expected_outputs": {"min_housing_exclusion": 20000, "min_excess_allowance": 5000, "min_se_line2": 65000, "D_MIN_EXCESS": True},
     "notes": "excl = min(25k,20k,22k) = 20,000; excess = 25k − 20k = 5,000 → 1040 1h; SE line 2 = 40k + 25k = 65,000 (FULL allowance)."},
    {"scenario_name": "MIN-T3 — in-kind parsonage (no cash allowance)", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"tax_year": 2025, "wages": 35000, "parsonage_frv": 18000},
     "expected_outputs": {"min_housing_exclusion": 0, "min_excess_allowance": 0, "min_se_line2": 53000},
     "notes": "parsonage fully excluded income tax; SE line 2 = 35k + 18k = 53,000."},
    {"scenario_name": "MIN-T4 — Form 4361 exemption (no ministerial SE)", "scenario_type": "edge_case", "sort_order": 4,
     "inputs": {"tax_year": 2025, "wages": 40000, "housing_allowance": 20000, "housing_used": 20000, "housing_frv": 25000, "form_4361_exempt": True},
     "expected_outputs": {"min_housing_exclusion": 20000, "min_excess_allowance": 0, "min_se_line2": 0, "D_MIN_4361": True},
     "notes": "income-tax exclusion still applies (20,000); SE line 2 = 0 (ministerial earnings omitted). D_MIN_4361 warning."},
    {"scenario_name": "MIN-T5 — unreimbursed expenses reduce the SE base", "scenario_type": "edge_case", "sort_order": 5,
     "inputs": {"tax_year": 2025, "wages": 50000, "housing_allowance": 24000, "housing_used": 24000, "housing_frv": 26000, "unreimbursed_expenses": 4000},
     "expected_outputs": {"min_housing_exclusion": 24000, "min_excess_allowance": 0, "min_se_line2": 70000, "D_MIN_DEASON": True},
     "notes": "excl 24,000; SE line 2 = 50k + 24k − 4k = 70,000 (full expenses for SE). D_MIN_DEASON info (income-tax allocation deferred)."},
    {"scenario_name": "MIN-T6 — incomplete housing inputs (RED)", "scenario_type": "diagnostic", "sort_order": 6,
     "inputs": {"tax_year": 2025, "wages": 40000, "housing_allowance": 18000, "housing_used": 0, "housing_frv": 0},
     "expected_outputs": {"min_housing_exclusion": 0, "min_excess_allowance": 18000, "min_se_line2": 58000, "D_MIN_HOUSING_INC": True},
     "notes": "used/FRV missing → exclusion NOT determined (0, conservative → all taxable); SE line 2 = 40k + 18k = 58,000. D_MIN_HOUSING_INC RED."},
]

N_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-MIN-EXCL", "IRC_107", "primary", "§107(2) rental allowance exclusion capped at FRV+utilities"),
    ("R-MIN-EXCL", "IRS_2025_PUB517", "secondary", "Least-of-three housing exclusion"),
    ("R-MIN-EXCESS", "IRS_2025_PUB517", "primary", "Excess allowance → Form 1040 line 1h"),
    ("R-MIN-SE", "IRC_1402", "primary", "§1402(a)(8) housing/parsonage in net SE earnings"),
    ("R-MIN-SE", "IRS_2025_PUB517", "secondary", "Schedule SE line 2 clergy feed (no Schedule C)"),
    ("R-MIN-4361", "IRC_1402", "primary", "§1402(e) Form 4361 exemption"),
    ("R-MIN-4361", "IRS_2025_F4361", "secondary", "Form 4361 application — ministerial only, irrevocable"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-MIN-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "§107 exclusion = least of (designated, used, FRV+utilities)",
     "description": "Validates R-MIN-EXCL. Bug it catches: the exclusion taken as the designated amount (or any single input) instead of the least of the three — over-excluding housing from income.",
     "definition": {"kind": "formula_check", "form": "MINISTER",
                    "formula": "line5 = min(line2, line3, line4) (income-tax exclusion)"},
     "sort_order": 1},
    {"assertion_id": "FA-1040-MIN-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Excess allowance (line 6) → Form 1040 line 1h",
     "description": "Validates R-MIN-EXCESS + the flow target. Bug it catches: the excess not added to taxable income (1040 line 1h), or computed as a negative.",
     "definition": {"kind": "flow_assertion", "form": "MINISTER",
                    "checks": [{"source_line": "6", "must_write_to": ["1040.1h"]}]},
     "sort_order": 2},
    {"assertion_id": "FA-1040-MIN-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Clergy SE base (line 9) = wages + housing + parsonage − expenses → Schedule SE line 2",
     "description": "Validates R-MIN-SE — §1402(a)(8). Bug it catches: the housing allowance/parsonage left OUT of the SE base (the most common clergy error), or routed through Schedule C, or the income-tax exclusion wrongly applied to SE.",
     "definition": {"kind": "flow_assertion", "form": "MINISTER",
                    "checks": [{"source_line": "9", "must_write_to": ["SCH_SE.2"]}]},
     "sort_order": 3},
    {"assertion_id": "FA-1040-MIN-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Form 4361 approved → Schedule SE line 2 ministerial amount = 0",
     "description": "Validates R-MIN-4361 — §1402(e). Bug it catches: SE tax still computed on ministerial earnings despite an approved exemption.",
     "definition": {"kind": "formula_check", "form": "MINISTER",
                    "formula": "min_4361_exempt → line9 = 0"},
     "sort_order": 4},
    {"assertion_id": "FA-1040-MIN-05", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "Outputs are floored (exclusion, excess, SE base all ≥ 0)",
     "description": "Validates the floors. Bug it catches: a negative excess (designated < exclusion never happens), or expenses driving the SE base negative instead of to 0.",
     "definition": {"kind": "reconciliation", "form": "MINISTER",
                    "formula": "line5 >= 0 and line6 == max(0, line2 - line5) and line9 == max(0, line1 + line2 + line7 - line8) (or 0 if exempt)"},
     "sort_order": 5},
    {"assertion_id": "FA-1040-MIN-06", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Gate — incomplete §107 inputs fire the RED",
     "description": "A housing allowance with a missing amount-used or fair rental value fires D_MIN_HOUSING_INC and the exclusion is not determined (treated as fully taxable) — no silently-wrong exclusion.",
     "definition": {"kind": "gating_check", "form": "MINISTER", "expect": {"red_fires": True},
                    "blockers": ["housing_incomplete"]},
     "sort_order": 6},
]


FORMS: list[dict] = [
    {"identity": N_IDENTITY, "facts": N_FACTS, "rules": N_RULES, "lines": N_LINES,
     "diagnostics": N_DIAGNOSTICS, "scenarios": N_SCENARIOS, "rule_links": N_RULE_LINKS},
]


class Command(BaseCommand):
    help = "Load the MINISTER spec (Minister/Clergy Housing Allowance & SE Tax). Refuses until READY_TO_SEED=True."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad MINISTER spec (Minister/Clergy Housing Allowance & SE Tax)\n"))
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
                "\nREFUSING TO SEED MINISTER: not cleared to seed.\n\n"
                "Gated until Ken's review walk (the §107 least-of-three; the §1402(a)(8)\n"
                "housing-in-SE inclusion; the Schedule-SE-line-2 feed; the Form 4361 zeroing;\n"
                "the v1 RED-defer boundary).\n\n"
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
        form = TaxForm.objects.filter(form_number="MINISTER").first()
        if form:
            uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
            self.stdout.write("MINISTER: all rules cited" if not uncited
                              else self.style.WARNING(f"MINISTER uncited rules: {len(uncited)}"))
