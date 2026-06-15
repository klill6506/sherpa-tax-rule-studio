"""Load the FORM_1099G spec — Form 1099-G Unemployment Compensation (§85).

Phase 2, second common form. Box 1 unemployment compensation is fully taxable
under IRC §85 → Schedule 1 line 7; box 4 federal withholding → Form 1040 line 25b.
A per-document model (the W2Income / 1099-INT doc precedent) aggregates across
1099-G documents. Box 2 (state/local income-tax refund) is OUT — it is already the
input to the STATE_REFUND worksheet (§111); do not double-count.

KEN'S 3 SCOPE DECISIONS (2026-06-14, AskUserQuestion):
  (1) A Form1099G doc sub-model (per-document: box 1, box-1 same-year repaid, box 4
      fed w/h, box 11 state w/h, owner). Aggregates to Sch 1 L7 + 1040 L25b.
  (2) §85 same-year repayment is netted on line 7 (with the "Repaid" literal); a
      prior-year repayment (§1341 claim of right) is RED-deferred (D_1099G_1341).
  (3) v1 = box 1 + box 4 (+ state w/h) only; a single "other 1099-G boxes present"
      RED (D_1099G_OTHERBOXES) catches box 5/6/7/9 so nothing is silently dropped.

LAW VERIFIED 2026-06-14 (brief tts-tax-app server/specs/_1099g_source_brief.md):
  - §85: unemployment compensation is FULLY includible. There is NO exclusion for
    TY2025 or TY2026 (the 2020 ARPA $10,200 exclusion was COVID-only). So there are
    NO year-keyed constants and NO exclusion worksheet — the only year-sensitivity
    is the form line numbers (Sch 1 line 7, 1040 line 25b), stable across both years.
  - Same-year repayment: subtract the repaid amount from box 1 and report the net on
    line 7, with the repaid amount on the dotted line next to "Repaid".
  - Prior-year repayment (§1341): NOT netted on line 7 — a claim-of-right deduction
    or credit if > $3,000; RED-deferred (prepare manually).

SAFETY GUARD: READY_TO_SEED stays False until Ken's review walk (the §85 full-
inclusion + same-year netting + the §1341 / other-boxes RED scope).
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


READY_TO_SEED = True  # FLIPPED 2026-06-14 — Ken approved the review walk ("Approved — seed it; no render form").


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_ENTITY_TYPES = ["1040"]
FORM_STATUS = "draft"


# ═══════════════════════════════════════════════════════════════════════════
# THE MATH (the integrity gate re-types this independently; they share no math).
# §85 full inclusion — no constants, no exclusion, no proration, no year keys.
# ═══════════════════════════════════════════════════════════════════════════


def _num(x) -> float:
    return float(x if x is not None else 0)


def net_unemployment(box1, repaid_same_year) -> float:
    """Per document: box 1 minus the SAME-YEAR repayment, floored at 0 (§85 / the
    Schedule 1 line 7 'Repaid' netting)."""
    return max(0.0, _num(box1) - _num(repaid_same_year))


def aggregate_1099g(docs) -> tuple[float, float, float]:
    """Aggregate across 1099-G documents. Returns (line7, repaid_literal, line25b):
    line 7 = Σ net unemployment; the 'Repaid' literal = Σ same-year repaid; 1040
    line 25b = Σ box-4 federal withholding."""
    line7 = sum(net_unemployment(d.get("box1", 0), d.get("repaid_same_year", 0)) for d in docs)
    repaid = sum(_num(d.get("repaid_same_year", 0)) for d in docs)
    line25b = sum(_num(d.get("box4", 0)) for d in docs)
    return (line7, repaid, line25b)


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("unemployment_compensation", "Unemployment compensation (§85) — fully taxable → Sch 1 line 7; same-year repayment netting; §1341 prior-year repayment"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_1040_FORM",
    "IRS_2025_1040_INSTR",
]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRC_85",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2026,
        "title": "IRC §85 — Unemployment Compensation",
        "citation": "26 U.S.C. §85(a) (gross income includes unemployment compensation)",
        "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:85%20edition:prelim)",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "Unemployment compensation is fully includible in gross income. §85(c) (the 2020 ARPA exclusion) was a one-year COVID provision — no exclusion applies for 2025/2026.",
        "topics": ["unemployment_compensation"],
        "excerpts": [
            {
                "excerpt_label": "§85(a) full inclusion",
                "location_reference": "26 U.S.C. §85(a)",
                "excerpt_text": (
                    "In the case of an individual, gross income includes unemployment compensation."
                ),
                "summary_text": "Unemployment compensation is fully includible in gross income.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_SCH1_LINE7",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Form 1040 — Schedule 1, Line 7 (Unemployment Compensation)",
        "citation": "Instructions for Form 1040 (2025), Schedule 1 Line 7",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i1040gi.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": "The same-year-repayment netting + the 'Repaid' literal. REQUIRES HUMAN REVIEW: re-verify the 2026 Form 1099-G box layout + the Schedule 1 line 7 number when the 2026 forms post.",
        "topics": ["unemployment_compensation"],
        "excerpts": [
            {
                "excerpt_label": "Report unemployment + the same-year repayment netting",
                "location_reference": "i1040 (2025), Schedule 1 Line 7",
                "excerpt_text": (
                    "Enter the total of your unemployment compensation from Form(s) 1099-G, box 1. If you "
                    "repaid an overpayment of unemployment compensation in 2025, subtract the amount you repaid "
                    "from the total amount you received, enter the result on line 7, and enter 'Repaid' and the "
                    "amount you repaid on the dotted line next to line 7."
                ),
                "summary_text": "Line 7 = box 1 total minus any SAME-YEAR repayment; show the repaid amount as the 'Repaid' literal.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Federal income tax withheld → line 25b",
                "location_reference": "i1040 (2025), Form 1040 Line 25b",
                "excerpt_text": (
                    "Include on line 25b any federal income tax withheld that is shown on a Form 1099 "
                    "(including Form 1099-G, box 4)."
                ),
                "summary_text": "1099-G box 4 federal withholding → Form 1040 line 25b.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_PUB_525_UNEMPLOY",
        "source_type": "official_guidance",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRS Publication 525 (2025) — Unemployment Benefits & Repayments (§1341)",
        "citation": "Pub. 525 (2025), Unemployment compensation; Repayments / Repayment over $3,000 under a claim of right",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/p525.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": False,
        "trust_score": 9.00,
        "requires_human_review": False,
        "notes": "Same-year repayment is netted; a repayment of benefits received in an EARLIER year is a §1341 claim-of-right deduction/credit (RED-deferred). Boxes 5/6/7/9 route elsewhere (RED-deferred).",
        "topics": ["unemployment_compensation"],
        "excerpts": [
            {
                "excerpt_label": "Repayment of benefits received in an earlier year (§1341)",
                "location_reference": "Pub. 525 (2025), Repayments",
                "excerpt_text": (
                    "If you repaid in 2025 unemployment compensation you included in income in an earlier year, "
                    "you can deduct the amount repaid on Schedule A if you itemize and the amount is more than "
                    "$3,000, or take a credit (the claim-of-right method under section 1341). You can't net the "
                    "earlier-year repayment against the current-year unemployment on Schedule 1, line 7."
                ),
                "summary_text": "Prior-year repayment = a §1341 claim-of-right deduction/credit, never netted on line 7.",
                "is_key_excerpt": True,
            },
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRC_85", "FORM_1099G", "governs"),
    ("IRS_2025_SCH1_LINE7", "FORM_1099G", "governs"),
    ("IRS_PUB_525_UNEMPLOY", "FORM_1099G", "governs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM: FORM_1099G
# ═══════════════════════════════════════════════════════════════════════════

G_IDENTITY = {
    "form_number": "FORM_1099G",
    "form_title": "Form 1099-G Unemployment Compensation (Schedule 1, Line 7) (TY2025)",
    "notes": (
        "Ken's 3 scope decisions 2026-06-14 (Phase 2). A per-document aggregation on "
        "the 1040: box 1 unemployment compensation (§85, fully taxable) → Schedule 1 "
        "line 7, netting any SAME-YEAR repayment (the 'Repaid' literal); box 4 federal "
        "withholding → Form 1040 line 25b. A prior-year repayment (§1341 claim of "
        "right) is RED-deferred (D_1099G_1341). Boxes 5/6/7/9 (RTAA / taxable grants "
        "/ agriculture / market gain) are RED-flagged (D_1099G_OTHERBOXES). Box 2 "
        "(state/local income-tax refund) is OUT — it is the STATE_REFUND worksheet's "
        "input. No year-keyed constants — §85 full inclusion is identical for 2025/2026."
    ),
}

G_FACTS: list[dict] = [
    # ── Inputs (per document; aggregated across the Form1099G rows) ──
    {"fact_key": "g_box1_unemployment", "label": "Box 1 — unemployment compensation",
     "data_type": "decimal", "default_value": "0", "sort_order": 1, "notes": "Fully taxable (§85) → Sch 1 line 7."},
    {"fact_key": "g_box1_repaid_same_year", "label": "Same-year repayment of unemployment",
     "data_type": "decimal", "default_value": "0", "sort_order": 2, "notes": "Netted against box 1 (the 'Repaid' literal)."},
    {"fact_key": "g_box4_fed_withholding", "label": "Box 4 — federal income tax withheld",
     "data_type": "decimal", "default_value": "0", "sort_order": 3, "notes": "→ Form 1040 line 25b."},
    {"fact_key": "g_box11_state_withholding", "label": "Box 11 — state income tax withheld",
     "data_type": "decimal", "default_value": "0", "sort_order": 4, "notes": "Informational (state return / e-file)."},
    {"fact_key": "g_owner", "label": "Owner (taxpayer / spouse)",
     "data_type": "string", "default_value": "taxpayer", "sort_order": 5, "notes": "Per-document owner."},
    # ── RED-deferred flags ──
    {"fact_key": "g_prior_year_repayment", "label": "Repayment of a PRIOR-year unemployment benefit (§1341)",
     "data_type": "decimal", "default_value": "0", "sort_order": 6, "notes": "D_1099G_1341 — claim of right, NOT netted."},
    {"fact_key": "g_other_boxes_present", "label": "Box 5/6/7/9 present (RTAA / grants / ag / market gain)?",
     "data_type": "boolean", "default_value": "false", "sort_order": 7, "notes": "D_1099G_OTHERBOXES — not supported in v1."},
    # ── Outputs ──
    {"fact_key": "g_sch1_line7", "label": "Unemployment → Schedule 1 line 7",
     "data_type": "decimal", "sort_order": 30, "notes": "OUTPUT. Σ max(0, box1 − same-year repaid)."},
    {"fact_key": "g_line7_repaid", "label": "Same-year repaid (the 'Repaid' literal)",
     "data_type": "decimal", "sort_order": 31, "notes": "OUTPUT. Σ same-year repayment."},
    {"fact_key": "g_line_25b", "label": "Federal withholding → Form 1040 line 25b",
     "data_type": "decimal", "sort_order": 32, "notes": "OUTPUT. Σ box 4."},
]

G_RULES: list[dict] = [
    {"rule_id": "R-1099G-LINE7", "title": "Unemployment (box 1) net of same-year repayment → Sch 1 line 7", "rule_type": "calculation",
     "precedence": 1, "sort_order": 1,
     "formula": ("Sch 1 line 7 = Σ over 1099-G docs of max(0, box1 − same-year-repaid); the 'Repaid' "
                 "literal = Σ same-year-repaid. §85 full inclusion — no exclusion, no constants."),
     "inputs": ["g_box1_unemployment", "g_box1_repaid_same_year"],
     "outputs": ["g_sch1_line7", "g_line7_repaid"],
     "description": "§85 + the Schedule 1 line 7 same-year-repayment netting."},
    {"rule_id": "R-1099G-WH", "title": "Federal withholding (box 4) → Form 1040 line 25b", "rule_type": "calculation",
     "precedence": 2, "sort_order": 2,
     "formula": "Form 1040 line 25b += Σ box 4 federal income tax withheld across the 1099-G docs.",
     "inputs": ["g_box4_fed_withholding"], "outputs": ["g_line_25b"],
     "description": "1099-G box 4 aggregates into the line-25b withholding total."},
    {"rule_id": "R-1099G-1341", "title": "Prior-year repayment (§1341) — RED, not netted", "rule_type": "routing",
     "precedence": 3, "sort_order": 3,
     "formula": "If g_prior_year_repayment > 0 → D_1099G_1341 (a claim-of-right deduction/credit; not computed).",
     "inputs": ["g_prior_year_repayment"], "outputs": [],
     "description": "§1341. A repayment of an earlier-year benefit is never netted on line 7."},
    {"rule_id": "R-1099G-OTHER", "title": "Other 1099-G boxes present — RED", "rule_type": "routing",
     "precedence": 4, "sort_order": 4,
     "formula": "If g_other_boxes_present → D_1099G_OTHERBOXES (box 5/6/7/9 income is not routed in v1).",
     "inputs": ["g_other_boxes_present"], "outputs": [],
     "description": "RTAA / taxable grants / agriculture payments / market gain — prepare manually."},
]

G_LINES: list[dict] = [
    {"line_number": "g1", "description": "Box 1 — unemployment compensation", "line_type": "input"},
    {"line_number": "g1_repaid", "description": "Same-year repayment of unemployment", "line_type": "input"},
    {"line_number": "g4", "description": "Box 4 — federal income tax withheld", "line_type": "input"},
    {"line_number": "g11", "description": "Box 11 — state income tax withheld", "line_type": "input"},
    {"line_number": "sch1_7", "description": "Unemployment net → Schedule 1 line 7", "line_type": "total"},
    {"line_number": "sch1_7_repaid", "description": "Same-year repaid (the 'Repaid' literal)", "line_type": "calculated"},
    {"line_number": "line_25b", "description": "Federal withholding → Form 1040 line 25b", "line_type": "total"},
]

G_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_1099G_1341", "title": "Prior-year unemployment repayment — claim of right (manual)", "severity": "error",
     "condition": "g_prior_year_repayment > 0",
     "message": ("Not supported: you repaid unemployment compensation that you included in income in an "
                 "EARLIER year. This is not netted on Schedule 1 line 7 — if the repayment is more than $3,000 "
                 "it is a claim-of-right deduction (Schedule A) or a section 1341 credit; otherwise it is not "
                 "deductible. Prepare this repayment manually (Pub 525)."),
     "notes": "§1341. RED-deferred."},
    {"diagnostic_id": "D_1099G_OTHERBOXES", "title": "Other 1099-G boxes present — not supported", "severity": "error",
     "condition": "g_other_boxes_present is True",
     "message": ("Not supported: this Form 1099-G reports an amount in box 5 (RTAA), box 6 (taxable grants), "
                 "box 7 (agriculture payments), or box 9 (market gain). Only box 1 unemployment compensation is "
                 "computed in this version — route the other amount to its correct schedule manually."),
     "notes": "Boxes 5/6/7/9 RED-deferred."},
    {"diagnostic_id": "D_1099G_REPAID", "title": "Same-year unemployment repayment netted on line 7", "severity": "info",
     "condition": "g_box1_repaid_same_year > 0",
     "message": ("A same-year repayment of unemployment was netted against box 1: Schedule 1 line 7 shows the "
                 "net, and the repaid amount prints as the 'Repaid' literal next to line 7."),
     "notes": "The common same-year-repayment case."},
    {"diagnostic_id": "D_1099G_WH_ONLY", "title": "Federal withholding with no unemployment income", "severity": "warning",
     "condition": "g_box4_fed_withholding > 0 AND g_box1_unemployment == 0",
     "message": ("This Form 1099-G has federal income tax withheld (box 4) but no box 1 unemployment "
                 "compensation. Confirm the withholding belongs to a box-1 payment — if it relates to box "
                 "2/5/6/7, it may be reported in the wrong place."),
     "notes": "No silent gap — withholding without income is suspicious."},
    {"diagnostic_id": "D_1099G_BOX2", "title": "State income-tax refund (box 2) goes on the State Refund worksheet", "severity": "info",
     "condition": "the preparer indicates a box-2 amount on a 1099-G",
     "message": ("A state or local income-tax refund (Form 1099-G box 2) is entered on the State & Local "
                 "Income Tax Refund worksheet (Schedule 1 line 1), not here — this form handles only box 1 "
                 "unemployment. Box 2 is not double-counted."),
     "notes": "Cross-reference to STATE_REFUND; informational."},
]

G_SCENARIOS: list[dict] = [
    {"scenario_name": "G-T1 — simple unemployment", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "docs": [{"box1": 5000, "box4": 0}]},
     "expected_outputs": {"g_sch1_line7": 5000, "g_line7_repaid": 0, "g_line_25b": 0},
     "notes": "$5,000 box 1, no withholding → line 7 = 5,000."},
    {"scenario_name": "G-T2 — unemployment with withholding", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"tax_year": 2025, "docs": [{"box1": 5000, "box4": 600}]},
     "expected_outputs": {"g_sch1_line7": 5000, "g_line7_repaid": 0, "g_line_25b": 600},
     "notes": "Box 4 $600 → 1040 line 25b."},
    {"scenario_name": "G-T3 — same-year repayment netted", "scenario_type": "edge_case", "sort_order": 3,
     "inputs": {"tax_year": 2025, "docs": [{"box1": 5000, "repaid_same_year": 1000, "box4": 0}]},
     "expected_outputs": {"g_sch1_line7": 4000, "g_line7_repaid": 1000, "g_line_25b": 0},
     "notes": "5,000 − 1,000 = 4,000 net; the 'Repaid' literal = 1,000."},
    {"scenario_name": "G-T4 — multi-document aggregation", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"tax_year": 2025, "docs": [{"box1": 5000, "box4": 600}, {"box1": 3000, "box4": 300}]},
     "expected_outputs": {"g_sch1_line7": 8000, "g_line7_repaid": 0, "g_line_25b": 900},
     "notes": "Two 1099-Gs → line 7 = 8,000; line 25b = 900."},
    {"scenario_name": "G-T5 — repaid exceeds same-year receipts (floored)", "scenario_type": "edge_case", "sort_order": 5,
     "inputs": {"tax_year": 2025, "docs": [{"box1": 1000, "repaid_same_year": 1500, "box4": 0}]},
     "expected_outputs": {"g_sch1_line7": 0, "g_line7_repaid": 1500, "g_line_25b": 0},
     "notes": "Net floored at 0; the excess repayment is handled as a §1341 item (D_1099G_1341 when flagged)."},
    {"scenario_name": "G-G1 — prior-year repayment → RED", "scenario_type": "diagnostic", "sort_order": 6,
     "inputs": {"tax_year": 2025, "docs": [{"box1": 0}], "g_prior_year_repayment": 4000},
     "expected_outputs": {"D_1099G_1341": True},
     "notes": "§1341 claim of right → D_1099G_1341 (not computed)."},
    {"scenario_name": "G-G2 — other boxes present → RED", "scenario_type": "diagnostic", "sort_order": 7,
     "inputs": {"tax_year": 2025, "docs": [{"box1": 0}], "g_other_boxes_present": True},
     "expected_outputs": {"D_1099G_OTHERBOXES": True},
     "notes": "Box 5/6/7/9 → D_1099G_OTHERBOXES."},
]

G_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-1099G-LINE7", "IRC_85", "primary", "§85 full inclusion"),
    ("R-1099G-LINE7", "IRS_2025_SCH1_LINE7", "secondary", "The line-7 same-year-repayment netting"),
    ("R-1099G-WH", "IRS_2025_SCH1_LINE7", "primary", "Box 4 → line 25b"),
    ("R-1099G-1341", "IRS_PUB_525_UNEMPLOY", "primary", "§1341 claim of right"),
    ("R-1099G-OTHER", "IRS_PUB_525_UNEMPLOY", "primary", "Boxes 5/6/7/9 route elsewhere"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-1099G-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "§85 full inclusion + the same-year-repayment net",
     "description": "Validates R-1099G-LINE7. Bug it catches: an exclusion wrongly applied (there is none for 2025/2026), or the same-year repayment not netted.",
     "definition": {"kind": "formula_check", "form": "FORM_1099G",
                    "formula": "line7 = max(0, box1 − same_year_repaid); no exclusion"},
     "sort_order": 1},
    {"assertion_id": "FA-1040-1099G-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Box 4 federal withholding → Form 1040 line 25b",
     "description": "Validates R-1099G-WH. Bug it catches: 1099-G box 4 not aggregating into the line-25b withholding total.",
     "definition": {"kind": "formula_check", "form": "FORM_1099G", "formula": "line_25b = Σ box4"},
     "sort_order": 2},
    {"assertion_id": "FA-1040-1099G-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Unemployment → Sch 1 line 7; withholding → 1040 line 25b",
     "description": "Validates the flow targets. Bug it catches: line 7 not landing on Schedule 1, or box-4 withholding leaking to the wrong line.",
     "definition": {"kind": "flow_assertion", "form": "FORM_1099G",
                    "checks": [{"source_line": "sch1_7", "must_write_to": ["SCH_1.7"]},
                               {"source_line": "line_25b", "must_write_to": ["1040.25b"]}]},
     "sort_order": 3},
    {"assertion_id": "FA-1040-1099G-04", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "Multi-document aggregation — line 7 = Σ net unemployment",
     "description": "Validates the aggregation. Bug it catches: only one 1099-G summed, or the per-doc floor not applied before summing.",
     "definition": {"kind": "reconciliation", "form": "FORM_1099G",
                    "formula": "sch1_7 == Σ max(0, box1_i − repaid_i)"},
     "sort_order": 4},
    {"assertion_id": "FA-1040-1099G-05", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Gates — §1341 prior-year repayment + other boxes fire RED",
     "description": "Validates R-1099G-1341 + R-1099G-OTHER. Bug it catches: a prior-year repayment silently netted, or boxes 5/6/7/9 silently dropped.",
     "definition": {"kind": "gating_check", "form": "FORM_1099G", "expect": {"red_fires": True},
                    "blockers": ["prior_year_repayment", "other_boxes"]},
     "sort_order": 5},
    {"assertion_id": "FA-1040-1099G-06", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "The same-year 'Repaid' literal = Σ repaid",
     "description": "Validates the 'Repaid' literal. Bug it catches: the repaid amount lost (only the net stored), which drops the line-7 disclosure.",
     "definition": {"kind": "formula_check", "form": "FORM_1099G", "formula": "sch1_7_repaid = Σ same_year_repaid"},
     "sort_order": 6},
]


FORMS: list[dict] = [
    {"identity": G_IDENTITY, "facts": G_FACTS, "rules": G_RULES, "lines": G_LINES,
     "diagnostics": G_DIAGNOSTICS, "scenarios": G_SCENARIOS, "rule_links": G_RULE_LINKS},
]


class Command(BaseCommand):
    help = "Load the FORM_1099G spec (Form 1099-G unemployment compensation). Refuses until READY_TO_SEED=True."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad FORM_1099G spec (Form 1099-G Unemployment Compensation)\n"))
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
                "\nREFUSING TO SEED FORM_1099G: not cleared to seed.\n\n"
                "Gated until Ken's review walk (the §85 full-inclusion + same-year netting\n"
                "+ the §1341 / other-boxes RED scope).\n\n"
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
        form = TaxForm.objects.filter(form_number="FORM_1099G").first()
        if form:
            uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
            self.stdout.write("FORM_1099G: all rules cited" if not uncited
                              else self.style.WARNING(f"FORM_1099G uncited rules: {len(uncited)}"))
