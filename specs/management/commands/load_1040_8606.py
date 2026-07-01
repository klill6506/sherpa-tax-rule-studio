"""Load the FORM_8606 spec — Nondeductible IRAs (§408(d) + §408A), all 3 parts.

Phase 2, fourth common form. Per owner (taxpayer + spouse each file their own).
Ken's 3 scope decisions (2026-06-15): ALL THREE PARTS; a per-owner Form8606
sub-model; the 8606 supersedes the 1099-R box-2a on 1040 line 4b.

  Part I  — nondeductible traditional IRA + the §408(d) pro-rata rule → line 15c
            (taxable distribution) → 1040 line 4b; line 14 = basis carryforward.
  Part II — Roth conversions → line 18 (taxable) → 1040 line 4b.
  Part III— nonqualified Roth distributions (§408A(d)(4) ordering) → line 25c → 4b.

LAW VERIFIED 2026-06-15 (brief tts-tax-app server/specs/_8606_source_brief.md):
  pro-rata ratio = line 5 basis / (year-end + distributions + conversions), capped
  at 1.0; nontaxable conversion = conv × ratio; nontaxable distribution = dist ×
  ratio; basis carryforward = total basis − nontaxable; Part III taxable = max(0,
  roth_dist − contribution_basis − conversion_basis). 2025 IRA limit $7,000/$8,000.

SAFETY GUARD: READY_TO_SEED stays False until Ken's review walk (the pro-rata + the
Roth ordering + the 1099-R box-2a supersession + the line-17 simplification).
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

IRA_LIMIT = {2025: 7000, 2026: 7000}            # base (under 50)
IRA_LIMIT_50 = {2025: 8000, 2026: 8000}         # age 50+


# ═══════════════════════════════════════════════════════════════════════════
# THE MATH (the integrity gate re-types this independently; they share no math).
# ═══════════════════════════════════════════════════════════════════════════

from decimal import ROUND_HALF_UP, Decimal  # noqa: E402


def _D(x):
    return Decimal(str(x if x is not None else 0))


def _r0(x):
    return int(_D(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def part_i(nondeduct, prior_basis, contrib_jan_apr, year_end, distributions, conversions) -> dict:
    """§408(d) pro-rata. Returns the key lines incl. l14 (basis cfwd) + l15c (taxable
    distribution) + l11 (nontaxable conversion, used by Part II)."""
    l3 = _D(nondeduct) + _D(prior_basis)
    l5 = l3 - _D(contrib_jan_apr)
    l7, l8 = _D(distributions), _D(conversions)
    l9 = _D(year_end) + l7 + l8
    if l9 <= 0:
        l10 = Decimal("0")
    else:
        l10 = min(Decimal("1"), (l5 / l9))
    l11 = _D(_r0(l8 * l10))            # nontaxable conversion
    l12 = _D(_r0(l7 * l10))            # nontaxable distribution
    l13 = l11 + l12
    l14 = l3 - l13                     # basis carryforward
    l15c = l7 - l12                    # taxable distribution → 4b
    return {"l3": l3, "l5": l5, "l10": l10, "l11": l11, "l12": l12,
            "l13": l13, "l14": l14, "l15c": l15c}


def part_ii(conversions, nontaxable_conversion) -> Decimal:
    """Taxable Roth conversion = line 16 (conversions) − line 17 (line 11 basis)."""
    return max(Decimal("0"), _D(conversions) - _D(nontaxable_conversion))


def part_iii(roth_distributions, homebuyer, contribution_basis, conversion_basis) -> Decimal:
    """§408A(d)(4) ordering — taxable = max(0, dist − contribution basis − conversion
    basis) (contributions first, then conversions, then taxable earnings)."""
    l21 = max(Decimal("0"), _D(roth_distributions) - _D(homebuyer))
    l23 = max(Decimal("0"), l21 - _D(contribution_basis))
    return max(Decimal("0"), l23 - _D(conversion_basis))


def compute_8606(nondeduct=0, prior_basis=0, contrib_jan_apr=0, year_end=0, distributions=0,
                 conversions=0, roth_distributions=0, homebuyer=0, contribution_basis=0,
                 conversion_basis=0) -> dict:
    """Full per-owner 8606. Returns l14 / l15c / l18 / l25c + the 4b contribution."""
    p1 = part_i(nondeduct, prior_basis, contrib_jan_apr, year_end, distributions, conversions)
    l18 = part_ii(conversions, p1["l11"])
    l25c = part_iii(roth_distributions, homebuyer, contribution_basis, conversion_basis)
    line_4b = p1["l15c"] + l18 + l25c
    return {"l14": p1["l14"], "l15c": p1["l15c"], "l18": l18, "l25c": l25c, "line_4b": line_4b}


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("nondeductible_ira", "Nondeductible IRAs (§408(d) pro-rata basis recovery + §408A Roth conversions/distributions) — Form 8606 → 1040 line 4b"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_1040_FORM",
    "IRS_2025_1040_INSTR",
]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_F8606_INSTR",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Form 8606 — Nondeductible IRAs",
        "citation": "Instructions for Form 8606 (2025), Parts I, II, III",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/instructions/i8606",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": "Part I pro-rata (lines 5-15c), Part II line 17 = the line-11 basis (the IRS 'line 2 + pre-conversion line 1' plain-language form equals line 11 in the no-other-IRA backdoor case — WALK ITEM), Part III §408A ordering. RED-deferred: qualified-disaster (15b), outstanding rollovers (line 6), recharacterizations, inherited-IRA basis.",
        "topics": ["nondeductible_ira"],
        "excerpts": [
            {
                "excerpt_label": "Part I — the pro-rata calculation (lines 5-15c)",
                "location_reference": "i8606 (2025), Part I",
                "excerpt_text": (
                    "Line 5 is your basis (line 3 minus line 4). Line 6 is the total value of all your "
                    "traditional, SEP, and SIMPLE IRAs as of December 31, 2025. Line 9 = line 6 + line 7 "
                    "(distributions) + line 8 (conversions). Line 10 = line 5 divided by line 9. Line 11 = line "
                    "8 x line 10 (nontaxable conversion). Line 12 = line 7 x line 10 (nontaxable distribution). "
                    "Line 14 = line 3 minus line 13 (your basis carryforward). Line 15c (line 15a minus 15b) is "
                    "the taxable amount; include it on Form 1040, line 4b."
                ),
                "summary_text": "Pro-rata: nontaxable% = basis / (year-end + distributions + conversions); taxable distribution = line 7 − line 12 → 4b; basis carries forward on line 14.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part II Roth conversion + Part III Roth distribution",
                "location_reference": "i8606 (2025), Parts II and III",
                "excerpt_text": (
                    "Part II: line 16 is the amount you converted, line 17 is your basis in that amount (line "
                    "11), and line 18 (line 16 minus line 17) is the taxable conversion — include it on Form "
                    "1040, line 4b. Part III: nonqualified Roth distributions come out first as your regular "
                    "contributions (line 22, tax-free), then your conversions (line 24), then earnings; line "
                    "25c is the taxable amount on Form 1040, line 4b."
                ),
                "summary_text": "Part II taxable conversion = line 16 − line 11 → 4b. Part III taxable = max(0, dist − contribution basis − conversion basis) → 4b.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_408D",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §408(d) — Tax Treatment of IRA Distributions (the pro-rata / aggregation rule)",
        "citation": "26 U.S.C. §408(d)(1)-(2) (distributions; the aggregation + basis pro-rata rule)",
        "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:408%20edition:prelim)",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "§408(d)(2): all traditional/SEP/SIMPLE IRAs are aggregated; the nontaxable part of any distribution is the basis times the ratio of the distribution to the total balance.",
        "topics": ["nondeductible_ira"],
        "excerpts": [
            {
                "excerpt_label": "§408(d)(1)-(2) the aggregation + pro-rata rule",
                "location_reference": "26 U.S.C. §408(d)(1)-(2)",
                "excerpt_text": (
                    "Any amount distributed out of an individual retirement plan shall be included in gross "
                    "income by the payee. For purposes of applying the basis-recovery rule, all individual "
                    "retirement plans are treated as one contract, all distributions during the taxable year as "
                    "one distribution, and the value of the contract computed as of the close of the year."
                ),
                "summary_text": "All IRAs are one contract; the nontaxable part of a distribution is basis prorated over the total year-end value.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_408A",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §408A — Roth IRAs (conversions + the distribution ordering rules)",
        "citation": "26 U.S.C. §408A(d)(3)-(4) (conversion income; the contributions-then-conversions-then-earnings ordering)",
        "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:408A%20edition:prelim)",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "§408A(d)(3) a conversion is taxable except for basis; §408A(d)(4) nonqualified Roth distributions come out contributions first, then conversions, then taxable earnings.",
        "topics": ["nondeductible_ira"],
        "excerpts": [
            {
                "excerpt_label": "§408A(d)(4) the Roth distribution ordering",
                "location_reference": "26 U.S.C. §408A(d)(4)",
                "excerpt_text": (
                    "Any amount distributed from a Roth IRA is treated as made first from regular contributions, "
                    "then from conversion contributions (on a first-in-first-out basis), and finally from "
                    "earnings. Only the earnings portion of a nonqualified distribution is includible in income."
                ),
                "summary_text": "Roth distributions: contributions (tax-free), then conversions, then earnings (taxable if nonqualified).",
                "is_key_excerpt": True,
            },
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_F8606_INSTR", "FORM_8606", "governs"),
    ("IRC_408D", "FORM_8606", "governs"),
    ("IRC_408A", "FORM_8606", "governs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM: FORM_8606
# ═══════════════════════════════════════════════════════════════════════════

F_IDENTITY = {
    "form_number": "FORM_8606",
    "form_title": "Form 8606 Nondeductible IRAs (§408(d) + §408A) (TY2025)",
    "notes": (
        "Ken's 3 scope decisions 2026-06-15. A per-owner sub-model (taxpayer + spouse "
        "each file their own; independent basis). Part I §408(d) pro-rata: nontaxable "
        "% = basis / (year-end + distributions + conversions); taxable distribution "
        "(line 15c) → 1040 line 4b; basis carryforward (line 14). Part II Roth "
        "conversions (line 18 = line 16 − the line-11 pro-rata basis) → 4b. Part III "
        "nonqualified Roth distributions (§408A ordering: contributions, then "
        "conversions, then earnings; line 25c) → 4b. The 8606 owner-with-basis taxable "
        "amount SUPERSEDES the 1099-R box-2a on line 4b (the Simplified Method "
        "precedent). RED-deferred: disaster distributions, outstanding rollovers, "
        "recharacterizations, inherited-IRA basis."
    ),
}

F_FACTS: list[dict] = [
    {"fact_key": "f8606_owner", "label": "Owner (taxpayer / spouse)",
     "data_type": "string", "default_value": "taxpayer", "sort_order": 1, "notes": "Per-owner 8606."},
    # ── Part I ──
    {"fact_key": "f8606_nondeductible_contrib", "label": "Nondeductible traditional IRA contributions (line 1)",
     "data_type": "decimal", "default_value": "0", "sort_order": 2, "notes": "2025 nondeductible contributions."},
    {"fact_key": "f8606_prior_basis", "label": "Basis carryforward from prior years (line 2)",
     "data_type": "decimal", "default_value": "0", "sort_order": 3, "notes": "Line 14 of the last 8606."},
    {"fact_key": "f8606_contrib_jan_apr", "label": "Contributions made Jan 1-Apr 15 2026 for 2025 (line 4)",
     "data_type": "decimal", "default_value": "0", "sort_order": 4, "notes": "Reduces the pro-rata basis (line 5)."},
    {"fact_key": "f8606_year_end_value", "label": "Year-end value of all trad/SEP/SIMPLE IRAs (line 6)",
     "data_type": "decimal", "default_value": "0", "sort_order": 5, "notes": "12/31/2025 total. Pro-rata denominator."},
    {"fact_key": "f8606_distributions", "label": "Traditional IRA distributions in 2025 (line 7)",
     "data_type": "decimal", "default_value": "0", "sort_order": 6, "notes": "Not counting conversions/rollovers/QCDs."},
    {"fact_key": "f8606_conversions", "label": "Amount converted to Roth in 2025 (line 8)",
     "data_type": "decimal", "default_value": "0", "sort_order": 7, "notes": "Part I line 8 = Part II line 16."},
    # ── Part III ──
    {"fact_key": "f8606_roth_distributions", "label": "Nonqualified Roth IRA distributions (line 19)",
     "data_type": "decimal", "default_value": "0", "sort_order": 8, "notes": "Part III."},
    {"fact_key": "f8606_roth_homebuyer", "label": "Qualified first-time homebuyer Roth amount (line 20)",
     "data_type": "decimal", "default_value": "0", "sort_order": 9, "notes": "Reduces the Part III taxable base."},
    {"fact_key": "f8606_roth_contribution_basis", "label": "Basis in Roth contributions (line 22)",
     "data_type": "decimal", "default_value": "0", "sort_order": 10, "notes": "Regular Roth contributions 1998-2025."},
    {"fact_key": "f8606_roth_conversion_basis", "label": "Basis in Roth conversions (line 24)",
     "data_type": "decimal", "default_value": "0", "sort_order": 11, "notes": "Historical conversions/rollovers."},
    {"fact_key": "f8606_age_50_plus", "label": "Age 50+ (the $8,000 contribution limit)?",
     "data_type": "boolean", "default_value": "false", "sort_order": 12, "notes": "D_8606_OVERCONTRIB threshold."},
    # ── Roth basis tracker (year-over-year; feeds line 22/24) ──
    {"fact_key": "f8606_roth_cy_contributions", "label": "Current-year regular Roth IRA contributions (basis tracker)",
     "data_type": "decimal", "default_value": "0", "sort_order": 13,
     "notes": ("Roth basis tracker field (NOT a current-year 8606 line). A regular Roth contribution does not "
               "require an 8606, so it is recorded on the per-owner Roth basis tracker; the proforma roll adds it "
               "to next year's line-22 contribution basis so Part III (§408A(d)(4)) is correct when a "
               "distribution later occurs.")},
    # ── Outputs ──
    {"fact_key": "f8606_line14", "label": "Basis carryforward to 2026 (line 14)",
     "data_type": "decimal", "sort_order": 30, "notes": "OUTPUT."},
    {"fact_key": "f8606_line15c", "label": "Taxable IRA distribution (line 15c) → 1040 line 4b",
     "data_type": "decimal", "sort_order": 31, "notes": "OUTPUT. Part I."},
    {"fact_key": "f8606_line18", "label": "Taxable Roth conversion (line 18) → 1040 line 4b",
     "data_type": "decimal", "sort_order": 32, "notes": "OUTPUT. Part II."},
    {"fact_key": "f8606_line25c", "label": "Taxable nonqualified Roth distribution (line 25c) → 1040 line 4b",
     "data_type": "decimal", "sort_order": 33, "notes": "OUTPUT. Part III."},
]

F_RULES: list[dict] = [
    {"rule_id": "R-8606-PART1", "title": "Part I — §408(d) pro-rata basis recovery", "rule_type": "calculation",
     "precedence": 1, "sort_order": 1,
     "formula": ("l3 = nondeductible + prior_basis; l5 = l3 − contrib_jan_apr; l9 = year_end + "
                 "distributions + conversions; l10 = min(1, l5/l9); l11 = round(conversions×l10); l12 = "
                 "round(distributions×l10); l14 = l3 − (l11+l12); l15c = distributions − l12 → 1040 4b."),
     "inputs": ["f8606_nondeductible_contrib", "f8606_prior_basis", "f8606_contrib_jan_apr",
                "f8606_year_end_value", "f8606_distributions", "f8606_conversions"],
     "outputs": ["f8606_line14", "f8606_line15c"],
     "description": "The §408(d) aggregation + pro-rata. All IRAs are one contract."},
    {"rule_id": "R-8606-PART2", "title": "Part II — taxable Roth conversion", "rule_type": "calculation",
     "precedence": 2, "sort_order": 2,
     "formula": "l16 = conversions; l17 = l11 (the pro-rata nontaxable conversion); l18 = max(0, l16 − l17) → 1040 4b.",
     "inputs": ["f8606_conversions"], "outputs": ["f8606_line18"],
     "description": "§408A(d)(3). Backdoor Roth (basis == conversion, no other IRA) → l18 = 0."},
    {"rule_id": "R-8606-PART3", "title": "Part III — nonqualified Roth distribution ordering", "rule_type": "calculation",
     "precedence": 3, "sort_order": 3,
     "formula": ("l21 = roth_dist − homebuyer; l23 = max(0, l21 − contribution_basis); l25c = max(0, l23 "
                 "− conversion_basis) → 1040 4b. Contributions first, then conversions, then earnings."),
     "inputs": ["f8606_roth_distributions", "f8606_roth_homebuyer", "f8606_roth_contribution_basis",
                "f8606_roth_conversion_basis"],
     "outputs": ["f8606_line25c"],
     "description": "§408A(d)(4) the Roth distribution ordering."},
    {"rule_id": "R-8606-4B", "title": "Per-owner 4b — supersede the 1099-R box-2a", "rule_type": "routing",
     "precedence": 4, "sort_order": 4,
     "formula": ("The per-owner 1040 line 4b contribution = line 15c + line 18 + line 25c. When an owner "
                 "has 8606 basis, this SUPERSEDES the 1099-R box-2a taxable amount on line 4b (the gross "
                 "4a still sums); the Simplified Method precedent."),
     "inputs": ["f8606_line15c", "f8606_line18", "f8606_line25c"], "outputs": [],
     "description": "The 1099-R coupling (Ken Decision 3)."},
    {"rule_id": "R-8606-ROTHTRACK", "title": "Roth basis tracker — sources line 22/24 + the year-over-year roll",
     "rule_type": "routing", "precedence": 5, "sort_order": 5,
     "formula": ("Line 22 (Roth contribution basis) and line 24 (Roth conversion basis) are SOURCED from the "
                 "per-owner Roth IRA basis tracker (the opening carryforward account — YELLOW), overridable by "
                 "direct entry (GREEN). Year-over-year roll (proforma producer): a distribution recovers "
                 "contribution basis FIRST, tax-free, so next-year line 22 = max(0, line 22 − line 21) + "
                 "current-year Roth contributions (f8606_roth_cy_contributions), where line 21 = roth_distributions "
                 "− homebuyer; next-year line 24 = max(0, line 24 − max(0, line 21 − line 22)) + this year's "
                 "conversions (line 8). Regular Roth contributions need no 8606, so the tracker is the only home "
                 "that keeps Part III (§408A(d)(4) ordering) correct across no-distribution years."),
     "inputs": ["f8606_roth_cy_contributions", "f8606_conversions", "f8606_roth_distributions", "f8606_roth_homebuyer"],
     "outputs": ["f8606_roth_contribution_basis", "f8606_roth_conversion_basis"],
     "description": "The Roth basis tracker feeder + proforma roll (records-keeping for the §408A(d)(4) ordering)."},
]

F_LINES: list[dict] = [
    {"line_number": "l1", "description": "Line 1 — nondeductible traditional IRA contributions", "line_type": "input"},
    {"line_number": "l2", "description": "Line 2 — basis carryforward from prior years", "line_type": "input"},
    {"line_number": "l3", "description": "Line 3 — line 1 + line 2", "line_type": "calculated"},
    {"line_number": "l5", "description": "Line 5 — basis for the pro-rata (line 3 − line 4)", "line_type": "calculated"},
    {"line_number": "l6", "description": "Line 6 — year-end value of all trad/SEP/SIMPLE IRAs", "line_type": "input"},
    {"line_number": "l7", "description": "Line 7 — traditional IRA distributions", "line_type": "input"},
    {"line_number": "l8", "description": "Line 8 — amount converted to Roth", "line_type": "input"},
    {"line_number": "l9", "description": "Line 9 — line 6 + line 7 + line 8", "line_type": "calculated"},
    {"line_number": "l10", "description": "Line 10 — pro-rata nontaxable ratio (line 5 / line 9)", "line_type": "calculated"},
    {"line_number": "l11", "description": "Line 11 — nontaxable conversion (line 8 × line 10)", "line_type": "calculated"},
    {"line_number": "l12", "description": "Line 12 — nontaxable distribution (line 7 × line 10)", "line_type": "calculated"},
    {"line_number": "l13", "description": "Line 13 — line 11 + line 12", "line_type": "calculated"},
    {"line_number": "l14", "description": "Line 14 — basis carryforward to 2026 (line 3 − line 13)", "line_type": "total"},
    {"line_number": "l15c", "description": "Line 15c — taxable distribution → 1040 line 4b", "line_type": "total"},
    {"line_number": "l16", "description": "Line 16 — amount converted (= line 8)", "line_type": "calculated"},
    {"line_number": "l17", "description": "Line 17 — basis in the converted amount (= line 11)", "line_type": "calculated"},
    {"line_number": "l18", "description": "Line 18 — taxable Roth conversion → 1040 line 4b", "line_type": "total"},
    {"line_number": "l19", "description": "Line 19 — nonqualified Roth distributions", "line_type": "input"},
    {"line_number": "l22", "description": "Line 22 — basis in Roth contributions", "line_type": "input"},
    {"line_number": "l24", "description": "Line 24 — basis in Roth conversions", "line_type": "input"},
    {"line_number": "l25c", "description": "Line 25c — taxable nonqualified Roth distribution → 1040 line 4b", "line_type": "total"},
    {"line_number": "line_4b", "description": "Per-owner 1040 line 4b (l15c + l18 + l25c)", "line_type": "total"},
]

F_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_8606_OVERCONTRIB", "title": "Nondeductible contribution over the IRA limit", "severity": "warning",
     "condition": "f8606_nondeductible_contrib > $7,000 ($8,000 if age 50+)",
     "message": ("The nondeductible traditional IRA contribution exceeds the annual limit ($7,000, or $8,000 "
                 "if age 50 or older for 2025). An excess contribution is subject to a 6% excise tax (Form "
                 "5329 Part III) — withdraw the excess or report the excise manually."),
     "notes": "§219(b). The 6% excise is not computed."},
    {"diagnostic_id": "D_8606_NO_YEAREND", "title": "Distribution/conversion present but year-end IRA value missing", "severity": "warning",
     "condition": "(distributions > 0 OR conversions > 0) AND year_end_value == 0 AND basis > 0",
     "message": ("A traditional IRA distribution or conversion is present with IRA basis, but the year-end "
                 "value of all traditional/SEP/SIMPLE IRAs (line 6) is blank. The §408(d) pro-rata rule needs "
                 "it — a blank line 6 overstates the nontaxable part. Enter the 12/31 total value."),
     "notes": "No silent gap — the pro-rata denominator."},
    {"diagnostic_id": "D_8606_BACKDOOR", "title": "Backdoor Roth — nondeductible contribution + same-year conversion", "severity": "info",
     "condition": "f8606_nondeductible_contrib > 0 AND f8606_conversions > 0",
     "message": ("A nondeductible contribution plus a same-year conversion is a 'backdoor Roth.' With no other "
                 "pre-tax IRA balance the conversion is fully nontaxable (line 18 = 0); any other pre-tax IRA "
                 "balance makes part of it taxable under the pro-rata rule."),
     "notes": "The common backdoor case."},
    {"diagnostic_id": "D_8606_SUPERSEDE", "title": "8606 taxable amount replaced the 1099-R box 2a on line 4b", "severity": "info",
     "condition": "the owner has 8606 basis and an IRA distribution",
     "message": ("Because this owner has IRA basis, Form 8606's pro-rata taxable amount (not the 1099-R box "
                 "2a) determines the taxable portion on Form 1040 line 4b. The gross (line 4a) still reflects "
                 "the full 1099-R distribution."),
     "notes": "The 1099-R coupling (Decision 3)."},
    {"diagnostic_id": "D_8606_PART3", "title": "Nonqualified Roth distribution — earnings taxable (+ possible 10%)", "severity": "info",
     "condition": "f8606_line25c > 0",
     "message": ("A nonqualified Roth IRA distribution includes taxable earnings (line 25c → Form 1040 line "
                 "4b). The earnings may also be subject to the 10% additional tax (Form 5329) unless an "
                 "exception applies."),
     "notes": "§408A(d). The 10% stays in Form 5329."},
    {"diagnostic_id": "D_8606_TY2026", "title": "TY2026 — re-verify the IRA contribution limit", "severity": "warning",
     "condition": "tax_year == 2026 AND a contribution is present",
     "message": ("This 2026 return uses the 2025 IRA contribution limit ($7,000 / $8,000), which is INTERIM "
                 "until the 2026 figure publishes (~Dec 2026). Re-verify the limit."),
     "notes": "Re-pin the 2026 limit."},
    {"diagnostic_id": "D_8606_ROTHNOBASIS", "title": "Nonqualified Roth distribution with no recorded Roth basis", "severity": "warning",
     "condition": "f8606_roth_distributions > 0 AND f8606_roth_contribution_basis == 0 AND f8606_roth_conversion_basis == 0",
     "message": ("A nonqualified Roth IRA distribution is present but no Roth contribution or conversion basis is "
                 "recorded. Under §408A(d)(4) regular contributions come out first, tax-free — with a blank basis "
                 "the entire distribution is taxed as earnings (line 25c). Enter the cumulative Roth basis, or use "
                 "the Roth basis tracker, so the ordering is correct."),
     "notes": "No silent gap — a blank Roth basis over-taxes the distribution."},
]

F_SCENARIOS: list[dict] = [
    {"scenario_name": "F-T1 — nondeductible contribution, no distribution", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "nondeduct": 7000, "prior_basis": 0},
     "expected_outputs": {"f8606_line14": 7000, "f8606_line15c": 0, "f8606_line18": 0, "f8606_line25c": 0},
     "notes": "Basis builds to 7,000; nothing taxable."},
    {"scenario_name": "F-T2 — backdoor Roth (no other IRA)", "scenario_type": "edge_case", "sort_order": 2,
     "inputs": {"tax_year": 2025, "nondeduct": 7000, "prior_basis": 0, "year_end": 0, "conversions": 7000},
     "expected_outputs": {"f8606_line18": 0, "f8606_line15c": 0, "f8606_line14": 0},
     "notes": "ratio = 7000/(0+0+7000) = 1.0 → l11 = 7000 → l18 = 0 (fully nontaxable)."},
    {"scenario_name": "F-T3 — pro-rata taxable distribution", "scenario_type": "edge_case", "sort_order": 3,
     "inputs": {"tax_year": 2025, "nondeduct": 0, "prior_basis": 10000, "year_end": 50000, "distributions": 10000},
     "expected_outputs": {"f8606_line15c": 8333, "f8606_line14": 8333},
     "notes": "ratio = 10000/(50000+10000) = 0.16667; nontaxable dist = round(10000×0.16667)=1667; taxable = 8333; basis cfwd 10000−1667 = 8333."},
    {"scenario_name": "F-T4 — partial backdoor (existing pre-tax IRA)", "scenario_type": "edge_case", "sort_order": 4,
     "inputs": {"tax_year": 2025, "nondeduct": 7000, "prior_basis": 0, "year_end": 43000, "conversions": 7000},
     "expected_outputs": {"f8606_line18": 6020},
     "notes": "ratio = 7000/(43000+0+7000) = 0.14; l11 = round(7000×0.14)=980; l18 = 7000−980 = 6020."},
    {"scenario_name": "F-T5 — Part III nonqualified Roth (earnings taxable)", "scenario_type": "edge_case", "sort_order": 5,
     "inputs": {"tax_year": 2025, "roth_distributions": 20000, "roth_contribution_basis": 15000, "roth_conversion_basis": 3000},
     "expected_outputs": {"f8606_line25c": 2000},
     "notes": "max(0, 20000 − 15000 − 3000) = 2000 (the earnings)."},
    {"scenario_name": "F-T6 — Part III covered by contributions", "scenario_type": "edge_case", "sort_order": 6,
     "inputs": {"tax_year": 2025, "roth_distributions": 10000, "roth_contribution_basis": 15000},
     "expected_outputs": {"f8606_line25c": 0},
     "notes": "10000 ≤ 15000 contribution basis → 0 taxable."},
    {"scenario_name": "F-T7 — combined Part I distribution + Part II conversion", "scenario_type": "normal", "sort_order": 7,
     "inputs": {"tax_year": 2025, "prior_basis": 10000, "year_end": 30000, "distributions": 5000, "conversions": 5000},
     "expected_outputs": {"f8606_line15c": 3750, "f8606_line18": 3750},
     "notes": "ratio = 10000/(30000+5000+5000)=0.25; nontaxable each = round(5000×0.25)=1250; taxable dist 3750 + taxable conv 3750."},
    {"scenario_name": "F-G1 — over-contribution → diagnostic", "scenario_type": "diagnostic", "sort_order": 8,
     "inputs": {"tax_year": 2025, "nondeduct": 9000, "age_50_plus": False},
     "expected_outputs": {"D_8606_OVERCONTRIB": True},
     "notes": "9000 > 7000 (under 50) → D_8606_OVERCONTRIB."},
    {"scenario_name": "F-G2 — Roth distribution, no basis → D_8606_ROTHNOBASIS", "scenario_type": "diagnostic", "sort_order": 9,
     "inputs": {"tax_year": 2025, "roth_distributions": 5000, "roth_contribution_basis": 0, "roth_conversion_basis": 0},
     "expected_outputs": {"D_8606_ROTHNOBASIS": True},
     "notes": "A nonqualified Roth distribution with zero recorded basis → the whole 5,000 is taxable earnings (line 25c) + the no-basis warning."},
]

F_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-8606-PART1", "IRC_408D", "primary", "§408(d) pro-rata"),
    ("R-8606-PART1", "IRS_2025_F8606_INSTR", "secondary", "Part I lines 5-15c"),
    ("R-8606-PART2", "IRC_408A", "primary", "§408A(d)(3) conversion income"),
    ("R-8606-PART2", "IRS_2025_F8606_INSTR", "secondary", "Part II lines 16-18"),
    ("R-8606-PART3", "IRC_408A", "primary", "§408A(d)(4) the distribution ordering"),
    ("R-8606-4B", "IRS_2025_F8606_INSTR", "primary", "The taxable amounts → 1040 line 4b"),
    ("R-8606-ROTHTRACK", "IRC_408A", "primary", "§408A(d)(4) the ordering the tracker keeps correct"),
    ("R-8606-ROTHTRACK", "IRS_2025_F8606_INSTR", "secondary", "Part III basis lines 22/24"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-8606-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Part I §408(d) pro-rata ratio + the nontaxable split",
     "description": "Validates R-8606-PART1. Bug it catches: the pro-rata denominator wrong (missing distributions/conversions) or the ratio not capped at 1.0.",
     "definition": {"kind": "formula_check", "form": "FORM_8606",
                    "formula": "l10 = min(1, basis / (year_end + dist + conv)); nontaxable = amount × l10"},
     "sort_order": 1},
    {"assertion_id": "FA-1040-8606-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Part I taxable distribution (15c) + basis carryforward (14)",
     "description": "Validates R-8606-PART1. Bug it catches: line 15c ≠ distributions − nontaxable, or line 14 ≠ total basis − nontaxable (basis not conserved).",
     "definition": {"kind": "formula_check", "form": "FORM_8606",
                    "formula": "l15c = dist − l12; l14 = l3 − l13"},
     "sort_order": 2},
    {"assertion_id": "FA-1040-8606-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Part II taxable conversion + Part III Roth ordering",
     "description": "Validates R-8606-PART2 + PART3. Bug it catches: the backdoor Roth not zeroing (l18 ≠ conv − l11), or the Roth ordering not contributions-then-conversions-then-earnings.",
     "definition": {"kind": "formula_check", "form": "FORM_8606",
                    "formula": "l18 = max(0, conv − l11); l25c = max(0, dist − contrib_basis − conv_basis)"},
     "sort_order": 3},
    {"assertion_id": "FA-1040-8606-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "The 8606 taxable amounts → 1040 line 4b (supersede the 1099-R box 2a)",
     "description": "Validates R-8606-4B. Bug it catches: the 8606 taxable amount not landing on 4b, or not superseding the 1099-R box-2a path for an owner with basis.",
     "definition": {"kind": "flow_assertion", "form": "FORM_8606",
                    "checks": [{"source_line": "line_4b", "must_write_to": ["1040.4b"]}]},
     "sort_order": 4},
    {"assertion_id": "FA-1040-8606-05", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "Basis conservation — line 14 = total basis − nontaxable recovered",
     "description": "Validates R-8606-PART1. Bug it catches: basis created or destroyed (the carryforward not equal to the opening basis less the nontaxable amounts recovered this year).",
     "definition": {"kind": "reconciliation", "form": "FORM_8606",
                    "formula": "l14 == l3 − (l11 + l12)"},
     "sort_order": 5},
    {"assertion_id": "FA-1040-8606-06", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Gates — over-contribution + the year-end-value requirement",
     "description": "The over-limit nondeductible contribution warns; a distribution with basis but no year-end value warns (the pro-rata denominator).",
     "definition": {"kind": "gating_check", "form": "FORM_8606", "expect": {"red_fires": True},
                    "blockers": ["over_contribution", "missing_year_end"]},
     "sort_order": 6},
    {"assertion_id": "FA-1040-8606-07", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Roth basis tracker sources line 22/24 + rolls forward",
     "description": "Validates R-8606-ROTHTRACK. Bug it catches: the per-owner Roth basis tracker not sourcing line 22 (contribution basis) / line 24 (conversion basis), so a nonqualified Roth distribution is mis-taxed under §408A(d)(4); or the year-over-year roll not carrying opening basis less the distribution recovery plus current-year contributions.",
     "definition": {"kind": "flow_assertion", "form": "FORM_8606",
                    "checks": [{"source_line": "roth_basis_tracker", "must_write_to": ["FORM_8606.l22", "FORM_8606.l24"]}]},
     "sort_order": 7},
]


FORMS: list[dict] = [
    {"identity": F_IDENTITY, "facts": F_FACTS, "rules": F_RULES, "lines": F_LINES,
     "diagnostics": F_DIAGNOSTICS, "scenarios": F_SCENARIOS, "rule_links": F_RULE_LINKS},
]


class Command(BaseCommand):
    help = "Load the FORM_8606 spec (Nondeductible IRAs). Refuses until READY_TO_SEED=True."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad FORM_8606 spec (Nondeductible IRAs)\n"))
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
                "\nREFUSING TO SEED FORM_8606: not cleared to seed.\n\n"
                "Gated until Ken's review walk (the pro-rata + the Roth ordering + the\n"
                "1099-R box-2a supersession + the line-17 simplification).\n\n"
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
        form = TaxForm.objects.filter(form_number="FORM_8606").first()
        if form:
            uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
            self.stdout.write("FORM_8606: all rules cited" if not uncited
                              else self.style.WARNING(f"FORM_8606 uncited rules: {len(uncited)}"))
