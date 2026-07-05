"""Load the Schedule K-1 (Form 1041) spec — Beneficiary's Share of Income, Deductions,
Credits, etc. (TY2025). Leg (b) of the 1041 module (S-11 / WO-09).

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
The ISSUER-SIDE beneficiary K-1: the Form 1041 fiduciary distributes DNI to each
beneficiary, and the K-1 reports that beneficiary's proportionate share of each
CLASS of income (character retained), the directly apportioned deductions, the
final-year deductions/carryovers, AMT items, credits, and other information.

This is the 1041's OWN beneficiary K-1 (`SCHEDULE_K1_1041`) — distinct from the
existing `load_1040_schedule_k1.py`, which is the RECEIVING side (a 1040 importing
a trust K-1 as `source_type="1041"`). Mirrors the 1065 precedent (`SCHEDULE_K1_1065`).

Depends on the spine leg (a): the entity DNI-class composition + the §662 tier
allocation come from `1041` (R-1041-CHAR / R-1041-TIERS). This leg encodes how
those flow onto the beneficiary K-1 boxes.

Greenfield: lookup/SCHEDULE_K1_1041/ → 404 at the 2026-07-05 gap-check.

═══════════════════════════════════════════════════════════════════════════
v1 SCOPE (per DECISIONS D-10 — K-1 full verbatim code transcription, 1065-K-1 precedent)
═══════════════════════════════════════════════════════════════════════════
COMPUTES:
  • Character retention — each beneficiary's boxes 1-8 = their proportionate share of
    each income class entering DNI (interest/dividends/cap-gain classes/portfolio/
    business/rental), NO losses in boxes 1-8 (i1041 p.45).
  • Box 9 directly apportioned deductions (depreciation / depletion / amortization) allocated.
  • Box 11 FINAL-YEAR deductions — §642(h) excess deductions (A §67(e), B non-misc itemized)
    + ST/LT capital-loss carryovers (C/D) + NOL (E) / ATNOL (F) — pass to the beneficiary
    ONLY on the estate's/trust's final return.
  • Box 14 information codes — A tax-exempt interest, E net investment income, H §1411 NIIT
    adjustment (→ beneficiary Form 8960 line 7), I §199A information.
  • RECON: Σ (all beneficiaries' box-N) = the entity's DNI class amount for that box.
FULL VERBATIM CODE LISTS (boxes 9/11/12/13/14) transcribed from the FINAL 2025
i1041 Sch K-1 as IRS_2025_I1041SK1 excerpts (source-grounded, not recalled).
STRUCTURE + FLAG:
  • Grantor-type trust → NO K-1 (grantor letter) — D_K1041_GRANTOR (mirrors the spine).
  • Box 12 AMT items are carried as structure; the Sch I AMT compute itself is RED-deferred (D-2).

═══════════════════════════════════════════════════════════════════════════
requires_human_review WALK ITEMS (W1-W3)
═══════════════════════════════════════════════════════════════════════════
W1. BOX/CODE STRUCTURE — boxes 1-14 + the box 9/11/12/13/14 code letters transcribed VERBATIM
    from the FINAL 2025 Schedule K-1 (Form 1041) (Created 5/2/25) + its beneficiary instructions
    (Cat. 11374Z, Mar 13 2025). CONFIRM the transcription.
W2. FINAL-YEAR GATE — box 11 excess deductions (§642(h)) + loss/NOL carryovers pass through ONLY
    on the final return; §67(g) suspends 2%-floor misc deductions through 2025 so those are NOT
    excess deductions on termination (only §67(e) / non-misc itemized survive). CONFIRM the gate.
W3. RECON — Σ beneficiary shares of each class = the entity DNI class amount; the allocation driver
    is the beneficiary's proportionate DNI share (from the spine §662 tier allocation). CONFIRM.

═══════════════════════════════════════════════════════════════════════════
SAFETY GUARD — READY_TO_SEED stays False until Ken approves the review walk (W1-W3).
═══════════════════════════════════════════════════════════════════════════
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

# ═══════════════════════════════════════════════════════════════════════════
# SAFETY GUARD — flip ONLY after Ken's in-session review walk (W1-W3 above).
#
# FLIPPED 2026-07-05 — Ken APPROVED the review walk in-session ("Approve — flip,
# seed, export, continue to GA 501"): W1 the box/code verbatim transcription,
# W2 the final-year §642(h) gate, W3 the character-retention + reconciliation —
# all blessed. Validated on throwaway SQLite (scratchpad/validate_1041_k1.py,
# 18 pass / 0 fail; seeds the spine first so the reused federal sources resolve).
# ═══════════════════════════════════════════════════════════════════════════
READY_TO_SEED = True


FORM_JURISDICTION = "federal"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1041"]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY TOPICS / SOURCES
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("fiduciary_k1", "Schedule K-1 (Form 1041): beneficiary's share of each DNI class (character "
     "retained), box 9 directly apportioned deductions, box 11 final-year §642(h) excess deductions "
     "+ carryovers, box 12 AMT, box 13 credits, box 14 info (§1411 NIIT, §199A)."),
]

# Reuse the federal sources the spine (leg a) already seeded.
EXISTING_SOURCES_TO_REFERENCE: list[str] = ["IRS_2025_I1041", "IRC_SUBCHAPTER_J"]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_F1041SK1",
        "source_type": "federal_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "US",
        "title": "2025 Schedule K-1 (Form 1041) — Beneficiary's Share of Income, Deductions, Credits, etc.",
        "citation": "Schedule K-1 (Form 1041) (2025), Cat. No. 11380D, Created 5/2/25",
        "issuer": "Internal Revenue Service",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f1041sk1.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.8,
        "topics": ["fiduciary_k1"],
        "excerpts": [
            {
                "excerpt_label": "Part III boxes 1-14 (2025 verbatim)",
                "excerpt_text": (
                    "Part III — Beneficiary's Share of Current Year Income, Deductions, Credits, and Other "
                    "Items: Box 1 Interest income; 2a Ordinary dividends; 2b Qualified dividends; 3 Net "
                    "short-term capital gain; 4a Net long-term capital gain; 4b 28% rate gain; 4c "
                    "Unrecaptured section 1250 gain; 5 Other portfolio and nonbusiness income; 6 Ordinary "
                    "business income; 7 Net rental real estate income; 8 Other rental income; 9 Directly "
                    "apportioned deductions (coded); 10 Estate tax deduction; 11 Final year deductions "
                    "(coded); 12 Alternative minimum tax adjustment (coded); 13 Credits and credit recapture "
                    "(coded); 14 Other information (coded). Coded boxes = 9, 11, 12, 13, 14 (codes printed on "
                    "page 2). No losses are entered in boxes 1-8; final-year losses/carryovers pass through "
                    "box 11."
                ),
                "summary_text": "K-1 (1041) Part III: boxes 1-8 income by class (no losses), box 9 directly apportioned deductions, box 10 estate tax deduction, boxes 11-14 coded (final-year, AMT, credits, other info).",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_I1041SK1",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "US",
        "title": "2025 Instructions for Schedule K-1 (Form 1041) for a Beneficiary Filing Form 1040",
        "citation": "Instructions for Schedule K-1 (Form 1041) (2025), Cat. No. 11374Z, dated Mar 13, 2025",
        "issuer": "Internal Revenue Service",
        "official_url": "https://www.irs.gov/pub/irs-prior/i1041sk1--2025.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.8,
        "topics": ["fiduciary_k1"],
        "excerpts": [
            {
                "excerpt_label": "Box 9 directly apportioned deductions + Box 11 final-year deductions (verbatim codes)",
                "excerpt_text": (
                    "Box 9 Directly apportioned deductions: A Depreciation; B Depletion; C Amortization. "
                    "Box 11 Final year deductions: A Excess deductions — Section 67(e) expenses (→ Sch 1 "
                    "(Form 1040) line 24k); B Excess deductions — Non-miscellaneous itemized deductions; C "
                    "Short-term capital loss carryover (→ Sch D line 5); D Long-term capital loss carryover "
                    "(→ Sch D line 12, and the 28%-rate + unrecaptured-1250 worksheets); E Net operating "
                    "loss carryover — regular tax (→ Sch 1 (Form 1040) line 8a); F Net operating loss "
                    "carryover — minimum tax (→ Form 6251 line 2f). Each excess deduction on termination "
                    "(§642(h)) retains its separate character; §67(g) suspends 2%-floor miscellaneous "
                    "itemized deductions through 2025, so those are NOT deductible as excess deductions."
                ),
                "summary_text": "Box 9: A depr/B depl/C amort. Box 11 final-year: A §67(e) excess/B non-misc itemized/C ST cap-loss CO/D LT cap-loss CO/E NOL/F ATNOL — pass through only in the final year; §67(g) 2% items excluded.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Box 12 AMT items (verbatim codes)",
                "excerpt_text": (
                    "Box 12 Alternative minimum tax adjustment: A Adjustment for minimum tax purposes (= "
                    "Form 6251 line 2j); B AMT adjustment attributable to qualified dividends; C ... to net "
                    "short-term capital gain; D ... to net long-term capital gain; E ... to unrecaptured "
                    "section 1250 gain; F ... to 28% rate gain; G Accelerated depreciation; H Depletion; I "
                    "Amortization; J Exclusion items (→ 2026 Form 8801). (The Form 1041 Schedule I AMT "
                    "COMPUTE is RED-deferred for season one per RS DECISIONS D-2; these codes are carried as "
                    "structure for the beneficiary's own Form 6251.)"
                ),
                "summary_text": "Box 12 AMT items A-J (A→6251 L2j; B-F class adjustments; G-I depr/depl/amort; J exclusion items→8801). Sch I AMT compute itself RED-deferred (D-2).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Box 13 credits + Box 14 other information (verbatim codes)",
                "excerpt_text": (
                    "Box 13 Credits and credit recapture: A Credit for estimated taxes; B Backup "
                    "withholding; C Low-income housing; D Advanced manufacturing production; E Clean "
                    "electricity production; F Work opportunity; G Small employer health insurance premiums; "
                    "H Biofuel producer; I Increasing research activities; J Renewable electricity "
                    "production; K Empowerment zone employment; L Clean fuel production; M Orphan drug; N "
                    "Employer-provided childcare facilities/services; O Biodiesel and renewable diesel fuels; "
                    "P Holders of tax credit bonds; Q Employer differential wage payments; R Recapture of "
                    "credits; S Advanced nuclear power facilities; T Zero-emission nuclear power production; "
                    "ZZ Other credits. Box 14 Other information: A Tax-exempt interest (→ 1040 line 2a); B "
                    "Foreign taxes; C Qualified rehabilitation expenditures; D Basis of energy property; E "
                    "Net investment income (→ Form 4952 line 4a); F Gross farm and fishing income; G Foreign "
                    "trading gross receipts (§942(a)); H Adjustment for section 1411 net investment income or "
                    "deductions (→ Form 8960 line 7); I Section 199A information; J Qualifying advanced coal/"
                    "gasification project property; K Qualifying advanced energy project property; L Advanced "
                    "manufacturing investment property; M Clean electricity investment credit; ZZ Other "
                    "information."
                ),
                "summary_text": "Box 13 credits A-T + ZZ. Box 14 info: A tax-exempt int→1040 L2a; E net investment income→4952 L4a; H §1411 NIIT adj→8960 L7; I §199A; B foreign taxes; etc.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Fiduciary box-fill + character retention (i1041 p.45)",
                "excerpt_text": (
                    "Boxes 1, 2a, 2b, 3, 4a-4c, 5, 6, 7, 8 are entered as the beneficiary's share of each "
                    "class of income entering DNI, minus allocable deductions; do NOT enter a loss in boxes "
                    "1-8. The beneficiary's income has the same proportion of each class of items entering "
                    "DNI that the total of each class has to DNI. §642(h) carryovers appear in box 11 codes "
                    "C/D (capital loss) and E/F (NOL/ATNOL) only on the final return. Grantor type trusts do "
                    "NOT use Schedule K-1 (grantor letter instead)."
                ),
                "summary_text": "Boxes 1-8 = beneficiary's proportionate share of each DNI class (no losses); §642(h) carryovers → box 11 final-year only; grantor trusts issue a grantor letter, not a K-1.",
                "is_key_excerpt": True,
            },
        ],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_F1041SK1", "SCHEDULE_K1_1041", "governs"),
    ("IRS_2025_I1041SK1", "SCHEDULE_K1_1041", "governs"),
    ("IRS_2025_I1041", "SCHEDULE_K1_1041", "informs"),
    ("IRC_SUBCHAPTER_J", "SCHEDULE_K1_1041", "governs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM — Schedule K-1 (Form 1041)
# ═══════════════════════════════════════════════════════════════════════════

K1_1041_FACTS: list[dict] = [
    {"fact_key": "is_grantor_trust", "label": "Grantor-type trust? (if True, NO K-1 — issue a grantor letter)", "data_type": "boolean", "required": False, "sort_order": 1,
     "notes": "Mirrors the spine D_1041_GRANTOR. A grantor trust does not issue Schedule K-1."},
    {"fact_key": "is_final_year", "label": "Final return of the estate/trust? (gates box 11 §642(h) carryovers)", "data_type": "boolean", "required": False, "sort_order": 2,
     "notes": "W2. Box 11 excess deductions + loss/NOL carryovers pass to beneficiaries ONLY in the final year."},
    {"fact_key": "beneficiary_dni_pct", "label": "Beneficiary's proportionate share of DNI (%) — the allocation driver", "data_type": "decimal", "required": False, "sort_order": 3,
     "notes": "W3. From the spine §662 tier allocation (R-1041-TIERS). Each income class × this % (character retained)."},
    # Entity DNI-class composition (from the spine; inputs to the K-1 allocation)
    {"fact_key": "ent_interest", "label": "Entity interest income in DNI (→ box 1)", "data_type": "decimal", "required": False, "sort_order": 10},
    {"fact_key": "ent_ordinary_dividends", "label": "Entity ordinary dividends in DNI (→ box 2a)", "data_type": "decimal", "required": False, "sort_order": 11},
    {"fact_key": "ent_qualified_dividends", "label": "Entity qualified dividends in DNI (→ box 2b)", "data_type": "decimal", "required": False, "sort_order": 12},
    {"fact_key": "ent_st_capital_gain", "label": "Entity net short-term capital gain distributed (→ box 3)", "data_type": "decimal", "required": False, "sort_order": 13},
    {"fact_key": "ent_lt_capital_gain", "label": "Entity net long-term capital gain distributed (→ box 4a)", "data_type": "decimal", "required": False, "sort_order": 14,
     "notes": "Cap gains reach the beneficiary only when included in DNI (Reg. §1.643(a)-3(b)) or on the final year."},
    {"fact_key": "ent_28_rate_gain", "label": "Entity 28% rate gain (→ box 4b)", "data_type": "decimal", "required": False, "sort_order": 15},
    {"fact_key": "ent_unrecap_1250", "label": "Entity unrecaptured §1250 gain (→ box 4c)", "data_type": "decimal", "required": False, "sort_order": 16},
    {"fact_key": "ent_other_portfolio", "label": "Entity other portfolio & nonbusiness income (→ box 5)", "data_type": "decimal", "required": False, "sort_order": 17},
    {"fact_key": "ent_business_income", "label": "Entity ordinary business income (→ box 6)", "data_type": "decimal", "required": False, "sort_order": 18},
    {"fact_key": "ent_rental_re", "label": "Entity net rental real estate income (→ box 7)", "data_type": "decimal", "required": False, "sort_order": 19},
    {"fact_key": "ent_other_rental", "label": "Entity other rental income (→ box 8)", "data_type": "decimal", "required": False, "sort_order": 20},
    # Box 9 directly apportioned deductions
    {"fact_key": "ent_depreciation", "label": "Directly apportioned depreciation (→ box 9 code A)", "data_type": "decimal", "required": False, "sort_order": 30},
    {"fact_key": "ent_depletion", "label": "Directly apportioned depletion (→ box 9 code B)", "data_type": "decimal", "required": False, "sort_order": 31},
    {"fact_key": "ent_amortization", "label": "Directly apportioned amortization (→ box 9 code C)", "data_type": "decimal", "required": False, "sort_order": 32},
    {"fact_key": "ent_estate_tax_deduction", "label": "Estate tax deduction (→ box 10)", "data_type": "decimal", "required": False, "sort_order": 33},
    # Box 11 final-year deductions (§642(h))
    {"fact_key": "fy_excess_ded_67e", "label": "Excess deductions — §67(e) expenses (→ box 11 code A, final year)", "data_type": "decimal", "required": False, "sort_order": 40,
     "notes": "W2. To the beneficiary's Sch 1 (Form 1040) line 24k. §67(e) admin costs survive; §67(g) 2% items do not."},
    {"fact_key": "fy_excess_ded_nonmisc", "label": "Excess deductions — non-misc itemized (→ box 11 code B, final year)", "data_type": "decimal", "required": False, "sort_order": 41},
    {"fact_key": "fy_st_caploss_co", "label": "Short-term capital loss carryover (→ box 11 code C, final year)", "data_type": "decimal", "required": False, "sort_order": 42},
    {"fact_key": "fy_lt_caploss_co", "label": "Long-term capital loss carryover (→ box 11 code D, final year)", "data_type": "decimal", "required": False, "sort_order": 43},
    {"fact_key": "fy_nol_co", "label": "NOL carryover — regular tax (→ box 11 code E, final year)", "data_type": "decimal", "required": False, "sort_order": 44},
    {"fact_key": "fy_atnol_co", "label": "NOL carryover — minimum tax / ATNOL (→ box 11 code F, final year)", "data_type": "decimal", "required": False, "sort_order": 45},
    # Box 12 / 14 selected
    {"fact_key": "amt_adjustment_12a", "label": "AMT adjustment for minimum tax purposes (→ box 12 code A → 6251 L2j)", "data_type": "decimal", "required": False, "sort_order": 50,
     "notes": "Structure only; the Sch I AMT compute is RED-deferred (D-2)."},
    {"fact_key": "ent_tax_exempt_interest", "label": "Tax-exempt interest (→ box 14 code A → 1040 L2a)", "data_type": "decimal", "required": False, "sort_order": 51},
    {"fact_key": "ent_niit_adjustment_14h", "label": "§1411 net investment income adjustment (→ box 14 code H → Form 8960 L7)", "data_type": "decimal", "required": False, "sort_order": 52},
    {"fact_key": "sec199a_info_14i", "label": "§199A information (→ box 14 code I)", "data_type": "string", "required": False, "sort_order": 53},
    {"fact_key": "foreign_taxes_14b", "label": "Foreign taxes (→ box 14 code B)", "data_type": "decimal", "required": False, "sort_order": 54},
]

K1_1041_RULES: list[dict] = [
    {"rule_id": "R-K1041-GRANT", "title": "Grantor trust issues no K-1", "rule_type": "conditional",
     "formula": "if is_grantor_trust: do NOT produce Schedule K-1 — issue a grantor letter (entity info only, dollars on an attachment).",
     "inputs": ["is_grantor_trust"], "outputs": [], "sort_order": 1,
     "description": "i1041 p.43/45. A grantor-type trust's income is taxed to the grantor; no K-1 is issued."},
    {"rule_id": "R-K1041-CHAR", "title": "Character retention — boxes 1-8 by DNI class", "rule_type": "calculation",
     "formula": ("for each class c in (interest, ord_div, qual_div, st_capgain, lt_capgain, 28_gain, "
                 "unrecap_1250, other_portfolio, business, rental_re, other_rental): "
                 "box[c] = round(ent_[c] * beneficiary_dni_pct / 100) ; no losses in boxes 1-8"),
     "inputs": ["beneficiary_dni_pct", "ent_interest", "ent_ordinary_dividends", "ent_qualified_dividends",
                "ent_st_capital_gain", "ent_lt_capital_gain", "ent_other_portfolio", "ent_business_income", "ent_rental_re"],
     "outputs": ["box1", "box2a", "box2b", "box3", "box4a", "box5", "box6", "box7", "box8"], "sort_order": 2,
     "description": "W3. i1041 p.44/45. Each beneficiary's share of a class = the class's proportion of DNI × the beneficiary's DNI share. Character is retained (interest stays interest, etc.)."},
    {"rule_id": "R-K1041-BOX9", "title": "Box 9 directly apportioned deductions", "rule_type": "calculation",
     "formula": "box9A = round(ent_depreciation * pct/100) ; box9B = round(ent_depletion * pct/100) ; box9C = round(ent_amortization * pct/100)",
     "inputs": ["ent_depreciation", "ent_depletion", "ent_amortization", "beneficiary_dni_pct"],
     "outputs": ["box9A", "box9B", "box9C"], "sort_order": 3,
     "description": "Box 9 codes A depreciation / B depletion / C amortization, directly apportioned to the beneficiary."},
    {"rule_id": "R-K1041-FINYR", "title": "Box 11 final-year deductions (§642(h)) — final year only", "rule_type": "conditional",
     "formula": ("if is_final_year: box11A = fy_excess_ded_67e ; box11B = fy_excess_ded_nonmisc ; "
                 "box11C = fy_st_caploss_co ; box11D = fy_lt_caploss_co ; box11E = fy_nol_co ; box11F = fy_atnol_co ; "
                 "else: box 11 is BLANK (carryovers do not pass through in a non-final year)"),
     "inputs": ["is_final_year", "fy_excess_ded_67e", "fy_excess_ded_nonmisc", "fy_st_caploss_co", "fy_lt_caploss_co", "fy_nol_co", "fy_atnol_co"],
     "outputs": ["box11A", "box11B", "box11C", "box11D", "box11E", "box11F"], "sort_order": 4,
     "description": "W2. §642(h). Excess deductions on termination (A §67(e) → 1040 Sch 1 L24k; B non-misc itemized) + ST/LT capital-loss carryovers (C/D) + NOL (E) / ATNOL (F) pass to the beneficiary ONLY on the final return. §67(g) 2% items are not excess deductions."},
    {"rule_id": "R-K1041-BOX14", "title": "Box 14 information — tax-exempt int, NIIT, §199A", "rule_type": "routing",
     "formula": ("box14A = round(ent_tax_exempt_interest * pct/100) -> beneficiary 1040 L2a ; "
                 "box14H = ent_niit_adjustment_14h -> beneficiary Form 8960 line 7 ; "
                 "box14I = sec199a_info -> beneficiary QBI ; box14B = foreign_taxes"),
     "inputs": ["ent_tax_exempt_interest", "ent_niit_adjustment_14h", "sec199a_info_14i", "foreign_taxes_14b", "beneficiary_dni_pct"],
     "outputs": ["box14A", "box14H", "box14I"], "sort_order": 5,
     "description": "Box 14 codes: A tax-exempt interest (→ 1040 L2a), E net investment income (→ 4952 L4a), H §1411 NIIT adjustment (→ Form 8960 line 7), I §199A information."},
    {"rule_id": "R-K1041-NOLOSS", "title": "No losses in boxes 1-8", "rule_type": "validation",
     "formula": "for boxes 1-8: value = max(0, allocated share). A distributed loss does NOT appear in boxes 1-8; a beneficiary receives a loss only via box 11 (final-year carryovers).",
     "inputs": [], "outputs": [], "sort_order": 6,
     "description": "i1041 p.45. Current-year losses are trapped at the entity except on the final year (box 11 C/D/E/F)."},
    {"rule_id": "R-K1041-RECON", "title": "Reconciliation — Σ beneficiary shares = entity DNI class", "rule_type": "validation",
     "formula": "for each class c: Σ (all beneficiaries' box[c]) == ent_[c] (the amount of class c carried out in DNI), within rounding.",
     "inputs": [], "outputs": [], "sort_order": 7,
     "description": "W3. The sum of every beneficiary's K-1 share of a class equals the entity's DNI amount for that class. The IDD (spine Sch B L15) equals the taxable DNI carried out on all K-1s."},
]

K1_1041_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-K1041-GRANT", "IRS_2025_I1041SK1", "primary", "grantor trust issues a grantor letter, not a K-1"),
    ("R-K1041-GRANT", "IRC_SUBCHAPTER_J", "secondary", "grantor trust rules (§§671-679)"),
    ("R-K1041-CHAR", "IRS_2025_I1041SK1", "primary", "character retention by DNI class (fiduciary box-fill p.45)"),
    ("R-K1041-CHAR", "IRS_2025_I1041", "secondary", "character of income proportional to DNI classes (p.44)"),
    ("R-K1041-BOX9", "IRS_2025_I1041SK1", "primary", "box 9 codes A/B/C directly apportioned deductions"),
    ("R-K1041-FINYR", "IRS_2025_I1041SK1", "primary", "box 11 final-year §642(h) deductions + carryovers, codes A-F"),
    ("R-K1041-FINYR", "IRC_SUBCHAPTER_J", "secondary", "§642(h) excess deductions on termination"),
    ("R-K1041-BOX14", "IRS_2025_I1041SK1", "primary", "box 14 codes A/E/H/I (tax-exempt, NII, §1411, §199A)"),
    ("R-K1041-NOLOSS", "IRS_2025_I1041SK1", "primary", "no losses in boxes 1-8 (p.45)"),
    ("R-K1041-RECON", "IRS_2025_F1041SK1", "primary", "Σ beneficiary shares reconcile to entity DNI classes"),
    ("R-K1041-RECON", "IRS_2025_I1041", "secondary", "IDD = taxable DNI carried out on the K-1s"),
]

K1_1041_LINES: list[dict] = [
    {"line_number": "1", "description": "Box 1 Interest income", "line_type": "calculated", "source_rules": ["R-K1041-CHAR"], "sort_order": 1},
    {"line_number": "2a", "description": "Box 2a Ordinary dividends", "line_type": "calculated", "source_rules": ["R-K1041-CHAR"], "sort_order": 2},
    {"line_number": "2b", "description": "Box 2b Qualified dividends", "line_type": "calculated", "source_rules": ["R-K1041-CHAR"], "sort_order": 3},
    {"line_number": "3", "description": "Box 3 Net short-term capital gain", "line_type": "calculated", "source_rules": ["R-K1041-CHAR"], "sort_order": 4},
    {"line_number": "4a", "description": "Box 4a Net long-term capital gain", "line_type": "calculated", "source_rules": ["R-K1041-CHAR"], "sort_order": 5},
    {"line_number": "4b", "description": "Box 4b 28% rate gain", "line_type": "calculated", "source_rules": ["R-K1041-CHAR"], "sort_order": 6},
    {"line_number": "4c", "description": "Box 4c Unrecaptured §1250 gain", "line_type": "calculated", "source_rules": ["R-K1041-CHAR"], "sort_order": 7},
    {"line_number": "5", "description": "Box 5 Other portfolio and nonbusiness income", "line_type": "calculated", "source_rules": ["R-K1041-CHAR"], "sort_order": 8},
    {"line_number": "6", "description": "Box 6 Ordinary business income", "line_type": "calculated", "source_rules": ["R-K1041-CHAR"], "sort_order": 9},
    {"line_number": "7", "description": "Box 7 Net rental real estate income", "line_type": "calculated", "source_rules": ["R-K1041-CHAR"], "sort_order": 10},
    {"line_number": "8", "description": "Box 8 Other rental income", "line_type": "calculated", "source_rules": ["R-K1041-CHAR"], "sort_order": 11},
    {"line_number": "9", "description": "Box 9 Directly apportioned deductions (A depr / B depl / C amort)", "line_type": "calculated", "source_rules": ["R-K1041-BOX9"], "sort_order": 12},
    {"line_number": "10", "description": "Box 10 Estate tax deduction", "line_type": "input", "source_facts": ["ent_estate_tax_deduction"], "sort_order": 13},
    {"line_number": "11", "description": "Box 11 Final year deductions (A §67(e) / B non-misc / C ST-CO / D LT-CO / E NOL / F ATNOL)", "line_type": "calculated", "source_rules": ["R-K1041-FINYR"], "sort_order": 14},
    {"line_number": "12", "description": "Box 12 Alternative minimum tax adjustment (A-J)", "line_type": "input", "source_facts": ["amt_adjustment_12a"], "sort_order": 15},
    {"line_number": "13", "description": "Box 13 Credits and credit recapture (A-T, ZZ)", "line_type": "informational", "sort_order": 16},
    {"line_number": "14", "description": "Box 14 Other information (A tax-exempt int / E NII / H §1411 / I §199A)", "line_type": "calculated", "source_rules": ["R-K1041-BOX14"], "sort_order": 17},
]

K1_1041_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_K1041_GRANTOR", "title": "Grantor trust — do not issue a K-1 (grantor letter)", "severity": "warning",
     "condition": "is_grantor_trust",
     "message": "A grantor-type trust does NOT issue Schedule K-1. Provide the grantor with a grantor letter (the income, deductions, and credits statement) instead; the items are taxed directly to the grantor.",
     "notes": "Mirrors the spine D_1041_GRANTOR."},
    {"diagnostic_id": "D_K1041_FINYR", "title": "Final-year deductions (§642(h)) pass through only on the final return", "severity": "info",
     "condition": "fy_* carryover present and NOT is_final_year",
     "message": "Excess deductions on termination (box 11 A/B), capital-loss carryovers (C/D), and NOL/ATNOL carryovers (E/F) pass to beneficiaries ONLY on the estate's/trust's FINAL return. In a non-final year these stay with the entity. Confirm the final-year box is checked before populating box 11.",
     "notes": "W2. §642(h)."},
    {"diagnostic_id": "D_K1041_67E", "title": "Box 11 code A excess deductions route to the beneficiary's Sch 1 line 24k", "severity": "info",
     "condition": "fy_excess_ded_67e > 0 and is_final_year",
     "message": "Box 11 code A (§67(e) excess deductions on termination) flows to the beneficiary's Schedule 1 (Form 1040) line 24k as an above-the-line deduction. §67(g) suspends 2%-floor miscellaneous itemized deductions through 2025, so only §67(e) administration costs and non-miscellaneous itemized deductions survive as excess deductions.",
     "notes": "W2. §67(e)/§67(g)/TD 9918."},
    {"diagnostic_id": "D_K1041_NOLOSS", "title": "No losses in boxes 1-8", "severity": "warning",
     "condition": "an allocated class share is negative",
     "message": "Boxes 1-8 cannot report a loss. Current-year losses are trapped at the entity level; a beneficiary receives a loss only through box 11 (final-year capital-loss/NOL carryovers). Do not enter a negative amount in boxes 1-8.",
     "notes": "i1041 p.45. R-K1041-NOLOSS."},
    {"diagnostic_id": "D_K1041_NIIT", "title": "Box 14 code H — §1411 adjustment to the beneficiary's Form 8960", "severity": "info",
     "condition": "ent_niit_adjustment_14h != 0",
     "message": "Box 14 code H reports the beneficiary's share of the §1411 net investment income adjustment, which the beneficiary carries to Form 8960 line 7. Distributed net investment income is taxed at the BENEFICIARY level (only UNdistributed NII is taxed on the trust's Schedule G line 5).",
     "notes": "§1411. Coordinates with the spine D_1041_NIIT."},
    {"diagnostic_id": "D_K1041_RECON", "title": "K-1 shares must reconcile to entity DNI classes", "severity": "info",
     "condition": "Σ beneficiary box[c] != entity DNI class c",
     "message": "The sum of all beneficiaries' shares of each income class must equal the amount of that class carried out in DNI (and total distributions ≤ DNI drive the income distribution deduction). If the K-1s don't reconcile to the entity's Schedule B, the allocation percentages or the DNI composition is off.",
     "notes": "W3. R-K1041-RECON."},
]

K1_1041_SCENARIOS: list[dict] = [
    {"scenario_name": "K1041-T1 — two beneficiaries 60/40, character retained", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"is_final_year": False, "ent_interest": 10000, "ent_ordinary_dividends": 5000,
                "beneficiaries": [{"name": "A", "beneficiary_dni_pct": 60}, {"name": "B", "beneficiary_dni_pct": 40}]},
     "expected_outputs": {"A_box1": 6000, "A_box2a": 3000, "B_box1": 4000, "B_box2a": 2000},
     "notes": "DNI = 10,000 interest + 5,000 dividends. A (60%): box1 6,000 / box2a 3,000. B (40%): box1 4,000 / box2a 2,000. Character retained; Σ box1 = 10,000, Σ box2a = 5,000 (reconciles)."},
    {"scenario_name": "K1041-T2 — single beneficiary, DNI limits the carry-out", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"is_final_year": False, "ent_interest": 20000, "beneficiary_dni_pct": 100},
     "expected_outputs": {"box1": 20000},
     "notes": "One beneficiary, 100% of DNI: box1 = 20,000 interest carried out."},
    {"scenario_name": "K1041-T3 — final year: excess deductions + capital loss carryover pass through", "scenario_type": "edge", "sort_order": 3,
     "inputs": {"is_final_year": True, "beneficiary_dni_pct": 100,
                "fy_excess_ded_67e": 3000, "fy_lt_caploss_co": 8000},
     "expected_outputs": {"box11A": 3000, "box11D": 8000},
     "notes": "Final return: box 11 code A (§67(e) excess deductions) 3,000 → beneficiary Sch 1 L24k; code D (LT capital-loss carryover) 8,000 → beneficiary Sch D L12."},
    {"scenario_name": "K1041-T4 — NON-final year: no carryovers pass through", "scenario_type": "edge", "sort_order": 4,
     "inputs": {"is_final_year": False, "fy_excess_ded_67e": 3000, "fy_lt_caploss_co": 8000},
     "expected_outputs": {"box11A": 0, "box11D": 0, "diagnostic": "D_K1041_FINYR"},
     "notes": "Not the final year → box 11 stays BLANK; the excess deductions and loss carryover remain with the trust. D_K1041_FINYR fires."},
    {"scenario_name": "K1041-T5 — grantor trust issues no K-1", "scenario_type": "failure", "sort_order": 5,
     "inputs": {"is_grantor_trust": True, "ent_interest": 5000},
     "expected_outputs": {"diagnostic": "D_K1041_GRANTOR", "k1_issued": False},
     "notes": "Grantor trust: no Schedule K-1 — issue a grantor letter. D_K1041_GRANTOR fires."},
    {"scenario_name": "K1041-T6 — §1411 NIIT adjustment routes to the beneficiary (box 14H)", "scenario_type": "edge", "sort_order": 6,
     "inputs": {"is_final_year": False, "beneficiary_dni_pct": 100, "ent_interest": 12000, "ent_niit_adjustment_14h": 12000},
     "expected_outputs": {"box1": 12000, "box14H": 12000},
     "notes": "Distributed NII: box 14 code H = 12,000 → beneficiary Form 8960 line 7 (taxed at the beneficiary level, not on the trust's Sch G L5)."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORMS registry + flow assertions
# ═══════════════════════════════════════════════════════════════════════════

FORMS: list[dict] = [
    {
        "identity": {"form_number": "SCHEDULE_K1_1041", "form_title": "Schedule K-1 (Form 1041) — Beneficiary's Share of Income, Deductions, Credits, etc. (TY2025)",
                     "notes": "Leg (b) of the 1041 module (S-11/WO-09). Issuer-side beneficiary K-1: boxes 1-8 = the beneficiary's proportionate share of each DNI income class (character retained, no losses); box 9 directly apportioned deductions (depr/depl/amort); box 10 estate tax deduction; box 11 final-year §642(h) excess deductions + loss/NOL carryovers (final year ONLY); box 12 AMT items (structure; Sch I compute RED-deferred D-2); box 13 credits; box 14 other info (tax-exempt int, §1411 NIIT → 8960 L7, §199A). Full verbatim box 9/11/12/13/14 code lists transcribed from the FINAL 2025 i1041 Sch K-1. Grantor trusts issue a grantor letter, not a K-1. Reconciles: Σ beneficiary class shares = entity DNI class. Distinct from load_1040_schedule_k1.py (the receiving side)."},
        "facts": K1_1041_FACTS, "rules": K1_1041_RULES, "rule_links": K1_1041_RULE_LINKS,
        "lines": K1_1041_LINES, "diagnostics": K1_1041_DIAGNOSTICS, "scenarios": K1_1041_SCENARIOS,
    },
]

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-K1041-CHAR", "title": "K-1 boxes 1-8 retain DNI class character proportionally", "assertion_type": "flow_assertion",
     "entity_types": ["1041"], "status": "draft", "sort_order": 1,
     "description": "Each beneficiary's box for a class = (entity class amount in DNI) × (beneficiary's DNI %). Interest stays box 1, dividends box 2, etc. No losses in boxes 1-8.",
     "definition": {"rule": "R-K1041-CHAR", "check": "box[c] = round(ent_[c] * beneficiary_dni_pct / 100)"}},
    {"assertion_id": "FA-K1041-RECON", "title": "Σ beneficiary K-1 shares reconcile to entity DNI classes", "assertion_type": "reconciliation",
     "entity_types": ["1041"], "status": "draft", "sort_order": 2,
     "description": "For each income class, the sum of all beneficiaries' K-1 amounts equals the amount of that class carried out in DNI. The total taxable DNI carried out equals the Schedule B income distribution deduction (L15).",
     "definition": {"rule": "R-K1041-RECON", "check": "sum(box[c] over beneficiaries) == ent_[c]; total == Sch B L15"}},
    {"assertion_id": "FA-K1041-FINYR", "title": "Box 11 §642(h) carryovers pass through only in the final year", "assertion_type": "flow_assertion",
     "entity_types": ["1041"], "status": "draft", "sort_order": 3,
     "description": "Excess deductions (11A/B) and capital-loss/NOL carryovers (11C/D/E/F) appear on the K-1 only when is_final_year; otherwise box 11 is blank and the attributes stay with the entity.",
     "definition": {"rule": "R-K1041-FINYR", "check": "box11* populated iff is_final_year"}},
    {"assertion_id": "FA-K1041-NIIT", "title": "Distributed NII taxed at the beneficiary (box 14H → 8960 L7)", "assertion_type": "flow_assertion",
     "entity_types": ["1041"], "status": "draft", "sort_order": 4,
     "description": "Box 14 code H carries the beneficiary's §1411 net investment income adjustment to Form 8960 line 7. Only UNdistributed NII is taxed on the trust's Schedule G line 5 — distributed NII follows the income to the beneficiary.",
     "definition": {"rule": "R-K1041-BOX14", "check": "box14H -> beneficiary Form 8960 line 7"}},
]


# ═══════════════════════════════════════════════════════════════════════════
# Command
# ═══════════════════════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = (
        "Load the Schedule K-1 (Form 1041) spec (beneficiary's share, TY2025). "
        "Refuses to seed until Ken sets READY_TO_SEED=True after the review walk (W1-W3)."
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad Schedule K-1 (Form 1041) spec\n"))
        self._load_topics()
        sources = self._load_sources()
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
                "\nREFUSING TO SEED SCHEDULE K-1 (FORM 1041): not cleared to seed.\n\n"
                "Content is authored, but seeding is gated until Ken reviews the packet\n"
                "(W1 the box/code transcription; W2 the final-year §642(h) gate; W3 the\n"
                "character-retention + reconciliation) and flips the sentinel.\n\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True to proceed)\n\n"
                f"Currently empty / placeholder:\n  {still_empty}\n\n"
                "To proceed: review the module-level data lists (and f1041_source_brief.md),\n"
                "then set READY_TO_SEED = True. Idempotent via update_or_create."
            )

    def _load_topics(self):
        ct = 0
        for code, name in AUTHORITY_TOPICS:
            _, created = AuthorityTopic.objects.update_or_create(topic_code=code, defaults={"topic_name": name})
            if created:
                ct += 1
        self.stdout.write(f"Topics: {ct} new ({len(AUTHORITY_TOPICS)} in batch)")

    def _load_sources(self) -> dict:
        sources: dict = {}
        for src_data in AUTHORITY_SOURCES:
            src_data = dict(src_data)
            excerpts_data = src_data.pop("excerpts", [])
            topic_codes = src_data.pop("topics", [])
            source, _ = AuthoritySource.objects.update_or_create(
                source_code=src_data["source_code"], defaults=src_data,
            )
            sources[source.source_code] = source
            for exc in excerpts_data:
                exc = dict(exc)
                AuthorityExcerpt.objects.update_or_create(
                    authority_source=source, excerpt_label=exc["excerpt_label"], defaults=exc,
                )
            for tc in topic_codes:
                topic = AuthorityTopic.objects.filter(topic_code=tc).first()
                if topic:
                    AuthoritySourceTopic.objects.get_or_create(authority_source=source, authority_topic=topic)
        for code in EXISTING_SOURCES_TO_REFERENCE:
            src = AuthoritySource.objects.filter(source_code=code).first()
            if src:
                sources[code] = src
            else:
                self.stdout.write(self.style.WARNING(f"  existing source {code} NOT FOUND — links to it will be skipped"))
        self.stdout.write(f"Sources ready: {len(sources)}")
        return sources

    def _upsert_form(self, identity: dict) -> TaxForm:
        form, created = TaxForm.objects.update_or_create(
            form_number=identity["form_number"], jurisdiction=FORM_JURISDICTION,
            tax_year=FORM_TAX_YEAR, version=FORM_VERSION,
            defaults={"form_title": identity["form_title"], "entity_types": FORM_ENTITY_TYPES,
                      "status": FORM_STATUS, "notes": identity["notes"]},
        )
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
                    defaults={"support_level": level, "relevance_note": note},
                )
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
                    defaults={"note": f"{source_code} -> {form_code}"},
                )

    def _load_flow_assertions(self):
        for a in FLOW_ASSERTIONS:
            a = dict(a)
            FlowAssertion.objects.update_or_create(assertion_id=a.pop("assertion_id"), defaults=a)
        self.stdout.write(f"  {len(FLOW_ASSERTIONS)} flow assertions")

    def _report_totals(self):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("Schedule K-1 (Form 1041) loaded.")
        self.stdout.write(
            f"  SCHEDULE_K1_1041: facts {len(K1_1041_FACTS)} / rules {len(K1_1041_RULES)} / "
            f"lines {len(K1_1041_LINES)} / diag {len(K1_1041_DIAGNOSTICS)} / tests {len(K1_1041_SCENARIOS)} / "
            f"FA {len(FLOW_ASSERTIONS)}"
        )
        self.stdout.write("=" * 60)
