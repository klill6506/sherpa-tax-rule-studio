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


READY_TO_SEED = True  # FLIPPED 2026-06-23 — Ken approved the per-activity review walk
# (Parts IV-VIII allocation: line C, the Part VI/VII loss-ratio split, the four activity-type
# feed, the Part IX RED-defer). Prior flip 2026-06-14 (aggregate Part I-III v1, "Looks good.").


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_ENTITY_TYPES = ["1040"]
FORM_STATUS = "active"  # promoted draft→active 2026-07-06 (S-6 reconciliation: SCHEDULE_E + FORM_8582)


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
            {
                "excerpt_label": "Per-activity Parts IV-IX (2025)",
                "location_reference": "i8582 (2025) + f8582.pdf Parts IV-IX",
                "excerpt_text": (
                    "Part IV (Rental Real Estate With Active Participation) and Part V (All Other Passive "
                    "Activities): for each activity enter (a) current-year net income, (b) current-year net loss, "
                    "(c) prior-year unallowed loss; combine for (d) overall gain or (e) overall loss. Totals -> "
                    "Part I lines 1a/1b/1c (IV) and 2a/2b/2c (V). Part VI (use if Part II line 9 > 0): (a) each "
                    "rental real estate loss, (b) ratio = each loss / total losses, (c) special allowance = ratio "
                    "x line 9, (d) = column (a) - column (c). Part VII (Allocation of Unallowed Losses): (a) the "
                    "unallowed losses [Part VI column (d) + Part V column (e)], (b) ratio = each / total, (c) "
                    "unallowed loss = ratio x line C [line C = Part I line 3 minus Part II line 9]. Part VIII "
                    "(Allowed Losses, single form): (a) net loss plus prior-year unallowed loss, (b) unallowed "
                    "loss [Part VII column (c)], (c) allowed loss = column (a) - column (b). Part IX: activities "
                    "with losses reported on two or more forms or schedules."
                ),
                "summary_text": ("Parts IV/V per-activity net (a-e); Part VI allocates line 9 by loss-ratio; Part "
                                 "VII allocates line C (= line 3 loss - line 9) by loss-ratio; Part VIII allowed "
                                 "= loss - unallowed; Part IX = losses on 2+ forms."),
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
            {
                "excerpt_label": "§469(k) — publicly traded partnerships (separate application)",
                "location_reference": "26 U.S.C. §469(k)(1),(3)",
                "excerpt_text": (
                    "§469(k)(1): This section shall be applied separately with respect to items attributable to "
                    "each publicly traded partnership. §469(k)(2): a partnership is publicly traded if interests "
                    "are traded on an established securities market or are readily tradable on a secondary market "
                    "(or the substantial equivalent thereof). §469(k)(3): a taxpayer is not treated as having "
                    "disposed of his entire interest in an activity of a PTP until he disposes of his entire "
                    "interest in such partnership."
                ),
                "summary_text": "§469(k): §469 applied SEPARATELY to each PTP — a PTP passive loss offsets only that same PTP's passive income; suspended losses freed only on full disposition of the entire PTP interest.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§469(c)(7) — real estate professional (the two tests)",
                "location_reference": "26 U.S.C. §469(c)(7)(A),(B),(C)",
                "excerpt_text": (
                    "§469(c)(7)(B): a taxpayer qualifies if (i) more than one-half of the personal services "
                    "performed in trades or businesses during the taxable year are performed in real property "
                    "trades or businesses in which the taxpayer materially participates, and (ii) such taxpayer "
                    "performs more than 750 hours of services during the taxable year in real property trades or "
                    "businesses in which the taxpayer materially participates. In the case of a joint return, the "
                    "requirements are satisfied only if either spouse separately satisfies them. §469(c)(7)(C): "
                    "'real property trade or business' means any real property development, redevelopment, "
                    "construction, reconstruction, acquisition, conversion, rental, operation, management, "
                    "leasing, or brokerage trade or business."
                ),
                "summary_text": "§469(c)(7): REP = (i) >½ personal services in real-property trades/businesses + (ii) >750 hours, BOTH met by one spouse alone (no combining). Qualifying removes the per-se-passive rule for rental RE; each rental still needs material participation unless the §1.469-9(g) election aggregates them.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "TREAS_REG_469",
        "source_type": "regulation",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "Treas. Reg. §1.469 — self-rental recharacterization, RE-professional grouping, at-risk ordering",
        "citation": "26 CFR §1.469-2(f)(6) (self-rental); §1.469-9(e),(g) (RE-pro per-activity + aggregation election); §1.469-2T(d)(6) (at-risk before passive)",
        "issuer": "U.S. Treasury / IRS",
        "official_url": "https://www.law.cornell.edu/cfr/text/26/1.469-2",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "The Treasury regs behind S-6 PAL deepening: (f)(6) self-rental net-income recharacterization; 1.469-9 the real-estate-professional per-activity material-participation rule + the (g) single-activity aggregation election; 1.469-2T(d)(6) the §465-before-§469 ordering.",
        "topics": ["passive_activity_loss"],
        "excerpts": [
            {
                "excerpt_label": "§1.469-2(f)(6) — property rented to a nonpassive activity (self-rental)",
                "location_reference": "26 CFR §1.469-2(f)(6)",
                "excerpt_text": (
                    "An amount of the taxpayer's gross rental activity income for the taxable year from an item of "
                    "property equal to the net rental activity income for the year from that item of property is "
                    "treated as not from a passive activity if the property (i) is rented for use in a trade or "
                    "business activity in which the taxpayer materially participates for the taxable year, and (ii) "
                    "is not described in §1.469-2T(f)(5)."
                ),
                "summary_text": "Self-rental: net rental INCOME (item-by-item) from property rented to a business the taxpayer materially participates in is recharacterized NON-passive. Net income only — a net loss stays passive (the asymmetry).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§1.469-9(e),(g) — RE-professional per-activity + aggregation election",
                "location_reference": "26 CFR §1.469-9(e)(1),(g)",
                "excerpt_text": (
                    "§1.469-9(e)(1): a qualifying taxpayer's interests in rental real estate are each treated as a "
                    "separate rental real estate activity, unless the taxpayer makes the election under paragraph "
                    "(g) to treat all interests in rental real estate as a single rental real estate activity. "
                    "§1.469-9(g): a qualifying taxpayer may make an election to treat all of the taxpayer's "
                    "interests in rental real estate as one activity; material participation is then tested against "
                    "the combined activity."
                ),
                "summary_text": "Qualifying as a REP removes rental RE's per-se-passive status, but each rental is tested for material participation separately UNLESS the §1.469-9(g) election aggregates all rental RE into one activity.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§1.469-2T(d)(6) — passive loss determined after §465 at-risk",
                "location_reference": "26 CFR §1.469-2T(d)(6)",
                "excerpt_text": (
                    "The passive activity deductions for a taxable year are determined after the application of the "
                    "at-risk rules of section 465 (and the basis limitations). A deduction disallowed under section "
                    "465 is not a passive activity deduction for the year and is carried over under section 465."
                ),
                "summary_text": "Ordering: §465 (at-risk) → §469 (passive) → §461(l) (EBL). A §465-limited loss never reaches Form 8582 that year.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_465",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §465 — Deductions Limited to Amount at Risk",
        "citation": "26 U.S.C. §465(b)(1),(2),(6) (amounts at risk; personal liability; qualified nonrecourse financing)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/465",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "The at-risk limitation (Form 6198) applied BEFORE §469 (Reg 1.469-2T(d)(6)) and before §461(l). S-6 R4 = diagnostic-only (route to 6198); the compute lives in the 6198 spec / tts.",
        "topics": ["passive_activity_loss"],
        "excerpts": [
            {
                "excerpt_label": "§465(b) — amounts considered at risk",
                "location_reference": "26 U.S.C. §465(b)(1),(2),(6)",
                "excerpt_text": (
                    "§465(b)(1): a taxpayer is at risk for the amount of money and the adjusted basis of other "
                    "property contributed to the activity, plus amounts borrowed with respect to the activity (as "
                    "limited by (b)(2)). §465(b)(2): borrowed amounts count to the extent the taxpayer is personally "
                    "liable for repayment, or has pledged property (other than property used in the activity) as "
                    "security, to the net FMV of the interest. §465(b)(6): in the case of an activity of holding "
                    "real property, the taxpayer is at risk for the taxpayer's share of qualified nonrecourse "
                    "financing secured by real property used in the activity."
                ),
                "summary_text": "At risk = cash + adjusted basis of contributed property + personally-liable borrowings + qualified nonrecourse financing (real property). Applies before §469.",
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
    # S-6 PAL deepening (2026-07-05)
    ("TREAS_REG_469", "FORM_8582", "governs"),
    ("TREAS_REG_469", "SCHEDULE_E", "informs"),
    ("IRC_465", "FORM_8582", "informs"),
    ("IRC_465", "6198", "governs"),
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
    # ── S-6 R1 self-rental recharacterization (§1.469-2(f)(6)) ──
    {"fact_key": "sche_selfrental_matl_part_tenant", "label": "Self-rental — materially participate in the TENANT trade/business?",
     "data_type": "boolean", "default_value": "false", "sort_order": 16,
     "notes": "INPUT (per type-7 property). §1.469-2(f)(6) gate: material participation in the activity the property is rented TO. Drives R-SCHE-SELFRENTAL."},
    {"fact_key": "sche_selfrental_recharacterized_income", "label": "Self-rental net income recharacterized NON-passive",
     "data_type": "decimal", "sort_order": 17,
     "notes": "OUTPUT. For each type-7 (Self-Rental) property with NET INCOME and tenant material participation: that net income is non-passive (excluded from Form 8582 passive income). Net LOSS stays passive."},
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
                 "professional → non-passive (diagnostic-only, D_8582_RE_PRO info; the engine still applies the "
                 "limitation, preparer adjusts)."),
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
    {"rule_id": "R-SCHE-SELFRENTAL", "title": "Self-rental net income → non-passive (§1.469-2(f)(6))", "rule_type": "calculation",
     "precedence": 5, "sort_order": 5,
     "formula": ("For EACH Self-Rental (type-7) property, ITEM BY ITEM: if the property has NET INCOME (line 21 > 0) "
                 "AND the taxpayer materially participates in the TENANT trade/business "
                 "(sche_selfrental_matl_part_tenant), an amount of gross rental income equal to that net income is "
                 "recharacterized as NON-passive (§1.469-2(f)(6)) → sche_selfrental_recharacterized_income. That "
                 "amount is EXCLUDED from Form 8582 passive income (it may NOT absorb passive losses). A net LOSS "
                 "on a self-rental stays PASSIVE (routes to 8582 like any rental). Applies only where not already "
                 "caught by §1.469-2T(f)(5)."),
     "inputs": ["sche_income_before_limit", "sche_selfrental_matl_part_tenant"],
     "outputs": ["sche_selfrental_recharacterized_income"],
     "description": "S-6 R1. The 'heads-the-IRS-wins' asymmetry — net income non-passive, net loss passive. Item-by-item, not netted across the activity."},
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
    {"diagnostic_id": "D_SCHE_SELFRENTAL", "title": "Self-rental net income recharacterized as non-passive", "severity": "info",
     "condition": "a type-7 (Self-Rental) property has line 21 > 0 AND sche_selfrental_matl_part_tenant is True",
     "message": ("A self-rental property with net income is rented to a business you materially participate in. "
                 "Under §1.469-2(f)(6) that net income is NON-passive — it cannot be offset by passive losses on "
                 "Form 8582. (A self-rental net LOSS remains passive.) Confirm material participation in the "
                 "tenant activity; the recharacterization is applied item-by-item."),
     "notes": "S-6 R1. §1.469-2(f)(6). The compute lives in R-SCHE-SELFRENTAL; this surfaces it to the preparer."},
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
    {"scenario_name": "SCHE-T5 — self-rental net income recharacterized non-passive", "scenario_type": "edge_case", "sort_order": 5,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "property_type": 7, "rents": 36000, "expenses": 21000,
                "selfrental_matl_part_tenant": True, "magi": 140000},
     "expected_outputs": {"sche_income_before_limit": 15000, "sche_selfrental_recharacterized_income": 15000,
                          "sche_net": 15000, "D_SCHE_SELFRENTAL": True},
     "notes": ("Type-7 self-rental: 36,000 − 21,000 = 15,000 net income; materially participates in the tenant "
               "business → §1.469-2(f)(6) recharacterizes the 15,000 as NON-passive (excluded from 8582 passive "
               "income, cannot absorb passive losses). Still reported on line 26 → Schedule 1 line 5.")},
    {"scenario_name": "SCHE-G1 — self-rental net LOSS stays passive", "scenario_type": "diagnostic", "sort_order": 6,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "property_type": 7, "rents": 12000, "expenses": 20000,
                "selfrental_matl_part_tenant": True, "magi": 140000},
     "expected_outputs": {"sche_income_before_limit": -8000, "sche_selfrental_recharacterized_income": 0},
     "notes": ("Self-rental NET LOSS (12,000 − 20,000 = −8,000): the (f)(6) recharacterization does NOT apply to "
               "losses → the 8,000 loss stays PASSIVE and routes to Form 8582 like any rental. No recharacterized "
               "income; D_SCHE_SELFRENTAL does not fire (income branch only).")},
]

SCHE_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-SCHE-NET", "IRS_2025_SCHE_INSTR", "primary", "Part I lines 3-21 (rents/royalties − expenses)"),
    ("R-SCHE-PASSIVE-ROUTE", "IRC_469", "primary", "§469(c)(2) rental = passive per se"),
    ("R-SCHE-PASSIVE-ROUTE", "IRS_2025_SCHE_INSTR", "secondary", "Line 22 hook to Form 8582"),
    ("R-SCHE-8582-LIMIT", "IRS_2025_F8582_INSTR", "primary", "Line 22 = the 8582-allowed loss"),
    ("R-SCHE-TO-SCH1", "IRS_2025_SCHE_INSTR", "primary", "Line 26 → Schedule 1 line 5"),
    ("R-SCHE-SELFRENTAL", "TREAS_REG_469", "primary", "§1.469-2(f)(6) self-rental net income → non-passive"),
    ("R-SCHE-SELFRENTAL", "IRC_469", "secondary", "§469 passive character; the recharacterization rule"),
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
        "the remainder suspended (carryforward). Real estate professional = RED-deferred. "
        "AMENDED 2026-06-23 (per-activity Parts IV-VIII; Ken directive): each passive "
        "activity nets its OWN columns (active rental -> Part IV; non-active rental + passive "
        "K-1 + passive Sch C/F -> Part V); the $25k special allowance is allocated by "
        "loss-ratio (Part VI), the remaining unallowed loss by loss-ratio (Part VII, basis = "
        "line 3 loss - line 9), and each activity's allowed loss (Part VIII = its loss - its "
        "unallowed) flows back to its own schedule; the per-activity unallowed is THAT "
        "activity's carryforward. Part IX (a single activity's losses on 2+ forms / 28%-rate "
        "/ section 1231 separate transaction) is RED-deferred (D_8582_MULTIFORM). "
        "AMENDED 2026-07-05 (S-6 PAL deepening, WO-03): R1 self-rental §1.469-2(f)(6) "
        "net-income recharacterization (on Schedule E); R2 PTP §469(k) per-PTP "
        "segregation off-8582; R3 real estate professional UPGRADED from RED-defer to a "
        "checkbox + §1.469-9(g) aggregation-election flag (two tests preparer-asserted, "
        "sanity-checked, not auto-computed); R4 §465 at-risk diagnostic (ordering "
        "§465→§469→§461(l), routes to Form 6198). §461(l) EBL = the separate Form 461 spec."
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
    {"fact_key": "f8582_line_c", "label": "Line C - total unallowed loss (line 3 loss minus line 9)",
     "data_type": "decimal", "sort_order": 14, "notes": "OUTPUT (per-activity amendment). The Part VII allocation basis: (Part I line 3 loss, positive) minus (Part II line 9). Sum of Part VII column (c) = line C = the total suspended."},
    {"fact_key": "f8582_suspended", "label": "Suspended passive loss (carried forward)",
     "data_type": "decimal", "sort_order": 13, "notes": "OUTPUT. net passive loss − total allowed → next-year carryover."},
    # ── Inputs (return-level facts) ──
    {"fact_key": "f8582_active_participation", "label": "Active participation in rental real estate?",
     "data_type": "boolean", "default_value": "true", "sort_order": 20, "notes": "Drives line 1 vs line 2; the special-allowance gate. §469(i)(6)."},
    {"fact_key": "f8582_real_estate_professional", "label": "Real estate professional (§469(c)(7))?",
     "data_type": "boolean", "default_value": "false", "sort_order": 21, "notes": "Diagnostic-only (D_8582_RE_PRO info, S-6 R3): the engine still applies the 8582 limitation; the preparer adjusts the non-passive rentals."},
    {"fact_key": "f8582_complete_disposition", "label": "Fully taxable disposition of an activity this year?",
     "data_type": "boolean", "default_value": "false", "sort_order": 22, "notes": "§469(g) — releases the prior-year suspended loss in full."},
    {"fact_key": "f8582_mfs_lived_apart", "label": "MFS — lived apart from spouse ALL year?",
     "data_type": "boolean", "default_value": "false", "sort_order": 23, "notes": "MFS-apart → $12,500 / $75k phaseout. (MFS not-apart → $0.)"},
    # ── S-6 R3 real estate professional (checkbox + §1.469-9(g) election) ──
    {"fact_key": "f8582_rep_agg_election", "label": "REP — §1.469-9(g) election to treat all rental RE as ONE activity?",
     "data_type": "boolean", "default_value": "false", "sort_order": 24,
     "notes": "S-6 R3. §1.469-9(g). When elected, material participation is tested against the COMBINED rental RE activity; otherwise each rental is tested separately. Only relevant when f8582_real_estate_professional is True."},
    {"fact_key": "f8582_rep_hours", "label": "REP — hours of services in real property trades/businesses",
     "data_type": "decimal", "default_value": "0", "sort_order": 25,
     "notes": "S-6 R3. OPTIONAL input for the D_8582_REP_TESTS sanity check (>750 hours, §469(c)(7)(B)(ii))."},
    {"fact_key": "f8582_rep_services_majority", "label": "REP — more than ½ of personal services in real property trades/businesses?",
     "data_type": "boolean", "default_value": "false", "sort_order": 26,
     "notes": "S-6 R3. OPTIONAL input for the D_8582_REP_TESTS sanity check (>½ personal services, §469(c)(7)(B)(i)). Per-spouse — not combined."},
    # ── S-6 R2 publicly traded partnership (§469(k)) ──
    {"fact_key": "f8582_ptp_present", "label": "Publicly traded partnership (PTP) passive item present?",
     "data_type": "boolean", "default_value": "false", "sort_order": 27,
     "notes": "S-6 R2. §469(k). PTP passive items are NOT reported on this Form 8582 — computed separately per PTP. Drives R-8582-PTP + D_8582_PTP."},
    # ── S-6 R4 at-risk (§465) diagnostic ──
    {"fact_key": "f8582_at_risk_limited", "label": "A loss may be limited by the §465 at-risk rules (Form 6198)?",
     "data_type": "boolean", "default_value": "false", "sort_order": 28,
     "notes": "S-6 R4. §465 applies BEFORE §469 (Reg 1.469-2T(d)(6)). If set, compute Form 6198 first; only the at-risk-allowed loss reaches Form 8582. Drives D_8582_ATRISK."},
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
    {"rule_id": "R-8582-ALLOWANCE", "title": "Lines 4-9 — the $25,000 active-participation special allowance", "rule_type": "calculation",
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
    {"rule_id": "R-8582-RE-PRO", "title": "Real estate professional → non-passive (checkbox + §1.469-9(g) election)", "rule_type": "routing",
     "precedence": 6, "sort_order": 6,
     "formula": ("If f8582_real_estate_professional (preparer-asserted checkbox): the §469(c)(7) two-test "
                 "qualification removes the per-se-passive rule (§469(c)(2)) for rental real estate — "
                 "materially-participated rentals are NON-passive and bypass the Form 8582 limitation. Each rental "
                 "interest is tested for material participation SEPARATELY unless f8582_rep_agg_election "
                 "(§1.469-9(g)) is made, which tests material participation against the COMBINED rental RE "
                 "activity. v1 does NOT auto-compute the two tests (>750 hours AND >½ personal services, per "
                 "spouse alone) — the preparer asserts qualification; D_8582_REP_TESTS sanity-checks if hours/"
                 "services are entered; D_8582_REP_MATLPART reminds that each un-aggregated rental still needs "
                 "material participation."),
     "inputs": ["f8582_real_estate_professional", "f8582_rep_agg_election"], "outputs": [],
     "description": "S-6 R3 (supersedes the 2026-06-13 RED-defer). Checkbox + §1.469-9(g) aggregation-election flag; the two tests are preparer-asserted, sanity-checked, not auto-computed."},
    # ── Per-activity amendment 2026-06-23 (Parts IV-VIII; Part IX RED) ──
    {"rule_id": "R-8582-WS-NET", "title": "Parts IV/V — per-activity netting into Part I", "rule_type": "calculation",
     "precedence": 7, "sort_order": 7,
     "formula": ("Parts IV and V are FILED (2025 form). For EACH passive activity enter (a) current-year net "
                 "income, (b) current-year net loss (positive), (c) prior-year unallowed loss (positive); overall "
                 "= a - b - c -> (d) overall gain if >= 0 else (e) overall loss (positive). Part IV = rental real "
                 "estate with active participation; Part V = ALL OTHER passive (non-active rental + passive K-1 + "
                 "passive Sch C + passive Sch F). Part I 1a/1b/1c = sum of Part IV cols (a)/(b)/(c); 2a/2b/2c = "
                 "sum of Part V cols; 1d = 1a-1b-1c; 2d = 2a-2b-2c; line 3 = 1d + 2d. The aggregate Part I is now "
                 "the SUM of the per-activity columns (supersedes the single-bucket v1)."),
     "inputs": [], "outputs": [],
     "description": "Per-activity Parts IV/V feed Part I (the four activity types). Replaces the aggregate bucket."},
    {"rule_id": "R-8582-ALLOC-VI", "title": "Part VI — allocate the special allowance by loss-ratio", "rule_type": "calculation",
     "precedence": 8, "sort_order": 8,
     "formula": ("Part VI (only when Part II line 9 > 0): for each ACTIVE-rental activity with an overall loss "
                 "(Part IV col (e) > 0): col (a) = that loss; col (b) ratio = col(a)_i / sum(col(a)); col (c) "
                 "special allowance = ratio x line 9; col (d) = col(a) - col(c) = remaining unallowed. Sum of "
                 "ratios = 1.00; sum of col (c) = line 9. col (d) carries to Part VII col (a)."),
     "inputs": ["f8582_special_allowance"], "outputs": [],
     "description": "Section 469(i) special allowance allocated per active-rental loss activity (Part VI)."},
    {"rule_id": "R-8582-ALLOC-VII", "title": "Part VII — allocate the unallowed loss by loss-ratio (line C)", "rule_type": "calculation",
     "precedence": 9, "sort_order": 9,
     "formula": ("line C = (Part I line 3 loss, as a positive amount) - (Part II line 9). Part VII pool col (a) = "
                 "Part VI col (d) [active-rental remaining] + Part V col (e) [other-passive overall losses]; col "
                 "(b) ratio = col(a)_i / sum(col(a)); col (c) unallowed loss = ratio x line C. Sum of ratios = "
                 "1.00 -> sum of col (c) = line C (the total suspended). The pool basis can EXCEED line C when "
                 "gain/income activities net down line 3 - that is correct; the ratio normalizes."),
     "inputs": ["f8582_line_c"], "outputs": ["f8582_line_c"],
     "description": "Allocation of the remaining unallowed loss across ALL loss activities (Part VII)."},
    {"rule_id": "R-8582-ALLOWED-VIII", "title": "Part VIII — allowed loss per activity; report back", "rule_type": "calculation",
     "precedence": 10, "sort_order": 10,
     "formula": ("Part VIII (single-form activities): col (a) = activity net loss + prior-year unallowed loss "
                 "(its total deduction); col (b) unallowed = Part VII col (c); col (c) allowed = col(a) - col(b). "
                 "Each activity's allowed loss is reported on ITS OWN form/schedule: active/other rental -> "
                 "Schedule E line 22 (-> line 26); passive K-1 -> Schedule E p2 line 28 col (g) (-> line 32/37 -> "
                 "41); passive Sch C -> Schedule C / Schedule 1 line 3; passive Sch F -> Schedule F / Schedule 1 "
                 "line 6. Conservation: sum of allowed = line 11 (= line 9 + line 10)."),
     "inputs": [], "outputs": [],
     "description": "Allowed loss per single-form activity (Part VIII), reported back to its schedule."},
    {"rule_id": "R-8582-CARRYFWD", "title": "Per-activity suspended loss carries forward", "rule_type": "routing",
     "precedence": 11, "sort_order": 11,
     "formula": ("Each activity's unallowed loss (Part VII col (c) / Part VIII col (b)) is suspended and carried "
                 "forward as THAT activity's prior-year unallowed loss next year (Part IV/V col (c)) - tracked "
                 "PER ACTIVITY, not as a single aggregate. A fully taxable disposition of an entire interest "
                 "(section 469(g)) releases that activity's suspended loss in full."),
     "inputs": ["f8582_complete_disposition"], "outputs": [],
     "description": "Section 469(b) per-activity carryforward; 469(g) disposition release."},
    {"rule_id": "R-8582-MULTIFORM", "title": "Part IX (losses on 2+ forms) RED-deferred", "rule_type": "routing",
     "precedence": 12, "sort_order": 12,
     "formula": ("Part IX (a SINGLE passive activity with losses reported on two or more forms/schedules, or "
                 "requiring 28%-rate / section 1231 separate-transaction identification) is NOT supported in v1 "
                 "-> D_8582_MULTIFORM (RED, prepare manually). The common Part IX triggers (section 1231, "
                 "28%-rate) are already RED-deferred upstream in the K-1 router, so no NEW silent gap. Parts "
                 "IV-VIII handle single-form activities."),
     "inputs": [], "outputs": [],
     "description": "Part IX RED-defer (Ken 2026-06-23). No new silent gap; the 1231/28% triggers defer upstream."},
    # ── S-6 R2 PTP segregation (§469(k)) + R4 at-risk ordering (§465) ──
    {"rule_id": "R-8582-PTP", "title": "PTP passive items segregated off Form 8582 (§469(k))", "rule_type": "routing",
     "precedence": 13, "sort_order": 13,
     "formula": ("If f8582_ptp_present: §469 is applied SEPARATELY to each publicly traded partnership (§469(k)(1)). "
                 "PTP passive items are NOT entered on this Form 8582 (excluded from Parts I/IV/V). For each PTP: a "
                 "net passive LOSS offsets ONLY that same PTP's net passive income; any excess is suspended and "
                 "carried forward against THAT PTP's future income; PTP net income above the loss is treated as "
                 "portfolio-like (included in MAGI). Suspended PTP losses are freed only on a fully taxable "
                 "disposition of the ENTIRE interest in that PTP (§469(k)(3)/§469(g)). Tracked PER PTP, off-8582."),
     "inputs": ["f8582_ptp_present"], "outputs": [],
     "description": "S-6 R2. §469(k) — PTPs computed separately, per-PTP, and never mixed into the 8582 aggregate."},
    {"rule_id": "R-8582-ATRISK-ORDER", "title": "§465 at-risk applies BEFORE §469 (route to Form 6198)", "rule_type": "routing",
     "precedence": 14, "sort_order": 14,
     "formula": ("Ordering (Reg §1.469-2T(d)(6)): §465 at-risk → §469 passive → §461(l) EBL. If f8582_at_risk_limited, "
                 "the loss is limited on Form 6198 FIRST; only the at-risk-allowed portion becomes a passive "
                 "deduction that reaches Form 8582. A §465-disallowed loss is suspended under §465 (not §469) and "
                 "carried forward. v1 = diagnostic-only (D_8582_ATRISK); the at-risk COMPUTE lives in the Form 6198 "
                 "spec / tts."),
     "inputs": ["f8582_at_risk_limited"], "outputs": [],
     "description": "S-6 R4. The at-risk-before-passive ordering; diagnostic-only, routes to 6198."},
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
    # ── Per-activity amendment 2026-06-23 (Parts IV-VIII descriptors + line C) ──
    {"line_number": "C", "description": "Line C - line 3 loss minus line 9 (total unallowed; Part VII basis)", "line_type": "calculated"},
    {"line_number": "P4", "description": "Part IV - rental RE (active participation), per-activity cols (a)-(e) -> Part I 1a/1b/1c", "line_type": "informational"},
    {"line_number": "P5", "description": "Part V - all other passive, per-activity cols (a)-(e) -> Part I 2a/2b/2c", "line_type": "informational"},
    {"line_number": "P6", "description": "Part VI - special-allowance allocation: (a) loss, (b) ratio, (c) ratio x line 9, (d) (a)-(c)", "line_type": "informational"},
    {"line_number": "P7", "description": "Part VII - unallowed-loss allocation: (a) loss [VI(d)+V(e)], (b) ratio, (c) ratio x line C", "line_type": "informational"},
    {"line_number": "P8", "description": "Part VIII - allowed loss per activity: (a) loss+prior, (b) unallowed [VII(c)], (c) allowed (a)-(b)", "line_type": "informational"},
]

F8582_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_8582_RE_PRO", "title": "Real estate professional asserted — rentals treated non-passive", "severity": "info",
     "condition": "f8582_real_estate_professional is True",
     "message": ("Real estate professional status (§469(c)(7)) is asserted: materially-participated rental real "
                 "estate is NON-passive and should bypass the Form 8582 limitation. This software does NOT "
                 "auto-compute the non-passive split — it still applies the passive limitation to the rentals it "
                 "sees, so verify the treatment and adjust the non-passive rentals manually. The two qualification "
                 "tests (>750 hours AND >½ personal services in real property trades/businesses, met by one spouse "
                 "alone) are preparer-asserted, not auto-computed — confirm they are met."),
     "notes": "S-6 R3 (supersedes the RED-defer). Checkbox-asserted; sanity check via D_8582_REP_TESTS."},
    {"diagnostic_id": "D_8582_REP_TESTS", "title": "REP claimed but a qualification test may fail", "severity": "warning",
     "condition": "f8582_real_estate_professional is True AND (0 < f8582_rep_hours <= 750 OR f8582_rep_services_majority is False)",
     "message": ("You claimed real estate professional status, but the entered figures do not meet a §469(c)(7)(B) "
                 "test: services must exceed 750 hours AND more than one-half of ALL personal services must be in "
                 "real property trades/businesses (each met by one spouse alone — hours may not be combined). "
                 "Re-verify qualification or clear the REP checkbox."),
     "notes": "S-6 R3. Sanity check only when the optional hours/services inputs are provided."},
    {"diagnostic_id": "D_8582_REP_MATLPART", "title": "REP — each rental still needs material participation", "severity": "info",
     "condition": "f8582_real_estate_professional is True AND f8582_rep_agg_election is False",
     "message": ("You qualified as a real estate professional but did NOT make the §1.469-9(g) election to treat "
                 "all rental real estate as one activity. Each rental interest must separately meet a material "
                 "participation test to be non-passive; rentals you do not materially participate in remain "
                 "passive. Consider the aggregation election if appropriate."),
     "notes": "S-6 R3. §1.469-9(e)/(g)."},
    {"diagnostic_id": "D_8582_PTP", "title": "PTP passive items computed separately (off Form 8582)", "severity": "info",
     "condition": "f8582_ptp_present is True",
     "message": ("Publicly traded partnership (PTP) passive items are NOT reported on Form 8582 (§469(k)). A PTP "
                 "passive loss offsets only net passive income from that SAME PTP; the excess is suspended and "
                 "carried forward against that PTP's future income, and is freed only on a fully taxable "
                 "disposition of your entire interest in that PTP. Compute each PTP separately."),
     "notes": "S-6 R2. §469(k)."},
    {"diagnostic_id": "D_8582_ATRISK", "title": "At-risk (§465) applies before the passive limitation", "severity": "warning",
     "condition": "f8582_at_risk_limited is True",
     "message": ("A loss may be limited by the §465 at-risk rules. At-risk applies BEFORE the passive activity "
                 "limitation (Reg §1.469-2T(d)(6)): figure Form 6198 first, and enter only the at-risk-allowed "
                 "loss on Form 8582. A loss disallowed by §465 is carried over under §465, not §469."),
     "notes": "S-6 R4. Diagnostic-only; the at-risk compute lives in Form 6198."},
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
    {"diagnostic_id": "D_8582_MULTIFORM", "title": "Passive losses on 2+ forms (Part IX) not supported", "severity": "error",
     "condition": "a passive activity reports losses on two or more forms/schedules, OR a 28%-rate or section 1231 passive loss needs separate-transaction identification (Form 8582 Part IX)",
     "message": ("Not supported - prepare manually: this passive activity has losses reported on two or more "
                 "forms or schedules, or involves a 28%-rate or section 1231 transaction requiring separate "
                 "identification (Form 8582 Part IX). The software allocates the passive loss only for "
                 "single-form activities (Parts IV-VIII). Figure the Part IX per-form allocation manually. The "
                 "section 1231 / 28%-rate K-1 items are already flagged upstream by the K-1 router."),
     "notes": "Per-activity amendment 2026-06-23 (Ken). Part IX RED-defer; no new silent gap."},
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
    {"scenario_name": "8582-G1 — real estate professional → info", "scenario_type": "diagnostic", "sort_order": 6,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "rental_loss": 50000, "magi": 200000,
                "active_participation": True, "real_estate_professional": True},
     "expected_outputs": {"D_8582_RE_PRO": True},
     "notes": "RE-pro flagged → D_8582_RE_PRO (info, S-6 R3 diagnostic-only). The engine STILL applies the 8582 limitation to the rentals it sees; the preparer adjusts the non-passive rentals manually."},
    {"scenario_name": "8582-G2 — MFS lived together → $0 allowance", "scenario_type": "diagnostic", "sort_order": 7,
     "inputs": {"tax_year": 2025, "filing_status": "mfs", "rental_loss": 12000, "magi": 30000,
                "active_participation": True, "mfs_lived_apart": False},
     "expected_outputs": {"f8582_special_allowance": 0, "f8582_suspended": 12000, "D_8582_MFS_TOGETHER": True},
     "notes": "MFS lived together → no special allowance (skip Part II); the 12,000 loss fully suspended; D_8582_MFS_TOGETHER warns."},
    # ── Per-activity amendment 2026-06-23 (Parts IV-VIII allocation) ──
    {"scenario_name": "8582-PA1 — two active rentals, phaseout splits by loss-ratio", "scenario_type": "normal", "sort_order": 8,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "magi": 120000,
                "activities": [{"name": "Rental A", "bucket": "IV", "loss": 30000},
                               {"name": "Rental B", "bucket": "IV", "loss": 10000}]},
     "expected_outputs": {"f8582_special_allowance": 15000, "f8582_line_c": 25000,
                          "f8582_total_allowed": 15000, "f8582_suspended": 25000,
                          "per_activity": [{"name": "Rental A", "allowed": 11250, "suspended": 18750},
                                           {"name": "Rental B", "allowed": 3750, "suspended": 6250}]},
     "notes": ("line3=(40,000); line4=40,000; MAGI 120k -> line9=min(40k, 50%x(150k-120k)=15k, 25k cap)=15,000; "
               "line C=40k-15k=25,000. Part VI ratios .75/.25 -> allowances 11,250/3,750. Part VII pool "
               "[18,750/6,250]=25k -> unallowed 18,750/6,250. Part VIII allowed 30k-18,750=11,250 / 10k-6,250="
               "3,750. Sum allowed=15,000=line 11; sum suspended=25,000=line C.")},
    {"scenario_name": "8582-PA2 — active rental + passive K-1 + passive income (Part VII split)", "scenario_type": "normal", "sort_order": 9,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "magi": 90000,
                "activities": [{"name": "Rental", "bucket": "IV", "loss": 20000},
                               {"name": "K-1 LP", "bucket": "V", "loss": 10000},
                               {"name": "K-1 Inc", "bucket": "V", "income": 5000}]},
     "expected_outputs": {"f8582_special_allowance": 20000, "f8582_line_c": 5000,
                          "f8582_total_allowed": 25000, "f8582_suspended": 5000,
                          "per_activity": [{"name": "Rental", "allowed": 20000, "suspended": 0},
                                           {"name": "K-1 LP", "allowed": 5000, "suspended": 5000}]},
     "notes": ("line1d=(20,000); line2d=5,000-10,000=(5,000); line3=(25,000); line4=20,000; MAGI 90k -> line9="
               "20,000 (full); line C=25k-20k=5,000. Part VI: rental gets all 20k -> remaining 0. Part VII pool "
               "[0 + K-1 10,000] -> K-1 unallowed=5,000. Part VIII: rental allowed 20,000 (0 susp); K-1 allowed "
               "10k-5k=5,000 (5,000 susp). +5,000 income reported in full. Sum allowed losses=25,000=line 11.")},
    {"scenario_name": "8582-PA3 — other-passive only (no special allowance), gain offsets", "scenario_type": "edge_case", "sort_order": 10,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "magi": 200000,
                "activities": [{"name": "LP loss (non-PTP)", "bucket": "V", "loss": 12000},
                               {"name": "K-1 gain", "bucket": "V", "income": 4000}]},
     "expected_outputs": {"f8582_special_allowance": 0, "f8582_line_c": 8000,
                          "f8582_total_allowed": 4000, "f8582_suspended": 8000,
                          "per_activity": [{"name": "LP loss (non-PTP)", "allowed": 4000, "suspended": 8000}]},
     "notes": ("No active rental -> line1d=0; line2d=4,000-12,000=(8,000); line3=(8,000). line1d>=0 -> skip Part "
               "II, line9=0. line C=8,000. Part VII pool [12,000] -> unallowed 8,000. Part VIII allowed 12k-8k="
               "4,000 (8,000 susp); +4,000 income full. Sum allowed=4,000=line 11 (=line9 0 + line10 income "
               "4,000); the special allowance never applies to non-active-participation passive losses. NOTE: a "
               "non-PTP passive interest (PTPs are segregated off-8582 per R-8582-PTP / 8582-PTP1).")},
    {"scenario_name": "8582-PG1 — passive losses on 2+ forms -> Part IX RED", "scenario_type": "diagnostic", "sort_order": 11,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "magi": 100000,
                "activities": [{"name": "K-1 mixed", "bucket": "V", "loss": 15000, "losses_on_multiple_forms": True}]},
     "expected_outputs": {"D_8582_MULTIFORM": True},
     "notes": ("A single activity reporting losses on 2+ forms/schedules (e.g. Sch E operating loss + a 4797 "
               "loss) requires Part IX -> RED-deferred (D_8582_MULTIFORM), prepare manually. The 1231/28% K-1 "
               "triggers are already RED-deferred upstream in the K-1 router.")},
    # ── S-6 PAL deepening scenarios (2026-07-05) ──
    {"scenario_name": "8582-REP1 — real estate professional asserted, no aggregation election", "scenario_type": "diagnostic", "sort_order": 12,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "real_estate_professional": True,
                "rep_hours": 1600, "rep_services_majority": True, "rep_agg_election": False},
     "expected_outputs": {"D_8582_RE_PRO": True, "D_8582_REP_MATLPART": True},
     "notes": ("REP asserted (1,600 hrs > 750 AND >½ services): materially-participated rentals treated "
               "non-passive (D_8582_RE_PRO info). No §1.469-9(g) election → D_8582_REP_MATLPART reminds each "
               "rental still needs material participation. D_8582_REP_TESTS does NOT fire (both tests met).")},
    {"scenario_name": "8582-REP2 — REP claimed but 750-hour test fails", "scenario_type": "diagnostic", "sort_order": 13,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "real_estate_professional": True,
                "rep_hours": 600, "rep_services_majority": True, "rep_agg_election": True},
     "expected_outputs": {"D_8582_REP_TESTS": True},
     "notes": ("REP claimed but only 600 hours entered (<= 750) → D_8582_REP_TESTS warns the §469(c)(7)(B)(ii) "
               "test is not met. Aggregation elected, so D_8582_REP_MATLPART does not fire.")},
    {"scenario_name": "8582-PTP1 — PTP passive item segregated off 8582", "scenario_type": "diagnostic", "sort_order": 14,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "magi": 150000, "ptp_present": True},
     "expected_outputs": {"D_8582_PTP": True},
     "notes": ("A PTP passive item is present → D_8582_PTP: §469(k) computes each PTP separately, off Form 8582. "
               "PTP loss offsets only same-PTP income; freed on full disposition. Not entered in Parts I/IV/V.")},
    {"scenario_name": "8582-AR1 — at-risk may limit before passive", "scenario_type": "diagnostic", "sort_order": 15,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "magi": 120000, "at_risk_limited": True,
                "rental_loss": 20000, "active_participation": True},
     "expected_outputs": {"D_8582_ATRISK": True},
     "notes": ("A loss flagged as possibly at-risk-limited → D_8582_ATRISK: figure Form 6198 FIRST (§465 before "
               "§469, Reg 1.469-2T(d)(6)); only the at-risk-allowed loss reaches Form 8582.")},
]

