"""Load the FORM_1116 spec — Foreign Tax Credit (§901/§904), Passive-only v1.

Phase 2 / next common form (Ken chose 2026-06-26). Two scope decisions:
  (1) FULL Form 1116 over the §904(j)-shortcut-only build;
  (2) "Tighter v1 — Passive-only": build the §904(j) election shortcut + the FULL
      Passive-category §904 limitation for the *adjustment-exception* case + carryover
      in/out; RED-defer General category, the above-exception QD adjustment, and every
      exotic provision (each its own D_1116_* — no silent gap, the 5329/2210 philosophy).

LAW VERIFIED 2026-06-26 (brief tts-tax-app server/specs/_1116_source_brief.md), read
directly from the 2025 Form 1116 (created 9/16/25) + i1116 (Dec 23 2025) + IRC §901/§904:
  §904(j) election: all foreign income passive + on a 1099/K-1/K-3 + total creditable
    foreign tax <= $300 ($600 MFJ) → credit = min(foreign tax, regular tax) → Sch 3 L1,
    NO carryover. Not for estates/trusts.
  Full Passive limitation: Part I L7 = foreign-source TI (deduction apportionment L3a-g,
    interest L4); Part III L19 = L17/L18, L21 = L20 × L19 (the §904 cap), L24 = min(L14,
    L23); Part IV L35 → Sch 3 L1; unused foreign tax (L14 − L24) carries forward.
  L18 = (1040 L11b − L14) + Sch 1-A L37 — Sch 1-A L37 = the SENIOR deduction only (verified
    i1116) → in our model L18 = 1040 line 15 + Sch 1-A line 37. L20 = 1040 L16 + Sch 2 L1z.
  Adjustment exception (skip the QD/cap-gain L1a adjustment): taxable income <= $394,600
    MFJ/QSS · $197,300 Single/MFS/HOH (2025) AND foreign QD + net cap gain < $20,000.

v1 RED-defers (each a diagnostic): non-passive category, the above-exception QD
  adjustment, high-tax kickout (L13), Form 2555 reduction (L12), §960(c) (L22), boycott
  (L34), AMT 1116, carryover-needs-Schedule-B, foreign cap gains needing Pub 514 WS A/B,
  >3 countries, accrued (vs paid), Form 4972 in L20.

SAFETY GUARD: READY_TO_SEED stays False until Ken's review walk (the §904(j) ceilings, the
limitation arithmetic, the L18/L20 mappings, the adjustment-exception thresholds).
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


READY_TO_SEED = True  # FLIPPED 2026-06-26 — Ken approved the review walk ("Approve — seed it").


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_ENTITY_TYPES = ["1040"]
FORM_STATUS = "draft"

# ── §904 / §904(j) constants (verified vs 2025 f1116 + i1116) ──
ELECT_CEILING = 300                 # §904(j) — total creditable foreign tax ceiling
ELECT_CEILING_MFJ = 600
ADJ_EXCEPTION_GAIN_CEILING = 20000  # foreign QD + net cap gain (regulatory, NOT indexed)
# Adjustment-exception taxable-income threshold (= the 24%/32% bracket boundary), per year:
ADJ_EXCEPTION_TI = {
    2025: {"mfj": 394600, "qss": 394600, "single": 197300, "mfs": 197300, "hoh": 197300},
    # TY2026 INTERIM — the verified 2026 §199A threshold (RP 2025-32 §4.26; identical bracket
    # basis, equal for 2025). Re-pin from the published 2026 i1116 (~Dec 2026):
    2026: {"mfj": 403500, "qss": 403500, "single": 201750, "mfs": 201750, "hoh": 201750},
}
_LATEST_TI_YEAR = 2026


from decimal import ROUND_HALF_UP, Decimal  # noqa: E402


def _D(x):
    return Decimal(str(x if x is not None else 0))


def _r0(x):
    return int(_D(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def adj_exception_ti(tax_year, filing_status) -> Decimal:
    table = ADJ_EXCEPTION_TI.get(int(tax_year)) or ADJ_EXCEPTION_TI[_LATEST_TI_YEAR]
    return _D(table.get((filing_status or "single").lower(), table["single"]))


def elect_ceiling(filing_status) -> int:
    return ELECT_CEILING_MFJ if (filing_status or "single").lower() in ("mfj", "qss") else ELECT_CEILING


# ── Pure functions (mirror the tts compute; check_1116_integrity.py re-types) ──


def red_defer_reasons(*, category="passive", has_form_2555=False, foreign_qd=0,
                      foreign_net_cap_gain=0, tax_year=2025, filing_status="single",
                      taxable_income=0, high_tax_kickout=False, section_960c=False,
                      boycott=False, has_form_4972=False) -> list:
    """Enumerate the v1 RED-defer reasons (each a no-silent-gap diagnostic)."""
    reasons = []
    if (category or "passive").lower() != "passive":
        reasons.append("non_passive_category")
    foreign_pref = _D(foreign_qd) + _D(foreign_net_cap_gain)
    if foreign_pref > 0:
        within = (_D(taxable_income) <= adj_exception_ti(tax_year, filing_status)
                  and foreign_pref < ADJ_EXCEPTION_GAIN_CEILING)
        if not within:
            reasons.append("qd_adjustment_above_exception")
    if has_form_2555:
        reasons.append("form_2555_reduction")
    if high_tax_kickout:
        reasons.append("high_tax_kickout")
    if section_960c:
        reasons.append("section_960c")
    if boycott:
        reasons.append("boycott")
    if has_form_4972:
        reasons.append("form_4972_lump_sum")
    return reasons


def compute_part1(*, foreign_source_income=0, definitely_related=0, deduction_apportion=0,
                  other_deductions=0, gross_foreign_source=0, gross_income_all=0,
                  home_mortgage_interest=0, other_interest=0, foreign_losses=0) -> dict:
    """Part I — foreign-source taxable income. L3 pro-rata apportionment + L4 interest → L7."""
    l1a = _D(foreign_source_income)
    l2 = _D(definitely_related)
    l3a, l3b = _D(deduction_apportion), _D(other_deductions)
    l3c = l3a + l3b
    l3d, l3e = _D(gross_foreign_source), _D(gross_income_all)
    l3f = (l3d / l3e).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP) if l3e > 0 else Decimal("0")
    l3g = _D(_r0(l3c * l3f))
    l4a, l4b, l5 = _D(home_mortgage_interest), _D(other_interest), _D(foreign_losses)
    l6 = l2 + l3g + l4a + l4b + l5
    l7 = l1a - l6
    return {"l1a": l1a, "l3c": l3c, "l3f": l3f, "l3g": l3g, "l6": l6, "l7": l7}


def compute_1116(*, tax_year=2025, filing_status="single",
                 elect_simplified=False, foreign_tax_total=0, regular_tax=0,
                 # Part I
                 foreign_source_income=0, definitely_related=0, deduction_apportion=0,
                 other_deductions=0, gross_foreign_source=0, gross_income_all=0,
                 home_mortgage_interest=0, other_interest=0, foreign_losses=0,
                 # Part III
                 carryover=0, taxable_income=0, senior_deduction=0,
                 # gates
                 category="passive", has_form_2555=False, foreign_qd=0, foreign_net_cap_gain=0,
                 high_tax_kickout=False, section_960c=False, boycott=False, has_form_4972=False) -> dict:
    """The full §901/§904 chain (Passive-only v1). Returns the credit → Schedule 3 line 1,
    the carryforward, and the form lines; or red_defer (credit None) on an unsupported path."""
    reasons = red_defer_reasons(
        category=category, has_form_2555=has_form_2555, foreign_qd=foreign_qd,
        foreign_net_cap_gain=foreign_net_cap_gain, tax_year=tax_year, filing_status=filing_status,
        taxable_income=taxable_income, high_tax_kickout=high_tax_kickout,
        section_960c=section_960c, boycott=boycott, has_form_4972=has_form_4972)
    if reasons:
        return {"red_defer": reasons, "credit": None, "carryforward": Decimal("0")}

    ceiling = elect_ceiling(filing_status)
    # ── Path A — §904(j) election (no Form 1116) ──
    if elect_simplified:
        if _D(foreign_tax_total) > ceiling:
            return {"red_defer": ["election_over_ceiling"], "credit": None,
                    "carryforward": Decimal("0"), "election_invalid": True}
        credit = min(_D(foreign_tax_total), _D(regular_tax))
        return {"path": "election", "credit": credit, "sch3_line1": credit,
                "carryforward": Decimal("0")}

    # ── Path B — full Passive-category §904 limitation ──
    p1 = compute_part1(
        foreign_source_income=foreign_source_income, definitely_related=definitely_related,
        deduction_apportion=deduction_apportion, other_deductions=other_deductions,
        gross_foreign_source=gross_foreign_source or foreign_source_income,
        gross_income_all=gross_income_all, home_mortgage_interest=home_mortgage_interest,
        other_interest=other_interest, foreign_losses=foreign_losses)
    l7 = p1["l7"]
    l8 = _D(foreign_tax_total)
    l9 = l8
    l10 = _D(carryover)
    l11 = l9 + l10
    l14 = l11                                   # L12=L13=0 in v1
    l15 = l7
    l17 = l15                                   # L16=0 in v1
    l18 = max(Decimal("0"), _D(taxable_income) + _D(senior_deduction))
    if l17 <= 0 or l18 <= 0:
        l19 = Decimal("0")
    elif l17 > l18:
        l19 = Decimal("1")
    else:
        l19 = (l17 / l18).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    l20 = _D(regular_tax)
    l21 = _D(_r0(l20 * l19))
    l23 = l21                                   # L22=0 in v1
    l24 = min(l14, l23)
    l32 = l24                                    # only L27 (passive) populated
    l33 = min(l20, l32)
    l35 = l33                                    # L34=0 in v1
    carryforward = max(Decimal("0"), l14 - l24)
    return {"path": "full", "l7": l7, "l8": l8, "l14": l14, "l17": l17, "l18": l18,
            "l19": l19, "l20": l20, "l21": l21, "l24": l24, "l32": l32, "l33": l33,
            "credit": l35, "sch3_line1": l35, "carryforward": carryforward}


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("foreign_tax_credit", "Foreign tax credit (§901/§904) — the §904(j) election and the per-category §904 limitation; Form 1116 → Schedule 3 line 1"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_1040_FORM",
    "IRS_2025_1040_INSTR",
]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_F1116_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Form 1116 — Foreign Tax Credit (Individual, Estate, or Trust)",
        "citation": "Form 1116 (2025), Parts I-IV (created 9/16/25)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f1116.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": "The line structure: Part I L1a-L7 (foreign-source TI), Part II L8 (foreign tax), Part III L9-L24 (the §904 limitation), Part IV L25-L35 → Schedule 3 line 1.",
        "topics": ["foreign_tax_credit"],
        "excerpts": [
            {
                "excerpt_label": "Part III — the §904 limitation (lines 18-24)",
                "location_reference": "f1116 (2025), Part III lines 18-24",
                "excerpt_text": (
                    "Line 18: Individuals enter the sum of (i) Form 1040 line 11b minus line 14, and (ii) "
                    "Schedule 1-A line 37. Line 19: divide line 17 by line 18 (if line 17 is more than line 18, "
                    "enter '1'). Line 20: enter the total of Form 1040 line 16 and Schedule 2 line 1z. Line 21: "
                    "multiply line 20 by line 19 (the maximum amount of credit). Line 24: enter the smaller of "
                    "line 14 or line 23."
                ),
                "summary_text": "L18 = taxable income + senior deduction; L19 = L17/L18; L21 = L20 × L19 (the §904 cap); L24 = min(L14, L23).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part IV — summary → Schedule 3 line 1",
                "location_reference": "f1116 (2025), Part IV lines 32-35",
                "excerpt_text": (
                    "Line 32: add lines 25 through 31. Line 33: enter the smaller of line 20 or line 32. Line 34: "
                    "reduction of credit for international boycott operations. Line 35: subtract line 34 from line "
                    "33. This is your foreign tax credit. Enter here and on Schedule 3 (Form 1040), line 1."
                ),
                "summary_text": "L33 = min(L20, L32); L35 = L33 − L34 → Schedule 3 line 1.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_F1116_INSTR",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Form 1116 — Foreign Tax Credit",
        "citation": "Instructions for Form 1116 (2025), Dec 23 2025",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/instructions/i1116",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": "The §904(j) election ($300/$600), the categories of income, the QD/cap-gain adjustment + the adjustment exception ($394,600/$197,300 + $20,000), the line-18 senior-deduction add-back, the line-20 regular-tax definition. REQUIRES HUMAN REVIEW: v1 computes only the adjustment-exception case + Passive category; everything else RED-defers.",
        "topics": ["foreign_tax_credit"],
        "excerpts": [
            {
                "excerpt_label": "§904(j) — claim the FTC without filing Form 1116",
                "location_reference": "i1116 (2025), 'Foreign Tax Credit Without Filing Form 1116'",
                "excerpt_text": (
                    "You may be able to claim the foreign tax credit without filing Form 1116. This election is "
                    "available only if all of your foreign source gross income was passive category income, all "
                    "the income and any foreign taxes paid were reported on a qualified payee statement (Form "
                    "1099-DIV, 1099-INT, Schedule K-1, K-3), and your total creditable foreign taxes aren't more "
                    "than $300 ($600 if married filing a joint return). To make the election, enter on Schedule 3 "
                    "line 1 the smaller of your total foreign tax or your regular tax."
                ),
                "summary_text": "All passive + payee-statement + foreign tax ≤ $300/$600 → credit = min(foreign tax, regular tax) → Sch 3 L1, no 1116.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "The adjustment exception (skip the QD/cap-gain L1a adjustment)",
                "location_reference": "i1116 (2025), Qualified Dividends and Capital Gain Tax Worksheet (Individuals)",
                "excerpt_text": (
                    "You qualify for the adjustment exception if you meet both of the following: (1) Line 5 of the "
                    "Qualified Dividends and Capital Gain Tax Worksheet doesn't exceed $394,600 if married filing "
                    "jointly or qualifying surviving spouse, or $197,300 if single, married filing separately, or "
                    "head of household; and (2) the amount of your foreign source capital gain distributions plus "
                    "your foreign source qualified dividends is less than $20,000. If you qualify and elect not to "
                    "adjust, include the foreign source qualified dividends and capital gain distributions without "
                    "adjustment on line 1a."
                ),
                "summary_text": "Exception (no adjustment): TI ≤ $394,600 MFJ/$197,300 other AND foreign QD+gain < $20,000.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Line 18 — the senior-deduction add-back",
                "location_reference": "i1116 (2025), Line 18",
                "excerpt_text": (
                    "Individuals: Enter on line 18 the sum of (i) Form 1040 line 11b minus line 14, and (ii) "
                    "Schedule 1-A line 37. [The senior deduction] is reported on Schedule 1-A line 37 and needs to "
                    "be removed from taxable income for purposes of computing the foreign tax credit limitation."
                ),
                "summary_text": "L18 = (1040 11b − 14) + Sch 1-A L37; Sch 1-A L37 = the senior deduction only.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_901_904",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §901 (Foreign Tax Credit) and §904 (Limitation)",
        "citation": "26 U.S.C. §901, §904 (incl. §904(j) the de-minimis election)",
        "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:904%20edition:prelim)",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "§901 allows the credit for foreign income taxes; §904(a) limits it to US tax × (foreign-source TI / total TI); §904(c) carryback 1 / carryforward 10; §904(j) the $300/$600 election without Form 1116.",
        "topics": ["foreign_tax_credit"],
        "excerpts": [
            {
                "excerpt_label": "§904(a) the limitation",
                "location_reference": "26 U.S.C. §904(a)",
                "excerpt_text": (
                    "The total amount of the credit taken under section 901(a) shall not exceed the same "
                    "proportion of the tax against which such credit is taken which the taxpayer's taxable income "
                    "from sources without the United States bears to his entire taxable income for the same "
                    "taxable year."
                ),
                "summary_text": "FTC ≤ US tax × (foreign-source taxable income / total taxable income) — the per-category limitation.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§904(j) the de-minimis election",
                "location_reference": "26 U.S.C. §904(j)",
                "excerpt_text": (
                    "In the case of an individual whose entire foreign source gross income is passive income "
                    "reported on a qualified payee statement and whose creditable foreign taxes don't exceed $300 "
                    "($600 in the case of a joint return), the limitation of subsection (a) shall not apply and no "
                    "carryback or carryover is allowed."
                ),
                "summary_text": "§904(j): all-passive + payee-statement + ≤ $300/$600 → no limitation, no carryover.",
                "is_key_excerpt": True,
            },
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_F1116_FORM", "FORM_1116", "governs"),
    ("IRS_2025_F1116_INSTR", "FORM_1116", "governs"),
    ("IRC_901_904", "FORM_1116", "governs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM: FORM_1116
# ═══════════════════════════════════════════════════════════════════════════

P_IDENTITY = {
    "form_number": "FORM_1116",
    "form_title": "Form 1116 Foreign Tax Credit (§901/§904) (TY2025)",
    "notes": (
        "Ken's 2 scope decisions 2026-06-26: FULL Form 1116, Passive-only v1. Path A — the "
        "§904(j) election (all passive + payee-statement + foreign tax ≤ $300/$600) → credit = "
        "min(foreign tax, regular tax) → Schedule 3 line 1, no carryover. Path B — the full "
        "Passive-category §904 limitation: Part I L7 = foreign-source TI (deduction apportionment "
        "L3a-g + interest L4), Part III L21 = L20 × (L17/L18) the §904 cap, L24 = min(L14, L23), "
        "Part IV L35 → Schedule 3 line 1; unused foreign tax (L14 − L24) carries forward. L18 = "
        "1040 line 15 + Sch 1-A line 37 (senior deduction); L20 = 1040 line 16 + Sch 2 line 1z. v1 "
        "computes only the adjustment-exception case (TI ≤ $394,600/$197,300 AND foreign QD+gain < "
        "$20,000); the above-exception QD adjustment + non-passive category + every exotic provision "
        "RED-defer (requires_human_review). AMENDED 2026-07-01 (Ken-approved): Path A now applies "
        "AUTOMATICALLY when the only foreign tax is from 1099-INT/1099-DIV ≤ $300/$600 and no full Form "
        "1116 is engaged (opt-out via f1116_deminimis_optout); D_1116_001 → 'auto-applied'; new D_1116_009 "
        "nudges when the 1099 foreign tax is over the ceiling with no Form 1116 engaged (closes a silent gap)."
    ),
}

P_FACTS: list[dict] = [
    # ── election + category ──
    {"fact_key": "f1116_elect_simplified", "label": "Elect the §904(j) credit without Form 1116?",
     "data_type": "boolean", "default_value": "false", "sort_order": 1,
     "notes": "Path A — requires all passive + payee-statement + foreign tax ≤ $300/$600."},
    {"fact_key": "f1116_category", "label": "Category of income (v1: passive)",
     "data_type": "string", "default_value": "passive", "sort_order": 2,
     "notes": "Non-passive → RED-defer (D_1116_003)."},
    {"fact_key": "f1116_deminimis_optout", "label": "Opt out of the automatic §904(j) de minimis credit?",
     "data_type": "boolean", "default_value": "false", "sort_order": 3,
     "notes": ("When the ONLY creditable foreign tax is from 1099-INT/1099-DIV (passive + payee-statement "
               "by definition), the total ≤ $300/$600, and no full Form 1116 is engaged, the §904(j) credit "
               "is applied AUTOMATICALLY (min(foreign tax, regular tax) → Sch 3 line 1, no carryover). Set "
               "this to opt out — the preparer then handles foreign tax manually (full Form 1116 or a "
               "Schedule A deduction). A return-level election, not a Form 1116 row field (the auto-path "
               "must work with no Form 1116 engaged).")},
    # ── Part I inputs ──
    {"fact_key": "f1116_foreign_source_income", "label": "Gross foreign source income (line 1a)",
     "data_type": "decimal", "default_value": "0", "sort_order": 10,
     "notes": "Preparer input — NOT on the 1099 (only the tax is)."},
    {"fact_key": "f1116_definitely_related", "label": "Expenses definitely related (line 2)",
     "data_type": "decimal", "default_value": "0", "sort_order": 11},
    {"fact_key": "f1116_deduction_apportion", "label": "Standard/certain itemized deduction (line 3a)",
     "data_type": "decimal", "default_value": "0", "sort_order": 12, "notes": "Auto = 1040 line 12; apportioned by L3f."},
    {"fact_key": "f1116_other_deductions", "label": "Other deductions not definitely related (line 3b)",
     "data_type": "decimal", "default_value": "0", "sort_order": 13},
    {"fact_key": "f1116_gross_income_all", "label": "Gross income from all sources (line 3e)",
     "data_type": "decimal", "default_value": "0", "sort_order": 14, "notes": "Auto = 1040 total income."},
    {"fact_key": "f1116_home_mortgage_interest", "label": "Home mortgage interest apportioned (line 4a)",
     "data_type": "decimal", "default_value": "0", "sort_order": 15},
    {"fact_key": "f1116_other_interest", "label": "Other interest expense apportioned (line 4b)",
     "data_type": "decimal", "default_value": "0", "sort_order": 16},
    {"fact_key": "f1116_foreign_losses", "label": "Losses from foreign sources (line 5)",
     "data_type": "decimal", "default_value": "0", "sort_order": 17},
    # ── Part III inputs ──
    {"fact_key": "f1116_carryover", "label": "Prior-year carryover + carryback (line 10)",
     "data_type": "decimal", "default_value": "0", "sort_order": 20, "notes": "Entered → must attach Schedule B (D_1116_005)."},
    {"fact_key": "f1116_additional_foreign_tax", "label": "Additional foreign tax beyond the 1099 aggregate (K-1, etc.)",
     "data_type": "decimal", "default_value": "0", "sort_order": 21},
    # ── adjustment-exception gate ──
    {"fact_key": "f1116_foreign_qualified_dividends", "label": "Foreign source qualified dividends (exception gate)",
     "data_type": "decimal", "default_value": "0", "sort_order": 25},
    {"fact_key": "f1116_foreign_net_capital_gain", "label": "Foreign source net capital gain (exception gate)",
     "data_type": "decimal", "default_value": "0", "sort_order": 26},
    # ── red-defer flags ──
    {"fact_key": "f1116_has_form_2555", "label": "Form 2555 (foreign earned income exclusion) present?",
     "data_type": "boolean", "default_value": "false", "sort_order": 30, "notes": "→ line 12 reduction not modeled (RED-defer)."},
    # ── outputs ──
    {"fact_key": "f1116_line7", "label": "Net foreign source taxable income (line 7)",
     "data_type": "decimal", "sort_order": 50, "notes": "OUTPUT."},
    {"fact_key": "f1116_line24", "label": "Category credit (line 24 = min(L14, L23))",
     "data_type": "decimal", "sort_order": 51, "notes": "OUTPUT."},
    {"fact_key": "f1116_line35", "label": "Foreign tax credit → Schedule 3 line 1 (line 35)",
     "data_type": "decimal", "sort_order": 52, "notes": "OUTPUT — the credit."},
    {"fact_key": "f1116_carryforward", "label": "Unused foreign tax carried forward (L14 − L24)",
     "data_type": "decimal", "sort_order": 53, "notes": "OUTPUT — 1-back/10-forward."},
]

P_RULES: list[dict] = [
    {"rule_id": "R-1116-ELECT", "title": "§904(j) election — credit without Form 1116 (auto-applied)", "rule_type": "calculation",
     "precedence": 1, "sort_order": 1,
     "formula": ("The §904(j) de minimis election applies AUTOMATICALLY when the only creditable foreign tax "
                 "is from 1099-INT/1099-DIV (passive category + payee-statement by definition), the total ≤ "
                 "ceiling ($300; $600 MFJ/QSS), no full Form 1116 is engaged, and the preparer has NOT opted "
                 "out (f1116_deminimis_optout) — OR when the preparer explicitly checks elect_simplified on an "
                 "engaged Form 1116. Either way: credit = min(foreign_tax_total, regular_tax) → Schedule 3 "
                 "line 1, no carryover. If an engaged Form 1116 elects but foreign tax > ceiling → invalid "
                 "(D_1116_002). If the 1099 foreign tax > ceiling with no Form 1116 engaged → NOT auto-applied; "
                 "nudge to file the full Form 1116 (D_1116_009)."),
     "inputs": ["f1116_elect_simplified", "f1116_deminimis_optout", "f1116_additional_foreign_tax"],
     "outputs": ["f1116_line35"],
     "description": "§904(j). All passive + payee-statement + foreign tax ≤ $300/$600 → auto-applied unless opted out."},
    {"rule_id": "R-1116-PART1", "title": "Part I — foreign-source taxable income (L1a-L7)", "rule_type": "calculation",
     "precedence": 2, "sort_order": 2,
     "formula": ("L3c = L3a + L3b; L3f = L3d/L3e (4 dp); L3g = round(L3c × L3f); L6 = L2 + L3g + L4a + "
                 "L4b + L5; L7 = L1a − L6. L3a = the standard/certain itemized deduction; L3d = gross "
                 "foreign source income; L3e = gross income all sources."),
     "inputs": ["f1116_foreign_source_income", "f1116_definitely_related", "f1116_deduction_apportion",
                "f1116_other_deductions", "f1116_gross_income_all", "f1116_home_mortgage_interest",
                "f1116_other_interest", "f1116_foreign_losses"],
     "outputs": ["f1116_line7"],
     "description": "Part I deduction apportionment (§861-865) → net foreign source TI."},
    {"rule_id": "R-1116-LIMIT", "title": "Part III — the §904 limitation (L9-L24)", "rule_type": "calculation",
     "precedence": 3, "sort_order": 3,
     "formula": ("L9 = L8 foreign tax; L11 = L9 + L10 carryover; L14 = L11 (L12=L13=0 v1); L15 = L7; "
                 "L17 = L15 (L16=0 v1); L18 = max(0, taxable_income + senior_deduction); L19 = L17/L18 "
                 "(cap 1; 0 if L18≤0); L20 = 1040 L16 + Sch 2 L1z; L21 = round(L20 × L19); L23 = L21 "
                 "(L22=0 v1); L24 = min(L14, L23)."),
     "inputs": ["f1116_carryover"], "outputs": ["f1116_line24"],
     "description": "§904(a) the limitation fraction → the category credit."},
    {"rule_id": "R-1116-SUMMARY", "title": "Part IV — summary → Schedule 3 line 1", "rule_type": "calculation",
     "precedence": 4, "sort_order": 4,
     "formula": ("L32 = Σ L25-31 (v1 = L27 passive = L24); L33 = min(L20, L32); L35 = L33 − L34 "
                 "(L34=0 v1) → Schedule 3 line 1."),
     "inputs": [], "outputs": ["f1116_line35"],
     "description": "Part IV combines the categories → the foreign tax credit."},
    {"rule_id": "R-1116-CARRY", "title": "Carryforward — unused foreign tax (L14 − L24)", "rule_type": "calculation",
     "precedence": 5, "sort_order": 5,
     "formula": "carryforward = max(0, L14 − L24); carries back 1 / forward 10 (§904(c)).",
     "inputs": [], "outputs": ["f1116_carryforward"],
     "description": "§904(c). v1 reports the current-year carryforward; full Schedule B reconciliation deferred."},
]

P_LINES: list[dict] = [
    {"line_number": "1a", "description": "Line 1a — gross foreign source income", "line_type": "input"},
    {"line_number": "2", "description": "Line 2 — expenses definitely related", "line_type": "input"},
    {"line_number": "3a", "description": "Line 3a — standard/certain itemized deduction", "line_type": "input"},
    {"line_number": "3b", "description": "Line 3b — other deductions not definitely related", "line_type": "input"},
    {"line_number": "3c", "description": "Line 3c — add 3a and 3b", "line_type": "calculated"},
    {"line_number": "3d", "description": "Line 3d — gross foreign source income", "line_type": "input"},
    {"line_number": "3e", "description": "Line 3e — gross income from all sources", "line_type": "input"},
    {"line_number": "3f", "description": "Line 3f — divide 3d by 3e", "line_type": "calculated"},
    {"line_number": "3g", "description": "Line 3g — multiply 3c by 3f", "line_type": "calculated"},
    {"line_number": "4a", "description": "Line 4a — home mortgage interest apportioned", "line_type": "input"},
    {"line_number": "4b", "description": "Line 4b — other interest expense apportioned", "line_type": "input"},
    {"line_number": "5", "description": "Line 5 — losses from foreign sources", "line_type": "input"},
    {"line_number": "6", "description": "Line 6 — add 2, 3g, 4a, 4b, 5", "line_type": "calculated"},
    {"line_number": "7", "description": "Line 7 — line 1a − line 6 (net foreign source TI)", "line_type": "calculated"},
    {"line_number": "8", "description": "Line 8 — total foreign taxes paid or accrued", "line_type": "input"},
    {"line_number": "9", "description": "Line 9 — total foreign taxes (from line 8)", "line_type": "calculated"},
    {"line_number": "10", "description": "Line 10 — carryover + carryback", "line_type": "input"},
    {"line_number": "11", "description": "Line 11 — add 9 and 10", "line_type": "calculated"},
    {"line_number": "14", "description": "Line 14 — total foreign taxes available for credit", "line_type": "calculated"},
    {"line_number": "15", "description": "Line 15 — net foreign source TI (from line 7)", "line_type": "calculated"},
    {"line_number": "17", "description": "Line 17 — net foreign source TI after adjustments", "line_type": "calculated"},
    {"line_number": "18", "description": "Line 18 — taxable income + Sch 1-A line 37 (senior deduction)", "line_type": "calculated"},
    {"line_number": "19", "description": "Line 19 — divide line 17 by line 18 (the limitation fraction)", "line_type": "calculated"},
    {"line_number": "20", "description": "Line 20 — 1040 line 16 + Schedule 2 line 1z (regular tax)", "line_type": "calculated"},
    {"line_number": "21", "description": "Line 21 — multiply line 20 by line 19 (the §904 cap)", "line_type": "calculated"},
    {"line_number": "23", "description": "Line 23 — add 21 and 22", "line_type": "calculated"},
    {"line_number": "24", "description": "Line 24 — smaller of line 14 or line 23 (category credit)", "line_type": "calculated"},
    {"line_number": "27", "description": "Line 27 — credit for taxes on passive category income", "line_type": "calculated"},
    {"line_number": "32", "description": "Line 32 — add lines 25 through 31", "line_type": "calculated"},
    {"line_number": "33", "description": "Line 33 — smaller of line 20 or line 32", "line_type": "calculated"},
    {"line_number": "35", "description": "Line 35 — foreign tax credit → Schedule 3 line 1", "line_type": "total"},
    {"line_number": "sch3_1", "description": "Schedule 3 line 1 — foreign tax credit", "line_type": "total"},
]

P_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_1116_001", "title": "§904(j) de minimis credit applied automatically", "severity": "info",
     "condition": "foreign tax from 1099s ≤ ceiling, all passive, no full Form 1116 engaged, not opted out",
     "message": ("The de minimis foreign tax from your 1099s is within the §904(j) ceiling ($300; $600 MFJ) "
                 "and is all passive income from payee statements, so the foreign tax credit is claimed "
                 "AUTOMATICALLY on Schedule 3 line 1 (the smaller of the foreign tax or your regular tax) — "
                 "no Form 1116 is filed and no carryover is allowed. Open the Foreign Tax Credit tab to opt "
                 "out or to file the full Form 1116 instead."),
     "notes": "§904(j). Auto-applied (the common mutual-fund-dividend case). Opt-out = f1116_deminimis_optout."},
    {"diagnostic_id": "D_1116_002", "title": "§904(j) election claimed but foreign tax exceeds the ceiling", "severity": "error",
     "condition": "elect_simplified AND foreign tax > $300 ($600 MFJ)",
     "message": ("The §904(j) election was claimed but the total creditable foreign tax exceeds $300 "
                 "($600 if married filing jointly) — the election is NOT available. File the full Form "
                 "1116 instead. The credit is deferred until the election is cleared or the full form "
                 "is completed."),
     "notes": "No silent gap — the election ceiling is hard."},
    {"diagnostic_id": "D_1116_003", "title": "Non-passive category — not supported (prepare manually)", "severity": "error",
     "condition": "category != passive",
     "message": ("This Form 1116 is for a non-passive category (general, §951A/GILTI, foreign branch, "
                 "§901(j), treaty-resourced, or lump-sum). Only the passive category is supported in "
                 "this version — prepare this category's Form 1116 manually."),
     "notes": "v1 Passive-only (RED-defer)."},
    {"diagnostic_id": "D_1116_004", "title": "Qualified-dividend adjustment required — not supported", "severity": "error",
     "condition": "foreign QD + net cap gain ≥ $20,000 OR taxable income above the threshold",
     "message": ("The foreign source qualified dividends / capital gains require the rate-differential "
                 "adjustment (foreign QD+gain ≥ $20,000, or taxable income above the adjustment-exception "
                 "threshold). This version computes only the adjustment-exception case — prepare the "
                 "Form 1116 line 1a / line 18 adjustment (×0.4054 / ×0.5405) manually."),
     "notes": "§904(b)(2)(B). v1 computes only the exception case."},
    {"diagnostic_id": "D_1116_005", "title": "Carryover entered — attach Schedule B", "severity": "warning",
     "condition": "line 10 carryover > 0",
     "message": ("A foreign tax carryover/carryback is entered on line 10. You must attach Schedule B "
                 "(Form 1116) to reconcile the prior-year and current-year carryover — this version does "
                 "not generate Schedule B."),
     "notes": "v1 — carryover as input; Schedule B reconciliation deferred."},
    {"diagnostic_id": "D_1116_006", "title": "Form 2555 present — line 12 reduction not modeled", "severity": "error",
     "condition": "has_form_2555",
     "message": ("Form 2555 (foreign earned income exclusion) is present. Form 1116 line 12 must reduce "
                 "the foreign taxes allocable to the excluded income — this version does not model that "
                 "reduction. Prepare the Form 1116 line 12 reduction manually."),
     "notes": "v1 — Form 2555 interaction deferred."},
    {"diagnostic_id": "D_1116_007", "title": "TY2026 — re-verify the adjustment-exception threshold", "severity": "warning",
     "condition": "tax_year == 2026 AND the full Form 1116 is computed",
     "message": ("This 2026 return uses an INTERIM adjustment-exception taxable-income threshold (the "
                 "2026 §199A/24%-bracket figure). Re-pin it from the published 2026 Instructions for Form "
                 "1116 (~Dec 2026)."),
     "notes": "Re-pin the 2026 indexed threshold."},
    {"diagnostic_id": "D_1116_008", "title": "Unused foreign tax carries forward", "severity": "info",
     "condition": "line 14 > line 24 (the limitation binds)",
     "message": ("The §904 limitation caps the credit below the foreign tax available — the unused "
                 "foreign tax (line 14 − line 24) carries back 1 year and forward 10 years. Track it for "
                 "next year (Schedule B)."),
     "notes": "§904(c)."},
    {"diagnostic_id": "D_1116_009", "title": "Foreign tax over the §904(j) ceiling — no Form 1116 engaged", "severity": "warning",
     "condition": "foreign tax from 1099s > ceiling ($300/$600) AND no Form 1116 engaged",
     "message": ("The foreign tax from your 1099s exceeds the §904(j) de minimis ceiling ($300; $600 MFJ), so "
                 "the credit is NOT applied automatically, and no Form 1116 is engaged — the foreign tax "
                 "credit is currently unclaimed. Open the Foreign Tax Credit tab to file the full Form 1116 "
                 "(passive category) and claim it, or take the foreign tax as a Schedule A deduction."),
     "notes": ("Closes the silent gap: >ceiling foreign tax with no Form 1116 would otherwise yield no credit "
               "and no nudge. App-layer condition (reads the 1099 aggregate + no-Form-1116-row); no pure "
               "compute_1116 scenario.")},
]

P_SCENARIOS: list[dict] = [
    {"scenario_name": "F1116-T1 — §904(j) election, single, $250 → credit 250", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "filing_status": "single", "elect_simplified": True,
                "foreign_tax_total": 250, "regular_tax": 5000},
     "expected_outputs": {"f1116_line35": 250},
     "notes": "Path A — min(250, 5000) = 250 → Schedule 3 line 1, no carryover."},
    {"scenario_name": "F1116-T2 — §904(j) election, MFJ, $550 ≤ 600 → credit 550", "scenario_type": "edge_case", "sort_order": 2,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "elect_simplified": True,
                "foreign_tax_total": 550, "regular_tax": 9000},
     "expected_outputs": {"f1116_line35": 550},
     "notes": "MFJ ceiling $600 — the election holds."},
    {"scenario_name": "F1116-T3 — election claimed, single, $400 > 300 → defer", "scenario_type": "edge_case", "sort_order": 3,
     "inputs": {"tax_year": 2025, "filing_status": "single", "elect_simplified": True,
                "foreign_tax_total": 400, "regular_tax": 9000},
     "expected_outputs": {"D_1116_002": True},
     "notes": "Over the $300 ceiling → the election is invalid → RED-defer to the full form."},
    {"scenario_name": "F1116-T4 — full Passive, limitation binds, carryforward 139", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"tax_year": 2025, "filing_status": "single", "elect_simplified": False,
                "foreign_source_income": 10000, "deduction_apportion": 15000, "gross_income_all": 100000,
                "gross_foreign_source": 10000, "foreign_tax_total": 1500,
                "taxable_income": 85000, "regular_tax": 13614},
     "expected_outputs": {"f1116_line7": 8500, "f1116_line24": 1361, "f1116_line35": 1361,
                          "f1116_carryforward": 139},
     "notes": ("L3f = 10000/100000 = 0.10; L3g = 15000 × 0.10 = 1500; L7 = 10000 − 1500 = 8500; L18 = "
               "85000; L19 = 8500/85000 = 0.10; L21 = round(13614 × 0.10) = 1361; L24 = min(1500, 1361) "
               "= 1361; carryforward = 1500 − 1361 = 139.")},
    {"scenario_name": "F1116-T5 — full Passive, full credit (L14 < cap), no carryforward", "scenario_type": "normal", "sort_order": 5,
     "inputs": {"tax_year": 2025, "filing_status": "single", "elect_simplified": False,
                "foreign_source_income": 10000, "deduction_apportion": 15000, "gross_income_all": 100000,
                "gross_foreign_source": 10000, "foreign_tax_total": 1000,
                "taxable_income": 85000, "regular_tax": 13614},
     "expected_outputs": {"f1116_line24": 1000, "f1116_line35": 1000, "f1116_carryforward": 0},
     "notes": "L14 = 1000 < L21 1361 → L24 = 1000 (full credit), carryforward 0."},
    {"scenario_name": "F1116-T6 — foreign QD $25,000 → adjustment required (defer)", "scenario_type": "edge_case", "sort_order": 6,
     "inputs": {"tax_year": 2025, "filing_status": "single", "elect_simplified": False,
                "foreign_source_income": 30000, "foreign_qd": 25000,
                "taxable_income": 120000, "regular_tax": 20000},
     "expected_outputs": {"D_1116_004": True},
     "notes": "Foreign QD 25,000 ≥ $20,000 → the adjustment exception fails → RED-defer."},
    {"scenario_name": "F1116-T7 — general category → not supported (defer)", "scenario_type": "edge_case", "sort_order": 7,
     "inputs": {"tax_year": 2025, "filing_status": "single", "elect_simplified": False,
                "category": "general", "foreign_source_income": 50000, "foreign_tax_total": 8000,
                "taxable_income": 120000, "regular_tax": 20000},
     "expected_outputs": {"D_1116_003": True},
     "notes": "Non-passive → RED-defer."},
    {"scenario_name": "F1116-T8 — L17 ≤ 0 → L19 = 0 → credit 0", "scenario_type": "edge_case", "sort_order": 8,
     "inputs": {"tax_year": 2025, "filing_status": "single", "elect_simplified": False,
                "foreign_source_income": 1000, "deduction_apportion": 30000, "gross_income_all": 30000,
                "gross_foreign_source": 1000, "foreign_tax_total": 200,
                "taxable_income": 5000, "regular_tax": 500},
     "expected_outputs": {"f1116_line35": 0, "f1116_carryforward": 200},
     "notes": "L3g = 30000 × (1000/30000)=1000; L7 = 1000 − 1000 = 0; L17 = 0 → L19 = 0 → L21 = 0 → L24 = 0; carryforward = 200."},
    {"scenario_name": "F1116-G1 — election-available info", "scenario_type": "diagnostic", "sort_order": 9,
     "inputs": {"tax_year": 2025, "filing_status": "single", "foreign_tax_total": 250},
     "expected_outputs": {"D_1116_001": True},
     "notes": "foreign tax 250 ≤ 300 → D_1116_001."},
    {"scenario_name": "F1116-G2 — carryover entered → attach Schedule B", "scenario_type": "diagnostic", "sort_order": 10,
     "inputs": {"tax_year": 2025, "filing_status": "single", "elect_simplified": False,
                "foreign_source_income": 10000, "foreign_tax_total": 1500, "carryover": 500,
                "deduction_apportion": 0, "gross_income_all": 100000, "gross_foreign_source": 10000,
                "taxable_income": 85000, "regular_tax": 13614},
     "expected_outputs": {"D_1116_005": True},
     "notes": "carryover 500 > 0 → D_1116_005."},
]

P_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-1116-ELECT", "IRC_901_904", "primary", "§904(j) the de-minimis election"),
    ("R-1116-ELECT", "IRS_2025_F1116_INSTR", "secondary", "Credit without filing Form 1116"),
    ("R-1116-PART1", "IRS_2025_F1116_FORM", "primary", "Part I lines 1a-7"),
    ("R-1116-PART1", "IRS_2025_F1116_INSTR", "secondary", "Part I deduction apportionment"),
    ("R-1116-LIMIT", "IRC_901_904", "primary", "§904(a) the limitation"),
    ("R-1116-LIMIT", "IRS_2025_F1116_FORM", "secondary", "Part III lines 9-24"),
    ("R-1116-SUMMARY", "IRS_2025_F1116_FORM", "primary", "Part IV lines 25-35 → Schedule 3 line 1"),
    ("R-1116-CARRY", "IRC_901_904", "primary", "§904(c) carryback 1 / carryforward 10"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-1116-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "§904(j) election → Schedule 3 line 1 = min(foreign tax, regular tax)",
     "description": "Validates R-1116-ELECT. Bug it catches: the wrong ceiling ($300/$600), or the smaller-of not applied.",
     "definition": {"kind": "formula_check", "form": "FORM_1116",
                    "formula": "if elect and foreign_tax ≤ ceiling: sch3_1 = min(foreign_tax, regular_tax)"},
     "sort_order": 1},
    {"assertion_id": "FA-1040-1116-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Part I — net foreign source TI (apportionment) → line 7",
     "description": "Validates R-1116-PART1. Bug it catches: the L3f ratio, the L3g apportionment, or the L6 sum wrong.",
     "definition": {"kind": "formula_check", "form": "FORM_1116",
                    "formula": "L7 = L1a − (L2 + round((L3a+L3b) × L3d/L3e) + L4a + L4b + L5)"},
     "sort_order": 2},
    {"assertion_id": "FA-1040-1116-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Part III — the §904 limitation L21 = L20 × (L17/L18)",
     "description": "Validates R-1116-LIMIT. Bug it catches: the limitation fraction, L18 base, or L20 regular tax wrong.",
     "definition": {"kind": "formula_check", "form": "FORM_1116",
                    "formula": "L19 = L17/L18; L21 = round(L20 × L19); L24 = min(L14, L21)"},
     "sort_order": 3},
    {"assertion_id": "FA-1040-1116-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Line 18 = 1040 taxable income + Schedule 1-A line 37 (senior deduction)",
     "description": "Validates the L18 base. Bug it catches: adding back ALL OBBBA Sch 1-A deductions instead of only the senior deduction.",
     "definition": {"kind": "flow_assertion", "form": "FORM_1116",
                    "checks": [{"source_line": "18", "must_read_from": ["1040.15", "SCH_1A.37"]}]},
     "sort_order": 4},
    {"assertion_id": "FA-1040-1116-05", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Part IV — line 35 → Schedule 3 line 1",
     "description": "Validates R-1116-SUMMARY + the flow target. Bug it catches: the FTC not landing on Schedule 3 line 1.",
     "definition": {"kind": "flow_assertion", "form": "FORM_1116",
                    "checks": [{"source_line": "35", "must_write_to": ["SCH_3.1"]}]},
     "sort_order": 5},
    {"assertion_id": "FA-1040-1116-06", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "Carryforward = max(0, L14 − L24)",
     "description": "Validates R-1116-CARRY. Bug it catches: the unused foreign tax not carried, or signed wrong.",
     "definition": {"kind": "reconciliation", "form": "FORM_1116",
                    "formula": "carryforward = max(0, L14 − L24)"},
     "sort_order": 6},
    {"assertion_id": "FA-1040-1116-07", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Gates — non-passive / above-exception QD / over-ceiling election RED-defer",
     "description": "An unsupported path (non-passive category, foreign QD+gain ≥ $20k, or an over-ceiling election) fires a RED diagnostic and defers the credit — never a silent wrong number.",
     "definition": {"kind": "gating_check", "form": "FORM_1116", "expect": {"red_fires": True},
                    "blockers": ["non_passive_category", "qd_adjustment_above_exception", "election_over_ceiling"]},
     "sort_order": 7},
]


FORMS: list[dict] = [
    {"identity": P_IDENTITY, "facts": P_FACTS, "rules": P_RULES, "lines": P_LINES,
     "diagnostics": P_DIAGNOSTICS, "scenarios": P_SCENARIOS, "rule_links": P_RULE_LINKS},
]


class Command(BaseCommand):
    help = "Load the FORM_1116 spec (Foreign Tax Credit). Refuses until READY_TO_SEED=True."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad FORM_1116 spec (Foreign Tax Credit)\n"))
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
                "\nREFUSING TO SEED FORM_1116: not cleared to seed.\n\n"
                "Gated until Ken's review walk (the §904(j) ceilings, the limitation arithmetic,\n"
                "the L18/L20 mappings, the adjustment-exception thresholds).\n\n"
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
        form = TaxForm.objects.filter(form_number="FORM_1116").first()
        if form:
            uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
            self.stdout.write("FORM_1116: all rules cited" if not uncited
                              else self.style.WARNING(f"FORM_1116 uncited rules: {len(uncited)}"))
