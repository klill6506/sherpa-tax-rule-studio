"""Load TY 2025 CTC/ACTC spec — first 1040 form spec in Rule Studio.

Session 14 (2026-05-26): Authors the full Child Tax Credit / Additional Child Tax Credit
spec for Form 1040 and Schedule 8812, with OBBBA P.L. 119-21 §70104 amendments.

Creates:
  - 6 new authority topics
  - 5 new authority sources + excerpts:
      IRC_24, IRC_152, PL_119_21_70104, IRS_2025_8812_FORM, IRS_2025_8812_INSTR
  - 2 new excerpts on the existing IRS_2025_1040_INSTR source
  - 2 new TaxForm records:
      1040  (stub — only Line 11 / Line 19 / Line 28 modeled)
      SCH_8812 (full — all 27 lines, ~30 facts, 30 rules, 12 diagnostics, 17 tests)
  - 13 FlowAssertion records (FA-1040-CTC-01 through 12 + TI-1040-CTC-A)

Idempotent: uses update_or_create throughout. Safe to re-run.
"""
from django.core.management.base import BaseCommand
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
# Topics — created if missing
# ═══════════════════════════════════════════════════════════════════════════

NEW_TOPICS = [
    ("child_tax_credit", "Child Tax Credit"),
    ("additional_child_tax_credit", "Additional Child Tax Credit"),
    ("credit_for_other_dependents", "Credit for Other Dependents"),
    ("qualifying_child", "Qualifying Child (§152(c))"),
    ("schedule_8812", "Schedule 8812"),
    ("obbba", "One Big Beautiful Bill Act (P.L. 119-21)"),
]


# ═══════════════════════════════════════════════════════════════════════════
# New authority sources with excerpts
# ═══════════════════════════════════════════════════════════════════════════