F8582_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-8582-PASSIVE", "IRC_469", "primary", "§469(c)(2) rental = passive per se; the netting"),
    ("R-8582-PASSIVE", "IRS_2025_F8582_INSTR", "secondary", "Part I lines 1a-3"),
    ("R-8582-MAGI", "IRS_2025_F8582_INSTR", "primary", "The modified-AGI add-back list (line 6)"),
    ("R-8582-ALLOWANCE", "IRC_469", "primary", "§469(i) the $25,000 offset + phaseout"),
    ("R-8582-ALLOWANCE", "IRS_2025_F8582_INSTR", "primary", "Part II lines 4-9"),
    ("R-8582-ALLOWED", "IRS_2025_F8582_INSTR", "primary", "Part III lines 10-11 (total allowed)"),
    ("R-8582-DISPOSITION", "IRC_469", "primary", "§469(g) disposition releases the suspended loss"),
    ("R-8582-RE-PRO", "IRC_469", "primary", "§469(c)(7) real-estate-professional exception"),
    # ── Per-activity amendment 2026-06-23 (Parts IV-VIII; Part IX RED) ──
    ("R-8582-WS-NET", "IRS_2025_F8582_INSTR", "primary", "Parts IV/V per-activity columns -> Part I 1a-2c"),
    ("R-8582-WS-NET", "IRC_469", "secondary", "469(c)(2) rental passive per se; 469(d) per-activity loss"),
    ("R-8582-ALLOC-VI", "IRC_469", "primary", "469(i) the $25,000 allowance allocated per activity"),
    ("R-8582-ALLOC-VI", "IRS_2025_F8582_INSTR", "primary", "Part VI ratio allocation (col a/b/c/d)"),
    ("R-8582-ALLOC-VII", "IRS_2025_F8582_INSTR", "primary", "Part VII line C unallowed-loss allocation"),
    ("R-8582-ALLOC-VII", "IRC_469", "secondary", "469(b) the disallowed loss carryforward"),
    ("R-8582-ALLOWED-VIII", "IRS_2025_F8582_INSTR", "primary", "Part VIII allowed loss + How To Report Allowed Losses"),
    ("R-8582-ALLOWED-VIII", "IRC_469", "secondary", "469 per-activity allowed/unallowed split"),
    ("R-8582-CARRYFWD", "IRC_469", "primary", "469(b) carryforward; 469(g) disposition release"),
    ("R-8582-CARRYFWD", "IRS_2025_F8582_INSTR", "secondary", "per-activity prior-year unallowed (col c)"),
    ("R-8582-MULTIFORM", "IRS_2025_F8582_INSTR", "primary", "Part IX losses on 2+ forms"),
    ("R-8582-MULTIFORM", "IRC_469", "secondary", "469 per-activity loss character"),
    # ── S-6 PAL deepening (2026-07-05) ──
    ("R-8582-RE-PRO", "TREAS_REG_469", "secondary", "§1.469-9(e)/(g) per-activity material participation + aggregation election"),
    ("R-8582-PTP", "IRC_469", "primary", "§469(k) separate application to each PTP; disposition rule"),
    ("R-8582-ATRISK-ORDER", "IRC_465", "primary", "§465(b) amounts at risk"),
    ("R-8582-ATRISK-ORDER", "TREAS_REG_469", "secondary", "§1.469-2T(d)(6) at-risk before passive"),
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
     "description": "Validates R-8582-ALLOWANCE. Bug it catches: the phaseout not applied (8582-T2 → $15k) or the cap exceeded.",
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
     "title": "Gates: RE-pro info; MFS-together $0 allowance",
     "description": "A real-estate-professional flag fires D_8582_RE_PRO (info, S-6 R3 diagnostic-only — was RED pre-S-6); MFS lived-together → $0 special allowance (D_8582_MFS_TOGETHER).",
     "definition": {"kind": "gating_check", "form": "FORM_8582", "expect": {"info_fires": True},
                    "blockers": ["real_estate_professional", "mfs_lived_together"]},
     "sort_order": 6},
    # ── Per-activity amendment 2026-06-23 (Parts IV-VIII) ──
    {"assertion_id": "FA-1040-8582-05", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "Per-activity allocation conserves (sum allowed = line 11; sum suspended = line C)",
     "description": "Validates R-8582-ALLOC-VII / R-8582-ALLOWED-VIII. Bug it catches: a per-activity allowed/suspended split that doesn't sum to the form totals (a loss vanishing or double-allocated).",
     "definition": {"kind": "reconciliation", "form": "FORM_8582",
                    "formula": "sum(per_activity.allowed) == line_11; sum(per_activity.suspended) == line_C; line_C == line_3_loss - line_9"},
     "sort_order": 7},
    {"assertion_id": "FA-1040-8582-06", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Part VI/VII allocate by loss-ratio (8582-PA1 .75/.25 split)",
     "description": "Validates R-8582-ALLOC-VI / R-8582-ALLOC-VII. Bug it catches: an even split or wrong basis — each activity's share must be its loss / total losses, times line 9 (Part VI) or line C (Part VII).",
     "definition": {"kind": "formula_check", "form": "FORM_8582",
                    "formula": "activity_unallowed_i == line_C * (activity_loss_i / sum(activity_loss)); activity_allowed_i == activity_gross_i - activity_unallowed_i"},
     "sort_order": 8},
    {"assertion_id": "FA-1040-8582-07", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Part IX (losses on 2+ forms) fires D_8582_MULTIFORM (RED)",
     "description": "No silent gap: a passive activity with losses on 2+ forms, or a 28%-rate / section 1231 separate transaction, RED-defers (Part IX not supported in v1).",
     "definition": {"kind": "gating_check", "form": "FORM_8582", "expect": {"red_fires": True},
                    "blockers": ["losses_on_multiple_forms"]},
     "sort_order": 9},
    # ── S-6 PAL deepening (2026-07-05) ──
    {"assertion_id": "FA-1040-SCHE-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Self-rental net income recharacterized non-passive (§1.469-2(f)(6))",
     "description": "Validates R-SCHE-SELFRENTAL. Bug it catches: self-rental net income leaking into Form 8582 passive income (where it could wrongly absorb passive losses), or a self-rental net LOSS being wrongly recharacterized (losses stay passive).",
     "definition": {"kind": "formula_check", "form": "SCHEDULE_E",
                    "formula": "type7 & line_21>0 & matl_part_tenant => recharacterized_income == line_21 (excluded from 8582 passive income); type7 & line_21<0 => recharacterized_income == 0 (loss stays passive)"},
     "sort_order": 10},
    {"assertion_id": "FA-1040-8582-08", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "PTP segregated off-8582 (§469(k)); at-risk routes to 6198 before passive",
     "description": "Validates R-8582-PTP / R-8582-ATRISK-ORDER. Bug it catches: a PTP item entered in the 8582 aggregate (Parts I/IV/V) instead of computed per-PTP; or a §465-limited loss reaching 8582 without the 6198 pass first.",
     "definition": {"kind": "gating_check", "form": "FORM_8582", "expect": {"red_fires": False, "info_fires": True},
                    "blockers": ["ptp_present", "at_risk_limited"]},
     "sort_order": 11},
]


