"""Load the SCHEDULE_A spec — Itemized Deductions (Form 1040) -> 1040 line 12.

Sprint NEXT-UP #4 (Ken's "A then B" — A = Simplified Method DONE; B = this).
The most OBBBA-modified itemized surface: the SALT cap + phasedown, the 2026
charitable 0.5%-AGI floor, the restored 2026 PMI deduction, the 2026 gambling
90% limit, and the 2026 §68 overall 35% itemized-benefit limitation.

Single form, the `load_1040_form_8880.py` precedent. Schedule A line 17 ->
Form 1040 line 12 (the engine already takes the larger of standard vs itemized).

CONSTANTS VERIFIED 2026-06-13 (tts-tax-app server/specs/_schedule_a_source_brief.md;
practitioner summaries of enacted OBBBA — Ken confirms vs statute / the forms at
the walk):
  - SALT cap 2025 $40,000 / 2026 $40,400 (MFS half); phasedown 30% over
    $500,000 (2025) / $505,000 (2026) MAGI, floor $10,000 ($5,000 MFS).
  - Medical 7.5% AGI floor (permanent). Mortgage $750k acquisition debt
    (permanent). PMI restored 2026 (line 8d), $100k-$110k AGI phaseout.
  - Charitable 60% cash limit (permanent) + the 2026 0.5%-AGI floor; the full
    Pub 526 bucket worksheet (60/50/30%, carryover) — Ken's call (the rare 20%
    private-foundation-capgain + special-50% election tail is RED-deferred,
    D_SCHA_007, for the walk).
  - Gambling 90% of losses, capped at winnings, 2026 (100% in 2025).
  - §68 overall 35% limitation (2026) = RED-DEFER (D_SCHA_001, a 1040-spine
    follow-up; Ken's Decision 8).

KEN'S CONFIRMED SCOPE (2026-06-13): (1) FormDefinition on the 1040; (2) SALT
phasedown computed; (3) mortgage debt-limit = preparer fact; (4) PMI 2026
phaseout computed; (5) charitable FULL bucket worksheet + 2026 floor; (6)
casualty = preparer enters the 4684 result; (7) gambling 90% computed; (8) §68
RED-defer; (9) line 18 itemize-election.

Source brief: tts-tax-app `server/specs/_schedule_a_source_brief.md`.

SAFETY GUARD: READY_TO_SEED stays False until Ken's review walk (the OBBBA
constants per year; the charitable bucket ordering vs Pub 526; the 2026
floor/PMI/gambling/§68 interactions).
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


READY_TO_SEED = True  # FLIPPED 2026-06-13 — Ken approved the review walk ("Looks good").


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1040"]


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS (year-keyed; the QDCGT/8880 pattern)
# ═══════════════════════════════════════════════════════════════════════════

# SALT cap (line 5e). MFS = half of every figure. Phasedown: cap reduced by
# 30% of (MAGI - threshold), floored. MAGI = AGI + §911/§931/§933 exclusions.
SALT = {
    2025: {"cap": 40000, "cap_mfs": 20000, "threshold": 500000, "threshold_mfs": 250000,
           "floor": 10000, "floor_mfs": 5000, "rate": "0.30"},
    2026: {"cap": 40400, "cap_mfs": 20200, "threshold": 505000, "threshold_mfs": 252500,
           "floor": 10000, "floor_mfs": 5000, "rate": "0.30"},
}

MEDICAL_FLOOR_PCT = "0.075"          # §213, permanent

# Charitable AGI-bucket limits (Pub 526). 60% cash to 50%-limit orgs; 50%
# non-cash to 50%-limit orgs; 30% capital-gain property to 50%-limit orgs.
CHARITABLE = {
    "cash_pct": "0.60",
    "fifty_pct": "0.50",
    "capgain_pct": "0.30",
    # The 2026 0.5%-of-AGI floor applies AFTER the bucket limits (2026 only).
    "floor_pct": {2025: None, 2026: "0.005"},
}

# PMI / mortgage insurance premiums (line 8d). 2026 only; phases out 10% per
# $1,000 (or fraction) of AGI over $100,000 (fully gone at $110,000). MFS uses
# $500 increments. §163(h)(3)(E) historical mechanic, restored by OBBBA.
PMI = {
    2025: None,
    2026: {"phaseout_start": 100000, "increment": 1000, "increment_mfs": 500,
           "pct_per_increment": "0.10"},
}

# Gambling losses (§165(d)): capped at winnings, AND 2026 limited to 90% of
# losses (the lost 10% does not carry over). 2025: 100%.
GAMBLING_LOSS_PCT = {2025: "1.00", 2026: "0.90"}

# §68 overall itemized-benefit limitation. 2025: none. 2026: the 2/37 haircut
# (RED-DEFER, D_SCHA_001 — a 1040-spine follow-up, Ken's Decision 8).
SECTION_68_ACTIVE = {2025: False, 2026: True}


def _salt_cap(line5d: int, magi: int, filing_status: str, tax_year: int) -> int:
    """Line 5e = min(line5d, the phased SALT cap). Shared traceability; the
    integrity gate re-types it."""
    c = SALT.get(tax_year) or SALT[2026]
    mfs = filing_status == "mfs"
    cap = c["cap_mfs"] if mfs else c["cap"]
    threshold = c["threshold_mfs"] if mfs else c["threshold"]
    floor = c["floor_mfs"] if mfs else c["floor"]
    over = max(0, magi - threshold)
    phased = max(floor, cap - int(float(c["rate"]) * over))
    return min(line5d, phased)


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("itemized_deductions", "Itemized deductions (Schedule A) — medical, SALT, interest, charitable, casualty, other -> 1040 line 12"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_1040_FORM",
    "IRS_2025_1040_INSTR",
]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_SCHA_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Schedule A (Form 1040) — Itemized Deductions",
        "citation": "Schedule A (Form 1040) (2025); f1040sa.pdf; Attachment Sequence No. 07",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f1040sa.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": "The line structure (1-18). REQUIRES HUMAN REVIEW: confirm the 2025 line text + the 2026 form when released (8d PMI, the 0.5% charitable floor placement, gambling).",
        "topics": ["itemized_deductions"],
        "excerpts": [
            {
                "excerpt_label": "Medical 7.5% floor + the SALT line structure (2025)",
                "location_reference": "Schedule A (2025), lines 1-7",
                "excerpt_text": (
                    "Line 3: Multiply line 2 (AGI) by 7.5% (0.075). Line 4: Subtract line 3 from line 1. "
                    "Line 5a state and local income taxes OR general sales taxes (check the box). 5b real "
                    "estate taxes. 5c personal property taxes. 5d add 5a-5c. 5e enter the smaller of 5d or "
                    "the limit. Line 6 other taxes. Line 7 add 5e and 6."
                ),
                "summary_text": "Medical floor 7.5% AGI; SALT 5a (income OR sales) + 5b + 5c = 5d; 5e = min(5d, cap); 7 = 5e + 6.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_PUB526_2025",
        "source_type": "official_publication",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRS Publication 526 (2025) — Charitable Contributions",
        "citation": "Pub. 526 (2025), 'Limits on Deductions' + Worksheet 2",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/publications/p526",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": False,
        "trust_score": 9.30,
        "requires_human_review": True,
        "notes": "The AGI-bucket limits + ordering + carryover. REQUIRES HUMAN REVIEW: the full Worksheet 2 line-by-line ordering (the 20% / special-50%-election tail is RED-deferred D_SCHA_007).",
        "topics": ["itemized_deductions"],
        "excerpts": [
            {
                "excerpt_label": "AGI-bucket limits + carryover (Pub 526)",
                "location_reference": "Pub. 526 (2025), 'Limits on Deductions'",
                "excerpt_text": (
                    "Your deduction for charitable contributions generally can't be more than 60% of your AGI "
                    "for cash to 50%-limit organizations, 50% for certain other contributions to 50%-limit "
                    "organizations, 30% for capital gain property to 50%-limit organizations and for "
                    "contributions to certain non-50%-limit organizations, and 20% for capital gain property "
                    "to non-50%-limit organizations. Contributions are applied against the higher limits "
                    "first. Excess contributions carry over to the next 5 years."
                ),
                "summary_text": "60% cash / 50% other / 30% capgain-to-50%-org / 20% capgain-to-non-50%-org; higher limits first; 5-year carryover.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "OBBBA_2025_SCHA",
        "source_type": "official_guidance",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2026,
        "title": "One Big Beautiful Bill Act (2025) — Schedule A provisions",
        "citation": "OBBBA, P.L. 119-21 (July 4, 2025) — §§ SALT cap, charitable floor, PMI, gambling, §68",
        "issuer": "Congress / IRS",
        "official_url": "https://www.irs.gov/newsroom",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 9.00,
        "requires_human_review": True,
        "notes": "OBBBA changes (practitioner-summarized): SALT cap 2025 $40k/$500k -> 2026 $40,400/$505k (30% phasedown, $10k floor); charitable 0.5% floor (2026); PMI restored (2026); gambling 90% (2026); §68 overall 35% limitation (2026). REQUIRES HUMAN REVIEW vs the statute / the 2026 forms.",
        "topics": ["itemized_deductions"],
        "excerpts": [
            {
                "excerpt_label": "SALT cap + phasedown (OBBBA, 2025/2026)",
                "location_reference": "OBBBA SALT provision",
                "excerpt_text": (
                    "The SALT deduction cap is $40,000 in 2025 and $40,400 in 2026 ($20,000 / $20,200 MFS). "
                    "The cap phases down by 30% of modified AGI over $500,000 (2025) / $505,000 (2026), but "
                    "not below $10,000 ($5,000 MFS). MAGI = AGI plus amounts excluded under §911, §931, or "
                    "§933. The cap reverts to a flat $10,000 in 2030."
                ),
                "summary_text": "SALT cap $40k(2025)/$40.4k(2026); 30% phasedown over $500k/$505k MAGI; $10k floor; MFS half.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Charitable 0.5% floor / PMI / gambling / §68 (OBBBA, 2026)",
                "location_reference": "OBBBA individual provisions",
                "excerpt_text": (
                    "Beginning 2026: itemized charitable deductions are reduced by 0.5% of AGI (a floor). "
                    "Mortgage insurance premiums are again deductible as qualified residence interest "
                    "(phasing out between $100,000 and $110,000 AGI). Gambling losses are deductible only to "
                    "90% of losses (and not over winnings). The Pease limitation is repealed and replaced by "
                    "an overall limitation capping the benefit of itemized deductions at 35% (a 2/37 "
                    "reduction in the top bracket)."
                ),
                "summary_text": "2026: charitable 0.5% floor; PMI restored ($100k-$110k phaseout); gambling 90%; §68 overall 35% limit (Pease repealed).",
                "is_key_excerpt": True,
            },
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_SCHA_FORM", "SCHEDULE_A", "governs"),
    ("IRS_PUB526_2025", "SCHEDULE_A", "informs"),
    ("OBBBA_2025_SCHA", "SCHEDULE_A", "informs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM: SCHEDULE_A
# ═══════════════════════════════════════════════════════════════════════════

SCHA_IDENTITY = {
    "form_number": "SCHEDULE_A",
    "form_title": "Schedule A (Form 1040) — Itemized Deductions (TY2025)",
    "notes": (
        "Ken's 9 scope decisions 2026-06-13 (A-then-B; B=this). Real IRS face, ONE "
        "per return -> 1040 line 12. Year-keyed OBBBA constants (2025 verification "
        "bed / 2026 product target): the SALT cap + 30% phasedown; the 2026 "
        "charitable 0.5%-AGI floor; the restored 2026 PMI deduction (line 8d, "
        "$100k-$110k phaseout); the 2026 gambling 90% limit; the 2026 §68 overall "
        "35% limitation (RED-defer, D_SCHA_001). Computed: medical (7.5% floor), "
        "SALT (phasedown), interest (+2026 PMI), charitable (Pub 526 60/50/30% "
        "buckets + carryover + 2026 floor), gambling. Preparer facts / RED-defers: "
        "the Form 4684 casualty result, the Pub 936 mortgage debt-limit haircut, "
        "the charitable 20%/special-election tail, the §68 haircut."
    ),
}

SCHA_FACTS: list[dict] = [
    # ── Medical ──
    {"fact_key": "scha_medical_expenses", "label": "Line 1 — medical and dental expenses",
     "data_type": "decimal", "default_value": "0", "sort_order": 1, "notes": "INPUT. Unreimbursed; line 4 = max(0, line1 - 7.5% AGI)."},
    # ── Taxes (SALT) ──
    {"fact_key": "scha_salt_income_or_sales", "label": "Line 5a — state/local income OR general sales taxes",
     "data_type": "decimal", "default_value": "0", "sort_order": 5, "notes": "INPUT. The larger of income or sales (preparer's choice)."},
    {"fact_key": "scha_use_sales_tax", "label": "Line 5a — box checked (elected general sales taxes)?",
     "data_type": "boolean", "default_value": "false", "sort_order": 6, "notes": "INPUT (5a checkbox). Render only; does not change the math (5a is the chosen amount)."},
    {"fact_key": "scha_real_estate_taxes", "label": "Line 5b — state/local real estate taxes",
     "data_type": "decimal", "default_value": "0", "sort_order": 7, "notes": "INPUT."},
    {"fact_key": "scha_personal_property_taxes", "label": "Line 5c — state/local personal property taxes",
     "data_type": "decimal", "default_value": "0", "sort_order": 8, "notes": "INPUT."},
    {"fact_key": "scha_other_taxes", "label": "Line 6 — other taxes",
     "data_type": "decimal", "default_value": "0", "sort_order": 9, "notes": "INPUT. Not subject to the SALT cap (foreign income tax, etc.)."},
    # ── Interest ──
    {"fact_key": "scha_mortgage_interest_1098", "label": "Line 8a — home mortgage interest reported on Form 1098",
     "data_type": "decimal", "default_value": "0", "sort_order": 10, "notes": "INPUT (already limited per Pub 936 — Decision 3; debt-limit haircut not computed)."},
    {"fact_key": "scha_mortgage_interest_no_1098", "label": "Line 8b — home mortgage interest NOT on Form 1098",
     "data_type": "decimal", "default_value": "0", "sort_order": 11, "notes": "INPUT."},
    {"fact_key": "scha_points_no_1098", "label": "Line 8c — points not reported on Form 1098",
     "data_type": "decimal", "default_value": "0", "sort_order": 12, "notes": "INPUT."},
    {"fact_key": "scha_mortgage_insurance_premiums", "label": "Line 8d — mortgage insurance premiums (2026 only)",
     "data_type": "decimal", "default_value": "0", "sort_order": 13, "notes": "INPUT (2026 only). Computed phaseout $100k-$110k AGI; blank/disabled in 2025."},
    {"fact_key": "scha_investment_interest", "label": "Line 9 — investment interest (Form 4952)",
     "data_type": "decimal", "default_value": "0", "sort_order": 14, "notes": "INPUT (the already-limited Form 4952 result — preparer fact)."},
    # ── Charity ──
    {"fact_key": "scha_charitable_cash", "label": "Line 11 — gifts by cash or check (60% bucket)",
     "data_type": "decimal", "default_value": "0", "sort_order": 15, "notes": "INPUT. Cash to 50%-limit (public) charities — 60% AGI limit."},
    {"fact_key": "scha_charitable_noncash_fmv", "label": "Line 12 — gifts other than cash, FMV to 50%-orgs (50% bucket)",
     "data_type": "decimal", "default_value": "0", "sort_order": 16, "notes": "INPUT. Non-capital-gain property at FMV to 50%-limit orgs — 50% AGI limit. Form 8283 if > $500."},
    {"fact_key": "scha_charitable_capgain_50org", "label": "Line 12 — capital-gain property to 50%-orgs (30% bucket)",
     "data_type": "decimal", "default_value": "0", "sort_order": 17, "notes": "INPUT. Appreciated long-term property at FMV to 50%-limit orgs — 30% AGI limit."},
    {"fact_key": "scha_charitable_carryover_in", "label": "Line 13 — carryover from prior year",
     "data_type": "decimal", "default_value": "0", "sort_order": 18, "notes": "INPUT (year 1 preparer fact; the carry-out is computed — the Schedule-D-carryover pattern)."},
    # ── Casualty / Other ──
    {"fact_key": "scha_casualty_loss", "label": "Line 15 — casualty/theft loss (Form 4684 result)",
     "data_type": "decimal", "default_value": "0", "sort_order": 20, "notes": "INPUT (the already-computed Form 4684 result — federally declared disaster only; D_SCHA_002)."},
    {"fact_key": "scha_gambling_winnings", "label": "Gambling winnings (for the §165(d) cap)",
     "data_type": "decimal", "default_value": "0", "sort_order": 21, "notes": "INPUT. Reported as income; the loss deduction can't exceed this."},
    {"fact_key": "scha_gambling_losses", "label": "Line 16 — gambling losses",
     "data_type": "decimal", "default_value": "0", "sort_order": 22, "notes": "INPUT. Deductible = min(pct x losses, winnings); pct = 100% (2025) / 90% (2026)."},
    {"fact_key": "scha_other_itemized", "label": "Line 16 — other itemized (non-gambling)",
     "data_type": "decimal", "default_value": "0", "sort_order": 23, "notes": "INPUT. Estate tax on IRD, amortizable bond premium, etc. (misc-2% permanently suspended)."},
    {"fact_key": "scha_elect_itemize", "label": "Line 18 — elect to itemize even if less than standard",
     "data_type": "boolean", "default_value": "false", "sort_order": 24, "notes": "INPUT (line 18 checkbox)."},
    # ── Outputs ──
    {"fact_key": "scha_magi_for_salt", "label": "MAGI for the SALT phasedown (AGI + 2555/4563/PR add-backs)",
     "data_type": "decimal", "sort_order": 40, "notes": "OUTPUT (derived). = 1040 line 11 + §911/§931/§933 exclusions."},
    {"fact_key": "scha_line5e", "label": "Line 5e — SALT after the cap/phasedown",
     "data_type": "decimal", "sort_order": 41, "notes": "OUTPUT. min(5d, the phased cap)."},
    {"fact_key": "scha_line14", "label": "Line 14 — total charitable (after bucket limits + 2026 floor)",
     "data_type": "decimal", "sort_order": 42, "notes": "OUTPUT. The Pub 526 worksheet result; 2026 less the 0.5%-AGI floor."},
    {"fact_key": "scha_charitable_carryover_out", "label": "Charitable carryover to next year",
     "data_type": "decimal", "sort_order": 43, "notes": "OUTPUT. Contributions over the AGI limits → carry forward 5 years."},
    {"fact_key": "scha_line16", "label": "Line 16 — other itemized (gambling-limited + other)",
     "data_type": "decimal", "sort_order": 44, "notes": "OUTPUT. min(gambling pct x losses, winnings) + other."},
    {"fact_key": "scha_line17", "label": "Line 17 — total itemized deductions → 1040 line 12",
     "data_type": "decimal", "sort_order": 45, "notes": "OUTPUT. 4 + 7 + 10 + 14 + 15 + 16 → Form 1040 line 12."},
]

SCHA_RULES: list[dict] = [
    {"rule_id": "R-SCHA-MEDICAL", "title": "Lines 1-4 — medical, 7.5% AGI floor", "rule_type": "calculation",
     "precedence": 1, "sort_order": 1,
     "formula": "line3 = round(0.075 * AGI); line4 = max(0, scha_medical_expenses - line3).",
     "inputs": ["scha_medical_expenses"], "outputs": [],
     "description": "§213 7.5% floor, permanent (both years)."},
    {"rule_id": "R-SCHA-SALT", "title": "Lines 5-7 — SALT cap + OBBBA phasedown", "rule_type": "calculation",
     "precedence": 2, "sort_order": 2,
     "formula": ("line5d = 5a + 5b + 5c; cap = max(floor, SALT[year].cap - 0.30 * max(0, MAGI - threshold)) "
                 "(MFS halves cap/threshold/floor); scha_line5e = min(line5d, cap); line7 = 5e + 6. MAGI = "
                 "AGI + §911/§931/§933."),
     "inputs": ["scha_salt_income_or_sales", "scha_real_estate_taxes", "scha_personal_property_taxes", "scha_other_taxes"],
     "outputs": ["scha_line5e", "scha_magi_for_salt"],
     "description": "Decision 2. Year-keyed: 2025 $40k/$500k, 2026 $40,400/$505k; 30% rate; $10k floor."},
    {"rule_id": "R-SCHA-INTEREST", "title": "Lines 8-10 — mortgage interest (+ 2026 PMI)", "rule_type": "calculation",
     "precedence": 3, "sort_order": 3,
     "formula": ("line8e = 8a + 8b + 8c (+ 8d in 2026); 2026 PMI (8d) = scha_mortgage_insurance_premiums x "
                 "(1 - 0.10 x ceil(max(0, AGI - 100000)/1000)), floored at 0 (gone at AGI >= 110000; MFS $500 "
                 "increments); 2025 8d = 0. line10 = 8e + 9."),
     "inputs": ["scha_mortgage_interest_1098", "scha_mortgage_interest_no_1098", "scha_points_no_1098",
                "scha_mortgage_insurance_premiums", "scha_investment_interest"],
     "outputs": [],
     "description": "Decisions 3/4. Debt-limit haircut = preparer fact (D_SCHA_003); PMI computed 2026 only."},
    {"rule_id": "R-SCHA-CHARITABLE", "title": "Lines 11-14 — Pub 526 bucket limits + carryover + 2026 floor",
     "rule_type": "calculation", "precedence": 4, "sort_order": 4,
     "formula": ("Apply AGI buckets, higher-% first: cash<=60% AGI; FMV-non-cash<=50% AGI; capgain-to-50org<="
                 "30% AGI; overall ceiling 60% AGI (cash) within 50% for the rest. Allowed = the within-limit "
                 "sum + carryover-in (subject to the same ceiling); over-limit -> scha_charitable_carryover_out "
                 "(5-year). scha_line14 = allowed; 2026: line14 -= round(0.005 * AGI) (floor, not below 0)."),
     "inputs": ["scha_charitable_cash", "scha_charitable_noncash_fmv", "scha_charitable_capgain_50org", "scha_charitable_carryover_in"],
     "outputs": ["scha_line14", "scha_charitable_carryover_out"],
     "description": "Decision 5 (Ken: full worksheet). The 20% private-foundation-capgain + special-50% election tail is RED-deferred (D_SCHA_007)."},
    {"rule_id": "R-SCHA-OTHER", "title": "Line 16 — gambling (§165(d), 2026 90%) + other", "rule_type": "calculation",
     "precedence": 5, "sort_order": 5,
     "formula": ("gambling_allowed = min(GAMBLING_LOSS_PCT[year] * scha_gambling_losses, scha_gambling_winnings); "
                 "scha_line16 = gambling_allowed + scha_other_itemized. pct = 1.00 (2025) / 0.90 (2026)."),
     "inputs": ["scha_gambling_losses", "scha_gambling_winnings", "scha_other_itemized"], "outputs": ["scha_line16"],
     "description": "Decision 7. Misc-2% permanently suspended (out)."},
    {"rule_id": "R-SCHA-TOTAL", "title": "Line 17 — total itemized -> 1040 line 12", "rule_type": "calculation",
     "precedence": 6, "sort_order": 6,
     "formula": "scha_line17 = line4 + line7 + line10 + scha_line14 + scha_casualty_loss + scha_line16 -> Form 1040 line 12.",
     "inputs": [], "outputs": ["scha_line17"],
     "description": "Decision 9. The engine takes the larger of standard vs line 17."},
    {"rule_id": "R-SCHA-68-DEFER", "title": "2026 §68 overall 35% limitation — RED-defer", "rule_type": "routing",
     "precedence": 7, "sort_order": 7,
     "formula": ("2026 AND 37%-bracket return -> the 2/37 overall itemized-benefit reduction on 1040 line 12 is "
                 "NOT computed (D_SCHA_001). Schedule A line 17 is correct; the 1040-level haircut is a "
                 "follow-up."),
     "inputs": [], "outputs": [],
     "description": "Decision 8 (Ken: RED-defer). Pease repealed 2026; the replacement is a spine change."},
]

SCHA_LINES: list[dict] = [
    {"line_number": "1", "description": "1 Medical and dental expenses", "line_type": "input"},
    {"line_number": "2", "description": "2 Amount from Form 1040 line 11 (AGI)", "line_type": "calculated"},
    {"line_number": "3", "description": "3 Multiply line 2 by 7.5% (0.075)", "line_type": "calculated"},
    {"line_number": "4", "description": "4 Subtract line 3 from line 1 (not < 0)", "line_type": "subtotal"},
    {"line_number": "5a", "description": "5a State/local income taxes OR general sales taxes (box)", "line_type": "input"},
    {"line_number": "5b", "description": "5b State/local real estate taxes", "line_type": "input"},
    {"line_number": "5c", "description": "5c State/local personal property taxes", "line_type": "input"},
    {"line_number": "5d", "description": "5d Add lines 5a through 5c", "line_type": "calculated"},
    {"line_number": "5e", "description": "5e Smaller of 5d or the SALT cap (phased)", "line_type": "calculated"},
    {"line_number": "6", "description": "6 Other taxes", "line_type": "input"},
    {"line_number": "7", "description": "7 Add lines 5e and 6", "line_type": "subtotal"},
    {"line_number": "8a", "description": "8a Home mortgage interest reported on Form 1098", "line_type": "input"},
    {"line_number": "8b", "description": "8b Home mortgage interest not on Form 1098", "line_type": "input"},
    {"line_number": "8c", "description": "8c Points not reported on Form 1098", "line_type": "input"},
    {"line_number": "8d", "description": "8d Mortgage insurance premiums (2026; phaseout $100k-$110k)", "line_type": "calculated"},
    {"line_number": "8e", "description": "8e Add lines 8a through 8d", "line_type": "calculated"},
    {"line_number": "9", "description": "9 Investment interest (Form 4952)", "line_type": "input"},
    {"line_number": "10", "description": "10 Add lines 8e and 9", "line_type": "subtotal"},
    {"line_number": "11", "description": "11 Gifts by cash or check", "line_type": "input"},
    {"line_number": "12", "description": "12 Gifts other than cash (Form 8283 if > $500)", "line_type": "input"},
    {"line_number": "13", "description": "13 Carryover from prior year", "line_type": "input"},
    {"line_number": "14", "description": "14 Total charitable (bucket limits + 2026 0.5% floor)", "line_type": "subtotal"},
    {"line_number": "15", "description": "15 Casualty and theft losses (Form 4684)", "line_type": "input"},
    {"line_number": "16", "description": "16 Other itemized deductions (gambling-limited + other)", "line_type": "subtotal"},
    {"line_number": "17", "description": "17 Total itemized deductions -> Form 1040 line 12", "line_type": "total"},
    {"line_number": "18", "description": "18 Elect to itemize even if less than the standard deduction", "line_type": "input"},
]

SCHA_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_SCHA_001", "title": "2026 §68 overall 35% itemized limitation — not computed", "severity": "error",
     "condition": "tax_year == 2026 AND filing in the 37% bracket (taxable income over the 37% threshold)",
     "message": ("Not supported — prepare manually: for 2026, the overall itemized-deduction benefit is limited "
                 "to 35% (a 2/37 reduction on Form 1040 line 12) for 37%-bracket filers. Schedule A line 17 is "
                 "correct, but this 1040-level limitation is not yet computed. Apply it manually."),
     "notes": "Decision 8 RED-defer. Pease repealed; the §68 replacement is a 1040-spine follow-up."},
    {"diagnostic_id": "D_SCHA_002", "title": "Casualty loss entered — Form 4684 not computed", "severity": "info",
     "condition": "scha_casualty_loss > 0",
     "message": ("Line 15 casualty/theft loss is taken as entered (the Form 4684 result). Form 4684 is not "
                 "computed here — verify the loss is from a federally declared disaster and figured correctly "
                 "(the 10%-AGI + $100 floors)."),
     "notes": "Decision 6."},
    {"diagnostic_id": "D_SCHA_003", "title": "Mortgage interest — debt-limit worksheet not computed", "severity": "info",
     "condition": "8a + 8b > 0",
     "message": ("Home mortgage interest is taken as entered. The $750,000 ($1,000,000 grandfathered) "
                 "acquisition-debt limit (Pub 936 Deductible Home Mortgage Interest Worksheet) is not computed "
                 "— enter the already-limited deductible interest."),
     "notes": "Decision 3."},
    {"diagnostic_id": "D_SCHA_004", "title": "Charitable contributions over the AGI limit — carryover computed", "severity": "info",
     "condition": "the bucket limits reduce line 14 below the contributions entered",
     "message": ("Charitable contributions exceed the AGI percentage limits; the allowed amount is on line 14 "
                 "and the excess carries forward up to 5 years (shown as the charitable carryover)."),
     "notes": "Decision 5."},
    {"diagnostic_id": "D_SCHA_005", "title": "2026 charitable 0.5%-AGI floor applied", "severity": "info",
     "condition": "tax_year == 2026 AND charitable contributions > 0",
     "message": ("For 2026, itemized charitable deductions are reduced by 0.5% of AGI (a floor). Line 14 "
                 "reflects the reduction."),
     "notes": "Decision 5; 2026-only OBBBA change."},
    {"diagnostic_id": "D_SCHA_006", "title": "2026 mortgage insurance premiums phaseout applied", "severity": "info",
     "condition": "tax_year == 2026 AND scha_mortgage_insurance_premiums > 0 AND AGI > 100000",
     "message": ("Mortgage insurance premiums (line 8d) are reduced 10% for each $1,000 (or part) of AGI over "
                 "$100,000 and are fully phased out at $110,000 AGI."),
     "notes": "Decision 4; 2026-only OBBBA restoration."},
    {"diagnostic_id": "D_SCHA_007", "title": "Charitable 20% / special-50%-election tail — not modeled", "severity": "info",
     "condition": "contributions to non-50%-limit orgs or capital-gain property to private non-operating foundations are present",
     "message": ("The 20%-limit bucket (capital-gain property to private non-operating foundations / non-50%-"
                 "limit organizations) and the special 50% election are not modeled in v1 — enter only "
                 "60%/50%/30%-bucket contributions, or figure those amounts manually (Pub 526 Worksheet 2)."),
     "notes": "Decision 5 tail RED-defer — Ken confirms at the walk whether to add it."},
    {"diagnostic_id": "D_SCHA_008", "title": "Itemizing less than the standard deduction", "severity": "info",
     "condition": "scha_line17 < the standard deduction AND scha_elect_itemize is True",
     "message": ("Total itemized deductions (line 17) are less than the standard deduction, and you elected to "
                 "itemize anyway (line 18). Verify this is intended (e.g., a state-return benefit)."),
     "notes": "Decision 9."},
    {"diagnostic_id": "D_SCHA_009", "title": "Gambling losses limited", "severity": "info",
     "condition": "scha_gambling_losses > 0",
     "message": ("Gambling losses are deductible only up to winnings, and for 2026 only up to 90% of losses "
                 "(the disallowed 10% does not carry over). Line 16 reflects the limit."),
     "notes": "Decision 7; the 90% is 2026-only OBBBA."},
]

SCHA_SCENARIOS: list[dict] = [
    {"scenario_name": "SCHA-T1 — medical 7.5% floor", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "filing_status": "single", "agi": 80000, "scha_medical_expenses": 10000},
     "expected_outputs": {"line_4": 4000},
     "notes": "floor = 7.5% x 80,000 = 6,000; line 4 = 10,000 - 6,000 = 4,000."},
    {"scenario_name": "SCHA-T2 — SALT phasedown to the floor ($600k MAGI)", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"tax_year": 2025, "filing_status": "single", "magi": 600000,
                "scha_salt_income_or_sales": 45000, "scha_real_estate_taxes": 5000},
     "expected_outputs": {"scha_line5e": 10000},
     "notes": "5d = 50,000; cap = max(10,000, 40,000 - 0.30 x 100,000) = max(10,000, 10,000) = 10,000; 5e = 10,000."},
    {"scenario_name": "SCHA-T3 — SALT partial phasedown ($550k MAGI)", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"tax_year": 2025, "filing_status": "single", "magi": 550000,
                "scha_salt_income_or_sales": 50000},
     "expected_outputs": {"scha_line5e": 25000},
     "notes": "cap = 40,000 - 0.30 x 50,000 = 25,000; 5e = min(50,000, 25,000) = 25,000."},
    {"scenario_name": "SCHA-T4 — SALT under the cap (no phasedown)", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"tax_year": 2025, "filing_status": "single", "magi": 200000,
                "scha_salt_income_or_sales": 18000, "scha_real_estate_taxes": 7000},
     "expected_outputs": {"scha_line5e": 25000},
     "notes": "5d = 25,000 <= 40,000 cap; no phasedown (MAGI < 500k); 5e = 25,000."},
    {"scenario_name": "SCHA-T5 — 2026 SALT cap + phasedown", "scenario_type": "normal", "sort_order": 5,
     "inputs": {"tax_year": 2026, "filing_status": "mfj", "magi": 605000,
                "scha_salt_income_or_sales": 60000},
     "expected_outputs": {"scha_line5e": 10400},
     "notes": "2026 cap 40,400, threshold 505,000; 40,400 - 0.30 x 100,000 = 10,400 (> 10,000 floor); 5e = 10,400."},
    {"scenario_name": "SCHA-T6 — charitable cash within 60%", "scenario_type": "normal", "sort_order": 6,
     "inputs": {"tax_year": 2025, "filing_status": "single", "agi": 100000, "scha_charitable_cash": 50000},
     "expected_outputs": {"scha_line14": 50000, "scha_charitable_carryover_out": 0},
     "notes": "50,000 <= 60% x 100,000 = 60,000; full deduction; no carryover; 2025 no floor."},
    {"scenario_name": "SCHA-T7 — charitable cash over 60% -> carryover", "scenario_type": "normal", "sort_order": 7,
     "inputs": {"tax_year": 2025, "filing_status": "single", "agi": 100000, "scha_charitable_cash": 70000},
     "expected_outputs": {"scha_line14": 60000, "scha_charitable_carryover_out": 10000, "D_SCHA_004": True},
     "notes": "60% x 100,000 = 60,000 allowed; 10,000 carries forward."},
    {"scenario_name": "SCHA-T8 — capital-gain property 30% bucket", "scenario_type": "normal", "sort_order": 8,
     "inputs": {"tax_year": 2025, "filing_status": "single", "agi": 100000, "scha_charitable_capgain_50org": 40000},
     "expected_outputs": {"scha_line14": 30000, "scha_charitable_carryover_out": 10000},
     "notes": "capgain to 50%-org <= 30% x 100,000 = 30,000; 10,000 carries forward."},
    {"scenario_name": "SCHA-T9 — 2026 charitable 0.5% floor", "scenario_type": "normal", "sort_order": 9,
     "inputs": {"tax_year": 2026, "filing_status": "single", "agi": 100000, "scha_charitable_cash": 50000},
     "expected_outputs": {"scha_line14": 49500, "D_SCHA_005": True},
     "notes": "50,000 within 60%; 2026 floor = 0.5% x 100,000 = 500; line 14 = 50,000 - 500 = 49,500."},
    {"scenario_name": "SCHA-T10 — gambling 2026 90% limit", "scenario_type": "normal", "sort_order": 10,
     "inputs": {"tax_year": 2026, "filing_status": "single", "scha_gambling_winnings": 10000,
                "scha_gambling_losses": 8000},
     "expected_outputs": {"scha_line16": 7200, "D_SCHA_009": True},
     "notes": "min(0.90 x 8,000, 10,000) = 7,200 (2025 would be 8,000)."},
    {"scenario_name": "SCHA-T11 — 2026 PMI phaseout", "scenario_type": "normal", "sort_order": 11,
     "inputs": {"tax_year": 2026, "filing_status": "single", "agi": 105000,
                "scha_mortgage_insurance_premiums": 2000},
     "expected_outputs": {"line_8d": 1000, "D_SCHA_006": True},
     "notes": "AGI 105,000 -> ceil(5,000/1,000) = 5 increments x 10% = 50% reduction; 2,000 x 0.50 = 1,000."},
    {"scenario_name": "SCHA-G1 — 2026 §68 limitation RED-defer", "scenario_type": "diagnostic", "sort_order": 12,
     "inputs": {"tax_year": 2026, "filing_status": "single", "taxable_income": 700000},
     "expected_outputs": {"D_SCHA_001": True},
     "notes": "2026 37%-bracket return -> the overall 35% limitation is not computed (D_SCHA_001)."},
]

SCHA_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-SCHA-MEDICAL", "IRS_2025_SCHA_FORM", "primary", "Lines 1-4: the 7.5% medical floor"),
    ("R-SCHA-SALT", "IRS_2025_SCHA_FORM", "primary", "Lines 5-7: the SALT line structure"),
    ("R-SCHA-SALT", "OBBBA_2025_SCHA", "primary", "The SALT cap + 30% phasedown (year-keyed)"),
    ("R-SCHA-INTEREST", "IRS_2025_SCHA_FORM", "primary", "Lines 8-10: mortgage interest"),
    ("R-SCHA-INTEREST", "OBBBA_2025_SCHA", "secondary", "2026 PMI restoration + phaseout"),
    ("R-SCHA-CHARITABLE", "IRS_PUB526_2025", "primary", "The AGI-bucket limits + carryover (Pub 526)"),
    ("R-SCHA-CHARITABLE", "OBBBA_2025_SCHA", "secondary", "The 2026 0.5%-AGI charitable floor"),
    ("R-SCHA-OTHER", "OBBBA_2025_SCHA", "primary", "Gambling 90% (2026) + misc-2% suspension"),
    ("R-SCHA-TOTAL", "IRS_2025_SCHA_FORM", "primary", "Line 17 total -> 1040 line 12"),
    ("R-SCHA-68-DEFER", "OBBBA_2025_SCHA", "primary", "The 2026 §68 overall 35% limitation (RED-defer)"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-SCHA-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Medical line 4 = max(0, expenses - 7.5% AGI)",
     "description": "Validates R-SCHA-MEDICAL. Bug it catches: a wrong floor percentage or a negative line 4.",
     "definition": {"kind": "formula_check", "form": "SCHEDULE_A",
                    "formula": "line_4 == max(0, line_1 - round(0.075 * agi))"},
     "sort_order": 1},
    {"assertion_id": "FA-1040-SCHA-02", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "SALT cap + phasedown constants (year-keyed) == verified OBBBA",
     "description": ("Pins the SALT cap/threshold/floor/rate both years. Bug it catches: a drifted cap or "
                     "threshold, or the MFS halving."),
     "definition": {"kind": "constants_check", "form": "SCHEDULE_A",
                    "constants": {"cap_2025": 40000, "cap_2026": 40400, "threshold_2025": 500000,
                                  "threshold_2026": 505000, "floor": 10000, "rate": 0.30}},
     "sort_order": 2},
    {"assertion_id": "FA-1040-SCHA-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Charitable line 14 = bucket limits, then the 2026 0.5%-AGI floor",
     "description": ("Validates R-SCHA-CHARITABLE. Bug it catches: a cash gift over 60% AGI not limited, or the "
                     "2026 floor missing/applied in 2025."),
     "definition": {"kind": "formula_check", "form": "SCHEDULE_A",
                    "formula": "line_14 == bucket_limited(cash<=0.60*agi, fmv<=0.50*agi, capgain<=0.30*agi) - floor_2026(0.005*agi)"},
     "sort_order": 3},
    {"assertion_id": "FA-1040-SCHA-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Line 17 total → Form 1040 line 12",
     "description": "Validates R-SCHA-TOTAL. Bug it catches: a wrong total, or the result not reaching 1040 line 12.",
     "definition": {"kind": "flow_assertion", "form": "SCHEDULE_A",
                    "checks": [{"source_line": "17", "must_write_to": ["1040.12"]}]},
     "sort_order": 4},
    {"assertion_id": "FA-1040-SCHA-05", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Gambling line 16 = min(pct × losses, winnings); pct year-keyed (90% in 2026)",
     "description": "Validates R-SCHA-OTHER. Bug it catches: losses over winnings, or the 2026 90% factor missing.",
     "definition": {"kind": "formula_check", "form": "SCHEDULE_A",
                    "formula": "gambling_allowed == min(gambling_pct[year] * losses, winnings); gambling_pct = {2025: 1.0, 2026: 0.9}"},
     "sort_order": 5},
    {"assertion_id": "FA-1040-SCHA-06", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "RED-defers each leave a RED (no silent gap)",
     "description": ("The 2026 §68 overall limitation (D_SCHA_001), the casualty 4684 (D_SCHA_002), the mortgage "
                     "debt-limit (D_SCHA_003), and the charitable 20%/special tail (D_SCHA_007) each flag rather "
                     "than silently computing a wrong number."),
     "definition": {"kind": "gating_check", "form": "SCHEDULE_A", "expect": {"red_fires": True},
                    "blockers": ["section_68_2026", "casualty_4684", "mortgage_debt_limit", "charitable_tail"]},
     "sort_order": 6},
]


FORMS: list[dict] = [
    {"identity": SCHA_IDENTITY, "facts": SCHA_FACTS, "rules": SCHA_RULES, "lines": SCHA_LINES,
     "diagnostics": SCHA_DIAGNOSTICS, "scenarios": SCHA_SCENARIOS, "rule_links": SCHA_RULE_LINKS},
]


class Command(BaseCommand):
    help = "Load the SCHEDULE_A spec (Itemized Deductions). Refuses until READY_TO_SEED=True."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad SCHEDULE_A spec (Itemized Deductions)\n"))
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
                "\nREFUSING TO SEED SCHEDULE_A: not cleared to seed.\n\n"
                "Gated until Ken's review walk (the OBBBA per-year constants — SALT cap + phasedown,\n"
                "the 2026 charitable 0.5% floor, the 2026 PMI/gambling/§68 changes; the Pub 526\n"
                "charitable bucket ordering + the 20%/special-election tail decision).\n\n"
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
        form = TaxForm.objects.filter(form_number="SCHEDULE_A").first()
        if form:
            uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
            self.stdout.write("SCHEDULE_A: all rules cited" if not uncited
                              else self.style.WARNING(f"SCHEDULE_A uncited rules: {len(uncited)}"))
