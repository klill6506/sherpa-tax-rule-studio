"""Load the Interest, Dividends & QDCGT specs — Sprint Topic 3.

Creates TWO TaxForms: 1040_INTDIV (1099-INT/1099-DIV document aggregation to
Form 1040 lines 2a/2b/3a/3b/7a + the Qualified Dividends and Capital Gain Tax
Worksheet for line 16) and SCH_B (Schedule B payer listings + Part III).

Session 2026-06-11: authored by transcription from primary sources fetched and
layout-extracted the same day (pymupdf positional dumps in tts-tax-app
server/.scratch/):

  - 2025 Schedule B (f1040sb.pdf, created 4/23/25) — single page, transcribed.
    SHA256 dd1ec371... (manifest-recorded download).
  - 2025 Instructions for Schedule B (i1040sb, Apr 23, 2025) — all 3 pages
    transcribed (nominee/accrued/OID/ABP adjustment conventions, seller-
    financed rules, Part III definitions, $10,000 FBAR threshold).
  - 2025 i1040gi pages 25-26 (lines 2a/2b/3a/3b), 31+33 (line 7a/7b incl.
    Exception 1), 37-38 (the QDCGT worksheet verbatim, all 25 lines, with
    the TY2025 breakpoints printed on the face).
  - Form 1099-INT (Rev. 1-2024, current for TY2025) — box structure 1-17 +
    FATCA box, matches the existing InterestIncome model.
  - Form 1099-DIV (Rev. 1-2024, current for TY2025) — boxes 1a-16 transcribed.
  - RP 2024-40 §2.03 (TY2025 0%/15% breakpoints) and RP 2025-32 §4.03
    (TY2026) — both extracted verbatim; TY2025 also corroborated by the
    worksheet face (lines 6/13).

TOPIC SCOPE (SPRINT_SCOPE.md Topic 3 DoD): 1099-INT document input
aggregating to 2a/2b; 1099-DIV document input (all boxes) aggregating to
3a/3b; line 7 checkbox path (capital gain distributions direct to 1040
line 7a + the line 7b "Schedule D not required" box); full QDCGT worksheet
(replaces the spine's R-TAX-07 bridge gate); Schedule B render from the
documents + Part III; flow assertions on 2a/2b, 3a/3b, line 7, line 16.

SPINE SUPERSESSION (build leg, flagged for Ken):
  - R-TAX-07 / D_1040_001 (the QDCGT bridge RED) NARROWS: the worksheet now
    computes line 16 for the supported paths; D_INTDIV_001/002/003/004 carry
    the still-unsupported paths (Sch D required, Form 8814, Form 2555 FEIE
    worksheet). The spine diagnostic retires at the build leg (loader edit +
    re-seed, PM #11 pattern) once Ken approves.
  - Spine R-PAY-02 (line 25b = 1099 withholding): EXTENDS to include 1099-DIV
    box 4 alongside the existing 1099-INT box 4.
  - 1040 lines 2a/2b/3a/3b become COMPUTED feeders (YELLOW) from the
    documents; every one keeps the preparer override escape hatch.

TY2026 NOTE (target-year policy): the ONLY year-keyed constants here are the
QDCGT 0%/15% breakpoints — both years transcribed from their rev procs in
this file. The 2026 form faces (Sch B, 1040) must be re-verified on release.
WS22/WS24 tax-method routing inherits the spine's verified Tax Table /
TCW semantics including the accepted derived-2026-table interim.

JUDGMENT ITEMS FOR KEN'S REVIEW WALK (each also flagged in its rule):
  1. ABP default: per-document net = box 1 + box 3 + box 10 - box 11 - box 12
     (payer-reported premium amortization subtracted by default; §171
     election subtlety — Sch B prints the "ABP Adjustment" row).
  2. Tax-exempt netting floors at 0 PER DOCUMENT: max(0, box 8 - box 13)
     ("the EXCESS of tax-exempt interest over the premium" — i1040sb).
  3. Box 10 market discount included in 2b when reported (box only populated
     under the §1278(b) current-inclusion election per 1099-INT instructions).
  4. WS18/WS21 rounding: ROUND HALF UP to whole dollars (matches the Tax
     Table half-up convention; scenario Q9 pins 247.50 -> 248).
  5. The line-7b checkbox path is gated on a preparer ASSERTION fact
     (capital_gain_distributions_only) = Exception 1 condition (1) ("you have
     no capital losses / no other capital gains") — software cannot know
     about unsold/unentered capital activity.
  6. Qualified dividends (3a) compute as sum(box 1b) with preparer OVERRIDE as
     the holding-period-exception escape hatch (61-day rule etc. is preparer
     judgment per i1040gi).

Safety guard
------------
`READY_TO_SEED = False`. Content is authored; Ken reviews the packet, flips
the sentinel, and seeds. Until then the command refuses to write to the DB.

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
# SAFETY GUARD — flipped to True 2026-06-11 on Ken's in-session approval of
# the review packet (the six judgment items incl. WS18/WS21 half-up rounding,
# both years' breakpoint tables, the aggregation rosters, diagnostics
# severities, the 21 scenarios, the D_1040_001-narrowing plan).
# ═══════════════════════════════════════════════════════════════════════════

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
    ("interest_dividends", "Interest & dividend income — 1099-INT/DIV aggregation, Schedule B"),
    ("qdcgt_worksheet", "Qualified Dividends and Capital Gain Tax Worksheet (1040 line 16)"),
]

# Existing sources to REUSE (looked up, not modified).
EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_1040_FORM",   # lines 2a/2b/3a/3b/3c/7a/7b on the 2025 face
    "IRS_2025_1040_INSTR",  # i1040gi: line instructions + the QDCGT worksheet
    "RP_2024_40",           # §2.03 TY2025 0%/15% breakpoints
    "RP_2025_32",           # §4.03 TY2026 0%/15% breakpoints
    "IRC_1",                # §1(h)/§1(j)(5) preferential rates (spine source)
]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY SOURCES (with embedded excerpts) — CREATE
# Form-face/instruction excerpts transcribed 2026-06-11 from the fetched
# PDFs — requires_human_review=False (verbatim, verifiable against the
# on-disk copies in tts-tax-app server/.scratch/ + resources/irs_forms/).
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_SCHB_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Schedule B (Form 1040) — Interest and Ordinary Dividends",
        "citation": "Schedule B (Form 1040) (2025); f1040sb.pdf (created 4/23/25)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f1040sb.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": (
            "Transcribed line by line 2026-06-11 from the manifest-verified copy "
            "(tts-tax-app resources/irs_forms/2025/f1040sb.pdf, SHA256 dd1ec371...). "
            "Single page: Part I 14 payer rows, Part II 15 payer rows, Part III."
        ),
        "topics": ["interest_dividends"],
        "excerpts": [
            {
                "excerpt_label": "Part I totals (verbatim)",
                "location_reference": "Schedule B (2025), Part I",
                "excerpt_text": (
                    "2 Add the amounts on line 1. 3 Excludable interest on series EE and I "
                    "U.S. savings bonds issued after 1989. Attach Form 8815. 4 Subtract "
                    "line 3 from line 2. Enter the result here and on Form 1040 or 1040-SR, "
                    "line 2b. Note: If line 4 is over $1,500, you must complete Part III."
                ),
                "summary_text": "L2 = sum(payer rows); L4 = L2 - L3(8815) -> 1040 line 2b. Over $1,500 -> Part III.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part II totals (verbatim)",
                "location_reference": "Schedule B (2025), Part II",
                "excerpt_text": (
                    "6 Add the amounts on line 5. Enter the total here and on Form 1040 or "
                    "1040-SR, line 3b. Note: If line 6 is over $1,500, you must complete Part III."
                ),
                "summary_text": "L6 = sum(payer rows) -> 1040 line 3b. Over $1,500 -> Part III.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part III gate + questions (verbatim)",
                "location_reference": "Schedule B (2025), Part III",
                "excerpt_text": (
                    "You must complete this part if you (a) had over $1,500 of taxable "
                    "interest or ordinary dividends; (b) had a foreign account; or (c) "
                    "received a distribution from, or were a grantor of, or a transferor "
                    "to, a foreign trust. 7a At any time during 2025, did you have a "
                    "financial interest in or signature authority over a financial account "
                    "... located in a foreign country? ... If 'Yes,' are you required to "
                    "file FinCEN Form 114 ...? 7b If you are required to file FinCEN Form "
                    "114, list the name(s) of the foreign country(-ies) ... 8 During 2025, "
                    "did you receive a distribution from, or were you the grantor of, or "
                    "transferor to, a foreign trust? If 'Yes,' you may have to file Form 3520."
                ),
                "summary_text": "Part III required when (a) over $1,500 either kind, (b) foreign account, (c) foreign trust. Questions 7a (two-part), 7b countries, 8.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Seller-financed mortgage listing rule",
                "location_reference": "Schedule B (2025), line 1 caption",
                "excerpt_text": (
                    "List name of payer. If any interest is from a seller-financed mortgage "
                    "and the buyer used the property as a personal residence, see the "
                    "instructions and list this interest first. Also, show that buyer's "
                    "social security number and address"
                ),
                "summary_text": "Seller-financed interest lists FIRST with buyer SSN + address on the face.",
                "is_key_excerpt": False,
            },
        ],
    },
    {
        "source_code": "IRS_2025_SCHB_INSTR",
        "source_type": "official_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Schedule B (Form 1040)",
        "citation": "Instructions for Schedule B (Form 1040) (2025), Apr 23, 2025; Cat. No. 70541Y",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i1040sb.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": (
            "All 3 pages transcribed 2026-06-11 (server/.scratch/i1040sb_dump.txt). "
            "Carries the filing-requirement list, the nominee/accrued-interest/OID/ABP "
            "subtotal-adjustment conventions, and the Part III definitions."
        ),
        "topics": ["interest_dividends"],
        "excerpts": [
            {
                "excerpt_label": "Schedule B filing requirement (verbatim list)",
                "location_reference": "i1040sb (2025), General Instructions",
                "excerpt_text": (
                    "Use Schedule B (Form 1040) if any of the following applies. You had "
                    "over $1,500 of taxable interest or ordinary dividends. You received "
                    "interest from a seller-financed mortgage and the buyer used the "
                    "property as a personal residence. You have accrued interest from a "
                    "bond. You are reporting original issue discount (OID) of less than "
                    "the amount shown on Form 1099-OID. You are reporting interest income "
                    "of less than the amount shown on a Form 1099 due to amortizable bond "
                    "premium. You are claiming the exclusion of interest from series EE or "
                    "I U.S. savings bonds issued after 1989. You received interest or "
                    "ordinary dividends as a nominee. You had a financial interest in, or "
                    "signature authority over, a financial account in a foreign country or "
                    "you received a distribution from, or were a grantor of, or transferor "
                    "to, a foreign trust."
                ),
                "summary_text": "The 8 Schedule-B-required triggers (R-SB-04).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Nominee subtotal-adjustment convention (verbatim)",
                "location_reference": "i1040sb (2025), Part I, Nominees",
                "excerpt_text": (
                    "Under your last entry on line 1, put a subtotal of all interest listed "
                    "on line 1. Below this subtotal, enter 'Nominee Distribution' and show "
                    "the total interest you received as a nominee. Subtract this amount "
                    "from the subtotal and enter the result on line 2."
                ),
                "summary_text": "Subtotal-then-subtract rows; same convention for 'Accrued Interest', 'OID Adjustment', 'ABP Adjustment' (and Part II nominee dividends).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "ABP Adjustment + payer-reported-net caveat (verbatim)",
                "location_reference": "i1040sb (2025), Amortizable bond premium",
                "excerpt_text": (
                    "If you elect to reduce your interest income on a taxable bond by the "
                    "amount of taxable amortizable bond premium, follow the rules earlier "
                    "under Nominees to see how to report the interest. But identify the "
                    "amount to be subtracted as 'ABP Adjustment.' However, if the payer "
                    "reported to you a net amount of interest income on the bond reflecting "
                    "the offset of the gross amount of interest income by the amortizable "
                    "bond premium, no reduction of the amount of interest income reported "
                    "to you by the payer is permitted on Schedule B for the bond."
                ),
                "summary_text": "JUDGMENT ITEM 1: default subtracts boxes 11/12 as the ABP Adjustment (broker premium reporting per Reg. 1.6045-1(n)); no double-reduction when payer already netted.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Tax-exempt netting + exempt-interest dividends (verbatim)",
                "location_reference": "i1040sb (2025), Tax-exempt interest",
                "excerpt_text": (
                    "Enter the total on line 2a of your Form 1040 or 1040-SR. However, if "
                    "you acquired a tax-exempt bond at a premium, only report the net "
                    "amount of tax-exempt interest on line 2a ... (that is, the excess of "
                    "the tax-exempt interest received during the year over the amortized "
                    "bond premium for the year). ... Also include on line 2a of your Form "
                    "1040 or 1040-SR any exempt-interest dividends from a mutual fund or "
                    "other regulated investment company. This amount should be shown in "
                    "box 12 of Form 1099-DIV."
                ),
                "summary_text": "JUDGMENT ITEM 2: 2a = per-doc max(0, box 8 - box 13) + DIV box 12. Box 9 (PAB) -> Form 6251 line 2g (deferred).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Market discount caution + accrued interest",
                "location_reference": "i1040sb (2025), Part I",
                "excerpt_text": (
                    "Report on line 1 all of your taxable interest. ... Also include any "
                    "accrued market discount that is includible in income ... The market "
                    "discount on a tax-exempt bond is taxable interest income and not "
                    "tax-exempt interest. ... When you buy bonds between interest payment "
                    "dates and pay accrued interest to the seller, this interest is taxable "
                    "to the seller. ... identify the amount to be subtracted as 'Accrued Interest.'"
                ),
                "summary_text": "JUDGMENT ITEM 3: box 10 market discount adds to 2b (taxable even on exempt bonds); purchaser's accrued-interest adjustment subtracts.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "FBAR threshold + penalties",
                "location_reference": "i1040sb (2025), Part III, Line 7a—Question 2",
                "excerpt_text": (
                    "A U.S. person that has a financial interest in or signature authority "
                    "over foreign financial accounts must file the form if the aggregate "
                    "value of foreign financial accounts exceeds $10,000 at any time during "
                    "2025. Do not attach FinCEN Form 114 to your tax return."
                ),
                "summary_text": "FBAR $10,000 aggregate threshold; FinCEN 114 filed separately (never attached).",
                "is_key_excerpt": False,
            },
        ],
    },
    {
        "source_code": "IRS_1099INT_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2024,
        "tax_year_end": 2025,
        "title": "Form 1099-INT — Interest Income (Rev. January 2024)",
        "citation": "Form 1099-INT (Rev. 1-2024), current revision for TY2025",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f1099int.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": (
            "Copy B + recipient instructions transcribed 2026-06-11 "
            "(server/.scratch/f1099int-2025_dump.txt). Boxes 1-17 + FATCA checkbox + "
            "payer RTN. Matches the existing InterestIncome model (17 boxes); the FATCA "
            "checkbox is a model gap noted for the build leg."
        ),
        "topics": ["interest_dividends"],
        "excerpts": [
            {
                "excerpt_label": "Box structure (Copy B)",
                "location_reference": "Form 1099-INT (Rev. 1-2024), Copy B",
                "excerpt_text": (
                    "1 Interest income. 2 Early withdrawal penalty. 3 Interest on U.S. "
                    "Savings Bonds and Treasury obligations. 4 Federal income tax withheld. "
                    "5 Investment expenses. 6 Foreign tax paid. 7 Foreign country or U.S. "
                    "territory. 8 Tax-exempt interest. 9 Specified private activity bond "
                    "interest. 10 Market discount. 11 Bond premium. 12 Bond premium on "
                    "Treasury obligations. 13 Bond premium on tax-exempt bond. 14 "
                    "Tax-exempt and tax credit bond CUSIP no. 15 State. 16 State "
                    "identification no. 17 State tax withheld. FATCA filing requirement [box]."
                ),
                "summary_text": "Boxes 1-17 + FATCA. Box 3 NOT included in box 1 (recipient instructions).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Box 3 not in box 1 (recipient instructions)",
                "location_reference": "Form 1099-INT (Rev. 1-2024), Instructions for Recipient, Box 3",
                "excerpt_text": (
                    "Shows interest on U.S. Savings Bonds, Treasury bills, Treasury bonds, "
                    "and Treasury notes. This may or may not all be taxable. See Pub. 550. "
                    "This interest is exempt from state and local income taxes. This "
                    "interest is not included in box 1."
                ),
                "summary_text": "2b per-doc taxable interest = box 1 + box 3 (+ box 10) - premiums; box 3 is additive, never a subset.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_1099DIV_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2024,
        "tax_year_end": 2025,
        "title": "Form 1099-DIV — Dividends and Distributions (Rev. January 2024)",
        "citation": "Form 1099-DIV (Rev. 1-2024), current revision for TY2025",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f1099div.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": (
            "Copy B + recipient instructions transcribed 2026-06-11 "
            "(server/.scratch/f1099div-2025_dump.txt). No dividend document model exists "
            "in the app today — the build leg creates DividendIncome mirroring "
            "InterestIncome (snapshot payer block + all boxes below)."
        ),
        "topics": ["interest_dividends"],
        "excerpts": [
            {
                "excerpt_label": "Box structure (Copy B)",
                "location_reference": "Form 1099-DIV (Rev. 1-2024), Copy B",
                "excerpt_text": (
                    "1a Total ordinary dividends. 1b Qualified dividends. 2a Total capital "
                    "gain distr. 2b Unrecap. Sec. 1250 gain. 2c Section 1202 gain. 2d "
                    "Collectibles (28%) gain. 2e Section 897 ordinary dividends. 2f "
                    "Section 897 capital gain. 3 Nondividend distributions. 4 Federal "
                    "income tax withheld. 5 Section 199A dividends. 6 Investment expenses. "
                    "7 Foreign tax paid. 8 Foreign country or U.S. possession. 9 Cash "
                    "liquidation distributions. 10 Noncash liquidation distributions. 11 "
                    "FATCA filing requirement [box]. 12 Exempt-interest dividends. 13 "
                    "Specified private activity bond interest dividends. 14 State. 15 "
                    "State identification no. 16 State tax withheld."
                ),
                "summary_text": "1a -> 3b; 1b -> 3a; 2a -> 7a (checkbox path) or Sch D; 4 -> 25b; 12 -> 2a; 2b/2c/2d block the no-Sch-D path (Exception 1).",
                "is_key_excerpt": True,
            },
        ],
    },
]

# Excerpts to add to EXISTING sources.
NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = [
    (
        "IRS_2025_1040_INSTR",
        {
            "excerpt_label": "QDCGT worksheet — all 25 lines (verbatim structure)",
            "location_reference": "i1040gi (2025), p.38 — Qualified Dividends and Capital Gain Tax Worksheet—Line 16",
            "excerpt_text": (
                "1. Enter the amount from Form 1040 or 1040-SR, line 15. 2. Enter the "
                "amount from Form 1040 or 1040-SR, line 3a. 3. Are you filing Schedule D? "
                "Yes: Enter the smaller of line 15 or line 16 of Schedule D. If either "
                "line 15 or line 16 is blank or a loss, enter -0-. No: Enter the amount "
                "from Form 1040 or 1040-SR, line 7a. 4. Add lines 2 and 3. 5. Subtract "
                "line 4 from line 1. If zero or less, enter -0-. 6. Enter: $48,350 if "
                "single or married filing separately, $96,700 if married filing jointly "
                "or qualifying surviving spouse, $64,750 if head of household. 7. Enter "
                "the smaller of line 1 or line 6. 8. Enter the smaller of line 5 or "
                "line 7. 9. Subtract line 8 from line 7. This amount is taxed at 0%. "
                "10. Enter the smaller of line 1 or line 4. 11. Enter the amount from "
                "line 9. 12. Subtract line 11 from line 10. 13. Enter: $533,400 if "
                "single, $300,000 if married filing separately, $600,050 if married "
                "filing jointly or qualifying surviving spouse, $566,700 if head of "
                "household. 14. Enter the smaller of line 1 or line 13. 15. Add lines 5 "
                "and 9. 16. Subtract line 15 from line 14. If zero or less, enter -0-. "
                "17. Enter the smaller of line 12 or line 16. 18. Multiply line 17 by "
                "15% (0.15). 19. Add lines 9 and 17. 20. Subtract line 19 from line 10. "
                "21. Multiply line 20 by 20% (0.20). 22. Figure the tax on the amount on "
                "line 5 [Tax Table if < $100,000; Tax Computation Worksheet otherwise]. "
                "23. Add lines 18, 21, and 22. 24. Figure the tax on the amount on "
                "line 1 [same routing]. 25. Tax on all taxable income. Enter the smaller "
                "of line 23 or line 24. Also include this amount on Form 1040 or "
                "1040-SR, line 16."
            ),
            "summary_text": (
                "The full worksheet. TY2025 breakpoints printed on the face (lines 6/13) "
                "match RP 2024-40 §2.03 exactly. WS22/WS24 inherit the line-16 tax-method "
                "routing (Table below $100K, TCW at/above)."
            ),
            "is_key_excerpt": True,
        },
    ),
    (
        "IRS_2025_1040_INSTR",
        {
            "excerpt_label": "Line 7a Exception 1 + line 7b boxes (verbatim)",
            "location_reference": "i1040gi (2025), pp.31+33 — Line 7a / Line 7b",
            "excerpt_text": (
                "Exception 1. You don't have to file Form 8949 or Schedule D if you "
                "aren't deferring any capital gain by investing in a qualified "
                "opportunity fund and both of the following apply. 1. You have no "
                "capital losses, and your only capital gains are capital gain "
                "distributions from Form(s) 1099-DIV, box 2a ...; and 2. None of the "
                "Form(s) 1099-DIV ... have an amount in box 2b (unrecaptured section "
                "1250 gain), box 2c (section 1202 gain), or box 2d (collectibles (28%) "
                "gain). ... If Exception 1 applies, enter your total capital gain "
                "distributions (from box 2a of Form(s) 1099-DIV) on line 7a and check "
                "the box 'Schedule D not required' on line 7b. ... If you are including "
                "your child's capital gain or (loss) in the total on line 7a, check the "
                "'includes child's capital gain or (loss)' box on line 7b and enter the "
                "amount from Form 8814, line 10, in the entry space."
            ),
            "summary_text": (
                "The line-7 checkbox path: 7a = sum(DIV box 2a) + 7b box checked, gated "
                "on Exception 1 (preparer-asserted condition 1; condition 2 checked "
                "computationally against the documents). 8814 child inclusion = separate "
                "7b box + entry space (RED unsupported this sprint)."
            ),
            "is_key_excerpt": True,
        },
    ),
    (
        "IRS_2025_1040_INSTR",
        {
            "excerpt_label": "Lines 2a/2b/3a/3b/3c sources (verbatim fragments)",
            "location_reference": "i1040gi (2025), pp.25-26",
            "excerpt_text": (
                "Line 2a: ... Also include on line 2a any exempt-interest dividends from "
                "a mutual fund or other regulated investment company. This amount should "
                "be shown in box 12 of Form 1099-DIV. ... Line 2b: Each payer should "
                "send you a Form 1099-INT or Form 1099-OID. Enter your total taxable "
                "interest income on line 2b. But you must fill in and attach Schedule B "
                "if the total is over $1,500 or any of the other conditions listed at "
                "the beginning of the Schedule B instructions applies to you. ... "
                "Line 3a: Enter your total qualified dividends on line 3a. Qualified "
                "dividends are also included in the ordinary dividend total required to "
                "be shown on line 3b. ... Generally, these dividends are shown in "
                "box 1b of Form(s) 1099-DIV. If you are including your child's "
                "qualified dividends in the total on line 3a, check box 1 on line 3c. "
                "... Line 3b: Each payer should send you a Form 1099-DIV. Enter your "
                "total ordinary dividends on line 3b. This amount should be shown in "
                "box 1a of Form(s) 1099-DIV. ... You must fill in and attach Schedule B "
                "if the total is over $1,500 or you received, as a nominee, ordinary "
                "dividends that actually belong to someone else."
            ),
            "summary_text": (
                "Line-source map: 2a <- INT box 8 net + DIV box 12; 2b <- INT documents; "
                "3a <- DIV box 1b (subset of 3b — D_INTDIV_005 polices 3a <= 3b); "
                "3b <- DIV box 1a. Line 3c = NEW 2025 child's-dividends checkboxes "
                "(Form 8814 — RED unsupported)."
            ),
            "is_key_excerpt": True,
        },
    ),
    (
        "RP_2024_40",
        {
            "excerpt_label": "§2.03 Maximum Capital Gains Rate (TY2025, verbatim)",
            "location_reference": "Rev. Proc. 2024-40, §2.03",
            "excerpt_text": (
                "For taxable years beginning in 2025, the maximum zero rate amounts and "
                "maximum 15 percent rate amounts under § 1(j)(5)(B), as adjusted for "
                "inflation, are as follows: Married Individuals Filing Joint Returns and "
                "Surviving Spouse $96,700 / $600,050. Married Individuals Filing "
                "Separate Returns $48,350 / $300,000. Heads of Household $64,750 / "
                "$566,700. All Other Individuals $48,350 / $533,400."
            ),
            "summary_text": (
                "TY2025 QDCGT WS6/WS13 constants. Triple-verified: rev proc + the "
                "published worksheet face (i1040gi p.38 lines 6/13) + prior capture."
            ),
            "is_key_excerpt": True,
        },
    ),
    (
        "RP_2025_32",
        {
            "excerpt_label": "§4.03 Maximum Capital Gains Rate (TY2026, verbatim)",
            "location_reference": "Rev. Proc. 2025-32, §4.03",
            "excerpt_text": (
                "For taxable years beginning in 2026, the maximum zero rate amounts and "
                "maximum 15 percent rate amounts under § 1(j)(5)(B), as adjusted for "
                "inflation, are as follows: Married Individuals Filing Joint Returns and "
                "Surviving Spouse $98,900 / $613,700. Married Individuals Filing "
                "Separate Returns $49,450 / $306,850. Heads of Household $66,200 / "
                "$579,600. All Other Individuals $49,450 / $545,500. Estates and Trusts "
                "$3,300 / $16,250."
            ),
            "summary_text": "TY2026 QDCGT WS6/WS13 constants (target-year policy: verified independently of 2025).",
            "is_key_excerpt": True,
        },
    ),
]


# ═══════════════════════════════════════════════════════════════════════════
# 1040_INTDIV — 1099-INT/DIV aggregation + QDCGT worksheet (pseudo-form)
# ═══════════════════════════════════════════════════════════════════════════

INTDIV_IDENTITY = {
    "form_number": "1040_INTDIV",
    "form_title": "Interest, Dividends & QDCGT — 1099-INT/DIV aggregation + Line 16 worksheet (TY2025)",
    "notes": (
        "Sprint Topic 3. PSEUDO-FORM: not an IRS face — it carries (a) the per-"
        "document 1099-INT/1099-DIV facts and their aggregation rules to Form 1040 "
        "lines 2a/2b/3a/3b/7a + the 25b withholding extension, and (b) the Qualified "
        "Dividends and Capital Gain Tax Worksheet (25 lines) that computes 1040 "
        "line 16 on the supported paths, superseding the spine's R-TAX-07 bridge "
        "gate. The worksheet prints as a STATEMENT page (never a faked IRS layout); "
        "Schedule B (separate TaxForm SCH_B) is the IRS face for the payer listings. "
        "Year-keyed constants: ONLY the WS6/WS13 breakpoints (TY2025 RP 2024-40 "
        "§2.03; TY2026 RP 2025-32 §4.03). The aggregated 1040 lines become computed "
        "feeders (YELLOW) with the preparer override as the universal escape hatch."
    ),
}

INTDIV_FACTS: list[dict] = [
    # ── 1099-INT document facts (per-document; existing InterestIncome model) ──
    {"fact_key": "int_payer_name", "label": "1099-INT: payer name", "data_type": "string", "sort_order": 1,
     "notes": "PER DOCUMENT. Existing InterestIncome.payer_name (+ EIN/address snapshot block)."},
    {"fact_key": "int_box1_interest", "label": "1099-INT box 1: interest income", "data_type": "decimal",
     "default_value": "0", "sort_order": 2, "notes": "PER DOCUMENT. InterestIncome.interest_income."},
    {"fact_key": "int_box2_early_withdrawal", "label": "1099-INT box 2: early withdrawal penalty", "data_type": "decimal",
     "default_value": "0", "sort_order": 3,
     "notes": "PER DOCUMENT. Already a live YELLOW feeder to Schedule 1 line 18 (Topic 2)."},
    {"fact_key": "int_box3_treasury", "label": "1099-INT box 3: US savings bonds / Treasury interest", "data_type": "decimal",
     "default_value": "0", "sort_order": 4,
     "notes": "PER DOCUMENT. NOT included in box 1 (recipient instructions) — additive in the 2b roster."},
    {"fact_key": "int_box4_fed_withheld", "label": "1099-INT box 4: federal income tax withheld", "data_type": "decimal",
     "default_value": "0", "sort_order": 5, "notes": "PER DOCUMENT. Already feeds 1040 line 25b (spine R-PAY-02)."},
    {"fact_key": "int_box5_investment_expenses", "label": "1099-INT box 5: investment expenses", "data_type": "decimal",
     "default_value": "0", "sort_order": 6, "notes": "PER DOCUMENT. Stored; no 1040 flow (TCJA suspended misc 2%)."},
    {"fact_key": "int_box6_foreign_tax", "label": "1099-INT box 6: foreign tax paid", "data_type": "decimal",
     "default_value": "0", "sort_order": 7, "notes": "PER DOCUMENT. Stored; FTC entry is manual (D_INTDIV_008)."},
    {"fact_key": "int_box7_foreign_country", "label": "1099-INT box 7: foreign country", "data_type": "string", "sort_order": 8},
    {"fact_key": "int_box8_tax_exempt", "label": "1099-INT box 8: tax-exempt interest", "data_type": "decimal",
     "default_value": "0", "sort_order": 9, "notes": "PER DOCUMENT. 2a roster (net of box 13)."},
    {"fact_key": "int_box9_pab", "label": "1099-INT box 9: specified private activity bond interest", "data_type": "decimal",
     "default_value": "0", "sort_order": 10,
     "notes": "PER DOCUMENT. Subset of box 8. AMT preference -> 6251 line 2g; 6251 DEFERRED (D_INTDIV_009 info)."},
    {"fact_key": "int_box10_market_discount", "label": "1099-INT box 10: market discount", "data_type": "decimal",
     "default_value": "0", "sort_order": 11,
     "notes": ("PER DOCUMENT. JUDGMENT ITEM 3: additive in 2b — box only populated under the §1278(b) "
               "current-inclusion election; taxable even on tax-exempt bonds (i1040sb caution).")},
    {"fact_key": "int_box11_bond_premium", "label": "1099-INT box 11: bond premium (taxable, non-Treasury)", "data_type": "decimal",
     "default_value": "0", "sort_order": 12,
     "notes": "PER DOCUMENT. JUDGMENT ITEM 1: subtracts from 2b (Sch B prints the ABP Adjustment row)."},
    {"fact_key": "int_box12_treasury_premium", "label": "1099-INT box 12: bond premium on Treasury obligations", "data_type": "decimal",
     "default_value": "0", "sort_order": 13, "notes": "PER DOCUMENT. Subtracts from 2b (pairs with box 3)."},
    {"fact_key": "int_box13_exempt_premium", "label": "1099-INT box 13: bond premium on tax-exempt bond", "data_type": "decimal",
     "default_value": "0", "sort_order": 14,
     "notes": "PER DOCUMENT. JUDGMENT ITEM 2: nets against box 8 inside 2a, floored at 0 per document."},
    {"fact_key": "int_box14_cusip", "label": "1099-INT box 14: tax-exempt bond CUSIP", "data_type": "string", "sort_order": 15},
    {"fact_key": "int_box15_state", "label": "1099-INT box 15: state", "data_type": "string", "sort_order": 16},
    {"fact_key": "int_box16_state_id", "label": "1099-INT box 16: state identification no.", "data_type": "string", "sort_order": 17},
    {"fact_key": "int_box17_state_withheld", "label": "1099-INT box 17: state tax withheld", "data_type": "decimal",
     "default_value": "0", "sort_order": 18, "notes": "PER DOCUMENT. Stored for the Georgia 500 (Aug-Sept runway)."},
    {"fact_key": "int_fatca", "label": "1099-INT: FATCA filing requirement box", "data_type": "boolean", "sort_order": 19,
     "notes": "PER DOCUMENT. MODEL GAP: InterestIncome has no FATCA flag — build leg adds it (additive migration)."},
    {"fact_key": "int_nominee_amount", "label": "1099-INT: portion received as nominee", "data_type": "decimal",
     "default_value": "0", "sort_order": 20,
     "notes": ("PER DOCUMENT. NEW FIELD (build leg). Subtracts from 2b; renders as the Sch B "
               "'Nominee Distribution' subtotal-adjustment row (i1040sb verbatim convention).")},
    {"fact_key": "int_accrued_interest_adjustment", "label": "1099-INT: accrued interest paid to seller (purchaser adjustment)",
     "data_type": "decimal", "default_value": "0", "sort_order": 21,
     "notes": "PER DOCUMENT. NEW FIELD (build leg). Subtracts from 2b; renders as the 'Accrued Interest' row."},
    {"fact_key": "int_seller_financed", "label": "1099-INT entry: seller-financed mortgage interest", "data_type": "boolean",
     "sort_order": 22,
     "notes": ("PER DOCUMENT. NEW FIELD (build leg) — interest entries are keyed as 1099-INT documents even "
               "when no 1099 was issued (seller-financed buyers don't issue one); this flag drives the "
               "list-first + buyer-SSN Schedule B convention. D_SCHB_006 polices the SSN.")},
    {"fact_key": "int_buyer_ssn", "label": "Seller-financed: buyer's SSN", "data_type": "string", "sort_order": 23,
     "notes": "PER DOCUMENT. NEW FIELD. MeF NNN-NN-NNNN; $50 penalty exposure when missing (i1040sb)."},
    {"fact_key": "int_buyer_address", "label": "Seller-financed: buyer's address", "data_type": "string", "sort_order": 24,
     "notes": "PER DOCUMENT. NEW FIELD. Shown on the Schedule B line-1 listing."},
    # ── 1099-DIV document facts (per-document; NEW DividendIncome model) ──
    {"fact_key": "div_payer_name", "label": "1099-DIV: payer name", "data_type": "string", "sort_order": 40,
     "notes": "PER DOCUMENT. Build leg creates DividendIncome mirroring InterestIncome (payer snapshot block)."},
    {"fact_key": "div_box1a_ordinary", "label": "1099-DIV box 1a: total ordinary dividends", "data_type": "decimal",
     "default_value": "0", "sort_order": 41, "notes": "PER DOCUMENT. 3b roster."},
    {"fact_key": "div_box1b_qualified", "label": "1099-DIV box 1b: qualified dividends", "data_type": "decimal",
     "default_value": "0", "sort_order": 42,
     "notes": "PER DOCUMENT. 3a roster. JUDGMENT ITEM 6: holding-period exceptions = preparer override on 3a."},
    {"fact_key": "div_box2a_capgain", "label": "1099-DIV box 2a: total capital gain distributions", "data_type": "decimal",
     "default_value": "0", "sort_order": 43,
     "notes": "PER DOCUMENT. Line 7a via the Exception-1 checkbox path ONLY; otherwise Sch D (RED this sprint)."},
    {"fact_key": "div_box2b_unrecap_1250", "label": "1099-DIV box 2b: unrecaptured §1250 gain", "data_type": "decimal",
     "default_value": "0", "sort_order": 44,
     "notes": "PER DOCUMENT. Stored. ANY amount blocks Exception 1 -> D_INTDIV_001 RED (Sch D Tax Worksheet territory)."},
    {"fact_key": "div_box2c_1202", "label": "1099-DIV box 2c: section 1202 gain", "data_type": "decimal",
     "default_value": "0", "sort_order": 45, "notes": "PER DOCUMENT. Stored. Blocks Exception 1 -> D_INTDIV_001."},
    {"fact_key": "div_box2d_collectibles", "label": "1099-DIV box 2d: collectibles (28%) gain", "data_type": "decimal",
     "default_value": "0", "sort_order": 46, "notes": "PER DOCUMENT. Stored. Blocks Exception 1 -> D_INTDIV_001."},
    {"fact_key": "div_box2e_897_ordinary", "label": "1099-DIV box 2e: section 897 ordinary dividends", "data_type": "decimal",
     "default_value": "0", "sort_order": 47,
     "notes": "PER DOCUMENT. Stored; FIRPTA disclosure relevant only to nonresident aliens — no 1040 flow."},
    {"fact_key": "div_box2f_897_capgain", "label": "1099-DIV box 2f: section 897 capital gain", "data_type": "decimal",
     "default_value": "0", "sort_order": 48, "notes": "PER DOCUMENT. Stored; same as 2e."},
    {"fact_key": "div_box3_nondividend", "label": "1099-DIV box 3: nondividend distributions", "data_type": "decimal",
     "default_value": "0", "sort_order": 49,
     "notes": "PER DOCUMENT. Return of basis — not taxable until basis exhausted (Pub 550); stored, info note."},
    {"fact_key": "div_box4_fed_withheld", "label": "1099-DIV box 4: federal income tax withheld", "data_type": "decimal",
     "default_value": "0", "sort_order": 50,
     "notes": "PER DOCUMENT. NEW 25b addend — extends spine R-PAY-02 (was 1099-INT box 4 only)."},
    {"fact_key": "div_box5_199a", "label": "1099-DIV box 5: section 199A dividends", "data_type": "decimal",
     "default_value": "0", "sort_order": 51,
     "notes": "PER DOCUMENT. STORED NOW, consumed by the QBI topic (8995) later — SPRINT_SCOPE explicit. D_INTDIV_010 info."},
    {"fact_key": "div_box6_investment_expenses", "label": "1099-DIV box 6: investment expenses", "data_type": "decimal",
     "default_value": "0", "sort_order": 52, "notes": "PER DOCUMENT. Stored; included in 1a by the payer."},
    {"fact_key": "div_box7_foreign_tax", "label": "1099-DIV box 7: foreign tax paid", "data_type": "decimal",
     "default_value": "0", "sort_order": 53,
     "notes": "PER DOCUMENT. Stored; FTC (Sch 3 line 1) entry is manual until a 1116 topic — D_INTDIV_008 info."},
    {"fact_key": "div_box8_foreign_country", "label": "1099-DIV box 8: foreign country or US possession",
     "data_type": "string", "sort_order": 54},
    {"fact_key": "div_box9_cash_liquidation", "label": "1099-DIV box 9: cash liquidation distributions", "data_type": "decimal",
     "default_value": "0", "sort_order": 55,
     "notes": "PER DOCUMENT. Basis-recovery/capital-gain treatment is manual (Pub 550) — D_INTDIV_007 warning."},
    {"fact_key": "div_box10_noncash_liquidation", "label": "1099-DIV box 10: noncash liquidation distributions",
     "data_type": "decimal", "default_value": "0", "sort_order": 56, "notes": "PER DOCUMENT. Same as box 9."},
    {"fact_key": "div_box11_fatca", "label": "1099-DIV box 11: FATCA filing requirement box", "data_type": "boolean",
     "sort_order": 57},
    {"fact_key": "div_box12_exempt_interest_div", "label": "1099-DIV box 12: exempt-interest dividends", "data_type": "decimal",
     "default_value": "0", "sort_order": 58, "notes": "PER DOCUMENT. 2a roster addend (i1040sb verbatim)."},
    {"fact_key": "div_box13_pab_div", "label": "1099-DIV box 13: specified PAB interest dividends", "data_type": "decimal",
     "default_value": "0", "sort_order": 59, "notes": "PER DOCUMENT. Subset of box 12; AMT preference (6251 deferred)."},
    {"fact_key": "div_box14_state", "label": "1099-DIV box 14: state", "data_type": "string", "sort_order": 60},
    {"fact_key": "div_box15_state_id", "label": "1099-DIV box 15: state identification no.", "data_type": "string", "sort_order": 61},
    {"fact_key": "div_box16_state_withheld", "label": "1099-DIV box 16: state tax withheld", "data_type": "decimal",
     "default_value": "0", "sort_order": 62, "notes": "PER DOCUMENT. Stored for the Georgia 500."},
    {"fact_key": "div_nominee_amount", "label": "1099-DIV: ordinary dividends received as nominee", "data_type": "decimal",
     "default_value": "0", "sort_order": 63,
     "notes": "PER DOCUMENT. Subtracts from 3b; renders as the Sch B Part II 'Nominee Distribution' row."},
    # ── Return-level facts ──
    {"fact_key": "capital_gain_distributions_only", "label": "Preparer assertion: Exception 1 condition (1) — no other capital gains/losses, no QOF deferral",
     "data_type": "boolean", "sort_order": 80,
     "notes": ("JUDGMENT ITEM 5. The software verifies condition (2) computationally (no 2b/2c/2d on any "
               "document); condition (1) — no capital losses, no other capital gains, no QOF deferral — is "
               "unknowable from entered data and is the preparer's assertion. True + clean documents -> "
               "7a computes and the 7b 'Schedule D not required' box checks at render.")},
    {"fact_key": "child_dividends_3c_qualified", "label": "Line 3c box 1: includes child's qualified dividends (Form 8814)",
     "data_type": "boolean", "sort_order": 81, "notes": "NEW 2025 face line 3c. ANY child-income inclusion -> D_INTDIV_003 RED (8814 not built)."},
    {"fact_key": "child_dividends_3c_ordinary", "label": "Line 3c box 2: includes child's ordinary dividends (Form 8814)",
     "data_type": "boolean", "sort_order": 82, "notes": "D_INTDIV_003 RED."},
    {"fact_key": "child_capgain_7b", "label": "Line 7b box: includes child's capital gain (Form 8814) + amount",
     "data_type": "decimal", "default_value": "0", "sort_order": 83,
     "notes": "7b second box + entry space (Form 8814 line 10 amount). Nonzero -> D_INTDIV_003 RED."},
    # ── QDCGT worksheet outputs (traceability) ──
    {"fact_key": "qdcgt_zero_rate_max", "label": "WS6: maximum zero-rate amount (year + filing status keyed)",
     "data_type": "decimal", "sort_order": 90,
     "notes": ("CONSTANT. TY2025 (RP 2024-40 §2.03): single/MFS 48,350; MFJ/QSS 96,700; HOH 64,750. "
               "TY2026 (RP 2025-32 §4.03): single/MFS 49,450; MFJ/QSS 98,900; HOH 66,200. QSS uses MFJ.")},
    {"fact_key": "qdcgt_15_rate_max", "label": "WS13: maximum 15%-rate amount (year + filing status keyed)",
     "data_type": "decimal", "sort_order": 91,
     "notes": ("CONSTANT. TY2025: single 533,400; MFS 300,000; MFJ/QSS 600,050; HOH 566,700. "
               "TY2026: single 545,500; MFS 306,850; MFJ/QSS 613,700; HOH 579,600. NOTE: WS13 single != MFS "
               "(unlike WS6) — never collapse them.")},
    {"fact_key": "qdcgt_tax_result", "label": "WS25: tax on all taxable income -> 1040 line 16", "data_type": "decimal",
     "sort_order": 92, "notes": "Calculated: min(WS23, WS24). Replaces the spine bridge gate on supported paths."},
]

INTDIV_RULES: list[dict] = [
    # ── Aggregation rules ──
    {"rule_id": "R-AGG-2B", "title": "1040 line 2b = sum of per-document net taxable interest - Form 8815 exclusion",
     "rule_type": "calculation", "precedence": 1, "sort_order": 1,
     "formula": ("L2b = SUM over 1099-INT docs [box1 + box3 + box10 - box11 - box12 - nominee - accrued_adj] "
                 "- SCH_B.L3 (Form 8815 exclusion). No per-document floor (a negative per-doc net fires "
                 "D_INTDIV_006 instead of being clamped)."),
     "inputs": ["int_box1_interest", "int_box3_treasury", "int_box10_market_discount", "int_box11_bond_premium",
                "int_box12_treasury_premium", "int_nominee_amount", "int_accrued_interest_adjustment"],
     "outputs": ["1040.L2b"],
     "description": ("ONCE PER RETURN. JUDGMENT ITEMS 1+3: boxes 11/12 subtract by default (broker premium "
                     "reporting, Reg. 1.6045-1(n); Sch B prints the ABP Adjustment row); box 10 adds (populated "
                     "only under the §1278(b) election). Box 3 is additive — NOT a subset of box 1 (1099-INT "
                     "recipient instructions verbatim). The 8815 subtraction comes from Schedule B line 3 "
                     "(R-SB-02) so Sch B line 4 and 1040 line 2b can never diverge. Supersedes today's "
                     "compute (box1+box3 only). Computed feeder (YELLOW); preparer override = escape hatch.")},
    {"rule_id": "R-AGG-2A", "title": "1040 line 2a = per-document net tax-exempt interest + exempt-interest dividends",
     "rule_type": "calculation", "precedence": 1, "sort_order": 2,
     "formula": "L2a = SUM over 1099-INT docs [max(0, box8 - box13)] + SUM over 1099-DIV docs [box12]",
     "inputs": ["int_box8_tax_exempt", "int_box13_exempt_premium", "div_box12_exempt_interest_div"],
     "outputs": ["1040.L2a"],
     "description": ("ONCE PER RETURN. JUDGMENT ITEM 2: 'the EXCESS of the tax-exempt interest received ... "
                     "over the amortized bond premium' (i1040sb verbatim) — floored at 0 per document. DIV "
                     "box 12 added per the same instruction. Box 9/13 (PAB) are subsets carried for the "
                     "deferred 6251. Supersedes today's compute (box 8 only).")},
    {"rule_id": "R-AGG-3B", "title": "1040 line 3b = sum of box 1a - nominee dividends",
     "rule_type": "calculation", "precedence": 1, "sort_order": 3,
     "formula": "L3b = SUM over 1099-DIV docs [box1a - nominee]",
     "inputs": ["div_box1a_ordinary", "div_nominee_amount"], "outputs": ["1040.L3b"],
     "description": ("ONCE PER RETURN. i1040gi line 3b verbatim (box 1a) + the Sch B Part II nominee "
                     "subtotal-adjustment. Computed feeder (YELLOW).")},
    {"rule_id": "R-AGG-3A", "title": "1040 line 3a = sum of box 1b (preparer override for holding-period exceptions)",
     "rule_type": "calculation", "precedence": 1, "sort_order": 4,
     "formula": "L3a = SUM over 1099-DIV docs [box1b]; preparer override allowed downward (61-day rule etc.)",
     "inputs": ["div_box1b_qualified"], "outputs": ["1040.L3a"],
     "description": ("ONCE PER RETURN. JUDGMENT ITEM 6: box 1b may overstate qualified dividends (holding-"
                     "period, payments in lieu, surrogate foreign corp — i1040gi Exception list); those are "
                     "preparer judgment, handled via the standard line override (is_overridden). "
                     "D_INTDIV_005 polices 3a <= 3b.")},
    {"rule_id": "R-AGG-7A", "title": "Line 7a checkbox path: capital gain distributions without Schedule D (Exception 1)",
     "rule_type": "calculation", "precedence": 1, "sort_order": 5,
     "formula": ("IF capital_gain_distributions_only AND every 1099-DIV doc has box2b = box2c = box2d = 0 "
                 "AND SUM(box2a) > 0: L7a = SUM(box2a); 7b 'Schedule D not required' box CHECKED at render. "
                 "ELSE IF SUM(box2a) > 0: 7a NOT computed; D_INTDIV_001/002 RED; line 16 not computed."),
     "inputs": ["capital_gain_distributions_only", "div_box2a_capgain", "div_box2b_unrecap_1250",
                "div_box2c_1202", "div_box2d_collectibles"],
     "outputs": ["1040.L7a"],
     "description": ("ONCE PER RETURN. i1040gi Exception 1 verbatim: condition (2) (no 2b/2c/2d on ANY "
                     "document) is checked computationally; condition (1) (no capital losses, no other "
                     "capital gains, no QOF deferral) is the preparer assertion fact — JUDGMENT ITEM 5. "
                     "Nominee capital-gain distributions: report only the owned portion (preparer adjusts "
                     "the document's 2a; statement = render-leg note).")},
    {"rule_id": "R-AGG-25B", "title": "1040 line 25b withholding roster EXTENDS to 1099-DIV box 4",
     "rule_type": "calculation", "precedence": 1, "sort_order": 6,
     "formula": "L25b = SUM over 1099-INT docs [box4] + SUM over 1099-DIV docs [box4]",
     "inputs": ["int_box4_fed_withheld", "div_box4_fed_withheld"], "outputs": ["1040.L25b"],
     "description": ("ONCE PER RETURN. Supersession note: spine R-PAY-02 computed 25b from 1099-INT box 4 "
                     "only ('computed from 1099 documents as they land' — this is the next landing). "
                     "Override stays for unmodeled 1099-R/G withholding until Topic 5.")},
    # ── QDCGT worksheet ──
    {"rule_id": "R-QDCGT-GATE", "title": "QDCGT worksheet applies on the supported preferential-rate paths",
     "rule_type": "routing", "precedence": 0, "sort_order": 10,
     "formula": ("USE the QDCGT worksheet for line 16 when: (L3a > 0 OR (L7a > 0 AND sch-D-not-required path "
                 "active)) AND NOT files_form_2555 AND no 8814 child-income inclusion AND no Schedule D. "
                 "BLOCKED (line 16 BLANK + RED): 7a < 0 (loss needs Sch D); 7a != 0 without the checkbox "
                 "path; any DIV 2b/2c/2d; files_form_2555 on a preferential-rate return; any 8814 flag. "
                 "When no preferential-rate income exists, spine R-TAX-01 routing stands unchanged."),
     "inputs": ["capital_gain_distributions_only", "child_dividends_3c_qualified", "child_dividends_3c_ordinary",
                "child_capgain_7b"],
     "outputs": [],
     "description": ("ONCE PER RETURN. SUPERSEDES spine R-TAX-07: the bridge gate (blank line 16 on ANY 3a/7a "
                     "value) NARROWS to the still-unsupported paths. D_1040_001 retires at the build leg "
                     "(spine loader edit on Ken's approval); D_INTDIV_001/002/003/004 carry the narrowed "
                     "REDs. Topic 8 (Schedule D) later replaces the line-3 No-branch with the Sch-D branch.")},
    {"rule_id": "R-QDCGT-01", "title": "WS1-WS5: income split", "rule_type": "calculation",
     "precedence": 2, "sort_order": 11,
     "formula": "WS1 = 1040.L15; WS2 = 1040.L3a; WS3 = 1040.L7a (No-Schedule-D branch this sprint); WS4 = WS2 + WS3; WS5 = max(0, WS1 - WS4)",
     "inputs": [], "outputs": ["WS1", "WS2", "WS3", "WS4", "WS5"],
     "description": ("Worksheet lines 1-5 verbatim (i1040gi p.38). WS5 = ordinary-rate income. The Yes-branch "
                     "of line 3 (smaller of Sch D 15/16, 0 if blank/loss) lands with Topic 8.")},
    {"rule_id": "R-QDCGT-02", "title": "WS6-WS9: 0% rate slice", "rule_type": "calculation",
     "precedence": 2, "sort_order": 12,
     "formula": ("WS6 = zero_rate_max(filing_status, tax_year); WS7 = min(WS1, WS6); WS8 = min(WS5, WS7); "
                 "WS9 = WS7 - WS8  [taxed at 0%]"),
     "inputs": ["qdcgt_zero_rate_max"], "outputs": ["WS6", "WS7", "WS8", "WS9"],
     "description": ("Year-keyed constant (TY2025 RP 2024-40 §2.03 / TY2026 RP 2025-32 §4.03, both transcribed "
                     "verbatim in this loader). QSS uses the MFJ amount ('married filing jointly or "
                     "qualifying surviving spouse' — worksheet face).")},
    {"rule_id": "R-QDCGT-03", "title": "WS10-WS12: preferential income above the 0% slice", "rule_type": "calculation",
     "precedence": 2, "sort_order": 13,
     "formula": "WS10 = min(WS1, WS4); WS11 = WS9; WS12 = WS10 - WS11",
     "inputs": [], "outputs": ["WS10", "WS11", "WS12"],
     "description": "Worksheet lines 10-12 verbatim."},
    {"rule_id": "R-QDCGT-04", "title": "WS13-WS18: 15% rate slice", "rule_type": "calculation",
     "precedence": 2, "sort_order": 14,
     "formula": ("WS13 = max_15_rate(filing_status, tax_year); WS14 = min(WS1, WS13); WS15 = WS5 + WS9; "
                 "WS16 = max(0, WS14 - WS15); WS17 = min(WS12, WS16); WS18 = ROUND_HALF_UP(0.15 * WS17, $1)"),
     "inputs": ["qdcgt_15_rate_max"], "outputs": ["WS13", "WS14", "WS15", "WS16", "WS17", "WS18"],
     "description": ("Year-keyed constant. JUDGMENT ITEM 4: the face says 'Multiply line 17 by 15%' with no "
                     "rounding instruction — whole-dollar ROUND HALF UP adopted to match the Tax Table "
                     "convention and TaxWise behavior (scenario Q9 pins 247.50 -> 248). Ken blesses or "
                     "changes at the review walk.")},
    {"rule_id": "R-QDCGT-05", "title": "WS19-WS21: 20% rate slice", "rule_type": "calculation",
     "precedence": 2, "sort_order": 15,
     "formula": "WS19 = WS9 + WS17; WS20 = WS10 - WS19; WS21 = ROUND_HALF_UP(0.20 * WS20, $1)",
     "inputs": [], "outputs": ["WS19", "WS20", "WS21"],
     "description": "Worksheet lines 19-21 verbatim; same rounding convention as WS18 (JUDGMENT ITEM 4)."},
    {"rule_id": "R-QDCGT-06", "title": "WS22/WS24: ordinary tax via the spine line-16 method", "rule_type": "calculation",
     "precedence": 2, "sort_order": 16,
     "formula": ("WS22 = tax(WS5): Tax Table semantics below $100,000, Tax Computation Worksheet at/above "
                 "(== spine compute_tax_line_16); WS24 = tax(WS1), same routing"),
     "inputs": [], "outputs": ["WS22", "WS24"],
     "description": ("Worksheet lines 22/24 verbatim ('use the Tax Table ... if $100,000 or more, use the Tax "
                     "Computation Worksheet'). REUSES spine R-TAX-01/R-TAX-02 — one tax method, two consumers; "
                     "inherits the accepted derived-2026-table interim and the unsupported-year hard stop.")},
    {"rule_id": "R-QDCGT-07", "title": "WS23/WS25: lesser-of finish -> 1040 line 16", "rule_type": "calculation",
     "precedence": 3, "sort_order": 17,
     "formula": "WS23 = WS18 + WS21 + WS22; WS25 = min(WS23, WS24); 1040.L16 = WS25",
     "inputs": [], "outputs": ["WS23", "WS25", "1040.L16"],
     "description": ("Worksheet lines 23-25 verbatim. The min() guarantees the worksheet never produces more "
                     "tax than ordinary rates (algebraic safety the IRS builds in). Writes line 16 "
                     "override-respecting, same convention as the spine.")},
    {"rule_id": "R-QDCGT-08", "title": "Partition identity: WS9 + WS17 + WS20 == WS10", "rule_type": "validation",
     "precedence": 4, "sort_order": 18,
     "formula": "WS9 + WS17 + WS20 == WS10 (0% + 15% + 20% slices partition the preferential income)",
     "inputs": [], "outputs": [],
     "description": ("Algebraic identity (WS19 = WS9 + WS17; WS20 = WS10 - WS19). Wired as a flow assertion — "
                     "a transcription error in any min/max line breaks the partition and fails by value.")},
    {"rule_id": "R-INTDIV-VAL-01", "title": "Qualified dividends cannot exceed ordinary dividends", "rule_type": "validation",
     "precedence": 0, "sort_order": 19,
     "formula": "L3a <= L3b (box 1b is 'the portion of the amount in box 1a' — 1099-DIV recipient instructions)",
     "inputs": ["div_box1b_qualified", "div_box1a_ordinary"], "outputs": [],
     "description": "ONCE PER RETURN. D_INTDIV_005 (error). Catches transposed 1a/1b entries — common keying error."},
    {"rule_id": "R-INTDIV-VAL-02", "title": "Per-document adjustments cannot exceed the document's income", "rule_type": "validation",
     "precedence": 0, "sort_order": 20,
     "formula": "per 1099-INT doc: box1 + box3 + box10 - box11 - box12 - nominee - accrued_adj >= 0 (warn below 0); per 1099-DIV doc: nominee <= box1a",
     "inputs": ["int_nominee_amount", "int_accrued_interest_adjustment", "div_nominee_amount"], "outputs": [],
     "description": "ONCE PER RETURN. D_INTDIV_006 (warning) — over-subtraction is almost always a keying error."},
]

INTDIV_LINES: list[dict] = [
    # Aggregated 1040 feeder lines (anchors for the line-status table + YELLOW totals in the UI)
    {"line_number": "agg_2a", "description": "Aggregated tax-exempt interest -> Form 1040 line 2a",
     "line_type": "total", "source_rules": ["R-AGG-2A"], "destination_form": "Form 1040 line 2a", "sort_order": 1},
    {"line_number": "agg_2b", "description": "Aggregated taxable interest (net of 8815) -> Form 1040 line 2b",
     "line_type": "total", "source_rules": ["R-AGG-2B"], "destination_form": "Form 1040 line 2b", "sort_order": 2},
    {"line_number": "agg_3a", "description": "Aggregated qualified dividends -> Form 1040 line 3a",
     "line_type": "total", "source_rules": ["R-AGG-3A"], "destination_form": "Form 1040 line 3a", "sort_order": 3},
    {"line_number": "agg_3b", "description": "Aggregated ordinary dividends -> Form 1040 line 3b",
     "line_type": "total", "source_rules": ["R-AGG-3B"], "destination_form": "Form 1040 line 3b", "sort_order": 4},
    {"line_number": "agg_7a", "description": "Capital gain distributions (Exception-1 path) -> Form 1040 line 7a",
     "line_type": "total", "source_rules": ["R-AGG-7A"], "destination_form": "Form 1040 line 7a", "sort_order": 5,
     "notes": "Only on the checkbox path; render checks the 7b 'Schedule D not required' box."},
    # QDCGT worksheet lines (statement-page render, never a faked IRS face)
    {"line_number": "ws_1", "description": "QDCGT WS1: taxable income (1040 line 15)", "line_type": "calculated",
     "source_rules": ["R-QDCGT-01"], "sort_order": 10},
    {"line_number": "ws_2", "description": "QDCGT WS2: qualified dividends (1040 line 3a)", "line_type": "calculated",
     "source_rules": ["R-QDCGT-01"], "sort_order": 11},
    {"line_number": "ws_3", "description": "QDCGT WS3: capital gain (no-Sch-D branch: 1040 line 7a)", "line_type": "calculated",
     "source_rules": ["R-QDCGT-01"], "sort_order": 12,
     "notes": "Topic 8 adds the Schedule D branch (smaller of Sch D 15/16; 0 if blank or loss)."},
    {"line_number": "ws_4", "description": "QDCGT WS4 = WS2 + WS3", "line_type": "calculated",
     "source_rules": ["R-QDCGT-01"], "sort_order": 13},
    {"line_number": "ws_5", "description": "QDCGT WS5 = max(0, WS1 - WS4) — ordinary-rate income", "line_type": "calculated",
     "source_rules": ["R-QDCGT-01"], "sort_order": 14},
    {"line_number": "ws_6", "description": "QDCGT WS6: maximum zero-rate amount (year/status constant)", "line_type": "calculated",
     "source_rules": ["R-QDCGT-02"], "sort_order": 15},
    {"line_number": "ws_7", "description": "QDCGT WS7 = min(WS1, WS6)", "line_type": "calculated",
     "source_rules": ["R-QDCGT-02"], "sort_order": 16},
    {"line_number": "ws_8", "description": "QDCGT WS8 = min(WS5, WS7)", "line_type": "calculated",
     "source_rules": ["R-QDCGT-02"], "sort_order": 17},
    {"line_number": "ws_9", "description": "QDCGT WS9 = WS7 - WS8 — amount taxed at 0%", "line_type": "calculated",
     "source_rules": ["R-QDCGT-02"], "sort_order": 18},
    {"line_number": "ws_10", "description": "QDCGT WS10 = min(WS1, WS4)", "line_type": "calculated",
     "source_rules": ["R-QDCGT-03"], "sort_order": 19},
    {"line_number": "ws_11", "description": "QDCGT WS11 = WS9", "line_type": "calculated",
     "source_rules": ["R-QDCGT-03"], "sort_order": 20},
    {"line_number": "ws_12", "description": "QDCGT WS12 = WS10 - WS11", "line_type": "calculated",
     "source_rules": ["R-QDCGT-03"], "sort_order": 21},
    {"line_number": "ws_13", "description": "QDCGT WS13: maximum 15%-rate amount (year/status constant)", "line_type": "calculated",
     "source_rules": ["R-QDCGT-04"], "sort_order": 22},
    {"line_number": "ws_14", "description": "QDCGT WS14 = min(WS1, WS13)", "line_type": "calculated",
     "source_rules": ["R-QDCGT-04"], "sort_order": 23},
    {"line_number": "ws_15", "description": "QDCGT WS15 = WS5 + WS9", "line_type": "calculated",
     "source_rules": ["R-QDCGT-04"], "sort_order": 24},
    {"line_number": "ws_16", "description": "QDCGT WS16 = max(0, WS14 - WS15)", "line_type": "calculated",
     "source_rules": ["R-QDCGT-04"], "sort_order": 25},
    {"line_number": "ws_17", "description": "QDCGT WS17 = min(WS12, WS16)", "line_type": "calculated",
     "source_rules": ["R-QDCGT-04"], "sort_order": 26},
    {"line_number": "ws_18", "description": "QDCGT WS18 = 15% x WS17 (ROUND HALF UP, whole dollars)", "line_type": "calculated",
     "source_rules": ["R-QDCGT-04"], "sort_order": 27},
    {"line_number": "ws_19", "description": "QDCGT WS19 = WS9 + WS17", "line_type": "calculated",
     "source_rules": ["R-QDCGT-05"], "sort_order": 28},
    {"line_number": "ws_20", "description": "QDCGT WS20 = WS10 - WS19 — amount taxed at 20%", "line_type": "calculated",
     "source_rules": ["R-QDCGT-05"], "sort_order": 29},
    {"line_number": "ws_21", "description": "QDCGT WS21 = 20% x WS20 (ROUND HALF UP, whole dollars)", "line_type": "calculated",
     "source_rules": ["R-QDCGT-05"], "sort_order": 30},
    {"line_number": "ws_22", "description": "QDCGT WS22 = tax(WS5) — Table < $100K / TCW at or above", "line_type": "calculated",
     "source_rules": ["R-QDCGT-06"], "sort_order": 31},
    {"line_number": "ws_23", "description": "QDCGT WS23 = WS18 + WS21 + WS22", "line_type": "calculated",
     "source_rules": ["R-QDCGT-07"], "sort_order": 32},
    {"line_number": "ws_24", "description": "QDCGT WS24 = tax(WS1) — same routing", "line_type": "calculated",
     "source_rules": ["R-QDCGT-06"], "sort_order": 33},
    {"line_number": "ws_25", "description": "QDCGT WS25 = min(WS23, WS24) -> Form 1040 line 16", "line_type": "total",
     "source_rules": ["R-QDCGT-07"], "destination_form": "Form 1040 line 16", "sort_order": 34},
]

INTDIV_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_INTDIV_001", "title": "1099-DIV box 2b/2c/2d present — Schedule D required (unsupported)",
     "severity": "error",
     "condition": "any 1099-DIV doc has box2b > 0 OR box2c > 0 OR box2d > 0",
     "message": ("Not supported — prepare manually: a 1099-DIV reports unrecaptured §1250 gain (2b), §1202 "
                 "gain (2c), or collectibles 28% gain (2d). Schedule D and the Schedule D Tax Worksheet are "
                 "required; line 16 is NOT computed."),
     "notes": "Exception 1 condition (2) verbatim. Line 16 stays blank (gate). Topic 8 narrows further; Sch D Tax Worksheet is post-sprint."},
    {"diagnostic_id": "D_INTDIV_002", "title": "Capital gain distributions without the Exception-1 assertion",
     "severity": "error",
     "condition": "SUM(div box2a) > 0 AND NOT (capital_gain_distributions_only AND all docs clean of 2b/2c/2d)",
     "message": ("Not supported — capital gain distributions are present but the 'Schedule D not required' "
                 "path is not asserted (or is blocked). Either assert capital-gain-distributions-only "
                 "(Exception 1) or prepare Schedule D manually; line 16 is NOT computed."),
     "notes": "Narrows spine D_1040_001 for the 7a-direct-entry / unasserted cases."},
    {"diagnostic_id": "D_INTDIV_003", "title": "Form 8814 child-income inclusion (unsupported)", "severity": "error",
     "condition": "child_dividends_3c_qualified OR child_dividends_3c_ordinary OR child_capgain_7b != 0",
     "message": ("Not supported — prepare manually: Form 8814 (child's interest/dividends election) inclusion "
                 "is flagged (line 3c / line 7b boxes). The election changes lines 3a/3b/7a and the line-16 "
                 "computation; line 16 is NOT computed."),
     "notes": "8814 is post-sprint backlog (Ken prioritizes)."},
    {"diagnostic_id": "D_INTDIV_004", "title": "Form 2555 with preferential-rate income (FEIE worksheet unsupported)",
     "severity": "error",
     "condition": "files_form_2555 AND (L3a > 0 OR L7a != 0)",
     "message": ("Not supported — compute line 16 manually: Form 2555 filers with qualified dividends or "
                 "capital gain use the Foreign Earned Income Tax Worksheet (which embeds a modified QDCGT); "
                 "line 16 is NOT computed."),
     "notes": "i1040gi p.37. files_form_2555 is the existing Taxpayer boolean (8812 gate)."},
    {"diagnostic_id": "D_INTDIV_005", "title": "Qualified dividends exceed ordinary dividends", "severity": "error",
     "condition": "L3a > L3b",
     "message": ("Line 3a (qualified) exceeds line 3b (ordinary). Box 1b is a SUBSET of box 1a — check for "
                 "transposed entries or an over-stated override."),
     "notes": "R-INTDIV-VAL-01."},
    {"diagnostic_id": "D_INTDIV_006", "title": "Document adjustments exceed its income", "severity": "warning",
     "condition": ("any 1099-INT doc nets below 0 (box1+box3+box10-box11-box12-nominee-accrued < 0) OR "
                   "any 1099-DIV doc has nominee > box1a"),
     "message": ("A 1099 document's nominee/accrued-interest/premium adjustments exceed its reported income — "
                 "verify the entries (the aggregate is NOT clamped)."),
     "notes": "R-INTDIV-VAL-02."},
    {"diagnostic_id": "D_INTDIV_007", "title": "Liquidation distributions present", "severity": "warning",
     "condition": "any 1099-DIV doc has box9 > 0 OR box10 > 0",
     "message": ("Cash/noncash liquidation distributions (boxes 9/10) reduce stock basis and become capital "
                 "gain once basis is exhausted (Pub 550) — manual treatment; nothing flows automatically."),
     "notes": "Stored fields only."},
    {"diagnostic_id": "D_INTDIV_008", "title": "Foreign tax paid on 1099-INT/DIV", "severity": "info",
     "condition": "SUM(int box6) + SUM(div box7) > 0",
     "message": ("Foreign tax paid is recorded on the document(s). The foreign tax credit entry (Schedule 3 "
                 "line 1, with or without Form 1116 under the $300/$600 election) is manual until a 1116 topic."),
     "notes": "Schedule 3 line 1 is direct-entry today (Topic 2)."},
    {"diagnostic_id": "D_INTDIV_009", "title": "Private activity bond interest (AMT preference)", "severity": "info",
     "condition": "SUM(int box9) + SUM(div box13) > 0",
     "message": ("Specified private activity bond interest is an AMT preference (Form 6251 line 2g). AMT is "
                 "deferred this sprint — the amount is stored, not computed."),
     "notes": "6251 is on the sprint DEFERRED list."},
    {"diagnostic_id": "D_INTDIV_010", "title": "Section 199A dividends stored for QBI", "severity": "info",
     "condition": "SUM(div box5) > 0",
     "message": ("Section 199A dividends (box 5) are stored and will flow to the QBI deduction when the "
                 "8995 topic lands (post-sprint #1) — no current-return effect."),
     "notes": "SPRINT_SCOPE Topic 3 DoD names this storage explicitly."},
]

INTDIV_SCENARIOS: list[dict] = [
    # ── Aggregation ──
    {"scenario_name": "ID-T1 — 2a/2b multi-document netting -> 2b = 2,375; 2a = 1,000",
     "scenario_type": "normal", "sort_order": 1,
     "inputs": {"int_docs": [
                    {"box1": 1000, "box3": 500, "box8": 900, "box10": 25, "box11": 100, "box12": 50, "box13": 100},
                    {"box1": 2000, "nominee": 300, "accrued": 200}],
                "div_docs": [{"box12": 200}],
                "sch_b_line_3_8815": 500},
     "expected_outputs": {"1040_line_2b": 2375, "1040_line_2a": 1000},
     "notes": ("Doc A nets 1000+500+25-100-50 = 1,375; doc B nets 2000-300-200 = 1,500; minus 8815 500 -> "
               "2,375. 2a: max(0, 900-100) = 800 + DIV box12 200 = 1,000. Every adjustment kind exercised "
               "with distinct values.")},
    {"scenario_name": "ID-T2 — 3a/3b/25b aggregation -> 3b = 2,600; 3a = 2,500; 25b = 400",
     "scenario_type": "normal", "sort_order": 2,
     "inputs": {"int_docs": [{"box4": 150}],
                "div_docs": [{"box1a": 2000, "box1b": 1500, "box4": 250},
                             {"box1a": 1000, "box1b": 1000, "nominee": 400}]},
     "expected_outputs": {"1040_line_3b": 2600, "1040_line_3a": 2500, "1040_line_25b": 400},
     "notes": "3b = 3,000 - 400 nominee; 3a = sum(1b) untouched by nominee; 25b spans BOTH document kinds."},
    {"scenario_name": "ID-T3 — line 7a checkbox path -> 7a = 2,000, 7b box checked",
     "scenario_type": "normal", "sort_order": 3,
     "inputs": {"capital_gain_distributions_only": True,
                "div_docs": [{"box2a": 1200}, {"box2a": 800}]},
     "expected_outputs": {"1040_line_7a": 2000, "line_7b_box_checked": True, "D_INTDIV_001_fires": False,
                          "D_INTDIV_002_fires": False},
     "notes": "Exception 1 satisfied: assertion + no 2b/2c/2d anywhere."},
    # ── QDCGT computes (Tax Table values via midpoint/half-up; TCW exact at >= $100K) ──
    {"scenario_name": "ID-Q1 — single TY2025, QD entirely in the 0% slice -> WS25 = 3,965",
     "scenario_type": "normal", "sort_order": 4,
     "inputs": {"filing_status": "single", "tax_year": 2025, "ws1_taxable_income": 40000, "ws2_qd": 5000, "ws3_cgd": 0},
     "expected_outputs": {"ws_5": 35000, "ws_9": 5000, "ws_17": 0, "ws_18": 0, "ws_20": 0, "ws_21": 0,
                          "ws_22": 3965, "ws_23": 3965, "ws_24": 4565, "ws_25": 3965, "1040_line_16": 3965},
     "notes": ("WS22 = table(35,000): mid 35,025 -> 1,192.50 + 12% x 23,100 = 3,964.50 -> 3,965. WS24 = "
               "table(40,000): mid 40,025 -> 4,564.50 -> 4,565. Savings = 600 = 12% x 5,000 (all QD at 0%).")},
    {"scenario_name": "ID-Q2 — single TY2025, QD straddles the 0% breakpoint -> WS25 = 4,907",
     "scenario_type": "normal", "sort_order": 5,
     "inputs": {"filing_status": "single", "tax_year": 2025, "ws1_taxable_income": 50350, "ws2_qd": 10000, "ws3_cgd": 0},
     "expected_outputs": {"ws_5": 40350, "ws_7": 48350, "ws_8": 40350, "ws_9": 8000, "ws_12": 2000,
                          "ws_16": 2000, "ws_17": 2000, "ws_18": 300, "ws_20": 0, "ws_21": 0,
                          "ws_22": 4607, "ws_23": 4907, "ws_24": 5997, "ws_25": 4907, "1040_line_16": 4907},
     "notes": ("8,000 at 0% + 2,000 at 15% (clean 300). WS22 = table(40,350): mid 40,375 -> 4,606.50 -> "
               "4,607. WS24 = table(50,350): mid 50,375 crosses into 22% -> 5,996.50 -> 5,997.")},
    {"scenario_name": "ID-Q3 — single TY2025, 20% reach at high income -> WS25 = 162,877.25",
     "scenario_type": "normal", "sort_order": 6,
     "inputs": {"filing_status": "single", "tax_year": 2025, "ws1_taxable_income": 600000, "ws2_qd": 100000, "ws3_cgd": 0},
     "expected_outputs": {"ws_5": 500000, "ws_9": 0, "ws_14": 533400, "ws_16": 33400, "ws_17": 33400,
                          "ws_18": 5010, "ws_20": 66600, "ws_21": 13320, "ws_22": 144547.25,
                          "ws_23": 162877.25, "ws_24": 179547.25, "ws_25": 162877.25, "1040_line_16": 162877.25},
     "notes": ("0% slice fully consumed (WS9 = 0 because WS5 > WS7). 33,400 at 15% + 66,600 at 20%. WS22/24 "
               "are TCW-exact cents: tax(500,000) = 57,231 + 35% x 249,475 = 144,547.25; tax(600,000) = "
               "179,547.25 (2025 single cumulative brackets).")},
    {"scenario_name": "ID-Q4 — MFJ TY2026 breakpoints + cap-gain distributions -> WS25 = 12,572",
     "scenario_type": "normal", "sort_order": 7,
     "inputs": {"filing_status": "mfj", "tax_year": 2026, "ws1_taxable_income": 110000, "ws2_qd": 12000,
                "ws3_cgd": 3000, "capital_gain_distributions_only": True},
     "expected_outputs": {"ws_4": 15000, "ws_5": 95000, "ws_6": 98900, "ws_9": 3900, "ws_13": 613700,
                          "ws_16": 11100, "ws_17": 11100, "ws_18": 1665, "ws_20": 0, "ws_21": 0,
                          "ws_22": 10907, "ws_23": 12572, "ws_24": 13624, "ws_25": 12572, "1040_line_16": 12572},
     "notes": ("TY2026 pins: WS6 = 98,900 / WS13 = 613,700 (RP 2025-32 §4.03). WS22 = derived-2026 "
               "table(95,000 MFJ): mid 95,025 -> 2,480 + 12% x 70,225 = 10,907 exact. WS24 = TCW(110,000) = "
               "11,600 + 22% x 9,200 = 13,624.00. 3,900 of the 15,000 preferential lands at 0%.")},
    {"scenario_name": "ID-Q9 — rounding-edge pin: WS18 = 247.50 -> 248 (HALF UP, flagged for Ken)",
     "scenario_type": "edge", "sort_order": 8,
     "inputs": {"filing_status": "single", "tax_year": 2025, "ws1_taxable_income": 50000, "ws2_qd": 10000, "ws3_cgd": 0},
     "expected_outputs": {"ws_9": 8350, "ws_17": 1650, "ws_18": 248, "ws_22": 4565, "ws_23": 4813,
                          "ws_24": 5920, "ws_25": 4813, "1040_line_16": 4813},
     "notes": ("JUDGMENT ITEM 4 pin: 0.15 x 1,650 = 247.50 -> 248 whole-dollar HALF UP. If Ken chooses "
               "cents-exact instead, this scenario changes to 247.50 / 4,812.50. WS22 = table(40,000) = "
               "4,565; WS24 = table(50,000): mid 50,025 -> 5,919.50 -> 5,920.")},
    {"scenario_name": "ID-Q10 — MFS TY2025 boundary: TI exactly at the 0% breakpoint -> all QD at 0%",
     "scenario_type": "boundary", "sort_order": 9,
     "inputs": {"filing_status": "mfs", "tax_year": 2025, "ws1_taxable_income": 48350, "ws2_qd": 5000, "ws3_cgd": 0},
     "expected_outputs": {"ws_6": 48350, "ws_9": 5000, "ws_12": 0, "ws_17": 0, "ws_18": 0,
                          "ws_22": 4967, "ws_23": 4967, "ws_24": 5567, "ws_25": 4967, "1040_line_16": 4967},
     "notes": ("Boundary pair (lower): TI == WS6 -> the entire QD rides 0%. WS22 = table(43,350): mid "
               "43,375 -> 4,966.50 -> 4,967; WS24 = table(48,350): mid 48,375 -> 5,566.50 -> 5,567.")},
    {"scenario_name": "ID-Q11 — MFS TY2025 boundary partner: TI $200 above -> 200 at 15%",
     "scenario_type": "boundary", "sort_order": 10,
     "inputs": {"filing_status": "mfs", "tax_year": 2025, "ws1_taxable_income": 48550, "ws2_qd": 5000, "ws3_cgd": 0},
     "expected_outputs": {"ws_9": 4800, "ws_12": 200, "ws_16": 200, "ws_17": 200, "ws_18": 30,
                          "ws_22": 4991, "ws_23": 5021, "ws_24": 5601, "ws_25": 5021, "1040_line_16": 5021},
     "notes": ("Boundary pair (upper): 4,800 at 0%, 200 at 15% (30). WS22 = table(43,550): mid 43,575 -> "
               "4,990.50 -> 4,991; WS24 = table(48,550): mid 48,575 crosses 48,475 into 22% -> 5,600.50 -> 5,601.")},
    {"scenario_name": "ID-Q12 — HOH TY2025 distinct breakpoints -> WS25 = 8,201",
     "scenario_type": "normal", "sort_order": 11,
     "inputs": {"filing_status": "hoh", "tax_year": 2025, "ws1_taxable_income": 71150, "ws2_qd": 8000, "ws3_cgd": 0},
     "expected_outputs": {"ws_5": 63150, "ws_6": 64750, "ws_9": 1600, "ws_12": 6400, "ws_16": 6400,
                          "ws_17": 6400, "ws_18": 960, "ws_22": 7241, "ws_23": 8201, "ws_24": 8834,
                          "ws_25": 8201, "1040_line_16": 8201},
     "notes": ("HOH-specific 64,750/566,700. WS22 = table(63,150): mid 63,175 -> 1,700 + 12% x 46,175 = "
               "7,241 exact. WS24 = table(71,150): mid 71,175 -> 7,442 + 22% x 6,325 = 8,833.50 -> 8,834.")},
    # ── Gates ──
    {"scenario_name": "ID-G1 — box 2b blocks the checkbox path; line 16 not computed",
     "scenario_type": "failure", "sort_order": 12,
     "inputs": {"capital_gain_distributions_only": True,
                "div_docs": [{"box2a": 1000, "box2b": 50}]},
     "expected_outputs": {"D_INTDIV_001_fires": True, "16_not_computed": True},
     "notes": "Exception 1 condition (2) violated even WITH the assertion — the documents win."},
    {"scenario_name": "ID-G2 — cap-gain distributions without the assertion; line 16 not computed",
     "scenario_type": "failure", "sort_order": 13,
     "inputs": {"div_docs": [{"box2a": 1000}]},
     "expected_outputs": {"D_INTDIV_002_fires": True, "16_not_computed": True},
     "notes": "The narrowed bridge: unasserted 2a -> Sch D path -> RED."},
    {"scenario_name": "ID-G3 — Form 2555 with qualified dividends; line 16 not computed",
     "scenario_type": "failure", "sort_order": 14,
     "inputs": {"files_form_2555": True, "div_docs": [{"box1a": 2000, "box1b": 2000}]},
     "expected_outputs": {"D_INTDIV_004_fires": True, "16_not_computed": True},
     "notes": "FEIE Tax Worksheet path (i1040gi p.37) is unsupported this sprint."},
    {"scenario_name": "ID-G4 — qualified > ordinary fires D_INTDIV_005",
     "scenario_type": "failure", "sort_order": 15,
     "inputs": {"div_docs": [{"box1a": 1500, "box1b": 2000}]},
     "expected_outputs": {"D_INTDIV_005_fires": True},
     "notes": "Transposed 1a/1b keying error."},
]

INTDIV_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-AGG-2B", "IRS_2025_SCHB_INSTR", "primary", "Line 1 roster + nominee/accrued/ABP adjustment conventions (verbatim)"),
    ("R-AGG-2B", "IRS_1099INT_FORM", "primary", "Box semantics: box 3 not in box 1; boxes 10/11/12"),
    ("R-AGG-2B", "IRS_2025_1040_INSTR", "secondary", "Line 2b: Sch B over $1,500 + Pub 550 pointers"),
    ("R-AGG-2A", "IRS_2025_SCHB_INSTR", "primary", "Tax-exempt netting 'excess over premium' + DIV box 12 (verbatim)"),
    ("R-AGG-2A", "IRS_1099DIV_FORM", "primary", "Box 12 exempt-interest dividends / box 13 PAB subset"),
    ("R-AGG-3B", "IRS_2025_1040_INSTR", "primary", "Line 3b <- box 1a; nominee -> Sch B"),
    ("R-AGG-3B", "IRS_1099DIV_FORM", "primary", "Box 1a definition"),
    ("R-AGG-3A", "IRS_2025_1040_INSTR", "primary", "Line 3a <- box 1b + the holding-period Exception list"),
    ("R-AGG-3A", "IRS_1099DIV_FORM", "primary", "Box 1b 'portion of box 1a' (subset)"),
    ("R-AGG-7A", "IRS_2025_1040_INSTR", "primary", "Exception 1 + the 7a/7b checkbox mechanics (verbatim)"),
    ("R-AGG-25B", "IRS_1099DIV_FORM", "primary", "Box 4 'include this amount ... as tax withheld'"),
    ("R-AGG-25B", "IRS_1099INT_FORM", "secondary", "Box 4 backup withholding (existing 25b source)"),
    ("R-QDCGT-GATE", "IRS_2025_1040_INSTR", "primary", "Line 16 trigger list + 'use this worksheet to figure your tax'"),
    ("R-QDCGT-01", "IRS_2025_1040_INSTR", "primary", "WS lines 1-5 verbatim (p.38)"),
    ("R-QDCGT-02", "RP_2024_40", "primary", "TY2025 zero-rate maxima (§2.03)"),
    ("R-QDCGT-02", "RP_2025_32", "primary", "TY2026 zero-rate maxima (§4.03)"),
    ("R-QDCGT-02", "IRS_2025_1040_INSTR", "primary", "WS6/WS7/WS8/WS9 verbatim incl. QSS-uses-MFJ"),
    ("R-QDCGT-02", "IRC_1", "secondary", "§1(h)/§1(j)(5)(B) preferential rate structure"),
    ("R-QDCGT-03", "IRS_2025_1040_INSTR", "primary", "WS lines 10-12 verbatim"),
    ("R-QDCGT-04", "RP_2024_40", "primary", "TY2025 15%-rate maxima (§2.03)"),
    ("R-QDCGT-04", "RP_2025_32", "primary", "TY2026 15%-rate maxima (§4.03)"),
    ("R-QDCGT-04", "IRS_2025_1040_INSTR", "primary", "WS lines 13-18 verbatim"),
    ("R-QDCGT-05", "IRS_2025_1040_INSTR", "primary", "WS lines 19-21 verbatim"),
    ("R-QDCGT-06", "IRS_2025_1040_INSTR", "primary", "WS lines 22/24: Table < $100K / TCW at or above (verbatim)"),
    ("R-QDCGT-07", "IRS_2025_1040_INSTR", "primary", "WS lines 23-25: smaller-of finish -> line 16 (verbatim)"),
    ("R-QDCGT-08", "IRS_2025_1040_INSTR", "secondary", "Partition identity derived from WS lines 9/17/19/20"),
    ("R-INTDIV-VAL-01", "IRS_1099DIV_FORM", "primary", "Box 1b is 'the portion of the amount in box 1a'"),
    ("R-INTDIV-VAL-02", "IRS_2025_SCHB_INSTR", "primary", "Adjustment rows subtract from the payer subtotal"),
]


# ═══════════════════════════════════════════════════════════════════════════
# SCH_B — Schedule B (Form 1040): Interest and Ordinary Dividends
# ═══════════════════════════════════════════════════════════════════════════

SCHB_IDENTITY = {
    "form_number": "SCH_B",
    "form_title": "Schedule B (Form 1040) — Interest and Ordinary Dividends (TY2025)",
    "notes": (
        "Sprint Topic 3. LISTING FORM: Parts I/II render from the 1099-INT/DIV "
        "documents (payer name + amount rows, with the i1040sb subtotal-adjustment "
        "convention for Nominee Distribution / Accrued Interest / ABP Adjustment "
        "rows; seller-financed entries list FIRST with buyer SSN + address). The "
        "only schedule-level inputs are line 3 (Form 8815 exclusion) and the Part "
        "III answers. Line 4 -> 1040 line 2b and line 6 -> 1040 line 3b are "
        "STRUCTURALLY equal to the 1040_INTDIV aggregates (one roster, two "
        "presentations — they cannot diverge). 2025 face: 14 Part-I payer rows, "
        "15 Part-II rows (overflow -> continuation statement, render leg). The "
        "schedule prints when REQUIRED (R-SB-04), not merely when nonzero."
    ),
}

SCHB_FACTS: list[dict] = [
    {"fact_key": "form_8815_exclusion", "label": "Excludable series EE/I savings bond interest — Form 8815 (line 3)",
     "data_type": "decimal", "default_value": "0", "sort_order": 1,
     "notes": ("Direct entry; Form 8815 itself is NOT built — D_SCHB_005 warns (attachment-not-generated, "
               "Topic 2 convention). Subtracts inside R-AGG-2B so line 4 == 1040 line 2b always.")},
    {"fact_key": "foreign_account_yes", "label": "Part III 7a question 1: foreign financial account? (Yes/No)",
     "data_type": "boolean", "sort_order": 2,
     "notes": "Nullable three-state in the app (unanswered representable — digital-asset convention). D_SCHB_001."},
    {"fact_key": "fbar_required_yes", "label": "Part III 7a question 2: required to file FinCEN Form 114? (Yes/No)",
     "data_type": "boolean", "sort_order": 3,
     "notes": "Required only when question 1 = Yes. $10,000 aggregate threshold is the PREPARER's call (i1040sb). D_SCHB_002."},
    {"fact_key": "foreign_countries_list", "label": "Part III 7b: foreign country(-ies) where accounts are located",
     "data_type": "string", "sort_order": 4, "notes": "Required when question 2 = Yes. D_SCHB_003."},
    {"fact_key": "foreign_trust_yes", "label": "Part III 8: foreign trust distribution/grantor/transferor? (Yes/No)",
     "data_type": "boolean", "sort_order": 5,
     "notes": "Yes -> Form 3520 may be required (filed separately, never attached). D_SCHB_004."},
]

SCHB_RULES: list[dict] = [
    {"rule_id": "R-SB-01", "title": "Line 2 = add the amounts on line 1 (incl. adjustment rows)", "rule_type": "calculation",
     "precedence": 1, "sort_order": 1,
     "formula": ("L2 = SUM(line-1 payer rows) where the rows are: per-doc gross (box1 + box3 + box10), then "
                 "subtotal, then NEGATIVE adjustment rows ('Nominee Distribution', 'Accrued Interest', "
                 "'ABP Adjustment' = boxes 11+12) per i1040sb. Numerically == the 1040_INTDIV 2b roster "
                 "BEFORE the 8815 subtraction."),
     "inputs": [], "outputs": ["L2"],
     "description": ("ONCE PER RETURN. The listing presentation of R-AGG-2B's roster: gross rows + adjustment "
                     "rows rather than per-doc nets, so the printed face matches IRS convention while the "
                     "math stays identical.")},
    {"rule_id": "R-SB-02", "title": "Line 4 = line 2 - line 3 -> Form 1040 line 2b", "rule_type": "calculation",
     "precedence": 2, "sort_order": 2,
     "formula": "L4 = L2 - L3(form_8815_exclusion). Writes/ties to Form 1040 line 2b.",
     "inputs": ["form_8815_exclusion"], "outputs": ["L4", "1040.L2b"],
     "description": ("ONCE PER RETURN. Face verbatim. STRUCTURAL TIE: R-AGG-2B subtracts the same 8815 fact, "
                     "so Schedule B line 4 and 1040 line 2b are the same number by construction (flow "
                     "assertion FA-1040-SCHB-02 pins it).")},
    {"rule_id": "R-SB-03", "title": "Line 6 = add the amounts on line 5 -> Form 1040 line 3b", "rule_type": "calculation",
     "precedence": 2, "sort_order": 3,
     "formula": ("L6 = SUM(line-5 payer rows incl. the Part II 'Nominee Distribution' negative row) "
                 "== the R-AGG-3B roster. Writes/ties to Form 1040 line 3b."),
     "inputs": [], "outputs": ["L6", "1040.L3b"],
     "description": "ONCE PER RETURN. Face verbatim."},
    {"rule_id": "R-SB-04", "title": "Schedule B REQUIRED when any of the eight i1040sb triggers applies", "rule_type": "routing",
     "precedence": 0, "sort_order": 4,
     "formula": ("required = (taxable interest > 1500) OR (ordinary dividends > 1500) OR seller-financed "
                 "interest OR accrued-interest adjustment OR OID adjustment OR ABP adjustment OR 8815 "
                 "exclusion OR nominee (either kind) OR foreign account/trust answers triggering Part III"),
     "inputs": ["form_8815_exclusion", "foreign_account_yes", "foreign_trust_yes"], "outputs": [],
     "description": ("ONCE PER RETURN. i1040sb General Instructions verbatim list. This is the RENDER gate: "
                     "the schedule prints when required (not merely when totals are nonzero). The $1,500 "
                     "thresholds are STATUTORY-FORM constants (not inflation-indexed; re-verify each year's "
                     "face — same convention as the Topic 2 faces).")},
    {"rule_id": "R-SB-05", "title": "Part III required when (a) over $1,500 either kind, (b) foreign account, (c) foreign trust",
     "rule_type": "validation", "precedence": 0, "sort_order": 5,
     "formula": ("part_iii_required = (L4 > 1500 OR L6 > 1500 OR foreign_account_yes OR foreign_trust_yes); "
                 "then: 7a question 1 must be ANSWERED (Yes or No); question 2 required when Q1 = Yes; "
                 "7b countries required when Q2 = Yes; line 8 must be ANSWERED."),
     "inputs": ["foreign_account_yes", "fbar_required_yes", "foreign_countries_list", "foreign_trust_yes"],
     "outputs": [],
     "description": ("ONCE PER RETURN. Face verbatim gate (a)/(b)/(c). Unanswered = NULL (three-state "
                     "booleans, digital-asset convention) — the face never guesses. D_SCHB_001/002/003.")},
    {"rule_id": "R-SB-06", "title": "Listing conventions: seller-financed first + buyer SSN; brokerage firm-name rows",
     "rule_type": "classification", "precedence": 0, "sort_order": 6,
     "formula": ("seller-financed entries list FIRST with buyer name/address/SSN (face + i1040sb; $50 penalty "
                 "exposure); brokerage 1099-INT/DIV: list the FIRM as payer with the form total"),
     "inputs": [], "outputs": [],
     "description": "ONCE PER RETURN. Render-leg conventions pinned at spec level. D_SCHB_006 polices the buyer SSN."},
]

SCHB_LINES: list[dict] = [
    {"line_number": "1", "description": "Part I: interest payer listing (name + amount; 14 rows on the face)",
     "line_type": "informational", "source_rules": ["R-SB-01", "R-SB-06"], "sort_order": 1,
     "notes": "MODEL-DRIVEN from the 1099-INT documents (widgets f1_03..f1_30 pairs). Overflow -> continuation statement."},
    {"line_number": "2", "description": "Add the amounts on line 1", "line_type": "subtotal",
     "source_rules": ["R-SB-01"], "sort_order": 2, "notes": "Widget f1_31."},
    {"line_number": "3", "description": "Excludable EE/I savings bond interest — attach Form 8815", "line_type": "input",
     "source_rules": ["R-SB-02"], "sort_order": 3, "notes": "Widget f1_32. D_SCHB_005 (8815 not generated)."},
    {"line_number": "4", "description": "Subtract line 3 from line 2 -> Form 1040 line 2b", "line_type": "total",
     "source_rules": ["R-SB-02"], "destination_form": "Form 1040 line 2b", "sort_order": 4,
     "notes": "Widget f1_33. Over $1,500 -> Part III."},
    {"line_number": "5", "description": "Part II: ordinary dividend payer listing (name + amount; 15 rows)",
     "line_type": "informational", "source_rules": ["R-SB-03", "R-SB-06"], "sort_order": 5,
     "notes": "MODEL-DRIVEN from the 1099-DIV documents (widgets f1_34..f1_63 pairs)."},
    {"line_number": "6", "description": "Add the amounts on line 5 -> Form 1040 line 3b", "line_type": "total",
     "source_rules": ["R-SB-03"], "destination_form": "Form 1040 line 3b", "sort_order": 6,
     "notes": "Widget f1_64. Over $1,500 -> Part III."},
    {"line_number": "7a_q1", "description": "Part III 7a: foreign financial account? Yes/No", "line_type": "input",
     "source_rules": ["R-SB-05"], "sort_order": 7, "notes": "Checkbox group c1_1[0]/[1]."},
    {"line_number": "7a_q2", "description": "Part III 7a: required to file FinCEN Form 114? Yes/No", "line_type": "input",
     "source_rules": ["R-SB-05"], "sort_order": 8, "notes": "Checkbox group c1_2[0]/[1]; only when Q1 = Yes."},
    {"line_number": "7b", "description": "Part III 7b: foreign country(-ies) list", "line_type": "input",
     "source_rules": ["R-SB-05"], "sort_order": 9, "notes": "Widgets f1_65/f1_66."},
    {"line_number": "8", "description": "Part III 8: foreign trust distribution/grantor/transferor? Yes/No",
     "line_type": "input", "source_rules": ["R-SB-05"], "sort_order": 10,
     "notes": "Checkbox group c1_3[0]/[1]. Yes -> Form 3520 (filed separately)."},
]

SCHB_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_SCHB_001", "title": "Part III required but question 7a-1 unanswered", "severity": "error",
     "condition": "part_iii_required AND foreign_account_yes is NULL",
     "message": ("Schedule B Part III is required (over $1,500 of interest/dividends, or foreign "
                 "account/trust) — answer question 7a (foreign financial account Yes/No)."),
     "notes": "R-SB-05. Also fires for an unanswered line 8 under the same gate."},
    {"diagnostic_id": "D_SCHB_002", "title": "7a question 1 = Yes but question 2 unanswered", "severity": "error",
     "condition": "foreign_account_yes is True AND fbar_required_yes is NULL",
     "message": ("You answered Yes to a foreign financial account — answer 7a question 2 (FinCEN Form 114 "
                 "required?). The $10,000 aggregate-value threshold determines the answer (see FinCEN 114 "
                 "instructions)."),
     "notes": "R-SB-05."},
    {"diagnostic_id": "D_SCHB_003", "title": "FBAR required but no countries listed on 7b", "severity": "error",
     "condition": "fbar_required_yes is True AND foreign_countries_list blank",
     "message": "Question 2 is Yes — list the foreign country(-ies) where the account(s) are located (line 7b).",
     "notes": "R-SB-05."},
    {"diagnostic_id": "D_SCHB_004", "title": "Foreign trust answer Yes — Form 3520 not generated", "severity": "warning",
     "condition": "foreign_trust_yes is True",
     "message": ("Line 8 is Yes — Form 3520 may be required. It is NOT generated by the software and is "
                 "filed SEPARATELY (never attached to the 1040). See the Form 3520 instructions."),
     "notes": "Attachment-not-generated convention (it is not even an attachment — separate filing)."},
    {"diagnostic_id": "D_SCHB_005", "title": "Form 8815 exclusion entered — form not generated", "severity": "warning",
     "condition": "form_8815_exclusion > 0",
     "message": ("Line 3 carries a series EE/I savings bond exclusion — Form 8815 is not generated yet; "
                 "attach the manually prepared form. (The exclusion math, incl. its MAGI phaseout, is the "
                 "preparer's until an 8815 topic.)"),
     "notes": "Topic 2 attachment convention."},
    {"diagnostic_id": "D_SCHB_006", "title": "Seller-financed mortgage entry missing buyer SSN/address", "severity": "error",
     "condition": "any seller-financed 1099-INT doc lacks buyer SSN (NNN-NN-NNNN) or address",
     "message": ("Seller-financed mortgage interest must list the buyer's name, address, and SSN first on "
                 "Schedule B line 1 — a missing/invalid buyer SSN exposes a $50 penalty (i1040sb)."),
     "notes": "R-SB-06. SSN format is MeF-typed at entry; this polices presence."},
    {"diagnostic_id": "D_SCHB_007", "title": "FinCEN Form 114 reminder", "severity": "info",
     "condition": "fbar_required_yes is True",
     "message": ("FinCEN Form 114 (FBAR) is filed electronically with FinCEN — NOT with this return. "
                 "Willful failure carries penalties up to the greater of $100,000 or 50% of the account."),
     "notes": "i1040sb caution, surfaced as a courtesy reminder."},
]

SCHB_SCENARIOS: list[dict] = [
    {"scenario_name": "SB-T1 — listing math: L2 = 2,875; L4 = 2,375 ties 1040 2b",
     "scenario_type": "normal", "sort_order": 1,
     "inputs": {"int_docs": [
                    {"payer": "Bank A", "box1": 1000, "box3": 500, "box10": 25, "box11": 100, "box12": 50},
                    {"payer": "Bank B", "box1": 2000, "nominee": 300, "accrued": 200}],
                "form_8815_exclusion": 500},
     "expected_outputs": {"2": 2875, "4": 2375, "1040_line_2b": 2375},
     "notes": ("Same fixture as ID-T1: gross rows 1,525 + 2,000 = 3,525, adjustment rows -150 (ABP) "
               "-300 (nominee) -200 (accrued) -> subtotal convention nets 2,875; minus 8815 500 = 2,375. "
               "The Sch B face and the 1040 line are the same roster.")},
    {"scenario_name": "SB-T2 — Part II nominee: L6 = 2,600 ties 1040 3b",
     "scenario_type": "normal", "sort_order": 2,
     "inputs": {"div_docs": [{"payer": "Broker X", "box1a": 2000}, {"payer": "Broker Y", "box1a": 1000, "nominee": 400}]},
     "expected_outputs": {"6": 2600, "1040_line_3b": 2600},
     "notes": "Rows 2,000 + 1,000, 'Nominee Distribution' row -400."},
    {"scenario_name": "SB-DG1 — $1,600 interest requires Part III; unanswered 7a fires D_SCHB_001",
     "scenario_type": "failure", "sort_order": 3,
     "inputs": {"int_docs": [{"payer": "Bank A", "box1": 1600}]},
     "expected_outputs": {"schedule_b_required": True, "part_iii_required": True, "D_SCHB_001_fires": True},
     "notes": "Threshold gate (a): taxable interest over $1,500."},
    {"scenario_name": "SB-DG2 — 7a Yes chain: unanswered Q2 then missing countries",
     "scenario_type": "failure", "sort_order": 4,
     "inputs": {"int_docs": [{"payer": "Bank A", "box1": 100}], "foreign_account_yes": True},
     "expected_outputs": {"schedule_b_required": True, "part_iii_required": True, "D_SCHB_002_fires": True},
     "notes": "Gate (b): foreign account forces Part III regardless of the $1,500 thresholds. With fbar_required_yes=True and blank 7b, D_SCHB_003 fires instead."},
    {"scenario_name": "SB-DG3 — seller-financed entry without buyer SSN fires D_SCHB_006",
     "scenario_type": "failure", "sort_order": 5,
     "inputs": {"int_docs": [{"payer": "Buyer (seller-financed)", "box1": 9000, "seller_financed": True}]},
     "expected_outputs": {"schedule_b_required": True, "D_SCHB_006_fires": True},
     "notes": "Seller-financed is itself a required-trigger (gate independent of $1,500)."},
    {"scenario_name": "SB-T3 — under both thresholds, no triggers: Schedule B NOT required",
     "scenario_type": "normal", "sort_order": 6,
     "inputs": {"int_docs": [{"payer": "Bank A", "box1": 800}], "div_docs": [{"payer": "Broker X", "box1a": 900}]},
     "expected_outputs": {"schedule_b_required": False, "1040_line_2b": 800, "1040_line_3b": 900},
     "notes": "The 1040 lines still compute from the documents — only the schedule's print gate is off."},
]

SCHB_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-SB-01", "IRS_2025_SCHB_FORM", "primary", "Line 2 verbatim: add the amounts on line 1"),
    ("R-SB-01", "IRS_2025_SCHB_INSTR", "primary", "Subtotal-adjustment row convention (verbatim)"),
    ("R-SB-02", "IRS_2025_SCHB_FORM", "primary", "Line 4 verbatim: L2 - L3 -> 1040 line 2b"),
    ("R-SB-03", "IRS_2025_SCHB_FORM", "primary", "Line 6 verbatim -> 1040 line 3b"),
    ("R-SB-04", "IRS_2025_SCHB_INSTR", "primary", "The eight required-use triggers (verbatim list)"),
    ("R-SB-05", "IRS_2025_SCHB_FORM", "primary", "Part III gate (a)/(b)/(c) + questions 7a/7b/8 (verbatim)"),
    ("R-SB-05", "IRS_2025_SCHB_INSTR", "secondary", "FBAR $10,000 threshold + Form 8938 note"),
    ("R-SB-06", "IRS_2025_SCHB_FORM", "primary", "Seller-financed list-first + buyer SSN (face caption)"),
    ("R-SB-06", "IRS_2025_SCHB_INSTR", "primary", "$50 penalty + brokerage firm-name convention"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS (12) — every aggregate, the worksheet, and the gates
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-INTDIV-01", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "2b roster: box1 + box3 + box10 - box11 - box12 - nominee - accrued, minus 8815",
     "description": ("Validates R-AGG-2B with distinct values per box. Bugs it catches: box 3 treated as a "
                     "subset of box 1; premiums added instead of subtracted; the 8815 exclusion dropped "
                     "(line 4 would diverge from 2b)."),
     "definition": {"kind": "sum_check", "form": "1040_INTDIV", "output": "agg_2b",
                    "sum_of": ["int_box1_interest", "int_box3_treasury", "int_box10_market_discount",
                               "-int_box11_bond_premium", "-int_box12_treasury_premium",
                               "-int_nominee_amount", "-int_accrued_interest_adjustment",
                               "-SCH_B.L3"],
                    "allow_negative_addends": True,
                    "must_write_to": {"form": "1040", "line": "2b"}},
     "sort_order": 1},
    {"assertion_id": "FA-1040-INTDIV-02", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "2a roster: per-doc max(0, box8 - box13) + DIV box12",
     "description": ("Validates R-AGG-2A. Bugs it catches: forgetting the DIV box-12 addend; netting below "
                     "zero per document; box 9 (PAB subset) leaking in as an addend."),
     "definition": {"kind": "sum_check", "form": "1040_INTDIV", "output": "agg_2a",
                    "sum_of": ["max0(int_box8_tax_exempt - int_box13_exempt_premium)",
                               "div_box12_exempt_interest_div"],
                    "excludes": ["int_box9_pab", "div_box13_pab_div"],
                    "must_write_to": {"form": "1040", "line": "2a"}},
     "sort_order": 2},
    {"assertion_id": "FA-1040-INTDIV-03", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "3b = sum(box1a) - sum(nominee); 3a = sum(box1b)",
     "description": ("Validates R-AGG-3A/3B. Bugs it catches: nominee subtracted from 3a instead of 3b; "
                     "1a/1b cross-wired."),
     "definition": {"kind": "sum_check", "form": "1040_INTDIV", "output": "agg_3b",
                    "sum_of": ["div_box1a_ordinary", "-div_nominee_amount"],
                    "companion": {"output": "agg_3a", "sum_of": ["div_box1b_qualified"]},
                    "must_write_to": {"form": "1040", "line": "3b"}},
     "sort_order": 3},
    {"assertion_id": "FA-1040-INTDIV-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "25b roster includes BOTH 1099-INT box 4 and 1099-DIV box 4",
     "description": ("Validates R-AGG-25B (extends spine R-PAY-02). Bug it catches: the DIV withholding "
                     "addend silently dropped when the dividend model lands."),
     "definition": {"kind": "sum_check", "form": "1040_INTDIV", "output": "L25b",
                    "sum_of": ["int_box4_fed_withheld", "div_box4_fed_withheld"],
                    "must_write_to": {"form": "1040", "line": "25b"}},
     "sort_order": 4},
    {"assertion_id": "FA-1040-INTDIV-05", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "7a checkbox path truth table (Exception 1)",
     "description": ("Validates R-AGG-7A: assertion + clean docs -> 7a = sum(2a) + box checked; any 2b/2c/2d "
                     "or missing assertion -> 7a not computed + RED + line 16 blank."),
     "definition": {"kind": "gating_check", "form": "1040_INTDIV",
                    "truth_table": [
                        {"asserted": True, "docs_clean": True, "sum_2a_positive": True,
                         "expect": {"7a_computed": True, "box_checked": True, "line16_path": "qdcgt"}},
                        {"asserted": True, "docs_clean": False, "sum_2a_positive": True,
                         "expect": {"7a_computed": False, "D_INTDIV_001": True, "line16_blank": True}},
                        {"asserted": False, "docs_clean": True, "sum_2a_positive": True,
                         "expect": {"7a_computed": False, "D_INTDIV_002": True, "line16_blank": True}},
                        {"asserted": False, "docs_clean": True, "sum_2a_positive": False,
                         "expect": {"7a_computed": False, "no_red": True}}]},
     "sort_order": 5},
    {"assertion_id": "FA-1040-INTDIV-06", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "QDCGT breakpoint constants per year per filing status",
     "description": ("Pins WS6/WS13 for both years against the rev procs: TY2025 48,350/96,700/64,750 zero-"
                     "rate and 533,400/300,000/600,050/566,700 15%-rate; TY2026 49,450/98,900/66,200 and "
                     "545,500/306,850/613,700/579,600. QSS == MFJ. Bug it catches: single/MFS collapsed on "
                     "WS13 (they differ there, unlike WS6)."),
     "definition": {"kind": "constants_check", "form": "1040_INTDIV",
                    "constants": {
                        "2025": {"zero_rate": {"single": 48350, "mfs": 48350, "mfj": 96700, "qss": 96700, "hoh": 64750},
                                 "rate_15": {"single": 533400, "mfs": 300000, "mfj": 600050, "qss": 600050, "hoh": 566700}},
                        "2026": {"zero_rate": {"single": 49450, "mfs": 49450, "mfj": 98900, "qss": 98900, "hoh": 66200},
                                 "rate_15": {"single": 545500, "mfs": 306850, "mfj": 613700, "qss": 613700, "hoh": 579600}}}},
     "sort_order": 6},
    {"assertion_id": "FA-1040-INTDIV-07", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Partition identity: WS9 + WS17 + WS20 == WS10 whenever the worksheet runs",
     "description": ("Validates R-QDCGT-08. The 0%/15%/20% slices must exactly partition min(TI, preferential "
                     "income) — any transcription error in the min/max ladder breaks it by value."),
     "definition": {"kind": "formula_check", "form": "1040_INTDIV",
                    "formula": "WS9 + WS17 + WS20 == WS10"},
     "sort_order": 7},
    {"assertion_id": "FA-1040-INTDIV-08", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "WS25 = min(WS23, WS24) writes 1040 line 16 (override-respecting)",
     "description": ("Validates R-QDCGT-07. Bugs it catches: max instead of min; the worksheet result not "
                     "landing on line 16; an override being clobbered."),
     "definition": {"kind": "formula_check", "form": "1040_INTDIV",
                    "formula": "WS25 == min(WS23, WS24)",
                    "must_write_to": {"form": "1040", "line": "16"}},
     "sort_order": 8},
    {"assertion_id": "FA-1040-INTDIV-09", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "WS22/WS24 use the spine line-16 tax method (Table < $100K / TCW at or above)",
     "description": ("Validates R-QDCGT-06: the worksheet's ordinary-tax legs route through "
                     "compute_tax_line_16 (one method, two consumers) — never raw brackets below $100K."),
     "definition": {"kind": "source_check", "form": "1040_INTDIV",
                    "source_contains": "compute_tax_line_16", "applies_to": ["WS22", "WS24"]},
     "sort_order": 9},
    {"assertion_id": "FA-1040-INTDIV-10", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "QDCGT gate blockers blank line 16 (2b/2c/2d, unasserted 2a, 2555, 8814)",
     "description": ("Validates R-QDCGT-GATE: every unsupported path leaves line 16 BLANK with its RED "
                     "(D_INTDIV_001/002/003/004) — never a silently-wrong table-only tax. Supersedes the "
                     "spine bridge (FA-1040-SPINE-15 retires with D_1040_001 at the build leg)."),
     "definition": {"kind": "gating_check", "form": "1040_INTDIV",
                    "blockers": ["div_2b2c2d_present", "capgain_dist_unasserted", "files_form_2555_with_pref_income",
                                 "form_8814_inclusion"],
                    "expect": {"line16_blank": True, "red_fires": True}},
     "sort_order": 10},
    # ── Schedule B ──
    {"assertion_id": "FA-1040-SCHB-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Sch B line 4 = line 2 - line 3 and EQUALS 1040 line 2b",
     "description": ("Validates R-SB-02 + the structural tie: the schedule face and the 1040 line are the "
                     "same roster (8815 subtracted in both). Bug it catches: 8815 subtracted on one side only."),
     "definition": {"kind": "formula_check", "form": "SCH_B", "formula": "L4 == L2 - L3",
                    "must_equal": {"form": "1040", "line": "2b"},
                    "must_write_to": {"form": "1040", "line": "2b"}},
     "sort_order": 11},
    {"assertion_id": "FA-1040-SCHB-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Sch B required-when gate incl. the $1,500 thresholds; line 6 ties 1040 3b",
     "description": ("Validates R-SB-03/04/05: required at >1,500 (either kind) or any non-threshold trigger; "
                     "Part III question chain enforced; line 6 == 1040 line 3b."),
     "definition": {"kind": "gating_check", "form": "SCH_B",
                    "truth_table": [
                        {"interest": 1600, "dividends": 0, "expect": {"required": True, "part_iii": True}},
                        {"interest": 1500, "dividends": 1500, "no_other_triggers": True,
                         "expect": {"required": False}},
                        {"interest": 100, "foreign_account": True, "expect": {"required": True, "part_iii": True}},
                        {"interest": 100, "seller_financed": True, "expect": {"required": True}}],
                    "must_equal": {"form": "1040", "line": "3b", "from": "L6"}},
     "sort_order": 12},
]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY FORM LINKS  (source_code, form_code, link_type)
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_SCHB_FORM", "SCH_B", "governs"),
    ("IRS_2025_SCHB_INSTR", "SCH_B", "governs"),
    ("IRS_1099INT_FORM", "SCH_B", "informs"),
    ("IRS_1099DIV_FORM", "SCH_B", "informs"),
    ("IRS_2025_1040_INSTR", "1040_INTDIV", "governs"),
    ("IRS_1099INT_FORM", "1040_INTDIV", "governs"),
    ("IRS_1099DIV_FORM", "1040_INTDIV", "governs"),
    ("IRS_2025_SCHB_INSTR", "1040_INTDIV", "governs"),
    ("IRS_2025_1040_FORM", "1040_INTDIV", "informs"),
    ("RP_2024_40", "1040_INTDIV", "governs"),
    ("RP_2025_32", "1040_INTDIV", "governs"),
    ("IRC_1", "1040_INTDIV", "informs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORMS ROSTER
# ═══════════════════════════════════════════════════════════════════════════

FORMS: list[dict] = [
    {"identity": INTDIV_IDENTITY, "facts": INTDIV_FACTS, "rules": INTDIV_RULES, "lines": INTDIV_LINES,
     "diagnostics": INTDIV_DIAGNOSTICS, "scenarios": INTDIV_SCENARIOS, "rule_links": INTDIV_RULE_LINKS},
    {"identity": SCHB_IDENTITY, "facts": SCHB_FACTS, "rules": SCHB_RULES, "lines": SCHB_LINES,
     "diagnostics": SCHB_DIAGNOSTICS, "scenarios": SCHB_SCENARIOS, "rule_links": SCHB_RULE_LINKS},
]


# ═══════════════════════════════════════════════════════════════════════════
# Command
# ═══════════════════════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = (
        "Load the Interest, Dividends & QDCGT specs into Rule Studio (creates "
        "1040_INTDIV, SCH_B). Refuses to seed until Ken sets READY_TO_SEED=True."
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()

        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad 1040_INTDIV / SCH_B specs (Topic 3)\n"))

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
                "REFUSING TO SEED 1040_INTDIV/SCH_B: not cleared to seed.\n"
                "\n"
                "Content is authored, but seeding is gated until Ken reviews the packet\n"
                "(the six judgment items in the module docstring, the QDCGT breakpoint\n"
                "tables for BOTH years, the aggregation rosters, diagnostics severities,\n"
                "the 21 scenarios) and flips the sentinel.\n"
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
    # Topics / sources (mirror load_1040_sch123.py exactly)
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
        self.stdout.write("DATABASE TOTALS (after load_1040_intdiv_qdcgt)")
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

        for fn in ("1040_INTDIV", "SCH_B"):
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
