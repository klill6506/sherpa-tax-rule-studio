"""Load the Form 8615 spec — Tax for Certain Children Who Have Unearned Income.

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
Form 8615 figures the "kiddie tax" (§1(g)): a child's NET UNEARNED INCOME is
taxed at the PARENT's marginal rate (to stop income-shifting to children in low
brackets). The result → the CHILD's Form 1040 line 16 (it REPLACES the child's
ordinary line-16 tax). Parts I-III:
  • Part I (1-5)  child's net unearned income = min(unearned − the §1(g) amount,
                  the child's taxable income).
  • Part II (6-13) tentative tax at the PARENT's rate = tax on (child's net
                  unearned + parent's taxable income + the OTHER children's net
                  unearned) at the parent's rate, minus the parent's own tax,
                  allocated to THIS child by line 5 ÷ (line 5 + line 7).
  • Part III (14-18) child's tax = LARGER of (the parent-rate piece + tax at the
                  child's rate on the rest) vs (tax at the child's rate on all).

Today the app has only the conservative interim diagnostic D_1040_004
(rules_1040.py) firing on ANY unearned income for a claimable filer. This spec
builds the real computation; D_1040_004 narrows to its genuine residual at the
diagnostics leg (the D_8995_001 / D_SC_007 narrow-on-compute precedent).

NO prior RS spec exists (lookup/8615/, FORM_8615, 1040_8615 → all 404). NEW form.

SCOPE (Ken-approved kickoff, two AskUserQuestion decisions 2026-06-24):
  COMPUTES (v1):
    • The full §1(g) ASSEMBLY (lines 1-18) → child's 1040 line 16.
    • The CAP-GAINS / QUALIFIED-DIVIDEND case via the QDCGT worksheet — lines
      9/15/17 reuse `compute_qdcgt_worksheet` with a parent-rate / child-rate
      `ordinary_tax_fn` (the Schedule J / 6251 precedent), plus the i8615 "Line 5
      Worksheets 1/2/3" that allocate the child's QD + net capital gain into the
      net-unearned amount.
  PREPARER-ASSERTED INPUTS (the way the IRS form works — the preparer transcribes
  the parent's figures; no auto-link to the parent's Sherpa return in v1):
    • the §1(g) qualification (k_applies) — the 5-condition test (age/support/
      parent-alive/not-MFJ), preparer-asserted (the dependents-spec pattern;
      NO eligibility-adjudication engine).
    • the PARENT's taxable income (L6), the PARENT's tax (L10), the parent's
      filing status, the parent's qualified dividends + net capital gain (for the
      L9 QDCGT split), and Σ the OTHER children's net unearned income (L7).
    • the child's unearned income / QD / net-cap-gain / taxable income come from
      the child's already-built 1040 / Topic-3 (intdiv) / Schedule D rows at the
      compute leg (sourcing confirmed there).
  RED-DEFERS (v1 — each its own "prepare manually" RED, no silent gap):
    • lines 9/15/17 requiring the SCHEDULE D TAX WORKSHEET (a §1250 unrecaptured
      gain or 28%-rate gain on the child / parent / sibling) — D_8615_002.
    • lines 9/17 where the parent or child used SCHEDULE J (income averaging) for
      their own tax — D_8615_003.
    • a Form 8814 PARENTAL ELECTION (the parent elects to report the child's
      income on the parent's return — a different form) — D_8615_004.

═══════════════════════════════════════════════════════════════════════════
VERIFIED STRUCTURE (i8615 (2025) + f8615 — READ DIRECTLY 2026-06-24, NOT memory;
IRC §1(g); §63(c)(5)(A); §1(h). 2026 constants from Rev. Proc. 2025-32 §3.02/§3.18.)
Full source brief: tts-tax-app/server/specs/_8615_source_brief.md
═══════════════════════════════════════════════════════════════════════════
Part I — Child's Net Unearned Income
  1  Child's unearned income (interest, dividends, capital gains, etc.).
  2  $2,700 if the child did NOT itemize; else $1,350 + the child's directly-
     connected itemized deductions. [year-keyed §63(c)(5)(A) base × 2]
  3  Line 1 − line 2 (if line 3 ≤ 0, the child is NOT subject to the kiddie tax → stop).
  4  Child's taxable income (child's Form 1040 line 15).
  5  SMALLER of line 3 or line 4 = NET UNEARNED INCOME (cannot exceed taxable income).
Part II — Tentative Tax Based on the Parent's Tax Rate
  6  Parent's taxable income (parent's Form 1040 line 15).                [preparer fact]
  7  Σ line 5 of ALL the parent's OTHER children's Forms 8615.            [preparer fact]
  8  Line 5 + line 6 + line 7.
  9  Tax on line 8 at the PARENT's rate (Tax Table / Tax Comp WS / QDCGT WS;
     SDTW / Schedule J → RED-defer).                                     [COMPUTED — reuse]
  10 Parent's tax (parent's Form 1040 line 16).                          [preparer fact]
  11 Line 9 − line 10 = the tentative tax.
  12a Line 5 + line 7;  12b line 5 ÷ line 12a (decimal).
  13 Line 11 × line 12b = THIS child's share of the tentative tax.
Part III — Child's Tax
  14 Line 4 − line 5 (the child's taxable income above net unearned).
  15 Tax on line 14 at the CHILD's rate (Tax Table / QDCGT WS; SDTW → RED-defer). [COMPUTED — reuse]
  16 Line 13 + line 15.
  17 Tax on line 4 at the CHILD's rate (same worksheet menu).            [COMPUTED — reuse]
  18 LARGER of line 16 or line 17 → CHILD's Form 1040 line 16.           [the kiddie tax]

CONSTANTS (verified):
  §63(c)(5)(A) base = $1,350 for BOTH 2025 and 2026 (UNCHANGED) → Form 8615 line 2
  / the kiddie-tax threshold (line 1 must EXCEED) = $2,700 both years. The 0/15/20%
  cap-gains breakpoints + the §1(j) rate schedules for lines 9/15/17 REUSE the
  existing year-keyed Topic-3 QDCGT constants + tax_table_lookup — never re-typed here.

═══════════════════════════════════════════════════════════════════════════
requires_human_review WALK ITEMS (for Ken's in-session review)
═══════════════════════════════════════════════════════════════════════════
W1. THE §1(g) ASSEMBLY + max(L16, L17). The child's tax is the LARGER of (a) the
    parent-rate piece on net unearned (L13) plus the child-rate tax on the rest
    (L15), and (b) the child-rate tax on ALL the child's taxable income (L17). The
    net unearned income (L5) is the smaller of (unearned − $2,700) and the child's
    taxable income, and is allocated among the parent's children by L5 ÷ (L5 + L7).
    CONFIRM the assembly + that L18 → the CHILD's 1040 line 16.
W2. PARENT DATA = PREPARER-ASSERTED FACTS (NOT a parent-return link). The preparer
    transcribes the parent's taxable income (L6), the parent's tax (L10), the
    parent's filing status, the parent's QD + net capital gain (for the L9 QDCGT),
    and Σ the other children's net unearned (L7). The app computes L9/11/13/15/17/18.
    CONFIRM: preparer-asserted parent facts for v1 (auto-link is a v2 item).
W3. CAP-GAINS = FULL QDCGT REUSE; SDTW §1250/28% RED-DEFERRED. Lines 9/15/17 use
    the Qualified Dividends & Capital Gain Tax Worksheet (reusing
    compute_qdcgt_worksheet with the parent-rate / child-rate ordinary_tax_fn) when
    QD / net capital gain is present; the rarer §1250/28% Schedule-D-Tax-Worksheet
    case RED-defers (D_8615_002). CONFIRM the QDCGT-in / SDTW-out boundary.
W4. THE LINE 5 WORKSHEETS (1/2/3). When the child has QD / net capital gain, i8615
    "Line 5 Worksheets 1/2/3" allocate that gain into line 5 (and across the line-2
    deduction) so the QDCGT on L9/L15 taxes the right cap-gain portion at 0/15/20%.
    WS1 (L2 = $2,700 and L3 = L5), WS2 (L2 > $2,700 and L3 = L5), WS3 (L5 < L3).
    The DRAFT specs the allocation PRINCIPLE (R-8615-L5-ALLOC) + provides cap-gain
    test scenarios; the EXACT WS1/2/3 line math is transcribed at the COMPUTE leg.
    CONFIRM this is an acceptable v1 boundary (spec the principle, transcribe the
    worksheet lines at compute) — or does Ken want the full WS line math in the spec?
W5. L13 PRECISION. Line 12b is "a decimal"; the form does not fix the precision.
    The DRAFT carries L12b at full precision and rounds L13 to the whole dollar
    (the QDCGT/tax-table whole-dollar convention). CONFIRM (vs a fixed 3- or
    4-decimal L12b — a $1 difference is possible on large tentative tax).
W6. CONSTANTS. §63(c)(5)(A) base $1,350 → line 2 / threshold $2,700, BOTH 2025 and
    2026 (2026 from Rev. Proc. 2025-32 §3.02/§3.18, read directly; unchanged). The
    rate schedules + QDCGT breakpoints REUSE the existing year-keyed constants (no
    re-typed brackets in 8615). CONFIRM the reuse (single source).

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
# SAFETY GUARD — flip ONLY after Ken's in-session review walk (W1–W6 above:
# the §1(g) assembly + max(L16,L17); the preparer-asserted parent-data model;
# the full-QDCGT / SDTW-RED-defer boundary; the Line 5 worksheet posture; the
# L13 precision; the verified constants). Until then the command writes nothing.
#
# FLIPPED 2026-06-24 — Ken APPROVED the review walk in-session ("Approve"):
# W1 the §1(g) assembly + max(L16,L17) greater-of floor → child's 1040 line 16
# blessed; W2 parent data = preparer-asserted facts (no parent-return link in v1)
# blessed; W3 full QDCGT reuse + RED-defer only §1250/28% SDTW (+ Sch J + Form
# 8814) blessed; W4 the Line 5 worksheets — spec the allocation PRINCIPLE now,
# transcribe the exact WS1/2/3 line math at the COMPUTE leg — APPROVED; W5 L13
# precision = full-precision line 12b + round line 13 to the whole dollar —
# APPROVED; W6 constants ($1,350 base / $2,700 line 2 + threshold, both 2025 +
# 2026 from Rev. Proc. 2025-32; rate schedules / QDCGT breakpoints reused) blessed.
# Math gate check_8615_integrity.py ALL CHECKS PASS (the §1(g) assembly +
# constants + helpers re-derived; 8 scenarios).
# ═══════════════════════════════════════════════════════════════════════════
READY_TO_SEED = True


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1040"]


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS (every value cited; never training memory)
#   §63(c)(5)(A) base — i8615 (2025) line 2 ($2,700) / Rev. Proc. 2025-32 §3.02,
#     §3.18(2) (2026 base $1,350, UNCHANGED → line 2 / threshold $2,700).
#   The line-2 amount = 2 × the §63(c)(5)(A) base; the kiddie-tax threshold (line 1
#     must EXCEED) = the same $2,700.
#   Rate schedules + the 0/15/20% cap-gains breakpoints — REUSED from the existing
#     year-keyed Topic-3 QDCGT constants + tax_table_lookup (single source; NOT
#     re-typed here). Documented below only to pin the FA constants_check.
# ═══════════════════════════════════════════════════════════════════════════

# §63(c)(5)(A) dependent standard-deduction floor (year-keyed). Line 2 = 2 × base.
KIDDIE_STD_FLOOR: dict[int, int] = {2025: 1350, 2026: 1350}
# Form 8615 line 2 (non-itemizer) = the kiddie-tax unearned-income threshold.
KIDDIE_LINE2_AMOUNT: dict[int, int] = {2025: 2700, 2026: 2700}


def kiddie_std_floor_for(year: int) -> int:
    return KIDDIE_STD_FLOOR.get(year) or KIDDIE_STD_FLOOR[2026]


def kiddie_line2_for(year: int) -> int:
    return KIDDIE_LINE2_AMOUNT.get(year) or KIDDIE_LINE2_AMOUNT[2026]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY TOPICS
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("kiddie_tax", "Form 8615 — Tax for certain children who have unearned income: §1(g) net unearned income, the parent's-rate tentative tax, the child's-tax max, the QDCGT/SDTW worksheet routing"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_1040_FORM",  # the child's 1040 line 15 / line 16 cross-form lines
]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY SOURCES (CREATE) — transcribed 2026-06-24 from i8615 (2025) read
# directly + IRC §1(g) + §63(c)(5)(A) + §1(h) + Rev. Proc. 2025-32 (2026 constants).
# requires_human_review = the W-items in the docstring.
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_8615_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "2025 Form 8615 — Tax for Certain Children Who Have Unearned Income",
        "citation": "Form 8615 (2025); f8615.pdf",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f8615.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["kiddie_tax"],
        "excerpts": [
            {
                "excerpt_label": "Form 8615 Parts I-III (2025) — verified line face",
                "excerpt_text": (
                    "Part I: 1 child's unearned income; 2 $2,700 (if the child did not itemize); 3 = line 1 − line 2 "
                    "(if zero or less, do not complete the rest); 4 child's taxable income (1040 line 15); 5 = SMALLER "
                    "of line 3 or line 4 (net unearned income). Part II: 6 parent's taxable income (1040 line 15); 7 "
                    "total of line 5 of all the parent's OTHER children's Forms 8615; 8 = line 5 + line 6 + line 7; 9 "
                    "tax on line 8 using the parent's rate (Tax Table / Tax Computation Worksheet / Qualified Dividends "
                    "& Capital Gain Tax Worksheet / Schedule D Tax Worksheet / Schedule J); 10 parent's tax (1040 line "
                    "16); 11 = line 9 − line 10; 12a = line 5 + line 7; 12b = line 5 ÷ line 12a (decimal); 13 = line 11 "
                    "× line 12b. Part III: 14 = line 4 − line 5; 15 tax on line 14 at the child's rate; 16 = line 13 + "
                    "line 15; 17 tax on line 4 at the child's rate; 18 = LARGER of line 16 or line 17 → child's Form "
                    "1040 line 16."
                ),
                "summary_text": "Form 8615: Part I net unearned income (min(L1−$2,700, L4)); Part II parent-rate tentative tax allocated by L5/(L5+L7); Part III child's tax = max(L16, L17) → 1040 L16.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_8615_INSTR",
        "source_type": "official_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "2025 Instructions for Form 8615 — Tax for Certain Children Who Have Unearned Income",
        "citation": "Instructions for Form 8615 (2025)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/instructions/i8615",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["kiddie_tax"],
        "excerpts": [
            {
                "excerpt_label": "Who must file + the unearned-income threshold ($2,700)",
                "excerpt_text": (
                    "Form 8615 must be filed for a child who meets ALL of: (1) more than $2,700 of unearned income; (2) "
                    "required to file a return; (3) age — under 18 at year-end, OR 18 with earned income not more than "
                    "half of support, OR a full-time student age 19-23 with earned income not more than half of support; "
                    "(4) at least one parent alive at year-end; (5) does not file a joint return. 'Unearned income' = "
                    "income other than wages/salary/professional fees (taxable interest, dividends, capital gains, "
                    "rents, royalties, taxable Social Security, certain trust/estate distributions). The age/support "
                    "tests are preparer-asserted."
                ),
                "summary_text": "Kiddie tax applies to a child with > $2,700 unearned income, under 18 (or 18 / 19-23 student with low earned income), a living parent, not filing jointly. Eligibility is preparer-asserted.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Lines 9/15/17 worksheet routing + the Line 5 Worksheets (QD / cap gain)",
                "excerpt_text": (
                    "Lines 9, 15, and 17 use the Tax Table or Tax Computation Worksheet for ordinary income; the "
                    "Qualified Dividends and Capital Gain Tax Worksheet when the relevant amount includes qualified "
                    "dividends or net capital gain; the Schedule D Tax Worksheet when there is 28%-rate gain (collectibles) "
                    "or unrecaptured §1250 gain; or Schedule J if the parent/child used income averaging. For line 9, the "
                    "QDCGT worksheet uses 'the amount of qualified dividends included on line 8' and 'the net capital gain "
                    "included on line 8' (= the parent's + child's + other children's). The 'Line 5 Worksheets 1, 2, and "
                    "3' allocate the child's qualified dividends and net capital gain into line 5 and across the line-2 "
                    "amount: Worksheet 1 when line 2 = $2,700 and lines 3 and 5 are the same; Worksheet 2 when line 2 is "
                    "more than $2,700 and lines 3 and 5 are the same; Worksheet 3 when line 5 is less than line 3."
                ),
                "summary_text": "Lines 9/15/17 = ordinary (Tax Table) / QDCGT (qualified dividends + net cap gain) / SDTW (28%-rate / §1250, RED-defer) / Schedule J (RED-defer). Line 5 Worksheets 1/2/3 allocate the child's QD + cap gain into line 5.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_1G",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "IRC §1(g) — Certain unearned income of children taxed as if parent's income (the 'kiddie tax')",
        "citation": "26 U.S.C. §1(g) (§1(g)(1) tax at the allocable parental tax; §1(g)(3) allocable parental tax; §1(g)(4) net unearned income; §1(g)(7) parental election)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/1",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 10.0,
        "topics": ["kiddie_tax"],
        "excerpts": [
            {
                "excerpt_label": "§1(g) — the kiddie tax structure",
                "excerpt_text": (
                    "§1(g)(1): the tax on a child's net unearned income is the greater of (A) the tax without §1(g), or "
                    "(B) the sum of the tax on the child's taxable income reduced by net unearned income PLUS the child's "
                    "share of the 'allocable parental tax'. §1(g)(3): the allocable parental tax = the tax the parent "
                    "would pay on the parent's taxable income INCREASED by the net unearned income of all the parent's "
                    "children, MINUS the parent's actual tax — allocated among the children by their net unearned income. "
                    "§1(g)(4): net unearned income = the child's unearned income reduced by $1,350 (2025/2026, §63(c)(5)(A) "
                    "as inflation-adjusted) and by the greater of $1,350 or the directly-connected itemized deductions; "
                    "capped at the child's taxable income. Applies to a child under 18 (or 18 / a 19-23 full-time student "
                    "with earned income ≤ half of support) with a living parent who does not file jointly."
                ),
                "summary_text": "§1(g): a child's net unearned income (unearned − 2 × $1,350, capped at taxable income) is taxed at the parent's marginal rate; the child's tax is the greater of the §1(g) result or the child's own tax.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "RP_2025_32_KIDDIE",
        "source_type": "irs_guidance",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "Rev. Proc. 2025-32 §3.02 / §3.18 — 2026 kiddie tax + dependent standard deduction",
        "citation": "Rev. Proc. 2025-32, §3.02 (Unearned Income of Minor Children — Kiddie Tax, §1(g)) + §3.18(2) (Dependent, §63(c)(5))",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-drop/rp-25-32.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 10.0,
        "topics": ["kiddie_tax"],
        "excerpts": [
            {
                "excerpt_label": "2026 §63(c)(5)(A) base = $1,350 (UNCHANGED) → line 2 / threshold $2,700",
                "excerpt_text": (
                    "Rev. Proc. 2025-32: for tax year 2026, 'the amount of unearned income on a child's return that is "
                    "subject to the kiddie tax, is $1,350. This $1,350 amount is the same as the amount provided in "
                    "§63(c)(5)(A), as adjusted for inflation.' §3.18(2): the dependent standard deduction under "
                    "§63(c)(5) cannot exceed the greater of (1) $1,350, or (2) $450 + the individual's earned income. The "
                    "$1,350 base is UNCHANGED from 2025, so Form 8615 line 2 (non-itemizer) and the > unearned-income "
                    "filing threshold = 2 × $1,350 = $2,700 for BOTH 2025 and 2026."
                ),
                "summary_text": "2026: §63(c)(5)(A) base = $1,350 (unchanged from 2025) → Form 8615 line 2 / kiddie threshold = $2,700 for both 2025 and 2026.",
                "is_key_excerpt": True,
            },
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_8615_FORM", "8615", "defines"),
    ("IRC_1G", "8615", "supports"),
    ("RP_2025_32_KIDDIE", "8615", "supports"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 8615 — FACTS  (k_ = kiddie; per child return)
# ═══════════════════════════════════════════════════════════════════════════

F8615_FACTS: list[dict] = [
    # ── Scope / qualification (preparer-asserted) ──
    {"fact_key": "k_applies", "label": "Form 8615 applies (the §1(g) 5-condition test is met)",
     "data_type": "boolean", "default_value": "false", "sort_order": 1,
     "notes": "PREPARER-ASSERTED gate: > $2,700 unearned + required to file + age (under 18 / 18 / 19-23 student w/ low earned) + a living parent + not MFJ. No eligibility engine (the dependents pattern). True → this engine; replaces the interim D_1040_004."},
    # ── Part I — child's net unearned income ──
    {"fact_key": "k_child_unearned_income", "label": "Line 1 — child's unearned income",
     "data_type": "decimal", "default_value": "0", "sort_order": 2,
     "notes": "Line 1. Taxable interest + ordinary dividends + capital gains + rents/royalties + taxable SS + certain trust/estate income. Sourced from the child's 1040 / Topic-3 / Sch D at compute."},
    {"fact_key": "k_child_itemizes", "label": "Child itemizes (Schedule A)?",
     "data_type": "boolean", "default_value": "false", "sort_order": 3,
     "notes": "Drives line 2: non-itemizer → $2,700; itemizer → $1,350 + directly-connected itemized deductions."},
    {"fact_key": "k_child_directly_connected_deductions", "label": "Line 2 (itemizer) — directly-connected itemized deductions",
     "data_type": "decimal", "default_value": "0", "sort_order": 4,
     "notes": "Itemizer only: deductions directly connected with producing the unearned income (added to $1,350 for line 2). Rare; preparer fact."},
    {"fact_key": "k_line2_amount", "label": "Line 2 — $2,700 (non-itemizer) or $1,350 + directly-connected (OUTPUT)",
     "data_type": "decimal", "sort_order": 5,
     "notes": "OUTPUT. = 2 × the §63(c)(5)(A) base ($2,700) if not itemizing; else $1,350 + directly-connected deductions. Year-keyed."},
    {"fact_key": "k_line3_unearned_over", "label": "Line 3 — line 1 − line 2 (OUTPUT)", "data_type": "decimal", "sort_order": 6,
     "notes": "OUTPUT = line 1 − line 2. If ≤ 0, the child is NOT subject to the kiddie tax (stop; D_8615_006)."},
    {"fact_key": "k_child_taxable_income", "label": "Line 4 — child's taxable income (1040 line 15)",
     "data_type": "decimal", "default_value": "0", "sort_order": 7,
     "notes": "Line 4 = the child's Form 1040 line 15. Sourced from the child's computed 1040 at compute."},
    {"fact_key": "k_line5_net_unearned", "label": "Line 5 — net unearned income = min(line 3, line 4) (OUTPUT)",
     "data_type": "decimal", "sort_order": 8,
     "notes": "OUTPUT = SMALLER of line 3 or line 4. The amount taxed at the parent's rate. §1(g)(4): can't exceed taxable income."},
    # ── Child cap-gains composition (for the QDCGT reuse + Line 5 worksheets) ──
    {"fact_key": "k_child_qualified_dividends", "label": "Child's qualified dividends (in unearned income)",
     "data_type": "decimal", "default_value": "0", "sort_order": 9,
     "notes": "For the Line 5 Worksheets + the QDCGT on lines 15/17. The child's qualified dividends (1040 line 3a). Sourced from Topic-3 at compute."},
    {"fact_key": "k_child_net_capital_gain", "label": "Child's net capital gain (in unearned income)",
     "data_type": "decimal", "default_value": "0", "sort_order": 10,
     "notes": "For the Line 5 Worksheets + the QDCGT on lines 15/17. = qualified dividends + net LT cap gain over net ST loss (Sch D). Sourced from Topic-3 / Sch D at compute."},
    # ── Part II — parent data (PREPARER-ASSERTED) ──
    {"fact_key": "k_parent_taxable_income", "label": "Line 6 — parent's taxable income (parent's 1040 line 15)",
     "data_type": "decimal", "default_value": "0", "sort_order": 20,
     "notes": "PREPARER FACT (the parent's return is not linked in v1). The taxpayer-parent if MFJ; the parent with the greater taxable income if the parents file separately / are unmarried (i8615)."},
    {"fact_key": "k_parent_filing_status", "label": "Parent's filing status (for the line-9 rate schedule)",
     "data_type": "string", "default_value": "mfj", "sort_order": 21,
     "notes": "PREPARER FACT. Drives the line-9 rate schedule / QDCGT breakpoints (the parent's bracket). single / mfj / mfs / hoh / qss."},
    {"fact_key": "k_parent_tax", "label": "Line 10 — parent's tax (parent's 1040 line 16)",
     "data_type": "decimal", "default_value": "0", "sort_order": 22,
     "notes": "Line 10. PREPARER FACT = the parent's actual tax on the parent's taxable income (their 1040 line 16). Subtracted from line 9 to isolate the marginal tax on the children's net unearned income."},
    {"fact_key": "k_parent_qualified_dividends", "label": "Parent's qualified dividends (for the line-9 QDCGT split)",
     "data_type": "decimal", "default_value": "0", "sort_order": 23,
     "notes": "For line 9: 'qualified dividends included on line 8' = parent + child + other children. PREPARER FACT (the parent's 1040 line 3a)."},
    {"fact_key": "k_parent_net_capital_gain", "label": "Parent's net capital gain (for the line-9 QDCGT split)",
     "data_type": "decimal", "default_value": "0", "sort_order": 24,
     "notes": "For line 9: 'net capital gain included on line 8'. PREPARER FACT (the parent's QDCGT worksheet line 3)."},
    {"fact_key": "k_other_children_net_unearned", "label": "Line 7 — Σ line 5 of the parent's OTHER children's Forms 8615",
     "data_type": "decimal", "default_value": "0", "sort_order": 25,
     "notes": "Line 7. PREPARER FACT (multi-child allocation). 0 when this is the parent's only child filing Form 8615. Drives line 12a / 12b."},
    # ── Part II — outputs ──
    {"fact_key": "k_line8", "label": "Line 8 — line 5 + line 6 + line 7 (OUTPUT)", "data_type": "decimal", "sort_order": 30,
     "notes": "OUTPUT = line 5 + line 6 + line 7. The base for the parent-rate tax on line 9."},
    {"fact_key": "k_line9_tax_parentrate", "label": "Line 9 — tax on line 8 at the parent's rate (OUTPUT — reuse)", "data_type": "decimal", "sort_order": 31,
     "notes": "OUTPUT = tax_table_lookup / compute_qdcgt_worksheet on line 8 at the parent's filing status (QD + net cap gain from parent + children). SDTW §1250/28% or Schedule J → RED-defer (D_8615_002/003)."},
    {"fact_key": "k_line11_tentative", "label": "Line 11 — line 9 − line 10 = tentative tax (OUTPUT)", "data_type": "decimal", "sort_order": 32,
     "notes": "OUTPUT = line 9 − line 10. The extra parent-bracket tax attributable to ALL the children's net unearned income."},
    {"fact_key": "k_line12b_ratio", "label": "Line 12b — line 5 ÷ (line 5 + line 7) (OUTPUT)", "data_type": "decimal", "sort_order": 33,
     "notes": "OUTPUT = line 5 ÷ line 12a (line 5 + line 7), as a decimal. This child's share of the children's combined net unearned income. 1.0 when an only child (line 7 = 0)."},
    {"fact_key": "k_line13_child_share", "label": "Line 13 — line 11 × line 12b (OUTPUT)", "data_type": "decimal", "sort_order": 34,
     "notes": "OUTPUT = line 11 × line 12b (whole dollar). THIS child's share of the parent-rate tentative tax."},
    # ── Part III — child's tax ──
    {"fact_key": "k_line14_child_excess", "label": "Line 14 — line 4 − line 5 (OUTPUT)", "data_type": "decimal", "sort_order": 40,
     "notes": "OUTPUT = line 4 − line 5. The child's taxable income ABOVE the net unearned income (taxed at the child's own rate)."},
    {"fact_key": "k_line15_tax_childrate", "label": "Line 15 — tax on line 14 at the child's rate (OUTPUT — reuse)", "data_type": "decimal", "sort_order": 41,
     "notes": "OUTPUT = tax_table_lookup / compute_qdcgt_worksheet on line 14 at the child's (single) rate. SDTW §1250/28% → RED-defer."},
    {"fact_key": "k_line16", "label": "Line 16 — line 13 + line 15 (OUTPUT)", "data_type": "decimal", "sort_order": 42,
     "notes": "OUTPUT = line 13 + line 15. The §1(g) tax = the parent-rate share on net unearned + the child-rate tax on the rest."},
    {"fact_key": "k_line17_tax_all_childrate", "label": "Line 17 — tax on line 4 at the child's rate (OUTPUT — reuse)", "data_type": "decimal", "sort_order": 43,
     "notes": "OUTPUT = tax_table_lookup / compute_qdcgt_worksheet on line 4 (ALL the child's taxable income) at the child's rate. The 'tax without §1(g)' floor."},
    {"fact_key": "k_line18_kiddie_tax", "label": "Line 18 — LARGER of line 16 or line 17 → child's 1040 line 16 (OUTPUT)", "data_type": "decimal", "sort_order": 44,
     "notes": "OUTPUT = max(line 16, line 17). The child's tax (§1(g)(1) greater-of). → the child's Form 1040 line 16, replacing the ordinary line-16 tax."},
    # ── RED-defer flags ──
    {"fact_key": "k_sdtw_required", "label": "Schedule D Tax Worksheet required (§1250 / 28%-rate gain)?",
     "data_type": "boolean", "default_value": "false", "sort_order": 50,
     "notes": "RED-defer: a 28%-rate gain (collectibles) or unrecaptured §1250 gain on the child/parent/sibling forces lines 9/15/17 onto the SDTW (not built for kiddie). D_8615_002 → line 18 blanked, prepare manually."},
    {"fact_key": "k_uses_schedule_j", "label": "Parent or child used Schedule J (income averaging)?",
     "data_type": "boolean", "default_value": "false", "sort_order": 51,
     "notes": "RED-defer: if the parent (line 9/10) or child (line 17) figured tax with Schedule J, lines 9/17 must use Schedule J (not wired into 8615 in v1). D_8615_003."},
    {"fact_key": "k_form_8814_election", "label": "Parent elected Form 8814 (report child's income on the parent's return)?",
     "data_type": "boolean", "default_value": "false", "sort_order": 52,
     "notes": "RED-defer/route: §1(g)(7) — the parent may elect to include the child's gross income on the parent's return (Form 8814) INSTEAD of Form 8615. A different form (not built); D_8615_004."},
    # ── Constants ──
    {"fact_key": "k_line2_base", "label": "§63(c)(5)(A) base / line-2 amount (CONSTANT, year-keyed)", "data_type": "decimal", "sort_order": 80,
     "notes": "CONSTANT: §63(c)(5)(A) base $1,350 → line 2 / threshold $2,700 (2025 i8615; 2026 Rev. Proc. 2025-32 §3.02/§3.18 — unchanged)."},
    {"fact_key": "k_rate_schedule_ref", "label": "Rate schedules + QDCGT breakpoints (REUSED — single source)", "data_type": "decimal", "sort_order": 81,
     "notes": "CONSTANT/REF: lines 9/15/17 reuse the existing year-keyed §1(j) rate schedule (tax_table_lookup) + the Topic-3 QDCGT 0/15/20% breakpoints. NOT re-typed in 8615 compute — single source."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 8615 — RULES
# ═══════════════════════════════════════════════════════════════════════════

F8615_RULES: list[dict] = [
    {"rule_id": "R-8615-SCOPE", "title": "Scope gate — Form 8615 (kiddie tax) engaged", "rule_type": "routing", "precedence": 0, "sort_order": 1,
     "formula": ("Form 8615 is computed when the §1(g) 5-condition test is met (k_applies, preparer-asserted): the child has "
                 "> $2,700 unearned income, is required to file, meets the age/support test (under 18; or 18 / a 19-23 "
                 "full-time student with earned income ≤ half of support), has a living parent at year-end, and does not "
                 "file jointly. The result REPLACES the child's ordinary 1040 line-16 tax. Narrows the interim D_1040_004."),
     "inputs": ["k_applies", "k_child_unearned_income"], "outputs": [],
     "description": "PER CHILD RETURN. The §1(g) applicability gate (preparer-asserted; no eligibility engine)."},
    {"rule_id": "R-8615-L2-DED", "title": "Line 2 — the §63(c)(5)(A) deduction amount", "rule_type": "calculation", "precedence": 1, "sort_order": 2,
     "formula": ("Line 2 = $2,700 (= 2 × the §63(c)(5)(A) base $1,350) if the child did NOT itemize; else $1,350 + the "
                 "child's itemized deductions directly connected with producing the unearned income. Year-keyed ($2,700 "
                 "both 2025 and 2026 — the base is unchanged)."),
     "inputs": ["k_child_itemizes", "k_child_directly_connected_deductions", "k_line2_base"], "outputs": ["2"],
     "description": "Part I. The kiddie-tax exemption amount (2 × the dependent standard-deduction floor)."},
    {"rule_id": "R-8615-L1-5", "title": "Lines 1-5 — child's net unearned income", "rule_type": "calculation", "precedence": 2, "sort_order": 3,
     "formula": ("Line 3 = line 1 (unearned income) − line 2. If line 3 ≤ 0, the child is NOT subject to the kiddie tax "
                 "(stop). Line 4 = the child's taxable income (1040 line 15). Line 5 = SMALLER of line 3 or line 4 = the "
                 "NET UNEARNED INCOME (§1(g)(4): cannot exceed taxable income)."),
     "inputs": ["k_child_unearned_income", "k_line2_amount", "k_child_taxable_income"], "outputs": ["3", "5"],
     "description": "Part I. The net unearned income taxed at the parent's rate."},
    {"rule_id": "R-8615-L5-ALLOC", "title": "Line 5 Worksheets 1/2/3 — allocate the child's QD + net capital gain into line 5", "rule_type": "calculation", "precedence": 3, "sort_order": 4,
     "formula": ("When the child has qualified dividends / net capital gain (k_child_qualified_dividends / "
                 "k_child_net_capital_gain), i8615 'Line 5 Worksheets 1, 2, and 3' determine how much of the net unearned "
                 "income on line 5 is qualified dividends vs net capital gain vs ordinary — for the QDCGT on lines 9/15. "
                 "WS1: line 2 = $2,700 and line 3 = line 5. WS2: line 2 > $2,700 and line 3 = line 5. WS3: line 5 < line 3 "
                 "(prorate). [W4 — the EXACT worksheet line math is transcribed at the compute leg; the spec defines the "
                 "allocation principle + the routing.]"),
     "inputs": ["k_child_qualified_dividends", "k_child_net_capital_gain", "k_line5_net_unearned", "k_line2_amount", "k_line3_unearned_over"], "outputs": ["5"],
     "description": "Part I (cap-gains). Splits the child's net unearned income into QD / net-cap-gain / ordinary for the QDCGT. requires_human_review (W4)."},
    {"rule_id": "R-8615-L6-8", "title": "Lines 6-8 — combine with the parent + other children", "rule_type": "calculation", "precedence": 4, "sort_order": 5,
     "formula": ("Line 6 = the parent's taxable income (1040 line 15; if the parents are not MFJ, the parent with the "
                 "greater taxable income). Line 7 = Σ line 5 of all the parent's OTHER children's Forms 8615. Line 8 = "
                 "line 5 + line 6 + line 7."),
     "inputs": ["k_line5_net_unearned", "k_parent_taxable_income", "k_other_children_net_unearned"], "outputs": ["8"],
     "description": "Part II. The combined base for the parent-rate tax (parent + all children's net unearned)."},
    {"rule_id": "R-8615-L9", "title": "Line 9 — tax on line 8 at the parent's rate (QDCGT reuse)", "rule_type": "calculation", "precedence": 5, "sort_order": 6,
     "formula": ("Line 9 = the tax on line 8 at the PARENT's filing status. Ordinary income → the Tax Table / Tax "
                 "Computation Worksheet (tax_table_lookup). If line 8 includes qualified dividends or net capital gain "
                 "(parent + children) → the Qualified Dividends & Capital Gain Tax Worksheet (REUSE compute_qdcgt_worksheet "
                 "with the parent's rate schedule as ordinary_tax_fn; the 'QD included on line 8' = parent + children's QD, "
                 "the 'net capital gain on line 8' = parent + children's). A §1250/28% gain → the Schedule D Tax Worksheet "
                 "(RED-defer, D_8615_002); Schedule J → RED-defer (D_8615_003)."),
     "inputs": ["k_line8", "k_parent_filing_status", "k_parent_qualified_dividends", "k_parent_net_capital_gain", "k_child_qualified_dividends", "k_child_net_capital_gain", "k_rate_schedule_ref"], "outputs": ["9"],
     "description": "Part II. The parent-rate tax — reuses tax_table_lookup / compute_qdcgt_worksheet (W3, single source)."},
    {"rule_id": "R-8615-L10-13", "title": "Lines 10-13 — tentative tax allocated to this child", "rule_type": "calculation", "precedence": 6, "sort_order": 7,
     "formula": ("Line 10 = the parent's tax (1040 line 16). Line 11 = line 9 − line 10 = the tentative tax (the extra "
                 "parent-bracket tax on the children's net unearned). Line 12a = line 5 + line 7; line 12b = line 5 ÷ line "
                 "12a (decimal, full precision). Line 13 = line 11 × line 12b (whole dollar) = THIS child's share."),
     "inputs": ["k_line9_tax_parentrate", "k_parent_tax", "k_line5_net_unearned", "k_other_children_net_unearned"], "outputs": ["11", "12a", "12b", "13"],
     "description": "Part II. Isolate the parent-bracket tax on net unearned income, allocate to this child by net-unearned share (W5 precision)."},
    {"rule_id": "R-8615-L14-16", "title": "Lines 14-16 — child's tax on the excess + the §1(g) sum", "rule_type": "calculation", "precedence": 7, "sort_order": 8,
     "formula": ("Line 14 = line 4 − line 5 (the child's taxable income above net unearned income). Line 15 = the tax on "
                 "line 14 at the CHILD's rate (Tax Table / QDCGT for the child's own QD/cap-gain above net unearned; SDTW "
                 "RED-defer). Line 16 = line 13 + line 15."),
     "inputs": ["k_child_taxable_income", "k_line5_net_unearned", "k_line13_child_share"], "outputs": ["14", "15", "16"],
     "description": "Part III. The §1(g)(1)(B) tax = parent-rate share + child-rate tax on the remainder."},
    {"rule_id": "R-8615-L17-18", "title": "Lines 17-18 — child's tax = max(line 16, line 17) → 1040 line 16", "rule_type": "calculation", "precedence": 8, "sort_order": 9,
     "formula": ("Line 17 = the tax on line 4 (ALL the child's taxable income) at the CHILD's rate (the 'tax without §1(g)' "
                 "floor; QDCGT for the child's QD/cap-gain; SDTW RED-defer). Line 18 = the LARGER of line 16 or line 17 → "
                 "the child's Form 1040 line 16. §1(g)(1): the kiddie tax never produces LESS than the child's own tax."),
     "inputs": ["k_line16", "k_child_taxable_income", "k_child_qualified_dividends", "k_child_net_capital_gain"], "outputs": ["17", "18"],
     "description": "Part III. The greater-of result → the child's 1040 line 16 (the kiddie tax)."},
    {"rule_id": "R-8615-DEFER", "title": "RED-defer — SDTW §1250/28% + Schedule J + Form 8814 (no silent gap)", "rule_type": "routing", "precedence": 9, "sort_order": 10,
     "formula": ("If lines 9/15/17 require the Schedule D Tax Worksheet (a 28%-rate / unrecaptured §1250 gain on the "
                 "child/parent/sibling), line 18 is BLANKED → D_8615_002 (prepare manually). If the parent or child used "
                 "Schedule J → D_8615_003. If the parent elected Form 8814 (report the child's income on the parent's "
                 "return) → D_8615_004 (a different form; Form 8615 does not apply). The tier math is otherwise computed; "
                 "the unsupported routing is flagged — never a silently-wrong number."),
     "inputs": ["k_sdtw_required", "k_uses_schedule_j", "k_form_8814_election"], "outputs": ["18"],
     "description": "PER CHILD. The no-silent-gap guard (SPRINT quality rule 2) for the three deferred routings."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 8615 — LINES (exact, read from the 2025 f8615.pdf — 18 lines, 3 parts)
# ═══════════════════════════════════════════════════════════════════════════

F8615_LINES: list[dict] = [
    {"line_number": "1", "description": "Child's unearned income", "line_type": "input"},
    {"line_number": "2", "description": "$2,700 (non-itemizer) or $1,350 + directly-connected itemized deductions", "line_type": "calculated"},
    {"line_number": "3", "description": "Line 1 − line 2 (if zero or less, do not complete the rest of the form)", "line_type": "calculated"},
    {"line_number": "4", "description": "Child's taxable income (Form 1040 line 15)", "line_type": "input"},
    {"line_number": "5", "description": "Smaller of line 3 or line 4 (net unearned income)", "line_type": "calculated"},
    {"line_number": "6", "description": "Parent's taxable income (parent's Form 1040 line 15)", "line_type": "input"},
    {"line_number": "7", "description": "Total of line 5 of all the parent's other children's Forms 8615", "line_type": "input"},
    {"line_number": "8", "description": "Add lines 5, 6, and 7", "line_type": "calculated"},
    {"line_number": "9", "description": "Tax on line 8 at the parent's rate (Tax Table / QDCGT WS; SDTW / Sch J RED-defer)", "line_type": "calculated"},
    {"line_number": "10", "description": "Parent's tax (parent's Form 1040 line 16)", "line_type": "input"},
    {"line_number": "11", "description": "Subtract line 10 from line 9 (tentative tax)", "line_type": "calculated"},
    {"line_number": "12a", "description": "Add line 5 and line 7", "line_type": "calculated"},
    {"line_number": "12b", "description": "Divide line 5 by line 12a (decimal)", "line_type": "calculated"},
    {"line_number": "13", "description": "Multiply line 11 by line 12b (this child's share of the tentative tax)", "line_type": "calculated"},
    {"line_number": "14", "description": "Subtract line 5 from line 4", "line_type": "calculated"},
    {"line_number": "15", "description": "Tax on line 14 at the child's rate (Tax Table / QDCGT WS; SDTW RED-defer)", "line_type": "calculated"},
    {"line_number": "16", "description": "Add lines 13 and 15", "line_type": "calculated"},
    {"line_number": "17", "description": "Tax on line 4 at the child's rate (Tax Table / QDCGT WS; SDTW RED-defer)", "line_type": "calculated"},
    {"line_number": "18", "description": "Larger of line 16 or line 17 → child's Form 1040 line 16 (the kiddie tax)", "line_type": "total"},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 8615 — DIAGNOSTICS
# ═══════════════════════════════════════════════════════════════════════════

F8615_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_8615_001", "title": "Kiddie tax applies — child's unearned income taxed at the parent's rate", "severity": "info",
     "condition": "k_applies True AND line 5 (net unearned income) > 0 AND line 18 computed",
     "message": ("This child's net unearned income over $2,700 is taxed at the parent's marginal rate (Form 8615, the "
                 "'kiddie tax', §1(g)). The child's tax on Form 1040 line 16 is the larger of the parent-rate result "
                 "(line 16) or the child's own tax (line 17). Verify the parent's taxable income (line 6) and tax (line "
                 "10), and the other children's net unearned income (line 7)."),
     "notes": "Info — the computed kiddie tax. Replaces the interim D_1040_004 'unearned income present' nudge for the supported case."},
    {"diagnostic_id": "D_8615_002", "title": "Schedule D Tax Worksheet required (§1250 / 28%-rate gain) — prepare manually", "severity": "error",
     "condition": "k_sdtw_required True (a 28%-rate or unrecaptured §1250 gain on the child / parent / sibling)",
     "message": ("Not supported — prepare manually: lines 9/15/17 require the Schedule D Tax Worksheet because a 28%-rate "
                 "gain (collectibles) or unrecaptured §1250 gain is present on the child, parent, or another child. The "
                 "kiddie-tax Schedule D Tax Worksheet is not built this version. Figure Form 8615 manually and enter line "
                 "18 on the child's Form 1040 line 16."),
     "notes": "RED-defer the §1250/28% SDTW path (W3). The Qualified Dividends & Capital Gain case IS computed; only SDTW defers."},
    {"diagnostic_id": "D_8615_003", "title": "Parent or child used Schedule J (income averaging) — prepare manually", "severity": "error",
     "condition": "k_uses_schedule_j True",
     "message": ("Not supported — prepare manually: the parent (line 9/10) or the child (line 17) figured tax using "
                 "Schedule J (farm/fishing income averaging), so lines 9/17 must also use Schedule J. The kiddie-tax "
                 "Schedule J path is not wired this version. Figure Form 8615 manually."),
     "notes": "RED-defer the Schedule J path on lines 9/17 (rare overlap with a kiddie return)."},
    {"diagnostic_id": "D_8615_004", "title": "Form 8814 parental election present — Form 8615 does not apply", "severity": "warning",
     "condition": "k_form_8814_election True",
     "message": ("The parent elected to report this child's interest and dividend income on the parent's own return (Form "
                 "8814, §1(g)(7)). When that election is made, the child does NOT file Form 8615. Form 8814 is a separate "
                 "form (not built this version) — verify the election and prepare Form 8814 manually if used."),
     "notes": "Routing — Form 8814 (parental election) is mutually exclusive with Form 8615; a different (unbuilt) form."},
    {"diagnostic_id": "D_8615_005", "title": "Form 8615 elected but parent data is missing", "severity": "error",
     "condition": "k_applies True AND line 5 > 0 AND (parent taxable income (line 6) is 0 / parent tax (line 10) is 0 with a positive line 9 base)",
     "message": ("The kiddie tax applies (net unearned income over $2,700), but required parent data is missing: the "
                 "parent's taxable income (line 6) and the parent's tax (line 10) are needed to figure the tax at the "
                 "parent's rate (lines 9-13). Enter the parent's Form 1040 line 15 (taxable income) and line 16 (tax)."),
     "notes": "Data validation — the parent-rate computation needs the preparer-entered parent taxable income + tax."},
    {"diagnostic_id": "D_8615_006", "title": "Net unearned income is zero or less — child not subject to the kiddie tax", "severity": "info",
     "condition": "k_applies True AND line 3 (line 1 − line 2) ≤ 0",
     "message": ("The child's unearned income does not exceed $2,700 (line 3 ≤ 0), so the child is NOT subject to the "
                 "kiddie tax — the child's tax is figured normally on the child's own return. If the kiddie-tax flag was "
                 "set in error, clear it; the child's regular tax stands."),
     "notes": "Info — the not-subject case (the threshold gate). The interim D_1040_004 over-fires below the threshold; this is the real boundary."},
    {"diagnostic_id": "D_8615_007", "title": "Multiple children with unearned income — verify the line-7 allocation", "severity": "info",
     "condition": "line 7 (other children's net unearned) > 0",
     "message": ("This parent has more than one child with net unearned income. The tentative tax (line 11) is allocated "
                 "among the children by each child's net unearned income (line 12b = line 5 ÷ (line 5 + line 7)). Make "
                 "sure line 7 equals the total of line 5 from ALL the parent's other children's Forms 8615, and that each "
                 "child's Form 8615 uses the SAME parent taxable income / tax."),
     "notes": "Info — the multi-child sibling allocation (each child's 8615 shares the parent figures + the combined net unearned)."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 8615 — TEST SCENARIOS (worked math; check_8615_integrity.py re-derives the
# §1(g) ASSEMBLY. The lines 9/10/15/17 tax-at-rate VALUES are scenario inputs —
# the QDCGT / Tax Table lookups are the Ken-approved REUSE of the existing engine,
# not re-derived in the 8615 gate. Tax inputs: t_l9 (line 9), k_parent_tax (line
# 10), t_l15 (line 15), t_l17 (line 17).)
# ═══════════════════════════════════════════════════════════════════════════

F8615_SCENARIOS: list[dict] = [
    {"scenario_name": "8615-T1 — ordinary, only child, parent rate > child rate", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "k_applies": True, "k_child_itemizes": False,
                "k_child_unearned_income": 5000, "k_child_taxable_income": 3650,
                "k_parent_taxable_income": 100000, "k_parent_filing_status": "mfj", "k_other_children_net_unearned": 0,
                "t_l9": 12906, "k_parent_tax": 12400, "t_l15": 135, "t_l17": 365},
     "expected_outputs": {"line_2": 2700, "line_3": 2300, "line_5": 2300, "line_8": 102300,
                          "line_11": 506, "line_12b": 1.0, "line_13": 506, "line_14": 1350,
                          "line_16": 641, "line_18": 641, "D_8615_001": True},
     "notes": ("Child unearned 5,000; not itemizing → line 2 = 2,700; line 3 = 2,300. Child taxable 3,650 (5,000 − 1,350 "
               "std ded). Line 5 = min(2,300, 3,650) = 2,300. Line 8 = 2,300 + 100,000 = 102,300. Line 9 (parent rate on "
               "102,300, MFJ) = 12,906; line 10 (parent tax on 100,000) = 12,400; line 11 = 506. Only child → line 12b = "
               "1.0; line 13 = 506. Line 14 = 3,650 − 2,300 = 1,350; line 15 (child rate) = 135; line 16 = 641. Line 17 "
               "(child rate on 3,650) = 365. Line 18 = max(641, 365) = 641 → 1040 line 16. Kiddie tax > the child's own tax.")},
    {"scenario_name": "8615-T2 — net unearned CAPPED by taxable income (line 5 = line 4)", "scenario_type": "edge_case", "sort_order": 2,
     "inputs": {"tax_year": 2025, "k_applies": True, "k_child_itemizes": False,
                "k_child_unearned_income": 6000, "k_child_taxable_income": 3000,
                "k_parent_taxable_income": 200000, "k_parent_filing_status": "mfj", "k_other_children_net_unearned": 0,
                "t_l9": 5060, "k_parent_tax": 4340, "t_l15": 0, "t_l17": 300},
     "expected_outputs": {"line_2": 2700, "line_3": 3300, "line_5": 3000, "line_8": 203000,
                          "line_11": 720, "line_12b": 1.0, "line_13": 720, "line_14": 0,
                          "line_16": 720, "line_18": 720},
     "notes": ("§1(g)(4) cap: line 3 = 6,000 − 2,700 = 3,300, but line 4 (taxable income) = 3,000, so line 5 = min(3,300, "
               "3,000) = 3,000 (net unearned can't exceed taxable income). Line 8 = 3,000 + 200,000 = 203,000; line 11 = "
               "5,060 − 4,340 = 720; line 13 = 720. Line 14 = 3,000 − 3,000 = 0 → line 15 = 0; line 16 = 720. Line 17 "
               "(child on 3,000) = 300. Line 18 = max(720, 300) = 720.")},
    {"scenario_name": "8615-T3 — multi-child sibling allocation (line 7 > 0 → line 12b < 1)", "scenario_type": "edge_case", "sort_order": 3,
     "inputs": {"tax_year": 2025, "k_applies": True, "k_child_itemizes": False,
                "k_child_unearned_income": 5700, "k_child_taxable_income": 4350,
                "k_parent_taxable_income": 150000, "k_parent_filing_status": "mfj", "k_other_children_net_unearned": 1000,
                "t_l9": 5060, "k_parent_tax": 4180, "t_l15": 135, "t_l17": 435},
     "expected_outputs": {"line_2": 2700, "line_3": 3000, "line_5": 3000, "line_8": 154000,
                          "line_11": 880, "line_12a": 4000, "line_12b": 0.75, "line_13": 660,
                          "line_14": 1350, "line_16": 795, "line_18": 795, "D_8615_007": True},
     "notes": ("Child net unearned line 5 = min(5,700 − 2,700, 4,350) = 3,000. Sibling line 7 = 1,000 → line 8 = 3,000 + "
               "150,000 + 1,000 = 154,000. Line 11 = 5,060 − 4,180 = 880 (the parent-bracket tax on BOTH children's "
               "4,000). Line 12a = 3,000 + 1,000 = 4,000; line 12b = 3,000/4,000 = 0.75; line 13 = 880 × 0.75 = 660 (this "
               "child's share). Line 14 = 4,350 − 3,000 = 1,350; line 15 = 135; line 16 = 795. Line 17 = 435. Line 18 = "
               "max(795, 435) = 795. D_8615_007 (verify the sibling allocation).")},
    {"scenario_name": "8615-T4 — child's OWN tax wins (line 17 > line 16: low parent bracket)", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"tax_year": 2025, "k_applies": True, "k_child_itemizes": False,
                "k_child_unearned_income": 4000, "k_child_taxable_income": 6650,
                "k_parent_taxable_income": 20000, "k_parent_filing_status": "mfj", "k_other_children_net_unearned": 0,
                "t_l9": 2330, "k_parent_tax": 2200, "t_l15": 415, "t_l17": 668},
     "expected_outputs": {"line_2": 2700, "line_3": 1300, "line_5": 1300, "line_8": 21300,
                          "line_11": 130, "line_12b": 1.0, "line_13": 130, "line_14": 5350,
                          "line_16": 545, "line_18": 668},
     "notes": ("The child also has earned income (taxable 6,650 > unearned). Line 3 = 4,000 − 2,700 = 1,300; line 5 = "
               "1,300. Parent in the 10% bracket: line 11 = 2,330 − 2,200 = 130; line 13 = 130. Line 14 = 6,650 − 1,300 "
               "= 5,350; line 15 = 415; line 16 = 545. Line 17 (child's own tax on 6,650) = 668. Line 18 = max(545, 668) "
               "= 668 → the §1(g)(1) floor: the kiddie tax never falls below the child's own tax.")},
    {"scenario_name": "8615-T5 — qualified dividends / net capital gain → QDCGT reuse (computed)", "scenario_type": "normal", "sort_order": 5,
     "inputs": {"tax_year": 2025, "k_applies": True, "k_child_itemizes": False,
                "k_child_unearned_income": 8000, "k_child_taxable_income": 6650,
                "k_child_qualified_dividends": 8000, "k_child_net_capital_gain": 8000,
                "k_parent_taxable_income": 120000, "k_parent_filing_status": "mfj",
                "k_parent_qualified_dividends": 5000, "k_parent_net_capital_gain": 5000, "k_other_children_net_unearned": 0,
                "t_l9": 18075, "k_parent_tax": 17400, "t_l15": 0, "t_l17": 0},
     "expected_outputs": {"line_2": 2700, "line_3": 5300, "line_5": 5300, "line_8": 125300,
                          "line_11": 675, "line_12b": 1.0, "line_13": 675, "line_14": 1350,
                          "line_16": 675, "line_18": 675},
     "notes": ("All the child's unearned income is qualified dividends / net capital gain (8,000). Line 5 = min(5,300, "
               "6,650) = 5,300. Line 9 = the QDCGT on 125,300 at the parent's rate (the 5,300 child cap-gain + 5,000 "
               "parent cap-gain taxed at 15%): line 9 = 18,075, line 10 = 17,400, line 11 = 675 (= 5,300 × 15% + a rate "
               "bump). Line 14 = 6,650 − 5,300 = 1,350; the 1,350 is all cap-gain under the 0% bracket for the child → "
               "line 15 = 0; line 16 = 675. Line 17 (QDCGT on 6,650, child, all cap-gain ≤ 0% bracket) = 0. Line 18 = "
               "max(675, 0) = 675. The QDCGT amounts (t_l9/t_l15/t_l17) are the REUSED compute_qdcgt_worksheet outputs; "
               "the gate verifies the §1(g) assembly. [Line 5 cap-gain allocation: W4 transcribes WS1 at compute.]")},
    {"scenario_name": "8615-T6 — §1250 / 28%-rate gain → SDTW RED-defer (D_8615_002)", "scenario_type": "edge_case", "sort_order": 6,
     "inputs": {"tax_year": 2025, "k_applies": True, "k_child_unearned_income": 9000, "k_child_taxable_income": 7650,
                "k_child_net_capital_gain": 9000, "k_sdtw_required": True,
                "k_parent_taxable_income": 300000, "k_parent_filing_status": "mfj", "k_parent_tax": 60000},
     "expected_outputs": {"D_8615_002": True, "line_18": None},
     "notes": ("A 28%-rate (collectibles) or unrecaptured §1250 gain forces the Schedule D Tax Worksheet on lines 9/15/17 "
               "→ D_8615_002 RED-defer; line 18 BLANKED (prepare manually). The Qualified Dividends & Capital Gain case "
               "IS computed (T5); only the §1250/28% SDTW path defers. No silent gap.")},
    {"scenario_name": "8615-T7 — not subject: unearned income ≤ $2,700 (D_8615_006)", "scenario_type": "edge_case", "sort_order": 7,
     "inputs": {"tax_year": 2025, "k_applies": True, "k_child_itemizes": False,
                "k_child_unearned_income": 2500, "k_child_taxable_income": 1150,
                "k_parent_taxable_income": 100000, "k_parent_filing_status": "mfj", "k_parent_tax": 12400},
     "expected_outputs": {"line_2": 2700, "line_3": -200, "line_5": 0, "D_8615_006": True, "line_18": None},
     "notes": ("Unearned 2,500 ≤ 2,700 → line 3 = 2,500 − 2,700 = -200 (≤ 0). The child is NOT subject to the kiddie tax "
               "(D_8615_006) — Form 8615 is not completed; the child's tax is figured normally on the child's own "
               "return. Net unearned (line 5) = max(0, min(-200, 1150)) = 0. The interim D_1040_004 over-fires here; "
               "this line-3 ≤ 0 gate is the real threshold boundary.")},
    {"scenario_name": "8615-T8 — 2026 constants (base $1,350 / line 2 $2,700 unchanged)", "scenario_type": "normal", "sort_order": 8,
     "inputs": {"tax_year": 2026, "k_applies": True, "k_child_itemizes": False,
                "k_child_unearned_income": 5000, "k_child_taxable_income": 3650,
                "k_parent_taxable_income": 100000, "k_parent_filing_status": "mfj", "k_other_children_net_unearned": 0,
                "t_l9": 12750, "k_parent_tax": 12250, "t_l15": 135, "t_l17": 365},
     "expected_outputs": {"line_2": 2700, "line_3": 2300, "line_5": 2300, "line_8": 102300,
                          "line_11": 500, "line_12b": 1.0, "line_13": 500, "line_14": 1350,
                          "line_16": 635, "line_18": 635},
     "notes": ("TY2026: the §63(c)(5)(A) base is UNCHANGED at $1,350 (Rev. Proc. 2025-32 §3.02/§3.18) → line 2 = $2,700, "
               "threshold $2,700 — identical to 2025. Same assembly; the parent/child rate-schedule tax inputs (t_l9 etc.) "
               "differ by the 2026 brackets (reused). Line 18 = max(635, 365) = 635.")},
]


# ═══════════════════════════════════════════════════════════════════════════
# RULE → AUTHORITY LINKS
# ═══════════════════════════════════════════════════════════════════════════

F8615_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-8615-SCOPE", "IRS_2025_8615_INSTR", "primary", "Who must file Form 8615 (the 5 conditions)"),
    ("R-8615-SCOPE", "IRC_1G", "primary", "§1(g) applicability"),
    ("R-8615-L2-DED", "RP_2025_32_KIDDIE", "primary", "§63(c)(5)(A) base $1,350 → line 2 $2,700 (2025/2026)"),
    ("R-8615-L2-DED", "IRC_1G", "secondary", "§1(g)(4) net unearned reduction amounts"),
    ("R-8615-L1-5", "IRS_2025_8615_FORM", "primary", "Part I lines 1-5 net unearned income"),
    ("R-8615-L1-5", "IRC_1G", "secondary", "§1(g)(4) net unearned ≤ taxable income"),
    ("R-8615-L5-ALLOC", "IRS_2025_8615_INSTR", "primary", "Line 5 Worksheets 1/2/3 (QD / cap gain allocation)"),
    ("R-8615-L6-8", "IRS_2025_8615_FORM", "primary", "Part II lines 6-8 combine parent + children"),
    ("R-8615-L9", "IRS_2025_8615_INSTR", "primary", "Line 9 worksheet routing (Tax Table / QDCGT / SDTW / Sch J)"),
    ("R-8615-L9", "IRC_1G", "secondary", "§1(g)(3) allocable parental tax"),
    ("R-8615-L10-13", "IRS_2025_8615_FORM", "primary", "Part II lines 10-13 tentative tax + allocation"),
    ("R-8615-L10-13", "IRC_1G", "secondary", "§1(g)(3)(B) allocation by net unearned income"),
    ("R-8615-L14-16", "IRS_2025_8615_FORM", "primary", "Part III lines 14-16"),
    ("R-8615-L17-18", "IRS_2025_8615_FORM", "primary", "Part III lines 17-18 (max → 1040 line 16)"),
    ("R-8615-L17-18", "IRC_1G", "secondary", "§1(g)(1) greater-of"),
    ("R-8615-DEFER", "IRS_2025_8615_INSTR", "primary", "Lines 9/15/17 SDTW / Schedule J; Form 8814 election"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS (staged into tts-tax-app at the assertions leg)
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-8615-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Form 8615 line 18 → child's Form 1040 line 16",
     "description": ("Validates R-8615-L17-18. The kiddie tax (line 18) → the child's Form 1040 line 16, REPLACING the "
                     "child's ordinary line-16 tax. Bug it catches: the kiddie tax not reaching line 16, or the child's "
                     "ordinary tax surviving."),
     "definition": {"kind": "flow_assertion", "form": "8615", "source_line": "18", "must_write_to": ["1040.16"]},
     "sort_order": 1},
    {"assertion_id": "FA-1040-8615-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Net unearned income: line 5 = min(line 3, line 4)",
     "description": ("Validates R-8615-L1-5 / §1(g)(4). Net unearned income (line 5) is the smaller of (unearned − $2,700) "
                     "and the child's taxable income. Bug it catches: net unearned exceeding taxable income, or the wrong "
                     "$2,700 threshold."),
     "definition": {"kind": "formula_check", "form": "8615", "formula": "line_5 == min(line_3, line_4)"},
     "sort_order": 2},
    {"assertion_id": "FA-1040-8615-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Line 8 = line 5 + line 6 + line 7 (child + parent + siblings)",
     "description": ("Validates R-8615-L6-8. The parent-rate base combines this child's net unearned, the parent's "
                     "taxable income, and the other children's net unearned. Bug it catches: omitting the sibling "
                     "amounts or the parent's income."),
     "definition": {"kind": "formula_check", "form": "8615", "formula": "line_8 == line_5 + line_6 + line_7"},
     "sort_order": 3},
    {"assertion_id": "FA-1040-8615-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Tentative-tax allocation: line 13 = line 11 × (line 5 ÷ (line 5 + line 7))",
     "description": ("Validates R-8615-L10-13 / §1(g)(3)(B). The tentative tax (line 9 − line 10) is allocated to this "
                     "child by its share of the children's combined net unearned income. Bug it catches: the wrong "
                     "allocation ratio, or not subtracting the parent's own tax (line 10)."),
     "definition": {"kind": "formula_check", "form": "8615",
                    "formula": "line_13 == round(line_11 * line_5 / (line_5 + line_7))"},
     "sort_order": 4},
    {"assertion_id": "FA-1040-8615-05", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Child's tax = max(line 16, line 17) — the §1(g)(1) greater-of floor",
     "description": ("Validates R-8615-L17-18 / §1(g)(1). The child's tax is the LARGER of the parent-rate result (line "
                     "16) or the child's own tax (line 17), so the kiddie tax never falls below the child's ordinary "
                     "tax. Bug it catches: taking line 16 unconditionally, or the wrong floor."),
     "definition": {"kind": "formula_check", "form": "8615", "formula": "line_18 == max(line_16, line_17)"},
     "sort_order": 5},
    {"assertion_id": "FA-1040-8615-06", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Lines 9/15/17 reuse the QDCGT worksheet for qualified dividends / net capital gain",
     "description": ("Validates R-8615-L9 / R-8615-L14-16 / R-8615-L17-18 / W3. When the relevant amount includes "
                     "qualified dividends or net capital gain, the tax reuses compute_qdcgt_worksheet (parent-rate / "
                     "child-rate ordinary_tax_fn — the Schedule J / 6251 precedent), NOT a re-typed rate schedule. Bug "
                     "it catches: taxing the child's cap gains at the ordinary rate."),
     "definition": {"kind": "gating_check", "form": "8615",
                    "blockers": ["cap_gain_taxed_ordinary", "rate_schedule_retyped_in_8615"],
                    "expect": {"reuses_compute_qdcgt_worksheet": True}},
     "sort_order": 6},
    {"assertion_id": "FA-1040-8615-07", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "§63(c)(5)(A) base $1,350 → line 2 / threshold $2,700 (2025 + 2026)",
     "description": ("Pins the kiddie-tax constants: the §63(c)(5)(A) base ($1,350) and the line-2 / unearned-income "
                     "threshold ($2,700), unchanged for 2026 (Rev. Proc. 2025-32). Bug it catches: a stale or mis-keyed "
                     "threshold, or a 2026 drift."),
     "definition": {"kind": "constants_check", "form": "8615",
                    "constants": {"kiddie_std_floor_2025": KIDDIE_STD_FLOOR[2025],
                                  "kiddie_std_floor_2026": KIDDIE_STD_FLOOR[2026],
                                  "line2_amount_2025": KIDDIE_LINE2_AMOUNT[2025],
                                  "line2_amount_2026": KIDDIE_LINE2_AMOUNT[2026],
                                  "applies_to_years": [2025, 2026]}},
     "sort_order": 7},
    {"assertion_id": "FA-1040-8615-08", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Net unearned income capped at taxable income (line 5 ≤ line 4)",
     "description": ("Validates §1(g)(4): a child's net unearned income can never exceed the child's taxable income "
                     "(line 5 = min(line 3, line 4)). Bug it catches: taxing more than the child actually has as taxable "
                     "income at the parent's rate."),
     "definition": {"kind": "formula_check", "form": "8615", "formula": "line_5 <= line_4"},
     "sort_order": 8},
    {"assertion_id": "FA-1040-8615-09", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "RED-defer no-silent-gap: SDTW §1250/28% / Schedule J blank line 18 + fire a RED",
     "description": ("Validates R-8615-DEFER. A §1250/28% Schedule-D-Tax-Worksheet requirement blanks line 18 + fires "
                     "D_8615_002; a Schedule J overlap fires D_8615_003; a Form 8814 election fires D_8615_004. Bug it "
                     "catches: a silently-wrong kiddie tax when an unsupported worksheet/election is present."),
     "definition": {"kind": "gating_check", "form": "8615",
                    "blockers": ["sdtw_required", "schedule_j_used", "form_8814_election"],
                    "expect": {"red_fires": True, "line_18_blank_on_sdtw": True}},
     "sort_order": 9},
]


FORMS: list[dict] = [
    {
        "identity": {
            "form_number": "8615",
            "form_title": "Form 8615 — Tax for Certain Children Who Have Unearned Income (TY2025)",
            "notes": (
                "NEW spec (no prior RS draft — lookup/8615 etc. all 404). The kiddie tax (§1(g)): Part I child's net "
                "unearned income = min(unearned − $2,700, taxable income); Part II tentative tax at the PARENT's rate "
                "(tax on net unearned + parent taxable income + other children's net unearned, minus the parent's tax, "
                "allocated by line 5 ÷ (line 5 + line 7)); Part III child's tax = LARGER of (parent-rate share + child-"
                "rate tax on the rest) vs (child-rate tax on all) → the child's 1040 line 16. v1 COMPUTES the qualified-"
                "dividend / net-capital-gain case by reusing compute_qdcgt_worksheet (parent/child ordinary_tax_fn); "
                "RED-defers the §1250/28% Schedule D Tax Worksheet, Schedule J, and the Form 8814 parental election. "
                "Parent data is preparer-asserted (no parent-return link in v1). Constants verified: $1,350 base / $2,700 "
                "line 2 / threshold, both 2025 and 2026 (2026 from Rev. Proc. 2025-32). Narrows the interim D_1040_004 "
                "at the diagnostics leg. Full source brief: tts-tax-app/server/specs/_8615_source_brief.md."
            ),
        },
        "facts": F8615_FACTS,
        "rules": F8615_RULES,
        "lines": F8615_LINES,
        "diagnostics": F8615_DIAGNOSTICS,
        "scenarios": F8615_SCENARIOS,
        "rule_links": F8615_RULE_LINKS,
    },
]


class Command(BaseCommand):
    help = (
        "Load the Form 8615 spec (Tax for Certain Children Who Have Unearned "
        "Income — the kiddie tax §1(g): net unearned income at the parent's rate "
        "→ the child's 1040 line 16). Refuses to seed until Ken sets "
        "READY_TO_SEED=True after the in-session review walk."
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()

        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad FORM 8615 spec (Kiddie Tax §1(g))\n"))

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
                "\nREFUSING TO SEED FORM 8615: not cleared to seed.\n\n"
                "Content is authored, but seeding is gated until Ken reviews the packet\n"
                "(W1 the §1(g) assembly + max(L16,L17); W2 the preparer-asserted parent\n"
                "data; W3 the full-QDCGT / SDTW-RED-defer boundary; W4 the Line 5\n"
                "worksheet posture; W5 the L13 precision; W6 the verified constants) and\n"
                "flips the sentinel.\n\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True to proceed)\n\n"
                f"Currently empty / placeholder:\n  {still_empty}\n\n"
                "To proceed: review the module-level data lists, then set READY_TO_SEED\n"
                "= True. Idempotent via update_or_create — safe to re-run after edits."
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Topics / sources (mirror load_1040_form_8829.py exactly)
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
        self.stdout.write("FORM 8615 loaded.")
        self.stdout.write(
            f"  facts {len(F8615_FACTS)} / rules {len(F8615_RULES)} / lines {len(F8615_LINES)} / "
            f"diagnostics {len(F8615_DIAGNOSTICS)} / tests {len(F8615_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}"
        )
        self.stdout.write("=" * 60)
