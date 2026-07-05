"""Load the Schedule D / Form 8949 / capital-gains-worksheets specs — Sprint Topic 9
(SPRINT_SCOPE roster #8, with the Schedule D Tax Worksheet PULLED IN by Ken).

Creates/re-authors THREE TaxForms (one idempotent command, the
load_1040_schedule_c.py 4-form precedent):

  - SCHEDULE_D (Capital Gains and Losses, Form 1040): the real 2025 face —
    Part I short-term netting (lines 1a-7), Part II long-term netting (lines
    8a-15), Part III summary (16-22): line 16 -> Form 1040 line 7a routing,
    the line-21 $3,000/$1,500 capital-loss limitation, the line-17/20/22
    tax-worksheet routing (QDCGT vs Schedule D Tax Worksheet vs ordinary),
    and the page-1 QOF disposal question.
  - 1040_SCHD_WS: companion computational pseudo-form (the 1040_INTDIV ws_*
    precedent — renders as STATEMENT pages, never a faked face) holding the
    FOUR worksheets from i1040sd 2025, transcribed line-by-line: the
    Schedule D Tax Worksheet (sdtw_1..47 — Ken pulled it IN-scope,
    overriding the sprint DoD RED-defer), the Capital Loss Carryover
    Worksheet applied year-shifted as the carryover-OUT computation
    (clc_1..13), the 28% Rate Gain Worksheet (w28_1..7), and the
    Unrecaptured Section 1250 Gain Worksheet (u1250_1..18).
  - 8949 (Sales and Other Dispositions of Capital Assets) — RE-AUTHORED.
    The existing RS "8949" is a thin 1120-S-era draft (4 unnamed rules, 12
    column lines, 10 nameless facts). This loader RETIRES the stale
    artifacts (the _retire_stale_8995 precedent) and authors the real 2025
    face: the TWELVE box system (A-F securities/1099-B + G-L digital
    assets/1099-DA, NEW for 2025), column (f)/(g) adjustment mechanics, the
    FULL i8949 adjustment-code table as a cited data list (Ken Decision 5 —
    the input-UI dropdown source), Exception-2 broker-summary rows (Ken
    Decision 2, code M), and the per-box totals that feed Schedule D lines
    1b/2/3/8b/9/10. entity_types is PRESERVED multi-entity (1120S/1065/
    1120/1040) — the 1120-S render reuses this form.

Session 2026-06-13: authored by transcription from primary sources fetched
and text-extracted the same day (pymupdf dumps in tts-tax-app
server/.scratch/: f1040sd_2025_dump.txt, i1040sd_2025_dump.txt,
i8949_2025_dump.txt, f8949_2025_dump.txt; consolidated in tts-tax-app
server/specs/_topic9_schedule_d_source_brief.md):

  - 2025 Schedule D (f1040sd.pdf, Attachment Seq 12) + i1040sd instructions
    (incl. all four worksheets verbatim).
  - 2025 Form 8949 (f8949.pdf — the local manifest copy IS the 2025 12-box
    revision; 1120-S 192-field map reusable) + i8949 instructions (the
    column-(f) code table, box definitions, Exceptions 1/2).
  - TY2026 SDTW constants: the 0%/15-20% breakpoints REUSE the Topic 3
    Ken-blessed year-keyed QDCGT constants (RP 2024-40 §2.03 / RP 2025-32
    §4.03 — NOT re-derived); the SDTW line-19 threshold is the 32%-bracket
    start from the spine's Ken-verified RP 2025-32 §4.01 bracket tables.

TOPIC SCOPE (SPRINT_SCOPE roster #8 + Ken's FIVE kickoff decisions,
DECISIONS.md 2026-06-13 — do not re-litigate; memory topic9-scheduled-scope):
  IN: per-transaction CapitalTransaction document model (Decision 1 — NOT
      the 1120-S Disposition); broker-summary per-box TOTALS rows, 8949
      Exception 2 / code M (Decision 2); Capital Loss Carryover v1 =
      preparer-entered prior-year ST/LT facts IN + the worksheet-computed
      carryover OUT (Decision 3); the Schedule D Tax Worksheet incl. 25%
      unrecaptured-1250 and 28% collectibles/1202 groups (Decision 4); the
      i8949 adjustment-code dropdown with definitions (Decision 5); wash
      sales as ENTERED (code W); digital-asset boxes G-L (1099-DA);
      1099-DIV box 2a -> line 13 / box 2b -> 1250 WS / box 2d -> 28% WS
      (retiring/narrowing the Topic 3 stored-field REDs).
  OUT (RED "prepare manually" or info-flagged direct entry; enumerated):
      Form 4952 investment-interest interplay (SDTW lines 3/4 — RED);
      §1202 exclusion FRACTION mechanics (the 50%/60%/75% add-back is a
      preparer-entered fact, code-Q transactions check it); QOF deferral
      elections (codes Y/Z — RED); Form 6252 / 4684 / 6781 / 8824 flows
      (lines 4/11 = direct entry + info); K-1 capital gains (lines 5/12 =
      direct entry + info, no doc model); 1099-B import; 1099-DIV box 2c
      (§1202 from a RIC — RED stays); auto wash-sale detection across lots.

YEAR-KEYED CONSTANTS (target-year policy: TY2026 product target, TY2025
verification bed; each year verified independently):
  - SDTW line 15 (0% max) + line 26 (15% max): the QDCGT breakpoints —
    IDENTICAL to the Topic 3 constants (cross-spec identity asserted by
    FA-1040-SCHD-06 and the integrity checker).
  - SDTW line 19: the 32%-bracket start (RP 2024-40 §2.01 / RP 2025-32
    §4.01). 2025: $197,300 single/MFS/HOH, $394,600 MFJ/QSS. 2026:
    $201,775 single/MFS, $403,550 MFJ/QSS, $201,750 HOH (note the $25 HOH
    asymmetry — per-status transcription mandatory).
  - STATUTORY / NON-INDEXED (do NOT year-key): the §1211(b) capital-loss
    limit $3,000 / $1,500 MFS (verbatim on the face, line 21); the §1(h)
    25% unrecaptured-1250 and 28% collectibles/1202 cap rates (verbatim in
    the SDTW, lines 40/43); the 0%/15%/20% preferential rates.

requires_human_review WALK ITEMS (flagged for Ken's review walk):
  1. SDTW line 19 TY2026 ($201,775/$403,550/$201,750) is DERIVED from the
     RP 2025-32 §4.01 bracket tables (spine-verified PM #11) — the IRS has
     not published a 2026 SDTW. Re-pin when the 2026 Schedule D
     instructions land (~Dec 2026; joins the Tax Table standing
     obligation). D_SCHD_010 info fires on TY2026 SDTW returns meanwhile.
  2. Digital-asset boxes G-L (1099-DA, new 2025): recommend IN scope —
     routing is pairwise identical to A-F (A/G->1b, B/H->2, C/I->3,
     D/J->8b, E/K->9, F/L->10); the box is one enum on the model.
  3. Form 4952 -> RED-defer (D_SCHD_001). The SDTW reads 4952 lines
     4g/4e; the form is unbuilt, so preparer-asserted 4952 filing blocks
     the worksheet rather than silently computing without it.
  4. Schedule D lines 4/5/11/12 = DIRECT ENTRY with info diagnostics
     (D_SCHD_003/004): the source forms (6252/4684/6781/8824, K-1s) are
     not computed, but a preparer-keyed result flows correctly — no
     silent gap. Confirm severity (info vs warning).
  5. Unrecaptured-1250 WS v1 sourcing: lines 1-9 (the Form 4797 path) = 0
     — no 1040-level 4797 exists; line 11 = 1099-DIV box 2b aggregate +
     the K-1 fact; line 12 = preparer-entered. D_SCHD_011 warns when
     line 11 of Schedule D is direct-entered (may carry 1250 gain).
  6. 28% Rate Gain WS line 2 (§1202 add-back) = preparer-entered fact
     (the 50%/60%/75% fraction math is OUT); D_SCHD_009 errors when a
     code-Q transaction exists but the fact is unanswered.
  7. Schedule D lines 1a/8a stay UNUSED (blank) — every transaction,
     including Exception-2 summary rows, flows through Form 8949 (always
     permitted: "if you choose to report all these transactions on Form
     8949, leave this line blank"). One path, no Exception-1 branch at
     the transaction level. (Topic 3's 1040-line-7 checkbox path for
     cap-gain-distributions-ONLY returns is unchanged.)
  8. 1099-DIV stored-field REDs retire/narrow: box 2a -> Schedule D line
     13 when engaged (else the Topic 3 Exception-1 path); box 2b -> 1250
     WS line 11; box 2d -> 28% WS line 4; box 2c (§1202) RED STAYS
     (D_SCHD_002). D_INTDIV_002's "Schedule D required -> blocked" RED
     retires — route_line_16 gains the Schedule-D path (sibling intdiv
     spec edit, the D_1040_001 bridge-retirement precedent).
  9. Carryover-OUT = the published CLC worksheet applied year-shifted
     (2025 Schedule D figures + 2025 line 15 -> the 2026 carryover; Pub
     550 equivalence per the Line 21 instruction). Display/statement
     only this year; next year it pre-fills the carryover facts.
 10. 8949 re-author keeps entity_types multi-entity and the 1120-S render
     path untouched (the 192-field map reads the PDF, not the RS
     line_map). The stale-artifact retirement is keyed to keep-sets.

SPINE / SIBLING SUPERSESSION (build legs, flagged for Ken — the Topic 5/7/8
precedent; override = escape hatch):
  - Form 1040 line 7a becomes a COMPUTED feeder from Schedule D line 16
    (gain), line 21 (limited loss), or 0 — when Schedule D is engaged.
    The Topic 3 "7b Schedule D not required" checkbox path remains for
    capital-gain-distributions-only returns.
  - route_line_16 (compute_intdiv) gains the Schedule-D route: line 20
    YES -> QDCGT (D16 replaces the cap-gain-dist component), line 20
    NO -> the SDTW; D_INTDIV_002 retires.
  - 8995 line 12 net capital gain gains the min(D15, D16) component when
    Schedule D is engaged (sibling 8995 spec edit; D_8995_002 retires).
  - EIC investment income already reads 1040 line 7 — flows automatically.
  The flow-assertion gate (100 active / 122 passed) must not regress.

Safety guard
------------
`READY_TO_SEED = False`. Content is authored; Ken reviews the packet (the
verified constants both years, the 10 walk items, the cross-form flow, the
RED-defer enumeration, the 8949 retire plan), flips the sentinel, then we
seed. Until then the command refuses to write to the DB. Idempotent via
update_or_create — safe to re-run after edits.

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
# citations, the verified constants BOTH years, the 10 requires_human_review
# walk items, the cross-form flow map, the RED-defer enumeration, the 8949
# stale-artifact retire plan). Until then the command refuses to write.
#
# FLIPPED 2026-06-13 — Ken APPROVED the review walk in-session ("Looks good.
# Go."): the verified constants both years (the QDCGT-identity breakpoints,
# the DERIVED 2026 SDTW line-19 bracket tops incl. the $25 HOH asymmetry, the
# statutory $3,000/$1,500 + 25%/28%), all 10 walk items as recommended
# (boxes G-L IN; 4952 RED; lines 4/5/11/12 direct-entry info; the 1250-WS v1
# sourcing; the SS1202 add-back fact; 1a/8a unused; the DIV 2a/2b/2d RED
# retirements with 2c surviving; the year-shifted carryover-out; the 8949
# retire plan), and the sibling intdiv/8995 supersession edits.
# ═══════════════════════════════════════════════════════════════════════════
READY_TO_SEED = True


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1040"]
# 8949 keeps its existing multi-entity surface (walk item 10).
FORM_ENTITY_TYPES_8949 = ["1120S", "1065", "1120", "1040"]


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS (every value cited; never training memory)
# ═══════════════════════════════════════════════════════════════════════════

# §1211(b) capital-loss limitation — STATUTORY, non-indexed. Verbatim on the
# 2025 Schedule D face, line 21: "($3,000), or if married filing separately,
# ($1,500)".
CAPITAL_LOSS_LIMIT = 3000
CAPITAL_LOSS_LIMIT_MFS = 1500

# §1(h) cap rates — STATUTORY, non-indexed. Verbatim in the SDTW: line 40
# "Multiply line 39 by 25%", line 43 "Multiply line 42 by 28%"; lines 31/34
# carry the 15%/20% preferential rates.
SDTW_RATE_UNRECAP_1250 = 0.25
SDTW_RATE_28PCT_GROUP = 0.28

# SDTW line 15 — maximum zero-rate amounts. YEAR-KEYED. IDENTICAL to the
# Topic 3 QDCGT ZERO_RATE_MAX constants (Ken-blessed; RP 2024-40 §2.03 /
# RP 2025-32 §4.03). 2025 values verbatim on the 2025 SDTW line 15.
SDTW_ZERO_RATE_MAX: dict[int, dict] = {
    2025: {"single": 48350, "mfs": 48350, "mfj": 96700, "qss": 96700, "hoh": 64750},
    2026: {"single": 49450, "mfs": 49450, "mfj": 98900, "qss": 98900, "hoh": 66200},
}

# SDTW line 26 — maximum 15%-rate amounts. YEAR-KEYED, == Topic 3 RATE15_MAX.
# single != MFS here (unlike line 15). 2025 verbatim on the SDTW line 26.
SDTW_RATE15_MAX: dict[int, dict] = {
    2025: {"single": 533400, "mfs": 300000, "mfj": 600050, "qss": 600050, "hoh": 566700},
    2026: {"single": 545500, "mfs": 306850, "mfj": 613700, "qss": 613700, "hoh": 579600},
}

# SDTW line 19 — the 32%-bracket start (top of the 24% bracket). YEAR-KEYED.
# 2025 verbatim on the SDTW line 19 ($197,300 single/MFS/HOH; $394,600
# MFJ/QSS — matches RP 2024-40 §2.01). 2026 DERIVED from RP 2025-32 §4.01
# Tables 1-4 (spine-verified PM #11): note HOH $201,750 vs single/MFS
# $201,775 — a $25 asymmetry the 2025 form hides. WALK ITEM 1: re-pin when
# the IRS publishes the 2026 Schedule D instructions (~Dec 2026).
SDTW_BRACKET32_START: dict[int, dict] = {
    2025: {"single": 197300, "mfs": 197300, "mfj": 394600, "qss": 394600, "hoh": 197300},
    2026: {"single": 201775, "mfs": 201775, "mfj": 403550, "qss": 403550, "hoh": 201750},
}


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY TOPICS
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("capital_gains_1040", "Schedule D (1040) — capital gain/loss netting, §1211(b) loss limit, line-16 routing -> 1040 line 7a"),
    ("form_8949_reporting", "Form 8949 — transaction reporting, boxes A-L (1099-B + 1099-DA), column (f)/(g) adjustment codes"),
    ("capital_gains_worksheets", "i1040sd worksheets — Schedule D Tax Worksheet (25%/28% groups), Capital Loss Carryover, 28% Rate Gain, Unrecaptured §1250"),
]

# Existing sources to REUSE (looked up, not modified).
EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "RP_2024_40",            # §2.03 TY2025 cap-gain breakpoints (excerpted by intdiv)
    "RP_2025_32",            # §4.03 TY2026 breakpoints (intdiv) + §4.01 brackets (spine)
    "IRS_2025_1040_FORM",    # 1040 line 7a/7b
    "IRS_2025_1040_INSTR",   # QDCGT worksheet (line 16) — the line-20 YES path
]

# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY SOURCES (with embedded excerpts) — CREATE
# Transcribed 2026-06-13 from the fetched PDFs (tts-tax-app server/.scratch/),
# requires_human_review=False (verbatim, verifiable against the on-disk dumps).
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_SCHEDD_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Schedule D (Form 1040) — Capital Gains and Losses",
        "citation": "Schedule D (Form 1040) 2025; f1040sd.pdf; Attachment Sequence No. 12",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f1040sd.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": "Both pages transcribed 2026-06-13 (server/.scratch/f1040sd_2025_dump.txt). NOTE: the 2025 face references Form 1099-DA and 8949 boxes A-L; feeds Form 1040 line 7a.",
        "topics": ["capital_gains_1040"],
        "excerpts": [
            {
                "excerpt_label": "Parts I-II netting structure (lines 1a-15, verbatim line list)",
                "location_reference": "Schedule D (2025), Parts I-II",
                "excerpt_text": (
                    "Part I Short-Term (assets held one year or less), columns (d) Proceeds, "
                    "(e) Cost, (g) Adjustments from Form(s) 8949, (h) Gain or (loss) = (d) - (e) "
                    "+ (g). 1a Totals for all short-term transactions reported on Form 1099-B or "
                    "Form 1099-DA for which basis was reported to the IRS and for which you have "
                    "no adjustments. However, if you choose to report all these transactions on "
                    "Form 8949, leave this line blank and go to line 1b. 1b Totals for all "
                    "transactions reported on Form(s) 8949 with Box A or Box G checked. 2 ... Box "
                    "B or Box H checked. 3 ... Box C or Box I checked. 4 Short-term gain from "
                    "Form 6252 and short-term gain or (loss) from Forms 4684, 6781, and 8824. 5 "
                    "Net short-term gain or (loss) from partnerships, S corporations, estates, "
                    "and trusts from Schedule(s) K-1. 6 Short-term capital loss carryover (from "
                    "line 8 of your Capital Loss Carryover Worksheet) (entered as a loss). 7 Net "
                    "short-term capital gain or (loss). Combine lines 1a through 6 in column (h). "
                    "Part II Long-Term: 8a/8b (Box D or J), 9 (Box E or K), 10 (Box F or L), 11 "
                    "Gain from Form 4797, Part I; long-term gain from Forms 2439 and 6252; and "
                    "long-term gain or (loss) from Forms 4684, 6781, and 8824. 12 Net long-term "
                    "gain or (loss) from partnerships, S corporations, estates, and trusts from "
                    "Schedule(s) K-1. 13 Capital gain distributions. 14 Long-term capital loss "
                    "carryover (from line 13 of the worksheet) (entered as a loss). 15 Net "
                    "long-term capital gain or (loss). Combine lines 8a through 14 in column (h)."
                ),
                "summary_text": (
                    "L7 = sum(1a..6 col h); L15 = sum(8a..14 col h). Per-box 8949 totals land "
                    "pairwise: A/G->1b, B/H->2, C/I->3, D/J->8b, E/K->9, F/L->10. Lines 4/5/11/12 "
                    "= v1 direct entry; 6/14 = carryover facts (negative); 13 = 1099-DIV box 2a."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part III summary + line-16 routing + line-21 loss limit (verbatim)",
                "location_reference": "Schedule D (2025), Part III lines 16-22",
                "excerpt_text": (
                    "16 Combine lines 7 and 15 and enter the result. If line 16 is a gain, enter "
                    "the amount from line 16 on Form 1040, 1040-SR, or 1040-NR, line 7a. Then, go "
                    "to line 17 below. If line 16 is a loss, skip lines 17 through 20 below. "
                    "Then, go to line 21. Also be sure to complete line 22. If line 16 is zero, "
                    "skip lines 17 through 21 below and enter -0- on Form 1040, line 7a. Then, go "
                    "to line 22. 17 Are lines 15 and 16 both gains? Yes -> line 18; No -> skip "
                    "18-21, go to 22. 18 If you are required to complete the 28% Rate Gain "
                    "Worksheet, enter the amount, if any, from line 7 of that worksheet. 19 If "
                    "you are required to complete the Unrecaptured Section 1250 Gain Worksheet, "
                    "enter the amount, if any, from line 18 of that worksheet. 20 Are lines 18 "
                    "and 19 both zero or blank and you are not filing Form 4952? Yes -> Complete "
                    "the Qualified Dividends and Capital Gain Tax Worksheet; don't complete "
                    "lines 21 and 22. No -> Complete the Schedule D Tax Worksheet; don't "
                    "complete lines 21 and 22. 21 If line 16 is a loss, enter here and on Form "
                    "1040, line 7a, the smaller of: the loss on line 16; or ($3,000), or if "
                    "married filing separately, ($1,500). Note: When figuring which amount is "
                    "smaller, treat both amounts as positive numbers. 22 Do you have qualified "
                    "dividends on Form 1040, line 3a? Yes -> Complete the QDCGT Worksheet. No "
                    "-> Complete the rest of Form 1040."
                ),
                "summary_text": (
                    "L16 = L7 + L15 -> 1040 line 7a (gain / 0 / loss limited by L21). The "
                    "$3,000/$1,500 §1211(b) limit is statutory non-indexed. Route: 17 both "
                    "gains? -> 18/19 worksheets -> 20 (both zero AND no Form 4952 -> QDCGT, "
                    "else SDTW); loss/zero -> 22 (qualified dividends -> QDCGT, else ordinary)."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Page-1 QOF disposal question (verbatim)",
                "location_reference": "Schedule D (2025), page 1 header",
                "excerpt_text": (
                    "Did you dispose of any investment(s) in a qualified opportunity fund during "
                    "the tax year? Yes / No. If 'Yes,' attach Form 8949 and see its instructions "
                    "for additional requirements for reporting your gain or loss."
                ),
                "summary_text": (
                    "Header Yes/No (three-state input, the digital-asset-question idiom; "
                    "D_SCHD_006 warns while unanswered). QOF deferral elections themselves "
                    "(8949 codes Y/Z) are RED-defer (D_SCHD_007)."
                ),
                "is_key_excerpt": False,
            },
        ],
    },
    {
        "source_code": "IRS_2025_SCHEDD_INSTR",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Schedule D (Form 1040) — incl. the four worksheets",
        "citation": "i1040sd (2025)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i1040sd.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": False,
        "trust_score": 9.00,
        "requires_human_review": False,
        "notes": "All 16 pages transcribed 2026-06-13 (server/.scratch/i1040sd_2025_dump.txt). The four worksheets transcribed line-by-line into 1040_SCHD_WS.",
        "topics": ["capital_gains_1040", "capital_gains_worksheets"],
        "excerpts": [
            {
                "excerpt_label": "Capital Loss Carryover Worksheet lines 1-13 (verbatim)",
                "location_reference": "i1040sd (2025), Capital Loss Carryover Worksheet—Lines 6 and 14",
                "excerpt_text": (
                    "Use this worksheet to figure your capital loss carryovers from 2024 to 2025 "
                    "if your 2024 Schedule D, line 21, is a loss and (a) that loss is a smaller "
                    "loss than the loss on your 2024 Schedule D, line 16; or (b) if the amount on "
                    "your 2024 Form 1040, line 15, would be less than zero if you could enter a "
                    "negative amount on that line. Otherwise, you don't have any carryovers. 1. "
                    "Enter the amount from your 2024 Form 1040, line 15. If the amount would "
                    "have been a loss if you could enter a negative number on that line, enclose "
                    "the amount in parentheses. 2. Enter the loss from your 2024 Schedule D, "
                    "line 21, as a positive amount. 3. Combine lines 1 and 2. If zero or less, "
                    "enter -0-. 4. Enter the smaller of line 2 or line 3. If line 7 of your 2024 "
                    "Schedule D is a loss, go to line 5; otherwise, enter -0- on line 5 and go "
                    "to line 9. 5. Enter the loss from your 2024 Schedule D, line 7, as a "
                    "positive amount. 6. Enter any gain from your 2024 Schedule D, line 15. If a "
                    "loss, enter -0-. 7. Add lines 4 and 6. 8. Short-term capital loss carryover "
                    "for 2025. Subtract line 7 from line 5. If zero or less, enter -0-. If more "
                    "than zero, also enter this amount on Schedule D, line 6. If line 15 of your "
                    "2024 Schedule D is a loss, go to line 9; otherwise, skip lines 9 through "
                    "13. 9. Enter the loss from your 2024 Schedule D, line 15, as a positive "
                    "amount. 10. Enter any gain from your 2024 Schedule D, line 7. If a loss, "
                    "enter -0-. 11. Subtract line 5 from line 4. If zero or less, enter -0-. 12. "
                    "Add lines 10 and 11. 13. Long-term capital loss carryover for 2025. "
                    "Subtract line 12 from line 9. If zero or less, enter -0-. If more than "
                    "zero, also enter this amount on Schedule D, line 14."
                ),
                "summary_text": (
                    "v1 (Ken Decision 3): carryover IN = two preparer-entered facts -> lines "
                    "6/14. The same worksheet applied YEAR-SHIFTED (this year's D7/D15/D16/D21 "
                    "+ 1040 line 15) computes the carryover OUT to next year (clc_1..13, "
                    "statement only; the Line 21 instruction defers to next year's worksheet / "
                    "Pub. 550 — same math). WALK ITEM 9."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "28% Rate Gain Worksheet lines 1-7 (verbatim)",
                "location_reference": "i1040sd (2025), 28% Rate Gain Worksheet—Line 18",
                "excerpt_text": (
                    "1. Enter the total of all collectibles gain or (loss) from items you "
                    "reported on Form 8949, Part II. 2. Enter as a positive number the total of: "
                    "any section 1202 exclusion you reported in column (g) of Form 8949, Part "
                    "II, with code 'Q' in column (f), that is 50% of the gain; 2/3 of any "
                    "section 1202 exclusion ... that is 60% of the gain; and 1/3 of any section "
                    "1202 exclusion ... that is 75% of the gain. Don't make an entry for any "
                    "section 1202 exclusion that is 100% of the gain. 3. Enter the total of all "
                    "collectibles gain or (loss) from Form 4684, line 4 (but only if Form 4684, "
                    "line 15, is more than zero); Form 6252; Form 6781, Part II; and Form 8824. "
                    "4. Enter the total of any collectibles gain reported to you on: Form "
                    "1099-DIV, box 2d; Form 2439, box 1d; and Schedule K-1 from a partnership, "
                    "S corporation, estate, or trust. 5. Enter your long-term capital loss "
                    "carryovers from Schedule D, line 14; and Schedule K-1 (Form 1041), box 11, "
                    "code D. (entered as a loss) 6. If Schedule D, line 7, is a (loss), enter "
                    "that (loss) here. Otherwise, enter -0-. 7. Combine lines 1 through 6. If "
                    "zero or less, enter -0-. If more than zero, also enter this amount on "
                    "Schedule D, line 18."
                ),
                "summary_text": (
                    "w28_1 = code-C collectibles from the transactions (COMPUTED); w28_2 = the "
                    "§1202 add-back PREPARER FACT (fraction math OUT — walk item 6); w28_3+4 = "
                    "1099-DIV box 2d aggregate (computed) + the K-1/other collectibles fact; "
                    "w28_5 = LT carryover (negative); w28_6 = ST loss if any; w28_7 = max(0, "
                    "combine) -> Schedule D line 18."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Unrecaptured Section 1250 Gain Worksheet lines 1-18 (verbatim, v1 path)",
                "location_reference": "i1040sd (2025), Unrecaptured Section 1250 Gain Worksheet—Line 19",
                "excerpt_text": (
                    "If you aren't reporting a gain on Form 4797, line 7, skip lines 1 through "
                    "9 and go to line 10. [Lines 1-9: the Form 4797 §1250 path — smaller of "
                    "4797 line 22/24 minus line 26g ordinary recapture, installment amounts "
                    "from Form 6252 lines 26/37, K-1 unrecaptured 1250 from partnerships/S "
                    "corps, capped at the 4797 line 7 gain net of line 8.] 10. Enter the amount "
                    "of any gain from the sale or exchange of an interest in a partnership "
                    "attributable to unrecaptured section 1250 gain. 11. Enter the total of any "
                    "amounts reported to you as 'unrecaptured section 1250 gain' on a Schedule "
                    "K-1, Form 1099-DIV, or Form 2439 from an estate, a trust, a real estate "
                    "investment trust, or a mutual fund (or other regulated investment company) "
                    "or in connection with a Form 1099-R. 12. Enter the total of any "
                    "unrecaptured section 1250 gain from sales (including installment sales) or "
                    "other dispositions of section 1250 property held more than 1 year for "
                    "which you didn't make an entry in Part I of Form 4797 for the year of "
                    "sale. 13. Add lines 9 through 12. 14. If you had any section 1202 gain or "
                    "collectibles gain or (loss), enter the total of lines 1 through 4 of the "
                    "28% Rate Gain Worksheet. Otherwise, enter -0-. 15. Enter the (loss), if "
                    "any, from Schedule D, line 7. If Schedule D, line 7, is zero or a gain, "
                    "enter -0-. 16. Enter your long-term capital loss carryovers from Schedule "
                    "D, line 14; and Schedule K-1 (Form 1041), box 11, code D. 17. Combine "
                    "lines 14 through 16. If the result is a (loss), enter it as a positive "
                    "amount. If the result is zero or a gain, enter -0-. 18. Unrecaptured "
                    "section 1250 gain. Subtract line 17 from line 13. If zero or less, enter "
                    "-0-. If more than zero, enter the result here and on Schedule D, line 19."
                ),
                "summary_text": (
                    "v1 sourcing (WALK ITEM 5): lines 1-9 = 0 (no 1040-level Form 4797); line "
                    "10 = 0; line 11 = 1099-DIV box 2b aggregate + the K-1 fact (COMPUTED); "
                    "line 12 = preparer-entered fact; 13 = 9+10+11+12; 14 = w28 lines 1-4 "
                    "total; 15 = ST loss; 16 = LT carryover; 17 = positive-if-loss combine; 18 "
                    "= max(0, 13-17) -> Schedule D line 19."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule D Tax Worksheet lines 1-47 (verbatim, condensed)",
                "location_reference": "i1040sd (2025), Schedule D Tax Worksheet (pages 15-16)",
                "excerpt_text": (
                    "Complete this worksheet only if line 18 or line 19 of Schedule D is more "
                    "than zero and lines 15 and 16 of Schedule D are gains or if you file Form "
                    "4952 and you have an amount on line 4g, even if you don't need to file "
                    "Schedule D. Exception: Don't use the QDCGT Worksheet or this worksheet if: "
                    "line 15 or 16 of Schedule D is zero or less and you have no qualified "
                    "dividends on line 3a; or Form 1040, line 15, is zero or less. 1. Taxable "
                    "income (1040 line 15). 2. Qualified dividends (3a). 3. Form 4952 line 4g. "
                    "4. Form 4952 line 4e. 5. L3-L4 (min 0). 6. L2-L5 (min 0). 7. Smaller of "
                    "Schedule D line 15 or 16. 8. Smaller of L3 or L4. 9. L7-L8 (min 0). 10. "
                    "L6+L9. 11. Schedule D lines 18+19. 12. Smaller of L9 or L11. 13. L10-L12. "
                    "14. L1-L13 (min 0). 15. $48,350 if single or married filing separately; "
                    "$96,700 if married filing jointly or qualifying surviving spouse; $64,750 "
                    "if head of household. 16. Smaller of L1 or L15. 17. Smaller of L14 or L16. "
                    "18. L1-L10 (min 0). 19. Smaller of L1 or: $197,300 if single or married "
                    "filing separately; $394,600 if married filing jointly or qualifying "
                    "surviving spouse; or $197,300 if head of household. 20. Smaller of L14 or "
                    "L19. 21. Larger of L18 or L20. 22. L16-L17. This amount is taxed at 0%. If "
                    "lines 1 and 16 are the same, skip lines 23 through 43 and go to line 44. "
                    "23. Smaller of L1 or L13. 24. L22 (if blank, -0-). 25. L23-L24 (min 0). "
                    "26. $533,400 if single; $300,000 if married filing separately; $600,050 if "
                    "married filing jointly or qualifying surviving spouse; or $566,700 if head "
                    "of household. 27. Smaller of L1 or L26. 28. L21+L22. 29. L27-L28 (min 0). "
                    "30. Smaller of L25 or L29. 31. Multiply line 30 by 15%. 32. L24+L30. If "
                    "lines 1 and 32 are the same, skip lines 33 through 43 and go to line 44. "
                    "33. L23-L32. 34. Multiply line 33 by 20%. If Schedule D, line 19, is zero "
                    "or blank, skip lines 35 through 40 and go to line 41. 35. Smaller of L9 or "
                    "Schedule D line 19. 36. L10+L21. 37. Amount from L1. 38. L36-L37 (min 0). "
                    "39. L35-L38 (min 0). 40. Multiply line 39 by 25%. If Schedule D, line 18, "
                    "is zero or blank, skip lines 41 through 43 and go to line 44. 41. "
                    "L21+L22+L30+L33+L39. 42. L1-L41. 43. Multiply line 42 by 28%. 44. Figure "
                    "the tax on the amount on line 21. If the amount on line 21 is less than "
                    "$100,000, use the Tax Table. If $100,000 or more, use the Tax Computation "
                    "Worksheet. 45. Add lines 31, 34, 40, 43, and 44. 46. Figure the tax on the "
                    "amount on line 1 (same method rule). 47. Tax on all taxable income. Enter "
                    "the smaller of line 45 or line 46. Also include this amount on Form 1040, "
                    "line 16."
                ),
                "summary_text": (
                    "The full 47-line SDTW (Ken Decision 4). Constants: lines 15/26 == the "
                    "Topic 3 QDCGT breakpoints; line 19 == the 32%-bracket start (WALK ITEM 1 "
                    "for 2026). Lines 44/46 use the spine tax method (Tax Table convention "
                    "below $100k). INVARIANT (integrity-checked): D18=D19=0 and no Form 4952 "
                    "-> line 47 == the QDCGT result. The skip rules (1==16, 1==32, D19/D18 "
                    "zero) are load-bearing — SDTW-T4 pins the 1==16 skip."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Capital gain distributions — 1099-DIV boxes 2a/2b/2c/2d routing (verbatim)",
                "location_reference": "i1040sd (2025), Capital Gain Distributions",
                "excerpt_text": (
                    "Enter on Schedule D, line 13, the total capital gain distributions paid to "
                    "you during the year, regardless of how long you held your investment. This "
                    "amount is shown in box 2a of Form 1099-DIV. If there is an amount in box "
                    "2b, include that amount on line 11 of the Unrecaptured Section 1250 Gain "
                    "Worksheet in these instructions if you complete line 19 of Schedule D. If "
                    "there is an amount in box 2c, see Exclusion of Gain on Qualified Small "
                    "Business (QSB) Stock, later. If there is an amount in box 2d, include that "
                    "amount on line 4 of the 28% Rate Gain Worksheet in these instructions if "
                    "you complete line 18 of Schedule D."
                ),
                "summary_text": (
                    "WALK ITEM 8: the Topic 3 stored-field REDs retire/narrow — box 2a -> line "
                    "13 (when Schedule D engaged; else the Exception-1 1040-line-7 path "
                    "remains), box 2b -> u1250_11, box 2d -> w28_4; box 2c RED STAYS "
                    "(D_SCHD_002, §1202 from a RIC)."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_8949_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Form 8949 — Sales and Other Dispositions of Capital Assets",
        "citation": "Form 8949 (2025); f8949.pdf; Attachment Sequence No. 12A",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f8949.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": "2025 12-box revision (verified: the local tts-tax-app manifest copy IS this revision; the 1120-S 192-field map is reusable). Transcribed 2026-06-13 (server/.scratch/f8949_2025_dump.txt).",
        "topics": ["form_8949_reporting"],
        "excerpts": [
            {
                "excerpt_label": "Part I/II structure + the 12-box system (verbatim)",
                "location_reference": "Form 8949 (2025), Parts I-II headers",
                "excerpt_text": (
                    "Before you check Box A, B, C, G, H, or I below, see whether you received "
                    "any Form(s) 1099-B, Form(s) 1099-DA, or substitute statement(s) from your "
                    "broker. You must check Box A, B, C, G, H, or I below. Check only one box. "
                    "If more than one box applies for your short-term transactions, complete a "
                    "separate Form 8949, page 1, for each applicable box. Columns: (a) "
                    "Description of property; (b) Date acquired; (c) Date sold or disposed of; "
                    "(d) Proceeds (sales price); (e) Cost or other basis; (f) Code(s) from "
                    "instructions; (g) Amount of adjustment; (h) Gain or (loss) = (d) - (e) + "
                    "(g). Line 2: Totals. Add the amounts in columns (d), (e), (g), and (h). "
                    "Include on your Schedule D, line 1b (if Box A or Box G above is checked), "
                    "line 2 (if Box B or Box H above is checked), or line 3 (if Box C or Box I "
                    "above is checked). Part II mirrors with Boxes D, E, F, J, K, L and totals "
                    "on line 4 -> Schedule D lines 8b, 9, 10."
                ),
                "summary_text": (
                    "One rendered Part I/II COPY PER BOX (the per-box copies pattern). h = d - "
                    "e + g. Totals flow pairwise to Schedule D. The box governs Part I vs II "
                    "(short/long); a dates-vs-box mismatch is a diagnostic (D_8949_001), the "
                    "box wins (broker-reported)."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_8949_INSTR",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Form 8949 — boxes A-L, Exceptions 1/2, the column (f)/(g) code table",
        "citation": "i8949 (2025)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i8949.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": False,
        "trust_score": 9.00,
        "requires_human_review": False,
        "notes": "All 13 pages transcribed 2026-06-13 (server/.scratch/i8949_2025_dump.txt). The full code table feeds the Decision-5 dropdown data list (the adj_code_* facts).",
        "topics": ["form_8949_reporting"],
        "excerpts": [
            {
                "excerpt_label": "Box definitions A-L incl. digital assets (verbatim, condensed)",
                "location_reference": "i8949 (2025), Specific Instructions, Parts I-II box text",
                "excerpt_text": (
                    "Box A or Box G: all short-term transactions reported to you on Form "
                    "1099-B or Form 1099-DA (or substitute statement) with an amount shown for "
                    "cost or other basis unless the statement indicates that amount wasn't "
                    "reported to the IRS. Box B or Box H: ... without an amount shown for cost "
                    "or other basis or showing that cost or other basis wasn't reported to the "
                    "IRS. Box C or Box I: all short-term transactions for which you can't check "
                    "box A, B, G or H because you didn't receive a Form 1099-B or Form 1099-DA. "
                    "Do not use box C to report digital asset transactions. Use box I. Part II: "
                    "Box D or Box J / Box E or Box K / Box F or Box L mirror the above for "
                    "long-term. Digital asset transactions should not be reported using box C "
                    "or F. Instead, digital asset transactions should be reported using box G, "
                    "H, or I for short-term transactions. Box J, K, or L should be used to "
                    "report long-term transactions."
                ),
                "summary_text": (
                    "WALK ITEM 2: A-F = securities (1099-B), G-L = digital assets (1099-DA), "
                    "NEW for 2025. Routing is pairwise identical — the box is one enum on "
                    "CapitalTransaction. Basis-reported test: 1099-B box 12 / 1099-DA box 2."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Exception 2 — broker summary rows / code M (verbatim)",
                "location_reference": "i8949 (2025), Exceptions to reporting each transaction on a separate row",
                "excerpt_text": (
                    "Exception 2. Instead of reporting each of your transactions on a separate "
                    "row of Part I or II, you can report them on an attached statement "
                    "containing all the same information as Parts I and II and in a similar "
                    "format. Use as many attached statements as you need. Enter the combined "
                    "totals from all your attached statements on Parts I and II with the "
                    "appropriate box checked. For example, report on Part I with box B or box H "
                    "checked all short-term gains and losses from transactions your broker "
                    "reported to you on a statement showing basis wasn't reported to the IRS. "
                    "Enter the name of the broker followed by the words 'see attached "
                    "statement' in column (a). Leave columns (b) and (c) blank. Enter 'M' in "
                    "column (f). If other codes also apply, enter all of them in column (f). "
                    "Enter the totals that apply in columns (d), (e), (g), and (h). If you have "
                    "statements from more than one broker, report the totals from each broker "
                    "on a separate row. Caution: Exception 2 is not available for the election "
                    "to defer eligible gain by investing in a QOF."
                ),
                "summary_text": (
                    "Ken Decision 2: is_summary rows = one row per broker per box, code M, "
                    "columns (b)/(c) blank, attached-statement flag (D_8949_004 reminds). A "
                    "100-transaction statement = one line per box."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Column (f)/(g) mechanics — multi-code + net adjustment (verbatim)",
                "location_reference": "i8949 (2025), Columns (f) and (g)",
                "excerpt_text": (
                    "Enter in column (g) any necessary adjustments to gain (or loss). Enter "
                    "negative amounts in parentheses. Also, enter a code in column (f) to "
                    "explain the adjustment. More than one code: If you entered more than one "
                    "code in column (f) on the same row, enter the net adjustment in column "
                    "(g). For example, if one adjustment is $5,000 and another is ($1,000), "
                    "enter $4,000 ($5,000 - $1,000). [Codes on the same row are listed "
                    "alphabetically with no separators, e.g. 'BOQ'.] Column (h): First, "
                    "subtract the cost or other basis in column (e) from the proceeds (sales "
                    "price) in column (d). Then take into account any adjustments in column "
                    "(g). Enter the gain (or loss) in column (h)."
                ),
                "summary_text": (
                    "h = d - e + g per row; multi-code rows carry ONE net (g) amount, codes "
                    "alphabetical (e.g. 'BW'). An amount in (g) with no code in (f) is invalid "
                    "(D_8949_002)."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Adjustment-code table B..Z (verbatim, condensed per code)",
                "location_reference": "i8949 (2025), How To Complete Form 8949, Columns (f) and (g) (pages 8-11)",
                "excerpt_text": (
                    "B: basis shown in box 1e (1099-B) / box 1g (1099-DA) is incorrect — "
                    "correct it in column (e) with -0- in (g) if basis was NOT reported to the "
                    "IRS (boxes B/E/H/K); if basis WAS reported (boxes A/D/G/J), keep the "
                    "reported basis in (e) and adjust in (g) per the Worksheet for Basis "
                    "Adjustments. C: you disposed of collectibles — enter -0- in (g) [feeds "
                    "the 28% Rate Gain Worksheet line 1]. D: accrued market discount in box "
                    "1f/1h — adjustment per worksheet; also report as interest. E: selling "
                    "expenses, option premiums, or digital asset transaction costs not "
                    "reflected — negative for amounts paid, positive for option premium "
                    "received. H: main-home gain exclusion — excluded gain as a negative "
                    "number. L: nondeductible loss other than a wash sale — positive. M: "
                    "multiple transactions on a single row (Exception 2) — -0- unless another "
                    "code applies. N: received as nominee — offsetting adjustment so (h) is "
                    "zero. O: adjustment not explained elsewhere — appropriate amount. P: "
                    "nonresident alien sale of a U.S. trade/business partnership interest "
                    "(§864(c)(8)). Q: QSB §1202 exclusion — the exclusion as a negative number "
                    "[the 50%/(2/3 of 60%)/(1/3 of 75%) add-back goes on the 28% Rate Gain "
                    "Worksheet line 2]. R: postponing gain (rollover) — postponed gain as a "
                    "negative number. S: §1244 small-business stock loss exceeding the "
                    "ordinary-loss maximum. T: type of gain (term) shown in box 2 / box 6 "
                    "incorrect — report on the correct part, -0- in (g). W: nondeductible "
                    "wash-sale loss — a POSITIVE number in (g). X: DC Zone / qualified "
                    "community asset exclusion — negative. Y: gain previously deferred in a "
                    "QOF now reported. Z: electing to defer eligible gain invested in a QOF. "
                    "[None apply: leave columns (f) and (g) blank.]"
                ),
                "summary_text": (
                    "The Decision-5 dropdown data list (18 codes, authored as the adj_code_* "
                    "facts with sign conventions). Sign pins (D_8949_003): W/L positive; "
                    "H/Q/R/X negative. Y/Z (QOF) = RED-defer (D_SCHD_007); Q checks the 28%-WS "
                    "add-back fact (D_SCHD_009)."
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
            "excerpt_label": "§4.01 32%-bracket starts (SDTW line 19, TY2026 — derived)",
            "location_reference": "Rev. Proc. 2025-32, §4.01 Tables 1-4 (income tax rate tables)",
            "excerpt_text": (
                "For taxable years beginning in 2026, the 24% bracket ends (and the 32% "
                "bracket begins) at: $403,550 for married individuals filing jointly and "
                "surviving spouses (Table 1); $201,750 for heads of households (Table 2); "
                "$201,775 for unmarried individuals (Table 3); and $201,775 for married "
                "individuals filing separately (Table 4). [The same tables the spine's "
                "TAX_BRACKETS transcribes — Ken-verified PM #11.]"
            ),
            "summary_text": (
                "WALK ITEM 1: the 2026 SDTW line-19 amounts are DERIVED from these bracket "
                "tops (the 2025 SDTW line 19 == the 2025 24%-bracket tops, verified "
                "verbatim). Note HOH $201,750 vs single/MFS $201,775 — a $25 asymmetry the "
                "2025 form hides ($197,300 across all three). Re-pin against the published "
                "2026 Schedule D instructions (~Dec 2026)."
            ),
            "is_key_excerpt": True,
        },
    ),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 1 — SCHEDULE_D (Capital Gains and Losses)
# ═══════════════════════════════════════════════════════════════════════════

SCHEDD_IDENTITY = {
    "form_number": "SCHEDULE_D",
    "form_title": "Schedule D (Form 1040) — Capital Gains and Losses (TY2025)",
    "notes": (
        "Sprint Topic 9 (roster #8 + Ken's 5 kickoff decisions 2026-06-13). Real "
        "IRS face, ONE per return. Parts I/II net the per-box Form 8949 totals "
        "(CapitalTransaction document model, Decision 1) with carryover facts "
        "(Decision 3) and 1099-DIV box 2a on line 13; Part III routes line 16 to "
        "Form 1040 line 7a (gain / zero / line-21 limited loss) and selects the "
        "tax worksheet (line 17/20/22: QDCGT vs Schedule D Tax Worksheet vs "
        "ordinary). Lines 1a/8a deliberately UNUSED (walk item 7); lines 4/5/11/12 "
        "direct entry (walk item 4). The worksheets live on the companion "
        "1040_SCHD_WS pseudo-form."
    ),
}

SCHEDD_FACTS: list[dict] = [
    # ── Preparer inputs (return level) ──
    {"fact_key": "schd_qof_disposal", "label": "Page 1 — disposed of any QOF investment during the year (Yes/No)",
     "data_type": "boolean", "sort_order": 1,
     "notes": ("RETURN LEVEL. Three-state nullable (the digital-asset-question idiom); D_SCHD_006 warns while "
               "unanswered on an engaged Schedule D. A Yes pairs with 8949 code Y/Z rows -> D_SCHD_007 RED-defer.")},
    {"fact_key": "schd_st_carryover_prior", "label": "Short-term capital loss carryover from the prior year (positive entry) -> line 6",
     "data_type": "decimal", "default_value": "0", "sort_order": 2,
     "notes": ("RETURN LEVEL. Decision 3: preparer-entered (the 8995 lines-3/7 carryforward pattern). Stored "
               "POSITIVE; enters line 6 as a LOSS (parens on the face, negative in the combine).")},
    {"fact_key": "schd_lt_carryover_prior", "label": "Long-term capital loss carryover from the prior year (positive entry) -> line 14",
     "data_type": "decimal", "default_value": "0", "sort_order": 3,
     "notes": "RETURN LEVEL. Decision 3. Stored POSITIVE; enters line 14 as a LOSS. Also feeds w28_5 / u1250_16."},
    {"fact_key": "schd_files_form_4952", "label": "Files Form 4952 (investment interest expense deduction)",
     "data_type": "boolean", "default_value": "false", "sort_order": 4,
     "notes": ("RETURN LEVEL. True -> D_SCHD_001 RED (the SDTW reads 4952 lines 4g/4e; Form 4952 is not built — "
               "walk item 3). Also flips the line-20 answer to No on the face.")},
    {"fact_key": "schd_other_unrecap_1250", "label": "Unrecaptured §1250 gain from K-1s / other (not 1099-DIV box 2b) -> 1250 WS lines 11-12",
     "data_type": "decimal", "default_value": "0", "sort_order": 5,
     "notes": ("RETURN LEVEL. Walk item 5: the v1 worksheet path is line 11 = 1099-DIV box 2b aggregate "
               "(computed) + this fact; lines 1-9 (Form 4797 path) = 0 — no 1040-level 4797 exists.")},
    {"fact_key": "schd_other_collectibles", "label": "Collectibles gain from K-1s / Form 2439 / other (not 1099-DIV box 2d, not 8949 code C) -> 28% WS lines 3-4",
     "data_type": "decimal", "default_value": "0", "sort_order": 6,
     "notes": "RETURN LEVEL. w28_4 supplement; the 8949 code-C transaction gains/losses are COMPUTED into w28_1."},
    {"fact_key": "schd_1202_exclusion_addback", "label": "§1202 exclusion 28%-group add-back (50% / 2-3 of 60% / 1-3 of 75% exclusions) -> 28% WS line 2",
     "data_type": "decimal", "default_value": "0", "sort_order": 7,
     "notes": ("RETURN LEVEL. Walk item 6: the FRACTION math is OUT — the preparer computes the add-back per the "
               "worksheet text (nothing for 100% exclusions). D_SCHD_009 errors when a code-Q transaction exists "
               "and this fact is unanswered/zero.")},
    # ── Outputs (written by compute) ──
    {"fact_key": "schd_net_st", "label": "Line 7 — net short-term capital gain or (loss) (output)",
     "data_type": "decimal", "sort_order": 20,
     "notes": "OUTPUT. = combine(1a..6 col h). Feeds line 16, w28_6, u1250_15, clc_5/clc_10."},
    {"fact_key": "schd_net_lt", "label": "Line 15 — net long-term capital gain or (loss) (output)",
     "data_type": "decimal", "sort_order": 21,
     "notes": "OUTPUT. = combine(8a..14 col h). Feeds line 16/17, the SDTW line 7, clc_6/clc_9."},
    {"fact_key": "schd_l16", "label": "Line 16 — combined gain or (loss) (output)", "data_type": "decimal", "sort_order": 22,
     "notes": "OUTPUT. = L7 + L15 -> Form 1040 line 7a routing (R-SCHD-1040L7)."},
    {"fact_key": "schd_loss_allowed", "label": "Line 21 — allowed loss (output, negative; limited)", "data_type": "decimal", "sort_order": 23,
     "notes": "OUTPUT. = -min(|L16|, 3000 or 1500 MFS) when L16 < 0. §1211(b) statutory, non-indexed."},
    {"fact_key": "schd_net_capital_gain", "label": "Net capital gain (output) — min(L15, L16) when both gains, else 0",
     "data_type": "decimal", "sort_order": 24,
     "notes": ("OUTPUT. The §1(h)(11)-style net-capital-gain figure the tax worksheets and Form 8995 line 12 "
               "consume (the sibling 8995 spec edit adds it to L12 alongside qualified dividends).")},
    {"fact_key": "schd_carryover_out_st", "label": "Short-term carryover OUT to next year (output, clc_8)",
     "data_type": "decimal", "sort_order": 25,
     "notes": "OUTPUT. Walk item 9: the CLC worksheet year-shifted. Statement display this year; next year's line-6 fact."},
    {"fact_key": "schd_carryover_out_lt", "label": "Long-term carryover OUT to next year (output, clc_13)",
     "data_type": "decimal", "sort_order": 26,
     "notes": "OUTPUT. clc_13. Statement display this year; next year's line-14 fact."},
    {"fact_key": "schd_route", "label": "Line-16 tax route (output): ordinary | qdcgt | sdtw",
     "data_type": "string", "sort_order": 27,
     "notes": ("OUTPUT. The R-SCHD-ROUTE result consumed by route_line_16 (compute_intdiv) — the sibling intdiv "
               "spec edit retires D_INTDIV_002's blocked-path RED.")},
    # ── Constants (traceability) ──
    {"fact_key": "schd_loss_limit", "label": "§1211(b) capital-loss limit ($3,000; $1,500 MFS) — statutory",
     "data_type": "decimal", "sort_order": 40,
     "notes": "CONSTANT. Verbatim on the face (line 21). NON-indexed — never year-key."},
]

SCHEDD_RULES: list[dict] = [
    {"rule_id": "R-SCHD-BOXTOTALS", "title": "Lines 1b/2/3/8b/9/10 — per-box 8949 totals land pairwise",
     "rule_type": "calculation", "precedence": 1, "sort_order": 1,
     "formula": ("For each Schedule D row, columns (d)/(e)/(g)/(h) = the Form 8949 per-box totals: "
                 "1b <- boxes A+G; 2 <- B+H; 3 <- C+I; 8b <- D+J; 9 <- E+K; 10 <- F+L."),
     "inputs": [], "outputs": ["1b_h", "2_h", "3_h", "8b_h", "9_h", "10_h"],
     "description": ("Walk item 2: securities (A-F) and digital-asset (G-L) boxes land pairwise on the SAME "
                     "Schedule D lines. Lines 1a/8a stay blank (walk item 7 — every transaction routes through "
                     "8949, which the face explicitly permits).")},
    {"rule_id": "R-SCHD-CARRYOVER-IN", "title": "Lines 6/14 — prior-year carryover facts enter as losses",
     "rule_type": "calculation", "precedence": 2, "sort_order": 2,
     "formula": "L6 = -schd_st_carryover_prior; L14 = -schd_lt_carryover_prior (stored positive, combined negative; parens on the face).",
     "inputs": ["schd_st_carryover_prior", "schd_lt_carryover_prior"], "outputs": ["6", "14"],
     "description": "Decision 3 (v1 = preparer-entered facts). L14 also feeds w28_5 and u1250_16 as the LT-carryover component."},
    {"rule_id": "R-SCHD-L13-CGD", "title": "Line 13 — capital gain distributions (1099-DIV box 2a) when engaged",
     "rule_type": "calculation", "precedence": 3, "sort_order": 3,
     "formula": ("L13 = sum(DividendIncome.box_2a) when Schedule D is ENGAGED. Box 2b -> u1250_11; box 2d -> "
                 "w28_4; box 2c -> D_SCHD_002 RED. When NOT engaged the Topic 3 Exception-1 path (1040 line 7 + "
                 "the 7b checkbox) is unchanged."),
     "inputs": [], "outputs": ["13"],
     "description": ("Walk item 8. ENGAGE = any CapitalTransaction row OR a nonzero carryover fact OR a nonzero "
                     "direct entry on 4/5/11/12 OR (box-2a distributions when 2b/2d present force the worksheet "
                     "path). The Topic 3 stored-field REDs for 2a/2b/2d retire into these flows; 2c stays RED.")},
    {"rule_id": "R-SCHD-L7-L15", "title": "Lines 7/15 — Part I/II combines", "rule_type": "calculation", "precedence": 4, "sort_order": 4,
     "formula": "L7 = combine(1a..6, col h); L15 = combine(8a..14, col h) -> schd_net_st / schd_net_lt.",
     "inputs": [], "outputs": ["7", "15"],
     "description": "Verbatim face combines. Negative amounts in parentheses on the face; signed in compute."},
    {"rule_id": "R-SCHD-L16-1040L7", "title": "Line 16 -> Form 1040 line 7a routing (gain / zero / loss)",
     "rule_type": "routing", "precedence": 5, "sort_order": 5,
     "formula": ("L16 = L7 + L15. Gain -> 1040 L7a = L16, go to 17. Zero -> 1040 L7a = 0, go to 22. Loss -> skip "
                 "17-20, L21 = -min(|L16|, limit), 1040 L7a = L21, complete 22."),
     "inputs": [], "outputs": ["16", "21"],
     "description": ("The topic's primary cross-form output: Form 1040 line 7a becomes a COMPUTED feeder when "
                     "engaged (override = escape hatch). EIC investment income reads 1040 L7 downstream — flows "
                     "automatically.")},
    {"rule_id": "R-SCHD-L21-LOSSLIMIT", "title": "Line 21 — §1211(b) $3,000/$1,500 capital-loss limitation",
     "rule_type": "calculation", "precedence": 6, "sort_order": 6,
     "formula": "limit = 1500 if MFS else 3000; L21 = -min(|L16|, limit) when L16 < 0. 'Treat both amounts as positive numbers' (face note).",
     "inputs": ["schd_loss_limit"], "outputs": ["21"],
     "description": "Statutory non-indexed. The unused excess goes to the carryover-out worksheet (R-WS-CLC); D_SCHD_005 informs."},
    {"rule_id": "R-SCHD-L17-L20-ROUTE", "title": "Lines 17/18/19/20/22 — tax-worksheet routing",
     "rule_type": "routing", "precedence": 7, "sort_order": 7,
     "formula": ("L17 = (L15 > 0 AND L16 > 0). If L17 No -> L22. If Yes: L18 = w28_7; L19 = u1250_18; L20 = (L18 "
                 "== 0 AND L19 == 0 AND NOT schd_files_form_4952). L20 Yes -> QDCGT; No -> SDTW. Loss/zero path: "
                 "L22 = (1040 line 3a > 0); Yes -> QDCGT; No -> ordinary. -> schd_route."),
     "inputs": ["schd_files_form_4952"], "outputs": ["17", "18", "19", "20", "22"],
     "description": ("The route_line_16 extension (sibling intdiv edit): the Schedule-D path replaces "
                     "D_INTDIV_002's blocked RED. Form 4952 forces line 20 No, but v1 cannot run the SDTW with "
                     "4952 amounts -> D_SCHD_001 RED instead (walk item 3).")},
    {"rule_id": "R-SCHD-DIRECT-ENTRY", "title": "Lines 4/5/11/12 — direct entry (source forms not computed)",
     "rule_type": "routing", "precedence": 8, "sort_order": 8,
     "formula": ("L4 (ST: 6252/4684/6781/8824), L5 (ST K-1), L11 (LT: 4797 Part I/2439/6252/4684/6781/8824), L12 "
                 "(LT K-1) accept preparer direct entry and join the combines verbatim."),
     "inputs": [], "outputs": ["4", "5", "11", "12"],
     "description": ("Walk item 4: Quality Rule 5 (every line direct-entry capable). The preparer keyed a "
                     "manually-computed result — no silent gap; D_SCHD_003/004 inform, D_SCHD_011 warns on L11 "
                     "(possible embedded 1250 gain).")},
    {"rule_id": "R-SCHD-NETCAPGAIN", "title": "Net capital gain output — min(L15, L16) when both gains",
     "rule_type": "calculation", "precedence": 9, "sort_order": 9,
     "formula": "schd_net_capital_gain = min(L15, L16) if (L15 > 0 AND L16 > 0) else 0.",
     "inputs": [], "outputs": [],
     "description": ("Consumed by the SDTW (line 7), and by Form 8995 line 12 (the sibling 8995 spec edit adds "
                     "'+ net capital gain when Schedule D engaged' alongside qualified dividends; D_8995_002 "
                     "retires). i8995 defines net capital gain as qualified dividends + the Schedule D figure.")},
]

SCHEDD_LINES: list[dict] = [
    # Header
    {"line_number": "qof", "description": "Page 1 — QOF disposal question (Yes/No)", "line_type": "input"},
    # Part I — short-term (columns d/e/g/h per row)
    {"line_number": "1a_d", "description": "1a Proceeds — 1099-B/DA basis-reported no-adjustment aggregate (UNUSED v1 — walk item 7)", "line_type": "calculated"},
    {"line_number": "1a_e", "description": "1a Cost (UNUSED v1)", "line_type": "calculated"},
    {"line_number": "1a_h", "description": "1a Gain/(loss) (UNUSED v1)", "line_type": "calculated"},
    {"line_number": "1b_d", "description": "1b Proceeds — 8949 Box A or G totals", "line_type": "calculated"},
    {"line_number": "1b_e", "description": "1b Cost — Box A or G", "line_type": "calculated"},
    {"line_number": "1b_g", "description": "1b Adjustments — Box A or G", "line_type": "calculated"},
    {"line_number": "1b_h", "description": "1b Gain/(loss) — Box A or G", "line_type": "calculated"},
    {"line_number": "2_d", "description": "2 Proceeds — Box B or H totals", "line_type": "calculated"},
    {"line_number": "2_e", "description": "2 Cost — Box B or H", "line_type": "calculated"},
    {"line_number": "2_g", "description": "2 Adjustments — Box B or H", "line_type": "calculated"},
    {"line_number": "2_h", "description": "2 Gain/(loss) — Box B or H", "line_type": "calculated"},
    {"line_number": "3_d", "description": "3 Proceeds — Box C or I totals", "line_type": "calculated"},
    {"line_number": "3_e", "description": "3 Cost — Box C or I", "line_type": "calculated"},
    {"line_number": "3_g", "description": "3 Adjustments — Box C or I", "line_type": "calculated"},
    {"line_number": "3_h", "description": "3 Gain/(loss) — Box C or I", "line_type": "calculated"},
    {"line_number": "4", "description": "4 ST gain from Form 6252; ST gain/(loss) from Forms 4684, 6781, 8824 (direct entry)", "line_type": "input"},
    {"line_number": "5", "description": "5 Net ST gain/(loss) from partnerships, S corps, estates, trusts (K-1; direct entry)", "line_type": "input"},
    {"line_number": "6", "description": "6 ST capital loss carryover (from the carryover fact; entered as a loss)", "line_type": "calculated"},
    {"line_number": "7", "description": "7 Net short-term capital gain or (loss) — combine 1a-6 col (h)", "line_type": "subtotal"},
    # Part II — long-term
    {"line_number": "8a_d", "description": "8a Proceeds — LT basis-reported no-adjustment aggregate (UNUSED v1)", "line_type": "calculated"},
    {"line_number": "8a_e", "description": "8a Cost (UNUSED v1)", "line_type": "calculated"},
    {"line_number": "8a_h", "description": "8a Gain/(loss) (UNUSED v1)", "line_type": "calculated"},
    {"line_number": "8b_d", "description": "8b Proceeds — Box D or J totals", "line_type": "calculated"},
    {"line_number": "8b_e", "description": "8b Cost — Box D or J", "line_type": "calculated"},
    {"line_number": "8b_g", "description": "8b Adjustments — Box D or J", "line_type": "calculated"},
    {"line_number": "8b_h", "description": "8b Gain/(loss) — Box D or J", "line_type": "calculated"},
    {"line_number": "9_d", "description": "9 Proceeds — Box E or K totals", "line_type": "calculated"},
    {"line_number": "9_e", "description": "9 Cost — Box E or K", "line_type": "calculated"},
    {"line_number": "9_g", "description": "9 Adjustments — Box E or K", "line_type": "calculated"},
    {"line_number": "9_h", "description": "9 Gain/(loss) — Box E or K", "line_type": "calculated"},
    {"line_number": "10_d", "description": "10 Proceeds — Box F or L totals", "line_type": "calculated"},
    {"line_number": "10_e", "description": "10 Cost — Box F or L", "line_type": "calculated"},
    {"line_number": "10_g", "description": "10 Adjustments — Box F or L", "line_type": "calculated"},
    {"line_number": "10_h", "description": "10 Gain/(loss) — Box F or L", "line_type": "calculated"},
    {"line_number": "11", "description": "11 Gain from 4797 Part I; LT gain from 2439/6252; LT gain/(loss) from 4684/6781/8824 (direct entry)", "line_type": "input"},
    {"line_number": "12", "description": "12 Net LT gain/(loss) from partnerships, S corps, estates, trusts (K-1; direct entry)", "line_type": "input"},
    {"line_number": "13", "description": "13 Capital gain distributions (1099-DIV box 2a aggregate when engaged)", "line_type": "calculated"},
    {"line_number": "14", "description": "14 LT capital loss carryover (from the carryover fact; entered as a loss)", "line_type": "calculated"},
    {"line_number": "15", "description": "15 Net long-term capital gain or (loss) — combine 8a-14 col (h)", "line_type": "subtotal"},
    # Part III
    {"line_number": "16", "description": "16 Combine lines 7 and 15 -> Form 1040 line 7a routing", "line_type": "total"},
    {"line_number": "17", "description": "17 Are lines 15 and 16 both gains? (Yes/No)", "line_type": "calculated"},
    {"line_number": "18", "description": "18 28% Rate Gain Worksheet line 7 amount", "line_type": "calculated"},
    {"line_number": "19", "description": "19 Unrecaptured Section 1250 Gain Worksheet line 18 amount", "line_type": "calculated"},
    {"line_number": "20", "description": "20 Lines 18/19 both zero AND not filing Form 4952? Yes -> QDCGT / No -> SDTW", "line_type": "calculated"},
    {"line_number": "21", "description": "21 Allowed loss — smaller of the line-16 loss or $3,000 ($1,500 MFS) (negative)", "line_type": "calculated"},
    {"line_number": "22", "description": "22 Qualified dividends on line 3a? Yes -> QDCGT / No -> ordinary", "line_type": "calculated"},
]

SCHEDD_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_SCHD_001", "title": "Form 4952 filed — Schedule D Tax Worksheet with investment-interest amounts not supported", "severity": "error",
     "condition": "schd_files_form_4952 is True (and Schedule D / the tax worksheets are engaged)",
     "message": ("Not supported — prepare manually: Form 4952 (investment interest expense) interacts with the "
                 "Schedule D Tax Worksheet (lines 3/4 read Form 4952 lines 4g/4e) and forces the worksheet even "
                 "without 28%/1250 gain. Form 4952 is not built; compute the tax manually."),
     "notes": "RED-defer (walk item 3). The line-20 answer also flips to No on the face."},
    {"diagnostic_id": "D_SCHD_002", "title": "1099-DIV box 2c (§1202 gain) present — not supported", "severity": "error",
     "condition": "sum(DividendIncome.box_2c) != 0",
     "message": ("Not supported — prepare manually: 1099-DIV box 2c reports §1202 qualified small business stock "
                 "gain from a RIC; its exclusion and 28%-group treatment are not modeled. (Boxes 2a, 2b, and 2d "
                 "now flow to Schedule D line 13 and the worksheets automatically.)"),
     "notes": "Walk item 8: the narrowed survivor of the Topic 3 stored-field REDs."},
    {"diagnostic_id": "D_SCHD_003", "title": "Schedule D line 4/11 direct entry — source forms not computed", "severity": "info",
     "condition": "line 4 != 0 OR line 11 != 0",
     "message": ("Lines 4/11 carry amounts from Forms 6252, 4684, 6781, 8824, 2439, or 4797 Part I, which this "
                 "software does not compute. The entered amounts flow into the netting as keyed — verify the "
                 "source forms manually."),
     "notes": "Walk item 4 (severity for Ken to confirm)."},
    {"diagnostic_id": "D_SCHD_004", "title": "Schedule D line 5/12 K-1 capital gain direct entry", "severity": "info",
     "condition": "line 5 != 0 OR line 12 != 0",
     "message": ("Lines 5/12 carry K-1 capital gains entered directly (no K-1 document model yet). Verify the "
                 "amounts against the Schedule(s) K-1; estate/trust (Form 1041 box 11 code D) loss carryovers "
                 "also affect the 28%/1250 worksheets."),
     "notes": "Walk item 4."},
    {"diagnostic_id": "D_SCHD_005", "title": "Capital loss limited — carryover to next year computed", "severity": "info",
     "condition": "line 16 < 0 AND |line 16| > the line-21 allowed loss",
     "message": ("The net capital loss exceeds the §1211(b) limit ($3,000; $1,500 MFS). Line 21 carries the "
                 "limited loss to Form 1040 line 7a; the Capital Loss Carryover statement shows the short- and "
                 "long-term amounts carrying to next year."),
     "notes": "Pairs with the clc_* worksheet output (walk item 9)."},
    {"diagnostic_id": "D_SCHD_006", "title": "QOF disposal question unanswered", "severity": "warning",
     "condition": "Schedule D engaged AND schd_qof_disposal is None",
     "message": "The qualified opportunity fund disposal question at the top of Schedule D must be answered (Yes or No) on every Schedule D.",
     "notes": "Three-state input; the digital-asset-question precedent (D_1040_017)."},
    {"diagnostic_id": "D_SCHD_007", "title": "QOF deferral election (8949 code Y or Z) — not supported", "severity": "error",
     "condition": "any CapitalTransaction with code Y or Z in adjustment_codes",
     "message": ("Not supported — prepare manually: qualified opportunity fund gain deferral (code Z) and "
                 "previously-deferred QOF gain recognition (code Y) require Form 8997 and per-investment "
                 "reporting (Exception 2 is unavailable). Remove the code or prepare the return manually."),
     "notes": "RED-defer."},
    {"diagnostic_id": "D_SCHD_008", "title": "Schedule D Tax Worksheet route taken — verify the 25%/28% computation", "severity": "info",
     "condition": "schd_route == 'sdtw'",
     "message": ("Line 18 (28% rate gain) or line 19 (unrecaptured §1250 gain) is nonzero, so tax was computed "
                 "on the Schedule D Tax Worksheet (statement attached). Ken: verify the worksheet against the "
                 "source documents — this is the v1 shake-out flag."),
     "notes": "Ken pulled the SDTW in-scope to verify calculations against it (Decision 4); this surfaces every use."},
    {"diagnostic_id": "D_SCHD_009", "title": "§1202 exclusion (code Q) without the 28%-group add-back fact", "severity": "error",
     "condition": "any code-Q transaction AND schd_1202_exclusion_addback == 0",
     "message": ("A §1202 exclusion (code Q) was entered on Form 8949 but the 28% Rate Gain Worksheet line-2 "
                 "add-back is zero. For 50%/60%/75% exclusions, the add-back (the full 50% exclusion, 2/3 of a "
                 "60% exclusion, 1/3 of a 75% exclusion) must be entered; enter 0 only for 100% exclusions — "
                 "confirm by leaving a preparer note."),
     "notes": "Walk item 6 (no-silent-gap on the 28% group). The fraction math itself is OUT of v1."},
    {"diagnostic_id": "D_SCHD_010", "title": "TY2026 SDTW line-19 threshold is derived — re-pin when IRS publishes", "severity": "info",
     "condition": "tax_year == 2026 AND schd_route == 'sdtw'",
     "message": ("The 2026 Schedule D Tax Worksheet has not been published; line 19 uses the 32%-bracket start "
                 "derived from Rev. Proc. 2025-32 §4.01 ($201,775 single/MFS, $403,550 MFJ/QSS, $201,750 HOH). "
                 "Re-verify when the IRS releases the 2026 Schedule D instructions (~Dec 2026)."),
     "notes": "Walk item 1; joins the Tax Table re-pin standing obligation."},
    {"diagnostic_id": "D_SCHD_011", "title": "Line 11 may contain unrecaptured §1250 gain — worksheet fact required", "severity": "warning",
     "condition": "line 11 != 0",
     "message": ("Line 11 (4797 Part I / 2439 / 6252 gains) was entered directly. If any of it is unrecaptured "
                 "§1250 gain, enter that amount in the 'Unrecaptured §1250 from K-1s/other' fact — the worksheet "
                 "lines 1-9 (the Form 4797 path) are not computed in v1."),
     "notes": "Walk item 5 (no-silent-gap on the 25% group)."},
]

SCHEDD_SCENARIOS: list[dict] = [
    {"scenario_name": "D-T1 — short-term only gain (ordinary route)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "filing_status": "single",
                "box_a_totals": {"d": 50000, "e": 42000, "g": 0}},
     "expected_outputs": {"line_1b_h": 8000, "line_7": 8000, "line_15": 0, "line_16": 8000,
                          "f1040_line_7a": 8000, "line_17": False, "schd_route": "ordinary",
                          "schd_net_capital_gain": 0},
     "notes": "L17 No (L15 not a gain) -> line 22; no qualified dividends -> ordinary rates (no worksheet)."},
    {"scenario_name": "D-T2 — long-term gain (QDCGT route)", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"tax_year": 2025, "filing_status": "single",
                "box_d_totals": {"d": 70000, "e": 50000, "g": 0}},
     "expected_outputs": {"line_8b_h": 20000, "line_15": 20000, "line_16": 20000, "line_17": True,
                          "line_18": 0, "line_19": 0, "line_20": True, "schd_route": "qdcgt",
                          "f1040_line_7a": 20000, "schd_net_capital_gain": 20000},
     "notes": "Both gains, 18/19 zero, no 4952 -> the Topic 3 QDCGT worksheet (line-16 tax path)."},
    {"scenario_name": "D-T3 — net loss beyond the limit (single)", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"tax_year": 2025, "filing_status": "single", "f1040_line_15": 50000,
                "box_a_totals": {"d": 20000, "e": 28500, "g": 0}},
     "expected_outputs": {"line_7": -8500, "line_16": -8500, "line_21": -3000, "f1040_line_7a": -3000,
                          "schd_carryover_out_st": 5500, "schd_carryover_out_lt": 0, "D_SCHD_005": True},
     "notes": "§1211(b): allowed -3,000; CLC-out ws5=8,500, ws7=3,000 -> ST carryover 5,500 (clc_8)."},
    {"scenario_name": "D-T4 — MFS loss limit $1,500", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"tax_year": 2025, "filing_status": "mfs", "f1040_line_15": 40000,
                "box_a_totals": {"d": 10000, "e": 12000, "g": 0}},
     "expected_outputs": {"line_16": -2000, "line_21": -1500, "f1040_line_7a": -1500,
                          "schd_carryover_out_st": 500},
     "notes": "MFS limit 1,500 (statutory). CLC-out: ws2=1,500, ws4=1,500, ws5=2,000, ws8=500."},
    {"scenario_name": "D-T5 — ST loss nets against LT gain", "scenario_type": "normal", "sort_order": 5,
     "inputs": {"tax_year": 2025, "filing_status": "single",
                "box_a_totals": {"d": 30000, "e": 35000, "g": 0},
                "box_d_totals": {"d": 40000, "e": 28000, "g": 0}},
     "expected_outputs": {"line_7": -5000, "line_15": 12000, "line_16": 7000, "line_17": True,
                          "line_20": True, "schd_route": "qdcgt", "f1040_line_7a": 7000,
                          "schd_net_capital_gain": 7000},
     "notes": "Netting: min(L15, L16) = 7,000 = the 8995-L12 / QDCGT net-capital-gain figure."},
    {"scenario_name": "D-T6 — carryover facts enter lines 6/14", "scenario_type": "normal", "sort_order": 6,
     "inputs": {"tax_year": 2025, "filing_status": "single",
                "schd_st_carryover_prior": 2000, "schd_lt_carryover_prior": 1000,
                "box_d_totals": {"d": 25000, "e": 15000, "g": 0}},
     "expected_outputs": {"line_6": -2000, "line_7": -2000, "line_14": -1000, "line_15": 9000,
                          "line_16": 7000, "f1040_line_7a": 7000},
     "notes": "Decision 3: facts stored positive, enter as losses. L15 = 10,000 - 1,000 = 9,000; L16 = 7,000."},
    {"scenario_name": "D-T7 — cap-gain distributions on line 13 (engaged)", "scenario_type": "normal", "sort_order": 7,
     "inputs": {"tax_year": 2025, "filing_status": "single",
                "schd_st_carryover_prior": 500, "div_box_2a_total": 4000},
     "expected_outputs": {"line_6": -500, "line_7": -500, "line_13": 4000, "line_15": 4000,
                          "line_16": 3500, "f1040_line_7a": 3500},
     "notes": "Walk item 8: the carryover engages Schedule D, so box 2a lands on line 13 (NOT the Topic 3 Exception-1 1040-line-7 path)."},
    {"scenario_name": "D-T8 — unrecaptured 1250 via 1099-DIV box 2b (SDTW route)", "scenario_type": "normal", "sort_order": 8,
     "inputs": {"tax_year": 2025, "filing_status": "single",
                "box_d_totals": {"d": 60000, "e": 40000, "g": 0},
                "div_box_2a_total": 10000, "div_box_2b_total": 5000},
     "expected_outputs": {"line_13": 10000, "line_15": 30000, "line_16": 30000, "line_17": True,
                          "line_18": 0, "line_19": 5000, "line_20": False, "schd_route": "sdtw",
                          "D_SCHD_008": True},
     "notes": "u1250: lines 1-10 = 0, 11 = 5,000 (box 2b), 13 = 5,000, 17 = 0, 18 = 5,000 -> D19 -> SDTW."},
    {"scenario_name": "D-T9 — collectibles (code C) -> 28% worksheet (SDTW route)", "scenario_type": "normal", "sort_order": 9,
     "inputs": {"tax_year": 2025, "filing_status": "single",
                "transactions": [{"box": "F", "d": 20000, "e": 12000, "codes": "C", "g": 0}]},
     "expected_outputs": {"line_10_h": 8000, "line_15": 8000, "line_16": 8000, "line_17": True,
                          "line_18": 8000, "line_19": 0, "line_20": False, "schd_route": "sdtw"},
     "notes": "w28_1 = 8,000 (code-C rows, computed), w28_7 = 8,000 -> D18 -> SDTW."},
    {"scenario_name": "D-T10 — line 16 exactly zero", "scenario_type": "edge_case", "sort_order": 10,
     "inputs": {"tax_year": 2025, "filing_status": "single",
                "box_a_totals": {"d": 30000, "e": 25000, "g": 0},
                "box_d_totals": {"d": 10000, "e": 15000, "g": 0}},
     "expected_outputs": {"line_7": 5000, "line_15": -5000, "line_16": 0, "f1040_line_7a": 0,
                          "line_21": 0, "schd_route": "ordinary"},
     "notes": "Zero -> 7a = 0, skip 17-21, line 22 (no qualified dividends here -> ordinary)."},
    {"scenario_name": "D-G1 — Form 4952 fires the RED", "scenario_type": "diagnostic", "sort_order": 11,
     "inputs": {"tax_year": 2025, "filing_status": "single", "schd_files_form_4952": True,
                "box_d_totals": {"d": 30000, "e": 20000, "g": 0}},
     "expected_outputs": {"line_20": False, "D_SCHD_001": True},
     "notes": "Walk item 3: the SDTW needs 4952 lines 4g/4e — unbuilt -> RED, never a silently-wrong worksheet."},
    {"scenario_name": "D-G2 — QOF code Z fires the RED", "scenario_type": "diagnostic", "sort_order": 12,
     "inputs": {"tax_year": 2025, "filing_status": "single",
                "transactions": [{"box": "C", "d": 50000, "e": 30000, "codes": "Z", "g": -20000}]},
     "expected_outputs": {"D_SCHD_007": True},
     "notes": "QOF deferral elections (Form 8997, per-investment reporting) are RED-defer."},
]

SCHEDD_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-SCHD-BOXTOTALS", "IRS_2025_SCHEDD_FORM", "primary", "Lines 1b/2/3/8b/9/10 per-box text (A/G, B/H, C/I, D/J, E/K, F/L)"),
    ("R-SCHD-BOXTOTALS", "IRS_2025_8949_FORM", "secondary", "8949 line 2/4 totals -> Schedule D routing text"),
    ("R-SCHD-CARRYOVER-IN", "IRS_2025_SCHEDD_INSTR", "primary", "Capital Loss Carryover Worksheet lines 8/13 -> Schedule D lines 6/14"),
    ("R-SCHD-L13-CGD", "IRS_2025_SCHEDD_INSTR", "primary", "Capital Gain Distributions — box 2a -> line 13; 2b/2d -> worksheets"),
    ("R-SCHD-L7-L15", "IRS_2025_SCHEDD_FORM", "primary", "Lines 7/15 combine text"),
    ("R-SCHD-L16-1040L7", "IRS_2025_SCHEDD_FORM", "primary", "Line 16 routing bullets -> Form 1040 line 7a"),
    ("R-SCHD-L21-LOSSLIMIT", "IRS_2025_SCHEDD_FORM", "primary", "Line 21 — ($3,000)/($1,500) smaller-of text + positive-numbers note"),
    ("R-SCHD-L17-L20-ROUTE", "IRS_2025_SCHEDD_FORM", "primary", "Lines 17/18/19/20/22 routing text"),
    ("R-SCHD-L17-L20-ROUTE", "IRS_2025_SCHEDD_INSTR", "secondary", "Lines 18/19 worksheet requirements; SDTW entry conditions"),
    ("R-SCHD-DIRECT-ENTRY", "IRS_2025_SCHEDD_FORM", "primary", "Lines 4/5/11/12 source-form text"),
    ("R-SCHD-NETCAPGAIN", "IRS_2025_SCHEDD_INSTR", "secondary", "SDTW line 7 (smaller of 15/16); 8995 L12 consumer noted"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 2 — 1040_SCHD_WS (the four i1040sd worksheets, computational pseudo-form)
# ═══════════════════════════════════════════════════════════════════════════

def _ws_lines(prefix: str, texts: dict[int, str]) -> list[dict]:
    """All worksheet lines are calculated; descriptions transcribed."""
    return [
        {"line_number": f"{prefix}_{n}", "description": t, "line_type": "calculated"}
        for n, t in texts.items()
    ]


_SDTW_TEXT = {
    1: "Taxable income (Form 1040 line 15)",
    2: "Qualified dividends (Form 1040 line 3a)",
    3: "Form 4952 line 4g (v1: 0 — Form 4952 is D_SCHD_001 RED)",
    4: "Form 4952 line 4e (v1: 0)",
    5: "L3 - L4 (not less than 0)",
    6: "L2 - L5 (not less than 0)",
    7: "Smaller of Schedule D line 15 or line 16",
    8: "Smaller of L3 or L4",
    9: "L7 - L8 (not less than 0)",
    10: "L6 + L9",
    11: "Schedule D lines 18 + 19",
    12: "Smaller of L9 or L11",
    13: "L10 - L12",
    14: "L1 - L13 (not less than 0)",
    15: "Maximum zero-rate amount ($48,350 single/MFS; $96,700 MFJ/QSS; $64,750 HOH — 2025; year-keyed == QDCGT)",
    16: "Smaller of L1 or L15",
    17: "Smaller of L14 or L16",
    18: "L1 - L10 (not less than 0)",
    19: "Smaller of L1 or the 32%-bracket start ($197,300 single/MFS/HOH; $394,600 MFJ/QSS — 2025; year-keyed)",
    20: "Smaller of L14 or L19",
    21: "Larger of L18 or L20",
    22: "L16 - L17 — taxed at 0%. (If L1 == L16, skip lines 23-43, go to line 44)",
    23: "Smaller of L1 or L13",
    24: "L22 (blank -> 0)",
    25: "L23 - L24 (not less than 0)",
    26: "Maximum 15%-rate amount ($533,400 single; $300,000 MFS; $600,050 MFJ/QSS; $566,700 HOH — 2025; year-keyed == QDCGT)",
    27: "Smaller of L1 or L26",
    28: "L21 + L22",
    29: "L27 - L28 (not less than 0)",
    30: "Smaller of L25 or L29",
    31: "L30 x 15%",
    32: "L24 + L30. (If L1 == L32, skip lines 33-43, go to line 44)",
    33: "L23 - L32",
    34: "L33 x 20%",
    35: "Smaller of L9 or Schedule D line 19 (skip 35-40 when D19 is zero/blank)",
    36: "L10 + L21",
    37: "Amount from L1",
    38: "L36 - L37 (not less than 0)",
    39: "L35 - L38 (not less than 0)",
    40: "L39 x 25% (unrecaptured §1250 — statutory rate)",
    41: "L21 + L22 + L30 + L33 + L39 (skip 41-43 when D18 is zero/blank)",
    42: "L1 - L41",
    43: "L42 x 28% (collectibles/§1202 group — statutory rate)",
    44: "Tax on L21 (Tax Table < $100,000; Tax Computation Worksheet >= $100,000 — the spine method)",
    45: "L31 + L34 + L40 + L43 + L44",
    46: "Tax on L1 (same method rule)",
    47: "Smaller of L45 or L46 -> Form 1040 line 16",
}

_CLC_TEXT = {
    1: "Form 1040 line 15 (this year), negative allowed (parenthesized if it would be a loss)",
    2: "Loss from Schedule D line 21 (this year) as a positive amount",
    3: "Combine L1 and L2 (not less than 0)",
    4: "Smaller of L2 or L3",
    5: "Loss from Schedule D line 7 as a positive amount (0 if line 7 not a loss)",
    6: "Gain from Schedule D line 15 (0 if a loss)",
    7: "L4 + L6",
    8: "SHORT-TERM carryover to next year = L5 - L7 (not less than 0) -> next year's Schedule D line 6",
    9: "Loss from Schedule D line 15 as a positive amount (0 if line 15 not a loss)",
    10: "Gain from Schedule D line 7 (0 if a loss)",
    11: "L4 - L5 (not less than 0)",
    12: "L10 + L11",
    13: "LONG-TERM carryover to next year = L9 - L12 (not less than 0) -> next year's Schedule D line 14",
}

_W28_TEXT = {
    1: "Collectibles gain/(loss) from Form 8949 Part II code-C rows (COMPUTED from the transactions)",
    2: "§1202 exclusion add-back, positive (50% / 2-3 of 60% / 1-3 of 75%; nothing for 100%) — preparer fact",
    3: "Collectibles gain/(loss) from 4684/6252/6781/8824 (v1: included in the K-1/other fact)",
    4: "Collectibles gain from 1099-DIV box 2d (COMPUTED) + 2439 box 1d / K-1 (the K-1/other fact)",
    5: "LT capital loss carryover from Schedule D line 14 (+ 1041 K-1 box 11 code D) — entered as a loss",
    6: "Schedule D line 7 loss, if a loss (entered as a loss)",
    7: "Combine 1-6; if more than zero -> Schedule D line 18 (else 0)",
}

_U1250_TEXT = {
    1: "Form 4797 §1250: smaller of 4797 line 22 or 24 (v1: 0 — no 1040-level Form 4797)",
    2: "Form 4797 line 26g for that property (v1: 0)",
    3: "L1 - L2 (v1: 0)",
    4: "Installment-sale unrecaptured 1250 from Form 6252 lines 26/37 (v1: 0)",
    5: "K-1 (partnership/S corp) unrecaptured 1250 included via Form 4797 (v1: 0)",
    6: "L3 + L4 + L5 (v1: 0)",
    7: "Smaller of L6 or the Form 4797 line 7 gain (v1: 0)",
    8: "Form 4797 line 8 amount (v1: 0)",
    9: "L7 - L8 (not less than 0) (v1: 0)",
    10: "Partnership-interest sale gain attributable to unrecaptured 1250 (v1: 0)",
    11: "Unrecaptured 1250 reported on K-1 / 1099-DIV box 2b / 2439 (COMPUTED: box-2b aggregate + the K-1 fact)",
    12: "Unrecaptured 1250 from dispositions with no 4797 Part I entry in the sale year (preparer fact share)",
    13: "L9 + L10 + L11 + L12",
    14: "28% Rate Gain Worksheet lines 1-4 total (0 if no 1202/collectibles items)",
    15: "Schedule D line 7 loss, if a loss (entered as a loss)",
    16: "LT capital loss carryover from Schedule D line 14 (entered as a loss)",
    17: "Combine 14-16; if a loss, enter as a positive amount (else 0)",
    18: "Unrecaptured section 1250 gain = L13 - L17 (not less than 0) -> Schedule D line 19",
}

SCHDWS_IDENTITY = {
    "form_number": "1040_SCHD_WS",
    "form_title": "Schedule D worksheets (1040) — SDTW + Capital Loss Carryover + 28% Rate Gain + Unrecaptured §1250 (TY2025)",
    "notes": (
        "Sprint Topic 9 companion computational pseudo-form (the 1040_INTDIV ws_* "
        "precedent). Renders as STATEMENT pages, never a faked IRS face. Four "
        "worksheets transcribed line-by-line from i1040sd 2025: sdtw_1..47 (Ken "
        "Decision 4 — IN scope), clc_1..13 (the carryover-OUT computation, walk "
        "item 9), w28_1..7, u1250_1..18 (v1 sourcing per walk item 5). Constants: "
        "sdtw_15/26 == the Topic 3 QDCGT breakpoints (cross-spec identity); "
        "sdtw_19 == the 32%-bracket start (walk item 1 for TY2026)."
    ),
}

SCHDWS_FACTS: list[dict] = [
    {"fact_key": "ws_sdtw_zero_rate_max", "label": "SDTW line 15 — maximum zero-rate amounts (year-keyed; == QDCGT ZERO_RATE_MAX)",
     "data_type": "decimal", "sort_order": 1,
     "notes": ("CONSTANT, YEAR-KEYED. 2025: 48,350 single/MFS / 96,700 MFJ-QSS / 64,750 HOH (SDTW verbatim; RP "
               "2024-40 §2.03). 2026: 49,450 / 98,900 / 66,200 (RP 2025-32 §4.03). MUST equal the Topic 3 QDCGT "
               "constants — integrity-checked + FA-1040-SCHD-06.")},
    {"fact_key": "ws_sdtw_rate15_max", "label": "SDTW line 26 — maximum 15%-rate amounts (year-keyed; == QDCGT RATE15_MAX)",
     "data_type": "decimal", "sort_order": 2,
     "notes": ("CONSTANT, YEAR-KEYED. 2025: 533,400 / 300,000 MFS / 600,050 MFJ-QSS / 566,700 HOH (SDTW verbatim). "
               "2026: 545,500 / 306,850 / 613,700 / 579,600. single != MFS on this one.")},
    {"fact_key": "ws_sdtw_bracket32_start", "label": "SDTW line 19 — 32%-bracket start (year-keyed; == spine bracket tops)",
     "data_type": "decimal", "sort_order": 3,
     "notes": ("CONSTANT, YEAR-KEYED. 2025: 197,300 single/MFS/HOH / 394,600 MFJ-QSS (SDTW verbatim == RP 2024-40 "
               "§2.01 24%-bracket tops). 2026 DERIVED from RP 2025-32 §4.01: 201,775 single/MFS / 403,550 MFJ-QSS "
               "/ 201,750 HOH ($25 HOH asymmetry). WALK ITEM 1 — re-pin ~Dec 2026 (D_SCHD_010).")},
    {"fact_key": "ws_rate_1250", "label": "Unrecaptured §1250 cap rate — 25% statutory", "data_type": "decimal", "sort_order": 4,
     "notes": "CONSTANT. §1(h); SDTW line 40 verbatim. NON-indexed — never year-key."},
    {"fact_key": "ws_rate_28", "label": "Collectibles/§1202 group cap rate — 28% statutory", "data_type": "decimal", "sort_order": 5,
     "notes": "CONSTANT. §1(h); SDTW line 43 verbatim. NON-indexed."},
]

SCHDWS_RULES: list[dict] = [
    {"rule_id": "R-WS-SDTW-ENTRY", "title": "SDTW entry/exception conditions", "rule_type": "routing", "precedence": 1, "sort_order": 1,
     "formula": ("Run the SDTW only when (D18 > 0 OR D19 > 0) AND D15 > 0 AND D16 > 0 (the Form 4952 trigger is "
                 "D_SCHD_001 RED instead). Exception: if (D15 <= 0 or D16 <= 0) and no qualified dividends, or "
                 "1040 L15 <= 0 -> neither worksheet (ordinary)."),
     "inputs": [], "outputs": [],
     "description": "Verbatim SDTW header. Pairs with R-SCHD-L17-L20-ROUTE (line 20 No -> SDTW)."},
    {"rule_id": "R-WS-SDTW-PARTITION", "title": "SDTW lines 1-22 — income partition + 0% amount", "rule_type": "calculation", "precedence": 2, "sort_order": 2,
     "formula": ("L5 = max(0, L3-L4); L6 = max(0, L2-L5); L7 = min(D15, D16); L8 = min(L3, L4); L9 = max(0, "
                 "L7-L8); L10 = L6+L9; L11 = D18+D19; L12 = min(L9, L11); L13 = L10-L12; L14 = max(0, L1-L13); "
                 "L16 = min(L1, L15const); L17 = min(L14, L16); L18 = max(0, L1-L10); L19 = min(L1, B32const); "
                 "L20 = min(L14, L19); L21 = max(L18, L20); L22 = L16-L17 (taxed at 0%)."),
     "inputs": ["ws_sdtw_zero_rate_max", "ws_sdtw_bracket32_start"], "outputs": [],
     "description": "Verbatim lines 1-22. SKIP RULE (load-bearing, pinned by SDTW-T4): if L1 == L16, skip 23-43 -> line 44."},
    {"rule_id": "R-WS-SDTW-15-20", "title": "SDTW lines 23-34 — 15% and 20% amounts", "rule_type": "calculation", "precedence": 3, "sort_order": 3,
     "formula": ("L23 = min(L1, L13); L24 = L22; L25 = max(0, L23-L24); L27 = min(L1, L26const); L28 = L21+L22; "
                 "L29 = max(0, L27-L28); L30 = min(L25, L29); L31 = L30 x 15%; L32 = L24+L30 (if L1 == L32 skip "
                 "33-43); L33 = L23-L32; L34 = L33 x 20%."),
     "inputs": ["ws_sdtw_rate15_max"], "outputs": [],
     "description": "Verbatim lines 23-34; the 15%/20% preferential blocks."},
    {"rule_id": "R-WS-SDTW-25-28", "title": "SDTW lines 35-43 — 25% (1250) and 28% blocks", "rule_type": "calculation", "precedence": 4, "sort_order": 4,
     "formula": ("D19 zero -> skip 35-40. L35 = min(L9, D19); L36 = L10+L21; L37 = L1; L38 = max(0, L36-L37); "
                 "L39 = max(0, L35-L38); L40 = L39 x 25%. D18 zero -> skip 41-43. L41 = L21+L22+L30+L33+L39; "
                 "L42 = L1-L41; L43 = L42 x 28%."),
     "inputs": ["ws_rate_1250", "ws_rate_28"], "outputs": [],
     "description": ("Verbatim 35-43. The 25%/28% groups are CAP rates — when the ordinary bracket is lower, the "
                     "gain rides line 44's ordinary tax (SDTW-T2 pins L43 = 0 at a 24% bracket; SDTW-T3 pins the "
                     "28% rate binding at a 37% bracket)."),},
    {"rule_id": "R-WS-SDTW-TAX", "title": "SDTW lines 44-47 — ordinary tax + smaller-of", "rule_type": "calculation", "precedence": 5, "sort_order": 5,
     "formula": ("L44 = tax(L21) [Tax Table < $100k, TCW >= $100k — the spine method, Topic 1 convention]; L45 = "
                 "L31+L34+L40+L43+L44; L46 = tax(L1); L47 = min(L45, L46) -> Form 1040 line 16."),
     "inputs": [], "outputs": [],
     "description": ("Verbatim 44-47. INVARIANT (integrity-checked): D18 = D19 = 0 and no 4952 -> L47 == the "
                     "QDCGT result. The build reuses the spine tax method exactly (the Topic 3 WS22/24 precedent).")},
    {"rule_id": "R-WS-CLC", "title": "Capital Loss Carryover — the carryover-OUT computation (year-shifted)", "rule_type": "calculation", "precedence": 6, "sort_order": 6,
     "formula": ("clc_1 = 1040 L15 (negative allowed); clc_2 = |D21|; clc_3 = max(0, clc_1+clc_2); clc_4 = "
                 "min(clc_2, clc_3); D7 loss -> clc_5 = |D7|, clc_6 = max(0, D15), clc_7 = clc_4+clc_6, clc_8 = "
                 "max(0, clc_5-clc_7) [ST out]; D15 loss -> clc_9 = |D15|, clc_10 = max(0, D7), clc_11 = max(0, "
                 "clc_4-clc_5), clc_12 = clc_10+clc_11, clc_13 = max(0, clc_9-clc_12) [LT out]."),
     "inputs": [], "outputs": [],
     "description": ("Walk item 9: the published worksheet figures PRIOR->CURRENT carryovers; applied with THIS "
                     "year's D7/D15/D21 + 1040 L15 it yields next year's (the Line 21 instruction defers to next "
                     "year's worksheet / Pub 550 — same math). Statement only; runs when D16 is a loss. clc_1 uses "
                     "the WOULD-BE-NEGATIVE line 15 (compute it before the floor)."),},
    {"rule_id": "R-WS-28RATE", "title": "28% Rate Gain Worksheet lines 1-7", "rule_type": "calculation", "precedence": 7, "sort_order": 7,
     "formula": ("w28_1 = sum(code-C transaction col h, Part II); w28_2 = schd_1202_exclusion_addback; w28_3 = 0 "
                 "v1; w28_4 = sum(DIV box 2d) + schd_other_collectibles; w28_5 = -(L14 carryover); w28_6 = "
                 "min(0, D7); w28_7 = max(0, sum(1..6)) -> Schedule D line 18."),
     "inputs": ["schd_1202_exclusion_addback", "schd_other_collectibles"], "outputs": [],
     "description": "Verbatim 1-7 with the v1 sourcing map (walk items 5/6). w28_1 is COMPUTED from the code-C rows."},
    {"rule_id": "R-WS-U1250", "title": "Unrecaptured §1250 Gain Worksheet lines 1-18 (v1 path)", "rule_type": "calculation", "precedence": 8, "sort_order": 8,
     "formula": ("u1250_1..10 = 0 (no 1040-level Form 4797 — v1); u1250_11 = sum(DIV box 2b) + "
                 "schd_other_unrecap_1250; u1250_12 = 0 v1 (folded into the fact); u1250_13 = sum(9..12); "
                 "u1250_14 = w28_1+w28_2+w28_3+w28_4; u1250_15 = min(0, D7); u1250_16 = -(L14 carryover); "
                 "u1250_17 = max(0, -(u1250_14+u1250_15+u1250_16)); u1250_18 = max(0, u1250_13-u1250_17) -> "
                 "Schedule D line 19."),
     "inputs": ["schd_other_unrecap_1250"], "outputs": [],
     "description": "Verbatim with the v1 zero-path for lines 1-10 (walk item 5; D_SCHD_011 guards line-11 direct entries)."},
]

SCHDWS_LINES: list[dict] = (
    _ws_lines("sdtw", _SDTW_TEXT)
    + _ws_lines("clc", _CLC_TEXT)
    + _ws_lines("w28", _W28_TEXT)
    + _ws_lines("u1250", _U1250_TEXT)
)

SCHDWS_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_SCHD_W01", "title": "SDTW computed — statement page attached", "severity": "info",
     "condition": "the SDTW ran (line 20 No path)",
     "message": "Tax was computed on the Schedule D Tax Worksheet; the 47-line statement page is attached after Schedule D. Reached lines only.",
     "notes": "Statement-render gate mirror (the QDCGT statement precedent)."},
]

SCHDWS_SCENARIOS: list[dict] = [
    {"scenario_name": "SDTW-T1 — 1250 gain at a 32% bracket (25% binds partially)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "filing_status": "single", "taxable_income": 250000,
                "qualified_dividends": 10000, "schd_15": 60000, "schd_16": 60000,
                "schd_18": 0, "schd_19": 20000},
     "expected_outputs": {"sdtw_10": 70000, "sdtw_13": 50000, "sdtw_14": 200000, "sdtw_21": 197300,
                          "sdtw_22": 0, "sdtw_30": 50000, "sdtw_31": 7500, "sdtw_35": 20000,
                          "sdtw_38": 17300, "sdtw_39": 2700, "sdtw_40": 675, "sdtw_44": 40199,
                          "sdtw_45": 48374, "sdtw_46": 57063, "sdtw_47": 48374},
     "notes": ("Hand-verified + model-verified (.scratch/topic9_pins.py). 50,000 at 15% = 7,500; only 2,700 of "
               "the 20,000 1250 gain is taxed at 25% (675) — the rest rides the brackets; L44 TCW(197,300) = "
               "40,199.00 exact.")},
    {"scenario_name": "SDTW-T2 — collectibles at a 24% bracket (28% cap does NOT bind)", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"tax_year": 2025, "filing_status": "single", "taxable_income": 150000,
                "qualified_dividends": 0, "schd_15": 30000, "schd_16": 30000,
                "schd_18": 8000, "schd_19": 0},
     "expected_outputs": {"sdtw_12": 8000, "sdtw_13": 22000, "sdtw_21": 128000, "sdtw_30": 22000,
                          "sdtw_31": 3300, "sdtw_41": 150000, "sdtw_42": 0, "sdtw_43": 0,
                          "sdtw_44": 23567, "sdtw_45": 26867, "sdtw_46": 28847, "sdtw_47": 26867},
     "notes": ("The 28% rate is a CAP: at a 24% ordinary bracket the collectibles gain lands in L21's ordinary "
               "tax (L42 = 0, L43 = 0). 22,000 at 15% = 3,300; TCW(128,000) = 23,567.00.")},
    {"scenario_name": "SDTW-T3 — collectibles at a 37% bracket (28% cap BINDS)", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"tax_year": 2025, "filing_status": "single", "taxable_income": 700000,
                "qualified_dividends": 0, "schd_15": 100000, "schd_16": 100000,
                "schd_18": 100000, "schd_19": 0},
     "expected_outputs": {"sdtw_13": 0, "sdtw_21": 600000, "sdtw_30": 0, "sdtw_31": 0,
                          "sdtw_41": 600000, "sdtw_42": 100000, "sdtw_43": 28000,
                          "sdtw_44": 179547.25, "sdtw_45": 207547.25, "sdtw_46": 216020.25,
                          "sdtw_47": 207547.25},
     "notes": ("All 100,000 collectibles gain taxed at 28% (28,000) vs 35/37% ordinary — the cap saves ~8,473. "
               "TCW(600,000) = 179,547.25 exact.")},
    {"scenario_name": "SDTW-T4 — TI at the 0% breakpoint (the 1==16 skip rule)", "scenario_type": "edge_case", "sort_order": 4,
     "inputs": {"tax_year": 2025, "filing_status": "single", "taxable_income": 40000,
                "qualified_dividends": 0, "schd_15": 10000, "schd_16": 10000,
                "schd_18": 0, "schd_19": 2000},
     "expected_outputs": {"sdtw_16": 40000, "sdtw_21": 32000, "sdtw_22": 8000,
                          "sdtw_31": 0, "sdtw_40": 0, "sdtw_43": 0,
                          "sdtw_44": 3605, "sdtw_45": 3605, "sdtw_46": 4565, "sdtw_47": 3605},
     "notes": ("LOAD-BEARING SKIP PIN: L1 (40,000) == L16 -> lines 23-43 SKIPPED — even the 1250 gain produces "
               "no 25% tax (absorbed below the 0% breakpoint). L44 = Tax Table convention: band [32,000-32,050) "
               "midpoint 32,025 -> 3,604.50 -> 3,605 HALF-UP; L46 = table(40,000) = 4,565.")},
    {"scenario_name": "CLC-T1 — mixed ST/LT carryover out", "scenario_type": "normal", "sort_order": 5,
     "inputs": {"tax_year": 2025, "f1040_line_15_signed": 1200, "schd_7": -4000, "schd_15": -6000,
                "schd_16": -10000, "schd_21_loss_pos": 3000},
     "expected_outputs": {"clc_3": 4200, "clc_4": 3000, "clc_5": 4000, "clc_7": 3000, "clc_8": 1000,
                          "clc_9": 6000, "clc_11": 0, "clc_12": 0, "clc_13": 6000},
     "notes": "Model-verified: 10,000 loss, 3,000 used -> 7,000 out (1,000 ST + 6,000 LT; ST absorbed first)."},
    {"scenario_name": "CLC-T2 — would-be-negative taxable income caps the usage", "scenario_type": "edge_case", "sort_order": 6,
     "inputs": {"tax_year": 2025, "f1040_line_15_signed": -2000, "schd_7": -5000, "schd_15": 0,
                "schd_16": -5000, "schd_21_loss_pos": 3000},
     "expected_outputs": {"clc_1": -2000, "clc_3": 1000, "clc_4": 1000, "clc_8": 4000, "clc_13": 0},
     "notes": ("clc_1 takes the WOULD-BE-NEGATIVE line 15 (-2,000): only 1,000 of the 3,000 allowed loss was "
               "absorbed -> 4,000 carries (not 2,000). The floor-before-worksheet bug this pins is the classic one.")},
    {"scenario_name": "W28-T1 — code-C collectibles net of carryover and ST loss", "scenario_type": "normal", "sort_order": 7,
     "inputs": {"tax_year": 2025, "code_c_total": 8000, "s1202_addback": 0, "div_2d_total": 0,
                "lt_carryover": 1000, "schd_7": -2000},
     "expected_outputs": {"w28_1": 8000, "w28_5": -1000, "w28_6": -2000, "w28_7": 5000},
     "notes": "Model-verified: 8,000 - 1,000 - 2,000 = 5,000 -> Schedule D line 18."},
    {"scenario_name": "U1250-T1 — DIV box 2b path with an ST-loss offset", "scenario_type": "normal", "sort_order": 8,
     "inputs": {"tax_year": 2025, "div_2b_total": 5000, "other_unrecap_1250": 0, "w28_1_4_total": 0,
                "schd_7": -1000, "lt_carryover": 0},
     "expected_outputs": {"u1250_11": 5000, "u1250_13": 5000, "u1250_15": -1000, "u1250_17": 1000,
                          "u1250_18": 4000},
     "notes": "Model-verified: the ST loss reduces the 1250 gain through line 17 (5,000 - 1,000 = 4,000)."},
]

SCHDWS_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-WS-SDTW-ENTRY", "IRS_2025_SCHEDD_INSTR", "primary", "SDTW header — entry conditions + the Exception"),
    ("R-WS-SDTW-PARTITION", "IRS_2025_SCHEDD_INSTR", "primary", "SDTW lines 1-22 verbatim"),
    ("R-WS-SDTW-15-20", "IRS_2025_SCHEDD_INSTR", "primary", "SDTW lines 23-34 verbatim"),
    ("R-WS-SDTW-15-20", "RP_2025_32", "secondary", "§4.03 TY2026 15%-max amounts (reused QDCGT constants)"),
    ("R-WS-SDTW-25-28", "IRS_2025_SCHEDD_INSTR", "primary", "SDTW lines 35-43 verbatim (25%/28% statutory rates)"),
    ("R-WS-SDTW-TAX", "IRS_2025_SCHEDD_INSTR", "primary", "SDTW lines 44-47 verbatim (Tax Table/TCW method rule)"),
    ("R-WS-CLC", "IRS_2025_SCHEDD_INSTR", "primary", "Capital Loss Carryover Worksheet lines 1-13 + the Line 21 carryover-to-next-year instruction"),
    ("R-WS-28RATE", "IRS_2025_SCHEDD_INSTR", "primary", "28% Rate Gain Worksheet lines 1-7 verbatim"),
    ("R-WS-U1250", "IRS_2025_SCHEDD_INSTR", "primary", "Unrecaptured §1250 Gain Worksheet lines 1-18 verbatim"),
    ("R-WS-SDTW-PARTITION", "RP_2025_32", "secondary", "§4.01 32%-bracket starts (sdtw_19 TY2026 — walk item 1)"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 3 — 8949 (RE-AUTHORED over the thin 1120-S-era draft)
# ═══════════════════════════════════════════════════════════════════════════

F8949_IDENTITY = {
    "form_number": "8949",
    "form_title": "Form 8949 — Sales and Other Dispositions of Capital Assets (TY2025)",
    "notes": (
        "Sprint Topic 9 RE-AUTHOR (the 8995 _retire_stale precedent — the prior "
        "spec was a thin 1120-S-era draft: 4 unnamed rules / 12 column lines / 10 "
        "nameless facts / 3 generic diagnostics, all retired by keep-set). Real "
        "2025 face: the TWELVE box system (A-F securities/1099-B + G-L digital "
        "assets/1099-DA — walk item 2), one Part I/II copy per box, columns "
        "(a)-(h) with h = d - e + g, the full i8949 column-(f) code table as the "
        "adj_code_* data-list facts (Ken Decision 5 — the input dropdown), "
        "Exception-2 broker-summary rows (Decision 2, code M), per-box totals -> "
        "Schedule D lines 1b/2/3/8b/9/10. The 1040 input is the NEW "
        "CapitalTransaction document model (Decision 1); entity_types stays "
        "multi-entity — the 1120-S render path (192-field map) is untouched "
        "(walk item 10)."
    ),
}

# The CapitalTransaction document surface (Decision 1) + the code data list.
F8949_FACTS: list[dict] = [
    # ── CapitalTransaction model surface (PER TRANSACTION) ──
    {"fact_key": "ct_owner", "label": "Owner — taxpayer / spouse / joint", "data_type": "string", "sort_order": 1,
     "notes": "PER TRANSACTION. Decision 1. MFS splits and future per-spouse analysis; no compute effect on MFJ."},
    {"fact_key": "ct_description", "label": "Column (a) — description of property (e.g., 100 sh. XYZ Co.)", "data_type": "string", "sort_order": 2,
     "notes": "PER TRANSACTION. Summary rows: broker name + 'see attached statement' (Exception 2)."},
    {"fact_key": "ct_date_acquired", "label": "Column (b) — date acquired (or VARIOUS / INHERITED)", "data_type": "string", "sort_order": 3,
     "notes": "PER TRANSACTION. String to honor the form's VARIOUS/INHERITED literals; blank on summary rows. D_8949_005 requires it on per-lot rows."},
    {"fact_key": "ct_date_sold", "label": "Column (c) — date sold or disposed of", "data_type": "string", "sort_order": 4,
     "notes": "PER TRANSACTION. Blank on summary rows (Exception 2: columns (b)/(c) blank)."},
    {"fact_key": "ct_proceeds", "label": "Column (d) — proceeds (sales price)", "data_type": "decimal", "default_value": "0", "sort_order": 5,
     "notes": "PER TRANSACTION."},
    {"fact_key": "ct_basis", "label": "Column (e) — cost or other basis", "data_type": "decimal", "default_value": "0", "sort_order": 6,
     "notes": "PER TRANSACTION."},
    {"fact_key": "ct_adjustment_codes", "label": "Column (f) — adjustment code(s), alphabetical, no separators (e.g., 'BW')", "data_type": "string", "sort_order": 7,
     "notes": "PER TRANSACTION. Decision 5: dropdown(s) sourced from the adj_code_* data list; multi-code allowed. Unknown letters -> D_8949_002."},
    {"fact_key": "ct_adjustment_amount", "label": "Column (g) — amount of adjustment (signed; net when multi-code)", "data_type": "decimal", "default_value": "0", "sort_order": 8,
     "notes": "PER TRANSACTION. ONE net amount per row (i8949 'More than one code'). Sign conventions per code -> D_8949_003."},
    {"fact_key": "ct_box", "label": "8949 box — A/B/C (ST 1099-B), G/H/I (ST 1099-DA), D/E/F (LT 1099-B), J/K/L (LT 1099-DA)", "data_type": "string", "sort_order": 9,
     "notes": ("PER TRANSACTION. The box GOVERNS Part I vs II (short/long) — broker-reported; a dates-vs-box "
               "mismatch is D_8949_001 (box wins). Basis-reported test: 1099-B box 12 / 1099-DA box 2.")},
    {"fact_key": "ct_is_summary", "label": "Broker-summary totals row (Exception 2)", "data_type": "boolean", "default_value": "false", "sort_order": 10,
     "notes": "PER TRANSACTION. Decision 2: code M auto-applies; columns (b)/(c) blank; one row per broker per box."},
    {"fact_key": "ct_statement_attached", "label": "Summary row — broker statement attached", "data_type": "boolean", "default_value": "false", "sort_order": 11,
     "notes": "PER TRANSACTION (summary rows). Exception 2 requires the statement (Form 8453 if e-filing); D_8949_004 reminds."},
    {"fact_key": "ct_import_confirmed", "label": "Imported summary row confirmed by preparer (Exception 2)", "data_type": "boolean", "default_value": "false", "sort_order": 12,
     "notes": ("PER TRANSACTION. YELLOW/imported provenance: a brokerage-imported Exception-2 summary row starts "
               "UNCONFIRMED (False) and must be preparer-reviewed before filing — D_8949_006. Manually-entered "
               "(GREEN) rows are created confirmed. Mirrors tts CapitalTransaction.import_confirmed (brokerage_1099b.py, mig 0160).")},
    # ── The i8949 column-(f) code table (Decision 5 — cited data list) ──
    {"fact_key": "adj_code_B", "label": "B — Basis shown on Form 1099-B/1099-DA is incorrect", "data_type": "string", "sort_order": 20,
     "notes": "DATA LIST. Basis NOT reported (B/E/H/K): correct (e), 0 in (g). Basis reported (A/D/G/J): keep reported (e), adjust in (g) per the Basis Adjustments worksheet. Sign: either."},
    {"fact_key": "adj_code_C", "label": "C — Disposed of collectibles", "data_type": "string", "sort_order": 21,
     "notes": "DATA LIST. (g) = 0. Part II code-C rows feed the 28% Rate Gain Worksheet line 1 (COMPUTED)."},
    {"fact_key": "adj_code_D", "label": "D — Accrued market discount (box 1f/1h)", "data_type": "string", "sort_order": 22,
     "notes": "DATA LIST. Adjustment per the Accrued Market Discount worksheet (negative); the discount is reported as interest income. Wash-sale interplay -> also code W."},
    {"fact_key": "adj_code_E", "label": "E — Selling expenses / option premiums / digital-asset transaction costs not reflected", "data_type": "string", "sort_order": 23,
     "notes": "DATA LIST. Sign: negative for amounts paid; positive for option premium received."},
    {"fact_key": "adj_code_H", "label": "H — Main-home sale gain exclusion (§121)", "data_type": "string", "sort_order": 24,
     "notes": "DATA LIST. Sign: NEGATIVE (the excluded gain). Part II; pairs with code E for selling expenses (the i8949 'EH' example)."},
    {"fact_key": "adj_code_L", "label": "L — Nondeductible loss (other than a wash sale)", "data_type": "string", "sort_order": 25,
     "notes": "DATA LIST. Sign: POSITIVE (offsets the loss; 1099-K personal-property loss zero-out is the canonical use)."},
    {"fact_key": "adj_code_M", "label": "M — Multiple transactions on a single row (Exception 2 summary)", "data_type": "string", "sort_order": 26,
     "notes": "DATA LIST. (g) = 0 unless another code applies. AUTO-APPLIED to is_summary rows (Decision 2)."},
    {"fact_key": "adj_code_N", "label": "N — Received as nominee for the actual owner", "data_type": "string", "sort_order": 27,
     "notes": "DATA LIST. Offsetting adjustment so column (h) nets to zero."},
    {"fact_key": "adj_code_O", "label": "O — Adjustment not explained by another code", "data_type": "string", "sort_order": 28,
     "notes": "DATA LIST. Sign: any. Also the contingent-payment-debt-instrument adjustment (the code-T tip)."},
    {"fact_key": "adj_code_P", "label": "P — NRA sale of a U.S. trade/business partnership interest (§864(c)(8))", "data_type": "string", "sort_order": 29,
     "notes": "DATA LIST. Rare; Schedule P interplay. Selectable; no engine math beyond the (g) amount."},
    {"fact_key": "adj_code_Q", "label": "Q — QSB stock §1202 exclusion", "data_type": "string", "sort_order": 30,
     "notes": "DATA LIST. Sign: NEGATIVE. The 50%/(2-3 of 60%)/(1-3 of 75%) 28%-group add-back is the schd_1202_exclusion_addback fact (walk item 6; D_SCHD_009)."},
    {"fact_key": "adj_code_R", "label": "R — Postponed gain (rollover, e.g. QSB §1045)", "data_type": "string", "sort_order": 31,
     "notes": "DATA LIST. Sign: NEGATIVE (the postponed gain)."},
    {"fact_key": "adj_code_S", "label": "S — §1244 small-business stock loss exceeding the ordinary-loss maximum", "data_type": "string", "sort_order": 32,
     "notes": "DATA LIST. See the Schedule D instructions (the ordinary portion goes to Form 4797 — outside v1; the capital remainder reports here)."},
    {"fact_key": "adj_code_T", "label": "T — Type of gain (term) shown in box 2 / box 6 is incorrect", "data_type": "string", "sort_order": 33,
     "notes": "DATA LIST. Report on the CORRECT part; (g) = 0 absent other adjustments."},
    {"fact_key": "adj_code_W", "label": "W — Nondeductible wash-sale loss", "data_type": "string", "sort_order": 34,
     "notes": "DATA LIST. Sign: POSITIVE (the disallowed loss). SUPPORTED as entered (kickoff: wash sales IN); no auto-detection across lots."},
    {"fact_key": "adj_code_X", "label": "X — DC Zone / qualified community asset gain exclusion", "data_type": "string", "sort_order": 35,
     "notes": "DATA LIST. Sign: NEGATIVE."},
    {"fact_key": "adj_code_Y", "label": "Y — QOF gain previously deferred, now reported", "data_type": "string", "sort_order": 36,
     "notes": "DATA LIST. RED-defer: selecting it fires D_SCHD_007 (Form 8997 reporting not built)."},
    {"fact_key": "adj_code_Z", "label": "Z — Electing to defer eligible gain invested in a QOF", "data_type": "string", "sort_order": 37,
     "notes": "DATA LIST. RED-defer: D_SCHD_007 (Exception 2 unavailable; Form 8997 required)."},
]

F8949_RULES: list[dict] = [
    {"rule_id": "R-8949-BOX", "title": "Box routing — A-L govern Part I/II and the Schedule D landing line",
     "rule_type": "routing", "precedence": 1, "sort_order": 1,
     "formula": ("Part I (short): A/B/C (1099-B) + G/H/I (1099-DA). Part II (long): D/E/F + J/K/L. One rendered "
                 "Part I/II copy per box in use. Landing: A+G -> Sch D 1b; B+H -> 2; C+I -> 3; D+J -> 8b; E+K -> "
                 "9; F+L -> 10. Digital assets never use box C or F (use I / L)."),
     "inputs": ["ct_box"], "outputs": [],
     "description": "Walk item 2. The box governs term; D_8949_001 flags a dates-vs-box mismatch (box wins, broker-reported)."},
    {"rule_id": "R-8949-COLH", "title": "Column (h) = (d) - (e) + (g) per row", "rule_type": "calculation", "precedence": 2, "sort_order": 2,
     "formula": "ct_gain_loss = ct_proceeds - ct_basis + ct_adjustment_amount (signed; negative in parens on the face).",
     "inputs": ["ct_proceeds", "ct_basis", "ct_adjustment_amount"], "outputs": [],
     "description": "Verbatim column-(h) math. The i8949 Example 3: 6,000 - 2,000 + (-1,000) = 3,000."},
    {"rule_id": "R-8949-CODES", "title": "Column (f)/(g) — codes alphabetical, ONE net adjustment, sign conventions",
     "rule_type": "validation", "precedence": 3, "sort_order": 3,
     "formula": ("Valid letters: B C D E H L M N O P Q R S T W X Y Z (the adj_code_* data list). Multi-code rows "
                 "list codes alphabetically with no separators and carry the NET amount in (g). An amount in (g) "
                 "requires a code (D_8949_002). Sign pins: W/L positive; H/Q/R/X negative (D_8949_003). Y/Z -> "
                 "D_SCHD_007 RED."),
     "inputs": ["ct_adjustment_codes", "ct_adjustment_amount"], "outputs": [],
     "description": "Decision 5: the dropdown renders each code with its definition ('W — Wash sale...'). Code C contributes to w28_1; code M marks summaries."},
    {"rule_id": "R-8949-SUMMARY", "title": "Exception-2 broker-summary rows (code M)", "rule_type": "routing", "precedence": 4, "sort_order": 4,
     "formula": ("is_summary -> code M auto; columns (b)/(c) blank; description = broker + 'see attached "
                 "statement'; one row per broker per box; totals in (d)/(e)/(g)/(h). Not available for QOF "
                 "deferral elections."),
     "inputs": ["ct_is_summary", "ct_statement_attached"], "outputs": [],
     "description": "Decision 2: a 100-transaction statement = one row per box. D_8949_004 reminds about the attached statement."},
    {"rule_id": "R-8949-TOTALS", "title": "Line 2 / line 4 per-box totals -> Schedule D", "rule_type": "calculation", "precedence": 5, "sort_order": 5,
     "formula": ("Per box in use: totals(d, e, g, h) over that box's rows -> the paired Schedule D line "
                 "(R-SCHD-BOXTOTALS). Line 2 = Part I totals; line 4 = Part II totals."),
     "inputs": [], "outputs": ["2", "4"],
     "description": "Verbatim face totals text. The build leg derives these from the CapitalTransaction rows per box."},
]

F8949_LINES: list[dict] = [
    # Part I (short-term)
    {"line_number": "p1_box", "description": "Part I — box checked (A/B/C/G/H/I; one copy per box)", "line_type": "input"},
    {"line_number": "p1_col_a", "description": "Part I col (a) — description of property", "line_type": "input"},
    {"line_number": "p1_col_b", "description": "Part I col (b) — date acquired (VARIOUS/INHERITED ok; blank on summaries)", "line_type": "input"},
    {"line_number": "p1_col_c", "description": "Part I col (c) — date sold or disposed of", "line_type": "input"},
    {"line_number": "p1_col_d", "description": "Part I col (d) — proceeds", "line_type": "input"},
    {"line_number": "p1_col_e", "description": "Part I col (e) — cost or other basis", "line_type": "input"},
    {"line_number": "p1_col_f", "description": "Part I col (f) — code(s) from instructions", "line_type": "input"},
    {"line_number": "p1_col_g", "description": "Part I col (g) — amount of adjustment (net)", "line_type": "input"},
    {"line_number": "p1_col_h", "description": "Part I col (h) — gain/(loss) = (d) - (e) + (g)", "line_type": "calculated"},
    {"line_number": "2_d", "description": "Line 2 totals col (d) -> Sch D 1b/2/3 per box", "line_type": "subtotal"},
    {"line_number": "2_e", "description": "Line 2 totals col (e)", "line_type": "subtotal"},
    {"line_number": "2_g", "description": "Line 2 totals col (g)", "line_type": "subtotal"},
    {"line_number": "2_h", "description": "Line 2 totals col (h)", "line_type": "subtotal"},
    # Part II (long-term)
    {"line_number": "p2_box", "description": "Part II — box checked (D/E/F/J/K/L; one copy per box)", "line_type": "input"},
    {"line_number": "p2_col_a", "description": "Part II col (a) — description of property", "line_type": "input"},
    {"line_number": "p2_col_b", "description": "Part II col (b) — date acquired", "line_type": "input"},
    {"line_number": "p2_col_c", "description": "Part II col (c) — date sold or disposed of", "line_type": "input"},
    {"line_number": "p2_col_d", "description": "Part II col (d) — proceeds", "line_type": "input"},
    {"line_number": "p2_col_e", "description": "Part II col (e) — cost or other basis", "line_type": "input"},
    {"line_number": "p2_col_f", "description": "Part II col (f) — code(s) from instructions", "line_type": "input"},
    {"line_number": "p2_col_g", "description": "Part II col (g) — amount of adjustment (net)", "line_type": "input"},
    {"line_number": "p2_col_h", "description": "Part II col (h) — gain/(loss) = (d) - (e) + (g)", "line_type": "calculated"},
    {"line_number": "4_d", "description": "Line 4 totals col (d) -> Sch D 8b/9/10 per box", "line_type": "subtotal"},
    {"line_number": "4_e", "description": "Line 4 totals col (e)", "line_type": "subtotal"},
    {"line_number": "4_g", "description": "Line 4 totals col (g)", "line_type": "subtotal"},
    {"line_number": "4_h", "description": "Line 4 totals col (h)", "line_type": "subtotal"},
]

F8949_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_8949_001", "title": "Holding period (dates) conflicts with the box term", "severity": "warning",
     "condition": "per-lot row where the date-derived term (<= 1 year vs > 1 year) contradicts the box's Part (I vs II)",
     "message": ("The acquisition/sale dates imply a different holding period than the checked box's part "
                 "(short vs long). The box governs (it is broker-reported — code T exists for a wrong-term "
                 "1099); verify the dates or the box."),
     "notes": "Re-authors the old D003. VARIOUS/INHERITED dates skip the check."},
    {"diagnostic_id": "D_8949_002", "title": "Adjustment amount without a code (or an unknown code letter)", "severity": "error",
     "condition": "ct_adjustment_amount != 0 AND ct_adjustment_codes is blank; OR any letter not in the 18-code list",
     "message": ("Column (g) carries an adjustment but column (f) has no valid code. Every adjustment needs an "
                 "explaining code from the Form 8949 instructions; pick it from the dropdown."),
     "notes": "i8949: 'Also, enter a code in column (f) to explain the adjustment.'"},
    {"diagnostic_id": "D_8949_003", "title": "Adjustment sign contradicts the code convention", "severity": "error",
     "condition": "single-code rows: W or L with (g) < 0; H, Q, R, or X with (g) > 0",
     "message": ("The adjustment sign is wrong for this code: wash-sale (W) and nondeductible-loss (L) "
                 "adjustments are POSITIVE; exclusions and postponements (H, Q, R, X) are NEGATIVE. Multi-code "
                 "rows carry a net amount and are not sign-checked."),
     "notes": "Sign pins from the i8949 code table. Single-code rows only (multi-code nets can be either sign)."},
    {"diagnostic_id": "D_8949_004", "title": "Summary row without the attached broker statement flag", "severity": "info",
     "condition": "ct_is_summary AND NOT ct_statement_attached",
     "message": ("Exception-2 summary rows require an attached statement with the per-transaction detail (Form "
                 "8453 transmittal if e-filing). Confirm the broker statement is attached and set the flag."),
     "notes": "Decision 2 companion."},
    {"diagnostic_id": "D_8949_005", "title": "Per-lot row missing dates", "severity": "error",
     "condition": "NOT ct_is_summary AND (date acquired blank OR date sold blank)",
     "message": ("A per-transaction row needs both dates (column (b) accepts VARIOUS or INHERITED). Only "
                 "Exception-2 summary rows leave the date columns blank."),
     "notes": "MeF-readiness: structured dates on per-lot rows."},
    {"diagnostic_id": "D_8949_006", "title": "Imported 8949 summary row not yet confirmed", "severity": "error",
     "condition": "ct_is_summary AND the row is imported (YELLOW provenance) AND NOT ct_import_confirmed",
     "message": ("A brokerage-imported Exception-2 summary row (code M) has not been confirmed by the preparer. "
                 "An imported summary row starts UNCONFIRMED and must be reviewed against the broker statement "
                 "before the return is filed. Imported (YELLOW) rows only — manually-entered (GREEN) rows are "
                 "untouched. Review the row and set the confirmation flag."),
     "notes": ("Mandatory pre-file confirm gate (SEASON_PLAN item 5; tts c25635f, mig 0160). Ref brokerage_1099b.py, "
               "CapitalTransaction.import_confirmed. Imported/YELLOW provenance rows only; GREEN manual rows untouched.")},
]

F8949_SCENARIOS: list[dict] = [
    {"scenario_name": "F8949-T1 — box A per-lot rows total to Sch D 1b", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "transactions": [
         {"box": "A", "d": 30000, "e": 26000, "codes": "", "g": 0},
         {"box": "A", "d": 20000, "e": 16000, "codes": "", "g": 0}]},
     "expected_outputs": {"line_2_d": 50000, "line_2_e": 42000, "line_2_g": 0, "line_2_h": 8000,
                          "schd_line": "1b"},
     "notes": "h per row: 4,000 + 4,000. Box A -> Schedule D line 1b (pairs with D-T1)."},
    {"scenario_name": "F8949-T2 — code W wash sale zeroes the loss", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"tax_year": 2025, "transactions": [
         {"box": "B", "d": 10000, "e": 12000, "codes": "W", "g": 2000}]},
     "expected_outputs": {"col_h": 0, "line_2_h": 0, "D_8949_003": False},
     "notes": "h = 10,000 - 12,000 + 2,000 = 0. W positive (the disallowed loss) — entered, not auto-detected."},
    {"scenario_name": "F8949-T3 — Exception-2 summary row (code M)", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"tax_year": 2025, "transactions": [
         {"box": "H", "is_summary": True, "statement_attached": True,
          "description": "Fidelity — see attached statement", "d": 150000, "e": 140000, "codes": "M", "g": 0}]},
     "expected_outputs": {"col_b": "", "col_c": "", "col_h": 10000, "line_2_h": 10000, "schd_line": "2"},
     "notes": "Decision 2: one row per broker per box; columns (b)/(c) blank; box H (DA basis-not-reported) -> Sch D line 2."},
    {"scenario_name": "F8949-T4 — multi-code 'BW' net adjustment", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"tax_year": 2025, "transactions": [
         {"box": "A", "d": 9000, "e": 10000, "codes": "BW", "g": 1500}]},
     "expected_outputs": {"col_h": 500, "sign_check_applied": False},
     "notes": "Codes alphabetical, ONE net (g) (i8949 'More than one code'); multi-code rows skip D_8949_003."},
    {"scenario_name": "F8949-T5 — box G digital asset (basis reported)", "scenario_type": "normal", "sort_order": 5,
     "inputs": {"tax_year": 2025, "transactions": [
         {"box": "G", "d": 12000, "e": 10000, "codes": "", "g": 0}]},
     "expected_outputs": {"col_h": 2000, "schd_line": "1b"},
     "notes": "Walk item 2: box G (1099-DA, ST, basis reported) lands on the SAME Schedule D line 1b as box A."},
    {"scenario_name": "F8949-G1 — adjustment without a code fires the error", "scenario_type": "diagnostic", "sort_order": 6,
     "inputs": {"tax_year": 2025, "transactions": [
         {"box": "C", "d": 5000, "e": 3000, "codes": "", "g": -500}]},
     "expected_outputs": {"D_8949_002": True},
     "notes": "An amount in (g) with a blank (f) is invalid."},
]

F8949_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-8949-BOX", "IRS_2025_8949_INSTR", "primary", "Box A-L definitions + the digital-asset box rule (use I/L, never C/F)"),
    ("R-8949-BOX", "IRS_2025_8949_FORM", "secondary", "Part I/II 'check only one box' + per-box copies"),
    ("R-8949-COLH", "IRS_2025_8949_FORM", "primary", "Column (h) = (d) - (e) + (g) face text"),
    ("R-8949-CODES", "IRS_2025_8949_INSTR", "primary", "The columns (f)/(g) code table (pages 8-11) + 'More than one code'"),
    ("R-8949-SUMMARY", "IRS_2025_8949_INSTR", "primary", "Exception 2 — code M, columns (b)/(c) blank, per-broker rows"),
    ("R-8949-TOTALS", "IRS_2025_8949_FORM", "primary", "Lines 2/4 totals -> Schedule D 1b/2/3/8b/9/10 text"),
]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY FORM LINKS  (source_code, form_code, link_type)
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_SCHEDD_FORM", "SCHEDULE_D", "governs"),
    ("IRS_2025_SCHEDD_INSTR", "SCHEDULE_D", "informs"),
    ("IRS_2025_SCHEDD_INSTR", "1040_SCHD_WS", "governs"),
    ("RP_2025_32", "1040_SCHD_WS", "informs"),
    ("RP_2024_40", "1040_SCHD_WS", "informs"),
    ("IRS_2025_8949_FORM", "8949", "governs"),
    ("IRS_2025_8949_INSTR", "8949", "governs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORMS ROSTER
# ═══════════════════════════════════════════════════════════════════════════

FORMS: list[dict] = [
    {"identity": SCHEDD_IDENTITY, "facts": SCHEDD_FACTS, "rules": SCHEDD_RULES, "lines": SCHEDD_LINES,
     "diagnostics": SCHEDD_DIAGNOSTICS, "scenarios": SCHEDD_SCENARIOS, "rule_links": SCHEDD_RULE_LINKS},
    {"identity": SCHDWS_IDENTITY, "facts": SCHDWS_FACTS, "rules": SCHDWS_RULES, "lines": SCHDWS_LINES,
     "diagnostics": SCHDWS_DIAGNOSTICS, "scenarios": SCHDWS_SCENARIOS, "rule_links": SCHDWS_RULE_LINKS},
    {"identity": F8949_IDENTITY, "facts": F8949_FACTS, "rules": F8949_RULES, "lines": F8949_LINES,
     "diagnostics": F8949_DIAGNOSTICS, "scenarios": F8949_SCENARIOS, "rule_links": F8949_RULE_LINKS},
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS  (staged in tts-tax-app until the assertions leg)
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-SCHD-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "8949 per-box totals land pairwise on Schedule D 1b/2/3/8b/9/10",
     "description": ("Validates R-8949-TOTALS/R-SCHD-BOXTOTALS. A+G -> 1b; B+H -> 2; C+I -> 3; D+J -> 8b; E+K -> "
                     "9; F+L -> 10 (columns d/e/g/h). Bug it catches: digital-asset boxes routed to their own "
                     "lines, or a box's totals dropped."),
     "definition": {"kind": "flow_assertion", "form": "8949",
                    "checks": [{"source": "boxes A+G totals", "must_write_to": ["SCHEDULE_D.1b"]},
                               {"source": "boxes B+H totals", "must_write_to": ["SCHEDULE_D.2"]},
                               {"source": "boxes C+I totals", "must_write_to": ["SCHEDULE_D.3"]},
                               {"source": "boxes D+J totals", "must_write_to": ["SCHEDULE_D.8b"]},
                               {"source": "boxes E+K totals", "must_write_to": ["SCHEDULE_D.9"]},
                               {"source": "boxes F+L totals", "must_write_to": ["SCHEDULE_D.10"]}]},
     "sort_order": 1},
    {"assertion_id": "FA-1040-SCHD-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Schedule D combines: L7 = sum(1a..6 h); L15 = sum(8a..14 h); L16 = L7 + L15",
     "description": ("Validates R-SCHD-L7-L15/R-SCHD-L16-1040L7. Carryover facts enter NEGATIVE on 6/14. Bug it "
                     "catches: carryovers added instead of subtracted, or a direct-entry line (4/5/11/12) "
                     "dropped from the combine."),
     "definition": {"kind": "formula_check", "form": "SCHEDULE_D",
                    "formula": "line_7 == sum(h: 1a,1b,2,3,4,5,6); line_15 == sum(h: 8a,8b,9,10,11,12,13,14); line_16 == line_7 + line_15"},
     "sort_order": 2},
    {"assertion_id": "FA-1040-SCHD-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Line 16 -> Form 1040 line 7a routing + the §1211(b) loss limit",
     "description": ("Gain -> 7a = L16; zero -> 7a = 0; loss -> 7a = L21 = -min(|L16|, 3000 or 1500 MFS). "
                     "Statutory NON-indexed constants. Bug it catches: the unlimited loss reaching 7a, or an "
                     "'inflation-adjusted' limit."),
     "definition": {"kind": "formula_check", "form": "SCHEDULE_D",
                    "formula": "f1040_7a == line_16 if line_16 >= 0 else -min(abs(line_16), limit)",
                    "constants": {"limit": 3000, "limit_mfs": 1500, "applies_to_years": [2025, 2026]}},
     "sort_order": 3},
    {"assertion_id": "FA-1040-SCHD-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Carryover facts -> lines 6/14; the CLC-out worksheet computes next year's amounts",
     "description": ("Validates R-SCHD-CARRYOVER-IN/R-WS-CLC. clc_8 = max(0, clc_5 - clc_7); clc_13 = max(0, "
                     "clc_9 - clc_12); clc_1 uses the WOULD-BE-NEGATIVE 1040 line 15. Bug it catches: flooring "
                     "line 15 before the worksheet (overstates usage, understates the carryover — CLC-T2)."),
     "definition": {"kind": "formula_check", "form": "1040_SCHD_WS",
                    "formula": "clc_8 == max(0, clc_5 - (clc_4 + clc_6)); clc_13 == max(0, clc_9 - (clc_10 + max(0, clc_4 - clc_5)))"},
     "sort_order": 4},
    {"assertion_id": "FA-1040-SCHD-05", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Line 17/20/22 routing truth table (ordinary vs QDCGT vs SDTW)",
     "description": ("Both 15/16 gains + 18/19 zero + no 4952 -> QDCGT; both gains + (18 or 19 nonzero) -> SDTW; "
                     "not-both-gains -> line 22 (qualified dividends -> QDCGT else ordinary). Bug it catches: "
                     "running QDCGT with 28%/1250 gain present (understates tax), or table-only tax on a "
                     "qualified-dividend loss return."),
     "definition": {"kind": "conditional_path_selection", "form": "SCHEDULE_D",
                    "paths": {"sdtw": "L15>0 and L16>0 and (L18>0 or L19>0)",
                              "qdcgt": "(L15>0 and L16>0 and L18==0 and L19==0 and not files_4952) or (L16<=0 and qualified_dividends>0)",
                              "ordinary": "L16<=0 and qualified_dividends==0"}},
     "sort_order": 5},
    {"assertion_id": "FA-1040-SCHD-06", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "SDTW constants year-keyed; lines 15/26 IDENTICAL to the Topic 3 QDCGT constants",
     "description": ("Pins SDTW_ZERO_RATE_MAX / SDTW_RATE15_MAX == QDCGT_CONSTANTS_BY_YEAR (cross-spec identity, "
                     "both years) and SDTW_BRACKET32_START both years (2026 derived — walk item 1). Bug it "
                     "catches: the two worksheets' breakpoints drifting apart, or a stale line-19 threshold."),
     "definition": {"kind": "constants_check", "form": "1040_SCHD_WS",
                    "constants": {"zero_rate_2025": SDTW_ZERO_RATE_MAX[2025], "zero_rate_2026": SDTW_ZERO_RATE_MAX[2026],
                                  "rate15_2025": SDTW_RATE15_MAX[2025], "rate15_2026": SDTW_RATE15_MAX[2026],
                                  "b32_2025": SDTW_BRACKET32_START[2025], "b32_2026": SDTW_BRACKET32_START[2026],
                                  "must_equal_qdcgt": True, "applies_to_years": [2025, 2026]}},
     "sort_order": 6},
    {"assertion_id": "FA-1040-SCHD-07", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "SDTW 25%/28% blocks + line 47 = min(45, 46); the rates are statutory CAPS",
     "description": ("L40 = max(0, min(L9, D19) - max(0, L10 + L21 - L1)) x 25%; L43 = (L1 - L41) x 28% only "
                     "when D18 > 0; L47 = min(L45, L46). The skip rules (1==16, 1==32, D18/D19 zero) gate the "
                     "blocks. Bug it catches: taxing the 28% group at 28% in a 24% bracket (SDTW-T2 pins L43 = "
                     "0), or skipping the L46 backstop."),
     "definition": {"kind": "formula_check", "form": "1040_SCHD_WS",
                    "formula": "sdtw_40 == sdtw_39 * 0.25; sdtw_43 == sdtw_42 * 0.28; sdtw_47 == min(sdtw_45, sdtw_46)",
                    "constants": {"rate_1250": 0.25, "rate_28": 0.28}},
     "sort_order": 7},
    {"assertion_id": "FA-1040-SCHD-08", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "28% WS line 7 -> Schedule D 18; 1250 WS line 18 -> Schedule D 19; the DIV 2b/2d feeds",
     "description": ("Validates R-WS-28RATE/R-WS-U1250/R-SCHD-L17-L20-ROUTE: w28_7 -> D18; u1250_18 -> D19; "
                     "DIV box 2d -> w28_4; DIV box 2b -> u1250_11; code-C rows -> w28_1. Bug it catches: a "
                     "worksheet computed but its result not landing on the face (the route then wrongly "
                     "picks QDCGT)."),
     "definition": {"kind": "flow_assertion", "form": "1040_SCHD_WS",
                    "checks": [{"source_line": "w28_7", "must_write_to": ["SCHEDULE_D.18"]},
                               {"source_line": "u1250_18", "must_write_to": ["SCHEDULE_D.19"]},
                               {"source": "DIV box 2b aggregate", "must_write_to": ["1040_SCHD_WS.u1250_11"]},
                               {"source": "DIV box 2d aggregate", "must_write_to": ["1040_SCHD_WS.w28_4"]}]},
     "sort_order": 8},
    {"assertion_id": "FA-1040-SCHD-09", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "1099-DIV box 2a -> Schedule D line 13 when engaged (Exception-1 path preserved when not)",
     "description": ("Validates R-SCHD-L13-CGD. Engaged -> box-2a aggregate lands on line 13 and the 1040 "
                     "line-7 Exception-1 checkbox path is OFF; not engaged -> the Topic 3 path is unchanged. "
                     "Bug it catches: double-counting distributions on both line 13 and 1040 line 7."),
     "definition": {"kind": "conditional_path_selection", "form": "SCHEDULE_D",
                    "paths": {"engaged": "div_2a -> SCHEDULE_D.13 (7b checkbox off)",
                              "not_engaged": "div_2a -> 1040.7 with the 7b checkbox (Topic 3 Exception-1)"}},
     "sort_order": 9},
    {"assertion_id": "FA-1040-SCHD-10", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Net capital gain output = min(L15, L16) when both gains -> 8995 line 12 + the SDTW line 7",
     "description": ("Validates R-SCHD-NETCAPGAIN + the sibling 8995 L12 amendment (D_8995_002 retires). Bug it "
                     "catches: 8995 L12 still missing the Schedule D component after this topic lands, or using "
                     "L16 instead of the smaller-of."),
     "definition": {"kind": "formula_check", "form": "SCHEDULE_D",
                    "formula": "net_capital_gain == (min(line_15, line_16) if line_15 > 0 and line_16 > 0 else 0)",
                    "must_write_to": ["8995.12 (component)", "1040_SCHD_WS.sdtw_7"]},
     "sort_order": 10},
    {"assertion_id": "FA-1040-SCHD-11", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Topic 9 RED-defers each leave a RED (no silent gap)",
     "description": ("Form 4952 (D_SCHD_001), DIV box 2c (D_SCHD_002), QOF codes Y/Z (D_SCHD_007), code-Q "
                     "without the add-back fact (D_SCHD_009), (g)-without-code (D_8949_002), sign violations "
                     "(D_8949_003). Each fires rather than silently computing a wrong number."),
     "definition": {"kind": "gating_check", "form": "SCHEDULE_D",
                    "blockers": ["files_form_4952", "div_box_2c", "qof_code_y_z", "code_q_no_addback",
                                 "adjustment_without_code", "sign_violation"],
                    "expect": {"red_fires": True}},
     "sort_order": 11},
    {"assertion_id": "FA-1040-SCHD-12", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "SDTW degenerates to the QDCGT result when D18 = D19 = 0 (no Form 4952)",
     "description": ("The structural invariant: with no 25%/28% groups, SDTW line 47 == the Topic 3 QDCGT "
                     "worksheet result for identical inputs (verified across 4 cases in the integrity gate). "
                     "Bug it catches: the two worksheets computing different tax for the same return — the "
                     "route choice must never change the answer when both are legal."),
     "definition": {"kind": "reconciliation", "form": "1040_SCHD_WS",
                    "invariant": "sdtw_47(ti, qd, ncg, d18=0, d19=0) == qdcgt(ti, qd, ncg) for all statuses/years"},
     "sort_order": 12},
]


# ═══════════════════════════════════════════════════════════════════════════
# Command
# ═══════════════════════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = (
        "Load the Schedule D / 1040_SCHD_WS / re-authored 8949 specs into Rule "
        "Studio (Sprint Topic 9). Refuses to seed until Ken sets READY_TO_SEED=True."
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()

        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad SCHEDULE_D / 1040_SCHD_WS / 8949 specs (Topic 9)\n"))

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
        self._retire_stale_8949()
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
                "REFUSING TO SEED SCHEDULE_D/1040_SCHD_WS/8949: not cleared to seed.\n"
                "\n"
                "Content is authored, but seeding is gated until Ken reviews the packet\n"
                "(the verified constants BOTH years — the QDCGT-identity breakpoints, the\n"
                "derived 2026 SDTW line-19 threshold, the statutory $3,000/$1,500 + 25%/28%;\n"
                "the 10 requires_human_review walk items; the cross-form flow map — 1040\n"
                "line 7a, route_line_16, 8995 L12; the RED-defer enumeration; and the 8949\n"
                "stale-artifact retire plan) and flips the sentinel.\n"
                "\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True to proceed)\n"
                "\n"
                "NOTE: seeding RE-AUTHORS Form 8949 — it retires the thin 1120-S-era\n"
                "artifacts (4 unnamed rules, 12 column lines, 10 nameless facts, 3 generic\n"
                "diagnostics, 3 stub tests) and writes the real 2025 12-box face.\n"
                "\n"
                "Currently empty / placeholder:\n"
                f"  {still_empty}\n"
                "\n"
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
        entity_types = (
            FORM_ENTITY_TYPES_8949 if identity["form_number"] == "8949" else FORM_ENTITY_TYPES
        )
        form, created = TaxForm.objects.update_or_create(
            form_number=identity["form_number"],
            jurisdiction=FORM_JURISDICTION,
            tax_year=FORM_TAX_YEAR,
            version=FORM_VERSION,
            defaults={
                "form_title": identity["form_title"],
                "entity_types": entity_types,
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
    # 8949 re-author — retire the thin 1120-S-era draft artifacts
    # ─────────────────────────────────────────────────────────────────────────

    def _retire_stale_8949(self):
        """Delete any 8949 artifact NOT in the re-authored sets (the old draft:
        rules R001-R004, diags D001-D003, the 1a_col_*/3a_col_*/2/4 lines, the 10
        nameless facts, the 3 stub tests). Runs AFTER the upsert so the new face
        is in place; idempotent (no-op on re-run). The _retire_stale_8995 precedent.
        """
        form = TaxForm.objects.filter(
            form_number="8949", jurisdiction=FORM_JURISDICTION,
            tax_year=FORM_TAX_YEAR, version=FORM_VERSION,
        ).first()
        if not form:
            return

        keep_facts = {f["fact_key"] for f in F8949_FACTS}
        keep_rules = {r["rule_id"] for r in F8949_RULES}
        keep_lines = {ln["line_number"] for ln in F8949_LINES}
        keep_diags = {d["diagnostic_id"] for d in F8949_DIAGNOSTICS}
        keep_tests = {t["scenario_name"] for t in F8949_SCENARIOS}

        removed = {}
        removed["facts"] = FormFact.objects.filter(tax_form=form).exclude(fact_key__in=keep_facts).delete()[0]
        removed["rules"] = FormRule.objects.filter(tax_form=form).exclude(rule_id__in=keep_rules).delete()[0]
        removed["lines"] = FormLine.objects.filter(tax_form=form).exclude(line_number__in=keep_lines).delete()[0]
        removed["diagnostics"] = FormDiagnostic.objects.filter(tax_form=form).exclude(diagnostic_id__in=keep_diags).delete()[0]
        removed["tests"] = TestScenario.objects.filter(tax_form=form).exclude(scenario_name__in=keep_tests).delete()[0]

        total = sum(removed.values())
        if total:
            self.stdout.write(self.style.WARNING(
                f"  8949 stale draft retired: {removed} ({total} stale rows deleted — RuleAuthorityLinks cascade)"
            ))
        else:
            self.stdout.write("  8949 draft: nothing stale to retire (clean re-author)")

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
        self.stdout.write("DATABASE TOTALS (after load_1040_schedule_d)")
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

        for fn in ("SCHEDULE_D", "1040_SCHD_WS", "8949"):
            all_rules = FormRule.objects.filter(tax_form__form_number=fn)
            uncited = [r for r in all_rules if not r.authority_links.exists()]
            if uncited:
                self.stdout.write(self.style.WARNING(
                    f"\n{fn} rules with ZERO authority links: {len(uncited)}"
                ))
                for r in uncited[:20]:
                    self.stdout.write(_safe(f"  {r.rule_id}: {r.title}"))
            else:
                self.stdout.write(f"{fn}: all rules cited")