FRESH_SOURCES = [
    # ───── IRC §24 — Child Tax Credit ─────
    {
        "source_code": "IRC_24",
        "source_type": "code_section",
        "source_rank": "controlling",
        "jurisdiction_code": "FED",
        "title": "IRC §24 — Child Tax Credit and Credit for Other Dependents",
        "citation": "26 U.S.C. §24",
        "issuer": "Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/24",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 10.00,
        "requires_human_review": True,
        "notes": (
            "Consolidated text post-OBBBA (P.L. 119-21 §70104, eff. TY 2025+). "
            "§24(h) and §24(i) overrides take precedence over base §24(a)(b)(d) for 2018+."
        ),
        "topics": ["child_tax_credit", "credits", "qualifying_child"],
        "excerpts": [
            {
                "excerpt_label": "§24(a) — General allowance",
                "location_reference": "26 U.S.C. §24(a)",
                "excerpt_text": (
                    "There shall be allowed as a credit against the tax imposed by this chapter "
                    "for the taxable year with respect to each qualifying child of the taxpayer "
                    "for which the taxpayer is allowed a deduction under section 151 an amount equal to $1,000."
                ),
                "summary_text": "Base statutory amount $1,000; superseded by §24(h)(2) for 2018+.",
                "is_key_excerpt": False,
            },
            {
                "excerpt_label": "§24(b)(1) — Phaseout formula",
                "location_reference": "26 U.S.C. §24(b)(1)",
                "excerpt_text": (
                    "The amount of the credit allowable under subsection (a) shall be reduced "
                    "(but not below zero) by $50 for each $1,000 (or fraction thereof) by which "
                    "the taxpayer's modified adjusted gross income exceeds the threshold amount."
                ),
                "summary_text": "$50 per $1,000 of MAGI over threshold; round UP for partial $1,000.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§24(b)(2) vs §24(h)(3) — Threshold override",
                "location_reference": "26 U.S.C. §24(b)(2), §24(h)(3)",
                "excerpt_text": (
                    "Base §24(b)(2) thresholds are $110,000 (MFJ) / $75,000 (single) / $55,000 (MFS). "
                    "For tax years beginning after 2017, §24(h)(3) OVERRIDES with: '$400,000 in the case "
                    "of a joint return ($200,000 in any other case).' OBBBA §70104(a)(1) removed the "
                    "§24(h)(1) sunset, making this override permanent."
                ),
                "summary_text": "Operational thresholds for TY 2025: $400K MFJ / $200K all other (per §24(h)(3), made permanent by OBBBA).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§24(c) — Qualifying child definition",
                "location_reference": "26 U.S.C. §24(c)(1)",
                "excerpt_text": (
                    "The term 'qualifying child' means a qualifying child of the taxpayer "
                    "(as defined in section 152(c)) who has not attained age 17."
                ),
                "summary_text": "§24(c) under-17 age modifier overrides §152(c)(3)'s general age tests.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§24(d) vs §24(h)(6) — Refundable formula and floor",
                "location_reference": "26 U.S.C. §24(d), §24(h)(6)",
                "excerpt_text": (
                    "§24(d)(1)(B)(i) provides the refundable portion equals 15% of earned income "
                    "in excess of $3,000. §24(h)(6) OVERRIDES the $3,000 figure to $2,500 for tax years "
                    "beginning after 2017. OBBBA §70104(a)(1) made this override permanent."
                ),
                "summary_text": "Operational earned-income floor for TY 2025: $2,500 (per §24(h)(6)). 15% rate above floor.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§24(h)(2) — Per-child credit amount $2,200 (OBBBA-amended)",
                "location_reference": "26 U.S.C. §24(h)(2) (as amended by P.L. 119-21 §70104(a)(2))",
                "excerpt_text": (
                    "(2) CREDIT AMOUNT.—Subsection (a) shall be applied by substituting '$2,200' for '$1,000'."
                ),
                "summary_text": "Per-child CTC amount $2,200, eff. TY 2025+ per OBBBA §70104(a)(2).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§24(h)(4)(A) — Credit for Other Dependents ($500)",
                "location_reference": "26 U.S.C. §24(h)(4)(A)",
                "excerpt_text": (
                    "Subsection (a) shall be applied by substituting '$500' for '$1,000' ... with respect "
                    "to any dependent of the taxpayer (as defined in section 152) other than a qualifying child "
                    "described in subsection (c)."
                ),
                "summary_text": "$500 ODC per non-QC dependent. Not amended by OBBBA.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§24(h)(5) + §24(i)(1) — ACTC base $1,400 indexed to $1,700 for 2025",
                "location_reference": "26 U.S.C. §24(h)(5), §24(i)(1)",
                "excerpt_text": (
                    "MAXIMUM AMOUNT OF REFUNDABLE CREDIT.—The amount determined under subsection (d)(1)(A) "
                    "with respect to any qualifying child shall not exceed $1,400. Per §24(i)(1) as amended "
                    "by OBBBA §70104(c), this $1,400 is COLA-adjusted starting 2025 (base year 2017), "
                    "rounded down to nearest $100. TY 2025 indexed value = $1,700."
                ),
                "summary_text": "ACTC per-child refundable cap for TY 2025: $1,700 (= $1,400 base indexed to 2025 dollars).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§24(h)(7) — SSN requirement (NEW TY 2025 per OBBBA)",
                "location_reference": "26 U.S.C. §24(h)(7) (as amended by P.L. 119-21 §70104(b))",
                "excerpt_text": (
                    "No credit shall be allowed under this section to a taxpayer with respect to any "
                    "qualifying child unless the taxpayer includes on the return of tax for the taxable year— "
                    "(i) the taxpayer's social security number (or, in the case of a joint return, the social "
                    "security number of at least 1 spouse), and (ii) the social security number of such "
                    "qualifying child."
                ),
                "summary_text": "New for TY 2025: taxpayer SSN required (MFJ: at least one spouse). Child SSN required.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ───── IRC §152 — Dependent Defined ─────
    {
        "source_code": "IRC_152",
        "source_type": "code_section",
        "source_rank": "controlling",
        "jurisdiction_code": "FED",
        "title": "IRC §152 — Dependent Defined",
        "citation": "26 U.S.C. §152",
        "issuer": "Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/152",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 10.00,
        "requires_human_review": True,
        "notes": (
            "Defines 'qualifying child' and 'qualifying relative' — both used by §24(c) (CTC) and "
            "§24(h)(4) (ODC). §24(c)'s 'under 17' overrides §152(c)(3)'s general age rule."
        ),
        "topics": ["qualifying_child", "credit_for_other_dependents"],
        "excerpts": [
            {
                "excerpt_label": "§152(a) — Dependent defined",
                "location_reference": "26 U.S.C. §152(a)",
                "excerpt_text": (
                    "For purposes of this subtitle, the term 'dependent' means— "
                    "(1) a qualifying child, or (2) a qualifying relative."
                ),
                "summary_text": "Dependent = qualifying child OR qualifying relative.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§152(b)(3) — Citizenship/residency requirement",
                "location_reference": "26 U.S.C. §152(b)(3)(A)",
                "excerpt_text": (
                    "The term 'dependent' does not include an individual who is not a citizen or national "
                    "of the United States unless such individual is a resident of the United States or a "
                    "country contiguous to the United States."
                ),
                "summary_text": "Dependents must be US citizen, US national, or US resident alien (or resident of Canada/Mexico).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§152(c)(1) — Five qualifying-child tests",
                "location_reference": "26 U.S.C. §152(c)(1)",
                "excerpt_text": (
                    "The term 'qualifying child' means ... an individual— "
                    "(A) who bears a relationship to the taxpayer described in paragraph (2), "
                    "(B) who has the same principal place of abode as the taxpayer for more than one-half "
                    "of such taxable year, "
                    "(C) who meets the age requirements of paragraph (3), "
                    "(D) who has not provided over one-half of such individual's own support for the "
                    "calendar year ..., and "
                    "(E) who has not filed a joint return ... with the individual's spouse under section 6013 "
                    "for the taxable year ...."
                ),
                "summary_text": "Five tests: relationship, residency (>½ year), age, support, joint return.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§152(c)(2) — Relationship test",
                "location_reference": "26 U.S.C. §152(c)(2)",
                "excerpt_text": (
                    "For purposes of paragraph (1)(A), an individual bears a relationship to the taxpayer "
                    "described in this paragraph if such individual is— "
                    "(A) a child of the taxpayer or a descendant of such a child, or "
                    "(B) a brother, sister, stepbrother, or stepsister of the taxpayer or a descendant of "
                    "any such relative."
                ),
                "summary_text": "Relationship: child/descendant OR sibling/descendant. §152(f)(1)(B) extends 'child' to adopted, foster, step.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§152(c)(4) — Tie-breaker rules for multiple claimants",
                "location_reference": "26 U.S.C. §152(c)(4)",
                "excerpt_text": (
                    "If multiple taxpayers may claim the same qualifying child, the child is treated as the "
                    "qualifying child of: (i) a parent if any parent could claim, or (ii) the taxpayer with "
                    "the highest adjusted gross income. For two parents not filing jointly: (i) parent with "
                    "longest residency, then (ii) higher-AGI parent. A non-parent claimant must have AGI "
                    "higher than any parent's."
                ),
                "summary_text": "Tie-breaker order: parent > non-parent; between two parents, longer residency then higher AGI.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ───── Public Law 119-21 §70104 (OBBBA) ─────
    {
        "source_code": "PL_119_21_70104",
        "source_type": "code_section",
        "source_rank": "controlling",
        "jurisdiction_code": "FED",
        "title": (
            "Public Law 119-21 §70104 — Extension and Enhancement of Increased Child Tax Credit "
            "(One Big Beautiful Bill Act)"
        ),
        "citation": "P.L. 119-21 §70104; 139 Stat. 160-161",
        "issuer": "Congress",
        "official_url": "https://www.congress.gov/119/plaws/publ21/PLAW-119publ21.pdf",
        "publication_date": "2025-07-04",
        "effective_date_start": "2025-01-01",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "Signed July 4, 2025; retroactive to start of TY 2025. Amends IRC §24(h) and §24(i).",
        "topics": ["obbba", "child_tax_credit"],
        "excerpts": [
            {
                "excerpt_label": "§70104(a)(1) — Permanent expansion of §24(h)",
                "location_reference": "P.L. 119-21 §70104(a)(1); 139 Stat. 160",
                "excerpt_text": (
                    "Section 24(h) is amended— (1) in paragraph (1), by striking ', and before January 1, 2026',"
                ),
                "summary_text": "Removes sunset on §24(h); makes the expanded CTC structure permanent.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§70104(a)(2) — Credit amount $2,200",
                "location_reference": "P.L. 119-21 §70104(a)(2); 139 Stat. 160",
                "excerpt_text": (
                    "Section 24(h) is amended— (2) in paragraph (2), by striking '$2,000' and inserting '$2,200',"
                ),
                "summary_text": "Per-qualifying-child credit amount raised from $2,000 to $2,200, eff. TY 2025+.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§70104(b) — Taxpayer SSN requirement (new §24(h)(7))",
                "location_reference": "P.L. 119-21 §70104(b); 139 Stat. 160",
                "excerpt_text": (
                    "Section 24(h)(7) is amended to read as follows: '(7) SOCIAL SECURITY NUMBER REQUIRED.— "
                    "(A) IN GENERAL.—No credit shall be allowed under this section to a taxpayer with respect "
                    "to any qualifying child unless the taxpayer includes on the return of tax for the taxable "
                    "year— (i) the taxpayer's social security number (or, in the case of a joint return, the "
                    "social security number of at least 1 spouse), and (ii) the social security number of such "
                    "qualifying child. (B) SOCIAL SECURITY NUMBER.—For purposes of this paragraph, the term "
                    "'social security number' means a social security number issued to an individual by the "
                    "Social Security Administration, but only if the social security number is issued— "
                    "(i) to a citizen of the United States or pursuant to subclause (I) (or that portion of "
                    "subclause (III) that relates to subclause (I)) of section 205(c)(2)(B)(i) of the Social "
                    "Security Act, and (ii) before the due date for such return.'"
                ),
                "summary_text": "New SSN requirement for taxpayer (MFJ: at least one spouse) AND qualifying child. Work-authorized SSN, issued before due date.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§70104(c) — Inflation adjustments to §24(i)",
                "location_reference": "P.L. 119-21 §70104(c); 139 Stat. 160-161",
                "excerpt_text": (
                    "Section 24(i) is amended to read as follows: '(i) INFLATION ADJUSTMENTS.— "
                    "(1) MAXIMUM AMOUNT OF REFUNDABLE CREDIT.—In the case of a taxable year beginning "
                    "after 2024, the $1,400 amount in subsection (h)(5) shall be increased by [COLA, base "
                    "year 2017]. "
                    "(2) SPECIAL RULE FOR ADJUSTMENT OF CREDIT AMOUNT.—In the case of a taxable year beginning "
                    "after 2025, the $2,200 amount in subsection (h)(2) shall be increased by [COLA, base year "
                    "2024]. "
                    "(3) ROUNDING.—If any increase under this subsection is not a multiple of $100, such "
                    "increase shall be rounded to the next lowest multiple of $100.'"
                ),
                "summary_text": "Refundable cap $1,400 indexed for 2025+ (→ $1,700 in 2025). Credit amount $2,200 indexed for 2026+.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§70104(f) — Effective date",
                "location_reference": "P.L. 119-21 §70104(f); 139 Stat. 161",
                "excerpt_text": (
                    "The amendments made by this section shall apply to taxable years beginning "
                    "after December 31, 2024."
                ),
                "summary_text": "All §70104 amendments effective for TY 2025+. Retroactive to start of 2025 despite July 4, 2025 signing.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ───── 2025 Schedule 8812 (Form) ─────
    {
        "source_code": "IRS_2025_8812_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Schedule 8812 (Form 1040) — Credits for Qualifying Children and Other Dependents",
        "citation": "Schedule 8812 (Form 1040) (2025); Cat. No. 59761M",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f1040s8.pdf",
        "publication_date": "2025-07-30",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": "The form establishes the canonical line numbering and labels used throughout the spec.",
        "topics": ["child_tax_credit", "schedule_8812"],
        "excerpts": [
            {
                "excerpt_label": "Part I — Lines 1-3 MAGI assembly",
                "location_reference": "Sch 8812 (2025), Part I lines 1-3",
                "excerpt_text": (
                    "1 Enter the amount from line 11a of your Form 1040, 1040-SR, or 1040-NR. "
                    "2a Enter income from Puerto Rico that you excluded. "
                    "2b Enter the amounts from lines 45 and 50 of your Form 2555. "
                    "2c Enter the amount from line 15 of your Form 4563. "
                    "2d Add lines 2a through 2c. "
                    "3 Add lines 1 and 2d."
                ),
                "summary_text": "Line 3 = MAGI = AGI + (PR excluded + Form 2555 lines 45+50 + Form 4563 line 15).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part I — Lines 4-8 pre-phaseout credit",
                "location_reference": "Sch 8812 (2025), Part I lines 4-8",
                "excerpt_text": (
                    "4 Number of qualifying children under age 17 with the required social security number. "
                    "5 Multiply line 4 by $2,200. "
                    "6 Number of other dependents, including any qualifying children who are not under age 17 "
                    "or who do not have the required social security number. "
                    "Caution: Do not include yourself, your spouse, or anyone who is not a U.S. citizen, "
                    "U.S. national, or U.S. resident alien. Also, do not include anyone you included on line 4. "
                    "7 Multiply line 6 by $500. "
                    "8 Add lines 5 and 7."
                ),
                "summary_text": "Lines 4-8: QC count × $2,200 + ODC count × $500 = pre-phaseout combined credit.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part I — Lines 9-11 phaseout with ceil-rounding",
                "location_reference": "Sch 8812 (2025), Part I lines 9-11",
                "excerpt_text": (
                    "9 Enter the amount shown below for your filing status. Married filing jointly—$400,000; "
                    "All other filing statuses—$200,000. "
                    "10 Subtract line 9 from line 3. If zero or less, enter -0-. If more than zero and not a "
                    "multiple of $1,000, enter the next multiple of $1,000. For example, if the result is $425, "
                    "enter $1,000; if the result is $1,025, enter $2,000, etc. "
                    "11 Multiply line 10 by 5% (0.05)."
                ),
                "summary_text": "Threshold $400K MFJ / $200K all other; excess rounded UP to next $1,000; reduction = 5% × Line 10.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part I — Lines 12-14 nonrefundable cap; Form 1040 Line 19 destination",
                "location_reference": "Sch 8812 (2025), Part I lines 12-14",
                "excerpt_text": (
                    "12 Is the amount on line 8 more than the amount on line 11? "
                    "No. Stop here. You cannot take the child tax credit, credit for other dependents, or "
                    "additional child tax credit. "
                    "Yes. Subtract line 11 from line 8. Enter the result. "
                    "13 Enter the amount from Credit Limit Worksheet A. "
                    "14 Enter the smaller of line 12 or line 13. This is your child tax credit and credit for "
                    "other dependents. Enter this amount on Form 1040, 1040-SR, or 1040-NR, line 19."
                ),
                "summary_text": "Line 14 = min(Line 12, Line 13) → Form 1040 Line 19. STOP if Line 8 ≤ Line 11.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part II-A — Lines 15-20 ACTC base computation",
                "location_reference": "Sch 8812 (2025), Part II-A lines 15-20",
                "excerpt_text": (
                    "Caution: If you file Form 2555, you cannot claim the additional child tax credit. "
                    "15 Reserved for future use. "
                    "16a Subtract line 14 from line 12. "
                    "16b Number of qualifying children under age 17 with the required social security number: "
                    "× $1,700. "
                    "17 Enter the smaller of line 16a or line 16b. "
                    "18a Earned income (see instructions). "
                    "18b Nontaxable combat pay. "
                    "19 Is the amount on line 18a more than $2,500? Yes. Subtract $2,500 from the amount on "
                    "line 18a. "
                    "20 Multiply the amount on line 19 by 15% (0.15)."
                ),
                "summary_text": "ACTC base: per-child cap $1,700; earned-income floor $2,500; 15% method. Form 2555 disqualifies.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part II-B + II-C — Lines 21-27 alternate path and ACTC destination",
                "location_reference": "Sch 8812 (2025), Part II-B lines 21-26, Part II-C line 27",
                "excerpt_text": (
                    "21 Withheld social security, Medicare, and Additional Medicare taxes from Form(s) W-2, "
                    "boxes 4 and 6. "
                    "22 Schedule 1 line 15 + Schedule 2 lines 5, 6, and 13. "
                    "23 Add lines 21 and 22. "
                    "24 Form 1040/1040-SR line 27a + Schedule 3 line 11. "
                    "25 Subtract line 24 from line 23. If zero or less, enter -0-. "
                    "26 Enter the larger of line 20 or line 25. "
                    "27 This is your additional child tax credit. Enter this amount on Form 1040, 1040-SR, or "
                    "1040-NR, line 28."
                ),
                "summary_text": "Part II-B (3+ QC alternate path): payroll-tax floor for ACTC. Line 27 → Form 1040 Line 28.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ───── 2025 Schedule 8812 Instructions ─────
    {
        "source_code": "IRS_2025_8812_INSTR",
        "source_type": "official_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": (
            "2025 Instructions for Schedule 8812 (Form 1040) — Credits for Qualifying Children "
            "and Other Dependents"
        ),
        "citation": "Instructions for Schedule 8812 (Form 1040) (2025); Cat. No. 59790P",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i1040s8.pdf",
        "publication_date": "2026-01-23",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": (
            "Reflects OBBBA TY 2025 implementation. Includes 7/26/26 update notice "
            "(heading change 'by' → 'before' the due date)."
        ),
        "topics": ["child_tax_credit", "schedule_8812", "additional_child_tax_credit"],
        "excerpts": [
            {
                "excerpt_label": "E1 — What's New: CTC amount $2,200",
                "location_reference": "2025 Sch 8812 Instructions, 'What's New'",
                "excerpt_text": (
                    "CTC amount increased. The maximum amount of CTC for each qualifying child increased to $2,200."
                ),
                "summary_text": "Per-QC CTC = $2,200 (TY 2025).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "E2 — Reminders: ACTC amount $1,700",
                "location_reference": "2025 Sch 8812 Instructions, 'Reminders'",
                "excerpt_text": "ACTC amount. The maximum amount of ACTC for each qualifying child is $1,700.",
                "summary_text": "Per-QC ACTC refundable cap = $1,700 (TY 2025).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "E3 — What's New: Taxpayer SSN requirement",
                "location_reference": "2025 Sch 8812 Instructions, 'What's New'",
                "excerpt_text": (
                    "Social security number (SSN) required to claim the child tax credit (CTC) and additional "
                    "child tax credit (ACTC). Beginning in tax year 2025, you must have a valid SSN to claim "
                    "the CTC or ACTC. If you are filing a joint return, only one filer must have a valid SSN. "
                    "The other filer must have either an SSN or an individual taxpayer identification number "
                    "(ITIN), and it must have been issued on or before the due date of your return."
                ),
                "summary_text": "TY 2025+: taxpayer needs valid SSN. MFJ: only one spouse SSN required (other needs SSN or ITIN).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "E4 — Valid SSN definition",
                "location_reference": "2025 Sch 8812 Instructions, 'SSN Required Before the Due Date'",
                "excerpt_text": (
                    "Valid SSN. For the CTC and ACTC, a valid SSN is one that is valid for employment and "
                    "that is issued by the Social Security Administration before the due date of your 2025 "
                    "return (including extensions)."
                ),
                "summary_text": "Valid SSN = work-authorized, issued by extended due date.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "E5 — Qualifying child basic conditions",
                "location_reference": "2025 Sch 8812 Instructions, 'Credits for Qualifying Children'",
                "excerpt_text": (
                    "To claim a child for the CTC and ACTC, the child must be your dependent, under age 17 "
                    "at the end of 2025, and meet all the conditions in Steps 1 through 3 under Who Qualifies "
                    "as Your Dependent in the Instructions for Form 1040."
                ),
                "summary_text": "CTC/ACTC: child must be dependent, under 17, meet 1040 Steps 1-3 (i.e., §152(c)).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "E6 — ODC eligibility conditions",
                "location_reference": "2025 Sch 8812 Instructions, 'Credit for Other Dependents (ODC)'",
                "excerpt_text": (
                    "The ODC is for individuals with a dependent who meets the following conditions. "
                    "1. The person is claimed as a dependent on your return. "
                    "2. The person can't be used by you to claim the CTC or ACTC. "
                    "3. The person was a U.S. citizen, U.S. national, or U.S. resident alien. "
                    "4. The person has an SSN, ITIN, or ATIN issued on or before the due date of your return "
                    "(including extensions)."
                ),
                "summary_text": "ODC: dependent, NOT a QC for CTC, US cit/nat/res-alien, has SSN/ITIN/ATIN by due date.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "E7 — Modified AGI definition",
                "location_reference": "2025 Sch 8812 Instructions, 'Limits on the CTC and ODC'",
                "excerpt_text": (
                    "Modified AGI. For purposes of the CTC and ODC, your modified AGI is the amount on line 3 "
                    "of Schedule 8812."
                ),
                "summary_text": "MAGI = Sch 8812 Line 3 = AGI + PR excluded + Form 2555 lines 45+50 + Form 4563 line 15.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "E8 — Phaseout threshold structure",
                "location_reference": "2025 Sch 8812 Instructions, 'Limits on the CTC and ODC'",
                "excerpt_text": (
                    "The maximum credit amount of your CTC and ODC may be reduced if ... your modified "
                    "adjusted gross income (AGI) is more than the amount shown below for your filing status. "
                    "Married filing jointly–$400,000; All other filing statuses–$200,000."
                ),
                "summary_text": "Phaseout: $400K MFJ / $200K all other (Single, HOH, MFS, QSS).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "E9 — Form 2555 disqualifies ACTC",
                "location_reference": "2025 Sch 8812 Instructions, 'Part II-A — Additional Child Tax Credit for All Filers'",
                "excerpt_text": (
                    "If you file Form 2555, you cannot claim the additional child tax credit."
                ),
                "summary_text": "Form 2555 filers: no ACTC. CTC + ODC still available (with MAGI add-back).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "E10 — Earned income definition (Line 18a)",
                "location_reference": "2025 Sch 8812 Instructions, Earned Income Worksheet",
                "excerpt_text": (
                    "Earned income = wages (Form 1040 line 1z) + nontaxable combat pay (elected, Line 18b) "
                    "+ statutory employee income + Schedule C net profit + Schedule K-1 (1065) box 14 code A "
                    "(other than farming) + Schedule F net farm profit + elected Medicaid waiver payments; "
                    "minus ½ SE tax deduction (Schedule 1 line 15). Income excluded under a tax treaty is "
                    "also excluded from earned income on line 18a. For bona fide PR residents: do not include "
                    "income earned in Puerto Rico."
                ),
                "summary_text": "EI = wages + combat pay (elected) + statutory + Sch C/F/K-1 — ½ SE tax. Excl: tax-treaty, PR.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "E11 — Improper-claim penalty",
                "location_reference": "2025 Sch 8812 Instructions, 'Improper Claims'",
                "excerpt_text": (
                    "If you erroneously claim the CTC, ACTC, or ODC and it is later determined that your "
                    "error was due to reckless or intentional disregard of the CTC, ACTC, or ODC rules, you "
                    "will not be allowed to claim any of these credits for 2 years even if you are otherwise "
                    "eligible to do so. If it is determined that your error was due to fraud, you will not be "
                    "allowed to claim any of these credits for 10 years."
                ),
                "summary_text": "Reckless disregard: 2-year bar. Fraud: 10-year bar. Form 8862 required after prior disallowance.",
                "is_key_excerpt": False,
            },
            {
                "excerpt_label": "E12 — STOP language for taxpayer-SSN failure",
                "location_reference": "2025 Sch 8812 Instructions, 'SSN Required Before the Due Date of Your Return To Claim the CTC and ACTC'",
                "excerpt_text": (
                    "If you, and your spouse if filing jointly, do not have a valid SSN, you can't claim the "
                    "CTC or ACTC on either your original or an amended 2025 return."
                ),
                "summary_text": "Verbatim STOP language for return-level taxpayer-SSN disqualifier.",
                "is_key_excerpt": True,
            },
        ],
    },
]


# Excerpts to ADD to the existing IRS_2025_1040_INSTR source
NEW_EXCERPTS_FOR_EXISTING_1040_INSTR = [
    {
        "excerpt_label": "Line 19 — CTC/ODC nonrefundable",
        "location_reference": "2025 Form 1040 Instructions, Line 19",
        "excerpt_text": (
            "Line 19. Child tax credit and credit for other dependents. To claim the credit, see the "
            "Instructions for Schedule 8812. Enter on line 19 the amount from Schedule 8812, line 14."
        ),
        "summary_text": "Form 1040 Line 19 = Schedule 8812 Line 14.",
        "is_key_excerpt": True,
    },
    {
        "excerpt_label": "Line 28 — ACTC refundable",
        "location_reference": "2025 Form 1040 Instructions, Line 28",
        "excerpt_text": (
            "Line 28. Additional child tax credit. Use Schedule 8812 to figure the credit. Enter on line 28 "
            "the amount from Schedule 8812, line 27."
        ),
        "summary_text": "Form 1040 Line 28 = Schedule 8812 Line 27.",
        "is_key_excerpt": True,
    },
]


EXISTING_SOURCES = ["IRS_2025_1040_INSTR"]


# ═══════════════════════════════════════════════════════════════════════════
# Command
# ═══════════════════════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = "Load TY 2025 CTC/ACTC spec (Session 14 — first 1040 form spec)."

    @transaction.atomic
    def handle(self, *args, **opts):
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad 1040 CTC/ACTC spec\n"))

        self._load_topics()
        sources = self._load_sources()
        self._load_new_excerpts_on_existing(sources)
        self._load_form_1040_stub(sources)
        self._load_form_sch_8812(sources)
        self._load_flow_assertions()
        self._report_totals()

    # ─────────────────────────────────────────────────────────────────────────
    # Topics
    # ─────────────────────────────────────────────────────────────────────────

    def _load_topics(self):
        ct = 0
        for code, name in NEW_TOPICS:
            _, created = AuthorityTopic.objects.update_or_create(
                topic_code=code, defaults={"topic_name": name},
            )
            if created:
                ct += 1
        self.stdout.write(f"Topics: {ct} new ({len(NEW_TOPICS)} total in batch)")

    # ─────────────────────────────────────────────────────────────────────────
    # Sources
    # ─────────────────────────────────────────────────────────────────────────

    def _load_sources(self) -> dict[str, AuthoritySource]:
        sources: dict[str, AuthoritySource] = {}
        for src_data in FRESH_SOURCES:
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
        for code in EXISTING_SOURCES:
            src = AuthoritySource.objects.filter(source_code=code).first()
            if src:
                sources[code] = src
        self.stdout.write(f"Sources ready: {len(sources)}")
        return sources

    def _load_new_excerpts_on_existing(self, sources):
        instr_1040 = sources.get("IRS_2025_1040_INSTR")
        if not instr_1040:
            self.stdout.write(self.style.WARNING(
                "IRS_2025_1040_INSTR not found — cannot add Line 19/28 excerpts"))
            return
        for exc in NEW_EXCERPTS_FOR_EXISTING_1040_INSTR:
            exc = dict(exc)
            AuthorityExcerpt.objects.update_or_create(
                authority_source=instr_1040, excerpt_label=exc["excerpt_label"], defaults=exc,
            )
        self.stdout.write(f"  {len(NEW_EXCERPTS_FOR_EXISTING_1040_INSTR)} new excerpts on IRS_2025_1040_INSTR")

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers (identical pattern to load_1120s_complete.py)
    # ─────────────────────────────────────────────────────────────────────────

    def _upsert_form(self, form_number, form_title, entity_types, jurisdiction="FED", notes="") -> TaxForm:
        form, created = TaxForm.objects.update_or_create(
            form_number=form_number, jurisdiction=jurisdiction, tax_year=2025, version=1,
            defaults={"form_title": form_title, "entity_types": entity_types,
                       "status": "draft", "notes": notes},
        )
        self.stdout.write(f"{'Created' if created else 'Updated'} {form_number}")
        return form

    def _upsert_facts(self, form, facts_data):
        for f in facts_data:
            f = dict(f)
            FormFact.objects.update_or_create(tax_form=form, fact_key=f.pop("fact_key"), defaults=f)
        self.stdout.write(f"  {len(facts_data)} facts")

    def _upsert_rules(self, form, rules_data) -> dict[str, FormRule]:
        created = {}
        for r in rules_data:
            r = dict(r)
            rule, _ = FormRule.objects.update_or_create(tax_form=form, rule_id=r.pop("rule_id"), defaults=r)
            created[rule.rule_id] = rule
        self.stdout.write(f"  {len(created)} rules")
        return created

    def _upsert_links(self, rules, sources, links_data):
        ct = 0
        for rule_id, source_code, level, note in links_data:
            rule, source = rules.get(rule_id), sources.get(source_code)
            if rule and source:
                RuleAuthorityLink.objects.get_or_create(
                    form_rule=rule, authority_source=source,
                    defaults={"support_level": level, "relevance_note": note})
                ct += 1
        self.stdout.write(f"  {ct} authority links")

    def _upsert_lines(self, form, lines_data):
        for ln in lines_data:
            ln = dict(ln)
            FormLine.objects.update_or_create(tax_form=form, line_number=ln.pop("line_number"), defaults=ln)
        self.stdout.write(f"  {len(lines_data)} lines")

    def _upsert_diagnostics(self, form, diags_data):
        for d in diags_data:
            d = dict(d)
            FormDiagnostic.objects.update_or_create(tax_form=form, diagnostic_id=d.pop("diagnostic_id"), defaults=d)
        self.stdout.write(f"  {len(diags_data)} diagnostics")

    def _upsert_tests(self, form, tests_data):
        for t in tests_data:
            t = dict(t)
            TestScenario.objects.update_or_create(tax_form=form, scenario_name=t.pop("scenario_name"), defaults=t)
        self.stdout.write(f"  {len(tests_data)} test scenarios")

    def _upsert_form_links(self, form_code, sources, links):
        for source_code, link_type in links:
            source = sources.get(source_code)
            if source:
                AuthorityFormLink.objects.get_or_create(
                    authority_source=source, form_code=form_code, link_type=link_type,
                    defaults={"note": f"{source_code} -> {form_code}"})

    # ═══════════════════════════════════════════════════════════════════════════
    # Form 1040 stub — Lines 11, 19, 28 only
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_form_1040_stub(self, sources):
        form = self._upsert_form(
            "1040", "Form 1040 — U.S. Individual Income Tax Return (stub: Lines 11, 19, 28 only)",
            ["1040"],
            notes=(
                "STUB SPEC: only Line 11 (AGI placeholder for Sch 8812 input), Line 19 (CTC/ODC), and "
                "Line 28 (ACTC) are modeled. Remaining lines will be specced in future sessions. "
                "Session 14 — first 1040 spec."
            ),
        )
        self._upsert_facts(form, [
            {"fact_key": "line_11_agi", "label": "Adjusted Gross Income (placeholder)", "data_type": "decimal",
             "required": True, "sort_order": 1,
             "notes": "Return-level fact. Will be computed in future sessions; currently a pass-through input for Schedule 8812 Line 1."},
        ])
        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "Line 19 = Schedule 8812 Line 14", "rule_type": "calculation",
             "formula": "line_19 = SCH_8812.L_14",
             "inputs": [], "outputs": ["line_19"],
             "precedence": 1, "sort_order": 1,
             "description": (
                 "Form 1040 Line 19 (CTC + ODC nonrefundable) is pulled from Schedule 8812 Line 14. "
                 "Iteration semantics: once per return."
             )},
            {"rule_id": "R002", "title": "Line 28 = Schedule 8812 Line 27", "rule_type": "calculation",
             "formula": "line_28 = SCH_8812.L_27",
             "inputs": [], "outputs": ["line_28"],
             "precedence": 1, "sort_order": 2,
             "description": (
                 "Form 1040 Line 28 (ACTC refundable) is pulled from Schedule 8812 Line 27. "
                 "Iteration semantics: once per return."
             )},
        ])
        self._upsert_links(rules, sources, [
            ("R001", "IRS_2025_8812_FORM", "primary", "Schedule 8812 Line 14 destination clause"),
            ("R001", "IRS_2025_1040_INSTR", "primary", "Form 1040 Line 19 instructions"),
            ("R002", "IRS_2025_8812_FORM", "primary", "Schedule 8812 Line 27 destination clause (Part II-C)"),
            ("R002", "IRS_2025_1040_INSTR", "primary", "Form 1040 Line 28 instructions"),
        ])
        self._upsert_lines(form, [
            {"line_number": "11", "description": "Adjusted Gross Income — feeds Schedule 8812 Line 1",
             "line_type": "informational", "sort_order": 1,
             "notes": "Placeholder for future 1040 main spec. AGI computation is upstream."},
            {"line_number": "19", "description": "Child tax credit and credit for other dependents",
             "line_type": "calculated", "source_rules": ["R001"], "sort_order": 2,
             "destination_form": "1040 Line 19 (final on return)"},
            {"line_number": "28", "description": "Additional child tax credit",
             "line_type": "calculated", "source_rules": ["R002"], "sort_order": 3,
             "destination_form": "1040 Line 28 (final on return, refundable)"},
        ])
        self._upsert_form_links("1040", sources, [
            ("IRS_2025_1040_INSTR", "governs"),
            ("IRS_2025_8812_FORM", "informs"),
        ])
        self.stdout.write(self.style.SUCCESS("  Form 1040 stub complete."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Schedule 8812 — Full spec
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_form_sch_8812(self, sources):
        form = self._upsert_form(
            "SCH_8812", "Schedule 8812 (Form 1040) — Credits for Qualifying Children and Other Dependents",
            ["1040"],
            notes=(
                "TY 2025 CTC/ACTC spec. Implements OBBBA §70104 (new SSN requirement, $2,200 credit, "
                "permanent §24(h) overrides). Part II-B (3+ QC alternate path) included. "
                "Per-dependent facts use 'dep_*' prefix and document iteration semantics. "
                "Worksheet B and Earned Income Worksheet deferred to future sessions (see diagnostics D009 and the "
                "earned_income_for_actc fact note)."
            ),
        )
        self._load_sch_8812_facts(form)
        rules = self._load_sch_8812_rules(form)
        self._load_sch_8812_authority_links(rules, sources)
        self._load_sch_8812_lines(form)
        self._load_sch_8812_diagnostics(form)
        self._load_sch_8812_tests(form)
        self._upsert_form_links("SCH_8812", sources, [
            ("IRS_2025_8812_FORM", "governs"),
            ("IRS_2025_8812_INSTR", "governs"),
            ("IRC_24", "governs"),
            ("IRC_152", "governs"),
            ("PL_119_21_70104", "governs"),
            ("IRS_2025_1040_INSTR", "informs"),
        ])
        self.stdout.write(self.style.SUCCESS("  Schedule 8812 complete."))

    # ──────────────────────────────────────
    # Schedule 8812 — Facts
    # ──────────────────────────────────────

    def _load_sch_8812_facts(self, form):
        self._upsert_facts(form, [
            # ─── Per-Dependent facts ───
            {"fact_key": "dep_age_at_eoy", "label": "Dependent age at end of tax year",
             "data_type": "integer", "sort_order": 1,
             "notes": "Per-Dependent fact — repeated per row in the Dependents table. CTC requires <17; ODC has no age requirement."},
            {"fact_key": "dep_relationship_code", "label": "Dependent relationship to taxpayer",
             "data_type": "choice", "sort_order": 2,
             "choices": ["child", "descendant_of_child", "sibling", "step_sibling", "descendant_of_sibling",
                         "foster_child", "adopted_child", "other"],
             "notes": "Per-Dependent fact. CTC qualifying-child test fails if 'other'."},
            {"fact_key": "dep_months_resided_with_taxpayer", "label": "Months dependent resided with taxpayer",
             "data_type": "integer", "sort_order": 3,
             "notes": "Per-Dependent fact. 0-12. CTC requires >6. §152(c)(4) tie-breaker resolved upstream."},
            {"fact_key": "dep_provided_over_half_own_support",
             "label": "Did dependent provide over ½ own support?",
             "data_type": "boolean", "sort_order": 4,
             "notes": "Per-Dependent fact. If true, fails §152(c)(1)(D)."},
            {"fact_key": "dep_filed_joint_return", "label": "Did dependent file a joint return?",
             "data_type": "boolean", "sort_order": 5,
             "notes": "Per-Dependent fact. If true (except solely for refund — pre-filtered upstream), fails §152(c)(1)(E)."},
            {"fact_key": "dep_citizenship_status", "label": "Dependent citizenship status",
             "data_type": "choice", "sort_order": 6,
             "choices": ["us_citizen", "us_national", "us_resident_alien", "nonresident_alien", "mexico_canada_resident"],
             "notes": "Per-Dependent fact. Per §152(b)(3). CTC/ODC require US cit/nat/res-alien."},
            {"fact_key": "dep_tin_type", "label": "Dependent TIN type",
             "data_type": "choice", "sort_order": 7,
             "choices": ["valid_ssn", "itin", "atin", "none"],
             "notes": "Per-Dependent fact. valid_ssn = work-authorized SSN issued before due date. CTC requires valid_ssn; ODC accepts valid_ssn/itin/atin."},
            {"fact_key": "dep_is_claimed_as_dependent",
             "label": "Is this person claimed as a dependent on the return?",
             "data_type": "boolean", "sort_order": 8,
             "notes": "Per-Dependent fact. Per §152(a). Tie-breaker rules resolved upstream."},
            {"fact_key": "dep_is_permanently_disabled",
             "label": "Is dependent permanently and totally disabled?",
             "data_type": "boolean", "sort_order": 9,
             "notes": "Per-Dependent fact. Affects ODC age tests (not CTC — CTC has hard <17)."},

            # ─── Return-level facts ───
            {"fact_key": "filing_status", "label": "Filing status",
             "data_type": "choice", "sort_order": 20,
             "choices": ["MFJ", "Single", "HOH", "MFS", "QSS"], "required": True,
             "notes": "Return-level fact. Drives phaseout threshold."},
            {"fact_key": "taxpayer_has_valid_ssn", "label": "Does taxpayer have a valid SSN?",
             "data_type": "boolean", "sort_order": 21, "required": True,
             "notes": "Return-level fact. Per OBBBA §70104(b). NEW for TY 2025."},
            {"fact_key": "spouse_has_valid_ssn", "label": "Does spouse have a valid SSN (MFJ only)?",
             "data_type": "boolean", "sort_order": 22,
             "notes": "Return-level fact. Material only if filing_status = MFJ."},
            {"fact_key": "spouse_has_ssn_or_itin_by_due_date",
             "label": "Does spouse have SSN or ITIN by due date (MFJ only)?",
             "data_type": "boolean", "sort_order": 23,
             "notes": "Return-level fact. MFJ filing requirement when taxpayer has SSN but spouse doesn't."},
            {"fact_key": "agi_line_11", "label": "Form 1040 Line 11 AGI",
             "data_type": "decimal", "sort_order": 24, "required": True,
             "notes": "Return-level fact. Schedule 8812 Line 1 input."},
            {"fact_key": "puerto_rico_excluded_income", "label": "Puerto Rico excluded income",
             "data_type": "decimal", "sort_order": 25, "default_value": "0",
             "notes": "Return-level fact. Schedule 8812 Line 2a."},
            {"fact_key": "form_2555_excluded_amount",
             "label": "Form 2555 excluded amount (lines 45 + 50 combined)",
             "data_type": "decimal", "sort_order": 26, "default_value": "0",
             "notes": "Return-level fact. Schedule 8812 Line 2b. Combined per design decision Q4 (single addback)."},
            {"fact_key": "form_4563_excluded_income", "label": "Form 4563 line 15 — American Samoa exclusion",
             "data_type": "decimal", "sort_order": 27, "default_value": "0",
             "notes": "Return-level fact. Schedule 8812 Line 2c."},
            {"fact_key": "files_form_2555", "label": "Does taxpayer file Form 2555?",
             "data_type": "boolean", "sort_order": 28,
             "notes": "Return-level fact. Disqualifies ACTC entirely; CTC and ODC remain available."},
            {"fact_key": "earned_income_for_actc",
             "label": "Earned income for ACTC (per Earned Income Worksheet)",
             "data_type": "decimal", "sort_order": 29, "default_value": "0",
             "notes": (
                 "Return-level fact. Schedule 8812 Line 18a. Computed in tts-tax-app per the Earned "
                 "Income Worksheet (Sch 8812 Instructions p. 8): wages + combat pay (elected) + "
                 "statutory + Sch C/F/K-1 net − ½ SE tax. DEFERRED WORK: a future spec session will "
                 "decompose the worksheet to serve both ACTC and EIC computations."
             )},
            {"fact_key": "nontaxable_combat_pay", "label": "Nontaxable combat pay (Line 18b)",
             "data_type": "decimal", "sort_order": 30, "default_value": "0",
             "notes": "Return-level fact. Schedule 8812 Line 18b. Election: include in EI for ACTC."},
            {"fact_key": "tax_before_ctc", "label": "Tax before CTC (Form 1040 Line 18)",
             "data_type": "decimal", "sort_order": 31, "default_value": "0",
             "notes": "Return-level fact. Regular tax + AMT + Sch 2 line 3."},
            {"fact_key": "schedule_3_pre_ctc_credits_total",
             "label": "Schedule 3 credits applied before CTC (sum of lines 1, 2, 3, 4, 5b, 6d, 6f, 6l, 6m)",
             "data_type": "decimal", "sort_order": 32, "default_value": "0",
             "notes": "Return-level fact. Per Credit Limit Worksheet A."},
            {"fact_key": "ss_medicare_taxes_withheld",
             "label": "Withheld SS + Medicare taxes (W-2 box 4 + box 6, both spouses if MFJ)",
             "data_type": "decimal", "sort_order": 33, "default_value": "0",
             "notes": "Return-level fact. Schedule 8812 Line 21 (Part II-B)."},
            {"fact_key": "additional_medicare_tax_amount", "label": "Additional Medicare Tax (Form 8959 line 7)",
             "data_type": "decimal", "sort_order": 34, "default_value": "0",
             "notes": "Return-level fact. Part II-B refinement deferred — see D010."},
            {"fact_key": "deductible_se_tax_half", "label": "½ SE tax deduction (Schedule 1 line 15)",
             "data_type": "decimal", "sort_order": 35, "default_value": "0",
             "notes": "Return-level fact. Part of Schedule 8812 Line 22."},
            {"fact_key": "se_tax_total", "label": "SE tax total (Schedule 2 line 5)",
             "data_type": "decimal", "sort_order": 36, "default_value": "0",
             "notes": "Return-level fact. Part of Schedule 8812 Line 22."},
            {"fact_key": "unreported_ss_medicare_tax",
             "label": "Unreported SS/Medicare tax (Schedule 2 line 6, from Forms 4137/8919)",
             "data_type": "decimal", "sort_order": 37, "default_value": "0",
             "notes": "Return-level fact. Part of Schedule 8812 Line 22."},
            {"fact_key": "other_employment_taxes",
             "label": "Other employment taxes (Schedule 2 line 13)",
             "data_type": "decimal", "sort_order": 38, "default_value": "0",
             "notes": "Return-level fact. Part of Schedule 8812 Line 22."},
            {"fact_key": "eitc_claimed", "label": "EITC claimed (Form 1040 Line 27a)",
             "data_type": "decimal", "sort_order": 39, "default_value": "0",
             "notes": "Return-level fact. Schedule 8812 Line 24 component."},
            {"fact_key": "excess_ss_rrta_withheld", "label": "Excess SS/RRTA withheld (Schedule 3 line 11)",
             "data_type": "decimal", "sort_order": 40, "default_value": "0",
             "notes": "Return-level fact. Schedule 8812 Line 24 component."},
            {"fact_key": "claims_credits_requiring_worksheet_b",
             "label": "Claims credits requiring Worksheet B? (Form 8396/8839/5695 Part I/8859)",
             "data_type": "boolean", "sort_order": 41,
             "notes": "Return-level fact. Triggers D009. Preparer-set flag."},
            {"fact_key": "taxpayer_has_rrta_taxes",
             "label": "Taxpayer has Tier 1 RRTA taxes (W-2 box 14 or CT-2)?",
             "data_type": "boolean", "sort_order": 42,
             "notes": "Return-level fact. Triggers D011. Part II-B RRTA handling deferred."},

            # ─── Calculated facts (outputs) ───
            {"fact_key": "magi", "label": "Modified AGI (Schedule 8812 Line 3)",
             "data_type": "decimal", "sort_order": 60,
             "notes": "Calculated. agi_line_11 + addbacks."},
            {"fact_key": "count_qualifying_children", "label": "Count of qualifying children for CTC (Line 4)",
             "data_type": "integer", "sort_order": 61,
             "notes": "Calculated by aggregation over Dependents where dep_qualifies_ctc = True."},
            {"fact_key": "count_other_dependents", "label": "Count of other dependents for ODC (Line 6)",
             "data_type": "integer", "sort_order": 62,
             "notes": "Calculated by aggregation over Dependents where dep_qualifies_odc = True."},
            {"fact_key": "return_ssn_eligible_for_ctc_actc",
             "label": "Return is SSN-eligible for CTC/ACTC?",
             "data_type": "boolean", "sort_order": 63,
             "notes": "Calculated per OBBBA §70104(b). For MFJ: at least one spouse SSN. For others: taxpayer SSN."},
            {"fact_key": "actc_eligible", "label": "Eligible for ACTC?", "data_type": "boolean",
             "sort_order": 64,
             "notes": "Calculated. False if Form 2555 filer OR taxpayer SSN missing OR no QC OR Line 12 = 0."},
            {"fact_key": "actc_part_iib_triggered", "label": "Part II-B alternate ACTC triggered?",
             "data_type": "boolean", "sort_order": 65,
             "notes": "Calculated. True if count_qc >= 3 AND L_20 < L_17."},
        ])

    # ──────────────────────────────────────
    # Schedule 8812 — Rules
    # ──────────────────────────────────────

    def _load_sch_8812_rules(self, form):
        return self._upsert_rules(form, [
            # ─── Group 1: Per-Dependent classification ───
            {"rule_id": "R001", "title": "Dependent qualifies for CTC (7-test classification)",
             "rule_type": "classification", "precedence": 1, "sort_order": 1,
             "formula": (
                 "dep_qualifies_ctc = (dep_age_at_eoy < 17 "
                 "AND dep_relationship_code != 'other' "
                 "AND dep_months_resided_with_taxpayer > 6 "
                 "AND NOT dep_provided_over_half_own_support "
                 "AND NOT dep_filed_joint_return "
                 "AND dep_citizenship_status IN ('us_citizen','us_national','us_resident_alien') "
                 "AND dep_tin_type == 'valid_ssn' "
                 "AND dep_is_claimed_as_dependent)"
             ),
             "inputs": ["dep_age_at_eoy", "dep_relationship_code", "dep_months_resided_with_taxpayer",
                        "dep_provided_over_half_own_support", "dep_filed_joint_return",
                        "dep_citizenship_status", "dep_tin_type", "dep_is_claimed_as_dependent"],
             "outputs": ["dep_qualifies_ctc"],
             "description": (
                 "Iteration semantics: ONCE PER DEPENDENT. Tests all seven CTC qualifying-child conditions "
                 "per §24(c) + §152(c) + §24(h)(7) SSN. Tie-breaker rules (§152(c)(4)) and joint-return-only-"
                 "for-refund exception assumed resolved upstream."
             )},
            {"rule_id": "R002", "title": "Dependent qualifies for ODC",
             "rule_type": "classification", "precedence": 2, "sort_order": 2,
             "formula": (
                 "dep_qualifies_odc = (dep_is_claimed_as_dependent "
                 "AND NOT dep_qualifies_ctc "
                 "AND dep_citizenship_status IN ('us_citizen','us_national','us_resident_alien') "
                 "AND dep_tin_type IN ('valid_ssn','itin','atin'))"
             ),
             "inputs": ["dep_is_claimed_as_dependent", "dep_qualifies_ctc", "dep_citizenship_status",
                        "dep_tin_type"],
             "outputs": ["dep_qualifies_odc"],
             "description": (
                 "Iteration semantics: ONCE PER DEPENDENT. Per §24(h)(4). Note: a QC without SSN drops "
                 "to ODC if has ITIN/ATIN (per Schedule 8812 Form Line 6 caution)."
             )},

            # ─── Group 2: Return-level eligibility ───
            {"rule_id": "R003", "title": "Return SSN-eligible for CTC/ACTC (OBBBA §70104(b))",
             "rule_type": "classification", "precedence": 1, "sort_order": 3,
             "formula": (
                 "return_ssn_eligible_for_ctc_actc = (taxpayer_has_valid_ssn OR "
                 "(filing_status == 'MFJ' AND spouse_has_valid_ssn))"
             ),
             "inputs": ["filing_status", "taxpayer_has_valid_ssn", "spouse_has_valid_ssn"],
             "outputs": ["return_ssn_eligible_for_ctc_actc"],
             "description": (
                 "Iteration semantics: ONCE PER RETURN. NEW for TY 2025. For non-MFJ: taxpayer must have "
                 "valid SSN. For MFJ: at least one spouse SSN sufficient (other needs SSN or ITIN by due date)."
             )},

            # ─── Group 3: Aggregation ───
            {"rule_id": "R004", "title": "Count qualifying children", "rule_type": "calculation",
             "precedence": 3, "sort_order": 4,
             "formula": "count_qualifying_children = COUNT(dependents WHERE dep_qualifies_ctc == True)",
             "inputs": ["dep_qualifies_ctc"], "outputs": ["count_qualifying_children", "L_4"],
             "description": "Iteration semantics: AGGREGATE OVER DEPENDENTS. Schedule 8812 Line 4."},
            {"rule_id": "R005", "title": "Count other dependents", "rule_type": "calculation",
             "precedence": 3, "sort_order": 5,
             "formula": "count_other_dependents = COUNT(dependents WHERE dep_qualifies_odc == True)",
             "inputs": ["dep_qualifies_odc"], "outputs": ["count_other_dependents", "L_6"],
             "description": "Iteration semantics: AGGREGATE OVER DEPENDENTS. Schedule 8812 Line 6."},

            # ─── Group 4: MAGI assembly ───
            {"rule_id": "R006", "title": "MAGI add-back (Line 2d)", "rule_type": "calculation",
             "precedence": 4, "sort_order": 6,
             "formula": "L_2d = puerto_rico_excluded_income + form_2555_excluded_amount + form_4563_excluded_income",
             "inputs": ["puerto_rico_excluded_income", "form_2555_excluded_amount", "form_4563_excluded_income"],
             "outputs": ["L_2d"],
             "description": "Iteration semantics: ONCE PER RETURN. Sch 8812 Line 2d = 2a + 2b + 2c."},
            {"rule_id": "R007", "title": "MAGI (Line 3)", "rule_type": "calculation",
             "precedence": 5, "sort_order": 7,
             "formula": "magi = L_3 = agi_line_11 + L_2d",
             "inputs": ["agi_line_11", "L_2d"], "outputs": ["magi", "L_3"],
             "description": "Iteration semantics: ONCE PER RETURN. Sch 8812 Line 3 = Line 1 + Line 2d."},

            # ─── Group 5: Pre-phaseout credit ───
            {"rule_id": "R008", "title": "CTC pre-phaseout (Line 5)", "rule_type": "calculation",
             "precedence": 6, "sort_order": 8,
             "formula": "L_5 = count_qualifying_children * 2200",
             "inputs": ["count_qualifying_children"], "outputs": ["L_5"],
             "description": "Iteration semantics: ONCE PER RETURN. Sch 8812 Line 5. $2,200 per OBBBA §70104(a)(2)."},
            {"rule_id": "R009", "title": "ODC pre-phaseout (Line 7)", "rule_type": "calculation",
             "precedence": 6, "sort_order": 9,
             "formula": "L_7 = count_other_dependents * 500",
             "inputs": ["count_other_dependents"], "outputs": ["L_7"],
             "description": "Iteration semantics: ONCE PER RETURN. Sch 8812 Line 7. $500 per §24(h)(4)."},
            {"rule_id": "R010", "title": "Combined pre-phaseout (Line 8)", "rule_type": "calculation",
             "precedence": 7, "sort_order": 10,
             "formula": "L_8 = L_5 + L_7",
             "inputs": ["L_5", "L_7"], "outputs": ["L_8"],
             "description": "Iteration semantics: ONCE PER RETURN. Sch 8812 Line 8."},

            # ─── Group 6: Phaseout ───
            {"rule_id": "R011", "title": "Phaseout threshold (Line 9)", "rule_type": "calculation",
             "precedence": 8, "sort_order": 11,
             "formula": "L_9 = 400000 if filing_status == 'MFJ' else 200000",
             "inputs": ["filing_status"], "outputs": ["L_9"],
             "description": (
                 "Iteration semantics: ONCE PER RETURN. Sch 8812 Line 9. $400K MFJ; $200K for Single, HOH, MFS, QSS. "
                 "Per §24(h)(3) override of §24(b)(2) — made permanent by OBBBA §70104(a)(1)."
             )},
            {"rule_id": "R012", "title": "Phaseout excess (Line 10) — round UP to next $1,000",
             "rule_type": "calculation", "precedence": 9, "sort_order": 12,
             "formula": "L_10 = max(0, ceil(max(0, L_3 - L_9) / 1000) * 1000)",
             "inputs": ["L_3", "L_9"], "outputs": ["L_10"],
             "description": (
                 "Iteration semantics: ONCE PER RETURN. Sch 8812 Line 10. CRITICAL: any non-zero excess rounds UP "
                 "to next $1,000 — even $1 of excess yields $1,000 on Line 10. Implements §24(b)(1) 'or fraction "
                 "thereof' rule. Common bug: floor instead of ceil."
             )},
            {"rule_id": "R013", "title": "Phaseout reduction (Line 11)", "rule_type": "calculation",
             "precedence": 10, "sort_order": 13,
             "formula": "L_11 = L_10 * 0.05",
             "inputs": ["L_10"], "outputs": ["L_11"],
             "description": (
                 "Iteration semantics: ONCE PER RETURN. Sch 8812 Line 11. Equivalent to '$50 per $1,000' from §24(b)(1)."
             )},
            {"rule_id": "R014", "title": "Net credit post-phaseout (Line 12)", "rule_type": "calculation",
             "precedence": 11, "sort_order": 14,
             "formula": "L_12 = max(0, L_8 - L_11) if L_8 > L_11 else 0  -- STOP if L_8 <= L_11",
             "inputs": ["L_8", "L_11"], "outputs": ["L_12"],
             "description": (
                 "Iteration semantics: ONCE PER RETURN. Sch 8812 Line 12. If L_8 ≤ L_11, STOP — no CTC, ODC, or ACTC."
             )},

            # ─── Group 7: Nonrefundable, Line 19 ───
            {"rule_id": "R015", "title": "Tax liability for CTC cap (Line 13 — Credit Limit Worksheet A)",
             "rule_type": "calculation", "precedence": 12, "sort_order": 15,
             "formula": "L_13 = max(0, tax_before_ctc - schedule_3_pre_ctc_credits_total)",
             "inputs": ["tax_before_ctc", "schedule_3_pre_ctc_credits_total"], "outputs": ["L_13"],
             "description": (
                 "Iteration semantics: ONCE PER RETURN. Sch 8812 Line 13. Credit Limit Worksheet A: "
                 "Form 1040 Line 18 minus Schedule 3 lines 1, 2, 3, 4, 5b, 6d, 6f, 6l, 6m. Worksheet B applies "
                 "when other competing credits exist — see D009 diagnostic."
             )},
            {"rule_id": "R016", "title": "Line 19 amount (nonrefundable CTC + ODC)", "rule_type": "calculation",
             "precedence": 13, "sort_order": 16,
             "formula": "L_14 = min(L_12, L_13)",
             "inputs": ["L_12", "L_13"], "outputs": ["L_14"],
             "description": "Iteration semantics: ONCE PER RETURN. Sch 8812 Line 14 → Form 1040 Line 19."},

            # ─── Group 8: ACTC Part II-A ───
            {"rule_id": "R017", "title": "ACTC eligibility check", "rule_type": "classification",
             "precedence": 14, "sort_order": 17,
             "formula": (
                 "actc_eligible = (L_12 > 0 AND NOT files_form_2555 "
                 "AND return_ssn_eligible_for_ctc_actc AND count_qualifying_children > 0)"
             ),
             "inputs": ["L_12", "files_form_2555", "return_ssn_eligible_for_ctc_actc",
                        "count_qualifying_children"],
             "outputs": ["actc_eligible"],
             "description": "Iteration semantics: ONCE PER RETURN. Form 2555 caution + return SSN gate + QC required."},
            {"rule_id": "R018", "title": "ACTC overflow (Line 16a)", "rule_type": "calculation",
             "precedence": 15, "sort_order": 18,
             "formula": "L_16a = max(0, L_12 - L_14) if actc_eligible else 0",
             "inputs": ["L_12", "L_14", "actc_eligible"], "outputs": ["L_16a"],
             "description": "Iteration semantics: ONCE PER RETURN. Sch 8812 Line 16a. Zeroes when ACTC ineligible."},
            {"rule_id": "R019", "title": "ACTC per-child cap (Line 16b)", "rule_type": "calculation",
             "precedence": 15, "sort_order": 19,
             "formula": "L_16b = count_qualifying_children * 1700",
             "inputs": ["count_qualifying_children"], "outputs": ["L_16b"],
             "description": (
                 "Iteration semantics: ONCE PER RETURN. Sch 8812 Line 16b. $1,700 per QC for TY 2025 — "
                 "= $1,400 base (§24(h)(5)) indexed via §24(i)(1) per OBBBA §70104(c)."
             )},
            {"rule_id": "R020", "title": "ACTC capped overflow (Line 17)", "rule_type": "calculation",
             "precedence": 16, "sort_order": 20,
             "formula": "L_17 = min(L_16a, L_16b)",
             "inputs": ["L_16a", "L_16b"], "outputs": ["L_17"],
             "description": "Iteration semantics: ONCE PER RETURN. Sch 8812 Line 17."},
            {"rule_id": "R021", "title": "ACTC earned-income excess (Line 19 of Sch 8812)",
             "rule_type": "calculation", "precedence": 17, "sort_order": 21,
             "formula": "L_19 = max(0, earned_income_for_actc - 2500)",
             "inputs": ["earned_income_for_actc"], "outputs": ["L_19"],
             "description": (
                 "Iteration semantics: ONCE PER RETURN. Sch 8812 Line 19 (distinct from Form 1040 Line 19). "
                 "Earned-income floor $2,500 per §24(h)(6) (override of §24(d) base $3,000)."
             )},
            {"rule_id": "R022", "title": "ACTC 15% method (Line 20)", "rule_type": "calculation",
             "precedence": 18, "sort_order": 22,
             "formula": "L_20 = L_19 * 0.15",
             "inputs": ["L_19"], "outputs": ["L_20"],
             "description": "Iteration semantics: ONCE PER RETURN. Sch 8812 Line 20. Per §24(d)(1)(B)(i)."},

            # ─── Group 9: ACTC Part II-B (3+ kids alternate) ───
            {"rule_id": "R023", "title": "Part II-B trigger", "rule_type": "classification",
             "precedence": 19, "sort_order": 23,
             "formula": "actc_part_iib_triggered = (count_qualifying_children >= 3 AND L_20 < L_17)",
             "inputs": ["count_qualifying_children", "L_20", "L_17"], "outputs": ["actc_part_iib_triggered"],
             "description": (
                 "Iteration semantics: ONCE PER RETURN. Triggers when 3+ QC AND 15% method below per-child cap."
             )},
            {"rule_id": "R024", "title": "SS + Medicare taxes paid (Line 21 — common case)",
             "rule_type": "calculation", "precedence": 20, "sort_order": 24,
             "formula": "L_21 = ss_medicare_taxes_withheld + (0.5 * additional_medicare_tax_amount)",
             "inputs": ["ss_medicare_taxes_withheld", "additional_medicare_tax_amount"],
             "outputs": ["L_21"],
             "description": (
                 "Iteration semantics: ONCE PER RETURN. Common-case formula. RRTA refinement deferred — see D010, D011."
             )},
            {"rule_id": "R025", "title": "Other payroll taxes (Line 22)", "rule_type": "calculation",
             "precedence": 20, "sort_order": 25,
             "formula": "L_22 = deductible_se_tax_half + se_tax_total + unreported_ss_medicare_tax + other_employment_taxes",
             "inputs": ["deductible_se_tax_half", "se_tax_total", "unreported_ss_medicare_tax",
                        "other_employment_taxes"],
             "outputs": ["L_22"],
             "description": "Iteration semantics: ONCE PER RETURN. Sch 8812 Line 22 = Sch 1 line 15 + Sch 2 lines 5, 6, 13."},
            {"rule_id": "R026", "title": "Total payroll taxes (Line 23)", "rule_type": "calculation",
             "precedence": 21, "sort_order": 26,
             "formula": "L_23 = L_21 + L_22",
             "inputs": ["L_21", "L_22"], "outputs": ["L_23"],
             "description": "Iteration semantics: ONCE PER RETURN. Sch 8812 Line 23."},
            {"rule_id": "R027", "title": "EITC + excess SS offset (Line 24)", "rule_type": "calculation",
             "precedence": 21, "sort_order": 27,
             "formula": "L_24 = eitc_claimed + excess_ss_rrta_withheld",
             "inputs": ["eitc_claimed", "excess_ss_rrta_withheld"], "outputs": ["L_24"],
             "description": "Iteration semantics: ONCE PER RETURN. Sch 8812 Line 24 = Form 1040 Line 27a + Sch 3 Line 11."},
            {"rule_id": "R028", "title": "ACTC payroll-tax floor (Lines 25-26)", "rule_type": "calculation",
             "precedence": 22, "sort_order": 28,
             "formula": "L_25 = max(0, L_23 - L_24); L_26 = max(L_20, L_25)",
             "inputs": ["L_23", "L_24", "L_20"], "outputs": ["L_25", "L_26"],
             "description": (
                 "Iteration semantics: ONCE PER RETURN. Sch 8812 Lines 25 (payroll - EITC offset, floored at 0) "
                 "and 26 (larger of 15% method or payroll-floor method)."
             )},

            # ─── Group 10: Final ACTC (Line 27) ───
            {"rule_id": "R029", "title": "Line 28 amount (final ACTC)", "rule_type": "calculation",
             "precedence": 23, "sort_order": 29,
             "formula": (
                 "L_27 = 0 if NOT actc_eligible "
                 "else min(L_17, L_26) if actc_part_iib_triggered "
                 "else min(L_17, L_20)"
             ),
             "inputs": ["actc_eligible", "actc_part_iib_triggered", "L_17", "L_20", "L_26"],
             "outputs": ["L_27"],
             "description": "Iteration semantics: ONCE PER RETURN. Sch 8812 Line 27 → Form 1040 Line 28."},

            # ─── Group 11: Disqualification override ───
            {"rule_id": "R030", "title": "Force zero if taxpayer SSN missing (return-level override)",
             "rule_type": "validation", "precedence": 99, "sort_order": 30,
             "formula": "IF NOT return_ssn_eligible_for_ctc_actc THEN L_14 = 0 AND L_27 = 0",
             "inputs": ["return_ssn_eligible_for_ctc_actc"], "outputs": ["L_14", "L_27"],
             "description": (
                 "Iteration semantics: ONCE PER RETURN. HIGHEST PRECEDENCE override per OBBBA §70104(b). "
                 "Forces both nonrefundable (L_14) and refundable (L_27) to $0 when taxpayer (and spouse if MFJ) "
                 "lacks valid SSN. Verbatim STOP language: 'If you, and your spouse if filing jointly, do not "
                 "have a valid SSN, you can't claim the CTC or ACTC.'"
             )},
        ])

    # ──────────────────────────────────────
    # Schedule 8812 — Authority links
    # ──────────────────────────────────────

    def _load_sch_8812_authority_links(self, rules, sources):
        self._upsert_links(rules, sources, [
            # R001 — qualifying child
            ("R001", "IRC_24", "primary", "§24(c) — qualifying child = §152(c) child under 17"),
            ("R001", "IRC_152", "primary", "§152(c)(1)-(2) — five qualifying-child tests + relationship"),
            ("R001", "IRS_2025_8812_INSTR", "primary", "Sch 8812 Instructions E5 — Steps 1-3"),
            ("R001", "PL_119_21_70104", "primary", "OBBBA §70104(b) — SSN requirement (qualifying child)"),
            # R002 — ODC
            ("R002", "IRC_24", "primary", "§24(h)(4) — $500 ODC for non-QC dependents"),
            ("R002", "IRC_152", "secondary", "§152(b)(3) — citizenship/residency requirement"),
            ("R002", "IRS_2025_8812_INSTR", "primary", "Sch 8812 Instructions E6 — ODC four conditions"),
            # R003 — return SSN eligibility
            ("R003", "PL_119_21_70104", "primary", "OBBBA §70104(b) — taxpayer SSN requirement"),
            ("R003", "IRC_24", "primary", "§24(h)(7) as amended — SSN requirement"),
            ("R003", "IRS_2025_8812_INSTR", "primary", "Sch 8812 Instructions E3 — taxpayer SSN req"),
            # R004 / R005 — aggregation
            ("R004", "IRS_2025_8812_FORM", "primary", "Sch 8812 Form — Line 4 instructions"),
            ("R005", "IRS_2025_8812_FORM", "primary", "Sch 8812 Form — Line 6 instructions"),
            # R006 / R007 — MAGI
            ("R006", "IRS_2025_8812_FORM", "primary", "Sch 8812 Lines 2a-2d"),
            ("R006", "IRS_2025_8812_INSTR", "secondary", "MAGI add-back composition"),
            ("R007", "IRS_2025_8812_FORM", "primary", "Sch 8812 Line 3 = Line 1 + Line 2d"),
            ("R007", "IRS_2025_8812_INSTR", "primary", "Sch 8812 Instructions E7 — MAGI definition"),
            # R008 — CTC pre-phaseout
            ("R008", "IRC_24", "primary", "§24(h)(2) — $2,200 per QC"),
            ("R008", "PL_119_21_70104", "primary", "OBBBA §70104(a)(2) — $2,000 → $2,200"),
            ("R008", "IRS_2025_8812_FORM", "primary", "Sch 8812 Line 5 = Line 4 × $2,200"),
            ("R008", "IRS_2025_8812_INSTR", "secondary", "Sch 8812 Instructions E1"),
            # R009 — ODC pre-phaseout
            ("R009", "IRC_24", "primary", "§24(h)(4) — $500 ODC"),
            ("R009", "IRS_2025_8812_FORM", "primary", "Sch 8812 Line 7 = Line 6 × $500"),
            # R010 — combined
            ("R010", "IRS_2025_8812_FORM", "primary", "Sch 8812 Line 8 = Line 5 + Line 7"),
            # R011 — phaseout threshold
            ("R011", "IRC_24", "primary", "§24(h)(3) — $400K MFJ / $200K other"),
            ("R011", "IRS_2025_8812_FORM", "primary", "Sch 8812 Line 9"),
            ("R011", "IRS_2025_8812_INSTR", "secondary", "Sch 8812 Instructions E8"),
            # R012 — phaseout excess (round UP)
            ("R012", "IRC_24", "primary", "§24(b)(1) — 'fraction thereof'"),
            ("R012", "IRS_2025_8812_FORM", "primary", "Sch 8812 Line 10 — round UP to next $1,000"),
            # R013 — phaseout reduction
            ("R013", "IRC_24", "primary", "§24(b)(1) — $50 per $1,000 ≡ 5% × Line 10"),
            ("R013", "IRS_2025_8812_FORM", "primary", "Sch 8812 Line 11 = Line 10 × 5%"),
            # R014 — net post-phaseout
            ("R014", "IRC_24", "primary", "§24(b)(1) — reduced but not below zero"),
            ("R014", "IRS_2025_8812_FORM", "primary", "Sch 8812 Line 12 — STOP if Line 8 ≤ Line 11"),
            # R015 — tax liability cap (Worksheet A)
            ("R015", "IRS_2025_8812_INSTR", "primary", "Credit Limit Worksheet A"),
            ("R015", "IRS_2025_8812_FORM", "primary", "Sch 8812 Line 13"),
            # R016 — Line 19 amount
            ("R016", "IRS_2025_8812_FORM", "primary", "Sch 8812 Line 14 → Form 1040 Line 19"),
            ("R016", "IRS_2025_1040_INSTR", "primary", "Form 1040 Line 19 instructions"),
            # R017 — ACTC eligibility
            ("R017", "IRC_24", "primary", "§24(d) — refundable portion availability"),
            ("R017", "IRS_2025_8812_FORM", "primary", "Sch 8812 Part II-A caution (Form 2555)"),
            ("R017", "IRS_2025_8812_INSTR", "primary", "Sch 8812 Instructions E9 — Form 2555 disqualifies"),
            # R018 — ACTC overflow
            ("R018", "IRS_2025_8812_FORM", "primary", "Sch 8812 Line 16a"),
            # R019 — ACTC per-child cap
            ("R019", "IRC_24", "primary", "§24(h)(5) + §24(i)(1) — $1,400 base indexed to $1,700"),
            ("R019", "PL_119_21_70104", "primary", "OBBBA §70104(c) — inflation adjustment"),
            ("R019", "IRS_2025_8812_INSTR", "primary", "Sch 8812 Instructions E2 — $1,700 ACTC cap"),
            ("R019", "IRS_2025_8812_FORM", "primary", "Sch 8812 Line 16b"),
            # R020 — Line 17
            ("R020", "IRS_2025_8812_FORM", "primary", "Sch 8812 Line 17"),
            # R021 — earned income excess
            ("R021", "IRC_24", "primary", "§24(h)(6) — $2,500 floor (override of §24(d) $3,000)"),
            ("R021", "IRS_2025_8812_FORM", "primary", "Sch 8812 Line 19 (of Sch 8812)"),
            # R022 — 15% method
            ("R022", "IRC_24", "primary", "§24(d)(1)(B)(i) — 15% rate"),
            ("R022", "IRS_2025_8812_FORM", "primary", "Sch 8812 Line 20"),
            # R023 — Part II-B trigger
            ("R023", "IRS_2025_8812_FORM", "primary", "Sch 8812 Part II-A → Part II-B decision"),
            # R024-R028 — Part II-B
            ("R024", "IRS_2025_8812_FORM", "primary", "Sch 8812 Line 21"),
            ("R024", "IRS_2025_8812_INSTR", "secondary", "Additional Medicare Tax and RRTA Tax Worksheet"),
            ("R025", "IRS_2025_8812_FORM", "primary", "Sch 8812 Line 22"),
            ("R026", "IRS_2025_8812_FORM", "primary", "Sch 8812 Line 23"),
            ("R027", "IRS_2025_8812_FORM", "primary", "Sch 8812 Line 24"),
            ("R028", "IRS_2025_8812_FORM", "primary", "Sch 8812 Lines 25-26"),
            # R029 — Final ACTC
            ("R029", "IRC_24", "primary", "§24(d) + §24(h)(5) — final refundable amount"),
            ("R029", "IRS_2025_8812_FORM", "primary", "Sch 8812 Line 27 → Form 1040 Line 28"),
            ("R029", "IRS_2025_1040_INSTR", "primary", "Form 1040 Line 28 instructions"),
            # R030 — Override
            ("R030", "PL_119_21_70104", "primary", "OBBBA §70104(b) — return-level SSN disqualifier"),
            ("R030", "IRC_24", "primary", "§24(h)(7) — no credit without taxpayer SSN"),
            ("R030", "IRS_2025_8812_INSTR", "primary", "Sch 8812 Instructions E12 — STOP language verbatim"),
        ])

    # ──────────────────────────────────────
    # Schedule 8812 — Lines
    # ──────────────────────────────────────

    def _load_sch_8812_lines(self, form):
        self._upsert_lines(form, [
            {"line_number": "1", "description": "Form 1040 Line 11 AGI", "line_type": "input", "sort_order": 1},
            {"line_number": "2a", "description": "Puerto Rico excluded income", "line_type": "input", "sort_order": 2},
            {"line_number": "2b", "description": "Form 2555 lines 45 + 50 (combined)", "line_type": "input", "sort_order": 3},
            {"line_number": "2c", "description": "Form 4563 line 15 (American Samoa)", "line_type": "input", "sort_order": 4},
            {"line_number": "2d", "description": "Sum of 2a + 2b + 2c", "line_type": "calculated",
             "source_rules": ["R006"], "sort_order": 5},
            {"line_number": "3", "description": "MAGI = Line 1 + Line 2d", "line_type": "calculated",
             "source_rules": ["R007"], "sort_order": 6},
            {"line_number": "4", "description": "Number of qualifying children under 17 with valid SSN",
             "line_type": "calculated", "source_rules": ["R004"], "sort_order": 7},
            {"line_number": "5", "description": "Line 4 × $2,200", "line_type": "calculated",
             "source_rules": ["R008"], "sort_order": 8},
            {"line_number": "6", "description": "Number of other dependents (includes QC w/o SSN if has ITIN/ATIN)",
             "line_type": "calculated", "source_rules": ["R005"], "sort_order": 9},
            {"line_number": "7", "description": "Line 6 × $500", "line_type": "calculated",
             "source_rules": ["R009"], "sort_order": 10},
            {"line_number": "8", "description": "Combined pre-phaseout credit (Line 5 + Line 7)",
             "line_type": "subtotal", "source_rules": ["R010"], "sort_order": 11},
            {"line_number": "9", "description": "Phaseout threshold ($400K MFJ / $200K other)",
             "line_type": "calculated", "source_rules": ["R011"], "sort_order": 12},
            {"line_number": "10", "description": "Excess of MAGI over threshold (rounded UP to $1,000)",
             "line_type": "calculated", "source_rules": ["R012"], "sort_order": 13},
            {"line_number": "11", "description": "Phaseout reduction = Line 10 × 5%",
             "line_type": "calculated", "source_rules": ["R013"], "sort_order": 14},
            {"line_number": "12", "description": "Net credit post-phaseout (Line 8 − Line 11). STOP if ≤ 0",
             "line_type": "calculated", "source_rules": ["R014"], "sort_order": 15},
            {"line_number": "13", "description": "Tax liability cap (Credit Limit Worksheet A)",
             "line_type": "calculated", "source_rules": ["R015"], "sort_order": 16},
            {"line_number": "14", "description": "CTC + ODC nonrefundable (min of Line 12, Line 13)",
             "line_type": "total", "source_rules": ["R016", "R030"],
             "destination_form": "Form 1040 Line 19", "sort_order": 17},
            {"line_number": "15", "description": "Reserved for future use",
             "line_type": "informational", "sort_order": 18},
            {"line_number": "16a", "description": "ACTC overflow (Line 12 − Line 14)",
             "line_type": "calculated", "source_rules": ["R018"], "sort_order": 19},
            {"line_number": "16b", "description": "ACTC per-child cap (count QC × $1,700)",
             "line_type": "calculated", "source_rules": ["R019"], "sort_order": 20},
            {"line_number": "17", "description": "Smaller of Line 16a or Line 16b",
             "line_type": "calculated", "source_rules": ["R020"], "sort_order": 21},
            {"line_number": "18a", "description": "Earned income (per Earned Income Worksheet)",
             "line_type": "input", "sort_order": 22},
            {"line_number": "18b", "description": "Nontaxable combat pay election",
             "line_type": "input", "sort_order": 23},
            {"line_number": "19", "description": "Earned income excess (Line 18a − $2,500, floored at 0). NOTE: This is Sch 8812 Line 19, NOT Form 1040 Line 19.",
             "line_type": "calculated", "source_rules": ["R021"], "sort_order": 24},
            {"line_number": "20", "description": "15% earned-income method (Line 19 × 0.15)",
             "line_type": "calculated", "source_rules": ["R022"], "sort_order": 25},
            {"line_number": "21", "description": "SS + Medicare + Additional Medicare taxes (W-2 box 4 + 6, both spouses if MFJ)",
             "line_type": "input", "sort_order": 26},
            {"line_number": "22", "description": "Sch 1 line 15 + Sch 2 lines 5, 6, 13",
             "line_type": "calculated", "source_rules": ["R025"], "sort_order": 27},
            {"line_number": "23", "description": "Line 21 + Line 22",
             "line_type": "calculated", "source_rules": ["R026"], "sort_order": 28},
            {"line_number": "24", "description": "Form 1040 Line 27a (EITC) + Sch 3 Line 11 (excess SS/RRTA)",
             "line_type": "calculated", "source_rules": ["R027"], "sort_order": 29},
            {"line_number": "25", "description": "Line 23 − Line 24, floored at 0",
             "line_type": "calculated", "source_rules": ["R028"], "sort_order": 30},
            {"line_number": "26", "description": "Larger of Line 20 or Line 25",
             "line_type": "calculated", "source_rules": ["R028"], "sort_order": 31},
            {"line_number": "27", "description": "Additional Child Tax Credit (final)",
             "line_type": "total", "source_rules": ["R029", "R030"],
             "destination_form": "Form 1040 Line 28", "sort_order": 32},
        ])

    # ──────────────────────────────────────
    # Schedule 8812 — Diagnostics
    # ──────────────────────────────────────

    def _load_sch_8812_diagnostics(self, form):
        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D001", "title": "Dependent would qualify for CTC but missing SSN",
             "severity": "error",
             "condition": (
                 "PER-DEP: dep_is_claimed_as_dependent AND dep_age_at_eoy < 17 "
                 "AND dep_relationship_code != 'other' AND dep_months_resided_with_taxpayer > 6 "
                 "AND NOT dep_provided_over_half_own_support AND NOT dep_filed_joint_return "
                 "AND dep_citizenship_status IN ('us_citizen','us_national','us_resident_alien') "
                 "AND dep_tin_type != 'valid_ssn'"
             ),
             "message": (
                 "Dependent meets all qualifying-child tests for CTC except the valid-SSN requirement. CTC of "
                 "$2,200 is NOT available. ODC of $500 may be available if the dependent has ITIN or ATIN."
             ),
             "notes": "Per-dependent firing. Cites: PL_119_21_70104.E3, IRC_24.E9, IRS_2025_8812_INSTR.E5, IRS_2025_8812_FORM.E2."},
            {"diagnostic_id": "D002", "title": "Taxpayer SSN missing — entire CTC/ACTC/ODC unavailable",
             "severity": "error",
             "condition": "RETURN: NOT return_ssn_eligible_for_ctc_actc",
             "message": (
                 "Return cannot claim CTC, ACTC, or ODC because taxpayer (and spouse if MFJ) lacks valid SSN. "
                 "New requirement for TY 2025 per OBBBA §70104(b). ODC also unavailable if neither has SSN or ITIN."
             ),
             "notes": "Return-level. Cites: PL_119_21_70104.E3, IRC_24.E9, IRS_2025_8812_INSTR.E3 + E12."},
            {"diagnostic_id": "D003", "title": "MAGI within $25K of phaseout threshold",
             "severity": "warning",
             "condition": (
                 "RETURN: NOT D013_fired AND ("
                 "(filing_status == 'MFJ' AND ABS(magi - 400000) <= 25000) OR "
                 "(filing_status != 'MFJ' AND ABS(magi - 200000) <= 25000))"
             ),
             "message": (
                 "MAGI is within $25,000 of the CTC phaseout threshold. Verify MAGI computation including "
                 "AGI plus Form 2555 lines 45+50, Puerto Rico, American Samoa add-backs."
             ),
             "notes": "Suppressed when D013 fires (avoid double-warn). Cites: IRC_24.E2, IRC_24.E3, IRS_2025_8812_FORM.E1+E3."},
            {"diagnostic_id": "D004", "title": "ACTC limited by 15% earned-income method (not per-child cap)",
             "severity": "warning",
             "condition": "RETURN: actc_eligible AND L_27 > 0 AND L_27 < L_16b",
             "message": (
                 "Refundable ACTC is below the per-child maximum because the 15% earned-income method is "
                 "binding. Verify earned income on Sch 8812 Line 18a includes all eligible items."
             ),
             "notes": "Cites: IRC_24.E5, IRS_2025_8812_INSTR.E10."},
            {"diagnostic_id": "D005", "title": "3+ qualifying children — verify Part II-B path",
             "severity": "warning",
             "condition": "RETURN: count_qualifying_children >= 3 AND L_27 > 0",
             "message": (
                 "Return has 3+ qualifying children. Schedule 8812 Part II-B alternate ACTC computation may "
                 "yield a larger refundable credit than the 15% method (common in SE returns without EITC). "
                 "Verify Part II-B was evaluated."
             ),
             "notes": "Cites: IRS_2025_8812_FORM.E6."},
            {"diagnostic_id": "D006", "title": "Form 2555 filer — ACTC disqualified, CTC/ODC still allowed",
             "severity": "info",
             "condition": "RETURN: files_form_2555 == True",
             "message": (
                 "Taxpayer files Form 2555 (foreign earned income exclusion). ACTC is NOT available "
                 "(Sch 8812 Part II-A caution); CTC and ODC remain available with MAGI add-back via Line 2b."
             ),
             "notes": "Cites: IRS_2025_8812_FORM.E1+E5, IRS_2025_8812_INSTR.E9."},
            {"diagnostic_id": "D007", "title": "Tie-breaker reminder (shared-custody)",
             "severity": "info",
             "condition": (
                 "RETURN: filing_status IN ('Single','HOH','MFS') AND count_qualifying_children > 0 "
                 "AND ANY(dep_relationship_code IN ('child','adopted_child','foster_child','descendant_of_child'))"
             ),
             "message": (
                 "Tie-breaker reminder: confirm §152(c)(4) was applied if any qualifying child has multiple "
                 "potential claimants (divorced parents, non-parent guardians, etc.). Parent prevails over "
                 "non-parent; between two parents, longer residency then higher AGI."
             ),
             "notes": "Narrowed to non-MFJ filers per Q6.2. Cites: IRC_152.E5."},
            {"diagnostic_id": "D008", "title": "Dependent aged 17+ — CTC unavailable, ODC may apply",
             "severity": "info",
             "condition": (
                 "PER-DEP: dep_age_at_eoy >= 17 AND dep_is_claimed_as_dependent "
                 "AND dep_relationship_code IN ('child','adopted_child','foster_child','descendant_of_child') "
                 "AND dep_tin_type != 'none'"
             ),
             "message": (
                 "Dependent is age 17 or older. CTC requires under 17 per §24(c). Dependent qualifies for "
                 "ODC ($500) if otherwise eligible. Common preparer error in the year a child turns 17."
             ),
             "notes": "Per-dependent firing. Cites: IRC_24.E4, IRS_2025_8812_INSTR.E5+E6."},
            {"diagnostic_id": "D009", "title": "Worksheet B applicability (other credits compete)",
             "severity": "warning",
             "condition": (
                 "RETURN: claims_credits_requiring_worksheet_b == True "
                 "AND (count_qualifying_children > 0 OR count_other_dependents > 0) "
                 "AND NOT files_form_2555"
             ),
             "message": (
                 "Taxpayer claims other credits (Form 8396, 8839, 5695 Part I, or 8859) that interact with "
                 "CTC for tax-liability ordering. Credit Limit Worksheet B applies instead of Worksheet A. "
                 "Rule Studio v1 models Worksheet A only — Worksheet B deferred until Schedule 3 credits are specced."
             ),
             "notes": "Cites: IRS_2025_8812_INSTR.E8. See TS_WSB_TBD."},
            {"diagnostic_id": "D010", "title": "Additional Medicare Tax — Part II-B Line 21 may need refinement",
             "severity": "warning",
             "condition": "RETURN: actc_part_iib_triggered == True AND additional_medicare_tax_amount > 0",
             "message": (
                 "Taxpayer paid Additional Medicare Tax (Form 8959). Sch 8812 Part II-B Line 21 requires "
                 "the Additional Medicare Tax and RRTA Tax Worksheet to avoid double-counting. Rule Studio "
                 "v1 uses the common case formula — verify against Form 8959 if amounts diverge."
             ),
             "notes": "Cites: IRS_2025_8812_INSTR.E10, IRS_2025_8812_FORM.E6."},
            {"diagnostic_id": "D011", "title": "RRTA taxes present — Part II-B not modeled",
             "severity": "warning",
             "condition": "RETURN: taxpayer_has_rrta_taxes == True AND actc_part_iib_triggered == True",
             "message": (
                 "Taxpayer has Tier 1 RRTA taxes (railroad employee/representative). Sch 8812 Part II-B has "
                 "RRTA-specific provisions not modeled in Rule Studio v1. Compute Line 21 manually using "
                 "the Additional Medicare Tax and RRTA Tax Worksheet and override Line 27."
             ),
             "notes": "Cites: IRS_2025_8812_FORM.E6."},
            {"diagnostic_id": "D013", "title": "Phaseout zeroed the credit (STOP at Line 12)",
             "severity": "info",
             "condition": "RETURN: L_8 > 0 AND L_11 >= L_8",
             "message": (
                 "Phaseout reduction (Line 11) equals or exceeds the combined credit (Line 8). Per Sch 8812 "
                 "Line 12: STOP — no CTC, ODC, or ACTC available. This is the expected result for high-income "
                 "taxpayers; verify MAGI inputs if unexpected."
             ),
             "notes": "Suppresses D003. Cites: IRS_2025_8812_FORM.E4."},
        ])

    # ──────────────────────────────────────
    # Schedule 8812 — Test scenarios
    # ──────────────────────────────────────

    def _load_sch_8812_tests(self, form):
        self._upsert_tests(form, [
            {"scenario_name": "TS01 — MFJ, 2 QC, no phaseout, ample tax liability",
             "scenario_type": "normal", "sort_order": 1,
             "inputs": {"filing_status": "MFJ", "taxpayer_has_valid_ssn": True, "spouse_has_valid_ssn": True,
                        "agi_line_11": 80000, "tax_before_ctc": 8000, "earned_income_for_actc": 80000,
                        "files_form_2555": False, "count_qualifying_children": 2, "count_other_dependents": 0},
             "expected_outputs": {"L_3": 80000, "L_5": 4400, "L_8": 4400, "L_11": 0, "L_12": 4400,
                                   "L_14": 4400, "L_16a": 0, "L_27": 0,
                                   "1040.L_19": 4400, "1040.L_28": 0},
             "notes": "Baseline. Full nonrefundable CTC with no ACTC needed."},
            {"scenario_name": "TS02 — MFJ, 2 QC, low tax → ACTC spillover at per-child cap",
             "scenario_type": "normal", "sort_order": 2,
             "inputs": {"filing_status": "MFJ", "taxpayer_has_valid_ssn": True, "spouse_has_valid_ssn": True,
                        "agi_line_11": 80000, "tax_before_ctc": 1000, "earned_income_for_actc": 80000,
                        "count_qualifying_children": 2, "count_other_dependents": 0},
             "expected_outputs": {"L_8": 4400, "L_12": 4400, "L_14": 1000, "L_16a": 3400, "L_16b": 3400,
                                   "L_17": 3400, "L_20": 11625, "L_27": 3400,
                                   "1040.L_19": 1000, "1040.L_28": 3400},
             "notes": "ACTC spillover capped by per-child max ($1,700 × 2)."},
            {"scenario_name": "TS03 — Single, 1 QC + 1 ODC, mixed credits",
             "scenario_type": "normal", "sort_order": 3,
             "inputs": {"filing_status": "Single", "taxpayer_has_valid_ssn": True,
                        "agi_line_11": 30000, "tax_before_ctc": 1500, "earned_income_for_actc": 30000,
                        "count_qualifying_children": 1, "count_other_dependents": 1},
             "expected_outputs": {"L_5": 2200, "L_7": 500, "L_8": 2700, "L_12": 2700, "L_14": 1500,
                                   "L_16a": 1200, "L_16b": 1700, "L_17": 1200, "L_20": 4125,
                                   "L_27": 1200, "1040.L_19": 1500, "1040.L_28": 1200},
             "notes": "Mixed QC + ODC, $1,200 ACTC = unused combined credit overflow."},
            {"scenario_name": "TS04 — MFJ, 1 QC, $410K AGI → exact-$1,000 excess phaseout",
             "scenario_type": "edge", "sort_order": 4,
             "inputs": {"filing_status": "MFJ", "taxpayer_has_valid_ssn": True, "spouse_has_valid_ssn": True,
                        "agi_line_11": 410000, "tax_before_ctc": 20000, "earned_income_for_actc": 410000,
                        "count_qualifying_children": 1, "count_other_dependents": 0},
             "expected_outputs": {"L_3": 410000, "L_9": 400000, "L_10": 10000, "L_11": 500,
                                   "L_12": 1700, "L_14": 1700, "L_16a": 0, "L_27": 0,
                                   "1040.L_19": 1700, "1040.L_28": 0},
             "notes": "Phaseout = 10 × $1,000 × 5% = $500. Excess already multiple of $1,000."},
            {"scenario_name": "TS05 — MFJ, 1 QC, $410,500 AGI → 'fraction thereof' rounding test",
             "scenario_type": "edge", "sort_order": 5,
             "inputs": {"filing_status": "MFJ", "taxpayer_has_valid_ssn": True, "spouse_has_valid_ssn": True,
                        "agi_line_11": 410500, "tax_before_ctc": 20000, "earned_income_for_actc": 410500,
                        "count_qualifying_children": 1, "count_other_dependents": 0},
             "expected_outputs": {"L_3": 410500, "L_10": 11000, "L_11": 550, "L_12": 1650,
                                   "L_14": 1650, "1040.L_19": 1650, "1040.L_28": 0},
             "notes": "CRITICAL ROUNDING TEST. Excess $10,500 rounds UP to $11,000 → reduction $550. Floor would give $525 (wrong)."},
            {"scenario_name": "TS05b — MFJ, 1 QC, $400,001 AGI → minimum positive phaseout",
             "scenario_type": "edge", "sort_order": 6,
             "inputs": {"filing_status": "MFJ", "taxpayer_has_valid_ssn": True, "spouse_has_valid_ssn": True,
                        "agi_line_11": 400001, "tax_before_ctc": 20000, "earned_income_for_actc": 400001,
                        "count_qualifying_children": 1, "count_other_dependents": 0},
             "expected_outputs": {"L_3": 400001, "L_10": 1000, "L_11": 50, "L_12": 2150,
                                   "L_14": 2150, "1040.L_19": 2150, "1040.L_28": 0},
             "notes": "Tests the ceil rule: $1 of excess → $1,000 on Line 10 → $50 reduction. High-frequency implementation bug."},
            {"scenario_name": "TS06 — MFJ, 1 QC, $450K AGI → phaseout exceeds credit; STOP",
             "scenario_type": "edge", "sort_order": 7,
             "inputs": {"filing_status": "MFJ", "taxpayer_has_valid_ssn": True, "spouse_has_valid_ssn": True,
                        "agi_line_11": 450000, "tax_before_ctc": 20000, "earned_income_for_actc": 450000,
                        "count_qualifying_children": 1, "count_other_dependents": 0},
             "expected_outputs": {"L_10": 50000, "L_11": 2500, "L_8": 2200, "L_12": 0,
                                   "L_14": 0, "L_27": 0, "1040.L_19": 0, "1040.L_28": 0,
                                   "D013_fires": True},
             "notes": "STOP at Line 12 — phaseout zeros the credit entirely. D013 fires."},
            {"scenario_name": "TS07 — HOH, 2 QC, very low EI → small ACTC via 15% method",
             "scenario_type": "normal", "sort_order": 8,
             "inputs": {"filing_status": "HOH", "taxpayer_has_valid_ssn": True,
                        "agi_line_11": 5000, "tax_before_ctc": 0, "earned_income_for_actc": 5000,
                        "count_qualifying_children": 2, "count_other_dependents": 0},
             "expected_outputs": {"L_8": 4400, "L_14": 0, "L_16a": 4400, "L_16b": 3400, "L_17": 3400,
                                   "L_19": 2500, "L_20": 375, "L_27": 375,
                                   "1040.L_19": 0, "1040.L_28": 375},
             "notes": "15% method binds. ACTC = $375 even though per-child cap allows $3,400. D004 fires."},
            {"scenario_name": "TS08 — HOH, 2 QC, $30K EI → ACTC at per-child cap",
             "scenario_type": "normal", "sort_order": 9,
             "inputs": {"filing_status": "HOH", "taxpayer_has_valid_ssn": True,
                        "agi_line_11": 30000, "tax_before_ctc": 0, "earned_income_for_actc": 30000,
                        "count_qualifying_children": 2, "count_other_dependents": 0},
             "expected_outputs": {"L_8": 4400, "L_14": 0, "L_16a": 4400, "L_16b": 3400, "L_17": 3400,
                                   "L_19": 27500, "L_20": 4125, "L_27": 3400,
                                   "1040.L_19": 0, "1040.L_28": 3400},
             "notes": "15% method exceeds per-child cap; cap binds. ACTC = $3,400."},
            {"scenario_name": "TS09 — MFJ, 1 dep ITIN-only, falls back to ODC",
             "scenario_type": "edge", "sort_order": 10,
             "inputs": {"filing_status": "MFJ", "taxpayer_has_valid_ssn": True, "spouse_has_valid_ssn": True,
                        "agi_line_11": 50000, "tax_before_ctc": 3000, "earned_income_for_actc": 50000,
                        "count_qualifying_children": 0, "count_other_dependents": 1},
             "expected_outputs": {"L_5": 0, "L_7": 500, "L_8": 500, "L_12": 500, "L_14": 500,
                                   "L_16b": 0, "L_27": 0, "1040.L_19": 500, "1040.L_28": 0,
                                   "D001_fires": True},
             "notes": "QC without SSN drops to ODC. D001 fires for the affected dependent."},
            {"scenario_name": "TS09b — ODC only with TLC=$200 — validates ODC NOT refundable",
             "scenario_type": "edge", "sort_order": 11,
             "inputs": {"filing_status": "MFJ", "taxpayer_has_valid_ssn": True, "spouse_has_valid_ssn": True,
                        "agi_line_11": 50000, "tax_before_ctc": 200, "earned_income_for_actc": 50000,
                        "count_qualifying_children": 0, "count_other_dependents": 1},
             "expected_outputs": {"L_8": 500, "L_12": 500, "L_14": 200, "L_16a": 300, "L_16b": 0,
                                   "L_17": 0, "L_27": 0, "1040.L_19": 200, "1040.L_28": 0},
             "notes": "ODC of $500 with $200 tax: $200 absorbed, $300 lost (not refundable). Validates ODC-not-refundable to prevent flow-to-ACTC bug."},
            {"scenario_name": "TS10 — Single, no taxpayer SSN, 1 QC w/SSN → all credits zero",
             "scenario_type": "failure", "sort_order": 12,
             "inputs": {"filing_status": "Single", "taxpayer_has_valid_ssn": False,
                        "agi_line_11": 40000, "tax_before_ctc": 2000, "earned_income_for_actc": 40000,
                        "count_qualifying_children": 1, "count_other_dependents": 0},
             "expected_outputs": {"return_ssn_eligible_for_ctc_actc": False,
                                   "L_14": 0, "L_27": 0, "1040.L_19": 0, "1040.L_28": 0,
                                   "ODC": 0, "D002_fires": True},
             "notes": (
                 "New TY 2025 OBBBA rule. Cited verbatim STOP: 'If you, and your spouse if filing jointly, "
                 "do not have a valid SSN, you can't claim the CTC or ACTC' (IRS_2025_8812_INSTR.E12). "
                 "ODC $0 because QC stays a QC (cannot reclassify as ODC under §24(h)(4))."
             )},
            {"scenario_name": "TS11 — MFJ, both spouses no SSN, 2 QC → all credits zero",
             "scenario_type": "failure", "sort_order": 13,
             "inputs": {"filing_status": "MFJ", "taxpayer_has_valid_ssn": False, "spouse_has_valid_ssn": False,
                        "agi_line_11": 80000, "tax_before_ctc": 8000, "count_qualifying_children": 2,
                        "count_other_dependents": 0},
             "expected_outputs": {"return_ssn_eligible_for_ctc_actc": False,
                                   "L_14": 0, "L_27": 0, "1040.L_19": 0, "1040.L_28": 0,
                                   "D002_fires": True},
             "notes": "MFJ needs AT LEAST one spouse SSN per OBBBA §70104(b) verbatim ('social security number of at least 1 spouse')."},
            {"scenario_name": "TS12 — MFS, 1 QC, $250K AGI → MFS threshold $200K binds; STOP",
             "scenario_type": "edge", "sort_order": 14,
             "inputs": {"filing_status": "MFS", "taxpayer_has_valid_ssn": True,
                        "agi_line_11": 250000, "tax_before_ctc": 20000, "earned_income_for_actc": 250000,
                        "count_qualifying_children": 1, "count_other_dependents": 0},
             "expected_outputs": {"L_9": 200000, "L_10": 50000, "L_11": 2500, "L_8": 2200,
                                   "L_12": 0, "L_14": 0, "L_27": 0,
                                   "1040.L_19": 0, "1040.L_28": 0, "D013_fires": True},
             "notes": "MFS uses $200K threshold, NOT $400K. At same income MFJ would get full $2,200 credit."},
            {"scenario_name": "TS13 — MFJ files Form 2555, 2 QC → CTC OK, ACTC blocked",
             "scenario_type": "edge", "sort_order": 15,
             "inputs": {"filing_status": "MFJ", "taxpayer_has_valid_ssn": True, "spouse_has_valid_ssn": True,
                        "agi_line_11": 80000, "form_2555_excluded_amount": 50000, "files_form_2555": True,
                        "tax_before_ctc": 3000, "earned_income_for_actc": 80000,
                        "count_qualifying_children": 2, "count_other_dependents": 0},
             "expected_outputs": {"L_2b": 50000, "L_2d": 50000, "L_3": 130000,
                                   "L_8": 4400, "L_12": 4400, "L_13": 3000, "L_14": 3000,
                                   "actc_eligible": False, "L_16a": 0, "L_27": 0,
                                   "1040.L_19": 3000, "1040.L_28": 0, "D006_fires": True},
             "notes": "Validates: MAGI add-back via Line 2b AND Form 2555 disqualifies ACTC but not CTC/ODC."},
            {"scenario_name": "TS14 — HOH, 3 QC, $25K SE, no EITC → Part II-B beats 15% method",
             "scenario_type": "edge", "sort_order": 16,
             "inputs": {"filing_status": "HOH", "taxpayer_has_valid_ssn": True,
                        "agi_line_11": 21467, "earned_income_for_actc": 25000, "tax_before_ctc": 0,
                        "se_tax_total": 3533, "deductible_se_tax_half": 1766, "eitc_claimed": 0,
                        "count_qualifying_children": 3, "count_other_dependents": 0},
             "expected_outputs": {"L_8": 6600, "L_14": 0, "L_16a": 6600, "L_16b": 5100, "L_17": 5100,
                                   "L_19": 22500, "L_20": 3375,
                                   "actc_part_iib_triggered": True,
                                   "L_22": 5299, "L_23": 5299, "L_25": 5299, "L_26": 5299,
                                   "L_27": 5100, "1040.L_28": 5100, "D005_fires": True},
             "notes": "Part II-B (SE tax payroll-floor) beats 15% method ($3,375). Per-child cap binds at $5,100. ACTC = $5,100 instead of $3,375."},
            {"scenario_name": "TS14b — HOH, 3 QC, $15K W-2, EITC swamps Part II-B",
             "scenario_type": "edge", "sort_order": 17,
             "inputs": {"filing_status": "HOH", "taxpayer_has_valid_ssn": True,
                        "agi_line_11": 15000, "earned_income_for_actc": 15000, "tax_before_ctc": 0,
                        "ss_medicare_taxes_withheld": 1148, "eitc_claimed": 7500,
                        "count_qualifying_children": 3, "count_other_dependents": 0},
             "expected_outputs": {"L_8": 6600, "L_14": 0, "L_17": 5100,
                                   "L_19": 12500, "L_20": 1875,
                                   "actc_part_iib_triggered": True,
                                   "L_21": 1148, "L_23": 1148, "L_24": 7500, "L_25": 0,
                                   "L_26": 1875, "L_27": 1875, "1040.L_28": 1875,
                                   "D005_fires": True},
             "notes": (
                 "EITC ($7,500) swamps payroll taxes ($1,148) — Line 25 = 0 — so Line 26 = max(L_20, 0) = $1,875. "
                 "15% method wins. Validates max() selection in BOTH directions (Part II-B can help OR not)."
             )},
            {"scenario_name": "TS_WSB_TBD — Worksheet B test scenarios deferred",
             "scenario_type": "edge", "sort_order": 18,
             "inputs": {"_deferred": True},
             "expected_outputs": {"_deferred": True},
             "notes": (
                 "TS_WSB_TBD: Worksheet B test scenarios deferred until Schedule 3 credits (foreign tax credit, "
                 "dependent care, retirement savings contributions) are specced. Diagnostic D009 fires when "
                 "claims_credits_requiring_worksheet_b = True; full test cases will land when supporting "
                 "credit forms are modeled."
             )},
        ])

    # ═══════════════════════════════════════════════════════════════════════════
    # Flow Assertions
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_flow_assertions(self):
        assertions = [
            {"assertion_id": "FA-1040-CTC-01",
             "title": "Each qualifying child with valid SSN contributes exactly $2,200 to pre-phaseout credit",
             "description": (
                 "Per-Dependent contribution check. Validates R001 + R004 + R008 collectively. "
                 "Bug it catches: SSN check accidentally relaxed (e.g., accepts ITIN) or stale TCJA $2,000 amount."
             ),
             "assertion_type": "flow_assertion", "entity_types": ["1040"],
             "definition": {
                 "kind": "per_record_contribution", "form": "SCH_8812",
                 "record_type": "Dependent", "filter": "dep_qualifies_ctc == True",
                 "contribution_amount": 2200, "aggregates_to_line": "SCH_8812.L_5",
                 "aggregate_formula": "count(dep_qualifies_ctc) * 2200",
             },
             "sort_order": 1},
            {"assertion_id": "FA-1040-CTC-02",
             "title": "Each qualifying other dependent contributes exactly $500 to pre-phaseout credit",
             "description": (
                 "Per-Dependent contribution check. Validates R002 + R005 + R009. "
                 "Bug it catches: ODC mis-amount; double-counting a child as both CTC and ODC."
             ),
             "assertion_type": "flow_assertion", "entity_types": ["1040"],
             "definition": {
                 "kind": "per_record_contribution", "form": "SCH_8812",
                 "record_type": "Dependent", "filter": "dep_qualifies_odc == True",
                 "contribution_amount": 500, "aggregates_to_line": "SCH_8812.L_7",
             },
             "sort_order": 2},
            {"assertion_id": "FA-1040-CTC-03",
             "title": "Phaseout reduction = 5% × ceil((MAGI − threshold)/1000)×1000; threshold $400K MFJ else $200K",
             "description": (
                 "Validates R011-R013 (threshold selection + ceil rounding + 5% multiplier). "
                 "Bug it catches: wrong threshold per filing status; floor vs ceil; using base §24(b)(2) thresholds instead of §24(h)(3) override."
             ),
             "assertion_type": "flow_assertion", "entity_types": ["1040"],
             "definition": {
                 "kind": "formula_check", "form": "SCH_8812",
                 "inputs": ["magi", "filing_status"],
                 "formula": (
                     "max(0, ceil(max(0, magi - (400000 if filing_status=='MFJ' else 200000)) / 1000) "
                     "* 1000 * 0.05)"
                 ),
                 "output_line": "SCH_8812.L_11",
             },
             "sort_order": 3},
            {"assertion_id": "FA-1040-CTC-04",
             "title": "ACTC spillover behavior (combined: overflow exists + per-child cap + earned-income cap)",
             "description": (
                 "Validates R017-R022, R029. Combined assertion per Q7.4 with sub-condition labels for "
                 "debugging. Bug it catches: ACTC computed when ineligible; overflow miscalculated; "
                 "wrong cap selected."
             ),
             "assertion_type": "flow_assertion", "entity_types": ["1040"],
             "definition": {
                 "kind": "conditional_flow", "form": "SCH_8812",
                 "condition": "L_12 > L_14 AND actc_eligible",
                 "sub_conditions": [
                     {"sub_id": "overflow_exists", "check": "L_16a == L_12 - L_14"},
                     {"sub_id": "per_child_cap_applies", "check": "L_17 == min(L_16a, L_16b)"},
                     {"sub_id": "earned_income_cap_applies", "check": "L_27 <= L_17"},
                 ],
                 "implication": "L_16a == L_12 - L_14 AND L_17 == min(L_16a, L_16b) AND L_27 <= L_17",
             },
             "sort_order": 4},
            {"assertion_id": "FA-1040-CTC-05",
             "title": "Refundable + nonrefundable ≤ post-phaseout AND ≤ pre-phaseout (universal invariant)",
             "description": (
                 "Two checks: tight (L_14 + L_27 ≤ L_12) and loose (L_14 + L_27 ≤ L_8). Both per Q7.2. "
                 "Bug it catches: double-counting; refund exceeding credited amount; pre-phaseout overflow if L_12 itself is buggy."
             ),
             "assertion_type": "reconciliation", "entity_types": ["1040"],
             "definition": {
                 "kind": "invariant", "form": "SCH_8812",
                 "assertion": "L_14 + L_27 <= L_12 AND L_14 + L_27 <= L_8",
             },
             "sort_order": 5},
            {"assertion_id": "FA-1040-CTC-06",
             "title": "Dependent without valid SSN contributes $0 to CTC (gates R001 SSN test)",
             "description": (
                 "Validates the SSN test inside R001. Per-Dependent gating. Bug it catches: "
                 "SSN check accidentally accepts ITIN/ATIN for CTC purposes."
             ),
             "assertion_type": "flow_assertion", "entity_types": ["1040"],
             "definition": {
                 "kind": "per_record_gating", "form": "SCH_8812",
                 "record_type": "Dependent",
                 "trigger": "dep_tin_type != 'valid_ssn'",
                 "implication": "dep_qualifies_ctc == False AND contributes 0 to SCH_8812.L_5",
             },
             "sort_order": 6},
            {"assertion_id": "FA-1040-CTC-07",
             "title": "Taxpayer SSN missing → both Form 1040 Lines 19 and 28 forced to $0 (return-level)",
             "description": (
                 "Validates R003 + R030. THE highest-value assertion for catching the OBBBA §70104(b) change. "
                 "Bug it catches: pre-OBBBA implementations that skip the taxpayer-SSN check."
             ),
             "assertion_type": "flow_assertion", "entity_types": ["1040"],
             "definition": {
                 "kind": "return_level_gating", "form": "SCH_8812",
                 "trigger": "NOT return_ssn_eligible_for_ctc_actc",
                 "implication": "L_14 == 0 AND L_27 == 0 AND 1040.L_19 == 0 AND 1040.L_28 == 0",
             },
             "sort_order": 7},
            {"assertion_id": "FA-1040-CTC-08",
             "title": "MAGI reconciliation: Line 3 = Line 1 + Line 2d (= 2a + 2b + 2c)",
             "description": (
                 "Validates R006 + R007. Bug it catches: using AGI directly as MAGI (missing addbacks); "
                 "Form 2555 line 45 included but not line 50."
             ),
             "assertion_type": "reconciliation", "entity_types": ["1040"],
             "definition": {
                 "kind": "sum_check", "form": "SCH_8812",
                 "output": "L_3", "sum_of": ["L_1", "L_2a", "L_2b", "L_2c"],
             },
             "sort_order": 8},
            {"assertion_id": "FA-1040-CTC-09",
             "title": "Form 2555 filer: ACTC = $0, but CTC and ODC remain available",
             "description": (
                 "Validates R017 (Form 2555 check). Bug it catches: implementations that either "
                 "(a) block CTC entirely for 2555 filers OR (b) allow ACTC for 2555 filers."
             ),
             "assertion_type": "flow_assertion", "entity_types": ["1040"],
             "definition": {
                 "kind": "conditional_zero", "form": "SCH_8812",
                 "trigger": "files_form_2555 == True",
                 "implication": "L_27 == 0 AND 1040.L_28 == 0",
                 "non_implication": "L_14 computed per normal CTC rules (unchanged)",
             },
             "sort_order": 9},
            {"assertion_id": "FA-1040-CTC-10",
             "title": "Part II-B path selection: triggers iff 3+ QC AND 15% < per-child cap; selects max",
             "description": (
                 "Validates R023, R028, R029. Bug it catches: Part II-B applied to <3 QC; not applied when "
                 "warranted; using L_25 alone instead of max(L_20, L_25)."
             ),
             "assertion_type": "flow_assertion", "entity_types": ["1040"],
             "definition": {
                 "kind": "conditional_path_selection", "form": "SCH_8812",
                 "trigger": "count_qualifying_children >= 3 AND L_20 < L_17",
                 "implication": (
                     "L_26 == max(L_20, max(0, L_23 - L_24)) AND L_27 == min(L_17, L_26)"
                 ),
                 "else_path": "L_27 == min(L_17, L_20)",
             },
             "sort_order": 10},
            {"assertion_id": "FA-1040-CTC-11",
             "title": "Schedule 8812 Lines 14 and 27 flow to Form 1040 Lines 19 and 28",
             "description": (
                 "Validates 1040.R001 + 1040.R002 (cross-form flow). Bug it catches: lines swapped, "
                 "or flow not implemented at all."
             ),
             "assertion_type": "flow_assertion", "entity_types": ["1040"],
             "definition": {
                 "kind": "cross_form_flow",
                 "flows": [
                     {"from": "SCH_8812.L_14", "to": "1040.L_19"},
                     {"from": "SCH_8812.L_27", "to": "1040.L_28"},
                 ],
             },
             "sort_order": 11},
            {"assertion_id": "FA-1040-CTC-12",
             "title": "Phaseout rounding: any non-zero excess rounds UP to next multiple of $1,000",
             "description": (
                 "Validates R012 rounding behavior with explicit test cases per Q7.3. THE single most "
                 "common phaseout implementation bug. Maps directly to TS05 ($410,500) and TS05b ($400,001)."
             ),
             "assertion_type": "flow_assertion", "entity_types": ["1040"],
             "definition": {
                 "kind": "rounding_check", "form": "SCH_8812", "line": "L_10",
                 "behavior": "ceiling_to_1000",
                 "specific_test_cases": [
                     {"excess": 1, "expected_L_10": 1000},
                     {"excess": 999, "expected_L_10": 1000},
                     {"excess": 1000, "expected_L_10": 1000},
                     {"excess": 1001, "expected_L_10": 2000},
                     {"excess": 10500, "expected_L_10": 11000},
                 ],
             },
             "sort_order": 12},
            {"assertion_id": "TI-1040-CTC-A",
             "title": "Dependent classification mutually exclusive: NOT (dep_qualifies_ctc AND dep_qualifies_odc)",
             "description": (
                 "Table invariant on Dependent records. A single dependent cannot be both CTC-qualifying "
                 "and ODC-qualifying simultaneously (Sch 8812 Form Line 6 caution: 'do not include anyone "
                 "you included on line 4'). Bug it catches: UI/data-entry bug that sets both flags."
             ),
             "assertion_type": "table_invariant", "entity_types": ["1040"],
             "definition": {
                 "table_name": "Dependent", "form": "SCH_8812",
                 "check": "mutual_exclusion",
                 "params": {"flags": ["dep_qualifies_ctc", "dep_qualifies_odc"]},
             },
             "sort_order": 13},
        ]
        for a in assertions:
            FlowAssertion.objects.update_or_create(
                assertion_id=a["assertion_id"],
                defaults={k: v for k, v in a.items() if k != "assertion_id"},
            )
        self.stdout.write(f"  {len(assertions)} flow assertions")

    # ═══════════════════════════════════════════════════════════════════════════
    # Report
    # ═══════════════════════════════════════════════════════════════════════════

    def _report_totals(self):
        def _safe(text):
            return text.encode("ascii", errors="replace").decode("ascii")

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("DATABASE TOTALS (after load_1040_ctc)")
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

        all_rules = FormRule.objects.all()
        uncited = [r for r in all_rules if not r.authority_links.exists()]
        if uncited:
            self.stdout.write(self.style.WARNING(f"\nRules with ZERO authority links: {len(uncited)}"))
            for r in uncited[:20]:
                self.stdout.write(_safe(f"  {r.tax_form.form_number} {r.rule_id}: {r.title}"))
        else:
            self.stdout.write(self.style.SUCCESS("\nAll rules have authority links."))

        self.stdout.write("=" * 60)
