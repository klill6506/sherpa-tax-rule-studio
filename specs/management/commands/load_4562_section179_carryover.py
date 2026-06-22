"""Amend Form 4562 (Part I) with the §179 prior-year carryover mechanics.

WHY: the existing 4562 spec (authored in load_remaining_1120s._expand_4562 +
load_1120s_specs) models the §179 dollar limit (line 5) and the business-income
limitation (line 11), but is SILENT on:
  - line 10  — carryover of disallowed deduction FROM the prior year
  - line 13  — carryover of disallowed deduction TO next year
and its line-12 description was wrong ("smaller of line 9 or line 11"). The real
2025 Form 4562 line 12 = "Add lines 9 and 10, but don't enter more than line 11."

This blocks the 1040 proforma unit, which carries a prior-year §179 carryover
forward into the current-year return (Taxpayer.sec_179_carryover_prior → line 10),
where it must be consumed into the current-year deduction (line 12) and any unused
remainder re-carried (line 13). Ken chose "amend RS spec first, then build inline"
(AskUserQuestion 2026-06-22).

This loader AMENDS the existing multi-entity 4562 form ADDITIVELY:
  - it LOOKS UP the existing TaxForm (never re-creates it / never touches
    entity_types — the form serves 1120S/1065/1120/1040)
  - adds the fact `section_179_carryover_prior`
  - upserts line_map L10 (input), L11 (enriched), L12 (fixed), L13 (new)
  - adds rules R014 (line 12 consumption) + R015 (line 13) + enriches R011
  - adds diagnostic D014 (carryover to next year generated — proforma continuity)
  - adds carryover test scenarios
  - adds verbatim L10/L11/L12/L13 excerpts on the existing IRS_2025_4562_INSTR_FULL
  - stages flow assertions FA-4562-179-01..04

LAW VERIFIED 2026-06-22 against the actual 2025 IRS PDF + instructions (NOT memory):
  - Form face (resources/irs_forms/2025/f4562.pdf, pymupdf dump):
      L9  Tentative deduction. Enter the smaller of line 5 or line 8.
      L10 Carryover of disallowed deduction from line 13 of your 2024 Form 4562.
      L11 Business income limitation. Enter the smaller of business income (not
          less than zero) or line 5. See instructions.
      L12 Section 179 expense deduction. Add lines 9 and 10, but don't enter more
          than line 11.
      L13 Carryover of disallowed deduction to 2026. Add lines 9 and 10, less line 12.
  - Instructions for Form 4562 (2025) — Line 11 "Individuals": "Enter the smaller of
    line 5 or the total taxable income from any trade or business you actively
    conducted, computed without regard to any section 179 expense deduction, the
    deduction for one-half of self-employment taxes under section 164(f), or any net
    operating loss deduction. Also, include all wages, salaries, tips, and other
    compensation you earned as an employee (from Form 1040, line 1a). ... If you are
    married filing a joint return, combine the total taxable incomes for you and your
    spouse." (fetched https://www.irs.gov/instructions/i4562 2026-06-22).

Idempotent: update_or_create / get_or_create throughout. Safe to re-run.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from sources.models import (
    AuthorityExcerpt,
    AuthoritySource,
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
# SAFETY GUARD — flip ONLY after Ken's in-session review walk (the verified
# L10-L13 wording off the 2025 PDF, the line-11 "Individuals" business-income
# definition incl. W-2 wages, the carryover consumption rules R014/R015, the
# D014 proforma-continuity diagnostic, the 3 new instruction excerpts).
# Until then the command refuses to write to the DB (zero writes while False).
#
# FLIPPED 2026-06-22 — Ken APPROVED the review walk in-session ("Approve & seed"):
# the verified L10-L13 wording off the 2025 Form 4562 PDF; the Line 11 Individuals
# business-income definition (active-T/B income + W-2 wages 1040 L1a, w/o §179 /
# §164(f) / NOL, MFJ combine); R014 [L12 = min(L9+L10, L11)] / R015 [L13 =
# (L9+L10) - L12]; D014 proforma-continuity; the 3 instruction excerpts. Math gate
# check_4562_section179_integrity.py = ALL CHECKS PASS. (Two build-leg decisions —
# the line-11 v1 component scope + the per-business carryover allocation — are
# downstream and do not change this spec.)
# ═══════════════════════════════════════════════════════════════════════════
READY_TO_SEED = True


# Target form (the EXISTING multi-entity 4562 row — looked up, never recreated).
FORM_NUMBER = "4562"
FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025


# ═══════════════════════════════════════════════════════════════════════════
# NEW FACT — the prior-year carryover (line 10)
# ═══════════════════════════════════════════════════════════════════════════

NEW_FACTS: list[dict] = [
    {"fact_key": "section_179_carryover_prior",
     "label": "§179 — carryover of disallowed deduction from prior year (line 10)",
     "data_type": "decimal", "required": False, "default_value": None, "sort_order": 6,
     "notes": ("Line 10 = the amount from line 13 of the PRIOR-year Form 4562 — §179 elected in "
               "earlier years that was disallowed by the business income limitation. Stored on the "
               "current-year return (1040 proforma carries it forward, YELLOW). Consumed into line "
               "12; any remainder re-carried on line 13.")},
]


# ═══════════════════════════════════════════════════════════════════════════
# RULES — R014 (line 12 consumption), R015 (line 13), enrich R011 (line 11)
# ═══════════════════════════════════════════════════════════════════════════

RULES: list[dict] = [
    {"rule_id": "R011", "title": "§179 business income limitation (line 11)", "rule_type": "calculation",
     "formula": "line_11 = min(line_5_dollar_limit, max(0, taxable_income_active_trade_or_business))",
     "inputs": ["section_179_dollar_limit", "taxable_income_limitation"],
     "outputs": ["section_179_business_income_limit"],
     "precedence": 2, "sort_order": 11,
     "description": (
         "Line 11. The §179 deduction cannot exceed taxable income from the ACTIVE conduct of a "
         "trade or business (line 11 = smaller of line 5 or that income, not less than zero). "
         "INDIVIDUALS (1040): total taxable income from any trade or business actively conducted "
         "(Schedule C net + Schedule F net + actively-conducted passthrough income), PLUS all wages, "
         "salaries, tips, and other compensation earned as an employee (Form 1040 line 1a), computed "
         "WITHOUT the §179 deduction, the §164(f) one-half-SE-tax deduction, or any NOL deduction; "
         "do not reduce by unreimbursed employee business expenses. MFJ: combine both spouses' "
         "totals. Excess over line 11 is disallowed and carries forward (line 13)."),
     "notes": "Individuals def verified vs Instructions for Form 4562 (2025), Line 11 Individuals."},
    {"rule_id": "R014", "title": "§179 expense deduction — tentative + prior carryover (line 12)",
     "rule_type": "calculation",
     "formula": "line_12 = min(line_9_tentative + line_10_prior_carryover, line_11_business_income_limit)",
     "inputs": ["section_179_carryover_prior", "taxable_income_limitation"],
     "outputs": ["section_179_expense_deduction"],
     "precedence": 3, "sort_order": 14,
     "description": (
         "Line 12. Section 179 expense deduction = ADD lines 9 (current-year tentative) and 10 "
         "(prior-year carryover), but do NOT enter more than line 11 (business income limitation). "
         "This is the §179 actually deducted this year. For 1040 it flows into the business that owns "
         "the assets (Schedule C line 13 / Schedule F line 14 / Schedule E); for 1120-S/1065 it is "
         "separately stated on Schedule K (not Page 1)."),
     "notes": ""},
    {"rule_id": "R015", "title": "§179 carryover of disallowed deduction to next year (line 13)",
     "rule_type": "calculation",
     "formula": "line_13 = (line_9_tentative + line_10_prior_carryover) - line_12",
     "inputs": ["section_179_carryover_prior"],
     "outputs": ["section_179_carryover_next"],
     "precedence": 4, "sort_order": 15,
     "description": (
         "Line 13. Carryover of disallowed deduction to next year = (line 9 + line 10) less line 12. "
         "When the business income limitation (line 11) caps line 12 below line 9 + line 10, the "
         "unused §179 carries to next year (becomes next year's line 10). Proforma MUST roll this "
         "value forward so the carryover is never silently lost."),
     "notes": ""},
]

RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R011", "IRS_2025_4562_INSTR_FULL", "primary", "Line 11 Individuals — active-T/B income + W-2 wages, w/o §179/§164(f)/NOL"),
    ("R011", "IRC_179", "secondary", "§179(b)(3)(A) — taxable income limitation"),
    ("R014", "IRS_2025_4562_INSTR_FULL", "primary", "Line 12 — add lines 9 and 10, not more than line 11"),
    ("R014", "IRC_179", "secondary", "§179(a)/(b) — current-year expense"),
    ("R015", "IRS_2025_4562_INSTR_FULL", "primary", "Line 13 — carryover of disallowed deduction to next year"),
    ("R015", "IRC_179", "secondary", "§179(b)(3)(B) — carryover of disallowed deduction"),
]


# ═══════════════════════════════════════════════════════════════════════════
# LINE MAP — upsert L10 (new) / L11 (enriched) / L12 (FIXED) / L13 (new)
# sort_order normalized to the line number (was L11=10, L12=11 — fix the drift).
# ═══════════════════════════════════════════════════════════════════════════

LINES: list[dict] = [
    {"line_number": "10",
     "description": "Carryover of disallowed deduction from line 13 of the prior-year Form 4562",
     "calculation": "", "source_facts": ["section_179_carryover_prior"], "source_rules": [],
     "destination_form": None, "line_type": "input", "sort_order": 10,
     "notes": "Prior-year line 13. 1040 proforma carries this forward (Taxpayer.sec_179_carryover_prior)."},
    {"line_number": "11",
     "description": "Business income limitation — smaller of business income (not less than zero) or line 5",
     "calculation": "min(line_5, max(0, active_trade_or_business_taxable_income))",
     "source_facts": ["taxable_income_limitation"], "source_rules": ["R011"],
     "destination_form": None, "line_type": "input", "sort_order": 11,
     "notes": "Individuals: active-T/B income + W-2 wages (1040 L1a), w/o §179/§164(f)/NOL; MFJ combine."},
    {"line_number": "12",
     "description": "§179 expense deduction — add lines 9 and 10, but not more than line 11",
     "calculation": "min(line_9 + line_10, line_11)", "source_facts": [], "source_rules": ["R001", "R014"],
     "destination_form": "1120-S Sch K L11 / 1065 Sch K L12 / 1040 Sch C L13·Sch E·Sch F L14 / 1120 Page 1",
     "line_type": "calculated", "sort_order": 12, "notes": ""},
    {"line_number": "13",
     "description": "Carryover of disallowed deduction to next year — add lines 9 and 10, less line 12",
     "calculation": "(line_9 + line_10) - line_12", "source_facts": [], "source_rules": ["R015"],
     "destination_form": "Next-year Form 4562 line 10", "line_type": "calculated", "sort_order": 13,
     "notes": "Proforma rolls this to next year's line 10."},
]


# ═══════════════════════════════════════════════════════════════════════════
# DIAGNOSTIC — carryover to next year generated (proforma continuity)
# ═══════════════════════════════════════════════════════════════════════════

DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D014", "title": "§179 carryover to next year generated", "severity": "info",
     "condition": "(line_9 + line_10) > line_11   (i.e. line_13 > 0)",
     "message": ("Part of the section 179 election (including any prior-year carryover) is disallowed "
                 "by the business income limitation and carries forward to next year (Form 4562 line 13). "
                 "Record it so it rolls to next year's line 10."),
     "notes": "Proforma continuity — line 13 must become next year's line 10. Companion to D011."},
]


# ═══════════════════════════════════════════════════════════════════════════
# TEST SCENARIOS — the carryover consumption math
# ═══════════════════════════════════════════════════════════════════════════

SCENARIOS: list[dict] = [
    {"scenario_name": "§179 prior-year carryover fully absorbed (income sufficient)", "scenario_type": "normal",
     "inputs": {"line_9_tentative": 10000, "section_179_carryover_prior": 5000, "line_11_business_income_limit": 50000},
     "expected_outputs": {"section_179_expense_deduction": 15000, "section_179_carryover_next": 0},
     "notes": "L12 = min(10,000 + 5,000, 50,000) = 15,000. L13 = 15,000 - 15,000 = 0.", "sort_order": 20},
    {"scenario_name": "§179 prior-year carryover income-limited — new carryover", "scenario_type": "edge",
     "inputs": {"line_9_tentative": 10000, "section_179_carryover_prior": 5000, "line_11_business_income_limit": 12000},
     "expected_outputs": {"section_179_expense_deduction": 12000, "section_179_carryover_next": 3000},
     "notes": "L9+L10 = 15,000, capped at L11 12,000 → deduct 12,000, carry 3,000 to next year.", "sort_order": 21},
    {"scenario_name": "§179 zero prior carryover — regression (line 12 unchanged)", "scenario_type": "normal",
     "inputs": {"line_9_tentative": 8000, "section_179_carryover_prior": 0, "line_11_business_income_limit": 50000},
     "expected_outputs": {"section_179_expense_deduction": 8000, "section_179_carryover_next": 0},
     "notes": "No carryover: L12 = min(8,000, 50,000) = 8,000; L13 = 0. Pre-amendment behavior preserved.", "sort_order": 22},
    {"scenario_name": "§179 carryover + current tentative both income-limited", "scenario_type": "edge",
     "inputs": {"line_9_tentative": 20000, "section_179_carryover_prior": 10000, "line_11_business_income_limit": 5000},
     "expected_outputs": {"section_179_expense_deduction": 5000, "section_179_carryover_next": 25000},
     "notes": "L9+L10 = 30,000, capped at L11 5,000 → deduct 5,000, carry 25,000.", "sort_order": 23},
    {"scenario_name": "§179 business income limitation zero — full carryover", "scenario_type": "edge",
     "inputs": {"line_9_tentative": 12000, "section_179_carryover_prior": 4000, "line_11_business_income_limit": 0},
     "expected_outputs": {"section_179_expense_deduction": 0, "section_179_carryover_next": 16000},
     "notes": "No active-business income → L11 = 0 → deduct nothing, carry the full 16,000.", "sort_order": 24},
]


# ═══════════════════════════════════════════════════════════════════════════
# NEW EXCERPTS on the EXISTING IRS_2025_4562_INSTR_FULL source
# ═══════════════════════════════════════════════════════════════════════════

EXISTING_SOURCES_TO_REFERENCE: list[str] = ["IRS_2025_4562_INSTR_FULL", "IRC_179"]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = [
    ("IRS_2025_4562_INSTR_FULL", {
        "excerpt_label": "Part I Line 10 — carryover of disallowed deduction (from prior year)",
        "location_reference": "Instructions for Form 4562 (2025), Part I, Line 10",
        "excerpt_text": (
            "Line 10. Enter the carryover of any disallowed deduction from prior years. This is the "
            "amount of section 179 property, if any, you elected to expense in previous years that was "
            "not allowed as a deduction because of the business income limitation. If you filed Form "
            "4562 for 2024, enter the amount from line 13 of your 2024 Form 4562."),
        "summary_text": "L10 = prior-year line 13 (§179 disallowed by the business income limit, carried in).",
        "is_key_excerpt": True,
    }),
    ("IRS_2025_4562_INSTR_FULL", {
        "excerpt_label": "Part I Line 11 — business income limitation (Individuals)",
        "location_reference": "Instructions for Form 4562 (2025), Part I, Line 11 — Individuals",
        "excerpt_text": (
            "Line 11. The total cost you can deduct is limited to your taxable income from the active "
            "conduct of a trade or business during the year. You are considered to actively conduct a "
            "trade or business only if you meaningfully participate in its management or operations. A "
            "mere passive investor is not considered to actively conduct a trade or business. "
            "Individuals. Enter the smaller of line 5 or the total taxable income from any trade or "
            "business you actively conducted, computed without regard to any section 179 expense "
            "deduction, the deduction for one-half of self-employment taxes under section 164(f), or "
            "any net operating loss deduction. Also, include all wages, salaries, tips, and other "
            "compensation you earned as an employee (from Form 1040, line 1a). Do not reduce this "
            "amount by unreimbursed employee business expenses. If you are married filing a joint "
            "return, combine the total taxable incomes for you and your spouse."),
        "summary_text": ("L11 (individuals) = min(L5, active-T/B taxable income + W-2 wages 1040 L1a; "
                         "w/o §179, §164(f) ½-SE, NOL; not < 0; MFJ combine)."),
        "is_key_excerpt": True,
    }),
    ("IRS_2025_4562_INSTR_FULL", {
        "excerpt_label": "Part I Lines 12-13 — §179 deduction and carryover to next year",
        "location_reference": "Form 4562 (2025) face, Part I, lines 12-13",
        "excerpt_text": (
            "Line 12. Section 179 expense deduction. Add lines 9 and 10, but don't enter more than "
            "line 11. Line 13. Carryover of disallowed deduction to 2026. Add lines 9 and 10, less "
            "line 12."),
        "summary_text": "L12 = min(L9+L10, L11). L13 = (L9+L10) - L12.",
        "is_key_excerpt": True,
    }),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS (staged in tts-tax-app until the assertions build leg)
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-4562-179-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "§179 prior-year carryover (Taxpayer field) -> Form 4562 line 10",
     "description": ("Validates the proforma carry. Taxpayer.sec_179_carryover_prior renders to Form 4562 "
                     "line 10. Bug it catches: the carried value not reaching line 10 (silently lost)."),
     "definition": {"kind": "flow_assertion", "form": "4562",
                    "source": "section_179_carryover_prior", "must_write_to": ["4562.10"]},
     "sort_order": 1},
    {"assertion_id": "FA-4562-179-02", "assertion_type": "flow_assertion", "entity_types": ["1040", "1120S", "1065", "1120"],
     "title": "Form 4562 line 12 = min(line 9 + line 10, line 11)",
     "description": ("Validates R014. Section 179 expense deduction adds the current-year tentative (L9) and "
                     "the prior-year carryover (L10), capped at the business income limitation (L11). Bug it "
                     "catches: omitting L10 (the pre-amendment bug), or not capping at L11."),
     "definition": {"kind": "formula_check", "form": "4562",
                    "formula": "line_12 == min(line_9 + line_10, line_11)"},
     "sort_order": 2},
    {"assertion_id": "FA-4562-179-03", "assertion_type": "flow_assertion", "entity_types": ["1040", "1120S", "1065", "1120"],
     "title": "Form 4562 line 13 = (line 9 + line 10) - line 12 (carryover to next year)",
     "description": ("Validates R015. The disallowed §179 carries forward. Bug it catches: dropping the "
                     "carryover (silently losing it) when L11 limits the deduction."),
     "definition": {"kind": "formula_check", "form": "4562",
                    "formula": "line_13 == (line_9 + line_10) - line_12"},
     "sort_order": 3},
    {"assertion_id": "FA-4562-179-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "§179 line 12 deduction flows into the owning business (Sch C L13 / Sch F L14)",
     "description": ("Validates that the consumed §179 (line 12, incl. the prior-year carryover) reaches the "
                     "business that owns the assets — Schedule C line 13 or Schedule F line 14 — via "
                     "aggregate_depreciation. Bug it catches: the carryover increasing line 12 but not the "
                     "business net (so AGI is overstated)."),
     "definition": {"kind": "flow_assertion", "form": "4562",
                    "source_line": "12", "must_write_to": ["SCHEDULE_C.13", "SCHEDULE_F.14"]},
     "sort_order": 4},
]


# ═══════════════════════════════════════════════════════════════════════════
# Command
# ═══════════════════════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = (
        "Amend Form 4562 Part I with the §179 prior-year carryover (lines 10/12/13) "
        "+ the line-11 Individuals business-income definition. AMENDS the existing "
        "multi-entity 4562 form additively (entity_types untouched). Refuses to seed "
        "until Ken sets READY_TO_SEED=True."
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()

        self.stdout.write(self.style.MIGRATE_HEADING(
            "\nAmend Form 4562 — §179 prior-year carryover (lines 10/12/13)\n"))

        form = self._get_existing_form()
        self._upsert_facts(form, NEW_FACTS)
        rules = self._upsert_rules(form, RULES)
        self._upsert_authority_links(rules, RULE_LINKS)
        self._upsert_lines(form, LINES)
        self._upsert_diagnostics(form, DIAGNOSTICS)
        self._upsert_tests(form, SCENARIOS)
        self._load_new_excerpts_on_existing()
        self._load_flow_assertions()
        self._report_totals(form)

    # ─────────────────────────────────────────────────────────────────────────
    # Safety guard
    # ─────────────────────────────────────────────────────────────────────────

    def _guard_against_hollow_seed(self):
        empty = [name for name, seq in (
            ("NEW_FACTS", NEW_FACTS), ("RULES", RULES), ("LINES", LINES),
            ("DIAGNOSTICS", DIAGNOSTICS), ("SCENARIOS", SCENARIOS),
            ("RULE_LINKS", RULE_LINKS), ("NEW_EXCERPTS_ON_EXISTING", NEW_EXCERPTS_ON_EXISTING),
            ("FLOW_ASSERTIONS", FLOW_ASSERTIONS),
        ) if not seq]

        # id-length guard (FormDiagnostic.diagnostic_id / FormRule.rule_id /
        # FormLine.line_number are varchar(20) — the Schedule F seed gotcha).
        too_long = []
        for d in DIAGNOSTICS:
            if len(d["diagnostic_id"]) > 20:
                too_long.append(f"diagnostic_id {d['diagnostic_id']}")
        for r in RULES:
            if len(r["rule_id"]) > 20:
                too_long.append(f"rule_id {r['rule_id']}")
        for ln in LINES:
            if len(ln["line_number"]) > 20:
                too_long.append(f"line_number {ln['line_number']}")

        if not READY_TO_SEED or empty or too_long:
            still_empty = "\n  ".join(f"- {n}" for n in empty) or "(all populated)"
            length_issues = "\n  ".join(f"- {n}" for n in too_long) or "(none)"
            raise CommandError(
                "\n"
                "REFUSING TO SEED 4562 §179 carryover amendment: not cleared to seed.\n"
                "\n"
                "Content is authored, but seeding is gated until Ken reviews the packet\n"
                "(the verified L10-L13 wording off the 2025 Form 4562 PDF; the Line 11\n"
                "Individuals business-income definition — active-T/B income + W-2 wages\n"
                "(1040 line 1a), w/o §179/§164(f)/NOL, MFJ combine; the carryover rules\n"
                "R014 [L12 = min(L9+L10, L11)] / R015 [L13 = (L9+L10) - L12]; the D014\n"
                "proforma-continuity diagnostic; the 3 new instruction excerpts) and flips\n"
                "the sentinel.\n"
                "\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True to proceed)\n"
                "\n"
                "NOTE: this AMENDS the existing multi-entity 4562 form ADDITIVELY — it looks\n"
                "up the form and never re-creates it (entity_types 1120S/1065/1120/1040 are\n"
                "untouched). The existing R001/R010-R013 + D010-D013 are preserved.\n"
                "\n"
                f"Currently empty / placeholder:\n  {still_empty}\n"
                f"\nID-length (varchar(20)) issues:\n  {length_issues}\n"
                "\n"
                "To proceed: review the module-level data lists, then set READY_TO_SEED\n"
                "= True. Idempotent via update_or_create — safe to re-run after edits."
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Form lookup (NEVER recreate — preserve entity_types)
    # ─────────────────────────────────────────────────────────────────────────

    def _get_existing_form(self) -> TaxForm:
        form = (
            TaxForm.objects.filter(
                form_number=FORM_NUMBER, jurisdiction=FORM_JURISDICTION, tax_year=FORM_TAX_YEAR,
            )
            .order_by("version")
            .first()
        )
        if not form:
            raise CommandError(
                f"Form {FORM_NUMBER} ({FORM_JURISDICTION} {FORM_TAX_YEAR}) not found — run "
                "load_1120s_specs / load_remaining_1120s first. This loader only AMENDS it."
            )
        self.stdout.write(
            f"Amending {FORM_NUMBER} v{form.version} (entity_types={form.entity_types} — untouched)")
        return form

    # ─────────────────────────────────────────────────────────────────────────
    # Upsert helpers (mirror load_1040_schedule_f.py)
    # ─────────────────────────────────────────────────────────────────────────

    def _upsert_facts(self, form, facts):
        for f in facts:
            f = dict(f)
            FormFact.objects.update_or_create(
                tax_form=form, fact_key=f.pop("fact_key"), defaults=f,
            )
        self.stdout.write(f"  {len(facts)} facts")

    def _upsert_rules(self, form, rules_data) -> dict:
        created = {}
        for r in rules_data:
            r = dict(r)
            rule, _ = FormRule.objects.update_or_create(
                tax_form=form, rule_id=r.pop("rule_id"), defaults=r,
            )
            created[rule.rule_id] = rule
        self.stdout.write(f"  {len(created)} rules (R011 enriched; R014/R015 new)")
        return created

    def _upsert_authority_links(self, rules, rule_links):
        ct = 0
        for rule_id, source_code, level, note in rule_links:
            rule = rules.get(rule_id)
            source = AuthoritySource.objects.filter(source_code=source_code).first()
            if rule and source:
                RuleAuthorityLink.objects.get_or_create(
                    form_rule=rule, authority_source=source,
                    defaults={"support_level": level, "relevance_note": note},
                )
                ct += 1
            elif not source:
                self.stdout.write(self.style.WARNING(f"  source {source_code} not found — link skipped"))
        self.stdout.write(f"  {ct} authority links")

    def _upsert_lines(self, form, lines):
        for ln in lines:
            ln = dict(ln)
            FormLine.objects.update_or_create(
                tax_form=form, line_number=ln.pop("line_number"), defaults=ln,
            )
        self.stdout.write(f"  {len(lines)} lines (L10/L13 new; L11/L12 corrected)")

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

    def _load_new_excerpts_on_existing(self):
        ct = 0
        for code, exc in NEW_EXCERPTS_ON_EXISTING:
            src = AuthoritySource.objects.filter(source_code=code).first()
            if not src:
                self.stdout.write(self.style.WARNING(f"  source {code} not found — excerpt skipped"))
                continue
            exc = dict(exc)
            AuthorityExcerpt.objects.update_or_create(
                authority_source=src, excerpt_label=exc["excerpt_label"], defaults=exc,
            )
            ct += 1
        self.stdout.write(f"  {ct} new excerpts on existing sources")

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

    def _report_totals(self, form):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS(
            f"4562 §179 carryover amendment seeded onto form v{form.version}."))
        self.stdout.write(
            f"  facts +{len(NEW_FACTS)} · rules +{len(RULES)} (R011 enriched) · "
            f"lines {len(LINES)} (L10/L13 new) · diagnostics +{len(DIAGNOSTICS)} · "
            f"tests +{len(SCENARIOS)} · excerpts +{len(NEW_EXCERPTS_ON_EXISTING)} · "
            f"FA {len(FLOW_ASSERTIONS)}")
        self.stdout.write("=" * 60)
