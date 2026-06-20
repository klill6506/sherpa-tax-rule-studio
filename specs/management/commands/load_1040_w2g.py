"""Load the FORM_W2G spec — Form W-2G Certain Gambling Winnings (§61).

Effort #4 (UI Batch #2). The income side of gambling: box 1 reportable winnings
are fully includible in gross income under IRC §61 → Schedule 1 line 8b
("Gambling"); box 4 federal income tax withheld → Form 1040 line 25c ("Other
forms" — NOT 25b; W-2G is not a 1099). A per-document model (the 1099-G / W-2
doc precedent) aggregates across W-2G documents. Box 15 (state income tax
withheld) is informational. The §165(d) loss side is the Schedule A worksheet
(already built) — this spec is the income side only.

KEN'S SCOPE DECISIONS (2026-06-20, AskUserQuestion + recommendations pending walk):
  (1) Pull W-2G into effort #4 WITH compute (answered): a FormW2G doc sub-model
      (per-document box 1 winnings, box 4 fed w/h, box 15 state w/h, owner)
      aggregating to Sch 1 L8b + 1040 L25c.
  (2) (recommended, confirm at walk) Schedule 1 line 8b is TOTAL gambling
      winnings — line 8b = Σ W-2G box 1 + a return-level `other_gambling_winnings`
      (non-W-2G winnings). Keeps line 8b accurate (it backs the Sch A §165(d) cap).

LAW VERIFIED 2026-06-20:
  - §61(a): gross income means all income from whatever source derived — gambling
    winnings are fully includible. No exclusion, no year-keyed constant (only the
    form line numbers can move). Reported on 2025 Schedule 1 line 8b ("Gambling"),
    confirmed against the canonical sch_1_spec.json line_map.
  - Federal income tax withheld on Form W-2G (box 4) is claimed on Form 1040 line
    25c ("Other forms"), with W-2G attached if withholding > 0 — NOT line 25b
    (which is 1099 forms only). Verified against the 1040 line-25 instructions.
  - W-2G box layout (Instructions for Forms W-2G and 5754): box 1 = reportable
    winnings; box 4 = federal income tax withheld (regular gambling or backup);
    box 15 = state income tax withheld.
  - §165(d): gambling losses are deductible only as an itemized deduction, capped
    at winnings — the Schedule A side (already built); referenced here only by the
    informational loss-reminder diagnostic.

SAFETY GUARD: READY_TO_SEED stays False until Ken's review walk (the §61 full-
inclusion + the line-8b / line-25c routing + the non-W-2G-winnings scope).
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


READY_TO_SEED = True  # FLIPPED 2026-06-20 — Ken approved the review walk ("Approve & seed as recommended").


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_ENTITY_TYPES = ["1040"]
FORM_STATUS = "draft"


# ═══════════════════════════════════════════════════════════════════════════
# THE MATH (the integrity gate re-types this independently; they share no math).
# §61 full inclusion — no constants, no exclusion, no proration, no year keys.
# ═══════════════════════════════════════════════════════════════════════════


def _num(x) -> float:
    return float(x if x is not None else 0)


def aggregate_w2g(docs, other_gambling_winnings=0) -> tuple[float, float]:
    """Aggregate across W-2G documents. Returns (line8b, line25c):
    Schedule 1 line 8b = Σ box-1 reportable winnings + any non-W-2G gambling
    winnings (the return-level addend); Form 1040 line 25c (this form's share) =
    Σ box-4 federal withholding. §61 full inclusion — no exclusion."""
    line8b = sum(_num(d.get("box1", 0)) for d in docs) + _num(other_gambling_winnings)
    line25c = sum(_num(d.get("box4", 0)) for d in docs)
    return (line8b, line25c)


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("gambling_winnings", "Gambling winnings (§61) — fully includible → Sch 1 line 8b; W-2G box 4 federal withholding → 1040 line 25c; §165(d) loss cap (Schedule A)"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_1040_FORM",
    "IRS_2025_1040_INSTR",
]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRC_61",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2026,
        "title": "IRC §61 — Gross Income Defined",
        "citation": "26 U.S.C. §61(a) (gross income means all income from whatever source derived)",
        "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:61%20edition:prelim)",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "Gambling winnings are fully includible in gross income under §61(a). No exclusion; no year-keyed constant (the §165(d) loss limitation is the deduction side, on Schedule A).",
        "topics": ["gambling_winnings"],
        "excerpts": [
            {
                "excerpt_label": "§61(a) all income from whatever source derived",
                "location_reference": "26 U.S.C. §61(a)",
                "excerpt_text": (
                    "Except as otherwise provided in this subtitle, gross income means all income from whatever "
                    "source derived"
                ),
                "summary_text": "Gambling winnings are fully includible in gross income (no specific exclusion).",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_165D",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2026,
        "title": "IRC §165(d) — Wagering Losses",
        "citation": "26 U.S.C. §165(d) (losses from wagering transactions allowed only to the extent of wagering gains)",
        "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:165%20edition:prelim)",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "The DEDUCTION side (Schedule A, already built). Referenced here only by the loss-reminder diagnostic — gambling losses are an itemized deduction capped at winnings.",
        "topics": ["gambling_winnings"],
        "excerpts": [
            {
                "excerpt_label": "§165(d) wagering losses capped at wagering gains",
                "location_reference": "26 U.S.C. §165(d)",
                "excerpt_text": (
                    "Losses from wagering transactions shall be allowed only to the extent of the gains from such "
                    "transactions."
                ),
                "summary_text": "Gambling losses are deductible only up to gambling winnings (itemized, Schedule A).",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_W2G_INSTR",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2026,
        "title": "IRS Instructions for Forms W-2G and 5754 — box layout",
        "citation": "Instructions for Forms W-2G and 5754, Boxes 1 / 4 / 15",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/iw2g.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": "Box 1 reportable winnings / box 4 federal income tax withheld / box 15 state income tax withheld. REQUIRES HUMAN REVIEW: confirm the box numbering against the W-2G revision applicable to the target year (box 1/4/15 are stable across recent revisions).",
        "topics": ["gambling_winnings"],
        "excerpts": [
            {
                "excerpt_label": "Box 1 — reportable winnings",
                "location_reference": "Instr. Forms W-2G & 5754, Box 1",
                "excerpt_text": (
                    "Enter payments that meet or exceed the applicable reporting threshold if the payment is at "
                    "least 300 times the wager."
                ),
                "summary_text": "Box 1 = the reportable gambling winnings.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Box 4 — federal income tax withheld",
                "location_reference": "Instr. Forms W-2G & 5754, Box 4",
                "excerpt_text": (
                    "Enter any federal income tax withheld, whether regular gambling withholding or backup "
                    "withholding."
                ),
                "summary_text": "Box 4 = federal income tax withheld on the winnings.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Box 15 — state income tax withheld",
                "location_reference": "Instr. Forms W-2G & 5754, Box 15",
                "excerpt_text": "Enter the amount of state income tax withheld.",
                "summary_text": "Box 15 = state income tax withheld (informational for the federal return).",
                "is_key_excerpt": False,
            },
        ],
    },
    {
        "source_code": "IRS_2025_SCH1_LINE8B",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Form 1040 — Schedule 1 Line 8b (Gambling) + Form 1040 Line 25c",
        "citation": "Instructions for Form 1040 (2025), Schedule 1 Line 8b; Form 1040 Line 25c",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i1040gi.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": "The recipient-side routing: gambling winnings → Schedule 1 line 8b; W-2G box-4 federal withholding → Form 1040 line 25c ('other forms', not 25b). REQUIRES HUMAN REVIEW: confirm the exact 2025/2026 instruction wording + the line numbers (8b, 25c) when the forms post.",
        "topics": ["gambling_winnings"],
        "excerpts": [
            {
                "excerpt_label": "Gambling winnings → Schedule 1 line 8b",
                "location_reference": "i1040 (2025), Schedule 1 Line 8b",
                "excerpt_text": (
                    "Report on Schedule 1, line 8b, the total gambling winnings shown on Form(s) W-2G and any "
                    "other gambling winnings not reported on a Form W-2G. Gambling winnings are fully taxable."
                ),
                "summary_text": "Line 8b = total gambling winnings (W-2G plus any winnings without a W-2G).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "W-2G box 4 federal withholding → Form 1040 line 25c",
                "location_reference": "i1040 (2025), Form 1040 Line 25c",
                "excerpt_text": (
                    "Include on line 25c any federal income tax withheld that is shown on the following forms: "
                    "Form W-2G, box 4; Schedule K-1; Form 8959; Form 1042-S; Form 8805; or Form 8288-A."
                ),
                "summary_text": "W-2G box 4 federal withholding goes on Form 1040 line 25c (other forms), not 25b.",
                "is_key_excerpt": True,
            },
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRC_61", "FORM_W2G", "governs"),
    ("IRC_165D", "FORM_W2G", "references"),
    ("IRS_W2G_INSTR", "FORM_W2G", "governs"),
    ("IRS_2025_SCH1_LINE8B", "FORM_W2G", "governs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM: FORM_W2G
# ═══════════════════════════════════════════════════════════════════════════

W_IDENTITY = {
    "form_number": "FORM_W2G",
    "form_title": "Form W-2G Certain Gambling Winnings (Schedule 1, Line 8b) (TY2025)",
    "notes": (
        "Effort #4 (UI Batch #2), 2026-06-20. A per-document aggregation on the 1040: "
        "box 1 reportable winnings (§61, fully includible) → Schedule 1 line 8b "
        "('Gambling'); box 4 federal withholding → Form 1040 line 25c ('Other forms' — "
        "NOT 25b; W-2G is not a 1099). Line 8b = Σ box 1 + a return-level "
        "`other_gambling_winnings` (non-W-2G winnings) so line 8b is the TOTAL winnings "
        "(it also backs the Schedule A §165(d) loss cap). Box 15 (state withholding) is "
        "informational. No render face (an input document, like 1099-G / W-2). No "
        "year-keyed constants — §61 full inclusion is identical for 2025/2026; line 25c "
        "is a roster shared with Form 8959 (additional-Medicare withholding)."
    ),
}

W_FACTS: list[dict] = [
    # ── Inputs (per document; aggregated across the FormW2G rows) ──
    {"fact_key": "wg_box1_winnings", "label": "Box 1 — reportable gambling winnings",
     "data_type": "decimal", "default_value": "0", "sort_order": 1, "notes": "Fully includible (§61) → Sch 1 line 8b."},
    {"fact_key": "wg_box4_fed_withholding", "label": "Box 4 — federal income tax withheld",
     "data_type": "decimal", "default_value": "0", "sort_order": 2, "notes": "→ Form 1040 line 25c (other forms)."},
    {"fact_key": "wg_box15_state_withholding", "label": "Box 15 — state income tax withheld",
     "data_type": "decimal", "default_value": "0", "sort_order": 3, "notes": "Informational (state return / e-file)."},
    {"fact_key": "wg_owner", "label": "Owner (taxpayer / spouse)",
     "data_type": "string", "default_value": "taxpayer", "sort_order": 4, "notes": "Per-document owner."},
    # ── Return-level input (non-W-2G winnings) ──
    {"fact_key": "other_gambling_winnings", "label": "Other gambling winnings (not on a W-2G)",
     "data_type": "decimal", "default_value": "0", "sort_order": 5,
     "notes": "RETURN-LEVEL. Winnings with no W-2G — added to line 8b so it is the total."},
    # ── Outputs ──
    {"fact_key": "wg_sch1_line8b", "label": "Gambling winnings → Schedule 1 line 8b",
     "data_type": "decimal", "sort_order": 30, "notes": "OUTPUT. Σ box1 + other_gambling_winnings."},
    {"fact_key": "wg_line_25c", "label": "Federal withholding → Form 1040 line 25c",
     "data_type": "decimal", "sort_order": 31, "notes": "OUTPUT. Σ box 4 (this form's share of the 25c roster)."},
]

W_RULES: list[dict] = [
    {"rule_id": "R-W2G-LINE8B", "title": "Gambling winnings (box 1) + non-W-2G winnings → Sch 1 line 8b", "rule_type": "calculation",
     "precedence": 1, "sort_order": 1,
     "formula": ("Sch 1 line 8b = Σ box 1 over W-2G docs + other_gambling_winnings (non-W-2G). "
                 "§61 full inclusion — no exclusion, no constants. (§165(d) losses are the Schedule A side.)"),
     "inputs": ["wg_box1_winnings", "other_gambling_winnings"],
     "outputs": ["wg_sch1_line8b"],
     "description": "§61 full inclusion of gambling winnings on Schedule 1 line 8b."},
    {"rule_id": "R-W2G-WH", "title": "Federal withholding (box 4) → Form 1040 line 25c", "rule_type": "calculation",
     "precedence": 2, "sort_order": 2,
     "formula": ("Form 1040 line 25c += Σ box 4 federal income tax withheld across the W-2G docs. Line 25c is a "
                 "ROSTER (W-2G box 4 + Form 8959 additional-Medicare withholding) — NOT line 25b (W-2G is not a 1099)."),
     "inputs": ["wg_box4_fed_withholding"], "outputs": ["wg_line_25c"],
     "description": "W-2G box 4 aggregates into the line-25c 'other forms' withholding total."},
]

W_LINES: list[dict] = [
    {"line_number": "w1", "description": "Box 1 — reportable gambling winnings", "line_type": "input"},
    {"line_number": "w4", "description": "Box 4 — federal income tax withheld", "line_type": "input"},
    {"line_number": "w15", "description": "Box 15 — state income tax withheld", "line_type": "input"},
    {"line_number": "other_gambling", "description": "Other gambling winnings (not on a W-2G)", "line_type": "input"},
    {"line_number": "sch1_8b", "description": "Gambling winnings → Schedule 1 line 8b", "line_type": "total"},
    {"line_number": "line_25c", "description": "Federal withholding → Form 1040 line 25c", "line_type": "total"},
]

W_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_W2G_WH_ONLY", "title": "Federal withholding with no gambling winnings", "severity": "warning",
     "condition": "wg_box4_fed_withholding > 0 AND wg_box1_winnings == 0",
     "message": ("This Form W-2G has federal income tax withheld (box 4) but no box 1 reportable winnings. "
                 "Confirm the withholding belongs to a winnings payment — box 1 should normally be present."),
     "notes": "No silent gap — withholding without winnings is suspicious."},
    {"diagnostic_id": "D_W2G_LOSS_SCHA", "title": "Gambling losses are deductible only on Schedule A (§165(d))", "severity": "info",
     "condition": "gambling winnings present on line 8b",
     "message": ("Gambling winnings are fully taxable on Schedule 1 line 8b. Gambling LOSSES are deductible only "
                 "as an itemized deduction on Schedule A, and only up to the amount of winnings (section 165(d)) "
                 "— they do not reduce line 8b. Enter any losses on the Schedule A worksheet."),
     "notes": "Cross-reference to the Schedule A §165(d) loss cap; informational."},
]

W_SCENARIOS: list[dict] = [
    {"scenario_name": "W-T1 — simple winnings", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "docs": [{"box1": 5000, "box4": 0}]},
     "expected_outputs": {"wg_sch1_line8b": 5000, "wg_line_25c": 0},
     "notes": "$5,000 box 1, no withholding → line 8b = 5,000."},
    {"scenario_name": "W-T2 — winnings with withholding", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"tax_year": 2025, "docs": [{"box1": 5000, "box4": 1000}]},
     "expected_outputs": {"wg_sch1_line8b": 5000, "wg_line_25c": 1000},
     "notes": "Box 4 $1,000 → 1040 line 25c (other forms)."},
    {"scenario_name": "W-T3 — multi-document aggregation", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"tax_year": 2025, "docs": [{"box1": 5000, "box4": 1000}, {"box1": 3000, "box4": 500}]},
     "expected_outputs": {"wg_sch1_line8b": 8000, "wg_line_25c": 1500},
     "notes": "Two W-2Gs → line 8b = 8,000; line 25c = 1,500."},
    {"scenario_name": "W-T4 — non-W-2G winnings add to line 8b", "scenario_type": "edge_case", "sort_order": 4,
     "inputs": {"tax_year": 2025, "docs": [{"box1": 2000, "box4": 0}], "other_gambling_winnings": 500},
     "expected_outputs": {"wg_sch1_line8b": 2500, "wg_line_25c": 0},
     "notes": "Total winnings = W-2G 2,000 + non-W-2G 500 = 2,500 on line 8b."},
    {"scenario_name": "W-T5 — withholding with no winnings → warning", "scenario_type": "diagnostic", "sort_order": 5,
     "inputs": {"tax_year": 2025, "docs": [{"box1": 0, "box4": 200}]},
     "expected_outputs": {"D_W2G_WH_ONLY": True},
     "notes": "Box 4 present, box 1 zero → D_W2G_WH_ONLY."},
]

W_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-W2G-LINE8B", "IRC_61", "primary", "§61 full inclusion of gambling winnings"),
    ("R-W2G-LINE8B", "IRS_W2G_INSTR", "secondary", "Box 1 reportable winnings"),
    ("R-W2G-LINE8B", "IRS_2025_SCH1_LINE8B", "secondary", "Winnings → Schedule 1 line 8b"),
    ("R-W2G-WH", "IRS_2025_SCH1_LINE8B", "primary", "Box 4 → Form 1040 line 25c"),
    ("R-W2G-WH", "IRS_W2G_INSTR", "secondary", "Box 4 federal income tax withheld"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-W2G-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "§61 full inclusion — line 8b = Σ box 1 + non-W-2G winnings",
     "description": "Validates R-W2G-LINE8B. Bug it catches: an exclusion wrongly applied (there is none), or the non-W-2G winnings dropped.",
     "definition": {"kind": "formula_check", "form": "FORM_W2G",
                    "formula": "sch1_8b = Σ box1 + other_gambling_winnings; no exclusion"},
     "sort_order": 1},
    {"assertion_id": "FA-1040-W2G-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Box 4 federal withholding → Form 1040 line 25c (not 25b)",
     "description": "Validates R-W2G-WH. Bug it catches: W-2G box 4 leaking to line 25b (the 1099 line) instead of 25c (other forms).",
     "definition": {"kind": "formula_check", "form": "FORM_W2G", "formula": "line_25c = Σ box4"},
     "sort_order": 2},
    {"assertion_id": "FA-1040-W2G-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Winnings → Sch 1 line 8b; withholding → 1040 line 25c",
     "description": "Validates the flow targets. Bug it catches: winnings not landing on Schedule 1 line 8b, or withholding on the wrong line.",
     "definition": {"kind": "flow_assertion", "form": "FORM_W2G",
                    "checks": [{"source_line": "sch1_8b", "must_write_to": ["SCH_1.8b"]},
                               {"source_line": "line_25c", "must_write_to": ["1040.25c"]}]},
     "sort_order": 3},
    {"assertion_id": "FA-1040-W2G-04", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "Multi-document aggregation — line 8b = Σ box 1 + non-W-2G",
     "description": "Validates the aggregation. Bug it catches: only one W-2G summed, or the non-W-2G addend omitted.",
     "definition": {"kind": "reconciliation", "form": "FORM_W2G",
                    "formula": "sch1_8b == Σ box1_i + other_gambling_winnings"},
     "sort_order": 4},
    {"assertion_id": "FA-1040-W2G-05", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Line 25c is a roster (W-2G box 4 + Form 8959), never a clobber",
     "description": "Validates the 25c roster. Bug it catches: the W-2G write overwriting the Form 8959 additional-Medicare withholding on line 25c (or vice versa).",
     "definition": {"kind": "reconciliation", "form": "FORM_W2G",
                    "formula": "1040.25c == Form8959.line24 + Σ W2G box4"},
     "sort_order": 5},
]


FORMS: list[dict] = [
    {"identity": W_IDENTITY, "facts": W_FACTS, "rules": W_RULES, "lines": W_LINES,
     "diagnostics": W_DIAGNOSTICS, "scenarios": W_SCENARIOS, "rule_links": W_RULE_LINKS},
]


class Command(BaseCommand):
    help = "Load the FORM_W2G spec (Form W-2G certain gambling winnings). Refuses until READY_TO_SEED=True."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad FORM_W2G spec (Form W-2G Certain Gambling Winnings)\n"))
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
                "\nREFUSING TO SEED FORM_W2G: not cleared to seed.\n\n"
                "Gated until Ken's review walk (the §61 full-inclusion + the line-8b /\n"
                "line-25c routing + the non-W-2G-winnings scope).\n\n"
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
        form = TaxForm.objects.filter(form_number="FORM_W2G").first()
        if form:
            uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
            self.stdout.write("FORM_W2G: all rules cited" if not uncited
                              else self.style.WARNING(f"FORM_W2G uncited rules: {len(uncited)}"))
