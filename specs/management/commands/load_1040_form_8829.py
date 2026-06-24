"""Load the Form 8829 spec — Expenses for Business Use of Your Home.

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
Form 8829 figures the ACTUAL-EXPENSE deduction for the business use of a home
on Schedule C (Form 1040), line 30, plus any carryover to next year of amounts
disallowed by the §280A(c)(5) gross-income limitation. It is filed with
Schedule C; a separate Form 8829 is used for each home used for business.

The app ALREADY computes the SIMPLIFIED method ($5/sq ft, cap 300 sq ft → Sch C
line 30) in `compute_schedule_c.py`. The ACTUAL-EXPENSE path (this form) is today
RED-deferred via `D_SC_007` (square footage entered, simplified not elected).
This spec builds the actual-expense engine; `D_SC_007` narrows to the genuine
residual at the diagnostics leg (the D_8995_001 / 8582 narrow-on-compute precedent).

NO prior RS spec exists (lookup/8829/ → 404). This is a NEW form (not a re-author).

SCOPE (Ken-approved kickoff, AskUserQuestion 2026-06-24 — "BROADER: build the
Schedule A split"):
  COMPUTES (v1):
    • Part I 1-7 business % (area %; daycare hours-of-use fraction × area %)
    • Part II 8-36 — the FULL §280A(c)(5) gross-income limitation, 3 ordered tiers:
        – line 8 cap = Sch C line 29 + home-business gain − non-home loss
        – tier 1 (9-14): casualty / deductible mortgage interest / RE taxes
        – tier 2 (16-27): operating expenses, allowable = smaller of line 15 or 26
        – tier 3 (29-33): excess casualty + depreciation, smaller of line 28 or 32
        – line 36 → Schedule C line 30
    • Part III 37-42 — 39-yr nonresidential SL mid-month depreciation
    • Part IV 43-44 — operating + casualty/depreciation carryover to next year
    • The RE-TAX deductible-vs-excess split (lines 11/17, the Line 11 Worksheet) —
      COMPUTED, reusing the Schedule A SALT cap (`salt_line5e`) including the
      OBBBA $500k-MAGI 30% phasedown circular iteration (>$500k MAGI only)
  PREPARER-ASSERTED INPUTS (the way the IRS form itself works — figured on side
  worksheets and entered into columns (a) direct / (b) indirect):
    • all expense amounts (lines 9-22 except the computed RE-tax split)
    • the MORTGAGE deductible-vs-excess split (lines 10/16) for ITEMIZERS — the
      Pub 936 acquisition-debt limit is a PREPARER FACT app-wide (Schedule A takes
      mortgage interest as entered too; no Pub 936 engine exists anywhere). The
      STANDARD-DEDUCTION mortgage path IS computed (all → line 16). [W3]
    • carryover-in (lines 25/31) from the prior-year Form 8829 (proforma direct-entry)
  RED-DEFERS (v1 — each its own "prepare manually" RED, no silent gap):
    • line 35 casualty-loss portion → Form 4684 (not built; rare post-TCJA — disaster-only)
    • line 36 allocation across MORE THAN ONE business using the same home

═══════════════════════════════════════════════════════════════════════════
VERIFIED FORM STRUCTURE (2025 f8829.pdf + i8829, Rev. Mar 4 2026 — READ DIRECTLY,
NOT memory; IRC §280A(c)(5) ordering; Pub 946 39-yr mid-month MACRS table)
═══════════════════════════════════════════════════════════════════════════
Part I — Part of Your Home Used for Business
  1  Area used regularly & exclusively for business (or daycare/storage) — sq ft
  2  Total area of home — sq ft
  3  Line 1 ÷ line 2 (percentage)
  4  (Daycare) days used × hours per day → hr
  5  (Daycare) 8,760 (or 24 × days available if started/stopped mid-year)
  6  (Daycare) line 4 ÷ line 5 (decimal)
  7  Business %: daycare-not-exclusive → line 6 × line 3; all others → line 3
Part II — Figure Your Allowable Deduction              (a) Direct  (b) Indirect
  8  Sch C line 29 + gain from business use of home − loss not from home use [§280A cap]
  9  Casualty losses                                       [a/b]
  10 Deductible mortgage interest (col b only — never direct)
  11 Real estate taxes  [col a = Line 11 WS line 10; col b if SALT ≤ cap]
  12 Add 9, 10, 11
  13 Line 12 col (b) × line 7
  14 Line 12 col (a) + line 13           [tier-1 allowed: deductible-anyway items]
  15 Line 8 − line 14 (if ≤ 0, enter 0)  [remaining §280A cap after tier 1]
  16 Excess mortgage interest            [a/b]
  17 Excess real estate taxes (= Line 11 WS line 11)  [a]
  18 Insurance / 19 Rent / 20 Repairs & maintenance / 21 Utilities / 22 Other  [a/b]
  23 Add 16 through 22
  24 Line 23 col (b) × line 7
  25 Carryover of prior-year operating expenses (col a)   [proforma]
  26 Line 23 col (a) + line 24 + line 25
  27 Allowable operating expenses = SMALLER of line 15 or line 26   [tier-2 limit]
  28 Line 15 − line 27                   [remaining §280A cap after tier 2]
  29 Excess casualty losses
  30 Depreciation of your home (from line 42)
  31 Carryover of prior-year excess casualty losses & depreciation   [proforma]
  32 Add 29 through 31
  33 Allowable excess casualty + depreciation = SMALLER of line 28 or line 32 [tier-3 limit]
  34 Add lines 14, 27, and 33
  35 Casualty loss portion from lines 14 & 33 → Form 4684            [RED-defer]
  36 Allowable expenses for business use of home = line 34 − line 35 → Sch C line 30
Part III — Depreciation of Your Home
  37 Smaller of home's adjusted basis or FMV (incl. land) at first business use
  38 Value of land included on line 37
  39 Basis of building = line 37 − line 38
  40 Business basis = line 39 × line 7
  41 Depreciation % (39-yr nonresidential SL mid-month — table below)
  42 Depreciation allowable = line 40 × line 41 → line 30
Part IV — Carryover of Unallowed Expenses to next year
  43 Operating expenses = line 26 − line 27 (if < 0, enter 0)    → next-year line 25
  44 Excess casualty + depreciation = line 32 − line 33 (if < 0, enter 0) → next-year line 31

LINE 41 — 39-YR NONRESIDENTIAL REAL PROPERTY, MID-MONTH, STRAIGHT-LINE (Pub 946,
verbatim from i8829 line-41 table). FIRST YEAR (month first used for business):
  Jan 2.461 · Feb 2.247 · Mar 2.033 · Apr 1.819 · May 1.605 · Jun 1.391 ·
  Jul 1.177 · Aug 0.963 · Sep 0.749 · Oct 0.535 · Nov 0.321 · Dec 0.107  (percent)
  SUBSEQUENT full year (first used in a prior year, before the current year): 2.564%.
  (1/39 = 2.5641%. The table is year-INVARIANT — the MACRS schedule keys to the
  month-first-used relative to the recovery period, not the calendar year.)

LINE 11 WORKSHEET (RE-tax deductible-vs-excess split — the Schedule A coupling):
  ws2  = real estate taxes paid on the home used for business
  ws6  = ws2 × business % (line 7)
  ws7a = (all personal SALT: state income/sales + other RE + personal property) − ws6
  ws8  = the overall SALT deduction limit (= the Schedule A cap; the app reuses
         `salt_line5e(line5d, MAGI, fs, year)` — NOT the form's simplified 7b/7c/7d
         branching. The form's branching is a hand-computation shortcut; §164(b)(6)
         is the precise 30%-of-excess-over-$500k-MAGI phasedown to a $10k floor.)
  ws9  = max(0, ws8 − ws7a)
  ws10 = min(ws6, ws9)  → Form 8829 line 11 col (a)  [deductible business-home RE tax]
  ws11 = ws6 − ws10     → Form 8829 line 17          [excess → §280A operating tier]
  ITERATION: ws8 (the cap) depends on MAGI → AGI → Sch C net → home-office deduction
  (line 36) → line 11 → ... The i8829 Iteration Instructions resolve it by repeating
  until MAGI changes < $1. Engages ONLY when MAGI is in the phasedown band (>$500k);
  below the threshold the cap is the flat $40k and a single pass converges. [W4]

═══════════════════════════════════════════════════════════════════════════
requires_human_review WALK ITEMS (for Ken's in-session review)
═══════════════════════════════════════════════════════════════════════════
W1. §280A(c)(5) GROSS-INCOME LIMITATION ORDERING. The 3-tier ordering (line 8 cap →
    tier 1 deductible-anyway 9-14 → tier 2 operating 16-27 → tier 3 casualty/depr
    29-33), with operating limited to "smaller of remaining cap or total" and
    depreciation last (so it is the first to carry over). CONFIRM the tier order +
    that depreciation/casualty (not operating) is what carries to Part IV.
W2. PART III DEPRECIATION = 39-YR NONRESIDENTIAL SL, MID-MONTH. A home office is
    nonresidential real property (39-yr, 1/39 = 2.564%), NOT 27.5-yr residential
    rental — the business use is nonresidential even though the dwelling is a home.
    First-year % is mid-month by month-first-used (Jan 2.461% … Dec 0.107%). Basis
    = smaller of adjusted basis or FMV (incl. land) at first business use; land
    excluded; business % applied. Ken (depreciation CPA) CONFIRM the 39-yr life,
    the mid-month table, and the basis = lower-of-cost-or-FMV rule.
W3. THE MORTGAGE SPLIT (lines 10/16) STAYS PREPARER-ASSERTED FOR ITEMIZERS — the
    "Sch A split" the app computes is the RE-TAX SALT split (11/17), because the
    SALT cap exists (`salt_line5e`). The mortgage Pub 936 acquisition-debt limit is
    a PREPARER FACT everywhere in the app (Schedule A line 12: "Pub-936 debt-limit =
    preparer fact"); building a Pub 936 engine for 8829 alone would be inconsistent
    and is a separate workstream. The STANDARD-DEDUCTION mortgage/RE-tax path IS
    computed (all → line 16/17). CONFIRM: is the itemizer-mortgage-split-as-input
    acceptable for v1, or does Ken want a Pub 936 engine (a follow-up)?
W4. THE RE-TAX SALT SPLIT + MAGI ITERATION. The Line 11 Worksheet is computed,
    reusing the Schedule A SALT cap. The circular MAGI↔home-office↔AGI iteration
    engages only above the $500k phasedown threshold; v1 implements the fixed-point
    loop (the i8829 Iteration Instructions, converge < $1) at the compute leg.
    CONFIRM: implement the loop, OR compute one pass and fire a verify-RED for the
    >$500k case? (Recommend the loop — deterministic, matches the IRS instructions;
    the common itemizer (<$500k) needs no iteration.)
W5. CASUALTY (lines 9/29/35) is supported as a column INPUT so the tier math is
    correct when present, but line 35 (the casualty portion → Form 4684) is
    RED-deferred (Form 4684 not built; post-TCJA personal casualty is disaster-area
    only — RARE). CONFIRM the casualty-input / 4684-routing-deferred split.
W6. CONSTANTS. Daycare line 5 = 8,760 hr (2025 & 2026, both non-leap). Depreciation
    table year-invariant (Pub 946). SALT cap reuses `compute_schedule_a.SALT`
    (2025 $40k/$500k @ 30%; 2026 $40.4k/$505k @ 30%; $10k floor). CONFIRM the reuse
    (single source — no re-typed SALT constants in 8829).

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
# SAFETY GUARD — flip ONLY after Ken's in-session review walk (W1–W6 above,
# the verified §280A ordering, the depreciation table, the RE-tax/mortgage split
# posture, the RED-defer enumeration). Until then the command writes nothing.
#
# FLIPPED 2026-06-24 — Ken APPROVED the review walk in-session ("Approve as
# drafted"): W1 the §280A(c)(5) 3-tier ordering (deductible-anyway → operating →
# depreciation; depreciation carries over first) blessed; W2 the 39-yr
# nonresidential mid-month SL depreciation + lower-of-cost-or-FMV-ex-land basis
# blessed; W3 the ITEMIZER mortgage split (10/16) stays a preparer input (Pub 936
# = preparer fact app-wide, matching Schedule A; the standard-deduction path is
# computed); W4 the >$500k-MAGI RE-tax split runs the fixed-point iteration (the
# i8829 Iteration Instructions); W5 casualty supported as a column input, line-35
# → Form 4684 RED-deferred; W6 constants reused from compute_schedule_a (no
# re-typed SALT). Math gate check_8829_integrity.py ALL PASS (depreciation table +
# daycare + SALT constants + helpers + 11 scenarios re-derived).
# ═══════════════════════════════════════════════════════════════════════════
READY_TO_SEED = True


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1040"]


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS (every value cited; never training memory)
#   Depreciation table — i8829 (2025) line-41 instructions / Pub 946 (39-yr
#     nonresidential real property, mid-month convention, straight-line).
#   Daycare hours — i8829 line 5 ("otherwise, enter 8,760").
#   SALT cap — REUSED from compute_schedule_a.SALT (single source; §164(b)(6)
#     as amended by OBBBA). Documented here for the math gate / FA pin only.
# ═══════════════════════════════════════════════════════════════════════════

# Line 41 — first-year mid-month percentage by month first used for business.
# Year-INVARIANT (the MACRS 39-yr table keys to the month relative to the
# recovery period, not the calendar year).
DEPRECIATION_FIRST_YEAR_PCT: dict[int, str] = {
    1: "2.461", 2: "2.247", 3: "2.033", 4: "1.819", 5: "1.605", 6: "1.391",
    7: "1.177", 8: "0.963", 9: "0.749", 10: "0.535", 11: "0.321", 12: "0.107",
}
# Subsequent full year (home first used for business in a PRIOR year): 1/39.
DEPRECIATION_SUBSEQUENT_PCT = "2.564"

# Daycare line 5 base — hours available in the year (non-leap). 2025 & 2026.
DAYCARE_HOURS_PER_YEAR: dict[int, int] = {2025: 8760, 2026: 8760}

# SALT cap — DOCUMENTED reference matching compute_schedule_a.SALT (the RE-tax
# split REUSES `salt_line5e`; these values are NOT re-typed into compute — single
# source — they exist here only to pin the FA constants_check + the math gate).
SALT_CAP_REF: dict[int, dict] = {
    2025: {"cap": 40000, "cap_mfs": 20000, "threshold": 500000, "threshold_mfs": 250000,
           "floor": 10000, "floor_mfs": 5000, "rate": "0.30"},
    2026: {"cap": 40400, "cap_mfs": 20200, "threshold": 505000, "threshold_mfs": 252500,
           "floor": 10000, "floor_mfs": 5000, "rate": "0.30"},
}


def depreciation_pct(first_use_year: int, tax_year: int, month_first_used: int) -> str:
    """Line 41. First year (placed in service this tax year) → mid-month table by
    month; a full subsequent year → 2.564% (1/39). The final partial (disposal)
    year is RED-deferred (Pub 946 Sale-or-Disposition adjustment — rare)."""
    if first_use_year == tax_year:
        return DEPRECIATION_FIRST_YEAR_PCT.get(int(month_first_used) or 1, "2.461")
    return DEPRECIATION_SUBSEQUENT_PCT


def daycare_hours_for(year: int) -> int:
    return DAYCARE_HOURS_PER_YEAR.get(year) or DAYCARE_HOURS_PER_YEAR[2026]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY TOPICS
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("business_use_of_home", "Form 8829 — Expenses for business use of home: §280A(c) eligibility, the (c)(5) gross-income limitation ordering, 39-yr home depreciation, carryover"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_1040_FORM",  # Schedule C line 29/30 cross-form lines
]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY SOURCES (CREATE) — transcribed 2026-06-24 from the on-disk
# f8829.pdf (read directly) + i8829 (Rev. Mar 4 2026) + IRC §280A + §168 + Pub 946.
# requires_human_review = the W-items in the docstring.
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_8829_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "2025 Form 8829 — Expenses for Business Use of Your Home",
        "citation": "Form 8829 (2025); f8829.pdf; Attachment Sequence No. 176",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f8829.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["business_use_of_home"],
        "excerpts": [
            {
                "excerpt_label": "Form 8829 Part I–II (2025) — verified line face + §280A tier ordering",
                "excerpt_text": (
                    "Part I: 1 area used for business; 2 total area; 3 = 1÷2 (%); 4-6 daycare hours-of-use; 7 business "
                    "% (daycare-not-exclusive = line 6 × line 3, else line 3). Part II: 8 = Sch C line 29 + gain from "
                    "business use of home − loss not from home use. Columns (a) Direct / (b) Indirect. 9 casualty; 10 "
                    "deductible mortgage interest; 11 real estate taxes; 12 = 9+10+11; 13 = line 12 col (b) × line 7; "
                    "14 = line 12 col (a) + line 13; 15 = line 8 − line 14 (≥0). 16 excess mortgage interest; 17 excess "
                    "real estate taxes; 18 insurance; 19 rent; 20 repairs; 21 utilities; 22 other; 23 = 16..22; 24 = "
                    "line 23 col (b) × line 7; 25 carryover prior operating; 26 = line 23 col (a) + 24 + 25; 27 = "
                    "SMALLER of 15 or 26; 28 = 15 − 27; 29 excess casualty; 30 depreciation (line 42); 31 carryover "
                    "prior casualty/depr; 32 = 29+30+31; 33 = SMALLER of 28 or 32; 34 = 14+27+33; 35 casualty → Form "
                    "4684; 36 = 34 − 35 → Schedule C line 30."
                ),
                "summary_text": "Form 8829 Part I-II: business % → §280A 3-tier limitation (deductible / operating / casualty+depr) → line 36 → Sch C line 30.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Form 8829 Part III–IV (2025) — depreciation + carryover",
                "excerpt_text": (
                    "Part III: 37 smaller of home's adjusted basis or FMV; 38 land value; 39 = 37 − 38 (building basis); "
                    "40 = line 39 × line 7 (business basis); 41 depreciation % (39-yr nonresidential SL mid-month: "
                    "first-year by month Jan 2.461%…Dec 0.107%, subsequent full year 2.564%); 42 = line 40 × line 41 "
                    "→ line 30. Part IV: 43 operating-expense carryover = line 26 − line 27 (if < 0, enter -0-); 44 "
                    "excess-casualty-and-depreciation carryover = line 32 − line 33 (if < 0, enter -0-). The carryover "
                    "is subject to next year's gross-income limit whether or not the same home is used."
                ),
                "summary_text": "Part III = 39-yr mid-month home depreciation → line 30. Part IV = operating + casualty/depr carryover to next year.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_8829_INSTR",
        "source_type": "official_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "2025 Instructions for Form 8829 — Expenses for Business Use of Your Home",
        "citation": "Instructions for Form 8829 (2025), Rev. Mar 4 2026",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/instructions/i8829",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["business_use_of_home"],
        "excerpts": [
            {
                "excerpt_label": "Lines 9-11 / 16-17 — deductible-vs-excess split (standard deduction vs itemizer)",
                "excerpt_text": (
                    "Lines 9-11 are for expenses that would be deductible as a PERSONAL expense even without business "
                    "use (casualty, mortgage interest, real estate taxes). Standard-deduction taxpayers: enter NO "
                    "mortgage interest or RE taxes on lines 10/11; instead claim the entire business-use portion on "
                    "lines 16/17. Itemizers: line 10 = the Pub-936-deductible home mortgage interest attributable to "
                    "the home (col b only — mortgage interest is never a direct/col-a expense); line 16 = the excess "
                    "(acquisition-debt interest disallowed by the §163(h)(3) limit). Line 11 / line 17: use the Line 11 "
                    "Worksheet — ws6 = home RE taxes × business %; ws8 = the overall SALT limit; ws10 = smaller of ws6 "
                    "or (ws8 − other personal SALT) → line 11 col (a); ws11 = ws6 − ws10 → line 17. The $40,000 "
                    "($20,000 MFS) SALT cap is reduced if MAGI > $500,000 ($250,000 MFS) but not below $10,000; the "
                    "Iteration Instructions repeat until MAGI changes < $1 (home-office deduction ↔ AGI ↔ cap)."
                ),
                "summary_text": "Standard deduction → all mortgage/RE to lines 16/17. Itemizer → line 10 (Pub 936 fact) + Line 11 Worksheet SALT split (11/17) with the MAGI iteration.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Line 41/42 depreciation table + Part IV carryover",
                "excerpt_text": (
                    "Line 41: if first used for business in 2025, the mid-month percentage for the month placed in "
                    "service (January 2.461% … December 0.107%); if first used after May 12 1993 and before 2025, "
                    "2.564%. Line 42 = line 40 × line 41 → line 30 (do NOT also include on Schedule C line 13; if first "
                    "used in 2025, also report on Form 4562 line 19j). Line 25/31: carryover of prior-year operating "
                    "expenses / excess casualty + depreciation = the prior-year Form 8829 line 43 / line 44 (or the "
                    "2024 Simplified Method Worksheet line 6a/6b). Line 43 = line 26 − line 27; line 44 = line 32 − "
                    "line 33 (each floored at 0) → next year."
                ),
                "summary_text": "Line 41 = 39-yr mid-month % (first-year by month, else 2.564%); line 42 → line 30. Carryover in 25/31 = prior 43/44; out 43/44 floored 0.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_280A",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "IRC §280A — Disallowance of certain expenses in connection with business use of home",
        "citation": "26 U.S.C. §280A (§280A(c)(1) business-use exception; §280A(c)(5) gross-income limitation + carryover)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/280A",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 10.0,
        "topics": ["business_use_of_home"],
        "excerpts": [
            {
                "excerpt_label": "§280A(c)(1) business use + (c)(5) gross-income limitation & ordering",
                "excerpt_text": (
                    "§280A(c)(1): a deduction is allowed for the portion of a dwelling unit used exclusively and "
                    "regularly as the principal place of business, a place to meet patients/clients/customers, or a "
                    "separate structure. §280A(c)(5): the deductions allowable for business use of the home (other than "
                    "those allowable without regard to business use — i.e., mortgage interest and real estate taxes) "
                    "may not exceed the gross income from the business use reduced by (A) the deductions allocable to "
                    "the business that are not home-use deductions, and (B) the home-use deductions allowable without "
                    "regard to business use. Amounts disallowed by this limitation carry over to the succeeding year, "
                    "subject to the same limitation. The ordering: otherwise-allowable items first, then operating "
                    "expenses, then depreciation (so depreciation is the first to be disallowed and carried over)."
                ),
                "summary_text": "§280A(c)(5): home-office deduction capped at business gross income; disallowed amounts carry over; deduct in order — deductible-anyway, then operating, then depreciation.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_168_PUB946",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "IRC §168 + Pub 946 — depreciation of the home (39-yr nonresidential real property, mid-month SL)",
        "citation": "26 U.S.C. §168(c) (recovery period) + §168(d)(2) (mid-month) + Pub 946 Table A-7a (39-yr nonresidential)",
        "issuer": "U.S. Congress / IRS",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/168",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 10.0,
        "topics": ["business_use_of_home"],
        "excerpts": [
            {
                "excerpt_label": "§168 — 39-yr nonresidential real property, mid-month, straight-line",
                "excerpt_text": (
                    "Business-use real property (a home office) is nonresidential real property under §168(e)(2)(B): a "
                    "39-year recovery period (§168(c)), the mid-month convention (§168(d)(2)), and the straight-line "
                    "method (§168(b)(3)). 1/39 = 2.564% per full year; the year placed in service is prorated mid-month "
                    "(Pub 946 Table A-7a: month 1 = 2.461% … month 12 = 0.107%). The home office is nonresidential "
                    "(business use) even though the dwelling is a residence. Basis for depreciation = the smaller of "
                    "the home's adjusted basis or FMV at first business use, excluding land, multiplied by the "
                    "business-use percentage."
                ),
                "summary_text": "Home office = 39-yr nonresidential real property, mid-month SL (2.564%/yr; first year by month). Basis = lower of adj basis or FMV, ex-land, × business %.",
                "is_key_excerpt": True,
            },
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_8829_FORM", "8829", "defines"),
    ("IRC_280A", "8829", "supports"),
    ("IRC_168_PUB946", "8829", "supports"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 8829 — FACTS  (h_ = home-office; per Schedule C / per home)
# ═══════════════════════════════════════════════════════════════════════════

F8829_FACTS: list[dict] = [
    # ── Part I — business percentage ──
    {"fact_key": "h_use_actual_expense", "label": "Elect actual-expense method (Form 8829, not simplified)",
     "data_type": "boolean", "default_value": "false", "sort_order": 1,
     "notes": "PER SCHEDULE C. True → Form 8829 engaged (this engine); False → the simplified $5/sq ft method (compute_schedule_c). Mutually exclusive."},
    {"fact_key": "h_area_business", "label": "Line 1 — area used regularly & exclusively for business (sq ft)",
     "data_type": "decimal", "default_value": "0", "sort_order": 2,
     "notes": "Line 1. Or area used regularly for daycare / inventory storage (the §280A(c)(1)/(c)(2)/(c)(4) exceptions)."},
    {"fact_key": "h_area_total", "label": "Line 2 — total area of home (sq ft)",
     "data_type": "decimal", "default_value": "0", "sort_order": 3,
     "notes": "Line 2. Any reasonable unit if consistent with line 1."},
    {"fact_key": "h_is_daycare", "label": "Daycare facility NOT used exclusively for business?",
     "data_type": "boolean", "default_value": "false", "sort_order": 4,
     "notes": "Drives Part I lines 4-6: line 7 = line 6 × line 3 (else line 7 = line 3)."},
    {"fact_key": "h_daycare_hours", "label": "Line 4 — hours used for daycare during the year",
     "data_type": "decimal", "default_value": "0", "sort_order": 5,
     "notes": "Line 4 = days × hours/day (i8829 example: 250 weekdays × 12 + 50 Saturdays × 8 = 3,400)."},
    {"fact_key": "h_daycare_hours_available", "label": "Line 5 — hours available (8,760, or 24 × days if started/stopped)",
     "data_type": "decimal", "default_value": "8760", "sort_order": 6,
     "notes": "Line 5 = 8,760 (full year), or 24 × days available if daycare started/stopped mid-year. 2025 & 2026 non-leap."},
    {"fact_key": "h_business_pct", "label": "Line 7 — business use percentage (OUTPUT)",
     "data_type": "decimal", "sort_order": 7,
     "notes": "OUTPUT. = line 3 (= line1/line2), or for daycare line 6 × line 3. Drives every indirect-expense allocation + line 40."},
    # ── Part II — line 8 gross-income cap ──
    {"fact_key": "h_sch_c_line29", "label": "Line 8 source — Schedule C line 29 (tentative profit)",
     "data_type": "decimal", "default_value": "0", "sort_order": 10,
     "notes": "Sch C line 29 = gross income − expenses BEFORE the home-office deduction (line 30). The §280A(c)(5) gross-income cap base."},
    {"fact_key": "h_home_business_gain", "label": "Line 8 — gain from business use of home (Form 8949/4797, add)",
     "data_type": "decimal", "default_value": "0", "sort_order": 11,
     "notes": "Line 8 add: gain on Form 8949/Sch D or 4797 derived from the business use of the home. Rare; preparer fact."},
    {"fact_key": "h_non_home_loss", "label": "Line 8 — loss NOT from business use of home (subtract)",
     "data_type": "decimal", "default_value": "0", "sort_order": 12,
     "notes": "Line 8 subtract: a loss from the trade/business allocable to it but NOT to the use of the home. Rare; preparer fact."},
    {"fact_key": "h_line8_cap", "label": "Line 8 — §280A gross-income limit (OUTPUT)",
     "data_type": "decimal", "sort_order": 13,
     "notes": "OUTPUT. = Sch C line 29 + home_business_gain − non_home_loss. The ceiling on the operating + depreciation deductions."},
    # ── Tier 1 — deductible-anyway items (9-14) ──
    {"fact_key": "h_casualty_direct", "label": "Line 9 col (a) — casualty losses (direct)",
     "data_type": "decimal", "default_value": "0", "sort_order": 20,
     "notes": "Line 9 direct. Post-TCJA personal casualty = federally-declared-disaster only. Line 35 routing → Form 4684 RED-deferred (W5)."},
    {"fact_key": "h_casualty_indirect", "label": "Line 9 col (b) — casualty losses (indirect)",
     "data_type": "decimal", "default_value": "0", "sort_order": 21,
     "notes": "Line 9 indirect (× business % at line 13)."},
    {"fact_key": "h_mortgage_deductible", "label": "Line 10 col (b) — deductible mortgage interest (itemizer; Pub 936 fact)",
     "data_type": "decimal", "default_value": "0", "sort_order": 22,
     "notes": "Line 10 (col b ONLY — mortgage interest is never a direct expense). The Pub-936-deductible home portion (preparer fact). Standard deduction → 0 (all → line 16). W3."},
    {"fact_key": "h_re_taxes_home", "label": "Line 11 source — real estate taxes paid on the home (total)",
     "data_type": "decimal", "default_value": "0", "sort_order": 23,
     "notes": "The RE tax on the home used for business (NOT yet allocated). The Line 11 Worksheet splits it: line 11 col (a) deductible vs line 17 excess (reuses the Sch A SALT cap). Standard deduction → all to line 17."},
    {"fact_key": "h_personal_salt_other", "label": "Line 11 WS — other personal SALT (income/sales + other RE + personal property)",
     "data_type": "decimal", "default_value": "0", "sort_order": 24,
     "notes": "Line 11 Worksheet lines 1/3/4 (excludes the home RE tax). Read from Schedule A at compute (scha_salt_income_or_sales + other RE + personal property). Drives ws7a."},
    {"fact_key": "h_itemizing", "label": "Itemizing (Schedule A filed)?",
     "data_type": "boolean", "default_value": "false", "sort_order": 25,
     "notes": "Drives the deductible-vs-excess split. False → mortgage/RE all to lines 16/17 (computed). True → line 10 (Pub 936 fact) + Line 11 Worksheet (computed)."},
    {"fact_key": "h_line11_deductible", "label": "Line 11 col (a) — deductible RE tax (OUTPUT)", "data_type": "decimal", "sort_order": 26,
     "notes": "OUTPUT = Line 11 Worksheet line 10 = min(home RE tax × business %, SALT cap − other personal SALT)."},
    {"fact_key": "h_line14_tier1", "label": "Line 14 — tier-1 allowed (OUTPUT)", "data_type": "decimal", "sort_order": 27,
     "notes": "OUTPUT = line 12 col (a) + line 12 col (b) × line 7. The deductible-anyway items (casualty/mortgage/RE) at the allocated amount."},
    {"fact_key": "h_line15_remaining", "label": "Line 15 — cap remaining after tier 1 (OUTPUT)", "data_type": "decimal", "sort_order": 28,
     "notes": "OUTPUT = max(0, line 8 − line 14)."},
    # ── Tier 2 — operating expenses (16-27) ──
    {"fact_key": "h_excess_mortgage", "label": "Line 16 — excess mortgage interest (col b; over-limit / standard-deduction)",
     "data_type": "decimal", "default_value": "0", "sort_order": 30,
     "notes": "Line 16. Standard deduction → the full home acquisition-debt interest. Itemizer → the §163(h)(3)-disallowed excess (Pub 936 fact). Operating-tier (business %, §280A-limited)."},
    {"fact_key": "h_excess_re_taxes", "label": "Line 17 — excess real estate taxes (OUTPUT/input)", "data_type": "decimal", "sort_order": 31,
     "notes": "Line 17 = Line 11 Worksheet line 11 (computed for itemizers); standard deduction → all home RE tax. Operating-tier."},
    {"fact_key": "h_insurance_direct", "label": "Line 18 col (a) — insurance (direct)", "data_type": "decimal", "default_value": "0", "sort_order": 32, "notes": "Line 18 direct."},
    {"fact_key": "h_insurance_indirect", "label": "Line 18 col (b) — insurance (indirect)", "data_type": "decimal", "default_value": "0", "sort_order": 33, "notes": "Line 18 indirect (× business %)."},
    {"fact_key": "h_rent_indirect", "label": "Line 19 col (b) — rent (renters only)", "data_type": "decimal", "default_value": "0", "sort_order": 34, "notes": "Line 19 (col b). Rent paid if you rent rather than own."},
    {"fact_key": "h_repairs_direct", "label": "Line 20 col (a) — repairs & maintenance (direct)", "data_type": "decimal", "default_value": "0", "sort_order": 35, "notes": "Line 20 direct."},
    {"fact_key": "h_repairs_indirect", "label": "Line 20 col (b) — repairs & maintenance (indirect)", "data_type": "decimal", "default_value": "0", "sort_order": 36, "notes": "Line 20 indirect (× business %)."},
    {"fact_key": "h_utilities_direct", "label": "Line 21 col (a) — utilities (direct)", "data_type": "decimal", "default_value": "0", "sort_order": 37, "notes": "Line 21 direct."},
    {"fact_key": "h_utilities_indirect", "label": "Line 21 col (b) — utilities (indirect)", "data_type": "decimal", "default_value": "0", "sort_order": 38, "notes": "Line 21 indirect (× business %)."},
    {"fact_key": "h_other_direct", "label": "Line 22 col (a) — other operating expenses (direct)", "data_type": "decimal", "default_value": "0", "sort_order": 39, "notes": "Line 22 direct."},
    {"fact_key": "h_other_indirect", "label": "Line 22 col (b) — other operating expenses (indirect)", "data_type": "decimal", "default_value": "0", "sort_order": 40, "notes": "Line 22 indirect (× business %)."},
    {"fact_key": "h_carryover_operating_prior", "label": "Line 25 — carryover of prior-year operating expenses (proforma)",
     "data_type": "decimal", "default_value": "0", "sort_order": 41,
     "notes": "Line 25 = prior-year Form 8829 line 43 (or 2024 Simplified Method WS line 6a). Direct-entry now; the proforma producer rolls it forward later."},
    {"fact_key": "h_line27_operating", "label": "Line 27 — allowable operating expenses (OUTPUT)", "data_type": "decimal", "sort_order": 42,
     "notes": "OUTPUT = SMALLER of line 15 (remaining cap) or line 26 (total operating). The §280A tier-2 limit."},
    {"fact_key": "h_line28_remaining", "label": "Line 28 — cap remaining after tier 2 (OUTPUT)", "data_type": "decimal", "sort_order": 43,
     "notes": "OUTPUT = line 15 − line 27."},
    # ── Tier 3 — excess casualty + depreciation (29-33) ──
    {"fact_key": "h_excess_casualty", "label": "Line 29 — excess casualty losses (× business %)",
     "data_type": "decimal", "default_value": "0", "sort_order": 50,
     "notes": "Line 29 = casualty in excess of line 9, × business %. Tier-3. Line 35 portion → Form 4684 RED-deferred (W5)."},
    {"fact_key": "h_carryover_casdep_prior", "label": "Line 31 — carryover of prior-year casualty + depreciation (proforma)",
     "data_type": "decimal", "default_value": "0", "sort_order": 51,
     "notes": "Line 31 = prior-year Form 8829 line 44 (or 2024 Simplified Method WS line 6b). Direct-entry now; proforma producer rolls it forward."},
    {"fact_key": "h_line33_casdep", "label": "Line 33 — allowable casualty + depreciation (OUTPUT)", "data_type": "decimal", "sort_order": 52,
     "notes": "OUTPUT = SMALLER of line 28 (remaining cap) or line 32 (total casualty+depr). The §280A tier-3 limit; depreciation is the first to be disallowed/carried over."},
    # ── Part III — depreciation ──
    {"fact_key": "h_basis_or_fmv", "label": "Line 37 — smaller of home's adjusted basis or FMV (incl. land) at first business use",
     "data_type": "decimal", "default_value": "0", "sort_order": 60,
     "notes": "Line 37. Cost/other basis OR (if less) FMV at first business use. Not adjusted for later depreciation/FMV change."},
    {"fact_key": "h_land_value", "label": "Line 38 — value of land included on line 37",
     "data_type": "decimal", "default_value": "0", "sort_order": 61,
     "notes": "Line 38. Land is non-depreciable → subtracted."},
    {"fact_key": "h_first_use_year", "label": "Year the home was first used for business",
     "data_type": "integer", "default_value": "0", "sort_order": 62,
     "notes": "Drives line 41: == tax year → first-year mid-month % by month; < tax year → 2.564%."},
    {"fact_key": "h_month_first_used", "label": "Month (1-12) first used for business (first year only)",
     "data_type": "integer", "default_value": "1", "sort_order": 63,
     "notes": "Line 41 first-year mid-month %: Jan 2.461% … Dec 0.107%."},
    {"fact_key": "h_depreciation", "label": "Line 42 — depreciation allowable (OUTPUT → line 30)", "data_type": "decimal", "sort_order": 64,
     "notes": "OUTPUT = line 40 (business basis) × line 41 (%). Feeds line 30 (tier 3). Not also on Sch C line 13. First year → Form 4562 line 19j."},
    # ── Outputs ──
    {"fact_key": "h_allowable_home_office", "label": "Line 36 — allowable home-office expense (OUTPUT → Schedule C line 30)",
     "data_type": "decimal", "sort_order": 70,
     "notes": "OUTPUT = line 34 − line 35. → Schedule C line 30 → Sch C line 31 net profit. Replaces the simplified $5/sq ft amount when actual-expense is elected."},
    {"fact_key": "h_carryover_operating_next", "label": "Line 43 — operating-expense carryover to next year (OUTPUT)",
     "data_type": "decimal", "sort_order": 71,
     "notes": "OUTPUT = max(0, line 26 − line 27). → next-year Form 8829 line 25. Stored for the proforma snapshot."},
    {"fact_key": "h_carryover_casdep_next", "label": "Line 44 — casualty/depreciation carryover to next year (OUTPUT)",
     "data_type": "decimal", "sort_order": 72,
     "notes": "OUTPUT = max(0, line 32 − line 33). → next-year Form 8829 line 31. Depreciation is the first to carry over under §280A(c)(5)."},
    # ── Constants ──
    {"fact_key": "h_depreciation_table", "label": "39-yr nonresidential mid-month depreciation table (CONSTANT, year-invariant)",
     "data_type": "decimal", "sort_order": 80,
     "notes": "CONSTANT (Pub 946): first-year by month Jan 2.461%…Dec 0.107%; subsequent 2.564% (1/39). Year-invariant."},
    {"fact_key": "h_salt_cap_ref", "label": "SALT deduction cap (REUSED from Schedule A — single source)", "data_type": "decimal", "sort_order": 81,
     "notes": "CONSTANT/REF: the Line 11 Worksheet overall limit = the Schedule A SALT cap (salt_line5e): 2025 $40k/$20k MFS @ $500k MAGI 30% phasedown to a $10k floor; 2026 $40.4k/$505k. NOT re-typed in compute — reuses compute_schedule_a."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 8829 — RULES
# ═══════════════════════════════════════════════════════════════════════════

F8829_RULES: list[dict] = [
    {"rule_id": "R-8829-SCOPE", "title": "Scope gate — Form 8829 engaged (actual-expense home office)", "rule_type": "routing", "precedence": 0, "sort_order": 1,
     "formula": ("Form 8829 is computed when a Schedule C elects the ACTUAL-EXPENSE method for business use of the home "
                 "(h_use_actual_expense True, area entered). The SIMPLIFIED method ($5/sq ft, cap 300) is the mutually "
                 "exclusive alternative (compute_schedule_c). A separate Form 8829 per home. D_SC_007 (actual-expense "
                 "RED-defer) narrows to the genuine residual once this engine computes."),
     "inputs": ["h_use_actual_expense", "h_area_business", "h_area_total"], "outputs": [],
     "description": "PER SCHEDULE C. Replaces the D_SC_007 RED-defer for the supported actual-expense case."},
    {"rule_id": "R-8829-L3-AREA", "title": "Lines 1-3 — area business percentage", "rule_type": "calculation", "precedence": 1, "sort_order": 2,
     "formula": "Line 3 = line 1 (business area) ÷ line 2 (total area), as a percentage. Carried full-precision into the allocations.",
     "inputs": ["h_area_business", "h_area_total"], "outputs": ["3"],
     "description": "Part I. The raw area percentage."},
    {"rule_id": "R-8829-L7-BUSPCT", "title": "Line 7 — business use percentage (daycare hours-of-use)", "rule_type": "calculation", "precedence": 2, "sort_order": 3,
     "formula": ("For a daycare facility NOT used exclusively for business: line 6 = line 4 (hours used) ÷ line 5 (8,760, "
                 "or 24 × days available); line 7 = line 6 × line 3. All others: line 7 = line 3."),
     "inputs": ["h_is_daycare", "h_daycare_hours", "h_daycare_hours_available", "h_business_pct"], "outputs": ["4", "5", "6", "7"],
     "description": "Part I. Daycare gets a time-of-use haircut on top of the area %."},
    {"rule_id": "R-8829-L8-LIMIT", "title": "Line 8 — §280A gross-income limit", "rule_type": "calculation", "precedence": 3, "sort_order": 4,
     "formula": "Line 8 = Schedule C line 29 (tentative profit) + gain from business use of home − loss not from home use. The §280A(c)(5) ceiling.",
     "inputs": ["h_sch_c_line29", "h_home_business_gain", "h_non_home_loss"], "outputs": ["8"],
     "description": "Part II. The cap on the operating + depreciation deductions (mortgage interest / RE taxes are deductible above it)."},
    {"rule_id": "R-8829-T1-DEDUCT", "title": "Lines 9-15 — tier 1 (deductible-anyway: casualty / mortgage / RE tax)", "rule_type": "calculation", "precedence": 4, "sort_order": 5,
     "formula": ("Line 12 = lines 9 + 10 + 11 (each column). Line 13 = line 12 col (b) × line 7. Line 14 = line 12 col (a) "
                 "+ line 13. Line 15 = max(0, line 8 − line 14). These items are deductible regardless of the income limit; "
                 "they consume the cap first."),
     "inputs": ["h_casualty_direct", "h_casualty_indirect", "h_mortgage_deductible", "h_line11_deductible", "h_business_pct", "h_line8_cap"], "outputs": ["12", "13", "14", "15"],
     "description": "Part II tier 1. §280A(c)(5): otherwise-allowable deductions reduce the gross-income limit first."},
    {"rule_id": "R-8829-L11WS", "title": "Line 11 / 17 — RE-tax SALT split (Line 11 Worksheet; reuses Schedule A cap)", "rule_type": "calculation", "precedence": 5, "sort_order": 6,
     "formula": ("ITEMIZER: ws6 = home RE tax × business %; ws8 = the Schedule A SALT cap (salt_line5e — the §164(b)(6) "
                 "$40k/$20k cap with the $500k/$250k-MAGI 30% phasedown to a $10k floor); ws9 = max(0, ws8 − other "
                 "personal SALT); line 11 col (a) = min(ws6, ws9); line 17 = ws6 − line 11. The cap depends on MAGI → AGI "
                 "→ home-office deduction → iterate until MAGI changes < $1 (>$500k only). STANDARD DEDUCTION: line 11 = 0, "
                 "line 17 = home RE tax (all to the operating tier)."),
     "inputs": ["h_re_taxes_home", "h_personal_salt_other", "h_business_pct", "h_itemizing", "h_salt_cap_ref"], "outputs": ["11", "17"],
     "description": "Part II. The computed Schedule A split (the OBBBA $40k SALT cap + MAGI iteration). Reuses compute_schedule_a.salt_line5e (single source — W4)."},
    {"rule_id": "R-8829-MTG-SPLIT", "title": "Lines 10 / 16 — mortgage deductible-vs-excess split", "rule_type": "calculation", "precedence": 6, "sort_order": 7,
     "formula": ("STANDARD DEDUCTION: line 10 = 0; line 16 = full home acquisition-debt interest (all the business-use "
                 "portion). ITEMIZER: line 10 = the Pub-936-deductible home portion (preparer fact); line 16 = the excess "
                 "(§163(h)(3)-disallowed acquisition-debt interest, preparer fact). Mortgage interest is never col (a)."),
     "inputs": ["h_itemizing", "h_mortgage_deductible", "h_excess_mortgage"], "outputs": ["10", "16"],
     "description": "Part II. The mortgage Pub 936 limit is a preparer fact app-wide (Schedule A too) — itemizer split entered; standard-deduction path computed (W3)."},
    {"rule_id": "R-8829-T2-OPER", "title": "Lines 16-27 — tier 2 (operating expenses, smaller of cap or total)", "rule_type": "calculation", "precedence": 7, "sort_order": 8,
     "formula": ("Line 23 = lines 16 + 17 + 18 + 19 + 20 + 21 + 22 (each column). Line 24 = line 23 col (b) × line 7. "
                 "Line 26 = line 23 col (a) + line 24 + line 25 (prior-year carryover). Line 27 = SMALLER of line 15 "
                 "(remaining cap) or line 26 (total operating). The §280A tier-2 limit."),
     "inputs": ["h_excess_mortgage", "h_excess_re_taxes", "h_insurance_direct", "h_insurance_indirect", "h_rent_indirect",
                "h_repairs_direct", "h_repairs_indirect", "h_utilities_direct", "h_utilities_indirect", "h_other_direct",
                "h_other_indirect", "h_carryover_operating_prior", "h_business_pct", "h_line15_remaining"], "outputs": ["23", "24", "26", "27"],
     "description": "Part II tier 2. Operating expenses, limited to the income remaining after the deductible-anyway items."},
    {"rule_id": "R-8829-T3-CASDEP", "title": "Lines 28-33 — tier 3 (excess casualty + depreciation, smaller of cap or total)", "rule_type": "calculation", "precedence": 8, "sort_order": 9,
     "formula": ("Line 28 = line 15 − line 27. Line 32 = line 29 (excess casualty) + line 30 (depreciation, from line 42) "
                 "+ line 31 (prior-year carryover). Line 33 = SMALLER of line 28 (remaining cap) or line 32. Depreciation "
                 "is the LAST tier → the first to be disallowed and carried over (§280A(c)(5))."),
     "inputs": ["h_line15_remaining", "h_line27_operating", "h_excess_casualty", "h_depreciation", "h_carryover_casdep_prior"], "outputs": ["28", "32", "33"],
     "description": "Part II tier 3. Casualty + depreciation, limited to the income remaining after operating expenses."},
    {"rule_id": "R-8829-L36", "title": "Lines 34-36 — allowable home-office expense → Schedule C line 30", "rule_type": "calculation", "precedence": 9, "sort_order": 10,
     "formula": ("Line 34 = line 14 + line 27 + line 33. Line 35 = the casualty-loss portion of lines 14 & 33 → Form 4684 "
                 "(RED-deferred; 0 in v1 unless casualty present). Line 36 = line 34 − line 35 → Schedule C line 30."),
     "inputs": ["h_line14_tier1", "h_line27_operating", "h_line33_casdep"], "outputs": ["34", "35", "36"],
     "description": "Part II. The total allowable home-office deduction. Replaces the simplified amount on Sch C line 30."},
    {"rule_id": "R-8829-P3-DEPR", "title": "Lines 37-42 — depreciation of the home (39-yr nonresidential mid-month)", "rule_type": "calculation", "precedence": 10, "sort_order": 11,
     "formula": ("Line 39 = line 37 (smaller of basis or FMV, incl. land) − line 38 (land). Line 40 = line 39 × line 7 "
                 "(business basis). Line 41 = the 39-yr nonresidential SL mid-month % — first year by month (Jan 2.461% … "
                 "Dec 0.107%), else 2.564%. Line 42 = line 40 × line 41 → line 30."),
     "inputs": ["h_basis_or_fmv", "h_land_value", "h_business_pct", "h_first_use_year", "h_month_first_used", "h_depreciation_table"], "outputs": ["39", "40", "41", "42"],
     "description": "Part III. §168 39-yr nonresidential real property, mid-month SL (Ken's specialty — W2)."},
    {"rule_id": "R-8829-P4-CARRY", "title": "Lines 43-44 — carryover of unallowed expenses to next year", "rule_type": "calculation", "precedence": 11, "sort_order": 12,
     "formula": ("Line 43 = max(0, line 26 − line 27) (operating carryover). Line 44 = max(0, line 32 − line 33) "
                 "(excess casualty + depreciation carryover). → next year's lines 25 / 31. Stored for the proforma snapshot."),
     "inputs": ["h_line27_operating", "h_line33_casdep"], "outputs": ["43", "44"],
     "description": "Part IV. §280A(c)(5) carryover — disallowed amounts deduct next year subject to the same limit."},
    {"rule_id": "R-8829-DEFER", "title": "RED-defer — casualty → Form 4684 + multi-business allocation (no silent gap)", "rule_type": "routing", "precedence": 12, "sort_order": 13,
     "formula": ("If a casualty loss is present (line 9/29), the line-35 portion routes to Form 4684 (not built) → "
                 "D_8829_002 RED-defer. If the home is used in MORE THAN ONE business, the line-36 allocation across "
                 "businesses (§280A reasonable-method) → D_8829_003. The tier math still computes; the routing/allocation "
                 "is flagged so the preparer completes it. Never a silently-wrong number."),
     "inputs": ["h_casualty_direct", "h_casualty_indirect", "h_excess_casualty"], "outputs": ["35"],
     "description": "PER SCHEDULE C. The no-silent-gap guard (SPRINT quality rule 2) for the two deferred routings."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 8829 — LINES (exact, read from the 2025 f8829.pdf — 44 lines, 4 parts)
# ═══════════════════════════════════════════════════════════════════════════

F8829_LINES: list[dict] = [
    {"line_number": "1", "description": "Area used regularly & exclusively for business (or daycare/storage) — sq ft", "line_type": "input"},
    {"line_number": "2", "description": "Total area of home — sq ft", "line_type": "input"},
    {"line_number": "3", "description": "Divide line 1 by line 2 (percentage)", "line_type": "calculated"},
    {"line_number": "4", "description": "Daycare — days used × hours per day (hr)", "line_type": "input"},
    {"line_number": "5", "description": "Daycare — 8,760 (or 24 × days available if started/stopped)", "line_type": "input"},
    {"line_number": "6", "description": "Daycare — divide line 4 by line 5 (decimal)", "line_type": "calculated"},
    {"line_number": "7", "description": "Business percentage (daycare: line 6 × line 3; else line 3)", "line_type": "calculated"},
    {"line_number": "8", "description": "Sch C line 29 + gain from business use of home − loss not from home use", "line_type": "calculated"},
    {"line_number": "9", "description": "Casualty losses — col (a) direct / col (b) indirect", "line_type": "input"},
    {"line_number": "10", "description": "Deductible mortgage interest — col (b) (itemizer; Pub 936 fact)", "line_type": "input"},
    {"line_number": "11", "description": "Real estate taxes — col (a) deductible (Line 11 Worksheet) / col (b)", "line_type": "calculated"},
    {"line_number": "12", "description": "Add lines 9, 10, and 11 (each column)", "line_type": "calculated"},
    {"line_number": "13", "description": "Multiply line 12 col (b) by line 7", "line_type": "calculated"},
    {"line_number": "14", "description": "Add line 12 col (a) and line 13 (tier-1 allowed)", "line_type": "calculated"},
    {"line_number": "15", "description": "Subtract line 14 from line 8 (if ≤ 0, enter 0)", "line_type": "calculated"},
    {"line_number": "16", "description": "Excess mortgage interest — col (a)/(b)", "line_type": "input"},
    {"line_number": "17", "description": "Excess real estate taxes (Line 11 Worksheet line 11)", "line_type": "calculated"},
    {"line_number": "18", "description": "Insurance — col (a)/(b)", "line_type": "input"},
    {"line_number": "19", "description": "Rent — col (b) (renters)", "line_type": "input"},
    {"line_number": "20", "description": "Repairs and maintenance — col (a)/(b)", "line_type": "input"},
    {"line_number": "21", "description": "Utilities — col (a)/(b)", "line_type": "input"},
    {"line_number": "22", "description": "Other expenses — col (a)/(b)", "line_type": "input"},
    {"line_number": "23", "description": "Add lines 16 through 22 (each column)", "line_type": "calculated"},
    {"line_number": "24", "description": "Multiply line 23 col (b) by line 7", "line_type": "calculated"},
    {"line_number": "25", "description": "Carryover of prior-year operating expenses (proforma)", "line_type": "input"},
    {"line_number": "26", "description": "Add line 23 col (a), line 24, and line 25", "line_type": "calculated"},
    {"line_number": "27", "description": "Allowable operating expenses — smaller of line 15 or line 26", "line_type": "calculated"},
    {"line_number": "28", "description": "Limit on excess casualty + depreciation — line 15 − line 27", "line_type": "calculated"},
    {"line_number": "29", "description": "Excess casualty losses (× business %)", "line_type": "input"},
    {"line_number": "30", "description": "Depreciation of your home from line 42", "line_type": "calculated"},
    {"line_number": "31", "description": "Carryover of prior-year excess casualty losses + depreciation (proforma)", "line_type": "input"},
    {"line_number": "32", "description": "Add lines 29 through 31", "line_type": "calculated"},
    {"line_number": "33", "description": "Allowable excess casualty + depreciation — smaller of line 28 or line 32", "line_type": "calculated"},
    {"line_number": "34", "description": "Add lines 14, 27, and 33", "line_type": "calculated"},
    {"line_number": "35", "description": "Casualty loss portion → Form 4684 (RED-defer)", "line_type": "input"},
    {"line_number": "36", "description": "Allowable expenses for business use of home — line 34 − line 35 → Sch C line 30", "line_type": "total"},
    {"line_number": "37", "description": "Smaller of home's adjusted basis or FMV (incl. land)", "line_type": "input"},
    {"line_number": "38", "description": "Value of land included on line 37", "line_type": "input"},
    {"line_number": "39", "description": "Basis of building — line 37 − line 38", "line_type": "calculated"},
    {"line_number": "40", "description": "Business basis of building — line 39 × line 7", "line_type": "calculated"},
    {"line_number": "41", "description": "Depreciation percentage (39-yr nonresidential mid-month)", "line_type": "calculated"},
    {"line_number": "42", "description": "Depreciation allowable — line 40 × line 41 → line 30", "line_type": "calculated"},
    {"line_number": "43", "description": "Carryover of operating expenses — line 26 − line 27 (if < 0, enter 0)", "line_type": "calculated"},
    {"line_number": "44", "description": "Carryover of excess casualty + depreciation — line 32 − line 33 (if < 0, enter 0)", "line_type": "calculated"},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 8829 — DIAGNOSTICS
# ═══════════════════════════════════════════════════════════════════════════

F8829_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_8829_001", "title": "Home-office deduction limited by business income (carryover created)", "severity": "info",
     "condition": "line 36 < total home-office expenses (line 14 + line 26 + line 32); line 43 or line 44 > 0",
     "message": ("The home-office deduction is limited to the business's gross income (§280A(c)(5)): the total expenses "
                 "exceed Schedule C line 29, so part is disallowed this year and carries over to next year (Form 8829 "
                 "lines 43/44). Operating expenses are deducted before depreciation, so depreciation carries over first. "
                 "This is the '$0 / limited' explanation for the preparer."),
     "notes": "Info — the office-usability '$0/limited' explainer. The §280A income limitation binding is normal, not an error."},
    {"diagnostic_id": "D_8829_002", "title": "Casualty loss on Form 8829 — Form 4684 not generated (prepare manually)", "severity": "error",
     "condition": "h_casualty_direct / h_casualty_indirect / h_excess_casualty present (lines 9/29/35)",
     "message": ("Not supported — prepare manually: this Form 8829 has a casualty loss (line 9/29), and the casualty "
                 "portion on line 35 must be carried to Form 4684, which is not built this version. Post-TCJA a personal "
                 "casualty loss is deductible only in a federally declared disaster area. Complete Form 4684 by hand for "
                 "the line-35 amount."),
     "notes": "RED-defer line 35 → Form 4684 (W5). The tier math still computes; only the 4684 routing is deferred."},
    {"diagnostic_id": "D_8829_003", "title": "Home used in more than one business — allocate line 36 manually", "severity": "warning",
     "condition": "the home supports more than one Schedule C (multiple businesses sharing the home)",
     "message": ("This home is used in more than one business. The allowable expenses on Form 8829 line 36 must be "
                 "allocated across the businesses by any reasonable method (i8829 line 36), and each business reports "
                 "only its share on its Schedule C line 30. The engine computes the total; verify the allocation."),
     "notes": "RED-defer the line-36 multi-business allocation (rare). One 8829 per home; one Sch C is the common case."},
    {"diagnostic_id": "D_8829_004", "title": "Business area exceeds total area of home", "severity": "error",
     "condition": "line 1 (business area) > line 2 (total area)",
     "message": ("Form 8829 line 1 (area used for business) is greater than line 2 (total area of home). The business "
                 "percentage cannot exceed 100%. Check the square-footage entries."),
     "notes": "Data validation — a business % > 100% is impossible."},
    {"diagnostic_id": "D_8829_005", "title": "SALT cap reduced by income (MAGI phasedown) — RE-tax split iterated", "severity": "info",
     "condition": "itemizing AND MAGI > the SALT phasedown threshold ($500,000 / $250,000 MFS)",
     "message": ("Modified AGI exceeds the SALT phasedown threshold, so the $40,000 state-and-local-tax cap is reduced "
                 "(30% of the excess, not below $10,000). The real-estate-tax split on Form 8829 lines 11/17 was solved "
                 "by iterating the home-office deduction against AGI (i8829 Iteration Instructions). Verify the SALT "
                 "deduction on Schedule A."),
     "notes": "Info — surfaces the >$500k MAGI iteration so the preparer can verify the coupled SALT/home-office result (W4)."},
    {"diagnostic_id": "D_8829_006", "title": "First-year home office — report depreciation on Form 4562 line 19j", "severity": "info",
     "condition": "h_first_use_year == tax year AND line 42 > 0",
     "message": ("This is the first year the home is used for business, so the home-office depreciation (Form 8829 lines "
                 "40 and 42) must also be reported on Form 4562 line 19j (columns (b)/(c)/(g)). The amount is deducted "
                 "via Form 8829 line 30 → line 36 → Schedule C line 30, NOT on Schedule C line 13."),
     "notes": "Info — the Form 4562 line 19j first-year reporting (the render coupling is a follow-up; compute is self-contained)."},
    {"diagnostic_id": "D_8829_007", "title": "Daycare facility — verify license/registration (exclusive-use exception)", "severity": "info",
     "condition": "h_is_daycare True",
     "message": ("This Form 8829 uses the daycare exception to the exclusive-use rule (Part I lines 4-6). The taxpayer "
                 "must have applied for, been granted, or be exempt from a state daycare license/registration. Verify "
                 "eligibility; the hours-of-use percentage (line 6) reduces the area percentage."),
     "notes": "Info — the §280A(c)(4) daycare exception is a facts question (license) the preparer attests."},
    {"diagnostic_id": "D_8829_008", "title": "Actual-expense method elected but a required input is missing", "severity": "error",
     "condition": "h_use_actual_expense True AND (line 2 total area is 0, or basis entered without land/first-use year)",
     "message": ("The actual-expense home-office method (Form 8829) is elected, but a required input is missing: the "
                 "total area of the home (line 2) is needed for the business percentage, and any depreciation (Part III) "
                 "requires the basis, land value, and the year/month first used for business. Complete the inputs or "
                 "switch to the simplified method."),
     "notes": "Data validation — actual-expense needs the area + (if depreciating) the Part III basis inputs."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 8829 — TEST SCENARIOS (worked math; check_8829_integrity.py re-derives)
# ═══════════════════════════════════════════════════════════════════════════

F8829_SCENARIOS: list[dict] = [
    {"scenario_name": "8829-T1 — simple, standard deduction, not income-limited", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "filing_status": "single", "h_itemizing": False,
                "h_area_business": 200, "h_area_total": 2000, "h_sch_c_line29": 20000,
                "h_excess_mortgage": 6000, "h_excess_re_taxes": 3000, "h_insurance_indirect": 1200,
                "h_repairs_direct": 500, "h_utilities_indirect": 2400, "h_depreciation": 1000},
     "expected_outputs": {"line_7": 0.10, "line_8": 20000, "line_14": 0, "line_15": 20000,
                          "line_26": 1760, "line_27": 1760, "line_28": 18240, "line_32": 1000,
                          "line_33": 1000, "line_34": 2760, "line_36": 2760, "line_43": 0, "line_44": 0},
     "notes": ("Business % 10%. Standard deduction → mortgage/RE to lines 16/17 (col b). Line 23 col (b) = 6000+3000+1200+2400 "
               "= 12,600; line 24 = 12,600 × 10% = 1,260; line 26 = 500 (repairs direct) + 1,260 = 1,760; line 27 = "
               "min(20000, 1760) = 1,760. Depreciation 1,000 fully allowed. Line 36 = 0 + 1,760 + 1,000 = 2,760. Not limited.")},
    {"scenario_name": "8829-T2 — income limitation BINDS → depreciation carries over (D_8829_001)", "scenario_type": "edge_case", "sort_order": 2,
     "inputs": {"tax_year": 2025, "filing_status": "single", "h_itemizing": False,
                "h_area_business": 200, "h_area_total": 2000, "h_sch_c_line29": 2000,
                "h_excess_mortgage": 6000, "h_excess_re_taxes": 3000, "h_insurance_indirect": 1200,
                "h_repairs_direct": 500, "h_utilities_indirect": 2400, "h_depreciation": 1000},
     "expected_outputs": {"line_8": 2000, "line_15": 2000, "line_26": 1760, "line_27": 1760,
                          "line_28": 240, "line_32": 1000, "line_33": 240, "line_36": 2000,
                          "line_43": 0, "line_44": 760, "D_8829_001": True},
     "notes": ("Same expenses, but Sch C line 29 = 2,000 (low income). Operating fully allowed (1,760). Line 28 = 2,000 − "
               "1,760 = 240. Depreciation 1,000 → only 240 allowed (line 33), 760 carries over (line 44). Line 36 = 1,760 + "
               "240 = 2,000 = the gross-income cap. The §280A(c)(5) limitation: depreciation carries over first.")},
    {"scenario_name": "8829-T3 — itemizer RE-tax SALT split, room under the cap (non-iterating)", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"tax_year": 2025, "filing_status": "single", "h_itemizing": True, "h_salt_cap_ref": 40000,
                "h_area_business": 200, "h_area_total": 2000, "h_sch_c_line29": 30000,
                "h_re_taxes_home": 8000, "h_personal_salt_other": 15500},
     "expected_outputs": {"line_7": 0.10, "line_11": 800, "line_17": 0, "line_14": 800, "line_36": 800},
     "notes": ("Business % 10%, home RE tax 8,000. WS6 = 8,000 × 10% = 800. Other personal SALT 15,500. WS7a = 15,500. "
               "Cap 40,000 (MAGI < 500k). WS9 = 40,000 − 15,500 = 24,500. WS10 = min(800, 24,500) = 800 → line 11. WS11 = 0 "
               "→ line 17. Tier 1 line 14 = 800 (deductible regardless of the income limit). Line 36 = 800.")},
    {"scenario_name": "8829-T4 — itemizer RE-tax split, SALT cap consumed → moves from tier 1 to tier 2", "scenario_type": "edge_case", "sort_order": 4,
     "inputs": {"tax_year": 2025, "filing_status": "single", "h_itemizing": True, "h_salt_cap_ref": 40000,
                "h_area_business": 200, "h_area_total": 2000, "h_sch_c_line29": 30000,
                "h_re_taxes_home": 8000, "h_personal_salt_other": 45000},
     "expected_outputs": {"line_11": 0, "line_17": 800, "line_14": 0, "line_27": 800, "line_36": 800},
     "notes": ("Other personal SALT 45,000 ≥ the 40,000 cap → WS9 = max(0, 40,000 − 45,000) = 0. WS10 = 0 → line 11 = 0. "
               "WS11 = ws6 − 0 = 800 → line 17 col (a) (already × business %, pre-allocated). Tier 1 line 14 = 0; the 800 "
               "now rides the operating tier (line 23 col (a) = 800, line 27 = min(30,000, 800) = 800). Line 36 = 800 — "
               "same dollars as T3, but the SALT cap binding moved the home RE tax from tier 1 (unconditional) to tier 2 "
               "(income-limited). The placement only changes the total when business income is tight.")},
    {"scenario_name": "8829-T5 — daycare hours-of-use percentage (Part I 4-6)", "scenario_type": "normal", "sort_order": 5,
     "inputs": {"tax_year": 2025, "filing_status": "single", "h_itemizing": False, "h_is_daycare": True,
                "h_area_business": 400, "h_area_total": 2000, "h_daycare_hours": 3400, "h_daycare_hours_available": 8760,
                "h_sch_c_line29": 25000, "h_utilities_indirect": 4000, "h_insurance_indirect": 1500},
     "expected_outputs": {"line_3": 0.20, "line_6": 0.388127, "line_7": 0.077625, "line_36": 427},
     "notes": ("Area % = 400/2000 = 20%. Daycare hours 3,400 / 8,760 = 0.388127. Line 7 = 0.20 × 0.388127 = 0.0776255. "
               "Operating indirect = 5,500; line 24 = 5,500 × 0.0776255 = 426.94 → 427. Line 36 = 427. The daycare time "
               "haircut on top of the area %.")},
    {"scenario_name": "8829-T6 — Part III depreciation, subsequent year (2.564%)", "scenario_type": "normal", "sort_order": 6,
     "inputs": {"tax_year": 2025, "filing_status": "single", "h_itemizing": False,
                "h_area_business": 300, "h_area_total": 2000, "h_basis_or_fmv": 350000, "h_land_value": 50000,
                "h_first_use_year": 2022, "h_month_first_used": 6, "h_sch_c_line29": 40000},
     "expected_outputs": {"line_7": 0.15, "line_39": 300000, "line_40": 45000, "line_41": 2.564, "line_42": 1154, "line_36": 1154},
     "notes": ("Business % 15%. Building basis = 350,000 − 50,000 land = 300,000. Business basis = 300,000 × 15% = 45,000. "
               "First used 2022 (< 2025) → 2.564%. Depreciation = 45,000 × 2.564% = 1,153.8 → 1,154 → line 30 → line 36. "
               "(No operating expenses in this scenario.)")},
    {"scenario_name": "8829-T7 — Part III depreciation, first year (March mid-month 2.033%)", "scenario_type": "normal", "sort_order": 7,
     "inputs": {"tax_year": 2025, "filing_status": "single", "h_itemizing": False,
                "h_area_business": 300, "h_area_total": 2000, "h_basis_or_fmv": 350000, "h_land_value": 50000,
                "h_first_use_year": 2025, "h_month_first_used": 3, "h_sch_c_line29": 40000},
     "expected_outputs": {"line_40": 45000, "line_41": 2.033, "line_42": 915, "line_36": 915},
     "notes": ("First used March 2025 → mid-month % 2.033%. Depreciation = 45,000 × 2.033% = 914.85 → 915. First-year home "
               "→ also Form 4562 line 19j (D_8829_006).")},
    {"scenario_name": "8829-T8 — carryover-in from prior year consumed (lines 25/31)", "scenario_type": "normal", "sort_order": 8,
     "inputs": {"tax_year": 2025, "filing_status": "single", "h_itemizing": False,
                "h_area_business": 200, "h_area_total": 2000, "h_sch_c_line29": 30000,
                "h_utilities_indirect": 3000, "h_carryover_operating_prior": 1500,
                "h_depreciation": 800, "h_carryover_casdep_prior": 400},
     "expected_outputs": {"line_24": 300, "line_26": 1800, "line_27": 1800, "line_32": 1200, "line_33": 1200, "line_36": 3000, "line_43": 0, "line_44": 0},
     "notes": ("Utilities indirect 3,000 → line 24 = 3,000 × 10% = 300. Line 26 = 0 + 300 + 1,500 carryover = 1,800; line 27 "
               "= min(30,000, 1,800) = 1,800. Line 32 = 0 + 800 depr + 400 carryover = 1,200; line 33 = min(28,200, 1,200) "
               "= 1,200. Line 36 = 1,800 + 1,200 = 3,000. Prior-year carryovers fully consumed.")},
    {"scenario_name": "8829-T9 — casualty loss present → RED-defer (D_8829_002)", "scenario_type": "edge_case", "sort_order": 9,
     "inputs": {"tax_year": 2025, "filing_status": "single", "h_itemizing": False,
                "h_area_business": 200, "h_area_total": 2000, "h_sch_c_line29": 30000,
                "h_casualty_indirect": 5000, "h_utilities_indirect": 2000},
     "expected_outputs": {"D_8829_002": True, "line_36": None},
     "notes": ("Casualty present (line 9 col b = 5,000) → D_8829_002 RED-defer; line 36 BLANKED (the line-35 → Form 4684 "
               "routing is not built). The preparer completes Form 4684 by hand. No silent gap.")},
    {"scenario_name": "8829-T10 — high-MAGI SALT iteration (>$500k) → D_8829_005", "scenario_type": "edge_case", "sort_order": 10,
     "inputs": {"tax_year": 2025, "filing_status": "single", "h_itemizing": True,
                "h_area_business": 300, "h_area_total": 2000, "h_sch_c_line29": 200000,
                "h_re_taxes_home": 12000, "h_personal_salt_other": 30000, "magi_over_threshold": True},
     "expected_outputs": {"D_8829_005": True, "SALT_iteration": True},
     "notes": ("MAGI > 500,000 → the $40k SALT cap phases down (30% of the excess, floor $10k) and the cap depends on AGI "
               "which depends on the home-office deduction → iterate (i8829 Iteration Instructions, converge < $1). "
               "Routing scenario: the compute leg runs the fixed-point loop; D_8829_005 surfaces it. Common itemizer "
               "(<$500k) needs no iteration.")},
    {"scenario_name": "8829-T11 — full stack: tier 1 + operating + depreciation, not limited", "scenario_type": "normal", "sort_order": 11,
     "inputs": {"tax_year": 2025, "filing_status": "single", "h_itemizing": True, "h_salt_cap_ref": 40000,
                "h_area_business": 250, "h_area_total": 2500, "h_sch_c_line29": 50000,
                "h_mortgage_deductible": 12000, "h_re_taxes_home": 6000, "h_personal_salt_other": 10000,
                "h_insurance_indirect": 1800, "h_utilities_indirect": 3600, "h_repairs_direct": 700,
                "h_basis_or_fmv": 400000, "h_land_value": 80000, "h_first_use_year": 2020, "h_month_first_used": 1},
     "expected_outputs": {"line_7": 0.10, "line_11": 600, "line_14": 1800, "line_15": 48200,
                          "line_40": 32000, "line_42": 820, "line_27": 1240, "line_33": 820, "line_36": 3860},
     "notes": ("Business % 10%. RE tax: WS6 = 6,000 × 10% = 600, other SALT 10,000, WS9 = 40,000 − 10,000 = 30,000, line 11 "
               "col (a) = min(600, 30,000) = 600, line 17 = 0. Mortgage deductible 12,000 → line 12 col (b) = 12,000; line "
               "12 col (a) = 600. Line 13 = 12,000 × 10% = 1,200; line 14 = 600 + 1,200 = 1,800. Line 15 = 50,000 − 1,800 = "
               "48,200. Operating: ins 1,800 + util 3,600 = 5,400 col (b) → line 24 = 540; repairs 700 col (a); line 26 = "
               "700 + 540 = 1,240; line 27 = 1,240. Depreciation: building 400,000 − 80,000 land = 320,000 × 10% = 32,000 × "
               "2.564% = 820.48 → 820; line 33 = 820. Line 36 = 1,800 + 1,240 + 820 = 3,860.")},
]


# ═══════════════════════════════════════════════════════════════════════════
# RULE → AUTHORITY LINKS
# ═══════════════════════════════════════════════════════════════════════════

F8829_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-8829-SCOPE", "IRS_2025_8829_FORM", "primary", "Who files Form 8829 / actual vs simplified"),
    ("R-8829-SCOPE", "IRC_280A", "primary", "§280A(c)(1) business-use exception"),
    ("R-8829-L3-AREA", "IRS_2025_8829_FORM", "primary", "Part I lines 1-3 area %"),
    ("R-8829-L7-BUSPCT", "IRS_2025_8829_INSTR", "primary", "Part I lines 4-7 daycare hours-of-use"),
    ("R-8829-L8-LIMIT", "IRC_280A", "primary", "§280A(c)(5) gross-income limitation"),
    ("R-8829-L8-LIMIT", "IRS_2025_8829_INSTR", "secondary", "Line 8 computation"),
    ("R-8829-T1-DEDUCT", "IRS_2025_8829_FORM", "primary", "Lines 9-15 deductible-anyway tier"),
    ("R-8829-T1-DEDUCT", "IRC_280A", "secondary", "§280A(c)(5) ordering — otherwise-allowable first"),
    ("R-8829-L11WS", "IRS_2025_8829_INSTR", "primary", "Line 11 Worksheet RE-tax SALT split + iteration"),
    ("R-8829-MTG-SPLIT", "IRS_2025_8829_INSTR", "primary", "Lines 10/16 mortgage deductible-vs-excess"),
    ("R-8829-T2-OPER", "IRS_2025_8829_FORM", "primary", "Lines 16-27 operating-expense tier"),
    ("R-8829-T2-OPER", "IRC_280A", "secondary", "§280A(c)(5) operating limited to remaining income"),
    ("R-8829-T3-CASDEP", "IRS_2025_8829_FORM", "primary", "Lines 28-33 casualty + depreciation tier"),
    ("R-8829-T3-CASDEP", "IRC_280A", "secondary", "§280A(c)(5) depreciation last / carries over first"),
    ("R-8829-L36", "IRS_2025_8829_FORM", "primary", "Lines 34-36 → Schedule C line 30"),
    ("R-8829-P3-DEPR", "IRC_168_PUB946", "primary", "§168 39-yr nonresidential mid-month SL"),
    ("R-8829-P3-DEPR", "IRS_2025_8829_INSTR", "secondary", "Line 41 mid-month percentage table"),
    ("R-8829-P4-CARRY", "IRC_280A", "primary", "§280A(c)(5) carryover to next year"),
    ("R-8829-P4-CARRY", "IRS_2025_8829_FORM", "secondary", "Part IV lines 43-44"),
    ("R-8829-DEFER", "IRS_2025_8829_INSTR", "primary", "Line 35 → Form 4684 / line 36 multi-business"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS (staged into tts-tax-app at the assertions leg)
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-8829-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Form 8829 line 36 → Schedule C line 30",
     "description": ("Validates R-8829-L36. The allowable home-office expense (line 36) → Schedule C line 30 → Sch C "
                     "line 31 net profit. Bug it catches: the actual-expense deduction not reaching Schedule C, or the "
                     "simplified $5/sq ft amount surviving when actual-expense is elected."),
     "definition": {"kind": "flow_assertion", "form": "8829", "source_line": "36", "must_write_to": ["SCHEDULE_C.30"]},
     "sort_order": 1},
    {"assertion_id": "FA-1040-8829-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "§280A(c)(5) gross-income limit: line 36 ≤ line 8",
     "description": ("Validates R-8829-L8-LIMIT / R-8829-L36 / §280A(c)(5). The total home-office deduction (line 36, "
                     "excluding the deductible-anyway tier-1 items already in line 14) never exceeds the business gross "
                     "income (line 8). Bug it catches: deducting operating/depreciation above the income limit."),
     "definition": {"kind": "formula_check", "form": "8829",
                    "formula": "line_27 + line_33 <= line_15"},
     "sort_order": 2},
    {"assertion_id": "FA-1040-8829-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Tier ordering: operating (27) = smaller of remaining cap (15) or total (26)",
     "description": ("Validates R-8829-T2-OPER. Allowable operating expenses = min(line 15, line 26); allowable "
                     "casualty+depreciation = min(line 28, line 32). Bug it catches: deducting the full operating/depr "
                     "regardless of the remaining income, or the wrong tier order."),
     "definition": {"kind": "formula_check", "form": "8829",
                    "formula": "line_27 == min(line_15, line_26) and line_33 == min(line_28, line_32)"},
     "sort_order": 3},
    {"assertion_id": "FA-1040-8829-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Carryover: line 43 = max(0, 26 − 27); line 44 = max(0, 32 − 33)",
     "description": ("Validates R-8829-P4-CARRY / §280A(c)(5). The disallowed operating expenses (line 43) and casualty+ "
                     "depreciation (line 44) carry over to next year, floored at 0. Bug it catches: a negative carryover, "
                     "or losing the disallowed depreciation entirely."),
     "definition": {"kind": "formula_check", "form": "8829",
                    "formula": "line_43 == max(0, line_26 - line_27) and line_44 == max(0, line_32 - line_33)"},
     "sort_order": 4},
    {"assertion_id": "FA-1040-8829-05", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Part III depreciation: line 42 = (basis − land) × business % × rate",
     "description": ("Validates R-8829-P3-DEPR. Home depreciation = line 40 (business basis = (line 37 − line 38) × line 7) "
                     "× line 41 (39-yr nonresidential mid-month %). Bug it catches: depreciating land, the wrong recovery "
                     "period (27.5-yr residential), or omitting the business % on the basis."),
     "definition": {"kind": "formula_check", "form": "8829",
                    "formula": "line_40 == (line_37 - line_38) * line_7 and line_42 == round(line_40 * line_41 / 100)"},
     "sort_order": 5},
    {"assertion_id": "FA-1040-8829-06", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Business % (line 7) = area % (daycare: × hours-of-use fraction)",
     "description": ("Validates R-8829-L3-AREA / R-8829-L7-BUSPCT. Line 7 = line 1 ÷ line 2, and for a non-exclusive "
                     "daycare facility × (line 4 ÷ line 5). Bug it catches: omitting the daycare time haircut, or a "
                     "business % > 100%."),
     "definition": {"kind": "gating_check", "form": "8829",
                    "blockers": ["business_pct_over_100", "daycare_hours_fraction_omitted"],
                    "expect": {"line_7_equals_area_pct_or_daycare_adjusted": True}},
     "sort_order": 6},
    {"assertion_id": "FA-1040-8829-07", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "RE-tax SALT split reuses the Schedule A cap (single source)",
     "description": ("Validates R-8829-L11WS / W4. The Line 11 Worksheet overall SALT limit is the Schedule A cap "
                     "(compute_schedule_a.salt_line5e — the OBBBA $40k cap with the $500k-MAGI 30% phasedown), NOT a "
                     "re-typed constant. Bug it catches: 8829 drifting from Schedule A's SALT cap, or a flat $10k cap."),
     "definition": {"kind": "gating_check", "form": "8829",
                    "blockers": ["salt_cap_retyped_in_8829", "flat_10k_cap"],
                    "expect": {"reuses_schedule_a_salt_line5e": True}},
     "sort_order": 7},
    {"assertion_id": "FA-1040-8829-08", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "Depreciation table (39-yr mid-month) + daycare hours + SALT cap constants",
     "description": ("Pins the 39-yr nonresidential mid-month percentages (first-year by month + 2.564% subsequent), the "
                     "daycare 8,760-hour base, and the SALT cap reference (matching Schedule A). Bug it catches: a 27.5-yr "
                     "rate, a wrong month percentage, or a stale SALT cap."),
     "definition": {"kind": "constants_check", "form": "8829",
                    "constants": {"depr_first_year_pct": DEPRECIATION_FIRST_YEAR_PCT,
                                  "depr_subsequent_pct": DEPRECIATION_SUBSEQUENT_PCT,
                                  "daycare_hours_2025": DAYCARE_HOURS_PER_YEAR[2025],
                                  "daycare_hours_2026": DAYCARE_HOURS_PER_YEAR[2026],
                                  "salt_cap_2025": SALT_CAP_REF[2025], "salt_cap_2026": SALT_CAP_REF[2026],
                                  "applies_to_years": [2025, 2026]}},
     "sort_order": 8},
    {"assertion_id": "FA-1040-8829-09", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "RED-defer no-silent-gap: casualty/multi-business blank line 36 + fire a RED",
     "description": ("Validates R-8829-DEFER. A casualty loss (line 9/29 → Form 4684 line 35) blanks line 36 + fires "
                     "D_8829_002; a multi-business home fires D_8829_003. Bug it catches: a silently-wrong home-office "
                     "deduction when the line-35 casualty routing or the multi-business allocation is unsupported."),
     "definition": {"kind": "gating_check", "form": "8829",
                    "blockers": ["casualty_on_8829", "multi_business_home"],
                    "expect": {"red_fires": True, "line_36_blank_on_casualty": True}},
     "sort_order": 9},
]


FORMS: list[dict] = [
    {
        "identity": {
            "form_number": "8829",
            "form_title": "Form 8829 — Expenses for Business Use of Your Home (TY2025)",
            "notes": (
                "NEW spec (no prior RS draft). The actual-expense home-office engine: Part I business % (area, daycare "
                "hours-of-use) → the §280A(c)(5) gross-income limitation in 3 ordered tiers (deductible-anyway 9-14 → "
                "operating 16-27 → casualty+depreciation 29-33) → line 36 → Schedule C line 30; Part III 39-yr "
                "nonresidential mid-month depreciation; Part IV operating + casualty/depr carryover. v1 COMPUTES the "
                "RE-tax SALT split (lines 11/17) reusing the Schedule A cap (salt_line5e) incl. the >$500k-MAGI "
                "iteration; the mortgage Pub-936 split (10/16) is a preparer fact for itemizers (computed for the "
                "standard-deduction path). RED-defers line-35 → Form 4684 + the multi-business line-36 allocation. "
                "Verified against the 2025 f8829.pdf (read directly) + i8829 + IRC §280A + §168/Pub 946. Replaces the "
                "existing simplified $5/sq ft amount on Schedule C line 30 when actual-expense is elected; D_SC_007 "
                "narrows to the genuine residual at the diagnostics leg."
            ),
        },
        "facts": F8829_FACTS,
        "rules": F8829_RULES,
        "lines": F8829_LINES,
        "diagnostics": F8829_DIAGNOSTICS,
        "scenarios": F8829_SCENARIOS,
        "rule_links": F8829_RULE_LINKS,
    },
]


class Command(BaseCommand):
    help = (
        "Load the Form 8829 spec (Expenses for Business Use of Your Home: business "
        "%, the §280A(c)(5) gross-income limitation, 39-yr home depreciation, "
        "carryover → Schedule C line 30). Refuses to seed until Ken sets "
        "READY_TO_SEED=True after the in-session review walk."
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()

        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad FORM 8829 spec (Business Use of Home)\n"))

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
                "\nREFUSING TO SEED FORM 8829: not cleared to seed.\n\n"
                "Content is authored, but seeding is gated until Ken reviews the packet\n"
                "(W1 §280A tier ordering; W2 the 39-yr mid-month depreciation; W3 the\n"
                "mortgage-split-as-input posture; W4 the RE-tax SALT split + MAGI\n"
                "iteration; W5 casualty/4684; W6 constants) and flips the sentinel.\n\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True to proceed)\n\n"
                f"Currently empty / placeholder:\n  {still_empty}\n\n"
                "To proceed: review the module-level data lists, then set READY_TO_SEED\n"
                "= True. Idempotent via update_or_create — safe to re-run after edits."
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Topics / sources (mirror load_1040_form_6251.py exactly)
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
        self.stdout.write("FORM 8829 loaded.")
        self.stdout.write(
            f"  facts {len(F8829_FACTS)} / rules {len(F8829_RULES)} / lines {len(F8829_LINES)} / "
            f"diagnostics {len(F8829_DIAGNOSTICS)} / tests {len(F8829_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}"
        )
        self.stdout.write("=" * 60)
