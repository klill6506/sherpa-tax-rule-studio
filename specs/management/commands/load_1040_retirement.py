"""Load the Retirement Income specs — Sprint Topic 5.

Creates TWO TaxForms:
  - 1040_RETIREMENT (pseudo-form): 1099-R document aggregation to Form 1040
    lines 4a/4b (IRA) and 5a/5b (pensions/annuities), the 1099-R box-4
    withholding extension to line 25b, the Social Security Benefits Worksheet
    (18 lines) -> lines 6a/6b, and the distribution-code routing that
    identifies early distributions feeding Form 5329.
  - 5329 (real IRS face, Part I only this sprint): the 10%/25% additional tax
    on early distributions -> Schedule 2 line 8.

Session 2026-06-11: authored by transcription from primary sources fetched and
text-extracted the same day (pymupdf dumps in tts-tax-app server/.scratch/;
consolidated in tts-tax-app server/specs/_topic5_retirement_source_brief.md):

  - Form 1099-R + Instructions for Forms 1099-R and 5498 (2025) — box
    structure (boxes 1-19) and the full Box 7 "Guide to Distribution Codes"
    (Table 1: codes 1-9, A-Y with valid combinations).
  - Form 5329 (2025) + Instructions for Form 5329 (2025, Nov 19 2025) —
    Part I lines 1-4 (10% of early distributions -> Sch 2 line 8; 25% caution
    for SIMPLE-first-2-years) + the Line 2 exception-number list (01-23).
  - i1040gi (2025) p.31 — the Social Security Benefits Worksheet (lines 6a/6b),
    all 18 lines verbatim ($25,000/$32,000 base and $9,000/$12,000 second-tier
    constants; 50%/85% inclusion); pages for lines 4a/4b/5a/5b (rollover/QCD
    literals).

TOPIC SCOPE (SPRINT_SCOPE.md Topic 5 DoD — Ken-confirmed 2026-06-11):
  IN: 1099-R all boxes; distribution codes driving treatment; rollover + QCD
      handling (4b/5b reduction + literal); minimal Form 5329 Part I (10% +
      common exception codes 01-12 + 19 -> Sch 2 line 8); taxable Social
      Security worksheet (50%/85% tiers); flow assertions on 4a/4b, 5a/5b,
      6a/6b, Schedule 2 additions.
  AMENDMENT 2026-06-28 (lump-sum SS election, D_RET_004) — Ken-directed retiree
  hardening unit. The Pub 915 Lump-Sum Election (Worksheets 2 + 4) is now COMPUTED
  (R-RET-LSE-WS2/WS4/ELECT), no longer RED-deferred. Explicit-toggle election
  (ss_lump_sum_election; irrevocable without IRS consent). D_RET_004 repurposed to
  the no-silent-gap "earlier-year data missing" guard; D_RET_008 surfaces the
  WS1-vs-WS4 comparison. Source: Pub 915 (2025) verbatim (IRS_2025_PUB915), the
  Terry Jackson worked example reconciles to the dollar (scenario LSE-1).

  OUT (RED "prepare manually", never silently computed):
      Simplified Method (box 2a blank / "taxable amount not determined" checked
      with basis); Net Unrealized Appreciation (box 6); pre-1994 lump-sum years
      (Worksheet 3 — RED, vanishingly rare); simultaneous IRA-deduction <->
      taxable-SS circular (D_RET_005, the separate larger unit); Roth basis tracking
      (codes J/T with blank box 2a -> needs Form 8606); Form 4972 10-year
      option (code A); §1035 exchange (code 6); recharacterizations (N/R);
      uncommon codes (C/E/F/K/L/M/U/W); 5329 exception numbers >= 13 and "99".

KEN'S CONFIRMED SCOPE DECISIONS (2026-06-11, the brief §4 judgment items):
  1. v1 supported distribution codes: 1,2,3,4,7,8,9,B,D,G,H,Q,S,Y + the
     IRA/SEP/SIMPLE checkbox; all others RED. ("I think so")
  2. 5329 exception numbers 01-12 + 19 supported; >= 13 and 99 RED. ("Yes")
  3. Direct-to-Schedule-2 shortcut for the pure code-1 full-amount case;
     Form 5329 Part I generated only when an exception is claimed or a non-1
     early code applies. ("Yes")
  4. Rollover/QCD = preparer-entered amounts on the 1099-R doc (codes G/Y
     assist but never silently auto-zero). ("I think so")
  5. TY2026 constants confirmed at the review walk (SS thresholds + 10%/25%
     rates are statutory/non-indexed — verify RP 2025-32 changes none, same as
     Schedule 1-A). ("confirm at walk")

SPINE / SIBLING SUPERSESSION (build leg, flagged for Ken):
  - 1040 lines 4a/4b/5a/5b/6a/6b become COMPUTED feeders (YELLOW) from the
    documents; each keeps the preparer override escape hatch.
  - Spine R-PAY-02 (line 25b withholding) EXTENDS again to include 1099-R
    box 4 (was 1099-INT box 4 + 1099-DIV box 4 after Topic 3).
  - Schedule 2 line 8 becomes a COMPUTED feeder from 5329 Part I (was
    direct-entry from Topic 2). The Topic-2 direct entry remains the override.
  - SS worksheet line 3 reads 1040 lines 1z, 2b, 3b, 4b, 5b, 7a, 8 — so it runs
    AFTER the Topic 3 (2b/3b/7a) and this topic's (4b/5b) aggregation.

TY2026 NOTE (target-year policy): the SS worksheet base/second-tier amounts
($25,000/$32,000, $9,000/$12,000) are STATUTORY and NOT inflation-indexed
(§86 has fixed dollar thresholds since 1983/1993) — same for both years; the
5329 rates (10%/25%) are statutory. No year-keyed constants in this topic
(unlike Topic 3's breakpoints). Confirm at the walk that RP 2025-32 adjusts
none of these.

Safety guard
------------
`READY_TO_SEED = False`. Content is authored; Ken reviews the packet, flips the
sentinel, and seeds. Until then the command refuses to write to the DB.

Idempotent via update_or_create — safe to re-run after edits.

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
# SAFETY GUARD — authored 2026-06-11, NOT yet reviewed/approved by Ken.
# Flip to True ONLY after the in-session review walk (the source citations,
# the v1 distribution-code set, the 5329 exception subset, the SS worksheet
# transcription, and the TY2026 statutory-constant confirmation).
# ═══════════════════════════════════════════════════════════════════════════

# Ken approved in-session 2026-06-11 (review walk: source citations + SS Benefits
# Worksheet transcription + TY2026 §86/5329 constants confirmed non-indexed +
# R-RET-CODE J-wording tightened). Math gate (check_retirement_integrity.py)
# green before the flip.
#
# AMENDMENT 2026-06-28 (lump-sum SS election): the new R-RET-LSE-* rules + Pub 915
# source + LSE-1/LSE-2 scenarios are math-gate-green (check_retirement_integrity.py).
# Ken approved building this in-session (chose D_RET_004 first + the explicit-toggle
# election behavior) and reviewed the Pub 915 verification (the Terry example
# reconciles to the dollar). Seed the amendment only after the in-session go-ahead.
READY_TO_SEED = True


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1040"]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY TOPICS
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("retirement_income", "Retirement income — 1099-R distributions, pensions/annuities, IRAs"),
    ("social_security", "Taxable Social Security benefits (1040 lines 6a/6b worksheet)"),
    ("early_distribution_tax", "Form 5329 Part I — 10%/25% additional tax on early distributions"),
]

# Existing sources to REUSE (looked up, not modified).
EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_1040_FORM",    # lines 4a/4b/5a/5b/6a/6b/6c/6d on the 2025 face
    "IRS_2025_1040_INSTR",   # i1040gi: line instructions + the SS Benefits Worksheet
]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY SOURCES (with embedded excerpts) — CREATE
# Transcribed 2026-06-11 from the fetched PDFs (tts-tax-app server/.scratch/),
# requires_human_review=False (verbatim, verifiable against the on-disk copies).
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_1099R_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Form 1099-R — Distributions From Pensions, Annuities, Retirement or Profit-Sharing Plans, IRAs, Insurance Contracts, etc.",
        "citation": "Form 1099-R (2025); f1099r.pdf",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f1099r.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": (
            "Box structure transcribed 2026-06-11 from the fetched copy "
            "(server/.scratch/f1099r-2025.pdf). 1099-R is an INPUT document (not "
            "rendered by us); a new RetirementDistribution model is created at the "
            "build leg mirroring the InterestIncome/DividendIncome document pattern."
        ),
        "topics": ["retirement_income"],
        "excerpts": [
            {
                "excerpt_label": "Box structure (recipient copy)",
                "location_reference": "Form 1099-R (2025), boxes 1-19",
                "excerpt_text": (
                    "1 Gross distribution. 2a Taxable amount. 2b Taxable amount not "
                    "determined / Total distribution [checkboxes]. 3 Capital gain "
                    "(included in box 2a). 4 Federal income tax withheld. 5 Employee "
                    "contributions/Designated Roth contributions or insurance premiums. "
                    "6 Net unrealized appreciation in employer's securities. 7 "
                    "Distribution code(s) / IRA/SEP/SIMPLE [checkbox]. 8 Other. 9a Your "
                    "percentage of total distribution. 9b Total employee contributions. "
                    "10 Amount allocable to IRR within 5 years. 11 1st year of desig. "
                    "Roth contrib. 12 FATCA filing requirement [checkbox]. 13 Date of "
                    "payment. 14 State tax withheld. 15 State/Payer's state no. 16 "
                    "State distribution. 17 Local tax withheld. 18 Name of locality. "
                    "19 Local distribution."
                ),
                "summary_text": (
                    "Box 2a is the primary taxable source. Box 2b-left ('taxable amount "
                    "not determined') + basis -> Simplified Method (RED). IRA/SEP/SIMPLE "
                    "checkbox routes line 4a/4b vs 5a/5b. Box 4 -> 1040 line 25b."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Box 7 IRA/SEP/SIMPLE checkbox + Box 2b (i1099r)",
                "location_reference": "Instructions for Forms 1099-R and 5498 (2025), Box 7 / Box 2a",
                "excerpt_text": (
                    "Enter an 'X' in the IRA/SEP/SIMPLE checkbox if the distribution is "
                    "from a traditional IRA or Roth SIMPLE IRA. ... If you are unable to "
                    "reasonably obtain the data necessary to compute the taxable amount, "
                    "leave box 2a blank, leave box 5 blank ..., and check the first box "
                    "in box 2b."
                ),
                "summary_text": (
                    "IRA checkbox -> lines 4a/4b. 'Taxable amount not determined' (box 2b "
                    "first checkbox) with basis -> Simplified Method territory (RED)."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_1099R_INSTR",
        "source_type": "official_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Forms 1099-R and 5498",
        "citation": "Instructions for Forms 1099-R and 5498 (2025)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i1099r.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": (
            "Table 1 'Guide to Distribution Codes' transcribed 2026-06-11 "
            "(server/.scratch/i1099r-2025_dump.txt, pages 17-19)."
        ),
        "topics": ["retirement_income", "early_distribution_tax"],
        "excerpts": [
            {
                "excerpt_label": "Box 7 Guide to Distribution Codes (Table 1, key codes — verbatim)",
                "location_reference": "i1099r (2025), Table 1, pp.17-19",
                "excerpt_text": (
                    "1 - Early distribution, no known exception. 2 - Early distribution, "
                    "exception applies. 3 - Disability. 4 - Death. 5 - Prohibited "
                    "transaction. 6 - Section 1035 exchange. 7 - Normal distribution. "
                    "8 - Excess contributions plus earnings/excess deferrals taxable in "
                    "2025. 9 - Cost of current life insurance protection. A - May be "
                    "eligible for 10-year tax option. B - Designated Roth account "
                    "distribution. G - Direct rollover and direct payment. H - Direct "
                    "rollover of a designated Roth account distribution to a Roth IRA. "
                    "J - Early distribution from a Roth IRA, no known exception. P - "
                    "Excess contributions plus earnings/excess deferrals taxable in "
                    "2024. Q - Qualified distribution from a Roth IRA. S - Early "
                    "distribution from a SIMPLE IRA in the first 2 years, no known "
                    "exception. T - Roth IRA distribution, exception applies. Y - "
                    "Qualified charitable distribution (QCD) under section 408(d)(8); "
                    "use Code Y with either 4, 7, or K."
                ),
                "summary_text": (
                    "Codes 1/J/S = early (10%/25% via 5329). 2/3/4/7 = no early tax. "
                    "G/H = rollover (0 taxable). Q = qualified Roth (not taxable). Y = "
                    "QCD. A/5/6/N/R/etc. = RED unsupported this sprint."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Code Y QCD pairing rule (verbatim)",
                "location_reference": "i1099r (2025), Code Y",
                "excerpt_text": (
                    "Use Code Y for a distribution made directly from an IRA to a "
                    "charitable organization and that the taxpayer intends to be a QCD. "
                    "... When using code Y, you must use either 4, 7, or K."
                ),
                "summary_text": "QCD code Y always pairs with 4, 7, or K; reduces 4b with the 'QCD' literal.",
                "is_key_excerpt": False,
            },
        ],
    },
    {
        "source_code": "IRS_2025_PUB915",
        "source_type": "official_publication",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Publication 915 — Social Security and Equivalent Railroad Retirement Benefits",
        "citation": "Pub 915 (2025), 'Lump-Sum Election' + Worksheets 1, 2, 4; p.11-19",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/p915.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": (
            "AMENDMENT 2026-06-28 (lump-sum election unit, D_RET_004). Transcribed "
            "verbatim from the fetched 2025 Pub 915 PDF (pymupdf dump, pages 10-19; "
            "scratchpad p915_worksheets.txt). Worksheet 1 = the regular SS Benefits "
            "Worksheet (already in this spec as R-RET-SS-01/02). Worksheet 2 (per "
            "earlier year, post-1993) refigures that year's taxable benefits with the "
            "lump-sum portion added, then subtracts the previously-reported taxable "
            "benefits = the ADDITIONAL taxable benefits. Worksheet 4 re-runs the 2025 "
            "worksheet with box 5 reduced by the pre-2025 lump sum, then adds the "
            "Worksheet-2 additionals; if WS4 line 21 < WS1 line 19 the election lowers "
            "taxable SS. requires_human_review=True for Ken's walk (the worked example "
            "below reconciles to the dollar — verify the transcription)."
        ),
        "topics": ["social_security"],
        "excerpts": [
            {
                "excerpt_label": "Lump-Sum Election — method (verbatim, p.11)",
                "location_reference": "Pub 915 (2025), 'Lump-Sum Election', p.11",
                "excerpt_text": (
                    "Under the lump-sum election method, you refigure the taxable part of "
                    "all your benefits for the earlier year (including the lump-sum payment) "
                    "using that year's income. Then, you subtract any taxable benefits for "
                    "that year that you previously reported. The remainder is the taxable "
                    "part of the lump-sum payment. Add it to the taxable part of your "
                    "benefits for 2025 (figured without the lump-sum payment for the earlier "
                    "year). ... Will the lump-sum election method lower your taxable "
                    "benefits? 1. Complete Worksheet 1. 2. Complete Worksheet 2 [post-1993] "
                    "or 3 [pre-1994] for each earlier year. 3. Complete Worksheet 4. "
                    "4. Compare line 19 of Worksheet 1 with line 21 of Worksheet 4. If the "
                    "taxable benefits on Worksheet 4 are lower, you can elect to report the "
                    "lower amount (check the box on Form 1040 line 6c; enter Worksheet 1 "
                    "line 1 on 6a and Worksheet 4 line 21 on 6b)."
                ),
                "summary_text": (
                    "Refigure earlier-year taxable benefits WITH the lump sum (WS2), subtract "
                    "previously-reported, = additional taxable benefits; WS4 = 2025 benefits "
                    "(net of pre-2025 lump sum) + Σ additionals; elect (check 6c) only if WS4 "
                    "L21 < WS1 L19. Election is irrevocable without IRS consent."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Worksheet 2 — Additional Taxable Benefits, earlier year (verbatim, p.17)",
                "location_reference": "Pub 915 (2025), Worksheet 2, p.17",
                "excerpt_text": (
                    "1. box 5 of all SSA/RRB-1099 for the earlier year, PLUS the lump-sum "
                    "payment for the earlier year received after that year. 2. line 1 x 50%. "
                    "3. AGI for the earlier year. 4. exclusions/adjustments for the earlier "
                    "year. 5. tax-exempt interest for the earlier year. 6. add lines 2-5. "
                    "7. taxable benefits previously reported for the earlier year. 8. line 6 "
                    "- line 7. 9. $32,000 MFJ / $25,000 single/HOH/QSS/MFS-apart (MFS-with-"
                    "spouse: skip 9-16, line 17 = 0.85 x line 8). 10. is line 8 > line 9? "
                    "No -> line 21 = 0; Yes -> line 8 - line 9. 11. $12,000 MFJ / $9,000 "
                    "other. 12. line 10 - line 11, not below 0. 13. smaller of line 10 or "
                    "11. 14. line 13 x 50%. 15. smaller of line 2 or 14. 16. line 12 x 85%. "
                    "17. line 15 + 16. 18. line 1 x 85%. 19. smaller of line 17 or 18 "
                    "(refigured taxable benefits). 20. taxable benefits for the earlier year "
                    "previously reported. 21. line 19 - line 20 (ADDITIONAL taxable benefits) "
                    "-> Worksheet 4 line 20."
                ),
                "summary_text": (
                    "Same 50%/85% tiers as WS1, but L1 = earlier-year benefits + lump sum, "
                    "and L8 subtracts the previously-reported taxable benefits (which AGI "
                    "already contains). L21 = refigured - previously-reported = additional."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Worksheet 4 — Taxable Benefits Under Lump-Sum Election (verbatim, p.18-19)",
                "location_reference": "Pub 915 (2025), Worksheet 4, p.18-19",
                "excerpt_text": (
                    "1. box 5 of all 2025 SSA/RRB-1099 MINUS the lump-sum payment for years "
                    "before 2025 (if <=0, line 19 = 0, go to 20). 2. line 1 x 50%. 3. "
                    "Worksheet 1 line 3. 4. Worksheet 1 line 4. 5. Worksheet 1 line 5. 6. "
                    "combine lines 2-5. 7. Worksheet 1 line 7. 8. line 6 - line 7. 9. "
                    "Worksheet 1 line 9 (MFS-with-spouse: skip 9-16, line 17 = 0.85 x line "
                    "8). 10. is line 8 > line 9? No -> line 19 = 0, go to 20; Yes -> line 8 "
                    "- line 9. 11. Worksheet 1 line 11. 12. line 10 - 11, not below 0. 13. "
                    "smaller of 10 or 11. 14. line 13 x 50%. 15. smaller of 2 or 14. 16. "
                    "line 12 x 85%. 17. line 15 + 16. 18. line 1 x 85%. 19. smaller of 17 "
                    "or 18. 20. total of Worksheet 2 line 21 (and Worksheet 3 line 14) for "
                    "all earlier years. 21. line 19 + line 20 = taxable benefits under the "
                    "lump-sum election method -> Form 1040 line 6b (if < Worksheet 1 line 19)."
                ),
                "summary_text": (
                    "WS4 reuses WS1 lines 3/4/5/7/9/11 (the 2025 income context) but starts "
                    "from box 5 reduced by the pre-2025 lump sum, then ADDS the Σ WS2 line-21 "
                    "additionals. Final L21 -> 6b when it beats WS1 L19."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Worked example (Terry Jackson, single) — reconciles to the dollar",
                "location_reference": "Pub 915 (2025), Example + filled-in Worksheet 4, p.11-14",
                "excerpt_text": (
                    "Terry (single) received in 2025 a $6,000 lump sum ($2,000 for 2024, "
                    "$4,000 for 2025) + $5,000 regular = $11,000 box 5. 2025 other income "
                    "$25,500; 2024 income $23,000. Worksheet 1 (regular, all $11,000): line "
                    "19 = $3,000. Worksheet 2 (2024): L1 = 0 + 2,000 = 2,000; L6 = 1,000 + "
                    "23,000 = 24,000; L8 = 24,000; L9 = 25,000 -> line 10 No -> line 21 = 0. "
                    "Worksheet 4: L1 = 11,000 - 2,000 = 9,000; L2 = 4,500; L3 = 25,500; L6 = "
                    "30,000; L8 = 30,000; L9 = 25,000; L10 = 5,000; L11 = 9,000; L12 = 0; "
                    "L13 = 5,000; L14 = 2,500; L15 = 2,500; L16 = 0; L17 = 2,500; L18 = "
                    "7,650; L19 = 2,500; L20 = 0; L21 = $2,500. Because $2,500 < $3,000, "
                    "Terry elects, checks 6c, reports $11,000 on 6a and $2,500 on 6b."
                ),
                "summary_text": (
                    "The whole method, end to end: election saves $500 of taxable SS. Used "
                    "as the canonical test scenario (LSE-1) for the integrity gate and the "
                    "tts pure compute tests."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_5329_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Form 5329 — Additional Taxes on Qualified Plans (Including IRAs) and Other Tax-Favored Accounts",
        "citation": "Form 5329 (2025); f5329.pdf; Attachment Sequence No. 29",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f5329.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": (
            "Part I transcribed 2026-06-11 (server/.scratch/f5329-2025.pdf). Real face "
            "rendered by us (build leg adds f5329 to the manifest + an AcroForm field "
            "map). Parts II-VIII out of scope this sprint."
        ),
        "topics": ["early_distribution_tax"],
        "excerpts": [
            {
                "excerpt_label": "Part I — Additional Tax on Early Distributions (verbatim)",
                "location_reference": "Form 5329 (2025), Part I, lines 1-4",
                "excerpt_text": (
                    "If you only owe the additional 10% tax on the full amount of the "
                    "early distributions, you may be able to report this tax directly on "
                    "Schedule 2 (Form 1040), line 8, without filing Form 5329. "
                    "1 Early distributions includible in income. 2 Early distributions "
                    "included on line 1 that are not subject to the additional tax. Enter "
                    "the appropriate exception number from the instructions. 3 Amount "
                    "subject to additional tax. Subtract line 2 from line 1. 4 Additional "
                    "tax. Enter 10% (0.10) of line 3. Include this amount on Schedule 2 "
                    "(Form 1040), line 8. Caution: If any part of the amount on line 3 "
                    "was a distribution from a SIMPLE IRA, you may have to include 25% of "
                    "that amount on line 4 instead of 10%."
                ),
                "summary_text": (
                    "L1 early distributions; L2 exception amount (number 01-23); L3 = "
                    "L1-L2; L4 = 10% x L3 -> Sch 2 line 8 (25% for SIMPLE-first-2-years). "
                    "Direct-to-Sch-2 shortcut for the pure code-1 full-amount case."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_5329_INSTR",
        "source_type": "official_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Form 5329",
        "citation": "Instructions for Form 5329 (2025), Nov 19, 2025; Cat. No. 13330R",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i5329.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": (
            "Line 1 / Line 2 instructions + the exception-number list 01-23 "
            "transcribed 2026-06-11 (server/.scratch/i5329-2025_dump.txt, pages 2-4)."
        ),
        "topics": ["early_distribution_tax"],
        "excerpts": [
            {
                "excerpt_label": "Line 2 exception-number list 01-12 + 19 (v1 supported, verbatim)",
                "location_reference": "i5329 (2025), Line 2, 'Exceptions to the Additional Tax on Early Distributions'",
                "excerpt_text": (
                    "Enter on line 2 the amount that you can exclude. In the space "
                    "provided, enter the applicable exception number (01-23). If more "
                    "than one exception applies, enter 99. 01 Qualified retirement plan "
                    "distributions after separation from service at age 55 (50 for public "
                    "safety/firefighters) (not IRAs). 02 Substantially equal periodic "
                    "payments. 03 Total and permanent disability. 04 Death. 05 "
                    "Unreimbursed medical expenses > 7.5% AGI. 06 QDRO (not IRAs). 07 IRA "
                    "distributions to unemployed for health insurance. 08 IRA higher "
                    "education expenses. 09 IRA first home, up to $10,000. 10 IRS levy. "
                    "11 Qualified reservist distributions (active duty >= 180 days). 12 "
                    "Distributions incorrectly indicated as early (code 1/J/S) when age "
                    ">= 59 1/2. ... 19 Qualified birth or adoption distributions, up to "
                    "$5,000."
                ),
                "summary_text": (
                    "v1 supported exception numbers: 01-12 + 19. Line 2 amount is "
                    "preparer-entered with the number; 13-23 and '99' (multiple) fire RED."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Rollover not subject to 10% (verbatim)",
                "location_reference": "i5329 (2025), Qualified retirement plan rollover",
                "excerpt_text": (
                    "If you rolled over part or all of a distribution from a qualified "
                    "retirement plan, the part rolled over isn't subject to the 10% "
                    "additional tax on early distributions. See the instructions for "
                    "Form 1040, lines 4a and 4b or lines 5a and 5b, for how to report "
                    "the rollover."
                ),
                "summary_text": "Rolled-over amounts are excluded from line 1 (and from 4b/5b — the 'Rollover' literal).",
                "is_key_excerpt": False,
            },
        ],
    },
    # ── AMENDMENT 2026-06-30: Medicare premium deductibility (Sch A / SEHI) ──
    {
        "source_code": "IRS_2025_PUB502",
        "source_type": "official_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Publication 502 — Medical and Dental Expenses",
        "citation": "Pub. 502 (2025), 'Medicare Part B' / 'Medicare Part D' / 'Medicare Part A'",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/publications/p502",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": "Medicare premium deductibility verified 2026-06-30 against the live Pub 502 text (Part B / Part D / voluntary Part A).",
        "topics": ["retirement_income"],
        "excerpts": [
            {
                "excerpt_label": "Medicare Part B / Part D / Part A premiums (verbatim)",
                "location_reference": "Pub. 502 (2025), 'Medicare Part B' and 'Medicare Part D'",
                "excerpt_text": (
                    "Medicare Part B is a supplemental medical insurance. Premiums you pay "
                    "for Medicare Part B are a medical expense. ... Medicare Part D is a "
                    "voluntary prescription drug insurance program for persons with Medicare "
                    "Part A or B. You can include as a medical expense premiums you pay for "
                    "Medicare Part D. ... If you aren't covered under social security (or "
                    "weren't a government employee who paid Medicare tax), you can voluntarily "
                    "enroll in Medicare Part A. In this situation, you can include the premiums "
                    "you paid for Medicare Part A as a medical expense."
                ),
                "summary_text": "Medicare Part B and Part D premiums are deductible Schedule A medical expenses (Part A only if voluntarily enrolled).",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_F7206_INSTR",
        "source_type": "official_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Form 7206 — Self-Employed Health Insurance Deduction",
        "citation": "Instructions for Form 7206 (2025), 'Purpose of Form' — Medicare premiums",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/instructions/i7206",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": "Medicare-as-SEHI verified 2026-06-30 against the live Form 7206 instructions.",
        "topics": ["retirement_income"],
        "excerpts": [
            {
                "excerpt_label": "Medicare premiums as self-employed health insurance (verbatim)",
                "location_reference": "Instructions for Form 7206 (2025), 'Purpose of Form' — Additional information",
                "excerpt_text": (
                    "Medicare premiums you voluntarily pay to obtain insurance in your name "
                    "that is similar to qualifying private health insurance can be used to "
                    "figure the deduction. You can't include amounts for any month you were "
                    "eligible to participate in a health plan subsidized by your employer or "
                    "your spouse's employer. The deduction can't be more than your net profit "
                    "from the business under which the insurance plan is established."
                ),
                "summary_text": "Medicare premiums qualify as the self-employed health insurance deduction (Form 7206 -> Sch 1 line 17), capped at net SE profit; not for months eligible for an employer plan.",
                "is_key_excerpt": True,
            },
        ],
    },
]

# Excerpts to add to the EXISTING 1040 instructions source.
NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = [
    (
        "IRS_2025_1040_INSTR",
        {
            "excerpt_label": "Social Security Benefits Worksheet — all 18 lines (verbatim, lines 6a/6b)",
            "location_reference": "i1040gi (2025), p.31 — Social Security Benefits Worksheet—Lines 6a and 6b",
            "excerpt_text": (
                "1. Enter the total amount from box 5 of all your Forms SSA-1099 and "
                "RRB-1099. Also enter on Form 1040, line 6a. 2. Multiply line 1 by 50% "
                "(0.50). 3. Combine the amounts from Form 1040, lines 1z, 2b, 3b, 4b, "
                "5b, 7a, and 8. 4. Enter the amount, if any, from Form 1040, line 2a. "
                "5. Combine lines 2, 3, and 4. 6. Enter the total of the amounts from "
                "Schedule 1, lines 11 through 20, and 23 and 25. 7. Is the amount on "
                "line 6 less than the amount on line 5? No: none of your benefits are "
                "taxable; enter -0- on line 6b. Yes: subtract line 6 from line 5. "
                "8. If you are married filing jointly, enter $32,000; single, head of "
                "household, qualifying surviving spouse, or married filing separately "
                "and you lived apart from your spouse for all of 2025, enter $25,000. "
                "(MFS and lived with spouse: skip lines 8-15; multiply line 7 by 85% and "
                "enter on line 16; then go to line 17.) 9. Is line 8 less than line 7? "
                "No: none taxable, enter -0- on 6b. Yes: subtract line 8 from line 7. "
                "10. Enter $12,000 if married filing jointly; $9,000 otherwise. "
                "11. Subtract line 10 from line 9. If zero or less, enter -0-. 12. Enter "
                "the smaller of line 9 or line 10. 13. Enter one-half of line 12. "
                "14. Enter the smaller of line 2 or line 13. 15. Multiply line 11 by "
                "85% (0.85). If line 11 is zero, enter -0-. 16. Add lines 14 and 15. "
                "17. Multiply line 1 by 85% (0.85). 18. Taxable social security "
                "benefits. Enter the smaller of line 16 or line 17. Also enter on "
                "Form 1040, line 6b."
            ),
            "summary_text": (
                "Provisional-income 50%/85% worksheet. Base $25,000/$32,000 (L8), "
                "second tier $9,000/$12,000 (L10). STATUTORY non-indexed (§86) — same "
                "for 2025 and 2026. Line 3 reads 1z/2b/3b/4b/5b/7a/8 -> runs AFTER "
                "Topic 3 + this topic's aggregation. Lump-sum prior-year benefit -> "
                "Pub 915 election (RED unsupported)."
            ),
            "is_key_excerpt": True,
        },
    ),
    (
        "IRS_2025_1040_INSTR",
        {
            "excerpt_label": "Lines 4a/4b/5a/5b — rollover/QCD literals (verbatim fragments)",
            "location_reference": "i1040gi (2025), Lines 4a/4b (IRA) and 5a/5b (Pensions and Annuities)",
            "excerpt_text": (
                "Lines 4a and 4b — IRA Distributions. ... If your IRA distribution is "
                "fully taxable, enter it on line 4b; don't make an entry on line 4a. ... "
                "Rollovers: ... enter the total distribution on line 4a and the taxable "
                "part on line 4b. Enter 'Rollover' next to line 4b. ... Qualified "
                "charitable distribution (QCD): ... Include the QCD in the total on line "
                "4a. Enter the taxable amount on line 4b ... enter 'QCD' next to line "
                "4b. Lines 5a and 5b — Pensions and Annuities. ... If your pension or "
                "annuity is fully taxable, enter it on line 5b; don't make an entry on "
                "line 5a. ... You must use the General Rule or Simplified Method to "
                "figure the taxable part if box 2a is blank."
            ),
            "summary_text": (
                "4a/5a = gross, 4b/5b = taxable. Fully-taxable shortcut (5b only) is "
                "still captured as 5a=5b for line-status clarity. 'Rollover'/'QCD' "
                "literals. Box-2a-blank pension -> Simplified Method (RED)."
            ),
            "is_key_excerpt": True,
        },
    ),
]


# ═══════════════════════════════════════════════════════════════════════════
# 1040_RETIREMENT — 1099-R aggregation + SS worksheet (pseudo-form)
# ═══════════════════════════════════════════════════════════════════════════

RET_IDENTITY = {
    "form_number": "1040_RETIREMENT",
    "form_title": "Retirement Income — 1099-R aggregation + Social Security worksheet (TY2025)",
    "notes": (
        "Sprint Topic 5. PSEUDO-FORM: not an IRS face — it carries (a) the per-"
        "document 1099-R facts + the distribution-code routing, (b) aggregation to "
        "Form 1040 lines 4a/4b (IRA, box-7 IRA/SEP/SIMPLE checked) and 5a/5b "
        "(pensions/annuities), the box-4 withholding extension to line 25b, and "
        "(c) the Social Security Benefits Worksheet (18 lines) -> lines 6a/6b "
        "(renders as a STATEMENT page, never a faked IRS face). Early-distribution "
        "amounts (codes 1/J/S without an exception) flow to the separate 5329 form. "
        "No year-keyed constants (SS thresholds + 10%/25% are statutory non-indexed)."
    ),
}

RET_FACTS: list[dict] = [
    # ── 1099-R document facts (per-document; NEW RetirementDistribution model) ──
    {"fact_key": "r_payer_name", "label": "1099-R: payer name", "data_type": "string", "sort_order": 1,
     "notes": "PER DOCUMENT. Build leg creates RetirementDistribution mirroring the InterestIncome payer snapshot block."},
    {"fact_key": "r_box1_gross", "label": "1099-R box 1: gross distribution", "data_type": "decimal",
     "default_value": "0", "sort_order": 2, "notes": "PER DOCUMENT. -> 4a (IRA) or 5a (pension) gross column."},
    {"fact_key": "r_box2a_taxable", "label": "1099-R box 2a: taxable amount", "data_type": "decimal",
     "default_value": "0", "sort_order": 3,
     "notes": "PER DOCUMENT. The PRIMARY taxable source -> 4b/5b. Blank + basis -> Simplified Method (D_RET_001 RED)."},
    {"fact_key": "r_box2b_not_determined", "label": "1099-R box 2b: 'Taxable amount not determined' checkbox",
     "data_type": "boolean", "sort_order": 4,
     "notes": "PER DOCUMENT. Checked + basis (box 5/9b) -> Simplified Method RED (the OPM CSA-1099-R pattern)."},
    {"fact_key": "r_box2b_total_distribution", "label": "1099-R box 2b: 'Total distribution' checkbox",
     "data_type": "boolean", "sort_order": 5, "notes": "PER DOCUMENT. Stored; relevant to NUA/lump-sum (RED) paths."},
    {"fact_key": "r_box3_capgain", "label": "1099-R box 3: capital gain (included in box 2a)", "data_type": "decimal",
     "default_value": "0", "sort_order": 6,
     "notes": "PER DOCUMENT. Stored. Pre-1936 lump-sum (Form 4972) territory -> code A is RED."},
    {"fact_key": "r_box4_fed_withheld", "label": "1099-R box 4: federal income tax withheld", "data_type": "decimal",
     "default_value": "0", "sort_order": 7, "notes": "PER DOCUMENT. -> 1040 line 25b (extends spine R-PAY-02)."},
    {"fact_key": "r_box5_basis", "label": "1099-R box 5: employee contributions / Roth contrib / insurance premiums",
     "data_type": "decimal", "default_value": "0", "sort_order": 8,
     "notes": "PER DOCUMENT. Basis recovered tax-free this year. Box-2a-blank WITH box 5 > 0 -> Simplified Method RED."},
    {"fact_key": "r_box6_nua", "label": "1099-R box 6: net unrealized appreciation (NUA)", "data_type": "decimal",
     "default_value": "0", "sort_order": 9,
     "notes": "PER DOCUMENT. ANY NUA > 0 -> D_RET_002 RED (NUA election not supported)."},
    {"fact_key": "r_box7_codes", "label": "1099-R box 7: distribution code(s)", "data_type": "string", "sort_order": 10,
     "notes": ("PER DOCUMENT. One or two codes (e.g. '7', '1', '4G', '7A'). Drives treatment per R-RET-CODE: "
               "v1 supports 1,2,3,4,7,8,9,B,D,G,H,Q,S,Y; others -> D_RET_003 RED.")},
    {"fact_key": "r_box7_ira_sep_simple", "label": "1099-R box 7: IRA/SEP/SIMPLE checkbox", "data_type": "boolean",
     "sort_order": 11, "notes": "PER DOCUMENT. Checked -> lines 4a/4b (IRA); unchecked -> lines 5a/5b (pension/annuity)."},
    {"fact_key": "r_box8_other", "label": "1099-R box 8: other", "data_type": "decimal", "default_value": "0", "sort_order": 12,
     "notes": "PER DOCUMENT. Stored."},
    {"fact_key": "r_box9b_total_contrib", "label": "1099-R box 9b: total employee contributions", "data_type": "decimal",
     "default_value": "0", "sort_order": 13, "notes": "PER DOCUMENT. Basis on a total distribution; Simplified-Method input (RED)."},
    {"fact_key": "r_box12_fatca", "label": "1099-R box 12: FATCA filing requirement box", "data_type": "boolean",
     "sort_order": 14},
    {"fact_key": "r_box14_state_withheld", "label": "1099-R box 14: state tax withheld", "data_type": "decimal",
     "default_value": "0", "sort_order": 15, "notes": "PER DOCUMENT. Stored for the Georgia 500 (Aug-Sept runway)."},
    {"fact_key": "r_box16_state_distribution", "label": "1099-R box 16: state distribution", "data_type": "decimal",
     "default_value": "0", "sort_order": 16, "notes": "PER DOCUMENT. Stored (GA retirement-income exclusion handoff)."},
    {"fact_key": "r_rollover_amount", "label": "1099-R: amount rolled over (preparer entry)", "data_type": "decimal",
     "default_value": "0", "sort_order": 17,
     "notes": ("PER DOCUMENT. JUDGMENT 4 (Ken-confirmed): preparer-entered. Reduces 4b/5b; renders the 'Rollover' "
               "literal. Code G/H prefills the suggestion but never silently auto-zeros.")},
    {"fact_key": "r_qcd_amount", "label": "1099-R: qualified charitable distribution amount (preparer entry)",
     "data_type": "decimal", "default_value": "0", "sort_order": 18,
     "notes": ("PER DOCUMENT. JUDGMENT 4: preparer-entered (IRA-only). Reduces 4b; renders the 'QCD' literal. "
               "Code Y assists. $108,000 per-taxpayer 2025 cap is the preparer's check (D_RET info).")},
    # ── SSA-1099 facts (return-level) ──
    {"fact_key": "ssa_box5_net_benefits", "label": "SSA-1099 / RRB-1099 box 5: net benefits (total of all)", "data_type": "decimal",
     "default_value": "0", "sort_order": 30, "notes": "RETURN LEVEL (sum across taxpayer + spouse). SS Worksheet line 1 -> 1040 6a."},
    {"fact_key": "ssa_lump_sum_prior_year", "label": "SSA-1099: includes a lump-sum payment for an earlier year",
     "data_type": "boolean", "sort_order": 31,
     "notes": "RETURN LEVEL. True -> Lump-Sum Election (Pub 915) -> D_RET_004 RED (not supported this sprint)."},
    {"fact_key": "mfs_lived_with_spouse", "label": "MFS and lived with spouse at any time in 2025", "data_type": "boolean",
     "sort_order": 32,
     "notes": ("RETURN LEVEL. SS Worksheet: MFS-lived-with-spouse skips lines 8-15 and taxes 85% from dollar one "
               "(line 16 = line 7 x 85%). MFS-lived-apart uses the single $25,000 base + checks 1040 line 6d.")},
    # ── Lump-Sum Election facts (AMENDMENT 2026-06-28; Pub 915 Worksheets 2 + 4) ──
    {"fact_key": "ss_lump_sum_election", "label": "Lump-sum election: report taxable SS under the Pub 915 lump-sum method",
     "data_type": "boolean", "sort_order": 33,
     "notes": ("RETURN LEVEL (Taxpayer toggle). EXPLICIT election (irrevocable without IRS consent — Ken 2026-06-28). "
               "False -> regular Worksheet 1 governs line 6b. True -> apply Worksheet 4 line 21 to 6b + check 1040 "
               "line 6c. The WS1-vs-WS4 comparison is always computed (D_RET_008)." )},
    {"fact_key": "lse_earlier_year", "label": "Lump-sum: the earlier year a portion is attributable to",
     "data_type": "string", "sort_order": 34,
     "notes": "PER EARLIER YEAR (SocialSecurityLumpSum row). The year from SSA-1099 box 3 (post-1993 -> Worksheet 2)."},
    {"fact_key": "lse_lump_sum_for_year", "label": "Lump-sum: amount of the 2025 lump-sum attributable to the earlier year",
     "data_type": "decimal", "default_value": "0", "sort_order": 35,
     "notes": "PER EARLIER YEAR. WS2 line 1 second addend; Σ across rows = the 'pre-2025 lump sum' subtracted at WS4 line 1."},
    {"fact_key": "lse_earlier_year_net_benefits", "label": "Lump-sum: SSA box 5 benefits actually received IN the earlier year",
     "data_type": "decimal", "default_value": "0", "sort_order": 36,
     "notes": "PER EARLIER YEAR. WS2 line 1 first addend (benefits received in that year, excluding the lump sum)."},
    {"fact_key": "lse_earlier_year_agi", "label": "Lump-sum: adjusted gross income for the earlier year",
     "data_type": "decimal", "default_value": "0", "sort_order": 37,
     "notes": "PER EARLIER YEAR. WS2 line 3 (preparer-asserted from the earlier-year return). AGI already includes that year's taxable SS."},
    {"fact_key": "lse_earlier_year_adjustments", "label": "Lump-sum: earlier-year exclusions/adjustments (8839/8815/2555/etc.)",
     "data_type": "decimal", "default_value": "0", "sort_order": 38,
     "notes": "PER EARLIER YEAR. WS2 line 4 (usually 0)."},
    {"fact_key": "lse_earlier_year_taxexempt", "label": "Lump-sum: tax-exempt interest received in the earlier year",
     "data_type": "decimal", "default_value": "0", "sort_order": 39,
     "notes": "PER EARLIER YEAR. WS2 line 5."},
    {"fact_key": "lse_earlier_year_prior_taxable_ss", "label": "Lump-sum: taxable SS benefits previously reported for the earlier year",
     "data_type": "decimal", "default_value": "0", "sort_order": 40,
     "notes": "PER EARLIER YEAR. WS2 line 7 AND line 20 (the previously-reported taxable benefits; AGI in line 3 already contains it)."},
    {"fact_key": "lse_earlier_year_mfj", "label": "Lump-sum: earlier-year filing status was married filing jointly",
     "data_type": "boolean", "sort_order": 41,
     "notes": "PER EARLIER YEAR. True -> WS2 base $32,000 / tier $12,000; else $25,000 / $9,000."},
    {"fact_key": "lse_earlier_year_mfs_with_spouse", "label": "Lump-sum: earlier-year MFS and lived with spouse",
     "data_type": "boolean", "sort_order": 42,
     "notes": "PER EARLIER YEAR. True -> WS2 skips lines 9-16 (85% from dollar one), like the current-year MFS-with-spouse path."},
    # ── SSA-1099 withholding / Medicare / Railroad facts (AMENDMENT 2026-06-30) ──
    {"fact_key": "ssa_fed_withheld", "label": "SSA-1099 box 6 / RRB-1099 box 10: federal income tax withheld",
     "data_type": "decimal", "default_value": "0", "sort_order": 43,
     "notes": ("RETURN LEVEL (taxpayer + spouse). Voluntary federal withholding on Social Security / Railroad "
               "Retirement benefits -> 1040 line 25b (i1040 line 25b 'Form(s) 1099'); NOT 25a (W-2) or 25c.")},
    {"fact_key": "ssa_medicare_premiums", "label": "Medicare premiums deducted from SSA/RRB benefits (Part B/C/D, Medigap)",
     "data_type": "decimal", "default_value": "0", "sort_order": 44,
     "notes": ("RETURN LEVEL (taxpayer + spouse). Part B/D (and voluntarily-enrolled Part A, Part C/Medigap) are "
               "deductible medical expenses (Pub 502). Routed per ssa_medicare_destination -> Schedule A line 1 "
               "OR self-employed health insurance (Form 7206 -> Schedule 1 line 17).")},
    {"fact_key": "ssa_medicare_destination", "label": "Where Medicare premiums are deducted: 'schedule_a' or 'sehi'",
     "data_type": "string", "default_value": "schedule_a", "sort_order": 45,
     "notes": ("RETURN LEVEL. 'schedule_a' (default) -> Sch A line 1 medical (Pub 502). 'sehi' -> self-employed "
               "health insurance premium (Form 7206 -> Sch 1 line 17), capped at the single proprietor's net SE "
               "profit; multiple businesses or Marketplace/PTC coverage -> D_RET_009 RED.")},
    {"fact_key": "ssa_is_railroad", "label": "Benefits are Railroad Retirement (RRB-1099 SSEB, Tier 1)",
     "data_type": "boolean", "sort_order": 46,
     "notes": ("RETURN LEVEL. RRB-1099 SSEB (Social Security Equivalent Benefit, Tier 1) is taxed IDENTICALLY to "
               "SSA-1099 social security -> pooled into box-5 net benefits / the same worksheet -> 6a/6b (Pub 915). "
               "Label/metadata only (no separate math). NSSEB/Tier 2 (RRB-1099-R) = pension, OUT (Simplified Method).")},
    # ── 5329 linkage facts (return level; consumed by the 5329 form) ──
    {"fact_key": "exception_number_5329", "label": "Form 5329 line 2: early-distribution exception number (01-23 or 99)",
     "data_type": "string", "sort_order": 40,
     "notes": ("RETURN LEVEL (per early-distribution document at the build leg). FULL CATALOG: 01-23 (i5329 "
               "line-2 table, incl. SECURE 2.0 codes 20 terminal-illness / 22 domestic-abuse / 23 emergency-"
               "expense) + 99 (more than one exception). An out-of-range entry -> D_RET_006 RED. Blank = no "
               "exception -> full 10%/25%. Account-type applicability (01/06 not-IRA; 07/08/09 IRA-only) is "
               "a tts-side diagnostic.")},
    {"fact_key": "exception_amount_5329", "label": "Form 5329 line 2: amount excluded under the exception", "data_type": "decimal",
     "default_value": "0", "sort_order": 41,
     "notes": "RETURN LEVEL. The portion of the early distribution covered by the exception number. <= line 1."},
    # ── Worksheet/aggregate outputs (traceability) ──
    {"fact_key": "ss_base_amount", "label": "SS Worksheet line 8: base amount (filing-status keyed)", "data_type": "decimal",
     "sort_order": 50,
     "notes": "CONSTANT (statutory §86, non-indexed): MFJ 32,000; single/HOH/QSS/MFS-apart 25,000; MFS-with-spouse n/a (85% path)."},
    {"fact_key": "ss_second_tier", "label": "SS Worksheet line 10: second-tier amount (filing-status keyed)", "data_type": "decimal",
     "sort_order": 51, "notes": "CONSTANT (statutory §86, non-indexed): MFJ 12,000; others 9,000."},
]

RET_RULES: list[dict] = [
    # ── Distribution-code routing (the spine of the topic) ──
    {"rule_id": "R-RET-CODE", "title": "Box 7 distribution-code routing (v1 supported set + RED gate)",
     "rule_type": "routing", "precedence": 0, "sort_order": 1,
     "formula": (
         "Per document, classify by box 7 code(s): "
         "SUPPORTED (compute taxable from box 2a): 1,2,3,4,7,8,9,B,D + IRA flow. "
         "ROLLOVER (0 taxable, 'Rollover'): G,H. QCD (reduce 4b, 'QCD'): Y. "
         "ROTH-QUALIFIED (0 taxable): Q. EARLY (-> 5329, v1): 1 (10%), S (25%). "
         "RED-UNSUPPORTED (D_RET_003), OUT of the v1 set: A (4972), 5 (prohibited), "
         "6 (1035), J (Roth early — needs Form 8606 basis), T (Roth exception — "
         "needs basis), C,E,F,K,L,M,N,P,R,U,W, and any unrecognized code. "
         "(J/T are early/Roth in tax law but are NOT in v1 — always RED, never "
         "computed.)"),
     "inputs": ["r_box7_codes", "r_box7_ira_sep_simple", "r_box2a_taxable"], "outputs": [],
     "description": ("ONCE PER DOCUMENT. JUDGMENT 1 (Ken-confirmed v1 set). i1099r Table 1. Unsupported codes "
                     "fire RED 'prepare manually' (no silent gap, SPRINT quality rule 2). Two-code combos "
                     "(e.g. '4G', '7A') route on the more-restrictive member.")},
    {"rule_id": "R-RET-4AB", "title": "IRA distributions -> 1040 lines 4a (gross) / 4b (taxable)",
     "rule_type": "calculation", "precedence": 1, "sort_order": 2,
     "formula": ("Over 1099-R docs with box-7 IRA/SEP/SIMPLE CHECKED: "
                 "4a = SUM(box1); 4b = SUM(box2a - rollover_amount - qcd_amount), floored at 0 per doc. "
                 "Code Q/G/H docs contribute box1 to 4a with 0 to 4b."),
     "inputs": ["r_box1_gross", "r_box2a_taxable", "r_rollover_amount", "r_qcd_amount", "r_box7_ira_sep_simple"],
     "outputs": ["1040.L4a", "1040.L4b"],
     "description": ("ONCE PER RETURN. i1040gi lines 4a/4b. Computed feeders (YELLOW); preparer override = escape "
                     "hatch. 'Rollover'/'QCD' literals render next to 4b when those amounts are nonzero.")},
    {"rule_id": "R-RET-5AB", "title": "Pensions and annuities -> 1040 lines 5a (gross) / 5b (taxable)",
     "rule_type": "calculation", "precedence": 1, "sort_order": 3,
     "formula": ("Over 1099-R docs with box-7 IRA/SEP/SIMPLE UNCHECKED: "
                 "5a = SUM(box1); 5b = SUM(box2a - rollover_amount), floored at 0 per doc. "
                 "QCD does not apply to non-IRA pensions."),
     "inputs": ["r_box1_gross", "r_box2a_taxable", "r_rollover_amount", "r_box7_ira_sep_simple"],
     "outputs": ["1040.L5a", "1040.L5b"],
     "description": "ONCE PER RETURN. i1040gi lines 5a/5b. Computed feeders (YELLOW). Box-2a-blank -> Simplified Method RED."},
    {"rule_id": "R-RET-25B", "title": "1040 line 25b withholding roster EXTENDS to 1099-R box 4",
     "rule_type": "calculation", "precedence": 1, "sort_order": 4,
     "formula": "L25b += SUM over 1099-R docs [box4] (on top of the 1099-INT + 1099-DIV box-4 addends)",
     "inputs": ["r_box4_fed_withheld"], "outputs": ["1040.L25b"],
     "description": ("ONCE PER RETURN. Extends spine R-PAY-02 again (Topic 3 added 1099-DIV box 4; this adds "
                     "1099-R box 4). Override stays for any still-unmodeled withholding source.")},
    {"rule_id": "R-RET-25B-SS", "title": "1040 line 25b withholding roster EXTENDS to SSA-1099/RRB-1099 withholding",
     "rule_type": "calculation", "precedence": 1, "sort_order": 6,
     "formula": "L25b += ssa_fed_withheld (on top of the 1099-INT + 1099-DIV + 1099-R box-4 addends)",
     "inputs": ["ssa_fed_withheld"], "outputs": ["1040.L25b"],
     "description": ("ONCE PER RETURN. Extends the R-RET-25B roster once more: SSA-1099 box 6 and RRB-1099 box 10 "
                     "voluntary federal withholding land on 1040 line 25b ('Form(s) 1099'). Was previously handled "
                     "only by the manual 25b override (AMENDMENT 2026-06-30).")},
    {"rule_id": "R-RET-MEDICARE", "title": "Medicare premiums -> Schedule A medical OR self-employed health insurance",
     "rule_type": "routing", "precedence": 9, "sort_order": 7,
     "formula": ("IF ssa_medicare_destination == 'sehi': add ssa_medicare_premiums to the self-employed health "
                 "insurance premium total (Form 7206 line 1) for the single proprietor, capped at net SE profit "
                 "-> Schedule 1 line 17. ELSE (default 'schedule_a'): add ssa_medicare_premiums to Schedule A "
                 "line 1 medical expenses (before the 7.5% AGI floor) -> Schedule A line 4."),
     "inputs": ["ssa_medicare_premiums", "ssa_medicare_destination"], "outputs": ["SCHEDULE_A.L1", "SCH_1.L17"],
     "description": ("ONCE PER RETURN. Pub 502: Medicare Part B/D (+ voluntary Part A, Part C/Medigap) are "
                     "deductible medical expenses. Form 7206: Medicare premiums qualify as self-employed health "
                     "insurance for a self-employed taxpayer. v1 SEHI = a SINGLE proprietor, capped at that "
                     "proprietor's net SE profit; multiple Sch C/F businesses or Marketplace/PTC coverage -> "
                     "D_RET_009 RED (verify manually). AMENDMENT 2026-06-30.")},
    # ── Form 5329 early-distribution identification (feeds the 5329 form) ──
    {"rule_id": "R-RET-EARLY", "title": "Identify early-distribution amount feeding Form 5329 line 1",
     "rule_type": "calculation", "precedence": 2, "sort_order": 5,
     "formula": ("early_distributions = SUM over docs with an EARLY code (1, J, or S) of the taxable amount "
                 "(box 2a) included in income, LESS any rolled-over portion. Feeds 5329 line 1."),
     "inputs": ["r_box7_codes", "r_box2a_taxable", "r_rollover_amount"], "outputs": ["5329.L1"],
     "description": ("ONCE PER RETURN. Codes 1/J/S = early (i1099r). Cross-form feeder to the 5329 form's "
                     "line 1 (the INTDIV->SCH_B cross-form pattern). Rolled-over portions are excluded "
                     "(i5329 rollover rule).")},
    # ── Social Security Benefits Worksheet (lines 6a/6b) ──
    {"rule_id": "R-RET-SS-01", "title": "SS Worksheet WS1-WS7: provisional income",
     "rule_type": "calculation", "precedence": 3, "sort_order": 10,
     "formula": ("WS1 = ssa_box5_net_benefits (-> 1040 6a); WS2 = 0.50 x WS1; "
                 "WS3 = 1040(L1z + L2b + L3b + L4b + L5b + L7a + L8); WS4 = 1040 L2a; "
                 "WS5 = WS2 + WS3 + WS4; WS6 = Sch 1 (L11..L20 + L23 + L25); "
                 "WS7 = max(0, WS5 - WS6). IF WS6 >= WS5: 6b = 0 (none taxable)."),
     "inputs": ["ssa_box5_net_benefits"], "outputs": ["ws_1", "ws_2", "ws_3", "ws_4", "ws_5", "ws_6", "ws_7", "1040.L6a"],
     "description": ("ONCE PER RETURN. i1040gi p.31 verbatim. Provisional income = MAGI(excl. SS) + ½ SS. "
                     "Runs AFTER Topic 3 (2b/3b/7a) + this topic's (4b/5b) aggregation since WS3 reads them.")},
    {"rule_id": "R-RET-SS-02", "title": "SS Worksheet WS8-WS18: 50%/85% tiers -> 1040 line 6b",
     "rule_type": "calculation", "precedence": 4, "sort_order": 11,
     "formula": ("WS8 = base(filing_status) [32,000 MFJ; 25,000 single/HOH/QSS/MFS-apart]; "
                 "IF MFS-lived-with-spouse: WS16 = 0.85 x WS7, skip to WS17. "
                 "IF WS8 >= WS7: 6b = 0. ELSE WS9 = WS7 - WS8; WS10 = second_tier [12,000 MFJ; 9,000 other]; "
                 "WS11 = max(0, WS9 - WS10); WS12 = min(WS9, WS10); WS13 = 0.5 x WS12; WS14 = min(WS2, WS13); "
                 "WS15 = 0.85 x WS11; WS16 = WS14 + WS15; WS17 = 0.85 x WS1; "
                 "WS18 = min(WS16, WS17) -> 1040 line 6b."),
     "inputs": ["ss_base_amount", "ss_second_tier", "mfs_lived_with_spouse"], "outputs": ["1040.L6b"],
     "description": ("ONCE PER RETURN. i1040gi p.31 lines 8-18 verbatim. STATUTORY constants (§86, non-indexed) "
                     "- same both years. 85% is the absolute cap (WS17). Renders as a statement page.")},
    {"rule_id": "R-RET-SS-VAL", "title": "SS Worksheet partition: WS18 <= 0.85 x WS1 always",
     "rule_type": "validation", "precedence": 5, "sort_order": 12,
     "formula": "taxable SS (6b) <= 85% of net benefits (WS17), and 6b <= WS1",
     "inputs": [], "outputs": [],
     "description": "ONCE PER RETURN. The 85% cap is algebraic (WS18 = min(WS16, WS17)) — wired as a flow assertion."},
    # ── Lump-Sum Election (Pub 915 Worksheets 2 + 4) — AMENDMENT 2026-06-28 ──
    {"rule_id": "R-RET-LSE-WS2", "title": "Worksheet 2 (per earlier year): ADDITIONAL taxable benefits from the lump sum",
     "rule_type": "calculation", "precedence": 6, "sort_order": 13,
     "formula": (
         "PER EARLIER YEAR (post-1993). L1 = lse_earlier_year_net_benefits + lse_lump_sum_for_year. "
         "IF L1 <= 0: L21 = 0. ELSE L2 = 0.5*L1; L6 = L2 + lse_earlier_year_agi + lse_earlier_year_adjustments "
         "+ lse_earlier_year_taxexempt; L8 = L6 - lse_earlier_year_prior_taxable_ss. "
         "base/tier = (32000/12000) if lse_earlier_year_mfj else (25000/9000). "
         "IF lse_earlier_year_mfs_with_spouse: L19 = min(max(0,0.85*L8), 0.85*L1). "
         "ELIF L8 <= base: L19 = 0. ELSE L10 = L8-base; L12 = max(0, L10-tier); L13 = min(L10,tier); "
         "L14 = 0.5*L13; L15 = min(L2,L14); L16 = 0.85*L12; L17 = L15+L16; L18 = 0.85*L1; L19 = min(L17,L18). "
         "L21 = L19 - lse_earlier_year_prior_taxable_ss (>= 0; refigured >= previously-reported)."),
     "inputs": ["lse_earlier_year_net_benefits", "lse_lump_sum_for_year", "lse_earlier_year_agi",
                "lse_earlier_year_adjustments", "lse_earlier_year_taxexempt", "lse_earlier_year_prior_taxable_ss",
                "lse_earlier_year_mfj", "lse_earlier_year_mfs_with_spouse"],
     "outputs": ["lse_ws2_21"],
     "description": ("PER EARLIER YEAR. Pub 915 Worksheet 2 verbatim. Refigures the earlier year's taxable benefits "
                     "WITH the lump-sum portion added (L1), subtracts the previously-reported taxable benefits "
                     "(already inside AGI at L3, removed at L8) -> the additional taxable benefits (L21) -> WS4 L20. "
                     "Same 50%/85% tier math as the regular worksheet.")},
    {"rule_id": "R-RET-LSE-WS4", "title": "Worksheet 4: taxable benefits under the lump-sum election method",
     "rule_type": "calculation", "precedence": 7, "sort_order": 14,
     "formula": (
         "L1 = ssa_box5_net_benefits - SUM(lse_lump_sum_for_year over rows) [the pre-2025 lump sum]. "
         "IF L1 <= 0: L19 = 0. ELSE L2 = 0.5*L1; L6 = L2 + WS1.L3(ws_3) + WS1.L4(ws_4) + WS1.L5(0); "
         "L8 = L6 - WS1.L7(ws_6). base = WS1.L9(ws_8); tier = WS1.L11(ws_10). "
         "IF mfs_lived_with_spouse: L19 = min(max(0,0.85*L8), 0.85*L1). ELIF L8 <= base: L19 = 0. "
         "ELSE L10 = L8-base; L12 = max(0,L10-tier); L13 = min(L10,tier); L14 = 0.5*L13; L15 = min(L2,L14); "
         "L16 = 0.85*L12; L17 = L15+L16; L18 = 0.85*L1; L19 = min(L17,L18). "
         "L20 = SUM(lse_ws2_21 over rows). L21 = L19 + L20 = taxable benefits under the election."),
     "inputs": ["ssa_box5_net_benefits", "lse_lump_sum_for_year", "mfs_lived_with_spouse"],
     "outputs": ["lse_ws4_21"],
     "description": ("ONCE PER RETURN. Pub 915 Worksheet 4 verbatim. Reuses the regular worksheet's 2025 income "
                     "context (WS1 lines 3/4/5/7/9/11 = the 1040_RETIREMENT ws_3/ws_4/0/ws_6/ws_8/ws_10) but starts "
                     "from box 5 reduced by the pre-2025 lump sum, then ADDS the Σ Worksheet-2 additionals. WS1 line "
                     "5 (Form 8839/2555/4563 exclusions) is folded to 0 here, matching R-RET-SS-01's ws_5.")},
    {"rule_id": "R-RET-LSE-ELECT", "title": "Apply the lump-sum election to 1040 line 6b (explicit toggle) + box 6c",
     "rule_type": "routing", "precedence": 8, "sort_order": 15,
     "formula": (
         "Always compute lse_ws4_21 (WS4) and ws_18 (WS1, the regular 6b) for the comparison (D_RET_008). "
         "IF ss_lump_sum_election is True: 1040 line 6b = lse_ws4_21 AND check 1040 line 6c (lump-sum-election box). "
         "ELSE 6b = ws_18 (regular). The preparer's explicit toggle governs (the election is irrevocable without "
         "IRS consent — Ken 2026-06-28); a preparer override on 6b still wins over both."),
     "inputs": ["ss_lump_sum_election"], "outputs": ["1040.L6b", "1040.L6c"],
     "description": ("ONCE PER RETURN. JUDGMENT (Ken 2026-06-28): explicit-toggle election, NOT auto-apply. Runs "
                     "AFTER R-RET-SS-02 (which wrote the regular 6b) and supersedes 6b only when the toggle is on. "
                     "Checks the 6c box on the rendered 1040. D_RET_008 surfaces the WS1-vs-WS4 comparison + savings.")},
]

RET_LINES: list[dict] = [
    {"line_number": "agg_4a", "description": "Aggregated IRA distributions (gross) -> Form 1040 line 4a",
     "line_type": "total", "source_rules": ["R-RET-4AB"], "destination_form": "Form 1040 line 4a", "sort_order": 1},
    {"line_number": "agg_4b", "description": "Aggregated IRA taxable (net of rollover/QCD) -> Form 1040 line 4b",
     "line_type": "total", "source_rules": ["R-RET-4AB"], "destination_form": "Form 1040 line 4b", "sort_order": 2,
     "notes": "'Rollover'/'QCD' literal renders next to 4b when present."},
    {"line_number": "agg_5a", "description": "Aggregated pensions/annuities (gross) -> Form 1040 line 5a",
     "line_type": "total", "source_rules": ["R-RET-5AB"], "destination_form": "Form 1040 line 5a", "sort_order": 3},
    {"line_number": "agg_5b", "description": "Aggregated pensions/annuities taxable -> Form 1040 line 5b",
     "line_type": "total", "source_rules": ["R-RET-5AB"], "destination_form": "Form 1040 line 5b", "sort_order": 4},
    {"line_number": "agg_6a", "description": "Social security benefits (gross, SSA box 5) -> Form 1040 line 6a",
     "line_type": "total", "source_rules": ["R-RET-SS-01"], "destination_form": "Form 1040 line 6a", "sort_order": 5},
    {"line_number": "agg_6b", "description": "Taxable social security -> Form 1040 line 6b",
     "line_type": "total", "source_rules": ["R-RET-SS-02"], "destination_form": "Form 1040 line 6b", "sort_order": 6},
    # SS worksheet lines (statement-page render)
    {"line_number": "ws_1", "description": "SS WS1: total SSA/RRB box 5 net benefits", "line_type": "calculated",
     "source_rules": ["R-RET-SS-01"], "sort_order": 10},
    {"line_number": "ws_2", "description": "SS WS2 = 50% x WS1", "line_type": "calculated", "source_rules": ["R-RET-SS-01"], "sort_order": 11},
    {"line_number": "ws_3", "description": "SS WS3 = 1040 lines 1z+2b+3b+4b+5b+7a+8", "line_type": "calculated",
     "source_rules": ["R-RET-SS-01"], "sort_order": 12},
    {"line_number": "ws_4", "description": "SS WS4 = 1040 line 2a (tax-exempt interest)", "line_type": "calculated",
     "source_rules": ["R-RET-SS-01"], "sort_order": 13},
    {"line_number": "ws_5", "description": "SS WS5 = WS2 + WS3 + WS4", "line_type": "calculated", "source_rules": ["R-RET-SS-01"], "sort_order": 14},
    {"line_number": "ws_6", "description": "SS WS6 = Schedule 1 lines 11-20 + 23 + 25 (adjustments)", "line_type": "calculated",
     "source_rules": ["R-RET-SS-01"], "sort_order": 15},
    {"line_number": "ws_7", "description": "SS WS7 = max(0, WS5 - WS6)", "line_type": "calculated", "source_rules": ["R-RET-SS-01"], "sort_order": 16},
    {"line_number": "ws_8", "description": "SS WS8 = base amount (32,000 MFJ / 25,000 other)", "line_type": "calculated",
     "source_rules": ["R-RET-SS-02"], "sort_order": 17},
    {"line_number": "ws_9", "description": "SS WS9 = WS7 - WS8", "line_type": "calculated", "source_rules": ["R-RET-SS-02"], "sort_order": 18},
    {"line_number": "ws_10", "description": "SS WS10 = second tier (12,000 MFJ / 9,000 other)", "line_type": "calculated",
     "source_rules": ["R-RET-SS-02"], "sort_order": 19},
    {"line_number": "ws_11", "description": "SS WS11 = max(0, WS9 - WS10)", "line_type": "calculated", "source_rules": ["R-RET-SS-02"], "sort_order": 20},
    {"line_number": "ws_12", "description": "SS WS12 = min(WS9, WS10)", "line_type": "calculated", "source_rules": ["R-RET-SS-02"], "sort_order": 21},
    {"line_number": "ws_13", "description": "SS WS13 = 50% x WS12", "line_type": "calculated", "source_rules": ["R-RET-SS-02"], "sort_order": 22},
    {"line_number": "ws_14", "description": "SS WS14 = min(WS2, WS13)", "line_type": "calculated", "source_rules": ["R-RET-SS-02"], "sort_order": 23},
    {"line_number": "ws_15", "description": "SS WS15 = 85% x WS11", "line_type": "calculated", "source_rules": ["R-RET-SS-02"], "sort_order": 24},
    {"line_number": "ws_16", "description": "SS WS16 = WS14 + WS15", "line_type": "calculated", "source_rules": ["R-RET-SS-02"], "sort_order": 25},
    {"line_number": "ws_17", "description": "SS WS17 = 85% x WS1 (absolute cap)", "line_type": "calculated", "source_rules": ["R-RET-SS-02"], "sort_order": 26},
    {"line_number": "ws_18", "description": "SS WS18 = min(WS16, WS17) -> Form 1040 line 6b", "line_type": "total",
     "source_rules": ["R-RET-SS-02"], "destination_form": "Form 1040 line 6b", "sort_order": 27},
    # Lump-Sum Election outputs (AMENDMENT 2026-06-28)
    {"line_number": "lse_ws2_21", "description": "Pub 915 Worksheet 2 line 21: additional taxable benefits per earlier year",
     "line_type": "calculated", "source_rules": ["R-RET-LSE-WS2"], "sort_order": 30,
     "notes": "PER EARLIER YEAR; Σ -> Worksheet 4 line 20."},
    {"line_number": "lse_ws4_21", "description": "Pub 915 Worksheet 4 line 21: taxable benefits under the lump-sum election",
     "line_type": "total", "source_rules": ["R-RET-LSE-WS4", "R-RET-LSE-ELECT"],
     "destination_form": "Form 1040 line 6b (when ss_lump_sum_election)", "sort_order": 31,
     "notes": "When the election toggle is on, supersedes ws_18 on 1040 line 6b + checks line 6c."},
]

RET_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_RET_001", "title": "Simplified Method needed (box 2a blank / 'not determined' + basis)",
     "severity": "error",
     "condition": "any 1099-R doc with (r_box2b_not_determined OR r_box2a_taxable blank) AND (r_box5_basis > 0 OR r_box9b_total_contrib > 0)",
     "message": ("Not supported — prepare manually: a 1099-R has no taxable amount in box 2a (or 'taxable amount "
                 "not determined' is checked) with basis indicated. The Simplified Method / General Rule is "
                 "required to figure the taxable portion (the OPM CSA-1099-R pattern); this distribution is NOT "
                 "computed."),
     "notes": "SPRINT_SCOPE: Simplified Method OUT this sprint (post-sprint #2). Most payers (TRS) report box 2a."},
    {"diagnostic_id": "D_RET_002", "title": "Net Unrealized Appreciation present (box 6) — unsupported",
     "severity": "error",
     "condition": "any 1099-R doc has r_box6_nua > 0",
     "message": ("Not supported — prepare manually: box 6 reports net unrealized appreciation (NUA) in employer "
                 "securities. The NUA election (deferral to capital-gain treatment at sale) is not modeled; this "
                 "distribution is NOT computed."),
     "notes": "Lump-sum/NUA territory (Pub 575). Stored only."},
    {"diagnostic_id": "D_RET_003", "title": "Unsupported distribution code", "severity": "error",
     "condition": "any 1099-R doc has a box-7 code not in the v1 supported set {1,2,3,4,7,8,9,B,D,G,H,Q,S,Y} (J and T are OUT of v1 -> always RED)",
     "message": ("Not supported — prepare manually: the 1099-R distribution code is outside this version's "
                 "supported set (e.g. A=10-year option/Form 4972, 5=prohibited transaction, 6=§1035 exchange, "
                 "N/R=recharacterization, or a Roth code J/T with a blank box 2a needing Form 8606 basis). This "
                 "distribution is NOT computed."),
     "notes": "JUDGMENT 1. v1 supported set Ken-confirmed 2026-06-11."},
    {"diagnostic_id": "D_RET_004", "title": "Social Security lump-sum election — earlier-year data missing",
     "severity": "error",
     "condition": ("ssa_lump_sum_prior_year is True AND no complete SocialSecurityLumpSum row exists "
                   "(no earlier-year row with lse_lump_sum_for_year > 0)"),
     "message": ("A lump-sum Social Security payment for an earlier year is indicated, but the earlier-year data "
                 "needed for the Pub 915 lump-sum election (the amount for each year, plus that year's AGI, "
                 "tax-exempt interest, and previously-reported taxable benefits) is missing or incomplete. The "
                 "election cannot be computed, so only the regular worksheet (all benefits taxed in 2025) is "
                 "applied. Enter the earlier-year rows, or clear the lump-sum indicator."),
     "notes": ("AMENDMENT 2026-06-28: was a blanket 'not supported' RED; the lump-sum election is now COMPUTED "
               "(R-RET-LSE-WS2/WS4/ELECT). This RED is the no-silent-gap guard that the election data is present "
               "when a lump sum is indicated — so we never quietly leave the election off for lack of inputs.")},
    {"diagnostic_id": "D_RET_005", "title": "IRA deduction with taxable Social Security — circular interaction",
     "severity": "error",
     "condition": "Schedule 1 line 20 (IRA deduction) > 0 AND ssa_box5_net_benefits > 0 AND 6b > 0",
     "message": ("Not supported — verify manually: an IRA deduction (Schedule 1 line 20) is present alongside "
                 "taxable Social Security. These interact circularly (the worksheets in Pub 590-A / Pub 915 must "
                 "be computed together); the values shown do not resolve the circular and must be verified."),
     "notes": "SPRINT_SCOPE Topic 5 DoD: IRA-deduction <-> taxable-SS circular RED."},
    {"diagnostic_id": "D_RET_006", "title": "Invalid Form 5329 exception number", "severity": "error",
     "condition": "exception_number_5329 is non-blank and not in {01..23, 99}",
     "message": ("Invalid Form 5329 line-2 exception number. Enter a number from the i5329 table (01-23), or 99 if "
                 "more than one exception applies. The current entry is not a recognized exception code."),
     "notes": ("FULL CATALOG (2026-06-25): 01-23 + 99 are all supported (the preparer asserts the exclusion amount). "
               "Was a >12 'unsupported' gap; now a validity guard on a garbage entry. Account-type applicability "
               "(01/06 not-IRA; 07/08/09 IRA-only) is a separate tts-side diagnostic.")},
    {"diagnostic_id": "D_RET_007", "title": "SIMPLE-IRA first-2-years early distribution — 25% rate", "severity": "info",
     "condition": "any 1099-R doc has box-7 code S (or code 1 from a SIMPLE in the first 2 years)",
     "message": ("This early distribution is from a SIMPLE IRA within the first 2 years (code S) — the additional "
                 "tax is 25%, not 10% (Form 5329 Part I caution). Verify the rate applied."),
     "notes": "Informational confirmation that the 25% branch engaged."},
    {"diagnostic_id": "D_RET_008", "title": "Social Security lump-sum election — comparison result", "severity": "info",
     "condition": "at least one complete SocialSecurityLumpSum row exists (the election is computable)",
     "message": ("Lump-sum election comparison — regular method (Worksheet 1) taxable Social Security vs the "
                 "Pub 915 lump-sum election method (Worksheet 4). The tts side fills the two amounts and adapts "
                 "the wording: (a) election OFF and the election would lower taxable SS -> WARNING 'electing "
                 "would lower taxable Social Security by $X; check the lump-sum election box to apply it'; "
                 "(b) election ON and beneficial -> INFO 'election applied; it lowers taxable Social Security by "
                 "$X'; (c) election ON but NOT beneficial -> WARNING 'the election does not lower taxable Social "
                 "Security; the regular method is lower or equal — consider clearing the election'."),
     "notes": ("AMENDMENT 2026-06-28: surfaces the WS1-vs-WS4 comparison + savings. Severity/message adapt on the "
               "tts side (bridge-gated to the same compute_ss_lumpsum helper). Pub 915 'Will the lump-sum election "
               "lower your taxable benefits?' decision step.")},
    {"diagnostic_id": "D_RET_009", "title": "Medicare-as-SEHI with multiple businesses or Marketplace/PTC — verify manually",
     "severity": "error",
     "condition": ("ssa_medicare_destination == 'sehi' AND ssa_medicare_premiums > 0 AND (more than one Sch C/F "
                   "proprietorship with net profit OR Marketplace/Form 8962 PTC coverage present)"),
     "message": ("Not auto-computed — verify manually: Medicare premiums are routed to the self-employed health "
                 "insurance deduction, but there are multiple self-employed businesses (premium allocation is a "
                 "preparer choice) and/or Marketplace coverage with the Premium Tax Credit (the Pub 974 SEHI<->PTC "
                 "iterative applies). The single-proprietor SEHI shortcut is not applied; figure the deduction by hand."),
     "notes": ("AMENDMENT 2026-06-30. v1 boundary: SEHI Medicare = a single proprietor capped at net SE profit. "
               "Multi-business apportionment + the Form 8962 PTC interaction (Pub 974) are out of v1.")},
]

RET_SCENARIOS: list[dict] = [
    # ── Aggregation ──
    {"scenario_name": "RET-T1 — normal pension (code 7): 5a = 5b = 30,000",
     "scenario_type": "normal", "sort_order": 1,
     "inputs": {"r_docs": [{"box1": 30000, "box2a": 30000, "code": "7", "ira": False}]},
     "expected_outputs": {"1040_line_5a": 30000, "1040_line_5b": 30000, "1040_line_4a": 0, "1040_line_4b": 0},
     "notes": "Box-7 IRA unchecked -> pension lines. Fully taxable per box 2a."},
    {"scenario_name": "RET-T2 — IRA normal (code 7, IRA box): 4a = 4b = 25,000",
     "scenario_type": "normal", "sort_order": 2,
     "inputs": {"r_docs": [{"box1": 25000, "box2a": 25000, "code": "7", "ira": True}]},
     "expected_outputs": {"1040_line_4a": 25000, "1040_line_4b": 25000, "1040_line_5a": 0, "1040_line_5b": 0},
     "notes": "IRA/SEP/SIMPLE checkbox routes to 4a/4b."},
    {"scenario_name": "RET-T3 — direct rollover (code G): 5a = 50,000, 5b = 0 ('Rollover')",
     "scenario_type": "normal", "sort_order": 3,
     "inputs": {"r_docs": [{"box1": 50000, "box2a": 0, "code": "G", "ira": False, "rollover": 50000}]},
     "expected_outputs": {"1040_line_5a": 50000, "1040_line_5b": 0, "rollover_literal": True},
     "notes": "Code G + rollover_amount=50,000 -> gross on 5a, 0 taxable, 'Rollover' literal."},
    {"scenario_name": "RET-T4 — QCD (code 7 + Y, IRA): 4a = 10,000, 4b = 0 ('QCD')",
     "scenario_type": "normal", "sort_order": 4,
     "inputs": {"r_docs": [{"box1": 10000, "box2a": 10000, "code": "7Y", "ira": True, "qcd": 10000}]},
     "expected_outputs": {"1040_line_4a": 10000, "1040_line_4b": 0, "qcd_literal": True},
     "notes": "QCD reduces 4b to 0; 'QCD' literal. Code Y pairs with 7."},
    {"scenario_name": "RET-T5 — box 4 withholding flows to 25b",
     "scenario_type": "normal", "sort_order": 5,
     "inputs": {"r_docs": [{"box1": 20000, "box2a": 20000, "box4": 3000, "code": "7", "ira": True}]},
     "expected_outputs": {"1040_line_4b": 20000, "1040_line_25b": 3000},
     "notes": "Extends the 25b roster (1099-INT + 1099-DIV + now 1099-R box 4)."},
    # ── Form 5329 ──
    {"scenario_name": "RET-5329-1 — early (code 1) $20,000 no exception: Sch 2 line 8 = 2,000",
     "scenario_type": "normal", "sort_order": 10,
     "inputs": {"r_docs": [{"box1": 20000, "box2a": 20000, "code": "1", "ira": True}]},
     "expected_outputs": {"5329_line_1": 20000, "5329_line_3": 20000, "5329_line_4": 2000, "schedule_2_line_8": 2000,
                          "form_5329_generated": False},
     "notes": "Pure code-1 full-amount -> 10% direct to Sch 2 line 8 (no 5329 form needed)."},
    {"scenario_name": "RET-5329-2 — early (code 1) $20,000, exception 08 $8,000: Sch 2 line 8 = 1,200",
     "scenario_type": "normal", "sort_order": 11,
     "inputs": {"r_docs": [{"box1": 20000, "box2a": 20000, "code": "1", "ira": True}],
                "exception_number_5329": "08", "exception_amount_5329": 8000},
     "expected_outputs": {"5329_line_1": 20000, "5329_line_2": 8000, "5329_line_3": 12000, "5329_line_4": 1200,
                          "schedule_2_line_8": 1200, "form_5329_generated": True},
     "notes": "Exception 08 (IRA higher education) reduces the base; 5329 form generated."},
    {"scenario_name": "RET-5329-3 — SIMPLE first-2-years (code S) $10,000: 25% = 2,500",
     "scenario_type": "edge", "sort_order": 12,
     "inputs": {"r_docs": [{"box1": 10000, "box2a": 10000, "code": "S", "ira": True}]},
     "expected_outputs": {"5329_line_1": 10000, "5329_line_3": 10000, "5329_line_4": 2500, "schedule_2_line_8": 2500,
                          "D_RET_007_fires": True},
     "notes": "Code S -> 25% rate (Form 5329 Part I caution)."},
    # ── Social Security worksheet (verified by hand against i1040gi p.31) ──
    {"scenario_name": "SS-1 — none taxable: single, SS 20,000 + pension 10,000 -> 6b = 0",
     "scenario_type": "normal", "sort_order": 20,
     "inputs": {"filing_status": "single", "ssa_box5": 20000, "other_ws3_income": 10000},
     "expected_outputs": {"ws_1": 20000, "ws_5": 20000, "ws_7": 20000, "ws_8": 25000, "1040_line_6a": 20000,
                          "1040_line_6b": 0},
     "notes": "Provisional = 10,000 + 10,000 = 20,000 < 25,000 base -> none taxable (worksheet line 9 STOP)."},
    {"scenario_name": "SS-2 — 50% tier: single, SS 20,000 + pension 20,000 -> 6b = 2,500",
     "scenario_type": "normal", "sort_order": 21,
     "inputs": {"filing_status": "single", "ssa_box5": 20000, "other_ws3_income": 20000},
     "expected_outputs": {"ws_2": 10000, "ws_7": 30000, "ws_8": 25000, "ws_9": 5000, "ws_10": 9000, "ws_11": 0,
                          "ws_12": 5000, "ws_13": 2500, "ws_14": 2500, "ws_16": 2500, "ws_17": 17000,
                          "1040_line_6b": 2500},
     "notes": ("Provisional 30,000 is between base 25,000 and adjusted base 34,000 -> 50% tier. Taxable = "
               "min(½ x (30,000-25,000), ½ x 20,000) = min(2,500, 10,000) = 2,500.")},
    {"scenario_name": "SS-3 — 85% cap: single, SS 20,000 + pension 40,000 -> 6b = 17,000",
     "scenario_type": "normal", "sort_order": 22,
     "inputs": {"filing_status": "single", "ssa_box5": 20000, "other_ws3_income": 40000},
     "expected_outputs": {"ws_2": 10000, "ws_7": 50000, "ws_8": 25000, "ws_9": 25000, "ws_10": 9000, "ws_11": 16000,
                          "ws_12": 9000, "ws_13": 4500, "ws_14": 4500, "ws_15": 13600, "ws_16": 18100,
                          "ws_17": 17000, "1040_line_6b": 17000},
     "notes": "Provisional 50,000 well above adjusted base -> capped at 85% of benefits = WS17 = 17,000."},
    {"scenario_name": "SS-4 — MFJ 85% tier: SS 30,000 + pension 40,000 -> 6b = 15,350",
     "scenario_type": "normal", "sort_order": 23,
     "inputs": {"filing_status": "mfj", "ssa_box5": 30000, "other_ws3_income": 40000},
     "expected_outputs": {"ws_2": 15000, "ws_7": 55000, "ws_8": 32000, "ws_9": 23000, "ws_10": 12000, "ws_11": 11000,
                          "ws_12": 12000, "ws_13": 6000, "ws_14": 6000, "ws_15": 9350, "ws_16": 15350,
                          "ws_17": 25500, "1040_line_6b": 15350},
     "notes": "MFJ base 32,000 / second tier 12,000. WS16 15,350 < WS17 25,500 -> 6b = 15,350 (not yet capped)."},
    {"scenario_name": "SS-5 — MFS lived with spouse: 85% from dollar one",
     "scenario_type": "edge", "sort_order": 24,
     "inputs": {"filing_status": "mfs", "mfs_lived_with_spouse": True, "ssa_box5": 10000, "other_ws3_income": 5000},
     "expected_outputs": {"ws_1": 10000, "ws_7": 10000, "ws_16": 8500, "ws_17": 8500, "1040_line_6b": 8500},
     "notes": "MFS-lived-with-spouse skips lines 8-15: WS16 = 0.85 x WS7 = 8,500; capped at WS17 = 8,500."},
    # ── RED gates ──
    {"scenario_name": "RET-G1 — box 2a blank + basis -> Simplified Method RED (D_RET_001)",
     "scenario_type": "failure", "sort_order": 30,
     "inputs": {"r_docs": [{"box1": 24000, "box2a": None, "box2b_not_determined": True, "box5": 18000, "code": "7", "ira": False}]},
     "expected_outputs": {"D_RET_001_fires": True, "5b_not_computed": True},
     "notes": "The OPM CSA-1099-R pattern: 'taxable amount not determined' + basis -> Simplified Method (out)."},
    {"scenario_name": "RET-G2 — NUA present (box 6) -> RED (D_RET_002)",
     "scenario_type": "failure", "sort_order": 31,
     "inputs": {"r_docs": [{"box1": 100000, "box2a": 60000, "box6": 40000, "code": "7", "ira": False}]},
     "expected_outputs": {"D_RET_002_fires": True},
     "notes": "Box 6 NUA election unsupported."},
    {"scenario_name": "RET-G3 — unsupported code A (10-year option) -> RED (D_RET_003)",
     "scenario_type": "failure", "sort_order": 32,
     "inputs": {"r_docs": [{"box1": 50000, "box2a": 50000, "code": "7A", "ira": False}]},
     "expected_outputs": {"D_RET_003_fires": True},
     "notes": "Code A -> Form 4972 lump-sum (out)."},
    {"scenario_name": "RET-G4 — SS lump-sum prior year -> RED (D_RET_004)",
     "scenario_type": "failure", "sort_order": 33,
     "inputs": {"filing_status": "single", "ssa_box5": 30000, "other_ws3_income": 30000, "ssa_lump_sum_prior_year": True},
     "expected_outputs": {"D_RET_004_fires": True},
     "notes": "Lump-Sum Election (Pub 915) unsupported; standard worksheet still shown."},
    {"scenario_name": "RET-G5 — invalid 5329 exception 25 -> RED (D_RET_006)",
     "scenario_type": "failure", "sort_order": 34,
     "inputs": {"r_docs": [{"box1": 15000, "box2a": 15000, "code": "1", "ira": False}], "exception_number_5329": "25"},
     "expected_outputs": {"D_RET_006_fires": True},
     "notes": "Exception 25 is outside the valid table (01-23/99) — a garbage entry. (Was '13', now a valid §457 code.)"},
    # ── Lump-Sum Election (Pub 915 Worksheets 2 + 4) — AMENDMENT 2026-06-28 ──
    {"scenario_name": "LSE-1 — Pub 915 worked example (Terry Jackson): election 2,500 < regular 3,000",
     "scenario_type": "normal", "sort_order": 40,
     "inputs": {"filing_status": "single", "ssa_box5_2025": 11000, "ws1_other_income": 25500,
                "ws1_taxexempt": 0, "ws1_adjustments": 0, "election": True,
                "earlier_years": [
                    {"year": 2024, "lump_for_year": 2000, "earlier_net_benefits": 0, "agi": 23000,
                     "adjustments": 0, "taxexempt": 0, "prior_taxable_ss": 0, "mfj": False, "mfs_with_spouse": False}]},
     "expected_outputs": {"ws1_line19": 3000, "ws2_21": [0], "ws4_line19": 2500, "ws4_line21": 2500,
                          "elected_6b": 2500, "beneficial": True},
     "notes": ("The canonical Pub 915 (2025) example, verbatim. 2024 WS2 = 0 (24,000 < 25,000 base -> line 10 No). "
               "WS4 = 2,500 < WS1 3,000 -> election applied; saves 500 of taxable SS.")},
    {"scenario_name": "LSE-2 — not beneficial: high earlier-year income makes WS4 (4,200) > WS1 (3,000)",
     "scenario_type": "edge", "sort_order": 41,
     "inputs": {"filing_status": "single", "ssa_box5_2025": 11000, "ws1_other_income": 25500,
                "ws1_taxexempt": 0, "ws1_adjustments": 0, "election": False,
                "earlier_years": [
                    {"year": 2024, "lump_for_year": 2000, "earlier_net_benefits": 0, "agi": 80000,
                     "adjustments": 0, "taxexempt": 0, "prior_taxable_ss": 0, "mfj": False, "mfs_with_spouse": False}]},
     "expected_outputs": {"ws1_line19": 3000, "ws2_21": [1700], "ws4_line19": 2500, "ws4_line21": 4200,
                          "elected_6b": 3000, "beneficial": False},
     "notes": ("Same current-year facts as LSE-1 but 2024 AGI = 80,000 -> the 2,000 lump sum is 85% taxable in 2024 "
               "(WS2 = 1,700). WS4 = 2,500 + 1,700 = 4,200 > WS1 3,000 -> NOT beneficial; election OFF keeps 3,000 "
               "(D_RET_008 reports 'does not lower'). Proves the comparison branch is load-bearing.")},
    # ── SSA withholding / Medicare (AMENDMENT 2026-06-30) ──
    {"scenario_name": "RET-WH-1 — SSA-1099 box 6 withholding 1,800 -> 1040 line 25b",
     "scenario_type": "normal", "sort_order": 6,
     "inputs": {"filing_status": "single", "ssa_box5": 24000, "other_ws3_income": 30000, "ssa_fed_withheld": 1800},
     "expected_outputs": {"1040_line_25b": 1800},
     "notes": "SSA/RRB voluntary withholding extends the 25b roster (alongside 1099-INT/DIV/R box 4)."},
    {"scenario_name": "RET-MED-1 — Medicare premiums 2,400 -> Schedule A line 1 (default schedule_a)",
     "scenario_type": "normal", "sort_order": 7,
     "inputs": {"ssa_medicare_premiums": 2400, "ssa_medicare_destination": "schedule_a",
                "scha_other_medical": 600, "agi": 40000},
     "expected_outputs": {"schedule_a_line1": 3000, "schedule_a_line3": 3000, "schedule_a_line4": 0},
     "notes": "Pub 502: Medicare Part B/D deductible. L1 = 600 + 2,400 = 3,000; floor 7.5% x 40,000 = 3,000; L4 = 0."},
]

RET_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-RET-CODE", "IRS_2025_1099R_INSTR", "primary", "Box 7 Guide to Distribution Codes (Table 1, verbatim)"),
    ("R-RET-CODE", "IRS_2025_1099R_FORM", "primary", "Box 7 codes + IRA/SEP/SIMPLE checkbox"),
    ("R-RET-4AB", "IRS_2025_1040_INSTR", "primary", "Lines 4a/4b: IRA distributions + Rollover/QCD literals"),
    ("R-RET-4AB", "IRS_2025_1099R_FORM", "primary", "Box 1 gross / box 2a taxable / IRA checkbox"),
    ("R-RET-5AB", "IRS_2025_1040_INSTR", "primary", "Lines 5a/5b: pensions and annuities + box-2a-blank Simplified Method"),
    ("R-RET-5AB", "IRS_2025_1099R_FORM", "primary", "Box 1/2a; non-IRA flow"),
    ("R-RET-25B", "IRS_2025_1099R_FORM", "primary", "Box 4 federal income tax withheld"),
    ("R-RET-EARLY", "IRS_2025_1099R_INSTR", "primary", "Early codes 1/J/S (Table 1)"),
    ("R-RET-EARLY", "IRS_2025_5329_INSTR", "primary", "Line 1 early distributions; rollover exclusion"),
    ("R-RET-SS-01", "IRS_2025_1040_INSTR", "primary", "SS Benefits Worksheet lines 1-7 (verbatim p.31)"),
    ("R-RET-SS-02", "IRS_2025_1040_INSTR", "primary", "SS Benefits Worksheet lines 8-18 (verbatim p.31)"),
    ("R-RET-SS-VAL", "IRS_2025_1040_INSTR", "secondary", "85% cap = worksheet line 17 (derived)"),
    ("R-RET-LSE-WS2", "IRS_2025_PUB915", "primary", "Pub 915 Worksheet 2 (additional taxable benefits, verbatim)"),
    ("R-RET-LSE-WS4", "IRS_2025_PUB915", "primary", "Pub 915 Worksheet 4 (taxable benefits under election, verbatim)"),
    ("R-RET-LSE-ELECT", "IRS_2025_PUB915", "primary", "Pub 915 'Lump-Sum Election' decision + 1040 line 6b/6c"),
    # ── AMENDMENT 2026-06-30 ──
    ("R-RET-25B-SS", "IRS_2025_1040_INSTR", "primary", "Line 25b: federal withholding from Forms SSA-1099/RRB-1099"),
    ("R-RET-MEDICARE", "IRS_2025_PUB502", "primary", "Medicare Part B/D premiums are deductible medical expenses"),
    ("R-RET-MEDICARE", "IRS_2025_F7206_INSTR", "primary", "Medicare premiums qualify as self-employed health insurance"),
]


# ═══════════════════════════════════════════════════════════════════════════
# 5329 — Additional Taxes on Qualified Plans, Part I (real IRS face)
# ═══════════════════════════════════════════════════════════════════════════

F5329_IDENTITY = {
    "form_number": "5329",
    "form_title": "Form 5329 — Additional Taxes on Qualified Plans (Including IRAs) and Other Tax-Favored Accounts (TY2025)",
    "notes": (
        "FULL FORM — Parts I-IX (Ken chose the full build 2026-06-25). Every part's "
        "additional tax flows to Schedule 2 (Form 1040) line 8 (the SUM L4+L8+L17+L25+"
        "L33+L41+L49+L51+L55 via R-5329-12). Part I (early distributions, 10%/25%) line 1 "
        "is fed cross-form by 1040_RETIREMENT R-RET-EARLY; the pure single-code-1 full-amount "
        "case still reports the 10% directly on Sch 2 line 8 with NO form (i5329 shortcut, "
        "R-5329-03). Parts III-VIII (excess contributions to Trad IRA / Roth IRA / Coverdell "
        "ESA / Archer MSA / HSA / ABLE) are each 6% of the SMALLER of the total excess or the "
        "12/31 account value, over a prior-year-carryforward chain. Part IX (excess accumulation "
        "/ missed RMD) is the SECURE 2.0 split: 10% for shortfalls corrected in the window (54a), "
        "25% otherwise (54b). v1 BOUNDARY: the FORM does the arithmetic; the preparer keys the "
        "leaf inputs (excess amounts, prior-year carryforwards, absorption lines, distributions, "
        "12/31 account values, RMD required/distributed). No contribution-limit / Roth-MAGI / "
        "HSA-family-limit modeling (Pub 590 worksheet territory). DUAL taxpayer+spouse is a "
        "tts-side instancing concern (a dedicated Form5329 model, owner enum) — this spec is "
        "owner-agnostic (one logical form). Source: f5329.pdf + i5329.pdf, verified 2026-06-25 "
        "(server/specs/_5329_full_source_brief.md)."
    ),
}

F5329_FACTS: list[dict] = [
    # ── Part I — Additional Tax on Early Distributions (10% / 25% SIMPLE) ──
    {"fact_key": "f5329_line1_early_in_income", "label": "5329 line 1: early distributions includible in income",
     "data_type": "decimal", "default_value": "0", "sort_order": 1,
     "notes": "Cross-form feeder from 1040_RETIREMENT R-RET-EARLY (codes 1/J/S taxable, net of rollover)."},
    {"fact_key": "f5329_line2_exception_amount", "label": "5329 line 2: amount not subject to the additional tax",
     "data_type": "decimal", "default_value": "0", "sort_order": 2,
     "notes": "= exception_amount_5329 (preparer, with the exception number 01-23/99). <= line 1. D_RET_006 polices the number."},
    {"fact_key": "f5329_simple_25pct", "label": "5329: distribution from a SIMPLE IRA in the first 2 years (25% rate)",
     "data_type": "boolean", "sort_order": 3,
     "notes": "Code S (or a SIMPLE-first-2-years code 1). Line 4 = 25% of line 3 instead of 10%. D_RET_007."},

    # ── Part II — Education/ABLE account distributions (10%) ──
    {"fact_key": "f5329_line5_edu_able_dist", "label": "5329 line 5: distributions in income from a Coverdell ESA, QTP, or ABLE account",
     "data_type": "decimal", "default_value": "0", "sort_order": 5,
     "notes": "Preparer. From Sch 1 line 8z (Coverdell/QTP) or line 8q (ABLE)."},
    {"fact_key": "f5329_line6_edu_able_not_subject", "label": "5329 line 6: line-5 distributions NOT subject to the additional tax",
     "data_type": "decimal", "default_value": "0", "sort_order": 6,
     "notes": "Preparer (scholarship, death/disability of the beneficiary, etc. — i5329 Part II). <= line 5."},

    # ── Part III — Excess Contributions to Traditional IRAs (6%) ──
    {"fact_key": "f5329_line9_tira_prior_excess", "label": "5329 line 9: prior-year excess traditional-IRA contributions (2024 Form 5329 line 16)",
     "data_type": "decimal", "default_value": "0", "sort_order": 9, "notes": "Preparer carryforward."},
    {"fact_key": "f5329_line10_tira_absorb", "label": "5329 line 10: traditional-IRA contribution room absorbing prior excess",
     "data_type": "decimal", "default_value": "0", "sort_order": 10,
     "notes": "Preparer. Unused current-year allowable contribution (i5329 worksheet); else -0-. We do NOT model the limit."},
    {"fact_key": "f5329_line11_tira_dist", "label": "5329 line 11: 2025 traditional-IRA distributions included in income",
     "data_type": "decimal", "default_value": "0", "sort_order": 11, "notes": "Preparer."},
    {"fact_key": "f5329_line12_tira_prior_excess_dist", "label": "5329 line 12: 2025 distributions of prior-year excess traditional-IRA contributions",
     "data_type": "decimal", "default_value": "0", "sort_order": 12, "notes": "Preparer."},
    {"fact_key": "f5329_line15_tira_curr_excess", "label": "5329 line 15: excess traditional-IRA contributions for 2025",
     "data_type": "decimal", "default_value": "0", "sort_order": 15, "notes": "Preparer."},
    {"fact_key": "f5329_tira_value", "label": "5329 line 17 cap: value of traditional IRAs on 12/31/2025 (smaller-of cap)",
     "data_type": "decimal", "sort_order": 17,
     "notes": "Preparer. NULLABLE — blank = no cap (tax on the full excess). D_5329_003 prompts entry when excess > 0."},

    # ── Part IV — Excess Contributions to Roth IRAs (6%) ──
    {"fact_key": "f5329_line18_roth_prior_excess", "label": "5329 line 18: prior-year excess Roth-IRA contributions (2024 Form 5329 line 24)",
     "data_type": "decimal", "default_value": "0", "sort_order": 18, "notes": "Preparer carryforward."},
    {"fact_key": "f5329_line19_roth_absorb", "label": "5329 line 19: Roth-IRA contribution room absorbing prior excess",
     "data_type": "decimal", "default_value": "0", "sort_order": 19, "notes": "Preparer; else -0-."},
    {"fact_key": "f5329_line20_roth_dist", "label": "5329 line 20: 2025 distributions from Roth IRAs",
     "data_type": "decimal", "default_value": "0", "sort_order": 20, "notes": "Preparer."},
    {"fact_key": "f5329_line23_roth_curr_excess", "label": "5329 line 23: excess Roth-IRA contributions for 2025",
     "data_type": "decimal", "default_value": "0", "sort_order": 23, "notes": "Preparer."},
    {"fact_key": "f5329_roth_value", "label": "5329 line 25 cap: value of Roth IRAs on 12/31/2025 (smaller-of cap)",
     "data_type": "decimal", "sort_order": 25, "notes": "Preparer. NULLABLE — blank = no cap. D_5329_003."},

    # ── Part V — Excess Contributions to Coverdell ESAs (6%) ──
    {"fact_key": "f5329_line26_coverdell_prior_excess", "label": "5329 line 26: prior-year excess Coverdell ESA contributions (2024 Form 5329 line 32)",
     "data_type": "decimal", "default_value": "0", "sort_order": 26, "notes": "Preparer carryforward."},
    {"fact_key": "f5329_line27_coverdell_absorb", "label": "5329 line 27: Coverdell contribution room absorbing prior excess",
     "data_type": "decimal", "default_value": "0", "sort_order": 27, "notes": "Preparer; else -0-."},
    {"fact_key": "f5329_line28_coverdell_dist", "label": "5329 line 28: 2025 distributions from Coverdell ESAs",
     "data_type": "decimal", "default_value": "0", "sort_order": 28, "notes": "Preparer."},
    {"fact_key": "f5329_line31_coverdell_curr_excess", "label": "5329 line 31: excess Coverdell ESA contributions for 2025",
     "data_type": "decimal", "default_value": "0", "sort_order": 31, "notes": "Preparer."},
    {"fact_key": "f5329_coverdell_value", "label": "5329 line 33 cap: value of Coverdell ESAs on 12/31/2025 (smaller-of cap)",
     "data_type": "decimal", "sort_order": 33, "notes": "Preparer. NULLABLE — blank = no cap. D_5329_003."},

    # ── Part VI — Excess Contributions to Archer MSAs (6%) ──
    {"fact_key": "f5329_line34_msa_prior_excess", "label": "5329 line 34: prior-year excess Archer MSA contributions (2024 Form 5329 line 40)",
     "data_type": "decimal", "default_value": "0", "sort_order": 34, "notes": "Preparer carryforward."},
    {"fact_key": "f5329_line35_msa_absorb", "label": "5329 line 35: Archer MSA contribution room absorbing prior excess",
     "data_type": "decimal", "default_value": "0", "sort_order": 35, "notes": "Preparer; else -0-."},
    {"fact_key": "f5329_line36_msa_dist", "label": "5329 line 36: 2025 distributions from Archer MSAs (Form 8853 line 8)",
     "data_type": "decimal", "default_value": "0", "sort_order": 36, "notes": "Preparer (no 8853 auto-pull in v1)."},
    {"fact_key": "f5329_line39_msa_curr_excess", "label": "5329 line 39: excess Archer MSA contributions for 2025",
     "data_type": "decimal", "default_value": "0", "sort_order": 39, "notes": "Preparer."},
    {"fact_key": "f5329_msa_value", "label": "5329 line 41 cap: value of Archer MSAs on 12/31/2025 (smaller-of cap)",
     "data_type": "decimal", "sort_order": 41, "notes": "Preparer. NULLABLE — blank = no cap. D_5329_003."},

    # ── Part VII — Excess Contributions to HSAs (6%) ──
    {"fact_key": "f5329_line42_hsa_prior_excess", "label": "5329 line 42: prior-year excess HSA contributions (2024 Form 5329 line 48)",
     "data_type": "decimal", "default_value": "0", "sort_order": 42, "notes": "Preparer carryforward."},
    {"fact_key": "f5329_line43_hsa_absorb", "label": "5329 line 43: HSA contribution room absorbing prior excess",
     "data_type": "decimal", "default_value": "0", "sort_order": 43, "notes": "Preparer; else -0-."},
    {"fact_key": "f5329_line44_hsa_dist", "label": "5329 line 44: 2025 distributions from HSAs (Form 8889 line 16)",
     "data_type": "decimal", "default_value": "0", "sort_order": 44, "notes": "Preparer (no 8889 auto-pull in v1)."},
    {"fact_key": "f5329_line47_hsa_curr_excess", "label": "5329 line 47: excess HSA contributions for 2025",
     "data_type": "decimal", "default_value": "0", "sort_order": 47, "notes": "Preparer."},
    {"fact_key": "f5329_hsa_value", "label": "5329 line 49 cap: value of HSAs on 12/31/2025 (smaller-of cap)",
     "data_type": "decimal", "sort_order": 49, "notes": "Preparer. NULLABLE — blank = no cap. D_5329_003."},

    # ── Part VIII — Excess Contributions to ABLE Account (6%) ──
    {"fact_key": "f5329_line50_able_curr_excess", "label": "5329 line 50: excess ABLE-account contributions for 2025",
     "data_type": "decimal", "default_value": "0", "sort_order": 50, "notes": "Preparer (no prior-year carryforward chain on the form)."},
    {"fact_key": "f5329_able_value", "label": "5329 line 51 cap: value of the ABLE account on 12/31/2025 (smaller-of cap)",
     "data_type": "decimal", "sort_order": 51, "notes": "Preparer. NULLABLE — blank = no cap. D_5329_003."},

    # ── Part IX — Excess Accumulation / missed RMD (SECURE 2.0: 10% window / 25% other) ──
    {"fact_key": "f5329_line52a_rmd_window", "label": "5329 line 52a: 2025 RMD from plans corrected in the window",
     "data_type": "decimal", "default_value": "0", "sort_order": 52,
     "notes": "Preparer. RMD for plans where the full shortfall was distributed during the correction window (54a -> 10%)."},
    {"fact_key": "f5329_line52b_rmd_other", "label": "5329 line 52b: 2025 RMD from all other plans",
     "data_type": "decimal", "default_value": "0", "sort_order": 53,
     "notes": "Preparer. RMD for all other plans (54b -> 25%)."},
    {"fact_key": "f5329_line53a_dist_window", "label": "5329 line 53a: 2025 amount distributed from the window plans",
     "data_type": "decimal", "default_value": "0", "sort_order": 54, "notes": "Preparer."},
    {"fact_key": "f5329_line53b_dist_other", "label": "5329 line 53b: 2025 amount distributed from the other plans",
     "data_type": "decimal", "default_value": "0", "sort_order": 55, "notes": "Preparer."},
]

F5329_RULES: list[dict] = [
    # ── Part I ──
    {"rule_id": "R-5329-01", "title": "Line 3 = line 1 - line 2 (amount subject to additional tax)",
     "rule_type": "calculation", "precedence": 1, "sort_order": 1,
     "formula": "L3 = max(0, f5329_line1_early_in_income - f5329_line2_exception_amount)",
     "inputs": ["f5329_line1_early_in_income", "f5329_line2_exception_amount"], "outputs": ["L3"],
     "description": "ONCE PER RETURN. Form 5329 Part I line 3 verbatim."},
    {"rule_id": "R-5329-02", "title": "Line 4 = 10% (or 25% SIMPLE) of line 3",
     "rule_type": "calculation", "precedence": 2, "sort_order": 2,
     "formula": "L4 = (0.25 if f5329_simple_25pct else 0.10) x L3.",
     "inputs": ["f5329_simple_25pct"], "outputs": ["L4"],
     "description": ("ONCE PER RETURN. Form 5329 Part I line 4 verbatim. Flows to Schedule 2 line 8 via "
                     "R-5329-12 (the all-parts aggregate). FULL-FORM CHANGE: R-5329-02 no longer writes "
                     "SCH_2.L8 directly — the aggregate rule does.")},
    {"rule_id": "R-5329-03", "title": "Form generation gate (direct-to-Schedule-2 shortcut)",
     "rule_type": "routing", "precedence": 0, "sort_order": 3,
     "formula": ("GENERATE Form 5329 when ANY part has input: a Part I exception amount (L2 > 0) OR any early "
                 "code is J/S OR more than one 1099-R contributes OR any of Parts II-IX produces tax. The pure "
                 "single-code-1 full-amount Part-I-only case reports L4 directly on Schedule 2 line 8 with NO "
                 "Form 5329 (i5329 shortcut)."),
     "inputs": ["f5329_line2_exception_amount", "f5329_simple_25pct"], "outputs": [],
     "description": "ONCE PER RETURN. JUDGMENT 3 (Ken-confirmed). i5329 'Who Must File' shortcut, widened to the full form."},

    # ── Part II — Education/ABLE distributions (10%) ──
    {"rule_id": "R-5329-04", "title": "Part II lines 7-8 (education/ABLE additional tax)",
     "rule_type": "calculation", "precedence": 4, "sort_order": 4,
     "formula": "L7 = max(0, L5 - L6); L8 = 0.10 x L7.",
     "inputs": ["f5329_line5_edu_able_dist", "f5329_line6_edu_able_not_subject"], "outputs": ["L7", "L8"],
     "description": "ONCE PER RETURN. Form 5329 Part II lines 7-8 verbatim (Coverdell/QTP/ABLE 10%)."},

    # ── Part III — Traditional IRA excess (6%) ──
    {"rule_id": "R-5329-05", "title": "Part III lines 13-17 (traditional-IRA excess-contribution tax)",
     "rule_type": "calculation", "precedence": 5, "sort_order": 5,
     "formula": ("L13 = L10 + L11 + L12; L14 = max(0, L9 - L13); L16 = L14 + L15; "
                 "L17 = 0.06 x min(L16, f5329_tira_value if not None else L16)."),
     "inputs": ["f5329_line9_tira_prior_excess", "f5329_line10_tira_absorb", "f5329_line11_tira_dist",
                "f5329_line12_tira_prior_excess_dist", "f5329_line15_tira_curr_excess", "f5329_tira_value"],
     "outputs": ["L13", "L14", "L16", "L17"],
     "description": "ONCE PER RETURN. Form 5329 Part III verbatim. 6% of the SMALLER of total excess or 12/31 value."},

    # ── Part IV — Roth IRA excess (6%) ──
    {"rule_id": "R-5329-06", "title": "Part IV lines 21-25 (Roth-IRA excess-contribution tax)",
     "rule_type": "calculation", "precedence": 6, "sort_order": 6,
     "formula": ("L21 = L19 + L20; L22 = max(0, L18 - L21); L24 = L22 + L23; "
                 "L25 = 0.06 x min(L24, f5329_roth_value if not None else L24)."),
     "inputs": ["f5329_line18_roth_prior_excess", "f5329_line19_roth_absorb", "f5329_line20_roth_dist",
                "f5329_line23_roth_curr_excess", "f5329_roth_value"],
     "outputs": ["L21", "L22", "L24", "L25"],
     "description": "ONCE PER RETURN. Form 5329 Part IV verbatim."},

    # ── Part V — Coverdell ESA excess (6%) ──
    {"rule_id": "R-5329-07", "title": "Part V lines 29-33 (Coverdell ESA excess-contribution tax)",
     "rule_type": "calculation", "precedence": 7, "sort_order": 7,
     "formula": ("L29 = L27 + L28; L30 = max(0, L26 - L29); L32 = L30 + L31; "
                 "L33 = 0.06 x min(L32, f5329_coverdell_value if not None else L32)."),
     "inputs": ["f5329_line26_coverdell_prior_excess", "f5329_line27_coverdell_absorb", "f5329_line28_coverdell_dist",
                "f5329_line31_coverdell_curr_excess", "f5329_coverdell_value"],
     "outputs": ["L29", "L30", "L32", "L33"],
     "description": "ONCE PER RETURN. Form 5329 Part V verbatim."},

    # ── Part VI — Archer MSA excess (6%) ──
    {"rule_id": "R-5329-08", "title": "Part VI lines 37-41 (Archer MSA excess-contribution tax)",
     "rule_type": "calculation", "precedence": 8, "sort_order": 8,
     "formula": ("L37 = L35 + L36; L38 = max(0, L34 - L37); L40 = L38 + L39; "
                 "L41 = 0.06 x min(L40, f5329_msa_value if not None else L40)."),
     "inputs": ["f5329_line34_msa_prior_excess", "f5329_line35_msa_absorb", "f5329_line36_msa_dist",
                "f5329_line39_msa_curr_excess", "f5329_msa_value"],
     "outputs": ["L37", "L38", "L40", "L41"],
     "description": "ONCE PER RETURN. Form 5329 Part VI verbatim."},

    # ── Part VII — HSA excess (6%) ──
    {"rule_id": "R-5329-09", "title": "Part VII lines 45-49 (HSA excess-contribution tax)",
     "rule_type": "calculation", "precedence": 9, "sort_order": 9,
     "formula": ("L45 = L43 + L44; L46 = max(0, L42 - L45); L48 = L46 + L47; "
                 "L49 = 0.06 x min(L48, f5329_hsa_value if not None else L48)."),
     "inputs": ["f5329_line42_hsa_prior_excess", "f5329_line43_hsa_absorb", "f5329_line44_hsa_dist",
                "f5329_line47_hsa_curr_excess", "f5329_hsa_value"],
     "outputs": ["L45", "L46", "L48", "L49"],
     "description": "ONCE PER RETURN. Form 5329 Part VII verbatim."},

    # ── Part VIII — ABLE excess (6%) ──
    {"rule_id": "R-5329-10", "title": "Part VIII line 51 (ABLE excess-contribution tax)",
     "rule_type": "calculation", "precedence": 10, "sort_order": 10,
     "formula": "L51 = 0.06 x min(L50, f5329_able_value if not None else L50).",
     "inputs": ["f5329_line50_able_curr_excess", "f5329_able_value"], "outputs": ["L51"],
     "description": "ONCE PER RETURN. Form 5329 Part VIII verbatim (no prior-year chain)."},

    # ── Part IX — Excess accumulation / missed RMD (SECURE 2.0 10%/25%) ──
    {"rule_id": "R-5329-11", "title": "Part IX lines 54a/54b/55 (excess accumulation additional tax)",
     "rule_type": "calculation", "precedence": 11, "sort_order": 11,
     "formula": ("L54a = 0.10 x max(0, L52a - L53a); L54b = 0.25 x max(0, L52b - L53b); L55 = L54a + L54b."),
     "inputs": ["f5329_line52a_rmd_window", "f5329_line53a_dist_window",
                "f5329_line52b_rmd_other", "f5329_line53b_dist_other"],
     "outputs": ["L54a", "L54b", "L55"],
     "description": ("ONCE PER RETURN. Form 5329 Part IX verbatim. SECURE 2.0 §302: 10% for shortfalls fully "
                     "corrected in the window (54a), 25% otherwise (54b). The window determination is preparer-asserted.")},

    # ── All-parts aggregate -> Schedule 2 line 8 ──
    {"rule_id": "R-5329-12", "title": "Schedule 2 line 8 = sum of all parts' additional taxes",
     "rule_type": "calculation", "precedence": 12, "sort_order": 12,
     "formula": "SCH_2.L8 = L4 + L8 + L17 + L25 + L33 + L41 + L49 + L51 + L55.",
     "inputs": [], "outputs": ["SCH_2.L8"],
     "description": ("ONCE PER RETURN. Each part's additional tax includes on Schedule 2 (Form 1040) line 8. "
                     "Computed feeder (Topic-2 direct-entry → computed; preparer override = the escape hatch). "
                     "DUAL: the tts side sums BOTH the taxpayer's and the spouse's Form 5329 totals into one Sch 2 L8.")},
]

_SCH2L8 = "Schedule 2 (Form 1040) line 8"

F5329_LINES: list[dict] = [
    # Part I — Early distributions
    {"line_number": "1", "description": "Early distributions includible in income", "line_type": "input",
     "source_rules": ["R-5329-01"], "sort_order": 1, "notes": "Cross-form feeder from 1040_RETIREMENT."},
    {"line_number": "2", "description": "Early distributions on line 1 not subject to the additional tax (exception number)",
     "line_type": "input", "source_rules": ["R-5329-01"], "sort_order": 2, "notes": "Preparer enters amount + exception number 01-23/99."},
    {"line_number": "3", "description": "Amount subject to additional tax (line 1 - line 2)", "line_type": "subtotal",
     "source_rules": ["R-5329-01"], "sort_order": 3},
    {"line_number": "4", "description": "Additional tax: 10% (or 25% SIMPLE) of line 3", "line_type": "total",
     "source_rules": ["R-5329-02"], "destination_form": _SCH2L8, "sort_order": 4},
    # Part II — Education/ABLE distributions (10%)
    {"line_number": "5", "description": "Distributions in income from a Coverdell ESA, a QTP, or an ABLE account", "line_type": "input",
     "source_rules": ["R-5329-04"], "sort_order": 5},
    {"line_number": "6", "description": "Distributions on line 5 not subject to the additional tax", "line_type": "input",
     "source_rules": ["R-5329-04"], "sort_order": 6},
    {"line_number": "7", "description": "Amount subject to additional tax (line 5 - line 6)", "line_type": "subtotal",
     "source_rules": ["R-5329-04"], "sort_order": 7},
    {"line_number": "8", "description": "Additional tax: 10% of line 7", "line_type": "total",
     "source_rules": ["R-5329-04"], "destination_form": _SCH2L8, "sort_order": 8},
    # Part III — Traditional IRA excess (6%)
    {"line_number": "9", "description": "Prior-year excess traditional-IRA contributions (2024 Form 5329 line 16)", "line_type": "input",
     "source_rules": ["R-5329-05"], "sort_order": 9},
    {"line_number": "10", "description": "Traditional-IRA contribution room absorbing prior excess (else -0-)", "line_type": "input",
     "source_rules": ["R-5329-05"], "sort_order": 10},
    {"line_number": "11", "description": "2025 traditional-IRA distributions included in income", "line_type": "input",
     "source_rules": ["R-5329-05"], "sort_order": 11},
    {"line_number": "12", "description": "2025 distributions of prior-year excess traditional-IRA contributions", "line_type": "input",
     "source_rules": ["R-5329-05"], "sort_order": 12},
    {"line_number": "13", "description": "Add lines 10, 11, and 12", "line_type": "subtotal",
     "source_rules": ["R-5329-05"], "sort_order": 13},
    {"line_number": "14", "description": "Prior-year excess remaining (line 9 - line 13, not below 0)", "line_type": "subtotal",
     "source_rules": ["R-5329-05"], "sort_order": 14},
    {"line_number": "15", "description": "Excess traditional-IRA contributions for 2025", "line_type": "input",
     "source_rules": ["R-5329-05"], "sort_order": 15},
    {"line_number": "16", "description": "Total excess contributions (line 14 + line 15)", "line_type": "subtotal",
     "source_rules": ["R-5329-05"], "sort_order": 16},
    {"line_number": "17", "description": "Additional tax: 6% of the smaller of line 16 or the 12/31 traditional-IRA value", "line_type": "total",
     "source_rules": ["R-5329-05"], "destination_form": _SCH2L8, "sort_order": 17},
    # Part IV — Roth IRA excess (6%)
    {"line_number": "18", "description": "Prior-year excess Roth-IRA contributions (2024 Form 5329 line 24)", "line_type": "input",
     "source_rules": ["R-5329-06"], "sort_order": 18},
    {"line_number": "19", "description": "Roth-IRA contribution room absorbing prior excess (else -0-)", "line_type": "input",
     "source_rules": ["R-5329-06"], "sort_order": 19},
    {"line_number": "20", "description": "2025 distributions from Roth IRAs", "line_type": "input",
     "source_rules": ["R-5329-06"], "sort_order": 20},
    {"line_number": "21", "description": "Add lines 19 and 20", "line_type": "subtotal",
     "source_rules": ["R-5329-06"], "sort_order": 21},
    {"line_number": "22", "description": "Prior-year excess remaining (line 18 - line 21, not below 0)", "line_type": "subtotal",
     "source_rules": ["R-5329-06"], "sort_order": 22},
    {"line_number": "23", "description": "Excess Roth-IRA contributions for 2025", "line_type": "input",
     "source_rules": ["R-5329-06"], "sort_order": 23},
    {"line_number": "24", "description": "Total excess contributions (line 22 + line 23)", "line_type": "subtotal",
     "source_rules": ["R-5329-06"], "sort_order": 24},
    {"line_number": "25", "description": "Additional tax: 6% of the smaller of line 24 or the 12/31 Roth-IRA value", "line_type": "total",
     "source_rules": ["R-5329-06"], "destination_form": _SCH2L8, "sort_order": 25},
    # Part V — Coverdell ESA excess (6%)
    {"line_number": "26", "description": "Prior-year excess Coverdell ESA contributions (2024 Form 5329 line 32)", "line_type": "input",
     "source_rules": ["R-5329-07"], "sort_order": 26},
    {"line_number": "27", "description": "Coverdell contribution room absorbing prior excess (else -0-)", "line_type": "input",
     "source_rules": ["R-5329-07"], "sort_order": 27},
    {"line_number": "28", "description": "2025 distributions from Coverdell ESAs", "line_type": "input",
     "source_rules": ["R-5329-07"], "sort_order": 28},
    {"line_number": "29", "description": "Add lines 27 and 28", "line_type": "subtotal",
     "source_rules": ["R-5329-07"], "sort_order": 29},
    {"line_number": "30", "description": "Prior-year excess remaining (line 26 - line 29, not below 0)", "line_type": "subtotal",
     "source_rules": ["R-5329-07"], "sort_order": 30},
    {"line_number": "31", "description": "Excess Coverdell ESA contributions for 2025", "line_type": "input",
     "source_rules": ["R-5329-07"], "sort_order": 31},
    {"line_number": "32", "description": "Total excess contributions (line 30 + line 31)", "line_type": "subtotal",
     "source_rules": ["R-5329-07"], "sort_order": 32},
    {"line_number": "33", "description": "Additional tax: 6% of the smaller of line 32 or the 12/31 Coverdell value", "line_type": "total",
     "source_rules": ["R-5329-07"], "destination_form": _SCH2L8, "sort_order": 33},
    # Part VI — Archer MSA excess (6%)
    {"line_number": "34", "description": "Prior-year excess Archer MSA contributions (2024 Form 5329 line 40)", "line_type": "input",
     "source_rules": ["R-5329-08"], "sort_order": 34},
    {"line_number": "35", "description": "Archer MSA contribution room absorbing prior excess (else -0-)", "line_type": "input",
     "source_rules": ["R-5329-08"], "sort_order": 35},
    {"line_number": "36", "description": "2025 distributions from Archer MSAs (Form 8853 line 8)", "line_type": "input",
     "source_rules": ["R-5329-08"], "sort_order": 36},
    {"line_number": "37", "description": "Add lines 35 and 36", "line_type": "subtotal",
     "source_rules": ["R-5329-08"], "sort_order": 37},
    {"line_number": "38", "description": "Prior-year excess remaining (line 34 - line 37, not below 0)", "line_type": "subtotal",
     "source_rules": ["R-5329-08"], "sort_order": 38},
    {"line_number": "39", "description": "Excess Archer MSA contributions for 2025", "line_type": "input",
     "source_rules": ["R-5329-08"], "sort_order": 39},
    {"line_number": "40", "description": "Total excess contributions (line 38 + line 39)", "line_type": "subtotal",
     "source_rules": ["R-5329-08"], "sort_order": 40},
    {"line_number": "41", "description": "Additional tax: 6% of the smaller of line 40 or the 12/31 Archer MSA value", "line_type": "total",
     "source_rules": ["R-5329-08"], "destination_form": _SCH2L8, "sort_order": 41},
    # Part VII — HSA excess (6%)
    {"line_number": "42", "description": "Prior-year excess HSA contributions (2024 Form 5329 line 48)", "line_type": "input",
     "source_rules": ["R-5329-09"], "sort_order": 42},
    {"line_number": "43", "description": "HSA contribution room absorbing prior excess (else -0-)", "line_type": "input",
     "source_rules": ["R-5329-09"], "sort_order": 43},
    {"line_number": "44", "description": "2025 distributions from HSAs (Form 8889 line 16)", "line_type": "input",
     "source_rules": ["R-5329-09"], "sort_order": 44},
    {"line_number": "45", "description": "Add lines 43 and 44", "line_type": "subtotal",
     "source_rules": ["R-5329-09"], "sort_order": 45},
    {"line_number": "46", "description": "Prior-year excess remaining (line 42 - line 45, not below 0)", "line_type": "subtotal",
     "source_rules": ["R-5329-09"], "sort_order": 46},
    {"line_number": "47", "description": "Excess HSA contributions for 2025", "line_type": "input",
     "source_rules": ["R-5329-09"], "sort_order": 47},
    {"line_number": "48", "description": "Total excess contributions (line 46 + line 47)", "line_type": "subtotal",
     "source_rules": ["R-5329-09"], "sort_order": 48},
    {"line_number": "49", "description": "Additional tax: 6% of the smaller of line 48 or the 12/31 HSA value", "line_type": "total",
     "source_rules": ["R-5329-09"], "destination_form": _SCH2L8, "sort_order": 49},
    # Part VIII — ABLE excess (6%)
    {"line_number": "50", "description": "Excess ABLE-account contributions for 2025", "line_type": "input",
     "source_rules": ["R-5329-10"], "sort_order": 50},
    {"line_number": "51", "description": "Additional tax: 6% of the smaller of line 50 or the 12/31 ABLE value", "line_type": "total",
     "source_rules": ["R-5329-10"], "destination_form": _SCH2L8, "sort_order": 51},
    # Part IX — Excess accumulation / missed RMD (SECURE 2.0 10%/25%)
    {"line_number": "52a", "description": "2025 RMD from plans corrected in the window", "line_type": "input",
     "source_rules": ["R-5329-11"], "sort_order": 52},
    {"line_number": "52b", "description": "2025 RMD from all other plans", "line_type": "input",
     "source_rules": ["R-5329-11"], "sort_order": 53},
    {"line_number": "53a", "description": "2025 amount distributed from the window plans", "line_type": "input",
     "source_rules": ["R-5329-11"], "sort_order": 54},
    {"line_number": "53b", "description": "2025 amount distributed from the other plans", "line_type": "input",
     "source_rules": ["R-5329-11"], "sort_order": 55},
    {"line_number": "54a", "description": "(line 52a - line 53a) x 10%, not below 0", "line_type": "subtotal",
     "source_rules": ["R-5329-11"], "sort_order": 56},
    {"line_number": "54b", "description": "(line 52b - line 53b) x 25%, not below 0", "line_type": "subtotal",
     "source_rules": ["R-5329-11"], "sort_order": 57},
    {"line_number": "55", "description": "Additional tax on excess accumulation (line 54a + line 54b)", "line_type": "total",
     "source_rules": ["R-5329-11"], "destination_form": _SCH2L8, "sort_order": 58},
]

F5329_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_5329_001", "title": "Exception amount exceeds early distributions", "severity": "error",
     "condition": "f5329_line2_exception_amount > f5329_line1_early_in_income",
     "message": ("Form 5329 line 2 (exception amount) exceeds line 1 (early distributions). The excluded amount "
                 "cannot exceed the early distribution included in income."),
     "notes": "Keying guard on the Part I subtraction."},
    {"diagnostic_id": "D_5329_002", "title": "Education/ABLE exclusion exceeds distributions", "severity": "error",
     "condition": "f5329_line6_edu_able_not_subject > f5329_line5_edu_able_dist",
     "message": ("Form 5329 line 6 (amount not subject to the additional tax) exceeds line 5 (Coverdell/QTP/ABLE "
                 "distributions in income). The excluded amount cannot exceed the distribution."),
     "notes": "Keying guard on the Part II subtraction."},
    {"diagnostic_id": "D_5329_003", "title": "Excess contribution present but 12/31 account value not entered", "severity": "warning",
     "condition": ("any excess-contribution part has total excess > 0 while its 12/31 account value "
                   "(f5329_*_value) is blank — the 6% smaller-of cap cannot be applied"),
     "message": ("An excess contribution is present but the 12/31 account value is blank, so the 6% additional tax "
                 "is computed on the FULL excess (no smaller-of cap). Enter the account value on 12/31/2025 to apply "
                 "the cap (Form 5329 Parts III-VIII)."),
     "notes": "Conservative (higher-tax) default when the cap value is missing; tts diagnostic fires per affected part."},
    {"diagnostic_id": "D_5329_004", "title": "Excess accumulation (missed RMD) — verify the correction-window split", "severity": "info",
     "condition": "Part IX has an RMD shortfall (line 52a>53a or 52b>53b)",
     "message": ("Form 5329 Part IX additional tax on excess accumulation applies. Verify the SECURE 2.0 split: 10% "
                 "(line 54a) only for shortfalls fully corrected during the correction window; 25% (line 54b) "
                 "otherwise. The window determination is preparer-asserted."),
     "notes": "No-silent-gap nudge on the Part IX rate split."},
]

F5329_SCENARIOS: list[dict] = [
    {"scenario_name": "F5329-T1 — line 1 20,000, no exception -> line 4 = 2,000",
     "scenario_type": "normal", "sort_order": 1,
     "inputs": {"f5329_line1_early_in_income": 20000, "f5329_line2_exception_amount": 0},
     "expected_outputs": {"3": 20000, "4": 2000, "schedule_2_line_8": 2000},
     "notes": "10% of 20,000."},
    {"scenario_name": "F5329-T2 — line 1 20,000, exception 8,000 -> line 4 = 1,200",
     "scenario_type": "normal", "sort_order": 2,
     "inputs": {"f5329_line1_early_in_income": 20000, "f5329_line2_exception_amount": 8000},
     "expected_outputs": {"3": 12000, "4": 1200, "schedule_2_line_8": 1200},
     "notes": "10% of 12,000."},
    {"scenario_name": "F5329-T3 — SIMPLE 25%: line 1 10,000 -> line 4 = 2,500",
     "scenario_type": "edge", "sort_order": 3,
     "inputs": {"f5329_line1_early_in_income": 10000, "f5329_simple_25pct": True},
     "expected_outputs": {"3": 10000, "4": 2500, "schedule_2_line_8": 2500},
     "notes": "25% of 10,000 (SIMPLE first-2-years)."},
    # Part II — education/ABLE (10%)
    {"scenario_name": "F5329-T4 — Part II: line 5 5,000, line 6 2,000 -> line 8 = 300",
     "scenario_type": "normal", "sort_order": 4,
     "inputs": {"f5329_line5_edu_able_dist": 5000, "f5329_line6_edu_able_not_subject": 2000},
     "expected_outputs": {"7": 3000, "8": 300, "schedule_2_line_8": 300},
     "notes": "10% of (5,000 - 2,000)."},
    # Part III — traditional IRA excess, value caps the base
    {"scenario_name": "F5329-T5 — Part III: 2,000 excess, 12/31 value 1,500 -> line 17 = 90 (capped)",
     "scenario_type": "edge", "sort_order": 5,
     "inputs": {"f5329_line15_tira_curr_excess": 2000, "f5329_tira_value": 1500},
     "expected_outputs": {"16": 2000, "17": 90, "schedule_2_line_8": 90},
     "notes": "6% of the SMALLER of 2,000 excess or 1,500 value = 6% x 1,500."},
    # Part III — value blank => no cap (conservative full-excess tax)
    {"scenario_name": "F5329-T6 — Part III: 2,000 excess, value blank -> line 17 = 120 (no cap)",
     "scenario_type": "edge", "sort_order": 6,
     "inputs": {"f5329_line15_tira_curr_excess": 2000},
     "expected_outputs": {"16": 2000, "17": 120, "schedule_2_line_8": 120},
     "notes": "Blank 12/31 value => 6% of the full 2,000 excess. D_5329_003 warns."},
    # Part IV — Roth carryforward chain absorbed partially
    {"scenario_name": "F5329-T7 — Part IV: prior 3,000, absorb 1,000 + dist 500 -> line 24 1,500, line 25 = 90",
     "scenario_type": "normal", "sort_order": 7,
     "inputs": {"f5329_line18_roth_prior_excess": 3000, "f5329_line19_roth_absorb": 1000,
                "f5329_line20_roth_dist": 500, "f5329_roth_value": 50000},
     "expected_outputs": {"21": 1500, "22": 1500, "24": 1500, "25": 90, "schedule_2_line_8": 90},
     "notes": "L22 = max(0, 3,000 - 1,500) = 1,500; value 50,000 doesn't cap; 6% x 1,500 = 90."},
    # Part IX — 25% (not corrected in window)
    {"scenario_name": "F5329-T8 — Part IX: RMD 4,000 other, distributed 1,000 -> line 55 = 750 (25%)",
     "scenario_type": "normal", "sort_order": 8,
     "inputs": {"f5329_line52b_rmd_other": 4000, "f5329_line53b_dist_other": 1000},
     "expected_outputs": {"54b": 750, "55": 750, "schedule_2_line_8": 750},
     "notes": "25% of (4,000 - 1,000) = 750. SECURE 2.0 standard rate."},
    # Part IX — 10% (corrected in window) + a fully-corrected window bucket
    {"scenario_name": "F5329-T9 — Part IX: window RMD 4,000 dist 1,000 (10%) + other fully corrected -> 300",
     "scenario_type": "edge", "sort_order": 9,
     "inputs": {"f5329_line52a_rmd_window": 4000, "f5329_line53a_dist_window": 1000,
                "f5329_line52b_rmd_other": 2000, "f5329_line53b_dist_other": 2000},
     "expected_outputs": {"54a": 300, "54b": 0, "55": 300, "schedule_2_line_8": 300},
     "notes": "10% of (4,000-1,000)=300 window; other bucket fully corrected -> 0."},
    # All-parts aggregate -> Schedule 2 line 8 is the SUM
    {"scenario_name": "F5329-T10 — all parts: PI 2,000 + PII 300 + PIII 120 + PIX 750 -> Sch 2 L8 = 3,170",
     "scenario_type": "edge", "sort_order": 10,
     "inputs": {"f5329_line1_early_in_income": 20000,
                "f5329_line5_edu_able_dist": 5000, "f5329_line6_edu_able_not_subject": 2000,
                "f5329_line15_tira_curr_excess": 2000,
                "f5329_line52b_rmd_other": 4000, "f5329_line53b_dist_other": 1000},
     "expected_outputs": {"4": 2000, "8": 300, "17": 120, "55": 750, "schedule_2_line_8": 3170},
     "notes": "Sch 2 L8 = L4 2,000 + L8 300 + L17 120 + L55 750 = 3,170 (R-5329-12 aggregate)."},
]

F5329_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-5329-01", "IRS_2025_5329_FORM", "primary", "Part I line 3 verbatim (line 1 - line 2)"),
    ("R-5329-02", "IRS_2025_5329_FORM", "primary", "Part I line 4: 10% (25% SIMPLE)"),
    ("R-5329-02", "IRS_2025_5329_INSTR", "secondary", "SIMPLE 25% caution"),
    ("R-5329-03", "IRS_2025_5329_INSTR", "primary", "'Who Must File' direct-to-Schedule-2 shortcut"),
    ("R-5329-04", "IRS_2025_5329_FORM", "primary", "Part II lines 5-8 verbatim (education/ABLE 10%)"),
    ("R-5329-05", "IRS_2025_5329_FORM", "primary", "Part III lines 9-17 verbatim (traditional-IRA excess 6%)"),
    ("R-5329-06", "IRS_2025_5329_FORM", "primary", "Part IV lines 18-25 verbatim (Roth-IRA excess 6%)"),
    ("R-5329-07", "IRS_2025_5329_FORM", "primary", "Part V lines 26-33 verbatim (Coverdell ESA excess 6%)"),
    ("R-5329-08", "IRS_2025_5329_FORM", "primary", "Part VI lines 34-41 verbatim (Archer MSA excess 6%)"),
    ("R-5329-09", "IRS_2025_5329_FORM", "primary", "Part VII lines 42-49 verbatim (HSA excess 6%)"),
    ("R-5329-10", "IRS_2025_5329_FORM", "primary", "Part VIII lines 50-51 verbatim (ABLE excess 6%)"),
    ("R-5329-11", "IRS_2025_5329_FORM", "primary", "Part IX lines 52-55 verbatim (excess accumulation 10%/25%)"),
    ("R-5329-11", "IRS_2025_5329_INSTR", "secondary", "SECURE 2.0 §302 correction-window split (Notice 2023-...)"),
    ("R-5329-12", "IRS_2025_5329_FORM", "primary", "Each part's additional tax includes on Schedule 2 line 8"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS (7)
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-RET-01", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "4a/4b roster: IRA docs -> gross 4a, taxable 4b (net of rollover/QCD)",
     "description": ("Validates R-RET-4AB. Bugs it catches: pension docs leaking into 4a/4b; QCD/rollover not "
                     "subtracted from 4b; the IRA checkbox ignored."),
     "definition": {"kind": "sum_check", "form": "1040_RETIREMENT", "output": "agg_4b",
                    "sum_of": ["r_box2a_taxable", "-r_rollover_amount", "-r_qcd_amount"],
                    "filter": "r_box7_ira_sep_simple == True",
                    "allow_negative_addends": True,
                    "must_write_to": {"form": "1040", "line": "4b"}},
     "sort_order": 1},
    {"assertion_id": "FA-1040-RET-02", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "5a/5b roster: pension docs -> gross 5a, taxable 5b (net of rollover)",
     "description": ("Validates R-RET-5AB. Bug it catches: IRA docs counted as pensions; rollover not subtracted."),
     "definition": {"kind": "sum_check", "form": "1040_RETIREMENT", "output": "agg_5b",
                    "sum_of": ["r_box2a_taxable", "-r_rollover_amount"],
                    "filter": "r_box7_ira_sep_simple == False",
                    "allow_negative_addends": True,
                    "must_write_to": {"form": "1040", "line": "5b"}},
     "sort_order": 2},
    {"assertion_id": "FA-1040-RET-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "1099-R box 4 withholding extends the 1040 line 25b roster",
     "description": ("Validates R-RET-25B. Bug it catches: the 1099-R box-4 addend dropped when the retirement "
                     "model lands (the same class as the Topic-3 DIV box-4 extension)."),
     "definition": {"kind": "sum_check", "form": "1040_RETIREMENT", "output": "L25b_retirement_addend",
                    "sum_of": ["r_box4_fed_withheld"],
                    "must_write_to": {"form": "1040", "line": "25b"}},
     "sort_order": 3},
    {"assertion_id": "FA-1040-RET-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Form 5329 Part I: line 4 = rate x (line 1 - line 2) -> Schedule 2 line 8",
     "description": ("Validates R-5329-01/02. Bugs it catches: 25% applied when not SIMPLE (or 10% when SIMPLE); "
                     "the exception amount not subtracted; line 4 not landing on Schedule 2 line 8."),
     "definition": {"kind": "formula_check", "form": "5329",
                    "formula": "L4 == (0.25 if f5329_simple_25pct else 0.10) * max(0, L1 - L2)",
                    "must_write_to": {"form": "SCH_2", "line": "8"}},
     "sort_order": 4},
    {"assertion_id": "FA-1040-RET-05", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Social Security worksheet: 6b = min(WS16, WS17) and 6b <= 0.85 x 6a",
     "description": ("Validates R-RET-SS-02 + R-RET-SS-VAL. The 85% cap (WS17) must bound taxable SS; bug it "
                     "catches: a tier formula error pushing 6b above 85% of benefits."),
     "definition": {"kind": "formula_check", "form": "1040_RETIREMENT",
                    "formula": "ws_18 == min(ws_16, ws_17) and ws_18 <= 0.85 * ws_1",
                    "must_write_to": {"form": "1040", "line": "6b"}},
     "sort_order": 5},
    {"assertion_id": "FA-1040-RET-06", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "SS worksheet base/second-tier constants (statutory §86, both years)",
     "description": ("Pins the worksheet thresholds: base $25,000 (single/HOH/QSS/MFS-apart) / $32,000 (MFJ); "
                     "second tier $9,000 / $12,000. NON-INDEXED — identical for 2025 and 2026 (bug it catches: "
                     "someone 'inflation-adjusting' a statutory §86 amount)."),
     "definition": {"kind": "constants_check", "form": "1040_RETIREMENT",
                    "constants": {
                        "base_amount": {"single": 25000, "hoh": 25000, "qss": 25000, "mfs_apart": 25000, "mfj": 32000},
                        "second_tier": {"single": 9000, "hoh": 9000, "qss": 9000, "mfs_apart": 9000, "mfj": 12000},
                        "rates": {"tier1": 0.50, "tier2": 0.85},
                        "applies_to_years": [2025, 2026]}},
     "sort_order": 6},
    {"assertion_id": "FA-1040-RET-07", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Unsupported-path gates blank the affected line (Simplified Method, NUA, codes, lump-sum)",
     "description": ("Validates the RED gates: box-2a-blank+basis (D_RET_001), NUA (D_RET_002), unsupported code "
                     "(D_RET_003), SS lump-sum (D_RET_004), IRA-ded<->SS circular (D_RET_005), 5329 exception "
                     "(D_RET_006) each leave their result uncomputed with a RED — never a silently-wrong number."),
     "definition": {"kind": "gating_check", "form": "1040_RETIREMENT",
                    "blockers": ["box2a_blank_with_basis", "nua_present", "unsupported_code",
                                 "ss_lump_sum", "ira_deduction_with_taxable_ss", "unsupported_5329_exception"],
                    "expect": {"result_blank": True, "red_fires": True}},
     "sort_order": 7},
    {"assertion_id": "FA-1040-RET-08", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Lump-sum election: 6b = Worksheet 4 line 21 when elected (else regular ws_18)",
     "description": ("Validates R-RET-LSE-WS2/WS4/ELECT. Bugs it catches: WS4 line 1 not reduced by the pre-2025 "
                     "lump sum; the Σ Worksheet-2 additionals not added; the election applied without the explicit "
                     "ss_lump_sum_election toggle; or 6b not superseding the regular worksheet result when elected."),
     "definition": {"kind": "formula_check", "form": "1040_RETIREMENT",
                    "formula": ("lse_ws4_21 == lse_ws4_19 + sum(lse_ws2_21) and "
                                "(line_6b == lse_ws4_21 if ss_lump_sum_election else line_6b == ws_18)"),
                    "must_write_to": {"form": "1040", "line": "6b"}},
     "sort_order": 8},
    {"assertion_id": "FA-1040-RET-09", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "SSA-1099/RRB-1099 federal withholding extends the 1040 line 25b roster",
     "description": ("Validates R-RET-25B-SS. Bug it catches: SSA/RRB box-6/box-10 withholding dropped from line "
                     "25b (the same class as the 1099-R box-4 extension)."),
     "definition": {"kind": "sum_check", "form": "1040_RETIREMENT", "output": "L25b_ssa_addend",
                    "sum_of": ["ssa_fed_withheld"],
                    "must_write_to": {"form": "1040", "line": "25b"}},
     "sort_order": 9},
    {"assertion_id": "FA-1040-RET-10", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Medicare premiums land on Schedule A line 1 (default destination)",
     "description": ("Validates R-RET-MEDICARE (schedule_a path). Bug it catches: Medicare premiums not added to "
                     "the Sch A medical total before the 7.5% floor, or routed nowhere."),
     "definition": {"kind": "formula_check", "form": "1040_RETIREMENT",
                    "formula": ("schedule_a_line1 includes ssa_medicare_premiums "
                                "when ssa_medicare_destination == 'schedule_a'"),
                    "must_write_to": {"form": "SCHEDULE_A", "line": "1"}},
     "sort_order": 10},
]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY FORM LINKS  (source_code, form_code, link_type)
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_1099R_FORM", "1040_RETIREMENT", "governs"),
    ("IRS_2025_1099R_INSTR", "1040_RETIREMENT", "governs"),
    ("IRS_2025_1040_INSTR", "1040_RETIREMENT", "governs"),
    ("IRS_2025_1040_FORM", "1040_RETIREMENT", "informs"),
    ("IRS_2025_PUB915", "1040_RETIREMENT", "governs"),
    ("IRS_2025_PUB502", "1040_RETIREMENT", "governs"),
    ("IRS_2025_F7206_INSTR", "1040_RETIREMENT", "governs"),
    ("IRS_2025_5329_FORM", "5329", "governs"),
    ("IRS_2025_5329_INSTR", "5329", "governs"),
    ("IRS_2025_1099R_INSTR", "5329", "informs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORMS ROSTER
# ═══════════════════════════════════════════════════════════════════════════

FORMS: list[dict] = [
    {"identity": RET_IDENTITY, "facts": RET_FACTS, "rules": RET_RULES, "lines": RET_LINES,
     "diagnostics": RET_DIAGNOSTICS, "scenarios": RET_SCENARIOS, "rule_links": RET_RULE_LINKS},
    {"identity": F5329_IDENTITY, "facts": F5329_FACTS, "rules": F5329_RULES, "lines": F5329_LINES,
     "diagnostics": F5329_DIAGNOSTICS, "scenarios": F5329_SCENARIOS, "rule_links": F5329_RULE_LINKS},
]


# ═══════════════════════════════════════════════════════════════════════════
# Command
# ═══════════════════════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = (
        "Load the Retirement Income specs into Rule Studio (creates "
        "1040_RETIREMENT, 5329). Refuses to seed until Ken sets READY_TO_SEED=True."
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()

        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad 1040_RETIREMENT / 5329 specs (Topic 5)\n"))

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

        if not READY_TO_SEED or empty:
            still_empty = "\n  ".join(f"- {n}" for n in empty) or "(all populated)"
            raise CommandError(
                "\n"
                "REFUSING TO SEED 1040_RETIREMENT/5329: not cleared to seed.\n"
                "\n"
                "Content is authored, but seeding is gated until Ken reviews the packet\n"
                "(the source citations, the v1 distribution-code set, the 5329 exception\n"
                "subset 01-12+19, the SS Benefits Worksheet transcription, and the TY2026\n"
                "statutory-constant confirmation) and flips the sentinel.\n"
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
    # Topics / sources (mirror load_1040_intdiv_qdcgt.py exactly)
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
        # Scenario renames orphan the old row (update_or_create keys on
        # scenario_name and cannot delete) — e.g. the RET-G5 "unsupported
        # exception 13" -> "invalid exception 25" rename (REVIEW_QUEUE s54:
        # the 5329 full unit made 13 a VALID §457 exception, so the old
        # scenario asserted a false diagnostic). Delete anything not in the
        # current authored list so a reseed self-heals the DB.
        current_names = {t["scenario_name"] for t in scenarios}
        stale = TestScenario.objects.filter(tax_form=form).exclude(
            scenario_name__in=current_names,
        )
        if stale.exists():
            self.stdout.write(
                f"  deleting {stale.count()} stale scenario rows: "
                + "; ".join(stale.values_list("scenario_name", flat=True))
            )
            stale.delete()
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
        self.stdout.write("DATABASE TOTALS (after load_1040_retirement)")
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

        for fn in ("1040_RETIREMENT", "5329"):
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
