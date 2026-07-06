"""Load the Form 4684 spec — Casualties and Thefts (2025, Created 9/26/25).
WO-16, 3rd item in the SPINE S-16 federal-forms queue (after 8990 + Schedule H). Greenfield.

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
Form 4684 computes casualty and theft gains/losses. Section A = personal-use property (deductible
ONLY if attributable to a federally declared disaster, §165(h)(5)); $100 per-event floor + 10%-of-AGI
floor, with a qualified-disaster special path ($500 floor, no 10%-AGI, add-to-standard-deduction).
Section B = business & income-producing property → §1231/ordinary holding-period netting routed to
Form 4797 / Schedule A / Schedule D. Section C = Ponzi-type theft safe harbor (Rev. Proc. 2009-20,
95%/75%). Section D = the §165(i) election to deduct a disaster loss in the preceding year.

The load-bearing law: the §165(h)(5) federally-declared-disaster limitation is STILL in effect for
TY2025; OBBBA (P.L. 119-21) EXTENDED the qualified-disaster special rules (declaration window to
9/2/2025) and ADDED a financial-scam theft-loss avenue (Section B) — it did NOT repeal the base
limitation or add state-declared disasters. The year-sensitive item is the qualified-disaster
declaration window.

Greenfield: 4684 not in the 112-form prod set at the 2026-07-05 gap-check (downstream Sch A / Sch D /
4797 / 8829 route TO 4684 but none authors it).

═══════════════════════════════════════════════════════════════════════════
v1 SCOPE — LOCKED (Ken's Gate-1 walk 2026-07-05; DECISIONS D-18). See f4684_source_brief.md.
═══════════════════════════════════════════════════════════════════════════
COMPUTES: (Q1) Section A per-property loss = min(basis, FMV decline) − insurance; FDD-limitation gate; $100/$500
floor; 10%-AGI floor; qualified-disaster special path (year-keyed window). (Q2) Section B Part I per-property
(total destruction → full basis) + Part II §1231/ordinary holding-period routing to 4797 L3/L14. (Q3) Section C
Ponzi safe harbor (95%/75%); Section D §165(i) = diagnostic. (Q4) entity_types 1040/1065/1120S/1120 + the OBBBA
financial-scam theft-loss diagnostic (Section B, 3 conditions).

requires_human_review WALK ITEMS (W1-W4):
W1. Section A: loss = min(adjusted basis, FMV before − FMV after) − insurance; deductible ONLY if federally
    declared disaster; − $100 (or $500 qualified) − 10% AGI (waived for qualified disaster). CONFIRM the FDD gate.
W2. Section B: Part I loss (total destruction → full basis); Part II ≤1yr→ordinary 4797 L14, >1yr gains≥losses→
    §1231 4797 L3 else ordinary L14. CONFIRM the holding-period §1231 routing.
W3. Section C Ponzi: qualified investment × (95% no-recovery / 75% potential-recovery) − recoveries. CONFIRM 95/75.
W4. Qualified-disaster window (declared 1/1/2020–9/2/2025, incident began by 7/4/2025, ended by 8/3/2025) +
    financial-scam theft (state-law theft / no reasonable recovery / profit-motive → Section B). CONFIRM the window.

CARRIED [UNVERIFIED]: none — all facts verbatim vs FINAL 2025 Form 4684 + i4684 + Pub 547 + §165 + Rev. Proc.
2009-20. The qualified-disaster declaration window is OBBBA-set and year-keyed (re-verify each season).

SAFETY GUARD — READY_TO_SEED stays False until Ken approves the review walk (W1-W4).
FLIPPED 2026-07-05 — Ken APPROVED ("Approve — flip, seed, export"): W1 Section A FDD gate + $100/$500
floor + 10% AGI (non-disaster -> 0; qualified disaster 19,500); W2 Section B total-destruction full
basis + §1231 routing to 4797 L3/L14; W3 Ponzi 95%/75% safe harbor; W4 qualified-disaster window
(9/2/2025) + financial-scam theft. Validated (scratchpad/validate_4684.py, 29/0).
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
FORM_ENTITY_TYPES = ["1040", "1065", "1120S", "1120"]

# ── Verified 2025 constants (f4684_source_brief.md; Form 4684 2025 Created 9/26/25 / i4684 / §165 / Rev. Proc. 2009-20) ──
PERSONAL_FLOOR = 100                    # L11 — per-event floor (personal)
QUALIFIED_DISASTER_FLOOR = 500          # L11 — qualified-disaster floor (replaces $100)
AGI_FLOOR_PCT = "0.10"                  # L17 — 10% of AGI floor (personal; waived for qualified disaster)
PONZI_FACTOR_NO_RECOVERY = "0.95"       # L46 — Rev. Proc. 2009-20, no potential third-party recovery
PONZI_FACTOR_POTENTIAL_RECOVERY = "0.75"  # L46 — potential recovery
# Year-keyed — OBBBA-set, the most-likely-to-change item. 2025 per i4684 "What's New".
QUALIFIED_DISASTER_WINDOW = {
    "declared_start": "2020-01-01", "declared_end": "2025-09-02",
    "incident_begin_by": "2025-07-04", "incident_end_by": "2025-08-03",
}


def _casualty_item(basis, fmv_before, fmv_after, insurance, total_destruction=False) -> dict:
    """Per-property gain/loss. Gain when insurance > basis (L4/L22). Otherwise loss = min(basis, FMV
    decline) − insurance, floored at 0 (L8-9 / L26-27). Total destruction/theft of business property
    → use full basis, ignore FMV (L26 note)."""
    if float(insurance) > float(basis):
        return {"gain": round(float(insurance) - float(basis), 2), "loss": 0.0}
    fmv_decline = max(0.0, float(fmv_before) - float(fmv_after))
    allowed = float(basis) if total_destruction else min(float(basis), fmv_decline)
    return {"gain": 0.0, "loss": max(0.0, round(allowed - float(insurance), 2))}


def _section_a_deduction(total_loss, gains, is_fdd, is_qualified_disaster, agi) -> float:
    """Section A deductible personal casualty loss. FDD gate: deductible only if attributable to a
    federally declared disaster (§165(h)(5)). Then − $100 (or $500 qualified) floor − 10% AGI (waived
    for a qualified disaster). Personal casualty gains (L13) reduce the loss before the AGI floor."""
    if not is_fdd:
        return 0.0  # non-disaster personal loss is not deductible (may only offset personal casualty gains)
    floor = QUALIFIED_DISASTER_FLOOR if is_qualified_disaster else PERSONAL_FLOOR
    after_floor = max(0.0, float(total_loss) - floor)          # L12/L14
    after_gains = max(0.0, after_floor - float(gains))          # L16 (gains offset)
    if is_qualified_disaster:
        return round(after_gains, 2)                            # no 10%-AGI floor
    return round(max(0.0, after_gains - float(AGI_FLOOR_PCT) * float(agi)), 2)  # L18


def _section_b_route(gain, loss, holding_long) -> str:
    """Section B Part II routing. Held <=1 yr -> ordinary (Form 4797 line 14). Held >1 yr: gains >= losses
    -> §1231 capital gain (Form 4797 line 3); losses > gains -> ordinary (Form 4797 line 14)."""
    if not holding_long:
        return "4797_L14_ordinary"
    return "4797_L3_1231" if float(gain) >= float(loss) else "4797_L14_ordinary"


def _ponzi_deduction(qualified_investment, potential_recovery, actual_recovery, potential_ins_recovery) -> float:
    """Section C Rev. Proc. 2009-20 safe harbor: L47 = qualified investment × (95% no-recovery / 75%
    potential-recovery); L51 = L47 − (actual + potential insurance/SIPC recovery) = deductible theft loss."""
    factor = float(PONZI_FACTOR_POTENTIAL_RECOVERY) if potential_recovery else float(PONZI_FACTOR_NO_RECOVERY)
    l47 = round(float(qualified_investment) * factor, 2)
    total_recovery = float(actual_recovery) + float(potential_ins_recovery)
    return max(0.0, round(l47 - total_recovery, 2))


AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("casualty_theft_loss", "Form 4684 casualties and thefts: Section A personal (FDD-only §165(h)(5), $100/$500 "
     "floor + 10% AGI, qualified-disaster path) / Section B business §1231 routing to 4797 / Section C Ponzi 95-75 "
     "safe harbor / Section D §165(i) election."),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_F4684", "source_type": "federal_form", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Form 4684 (2025) — Casualties and Thefts",
        "citation": "Form 4684 (2025), Cat. No. 12997O, Created 9/26/25, Attach. Seq. No. 26",
        "issuer": "Internal Revenue Service", "official_url": "https://www.irs.gov/pub/irs-pdf/f4684.pdf",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.6, "topics": ["casualty_theft_loss"],
        "excerpts": [{
            "excerpt_label": "Section A personal-use property line map (2025 verbatim)",
            "excerpt_text": (
                "Header: 'For tax years beginning after 2017, if you are an individual, casualty or theft losses "
                "of personal-use property are deductible only if the loss is attributable to a federally declared "
                "disaster.' L2 cost/other basis; L3 insurance or reimbursement (whether or not you filed a claim); "
                "L4 gain if L3 > L2 (skip L5-9); L5 FMV before; L6 FMV after; L7 = L5 − L6; L8 = smaller of L2 or "
                "L7; L9 = L8 − L3 (>=0); L10 = add L9; L11 = '$100 ($500 if qualified disaster loss rules apply)'; "
                "L12 = L10 − L11 (>=0); L13 = total gains (L4); L14 = total losses (L12); L15 compares 13 vs 14 "
                "(net gain -> Schedule D; qualified-disaster $500 losses -> Schedule A line 16, add standard "
                "deduction if not itemizing); L16 = L14 − (L13 + L15); L17 = 10% of AGI; L18 = L16 − L17 (>=0) -> "
                "Schedule A line 15."
            ),
            "summary_text": "Section A: L8 = min(basis, FMV decline); L9 = L8 − insurance; L11 $100/$500 floor; L17 10% AGI; L18 -> Schedule A line 15. FDD-only.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "Section B business + Section C Ponzi + Section D election (2025 verbatim)",
            "excerpt_text": (
                "Section B Part I: L20 cost/adjusted basis; L21 insurance; L22 gain if L21 > L20; L23 FMV before; "
                "L24 FMV after; L25 = L23 − L24; L26 = smaller of L20 or L25 (NOTE: if totally destroyed / lost "
                "from theft, enter the L20 amount = full basis); L27 = L26 − L21 (>=0); L28 = add L27. Part II "
                "summary: Held <=1 year (L29-32): L31 combine -> Form 4797 line 14 (ordinary); L32 income-producing "
                "-> Schedule A line 16. Held >1 year (L33-39): L38a losses>gains -> Form 4797 line 14 (ordinary); "
                "L39 gains>=losses -> Form 4797 line 3 (§1231). Section C Ponzi (Rev. Proc. 2009-20): L45 total "
                "qualified investment; L46 = 0.95 (no potential recovery) or 0.75 (potential recovery); L47 = L46 × "
                "L45; L50 total recovery; L51 = L47 − L50 -> Section B line 28. Section D = §165(i) election to "
                "deduct a federally declared disaster loss in the preceding tax year (L52-57)."
            ),
            "summary_text": "Section B Part I L26 = min(basis, FMV decline) (total destruction = full basis); Part II §1231 routing 4797 L3/L14. Section C Ponzi 95%/75%. Section D §165(i) election.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "IRS_2025_I4684", "source_type": "official_instructions", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "2025 Instructions for Form 4684",
        "citation": "Instructions for Form 4684 (2025), updated 30-Apr-2026", "issuer": "Internal Revenue Service",
        "official_url": "https://www.irs.gov/instructions/i4684",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.5, "topics": ["casualty_theft_loss"],
        "excerpts": [{
            "excerpt_label": "What's New — OBBBA qualified-disaster window + financial-scam theft (i4684 verbatim)",
            "excerpt_text": (
                "P.L. 119-21 (One Big Beautiful Bill Act) extended the special rules and return procedures for "
                "personal casualty losses attributable to certain major federal disasters. Qualified disaster: a "
                "major disaster declared by the President between January 1, 2020, and September 2, 2025, with an "
                "incident period beginning on or after December 28, 2019, and on or before July 4, 2025, ending no "
                "later than August 3, 2025 (COVID-19-only declarations excluded). Qualified disaster losses use a "
                "$500 floor (instead of $100), are NOT subject to the 10%-of-AGI limit, and may be added to the "
                "standard deduction. New — 'Losses from financial scams': a victim of a financial scam involving a "
                "transaction entered into for profit may claim a theft loss if the loss results from conduct that "
                "is criminal theft under applicable state law and there is no reasonable prospect of recovery "
                "(reported in Section B). A reasonable prospect of recovery defers the loss until it can be "
                "ascertained; expected reimbursement must be subtracted."
            ),
            "summary_text": "OBBBA: qualified-disaster window declared 1/1/2020-9/2/2025 ($500 floor / no-10%-AGI / std-deduction add). New financial-scam theft loss (profit-motive, Section B). Reasonable-prospect-of-recovery defers.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "IRC_165", "source_type": "statute", "source_rank": "controlling",
        "jurisdiction_code": "US", "title": "IRC §165 — casualty and theft losses (§165(c)/(h)/(i))",
        "citation": "26 U.S.C. §165(c),(h)(1)-(5),(i); P.L. 119-21 (OBBBA)", "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/165",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.3, "topics": ["casualty_theft_loss"],
        "excerpts": [{
            "excerpt_label": "§165(h) personal casualty limits + FDD-only limitation (verbatim substance)",
            "excerpt_text": (
                "§165(c): an individual's deductible losses are limited to trade/business, transactions entered "
                "into for profit, and (§165(c)(3)) casualty/theft losses. §165(h)(1): each personal casualty/theft "
                "loss is allowed only to the extent it exceeds $100. §165(h)(2): aggregate net personal casualty "
                "losses are allowed only to the extent they exceed 10% of AGI (after netting personal casualty "
                "gains). §165(h)(5): for 2018-2025, a personal casualty loss is deductible ONLY if attributable to "
                "a federally declared disaster (except to the extent of personal casualty gains). §165(i): a "
                "taxpayer may elect to deduct a disaster loss in the taxable year immediately preceding the "
                "disaster year."
            ),
            "summary_text": "§165(h)(1) $100 floor; (h)(2) 10% AGI; (h)(5) FDD-only 2018-2025; (i) preceding-year election; (c)(3) personal casualty/theft.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "REVPROC_2009_20", "source_type": "official_guidance", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Rev. Proc. 2009-20 — Ponzi-type theft loss safe harbor",
        "citation": "Rev. Proc. 2009-20 (95%/75% safe-harbor deduction factors)", "issuer": "Internal Revenue Service",
        "official_url": "https://www.irs.gov/irb/2009-14_IRB",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.0, "topics": ["casualty_theft_loss"],
        "excerpts": [{
            "excerpt_label": "Ponzi safe-harbor 95%/75% (verbatim substance)",
            "excerpt_text": (
                "A qualified investor in a specified fraudulent arrangement (Ponzi-type scheme) may deduct a theft "
                "loss equal to 95% of the qualified investment (total investment plus income previously reported "
                "less withdrawals) if the investor does not intend to pursue any potential third-party recovery, or "
                "75% if the investor is pursuing or intends to pursue potential third-party recovery, in each case "
                "reduced by actual recovery and potential insurance/SIPC recovery, in the discovery year."
            ),
            "summary_text": "Ponzi safe harbor: 95% (no potential recovery) or 75% (potential recovery) of qualified investment, less actual + potential insurance/SIPC recovery.",
            "is_key_excerpt": True,
        }],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_F4684", "4684", "governs"), ("IRS_2025_I4684", "4684", "governs"),
    ("IRC_165", "4684", "governs"), ("REVPROC_2009_20", "4684", "governs"),
]


F4684_FACTS: list[dict] = [
    # Section A — personal-use property
    {"fact_key": "pa_basis", "label": "Adjusted basis of the personal-use property (Section A L2)", "data_type": "decimal", "required": False, "sort_order": 1},
    {"fact_key": "pa_fmv_before", "label": "FMV before the casualty/theft — personal (L5)", "data_type": "decimal", "required": False, "sort_order": 2},
    {"fact_key": "pa_fmv_after", "label": "FMV after the casualty/theft — personal (L6)", "data_type": "decimal", "required": False, "sort_order": 3},
    {"fact_key": "pa_insurance", "label": "Insurance/reimbursement — personal, whether or not claimed (L3)", "data_type": "decimal", "required": False, "sort_order": 4},
    {"fact_key": "pa_is_fdd", "label": "Loss attributable to a FEDERALLY DECLARED DISASTER? (§165(h)(5) gate)", "data_type": "boolean", "required": False, "sort_order": 5,
     "notes": "W1. A personal casualty/theft loss is deductible ONLY if federally declared disaster (except to offset personal casualty gains)."},
    {"fact_key": "pa_is_qualified_disaster", "label": "Qualified disaster (declared 1/1/2020-9/2/2025)? -> $500 floor, no 10% AGI, add to standard deduction", "data_type": "boolean", "required": False, "sort_order": 6,
     "notes": "W4. OBBBA-extended window — year-keyed."},
    {"fact_key": "pa_gains", "label": "Personal casualty GAINS (L13) — offset losses before the 10%-AGI floor", "data_type": "decimal", "required": False, "sort_order": 7},
    {"fact_key": "agi", "label": "Adjusted gross income (for the 10%-AGI floor, L17)", "data_type": "decimal", "required": False, "sort_order": 8},
    # Section B — business & income-producing property
    {"fact_key": "pb_basis", "label": "Adjusted basis of the business/income-producing property (Section B L20)", "data_type": "decimal", "required": False, "sort_order": 9},
    {"fact_key": "pb_fmv_before", "label": "FMV before — business (L23)", "data_type": "decimal", "required": False, "sort_order": 10},
    {"fact_key": "pb_fmv_after", "label": "FMV after — business (L24)", "data_type": "decimal", "required": False, "sort_order": 11},
    {"fact_key": "pb_insurance", "label": "Insurance/reimbursement — business (L21)", "data_type": "decimal", "required": False, "sort_order": 12},
    {"fact_key": "pb_total_destruction", "label": "Property totally destroyed / lost from theft? -> use full basis, ignore FMV (L26 note)", "data_type": "boolean", "required": False, "sort_order": 13},
    {"fact_key": "pb_holding_long", "label": "Held MORE than 1 year? (drives §1231 vs ordinary, Part II)", "data_type": "boolean", "required": False, "sort_order": 14},
    {"fact_key": "pb_property_use", "label": "Property use (trade/business vs income-producing vs employee)", "data_type": "choice", "required": False, "sort_order": 15,
     "choices": ["trade_business", "income_producing", "employee"]},
    {"fact_key": "is_financial_scam", "label": "Financial-scam theft (OBBBA) — profit-motive, state-law theft, no reasonable recovery? (Section B)", "data_type": "boolean", "required": False, "sort_order": 16,
     "notes": "W4. New OBBBA avenue — reported in Section B, NOT subject to the FDD limitation."},
    # Section C — Ponzi
    {"fact_key": "pc_qualified_investment", "label": "Ponzi total qualified investment (L45)", "data_type": "decimal", "required": False, "sort_order": 17},
    {"fact_key": "pc_potential_recovery", "label": "Pursuing/intending potential third-party recovery? -> 75% factor (else 95%)", "data_type": "boolean", "required": False, "sort_order": 18},
    {"fact_key": "pc_recovery", "label": "Ponzi actual + potential insurance/SIPC recovery (L48+L49)", "data_type": "decimal", "required": False, "sort_order": 19},
    # Section D
    {"fact_key": "pd_elect_165i", "label": "Electing to deduct the disaster loss in the PRECEDING year? (§165(i), Section D)", "data_type": "boolean", "required": False, "sort_order": 20},
]

F4684_RULES: list[dict] = [
    {"rule_id": "R-4684-ITEM", "title": "Per-property casualty gain/loss (Section A L8-9 / Section B L26-27)", "rule_type": "calculation",
     "formula": "if insurance > basis: gain = insurance - basis (skip loss) ; else loss = max(0, (basis if total_destruction else min(basis, fmv_before - fmv_after)) - insurance)",
     "inputs": ["pa_basis", "pa_fmv_before", "pa_fmv_after", "pa_insurance"], "outputs": ["item_gain", "item_loss"], "sort_order": 1,
     "description": "Per-property: a GAIN results when insurance/reimbursement exceeds adjusted basis (L4/L22). Otherwise the loss = smaller of (adjusted basis) or (FMV decline = FMV before − FMV after), minus insurance, floored at 0. Total destruction / theft of business property uses the full basis (ignore FMV)."},
    {"rule_id": "R-4684-SECA", "title": "Section A personal deductible loss — FDD gate + floors (L18)", "rule_type": "calculation",
     "formula": "if not pa_is_fdd: 0 ; floor = 500 if pa_is_qualified_disaster else 100 ; after = max(0, total_loss - floor) - pa_gains ; deductible = after if pa_is_qualified_disaster else max(0, after - 0.10*agi)",
     "inputs": ["pa_is_fdd", "pa_is_qualified_disaster", "pa_gains", "agi"], "outputs": ["section_a_deduction"], "sort_order": 2,
     "description": "W1. Section A: a personal casualty/theft loss is deductible ONLY if attributable to a federally declared disaster (§165(h)(5)). Then subtract the $100 floor ($500 for a qualified disaster), subtract personal casualty gains, and subtract 10% of AGI (waived for a qualified disaster; qualified-disaster losses may also be added to the standard deduction). -> Schedule A line 15/16."},
    {"rule_id": "R-4684-SECB", "title": "Section B business — Part I loss + Part II §1231 routing", "rule_type": "calculation",
     "formula": "loss = R-4684-ITEM(business) ; route: holding<=1yr -> 4797 L14 (ordinary) ; >1yr and gains>=losses -> 4797 L3 (§1231 capital) ; >1yr and losses>gains -> 4797 L14 (ordinary)",
     "inputs": ["pb_basis", "pb_fmv_before", "pb_fmv_after", "pb_insurance", "pb_total_destruction", "pb_holding_long"], "outputs": ["section_b_loss", "section_b_route"], "sort_order": 3,
     "description": "W2. Section B Part I per-property loss/gain (total destruction -> full basis). Part II holding-period netting: property held <=1 year -> ordinary (Form 4797 line 14); held >1 year with gains >= losses -> §1231 capital gain (Form 4797 line 3); held >1 year with losses > gains -> ordinary (Form 4797 line 14). Income-producing losses -> Schedule A line 16."},
    {"rule_id": "R-4684-PONZI", "title": "Section C Ponzi-type theft safe harbor (Rev. Proc. 2009-20)", "rule_type": "calculation",
     "formula": "factor = 0.75 if pc_potential_recovery else 0.95 ; deductible = max(0, pc_qualified_investment*factor - pc_recovery)",
     "inputs": ["pc_qualified_investment", "pc_potential_recovery", "pc_recovery"], "outputs": ["ponzi_deduction"], "sort_order": 4,
     "description": "W3. Section C: deductible theft loss = qualified investment (L45) × 95% (no potential third-party recovery) or 75% (potential recovery), less actual + potential insurance/SIPC recovery (L50). Flows to Section B Part I line 28."},
    {"rule_id": "R-4684-FDD", "title": "Federally-declared-disaster limitation gate (§165(h)(5))", "rule_type": "routing",
     "formula": "if not pa_is_fdd and pa_gains == 0: personal casualty loss NOT deductible ; financial-scam theft routes to Section B (not subject to FDD)",
     "inputs": ["pa_is_fdd", "is_financial_scam"], "outputs": ["fdd_blocks_deduction"], "sort_order": 5,
     "description": "W1/W4. For 2018-2025 (§165(h)(5)), a personal casualty/theft loss is deductible only if attributable to a federally declared disaster, except to the extent of personal casualty gains. A financial-scam theft loss (OBBBA, profit-motive) is an income-producing loss reported in Section B and is NOT subject to this limitation."},
]

F4684_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-4684-ITEM", "IRS_2025_F4684", "primary", "L5-9 / L23-27"),
    ("R-4684-ITEM", "IRC_165", "secondary", "§165 loss = lesser of basis or FMV decline"),
    ("R-4684-SECA", "IRS_2025_F4684", "primary", "Section A L10-18"),
    ("R-4684-SECA", "IRC_165", "primary", "§165(h)(1)/(2)/(5)"),
    ("R-4684-SECB", "IRS_2025_F4684", "primary", "Section B Part I/II L19-39"),
    ("R-4684-PONZI", "REVPROC_2009_20", "primary", "95%/75% safe harbor"),
    ("R-4684-PONZI", "IRS_2025_F4684", "secondary", "Section C L40-51"),
    ("R-4684-FDD", "IRC_165", "primary", "§165(h)(5) FDD-only 2018-2025"),
    ("R-4684-FDD", "IRS_2025_I4684", "secondary", "OBBBA qualified-disaster window + financial-scam theft"),
]

F4684_LINES: list[dict] = [
    {"line_number": "A_L8", "description": "Section A — smaller of basis or FMV decline", "line_type": "calculated", "source_rules": ["R-4684-ITEM"], "sort_order": 1},
    {"line_number": "A_L12", "description": "Section A — loss after $100/$500 floor", "line_type": "calculated", "source_rules": ["R-4684-SECA"], "sort_order": 2},
    {"line_number": "A_L18", "description": "Section A — deductible loss to Schedule A line 15", "line_type": "calculated", "source_rules": ["R-4684-SECA"], "sort_order": 3},
    {"line_number": "B_L27", "description": "Section B — per-property loss (business)", "line_type": "calculated", "source_rules": ["R-4684-SECB"], "sort_order": 4},
    {"line_number": "B_L31_39", "description": "Section B Part II — §1231/ordinary to Form 4797 (L3/L14)", "line_type": "calculated", "source_rules": ["R-4684-SECB"], "sort_order": 5},
    {"line_number": "C_L51", "description": "Section C — Ponzi deductible theft loss", "line_type": "calculated", "source_rules": ["R-4684-PONZI"], "sort_order": 6},
]

F4684_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_4684_FDD", "title": "Personal casualty loss requires a federally declared disaster", "severity": "warning",
     "condition": "not pa_is_fdd and pa_gains == 0",
     "message": "For 2018-2025 (§165(h)(5)), a casualty or theft loss of PERSONAL-use property is deductible only if the loss is attributable to a federally declared disaster (except to the extent of personal casualty gains). A non-disaster personal casualty loss is NOT deductible. Enter the FEMA disaster declaration number on Section A.",
     "notes": "W1."},
    {"diagnostic_id": "D_4684_QUALDIS", "title": "Qualified disaster — $500 floor, no 10%-AGI, add to standard deduction", "severity": "info",
     "condition": "pa_is_qualified_disaster",
     "message": "A qualified disaster loss (major disaster declared 1/1/2020-9/2/2025, incident beginning by 7/4/2025 and ending by 8/3/2025, OBBBA-extended) uses a $500 floor instead of $100, is NOT subject to the 10%-of-AGI limit, and may be added to the standard deduction (you need not itemize). This declaration window is OBBBA-set and changes each season — re-verify.",
     "notes": "W4. Year-keyed window."},
    {"diagnostic_id": "D_4684_TOTALDEST", "title": "Total destruction/theft of business property — use full basis", "severity": "info",
     "condition": "pb_total_destruction",
     "message": "If business or income-producing property was totally destroyed by casualty or lost from theft, the loss is the FULL adjusted basis (line 26 = line 20) — do not reduce by the FMV decline. FMV is only relevant for a partial casualty. Then subtract any insurance/reimbursement.",
     "notes": "W2."},
    {"diagnostic_id": "D_4684_1231", "title": "Section B routes to Form 4797 (§1231 vs ordinary)", "severity": "info",
     "condition": "pb_basis > 0",
     "message": "Section B casualty/theft of business property is netted by holding period on Form 4797: property held 1 year or less -> ordinary (Form 4797 line 14); held more than 1 year with gains >= losses -> §1231 capital gain (Form 4797 line 3); held more than 1 year with losses > gains -> ordinary (Form 4797 line 14). Partnerships report on 1065 Sch K line 11; S corporations on 1120-S Sch K line 10.",
     "notes": "W2."},
    {"diagnostic_id": "D_4684_PONZI", "title": "Ponzi-type theft safe harbor (95%/75%)", "severity": "info",
     "condition": "pc_qualified_investment > 0",
     "message": "Under the Rev. Proc. 2009-20 safe harbor (Section C), a qualified investor deducts 95% of the qualified investment if not pursuing a potential third-party recovery, or 75% if pursuing/intending to pursue one, less actual and potential insurance/SIPC recovery. The result flows to Section B Part I line 28. Attach the required Part II statements.",
     "notes": "W3."},
    {"diagnostic_id": "D_4684_SCAM", "title": "Financial-scam theft loss (OBBBA) — Section B, not FDD-limited", "severity": "info",
     "condition": "is_financial_scam",
     "message": "A victim of a financial scam involving a transaction entered into FOR PROFIT may claim a theft loss (OBBBA/2025) if: (1) the loss results from conduct that is criminal theft under applicable state law, (2) there is no reasonable prospect of recovery, and (3) the transaction was entered into for profit. Report it in Section B (income-producing) — it is NOT subject to the personal federally-declared-disaster limitation.",
     "notes": "W4."},
    {"diagnostic_id": "D_4684_165I", "title": "§165(i) election — deduct the disaster loss in the preceding year", "severity": "info",
     "condition": "pd_elect_165i",
     "message": "You may elect (Section D, §165(i)) to deduct a federally declared disaster loss on the return for the tax year IMMEDIATELY PRECEDING the disaster year (often accelerating the refund). The election is made by the due date (with extensions) of the disaster-year return; revocation follows the rules effective October 13, 2016. This is a filing-mechanics election — prepare the amended/prior-year return accordingly.",
     "notes": "Section D — diagnostic (not computed)."},
    {"diagnostic_id": "D_4684_RECOVERY", "title": "Reasonable prospect of recovery defers the loss", "severity": "warning",
     "condition": "pa_insurance == 0 and pb_insurance == 0",
     "message": "A casualty/theft loss is not 'sustained' while there is a reasonable prospect of recovery (e.g., a pending insurance claim or lawsuit) — subtract expected reimbursement even if not yet received, and defer the still-contested portion until the year recovery can be ascertained with reasonable certainty. Insurance counts whether or not you filed a claim; failing to file a timely claim bars the covered portion.",
     "notes": "Verify no expected reimbursement was omitted."},
]

F4684_SCENARIOS: list[dict] = [
    {"scenario_name": "4684-A — personal disaster loss (FDD, $100 + 10% AGI)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"pa_basis": 30000, "pa_fmv_before": 30000, "pa_fmv_after": 10000, "pa_insurance": 5000, "pa_is_fdd": True, "agi": 60000},
     "expected_outputs": {"item_loss": 15000.0, "section_a_deduction": 8900.0},
     "notes": "Loss = min(30,000 basis, 20,000 FMV decline) − 5,000 insurance = 15,000; − $100 = 14,900; − 10%×60,000 = 6,000 -> deductible 8,900 to Schedule A line 15."},
    {"scenario_name": "4684-B — non-disaster personal loss = not deductible", "scenario_type": "failure", "sort_order": 2,
     "inputs": {"pa_basis": 30000, "pa_fmv_before": 30000, "pa_fmv_after": 10000, "pa_insurance": 0, "pa_is_fdd": False, "agi": 60000},
     "expected_outputs": {"section_a_deduction": 0.0, "diagnostic": "D_4684_FDD"},
     "notes": "§165(h)(5): a personal casualty loss not attributable to a federally declared disaster is not deductible -> 0."},
    {"scenario_name": "4684-C — qualified disaster ($500 floor, no AGI)", "scenario_type": "edge", "sort_order": 3,
     "inputs": {"pa_basis": 30000, "pa_fmv_before": 30000, "pa_fmv_after": 10000, "pa_insurance": 0, "pa_is_fdd": True, "pa_is_qualified_disaster": True, "agi": 60000},
     "expected_outputs": {"item_loss": 20000.0, "section_a_deduction": 19500.0, "diagnostic": "D_4684_QUALDIS"},
     "notes": "Qualified disaster: loss 20,000 − $500 floor = 19,500; 10%-AGI floor waived; may be added to the standard deduction."},
    {"scenario_name": "4684-D — business total destruction -> full basis, §1231", "scenario_type": "edge", "sort_order": 4,
     "inputs": {"pb_basis": 50000, "pb_fmv_before": 45000, "pb_fmv_after": 0, "pb_insurance": 20000, "pb_total_destruction": True, "pb_holding_long": True, "pb_property_use": "trade_business"},
     "expected_outputs": {"section_b_loss": 30000.0, "section_b_route": "4797_L14_ordinary", "diagnostic": "D_4684_TOTALDEST"},
     "notes": "Total destruction -> full basis 50,000 (ignore the 45,000 FMV) − 20,000 insurance = 30,000 loss; >1yr, loss>gain -> ordinary (Form 4797 line 14)."},
    {"scenario_name": "4684-E — casualty gain (insurance > basis)", "scenario_type": "edge", "sort_order": 5,
     "inputs": {"pb_basis": 20000, "pb_insurance": 35000, "pb_fmv_before": 40000, "pb_fmv_after": 0, "pb_holding_long": True},
     "expected_outputs": {"item_gain": 15000.0, "section_b_route": "4797_L3_1231"},
     "notes": "Insurance 35,000 > basis 20,000 -> gain 15,000; >1yr, gain>=loss -> §1231 capital gain (Form 4797 line 3)."},
    {"scenario_name": "4684-F — Ponzi safe harbor (95%, no recovery pursued)", "scenario_type": "edge", "sort_order": 6,
     "inputs": {"pc_qualified_investment": 100000, "pc_potential_recovery": False, "pc_recovery": 10000},
     "expected_outputs": {"ponzi_deduction": 85000.0, "diagnostic": "D_4684_PONZI"},
     "notes": "95% × 100,000 = 95,000; − 10,000 recovery = 85,000 deductible theft loss (75% factor if pursuing recovery: 65,000)."},
    {"scenario_name": "4684-G — financial-scam theft (OBBBA, Section B)", "scenario_type": "edge", "sort_order": 7,
     "inputs": {"is_financial_scam": True, "pb_basis": 40000, "pb_insurance": 0, "pb_fmv_before": 40000, "pb_fmv_after": 0, "pb_holding_long": True},
     "expected_outputs": {"section_b_loss": 40000.0, "diagnostic": "D_4684_SCAM"},
     "notes": "Profit-motive financial-scam theft (state-law theft, no reasonable recovery) -> Section B income-producing loss 40,000; NOT subject to the personal FDD limitation."},
]

FORMS: list[dict] = [
    {
        "identity": {"form_number": "4684", "form_title": "Form 4684 — Casualties and Thefts (2025)",
                     "notes": "WO-16 (SPINE S-16, 3rd; DECISIONS D-18). Section A personal: loss = min(basis, FMV decline) − insurance; FDD-only §165(h)(5); $100/$500 floor; 10%-AGI floor (waived for qualified disaster; window declared 1/1/2020-9/2/2025, OBBBA); -> Schedule A L15/L16. Section B business: Part I per-property (total destruction -> full basis) + Part II §1231/ordinary holding-period routing to Form 4797 L3/L14. Section C Ponzi safe harbor (Rev. Proc. 2009-20, 95%/75%). Section D §165(i) preceding-year election = diagnostic. New OBBBA financial-scam theft loss (profit-motive, Section B). entity_types 1040/1065/1120S/1120. Year-keyed: qualified-disaster window."},
        "facts": F4684_FACTS, "rules": F4684_RULES, "rule_links": F4684_RULE_LINKS,
        "lines": F4684_LINES, "diagnostics": F4684_DIAGNOSTICS, "scenarios": F4684_SCENARIOS,
    },
]

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-4684-SECA", "title": "Personal casualty loss deductible only if federally declared disaster", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "draft", "sort_order": 1,
     "description": "Section A: a personal casualty/theft loss (min(basis, FMV decline) − insurance − $100/$500 − 10% AGI) is deductible only if attributable to a federally declared disaster (§165(h)(5)); otherwise 0.",
     "definition": {"rule": "R-4684-SECA", "check": "section_a_deduction = 0 if not pa_is_fdd else max(0, (loss - floor) - gains - 0.10*agi)"}},
    {"assertion_id": "FA-4684-4797", "title": "Section B business casualty routes to Form 4797 (§1231 L3 / ordinary L14)", "assertion_type": "reconciliation",
     "entity_types": ["1040", "1065", "1120S", "1120"], "status": "draft", "sort_order": 2,
     "description": "Section B net: held <=1yr or (>1yr and losses>gains) -> ordinary (Form 4797 line 14); held >1yr and gains>=losses -> §1231 capital gain (Form 4797 line 3).",
     "definition": {"rule": "R-4684-SECB", "check": "section_b_route in {4797_L14_ordinary, 4797_L3_1231}"}},
    {"assertion_id": "FA-4684-PONZI", "title": "Ponzi safe harbor 95%/75% flows to Section B line 28", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "draft", "sort_order": 3,
     "description": "Section C deductible theft loss = qualified investment × (95% no-recovery / 75% potential-recovery) − recoveries; carried to Section B Part I line 28.",
     "definition": {"rule": "R-4684-PONZI", "check": "ponzi_deduction = max(0, qualified_investment*factor - recovery)"}},
]


class Command(BaseCommand):
    help = "Load the Form 4684 spec (Casualties and Thefts, 2025). Refuses to seed until READY_TO_SEED=True (W1-W4)."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad Form 4684 spec (Casualties and Thefts)\n"))
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
                "\nREFUSING TO SEED FORM 4684: not cleared.\n\n"
                "Gated until Ken reviews (W1 Section A FDD gate + floors; W2 Section B §1231 routing;\n"
                "W3 Ponzi 95%/75%; W4 qualified-disaster window + financial-scam theft) and flips the\n"
                f"sentinel.\n\nREADY_TO_SEED = {READY_TO_SEED}\n\nEmpty:\n  {still}\n"
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
        self.stdout.write("Form 4684 loaded.")
        self.stdout.write(f"  4684: facts {len(F4684_FACTS)} / rules {len(F4684_RULES)} / lines {len(F4684_LINES)} / diag {len(F4684_DIAGNOSTICS)} / tests {len(F4684_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}")
        self.stdout.write("=" * 60)
