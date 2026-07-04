"""Load the Form 8995-A spec — QBI deduction ABOVE the §199A threshold.

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
Form 8995-A (Qualified Business Income Deduction) is the FULL-computation QBI
form used when taxable income before the QBI deduction is ABOVE the §199A
threshold ($197,300 / $394,600 MFJ for 2025). Below the threshold the simplified
Form 8995 (already seeded — see load_1040_schedule_c.py FORM 3) applies and the
SSTB / W-2-wage / UBIA limitations are irrelevant. Above the threshold those
limitations bite, and Form 8995-A is required.

This loader RE-AUTHORS the existing thin `8995A` draft (a hand-authored
conceptual skeleton: 20 facts / 6 rules / 15 lines whose line numbers do NOT
match the real form) into the real 2025 face, verified against the IRS PDF +
i8995a instructions (NOT memory). `_retire_stale_8995a` drops the draft
artifacts on seed.

SCOPE (Ken-approved kickoff, AskUserQuestion 2026-06-23):
  • Parts I–IV (per-business W-2/UBIA limit → phase-in → income limit → 1040 L13)  = IN
  • Schedule A (SSTB applicable-% phase-in)                                         = IN
  • Schedule B (aggregation of business operations — FULL engine)                   = IN
  • Schedule C (per-business loss netting + carryforward)                           = IN
  • Schedule D (patron reduction L14 + capped DPAD §199A(g) L38)                    = IN (built 2026-07-03, Ken ruling — MeF ATS S2)

═══════════════════════════════════════════════════════════════════════════
VERIFIED FORM STRUCTURE (2025 f8995a.pdf — read directly; i8995a 12pp)
═══════════════════════════════════════════════════════════════════════════
Part I  (rows A/B/C; >3 → attached worksheets): (a) name, (b) SSTB ✓, (c) aggregation ✓,
        (d) TIN, (e) patron ✓.
Part II (cols A/B/C, per business):
   2  QBI from the trade/business/aggregation
   3  L2 × 20%   (if TI ≤ threshold, skip 4–12, enter L3 on L13)
   4  Allocable W-2 wages
   5  L4 × 50%
   6  L4 × 25%
   7  Allocable UBIA of qualified property
   8  L7 × 2.5%
   9  L6 + L8
  10  greater of L5 or L9
  11  W-2/UBIA limitation = smaller of L3 or L10
  12  Phased-in reduction = amount from L26 (Part III), if any
  13  greater of L11 or L12
  14  Patron reduction (Schedule D L6)                     [COMPUTED 2026-07-03]
  15  L13 − L14   (QBI component)
  16  Σ L15 across all businesses (Total QBI component)
Part III (cols A/B/C — ONLY if TI in band AND L10 < L3):
  17  amounts from L3
  18  amounts from L10
  19  L17 − L18
  20  Taxable income before QBI deduction
  21  Threshold (197,300 / 394,600 MFJ)
  22  L20 − L21
  23  Phase-in range (50,000 / 100,000 MFJ)
  24  L22 ÷ L23  (phase-in %)
  25  L19 × L24
  26  L17 − L25  → enter on L12 for the corresponding business
Part IV (single column):
  27  Total QBI component (from L16)
  28  Qualified REIT dividends + PTP income/(loss)
  29  REIT/PTP (loss) carryforward from prior years  (negative)
  30  combine 28+29; if <0 enter 0
  31  L30 × 20%  (REIT/PTP component)
  32  L27 + L31  (QBI deduction before income limit)
  33  Taxable income before QBI deduction
  34  net capital gain + qualified dividends
  35  L33 − L34  (≥0)
  36  L35 × 20%  (income limitation)
  37  smaller of L32 or L36  (before DPAD)
  38  DPAD §199A(g) from ag/hort coop                      [RED-defer]
  39  L37 + L38  → Form 1040 line 13   (TOTAL QBI DEDUCTION)
  40  REIT/PTP (loss) carryforward out = combine 28+29; if ≥0 enter 0  (negative)

Schedule A (SSTB) — complete only if the business IS an SSTB and TI is in the
  phase-in band. applicable % = (ceiling − TI) / range, clamped to [0,1]
  (= 100% − phase-in%). Reduce the SSTB's QBI, W-2 wages, AND UBIA by the
  applicable % BEFORE they flow to Part II (lines 2/4/7). Above the ceiling
  (TI > 247,300 / 494,600) the SSTB is EXCLUDED (applicable % = 0 → all zero).
  Part I of Sch A = non-PTP SSTBs; Part II = PTP SSTBs (i8995a).
Schedule B (Aggregation) — combine QBI, W-2 wages, and UBIA across an aggregated
  group, treated as ONE column in Part I/II. Eligibility (§1.199A-4): (1) 50%+
  common ownership for a majority of the year incl. the last day + same tax-year
  end; (2) none is an SSTB; (3) ≥2 of 3 factors (same/customary products;
  shared facilities/centralized elements; operated in coordination). Ownership
  and factor tests are preparer-asserted (not on the return); none-SSTB is
  checkable. An RPE's aggregation must be carried forward and may be added to.
Schedule C (Loss Netting) — when any business has a current-year QB loss OR a
  prior-year QB net-loss carryforward: apportion the TOTAL loss (current + prior)
  across the POSITIVE-QBI businesses pro-rata by their QBI; the adjusted QBI
  (line 1 col (c)) flows to Part II line 2. If a business's adjusted QBI ≤ 0
  after netting, its W-2 wages AND UBIA must be ZERO. A net negative
  (loss > positive QBI) carries forward (line 6 → next year's Sch C line 2 /
  Form 8995 line 3).

═══════════════════════════════════════════════════════════════════════════
requires_human_review WALK ITEMS (for Ken's in-session review)
═══════════════════════════════════════════════════════════════════════════
W1. Schedule A applicable %: = (ceiling − TI)/range, the fraction of QBI/W-2/UBIA
    RETAINED (decreasing 100%→0% across the band). Confirm direction + that it
    reduces ALL THREE (QBI, W-2 wages, UBIA), and that an in-band SSTB then ALSO
    gets the Part III phase-in on the already-reduced amounts (the two stack).
W2. Schedule C loss apportionment: total QB loss (current-year losses + prior
    carryforward) apportioned pro-rata by QBI across positive-QBI businesses;
    adjusted QBI ≤ 0 ⇒ that business's W-2/UBIA = 0; net negative ⇒ line-6
    carryforward (negative). Confirm.
W3. Schedule B aggregation (FULL engine per Ken): 50%-ownership + 2-of-3-factor
    tests are preparer-asserted; none-SSTB is enforced (an SSTB in an aggregation
    = error). Combine QBI/W-2/UBIA. Confirm the asserted-vs-enforced split.
W4. Patron reduction (L14) + DPAD §199A(g) (L38) — Schedule D BUILT 2026-07-03
    (Ken ruled build-it for the MeF ATS S2 scenario leg; superseded the v1
    RED-defer). Per patron business: SD6 = min(9% × allocable QBI, 50% × allocable
    W-2 wages) → L14; patron routes to 8995-A at ANY income with the face line-3
    skip at/below the threshold; L38 capped at L33 − L37 (face verbatim).
    D_8995A_001/002 repurposed error → info; new guards D_8995A_008/009.
W5. Line 34 net capital gain = qualified dividends (1040 L3a) + net capital gain
    (Schedule D min(15,16), else 1040 L7) — IDENTICAL to the simplified-8995 L12
    sourcing (already Ken-approved 2026-06-13). Confirm reuse.
W6. Phase-in range $50,000 / $100,000 MFJ is STATUTORY NON-INDEXED (§199A(b)(3)
    (B)(ii)); the ceiling is derived (threshold + range), so it is year-keyed via
    the threshold. Confirm.
W7. No public fillable Schedule A/B/C PDF exists (the irs.gov f8995a.pdf is the
    2-page main form only; standalone schedule PDFs 404). The schedules are
    authored here at the COMPUTATIONAL level (math verified vs §199A + i8995a);
    the exact schedule PDF widget layout is verified at the RENDER leg. The main
    form Parts I–IV ARE verified exactly from the PDF. Confirm acceptable.

═══════════════════════════════════════════════════════════════════════════
SAFETY GUARD — READY_TO_SEED stays False until Ken approves the review walk
in-session. Until then the command refuses to write to the DB (zero writes).
DO NOT relax the guard to silence the error.
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
# SAFETY GUARD — flip ONLY after Ken's in-session review walk (W1–W7 above,
# the verified constants both years, the cross-form flow map, the RED-defer
# enumeration). Until then the command writes nothing.
#
# FLIPPED 2026-06-23 — Ken APPROVED the review walk in-session ("Approve & seed"):
# W1–W7 blessed as drafted (Schedule A applicable % reduces QBI/W-2/UBIA and stacks
# with the Part III phase-in; Schedule C loss apportioned pro-rata by QBI with
# W-2/UBIA zeroed on netted-to-≤0 businesses; Schedule B full aggregation with
# ownership/factors asserted + none-SSTB enforced; patron/DPAD RED-deferred; line-34
# net cap gain reuses the simplified-8995 sourcing; phase-in range $50k/$100k
# non-indexed; schedule PDF widget layout verified at the render leg). Math gate
# check_8995a_integrity.py ALL PASS (10 scenarios re-derived).
# ═══════════════════════════════════════════════════════════════════════════
READY_TO_SEED = True


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1040"]


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS (every value cited; never training memory)
# ═══════════════════════════════════════════════════════════════════════════

# §199A QBI rate — statutory, NON-indexed.
QBI_RATE = 0.20

# §199A threshold — YEAR-INDEXED (same table as the simplified 8995 loader).
#   2025 i8995a: $394,600 MFJ / $197,300 all other.
#   2026 RP 2025-32 §4.26: $403,500 MFJ / $201,775 MFS / $201,750 other.
QBI_THRESHOLDS: dict[int, dict] = {
    2025: {"mfj": 394600, "mfs": 197300, "other": 197300},
    2026: {"mfj": 403500, "mfs": 201775, "other": 201750},
}

# Phase-in range — STATUTORY NON-INDEXED (§199A(b)(3)(B)(ii): "$50,000
# ($100,000 in the case of a joint return)"). MFS = $50,000 (not joint).
PHASE_IN_RANGE: dict[str, int] = {"mfj": 100000, "mfs": 50000, "other": 50000}


def _status_key(filing_status: str) -> str:
    if filing_status in ("mfj", "mfs"):
        return filing_status
    return "other"


def threshold_for(year: int, status: str) -> int:
    table = QBI_THRESHOLDS.get(year) or QBI_THRESHOLDS[2026]
    return table[_status_key(status)]


def phase_in_range_for(status: str) -> int:
    return PHASE_IN_RANGE[_status_key(status)]


def ceiling_for(year: int, status: str) -> int:
    return threshold_for(year, status) + phase_in_range_for(status)


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY TOPICS
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    # NOTE: "qbi_deduction" already exists (created by load_1040_schedule_c.py) —
    # not re-declared here so its label isn't clobbered; the source-topic link
    # below resolves it by lookup. Only the new above-threshold topic is created.
    ("qbi_above_threshold", "Form 8995-A — above-threshold QBI: W-2/UBIA limit, SSTB phase-out, aggregation, loss netting"),
]

# Existing sources to REUSE (looked up, not modified). IRC_199A and
# IRS_2025_8995A_INSTR were seeded with the 8995A draft (forms_supporting.py /
# irc_sections.py). RP_2025_32 carries the TY2026 thresholds.
EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRC_199A",
    "IRS_2025_8995A_INSTR",
    "RP_2025_32",
    "IRS_2025_1040_FORM",
]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY SOURCES (CREATE) — the form-face transcription
# Transcribed 2026-06-23 from the on-disk resources/irs_forms/2025/f8995a.pdf
# (read directly) + i8995a.pdf. requires_human_review=False (verbatim).
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_8995A_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "2025 Form 8995-A — Qualified Business Income Deduction (full computation)",
        "citation": "Form 8995-A (2025); f8995a.pdf; Attachment Sequence No. 55A",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f8995a.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["qbi_deduction", "qbi_above_threshold"],
        "excerpts": [
            {
                "excerpt_label": "Form 8995-A Parts I–IV (2025) — verified line face",
                "excerpt_text": (
                    "Part I rows A/B/C: (a) name, (b) check if specified service, (c) check if aggregation, "
                    "(d) TIN, (e) check if patron. Part II (cols A/B/C): 2 QBI; 3 = L2×20% (if TI ≤ threshold "
                    "skip 4–12, L3→L13); 4 W-2 wages; 5 = L4×50%; 6 = L4×25%; 7 UBIA; 8 = L7×2.5%; 9 = L6+L8; "
                    "10 greater of L5 or L9; 11 = smaller of L3 or L10; 12 phased-in reduction (from L26); "
                    "13 greater of L11 or L12; 14 patron reduction (Sch D L6); 15 = L13−L14; 16 = ΣL15. "
                    "Part III (only if TI > 197,300 but ≤ 247,300 / 394,600–494,600 MFJ AND L10 < L3): "
                    "17 from L3; 18 from L10; 19 = L17−L18; 20 TI before QBI; 21 threshold; 22 = L20−L21; "
                    "23 phase-in range (50,000 / 100,000 MFJ); 24 = L22÷L23; 25 = L19×L24; 26 = L17−L25 → L12. "
                    "Part IV: 27 from L16; 28 REIT/PTP income/(loss); 29 REIT/PTP carryforward (neg); "
                    "30 = max(0, 28+29); 31 = L30×20%; 32 = L27+L31; 33 TI before QBI; 34 net cap gain + qual "
                    "dividends; 35 = max(0, L33−L34); 36 = L35×20%; 37 = smaller of L32 or L36; 38 DPAD §199A(g); "
                    "39 = L37+L38 → Form 1040 line 13; 40 REIT/PTP carryforward out = min(0, 28+29)."
                ),
                "summary_text": "Form 8995-A Parts I–IV: per-business W-2/UBIA limit → phase-in → income limit → 1040 L13.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Use-this-form-if threshold + Part III trigger (2025)",
                "excerpt_text": (
                    "Use Form 8995-A if taxable income, before the QBI deduction, is above $197,300 ($394,600 "
                    "MFJ), or you're a patron of an agricultural or horticultural cooperative. Complete Part III "
                    "only if taxable income is more than $197,300 but not $247,300 ($394,600 and $494,600 if MFJ) "
                    "and line 10 is less than line 3. Otherwise, skip Part III."
                ),
                "summary_text": "Above $197,300/$394,600 → 8995-A. Part III phase-in only in-band AND when the wage limit binds.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Line 3 below-threshold skip + line 38 DPAD cap (2025 face, verbatim)",
                "excerpt_text": (
                    "Line 3: Multiply line 2 by 20% (0.20). If your taxable income is $197,300 or less ($394,600 "
                    "if married filing jointly), skip lines 4 through 12 and enter the amount from line 3 on "
                    "line 13. Line 14: Patron reduction. Enter the amount from Schedule D (Form 8995-A), line 6, "
                    "if any. See instructions. Line 15: Qualified business income component. Subtract line 14 "
                    "from line 13. Line 38: DPAD under section 199A(g) allocated from an agricultural or "
                    "horticultural cooperative. Don't enter more than line 33 minus line 37."
                ),
                "summary_text": "Below threshold: skip L4–12, L13 = L3 (no W-2/UBIA limit). L14 ← Sch D L6. L38 capped at L33 − L37.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_8995A_SCHD_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "Schedule D (Form 8995-A) — Special Rules for Patrons of Agricultural or Horticultural Cooperatives (Rev. Dec 2022, current for TY2025)",
        "citation": "Schedule D (Form 8995-A) (Rev. 12-2022); f8995ad.pdf; Attachment Sequence No. 55E; Cat. No. 72683Z",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f8995ad.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["qbi_deduction", "qbi_patron_reduction"],
        "excerpts": [
            {
                "excerpt_label": "Schedule D (8995-A) full face (Rev. 12-2022, verbatim; fetched 2026-07-03)",
                "excerpt_text": (
                    "Complete Schedule D only if you're a patron of an agricultural or horticultural cooperative. "
                    "If you have more than three trades, businesses, or aggregations, attach as many Schedules D "
                    "as needed. Columns A/B/C: 1a Trade, business, or aggregation name; 1b Taxpayer identification "
                    "number; 2 Qualified business income allocable to qualified payments received from "
                    "cooperative; 3 Multiply line 2 by 9% (0.09); 4 W-2 wages from trade or business allocable to "
                    "the qualified payments; 5 Multiply line 4 by 50% (0.50); 6 Patron reduction. Enter the "
                    "smaller of line 3 or line 5. Enter this amount on Form 8995-A, line 14, for the "
                    "corresponding trade, business, or aggregation."
                ),
                "summary_text": "Sch D per business: L6 patron reduction = min(9% × allocable QBI, 50% × allocable W-2 wages) → 8995-A L14.",
                "is_key_excerpt": True,
            },
        ],
    },
]

# New excerpts to attach to the EXISTING i8995a source (the schedule mechanics).
NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = [
    ("IRS_2025_8995A_INSTR", {
        "excerpt_label": "Schedule C (8995-A) loss netting — apportion by QBI; zero-out W-2/UBIA",
        "excerpt_text": (
            "Schedule C offsets a trade/business that generated a qualified business loss against the QBI from "
            "your other trades or businesses. The qualified business loss must be apportioned among all your "
            "trades or businesses with QBI in proportion to their QBI. Line 1(b): apportion the amount from line 5 "
            "among all your trades or businesses with QBI, but not loss, in proportion to their QBI. Line 1(c): "
            "enter on the corresponding line on Form 8995-A, Part II. Note: if the adjusted QBI is zero or less "
            "after the reduction for loss netting, the W-2 wages and UBIA of qualified property must be zero for "
            "that trade or business. Line 6 carries to next year's Schedule C line 2 or Form 8995 line 3."
        ),
        "summary_text": "Sch C: apportion the loss pro-rata by QBI; adjusted QBI ≤ 0 ⇒ W-2/UBIA = 0; line 6 carries forward.",
        "is_key_excerpt": True,
    }),
    ("IRS_2025_8995A_INSTR", {
        "excerpt_label": "Schedule B (8995-A) aggregation — eligibility + combine",
        "excerpt_text": (
            "You may aggregate multiple trades or businesses into a single trade or business for applying the "
            "W-2 wage/UBIA limitation if: (1) you or a group own 50% or more of each for a majority of the tax "
            "year including the last day, and all use the same tax-year end; (2) none is an SSTB; (3) they meet "
            "at least two of: (a) same/customary products or services; (b) shared facilities or centralized "
            "elements; (c) operated in coordination/reliance. You must combine the QBI, W-2 wages, and UBIA of "
            "qualified property for all aggregated trades or businesses for purposes of the limitations. "
            "Complete Schedule B before starting Part I."
        ),
        "summary_text": "Sch B: 50% ownership + none-SSTB + 2-of-3 factors; combine QBI/W-2/UBIA across the group.",
        "is_key_excerpt": True,
    }),
    ("IRS_2025_8995A_INSTR", {
        "excerpt_label": "Schedule D (8995-A) patron rules — routing, qualified payments, L14 (2025, verbatim)",
        "excerpt_text": (
            "Who Can Take the Deduction: use Form 8995-A if you have QBI and your taxable income before the QBI "
            "deduction is more than $394,600 MFJ / $197,300 all other returns, OR you're a patron in a specified "
            "agricultural or horticultural cooperative. Otherwise use Form 8995. If your taxable income is at or "
            "below the threshold, you don't need to reduce your QBI. You must complete Schedule D (Form 8995-A) "
            "if you're a patron in a specified agricultural or horticultural cooperative and are claiming a QBI "
            "deduction in relation to your trade or business conducted with the cooperative. A specified "
            "agricultural or horticultural cooperative is a cooperative that markets or is engaged in the "
            "manufacturing, production, growth, or extraction of any agricultural or horticultural products to "
            "which Part I of subchapter T applies. See section 199A(g)(3). Also see T.D. 9947. Schedule D "
            "Line 2: Input the QBI for the trade or business as properly allocable to qualified payments "
            "received from the cooperative. Qualified payments include patronage dividends and per-unit retains "
            "allocations. Schedule D Line 4: Enter the portion of W-2 wages from Form 8995-A, line 4, that are "
            "allocable to the qualified payments. Form 8995-A Line 14: Report the amount from Schedule D "
            "(Form 8995-A), line 6, if any. Patrons of agricultural or horticultural cooperatives are required "
            "to reduce their QBI component by the lesser of: 9% of QBI allocable to qualified payments from a "
            "specified cooperative, or 50% of W-2 wages allocable to qualified payments. Line 15: Subtract the "
            "patron reduction on line 14 from the amount on line 13. If zero or less, enter zero. Line 39: Enter "
            "the amount from line 39 on Form 1040 or 1040-SR, line 13a."
        ),
        "summary_text": "Patron → 8995-A at ANY income; at/below threshold no QBI reduction; Sch D L2 = QBI allocable to qualified payments (patronage dividends + per-unit retains); L14 = lesser of 9%/50%.",
        "is_key_excerpt": True,
    }),
    ("IRS_2025_8995A_INSTR", {
        "excerpt_label": "Schedule A (8995-A) SSTB + line 34 net capital gain",
        "excerpt_text": (
            "Complete Schedule A only if your trade or business is an SSTB and your taxable income is more than "
            "$197,300 but not $247,300 ($394,600 and $494,600 if MFJ). If taxable income is more than $247,300 "
            "($494,600 MFJ), your SSTB doesn't qualify for the deduction. Schedule A Part II is used for SSTBs "
            "that are PTPs; Part I for all other SSTBs. Line 34 (Part IV): Form 1040 filers — your qualified "
            "dividends on line 3a, plus your net capital gain (if filing Schedule D, the smaller of Schedule D "
            "line 15 or 16, unless line 15 or 16 is zero or less)."
        ),
        "summary_text": "Sch A: in-band SSTB → applicable-% reduction; above ceiling → excluded. Line 34 = qual div + net cap gain.",
        "is_key_excerpt": True,
    }),
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_8995A_FORM", "8995A", "defines"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 8995-A — FACTS
# ═══════════════════════════════════════════════════════════════════════════

F8995A_FACTS: list[dict] = [
    # ── Per-business inputs (model-driven: ScheduleC / ScheduleF / ScheduleK1) ──
    {"fact_key": "a_business_qbi", "label": "Line 2 — QBI per trade/business/aggregation (model-driven)",
     "data_type": "decimal", "default_value": "0", "sort_order": 1,
     "notes": ("PER BUSINESS (column). = the §199A QBI for the business (Schedule C/F net reduced by "
               "attributable 1/2-SE/SEHI/SE-retirement; K-1 §199A QBI). After Schedule A (SSTB) and Schedule C "
               "(loss netting) adjustments. Flows to Part II line 2.")},
    {"fact_key": "a_business_w2_wages", "label": "Line 4 — allocable W-2 wages per business",
     "data_type": "decimal", "default_value": "0", "sort_order": 2,
     "notes": ("PER BUSINESS. NEW per-business input (no model field existed — added at the seed leg on "
               "ScheduleC/ScheduleF/ScheduleK1). K-1: box 17V (1120-S) / box 20 (1065) §199A W-2 wages. "
               "If adjusted QBI ≤ 0 after loss netting, must be 0 (i8995a).")},
    {"fact_key": "a_business_ubia", "label": "Line 7 — allocable UBIA of qualified property per business",
     "data_type": "decimal", "default_value": "0", "sort_order": 3,
     "notes": ("PER BUSINESS. NEW per-business input. UBIA = unadjusted basis immediately after acquisition of "
               "depreciable property within its depreciable period (later of 10 yrs / recovery period). "
               "If adjusted QBI ≤ 0 after loss netting, must be 0.")},
    {"fact_key": "a_business_is_sstb", "label": "Part I col (b) — specified service trade/business (SSTB)",
     "data_type": "boolean", "sort_order": 4,
     "notes": ("PER BUSINESS. Preparer-asserted (facts-and-circumstances). Drives Schedule A: in-band SSTB gets "
               "the applicable-% reduction; above-ceiling SSTB is EXCLUDED (QBI/W-2/UBIA = 0). An SSTB may not be "
               "in an aggregation (Schedule B eligibility).")},
    {"fact_key": "a_business_is_patron", "label": "Part I col (e) — patron of an ag/hort cooperative",
     "data_type": "boolean", "sort_order": 5,
     "notes": ("PER BUSINESS. Routes the return to Form 8995-A at ANY income (i8995a 2025 'Who Can Take the "
               "Deduction') and engages Schedule D (patron reduction → L14). COMPUTED since 2026-07-03 "
               "(Ken ruling, MeF S2): R-8995A-PATRON. Specified ag/hort co-op per §199A(g)(3) / T.D. 9947.")},
    {"fact_key": "a_business_schd_qbi_alloc", "label": "Schedule D line 2 — QBI allocable to qualified payments from the cooperative",
     "data_type": "decimal", "default_value": "0", "sort_order": 9,
     "notes": ("PER BUSINESS (patron only). Preparer-entered: the portion of the business's QBI properly "
               "allocable to qualified payments (patronage dividends + per-unit retains allocations, "
               "Form 1099-PATR). Blank/0 with the patron flag set → patron reduction $0 + D_8995A_001 "
               "(info) asks the preparer to confirm no qualified payments.")},
    {"fact_key": "a_business_schd_wages_alloc", "label": "Schedule D line 4 — W-2 wages allocable to the qualified payments",
     "data_type": "decimal", "default_value": "0", "sort_order": 10,
     "notes": ("PER BUSINESS (patron only). The portion of Form 8995-A line 4 W-2 wages allocable to the "
               "qualified payments. Must not exceed the business's line 4 wages (D_8995A_009). A zero-wage "
               "business ⇒ reduction $0 (the 50% arm is the lesser) — §199A(b)(7)(B).")},
    {"fact_key": "a_aggregation_group", "label": "Part I col (c) — aggregation group id (Schedule B)",
     "data_type": "string", "sort_order": 6,
     "notes": ("PER BUSINESS. Blank = stands alone; a shared group id (e.g. 'AGG1') aggregates the businesses "
               "into one Part I/II column (Schedule B). Full aggregation engine (Ken 2026-06-23).")},
    # ── Schedule B aggregation eligibility (per group; preparer-asserted) ──
    {"fact_key": "a_agg_ownership_50pct", "label": "Schedule B — 50%+ common ownership for a majority of the year (asserted)",
     "data_type": "boolean", "sort_order": 7,
     "notes": "PER GROUP. §1.199A-4(b)(1)(i). Preparer-asserted (ownership data not on the return). Required to aggregate."},
    {"fact_key": "a_agg_factors_met", "label": "Schedule B — ≥2 of 3 aggregation factors met (asserted)",
     "data_type": "boolean", "sort_order": 8,
     "notes": "PER GROUP. §1.199A-4(b)(1)(v). Preparer-asserted. Required to aggregate."},
    # ── Return-level inputs ──
    {"fact_key": "a_taxable_income_before_qbi", "label": "Lines 20/33 — taxable income before the QBI deduction",
     "data_type": "decimal", "default_value": "0", "sort_order": 20,
     "notes": ("RETURN LEVEL. = 1040 line 11 (AGI) − line 12 − line 13b (Sch 1-A OBBBA), IDENTICAL to the "
               "simplified-8995 L11 sourcing (Ken-approved 2026-06-12). Drives the scope gate, the Part III "
               "phase-in, the Schedule A applicable %, and the Part IV income limit.")},
    {"fact_key": "a_net_capital_gain", "label": "Line 34 — net capital gain + qualified dividends",
     "data_type": "decimal", "default_value": "0", "sort_order": 21,
     "notes": ("RETURN LEVEL. = 1040 L3a (qualified dividends) + net capital gain (Schedule D min(15,16) if "
               "engaged, else 1040 L7). IDENTICAL to simplified-8995 L12 (W5).")},
    {"fact_key": "a_filing_status", "label": "Filing status (selects threshold + phase-in range)", "data_type": "string", "sort_order": 22,
     "notes": "RETURN LEVEL. mfj|mfs|single|hoh|qss. single/hoh/qss → 'other'."},
    {"fact_key": "a_reit_ptp_income", "label": "Line 28 — qualified REIT dividends + PTP income/(loss)",
     "data_type": "decimal", "default_value": "0", "sort_order": 23,
     "notes": "RETURN LEVEL. Reuses 1099-DIV box 5 §199A dividends + PTP K-1. May be negative (loss carried out via L40)."},
    {"fact_key": "a_reit_ptp_carryforward_prior", "label": "Line 29 — REIT/PTP (loss) carryforward from prior years",
     "data_type": "decimal", "default_value": "0", "sort_order": 24,
     "notes": "RETURN LEVEL. Negative. Preparer-entered prior-year carryforward."},
    {"fact_key": "a_qbi_loss_carryforward_prior", "label": "Schedule C line 2 — QBI net (loss) carryforward from prior years",
     "data_type": "decimal", "default_value": "0", "sort_order": 25,
     "notes": "RETURN LEVEL. Negative. Enters Schedule C loss netting (or Form 8995 line 16 of the prior year)."},
    {"fact_key": "a_dpad_199ag", "label": "Line 38 — DPAD §199A(g) allocated from an ag/hort cooperative",
     "data_type": "decimal", "default_value": "0", "sort_order": 26,
     "notes": ("RETURN LEVEL. Preparer-entered from the cooperative's written notice (1099-PATR box 6 / "
               "attachment). CAPPED on entry to the form: line 38 face verbatim — \"Don't enter more than "
               "line 33 minus line 37\" (D_8995A_002 fires when the cap clips). COMPUTED since 2026-07-03; "
               "previously the D_8995A_002 RED-defer.")},
    # ── Outputs ──
    {"fact_key": "a_qbi_deduction_l39", "label": "Line 39 — total QBI deduction (output → Form 1040 line 13)",
     "data_type": "decimal", "sort_order": 40,
     "notes": "OUTPUT. = L37 + L38. Feeds Form 1040 line 13 (computed feeder; replaces the D_8995_001 RED-defer above threshold)."},
    {"fact_key": "a_qbi_carryforward_out", "label": "Schedule C line 6 — QBI net (loss) carryforward to next year (output)",
     "data_type": "decimal", "sort_order": 41,
     "notes": "OUTPUT. Net negative QBI (loss > positive QBI) carried forward (negative)."},
    {"fact_key": "a_reit_carryforward_out_l40", "label": "Line 40 — REIT/PTP (loss) carryforward to next year (output)",
     "data_type": "decimal", "sort_order": 42,
     "notes": "OUTPUT. = min(0, L28 + L29) (negative REIT/PTP carried out)."},
    {"fact_key": "a_sstb_applicable_pct", "label": "Schedule A — SSTB applicable percentage (computed)",
     "data_type": "decimal", "sort_order": 43,
     "notes": "OUTPUT/intermediate. = clamp((ceiling − TI)/range, 0, 1). Multiplies SSTB QBI/W-2/UBIA before Part II."},
    # ── Constants ──
    {"fact_key": "a_qbi_rate", "label": "QBI rate (20%) — statutory §199A, non-indexed", "data_type": "decimal", "sort_order": 50,
     "notes": "CONSTANT 0.20 (lines 3/8/31/36). Same both years."},
    {"fact_key": "a_threshold", "label": "§199A threshold (YEAR-KEYED + filing status)", "data_type": "decimal", "sort_order": 51,
     "notes": "CONSTANT (year-keyed): 2025 $394,600 MFJ / $197,300 other; 2026 $403,500 / $201,775 MFS / $201,750 other."},
    {"fact_key": "a_phase_in_range", "label": "Phase-in range ($50,000 / $100,000 MFJ) — statutory non-indexed", "data_type": "decimal", "sort_order": 52,
     "notes": "CONSTANT §199A(b)(3)(B)(ii). $100,000 MFJ / $50,000 all other (incl. MFS). Same both years. Ceiling = threshold + range."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 8995-A — RULES
# ═══════════════════════════════════════════════════════════════════════════

F8995A_RULES: list[dict] = [
    {"rule_id": "R-8995A-SCOPE", "title": "Scope gate — above the threshold OR any patron business", "rule_type": "routing", "precedence": 0, "sort_order": 1,
     "formula": ("Used iff a_taxable_income_before_qbi > QBI_THRESHOLDS[year][status] OR any business has "
                 "a_business_is_patron (patrons use 8995-A at ANY income — i8995a 2025 'Who Can Take the "
                 "Deduction'). A patron at/below the threshold takes the face line-3 skip: skip lines 4–12, "
                 "L13 = L3 (no W-2/UBIA limit, no Part III, no Schedule A) — only the Schedule D patron "
                 "reduction applies. Otherwise the simplified Form 8995 computes."),
     "inputs": ["a_taxable_income_before_qbi", "a_threshold", "a_filing_status", "a_business_is_patron"], "outputs": [],
     "description": "RETURN LEVEL. Complement of R-8995-SCOPE (simplified). Above the year-keyed threshold the W-2/UBIA and SSTB limits bite; a patron routes here regardless of income."},
    {"rule_id": "R-8995A-SCHA", "title": "Schedule A — SSTB applicable percentage (in-band reduction; above-ceiling exclusion)", "rule_type": "calculation", "precedence": 1, "sort_order": 2,
     "formula": ("If a business is an SSTB: applicable% = clamp((ceiling − TI) / range, 0, 1) where ceiling = "
                 "threshold + range. Reduce the SSTB's QBI (L2), W-2 wages (L4), and UBIA (L7) by applicable% "
                 "BEFORE Part II. TI ≤ threshold → 8995-A not used; TI ≥ ceiling → applicable% = 0 (excluded). "
                 "Non-SSTB businesses: no Schedule A reduction."),
     "inputs": ["a_business_is_sstb", "a_taxable_income_before_qbi", "a_threshold", "a_phase_in_range", "a_sstb_applicable_pct"],
     "outputs": ["A-APPLPCT", "A-QBI", "A-W2", "A-UBIA"],
     "description": "RETURN LEVEL (per SSTB). §199A(d)(3) / §1.199A-5(a)(2). The applicable % is the fraction RETAINED (100%→0% across the band)."},
    {"rule_id": "R-8995A-SCHB", "title": "Schedule B — aggregation: combine QBI/W-2/UBIA across the group", "rule_type": "calculation", "precedence": 2, "sort_order": 3,
     "formula": ("For each aggregation group (shared a_aggregation_group): combined QBI = Σ member QBI; combined "
                 "W-2 = Σ member W-2; combined UBIA = Σ member UBIA → ONE Part I/II column. Eligibility "
                 "(§1.199A-4): 50%+ common ownership (asserted) + same tax-year end + NONE is an SSTB (enforced) "
                 "+ ≥2 of 3 factors (asserted)."),
     "inputs": ["a_aggregation_group", "a_business_qbi", "a_business_w2_wages", "a_business_ubia",
                "a_agg_ownership_50pct", "a_agg_factors_met", "a_business_is_sstb"],
     "outputs": ["SB-AGG-QBI", "SB-AGG-W2", "SB-AGG-UBIA"],
     "description": "RETURN LEVEL (per group). Aggregation combines the W-2/UBIA bases — often the difference between a binding and a non-binding wage limit."},
    {"rule_id": "R-8995A-SCHC", "title": "Schedule C — per-business loss netting + carryforward", "rule_type": "calculation", "precedence": 3, "sort_order": 4,
     "formula": ("total_loss = Σ(negative current-year QBI) + a_qbi_loss_carryforward_prior (both negative). "
                 "Apportion total_loss across POSITIVE-QBI businesses pro-rata by QBI: adjusted_qbi[b] = qbi[b] + "
                 "total_loss × qbi[b]/Σpositive_qbi → Part II line 2 (line 1 col (c)). A loss business → adjusted "
                 "QBI removed (0). If adjusted_qbi[b] ≤ 0 → W-2[b] = UBIA[b] = 0. Net negative (|total_loss| > "
                 "Σpositive_qbi) → line 6 carryforward (negative)."),
     "inputs": ["a_business_qbi", "a_qbi_loss_carryforward_prior"], "outputs": ["SC-1C", "SC-6"],
     "description": "RETURN LEVEL. i8995a Schedule C. The §199A-correct order: net the loss BEFORE applying each positive business's wage/UBIA limit."},
    {"rule_id": "R-8995A-P2-LIMIT", "title": "Part II lines 2–11 — W-2 wage / UBIA limitation", "rule_type": "calculation", "precedence": 4, "sort_order": 5,
     "formula": ("Per business: L3 = L2 × 20%; L5 = L4 × 50%; L6 = L4 × 25%; L8 = L7 × 2.5%; L9 = L6 + L8; "
                 "L10 = max(L5, L9); L11 = min(L3, L10)."),
     "inputs": ["a_business_qbi", "a_business_w2_wages", "a_business_ubia", "a_qbi_rate"],
     "outputs": ["2", "3", "4", "5", "6", "7", "8", "9", "10", "11"],
     "description": "RETURN LEVEL (per column). The greater-of (50% W-2) or (25% W-2 + 2.5% UBIA), capped at 20% of QBI."},
    {"rule_id": "R-8995A-P3-PHASEIN", "title": "Part III lines 17–26 — phased-in reduction (in-band wage-limit relief)", "rule_type": "calculation", "precedence": 5, "sort_order": 6,
     "formula": ("Per business, ONLY if threshold < TI ≤ ceiling AND L10 < L3: L17 = L3; L18 = L10; L19 = L17 − "
                 "L18; L22 = TI − threshold; L24 = L22 / range; L25 = L19 × L24; L26 = L17 − L25 → L12. "
                 "Otherwise L12 is blank (L13 = L11)."),
     "inputs": ["a_taxable_income_before_qbi", "a_threshold", "a_phase_in_range"],
     "outputs": ["17", "18", "19", "20", "21", "22", "23", "24", "25", "26"],
     "description": "RETURN LEVEL (per column). Phases OUT the wage/UBIA limitation across the band (full QBI 20% at the floor → full limit at the ceiling)."},
    {"rule_id": "R-8995A-P2-COMP", "title": "Part II lines 12–16 — QBI component", "rule_type": "calculation", "precedence": 6, "sort_order": 7,
     "formula": ("Per business: L12 = L26 (if Part III) else blank; L13 = max(L11, L12) — EXCEPT at/below the "
                 "threshold (patron path): skip 4–12 and L13 = L3 (face line-3 verbatim); L14 = Schedule D "
                 "line 6 for the corresponding business (R-8995A-PATRON; 0 for non-patrons); L15 = max(0, "
                 "L13 − L14) ('If zero or less, enter zero' — i8995a L15). L16 = Σ L15 across all businesses."),
     "inputs": ["a_business_schd_qbi_alloc", "a_business_schd_wages_alloc"], "outputs": ["12", "13", "14", "15", "16"],
     "description": "RETURN LEVEL. L13 takes the GREATER of the full limit (L11) or the phased-in amount (L12) — the phase-in only ever helps. L14 is the computed Schedule D patron reduction."},
    {"rule_id": "R-8995A-P4-REIT", "title": "Part IV lines 27–32 — REIT/PTP component", "rule_type": "calculation", "precedence": 7, "sort_order": 8,
     "formula": "L27 = L16; L30 = max(0, L28 REIT/PTP income + L29 prior carryforward); L31 = L30 × 20%; L32 = L27 + L31.",
     "inputs": ["a_reit_ptp_income", "a_reit_ptp_carryforward_prior", "a_qbi_rate"], "outputs": ["27", "28", "29", "30", "31", "32"],
     "description": "RETURN LEVEL. The REIT/PTP component is 20% of (positive) qualified REIT dividends + PTP income."},
    {"rule_id": "R-8995A-P4-LIMIT", "title": "Part IV lines 33–39 — income limitation → Form 1040 line 13", "rule_type": "calculation", "precedence": 8, "sort_order": 9,
     "formula": ("L33 = TI before QBI; L34 = net cap gain + qual dividends; L35 = max(0, L33 − L34); L36 = L35 × "
                 "20%; L37 = min(L32, L36); L38 = min(a_dpad_199ag, max(0, L33 − L37)) — face-verbatim cap "
                 "\"Don't enter more than line 33 minus line 37\" (D_8995A_002 info when clipped); "
                 "L39 = L37 + L38 → Form 1040 line 13."),
     "inputs": ["a_taxable_income_before_qbi", "a_net_capital_gain", "a_qbi_rate", "a_dpad_199ag"], "outputs": ["33", "34", "35", "36", "37", "38", "39"],
     "description": "RETURN LEVEL. The deduction is the smaller of the components total (L32) and 20% of (TI − net cap gain), plus the capped §199A(g) DPAD. L39 → 1040 line 13 (override = escape hatch)."},
    {"rule_id": "R-8995A-P4-CARRYFWD", "title": "Line 40 — REIT/PTP (loss) carryforward to next year", "rule_type": "calculation", "precedence": 9, "sort_order": 10,
     "formula": "L40 = min(0, L28 + L29) (negative REIT/PTP carried forward); else 0.",
     "inputs": ["a_reit_ptp_income", "a_reit_ptp_carryforward_prior"], "outputs": ["40"],
     "description": "RETURN LEVEL. A net negative REIT/PTP carries forward; it does not reduce the QBI component."},
    {"rule_id": "R-8995A-PATRON", "title": "Schedule D — patron reduction per business (COMPUTED; Ken ruling 2026-07-03, MeF S2)", "rule_type": "calculation", "precedence": 10, "sort_order": 11,
     "formula": ("Per patron business (a_business_is_patron): SD2 = a_business_schd_qbi_alloc; SD3 = SD2 × 9% "
                 "(0.09); SD4 = a_business_schd_wages_alloc; SD5 = SD4 × 50% (0.50); SD6 = min(SD3, SD5) → "
                 "Form 8995-A line 14 for the corresponding trade, business, or aggregation (f8995ad face "
                 "verbatim; §199A(b)(7)). Non-patron business → L14 = 0. Patron with SD2 blank/0 → reduction 0 "
                 "+ D_8995A_001 (info: confirm no qualified payments on the 1099-PATR). NOTE the lesser-of arms: "
                 "a zero-wage patron business (e.g. a statutory-employee Sch C) always reduces by $0 even when "
                 "ALL QBI is allocable to qualified payments — 50% × 0 wages is the lesser."),
     "inputs": ["a_business_is_patron", "a_business_schd_qbi_alloc", "a_business_schd_wages_alloc"],
     "outputs": ["14", "SD2", "SD3", "SD4", "SD5", "SD6"],
     "description": ("RETURN LEVEL (per patron business). Replaces the v1 RED-defer (D_8995A_001/002 error → "
                     "info, 2026-07-03). Amounts stay CENTS through the chain (8995-A is a stated R-SE-ROUND "
                     "boundary; whole-dollar only at the 1040 face).")},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 8995-A — LINES (main form lines exact; schedule lines documented)
# ═══════════════════════════════════════════════════════════════════════════

F8995A_LINES: list[dict] = [
    # Part I (rows on the face; >3 → attached worksheets)
    {"line_number": "1A", "description": "Part I row A — name / SSTB / aggregation / TIN / patron", "line_type": "input"},
    {"line_number": "1B", "description": "Part I row B — name / SSTB / aggregation / TIN / patron", "line_type": "input"},
    {"line_number": "1C", "description": "Part I row C — name / SSTB / aggregation / TIN / patron", "line_type": "input"},
    # Part II (per business column A/B/C)
    {"line_number": "2", "description": "QBI from the trade/business/aggregation (per column; after Sch A/C adjustments)", "line_type": "input"},
    {"line_number": "3", "description": "Line 2 × 20%", "line_type": "calculated"},
    {"line_number": "4", "description": "Allocable W-2 wages (per column)", "line_type": "input"},
    {"line_number": "5", "description": "Line 4 × 50%", "line_type": "calculated"},
    {"line_number": "6", "description": "Line 4 × 25%", "line_type": "calculated"},
    {"line_number": "7", "description": "Allocable UBIA of qualified property (per column)", "line_type": "input"},
    {"line_number": "8", "description": "Line 7 × 2.5%", "line_type": "calculated"},
    {"line_number": "9", "description": "Add lines 6 and 8", "line_type": "calculated"},
    {"line_number": "10", "description": "Greater of line 5 or line 9", "line_type": "calculated"},
    {"line_number": "11", "description": "W-2/UBIA limitation = smaller of line 3 or line 10", "line_type": "calculated"},
    {"line_number": "12", "description": "Phased-in reduction = amount from line 26 (Part III), if any", "line_type": "calculated"},
    {"line_number": "13", "description": "Greater of line 11 or line 12 (QBI deduction before patron reduction)", "line_type": "calculated"},
    {"line_number": "14", "description": "Patron reduction = Schedule D line 6 for the corresponding business (computed)", "line_type": "calculated"},
    {"line_number": "15", "description": "QBI component = line 13 − line 14", "line_type": "calculated"},
    {"line_number": "16", "description": "Total QBI component = Σ line 15 (all businesses)", "line_type": "subtotal"},
    # Part III (per business column A/B/C)
    {"line_number": "17", "description": "Amounts from line 3", "line_type": "calculated"},
    {"line_number": "18", "description": "Amounts from line 10", "line_type": "calculated"},
    {"line_number": "19", "description": "Subtract line 18 from line 17", "line_type": "calculated"},
    {"line_number": "20", "description": "Taxable income before the QBI deduction", "line_type": "calculated"},
    {"line_number": "21", "description": "Threshold (197,300 / 394,600 MFJ)", "line_type": "calculated"},
    {"line_number": "22", "description": "Subtract line 21 from line 20", "line_type": "calculated"},
    {"line_number": "23", "description": "Phase-in range (50,000 / 100,000 MFJ)", "line_type": "calculated"},
    {"line_number": "24", "description": "Phase-in percentage = line 22 ÷ line 23", "line_type": "calculated"},
    {"line_number": "25", "description": "Total phase-in reduction = line 19 × line 24", "line_type": "calculated"},
    {"line_number": "26", "description": "QBI after phase-in = line 17 − line 25 → enter on line 12", "line_type": "calculated"},
    # Part IV (single column)
    {"line_number": "27", "description": "Total QBI component (from line 16)", "line_type": "calculated"},
    {"line_number": "28", "description": "Qualified REIT dividends + PTP income/(loss)", "line_type": "input"},
    {"line_number": "29", "description": "REIT/PTP (loss) carryforward from prior years (negative)", "line_type": "input"},
    {"line_number": "30", "description": "Combine lines 28 and 29; if < 0 enter 0", "line_type": "calculated"},
    {"line_number": "31", "description": "REIT/PTP component = line 30 × 20%", "line_type": "calculated"},
    {"line_number": "32", "description": "QBI deduction before income limit = line 27 + line 31", "line_type": "calculated"},
    {"line_number": "33", "description": "Taxable income before the QBI deduction", "line_type": "calculated"},
    {"line_number": "34", "description": "Net capital gain + qualified dividends", "line_type": "calculated"},
    {"line_number": "35", "description": "Subtract line 34 from line 33; if ≤ 0 enter 0", "line_type": "calculated"},
    {"line_number": "36", "description": "Income limitation = line 35 × 20%", "line_type": "calculated"},
    {"line_number": "37", "description": "Smaller of line 32 or line 36 (before DPAD)", "line_type": "calculated"},
    {"line_number": "38", "description": "DPAD §199A(g) from ag/hort coop — input capped at line 33 − line 37 (face verbatim)", "line_type": "input"},
    {"line_number": "39", "description": "Total QBI deduction = line 37 + line 38 → Form 1040 line 13", "line_type": "total"},
    {"line_number": "40", "description": "REIT/PTP (loss) carryforward out = min(0, line 28 + line 29)", "line_type": "calculated"},
    # Schedule A (SSTB) — computational worksheet; exact PDF line numbers verified at render (W7)
    {"line_number": "A-APPLPCT", "description": "Schedule A — SSTB applicable % = clamp((ceiling − TI)/range, 0, 1)", "line_type": "calculated"},
    {"line_number": "A-QBI", "description": "Schedule A — SSTB QBI × applicable % → Part II line 2", "line_type": "calculated"},
    {"line_number": "A-W2", "description": "Schedule A — SSTB W-2 wages × applicable % → Part II line 4", "line_type": "calculated"},
    {"line_number": "A-UBIA", "description": "Schedule A — SSTB UBIA × applicable % → Part II line 7", "line_type": "calculated"},
    # Schedule B (aggregation)
    {"line_number": "SB-AGG-QBI", "description": "Schedule B — combined QBI across the aggregation group", "line_type": "calculated"},
    {"line_number": "SB-AGG-W2", "description": "Schedule B — combined W-2 wages across the aggregation group", "line_type": "calculated"},
    {"line_number": "SB-AGG-UBIA", "description": "Schedule B — combined UBIA across the aggregation group", "line_type": "calculated"},
    # Schedule C (loss netting)
    {"line_number": "SC-1C", "description": "Schedule C line 1(c) — adjusted QBI after loss netting → Part II line 2", "line_type": "calculated"},
    {"line_number": "SC-6", "description": "Schedule C line 6 — QBI net (loss) carryforward to next year (negative)", "line_type": "calculated"},
    # Schedule D (patron reduction; per business column A/B/C, Rev. 12-2022 face)
    {"line_number": "SD1A", "description": "Schedule D line 1a — trade, business, or aggregation name (per column)", "line_type": "input"},
    {"line_number": "SD1B", "description": "Schedule D line 1b — taxpayer identification number (per column)", "line_type": "input"},
    {"line_number": "SD2", "description": "Schedule D line 2 — QBI allocable to qualified payments received from cooperative", "line_type": "input"},
    {"line_number": "SD3", "description": "Schedule D line 3 — line 2 × 9%", "line_type": "calculated"},
    {"line_number": "SD4", "description": "Schedule D line 4 — W-2 wages allocable to the qualified payments", "line_type": "input"},
    {"line_number": "SD5", "description": "Schedule D line 5 — line 4 × 50%", "line_type": "calculated"},
    {"line_number": "SD6", "description": "Schedule D line 6 — patron reduction = smaller of line 3 or line 5 → 8995-A line 14", "line_type": "calculated"},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 8995-A — DIAGNOSTICS
# ═══════════════════════════════════════════════════════════════════════════

F8995A_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_8995A_001", "title": "Patron with no Schedule D allocation — patron reduction computed as $0", "severity": "info",
     "condition": "a_business_is_patron is True AND a_business_schd_qbi_alloc is blank/0 for that business",
     "message": ("This business is flagged as a patron of an agricultural or horticultural cooperative, but no "
                 "QBI allocable to qualified payments (Schedule D line 2) has been entered. The patron reduction "
                 "computes as $0 and the full QBI deduction flows. Confirm against the Form 1099-PATR that the "
                 "business received no qualified payments (patronage dividends or per-unit retain allocations); "
                 "if it did, enter the allocable QBI and W-2 wages on the business's Schedule D fields."),
     "notes": ("REPURPOSED 2026-07-03 (was the Schedule D RED-defer; Ken ruled build for MeF S2). Now the "
               "confirm-the-zero surface. Severity error → info.")},
    {"diagnostic_id": "D_8995A_002", "title": "DPAD §199A(g) clipped to the line 38 cap", "severity": "info",
     "condition": "a_dpad_199ag > max(0, line_33 − line_37)",
     "message": ("The §199A(g) DPAD entered exceeds the Form 8995-A line 38 cap — the face instructs \"Don't "
                 "enter more than line 33 minus line 37.\" Line 38 is limited to ${cap}; the excess does not "
                 "carry forward on this form. Verify the cooperative's written notice amount."),
     "notes": ("REPURPOSED 2026-07-03 (was the DPAD RED-defer). Now fires only when the input is clipped by "
               "the face cap. Severity error → info.")},
    {"diagnostic_id": "D_8995A_008", "title": "Schedule D allocable QBI exceeds the business's QBI", "severity": "warning",
     "condition": "a_business_schd_qbi_alloc > adjusted QBI (Part II line 2) for that business",
     "message": ("Schedule D line 2 (QBI allocable to qualified payments) exceeds the business's total QBI on "
                 "Form 8995-A Part II line 2. Allocable QBI is a portion of the business's QBI and cannot "
                 "exceed it. Correct the allocation."),
     "notes": "Input-consistency guard on the Schedule D allocation (new 2026-07-03)."},
    {"diagnostic_id": "D_8995A_009", "title": "Schedule D allocable W-2 wages exceed the business's W-2 wages", "severity": "warning",
     "condition": "a_business_schd_wages_alloc > a_business_w2_wages for that business",
     "message": ("Schedule D line 4 (W-2 wages allocable to qualified payments) exceeds the business's W-2 "
                 "wages on Form 8995-A line 4. The instructions define line 4 as the PORTION of Form 8995-A "
                 "line 4 wages allocable to the qualified payments. Correct the allocation."),
     "notes": "Input-consistency guard on the Schedule D allocation (new 2026-07-03)."},
    {"diagnostic_id": "D_8995A_003", "title": "Aggregation elected — verify §1.199A-4 eligibility", "severity": "warning",
     "condition": "a_aggregation_group set for a group but a_agg_ownership_50pct or a_agg_factors_met not asserted",
     "message": ("Businesses are aggregated for the QBI W-2/UBIA limitation, but the §1.199A-4 eligibility "
                 "(50%+ common ownership for a majority of the year, same tax-year end, and at least two of the "
                 "three aggregation factors) has not been fully attested. Verify the aggregation qualifies and "
                 "that it is reported consistently with prior years."),
     "notes": "Aggregation is preparer-asserted for the ownership/factor tests; none-SSTB is enforced (D_8995A_007)."},
    {"diagnostic_id": "D_8995A_004", "title": "SSTB above the phase-in ceiling — no QBI deduction for that business", "severity": "info",
     "condition": "a_business_is_sstb is True AND taxable income > ceiling (threshold + range)",
     "message": ("This specified service trade or business (SSTB) is above the §199A phase-in ceiling "
                 "(${ceiling}), so none of its QBI, W-2 wages, or UBIA is taken into account — its QBI deduction "
                 "is $0. This is correct, not an omission."),
     "notes": "Explains the (correct) $0; the 'why is this $0' surface for above-ceiling SSTBs."},
    {"diagnostic_id": "D_8995A_005", "title": "Above-threshold business with no W-2 wages or UBIA — limit may be $0", "severity": "warning",
     "condition": "taxable income above the threshold AND a business has QBI but W-2 wages = 0 AND UBIA = 0",
     "message": ("A qualified business above the §199A threshold reports no W-2 wages and no UBIA of qualified "
                 "property. Above the threshold the QBI deduction for that business is limited to the greater of "
                 "50% of W-2 wages or 25% of W-2 wages + 2.5% of UBIA — with both zero, the limit (and the "
                 "deduction) is $0 except as relieved by the Part III phase-in. Verify the W-2 wages and UBIA."),
     "notes": "No silent gap — the wage/UBIA limit genuinely zeroes the deduction; this nudges the preparer to confirm the inputs."},
    {"diagnostic_id": "D_8995A_006", "title": "Qualified business net loss carryforward present — verify", "severity": "info",
     "condition": "a_qbi_loss_carryforward_prior < 0 OR Schedule C line 6 < 0 OR line 29/40 REIT-PTP loss present",
     "message": ("A qualified-business or REIT/PTP loss carryforward is present (prior-year carryforward in, or a "
                 "current-year net loss carried out on Schedule C line 6 / line 40). Verify the prior-year amounts "
                 "and note the current-year loss carried to next year."),
     "notes": "Loss netting (Schedule C) + REIT/PTP carryforward verification."},
    {"diagnostic_id": "D_8995A_007", "title": "SSTB cannot be aggregated", "severity": "error",
     "condition": "a business with a_business_is_sstb is True shares an a_aggregation_group",
     "message": ("A specified service trade or business (SSTB) is included in an aggregation group. Under "
                 "§1.199A-4(b)(1)(ii) an SSTB may not be aggregated with other trades or businesses. Remove the "
                 "SSTB from the aggregation group."),
     "notes": "Enforced eligibility (none-SSTB) — the one aggregation condition that IS checkable on the return."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 8995-A — TEST SCENARIOS (worked math; the integrity gate re-derives)
# ═══════════════════════════════════════════════════════════════════════════

F8995A_SCENARIOS: list[dict] = [
    {"scenario_name": "8995A-T1 — non-SSTB above ceiling, wage limit binds (no phase-in)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "filing_status": "single", "a_taxable_income_before_qbi": 300000,
                "businesses": [{"qbi": 100000, "w2": 30000, "ubia": 0, "sstb": False}], "a_net_capital_gain": 0},
     "expected_outputs": {"line_3": 20000, "line_5": 15000, "line_10": 15000, "line_11": 15000, "line_13": 15000, "line_16": 15000, "line_37": 15000, "line_39": 15000},
     "notes": "TI 300k > ceiling 247,300 → no Part III. L11 = min(20k, 15k) = 15k. Income limit 60k not binding → L39 = 15,000 → 1040 L13."},
    {"scenario_name": "8995A-T2 — non-SSTB in band, wage limit binds → phase-in relief", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"tax_year": 2025, "filing_status": "single", "a_taxable_income_before_qbi": 222300,
                "businesses": [{"qbi": 100000, "w2": 20000, "ubia": 0, "sstb": False}], "a_net_capital_gain": 0},
     "expected_outputs": {"line_3": 20000, "line_10": 10000, "line_11": 10000, "line_24": 0.50, "line_25": 5000, "line_26": 15000, "line_13": 15000, "line_39": 15000},
     "notes": "In band (197,300–247,300), L10 10k < L3 20k → Part III. Phase-in% = 25,000/50,000 = 50%; L25 = 5k; L26 = 15k → L13 = max(10k,15k) = 15,000 (vs 10,000 without relief)."},
    {"scenario_name": "8995A-T3 — SSTB in band (Schedule A applicable %), ample wages", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"tax_year": 2025, "filing_status": "single", "a_taxable_income_before_qbi": 222300,
                "businesses": [{"qbi": 100000, "w2": 100000, "ubia": 0, "sstb": True}], "a_net_capital_gain": 0},
     "expected_outputs": {"a_sstb_applicable_pct": 0.50, "line_2": 50000, "line_3": 10000, "line_5": 25000, "line_10": 25000, "line_11": 10000, "line_13": 10000, "line_39": 10000},
     "notes": "Sch A applicable% = (247,300−222,300)/50,000 = 50%. Reduced QBI 50k, W-2 50k. L11 = min(10k,25k) = 10k; L10 not < L3 → no Part III. L39 = 10,000."},
    {"scenario_name": "8995A-T4 — SSTB above the ceiling → excluded ($0)", "scenario_type": "edge_case", "sort_order": 4,
     "inputs": {"tax_year": 2025, "filing_status": "single", "a_taxable_income_before_qbi": 300000,
                "businesses": [{"qbi": 100000, "w2": 100000, "ubia": 0, "sstb": True}], "a_net_capital_gain": 0},
     "expected_outputs": {"a_sstb_applicable_pct": 0, "line_2": 0, "line_15": 0, "line_16": 0, "line_39": 0, "D_8995A_004": True},
     "notes": "TI 300k > ceiling 247,300 → applicable% = 0 → SSTB QBI/W-2/UBIA all 0 → L39 = 0 (D_8995A_004 info)."},
    {"scenario_name": "8995A-T5 — Schedule C loss netting (gain + loss business)", "scenario_type": "normal", "sort_order": 5,
     "inputs": {"tax_year": 2025, "filing_status": "single", "a_taxable_income_before_qbi": 260000,
                "businesses": [{"qbi": 100000, "w2": 40000, "ubia": 0, "sstb": False}, {"qbi": -40000, "w2": 0, "ubia": 0, "sstb": False}], "a_net_capital_gain": 0},
     "expected_outputs": {"SC-1C_business0": 60000, "line_3": 12000, "line_5": 20000, "line_11": 12000, "line_16": 12000, "line_39": 12000, "a_qbi_carryforward_out": 0},
     "notes": "Loss −40k apportioned to the only positive business → adjusted QBI 60k. L3 = 12k; L11 = min(12k, 20k) = 12k. Above ceiling → no Part III. L39 = 12,000 (vs 20k if the loss were ignored)."},
    {"scenario_name": "8995A-T6 — Part IV income limitation binds (net capital gain)", "scenario_type": "normal", "sort_order": 6,
     "inputs": {"tax_year": 2025, "filing_status": "single", "a_taxable_income_before_qbi": 250000,
                "businesses": [{"qbi": 100000, "w2": 100000, "ubia": 0, "sstb": False}], "a_net_capital_gain": 230000},
     "expected_outputs": {"line_11": 20000, "line_32": 20000, "line_35": 20000, "line_36": 4000, "line_37": 4000, "line_39": 4000},
     "notes": "L11 = min(20k, 50k) = 20k. Income limit L36 = 20% × (250k − 230k) = 4k binds → L39 = 4,000."},
    {"scenario_name": "8995A-T7 — REIT/PTP only, above threshold (no business)", "scenario_type": "normal", "sort_order": 7,
     "inputs": {"tax_year": 2025, "filing_status": "single", "a_taxable_income_before_qbi": 250000,
                "businesses": [], "a_reit_ptp_income": 10000, "a_net_capital_gain": 0},
     "expected_outputs": {"line_16": 0, "line_30": 10000, "line_31": 2000, "line_32": 2000, "line_37": 2000, "line_39": 2000},
     "notes": "No business → L16 = 0. REIT/PTP component L31 = 10k × 20% = 2k; income limit 50k not binding → L39 = 2,000."},
    {"scenario_name": "8995A-T8 — aggregation (Schedule B) combines W-2 bases", "scenario_type": "normal", "sort_order": 8,
     "inputs": {"tax_year": 2025, "filing_status": "single", "a_taxable_income_before_qbi": 260000,
                "businesses": [{"qbi": 80000, "w2": 10000, "ubia": 0, "sstb": False, "agg": "AGG1"}, {"qbi": 20000, "w2": 50000, "ubia": 0, "sstb": False, "agg": "AGG1"}],
                "a_agg_ownership_50pct": True, "a_agg_factors_met": True, "a_net_capital_gain": 0},
     "expected_outputs": {"SB-AGG-QBI": 100000, "SB-AGG-W2": 60000, "line_3": 20000, "line_5": 30000, "line_10": 30000, "line_11": 20000, "line_39": 20000},
     "notes": "Aggregated QBI 100k, W-2 60k → L11 = min(20k, 30k) = 20k. Without aggregation the separate wage limits give ~9k. Aggregation engine load-bearing."},
    {"scenario_name": "8995A-T9 — patron with no Schedule D allocation → reduction $0 + D_8995A_001 info", "scenario_type": "edge_case", "sort_order": 9,
     "inputs": {"tax_year": 2025, "filing_status": "single", "a_taxable_income_before_qbi": 260000,
                "businesses": [{"qbi": 100000, "w2": 100000, "ubia": 0, "sstb": False, "patron": True}], "a_net_capital_gain": 0},
     "expected_outputs": {"D_8995A_001": True, "line_14": 0, "line_11": 20000, "line_13": 20000, "line_15": 20000, "line_16": 20000, "line_39": 20000},
     "notes": ("AMENDED 2026-07-03 (was the RED-defer pin). Patron flag with no allocable-QBI entry → Schedule D "
               "L2 = 0 → L14 = 0 and the FULL deduction flows (L11 = min(20k, 50k) = 20k → L39 = 20,000); "
               "D_8995A_001 (now info) asks the preparer to confirm no qualified payments.")},
    {"scenario_name": "8995A-T11 — patron 9%-arm binds (Sch D L3 < L5)", "scenario_type": "normal", "sort_order": 11,
     "inputs": {"tax_year": 2025, "filing_status": "single", "a_taxable_income_before_qbi": 260000,
                "businesses": [{"qbi": 100000, "w2": 60000, "ubia": 0, "sstb": False, "patron": True,
                                "schd_qbi_alloc": 100000, "schd_wages_alloc": 60000}], "a_net_capital_gain": 0},
     "expected_outputs": {"SD2": 100000, "SD3": 9000, "SD4": 60000, "SD5": 30000, "SD6": 9000,
                          "line_11": 20000, "line_13": 20000, "line_14": 9000, "line_15": 11000, "line_16": 11000, "line_37": 11000, "line_39": 11000},
     "notes": ("HAND-COMPUTED. Above ceiling (260k), wage limit L5 = 30k > L3 = 20k → L11 = 20k = L13. Sch D: "
               "9% × 100k = 9,000 vs 50% × 60k = 30,000 → SD6 = 9,000 (9% arm). L15 = 20,000 − 9,000 = 11,000; "
               "income limit 52k not binding → L39 = 11,000.")},
    {"scenario_name": "8995A-T12 — patron 50%-wage-arm binds (Sch D L5 < L3)", "scenario_type": "normal", "sort_order": 12,
     "inputs": {"tax_year": 2025, "filing_status": "single", "a_taxable_income_before_qbi": 260000,
                "businesses": [{"qbi": 100000, "w2": 60000, "ubia": 0, "sstb": False, "patron": True,
                                "schd_qbi_alloc": 100000, "schd_wages_alloc": 10000}], "a_net_capital_gain": 0},
     "expected_outputs": {"SD3": 9000, "SD5": 5000, "SD6": 5000, "line_14": 5000, "line_15": 15000, "line_39": 15000},
     "notes": ("HAND-COMPUTED. Same as T11 but only 10k of wages allocable: 50% × 10k = 5,000 < 9,000 → "
               "SD6 = 5,000 (wage arm). L15 = 20,000 − 5,000 = 15,000 → L39 = 15,000.")},
    {"scenario_name": "8995A-T13 — BELOW-threshold patron, zero wages (S2 Jones shape): skip 4–12, reduction $0", "scenario_type": "edge_case", "sort_order": 13,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "a_taxable_income_before_qbi": 60000,
                "businesses": [{"qbi": 26979, "w2": 0, "ubia": 0, "sstb": False, "patron": True}], "a_net_capital_gain": 0},
     "expected_outputs": {"line_3": 5395.80, "line_13": 5395.80, "line_14": 0, "line_15": 5395.80, "line_16": 5395.80,
                          "line_36": 12000, "line_37": 5395.80, "line_39": 5395.80, "D_8995A_001": True},
     "notes": ("HAND-COMPUTED — THE LOAD-BEARING S2 TEST. Patron routes to 8995-A BELOW the threshold (i8995a "
               "'Who Can Take'); face line-3 skip: skip L4–12, L13 = L3 = 20% × 26,979 = 5,395.80 (cents — "
               "8995-A is an R-SE-ROUND stated boundary). The zero-wage business is NOT zeroed by the W-2 "
               "limit (the limit doesn't exist below the threshold — §199A(b)(3)(A)); no allocation entered → "
               "L14 = 0 + D_8995A_001 info. L39 = 5,395.80 → 1040 13a. Proves the ATS S2 stipulation "
               "('patrons therefore do not qualify') is NOT enacted law — the divergence is documented at the "
               "scenario leg.")},
    {"scenario_name": "8995A-T14 — patron below threshold, FULL allocation but zero wages → reduction still $0", "scenario_type": "edge_case", "sort_order": 14,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "a_taxable_income_before_qbi": 100000,
                "businesses": [{"qbi": 50000, "w2": 0, "ubia": 0, "sstb": False, "patron": True,
                                "schd_qbi_alloc": 50000, "schd_wages_alloc": 0}], "a_net_capital_gain": 0},
     "expected_outputs": {"SD2": 50000, "SD3": 4500, "SD4": 0, "SD5": 0, "SD6": 0,
                          "line_13": 10000, "line_14": 0, "line_15": 10000, "line_39": 10000},
     "notes": ("HAND-COMPUTED — the sharpest §199A(b)(7) point: even with 100% of QBI allocable to qualified "
               "payments, a business that paid NO W-2 wages reduces by $0 — min(9% × 50k = 4,500, 50% × 0 = 0) "
               "= 0. D_8995A_001 does NOT fire (allocation entered). L39 = 10,000.")},
    {"scenario_name": "8995A-T15 — DPAD input clipped by the line 38 cap (L33 − L37)", "scenario_type": "edge_case", "sort_order": 15,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "a_taxable_income_before_qbi": 8000,
                "businesses": [{"qbi": 30000, "w2": 0, "ubia": 0, "sstb": False, "patron": True}],
                "a_net_capital_gain": 0, "a_dpad_199ag": 10000},
     "expected_outputs": {"line_13": 6000, "line_32": 6000, "line_36": 1600, "line_37": 1600,
                          "line_38": 6400, "line_39": 8000, "D_8995A_002": True},
     "notes": ("HAND-COMPUTED. Below threshold: L13 = 20% × 30k = 6,000; income limit L36 = 20% × 8,000 = "
               "1,600 binds → L37 = 1,600. DPAD cap = L33 − L37 = 8,000 − 1,600 = 6,400 < input 10,000 → "
               "L38 = 6,400 + D_8995A_002 (clipped). L39 = 1,600 + 6,400 = 8,000 (= L33 — the cap exists "
               "precisely so QBI + DPAD never exceeds taxable income).")},
    {"scenario_name": "8995A-T10 — TY2026 ceiling year-keying (load-bearing)", "scenario_type": "normal", "sort_order": 10,
     "inputs": {"tax_year": 2026, "filing_status": "single", "a_taxable_income_before_qbi": 230000,
                "businesses": [{"qbi": 100000, "w2": 20000, "ubia": 0, "sstb": False}], "a_net_capital_gain": 0},
     "expected_outputs": {"line_3": 20000, "line_10": 10000, "line_24": 0.565, "line_25": 5650, "line_26": 14350, "line_13": 14350, "line_39": 14350},
     "notes": "TY2026 single threshold 201,750, ceiling 251,750. In band: L22 = 230,000 − 201,750 = 28,250; phase-in% = 28,250/50,000 = 0.565; L25 = 10,000 × 0.565 = 5,650; L26 = 20,000 − 5,650 = 14,350 → L13 = max(10,000, 14,350) = 14,350 → L39 = 14,350.",
     },
]


# ═══════════════════════════════════════════════════════════════════════════
# RULE → AUTHORITY LINKS
# ═══════════════════════════════════════════════════════════════════════════

F8995A_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-8995A-SCOPE", "IRS_2025_8995A_FORM", "primary", "Use-this-form-if threshold"),
    ("R-8995A-SCOPE", "RP_2025_32", "primary", "TY2026 §199A thresholds (§4.26)"),
    ("R-8995A-SCHA", "IRS_2025_8995A_INSTR", "primary", "Schedule A SSTB applicable %"),
    ("R-8995A-SCHA", "IRC_199A", "primary", "§199A(d)(3) SSTB phase-in"),
    ("R-8995A-SCHB", "IRS_2025_8995A_INSTR", "primary", "Schedule B aggregation eligibility + combine"),
    ("R-8995A-SCHC", "IRS_2025_8995A_INSTR", "primary", "Schedule C loss netting (apportion by QBI; zero W-2/UBIA)"),
    ("R-8995A-P2-LIMIT", "IRS_2025_8995A_FORM", "primary", "Part II lines 2–11 W-2/UBIA limit"),
    ("R-8995A-P2-LIMIT", "IRC_199A", "primary", "§199A(b)(2) greater-of W-2 or W-2+UBIA"),
    ("R-8995A-P3-PHASEIN", "IRS_2025_8995A_FORM", "primary", "Part III lines 17–26 phase-in"),
    ("R-8995A-P3-PHASEIN", "IRC_199A", "secondary", "§199A(b)(3)(B) phase-in range $50k/$100k"),
    ("R-8995A-P2-COMP", "IRS_2025_8995A_FORM", "primary", "Part II lines 12–16 QBI component"),
    ("R-8995A-P4-REIT", "IRS_2025_8995A_FORM", "primary", "Part IV lines 27–32 REIT/PTP component"),
    ("R-8995A-P4-LIMIT", "IRS_2025_8995A_FORM", "primary", "Part IV lines 33–39 income limit → 1040 L13"),
    ("R-8995A-P4-LIMIT", "IRS_2025_8995A_INSTR", "secondary", "Line 34 net cap gain + qualified dividends"),
    ("R-8995A-P4-CARRYFWD", "IRS_2025_8995A_FORM", "primary", "Line 40 REIT/PTP carryforward out"),
    ("R-8995A-PATRON", "IRS_8995A_SCHD_FORM", "primary", "Schedule D face: L6 = min(9% × L2, 50% × L4) → 8995-A L14"),
    ("R-8995A-PATRON", "IRS_2025_8995A_INSTR", "primary", "Patron routing at any income; qualified payments; L14/L15"),
    ("R-8995A-PATRON", "IRC_199A", "primary", "§199A(b)(7) patron reduction; §199A(g)(3) specified co-op"),
    ("R-8995A-P4-LIMIT", "IRS_2025_8995A_FORM", "secondary", "L38 DPAD cap: don't enter more than L33 − L37 (face verbatim)"),
    ("R-8995A-SCOPE", "IRS_2025_8995A_INSTR", "primary", "Patron uses 8995-A at any income ('Who Can Take the Deduction')"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS (staged into tts-tax-app at the assertions leg)
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-8995A-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Form 8995-A line 39 → Form 1040 line 13",
     "description": ("Validates R-8995A-P4-LIMIT. L39 = L37 + L38 (DPAD = 0 in v1) → 1040 line 13. Bug it catches: "
                     "the above-threshold deduction not reaching 1040 line 13 (the old D_8995_001 blanked it)."),
     "definition": {"kind": "flow_assertion", "form": "8995A", "source_line": "39", "must_write_to": ["1040.13"]},
     "sort_order": 1},
    {"assertion_id": "FA-1040-8995A-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Part II W-2/UBIA limitation: L11 = min(L3, max(L5, L9))",
     "description": ("Validates R-8995A-P2-LIMIT. L10 = greater of 50% W-2 (L5) or 25% W-2 + 2.5% UBIA (L9); "
                     "L11 = smaller of L3 (20% QBI) or L10. Bug it catches: taking the lesser of the two wage "
                     "limits, or omitting the UBIA branch."),
     "definition": {"kind": "formula_check", "form": "8995A",
                    "formula": "line_10 == max(line_5, line_9); line_11 == min(line_3, line_10)",
                    "constants": {"qbi_rate": 0.20, "w2_50": 0.50, "w2_25": 0.25, "ubia_25": 0.025}},
     "sort_order": 2},
    {"assertion_id": "FA-1040-8995A-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Part III phase-in: L26 = L17 − L19 × (TI − threshold)/range; gated in-band AND L10 < L3",
     "description": ("Validates R-8995A-P3-PHASEIN. Only computed when threshold < TI ≤ ceiling AND the wage "
                     "limit binds (L10 < L3); L13 = max(L11, L12). Bug it catches: running the phase-in above the "
                     "ceiling, or when the limit doesn't bind."),
     "definition": {"kind": "formula_check", "form": "8995A",
                    "formula": "line_26 == line_17 - line_19 * ((ti - threshold) / phase_in_range); line_13 == max(line_11, line_12)"},
     "sort_order": 3},
    {"assertion_id": "FA-1040-8995A-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Schedule A SSTB applicable % = clamp((ceiling − TI)/range, 0, 1); above ceiling → 0",
     "description": ("Validates R-8995A-SCHA. The SSTB QBI/W-2/UBIA are multiplied by the applicable % before "
                     "Part II; above the ceiling the SSTB is excluded (0). Bug it catches: reducing only QBI (not "
                     "W-2/UBIA), or the wrong phase direction."),
     "definition": {"kind": "formula_check", "form": "8995A",
                    "formula": "applicable_pct == max(0, min(1, (ceiling - ti) / phase_in_range)); sstb_qbi == qbi * applicable_pct"},
     "sort_order": 4},
    {"assertion_id": "FA-1040-8995A-05", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Schedule C loss netting: apportion by QBI; adjusted QBI ≤ 0 → W-2/UBIA = 0",
     "description": ("Validates R-8995A-SCHC. The total QB loss (current + prior carryforward) is apportioned "
                     "across positive-QBI businesses pro-rata by QBI; a business whose adjusted QBI ≤ 0 must "
                     "report W-2 wages and UBIA of 0. Bug it catches: applying the wage limit before netting, or "
                     "leaving W-2/UBIA on a netted-to-zero business."),
     "definition": {"kind": "gating_check", "form": "8995A",
                    "blockers": ["adjusted_qbi_nonpositive_with_w2_or_ubia"], "expect": {"red_fires": False, "w2_ubia_zeroed": True}},
     "sort_order": 5},
    {"assertion_id": "FA-1040-8995A-06", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Schedule B aggregation combines QBI/W-2/UBIA across the group",
     "description": ("Validates R-8995A-SCHB. An aggregation group's combined QBI, W-2 wages, and UBIA are summed "
                     "into one Part II column for the limitation. Bug it catches: applying the wage limit "
                     "per-member instead of to the combined group."),
     "definition": {"kind": "formula_check", "form": "8995A",
                    "formula": "agg_qbi == sum(member_qbi); agg_w2 == sum(member_w2); agg_ubia == sum(member_ubia)"},
     "sort_order": 6},
    {"assertion_id": "FA-1040-8995A-07", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "§199A threshold year-keyed; phase-in range $50k/$100k non-indexed; 20% rate statutory",
     "description": ("Pins QBI_THRESHOLDS both years, the statutory phase-in range ($50,000 / $100,000 MFJ), and "
                     "the 20% rate. Bug it catches: a stale threshold, year-keying the range/rate, or an MFS "
                     "phase-in range ≠ $50,000."),
     "definition": {"kind": "constants_check", "form": "8995A",
                    "constants": {"threshold_2025": QBI_THRESHOLDS[2025], "threshold_2026": QBI_THRESHOLDS[2026],
                                  "phase_in_range": PHASE_IN_RANGE, "rate": 0.20, "applies_to_years": [2025, 2026]}},
     "sort_order": 7},
    {"assertion_id": "FA-1040-8995A-08", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Schedule D patron reduction: L14 = min(9% × SD2, 50% × SD4); patron routes to 8995-A at ANY income",
     "description": ("Validates R-8995A-PATRON (COMPUTED since 2026-07-03 — was the RED-defer gating check). "
                     "Per patron business: Sch D L6 = min(9% × allocable QBI, 50% × allocable W-2 wages) → "
                     "8995-A L14; L15 = max(0, L13 − L14). A patron return uses 8995-A even at/below the "
                     "threshold, where the face line-3 skip applies (L13 = L3 — the W-2/UBIA limit must NOT "
                     "zero a below-threshold zero-wage patron). L38 = min(DPAD input, L33 − L37). Bugs it "
                     "catches: patron routed to the simplified 8995; the wage limit applied below the "
                     "threshold; the reduction taken as the GREATER arm; the DPAD cap dropped."),
     "definition": {"kind": "formula_check", "form": "8995A",
                    "formula": ("line_14 == min(0.09 * schd_qbi_alloc, 0.50 * schd_wages_alloc); "
                                "line_15 == max(0, line_13 - line_14); "
                                "patron_below_threshold_line_13 == line_3; "
                                "line_38 == min(dpad_input, max(0, line_33 - line_37))"),
                    "constants": {"patron_pct": 0.09, "wage_pct": 0.50}},
     "sort_order": 8},
    {"assertion_id": "FA-1040-8995A-09", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Routing: above the threshold uses Form 8995-A (not the simplified 8995)",
     "description": ("Validates R-8995A-SCOPE (complement of R-8995-SCOPE). When taxable income before the QBI "
                     "deduction exceeds the year-keyed §199A threshold, Form 8995-A computes the deduction; the "
                     "simplified Form 8995 is not used. Bug it catches: both forms computing line 13, or neither."),
     "definition": {"kind": "gating_check", "form": "8995A",
                    "blockers": ["taxable_income_above_threshold"], "expect": {"form_8995a_used": True, "form_8995_used": False}},
     "sort_order": 9},
]


FORMS: list[dict] = [
    {
        "identity": {
            "form_number": "8995A",
            "form_title": "Form 8995-A — Qualified Business Income Deduction (TY2025)",
            "notes": (
                "RE-AUTHORED over the thin hand-authored draft (20 facts / 6 rules / 15 lines whose numbers "
                "did NOT match the form). The real face: Part I (businesses A/B/C + SSTB/aggregation/patron), "
                "Part II (per-business W-2/UBIA limit), Part III (phase-in), Part IV (REIT/PTP + income limit "
                "→ 1040 L13), Schedule A (SSTB applicable %), Schedule B (aggregation — full engine), "
                "Schedule C (loss netting), Schedule D (patron reduction L14 + capped DPAD L38 — BUILT "
                "2026-07-03, Ken ruling for MeF ATS S2; was RED-deferred). Verified against the 2025 "
                "f8995a.pdf + i8995a + f8995ad Rev 12-2022 (NOT memory). Used ABOVE the §199A threshold OR "
                "for any patron at any income (face line-3 skip at/below); the simplified 8995 otherwise."
            ),
        },
        "facts": F8995A_FACTS,
        "rules": F8995A_RULES,
        "lines": F8995A_LINES,
        "diagnostics": F8995A_DIAGNOSTICS,
        "scenarios": F8995A_SCENARIOS,
        "rule_links": F8995A_RULE_LINKS,
    },
]


class Command(BaseCommand):
    help = (
        "Load the Form 8995-A spec (above-threshold QBI: W-2/UBIA limit, SSTB "
        "phase-in, aggregation, loss netting). Refuses to seed until Ken sets "
        "READY_TO_SEED=True after the in-session review walk."
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()

        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad FORM 8995-A spec (above-threshold QBI)\n"))

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
        self._retire_stale_8995a()
        self._upsert_form_links(sources)
        self._load_flow_assertions()
        self._report_totals()

    # ─────────────────────────────────────────────────────────────────────────
    # Safety guard
    # ─────────────────────────────────────────────────────────────────────────

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
                "\nREFUSING TO SEED FORM 8995-A: not cleared to seed.\n\n"
                "Content is authored, but seeding is gated until Ken reviews the packet\n"
                "(W1–W7: Schedule A applicable %, Schedule C loss netting, Schedule B\n"
                "aggregation asserted-vs-enforced, patron/DPAD RED-defer, line-34 net cap\n"
                "gain reuse, phase-in range non-indexed, schedule PDF layout deferred) and\n"
                "flips the sentinel.\n\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True to proceed)\n\n"
                "NOTE: seeding RE-AUTHORS the 8995A draft — it retires the stub artifacts\n"
                "(R001-R006, the mismatched lines/facts/tests) and writes the real face.\n\n"
                f"Currently empty / placeholder:\n  {still_empty}\n\n"
                "To proceed: review the module-level data lists, then set READY_TO_SEED\n"
                "= True. Idempotent via update_or_create — safe to re-run after edits."
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Topics / sources (mirror load_1040_schedule_c.py exactly)
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
                    AuthoritySourceTopic.objects.get_or_create(
                        authority_source=source, authority_topic=topic,
                    )
        for code in EXISTING_SOURCES_TO_REFERENCE:
            src = AuthoritySource.objects.filter(source_code=code).first()
            if src:
                sources[code] = src
            else:
                self.stdout.write(self.style.WARNING(f"  existing source {code} NOT FOUND — links to it will be skipped"))
        self.stdout.write(f"Sources ready: {len(sources)}")
        return sources

    def _load_new_excerpts_on_existing(self, sources):
        ct = 0
        for code, exc in NEW_EXCERPTS_ON_EXISTING:
            src = sources.get(code) or AuthoritySource.objects.filter(source_code=code).first()
            if not src:
                self.stdout.write(self.style.WARNING(f"  source {code} not found — skipping new excerpt"))
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

    def _upsert_rules(self, form, rules_data) -> dict:
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
    # Retire the thin 8995A draft artifacts not in the re-authored sets
    # ─────────────────────────────────────────────────────────────────────────

    def _retire_stale_8995a(self):
        form = TaxForm.objects.filter(
            form_number="8995A", jurisdiction=FORM_JURISDICTION,
            tax_year=FORM_TAX_YEAR, version=FORM_VERSION,
        ).first()
        if not form:
            return
        keep_facts = {f["fact_key"] for f in F8995A_FACTS}
        keep_rules = {r["rule_id"] for r in F8995A_RULES}
        keep_lines = {ln["line_number"] for ln in F8995A_LINES}
        keep_diags = {d["diagnostic_id"] for d in F8995A_DIAGNOSTICS}
        keep_tests = {t["scenario_name"] for t in F8995A_SCENARIOS}

        removed = {}
        removed["facts"] = FormFact.objects.filter(tax_form=form).exclude(fact_key__in=keep_facts).delete()[0]
        removed["rules"] = FormRule.objects.filter(tax_form=form).exclude(rule_id__in=keep_rules).delete()[0]
        removed["lines"] = FormLine.objects.filter(tax_form=form).exclude(line_number__in=keep_lines).delete()[0]
        removed["diagnostics"] = FormDiagnostic.objects.filter(tax_form=form).exclude(diagnostic_id__in=keep_diags).delete()[0]
        removed["tests"] = TestScenario.objects.filter(tax_form=form).exclude(scenario_name__in=keep_tests).delete()[0]
        total = sum(removed.values())
        if total:
            self.stdout.write(self.style.WARNING(
                f"  8995A draft retired: {removed} ({total} stale rows deleted — RuleAuthorityLinks cascade)"
            ))
        else:
            self.stdout.write("  8995A draft: nothing stale to retire (clean re-author)")

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
            FlowAssertion.objects.update_or_create(
                assertion_id=a.pop("assertion_id"), defaults=a,
            )
        self.stdout.write(f"  {len(FLOW_ASSERTIONS)} flow assertions")

    def _report_totals(self):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("FORM 8995-A loaded.")
        self.stdout.write(
            f"  facts {len(F8995A_FACTS)} / rules {len(F8995A_RULES)} / lines {len(F8995A_LINES)} / "
            f"diagnostics {len(F8995A_DIAGNOSTICS)} / tests {len(F8995A_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}"
        )
        self.stdout.write("=" * 60)
