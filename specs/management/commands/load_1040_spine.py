"""Load the Form 1040 SPINE spec (form_number "1040"), TY 2025 — Sprint Topic 1.

Session 2026-06-10 PM: authored by transcription from primary sources fetched
and layout-extracted the same day (naive text layers interleave table columns —
all tables were reconstructed positionally with pymupdf):

  - 2025 Form 1040 PDF (f1040.pdf, created 9/5/25) — the on-disk audited copy at
    tts-tax-app resources/irs_forms/2025/f1040.pdf. Both pages transcribed line
    by line; the FORM_LINES list below mirrors the actual 2025 OBBBA-redesigned
    form face (11a/11b, 12a-12e, 13a/13b, 7a, 27a-27c, new line 30).
  - Publication 1040 (2025), Tax and Earned Income Credit Tables (i1040tt.pdf).
    Tax Table row structure, sample rows, the $100,000 cutover, the QSS-uses-MFJ
    footnote, and the Tax Computation Worksheet sections A-D were transcribed.
    The MIDPOINT + ROUND-HALF-UP convention was verified against published rows
    at multiple half-dollar pins (302.50->303, 357.50->358) and the final row
    (99,950-100,000) for all four columns to the dollar.
  - 2025 Instructions for Form 1040 (i1040gi.pdf): Line 16 method routing
    ("must use the Tax Table" under $100,000), QDCGT / Schedule D Tax Worksheet
    / Form 8615 trigger conditions, standard-deduction exceptions 1-3, the
    line 37 "include line 38 penalty" rule, line 36 irrevocability.
  - Publication 501 (2025): Tables 6/7/8 — base standard deduction, aged/blind
    additional ($2,000 unmarried; $1,600 MFJ/MFS/QSS), dependent worksheet
    ($1,350 minimum / earned + $450), all transcribed verbatim.
  - Rev. Proc. 2024-40 §2.01 (TY2025 rate schedules — verified in tts-tax-app
    2026-06-10) and Rev. Proc. 2025-32 §4.01/§4.14 (TY2026 rate schedules,
    standard deduction, aged/blind, dependent cap — verified 2026-06-10).
  - OBBBA P.L. 119-21 §70102 (TY2025 standard deduction $15,750/$31,500/$23,625
    — also printed in the 2025 Form 1040 page-2 margin, double-confirmed).

This loader UPDATES the existing TaxForm ("1040", FED, 2025, v1) — the Session
14 stub (1 fact, 2 rules, 3 lines) — into the full spine spec. The superseded
stub artifacts (rules R001/R002, fact line_11_agi, line "11") are retired by
the loader with explicit stdout notes; their semantics are re-specified here
(R-CR-03, R-PAY-07, lines 11a/11b).

TARGET-YEAR POLICY (sprint): TY2026 is the product target, TY2025 the
verification bed. Year-keyed constants for BOTH years are specified in the
rules below, each with its own citation. The TY2026 Tax Table itself is not
yet published — TY2026 line-16 values are defined by the table CONVENTION
applied to the Rev. Proc. 2025-32 §4.01 schedules and MUST be re-verified
against the published 2026 Tax Table when the IRS releases it (tracker note).

Safety guard
------------
`READY_TO_SEED = False`. Content is authored; Ken reviews the packet (consts,
conventions, diagnostics severities, scenarios, the stub retirement), flips
the sentinel, and seeds. Until then the command refuses to write to the DB.

Authoring notes
---------------
- TEST_SCENARIOS expected values were computed independently from the
  transcribed published tables/worksheets (several are direct transcriptions
  of published Tax Table rows); they exist to VALIDATE the rules.
- The midpoint convention is an INFERENCE from published row values (the IRS
  does not print the word "midpoint" in the booklet) — its excerpt carries
  requires_human_review=True with the verification evidence for Ken to bless.
- Statute / P.L. / Rev. Proc. excerpts carry requires_human_review=True
  pending verbatim confirmation against the cited source text.

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
# SAFETY GUARD — flipped to True 2026-06-10 on Ken's in-session approval of
# the review packet (constants per year, the Tax Table midpoint/half-up
# convention, diagnostics severities, stub retirement, the 33 scenarios).
# ═══════════════════════════════════════════════════════════════════════════

READY_TO_SEED = True


# ═══════════════════════════════════════════════════════════════════════════
# FORM IDENTITY — updates the Session-14 stub in place
# ═══════════════════════════════════════════════════════════════════════════

FORM_NUMBER = "1040"
FORM_TITLE = "Form 1040 — U.S. Individual Income Tax Return (TY2025 spine)"
FORM_JURISDICTION = "FED"
FORM_ENTITY_TYPES = ["1040"]
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_NOTES = (
    "Form 1040 SPINE spec (Sprint Topic 1): filing status (all five) with MFS/HOH "
    "diagnostics; preparer-asserted dependent entry with diagnostics (NO eligibility "
    "adjudication engine this sprint); all income lines direct-entry capable (computed "
    "where feeders exist: 1a, 2a/2b, 25a); standard deduction incl. aged (born before "
    "Jan 2 of tax_year-64) / blind additional amounts and the dependent worksheet; "
    "tax via the Tax Table MIDPOINT convention under $100,000 and the Tax Computation "
    "Worksheet (= rate schedules) at/above; credits/other-taxes/payments chains; "
    "estimated payments (four quarters + prior-year applied); refund/owe incl. the "
    "line 38 penalty inclusion rule. Constants year-keyed for TY2025 AND TY2026 "
    "(_constants_for_year pattern) — every constant cited per year. BRIDGE: until "
    "Sprint Topic 3 lands, any line 3a amount or line 7a capital gain distribution "
    "fires a RED diagnostic and the spine must NOT compute table-only tax on that "
    "return (D_1040_001). Unsupported paths are enumerated as RED diagnostics — the "
    "spine never computes a wrong number silently. Supersedes the Session-14 stub "
    "(R001/R002/line_11_agi retired by this loader; semantics re-specified as "
    "R-CR-03 / R-PAY-07 / lines 11a-11b)."
)

# Existing sources to REUSE (looked up, not modified). New excerpts attach via
# NEW_EXCERPTS_ON_EXISTING below.
EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_1040_INSTR",  # Session 14 source — line 16 routing excerpts added below
    "IRC_63",               # standard deduction (c)(2)/(c)(5)/(c)(6)/(f)
    "IRC_151",              # exemptions/dependents (cross-ref)
    "IRC_152",              # dependent definition (cross-ref)
    "IRS_2025_8812_FORM",   # Sch 8812 lines 14/27 feed 1040 lines 19/28
]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY TOPICS
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("form_1040_spine", "Form 1040 Spine (status, income, deductions, tax, payments)"),
    ("filing_status", "Filing Status & Marital Determination (§§1, 2, 7703)"),
    ("standard_deduction", "Standard Deduction (§63)"),
    ("tax_computation", "Tax Tables & Tax Computation (§§1, 3)"),
    ("dependents_entry", "Dependent Entry & Diagnostics (§§151, 152)"),
    ("estimated_payments", "Estimated Tax Payments (§6654)"),
]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY SOURCES (with embedded excerpts) — CREATE
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_SOURCES: list[dict] = [
    # ─── 2025 Form 1040 (the form face) ───
    {
        "source_code": "IRS_2025_1040_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Form 1040 — U.S. Individual Income Tax Return",
        "citation": "Form 1040 (2025); f1040.pdf (created 9/5/25)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f1040.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": (
            "Canonical line numbering for the 2025 OBBBA-redesigned form. Transcribed "
            "line by line from the audited on-disk copy (tts-tax-app "
            "resources/irs_forms/2025/f1040.pdf, manifest SHA-verified)."
        ),
        "topics": ["form_1040_spine"],
        "excerpts": [
            {
                "excerpt_label": "Filing status block + special checkboxes",
                "location_reference": "Form 1040 (2025), page 1",
                "excerpt_text": (
                    "Filing Status (check only one box): Single; Married filing jointly (even if "
                    "only one had income); Married filing separately (MFS) — enter spouse's SSN "
                    "above and full name here; Head of household (HOH); Qualifying surviving "
                    "spouse (QSS). If you checked the HOH or QSS box, enter the child's name if "
                    "the qualifying person is a child but not your dependent. NRA-spouse "
                    "election checkbox (treat nonresident/dual-status spouse as U.S. resident). "
                    "Separate checkbox below the dependents block: 'Check if your filing status "
                    "is MFS or HOH and you lived apart from your spouse for the last 6 months of "
                    "2025, or you are legally separated... and you did not live in the same "
                    "household as your spouse at the end of 2025.' Also new for 2025: 'Check "
                    "here if your main home, and your spouse's if filing a joint return, was in "
                    "the U.S. for more than half of 2025.' Digital-assets yes/no question."
                ),
                "summary_text": "Five filing statuses + 2025 checkbox set (lived-apart, U.S.-home, NRA election, digital assets).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Dependents block (columns 1-7)",
                "location_reference": "Form 1040 (2025), page 1, Dependents",
                "excerpt_text": (
                    "Per dependent: (1) First name, (2) Last name, (3) SSN, (4) Relationship, "
                    "(5) Check if lived with you more than half of 2025 — (a) Yes (b) And in "
                    "the U.S., (6) Check if Full-time student / Permanently and totally "
                    "disabled, (7) Credits: Child tax credit / Credit for other dependents. "
                    "If more than four dependents, see instructions and check here."
                ),
                "summary_text": "2025 dependent grid adds residency (5b 'And in the U.S.') and student/disabled (6) columns.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Income lines 1a-9",
                "location_reference": "Form 1040 (2025), page 1, Income",
                "excerpt_text": (
                    "1a W-2 box 1 total; 1b household employee wages; 1c tip income not "
                    "reported on 1a; 1d Medicaid waiver payments not on W-2; 1e taxable "
                    "dependent care benefits (Form 2441 line 26); 1f employer-provided "
                    "adoption benefits (Form 8839 line 31); 1g wages from Form 8919 line 6; "
                    "1h other earned income; 1i nontaxable combat pay election (memo); "
                    "1z = add 1a through 1h. 2a tax-exempt / 2b taxable interest; 3a qualified "
                    "/ 3b ordinary dividends (3c child's-dividends checkboxes); 4a IRA "
                    "distributions / 4b taxable (4c Rollover/QCD checkboxes); 5a pensions and "
                    "annuities / 5b taxable (5c Rollover/PSO checkboxes); 6a social security "
                    "benefits / 6b taxable (6c lump-sum election checkbox; 6d MFS-lived-apart-"
                    "all-year checkbox); 7a capital gain or (loss), attach Schedule D if "
                    "required (7b: Schedule D not required / includes child's gain checkboxes); "
                    "8 additional income from Schedule 1 line 10; "
                    "9 = add 1z, 2b, 3b, 4b, 5b, 6b, 7a, and 8 (total income)."
                ),
                "summary_text": "Line 9 sums 1z+2b+3b+4b+5b+6b+7a+8. Line 7 is '7a' on the 2025 form.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Lines 10-15 (AGI through taxable income)",
                "location_reference": "Form 1040 (2025), pages 1-2",
                "excerpt_text": (
                    "10 adjustments from Schedule 1 line 26; 11a = 9 - 10 (adjusted gross "
                    "income, page 1); 11b = amount from 11a (page 2 carry). 12a checkboxes: "
                    "someone can claim You / Your spouse as a dependent; 12b spouse itemizes "
                    "on a separate return; 12c you were a dual-status alien; 12d You: born "
                    "before January 2, 1961 / blind; Spouse: born before January 2, 1961 / "
                    "blind. 12e standard deduction or itemized deductions (from Schedule A). "
                    "Page-2 margin prints the 2025 standard deduction: Single or MFS $15,750; "
                    "MFJ or QSS $31,500; HOH $23,625; 'If you checked a box on line 12a, 12b, "
                    "12c, or 12d, see instructions.' 13a QBI deduction (8995/8995-A); 13b "
                    "additional deductions from Schedule 1-A line 38; 14 = 12e + 13a + 13b; "
                    "15 = 11b - 14, if zero or less enter -0- (taxable income)."
                ),
                "summary_text": "12a-12e checkbox block; margin confirms OBBBA TY2025 std deduction; 15 = max(0, 11b - 14).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Lines 16-24 (tax and credits)",
                "location_reference": "Form 1040 (2025), page 2",
                "excerpt_text": (
                    "16 Tax (see instructions) — checkboxes: 1 Form 8814, 2 Form 4972, 3 "
                    "(other, with literal); 17 amount from Schedule 2 line 3; 18 = 16 + 17; "
                    "19 child tax credit or credit for other dependents from Schedule 8812; "
                    "20 amount from Schedule 3 line 8; 21 = 19 + 20; 22 = 18 - 21, if zero or "
                    "less enter -0-; 23 other taxes from Schedule 2 line 21; 24 = 22 + 23 "
                    "(total tax)."
                ),
                "summary_text": "Tax-and-credits chain 16..24 with the line 16 add-on checkboxes.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Lines 25-33 (payments)",
                "location_reference": "Form 1040 (2025), page 2",
                "excerpt_text": (
                    "25 federal income tax withheld from: a Form(s) W-2, b Form(s) 1099, "
                    "c other forms; 25d = 25a + 25b + 25c. 26 = 2025 estimated tax payments "
                    "and amount applied from 2024 return (enter former spouse's SSN if "
                    "estimates were made jointly with a former spouse). 27a earned income "
                    "credit (EIC); 27b clergy filing Schedule SE checkbox; 27c check to NOT "
                    "claim EIC. 28 additional child tax credit from Schedule 8812 (opt-out "
                    "checkbox). 29 American opportunity credit (Form 8863 line 8). 30 "
                    "refundable adoption credit (Form 8839 line 13) — NEW for 2025. 31 amount "
                    "from Schedule 3 line 15. 32 = 27a + 28 + 29 + 30 + 31 (total other "
                    "payments and refundable credits). 33 = 25d + 26 + 32 (total payments)."
                ),
                "summary_text": "25d sums three withholding sources; 32 includes the new line 30 refundable adoption credit.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Lines 34-38 (refund / amount owed)",
                "location_reference": "Form 1040 (2025), page 2",
                "excerpt_text": (
                    "34 = 33 - 24 if 33 > 24 (amount overpaid); 35a amount of line 34 to be "
                    "refunded (Form 8888 checkbox; 35b routing number, 35c account type "
                    "checking/savings, 35d account number); 36 amount of line 34 applied to "
                    "2026 estimated tax; 37 = 24 - 33 (amount you owe); 38 estimated tax "
                    "penalty (see instructions)."
                ),
                "summary_text": "Refund/owe block; 35a-35d direct deposit; 36 carryforward; 38 penalty.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ─── Pub 1040-TT: Tax Table + Tax Computation Worksheet ───
    {
        "source_code": "IRS_2025_1040_TT",
        "source_type": "official_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "Publication 1040 (2025) — Tax and Earned Income Credit Tables",
        "citation": "Pub. 1040 (2025), Tax Table pp. 2-13; 2025 Tax Computation Worksheet p. 14",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i1040tt.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": (
            "The published 2025 Tax Table and Tax Computation Worksheet. Row values "
            "transcribed positionally (pymupdf words grouped by y-band) 2026-06-10."
        ),
        "topics": ["tax_computation"],
        "excerpts": [
            {
                "excerpt_label": "Tax Table row structure",
                "location_reference": "Pub. 1040 (2025), Tax Table, pp. 2-13",
                "excerpt_text": (
                    "Columns: 'At least' / 'But less than' / Single / Married filing jointly* "
                    "/ Married filing separately / Head of a household. Rows: 0-5 (tax $0); "
                    "5-15 and 15-25 ($10-wide rows); 25 to 3,000 ($25-wide rows); 3,000 to "
                    "100,000 ($50-wide rows). After the 99,950-100,000 row the table ends "
                    "with: '$100,000 or over — use the Tax Computation Worksheet'. Footnote: "
                    "'* This column must also be used by a qualifying surviving spouse.'"
                ),
                "summary_text": "Band widths $10/$25/$50; table covers TI < $100,000; QSS uses the MFJ column.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Midpoint + round-half-up convention (verified inference)",
                "location_reference": "Pub. 1040 (2025), Tax Table (row-value verification)",
                "excerpt_text": (
                    "INFERENCE, verified against published rows: each row's tax equals the "
                    "rate-schedule tax computed at the row MIDPOINT, rounded to the nearest "
                    "whole dollar with $0.50 rounding UP. Half-dollar pins from the published "
                    "table: row 3,000-3,050 (midpoint 3,025; 10% = 302.50) prints 303; row "
                    "3,550-3,600 (midpoint 3,575; 10% = 357.50) prints 358. Final-row cross-"
                    "checks at midpoint 99,975 against Rev. Proc. 2024-40 §2.01 schedules: "
                    "single 16,908.50 -> printed 16,909; MFJ 11,822.50 -> 11,823; HOH "
                    "15,169.50 -> 15,170; MFS = single 16,909. Sample-table rows 25,300-"
                    "25,350: single 2,801 / MFJ 2,562 / MFS 2,801 / HOH 2,699 — all match "
                    "midpoint math exactly. The IRS does not print the word 'midpoint' in the "
                    "booklet; Ken must bless this convention as the encoding of the table."
                ),
                "summary_text": "Tax Table value = rate schedule at row midpoint, rounded half-UP to whole dollars — multi-point verified.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "2025 Tax Computation Worksheet (TI >= $100,000)",
                "location_reference": "Pub. 1040 (2025), p. 14",
                "excerpt_text": (
                    "Sections A (Single), B (MFJ or QSS), C (MFS), D (HOH). Each row: (a) "
                    "amount from line 15, (b) multiplication amount, (c) = (a) x (b), (d) "
                    "subtraction amount; tax = (c) - (d). Section A: at least 100,000 but not "
                    "over 103,350 -> 22% minus 5,086.00; over 103,350 not over 197,300 -> 24% "
                    "minus 7,153.00; over 197,300 not over 250,525 -> 32% minus 22,937.00; "
                    "over 250,525 not over 626,350 -> 35% minus 30,452.75; over 626,350 -> "
                    "37% minus 42,979.75. Section B first row: 100,000-206,700 -> 22% minus "
                    "10,172.00. Algebraically IDENTICAL to cumulative bracket math (checked: "
                    "single TI 100,000 -> 16,914.00 both ways). Bracket boundaries match Rev. "
                    "Proc. 2024-40 §2.01 exactly."
                ),
                "summary_text": "TCW = rate schedules in subtract-amount form; equals cumulative bracket computation.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ─── Pub 501 (2025) — standard deduction tables + filing status ───
    {
        "source_code": "PUB_501_2025",
        "source_type": "official_publication",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "Publication 501 (2025) — Dependents, Standard Deduction, and Filing Information",
        "citation": "Pub. 501 (2025), Tables 6, 7, 8 (pp. 25-26)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/p501.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.00,
        "requires_human_review": False,
        "notes": "TY2025 standard deduction charts transcribed verbatim 2026-06-10.",
        "topics": ["standard_deduction", "filing_status"],
        "excerpts": [
            {
                "excerpt_label": "Table 6 — base standard deduction (TY2025)",
                "location_reference": "Pub. 501 (2025), Table 6, p. 25",
                "excerpt_text": (
                    "Single or MFS $15,750; MFJ or QSS $31,500; HOH $23,625. Don't use this "
                    "chart if born before January 2, 1961, or blind, or if someone else can "
                    "claim you (or your spouse if filing jointly) as a dependent — use Table "
                    "7 or Table 8 instead."
                ),
                "summary_text": "TY2025 base amounts (OBBBA §70102 values).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Table 7 — aged/blind chart (TY2025)",
                "location_reference": "Pub. 501 (2025), Table 7, p. 25",
                "excerpt_text": (
                    "Check one box per condition: You born before January 2, 1961 / blind; "
                    "spouse born before January 2, 1961 / blind. Single: 1 box $17,750, 2 "
                    "$19,750 (+$2,000 each). MFJ: 1 $33,100, 2 $34,700, 3 $36,300, 4 $37,900 "
                    "(+$1,600 each). QSS: 1 $33,100, 2 $34,700 (+$1,600). MFS: 1 $17,350, 2 "
                    "$18,950, 3 $20,550, 4 $22,150 (+$1,600 each — the MARRIED rate even "
                    "though the MFS base equals single's). HOH: 1 $25,625, 2 $27,625 "
                    "(+$2,000). Footnote: MFS may check the spouse boxes only if the spouse "
                    "had no income, isn't filing a return, and can't be claimed as a "
                    "dependent on another person's return."
                ),
                "summary_text": "Additional per box: $2,000 unmarried (single/HOH); $1,600 married (MFJ/MFS/QSS).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Table 8 — dependent worksheet (TY2025)",
                "location_reference": "Pub. 501 (2025), Table 8, p. 26",
                "excerpt_text": (
                    "If someone can claim you (or your spouse if filing jointly) as a "
                    "dependent: (1) earned income; (2) additional amount $450; (3) = 1 + 2; "
                    "(4) minimum standard deduction $1,350; (5) larger of 3 or 4; (6) filing-"
                    "status base ($15,750 / $31,500 / $23,625); (7a) smaller of 5 or 6 — stop "
                    "here if born after January 1, 1961, and not blind; (7b) if born before "
                    "January 2, 1961, or blind: multiply $2,000 ($1,600 if married) by the "
                    "number of boxes; (7c) = 7a + 7b. Earned income includes wages, salaries, "
                    "tips, professional fees, other compensation for personal services, and "
                    "taxable scholarship/fellowship grants."
                ),
                "summary_text": "Dependent std deduction = min(base, max($1,350, earned + $450)) + aged/blind boxes.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Age-65 attainment + decedent rule",
                "location_reference": "Pub. 501 (2025), p. 26",
                "excerpt_text": (
                    "A person is considered to reach age 65 on the day before the person's "
                    "65th birthday (hence 'born before January 2' of tax_year - 64). A "
                    "deceased taxpayer is considered 65 or older at the end of 2025 only if "
                    "the taxpayer was 65 or older at the time of death."
                ),
                "summary_text": "Day-before-birthday attainment rule is the legal root of the Jan-2 convention; decedent edge.",
                "is_key_excerpt": False,
            },
        ],
    },
]
AUTHORITY_SOURCES += [
    # ─── Rev. Proc. 2024-40 (TY2025 inflation adjustments) ───
    {
        "source_code": "RP_2024_40",
        "source_type": "official_revenue_procedure",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "Rev. Proc. 2024-40 — TY2025 inflation adjustments",
        "citation": "Rev. Proc. 2024-40, §2.01 (tax rate tables)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-drop/rp-24-40.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": (
            "TY2025 ordinary rate schedules (§2.01 Tables 1-4) — verified against "
            "tts-tax-app TAX_BRACKETS 2026-06-10 (layout-aware extraction). NOTE: its "
            "§2.15 standard-deduction projections ($15,700/$31,400/$23,500) were "
            "SUPERSEDED by OBBBA §70102 — do NOT cite §2.15 for the deduction."
        ),
        "topics": ["tax_computation"],
        "excerpts": [
            {
                "excerpt_label": "§2.01 TY2025 rate schedule breakpoints",
                "location_reference": "Rev. Proc. 2024-40, §2.01, Tables 1-4",
                "excerpt_text": (
                    "Bracket tops (10/12/22/24/32/35/37%): Single 11,925 / 48,475 / 103,350 "
                    "/ 197,300 / 250,525 / 626,350; MFJ-QSS 23,850 / 96,950 / 206,700 / "
                    "394,600 / 501,050 / 751,600; MFS as single through 32% then 35% top "
                    "375,800; HOH 17,000 / 64,850 / 103,350 / 197,300 / 250,500 / 626,350."
                ),
                "summary_text": "TY2025 ordinary brackets (matches code + the published TCW boundaries).",
                "is_key_excerpt": True,
            },
        ],
    },
    # ─── Rev. Proc. 2025-32 (TY2026 inflation adjustments) ───
    {
        "source_code": "RP_2025_32",
        "source_type": "official_revenue_procedure",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2026,
        "tax_year_end": 2026,
        "title": "Rev. Proc. 2025-32 — TY2026 inflation adjustments",
        "citation": "Rev. Proc. 2025-32, §4.01 (rate tables), §4.14 (standard deduction)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-drop/rp-25-32.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": (
            "TY2026 constants (sprint target year), verified 2026-06-10 via layout-aware "
            "extraction: §4.01 rate schedules (note the asymmetries — MFS 35% top "
            "$384,350; HOH 24%/32% breakpoints $25 below single's); §4.14(1) standard "
            "deduction $16,100/$32,200/$24,150; §4.14(2) dependent cap greater of $1,350 "
            "or $450 + earned income; §4.14(3) aged/blind additional $1,650 married / "
            "$2,050 unmarried."
        ),
        "topics": ["tax_computation", "standard_deduction"],
        "excerpts": [
            {
                "excerpt_label": "§4.01 TY2026 rate schedule breakpoints",
                "location_reference": "Rev. Proc. 2025-32, §4.01, Tables 1-4",
                "excerpt_text": (
                    "Bracket tops (10/12/22/24/32/35/37%): Single 12,400 / 50,400 / 105,700 "
                    "/ 201,775 / 256,225 / 640,600; MFJ-QSS 24,800 / 100,800 / 211,400 / "
                    "403,550 / 512,450 / 768,700; MFS as single through 32% then 35% top "
                    "384,350; HOH 17,700 / 67,450 / 105,700 / 201,750 / 256,200 / 640,600."
                ),
                "summary_text": "TY2026 ordinary brackets (in code since 0052ebf with 6 pinning tests).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§4.14 TY2026 standard deduction set",
                "location_reference": "Rev. Proc. 2025-32, §4.14(1)-(3)",
                "excerpt_text": (
                    "(1) Base: MFJ/QSS $32,200; HOH $24,150; single/MFS $16,100. (2) "
                    "Dependent limitation: greater of $1,350 or $450 + earned income (capped "
                    "at the base). (3) Aged/blind additional: $1,650 (married), $2,050 "
                    "(unmarried, not a surviving spouse)."
                ),
                "summary_text": "TY2026 std deduction base / dependent cap / aged-blind amounts.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ─── OBBBA §70102 (TY2025 standard deduction) ───
    {
        "source_code": "PL_119_21_70102",
        "source_type": "code_section",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": None,
        "title": "OBBBA §70102 — standard deduction amounts (P.L. 119-21)",
        "citation": "P.L. 119-21, §70102 (July 4, 2025), amending IRC §63(c)",
        "issuer": "Congress",
        "official_url": "https://www.congress.gov/119/plaws/publ21/PLAW-119publ21.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": True,
        "notes": (
            "Enacted the TY2025 base standard deduction $15,750 / $31,500 / $23,625, "
            "superseding the Rev. Proc. 2024-40 §2.15 projections. Double-confirmed by "
            "the 2025 Form 1040 page-2 margin and Pub 501 Table 6. Found+fixed in "
            "tts-tax-app 2026-06-10 (commit 0c1e771)."
        ),
        "topics": ["standard_deduction"],
        "excerpts": [
            {
                "excerpt_label": "§70102 TY2025 amounts",
                "location_reference": "P.L. 119-21, §70102",
                "excerpt_text": (
                    "TY2025 standard deduction: $31,500 MFJ/QSS; $23,625 HOH; $15,750 "
                    "single/MFS; inflation-indexed thereafter (TY2026 values published in "
                    "Rev. Proc. 2025-32 §4.14(1))."
                ),
                "summary_text": "OBBBA TY2025 base standard deduction.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ─── IRC §1 (tax imposed; rate schedules) ───
    {
        "source_code": "IRC_1",
        "source_type": "code_section",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": None,
        "tax_year_end": None,
        "title": "IRC §1 — Tax imposed",
        "citation": "26 U.S.C. §1; §1(j) (TCJA rates); §1(f) (inflation adjustment)",
        "issuer": "Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:1)",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": True,
        "notes": "Imposes the income tax by filing status; §1(j) seven-rate structure; §1(f) indexing.",
        "topics": ["tax_computation", "filing_status"],
        "excerpts": [
            {
                "excerpt_label": "§1(a)-(d), (j) — rates by filing status",
                "location_reference": "26 U.S.C. §1(a)-(d), (j)",
                "excerpt_text": (
                    "Tax imposed on married individuals filing jointly and surviving spouses "
                    "(§1(a)); heads of households (§1(b)); unmarried individuals (§1(c)); "
                    "married filing separately (§1(d)). §1(j) sets the 10/12/22/24/32/35/37% "
                    "structure for 2018+ (made permanent by OBBBA §70101)."
                ),
                "summary_text": "Statutory basis for the four rate schedules; QSS taxed under §1(a).",
                "is_key_excerpt": True,
            },
        ],
    },
    # ─── IRC §3 (tax tables) ───
    {
        "source_code": "IRC_3",
        "source_type": "code_section",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": None,
        "tax_year_end": None,
        "title": "IRC §3 — Tax tables for individuals",
        "citation": "26 U.S.C. §3",
        "issuer": "Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:3)",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": True,
        "notes": "Authorizes Secretary-prescribed tax tables; table tax IS the §1 tax for table-eligible income.",
        "topics": ["tax_computation"],
        "excerpts": [
            {
                "excerpt_label": "§3(a)-(b) — table tax in lieu of §1 computation",
                "location_reference": "26 U.S.C. §3",
                "excerpt_text": (
                    "Individuals with taxable income below the ceiling amount pay a tax "
                    "determined under tables prescribed by the Secretary (income brackets of "
                    "uniform size); the table amount is treated as the tax imposed by §1. "
                    "The 2025 ceiling as administered is $100,000 (Tax Table covers TI under "
                    "$100,000)."
                ),
                "summary_text": "Statutory authority for the Tax Table lookup convention.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ─── IRC §2 (definitions: QSS, HOH) ───
    {
        "source_code": "IRC_2",
        "source_type": "code_section",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": None,
        "tax_year_end": None,
        "title": "IRC §2 — Definitions and special rules (QSS, HOH)",
        "citation": "26 U.S.C. §2(a) (surviving spouse), §2(b) (head of household)",
        "issuer": "Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:2)",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": True,
        "notes": "QSS: spouse died in one of two preceding years + maintains household for dependent child. HOH: unmarried + maintains household for qualifying person.",
        "topics": ["filing_status"],
        "excerpts": [
            {
                "excerpt_label": "§2(a)/(b) — QSS and HOH definitions",
                "location_reference": "26 U.S.C. §2(a), (b)",
                "excerpt_text": (
                    "Surviving spouse: taxpayer whose spouse died during either of the two "
                    "taxable years immediately preceding, who maintains a household that is "
                    "the principal place of abode of a dependent child (§2(a)); taxed at "
                    "§1(a) MFJ rates. Head of household: not married at year end, not a "
                    "surviving spouse, maintains as their home a household that is the "
                    "principal place of abode of a qualifying child or dependent for more "
                    "than half the year (§2(b))."
                ),
                "summary_text": "Definitional gates behind the QSS and HOH checkboxes — preparer-asserted this sprint.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ─── IRC §7703 (marital status) ───
    {
        "source_code": "IRC_7703",
        "source_type": "code_section",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": None,
        "tax_year_end": None,
        "title": "IRC §7703 — Determination of marital status",
        "citation": "26 U.S.C. §7703(a), (b)",
        "issuer": "Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:7703)",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": True,
        "notes": "Year-end determination; legal separation = unmarried; §7703(b) abandoned-spouse rule behind the form's lived-apart checkbox.",
        "topics": ["filing_status"],
        "excerpts": [
            {
                "excerpt_label": "§7703(a)-(b) — year-end status; lived-apart rule",
                "location_reference": "26 U.S.C. §7703",
                "excerpt_text": (
                    "Marital status is determined at the close of the taxable year (or at "
                    "death); a legally separated individual (decree of divorce or separate "
                    "maintenance) is not married (§7703(a)). §7703(b): a married individual "
                    "maintaining a household for a qualifying child, whose spouse was not a "
                    "member of the household during the last 6 months of the year, and who "
                    "furnishes over half the household cost, is considered NOT married — "
                    "the basis of the 2025 form's MFS/HOH lived-apart checkbox."
                ),
                "summary_text": "Year-end marital determination + §7703(b) considered-unmarried rule.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ─── IRC §6654 (estimated tax) ───
    {
        "source_code": "IRC_6654",
        "source_type": "code_section",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": None,
        "tax_year_end": None,
        "title": "IRC §6654 — Failure by individual to pay estimated income tax",
        "citation": "26 U.S.C. §6654",
        "issuer": "Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:6654)",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": True,
        "notes": (
            "Informs the line 26 quarterly-payment input model and line 38. Penalty "
            "COMPUTATION (Form 2210) is deferred per sprint scope — line 38 is direct "
            "entry; the IRS bills the penalty meanwhile."
        ),
        "topics": ["estimated_payments"],
        "excerpts": [
            {
                "excerpt_label": "§6654 — quarterly installments",
                "location_reference": "26 U.S.C. §6654(c)",
                "excerpt_text": (
                    "Four required installments (Apr 15 / Jun 15 / Sep 15 / Jan 15 of the "
                    "following year). The spine models line 26 as four quarterly inputs plus "
                    "the prior-year overpayment applied."
                ),
                "summary_text": "Quarterly structure behind the 4-quarter + PY-applied input model.",
                "is_key_excerpt": False,
            },
        ],
    },
]


# ═══════════════════════════════════════════════════════════════════════════
# NEW EXCERPTS ON EXISTING SOURCES
# ═══════════════════════════════════════════════════════════════════════════

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = [
    (
        "IRS_2025_1040_INSTR",
        {
            "excerpt_label": "Line 16 — method routing",
            "location_reference": "2025 Instructions for Form 1040, Line 16 (p. 36)",
            "excerpt_text": (
                "VERBATIM: 'Tax Table or Tax Computation Worksheet. If your taxable income "
                "is less than $100,000, you must use the Tax Table, later in these "
                "instructions, to figure your tax. Be sure you use the correct column. If "
                "your taxable income is $100,000 or more, use the Tax Computation Worksheet "
                "right after the Tax Table. However, don't use the Tax Table or Tax "
                "Computation Worksheet to figure your tax if any of the following applies.' "
                "The exceptions listed: Form 8615 (unearned income over $2,700 + age "
                "conditions); Schedule D Tax Worksheet (Sch D required AND line 18 or 19 > 0 "
                "AND lines 15 and 16 are gains; or Form 4952 line 4g); Qualified Dividends "
                "and Capital Gain Tax Worksheet (if not using the Sch D Tax Worksheet and: "
                "qualified dividends on line 3a; OR no Schedule D required and capital gain "
                "distributions reported on line 7a; ...); Schedule J; Foreign Earned Income "
                "Tax Worksheet (if filing Form 2555)."
            ),
            "summary_text": "Table mandatory under $100,000; TCW at/above; QDCGT/SchD-TW/8615/J/FEIE override — the bridge diagnostic's trigger list.",
            "is_key_excerpt": True,
        },
    ),
    (
        "IRS_2025_1040_INSTR",
        {
            "excerpt_label": "Line 16 — amounts included via checkboxes",
            "location_reference": "2025 Instructions for Form 1040, Line 16 (p. 34)",
            "excerpt_text": (
                "Include in the line 16 total: tax on taxable income (by the routed "
                "method); tax from Form(s) 8814 (child's interest/dividends — box 1); tax "
                "from Form 4972 (lump-sum distributions — box 2); §962 election tax (box 3 "
                "'962'); recapture of an education credit (box 3 'ECR'); tax from Form "
                "8621 line 16e; §965(i) triggered liability (box 3 '965INC')."
            ),
            "summary_text": "Line 16 add-on taxes — ALL fire RED-unsupported in the v1 spine (checkbox literals stored).",
            "is_key_excerpt": True,
        },
    ),
    (
        "IRS_2025_1040_INSTR",
        {
            "excerpt_label": "Standard deduction — exceptions 1-3",
            "location_reference": "2025 Instructions for Form 1040, Line 12 (p. 34)",
            "excerpt_text": (
                "Exception 1 — Dependent (line 12a checked): use the Standard Deduction "
                "Worksheet for Dependents. Exception 2 — Spouse itemizes on a separate "
                "return (12b): your standard deduction is ZERO, even if born before "
                "January 2, 1961, or blind. Exception 3 — Dual-status alien (12c): standard "
                "deduction is ZERO (same override)."
            ),
            "summary_text": "12b/12c force a zero standard deduction regardless of aged/blind boxes.",
            "is_key_excerpt": True,
        },
    ),
    (
        "IRS_2025_1040_INSTR",
        {
            "excerpt_label": "Lines 36-38 — applied election, owe, penalty",
            "location_reference": "2025 Instructions for Form 1040, pp. 63-65",
            "excerpt_text": (
                "Line 36 election (apply overpayment to 2026 estimates) CANNOT be changed "
                "later. Amount You Owe: 'You don't have to pay if line 37 is under $1.' "
                "VERBATIM: 'Include any estimated tax penalty from line 38 in the amount "
                "you enter on line 37.' Line 38 may apply if line 37 is at least $1,000 and "
                "more than 10% of the tax shown, or estimates were underpaid by any due "
                "date (possible even if a refund is due)."
            ),
            "summary_text": "L37 includes the L38 penalty; L36 irrevocable; under-$1 no-pay rule.",
            "is_key_excerpt": True,
        },
    ),
    (
        "IRC_63",
        {
            "excerpt_label": "§63(c)(5)/(c)(6)/(f) — dependent cap, ineligibles, aged/blind",
            "location_reference": "26 U.S.C. §63(c)(5), (c)(6), (f)",
            "excerpt_text": (
                "§63(c)(5): for a dependent claimable by another, the basic standard "
                "deduction is limited to the greater of a floor amount or earned income "
                "plus an additional amount (TY2025 and TY2026: $1,350 / $450 as indexed). "
                "§63(c)(6): standard deduction is ZERO for an MFS filer whose spouse "
                "itemizes, a nonresident/dual-status alien, and a short-year filer. "
                "§63(f): additional amounts for taxpayers aged 65+ and/or blind; the "
                "unmarried (non-surviving-spouse) additional is higher than the married "
                "additional ($2,000 vs $1,600 in TY2025; $2,050 vs $1,650 in TY2026)."
            ),
            "summary_text": "Statutory basis for Tables 7/8 and the 12b/12c zero overrides.",
            "is_key_excerpt": True,
        },
    ),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM FACTS
# Return-level unless the note says per-row. Dependents and W-2s are per-row.
# ═══════════════════════════════════════════════════════════════════════════

FORM_FACTS: list[dict] = [
    # ── Identity / status ──
    {"fact_key": "tax_year", "label": "Tax year of the return", "data_type": "integer",
     "required": True, "sort_order": 1,
     "notes": "Return-level. Drives every year-keyed constant. Unsupported year -> D_1040_002."},
    {"fact_key": "filing_status", "label": "Filing status", "data_type": "choice",
     "choices": ["single", "mfj", "mfs", "hoh", "qss"], "required": True, "sort_order": 2,
     "notes": "Return-level. The five 2025 statuses. QSS uses MFJ rate column/brackets."},
    {"fact_key": "hoh_qss_qualifying_person_name", "label": "HOH/QSS qualifying child's name (if not a dependent)",
     "data_type": "string", "sort_order": 3,
     "notes": "Return-level. Form field next to the status boxes. D_1040_006 nudges when HOH/QSS and blank with no dependents."},
    {"fact_key": "mfs_hoh_lived_apart_last_6_months", "label": "MFS/HOH lived-apart checkbox (§7703(b))",
     "data_type": "boolean", "sort_order": 4,
     "notes": "Return-level. 2025 form checkbox below the dependents block. Preparer-asserted."},
    {"fact_key": "nra_spouse_election", "label": "NRA/dual-status spouse treated as U.S. resident (election checkbox)",
     "data_type": "boolean", "sort_order": 5, "notes": "Return-level. Stored; no compute effect in the spine."},
    {"fact_key": "us_home_more_than_half_year", "label": "Main home in U.S. more than half of the year (checkbox)",
     "data_type": "boolean", "sort_order": 6,
     "notes": "Return-level. New 2025 checkbox; consumed by ACTC/EIC rules (Topics 6/7). Stored now."},
    {"fact_key": "digital_assets_answer", "label": "Digital assets question (yes/no)", "data_type": "choice",
     "choices": ["yes", "no"], "required": True, "sort_order": 7,
     "notes": "Return-level. Must be answered on every return; no compute effect."},
    {"fact_key": "taxpayer_dob", "label": "Taxpayer date of birth", "data_type": "date",
     "required": True, "sort_order": 8,
     "notes": "Return-level. Drives the 12d aged box: born before Jan 2 of (tax_year - 64)."},
    {"fact_key": "spouse_dob", "label": "Spouse date of birth (MFJ/MFS/QSS)", "data_type": "date",
     "sort_order": 9, "notes": "Return-level. Drives the spouse 12d aged box."},
    {"fact_key": "taxpayer_blind", "label": "Taxpayer is blind (12d)", "data_type": "boolean",
     "sort_order": 10, "notes": "Return-level. NEW model field needed in tts-tax-app (no blind flag exists today)."},
    {"fact_key": "spouse_blind", "label": "Spouse is blind (12d)", "data_type": "boolean",
     "sort_order": 11, "notes": "Return-level. NEW model field needed in tts-tax-app."},
    {"fact_key": "taxpayer_claimed_as_dependent", "label": "Someone can claim you as a dependent (12a)",
     "data_type": "boolean", "sort_order": 12,
     "notes": "Return-level. Routes the standard deduction to the dependent worksheet (Table 8)."},
    {"fact_key": "spouse_claimed_as_dependent", "label": "Someone can claim your spouse as a dependent (12a)",
     "data_type": "boolean", "sort_order": 13, "notes": "Return-level. Same routing on a joint return."},
    {"fact_key": "spouse_itemizes_separately", "label": "Spouse itemizes on a separate return (12b)",
     "data_type": "boolean", "sort_order": 14,
     "notes": "Return-level. Standard deduction = 0 (instructions Exception 2), even if aged/blind."},
    {"fact_key": "dual_status_alien", "label": "You were a dual-status alien (12c)", "data_type": "boolean",
     "sort_order": 15, "notes": "Return-level. Standard deduction = 0 (Exception 3)."},
    {"fact_key": "mfs_spouse_boxes_allowed", "label": "MFS: spouse had no income, isn't filing, not claimable (Table 7 footnote)",
     "data_type": "boolean", "sort_order": 16,
     "notes": "Return-level. Required before an MFS filer checks the SPOUSE aged/blind boxes. D_1040_010 polices it."},

    # ── Dependents (per-row, preparer-asserted) ──
    {"fact_key": "dep_first_name", "label": "Dependent first name", "data_type": "string",
     "sort_order": 20, "notes": "Per-Dependent (form col 1)."},
    {"fact_key": "dep_last_name", "label": "Dependent last name", "data_type": "string",
     "sort_order": 21, "notes": "Per-Dependent (col 2)."},
    {"fact_key": "dep_ssn", "label": "Dependent SSN/TIN", "data_type": "string",
     "sort_order": 22, "notes": "Per-Dependent (col 3). MeF format NNN-NN-NNNN; D_1040_007 on format failure."},
    {"fact_key": "dep_relationship", "label": "Dependent relationship", "data_type": "choice",
     "choices": ["child", "descendant_of_child", "sibling", "step_sibling",
                 "descendant_of_sibling", "foster_child", "adopted_child", "other"],
     "sort_order": 23, "notes": "Per-Dependent (col 4). Same 8 codes as the SCH_8812 spec / Dependent model."},
    {"fact_key": "dep_dob", "label": "Dependent date of birth", "data_type": "date",
     "sort_order": 24, "notes": "Per-Dependent. Drives age-consistency diagnostics (D_1040_008/009); NOT an adjudication input."},
    {"fact_key": "dep_lived_with_taxpayer_majority", "label": "Lived with you more than half the year (col 5a)",
     "data_type": "boolean", "sort_order": 25, "notes": "Per-Dependent. Preparer-asserted."},
    {"fact_key": "dep_residence_in_us", "label": "...and in the U.S. (col 5b)", "data_type": "boolean",
     "sort_order": 26, "notes": "Per-Dependent. NEW 2025 sub-box; consumed by CTC/EIC topics later. Stored now."},
    {"fact_key": "dep_full_time_student", "label": "Full-time student (col 6)", "data_type": "boolean",
     "sort_order": 27, "notes": "Per-Dependent. NEW 2025 box. Stored; feeds EIC/kiddie logic later."},
    {"fact_key": "dep_permanently_disabled", "label": "Permanently and totally disabled (col 6)",
     "data_type": "boolean", "sort_order": 28, "notes": "Per-Dependent. Exists on the Dependent model."},
    {"fact_key": "dep_ctc_flag", "label": "Child tax credit box (col 7)", "data_type": "boolean",
     "sort_order": 29, "notes": "Per-Dependent. Preparer-asserted; D_1040_008 checks age consistency. Consumed by SCH_8812."},
    {"fact_key": "dep_odc_flag", "label": "Credit for other dependents box (col 7)", "data_type": "boolean",
     "sort_order": 30, "notes": "Per-Dependent. Preparer-asserted; mutually exclusive with the CTC box."},

    # ── Income inputs (lines 1-8) ──
    {"fact_key": "w2_box1_total", "label": "Sum of W-2 box 1 (line 1a)", "data_type": "decimal",
     "default_value": "0", "sort_order": 40, "notes": "AGGREGATE over W2Income rows -> line 1a (computed feeder, exists today)."},
    {"fact_key": "household_employee_wages", "label": "Household employee wages (1b)", "data_type": "decimal",
     "default_value": "0", "sort_order": 41, "notes": "Return-level direct entry."},
    {"fact_key": "unreported_tips", "label": "Tip income not reported on 1a (1c)", "data_type": "decimal",
     "default_value": "0", "sort_order": 42,
     "notes": "Return-level direct entry. Interacts with Sch 1-A Part II (qualified tips) — preparer reconciles."},
    {"fact_key": "medicaid_waiver_payments", "label": "Medicaid waiver payments not on W-2 (1d)", "data_type": "decimal",
     "default_value": "0", "sort_order": 43, "notes": "Return-level direct entry."},
    {"fact_key": "dependent_care_benefits_taxable", "label": "Taxable dependent care benefits (1e, Form 2441 line 26)",
     "data_type": "decimal", "default_value": "0", "sort_order": 44,
     "notes": "Return-level direct entry until Form 2441 lands (post-sprint list)."},
    {"fact_key": "adoption_benefits_taxable", "label": "Employer-provided adoption benefits (1f, Form 8839 line 31)",
     "data_type": "decimal", "default_value": "0", "sort_order": 45, "notes": "Return-level direct entry; 8839 not built."},
    {"fact_key": "wages_8919", "label": "Wages from Form 8919 line 6 (1g)", "data_type": "decimal",
     "default_value": "0", "sort_order": 46, "notes": "Return-level direct entry; 8919 not built."},
    {"fact_key": "other_earned_income", "label": "Other earned income (1h)", "data_type": "decimal",
     "default_value": "0", "sort_order": 47, "notes": "Return-level direct entry with type literal."},
    {"fact_key": "nontaxable_combat_pay_election", "label": "Nontaxable combat pay election (1i, memo)",
     "data_type": "decimal", "default_value": "0", "sort_order": 48,
     "notes": "Return-level memo — NOT added into 1z. Already a Taxpayer field (nontaxable_combat_pay)."},
    {"fact_key": "tax_exempt_interest", "label": "Tax-exempt interest (2a)", "data_type": "decimal",
     "default_value": "0", "sort_order": 49, "notes": "AGGREGATE over InterestIncome rows (computed feeder, exists today)."},
    {"fact_key": "taxable_interest", "label": "Taxable interest (2b)", "data_type": "decimal",
     "default_value": "0", "sort_order": 50, "notes": "AGGREGATE over InterestIncome rows (computed feeder, exists today)."},
    {"fact_key": "qualified_dividends", "label": "Qualified dividends (3a)", "data_type": "decimal",
     "default_value": "0", "sort_order": 51,
     "notes": "Direct entry until Topic 3 (1099-DIV model). ANY value here fires the D_1040_001 bridge — tax not computable."},
    {"fact_key": "ordinary_dividends", "label": "Ordinary dividends (3b)", "data_type": "decimal",
     "default_value": "0", "sort_order": 52, "notes": "Direct entry until Topic 3. Included in line 9."},
    {"fact_key": "ira_distributions_gross", "label": "IRA distributions (4a)", "data_type": "decimal",
     "default_value": "0", "sort_order": 53, "notes": "Direct entry until Topic 5 (1099-R model)."},
    {"fact_key": "ira_distributions_taxable", "label": "IRA distributions — taxable (4b)", "data_type": "decimal",
     "default_value": "0", "sort_order": 54, "notes": "Direct entry until Topic 5. Included in line 9."},
    {"fact_key": "pensions_gross", "label": "Pensions and annuities (5a)", "data_type": "decimal",
     "default_value": "0", "sort_order": 55, "notes": "Direct entry until Topic 5."},
    {"fact_key": "pensions_taxable", "label": "Pensions and annuities — taxable (5b)", "data_type": "decimal",
     "default_value": "0", "sort_order": 56, "notes": "Direct entry until Topic 5. Included in line 9."},
    {"fact_key": "social_security_benefits", "label": "Social security benefits (6a)", "data_type": "decimal",
     "default_value": "0", "sort_order": 57, "notes": "Direct entry until Topic 5 (taxable-SS worksheet)."},
    {"fact_key": "social_security_taxable", "label": "Social security — taxable (6b)", "data_type": "decimal",
     "default_value": "0", "sort_order": 58, "notes": "Direct entry until Topic 5. Included in line 9."},
    {"fact_key": "ss_lump_sum_election", "label": "Lump-sum election method (6c checkbox)", "data_type": "boolean",
     "sort_order": 59, "notes": "RED unsupported (Topic 5 keeps it RED too) — D_1040_014."},
    {"fact_key": "capital_gain_or_loss", "label": "Capital gain or (loss) (7a)", "data_type": "decimal",
     "default_value": "0", "sort_order": 60,
     "notes": "Direct entry until Topics 3/8. ANY nonzero value fires the D_1040_001 bridge — tax not computable."},
    {"fact_key": "schedule_1_additional_income", "label": "Additional income — Schedule 1 line 10 (line 8)",
     "data_type": "decimal", "default_value": "0", "sort_order": 61,
     "notes": "Direct entry until Topic 2 seeds Schedule 1 (then computed from its total)."},
    {"fact_key": "schedule_1_adjustments", "label": "Adjustments — Schedule 1 line 26 (line 10)",
     "data_type": "decimal", "default_value": "0", "sort_order": 62, "notes": "Direct entry until Topic 2."},

    # ── Deductions ──
    {"fact_key": "itemizing", "label": "Itemizing (Schedule A) instead of standard deduction", "data_type": "boolean",
     "sort_order": 70, "notes": "Schedule A is post-sprint; itemized amount is direct entry on 12e with a WARNING."},
    {"fact_key": "itemized_deductions_amount", "label": "Itemized deductions (Schedule A) — manual",
     "data_type": "decimal", "default_value": "0", "sort_order": 71,
     "notes": "Direct entry; replaces the computed standard deduction on 12e when itemizing=True."},
    {"fact_key": "dependent_filer_earned_income", "label": "Earned income (dependent std-deduction worksheet line 1)",
     "data_type": "decimal", "default_value": "0", "sort_order": 72,
     "notes": "Used only when 12a is checked. Wages/salaries/tips/fees + taxable scholarship per Table 8."},
    {"fact_key": "qbi_deduction", "label": "QBI deduction (13a, Form 8995/8995-A)", "data_type": "decimal",
     "default_value": "0", "sort_order": 73, "notes": "Direct entry until the 8995 topic (post-sprint)."},
    {"fact_key": "sch_1a_additional_deductions", "label": "Schedule 1-A line 38 (13b)", "data_type": "decimal",
     "default_value": "0", "sort_order": 74, "notes": "COMPUTED feeder — flows from SCH_1A L38 (live today)."},

    # ── Tax / credits inputs ──
    {"fact_key": "tax_8814_amount", "label": "Tax from Form 8814 (line 16 box 1)", "data_type": "decimal",
     "default_value": "0", "sort_order": 80, "notes": "RED unsupported — D_1040_003."},
    {"fact_key": "tax_4972_amount", "label": "Tax from Form 4972 (line 16 box 2)", "data_type": "decimal",
     "default_value": "0", "sort_order": 81, "notes": "RED unsupported — D_1040_003."},
    {"fact_key": "tax_other_box3_amount", "label": "Line 16 box 3 amount (962/ECR/8621/965INC)", "data_type": "decimal",
     "default_value": "0", "sort_order": 82, "notes": "RED unsupported — D_1040_003. Literal stored with the amount."},
    {"fact_key": "schedule_2_line_3", "label": "Schedule 2 line 3 (line 17)", "data_type": "decimal",
     "default_value": "0", "sort_order": 83, "notes": "Direct entry until Topic 2. Maps to existing Taxpayer placeholder."},
    {"fact_key": "schedule_3_line_8", "label": "Schedule 3 line 8 (line 20)", "data_type": "decimal",
     "default_value": "0", "sort_order": 84, "notes": "Direct entry until Topic 2."},
    {"fact_key": "schedule_2_line_21", "label": "Schedule 2 line 21 (line 23)", "data_type": "decimal",
     "default_value": "0", "sort_order": 85, "notes": "Direct entry until Topic 2."},

    # ── Payments inputs ──
    {"fact_key": "w2_box2_total", "label": "Sum of W-2 box 2 withholding (25a)", "data_type": "decimal",
     "default_value": "0", "sort_order": 90, "notes": "AGGREGATE over W2Income rows (computed feeder, exists today)."},
    {"fact_key": "withholding_1099_total", "label": "Withholding from Form(s) 1099 (25b)", "data_type": "decimal",
     "default_value": "0", "sort_order": 91,
     "notes": "Direct-entry capable; becomes computed as 1099 document models land (InterestIncome box 4 today, 1099-R/DIV later)."},
    {"fact_key": "withholding_other_total", "label": "Withholding from other forms (25c)", "data_type": "decimal",
     "default_value": "0", "sort_order": 92, "notes": "Direct entry (W-2G, 8959 additional withholding, etc.)."},
    {"fact_key": "est_payment_q1", "label": "Estimated payment Q1 (due Apr 15)", "data_type": "decimal",
     "default_value": "0", "sort_order": 93, "notes": "Return-level. New input model — feeds line 26."},
    {"fact_key": "est_payment_q2", "label": "Estimated payment Q2 (due Jun 15)", "data_type": "decimal",
     "default_value": "0", "sort_order": 94, "notes": "Return-level. Feeds line 26."},
    {"fact_key": "est_payment_q3", "label": "Estimated payment Q3 (due Sep 15)", "data_type": "decimal",
     "default_value": "0", "sort_order": 95, "notes": "Return-level. Feeds line 26."},
    {"fact_key": "est_payment_q4", "label": "Estimated payment Q4 (due Jan 15)", "data_type": "decimal",
     "default_value": "0", "sort_order": 96, "notes": "Return-level. Feeds line 26."},
    {"fact_key": "py_overpayment_applied", "label": "Prior-year overpayment applied", "data_type": "decimal",
     "default_value": "0", "sort_order": 97, "notes": "Return-level. Feeds line 26."},
    {"fact_key": "former_spouse_ssn_for_estimates", "label": "Former spouse SSN (joint estimates literal)",
     "data_type": "string", "sort_order": 98, "notes": "Return-level literal under line 26. Format NNN-NN-NNNN when present."},
    {"fact_key": "eic_amount_manual", "label": "EIC (27a) — preparer-computed until Topic 7", "data_type": "decimal",
     "default_value": "0", "sort_order": 99, "notes": "Direct entry; D_1040_011 warns the engine isn't built."},
    {"fact_key": "clergy_se_box", "label": "Clergy filing Schedule SE (27b checkbox)", "data_type": "boolean",
     "sort_order": 100, "notes": "Stored; EIC clergy path is Topic 7+. RED via D_1040_011 when checked with 27a > 0."},
    {"fact_key": "eic_opt_out", "label": "Do not claim EIC (27c checkbox)", "data_type": "boolean",
     "sort_order": 101, "notes": "Stored."},
    {"fact_key": "aotc_amount_manual", "label": "American opportunity credit (29) — manual until 8863",
     "data_type": "decimal", "default_value": "0", "sort_order": 102, "notes": "Direct entry; D_1040_011 warns."},
    {"fact_key": "refundable_adoption_credit", "label": "Refundable adoption credit (30, Form 8839 line 13) — manual",
     "data_type": "decimal", "default_value": "0", "sort_order": 103,
     "notes": "NEW 2025 line. Direct entry; D_1040_011 warns (8839 not built)."},
    {"fact_key": "schedule_3_line_15", "label": "Schedule 3 line 15 (line 31)", "data_type": "decimal",
     "default_value": "0", "sort_order": 104, "notes": "Direct entry until Topic 2."},

    # ── Refund / owe inputs ──
    {"fact_key": "refund_requested", "label": "Amount of line 34 to refund (35a)", "data_type": "decimal",
     "default_value": "0", "sort_order": 110, "notes": "35a + 36 must equal line 34 (D_1040_012). Defaults to all of 34."},
    {"fact_key": "applied_to_next_year", "label": "Amount of line 34 applied to next year (36)", "data_type": "decimal",
     "default_value": "0", "sort_order": 111, "notes": "Irrevocable election per instructions."},
    {"fact_key": "routing_number", "label": "Direct deposit routing number (35b)", "data_type": "string",
     "sort_order": 112, "notes": "Entry-level validation: 9 digits, valid ABA prefix. MeF-typed field."},
    {"fact_key": "account_number", "label": "Direct deposit account number (35d)", "data_type": "string",
     "sort_order": 113, "notes": "Entry-level validation: 1-17 alphanumeric. MeF-typed field."},
    {"fact_key": "account_type", "label": "Account type (35c)", "data_type": "choice",
     "choices": ["checking", "savings"], "sort_order": 114, "notes": "Required when 35a > 0 and direct deposit used."},
    {"fact_key": "estimated_tax_penalty", "label": "Estimated tax penalty (38) — manual until Form 2210",
     "data_type": "decimal", "default_value": "0", "sort_order": 115,
     "notes": "Direct entry (IRS bills it otherwise). INCLUDED in line 37 per the instructions."},

    # ── Calculated outputs (traceability) ──
    {"fact_key": "total_income", "label": "Total income (line 9)", "data_type": "decimal", "sort_order": 120,
     "notes": "Calculated: 1z + 2b + 3b + 4b + 5b + 6b + 7a + 8."},
    {"fact_key": "agi", "label": "Adjusted gross income (11a/11b)", "data_type": "decimal", "sort_order": 121,
     "notes": "Calculated: 9 - 10. App internal key '11'."},
    {"fact_key": "standard_deduction_amount", "label": "Standard deduction (12e when not itemizing)",
     "data_type": "decimal", "sort_order": 122,
     "notes": "Calculated per R-STD-01..07 (base + aged/blind, dependent worksheet, zero overrides)."},
    {"fact_key": "taxable_income", "label": "Taxable income (15)", "data_type": "decimal", "sort_order": 123,
     "notes": "Calculated: max(0, 11b - 14)."},
    {"fact_key": "tax_line_16", "label": "Tax (16)", "data_type": "decimal", "sort_order": 124,
     "notes": "Calculated per the routed method (Tax Table / TCW); add-on boxes are RED-unsupported."},
    {"fact_key": "total_tax", "label": "Total tax (24)", "data_type": "decimal", "sort_order": 125,
     "notes": "Calculated: max(0, 18 - 21) + 23."},
    {"fact_key": "total_payments", "label": "Total payments (33)", "data_type": "decimal", "sort_order": 126,
     "notes": "Calculated: 25d + 26 + 32."},
    {"fact_key": "overpayment", "label": "Overpayment (34)", "data_type": "decimal", "sort_order": 127,
     "notes": "Calculated: max(0, 33 - 24)."},
    {"fact_key": "amount_owed", "label": "Amount you owe (37)", "data_type": "decimal", "sort_order": 128,
     "notes": "Calculated: max(0, 24 - 33) + line 38 penalty (per instructions)."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM RULES
# ═══════════════════════════════════════════════════════════════════════════

FORM_RULES: list[dict] = [
    # ── Filing status ──
    {"rule_id": "R-FS-01", "title": "Filing status — five statuses, year-end determination", "rule_type": "classification",
     "precedence": 0, "sort_order": 1,
     "formula": "filing_status in {single, mfj, mfs, hoh, qss}; marital status determined at Dec 31 (or date of death); legally separated = unmarried",
     "inputs": ["filing_status"], "outputs": [],
     "description": ("ONCE PER RETURN. §7703(a) year-end determination. Status is preparer-selected; "
                     "the spine validates consistency (spouse fields on MFJ/MFS, qualifying person on "
                     "HOH/QSS) but does NOT adjudicate eligibility this sprint.")},
    {"rule_id": "R-FS-02", "title": "QSS uses the MFJ rate column and brackets", "rule_type": "routing",
     "precedence": 0, "sort_order": 2,
     "formula": "tax_column(qss) = tax_column(mfj); brackets(qss) = brackets(mfj); std_ded(qss) = std_ded(mfj)",
     "inputs": ["filing_status"], "outputs": [],
     "description": ("ONCE PER RETURN. §1(a) taxes surviving spouses with joint filers; the Tax Table "
                     "footnote directs QSS to the MFJ column; Pub 501 Table 6 gives QSS the MFJ base. "
                     "BUT the aged/blind additional is the MARRIED $1,600 rate (Table 7) and QSS can "
                     "check at most 2 boxes (self only).")},
    {"rule_id": "R-FS-03", "title": "MFS/HOH lived-apart checkbox (§7703(b))", "rule_type": "classification",
     "precedence": 0, "sort_order": 3,
     "formula": "checkbox stored; preparer asserts the §7703(b)/legal-separation facts",
     "inputs": ["mfs_hoh_lived_apart_last_6_months"], "outputs": [],
     "description": ("ONCE PER RETURN. The 2025 form checkbox. Consumed by EIC/CTC and the 6d SS box "
                     "downstream; no spine compute effect.")},
    {"rule_id": "R-FS-04", "title": "HOH/QSS qualifying person name", "rule_type": "validation",
     "precedence": 0, "sort_order": 4,
     "formula": "if filing_status in {hoh, qss} and qualifying person is a non-dependent child: name entered",
     "inputs": ["filing_status", "hoh_qss_qualifying_person_name"], "outputs": [],
     "description": "ONCE PER RETURN. D_1040_006 warns when HOH/QSS with no dependents and no name."},

    # ── Dependents (entry + diagnostics only — NO adjudication engine) ──
    {"rule_id": "R-DEP-01", "title": "Dependent entry is preparer-asserted", "rule_type": "classification",
     "precedence": 0, "sort_order": 10,
     "formula": "dependent rows are entered with columns (1)-(7); qualification flags are assertions, not computed",
     "inputs": ["dep_first_name", "dep_last_name", "dep_ssn", "dep_relationship", "dep_dob",
                "dep_lived_with_taxpayer_majority", "dep_residence_in_us", "dep_full_time_student",
                "dep_permanently_disabled", "dep_ctc_flag", "dep_odc_flag"], "outputs": [],
     "description": ("PER DEPENDENT ROW. Sprint scope: NO eligibility adjudication engine. The §152 "
                     "tests live with the preparer; the spine stores the assertions and fires "
                     "consistency diagnostics (D_1040_007/008/009). SCH_8812 consumes the CTC/ODC flags.")},
    {"rule_id": "R-DEP-02", "title": "Dependent SSN format (MeF)", "rule_type": "validation",
     "precedence": 0, "sort_order": 11,
     "formula": "dep_ssn matches NNN-NN-NNNN",
     "inputs": ["dep_ssn"], "outputs": [],
     "description": "PER DEPENDENT ROW. Entry-level validation; D_1040_007 (error) on failure."},
    {"rule_id": "R-DEP-03", "title": "CTC flag vs age consistency", "rule_type": "validation",
     "precedence": 0, "sort_order": 12,
     "formula": "dep_ctc_flag implies age at Dec 31 of tax_year < 17 (per §24(c)); else D_1040_008",
     "inputs": ["dep_ctc_flag", "dep_dob", "tax_year"], "outputs": [],
     "description": ("PER DEPENDENT ROW. Consistency check only (the 8812 spec adjudicates the credit). "
                     "Also: CTC and ODC boxes are mutually exclusive on one row.")},

    # ── Income (lines 1-11) ──
    {"rule_id": "R-INC-01", "title": "Line 1a = sum of W-2 box 1", "rule_type": "calculation",
     "precedence": 1, "sort_order": 20,
     "formula": "L1a = sum(W2Income.wages)",
     "inputs": ["w2_box1_total"], "outputs": ["L1a"],
     "description": "AGGREGATE OVER W-2 ROWS. Computed feeder (exists in aggregate_1040_income today)."},
    {"rule_id": "R-INC-02", "title": "Line 1z = 1a + 1b + 1c + 1d + 1e + 1f + 1g + 1h", "rule_type": "calculation",
     "precedence": 2, "sort_order": 21,
     "formula": "L1z = L1a + L1b + L1c + L1d + L1e + L1f + L1g + L1h   (1i is a memo, NOT added)",
     "inputs": ["w2_box1_total", "household_employee_wages", "unreported_tips", "medicaid_waiver_payments",
                "dependent_care_benefits_taxable", "adoption_benefits_taxable", "wages_8919", "other_earned_income"],
     "outputs": ["L1z"],
     "description": "ONCE PER RETURN. Today's code computes L1z = L1a only — 1b-1h must be added (all direct entry)."},
    {"rule_id": "R-INC-03", "title": "Lines 2a/2b = interest aggregates", "rule_type": "calculation",
     "precedence": 1, "sort_order": 22,
     "formula": "L2a = sum(InterestIncome.tax_exempt_interest); L2b = sum(interest_income + treasury_interest)",
     "inputs": ["tax_exempt_interest", "taxable_interest"], "outputs": ["L2a", "L2b"],
     "description": "AGGREGATE OVER 1099-INT ROWS. Computed feeders (exist today). Topic 3 re-specs the full box surface."},
    {"rule_id": "R-INC-04", "title": "Line 9 = total income (eight addends)", "rule_type": "calculation",
     "precedence": 3, "sort_order": 23,
     "formula": "L9 = L1z + L2b + L3b + L4b + L5b + L6b + L7a + L8",
     "inputs": ["L1z", "taxable_interest", "ordinary_dividends", "ira_distributions_taxable",
                "pensions_taxable", "social_security_taxable", "capital_gain_or_loss", "schedule_1_additional_income"],
     "outputs": ["total_income", "L9"],
     "description": ("ONCE PER RETURN. Per the 2025 form face. Today's code sums only 1z + 2b + 8 — "
                     "the 3b/4b/5b/6b/7a addends must be wired (direct-entry capable now, computed as "
                     "their feeder topics land). L7a may be NEGATIVE (capital loss, limited upstream).")},
    {"rule_id": "R-INC-05", "title": "Line 11 (11a/11b) = AGI", "rule_type": "calculation",
     "precedence": 4, "sort_order": 24,
     "formula": "L11a = L9 - L10; L11b = L11a   (app internal key '11')",
     "inputs": ["L9", "schedule_1_adjustments"], "outputs": ["agi", "L11a", "L11b"],
     "description": "ONCE PER RETURN. AGI may be negative (NOL situations) — do NOT floor at 0."},

    # ── Standard deduction (line 12e) ──
    {"rule_id": "R-STD-01", "title": "Base standard deduction by filing status (year-keyed)", "rule_type": "calculation",
     "precedence": 5, "sort_order": 30,
     "formula": ("base = {TY2025: single/mfs 15750, mfj/qss 31500, hoh 23625 | "
                 "TY2026: single/mfs 16100, mfj/qss 32200, hoh 24150}[tax_year][filing_status]"),
     "inputs": ["filing_status", "tax_year"], "outputs": [],
     "description": ("ONCE PER RETURN. TY2025 per OBBBA §70102 (Pub 501 Table 6; printed on the 2025 "
                     "form margin). TY2026 per Rev. Proc. 2025-32 §4.14(1). _constants_for_year pattern; "
                     "unsupported year -> D_1040_002, never a silent $0 or stale-year fallback.")},
    {"rule_id": "R-STD-02", "title": "Aged boxes — born before Jan 2 of (tax_year - 64)", "rule_type": "classification",
     "precedence": 5, "sort_order": 31,
     "formula": "aged_box(person) = dob < Jan 2 of (tax_year - 64)   (TY2025: 1961-01-02; TY2026: 1962-01-02)",
     "inputs": ["taxpayer_dob", "spouse_dob", "tax_year"], "outputs": [],
     "description": ("ONCE PER RETURN. The 12d boxes are DERIVED from DOB, not hand-checked. Legal root: "
                     "age 65 attained the day before the 65th birthday (Pub 501). Decedent edge: 65+ only "
                     "if 65+ at death (D_1040_013 info). Same convention as SCH_1A Part V (R-SEN-08).")},
    {"rule_id": "R-STD-03", "title": "Aged/blind additional amount per box (year-keyed)", "rule_type": "calculation",
     "precedence": 6, "sort_order": 32,
     "formula": ("boxes = aged_tp + blind_tp + aged_sp + blind_sp; per_box = TY2025: 1600 married / 2000 unmarried; "
                 "TY2026: 1650 married / 2050 unmarried; married = {mfj, mfs, qss}; unmarried = {single, hoh}; "
                 "additional = boxes x per_box"),
     "inputs": ["taxpayer_blind", "spouse_blind", "filing_status", "tax_year"], "outputs": [],
     "description": ("ONCE PER RETURN. Pub 501 Table 7 (TY2025) / Rev. Proc. 2025-32 §4.14(3) (TY2026). "
                     "NOTE: MFS uses the MARRIED $1,600/$1,650 rate even though its base equals single's. "
                     "Spouse boxes: MFJ always; MFS only when mfs_spouse_boxes_allowed (Table 7 footnote, "
                     "D_1040_010); single/HOH/QSS never (no spouse at year end).")},
    {"rule_id": "R-STD-04", "title": "Dependent-filer worksheet (12a checked)", "rule_type": "calculation",
     "precedence": 6, "sort_order": 33,
     "formula": ("limited_base = min(base, max(dep_floor, earned + dep_addl)); dep_floor/dep_addl = "
                 "1350/450 (both TY2025 per Pub 501 Table 8 and TY2026 per RP 2025-32 §4.14(2)); "
                 "std_ded = limited_base + aged/blind additional (R-STD-03)"),
     "inputs": ["taxpayer_claimed_as_dependent", "spouse_claimed_as_dependent",
                "dependent_filer_earned_income", "filing_status", "tax_year"], "outputs": [],
     "description": ("ONCE PER RETURN. §63(c)(5) / Pub 501 Table 8. Earned income for this worksheet = "
                     "wages/salaries/tips/fees/compensation + taxable scholarship-fellowship. The "
                     "aged/blind additional is added AFTER the cap (worksheet line 7b).")},
    {"rule_id": "R-STD-05", "title": "Zero standard deduction overrides (12b/12c)", "rule_type": "calculation",
     "precedence": 7, "sort_order": 34,
     "formula": "if spouse_itemizes_separately OR dual_status_alien: std_ded = 0 (even if aged/blind)",
     "inputs": ["spouse_itemizes_separately", "dual_status_alien"], "outputs": [],
     "description": "ONCE PER RETURN. §63(c)(6); instructions Exceptions 2-3. Beats every other std-ded rule."},
    {"rule_id": "R-STD-06", "title": "Line 12e = standard deduction or itemized", "rule_type": "calculation",
     "precedence": 8, "sort_order": 35,
     "formula": "L12e = itemized_deductions_amount if itemizing else standard_deduction_amount   (app internal key '12')",
     "inputs": ["itemizing", "itemized_deductions_amount"], "outputs": ["standard_deduction_amount", "L12e"],
     "description": ("ONCE PER RETURN. Schedule A is post-sprint: when itemizing, 12e is direct entry "
                     "with D_1040_011-style warning. The existing standard_deduction_override field "
                     "remains an escape hatch but the computed chain above replaces it as default.")},

    # ── Tax (line 16) ──
    {"rule_id": "R-TAX-01", "title": "Line 16 method routing", "rule_type": "routing",
     "precedence": 9, "sort_order": 40,
     "formula": ("if TI < 100000: Tax Table (MANDATORY) | if TI >= 100000: Tax Computation Worksheet | "
                 "OVERRIDES (any -> D_1040_001/003/004, tax NOT computed): QDCGT triggers (L3a > 0, or "
                 "cap-gain distributions on L7a), Sch D Tax Worksheet triggers, Form 8615 conditions, "
                 "Schedule J, Form 2555 FEIE worksheet"),
     "inputs": ["taxable_income", "qualified_dividends", "capital_gain_or_loss"], "outputs": [],
     "description": ("ONCE PER RETURN. Verbatim from the 2025 instructions: under $100,000 the Tax Table "
                     "is mandatory ('you must use'); the spine NEVER applies rate schedules below the "
                     "threshold. Until Topic 3, any QDCGT trigger fires the RED bridge instead of "
                     "computing a wrong table-only number.")},
    {"rule_id": "R-TAX-02", "title": "Tax Table convention (TI < $100,000) — midpoint, half-up", "rule_type": "calculation",
     "precedence": 10, "sort_order": 41,
     "formula": ("rows: [0,5)->tax 0 by convention; [5,25) in $10 bands; [25,3000) in $25 bands; "
                 "[3000,100000) in $50 bands. tax(TI) = round_half_up_to_dollar( rate_schedule(filing_status, "
                 "tax_year, midpoint(row(TI))) ). Column by filing status; QSS uses the MFJ column."),
     "inputs": ["taxable_income", "filing_status", "tax_year"], "outputs": ["tax_line_16", "L16"],
     "description": ("ONCE PER RETURN. Encodes the published 2025 Tax Table exactly (structure transcribed; "
                     "convention verified at half-dollar pins 302.50->303 and 357.50->358 and the final row "
                     "for all four columns). A $2 mismatch vs TaxWise destroys preparer trust — table "
                     "semantics, NOT rate formulas, below $100,000. TY2026: same convention over the RP "
                     "2025-32 §4.01 schedules; RE-VERIFY against the published 2026 Tax Table when released.")},
    {"rule_id": "R-TAX-03", "title": "Tax Computation Worksheet (TI >= $100,000)", "rule_type": "calculation",
     "precedence": 10, "sort_order": 42,
     "formula": "tax = TI x marginal_rate - subtraction_amount  ==  cumulative bracket math over the year's rate schedule",
     "inputs": ["taxable_income", "filing_status", "tax_year"], "outputs": ["tax_line_16", "L16"],
     "description": ("ONCE PER RETURN. The published worksheet's multiply-subtract rows are algebraically "
                     "identical to compute_tax_from_brackets (verified at $100,000 single = 16,914.00 both "
                     "ways) — the existing bracket function IS the worksheet for TI >= $100,000.")},
    {"rule_id": "R-TAX-04", "title": "Rate schedules are year-keyed (TY2025 + TY2026)", "rule_type": "calculation",
     "precedence": 0, "sort_order": 43,
     "formula": ("TY2025 brackets per Rev. Proc. 2024-40 §2.01; TY2026 per Rev. Proc. 2025-32 §4.01 "
                 "(both already pinned in tts-tax-app TAX_BRACKETS with regression tests). QSS -> MFJ schedule."),
     "inputs": ["tax_year"], "outputs": [],
     "description": ("ONCE PER RETURN. Watch the asymmetries: MFS 35% top differs from single's "
                     "(375,800/384,350 vs 626,350/640,600); TY2026 HOH 24%/32% breakpoints are $25 below "
                     "single's. Never derive one status's schedule from another's.")},
    {"rule_id": "R-TAX-05", "title": "Unsupported tax year is a hard stop", "rule_type": "validation",
     "precedence": 0, "sort_order": 44,
     "formula": "if tax_year not in constants: D_1040_002 (error); line 16 NOT computed",
     "inputs": ["tax_year"], "outputs": [],
     "description": ("ONCE PER RETURN. Closes the verified silent gap: compute_tax_from_brackets returns "
                     "$0 for a missing year today. A RED diagnostic must fire instead — no silent $0 tax.")},
    {"rule_id": "R-TAX-06", "title": "Line 16 add-on taxes (8814/4972/box 3) — unsupported", "rule_type": "validation",
     "precedence": 0, "sort_order": 45,
     "formula": "if tax_8814_amount or tax_4972_amount or tax_other_box3_amount != 0: D_1040_003 (error)",
     "inputs": ["tax_8814_amount", "tax_4972_amount", "tax_other_box3_amount"], "outputs": [],
     "description": "ONCE PER RETURN. Checkbox literals + amounts are stored for the render leg, but v1 does not compute them."},
    {"rule_id": "R-TAX-07", "title": "BRIDGE — qualified dividends / capital gains block table-only tax", "rule_type": "validation",
     "precedence": 9, "sort_order": 46,
     "formula": "if L3a > 0 OR L7a != 0: D_1040_001 (error); line 16 NOT computed by the table/TCW",
     "inputs": ["qualified_dividends", "capital_gain_or_loss"], "outputs": [],
     "description": ("ONCE PER RETURN. Sprint Topic 1 DoD bridge: those returns need the QDCGT worksheet "
                     "(Topic 3) or Schedule D (Topic 8). The spine must never compute ordinary-rate tax on "
                     "preferential-rate income. Topic 3 replaces this diagnostic with the worksheet.")},
    {"rule_id": "R-TAX-08", "title": "Kiddie-tax exposure (Form 8615) — unsupported", "rule_type": "validation",
     "precedence": 0, "sort_order": 47,
     "formula": ("if taxpayer_claimed_as_dependent AND unearned income > 2700 (TY2025): D_1040_004 (error). "
                 "Unearned proxy in the spine: L2b + L2a + L3b + L7a."),
     "inputs": ["taxpayer_claimed_as_dependent", "taxable_interest", "tax_exempt_interest",
                "ordinary_dividends", "capital_gain_or_loss"], "outputs": [],
     "description": ("ONCE PER RETURN. 8615 is deferred (sprint scope). The $2,700 TY2025 threshold is "
                     "from the line 16 instructions; TY2026 amount must be verified when specced. "
                     "Conservative proxy errs toward firing.")},

    # ── Credits / other taxes (lines 17-24) ──
    {"rule_id": "R-CR-01", "title": "Line 17 = Schedule 2 line 3", "rule_type": "calculation",
     "precedence": 11, "sort_order": 50,
     "formula": "L17 = schedule_2_line_3   (direct entry until Topic 2)",
     "inputs": ["schedule_2_line_3"], "outputs": ["L17"],
     "description": "ONCE PER RETURN. Becomes computed when Schedule 2 lands (Topic 2)."},
    {"rule_id": "R-CR-02", "title": "Line 18 = 16 + 17", "rule_type": "calculation",
     "precedence": 12, "sort_order": 51,
     "formula": "L18 = L16 + L17",
     "inputs": ["L16", "L17"], "outputs": ["L18"],
     "description": "ONCE PER RETURN. tax_before_ctc — the value Schedule 8812 reads."},
    {"rule_id": "R-CR-03", "title": "Line 19 = Schedule 8812 line 14", "rule_type": "calculation",
     "precedence": 13, "sort_order": 52,
     "formula": "L19 = SCH_8812.L_14",
     "inputs": [], "outputs": ["L19"],
     "description": ("ONCE PER RETURN. CTC + ODC nonrefundable. Live today via compute_sch_8812. "
                     "(Re-specifies stub rule R001, retired by this loader.)")},
    {"rule_id": "R-CR-04", "title": "Line 20 = Schedule 3 line 8", "rule_type": "calculation",
     "precedence": 13, "sort_order": 53,
     "formula": "L20 = schedule_3_line_8   (direct entry until Topic 2)",
     "inputs": ["schedule_3_line_8"], "outputs": ["L20"],
     "description": "ONCE PER RETURN."},
    {"rule_id": "R-CR-05", "title": "Line 21 = 19 + 20; Line 22 = max(0, 18 - 21)", "rule_type": "calculation",
     "precedence": 14, "sort_order": 54,
     "formula": "L21 = L19 + L20; L22 = max(0, L18 - L21)",
     "inputs": ["L19", "L20", "L18"], "outputs": ["L21", "L22"],
     "description": "ONCE PER RETURN. The form's 'if zero or less, enter -0-' floor on 22."},
    {"rule_id": "R-CR-06", "title": "Line 23 = Schedule 2 line 21; Line 24 = 22 + 23", "rule_type": "calculation",
     "precedence": 15, "sort_order": 55,
     "formula": "L23 = schedule_2_line_21 (direct entry until Topic 2); L24 = L22 + L23",
     "inputs": ["schedule_2_line_21", "L22"], "outputs": ["total_tax", "L23", "L24"],
     "description": "ONCE PER RETURN. Total tax."},

    # ── Payments (lines 25-33) ──
    {"rule_id": "R-PAY-01", "title": "Line 25a = sum of W-2 box 2", "rule_type": "calculation",
     "precedence": 11, "sort_order": 60,
     "formula": "L25a = sum(W2Income.federal_tax_withheld)",
     "inputs": ["w2_box2_total"], "outputs": ["L25a"],
     "description": "AGGREGATE OVER W-2 ROWS. Computed feeder (exists today)."},
    {"rule_id": "R-PAY-02", "title": "Lines 25b/25c — 1099 and other withholding", "rule_type": "calculation",
     "precedence": 11, "sort_order": 61,
     "formula": ("L25b = withholding_1099_total (direct-entry capable; computed from 1099 documents as "
                 "they land — InterestIncome box 4 today, 1099-R/DIV later); L25c = withholding_other_total"),
     "inputs": ["withholding_1099_total", "withholding_other_total"], "outputs": ["L25b", "L25c"],
     "description": ("ONCE PER RETURN. Closes the Session-J audit gap: 1099-INT box 4 withholding has "
                     "nowhere to land today (25b missing from seed/compute/field map).")},
    {"rule_id": "R-PAY-03", "title": "Line 25d = 25a + 25b + 25c", "rule_type": "calculation",
     "precedence": 12, "sort_order": 62,
     "formula": "L25d = L25a + L25b + L25c",
     "inputs": ["L25a", "L25b", "L25c"], "outputs": ["L25d"],
     "description": "ONCE PER RETURN. Today's code sets 25d = 25a only — must include 25b + 25c."},
    {"rule_id": "R-PAY-04", "title": "Line 26 = estimated payments (4 quarters + PY applied)", "rule_type": "calculation",
     "precedence": 12, "sort_order": 63,
     "formula": "L26 = est_payment_q1 + est_payment_q2 + est_payment_q3 + est_payment_q4 + py_overpayment_applied",
     "inputs": ["est_payment_q1", "est_payment_q2", "est_payment_q3", "est_payment_q4", "py_overpayment_applied"],
     "outputs": ["L26"],
     "description": ("ONCE PER RETURN. New input model (sprint DoD). The form shows only the total; the "
                     "four-quarter + PY-applied detail is the input UI (TaxWise convention) and feeds "
                     "Form 2210 later. former_spouse_ssn_for_estimates renders as the line 26 literal.")},
    {"rule_id": "R-PAY-05", "title": "Lines 27a/29/30 — manual refundable credits (engines deferred)", "rule_type": "calculation",
     "precedence": 12, "sort_order": 64,
     "formula": ("L27a = eic_amount_manual (Topic 7 computes); L29 = aotc_amount_manual (8863 deferred); "
                 "L30 = refundable_adoption_credit (8839 deferred). Each nonzero entry -> D_1040_011 warning."),
     "inputs": ["eic_amount_manual", "aotc_amount_manual", "refundable_adoption_credit"],
     "outputs": ["L27a", "L29", "L30"],
     "description": ("ONCE PER RETURN. Direct entry per Quality Rule 5 (every line direct-entry capable "
                     "from day one); computed engines replace them topic by topic.")},
    {"rule_id": "R-PAY-06", "title": "Line 28 = Schedule 8812 line 27", "rule_type": "calculation",
     "precedence": 12, "sort_order": 65,
     "formula": "L28 = SCH_8812.L_27",
     "inputs": [], "outputs": ["L28"],
     "description": ("ONCE PER RETURN. Refundable ACTC. Live today via compute_sch_8812. "
                     "(Re-specifies stub rule R002, retired by this loader.)")},
    {"rule_id": "R-PAY-07", "title": "Line 31 = Schedule 3 line 15; Line 32 = 27a + 28 + 29 + 30 + 31", "rule_type": "calculation",
     "precedence": 13, "sort_order": 66,
     "formula": "L31 = schedule_3_line_15 (direct entry until Topic 2); L32 = L27a + L28 + L29 + L30 + L31",
     "inputs": ["schedule_3_line_15", "L27a", "L28", "L29", "L30"], "outputs": ["L31", "L32"],
     "description": "ONCE PER RETURN. Total other payments and refundable credits (includes NEW line 30)."},
    {"rule_id": "R-PAY-08", "title": "Line 33 = 25d + 26 + 32", "rule_type": "calculation",
     "precedence": 14, "sort_order": 67,
     "formula": "L33 = L25d + L26 + L32",
     "inputs": ["L25d", "L26", "L32"], "outputs": ["total_payments", "L33"],
     "description": "ONCE PER RETURN. Total payments. Today's code computes 25d + 28 only — must follow the form."},

    # ── Refund / amount owed (lines 34-38) ──
    {"rule_id": "R-REF-01", "title": "Line 34 = max(0, 33 - 24)", "rule_type": "calculation",
     "precedence": 15, "sort_order": 70,
     "formula": "L34 = max(0, L33 - L24)",
     "inputs": ["L33", "L24"], "outputs": ["overpayment", "L34"],
     "description": "ONCE PER RETURN. Overpayment."},
    {"rule_id": "R-REF-02", "title": "Refund split: 35a + 36 = 34", "rule_type": "validation",
     "precedence": 16, "sort_order": 71,
     "formula": "if L34 > 0: refund_requested + applied_to_next_year == L34 (default: 35a = L34, 36 = 0)",
     "inputs": ["refund_requested", "applied_to_next_year", "L34"], "outputs": ["L35a", "L36"],
     "description": ("ONCE PER RETURN. D_1040_012 (error) when the split doesn't tie. The line 36 "
                     "election is IRREVOCABLE per the instructions — D_1040_015 info reminds the preparer.")},
    {"rule_id": "R-REF-03", "title": "Line 37 = max(0, 24 - 33) + line 38 penalty", "rule_type": "calculation",
     "precedence": 16, "sort_order": 72,
     "formula": "L37 = max(0, L24 - L33) + estimated_tax_penalty   (when 24 > 33)",
     "inputs": ["L24", "L33", "estimated_tax_penalty"], "outputs": ["amount_owed", "L37"],
     "description": ("ONCE PER RETURN. VERBATIM instruction: 'Include any estimated tax penalty from "
                     "line 38 in the amount you enter on line 37.' Penalty COMPUTATION (Form 2210) is "
                     "deferred — line 38 is direct entry. Penalty entered WITH an overpayment (L34 > 0) "
                     "fires D_1040_016 (warning) — treatment verified manually until 2210 lands.")},
    {"rule_id": "R-REF-04", "title": "Direct deposit entry validation (35b-35d)", "rule_type": "validation",
     "precedence": 0, "sort_order": 73,
     "formula": "routing_number: 9 digits, ABA prefix 01-12/21-32; account_number: 1-17 alphanumeric; account_type required with direct deposit",
     "inputs": ["routing_number", "account_number", "account_type"], "outputs": [],
     "description": "ONCE PER RETURN. MeF-compatible entry-level validation (e-file readiness rule)."},

    # ── Year-keyed constants registry ──
    {"rule_id": "R-YR-01", "title": "Every constant is year-keyed (_constants_for_year)", "rule_type": "classification",
     "precedence": 0, "sort_order": 80,
     "formula": ("constants[2025] = {std_base: 15750/31500/23625; aged_blind: 1600 married, 2000 unmarried; "
                 "dep_floor/addl: 1350/450; brackets: RP 2024-40 §2.01; aged cutoff: 1961-01-02; kiddie "
                 "unearned threshold: 2700}. constants[2026] = {std_base: 16100/32200/24150; aged_blind: "
                 "1650/2050; dep_floor/addl: 1350/450; brackets: RP 2025-32 §4.01; aged cutoff: 1962-01-02; "
                 "kiddie threshold: VERIFY when 2026 instructions publish}."),
     "inputs": ["tax_year"], "outputs": [],
     "description": ("ONCE PER RETURN. Sprint target-year policy: TY2026 is the product target, TY2025 the "
                     "verification bed; each year verified independently (never assume a 2025 amount "
                     "carries). The TY2026 Tax Table is unpublished — table-convention output for 2026 "
                     "must be re-verified against the published table when released (tracker item).")},
]


# ═══════════════════════════════════════════════════════════════════════════
# RULE → AUTHORITY LINKS  (100% coverage — every rule links to ≥ 1 source)
# ═══════════════════════════════════════════════════════════════════════════

RULE_AUTHORITY_LINKS: list[tuple[str, str, str, str]] = [
    # ── Filing status ──
    ("R-FS-01", "IRC_7703", "primary", "§7703(a) year-end marital determination"),
    ("R-FS-01", "IRS_2025_1040_FORM", "primary", "Five status checkboxes on the 2025 form"),
    ("R-FS-02", "IRC_1", "primary", "§1(a) taxes surviving spouses at joint rates"),
    ("R-FS-02", "IRS_2025_1040_TT", "primary", "Tax Table footnote: QSS uses the MFJ column"),
    ("R-FS-02", "PUB_501_2025", "secondary", "Table 6 QSS base = MFJ; Table 7 QSS additional = married rate"),
    ("R-FS-03", "IRC_7703", "primary", "§7703(b) considered-unmarried rule"),
    ("R-FS-03", "IRS_2025_1040_FORM", "primary", "2025 lived-apart checkbox text"),
    ("R-FS-04", "IRC_2", "primary", "§2(a)/(b) qualifying person requirements"),
    ("R-FS-04", "IRS_2025_1040_FORM", "secondary", "HOH/QSS child-name entry on the form"),

    # ── Dependents ──
    ("R-DEP-01", "IRC_152", "primary", "§152 dependent definition (preparer applies the tests)"),
    ("R-DEP-01", "IRS_2025_1040_FORM", "primary", "2025 dependents grid columns (1)-(7)"),
    ("R-DEP-02", "IRS_2025_1040_FORM", "primary", "Dependent SSN column (3); MeF format"),
    ("R-DEP-03", "IRC_151", "secondary", "Dependent claim context"),
    ("R-DEP-03", "IRS_2025_1040_FORM", "primary", "Col (7) CTC/ODC checkboxes"),

    # ── Income ──
    ("R-INC-01", "IRS_2025_1040_FORM", "primary", "Line 1a: total from W-2 box 1"),
    ("R-INC-02", "IRS_2025_1040_FORM", "primary", "Line 1z = add lines 1a through 1h; 1i is a memo"),
    ("R-INC-03", "IRS_2025_1040_FORM", "primary", "Lines 2a/2b interest"),
    ("R-INC-04", "IRS_2025_1040_FORM", "primary", "Line 9 verbatim: add 1z, 2b, 3b, 4b, 5b, 6b, 7a, and 8"),
    ("R-INC-05", "IRS_2025_1040_FORM", "primary", "Line 11a = 9 - 10; 11b carries 11a to page 2"),

    # ── Standard deduction ──
    ("R-STD-01", "PL_119_21_70102", "primary", "TY2025 base amounts (OBBBA)"),
    ("R-STD-01", "PUB_501_2025", "primary", "Table 6 TY2025 base"),
    ("R-STD-01", "RP_2025_32", "primary", "§4.14(1) TY2026 base"),
    ("R-STD-01", "IRS_2025_1040_FORM", "secondary", "Page-2 margin prints the TY2025 amounts"),
    ("R-STD-02", "PUB_501_2025", "primary", "Born-before-Jan-2 convention; day-before-birthday rule"),
    ("R-STD-02", "IRS_2025_1040_FORM", "primary", "12d checkbox text: born before January 2, 1961"),
    ("R-STD-03", "IRC_63", "primary", "§63(f) additional amounts"),
    ("R-STD-03", "PUB_501_2025", "primary", "Table 7 per-box amounts incl. the MFS married rate + spouse-box footnote"),
    ("R-STD-03", "RP_2025_32", "primary", "§4.14(3) TY2026 amounts"),
    ("R-STD-04", "IRC_63", "primary", "§63(c)(5) dependent limitation"),
    ("R-STD-04", "PUB_501_2025", "primary", "Table 8 worksheet ($1,350 / $450; 7b after cap)"),
    ("R-STD-04", "RP_2025_32", "primary", "§4.14(2) TY2026 dependent figures"),
    ("R-STD-05", "IRC_63", "primary", "§63(c)(6) zero standard deduction cases"),
    ("R-STD-05", "IRS_2025_1040_INSTR", "primary", "Line 12 Exceptions 2-3"),
    ("R-STD-06", "IRS_2025_1040_FORM", "primary", "Line 12e: standard or itemized (Schedule A)"),

    # ── Tax ──
    ("R-TAX-01", "IRS_2025_1040_INSTR", "primary", "Line 16 routing verbatim ('must use the Tax Table')"),
    ("R-TAX-01", "IRC_3", "primary", "§3 table tax in lieu of §1 computation"),
    ("R-TAX-02", "IRS_2025_1040_TT", "primary", "Published table structure + verified midpoint/half-up convention"),
    ("R-TAX-02", "IRC_3", "primary", "§3(a) Secretary-prescribed tables"),
    ("R-TAX-03", "IRS_2025_1040_TT", "primary", "2025 Tax Computation Worksheet sections A-D"),
    ("R-TAX-03", "IRC_1", "primary", "§1 rate schedules"),
    ("R-TAX-04", "RP_2024_40", "primary", "§2.01 TY2025 schedules"),
    ("R-TAX-04", "RP_2025_32", "primary", "§4.01 TY2026 schedules"),
    ("R-TAX-05", "IRS_2025_1040_TT", "secondary", "No published table for other years — hard stop"),
    ("R-TAX-06", "IRS_2025_1040_INSTR", "primary", "Line 16 add-on taxes list (8814/4972/962/ECR/8621/965INC)"),
    ("R-TAX-07", "IRS_2025_1040_INSTR", "primary", "QDCGT worksheet triggers (3a; 7a cap-gain distributions)"),
    ("R-TAX-08", "IRS_2025_1040_INSTR", "primary", "Form 8615 conditions; $2,700 TY2025 threshold"),

    # ── Credits / other taxes ──
    ("R-CR-01", "IRS_2025_1040_FORM", "primary", "Line 17 from Schedule 2 line 3"),
    ("R-CR-02", "IRS_2025_1040_FORM", "primary", "Line 18 = 16 + 17"),
    ("R-CR-03", "IRS_2025_8812_FORM", "primary", "Schedule 8812 line 14 destination"),
    ("R-CR-03", "IRS_2025_1040_FORM", "primary", "Line 19 text"),
    ("R-CR-04", "IRS_2025_1040_FORM", "primary", "Line 20 from Schedule 3 line 8"),
    ("R-CR-05", "IRS_2025_1040_FORM", "primary", "Lines 21-22 with the zero floor"),
    ("R-CR-06", "IRS_2025_1040_FORM", "primary", "Lines 23-24 total tax"),

    # ── Payments ──
    ("R-PAY-01", "IRS_2025_1040_FORM", "primary", "Line 25a W-2 withholding"),
    ("R-PAY-02", "IRS_2025_1040_FORM", "primary", "Lines 25b/25c withholding sources"),
    ("R-PAY-03", "IRS_2025_1040_FORM", "primary", "Line 25d = add 25a through 25c"),
    ("R-PAY-04", "IRS_2025_1040_FORM", "primary", "Line 26 text incl. former-spouse SSN literal"),
    ("R-PAY-04", "IRC_6654", "secondary", "§6654(c) quarterly installment structure"),
    ("R-PAY-05", "IRS_2025_1040_FORM", "primary", "Lines 27a/29/30 (incl. NEW refundable adoption credit)"),
    ("R-PAY-06", "IRS_2025_8812_FORM", "primary", "Schedule 8812 line 27 destination"),
    ("R-PAY-07", "IRS_2025_1040_FORM", "primary", "Lines 31-32 sum (27a + 28 + 29 + 30 + 31)"),
    ("R-PAY-08", "IRS_2025_1040_FORM", "primary", "Line 33 = 25d + 26 + 32"),

    # ── Refund / owe ──
    ("R-REF-01", "IRS_2025_1040_FORM", "primary", "Line 34 overpaid"),
    ("R-REF-02", "IRS_2025_1040_FORM", "primary", "Lines 35a/36 split of line 34"),
    ("R-REF-02", "IRS_2025_1040_INSTR", "primary", "Line 36 election irrevocable"),
    ("R-REF-03", "IRS_2025_1040_FORM", "primary", "Lines 37-38"),
    ("R-REF-03", "IRS_2025_1040_INSTR", "primary", "'Include any estimated tax penalty from line 38 in line 37'"),
    ("R-REF-04", "IRS_2025_1040_FORM", "primary", "Lines 35b-35d direct deposit fields"),

    # ── Constants registry ──
    ("R-YR-01", "RP_2024_40", "primary", "TY2025 schedules"),
    ("R-YR-01", "RP_2025_32", "primary", "TY2026 schedules + std deduction set"),
    ("R-YR-01", "PL_119_21_70102", "primary", "TY2025 std deduction base"),
    ("R-YR-01", "PUB_501_2025", "primary", "TY2025 aged/blind + dependent figures"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM LINES (line_map) — 2025 IRS form labels. Where the tts-tax-app internal
# semantic key differs (DECISIONS 2026-05-29 convention), the note names it.
# ═══════════════════════════════════════════════════════════════════════════

FORM_LINES: list[dict] = [
    # ── Income ──
    {"line_number": "1a", "description": "Total from Form(s) W-2, box 1", "line_type": "calculated",
     "source_rules": ["R-INC-01"], "sort_order": 10, "notes": "Computed feeder (W2Income aggregate). App key 1a."},
    {"line_number": "1b", "description": "Household employee wages", "line_type": "input", "sort_order": 11},
    {"line_number": "1c", "description": "Tip income not reported on line 1a", "line_type": "input", "sort_order": 12},
    {"line_number": "1d", "description": "Medicaid waiver payments not on W-2", "line_type": "input", "sort_order": 13},
    {"line_number": "1e", "description": "Taxable dependent care benefits (Form 2441 line 26)", "line_type": "input",
     "sort_order": 14, "notes": "Direct entry until Form 2441 (post-sprint)."},
    {"line_number": "1f", "description": "Employer-provided adoption benefits (Form 8839 line 31)", "line_type": "input", "sort_order": 15},
    {"line_number": "1g", "description": "Wages from Form 8919 line 6", "line_type": "input", "sort_order": 16},
    {"line_number": "1h", "description": "Other earned income (type + amount)", "line_type": "input", "sort_order": 17},
    {"line_number": "1i", "description": "Nontaxable combat pay election (memo — NOT in 1z)", "line_type": "informational",
     "sort_order": 18, "notes": "Existing Taxpayer.nontaxable_combat_pay field."},
    {"line_number": "1z", "description": "Add lines 1a through 1h", "line_type": "subtotal",
     "source_rules": ["R-INC-02"], "sort_order": 19},
    {"line_number": "2a", "description": "Tax-exempt interest", "line_type": "calculated",
     "source_rules": ["R-INC-03"], "sort_order": 20, "notes": "Computed feeder (InterestIncome aggregate)."},
    {"line_number": "2b", "description": "Taxable interest", "line_type": "calculated",
     "source_rules": ["R-INC-03"], "sort_order": 21, "notes": "Computed feeder (InterestIncome aggregate)."},
    {"line_number": "3a", "description": "Qualified dividends", "line_type": "input", "sort_order": 22,
     "notes": "Direct entry until Topic 3. ANY value -> D_1040_001 bridge (tax not computed)."},
    {"line_number": "3b", "description": "Ordinary dividends", "line_type": "input", "sort_order": 23,
     "notes": "Direct entry until Topic 3. Included in line 9."},
    {"line_number": "3c", "description": "Child's dividends included (checkboxes: in 3a / in 3b)", "line_type": "informational",
     "sort_order": 24, "notes": "Form 8814 interplay -> RED via line 16 box 1 when tax effect claimed."},
    {"line_number": "4a", "description": "IRA distributions", "line_type": "input", "sort_order": 25,
     "notes": "Direct entry until Topic 5 (1099-R)."},
    {"line_number": "4b", "description": "IRA distributions — taxable amount", "line_type": "input", "sort_order": 26},
    {"line_number": "4c", "description": "Checkboxes: Rollover / QCD / blank literal", "line_type": "informational",
     "sort_order": 27, "notes": "Stored for render; Topic 5 wires the treatment."},
    {"line_number": "5a", "description": "Pensions and annuities", "line_type": "input", "sort_order": 28},
    {"line_number": "5b", "description": "Pensions and annuities — taxable amount", "line_type": "input", "sort_order": 29},
    {"line_number": "5c", "description": "Checkboxes: Rollover / PSO / blank literal", "line_type": "informational", "sort_order": 30},
    {"line_number": "6a", "description": "Social security benefits", "line_type": "input", "sort_order": 31},
    {"line_number": "6b", "description": "Social security — taxable amount", "line_type": "input", "sort_order": 32,
     "notes": "Direct entry until Topic 5 (provisional-income worksheet)."},
    {"line_number": "6c", "description": "Lump-sum election method checkbox", "line_type": "informational",
     "sort_order": 33, "notes": "Checked -> D_1040_014 RED (unsupported, stays RED through Topic 5)."},
    {"line_number": "6d", "description": "MFS lived apart all year checkbox", "line_type": "informational", "sort_order": 34},
    {"line_number": "7a", "description": "Capital gain or (loss); attach Schedule D if required", "line_type": "input",
     "sort_order": 35, "notes": "App key 7. Direct entry until Topics 3/8. Nonzero -> D_1040_001 bridge."},
    {"line_number": "7b", "description": "Checkboxes: Schedule D not required / includes child's gain", "line_type": "informational", "sort_order": 36},
    {"line_number": "8", "description": "Additional income from Schedule 1, line 10", "line_type": "input",
     "sort_order": 37, "notes": "Direct entry until Topic 2 wires the Schedule 1 total."},
    {"line_number": "9", "description": "Total income = 1z + 2b + 3b + 4b + 5b + 6b + 7a + 8", "line_type": "subtotal",
     "source_rules": ["R-INC-04"], "sort_order": 38},
    {"line_number": "10", "description": "Adjustments from Schedule 1, line 26", "line_type": "input",
     "sort_order": 39, "notes": "Direct entry until Topic 2."},
    {"line_number": "11a", "description": "Adjusted gross income = 9 - 10 (page 1)", "line_type": "calculated",
     "source_rules": ["R-INC-05"], "sort_order": 40, "notes": "App key 11. May be negative — no floor."},
    {"line_number": "11b", "description": "Amount from line 11a (page 2 carry)", "line_type": "calculated",
     "source_rules": ["R-INC-05"], "sort_order": 41},

    # ── Deductions ──
    {"line_number": "12a", "description": "Checkboxes: someone can claim You / Your spouse as a dependent", "line_type": "informational",
     "sort_order": 50, "notes": "Routes 12e to the dependent worksheet (R-STD-04)."},
    {"line_number": "12b", "description": "Checkbox: spouse itemizes on a separate return", "line_type": "informational",
     "sort_order": 51, "notes": "Std deduction = 0 (R-STD-05)."},
    {"line_number": "12c", "description": "Checkbox: you were a dual-status alien", "line_type": "informational",
     "sort_order": 52, "notes": "Std deduction = 0 (R-STD-05)."},
    {"line_number": "12d", "description": "Checkboxes: You/Spouse born before Jan 2, 1961 / blind", "line_type": "informational",
     "sort_order": 53, "notes": "Aged boxes DERIVED from DOB (R-STD-02); blind boxes are new model fields."},
    {"line_number": "12e", "description": "Standard deduction or itemized deductions (Schedule A)", "line_type": "calculated",
     "source_rules": ["R-STD-01", "R-STD-02", "R-STD-03", "R-STD-04", "R-STD-05", "R-STD-06"],
     "sort_order": 54, "notes": "App key 12."},
    {"line_number": "13a", "description": "QBI deduction (Form 8995/8995-A)", "line_type": "input",
     "sort_order": 55, "notes": "App key 13. Direct entry until the 8995 topic (post-sprint)."},
    {"line_number": "13b", "description": "Additional deductions from Schedule 1-A, line 38", "line_type": "calculated",
     "sort_order": 56, "notes": "App key 13b. Computed feeder — SCH_1A live today."},
    {"line_number": "14", "description": "Add lines 12e, 13a, and 13b", "line_type": "subtotal", "sort_order": 57},
    {"line_number": "15", "description": "Taxable income = max(0, 11b - 14)", "line_type": "calculated", "sort_order": 58},

    # ── Tax and credits ──
    {"line_number": "16", "description": "Tax (Tax Table / Tax Computation Worksheet; checkboxes 8814 / 4972 / other)",
     "line_type": "calculated", "source_rules": ["R-TAX-01", "R-TAX-02", "R-TAX-03", "R-TAX-05", "R-TAX-06", "R-TAX-07"],
     "sort_order": 60, "notes": "Table semantics below $100,000 — NOT rate formulas (today's code uses brackets everywhere: must change)."},
    {"line_number": "17", "description": "Amount from Schedule 2, line 3", "line_type": "input",
     "source_rules": ["R-CR-01"], "sort_order": 61},
    {"line_number": "18", "description": "Add lines 16 and 17", "line_type": "subtotal", "source_rules": ["R-CR-02"], "sort_order": 62},
    {"line_number": "19", "description": "CTC / ODC from Schedule 8812", "line_type": "calculated",
     "source_rules": ["R-CR-03"], "sort_order": 63, "destination_form": "From SCH_8812 L_14 (live)"},
    {"line_number": "20", "description": "Amount from Schedule 3, line 8", "line_type": "input",
     "source_rules": ["R-CR-04"], "sort_order": 64},
    {"line_number": "21", "description": "Add lines 19 and 20", "line_type": "subtotal", "source_rules": ["R-CR-05"], "sort_order": 65},
    {"line_number": "22", "description": "Subtract line 21 from line 18 (floor 0)", "line_type": "calculated",
     "source_rules": ["R-CR-05"], "sort_order": 66},
    {"line_number": "23", "description": "Other taxes from Schedule 2, line 21", "line_type": "input",
     "source_rules": ["R-CR-06"], "sort_order": 67},
    {"line_number": "24", "description": "Total tax = 22 + 23", "line_type": "total", "source_rules": ["R-CR-06"], "sort_order": 68},

    # ── Payments ──
    {"line_number": "25a", "description": "Withholding — Form(s) W-2", "line_type": "calculated",
     "source_rules": ["R-PAY-01"], "sort_order": 70, "notes": "Computed feeder (W2Income box 2 aggregate)."},
    {"line_number": "25b", "description": "Withholding — Form(s) 1099", "line_type": "input",
     "source_rules": ["R-PAY-02"], "sort_order": 71,
     "notes": "Direct-entry capable; computed from 1099 documents as models land. NEW to seed/compute/field map."},
    {"line_number": "25c", "description": "Withholding — other forms", "line_type": "input",
     "source_rules": ["R-PAY-02"], "sort_order": 72, "notes": "NEW to seed/compute/field map."},
    {"line_number": "25d", "description": "Add lines 25a through 25c", "line_type": "subtotal",
     "source_rules": ["R-PAY-03"], "sort_order": 73},
    {"line_number": "26", "description": "Estimated tax payments + prior-year applied (former-spouse SSN literal)",
     "line_type": "calculated", "source_rules": ["R-PAY-04"], "sort_order": 74,
     "notes": "Computed from the NEW 4-quarter + PY-applied input model."},
    {"line_number": "27a", "description": "Earned income credit (EIC)", "line_type": "input",
     "source_rules": ["R-PAY-05"], "sort_order": 75, "notes": "App key 27 (when seeded). Manual until Topic 7; D_1040_011."},
    {"line_number": "27b", "description": "Clergy filing Schedule SE checkbox", "line_type": "informational", "sort_order": 76},
    {"line_number": "27c", "description": "Do-not-claim-EIC checkbox", "line_type": "informational", "sort_order": 77},
    {"line_number": "28", "description": "Additional child tax credit from Schedule 8812", "line_type": "calculated",
     "source_rules": ["R-PAY-06"], "sort_order": 78, "destination_form": "From SCH_8812 L_27 (live)"},
    {"line_number": "29", "description": "American opportunity credit (Form 8863 line 8)", "line_type": "input",
     "source_rules": ["R-PAY-05"], "sort_order": 79, "notes": "Manual until 8863; D_1040_011."},
    {"line_number": "30", "description": "Refundable adoption credit (Form 8839 line 13) — NEW 2025", "line_type": "input",
     "source_rules": ["R-PAY-05"], "sort_order": 80, "notes": "Manual; D_1040_011."},
    {"line_number": "31", "description": "Amount from Schedule 3, line 15", "line_type": "input",
     "source_rules": ["R-PAY-07"], "sort_order": 81},
    {"line_number": "32", "description": "Total other payments and refundable credits = 27a + 28 + 29 + 30 + 31",
     "line_type": "subtotal", "source_rules": ["R-PAY-07"], "sort_order": 82},
    {"line_number": "33", "description": "Total payments = 25d + 26 + 32", "line_type": "total",
     "source_rules": ["R-PAY-08"], "sort_order": 83},

    # ── Refund / amount owed ──
    {"line_number": "34", "description": "Amount overpaid = max(0, 33 - 24)", "line_type": "calculated",
     "source_rules": ["R-REF-01"], "sort_order": 90},
    {"line_number": "35a", "description": "Amount of line 34 refunded (Form 8888 checkbox)", "line_type": "input",
     "source_rules": ["R-REF-02"], "sort_order": 91, "notes": "Defaults to all of line 34; 35a + 36 must tie (D_1040_012)."},
    {"line_number": "35b", "description": "Routing number", "line_type": "input", "source_rules": ["R-REF-04"], "sort_order": 92},
    {"line_number": "35c", "description": "Account type (checking/savings)", "line_type": "input", "source_rules": ["R-REF-04"], "sort_order": 93},
    {"line_number": "35d", "description": "Account number", "line_type": "input", "source_rules": ["R-REF-04"], "sort_order": 94},
    {"line_number": "36", "description": "Amount of line 34 applied to next year's estimates (IRREVOCABLE)",
     "line_type": "input", "source_rules": ["R-REF-02"], "sort_order": 95},
    {"line_number": "37", "description": "Amount you owe = max(0, 24 - 33) + line 38 penalty", "line_type": "calculated",
     "source_rules": ["R-REF-03"], "sort_order": 96},
    {"line_number": "38", "description": "Estimated tax penalty (manual until Form 2210)", "line_type": "input",
     "source_rules": ["R-REF-03"], "sort_order": 97},
]


# ═══════════════════════════════════════════════════════════════════════════
# DIAGNOSTICS — severities are Ken's calls; v1 grading restates the sprint
# quality rule: anything the software cannot compute correctly is a RED error.
# ═══════════════════════════════════════════════════════════════════════════

FORM_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_1040_001", "title": "BRIDGE — qualified dividends / capital gain present", "severity": "error",
     "condition": "L3a > 0 OR L7a != 0",
     "message": ("Qualified dividends / capital gain distributions present — tax computation not yet "
                 "supported (Qualified Dividends and Capital Gain Tax Worksheet / Schedule D). Prepare manually."),
     "notes": "Sprint Topic 1 DoD bridge. Topic 3 (QDCGT worksheet) replaces this; Topic 8 extends to Schedule D."},
    {"diagnostic_id": "D_1040_002", "title": "Unsupported tax year", "severity": "error",
     "condition": "tax_year not in year-keyed constants (brackets / std deduction / aged-blind / dependent cap)",
     "message": "Tax year {tax_year} is not supported — constants not verified. Tax and standard deduction NOT computed.",
     "notes": "Closes the verified silent gap (compute_tax_from_brackets returns $0 for unknown years today)."},
    {"diagnostic_id": "D_1040_003", "title": "Line 16 add-on tax present (8814/4972/962/ECR/8621)", "severity": "error",
     "condition": "tax_8814_amount != 0 OR tax_4972_amount != 0 OR tax_other_box3_amount != 0",
     "message": "Line 16 includes tax from Form 8814 / 4972 / a box-3 item — not supported. Prepare manually.",
     "notes": "Checkbox literals + amounts stored for render only."},
    {"diagnostic_id": "D_1040_004", "title": "Possible Form 8615 (kiddie tax) exposure", "severity": "error",
     "condition": "taxpayer_claimed_as_dependent AND (L2a + L2b + L3b + L7a) > 2700  [TY2025 threshold]",
     "message": "Filer is claimable as a dependent with unearned income over the Form 8615 threshold — kiddie tax not supported. Prepare manually.",
     "notes": "Conservative proxy (errs toward firing). TY2026 threshold must be verified when published."},
    {"diagnostic_id": "D_1040_005", "title": "Standard deduction forced to zero (12b/12c)", "severity": "warning",
     "condition": "spouse_itemizes_separately OR dual_status_alien",
     "message": "Standard deduction is $0 — spouse itemizes on a separate return / dual-status alien (instructions Exceptions 2-3).",
     "notes": "Computational (R-STD-05) + this notice so the preparer sees WHY 12e is 0."},
    {"diagnostic_id": "D_1040_006", "title": "HOH/QSS without qualifying person", "severity": "warning",
     "condition": "filing_status in {hoh, qss} AND no dependents AND hoh_qss_qualifying_person_name blank",
     "message": "HOH/QSS requires a qualifying person — enter the non-dependent child's name or add the dependent.",
     "notes": "Entry-completeness check, not adjudication."},
    {"diagnostic_id": "D_1040_007", "title": "Dependent SSN format invalid", "severity": "error",
     "condition": "dep_ssn present AND NOT matches NNN-NN-NNNN",
     "message": "Dependent SSN must be in NNN-NN-NNNN format (MeF requirement).",
     "notes": "Per-dependent row. Entry-level validation backstop."},
    {"diagnostic_id": "D_1040_008", "title": "Dependent credit-flag inconsistency", "severity": "warning",
     "condition": "(dep_ctc_flag AND age at Dec 31 >= 17) OR (dep_ctc_flag AND dep_odc_flag)",
     "message": "CTC box checked for a dependent 17 or older at year end (or both CTC and ODC checked) — verify column (7).",
     "notes": "Per-dependent row. Consistency only; SCH_8812 adjudicates."},
    {"diagnostic_id": "D_1040_009", "title": "Dependent date of birth implausible", "severity": "warning",
     "condition": "dep_dob missing, after Dec 31 of tax_year, or > 120 years before tax year end",
     "message": "Dependent date of birth is missing or inconsistent with the tax year — verify.",
     "notes": "Per-dependent row."},
    {"diagnostic_id": "D_1040_010", "title": "MFS spouse aged/blind boxes without required conditions", "severity": "warning",
     "condition": "filing_status == mfs AND (spouse aged/blind box would apply) AND NOT mfs_spouse_boxes_allowed",
     "message": ("MFS may count spouse aged/blind boxes only if the spouse had no income, isn't filing, "
                 "and can't be claimed as a dependent (Pub 501 Table 7 footnote). Boxes not counted."),
     "notes": "Computational gate in R-STD-03 + this notice."},
    {"diagnostic_id": "D_1040_011", "title": "Manually entered amount — engine not built", "severity": "warning",
     "condition": "eic_amount_manual > 0 OR aotc_amount_manual > 0 OR refundable_adoption_credit > 0 OR (itemizing AND itemized_deductions_amount > 0)",
     "message": ("Manually entered EIC / AOTC / adoption credit / itemized deductions — no computation "
                 "engine yet (Topics 7 / post-sprint). Preparer is responsible for the amount."),
     "notes": "Also fires for clergy_se_box with 27a > 0 (clergy EIC path unsupported)."},
    {"diagnostic_id": "D_1040_012", "title": "Refund split doesn't tie", "severity": "error",
     "condition": "L34 > 0 AND (refund_requested + applied_to_next_year) != L34",
     "message": "Lines 35a + 36 must equal line 34. Adjust the refund/applied split.",
     "notes": "Default behavior: 35a = full line 34, 36 = 0."},
    {"diagnostic_id": "D_1040_013", "title": "Deceased taxpayer — age-65 at death rule", "severity": "info",
     "condition": "return marked deceased AND aged box derived from DOB",
     "message": "A decedent counts as 65+ only if 65+ at the time of death (Pub 501) — verify the aged box.",
     "notes": "The spine has no death-date field yet; rides on the header Deceased dates when modeled."},
    {"diagnostic_id": "D_1040_014", "title": "Social security lump-sum election", "severity": "error",
     "condition": "ss_lump_sum_election == True",
     "message": "Lump-sum election method (6c) is not supported — compute the taxable amount manually.",
     "notes": "Stays RED through Topic 5 per sprint scope."},
    {"diagnostic_id": "D_1040_015", "title": "Line 36 election is irrevocable", "severity": "info",
     "condition": "applied_to_next_year > 0",
     "message": "The election to apply the overpayment to next year's estimates cannot be changed later.",
     "notes": "Verbatim from the instructions."},
    {"diagnostic_id": "D_1040_016", "title": "Penalty entered with an overpayment", "severity": "warning",
     "condition": "estimated_tax_penalty > 0 AND L34 > 0",
     "message": "Estimated tax penalty entered on a refund return — verify the offset treatment manually (Form 2210 not built).",
     "notes": "§6654 penalty can apply even when a refund is due."},
]


# ═══════════════════════════════════════════════════════════════════════════
# TEST SCENARIOS
# Expected values computed independently from the TRANSCRIBED published tables
# (several are direct transcriptions of published Tax Table rows). Inputs use
# fact keys; aggregate feeders are injected at line level ("1a", "2b", ...).
# Standard preconditions: supported tax_year, no bridge triggers unless the
# scenario tests them. Expected-output keys are 2025 form line labels.
# ═══════════════════════════════════════════════════════════════════════════

TEST_SCENARIOS: list[dict] = [
    # ── Tax Table (line 16) — transcribed rows ──
    {"scenario_name": "TT-1 — single, TI 25,300 -> tax 2,801 (published row)",
     "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "filing_status": "single", "15": 25300},
     "expected_outputs": {"16": 2801},
     "notes": "Row 25,300-25,350 single column, transcribed from the booklet's sample table."},
    {"scenario_name": "TT-2 — MFJ, TI 25,300 -> tax 2,562 (published row)",
     "scenario_type": "normal", "sort_order": 2,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "15": 25300},
     "expected_outputs": {"16": 2562},
     "notes": "The booklet's own worked example row, MFJ column."},
    {"scenario_name": "TT-3 — HOH, TI 25,300 -> tax 2,699 (published row)",
     "scenario_type": "normal", "sort_order": 3,
     "inputs": {"tax_year": 2025, "filing_status": "hoh", "15": 25300},
     "expected_outputs": {"16": 2699}, "notes": "Same row, HOH column."},
    {"scenario_name": "TT-4 — QSS, TI 25,300 -> tax 2,562 (MFJ column rule)",
     "scenario_type": "normal", "sort_order": 4,
     "inputs": {"tax_year": 2025, "filing_status": "qss", "15": 25300},
     "expected_outputs": {"16": 2562},
     "notes": "Footnote: QSS must use the MFJ column. Catches a QSS->single mis-wire."},
    {"scenario_name": "TT-5 — single, TI 3,020 -> tax 303 (half-up pin)",
     "scenario_type": "edge", "sort_order": 5,
     "inputs": {"tax_year": 2025, "filing_status": "single", "15": 3020},
     "expected_outputs": {"16": 303},
     "notes": "Row 3,000-3,050: midpoint 3,025 x 10% = 302.50 -> published 303. Pins ROUND HALF UP."},
    {"scenario_name": "TT-6 — single, TI 3,560 -> tax 358 (half-up pin #2)",
     "scenario_type": "edge", "sort_order": 6,
     "inputs": {"tax_year": 2025, "filing_status": "single", "15": 3560},
     "expected_outputs": {"16": 358},
     "notes": "Row 3,550-3,600: midpoint 3,575 x 10% = 357.50 -> published 358."},
    {"scenario_name": "TT-7 — last table row (TI 99,990): single 16,909 / MFJ 11,823 / HOH 15,170",
     "scenario_type": "edge", "sort_order": 7,
     "inputs": {"tax_year": 2025, "15": 99990,
                "cases": {"single": 16909, "mfj": 11823, "mfs": 16909, "hoh": 15170}},
     "expected_outputs": {"16_by_status": {"single": 16909, "mfj": 11823, "mfs": 16909, "hoh": 15170}},
     "notes": "Row 99,950-100,000 transcribed for all four columns; midpoint 99,975 cross-checks to the dollar."},
    {"scenario_name": "TT-8 — single, TI 40 -> tax 4 ($25-band micro row)",
     "scenario_type": "edge", "sort_order": 8,
     "inputs": {"tax_year": 2025, "filing_status": "single", "15": 40},
     "expected_outputs": {"16": 4},
     "notes": "Row 25-50: midpoint 37.50 x 10% = 3.75 -> 4. Pins the sub-$3,000 $25 band structure."},

    # ── Tax Computation Worksheet (TI >= 100,000) ──
    {"scenario_name": "TCW-1 — single, TI 100,000 -> tax 16,914.00 (threshold row)",
     "scenario_type": "edge", "sort_order": 9,
     "inputs": {"tax_year": 2025, "filing_status": "single", "15": 100000},
     "expected_outputs": {"16": 16914},
     "notes": "Exactly at the cutover: TCW Section A row 1 (22% minus 5,086) = cumulative brackets. NOT a table lookup."},
    {"scenario_name": "TCW-2 — MFJ, TI 250,000 -> tax 45,694.00",
     "scenario_type": "normal", "sort_order": 10,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "15": 250000},
     "expected_outputs": {"16": 45694},
     "notes": "Section B row 2 (24% minus 14,306) = bracket math: 2,385 + 8,772 + 24,145 + 10,392."},

    # ── TY2026 (convention over RP 2025-32 schedules — re-verify vs published 2026 table) ──
    {"scenario_name": "T26-1 — TY2026 single, TI 50,000 -> tax 5,755 (table convention)",
     "scenario_type": "normal", "sort_order": 11,
     "inputs": {"tax_year": 2026, "filing_status": "single", "15": 50000},
     "expected_outputs": {"16": 5755},
     "notes": ("Row 50,000-50,050 midpoint 50,025: 1,240 + 12% x 37,625 = 5,755.00. CAVEAT: 2026 Tax "
               "Table unpublished — re-verify against the printed row when the IRS releases it.")},
    {"scenario_name": "T26-2 — TY2026 single, TI 150,000 -> tax 28,598 (rate schedule)",
     "scenario_type": "normal", "sort_order": 12,
     "inputs": {"tax_year": 2026, "filing_status": "single", "15": 150000},
     "expected_outputs": {"16": 28598},
     "notes": "RP 2025-32 §4.01: 1,240 + 4,560 + 12,166 + 24% x 44,300 = 28,598.00."},

    # ── Standard deduction (12e) ──
    {"scenario_name": "SD-1 — single, under 65, not blind -> 15,750",
     "scenario_type": "normal", "sort_order": 20,
     "inputs": {"tax_year": 2025, "filing_status": "single", "taxpayer_dob": "1980-05-15"},
     "expected_outputs": {"12e": 15750}, "notes": "Table 6 base (OBBBA §70102)."},
    {"scenario_name": "SD-2 — MFJ, both born 1955, taxpayer blind (3 boxes) -> 36,300",
     "scenario_type": "normal", "sort_order": 21,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "taxpayer_dob": "1955-03-10",
                "spouse_dob": "1955-08-22", "taxpayer_blind": True},
     "expected_outputs": {"12e": 36300},
     "notes": "Table 7 verbatim: MFJ 3 boxes = 36,300 (31,500 + 3 x 1,600)."},
    {"scenario_name": "SD-3 — MFS, taxpayer 65+ (1 box) -> 17,350 (married rate pin)",
     "scenario_type": "edge", "sort_order": 22,
     "inputs": {"tax_year": 2025, "filing_status": "mfs", "taxpayer_dob": "1955-03-10",
                "spouse_itemizes_separately": False},
     "expected_outputs": {"12e": 17350},
     "notes": "Table 7: MFS 1 box = 17,350 — the MARRIED $1,600 additional despite the single-size base. Catches a $2,000 mis-wire."},
    {"scenario_name": "SD-4 — HOH, blind -> 25,625",
     "scenario_type": "normal", "sort_order": 23,
     "inputs": {"tax_year": 2025, "filing_status": "hoh", "taxpayer_dob": "1980-01-01", "taxpayer_blind": True},
     "expected_outputs": {"12e": 25625}, "notes": "Table 7: HOH 1 box (23,625 + 2,000)."},
    {"scenario_name": "SD-5 — BOUNDARY: single DOB 1961-01-01 -> aged box -> 17,750",
     "scenario_type": "edge", "sort_order": 24,
     "inputs": {"tax_year": 2025, "filing_status": "single", "taxpayer_dob": "1961-01-01"},
     "expected_outputs": {"12e": 17750},
     "notes": "Born BEFORE Jan 2, 1961 -> qualifies. Pair with SD-6 (same convention as SCH_1A S5/S6)."},
    {"scenario_name": "SD-6 — BOUNDARY: single DOB 1961-01-02 -> no aged box -> 15,750",
     "scenario_type": "edge", "sort_order": 25,
     "inputs": {"tax_year": 2025, "filing_status": "single", "taxpayer_dob": "1961-01-02"},
     "expected_outputs": {"12e": 15750},
     "notes": "NOT born before Jan 2, 1961 -> base only."},
    {"scenario_name": "SD-DEP-1 — dependent filer, earned 800 -> 1,350 (floor)",
     "scenario_type": "normal", "sort_order": 26,
     "inputs": {"tax_year": 2025, "filing_status": "single", "taxpayer_dob": "2008-04-01",
                "taxpayer_claimed_as_dependent": True, "dependent_filer_earned_income": 800},
     "expected_outputs": {"12e": 1350},
     "notes": "Table 8: max(1,350, 800 + 450 = 1,250) = 1,350."},
    {"scenario_name": "SD-DEP-2 — dependent filer, earned 5,000 -> 5,450",
     "scenario_type": "normal", "sort_order": 27,
     "inputs": {"tax_year": 2025, "filing_status": "single", "taxpayer_dob": "2008-04-01",
                "taxpayer_claimed_as_dependent": True, "dependent_filer_earned_income": 5000},
     "expected_outputs": {"12e": 5450}, "notes": "Table 8: max(1,350, 5,450) = 5,450 < base."},
    {"scenario_name": "SD-DEP-3 — dependent filer, earned 20,000 -> capped at 15,750",
     "scenario_type": "edge", "sort_order": 28,
     "inputs": {"tax_year": 2025, "filing_status": "single", "taxpayer_dob": "2008-04-01",
                "taxpayer_claimed_as_dependent": True, "dependent_filer_earned_income": 20000},
     "expected_outputs": {"12e": 15750}, "notes": "Table 8 line 7a: smaller of (20,450) or base (15,750)."},
    {"scenario_name": "SD-DEP-4 — dependent filer, earned 2,000, blind -> 4,450",
     "scenario_type": "edge", "sort_order": 29,
     "inputs": {"tax_year": 2025, "filing_status": "single", "taxpayer_dob": "2008-04-01",
                "taxpayer_claimed_as_dependent": True, "dependent_filer_earned_income": 2000,
                "taxpayer_blind": True},
     "expected_outputs": {"12e": 4450},
     "notes": "Table 8: min(max(1,350, 2,450), 15,750) = 2,450, THEN + 2,000 blind (7b after the cap)."},
    {"scenario_name": "SD-26-1 — TY2026 single 65+ -> 18,150",
     "scenario_type": "normal", "sort_order": 30,
     "inputs": {"tax_year": 2026, "filing_status": "single", "taxpayer_dob": "1955-06-15"},
     "expected_outputs": {"12e": 18150},
     "notes": "RP 2025-32 §4.14: 16,100 + 2,050. TY2026 aged cutoff is 1962-01-02."},
    {"scenario_name": "SD-26-2 — TY2026 MFJ both 65+ -> 35,500",
     "scenario_type": "normal", "sort_order": 31,
     "inputs": {"tax_year": 2026, "filing_status": "mfj", "taxpayer_dob": "1950-01-01", "spouse_dob": "1952-01-01"},
     "expected_outputs": {"12e": 35500}, "notes": "32,200 + 2 x 1,650."},

    # ── End-to-end spine arithmetic ──
    {"scenario_name": "E2E-1 — single W-2 only: wages 60,000 / W-H 7,000 -> refund 1,925",
     "scenario_type": "normal", "sort_order": 40,
     "inputs": {"tax_year": 2025, "filing_status": "single", "taxpayer_dob": "1985-07-04",
                "1a": 60000, "25a": 7000},
     "expected_outputs": {"1z": 60000, "9": 60000, "11a": 60000, "12e": 15750, "14": 15750,
                          "15": 44250, "16": 5075, "18": 5075, "22": 5075, "24": 5075,
                          "25d": 7000, "33": 7000, "34": 1925, "35a": 1925, "37": 0},
     "notes": "Line 16: row 44,250-44,300 midpoint 44,275 -> 1,192.50 + 3,882.00 = 5,074.50 -> 5,075 (half-up)."},
    {"scenario_name": "E2E-2 — MFJ + estimates: wages 50,000, interest 1,000, est 4x1,000 + 500 PY, W-H 1,200; split refund",
     "scenario_type": "normal", "sort_order": 41,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "taxpayer_dob": "1985-01-01", "spouse_dob": "1986-01-01",
                "1a": 50000, "2b": 1000, "25a": 1200,
                "est_payment_q1": 1000, "est_payment_q2": 1000, "est_payment_q3": 1000, "est_payment_q4": 1000,
                "py_overpayment_applied": 500, "refund_requested": 3000, "applied_to_next_year": 747},
     "expected_outputs": {"9": 51000, "11a": 51000, "12e": 31500, "15": 19500, "16": 1953,
                          "24": 1953, "25d": 1200, "26": 4500, "33": 5700, "34": 3747,
                          "35a": 3000, "36": 747, "37": 0},
     "notes": "Line 16: row 19,500-19,550 midpoint 19,525 x 10% = 1,952.50 -> 1,953. 35a + 36 = 34 ties."},
    {"scenario_name": "E2E-3 — single owes + penalty: wages 80,000, W-H 5,000, penalty 50 -> owe 4,105",
     "scenario_type": "normal", "sort_order": 42,
     "inputs": {"tax_year": 2025, "filing_status": "single", "taxpayer_dob": "1990-09-09",
                "1a": 80000, "25a": 5000, "estimated_tax_penalty": 50},
     "expected_outputs": {"15": 64250, "16": 9055, "24": 9055, "33": 5000, "34": 0,
                          "37": 4105, "38": 50},
     "notes": ("Line 16: midpoint 64,275 -> 1,192.50 + 4,386.00 + 3,476.00 = 9,054.50 -> 9,055. "
               "Line 37 = 4,055 + 50 penalty (instructions: include line 38 in line 37).")},

    # ── Diagnostics fire ──
    {"scenario_name": "DG-1 — bridge: qualified dividends present -> D_1040_001, no tax computed",
     "scenario_type": "failure", "sort_order": 50,
     "inputs": {"tax_year": 2025, "filing_status": "single", "taxpayer_dob": "1985-01-01",
                "1a": 30000, "3a": 500, "3b": 500},
     "expected_outputs": {"D_1040_001_fires": True, "16_not_computed": True},
     "notes": "The spine must never compute table-only tax on a return with line 3a amounts."},
    {"scenario_name": "DG-2 — unsupported year 2024 -> D_1040_002, no silent $0",
     "scenario_type": "failure", "sort_order": 51,
     "inputs": {"tax_year": 2024, "filing_status": "single", "taxpayer_dob": "1985-01-01", "1a": 50000},
     "expected_outputs": {"D_1040_002_fires": True, "16_not_computed": True},
     "notes": "Today's code would emit $0 tax for 2024 — the diagnostic replaces the silent gap."},
    {"scenario_name": "DG-3 — dependent SSN malformed -> D_1040_007",
     "scenario_type": "failure", "sort_order": 52,
     "inputs": {"tax_year": 2025, "filing_status": "hoh", "taxpayer_dob": "1985-01-01",
                "dependents": [{"dep_first_name": "A", "dep_last_name": "B", "dep_ssn": "123-45-678",
                                "dep_relationship": "child", "dep_dob": "2015-05-01", "dep_ctc_flag": True}]},
     "expected_outputs": {"D_1040_007_fires": True},
     "notes": "8-digit SSN fails the NNN-NN-NNNN gate."},
    {"scenario_name": "DG-4 — CTC box on a 18-year-old -> D_1040_008",
     "scenario_type": "failure", "sort_order": 53,
     "inputs": {"tax_year": 2025, "filing_status": "single", "taxpayer_dob": "1980-01-01",
                "dependents": [{"dep_first_name": "C", "dep_last_name": "D", "dep_ssn": "400-00-1234",
                                "dep_relationship": "child", "dep_dob": "2007-06-01", "dep_ctc_flag": True}]},
     "expected_outputs": {"D_1040_008_fires": True},
     "notes": "Age 18 at Dec 31, 2025 with the CTC box checked — consistency warning."},
    {"scenario_name": "DG-5 — MFS spouse itemizes -> 12e = 0 + D_1040_005",
     "scenario_type": "edge", "sort_order": 54,
     "inputs": {"tax_year": 2025, "filing_status": "mfs", "taxpayer_dob": "1955-01-01",
                "spouse_itemizes_separately": True},
     "expected_outputs": {"12e": 0, "D_1040_005_fires": True},
     "notes": "Zero even though the taxpayer is 65+ (Exception 2)."},
    {"scenario_name": "DG-6 — refund split mismatch -> D_1040_012",
     "scenario_type": "failure", "sort_order": 55,
     "inputs": {"tax_year": 2025, "filing_status": "single", "taxpayer_dob": "1985-01-01",
                "1a": 30000, "25a": 5000, "refund_requested": 1000, "applied_to_next_year": 0},
     "expected_outputs": {"D_1040_012_fires": True},
     "notes": "34 > 0 but 35a + 36 != 34."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-SPINE-01", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "L1z sums 1a through 1h (1i excluded)",
     "description": "Validates R-INC-02. Bug it catches: 1z = 1a only (today's code) or combat-pay memo leaking into wages.",
     "definition": {"kind": "sum_check", "form": "1040", "output": "L1z",
                    "sum_of": ["L1a", "L1b", "L1c", "L1d", "L1e", "L1f", "L1g", "L1h"], "excludes": ["L1i"]},
     "sort_order": 1},
    {"assertion_id": "FA-1040-SPINE-02", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "L9 sums the eight form addends",
     "description": "Validates R-INC-04. Bug it catches: today's 1z + 2b + 8 shortcut dropping 3b/4b/5b/6b/7a.",
     "definition": {"kind": "sum_check", "form": "1040", "output": "L9",
                    "sum_of": ["L1z", "L2b", "L3b", "L4b", "L5b", "L6b", "L7a", "L8"]},
     "sort_order": 2},
    {"assertion_id": "FA-1040-SPINE-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "AGI = 9 - 10 with NO zero floor",
     "description": "Validates R-INC-05. Bug it catches: flooring AGI at 0 (breaks NOL-year returns).",
     "definition": {"kind": "formula_check", "form": "1040", "formula": "L11a == L9 - L10", "allow_negative": True},
     "sort_order": 3},
    {"assertion_id": "FA-1040-SPINE-04", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "Standard deduction constants per year (base / aged-blind / dependent)",
     "description": ("Validates R-STD-01/03/04 constants. TY2025: 15750/31500/23625; +1600 married / +2000 "
                     "unmarried; dep 1350/450. TY2026: 16100/32200/24150; +1650/+2050; dep 1350/450. "
                     "Bug it catches: pre-OBBBA RP 2024-40 projections resurfacing, or the MFS additional "
                     "wired to the unmarried rate."),
     "definition": {"kind": "constants_check", "form": "1040",
                    "constants": {
                        "2025": {"base": {"single": 15750, "mfs": 15750, "mfj": 31500, "qss": 31500, "hoh": 23625},
                                 "addl_married": 1600, "addl_unmarried": 2000,
                                 "dep_floor": 1350, "dep_earned_addl": 450, "aged_cutoff": "1961-01-02"},
                        "2026": {"base": {"single": 16100, "mfs": 16100, "mfj": 32200, "qss": 32200, "hoh": 24150},
                                 "addl_married": 1650, "addl_unmarried": 2050,
                                 "dep_floor": 1350, "dep_earned_addl": 450, "aged_cutoff": "1962-01-02"}}},
     "sort_order": 4},
    {"assertion_id": "FA-1040-SPINE-05", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Deduction chain: L14 = 12e + 13a + 13b; L15 = max(0, 11b - 14)",
     "description": "Validates the deduction chain incl. the SCH_1A 13b feeder. Bug it catches: 13b dropped from 14, or 15 missing the floor.",
     "definition": {"kind": "formula_check", "form": "1040",
                    "formula": "L14 == L12e + L13a + L13b AND L15 == max(0, L11b - L14)"},
     "sort_order": 5},
    {"assertion_id": "FA-1040-SPINE-06", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Line 16 method threshold at exactly $100,000",
     "description": ("Validates R-TAX-01. TI 99,999.49-> table; TI 100,000 -> TCW. Bug it catches: rate "
                     "schedules used below the threshold (today's behavior) or an off-by-one cutover."),
     "definition": {"kind": "threshold_check", "form": "1040", "line": "L16",
                    "below": "tax_table_lookup", "at_or_above": "tax_computation_worksheet", "threshold": 100000},
     "sort_order": 6},
    {"assertion_id": "FA-1040-SPINE-07", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Tax Table = rate schedule at row MIDPOINT, rounded HALF-UP",
     "description": ("Validates R-TAX-02 with published pins: TI 3,020 -> 303; TI 3,560 -> 358; TI 99,990 "
                     "single -> 16,909. Bug it catches: taxing the row floor, truncating, or banker's rounding."),
     "definition": {"kind": "table_convention_check", "form": "1040", "line": "L16",
                    "bands": [[0, 5, 5], [5, 25, 10], [25, 3000, 25], [3000, 100000, 50]],
                    "value_at": "midpoint", "rounding": "half_up_to_dollar",
                    "pins": [{"ti": 3020, "status": "single", "year": 2025, "tax": 303},
                             {"ti": 3560, "status": "single", "year": 2025, "tax": 358},
                             {"ti": 99990, "status": "single", "year": 2025, "tax": 16909},
                             {"ti": 99990, "status": "hoh", "year": 2025, "tax": 15170}]},
     "sort_order": 7},
    {"assertion_id": "FA-1040-SPINE-08", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "QSS resolves to the MFJ column/brackets everywhere",
     "description": "Validates R-FS-02. Bug it catches: QSS falling through to single (or erroring).",
     "definition": {"kind": "column_check", "form": "1040", "status": "qss", "resolves_to": "mfj",
                    "applies_to": ["tax_table_column", "rate_brackets", "std_deduction_base"]},
     "sort_order": 8},
    {"assertion_id": "FA-1040-SPINE-09", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "Credits chain: 18 = 16 + 17; 21 = 19 + 20; 22 = max(0, 18 - 21); 24 = 22 + 23",
     "description": "Validates R-CR-02/05/06 incl. the line 22 floor (nonrefundable credits can't go negative).",
     "definition": {"kind": "formula_check", "form": "1040",
                    "formula": "L18 == L16 + L17 AND L21 == L19 + L20 AND L22 == max(0, L18 - L21) AND L24 == L22 + L23"},
     "sort_order": 9},
    {"assertion_id": "FA-1040-SPINE-10", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "L25d sums all three withholding sources",
     "description": "Validates R-PAY-03. Bug it catches: 25d = 25a only (today's code) — 1099/other withholding dropped.",
     "definition": {"kind": "sum_check", "form": "1040", "output": "L25d", "sum_of": ["L25a", "L25b", "L25c"]},
     "sort_order": 10},
    {"assertion_id": "FA-1040-SPINE-11", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "L26 = four quarters + prior-year applied",
     "description": "Validates R-PAY-04 (new estimated-payments input model).",
     "definition": {"kind": "sum_check", "form": "1040", "output": "L26",
                    "sum_of": ["est_payment_q1", "est_payment_q2", "est_payment_q3", "est_payment_q4",
                               "py_overpayment_applied"]},
     "sort_order": 11},
    {"assertion_id": "FA-1040-SPINE-12", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "Payments chain: 32 = 27a + 28 + 29 + 30 + 31; 33 = 25d + 26 + 32",
     "description": "Validates R-PAY-07/08 incl. the NEW line 30. Bug it catches: today's 33 = 25d + 28 shortcut.",
     "definition": {"kind": "formula_check", "form": "1040",
                    "formula": "L32 == L27a + L28 + L29 + L30 + L31 AND L33 == L25d + L26 + L32"},
     "sort_order": 12},
    {"assertion_id": "FA-1040-SPINE-13", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Refund/owe complementarity; L37 includes the L38 penalty",
     "description": ("Validates R-REF-01/03. At most one of 34/37 is positive; when owing, "
                     "L37 == (L24 - L33) + L38."),
     "definition": {"kind": "formula_check", "form": "1040",
                    "formula": "NOT (L34 > 0 AND L37 > 0) AND (L24 > L33 implies L37 == L24 - L33 + L38)"},
     "sort_order": 13},
    {"assertion_id": "FA-1040-SPINE-14", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "Refund split ties: 35a + 36 == 34",
     "description": "Validates R-REF-02 / D_1040_012.",
     "definition": {"kind": "sum_check", "form": "1040", "output": "L34", "sum_of": ["L35a", "L36"],
                    "when": "L34 > 0"},
     "sort_order": 14},
    {"assertion_id": "FA-1040-SPINE-15", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "BRIDGE gate: 3a/7a present -> table-only tax NOT computed",
     "description": ("Validates R-TAX-07 / D_1040_001. Bug it catches: the spine quietly taxing "
                     "preferential-rate income at ordinary rates (the exact failure the sprint forbids)."),
     "definition": {"kind": "gating_check", "form": "1040",
                    "trigger": "L3a > 0 OR L7a != 0", "blocked_output": "L16",
                    "diagnostic": "D_1040_001", "replaced_by": "Topic 3 QDCGT worksheet"},
     "sort_order": 15},
    {"assertion_id": "FA-1040-SPINE-16", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Unsupported year is a hard stop, never silent $0",
     "description": "Validates R-TAX-05 / D_1040_002 (the audited silent gap).",
     "definition": {"kind": "gating_check", "form": "1040",
                    "trigger": "tax_year not in constants", "blocked_output": "L16",
                    "diagnostic": "D_1040_002"},
     "sort_order": 16},
]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY FORM LINKS  (source_code, link_type)
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_FORM_LINKS: list[tuple[str, str]] = [
    ("IRS_2025_1040_FORM", "governs"),
    ("IRS_2025_1040_TT", "governs"),
    ("IRS_2025_1040_INSTR", "governs"),
    ("PUB_501_2025", "governs"),
    ("RP_2024_40", "governs"),
    ("RP_2025_32", "governs"),
    ("PL_119_21_70102", "governs"),
    ("IRC_1", "governs"),
    ("IRC_3", "governs"),
    ("IRC_63", "governs"),
    ("IRC_2", "informs"),
    ("IRC_7703", "informs"),
    ("IRC_151", "informs"),
    ("IRC_152", "informs"),
    ("IRC_6654", "informs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# Command
# ═══════════════════════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = (
        "Load the Form 1040 spine spec into Rule Studio (updates the Session-14 stub). "
        "Refuses to seed until Ken sets READY_TO_SEED=True."
    )

    REQUIRED_CONTENT_LISTS: tuple[tuple[str, list], ...] = (
        ("AUTHORITY_SOURCES",     AUTHORITY_SOURCES),
        ("FORM_RULES",            FORM_RULES),
        ("FORM_LINES",            FORM_LINES),
        ("RULE_AUTHORITY_LINKS",  RULE_AUTHORITY_LINKS),
    )

    # Session-14 stub artifacts superseded by this spec. Deleted (with stdout
    # notes) so the export doesn't carry duplicate semantics: R001/R002 are
    # re-specified as R-CR-03 / R-PAY-06; line "11" becomes 11a/11b; fact
    # line_11_agi becomes the agi calculated fact.
    STUB_RULE_IDS = ("R001", "R002")
    STUB_FACT_KEYS = ("line_11_agi",)
    STUB_LINE_NUMBERS = ("11",)

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()

        self.stdout.write(self.style.MIGRATE_HEADING(f"\nLoad {FORM_NUMBER} spine spec\n"))

        self._load_topics()
        sources = self._load_sources()
        self._load_new_excerpts_on_existing(sources)
        form = self._upsert_form()
        self._retire_stub_artifacts(form)
        self._upsert_facts(form)
        rules = self._upsert_rules(form)
        self._upsert_authority_links(rules, sources)
        self._upsert_lines(form)
        self._upsert_diagnostics(form)
        self._upsert_tests(form)
        self._upsert_form_links(sources)
        self._load_flow_assertions()
        self._report_totals()

    # ─────────────────────────────────────────────────────────────────────────
    # Safety guard
    # ─────────────────────────────────────────────────────────────────────────

    def _guard_against_hollow_seed(self):
        """Refuse to write anything until Ken has reviewed AND flipped READY_TO_SEED."""
        empty = [name for name, lst in self.REQUIRED_CONTENT_LISTS if not lst]
        if "[TODO" in FORM_TITLE:
            empty.append("FORM_TITLE (still a [TODO] placeholder)")

        if not READY_TO_SEED or empty:
            checklist = "\n  ".join(f"- {name}" for name, lst in self.REQUIRED_CONTENT_LISTS)
            still_empty = "\n  ".join(f"- {n}" for n in empty) or "(all populated)"
            raise CommandError(
                "\n"
                f"REFUSING TO SEED {FORM_NUMBER}: not cleared to seed.\n"
                "\n"
                "Content is authored, but seeding is gated until Ken reviews the packet\n"
                "(constants per year, Tax Table convention, diagnostics severities, the\n"
                "stub retirement) and flips the sentinel.\n"
                "\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True to proceed)\n"
                "\n"
                "Content checklist (required lists):\n"
                f"  {checklist}\n"
                "\n"
                "Currently empty / placeholder:\n"
                f"  {still_empty}\n"
                "\n"
                "To proceed: review the module-level data lists, then set READY_TO_SEED\n"
                "= True. Idempotent via update_or_create — safe to re-run after edits."
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Stub retirement (Session-14 artifacts superseded by the spine)
    # ─────────────────────────────────────────────────────────────────────────

    def _retire_stub_artifacts(self, form):
        n_rules, _ = FormRule.objects.filter(tax_form=form, rule_id__in=self.STUB_RULE_IDS).delete()
        n_facts, _ = FormFact.objects.filter(tax_form=form, fact_key__in=self.STUB_FACT_KEYS).delete()
        n_lines, _ = FormLine.objects.filter(tax_form=form, line_number__in=self.STUB_LINE_NUMBERS).delete()
        if n_rules or n_facts or n_lines:
            self.stdout.write(self.style.WARNING(
                f"  retired stub artifacts: rules+links={n_rules}, facts={n_facts}, lines={n_lines} "
                "(R001/R002 -> R-CR-03/R-PAY-06; line_11_agi -> agi; line 11 -> 11a/11b)"
            ))

    # ─────────────────────────────────────────────────────────────────────────
    # Topics / sources (mirror load_sch_1a.py exactly)
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
    # Form helpers (mirror load_sch_1a.py exactly)
    # ─────────────────────────────────────────────────────────────────────────

    def _upsert_form(self) -> TaxForm:
        form, created = TaxForm.objects.update_or_create(
            form_number=FORM_NUMBER,
            jurisdiction=FORM_JURISDICTION,
            tax_year=FORM_TAX_YEAR,
            version=FORM_VERSION,
            defaults={
                "form_title": FORM_TITLE,
                "entity_types": FORM_ENTITY_TYPES,
                "status": FORM_STATUS,
                "notes": FORM_NOTES,
            },
        )
        self.stdout.write(f"{'Created' if created else 'Updated'} {FORM_NUMBER}")
        return form

    def _upsert_facts(self, form):
        for f in FORM_FACTS:
            f = dict(f)
            FormFact.objects.update_or_create(
                tax_form=form, fact_key=f.pop("fact_key"), defaults=f,
            )
        self.stdout.write(f"  {len(FORM_FACTS)} facts")

    def _upsert_rules(self, form) -> dict[str, FormRule]:
        created = {}
        for r in FORM_RULES:
            r = dict(r)
            rule, _ = FormRule.objects.update_or_create(
                tax_form=form, rule_id=r.pop("rule_id"), defaults=r,
            )
            created[rule.rule_id] = rule
        self.stdout.write(f"  {len(created)} rules")
        return created

    def _upsert_authority_links(self, rules, sources):
        ct = 0
        for rule_id, source_code, level, note in RULE_AUTHORITY_LINKS:
            rule, source = rules.get(rule_id), sources.get(source_code)
            if rule and source:
                RuleAuthorityLink.objects.get_or_create(
                    form_rule=rule, authority_source=source,
                    defaults={"support_level": level, "relevance_note": note},
                )
                ct += 1
        self.stdout.write(f"  {ct} authority links")

    def _upsert_lines(self, form):
        for ln in FORM_LINES:
            ln = dict(ln)
            FormLine.objects.update_or_create(
                tax_form=form, line_number=ln.pop("line_number"), defaults=ln,
            )
        self.stdout.write(f"  {len(FORM_LINES)} lines")

    def _upsert_diagnostics(self, form):
        for d in FORM_DIAGNOSTICS:
            d = dict(d)
            FormDiagnostic.objects.update_or_create(
                tax_form=form, diagnostic_id=d.pop("diagnostic_id"), defaults=d,
            )
        self.stdout.write(f"  {len(FORM_DIAGNOSTICS)} diagnostics")

    def _upsert_tests(self, form):
        for t in TEST_SCENARIOS:
            t = dict(t)
            TestScenario.objects.update_or_create(
                tax_form=form, scenario_name=t.pop("scenario_name"), defaults=t,
            )
        self.stdout.write(f"  {len(TEST_SCENARIOS)} test scenarios")

    def _upsert_form_links(self, sources):
        for source_code, link_type in AUTHORITY_FORM_LINKS:
            source = sources.get(source_code) or AuthoritySource.objects.filter(
                source_code=source_code,
            ).first()
            if source:
                AuthorityFormLink.objects.get_or_create(
                    authority_source=source, form_code=FORM_NUMBER, link_type=link_type,
                    defaults={"note": f"{source_code} -> {FORM_NUMBER}"},
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
        self.stdout.write(f"DATABASE TOTALS (after load_{FORM_NUMBER.lower()}_spine)")
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

        all_rules = FormRule.objects.filter(tax_form__form_number=FORM_NUMBER)
        uncited = [r for r in all_rules if not r.authority_links.exists()]
        if uncited:
            self.stdout.write(self.style.WARNING(
                f"\n{FORM_NUMBER} rules with ZERO authority links: {len(uncited)}"
            ))
            for r in uncited[:20]:
                self.stdout.write(_safe(f"  {r.rule_id}: {r.title}"))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"\nAll {FORM_NUMBER} rules have authority links."
            ))
