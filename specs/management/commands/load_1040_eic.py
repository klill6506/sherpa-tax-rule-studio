"""Load the Earned Income Credit specs — Sprint Topic 7.

Creates FOUR TaxForms:
  - 1040_EIC (computational pseudo-form): the Step-5 earned-income worksheet,
    Worksheet A (non-SE) and the mainstream Worksheet B (SE) path, the EIC Table
    $50-bracket midpoint lookup, the lower-of-AGI/earned-income rule, the Pub 596
    Worksheet-1 investment-income limit, and the "Rules for Everyone" + childless
    eligibility gates -> Form 1040 line 27a. YEAR-KEYED §32 constants (both years).
  - SCHEDULE_EIC (real IRS face): the per-qualifying-child information page,
    model-driven from the Dependent rows where eic_qualifying_child is set.
  - 8867 (real IRS face): the paid-preparer due-diligence checklist (EIC + CTC/
    ACTC/ODC + HOH this sprint; AOTC section renders but flags RED until 8863
    exists). Data-map render — preparer-answer facts, no compute.
  - 8862 (real IRS face): Information To Claim Certain Credits After Disallowance.
    Data-map render gated on a preparer "previously disallowed" flag, no compute.

Session 2026-06-11: authored by transcription from primary sources fetched and
text-extracted the same day (pymupdf dumps in tts-tax-app server/.scratch/;
consolidated in tts-tax-app server/specs/_topic7_eic_source_brief.md):

  - RP 2024-40 §2.06 (rp-24-40.pdf) — TY2025 EIC §32 parameters.
  - RP 2025-32 §2.06 (rp-25-32.pdf) — TY2026 EIC §32 parameters.
  - Pub 596 (2025 Returns) (p596.pdf) — EIC rules for everyone, qualifying-child
    tests, Worksheet 1 (investment income).
  - i1040gi (2025) pp.42-48 — EIC line-27a instructions: Step 5 earned income,
    Worksheet A, Worksheet B, eligibility; EIC Table pp.49-60.
  - Schedule EIC (Form 1040) 2025 (f1040sei.pdf, Attachment Seq 43) — the
    qualifying-child information render face.
  - Form 8867 (Rev. Nov 2024) (f8867.pdf, Attachment Seq 70) + instructions.
  - Form 8862 (Rev. Dec 2025) (f8862.pdf, Attachment Seq 862) + instructions.

TOPIC SCOPE (SPRINT_SCOPE.md Topic 7 DoD — Ken-confirmed 2026-06-11):
  IN: eligibility rules as RS spec (qualifying-child tests as diagnostics +
      preparer assertion, investment-income limit verified per year, MFS §32(d)
      exception, SSN requirements); earned-income worksheet incl. SE earnings
      (from Schedule 1 flowed-or-direct values; Schedule C compute NOT required);
      credit lookup with lower-of-AGI/earned-income rule + the EIC Table $50-
      bracket midpoint convention; Schedule EIC render; Form 8862 data-map
      render; Form 8867 due-diligence checklist (EIC + CTC/ODC + HOH); flow
      assertions wired.
  OUT (RED "prepare manually", never silently computed; enumerated in the spec):
      Worksheet B clergy / church-employee (>= $108.28) / statutory-employee
      paths (need Schedule SE detail not built); Form 4797 gain in line-7a
      investment income (Pub 596 requires Worksheet 1 — verify-RED); §32(k)
      2-year (reckless) / 10-year (fraud) EIC ban (preparer-asserted -> RED
      block); "IRS figures the credit for you" path; Puerto Rico / U.S.
      territory main home; nonresident-alien spouse not treated as resident.

KEN'S CONFIRMED SCOPE DECISIONS (2026-06-11, the brief V1 SCOPE §; memory
topic7-eic-scope):
  1. Investment income: COMPUTE the modeled pieces (2a/2b interest, 3b ordinary
     dividends, 7a cap-gain distributions) as YELLOW + a GREEN preparer "other
     investment income" field for the unmodeled Worksheet-1 categories (Form 4797
     gain, royalties + personal-property-rental net, net passive income, 8814
     child amounts). RED diagnostic when total > limit; reminder diagnostic to
     add unmodeled items (no silent gap). ("recommended option")
  2. Nontaxable combat pay: preparer enters amount + a Y/N election; v1 includes
     it in earned income ONLY if elected, with a diagnostic suggesting they test
     both ways. NO auto-optimizer. ("recommended option")
  3. EIC qualifying child: REUSE the Dependent model + add an
     eic_qualifying_child override flag (mirrors ctc_override/odc_override) and
     full-time-student status. Schedule EIC renders from Dependent rows.
     ("recommended option")

YEAR-KEYED CONSTANTS (target-year policy: TY2026 product target, TY2025
verification bed). Unlike Topic 5 (statutory §86, non-indexed), the §32 EIC
parameters ARE inflation-indexed and DIFFER between years — both years'
parameter tables are transcribed VERBATIM here (EIC_PARAMS), each verified
independently against its Rev Proc. The statutory %s (§32(b)(1): credit
7.65/34/40/45; phaseout 7.65/15.98/21.06/21.06) are NOT indexed (EIC_RATES).
ENCODE THE PUBLISHED max-credit amounts (TY2026 0-QC = $664, not the 663.42 a
naive 8,680 x 7.65% gives). QSS uses the "other" (single/HOH/QSS) column for the
table, NOT the MFJ column (UNLIKE the MFJ-aligned QDCGT treatment).

SPINE / SIBLING SUPERSESSION (build leg, flagged for Ken):
  - 1040 line 27a becomes a COMPUTED feeder (YELLOW) from the EIC worksheet;
    the preparer override remains the escape hatch.
  - Schedule 2 / 3 untouched (EIC is a refundable credit on the page-2 payments
    block, not an "other tax" or a nonrefundable credit).
  - The earned-income Worksheet B SE path reads Schedule 1 line 3 (net SE
    profit, already direct-entry) and line 15 (1/2 SE-tax deduction, computed in
    Topic 2) — so it runs AFTER the Schedule 1 aggregation. The investment-income
    worksheet reads 1040 lines 2a/2b/3b/7a — so it runs AFTER Topic 3.

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
# Flip to True ONLY after the in-session review walk (the source citations, the
# §32 parameter tables BOTH years verified independently, the EIC Table midpoint
# convention, the v1 in/out scope enumeration, the Worksheet-B SE sourcing, and
# the qualifying-child / eligibility gate set). The math gate
# (check_eic_integrity.py) must be green before the flip.
# ═══════════════════════════════════════════════════════════════════════════

READY_TO_SEED = False


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1040"]


# ═══════════════════════════════════════════════════════════════════════════
# §32 EIC PARAMETER TABLES — verified VERBATIM from the Rev Procs
# (tts-tax-app memory topic7-eic-parameters; brief §"EIC §32 PARAMETERS").
# Columns indexed by number of qualifying children: "0" / "1" / "2" / "3+".
# Both years transcribed independently per the target-year policy.
# ═══════════════════════════════════════════════════════════════════════════

EIC_PARAMS: dict[int, dict] = {
    2025: {  # RP 2024-40 §2.06
        "earned_income_amount": {"0": 8490, "1": 12730, "2": 17880, "3+": 17880},
        "max_credit":           {"0": 649,  "1": 4328,  "2": 7152,  "3+": 8046},
        "threshold_mfj":        {"0": 17730, "1": 30470, "2": 30470, "3+": 30470},
        "completed_mfj":        {"0": 26214, "1": 57554, "2": 64430, "3+": 68675},
        "threshold_other":      {"0": 10620, "1": 23350, "2": 23350, "3+": 23350},
        "completed_other":      {"0": 19104, "1": 50434, "2": 57310, "3+": 61555},
        "investment_income_limit": 11950,
    },
    2026: {  # RP 2025-32 §2.06
        "earned_income_amount": {"0": 8680, "1": 13020, "2": 18290, "3+": 18290},
        "max_credit":           {"0": 664,  "1": 4427,  "2": 7316,  "3+": 8231},
        "threshold_mfj":        {"0": 18140, "1": 31160, "2": 31160, "3+": 31160},
        "completed_mfj":        {"0": 26820, "1": 58863, "2": 65899, "3+": 70244},
        "threshold_other":      {"0": 10860, "1": 23890, "2": 23890, "3+": 23890},
        "completed_other":      {"0": 19540, "1": 51593, "2": 58629, "3+": 62974},
        "investment_income_limit": 12200,
    },
}

# Statutory §32(b)(1) percentages — same both years, NOT indexed.
EIC_RATES: dict[str, dict] = {
    "credit_rate":   {"0": 0.0765, "1": 0.34, "2": 0.40, "3+": 0.45},
    "phaseout_rate": {"0": 0.0765, "1": 0.1598, "2": 0.2106, "3+": 0.2106},
}

# Childless EIC age band (§32(c)(1)(A)(ii)) — at least 25, under 65 at year-end.
# Statutory, not indexed (OBBBA did not change it). One spouse suffices for MFJ.
EIC_CHILDLESS_AGE_MIN = 25
EIC_CHILDLESS_AGE_MAX_EXCLUSIVE = 65


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY TOPICS
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("earned_income_credit", "Earned Income Credit (§32) — eligibility, earned-income worksheets, EIC Table, line 27a"),
    ("eic_qualifying_child", "EIC qualifying-child tests (Schedule EIC) + tie-breaker"),
    ("preparer_due_diligence", "Paid-preparer due diligence (Form 8867) + after-disallowance (Form 8862)"),
]

# Existing sources to REUSE (looked up, not modified).
EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "RP_2024_40",            # §2.06 TY2025 EIC parameters (§2.03 already used by intdiv)
    "RP_2025_32",            # §2.06 TY2026 EIC parameters (§4.03 already used by intdiv)
    "IRS_2025_1040_FORM",    # line 27a on the 2025 face
    "IRS_2025_1040_INSTR",   # i1040gi: line-27a instructions, Worksheets A/B, EIC Table
]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY SOURCES (with embedded excerpts) — CREATE
# Transcribed 2026-06-11 from the fetched PDFs (tts-tax-app server/.scratch/),
# requires_human_review=False (verbatim, verifiable against the on-disk copies).
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_PUB596",
        "source_type": "official_publication",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "Publication 596 — Earned Income Credit (EIC) (For use in preparing 2025 Returns)",
        "citation": "IRS Pub. 596 (2025); Cat. No. 15173A",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/p596.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": False,
        "trust_score": 9.00,
        "requires_human_review": False,
        "notes": (
            "Rules for Everyone, qualifying-child tests, childless rules, and "
            "Worksheet 1 (investment income) transcribed 2026-06-11 "
            "(server/.scratch/p596_full.txt)."
        ),
        "topics": ["earned_income_credit", "eic_qualifying_child"],
        "excerpts": [
            {
                "excerpt_label": "Rules for Everyone (the seven common rules — summary, verbatim headings)",
                "location_reference": "Pub 596 (2025), Chapter 1 'Rules for Everyone'",
                "excerpt_text": (
                    "Rule 1. Your AGI must be less than [the table limit for your status/"
                    "number of children]. Rule 2. You must have a valid social security "
                    "number (SSN) by the due date of your return (including extensions). "
                    "Rule 3. Your filing status can't be married filing separately unless "
                    "you meet the special rule. Rule 4. You must be a U.S. citizen or "
                    "resident alien all year. Rule 5. You can't file Form 2555. Rule 6. "
                    "Your investment income must be $11,950 or less. Rule 7. You must have "
                    "earned income."
                ),
                "summary_text": (
                    "Seven 'Rules for Everyone' -> RED-gate/diagnostic conditions. Rule 6 "
                    "investment-income limit is the year-keyed §32(i) amount ($11,950 "
                    "TY2025 / $12,200 TY2026)."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "MFS special rule (Rule 3, §32(d) — verbatim)",
                "location_reference": "Pub 596 (2025), Rule 3; i1040gi p.44",
                "excerpt_text": (
                    "If you are married filing separately, you can claim the EIC if you "
                    "had a qualifying child who lived with you for more than half of 2025 "
                    "and either: you lived apart from your spouse for the last 6 months of "
                    "2025, OR you are legally separated according to your state law under a "
                    "written separation agreement or a decree of separate maintenance and "
                    "didn't live in the same household as your spouse at the end of 2025."
                ),
                "summary_text": (
                    "MFS allowed only with a qualifying child + lived-apart-last-6-months "
                    "OR legally-separated-not-same-household. Preparer asserts -> diagnostic."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Childless EIC extra rules (age 25-64, not a dependent / QC of another — verbatim)",
                "location_reference": "Pub 596 (2025), Chapter 3 'Rules If You Don't Have a Qualifying Child'",
                "excerpt_text": (
                    "Rule 11. You must be at least age 25 but under age 65 at the end of "
                    "2025. If you are married filing jointly, either you or your spouse must "
                    "be at least 25 but under 65 at the end of the year. Rule 12. You can't "
                    "be the dependent of another person. Rule 13. You can't be a qualifying "
                    "child of another person. Rule 14. You must have lived in the United "
                    "States more than half of the year."
                ),
                "summary_text": (
                    "Childless: age >= 25 and < 65 (one spouse suffices for MFJ); not a "
                    "dependent; not a QC of another; main home in US > 1/2 year."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Worksheet 1 — Investment Income (Rule 6, verbatim line list)",
                "location_reference": "Pub 596 (2025), Worksheet 1 'Investment Income If You Are Filing Form 1040'",
                "excerpt_text": (
                    "1. Enter the amount from Form 1040, line 2b (taxable interest). 2. "
                    "Enter the amount from Form 1040, line 2a (tax-exempt interest) plus any "
                    "amount on Form 8814, line 1b. 3. Enter the amount from Form 1040, line "
                    "3b (ordinary dividends). 4. Enter the amount from Schedule 1, line 8z "
                    "that is from Form 8814 (child interest and dividends). 5. Enter the "
                    "amount from Form 1040, line 7 (capital gain). If the amount on that "
                    "line is a loss, enter -0-. 6. Enter the gain, if any, from Form 4797, "
                    "line 7. (If line 7 is a loss, enter -0-. But if you completed lines 8 "
                    "and 9 of Form 4797, enter the amount from line 9 instead.) 7. Subtract "
                    "line 6 from line 5. If zero or less, enter -0-. 8-10. Royalties and "
                    "rental of personal property less related expenses (>= 0). 11. Net "
                    "income from passive activities. Add lines 1, 2, 3, 4, 7, and the result "
                    "of lines 8-11. This is your investment income."
                ),
                "summary_text": (
                    "Investment income = taxable + tax-exempt interest + ordinary "
                    "dividends + 8814 child amounts + capital-gain net (line 5 - 4797 line "
                    "6, >= 0) + royalties/personal-property-rental net + passive income. "
                    "v1 models items 1/2a/3/5(cap-gain-distributions); preparer GREEN "
                    "'other' covers 4/6/8-11; 4797 present -> verify-RED."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_SCHEDEIC_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Schedule EIC (Form 1040) — Earned Income Credit (Qualifying Child Information)",
        "citation": "Schedule EIC (Form 1040) 2025; f1040sei.pdf; Attachment Sequence No. 43",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f1040sei.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": (
            "Qualifying-child information page transcribed 2026-06-11 "
            "(server/.scratch/sei_text.txt). Real face rendered by us; model-driven "
            "from Dependent rows where eic_qualifying_child is set (the Schedule-B "
            "payer-listing precedent). Up to 3 children listed even if more."
        ),
        "topics": ["eic_qualifying_child"],
        "excerpts": [
            {
                "excerpt_label": "Qualifying-child lines 1-6 (verbatim)",
                "location_reference": "Schedule EIC (2025), Child 1/2/3 columns, lines 1-6",
                "excerpt_text": (
                    "1 Child's name (first and last). 2 Child's SSN. The child must have an "
                    "SSN as defined in the instructions ... unless the child was born and "
                    "died in 2025. 3 Child's year of birth. 4a Was the child under age 24 "
                    "at the end of 2025, a student, and younger than you (or your spouse, if "
                    "filing jointly)? 4b Was the child permanently and totally disabled "
                    "during any part of 2025? 5 Child's relationship to you. 6 Number of "
                    "months the child lived with you in the United States during 2025. Do "
                    "not enter more than 12 months. If the child lived with you for more "
                    "than half of 2025 but less than 7 months, enter '7'. If the child was "
                    "born or died in 2025 ... enter '12'."
                ),
                "summary_text": (
                    "Per child: name, SSN, year of birth, 4a (under 24 + student + younger) "
                    "Y/N, 4b (disabled) Y/N, relationship, months in the US (>half but <7 -> "
                    "7; born/died -> 12; max 12). If 4a and 4b both No -> not a QC."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_8867_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "Form 8867 (Rev. November 2024) — Paid Preparer's Due Diligence Checklist",
        "citation": "Form 8867 (Rev. Nov 2024); f8867.pdf; Attachment Sequence No. 70",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f8867.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": (
            "Checklist questions transcribed 2026-06-11 (server/.scratch/f8867_text.txt). "
            "Data-map render — preparer-answer facts, NO compute. v1 covers EIC + "
            "CTC/ACTC/ODC + HOH; the AOTC (Part IV) section renders but flags RED "
            "until Form 8863 exists."
        ),
        "topics": ["preparer_due_diligence"],
        "excerpts": [
            {
                "excerpt_label": "Header credit checkboxes + Part I general due diligence (Q1-8, verbatim)",
                "location_reference": "Form 8867 (Rev. Nov 2024), header + Part I",
                "excerpt_text": (
                    "Check here if any applicable credits are claimed on the return: "
                    "Earned Income Credit (EIC); Child Tax Credit/Additional Child Tax "
                    "Credit/Credit for Other Dependents (CTC/ACTC/ODC); American "
                    "Opportunity Tax Credit (AOTC); Head of Household (HOH). Part I — Due "
                    "Diligence Requirements. 1 Did you complete the return based on "
                    "information provided by the taxpayer or reasonably obtained? 2 Did you "
                    "complete the applicable worksheet(s) or your own equivalent? 3 Did you "
                    "satisfy the knowledge requirement? 4 Did any information seem "
                    "incorrect, incomplete, or inconsistent? (4a make inquiries / 4b "
                    "document) 5 Did you satisfy the record retention requirement? 6 Did "
                    "you ask the taxpayer questions to substantiate eligibility/amounts? 7 "
                    "Did you ask whether the credit(s) were disallowed in a prior year? 8 "
                    "If credits were disallowed, did you complete the required "
                    "recertification (Form 8862)?"
                ),
                "summary_text": (
                    "Header: which of EIC / CTC-ACTC-ODC / AOTC / HOH are claimed "
                    "(drive from computed credits + filing status). Part I Q1-8 = general "
                    "due-diligence Y/N (4a/4b inquiry+documentation; 7/8 prior-year "
                    "disallowance + 8862)."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Parts II-V credit-specific (Q9-13 + HOH, verbatim)",
                "location_reference": "Form 8867 (Rev. Nov 2024), Parts II-V",
                "excerpt_text": (
                    "Part II — Due Diligence Questions for Returns Claiming EIC (9a/9b/9c: "
                    "residency, relationship, and income inquiries for a qualifying child; "
                    "if no qualifying child, the taxpayer-eligibility questions). Part III "
                    "— Due Diligence Questions for Returns Claiming CTC/ACTC/ODC (10-12). "
                    "Part IV — Due Diligence Questions for Returns Claiming AOTC (13). Part "
                    "V — Eligibility Certification: you will comply with all due-diligence "
                    "requirements for each credit; Head of Household filing status "
                    "determination questions."
                ),
                "summary_text": (
                    "Part II EIC (Q9), Part III CTC/ACTC/ODC (Q10-12), Part IV AOTC (Q13 — "
                    "RED until 8863), Part V HOH determination + certification. All "
                    "preparer-answered inputs."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_8862_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "Form 8862 (Rev. December 2025) — Information To Claim Certain Credits After Disallowance",
        "citation": "Form 8862 (Rev. Dec 2025); f8862.pdf; Attachment Sequence No. 862",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f8862.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": (
            "Parts I-V transcribed 2026-06-11 (server/.scratch/f8862_text.txt). Data-map "
            "render gated on a preparer 'EIC/credit previously disallowed -> must file "
            "8862' flag. NO compute."
        ),
        "topics": ["preparer_due_diligence"],
        "excerpts": [
            {
                "excerpt_label": "Parts I-V structure (verbatim headings)",
                "location_reference": "Form 8862 (Rev. Dec 2025), Parts I-V",
                "excerpt_text": (
                    "Part I — All Filers (the tax year for which the credit was previously "
                    "reduced or disallowed; whether it was due to a math/clerical error). "
                    "Part II — Earned Income Credit (with a qualifying child / without a "
                    "qualifying child residency and relationship questions). Part III — "
                    "Child Tax Credit / Refundable Child Tax Credit / Additional Child Tax "
                    "Credit / Credit for Other Dependents. Part IV — American Opportunity "
                    "Tax Credit. Part V — Qualifying Child of More Than One Person."
                ),
                "summary_text": (
                    "After-disallowance form: Part I all filers, Part II EIC, Part III "
                    "CTC/RCTC/ACTC/ODC, Part IV AOTC, Part V QC of more than one person. "
                    "Pure data-map."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
]

# Excerpts to add to the EXISTING sources (the two Rev Procs + the 1040
# instructions). The §2.06 EIC sections are distinct from the §2.03/§4.03
# QDCGT sections the intdiv loader already added.
NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = [
    (
        "RP_2024_40",
        {
            "excerpt_label": "§2.06 Earned Income Credit (TY2025, verbatim parameters)",
            "location_reference": "Rev. Proc. 2024-40, §2.06 'Earned Income Credit'",
            "excerpt_text": (
                "For taxable years beginning in 2025, the earned income tax credit "
                "amounts are: No qualifying children — earned income amount $8,490, "
                "maximum credit $649, threshold phaseout (other) $10,620, completed "
                "phaseout (other) $19,104, threshold phaseout (MFJ) $17,730, completed "
                "phaseout (MFJ) $26,214. One qualifying child — $12,730 / $4,328 / "
                "$23,350 / $50,434 / $30,470 / $57,554. Two — $17,880 / $7,152 / "
                "$23,350 / $57,310 / $30,470 / $64,430. Three or more — $17,880 / "
                "$8,046 / $23,350 / $61,555 / $30,470 / $68,675. The §32(i) disqualified "
                "investment income limit is $11,950."
            ),
            "summary_text": (
                "TY2025 §32 EIC parameters (0/1/2/3+ children). Investment income limit "
                "$11,950. Statutory rates (7.65/34/40/45 credit; 7.65/15.98/21.06/21.06 "
                "phaseout) are NOT in the rev proc — they are statutory §32(b)(1)."
            ),
            "is_key_excerpt": True,
        },
    ),
    (
        "RP_2025_32",
        {
            "excerpt_label": "§2.06 Earned Income Credit (TY2026, verbatim parameters)",
            "location_reference": "Rev. Proc. 2025-32, §2.06 'Earned Income Credit'",
            "excerpt_text": (
                "For taxable years beginning in 2026, the earned income tax credit "
                "amounts are: No qualifying children — earned income amount $8,680, "
                "maximum credit $664, threshold phaseout (other) $10,860, completed "
                "phaseout (other) $19,540, threshold phaseout (MFJ) $18,140, completed "
                "phaseout (MFJ) $26,820. One qualifying child — $13,020 / $4,427 / "
                "$23,890 / $51,593 / $31,160 / $58,863. Two — $18,290 / $7,316 / "
                "$23,890 / $58,629 / $31,160 / $65,899. Three or more — $18,290 / "
                "$8,231 / $23,890 / $62,974 / $31,160 / $70,244. The §32(i) disqualified "
                "investment income limit is $12,200."
            ),
            "summary_text": (
                "TY2026 §32 EIC parameters (target-year, verified independently of 2025). "
                "Investment income limit $12,200. Published 0-QC max credit $664 (NOT the "
                "663.42 a naive 8,680 x 7.65% gives — encode the published amount)."
            ),
            "is_key_excerpt": True,
        },
    ),
    (
        "IRS_2025_1040_INSTR",
        {
            "excerpt_label": "EIC Step 5 earned income + Worksheet A (non-SE), verbatim",
            "location_reference": "i1040gi (2025), Line 27a EIC instructions Step 5 + Worksheet A (pp.46)",
            "excerpt_text": (
                "Step 5 — earned income: 1. Enter the amount from Form 1040, line 1z. "
                "2. Enter any Medicaid waiver payments you exclude (Schedule 1, line 8s) "
                "unless you choose to include them in earned income. 3. Subtract line 2 "
                "from line 1. 4. Enter any nontaxable combat pay you elect to include in "
                "earned income (also entered on Form 1040, line 1i). 5. Add lines 3 and 4. "
                "This is your earned income. Worksheet A: 1. Enter your earned income from "
                "Step 5. 2. Look up the amount on line 1 in the EIC Table to find the "
                "credit. If line 2 is zero, you can't take the credit. 3. Enter the amount "
                "from Form 1040, line 11 (AGI). 4. Are the amounts on lines 3 and 1 the "
                "same? Yes -> skip line 5, enter the line-2 amount on line 6. No -> go to "
                "line 5. 5. If line 3 is less than the threshold ($10,620 [0 children] / "
                "$23,350 [with children]; MFJ $17,730 / $30,470), skip line 5, enter line "
                "2 on line 6; otherwise look up the line-3 amount in the EIC Table. 6. "
                "Enter the smaller of line 2 or line 5. This is your earned income credit; "
                "enter on Form 1040, line 27a."
            ),
            "summary_text": (
                "Step 5 earned income = 1z - excluded Medicaid waiver (unless elected) + "
                "elected nontaxable combat pay. Worksheet A: table at earned income; the "
                "lower-of-AGI rule only binds when AGI > earned income AND AGI >= the "
                "threshold-phaseout for the status/# children."
            ),
            "is_key_excerpt": True,
        },
    ),
    (
        "IRS_2025_1040_INSTR",
        {
            "excerpt_label": "EIC Worksheet B (SE) + EIC Table $50-bracket convention, verbatim",
            "location_reference": "i1040gi (2025), Worksheet B (pp.47-48) + EIC Table (pp.49-60)",
            "excerpt_text": (
                "Worksheet B (self-employed / clergy / church employee / statutory "
                "employee): Part 1 (Schedule SE filers) 1a = Sch SE, Part I, line 3; 1b = "
                "Sch SE, Part I, line 4b and line 5a; 1c = 1a + 1b; 1d = Sch SE, Part I, "
                "line 13 (one-half SE tax); 1e = 1c - 1d. Part 2 (not required to file Sch "
                "SE) net farm + net nonfarm. Part 3 statutory employees: Schedule C, line "
                "1. Part 4: 4a = earned income from Step 5; 4b = 1e + 2c + 3 + 4a (total "
                "earned income). If 4b is zero or less, you can't take the credit. Part 5: "
                "6 = 4b; 7 = EIC Table at line 6; 8 = Form 1040, line 11 (AGI). Part 6: the "
                "lower-of-AGI rule (same as Worksheet A); line 11 = your earned income "
                "credit -> Form 1040, line 27a. EIC Table: read the credit for the line of "
                "the table that includes the amount you are looking up (each row covers a "
                "$50 bracket: 'At least X but less than X+50')."
            ),
            "summary_text": (
                "Worksheet B SE earned income = (net SE earnings) - (1/2 SE tax) + wages "
                "(Step 5). v1 mainstream: Sch 1 line 3 net SE - Sch 1 line 15 (1/2 SE tax) "
                "+ Step-5 wages; clergy/church/statutory RED-defer. EIC Table = the §32 "
                "credit function at each $50 bracket midpoint, ROUND_HALF_UP (the Tax "
                "Table convention)."
            ),
            "is_key_excerpt": True,
        },
    ),
]


# ═══════════════════════════════════════════════════════════════════════════
# 1040_EIC — earned-income worksheets + EIC Table + eligibility (pseudo-form)
# ═══════════════════════════════════════════════════════════════════════════

EIC_IDENTITY = {
    "form_number": "1040_EIC",
    "form_title": "Earned Income Credit — earned-income worksheets + EIC Table lookup (TY2025)",
    "notes": (
        "Sprint Topic 7. PSEUDO-FORM: not an IRS face — it carries (a) the Step-5 "
        "earned-income worksheet, Worksheet A (non-SE) and the mainstream Worksheet "
        "B (SE) path, (b) the EIC Table $50-bracket midpoint lookup (the Tax-Table "
        "convention) with the lower-of-AGI/earned-income rule, (c) the Pub 596 "
        "Worksheet-1 investment-income limit, and (d) the 'Rules for Everyone' + "
        "childless eligibility gates -> Form 1040 line 27a. YEAR-KEYED §32 constants "
        "(both years' parameter tables, each verified independently). Qualifying "
        "children come from the Dependent rows (eic_qualifying_child); Schedule EIC "
        "renders them. Renders as a STATEMENT page (worksheet), never a faked IRS face."
    ),
}

EIC_FACTS: list[dict] = [
    # ── Earned income (Step 5) — return-level preparer entries ──
    {"fact_key": "elect_include_medicaid_waiver", "label": "Elect to INCLUDE Medicaid waiver payments (Sch 1 8s) in earned income",
     "data_type": "boolean", "sort_order": 1,
     "notes": ("RETURN LEVEL (per-spouse election allowed; v1 return-level). Default False: excluded waiver "
               "payments (Sch 1 line 8s) are SUBTRACTED from line 1z in Step 5. True -> include (subtract 0). "
               "Notice 2014-7.")},
    {"fact_key": "nontaxable_combat_pay", "label": "Nontaxable combat pay (W-2 box 12 code Q; also 1040 line 1i)",
     "data_type": "decimal", "default_value": "0", "sort_order": 2,
     "notes": "RETURN LEVEL. Preparer entry. Added to earned income ONLY if elect_combat_pay (JUDGMENT 2)."},
    {"fact_key": "elect_combat_pay", "label": "Elect to include nontaxable combat pay in earned income",
     "data_type": "boolean", "sort_order": 3,
     "notes": ("RETURN LEVEL. JUDGMENT 2 (Ken-confirmed): preparer election honored as entered. No auto-optimizer "
               "in v1; D_EIC_004 suggests testing both ways.")},
    # ── Worksheet routing + SE earned income (Worksheet B) ──
    {"fact_key": "eic_self_employed", "label": "Self-employed at any time in 2025 (routes Worksheet A vs B)",
     "data_type": "boolean", "sort_order": 10,
     "notes": ("RETURN LEVEL. Step-5 Q2: self-employed / clergy / church employee / statutory employee filing "
               "Schedule C? No -> Worksheet A; Yes -> Worksheet B.")},
    {"fact_key": "eic_clergy_church_statutory", "label": "Clergy / church-employee (>= $108.28) / statutory-employee Sch C path",
     "data_type": "boolean", "sort_order": 11,
     "notes": ("RETURN LEVEL. v1 RED-DEFER (D_EIC_015): these Worksheet-B sub-paths need Schedule SE detail not "
               "built. The mainstream sole-proprietor SE path (Sch 1 L3 - Sch 1 L15) IS computed.")},
    {"fact_key": "eic_se_net_earnings", "label": "Worksheet B SE net earnings (Sch 1 line 3 net SE profit, or override)",
     "data_type": "decimal", "default_value": "0", "sort_order": 12,
     "notes": ("RETURN LEVEL. DoD: 'SE from Schedule 1 flowed-or-direct; Schedule C compute NOT required.' "
               "Default sources Schedule 1 line 3 (business income, already direct-entry); preparer override. "
               "CONFIRM exact sourcing at the walk.")},
    {"fact_key": "eic_se_half_deduction", "label": "Worksheet B 1/2 SE-tax deduction (Sch 1 line 15, or override)",
     "data_type": "decimal", "default_value": "0", "sort_order": 13,
     "notes": "RETURN LEVEL. Sources Schedule 1 line 15 (computed in Topic 2). Subtracted from SE earnings (WS B 1e)."},
    # ── Investment income (Pub 596 Worksheet 1) ──
    {"fact_key": "other_investment_income", "label": "Other investment income (unmodeled Worksheet-1 categories)",
     "data_type": "decimal", "default_value": "0", "sort_order": 20,
     "notes": ("RETURN LEVEL. JUDGMENT 1 (Ken-confirmed): GREEN preparer bucket for the Worksheet-1 lines we do "
               "NOT model — Form 4797 gain (item 6), royalties + personal-property rental net (8-10), passive "
               "income (11), Form 8814 child amounts (items 2/4). Added to the modeled 2a/2b/3b/7a pieces. "
               "D_EIC_002 reminds the preparer to populate it.")},
    {"fact_key": "eic_form_4797_present", "label": "Form 4797 present (Pub 596 requires Worksheet 1 — verify)",
     "data_type": "boolean", "sort_order": 21,
     "notes": "RETURN LEVEL. Any 4797 -> D_EIC_003 verify-RED (Pub 596: you MUST use Worksheet 1 if 4797 present)."},
    # ── Eligibility assertions ("Rules for Everyone" + childless) ──
    {"fact_key": "eic_valid_ssn_taxpayer", "label": "Taxpayer has a valid SSN for EIC (by the due date incl. extensions)",
     "data_type": "boolean", "sort_order": 30,
     "notes": ("RETURN LEVEL. Rule 2. 'Not Valid for Employment' SSN (federally-funded benefit only) is NOT valid "
               "for EIC. Default False/blank -> D_EIC_016. Preparer asserts.")},
    {"fact_key": "eic_valid_ssn_spouse", "label": "Spouse has a valid SSN for EIC (MFJ)", "data_type": "boolean",
     "sort_order": 31, "notes": "RETURN LEVEL. Rule 2, MFJ only. Both spouses need a valid SSN."},
    {"fact_key": "eic_us_citizen_resident_all_year", "label": "U.S. citizen or resident alien ALL year",
     "data_type": "boolean", "sort_order": 32,
     "notes": ("RETURN LEVEL. Rule 4. A nonresident-alien spouse not treated as a resident (no §6013(g)/(h) "
               "election) -> D_EIC_013 ineligible.")},
    {"fact_key": "eic_main_home_us_half_year", "label": "Main home in the United States > 1/2 of 2025",
     "data_type": "boolean", "sort_order": 33,
     "notes": ("RETURN LEVEL. Rule 14 (childless) / qualifying-child residency. US = 50 states + DC, NOT PR/"
               "territories; military on extended active duty outside the US counts as in-US.")},
    {"fact_key": "eic_puerto_rico_territory_home", "label": "Main home in Puerto Rico or a U.S. territory",
     "data_type": "boolean", "sort_order": 34,
     "notes": "RETURN LEVEL. True -> D_EIC_012 ineligible (PR/territories are not the 'United States' for EIC)."},
    {"fact_key": "mfs_eic_special_rule", "label": "MFS meets the §32(d) special rule (QC + lived apart / legally separated)",
     "data_type": "boolean", "sort_order": 35,
     "notes": ("RETURN LEVEL. Rule 3 / §32(d). MFS allowed ONLY if a qualifying child lived with you > 1/2 year "
               "AND (lived apart from spouse the last 6 months OR legally separated, not same household at "
               "year-end). MFS without this -> D_EIC_005 no EIC. Preparer asserts the conditions.")},
    {"fact_key": "eic_qualifying_child_of_another", "label": "Taxpayer is a qualifying child of another person",
     "data_type": "boolean", "sort_order": 36,
     "notes": "RETURN LEVEL. Childless Rule 13. True -> D_EIC_007 no EIC."},
    {"fact_key": "eic_claimed_as_dependent", "label": "Taxpayer can be claimed as a dependent by another person",
     "data_type": "boolean", "sort_order": 37,
     "notes": "RETURN LEVEL. Childless Rule 12. True -> D_EIC_007 no EIC."},
    {"fact_key": "eic_ban_2yr", "label": "§32(k) 2-year ban in effect (reckless/intentional disregard)",
     "data_type": "boolean", "sort_order": 38,
     "notes": "RETURN LEVEL. §32(k)(1)(B)(ii). True -> D_EIC_009 RED block (can't claim)."},
    {"fact_key": "eic_ban_10yr", "label": "§32(k) 10-year ban in effect (fraud)", "data_type": "boolean",
     "sort_order": 39, "notes": "RETURN LEVEL. §32(k)(1)(B)(i). True -> D_EIC_009 RED block."},
    {"fact_key": "eic_disallowed_prior_year", "label": "EIC/credit reduced or disallowed in a prior year (must file 8862)",
     "data_type": "boolean", "sort_order": 40,
     "notes": "RETURN LEVEL. True (not due to math/clerical error) -> D_EIC_008 Form 8862 required."},
    # ── Childless age band (read from Taxpayer DOB at the build leg) ──
    {"fact_key": "eic_childless_age_qualifies", "label": "Childless EIC age test met (>= 25 and < 65 at year-end; one spouse for MFJ)",
     "data_type": "boolean", "sort_order": 41,
     "notes": ("RETURN LEVEL — DERIVED at the build leg from Taxpayer.date_of_birth (and spouse for MFJ). "
               "Childless Rule 11: at least 25, under 65 at the end of 2025. For MFJ, one spouse qualifying "
               "suffices. The spec carries it as a fact so the gate is explicit; compute derives it from DOB.")},
    # ── Year-keyed constant outputs (traceability; see EIC_PARAMS) ──
    {"fact_key": "eic_earned_income_amount", "label": "EIC earned-income amount (year + # qualifying children keyed)",
     "data_type": "decimal", "sort_order": 50,
     "notes": ("CONSTANT (year-keyed, EIC_PARAMS). TY2025: 8,490/12,730/17,880/17,880 (0/1/2/3+). "
               "TY2026: 8,680/13,020/18,290/18,290. The plateau start where credit = max_credit.")},
    {"fact_key": "eic_max_credit", "label": "EIC maximum credit (year + # qualifying children keyed)", "data_type": "decimal",
     "sort_order": 51,
     "notes": ("CONSTANT (year-keyed). TY2025: 649/4,328/7,152/8,046. TY2026: 664/4,427/7,316/8,231 "
               "(0-QC PUBLISHED 664, not 663.42). The plateau credit amount.")},
    {"fact_key": "eic_threshold_phaseout", "label": "EIC threshold phaseout (year + # QC + filing-status keyed)",
     "data_type": "decimal", "sort_order": 52,
     "notes": ("CONSTANT (year-keyed). Where the credit begins to phase out. 'Other' column also applies to MFS "
               "meeting §32(d); QSS uses 'other', NOT MFJ. TY2025 other 10,620/23,350/...; MFJ 17,730/30,470/...")},
    {"fact_key": "eic_completed_phaseout", "label": "EIC completed phaseout (year + # QC + filing-status keyed)",
     "data_type": "decimal", "sort_order": 53,
     "notes": ("CONSTANT (year-keyed) = the AGI limit (Rule 1) — credit is 0 at/above this. TY2025 other "
               "19,104/50,434/57,310/61,555; MFJ 26,214/57,554/64,430/68,675.")},
    {"fact_key": "eic_investment_income_limit", "label": "EIC investment income limit (§32(i), year-keyed)",
     "data_type": "decimal", "sort_order": 54,
     "notes": "CONSTANT (year-keyed): TY2025 11,950; TY2026 12,200. Total investment income > limit -> no EIC."},
    {"fact_key": "eic_credit_rate", "label": "EIC credit rate (statutory §32(b)(1), # QC keyed, NON-indexed)",
     "data_type": "decimal", "sort_order": 55, "notes": "CONSTANT: 7.65% / 34% / 40% / 45% (0/1/2/3+). Same both years."},
    {"fact_key": "eic_phaseout_rate", "label": "EIC phaseout rate (statutory §32(b)(1), # QC keyed, NON-indexed)",
     "data_type": "decimal", "sort_order": 56, "notes": "CONSTANT: 7.65% / 15.98% / 21.06% / 21.06%. Same both years."},
    # ── Worksheet output traceability ──
    {"fact_key": "eic_num_qualifying_children", "label": "Number of EIC qualifying children (0/1/2/3+ -> column)",
     "data_type": "integer", "sort_order": 60,
     "notes": ("DERIVED at the build leg = count of Dependent rows where eic_qualifying_child AND valid SSN. "
               "Capped at 3 for the table column (3+ shares the col). A QC without a valid SSN does NOT count "
               "toward the larger credit (drops to childless) but Schedule EIC still attaches.")},
    {"fact_key": "eic_earned_income_result", "label": "Earned income (Step 5 / Worksheet B Part 4) result", "data_type": "decimal",
     "sort_order": 61, "notes": "OUTPUT. Worksheet A line 1 / Worksheet B line 6. The lookup amount for the table."},
    {"fact_key": "eic_table_amount_earned", "label": "EIC Table credit at earned income", "data_type": "decimal",
     "sort_order": 62, "notes": "OUTPUT. Table lookup at earned income (WS A line 2 / WS B line 7). Zero -> no credit."},
    {"fact_key": "eic_table_amount_agi", "label": "EIC Table credit at AGI (lower-of rule)", "data_type": "decimal",
     "sort_order": 63, "notes": "OUTPUT. Table lookup at AGI (WS A line 5 / WS B line 10) when AGI > earned income and AGI >= threshold."},
    {"fact_key": "eic_investment_income_total", "label": "Total investment income (Pub 596 Worksheet 1)", "data_type": "decimal",
     "sort_order": 64, "notes": "OUTPUT. Sum of modeled pieces (2a/2b/3b/7a) + other_investment_income. > limit -> 0 credit."},
]

EIC_RULES: list[dict] = [
    # ── Step 5 earned income ──
    {"rule_id": "R-EIC-STEP5", "title": "Step 5 — preliminary earned income (all filers)",
     "rule_type": "calculation", "precedence": 1, "sort_order": 1,
     "formula": ("step5_1 = 1040 line 1z (wages); step5_2 = Sch 1 line 8s Medicaid waiver excluded "
                 "(0 if elect_include_medicaid_waiver); step5_3 = step5_1 - step5_2; "
                 "step5_4 = nontaxable_combat_pay if elect_combat_pay else 0; "
                 "earned_income = step5_3 + step5_4."),
     "inputs": ["elect_include_medicaid_waiver", "nontaxable_combat_pay", "elect_combat_pay"],
     "outputs": ["step5_1", "step5_2", "step5_3", "step5_4", "step5_5"],
     "description": ("ONCE PER RETURN. i1040gi Step 5 verbatim. Wages less excluded Medicaid waiver (unless "
                     "elected to include) plus elected nontaxable combat pay. Feeds Worksheet A line 1 / "
                     "Worksheet B line 4a.")},
    # ── Worksheet routing ──
    {"rule_id": "R-EIC-ROUTE", "title": "Worksheet A vs Worksheet B routing (Step-5 Q2)",
     "rule_type": "routing", "precedence": 0, "sort_order": 2,
     "formula": ("If NOT eic_self_employed -> Worksheet A (non-SE). If eic_self_employed -> Worksheet B. "
                 "If eic_clergy_church_statutory -> Worksheet B clergy/church/statutory sub-path = RED-DEFER "
                 "(D_EIC_015): not computed this sprint."),
     "inputs": ["eic_self_employed", "eic_clergy_church_statutory"], "outputs": [],
     "description": ("ONCE PER RETURN. i1040gi Step-5 Q2. The mainstream sole-proprietor SE path runs Worksheet "
                     "B Part 1/4; clergy/church-employee/statutory-employee RED-defer (need Sch SE detail).")},
    # ── Worksheet B SE earned income (mainstream sole-proprietor) ──
    {"rule_id": "R-EIC-WSB-SE", "title": "Worksheet B — SE earned income (mainstream sole-proprietor path)",
     "rule_type": "calculation", "precedence": 2, "sort_order": 3,
     "formula": ("wsb_1e = eic_se_net_earnings - eic_se_half_deduction (Sch 1 L3 net SE - Sch 1 L15 1/2 SE tax); "
                 "wsb_4a = earned_income (Step 5 wages); wsb_4b = wsb_1e + wsb_4a (mainstream: parts 2c/3 = 0). "
                 "If wsb_4b <= 0 -> no credit. wsb_6 = wsb_4b is the lookup amount."),
     "inputs": ["eic_se_net_earnings", "eic_se_half_deduction"], "outputs": ["wsb_1e", "wsb_4a", "wsb_4b", "wsb_6"],
     "description": ("ONCE PER RETURN (SE path only). i1040gi Worksheet B Parts 1/4. DoD simplification: SE net "
                     "earnings from Sch 1 line 3, 1/2-SE-tax from Sch 1 line 15. Part 2 (no-SE-required <$400) + "
                     "Part 3 (statutory employee) = 0 in v1 (RED-defer covers those). Replaces Step-5 wages as "
                     "the lookup amount.")},
    # ── EIC Table lookup (the $50-bracket midpoint convention) ──
    {"rule_id": "R-EIC-TABLE", "title": "EIC Table lookup — $50-bracket midpoint x §32 rate, ROUND_HALF_UP",
     "rule_type": "calculation", "precedence": 3, "sort_order": 4,
     "formula": ("eic_table(L, #QC, status, year): find L's $50 bracket [50*floor(L/50), +50); midpoint = "
                 "lo + 25; apply the piecewise §32 f(midpoint): "
                 "f = midpoint*credit_rate           if midpoint < earned_income_amount (rising); "
                 "f = max_credit                      if earned_income_amount <= midpoint < threshold_phaseout (plateau); "
                 "f = max_credit - (midpoint - threshold_phaseout)*phaseout_rate  if threshold <= midpoint < completed (phaseout); "
                 "f = 0                               if midpoint >= completed_phaseout. "
                 "Round f HALF_UP to whole dollars. (status: 'other' for single/HOH/QSS/MFS-with-§32(d); 'mfj' "
                 "for MFJ. #QC capped at 3.)"),
     "inputs": ["eic_num_qualifying_children", "eic_earned_income_amount", "eic_max_credit",
                "eic_threshold_phaseout", "eic_completed_phaseout", "eic_credit_rate", "eic_phaseout_rate"],
     "outputs": ["eic_table_amount_earned", "eic_table_amount_agi"],
     "description": ("QUALITY RULE 1. The published EIC Table is the §32 credit function evaluated at each $50 "
                     "bracket MIDPOINT, ROUND_HALF_UP — the SAME convention Ken blessed for the Tax Table "
                     "(Topic 1). Verified at the i1040gi example: bracket 2,450-2,500 -> midpoint 2,475 x 34% "
                     "(1 QC) = 841.5 -> 842. Year-keyed constants (EIC_PARAMS) carry the breakpoints. Standing "
                     "obligation: re-pin against the published TY2026 EIC Table when IRS releases the 2026 1040 "
                     "instructions (~Dec 2026), same as the Tax Table.")},
    # ── Lower-of-AGI/earned-income rule ──
    {"rule_id": "R-EIC-LOWEROF", "title": "Lower-of-AGI/earned-income rule (Worksheet A/B Parts 2/6)",
     "rule_type": "calculation", "precedence": 4, "sort_order": 5,
     "formula": ("L_earned = table(earned_income); L_agi: if AGI(1040 line 11) == earned_income -> credit = "
                 "L_earned. Else if AGI < threshold_phaseout(status, #QC) -> credit = L_earned. Else credit = "
                 "min(table(AGI), L_earned). The lower-of only BINDS when AGI > earned income AND AGI >= "
                 "threshold."),
     "inputs": ["eic_table_amount_earned", "eic_table_amount_agi", "eic_threshold_phaseout"], "outputs": ["agg_27a"],
     "description": ("ONCE PER RETURN. i1040gi Worksheet A lines 3-6 / Worksheet B lines 8-11. AGI is the page-2 "
                     "line-11 carry (Topic 1 synthesizes it at render). The taxpayer gets the SMALLER of the two "
                     "table lookups once AGI is in/past the phaseout — never the larger.")},
    # ── Investment income limit (Pub 596 Worksheet 1) ──
    {"rule_id": "R-EIC-INVINC", "title": "Investment income (Pub 596 Worksheet 1) + §32(i) limit gate",
     "rule_type": "calculation", "precedence": 3, "sort_order": 6,
     "formula": ("inv = 1040 2b + 1040 2a + 1040 3b + max(0, 1040 7a capital-gain net) + other_investment_income. "
                 "If inv > eic_investment_income_limit(year) -> credit = 0 (D_EIC_001 RED)."),
     "inputs": ["other_investment_income", "eic_investment_income_limit"], "outputs": ["eic_investment_income_total"],
     "description": ("ONCE PER RETURN. JUDGMENT 1. Models items 1/2a/3/5 (2b/2a/3b/7a — already in the app) + the "
                     "GREEN preparer 'other' bucket for 4/6/8-11. > limit -> no EIC (the table doesn't catch it; "
                     "this is a hard disqualifier). A Form-4797 indicator fires a verify-RED (D_EIC_003).")},
    # ── Eligibility gates (Rules for Everyone) ──
    {"rule_id": "R-EIC-ELIG", "title": "Eligibility gates — 'Rules for Everyone' (§32 disqualifiers)",
     "rule_type": "routing", "precedence": 0, "sort_order": 7,
     "formula": ("Credit = 0 (with the matching RED) if ANY: taxpayer/spouse(MFJ) lacks a valid SSN "
                 "(D_EIC_016); MFS without §32(d) (D_EIC_005); files Form 2555 (D_EIC_006); not a US citizen/"
                 "resident all year or NRA spouse (D_EIC_013); main home not in the US > 1/2 year, or PR/"
                 "territory (D_EIC_012); investment income over limit (D_EIC_001); §32(k) ban (D_EIC_009)."),
     "inputs": ["eic_valid_ssn_taxpayer", "eic_valid_ssn_spouse", "mfs_eic_special_rule", "eic_us_citizen_resident_all_year",
                "eic_main_home_us_half_year", "eic_puerto_rico_territory_home", "eic_ban_2yr", "eic_ban_10yr"], "outputs": [],
     "description": ("ONCE PER RETURN. Pub 596 'Rules for Everyone' (Rules 1-7) + the §32(k) ban. Each failed "
                     "gate zeroes the credit with a specific RED — never a silently-wrong number (quality rule "
                     "2). 'files_form_2555' is the existing Taxpayer fact.")},
    # ── Childless age gate ──
    {"rule_id": "R-EIC-CHILDLESS", "title": "Childless EIC extra rules (age 25-64, not dependent / QC of another)",
     "rule_type": "routing", "precedence": 0, "sort_order": 8,
     "formula": ("Applies only when eic_num_qualifying_children == 0: require eic_childless_age_qualifies "
                 "(>= 25, < 65 at year-end; one spouse for MFJ) AND not eic_claimed_as_dependent AND not "
                 "eic_qualifying_child_of_another. Any failure -> credit = 0 (D_EIC_007)."),
     "inputs": ["eic_num_qualifying_children", "eic_childless_age_qualifies", "eic_claimed_as_dependent",
                "eic_qualifying_child_of_another"], "outputs": [],
     "description": ("ONCE PER RETURN (childless only). Pub 596 Rules 11-13. Age band is STATUTORY (25-64), not "
                     "indexed. Build leg derives eic_childless_age_qualifies from Taxpayer.date_of_birth.")},
    # ── Qualifying-child tests (preparer-asserted + diagnostics) ──
    {"rule_id": "R-EIC-QC", "title": "Qualifying-child tests (relationship/age/residency/joint-return/SSN)",
     "rule_type": "validation", "precedence": 5, "sort_order": 9,
     "formula": ("Each Dependent flagged eic_qualifying_child must satisfy: relationship (son/daughter/"
                 "stepchild/foster/sibling/step-sibling or descendant); age (< 19, OR < 24 + full-time student, "
                 "OR any age if permanently disabled — AND younger than the taxpayer unless disabled); "
                 "residency (lived with you in the US > 1/2 year; months on Schedule EIC line 6); didn't file a "
                 "joint return (except refund-only); valid SSN to count toward the larger credit. A QC without a "
                 "valid SSN -> childless EIC (D_EIC_010); Schedule EIC still attaches."),
     "inputs": ["eic_num_qualifying_children"], "outputs": [],
     "description": ("ONCE PER QUALIFYING CHILD. Pub 596 Chapter 2 + Schedule EIC lines 3/4a/4b/5/6. "
                     "Preparer-asserted on the Dependent (eic_qualifying_child + is_full_time_student + DOB + "
                     "months + tin_type); the tests are DIAGNOSTICS (D_EIC_010/011/014), NOT an adjudication "
                     "engine (DoD: NO eligibility adjudication this sprint).")},
    # ── Final EIC -> 1040 line 27a ──
    {"rule_id": "R-EIC-27A", "title": "Earned Income Credit -> 1040 line 27a (computed feeder)",
     "rule_type": "calculation", "precedence": 6, "sort_order": 10,
     "formula": ("agg_27a = 0 if any eligibility gate fails (R-EIC-ELIG / R-EIC-CHILDLESS / R-EIC-INVINC); "
                 "else the lower-of result (R-EIC-LOWEROF). -> 1040 line 27a (override = escape hatch)."),
     "inputs": [], "outputs": ["1040.L27a"],
     "description": ("ONCE PER RETURN. The EIC lands on Form 1040 line 27a (refundable, page-2 payments block). "
                     "Computed feeder (YELLOW); preparer override remains. 27b (PYEI election) / 27c are "
                     "separate; v1 uses current-year earned income only.")},
]

EIC_LINES: list[dict] = [
    # Step 5 earned income
    {"line_number": "step5_1", "description": "Step 5 line 1: Form 1040 line 1z (wages)", "line_type": "calculated",
     "source_rules": ["R-EIC-STEP5"], "sort_order": 1},
    {"line_number": "step5_2", "description": "Step 5 line 2: excluded Medicaid waiver (Sch 1 8s) unless elected", "line_type": "calculated",
     "source_rules": ["R-EIC-STEP5"], "sort_order": 2},
    {"line_number": "step5_3", "description": "Step 5 line 3: line 1 - line 2", "line_type": "calculated",
     "source_rules": ["R-EIC-STEP5"], "sort_order": 3},
    {"line_number": "step5_4", "description": "Step 5 line 4: elected nontaxable combat pay (1040 1i)", "line_type": "calculated",
     "source_rules": ["R-EIC-STEP5"], "sort_order": 4},
    {"line_number": "step5_5", "description": "Step 5 line 5: earned income = line 3 + line 4", "line_type": "subtotal",
     "source_rules": ["R-EIC-STEP5"], "sort_order": 5},
    # Worksheet B (SE) — mainstream lines
    {"line_number": "wsb_1e", "description": "Worksheet B line 1e: net SE earnings - 1/2 SE tax (Sch 1 L3 - L15)", "line_type": "calculated",
     "source_rules": ["R-EIC-WSB-SE"], "sort_order": 10},
    {"line_number": "wsb_4a", "description": "Worksheet B line 4a: earned income from Step 5 (wages)", "line_type": "calculated",
     "source_rules": ["R-EIC-WSB-SE"], "sort_order": 11},
    {"line_number": "wsb_4b", "description": "Worksheet B line 4b: total earned income = 1e + 2c + 3 + 4a", "line_type": "subtotal",
     "source_rules": ["R-EIC-WSB-SE"], "sort_order": 12, "notes": "v1 mainstream: 2c (no-SE-required) and 3 (statutory) = 0."},
    {"line_number": "wsb_6", "description": "Worksheet B line 6: lookup amount (= 4b)", "line_type": "calculated",
     "source_rules": ["R-EIC-WSB-SE"], "sort_order": 13},
    # EIC table lookups
    {"line_number": "eic_lookup_earned", "description": "EIC Table credit at earned income (WS A L2 / WS B L7)", "line_type": "calculated",
     "source_rules": ["R-EIC-TABLE"], "sort_order": 20},
    {"line_number": "eic_lookup_agi", "description": "EIC Table credit at AGI (WS A L5 / WS B L10; lower-of rule)", "line_type": "calculated",
     "source_rules": ["R-EIC-TABLE", "R-EIC-LOWEROF"], "sort_order": 21},
    # Investment income worksheet (Pub 596 Worksheet 1)
    {"line_number": "inv_1", "description": "Inv WS line 1: 1040 line 2b (taxable interest) — modeled", "line_type": "calculated",
     "source_rules": ["R-EIC-INVINC"], "sort_order": 30},
    {"line_number": "inv_2", "description": "Inv WS line 2: 1040 line 2a (tax-exempt interest) + 8814 1b — 2a modeled", "line_type": "calculated",
     "source_rules": ["R-EIC-INVINC"], "sort_order": 31},
    {"line_number": "inv_3", "description": "Inv WS line 3: 1040 line 3b (ordinary dividends) — modeled", "line_type": "calculated",
     "source_rules": ["R-EIC-INVINC"], "sort_order": 32},
    {"line_number": "inv_5", "description": "Inv WS line 5: 1040 line 7 capital gain (loss -> 0) — cap-gain-distributions modeled", "line_type": "calculated",
     "source_rules": ["R-EIC-INVINC"], "sort_order": 33},
    {"line_number": "inv_other", "description": "Inv WS other (items 4/6/8-11): preparer 'other investment income'", "line_type": "input",
     "source_rules": ["R-EIC-INVINC"], "sort_order": 34, "notes": "GREEN preparer bucket for the unmodeled categories."},
    {"line_number": "inv_total", "description": "Inv WS total investment income (> limit -> no EIC)", "line_type": "total",
     "source_rules": ["R-EIC-INVINC"], "sort_order": 35},
    # Output
    {"line_number": "agg_27a", "description": "Earned Income Credit -> Form 1040 line 27a", "line_type": "total",
     "source_rules": ["R-EIC-LOWEROF", "R-EIC-27A"], "destination_form": "Form 1040 line 27a", "sort_order": 40},
]

EIC_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_EIC_001", "title": "Investment income over the §32(i) limit — no EIC", "severity": "error",
     "condition": "eic_investment_income_total > eic_investment_income_limit(year) [11,950 TY2025 / 12,200 TY2026]",
     "message": ("Not eligible — investment income exceeds the limit (${limit}). The Earned Income Credit is "
                 "disallowed (Pub 596 Rule 6). Line 27a is set to 0."),
     "notes": "JUDGMENT 1. Year-keyed limit. Hard disqualifier — the table alone would not zero it."},
    {"diagnostic_id": "D_EIC_002", "title": "Add unmodeled investment income (Worksheet 1 reminder)", "severity": "warning",
     "condition": "EIC claimed AND investment income is near the limit OR unmodeled categories may apply (4797/royalties/8814/passive)",
     "message": ("Reminder: investment income includes Form 4797 gain, royalties, personal-property rental net, "
                 "net passive income, and Form 8814 child amounts — none of which the software models. Enter "
                 "them in 'other investment income' so the limit check is complete (Pub 596 Worksheet 1)."),
     "notes": "JUDGMENT 1 no-silent-gap reminder. Prompts the preparer to populate other_investment_income."},
    {"diagnostic_id": "D_EIC_003", "title": "Form 4797 present — verify investment income (Worksheet 1 required)", "severity": "error",
     "condition": "eic_form_4797_present is True",
     "message": ("Verify manually: a Form 4797 is present. Pub 596 requires you to use Worksheet 1 to figure "
                 "investment income when Form 4797 is filed; confirm the Form 4797 gain (line 7 or line 9) is "
                 "included in 'other investment income' before relying on the EIC limit check."),
     "notes": "Pub 596 Worksheet 1 footnote: MUST use Worksheet 1 if 4797 present. We have the override field."},
    {"diagnostic_id": "D_EIC_004", "title": "Nontaxable combat pay — consider testing both ways", "severity": "info",
     "condition": "nontaxable_combat_pay > 0",
     "message": ("Nontaxable combat pay of ${amount} is present. Including it in earned income can raise OR "
                 "lower the credit depending on where earned income falls on the EIC curve. v1 honors your "
                 "election as entered — consider computing the credit both ways and choosing the larger."),
     "notes": "JUDGMENT 2. No auto-optimizer in v1; informational nudge only."},
    {"diagnostic_id": "D_EIC_005", "title": "Married filing separately without the §32(d) special rule — no EIC", "severity": "error",
     "condition": "filing_status == MFS AND NOT mfs_eic_special_rule",
     "message": ("Not eligible — married filing separately may claim the EIC only under the §32(d) special rule "
                 "(a qualifying child lived with you more than half the year AND you lived apart from your "
                 "spouse the last 6 months or are legally separated). The conditions are not asserted; line 27a "
                 "is set to 0 (Pub 596 Rule 3)."),
     "notes": "Rule 3. Preparer asserts the §32(d) conditions via mfs_eic_special_rule."},
    {"diagnostic_id": "D_EIC_006", "title": "Form 2555 filed — not eligible for EIC", "severity": "error",
     "condition": "files_form_2555 is True (existing Taxpayer fact)",
     "message": ("Not eligible — Form 2555 (Foreign Earned Income) is filed. You can't claim the Earned Income "
                 "Credit (Pub 596 Rule 5). Line 27a is set to 0."),
     "notes": "Rule 5. Reuses the existing Taxpayer.files_form_2555 fact."},
    {"diagnostic_id": "D_EIC_007", "title": "Childless EIC eligibility failed (age / dependent / QC of another)", "severity": "error",
     "condition": "eic_num_qualifying_children == 0 AND (NOT eic_childless_age_qualifies OR eic_claimed_as_dependent OR eic_qualifying_child_of_another)",
     "message": ("Not eligible (no qualifying child): you must be at least 25 and under 65 at year-end (one "
                 "spouse for MFJ), not be claimable as someone's dependent, and not be a qualifying child of "
                 "another person (Pub 596 Rules 11-13). Line 27a is set to 0."),
     "notes": "Childless rules. Age band statutory 25-64."},
    {"diagnostic_id": "D_EIC_008", "title": "Form 8862 required (EIC disallowed in a prior year)", "severity": "warning",
     "condition": "eic_disallowed_prior_year is True",
     "message": ("Form 8862 is required: the EIC (or another covered credit) was reduced or disallowed in a "
                 "prior year for a reason other than a math or clerical error. Form 8862 must be attached to "
                 "claim the credit this year."),
     "notes": "Triggers the 8862 data-map render (gated on this flag)."},
    {"diagnostic_id": "D_EIC_009", "title": "§32(k) EIC ban in effect — cannot claim", "severity": "error",
     "condition": "eic_ban_2yr is True OR eic_ban_10yr is True",
     "message": ("Not eligible — a §32(k) EIC ban is in effect (2 years for reckless/intentional disregard, 10 "
                 "years for fraud). The credit cannot be claimed during the ban period. Line 27a is set to 0."),
     "notes": "§32(k). Preparer-asserted ban flags."},
    {"diagnostic_id": "D_EIC_010", "title": "Qualifying child without a valid SSN — childless EIC only", "severity": "warning",
     "condition": "a Dependent flagged eic_qualifying_child lacks a valid SSN (tin_type != SSN)",
     "message": ("A qualifying child does not have a valid SSN, so the child does not count toward the larger "
                 "credit — only the childless EIC (if otherwise eligible) is allowed. Schedule EIC is still "
                 "attached (Pub 596 Chapter 2 SSN rule)."),
     "notes": "Drops the column to 0 children for the table; Schedule EIC still renders."},
    {"diagnostic_id": "D_EIC_011", "title": "Verify qualifying-child age/residency assertions", "severity": "info",
     "condition": "any Dependent flagged eic_qualifying_child (residency months / age-student / disabled assertions present)",
     "message": ("Verify the qualifying-child tests for each child: relationship, age (< 19, or < 24 + full-time "
                 "student, or any age if permanently disabled — and younger than you unless disabled), and "
                 "residency (lived with you in the US more than half the year). These are preparer assertions, "
                 "not adjudicated by the software."),
     "notes": "DoD: NO eligibility adjudication engine. Reminder only."},
    {"diagnostic_id": "D_EIC_012", "title": "Main home in Puerto Rico / U.S. territory — not eligible", "severity": "error",
     "condition": "eic_puerto_rico_territory_home is True OR NOT eic_main_home_us_half_year",
     "message": ("Not eligible — your main home must be in the United States (the 50 states and D.C., not Puerto "
                 "Rico or a U.S. territory) for more than half the year (Pub 596 Rule 14 / qualifying-child "
                 "residency). Line 27a is set to 0."),
     "notes": "US = 50 states + DC. Military on extended active duty outside the US counts as in-US."},
    {"diagnostic_id": "D_EIC_013", "title": "Not a U.S. citizen/resident all year (or NRA spouse) — not eligible", "severity": "error",
     "condition": "NOT eic_us_citizen_resident_all_year",
     "message": ("Not eligible — you (and your spouse, if MFJ) must be a U.S. citizen or resident alien all "
                 "year. A nonresident-alien spouse not treated as a resident (no §6013(g)/(h) election) "
                 "disqualifies the credit (Pub 596 Rule 4). Line 27a is set to 0."),
     "notes": "Rule 4."},
    {"diagnostic_id": "D_EIC_014", "title": "Qualifying child of more than one person — tie-breaker", "severity": "info",
     "condition": "preparer indicates a qualifying child could be claimed by more than one person",
     "message": ("A child who is a qualifying child of more than one person — only one person can claim the EIC "
                 "using that child. Apply the tie-breaker rules (Pub 596) and confirm the correct claimant. The "
                 "software does not adjudicate this."),
     "notes": "Tie-breaker is preparer-asserted; reminder only."},
    {"diagnostic_id": "D_EIC_015", "title": "Clergy / church-employee / statutory-employee SE path — not supported", "severity": "error",
     "condition": "eic_clergy_church_statutory is True",
     "message": ("Not supported — prepare manually: the Worksheet B clergy, church-employee (>= $108.28), or "
                 "statutory-employee path requires Schedule SE detail that is not built this sprint. The earned "
                 "income (and therefore the EIC) for this return is NOT computed."),
     "notes": "RED-defer. Mainstream sole-proprietor SE (Sch 1 L3 - L15) IS computed."},
    {"diagnostic_id": "D_EIC_016", "title": "Taxpayer/spouse missing a valid SSN — no EIC", "severity": "error",
     "condition": "NOT eic_valid_ssn_taxpayer OR (filing_status == MFJ AND NOT eic_valid_ssn_spouse)",
     "message": ("Not eligible — you (and your spouse, if filing jointly) must have a valid social security "
                 "number for employment by the due date of the return (Pub 596 Rule 2). An ITIN or a 'Not Valid "
                 "for Employment' SSN does not qualify. Line 27a is set to 0."),
     "notes": "Rule 2."},
]

EIC_SCENARIOS: list[dict] = [
    # ── Earned-income / credit-curve (Worksheet A) ──
    {"scenario_name": "EIC-T1 — 1 QC, plateau, TY2025: earned 15,000 -> max credit 4,328",
     "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "filing_status": "single", "qualifying_children": 1, "earned_income": 15000, "agi": 15000},
     "expected_outputs": {"eic_table_amount_earned": 4328, "1040_line_27a": 4328},
     "notes": "Earned 15,000 is in the plateau (>= 12,730 earned-income-amount, < 23,350 threshold) -> max 4,328."},
    {"scenario_name": "EIC-T2 — 0 QC childless, TY2025 phaseout: earned 14,000 -> partial",
     "scenario_type": "normal", "sort_order": 2,
     "inputs": {"tax_year": 2025, "filing_status": "single", "qualifying_children": 0, "earned_income": 14000, "agi": 14000,
                "eic_childless_age_qualifies": True},
     "expected_outputs": {"eic_table_in_phaseout": True, "1040_line_27a_gt": 0},
     "notes": ("Earned 14,000 > threshold 10,620 (0 QC, other), < completed 19,104 -> phaseout. Midpoint of the "
               "$50 bracket [14,000-14,050] = 14,025; credit = 649 - (14,025 - 10,620) x 7.65% = 649 - 260.48 = "
               "388.52 -> 389 (the integrity check pins the exact table row).")},
    {"scenario_name": "EIC-T3 — lower-of-AGI binds: 1 QC, earned 15,000 (plateau) but AGI 40,000 (phaseout)",
     "scenario_type": "normal", "sort_order": 3,
     "inputs": {"tax_year": 2025, "filing_status": "single", "qualifying_children": 1, "earned_income": 15000, "agi": 40000},
     "expected_outputs": {"eic_table_amount_earned": 4328, "lower_of_binds": True, "1040_line_27a_lt": 4328},
     "notes": ("AGI 40,000 > earned 15,000 AND >= threshold 23,350 -> credit = min(table(40,000), 4,328). "
               "table(40,000): midpoint 40,025; 4,328 - (40,025 - 23,350) x 15.98% = 4,328 - 2,664.66 = "
               "1,663.34 -> 1,663. The taxpayer gets the SMALLER (1,663), not the plateau 4,328.")},
    {"scenario_name": "EIC-T4 — $50-bracket midpoint pin (i1040gi example): 1 QC, earned 2,475 -> 842",
     "scenario_type": "edge", "sort_order": 4,
     "inputs": {"tax_year": 2025, "filing_status": "single", "qualifying_children": 1, "earned_income": 2475, "agi": 2475},
     "expected_outputs": {"eic_table_amount_earned": 842, "1040_line_27a": 842},
     "notes": ("Bracket [2,450-2,500], midpoint 2,475 x 34% (1 QC rising) = 841.5 -> ROUND_HALF_UP 842. The "
               "verbatim i1040gi reconciliation pin (Quality Rule 1). Earned 2,475 happens to be the midpoint.")},
    {"scenario_name": "EIC-T5 — investment income over limit -> 0 (D_EIC_001)",
     "scenario_type": "failure", "sort_order": 5,
     "inputs": {"tax_year": 2025, "filing_status": "single", "qualifying_children": 1, "earned_income": 15000, "agi": 15000,
                "investment_income_total": 12000},
     "expected_outputs": {"1040_line_27a": 0, "D_EIC_001_fires": True},
     "notes": "Investment income 12,000 > 11,950 (TY2025) -> hard disqualifier; credit zeroed despite a valid earned-income credit."},
    {"scenario_name": "EIC-T6a — childless age boundary: exactly 25 -> qualifies",
     "scenario_type": "edge", "sort_order": 6,
     "inputs": {"tax_year": 2025, "filing_status": "single", "qualifying_children": 0, "earned_income": 8000, "agi": 8000,
                "eic_childless_age_qualifies": True},
     "expected_outputs": {"1040_line_27a_gt": 0},
     "notes": "Age >= 25 and < 65: the band is inclusive of 25. (The build leg derives the flag from DOB.)"},
    {"scenario_name": "EIC-T6b — childless age boundary: 24 -> no credit (D_EIC_007)",
     "scenario_type": "failure", "sort_order": 7,
     "inputs": {"tax_year": 2025, "filing_status": "single", "qualifying_children": 0, "earned_income": 8000, "agi": 8000,
                "eic_childless_age_qualifies": False},
     "expected_outputs": {"1040_line_27a": 0, "D_EIC_007_fires": True},
     "notes": "Under 25 (and no qualifying child) -> ineligible."},
    {"scenario_name": "EIC-T7 — MFJ uses the MFJ phaseout column (higher than 'other')",
     "scenario_type": "normal", "sort_order": 8,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "qualifying_children": 2, "earned_income": 28000, "agi": 28000},
     "expected_outputs": {"uses_mfj_threshold": 30470, "eic_table_amount_earned": 7152},
     "notes": ("MFJ 2 QC: earned 28,000 < MFJ threshold 30,470 -> still plateau (max 7,152). The SAME earned "
               "income for a single filer (threshold 23,350) would already be phasing out — MFJ column matters.")},
    {"scenario_name": "EIC-T8 — combat pay election raises earned income into the plateau",
     "scenario_type": "edge", "sort_order": 9,
     "inputs": {"tax_year": 2025, "filing_status": "single", "qualifying_children": 1, "wages_1z": 10000,
                "nontaxable_combat_pay": 3000, "elect_combat_pay": True, "agi": 10000},
     "expected_outputs": {"eic_earned_income_result": 13000, "eic_table_amount_earned": 4328},
     "notes": "Earned = 10,000 + 3,000 elected combat pay = 13,000 (>= 12,730 -> plateau 4,328). Without the election: 10,000 (still rising)."},
    {"scenario_name": "EIC-T9 — 3+ QC max credit, TY2026: earned 20,000 -> 8,231",
     "scenario_type": "normal", "sort_order": 10,
     "inputs": {"tax_year": 2026, "filing_status": "single", "qualifying_children": 3, "earned_income": 20000, "agi": 20000},
     "expected_outputs": {"eic_table_amount_earned": 8231, "1040_line_27a": 8231},
     "notes": ("TY2026 3+ QC: earned 20,000 is in the plateau (>= 18,290 earned-income-amount, < 23,890 "
               "threshold) -> max credit 8,231 (the published TY2026 3+ amount). Pins TY2026 != TY2025 8,046.")},
    {"scenario_name": "EIC-T10 — Worksheet B SE path: net SE 12,000, 1/2-SE-tax 848 -> earned 11,152",
     "scenario_type": "normal", "sort_order": 11,
     "inputs": {"tax_year": 2025, "filing_status": "single", "qualifying_children": 1, "eic_self_employed": True,
                "eic_se_net_earnings": 12000, "eic_se_half_deduction": 848, "wages_1z": 0, "agi": 11152},
     "expected_outputs": {"wsb_1e": 11152, "wsb_4b": 11152, "eic_earned_income_result": 11152},
     "notes": "Worksheet B: 1e = 12,000 - 848 = 11,152; 4b = 1e + wages(0) = 11,152. Mainstream sole-proprietor."},
    # ── RED gates ──
    {"scenario_name": "EIC-G1 — MFS without §32(d) -> 0 (D_EIC_005)",
     "scenario_type": "failure", "sort_order": 20,
     "inputs": {"tax_year": 2025, "filing_status": "mfs", "qualifying_children": 1, "earned_income": 15000, "agi": 15000,
                "mfs_eic_special_rule": False},
     "expected_outputs": {"1040_line_27a": 0, "D_EIC_005_fires": True},
     "notes": "MFS without the special rule -> no EIC."},
    {"scenario_name": "EIC-G2 — Form 2555 filed -> 0 (D_EIC_006)",
     "scenario_type": "failure", "sort_order": 21,
     "inputs": {"tax_year": 2025, "filing_status": "single", "qualifying_children": 1, "earned_income": 15000, "agi": 15000,
                "files_form_2555": True},
     "expected_outputs": {"1040_line_27a": 0, "D_EIC_006_fires": True},
     "notes": "Rule 5: 2555 disqualifies."},
    {"scenario_name": "EIC-G3 — Form 4797 present -> verify-RED (D_EIC_003)",
     "scenario_type": "failure", "sort_order": 22,
     "inputs": {"tax_year": 2025, "filing_status": "single", "qualifying_children": 1, "earned_income": 15000, "agi": 15000,
                "eic_form_4797_present": True},
     "expected_outputs": {"D_EIC_003_fires": True},
     "notes": "Pub 596 Worksheet 1 requires the 4797 gain in investment income; verify before relying on the limit check."},
    {"scenario_name": "EIC-G4 — §32(k) 10-year ban -> 0 (D_EIC_009)",
     "scenario_type": "failure", "sort_order": 23,
     "inputs": {"tax_year": 2025, "filing_status": "single", "qualifying_children": 2, "earned_income": 18000, "agi": 18000,
                "eic_ban_10yr": True},
     "expected_outputs": {"1040_line_27a": 0, "D_EIC_009_fires": True},
     "notes": "Fraud ban blocks the credit regardless of the computed amount."},
    {"scenario_name": "EIC-G5 — clergy/statutory SE sub-path -> RED-defer (D_EIC_015)",
     "scenario_type": "failure", "sort_order": 24,
     "inputs": {"tax_year": 2025, "filing_status": "single", "qualifying_children": 1, "eic_self_employed": True,
                "eic_clergy_church_statutory": True},
     "expected_outputs": {"D_EIC_015_fires": True, "earned_income_not_computed": True},
     "notes": "Worksheet B clergy/church/statutory needs Sch SE detail -> not computed this sprint."},
]

EIC_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-EIC-STEP5", "IRS_2025_1040_INSTR", "primary", "Step 5 earned income (1z - Medicaid waiver + combat pay)"),
    ("R-EIC-ROUTE", "IRS_2025_1040_INSTR", "primary", "Step-5 Q2 Worksheet A vs B routing"),
    ("R-EIC-WSB-SE", "IRS_2025_1040_INSTR", "primary", "Worksheet B Parts 1/4 (SE earned income)"),
    ("R-EIC-TABLE", "IRS_2025_1040_INSTR", "primary", "EIC Table $50-bracket convention (pp.49-60)"),
    ("R-EIC-TABLE", "RP_2024_40", "primary", "TY2025 §32 parameters (§2.06)"),
    ("R-EIC-TABLE", "RP_2025_32", "primary", "TY2026 §32 parameters (§2.06)"),
    ("R-EIC-LOWEROF", "IRS_2025_1040_INSTR", "primary", "Worksheet A/B lower-of-AGI rule"),
    ("R-EIC-INVINC", "IRS_2025_PUB596", "primary", "Worksheet 1 investment income + Rule 6 limit"),
    ("R-EIC-INVINC", "RP_2024_40", "secondary", "§32(i) limit 11,950 (TY2025)"),
    ("R-EIC-INVINC", "RP_2025_32", "secondary", "§32(i) limit 12,200 (TY2026)"),
    ("R-EIC-ELIG", "IRS_2025_PUB596", "primary", "Rules for Everyone (1-7) + §32(k) ban"),
    ("R-EIC-CHILDLESS", "IRS_2025_PUB596", "primary", "Childless Rules 11-13 (age 25-64, dependent, QC of another)"),
    ("R-EIC-QC", "IRS_2025_PUB596", "primary", "Qualifying-child tests (Chapter 2)"),
    ("R-EIC-QC", "IRS_2025_SCHEDEIC_FORM", "primary", "Schedule EIC lines 3/4a/4b/5/6"),
    ("R-EIC-27A", "IRS_2025_1040_FORM", "primary", "Form 1040 line 27a (EIC)"),
    ("R-EIC-27A", "IRS_2025_1040_INSTR", "secondary", "Line 27a instructions"),
]


# ═══════════════════════════════════════════════════════════════════════════
# SCHEDULE_EIC — Qualifying Child Information (real IRS face, model-driven)
# ═══════════════════════════════════════════════════════════════════════════

SCHEDEIC_IDENTITY = {
    "form_number": "SCHEDULE_EIC",
    "form_title": "Schedule EIC (Form 1040) — Earned Income Credit (Qualifying Child Information) (TY2025)",
    "notes": (
        "Sprint Topic 7. REAL IRS FACE (Attachment Seq 43). DATA-MAP render — the "
        "per-qualifying-child columns (up to 3) are model-driven from the Dependent "
        "rows where eic_qualifying_child is set (the Schedule-B payer-listing "
        "precedent). NO compute on the face: the credit is figured by 1040_EIC and "
        "lands on 1040 line 27a. Renders whenever the EIC has >= 1 qualifying child."
    ),
}

SCHEDEIC_FACTS: list[dict] = [
    {"fact_key": "sei_child_name", "label": "Schedule EIC line 1: child's name (first/last)", "data_type": "string", "sort_order": 1,
     "notes": "PER CHILD (model-driven from Dependent). Up to 3 columns even if more children."},
    {"fact_key": "sei_child_ssn", "label": "Schedule EIC line 2: child's SSN", "data_type": "string", "sort_order": 2,
     "notes": "PER CHILD. From Dependent.tin (SSN); 'born and died in 2025' is the only no-SSN exception."},
    {"fact_key": "sei_child_year_of_birth", "label": "Schedule EIC line 3: child's year of birth", "data_type": "string", "sort_order": 3,
     "notes": "PER CHILD. From Dependent.date_of_birth."},
    {"fact_key": "sei_line4a_under24_student_younger", "label": "Schedule EIC line 4a: under 24 + student + younger than you? (Y/N)",
     "data_type": "boolean", "sort_order": 4,
     "notes": "PER CHILD. From Dependent age + is_full_time_student. If 4a No and 4b No -> not a qualifying child."},
    {"fact_key": "sei_line4b_disabled", "label": "Schedule EIC line 4b: permanently and totally disabled in 2025? (Y/N)",
     "data_type": "boolean", "sort_order": 5, "notes": "PER CHILD. From Dependent.is_permanently_disabled."},
    {"fact_key": "sei_child_relationship", "label": "Schedule EIC line 5: child's relationship to you", "data_type": "string", "sort_order": 6,
     "notes": "PER CHILD. From Dependent.relationship (son/daughter/stepchild/foster/sibling/etc.)."},
    {"fact_key": "sei_months_in_us", "label": "Schedule EIC line 6: months the child lived with you in the US (max 12)",
     "data_type": "integer", "sort_order": 7,
     "notes": "PER CHILD. From Dependent.months_resided_with_taxpayer. >half but <7 -> 7; born/died -> 12; max 12."},
]

SCHEDEIC_RULES: list[dict] = [
    {"rule_id": "R-SEI-RENDER", "title": "Schedule EIC render gate + per-child column mapping",
     "rule_type": "routing", "precedence": 0, "sort_order": 1,
     "formula": ("RENDER Schedule EIC when 1040_EIC has >= 1 qualifying child (eic_num_qualifying_children >= 1). "
                 "Map up to 3 Dependent rows (eic_qualifying_child set) to the child columns: line 1 name, line "
                 "2 SSN, line 3 year of birth, line 4a (under 24 + student + younger) / 4b (disabled), line 5 "
                 "relationship, line 6 months in the US."),
     "inputs": ["sei_child_name", "sei_child_ssn", "sei_child_year_of_birth", "sei_line4a_under24_student_younger",
                "sei_line4b_disabled", "sei_child_relationship", "sei_months_in_us"], "outputs": [],
     "description": ("ONCE PER RETURN (render). DATA-MAP face — no compute. The Schedule-B payer-listing "
                     "convention: the model rows drive the face; >3 children list only the first 3 (Schedule EIC "
                     "convention). Self-contained; the credit is figured by 1040_EIC.")},
]

SCHEDEIC_LINES: list[dict] = [
    {"line_number": "1", "description": "Child's name (first and last)", "line_type": "input", "source_rules": ["R-SEI-RENDER"], "sort_order": 1},
    {"line_number": "2", "description": "Child's SSN", "line_type": "input", "source_rules": ["R-SEI-RENDER"], "sort_order": 2},
    {"line_number": "3", "description": "Child's year of birth", "line_type": "input", "source_rules": ["R-SEI-RENDER"], "sort_order": 3},
    {"line_number": "4a", "description": "Under 24 at year-end, a student, and younger than you? (Y/N)", "line_type": "input",
     "source_rules": ["R-SEI-RENDER"], "sort_order": 4},
    {"line_number": "4b", "description": "Permanently and totally disabled during any part of 2025? (Y/N)", "line_type": "input",
     "source_rules": ["R-SEI-RENDER"], "sort_order": 5},
    {"line_number": "5", "description": "Child's relationship to you", "line_type": "input", "source_rules": ["R-SEI-RENDER"], "sort_order": 6},
    {"line_number": "6", "description": "Number of months child lived with you in the US during 2025 (max 12)", "line_type": "input",
     "source_rules": ["R-SEI-RENDER"], "sort_order": 7},
]

SCHEDEIC_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_SEI_001", "title": "Qualifying child not a child under 4a/4b but flagged for EIC", "severity": "error",
     "condition": "a Dependent flagged eic_qualifying_child has line 4a No AND line 4b No (and is not under 19)",
     "message": ("This child is flagged as an EIC qualifying child but fails the age test: not under 19, not "
                 "under 24 + a full-time student, and not permanently and totally disabled (Schedule EIC 4a/4b). "
                 "Remove the EIC flag or correct the age/student/disability data."),
     "notes": "Schedule EIC line 4a/4b consistency check (data-map)."},
]

SCHEDEIC_SCENARIOS: list[dict] = [
    {"scenario_name": "SEI-T1 — one qualifying child renders columns 1-6",
     "scenario_type": "normal", "sort_order": 1,
     "inputs": {"qualifying_children": [{"name": "Pat Q Sample", "ssn": "400-00-1234", "yob": "2015", "4a": "N",
                                          "4b": "N", "relationship": "Daughter", "months": 12}]},
     "expected_outputs": {"renders": True, "child_columns": 1},
     "notes": "Under-19 child (born 2015): 4a/4b both No is fine (the under-19 path doesn't use 4a). Renders all 6 lines."},
    {"scenario_name": "SEI-T2 — three+ children list only the first 3",
     "scenario_type": "edge", "sort_order": 2,
     "inputs": {"qualifying_children_count": 4},
     "expected_outputs": {"renders": True, "child_columns": 3},
     "notes": "Schedule EIC has 3 columns; a 4th qualifying child still counts in the table column (3+) but isn't listed."},
]

SCHEDEIC_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-SEI-RENDER", "IRS_2025_SCHEDEIC_FORM", "primary", "Qualifying-child lines 1-6 (verbatim)"),
]


# ═══════════════════════════════════════════════════════════════════════════
# 8867 — Paid Preparer's Due Diligence Checklist (real IRS face, data-map)
# ═══════════════════════════════════════════════════════════════════════════

F8867_IDENTITY = {
    "form_number": "8867",
    "form_title": "Form 8867 — Paid Preparer's Due Diligence Checklist (Rev. Nov 2024)",
    "notes": (
        "Sprint Topic 7. REAL IRS FACE (Attachment Seq 70). DATA-MAP render — all "
        "preparer-answered Y/N/N-A facts, NO compute. Required on every return "
        "claiming EIC / CTC-ACTC-ODC / AOTC / HOH. v1 covers EIC + CTC/ODC + HOH; "
        "the AOTC section (Part IV, Q13) renders but flags RED until Form 8863 "
        "exists (DoD). Header credit checkboxes are driven from the computed credits "
        "+ filing status; everything else is the preparer's answers."
    ),
}

F8867_FACTS: list[dict] = [
    {"fact_key": "f8867_claims_eic", "label": "Header: EIC claimed on the return", "data_type": "boolean", "sort_order": 1,
     "notes": "DERIVED from 1040 line 27a > 0 (or the EIC worksheet active). Drives Part II applicability."},
    {"fact_key": "f8867_claims_ctc_actc_odc", "label": "Header: CTC/ACTC/ODC claimed", "data_type": "boolean", "sort_order": 2,
     "notes": "DERIVED from Schedule 8812 (1040 line 19/28). Drives Part III."},
    {"fact_key": "f8867_claims_aotc", "label": "Header: AOTC claimed", "data_type": "boolean", "sort_order": 3,
     "notes": "v1: Form 8863 not built -> Part IV renders but flags RED (DoD)."},
    {"fact_key": "f8867_claims_hoh", "label": "Header: Head of Household filing status claimed", "data_type": "boolean", "sort_order": 4,
     "notes": "DERIVED from filing_status == HOH. Drives Part V."},
    {"fact_key": "f8867_q1_based_on_info", "label": "Q1: return based on info provided by / reasonably obtained from the taxpayer",
     "data_type": "boolean", "sort_order": 10, "notes": "Preparer answer (Part I general due diligence)."},
    {"fact_key": "f8867_q2_worksheets", "label": "Q2: completed the applicable worksheet(s) or equivalent",
     "data_type": "boolean", "sort_order": 11, "notes": "Preparer answer."},
    {"fact_key": "f8867_q3_knowledge", "label": "Q3: satisfied the knowledge requirement", "data_type": "boolean", "sort_order": 12,
     "notes": "Preparer answer."},
    {"fact_key": "f8867_q4_inconsistent", "label": "Q4: any information incorrect/incomplete/inconsistent (4a inquire / 4b document)",
     "data_type": "boolean", "sort_order": 13, "notes": "Preparer answer (Y triggers 4a/4b sub-answers)."},
    {"fact_key": "f8867_q5_record_retention", "label": "Q5: satisfied the record retention requirement", "data_type": "boolean",
     "sort_order": 14, "notes": "Preparer answer."},
    {"fact_key": "f8867_q6_substantiation", "label": "Q6: asked questions to substantiate eligibility/amounts", "data_type": "boolean",
     "sort_order": 15, "notes": "Preparer answer."},
    {"fact_key": "f8867_q7_prior_disallowance", "label": "Q7: asked whether the credit(s) were disallowed in a prior year",
     "data_type": "boolean", "sort_order": 16, "notes": "Preparer answer."},
    {"fact_key": "f8867_q8_recertification", "label": "Q8: completed the required recertification (Form 8862) if applicable",
     "data_type": "boolean", "sort_order": 17, "notes": "Preparer answer (links to the 8862 render)."},
    {"fact_key": "f8867_q9_eic", "label": "Part II Q9 (a/b/c): EIC residency/relationship/income inquiries", "data_type": "boolean",
     "sort_order": 20, "notes": "Preparer answer (EIC-specific)."},
    {"fact_key": "f8867_q10_12_ctc", "label": "Part III Q10-12: CTC/ACTC/ODC due-diligence answers", "data_type": "boolean",
     "sort_order": 21, "notes": "Preparer answer (CTC-specific)."},
    {"fact_key": "f8867_q13_aotc", "label": "Part IV Q13: AOTC due-diligence answer", "data_type": "boolean", "sort_order": 22,
     "notes": "v1: renders but RED until 8863 exists."},
    {"fact_key": "f8867_part_v_hoh", "label": "Part V: HOH determination questions answered", "data_type": "boolean", "sort_order": 23,
     "notes": "Preparer answer (HOH-specific)."},
]

F8867_RULES: list[dict] = [
    {"rule_id": "R-8867-RENDER", "title": "Form 8867 render gate + section applicability",
     "rule_type": "routing", "precedence": 0, "sort_order": 1,
     "formula": ("RENDER Form 8867 when ANY of EIC / CTC-ACTC-ODC / AOTC / HOH is claimed. Header checkboxes "
                 "DERIVED: EIC (1040 27a > 0), CTC/ACTC/ODC (Schedule 8812), AOTC (Form 8863 — not built, RED), "
                 "HOH (filing_status). Part I (Q1-8) always; Part II if EIC; Part III if CTC; Part IV if AOTC "
                 "(RED v1); Part V if HOH. All answers are preparer inputs — NO compute."),
     "inputs": ["f8867_claims_eic", "f8867_claims_ctc_actc_odc", "f8867_claims_aotc", "f8867_claims_hoh"], "outputs": [],
     "description": ("ONCE PER RETURN (render). DATA-MAP face (the 8812/Sch-B sibling precedent). Required on "
                     "every return claiming a covered credit/status; the §6695(g) penalty makes it mandatory. "
                     "v1 covers EIC + CTC/ODC + HOH; AOTC section RED until 8863.")},
]

F8867_LINES: list[dict] = [
    {"line_number": "1", "description": "Q1: based on taxpayer-provided / reasonably-obtained information", "line_type": "input",
     "source_rules": ["R-8867-RENDER"], "sort_order": 1},
    {"line_number": "2", "description": "Q2: completed applicable worksheet(s)", "line_type": "input", "source_rules": ["R-8867-RENDER"], "sort_order": 2},
    {"line_number": "3", "description": "Q3: knowledge requirement satisfied", "line_type": "input", "source_rules": ["R-8867-RENDER"], "sort_order": 3},
    {"line_number": "4", "description": "Q4: information inconsistent (4a inquire / 4b document)", "line_type": "input",
     "source_rules": ["R-8867-RENDER"], "sort_order": 4},
    {"line_number": "5", "description": "Q5: record retention requirement", "line_type": "input", "source_rules": ["R-8867-RENDER"], "sort_order": 5},
    {"line_number": "6", "description": "Q6: substantiation inquiries", "line_type": "input", "source_rules": ["R-8867-RENDER"], "sort_order": 6},
    {"line_number": "7", "description": "Q7: prior-year disallowance asked", "line_type": "input", "source_rules": ["R-8867-RENDER"], "sort_order": 7},
    {"line_number": "8", "description": "Q8: recertification (Form 8862) completed", "line_type": "input", "source_rules": ["R-8867-RENDER"], "sort_order": 8},
    {"line_number": "9", "description": "Part II (Q9 a/b/c): EIC due-diligence questions", "line_type": "input",
     "source_rules": ["R-8867-RENDER"], "sort_order": 9},
    {"line_number": "10", "description": "Part III (Q10-12): CTC/ACTC/ODC due-diligence questions", "line_type": "input",
     "source_rules": ["R-8867-RENDER"], "sort_order": 10},
    {"line_number": "13", "description": "Part IV (Q13): AOTC due-diligence question (RED until 8863)", "line_type": "input",
     "source_rules": ["R-8867-RENDER"], "sort_order": 11},
    {"line_number": "hoh", "description": "Part V: HOH determination questions", "line_type": "input", "source_rules": ["R-8867-RENDER"], "sort_order": 12},
]

F8867_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_8867_001", "title": "Form 8867 required but a due-diligence answer is blank", "severity": "error",
     "condition": "8867 renders (a covered credit/status claimed) AND any applicable Part I-V question is unanswered",
     "message": ("Form 8867 is required for this return (a covered credit or HOH is claimed), and a due-diligence "
                 "question is unanswered. Complete every applicable question — the §6695(g) penalty applies per "
                 "credit for an incomplete checklist."),
     "notes": "Data-map completeness gate. Required-answer enforcement (no compute)."},
    {"diagnostic_id": "D_8867_002", "title": "AOTC claimed on 8867 but Form 8863 is not supported", "severity": "error",
     "condition": "f8867_claims_aotc is True (Form 8863 not built this sprint)",
     "message": ("The AOTC due-diligence section (Part IV) is shown but Form 8863 (education credits) is not "
                 "built this version. Prepare the AOTC and its due diligence manually; the EIC/CTC/HOH sections "
                 "are supported."),
     "notes": "DoD: AOTC section renders but flags RED until 8863 exists."},
]

F8867_SCENARIOS: list[dict] = [
    {"scenario_name": "F8867-T1 — EIC + HOH return renders Parts I/II/V",
     "scenario_type": "normal", "sort_order": 1,
     "inputs": {"claims_eic": True, "claims_hoh": True, "all_questions_answered": True},
     "expected_outputs": {"renders": True, "part_ii_active": True, "part_v_active": True},
     "notes": "EIC + HOH -> header boxes checked; Parts I (general), II (EIC), V (HOH) apply."},
    {"scenario_name": "F8867-T2 — AOTC claimed -> Part IV RED (D_8867_002)",
     "scenario_type": "failure", "sort_order": 2,
     "inputs": {"claims_aotc": True},
     "expected_outputs": {"D_8867_002_fires": True},
     "notes": "AOTC due diligence not supported (8863 not built)."},
    {"scenario_name": "F8867-T3 — required but a question blank -> D_8867_001",
     "scenario_type": "failure", "sort_order": 3,
     "inputs": {"claims_eic": True, "q3_knowledge": None},
     "expected_outputs": {"D_8867_001_fires": True},
     "notes": "Incomplete checklist on a required return."},
]

F8867_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-8867-RENDER", "IRS_2025_8867_FORM", "primary", "Header credit boxes + Parts I-V questions (verbatim)"),
]


# ═══════════════════════════════════════════════════════════════════════════
# 8862 — Information To Claim Certain Credits After Disallowance (data-map)
# ═══════════════════════════════════════════════════════════════════════════

F8862_IDENTITY = {
    "form_number": "8862",
    "form_title": "Form 8862 — Information To Claim Certain Credits After Disallowance (Rev. Dec 2025)",
    "notes": (
        "Sprint Topic 7. REAL IRS FACE (Attachment Seq 862). DATA-MAP render gated "
        "on a preparer 'EIC/credit previously disallowed -> must file 8862' flag "
        "(eic_disallowed_prior_year). All preparer-answered facts, NO compute. Parts "
        "I (all filers), II (EIC), III (CTC/RCTC/ACTC/ODC), IV (AOTC), V (QC of more "
        "than one person)."
    ),
}

F8862_FACTS: list[dict] = [
    {"fact_key": "f8862_disallowance_year", "label": "Part I: tax year the credit was reduced or disallowed", "data_type": "string",
     "sort_order": 1, "notes": "Preparer entry. Part I, all filers."},
    {"fact_key": "f8862_was_math_error", "label": "Part I: disallowance was due to a math or clerical error only", "data_type": "boolean",
     "sort_order": 2, "notes": "Preparer answer. If Yes, Form 8862 is NOT required (D_8862_001)."},
    {"fact_key": "f8862_part_ii_eic", "label": "Part II: EIC after-disallowance answers (residency/relationship)", "data_type": "boolean",
     "sort_order": 3, "notes": "Preparer answer (EIC section)."},
    {"fact_key": "f8862_part_iii_ctc", "label": "Part III: CTC/RCTC/ACTC/ODC after-disallowance answers", "data_type": "boolean",
     "sort_order": 4, "notes": "Preparer answer."},
    {"fact_key": "f8862_part_iv_aotc", "label": "Part IV: AOTC after-disallowance answers", "data_type": "boolean", "sort_order": 5,
     "notes": "v1: AOTC not built; section data-mapped only."},
    {"fact_key": "f8862_part_v_qc_shared", "label": "Part V: qualifying child of more than one person", "data_type": "boolean",
     "sort_order": 6, "notes": "Preparer answer (tie-breaker context)."},
]

F8862_RULES: list[dict] = [
    {"rule_id": "R-8862-RENDER", "title": "Form 8862 render gate (previously disallowed) + part mapping",
     "rule_type": "routing", "precedence": 0, "sort_order": 1,
     "formula": ("RENDER Form 8862 when eic_disallowed_prior_year is True AND NOT f8862_was_math_error. Map "
                 "Part I (year + math-error), Part II (EIC), Part III (CTC/RCTC/ACTC/ODC), Part IV (AOTC), Part "
                 "V (QC of more than one person) from the preparer answers. NO compute."),
     "inputs": ["f8862_disallowance_year", "f8862_was_math_error", "f8862_part_ii_eic", "f8862_part_iii_ctc",
                "f8862_part_iv_aotc", "f8862_part_v_qc_shared"], "outputs": [],
     "description": ("ONCE PER RETURN (render). DATA-MAP face. Required to RE-claim a credit after a non-math "
                     "disallowance; attaches to the return. Gated on the preparer flag (D_EIC_008 surfaces it).")},
]

F8862_LINES: list[dict] = [
    {"line_number": "1", "description": "Part I: tax year the credit was disallowed", "line_type": "input", "source_rules": ["R-8862-RENDER"], "sort_order": 1},
    {"line_number": "2", "description": "Part I: disallowance due to math/clerical error?", "line_type": "input", "source_rules": ["R-8862-RENDER"], "sort_order": 2},
    {"line_number": "part_ii", "description": "Part II: Earned Income Credit", "line_type": "input", "source_rules": ["R-8862-RENDER"], "sort_order": 3},
    {"line_number": "part_iii", "description": "Part III: CTC/RCTC/ACTC/ODC", "line_type": "input", "source_rules": ["R-8862-RENDER"], "sort_order": 4},
    {"line_number": "part_iv", "description": "Part IV: AOTC", "line_type": "input", "source_rules": ["R-8862-RENDER"], "sort_order": 5},
    {"line_number": "part_v", "description": "Part V: qualifying child of more than one person", "line_type": "input", "source_rules": ["R-8862-RENDER"], "sort_order": 6},
]

F8862_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_8862_001", "title": "Form 8862 not required (disallowance was a math/clerical error)", "severity": "info",
     "condition": "f8862_was_math_error is True",
     "message": ("Form 8862 is not required: the prior-year disallowance was due to a math or clerical error. "
                 "Do not attach Form 8862 for a math-error adjustment (Form 8862 instructions)."),
     "notes": "Data-map gate refinement — math-error disallowance does NOT require 8862."},
]

F8862_SCENARIOS: list[dict] = [
    {"scenario_name": "F8862-T1 — EIC disallowed (non-math) renders Parts I/II",
     "scenario_type": "normal", "sort_order": 1,
     "inputs": {"eic_disallowed_prior_year": True, "was_math_error": False, "disallowance_year": "2023"},
     "expected_outputs": {"renders": True, "part_ii_active": True},
     "notes": "Non-math disallowance -> 8862 required; Part I (year) + Part II (EIC)."},
    {"scenario_name": "F8862-T2 — math-error disallowance -> not required (D_8862_001)",
     "scenario_type": "edge", "sort_order": 2,
     "inputs": {"eic_disallowed_prior_year": True, "was_math_error": True},
     "expected_outputs": {"renders": False, "D_8862_001_fires": True},
     "notes": "Math/clerical error does not require 8862."},
]

F8862_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-8862-RENDER", "IRS_2025_8862_FORM", "primary", "Parts I-V structure (verbatim)"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS (9)
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-EIC-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "EIC -> 1040 line 27a (lower-of result, after eligibility gates)",
     "description": ("Validates R-EIC-27A/LOWEROF. Bugs it catches: the EIC not landing on line 27a; an "
                     "eligibility gate failing to zero the credit; the larger (not smaller) table amount used."),
     "definition": {"kind": "flow_assertion", "form": "1040_EIC", "output": "agg_27a",
                    "must_write_to": {"form": "1040", "line": "27a"}},
     "sort_order": 1},
    {"assertion_id": "FA-1040-EIC-02", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "EIC §32 parameter tables (year-keyed, both years verified independently)",
     "description": ("Pins the §32 parameters per year per #-children: earned-income amount, max credit, "
                     "threshold/completed phaseout (MFJ + other), investment-income limit. Bug it catches: a "
                     "TY2025 amount carried to TY2026, or a transcription error in any cell."),
     "definition": {"kind": "constants_check", "form": "1040_EIC",
                    "constants": {
                        "2025": EIC_PARAMS[2025],
                        "2026": EIC_PARAMS[2026],
                        "rates": EIC_RATES,
                        "applies_to_years": [2025, 2026]}},
     "sort_order": 2},
    {"assertion_id": "FA-1040-EIC-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "EIC Table $50-bracket midpoint convention (ROUND_HALF_UP)",
     "description": ("Validates R-EIC-TABLE. The credit = §32 f(bracket midpoint), ROUND_HALF_UP — the Tax-Table "
                     "convention. Pins the i1040gi example: 1 QC, lookup 2,475 -> midpoint 2,475 x 34% = 841.5 "
                     "-> 842. Bug it catches: evaluating at the bracket floor, or truncating instead of half-up."),
     "definition": {"kind": "formula_check", "form": "1040_EIC",
                    "formula": "eic_table(2475, qc=1, status='other', year=2025) == 842",
                    "convention": "midpoint_x_rate_round_half_up"},
     "sort_order": 3},
    {"assertion_id": "FA-1040-EIC-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Lower-of-AGI/earned-income rule binds only when AGI > earned AND AGI >= threshold",
     "description": ("Validates R-EIC-LOWEROF. The credit is min(table(earned), table(AGI)) once AGI is in/past "
                     "the phaseout; equal to table(earned) otherwise. Bug it catches: always using earned "
                     "income (ignoring a higher AGI), or always taking the min."),
     "definition": {"kind": "formula_check", "form": "1040_EIC",
                    "formula": ("credit == table(earned) if (AGI == earned or AGI < threshold) "
                                "else min(table(AGI), table(earned))")},
     "sort_order": 4},
    {"assertion_id": "FA-1040-EIC-05", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Investment income over the §32(i) limit zeroes the credit",
     "description": ("Validates R-EIC-INVINC. inv = 2b + 2a + 3b + max(0, 7a) + other_investment_income; "
                     "inv > limit(year) -> credit 0 (D_EIC_001). Bug it catches: the limit not enforced, or a "
                     "year-wrong limit (11,950 vs 12,200)."),
     "definition": {"kind": "gating_check", "form": "1040_EIC",
                    "blockers": ["investment_income_over_limit"],
                    "expect": {"result_blank": True, "red_fires": True},
                    "limit_by_year": {"2025": 11950, "2026": 12200}},
     "sort_order": 5},
    {"assertion_id": "FA-1040-EIC-06", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Childless EIC age band 25-64 (statutory, non-indexed; one spouse for MFJ)",
     "description": ("Validates R-EIC-CHILDLESS. With 0 qualifying children, the taxpayer (or one spouse for "
                     "MFJ) must be >= 25 and < 65 at year-end. Bug it catches: an off-by-one on the boundary "
                     "(24/25 or 64/65) or 'inflation-adjusting' the statutory band."),
     "definition": {"kind": "constants_check", "form": "1040_EIC",
                    "constants": {"childless_age_min": 25, "childless_age_max_exclusive": 65,
                                  "applies_to_years": [2025, 2026]}},
     "sort_order": 6},
    {"assertion_id": "FA-1040-EIC-07", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Combat-pay election: included in earned income only when elected",
     "description": ("Validates R-EIC-STEP5. earned_income includes nontaxable_combat_pay iff elect_combat_pay; "
                     "Medicaid waiver is subtracted unless elect_include_medicaid_waiver. Bug it catches: combat "
                     "pay always added (or never), defeating JUDGMENT 2."),
     "definition": {"kind": "formula_check", "form": "1040_EIC",
                    "formula": ("step5_5 == (1z - (0 if elect_include_medicaid_waiver else medicaid_waiver_8s)) "
                                "+ (nontaxable_combat_pay if elect_combat_pay else 0)")},
     "sort_order": 7},
    {"assertion_id": "FA-1040-EIC-08", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "Filing-status column: QSS uses 'other', MFS-with-§32(d) uses 'other', MFJ uses 'mfj'",
     "description": ("Pins the column-selection rule (UNLIKE QDCGT, QSS does NOT align with MFJ here). "
                     "Bug it catches: QSS routed to the MFJ phaseout column, or MFS-§32(d) not getting the "
                     "'other' amounts."),
     "definition": {"kind": "constants_check", "form": "1040_EIC",
                    "constants": {"column_for_status": {"single": "other", "hoh": "other", "qss": "other",
                                                         "mfs": "other", "mfj": "mfj"},
                                  "note": "QSS=other (not MFJ); MFS uses other only when §32(d) met else no EIC",
                                  "applies_to_years": [2025, 2026]}},
     "sort_order": 8},
    {"assertion_id": "FA-1040-EIC-09", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Eligibility gates each zero the credit with a registered RED (no silent gap)",
     "description": ("Validates R-EIC-ELIG/CHILDLESS + the RED-defer paths: missing SSN (D_EIC_016), MFS without "
                     "§32(d) (D_EIC_005), Form 2555 (D_EIC_006), childless age/dependent/QC-of-another "
                     "(D_EIC_007), §32(k) ban (D_EIC_009), PR/territory or non-US home (D_EIC_012), not "
                     "citizen/resident (D_EIC_013), clergy/statutory SE (D_EIC_015), 4797 verify (D_EIC_003) — "
                     "each leaves the credit 0/uncomputed with a RED, never a silently-wrong number."),
     "definition": {"kind": "gating_check", "form": "1040_EIC",
                    "blockers": ["missing_ssn", "mfs_no_special_rule", "form_2555", "childless_ineligible",
                                 "eic_ban", "non_us_home", "not_citizen_resident", "clergy_statutory_se",
                                 "form_4797_present"],
                    "expect": {"result_blank": True, "red_fires": True}},
     "sort_order": 9},
]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY FORM LINKS  (source_code, form_code, link_type)
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_PUB596", "1040_EIC", "governs"),
    ("IRS_2025_1040_INSTR", "1040_EIC", "governs"),
    ("RP_2024_40", "1040_EIC", "governs"),
    ("RP_2025_32", "1040_EIC", "governs"),
    ("IRS_2025_1040_FORM", "1040_EIC", "informs"),
    ("IRS_2025_SCHEDEIC_FORM", "SCHEDULE_EIC", "governs"),
    ("IRS_2025_PUB596", "SCHEDULE_EIC", "informs"),
    ("IRS_2025_8867_FORM", "8867", "governs"),
    ("IRS_2025_8862_FORM", "8862", "governs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORMS ROSTER
# ═══════════════════════════════════════════════════════════════════════════

FORMS: list[dict] = [
    {"identity": EIC_IDENTITY, "facts": EIC_FACTS, "rules": EIC_RULES, "lines": EIC_LINES,
     "diagnostics": EIC_DIAGNOSTICS, "scenarios": EIC_SCENARIOS, "rule_links": EIC_RULE_LINKS},
    {"identity": SCHEDEIC_IDENTITY, "facts": SCHEDEIC_FACTS, "rules": SCHEDEIC_RULES, "lines": SCHEDEIC_LINES,
     "diagnostics": SCHEDEIC_DIAGNOSTICS, "scenarios": SCHEDEIC_SCENARIOS, "rule_links": SCHEDEIC_RULE_LINKS},
    {"identity": F8867_IDENTITY, "facts": F8867_FACTS, "rules": F8867_RULES, "lines": F8867_LINES,
     "diagnostics": F8867_DIAGNOSTICS, "scenarios": F8867_SCENARIOS, "rule_links": F8867_RULE_LINKS},
    {"identity": F8862_IDENTITY, "facts": F8862_FACTS, "rules": F8862_RULES, "lines": F8862_LINES,
     "diagnostics": F8862_DIAGNOSTICS, "scenarios": F8862_SCENARIOS, "rule_links": F8862_RULE_LINKS},
]


# ═══════════════════════════════════════════════════════════════════════════
# Command
# ═══════════════════════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = (
        "Load the Earned Income Credit specs into Rule Studio (creates 1040_EIC, "
        "SCHEDULE_EIC, 8867, 8862). Refuses to seed until Ken sets READY_TO_SEED=True."
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()

        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad 1040_EIC / SCHEDULE_EIC / 8867 / 8862 specs (Topic 7)\n"))

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
                "REFUSING TO SEED 1040_EIC/SCHEDULE_EIC/8867/8862: not cleared to seed.\n"
                "\n"
                "Content is authored, but seeding is gated until Ken reviews the packet\n"
                "(the source citations, the §32 parameter tables BOTH years verified\n"
                "independently, the EIC Table $50-bracket midpoint convention, the v1\n"
                "in/out scope enumeration, the Worksheet-B SE sourcing, and the\n"
                "qualifying-child / eligibility gate set) and flips the sentinel.\n"
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
    # Topics / sources (mirror load_1040_retirement.py exactly)
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
        self.stdout.write("DATABASE TOTALS (after load_1040_eic)")
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

        for fn in ("1040_EIC", "SCHEDULE_EIC", "8867", "8862"):
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
