"""Load the SCHEDULE_E (Part I) + FORM_8582 specs — Supplemental Income and Loss
(rental real estate & royalties) and the Passive Activity Loss Limitations that
gate the rental losses.

Post-sprint NEXT-UP #6. ONE topic, never split (SPRINT_SCOPE line 107: the
$25,000 special allowance lives on Form 8582; Schedule E page 1 without it is the
half-done trap). Schedule E Part I net rental/royalty income or loss → Schedule 1
line 5 → 1040 line 8; rental real estate losses with active participation are
limited by Form 8582's $25,000 special allowance (MAGI-phased), the remainder
suspended (carryforward). Two forms in one loader (the load_1040_schedule_d
3-form precedent).

CONSTANTS VERIFIED 2026-06-13 (tts-tax-app server/specs/_schedule_e_8582_source_brief.md;
IRS i8582 + i1040se + the f8582.pdf / f1040se.pdf line dumps):
  Form 8582 §469(i) special allowance (NON-indexed statutory, stable since 1986):
    - $25,000 maximum (single / MFJ), active participation in rental real estate.
    - line 5 = $150,000 ($75,000 MFS-apart); line 7 = line 5 − MAGI; line 8 =
      50% × line 7, capped $25,000 ($12,500 MFS-apart); line 9 = min(line 4 loss,
      line 8). Fully phased out at MAGI = $150,000 ($75,000 MFS-apart).
    - MFS who lived WITH spouse at any time → $0 special allowance (skip Part II).
  8582 MAGI = AGI figured WITHOUT: the passive loss itself, the RE-professional
    rental loss, taxable SS/RRB, the IRA + §501(c)(18) deduction, ½ SE-tax
    deduction, the §135 savings-bond interest exclusion, the §137 adoption
    exclusion, the §221 student-loan-interest deduction, the §250 FDII/GILTI
    deduction. (§199A is NOT a MAGI add-back — verified.)
  Schedule E Part I: property types 1-8 (1 SFR / 2 Multi-Family / 3 Vacation-
    Short-Term / 4 Commercial / 5 Land / 6 Royalties / 7 Self-Rental / 8 Other);
    line 22 = "deductible rental real estate loss after limitation from Form
    8582"; line 26 → Schedule 1 line 5.

KEN'S CONFIRMED SCOPE (2026-06-13, AskUserQuestion): (1) REUSE + EXTEND the
RentalProperty model (route by parent form code); (2) 8582 v1 = the SIMPLIFIED
active-participation bucket (the per-activity Parts IV/V Worksheets are a
follow-up; v1 computes the aggregate columns from the RentalProperty rows + the
prior-year-suspended fact); (3) RED-DEFER real estate professional
(D_8582_RE_PRO); (4) COMPUTE the proper 8582 modified AGI (the add-backs; flag
the ones we lack with D_8582_005).

Source brief: tts-tax-app `server/specs/_schedule_e_8582_source_brief.md`.

SAFETY GUARD: READY_TO_SEED stays False until Ken's review walk (the $25k
allowance + the MAGI phaseout + the MFS amounts + the netting + the MAGI
add-back list + the v1 simplified-bucket deviations).
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


READY_TO_SEED = False  # Gated until Ken's review walk.


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_ENTITY_TYPES = ["1040"]
FORM_STATUS = "draft"


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS — Form 8582 §469(i) special allowance (NON-indexed)
# ═══════════════════════════════════════════════════════════════════════════

SPECIAL_ALLOWANCE_MAX = 25000          # single / MFJ (line 8 cap)
SPECIAL_ALLOWANCE_MFS = 12500          # MFS lived apart all year
PHASEOUT_TOP = 150000                  # line 5 (single / MFJ)
PHASEOUT_TOP_MFS = 75000               # line 5 (MFS lived apart)
PHASEOUT_RATE = 0.50                   # line 8 = 50% × (line 5 − MAGI)
# (Equivalent forms: 50%×($150k−MAGI) capped $25k == $25k − 50%×(MAGI−$100k);
#  zero allowance once MAGI ≥ $150,000 / $75,000 MFS.)

# Schedule E line 1b property-type codes (verbatim from f1040se.pdf).
SCHE_PROPERTY_TYPES = {
    1: "Single Family Residence", 2: "Multi-Family Residence",
    3: "Vacation/Short-Term Rental", 4: "Commercial", 5: "Land",
    6: "Royalties", 7: "Self-Rental", 8: "Other",
}

# The 8582 MAGI add-backs (verified i8582). Documented for the source pins; the
# tts-tax-app compute leg adds back what the engine has and flags the rest.
MAGI_ADDBACKS = [
    "the passive activity loss itself (§469(d)(1))",
    "the rental real estate loss allowed to real estate professionals",
    "taxable social security & tier-1 RRB benefits",
    "the IRA + §501(c)(18) deduction",
    "½ of the self-employment-tax deduction",
    "the §135 Series EE/I savings-bond interest exclusion",
    "the §137 employer adoption-assistance exclusion",
    "the §221 student-loan-interest deduction",
    "the §250 FDII / GILTI deduction",
]


def special_allowance(net_rental_loss, magi, mfs_apart: bool) -> int:
    """Form 8582 lines 4-9 — the active-participation special allowance.
    `net_rental_loss` is the (positive) smaller of the line-1d / line-3 loss.
    Shared traceability; the integrity gate re-types it independently."""
    import math

    top = PHASEOUT_TOP_MFS if mfs_apart else PHASEOUT_TOP
    cap = SPECIAL_ALLOWANCE_MFS if mfs_apart else SPECIAL_ALLOWANCE_MAX
    if net_rental_loss <= 0:
        return 0
    if magi >= top:                       # line 6 ≥ line 5 → line 8 = 0
        line8 = 0
    else:
        line8 = math.floor(PHASEOUT_RATE * (top - magi))   # line 7 × 50%
        line8 = min(line8, cap)           # "do not enter more than $25,000"
    return min(int(net_rental_loss), line8)   # line 9 = smaller of line 4 / 8


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("rental_real_estate", "Rental real estate & royalties (Schedule E Part I) → Schedule 1 line 5"),
    ("passive_activity_loss", "Passive activity loss limitations (Form 8582, §469) — the $25,000 active-participation special allowance"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_1040_FORM",
    "IRS_2025_1040_INSTR",
]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_SCHE_INSTR",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Schedule E (Form 1040) — Supplemental Income and Loss",
        "citation": "Instructions for Schedule E (Form 1040) (2025); i1040se; Schedule E Attachment Sequence No. 13",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i1040se.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": "Schedule E Part I — rental real estate & royalties. Property types 1-8; line 22 deductible loss after Form 8582; line 26 → Schedule 1 line 5. REQUIRES HUMAN REVIEW: confirm the expense-line labels vs the 2025 form (pinned from f1040se.pdf at the field-map dump).",
        "topics": ["rental_real_estate"],
        "excerpts": [
            {
                "excerpt_label": "Schedule E Part I line structure (2025)",
                "location_reference": "i1040se (2025), Part I",
                "excerpt_text": (
                    "Part I — Income or Loss From Rental Real Estate and Royalties. 1b Type of property "
                    "(1 Single Family Residence, 2 Multi-Family Residence, 3 Vacation/Short-Term Rental, "
                    "4 Commercial, 5 Land, 6 Royalties, 7 Self-Rental, 8 Other). 3 Rents received; 4 Royalties "
                    "received; 5-19 expenses; 20 Total expenses; 21 income or (loss) (subtract line 20 from "
                    "line 3 and/or 4); 22 Deductible rental real estate loss after limitation, if any, on Form "
                    "8582; 23a-23e totals; 24 Income; 25 Losses; 26 Total rental real estate and royalty income "
                    "or (loss) — enter on Schedule 1 (Form 1040), line 5."
                ),
                "summary_text": "Part I rentals/royalties; line 22 = deductible loss after Form 8582; line 26 → Schedule 1 line 5.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_F8582_INSTR",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Form 8582 — Passive Activity Loss Limitations",
        "citation": "Instructions for Form 8582 (2025); i8582; Form 8582 Attachment Sequence No. 858",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i8582.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": "The $25,000 special allowance + the 50%×($150k−MAGI) phaseout + the MFS amounts + the modified-AGI add-back list. REQUIRES HUMAN REVIEW: confirm the MAGI add-back list + the MFS-apart/together split vs the 2025 i8582.",
        "topics": ["passive_activity_loss"],
        "excerpts": [
            {
                "excerpt_label": "Special allowance + phaseout (2025, lines 5-9)",
                "location_reference": "i8582 (2025), Part II + 'Special Allowance'",
                "excerpt_text": (
                    "The maximum special allowance is $25,000 ($12,500 if married filing separately and you "
                    "lived apart from your spouse all year). Line 5: enter $150,000 ($75,000 if MFS). Line 6: "
                    "modified adjusted gross income, not less than zero. Line 7: subtract line 6 from line 5. "
                    "Line 8: multiply line 7 by 50% — do not enter more than $25,000 ($12,500 if MFS). Line 9: "
                    "the smaller of line 4 or line 8. If MFS and you lived with your spouse at any time during "
                    "the year, you cannot use the special allowance."
                ),
                "summary_text": "$25,000 / $12,500 MFS-apart; allowance = min(line 4 loss, 50%×($150k/$75k − MAGI) capped $25k/$12,500); MFS-together = $0.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Modified adjusted gross income (2025)",
                "location_reference": "i8582 (2025), 'Modified adjusted gross income'",
                "excerpt_text": (
                    "Modified adjusted gross income is your adjusted gross income figured without: any passive "
                    "activity loss; any rental real estate loss allowed to real estate professionals; taxable "
                    "social security and tier 1 railroad retirement benefits; the deduction for IRA and "
                    "section 501(c)(18) contributions; the deductible part of self-employment tax; the "
                    "exclusion of Series EE and I bond interest used for education; the exclusion of employer "
                    "adoption assistance; the student loan interest deduction; and the deduction for FDII and "
                    "GILTI. Include in MAGI any portfolio income and the overall gain from a PTP."
                ),
                "summary_text": "MAGI = AGI WITHOUT passive loss / RE-pro loss / taxable SS / IRA+501(c)(18) / ½ SE tax / §135 / §137 / §221 / §250. (NOT §199A.)",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_469",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §469 — Passive Activity Losses and Credits Limited",
        "citation": "26 U.S.C. §469 (passive activity loss; §469(i) the $25,000 offset; §469(c)(7) real estate professional; §469(g) disposition)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/469",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "The substantive passive-activity authority: §469(i) the $25,000 active-participation offset + the $100k-$150k phaseout; §469(c)(2) rental = passive per se; §469(c)(7) real-estate-professional exception; §469(g) fully-taxable disposition releases suspended losses.",
        "topics": ["passive_activity_loss"],
        "excerpts": [
            {
                "excerpt_label": "§469(i) the $25,000 offset + phaseout",
                "location_reference": "26 U.S.C. §469(i)(2)-(3),(5)",
                "excerpt_text": (
                    "§469(i)(2): the $25,000 amount. §469(i)(3)(A): the $25,000 amount is reduced by 50% of the "
                    "amount by which the adjusted gross income exceeds $100,000. §469(i)(5): in the case of a "
                    "married individual filing separately who lived apart, $12,500 and $50,000 (substituted for "
                    "$25,000 and $100,000); a married individual filing separately who did not live apart gets "
                    "zero. §469(g): a fully taxable disposition of an entire interest releases the suspended loss."
                ),
                "summary_text": "§469(i): $25,000 offset reduced 50% of AGI over $100,000; MFS-apart $12,500/$50,000; MFS-together $0; §469(g) disposition releases the suspended loss.",
                "is_key_excerpt": True,
            },
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_SCHE_INSTR", "SCHEDULE_E", "governs"),
    ("IRS_2025_F8582_INSTR", "FORM_8582", "governs"),
    ("IRC_469", "FORM_8582", "governs"),
    ("IRC_469", "SCHEDULE_E", "informs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM: SCHEDULE_E (Part I — rental real estate & royalties)
# ═══════════════════════════════════════════════════════════════════════════

SCHE_IDENTITY = {
    "form_number": "SCHEDULE_E",
    "form_title": "Schedule E (Form 1040) — Supplemental Income and Loss (Part I, TY2025)",
    "notes": (
        "Ken's scope 2026-06-13 (post-sprint NEXT-UP #6). Part I ONLY (rental real "
        "estate & royalties) — Parts II-V (K-1 passthrough partnerships/S-corps, "
        "estates/trusts, REMICs, the summary) are out of scope. The per-property "
        "rows REUSE + EXTEND the RentalProperty model (routed by the parent return "
        "form code). Net income/(loss) line 26 → Schedule 1 line 5 → 1040 line 8. "
        "Rental real estate losses with active participation are limited by Form "
        "8582 (line 22); royalties + net rental income flow directly."
    ),
}

SCHE_FACTS: list[dict] = [
    # ── Return-level inputs (Part I header) ──
    {"fact_key": "sche_made_1099_payments", "label": "A — Made payments requiring Form(s) 1099?",
     "data_type": "boolean", "default_value": "false", "sort_order": 1,
     "notes": "Schedule E line A. Drives D_SCHE_003 (the 1099-filing due-diligence question)."},
    {"fact_key": "sche_will_file_1099", "label": "B — Did/will you file the required Form(s) 1099?",
     "data_type": "boolean", "default_value": "false", "sort_order": 2,
     "notes": "Schedule E line B."},
    # ── Outputs (the per-property income/expense ride RentalProperty) ──
    {"fact_key": "sche_total_rents", "label": "Line 3 — total rents received (all properties)",
     "data_type": "decimal", "sort_order": 10, "notes": "OUTPUT. Σ RentalProperty.rents_received (1040-scoped)."},
    {"fact_key": "sche_total_royalties", "label": "Line 4 — total royalties received",
     "data_type": "decimal", "sort_order": 11, "notes": "OUTPUT. Σ royalties (property_type 6)."},
    {"fact_key": "sche_total_expenses", "label": "Line 20 — total expenses (all properties)",
     "data_type": "decimal", "sort_order": 12, "notes": "OUTPUT. Σ lines 5-19 incl. depreciation (from the depreciation engine)."},
    {"fact_key": "sche_income_before_limit", "label": "Line 21 — income/(loss) before the passive limit",
     "data_type": "decimal", "sort_order": 13, "notes": "OUTPUT. (rents + royalties) − total expenses, per property then aggregated."},
    {"fact_key": "sche_deductible_loss", "label": "Line 22 — deductible rental RE loss after Form 8582",
     "data_type": "decimal", "sort_order": 14, "notes": "OUTPUT. The 8582-allowed portion of the active-participation rental loss."},
    {"fact_key": "sche_net", "label": "Line 26 — total rental/royalty income or (loss) → Schedule 1 line 5",
     "data_type": "decimal", "sort_order": 15, "notes": "OUTPUT. Σ positive line-21 income + royalties + allowed line-22 losses → Schedule 1 line 5."},
]

SCHE_RULES: list[dict] = [
    {"rule_id": "R-SCHE-NET", "title": "Per-property net + the Part I aggregate (lines 20/21/26)", "rule_type": "calculation",
     "precedence": 1, "sort_order": 1,
     "formula": ("Per RentalProperty (1040-scoped): line 20 = Σ expenses (5-19, incl. depreciation from the "
                 "engine); line 21 = rents (3) + royalties (4) − line 20. Aggregate line 26 = Σ positive "
                 "line-21 income + Σ line-22 allowed losses → Schedule 1 line 5."),
     "inputs": ["sche_total_rents", "sche_total_royalties", "sche_total_expenses"],
     "outputs": ["sche_income_before_limit", "sche_net"],
     "description": "Decision 1. Reuse + extend RentalProperty; depreciation rides the existing rental_property_id linkage retargeted for the 1040."},
    {"rule_id": "R-SCHE-PASSIVE-ROUTE", "title": "Rental real estate losses are passive → Form 8582", "rule_type": "routing",
     "precedence": 2, "sort_order": 2,
     "formula": ("A property's line-21 LOSS that is rental real estate is passive per se (§469(c)(2)) and "
                 "routes to Form 8582 line 1 (active participation) or line 2 (no active participation). "
                 "Royalties + net rental income are NOT limited and flow directly to line 26. Real estate "
                 "professional → non-passive (RED-deferred, D_8582_RE_PRO)."),
     "inputs": [], "outputs": [],
     "description": "Decision 2/3. The passive-loss hook on line 22; the simplified active-participation bucket."},
    {"rule_id": "R-SCHE-8582-LIMIT", "title": "Line 22 — deductible loss after the 8582 limitation", "rule_type": "calculation",
     "precedence": 3, "sort_order": 3,
     "formula": ("sche_deductible_loss (line 22) = the Form 8582-allowed portion of the active-participation "
                 "rental loss (8582 line 11 total allowed, attributable to rental RE). The disallowed remainder "
                 "is suspended (8582 carryforward)."),
     "inputs": [], "outputs": ["sche_deductible_loss"],
     "description": "Decision 2. The $25k special allowance lives on 8582 — Schedule E reads back the allowed loss."},
    {"rule_id": "R-SCHE-TO-SCH1", "title": "Line 26 → Schedule 1 line 5", "rule_type": "routing",
     "precedence": 4, "sort_order": 4,
     "formula": "sche_net (line 26) → Schedule 1 (Form 1040) line 5 → 1040 line 8.",
     "inputs": ["sche_net"], "outputs": [],
     "description": "Schedule 1 line 5 is already a direct-entry feeder in tts-tax-app; Schedule E supplies the computed value (YELLOW)."},
]

SCHE_LINES: list[dict] = [
    {"line_number": "A", "description": "A Made payments in 2025 requiring Form(s) 1099?", "line_type": "input"},
    {"line_number": "B", "description": "B If 'Yes,' did you or will you file the required Form(s) 1099?", "line_type": "input"},
    {"line_number": "1a", "description": "1a Physical address of each property (A/B/C)", "line_type": "input"},
    {"line_number": "1b", "description": "1b Type of property (1-8: SFR/Multi/Vacation/Commercial/Land/Royalties/Self-Rental/Other)", "line_type": "input"},
    {"line_number": "2", "description": "2 Fair rental days / personal use days / QJV (per property)", "line_type": "input"},
    {"line_number": "3", "description": "3 Rents received", "line_type": "input"},
    {"line_number": "4", "description": "4 Royalties received", "line_type": "input"},
    {"line_number": "5", "description": "5 Advertising", "line_type": "input"},
    {"line_number": "6", "description": "6 Auto and travel", "line_type": "input"},
    {"line_number": "7", "description": "7 Cleaning and maintenance", "line_type": "input"},
    {"line_number": "8", "description": "8 Commissions", "line_type": "input"},
    {"line_number": "9", "description": "9 Insurance", "line_type": "input"},
    {"line_number": "10", "description": "10 Legal and other professional fees", "line_type": "input"},
    {"line_number": "11", "description": "11 Management fees", "line_type": "input"},
    {"line_number": "12", "description": "12 Mortgage interest paid to banks, etc.", "line_type": "input"},
    {"line_number": "13", "description": "13 Other interest", "line_type": "input"},
    {"line_number": "14", "description": "14 Repairs", "line_type": "input"},
    {"line_number": "15", "description": "15 Supplies", "line_type": "input"},
    {"line_number": "16", "description": "16 Taxes", "line_type": "input"},
    {"line_number": "17", "description": "17 Utilities", "line_type": "input"},
    {"line_number": "18", "description": "18 Depreciation expense or depletion", "line_type": "input"},
    {"line_number": "19", "description": "19 Other (list)", "line_type": "input"},
    {"line_number": "20", "description": "20 Total expenses (add lines 5 through 19)", "line_type": "calculated"},
    {"line_number": "21", "description": "21 Income or (loss) (subtract line 20 from line 3 and/or 4)", "line_type": "calculated"},
    {"line_number": "22", "description": "22 Deductible rental real estate loss after limitation from Form 8582", "line_type": "calculated"},
    {"line_number": "23a", "description": "23a Total of all amounts reported on line 3 (rents)", "line_type": "calculated"},
    {"line_number": "23b", "description": "23b Total of all amounts reported on line 4 (royalties)", "line_type": "calculated"},
    {"line_number": "23c", "description": "23c Total of all amounts reported on line 12 (mortgage interest)", "line_type": "calculated"},
    {"line_number": "23d", "description": "23d Total of all amounts reported on line 18 (depreciation)", "line_type": "calculated"},
    {"line_number": "23e", "description": "23e Total of all amounts reported on line 20 (total expenses)", "line_type": "calculated"},
    {"line_number": "24", "description": "24 Income (add positive amounts on line 21 and royalties)", "line_type": "calculated"},
    {"line_number": "25", "description": "25 Losses (add royalty losses from line 21 and rental losses from line 22)", "line_type": "calculated"},
    {"line_number": "26", "description": "26 Total rental real estate and royalty income or (loss) → Schedule 1 line 5", "line_type": "total"},
]

SCHE_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_SCHE_001", "title": "Rental real estate loss — passive limitation computed", "severity": "info",
     "condition": "any property line 21 < 0 (rental real estate)",
     "message": ("A rental real estate loss is present. Rental activities are passive per se; the deductible "
                 "loss is limited by Form 8582 (the $25,000 active-participation special allowance, phased out "
                 "over modified AGI $100,000-$150,000). The disallowed remainder is suspended and carried forward."),
     "notes": "§469(c)(2). The 8582 hook on line 22."},
    {"diagnostic_id": "D_SCHE_002", "title": "Personal use may trigger the vacation-home limit (§280A)", "severity": "warning",
     "condition": "personal_use_days > max(14, 10% of fair_rental_days)",
     "message": ("Personal use of a dwelling unit exceeds the greater of 14 days or 10% of the days rented at "
                 "fair value — the §280A vacation-home rules may limit deductible expenses to rental income. "
                 "v1 does NOT apply the §280A allocation; verify the expense limitation manually."),
     "notes": "§280A vacation-home limit — a v1 deviation (RED-defer the allocation)."},
    {"diagnostic_id": "D_SCHE_003", "title": "Form 1099 filing question unanswered", "severity": "warning",
     "condition": "sche_made_1099_payments is True AND sche_will_file_1099 is False",
     "message": ("You indicated payments requiring Form(s) 1099 but did not confirm filing them. Answer the "
                 "Schedule E line A/B due-diligence questions."),
     "notes": "Schedule E lines A/B."},
    {"diagnostic_id": "D_SCHE_004", "title": "Rental income — Schedule E net flows to Schedule 1 line 5", "severity": "info",
     "condition": "sche_net != 0",
     "message": ("The Schedule E Part I total (line 26) flows to Schedule 1 line 5 and into 1040 line 8."),
     "notes": "The flow confirmation."},
]

SCHE_SCENARIOS: list[dict] = [
    {"scenario_name": "SCHE-T1 — profitable rental → Schedule 1 line 5", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "filing_status": "single", "rents": 24000, "royalties": 0, "expenses": 15000,
                "active_participation": True, "magi": 60000},
     "expected_outputs": {"sche_income_before_limit": 9000, "sche_net": 9000},
     "notes": "24,000 − 15,000 = 9,000 income; no loss → no 8582; line 26 = 9,000 → Schedule 1 line 5."},
    {"scenario_name": "SCHE-T2 — active rental loss fully allowed ($25k allowance)", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "rents": 18000, "royalties": 0, "expenses": 38000,
                "active_participation": True, "magi": 80000},
     "expected_outputs": {"sche_income_before_limit": -20000, "sche_deductible_loss": -20000, "sche_net": -20000},
     "notes": "loss 20,000; MAGI 80,000 < 100,000 → full $25k allowance covers it → line 22 = (20,000); line 26 = (20,000)."},
    {"scenario_name": "SCHE-T3 — active rental loss partly suspended (phaseout)", "scenario_type": "edge_case", "sort_order": 3,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "rents": 10000, "royalties": 0, "expenses": 50000,
                "active_participation": True, "magi": 120000},
     "expected_outputs": {"sche_income_before_limit": -40000, "sche_deductible_loss": -15000, "sche_net": -15000},
     "notes": "loss 40,000; allowance = 50%×(150,000−120,000) = 15,000 → line 22 = (15,000); 25,000 suspended; line 26 = (15,000)."},
    {"scenario_name": "SCHE-T4 — royalty income only", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"tax_year": 2025, "filing_status": "single", "rents": 0, "royalties": 5000, "expenses": 800,
                "active_participation": False, "magi": 70000},
     "expected_outputs": {"sche_income_before_limit": 4200, "sche_net": 4200},
     "notes": "royalties 5,000 − 800 = 4,200 (not passive-limited) → line 26 = 4,200 → Schedule 1 line 5."},
]

SCHE_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-SCHE-NET", "IRS_2025_SCHE_INSTR", "primary", "Part I lines 3-21 (rents/royalties − expenses)"),
    ("R-SCHE-PASSIVE-ROUTE", "IRC_469", "primary", "§469(c)(2) rental = passive per se"),
    ("R-SCHE-PASSIVE-ROUTE", "IRS_2025_SCHE_INSTR", "secondary", "Line 22 hook to Form 8582"),
    ("R-SCHE-8582-LIMIT", "IRS_2025_F8582_INSTR", "primary", "Line 22 = the 8582-allowed loss"),
    ("R-SCHE-TO-SCH1", "IRS_2025_SCHE_INSTR", "primary", "Line 26 → Schedule 1 line 5"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM: FORM_8582 (Passive Activity Loss Limitations — simplified v1 bucket)
# ═══════════════════════════════════════════════════════════════════════════

F8582_IDENTITY = {
    "form_number": "FORM_8582",
    "form_title": "Form 8582 — Passive Activity Loss Limitations (TY2025)",
    "notes": (
        "Re-authored to standard 2026-06-13 (the prior deployed draft used a wrong "
        "line numbering — invented a CRD line 2; the real 2025 form is 1a-1d rental "
        "RE active / 2a-2d all other passive / 3 combine / Part II 4-9 special "
        "allowance / 10-11 total allowed). v1 = Ken's SIMPLIFIED active-participation "
        "bucket: the aggregate columns are computed from the RentalProperty rows + "
        "the prior-year-suspended fact (the per-activity Parts IV/V Worksheets are a "
        "follow-up). The $25,000 special allowance ($12,500 MFS-apart) phases out 50% "
        "of MAGI over $100,000 (zero at $150,000). Allowed loss → Schedule E line 22; "
        "the remainder suspended (carryforward). Real estate professional = RED-deferred."
    ),
}

F8582_FACTS: list[dict] = [
    # ── Part I (aggregate columns; v1 from the RentalProperty rows) ──
    {"fact_key": "f8582_rental_income", "label": "Line 1a — rental RE (active) net income",
     "data_type": "decimal", "default_value": "0", "sort_order": 1, "notes": "Σ active-participation rental properties with net income."},
    {"fact_key": "f8582_rental_loss", "label": "Line 1b — rental RE (active) net loss",
     "data_type": "decimal", "default_value": "0", "sort_order": 2, "notes": "Σ active-participation rental properties with net loss (positive)."},
    {"fact_key": "f8582_rental_prior_unallowed", "label": "Line 1c — prior-year unallowed rental losses",
     "data_type": "decimal", "default_value": "0", "sort_order": 3, "notes": "The aggregate prior-year suspended rental loss (preparer carryover fact)."},
    {"fact_key": "f8582_rental_combined", "label": "Line 1d — combine 1a/1b/1c",
     "data_type": "decimal", "sort_order": 4, "notes": "OUTPUT."},
    {"fact_key": "f8582_other_income", "label": "Line 2a — all other passive net income",
     "data_type": "decimal", "default_value": "0", "sort_order": 5, "notes": "Other passive (single bucket, v1)."},
    {"fact_key": "f8582_other_loss", "label": "Line 2b — all other passive net loss",
     "data_type": "decimal", "default_value": "0", "sort_order": 6, "notes": "Other passive loss (positive)."},
    {"fact_key": "f8582_other_prior_unallowed", "label": "Line 2c — prior-year unallowed other passive",
     "data_type": "decimal", "default_value": "0", "sort_order": 7, "notes": "Prior-year suspended other-passive loss."},
    {"fact_key": "f8582_combined", "label": "Line 3 — combine 1d and 2d",
     "data_type": "decimal", "sort_order": 8, "notes": "OUTPUT. >= 0 → all losses allowed (stop)."},
    {"fact_key": "f8582_smaller_loss", "label": "Line 4 — smaller of the loss on 1d or line 3",
     "data_type": "decimal", "sort_order": 9, "notes": "OUTPUT (positive). The active-rental loss eligible for the special allowance."},
    {"fact_key": "f8582_magi", "label": "Line 6 — modified adjusted gross income",
     "data_type": "decimal", "default_value": "0", "sort_order": 10, "notes": "OUTPUT. AGI + the §469 add-backs (compute what we have; flag the rest — D_8582_005)."},
    {"fact_key": "f8582_special_allowance", "label": "Line 9 — special allowance",
     "data_type": "decimal", "sort_order": 11, "notes": "OUTPUT. min(line 4, 50%×($150k/$75k − MAGI) capped $25k/$12,500)."},
    {"fact_key": "f8582_total_allowed", "label": "Line 11 — total losses allowed",
     "data_type": "decimal", "sort_order": 12, "notes": "OUTPUT. line 9 + line 10 → Schedule E line 22 (rental RE share)."},
    {"fact_key": "f8582_suspended", "label": "Suspended passive loss (carried forward)",
     "data_type": "decimal", "sort_order": 13, "notes": "OUTPUT. net passive loss − total allowed → next-year carryover."},
    # ── Inputs (return-level facts) ──
    {"fact_key": "f8582_active_participation", "label": "Active participation in rental real estate?",
     "data_type": "boolean", "default_value": "true", "sort_order": 20, "notes": "Drives line 1 vs line 2; the special-allowance gate. §469(i)(6)."},
    {"fact_key": "f8582_real_estate_professional", "label": "Real estate professional (§469(c)(7))?",
     "data_type": "boolean", "default_value": "false", "sort_order": 21, "notes": "RED-deferred (D_8582_RE_PRO) — non-passive treatment not supported in v1."},
    {"fact_key": "f8582_complete_disposition", "label": "Fully taxable disposition of an activity this year?",
     "data_type": "boolean", "default_value": "false", "sort_order": 22, "notes": "§469(g) — releases the prior-year suspended loss in full."},
    {"fact_key": "f8582_mfs_lived_apart", "label": "MFS — lived apart from spouse ALL year?",
     "data_type": "boolean", "default_value": "false", "sort_order": 23, "notes": "MFS-apart → $12,500 / $75k phaseout. (MFS not-apart → $0.)"},
]

F8582_RULES: list[dict] = [
    {"rule_id": "R-8582-PASSIVE", "title": "Rental activities passive per se; net the columns", "rule_type": "calculation",
     "precedence": 1, "sort_order": 1,
     "formula": ("Rental activities are passive per se (§469(c)(2)). Line 1d = 1a − 1b − 1c (active rental RE); "
                 "line 2d = 2a − 2b − 2c (all other passive); line 3 = 1d + 2d. If line 3 >= 0, all losses are "
                 "allowed (stop). If line 3 is a loss and line 1d is a loss → Part II."),
     "inputs": ["f8582_rental_income", "f8582_rental_loss", "f8582_rental_prior_unallowed", "f8582_other_income", "f8582_other_loss", "f8582_other_prior_unallowed"],
     "outputs": ["f8582_rental_combined", "f8582_combined"],
     "description": "Decision 2. The simplified aggregate bucket (per-activity Parts IV/V = follow-up)."},
    {"rule_id": "R-8582-MAGI", "title": "Line 6 — modified adjusted gross income", "rule_type": "calculation",
     "precedence": 2, "sort_order": 2,
     "formula": ("f8582_magi = AGI figured WITHOUT: the passive loss, the RE-professional rental loss, taxable "
                 "SS/RRB, the IRA + §501(c)(18) deduction, ½ SE-tax, the §135/§137/§221/§250 items. (NOT §199A.) "
                 "v1 adds back what the engine has and flags the rest (D_8582_005)."),
     "inputs": [], "outputs": ["f8582_magi"],
     "description": "Decision 4. The proper modified AGI; partial add-backs flagged."},
    {"rule_id": "R-8582-SPECIAL-ALLOWANCE", "title": "Lines 4-9 — the $25,000 active-participation special allowance", "rule_type": "calculation",
     "precedence": 3, "sort_order": 3,
     "formula": ("line 4 = smaller of |line 1d loss| or |line 3 loss| (active rental). line 5 = $150,000 "
                 "($75,000 MFS-apart). line 7 = max(0, line 5 − MAGI). line 8 = floor(50% × line 7), capped "
                 "$25,000 ($12,500 MFS-apart). line 9 = min(line 4, line 8). MFS lived WITH spouse → $0 (skip "
                 "Part II)."),
     "inputs": ["f8582_smaller_loss", "f8582_magi", "f8582_active_participation", "f8582_mfs_lived_apart"],
     "outputs": ["f8582_special_allowance"],
     "description": "Decision 2. §469(i) — the core of pairing 8582 with Schedule E."},
    {"rule_id": "R-8582-ALLOWED", "title": "Lines 10-11 — total losses allowed + the suspended carryforward", "rule_type": "calculation",
     "precedence": 4, "sort_order": 4,
     "formula": ("line 10 = the income on lines 1a + 2a. line 11 (total allowed) = line 9 + line 10. The "
                 "suspended loss (carryforward) = the net passive loss − line 11. The rental RE share of line "
                 "11 → Schedule E line 22."),
     "inputs": [], "outputs": ["f8582_total_allowed", "f8582_suspended"],
     "description": "The allowed/suspended split (aggregate; per-activity allocation = follow-up)."},
    {"rule_id": "R-8582-DISPOSITION", "title": "Complete disposition releases the suspended loss", "rule_type": "routing",
     "precedence": 5, "sort_order": 5,
     "formula": ("If f8582_complete_disposition (a fully taxable disposition of the entire interest, §469(g)): "
                 "the activity's prior-year suspended loss is released in full (no 8582 limitation on it)."),
     "inputs": ["f8582_complete_disposition"], "outputs": [],
     "description": "§469(g). The spec's release rule — simple, kept in v1."},
    {"rule_id": "R-8582-RE-PRO", "title": "Real estate professional → non-passive (RED-deferred)", "rule_type": "routing",
     "precedence": 6, "sort_order": 6,
     "formula": ("If f8582_real_estate_professional: the 750-hour + >half-personal-services test (§469(c)(7)) "
                 "reclassifies materially-participated rentals as NON-passive (bypassing 8582). v1 does NOT "
                 "support this → D_8582_RE_PRO (RED, prepare manually)."),
     "inputs": ["f8582_real_estate_professional"], "outputs": [],
     "description": "Decision 3. RED-defer."},
]

F8582_LINES: list[dict] = [
    {"line_number": "1a", "description": "1a Rental RE (active) — activities with net income", "line_type": "input"},
    {"line_number": "1b", "description": "1b Rental RE (active) — activities with net loss", "line_type": "input"},
    {"line_number": "1c", "description": "1c Rental RE (active) — prior years' unallowed losses", "line_type": "input"},
    {"line_number": "1d", "description": "1d Combine lines 1a, 1b, and 1c", "line_type": "calculated"},
    {"line_number": "2a", "description": "2a All other passive activities — net income", "line_type": "input"},
    {"line_number": "2b", "description": "2b All other passive activities — net loss", "line_type": "input"},
    {"line_number": "2c", "description": "2c All other passive activities — prior years' unallowed losses", "line_type": "input"},
    {"line_number": "2d", "description": "2d Combine lines 2a, 2b, and 2c", "line_type": "calculated"},
    {"line_number": "3", "description": "3 Combine lines 1d and 2d", "line_type": "subtotal"},
    {"line_number": "4", "description": "4 Smaller of the loss on line 1d or the loss on line 3", "line_type": "calculated"},
    {"line_number": "5", "description": "5 $150,000 ($75,000 if MFS lived apart)", "line_type": "calculated"},
    {"line_number": "6", "description": "6 Modified adjusted gross income (not less than zero)", "line_type": "calculated"},
    {"line_number": "7", "description": "7 Subtract line 6 from line 5", "line_type": "calculated"},
    {"line_number": "8", "description": "8 Multiply line 7 by 50% (max $25,000 / $12,500 MFS)", "line_type": "calculated"},
    {"line_number": "9", "description": "9 Smaller of line 4 or line 8 — the special allowance", "line_type": "calculated"},
    {"line_number": "10", "description": "10 Add the income on lines 1a and 2a", "line_type": "calculated"},
    {"line_number": "11", "description": "11 Total losses allowed (add lines 9 and 10)", "line_type": "total"},
]

F8582_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_8582_RE_PRO", "title": "Real estate professional — non-passive not supported", "severity": "error",
     "condition": "f8582_real_estate_professional is True",
     "message": ("Not supported — prepare manually: real estate professional status (§469(c)(7)) reclassifies "
                 "materially-participated rentals as non-passive, bypassing the Form 8582 limitation. This "
                 "software does not compute the 750-hour / material-participation determination. Figure the "
                 "passive/non-passive split manually."),
     "notes": "Decision 3. RED-defer."},
    {"diagnostic_id": "D_8582_MFS_TOGETHER", "title": "MFS lived with spouse — no special allowance", "severity": "warning",
     "condition": "filing_status == 'mfs' AND not f8582_mfs_lived_apart",
     "message": ("Married filing separately and you did not live apart from your spouse all year: the $25,000 "
                 "special allowance is $0 (the rental loss is fully suspended unless offset by passive income). "
                 "Confirm the lived-apart status."),
     "notes": "§469(i)(5)(B)."},
    {"diagnostic_id": "D_8582_SUSPENDED", "title": "Passive losses suspended (carried forward)", "severity": "info",
     "condition": "f8582_suspended > 0",
     "message": ("Part of the passive activity loss exceeds the passive income plus the special allowance and is "
                 "suspended — it carries forward to next year (and is released on a fully taxable disposition). "
                 "Record the suspended amount as next year's prior-year-unallowed carryover."),
     "notes": "§469(b) carryforward."},
    {"diagnostic_id": "D_8582_PHASEOUT", "title": "Special allowance phased out by MAGI", "severity": "info",
     "condition": "100000 < MAGI < 150000 (or 50000 < MAGI < 75000 MFS-apart)",
     "message": ("Modified AGI is in the $100,000-$150,000 phaseout range ($50,000-$75,000 if MFS lived apart), "
                 "so the $25,000 special allowance is reduced by 50% of the excess over $100,000."),
     "notes": "§469(i)(3)."},
    {"diagnostic_id": "D_8582_005", "title": "Modified AGI add-backs partially computed", "severity": "info",
     "condition": "the special allowance is in the phaseout range AND an un-computed add-back may apply",
     "message": ("Form 8582 MAGI adds back several items the engine does not yet compute (the §135 savings-bond, "
                 "§137 adoption, §250 FDII/GILTI exclusions, and the real-estate-professional rental loss). Near "
                 "the $100,000-$150,000 phaseout boundary, verify the modified AGI manually."),
     "notes": "Decision 4. The partial-MAGI flag."},
    {"diagnostic_id": "D_8582_DISPOSITION", "title": "Complete disposition released suspended losses", "severity": "info",
     "condition": "f8582_complete_disposition is True",
     "message": ("A fully taxable disposition of an entire passive activity releases that activity's prior-year "
                 "suspended losses in full (§469(g)) — they are deductible without the 8582 limitation."),
     "notes": "§469(g)."},
]

F8582_SCENARIOS: list[dict] = [
    {"scenario_name": "8582-T1 — active rental loss fully allowed (MAGI < $100k)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "rental_loss": 20000, "magi": 80000,
                "active_participation": True},
     "expected_outputs": {"f8582_smaller_loss": 20000, "f8582_special_allowance": 20000,
                          "f8582_total_allowed": 20000, "f8582_suspended": 0},
     "notes": "line 4 = 20,000; MAGI 80,000 → allowance cap = min(50%×(150k−80k)=35k, 25k)=25,000; line 9 = min(20,000, 25,000)=20,000; suspended 0."},
    {"scenario_name": "8582-T2 — phaseout partially suspends (MAGI $120k)", "scenario_type": "edge_case", "sort_order": 2,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "rental_loss": 40000, "magi": 120000,
                "active_participation": True},
     "expected_outputs": {"f8582_smaller_loss": 40000, "f8582_special_allowance": 15000,
                          "f8582_total_allowed": 15000, "f8582_suspended": 25000},
     "notes": "allowance = min(50%×(150k−120k)=15,000, 25k)=15,000; line 9 = min(40,000, 15,000)=15,000; suspended 40,000−15,000=25,000."},
    {"scenario_name": "8582-T3 — MAGI over $150k, fully suspended", "scenario_type": "edge_case", "sort_order": 3,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "rental_loss": 30000, "magi": 160000,
                "active_participation": True},
     "expected_outputs": {"f8582_special_allowance": 0, "f8582_total_allowed": 0, "f8582_suspended": 30000},
     "notes": "MAGI 160,000 ≥ 150,000 → line 8 = 0 → line 9 = 0; the whole 30,000 loss suspended."},
    {"scenario_name": "8582-T4 — MFS lived apart ($12,500 cap)", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"tax_year": 2025, "filing_status": "mfs", "rental_loss": 10000, "magi": 40000,
                "active_participation": True, "mfs_lived_apart": True},
     "expected_outputs": {"f8582_special_allowance": 10000, "f8582_total_allowed": 10000, "f8582_suspended": 0},
     "notes": "MFS-apart: line 5 = 75,000; allowance = min(50%×(75k−40k)=17,500, 12,500)=12,500; line 9 = min(10,000, 12,500)=10,000; suspended 0."},
    {"scenario_name": "8582-T5 — passive income offsets part of the loss", "scenario_type": "normal", "sort_order": 5,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "rental_loss": 8000, "other_income": 5000, "magi": 130000,
                "active_participation": True},
     "expected_outputs": {"f8582_smaller_loss": 3000, "f8582_special_allowance": 3000,
                          "f8582_total_allowed": 8000, "f8582_suspended": 0},
     "notes": "1d=(8,000); 2d=5,000; line 3 = (3,000); line 4 = smaller of 8,000 or 3,000 = 3,000; allowance = min(3,000, 50%×(150k−130k)=10,000)=3,000; line 10 income = 5,000; line 11 = 3,000+5,000=8,000; suspended 0."},
    {"scenario_name": "8582-G1 — real estate professional → RED", "scenario_type": "diagnostic", "sort_order": 6,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "rental_loss": 50000, "magi": 200000,
                "active_participation": True, "real_estate_professional": True},
     "expected_outputs": {"D_8582_RE_PRO": True},
     "notes": "RE-pro flagged → D_8582_RE_PRO (RED, prepare manually); the 8582 limitation is not applied."},
    {"scenario_name": "8582-G2 — MFS lived together → $0 allowance", "scenario_type": "diagnostic", "sort_order": 7,
     "inputs": {"tax_year": 2025, "filing_status": "mfs", "rental_loss": 12000, "magi": 30000,
                "active_participation": True, "mfs_lived_apart": False},
     "expected_outputs": {"f8582_special_allowance": 0, "f8582_suspended": 12000, "D_8582_MFS_TOGETHER": True},
     "notes": "MFS lived together → no special allowance (skip Part II); the 12,000 loss fully suspended; D_8582_MFS_TOGETHER warns."},
]

F8582_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-8582-PASSIVE", "IRC_469", "primary", "§469(c)(2) rental = passive per se; the netting"),
    ("R-8582-PASSIVE", "IRS_2025_F8582_INSTR", "secondary", "Part I lines 1a-3"),
    ("R-8582-MAGI", "IRS_2025_F8582_INSTR", "primary", "The modified-AGI add-back list (line 6)"),
    ("R-8582-SPECIAL-ALLOWANCE", "IRC_469", "primary", "§469(i) the $25,000 offset + phaseout"),
    ("R-8582-SPECIAL-ALLOWANCE", "IRS_2025_F8582_INSTR", "primary", "Part II lines 4-9"),
    ("R-8582-ALLOWED", "IRS_2025_F8582_INSTR", "primary", "Part III lines 10-11 (total allowed)"),
    ("R-8582-DISPOSITION", "IRC_469", "primary", "§469(g) disposition releases the suspended loss"),
    ("R-8582-RE-PRO", "IRC_469", "primary", "§469(c)(7) real-estate-professional exception"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS (cross-form: Schedule E ↔ Form 8582 ↔ Schedule 1)
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-SCHE-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Schedule E line 26 → Schedule 1 line 5",
     "description": "Validates R-SCHE-TO-SCH1. Bug it catches: the rental/royalty total not reaching Schedule 1 line 5 (→ 1040 line 8).",
     "definition": {"kind": "flow_assertion", "form": "SCHEDULE_E",
                    "checks": [{"source_line": "26", "must_write_to": ["SCH_1.5"]}]},
     "sort_order": 1},
    {"assertion_id": "FA-1040-SCHE-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Per-property net (line 21) = rents + royalties − total expenses",
     "description": "Validates R-SCHE-NET. Bug it catches: an expense not subtracted, or depreciation not flowed into line 20.",
     "definition": {"kind": "formula_check", "form": "SCHEDULE_E",
                    "formula": "line_21 == (rents + royalties) - total_expenses; total_expenses includes depreciation"},
     "sort_order": 2},
    {"assertion_id": "FA-1040-8582-01", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "Special-allowance constants ($25k / $150k / MFS $12,500 / $75k)",
     "description": "Pins the §469(i) statutory amounts. Bug it catches: a drifted allowance cap or phaseout threshold.",
     "definition": {"kind": "constants_check", "form": "FORM_8582",
                    "constants": {"allowance_max": 25000, "allowance_mfs": 12500, "phaseout_top": 150000,
                                  "phaseout_top_mfs": 75000, "phaseout_rate": 0.50, "phaseout_start": 100000}},
     "sort_order": 3},
    {"assertion_id": "FA-1040-8582-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Special allowance = min(line 4 loss, 50%×($150k − MAGI) capped $25k)",
     "description": "Validates R-8582-SPECIAL-ALLOWANCE. Bug it catches: the phaseout not applied (8582-T2 → $15k) or the cap exceeded.",
     "definition": {"kind": "formula_check", "form": "FORM_8582",
                    "formula": "line_9 == min(line_4_loss, min(cap, floor(0.50*(top - magi)))); top/cap = 150000/25000 or 75000/12500 MFS-apart"},
     "sort_order": 4},
    {"assertion_id": "FA-1040-8582-03", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "Allowed + suspended = the net passive loss (conservation)",
     "description": "Validates R-8582-ALLOWED. Bug it catches: a loss vanishing or double-counted — total_allowed + suspended must equal the net passive loss + the offsetting passive income.",
     "definition": {"kind": "reconciliation", "form": "FORM_8582",
                    "formula": "total_allowed + suspended == net_passive_loss + line_10_income"},
     "sort_order": 5},
    {"assertion_id": "FA-1040-8582-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Gates: RE-pro RED; MFS-together $0 allowance",
     "description": "A real-estate-professional flag fires D_8582_RE_PRO (RED); MFS lived-together → $0 special allowance (D_8582_MFS_TOGETHER).",
     "definition": {"kind": "gating_check", "form": "FORM_8582", "expect": {"red_fires": True},
                    "blockers": ["real_estate_professional", "mfs_lived_together"]},
     "sort_order": 6},
]


FORMS: list[dict] = [
    {"identity": SCHE_IDENTITY, "facts": SCHE_FACTS, "rules": SCHE_RULES, "lines": SCHE_LINES,
     "diagnostics": SCHE_DIAGNOSTICS, "scenarios": SCHE_SCENARIOS, "rule_links": SCHE_RULE_LINKS},
    {"identity": F8582_IDENTITY, "facts": F8582_FACTS, "rules": F8582_RULES, "lines": F8582_LINES,
     "diagnostics": F8582_DIAGNOSTICS, "scenarios": F8582_SCENARIOS, "rule_links": F8582_RULE_LINKS},
]


class Command(BaseCommand):
    help = "Load the SCHEDULE_E (Part I) + FORM_8582 specs. Refuses until READY_TO_SEED=True."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad SCHEDULE_E (Part I) + FORM_8582 specs\n"))
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
                "\nREFUSING TO SEED SCHEDULE_E / FORM_8582: not cleared to seed.\n\n"
                "Gated until Ken's review walk (the $25,000 special allowance + the MAGI\n"
                "phaseout + the MFS amounts + the netting + the modified-AGI add-back list +\n"
                "the v1 simplified-bucket deviations).\n\n"
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
        for fn in ("SCHEDULE_E", "FORM_8582"):
            form = TaxForm.objects.filter(form_number=fn).first()
            if form:
                uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
                self.stdout.write(f"{fn}: all rules cited" if not uncited
                                  else self.style.WARNING(f"{fn} uncited rules: {len(uncited)}"))
