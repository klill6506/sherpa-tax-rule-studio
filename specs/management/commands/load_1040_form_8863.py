"""Load the FORM_8863 spec — Education Credits (§25A): AOTC + LLC.

Post-sprint NEXT-UP #8. Reconciles the two §25A education credits:
  - American Opportunity Tax Credit (AOTC) — 40% refundable -> 1040 line 29.
  - Lifetime Learning Credit (LLC) — nonrefundable -> Schedule 3 line 3.
Part III is PER STUDENT (lines 20-31); Parts I & II aggregate.

KEN'S 4 SCOPE DECISIONS (2026-06-14, AskUserQuestion):
  (1) DEDICATED EducationStudent sub-model (built in the tts-tax-app seed leg —
      owner self/spouse/dependent; AOTC + LLC expenses; the 4 eligibility flags
      23-26; the line-7 lockout flag; full line-22 institution info).
  (2) Line-7 refundable kiddie-tax lockout = PREPARER CHECKBOX + diagnostic (v1
      does NOT auto-run the support test).
  (3) FULL Credit Limit Worksheet (line 19 capped at 1040 line 18 tax minus the
      earlier listed credits).
  (4) FULL Part III line 22 (2 institutions, address, EIN, both 1098-T Y/N).

CONSTANTS VERIFIED 2026-06-14 from the published 2025 f8863.pdf (9/23/25) /
i8863 / Pub 970 (brief tts-tax-app server/specs/_form_8863_source_brief.md).
ALL §25A figures are STATUTORY and NOT inflation-indexed (identical 2024/25/26):
  - AOTC: 100% of first $2,000 + 25% of next $2,000 -> max $2,500/student;
    adjusted-qualified-expense cap $4,000; refundable 40% (cap $1,000) -> 1040 L29.
  - LLC: 20% of up to $10,000 -> max $2,000 PER RETURN (not per student) -> Sch 3 L3.
  - Phaseout (BOTH credits, same): ceiling $90,000 (others) / $180,000 (MFJ);
    divisor $10,000 (others) / $20,000 (MFJ); ratio = (ceiling - MAGI) / divisor,
    capped 1.000, >= 3 decimals; <= 0 -> NO credit. (Floor where phaseout begins
    = $80,000 / $160,000.)
  - MAGI = AGI (1040 L11) + §911 foreign earned income / housing exclusion (Form
    2555) + §933 Puerto Rico + §931 American Samoa (Form 4563). Most filers: = AGI.
  - MFS barred from BOTH credits; a taxpayer claimed as a dependent is barred.
  - Line-7 lockout: whole AOTC becomes nonrefundable (L8 = 0, carry L7 -> L9).

Single form, the load_1040_form_8962 precedent.

TY2026: OBBBA §70606 adds a TIN/EIN-on-return requirement effective for tax years
beginning after 12/31/2025 (TY2026 only) — a deferred TY2026 diagnostic; it must
NOT gate/alter TY2025 compute. The AOTC/LLC computation itself is UNCHANGED 2026.
DISINFO (do NOT implement): "OBBBA AOTC 5 years" / "LLC max $3,000" — both FALSE.

SAFETY GUARD: READY_TO_SEED stays False until Ken's review walk (the §25A
constants + the phaseout + the Credit Limit Worksheet + the line-7 lockout).
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


READY_TO_SEED = True  # FLIPPED 2026-06-14 — Ken approved the review walk ("Looks good.").


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_ENTITY_TYPES = ["1040"]
FORM_STATUS = "draft"


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS (2025 f8863 / i8863 / Pub 970) — the integrity gate re-types.
# ALL §25A statutory; identical 2024/2025/2026.
# ═══════════════════════════════════════════════════════════════════════════

AOTC = {
    "tier1": 2000,         # 100% of the first $2,000
    "tier2": 2000,         # 25% of the next $2,000
    "tier2_rate": 0.25,
    "max": 2500,           # per student
    "expense_cap": 4000,   # line 27 adjusted-qualified-expense cap
    "refundable_rate": 0.40,
    "refundable_cap": 1000,
}
LLC = {
    "rate": 0.20,
    "expense_cap": 10000,  # line 11
    "max": 2000,           # per RETURN
}
# Phaseout (both credits): {key: (ceiling, divisor)}; "mfj" vs "other".
PHASEOUT = {
    "other": (90000, 10000),
    "mfj": (180000, 20000),
}


def _round0(x) -> int:
    """Whole-dollar round (the 8863 face is whole dollars)."""
    return int(round(x))


def aotc_student_l30(adjusted_expenses) -> int:
    """Part III lines 27-30 — the AOTC credit for ONE student (<= $2,500)."""
    l27 = min(adjusted_expenses, AOTC["expense_cap"])      # cap $4,000
    l28 = max(0, l27 - AOTC["tier1"])                       # over the first $2,000
    l29 = _round0(l28 * AOTC["tier2_rate"])                 # 25% of the next $2,000
    return l27 if l28 == 0 else l29 + AOTC["tier1"]         # line 30 (<= 2,500)


def phaseout_ratio(magi, filing_status) -> float:
    """Lines 6 / 17 — (ceiling - MAGI) / divisor, capped 1.000, >= 3 places.
    Returns 0.0 when MAGI is at/over the ceiling (no credit)."""
    ceiling, divisor = PHASEOUT["mfj" if (filing_status or "").lower() == "mfj" else "other"]
    diff = ceiling - magi
    if diff <= 0:
        return 0.0
    if diff >= divisor:
        return 1.0
    return round(diff / divisor, 3)


def aotc_part1(sum_l30, magi, filing_status, lockout=False) -> dict:
    """Part I lines 1-9 — refundable AOTC. Returns L4/L6/L7/L8(refundable)/L9(nonref)."""
    ceiling, _ = PHASEOUT["mfj" if (filing_status or "").lower() == "mfj" else "other"]
    l4 = ceiling - magi
    ratio = phaseout_ratio(magi, filing_status)             # line 6
    l7 = 0 if ratio <= 0 else _round0(sum_l30 * ratio)      # line 7
    if lockout:
        l8, l9 = 0, l7                                       # skip L8, carry L7 -> L9
    else:
        l8 = _round0(l7 * AOTC["refundable_rate"])          # line 8 -> 1040 L29
        l9 = l7 - l8                                         # line 9 (nonrefundable)
    return {"l4": l4, "l6": ratio, "l7": l7, "l8": l8, "l9": l9}


def llc_l18(llc_expenses, magi, filing_status) -> int:
    """Part II lines 10-18 — the nonrefundable Lifetime Learning Credit."""
    if llc_expenses <= 0:
        return 0
    l11 = min(llc_expenses, LLC["expense_cap"])             # cap $10,000
    l12 = _round0(l11 * LLC["rate"])                        # 20%
    ratio = phaseout_ratio(magi, filing_status)            # line 17
    return 0 if ratio <= 0 else _round0(l12 * ratio)       # line 18 (<= $2,000)


def credit_limit_l19(l18, l9_nonref_aotc, tax_1040_l18, prior_credits) -> int:
    """Credit Limit Worksheet (off-form) — line 19 = min(L18 + L9, tax available).
    tax available = 1040 line 18 minus the credits that come before education
    (Sch 3 lines 1-2 + 6c + 6g + 6l, per the 2025 i8863 worksheet)."""
    clw3 = l18 + l9_nonref_aotc
    clw6 = max(0, tax_1040_l18 - prior_credits)
    return min(clw3, clw6)


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("education_credits", "Education credits (§25A) — Form 8863; AOTC (40% refundable → 1040 L29) + LLC (→ Sch 3 L3)"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_1040_FORM",
    "IRS_2025_1040_INSTR",
]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_F8863_INSTR",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Form 8863 — Education Credits (AOTC and LLC)",
        "citation": "Instructions for Form 8863 (2025); i8863; Form 8863 Attachment Sequence No. 50",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i8863.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": ("The §25A line-by-line + the phaseout + the Credit Limit Worksheet + the line-7 refundable "
                  "lockout + the MFS bar. REQUIRES HUMAN REVIEW: confirm the exact line-7 kiddie-tax box "
                  "sentence + the Credit Limit Worksheet line-5 enumerated Schedule 3 credit lines vs the "
                  "2025 i8863."),
        "topics": ["education_credits"],
        "excerpts": [
            {
                "excerpt_label": "AOTC + LLC amounts (2025)",
                "location_reference": "i8863 (2025), Parts I/II/III",
                "excerpt_text": (
                    "American opportunity credit: 100% of the first $2,000 plus 25% of the next $2,000 of "
                    "adjusted qualified education expenses (line 27 not more than $4,000) for each student, up "
                    "to $2,500; 40% is refundable (up to $1,000) on Form 1040 line 29. Lifetime learning "
                    "credit: 20% of up to $10,000 of expenses (line 11), up to $2,000 per return regardless of "
                    "the number of students; nonrefundable, to Schedule 3 line 3."
                ),
                "summary_text": "AOTC max $2,500/student (40% refundable $1,000 → L29); LLC 20%×$10k = $2,000/return → Sch 3 L3.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Phaseout (lines 4-6 / 13-17)",
                "location_reference": "i8863 (2025), Parts I/II",
                "excerpt_text": (
                    "Line 2/13: enter $180,000 if married filing jointly, $90,000 if single, head of "
                    "household, or qualifying surviving spouse. Subtract MAGI (line 3/14) from it; if zero or "
                    "less, you cannot take the credit. Line 5/16: $20,000 if MFJ, $10,000 otherwise. Divide and "
                    "enter the result as a decimal rounded to at least three places; if line 4 (15) is equal to "
                    "or more than line 5 (16), enter 1.000."
                ),
                "summary_text": "Ceiling $90k/$180k MFJ; divisor $10k/$20k MFJ; ratio = (ceiling−MAGI)/divisor, cap 1.000; ≤0 → no credit.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Line 7 refundable lockout + the Credit Limit Worksheet",
                "location_reference": "i8863 (2025), line 7 + the Credit Limit Worksheet",
                "excerpt_text": (
                    "Line 7: if you were under age 24 at the end of the year and meet the conditions described "
                    "in the instructions (the kiddie-tax conditions of §1(g)), you cannot take the refundable "
                    "American opportunity credit; check the box, skip line 8, and enter the amount from line 7 "
                    "on line 9. Credit Limit Worksheet: line 19 is the smaller of (line 18 + line 9) or your tax "
                    "liability after the credits that come before the education credit (Schedule 3 lines 1-2, "
                    "6c, 6g, 6l)."
                ),
                "summary_text": "Line-7 lockout: whole AOTC nonrefundable (L8=0, L7→L9). CLW: L19 = min(L18+L9, tax − earlier credits).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Who cannot claim a credit (MFS / dependent)",
                "location_reference": "i8863 (2025), 'Who Can't Claim the Credit'",
                "excerpt_text": (
                    "You cannot claim an education credit if your filing status is married filing separately, "
                    "if you are claimed as a dependent on another person's return, or (for the AOTC) if you do "
                    "not have a valid taxpayer identification number by the due date of the return."
                ),
                "summary_text": "MFS and dependents barred from both credits.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_25A",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §25A — Hope and Lifetime Learning Credits (the education credits)",
        "citation": "26 U.S.C. §25A (§25A(b) AOTC; §25A(c) LLC; §25A(d) phaseout; §25A(i) the refundable AOTC + the line-7 lockout)",
        "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:25A%20edition:prelim)",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": ("The substantive §25A authority: §25A(b)(1) the 100%/25% AOTC; §25A(c)(1) the 20% LLC; "
                  "§25A(d) the MAGI phaseout; §25A(i)(5) the 40% refundable portion; §25A(i)(6) the line-7 "
                  "kiddie-tax lockout (cross-references §1(g))."),
        "topics": ["education_credits"],
        "excerpts": [
            {
                "excerpt_label": "§25A(b)/(c)/(d) AOTC + LLC + phaseout",
                "location_reference": "26 U.S.C. §25A(b)(1), (c)(1), (d)",
                "excerpt_text": (
                    "§25A(b)(1): the American Opportunity Credit = 100% of so much of the qualified tuition and "
                    "related expenses as does not exceed $2,000, plus 25% of such expenses in excess of $2,000 "
                    "(but not more than $4,000). §25A(c)(1): the Lifetime Learning Credit = 20% of so much of "
                    "the qualified expenses as does not exceed $10,000. §25A(d): the credit phases out ratably "
                    "over a $10,000 ($20,000 joint) modified-AGI range."
                ),
                "summary_text": "§25A(b) AOTC 100%/25% to $4,000; (c) LLC 20% to $10,000; (d) the $10k/$20k phaseout range.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§25A(i) refundable AOTC + the line-7 lockout",
                "location_reference": "26 U.S.C. §25A(i)(5), (i)(6)",
                "excerpt_text": (
                    "§25A(i)(5): 40% of the American Opportunity Credit is treated as a refundable credit. "
                    "§25A(i)(6): the refundable portion does not apply to a taxpayer to whom the §1(g) "
                    "kiddie-tax rules apply (a child under 24 with the support/parent/joint-return conditions); "
                    "the entire credit is then nonrefundable."
                ),
                "summary_text": "§25A(i)(5): 40% refundable. (i)(6): the §1(g) kiddie-tax child loses the refundable portion.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_PUB_970",
        "source_type": "official_guidance",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRS Publication 970 — Tax Benefits for Education (chapters 2-3: AOTC + LLC)",
        "citation": "Pub. 970 (2025) — American Opportunity Credit (ch. 2) and Lifetime Learning Credit (ch. 3)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/p970.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": False,
        "trust_score": 9.00,
        "requires_human_review": True,
        "notes": ("The adjusted-qualified-expense rules (tax-free assistance reduces expenses), the eligibility "
                  "tests (first-4-years / half-time / degree-seeking / no felony drug conviction), and the MAGI "
                  "definition. REQUIRES HUMAN REVIEW: confirm the MAGI worksheet rows + the adjusted-expense "
                  "reductions vs Pub 970."),
        "topics": ["education_credits"],
        "excerpts": [
            {
                "excerpt_label": "MAGI for the education credits",
                "location_reference": "Pub. 970 (2025), ch. 2/3 'Modified adjusted gross income'",
                "excerpt_text": (
                    "For most taxpayers, MAGI is AGI as figured on the federal income tax return. MAGI for the "
                    "education credits = AGI + foreign earned income exclusion + foreign housing exclusion or "
                    "deduction + income excluded by bona fide residents of Puerto Rico or American Samoa."
                ),
                "summary_text": "MAGI = AGI + §911 foreign earned income/housing + §933 Puerto Rico + §931 American Samoa.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "AOTC eligibility + adjusted qualified expenses",
                "location_reference": "Pub. 970 (2025), ch. 2",
                "excerpt_text": (
                    "To claim the AOTC for a student: had not completed the first 4 years of postsecondary "
                    "education before the year, has not claimed the AOTC for more than 4 tax years, was enrolled "
                    "at least half-time in a program leading to a degree or credential, and has no felony drug "
                    "conviction. Reduce qualified expenses by tax-free scholarships, grants, and assistance to "
                    "get the adjusted qualified expenses. A student cannot take both the AOTC and the LLC."
                ),
                "summary_text": "AOTC eligibility (first-4-years / ≤4 claims / half-time / degree / no felony); adjusted expenses; AOTC XOR LLC per student.",
                "is_key_excerpt": True,
            },
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_F8863_INSTR", "FORM_8863", "governs"),
    ("IRC_25A", "FORM_8863", "governs"),
    ("IRS_PUB_970", "FORM_8863", "informs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM: FORM_8863
# ═══════════════════════════════════════════════════════════════════════════

F8863_IDENTITY = {
    "form_number": "FORM_8863",
    "form_title": "Form 8863 — Education Credits (AOTC and LLC) (TY2025)",
    "notes": (
        "Ken's 4 scope decisions 2026-06-14 (post-sprint NEXT-UP #8). Real IRS "
        "face. Part III is PER STUDENT (lines 20-31, on the dedicated "
        "EducationStudent model); Parts I & II aggregate. AOTC: per-student L30 "
        "(100% of first $2,000 + 25% of next $2,000, expense cap $4,000, max "
        "$2,500) -> L1 -> phaseout L6 -> L7 -> L8 = 40% refundable (1040 L29) / "
        "L9 = nonrefundable. LLC: ΣL31 -> L11 (cap $10,000) -> 20% L12 -> phaseout "
        "L17 -> L18 (max $2,000). L19 = the Credit Limit Worksheet min(L18 + L9, "
        "tax − earlier credits) -> Schedule 3 line 3. Phaseout (both): ceiling "
        "$90k/$180k MFJ, divisor $10k/$20k MFJ. MFS + dependents barred. Line-7 "
        "kiddie-tax lockout = a preparer checkbox (whole AOTC nonrefundable). "
        "TY2026 compute unchanged; OBBBA §70606 TIN/EIN = a TY2026 diagnostic."
    ),
}

F8863_FACTS: list[dict] = [
    # ── Return-level input (the per-student data rides the EducationStudent model) ──
    {"fact_key": "f8863_lockout_any", "label": "Any student subject to the line-7 refundable lockout?",
     "data_type": "boolean", "default_value": "false", "sort_order": 1,
     "notes": "Decision 2. Per-student on the model; aggregated here. Checked → the whole AOTC is nonrefundable (L8=0, L7→L9)."},
    # ── Outputs ──
    {"fact_key": "f8863_magi", "label": "Line 3/14 — modified AGI",
     "data_type": "decimal", "sort_order": 20, "notes": "OUTPUT. AGI + §911/931/933 add-backs (= AGI for most filers)."},
    {"fact_key": "f8863_total_aotc", "label": "Line 7 — tentative AOTC (after phaseout)",
     "data_type": "decimal", "sort_order": 21, "notes": "OUTPUT. ΣL30 × the phaseout ratio L6."},
    {"fact_key": "f8863_aotc_refundable", "label": "Line 8 — refundable AOTC → 1040 line 29",
     "data_type": "decimal", "sort_order": 22, "notes": "OUTPUT. 40% × L7 (0 when the line-7 lockout applies)."},
    {"fact_key": "f8863_aotc_nonref", "label": "Line 9 — nonrefundable AOTC",
     "data_type": "decimal", "sort_order": 23, "notes": "OUTPUT. L7 − L8 (= L7 under the lockout) → the Credit Limit Worksheet."},
    {"fact_key": "f8863_llc", "label": "Line 18 — Lifetime Learning Credit",
     "data_type": "decimal", "sort_order": 24, "notes": "OUTPUT. 20% × min(ΣL31, $10,000) × the phaseout ratio L17 (max $2,000)."},
    {"fact_key": "f8863_education_credit", "label": "Line 19 — nonrefundable education credit → Schedule 3 line 3",
     "data_type": "decimal", "sort_order": 25, "notes": "OUTPUT. the Credit Limit Worksheet = min(L18 + L9, tax − earlier credits)."},
]

F8863_RULES: list[dict] = [
    {"rule_id": "R-8863-MAGI", "title": "Lines 3/14 — modified AGI", "rule_type": "calculation",
     "precedence": 1, "sort_order": 1,
     "formula": ("MAGI = AGI (1040 line 11) + the foreign earned income exclusion / housing (Form 2555) + "
                 "§933 Puerto Rico + §931 American Samoa (Form 4563). = AGI for most filers."),
     "inputs": [], "outputs": ["f8863_magi"],
     "description": "§25A(d)(3). The same MAGI feeds both Part I (line 3) and Part II (line 14)."},
    {"rule_id": "R-8863-STUDENT-AOTC", "title": "Lines 27-30 — per-student AOTC (≤ $2,500)", "rule_type": "calculation",
     "precedence": 2, "sort_order": 2,
     "formula": ("Per student: L27 = min(adjusted qualified expenses, $4,000); L28 = max(0, L27 − $2,000); "
                 "L29 = round(L28 × 25%); L30 = L27 if L28 = 0 else L29 + $2,000 (≤ $2,500). L1 = Σ L30."),
     "inputs": [], "outputs": [],
     "description": "§25A(b)(1). Per student on the EducationStudent model (decision 1); aggregated to Part I line 1."},
    {"rule_id": "R-8863-AOTC-PHASEOUT", "title": "Lines 1-9 — refundable AOTC + phaseout", "rule_type": "calculation",
     "precedence": 3, "sort_order": 3,
     "formula": ("L2 = ceiling ($180k MFJ / $90k others); L3 = MAGI; L4 = L2 − L3 (≤ 0 → no credit); L5 = "
                 "divisor ($20k MFJ / $10k others); L6 = 1.000 if L4 ≥ L5 else round(L4/L5, 3); L7 = "
                 "round(L1 × L6); L8 = round(L7 × 40%) → 1040 L29; L9 = L7 − L8. If the line-7 lockout is "
                 "checked: L8 = 0 and L9 = L7 (whole AOTC nonrefundable)."),
     "inputs": ["f8863_lockout_any"], "outputs": ["f8863_total_aotc", "f8863_aotc_refundable", "f8863_aotc_nonref"],
     "description": "§25A(d), (i)(5)-(6). The refundable 40% + the kiddie-tax lockout (decision 2)."},
    {"rule_id": "R-8863-LLC", "title": "Lines 10-18 — Lifetime Learning Credit", "rule_type": "calculation",
     "precedence": 4, "sort_order": 4,
     "formula": ("L10 = Σ student LLC adjusted expenses; L11 = min(L10, $10,000); L12 = round(L11 × 20%); "
                 "L13 = ceiling; L14 = MAGI; L15 = L13 − L14 (≤ 0 → L18 = 0); L16 = divisor; L17 = 1.000 if "
                 "L15 ≥ L16 else round(L15/L16, 3); L18 = round(L12 × L17) (max $2,000 per return)."),
     "inputs": [], "outputs": ["f8863_llc"],
     "description": "§25A(c)(1), (d). 20% of up to $10,000, $2,000 max per RETURN (not per student)."},
    {"rule_id": "R-8863-CREDIT-LIMIT", "title": "Line 19 — Credit Limit Worksheet → Schedule 3 line 3", "rule_type": "calculation",
     "precedence": 5, "sort_order": 5,
     "formula": ("Credit Limit Worksheet: CLW1 = L18; CLW2 = L9; CLW3 = CLW1 + CLW2; CLW4 = 1040 line 18 "
                 "(tax); CLW5 = the credits before education (Schedule 3 lines 1-2 + 6c + 6g + 6l); CLW6 = "
                 "max(0, CLW4 − CLW5); CLW7 = min(CLW3, CLW6) → L19 → Schedule 3 line 3."),
     "inputs": [], "outputs": ["f8863_education_credit"],
     "description": "Decision 3. The full off-form Credit Limit Worksheet caps the nonrefundable credit at tax."},
    {"rule_id": "R-8863-MFS-BAR", "title": "MFS / dependent — no education credit", "rule_type": "routing",
     "precedence": 6, "sort_order": 6,
     "formula": ("If filing_status == MFS OR the taxpayer is claimed as a dependent on another return → no "
                 "education credit (L8/L19 = 0); D_8863_MFS / D_8863_DEPENDENT."),
     "inputs": [], "outputs": [],
     "description": "§25A(g)(2), (g)(6). MFS + dependents barred from both credits."},
    {"rule_id": "R-8863-2026-SSN", "title": "TY2026 — OBBBA §70606 TIN/EIN requirement (deferred)", "rule_type": "routing",
     "precedence": 7, "sort_order": 7,
     "formula": ("tax_year == 2026 AND a required TIN (taxpayer/student) or institution EIN is missing → "
                 "D_8863_TY2026_SSN. Computation UNCHANGED 2026; the requirement is identification-only."),
     "inputs": [], "outputs": [],
     "description": "OBBBA §70606 (effective TY2026). Must NOT gate/alter TY2025 compute."},
]

F8863_LINES: list[dict] = [
    # ── Part I — Refundable AOTC ──
    {"line_number": "1", "description": "1 Total AOTC from all Part III line 30 (Σ)", "line_type": "calculated"},
    {"line_number": "2", "description": "2 $180,000 (MFJ) or $90,000 (others)", "line_type": "calculated"},
    {"line_number": "3", "description": "3 Modified AGI", "line_type": "calculated"},
    {"line_number": "4", "description": "4 Line 2 − line 3 (if zero or less, no credit)", "line_type": "calculated"},
    {"line_number": "5", "description": "5 $20,000 (MFJ) or $10,000 (others)", "line_type": "calculated"},
    {"line_number": "6", "description": "6 Line 4 ÷ line 5 (decimal ≥ 3 places; 1.000 if line 4 ≥ line 5)", "line_type": "calculated"},
    {"line_number": "7", "description": "7 Line 1 × line 6 (tentative AOTC)", "line_type": "calculated"},
    {"line_number": "8", "description": "8 Refundable AOTC = line 7 × 40% → Form 1040 line 29", "line_type": "total"},
    # ── Part II — Nonrefundable credits ──
    {"line_number": "9", "description": "9 Line 7 − line 8 (nonrefundable AOTC)", "line_type": "calculated"},
    {"line_number": "10", "description": "10 Total LLC expenses from all Part III line 31 (Σ)", "line_type": "calculated"},
    {"line_number": "11", "description": "11 Smaller of line 10 or $10,000", "line_type": "calculated"},
    {"line_number": "12", "description": "12 Line 11 × 20%", "line_type": "calculated"},
    {"line_number": "13", "description": "13 $180,000 (MFJ) or $90,000 (others)", "line_type": "calculated"},
    {"line_number": "14", "description": "14 Modified AGI", "line_type": "calculated"},
    {"line_number": "15", "description": "15 Line 13 − line 14 (if zero or less, line 18 = 0)", "line_type": "calculated"},
    {"line_number": "16", "description": "16 $20,000 (MFJ) or $10,000 (others)", "line_type": "calculated"},
    {"line_number": "17", "description": "17 Line 15 ÷ line 16 (decimal ≥ 3 places; 1.000 if line 15 ≥ line 16)", "line_type": "calculated"},
    {"line_number": "18", "description": "18 Line 12 × line 17 (LLC, max $2,000)", "line_type": "calculated"},
    {"line_number": "19", "description": "19 Nonrefundable education credits (Credit Limit Worksheet) → Schedule 3 line 3", "line_type": "total"},
    # ── Part III — per student (the template; one copy per EducationStudent) ──
    {"line_number": "20", "description": "20 Student name", "line_type": "input"},
    {"line_number": "21", "description": "21 Student SSN", "line_type": "input"},
    {"line_number": "22a", "description": "22a Institution 1 — name/address, 1098-T (2025 Y/N), 1098-T 2024 box 7 (Y/N), EIN", "line_type": "input"},
    {"line_number": "22b", "description": "22b Institution 2 — name/address, 1098-T (2025 Y/N), 1098-T 2024 box 7 (Y/N), EIN", "line_type": "input"},
    {"line_number": "23", "description": "23 AOTC claimed in any 4 prior years? (Yes → line 31, LLC only)", "line_type": "input"},
    {"line_number": "24", "description": "24 Enrolled at least half-time? (No → line 31)", "line_type": "input"},
    {"line_number": "25", "description": "25 Completed first 4 years before 2025? (Yes → line 31)", "line_type": "input"},
    {"line_number": "26", "description": "26 Felony drug conviction by year-end? (Yes → line 31)", "line_type": "input"},
    {"line_number": "27", "description": "27 AOTC adjusted qualified expenses (cap $4,000)", "line_type": "input"},
    {"line_number": "28", "description": "28 Line 27 − $2,000 (if zero or less, 0)", "line_type": "calculated"},
    {"line_number": "29", "description": "29 Line 28 × 25%", "line_type": "calculated"},
    {"line_number": "30", "description": "30 If line 28 = 0 → line 27, else line 29 + $2,000 → Part I line 1", "line_type": "calculated"},
    {"line_number": "31", "description": "31 LLC adjusted qualified expenses → Part II line 10", "line_type": "input"},
]

F8863_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_8863_MFS", "title": "MFS cannot claim an education credit", "severity": "error",
     "condition": "filing_status == MFS AND any student/expense entered",
     "message": ("Married filing separately cannot claim the American Opportunity or Lifetime Learning credit "
                 "(IRC §25A(g)(6)). No education credit is computed — remove the entries or change the filing "
                 "status."),
     "notes": "§25A(g)(6). Hard bar."},
    {"diagnostic_id": "D_8863_DEPENDENT", "title": "A dependent cannot claim an education credit", "severity": "error",
     "condition": "taxpayer is claimed as a dependent on another return AND any student/expense entered",
     "message": ("A taxpayer who is claimed as a dependent on another person's return cannot claim an education "
                 "credit (the credit belongs to the person who claims the exemption). No credit is computed."),
     "notes": "§25A(g)(3)."},
    {"diagnostic_id": "D_8863_DUAL_STUDENT", "title": "Same student — AOTC and LLC both entered", "severity": "warning",
     "condition": "a student has both line-27 (AOTC) and line-31 (LLC) expenses",
     "message": ("A student cannot take both the American Opportunity and the Lifetime Learning credit in the "
                 "same year. Enter the expenses under one credit only (lines 27-30 OR line 31) for this "
                 "student."),
     "notes": "Pub 970. Per-student AOTC XOR LLC."},
    {"diagnostic_id": "D_8863_NO_CREDIT", "title": "MAGI over the ceiling — no education credit", "severity": "info",
     "condition": "MAGI >= ceiling ($90k single / $180k MFJ) AND expenses entered",
     "message": ("Modified AGI is at or above the phaseout ceiling ($90,000 single / $180,000 MFJ), so no "
                 "education credit is allowed this year (line 4 / line 15 is zero or less)."),
     "notes": "§25A(d). The full phaseout."},
    {"diagnostic_id": "D_8863_LOCKOUT", "title": "Line 7 refundable lockout applied", "severity": "info",
     "condition": "f8863_lockout_any is True",
     "message": ("A student is marked subject to the line-7 kiddie-tax rule, so the entire American Opportunity "
                 "credit is nonrefundable (line 8 = 0; line 7 carries to line 9). v1 does not auto-run the "
                 "support test — verify the §1(g) conditions."),
     "notes": "Decision 2. §25A(i)(6)."},
    {"diagnostic_id": "D_8863_AOTC_INELIG", "title": "Student fails an AOTC test → Lifetime Learning only", "severity": "warning",
     "condition": "line 23/24/25/26 routes the student off the AOTC",
     "message": ("This student does not qualify for the American Opportunity credit (4 prior years claimed, not "
                 "at least half-time, first 4 years already completed, or a felony drug conviction). Only the "
                 "Lifetime Learning credit (line 31) is available for the student."),
     "notes": "Pub 970 ch. 2. The Part III routing 23-26."},
    {"diagnostic_id": "D_8863_TY2026_SSN", "title": "TY2026 — OBBBA TIN/EIN requirement (deferred)", "severity": "warning",
     "condition": "tax_year == 2026 AND a required taxpayer/student TIN or institution EIN is missing",
     "message": ("For 2026, OBBBA §70606 requires the taxpayer's SSN, the student's name/SSN, and the "
                 "institution's EIN on the return to claim an education credit. The credit computation is "
                 "unchanged — supply the identifiers. (TY2025 is not affected.)"),
     "notes": "OBBBA §70606, effective TY2026. Identification-only; does not change compute."},
]

F8863_SCENARIOS: list[dict] = [
    {"scenario_name": "8863-T1 — AOTC full, no phaseout (single)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "filing_status": "single", "magi": 50000, "aotc_students": [4000]},
     "expected_outputs": {"f8863_total_aotc": 2500, "f8863_aotc_refundable": 1000, "f8863_aotc_nonref": 1500,
                          "f8863_llc": 0, "f8863_education_credit": 1500},
     "notes": "One student $4,000 → L30 2,500; MAGI 50k < 80k → ratio 1.000; L7 2,500; L8 40% = 1,000 → 1040 L29; L9 1,500 → Sch 3 L3."},
    {"scenario_name": "8863-T2 — AOTC in phaseout (single, MAGI 85k)", "scenario_type": "edge_case", "sort_order": 2,
     "inputs": {"tax_year": 2025, "filing_status": "single", "magi": 85000, "aotc_students": [4000]},
     "expected_outputs": {"f8863_total_aotc": 1250, "f8863_aotc_refundable": 500, "f8863_aotc_nonref": 750,
                          "f8863_llc": 0, "f8863_education_credit": 750},
     "notes": "ratio = (90,000−85,000)/10,000 = 0.500; L7 = 2,500 × 0.5 = 1,250; L8 = 500; L9 = 750."},
    {"scenario_name": "8863-T3 — LLC only (single, MAGI 60k)", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"tax_year": 2025, "filing_status": "single", "magi": 60000, "llc_expenses": 8000},
     "expected_outputs": {"f8863_total_aotc": 0, "f8863_aotc_refundable": 0, "f8863_llc": 1600,
                          "f8863_education_credit": 1600},
     "notes": "L11 = 8,000; L12 = 20% = 1,600; ratio 1.000 (60k < 80k); L18 = 1,600 → Sch 3 L3. No refundable."},
    {"scenario_name": "8863-T4 — LLC capped at $2,000 (single)", "scenario_type": "edge_case", "sort_order": 4,
     "inputs": {"tax_year": 2025, "filing_status": "single", "magi": 50000, "llc_expenses": 12000},
     "expected_outputs": {"f8863_llc": 2000, "f8863_education_credit": 2000},
     "notes": "L11 = min(12,000, 10,000) = 10,000; L12 = 2,000; ratio 1.000; L18 = 2,000 (the per-return cap)."},
    {"scenario_name": "8863-T5 — LLC phaseout (MFJ, MAGI 170k)", "scenario_type": "edge_case", "sort_order": 5,
     "inputs": {"tax_year": 2025, "filing_status": "mfj", "magi": 170000, "llc_expenses": 10000},
     "expected_outputs": {"f8863_llc": 1000, "f8863_education_credit": 1000},
     "notes": "L12 = 2,000; ratio = (180,000−170,000)/20,000 = 0.500; L18 = 1,000."},
    {"scenario_name": "8863-T6 — line-7 refundable lockout (single)", "scenario_type": "edge_case", "sort_order": 6,
     "inputs": {"tax_year": 2025, "filing_status": "single", "magi": 40000, "aotc_students": [4000], "lockout": True},
     "expected_outputs": {"f8863_total_aotc": 2500, "f8863_aotc_refundable": 0, "f8863_aotc_nonref": 2500,
                          "f8863_education_credit": 2500},
     "notes": "Lockout: L7 2,500; L8 = 0 (skip); L9 = L7 = 2,500 — the whole AOTC is nonrefundable."},
    {"scenario_name": "8863-T7 — MAGI over the ceiling, no credit (single)", "scenario_type": "edge_case", "sort_order": 7,
     "inputs": {"tax_year": 2025, "filing_status": "single", "magi": 95000, "aotc_students": [4000]},
     "expected_outputs": {"f8863_total_aotc": 0, "f8863_aotc_refundable": 0, "f8863_aotc_nonref": 0,
                          "f8863_llc": 0, "f8863_education_credit": 0},
     "notes": "L4 = 90,000 − 95,000 = −5,000 ≤ 0 → ratio 0 → no credit."},
    {"scenario_name": "8863-T8 — Credit Limit Worksheet binds (low tax)", "scenario_type": "edge_case", "sort_order": 8,
     "inputs": {"tax_year": 2025, "filing_status": "single", "magi": 50000, "aotc_students": [4000],
                "tax": 800, "prior_credits": 0},
     "expected_outputs": {"f8863_aotc_refundable": 1000, "f8863_aotc_nonref": 1500, "f8863_education_credit": 800},
     "notes": "Refundable 1,000 still flows to 1040 L29; the nonrefundable L9 1,500 is capped by the CLW at tax 800 → L19 = 800."},
    {"scenario_name": "8863-G1 — MFS barred → RED", "scenario_type": "diagnostic", "sort_order": 9,
     "inputs": {"tax_year": 2025, "filing_status": "mfs", "magi": 50000, "aotc_students": [4000]},
     "expected_outputs": {"D_8863_MFS": True},
     "notes": "MFS cannot claim either credit (§25A(g)(6)) → D_8863_MFS RED."},
]

F8863_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-8863-MAGI", "IRS_PUB_970", "primary", "The education-credit MAGI add-backs"),
    ("R-8863-MAGI", "IRC_25A", "secondary", "§25A(d)(3) modified AGI"),
    ("R-8863-STUDENT-AOTC", "IRC_25A", "primary", "§25A(b)(1) the 100%/25% per-student AOTC"),
    ("R-8863-STUDENT-AOTC", "IRS_2025_F8863_INSTR", "secondary", "Part III lines 27-30"),
    ("R-8863-AOTC-PHASEOUT", "IRC_25A", "primary", "§25A(d) phaseout + §25A(i)(5)-(6) refundable/lockout"),
    ("R-8863-AOTC-PHASEOUT", "IRS_2025_F8863_INSTR", "secondary", "Part I lines 1-9"),
    ("R-8863-LLC", "IRC_25A", "primary", "§25A(c)(1) the 20% LLC + §25A(d) phaseout"),
    ("R-8863-LLC", "IRS_2025_F8863_INSTR", "secondary", "Part II lines 10-18"),
    ("R-8863-CREDIT-LIMIT", "IRS_2025_F8863_INSTR", "primary", "The Credit Limit Worksheet → Sch 3 line 3"),
    ("R-8863-MFS-BAR", "IRS_2025_F8863_INSTR", "primary", "Who can't claim a credit (MFS / dependent)"),
    ("R-8863-MFS-BAR", "IRC_25A", "secondary", "§25A(g)(6) MFS bar"),
    ("R-8863-2026-SSN", "IRS_2025_F8863_INSTR", "secondary", "OBBBA §70606 TIN/EIN (TY2026)"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-8863-01", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "The §25A constants (AOTC / LLC / phaseout)",
     "description": "Pins the AOTC $2,000/$2,000/$2,500/$4,000 + 40%/$1,000, the LLC 20%/$10,000/$2,000, and the $90k/$180k ceiling + $10k/$20k divisor. Bug it catches: a drifted amount or the wrong year's table (none, but guards future edits).",
     "definition": {"kind": "constants_check", "form": "FORM_8863",
                    "constants": {"aotc_tier1": 2000, "aotc_max": 2500, "aotc_expense_cap": 4000,
                                  "aotc_refundable_rate": 0.40, "aotc_refundable_cap": 1000,
                                  "llc_rate": 0.20, "llc_expense_cap": 10000, "llc_max": 2000,
                                  "ceiling_other": 90000, "ceiling_mfj": 180000,
                                  "divisor_other": 10000, "divisor_mfj": 20000}},
     "sort_order": 1},
    {"assertion_id": "FA-1040-8863-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Per-student AOTC = 100% first $2,000 + 25% next $2,000 (≤ $2,500)",
     "description": "Validates R-8863-STUDENT-AOTC. Bug it catches: the $4,000 expense cap not applied, the $2,000 floor wrong, or the 25% mis-tiered ($4,000 → $2,500; $3,000 → $2,250; $1,500 → $1,500).",
     "definition": {"kind": "formula_check", "form": "FORM_8863",
                    "formula": "L30 == (L27 if L28==0 else round((min(exp,4000)-2000)*0.25)+2000); L27=min(exp,4000)"},
     "sort_order": 2},
    {"assertion_id": "FA-1040-8863-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Phaseout ratio = (ceiling − MAGI) / divisor, capped 1.000",
     "description": "Validates R-8863-AOTC-PHASEOUT + R-8863-LLC (the shared phaseout). Bug it catches: the ratio not capped at 1.000, not floored at 0 (MAGI ≥ ceiling), or the MFJ divisor swapped (85k single → 0.500; 170k MFJ → 0.500; 95k single → 0).",
     "definition": {"kind": "formula_check", "form": "FORM_8863",
                    "formula": "ratio == clamp((ceiling-magi)/divisor, 0, 1) rounded 3"},
     "sort_order": 3},
    {"assertion_id": "FA-1040-8863-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Refundable AOTC → 1040 line 29; nonrefundable education credit → Sch 3 line 3",
     "description": "Validates R-8863-AOTC-PHASEOUT + R-8863-CREDIT-LIMIT. Bug it catches: the 40% refundable not landing on 1040 line 29, or line 19 not landing on Schedule 3 line 3.",
     "definition": {"kind": "flow_assertion", "form": "FORM_8863",
                    "checks": [{"source_line": "8", "must_write_to": ["1040.29"]},
                               {"source_line": "19", "must_write_to": ["SCH_3.3"]}]},
     "sort_order": 4},
    {"assertion_id": "FA-1040-8863-05", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "Credit Limit Worksheet — line 19 = min(L18 + L9, tax − earlier credits)",
     "description": "Validates R-8863-CREDIT-LIMIT. Bug it catches: the nonrefundable education credit not capped at tax liability (low-tax returns over-credited).",
     "definition": {"kind": "reconciliation", "form": "FORM_8863",
                    "formula": "L19 == min(L18 + L9, max(0, tax_1040_L18 - prior_credits))"},
     "sort_order": 5},
    {"assertion_id": "FA-1040-8863-06", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Gates: line-7 lockout (whole AOTC nonrefundable); MFS barred",
     "description": "The line-7 lockout zeroes the refundable AOTC (L8=0, L7→L9, D_8863_LOCKOUT); MFS fires D_8863_MFS and computes no credit.",
     "definition": {"kind": "gating_check", "form": "FORM_8863", "expect": {"red_fires": True},
                    "blockers": ["filing_status_mfs"]},
     "sort_order": 6},
]


FORMS: list[dict] = [
    {"identity": F8863_IDENTITY, "facts": F8863_FACTS, "rules": F8863_RULES, "lines": F8863_LINES,
     "diagnostics": F8863_DIAGNOSTICS, "scenarios": F8863_SCENARIOS, "rule_links": F8863_RULE_LINKS},
]


class Command(BaseCommand):
    help = "Load the FORM_8863 spec (Education Credits). Refuses until READY_TO_SEED=True."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad FORM_8863 spec (Education Credits)\n"))
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
                "\nREFUSING TO SEED FORM_8863: not cleared to seed.\n\n"
                "Gated until Ken's review walk (the §25A constants + the phaseout +\n"
                "the Credit Limit Worksheet + the line-7 lockout).\n\n"
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
        form = TaxForm.objects.filter(form_number="FORM_8863").first()
        if form:
            uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
            self.stdout.write("FORM_8863: all rules cited" if not uncited
                              else self.style.WARNING(f"FORM_8863 uncited rules: {len(uncited)}"))
