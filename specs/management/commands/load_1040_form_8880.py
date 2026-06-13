"""Load the FORM_8880 spec — Credit for Qualified Retirement Savings
Contributions (the Saver's Credit, §25B) → Schedule 3 line 4.

Sprint roster #9 (the ride-along; Ken pulled it back in 2026-06-13). A
nonrefundable credit = an AGI-tiered applicable percentage (50/20/10/0%) ×
the smaller of each person's qualifying contributions or $2,000, limited by
tax liability. Two columns: (a) You, (b) Spouse.

Single form, the `load_1040_simplified_method.py` precedent. Schedule 3 line 4
already exists in tts-tax-app as a direct-entry feeder (in the Sch 3 total +
the CLW-A pre-CTC set), so the cross-form plumbing is ready.

Constants VERIFIED 2026-06-13:
  - 2025 line-9 AGI tier table — VERBATIM from f8880.pdf (2025), extracted via
    pymupdf (tts-tax-app server/.scratch/f8880.pdf).
  - 2026 TOP cutoffs — VERIFIED from the IRS 2026 COLA announcement (MFJ
    $80,500 / HoH $60,375 / single-MFS $40,250). The 2026 INTERMEDIATE 50%/20%
    breakpoints are NOT yet published (they land on the 2026 Form 8880 ~Dec
    2026) → carried from 2025 as an INTERIM (D_8880_003 re-pin), the spine
    derived-2026-Tax-Table precedent.

Box-12 derive (Ken): Form 8880 line 2 (elective deferrals) is computed from the
W-2 box-12 entries with qualifying codes {D,E,F,G,H,S,AA,BB,EE}, per W-2 owner
(a new tts-tax-app W2Income.owner field + "spouse's W-2" checkbox at the build
leg). Line 1 (IRA) + line 4 (distributions) stay preparer facts.

Source brief: tts-tax-app `server/specs/_8880_savers_credit_source_brief.md`.

SAFETY GUARD: READY_TO_SEED flipped 2026-06-13 — Ken approved the scope walk
in-session ("Looks good. Run it.").
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


READY_TO_SEED = True  # FLIPPED 2026-06-13 — Ken approved the scope walk ("Looks good. Run it.").


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1040"]


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

_INF = 10 ** 12

# Line-9 applicable-decimal tiers (upper_bound_inclusive, decimal). Status key:
# mfj / hoh / other (single + MFS + QSS, per the form's third column).
# 2025: VERBATIM from f8880.pdf (2025). 2026: top cutoffs VERIFIED (COLA
# notice); the 50%/20% intermediate breakpoints carried from 2025 (INTERIM —
# D_8880_003 re-pin when the 2026 Form 8880 publishes).
SAVERS_AGI_TIERS: dict = {
    2025: {
        "mfj":   [(47500, "0.5"), (51000, "0.2"), (79000, "0.1"), (_INF, "0.0")],
        "hoh":   [(35625, "0.5"), (38250, "0.2"), (59250, "0.1"), (_INF, "0.0")],
        "other": [(23750, "0.5"), (25500, "0.2"), (39500, "0.1"), (_INF, "0.0")],
    },
    2026: {
        "mfj":   [(47500, "0.5"), (51000, "0.2"), (80500, "0.1"), (_INF, "0.0")],
        "hoh":   [(35625, "0.5"), (38250, "0.2"), (60375, "0.1"), (_INF, "0.0")],
        "other": [(23750, "0.5"), (25500, "0.2"), (40250, "0.1"), (_INF, "0.0")],
    },
}

# §25B statutory, NON-indexed.
SAVERS_CONTRIB_CAP = 2000        # per person (line 6)

# Form 8880 line 2 qualifying W-2 box-12 codes (elective deferrals + voluntary).
QUALIFYING_BOX12_CODES = {"D", "E", "F", "G", "H", "S", "AA", "BB", "EE"}


def _status_key(filing_status: str) -> str:
    if filing_status in ("mfj",):
        return "mfj"
    if filing_status in ("hoh",):
        return "hoh"
    return "other"   # single / mfs / qss


def savers_decimal(agi: int, filing_status: str, tax_year: int) -> str:
    """Form 8880 line 9 — the applicable decimal (shared traceability; the
    integrity gate re-types it)."""
    table = SAVERS_AGI_TIERS.get(tax_year) or SAVERS_AGI_TIERS[2026]
    for upper, dec in table[_status_key(filing_status)]:
        if agi <= upper:
            return dec
    return "0.0"


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("savers_credit", "Saver's Credit (§25B) — Form 8880, AGI-tiered nonrefundable credit -> Schedule 3 line 4"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_1040_FORM",
    "IRS_2025_1040_INSTR",
]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_F8880_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Form 8880 — Credit for Qualified Retirement Savings Contributions",
        "citation": "Form 8880 (2025); f8880.pdf; Attachment Sequence No. 54",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f8880.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": "The line-9 AGI tier table extracted VERBATIM 2026-06-13 from f8880.pdf (2025) via pymupdf. Two columns (a) You / (b) Spouse; line 6 caps each at $2,000; line 12 -> Schedule 3 line 4.",
        "topics": ["savers_credit"],
        "excerpts": [
            {
                "excerpt_label": "Line 9 applicable-decimal table (2025, verbatim)",
                "location_reference": "Form 8880 (2025), line 9",
                "excerpt_text": (
                    "IF line 8 is Over / But not over ... THEN enter on line 9 (MFJ / HoH / "
                    "Single, MFS, or QSS): up to $23,750 -> .5/.5/.5; $23,750-$25,500 -> .5/.5/.2; "
                    "$25,500-$35,625 -> .5/.5/.1; $35,625-$38,250 -> .5/.2/.1; $38,250-$39,500 -> "
                    ".5/.1/.1; $39,500-$47,500 -> .5/.1/0; $47,500-$51,000 -> .2/.1/0; "
                    "$51,000-$59,250 -> .1/.1/0; $59,250-$79,000 -> .1/0/0; over $79,000 -> 0/0/0. "
                    "If line 9 is zero, stop; you can't take this credit."
                ),
                "summary_text": "Per-status tiers: MFJ 50%<=47,500 / 20%<=51,000 / 10%<=79,000; HoH 50%<=35,625 / 20%<=38,250 / 10%<=59,250; single/MFS/QSS 50%<=23,750 / 20%<=25,500 / 10%<=39,500.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Caution disqualifiers + the $2,000 cap (2025, verbatim)",
                "location_reference": "Form 8880 (2025), Caution + lines 1/2/4/6",
                "excerpt_text": (
                    "You cannot take this credit if either of the following applies. The amount on "
                    "Form 1040 line 11 is more than $39,500 ($59,250 HoH; $79,000 MFJ). The person(s) "
                    "who made the qualifying contribution was born after January 1, 2008, is claimed "
                    "as a dependent on someone else's 2025 return, or was a student. Line 1 "
                    "traditional and Roth IRA contributions. Line 2 elective deferrals to a 401(k) or "
                    "other qualified employer plan, voluntary employee contributions, and 501(c)(18)(D) "
                    "plan contributions. Line 4 distributions received (testing period). Line 6 in each "
                    "column, enter the smaller of line 5 or $2,000."
                ),
                "summary_text": "Disqualifiers: AGI over the top; born after Jan 1 2008 (under 18); claimed as a dependent; full-time student. Per-person $2,000 cap. Line 2 = elective deferrals (W-2 box 12 codes D/E/F/G/H/S/AA/BB/EE).",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2026_COLA_8880",
        "source_type": "official_guidance",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2026,
        "tax_year_end": 2026,
        "title": "IRS 2026 cost-of-living adjustments — Saver's Credit income limits",
        "citation": "IRS 2026 retirement COLA announcement (Nov 2025)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/newsroom",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": False,
        "trust_score": 9.00,
        "requires_human_review": True,
        "notes": "2026 TOP cutoffs VERIFIED (MFJ $80,500 / HoH $60,375 / single-MFS $40,250). The 2026 INTERMEDIATE 50%/20% breakpoints are NOT yet published — carried from 2025 as an interim. REQUIRES HUMAN REVIEW: re-pin all 2026 tiers from the 2026 Form 8880 (~Dec 2026); D_8880_003.",
        "topics": ["savers_credit"],
        "excerpts": [
            {
                "excerpt_label": "2026 Saver's Credit top income limits (verbatim)",
                "location_reference": "IRS 2026 COLA announcement",
                "excerpt_text": (
                    "The income limit for the Saver's Credit for 2026 is $80,500 for married couples "
                    "filing jointly, up from $79,000 for 2025; $60,375 for heads of household, up from "
                    "$59,250; and $40,250 for singles and married individuals filing separately, up "
                    "from $39,500."
                ),
                "summary_text": "2026 top cutoffs (0% above): MFJ 80,500 / HoH 60,375 / single-MFS 40,250. Intermediate 50%/20% breakpoints pending the 2026 form (interim = 2025 values).",
                "is_key_excerpt": True,
            },
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_F8880_FORM", "FORM_8880", "governs"),
    ("IRS_2026_COLA_8880", "FORM_8880", "informs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM: FORM_8880
# ═══════════════════════════════════════════════════════════════════════════

F8880_IDENTITY = {
    "form_number": "FORM_8880",
    "form_title": "Form 8880 — Credit for Qualified Retirement Savings Contributions (Saver's Credit) (TY2025)",
    "notes": (
        "Roster #9 (Ken's 6 scope decisions 2026-06-13). Real IRS face, ONE per "
        "return, two columns (a) You / (b) Spouse. Nonrefundable §25B credit: an "
        "AGI-tiered applicable percentage (50/20/10/0%) x the smaller of each "
        "person's qualifying contributions or $2,000, limited by tax liability "
        "-> Schedule 3 line 4. Line 2 elective deferrals AUTO-DERIVED from W-2 "
        "box-12 qualifying codes per owner (Decision 1). Eligibility (18+, not a "
        "full-time student, not a dependent) computed. Year-keyed AGI tiers "
        "(2025 verified verbatim; 2026 top cutoffs verified + interim 50/20% "
        "breakpoints, D_8880_003 re-pin)."
    ),
}

F8880_FACTS: list[dict] = [
    {"fact_key": "f8880_you_ira", "label": "Line 1 (You) — traditional + Roth IRA contributions",
     "data_type": "decimal", "default_value": "0", "sort_order": 1, "notes": "PER-PERSON INPUT (column a)."},
    {"fact_key": "f8880_spouse_ira", "label": "Line 1 (Spouse) — traditional + Roth IRA contributions",
     "data_type": "decimal", "default_value": "0", "sort_order": 2, "notes": "PER-PERSON INPUT (column b)."},
    {"fact_key": "f8880_you_deferrals", "label": "Line 2 (You) — elective deferrals (auto from W-2 box 12)",
     "data_type": "decimal", "default_value": "0", "sort_order": 3,
     "notes": ("DERIVED (override). Sum of W-2 box-12 amounts with qualifying codes (D/E/F/G/H/S/AA/BB/EE) "
               "on the taxpayer's W-2s. YELLOW.")},
    {"fact_key": "f8880_spouse_deferrals", "label": "Line 2 (Spouse) — elective deferrals (auto from W-2 box 12)",
     "data_type": "decimal", "default_value": "0", "sort_order": 4, "notes": "DERIVED (override). Spouse's W-2 box-12 qualifying codes."},
    {"fact_key": "f8880_you_distributions", "label": "Line 4 (You) — distributions received in the testing period",
     "data_type": "decimal", "default_value": "0", "sort_order": 5,
     "notes": "PER-PERSON INPUT. The testing period = the current year + 2 prior + through the due date (Decision 3, preparer fact)."},
    {"fact_key": "f8880_spouse_distributions", "label": "Line 4 (Spouse) — distributions received in the testing period",
     "data_type": "decimal", "default_value": "0", "sort_order": 6, "notes": "PER-PERSON INPUT."},
    {"fact_key": "f8880_you_full_time_student", "label": "Were you a full-time student during the year?",
     "data_type": "boolean", "default_value": "false", "sort_order": 7, "notes": "ELIGIBILITY (Decision 2). True -> column a excluded."},
    {"fact_key": "f8880_spouse_full_time_student", "label": "Was your spouse a full-time student during the year?",
     "data_type": "boolean", "default_value": "false", "sort_order": 8, "notes": "ELIGIBILITY. True -> column b excluded."},
    # ── Outputs ──
    {"fact_key": "f8880_total_contributions", "label": "Line 7 — total qualifying contributions (both columns, max $4,000)",
     "data_type": "decimal", "sort_order": 20, "notes": "OUTPUT. Sum of line 6 (each = min(line 5, $2,000))."},
    {"fact_key": "f8880_decimal", "label": "Line 9 — applicable decimal (0.5 / 0.2 / 0.1 / 0.0)",
     "data_type": "decimal", "sort_order": 21, "notes": "OUTPUT. AGI tier lookup by filing status + year."},
    {"fact_key": "f8880_credit", "label": "Line 12 — saver's credit -> Schedule 3 line 4",
     "data_type": "decimal", "sort_order": 22, "notes": "OUTPUT. min(line 10 = line 7 x line 9, the tax-liability cap)."},
]

F8880_RULES: list[dict] = [
    {"rule_id": "R-8880-ELIGIBILITY", "title": "Per-person eligibility (18+, not a full-time student, not a dependent)",
     "rule_type": "routing", "precedence": 1, "sort_order": 1,
     "formula": ("A person counts iff: born on/before Jan 1 of (tax_year - 17) [age 18+] AND NOT full_time_student "
                 "AND NOT claimed_as_dependent. An ineligible person's columns (lines 1/2) are excluded; both "
                 "ineligible -> no credit. D_8880_002 when an ineligible person has contributions."),
     "inputs": ["f8880_you_full_time_student", "f8880_spouse_full_time_student"], "outputs": [],
     "description": "Decision 2. The 'Caution' disqualifiers, computed from DOB + the 0047 dependent fact + the new student facts."},
    {"rule_id": "R-8880-LINE2-BOX12", "title": "Line 2 — elective deferrals auto-derived from W-2 box 12",
     "rule_type": "calculation", "precedence": 2, "sort_order": 2,
     "formula": ("f8880_{you,spouse}_deferrals = sum(W2Box12Entry.amount) over that owner's W-2s where code in "
                 "{D,E,F,G,H,S,AA,BB,EE}. Preparer override allowed (YELLOW)."),
     "inputs": [], "outputs": ["f8880_you_deferrals", "f8880_spouse_deferrals"],
     "description": "Decision 1. Requires the new tts-tax-app W2Income.owner field; non-qualifying codes (DD/W/C...) excluded."},
    {"rule_id": "R-8880-CONTRIB", "title": "Lines 3-7 — net contributions, the $2,000 per-person cap, total",
     "rule_type": "calculation", "precedence": 3, "sort_order": 3,
     "formula": ("per column: line3 = line1 + line2; line5 = max(0, line3 - line4); line6 = min(line5, 2000). "
                 "f8880_total_contributions (line 7) = line6(you) + line6(spouse) [eligible columns only]."),
     "inputs": ["f8880_you_ira", "f8880_spouse_ira"], "outputs": ["f8880_total_contributions"],
     "description": "$2,000 cap statutory §25B. Max line 7 = $4,000 (MFJ)."},
    {"rule_id": "R-8880-DECIMAL", "title": "Line 9 — applicable decimal (AGI tier, year-keyed)",
     "rule_type": "calculation", "precedence": 4, "sort_order": 4,
     "formula": ("f8880_decimal = SAVERS_AGI_TIERS[year][status_key(filing_status)] lookup by AGI (1040 line 11). "
                 "status: mfj / hoh / other(single,mfs,qss). 2025 verbatim; 2026 top cutoffs verified + interim "
                 "intermediate (D_8880_003)."),
     "inputs": [], "outputs": ["f8880_decimal"],
     "description": "Decision 5. AGI over the top -> 0.0 (no credit, D_8880_001 info)."},
    {"rule_id": "R-8880-CREDIT", "title": "Lines 10-12 — credit (tax-liability-limited) -> Schedule 3 line 4",
     "rule_type": "calculation", "precedence": 5, "sort_order": 5,
     "formula": "line10 = f8880_total_contributions * f8880_decimal; f8880_credit (line 12) = min(line10, credit_limit_worksheet) -> Schedule 3 line 4.",
     "inputs": [], "outputs": ["f8880_credit"],
     "description": "Decision 4. Nonrefundable: limited by tax (the pre-CTC CLW-A read). -> Sch 3 line 4 (already a direct-entry feeder)."},
]

F8880_LINES: list[dict] = [
    {"line_number": "1a", "description": "1 (You) Traditional + Roth IRA contributions", "line_type": "input"},
    {"line_number": "1b", "description": "1 (Spouse) Traditional + Roth IRA contributions", "line_type": "input"},
    {"line_number": "2a", "description": "2 (You) Elective deferrals (auto from W-2 box 12)", "line_type": "calculated"},
    {"line_number": "2b", "description": "2 (Spouse) Elective deferrals (auto from W-2 box 12)", "line_type": "calculated"},
    {"line_number": "3a", "description": "3 (You) Add lines 1 and 2", "line_type": "calculated"},
    {"line_number": "3b", "description": "3 (Spouse) Add lines 1 and 2", "line_type": "calculated"},
    {"line_number": "4a", "description": "4 (You) Distributions received (testing period)", "line_type": "input"},
    {"line_number": "4b", "description": "4 (Spouse) Distributions received (testing period)", "line_type": "input"},
    {"line_number": "5a", "description": "5 (You) Subtract line 4 from line 3 (not < 0)", "line_type": "calculated"},
    {"line_number": "5b", "description": "5 (Spouse) Subtract line 4 from line 3 (not < 0)", "line_type": "calculated"},
    {"line_number": "6a", "description": "6 (You) Smaller of line 5 or $2,000", "line_type": "calculated"},
    {"line_number": "6b", "description": "6 (Spouse) Smaller of line 5 or $2,000", "line_type": "calculated"},
    {"line_number": "7", "description": "7 Add the amounts on line 6 (max $4,000)", "line_type": "subtotal"},
    {"line_number": "8", "description": "8 Amount from Form 1040 line 11 (AGI; modified for 2555/4563/PR)", "line_type": "calculated"},
    {"line_number": "9", "description": "9 Applicable decimal from the table", "line_type": "calculated"},
    {"line_number": "10", "description": "10 Multiply line 7 by line 9", "line_type": "calculated"},
    {"line_number": "11", "description": "11 Limitation based on tax liability (Credit Limit Worksheet)", "line_type": "calculated"},
    {"line_number": "12", "description": "12 Saver's credit (smaller of line 10 or 11) -> Schedule 3 line 4", "line_type": "total"},
]

F8880_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_8880_001", "title": "AGI over the limit — no saver's credit", "severity": "info",
     "condition": "f8880_decimal == 0.0 (AGI over the top threshold for the filing status/year)",
     "message": ("Adjusted gross income exceeds the Saver's Credit limit for this filing status, so the applicable "
                 "decimal is zero and no credit is allowed (Form 8880 line 9)."),
     "notes": "The 'Caution' AGI cutoff; a 0% result, not an error."},
    {"diagnostic_id": "D_8880_002", "title": "Contributions by an ineligible person", "severity": "error",
     "condition": "a person with line-1/line-2 contributions is under 18 (born after Jan 1 of tax_year-17), a full-time student, or claimed as a dependent",
     "message": ("A person who made qualifying contributions is not eligible for the Saver's Credit (under 18, a "
                 "full-time student, or claimed as a dependent on another return). Their contributions are excluded "
                 "from the credit — verify the eligibility facts."),
     "notes": "Decision 2."},
    {"diagnostic_id": "D_8880_003", "title": "TY2026 intermediate AGI tiers are interim — re-pin when IRS publishes", "severity": "info",
     "condition": "tax_year == 2026 AND f8880_decimal in (0.5, 0.2) near a tier boundary",
     "message": ("The 2026 Saver's Credit top income limits are confirmed (MFJ $80,500 / HoH $60,375 / single-MFS "
                 "$40,250), but the intermediate 50%/20% breakpoints are carried from 2025 pending the 2026 Form "
                 "8880. Re-verify when the IRS releases the 2026 Form 8880 (~Dec 2026)."),
     "notes": "Spine derived-2026 interim precedent. Joins the Tax-Table/SDTW re-pin standing obligation."},
    {"diagnostic_id": "D_8880_004", "title": "Elective deferrals auto-derived from W-2 box 12 — verify", "severity": "info",
     "condition": "f8880_{you,spouse}_deferrals derived from W-2 box-12 entries",
     "message": ("Line 2 elective deferrals were summed automatically from the W-2 box-12 entries with qualifying "
                 "codes (D, E, F, G, H, S, AA, BB, EE), per W-2 owner. Verify against the W-2s; override on line 2 "
                 "if needed."),
     "notes": "Decision 1 transparency flag."},
    {"diagnostic_id": "D_8880_005", "title": "Form 2555 / 4563 / Puerto Rico exclusion — modified AGI not computed", "severity": "error",
     "condition": "files_form_2555 OR form_4563_excluded_income OR puerto_rico_excluded_income present",
     "message": ("Line 8 uses a MODIFIED AGI (adding back Form 2555/4563 and Puerto Rico exclusions), which this "
                 "software does not compute. Figure the modified AGI and the credit manually."),
     "notes": "Decision 6 RED-defer; the facts are already stored (0042 block)."},
    {"diagnostic_id": "D_8880_006", "title": "Testing-period distributions reduce the credit — verify the window", "severity": "info",
     "condition": "f8880_{you,spouse}_distributions > 0",
     "message": ("Distributions received reduce qualifying contributions (Form 8880 line 4). The testing period is "
                 "the current year, the two preceding years, and the period after year-end through the return due "
                 "date — include all such distributions; prior-year amounts are preparer-entered."),
     "notes": "Decision 3."},
]

F8880_SCENARIOS: list[dict] = [
    {"scenario_name": "8880-T1 — MFJ both at the 50% tier", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "f1040_agi": 40000,
                "f8880_you_ira": 2000, "f8880_spouse_ira": 2500},
     "expected_outputs": {"f8880_total_contributions": 4000, "f8880_decimal": 0.5, "f8880_credit": 2000},
     "notes": "Each capped at 2,000 -> line 7 4,000; AGI 40,000 <= 47,500 MFJ -> 0.5; credit 2,000 (the max)."},
    {"scenario_name": "8880-T2 — single 20% tier", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"tax_year": 2025, "filing_status": "single", "f1040_agi": 24000, "f8880_you_ira": 2000},
     "expected_outputs": {"f8880_total_contributions": 2000, "f8880_decimal": 0.2, "f8880_credit": 400},
     "notes": "23,750 < 24,000 <= 25,500 single -> 0.2; 2,000 x 0.2 = 400."},
    {"scenario_name": "8880-T3 — single 10%, IRA + box-12 deferrals, $2,000 cap", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"tax_year": 2025, "filing_status": "single", "f1040_agi": 30000,
                "f8880_you_ira": 1500, "box12_deferrals_you": 800},
     "expected_outputs": {"f8880_total_contributions": 2000, "f8880_decimal": 0.1, "f8880_credit": 200},
     "notes": "line3 = 1,500 + 800 = 2,300; line6 = min(2,300, 2,000) = 2,000; 25,500 < 30,000 <= 39,500 -> 0.1; 200."},
    {"scenario_name": "8880-T4 — distribution reduces contributions", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"tax_year": 2025, "filing_status": "single", "f1040_agi": 24000,
                "f8880_you_ira": 2000, "f8880_you_distributions": 500},
     "expected_outputs": {"f8880_total_contributions": 1500, "f8880_decimal": 0.2, "f8880_credit": 300},
     "notes": "line5 = max(0, 2,000 - 500) = 1,500; line6 = 1,500; 0.2 -> 300."},
    {"scenario_name": "8880-T5 — AGI over the limit (single)", "scenario_type": "edge_case", "sort_order": 5,
     "inputs": {"tax_year": 2025, "filing_status": "single", "f1040_agi": 45000, "f8880_you_ira": 2000},
     "expected_outputs": {"f8880_decimal": 0.0, "f8880_credit": 0, "D_8880_001": True},
     "notes": "45,000 > 39,500 single -> 0.0; no credit (D_8880_001)."},
    {"scenario_name": "8880-T6 — 2026 MFJ at the verified top cutoff", "scenario_type": "normal", "sort_order": 6,
     "inputs": {"tax_year": 2026, "filing_status": "mfj", "f1040_agi": 80000,
                "f8880_you_ira": 2000, "f8880_spouse_ira": 2000},
     "expected_outputs": {"f8880_total_contributions": 4000, "f8880_decimal": 0.1, "f8880_credit": 400, "D_8880_003": True},
     "notes": "2026 MFJ: 79,000 < 80,000 <= 80,500 -> 0.1 (the verified 2026 top cutoff); D_8880_003 interim flag."},
    {"scenario_name": "8880-G1 — full-time student excluded", "scenario_type": "diagnostic", "sort_order": 7,
     "inputs": {"tax_year": 2025, "filing_status": "single", "f1040_agi": 20000,
                "f8880_you_ira": 2000, "f8880_you_full_time_student": True},
     "expected_outputs": {"f8880_credit": 0, "D_8880_002": True},
     "notes": "A full-time student is ineligible -> contributions excluded, no credit (D_8880_002)."},
]

F8880_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-8880-ELIGIBILITY", "IRS_2025_F8880_FORM", "primary", "The Caution disqualifiers (18+, student, dependent)"),
    ("R-8880-LINE2-BOX12", "IRS_2025_F8880_FORM", "primary", "Line 2 elective deferrals (box-12 codes)"),
    ("R-8880-CONTRIB", "IRS_2025_F8880_FORM", "primary", "Lines 1-7: net contributions + the $2,000 cap"),
    ("R-8880-DECIMAL", "IRS_2025_F8880_FORM", "primary", "Line 9: the 2025 AGI tier table (verbatim)"),
    ("R-8880-DECIMAL", "IRS_2026_COLA_8880", "secondary", "2026 top cutoffs (interim intermediate breakpoints)"),
    ("R-8880-CREDIT", "IRS_2025_F8880_FORM", "primary", "Lines 10-12: credit, tax-liability cap -> Sch 3 line 4"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-8880-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Line 9 decimal == the AGI tier table (year-keyed by filing status)",
     "description": ("Validates R-8880-DECIMAL. Bug it catches: the wrong status column, or a stale/inflation-drifted "
                     "tier breakpoint."),
     "definition": {"kind": "constants_check", "form": "FORM_8880",
                    "constants": {"mfj_2025": [47500, 51000, 79000], "hoh_2025": [35625, 38250, 59250],
                                  "other_2025": [23750, 25500, 39500],
                                  "mfj_2026_top": 80500, "hoh_2026_top": 60375, "other_2026_top": 40250,
                                  "decimals": [0.5, 0.2, 0.1, 0.0]}},
     "sort_order": 1},
    {"assertion_id": "FA-1040-8880-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Per-person $2,000 cap: line 6 = min(line 5, 2000); line 7 = Σ line 6",
     "description": ("Validates R-8880-CONTRIB. Bug it catches: an uncapped contribution (8880-T3 caps 2,300 at "
                     "2,000), or the columns not summing."),
     "definition": {"kind": "formula_check", "form": "FORM_8880",
                    "formula": "line_6a == min(line_5a, 2000); line_6b == min(line_5b, 2000); line_7 == line_6a + line_6b"},
     "sort_order": 2},
    {"assertion_id": "FA-1040-8880-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Line 2 elective deferrals = Σ W-2 box-12 qualifying codes per owner",
     "description": ("Validates R-8880-LINE2-BOX12. Only codes D/E/F/G/H/S/AA/BB/EE count, attributed by W-2 owner. "
                     "Bug it catches: a non-qualifying code (DD/W/C) counted, or both spouses' W-2s pooled."),
     "definition": {"kind": "flow_assertion", "form": "FORM_8880",
                    "checks": [{"source": "W-2 box-12 qualifying codes (per owner)",
                                "must_write_to": ["FORM_8880.2a", "FORM_8880.2b"]}]},
     "sort_order": 3},
    {"assertion_id": "FA-1040-8880-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Credit = min(line 7 × line 9, tax cap) → Schedule 3 line 4 (nonrefundable)",
     "description": ("Validates R-8880-CREDIT. Bug it catches: a refundable overflow past the tax-liability limit, or "
                     "the result not landing on Schedule 3 line 4."),
     "definition": {"kind": "flow_assertion", "form": "FORM_8880",
                    "checks": [{"source_line": "12", "must_write_to": ["SCH_3.4"]}]},
     "sort_order": 4},
    {"assertion_id": "FA-1040-8880-05", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Eligibility gates exclude ineligible persons (no silent gap)",
     "description": ("Under-18 / full-time-student / claimed-as-dependent each exclude that person's contributions; "
                     "an ineligible contributor fires D_8880_002, AGI-over fires D_8880_001."),
     "definition": {"kind": "gating_check", "form": "FORM_8880", "expect": {"red_fires": True},
                    "blockers": ["under_18", "full_time_student", "claimed_dependent"]},
     "sort_order": 5},
]


FORMS: list[dict] = [
    {"identity": F8880_IDENTITY, "facts": F8880_FACTS, "rules": F8880_RULES, "lines": F8880_LINES,
     "diagnostics": F8880_DIAGNOSTICS, "scenarios": F8880_SCENARIOS, "rule_links": F8880_RULE_LINKS},
]


class Command(BaseCommand):
    help = "Load the FORM_8880 spec (Saver's Credit, roster #9). Refuses until READY_TO_SEED=True."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad FORM_8880 spec (Saver's Credit, roster #9)\n"))
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
                "\nREFUSING TO SEED FORM_8880: not cleared to seed.\n\n"
                "Gated until Ken's review walk (the 2025 verbatim tier table; the 2026 verified\n"
                "top cutoffs + interim intermediate breakpoints; the box-12 derive; the 6 scope\n"
                "decisions).\n\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True)\n\n"
                f"Currently empty / placeholder:\n  {still_empty}\n"
            )

    def _load_topics(self):
        ct = 0
        for code, name in AUTHORITY_TOPICS:
            _, created = AuthorityTopic.objects.update_or_create(topic_code=code, defaults={"topic_name": name})
            ct += 1 if created else 0
        self.stdout.write(f"Topics: {ct} new ({len(AUTHORITY_TOPICS)} in batch)")

    def _load_sources(self) -> dict:
        sources: dict = {}
        for src_data in AUTHORITY_SOURCES:
            src_data = dict(src_data)
            excerpts_data = src_data.pop("excerpts", [])
            topic_codes = src_data.pop("topics", [])
            source, _ = AuthoritySource.objects.update_or_create(
                source_code=src_data["source_code"], defaults=src_data)
            sources[source.source_code] = source
            for exc in excerpts_data:
                exc = dict(exc)
                AuthorityExcerpt.objects.update_or_create(
                    authority_source=source, excerpt_label=exc["excerpt_label"], defaults=exc)
            for tc in topic_codes:
                topic = AuthorityTopic.objects.filter(topic_code=tc).first()
                if topic:
                    AuthoritySourceTopic.objects.get_or_create(authority_source=source, authority_topic=topic)
        for code in EXISTING_SOURCES_TO_REFERENCE:
            src = AuthoritySource.objects.filter(source_code=code).first()
            if src:
                sources[code] = src
        self.stdout.write(f"Sources ready: {len(sources)}")
        return sources

    def _load_new_excerpts_on_existing(self, sources):
        for code, exc in NEW_EXCERPTS_ON_EXISTING:
            src = sources.get(code) or AuthoritySource.objects.filter(source_code=code).first()
            if src:
                exc = dict(exc)
                AuthorityExcerpt.objects.update_or_create(
                    authority_source=src, excerpt_label=exc["excerpt_label"], defaults=exc)

    def _upsert_form(self, identity: dict) -> TaxForm:
        form, created = TaxForm.objects.update_or_create(
            form_number=identity["form_number"], jurisdiction=FORM_JURISDICTION,
            tax_year=FORM_TAX_YEAR, version=FORM_VERSION,
            defaults={"form_title": identity["form_title"], "entity_types": FORM_ENTITY_TYPES,
                      "status": FORM_STATUS, "notes": identity["notes"]})
        self.stdout.write(f"{'Created' if created else 'Updated'} {identity['form_number']}")
        return form

    def _upsert_facts(self, form, facts):
        for f in facts:
            f = dict(f)
            FormFact.objects.update_or_create(tax_form=form, fact_key=f.pop("fact_key"), defaults=f)
        self.stdout.write(f"  {len(facts)} facts")

    def _upsert_rules(self, form, rules_data) -> dict:
        created = {}
        for r in rules_data:
            r = dict(r)
            rule, _ = FormRule.objects.update_or_create(tax_form=form, rule_id=r.pop("rule_id"), defaults=r)
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
                    defaults={"support_level": level, "relevance_note": note})
                ct += 1
        self.stdout.write(f"  {ct} authority links")

    def _upsert_lines(self, form, lines):
        for ln in lines:
            ln = dict(ln)
            FormLine.objects.update_or_create(tax_form=form, line_number=ln.pop("line_number"), defaults=ln)
        self.stdout.write(f"  {len(lines)} lines")

    def _upsert_diagnostics(self, form, diagnostics):
        for d in diagnostics:
            d = dict(d)
            FormDiagnostic.objects.update_or_create(tax_form=form, diagnostic_id=d.pop("diagnostic_id"), defaults=d)
        self.stdout.write(f"  {len(diagnostics)} diagnostics")

    def _upsert_tests(self, form, scenarios):
        for t in scenarios:
            t = dict(t)
            TestScenario.objects.update_or_create(tax_form=form, scenario_name=t.pop("scenario_name"), defaults=t)
        self.stdout.write(f"  {len(scenarios)} test scenarios")

    def _upsert_form_links(self, sources):
        for source_code, form_code, link_type in AUTHORITY_FORM_LINKS:
            source = sources.get(source_code) or AuthoritySource.objects.filter(source_code=source_code).first()
            if source:
                AuthorityFormLink.objects.get_or_create(
                    authority_source=source, form_code=form_code, link_type=link_type,
                    defaults={"note": f"{source_code} -> {form_code}"})

    def _load_flow_assertions(self):
        for a in FLOW_ASSERTIONS:
            a = dict(a)
            FlowAssertion.objects.update_or_create(assertion_id=a.pop("assertion_id"), defaults=a)
        self.stdout.write(f"  {len(FLOW_ASSERTIONS)} flow assertions")

    def _report_totals(self):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(f"TaxForms: {TaxForm.objects.count()} | FlowAssertions: {FlowAssertion.objects.count()}")
        form = TaxForm.objects.filter(form_number="FORM_8880").first()
        if form:
            uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
            self.stdout.write("FORM_8880: all rules cited" if not uncited
                              else self.style.WARNING(f"FORM_8880 uncited rules: {len(uncited)}"))
