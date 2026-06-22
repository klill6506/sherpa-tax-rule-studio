"""Load the Schedule J spec — Income Averaging for Farmers/Fishermen (1040).

Creates ONE new TaxForm (no amendments — the load_1040_schedule_f.py precedent
without the sibling-form amendment):

  - SCHEDULE_J (Income Averaging for Individuals With Income From Farming or
    Fishing) — NEW. An ELECTION (IRC §1301) to figure the election-year (2025)
    income tax by averaging "elected farm income" over the 3 prior BASE YEARS.
    For TY2025 the base years are 2022/2023/2024; for TY2026 they are
    2023/2024/2025. The 23-line chain recomputes the election-year tax (line 4,
    current-year method) plus a recomputed base-year tax for each base year with
    1/3 of the elected farm income layered in (lines 8/12/16, BASE-YEAR rate
    schedules), nets out the base years' original tax (lines 19-22), and lands the
    result on Form 1040 line 16 (line 23, a route gate — replaces the regular tax
    only when elected). Schedule J is the Schedule F fast-follow (Ken, 2026-06-21).

Session 2026-06-21: spec-first probe found NO RS Schedule J spec (SCHEDULE_J /
1040_SCHJ / SCHJ / J / f1040sj all 404; RS up, real 404s). Authored by
transcription from primary sources verified the same day (pymupdf dumps):

  - 2025 Schedule J (f1040sj.pdf, Attachment Seq 20) — the 23-line chain.
  - 2025 Instructions for Schedule J (i1040sj.pdf) — base-year RATE SCHEDULES
    (2022/2023/2024), the base-year QDCGT worksheets, the zero-or-less Taxable
    Income worksheets, the Foreign Earned Income worksheets, the elected-farm-
    income definition, the §1-only base-year-tax caveat.
  - 2022/2023/2024/2025 Schedule D instructions (i1040sd) — the Schedule D Tax
    Worksheet (IDENTICAL 47-line structure across all four years; only the three
    breakpoint sets differ -> one year-keyed engine).
  - IRC §1301, Reg. 1.1301-1.

Consolidated brief (constants verbatim, the 4 open requires_human_review Qs, the
data-model + 6-build-leg plan): tts-tax-app server/specs/_schedule_j_source_brief.md.

TOPIC SCOPE (Ken-locked 2026-06-21, AskUserQuestion at kickoff):
  IN: the 23-line chain; elected farm income INCLUDING net capital gain (2a/2b/2c);
      lines 4/8/12/16 route through RATE SCHEDULE -> base-year QDCGT -> base-year
      Schedule D Tax Worksheet as the income picture requires, YEAR-KEYED for
      2022/23/24 (base) + 2025 (current). Base-year amounts (taxable income, tax,
      and the preferential-income detail the worksheets consume) are PREPARER
      DIRECT ENTRY (optional YELLOW pull from PriorYearReturn). Both TY2025 (base
      22/23/24) + TY2026 (base 23/24/25) buildable now.
  OUT / RED-defer (no silent gap, never silently computed; each -> a D_SJ_*):
      prior-Schedule-J CHAINING (the "if you used Schedule J for 2024/2023/2022 ->
      enter prior Sch J line ..." branches); the zero-or-less TAXABLE INCOME
      WORKSHEETS (NOL/capital-loss refiguring of a negative base-year TI — the
      preparer enters the worksheet's result directly, a diagnostic nudges); Form
      2555 / Foreign Earned Income Tax Worksheet (any year).

KEY OVERRIDE (verified): base-year tax (lines 8/12/16) uses the BASE-YEAR RATE
SCHEDULES for the ordinary sub-computation — NEVER the base-year Tax Table (Sch J
instr). Line 4 (current year) uses the normal current-year method (Tax Table
<$100k / TCW). Within the base-year SDTW/QDCGT the two "figure the tax" sub-lines
use the rate schedule. STALE-CROSS-REF FLAG: the Sch J instr cite SDTW "lines
34/36" (2022) & "42/44" (2023), but the actual 2022/23/24/25 worksheets all put
the two ordinary-tax computations at lines 44/46 — implement against 44/46.

YEAR-KEYED CONSTANTS (verified verbatim; brief §5-7; target-year policy: TY2026
product target, TY2025 verification bed; verify each year independently):
  - BASE_YEAR_RATE_SCHEDULES (2022/23/24, per filing status) — for lines 8/12/16,
    the QDCGT lines 24/26, and the SDTW lines 44/46. (2025/2026 already in the
    spine's TAX_BRACKETS; the compute leg merges 2022/23/24 in.)
  - PREF_RATE_BREAKPOINTS (0%-rate ceiling + 20%-rate floor, per status, 2022-2025)
    — the QDCGT/SDTW preferential breakpoints.
  - SDTW_MID_THRESHOLD (SDTW line-19 mid threshold, per status, 2022-2025).
  - STATUTORY / NON-INDEXED: the 1/3 averaging divisor; the 0/15/20% LTCG rates;
    25% unrecap §1250; 28%-rate gain.

requires_human_review WALK ITEMS (flagged for Ken's review walk; brief §10):
  A. Line-4 capital-gain netting: when 2b>0, the base-year SDTWs explicitly ADD
     1/3 of 2b/2c; the line-4 (current-year) instruction is silent on whether the
     current-year SDTW reduces the Sch D figures by 2b/2c. Recommend yes-reduce
     (floored at 0). Confirm vs §1301 / Reg 1.1301-1.  [LOAD-BEARING]
  B. Line-6 rounding: "Divide line 2a by 3.0." Recommend round-half-up to whole
     dollar (the QDCGT WS18/21 precedent); L6+L6+L6 need not == L2a.
  C. Stale SDTW cross-ref: confirm implementing against worksheet lines 44/46.
  D. Elect-when-higher: WARNING-only diagnostic if L23 >= regular tax (recommend),
     not a hard block (it is the preparer's election).

Safety guard
------------
`READY_TO_SEED = False`. Content is authored; Ken reviews the packet (the 23-line
chain, the base-year rate schedules + QDCGT + SDTW constants, the RED-defer
enumeration, the 4 walk items), flips the sentinel, then we seed. Until then the
command refuses to write to the DB. Idempotent via update_or_create.

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
# SAFETY GUARD — flip ONLY after Ken's in-session review walk (the 23-line
# chain, the verified base-year rate schedules / QDCGT / SDTW constants, the
# RED-defer enumeration, the 4 requires_human_review walk items — especially
# Q-A line-4 capital-gain netting). Until then the command refuses to write to
# the DB (zero writes while False).
#
# FLIPPED 2026-06-21 — Ken APPROVED the review walk in-session ("Approve & seed
# now"). The 4 requires_human_review walk items were ruled, ALL matching the
# authored spec (no edits): Q-A line-4 SDTW REDUCES the current-year Sch D net
# capital gain by 2b (and unrecap §1250 by 2c), floored at 0; Q-B line 6 =
# round_half_up(2a/3) to whole dollar; Q-C SDTW ordinary-tax lines are 44/46
# (the instr's 34/36 & 42/44 cross-refs are stale); Q-D D_SJ_ELECT_HIGH is a
# WARNING (the election is the preparer's choice). Math gate ALL CHECKS PASS.
# ═══════════════════════════════════════════════════════════════════════════
READY_TO_SEED = True


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1040"]


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS (brief §5-7 — every value transcribed verbatim from the
# 2025 i1040sj.pdf / i1040sd PDFs; never training memory). The math gate
# (check_schedule_j_integrity.py) imports these and recomputes independently.
# Format mirrors the spine's TAX_BRACKETS: list of (bracket_ceiling, rate),
# cumulative; the top bracket ceiling is _INF. Algebraically == the IRS
# "base tax + marginal% of excess over floor" rate-schedule pages.
# ═══════════════════════════════════════════════════════════════════════════

_INF = 10 ** 12  # "and over" sentinel (documentation/gate use only; RS stores no math)

# Base-year RATE SCHEDULES — i1040sj.pdf pages 4 (2022), 8 (2023), 12 (2024).
# Used for Sch J lines 8/12/16 (ordinary path), QDCGT lines 24/26, SDTW lines 44/46.
# (2025/2026 are already in the spine TAX_BRACKETS; the compute leg merges these in.)
BASE_YEAR_RATE_SCHEDULES: dict[int, dict[str, list[tuple[int, str]]]] = {
    2022: {
        "single": [(10275, "0.10"), (41775, "0.12"), (89075, "0.22"), (170050, "0.24"), (215950, "0.32"), (539900, "0.35"), (_INF, "0.37")],
        "mfj":    [(20550, "0.10"), (83550, "0.12"), (178150, "0.22"), (340100, "0.24"), (431900, "0.32"), (647850, "0.35"), (_INF, "0.37")],
        "mfs":    [(10275, "0.10"), (41775, "0.12"), (89075, "0.22"), (170050, "0.24"), (215950, "0.32"), (323925, "0.35"), (_INF, "0.37")],
        "hoh":    [(14650, "0.10"), (55900, "0.12"), (89050, "0.22"), (170050, "0.24"), (215950, "0.32"), (539900, "0.35"), (_INF, "0.37")],
        "qss":    None,  # QSS uses MFJ
    },
    2023: {
        "single": [(11000, "0.10"), (44725, "0.12"), (95375, "0.22"), (182100, "0.24"), (231250, "0.32"), (578125, "0.35"), (_INF, "0.37")],
        "mfj":    [(22000, "0.10"), (89450, "0.12"), (190750, "0.22"), (364200, "0.24"), (462500, "0.32"), (693750, "0.35"), (_INF, "0.37")],
        "mfs":    [(11000, "0.10"), (44725, "0.12"), (95375, "0.22"), (182100, "0.24"), (231250, "0.32"), (346875, "0.35"), (_INF, "0.37")],
        "hoh":    [(15700, "0.10"), (59850, "0.12"), (95350, "0.22"), (182100, "0.24"), (231250, "0.32"), (578100, "0.35"), (_INF, "0.37")],
        "qss":    None,
    },
    2024: {
        "single": [(11600, "0.10"), (47150, "0.12"), (100525, "0.22"), (191950, "0.24"), (243725, "0.32"), (609350, "0.35"), (_INF, "0.37")],
        "mfj":    [(23200, "0.10"), (94300, "0.12"), (201050, "0.22"), (383900, "0.24"), (487450, "0.32"), (731200, "0.35"), (_INF, "0.37")],
        "mfs":    [(11600, "0.10"), (47150, "0.12"), (100525, "0.22"), (191950, "0.24"), (243725, "0.32"), (365600, "0.35"), (_INF, "0.37")],
        "hoh":    [(16550, "0.10"), (63100, "0.12"), (100500, "0.22"), (191950, "0.24"), (243700, "0.32"), (609350, "0.35"), (_INF, "0.37")],
        "qss":    None,
    },
}

# Preferential-rate breakpoints (QDCGT line 8 / line 15; SDTW line 15 / line 26).
# i1040sj QDCGT worksheets (pages 5/9/13) + the SDTW (i1040sd) line 15/26. Per status.
# "zero_ceiling" = top of the 0% LTCG rate; "twenty_floor" = start of the 20% LTCG rate.
PREF_RATE_BREAKPOINTS: dict[int, dict[str, dict[str, int]]] = {
    2022: {"single": {"zero_ceiling": 41675, "twenty_floor": 459750},
           "mfj":    {"zero_ceiling": 83350, "twenty_floor": 517200},
           "mfs":    {"zero_ceiling": 41675, "twenty_floor": 258600},
           "hoh":    {"zero_ceiling": 55800, "twenty_floor": 488500}},
    2023: {"single": {"zero_ceiling": 44625, "twenty_floor": 492300},
           "mfj":    {"zero_ceiling": 89250, "twenty_floor": 553850},
           "mfs":    {"zero_ceiling": 44625, "twenty_floor": 276900},
           "hoh":    {"zero_ceiling": 59750, "twenty_floor": 523050}},
    2024: {"single": {"zero_ceiling": 47025, "twenty_floor": 518900},
           "mfj":    {"zero_ceiling": 94050, "twenty_floor": 583750},
           "mfs":    {"zero_ceiling": 47025, "twenty_floor": 291850},
           "hoh":    {"zero_ceiling": 63000, "twenty_floor": 551350}},
    2025: {"single": {"zero_ceiling": 48350, "twenty_floor": 533400},
           "mfj":    {"zero_ceiling": 96700, "twenty_floor": 600050},
           "mfs":    {"zero_ceiling": 48350, "twenty_floor": 300000},
           "hoh":    {"zero_ceiling": 64750, "twenty_floor": 566700}},
}

# Schedule D Tax Worksheet line-19 MID threshold (start of the 32% ordinary
# bracket; SDTW-only). i1040sd SDTW line 19, per status, 2022-2025.
SDTW_MID_THRESHOLD: dict[int, dict[str, int]] = {
    2022: {"single": 170050, "mfj": 340100, "mfs": 170050, "hoh": 170050},
    2023: {"single": 182100, "mfj": 364200, "mfs": 182100, "hoh": 182100},
    2024: {"single": 191950, "mfj": 383900, "mfs": 191950, "hoh": 191950},
    2025: {"single": 197300, "mfj": 394600, "mfs": 197300, "hoh": 197300},
}

LINE6_DIVISOR = 3              # statutory (§1301): elected farm income / 3
SDTW_RATE_1250 = "0.25"       # unrecaptured §1250 gain (statutory)
SDTW_RATE_28 = "0.28"         # 28%-rate gain (collectibles/§1202) (statutory)
LTCG_RATE_15 = "0.15"
LTCG_RATE_20 = "0.20"

# Base years by election year (TY2025 -> 2022/23/24; TY2026 -> 2023/24/25).
BASE_YEARS_BY_ELECTION: dict[int, dict[int, int]] = {
    2025: {1: 2022, 2: 2023, 3: 2024},
    2026: {1: 2023, 2: 2024, 3: 2025},
}


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY TOPICS
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("schedule_j_income_averaging", "Schedule J — income averaging for farmers/fishermen: elect to average elected farm income over the 3 prior base years -> 1040 line 16"),
    ("base_year_tax_recompute", "Base-year tax recomputation: base-year rate schedules / QDCGT / Schedule D Tax Worksheet, year + filing-status keyed (Sch J lines 8/12/16)"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_1040_FORM",   # 1040 line 15 (taxable income, Sch J line 1) + line 16 (tax)
    "IRS_2025_1040_INSTR",  # the QDCGT worksheet + the Tax Computation Worksheet (line 4 current-year method)
]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY SOURCES (with embedded excerpts) — CREATE
# Transcribed 2026-06-21 from the fetched PDFs (tts-tax-app server/.scratch/schedj/).
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_SCHEDJ_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Schedule J (Form 1040) — Income Averaging for Individuals With Income From Farming or Fishing",
        "citation": "Schedule J (Form 1040) 2025; f1040sj.pdf; Attachment Sequence No. 20; Cat. No. 25513Y",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f1040sj.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": "23-line chain transcribed verbatim 2026-06-21 (sha256 5c888d02…). For TY2025 base years = 2022/2023/2024.",
        "topics": ["schedule_j_income_averaging"],
        "excerpts": [
            {
                "excerpt_label": "Schedule J lines 1-17 (page 1) — verbatim",
                "location_reference": "Schedule J (2025), Part I lines 1-17",
                "excerpt_text": (
                    "1 Enter the taxable income from your 2025 Form 1040, line 15. 2a Enter your elected farm "
                    "income (do not enter more than line 1). 2b Excess, if any, of net long-term capital gain over "
                    "net short-term capital loss. 2c Unrecaptured section 1250 gain. 3 Subtract line 2a from line "
                    "1. 4 Figure the tax on the amount on line 3 using the 2025 tax rates. 5 [2022 base] If you "
                    "used Schedule J for 2024, enter 2024 Sch J line 11; for 2023 not 2024, 2023 Sch J line 15; "
                    "for 2022 not 2023/2024, 2022 Sch J line 3; otherwise the taxable income from your 2022 Form "
                    "1040, line 15 (if zero or less, see instructions). 6 Divide the amount on line 2a by 3.0. 7 "
                    "Combine lines 5 and 6. If zero or less, enter -0-. 8 Figure the tax on line 7 using the 2022 "
                    "tax rates. 9 [2023 base] ... otherwise the taxable income from your 2023 Form 1040, line 15. "
                    "10 Enter the amount from line 6. 11 Combine lines 9 and 10. If less than zero, enter as a "
                    "negative amount. 12 Figure the tax on line 11 using the 2023 tax rates. 13 [2024 base] ... "
                    "otherwise the taxable income from your 2024 Form 1040, line 15. 14 Enter the amount from line "
                    "6. 15 Combine lines 13 and 14. If less than zero, enter as a negative amount. 16 Figure the "
                    "tax on line 15 using the 2024 tax rates. 17 Add lines 4, 8, 12, and 16."
                ),
                "summary_text": (
                    "L3 = L1 - L2a. L4 = tax(L3) current-year method. L6 = L2a/3. L7 = max(0, L5+L6); "
                    "L11 = L9+L6 (signed); L15 = L13+L6 (signed). L8/12/16 = base-year tax (rate schedule/QDCGT/"
                    "SDTW) on L7/L11/L15 (0 when the base <= 0). L17 = L4+L8+L12+L16. Base years (TY2025) = "
                    "2022/2023/2024. Prior-Sch-J chaining = RED-defer; the 'if zero or less' worksheet = RED-defer."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule J lines 18-23 (page 2) — verbatim",
                "location_reference": "Schedule J (2025), lines 18-23",
                "excerpt_text": (
                    "18 Amount from line 17. 19 [2022 tax] ... otherwise the tax from your 2022 Form 1040, line "
                    "16. 20 [2023 tax] ... otherwise the tax from your 2023 Form 1040, line 16. 21 [2024 tax] ... "
                    "otherwise the tax from your 2024 Form 1040, line 16 (*only include tax imposed by section 1 "
                    "of the Internal Revenue Code). 22 Add lines 19 through 21. 23 Tax. Subtract line 22 from line "
                    "18. Also include this amount on Form 1040, line 16. Caution: Your tax may be less if you "
                    "figure it using the Tax Table, QDCGT Worksheet, or Schedule D Tax Worksheet. Attach Schedule "
                    "J only if you are using it to figure your tax."
                ),
                "summary_text": (
                    "L19/20/21 = base-year ORIGINAL tax (direct entry; §1 tax ONLY — exclude 8814/4972/recapture/"
                    "HCTC repayment). L22 = L19+L20+L21. L23 = L18 - L22 -> Form 1040 line 16 (route gate, only when "
                    "elected). Caution -> D_SJ_ELECT_HIGH warning when L23 >= regular tax."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_SCHEDJ_INSTR",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Schedule J (Form 1040)",
        "citation": "i1040sj (2025); Cat. No. 25514J",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i1040sj.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": False,
        "trust_score": 9.00,
        "requires_human_review": True,
        "notes": (
            "Contains the base-year RATE SCHEDULES (2022/23/24), the base-year QDCGT worksheets, the "
            "zero-or-less Taxable Income worksheets (RED-defer), the FEI worksheets (RED-defer), the elected-"
            "farm-income definition, the §1-only base-year-tax caveat. WALK ITEM A (line-4 cap-gain netting), "
            "WALK ITEM C (stale SDTW cross-ref 34/36 & 42/44 vs the real 44/46). requires_human_review=True."
        ),
        "topics": ["schedule_j_income_averaging", "base_year_tax_recompute"],
        "excerpts": [
            {
                "excerpt_label": "Elected farm income (line 2a) + 2b/2c — verbatim",
                "location_reference": "i1040sj (2025), 'Line 2a Elected Farm Income' / 'Lines 2b and 2c'",
                "excerpt_text": (
                    "Elected farm income is the amount of your taxable income from farming or fishing that you "
                    "elect to include on line 2a. It includes income, gains, losses, and deductions attributable "
                    "to your farming or fishing business, PLUS gain or loss from the sale or other disposition of "
                    "property regularly used in the farming or fishing business for a substantial period. Elected "
                    "farm income does NOT include income, gain, or loss from the sale or disposition of LAND, or "
                    "from the sale of development rights, grazing rights, and other similar rights. Your elected "
                    "farm income can't exceed your taxable income. Complete lines 2b and 2c if line 2a includes "
                    "net capital gain. Line 2b = the portion of line 2a treated as net capital gain (excess of net "
                    "LTCG over net STCL, not more than the smaller of total net capital gain or the net capital "
                    "gain attributable to farming/fishing). Line 2c = the smaller of line 2b or the unrecaptured "
                    "section 1250 gain attributable to farming/fishing."
                ),
                "summary_text": (
                    "L2a = preparer-elected farm income (<= L1; LAND excluded). L2b/2c = the capital-gain / "
                    "unrecap-§1250 portion of L2a -> drives the Schedule D Tax Worksheet path on lines 4/8/12/16; "
                    "the base-year SDTW allocates 1/3 of 2b (and 2c) to each base year."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Lines 8/12/16 base-year tax method + the base-year RATE SCHEDULES override — verbatim",
                "location_reference": "i1040sj (2025), Line 8 / Line 12 / Line 16",
                "excerpt_text": (
                    "If line 7 is zero, enter -0- on line 8. Otherwise, figure the tax on line 7 using: the 2022 "
                    "Tax Rate Schedules; the 2022 Qualified Dividends and Capital Gain Tax Worksheet; the 2022 "
                    "Schedule D Tax Worksheet (but use the 2022 Tax Rate Schedules when figuring the tax on the "
                    "Schedule D Tax Worksheet's ordinary-tax lines); or the 2022 Foreign Earned Income Tax "
                    "Worksheet. If your elected farm income includes net capital gain, you MUST use the [year] "
                    "Schedule D Tax Worksheet. When completing the Schedule D Tax Worksheet, allocate 1/3 of the "
                    "amount on Schedule J line 2b (and 1/3 of line 2c, if any) to [year]. [Line 12: if line 11 is "
                    "zero or less, enter -0-. Line 16: if line 15 is zero or less, enter -0-.]"
                ),
                "summary_text": (
                    "L8/12/16: 0 if the base (L7/L11/L15) <= 0; else tax via the base-year rate schedule "
                    "(ordinary), the base-year QDCGT (preferential income, 2b=0), or the base-year Schedule D Tax "
                    "Worksheet (2b>0; +1/3 of 2b/2c allocated to the base year). The ordinary sub-tax ALWAYS uses "
                    "the base-year RATE SCHEDULES, never the base-year Tax Table. STALE-CROSS-REF: instr cite SDTW "
                    "lines 34/36 (2022) & 42/44 (2023) but the real worksheets are 44/46 — use 44/46 (WALK ITEM C)."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Line 4 (current-year tax) + lines 19-21 (§1-only) + zero-or-less worksheet (RED-defer) — verbatim",
                "location_reference": "i1040sj (2025), Line 4 / Line 5 / Lines 19,20,21",
                "excerpt_text": (
                    "Line 4: figure the tax on line 3 using the 2025 Tax Table, Tax Computation Worksheet, or "
                    "Qualified Dividends and Capital Gain Tax Worksheet from the 2025 Form 1040 instructions; or "
                    "the Schedule D Tax Worksheet in the 2025 Schedule D instructions. Line 5 (and 9, 13): if you "
                    "figured your tax for the base years without using Schedule J, enter the taxable income from "
                    "that base year's Form 1040, line 15. But if that amount is zero or less, complete the [year] "
                    "Taxable Income Worksheet to figure the amount (a negative amount via the NOL/capital-loss "
                    "refiguring). Lines 19, 20, and 21: your 'tax' may, in addition to the tax imposed by section "
                    "1, include amounts from Form 8814 or 4972, recapture of an education credit, or an HCTC "
                    "repayment — include ONLY the section 1 tax."
                ),
                "summary_text": (
                    "L4 = current-year method (Tax Table <$100k / TCW / QDCGT / SDTW) on L3. L5/9/13 = base-year "
                    "1040 line 15 (direct entry); a zero-or-less base year needs the Taxable Income Worksheet "
                    "(NOL/cap-loss) -> RED-defer (preparer enters the negative result; D_SJ_NEG_TI nudges). "
                    "L19/20/21 = base-year §1 tax ONLY (exclude 8814/4972/recapture/HCTC)."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_SCHEDD_SDTW",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2022,
        "tax_year_end": 2025,
        "title": "Schedule D Tax Worksheet (Instructions for Schedule D, Form 1040) — 2022-2025",
        "citation": "i1040sd Schedule D Tax Worksheet (2022/2023/2024/2025)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i1040sd.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": False,
        "trust_score": 9.00,
        "requires_human_review": False,
        "notes": (
            "The Schedule D Tax Worksheet is the IDENTICAL 47-line structure across 2022/23/24/25 (verified "
            "verbatim, pymupdf); only the 3 breakpoint sets differ (PREF_RATE_BREAKPOINTS + SDTW_MID_THRESHOLD). "
            "One year-keyed engine. Ordinary-tax lines 44/46. Used for Sch J lines 4/8/12/16 when 2b>0."
        ),
        "topics": ["base_year_tax_recompute"],
        "excerpts": [
            {
                "excerpt_label": "Schedule D Tax Worksheet — 47-line structure (identical 2022-2025) — verbatim skeleton",
                "location_reference": "i1040sd Schedule D Tax Worksheet, lines 1-47",
                "excerpt_text": (
                    "1 taxable income. 2 qualified dividends (1040 3a). 3/4 Form 4952 4g/4e. 5 = 3-4. 6 = 2-5. 7 "
                    "smaller of Sch D 15/16. 8 smaller of 3/4. 9 = 7-8. 10 = 6+9. 11 = Sch D 18+19. 12 smaller of "
                    "9/11. 13 = 10-12. 14 = 1-13. 15 [0%-rate ceiling by status]. 16 smaller of 1/15. 17 smaller "
                    "of 14/16. 18 = 1-10. 19 smaller of 1 or [mid threshold]. 20 smaller of 14/19. 21 larger of "
                    "18/20. 22 = 16-17 (taxed at 0%). 23 smaller of 1/13. 24 = line 22. 25 = 23-24. 26 [20%-rate "
                    "floor by status]. 27 smaller of 1/26. 28 = 21+22. 29 = 27-28. 30 smaller of 25/29. 31 = "
                    "30x15%. 32 = 24+30. 33 = 23-32. 34 = 33x20%. 35 smaller of 9 or Sch D 19. 36 = 10+21. 37 = "
                    "line 1. 38 = 36-37. 39 = 35-38. 40 = 39x25% (unrecap §1250). 41 = 21+22+30+33+39. 42 = 1-41. "
                    "43 = 42x28% (28%-rate gain). 44 tax on line 21 (Tax Table/TCW; Sch J: BASE-YEAR RATE "
                    "SCHEDULE). 45 = 31+34+40+43+44. 46 tax on line 1 (Tax Table/TCW; Sch J: BASE-YEAR RATE "
                    "SCHEDULE). 47 smaller of 45/46 -> the tax."
                ),
                "summary_text": (
                    "L15 = 0%-rate ceiling (PREF_RATE_BREAKPOINTS.zero_ceiling); L19 = mid threshold "
                    "(SDTW_MID_THRESHOLD); L26 = 20%-rate floor (PREF_RATE_BREAKPOINTS.twenty_floor); L31 x15%, "
                    "L34 x20%, L40 x25% (§1250), L43 x28%; L44/L46 ordinary (Sch J base years -> rate schedule). "
                    "L47 = min(L45, L46). One engine, year-keyed by 3 breakpoint sets + the rate schedule."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_1301",
        "source_type": "statute",
        "source_rank": "primary_authority",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2026,
        "title": "IRC §1301 — Averaging of farm income",
        "citation": "26 U.S.C. §1301; Treas. Reg. 1.1301-1",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/1301",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": (
            "Statutory authority for the Schedule J election. Reg 1.1301-1 defines elected farm income (incl. "
            "gain from property regularly used in farming, LAND excluded) and the base-year allocation. WALK "
            "ITEM A: the line-4 capital-gain netting interaction with the current-year SDTW. requires_human_review=True."
        ),
        "topics": ["schedule_j_income_averaging"],
        "excerpts": [
            {
                "excerpt_label": "§1301(a)/(b) — election and elected farm income (summary)",
                "location_reference": "26 U.S.C. §1301(a),(b)",
                "excerpt_text": (
                    "(a) At the election of an individual engaged in a farming business or fishing business, the "
                    "tax imposed by section 1 for the taxable year shall be equal to the sum of (1) a tax computed "
                    "on taxable income reduced by elected farm income, plus (2) the increase in tax that would "
                    "result from adding one-third of elected farm income to taxable income for each of the 3 prior "
                    "taxable years. (b) Elected farm income means so much of taxable income attributable to any "
                    "farming or fishing business as is specified in the election; gain from the sale of property "
                    "(other than land) regularly used for a substantial period is treated as attributable to such "
                    "business."
                ),
                "summary_text": (
                    "§1301: tax = [tax on TI - elected farm income] + Σ over 3 base years of [tax(base + 1/3 EFI) "
                    "- tax(base)]. This IS the Schedule J line 4 + (8,12,16) - (19,20,21) chain. Land excluded."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []


# ═══════════════════════════════════════════════════════════════════════════
# FORM — SCHEDULE_J (Income Averaging for Farmers/Fishermen) — NEW
# ═══════════════════════════════════════════════════════════════════════════

SCHEDJ_IDENTITY = {
    "form_number": "SCHEDULE_J",
    "form_title": "Schedule J (Form 1040) — Income Averaging for Farmers/Fishermen (TY2025)",
    "notes": (
        "1040 income-averaging ELECTION (IRC §1301). 23-line chain -> Form 1040 line "
        "16 (route gate, only when elected). Base years (TY2025) = 2022/2023/2024; "
        "(TY2026) = 2023/2024/2025. Line 4 = current-year tax on (TI - elected farm "
        "income); lines 8/12/16 = base-year tax on (base TI + 1/3 EFI) via the "
        "BASE-YEAR rate schedule / QDCGT / Schedule D Tax Worksheet (year + filing-"
        "status keyed); lines 19/20/21 = base-year ORIGINAL §1 tax (direct entry); "
        "line 23 = line 18 - line 22. Base-year amounts are preparer DIRECT ENTRY "
        "(optional PriorYearReturn pull). RED-defer (no silent gap): prior-Sch-J "
        "chaining, the zero-or-less Taxable Income worksheets (NOL/cap-loss), Form "
        "2555/FEI. Build SDTW + base-year QDCGT (Ken-locked 2026-06-21)."
    ),
}


def _base_year_facts(n: int) -> list[dict]:
    """The 10 direct-entry facts for base year n (1/2/3). For TY2025: 2022/23/24.
    Lines 5/9/13 (taxable income) + 19/20/21 (tax) + the preferential-income detail
    the base-year QDCGT/SDTW consume. All preparer DIRECT ENTRY (optional YELLOW
    pull from PriorYearReturn)."""
    ti_line = {1: "5", 2: "9", 3: "13"}[n]
    tax_line = {1: "19", 2: "20", 3: "21"}[n]
    base = 100 + n * 20
    return [
        {"fact_key": f"sj_by{n}_filing_status", "label": f"Base year {n} — filing status (single|mfj|mfs|hoh|qss)",
         "data_type": "string", "sort_order": base + 1,
         "notes": "Base-year filing status MAY DIFFER from the election year (Sch J instr) — drives the base-year rate schedule/breakpoints."},
        {"fact_key": f"sj_by{n}_taxable_income", "label": f"Line {ti_line} — base year {n} taxable income (1040 line 15)",
         "data_type": "decimal", "default_value": "0", "sort_order": base + 2,
         "notes": f"DIRECT ENTRY -> Sch J line {ti_line}. MAY be NEGATIVE (zero-or-less Taxable Income Worksheet result; D_SJ_NEG_TI nudges). Prior-Sch-J chaining -> D_SJ_CHAIN."},
        {"fact_key": f"sj_by{n}_tax", "label": f"Line {tax_line} — base year {n} original tax (1040 line 16, §1 only)",
         "data_type": "decimal", "default_value": "0", "sort_order": base + 3,
         "notes": f"DIRECT ENTRY -> Sch J line {tax_line}. §1 tax ONLY (exclude Form 8814/4972, education-credit recapture, HCTC repayment)."},
        {"fact_key": f"sj_by{n}_qualified_dividends", "label": f"Base year {n} — qualified dividends (1040 line 3a)",
         "data_type": "decimal", "default_value": "0", "sort_order": base + 4,
         "notes": "Base-year QDCGT/SDTW line 2. Preferential-rate input."},
        {"fact_key": f"sj_by{n}_net_capital_gain", "label": f"Base year {n} — net capital gain (smaller Sch D 15/16, >=0)",
         "data_type": "decimal", "default_value": "0", "sort_order": base + 5,
         "notes": "Base-year QDCGT line 3 / SDTW line 7 (or 1040 line 7 cap-gain distributions if no Sch D)."},
        {"fact_key": f"sj_by{n}_unrecap_1250", "label": f"Base year {n} — unrecaptured §1250 gain (Sch D line 19)",
         "data_type": "decimal", "default_value": "0", "sort_order": base + 6,
         "notes": "Base-year SDTW (line 35 etc.). 25% rate. Only consumed when 2b>0 (SDTW path)."},
        {"fact_key": f"sj_by{n}_gain_28_rate", "label": f"Base year {n} — 28%-rate gain (Sch D line 18)",
         "data_type": "decimal", "default_value": "0", "sort_order": base + 7,
         "notes": "Base-year SDTW (line 41 gate). 28% rate. Only consumed when 2b>0 (SDTW path)."},
        {"fact_key": f"sj_by{n}_form_4952_4g", "label": f"Base year {n} — Form 4952 line 4g",
         "data_type": "decimal", "default_value": "0", "sort_order": base + 8,
         "notes": "Base-year QDCGT/SDTW line 3. Default 0 (rare — investment-interest election)."},
        {"fact_key": f"sj_by{n}_used_schedule_j", "label": f"Base year {n} — did you use Schedule J for that year? (Y/N)",
         "data_type": "boolean", "sort_order": base + 9,
         "notes": "True -> D_SJ_CHAIN (prior-Schedule-J chaining is RED-defer in v1; the line 5/9/13 + 19/20/21 sources shift to prior Sch J lines)."},
        {"fact_key": f"sj_by{n}_form_2555", "label": f"Base year {n} — Form 2555 (foreign earned income) filed? (Y/N)",
         "data_type": "boolean", "sort_order": base + 10,
         "notes": "True -> D_SJ_2555 (the Foreign Earned Income Tax Worksheet is RED-defer in v1)."},
    ]


SCHEDJ_FACTS: list[dict] = [
    # ── Election + line 2a/2b/2c ──
    {"fact_key": "sj_elected", "label": "Schedule J election active (figure 1040 line 16 via income averaging)", "data_type": "boolean", "sort_order": 1,
     "notes": "Engage gate: when True AND line 2a > 0 AND no RED-defer blocker, 1040 line 16 = Sch J line 23."},
    {"fact_key": "sj_elected_farm_income_2a", "label": "Line 2a — elected farm income", "data_type": "decimal", "default_value": "0", "sort_order": 2,
     "notes": "Preparer-elected farm/fishing income to average (<= line 1; LAND excluded). > line 1 -> D_SJ_2A_EXCEED."},
    {"fact_key": "sj_capital_gain_2b", "label": "Line 2b — net capital gain included in line 2a", "data_type": "decimal", "default_value": "0", "sort_order": 3,
     "notes": "Excess of net LTCG over net STCL in elected farm income. >0 -> the Schedule D Tax Worksheet path on lines 4/8/12/16 (1/3 allocated to each base year)."},
    {"fact_key": "sj_unrecap_1250_2c", "label": "Line 2c — unrecaptured §1250 gain included in line 2a", "data_type": "decimal", "default_value": "0", "sort_order": 4,
     "notes": "Smaller of line 2b or farm unrecap §1250. 25%-rate component within the SDTW path."},
    # ── Current-year (2025) preferential-income detail for the line-4 method ──
    {"fact_key": "sj_cy_qualified_dividends", "label": "Current year — qualified dividends (1040 line 3a)", "data_type": "decimal", "default_value": "0", "sort_order": 10,
     "notes": "Line 4 routing (QDCGT/SDTW). Sourced from the existing return where present; here as the Sch-J input."},
    {"fact_key": "sj_cy_net_capital_gain", "label": "Current year — net capital gain (smaller Sch D 15/16)", "data_type": "decimal", "default_value": "0", "sort_order": 11,
     "notes": "Line 4 SDTW/QDCGT. WALK ITEM A: when 2b>0 the line-4 SDTW likely REDUCES this by 2b (floored at 0) — confirm vs §1301."},
    {"fact_key": "sj_cy_unrecap_1250", "label": "Current year — unrecaptured §1250 gain (Sch D line 19)", "data_type": "decimal", "default_value": "0", "sort_order": 12,
     "notes": "Line 4 SDTW. WALK ITEM A: reduced by 2c when 2b>0 (confirm)."},
    {"fact_key": "sj_cy_gain_28_rate", "label": "Current year — 28%-rate gain (Sch D line 18)", "data_type": "decimal", "default_value": "0", "sort_order": 13,
     "notes": "Line 4 SDTW (28%-rate component)."},
    {"fact_key": "sj_cy_form_4952_4g", "label": "Current year — Form 4952 line 4g", "data_type": "decimal", "default_value": "0", "sort_order": 14,
     "notes": "Line 4 QDCGT/SDTW. Default 0."},
    # ── Outputs (traceability) ──
    {"fact_key": "sj_line17_total", "label": "Line 17/18 — sum of recomputed taxes (output)", "data_type": "decimal", "sort_order": 90,
     "notes": "OUTPUT. = L4 + L8 + L12 + L16."},
    {"fact_key": "sj_line22_total", "label": "Line 22 — sum of base-year original taxes (output)", "data_type": "decimal", "sort_order": 91,
     "notes": "OUTPUT. = L19 + L20 + L21."},
    {"fact_key": "sj_line23_tax", "label": "Line 23 — Schedule J tax -> 1040 line 16 (output)", "data_type": "decimal", "sort_order": 92,
     "notes": "OUTPUT. = L18 - L22. Replaces the regular tax on 1040 line 16 when elected."},
] + _base_year_facts(1) + _base_year_facts(2) + _base_year_facts(3)


SCHEDJ_RULES: list[dict] = [
    {"rule_id": "R-SJ-L3", "title": "Line 3 — taxable income less elected farm income", "rule_type": "calculation", "precedence": 1, "sort_order": 1,
     "formula": "L3 = L1 - L2a, where L1 = 1040 line 15.",
     "inputs": ["sj_elected_farm_income_2a"], "outputs": ["3"],
     "description": "L1 (1040 line 15) minus the elected farm income. L1 >= 0 (1040 L15 floors at 0); L2a <= L1 (D_SJ_2A_EXCEED)."},
    {"rule_id": "R-SJ-L4", "title": "Line 4 — tax on line 3 (CURRENT-year method)", "rule_type": "routing", "precedence": 2, "sort_order": 2,
     "formula": "L4 = tax(L3) using the 2025 method: Tax Table (<$100k) / TCW (>=$100k) / QDCGT (preferential income, 2b=0) / Schedule D Tax Worksheet (2b>0).",
     "inputs": ["sj_cy_qualified_dividends", "sj_cy_net_capital_gain", "sj_cy_unrecap_1250", "sj_cy_gain_28_rate", "sj_capital_gain_2b"], "outputs": ["4"],
     "description": ("CURRENT-year tax (reuses the spine tax + the Topic-3 QDCGT engine + the new year-keyed SDTW). "
                     "WALK ITEM A: when 2b>0 the current-year SDTW likely reduces the Sch D figures by 2b/2c "
                     "(the elected farm cap gain moved into line 2a) — confirm vs §1301 / Reg 1.1301-1.")},
    {"rule_id": "R-SJ-L6", "title": "Line 6 — one-third of elected farm income", "rule_type": "calculation", "precedence": 3, "sort_order": 3,
     "formula": "L6 = round_half_up(L2a / 3). [WALK ITEM B: rounding convention.]",
     "inputs": ["sj_elected_farm_income_2a"], "outputs": ["6"],
     "description": "Divide line 2a by 3.0. WALK ITEM B: recommend round-half-up to whole dollar (QDCGT WS18/21 precedent); L6+L6+L6 need not == L2a."},
    {"rule_id": "R-SJ-L7", "title": "Line 7 — base-year-1 income + 1/3 EFI (floored)", "rule_type": "calculation", "precedence": 4, "sort_order": 4,
     "formula": "L7 = max(0, L5 + L6). 'If zero or less, enter -0-.'",
     "inputs": [], "outputs": ["7"],
     "description": "Combine the 2022 base-year taxable income (line 5) and 1/3 EFI (line 6); FLOORED at 0."},
    {"rule_id": "R-SJ-L8", "title": "Line 8 — tax on line 7 (2022 method)", "rule_type": "routing", "precedence": 5, "sort_order": 5,
     "formula": "L8 = 0 if L7 <= 0 else tax_2022(L7) via the base-year method (rate schedule / QDCGT / SDTW; +1/3 of 2b/2c if SDTW).",
     "inputs": [], "outputs": ["8"],
     "description": "Base-year-1 (2022) recomputed tax. Ordinary sub-tax via the 2022 RATE SCHEDULE (never the 2022 Tax Table)."},
    {"rule_id": "R-SJ-L11", "title": "Line 11 — base-year-2 income + 1/3 EFI (signed)", "rule_type": "calculation", "precedence": 6, "sort_order": 6,
     "formula": "L11 = L9 + L6. 'If less than zero, enter as a negative amount' (NO floor).",
     "inputs": [], "outputs": ["11"],
     "description": "Combine the 2023 base-year taxable income (line 9, may be negative) and 1/3 EFI (line 10 = line 6). May be negative."},
    {"rule_id": "R-SJ-L12", "title": "Line 12 — tax on line 11 (2023 method)", "rule_type": "routing", "precedence": 7, "sort_order": 7,
     "formula": "L12 = 0 if L11 <= 0 else tax_2023(L11) via the base-year method.",
     "inputs": [], "outputs": ["12"],
     "description": "Base-year-2 (2023) recomputed tax. 0 when line 11 <= 0. Ordinary sub-tax via the 2023 RATE SCHEDULE."},
    {"rule_id": "R-SJ-L15", "title": "Line 15 — base-year-3 income + 1/3 EFI (signed)", "rule_type": "calculation", "precedence": 8, "sort_order": 8,
     "formula": "L15 = L13 + L6. 'If less than zero, enter as a negative amount' (NO floor).",
     "inputs": [], "outputs": ["15"],
     "description": "Combine the 2024 base-year taxable income (line 13, may be negative) and 1/3 EFI (line 14 = line 6). May be negative."},
    {"rule_id": "R-SJ-L16", "title": "Line 16 — tax on line 15 (2024 method)", "rule_type": "routing", "precedence": 9, "sort_order": 9,
     "formula": "L16 = 0 if L15 <= 0 else tax_2024(L15) via the base-year method.",
     "inputs": [], "outputs": ["16"],
     "description": "Base-year-3 (2024) recomputed tax. 0 when line 15 <= 0. Ordinary sub-tax via the 2024 RATE SCHEDULE."},
    {"rule_id": "R-SJ-L17", "title": "Line 17/18 — sum of recomputed taxes", "rule_type": "calculation", "precedence": 10, "sort_order": 10,
     "formula": "L17 = L4 + L8 + L12 + L16; L18 = L17.",
     "inputs": [], "outputs": ["17", "18"],
     "description": "Add the current-year tax (line 4) and the three base-year recomputed taxes (8/12/16)."},
    {"rule_id": "R-SJ-L22", "title": "Line 22 — sum of base-year original taxes", "rule_type": "calculation", "precedence": 11, "sort_order": 11,
     "formula": "L22 = L19 + L20 + L21 (each base-year §1 tax, direct entry).",
     "inputs": [], "outputs": ["22"],
     "description": "Add the three base years' ORIGINAL §1 tax (lines 19/20/21, direct entry)."},
    {"rule_id": "R-SJ-L23", "title": "Line 23 — Schedule J tax -> 1040 line 16", "rule_type": "calculation", "precedence": 12, "sort_order": 12,
     "formula": "L23 = L18 - L22 -> sj_line23_tax. Also include on Form 1040 line 16 (when elected).",
     "inputs": [], "outputs": ["23"],
     "description": "The income-averaged tax. Equals §1301: [tax on TI - EFI] + Σ[tax(base + 1/3 EFI) - tax(base)]."},
    {"rule_id": "R-SJ-ROUTE16", "title": "Route — 1040 line 16 = Schedule J line 23 when elected", "rule_type": "routing", "precedence": 13, "sort_order": 13,
     "formula": "If sj_elected AND L2a > 0 AND no RED-defer blocker -> 1040 line 16 = L23 (overrides the regular tax). Else regular tax.",
     "inputs": ["sj_elected", "sj_elected_farm_income_2a"], "outputs": [],
     "description": "The route gate (the Topic-3 route_line_16 precedent). Schedule J is an ELECTION; when elected, line 23 replaces the regular line-16 tax."},
    {"rule_id": "R-SJ-RATES", "title": "Base-year RATE SCHEDULES (year + filing-status keyed)", "rule_type": "calculation", "precedence": 14, "sort_order": 14,
     "formula": "tax_year(amount, status) via BASE_YEAR_RATE_SCHEDULES[year][status] (2022/23/24; 2025/26 from the spine). Cumulative bracket math; round to whole dollar.",
     "inputs": [], "outputs": [],
     "description": ("The ordinary-tax engine for lines 8/12/16 and the SDTW/QDCGT ordinary sub-lines. VERIFIED verbatim "
                     "(brief §5). Base-year tax NEVER uses the Tax Table (Sch J instr override).")},
    {"rule_id": "R-SJ-QDCGT", "title": "Base-year QDCGT worksheet (year + status keyed)", "rule_type": "calculation", "precedence": 15, "sort_order": 15,
     "formula": "27-line QDCGT worksheet, breakpoints PREF_RATE_BREAKPOINTS[year][status]; ordinary lines 24/26 via the base-year rate schedule. Used when 2b=0 AND the base year has qualified dividends / cap-gain distributions.",
     "inputs": [], "outputs": [],
     "description": "Reuses the Topic-3 QDCGT engine, year-keyed. 0%/15%/20% LTCG. Used for lines 4/8/12/16 in the preferential-income (no farm cap gain) case."},
    {"rule_id": "R-SJ-SDTW", "title": "Schedule D Tax Worksheet (year + status keyed; 2b>0)", "rule_type": "calculation", "precedence": 16, "sort_order": 16,
     "formula": "47-line SDTW (identical structure 2022-2025); breakpoints PREF_RATE_BREAKPOINTS + SDTW_MID_THRESHOLD; 25% §1250 (L40), 28% (L43); ordinary lines 44/46 via the base-year rate schedule. Base years add 1/3 of 2b/2c.",
     "inputs": ["sj_capital_gain_2b", "sj_unrecap_1250_2c"], "outputs": [],
     "description": ("REQUIRED for lines 4/8/12/16 when elected farm income includes net capital gain (2b>0). ONE "
                     "year-keyed engine (brief §7). STALE-CROSS-REF: ordinary-tax lines are 44/46 (not the instr's "
                     "34/36 & 42/44). WALK ITEM A (line-4 netting), WALK ITEM C (cross-ref).")},
    {"rule_id": "R-SJ-2ALIMIT", "title": "Line 2a validation — cannot exceed line 1", "rule_type": "validation", "precedence": 17, "sort_order": 17,
     "formula": "If L2a > L1 -> D_SJ_2A_EXCEED (error).",
     "inputs": ["sj_elected_farm_income_2a"], "outputs": [],
     "description": "Elected farm income can't exceed taxable income (form face: 'Do not enter more than the amount on line 1')."},
    {"rule_id": "R-SJ-CHAIN", "title": "Prior-Schedule-J chaining — RED-defer", "rule_type": "routing", "precedence": 18, "sort_order": 18,
     "formula": "If any sj_byN_used_schedule_j is True -> D_SJ_CHAIN; the line 5/9/13 + 19/20/21 sources shift to prior-Sch-J lines (not modeled). No silent compute.",
     "inputs": ["sj_by1_used_schedule_j", "sj_by2_used_schedule_j", "sj_by3_used_schedule_j"], "outputs": [],
     "description": "v1 supports the 'did NOT use Schedule J in the base years' path only. A repeat income-averager triggers RED-defer (the chained prior-Sch-J line references)."},
    {"rule_id": "R-SJ-NEGTI", "title": "Zero-or-less base-year taxable income worksheet — RED-defer (preparer-entered)", "rule_type": "routing", "precedence": 19, "sort_order": 19,
     "formula": "If any base-year taxable income (line 5/9/13) is entered <= 0 -> D_SJ_NEG_TI (warning): use the [year] Taxable Income Worksheet (NOL/cap-loss refiguring) to figure the negative amount; the engine uses the entered value as-is.",
     "inputs": ["sj_by1_taxable_income", "sj_by2_taxable_income", "sj_by3_taxable_income"], "outputs": [],
     "description": "The NOL/capital-loss refiguring worksheet is preparer-handled (v1). The engine accepts the entered (possibly negative) value; the warning nudges the preparer to run the worksheet rather than enter the raw 1040 line 15."},
    {"rule_id": "R-SJ-2555", "title": "Form 2555 / Foreign Earned Income — RED-defer", "rule_type": "routing", "precedence": 20, "sort_order": 20,
     "formula": "If any sj_byN_form_2555 is True (or the current year filed 2555) -> D_SJ_2555; the Foreign Earned Income Tax Worksheet is not modeled. No silent compute for that year's tax.",
     "inputs": ["sj_by1_form_2555", "sj_by2_form_2555", "sj_by3_form_2555"], "outputs": [],
     "description": "The FEI Tax Worksheet (capital-gain-excess handling) is RED-defer in v1."},
]


SCHEDJ_LINES: list[dict] = [
    {"line_number": "1", "description": "Taxable income from 2025 Form 1040 line 15", "line_type": "input"},
    {"line_number": "2a", "description": "Elected farm income (<= line 1)", "line_type": "input"},
    {"line_number": "2b", "description": "Net capital gain included in line 2a", "line_type": "input"},
    {"line_number": "2c", "description": "Unrecaptured §1250 gain included in line 2a", "line_type": "input"},
    {"line_number": "3", "description": "Subtract line 2a from line 1", "line_type": "calculated"},
    {"line_number": "4", "description": "Tax on line 3 using the 2025 rates (current-year method)", "line_type": "calculated"},
    {"line_number": "5", "description": "Base year 1 (2022) taxable income (1040 line 15; or prior Sch J — RED-defer)", "line_type": "input"},
    {"line_number": "6", "description": "Divide line 2a by 3.0", "line_type": "calculated"},
    {"line_number": "7", "description": "Combine lines 5 and 6 (if zero or less, -0-)", "line_type": "calculated"},
    {"line_number": "8", "description": "Tax on line 7 using the 2022 rates", "line_type": "calculated"},
    {"line_number": "9", "description": "Base year 2 (2023) taxable income (1040 line 15)", "line_type": "input"},
    {"line_number": "10", "description": "Amount from line 6", "line_type": "calculated"},
    {"line_number": "11", "description": "Combine lines 9 and 10 (may be negative)", "line_type": "calculated"},
    {"line_number": "12", "description": "Tax on line 11 using the 2023 rates", "line_type": "calculated"},
    {"line_number": "13", "description": "Base year 3 (2024) taxable income (1040 line 15)", "line_type": "input"},
    {"line_number": "14", "description": "Amount from line 6", "line_type": "calculated"},
    {"line_number": "15", "description": "Combine lines 13 and 14 (may be negative)", "line_type": "calculated"},
    {"line_number": "16", "description": "Tax on line 15 using the 2024 rates", "line_type": "calculated"},
    {"line_number": "17", "description": "Add lines 4, 8, 12, and 16", "line_type": "subtotal"},
    {"line_number": "18", "description": "Amount from line 17", "line_type": "calculated"},
    {"line_number": "19", "description": "Base year 1 (2022) original tax (1040 line 16, §1 only)", "line_type": "input"},
    {"line_number": "20", "description": "Base year 2 (2023) original tax (1040 line 16, §1 only)", "line_type": "input"},
    {"line_number": "21", "description": "Base year 3 (2024) original tax (1040 line 16, §1 only)", "line_type": "input"},
    {"line_number": "22", "description": "Add lines 19 through 21", "line_type": "subtotal"},
    {"line_number": "23", "description": "Tax. Subtract line 22 from line 18 -> Form 1040 line 16", "line_type": "total"},
]


SCHEDJ_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_SJ_CHAIN", "title": "Used Schedule J in a base year — chaining not supported", "severity": "error",
     "condition": "any sj_byN_used_schedule_j is True",
     "message": ("Not supported — prepare manually: you used Schedule J to figure your tax for one or more of the "
                 "base years (2022/2023/2024). The prior-Schedule-J line chaining (the base-year income and tax "
                 "come from the prior Schedule J, not Form 1040 line 15/16) is not modeled this version."),
     "notes": "RED-defer prior-Sch-J chaining. v1 supports the 'did not use Schedule J in the base years' path."},
    {"diagnostic_id": "D_SJ_NEG_TI", "title": "Base-year taxable income is zero or less — use the worksheet", "severity": "warning",
     "condition": "any base-year taxable income (line 5/9/13) <= 0",
     "message": ("A base-year taxable income is zero or less. Per the Schedule J instructions, figure the amount "
                 "using that year's Taxable Income Worksheet (which refigures NOLs and disallowed capital losses) "
                 "and enter the result as a negative amount — do not enter the raw Form 1040 line 15. The software "
                 "uses the amount you entered as-is."),
     "notes": "The NOL/cap-loss refiguring worksheet is preparer-handled; the warning nudges. Engine uses the entered value."},
    {"diagnostic_id": "D_SJ_2555", "title": "Form 2555 (foreign earned income) in a relevant year — not supported", "severity": "error",
     "condition": "any sj_byN_form_2555 is True (or current-year Form 2555)",
     "message": ("Not supported — prepare manually: a Form 2555 (foreign earned income exclusion) applies to the "
                 "current year or a base year. The Foreign Earned Income Tax Worksheet (with its capital-gain-"
                 "excess handling) is not modeled this version."),
     "notes": "RED-defer Form 2555 / FEI Tax Worksheet."},
    {"diagnostic_id": "D_SJ_2A_EXCEED", "title": "Elected farm income exceeds taxable income", "severity": "error",
     "condition": "line 2a > line 1",
     "message": ("Elected farm income (line 2a) cannot exceed your taxable income (line 1). Reduce the elected "
                 "farm income to no more than line 1."),
     "notes": "Form face: 'Do not enter more than the amount on line 1.'"},
    {"diagnostic_id": "D_SJ_ELECT_HIGH", "title": "Schedule J tax is not lower than the regular tax", "severity": "warning",
     "condition": "line 23 >= the regular (non-Schedule-J) tax",
     "message": ("Income averaging does not reduce your tax here — the Schedule J tax (line 23) is not less than "
                 "the regular tax. Attach Schedule J only if it lowers your tax. Consider not electing, or "
                 "electing a smaller amount of farm income on line 2a."),
     "notes": "WALK ITEM D: warning-only (the election is the preparer's choice), not a hard block."},
]


# Numeric anchor (SJ-T1) hand-computed off the verified rate schedules; the math
# gate (check_schedule_j_integrity.py) recomputes the whole chain independently.
SCHEDJ_SCENARIOS: list[dict] = [
    {"scenario_name": "SJ-T1 — ordinary case, single, all rate-schedule (full numeric anchor)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "sj_elected": True, "filing_status": "single", "line_1": 180000,
                "sj_elected_farm_income_2a": 60000,
                "sj_by1_filing_status": "single", "sj_by1_taxable_income": 30000, "sj_by1_tax": 3395,
                "sj_by2_filing_status": "single", "sj_by2_taxable_income": 35000, "sj_by2_tax": 3980,
                "sj_by3_filing_status": "single", "sj_by3_taxable_income": 40000, "sj_by3_tax": 4568},
     "expected_outputs": {"line_3": 120000, "line_4": 21647, "line_6": 20000,
                          "line_7": 50000, "line_8": 6617, "line_11": 55000, "line_12": 7408,
                          "line_15": 60000, "line_16": 8253, "line_17": 43925, "line_22": 11943,
                          "line_23": 31982, "regular_tax_2025": 36047, "averaging_saves": True},
     "notes": ("L3=120,000; L4=tax_2025_single(120,000)=21,647; L6=20,000. by1 2022: L7=50,000, "
               "L8=tax_2022_single(50,000)=6,617. by2 2023: L11=55,000, L12=tax_2023_single(55,000)=7,408 "
               "(7,407.50 half-up). by3 2024: L15=60,000, L16=tax_2024_single(60,000)=8,253. L17=43,925; "
               "L22=3,395+3,980+4,568=11,943; L23=31,982 < regular 36,047 -> averaging helps.")},
    {"scenario_name": "SJ-T2 — negative base year (line 11 < 0 -> line 12 = 0)", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"tax_year": 2025, "sj_elected": True, "filing_status": "single", "line_1": 120000,
                "sj_elected_farm_income_2a": 30000,
                "sj_by2_filing_status": "single", "sj_by2_taxable_income": -15000},
     "expected_outputs": {"line_6": 10000, "line_11": -5000, "line_12": 0},
     "notes": "L6=10,000; by2 2023 TI=-15,000 (worksheet result); L11=-15,000+10,000=-5,000 (<=0) -> L12=0."},
    {"scenario_name": "SJ-T3 — cap gain in elected farm income (2b>0) -> Schedule D Tax Worksheet path", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"tax_year": 2025, "sj_elected": True, "filing_status": "single", "line_1": 200000,
                "sj_elected_farm_income_2a": 60000, "sj_capital_gain_2b": 30000, "sj_unrecap_1250_2c": 0,
                "sj_by1_filing_status": "single", "sj_by1_taxable_income": 40000, "sj_by1_net_capital_gain": 0},
     "expected_outputs": {"line4_method": "sdtw", "line8_method": "sdtw", "sdtw_allocates_third_2b": 10000},
     "notes": "2b>0 -> lines 4/8/12/16 use the Schedule D Tax Worksheet; base-year SDTW adds 1/3 of 2b (=10,000) to that base year. (Structural; the math gate carries the 47-line numeric.)"},
    {"scenario_name": "SJ-T4 — base-year qualified dividends (2b=0) -> base-year QDCGT path", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"tax_year": 2025, "sj_elected": True, "filing_status": "single", "line_1": 150000,
                "sj_elected_farm_income_2a": 45000, "sj_capital_gain_2b": 0,
                "sj_by1_filing_status": "single", "sj_by1_taxable_income": 50000, "sj_by1_qualified_dividends": 8000},
     "expected_outputs": {"line8_method": "qdcgt"},
     "notes": "2b=0 AND base year 1 has qualified dividends -> line 8 uses the 2022 QDCGT worksheet (ordinary sub-tax via the 2022 rate schedule)."},
    {"scenario_name": "SJ-T5 — prior Schedule J used (D_SJ_CHAIN RED)", "scenario_type": "normal", "sort_order": 5,
     "inputs": {"tax_year": 2025, "sj_elected": True, "filing_status": "single", "line_1": 120000,
                "sj_elected_farm_income_2a": 30000, "sj_by3_used_schedule_j": True},
     "expected_outputs": {"D_SJ_CHAIN": True, "line_23": None},
     "notes": "Used Schedule J for 2024 -> chaining RED-defer; line 23 not silently computed (no silent gap)."},
    {"scenario_name": "SJ-T6 — Form 2555 in a base year (D_SJ_2555 RED)", "scenario_type": "normal", "sort_order": 6,
     "inputs": {"tax_year": 2025, "sj_elected": True, "filing_status": "single", "line_1": 120000,
                "sj_elected_farm_income_2a": 30000, "sj_by1_form_2555": True},
     "expected_outputs": {"D_SJ_2555": True, "line_23": None},
     "notes": "Form 2555 (FEI) in 2022 -> the Foreign Earned Income Tax Worksheet is RED-defer; no silent compute."},
    {"scenario_name": "SJ-T7 — zero-or-less base-year TI entered (D_SJ_NEG_TI warning + compute proceeds)", "scenario_type": "normal", "sort_order": 7,
     "inputs": {"tax_year": 2025, "sj_elected": True, "filing_status": "single", "line_1": 120000,
                "sj_elected_farm_income_2a": 30000, "sj_by1_taxable_income": -2000},
     "expected_outputs": {"D_SJ_NEG_TI": True, "line_7": 8000},
     "notes": "by1 TI=-2,000 (worksheet result) -> D_SJ_NEG_TI warning; L6=10,000; L7=max(0,-2,000+10,000)=8,000 (compute proceeds with the entered value)."},
    {"scenario_name": "SJ-T8 — line 2a exceeds line 1 (D_SJ_2A_EXCEED)", "scenario_type": "normal", "sort_order": 8,
     "inputs": {"tax_year": 2025, "sj_elected": True, "filing_status": "single", "line_1": 40000,
                "sj_elected_farm_income_2a": 50000},
     "expected_outputs": {"D_SJ_2A_EXCEED": True},
     "notes": "Elected farm income 50,000 > taxable income 40,000 -> error."},
    {"scenario_name": "SJ-T9 — differing filing status (election single, base year MFJ)", "scenario_type": "normal", "sort_order": 9,
     "inputs": {"tax_year": 2025, "sj_elected": True, "filing_status": "single", "line_1": 150000,
                "sj_elected_farm_income_2a": 30000,
                "sj_by1_filing_status": "mfj", "sj_by1_taxable_income": 60000},
     "expected_outputs": {"line_7": 70000, "line8_uses_status": "mfj"},
     "notes": "Filing status may differ between election year and base years (Sch J instr). L7=60,000+10,000=70,000; L8 uses the 2022 MFJ rate schedule."},
    {"scenario_name": "SJ-T10 — line 6 rounding (2a not divisible by 3)", "scenario_type": "edge", "sort_order": 10,
     "inputs": {"tax_year": 2025, "sj_elected": True, "filing_status": "single", "line_1": 100000,
                "sj_elected_farm_income_2a": 50000},
     "expected_outputs": {"line_6": 16667},
     "notes": "L6 = round_half_up(50,000/3) = round_half_up(16,666.67) = 16,667 (WALK ITEM B)."},
]


SCHEDJ_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-SJ-L3", "IRS_2025_SCHEDJ_FORM", "primary", "Line 3 = line 1 - line 2a"),
    ("R-SJ-L4", "IRS_2025_SCHEDJ_INSTR", "primary", "Line 4 current-year method (Tax Table/TCW/QDCGT/SDTW)"),
    ("R-SJ-L6", "IRS_2025_SCHEDJ_FORM", "primary", "Line 6 = line 2a / 3.0"),
    ("R-SJ-L7", "IRS_2025_SCHEDJ_FORM", "primary", "Line 7 = combine 5 and 6 (floor 0)"),
    ("R-SJ-L8", "IRS_2025_SCHEDJ_INSTR", "primary", "Line 8 base-year (2022) method"),
    ("R-SJ-L11", "IRS_2025_SCHEDJ_FORM", "primary", "Line 11 = combine 9 and 10 (signed)"),
    ("R-SJ-L12", "IRS_2025_SCHEDJ_INSTR", "primary", "Line 12 base-year (2023) method"),
    ("R-SJ-L15", "IRS_2025_SCHEDJ_FORM", "primary", "Line 15 = combine 13 and 14 (signed)"),
    ("R-SJ-L16", "IRS_2025_SCHEDJ_INSTR", "primary", "Line 16 base-year (2024) method"),
    ("R-SJ-L17", "IRS_2025_SCHEDJ_FORM", "primary", "Line 17 = 4 + 8 + 12 + 16"),
    ("R-SJ-L22", "IRS_2025_SCHEDJ_FORM", "primary", "Line 22 = 19 + 20 + 21"),
    ("R-SJ-L23", "IRS_2025_SCHEDJ_FORM", "primary", "Line 23 = 18 - 22 -> 1040 line 16"),
    ("R-SJ-L23", "IRC_1301", "secondary", "§1301 averaging formula"),
    ("R-SJ-ROUTE16", "IRC_1301", "primary", "§1301(a) election replaces the §1 tax"),
    ("R-SJ-RATES", "IRS_2025_SCHEDJ_INSTR", "primary", "Base-year 2022/23/24 rate schedules"),
    ("R-SJ-QDCGT", "IRS_2025_SCHEDJ_INSTR", "primary", "Base-year QDCGT worksheets (pages 5/9/13)"),
    ("R-SJ-SDTW", "IRS_2025_SCHEDD_SDTW", "primary", "Schedule D Tax Worksheet (47-line, year-keyed)"),
    ("R-SJ-SDTW", "IRS_2025_SCHEDJ_INSTR", "secondary", "Base-year SDTW: rate-schedule sub-tax + 1/3 2b/2c allocation"),
    ("R-SJ-2ALIMIT", "IRS_2025_SCHEDJ_FORM", "primary", "Line 2a <= line 1"),
    ("R-SJ-CHAIN", "IRS_2025_SCHEDJ_INSTR", "primary", "Prior-Sch-J line chaining (lines 5/9/13/19/20/21)"),
    ("R-SJ-NEGTI", "IRS_2025_SCHEDJ_INSTR", "primary", "Zero-or-less Taxable Income Worksheet"),
    ("R-SJ-2555", "IRS_2025_SCHEDJ_INSTR", "primary", "Foreign Earned Income Tax Worksheet"),
    ("R-SJ-L4", "IRS_2025_SCHEDD_SDTW", "secondary", "Line 4 SDTW when 2b>0"),
]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY FORM LINKS
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_SCHEDJ_FORM", "SCHEDULE_J", "governs"),
    ("IRS_2025_SCHEDJ_INSTR", "SCHEDULE_J", "informs"),
    ("IRS_2025_SCHEDD_SDTW", "SCHEDULE_J", "informs"),
    ("IRC_1301", "SCHEDULE_J", "informs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORMS ROSTER
# ═══════════════════════════════════════════════════════════════════════════

FORMS: list[dict] = [
    {"identity": SCHEDJ_IDENTITY, "facts": SCHEDJ_FACTS, "rules": SCHEDJ_RULES, "lines": SCHEDJ_LINES,
     "diagnostics": SCHEDJ_DIAGNOSTICS, "scenarios": SCHEDJ_SCENARIOS, "rule_links": SCHEDJ_RULE_LINKS},
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS  (staged in tts-tax-app until the assertions build leg)
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-SCHJ-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Schedule J line 23 -> Form 1040 line 16 (route gate, only when elected)",
     "description": ("Validates R-SJ-L23/R-SJ-ROUTE16. L23 = L18 - L22, and when elected it REPLACES the regular "
                     "tax on 1040 line 16. Bug it catches: line 23 not routing to 1040 line 16, or overriding the "
                     "regular tax when Schedule J is not elected."),
     "definition": {"kind": "flow_assertion", "form": "SCHEDULE_J",
                    "source_line": "23", "must_write_to": ["1040.16"], "gated_on": "sj_elected"},
     "sort_order": 1},
    {"assertion_id": "FA-1040-SCHJ-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Schedule J line 17 = 4+8+12+16 and line 22 = 19+20+21",
     "description": ("Validates R-SJ-L17/R-SJ-L22. L17/18 = L4+L8+L12+L16; L22 = L19+L20+L21. Bug it catches: "
                     "dropping a base-year recomputed tax (8/12/16) or a base-year original tax (19/20/21)."),
     "definition": {"kind": "formula_check", "form": "SCHEDULE_J",
                    "formula": "line_17 == line_4 + line_8 + line_12 + line_16; line_22 == line_19 + line_20 + line_21; line_23 == line_18 - line_22"},
     "sort_order": 2},
    {"assertion_id": "FA-1040-SCHJ-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Line 6 = round(2a/3); line 7 floors at 0; lines 11/15 keep the sign",
     "description": ("Validates R-SJ-L6/L7/L11/L15. L6 = round_half_up(L2a/3); L7 = max(0, L5+L6); L11 = L9+L6 and "
                     "L15 = L13+L6 (may be negative). Bug it catches: flooring line 11/15 at 0 (wrong — they keep "
                     "the sign), or not flooring line 7."),
     "definition": {"kind": "formula_check", "form": "SCHEDULE_J",
                    "formula": "line_6 == round_half_up(line_2a / 3); line_7 == max(0, line_5 + line_6); line_11 == line_9 + line_6; line_15 == line_13 + line_6"},
     "sort_order": 3},
    {"assertion_id": "FA-1040-SCHJ-04", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "Base-year tax (lines 8/12/16) uses the base-year RATE SCHEDULES (never the Tax Table)",
     "description": ("Validates R-SJ-RATES. The ordinary sub-tax on lines 8/12/16 (and the SDTW/QDCGT ordinary "
                     "lines) uses BASE_YEAR_RATE_SCHEDULES[year][filing_status], year + status keyed, NOT the "
                     "base-year Tax Table. Bug it catches: using the current-year schedule, the wrong status, or "
                     "the Tax Table for a base year."),
     "definition": {"kind": "constants_check", "form": "SCHEDULE_J",
                    "constants": {"rate_schedules_years": [2022, 2023, 2024],
                                  "single_2022_floors": [10275, 41775, 89075, 170050, 215950, 539900],
                                  "mfj_2024_floors": [23200, 94300, 201050, 383900, 487450, 731200],
                                  "ordinary_via_rate_schedule_not_tax_table": True}},
     "sort_order": 4},
    {"assertion_id": "FA-1040-SCHJ-05", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "Schedule D Tax Worksheet path when 2b>0 (year-keyed; +1/3 of 2b/2c to each base year)",
     "description": ("Validates R-SJ-SDTW. When elected farm income includes net capital gain (2b>0), lines "
                     "4/8/12/16 use the year-keyed Schedule D Tax Worksheet (identical 47-line structure 2022-"
                     "2025; ordinary lines 44/46); the base-year SDTW adds 1/3 of line 2b (and 2c) to that base "
                     "year. Bug it catches: a stale cross-ref (34/36 vs 44/46), or not allocating 1/3 of 2b."),
     "definition": {"kind": "constants_check", "form": "SCHEDULE_J",
                    "constants": {"sdtw_ordinary_lines": [44, 46], "rate_1250": "0.25", "rate_28": "0.28",
                                  "zero_ceiling_2022_single": 41675, "twenty_floor_2024_mfj": 583750,
                                  "mid_threshold_2023_single": 182100, "base_year_allocates_third_2b": True}},
     "sort_order": 5},
    {"assertion_id": "FA-1040-SCHJ-06", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "Base-year QDCGT path when 2b=0 + base-year preferential income (breakpoints year-keyed)",
     "description": ("Validates R-SJ-QDCGT. When 2b=0 and a base year had qualified dividends / cap-gain "
                     "distributions, that year's line (8/12/16) uses the base-year QDCGT worksheet with "
                     "PREF_RATE_BREAKPOINTS[year][status] and the base-year rate schedule for the ordinary lines. "
                     "Bug it catches: using the current-year breakpoints for a base year."),
     "definition": {"kind": "constants_check", "form": "SCHEDULE_J",
                    "constants": {"zero_ceiling_2023_mfj": 89250, "twenty_floor_2022_single": 459750,
                                  "zero_ceiling_2024_hoh": 63000, "ltcg_rates": ["0.0", "0.15", "0.20"]}},
     "sort_order": 6},
    {"assertion_id": "FA-1040-SCHJ-07", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Numeric anchor SJ-T1 — single, ordinary, line 23 = 31,982",
     "description": ("Validates the full chain end-to-end (SJ-T1). L1=180,000 single; L2a=60,000; base years "
                     "2022/23/24 TI 30k/35k/40k, tax 3,395/3,980/4,568 -> L4=21,647, L8=6,617, L12=7,408, "
                     "L16=8,253, L17=43,925, L22=11,943, L23=31,982 (< regular 36,047). Bug it catches: any "
                     "off-by-one in the chain or a rate-schedule transcription error."),
     "definition": {"kind": "formula_check", "form": "SCHEDULE_J",
                    "formula": "given SJ-T1 inputs: line_4==21647 and line_8==6617 and line_12==7408 and line_16==8253 and line_23==31982"},
     "sort_order": 7},
    {"assertion_id": "FA-1040-SCHJ-08", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Schedule J RED-defers each leave a RED (no silent gap)",
     "description": ("Validates the RED-defer set: prior-Schedule-J chaining (D_SJ_CHAIN), zero-or-less base-year "
                     "TI (D_SJ_NEG_TI warning), Form 2555 (D_SJ_2555), line-2a-exceeds-line-1 (D_SJ_2A_EXCEED). "
                     "Each fires rather than silently computing a wrong number."),
     "definition": {"kind": "gating_check", "form": "SCHEDULE_J",
                    "blockers": ["used_schedule_j", "neg_base_year_ti", "form_2555", "elected_farm_income_exceeds_ti"],
                    "expect": {"red_fires": True}},
     "sort_order": 8},
]


# ═══════════════════════════════════════════════════════════════════════════
# Command
# ═══════════════════════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = (
        "Load the Schedule J spec into Rule Studio (creates SCHEDULE_J — income "
        "averaging for farmers/fishermen). Refuses to seed until Ken sets "
        "READY_TO_SEED=True."
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()

        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad SCHEDULE_J spec (income averaging)\n"))

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
        """Refuse to write anything until Ken has reviewed AND flipped READY_TO_SEED."""
        empty = []
        for spec in FORMS:
            fn = spec["identity"]["form_number"]
            for key in ("facts", "rules", "lines", "diagnostics", "scenarios", "rule_links"):
                if not spec[key]:
                    empty.append(f"{fn}.{key}")
        if not FLOW_ASSERTIONS:
            empty.append("FLOW_ASSERTIONS")

        # ID-length guards (the Schedule F seed lesson: FormDiagnostic.diagnostic_id /
        # FormRule.rule_id / FormLine.line_number are varchar(20)). Catch pre-seed.
        too_long = []
        for spec in FORMS:
            for d in spec["diagnostics"]:
                if len(d["diagnostic_id"]) > 20:
                    too_long.append(f"diagnostic_id {d['diagnostic_id']} ({len(d['diagnostic_id'])})")
            for r in spec["rules"]:
                if len(r["rule_id"]) > 20:
                    too_long.append(f"rule_id {r['rule_id']} ({len(r['rule_id'])})")
            for ln in spec["lines"]:
                if len(ln["line_number"]) > 20:
                    too_long.append(f"line_number {ln['line_number']} ({len(ln['line_number'])})")
        for a in FLOW_ASSERTIONS:
            if len(a["assertion_id"]) > 20:
                too_long.append(f"assertion_id {a['assertion_id']} ({len(a['assertion_id'])})")
        if too_long:
            raise CommandError(
                "REFUSING TO SEED SCHEDULE_J: id-length cap exceeded (varchar(20)):\n  "
                + "\n  ".join(too_long)
            )

        if not READY_TO_SEED or empty:
            still_empty = "\n  ".join(f"- {n}" for n in empty) or "(all populated)"
            raise CommandError(
                "\n"
                "REFUSING TO SEED SCHEDULE_J: not cleared to seed.\n"
                "\n"
                "Content is authored, but seeding is gated until Ken reviews the packet\n"
                "(the 23-line chain; the base-year RATE SCHEDULES 2022/23/24 + the base-year\n"
                "QDCGT + the year-keyed Schedule D Tax Worksheet; the RED-defer enumeration —\n"
                "prior-Sch-J chaining / zero-or-less Taxable Income worksheets / Form 2555; the\n"
                "4 requires_human_review walk items A-D, especially A line-4 cap-gain netting)\n"
                "and flips the sentinel.\n"
                "\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True to proceed)\n"
                "\n"
                "Currently empty / placeholder:\n"
                f"  {still_empty}\n"
                "\n"
                "To proceed: review the module-level data lists, then set READY_TO_SEED\n"
                "= True. Idempotent via update_or_create — safe to re-run after edits."
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Topics / sources (mirror load_1040_schedule_f.py exactly)
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
        self.stdout.write("DATABASE TOTALS (after load_1040_schedule_j)")
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

        for fn in ("SCHEDULE_J",):
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
