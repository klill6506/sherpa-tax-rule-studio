"""Load Form 6252 (Installment Sale Income) — Broad v1, modern-style loader.

Authored 2026-06-28 in the load_4797.py / load_1040_form_1116.py modern pattern: a pure
module-level ``compute_6252()`` the integrity gate re-types, a ``FORMS`` structure, and
``FLOW_ASSERTIONS``.

KEN'S BROAD-V1 SCOPE (chosen 2026-06-28, two AskUserQuestions): the full Form 6252 — Parts
I, II, and III (related-party §453(e)) — PLUS §453A interest on deferred tax. RED-defer only
contingent-payment sales (line 4 = "No"). §453A aggregate-obligation balances and the L25/L36
spread-recapture portions are preparer-asserted; the §6621 underpayment rate is reused from the
Form 2210 infrastructure; the maximum tax rate is year-keyed. Closes the Form 4797 line-4 / line-15
RED-defer (the 6252 ↔ 4797 interplay the 4797 unit deferred).

LAW VERIFIED 2026-06-28 against the actual 2025 Form 6252 PDF (f6252.pdf, all 4 pages incl. the
embedded instructions, OMB 1545-0228, "Created 5/28/25") + IRS Pub 537 (2025) "Interest on Deferred
Tax" / §453A worksheet + IRC §453 / §453(e) / §453(g) / §453A. Every line number and routing
destination below is read directly off that PDF.

CORE MODEL (installment method, §453):
  Part I (year of sale, then frozen):
    L7 = L5 − L6 (selling price net of assumed debt). L10 = L8 − L9 (adjusted basis).
    L13 = L10 + L11 + L12, where L12 = §1245/§1250 ordinary recapture from Form 4797 Part III
      line 31 — FULLY taxable in the year of sale (not spread) and added to basis here.
    L14 = L5 − L13 (if ≤ 0 → NOT an installment sale; report on 4797/8949/Sch D — D_6252_002).
    L16 = L14 − L15 (gross profit; L15 = §121 main-home exclusion, default 0).
    L17 = max(0, L6 − L13) (excess assumed debt over basis = deemed payment in year of sale).
    L18 = L7 + L17 (contract price).
    L19 = L16 / L18 — the gross profit percentage, FROZEN for every later year.
  Part II (every year):
    L20 = L17 in the year of sale else 0. L22 = L20 + L21 (payments this year).
    L24 = L22 × L19 (installment sale income, ≥ 0). L25 = ordinary recapture portion → Form 4797
      line 15. L26 = L24 − L25 → routes by property character.
  Part III (related party, §453(e); year of sale + 2 yrs unless a line-29 condition is met):
    L31 = L18 (contract price). L32 = min(L30, L31). L33 = L22 + L23 (payments to date).
    L34 = max(0, L32 − L33). L35 = L34 × L19. L36 ordinary → 4797 line 15. L37 = L35 − L36 → Sch D/4797.

ROUTING (6252 → 1040), per the i6252 line-25 / line-26 instructions:
  Ordinary recapture (L25 + L36) → Form 4797 line 15 (ordinary gains from installment sales).
  Gain (L26 + L37) by character:
    business §1231 held > 1 yr → Form 4797 line 4 (→ 4797's §1231 netting → Schedule D),
    held ≤ 1 yr or ordinary noncapital → Form 4797 line 10 ("From Form 6252"),
    capital asset → Schedule D directly (short- or long-term per holding period).
  §1250 property: the unrecaptured-§1250 portion of L26 → the Schedule D Unrecaptured §1250 Gain
    Worksheet (25%) — preparer-asserted in v1 (consistent with the 4797 line-26a boundary).

§453A INTEREST ON DEFERRED TAX (Pub 537 — NOT figured on Form 6252; lands on Schedule 2):
  Gate: selling price > $150,000 AND aggregate nondealer installment obligations outstanding at the
    close of the tax year > $5,000,000 (exceptions: farm property, personal-use property of an
    individual, real property before 1988, personal property before 1989).
  Interest = Deferred Tax Liability × Applicable Percentage × §6621 underpayment rate, where
    Deferred Tax Liability = unrecognized gain × max tax rate (ordinary 37% / LTCG 20%, as
      appropriate); unrecognized gain = outstanding obligation (L18 − payments to date) × L19;
    Applicable Percentage = (aggregate obligations at year end − $5M) / aggregate obligations at year end.
  v1: aggregate-obligation balances are preparer-asserted (the system can't know a taxpayer's other
    installment notes); the §6621 rate is the Form 2210 year-keyed rate; max rate is year-keyed.

v1 RED-defers / no-silent-gap diagnostics: contingent-payment sale (line 4 = No → ratable basis
  recovery, its own regime), §453(g) depreciable-property-to-related-person bar, the §453A(d) pledge
  rule deemed-payment, and the "line 14 ≤ 0 = not an installment sale" stop.

SAFETY GUARD: READY_TO_SEED stays False until Ken's review walk (the gross-profit %/contract-price
arithmetic, the 4797 line-4/15 routing closure, the Part III related-party acceleration, the §453A
worksheet, and the preparer-asserted boundaries).
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


READY_TO_SEED = True  # FLIPPED 2026-06-28 — Ken approved the review walk ("Approve — seed it").


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1  # New form — no prior RS row (lookup returned 404).
FORM_ENTITY_TYPES = ["1040"]  # 1040 build. (6252 is filed by entities too; entity routing = future.)
FORM_STATUS = "draft"


from decimal import ROUND_HALF_UP, Decimal  # noqa: E402


def _D(x):
    return Decimal(str(x if x is not None else 0))


def _r0(x):
    return int(_D(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


# ═══════════════════════════════════════════════════════════════════════════
# PURE COMPUTE (mirrors the tts compute leg; check_6252_integrity.py re-types it)
# ═══════════════════════════════════════════════════════════════════════════

_FIVE_MILLION = Decimal("5000000")
_PRICE_THRESHOLD = Decimal("150000")


def compute_6252(*,
                 # ── Part I (year of sale) ──
                 selling_price=0, mortgages_assumed=0, cost_basis=0, depreciation_allowed=0,
                 commissions_expenses=0, recapture_from_4797=0, excluded_gain_main_home=0,
                 # ── Part II (every year) ──
                 is_year_of_sale=True, payments_current_year=0, payments_prior_years=0,
                 ordinary_recapture_portion=0, prior_gross_profit_pct=None,
                 # ── character / routing ──
                 property_character="capital", holding_period_months=0, unrecaptured_1250_portion=0,
                 # ── Part III related party (§453(e)) ──
                 related_party=False, related_party_resold=False, rp_exception="",
                 rp_selling_price=0, rp_ordinary_recapture=0,
                 # ── §453A interest on deferred tax ──
                 aggregate_obligations_year_end=0, section_6621_rate=0,
                 max_rate_ordinary="0.37", max_rate_ltcg="0.20",
                 # ── red-defer flags ──
                 price_not_determinable=False, depreciable_to_related_person=False,
                 **_ignored) -> dict:
    """One installment sale, one tax year → the 6252 lines + the 1040 routing + §453A interest.

    Returns key lines and destinations:
      l16/l18/l19          — gross profit, contract price, gross profit % (frozen)
      l24/l26/l37          — installment income, the capital gain (Part II / Part III)
      f4797_line4          — §1231 gain from installment sales (business, held > 1 yr)
      f4797_line10         — ordinary gain from installment sales (≤ 1 yr / noncapital)
      f4797_line15         — ordinary recapture from installment sales (L25 + L36)
      sch_d_st / sch_d_lt  — capital-asset gain routed directly to Schedule D
      unrecaptured_1250    — the 25% bucket → Sch D Unrecaptured §1250 Gain Worksheet
      section_453a_interest — §453A(c) interest on deferred tax → Schedule 2
    Or {'red_defer': [...]} for an unsupported path (contingent sale / §453(g) bar)."""
    reasons = []
    if price_not_determinable:
        reasons.append("contingent_payment_sale")        # line 4 = No
    if depreciable_to_related_person:
        reasons.append("depreciable_property_to_related_person")  # §453(g)
    if reasons:
        return {"red_defer": reasons, "f4797_line4": None, "f4797_line15": None,
                "sch_d_lt": None, "section_453a_interest": None}

    # ── Part I — gross profit and contract price ──
    l5 = _D(selling_price)
    l6 = _D(mortgages_assumed)
    l7 = l5 - l6
    l8 = _D(cost_basis)
    l9 = _D(depreciation_allowed)
    l10 = l8 - l9
    l11 = _D(commissions_expenses)
    l12 = _D(recapture_from_4797)                         # §1245/1250 recapture (full, year of sale)
    l13 = l10 + l11 + l12
    l14 = l5 - l13
    l15 = _D(excluded_gain_main_home)
    l16 = max(Decimal("0"), l14 - l15)                   # gross profit
    l17 = max(Decimal("0"), l6 - l13)                    # excess assumed debt = deemed payment
    l18 = l7 + l17                                        # contract price

    not_installment = l14 <= 0                            # gain ≤ 0 → don't file 6252 (D_6252_002)

    # ── gross profit percentage (frozen at the year-of-sale value) ──
    if is_year_of_sale:
        l19 = (l16 / l18) if l18 > 0 else Decimal("0")
    else:
        l19 = _D(prior_gross_profit_pct)

    # ── Part II — installment sale income ──
    l20 = l17 if is_year_of_sale else Decimal("0")
    l21 = _D(payments_current_year)
    l22 = l20 + l21
    l23 = _D(payments_prior_years)
    l24 = max(Decimal("0"), l22 * l19)
    l25 = _D(ordinary_recapture_portion)                 # → Form 4797 line 15
    l26 = l24 - l25                                       # → routed by character

    # ── Part III — related-party second disposition (§453(e)) ──
    part3_applies = bool(related_party and related_party_resold and not rp_exception)
    if part3_applies:
        l30 = _D(rp_selling_price)
        l31 = l18
        l32 = min(l30, l31)
        l33 = l22 + l23                                  # payments to date (i6252 line 33)
        l34 = max(Decimal("0"), l32 - l33)
        l35 = l34 * l19
        l36 = _D(rp_ordinary_recapture)                  # → Form 4797 line 15
        l37 = l35 - l36                                  # → Sch D / Form 4797
    else:
        l30 = l31 = l32 = l33 = l34 = l35 = l36 = l37 = Decimal("0")

    # ── routing of the capital gain (L26 + L37) and ordinary recapture (L25 + L36) ──
    gain = l26 + l37
    f4797_line15 = l25 + l36                             # ordinary recapture → 4797 Part II line 15
    f4797_line4 = f4797_line10 = sch_d_st = sch_d_lt = Decimal("0")
    long_term = int(holding_period_months or 0) > 12
    if property_character == "business_1231" and long_term:
        f4797_line4 = gain                               # → 4797 §1231 netting → Schedule D
    elif property_character == "ordinary" or not long_term:
        f4797_line10 = gain                              # ordinary "From Form 6252"
    else:                                                 # capital asset
        if long_term:
            sch_d_lt = gain
        else:
            sch_d_st = gain
    unrecaptured_1250 = _D(unrecaptured_1250_portion)    # → Sch D 25% worksheet (preparer-asserted)

    # ── §453A interest on deferred tax (Pub 537) ──
    section_453a_interest = Decimal("0")
    s453a_applies = (l5 > _PRICE_THRESHOLD
                     and _D(aggregate_obligations_year_end) > _FIVE_MILLION)
    if s453a_applies:
        outstanding = max(Decimal("0"), l18 - (l22 + l23))   # remaining obligation balance
        unrecognized_gain = outstanding * l19
        max_rate = (_D(max_rate_ltcg)
                    if (property_character in ("capital", "business_1231") and long_term)
                    else _D(max_rate_ordinary))
        deferred_tax_liability = unrecognized_gain * max_rate
        agg = _D(aggregate_obligations_year_end)
        applicable_pct = (agg - _FIVE_MILLION) / agg if agg > 0 else Decimal("0")
        # Whole-dollar Schedule 2 amount (the applicable % is a repeating decimal — quantize the result).
        section_453a_interest = _D(_r0(deferred_tax_liability * applicable_pct * _D(section_6621_rate)))

    return {
        "l7": l7, "l10": l10, "l13": l13, "l14": l14, "l16": l16, "l17": l17, "l18": l18,
        "l19": l19, "l20": l20, "l22": l22, "l24": l24, "l25": l25, "l26": l26,
        "l30": l30, "l32": l32, "l33": l33, "l34": l34, "l35": l35, "l36": l36, "l37": l37,
        "f4797_line4": f4797_line4, "f4797_line10": f4797_line10, "f4797_line15": f4797_line15,
        "sch_d_st": sch_d_st, "sch_d_lt": sch_d_lt, "unrecaptured_1250": unrecaptured_1250,
        "section_453a_interest": section_453a_interest,
        "not_installment_sale": not_installment, "part3_applies": part3_applies,
        "s453a_applies": s453a_applies,
    }


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("6252", "Form 6252 — Installment Sale Income"),
    ("installment_method", "§453 installment method — gross profit %, contract price, payments"),
    ("section_453a", "§453A — interest on deferred tax for large nondealer installment obligations"),
    ("related_party_installment", "§453(e)/(g) — related-party second disposition + depreciable-property bar"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_4797_INSTR",   # the recapture interplay (6252 L12/L25/L26 ↔ 4797 lines 4/15/31)
]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRC_453",
        "source_type": "statute", "source_rank": "primary_official", "jurisdiction_code": "FED",
        "title": "IRC §453 — Installment Method",
        "citation": "26 U.S.C. §453", "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:453%20edition:prelim)",
        "current_status": "active", "is_substantive_authority": True, "is_filing_authority": False,
        "trust_score": 10.0, "requires_human_review": True,
        "notes": "Installment method: income = payments received × gross profit %. Losses can't use it (Rev. Rul. 70-430).",
        "topics": ["installment_method"],
        "excerpts": [
            {"excerpt_label": "§453(a),(c) — installment method gross-profit ratio",
             "location_reference": "§453(a), §453(c)",
             "excerpt_text": (
                 "Under the installment method, the income recognized for any taxable year from a "
                 "disposition is the proportion of the payments received in that year which the gross "
                 "profit (realized or to be realized when payment is completed) bears to the total "
                 "contract price. An installment sale is a disposition of property where at least one "
                 "payment is received after the close of the year of disposition. The installment method "
                 "may be used only where the sale results in a gain."),
             "summary_text": "Income = payments × (gross profit / contract price); gains only.",
             "is_key_excerpt": True},
        ],
    },
    {
        "source_code": "IRC_453_E_G",
        "source_type": "statute", "source_rank": "primary_official", "jurisdiction_code": "FED",
        "title": "IRC §453(e) and §453(g) — Related-Party Rules",
        "citation": "26 U.S.C. §453(e), §453(g)", "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:453%20edition:prelim)",
        "current_status": "active", "is_substantive_authority": True, "is_filing_authority": False,
        "trust_score": 10.0, "requires_human_review": True,
        "notes": "§453(e): a related party's second disposition within 2 years accelerates the first seller's gain. §453(g): installment method generally barred on a sale of depreciable property to a related person.",
        "topics": ["related_party_installment"],
        "excerpts": [
            {"excerpt_label": "§453(e) second-disposition acceleration; §453(g) depreciable bar",
             "location_reference": "§453(e), §453(g)",
             "excerpt_text": (
                 "§453(e): if a person makes an installment sale to a related party who then makes a "
                 "second disposition before paying for the first, the amount realized on the second "
                 "disposition is treated as received by the first seller (Part III, lines 30-37). The "
                 "rule does not apply if the second disposition is more than 2 years after the first "
                 "(non-marketable securities), is after a death, is involuntary, or non-tax-avoidance is "
                 "established. §453(g): the installment method generally may not be used for a sale of "
                 "depreciable property to a related person; all payments are treated as received in the "
                 "year of sale unless no significant tax-deferral purpose is shown."),
             "summary_text": "§453(e) related-party resale within 2 yrs accelerates gain; §453(g) bars installment on depreciable sales to related persons.",
             "is_key_excerpt": True},
        ],
    },
    {
        "source_code": "IRC_453A",
        "source_type": "statute", "source_rank": "primary_official", "jurisdiction_code": "FED",
        "title": "IRC §453A — Interest on Deferred Tax; Pledge Rule",
        "citation": "26 U.S.C. §453A", "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:453A%20edition:prelim)",
        "current_status": "active", "is_substantive_authority": True, "is_filing_authority": False,
        "trust_score": 10.0, "requires_human_review": True,
        "notes": "Interest charge on the deferred tax for large nondealer obligations; the §453A(d) pledge rule treats secured-debt proceeds as payments.",
        "topics": ["section_453a"],
        "excerpts": [
            {"excerpt_label": "§453A(a)-(c) — interest on deferred tax; >$150k + >$5M tests",
             "location_reference": "§453A(b),(c)",
             "excerpt_text": (
                 "§453A applies to a nondealer installment obligation arising from a disposition of "
                 "property with a sales price over $150,000 if the aggregate face amount of such "
                 "obligations outstanding at the close of the tax year exceeds $5,000,000. The taxpayer "
                 "owes interest on the deferred tax liability: the unrecognized gain at year end times "
                 "the maximum rate of tax (ordinary or capital, as applicable), multiplied by the "
                 "applicable percentage — the excess of the year-end obligation balance over $5,000,000 "
                 "divided by that balance — and by the §6621 underpayment rate. Excepted: farm property, "
                 "an individual's personal-use property, real property before 1988, personal before 1989."),
             "summary_text": "§453A interest = deferred-tax-liability × applicable% × §6621 rate; gate >$150k sale and >$5M aggregate obligations.",
             "is_key_excerpt": True},
        ],
    },
    {
        "source_code": "IRS_2025_6252_FORM",
        "source_type": "official_form", "source_rank": "primary_official", "jurisdiction_code": "FED",
        "tax_year_start": 2025, "tax_year_end": 2025,
        "title": "Form 6252 (2025) — Installment Sale Income (with instructions)",
        "citation": "Form 6252 (2025), OMB 1545-0228", "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f6252.pdf",
        "current_status": "active", "is_substantive_authority": False, "is_filing_authority": True,
        "trust_score": 9.5, "requires_human_review": False,
        "notes": "Verified line-by-line 2026-06-28 against the PDF (all 4 pages). The line-25/26 destinations to Form 4797 lines 15/4 are quoted directly.",
        "topics": ["6252", "installment_method"],
        "excerpts": [
            {"excerpt_label": "Part I/II line-by-line (L5-L26) + GP% frozen",
             "location_reference": "Form 6252 (2025), Parts I-II",
             "excerpt_text": (
                 "L7 = L5 − L6; L10 = L8 − L9; L13 = L10 + L11 + L12 (L12 = income recapture from Form "
                 "4797 Part III); L14 = L5 − L13 (if ≤ 0 don't complete the rest); L16 = L14 − L15; L17 "
                 "= L6 − L13 (≥ 0); L18 = L7 + L17 (contract price); L19 = L16 / L18 (gross profit %, "
                 "use the year-of-sale value in later years); L20 = L17 in year of sale else 0; L22 = "
                 "L20 + L21; L24 = L22 × L19 (≥ 0); L25 = ordinary recapture → Form 4797 line 15; L26 = "
                 "L24 − L25 → Schedule D or Form 4797."),
             "summary_text": "Parts I-II arithmetic; GP% frozen at the year-of-sale value; L25 → 4797 L15, L26 → Sch D/4797.",
             "is_key_excerpt": True},
            {"excerpt_label": "Line 12 — recapture full in year of sale; lines 25/26 destinations",
             "location_reference": "i6252 (2025), lines 12, 25, 26",
             "excerpt_text": (
                 "Line 12: any §1245/§1250 ordinary recapture (including §179/§291) is fully taxable in "
                 "the year of sale even if no payments were received; figure it on Form 4797 Part III "
                 "(the amount on Form 4797 line 31) and enter it here and on Form 4797 line 13. Line 25: "
                 "enter here and on Form 4797 line 15 any ordinary income recapture on §1252/§1254/§1255 "
                 "property or remaining recapture from a prior-year sale. Line 26: for trade/business "
                 "property held more than 1 year, enter on Form 4797 line 4; if held 1 year or less or "
                 "ordinary, on Form 4797 line 10 ('From Form 6252'); for capital assets, on Schedule D. "
                 "§1250 property: figure the unrecaptured §1250 gain in line 26 via the Sch D worksheet."),
             "summary_text": "§1245/1250 recapture full in year of sale (L12→4797 L13); L25→4797 L15; L26→4797 L4/L10 or Sch D; §1250 unrecaptured via Sch D worksheet.",
             "is_key_excerpt": True},
            {"excerpt_label": "Part III — related-party second disposition (L27-L37)",
             "location_reference": "Form 6252 (2025), Part III",
             "excerpt_text": (
                 "Complete Part III for the year of sale and 2 years after if the property was sold to a "
                 "related party, unless final payment was received this year. If the related party "
                 "resold (line 28 Yes) and no line-29 condition (a-e) is met: L31 = contract price from "
                 "line 18; L32 = smaller of L30 (related party's selling price) or L31; L33 = sum of "
                 "lines 22 and 23; L34 = L32 − L33 (≥ 0); L35 = L34 × the year-of-first-sale GP% (line "
                 "19); L36 = ordinary recapture → Form 4797 line 15; L37 = L35 − L36 → Schedule D/4797."),
             "summary_text": "Part III accelerates gain on a related party's resale within 2 years: L35 = (min(L30,L31) − payments) × GP%.",
             "is_key_excerpt": True},
        ],
    },
    {
        "source_code": "IRS_PUB_537",
        "source_type": "official_publication", "source_rank": "primary_official", "jurisdiction_code": "FED",
        "tax_year_start": 2025, "tax_year_end": 2025,
        "title": "IRS Publication 537 — Installment Sales",
        "citation": "Publication 537 (2025)", "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/p537.pdf",
        "current_status": "active", "is_substantive_authority": False, "is_filing_authority": False,
        "trust_score": 9.0, "requires_human_review": False,
        "notes": "The §453A interest worksheet (not on Form 6252). Verified excerpt 2026-06-28.",
        "topics": ["section_453a", "installment_method"],
        "excerpts": [
            {"excerpt_label": "Interest on Deferred Tax — how to figure (§453A)",
             "location_reference": "Pub 537 (2025), 'Interest on Deferred Tax'",
             "excerpt_text": (
                 "First, find the §6621 underpayment rate in effect for the month the tax year ends. "
                 "Compute the deferred tax liability = the balance of unrecognized gain at year end × "
                 "your maximum tax rate (ordinary or capital gain, as appropriate). Compute the "
                 "applicable percentage = the aggregate face amount of obligations outstanding at year "
                 "end in excess of $5,000,000, divided by the aggregate face amount outstanding at year "
                 "end. Interest on deferred tax = deferred tax liability × applicable percentage × the "
                 "underpayment rate."),
             "summary_text": "§453A interest = (unrecognized gain × max rate) × ((year-end obligations − $5M)/year-end obligations) × §6621 rate.",
             "is_key_excerpt": True},
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRC_453", "6252", "governs"),
    ("IRC_453_E_G", "6252", "governs"),
    ("IRC_453A", "6252", "governs"),
    ("IRS_2025_6252_FORM", "6252", "governs"),
    ("IRS_PUB_537", "6252", "informs"),
    ("IRS_2025_4797_INSTR", "6252", "informs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM: 6252
# ═══════════════════════════════════════════════════════════════════════════

P_IDENTITY = {
    "form_number": "6252",
    "form_title": "Installment Sale Income",
    "notes": (
        "Broad-v1 1040 build (Ken 2026-06-28): the full Form 6252 — Parts I, II, III (related "
        "party §453(e)) — plus §453A interest on deferred tax. §453 installment method: gross "
        "profit % (L19 = L16/L18) frozen at the year of sale; installment income L24 = payments "
        "(L22) × L19. §1245/§1250 recapture (L12, from Form 4797 Part III line 31) is FULLY taxed "
        "in the year of sale and added to basis. Routing: ordinary recapture (L25+L36) → Form 4797 "
        "line 15; capital gain (L26+L37) → Form 4797 line 4 (business §1231 >1yr) / line 10 "
        "(≤1yr or ordinary) / Schedule D (capital). Unrecaptured §1250 portion → the Sch D 25% "
        "worksheet (preparer-asserted). §453A interest (Pub 537, off-form → Schedule 2) gated on "
        "sale >$150k and aggregate nondealer obligations >$5M. Closes the Form 4797 line-4/15 "
        "RED-defer. RED-defers (no silent gap): contingent-payment sale (line 4=No), §453(g) "
        "depreciable-to-related-person bar, §453A(d) pledge rule, line-14≤0 not-an-installment-sale."
    ),
}

P_FACTS: list[dict] = [
    # ── Part I (year-of-sale inputs) ──
    {"fact_key": "f6252_selling_price", "label": "Selling price incl. mortgages/debts, no interest (line 5)",
     "data_type": "decimal", "default_value": "0", "sort_order": 1},
    {"fact_key": "f6252_mortgages_assumed", "label": "Mortgages/debts the buyer assumed or took subject to (line 6)",
     "data_type": "decimal", "default_value": "0", "sort_order": 2},
    {"fact_key": "f6252_cost_basis", "label": "Cost or other basis of property sold (line 8)",
     "data_type": "decimal", "default_value": "0", "sort_order": 3},
    {"fact_key": "f6252_depreciation_allowed", "label": "Depreciation allowed or allowable (line 9)",
     "data_type": "decimal", "default_value": "0", "sort_order": 4},
    {"fact_key": "f6252_commissions_expenses", "label": "Commissions and other expenses of sale (line 11)",
     "data_type": "decimal", "default_value": "0", "sort_order": 5},
    {"fact_key": "f6252_recapture_from_4797", "label": "Income recapture from Form 4797 Part III, line 31 (line 12)",
     "data_type": "decimal", "default_value": "0", "sort_order": 6,
     "notes": "§1245/§1250 ordinary recapture — fully taxed in the year of sale; added to basis here."},
    {"fact_key": "f6252_excluded_gain_main_home", "label": "§121 excluded gain if main home (line 15)",
     "data_type": "decimal", "default_value": "0", "sort_order": 7},
    # ── Part II (per-year inputs) ──
    {"fact_key": "f6252_is_year_of_sale", "label": "Is this the year of sale? (drives line 20)",
     "data_type": "boolean", "default_value": "true", "sort_order": 10},
    {"fact_key": "f6252_payments_current_year", "label": "Payments received during the year, no interest (line 21)",
     "data_type": "decimal", "default_value": "0", "sort_order": 11},
    {"fact_key": "f6252_payments_prior_years", "label": "Payments received in prior years, no interest (line 23)",
     "data_type": "decimal", "default_value": "0", "sort_order": 12},
    {"fact_key": "f6252_ordinary_recapture_portion", "label": "Part of line 24 that is ordinary recapture (line 25)",
     "data_type": "decimal", "default_value": "0", "sort_order": 13,
     "notes": "§1252/1254/1255 or remaining prior-year recapture → Form 4797 line 15. Preparer-asserted."},
    {"fact_key": "f6252_prior_gross_profit_pct", "label": "Year-of-sale gross profit % (later years, line 19)",
     "data_type": "decimal", "default_value": "0", "sort_order": 14,
     "notes": "Frozen from the year of sale; used when is_year_of_sale is False."},
    # ── character / routing ──
    {"fact_key": "f6252_property_character", "label": "Character: capital / business_1231 / ordinary",
     "data_type": "string", "default_value": "capital", "sort_order": 20,
     "notes": "Drives the line-26 destination (Sch D vs Form 4797 line 4/10)."},
    {"fact_key": "f6252_holding_period_months", "label": "Holding period (months) — >12 = long-term",
     "data_type": "integer", "default_value": "0", "sort_order": 21},
    {"fact_key": "f6252_unrecaptured_1250_portion", "label": "Unrecaptured §1250 portion of line 26 (→ Sch D 25%)",
     "data_type": "decimal", "default_value": "0", "sort_order": 22,
     "notes": "Preparer-asserted via the Sch D Unrecaptured §1250 Gain Worksheet (v1 boundary)."},
    # ── Part III related party ──
    {"fact_key": "f6252_related_party", "label": "Sold to a related party? (line 3)",
     "data_type": "boolean", "default_value": "false", "sort_order": 30},
    {"fact_key": "f6252_related_party_resold", "label": "Related party resold this tax year? (line 28)",
     "data_type": "boolean", "default_value": "false", "sort_order": 31},
    {"fact_key": "f6252_rp_exception", "label": "Line-29 exception met (a-e), else blank",
     "data_type": "string", "default_value": "", "sort_order": 32,
     "notes": "Any of 29a-e met → skip lines 30-37."},
    {"fact_key": "f6252_rp_selling_price", "label": "Selling price by related party (line 30)",
     "data_type": "decimal", "default_value": "0", "sort_order": 33},
    {"fact_key": "f6252_rp_ordinary_recapture", "label": "Ordinary recapture portion of line 35 (line 36)",
     "data_type": "decimal", "default_value": "0", "sort_order": 34},
    # ── §453A ──
    {"fact_key": "f6252_aggregate_obligations_year_end", "label": "Aggregate nondealer installment obligations at year end (§453A)",
     "data_type": "decimal", "default_value": "0", "sort_order": 40,
     "notes": "Preparer-asserted — the §453A >$5M test; the system can't know other installment notes."},
    {"fact_key": "f6252_section_6621_rate", "label": "§6621 underpayment rate for the month the tax year ends",
     "data_type": "decimal", "default_value": "0", "sort_order": 41,
     "notes": "Reused from the Form 2210 §6621 infrastructure (year-keyed)."},
    # ── red-defer flags ──
    {"fact_key": "f6252_price_not_determinable", "label": "Total selling price not determinable (line 4 = No)?",
     "data_type": "boolean", "default_value": "false", "sort_order": 50,
     "notes": "Contingent payment sale → RED-defer (ratable basis recovery not modeled)."},
    {"fact_key": "f6252_depreciable_to_related_person", "label": "Sale of depreciable property to a related person (§453(g))?",
     "data_type": "boolean", "default_value": "false", "sort_order": 51,
     "notes": "Installment method generally barred → RED-defer."},
    # ── outputs ──
    {"fact_key": "f6252_line19", "label": "Gross profit percentage (line 19)", "data_type": "decimal",
     "sort_order": 60, "notes": "OUTPUT (frozen at year of sale)."},
    {"fact_key": "f6252_line24", "label": "Installment sale income (line 24)", "data_type": "decimal",
     "sort_order": 61, "notes": "OUTPUT."},
    {"fact_key": "f6252_line26", "label": "Line 26 gain → Schedule D or Form 4797", "data_type": "decimal",
     "sort_order": 62, "notes": "OUTPUT."},
    {"fact_key": "f6252_f4797_line4", "label": "§1231 gain from installment sales → Form 4797 line 4",
     "data_type": "decimal", "sort_order": 63, "notes": "OUTPUT."},
    {"fact_key": "f6252_f4797_line15", "label": "Ordinary recapture from installment sales → Form 4797 line 15",
     "data_type": "decimal", "sort_order": 64, "notes": "OUTPUT (L25 + L36)."},
    {"fact_key": "f6252_section_453a_interest", "label": "§453A interest on deferred tax → Schedule 2",
     "data_type": "decimal", "sort_order": 65, "notes": "OUTPUT — off-form (Pub 537)."},
]

P_RULES: list[dict] = [
    {"rule_id": "R-6252-GP", "title": "Part I gross profit + contract price (L7-L18)", "rule_type": "calculation",
     "precedence": 1, "sort_order": 1,
     "formula": ("L7 = L5 − L6; L10 = L8 − L9; L13 = L10 + L11 + L12; L14 = L5 − L13; L16 = L14 − L15; "
                 "L17 = max(0, L6 − L13); L18 = L7 + L17. L12 = §1245/1250 recapture (Form 4797 L31)."),
     "inputs": ["f6252_selling_price", "f6252_mortgages_assumed", "f6252_cost_basis",
                "f6252_depreciation_allowed", "f6252_commissions_expenses", "f6252_recapture_from_4797",
                "f6252_excluded_gain_main_home"],
     "outputs": [],
     "description": "Gross profit (L16) and contract price (L18); recapture is added to basis (L13) and taxed full in year of sale."},
    {"rule_id": "R-6252-GPPCT", "title": "Gross profit percentage, frozen (L19)", "rule_type": "calculation",
     "precedence": 2, "sort_order": 2,
     "formula": "L19 = L16 / L18 in the year of sale; in later years use the year-of-sale L19.",
     "inputs": ["f6252_is_year_of_sale", "f6252_prior_gross_profit_pct"],
     "outputs": ["f6252_line19"],
     "description": "The gross profit ratio is fixed at the year of sale and reused every later year."},
    {"rule_id": "R-6252-INCOME", "title": "Part II installment sale income (L20-L26)", "rule_type": "calculation",
     "precedence": 3, "sort_order": 3,
     "formula": ("L20 = L17 (year of sale) else 0; L22 = L20 + L21; L24 = max(0, L22 × L19); "
                 "L25 = ordinary recapture portion → 4797 L15; L26 = L24 − L25."),
     "inputs": ["f6252_payments_current_year", "f6252_payments_prior_years", "f6252_ordinary_recapture_portion"],
     "outputs": ["f6252_line24", "f6252_line26"],
     "description": "Installment income = payments × gross profit %; ordinary recapture split out to L25."},
    {"rule_id": "R-6252-ROUTE", "title": "Route L26/L37 + L25/L36 to 4797 / Schedule D", "rule_type": "routing",
     "precedence": 4, "sort_order": 4,
     "formula": ("Ordinary recapture (L25 + L36) → Form 4797 line 15. Gain (L26 + L37): business §1231 "
                 ">1yr → 4797 line 4; ≤1yr or ordinary → 4797 line 10; capital → Schedule D (ST/LT)."),
     "inputs": ["f6252_property_character", "f6252_holding_period_months", "f6252_unrecaptured_1250_portion"],
     "outputs": ["f6252_f4797_line4", "f6252_f4797_line15"],
     "description": "Closes the 4797 line-4/15 RED-defer; §1250 unrecaptured portion → Sch D 25% worksheet."},
    {"rule_id": "R-6252-RELPARTY", "title": "Part III related-party second disposition (§453(e))", "rule_type": "calculation",
     "precedence": 5, "sort_order": 5,
     "formula": ("If related party resold and no line-29 exception: L31 = L18; L32 = min(L30, L31); "
                 "L33 = L22 + L23; L34 = max(0, L32 − L33); L35 = L34 × L19; L37 = L35 − L36."),
     "inputs": ["f6252_related_party", "f6252_related_party_resold", "f6252_rp_exception",
                "f6252_rp_selling_price", "f6252_rp_ordinary_recapture"],
     "outputs": ["f6252_line26"],
     "description": "A related party's resale within 2 years accelerates the original seller's gain."},
    {"rule_id": "R-6252-453A", "title": "§453A interest on deferred tax (Pub 537)", "rule_type": "calculation",
     "precedence": 6, "sort_order": 6,
     "formula": ("If L5 > 150,000 AND aggregate obligations at year end > 5,000,000: interest = "
                 "(unrecognized gain × max rate) × ((aggregate − 5M)/aggregate) × §6621 rate, where "
                 "unrecognized gain = (L18 − payments to date) × L19."),
     "inputs": ["f6252_aggregate_obligations_year_end", "f6252_section_6621_rate"],
     "outputs": ["f6252_section_453a_interest"],
     "description": "Interest charge on deferred tax for large nondealer installment obligations → Schedule 2."},
]

P_LINES: list[dict] = [
    {"line_number": "3", "description": "Line 3 — sold to a related party? (Yes → Part III)", "line_type": "input"},
    {"line_number": "4", "description": "Line 4 — total selling price determinable? (No → contingent sale)", "line_type": "input"},
    {"line_number": "5", "description": "Line 5 — selling price incl. mortgages/debts (no interest)", "line_type": "input"},
    {"line_number": "6", "description": "Line 6 — mortgages/debts the buyer assumed or took subject to", "line_type": "input"},
    {"line_number": "7", "description": "Line 7 — line 5 minus line 6", "line_type": "calculated"},
    {"line_number": "8", "description": "Line 8 — cost or other basis of property sold", "line_type": "input"},
    {"line_number": "9", "description": "Line 9 — depreciation allowed or allowable", "line_type": "input"},
    {"line_number": "10", "description": "Line 10 — adjusted basis (line 8 − line 9)", "line_type": "calculated"},
    {"line_number": "11", "description": "Line 11 — commissions and other expenses of sale", "line_type": "input"},
    {"line_number": "12", "description": "Line 12 — income recapture from Form 4797 Part III (line 31)",
     "line_type": "input", "destination_form": "Also Form 4797 line 13 (full recapture, year of sale)"},
    {"line_number": "13", "description": "Line 13 — add lines 10, 11, and 12", "line_type": "calculated"},
    {"line_number": "14", "description": "Line 14 — line 5 minus line 13 (if ≤ 0, not an installment sale)", "line_type": "calculated"},
    {"line_number": "15", "description": "Line 15 — §121 excluded gain if main home, else 0", "line_type": "input"},
    {"line_number": "16", "description": "Line 16 — gross profit (line 14 − line 15)", "line_type": "calculated"},
    {"line_number": "17", "description": "Line 17 — line 6 minus line 13 (≥ 0)", "line_type": "calculated"},
    {"line_number": "18", "description": "Line 18 — contract price (line 7 + line 17)", "line_type": "calculated"},
    {"line_number": "19", "description": "Line 19 — gross profit percentage (line 16 ÷ line 18), frozen", "line_type": "calculated"},
    {"line_number": "20", "description": "Line 20 — line 17 in the year of sale, else 0", "line_type": "calculated"},
    {"line_number": "21", "description": "Line 21 — payments received during the year (no interest)", "line_type": "input"},
    {"line_number": "22", "description": "Line 22 — add lines 20 and 21", "line_type": "calculated"},
    {"line_number": "23", "description": "Line 23 — payments received in prior years (no interest)", "line_type": "input"},
    {"line_number": "24", "description": "Line 24 — installment sale income (line 22 × line 19), ≥ 0", "line_type": "calculated"},
    {"line_number": "25", "description": "Line 25 — ordinary recapture portion of line 24",
     "line_type": "total", "destination_form": "Form 4797 line 15 (ordinary gain from installment sales)"},
    {"line_number": "26", "description": "Line 26 — line 24 minus line 25 (the capital/§1231 gain)",
     "line_type": "total", "destination_form": "Form 4797 line 4 / line 10, or Schedule D (by character)"},
    {"line_number": "30", "description": "Line 30 — selling price of property sold by related party", "line_type": "input"},
    {"line_number": "31", "description": "Line 31 — contract price from line 18 (year of first sale)", "line_type": "calculated"},
    {"line_number": "32", "description": "Line 32 — smaller of line 30 or line 31", "line_type": "calculated"},
    {"line_number": "33", "description": "Line 33 — total payments received by end of year (line 22 + line 23)", "line_type": "calculated"},
    {"line_number": "34", "description": "Line 34 — line 32 minus line 33 (≥ 0)", "line_type": "calculated"},
    {"line_number": "35", "description": "Line 35 — line 34 × the year-of-first-sale gross profit %", "line_type": "calculated"},
    {"line_number": "36", "description": "Line 36 — ordinary recapture portion of line 35",
     "line_type": "total", "destination_form": "Form 4797 line 15"},
    {"line_number": "37", "description": "Line 37 — line 35 minus line 36",
     "line_type": "total", "destination_form": "Schedule D or Form 4797 (by character)"},
    {"line_number": "453a", "description": "§453A interest on deferred tax (NOT a 6252 line; Pub 537)",
     "line_type": "total", "destination_form": "Schedule 2 — interest on deferred tax (§453A(c))"},
    {"line_number": "ur1250", "description": "Unrecaptured §1250 portion of line 26 (NOT a 6252 line)",
     "line_type": "total", "destination_form": "Schedule D Unrecaptured §1250 Gain Worksheet (25%)"},
]

P_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_6252_001", "title": "Contingent-payment sale not supported", "severity": "error",
     "condition": "price_not_determinable (line 4 = No)",
     "message": ("The total selling price can't be determined by year end (line 4 = No), so this is a "
                 "contingent-payment sale. Ratable basis recovery / stated-maximum-price computation is "
                 "not modeled in this version — prepare Form 6252 manually (see Temp. Reg. 15a.453-1(c))."),
     "notes": "v1 RED-defer (no silent gap)."},
    {"diagnostic_id": "D_6252_002", "title": "Not an installment sale — line 14 is zero or less", "severity": "error",
     "condition": "line 14 ≤ 0 (no gross profit)",
     "message": ("Line 14 (selling price minus basis, expenses, and recapture) is zero or less. The "
                 "installment method applies only to a sale at a GAIN — don't file Form 6252. Report the "
                 "entire sale on Form 4797, Form 8949, or Schedule D."),
     "notes": "i6252 line 14 / line 24 — losses can't use the installment method (Rev. Rul. 70-430)."},
    {"diagnostic_id": "D_6252_003", "title": "Related-party sale — complete Part III", "severity": "warning",
     "condition": "related_party (line 3 = Yes)",
     "message": ("This sale was to a related party. Complete Part III for the year of sale and the 2 "
                 "following years (unless final payment was received this year). A second disposition by "
                 "the related party within 2 years can accelerate your gain under §453(e)."),
     "notes": "§453(e) reminder."},
    {"diagnostic_id": "D_6252_004", "title": "§453(g) — depreciable property sold to a related person", "severity": "error",
     "condition": "depreciable_to_related_person",
     "message": ("A sale of DEPRECIABLE property to a related person generally cannot use the installment "
                 "method (§453(g)) — all payments are treated as received in the year of sale unless you "
                 "show no significant tax-deferral purpose. Not modeled — prepare manually."),
     "notes": "v1 RED-defer."},
    {"diagnostic_id": "D_6252_005", "title": "§453A interest on deferred tax applies", "severity": "warning",
     "condition": "selling_price > 150000 AND aggregate_obligations_year_end > 5,000,000",
     "message": ("This sale (price over $150,000) plus aggregate nondealer installment obligations over "
                 "$5,000,000 triggers §453A interest on the deferred tax. The interest is computed off "
                 "Form 6252 (Pub 537) and reported on Schedule 2. Verify the aggregate-obligation balance "
                 "and the §6621 rate."),
     "notes": "§453A(c). Lands on Schedule 2."},
    {"diagnostic_id": "D_6252_006", "title": "§453A obligations not entered (price over $150,000)", "severity": "warning",
     "condition": "selling_price > 150000 AND aggregate_obligations_year_end == 0",
     "message": ("This sale's price is over $150,000. §453A interest on deferred tax applies if the "
                 "aggregate face amount of your nondealer installment obligations outstanding at year end "
                 "exceeds $5,000,000. Enter the aggregate balance so the interest can be evaluated."),
     "notes": "Prompts the preparer-asserted §453A input."},
    {"diagnostic_id": "D_6252_007", "title": "§1250 property — confirm the unrecaptured §1250 portion", "severity": "warning",
     "condition": "property_character involves §1250 AND unrecaptured_1250_portion == 0",
     "message": ("For §1250 property (depreciated real property) sold on the installment method, part of "
                 "the line-26 gain may be unrecaptured §1250 gain taxed at up to 25%. Figure it with the "
                 "Unrecaptured §1250 Gain Worksheet in the Schedule D instructions and enter the portion."),
     "notes": "i6252 line 26 — preparer-asserted (v1 boundary)."},
    {"diagnostic_id": "D_6252_008", "title": "§453A(d) pledge rule may treat secured debt as payment", "severity": "info",
     "condition": "selling_price > 150000 (informational)",
     "message": ("If you pledged this installment obligation as security for a debt (sale over $150,000), "
                 "the §453A(d) pledge rule treats the net debt proceeds as a payment received. That "
                 "deemed payment is not auto-computed — include it in payments (line 21) if it applies."),
     "notes": "Pledge-rule deemed payment is preparer-handled in v1."},
]

P_SCENARIOS: list[dict] = [
    {"scenario_name": "F6252-T1 — year of sale, capital asset, simple", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"selling_price": 100000, "cost_basis": 60000, "payments_current_year": 20000,
                "property_character": "capital", "holding_period_months": 24, "is_year_of_sale": True},
     "expected_outputs": {"f6252_line19": 0.40, "f6252_line24": 8000, "f6252_line26": 8000, "sch_d_lt": 8000},
     "notes": "GP 40000 / contract 100000 = 0.40; L24 = 20000 × 0.40 = 8000 → Sch D LT."},
    {"scenario_name": "F6252-T2 — later year, same sale (GP% frozen)", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"selling_price": 100000, "cost_basis": 60000, "is_year_of_sale": False,
                "prior_gross_profit_pct": 0.40, "payments_current_year": 20000, "payments_prior_years": 20000,
                "property_character": "capital", "holding_period_months": 24},
     "expected_outputs": {"f6252_line19": 0.40, "f6252_line24": 8000, "sch_d_lt": 8000},
     "notes": "L20 = 0 (not year of sale); L22 = 20000; L24 = 8000 at the frozen 0.40."},
    {"scenario_name": "F6252-T3 — §1245 recapture full in year of sale; spread is §1231", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"selling_price": 100000, "cost_basis": 60000, "depreciation_allowed": 30000,
                "recapture_from_4797": 30000, "payments_current_year": 25000,
                "property_character": "business_1231", "holding_period_months": 60, "is_year_of_sale": True},
     "expected_outputs": {"f6252_line13": 60000, "f6252_line16": 40000, "f6252_line19": 0.40,
                          "f6252_line24": 10000, "f4797_line4": 10000},
     "notes": ("adj basis 30000 + recapture 30000 = L13 60000; gross profit 40000; GP% 0.40; "
               "L24 = 25000 × 0.40 = 10000 → 4797 line 4 (recapture 30000 sits on 4797 itself).")},
    {"scenario_name": "F6252-T4 — business §1231 → Form 4797 line 4", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"selling_price": 200000, "cost_basis": 120000, "payments_current_year": 50000,
                "property_character": "business_1231", "holding_period_months": 48, "is_year_of_sale": True},
     "expected_outputs": {"f6252_line19": 0.40, "f6252_line24": 20000, "f4797_line4": 20000, "sch_d_lt": 0},
     "notes": "GP 80000/200000 = 0.40; L24 = 50000 × 0.40 = 20000 → 4797 line 4 (not Sch D directly)."},
    {"scenario_name": "F6252-T5 — §453A interest on deferred tax", "scenario_type": "edge_case", "sort_order": 5,
     "inputs": {"selling_price": 10000000, "cost_basis": 2000000, "payments_current_year": 1000000,
                "property_character": "capital", "holding_period_months": 36, "is_year_of_sale": True,
                "aggregate_obligations_year_end": 9000000, "section_6621_rate": 0.08, "max_rate_ltcg": 0.20},
     "expected_outputs": {"f6252_line19": 0.80, "f6252_line24": 800000, "section_453a_interest": 51200},
     "notes": ("GP 8M/10M = 0.80; outstanding = 10M − 1M = 9M; unrecognized 7.2M × 0.20 = DTL 1.44M; "
               "applicable% = (9M−5M)/9M; interest = 1.44M × 4/9 × 0.08 = 51,200.")},
    {"scenario_name": "F6252-T6 — Part III related-party second disposition", "scenario_type": "edge_case", "sort_order": 6,
     "inputs": {"selling_price": 100000, "cost_basis": 60000, "payments_current_year": 20000,
                "property_character": "capital", "holding_period_months": 24, "is_year_of_sale": True,
                "related_party": True, "related_party_resold": True, "rp_selling_price": 80000},
     "expected_outputs": {"f6252_line35": 24000, "f6252_line37": 24000, "sch_d_lt": 32000},
     "notes": ("L31 = 100000; L32 = min(80000,100000) = 80000; L33 = 20000; L34 = 60000; "
               "L35 = 60000 × 0.40 = 24000 → L37; Sch D LT = L26 8000 + L37 24000 = 32000.")},
    {"scenario_name": "F6252-G1 — contingent sale (line 4 = No) → RED-defer", "scenario_type": "diagnostic", "sort_order": 7,
     "inputs": {"selling_price": 100000, "cost_basis": 60000, "price_not_determinable": True},
     "expected_outputs": {"D_6252_001": True},
     "notes": "line 4 = No → contingent payment sale → RED-defer."},
    {"scenario_name": "F6252-G2 — line 14 ≤ 0 → not an installment sale", "scenario_type": "diagnostic", "sort_order": 8,
     "inputs": {"selling_price": 50000, "cost_basis": 80000, "payments_current_year": 10000,
                "property_character": "capital", "holding_period_months": 24, "is_year_of_sale": True},
     "expected_outputs": {"D_6252_002": True},
     "notes": "L14 = 50000 − 80000 = −30000 ≤ 0 → don't file 6252 (report on 4797/8949/Sch D)."},
    {"scenario_name": "F6252-G3 — §453(g) depreciable to related person → RED-defer", "scenario_type": "diagnostic", "sort_order": 9,
     "inputs": {"selling_price": 100000, "cost_basis": 60000, "depreciable_to_related_person": True},
     "expected_outputs": {"D_6252_004": True},
     "notes": "§453(g) bar on installment method for depreciable-property sales to related persons."},
]

P_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-6252-GP", "IRS_2025_6252_FORM", "primary", "Part I lines 5-18 gross profit / contract price"),
    ("R-6252-GP", "IRC_453", "secondary", "§453 installment method definition"),
    ("R-6252-GPPCT", "IRS_2025_6252_FORM", "primary", "Line 19 gross profit % (frozen)"),
    ("R-6252-GPPCT", "IRC_453", "secondary", "§453(c) gross-profit ratio"),
    ("R-6252-INCOME", "IRS_2025_6252_FORM", "primary", "Part II lines 20-26 installment income"),
    ("R-6252-INCOME", "IRC_453", "secondary", "§453(a) income = payments × ratio"),
    ("R-6252-ROUTE", "IRS_2025_6252_FORM", "primary", "Lines 25/26 destinations to Form 4797 lines 15/4/10"),
    ("R-6252-ROUTE", "IRS_2025_4797_INSTR", "secondary", "Form 4797 lines 4 and 15 receive the 6252 amounts"),
    ("R-6252-RELPARTY", "IRC_453_E_G", "primary", "§453(e) related-party second disposition"),
    ("R-6252-RELPARTY", "IRS_2025_6252_FORM", "secondary", "Part III lines 27-37"),
    ("R-6252-453A", "IRC_453A", "primary", "§453A interest on deferred tax"),
    ("R-6252-453A", "IRS_PUB_537", "primary", "Pub 537 §453A worksheet (off-form)"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-6252-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Gross profit % = gross profit / contract price (line 19), frozen",
     "description": "Validates R-6252-GPPCT. Bug it catches: recomputing GP% in a later year instead of using the frozen year-of-sale ratio.",
     "definition": {"kind": "formula_check", "form": "6252",
                    "formula": "L19 = L16 / L18 (year of sale); later years reuse the year-of-sale L19"},
     "sort_order": 1},
    {"assertion_id": "FA-1040-6252-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Installment income = payments × GP% (line 24)",
     "description": "Validates R-6252-INCOME. Bug it catches: spreading recapture or computing income off the wrong payment base.",
     "definition": {"kind": "formula_check", "form": "6252",
                    "formula": "L24 = max(0, (L20 + L21) × L19)"},
     "sort_order": 2},
    {"assertion_id": "FA-1040-6252-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Line 26 capital gain → Schedule D (capital asset)",
     "description": "Validates R-6252-ROUTE for capital assets. Bug it catches: 6252 gain not reaching Schedule D.",
     "definition": {"kind": "flow_assertion", "form": "6252",
                    "checks": [{"source_line": "26", "must_write_to": ["SCH_D"]}]},
     "sort_order": 3},
    {"assertion_id": "FA-1040-6252-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Line 26 §1231 gain → Form 4797 line 4 (closes the 4797 RED-defer)",
     "description": "Validates the 6252 ↔ 4797 interplay. Bug it catches: business installment gain not feeding 4797 line 4.",
     "definition": {"kind": "flow_assertion", "form": "6252",
                    "checks": [{"source_line": "26", "must_write_to": ["F4797.4"]}]},
     "sort_order": 4},
    {"assertion_id": "FA-1040-6252-05", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Ordinary recapture (lines 25/36) → Form 4797 line 15",
     "description": "Validates R-6252-ROUTE ordinary leg. Bug it catches: installment ordinary recapture not landing on 4797 line 15.",
     "definition": {"kind": "flow_assertion", "form": "6252",
                    "checks": [{"source_line": "25", "must_write_to": ["F4797.15"]}]},
     "sort_order": 5},
    {"assertion_id": "FA-1040-6252-06", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "Part III related-party acceleration: L35 = (min(L30,L31) − payments) × GP%",
     "description": "Validates R-6252-RELPARTY. Bug it catches: not accelerating gain on a related party's resale within 2 years.",
     "definition": {"kind": "reconciliation", "form": "6252",
                    "formula": "L34 = max(0, min(L30,L18) − (L22+L23)); L35 = L34 × L19; L37 = L35 − L36"},
     "sort_order": 6},
    {"assertion_id": "FA-1040-6252-07", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "§453A interest = DTL × applicable% × §6621 rate → Schedule 2",
     "description": "Validates R-6252-453A. Bug it catches: charging §453A interest below the $5M gate, or wrong applicable %.",
     "definition": {"kind": "reconciliation", "form": "6252",
                    "formula": "gate price>150k & obligations>5M; interest = (unrecognized_gain × max_rate) × ((agg−5M)/agg) × §6621"},
     "sort_order": 7},
    {"assertion_id": "FA-1040-6252-08", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Gates — contingent sale / §453(g) / line-14≤0 RED-defer",
     "description": "Unsupported paths fire a RED diagnostic and defer — never a silent wrong number.",
     "definition": {"kind": "gating_check", "form": "6252", "expect": {"red_fires": True},
                    "blockers": ["contingent_payment_sale", "depreciable_property_to_related_person"]},
     "sort_order": 8},
]


FORMS: list[dict] = [
    {"identity": P_IDENTITY, "facts": P_FACTS, "rules": P_RULES, "lines": P_LINES,
     "diagnostics": P_DIAGNOSTICS, "scenarios": P_SCENARIOS, "rule_links": P_RULE_LINKS},
]


class Command(BaseCommand):
    help = "Load the Form 6252 spec (Installment Sale Income). Refuses until READY_TO_SEED=True."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad Form 6252 spec (Installment Sale Income)\n"))
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
                "\nREFUSING TO SEED Form 6252: not cleared to seed.\n\n"
                "Gated until Ken's review walk (the gross-profit %/contract-price arithmetic, the\n"
                "4797 line-4/15 routing closure, the Part III related-party acceleration, the §453A\n"
                "worksheet, and the preparer-asserted boundaries).\n\n"
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
        self.stdout.write(f"{'Created' if created else 'Updated'} Form {identity['form_number']}")
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
        form = TaxForm.objects.filter(form_number="6252").order_by("-version").first()
        if form:
            uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
            self.stdout.write("Form 6252: all rules cited" if not uncited
                              else self.style.WARNING(f"Form 6252 uncited rules: {len(uncited)}"))
