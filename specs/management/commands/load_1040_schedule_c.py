"""Load the Schedule C / SE / 8995 / 8959 specs — Sprint Topic 8 (NEXT-UP #1).

Creates FOUR TaxForms (one idempotent command, the load_1040_eic.py precedent):

  - SCHEDULE_C (Profit or Loss From Business): the sole-proprietor P&L — Part I
    income, Part II expenses, Part III Cost of Goods Sold, the simplified-method
    home-office deduction (line 30), and the at-risk routing (line 32). Net profit
    (line 31) feeds Schedule 1 line 3 AND Schedule SE line 2. PER BUSINESS
    (multiple Schedule C per return; FK model). Depreciation (line 13) reuses the
    mature 4562 engine.
  - SCHEDULE_SE (Self-Employment Tax): Part I standard method — net SE earnings
    x 92.35%, the 12.4% SS portion capped by the year-keyed wage base (consuming
    W-2 social-security wages), the uncapped 2.9% Medicare portion -> SE tax
    (line 12 -> Schedule 2 line 4) and the 1/2-SE-tax deduction (line 13 ->
    Schedule 1 line 15). PER PROPRIETOR (aggregates that person's Schedule C
    businesses). Part II optional methods = RED-defer.
  - 8995 (QBI Deduction, Simplified Computation) — RE-AUTHORED. The existing RS
    "8995" is a wrong early-draft stub (Line 2 QBI sourced "from K-1", an 8-line
    map != the real 17-line face, no income limitation / REIT-PTP split / loss
    carryforward). This loader RETIRES the stub artifacts and authors the real
    17-line face: per-business QBI (Sch C net profit reduced by attributable
    1/2-SE-tax / SEHI / SE-retirement) x 20%, the REIT/PTP component x 20%, the
    taxable-income-x-20% limitation -> Form 1040 line 13a. Below-threshold only;
    above threshold -> RED "use Form 8995-A".
  - 8959 (Additional Medicare Tax) — Ken-expanded scope (Decision 4). Part I
    (Medicare wages over the filing-status threshold x 0.9%), Part II (SE income
    over the threshold REDUCED BY Medicare wages x 0.9%) -> Schedule 2 line 11;
    Part V withholding reconciliation -> Form 1040 line 25c. Part III RRTA =
    RED-defer.

Session 2026-06-12: authored by transcription from primary sources fetched and
text-extracted the same day (pymupdf dumps in tts-tax-app server/.scratch/;
consolidated in tts-tax-app server/specs/_topic8_schedulec_source_brief.md):

  - 2025 Schedule C (f1040sc.pdf, Attachment Seq 09) + i1040sc instructions.
  - 2025 Schedule SE (f1040sse.pdf, Attachment Seq 17).
  - 2025 Form 8995 (f8995.pdf, Attachment Seq 55) + i8995 instructions.
  - 2025 Form 8959 (f8959.pdf, Attachment Seq 71) + i8959 instructions.
  - IRS Topic 751 + SSA: SS/Medicare rates, 2026 SS wage base $184,500.
  - Rev. Proc. 2025-32 §4.26: 2026 §199A QBI thresholds.

TOPIC SCOPE (SPRINT_SCOPE.md NEXT-UP #1; DECISIONS.md 2026-06-12 — Ken-confirmed
4 kickoff decisions; memory topic8-schedulec-scope):
  IN: Schedule C P&L incl. Part III COGS (Decision 1); home-office simplified
      method inline ($5/sqft x <=300 sqft) (Decision 2); MULTIPLE Schedule C per
      return (Decision 3, FK model; SE aggregates per proprietor, QBI per
      business); Schedule SE standard method; SEHI (-> Sch 1 line 17, limited to
      net SE profit); Form 8995 simplified QBI; Form 8959 (Decision 4);
      depreciation via the existing 4562 engine.
  OUT (RED "prepare manually", never silently computed; enumerated in the spec):
      Form 8829 actual-expense home office; Form 6198 at-risk / passive-loss
      limits (Sch C line 32b); SE optional methods (farm/nonfarm, Sch SE Part II);
      church-employee SE income (Sch SE line 5); statutory-employee Schedule C
      (W-2 box 13); Form 8995-A (above-threshold / SSTB / W-2-UBIA); RRTA
      compensation on Form 8959 (Part III); SEHI<->PTC circular (until Form 8962
      exists, SPRINT_SCOPE NEXT-UP #1).

YEAR-KEYED CONSTANTS (target-year policy: TY2026 product target, TY2025
verification bed; verify each year independently — never assume 2025 carries):
  - SE social-security WAGE BASE is inflation-indexed: 2025 $176,100 / 2026
    $184,500 (SE_WAGE_BASE). _constants_for_year at the build leg.
  - 8995 8995-vs-8995A THRESHOLD is RP-indexed: 2025 $394,600 MFJ / $197,300
    other; 2026 $403,500 MFJ / $201,775 MFS / $201,750 other (QBI_THRESHOLDS).
  - STATUTORY / NON-INDEXED (do NOT year-key — the Topic 5 §86 lesson): SE rates
    92.35% / 12.4% / 2.9% / 50%, the $400 filing floor; the 8959 thresholds
    ($250k MFJ / $125k MFS / $200k other) + the 0.9% / 1.45% rates; the 20% QBI
    rate; the home-office $5/sqft x 300-sqft safe harbor (Rev. Proc. 2013-13).

requires_human_review WALK ITEMS (flagged in the source notes + rule
descriptions for Ken's review walk):
  1. 2026 MFS 8995 threshold $201,775 is $25 ABOVE "all other" $201,750 (an RP
     rounding artifact; 2025 i8995 lumped all non-MFJ at $197,300). For the
     simplified 8995 this only moves the 8995-vs-8995A *diagnostic* boundary, not
     the compute. Confirm the per-status 2026 table at the walk.
  2. MULTI-BUSINESS QBI allocation: when a person has >1 Schedule C, the
     1/2-SE-tax / SEHI / SE-retirement reductions to QBI must be allocated across
     businesses. Default = pro-rata by each business's net SE earnings (standard
     convention). Confirm at the walk.
  3. 8995 line 12 NET CAPITAL GAIN: Schedule D is NOT built yet (later topic), so
     v1 net capital gain = 1040 line 3a (qualified dividends) + line 7
     (cap-gain distributions when no Sch D). When Schedule D lands, line 12 must
     add net LT capital gain. Deferred-interaction, confirm scope at the walk.
  4. 8995 QBI LOSS CARRYFORWARD (lines 3/7 in, 16/17 out): v1 = preparer-entered
     prior-year carryforward + compute the current-year carryforward when net QBI
     < 0. Confirm v1 supports carryforward vs RED-defer.

SPINE / SIBLING SUPERSESSION (build leg, flagged for Ken — the Topic 5 Sch 2 L8 /
Topic 7 L27a precedent; override = escape hatch):
  - Schedule 1 line 15 (1/2-SE-tax) becomes a COMPUTED feeder from Sch SE line 13
    (today direct-entry). ALREADY an EIC Worksheet-B feeder (eic_se_half_deduction
    <- Sch 1 L15) + an 8812 feeder — re-point cleanly.
  - Schedule 1 line 17 (SEHI) becomes a COMPUTED feeder (limited to net SE profit).
  - Schedule 2 line 4 (SE tax) becomes a COMPUTED feeder from Sch SE line 12.
  - Schedule 2 line 11 (Additional Medicare Tax) becomes a COMPUTED feeder from
    Form 8959 line 18.
  - Form 1040 line 13a (QBI deduction) becomes a COMPUTED feeder from Form 8995
    line 15.
  - Form 1040 line 25c picks up Form 8959 line 24 (Additional Medicare withholding).
  The flow-assertion gate (86 active / 108 passed) must not regress.

Safety guard
------------
`READY_TO_SEED = False`. Content is authored; Ken reviews the packet (the verified
constants both years, the 4 walk items, the cross-form flow, the RED-defer
enumeration), flips the sentinel, then we seed. Until then the command refuses to
write to the DB. Idempotent via update_or_create — safe to re-run after edits.

DO NOT relax the safety guard to silence the error.
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
# SAFETY GUARD — flip ONLY after Ken's in-session review walk (the source
# citations, the verified constants BOTH years, the 4 requires_human_review walk
# items, the cross-form flow map, the RED-defer enumeration). Until then the
# command refuses to write to the DB (zero writes while False).
#
# FLIPPED 2026-06-12 — Ken APPROVED the review walk in-session: the verified
# constants both years, the 4 requires_human_review walk items (2026 MFS 8995
# threshold $201,775 as published; multi-business QBI reduction allocated pro-rata
# by net SE earnings; 8995 L12 net capital gain = 1040 L3a + cap-gain distributions
# in v1, net-LT-gain added when Schedule D lands + D_8995_002 warning; QBI loss
# carryforward supported in v1), and the RED-defer enumeration.
# ═══════════════════════════════════════════════════════════════════════════
READY_TO_SEED = True


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1040"]


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS (brief §1 — every value cited; never training memory)
# ═══════════════════════════════════════════════════════════════════════════

# Schedule SE social-security wage base — YEAR-INDEXED.
#   2025 $176,100 (Sch SE line 7, on the 2025 face) / 2026 $184,500 (IRS Topic
#   751 + SSA). The SS portion (line 10) is capped at this; the Medicare portion
#   (line 11) is uncapped.
SE_WAGE_BASE: dict[int, int] = {2025: 176100, 2026: 184500}

# Statutory SE factors/rates — NON-indexed (same both years).
SE_NET_EARNINGS_FACTOR = 0.9235   # Sch SE line 4a (92.35%)
SE_SS_RATE = 0.124                # Sch SE line 10 (12.4%)
SE_MEDICARE_RATE = 0.029          # Sch SE line 11 (2.9%)
SE_HALF_DEDUCTION_RATE = 0.50     # Sch SE line 13 (50%)
SE_FILING_FLOOR = 400             # Sch SE line 4c ("if less than $400, stop")

# Form 8959 Additional Medicare Tax — thresholds NON-indexed (i8959), same years.
ADDL_MEDICARE_RATE = 0.009        # 0.9%
REGULAR_MEDICARE_RATE = 0.0145    # 1.45% (8959 line 21 regular withholding)
ADDL_MEDICARE_THRESHOLDS: dict[str, int] = {
    "mfj": 250000, "mfs": 125000, "other": 200000,  # Single / HOH / QSS = other
}

# Form 8995 §199A QBI — rate statutory; 8995-vs-8995A threshold YEAR-INDEXED.
QBI_RATE = 0.20                   # 8995 lines 5/9/14 (20%)
QBI_THRESHOLDS: dict[int, dict] = {
    2025: {"mfj": 394600, "mfs": 197300, "other": 197300},  # i8995 (2025 lumped all non-MFJ)
    2026: {"mfj": 403500, "mfs": 201775, "other": 201750},  # RP 2025-32 §4.26 (MFS $25 > other)
}

# Home-office simplified method — fixed safe harbor (Rev. Proc. 2013-13).
HOME_OFFICE_RATE = 5              # $5 per square foot
HOME_OFFICE_MAX_SQFT = 300       # capped at 300 sqft -> $1,500 max


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY TOPICS
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("schedule_c_business", "Schedule C — sole-proprietor profit/loss, COGS (Part III), simplified home office"),
    ("self_employment_tax", "Schedule SE — SE tax (§1401) + 1/2-SE deduction (§164(f)) -> Sch 2 L4 / Sch 1 L15"),
    ("qbi_deduction", "Form 8995 — §199A QBI deduction (simplified, below-threshold) -> 1040 L13a"),
    ("additional_medicare_tax", "Form 8959 — Additional Medicare Tax (§3101(b)(2)/§1401(b)(2)) -> Sch 2 L11 / 1040 L25c"),
]

# Existing sources to REUSE (looked up, not modified).
EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "RP_2025_32",            # §4.26 TY2026 QBI thresholds (§2.06/§4.03 already used by eic/intdiv)
    "IRS_2025_1040_FORM",    # 1040 lines 13a (QBI), 23 (other taxes), 25c (withholding)
    "IRS_2025_1040_INSTR",   # i1040gi cross-references
]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY SOURCES (with embedded excerpts) — CREATE / re-author
# Transcribed 2026-06-12 from the fetched PDFs (tts-tax-app server/.scratch/),
# requires_human_review=False (verbatim, verifiable against the on-disk copies).
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_SCHEDC_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Schedule C (Form 1040) — Profit or Loss From Business (Sole Proprietorship)",
        "citation": "Schedule C (Form 1040) 2025; f1040sc.pdf; Attachment Sequence No. 09",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f1040sc.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": "Parts I-V transcribed 2026-06-12 (server/.scratch/f1040sc_dump.txt). Real face; PER BUSINESS.",
        "topics": ["schedule_c_business"],
        "excerpts": [
            {
                "excerpt_label": "Part I Income + Part II totals (lines 1-31, verbatim line list)",
                "location_reference": "Schedule C (2025), Parts I-II",
                "excerpt_text": (
                    "1 Gross receipts or sales. 2 Returns and allowances. 3 Subtract line 2 "
                    "from line 1. 4 Cost of goods sold (from line 42). 5 Gross profit. "
                    "Subtract line 4 from line 3. 6 Other income. 7 Gross income. Add lines "
                    "5 and 6. 8-27b Expenses (8 advertising; 9 car and truck; 10 commissions "
                    "and fees; 11 contract labor; 12 depletion; 13 depreciation and section "
                    "179 (not in Part III); 14 employee benefit programs; 15 insurance "
                    "(other than health); 16a mortgage interest, 16b other interest; 17 legal "
                    "and professional; 18 office; 19 pension and profit-sharing; 20a rent "
                    "vehicles/machinery/equipment, 20b rent other business property; 21 "
                    "repairs and maintenance; 22 supplies; 23 taxes and licenses; 24a travel, "
                    "24b deductible meals; 25 utilities; 26 wages; 27a energy-efficient "
                    "commercial bldgs (Form 7205), 27b other expenses (from line 48)). 28 "
                    "Total expenses before business use of home. Add lines 8 through 27b. 29 "
                    "Tentative profit or (loss). Subtract line 28 from line 7. 30 Expenses "
                    "for business use of your home (Form 8829 unless using the simplified "
                    "method). 31 Net profit or (loss). Subtract line 30 from line 29. If a "
                    "profit, enter on both Schedule 1 (Form 1040), line 3, and on Schedule "
                    "SE, line 2. If a loss, you must go to line 32. 32a All investment is at "
                    "risk. 32b Some investment is not at risk (attach Form 6198)."
                ),
                "summary_text": (
                    "L3=L1-L2; L5=L3-L4(COGS); L7=L5+L6; L28=sum(8..27b); L29=L7-L28; "
                    "L30=home office; L31=L29-L30 -> Sch 1 L3 + Sch SE L2. L32b -> Form 6198 "
                    "(RED-defer). L13 depreciation -> Form 4562 engine."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part III Cost of Goods Sold (lines 33-42, verbatim)",
                "location_reference": "Schedule C (2025), Part III",
                "excerpt_text": (
                    "33 Method(s) used to value closing inventory: a Cost; b Lower of cost "
                    "or market; c Other. 34 Was there any change in determining quantities, "
                    "costs, or valuations between opening and closing inventory? 35 Inventory "
                    "at beginning of year. 36 Purchases less cost of items withdrawn for "
                    "personal use. 37 Cost of labor. Do not include any amounts paid to "
                    "yourself. 38 Materials and supplies. 39 Other costs. 40 Add lines 35 "
                    "through 39. 41 Inventory at end of year. 42 Cost of goods sold. Subtract "
                    "line 41 from line 40. Enter the result here and on line 4."
                ),
                "summary_text": (
                    "L40 = sum(35..39); L42 = L40 - L41 (ending inventory) -> line 4. "
                    "Method (cost/LCM/other) + the inventory-change question are metadata."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Line 30 simplified-method home office (verbatim) + Simplified Method Worksheet",
                "location_reference": "Schedule C (2025) line 30; i1040sc Simplified Method Worksheet",
                "excerpt_text": (
                    "Line 30: Expenses for business use of your home. Attach Form 8829 unless "
                    "using the simplified method. Simplified method filers only: Enter the "
                    "total square footage of (a) your home and (b) the part of your home used "
                    "for business. Use the Simplified Method Worksheet in the instructions to "
                    "figure the amount to enter on line 30. [i1040sc Simplified Method "
                    "Worksheet: allowable square footage (not more than 300) x $5.00; the "
                    "deduction may not exceed the gross income derived from the business use "
                    "(line 29 tentative profit); the excess is NOT carried over under the "
                    "simplified method.]"
                ),
                "summary_text": (
                    "Simplified line 30 = min(business sqft, 300) x $5, further capped at "
                    "max(0, line 29 tentative profit). No carryover of the excess. Form 8829 "
                    "(actual-expense %) is RED-defer."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_SCHEDC_INSTR",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Schedule C (Form 1040)",
        "citation": "i1040sc (2025)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i1040sc.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": False,
        "trust_score": 9.00,
        "requires_human_review": False,
        "notes": "Home-office simplified worksheet + line 13 depreciation routing + statutory-employee box, 2026-06-12.",
        "topics": ["schedule_c_business"],
        "excerpts": [
            {
                "excerpt_label": "Statutory employee + at-risk (line 1 box / line 32, verbatim)",
                "location_reference": "i1040sc (2025), Line 1 / Line 32",
                "excerpt_text": (
                    "Statutory employees: if you received a Form W-2 and the 'Statutory "
                    "employee' box (box 13) was checked, report your income and expenses on "
                    "Schedule C; statutory-employee income is NOT subject to self-employment "
                    "tax. At-risk (line 32): if you have a loss, you must check 32a (all "
                    "investment at risk) or 32b (some investment not at risk). If 32b, you "
                    "must attach Form 6198 and your loss may be limited."
                ),
                "summary_text": (
                    "Statutory employee (W-2 box 13) -> Schedule C WITHOUT Schedule SE "
                    "(RED-defer this sprint). Line 32b -> Form 6198 at-risk limitation "
                    "(RED-defer)."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_SCHEDSE_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Schedule SE (Form 1040) — Self-Employment Tax",
        "citation": "Schedule SE (Form 1040) 2025; f1040sse.pdf; Attachment Sequence No. 17",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f1040sse.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": "Part I standard method transcribed 2026-06-12 (server/.scratch/f1040sse_dump.txt). PER PROPRIETOR.",
        "topics": ["self_employment_tax"],
        "excerpts": [
            {
                "excerpt_label": "Part I standard method (lines 1a-13, verbatim)",
                "location_reference": "Schedule SE (2025), Part I",
                "excerpt_text": (
                    "1a Net farm profit or (loss) from Schedule F, line 34, and farm "
                    "partnerships, Schedule K-1 (Form 1065), box 14, code A. 1b Conservation "
                    "Reserve Program payments (negative). 2 Net profit or (loss) from "
                    "Schedule C, line 31; and Schedule K-1 (Form 1065), box 14, code A (other "
                    "than farming). 3 Combine lines 1a, 1b, and 2. 4a If line 3 is more than "
                    "zero, multiply line 3 by 92.35% (0.9235); otherwise, enter amount from "
                    "line 3. 4b Optional methods (lines 15 and 17). 4c Combine lines 4a and "
                    "4b. If less than $400, stop; you don't owe self-employment tax. 5a "
                    "Church employee income; 5b multiply 5a by 92.35%. 6 Add lines 4c and 5b. "
                    "7 Maximum amount subject to social security tax = $176,100 (2025). 8a "
                    "Total social security wages and tips (boxes 3 and 7 on Form(s) W-2) and "
                    "RRTA tier 1; if $176,100 or more, skip 8b-10 and go to 11. 8b unreported "
                    "tips (Form 4137 line 10). 8c wages (Form 8919 line 10). 8d add 8a-8c. 9 "
                    "Subtract line 8d from line 7. If zero or less, enter -0- and go to 11. "
                    "10 Multiply the smaller of line 6 or line 9 by 12.4% (0.124). 11 "
                    "Multiply line 6 by 2.9% (0.029). 12 Self-employment tax. Add lines 10 "
                    "and 11. Enter here and on Schedule 2 (Form 1040), line 4. 13 Deduction "
                    "for one-half of self-employment tax. Multiply line 12 by 50% (0.50). "
                    "Enter here and on Schedule 1 (Form 1040), line 15."
                ),
                "summary_text": (
                    "L2 <- Sch C L31 (sum the proprietor's businesses); L4a = L3 x 0.9235 if "
                    "L3>0; L4c < $400 -> stop. L7 wage base year-keyed; L8d W-2 SS wages "
                    "consume it; L9 = L7-L8d; L10 = min(L6,L9) x 12.4%; L11 = L6 x 2.9%; "
                    "L12 = L10+L11 -> Sch 2 L4; L13 = L12 x 50% -> Sch 1 L15. Part II optional "
                    "+ church (5a/5b) = RED-defer."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_8995_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Form 8995 — Qualified Business Income Deduction Simplified Computation",
        "citation": "Form 8995 (2025); f8995.pdf; Attachment Sequence No. 55",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f8995.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": (
            "The REAL 17-line face transcribed 2026-06-12 (server/.scratch/f8995_dump.txt). "
            "Replaces the wrong early-draft RS stub (Line 2 'from K-1', 8-line map). "
            "Use only if taxable income before QBI <= $197,300 ($394,600 MFJ) (2025)."
        ),
        "topics": ["qbi_deduction"],
        "excerpts": [
            {
                "excerpt_label": "Lines 1-17 (the real 17-line face, verbatim)",
                "location_reference": "Form 8995 (2025), lines 1-17",
                "excerpt_text": (
                    "Use this form if your taxable income, before your qualified business "
                    "income deduction, is at or below $197,300 ($394,600 if married filing "
                    "jointly). 1 (i-v) Trade, business, or aggregation name / TIN / qualified "
                    "business income or (loss). 2 Total qualified business income or (loss). "
                    "Combine lines 1i through 1v, column (c). 3 Qualified business net (loss) "
                    "carryforward from the prior year. 4 Total QBI. Combine lines 2 and 3. If "
                    "zero or less, enter -0-. 5 Qualified business income component. Multiply "
                    "line 4 by 20% (0.20). 6 Qualified REIT dividends and publicly traded "
                    "partnership (PTP) income or (loss). 7 Qualified REIT dividends and "
                    "qualified PTP (loss) carryforward from the prior year. 8 Total qualified "
                    "REIT dividends and PTP income. Combine lines 6 and 7. If zero or less, "
                    "enter -0-. 9 REIT and PTP component. Multiply line 8 by 20% (0.20). 10 "
                    "QBI deduction before the income limitation. Add lines 5 and 9. 11 "
                    "Taxable income before qualified business income deduction. 12 Net "
                    "capital gain (qualified dividends + net capital gain). 13 Subtract line "
                    "12 from line 11. If zero or less, enter -0-. 14 Income limitation. "
                    "Multiply line 13 by 20% (0.20). 15 Qualified business income deduction. "
                    "Enter the smaller of line 10 or line 14. Also enter this amount on the "
                    "applicable line of your return. 16 Total qualified business (loss) "
                    "carryforward (combine lines 2 and 3; if greater than zero, enter -0-). "
                    "17 Total qualified REIT dividends and PTP (loss) carryforward (combine "
                    "lines 6 and 7; if greater than zero, enter -0-)."
                ),
                "summary_text": (
                    "L4=L2+L3 (>=0); L5=L4 x 20%; L8=L6+L7 (>=0); L9=L8 x 20%; L10=L5+L9; "
                    "L13=L11-L12 (>=0); L14=L13 x 20%; L15=min(L10,L14) -> 1040 L13a; "
                    "L16/L17 carryforward out. Above threshold -> Form 8995-A (RED-defer)."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_8995_INSTR",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Form 8995",
        "citation": "i8995 (2025)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i8995.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": False,
        "trust_score": 9.00,
        "requires_human_review": False,
        "notes": "RE-AUTHORED over the stub source. QBI-reduction rule + line 11/12 sourcing transcribed 2026-06-12.",
        "topics": ["qbi_deduction"],
        "excerpts": [
            {
                "excerpt_label": "QBI per business reduced by 1/2-SE-tax / SEHI / SE-retirement (verbatim guidance)",
                "location_reference": "i8995 (2025), 'Determining Your Qualified Business Income'",
                "excerpt_text": (
                    "Your qualified business income for a qualified trade or business "
                    "includes income effectively connected with the conduct of the trade or "
                    "business and reduced by the deductions attributable to it, including the "
                    "deductible part of self-employment tax, self-employed health insurance, "
                    "and self-employed retirement (SEP, SIMPLE, and qualified plans) "
                    "deductions to the extent they are attributable to the trade or business. "
                    "Line 11: enter your taxable income figured before any qualified business "
                    "income deduction (Form 1040 line 11 minus line 12). Line 12: enter your "
                    "net capital gain. Net capital gain means qualified dividends plus the "
                    "excess of net long-term capital gain over net short-term capital loss."
                ),
                "summary_text": (
                    "QBI (per business) = Sch C net profit - attributable 1/2-SE-tax (Sch 1 "
                    "L15) - SEHI (Sch 1 L17) - SE-retirement (Sch 1 L16). L11 = 1040 L11 - "
                    "L12. L12 = qualified dividends (1040 L3a) + net capital gain (Schedule D; "
                    "v1 = cap-gain distributions until Sch D is built)."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_8959_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Form 8959 — Additional Medicare Tax",
        "citation": "Form 8959 (2025); f8959.pdf; Attachment Sequence No. 71",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f8959.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": "Parts I-V transcribed 2026-06-12 (server/.scratch/f8959_dump.txt). Part III RRTA = RED-defer.",
        "topics": ["additional_medicare_tax"],
        "excerpts": [
            {
                "excerpt_label": "Parts I/II/IV/V (lines 1-24, verbatim) — the threshold-reduced-by-wages nuance",
                "location_reference": "Form 8959 (2025), Parts I-V",
                "excerpt_text": (
                    "Part I Medicare wages: 1 Medicare wages and tips (W-2 box 5). 2 "
                    "unreported tips (Form 4137 line 6). 3 wages (Form 8919 line 6). 4 add "
                    "lines 1-3. 5 filing-status threshold ($250,000 MFJ / $125,000 MFS / "
                    "$200,000 single, HOH, or QSS). 6 subtract line 5 from line 4 (>=0). 7 "
                    "Additional Medicare Tax on Medicare wages = line 6 x 0.9%. Part II SE "
                    "income: 8 self-employment income from Schedule SE, Part I, line 6 (loss "
                    "-> 0). 9 filing-status threshold (same table). 10 enter the amount from "
                    "line 4. 11 subtract line 10 from line 9 (>=0). 12 subtract line 11 from "
                    "line 8 (>=0). 13 Additional Medicare Tax on SE income = line 12 x 0.9%. "
                    "Part III RRTA (lines 14-17). Part IV: 18 add lines 7, 13, and 17. Also "
                    "include on Schedule 2 (Form 1040), line 11. Part V Withholding "
                    "Reconciliation: 19 Medicare tax withheld (W-2 box 6). 20 amount from "
                    "line 1. 21 multiply line 20 by 1.45%. 22 subtract line 21 from line 19 "
                    "(>=0). 23 Additional Medicare Tax withholding on RRTA. 24 add lines 22 "
                    "and 23. Also include with federal income tax withholding on Form 1040 "
                    "line 25c."
                ),
                "summary_text": (
                    "Part I: L7 = max(0, L4 - threshold) x 0.9%. Part II: the threshold is "
                    "REDUCED BY Medicare wages -> L11 = max(0, threshold - L4); L12 = max(0, "
                    "L8 - L11); L13 = L12 x 0.9%. L18 = L7+L13+L17 -> Sch 2 L11. L24 = "
                    "L22+L23 -> 1040 L25c. Part III RRTA = RED-defer."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_TOPIC751_SE",
        "source_type": "official_publication",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2026,
        "title": "IRS Tax Topic 751 — Social Security and Medicare Withholding Rates (+ SSA wage base)",
        "citation": "IRS Topic No. 751; SSA Fact Sheet 2026 (wage base $184,500)",
        "issuer": "IRS / SSA",
        "official_url": "https://www.irs.gov/taxtopics/tc751",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": False,
        "trust_score": 9.00,
        "requires_human_review": False,
        "notes": "SS/Medicare rates + the 2026 SS wage base ($184,500, up from $176,100), 2026-06-12.",
        "topics": ["self_employment_tax", "additional_medicare_tax"],
        "excerpts": [
            {
                "excerpt_label": "Rates + 2026 SS wage base (verbatim)",
                "location_reference": "IRS Topic 751; SSA 2026",
                "excerpt_text": (
                    "Social security: employee/employer 6.2% each (12.4% self-employment). "
                    "Medicare: employee/employer 1.45% each (2.9% self-employment), with no "
                    "wage base limit. Additional Medicare Tax: 0.9% on wages/compensation/SE "
                    "income above the filing-status threshold. The social security wage base "
                    "is $176,100 for 2025 and $184,500 for 2026."
                ),
                "summary_text": (
                    "SS 12.4% (SE) capped at the wage base ($176,100 2025 / $184,500 2026); "
                    "Medicare 2.9% (SE) uncapped; Additional Medicare 0.9% over threshold."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
]


# ═══════════════════════════════════════════════════════════════════════════
# NEW EXCERPTS ON EXISTING SOURCES  (source_code, excerpt_dict)
# ═══════════════════════════════════════════════════════════════════════════

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = [
    (
        "RP_2025_32",
        {
            "excerpt_label": "§4.26 Qualified Business Income (TY2026 §199A thresholds, verbatim)",
            "location_reference": "Rev. Proc. 2025-32, §4.26 'Qualified Business Income'",
            "excerpt_text": (
                "For taxable years beginning in 2026, under §199A(e)(2) the threshold "
                "amount is $403,500 for married individuals filing jointly, $201,775 for "
                "married individuals filing separately, and $201,750 for all other "
                "returns. [The simplified Form 8995 may be used at or below the threshold; "
                "above it, Form 8995-A applies the W-2/UBIA and SSTB limitations.]"
            ),
            "summary_text": (
                "TY2026 §199A thresholds: $403,500 MFJ / $201,775 MFS / $201,750 other. "
                "WALK ITEM: MFS is $25 ABOVE 'other' (RP rounding artifact). 2025 was "
                "$394,600 MFJ / $197,300 all-other (i8995)."
            ),
            "is_key_excerpt": True,
        },
    ),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 1 — SCHEDULE_C (Profit or Loss From Business)
# ═══════════════════════════════════════════════════════════════════════════

SCHEDC_IDENTITY = {
    "form_number": "SCHEDULE_C",
    "form_title": "Schedule C (Form 1040) — Profit or Loss From Business (Sole Proprietorship) (TY2025)",
    "notes": (
        "Sprint Topic 8 (NEXT-UP #1). Real IRS face, PER BUSINESS (multiple Schedule "
        "C per return; FK model — Decision 3). Part I income, Part II expenses, Part "
        "III COGS (Decision 1), the line-30 simplified home-office deduction "
        "(Decision 2), and the line-32 at-risk routing. Net profit (line 31) feeds "
        "Schedule 1 line 3 (sum all businesses) AND Schedule SE line 2 (sum per "
        "proprietor). Line 13 depreciation reuses the mature 4562 engine. Form 8829 "
        "actual-expense home office, Form 6198 at-risk, statutory-employee Schedule "
        "C = RED-defer."
    ),
}

SCHEDC_FACTS: list[dict] = [
    # ── Header / identity (metadata; e-file structured fields) ──
    {"fact_key": "sc_proprietor", "label": "Proprietor (taxpayer or spouse) — which person owns this Schedule C",
     "data_type": "string", "sort_order": 1,
     "notes": "PER BUSINESS. taxpayer|spouse. Decision 3: SE aggregates per proprietor; each business its own Sch C."},
    {"fact_key": "sc_business_name", "label": "Line C — Business name (blank if none)", "data_type": "string", "sort_order": 2,
     "notes": "PER BUSINESS. Metadata."},
    {"fact_key": "sc_principal_business", "label": "Line A — Principal business or profession", "data_type": "string", "sort_order": 3,
     "notes": "PER BUSINESS. Metadata."},
    {"fact_key": "sc_business_code", "label": "Line B — Principal business code (from instructions)", "data_type": "string", "sort_order": 4,
     "notes": "PER BUSINESS. NAICS-style code; metadata (e-file structured)."},
    {"fact_key": "sc_ein", "label": "Line D — Employer ID number (EIN), if any", "data_type": "string", "sort_order": 5,
     "notes": "PER BUSINESS. Format NN-NNNNNNN or blank (MeF rule)."},
    {"fact_key": "sc_accounting_method", "label": "Line F — Accounting method (cash / accrual / other)", "data_type": "string", "sort_order": 6,
     "notes": "PER BUSINESS. cash|accrual|other. 'Other' -> attach explanation (metadata/diagnostic)."},
    {"fact_key": "sc_material_participation", "label": "Line G — Materially participated in the business in 2025", "data_type": "boolean", "sort_order": 7,
     "notes": "PER BUSINESS. No -> passive-loss limits may apply (RED-defer 6198/8582). Metadata this sprint."},
    {"fact_key": "sc_started_acquired", "label": "Line H — Started or acquired this business during 2025", "data_type": "boolean", "sort_order": 8,
     "notes": "PER BUSINESS. Metadata (start-up cost amortization is a separate concern)."},
    {"fact_key": "sc_made_1099_payments", "label": "Line I — Made payments requiring Form 1099", "data_type": "boolean", "sort_order": 9,
     "notes": "PER BUSINESS. Metadata; pairs with line J."},
    {"fact_key": "sc_filed_1099", "label": "Line J — Filed (or will file) required Form(s) 1099", "data_type": "boolean", "sort_order": 10,
     "notes": "PER BUSINESS. Metadata."},
    {"fact_key": "sc_statutory_employee", "label": "Statutory employee (W-2 box 13 checked) — Schedule C WITHOUT Schedule SE",
     "data_type": "boolean", "sort_order": 11,
     "notes": "PER BUSINESS. True -> D_SC_001 RED-defer (statutory-employee income not subject to SE tax; v1 unsupported)."},
    # ── Income / expense inputs that are not plain money lines ──
    {"fact_key": "sc_home_office_sqft", "label": "Line 30 — Square footage used for business (simplified method)",
     "data_type": "integer", "default_value": "0", "sort_order": 20,
     "notes": ("PER BUSINESS. Decision 2: simplified deduction = min(sqft, 300) x $5, capped at line 29. "
               ">300 -> capped (D_SC_004). Form 8829 actual-expense = RED-defer.")},
    {"fact_key": "sc_total_home_sqft", "label": "Line 30(a) — Total square footage of the home", "data_type": "integer", "default_value": "0", "sort_order": 21,
     "notes": "PER BUSINESS. Metadata (the (a) box); not used by the simplified computation."},
    {"fact_key": "sc_use_simplified_home_office", "label": "Use the simplified home-office method (vs Form 8829)", "data_type": "boolean", "sort_order": 22,
     "notes": "PER BUSINESS. v1 supports the simplified method only; Form 8829 selection -> RED-defer (D_SC_007)."},
    {"fact_key": "sc_all_at_risk", "label": "Line 32a — All investment is at risk", "data_type": "boolean", "sort_order": 23,
     "notes": "PER BUSINESS. On a loss, exactly one of 32a/32b. 32a -> loss allowed in full (v1 assumes all at risk)."},
    {"fact_key": "sc_some_not_at_risk", "label": "Line 32b — Some investment is not at risk", "data_type": "boolean", "sort_order": 24,
     "notes": "PER BUSINESS. True -> D_SC_002 RED-defer (attach Form 6198; loss may be limited; v1 unsupported)."},
    {"fact_key": "sc_inventory_method", "label": "Line 33 — Closing-inventory valuation method", "data_type": "string", "sort_order": 25,
     "notes": "PER BUSINESS. cost|lcm|other. 'Other' -> attach explanation. Metadata/diagnostic."},
    {"fact_key": "sc_inventory_change", "label": "Line 34 — Change in determining quantities/costs/valuations", "data_type": "boolean", "sort_order": 26,
     "notes": "PER BUSINESS. True -> attach explanation (metadata/diagnostic)."},
    {"fact_key": "sc_sehi_amount", "label": "Self-employed health insurance premiums (-> Schedule 1 line 17, limited)",
     "data_type": "decimal", "default_value": "0", "sort_order": 27,
     "notes": ("PER PROPRIETOR. SEHI deduction -> Sch 1 L17, LIMITED to net SE profit (this business / proprietor). "
               "SEHI<->PTC circular = RED-defer until Form 8962. Lives with Schedule C but feeds Schedule 1.")},
    {"fact_key": "sc_se_retirement_amount", "label": "Self-employed retirement contributions (SEP/SIMPLE/qualified; -> Schedule 1 line 16)",
     "data_type": "decimal", "default_value": "0", "sort_order": 28,
     "notes": "PER PROPRIETOR. Reduces QBI for this business (i8995). v1 preparer-entered -> Sch 1 L16 (direct-entry feeder)."},
    # ── Output ──
    {"fact_key": "sc_net_profit_l31", "label": "Line 31 — Net profit or (loss) (output -> Sch 1 L3 + Sch SE L2)",
     "data_type": "decimal", "sort_order": 40,
     "notes": "OUTPUT. = line 29 - line 30. Profit -> Sch 1 L3 + Sch SE L2; loss -> go to line 32 (at-risk)."},
    {"fact_key": "sc_cogs_l42", "label": "Line 42 — Cost of goods sold (output -> line 4)", "data_type": "decimal", "sort_order": 41,
     "notes": "OUTPUT. = line 40 - line 41 (Part III). Feeds line 4."},
    # ── Constants (traceability) ──
    {"fact_key": "sc_home_office_rate", "label": "Home-office simplified rate ($/sqft) — fixed safe harbor", "data_type": "decimal", "sort_order": 50,
     "notes": "CONSTANT $5/sqft (Rev. Proc. 2013-13, fixed — NOT indexed). Same both years."},
    {"fact_key": "sc_home_office_max_sqft", "label": "Home-office simplified max square footage", "data_type": "integer", "sort_order": 51,
     "notes": "CONSTANT 300 sqft -> $1,500 max (Rev. Proc. 2013-13). Same both years."},
]

SCHEDC_RULES: list[dict] = [
    {"rule_id": "R-SC-GROSSPROFIT", "title": "Lines 3/5/7 — gross income", "rule_type": "calculation", "precedence": 1, "sort_order": 1,
     "formula": "L3 = L1 - L2; L4 = L42 (COGS); L5 = L3 - L4; L7 = L5 + L6.",
     "inputs": [], "outputs": ["3", "5", "7"],
     "description": "PER BUSINESS. Schedule C Part I gross-income chain. L4 sourced from Part III line 42 (R-SC-COGS)."},
    {"rule_id": "R-SC-COGS", "title": "Part III lines 40/42 — cost of goods sold (Decision 1)", "rule_type": "calculation", "precedence": 2, "sort_order": 2,
     "formula": "L40 = L35 + L36 + L37 + L38 + L39; L42 = L40 - L41 (ending inventory). L42 -> line 4.",
     "inputs": [], "outputs": ["40", "42"],
     "description": ("PER BUSINESS. Decision 1: full COGS. Negative COGS or ending inventory > available (L41 > L40) "
                     "-> D_SC_003. Method/change questions are metadata.")},
    {"rule_id": "R-SC-DEPR", "title": "Line 13 — depreciation and §179 (4562 engine reuse)", "rule_type": "routing", "precedence": 3, "sort_order": 3,
     "formula": "L13 = depreciation + §179 from the 4562 engine for this business's assets (carried/YELLOW).",
     "inputs": [], "outputs": ["13"],
     "description": ("PER BUSINESS. Reuse depreciation_engine.py (business-entity 4562 path). §179 limited to business "
                     "income. Schedule C assets attach to the Schedule C. Build-leg wiring, not re-derived here.")},
    {"rule_id": "R-SC-EXPENSES", "title": "Line 28 — total expenses", "rule_type": "calculation", "precedence": 4, "sort_order": 4,
     "formula": "L28 = sum(L8, L9, L10, L11, L12, L13, L14, L15, L16a, L16b, L17, L18, L19, L20a, L20b, L21, L22, L23, L24a, L24b, L25, L26, L27a, L27b).",
     "inputs": [], "outputs": ["28"],
     "description": "PER BUSINESS. Total expenses BEFORE business use of home (line 30 is added separately). L27b <- Part V line 48."},
    {"rule_id": "R-SC-TENTATIVE", "title": "Line 29 — tentative profit/(loss)", "rule_type": "calculation", "precedence": 5, "sort_order": 5,
     "formula": "L29 = L7 - L28. (May be negative.)",
     "inputs": [], "outputs": ["29"],
     "description": "PER BUSINESS. The gross-income limitation base for the simplified home-office deduction (R-SC-HOMEOFFICE)."},
    {"rule_id": "R-SC-HOMEOFFICE", "title": "Line 30 — simplified home-office deduction (Decision 2)", "rule_type": "calculation", "precedence": 6, "sort_order": 6,
     "formula": ("If sc_use_simplified_home_office: L30 = min( min(sc_home_office_sqft, 300) x $5, max(0, L29) ). "
                 "Else (Form 8829) = RED-defer (D_SC_007)."),
     "inputs": ["sc_home_office_sqft", "sc_use_simplified_home_office", "sc_home_office_rate", "sc_home_office_max_sqft"],
     "outputs": ["30"],
     "description": ("PER BUSINESS. Decision 2: simplified safe harbor. 300-sqft cap (D_SC_004 when sqft>300); "
                     "gross-income limitation = max(0, line 29 tentative profit) — the deduction cannot create/"
                     "increase a loss (D_SC_005). NO carryover of the disallowed excess under the simplified method.")},
    {"rule_id": "R-SC-NETPROFIT", "title": "Line 31 — net profit/(loss) -> Sch 1 L3 + Sch SE L2", "rule_type": "calculation", "precedence": 7, "sort_order": 7,
     "formula": "L31 = L29 - L30 -> sc_net_profit_l31. Profit -> Schedule 1 line 3 AND Schedule SE line 2; loss -> go to line 32.",
     "inputs": [], "outputs": ["31"],
     "description": ("PER BUSINESS. The topic's primary cross-form output. Schedule 1 line 3 = SUM of all businesses' "
                     "L31; Schedule SE line 2 = SUM per proprietor. Statutory-employee income is NOT carried to "
                     "Schedule SE (D_SC_001).")},
    {"rule_id": "R-SC-ATRISK", "title": "Line 32 — at-risk routing (RED-defer Form 6198)", "rule_type": "routing", "precedence": 8, "sort_order": 8,
     "formula": "If L31 < 0: require 32a XOR 32b. 32a -> loss allowed (v1 assumes all at risk). 32b -> D_SC_002 RED-defer (Form 6198).",
     "inputs": ["sc_all_at_risk", "sc_some_not_at_risk"], "outputs": ["32a", "32b"],
     "description": "PER BUSINESS. v1 supports the all-at-risk case only; 32b (Form 6198 at-risk limitation) is RED-defer."},
    {"rule_id": "R-SC-SEHI", "title": "Self-employed health insurance -> Schedule 1 line 17 (limited)", "rule_type": "calculation", "precedence": 9, "sort_order": 9,
     "formula": "Sch 1 L17 = min(sc_sehi_amount summed per proprietor, net SE profit of that proprietor). SEHI<->PTC circular = RED-defer.",
     "inputs": ["sc_sehi_amount"], "outputs": [],
     "description": ("PER PROPRIETOR. SEHI deduction limited to net SE earnings from the trade/business. Feeds Schedule "
                     "1 line 17 (computed feeder). The §162(l)/§36B circular interaction is RED-deferred until Form 8962.")},
]

SCHEDC_LINES: list[dict] = [
    # Part I
    {"line_number": "1", "description": "Gross receipts or sales", "line_type": "input"},
    {"line_number": "2", "description": "Returns and allowances", "line_type": "input"},
    {"line_number": "3", "description": "Subtract line 2 from line 1", "line_type": "calculated"},
    {"line_number": "4", "description": "Cost of goods sold (from line 42)", "line_type": "calculated"},
    {"line_number": "5", "description": "Gross profit. Subtract line 4 from line 3", "line_type": "calculated"},
    {"line_number": "6", "description": "Other income (incl. fuel tax credit/refund)", "line_type": "input"},
    {"line_number": "7", "description": "Gross income. Add lines 5 and 6", "line_type": "subtotal"},
    # Part II
    {"line_number": "8", "description": "Advertising", "line_type": "input"},
    {"line_number": "9", "description": "Car and truck expenses", "line_type": "input"},
    {"line_number": "10", "description": "Commissions and fees", "line_type": "input"},
    {"line_number": "11", "description": "Contract labor", "line_type": "input"},
    {"line_number": "12", "description": "Depletion", "line_type": "input"},
    {"line_number": "13", "description": "Depreciation and section 179 (not in Part III) — from Form 4562", "line_type": "calculated"},
    {"line_number": "14", "description": "Employee benefit programs", "line_type": "input"},
    {"line_number": "15", "description": "Insurance (other than health)", "line_type": "input"},
    {"line_number": "16a", "description": "Interest — mortgage (paid to banks, etc.)", "line_type": "input"},
    {"line_number": "16b", "description": "Interest — other", "line_type": "input"},
    {"line_number": "17", "description": "Legal and professional services", "line_type": "input"},
    {"line_number": "18", "description": "Office expense", "line_type": "input"},
    {"line_number": "19", "description": "Pension and profit-sharing plans", "line_type": "input"},
    {"line_number": "20a", "description": "Rent or lease — vehicles, machinery, and equipment", "line_type": "input"},
    {"line_number": "20b", "description": "Rent or lease — other business property", "line_type": "input"},
    {"line_number": "21", "description": "Repairs and maintenance", "line_type": "input"},
    {"line_number": "22", "description": "Supplies (not included in Part III)", "line_type": "input"},
    {"line_number": "23", "description": "Taxes and licenses", "line_type": "input"},
    {"line_number": "24a", "description": "Travel", "line_type": "input"},
    {"line_number": "24b", "description": "Deductible meals", "line_type": "input"},
    {"line_number": "25", "description": "Utilities", "line_type": "input"},
    {"line_number": "26", "description": "Wages (less employment credits)", "line_type": "input"},
    {"line_number": "27a", "description": "Energy-efficient commercial bldgs deduction (Form 7205)", "line_type": "input"},
    {"line_number": "27b", "description": "Other expenses (from line 48)", "line_type": "calculated"},
    {"line_number": "28", "description": "Total expenses before business use of home. Add lines 8 through 27b", "line_type": "subtotal"},
    {"line_number": "29", "description": "Tentative profit or (loss). Subtract line 28 from line 7", "line_type": "subtotal"},
    {"line_number": "30", "description": "Expenses for business use of home (simplified method inline)", "line_type": "calculated"},
    {"line_number": "31", "description": "Net profit or (loss). Subtract line 30 from line 29 -> Sch 1 L3 + Sch SE L2", "line_type": "total"},
    {"line_number": "32a", "description": "All investment is at risk", "line_type": "input"},
    {"line_number": "32b", "description": "Some investment is not at risk (attach Form 6198 — RED-defer)", "line_type": "input"},
    # Part III COGS
    {"line_number": "33", "description": "Method used to value closing inventory (cost/LCM/other)", "line_type": "input"},
    {"line_number": "34", "description": "Change in determining quantities/costs/valuations (Y/N)", "line_type": "input"},
    {"line_number": "35", "description": "Inventory at beginning of year", "line_type": "input"},
    {"line_number": "36", "description": "Purchases less cost of items withdrawn for personal use", "line_type": "input"},
    {"line_number": "37", "description": "Cost of labor (not amounts paid to yourself)", "line_type": "input"},
    {"line_number": "38", "description": "Materials and supplies", "line_type": "input"},
    {"line_number": "39", "description": "Other costs", "line_type": "input"},
    {"line_number": "40", "description": "Add lines 35 through 39", "line_type": "subtotal"},
    {"line_number": "41", "description": "Inventory at end of year", "line_type": "input"},
    {"line_number": "42", "description": "Cost of goods sold. Subtract line 41 from line 40 -> line 4", "line_type": "total"},
    # Part IV vehicle (data-map)
    {"line_number": "43", "description": "Date vehicle placed in service (Part IV)", "line_type": "input"},
    {"line_number": "44a", "description": "Business miles (Part IV)", "line_type": "input"},
    {"line_number": "44b", "description": "Commuting miles (Part IV)", "line_type": "input"},
    {"line_number": "44c", "description": "Other miles (Part IV)", "line_type": "input"},
    {"line_number": "45", "description": "Vehicle available for personal use off-duty (Part IV)", "line_type": "input"},
    {"line_number": "46", "description": "Another vehicle available for personal use (Part IV)", "line_type": "input"},
    {"line_number": "47a", "description": "Evidence to support the deduction (Part IV)", "line_type": "input"},
    {"line_number": "47b", "description": "Is the evidence written (Part IV)", "line_type": "input"},
    # Part V
    {"line_number": "48", "description": "Total other expenses (Part V) -> line 27b", "line_type": "subtotal"},
]

SCHEDC_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_SC_001", "title": "Statutory employee — Schedule C without Schedule SE not supported", "severity": "error",
     "condition": "sc_statutory_employee is True",
     "message": ("Not supported — prepare manually: a statutory employee (Form W-2 box 13) reports income on "
                 "Schedule C but it is NOT subject to self-employment tax. The Schedule C -> Schedule SE coupling "
                 "this sprint assumes SE-taxable net profit; the statutory-employee path is not modeled."),
     "notes": "RED-defer. Statutory-employee income skips Schedule SE; v1 does not split it out."},
    {"diagnostic_id": "D_SC_002", "title": "Some investment not at risk (line 32b) — Form 6198 not supported", "severity": "error",
     "condition": "sc_some_not_at_risk is True (or a loss with 32b checked)",
     "message": ("Not supported — prepare manually: you indicated some investment is not at risk (line 32b), which "
                 "requires Form 6198 and may limit your loss. The at-risk limitation is not modeled this sprint; "
                 "v1 supports only the all-at-risk case (line 32a)."),
     "notes": "RED-defer Form 6198 (brief standing RED-defer)."},
    {"diagnostic_id": "D_SC_003", "title": "Cost of goods sold invalid (negative, or ending inventory exceeds available)", "severity": "error",
     "condition": "line 42 < 0 OR line 41 (ending inventory) > line 40 (beginning + purchases + costs)",
     "message": ("Cost of goods sold is invalid: ending inventory (line 41) cannot exceed the goods available "
                 "(line 40 = beginning inventory + purchases + costs), and COGS (line 42) cannot be negative. "
                 "Check the Part III entries."),
     "notes": "No-silent-gap guard on the COGS computation."},
    {"diagnostic_id": "D_SC_004", "title": "Home-office square footage exceeds 300 — capped", "severity": "info",
     "condition": "sc_home_office_sqft > 300",
     "message": ("The simplified home-office method caps the deductible area at 300 square feet ($1,500). Square "
                 "footage above 300 is ignored; use Form 8829 (actual-expense method) if your home-office costs "
                 "exceed the safe harbor."),
     "notes": "Decision 2. The cap is applied automatically; informational."},
    {"diagnostic_id": "D_SC_005", "title": "Home-office deduction limited by tentative profit (gross-income limitation)", "severity": "info",
     "condition": "min(sqft,300) x $5 > max(0, line 29 tentative profit)",
     "message": ("The simplified home-office deduction is limited to your tentative profit (line 29) and cannot "
                 "create or increase a loss. The disallowed excess is NOT carried over under the simplified "
                 "method (unlike Form 8829)."),
     "notes": "Decision 2 gross-income limitation. No-silent-gap (the preparer sees why line 30 < the raw $5xsqft)."},
    {"diagnostic_id": "D_SC_006", "title": "Net loss on Schedule C — verify at-risk and passive-activity rules", "severity": "info",
     "condition": "line 31 < 0",
     "message": ("This Schedule C shows a net loss. Confirm the at-risk box (line 32a/32b) and consider whether "
                 "passive-activity rules limit the loss (material participation, line G). v1 allows the full loss "
                 "only when all investment is at risk and the activity is non-passive."),
     "notes": "Routes the preparer to line 32; passive-loss limits (8582) are RED-defer."},
    {"diagnostic_id": "D_SC_007", "title": "Form 8829 (actual-expense home office) selected — not supported", "severity": "error",
     "condition": "NOT sc_use_simplified_home_office AND a home-office deduction is claimed",
     "message": ("Not supported — prepare manually: the actual-expense home-office method (Form 8829 — percentage "
                 "of home, gross-income limitation, carryover) is not built this sprint. Use the simplified method "
                 "($5/sqft, up to 300 sqft) or compute Form 8829 manually."),
     "notes": "RED-defer Form 8829 (Decision 2)."},
]

SCHEDC_SCENARIOS: list[dict] = [
    {"scenario_name": "SC-T1 — service business profit (no COGS, no home office)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "line_1": 120000, "line_2": 0, "line_4": 0, "line_6": 0,
                "line_28": 45000, "sc_home_office_sqft": 0},
     "expected_outputs": {"line_7": 120000, "line_29": 75000, "line_30": 0, "line_31": 75000},
     "notes": "L7=120,000; L29=120,000-45,000=75,000; no home office -> L31=75,000 -> Sch 1 L3 + Sch SE L2."},
    {"scenario_name": "SC-T2 — retail with COGS (Part III)", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"tax_year": 2025, "line_1": 200000, "line_2": 0, "line_6": 0, "line_28": 40000,
                "line_35": 30000, "line_36": 90000, "line_37": 0, "line_38": 5000, "line_39": 0, "line_41": 25000,
                "sc_home_office_sqft": 0},
     "expected_outputs": {"line_40": 125000, "line_42": 100000, "line_4": 100000, "line_5": 100000, "line_7": 100000,
                          "line_29": 60000, "line_31": 60000},
     "notes": "COGS: L40=30k+90k+5k=125k; L42=125k-25k=100k -> L4. L5=200k-100k=100k=L7; L29=100k-40k=60k=L31."},
    {"scenario_name": "SC-T3 — home office at 300-sqft cap (D_SC_004)", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"tax_year": 2025, "line_1": 80000, "line_2": 0, "line_4": 0, "line_6": 0, "line_28": 20000,
                "sc_use_simplified_home_office": True, "sc_home_office_sqft": 350},
     "expected_outputs": {"line_29": 60000, "line_30": 1500, "line_31": 58500, "D_SC_004": True},
     "notes": "sqft 350 -> capped at 300 x $5 = $1,500 (well under L29 60,000). L31=60,000-1,500=58,500."},
    {"scenario_name": "SC-T4 — home office limited by tentative profit (D_SC_005)", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"tax_year": 2025, "line_1": 22000, "line_2": 0, "line_4": 0, "line_6": 0, "line_28": 21200,
                "sc_use_simplified_home_office": True, "sc_home_office_sqft": 300},
     "expected_outputs": {"line_29": 800, "line_30": 800, "line_31": 0, "D_SC_005": True},
     "notes": "Raw simplified = 300 x $5 = $1,500, but L29 tentative profit is only 800 -> L30 capped at 800; L31=0 (no loss created)."},
    {"scenario_name": "SC-T5 — net loss -> go to line 32 (D_SC_006)", "scenario_type": "normal", "sort_order": 5,
     "inputs": {"tax_year": 2025, "line_1": 30000, "line_2": 0, "line_4": 0, "line_6": 0, "line_28": 45000,
                "sc_home_office_sqft": 0, "sc_all_at_risk": True},
     "expected_outputs": {"line_29": -15000, "line_30": 0, "line_31": -15000, "D_SC_006": True},
     "notes": "Loss -15,000; home office cannot apply (L29 < 0 -> L30=0); all at risk -> loss allowed -> Sch 1 L3 + Sch SE L2."},
    {"scenario_name": "SC-T6 — statutory employee RED (D_SC_001)", "scenario_type": "normal", "sort_order": 6,
     "inputs": {"tax_year": 2025, "sc_statutory_employee": True, "line_1": 50000, "line_28": 8000, "sc_home_office_sqft": 0},
     "expected_outputs": {"D_SC_001": True, "carries_to_schedule_se": False},
     "notes": "Statutory employee -> Schedule C computes but does NOT feed Schedule SE; RED unsupported this sprint."},
    {"scenario_name": "SC-T7 — some not at risk RED (D_SC_002)", "scenario_type": "normal", "sort_order": 7,
     "inputs": {"tax_year": 2025, "line_1": 20000, "line_28": 35000, "sc_some_not_at_risk": True, "sc_home_office_sqft": 0},
     "expected_outputs": {"line_31": -15000, "D_SC_002": True},
     "notes": "Loss with 32b checked -> Form 6198 at-risk limitation required; RED-defer (loss not auto-allowed)."},
]

SCHEDC_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-SC-GROSSPROFIT", "IRS_2025_SCHEDC_FORM", "primary", "Part I lines 1-7 (gross income chain)"),
    ("R-SC-COGS", "IRS_2025_SCHEDC_FORM", "primary", "Part III lines 33-42 (COGS)"),
    ("R-SC-DEPR", "IRS_2025_SCHEDC_INSTR", "primary", "Line 13 depreciation -> Form 4562"),
    ("R-SC-EXPENSES", "IRS_2025_SCHEDC_FORM", "primary", "Part II lines 8-28 (total expenses)"),
    ("R-SC-TENTATIVE", "IRS_2025_SCHEDC_FORM", "primary", "Line 29 tentative profit"),
    ("R-SC-HOMEOFFICE", "IRS_2025_SCHEDC_FORM", "primary", "Line 30 simplified home office"),
    ("R-SC-HOMEOFFICE", "IRS_2025_SCHEDC_INSTR", "secondary", "Simplified Method Worksheet (300 sqft / $5 / gross-income limit)"),
    ("R-SC-NETPROFIT", "IRS_2025_SCHEDC_FORM", "primary", "Line 31 -> Sch 1 L3 + Sch SE L2"),
    ("R-SC-ATRISK", "IRS_2025_SCHEDC_INSTR", "primary", "Line 32 at-risk routing (Form 6198)"),
    ("R-SC-SEHI", "IRS_2025_8995_INSTR", "secondary", "SEHI deduction (attributable to the trade/business) -> Sch 1 L17"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 2 — SCHEDULE_SE (Self-Employment Tax)
# ═══════════════════════════════════════════════════════════════════════════

SCHEDSE_IDENTITY = {
    "form_number": "SCHEDULE_SE",
    "form_title": "Schedule SE (Form 1040) — Self-Employment Tax (TY2025)",
    "notes": (
        "Sprint Topic 8. Real IRS face, PER PROPRIETOR (taxpayer and spouse each have "
        "their own Schedule SE aggregating their own Schedule C businesses + own W-2 "
        "SS wages). Part I standard method only. SE tax (line 12) -> Schedule 2 line "
        "4; 1/2-SE-tax deduction (line 13) -> Schedule 1 line 15 (already an EIC "
        "Worksheet-B + 8812 feeder). Year-keyed SS wage base (line 7). Part II "
        "optional methods + church-employee income (line 5) = RED-defer."
    ),
}

SCHEDSE_FACTS: list[dict] = [
    {"fact_key": "se_proprietor", "label": "Proprietor (taxpayer or spouse) for this Schedule SE", "data_type": "string", "sort_order": 1,
     "notes": "PER PROPRIETOR. taxpayer|spouse. Aggregates that person's Schedule C line 31 -> line 2."},
    {"fact_key": "se_net_farm_profit_l1a", "label": "Line 1a — net farm profit/(loss) (Sch F L34 / 1065 K-1 box 14 A)",
     "data_type": "decimal", "default_value": "0", "sort_order": 2,
     "notes": "PER PROPRIETOR. Schedule F (separate built form) / farm K-1. v1 may carry 0; wire if Schedule F present."},
    {"fact_key": "se_crp_payments_l1b", "label": "Line 1b — Conservation Reserve Program payments (negative)",
     "data_type": "decimal", "default_value": "0", "sort_order": 3,
     "notes": "PER PROPRIETOR. SS retirement/disability recipients only; reduces line 3. v1 metadata (farm)."},
    {"fact_key": "se_minister_4361", "label": "Part I 'A' — minister/religious-order Form 4361 filer", "data_type": "boolean", "sort_order": 4,
     "notes": "PER PROPRIETOR. Clergy/4361 special handling -> RED-defer (D_SE_003); v1 standard method only."},
    {"fact_key": "se_church_employee_income_l5a", "label": "Line 5a — church employee income (W-2)", "data_type": "decimal", "default_value": "0", "sort_order": 5,
     "notes": "PER PROPRIETOR. Church-employee SE income -> RED-defer (D_SE_003); v1 line 5a/5b = 0."},
    {"fact_key": "se_w2_ss_wages_l8a", "label": "Line 8a — W-2 social-security wages + tips (boxes 3 + 7) + RRTA tier 1",
     "data_type": "decimal", "default_value": "0", "sort_order": 6,
     "notes": "PER PROPRIETOR. Consumes the SS wage base (line 9 = line 7 - line 8d). The W-2-SS-wage cap interaction."},
    {"fact_key": "se_unreported_tips_l8b", "label": "Line 8b — unreported tips subject to SS tax (Form 4137 line 10)",
     "data_type": "decimal", "default_value": "0", "sort_order": 7, "notes": "PER PROPRIETOR. Part of line 8d."},
    {"fact_key": "se_wages_8919_l8c", "label": "Line 8c — wages subject to SS tax (Form 8919 line 10)",
     "data_type": "decimal", "default_value": "0", "sort_order": 8, "notes": "PER PROPRIETOR. Part of line 8d."},
    # ── Outputs ──
    {"fact_key": "se_tax_l12", "label": "Line 12 — self-employment tax (output -> Schedule 2 line 4)", "data_type": "decimal", "sort_order": 20,
     "notes": "OUTPUT. = line 10 + line 11. Feeds Schedule 2 line 4 (computed feeder)."},
    {"fact_key": "se_half_deduction_l13", "label": "Line 13 — 1/2-SE-tax deduction (output -> Schedule 1 line 15)", "data_type": "decimal", "sort_order": 21,
     "notes": "OUTPUT. = line 12 x 50%. Feeds Schedule 1 line 15 (already an EIC Worksheet-B + 8812 feeder)."},
    {"fact_key": "se_net_earnings_l6", "label": "Line 6 — net earnings from self-employment (output; -> Form 8959 line 8)", "data_type": "decimal", "sort_order": 22,
     "notes": "OUTPUT. = line 4c + line 5b. Read by Form 8959 Part II line 8 (Additional Medicare on SE income)."},
    # ── Constants (traceability) ──
    {"fact_key": "se_wage_base_l7", "label": "Line 7 — SS wage base (YEAR-KEYED)", "data_type": "decimal", "sort_order": 30,
     "notes": "CONSTANT (year-keyed, SE_WAGE_BASE): 2025 $176,100 / 2026 $184,500. Caps the 12.4% SS portion (line 10)."},
    {"fact_key": "se_net_earnings_factor", "label": "Line 4a factor (92.35%) — statutory, non-indexed", "data_type": "decimal", "sort_order": 31,
     "notes": "CONSTANT 0.9235. Same both years."},
    {"fact_key": "se_ss_rate", "label": "Line 10 SS rate (12.4%) — statutory, non-indexed", "data_type": "decimal", "sort_order": 32,
     "notes": "CONSTANT 0.124. Same both years."},
    {"fact_key": "se_medicare_rate", "label": "Line 11 Medicare rate (2.9%, uncapped) — statutory, non-indexed", "data_type": "decimal", "sort_order": 33,
     "notes": "CONSTANT 0.029. Same both years."},
    {"fact_key": "se_half_rate", "label": "Line 13 rate (50%) — statutory, non-indexed", "data_type": "decimal", "sort_order": 34,
     "notes": "CONSTANT 0.50. Same both years."},
    {"fact_key": "se_filing_floor", "label": "Line 4c floor ($400) — statutory, non-indexed", "data_type": "decimal", "sort_order": 35,
     "notes": "CONSTANT $400. If line 4c < $400 -> stop, no SE tax (D_SE_001). Same both years."},
]

SCHEDSE_RULES: list[dict] = [
    {"rule_id": "R-SE-L2", "title": "Line 2 — aggregate Schedule C net profit per proprietor", "rule_type": "aggregation", "precedence": 1, "sort_order": 1,
     "formula": "L2 = sum of Schedule C line 31 over all businesses where sc_proprietor == se_proprietor (+ 1065 K-1 box 14 A non-farm).",
     "inputs": ["se_proprietor"], "outputs": ["2"],
     "description": ("PER PROPRIETOR. Decision 3: one Schedule SE per person aggregates that person's Schedule C "
                     "businesses. Statutory-employee Schedule C is excluded (D_SC_001).")},
    {"rule_id": "R-SE-L3", "title": "Line 3 — combine lines 1a, 1b, 2", "rule_type": "calculation", "precedence": 2, "sort_order": 2,
     "formula": "L3 = L1a + L1b + L2. (L1b is negative — CRP payments.)",
     "inputs": [], "outputs": ["3"], "description": "PER PROPRIETOR."},
    {"rule_id": "R-SE-L4A", "title": "Line 4a — net earnings x 92.35%", "rule_type": "calculation", "precedence": 3, "sort_order": 3,
     "formula": "L4a = L3 x 0.9235 if L3 > 0 else L3.",
     "inputs": ["se_net_earnings_factor"], "outputs": ["4a"],
     "description": "PER PROPRIETOR. Net earnings from self-employment. If L3 <= 0, carry L3 (a loss yields no SE tax)."},
    {"rule_id": "R-SE-L4C", "title": "Line 4c — combine 4a/4b; $400 floor", "rule_type": "calculation", "precedence": 4, "sort_order": 4,
     "formula": "L4c = L4a + L4b (L4b optional methods = 0 in v1). If L4c < $400 -> STOP, no SE tax (D_SE_001).",
     "inputs": ["se_filing_floor"], "outputs": ["4c"],
     "description": "PER PROPRIETOR. The $400 filing floor. Optional methods (Part II) are RED-defer (D_SE_003)."},
    {"rule_id": "R-SE-L6", "title": "Line 6 — add 4c and 5b", "rule_type": "calculation", "precedence": 5, "sort_order": 5,
     "formula": "L5b = L5a x 0.9235 (if < $100 -> 0); L6 = L4c + L5b. v1: L5a/L5b = 0 (church = RED-defer).",
     "inputs": [], "outputs": ["5b", "6"],
     "description": "PER PROPRIETOR. The SE-tax base. -> se_net_earnings_l6, read by Form 8959 line 8."},
    {"rule_id": "R-SE-L7", "title": "Line 7 — SS wage base (year-keyed)", "rule_type": "calculation", "precedence": 6, "sort_order": 6,
     "formula": "L7 = SE_WAGE_BASE[year] = $176,100 (2025) / $184,500 (2026).",
     "inputs": ["se_wage_base_l7"], "outputs": ["7"],
     "description": "PER PROPRIETOR. _constants_for_year at the build leg. Caps the SS portion."},
    {"rule_id": "R-SE-L8D-L9", "title": "Lines 8d/9 — W-2 SS wages consume the wage base", "rule_type": "calculation", "precedence": 7, "sort_order": 7,
     "formula": "L8d = L8a + L8b + L8c; L9 = max(0, L7 - L8d). If L8a >= L7, L9 = 0 (no SS portion).",
     "inputs": [], "outputs": ["8d", "9"],
     "description": "PER PROPRIETOR. The W-2-SS-wage cap interaction (D_SE_002): wages already taxed for SS reduce the SE SS base."},
    {"rule_id": "R-SE-L10", "title": "Line 10 — SS portion (capped) x 12.4%", "rule_type": "calculation", "precedence": 8, "sort_order": 8,
     "formula": "L10 = min(L6, L9) x 0.124.",
     "inputs": ["se_ss_rate"], "outputs": ["10"],
     "description": "PER PROPRIETOR. The 12.4% social-security portion, capped at the remaining wage base (line 9)."},
    {"rule_id": "R-SE-L11", "title": "Line 11 — Medicare portion (uncapped) x 2.9%", "rule_type": "calculation", "precedence": 9, "sort_order": 9,
     "formula": "L11 = L6 x 0.029.",
     "inputs": ["se_medicare_rate"], "outputs": ["11"],
     "description": "PER PROPRIETOR. The 2.9% Medicare portion — uncapped (no wage-base limit)."},
    {"rule_id": "R-SE-L12", "title": "Line 12 — SE tax -> Schedule 2 line 4", "rule_type": "calculation", "precedence": 10, "sort_order": 10,
     "formula": "L12 = L10 + L11 -> se_tax_l12 -> Schedule 2 line 4.",
     "inputs": [], "outputs": ["12"],
     "description": "PER PROPRIETOR. Total SE tax. On MFJ, taxpayer + spouse Schedule SE line 12 amounts both feed Schedule 2 line 4."},
    {"rule_id": "R-SE-L13", "title": "Line 13 — 1/2-SE-tax deduction -> Schedule 1 line 15", "rule_type": "calculation", "precedence": 11, "sort_order": 11,
     "formula": "L13 = L12 x 0.50 -> se_half_deduction_l13 -> Schedule 1 line 15.",
     "inputs": ["se_half_rate"], "outputs": ["13"],
     "description": ("PER PROPRIETOR. The above-the-line 1/2-SE-tax deduction (§164(f)). ALREADY feeds the EIC "
                     "Worksheet-B (eic_se_half_deduction <- Sch 1 L15) and Schedule 8812 — re-point cleanly when "
                     "Sch 1 L15 flips from direct-entry to computed.")},
    {"rule_id": "R-SE-OPTIONAL", "title": "Part II optional methods / church-employee — RED-defer", "rule_type": "routing", "precedence": 12, "sort_order": 12,
     "formula": "If se_minister_4361 OR se_church_employee_income_l5a > 0 OR farm/nonfarm optional method elected -> D_SE_003 RED-defer.",
     "inputs": ["se_minister_4361", "se_church_employee_income_l5a"], "outputs": [],
     "description": "PER PROPRIETOR. v1 = Part I standard method only. Optional methods (Part II) + church/clergy = RED-defer."},
]

SCHEDSE_LINES: list[dict] = [
    {"line_number": "1a", "description": "Net farm profit/(loss) (Sch F L34 / 1065 K-1 box 14 A)", "line_type": "input"},
    {"line_number": "1b", "description": "Conservation Reserve Program payments (negative)", "line_type": "input"},
    {"line_number": "2", "description": "Net profit/(loss) from Schedule C line 31 (sum per proprietor)", "line_type": "calculated"},
    {"line_number": "3", "description": "Combine lines 1a, 1b, and 2", "line_type": "calculated"},
    {"line_number": "4a", "description": "Line 3 x 92.35% if line 3 > 0, else line 3", "line_type": "calculated"},
    {"line_number": "4b", "description": "Optional methods (lines 15 + 17) — RED-defer (v1 = 0)", "line_type": "input"},
    {"line_number": "4c", "description": "Combine 4a and 4b; if < $400, stop (no SE tax)", "line_type": "subtotal"},
    {"line_number": "5a", "description": "Church employee income (W-2) — RED-defer (v1 = 0)", "line_type": "input"},
    {"line_number": "5b", "description": "Line 5a x 92.35% (if < $100, enter 0)", "line_type": "calculated"},
    {"line_number": "6", "description": "Add lines 4c and 5b (SE-tax base; -> Form 8959 line 8)", "line_type": "subtotal"},
    {"line_number": "7", "description": "Maximum SS wage base (year-keyed: $176,100 2025 / $184,500 2026)", "line_type": "calculated"},
    {"line_number": "8a", "description": "W-2 social-security wages + tips (boxes 3 + 7) + RRTA tier 1", "line_type": "input"},
    {"line_number": "8b", "description": "Unreported tips subject to SS tax (Form 4137 line 10)", "line_type": "input"},
    {"line_number": "8c", "description": "Wages subject to SS tax (Form 8919 line 10)", "line_type": "input"},
    {"line_number": "8d", "description": "Add lines 8a, 8b, and 8c", "line_type": "subtotal"},
    {"line_number": "9", "description": "Subtract line 8d from line 7 (>= 0)", "line_type": "calculated"},
    {"line_number": "10", "description": "Smaller of line 6 or line 9, x 12.4%", "line_type": "calculated"},
    {"line_number": "11", "description": "Line 6 x 2.9% (uncapped Medicare portion)", "line_type": "calculated"},
    {"line_number": "12", "description": "Self-employment tax. Add lines 10 and 11 -> Schedule 2 line 4", "line_type": "total"},
    {"line_number": "13", "description": "1/2-SE-tax deduction. Line 12 x 50% -> Schedule 1 line 15", "line_type": "total"},
    {"line_number": "14", "description": "Part II — maximum income for optional methods (RED-defer)", "line_type": "input"},
    {"line_number": "15", "description": "Part II — farm optional method amount (RED-defer)", "line_type": "input"},
    {"line_number": "16", "description": "Part II — line 14 minus line 15 (RED-defer)", "line_type": "input"},
    {"line_number": "17", "description": "Part II — nonfarm optional method amount (RED-defer)", "line_type": "input"},
]

SCHEDSE_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_SE_001", "title": "Net SE earnings below $400 — no self-employment tax", "severity": "info",
     "condition": "line 4c < $400",
     "message": ("Net earnings from self-employment (line 4c) are less than $400, so no self-employment tax is "
                 "due (Schedule SE is not required). Confirm this is correct — small or loss businesses still "
                 "report Schedule C."),
     "notes": "The $400 floor. Informational (not an error)."},
    {"diagnostic_id": "D_SE_002", "title": "W-2 social-security wages reduce the SE social-security base", "severity": "info",
     "condition": "line 8d > 0 (W-2 SS wages present)",
     "message": ("Your W-2 social-security wages (line 8d) reduce the remaining social-security wage base available "
                 "for self-employment tax (line 9). If your W-2 SS wages already meet or exceed the wage base, only "
                 "the 2.9% Medicare portion applies to your SE earnings."),
     "notes": "The W-2-SS-wage cap interaction. Informational (explains a lower line 10)."},
    {"diagnostic_id": "D_SE_003", "title": "Optional methods / church-employee / clergy SE — not supported", "severity": "error",
     "condition": "se_minister_4361 is True OR se_church_employee_income_l5a > 0 OR a Part II optional method is elected",
     "message": ("Not supported — prepare manually: Schedule SE optional methods (farm/nonfarm, Part II), "
                 "church-employee income (line 5), and Form 4361 minister handling are not modeled this sprint. "
                 "v1 computes the Part I standard method only."),
     "notes": "RED-defer (brief standing RED-defer: SE optional methods + church-employee)."},
    {"diagnostic_id": "D_SE_004", "title": "SE earnings exceed the social-security wage base — SS portion capped", "severity": "info",
     "condition": "min(line 6, line 9) == line 9 AND line 9 < line 6",
     "message": ("Your combined self-employment earnings plus W-2 social-security wages exceed the social-security "
                 "wage base for the year, so the 12.4% social-security portion is capped (line 10 uses line 9, not "
                 "line 6). The 2.9% Medicare portion (line 11) still applies to all of line 6."),
     "notes": "The wage-base cap binding. Informational."},
]

SCHEDSE_SCENARIOS: list[dict] = [
    {"scenario_name": "SE-T1 — simple sole proprietor, TY2025: net profit 50,000", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "line_2": 50000, "se_w2_ss_wages_l8a": 0},
     "expected_outputs": {"line_4a": 46175, "line_6": 46175, "line_10": 5725.70, "line_11": 1339.08,
                          "line_12": 7064.78, "line_13": 3532.39},
     "notes": ("L4a=50,000 x 0.9235=46,175; SS L10=46,175 x 0.124=5,725.70; Medicare L11=46,175 x 0.029=1,339.08; "
               "L12=7,064.78 -> Sch 2 L4; L13=3,532.39 -> Sch 1 L15. Integrity check pins the rounding.")},
    {"scenario_name": "SE-T2 — W-2 wages consume the SS base, TY2025: profit 60,000 + W-2 SS wages 170,000", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"tax_year": 2025, "line_2": 60000, "se_w2_ss_wages_l8a": 170000},
     "expected_outputs": {"line_4a": 55410, "line_6": 55410, "line_7": 176100, "line_9": 6100,
                          "line_10": 756.40, "line_11": 1606.89, "line_12": 2363.29, "D_SE_002": True},
     "notes": ("L6=55,410; L9=176,100-170,000=6,100; SS L10=min(55,410, 6,100) x 0.124=756.40; Medicare "
               "L11=55,410 x 0.029=1,606.89; L12=2,363.29. W-2 SS wages cap the SS portion.")},
    {"scenario_name": "SE-T3 — below the $400 floor (D_SE_001)", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"tax_year": 2025, "line_2": 400, "se_w2_ss_wages_l8a": 0},
     "expected_outputs": {"line_4a": 369.40, "line_4c": 369.40, "line_12": 0, "D_SE_001": True},
     "notes": "L4a=400 x 0.9235=369.40 < $400 -> stop, no SE tax."},
    {"scenario_name": "SE-T4 — profit above the wage base, TY2026: profit 250,000 (SS capped, D_SE_004)", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"tax_year": 2026, "line_2": 250000, "se_w2_ss_wages_l8a": 0},
     "expected_outputs": {"line_4a": 230875, "line_6": 230875, "line_7": 184500, "line_9": 184500,
                          "line_10": 22878.00, "line_11": 6695.38, "line_12": 29573.38, "D_SE_004": True},
     "notes": ("TY2026 wage base 184,500. L6=230,875 > L9=184,500 -> SS L10=184,500 x 0.124=22,878.00; Medicare "
               "L11=230,875 x 0.029=6,695.38 (uncapped). Year-keying load-bearing (2025 base would differ).")},
    {"scenario_name": "SE-T5 — 1/2-SE-tax feeds Schedule 1 line 15 (EIC/8812 feeder)", "scenario_type": "normal", "sort_order": 5,
     "inputs": {"tax_year": 2025, "line_2": 30000, "se_w2_ss_wages_l8a": 0},
     "expected_outputs": {"line_4a": 27705, "line_12": 4238.87, "line_13": 2119.44, "feeds_sch1_l15": True},
     "notes": ("L4a=27,705; L12=27,705 x 0.153=4,238.87; L13=2,119.44 -> Sch 1 L15 (re-points the EIC Worksheet-B "
               "+ 8812 feeder from direct-entry to computed).")},
]

SCHEDSE_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-SE-L2", "IRS_2025_SCHEDSE_FORM", "primary", "Line 2 <- Schedule C line 31"),
    ("R-SE-L3", "IRS_2025_SCHEDSE_FORM", "primary", "Line 3 combine 1a/1b/2"),
    ("R-SE-L4A", "IRS_2025_SCHEDSE_FORM", "primary", "Line 4a x 92.35%"),
    ("R-SE-L4C", "IRS_2025_SCHEDSE_FORM", "primary", "Line 4c $400 floor"),
    ("R-SE-L6", "IRS_2025_SCHEDSE_FORM", "primary", "Line 6 SE-tax base"),
    ("R-SE-L7", "IRS_2025_SCHEDSE_FORM", "primary", "Line 7 wage base (2025 $176,100)"),
    ("R-SE-L7", "IRS_TOPIC751_SE", "secondary", "2026 wage base $184,500"),
    ("R-SE-L8D-L9", "IRS_2025_SCHEDSE_FORM", "primary", "Lines 8d/9 W-2 SS wages consume base"),
    ("R-SE-L10", "IRS_2025_SCHEDSE_FORM", "primary", "Line 10 SS portion x 12.4%"),
    ("R-SE-L11", "IRS_2025_SCHEDSE_FORM", "primary", "Line 11 Medicare x 2.9%"),
    ("R-SE-L12", "IRS_2025_SCHEDSE_FORM", "primary", "Line 12 SE tax -> Sch 2 L4"),
    ("R-SE-L13", "IRS_2025_SCHEDSE_FORM", "primary", "Line 13 1/2-SE -> Sch 1 L15"),
    ("R-SE-OPTIONAL", "IRS_2025_SCHEDSE_FORM", "primary", "Part II optional methods (RED-defer)"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 3 — 8995 (QBI Deduction, Simplified Computation) — RE-AUTHORED
# ═══════════════════════════════════════════════════════════════════════════

F8995_IDENTITY = {
    "form_number": "8995",
    "form_title": "Form 8995 — Qualified Business Income Deduction Simplified Computation (TY2025)",
    "notes": (
        "Sprint Topic 8. RE-AUTHORED over a wrong early-draft stub (Line 2 QBI 'from "
        "K-1', 8-line map, no income limitation / REIT-PTP split / loss carryforward). "
        "The real 17-line face: per-business QBI (Schedule C net profit reduced by "
        "attributable 1/2-SE-tax / SEHI / SE-retirement) x 20%, the REIT/PTP component "
        "x 20%, the taxable-income x 20% limitation -> the smaller -> Form 1040 line "
        "13a. BELOW-THRESHOLD ONLY (year-keyed); above threshold -> Form 8995-A "
        "RED-defer. The stub artifacts (R001-R005, D001-D003, lines 1-8, the 3 "
        "tests) are retired by this loader."
    ),
}

F8995_FACTS: list[dict] = [
    # ── Per-business QBI (model-driven from Schedule C; up to 5 on the face) ──
    {"fact_key": "qbi_business_qbi", "label": "Line 1(c) — qualified business income per business (model-driven)",
     "data_type": "decimal", "default_value": "0", "sort_order": 1,
     "notes": ("PER BUSINESS. = Schedule C net profit (line 31) REDUCED by the attributable deductible 1/2-SE-tax "
               "(Sch 1 L15), SEHI (Sch 1 L17), and SE retirement (Sch 1 L16). WALK ITEM 2: multi-business "
               "allocation = pro-rata by net SE earnings. Up to 5 businesses list on lines 1i-1v.")},
    {"fact_key": "qbi_is_sstb", "label": "Specified service trade/business (SSTB) — for the above-threshold diagnostic only",
     "data_type": "boolean", "sort_order": 2,
     "notes": "PER BUSINESS. Below threshold SSTB is irrelevant (no limit). Stored only for the 8995-A scope diagnostic (D_8995_001)."},
    {"fact_key": "qbi_loss_carryforward_prior", "label": "Line 3 — qualified business net (loss) carryforward from the prior year",
     "data_type": "decimal", "default_value": "0", "sort_order": 3,
     "notes": "RETURN LEVEL. Negative. WALK ITEM 4: v1 preparer-entered prior-year carryforward."},
    {"fact_key": "qbi_reit_ptp_income", "label": "Line 6 — qualified REIT dividends + PTP income/(loss)",
     "data_type": "decimal", "default_value": "0", "sort_order": 4,
     "notes": "RETURN LEVEL. Reuses 1099-DIV box 5 (§199A dividends, stored Topic 3) + PTP K-1 income. YELLOW."},
    {"fact_key": "qbi_reit_ptp_carryforward_prior", "label": "Line 7 — REIT/PTP (loss) carryforward from the prior year",
     "data_type": "decimal", "default_value": "0", "sort_order": 5,
     "notes": "RETURN LEVEL. Negative. WALK ITEM 4."},
    {"fact_key": "qbi_taxable_income_before_qbi", "label": "Line 11 — taxable income before the QBI deduction",
     "data_type": "decimal", "default_value": "0", "sort_order": 6,
     "notes": "RETURN LEVEL. = Form 1040 line 11 (AGI) - line 12 (std/itemized deduction). The scope gate compares this to the threshold."},
    {"fact_key": "qbi_net_capital_gain", "label": "Line 12 — net capital gain (qualified dividends + net capital gain)",
     "data_type": "decimal", "default_value": "0", "sort_order": 7,
     "notes": ("RETURN LEVEL. = 1040 L3a (qualified dividends) + net capital gain. WALK ITEM 3: Schedule D not "
               "built -> v1 = L3a + cap-gain distributions (1040 L7 when no Sch D); add net LT gain when Sch D lands.")},
    {"fact_key": "qbi_filing_status", "label": "Filing status (selects the year-keyed threshold)", "data_type": "string", "sort_order": 8,
     "notes": "RETURN LEVEL. mfj|mfs|single|hoh|qss. Selects QBI_THRESHOLDS column (single/hoh/qss -> 'other')."},
    # ── Outputs ──
    {"fact_key": "qbi_deduction_l15", "label": "Line 15 — QBI deduction (output -> Form 1040 line 13a)", "data_type": "decimal", "sort_order": 20,
     "notes": "OUTPUT. = min(line 10, line 14). Feeds Form 1040 line 13a (computed feeder)."},
    {"fact_key": "qbi_carryforward_out_l16", "label": "Line 16 — QBI (loss) carryforward to next year (output)", "data_type": "decimal", "sort_order": 21,
     "notes": "OUTPUT. = combine lines 2 and 3 if <= 0 (negative carried forward); else 0. WALK ITEM 4."},
    {"fact_key": "qbi_reit_carryforward_out_l17", "label": "Line 17 — REIT/PTP (loss) carryforward to next year (output)", "data_type": "decimal", "sort_order": 22,
     "notes": "OUTPUT. = combine lines 6 and 7 if <= 0; else 0. WALK ITEM 4."},
    # ── Constants ──
    {"fact_key": "qbi_rate", "label": "QBI rate (20%) — statutory §199A, non-indexed", "data_type": "decimal", "sort_order": 30,
     "notes": "CONSTANT 0.20 (lines 5/9/14). Same both years."},
    {"fact_key": "qbi_threshold", "label": "8995-vs-8995A threshold (YEAR-KEYED + filing-status)", "data_type": "decimal", "sort_order": 31,
     "notes": ("CONSTANT (year-keyed, QBI_THRESHOLDS): 2025 $394,600 MFJ / $197,300 other; 2026 $403,500 MFJ / "
               "$201,775 MFS / $201,750 other. WALK ITEM 1: 2026 MFS is $25 above 'other'. Above -> Form 8995-A.")},
]

F8995_RULES: list[dict] = [
    {"rule_id": "R-8995-SCOPE", "title": "Scope gate — taxable income at/below threshold (else Form 8995-A)", "rule_type": "routing", "precedence": 0, "sort_order": 1,
     "formula": "If qbi_taxable_income_before_qbi (line 11) > QBI_THRESHOLDS[year][status] -> D_8995_001 RED (use Form 8995-A); 8995 not used.",
     "inputs": ["qbi_taxable_income_before_qbi", "qbi_threshold", "qbi_filing_status"], "outputs": [],
     "description": ("RETURN LEVEL. Simplified Form 8995 is valid only at/below the threshold; above it, Form 8995-A "
                     "applies the W-2/UBIA and SSTB limitations (RED-defer). WALK ITEM 1: per-status 2026 table.")},
    {"rule_id": "R-8995-QBI", "title": "Line 1 — per-business QBI (Sch C net profit reduced by 1/2-SE/SEHI/retirement)", "rule_type": "calculation", "precedence": 1, "sort_order": 2,
     "formula": ("Per business: QBI = Schedule C line 31 - attributable (Sch 1 L15 1/2-SE-tax + Sch 1 L17 SEHI + "
                 "Sch 1 L16 SE-retirement). Multi-business: allocate the three reductions pro-rata by net SE "
                 "earnings (WALK ITEM 2). Lines 1i-1v list up to 5 businesses."),
     "inputs": ["qbi_business_qbi"], "outputs": ["1i", "1ii", "1iii", "1iv", "1v"],
     "description": "RETURN LEVEL (per-business rows). i8995: QBI is reduced by the deductions attributable to the trade/business."},
    {"rule_id": "R-8995-L2-L5", "title": "Lines 2/4/5 — QBI component", "rule_type": "calculation", "precedence": 2, "sort_order": 3,
     "formula": "L2 = sum(1i..1v); L4 = max(0, L2 + L3 prior-year carryforward); L5 = L4 x 20%.",
     "inputs": ["qbi_loss_carryforward_prior", "qbi_rate"], "outputs": ["2", "4", "5"],
     "description": "RETURN LEVEL. The QBI component. L3 (prior-year loss carryforward) is negative."},
    {"rule_id": "R-8995-L8-L9", "title": "Lines 8/9 — REIT/PTP component", "rule_type": "calculation", "precedence": 3, "sort_order": 4,
     "formula": "L8 = max(0, L6 REIT/PTP income + L7 prior-year carryforward); L9 = L8 x 20%.",
     "inputs": ["qbi_reit_ptp_income", "qbi_reit_ptp_carryforward_prior", "qbi_rate"], "outputs": ["8", "9"],
     "description": "RETURN LEVEL. The REIT/PTP component. L6 reuses 1099-DIV box 5 §199A dividends + PTP income."},
    {"rule_id": "R-8995-L10", "title": "Line 10 — QBI deduction before income limitation", "rule_type": "calculation", "precedence": 4, "sort_order": 5,
     "formula": "L10 = L5 + L9.",
     "inputs": [], "outputs": ["10"], "description": "RETURN LEVEL."},
    {"rule_id": "R-8995-L13-L14", "title": "Lines 11/12/13/14 — income limitation", "rule_type": "calculation", "precedence": 5, "sort_order": 6,
     "formula": "L11 = taxable income before QBI (1040 L11 - L12); L12 = net capital gain (L3a + net cap gain); L13 = max(0, L11 - L12); L14 = L13 x 20%.",
     "inputs": ["qbi_taxable_income_before_qbi", "qbi_net_capital_gain", "qbi_rate"], "outputs": ["11", "12", "13", "14"],
     "description": "RETURN LEVEL. The income limitation reduces taxable income by net capital gain before the 20%. WALK ITEM 3 (net cap gain / Sch D)."},
    {"rule_id": "R-8995-L15", "title": "Line 15 — QBI deduction = min(L10, L14) -> 1040 line 13a", "rule_type": "calculation", "precedence": 6, "sort_order": 7,
     "formula": "L15 = min(L10, L14) -> qbi_deduction_l15 -> Form 1040 line 13a.",
     "inputs": [], "outputs": ["15"],
     "description": "RETURN LEVEL. The deduction is the smaller of the components total and the income limitation. Override = escape hatch."},
    {"rule_id": "R-8995-L16-L17", "title": "Lines 16/17 — loss carryforward to next year", "rule_type": "calculation", "precedence": 7, "sort_order": 8,
     "formula": "L16 = min(0, L2 + L3) (QBI loss carried out); L17 = min(0, L6 + L7) (REIT/PTP loss carried out). Reported as <= 0.",
     "inputs": [], "outputs": ["16", "17"],
     "description": "RETURN LEVEL. WALK ITEM 4: when net QBI or net REIT/PTP < 0, the loss carries forward (negative)."},
]

F8995_LINES: list[dict] = [
    {"line_number": "1i", "description": "Line 1(i) — business 1: name / TIN / QBI", "line_type": "input"},
    {"line_number": "1ii", "description": "Line 1(ii) — business 2: name / TIN / QBI", "line_type": "input"},
    {"line_number": "1iii", "description": "Line 1(iii) — business 3: name / TIN / QBI", "line_type": "input"},
    {"line_number": "1iv", "description": "Line 1(iv) — business 4: name / TIN / QBI", "line_type": "input"},
    {"line_number": "1v", "description": "Line 1(v) — business 5: name / TIN / QBI", "line_type": "input"},
    {"line_number": "2", "description": "Total QBI. Combine lines 1i-1v, column (c)", "line_type": "subtotal"},
    {"line_number": "3", "description": "Qualified business net (loss) carryforward from the prior year", "line_type": "input"},
    {"line_number": "4", "description": "Total QBI. Combine lines 2 and 3 (if <= 0, enter 0)", "line_type": "calculated"},
    {"line_number": "5", "description": "QBI component. Line 4 x 20%", "line_type": "calculated"},
    {"line_number": "6", "description": "Qualified REIT dividends + PTP income/(loss)", "line_type": "input"},
    {"line_number": "7", "description": "REIT/PTP (loss) carryforward from the prior year", "line_type": "input"},
    {"line_number": "8", "description": "Total REIT/PTP income. Combine lines 6 and 7 (if <= 0, enter 0)", "line_type": "calculated"},
    {"line_number": "9", "description": "REIT/PTP component. Line 8 x 20%", "line_type": "calculated"},
    {"line_number": "10", "description": "QBI deduction before income limitation. Add lines 5 and 9", "line_type": "subtotal"},
    {"line_number": "11", "description": "Taxable income before the QBI deduction (1040 L11 - L12)", "line_type": "calculated"},
    {"line_number": "12", "description": "Net capital gain (qualified dividends + net capital gain)", "line_type": "calculated"},
    {"line_number": "13", "description": "Subtract line 12 from line 11 (if <= 0, enter 0)", "line_type": "calculated"},
    {"line_number": "14", "description": "Income limitation. Line 13 x 20%", "line_type": "calculated"},
    {"line_number": "15", "description": "QBI deduction = smaller of line 10 or 14 -> Form 1040 line 13a", "line_type": "total"},
    {"line_number": "16", "description": "Total QBI (loss) carryforward to next year", "line_type": "calculated"},
    {"line_number": "17", "description": "Total REIT/PTP (loss) carryforward to next year", "line_type": "calculated"},
]

F8995_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_8995_001", "title": "Taxable income above the §199A threshold — use Form 8995-A", "severity": "error",
     "condition": "qbi_taxable_income_before_qbi > QBI_THRESHOLDS[year][status]",
     "message": ("Not supported — prepare manually: your taxable income before the QBI deduction exceeds the "
                 "§199A threshold (${threshold}), so the simplified Form 8995 cannot be used. Form 8995-A "
                 "(W-2 wages / UBIA limits, SSTB phase-out) is required and is not built this sprint."),
     "notes": "Year-keyed threshold. WALK ITEM 1 (2026 MFS $25 split). RED-defer Form 8995-A."},
    {"diagnostic_id": "D_8995_002", "title": "Net capital gain — Schedule D not built (line 12 partial)", "severity": "warning",
     "condition": "Schedule D / 8949 not built AND (1040 line 7 capital gain present)",
     "message": ("Line 12 (net capital gain) currently uses qualified dividends (1040 line 3a) plus capital-gain "
                 "distributions only. When Schedule D is built, net long-term capital gain must be added to line 12 "
                 "— a higher line 12 lowers the income-limitation cap (line 14) and can reduce the QBI deduction."),
     "notes": "WALK ITEM 3 deferred-interaction. No-silent-gap reminder."},
    {"diagnostic_id": "D_8995_003", "title": "QBI loss carryforward present — verify prior/next-year amounts", "severity": "info",
     "condition": "qbi_loss_carryforward_prior < 0 OR qbi_reit_ptp_carryforward_prior < 0 OR line 16 < 0 OR line 17 < 0",
     "message": ("A qualified-business or REIT/PTP loss carryforward is present (line 3/7 in, or line 16/17 out). "
                 "Verify the prior-year carryforward entries and note the current-year loss carried to next year."),
     "notes": "WALK ITEM 4."},
    {"diagnostic_id": "D_8995_004", "title": "Multiple businesses — verify QBI reduction allocation", "severity": "info",
     "condition": "more than one business with QBI AND (1/2-SE-tax or SEHI or SE-retirement deductions present)",
     "message": ("With more than one qualified business, the deductible 1/2-SE-tax, self-employed health "
                 "insurance, and self-employed retirement deductions are allocated across businesses (pro-rata by "
                 "net SE earnings) to figure each business's QBI. Verify the allocation."),
     "notes": "WALK ITEM 2 (multi-business QBI allocation)."},
    {"diagnostic_id": "D_8995_005", "title": "Specified service trade/business (SSTB) below threshold — no limit", "severity": "info",
     "condition": "qbi_is_sstb is True AND taxable income at/below threshold",
     "message": ("This is a specified service trade or business (SSTB). Below the §199A threshold the SSTB "
                 "limitation does NOT apply — full QBI is allowed. (Above the threshold, the SSTB phase-out on "
                 "Form 8995-A would apply.)"),
     "notes": "Clarifies that SSTB is irrelevant below threshold (the simplified form's whole premise)."},
]

F8995_SCENARIOS: list[dict] = [
    {"scenario_name": "8995-T1 — single Schedule C, below threshold: QBI 60,000 -> 12,000", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "filing_status": "single", "qbi_business_qbi": 60000,
                "qbi_taxable_income_before_qbi": 90000, "qbi_net_capital_gain": 0},
     "expected_outputs": {"line_2": 60000, "line_5": 12000, "line_10": 12000, "line_13": 90000, "line_14": 18000, "line_15": 12000},
     "notes": "L5=60,000 x 20%=12,000; income limit L14=90,000 x 20%=18,000; L15=min(12,000, 18,000)=12,000 -> 1040 L13a."},
    {"scenario_name": "8995-T2 — QBI reduced by 1/2-SE-tax + SEHI", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"tax_year": 2025, "filing_status": "single", "sch_c_net_profit": 60000, "half_se_tax": 4239, "sehi": 6000,
                "qbi_taxable_income_before_qbi": 80000, "qbi_net_capital_gain": 0},
     "expected_outputs": {"qbi_business_qbi": 49761, "line_5": 9952.20, "line_15": 9952.20},
     "notes": "QBI = 60,000 - 4,239 (1/2-SE) - 6,000 (SEHI) = 49,761; L5=9,952.20; income limit not binding -> L15=9,952.20."},
    {"scenario_name": "8995-T3 — income limitation binds (L14 < L10)", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"tax_year": 2025, "filing_status": "single", "qbi_business_qbi": 50000,
                "qbi_taxable_income_before_qbi": 40000, "qbi_net_capital_gain": 0},
     "expected_outputs": {"line_10": 10000, "line_13": 40000, "line_14": 8000, "line_15": 8000},
     "notes": "L10=50,000 x 20%=10,000 but income limit L14=40,000 x 20%=8,000 binds -> L15=8,000 (the smaller)."},
    {"scenario_name": "8995-T4 — REIT/PTP dividends only (no Schedule C)", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "qbi_business_qbi": 0, "qbi_reit_ptp_income": 8000,
                "qbi_taxable_income_before_qbi": 120000, "qbi_net_capital_gain": 0},
     "expected_outputs": {"line_8": 8000, "line_9": 1600, "line_10": 1600, "line_15": 1600},
     "notes": "REIT/PTP component L9=8,000 x 20%=1,600; income limit not binding -> L15=1,600 -> 1040 L13a."},
    {"scenario_name": "8995-T5 — above threshold -> Form 8995-A RED (D_8995_001)", "scenario_type": "normal", "sort_order": 5,
     "inputs": {"tax_year": 2025, "filing_status": "single", "qbi_business_qbi": 100000, "qbi_taxable_income_before_qbi": 250000},
     "expected_outputs": {"D_8995_001": True, "form_8995_used": False},
     "notes": "Taxable income 250,000 > 197,300 (2025 other) -> Form 8995-A required; simplified 8995 not used (RED-defer)."},
    {"scenario_name": "8995-T6 — net capital gain reduces the income limitation", "scenario_type": "normal", "sort_order": 6,
     "inputs": {"tax_year": 2025, "filing_status": "single", "qbi_business_qbi": 50000,
                "qbi_taxable_income_before_qbi": 60000, "qbi_net_capital_gain": 20000},
     "expected_outputs": {"line_10": 10000, "line_13": 40000, "line_14": 8000, "line_15": 8000},
     "notes": "L13=60,000 - 20,000 net cap gain=40,000; L14=8,000 < L10=10,000 -> L15=8,000. WALK ITEM 3 (net cap gain)."},
    {"scenario_name": "8995-T7 — TY2026 threshold (year-keying load-bearing)", "scenario_type": "normal", "sort_order": 7,
     "inputs": {"tax_year": 2026, "filing_status": "single", "qbi_business_qbi": 80000, "qbi_taxable_income_before_qbi": 201000},
     "expected_outputs": {"form_8995_used": True, "line_5": 16000},
     "notes": "TY2026 single threshold 201,750: taxable income 201,000 <= 201,750 -> 8995 valid (2025 threshold 197,300 would block). Year-keying load-bearing."},
]

F8995_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-8995-SCOPE", "IRS_2025_8995_FORM", "primary", "Use-this-form-if threshold ($197,300/$394,600 2025)"),
    ("R-8995-SCOPE", "RP_2025_32", "primary", "TY2026 §199A thresholds (§4.26)"),
    ("R-8995-QBI", "IRS_2025_8995_INSTR", "primary", "QBI reduced by 1/2-SE/SEHI/SE-retirement"),
    ("R-8995-L2-L5", "IRS_2025_8995_FORM", "primary", "Lines 2/4/5 QBI component"),
    ("R-8995-L8-L9", "IRS_2025_8995_FORM", "primary", "Lines 6/8/9 REIT/PTP component"),
    ("R-8995-L10", "IRS_2025_8995_FORM", "primary", "Line 10 add 5 and 9"),
    ("R-8995-L13-L14", "IRS_2025_8995_FORM", "primary", "Lines 11-14 income limitation"),
    ("R-8995-L13-L14", "IRS_2025_8995_INSTR", "secondary", "Line 11/12 sourcing (taxable income before QBI; net cap gain)"),
    ("R-8995-L15", "IRS_2025_8995_FORM", "primary", "Line 15 min(10,14) -> 1040 L13a"),
    ("R-8995-L16-L17", "IRS_2025_8995_FORM", "primary", "Lines 16/17 loss carryforward out"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 4 — 8959 (Additional Medicare Tax)
# ═══════════════════════════════════════════════════════════════════════════

F8959_IDENTITY = {
    "form_number": "8959",
    "form_title": "Form 8959 — Additional Medicare Tax (TY2025)",
    "notes": (
        "Sprint Topic 8 (Decision 4 — Ken expanded scope over the RED-defer "
        "recommendation). Part I (Medicare wages over the filing-status threshold x "
        "0.9%), Part II (SE income over the threshold REDUCED BY Medicare wages x "
        "0.9%) -> line 18 -> Schedule 2 line 11. Part V withholding reconciliation "
        "-> Form 1040 line 25c. Thresholds NON-indexed ($250k MFJ / $125k MFS / "
        "$200k other). Engage-gated (no 8959 on ordinary returns). Part III RRTA = "
        "RED-defer."
    ),
}

F8959_FACTS: list[dict] = [
    {"fact_key": "amt_medicare_wages_l1", "label": "Line 1 — Medicare wages and tips (W-2 box 5)", "data_type": "decimal", "default_value": "0", "sort_order": 1,
     "notes": "RETURN LEVEL. Sum of W-2 box 5 across all W-2s. Drives Part I and (as line 10) the Part II threshold reduction."},
    {"fact_key": "amt_unreported_tips_l2", "label": "Line 2 — unreported tips (Form 4137 line 6)", "data_type": "decimal", "default_value": "0", "sort_order": 2,
     "notes": "RETURN LEVEL. Part of line 4."},
    {"fact_key": "amt_wages_8919_l3", "label": "Line 3 — wages (Form 8919 line 6)", "data_type": "decimal", "default_value": "0", "sort_order": 3,
     "notes": "RETURN LEVEL. Part of line 4."},
    {"fact_key": "amt_se_income_l8", "label": "Line 8 — self-employment income (Schedule SE Part I line 6; loss -> 0)", "data_type": "decimal", "default_value": "0", "sort_order": 4,
     "notes": "RETURN LEVEL. <- Schedule SE line 6 (se_net_earnings_l6). If a loss, enter 0."},
    {"fact_key": "amt_rrta_compensation_l14", "label": "Line 14 — RRTA compensation (W-2 box 14) — RED-defer", "data_type": "decimal", "default_value": "0", "sort_order": 5,
     "notes": "RETURN LEVEL. Part III RRTA -> RED-defer (D_8959_002); v1 line 17 = 0."},
    {"fact_key": "amt_medicare_withheld_l19", "label": "Line 19 — Medicare tax withheld (W-2 box 6)", "data_type": "decimal", "default_value": "0", "sort_order": 6,
     "notes": "RETURN LEVEL. Part V reconciliation; the 0.9% extra withholding flows to 1040 line 25c."},
    {"fact_key": "amt_rrta_addl_withheld_l23", "label": "Line 23 — Additional Medicare withholding on RRTA (W-2 box 14) — RED-defer", "data_type": "decimal", "default_value": "0", "sort_order": 7,
     "notes": "RETURN LEVEL. RRTA -> RED-defer; v1 = 0."},
    {"fact_key": "amt_filing_status", "label": "Filing status (selects the threshold)", "data_type": "string", "sort_order": 8,
     "notes": "RETURN LEVEL. mfj|mfs|single|hoh|qss. Selects ADDL_MEDICARE_THRESHOLDS (single/hoh/qss -> 'other')."},
    # ── Outputs ──
    {"fact_key": "addl_medicare_tax_l18", "label": "Line 18 — total Additional Medicare Tax (output -> Schedule 2 line 11)", "data_type": "decimal", "sort_order": 20,
     "notes": "OUTPUT. = line 7 + line 13 + line 17. Feeds Schedule 2 line 11 (computed feeder)."},
    {"fact_key": "addl_medicare_withholding_l24", "label": "Line 24 — Additional Medicare withholding (output -> Form 1040 line 25c)", "data_type": "decimal", "sort_order": 21,
     "notes": "OUTPUT. = line 22 + line 23. Added with federal income tax withholding on Form 1040 line 25c."},
    # ── Constants ──
    {"fact_key": "addl_medicare_rate", "label": "Additional Medicare rate (0.9%) — statutory, non-indexed", "data_type": "decimal", "sort_order": 30,
     "notes": "CONSTANT 0.009 (lines 7/13/17). Same both years."},
    {"fact_key": "regular_medicare_rate", "label": "Regular Medicare withholding rate (1.45%) — line 21", "data_type": "decimal", "sort_order": 31,
     "notes": "CONSTANT 0.0145 (line 21 regular Medicare withholding on wages). Same both years."},
    {"fact_key": "addl_medicare_threshold", "label": "Filing-status threshold (NON-indexed)", "data_type": "decimal", "sort_order": 32,
     "notes": "CONSTANT (non-indexed, same both years): MFJ $250,000 / MFS $125,000 / Single·HOH·QSS $200,000."},
]

F8959_RULES: list[dict] = [
    {"rule_id": "R-8959-ENGAGE", "title": "Engage gate — compute only when wages/SE exceed the threshold", "rule_type": "routing", "precedence": 0, "sort_order": 1,
     "formula": "8959 engages iff line 4 (Medicare wages) > threshold OR (line 8 SE income + line 4) > threshold. Else line 11 (Sch 2) untouched.",
     "inputs": ["amt_medicare_wages_l1", "amt_se_income_l8", "amt_filing_status", "addl_medicare_threshold"], "outputs": [],
     "description": ("RETURN LEVEL. The EIC engage-gate precedent: no Form 8959 / Schedule 2 line 11 entry on "
                     "ordinary returns under the threshold (D_8959_001 explains when it engages).")},
    {"rule_id": "R-8959-L4-L7", "title": "Part I lines 4/6/7 — Additional Medicare on wages", "rule_type": "calculation", "precedence": 1, "sort_order": 2,
     "formula": "L4 = L1 + L2 + L3; L6 = max(0, L4 - threshold); L7 = L6 x 0.9%.",
     "inputs": ["addl_medicare_rate", "addl_medicare_threshold"], "outputs": ["4", "6", "7"],
     "description": "RETURN LEVEL. Part I: Medicare wages over the filing-status threshold, at 0.9%."},
    {"rule_id": "R-8959-L11-L13", "title": "Part II lines 8/10/11/12/13 — SE income (threshold reduced by Medicare wages)", "rule_type": "calculation", "precedence": 2, "sort_order": 3,
     "formula": "L8 = Sch SE line 6 (loss -> 0); L10 = L4 (Medicare wages); L11 = max(0, threshold - L10); L12 = max(0, L8 - L11); L13 = L12 x 0.9%.",
     "inputs": ["amt_se_income_l8", "addl_medicare_rate", "addl_medicare_threshold"], "outputs": ["8", "10", "11", "12", "13"],
     "description": ("RETURN LEVEL. The LOAD-BEARING nuance: the SE threshold is REDUCED BY Medicare wages (line 11 = "
                     "threshold - line 4), so wages and SE income share one threshold (D_8959_004).")},
    {"rule_id": "R-8959-L18", "title": "Part IV line 18 — total Additional Medicare Tax -> Schedule 2 line 11", "rule_type": "calculation", "precedence": 3, "sort_order": 4,
     "formula": "L18 = L7 + L13 + L17 (RRTA = 0 in v1) -> addl_medicare_tax_l18 -> Schedule 2 line 11.",
     "inputs": [], "outputs": ["18"],
     "description": "RETURN LEVEL. The total Additional Medicare Tax (computed feeder to Schedule 2 line 11)."},
    {"rule_id": "R-8959-L21-L24", "title": "Part V lines 19-24 — withholding reconciliation -> 1040 line 25c", "rule_type": "calculation", "precedence": 4, "sort_order": 5,
     "formula": "L20 = L1; L21 = L20 x 1.45%; L22 = max(0, L19 - L21); L24 = L22 + L23 (RRTA = 0) -> Form 1040 line 25c.",
     "inputs": ["regular_medicare_rate"], "outputs": ["19", "20", "21", "22", "24"],
     "description": ("RETURN LEVEL. Separates the Additional Medicare Tax withholding (the 0.9% extra over 1.45% in "
                     "W-2 box 6) from regular Medicare withholding; line 24 -> 1040 line 25c (federal withholding).")},
    {"rule_id": "R-8959-RRTA", "title": "Part III RRTA (lines 14-17) — RED-defer", "rule_type": "routing", "precedence": 5, "sort_order": 6,
     "formula": "If amt_rrta_compensation_l14 > 0 -> D_8959_002 RED-defer; v1 line 17 = 0.",
     "inputs": ["amt_rrta_compensation_l14"], "outputs": ["17"],
     "description": "RETURN LEVEL. RRTA compensation Additional Medicare Tax is RED-defer (brief standing RED-defer)."},
]

F8959_LINES: list[dict] = [
    {"line_number": "1", "description": "Medicare wages and tips (W-2 box 5)", "line_type": "input"},
    {"line_number": "2", "description": "Unreported tips (Form 4137 line 6)", "line_type": "input"},
    {"line_number": "3", "description": "Wages (Form 8919 line 6)", "line_type": "input"},
    {"line_number": "4", "description": "Add lines 1 through 3", "line_type": "subtotal"},
    {"line_number": "5", "description": "Filing-status threshold (MFJ 250k / MFS 125k / other 200k)", "line_type": "calculated"},
    {"line_number": "6", "description": "Subtract line 5 from line 4 (>= 0)", "line_type": "calculated"},
    {"line_number": "7", "description": "Additional Medicare Tax on Medicare wages. Line 6 x 0.9%", "line_type": "calculated"},
    {"line_number": "8", "description": "Self-employment income (Schedule SE Part I line 6; loss -> 0)", "line_type": "calculated"},
    {"line_number": "9", "description": "Filing-status threshold (same table)", "line_type": "calculated"},
    {"line_number": "10", "description": "Amount from line 4 (Medicare wages)", "line_type": "calculated"},
    {"line_number": "11", "description": "Subtract line 10 from line 9 (>= 0) — threshold reduced by Medicare wages", "line_type": "calculated"},
    {"line_number": "12", "description": "Subtract line 11 from line 8 (>= 0)", "line_type": "calculated"},
    {"line_number": "13", "description": "Additional Medicare Tax on SE income. Line 12 x 0.9%", "line_type": "calculated"},
    {"line_number": "14", "description": "RRTA compensation (W-2 box 14) — RED-defer", "line_type": "input"},
    {"line_number": "15", "description": "Filing-status threshold (RRTA) — RED-defer", "line_type": "calculated"},
    {"line_number": "16", "description": "Subtract line 15 from line 14 (>= 0) — RED-defer", "line_type": "calculated"},
    {"line_number": "17", "description": "Additional Medicare Tax on RRTA. Line 16 x 0.9% — RED-defer (v1 = 0)", "line_type": "calculated"},
    {"line_number": "18", "description": "Total Additional Medicare Tax. Add lines 7, 13, 17 -> Schedule 2 line 11", "line_type": "total"},
    {"line_number": "19", "description": "Medicare tax withheld (W-2 box 6)", "line_type": "input"},
    {"line_number": "20", "description": "Amount from line 1", "line_type": "calculated"},
    {"line_number": "21", "description": "Line 20 x 1.45% (regular Medicare withholding)", "line_type": "calculated"},
    {"line_number": "22", "description": "Subtract line 21 from line 19 (>= 0) — Additional Medicare withholding on wages", "line_type": "calculated"},
    {"line_number": "23", "description": "Additional Medicare withholding on RRTA (W-2 box 14) — RED-defer", "line_type": "input"},
    {"line_number": "24", "description": "Total Additional Medicare withholding. Add lines 22 and 23 -> Form 1040 line 25c", "line_type": "total"},
]

F8959_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_8959_001", "title": "Additional Medicare Tax applies (wages/SE over threshold)", "severity": "info",
     "condition": "line 4 (Medicare wages) + line 8 (SE income) > filing-status threshold",
     "message": ("Form 8959 Additional Medicare Tax applies: your combined Medicare wages and self-employment "
                 "income exceed the ${threshold} threshold for your filing status. The 0.9% tax flows to Schedule "
                 "2 line 11, and any extra 0.9% withholding flows to Form 1040 line 25c."),
     "notes": "Engage-gate explainer (the EIC engage-gate precedent). Not an error."},
    {"diagnostic_id": "D_8959_002", "title": "RRTA compensation — Additional Medicare on RRTA not supported", "severity": "error",
     "condition": "amt_rrta_compensation_l14 > 0 OR amt_rrta_addl_withheld_l23 > 0",
     "message": ("Not supported — prepare manually: Additional Medicare Tax on Railroad Retirement (RRTA) "
                 "compensation (Form 8959 Part III) is not modeled this sprint. Compute lines 14-17 (and the line "
                 "23 RRTA withholding) manually."),
     "notes": "RED-defer Part III RRTA (brief standing RED-defer)."},
    {"diagnostic_id": "D_8959_003", "title": "Additional Medicare withholding reconciled to Form 1040 line 25c", "severity": "info",
     "condition": "line 19 (Medicare tax withheld) > line 21 (1.45% x Medicare wages)",
     "message": ("Your employer withheld Additional Medicare Tax (Medicare withholding in W-2 box 6 exceeds 1.45% "
                 "of your Medicare wages). That extra amount (line 24) is added with your federal income tax "
                 "withholding on Form 1040 line 25c."),
     "notes": "Part V reconciliation -> 1040 line 25c. Informational."},
    {"diagnostic_id": "D_8959_004", "title": "Self-employment threshold reduced by Medicare wages", "severity": "info",
     "condition": "line 4 (Medicare wages) > 0 AND line 8 (SE income) > 0",
     "message": ("Because you have both Medicare wages and self-employment income, the Additional Medicare Tax "
                 "threshold for your SE income is reduced by your Medicare wages (line 11 = threshold - line 4). "
                 "Wages and SE income share a single filing-status threshold."),
     "notes": "The load-bearing Part II nuance. Informational."},
]

F8959_SCENARIOS: list[dict] = [
    {"scenario_name": "8959-T1 — high W-2 wages, single: box 5 = 250,000 -> Part I 450", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "filing_status": "single", "amt_medicare_wages_l1": 250000, "amt_se_income_l8": 0},
     "expected_outputs": {"line_4": 250000, "line_6": 50000, "line_7": 450.00, "line_18": 450.00},
     "notes": "L6=250,000-200,000=50,000; L7=50,000 x 0.9%=450 -> Sch 2 L11."},
    {"scenario_name": "8959-T2 — high SE income, single: SE 260,000 -> Part II (threshold reduced by 0 wages)", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"tax_year": 2025, "filing_status": "single", "amt_medicare_wages_l1": 0, "amt_se_income_l8": 260000},
     "expected_outputs": {"line_11": 200000, "line_12": 60000, "line_13": 540.00, "line_18": 540.00},
     "notes": "L11=200,000-0=200,000; L12=260,000-200,000=60,000; L13=540 -> Sch 2 L11."},
    {"scenario_name": "8959-T3 — both wages + SE, MFJ: wages 200,000 + SE 100,000 (shared threshold)", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "amt_medicare_wages_l1": 200000, "amt_se_income_l8": 100000},
     "expected_outputs": {"line_6": 0, "line_7": 0, "line_11": 50000, "line_12": 50000, "line_13": 450.00, "line_18": 450.00},
     "notes": ("MFJ threshold 250,000. Part I: wages 200,000 < 250,000 -> L7=0. Part II: L11=250,000-200,000=50,000; "
               "L12=100,000-50,000=50,000; L13=450. Total 450 — the shared threshold (D_8959_004).")},
    {"scenario_name": "8959-T4 — below threshold -> no tax (engage gate, D_8959_001 quiet)", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"tax_year": 2025, "filing_status": "single", "amt_medicare_wages_l1": 90000, "amt_se_income_l8": 40000},
     "expected_outputs": {"line_18": 0, "form_8959_engaged": False},
     "notes": "Wages 90,000 + SE 40,000 = 130,000 < 200,000 -> no Additional Medicare Tax; Schedule 2 line 11 untouched."},
    {"scenario_name": "8959-T5 — withholding reconciliation -> 1040 line 25c (D_8959_003)", "scenario_type": "normal", "sort_order": 5,
     "inputs": {"tax_year": 2025, "filing_status": "single", "amt_medicare_wages_l1": 250000, "amt_medicare_withheld_l19": 4025},
     "expected_outputs": {"line_21": 3625.00, "line_22": 400.00, "line_24": 400.00},
     "notes": "L21=250,000 x 1.45%=3,625; box 6 withheld 4,025 -> L22=400 extra Additional Medicare withholding -> 1040 L25c."},
]

F8959_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-8959-ENGAGE", "IRS_2025_8959_FORM", "primary", "Threshold engage gate"),
    ("R-8959-L4-L7", "IRS_2025_8959_FORM", "primary", "Part I lines 4-7"),
    ("R-8959-L11-L13", "IRS_2025_8959_FORM", "primary", "Part II lines 8-13 (threshold reduced by wages)"),
    ("R-8959-L18", "IRS_2025_8959_FORM", "primary", "Line 18 -> Schedule 2 line 11"),
    ("R-8959-L21-L24", "IRS_2025_8959_FORM", "primary", "Part V lines 19-24 -> 1040 line 25c"),
    ("R-8959-RRTA", "IRS_2025_8959_FORM", "primary", "Part III RRTA (RED-defer)"),
    ("R-8959-L4-L7", "IRS_TOPIC751_SE", "secondary", "0.9% Additional Medicare rate + thresholds"),
]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY FORM LINKS  (source_code, form_code, link_type)
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_SCHEDC_FORM", "SCHEDULE_C", "governs"),
    ("IRS_2025_SCHEDC_INSTR", "SCHEDULE_C", "informs"),
    ("IRS_2025_SCHEDSE_FORM", "SCHEDULE_SE", "governs"),
    ("IRS_TOPIC751_SE", "SCHEDULE_SE", "informs"),
    ("IRS_2025_8995_FORM", "8995", "governs"),
    ("IRS_2025_8995_INSTR", "8995", "governs"),
    ("RP_2025_32", "8995", "informs"),
    ("IRS_2025_8959_FORM", "8959", "governs"),
    ("IRS_TOPIC751_SE", "8959", "informs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORMS ROSTER
# ═══════════════════════════════════════════════════════════════════════════

FORMS: list[dict] = [
    {"identity": SCHEDC_IDENTITY, "facts": SCHEDC_FACTS, "rules": SCHEDC_RULES, "lines": SCHEDC_LINES,
     "diagnostics": SCHEDC_DIAGNOSTICS, "scenarios": SCHEDC_SCENARIOS, "rule_links": SCHEDC_RULE_LINKS},
    {"identity": SCHEDSE_IDENTITY, "facts": SCHEDSE_FACTS, "rules": SCHEDSE_RULES, "lines": SCHEDSE_LINES,
     "diagnostics": SCHEDSE_DIAGNOSTICS, "scenarios": SCHEDSE_SCENARIOS, "rule_links": SCHEDSE_RULE_LINKS},
    {"identity": F8995_IDENTITY, "facts": F8995_FACTS, "rules": F8995_RULES, "lines": F8995_LINES,
     "diagnostics": F8995_DIAGNOSTICS, "scenarios": F8995_SCENARIOS, "rule_links": F8995_RULE_LINKS},
    {"identity": F8959_IDENTITY, "facts": F8959_FACTS, "rules": F8959_RULES, "lines": F8959_LINES,
     "diagnostics": F8959_DIAGNOSTICS, "scenarios": F8959_SCENARIOS, "rule_links": F8959_RULE_LINKS},
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS  (staged in tts-tax-app until the assertions leg)
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-SCHC-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Schedule C line 31 net profit -> Schedule 1 line 3 AND Schedule SE line 2",
     "description": ("Validates R-SC-NETPROFIT. L31 = L29 - L30. The SAME L31 feeds Schedule 1 line 3 (sum all "
                     "businesses) and Schedule SE line 2 (sum per proprietor). Bug it catches: feeding one but "
                     "not the other, or summing across proprietors on Schedule SE."),
     "definition": {"kind": "flow_assertion", "form": "SCHEDULE_C",
                    "source_line": "31", "must_write_to": ["SCH_1.3", "SCHEDULE_SE.2"]},
     "sort_order": 1},
    {"assertion_id": "FA-1040-SCHC-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Schedule C COGS (line 42) -> line 4, and the gross-income chain",
     "description": ("Validates R-SC-COGS/R-SC-GROSSPROFIT. L40=sum(35..39); L42=L40-L41 -> L4; L5=L3-L4; L7=L5+L6. "
                     "Bug it catches: not subtracting ending inventory, or COGS not flowing to line 4."),
     "definition": {"kind": "formula_check", "form": "SCHEDULE_C",
                    "formula": "line_42 == (line_35+line_36+line_37+line_38+line_39) - line_41; line_4 == line_42"},
     "sort_order": 2},
    {"assertion_id": "FA-1040-SCHC-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Home-office simplified deduction = min(min(sqft,300)x$5, max(0, line 29))",
     "description": ("Validates R-SC-HOMEOFFICE (Decision 2). 300-sqft cap AND the gross-income limitation (cannot "
                     "create/increase a loss; no carryover). Bug it catches: missing the 300 cap, missing the "
                     "line-29 limit, or carrying the excess over."),
     "definition": {"kind": "formula_check", "form": "SCHEDULE_C",
                    "formula": "line_30 == min(min(sqft, 300) * 5, max(0, line_29))",
                    "constants": {"rate": 5, "max_sqft": 300}},
     "sort_order": 3},
    {"assertion_id": "FA-1040-SCHC-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Schedule C RED-defers each leave a RED (no silent gap)",
     "description": ("Validates the Schedule C RED-defer set: statutory employee (D_SC_001), line 32b at-risk "
                     "(D_SC_002), Form 8829 actual-expense (D_SC_007), invalid COGS (D_SC_003). Each fires a RED "
                     "rather than silently computing a wrong number."),
     "definition": {"kind": "gating_check", "form": "SCHEDULE_C",
                    "blockers": ["statutory_employee", "some_not_at_risk", "actual_expense_home_office", "invalid_cogs"],
                    "expect": {"red_fires": True}},
     "sort_order": 4},
    {"assertion_id": "FA-1040-SCHSE-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Schedule SE line 12 SE tax -> Schedule 2 line 4; line 13 1/2-SE -> Schedule 1 line 15",
     "description": ("Validates R-SE-L12/R-SE-L13. L12 = L10+L11 -> Sch 2 L4; L13 = L12 x 50% -> Sch 1 L15 (already "
                     "an EIC Worksheet-B + 8812 feeder). Bug it catches: a feeder not re-pointed when Sch 1 L15 / "
                     "Sch 2 L4 flip from direct-entry to computed."),
     "definition": {"kind": "flow_assertion", "form": "SCHEDULE_SE",
                    "checks": [{"source_line": "12", "must_write_to": ["SCH_2.4"]},
                               {"source_line": "13", "must_write_to": ["SCH_1.15"]}]},
     "sort_order": 5},
    {"assertion_id": "FA-1040-SCHSE-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Schedule SE math: 92.35% net earnings, 12.4% SS (capped), 2.9% Medicare (uncapped)",
     "description": ("Validates R-SE-L4A/L10/L11. L4a = L3 x 0.9235 (L3>0); L10 = min(L6,L9) x 12.4%; L11 = L6 x "
                     "2.9%. Bug it catches: applying the wage-base cap to the Medicare portion, or dropping the "
                     "92.35% factor."),
     "definition": {"kind": "formula_check", "form": "SCHEDULE_SE",
                    "formula": "line_4a == round(line_3*0.9235,2) if line_3>0 else line_3; line_10 == round(min(line_6,line_9)*0.124,2); line_11 == round(line_6*0.029,2)",
                    "constants": {"factor": 0.9235, "ss_rate": 0.124, "medicare_rate": 0.029, "floor": 400}},
     "sort_order": 6},
    {"assertion_id": "FA-1040-SCHSE-03", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "SE social-security wage base is year-keyed ($176,100 2025 / $184,500 2026)",
     "description": ("Pins SE_WAGE_BASE both years (line 7). The 12.4% SS portion is capped at this; the 2.9% "
                     "Medicare portion is uncapped. Bug it catches: a stale or carried-over wage base, or "
                     "year-keying the statutory 92.35/12.4/2.9/50 factors."),
     "definition": {"kind": "constants_check", "form": "SCHEDULE_SE",
                    "constants": {"wage_base_2025": 176100, "wage_base_2026": 184500,
                                  "ss_rate": 0.124, "medicare_rate": 0.029, "factor": 0.9235,
                                  "half": 0.50, "floor": 400, "applies_to_years": [2025, 2026]}},
     "sort_order": 7},
    {"assertion_id": "FA-1040-8995-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Form 8995 line 15 = min(line 10, line 14) -> Form 1040 line 13a",
     "description": ("Validates R-8995-L15. L10 = L5 + L9 (components); L14 = L13 x 20% (income limitation); "
                     "L15 = min(L10, L14) -> 1040 L13a. Bug it catches: taking max instead of min, or not applying "
                     "the income limitation."),
     "definition": {"kind": "formula_check", "form": "8995",
                    "formula": "line_15 == min(line_10, line_14)", "must_write_to": ["1040.13a"]},
     "sort_order": 8},
    {"assertion_id": "FA-1040-8995-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Form 8995 QBI reduced by 1/2-SE-tax / SEHI / SE-retirement",
     "description": ("Validates R-8995-QBI. Per-business QBI = Schedule C net profit - attributable (Sch 1 L15 + "
                     "Sch 1 L17 + Sch 1 L16). Bug it catches: using gross Schedule C net profit as QBI (overstating "
                     "the deduction)."),
     "definition": {"kind": "formula_check", "form": "8995",
                    "formula": "qbi_business == sch_c_net_profit - (half_se_tax + sehi + se_retirement)"},
     "sort_order": 9},
    {"assertion_id": "FA-1040-8995-03", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "8995-vs-8995A threshold is year-keyed; 20% rate is statutory",
     "description": ("Pins QBI_THRESHOLDS both years (above -> Form 8995-A RED) and the statutory 20% rate. "
                     "Bug it catches: a stale threshold, or year-keying the 20% rate. WALK ITEM 1: 2026 MFS $25 > other."),
     "definition": {"kind": "constants_check", "form": "8995",
                    "constants": {"2025": QBI_THRESHOLDS[2025], "2026": QBI_THRESHOLDS[2026],
                                  "rate": 0.20, "applies_to_years": [2025, 2026]}},
     "sort_order": 10},
    {"assertion_id": "FA-1040-8959-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Form 8959 line 18 -> Schedule 2 line 11; line 24 -> Form 1040 line 25c",
     "description": ("Validates R-8959-L18/R-8959-L21-L24. L18 = L7 + L13 + L17 -> Sch 2 L11; L24 = L22 + L23 -> "
                     "1040 L25c. Bug it catches: the total not feeding Schedule 2, or the withholding not feeding "
                     "1040 line 25c."),
     "definition": {"kind": "flow_assertion", "form": "8959",
                    "checks": [{"source_line": "18", "must_write_to": ["SCH_2.11"]},
                               {"source_line": "24", "must_write_to": ["1040.25c"]}]},
     "sort_order": 11},
    {"assertion_id": "FA-1040-8959-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Form 8959 Part II threshold is REDUCED BY Medicare wages (line 11 = threshold - line 4)",
     "description": ("Validates R-8959-L11-L13 — the load-bearing nuance. L11 = max(0, threshold - L4); L12 = "
                     "max(0, L8 - L11); L13 = L12 x 0.9%. Bug it catches: applying the full threshold to SE income "
                     "(double-counting the exemption when wages are also present)."),
     "definition": {"kind": "formula_check", "form": "8959",
                    "formula": "line_11 == max(0, threshold - line_4); line_12 == max(0, line_8 - line_11); line_13 == round(line_12*0.009,2)"},
     "sort_order": 12},
    {"assertion_id": "FA-1040-8959-03", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "Form 8959 thresholds NON-indexed ($250k MFJ / $125k MFS / $200k other); 0.9% rate",
     "description": ("Pins ADDL_MEDICARE_THRESHOLDS (same both years) + the 0.9% rate. Bug it catches: "
                     "'inflation-adjusting' the statutory thresholds, or a wrong rate."),
     "definition": {"kind": "constants_check", "form": "8959",
                    "constants": {"mfj": 250000, "mfs": 125000, "other": 200000,
                                  "rate": 0.009, "regular_medicare": 0.0145, "applies_to_years": [2025, 2026]}},
     "sort_order": 13},
    {"assertion_id": "FA-1040-TOPIC8-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Cross-form chain: Schedule C -> Schedule SE line 6 -> Form 8959 line 8",
     "description": ("Validates the SE-income chain into 8959 Part II. Schedule SE line 6 (net SE earnings) is "
                     "read by Form 8959 line 8 (loss -> 0). Bug it catches: 8959 reading the wrong SE line (e.g. "
                     "line 12 SE tax) instead of line 6."),
     "definition": {"kind": "flow_assertion", "form": "8959",
                    "reads_from": "SCHEDULE_SE.6", "target_line": "8"},
     "sort_order": 14},
]


# ═══════════════════════════════════════════════════════════════════════════
# Command
# ═══════════════════════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = (
        "Load the Schedule C / SE / 8995 / 8959 specs into Rule Studio (creates "
        "SCHEDULE_C, SCHEDULE_SE, re-authored 8995, 8959). Refuses to seed until "
        "Ken sets READY_TO_SEED=True."
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()

        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad SCHEDULE_C / SCHEDULE_SE / 8995 / 8959 specs (Topic 8)\n"))

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
        self._retire_stale_8995()
        self._upsert_form_links(sources)
        self._load_flow_assertions()
        self._report_totals()

    # ─────────────────────────────────────────────────────────────────────────
    # Safety guard
    # ─────────────────────────────────────────────────────────────────────────

    def _guard_against_hollow_seed(self):
        """Refuse to write anything until Ken has reviewed AND flipped READY_TO_SEED."""
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
                "\n"
                "REFUSING TO SEED SCHEDULE_C/SCHEDULE_SE/8995/8959: not cleared to seed.\n"
                "\n"
                "Content is authored, but seeding is gated until Ken reviews the packet\n"
                "(the verified constants BOTH years — SE wage base, 8995 thresholds, 8959\n"
                "thresholds; the 4 requires_human_review walk items — 2026 MFS 8995 split,\n"
                "multi-business QBI allocation, net-cap-gain/Schedule-D deferral, QBI loss\n"
                "carryforward; the cross-form flow map; and the RED-defer enumeration) and\n"
                "flips the sentinel.\n"
                "\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True to proceed)\n"
                "\n"
                "NOTE: seeding RE-AUTHORS Form 8995 — it retires the wrong stub artifacts\n"
                "(R001-R005, D001-D003, lines 1-8, the 3 stub tests) and writes the real\n"
                "17-line face.\n"
                "\n"
                "Currently empty / placeholder:\n"
                f"  {still_empty}\n"
                "\n"
                "To proceed: review the module-level data lists, then set READY_TO_SEED\n"
                "= True. Idempotent via update_or_create — safe to re-run after edits."
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Topics / sources (mirror load_1040_eic.py exactly)
    # ─────────────────────────────────────────────────────────────────────────

    def _load_topics(self):
        ct = 0
        for code, name in AUTHORITY_TOPICS:
            _, created = AuthorityTopic.objects.update_or_create(
                topic_code=code, defaults={"topic_name": name},
            )
            if created:
                ct += 1
        self.stdout.write(f"Topics: {ct} new ({len(AUTHORITY_TOPICS)} total in batch)")

    def _load_sources(self) -> dict[str, AuthoritySource]:
        sources: dict[str, AuthoritySource] = {}
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
                    AuthoritySourceTopic.objects.get_or_create(
                        authority_source=source, authority_topic=topic,
                    )
        for code in EXISTING_SOURCES_TO_REFERENCE:
            src = AuthoritySource.objects.filter(source_code=code).first()
            if src:
                sources[code] = src
        self.stdout.write(f"Sources ready: {len(sources)}")
        return sources

    def _load_new_excerpts_on_existing(self, sources):
        ct = 0
        for code, exc in NEW_EXCERPTS_ON_EXISTING:
            src = sources.get(code) or AuthoritySource.objects.filter(source_code=code).first()
            if not src:
                self.stdout.write(self.style.WARNING(
                    f"  source {code} not found — skipping new excerpt"
                ))
                continue
            exc = dict(exc)
            AuthorityExcerpt.objects.update_or_create(
                authority_source=src, excerpt_label=exc["excerpt_label"], defaults=exc,
            )
            ct += 1
        if ct:
            self.stdout.write(f"  {ct} new excerpts on existing sources")

    # ─────────────────────────────────────────────────────────────────────────
    # Per-form helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _upsert_form(self, identity: dict) -> TaxForm:
        form, created = TaxForm.objects.update_or_create(
            form_number=identity["form_number"],
            jurisdiction=FORM_JURISDICTION,
            tax_year=FORM_TAX_YEAR,
            version=FORM_VERSION,
            defaults={
                "form_title": identity["form_title"],
                "entity_types": FORM_ENTITY_TYPES,
                "status": FORM_STATUS,
                "notes": identity["notes"],
            },
        )
        self.stdout.write(f"{'Created' if created else 'Updated'} {identity['form_number']}")
        return form

    def _upsert_facts(self, form, facts):
        for f in facts:
            f = dict(f)
            FormFact.objects.update_or_create(
                tax_form=form, fact_key=f.pop("fact_key"), defaults=f,
            )
        self.stdout.write(f"  {len(facts)} facts")

    def _upsert_rules(self, form, rules_data) -> dict[str, FormRule]:
        created = {}
        for r in rules_data:
            r = dict(r)
            rule, _ = FormRule.objects.update_or_create(
                tax_form=form, rule_id=r.pop("rule_id"), defaults=r,
            )
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
            FormLine.objects.update_or_create(
                tax_form=form, line_number=ln.pop("line_number"), defaults=ln,
            )
        self.stdout.write(f"  {len(lines)} lines")

    def _upsert_diagnostics(self, form, diagnostics):
        for d in diagnostics:
            d = dict(d)
            FormDiagnostic.objects.update_or_create(
                tax_form=form, diagnostic_id=d.pop("diagnostic_id"), defaults=d,
            )
        self.stdout.write(f"  {len(diagnostics)} diagnostics")

    def _upsert_tests(self, form, scenarios):
        for t in scenarios:
            t = dict(t)
            TestScenario.objects.update_or_create(
                tax_form=form, scenario_name=t.pop("scenario_name"), defaults=t,
            )
        self.stdout.write(f"  {len(scenarios)} test scenarios")

    # ─────────────────────────────────────────────────────────────────────────
    # 8995 re-author — retire the wrong early-draft stub artifacts
    # ─────────────────────────────────────────────────────────────────────────

    def _retire_stale_8995(self):
        """Delete any 8995 artifact NOT in the re-authored sets (the wrong stub:
        rules R001-R005, diags D001-D003, lines 1-8, the 3 stub tests, stale facts).
        Runs AFTER the upsert so the new face is in place; idempotent (no-op on re-run).
        """
        form = TaxForm.objects.filter(
            form_number="8995", jurisdiction=FORM_JURISDICTION,
            tax_year=FORM_TAX_YEAR, version=FORM_VERSION,
        ).first()
        if not form:
            return

        keep_facts = {f["fact_key"] for f in F8995_FACTS}
        keep_rules = {r["rule_id"] for r in F8995_RULES}
        keep_lines = {ln["line_number"] for ln in F8995_LINES}
        keep_diags = {d["diagnostic_id"] for d in F8995_DIAGNOSTICS}
        keep_tests = {t["scenario_name"] for t in F8995_SCENARIOS}

        removed = {}
        removed["facts"] = FormFact.objects.filter(tax_form=form).exclude(fact_key__in=keep_facts).delete()[0]
        removed["rules"] = FormRule.objects.filter(tax_form=form).exclude(rule_id__in=keep_rules).delete()[0]
        removed["lines"] = FormLine.objects.filter(tax_form=form).exclude(line_number__in=keep_lines).delete()[0]
        removed["diagnostics"] = FormDiagnostic.objects.filter(tax_form=form).exclude(diagnostic_id__in=keep_diags).delete()[0]
        removed["tests"] = TestScenario.objects.filter(tax_form=form).exclude(scenario_name__in=keep_tests).delete()[0]

        total = sum(removed.values())
        if total:
            self.stdout.write(self.style.WARNING(
                f"  8995 stub retired: {removed} ({total} stale rows deleted — RuleAuthorityLinks cascade)"
            ))
        else:
            self.stdout.write("  8995 stub: nothing stale to retire (clean re-author)")

    def _upsert_form_links(self, sources):
        for source_code, form_code, link_type in AUTHORITY_FORM_LINKS:
            source = sources.get(source_code) or AuthoritySource.objects.filter(
                source_code=source_code,
            ).first()
            if source:
                AuthorityFormLink.objects.get_or_create(
                    authority_source=source, form_code=form_code, link_type=link_type,
                    defaults={"note": f"{source_code} -> {form_code}"},
                )

    def _load_flow_assertions(self):
        for a in FLOW_ASSERTIONS:
            a = dict(a)
            FlowAssertion.objects.update_or_create(
                assertion_id=a.pop("assertion_id"), defaults=a,
            )
        self.stdout.write(f"  {len(FLOW_ASSERTIONS)} flow assertions")

    # ─────────────────────────────────────────────────────────────────────────
    # Report
    # ─────────────────────────────────────────────────────────────────────────

    def _report_totals(self):
        def _safe(text):
            return text.encode("ascii", errors="replace").decode("ascii")

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("DATABASE TOTALS (after load_1040_schedule_c)")
        self.stdout.write("=" * 60)
        self.stdout.write(f"TaxForms:           {TaxForm.objects.count()}")
        self.stdout.write(f"FormFacts:          {FormFact.objects.count()}")
        self.stdout.write(f"FormRules:          {FormRule.objects.count()}")
        self.stdout.write(f"FormLines:          {FormLine.objects.count()}")
        self.stdout.write(f"FormDiagnostics:    {FormDiagnostic.objects.count()}")
        self.stdout.write(f"TestScenarios:      {TestScenario.objects.count()}")
        self.stdout.write(f"AuthoritySources:   {AuthoritySource.objects.count()}")
        self.stdout.write(f"AuthorityExcerpts:  {AuthorityExcerpt.objects.count()}")
        self.stdout.write(f"RuleAuthorityLinks: {RuleAuthorityLink.objects.count()}")
        self.stdout.write(f"AuthorityFormLinks: {AuthorityFormLink.objects.count()}")
        self.stdout.write(f"FlowAssertions:     {FlowAssertion.objects.count()}")

        for fn in ("SCHEDULE_C", "SCHEDULE_SE", "8995", "8959"):
            all_rules = FormRule.objects.filter(tax_form__form_number=fn)
            uncited = [r for r in all_rules if not r.authority_links.exists()]
            if uncited:
                self.stdout.write(self.style.WARNING(
                    f"\n{fn} rules with ZERO authority links: {len(uncited)}"
                ))
                for r in uncited[:20]:
                    self.stdout.write(_safe(f"  {r.rule_id}: {r.title}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"{fn}: all rules have authority links."))
