"""Load the Form 461 spec — Limitation on Business Losses (§461(l) Excess Business Loss).

S-6 PAL/basis deepening, WO-03 R5. Authored 2026-07-05 through the WORK_ORDERS front
door; scope = DIAGNOSTIC + pinned 2025 thresholds (Ken, Gate-1 walk 2026-07-05) — NOT a
full NOL-carryover build (the §172 NOL mechanic is not yet built; this spec computes the
EBL amount, flags it, and DESCRIBES the NOL-conversion treatment).

Ordering: §465 at-risk → §469 passive → §461(l) EBL (the LAST of the three individual
loss limiters). Applies to non-corporate taxpayers only.

VERIFIED 2026-07-05 against primary sources (pal_basis_source_brief.md; research pass):
  - 2025 threshold: $313,000 (single/non-joint) / $626,000 (MFJ). Rev. Proc. 2024-40
    (2025 inflation adjustment of the §461(l)(3)(A)(ii)(II) base $250,000/$500,000);
    INDEPENDENTLY confirmed by the 2025 Instructions for Form 461 (verbatim).
  - EBL = aggregate business deductions − (aggregate business gross income/gains +
    threshold), floored at 0. §461(l)(3).
  - OBBBA (P.L. 119-21, 7/4/2025) made §461(l) PERMANENT (removed the post-2028 sunset).
  - Disallowed EBL → NOL carryover (§461(l)(2), §172 80%-limited). ⚠ YEAR-KEYED: the
    "retest as a current-year business loss" alternative was a NON-ENACTED proposal; the
    enacted TY2025 law keeps NOL conversion. Re-verify each season.
  - Applied AFTER §469 and §465 (§461(l)(6)); partner/S-shareholder allocable share
    (§461(l)(4)); does NOT apply to C corporations (§461(l)(1)).

⚠ FACE-LINE CAVEAT: the exact 2025 Form 461 face line NUMBERS (Parts I-III) were not
transcribed verbatim this pass; the FormLines below map to the §461(l)(3) MECHANIC, not
the printed line positions. Confirm the face line-numbering at Ken's review walk
(IRS_2025_F461_INSTR.requires_human_review = True).

SAFETY GUARD: READY_TO_SEED stays False until Ken's review walk (the $313k/$626k
thresholds + the EBL mechanic + the diagnostic-only scope + the NOL year-keyed caveat).
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


READY_TO_SEED = True  # FLIPPED 2026-07-05 — Ken approved the S-6 R5 review walk ("Approve — flip, seed, export").


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_ENTITY_TYPES = ["1040"]
FORM_STATUS = "active"  # promoted draft→active 2026-07-06 (S-6 reconciliation)


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS — §461(l) excess business loss (2025)
# ═══════════════════════════════════════════════════════════════════════════

EBL_THRESHOLD_SINGLE_2025 = 313000     # Rev. Proc. 2024-40; i461 (2025)
EBL_THRESHOLD_MFJ_2025 = 626000        # 200% of single
EBL_BASE_SINGLE = 250000               # §461(l)(3)(A)(ii)(II) statutory base (pre-indexing)
EBL_BASE_MFJ = 500000


def excess_business_loss(agg_business_income, agg_business_deductions, is_joint: bool) -> int:
    """§461(l)(3): EBL = business deductions − (business income/gains + threshold), floor 0."""
    threshold = EBL_THRESHOLD_MFJ_2025 if is_joint else EBL_THRESHOLD_SINGLE_2025
    ebl = agg_business_deductions - (agg_business_income + threshold)
    return int(ebl) if ebl > 0 else 0


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("excess_business_loss", "Excess business loss limitation (Form 461, §461(l)) — non-corporate; after §469/§465; disallowed → NOL"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRC_461",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §461(l) — Limitation on Excess Business Losses of Noncorporate Taxpayers",
        "citation": "26 U.S.C. §461(l)(1),(2),(3),(4),(6) (as amended, made permanent by P.L. 119-21 / OBBBA)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/461",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "The EBL limitation: non-corporate only (l)(1); disallowed → NOL carryover (l)(2); the EBL definition + $250k/$500k base (l)(3); partner/S-shareholder allocable share (l)(4); applied after §469 (l)(6). OBBBA made it permanent.",
        "topics": ["excess_business_loss"],
        "excerpts": [
            {
                "excerpt_label": "§461(l)(1),(2),(3),(6) — the EBL limitation",
                "location_reference": "26 U.S.C. §461(l)(1),(2),(3),(6)",
                "excerpt_text": (
                    "§461(l)(1): in the case of a taxpayer other than a corporation, any excess business loss of "
                    "the taxpayer for the taxable year shall not be allowed. §461(l)(2): any loss disallowed under "
                    "paragraph (1) shall be treated as a net operating loss carryover to the following taxable year "
                    "under section 172. §461(l)(3)(A): 'excess business loss' means the excess of aggregate "
                    "deductions attributable to trades or businesses over the sum of aggregate gross income or gain "
                    "attributable to such trades or businesses plus $250,000 (200 percent of such amount for a "
                    "joint return). §461(l)(6): this subsection is applied after the application of section 469."
                ),
                "summary_text": "§461(l): non-corporate EBL disallowed; disallowed → NOL carryover (l)(2); EBL = business deductions − (business income + $250k/$500k base); applied after §469.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_F461_INSTR",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Form 461 — Limitation on Business Losses",
        "citation": "Instructions for Form 461 (2025); i461",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/instructions/i461",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": "2025 threshold $313,000 / $626,000 (confirmed verbatim) + OBBBA permanence + the disallowed-EBL → NOL carryover statement. REQUIRES HUMAN REVIEW: confirm the exact 2025 Form 461 FACE line-numbering (Parts I-III) — this spec maps to the §461(l)(3) mechanic, not the printed line positions.",
        "topics": ["excess_business_loss"],
        "excerpts": [
            {
                "excerpt_label": "2025 threshold + OBBBA permanence + NOL carryover",
                "location_reference": "i461 (2025), 'What's New' + line instructions",
                "excerpt_text": (
                    "For 2025, the threshold amount is $313,000 ($626,000 for taxpayers filing a joint return). "
                    "P.L. 119-21, commonly known as the One Big Beautiful Bill Act (OBBBA), permanently extended "
                    "the disallowance of a deduction for excess business losses. A disallowed excess business loss "
                    "is treated as a net operating loss (NOL) carryover to the following year."
                ),
                "summary_text": "2025: $313,000 / $626,000 threshold; §461(l) permanent (OBBBA); disallowed EBL → NOL carryover.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule 1 line 8p — report the EBL adjustment as a POSITIVE number",
                "location_reference": "i461 (2025), 'How To Report' / line-8p reporting instructions",
                "excerpt_text": (
                    "For Schedule 1 (Form 1040), enter any excess business loss adjustment on line 8p. Although "
                    "it's a loss, you will report the excess business loss adjustment as a positive number on the "
                    "'Other income' line on your tax return and enter 'ELA' on the dotted line."
                ),
                "summary_text": "Report the excess business loss on Schedule 1 line 8p as a POSITIVE number ('ELA' on the dotted line).",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "REV_PROC_2024_40",
        "source_type": "revenue_procedure",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "Rev. Proc. 2024-40 — 2025 inflation-adjusted amounts",
        "citation": "Rev. Proc. 2024-40 (the §461(l)(3)(A)(ii)(II) 2025 threshold: $313,000 / $626,000)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-drop/rp-24-40.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": "Sets the 2025 §461(l) threshold ($313,000 single / $626,000 MFJ). The figure is independently confirmed by the i461 (2025). (The subsection number within the Rev. Proc. is cited by secondary sources as §2.32 / §3.32 — confirm against rp-24-40.pdf if that citation becomes load-bearing.)",
        "topics": ["excess_business_loss"],
        "excerpts": [
            {
                "excerpt_label": "§461(l) 2025 threshold amounts",
                "location_reference": "Rev. Proc. 2024-40 (2025 inflation adjustments), §461(l)(3)(A)(ii)(II)",
                "excerpt_text": (
                    "For taxable years beginning in 2025, the threshold amount under §461(l)(3)(A)(ii)(II) is "
                    "$313,000 ($626,000 for a joint return)."
                ),
                "summary_text": "2025 §461(l) threshold: $313,000 / $626,000.",
                "is_key_excerpt": True,
            },
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRC_461", "461", "governs"),
    ("IRS_2025_F461_INSTR", "461", "governs"),
    ("REV_PROC_2024_40", "461", "informs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM: 461 (Limitation on Business Losses — §461(l) EBL, diagnostic v1)
# ═══════════════════════════════════════════════════════════════════════════

F461_IDENTITY = {
    "form_number": "461",
    "form_title": "Form 461 — Limitation on Business Losses (§461(l), TY2025)",
    "notes": (
        "S-6 R5 (WO-03), authored 2026-07-05. Scope = DIAGNOSTIC + pinned 2025 thresholds "
        "($313,000 / $626,000; Rev. Proc. 2024-40, confirmed by i461 2025). Computes the "
        "excess business loss (EBL = business deductions − (business income + threshold), "
        "§461(l)(3)) and flags it; the disallowed EBL is DESCRIBED as an NOL carryover "
        "(§461(l)(2)) but the §172 NOL mechanic is NOT built here (deferred). Applies to "
        "non-corporate taxpayers only, AFTER §465 (at-risk) and §469 (passive). "
        "⚠ YEAR-KEYED: OBBBA made §461(l) permanent; disallowed EBL → NOL (the 'retest' "
        "alternative was NOT enacted) — re-verify each season. ⚠ The FormLines map to the "
        "§461(l)(3) mechanic, not the printed 2025 Form 461 face line numbers — confirm the "
        "face numbering at review (i461 requires_human_review)."
    ),
}

F461_FACTS: list[dict] = [
    {"fact_key": "f461_is_joint", "label": "Filing a joint return (MFJ)?",
     "data_type": "boolean", "default_value": "false", "sort_order": 1,
     "notes": "Drives the threshold: $626,000 MFJ vs $313,000 otherwise (2025)."},
    {"fact_key": "f461_agg_business_income", "label": "Aggregate business gross income/gains (§461(l)(3)(A)(ii)(I))",
     "data_type": "decimal", "default_value": "0", "sort_order": 2,
     "notes": "INPUT/OUTPUT. Aggregate income/gain attributable to trades or businesses (after §469/§465). Excludes wages per the Form 461 adjustment; verify at review."},
    {"fact_key": "f461_agg_business_deductions", "label": "Aggregate business deductions (§461(l)(3)(A)(i))",
     "data_type": "decimal", "default_value": "0", "sort_order": 3,
     "notes": "INPUT/OUTPUT. Aggregate deductions attributable to trades or businesses (after §469/§465)."},
    {"fact_key": "f461_threshold", "label": "Threshold amount (2025)",
     "data_type": "decimal", "sort_order": 4,
     "notes": "OUTPUT. $626,000 if f461_is_joint else $313,000 (Rev. Proc. 2024-40)."},
    {"fact_key": "f461_excess_business_loss", "label": "Excess business loss (disallowed)",
     "data_type": "decimal", "sort_order": 5,
     "notes": "OUTPUT. max(0, deductions − (income + threshold)). §461(l)(3)."},
    {"fact_key": "f461_disallowed_to_nol", "label": "Disallowed EBL treated as an NOL carryover",
     "data_type": "decimal", "sort_order": 6,
     "notes": "OUTPUT (= f461_excess_business_loss). §461(l)(2) → §172 next-year NOL (80%-limited). The NOL mechanic itself is not built here."},
    {"fact_key": "f461_sch1_8p", "label": "§461(l) add-back → Schedule 1 line 8p (positive)",
     "data_type": "decimal", "sort_order": 7,
     "notes": "OUTPUT (= f461_excess_business_loss). The current-year add-back reported as a POSITIVE number on Schedule 1 line 8p ('ELA'), increasing AGI. i461 (2025). The NEXT-year NOL is separate (f461_disallowed_to_nol)."},
]

F461_RULES: list[dict] = [
    {"rule_id": "R-461-THRESH", "title": "Threshold = $313,000 / $626,000 (2025)", "rule_type": "calculation",
     "precedence": 1, "sort_order": 1,
     "formula": "f461_threshold = 626000 if f461_is_joint else 313000. (Rev. Proc. 2024-40; §461(l)(3)(A)(ii)(II) base $250k/$500k indexed.)",
     "inputs": ["f461_is_joint"], "outputs": ["f461_threshold"],
     "description": "S-6 R5. Pinned 2025 thresholds; year-keyed (re-verify each season)."},
    {"rule_id": "R-461-EBL", "title": "Excess business loss = deductions − (income + threshold)", "rule_type": "calculation",
     "precedence": 2, "sort_order": 2,
     "formula": ("f461_excess_business_loss = max(0, f461_agg_business_deductions − (f461_agg_business_income + "
                 "f461_threshold)). §461(l)(3). Only a positive result is an EBL (disallowed); zero otherwise."),
     "inputs": ["f461_agg_business_income", "f461_agg_business_deductions", "f461_threshold"],
     "outputs": ["f461_excess_business_loss"],
     "description": "S-6 R5. The core EBL computation (diagnostic scope — computes the amount, flags it)."},
    {"rule_id": "R-461-ORDER", "title": "Applied after §465 and §469; non-corporate only", "rule_type": "routing",
     "precedence": 3, "sort_order": 3,
     "formula": ("§461(l) is the LAST individual loss limiter: §465 at-risk → §469 passive → §461(l) EBL "
                 "(§461(l)(6)). The business income/deduction inputs are the amounts remaining AFTER §465 and "
                 "§469. §461(l)(1) applies to non-corporate taxpayers only (not C corporations); §461(l)(4) uses "
                 "each partner/S-shareholder's allocable share."),
     "inputs": [], "outputs": [],
     "description": "S-6 R5. The ordering + scope guardrail."},
    {"rule_id": "R-461-SCH1", "title": "Disallowed EBL → Schedule 1 line 8p (positive add-back)", "rule_type": "routing",
     "precedence": 3, "sort_order": 3,
     "formula": ("The excess business loss (f461_excess_business_loss) is reported as a POSITIVE number on "
                 "Schedule 1 (Form 1040) line 8p ('Section 461(l) excess business loss adjustment'), with 'ELA' on "
                 "the dotted line (i461 2025). It is an 'Other income' add-back: the business loss was already "
                 "deducted in full via Schedule C/E/F / K-1, so line 8p adds the disallowed excess BACK to income, "
                 "increasing Schedule 1 line 9/10 → Form 1040 line 8 → AGI. Only the CURRENT-year disallowance is "
                 "applied here; the resulting NOL carryover to next year (R-461-NOL) is still described-not-built."),
     "inputs": ["f461_excess_business_loss"], "outputs": ["f461_sch1_8p"],
     "description": "S-6 R5 add-back (2026-07-06). The current-year §461(l) add-back to Schedule 1 line 8p, "
                    "verified verbatim against i461 (2025)."},
    {"rule_id": "R-461-NOL", "title": "Disallowed EBL → NOL carryover (§461(l)(2))", "rule_type": "routing",
     "precedence": 4, "sort_order": 4,
     "formula": ("The disallowed EBL (f461_disallowed_to_nol = f461_excess_business_loss) is treated as a net "
                 "operating loss carryover to the following year under §172 (80%-of-taxable-income limited). "
                 "ENACTED TY2025 treatment (OBBBA permanent); the 'retest as current-year business loss' "
                 "alternative was NOT enacted. The §172 NOL mechanic is NOT built in this spec (diagnostic scope) "
                 "— D_461_NOL records the treatment. Year-keyed: re-verify each season."),
     "inputs": ["f461_excess_business_loss"], "outputs": ["f461_disallowed_to_nol"],
     "description": "S-6 R5. The carryover treatment, described (not built). Year-keyed caveat."},
]

F461_LINES: list[dict] = [
    {"line_number": "BIZ-INC", "description": "Aggregate business gross income/gains (§461(l)(3)(A)(ii)(I))", "line_type": "input"},
    {"line_number": "BIZ-DED", "description": "Aggregate business deductions (§461(l)(3)(A)(i))", "line_type": "input"},
    {"line_number": "THRESH", "description": "Threshold amount — $313,000 / $626,000 MFJ (2025)", "line_type": "calculated"},
    {"line_number": "EBL", "description": "Excess business loss = max(0, BIZ-DED − (BIZ-INC + THRESH))", "line_type": "calculated"},
    {"line_number": "SCH1-8P", "description": "§461(l) add-back → Schedule 1 line 8p (positive; 'ELA')", "line_type": "total", "destination_form": "SCH_1"},
    {"line_number": "NOL", "description": "Disallowed EBL treated as an NOL carryover (§461(l)(2))", "line_type": "total"},
]

F461_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_461_EBL", "title": "Excess business loss limited (§461(l))", "severity": "warning",
     "condition": "f461_excess_business_loss > 0",
     "message": ("Your aggregate business loss exceeds the §461(l) threshold ($313,000; $626,000 if MFJ, 2025), "
                 "so the excess is disallowed this year and carried forward as a net operating loss. This limit "
                 "applies AFTER the at-risk (§465) and passive-activity (§469) limitations. The software has added "
                 "the disallowed excess back on Schedule 1 line 8p ('ELA') this year; the resulting NOL carryover "
                 "to next year is not yet built — record it manually."),
     "notes": "S-6 R5. §461(l)(1),(3). Fires when EBL > 0. The current-year Sch-1 line-8p add-back IS applied (R-461-SCH1); only the next-year §172 NOL carryover remains manual."},
    {"diagnostic_id": "D_461_NOL", "title": "Disallowed EBL becomes an NOL carryover", "severity": "info",
     "condition": "f461_excess_business_loss > 0",
     "message": ("The disallowed excess business loss is treated as a net operating loss carryover to next year "
                 "(§461(l)(2), §172 — limited to 80% of taxable income). Record it as an NOL carryforward. (This "
                 "software computes the EBL amount but does not yet build the NOL carryover mechanics.)"),
     "notes": "S-6 R5. §461(l)(2). Year-keyed: enacted TY2025 = NOL conversion (retest alternative not enacted); re-verify each season."},
    {"diagnostic_id": "D_461_ORDER", "title": "§461(l) applies after §465/§469; not to C corporations", "severity": "info",
     "condition": "f461_agg_business_deductions > 0 OR f461_agg_business_income != 0",
     "message": ("Form 461 (§461(l)) is the last of the three individual loss limits: figure at-risk (Form 6198, "
                 "§465) and passive (Form 8582, §469) FIRST; only the surviving business income/deductions enter "
                 "here. §461(l) does not apply to C corporations."),
     "notes": "S-6 R5. §461(l)(6) ordering; §461(l)(1) non-corporate scope."},
]

F461_SCENARIOS: list[dict] = [
    {"scenario_name": "461-T1 — MFJ business loss under threshold (no EBL)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "is_joint": True, "agg_business_income": 100000, "agg_business_deductions": 600000},
     "expected_outputs": {"f461_threshold": 626000, "f461_excess_business_loss": 0},
     "notes": "deductions 600,000 − (income 100,000 + threshold 626,000) = −126,000 → floored 0. No EBL; full loss allowed."},
    {"scenario_name": "461-T2 — MFJ business loss over threshold (EBL computed)", "scenario_type": "edge_case", "sort_order": 2,
     "inputs": {"tax_year": 2025, "is_joint": True, "agg_business_income": 50000, "agg_business_deductions": 900000},
     "expected_outputs": {"f461_threshold": 626000, "f461_excess_business_loss": 224000, "f461_disallowed_to_nol": 224000,
                          "D_461_EBL": True, "D_461_NOL": True},
     "notes": "900,000 − (50,000 + 626,000) = 224,000 EBL disallowed → NOL carryover. Net business loss 850,000; 626,000 allowed."},
    {"scenario_name": "461-T3 — single over threshold (EBL computed)", "scenario_type": "edge_case", "sort_order": 3,
     "inputs": {"tax_year": 2025, "is_joint": False, "agg_business_income": 0, "agg_business_deductions": 500000},
     "expected_outputs": {"f461_threshold": 313000, "f461_excess_business_loss": 187000, "D_461_EBL": True},
     "notes": "single: 500,000 − (0 + 313,000) = 187,000 EBL disallowed → NOL. 313,000 loss allowed this year."},
    {"scenario_name": "461-T4 — net business income (no limitation)", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"tax_year": 2025, "is_joint": True, "agg_business_income": 400000, "agg_business_deductions": 250000},
     "expected_outputs": {"f461_excess_business_loss": 0},
     "notes": "Net business INCOME (deductions < income) → no excess business loss; §461(l) does not limit."},
]

F461_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-461-THRESH", "REV_PROC_2024_40", "primary", "2025 threshold $313,000 / $626,000"),
    ("R-461-THRESH", "IRS_2025_F461_INSTR", "secondary", "i461 (2025) confirms the threshold"),
    ("R-461-EBL", "IRC_461", "primary", "§461(l)(3) the EBL definition"),
    ("R-461-EBL", "IRS_2025_F461_INSTR", "secondary", "Form 461 EBL computation"),
    ("R-461-ORDER", "IRC_461", "primary", "§461(l)(6) after §469; (l)(1) non-corporate"),
    ("R-461-SCH1", "IRS_2025_F461_INSTR", "primary", "i461 (2025): EBL → Schedule 1 line 8p as a positive number ('ELA')"),
    ("R-461-NOL", "IRC_461", "primary", "§461(l)(2) disallowed → NOL carryover"),
    ("R-461-NOL", "IRS_2025_F461_INSTR", "secondary", "i461 (2025) NOL-carryover statement"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-461-01", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "§461(l) 2025 thresholds ($313k / $626k; base $250k / $500k)",
     "description": "Pins the 2025 EBL threshold + statutory base. Bug it catches: a drifted threshold (e.g. the stale 2024 $305k/$610k).",
     "definition": {"kind": "constants_check", "form": "461",
                    "constants": {"threshold_single": 313000, "threshold_mfj": 626000,
                                  "base_single": 250000, "base_mfj": 500000}},
     "sort_order": 1},
    {"assertion_id": "FA-1040-461-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "EBL = max(0, deductions − (income + threshold))",
     "description": "Validates R-461-EBL. Bug it catches: the threshold not subtracted, or a negative EBL not floored to zero.",
     "definition": {"kind": "formula_check", "form": "461",
                    "formula": "ebl == max(0, agg_business_deductions - (agg_business_income + threshold)); threshold = 626000 if joint else 313000"},
     "sort_order": 2},
    {"assertion_id": "FA-1040-461-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "EBL > 0 fires D_461_EBL + the NOL-carryover note",
     "description": "Validates R-461-NOL / D_461_EBL. Bug it catches: a disallowed EBL not surfaced, or the NOL-carryover treatment not recorded.",
     "definition": {"kind": "gating_check", "form": "461", "expect": {"warn_fires": True},
                    "blockers": ["excess_business_loss_positive"]},
     "sort_order": 3},
    {"assertion_id": "FA-1040-461-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Disallowed EBL adds back to Schedule 1 line 8p (positive) → AGI",
     "description": "Validates R-461-SCH1. Bug it catches: the disallowed EBL not added back (return over-deducts), a wrong sign (must be positive), or the wrong Schedule 1 line.",
     "definition": {"kind": "flow_assertion", "form": "461",
                    "flow": "f461_excess_business_loss -> SCH_1.8p (positive) -> SCH_1.9/10 -> 1040.8"},
     "sort_order": 4},
]


FORMS: list[dict] = [
    {"identity": F461_IDENTITY, "facts": F461_FACTS, "rules": F461_RULES, "lines": F461_LINES,
     "diagnostics": F461_DIAGNOSTICS, "scenarios": F461_SCENARIOS, "rule_links": F461_RULE_LINKS},
]


class Command(BaseCommand):
    help = "Load the Form 461 (§461(l) EBL) spec. Refuses until READY_TO_SEED=True."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad Form 461 (§461(l) EBL) spec\n"))
        self._load_topics()
        sources = self._load_sources()
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
                "\nREFUSING TO SEED Form 461: not cleared to seed.\n\n"
                "Gated until Ken's review walk (the $313k/$626k thresholds + the EBL\n"
                "mechanic + the diagnostic-only scope + the NOL year-keyed caveat +\n"
                "the face-line-numbering confirmation).\n\n"
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
        form = TaxForm.objects.filter(form_number="461").first()
        if form:
            uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
            self.stdout.write("461: all rules cited" if not uncited
                              else self.style.WARNING(f"461 uncited rules: {len(uncited)}"))