FORMS: list[dict] = [
    {"identity": SCHE_IDENTITY, "facts": SCHE_FACTS, "rules": SCHE_RULES, "lines": SCHE_LINES,
     "diagnostics": SCHE_DIAGNOSTICS, "scenarios": SCHE_SCENARIOS, "rule_links": SCHE_RULE_LINKS},
    {"identity": F8582_IDENTITY, "facts": F8582_FACTS, "rules": F8582_RULES, "lines": F8582_LINES,
     "diagnostics": F8582_DIAGNOSTICS, "scenarios": F8582_SCENARIOS, "rule_links": F8582_RULE_LINKS},
]


class Command(BaseCommand):
    help = "Load the SCHEDULE_E (Part I) + FORM_8582 specs. Refuses until READY_TO_SEED=True."

    def add_arguments(self, parser):
        parser.add_argument(
            "--only", default=None,
            help=("Seed only this form_number (e.g. FORM_8582). Scopes the FORMS loop + "
                  "the flow assertions; shared sources/topics/form-links still upsert "
                  "additively. Used by the 2026-06-23 per-activity amendment to avoid "
                  "re-touching SCHEDULE_E (the K-1 router owns its page-2 spec)."))

    @transaction.atomic
    def handle(self, *args, **opts):
        only = opts.get("only")
        forms = [s for s in FORMS if (only is None or s["identity"]["form_number"] == only)]
        if not forms:
            raise CommandError(f"--only {only!r} matched no form in FORMS")
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\nLoad {' + '.join(s['identity']['form_number'] for s in forms)} spec(s)\n"))
        self._load_topics()
        sources = self._load_sources()
        self._load_new_excerpts_on_existing(sources)
        for spec in forms:
            form = self._upsert_form(spec["identity"])
            self._upsert_facts(form, spec["facts"])
            rules = self._upsert_rules(form, spec["rules"])
            self._upsert_authority_links(rules, sources, spec["rule_links"])
            self._upsert_lines(form, spec["lines"])
            self._upsert_diagnostics(form, spec["diagnostics"])
            self._upsert_tests(form, spec["scenarios"])
        self._upsert_form_links(sources)
        self._load_flow_assertions(only)
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

    def _load_flow_assertions(self, only=None):
        fas = [a for a in FLOW_ASSERTIONS
               if only is None or a.get("definition", {}).get("form") == only]
        for a in fas:
            a = dict(a)
            FlowAssertion.objects.update_or_create(assertion_id=a.pop("assertion_id"), defaults=a)
        self.stdout.write(f"  {len(fas)} flow assertions" + (f" (scoped to {only})" if only else ""))

    def _report_totals(self):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(f"TaxForms: {TaxForm.objects.count()} | FlowAssertions: {FlowAssertion.objects.count()}")
        for fn in ("SCHEDULE_E", "FORM_8582"):
            form = TaxForm.objects.filter(form_number=fn).first()
            if form:
                uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
                self.stdout.write(f"{fn}: all rules cited" if not uncited
                                  else self.style.WARNING(f"{fn} uncited rules: {len(uncited)}"))
