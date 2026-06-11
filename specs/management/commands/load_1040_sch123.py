"""Load the Schedules 1 / 2 / 3 (Form 1040) specs — Sprint Topic 2.

Creates THREE TaxForms: SCH_1, SCH_2, SCH_3 (FED, TY2025, v1).

Session 2026-06-10: authored by transcription from primary sources fetched and
layout-extracted the same day (pymupdf positional dumps; SHA256-verified
downloads recorded in tts-tax-app resources/irs_forms/forms_manifest.json):

  - 2025 Schedule 1 (f1040s1.pdf, created 7/25/25) — both pages transcribed
    line by line. SHA256 8dafec71...
  - 2025 Schedule 2 (f1040s2.pdf, created 5/8/25) — both pages transcribed.
    SHA256 64d867b6...
  - 2025 Schedule 3 (f1040s3.pdf, created 11/17/25) — SINGLE page (the 2025
    revision compresses to one page). SHA256 008cfd3f...

TOPIC SCOPE (SPRINT_SCOPE.md Topic 2 DoD): full structure, every line
direct-entry capable, totals flow to Form 1040 lines 8 / 10 / 17 / 20 / 23 /
31, line-status table sections, flow assertions on all totals and every
computed line. These are AGGREGATION forms: the only computed lines are the
sums printed on the form face. No rates, limits, or phaseouts live here —
there is NO year-keyed constants table. The substantive law for each line
lives with its attached form (Sch C/SE/6251/8962/...), which are separate
topics; entering an amount on an attachment-backed line fires a
"attachment not generated" warning (no silent gaps).

SPINE SUPERSESSION: the seeded 1040 spine facts schedule_1_additional_income,
schedule_1_adjustments, schedule_2_line_3, schedule_2_line_21,
schedule_3_line_8, schedule_3_line_15 are direct-entry placeholders "until
Topic 2". When these specs seed, the 1040 lines 8/10/17/20/23/31 become
COMPUTED from the schedule totals (YELLOW); every schedule line stays
direct-entry (GREEN) per sprint Quality Rule 5.

TY2026 NOTE (target-year policy): no indexed constants exist on these forms,
but the 2026 form FACES must be re-verified when the IRS releases them — the
2025 revisions changed structure (Sch 2 gained 1d-1f EPE lines; Sch 3
compressed to one page). Tracker note, same convention as the 2026 Tax Table.

Safety guard
------------
`READY_TO_SEED = False`. Content is authored; Ken reviews the packet (line
inventory vs the form faces, totals formulas, the Sch 2 line-20 exclusion,
sign conventions, diagnostics severities, scenarios), flips the sentinel,
and seeds. Until then the command refuses to write to the DB.

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
# the review packet (totals formulas incl. the Sch 2 line-20 exclusion, sign
# conventions, diagnostics severities, the 13 scenarios, 8812 placeholder
# re-pointing by semantic content, the candidate YELLOW feeders).
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
    ("schedules_123", "Schedules 1/2/3 (Form 1040) — structure and totals flow"),
]

# Existing sources to REUSE (looked up, not modified).
EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_1040_FORM",   # 1040 lines 8/10/17/20/23/31 name the schedule totals
    "IRS_2025_1040_INSTR",  # i1040gi carries the Schedule 1-3 line instructions
]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY SOURCES (with embedded excerpts) — CREATE
# Form-face excerpts transcribed 2026-06-10 from the SHA-verified PDFs —
# requires_human_review=False (verbatim, verifiable against the on-disk copy).
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_SCH1_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Schedule 1 (Form 1040) — Additional Income and Adjustments to Income",
        "citation": "Schedule 1 (Form 1040) (2025); f1040s1.pdf (created 7/25/25)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f1040s1.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": (
            "Transcribed line by line 2026-06-10 from the manifest-verified copy "
            "(tts-tax-app resources/irs_forms/2025/f1040s1.pdf, SHA256 8dafec71...)."
        ),
        "topics": ["schedules_123"],
        "excerpts": [
            {
                "excerpt_label": "Line 9 / line 10 totals (verbatim)",
                "location_reference": "Schedule 1 (2025), page 1",
                "excerpt_text": (
                    "9 Total other income. Add lines 8a through 8z. "
                    "10 Combine lines 1 through 7 and 9. This is your additional income. "
                    "Enter here and on Form 1040, 1040-SR, or 1040-NR, line 8."
                ),
                "summary_text": "Part I totals: 9 = sum(8a..8z); 10 = combine(1..7, 9) -> 1040 line 8. 'Combine' = negatives allowed.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Line 25 / line 26 totals (verbatim)",
                "location_reference": "Schedule 1 (2025), page 2",
                "excerpt_text": (
                    "25 Total other adjustments. Add lines 24a through 24z. "
                    "26 Add lines 11 through 23 and 25. These are your adjustments to income. "
                    "Enter here and on Form 1040, 1040-SR, or 1040-NR, line 10."
                ),
                "summary_text": "Part II totals: 25 = sum(24a..24z); 26 = sum(11..23) + 25 -> 1040 line 10. Line 22 is 'Reserved for future use'.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Negative-entry lines (parentheses on the face)",
                "location_reference": "Schedule 1 (2025), page 1, lines 8a/8d/8s",
                "excerpt_text": (
                    "8a Net operating loss ( ) ... 8d Foreign earned income exclusion from "
                    "Form 2555 ( ) ... 8s Nontaxable amount of Medicaid waiver payments "
                    "included on Form 1040, line 1a or 1d ( )"
                ),
                "summary_text": "8a/8d/8s print parentheses — entered as NEGATIVE amounts (subtractions inside the line-9 sum).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "1099-K unnumbered entry box (memo)",
                "location_reference": "Schedule 1 (2025), page 1, above Part I",
                "excerpt_text": (
                    "For 2025, enter the amount reported to you on Form(s) 1099-K that was "
                    "included in error or for personal items sold at a loss. Note: The "
                    "remaining amounts reported to you on Form(s) 1099-K should be reported "
                    "elsewhere on your return depending on the nature of the transaction."
                ),
                "summary_text": "Unnumbered disclosure box above Part I — NOT included in any total.",
                "is_key_excerpt": False,
            },
            {
                "excerpt_label": "Alimony date/SSN sub-lines",
                "location_reference": "Schedule 1 (2025), lines 2b, 19b, 19c",
                "excerpt_text": (
                    "2b Date of original divorce or separation agreement (see instructions). "
                    "19a Alimony paid; b Recipient's SSN; c Date of original divorce or "
                    "separation agreement (see instructions)."
                ),
                "summary_text": "Alimony entries carry companion date/SSN sub-lines on the face.",
                "is_key_excerpt": False,
            },
        ],
    },
    {
        "source_code": "IRS_2025_SCH2_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Schedule 2 (Form 1040) — Additional Taxes",
        "citation": "Schedule 2 (Form 1040) (2025); f1040s2.pdf (created 5/8/25)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f1040s2.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": (
            "Transcribed line by line 2026-06-10 (SHA256 64d867b6...). The 2025 revision "
            "adds EPE recapture lines 1d-1f and line 19 (Form 4255)."
        ),
        "topics": ["schedules_123"],
        "excerpts": [
            {
                "excerpt_label": "Part I totals (verbatim)",
                "location_reference": "Schedule 2 (2025), page 1",
                "excerpt_text": (
                    "1z Add lines 1a through 1y. 2 Alternative minimum tax. Attach Form 6251. "
                    "3 Add lines 1z and 2. Enter here and on Form 1040, 1040-SR, or 1040-NR, line 17."
                ),
                "summary_text": "Part I: 1z = sum(1a..1y); 3 = 1z + 2 -> 1040 line 17.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Line 21 total — line 20 EXCLUDED (verbatim)",
                "location_reference": "Schedule 2 (2025), page 2",
                "excerpt_text": (
                    "20 Section 965 net tax liability installment from Form 965-A "
                    "[entry box in the LEFT amount column, not the totals column] ... "
                    "21 Add lines 4, 7 through 16, 18, and 19. These are your total other "
                    "taxes. Enter here and on Form 1040 or 1040-SR, line 23; or Form "
                    "1040-NR, line 23b."
                ),
                "summary_text": (
                    "21 = 4 + (7..16) + 18 + 19 -> 1040 line 23. Line 20 (965 installment) is "
                    "NOT an addend — it sits in the left column for IRS tracking. Lines 5/6 "
                    "roll through 7; lines 17a-17z roll through 18; line 10 is reserved."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Line 7 subtotal (verbatim)",
                "location_reference": "Schedule 2 (2025), page 1",
                "excerpt_text": (
                    "7 Total additional social security and Medicare tax. Add lines 5 and 6."
                ),
                "summary_text": "7 = 5 + 6 (4137 unreported-tip tax + 8919 uncollected tax).",
                "is_key_excerpt": False,
            },
            {
                "excerpt_label": "Line 18 subtotal (verbatim)",
                "location_reference": "Schedule 2 (2025), page 2",
                "excerpt_text": "18 Total additional taxes. Add lines 17a through 17z.",
                "summary_text": "18 = sum(17a..17z).",
                "is_key_excerpt": False,
            },
            {
                "excerpt_label": "Checkbox sets (1e/1f, line 4, line 8)",
                "location_reference": "Schedule 2 (2025), pages 1-2",
                "excerpt_text": (
                    "1e Excessive payments (EPs) on gross EPE from Form 4255. Check applicable "
                    "box and enter amount: (i) Line 1a (ii) Line 1c (iii) Line 1d (iv) Line 2a. "
                    "1f 20% EP from Form 4255. Check applicable box and enter amount [same four "
                    "boxes]. 4 Self-employment tax. Attach Schedule SE. Check if any exemption "
                    "from (see instructions): 1 4361, 2 4029, 3 [literal]. 8 Additional tax on "
                    "IRAs or other tax-favored accounts. Attach Form 5329 if required. If not "
                    "required, check here."
                ),
                "summary_text": "Stored checkbox facts: 1e/1f source-line boxes (i-iv), SE-tax exemption boxes (4361/4029/other), 5329-not-required.",
                "is_key_excerpt": False,
            },
        ],
    },
    {
        "source_code": "IRS_2025_SCH3_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Schedule 3 (Form 1040) — Additional Credits and Payments",
        "citation": "Schedule 3 (Form 1040) (2025); f1040s3.pdf (created 11/17/25)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f1040s3.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": (
            "Transcribed 2026-06-10 (SHA256 008cfd3f...). The 2025 revision is a SINGLE "
            "page (prior years ran two); line 6e is 'Reserved for future use'."
        ),
        "topics": ["schedules_123"],
        "excerpts": [
            {
                "excerpt_label": "Part I totals (verbatim)",
                "location_reference": "Schedule 3 (2025)",
                "excerpt_text": (
                    "7 Total other nonrefundable credits. Add lines 6a through 6z. "
                    "8 Add lines 1 through 4, 5a, 5b, and 7. Enter here and on Form 1040, "
                    "1040-SR, or 1040-NR, line 20."
                ),
                "summary_text": "Part I: 7 = sum(6a..6z); 8 = 1+2+3+4+5a+5b+7 -> 1040 line 20.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part II totals (verbatim)",
                "location_reference": "Schedule 3 (2025)",
                "excerpt_text": (
                    "14 Total other payments or refundable credits. Add lines 13a through 13z. "
                    "15 Add lines 9 through 12 and 14. Enter here and on Form 1040, 1040-SR, "
                    "or 1040-NR, line 31."
                ),
                "summary_text": "Part II: 14 = sum(13a..13z); 15 = 9+10+11+12+14 -> 1040 line 31.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_62",
        "source_type": "code_section",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "title": "IRC §62 — Adjusted gross income defined",
        "citation": "26 U.S.C. §62",
        "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title26-section62",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": True,
        "notes": "Substantive basis for Schedule 1 Part II (above-the-line deductions).",
        "topics": ["schedules_123"],
        "excerpts": [
            {
                "excerpt_label": "§62(a) AGI definition",
                "location_reference": "26 U.S.C. §62(a)",
                "excerpt_text": (
                    "For purposes of this subtitle, the term 'adjusted gross income' means, in "
                    "the case of an individual, gross income minus the following deductions: ... "
                    "[enumerated above-the-line deductions]"
                ),
                "summary_text": ("AGI = gross income minus the §62(a)-listed deductions — the law behind "
                                 "Schedule 1 Part II. PENDING VERBATIM CONFIRMATION (source-level "
                                 "requires_human_review=True; excerpt model has no such field)."),
                "is_key_excerpt": True,
            },
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = [
    (
        "IRS_2025_1040_FORM",
        {
            "excerpt_label": "1040 lines that consume the Schedule 1/2/3 totals",
            "location_reference": "Form 1040 (2025), pages 1-2",
            "excerpt_text": (
                "8 Additional income from Schedule 1, line 10. 10 Adjustments to income "
                "from Schedule 1, line 26. 17 Amount from Schedule 2, line 3. 20 Amount "
                "from Schedule 3, line 8. 23 Other taxes, including self-employment tax, "
                "from Schedule 2, line 21. 31 Amount from Schedule 3, line 15."
            ),
            "summary_text": "The six 1040 consumption points: 8<-S1.10, 10<-S1.26, 17<-S2.3, 20<-S3.8, 23<-S2.21, 31<-S3.15.",
            "is_key_excerpt": True,
        },
    ),
]


# ═══════════════════════════════════════════════════════════════════════════
# SCHEDULE 1 — Additional Income and Adjustments to Income
# ═══════════════════════════════════════════════════════════════════════════

SCH1_IDENTITY = {
    "form_number": "SCH_1",
    "form_title": "Schedule 1 (Form 1040) — Additional Income and Adjustments to Income (TY2025)",
    "notes": (
        "Sprint Topic 2. Aggregation form: every line direct-entry capable; computed "
        "lines are the face sums only (9, 10, 25, 26). Line 10 -> 1040 line 8; line 26 "
        "-> 1040 line 10 (supersedes the spine direct-entry facts "
        "schedule_1_additional_income / schedule_1_adjustments). Lines 8a/8d/8s are "
        "NEGATIVE entries (parentheses on the face). Line 22 is reserved. Attachment-"
        "backed lines (Sch C/E/F/SE, 2106, 3903, 8889, 8853, 2555, 4797) warn that the "
        "attachment is not generated. The 1099-K box above Part I is a memo only. "
        "Line 15 is the amount the SCH_8812 spec reads via the Taxpayer "
        "deductible_se_tax_half placeholder — the build leg re-points that read to "
        "this line (one source, two consumers)."
    ),
}

SCH1_FACTS: list[dict] = [
    {"fact_key": "f1099k_error_amount", "label": "1099-K amounts in error / personal items sold at a loss (memo box)",
     "data_type": "decimal", "default_value": "0", "sort_order": 1,
     "notes": "Unnumbered disclosure box above Part I. NOT included in any total (R-S1-08)."},
    # ── Part I lines 1-7 ──
    {"fact_key": "state_local_refunds", "label": "Taxable refunds/credits/offsets of state and local income taxes (1)",
     "data_type": "decimal", "default_value": "0", "sort_order": 10,
     "notes": "Direct entry. State-refund taxability worksheet is a post-sprint RED item (NEXT-UP list #9)."},
    {"fact_key": "alimony_received", "label": "Alimony received (2a)", "data_type": "decimal",
     "default_value": "0", "sort_order": 11,
     "notes": "Pre-2019 instruments only (TCJA); preparer determines taxability. D_SCH1_003 wants 2b when present."},
    {"fact_key": "alimony_received_divorce_date", "label": "Date of original divorce/separation agreement (2b)",
     "data_type": "date", "sort_order": 12, "notes": "Companion to 2a; renders as a date literal."},
    {"fact_key": "business_income_sch_c", "label": "Business income or (loss) — Schedule C (3)",
     "data_type": "decimal", "default_value": "0", "sort_order": 13,
     "notes": "Direct entry until the Schedule C topic (post-sprint #1). Negative allowed. D_SCH1_004."},
    {"fact_key": "other_gains_4797", "label": "Other gains or (losses) (4)", "data_type": "decimal",
     "default_value": "0", "sort_order": 14, "notes": "Negative allowed. D_SCH1_004 (Form 4797 not generated at 1040 level)."},
    {"fact_key": "line4_from_4797", "label": "Line 4 checkbox: from Form 4797", "data_type": "boolean",
     "sort_order": 15, "notes": "Render-only checkbox (c1_1)."},
    {"fact_key": "line4_from_4684", "label": "Line 4 checkbox: from Form 4684", "data_type": "boolean",
     "sort_order": 16, "notes": "Render-only checkbox (c1_2)."},
    {"fact_key": "rental_sch_e", "label": "Rental real estate, royalties, partnerships, S corps, trusts — Schedule E (5)",
     "data_type": "decimal", "default_value": "0", "sort_order": 17,
     "notes": "Direct entry until the Schedule E + 8582 topic (post-sprint #6). Negative allowed. D_SCH1_004."},
    {"fact_key": "farm_income_sch_f", "label": "Farm income or (loss) — Schedule F (6)", "data_type": "decimal",
     "default_value": "0", "sort_order": 18, "notes": "Negative allowed. D_SCH1_004."},
    {"fact_key": "unemployment_compensation", "label": "Unemployment compensation (7)", "data_type": "decimal",
     "default_value": "0", "sort_order": 19, "notes": "Direct entry (1099-G model is a future upgrade)."},
    {"fact_key": "unemployment_repaid_amount", "label": "2025 overpayment repaid (line 7 checkbox + amount)",
     "data_type": "decimal", "default_value": "0", "sort_order": 20,
     "notes": "Amount literal on the line-7 row; > 0 checks the box (c1_3) at render. Preparer nets line 7 per instructions."},
    # ── Part I line 8 series ──
    {"fact_key": "nol_deduction_8a", "label": "Net operating loss (8a) — NEGATIVE", "data_type": "decimal",
     "default_value": "0", "sort_order": 30, "notes": "Parentheses on the face: must be <= 0 (D_SCH1_001)."},
    {"fact_key": "gambling_income_8b", "label": "Gambling income (8b)", "data_type": "decimal",
     "default_value": "0", "sort_order": 31},
    {"fact_key": "cancellation_of_debt_8c", "label": "Cancellation of debt (8c)", "data_type": "decimal",
     "default_value": "0", "sort_order": 32},
    {"fact_key": "feie_2555_8d", "label": "Foreign earned income exclusion from Form 2555 (8d) — NEGATIVE",
     "data_type": "decimal", "default_value": "0", "sort_order": 33,
     "notes": "Must be <= 0 (D_SCH1_001). Interacts with Taxpayer.files_form_2555 (8812 gate) — D_SCH1_004 notes 2555 not built."},
    {"fact_key": "income_8853_8e", "label": "Income from Form 8853 (8e)", "data_type": "decimal",
     "default_value": "0", "sort_order": 34, "notes": "D_SCH1_004 (8853 not built)."},
    {"fact_key": "income_8889_8f", "label": "Income from Form 8889 (8f)", "data_type": "decimal",
     "default_value": "0", "sort_order": 35, "notes": "D_SCH1_004 (8889 not built)."},
    {"fact_key": "alaska_pfd_8g", "label": "Alaska Permanent Fund dividends (8g)", "data_type": "decimal",
     "default_value": "0", "sort_order": 36},
    {"fact_key": "jury_duty_pay_8h", "label": "Jury duty pay (8h)", "data_type": "decimal",
     "default_value": "0", "sort_order": 37},
    {"fact_key": "prizes_awards_8i", "label": "Prizes and awards (8i)", "data_type": "decimal",
     "default_value": "0", "sort_order": 38},
    {"fact_key": "hobby_income_8j", "label": "Activity not engaged in for profit income (8j)", "data_type": "decimal",
     "default_value": "0", "sort_order": 39},
    {"fact_key": "stock_options_8k", "label": "Stock options (8k)", "data_type": "decimal",
     "default_value": "0", "sort_order": 40},
    {"fact_key": "personal_property_rental_8l", "label": "Income from rental of personal property (for profit, not a business) (8l)",
     "data_type": "decimal", "default_value": "0", "sort_order": 41,
     "notes": "Companion deduction is 24b."},
    {"fact_key": "olympic_medals_8m", "label": "Olympic/Paralympic medals and USOC prize money (8m)",
     "data_type": "decimal", "default_value": "0", "sort_order": 42, "notes": "Companion exclusion is 24c."},
    {"fact_key": "sec_951a_inclusion_8n", "label": "Section 951(a) inclusion (8n)", "data_type": "decimal",
     "default_value": "0", "sort_order": 43},
    {"fact_key": "sec_951Aa_inclusion_8o", "label": "Section 951A(a) inclusion (8o)", "data_type": "decimal",
     "default_value": "0", "sort_order": 44},
    {"fact_key": "sec_461l_adjustment_8p", "label": "Section 461(l) excess business loss adjustment (8p)",
     "data_type": "decimal", "default_value": "0", "sort_order": 45},
    {"fact_key": "able_distributions_8q", "label": "Taxable ABLE account distributions (8q)", "data_type": "decimal",
     "default_value": "0", "sort_order": 46},
    {"fact_key": "scholarships_8r", "label": "Scholarship/fellowship grants not on W-2 (8r)", "data_type": "decimal",
     "default_value": "0", "sort_order": 47},
    {"fact_key": "medicaid_waiver_negative_8s", "label": "Nontaxable Medicaid waiver payments in 1040 1a/1d (8s) — NEGATIVE",
     "data_type": "decimal", "default_value": "0", "sort_order": 48,
     "notes": "Must be <= 0 (D_SCH1_001). Backs out amounts included on 1040 line 1a/1d."},
    {"fact_key": "nonqual_deferred_comp_8t", "label": "Pension/annuity from nonqualified deferred comp or 457 plan (8t)",
     "data_type": "decimal", "default_value": "0", "sort_order": 49},
    {"fact_key": "incarcerated_wages_8u", "label": "Wages earned while incarcerated (8u)", "data_type": "decimal",
     "default_value": "0", "sort_order": 50},
    {"fact_key": "digital_assets_income_8v", "label": "Digital assets received as ordinary income not reported elsewhere (8v)",
     "data_type": "decimal", "default_value": "0", "sort_order": 51,
     "notes": "Pairs with the 1040 header digital-asset question (D_1040_017 on the spine)."},
    {"fact_key": "other_income_8z", "label": "Other income — amount (8z)", "data_type": "decimal",
     "default_value": "0", "sort_order": 52, "notes": "D_SCH1_002 wants the type literal when nonzero."},
    {"fact_key": "other_income_8z_type", "label": "Other income — list type (8z literal)", "data_type": "string",
     "sort_order": 53},
    # ── Part II ──
    {"fact_key": "educator_expenses", "label": "Educator expenses (11)", "data_type": "decimal",
     "default_value": "0", "sort_order": 60},
    {"fact_key": "reservist_artist_2106", "label": "Business expenses of reservists/performing artists/fee-basis officials — Form 2106 (12)",
     "data_type": "decimal", "default_value": "0", "sort_order": 61, "notes": "D_SCH1_004 (2106 not built)."},
    {"fact_key": "hsa_deduction_8889", "label": "HSA deduction — Form 8889 (13)", "data_type": "decimal",
     "default_value": "0", "sort_order": 62, "notes": "D_SCH1_004 (8889 not built)."},
    {"fact_key": "moving_expenses_3903", "label": "Moving expenses, Armed Forces — Form 3903 (14)",
     "data_type": "decimal", "default_value": "0", "sort_order": 63, "notes": "D_SCH1_004 (3903 not built)."},
    {"fact_key": "moving_storage_only", "label": "Line 14 checkbox: claiming only storage fees", "data_type": "boolean",
     "sort_order": 64, "notes": "Render-only checkbox (c2_1)."},
    {"fact_key": "deductible_se_tax", "label": "Deductible part of self-employment tax — Schedule SE (15)",
     "data_type": "decimal", "default_value": "0", "sort_order": 65,
     "notes": ("THE SAME AMOUNT the seeded SCH_8812 spec reads via Taxpayer.deductible_se_tax_half. "
               "Build leg: line 15 becomes the single source; the placeholder mapping is retired "
               "(one field, two consumers — same convention as eitc_claimed). D_SCH1_004 (Sch SE not built).")},
    {"fact_key": "sep_simple_qualified", "label": "Self-employed SEP, SIMPLE, and qualified plans (16)",
     "data_type": "decimal", "default_value": "0", "sort_order": 66},
    {"fact_key": "se_health_insurance", "label": "Self-employed health insurance deduction (17)",
     "data_type": "decimal", "default_value": "0", "sort_order": 67,
     "notes": "SEHI compute (Form 7206 logic) arrives with the Schedule C topic; direct entry until then."},
    {"fact_key": "early_withdrawal_penalty", "label": "Penalty on early withdrawal of savings (18)",
     "data_type": "decimal", "default_value": "0", "sort_order": 68,
     "notes": "1099-INT box 2 is modeled on InterestIncome — build leg MAY compute this as a YELLOW feeder (flag for Ken)."},
    {"fact_key": "alimony_paid", "label": "Alimony paid (19a)", "data_type": "decimal",
     "default_value": "0", "sort_order": 69, "notes": "Pre-2019 instruments only. D_SCH1_003 wants 19b + 19c."},
    {"fact_key": "alimony_paid_recipient_ssn", "label": "Recipient's SSN (19b)", "data_type": "string",
     "sort_order": 70, "notes": "MeF NNN-NN-NNNN; entry-level validation + D_SCH1_003."},
    {"fact_key": "alimony_paid_divorce_date", "label": "Date of original divorce/separation agreement (19c)",
     "data_type": "date", "sort_order": 71},
    {"fact_key": "ira_deduction", "label": "IRA deduction (20)", "data_type": "decimal",
     "default_value": "0", "sort_order": 72,
     "notes": "Direct entry; the IRA-deduction/taxable-SS interaction worksheet is RED-unsupported this sprint (Topic 5 DoD)."},
    {"fact_key": "ira_mfs_lived_apart", "label": "Line 20 checkbox: MFS and lived apart all year", "data_type": "boolean",
     "sort_order": 73, "notes": "Render-only checkbox (c2_2)."},
    {"fact_key": "student_loan_interest", "label": "Student loan interest deduction (21)", "data_type": "decimal",
     "default_value": "0", "sort_order": 74,
     "notes": "Direct entry; the MAGI phaseout worksheet is NOT computed this sprint — preparer enters the allowed amount."},
    {"fact_key": "archer_msa_deduction", "label": "Archer MSA deduction (23)", "data_type": "decimal",
     "default_value": "0", "sort_order": 75},
    # ── Part II line 24 series ──
    {"fact_key": "jury_duty_pay_given_24a", "label": "Jury duty pay given to employer (24a)", "data_type": "decimal",
     "default_value": "0", "sort_order": 80},
    {"fact_key": "personal_property_rental_exp_24b", "label": "Deductible expenses for line 8l rental (24b)",
     "data_type": "decimal", "default_value": "0", "sort_order": 81},
    {"fact_key": "olympic_nontaxable_24c", "label": "Nontaxable Olympic/Paralympic medals and USOC prize money (24c)",
     "data_type": "decimal", "default_value": "0", "sort_order": 82},
    {"fact_key": "reforestation_24d", "label": "Reforestation amortization and expenses (24d)", "data_type": "decimal",
     "default_value": "0", "sort_order": 83},
    {"fact_key": "trade_act_repayment_24e", "label": "Repayment of supplemental unemployment benefits (Trade Act 1974) (24e)",
     "data_type": "decimal", "default_value": "0", "sort_order": 84},
    {"fact_key": "sec_501c18d_contrib_24f", "label": "Contributions to §501(c)(18)(D) pension plans (24f)",
     "data_type": "decimal", "default_value": "0", "sort_order": 85},
    {"fact_key": "chaplain_403b_24g", "label": "Contributions by certain chaplains to §403(b) plans (24g)",
     "data_type": "decimal", "default_value": "0", "sort_order": 86},
    {"fact_key": "attorney_fees_discrimination_24h", "label": "Attorney fees/court costs — unlawful discrimination claims (24h)",
     "data_type": "decimal", "default_value": "0", "sort_order": 87},
    {"fact_key": "attorney_fees_irs_award_24i", "label": "Attorney fees/court costs — IRS whistleblower award (24i)",
     "data_type": "decimal", "default_value": "0", "sort_order": 88},
    {"fact_key": "housing_deduction_2555_24j", "label": "Housing deduction from Form 2555 (24j)", "data_type": "decimal",
     "default_value": "0", "sort_order": 89, "notes": "D_SCH1_004 (2555 not built)."},
    {"fact_key": "excess_67e_deductions_24k", "label": "Excess §67(e) deductions from Schedule K-1 (Form 1041) (24k)",
     "data_type": "decimal", "default_value": "0", "sort_order": 90},
    {"fact_key": "other_adjustments_24z", "label": "Other adjustments — amount (24z)", "data_type": "decimal",
     "default_value": "0", "sort_order": 91, "notes": "D_SCH1_002 wants the type literal when nonzero."},
    {"fact_key": "other_adjustments_24z_type", "label": "Other adjustments — list type (24z literal)", "data_type": "string",
     "sort_order": 92},
    # ── Calculated outputs (traceability) ──
    {"fact_key": "total_other_income", "label": "Total other income (9)", "data_type": "decimal", "sort_order": 100,
     "notes": "Calculated: sum(8a..8z) — negative items included."},
    {"fact_key": "additional_income_total", "label": "Additional income (10) -> 1040 line 8", "data_type": "decimal",
     "sort_order": 101, "notes": "Calculated: combine(1, 2a, 3, 4, 5, 6, 7, 9). May be NEGATIVE."},
    {"fact_key": "total_other_adjustments", "label": "Total other adjustments (25)", "data_type": "decimal",
     "sort_order": 102, "notes": "Calculated: sum(24a..24z)."},
    {"fact_key": "adjustments_total", "label": "Adjustments to income (26) -> 1040 line 10", "data_type": "decimal",
     "sort_order": 103, "notes": "Calculated: sum(11..21, 23) + 25 (line 22 reserved)."},
]

SCH1_RULES: list[dict] = [
    {"rule_id": "R-S1-01", "title": "Line 9 = add lines 8a through 8z", "rule_type": "calculation",
     "precedence": 1, "sort_order": 1,
     "formula": "L9 = 8a + 8b + 8c + 8d + 8e + 8f + 8g + 8h + 8i + 8j + 8k + 8l + 8m + 8n + 8o + 8p + 8q + 8r + 8s + 8t + 8u + 8v + 8z   (8a/8d/8s are <= 0)",
     "inputs": ["nol_deduction_8a", "gambling_income_8b", "cancellation_of_debt_8c", "feie_2555_8d",
                "income_8853_8e", "income_8889_8f", "alaska_pfd_8g", "jury_duty_pay_8h", "prizes_awards_8i",
                "hobby_income_8j", "stock_options_8k", "personal_property_rental_8l", "olympic_medals_8m",
                "sec_951a_inclusion_8n", "sec_951Aa_inclusion_8o", "sec_461l_adjustment_8p",
                "able_distributions_8q", "scholarships_8r", "medicaid_waiver_negative_8s",
                "nonqual_deferred_comp_8t", "incarcerated_wages_8u", "digital_assets_income_8v",
                "other_income_8z"],
     "outputs": ["L9"],
     "description": "ONCE PER RETURN. Verbatim face sum. The negative-entry items (8a/8d/8s) subtract inside the sum."},
    {"rule_id": "R-S1-02", "title": "Line 10 = combine lines 1-7 and 9 -> Form 1040 line 8", "rule_type": "calculation",
     "precedence": 2, "sort_order": 2,
     "formula": "L10 = L1 + L2a + L3 + L4 + L5 + L6 + L7 + L9; NO floor — may be negative. Writes Form 1040 line 8.",
     "inputs": ["state_local_refunds", "alimony_received", "business_income_sch_c", "other_gains_4797",
                "rental_sch_e", "farm_income_sch_f", "unemployment_compensation"],
     "outputs": ["L10", "1040.L8"],
     "description": ("ONCE PER RETURN. 'Combine' (form verbatim) = negatives flow through (business/rental/"
                     "farm losses, NOL). SUPERSEDES the spine direct-entry fact schedule_1_additional_income: "
                     "1040 line 8 becomes a COMPUTED feeder (YELLOW) when Schedule 1 has entries.")},
    {"rule_id": "R-S1-03", "title": "Line 25 = add lines 24a through 24z", "rule_type": "calculation",
     "precedence": 1, "sort_order": 3,
     "formula": "L25 = 24a + 24b + 24c + 24d + 24e + 24f + 24g + 24h + 24i + 24j + 24k + 24z",
     "inputs": ["jury_duty_pay_given_24a", "personal_property_rental_exp_24b", "olympic_nontaxable_24c",
                "reforestation_24d", "trade_act_repayment_24e", "sec_501c18d_contrib_24f", "chaplain_403b_24g",
                "attorney_fees_discrimination_24h", "attorney_fees_irs_award_24i", "housing_deduction_2555_24j",
                "excess_67e_deductions_24k", "other_adjustments_24z"],
     "outputs": ["L25"],
     "description": "ONCE PER RETURN. Verbatim face sum."},
    {"rule_id": "R-S1-04", "title": "Line 26 = add lines 11-23 and 25 -> Form 1040 line 10", "rule_type": "calculation",
     "precedence": 2, "sort_order": 4,
     "formula": "L26 = L11 + L12 + L13 + L14 + L15 + L16 + L17 + L18 + L19a + L20 + L21 + L23 + L25   (L22 reserved = 0)",
     "inputs": ["educator_expenses", "reservist_artist_2106", "hsa_deduction_8889", "moving_expenses_3903",
                "deductible_se_tax", "sep_simple_qualified", "se_health_insurance", "early_withdrawal_penalty",
                "alimony_paid", "ira_deduction", "student_loan_interest", "archer_msa_deduction"],
     "outputs": ["L26", "1040.L10"],
     "description": ("ONCE PER RETURN. 'Add lines 11 through 23 and 25' — line 22 is 'Reserved for future "
                     "use' and contributes 0 (R-S1-09 polices it). SUPERSEDES the spine fact "
                     "schedule_1_adjustments: 1040 line 10 becomes a COMPUTED feeder.")},
    {"rule_id": "R-S1-05", "title": "Sign convention: 8a / 8d / 8s entered as negative", "rule_type": "validation",
     "precedence": 0, "sort_order": 5,
     "formula": "nol_deduction_8a <= 0 AND feie_2555_8d <= 0 AND medicaid_waiver_negative_8s <= 0",
     "inputs": ["nol_deduction_8a", "feie_2555_8d", "medicaid_waiver_negative_8s"], "outputs": [],
     "description": ("ONCE PER RETURN. The face prints parentheses on exactly these three 8-series lines — "
                     "a positive entry would ADD where the law subtracts. D_SCH1_001 (error).")},
    {"rule_id": "R-S1-06", "title": "List-type literals required with 8z / 24z amounts", "rule_type": "validation",
     "precedence": 0, "sort_order": 6,
     "formula": "(other_income_8z != 0 implies other_income_8z_type nonblank) AND (other_adjustments_24z != 0 implies other_adjustments_24z_type nonblank)",
     "inputs": ["other_income_8z", "other_income_8z_type", "other_adjustments_24z", "other_adjustments_24z_type"],
     "outputs": [],
     "description": "ONCE PER RETURN. 'List type and amount' (face verbatim). D_SCH1_002 (warning)."},
    {"rule_id": "R-S1-07", "title": "Alimony completeness (2b; 19b/19c)", "rule_type": "validation",
     "precedence": 0, "sort_order": 7,
     "formula": ("(alimony_received > 0 implies alimony_received_divorce_date present) AND "
                 "(alimony_paid > 0 implies alimony_paid_recipient_ssn matches NNN-NN-NNNN AND alimony_paid_divorce_date present)"),
     "inputs": ["alimony_received", "alimony_received_divorce_date", "alimony_paid",
                "alimony_paid_recipient_ssn", "alimony_paid_divorce_date"], "outputs": [],
     "description": "ONCE PER RETURN. The face carries the companion sub-lines; the SSN is MeF-typed. D_SCH1_003 (warning)."},
    {"rule_id": "R-S1-08", "title": "1099-K box above Part I is a memo — never summed", "rule_type": "classification",
     "precedence": 0, "sort_order": 8,
     "formula": "f1099k_error_amount participates in NO total",
     "inputs": ["f1099k_error_amount"], "outputs": [],
     "description": ("ONCE PER RETURN. Face note: remaining 1099-K amounts are reported elsewhere by "
                     "transaction nature. Disclosure box only. D_SCH1_006 (info) reminds when nonzero.")},
    {"rule_id": "R-S1-09", "title": "Line 22 reserved — must be blank", "rule_type": "validation",
     "precedence": 0, "sort_order": 9,
     "formula": "L22 has no entry (face: 'Reserved for future use')",
     "inputs": [], "outputs": [],
     "description": "ONCE PER RETURN. D_SCH1_005 (error) if a value lands there."},
    {"rule_id": "R-S1-10", "title": "Attachment-backed lines warn until their topics build", "rule_type": "classification",
     "precedence": 0, "sort_order": 10,
     "formula": ("nonzero on any of {3 (Sch C), 4 (4797/4684), 5 (Sch E), 6 (Sch F), 8d (2555), 8e (8853), "
                 "8f (8889), 12 (2106), 13 (8889), 14 (3903), 15 (Sch SE), 24j (2555)} -> attachment-not-generated warning"),
     "inputs": ["business_income_sch_c", "other_gains_4797", "rental_sch_e", "farm_income_sch_f",
                "feie_2555_8d", "income_8853_8e", "income_8889_8f", "reservist_artist_2106",
                "hsa_deduction_8889", "moving_expenses_3903", "deductible_se_tax", "housing_deduction_2555_24j"],
     "outputs": [],
     "description": ("ONCE PER RETURN. Sprint no-silent-gap rule applied to attachments: the amount computes "
                     "fine (it is direct entry) but the printed packet will not contain the attached form — "
                     "the preparer attaches the manually prepared form. D_SCH1_004 (warning, grouped).")},
]

SCH1_LINES: list[dict] = [
    {"line_number": "1099K", "description": "1099-K amounts in error / personal items sold at a loss (unnumbered memo box)",
     "line_type": "informational", "source_rules": ["R-S1-08"], "sort_order": 1,
     "notes": "Widget f1_03. Never summed."},
    {"line_number": "1", "description": "Taxable refunds, credits, or offsets of state and local income taxes",
     "line_type": "input", "sort_order": 10, "notes": "State-refund taxability worksheet = post-sprint RED item."},
    {"line_number": "2a", "description": "Alimony received", "line_type": "input", "sort_order": 11},
    {"line_number": "2b", "description": "Date of original divorce or separation agreement", "line_type": "input",
     "sort_order": 12, "notes": "Date literal (widget f1_06)."},
    {"line_number": "3", "description": "Business income or (loss) — attach Schedule C", "line_type": "input",
     "sort_order": 13, "notes": "Negative allowed. D_SCH1_004 until the Schedule C topic."},
    {"line_number": "4", "description": "Other gains or (losses) — checkboxes 4797 / 4684", "line_type": "input",
     "sort_order": 14, "notes": "Negative allowed. Checkbox facts line4_from_4797/4684."},
    {"line_number": "5", "description": "Rental real estate, royalties, partnerships, S corps, trusts — attach Schedule E",
     "line_type": "input", "sort_order": 15, "notes": "Negative allowed. D_SCH1_004 until Schedule E topic."},
    {"line_number": "6", "description": "Farm income or (loss) — attach Schedule F", "line_type": "input",
     "sort_order": 16, "notes": "Negative allowed."},
    {"line_number": "7", "description": "Unemployment compensation (repaid checkbox + amount literal)",
     "line_type": "input", "sort_order": 17, "notes": "Repaid amount fact renders on the row (f1_11 + c1_3)."},
    {"line_number": "8a", "description": "Net operating loss — NEGATIVE entry", "line_type": "input",
     "source_rules": ["R-S1-05"], "sort_order": 20},
    {"line_number": "8b", "description": "Gambling", "line_type": "input", "sort_order": 21},
    {"line_number": "8c", "description": "Cancellation of debt", "line_type": "input", "sort_order": 22},
    {"line_number": "8d", "description": "Foreign earned income exclusion from Form 2555 — NEGATIVE entry",
     "line_type": "input", "source_rules": ["R-S1-05"], "sort_order": 23},
    {"line_number": "8e", "description": "Income from Form 8853", "line_type": "input", "sort_order": 24},
    {"line_number": "8f", "description": "Income from Form 8889", "line_type": "input", "sort_order": 25},
    {"line_number": "8g", "description": "Alaska Permanent Fund dividends", "line_type": "input", "sort_order": 26},
    {"line_number": "8h", "description": "Jury duty pay", "line_type": "input", "sort_order": 27},
    {"line_number": "8i", "description": "Prizes and awards", "line_type": "input", "sort_order": 28},
    {"line_number": "8j", "description": "Activity not engaged in for profit income", "line_type": "input", "sort_order": 29},
    {"line_number": "8k", "description": "Stock options", "line_type": "input", "sort_order": 30},
    {"line_number": "8l", "description": "Income from rental of personal property (for profit, not a business)",
     "line_type": "input", "sort_order": 31, "notes": "Companion deduction 24b."},
    {"line_number": "8m", "description": "Olympic and Paralympic medals and USOC prize money", "line_type": "input",
     "sort_order": 32, "notes": "Companion exclusion 24c."},
    {"line_number": "8n", "description": "Section 951(a) inclusion", "line_type": "input", "sort_order": 33},
    {"line_number": "8o", "description": "Section 951A(a) inclusion", "line_type": "input", "sort_order": 34},
    {"line_number": "8p", "description": "Section 461(l) excess business loss adjustment", "line_type": "input", "sort_order": 35},
    {"line_number": "8q", "description": "Taxable distributions from an ABLE account", "line_type": "input", "sort_order": 36},
    {"line_number": "8r", "description": "Scholarship and fellowship grants not reported on Form W-2",
     "line_type": "input", "sort_order": 37},
    {"line_number": "8s", "description": "Nontaxable Medicaid waiver payments included on 1040 line 1a/1d — NEGATIVE entry",
     "line_type": "input", "source_rules": ["R-S1-05"], "sort_order": 38},
    {"line_number": "8t", "description": "Pension/annuity from a nonqualified deferred compensation or 457 plan",
     "line_type": "input", "sort_order": 39},
    {"line_number": "8u", "description": "Wages earned while incarcerated", "line_type": "input", "sort_order": 40},
    {"line_number": "8v", "description": "Digital assets received as ordinary income not reported elsewhere",
     "line_type": "input", "sort_order": 41},
    {"line_number": "8z", "description": "Other income — list type and amount", "line_type": "input",
     "source_rules": ["R-S1-06"], "sort_order": 42, "notes": "Type literal widget f1_35; amount f1_36."},
    {"line_number": "9", "description": "Total other income = add lines 8a through 8z", "line_type": "subtotal",
     "source_rules": ["R-S1-01"], "sort_order": 43},
    {"line_number": "10", "description": "Combine lines 1-7 and 9 — additional income", "line_type": "total",
     "source_rules": ["R-S1-02"], "destination_form": "Form 1040 line 8", "sort_order": 44,
     "notes": "May be negative (combine semantics)."},
    {"line_number": "11", "description": "Educator expenses", "line_type": "input", "sort_order": 50},
    {"line_number": "12", "description": "Reservists/performing artists/fee-basis officials — attach Form 2106",
     "line_type": "input", "sort_order": 51},
    {"line_number": "13", "description": "Health savings account deduction — attach Form 8889", "line_type": "input", "sort_order": 52},
    {"line_number": "14", "description": "Moving expenses for Armed Forces — attach Form 3903 (storage-only checkbox)",
     "line_type": "input", "sort_order": 53, "notes": "Checkbox fact moving_storage_only (c2_1)."},
    {"line_number": "15", "description": "Deductible part of self-employment tax — attach Schedule SE",
     "line_type": "input", "sort_order": 54,
     "notes": "Single source for the 8812 deductible_se_tax_half placeholder (build leg re-points the read)."},
    {"line_number": "16", "description": "Self-employed SEP, SIMPLE, and qualified plans", "line_type": "input", "sort_order": 55},
    {"line_number": "17", "description": "Self-employed health insurance deduction", "line_type": "input", "sort_order": 56},
    {"line_number": "18", "description": "Penalty on early withdrawal of savings", "line_type": "input",
     "sort_order": 57, "notes": "Possible YELLOW feeder from InterestIncome box 2 — flag for Ken at the build leg."},
    {"line_number": "19a", "description": "Alimony paid", "line_type": "input", "source_rules": ["R-S1-07"], "sort_order": 58},
    {"line_number": "19b", "description": "Recipient's SSN", "line_type": "input", "source_rules": ["R-S1-07"],
     "sort_order": 59, "notes": "MeF NNN-NN-NNNN (comb field f2_10)."},
    {"line_number": "19c", "description": "Date of original divorce or separation agreement", "line_type": "input", "sort_order": 60},
    {"line_number": "20", "description": "IRA deduction (MFS lived-apart checkbox)", "line_type": "input",
     "sort_order": 61, "notes": "Checkbox fact ira_mfs_lived_apart (c2_2)."},
    {"line_number": "21", "description": "Student loan interest deduction", "line_type": "input", "sort_order": 62},
    {"line_number": "22", "description": "Reserved for future use", "line_type": "informational",
     "source_rules": ["R-S1-09"], "sort_order": 63, "notes": "Must stay blank (D_SCH1_005)."},
    {"line_number": "23", "description": "Archer MSA deduction", "line_type": "input", "sort_order": 64},
    {"line_number": "24a", "description": "Jury duty pay given to employer", "line_type": "input", "sort_order": 70},
    {"line_number": "24b", "description": "Deductible expenses for line 8l personal-property rental", "line_type": "input", "sort_order": 71},
    {"line_number": "24c", "description": "Nontaxable Olympic/Paralympic medals and USOC prize money (re line 8m)",
     "line_type": "input", "sort_order": 72},
    {"line_number": "24d", "description": "Reforestation amortization and expenses", "line_type": "input", "sort_order": 73},
    {"line_number": "24e", "description": "Repayment of supplemental unemployment benefits (Trade Act of 1974)",
     "line_type": "input", "sort_order": 74},
    {"line_number": "24f", "description": "Contributions to section 501(c)(18)(D) pension plans", "line_type": "input", "sort_order": 75},
    {"line_number": "24g", "description": "Contributions by certain chaplains to section 403(b) plans", "line_type": "input", "sort_order": 76},
    {"line_number": "24h", "description": "Attorney fees and court costs — unlawful discrimination claims", "line_type": "input", "sort_order": 77},
    {"line_number": "24i", "description": "Attorney fees and court costs — IRS whistleblower award", "line_type": "input", "sort_order": 78},
    {"line_number": "24j", "description": "Housing deduction from Form 2555", "line_type": "input", "sort_order": 79},
    {"line_number": "24k", "description": "Excess deductions of section 67(e) expenses from Schedule K-1 (Form 1041)",
     "line_type": "input", "sort_order": 80},
    {"line_number": "24z", "description": "Other adjustments — list type and amount", "line_type": "input",
     "source_rules": ["R-S1-06"], "sort_order": 81, "notes": "Type literal f2_27; amount f2_28."},
    {"line_number": "25", "description": "Total other adjustments = add lines 24a through 24z", "line_type": "subtotal",
     "source_rules": ["R-S1-03"], "sort_order": 82},
    {"line_number": "26", "description": "Add lines 11-23 and 25 — adjustments to income", "line_type": "total",
     "source_rules": ["R-S1-04"], "destination_form": "Form 1040 line 10", "sort_order": 83},
]

SCH1_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_SCH1_001", "title": "8a/8d/8s must be negative (parenthetical lines)", "severity": "error",
     "condition": "nol_deduction_8a > 0 OR feie_2555_8d > 0 OR medicaid_waiver_negative_8s > 0",
     "message": ("Lines 8a (NOL), 8d (foreign earned income exclusion), and 8s (Medicaid waiver) are "
                 "subtractions — enter them as NEGATIVE amounts (the form prints parentheses)."),
     "notes": "A positive entry overstates line 9/10 income. R-S1-05."},
    {"diagnostic_id": "D_SCH1_002", "title": "8z/24z amount without a type literal", "severity": "warning",
     "condition": "(other_income_8z != 0 AND other_income_8z_type blank) OR (other_adjustments_24z != 0 AND other_adjustments_24z_type blank)",
     "message": "Line 8z/24z requires 'list type and amount' — enter the description literal.",
     "notes": "R-S1-06."},
    {"diagnostic_id": "D_SCH1_003", "title": "Alimony entry incomplete", "severity": "warning",
     "condition": ("(alimony_received > 0 AND alimony_received_divorce_date missing) OR "
                   "(alimony_paid > 0 AND (alimony_paid_recipient_ssn invalid OR alimony_paid_divorce_date missing))"),
     "message": ("Alimony entries need the divorce/separation agreement date (2b/19c) and, for alimony paid, "
                 "the recipient's SSN (19b, NNN-NN-NNNN)."),
     "notes": "R-S1-07. Post-2018 instruments are not alimony (TCJA) — preparer determines taxability."},
    {"diagnostic_id": "D_SCH1_004", "title": "Attachment-backed amount entered — attachment not generated", "severity": "warning",
     "condition": "nonzero on any of lines 3, 4, 5, 6, 8d, 8e, 8f, 12, 13, 14, 15, 24j",
     "message": ("Amount entered on a line that requires an attached form (Schedule C/E/F/SE, Form 4797/4684, "
                 "2555, 8853, 8889, 2106, 3903) — the software does not generate that form yet. Attach the "
                 "manually prepared form: {lines}."),
     "notes": "R-S1-10. One grouped finding listing the triggering lines (not one finding per line)."},
    {"diagnostic_id": "D_SCH1_005", "title": "Line 22 is reserved", "severity": "error",
     "condition": "line 22 has a value",
     "message": "Schedule 1 line 22 is 'Reserved for future use' — it must be blank.",
     "notes": "R-S1-09."},
    {"diagnostic_id": "D_SCH1_006", "title": "1099-K memo box is disclosure-only", "severity": "info",
     "condition": "f1099k_error_amount != 0",
     "message": ("The 1099-K in-error/personal-loss box is disclosure only — the remaining 1099-K amounts "
                 "must be reported elsewhere on the return by transaction nature."),
     "notes": "R-S1-08."},
]

SCH1_SCENARIOS: list[dict] = [
    {"scenario_name": "S1-T1 — Part I distinct-value sweep -> 9 = 4,130; 10 = 6,930",
     "scenario_type": "normal", "sort_order": 1,
     "inputs": {"1": 100, "2a": 200, "3": 300, "4": 400, "5": 500, "6": 600, "7": 700,
                "8a": -110, "8b": 120, "8c": 130, "8d": -140, "8e": 150, "8f": 160, "8g": 170,
                "8h": 180, "8i": 190, "8j": 210, "8k": 220, "8l": 230, "8m": 240, "8n": 250,
                "8o": 260, "8p": 270, "8q": 280, "8r": 290, "8s": -310, "8t": 320, "8u": 330,
                "8v": 340, "8z": 350, "8z_type": "test income"},
     "expected_outputs": {"9": 4130, "10": 6930, "1040_line_8": 6930},
     "notes": ("Every addend distinct (load-bearing per the render-assertion convention): a dropped/duplicated "
               "term fails by value. Positives 4,690 + negatives -560 = 4,130; 2,800 + 4,130 = 6,930.")},
    {"scenario_name": "S1-T2 — negative combine: loss year -> 10 = -21,000 (no floor)",
     "scenario_type": "edge", "sort_order": 2,
     "inputs": {"3": -20000, "7": 4000, "8a": -5000},
     "expected_outputs": {"9": -5000, "10": -21000, "1040_line_8": -21000},
     "notes": "'Combine' semantics: business loss + NOL flow through negative. 1040 line 8/9/11 must not floor."},
    {"scenario_name": "S1-T3 — Part II distinct-value sweep -> 25 = 198; 26 = 2,188",
     "scenario_type": "normal", "sort_order": 3,
     "inputs": {"11": 110, "12": 120, "13": 130, "14": 140, "15": 150, "16": 160, "17": 170,
                "18": 180, "19a": 190, "20": 200, "21": 210, "23": 230,
                "24a": 11, "24b": 12, "24c": 13, "24d": 14, "24e": 15, "24f": 16, "24g": 17,
                "24h": 18, "24i": 19, "24j": 20, "24k": 21, "24z": 22, "24z_type": "test adj"},
     "expected_outputs": {"25": 198, "26": 2188, "1040_line_10": 2188},
     "notes": "24-series sums 11+12+...+22 = 198; lines 11-21,23 sum 1,990; 26 = 1,990 + 198 = 2,188. Line 22 contributes 0."},
    {"scenario_name": "S1-DG1 — positive NOL on 8a fires D_SCH1_001",
     "scenario_type": "failure", "sort_order": 4,
     "inputs": {"8a": 5000},
     "expected_outputs": {"D_SCH1_001_fires": True},
     "notes": "Sign-convention guard: positive 8a would overstate income by 2x the NOL."},
    {"scenario_name": "S1-DG2 — 8z amount without type fires D_SCH1_002",
     "scenario_type": "failure", "sort_order": 5,
     "inputs": {"8z": 100},
     "expected_outputs": {"D_SCH1_002_fires": True, "9": 100}},
    {"scenario_name": "S1-DG3 — alimony paid without recipient SSN fires D_SCH1_003",
     "scenario_type": "failure", "sort_order": 6,
     "inputs": {"19a": 12000},
     "expected_outputs": {"D_SCH1_003_fires": True, "26": 12000}},
]

SCH1_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-S1-01", "IRS_2025_SCH1_FORM", "primary", "Line 9 verbatim: add lines 8a through 8z"),
    ("R-S1-02", "IRS_2025_SCH1_FORM", "primary", "Line 10 verbatim: combine 1-7 and 9 -> 1040 line 8"),
    ("R-S1-02", "IRS_2025_1040_FORM", "primary", "1040 line 8 names Schedule 1 line 10"),
    ("R-S1-03", "IRS_2025_SCH1_FORM", "primary", "Line 25 verbatim: add lines 24a through 24z"),
    ("R-S1-04", "IRS_2025_SCH1_FORM", "primary", "Line 26 verbatim: add 11-23 and 25 -> 1040 line 10"),
    ("R-S1-04", "IRS_2025_1040_FORM", "primary", "1040 line 10 names Schedule 1 line 26"),
    ("R-S1-04", "IRC_62", "secondary", "Part II lines are the §62(a) above-the-line deductions"),
    ("R-S1-05", "IRS_2025_SCH1_FORM", "primary", "Parentheses printed on 8a/8d/8s only"),
    ("R-S1-06", "IRS_2025_SCH1_FORM", "primary", "8z/24z 'List type and amount' (face verbatim)"),
    ("R-S1-07", "IRS_2025_SCH1_FORM", "primary", "2b/19b/19c companion sub-lines on the face"),
    ("R-S1-08", "IRS_2025_SCH1_FORM", "primary", "1099-K box note: remaining amounts reported elsewhere"),
    ("R-S1-09", "IRS_2025_SCH1_FORM", "primary", "Line 22 'Reserved for future use'"),
    ("R-S1-10", "IRS_2025_SCH1_FORM", "primary", "'Attach Schedule C/E/F/SE, Form ...' line labels"),
]


# ═══════════════════════════════════════════════════════════════════════════
# SCHEDULE 2 — Additional Taxes
# ═══════════════════════════════════════════════════════════════════════════

SCH2_IDENTITY = {
    "form_number": "SCH_2",
    "form_title": "Schedule 2 (Form 1040) — Additional Taxes (TY2025)",
    "notes": (
        "Sprint Topic 2. Aggregation form: every line direct-entry capable; computed "
        "lines are the face sums (1z, 3, 7, 18, 21). Line 3 -> 1040 line 17; line 21 "
        "-> 1040 line 23 (supersedes spine facts schedule_2_line_3 / schedule_2_line_21). "
        "THE LOAD-BEARING SUBTLETY: line 20 (965 installment) is NOT in the line-21 sum "
        "— it sits in the left amount column for IRS tracking. Line 10 is reserved. The "
        "2025 revision adds EPE recapture lines 1d/1e/1f/19 (Form 4255). Lines 4/5/6/"
        "11/13 carry the amounts the seeded SCH_8812 spec reads via Taxpayer "
        "placeholders (se_tax_total, unreported_ss_medicare_tax, "
        "additional_medicare_tax_amount, other_employment_taxes) — the build leg "
        "re-points those reads to schedule lines (Ken confirms the exact placeholder->"
        "line mapping in the review walk; the 8812 spec's line references predate the "
        "2025 renumbering)."
    ),
}

SCH2_FACTS: list[dict] = [
    # ── Part I ──
    {"fact_key": "aptc_repayment_8962", "label": "Excess advance premium tax credit repayment — Form 8962 (1a)",
     "data_type": "decimal", "default_value": "0", "sort_order": 10,
     "notes": "Form 8962 is mandatory pre-live for marketplace clients (NEXT-UP #7); direct entry until then. D_SCH2_004."},
    {"fact_key": "repay_new_clean_vehicle_1b", "label": "Repayment of new clean vehicle credit(s) transferred to dealer (1b)",
     "data_type": "decimal", "default_value": "0", "sort_order": 11, "notes": "Form 8936 + Sch A Part II. D_SCH2_004."},
    {"fact_key": "repay_used_clean_vehicle_1c", "label": "Repayment of previously owned clean vehicle credit(s) (1c)",
     "data_type": "decimal", "default_value": "0", "sort_order": 12, "notes": "Form 8936 + Sch A Part IV. D_SCH2_004."},
    {"fact_key": "recapture_net_epe_1d", "label": "Recapture of net EPE — Form 4255 line 2a col (l) (1d)",
     "data_type": "decimal", "default_value": "0", "sort_order": 13, "notes": "NEW 2025 line. D_SCH2_004."},
    {"fact_key": "excessive_payments_1e", "label": "Excessive payments (EPs) on gross EPE — Form 4255 (1e)",
     "data_type": "decimal", "default_value": "0", "sort_order": 14, "notes": "D_SCH2_005 wants a source box checked."},
    {"fact_key": "excessive_payments_1e_source", "label": "Line 1e source box (i 1a / ii 1c / iii 1d / iv 2a)",
     "data_type": "choice", "choices": ["i_line_1a", "ii_line_1c", "iii_line_1d", "iv_line_2a"],
     "sort_order": 15, "notes": "Checkbox group c1_1[0..3]."},
    {"fact_key": "ep_20pct_1f", "label": "20% EP from Form 4255 (1f)", "data_type": "decimal",
     "default_value": "0", "sort_order": 16, "notes": "D_SCH2_005 wants a source box checked."},
    {"fact_key": "ep_20pct_1f_source", "label": "Line 1f source box (i 1a / ii 1c / iii 1d / iv 2a)",
     "data_type": "choice", "choices": ["i_line_1a", "ii_line_1c", "iii_line_1d", "iv_line_2a"],
     "sort_order": 17, "notes": "Checkbox group c1_2[0..3]."},
    {"fact_key": "other_additions_1y", "label": "Other additions to tax — amount (1y)", "data_type": "decimal",
     "default_value": "0", "sort_order": 18, "notes": "D_SCH2_001 wants the type literal."},
    {"fact_key": "other_additions_1y_type", "label": "Other additions to tax — list type (1y literal)",
     "data_type": "string", "sort_order": 19, "notes": "Widget f1_09."},
    {"fact_key": "amt_6251", "label": "Alternative minimum tax — Form 6251 (2)", "data_type": "decimal",
     "default_value": "0", "sort_order": 20,
     "notes": "AMT is DEFERRED (sprint deferred list) — direct entry; D_SCH2_004 (6251 not built)."},
    # ── Part II ──
    {"fact_key": "se_tax_4", "label": "Self-employment tax — Schedule SE (4)", "data_type": "decimal",
     "default_value": "0", "sort_order": 30,
     "notes": ("Build leg: the SCH_8812 Taxpayer placeholder se_tax_total points at this amount "
               "(one source, two consumers). Sch SE compute = post-sprint Schedule C topic. D_SCH2_004.")},
    {"fact_key": "se_exempt_4361", "label": "Line 4 checkbox: Form 4361 exemption", "data_type": "boolean",
     "sort_order": 31, "notes": "Render-only (c1_3)."},
    {"fact_key": "se_exempt_4029", "label": "Line 4 checkbox: Form 4029 exemption", "data_type": "boolean",
     "sort_order": 32, "notes": "Render-only (c1_4)."},
    {"fact_key": "se_exempt_other", "label": "Line 4 checkbox 3 + literal", "data_type": "string",
     "sort_order": 33, "notes": "Checkbox c1_5 + text f1_14; nonblank literal checks the box at render."},
    {"fact_key": "unreported_tips_tax_4137_5", "label": "SS/Medicare tax on unreported tips — Form 4137 (5)",
     "data_type": "decimal", "default_value": "0", "sort_order": 34, "notes": "D_SCH2_004 (4137 not built)."},
    {"fact_key": "uncollected_ss_8919_6", "label": "Uncollected SS/Medicare tax on wages — Form 8919 (6)",
     "data_type": "decimal", "default_value": "0", "sort_order": 35, "notes": "D_SCH2_004 (8919 not built)."},
    {"fact_key": "ira_additional_tax_5329_8", "label": "Additional tax on IRAs/tax-favored accounts — Form 5329 (8)",
     "data_type": "decimal", "default_value": "0", "sort_order": 36,
     "notes": "Topic 5 builds MINIMAL 5329 (10% + common exceptions) — this line then becomes a YELLOW feeder."},
    {"fact_key": "f5329_not_required", "label": "Line 8 checkbox: Form 5329 not required", "data_type": "boolean",
     "sort_order": 37, "notes": "Render-only (c1_6)."},
    {"fact_key": "household_employment_sch_h_9", "label": "Household employment taxes — Schedule H (9)",
     "data_type": "decimal", "default_value": "0", "sort_order": 38, "notes": "D_SCH2_004 (Sch H not built)."},
    {"fact_key": "additional_medicare_8959_11", "label": "Additional Medicare Tax — Form 8959 (11)",
     "data_type": "decimal", "default_value": "0", "sort_order": 39,
     "notes": "Build leg: SCH_8812 placeholder additional_medicare_tax_amount points here. D_SCH2_004 (8959 not built)."},
    {"fact_key": "niit_8960_12", "label": "Net investment income tax — Form 8960 (12)", "data_type": "decimal",
     "default_value": "0", "sort_order": 40, "notes": "D_SCH2_004 (8960 not built)."},
    {"fact_key": "uncollected_w2_box12_13", "label": "Uncollected SS/Medicare/RRTA from W-2 box 12 (13)",
     "data_type": "decimal", "default_value": "0", "sort_order": 41,
     "notes": ("W-2 Box 12 codes A/B/M/N are modeled on W2Box12Entry — build leg MAY compute this as a "
               "YELLOW feeder (flag for Ken). SCH_8812 placeholder other_employment_taxes points here.")},
    {"fact_key": "installment_interest_lots_14", "label": "Interest on tax due — residential lots/timeshares installments (14)",
     "data_type": "decimal", "default_value": "0", "sort_order": 42},
    {"fact_key": "installment_interest_150k_15", "label": "Interest on deferred tax — installment sales > $150,000 (15)",
     "data_type": "decimal", "default_value": "0", "sort_order": 43,
     "notes": "The $150,000 is part of the line LABEL (§453A), not a computed constant here."},
    {"fact_key": "lihc_recapture_8611_16", "label": "Recapture of low-income housing credit — Form 8611 (16)",
     "data_type": "decimal", "default_value": "0", "sort_order": 44},
    # ── line 17 series ──
    {"fact_key": "recapture_other_credits_17a", "label": "Recapture of other credits — amount (17a)",
     "data_type": "decimal", "default_value": "0", "sort_order": 50, "notes": "D_SCH2_001 wants the type literal."},
    {"fact_key": "recapture_other_credits_17a_type", "label": "Recapture of other credits — list type/form (17a literal)",
     "data_type": "string", "sort_order": 51, "notes": "Widget f2_01."},
    {"fact_key": "mortgage_subsidy_17b", "label": "Recapture of federal mortgage subsidy (17b)", "data_type": "decimal",
     "default_value": "0", "sort_order": 52},
    {"fact_key": "hsa_distributions_17c", "label": "Additional tax on HSA distributions — Form 8889 (17c)",
     "data_type": "decimal", "default_value": "0", "sort_order": 53},
    {"fact_key": "hsa_ineligible_17d", "label": "HSA tax — didn't remain eligible — Form 8889 (17d)",
     "data_type": "decimal", "default_value": "0", "sort_order": 54},
    {"fact_key": "archer_msa_17e", "label": "Additional tax on Archer MSA distributions — Form 8853 (17e)",
     "data_type": "decimal", "default_value": "0", "sort_order": 55},
    {"fact_key": "medicare_advantage_msa_17f", "label": "Additional tax on Medicare Advantage MSA distributions (17f)",
     "data_type": "decimal", "default_value": "0", "sort_order": 56},
    {"fact_key": "fractional_interest_17g", "label": "Recapture of charitable deduction — fractional interest (17g)",
     "data_type": "decimal", "default_value": "0", "sort_order": 57},
    {"fact_key": "sec_409a_17h", "label": "Nonqualified deferred comp failing §409A (17h)", "data_type": "decimal",
     "default_value": "0", "sort_order": 58},
    {"fact_key": "sec_457a_17i", "label": "Nonqualified deferred comp under §457A (17i)", "data_type": "decimal",
     "default_value": "0", "sort_order": 59},
    {"fact_key": "sec_72m5_17j", "label": "Section 72(m)(5) excess benefits tax (17j)", "data_type": "decimal",
     "default_value": "0", "sort_order": 60},
    {"fact_key": "golden_parachute_17k", "label": "Golden parachute payments (17k)", "data_type": "decimal",
     "default_value": "0", "sort_order": 61},
    {"fact_key": "trust_accumulation_17l", "label": "Tax on accumulation distribution of trusts (17l)",
     "data_type": "decimal", "default_value": "0", "sort_order": 62},
    {"fact_key": "insider_stock_comp_17m", "label": "Excise tax — insider stock comp, expatriated corp (17m)",
     "data_type": "decimal", "default_value": "0", "sort_order": 63},
    {"fact_key": "lookback_interest_17n", "label": "Look-back interest §167(g)/§460(b) — Form 8697/8866 (17n)",
     "data_type": "decimal", "default_value": "0", "sort_order": 64},
    {"fact_key": "nonresident_nec_17o", "label": "Tax on non-effectively-connected income (1040-NR period) (17o)",
     "data_type": "decimal", "default_value": "0", "sort_order": 65},
    {"fact_key": "sec_1291_interest_17p", "label": "Interest from Form 8621 line 16f (§1291 fund) (17p)",
     "data_type": "decimal", "default_value": "0", "sort_order": 66},
    {"fact_key": "f8621_line24_17q", "label": "Interest from Form 8621 line 24 (17q)", "data_type": "decimal",
     "default_value": "0", "sort_order": 67},
    {"fact_key": "other_taxes_17z", "label": "Any other taxes — amount (17z)", "data_type": "decimal",
     "default_value": "0", "sort_order": 68, "notes": "D_SCH2_001 wants the type literal."},
    {"fact_key": "other_taxes_17z_type", "label": "Any other taxes — list type (17z literal)", "data_type": "string",
     "sort_order": 69, "notes": "Widget f2_19."},
    {"fact_key": "recapture_net_epe_19", "label": "Recapture of net EPE — Form 4255 line 1d col (l) (19)",
     "data_type": "decimal", "default_value": "0", "sort_order": 75, "notes": "NEW 2025 line. IN the line-21 sum."},
    {"fact_key": "sec_965_installment_20", "label": "Section 965 net tax liability installment — Form 965-A (20)",
     "data_type": "decimal", "default_value": "0", "sort_order": 76,
     "notes": "NOT an addend of line 21 (left-column box, IRS tracking only). D_SCH2_003 info."},
    # ── Calculated outputs (traceability) ──
    {"fact_key": "additions_subtotal_1z", "label": "Add lines 1a through 1y (1z)", "data_type": "decimal",
     "sort_order": 90, "notes": "Calculated."},
    {"fact_key": "tax_total_3", "label": "Add lines 1z and 2 (3) -> 1040 line 17", "data_type": "decimal",
     "sort_order": 91, "notes": "Calculated."},
    {"fact_key": "ss_medicare_subtotal_7", "label": "Add lines 5 and 6 (7)", "data_type": "decimal",
     "sort_order": 92, "notes": "Calculated."},
    {"fact_key": "other_taxes_subtotal_18", "label": "Add lines 17a through 17z (18)", "data_type": "decimal",
     "sort_order": 93, "notes": "Calculated."},
    {"fact_key": "other_taxes_total_21", "label": "Add lines 4, 7-16, 18, and 19 (21) -> 1040 line 23",
     "data_type": "decimal", "sort_order": 94, "notes": "Calculated. EXCLUDES line 20; line 10 reserved."},
]

SCH2_RULES: list[dict] = [
    {"rule_id": "R-S2-01", "title": "Line 1z = add lines 1a through 1y", "rule_type": "calculation",
     "precedence": 1, "sort_order": 1,
     "formula": "L1z = 1a + 1b + 1c + 1d + 1e + 1f + 1y",
     "inputs": ["aptc_repayment_8962", "repay_new_clean_vehicle_1b", "repay_used_clean_vehicle_1c",
                "recapture_net_epe_1d", "excessive_payments_1e", "ep_20pct_1f", "other_additions_1y"],
     "outputs": ["L1z"],
     "description": "ONCE PER RETURN. Verbatim face sum (the 2025 1a-1f set incl. the new EPE lines)."},
    {"rule_id": "R-S2-02", "title": "Line 3 = 1z + 2 -> Form 1040 line 17", "rule_type": "calculation",
     "precedence": 2, "sort_order": 2,
     "formula": "L3 = L1z + L2. Writes Form 1040 line 17.",
     "inputs": ["amt_6251"], "outputs": ["L3", "1040.L17"],
     "description": ("ONCE PER RETURN. SUPERSEDES the spine direct-entry fact schedule_2_line_3: 1040 line "
                     "17 becomes a COMPUTED feeder (YELLOW) when Schedule 2 has entries.")},
    {"rule_id": "R-S2-03", "title": "Line 7 = add lines 5 and 6", "rule_type": "calculation",
     "precedence": 1, "sort_order": 3,
     "formula": "L7 = L5 + L6",
     "inputs": ["unreported_tips_tax_4137_5", "uncollected_ss_8919_6"], "outputs": ["L7"],
     "description": "ONCE PER RETURN. Verbatim face sum."},
    {"rule_id": "R-S2-04", "title": "Line 18 = add lines 17a through 17z", "rule_type": "calculation",
     "precedence": 1, "sort_order": 4,
     "formula": "L18 = 17a + 17b + 17c + 17d + 17e + 17f + 17g + 17h + 17i + 17j + 17k + 17l + 17m + 17n + 17o + 17p + 17q + 17z",
     "inputs": ["recapture_other_credits_17a", "mortgage_subsidy_17b", "hsa_distributions_17c",
                "hsa_ineligible_17d", "archer_msa_17e", "medicare_advantage_msa_17f", "fractional_interest_17g",
                "sec_409a_17h", "sec_457a_17i", "sec_72m5_17j", "golden_parachute_17k", "trust_accumulation_17l",
                "insider_stock_comp_17m", "lookback_interest_17n", "nonresident_nec_17o", "sec_1291_interest_17p",
                "f8621_line24_17q", "other_taxes_17z"],
     "outputs": ["L18"],
     "description": "ONCE PER RETURN. Verbatim face sum (18 addends)."},
    {"rule_id": "R-S2-05", "title": "Line 21 = 4 + (7-16) + 18 + 19 — line 20 EXCLUDED -> Form 1040 line 23",
     "rule_type": "calculation", "precedence": 2, "sort_order": 5,
     "formula": ("L21 = L4 + L7 + L8 + L9 + L11 + L12 + L13 + L14 + L15 + L16 + L18 + L19. "
                 "EXCLUDES L20 (965 installment) and L10 (reserved). L5/L6 enter via L7; 17a-17z via L18. "
                 "Writes Form 1040 line 23 (1040-NR line 23b path out of scope)."),
     "inputs": ["se_tax_4", "ira_additional_tax_5329_8", "household_employment_sch_h_9",
                "additional_medicare_8959_11", "niit_8960_12", "uncollected_w2_box12_13",
                "installment_interest_lots_14", "installment_interest_150k_15", "lihc_recapture_8611_16",
                "recapture_net_epe_19"],
     "outputs": ["L21", "1040.L23"],
     "description": ("ONCE PER RETURN. Face verbatim: 'Add lines 4, 7 through 16, 18, and 19.' The line-20 "
                     "exclusion is THE bug to guard (FA-1040-SCH2-05 pins it). SUPERSEDES the spine fact "
                     "schedule_2_line_21.")},
    {"rule_id": "R-S2-06", "title": "List-type literals required with 1y / 17a / 17z amounts", "rule_type": "validation",
     "precedence": 0, "sort_order": 6,
     "formula": "amount != 0 implies the matching type literal is nonblank (1y, 17a, 17z)",
     "inputs": ["other_additions_1y", "other_additions_1y_type", "recapture_other_credits_17a",
                "recapture_other_credits_17a_type", "other_taxes_17z", "other_taxes_17z_type"], "outputs": [],
     "description": "ONCE PER RETURN. D_SCH2_001 (warning)."},
    {"rule_id": "R-S2-07", "title": "Line 10 reserved — must be blank", "rule_type": "validation",
     "precedence": 0, "sort_order": 7,
     "formula": "L10 has no entry (face: 'Reserved for future use')",
     "inputs": [], "outputs": [],
     "description": "ONCE PER RETURN. D_SCH2_002 (error) if a value lands there."},
    {"rule_id": "R-S2-08", "title": "Line 20 is informational — never summed", "rule_type": "classification",
     "precedence": 0, "sort_order": 8,
     "formula": "sec_965_installment_20 participates in NO total (left-column box)",
     "inputs": ["sec_965_installment_20"], "outputs": [],
     "description": "ONCE PER RETURN. D_SCH2_003 (info) explains when nonzero."},
    {"rule_id": "R-S2-09", "title": "Attachment-backed lines warn until their topics build", "rule_type": "classification",
     "precedence": 0, "sort_order": 9,
     "formula": ("nonzero on any of {1a (8962), 1b/1c (8936), 1d/1e/1f/19 (4255), 2 (6251), 4 (Sch SE), "
                 "5 (4137), 6 (8919), 8 (5329), 9 (Sch H), 11 (8959), 12 (8960), 16 (8611), 17c/17d (8889), "
                 "17e/17f (8853), 17n (8697/8866), 17p/17q (8621), 20 (965-A)} -> attachment-not-generated warning"),
     "inputs": ["aptc_repayment_8962", "amt_6251", "se_tax_4", "unreported_tips_tax_4137_5",
                "uncollected_ss_8919_6", "ira_additional_tax_5329_8", "household_employment_sch_h_9",
                "additional_medicare_8959_11", "niit_8960_12", "lihc_recapture_8611_16"],
     "outputs": [],
     "description": ("ONCE PER RETURN. Same shape as R-S1-10: amounts compute (direct entry) but the "
                     "packet won't contain the attached form. D_SCH2_004 (warning, grouped). Topic 5's "
                     "minimal 5329 converts line 8 to a YELLOW feeder.")},
    {"rule_id": "R-S2-10", "title": "1e/1f require a source box (i-iv)", "rule_type": "validation",
     "precedence": 0, "sort_order": 10,
     "formula": "(excessive_payments_1e != 0 implies excessive_payments_1e_source set) AND (ep_20pct_1f != 0 implies ep_20pct_1f_source set)",
     "inputs": ["excessive_payments_1e", "excessive_payments_1e_source", "ep_20pct_1f", "ep_20pct_1f_source"],
     "outputs": [],
     "description": "ONCE PER RETURN. Face: 'Check applicable box and enter amount.' D_SCH2_005 (warning)."},
]

SCH2_LINES: list[dict] = [
    {"line_number": "1a", "description": "Excess advance premium tax credit repayment — attach Form 8962",
     "line_type": "input", "sort_order": 10},
    {"line_number": "1b", "description": "Repayment of new clean vehicle credit(s) transferred to dealer — Form 8936",
     "line_type": "input", "sort_order": 11},
    {"line_number": "1c", "description": "Repayment of previously owned clean vehicle credit(s) — Form 8936",
     "line_type": "input", "sort_order": 12},
    {"line_number": "1d", "description": "Recapture of net EPE from Form 4255, line 2a, column (l)",
     "line_type": "input", "sort_order": 13, "notes": "NEW 2025."},
    {"line_number": "1e", "description": "Excessive payments on gross EPE from Form 4255 (source boxes i-iv)",
     "line_type": "input", "source_rules": ["R-S2-10"], "sort_order": 14},
    {"line_number": "1f", "description": "20% EP from Form 4255 (source boxes i-iv)", "line_type": "input",
     "source_rules": ["R-S2-10"], "sort_order": 15},
    {"line_number": "1y", "description": "Other additions to tax — list type and amount", "line_type": "input",
     "source_rules": ["R-S2-06"], "sort_order": 16},
    {"line_number": "1z", "description": "Add lines 1a through 1y", "line_type": "subtotal",
     "source_rules": ["R-S2-01"], "sort_order": 17},
    {"line_number": "2", "description": "Alternative minimum tax — attach Form 6251", "line_type": "input",
     "sort_order": 18, "notes": "AMT engine deferred (sprint list) — direct entry."},
    {"line_number": "3", "description": "Add lines 1z and 2", "line_type": "total",
     "source_rules": ["R-S2-02"], "destination_form": "Form 1040 line 17", "sort_order": 19},
    {"line_number": "4", "description": "Self-employment tax — attach Schedule SE (exemption boxes 4361/4029/other)",
     "line_type": "input", "sort_order": 30,
     "notes": "8812 placeholder se_tax_total points here (build leg)."},
    {"line_number": "5", "description": "SS/Medicare tax on unreported tip income — attach Form 4137",
     "line_type": "input", "sort_order": 31},
    {"line_number": "6", "description": "Uncollected SS/Medicare tax on wages — attach Form 8919",
     "line_type": "input", "sort_order": 32},
    {"line_number": "7", "description": "Total additional SS/Medicare tax = add lines 5 and 6", "line_type": "subtotal",
     "source_rules": ["R-S2-03"], "sort_order": 33},
    {"line_number": "8", "description": "Additional tax on IRAs/tax-favored accounts — Form 5329 (not-required checkbox)",
     "line_type": "input", "sort_order": 34, "notes": "Topic 5 minimal 5329 makes this a YELLOW feeder."},
    {"line_number": "9", "description": "Household employment taxes — attach Schedule H", "line_type": "input", "sort_order": 35},
    {"line_number": "10", "description": "Reserved for future use", "line_type": "informational",
     "source_rules": ["R-S2-07"], "sort_order": 36, "notes": "Must stay blank (D_SCH2_002)."},
    {"line_number": "11", "description": "Additional Medicare Tax — attach Form 8959", "line_type": "input",
     "sort_order": 37, "notes": "8812 placeholder additional_medicare_tax_amount points here (build leg)."},
    {"line_number": "12", "description": "Net investment income tax — attach Form 8960", "line_type": "input", "sort_order": 38},
    {"line_number": "13", "description": "Uncollected SS/Medicare/RRTA tax from W-2 box 12", "line_type": "input",
     "sort_order": 39, "notes": "Candidate YELLOW feeder from W2Box12Entry codes A/B/M/N — flag for Ken."},
    {"line_number": "14", "description": "Interest on tax due — residential lots/timeshares installment income",
     "line_type": "input", "sort_order": 40},
    {"line_number": "15", "description": "Interest on deferred tax — installment sales with sales price over $150,000",
     "line_type": "input", "sort_order": 41},
    {"line_number": "16", "description": "Recapture of low-income housing credit — attach Form 8611",
     "line_type": "input", "sort_order": 42},
    {"line_number": "17a", "description": "Recapture of other credits — list type, form number, and amount",
     "line_type": "input", "source_rules": ["R-S2-06"], "sort_order": 50},
    {"line_number": "17b", "description": "Recapture of federal mortgage subsidy", "line_type": "input", "sort_order": 51},
    {"line_number": "17c", "description": "Additional tax on HSA distributions — attach Form 8889", "line_type": "input", "sort_order": 52},
    {"line_number": "17d", "description": "HSA tax — didn't remain eligible — attach Form 8889", "line_type": "input", "sort_order": 53},
    {"line_number": "17e", "description": "Additional tax on Archer MSA distributions — attach Form 8853", "line_type": "input", "sort_order": 54},
    {"line_number": "17f", "description": "Additional tax on Medicare Advantage MSA distributions — Form 8853",
     "line_type": "input", "sort_order": 55},
    {"line_number": "17g", "description": "Recapture of charitable deduction — fractional interest in tangible property",
     "line_type": "input", "sort_order": 56},
    {"line_number": "17h", "description": "Nonqualified deferred comp failing §409A requirements", "line_type": "input", "sort_order": 57},
    {"line_number": "17i", "description": "Nonqualified deferred comp under §457A", "line_type": "input", "sort_order": 58},
    {"line_number": "17j", "description": "Section 72(m)(5) excess benefits tax", "line_type": "input", "sort_order": 59},
    {"line_number": "17k", "description": "Golden parachute payments", "line_type": "input", "sort_order": 60},
    {"line_number": "17l", "description": "Tax on accumulation distribution of trusts", "line_type": "input", "sort_order": 61},
    {"line_number": "17m", "description": "Excise tax on insider stock compensation (expatriated corporation)",
     "line_type": "input", "sort_order": 62},
    {"line_number": "17n", "description": "Look-back interest §167(g)/§460(b) — Form 8697/8866", "line_type": "input", "sort_order": 63},
    {"line_number": "17o", "description": "Tax on non-effectively-connected income (1040-NR period)", "line_type": "input", "sort_order": 64},
    {"line_number": "17p", "description": "Interest from Form 8621 line 16f (§1291 fund)", "line_type": "input", "sort_order": 65},
    {"line_number": "17q", "description": "Interest from Form 8621 line 24", "line_type": "input", "sort_order": 66},
    {"line_number": "17z", "description": "Any other taxes — list type and amount", "line_type": "input",
     "source_rules": ["R-S2-06"], "sort_order": 67},
    {"line_number": "18", "description": "Total additional taxes = add lines 17a through 17z", "line_type": "subtotal",
     "source_rules": ["R-S2-04"], "sort_order": 68},
    {"line_number": "19", "description": "Recapture of net EPE from Form 4255, line 1d, column (l)",
     "line_type": "input", "sort_order": 69, "notes": "NEW 2025. IN the line-21 sum."},
    {"line_number": "20", "description": "Section 965 net tax liability installment — Form 965-A (NOT in line 21)",
     "line_type": "informational", "source_rules": ["R-S2-08"], "sort_order": 70,
     "notes": "Left-column amount box; IRS tracking only."},
    {"line_number": "21", "description": "Add lines 4, 7-16, 18, and 19 — total other taxes", "line_type": "total",
     "source_rules": ["R-S2-05"], "destination_form": "Form 1040 line 23", "sort_order": 71},
]

SCH2_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_SCH2_001", "title": "1y/17a/17z amount without a type literal", "severity": "warning",
     "condition": "(1y != 0 AND 1y type blank) OR (17a != 0 AND 17a type blank) OR (17z != 0 AND 17z type blank)",
     "message": "Lines 1y/17a/17z require 'list type and amount' — enter the description literal.",
     "notes": "R-S2-06."},
    {"diagnostic_id": "D_SCH2_002", "title": "Line 10 is reserved", "severity": "error",
     "condition": "line 10 has a value",
     "message": "Schedule 2 line 10 is 'Reserved for future use' — it must be blank.",
     "notes": "R-S2-07."},
    {"diagnostic_id": "D_SCH2_003", "title": "Line 20 (965 installment) is not included in line 21", "severity": "info",
     "condition": "sec_965_installment_20 != 0",
     "message": ("The §965 net tax liability installment (line 20) is reported for IRS tracking only — it is "
                 "NOT added into line 21 or Form 1040 line 23."),
     "notes": "R-S2-08. Face verbatim: line 21 adds '4, 7 through 16, 18, and 19'."},
    {"diagnostic_id": "D_SCH2_004", "title": "Attachment-backed amount entered — attachment not generated", "severity": "warning",
     "condition": "nonzero on any attachment-backed line (8962/8936/4255/6251/SE/4137/8919/5329/H/8959/8960/8611/8889/8853/8697/8866/8621/965-A)",
     "message": ("Amount entered on a line that requires an attached form — the software does not generate "
                 "that form yet. Attach the manually prepared form: {lines}."),
     "notes": "R-S2-09. One grouped finding listing the triggering lines."},
    {"diagnostic_id": "D_SCH2_005", "title": "1e/1f amount without a source box", "severity": "warning",
     "condition": "(excessive_payments_1e != 0 AND no 1e box) OR (ep_20pct_1f != 0 AND no 1f box)",
     "message": "Lines 1e/1f require checking the applicable source box (i-iv) with the amount.",
     "notes": "R-S2-10."},
]

SCH2_SCENARIOS: list[dict] = [
    {"scenario_name": "S2-T1 — Part I distinct-value sweep -> 1z = 910; 3 = 1,910",
     "scenario_type": "normal", "sort_order": 1,
     "inputs": {"1a": 100, "1b": 110, "1c": 120, "1d": 130, "1e": 140, "1e_source": "i_line_1a",
                "1f": 150, "1f_source": "ii_line_1c", "1y": 160, "1y_type": "test addition", "2": 1000},
     "expected_outputs": {"1z": 910, "3": 1910, "1040_line_17": 1910},
     "notes": "Every addend distinct; a dropped/duplicated term fails by value."},
    {"scenario_name": "S2-T2 — Part II sweep with line 20 EXCLUDED -> 21 = 1,884 (not 3,884)",
     "scenario_type": "edge", "sort_order": 2,
     "inputs": {"4": 400, "5": 50, "6": 60, "8": 80, "9": 90, "11": 111, "12": 112, "13": 113,
                "14": 114, "15": 115, "16": 116,
                "17a": 10, "17a_type": "recapture test", "17b": 11, "17c": 12, "17d": 13, "17e": 14,
                "17f": 15, "17g": 16, "17h": 17, "17i": 18, "17j": 19, "17k": 20, "17l": 21, "17m": 22,
                "17n": 23, "17o": 24, "17p": 25, "17q": 26, "17z": 27, "17z_type": "other test",
                "19": 190, "20": 2000},
     "expected_outputs": {"7": 110, "18": 333, "21": 1884, "1040_line_23": 1884},
     "notes": ("THE load-bearing scenario: 21 = 400 + (110+80+90+111+112+113+114+115+116=961) + 333 + 190 "
               "= 1,884. A compute that sums line 20 produces 3,884 and fails. 18 = sum(10..27) = 333.")},
    {"scenario_name": "S2-DG1 — value on reserved line 10 fires D_SCH2_002",
     "scenario_type": "failure", "sort_order": 3,
     "inputs": {"10": 50},
     "expected_outputs": {"D_SCH2_002_fires": True}},
    {"scenario_name": "S2-DG2 — line 20 alone: 21 stays 0, D_SCH2_003 info fires",
     "scenario_type": "edge", "sort_order": 4,
     "inputs": {"20": 5000},
     "expected_outputs": {"21": 0, "D_SCH2_003_fires": True, "1040_line_23": 0}},
]

SCH2_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-S2-01", "IRS_2025_SCH2_FORM", "primary", "Line 1z verbatim: add lines 1a through 1y"),
    ("R-S2-02", "IRS_2025_SCH2_FORM", "primary", "Line 3 verbatim: add 1z and 2 -> 1040 line 17"),
    ("R-S2-02", "IRS_2025_1040_FORM", "primary", "1040 line 17 names Schedule 2 line 3"),
    ("R-S2-03", "IRS_2025_SCH2_FORM", "primary", "Line 7 verbatim: add lines 5 and 6"),
    ("R-S2-04", "IRS_2025_SCH2_FORM", "primary", "Line 18 verbatim: add lines 17a through 17z"),
    ("R-S2-05", "IRS_2025_SCH2_FORM", "primary", "Line 21 verbatim: add 4, 7-16, 18, and 19 (20 excluded)"),
    ("R-S2-05", "IRS_2025_1040_FORM", "primary", "1040 line 23 names Schedule 2 line 21"),
    ("R-S2-06", "IRS_2025_SCH2_FORM", "primary", "1y/17a/17z 'list type and amount' (face verbatim)"),
    ("R-S2-07", "IRS_2025_SCH2_FORM", "primary", "Line 10 'Reserved for future use'"),
    ("R-S2-08", "IRS_2025_SCH2_FORM", "primary", "Line 20 sits in the left column; line 21 sum omits it"),
    ("R-S2-09", "IRS_2025_SCH2_FORM", "primary", "'Attach Form/Schedule ...' line labels"),
    ("R-S2-10", "IRS_2025_SCH2_FORM", "primary", "1e/1f 'Check applicable box and enter amount'"),
]


# ═══════════════════════════════════════════════════════════════════════════
# SCHEDULE 3 — Additional Credits and Payments
# ═══════════════════════════════════════════════════════════════════════════

SCH3_IDENTITY = {
    "form_number": "SCH_3",
    "form_title": "Schedule 3 (Form 1040) — Additional Credits and Payments (TY2025)",
    "notes": (
        "Sprint Topic 2. Aggregation form: every line direct-entry capable; computed "
        "lines are the face sums (7, 8, 14, 15). Line 8 -> 1040 line 20; line 15 -> "
        "1040 line 31 (supersedes spine facts schedule_3_line_8 / schedule_3_line_15). "
        "The 2025 revision is a SINGLE page; line 6e is reserved. Line 6l (Form 8978) "
        "may be NEGATIVE. The SCH_8812 Taxpayer placeholders "
        "schedule_3_pre_ctc_credits_total (lines 1-4 + 5a + 5b + 6l per the 8812 "
        "Credit Limit Worksheet) and excess_ss_rrta_withheld (line 11) get re-pointed "
        "to schedule lines at the build leg — Ken confirms the worksheet line set in "
        "the review walk. Topic 9 ride-along (Form 8880) lands on line 4; Topic 7's "
        "Form 2441 (post-sprint) lands on line 2."
    ),
}

SCH3_FACTS: list[dict] = [
    # ── Part I ──
    {"fact_key": "foreign_tax_credit_1116_1", "label": "Foreign tax credit — Form 1116 if required (1)",
     "data_type": "decimal", "default_value": "0", "sort_order": 10,
     "notes": "Direct entry. Under the $300/$600 de-minimis election no 1116 attaches — preparer decides. D_SCH3_003."},
    {"fact_key": "dependent_care_credit_2441_2", "label": "Child/dependent care credit — Form 2441 line 11 (2)",
     "data_type": "decimal", "default_value": "0", "sort_order": 11, "notes": "Form 2441 = post-sprint #5. D_SCH3_003."},
    {"fact_key": "education_credits_8863_3", "label": "Education credits — Form 8863 line 19 (3)",
     "data_type": "decimal", "default_value": "0", "sort_order": 12, "notes": "Form 8863 = post-sprint #8. D_SCH3_003."},
    {"fact_key": "savers_credit_8880_4", "label": "Retirement savings contributions credit — Form 8880 (4)",
     "data_type": "decimal", "default_value": "0", "sort_order": 13,
     "notes": "Sprint Topic 9 ride-along builds 8880 — this line then becomes a YELLOW feeder."},
    {"fact_key": "residential_clean_energy_5a", "label": "Residential clean energy credit — Form 5695 line 15 (5a)",
     "data_type": "decimal", "default_value": "0", "sort_order": 14, "notes": "D_SCH3_003 (5695 not built)."},
    {"fact_key": "home_improvement_5b", "label": "Energy efficient home improvement credit — Form 5695 line 32 (5b)",
     "data_type": "decimal", "default_value": "0", "sort_order": 15, "notes": "D_SCH3_003 (5695 not built)."},
    {"fact_key": "general_business_3800_6a", "label": "General business credit — Form 3800 (6a)",
     "data_type": "decimal", "default_value": "0", "sort_order": 20},
    {"fact_key": "prior_year_min_tax_8801_6b", "label": "Credit for prior year minimum tax — Form 8801 (6b)",
     "data_type": "decimal", "default_value": "0", "sort_order": 21},
    {"fact_key": "adoption_credit_8839_6c", "label": "Adoption credit — Form 8839 (6c)", "data_type": "decimal",
     "default_value": "0", "sort_order": 22,
     "notes": "NONREFUNDABLE portion. The refundable portion is 1040 line 30 (spine fact refundable_adoption_credit)."},
    {"fact_key": "elderly_disabled_sch_r_6d", "label": "Credit for the elderly or disabled — Schedule R (6d)",
     "data_type": "decimal", "default_value": "0", "sort_order": 23},
    {"fact_key": "clean_vehicle_8936_6f", "label": "Clean vehicle credit — Form 8936 (6f)", "data_type": "decimal",
     "default_value": "0", "sort_order": 24},
    {"fact_key": "mortgage_interest_8396_6g", "label": "Mortgage interest credit — Form 8396 (6g)",
     "data_type": "decimal", "default_value": "0", "sort_order": 25,
     "notes": "A Worksheet-B credit on the 8812 side (D009 there fires when claims_credits_requiring_worksheet_b)."},
    {"fact_key": "dc_homebuyer_8859_6h", "label": "DC first-time homebuyer credit — Form 8859 (6h)",
     "data_type": "decimal", "default_value": "0", "sort_order": 26, "notes": "Also a Worksheet-B credit."},
    {"fact_key": "electric_vehicle_8834_6i", "label": "Qualified electric vehicle credit — Form 8834 (6i)",
     "data_type": "decimal", "default_value": "0", "sort_order": 27},
    {"fact_key": "alt_fuel_refueling_8911_6j", "label": "Alternative fuel vehicle refueling property credit — Form 8911 (6j)",
     "data_type": "decimal", "default_value": "0", "sort_order": 28},
    {"fact_key": "tax_credit_bonds_8912_6k", "label": "Credit to holders of tax credit bonds — Form 8912 (6k)",
     "data_type": "decimal", "default_value": "0", "sort_order": 29},
    {"fact_key": "form_8978_amount_6l", "label": "Amount on Form 8978, line 14 (6l) — may be NEGATIVE",
     "data_type": "decimal", "default_value": "0", "sort_order": 30,
     "notes": "Partner audit-adjustment pushout; a negative 8978 amount REDUCES line 7 (no floor on the addend)."},
    {"fact_key": "prev_owned_clean_vehicle_6m", "label": "Credit for previously owned clean vehicles — Form 8936 (6m)",
     "data_type": "decimal", "default_value": "0", "sort_order": 31},
    {"fact_key": "other_nonref_credits_6z", "label": "Other nonrefundable credits — amount (6z)", "data_type": "decimal",
     "default_value": "0", "sort_order": 32, "notes": "D_SCH3_001 wants the type literal."},
    {"fact_key": "other_nonref_credits_6z_type", "label": "Other nonrefundable credits — list type (6z literal)",
     "data_type": "string", "sort_order": 33},
    # ── Part II ──
    {"fact_key": "net_ptc_8962_9", "label": "Net premium tax credit — Form 8962 (9)", "data_type": "decimal",
     "default_value": "0", "sort_order": 40, "notes": "Form 8962 = NEXT-UP #7. D_SCH3_003."},
    {"fact_key": "extension_payment_10", "label": "Amount paid with extension request (10)", "data_type": "decimal",
     "default_value": "0", "sort_order": 41,
     "notes": "Candidate YELLOW feeder from the Extensions tab when 1040 extensions are modeled — flag for Ken."},
    {"fact_key": "excess_ss_rrta_11", "label": "Excess social security and tier 1 RRTA tax withheld (11)",
     "data_type": "decimal", "default_value": "0", "sort_order": 42,
     "notes": ("Build leg: the SCH_8812 placeholder excess_ss_rrta_withheld points here (one source, two "
               "consumers). Computable from W-2 rows when multi-employer SS-wage caps are modeled — future upgrade.")},
    {"fact_key": "fuel_tax_credit_4136_12", "label": "Credit for federal tax on fuels — Form 4136 (12)",
     "data_type": "decimal", "default_value": "0", "sort_order": 43, "notes": "D_SCH3_003 (4136 not built at 1040 level)."},
    {"fact_key": "form_2439_13a", "label": "Form 2439 (undistributed LTCG tax paid) (13a)", "data_type": "decimal",
     "default_value": "0", "sort_order": 44},
    {"fact_key": "sec_1341_credit_13b", "label": "Section 1341 credit — claim of right repayment (13b)",
     "data_type": "decimal", "default_value": "0", "sort_order": 45},
    {"fact_key": "elective_payment_3800_13c", "label": "Net elective payment election — Form 3800 Part III line 6 col (j) (13c)",
     "data_type": "decimal", "default_value": "0", "sort_order": 46},
    {"fact_key": "deferred_965_13d", "label": "Deferred amount of net 965 tax liability (13d)", "data_type": "decimal",
     "default_value": "0", "sort_order": 47},
    {"fact_key": "other_refundable_13z", "label": "Other payments or refundable credits — amount (13z)",
     "data_type": "decimal", "default_value": "0", "sort_order": 48, "notes": "D_SCH3_001 wants the type literal."},
    {"fact_key": "other_refundable_13z_type", "label": "Other payments or refundable credits — list type (13z literal)",
     "data_type": "string", "sort_order": 49},
    # ── Calculated outputs (traceability) ──
    {"fact_key": "other_nonref_subtotal_7", "label": "Add lines 6a through 6z (7)", "data_type": "decimal",
     "sort_order": 60, "notes": "Calculated. 6e reserved; 6l may be negative."},
    {"fact_key": "nonref_credits_total_8", "label": "Add lines 1-4, 5a, 5b, and 7 (8) -> 1040 line 20",
     "data_type": "decimal", "sort_order": 61, "notes": "Calculated."},
    {"fact_key": "other_refundable_subtotal_14", "label": "Add lines 13a through 13z (14)", "data_type": "decimal",
     "sort_order": 62, "notes": "Calculated."},
    {"fact_key": "payments_credits_total_15", "label": "Add lines 9-12 and 14 (15) -> 1040 line 31",
     "data_type": "decimal", "sort_order": 63, "notes": "Calculated."},
]

SCH3_RULES: list[dict] = [
    {"rule_id": "R-S3-01", "title": "Line 7 = add lines 6a through 6z", "rule_type": "calculation",
     "precedence": 1, "sort_order": 1,
     "formula": "L7 = 6a + 6b + 6c + 6d + 6f + 6g + 6h + 6i + 6j + 6k + 6l + 6m + 6z   (6e reserved = 0; 6l may be negative)",
     "inputs": ["general_business_3800_6a", "prior_year_min_tax_8801_6b", "adoption_credit_8839_6c",
                "elderly_disabled_sch_r_6d", "clean_vehicle_8936_6f", "mortgage_interest_8396_6g",
                "dc_homebuyer_8859_6h", "electric_vehicle_8834_6i", "alt_fuel_refueling_8911_6j",
                "tax_credit_bonds_8912_6k", "form_8978_amount_6l", "prev_owned_clean_vehicle_6m",
                "other_nonref_credits_6z"],
     "outputs": ["L7"],
     "description": "ONCE PER RETURN. Verbatim face sum. R-S3-06 polices 6e."},
    {"rule_id": "R-S3-02", "title": "Line 8 = 1 + 2 + 3 + 4 + 5a + 5b + 7 -> Form 1040 line 20", "rule_type": "calculation",
     "precedence": 2, "sort_order": 2,
     "formula": "L8 = L1 + L2 + L3 + L4 + L5a + L5b + L7. Writes Form 1040 line 20.",
     "inputs": ["foreign_tax_credit_1116_1", "dependent_care_credit_2441_2", "education_credits_8863_3",
                "savers_credit_8880_4", "residential_clean_energy_5a", "home_improvement_5b"],
     "outputs": ["L8", "1040.L20"],
     "description": ("ONCE PER RETURN. Face verbatim: 'Add lines 1 through 4, 5a, 5b, and 7.' SUPERSEDES the "
                     "spine direct-entry fact schedule_3_line_8: 1040 line 20 becomes a COMPUTED feeder.")},
    {"rule_id": "R-S3-03", "title": "Line 14 = add lines 13a through 13z", "rule_type": "calculation",
     "precedence": 1, "sort_order": 3,
     "formula": "L14 = 13a + 13b + 13c + 13d + 13z",
     "inputs": ["form_2439_13a", "sec_1341_credit_13b", "elective_payment_3800_13c", "deferred_965_13d",
                "other_refundable_13z"],
     "outputs": ["L14"],
     "description": "ONCE PER RETURN. Verbatim face sum."},
    {"rule_id": "R-S3-04", "title": "Line 15 = 9 + 10 + 11 + 12 + 14 -> Form 1040 line 31", "rule_type": "calculation",
     "precedence": 2, "sort_order": 4,
     "formula": "L15 = L9 + L10 + L11 + L12 + L14. Writes Form 1040 line 31.",
     "inputs": ["net_ptc_8962_9", "extension_payment_10", "excess_ss_rrta_11", "fuel_tax_credit_4136_12"],
     "outputs": ["L15", "1040.L31"],
     "description": ("ONCE PER RETURN. Face verbatim: 'Add lines 9 through 12 and 14.' SUPERSEDES the spine "
                     "fact schedule_3_line_15: 1040 line 31 becomes a COMPUTED feeder.")},
    {"rule_id": "R-S3-05", "title": "List-type literals required with 6z / 13z amounts", "rule_type": "validation",
     "precedence": 0, "sort_order": 5,
     "formula": "(6z != 0 implies 6z type nonblank) AND (13z != 0 implies 13z type nonblank)",
     "inputs": ["other_nonref_credits_6z", "other_nonref_credits_6z_type", "other_refundable_13z",
                "other_refundable_13z_type"], "outputs": [],
     "description": "ONCE PER RETURN. D_SCH3_001 (warning)."},
    {"rule_id": "R-S3-06", "title": "Line 6e reserved — must be blank", "rule_type": "validation",
     "precedence": 0, "sort_order": 6,
     "formula": "L6e has no entry (face: 'Reserved for future use')",
     "inputs": [], "outputs": [],
     "description": "ONCE PER RETURN. D_SCH3_002 (error) if a value lands there."},
    {"rule_id": "R-S3-07", "title": "Attachment-backed lines warn until their topics build", "rule_type": "classification",
     "precedence": 0, "sort_order": 7,
     "formula": ("nonzero on any of {1 (1116 if required), 2 (2441), 3 (8863), 4 (8880), 5a/5b (5695), "
                 "6a (3800), 6b (8801), 6c (8839), 6d (Sch R), 6f/6m (8936), 6g (8396), 6h (8859), 6i (8834), "
                 "6j (8911), 6k (8912), 6l (8978), 9 (8962), 12 (4136), 13a (2439)} -> attachment-not-generated warning"),
     "inputs": ["foreign_tax_credit_1116_1", "dependent_care_credit_2441_2", "education_credits_8863_3",
                "savers_credit_8880_4", "residential_clean_energy_5a", "home_improvement_5b",
                "net_ptc_8962_9", "fuel_tax_credit_4136_12"],
     "outputs": [],
     "description": ("ONCE PER RETURN. Same shape as R-S1-10/R-S2-09. D_SCH3_003 (warning, grouped). Topic 9 "
                     "(8880) and post-sprint 2441/8863/8962 convert their lines to YELLOW feeders.")},
    {"rule_id": "R-S3-08", "title": "Line 6l (Form 8978) may be negative", "rule_type": "classification",
     "precedence": 0, "sort_order": 8,
     "formula": "form_8978_amount_6l accepts negative values; no floor inside the line-7 sum",
     "inputs": ["form_8978_amount_6l"], "outputs": [],
     "description": ("ONCE PER RETURN. BBA partner pushout adjustments can be a NEGATIVE credit amount that "
                     "reduces line 7 (face: 'See instructions'). Don't clamp at entry.")},
]

SCH3_LINES: list[dict] = [
    {"line_number": "1", "description": "Foreign tax credit — attach Form 1116 if required", "line_type": "input", "sort_order": 10},
    {"line_number": "2", "description": "Credit for child and dependent care expenses — Form 2441 line 11",
     "line_type": "input", "sort_order": 11, "notes": "Form 2441 = post-sprint #5."},
    {"line_number": "3", "description": "Education credits — Form 8863 line 19", "line_type": "input",
     "sort_order": 12, "notes": "Form 8863 = post-sprint #8."},
    {"line_number": "4", "description": "Retirement savings contributions credit — attach Form 8880",
     "line_type": "input", "sort_order": 13, "notes": "Topic 9 ride-along feeder."},
    {"line_number": "5a", "description": "Residential clean energy credit — Form 5695 line 15", "line_type": "input", "sort_order": 14},
    {"line_number": "5b", "description": "Energy efficient home improvement credit — Form 5695 line 32",
     "line_type": "input", "sort_order": 15},
    {"line_number": "6a", "description": "General business credit — attach Form 3800", "line_type": "input", "sort_order": 20},
    {"line_number": "6b", "description": "Credit for prior year minimum tax — attach Form 8801", "line_type": "input", "sort_order": 21},
    {"line_number": "6c", "description": "Adoption credit (nonrefundable) — attach Form 8839", "line_type": "input",
     "sort_order": 22, "notes": "Refundable portion = 1040 line 30."},
    {"line_number": "6d", "description": "Credit for the elderly or disabled — attach Schedule R", "line_type": "input", "sort_order": 23},
    {"line_number": "6e", "description": "Reserved for future use", "line_type": "informational",
     "source_rules": ["R-S3-06"], "sort_order": 24, "notes": "Must stay blank (D_SCH3_002)."},
    {"line_number": "6f", "description": "Clean vehicle credit — attach Form 8936", "line_type": "input", "sort_order": 25},
    {"line_number": "6g", "description": "Mortgage interest credit — attach Form 8396", "line_type": "input",
     "sort_order": 26, "notes": "8812 Worksheet-B credit."},
    {"line_number": "6h", "description": "District of Columbia first-time homebuyer credit — attach Form 8859",
     "line_type": "input", "sort_order": 27, "notes": "8812 Worksheet-B credit."},
    {"line_number": "6i", "description": "Qualified electric vehicle credit — attach Form 8834", "line_type": "input", "sort_order": 28},
    {"line_number": "6j", "description": "Alternative fuel vehicle refueling property credit — attach Form 8911",
     "line_type": "input", "sort_order": 29},
    {"line_number": "6k", "description": "Credit to holders of tax credit bonds — attach Form 8912", "line_type": "input", "sort_order": 30},
    {"line_number": "6l", "description": "Amount on Form 8978, line 14 (may be NEGATIVE)", "line_type": "input",
     "source_rules": ["R-S3-08"], "sort_order": 31},
    {"line_number": "6m", "description": "Credit for previously owned clean vehicles — attach Form 8936",
     "line_type": "input", "sort_order": 32},
    {"line_number": "6z", "description": "Other nonrefundable credits — list type and amount", "line_type": "input",
     "source_rules": ["R-S3-05"], "sort_order": 33, "notes": "Type literal f2_22 (page-1 widget with an f2_ name — render-leg note)."},
    {"line_number": "7", "description": "Total other nonrefundable credits = add lines 6a through 6z",
     "line_type": "subtotal", "source_rules": ["R-S3-01"], "sort_order": 34},
    {"line_number": "8", "description": "Add lines 1-4, 5a, 5b, and 7", "line_type": "total",
     "source_rules": ["R-S3-02"], "destination_form": "Form 1040 line 20", "sort_order": 35},
    {"line_number": "9", "description": "Net premium tax credit — attach Form 8962", "line_type": "input", "sort_order": 40},
    {"line_number": "10", "description": "Amount paid with request for extension to file", "line_type": "input", "sort_order": 41},
    {"line_number": "11", "description": "Excess social security and tier 1 RRTA tax withheld", "line_type": "input",
     "sort_order": 42, "notes": "8812 placeholder excess_ss_rrta_withheld points here (build leg)."},
    {"line_number": "12", "description": "Credit for federal tax on fuels — attach Form 4136", "line_type": "input", "sort_order": 43},
    {"line_number": "13a", "description": "Form 2439 (undistributed long-term capital gains tax)", "line_type": "input", "sort_order": 50},
    {"line_number": "13b", "description": "Section 1341 credit — repayment of amounts included in income from earlier years",
     "line_type": "input", "sort_order": 51},
    {"line_number": "13c", "description": "Net elective payment election amount — Form 3800 Part III line 6 col (j)",
     "line_type": "input", "sort_order": 52},
    {"line_number": "13d", "description": "Deferred amount of net 965 tax liability", "line_type": "input", "sort_order": 53},
    {"line_number": "13z", "description": "Other refundable credits — list type and amount", "line_type": "input",
     "source_rules": ["R-S3-05"], "sort_order": 54},
    {"line_number": "14", "description": "Total other payments or refundable credits = add lines 13a through 13z",
     "line_type": "subtotal", "source_rules": ["R-S3-03"], "sort_order": 55},
    {"line_number": "15", "description": "Add lines 9-12 and 14", "line_type": "total",
     "source_rules": ["R-S3-04"], "destination_form": "Form 1040 line 31", "sort_order": 56},
]

SCH3_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_SCH3_001", "title": "6z/13z amount without a type literal", "severity": "warning",
     "condition": "(6z != 0 AND 6z type blank) OR (13z != 0 AND 13z type blank)",
     "message": "Lines 6z/13z require 'list type and amount' — enter the description literal.",
     "notes": "R-S3-05."},
    {"diagnostic_id": "D_SCH3_002", "title": "Line 6e is reserved", "severity": "error",
     "condition": "line 6e has a value",
     "message": "Schedule 3 line 6e is 'Reserved for future use' — it must be blank.",
     "notes": "R-S3-06."},
    {"diagnostic_id": "D_SCH3_003", "title": "Attachment-backed amount entered — attachment not generated", "severity": "warning",
     "condition": "nonzero on any attachment-backed line (1116/2441/8863/8880/5695/3800/8801/8839/Sch R/8936/8396/8859/8834/8911/8912/8978/8962/4136/2439)",
     "message": ("Amount entered on a line that requires an attached form — the software does not generate "
                 "that form yet. Attach the manually prepared form: {lines}."),
     "notes": "R-S3-07. One grouped finding listing the triggering lines."},
]

SCH3_SCENARIOS: list[dict] = [
    {"scenario_name": "S3-T1 — Part I distinct-value sweep -> 7 = 208; 8 = 2,238",
     "scenario_type": "normal", "sort_order": 1,
     "inputs": {"1": 100, "2": 200, "3": 300, "4": 400, "5a": 510, "5b": 520,
                "6a": 10, "6b": 11, "6c": 12, "6d": 13, "6f": 14, "6g": 15, "6h": 16, "6i": 17,
                "6j": 18, "6k": 19, "6l": 20, "6m": 21, "6z": 22, "6z_type": "test credit"},
     "expected_outputs": {"7": 208, "8": 2238, "1040_line_20": 2238},
     "notes": "Every addend distinct. 6-series sums 10+11+...+22 (no 6e) = 208; 8 = 2,030 + 208 = 2,238."},
    {"scenario_name": "S3-T2 — Part II distinct-value sweep -> 14 = 165; 15 = 4,365",
     "scenario_type": "normal", "sort_order": 2,
     "inputs": {"9": 900, "10": 1000, "11": 1100, "12": 1200,
                "13a": 31, "13b": 32, "13c": 33, "13d": 34, "13z": 35, "13z_type": "test refundable"},
     "expected_outputs": {"14": 165, "15": 4365, "1040_line_31": 4365},
     "notes": "14 = 31+32+33+34+35 = 165; 15 = 4,200 + 165 = 4,365."},
    {"scenario_name": "S3-T3 — negative 8978 amount reduces line 7 (6l = -500)",
     "scenario_type": "edge", "sort_order": 3,
     "inputs": {"6a": 1000, "6l": -500},
     "expected_outputs": {"7": 500, "8": 500, "1040_line_20": 500},
     "notes": "R-S3-08: the 6l addend is signed — clamping it at 0 fails this scenario."},
    {"scenario_name": "S3-DG1 — 6z amount without type fires D_SCH3_001",
     "scenario_type": "failure", "sort_order": 4,
     "inputs": {"6z": 100},
     "expected_outputs": {"D_SCH3_001_fires": True, "7": 100}},
]

SCH3_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-S3-01", "IRS_2025_SCH3_FORM", "primary", "Line 7 verbatim: add lines 6a through 6z"),
    ("R-S3-02", "IRS_2025_SCH3_FORM", "primary", "Line 8 verbatim: add 1-4, 5a, 5b, and 7 -> 1040 line 20"),
    ("R-S3-02", "IRS_2025_1040_FORM", "primary", "1040 line 20 names Schedule 3 line 8"),
    ("R-S3-03", "IRS_2025_SCH3_FORM", "primary", "Line 14 verbatim: add lines 13a through 13z"),
    ("R-S3-04", "IRS_2025_SCH3_FORM", "primary", "Line 15 verbatim: add 9-12 and 14 -> 1040 line 31"),
    ("R-S3-04", "IRS_2025_1040_FORM", "primary", "1040 line 31 names Schedule 3 line 15"),
    ("R-S3-05", "IRS_2025_SCH3_FORM", "primary", "6z/13z 'list type and amount' (face verbatim)"),
    ("R-S3-06", "IRS_2025_SCH3_FORM", "primary", "Line 6e 'Reserved for future use'"),
    ("R-S3-07", "IRS_2025_SCH3_FORM", "primary", "'Attach Form/Schedule ...' line labels"),
    ("R-S3-08", "IRS_2025_SCH3_FORM", "primary", "Line 6l 'Amount on Form 8978, line 14. See instructions'"),
    ("R-S3-08", "IRS_2025_1040_INSTR", "secondary", "8978 negative-amount entry convention (instructions)"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS (13) — every total + every 1040 consumption point
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    # ── Schedule 1 ──
    {"assertion_id": "FA-1040-SCH1-01", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "S1 L9 sums all 23 line-8 addends (8a..8v, 8z)",
     "description": "Validates R-S1-01 with distinct values incl. the negative 8a/8d/8s. Bug it catches: a dropped 8-series addend or a sign flip.",
     "definition": {"kind": "sum_check", "form": "SCH_1", "output": "L9",
                    "sum_of": ["L8a", "L8b", "L8c", "L8d", "L8e", "L8f", "L8g", "L8h", "L8i", "L8j", "L8k",
                               "L8l", "L8m", "L8n", "L8o", "L8p", "L8q", "L8r", "L8s", "L8t", "L8u", "L8v", "L8z"],
                    "allow_negative_addends": True},
     "sort_order": 1},
    {"assertion_id": "FA-1040-SCH1-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "S1 L10 = combine(1, 2a, 3-7, 9) with NO floor; writes 1040 L8",
     "description": "Validates R-S1-02. Bug it catches: flooring a loss-year line 10 at 0, or 1040 line 8 not consuming the schedule total.",
     "definition": {"kind": "formula_check", "form": "SCH_1",
                    "formula": "L10 == L1 + L2a + L3 + L4 + L5 + L6 + L7 + L9", "allow_negative": True,
                    "must_write_to": {"form": "1040", "line": "8"}},
     "sort_order": 2},
    {"assertion_id": "FA-1040-SCH1-03", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "S1 L25 sums all 12 line-24 addends",
     "description": "Validates R-S1-03.",
     "definition": {"kind": "sum_check", "form": "SCH_1", "output": "L25",
                    "sum_of": ["L24a", "L24b", "L24c", "L24d", "L24e", "L24f", "L24g", "L24h", "L24i",
                               "L24j", "L24k", "L24z"]},
     "sort_order": 3},
    {"assertion_id": "FA-1040-SCH1-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "S1 L26 = sum(11-21, 23) + 25 (22 reserved); writes 1040 L10",
     "description": "Validates R-S1-04/09. Bug it catches: line 22 leaking a value into 26, or a dropped Part II addend.",
     "definition": {"kind": "formula_check", "form": "SCH_1",
                    "formula": "L26 == L11 + L12 + L13 + L14 + L15 + L16 + L17 + L18 + L19a + L20 + L21 + L23 + L25",
                    "excludes": ["L22"],
                    "must_write_to": {"form": "1040", "line": "10"}},
     "sort_order": 4},
    # ── Schedule 2 ──
    {"assertion_id": "FA-1040-SCH2-01", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "S2 L1z sums 1a-1f and 1y",
     "description": "Validates R-S2-01 incl. the new 2025 EPE lines 1d/1e/1f.",
     "definition": {"kind": "sum_check", "form": "SCH_2", "output": "L1z",
                    "sum_of": ["L1a", "L1b", "L1c", "L1d", "L1e", "L1f", "L1y"]},
     "sort_order": 5},
    {"assertion_id": "FA-1040-SCH2-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "S2 L3 = 1z + 2; writes 1040 L17",
     "description": "Validates R-S2-02.",
     "definition": {"kind": "formula_check", "form": "SCH_2", "formula": "L3 == L1z + L2",
                    "must_write_to": {"form": "1040", "line": "17"}},
     "sort_order": 6},
    {"assertion_id": "FA-1040-SCH2-03", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "S2 L7 = 5 + 6",
     "description": "Validates R-S2-03.",
     "definition": {"kind": "sum_check", "form": "SCH_2", "output": "L7", "sum_of": ["L5", "L6"]},
     "sort_order": 7},
    {"assertion_id": "FA-1040-SCH2-04", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "S2 L18 sums all 18 line-17 addends",
     "description": "Validates R-S2-04.",
     "definition": {"kind": "sum_check", "form": "SCH_2", "output": "L18",
                    "sum_of": ["L17a", "L17b", "L17c", "L17d", "L17e", "L17f", "L17g", "L17h", "L17i",
                               "L17j", "L17k", "L17l", "L17m", "L17n", "L17o", "L17p", "L17q", "L17z"]},
     "sort_order": 8},
    {"assertion_id": "FA-1040-SCH2-05", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "S2 L21 = 4 + (7-9, 11-16) + 18 + 19 — line 20 EXCLUDED; writes 1040 L23",
     "description": ("Validates R-S2-05/07/08 — THE load-bearing Schedule 2 assertion. Bugs it catches: "
                     "the 965 installment (L20) summed into L21; reserved L10 leaking; L5/L6 double-counted "
                     "alongside L7."),
     "definition": {"kind": "formula_check", "form": "SCH_2",
                    "formula": "L21 == L4 + L7 + L8 + L9 + L11 + L12 + L13 + L14 + L15 + L16 + L18 + L19",
                    "excludes": ["L20", "L10", "L5", "L6", "L17a"],
                    "must_write_to": {"form": "1040", "line": "23"}},
     "sort_order": 9},
    # ── Schedule 3 ──
    {"assertion_id": "FA-1040-SCH3-01", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "S3 L7 sums all 13 line-6 addends (6e reserved; 6l signed)",
     "description": "Validates R-S3-01/06/08. Bug it catches: clamping a negative 6l, or 6e leaking.",
     "definition": {"kind": "sum_check", "form": "SCH_3", "output": "L7",
                    "sum_of": ["L6a", "L6b", "L6c", "L6d", "L6f", "L6g", "L6h", "L6i", "L6j", "L6k",
                               "L6l", "L6m", "L6z"],
                    "excludes": ["L6e"], "allow_negative_addends": True},
     "sort_order": 10},
    {"assertion_id": "FA-1040-SCH3-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "S3 L8 = 1 + 2 + 3 + 4 + 5a + 5b + 7; writes 1040 L20",
     "description": "Validates R-S3-02.",
     "definition": {"kind": "formula_check", "form": "SCH_3",
                    "formula": "L8 == L1 + L2 + L3 + L4 + L5a + L5b + L7",
                    "must_write_to": {"form": "1040", "line": "20"}},
     "sort_order": 11},
    {"assertion_id": "FA-1040-SCH3-03", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "S3 L14 sums the five line-13 addends",
     "description": "Validates R-S3-03.",
     "definition": {"kind": "sum_check", "form": "SCH_3", "output": "L14",
                    "sum_of": ["L13a", "L13b", "L13c", "L13d", "L13z"]},
     "sort_order": 12},
    {"assertion_id": "FA-1040-SCH3-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "S3 L15 = 9 + 10 + 11 + 12 + 14; writes 1040 L31",
     "description": "Validates R-S3-04.",
     "definition": {"kind": "formula_check", "form": "SCH_3",
                    "formula": "L15 == L9 + L10 + L11 + L12 + L14",
                    "must_write_to": {"form": "1040", "line": "31"}},
     "sort_order": 13},
]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY FORM LINKS  (source_code, form_code, link_type)
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_SCH1_FORM", "SCH_1", "governs"),
    ("IRS_2025_1040_INSTR", "SCH_1", "governs"),
    ("IRS_2025_1040_FORM", "SCH_1", "informs"),
    ("IRC_62", "SCH_1", "informs"),
    ("IRS_2025_SCH2_FORM", "SCH_2", "governs"),
    ("IRS_2025_1040_INSTR", "SCH_2", "governs"),
    ("IRS_2025_1040_FORM", "SCH_2", "informs"),
    ("IRS_2025_SCH3_FORM", "SCH_3", "governs"),
    ("IRS_2025_1040_INSTR", "SCH_3", "governs"),
    ("IRS_2025_1040_FORM", "SCH_3", "informs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORMS ROSTER
# ═══════════════════════════════════════════════════════════════════════════

FORMS: list[dict] = [
    {"identity": SCH1_IDENTITY, "facts": SCH1_FACTS, "rules": SCH1_RULES, "lines": SCH1_LINES,
     "diagnostics": SCH1_DIAGNOSTICS, "scenarios": SCH1_SCENARIOS, "rule_links": SCH1_RULE_LINKS},
    {"identity": SCH2_IDENTITY, "facts": SCH2_FACTS, "rules": SCH2_RULES, "lines": SCH2_LINES,
     "diagnostics": SCH2_DIAGNOSTICS, "scenarios": SCH2_SCENARIOS, "rule_links": SCH2_RULE_LINKS},
    {"identity": SCH3_IDENTITY, "facts": SCH3_FACTS, "rules": SCH3_RULES, "lines": SCH3_LINES,
     "diagnostics": SCH3_DIAGNOSTICS, "scenarios": SCH3_SCENARIOS, "rule_links": SCH3_RULE_LINKS},
]


# ═══════════════════════════════════════════════════════════════════════════
# Command
# ═══════════════════════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = (
        "Load the Schedule 1 / 2 / 3 (Form 1040) specs into Rule Studio (creates "
        "SCH_1, SCH_2, SCH_3). Refuses to seed until Ken sets READY_TO_SEED=True."
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()

        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad SCH_1 / SCH_2 / SCH_3 specs (Topic 2)\n"))

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
                "REFUSING TO SEED SCH_1/SCH_2/SCH_3: not cleared to seed.\n"
                "\n"
                "Content is authored, but seeding is gated until Ken reviews the packet\n"
                "(line inventory vs the 2025 form faces, totals formulas incl. the\n"
                "Schedule 2 line-20 exclusion, sign conventions, diagnostics severities,\n"
                "the 13 scenarios) and flips the sentinel.\n"
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
    # Topics / sources (mirror load_1040_spine.py exactly)
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
        self.stdout.write("DATABASE TOTALS (after load_1040_sch123)")
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

        for fn in ("SCH_1", "SCH_2", "SCH_3"):
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




