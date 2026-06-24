"""Load the Form 6251 spec — Alternative Minimum Tax (Individuals).

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
Form 6251 (Alternative Minimum Tax — Individuals) recomputes tax on a broader
base (AMTI = regular taxable income + preference/adjustment add-backs), allows a
phased-out exemption, applies the 26%/28% AMT rate schedule (with a capital-gains
worksheet in Part III), and charges the EXCESS of the tentative minimum tax over
the regular tax. Line 11 → Schedule 2 line 2 → Form 1040 line 17 → total tax.

This is the FIRST AMT engine for the suite. Before it, AMT was a presence-check
guardrail only (`apps/diagnostics/rules_amt.py` D_AMT_DEFER — fires on a PAB-
interest / K-1-AMT indicator, cleared by a MANUAL Form 6251 result on Schedule 2
line 2). The DEFERRAL_AUDIT calls AMT "the single most important finding — the one
silent gap." This spec builds the common-case engine; D_AMT_DEFER NARROWS to the
still-deferred preferences (the D_8995_001 / D_8582 narrow-on-compute precedent).

NO prior RS spec exists (lookup/6251/ → 404). This is a NEW form (not a re-author).

SCOPE (Ken-approved kickoff, AskUserQuestion 2026-06-23 — "common-case engine"):
  COMPUTES (v1):
    • Line 1 AMTI base — taxable income + std-deduction-or-SALT add-back +
      OBBBA senior-deduction add-back; QBI retained (Ken-confirmed 2026-06-23)
    • 2a Taxes (Sch A line 7 SALT for itemizers; the standard deduction otherwise)
    • 2b Tax refund (subtract)
    • 2g Specified private activity bond interest (the app already tracks pab_interest)
    • 2l Post-1986 depreciation difference (the depreciation engine carries AMT adj)
    • Line 5 exemption + phaseout (year-keyed; 2026 OBBBA)
    • Part II 6-11 (tentative minimum tax → AMT → Schedule 2 line 2)
    • Part III 12-40 AMT capital-gains worksheet (reuse the app's QDCGT/SDTW machinery)
  RED-DEFERS (v1 — each its own "prepare manually" RED, no silent gap):
    • 2c investment interest, 2d depletion, 2e/2f NOL/ATNOLD, 2h QSBS, 2i ISO,
      2j estates/trusts (K-1 1041), 2k disposition, 2m passive, 2n loss limits,
      2o-2t (circulation/contracts/mining/R&E/installment/IDC), line 3 other
    • Line 8 AMT foreign tax credit (needs a Form 1116 AMT variant)

═══════════════════════════════════════════════════════════════════════════
VERIFIED FORM STRUCTURE (2025 f6251.pdf — READ DIRECTLY via pymupdf, NOT memory;
i6251 instructions cross-checked)
═══════════════════════════════════════════════════════════════════════════
Part I — Alternative Minimum Taxable Income
  1a  Subtract Schedule 1-A (Form 1040) line 37 from Form 1040 line 14
  1b  Subtract line 1a from Form 1040 line 11b (if < 0, negative)  [AMTI base]
  2a  If filing Sch A: taxes from Sch A line 7; otherwise the standard deduction
      (Form 1040 line 12e)                                          [v1 IN]
  2b  Tax refund from Schedule 1 line 1 or 8z (subtract)            [v1 IN]
  2c  Investment interest expense (reg vs AMT difference)           [RED-defer]
  2d  Depletion (difference)                                        [RED-defer]
  2e  NOL deduction from Schedule 1 line 8a (enter as POSITIVE)     [RED-defer]
  2f  Alternative tax NOL deduction (subtract)                      [RED-defer]
  2g  Interest from specified private activity bonds (exempt from regular tax) [v1 IN]
  2h  Qualified small business stock (§1202 7% preference)          [RED-defer]
  2i  Exercise of incentive stock options (AMT income − regular)    [RED-defer]
  2j  Estates and trusts (Schedule K-1 (Form 1041) box 12 code A)   [RED-defer]
  2k  Disposition of property (AMT vs regular gain/loss difference) [RED-defer]
  2l  Depreciation on assets placed in service after 1986 (difference) [v1 IN]
  2m  Passive activities (difference)                               [RED-defer]
  2n  Loss limitations (difference)                                 [RED-defer]
  2o  Circulation costs                                             [RED-defer]
  2p  Long-term contracts                                           [RED-defer]
  2q  Mining costs                                                  [RED-defer]
  2r  Research and experimental costs                               [RED-defer]
  2s  Income from certain installment sales before 1/1/1987         [RED-defer]
  2t  Intangible drilling costs preference                          [RED-defer]
  3   Other adjustments, including income-based related adjustments [RED-defer]
  4   AMTI = combine lines 1b through 3 (MFS & line 4 > $900,350 → extra step)
Part II — Alternative Minimum Tax
  5   Exemption (year-keyed; phased out — worksheet below)
  6   L4 − L5 (if ≤ 0, enter 0 on 6/7/9/11 and go to L10)
  7   Tentative minimum tax: if L6 ≤ $239,100 ($119,550 MFS) → L6 × 26%;
      else L6 × 28% − $4,782 ($2,391 MFS).  If cap gains/qual div → Part III L40.
  8   Alternative minimum tax foreign tax credit                    [RED-defer]
  9   L7 − L8 (tentative minimum tax)
  10  Regular tax = 1040 L16 (− Form 4972) + Sch 2 L1z − Sch 3 L1 − Form 8978 neg
  11  AMT = max(0, L9 − L10) → Schedule 2 line 2
Part III — Tax Computation Using Maximum Capital Gains Rates (L12-40)
  The AMT version of the QDCGT / Schedule D Tax Worksheet — refigures the 0/15/20/
  25/28% capital-gains tax on the AMT base. Reuses the regular-tax QDCGT and SDTW
  amounts "as refigured for the AMT." 2025 0%-bracket $48,350 single/MFS / $96,700
  MFJ-QSS / $64,750 HOH; 15%-bracket $533,400 single / $300,000 MFS / $600,050
  MFJ-QSS / $566,700 HOH. (The app already implements QDCGT + SDTW — Topics 3/9 +
  Schedule J — so Part III reuses that machinery at the compute leg.)

Line 5 EXEMPTION WORKSHEET (phaseout):
  exemption = max(0, BASE − RATE × max(0, AMTI(L4) − THRESHOLD))
  2025: BASE 88,100 single/HOH | 137,000 MFJ-QSS | 68,500 MFS; THRESHOLD 626,350 |
        1,252,700 | 626,350; RATE 25%.
  2026 (OBBBA §70107): BASE 90,100 single | 140,200 MFJ | 70,100 MFS (½ MFJ, verify);
        THRESHOLD 500,000 single | 1,000,000 MFJ | 500,000 MFS; RATE 50%.

═══════════════════════════════════════════════════════════════════════════
requires_human_review WALK ITEMS (for Ken's in-session review)
═══════════════════════════════════════════════════════════════════════════
W1. AMTI BASE (line 1 / line 1b). Ken-confirmed 2026-06-23: the AMTI base =
    regular taxable income + the standard deduction (or Sch A line 7 SALT, if
    itemizing) added back + the OBBBA senior deduction (Sch 1-A) added back; the
    QBI deduction is RETAINED (AMT allows §199A). The form's 1a/1b reference 2025-
    renumbered 1040 lines (14 / 11b / 12e) that do NOT cleanly map to the app's
    seeded 1040 (app "14" = total deductions, "15" = taxable income). v1 models the
    base ECONOMICALLY from the app's quantities; the exact 1a/1b face mapping is
    pinned at the RENDER leg against the real 2025 1040 line numbers. CONFIRM the
    composition + that the senior deduction is disallowed for AMT (added back).
W2. 2026 OBBBA CONSTANTS (§70107). The exemption phaseout threshold reverts to
    $500,000 single / $1,000,000 MFJ (down from the TCJA-inflated $626,350 /
    $1,252,700) AND the phaseout rate rises 25% → 50%. The 2026 exemption amounts
    ($90,100 single / $140,200 MFJ) are RP 2025-32. CONFIRM: is $500k/$1M the exact
    2026 figure or a 2018-base indexed amount; the 2026 MFS exemption ($70,100 = ½
    MFJ, assumed); whether HOH 2026 threshold = $500,000.
W3. RED-DEFER ENUMERATION (no silent gap). v1 RED-defers ISO (2i), QSBS (2h),
    NOL/ATNOLD (2e/2f), estates/trusts (2j), the exotic preferences (2c/2d/2k/2m/2n/
    2o-2t/3), and the AMT foreign tax credit (line 8). Each fires a specific
    D_6251_* "prepare manually" RED and BLANKS line 11 (the engine never computes a
    wrong AMT silently). CONFIRM the scope split.
W4. PART III reuses the app's existing QDCGT + Schedule D Tax Worksheet machinery
    "as refigured for the AMT" (Topics 3/9 + Schedule J). The 25%/28% AMT-only
    branches (unrecaptured §1250 / 28%-rate gain) ride the SDTW path. CONFIRM the
    reuse; the AMT-basis-difference inputs (line 14 / AMT capital loss carryover)
    are RED-deferred in v1 (the same items 2k handles).
W5. LINE 10 REGULAR TAX = 1040 L16 (− Form 4972) + Sch 2 L1z − Sch 3 L1 − Form
    8978 negative. If Schedule J was used, refigure the regular tax WITHOUT Schedule
    J first (the app has `compute_regular_tax` from the Schedule J unit — reuse).
    CONFIRM the composition + the Schedule-J refigure.
W6. D_AMT_DEFER NARROWING. The existing presence-check RED narrows to the still-
    deferred preferences once the engine computes the common case (it currently
    fires on PAB / K-1-AMT — both of which v1 now handles or RED-defers granularly).
    The manual Schedule-2-line-2 escape hatch becomes the COMPUTED feed. CONFIRM.

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
# the verified constants both years, the cross-form flow map, the RED-defer
# enumeration). Until then the command writes nothing.
#
# FLIPPED 2026-06-23 — Ken APPROVED the review walk in-session ("approve and seed"):
# W1 AMTI base = regular taxable income + std-deduction/SALT add-back + senior-
# deduction add-back, QBI retained (senior deduction disallowed for AMT); W2 the
# 2026 OBBBA constants ($90,100/$140,200/$70,100 exemption; $500k/$1M phaseout @ 50%;
# $244,500 breakpoint) blessed as drafted; W3 RED-defer scope (ISO/QSBS/NOL/estates/
# exotic prefs/AMT-FTC) blessed; W4 Part III reuses the app QDCGT/SDTW; W5 line-10
# regular tax refigured without Schedule J; W6 D_AMT_DEFER narrows on compute. Math
# gate check_6251_integrity.py ALL PASS (constants both years + 10 scenarios re-derived).
# ═══════════════════════════════════════════════════════════════════════════
READY_TO_SEED = True


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1040"]


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS (every value cited; never training memory)
#   2025 — IRS i6251 / 2025 f6251.pdf / Rev. Proc. 2024-40.
#   2026 — Rev. Proc. 2025-32 (exemption amounts) + OBBBA §70107 (the phaseout
#          threshold reversion to $500k/$1M and the 25%→50% rate). W2.
# ═══════════════════════════════════════════════════════════════════════════

# AMT rate schedule — statutory §55(b)(1), NON-indexed. 28% applies above the
# breakpoint; the subtracted amount = breakpoint × (28% − 26%) = breakpoint × 0.02.
AMT_RATE_LOW = 0.26
AMT_RATE_HIGH = 0.28

# The 26%/28% breakpoint (line 7 / Part III line 18) — year-keyed (§55(b)(1)(A)
# inflation-adjusted). MFS = half. 2025 i6251: $239,100 / $119,550 MFS.
AMT_BREAKPOINT: dict[int, dict] = {
    2025: {"single": 239100, "mfj": 239100, "mfs": 119550},
    2026: {"single": 244500, "mfj": 244500, "mfs": 122250},  # RP 2025-32
}

# AMT exemption — year-keyed (§55(d), inflation-adjusted; OBBBA kept the TCJA
# amounts). single == HOH; MFJ == QSS.
AMT_EXEMPTION: dict[int, dict] = {
    2025: {"single": 88100, "mfj": 137000, "mfs": 68500},   # i6251 (RP 2024-40)
    2026: {"single": 90100, "mfj": 140200, "mfs": 70100},   # RP 2025-32 (MFS ½ MFJ — W2)
}

# Exemption phaseout START threshold — year-keyed. §55(d)(3). single == HOH.
# 2026 OBBBA §70107: reverts to $500k/$1M (down from the TCJA-inflated amounts). W2.
AMT_PHASEOUT_THRESHOLD: dict[int, dict] = {
    2025: {"single": 626350, "mfj": 1252700, "mfs": 626350},
    2026: {"single": 500000, "mfj": 1000000, "mfs": 500000},  # OBBBA §70107 — W2
}

# Exemption phaseout RATE — 2025 25% (TCJA); 2026 50% (OBBBA §70107). W2.
AMT_PHASEOUT_RATE: dict[int, float] = {2025: 0.25, 2026: 0.50}


def _status_key(filing_status: str) -> str:
    """AMT status key: MFJ/QSS share a column; MFS its own; single/HOH share
    (the AMT exemption, threshold, and 26/28 breakpoint are identical for single
    and HOH — only the Part III capital-gains breakpoints differ, handled there)."""
    if filing_status in ("mfj", "qss"):
        return "mfj"
    if filing_status == "mfs":
        return "mfs"
    return "single"  # single / hoh


def exemption_for(year: int, status: str) -> int:
    return (AMT_EXEMPTION.get(year) or AMT_EXEMPTION[2026])[_status_key(status)]


def phaseout_threshold_for(year: int, status: str) -> int:
    return (AMT_PHASEOUT_THRESHOLD.get(year) or AMT_PHASEOUT_THRESHOLD[2026])[_status_key(status)]


def phaseout_rate_for(year: int) -> float:
    return AMT_PHASEOUT_RATE.get(year) or AMT_PHASEOUT_RATE[2026]


def breakpoint_for(year: int, status: str) -> int:
    return (AMT_BREAKPOINT.get(year) or AMT_BREAKPOINT[2026])[_status_key(status)]


def amt_exemption_amount(year: int, status: str, amti: float) -> float:
    """Line 5 exemption worksheet: base − rate × max(0, AMTI − threshold), floored 0."""
    base = exemption_for(year, status)
    over = max(0.0, amti - phaseout_threshold_for(year, status))
    return max(0.0, base - phaseout_rate_for(year) * over)


def tentative_minimum_tax_ordinary(year: int, status: str, taxable_excess: float) -> float:
    """Line 7 (no capital gains): 26% up to the breakpoint, else 28% − (breakpoint × 2%)."""
    bp = breakpoint_for(year, status)
    if taxable_excess <= bp:
        return taxable_excess * AMT_RATE_LOW
    return taxable_excess * AMT_RATE_HIGH - bp * (AMT_RATE_HIGH - AMT_RATE_LOW)


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY TOPICS
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("alternative_minimum_tax", "Form 6251 — Alternative Minimum Tax (individuals): AMTI, exemption phaseout, 26/28% TMT, AMT capital gains"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "RP_2025_32",          # 2026 exemption amounts + the 2026 cap-gains breakpoints
    "IRS_2025_1040_FORM",  # the 1040/Sch 2 cross-form lines
]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY SOURCES (CREATE) — transcribed 2026-06-23 from the on-disk
# resources/irs_forms/2025/f6251.pdf (read directly via pymupdf) + i6251 +
# IRC §55-59 + OBBBA §70107. requires_human_review = the W-items in the docstring.
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_6251_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "2025 Form 6251 — Alternative Minimum Tax—Individuals",
        "citation": "Form 6251 (2025); f6251.pdf; Attachment Sequence No. 32",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f6251.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["alternative_minimum_tax"],
        "excerpts": [
            {
                "excerpt_label": "Form 6251 Part I–II (2025) — verified line face",
                "excerpt_text": (
                    "Part I: 1a = Form 1040 line 14 − Schedule 1-A line 37; 1b = Form 1040 line 11b − line 1a "
                    "(if < 0, negative); 2a = Sch A line 7 taxes (or, if not itemizing, the standard deduction from "
                    "1040 line 12e); 2b tax refund (Sch 1 line 1/8z, subtract); 2c investment interest; 2d depletion; "
                    "2e NOL (Sch 1 line 8a, positive); 2f ATNOLD (subtract); 2g specified private activity bond "
                    "interest; 2h QSBS; 2i ISO exercise; 2j estates/trusts (K-1 1041 box 12 code A); 2k disposition; "
                    "2l post-1986 depreciation; 2m passive; 2n loss limitations; 2o circulation; 2p long-term "
                    "contracts; 2q mining; 2r R&E; 2s pre-1987 installment sales; 2t IDC preference; 3 other "
                    "adjustments; 4 AMTI = combine 1b–3. Part II: 5 exemption (phased out); 6 = L4 − L5; 7 TMT "
                    "(26% if L6 ≤ 239,100/119,550 MFS, else 28% − 4,782/2,391; or Part III L40 for capital gains); "
                    "8 AMT foreign tax credit; 9 = L7 − L8; 10 regular tax (1040 L16 − Form 4972 + Sch 2 L1z − Sch 3 "
                    "L1 − Form 8978 neg); 11 AMT = max(0, L9 − L10) → Schedule 2 line 2."
                ),
                "summary_text": "Form 6251 Part I–II: AMTI add-backs → exemption → 26/28% TMT → AMT = TMT − regular tax → Sch 2 L2.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Line 5 exemption worksheet + Part III trigger (2025)",
                "excerpt_text": (
                    "Exemption worksheet: line 1 base (88,100 single/HOH; 137,000 MFJ-QSS; 68,500 MFS); line 2 AMTI "
                    "(L4); line 3 threshold (626,350 single/HOH/MFS; 1,252,700 MFJ-QSS); line 4 = L2 − L3 (≥0); "
                    "line 5 = L4 × 25%; line 6 = base − L5 (≥0) → exemption. Part III (Tax Computation Using Maximum "
                    "Capital Gains Rates) is completed only if required by line 7 — i.e. an AMT gain/loss basis "
                    "difference, 1040 line 15 = 0, a 1041 K-1 box-12 code B-F, or capital gain distributions / "
                    "qualified dividends / a gain on both Schedule D lines 15 and 16. Part III refigures the 0/15/20/"
                    "25/28% capital-gains tax on the AMT base (2025 0%-bracket 48,350 single-MFS / 96,700 MFJ-QSS / "
                    "64,750 HOH; 15%-bracket 533,400 single / 300,000 MFS / 600,050 MFJ-QSS / 566,700 HOH)."
                ),
                "summary_text": "Exemption = base − 25%×(AMTI − threshold). Part III = the AMT capital-gains worksheet (0/15/20/25/28%).",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_6251_INSTR",
        "source_type": "official_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "2025 Instructions for Form 6251 — Alternative Minimum Tax—Individuals",
        "citation": "Instructions for Form 6251 (2025)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/instructions/i6251",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["alternative_minimum_tax"],
        "excerpts": [
            {
                "excerpt_label": "Line 1 (AMTI base) + line 2a (taxes) — 2025 redesign",
                "excerpt_text": (
                    "Line 1a: subtract Schedule 1-A line 37 from Form 1040 line 14. Line 1b: subtract line 1a from "
                    "Form 1040 line 11b (the standard deduction); if less than zero enter as a negative amount. The "
                    "net effect restores the AMT base: AMT does not allow the standard deduction (added back) and "
                    "removes the new enhanced senior deduction (Schedule 1-A line 37), while the QBI deduction is "
                    "retained for the AMT. Line 2a: if filing Schedule A, enter the taxes from Schedule A line 7 "
                    "(except GST taxes on income distributions); if not itemizing, enter the standard deduction "
                    "amount (1040 line 12e). The standard deduction and the deducted state/local taxes are the most "
                    "common AMT add-backs."
                ),
                "summary_text": "AMTI base = taxable income + std-deduction/SALT add-back + senior-deduction add-back; QBI retained.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Line 7 TMT + line 10 regular tax",
                "excerpt_text": (
                    "Line 7: if line 6 is $239,100 or less ($119,550 MFS), multiply by 26%; otherwise multiply by 28% "
                    "and subtract $4,782 ($2,391 MFS). If you have capital gain distributions, qualified dividends, or "
                    "a net capital gain, complete Part III and enter the amount from line 40. Line 10: add Form 1040 "
                    "line 16 (minus any Form 4972 tax) and Schedule 2 line 1z; subtract Schedule 3 line 1 and any "
                    "negative Form 8978 line 14; if zero or less enter -0-. If you filed Schedule J, refigure the "
                    "regular tax without Schedule J before completing line 10."
                ),
                "summary_text": "TMT = 26/28% of the taxable excess (Part III for cap gains). Regular tax (L10) excludes Schedule J.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_55_59",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "IRC §§55–59 — Alternative Minimum Tax",
        "citation": "26 U.S.C. §§55–59 (§55 imposition + rates; §56 adjustments; §57 preferences; §58 limitations; §59 other)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/55",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 10.0,
        "topics": ["alternative_minimum_tax"],
        "excerpts": [
            {
                "excerpt_label": "§55 — AMT imposition + 26/28% rate; §56(b) standard-deduction add-back",
                "excerpt_text": (
                    "§55(a): the AMT is the excess of the tentative minimum tax over the regular tax. §55(b)(1)(A): "
                    "the tentative minimum tax is 26% of so much of the taxable excess as does not exceed $175,000 "
                    "(inflation-adjusted to $239,100 for 2025), plus 28% of the remainder. §55(d): the exemption "
                    "amount, reduced by 25% of the amount by which AMTI exceeds the phaseout threshold. §56(b)(1): in "
                    "computing AMTI, no deduction is allowed for the standard deduction or for state and local taxes; "
                    "the QBI deduction under §199A is allowed."
                ),
                "summary_text": "§55: AMT = TMT − regular tax; 26/28%; exemption phaseout. §56(b): no standard deduction / no SALT for AMT.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "OBBBA_70107",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "One Big Beautiful Bill Act §70107 — AMT exemption phaseout (effective 2026)",
        "citation": "P.L. 119-21 §70107 (2025); amending IRC §55(d)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.congress.gov/bill/119th-congress/house-bill/1",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 10.0,
        "topics": ["alternative_minimum_tax"],
        "excerpts": [
            {
                "excerpt_label": "OBBBA §70107 — 2026 phaseout reversion + 50% rate (requires_human_review W2)",
                "excerpt_text": (
                    "Effective for taxable years beginning after December 31, 2025, the AMT exemption phaseout "
                    "threshold reverts to $500,000 (unmarried) / $1,000,000 (married filing jointly) — down from the "
                    "TCJA-inflated 2025 amounts of $626,350 / $1,252,700 — and the phaseout rate increases from 25% to "
                    "50%. The exemption amounts (kept at the TCJA levels, inflation-adjusted: $90,100 single / $140,200 "
                    "MFJ for 2026 per Rev. Proc. 2025-32) are unchanged in structure. REQUIRES HUMAN REVIEW: confirm "
                    "whether $500,000/$1,000,000 is the fixed 2026 figure or a 2018-base indexed amount, the 2026 MFS "
                    "exemption ($70,100 assumed = ½ MFJ), and the 2026 HOH threshold."
                ),
                "summary_text": "OBBBA 2026: phaseout threshold → $500k/$1M, rate 25%→50%. Verify exact figures (W2).",
                "is_key_excerpt": True,
            },
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = [
    ("RP_2025_32", {
        "excerpt_label": "§3.10 AMT exemption + phaseout (TY2026, verbatim-pending — W2)",
        "excerpt_text": (
            "For taxable years beginning in 2026, the AMT exemption amount is $90,100 for unmarried individuals "
            "(other than surviving spouses) and $140,200 for married individuals filing jointly and surviving "
            "spouses; $70,100 for married filing separately. The exemption phases out (per OBBBA §70107) beginning at "
            "$500,000 (unmarried) / $1,000,000 (MFJ) at a 50% rate. The 28% AMT rate begins at $244,500 of taxable "
            "excess ($122,250 MFS). [Cross-check the exact §3.10 amounts against the published Rev. Proc. 2025-32 "
            "at the review walk — W2.]"
        ),
        "summary_text": "TY2026 AMT: exemption $90,100/$140,200; phaseout $500k/$1M @ 50% (OBBBA); 28% at $244,500.",
        "is_key_excerpt": True,
    }),
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_6251_FORM", "6251", "defines"),
    ("IRC_55_59", "6251", "supports"),
    ("OBBBA_70107", "6251", "modifies"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 6251 — FACTS
# ═══════════════════════════════════════════════════════════════════════════

F6251_FACTS: list[dict] = [
    # ── Return-level inputs (sourced from the 1040 / schedules) ──
    {"fact_key": "a_taxable_income", "label": "Line 1 source — regular taxable income (1040 line 15)",
     "data_type": "decimal", "default_value": "0", "sort_order": 1,
     "notes": ("RETURN LEVEL. The regular-tax taxable income (app 1040 line 15). The AMTI base (line 1b) adds back "
               "the standard deduction (or SALT, line 2a) and the OBBBA senior deduction, and retains QBI. "
               "requires_human_review W1: the exact 1a/1b 1040-line mapping is pinned at the render leg.")},
    {"fact_key": "a_itemizing", "label": "Itemizing? (Schedule A filed)", "data_type": "boolean", "sort_order": 2,
     "notes": "RETURN LEVEL. Drives line 2a: True → add back Sch A line 7 SALT; False → add back the standard deduction (1040 line 12e)."},
    {"fact_key": "a_salt_deduction", "label": "Line 2a (itemizer) — taxes from Schedule A line 7",
     "data_type": "decimal", "default_value": "0", "sort_order": 3,
     "notes": "RETURN LEVEL. State/local income (or sales) + real-estate + personal-property taxes, except GST on income distributions. Added back for AMT (§56(b)(1))."},
    {"fact_key": "a_standard_deduction", "label": "Line 2a (non-itemizer) — standard deduction (1040 line 12e)",
     "data_type": "decimal", "default_value": "0", "sort_order": 4,
     "notes": "RETURN LEVEL. The standard deduction is disallowed for AMT (§56(b)(1)) → added back on line 2a for non-itemizers."},
    {"fact_key": "a_senior_deduction", "label": "Line 1a — OBBBA senior deduction (Schedule 1-A line 37)",
     "data_type": "decimal", "default_value": "0", "sort_order": 5,
     "notes": "RETURN LEVEL. The new enhanced senior deduction is removed from the AMT base (line 1a). Ken-confirmed disallowed for AMT (W1)."},
    {"fact_key": "a_tax_refund", "label": "Line 2b — taxable state tax refund (Schedule 1 line 1/8z)",
     "data_type": "decimal", "default_value": "0", "sort_order": 6,
     "notes": "RETURN LEVEL. A refund of taxes added back is subtracted for AMT (line 2b, negative)."},
    {"fact_key": "a_pab_interest", "label": "Line 2g — specified private activity bond interest",
     "data_type": "decimal", "default_value": "0", "sort_order": 7,
     "notes": "RETURN LEVEL. §57(a)(5). Tax-exempt for regular tax but an AMT preference. The app already tracks pab_interest (1099-INT box 9 / 1099-DIV box 13)."},
    {"fact_key": "a_amt_depreciation_adj", "label": "Line 2l — post-1986 depreciation difference (regular − AMT)",
     "data_type": "decimal", "default_value": "0", "sort_order": 8,
     "notes": "RETURN LEVEL. §56(a)(1). The excess of regular MACRS over AMT depreciation (150% DB / longer life). The depreciation engine carries the AMT adjustment (entity side; reused at the 1040 level)."},
    {"fact_key": "a_net_capital_gain", "label": "Part III — net capital gain + qualified dividends (for the AMT cap-gains worksheet)",
     "data_type": "decimal", "default_value": "0", "sort_order": 9,
     "notes": "RETURN LEVEL. Triggers Part III; the 0/15/20/25/28% rates are refigured on the AMT base. Reuses the QDCGT/SDTW inputs (Topics 3/9)."},
    {"fact_key": "a_regular_tax_for_amt", "label": "Line 10 — regular tax for the AMT comparison",
     "data_type": "decimal", "default_value": "0", "sort_order": 10,
     "notes": "RETURN LEVEL. 1040 L16 (− Form 4972) + Sch 2 L1z − Sch 3 L1 − Form 8978 neg; refigured WITHOUT Schedule J if used. Reuse `compute_regular_tax` (the Schedule J unit)."},
    {"fact_key": "a_filing_status", "label": "Filing status (selects exemption / threshold / breakpoint)",
     "data_type": "string", "sort_order": 11,
     "notes": "RETURN LEVEL. mfj|qss → mfj column; mfs → mfs; single|hoh → single (the AMT exemption/threshold/26-28 breakpoint are equal for single and HOH; Part III cap-gains breakpoints differ for HOH)."},
    # ── RED-deferred preference indicators (presence flags → D_6251_* no silent gap) ──
    {"fact_key": "a_iso_exercise", "label": "Line 2i — incentive stock option exercise (RED-defer)",
     "data_type": "decimal", "default_value": "0", "sort_order": 20,
     "notes": "RETURN LEVEL. The classic AMT trap. Needs ISO-basis tracking (not modeled v1) → D_6251_001 RED-defer."},
    {"fact_key": "a_qsbs_preference", "label": "Line 2h — §1202 qualified small business stock (RED-defer)",
     "data_type": "decimal", "default_value": "0", "sort_order": 21,
     "notes": "RETURN LEVEL. 7% of the excluded §1202 gain is an AMT preference → D_6251_002 RED-defer."},
    {"fact_key": "a_amt_nol", "label": "Lines 2e/2f — NOL / alternative-tax NOL (RED-defer)",
     "data_type": "decimal", "default_value": "0", "sort_order": 22,
     "notes": "RETURN LEVEL. The AMT NOL (ATNOLD, 90% limit) is not modeled v1 → D_6251_003 RED-defer."},
    {"fact_key": "a_estate_trust_amt", "label": "Line 2j — estates/trusts AMT (K-1 1041 box 12 code A) (RED-defer)",
     "data_type": "decimal", "default_value": "0", "sort_order": 23,
     "notes": "RETURN LEVEL. Pass-through AMT adjustment from a 1041 K-1 → D_6251_004 RED-defer."},
    {"fact_key": "a_other_amt_preference", "label": "Lines 2c/2d/2k/2m/2n/2o-2t/3 — other AMT preferences (RED-defer)",
     "data_type": "decimal", "default_value": "0", "sort_order": 24,
     "notes": "RETURN LEVEL. Investment interest / depletion / disposition / passive / loss-limit / circulation / contracts / mining / R&E / installment / IDC / other → D_6251_005 RED-defer."},
    {"fact_key": "a_amt_ftc", "label": "Line 8 — AMT foreign tax credit (RED-defer)",
     "data_type": "decimal", "default_value": "0", "sort_order": 25,
     "notes": "RETURN LEVEL. Needs a Form 1116 AMT variant (not built) → D_6251_006 RED-defer; v1 line 8 = 0."},
    # ── Outputs ──
    {"fact_key": "a_amti_l4", "label": "Line 4 — alternative minimum taxable income (output)",
     "data_type": "decimal", "sort_order": 40,
     "notes": "OUTPUT. = line 1b + 2a + 2b + 2g + 2l (+ RED-deferred items when supported). The AMT base."},
    {"fact_key": "a_exemption_l5", "label": "Line 5 — AMT exemption after phaseout (output)",
     "data_type": "decimal", "sort_order": 41,
     "notes": "OUTPUT. = max(0, base − rate × max(0, AMTI − threshold)). Year-keyed (2026 OBBBA 50% rate)."},
    {"fact_key": "a_tmt_l9", "label": "Line 9 — tentative minimum tax (output)",
     "data_type": "decimal", "sort_order": 42,
     "notes": "OUTPUT. = line 7 (26/28% of taxable excess, or Part III line 40) − line 8 (AMT FTC, v1 = 0)."},
    {"fact_key": "a_amt_l11", "label": "Line 11 — alternative minimum tax (output → Schedule 2 line 2)",
     "data_type": "decimal", "sort_order": 43,
     "notes": "OUTPUT. = max(0, line 9 − line 10). Feeds Schedule 2 line 2 → 1040 line 17 → total tax. Replaces the D_AMT_DEFER manual escape hatch."},
    # ── Constants ──
    {"fact_key": "a_amt_rates", "label": "AMT rates 26% / 28% — statutory §55(b)(1) non-indexed",
     "data_type": "decimal", "sort_order": 50, "notes": "CONSTANT 0.26 / 0.28. Same both years; breakpoint year-keyed."},
    {"fact_key": "a_amt_breakpoint", "label": "26%/28% breakpoint (YEAR-KEYED)", "data_type": "decimal", "sort_order": 51,
     "notes": "CONSTANT: 2025 $239,100 ($119,550 MFS); 2026 $244,500 ($122,250 MFS). 28% subtract = breakpoint × 2%."},
    {"fact_key": "a_amt_exemption_const", "label": "AMT exemption (YEAR-KEYED + status)", "data_type": "decimal", "sort_order": 52,
     "notes": "CONSTANT: 2025 88,100 single/HOH / 137,000 MFJ / 68,500 MFS; 2026 90,100 / 140,200 / 70,100 (W2)."},
    {"fact_key": "a_amt_phaseout", "label": "Exemption phaseout threshold + rate (YEAR-KEYED — OBBBA 2026)", "data_type": "decimal", "sort_order": 53,
     "notes": "CONSTANT: 2025 threshold 626,350/1,252,700 @ 25%; 2026 threshold 500,000/1,000,000 @ 50% (OBBBA §70107 — W2)."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 6251 — RULES
# ═══════════════════════════════════════════════════════════════════════════

F6251_RULES: list[dict] = [
    {"rule_id": "R-6251-SCOPE", "title": "Scope gate — Form 6251 engaged (AMT may apply)", "rule_type": "routing", "precedence": 0, "sort_order": 1,
     "formula": ("Form 6251 is computed when the return carries an AMT add-back/preference OR the tentative minimum "
                 "tax could exceed the regular tax. A clean return with no add-backs and TMT ≤ regular tax → AMT = 0 "
                 "(line 11). The presence-check D_AMT_DEFER narrows to the still-deferred preferences."),
     "inputs": ["a_taxable_income", "a_pab_interest", "a_amt_depreciation_adj", "a_salt_deduction", "a_standard_deduction"], "outputs": [],
     "description": "RETURN LEVEL. The common case: most returns compute AMT = 0 (the exemption covers the std-deduction add-back). The engine still proves it."},
    {"rule_id": "R-6251-L1-BASE", "title": "Line 1 — AMTI base (std-deduction/SALT/senior add-back; QBI retained)", "rule_type": "calculation", "precedence": 1, "sort_order": 2,
     "formula": ("AMTI base (line 1b) = regular taxable income (1040 L15) + the standard deduction (or, if itemizing, "
                 "the Sch A line 7 SALT — added on line 2a) + the OBBBA senior deduction (Sch 1-A, removed on line 1a) "
                 "with the §199A QBI deduction RETAINED. §56(b)(1): no standard deduction / no SALT for AMT; QBI "
                 "allowed. Modeled economically from the app's quantities; the 1a/1b face mapping is pinned at render (W1)."),
     "inputs": ["a_taxable_income", "a_standard_deduction", "a_salt_deduction", "a_senior_deduction", "a_itemizing"], "outputs": ["1a", "1b"],
     "description": "RETURN LEVEL. The AMTI starting base. Ken-confirmed composition 2026-06-23 (W1)."},
    {"rule_id": "R-6251-2A-TAXES", "title": "Line 2a — taxes add-back (SALT or standard deduction)", "rule_type": "calculation", "precedence": 2, "sort_order": 3,
     "formula": "If itemizing: line 2a = Sch A line 7 SALT (a_salt_deduction). Else: line 2a = the standard deduction (a_standard_deduction). §56(b)(1).",
     "inputs": ["a_itemizing", "a_salt_deduction", "a_standard_deduction"], "outputs": ["2a"],
     "description": "RETURN LEVEL. The most common AMT add-back. v1 IN."},
    {"rule_id": "R-6251-2B-REFUND", "title": "Line 2b — taxable tax refund (subtract)", "rule_type": "calculation", "precedence": 3, "sort_order": 4,
     "formula": "Line 2b = − a_tax_refund (a refund of taxes added back is removed from AMTI).",
     "inputs": ["a_tax_refund"], "outputs": ["2b"],
     "description": "RETURN LEVEL. v1 IN. The Schedule 1 line 1/8z taxable refund is subtracted for AMT."},
    {"rule_id": "R-6251-2G-PAB", "title": "Line 2g — specified private activity bond interest", "rule_type": "calculation", "precedence": 4, "sort_order": 5,
     "formula": "Line 2g = a_pab_interest (§57(a)(5)). Tax-exempt for regular tax; an AMT preference.",
     "inputs": ["a_pab_interest"], "outputs": ["2g"],
     "description": "RETURN LEVEL. v1 IN. The app already tracks pab_interest (1099-INT box 9 / 1099-DIV box 13)."},
    {"rule_id": "R-6251-2L-DEPR", "title": "Line 2l — post-1986 depreciation difference", "rule_type": "calculation", "precedence": 5, "sort_order": 6,
     "formula": "Line 2l = a_amt_depreciation_adj = (regular MACRS depreciation) − (AMT depreciation). §56(a)(1).",
     "inputs": ["a_amt_depreciation_adj"], "outputs": ["2l"],
     "description": "RETURN LEVEL. v1 IN. The depreciation engine carries the AMT adjustment (Ken's specialty)."},
    {"rule_id": "R-6251-L4-AMTI", "title": "Line 4 — AMTI = combine 1b through 3", "rule_type": "calculation", "precedence": 6, "sort_order": 7,
     "formula": "Line 4 = line 1b + 2a + 2b + 2g + 2l (+ any supported additional add-backs). The AMT base.",
     "inputs": [], "outputs": ["4"],
     "description": "RETURN LEVEL. The total AMTI. RED-deferred preferences blank line 11 (no silent gap), so they never silently drop out of line 4."},
    {"rule_id": "R-6251-L5-EXEMPTION", "title": "Line 5 — exemption with phaseout (year-keyed; OBBBA 2026)", "rule_type": "calculation", "precedence": 7, "sort_order": 8,
     "formula": ("Line 5 = max(0, BASE − RATE × max(0, AMTI(L4) − THRESHOLD)). 2025: BASE 88,100/137,000/68,500, "
                 "THRESHOLD 626,350/1,252,700/626,350, RATE 25%. 2026 (OBBBA §70107): BASE 90,100/140,200/70,100, "
                 "THRESHOLD 500,000/1,000,000/500,000, RATE 50%."),
     "inputs": ["a_amti_l4", "a_filing_status", "a_amt_exemption_const", "a_amt_phaseout"], "outputs": ["5"],
     "description": "RETURN LEVEL. §55(d). The exemption phases out 25¢ (2026: 50¢) per $1 of AMTI over the threshold."},
    {"rule_id": "R-6251-L6", "title": "Line 6 — taxable excess", "rule_type": "calculation", "precedence": 8, "sort_order": 9,
     "formula": "Line 6 = max(0, line 4 − line 5). If ≤ 0, enter 0 on lines 6/7/9/11 and go to line 10 (no AMT).",
     "inputs": [], "outputs": ["6"],
     "description": "RETURN LEVEL. The AMT base above the exemption."},
    {"rule_id": "R-6251-L7-TMT", "title": "Line 7 — tentative minimum tax (26/28% or Part III)", "rule_type": "calculation", "precedence": 9, "sort_order": 10,
     "formula": ("If no net capital gain / qualified dividends: line 7 = (line 6 × 26%) if line 6 ≤ breakpoint "
                 "($239,100 / $119,550 MFS for 2025; $244,500 / $122,250 for 2026) else (line 6 × 28% − breakpoint × "
                 "2%). If capital gains present → complete Part III and enter line 40."),
     "inputs": ["a_amti_l4", "a_net_capital_gain", "a_amt_breakpoint", "a_amt_rates", "a_filing_status"], "outputs": ["7"],
     "description": "RETURN LEVEL. §55(b)(1). The 26/28% rate schedule; the AMT capital-gains worksheet for preferential-rate income."},
    {"rule_id": "R-6251-P3-CAPGAINS", "title": "Part III lines 12-40 — AMT capital-gains worksheet", "rule_type": "calculation", "precedence": 10, "sort_order": 11,
     "formula": ("Refigure the 0/15/20/25/28% capital-gains tax on the AMT base, reusing the regular QDCGT / Schedule "
                 "D Tax Worksheet amounts 'as refigured for the AMT'. 2025 0%-bracket 48,350 single-MFS / 96,700 "
                 "MFJ-QSS / 64,750 HOH; 15%-bracket 533,400 single / 300,000 MFS / 600,050 MFJ-QSS / 566,700 HOH. "
                 "Line 40 → line 7. The app reuses its existing QDCGT + SDTW machinery (Topics 3/9 + Schedule J)."),
     "inputs": ["a_amti_l4", "a_net_capital_gain", "a_filing_status"], "outputs": ["12", "18", "31", "34", "37", "38", "40"],
     "description": "RETURN LEVEL. The AMT version of the cap-gains worksheet. AMT-basis-difference inputs (line 14) are RED-deferred (W4)."},
    {"rule_id": "R-6251-L10-REGTAX", "title": "Line 10 — regular tax for the AMT comparison", "rule_type": "calculation", "precedence": 11, "sort_order": 12,
     "formula": ("Line 10 = 1040 L16 (− Form 4972) + Sch 2 L1z − Sch 3 L1 − (negative Form 8978 L14); if ≤ 0, enter 0. "
                 "If Schedule J was used, refigure the regular tax WITHOUT Schedule J first (reuse compute_regular_tax)."),
     "inputs": ["a_regular_tax_for_amt"], "outputs": ["10"],
     "description": "RETURN LEVEL. The regular tax the AMT is compared against (W5)."},
    {"rule_id": "R-6251-L11-AMT", "title": "Line 11 — AMT = max(0, TMT − regular tax) → Schedule 2 line 2", "rule_type": "calculation", "precedence": 12, "sort_order": 13,
     "formula": "Line 9 = line 7 − line 8 (AMT FTC, v1 = 0). Line 11 = max(0, line 9 − line 10) → Schedule 2 line 2 → 1040 line 17.",
     "inputs": ["a_tmt_l9", "a_regular_tax_for_amt"], "outputs": ["9", "11"],
     "description": "RETURN LEVEL. §55(a). The AMT is the EXCESS of the tentative minimum tax over the regular tax. Replaces the D_AMT_DEFER manual entry."},
    {"rule_id": "R-6251-DEFER", "title": "RED-defer — unsupported preferences blank line 11 (no silent gap)", "rule_type": "routing", "precedence": 13, "sort_order": 14,
     "formula": ("If any RED-deferred item is present — ISO (2i), QSBS (2h), NOL (2e/2f), estates/trusts (2j), the "
                 "other preferences (2c/2d/2k/2m/2n/2o-2t/3), or an AMT foreign tax credit (line 8) — the engine "
                 "CANNOT compute a correct AMT → fire the specific D_6251_* RED and BLANK line 11 (the preparer "
                 "figures Form 6251 manually and enters it on Schedule 2 line 2). Never a silently-wrong number."),
     "inputs": ["a_iso_exercise", "a_qsbs_preference", "a_amt_nol", "a_estate_trust_amt", "a_other_amt_preference", "a_amt_ftc"], "outputs": ["8", "11"],
     "description": "RETURN LEVEL. The no-silent-gap guard (SPRINT quality rule 2). The common case computes; the exotic preferences RED-defer."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 6251 — LINES (main-form lines exact, read from the 2025 f6251.pdf)
# ═══════════════════════════════════════════════════════════════════════════

F6251_LINES: list[dict] = [
    {"line_number": "1a", "description": "Subtract Schedule 1-A (Form 1040) line 37 from Form 1040 line 14", "line_type": "calculated"},
    {"line_number": "1b", "description": "Subtract line 1a from Form 1040 line 11b (AMTI base; if < 0, negative)", "line_type": "calculated"},
    {"line_number": "2a", "description": "Taxes — Sch A line 7 (itemizer) or the standard deduction (line 12e)", "line_type": "input"},
    {"line_number": "2b", "description": "Tax refund from Schedule 1 line 1 or 8z (subtract)", "line_type": "input"},
    {"line_number": "2c", "description": "Investment interest expense (reg vs AMT) — RED-defer", "line_type": "input"},
    {"line_number": "2d", "description": "Depletion (difference) — RED-defer", "line_type": "input"},
    {"line_number": "2e", "description": "Net operating loss deduction (Sch 1 line 8a, positive) — RED-defer", "line_type": "input"},
    {"line_number": "2f", "description": "Alternative tax net operating loss deduction (subtract) — RED-defer", "line_type": "input"},
    {"line_number": "2g", "description": "Interest from specified private activity bonds", "line_type": "input"},
    {"line_number": "2h", "description": "Qualified small business stock (§1202) — RED-defer", "line_type": "input"},
    {"line_number": "2i", "description": "Exercise of incentive stock options — RED-defer", "line_type": "input"},
    {"line_number": "2j", "description": "Estates and trusts (K-1 (1041) box 12 code A) — RED-defer", "line_type": "input"},
    {"line_number": "2k", "description": "Disposition of property (AMT vs regular) — RED-defer", "line_type": "input"},
    {"line_number": "2l", "description": "Depreciation on assets placed in service after 1986 (difference)", "line_type": "input"},
    {"line_number": "2m", "description": "Passive activities (difference) — RED-defer", "line_type": "input"},
    {"line_number": "2n", "description": "Loss limitations (difference) — RED-defer", "line_type": "input"},
    {"line_number": "2o", "description": "Circulation costs (difference) — RED-defer", "line_type": "input"},
    {"line_number": "2p", "description": "Long-term contracts (difference) — RED-defer", "line_type": "input"},
    {"line_number": "2q", "description": "Mining costs (difference) — RED-defer", "line_type": "input"},
    {"line_number": "2r", "description": "Research and experimental costs (difference) — RED-defer", "line_type": "input"},
    {"line_number": "2s", "description": "Income from certain installment sales before 1/1/1987 — RED-defer", "line_type": "input"},
    {"line_number": "2t", "description": "Intangible drilling costs preference — RED-defer", "line_type": "input"},
    {"line_number": "3", "description": "Other adjustments, including income-based related adjustments — RED-defer", "line_type": "input"},
    {"line_number": "4", "description": "Alternative minimum taxable income = combine lines 1b through 3", "line_type": "calculated"},
    {"line_number": "5", "description": "Exemption (year-keyed; phased out per the line-5 worksheet)", "line_type": "calculated"},
    {"line_number": "6", "description": "Subtract line 5 from line 4 (if ≤ 0, enter 0; no AMT)", "line_type": "calculated"},
    {"line_number": "7", "description": "Tentative minimum tax — 26/28% of line 6 (or Part III line 40)", "line_type": "calculated"},
    {"line_number": "8", "description": "Alternative minimum tax foreign tax credit — RED-defer (v1 = 0)", "line_type": "input"},
    {"line_number": "9", "description": "Tentative minimum tax = line 7 − line 8", "line_type": "calculated"},
    {"line_number": "10", "description": "Regular tax (1040 L16 − 4972 + Sch 2 L1z − Sch 3 L1 − 8978 neg; no Schedule J)", "line_type": "calculated"},
    {"line_number": "11", "description": "Alternative minimum tax = max(0, line 9 − line 10) → Schedule 2 line 2", "line_type": "total"},
    # Part III (AMT capital-gains worksheet — main lines; full 12-40 chain at compute)
    {"line_number": "12", "description": "Part III — amount from line 6 (AMT taxable excess)", "line_type": "calculated"},
    {"line_number": "18", "description": "Part III — 26/28% tax on the non-cap-gain portion (line 17)", "line_type": "calculated"},
    {"line_number": "31", "description": "Part III — 15% capital-gains tax (line 30 × 15%)", "line_type": "calculated"},
    {"line_number": "34", "description": "Part III — 20% capital-gains tax (line 33 × 20%)", "line_type": "calculated"},
    {"line_number": "37", "description": "Part III — 25% unrecaptured §1250 tax (line 36 × 25%)", "line_type": "calculated"},
    {"line_number": "38", "description": "Part III — add lines 18, 31, 34, and 37", "line_type": "calculated"},
    {"line_number": "40", "description": "Part III — tentative minimum tax (smaller of line 38 or 39) → line 7", "line_type": "calculated"},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 6251 — DIAGNOSTICS
# ═══════════════════════════════════════════════════════════════════════════

F6251_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_6251_001", "title": "Incentive stock option exercise — AMT not computed (prepare manually)", "severity": "error",
     "condition": "a_iso_exercise present (line 2i)",
     "message": ("Not supported — prepare manually: this return has an incentive stock option (ISO) exercise (Form "
                 "6251 line 2i), the classic AMT adjustment. It requires tracking the AMT basis of the ISO stock, "
                 "which is not built this version. Figure Form 6251 manually and enter the AMT on Schedule 2 line 2."),
     "notes": "RED-defer 2i. ISO needs AMT-basis tracking."},
    {"diagnostic_id": "D_6251_002", "title": "Qualified small business stock preference — not computed", "severity": "error",
     "condition": "a_qsbs_preference present (line 2h)",
     "message": ("Not supported — prepare manually: a §1202 qualified small business stock AMT preference (Form 6251 "
                 "line 2h, 7% of the excluded gain) is present and is not computed this version. Figure Form 6251 "
                 "manually and enter the AMT on Schedule 2 line 2."),
     "notes": "RED-defer 2h."},
    {"diagnostic_id": "D_6251_003", "title": "AMT net operating loss — not computed", "severity": "error",
     "condition": "a_amt_nol present (lines 2e/2f)",
     "message": ("Not supported — prepare manually: an NOL deduction / alternative-tax NOL deduction (Form 6251 lines "
                 "2e/2f) is present. The AMT NOL (90% limitation) is not computed this version. Figure Form 6251 "
                 "manually and enter the AMT on Schedule 2 line 2."),
     "notes": "RED-defer 2e/2f."},
    {"diagnostic_id": "D_6251_004", "title": "Estate/trust AMT pass-through (K-1) — not computed", "severity": "error",
     "condition": "a_estate_trust_amt present (line 2j)",
     "message": ("Not supported — prepare manually: an estate/trust AMT adjustment from a Schedule K-1 (Form 1041) "
                 "box 12 code A (Form 6251 line 2j) is present and is not computed this version. Figure Form 6251 "
                 "manually and enter the AMT on Schedule 2 line 2."),
     "notes": "RED-defer 2j."},
    {"diagnostic_id": "D_6251_005", "title": "Other AMT preference present — not computed", "severity": "error",
     "condition": "a_other_amt_preference present (lines 2c/2d/2k/2m/2n/2o-2t/3)",
     "message": ("Not supported — prepare manually: an AMT preference/adjustment that is not built this version is "
                 "present (investment interest, depletion, disposition, passive, loss limitation, circulation, "
                 "long-term contracts, mining, research, installment sales, intangible drilling, or another "
                 "adjustment — Form 6251 lines 2c/2d/2k/2m/2n/2o-2t/3). Figure Form 6251 manually and enter the AMT "
                 "on Schedule 2 line 2."),
     "notes": "RED-defer the exotic preferences."},
    {"diagnostic_id": "D_6251_006", "title": "AMT foreign tax credit — not computed", "severity": "error",
     "condition": "a_amt_ftc present (line 8)",
     "message": ("Not supported — prepare manually: an alternative minimum tax foreign tax credit (Form 6251 line 8) "
                 "is present. The AMT FTC (a Form 1116 AMT version) is not built this version. Figure Form 6251 "
                 "manually and enter the AMT on Schedule 2 line 2."),
     "notes": "RED-defer line 8 (AMT FTC)."},
    {"diagnostic_id": "D_6251_007", "title": "Alternative minimum tax applies", "severity": "info",
     "condition": "line 11 > 0",
     "message": ("This return owes alternative minimum tax (Form 6251 line 11 > $0) — the tentative minimum tax "
                 "exceeds the regular tax. The AMT is on Schedule 2 line 2 and is included in total tax. Review the "
                 "AMT preference items (commonly the state/local tax add-back or private activity bond interest)."),
     "notes": "Info — surfaces a computed AMT so the preparer can review the drivers."},
    {"diagnostic_id": "D_6251_008", "title": "AMT capital-gains basis difference — verify (Part III)", "severity": "warning",
     "condition": "a_net_capital_gain present AND an AMT-basis difference may exist (line 14 / AMT capital loss carryover)",
     "message": ("Capital gains are present and Form 6251 Part III refigures the capital-gains tax on the AMT base. "
                 "If the AMT basis of any asset differs from the regular-tax basis (depreciation, a prior ISO "
                 "adjustment, or a different AMT capital loss carryover), the Part III amounts must be refigured for "
                 "the AMT — that adjustment (line 14 / line 2k) is not computed this version. Verify."),
     "notes": "Part III reuses the regular cap-gains worksheet; AMT-basis differences are RED-deferred (W4)."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 6251 — TEST SCENARIOS (worked math; check_6251_integrity.py re-derives)
# ═══════════════════════════════════════════════════════════════════════════

F6251_SCENARIOS: list[dict] = [
    {"scenario_name": "6251-T1 — non-itemizer, no preferences → no AMT (the common case)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "filing_status": "single", "a_taxable_income": 100000, "a_standard_deduction": 15000,
                "a_itemizing": False, "a_regular_tax_for_amt": 17000, "a_net_capital_gain": 0},
     "expected_outputs": {"line_4": 115000, "line_5": 88100, "line_6": 26900, "line_7": 6994, "line_11": 0},
     "notes": "AMTI = 100k + 15k std add-back = 115k. Exemption full 88,100 (TI < threshold). L6 = 26,900; TMT = 26% × 26,900 = 6,994 < regular 17,000 → AMT = 0."},
    {"scenario_name": "6251-T2 — high private activity bond interest → AMT applies", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"tax_year": 2025, "filing_status": "single", "a_taxable_income": 400000, "a_standard_deduction": 15000,
                "a_itemizing": False, "a_pab_interest": 80000, "a_regular_tax_for_amt": 100000, "a_net_capital_gain": 0},
     "expected_outputs": {"line_4": 495000, "line_5": 88100, "line_6": 406900, "line_7": 109150, "line_11": 9150, "D_6251_007": True},
     "notes": "AMTI = 400k + 15k + 80k PAB = 495k (< 626,350 → full exemption). L6 = 406,900 > 239,100 → TMT = 28% × 406,900 − 4,782 = 109,150. AMT = 109,150 − 100,000 = 9,150."},
    {"scenario_name": "6251-T3 — SALT itemizer add-back drives AMT", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "a_taxable_income": 500000, "a_salt_deduction": 40000,
                "a_itemizing": True, "a_regular_tax_for_amt": 100000, "a_net_capital_gain": 0},
     "expected_outputs": {"line_2a": 40000, "line_4": 540000, "line_5": 137000, "line_6": 403000, "line_7": 108058, "line_11": 8058, "D_6251_007": True},
     "notes": "MFJ. SALT 40k added back (line 2a). AMTI = 500k + 40k = 540k (< 1,252,700 → full 137,000 exemption). L6 = 403,000 > 239,100 → TMT = 28% × 403,000 − 4,782 = 108,058. AMT = 108,058 − 100,000 = 8,058."},
    {"scenario_name": "6251-T4 — exemption phaseout (high AMTI)", "scenario_type": "edge_case", "sort_order": 4,
     "inputs": {"tax_year": 2025, "filing_status": "single", "a_taxable_income": 700000, "a_standard_deduction": 15000,
                "a_itemizing": False, "a_regular_tax_for_amt": 210000, "a_net_capital_gain": 0},
     "expected_outputs": {"line_4": 715000, "line_5": 65938, "line_6": 649062},
     "notes": "AMTI 715,000 > 626,350 → exemption phased: 88,100 − 25% × (715,000 − 626,350) = 88,100 − 22,162.50 = 65,937.50 → 65,938. L6 = 649,062."},
    {"scenario_name": "6251-T5 — 28% bracket (taxable excess over the breakpoint)", "scenario_type": "normal", "sort_order": 5,
     "inputs": {"tax_year": 2025, "filing_status": "single", "a_taxable_income": 300000, "a_standard_deduction": 15000,
                "a_itemizing": False, "a_pab_interest": 50000, "a_regular_tax_for_amt": 70000, "a_net_capital_gain": 0},
     "expected_outputs": {"line_4": 365000, "line_5": 88100, "line_6": 276900, "line_7": 72750},
     "notes": "L6 = 276,900 > 239,100 → 28% × 276,900 − 4,782 = 77,532 − 4,782 = 72,750. (TMT 72,750 vs regular 70,000 → AMT 2,750.)"},
    {"scenario_name": "6251-T6 — Part III capital-gains worksheet triggered", "scenario_type": "normal", "sort_order": 6,
     "inputs": {"tax_year": 2025, "filing_status": "single", "a_taxable_income": 300000, "a_standard_deduction": 15000,
                "a_itemizing": False, "a_net_capital_gain": 120000, "a_regular_tax_for_amt": 55000},
     "expected_outputs": {"line_4": 315000, "line_6": 226900, "Part_III": True},
     "notes": "Net capital gain present → Part III refigures the 0/15/20% rates on the AMT base; the ordinary portion (L17) gets 26/28%. Integrity gate computes line 40 → line 7."},
    {"scenario_name": "6251-T7 — ISO exercise → RED-defer (D_6251_001)", "scenario_type": "edge_case", "sort_order": 7,
     "inputs": {"tax_year": 2025, "filing_status": "single", "a_taxable_income": 200000, "a_standard_deduction": 15000,
                "a_itemizing": False, "a_iso_exercise": 90000, "a_regular_tax_for_amt": 40000, "a_net_capital_gain": 0},
     "expected_outputs": {"D_6251_001": True, "line_11": None},
     "notes": "ISO present → D_6251_001 RED-defer; line 11 BLANKED (computed manually on Schedule 2 line 2). No silent gap."},
    {"scenario_name": "6251-T8 — TY2026 OBBBA phaseout (50% rate, $500k threshold) — load-bearing", "scenario_type": "normal", "sort_order": 8,
     "inputs": {"tax_year": 2026, "filing_status": "single", "a_taxable_income": 560000, "a_standard_deduction": 16100,
                "a_itemizing": False, "a_regular_tax_for_amt": 130000, "a_net_capital_gain": 0},
     "expected_outputs": {"line_4": 576100, "line_5": 52050, "line_6": 524050, "line_7": 141844, "line_11": 11844, "D_6251_007": True},
     "notes": "TY2026: AMTI 576,100 > 500,000 → exemption 90,100 − 50% × 76,100 = 52,050; L6 = 524,050 > 244,500 → TMT = 28% × 524,050 − 4,890 = 141,844; AMT = 141,844 − 130,000 = 11,844. The OBBBA 50% rate (vs 25%) + $500k threshold (vs $626,350) materially raise AMT vs 2025."},
    {"scenario_name": "6251-T9 — AMT depreciation adjustment (2l) drives AMT", "scenario_type": "normal", "sort_order": 9,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "a_taxable_income": 450000, "a_salt_deduction": 20000,
                "a_itemizing": True, "a_amt_depreciation_adj": 60000, "a_regular_tax_for_amt": 95000, "a_net_capital_gain": 0},
     "expected_outputs": {"line_2l": 60000, "line_4": 530000, "line_5": 137000, "line_6": 393000, "D_6251_007": True},
     "notes": "Depreciation difference 60k (line 2l) + SALT 20k. AMTI = 450k + 20k + 60k = 530k. L6 = 393,000; AMT = TMT − 95,000."},
    {"scenario_name": "6251-T10 — regular tax exceeds TMT → AMT = 0", "scenario_type": "edge_case", "sort_order": 10,
     "inputs": {"tax_year": 2025, "filing_status": "single", "a_taxable_income": 250000, "a_standard_deduction": 15000,
                "a_itemizing": False, "a_pab_interest": 5000, "a_regular_tax_for_amt": 90000, "a_net_capital_gain": 0},
     "expected_outputs": {"line_4": 270000, "line_5": 88100, "line_6": 181900, "line_7": 47294, "line_11": 0},
     "notes": "L6 = 181,900 ≤ 239,100 → TMT = 26% × 181,900 = 47,294 < regular 90,000 → AMT = 0. The no-AMT outcome the engine must PROVE (not assume)."},
]


# ═══════════════════════════════════════════════════════════════════════════
# RULE → AUTHORITY LINKS
# ═══════════════════════════════════════════════════════════════════════════

F6251_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-6251-SCOPE", "IRS_2025_6251_FORM", "primary", "Who must file Form 6251 / AMT imposition"),
    ("R-6251-SCOPE", "IRC_55_59", "primary", "§55(a) AMT = excess of TMT over regular tax"),
    ("R-6251-L1-BASE", "IRS_2025_6251_INSTR", "primary", "Line 1a/1b AMTI base (2025 redesign)"),
    ("R-6251-L1-BASE", "IRC_55_59", "primary", "§56(b)(1) no standard deduction / no SALT; QBI retained"),
    ("R-6251-2A-TAXES", "IRS_2025_6251_FORM", "primary", "Line 2a taxes / standard deduction add-back"),
    ("R-6251-2A-TAXES", "IRC_55_59", "secondary", "§56(b)(1)(A) disallowed taxes"),
    ("R-6251-2B-REFUND", "IRS_2025_6251_FORM", "primary", "Line 2b tax refund subtract"),
    ("R-6251-2G-PAB", "IRS_2025_6251_FORM", "primary", "Line 2g specified private activity bond interest"),
    ("R-6251-2G-PAB", "IRC_55_59", "secondary", "§57(a)(5) PAB interest preference"),
    ("R-6251-2L-DEPR", "IRS_2025_6251_FORM", "primary", "Line 2l post-1986 depreciation"),
    ("R-6251-2L-DEPR", "IRC_55_59", "secondary", "§56(a)(1) AMT depreciation"),
    ("R-6251-L4-AMTI", "IRS_2025_6251_FORM", "primary", "Line 4 AMTI"),
    ("R-6251-L5-EXEMPTION", "IRS_2025_6251_FORM", "primary", "Line 5 exemption worksheet (2025)"),
    ("R-6251-L5-EXEMPTION", "OBBBA_70107", "primary", "2026 phaseout threshold + 50% rate"),
    ("R-6251-L5-EXEMPTION", "RP_2025_32", "primary", "2026 exemption amounts"),
    ("R-6251-L5-EXEMPTION", "IRC_55_59", "secondary", "§55(d) exemption + phaseout"),
    ("R-6251-L6", "IRS_2025_6251_FORM", "primary", "Line 6 taxable excess"),
    ("R-6251-L7-TMT", "IRS_2025_6251_FORM", "primary", "Line 7 26/28% TMT"),
    ("R-6251-L7-TMT", "IRC_55_59", "primary", "§55(b)(1) rate schedule"),
    ("R-6251-L7-TMT", "RP_2025_32", "secondary", "2026 26/28% breakpoint $244,500"),
    ("R-6251-P3-CAPGAINS", "IRS_2025_6251_FORM", "primary", "Part III AMT capital-gains worksheet"),
    ("R-6251-L10-REGTAX", "IRS_2025_6251_INSTR", "primary", "Line 10 regular tax (no Schedule J)"),
    ("R-6251-L11-AMT", "IRS_2025_6251_FORM", "primary", "Line 11 AMT → Schedule 2 line 2"),
    ("R-6251-L11-AMT", "IRC_55_59", "primary", "§55(a) AMT = TMT − regular tax"),
    ("R-6251-DEFER", "IRS_2025_6251_FORM", "primary", "Lines 2c-2t / 8 preferences (RED-deferred v1)"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS (staged into tts-tax-app at the assertions leg)
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-6251-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Form 6251 line 11 → Schedule 2 line 2",
     "description": ("Validates R-6251-L11-AMT. AMT (line 11) → Schedule 2 line 2 → 1040 line 17 → total tax. Bug it "
                     "catches: a computed AMT not reaching total tax (the old D_AMT_DEFER manual-entry gap)."),
     "definition": {"kind": "flow_assertion", "form": "6251", "source_line": "11", "must_write_to": ["SCH_2.2"]},
     "sort_order": 1},
    {"assertion_id": "FA-1040-6251-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "AMT = max(0, tentative minimum tax − regular tax)",
     "description": ("Validates R-6251-L11-AMT / §55(a). Line 11 = max(0, line 9 − line 10); the AMT is the EXCESS of "
                     "the tentative minimum tax over the regular tax, never negative. Bug it catches: charging the "
                     "full TMT, or a negative AMT."),
     "definition": {"kind": "formula_check", "form": "6251", "formula": "line_11 == max(0, line_9 - line_10)"},
     "sort_order": 2},
    {"assertion_id": "FA-1040-6251-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Exemption phaseout: L5 = max(0, base − rate × max(0, AMTI − threshold))",
     "description": ("Validates R-6251-L5-EXEMPTION. The exemption phases out at 25% (2025) / 50% (2026, OBBBA) of the "
                     "AMTI excess over the threshold. Bug it catches: no phaseout, the wrong rate, or a negative "
                     "exemption."),
     "definition": {"kind": "formula_check", "form": "6251",
                    "formula": "line_5 == max(0, exemption_base - phaseout_rate * max(0, line_4 - phaseout_threshold))"},
     "sort_order": 3},
    {"assertion_id": "FA-1040-6251-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "TMT 26%/28% breakpoint (line 7)",
     "description": ("Validates R-6251-L7-TMT. Line 7 = 26% of the taxable excess up to the breakpoint, else 28% minus "
                     "(breakpoint × 2%). Bug it catches: a flat 26%, the wrong breakpoint, or omitting the 28% "
                     "subtraction."),
     "definition": {"kind": "formula_check", "form": "6251",
                    "formula": "line_7 == (line_6 * 0.26 if line_6 <= breakpoint else line_6 * 0.28 - breakpoint * 0.02)"},
     "sort_order": 4},
    {"assertion_id": "FA-1040-6251-05", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "AMTI base — std-deduction/SALT add-back; QBI retained; senior deduction removed",
     "description": ("Validates R-6251-L1-BASE / §56(b)(1). The AMTI base adds back the standard deduction (or SALT) and "
                     "the OBBBA senior deduction, and RETAINS the QBI deduction. Bug it catches: leaving the standard "
                     "deduction in the base, or disallowing QBI."),
     "definition": {"kind": "gating_check", "form": "6251",
                    "blockers": ["standard_deduction_in_amti", "qbi_disallowed_for_amt"],
                    "expect": {"std_deduction_added_back": True, "qbi_retained": True}},
     "sort_order": 5},
    {"assertion_id": "FA-1040-6251-06", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Part III reuses the capital-gains rates (0/15/20/25/28%) on the AMT base",
     "description": ("Validates R-6251-P3-CAPGAINS. When net capital gain / qualified dividends are present, Part III "
                     "refigures the preferential-rate tax on the AMT base (reusing the regular QDCGT/SDTW breakpoints) "
                     "rather than taxing it at 26/28%. Bug it catches: applying 26/28% to capital gains."),
     "definition": {"kind": "gating_check", "form": "6251",
                    "blockers": ["capital_gain_taxed_at_28pct"], "expect": {"part_iii_used": True}},
     "sort_order": 6},
    {"assertion_id": "FA-1040-6251-07", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "AMT constants year-keyed; 2026 OBBBA phaseout ($500k/$1M @ 50%)",
     "description": ("Pins the AMT exemption / phaseout threshold / phaseout rate / 26-28 breakpoint for both years. "
                     "Bug it catches: a stale 2025 amount carried to 2026, or missing the OBBBA threshold reversion / "
                     "50% rate."),
     "definition": {"kind": "constants_check", "form": "6251",
                    "constants": {"exemption_2025": AMT_EXEMPTION[2025], "exemption_2026": AMT_EXEMPTION[2026],
                                  "threshold_2025": AMT_PHASEOUT_THRESHOLD[2025], "threshold_2026": AMT_PHASEOUT_THRESHOLD[2026],
                                  "rate_2025": AMT_PHASEOUT_RATE[2025], "rate_2026": AMT_PHASEOUT_RATE[2026],
                                  "breakpoint_2025": AMT_BREAKPOINT[2025], "breakpoint_2026": AMT_BREAKPOINT[2026],
                                  "amt_rates": [AMT_RATE_LOW, AMT_RATE_HIGH], "applies_to_years": [2025, 2026]}},
     "sort_order": 7},
    {"assertion_id": "FA-1040-6251-08", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "RED-defer no-silent-gap: unsupported preferences blank line 11 + fire a RED",
     "description": ("Validates R-6251-DEFER. ISO (2i), QSBS (2h), NOL (2e/2f), estates/trusts (2j), the exotic "
                     "preferences, and the AMT FTC (line 8) each fire a specific D_6251_* error and BLANK line 11 "
                     "(prepare manually) rather than silently computing a wrong AMT. Bug it catches: a silently-wrong "
                     "AMT when an unsupported preference is present."),
     "definition": {"kind": "gating_check", "form": "6251",
                    "blockers": ["iso_exercise", "qsbs", "amt_nol", "estate_trust_amt", "other_preference", "amt_ftc"],
                    "expect": {"red_fires": True, "line_11_blank": True}},
     "sort_order": 8},
    {"assertion_id": "FA-1040-6251-09", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Line 10 regular tax excludes Schedule J (refigured)",
     "description": ("Validates R-6251-L10-REGTAX. The regular tax compared against the TMT is refigured WITHOUT "
                     "Schedule J income averaging (1040 L16 − 4972 + Sch 2 L1z − Sch 3 L1 − 8978 neg). Bug it catches: "
                     "comparing the TMT against the Schedule-J-reduced tax (overstating AMT)."),
     "definition": {"kind": "gating_check", "form": "6251",
                    "blockers": ["schedule_j_tax_used_for_amt"], "expect": {"regular_tax_refigured_without_schedule_j": True}},
     "sort_order": 9},
]


FORMS: list[dict] = [
    {
        "identity": {
            "form_number": "6251",
            "form_title": "Form 6251 — Alternative Minimum Tax—Individuals (TY2025)",
            "notes": (
                "NEW spec (no prior RS draft). The common-case AMT engine: AMTI add-backs (std-deduction/SALT/senior; "
                "QBI retained) → exemption with phaseout (year-keyed; 2026 OBBBA $500k/$1M @ 50%) → 26/28% tentative "
                "minimum tax (Part III AMT capital-gains worksheet for preferential-rate income) → AMT = max(0, TMT − "
                "regular tax) → Schedule 2 line 2. v1 computes 2a/2b/2g/2l; RED-defers ISO (2i), QSBS (2h), NOL "
                "(2e/2f), estates/trusts (2j), the exotic preferences, and the AMT FTC (line 8) — each its own RED, "
                "line 11 blanked. Verified against the 2025 f6251.pdf (read directly) + i6251 + IRC §§55-59 + OBBBA "
                "§70107. The existing D_AMT_DEFER presence-check narrows to the deferred items at the diagnostics leg."
            ),
        },
        "facts": F6251_FACTS,
        "rules": F6251_RULES,
        "lines": F6251_LINES,
        "diagnostics": F6251_DIAGNOSTICS,
        "scenarios": F6251_SCENARIOS,
        "rule_links": F6251_RULE_LINKS,
    },
]


class Command(BaseCommand):
    help = (
        "Load the Form 6251 spec (Alternative Minimum Tax — Individuals: AMTI "
        "add-backs, exemption phaseout, 26/28% TMT, Part III capital gains, "
        "AMT = TMT − regular tax → Schedule 2 line 2). Refuses to seed until Ken "
        "sets READY_TO_SEED=True after the in-session review walk."
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()

        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad FORM 6251 spec (Alternative Minimum Tax)\n"))

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
                "\nREFUSING TO SEED FORM 6251: not cleared to seed.\n\n"
                "Content is authored, but seeding is gated until Ken reviews the packet\n"
                "(W1 AMTI base composition; W2 the 2026 OBBBA constants $500k/$1M @ 50%;\n"
                "W3 the RED-defer enumeration; W4 Part III cap-gains reuse; W5 line-10\n"
                "regular tax / Schedule-J refigure; W6 D_AMT_DEFER narrowing) and flips\n"
                "the sentinel.\n\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True to proceed)\n\n"
                f"Currently empty / placeholder:\n  {still_empty}\n\n"
                "To proceed: review the module-level data lists, then set READY_TO_SEED\n"
                "= True. Idempotent via update_or_create — safe to re-run after edits."
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Topics / sources (mirror load_1040_form_8995a.py exactly)
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
        self.stdout.write("FORM 6251 loaded.")
        self.stdout.write(
            f"  facts {len(F6251_FACTS)} / rules {len(F6251_RULES)} / lines {len(F6251_LINES)} / "
            f"diagnostics {len(F6251_DIAGNOSTICS)} / tests {len(F6251_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}"
        )
        self.stdout.write("=" * 60)
