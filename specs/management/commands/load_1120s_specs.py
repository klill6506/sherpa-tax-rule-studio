"""Load 1120-S family form specs — Schedule K, K-1, Schedule D, Form 8949, Form 4562.

Idempotent: uses update_or_create throughout. Safe to re-run.
Creates authority sources not yet in load_all_federal, then loads full specs
(facts, rules, authority links, lines, diagnostics, tests) for each form.
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
    FormDiagnostic,
    FormFact,
    FormLine,
    FormRule,
    TaxForm,
    TestScenario,
)

from ._1120s_sources import EXISTING_SOURCE_CODES, NEW_INSTRUCTION_SOURCES, NEW_IRC_SOURCES


class Command(BaseCommand):
    help = "Load 1120-S family form specs (Schedule K, K-1, Schedule D, 8949, 4562)"

    def handle(self, *_args, **_options):
        with transaction.atomic():
            sources = self._load_sources()
            self._load_schedule_k(sources)
            self._load_k1(sources)
            self._load_schedule_d(sources)
            self._load_form_8949(sources)
            self._load_form_4562(sources)
        self._report_totals()

    # ─────────────────────────────────────────────────────────────────────────
    # Authority sources
    # ─────────────────────────────────────────────────────────────────────────

    def _load_sources(self) -> dict[str, AuthoritySource]:
        """Load new sources and collect existing ones into a single lookup dict."""
        sources: dict[str, AuthoritySource] = {}

        # Create new IRC sections + instruction sources
        for src_data in NEW_IRC_SOURCES + NEW_INSTRUCTION_SOURCES:
            src_data = dict(src_data)  # don't mutate module-level data
            excerpts_data = src_data.pop("excerpts", [])
            topic_codes = src_data.pop("topics", [])
            src_data.pop("form_links", None)
            source, _ = AuthoritySource.objects.update_or_create(
                source_code=src_data["source_code"], defaults=src_data,
            )
            sources[source.source_code] = source
            for exc in excerpts_data:
                exc = dict(exc)
                exc.pop("topic_tags", None)
                AuthorityExcerpt.objects.update_or_create(
                    authority_source=source, excerpt_label=exc["excerpt_label"], defaults=exc,
                )
            for tc in topic_codes:
                topic = AuthorityTopic.objects.filter(topic_code=tc).first()
                if topic:
                    AuthoritySourceTopic.objects.get_or_create(
                        authority_source=source, authority_topic=topic,
                    )

        # Collect existing sources
        for code in EXISTING_SOURCE_CODES:
            src = AuthoritySource.objects.filter(source_code=code).first()
            if src:
                sources[code] = src

        self.stdout.write(f"Sources ready: {len(sources)} ({len(NEW_IRC_SOURCES) + len(NEW_INSTRUCTION_SOURCES)} new/updated)")
        return sources

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _upsert_form(self, form_number, form_title, entity_types, notes="") -> TaxForm:
        form, created = TaxForm.objects.update_or_create(
            form_number=form_number, jurisdiction="FED", tax_year=2025, version=1,
            defaults={"form_title": form_title, "entity_types": entity_types,
                       "status": "draft", "notes": notes},
        )
        self.stdout.write(f"{'Created' if created else 'Updated'} {form_number}")
        return form

    def _upsert_facts(self, form, facts_data):
        for f in facts_data:
            f = dict(f)
            key = f.pop("fact_key")
            FormFact.objects.update_or_create(tax_form=form, fact_key=key, defaults=f)
        self.stdout.write(f"  {len(facts_data)} facts")

    def _upsert_rules(self, form, rules_data) -> dict[str, FormRule]:
        created = {}
        for r in rules_data:
            r = dict(r)
            rid = r.pop("rule_id")
            rule, _ = FormRule.objects.update_or_create(
                tax_form=form, rule_id=rid, defaults=r,
            )
            created[rid] = rule
        self.stdout.write(f"  {len(created)} rules")
        return created

    def _upsert_links(self, rules, sources, links_data):
        count = 0
        for rule_id, source_code, level, note in links_data:
            rule = rules.get(rule_id)
            source = sources.get(source_code)
            if rule and source:
                RuleAuthorityLink.objects.get_or_create(
                    form_rule=rule, authority_source=source,
                    defaults={"support_level": level, "relevance_note": note},
                )
                count += 1
        self.stdout.write(f"  {count} authority links")

    def _upsert_lines(self, form, lines_data):
        for ln in lines_data:
            ln = dict(ln)
            num = ln.pop("line_number")
            FormLine.objects.update_or_create(
                tax_form=form, line_number=num, defaults=ln,
            )
        self.stdout.write(f"  {len(lines_data)} lines")

    def _upsert_diagnostics(self, form, diags_data):
        for d in diags_data:
            d = dict(d)
            did = d.pop("diagnostic_id")
            FormDiagnostic.objects.update_or_create(
                tax_form=form, diagnostic_id=did, defaults=d,
            )
        self.stdout.write(f"  {len(diags_data)} diagnostics")

    def _upsert_tests(self, form, tests_data):
        for t in tests_data:
            t = dict(t)
            name = t.pop("scenario_name")
            TestScenario.objects.update_or_create(
                tax_form=form, scenario_name=name, defaults=t,
            )
        self.stdout.write(f"  {len(tests_data)} test scenarios")

    def _upsert_form_links(self, form_code, sources, links):
        for source_code, link_type in links:
            source = sources.get(source_code)
            if source:
                AuthorityFormLink.objects.get_or_create(
                    authority_source=source, form_code=form_code, link_type=link_type,
                    defaults={"note": f"{source_code} → {form_code}"},
                )

    # ─────────────────────────────────────────────────────────────────────────
    # Form 1: Schedule K (Form 1120-S)
    # ─────────────────────────────────────────────────────────────────────────

    def _load_schedule_k(self, sources):
        form = self._upsert_form(
            "SCH_K_1120S",
            "Schedule K — Shareholders' Pro Rata Share Items (Form 1120-S)",
            ["1120S"],
            notes="Heart of the S-Corp return. All income/deduction/credit items flow through K before K-1 allocation.",
        )

        self._upsert_facts(form, [
            # Income/Loss (K Lines 1-10)
            {"fact_key": "ordinary_business_income", "label": "Ordinary business income (loss) — from Page 1 Line 21", "data_type": "decimal", "required": True, "sort_order": 1},
            {"fact_key": "net_rental_real_estate_income", "label": "Net rental real estate income (loss) — from Form 8825", "data_type": "decimal", "sort_order": 2},
            {"fact_key": "other_net_rental_income", "label": "Other net rental income (loss)", "data_type": "decimal", "sort_order": 3},
            {"fact_key": "interest_income", "label": "Interest income", "data_type": "decimal", "sort_order": 4},
            {"fact_key": "dividend_income", "label": "Ordinary dividends", "data_type": "decimal", "sort_order": 5},
            {"fact_key": "qualified_dividends", "label": "Qualified dividends", "data_type": "decimal", "sort_order": 6},
            {"fact_key": "royalties", "label": "Royalties", "data_type": "decimal", "sort_order": 7},
            {"fact_key": "net_short_term_capital_gain", "label": "Net short-term capital gain (loss) — from Schedule D", "data_type": "decimal", "sort_order": 8},
            {"fact_key": "net_long_term_capital_gain", "label": "Net long-term capital gain (loss) — from Schedule D", "data_type": "decimal", "sort_order": 9},
            {"fact_key": "net_section_1231_gain", "label": "Net §1231 gain (loss) — from Form 4797 Part I", "data_type": "decimal", "sort_order": 10},
            {"fact_key": "other_income", "label": "Other income (loss)", "data_type": "decimal", "sort_order": 11},
            # Deductions (K Lines 11-12)
            {"fact_key": "section_179_deduction", "label": "§179 deduction — from Form 4562", "data_type": "decimal", "sort_order": 12},
            {"fact_key": "charitable_contributions_cash", "label": "Charitable contributions — cash", "data_type": "decimal", "sort_order": 13},
            {"fact_key": "charitable_contributions_noncash", "label": "Charitable contributions — noncash", "data_type": "decimal", "sort_order": 14},
            {"fact_key": "investment_interest_expense", "label": "Investment interest expense — §163(d)", "data_type": "decimal", "sort_order": 15},
            {"fact_key": "other_deductions", "label": "Other deductions", "data_type": "decimal", "sort_order": 16},
            # Credits (K Line 13)
            {"fact_key": "low_income_housing_credit", "label": "Low-income housing credit — §42", "data_type": "decimal", "sort_order": 17},
            {"fact_key": "rehabilitation_credit", "label": "Qualified rehabilitation expenditures", "data_type": "decimal", "sort_order": 18},
            {"fact_key": "other_rental_credits", "label": "Other rental credits", "data_type": "decimal", "sort_order": 19},
            {"fact_key": "foreign_tax_credit", "label": "Foreign tax credit", "data_type": "decimal", "sort_order": 20},
            {"fact_key": "other_credits", "label": "Other credits", "data_type": "decimal", "sort_order": 21},
            # Other Items (K Lines 14-17)
            {"fact_key": "tax_exempt_interest", "label": "Tax-exempt interest income", "data_type": "decimal", "sort_order": 22},
            {"fact_key": "other_tax_exempt_income", "label": "Other tax-exempt income", "data_type": "decimal", "sort_order": 23},
            {"fact_key": "nondeductible_expenses", "label": "Nondeductible expenses", "data_type": "decimal", "sort_order": 24},
            {"fact_key": "distributions_cash", "label": "Distributions — cash and marketable securities", "data_type": "decimal", "sort_order": 25},
            {"fact_key": "distributions_property", "label": "Distributions — other property", "data_type": "decimal", "sort_order": 26},
            {"fact_key": "investment_income", "label": "Investment income for Form 4952", "data_type": "decimal", "sort_order": 27},
            {"fact_key": "investment_expenses", "label": "Investment expenses for Form 4952", "data_type": "decimal", "sort_order": 28},
            {"fact_key": "qbi_ordinary_income", "label": "§199A QBI — ordinary income component", "data_type": "decimal", "sort_order": 29},
            {"fact_key": "qbi_w2_wages", "label": "§199A QBI — W-2 wages", "data_type": "decimal", "sort_order": 30},
            {"fact_key": "qbi_ubia", "label": "§199A QBI — UBIA of qualified property", "data_type": "decimal", "sort_order": 31},
            {"fact_key": "qbi_sstb_indicator", "label": "§199A — Specified service trade or business (SSTB) indicator", "data_type": "boolean", "sort_order": 32},
            # Allocation inputs
            {"fact_key": "total_shares_outstanding", "label": "Total shares outstanding", "data_type": "integer", "required": True, "sort_order": 40},
            {"fact_key": "days_in_year", "label": "Days in tax year", "data_type": "integer", "default_value": "365", "sort_order": 41},
        ])

        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "Ordinary business income passthrough", "rule_type": "routing",
             "formula": "ordinary_business_income",
             "inputs": ["ordinary_business_income"], "outputs": ["k_line_1"],
             "description": "Page 1 Line 21 flows directly to Schedule K Line 1. No modification.",
             "sort_order": 1, "precedence": 1},

            {"rule_id": "R002", "title": "Rental real estate from Form 8825", "rule_type": "routing",
             "formula": "net_rental_real_estate_income",
             "inputs": ["net_rental_real_estate_income"], "outputs": ["k_line_2"],
             "description": "Net income/loss from Form 8825 flows to K Line 2.",
             "sort_order": 2, "precedence": 1},

            {"rule_id": "R003", "title": "Capital gains routing", "rule_type": "routing",
             "formula": "net_short_term_capital_gain → K Line 7; net_long_term_capital_gain → K Line 8a",
             "inputs": ["net_short_term_capital_gain", "net_long_term_capital_gain"],
             "outputs": ["k_line_7", "k_line_8a"],
             "description": "Net STCG → K Line 7, Net LTCG → K Line 8a. From Schedule D.",
             "sort_order": 3, "precedence": 1},

            {"rule_id": "R004", "title": "Section 1231 gain routing", "rule_type": "routing",
             "formula": "net_section_1231_gain",
             "inputs": ["net_section_1231_gain"], "outputs": ["k_line_9"],
             "description": "Net §1231 gain from 4797 Part I → K Line 9. EXCESS gain after recapture. Ordinary recapture goes to Page 1 Line 4.",
             "sort_order": 4, "precedence": 1},

            {"rule_id": "R005", "title": "Section 179 routing — separately stated", "rule_type": "routing",
             "formula": "section_179_deduction",
             "inputs": ["section_179_deduction"], "outputs": ["k_line_11"],
             "description": "§179 deduction from Form 4562 → K Line 11. NOT Page 1. This is a separately stated item that passes through to shareholders. Common error: §179 should NOT reduce ordinary income on Page 1.",
             "sort_order": 5, "precedence": 1},

            {"rule_id": "R006", "title": "Charitable contributions — separately stated", "rule_type": "routing",
             "formula": "charitable_contributions_cash + charitable_contributions_noncash",
             "inputs": ["charitable_contributions_cash", "charitable_contributions_noncash"],
             "outputs": ["k_line_12a", "k_line_12b"],
             "description": "Charitable contributions → K Line 12a (cash) and 12b (noncash). Separately stated, NOT deducted on Page 1.",
             "sort_order": 6, "precedence": 1},

            {"rule_id": "R007", "title": "QBI information routing", "rule_type": "routing",
             "formula": "qbi_ordinary_income, qbi_w2_wages, qbi_ubia, qbi_sstb_indicator → K Line 17",
             "inputs": ["qbi_ordinary_income", "qbi_w2_wages", "qbi_ubia", "qbi_sstb_indicator"],
             "outputs": ["k_line_17_qbi"],
             "description": "§199A QBI items flow through K Line 17. Includes ordinary income, W-2 wages, UBIA of qualified property, SSTB indicator.",
             "sort_order": 7, "precedence": 1},

            {"rule_id": "R008", "title": "Pro rata allocation base", "rule_type": "calculation",
             "formula": "item_amount * (shareholder_shares / total_shares) * (days_owned / days_in_year)",
             "inputs": ["total_shares_outstanding", "days_in_year"],
             "outputs": ["shareholder_allocation"],
             "description": "Each K line item is allocated to shareholders based on pro rata share (daily ownership percentage). Unlike partnerships, S-Corps cannot do special allocations — must be pro rata per share per day.",
             "sort_order": 8, "precedence": 10},
        ])

        self._upsert_links(rules, sources, [
            ("R001", "IRS_2025_1120S_INSTR", "primary", "Schedule K Line 1 — ordinary income from page 1 line 21"),
            ("R002", "IRS_2025_1120S_INSTR", "primary", "Schedule K Line 2 — rental real estate from Form 8825"),
            ("R003", "IRS_2025_1120S_INSTR", "primary", "Schedule K Lines 7-8 — capital gains from Schedule D"),
            ("R003", "IRS_2025_1120S_SCHD_INSTR", "secondary", "Schedule D aggregates → K lines"),
            ("R004", "IRS_2025_1120S_INSTR", "primary", "Schedule K Line 9 — §1231 gain from Form 4797"),
            ("R004", "IRS_2025_4797_INSTR", "secondary", "Form 4797 Part I provides §1231 gain"),
            ("R005", "IRC_179", "primary", "§179(d)(4) — separately stated for S-Corps"),
            ("R005", "IRS_2025_1120S_INSTR", "secondary", "Schedule K Line 11 instructions"),
            ("R005", "IRS_2025_4562_INSTR", "secondary", "Form 4562 Part I → K Line 11"),
            ("R006", "IRC_1363", "primary", "§1363(b)(2) — charitable not deducted at entity level"),
            ("R006", "IRS_2025_1120S_INSTR", "secondary", "Schedule K Line 12 instructions"),
            ("R006", "IRC_170", "secondary", "§170 — charitable contribution rules"),
            ("R007", "IRC_199A", "primary", "§199A QBI deduction — items reported on K Line 17"),
            ("R007", "IRS_2025_1120S_INSTR", "secondary", "Schedule K Line 17 — other information"),
            ("R008", "IRC_1366", "primary", "§1366(a) — pro rata share determination"),
            ("R008", "IRC_1377", "primary", "§1377(a) — per share per day allocation rule"),
        ])

        self._upsert_lines(form, [
            {"line_number": "1", "description": "Ordinary business income (loss) (page 1, line 21)", "line_type": "input", "source_facts": ["ordinary_business_income"], "source_rules": ["R001"], "destination_form": "Schedule K-1 Box 1", "sort_order": 1},
            {"line_number": "2", "description": "Net rental real estate income (loss) (Form 8825)", "line_type": "input", "source_facts": ["net_rental_real_estate_income"], "source_rules": ["R002"], "destination_form": "Schedule K-1 Box 2", "sort_order": 2},
            {"line_number": "3a", "description": "Other gross rental income (loss)", "line_type": "input", "source_facts": ["other_net_rental_income"], "destination_form": "Schedule K-1 Box 3", "sort_order": 3},
            {"line_number": "4", "description": "Interest income", "line_type": "input", "source_facts": ["interest_income"], "destination_form": "Schedule K-1 Box 4", "sort_order": 4},
            {"line_number": "5a", "description": "Ordinary dividends", "line_type": "input", "source_facts": ["dividend_income"], "destination_form": "Schedule K-1 Box 5a", "sort_order": 5},
            {"line_number": "5b", "description": "Qualified dividends", "line_type": "input", "source_facts": ["qualified_dividends"], "destination_form": "Schedule K-1 Box 5b", "sort_order": 6},
            {"line_number": "6", "description": "Royalties", "line_type": "input", "source_facts": ["royalties"], "destination_form": "Schedule K-1 Box 6", "sort_order": 7},
            {"line_number": "7", "description": "Net short-term capital gain (loss) (Schedule D)", "line_type": "input", "source_facts": ["net_short_term_capital_gain"], "source_rules": ["R003"], "destination_form": "Schedule K-1 Box 7", "sort_order": 8},
            {"line_number": "8a", "description": "Net long-term capital gain (loss) (Schedule D)", "line_type": "input", "source_facts": ["net_long_term_capital_gain"], "source_rules": ["R003"], "destination_form": "Schedule K-1 Box 8a", "sort_order": 9},
            {"line_number": "9", "description": "Net section 1231 gain (loss) (Form 4797)", "line_type": "input", "source_facts": ["net_section_1231_gain"], "source_rules": ["R004"], "destination_form": "Schedule K-1 Box 9", "sort_order": 10},
            {"line_number": "10", "description": "Other income (loss)", "line_type": "input", "source_facts": ["other_income"], "destination_form": "Schedule K-1 Box 10", "sort_order": 11},
            {"line_number": "11", "description": "Section 179 deduction (Form 4562)", "line_type": "input", "source_facts": ["section_179_deduction"], "source_rules": ["R005"], "destination_form": "Schedule K-1 Box 11", "sort_order": 12},
            {"line_number": "12a", "description": "Charitable contributions — cash", "line_type": "input", "source_facts": ["charitable_contributions_cash"], "source_rules": ["R006"], "destination_form": "Schedule K-1 Box 12 Code A", "sort_order": 13},
            {"line_number": "12b", "description": "Charitable contributions — noncash", "line_type": "input", "source_facts": ["charitable_contributions_noncash"], "source_rules": ["R006"], "destination_form": "Schedule K-1 Box 12 Code B", "sort_order": 14},
            {"line_number": "12c", "description": "Investment interest expense — §163(d)", "line_type": "input", "source_facts": ["investment_interest_expense"], "destination_form": "Schedule K-1 Box 12 Code C", "sort_order": 15},
            {"line_number": "12d", "description": "Other deductions", "line_type": "input", "source_facts": ["other_deductions"], "destination_form": "Schedule K-1 Box 12", "sort_order": 16},
            {"line_number": "13a", "description": "Low-income housing credit (§42) — current year", "line_type": "input", "source_facts": ["low_income_housing_credit"], "destination_form": "Schedule K-1 Box 13 Code A", "sort_order": 17},
            {"line_number": "13d", "description": "Other rental real estate credits", "line_type": "input", "source_facts": ["rehabilitation_credit"], "destination_form": "Schedule K-1 Box 13 Code D", "sort_order": 18},
            {"line_number": "13f", "description": "Foreign tax credit (Form 1116)", "line_type": "input", "source_facts": ["foreign_tax_credit"], "destination_form": "Schedule K-1 Box 13 Code F", "sort_order": 19},
            {"line_number": "13g", "description": "Other credits", "line_type": "input", "source_facts": ["other_credits"], "destination_form": "Schedule K-1 Box 13 Code G", "sort_order": 20},
            {"line_number": "16a", "description": "Tax-exempt interest income", "line_type": "input", "source_facts": ["tax_exempt_interest"], "destination_form": "Schedule K-1 Box 16 Code A", "sort_order": 21},
            {"line_number": "16b", "description": "Other tax-exempt income", "line_type": "input", "source_facts": ["other_tax_exempt_income"], "destination_form": "Schedule K-1 Box 16 Code B", "sort_order": 22},
            {"line_number": "16c", "description": "Nondeductible expenses", "line_type": "input", "source_facts": ["nondeductible_expenses"], "destination_form": "Schedule K-1 Box 16 Code C", "sort_order": 23},
            {"line_number": "16d", "description": "Distributions — cash and marketable securities", "line_type": "input", "source_facts": ["distributions_cash"], "destination_form": "Schedule K-1 Box 16 Code D", "sort_order": 24},
            {"line_number": "17", "description": "Other information — §199A QBI items, investment income/expenses", "line_type": "input", "source_facts": ["qbi_ordinary_income", "qbi_w2_wages", "qbi_ubia", "qbi_sstb_indicator"], "source_rules": ["R007"], "destination_form": "Schedule K-1 Box 17", "sort_order": 25},
            {"line_number": "18", "description": "Total income (loss) — combine lines 1 through 10", "line_type": "total", "calculation": "Sum of lines 1-10", "sort_order": 26, "notes": "Informational total. Each line item flows separately to K-1."},
        ])

        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D001", "title": "§179 on Page 1", "severity": "error",
             "condition": "section_179_deduction > 0 AND ordinary_business_income appears reduced by §179",
             "message": "§179 deduction should NOT reduce ordinary income on Page 1. It must flow to Schedule K Line 11 as a separately stated item."},
            {"diagnostic_id": "D002", "title": "Charitable on Page 1", "severity": "error",
             "condition": "charitable_contributions > 0 AND deducted on Page 1",
             "message": "Charitable contributions are separately stated items. They should NOT be deducted on Page 1 — they flow to K Line 12a/12b."},
            {"diagnostic_id": "D003", "title": "Capital gain/loss not separately stated", "severity": "warning",
             "condition": "capital gains included in ordinary_business_income",
             "message": "Capital gains and losses must be separately stated on K Lines 7-8. They should not be included in ordinary business income (K Line 1)."},
            {"diagnostic_id": "D004", "title": "Missing QBI information", "severity": "warning",
             "condition": "ordinary_business_income != 0 AND qbi_ordinary_income is null",
             "message": "Ordinary business income exists but no §199A QBI information on Line 17. Most S-Corps must report QBI items for the shareholder's §199A computation."},
        ])

        self._upsert_tests(form, [
            {"scenario_name": "Basic S-Corp — ordinary income only",
             "scenario_type": "normal",
             "inputs": {"ordinary_business_income": 200000, "section_179_deduction": 50000},
             "expected_outputs": {"k_line_1": 200000, "k_line_11": 50000},
             "notes": "§179 is separate from ordinary income. K Line 1=200K, K Line 11=50K.",
             "sort_order": 1},
            {"scenario_name": "S-Corp with capital gains and recapture",
             "scenario_type": "normal",
             "inputs": {"ordinary_business_income": 150000, "net_long_term_capital_gain": 30000, "net_section_1231_gain": 20000},
             "expected_outputs": {"k_line_1": 150000, "k_line_8a": 30000, "k_line_9": 20000},
             "notes": "Each item flows to its own K line — nothing combined.",
             "sort_order": 2},
            {"scenario_name": "Pro rata allocation — 2 equal shareholders",
             "scenario_type": "normal",
             "inputs": {"ordinary_business_income": 100000, "total_shares_outstanding": 100, "shareholder_shares": 50, "days_owned": 365, "days_in_year": 365},
             "expected_outputs": {"shareholder_allocation": 50000},
             "notes": "50/100 shares × 365/365 days = 50% pro rata share.",
             "sort_order": 3},
        ])

        self._upsert_form_links("SCH_K_1120S", sources, [
            ("IRS_2025_1120S_INSTR", "governs"),
            ("IRC_1366", "governs"),
            ("IRC_1377", "governs"),
            ("IRC_1363", "governs"),
        ])

        self.stdout.write(self.style.SUCCESS("  Schedule K complete."))

    # ─────────────────────────────────────────────────────────────────────────
    # Form 2: Schedule K-1 (Form 1120-S)
    # ─────────────────────────────────────────────────────────────────────────

    def _load_k1(self, sources):
        form = self._upsert_form(
            "K1_1120S",
            "Schedule K-1 (Form 1120-S) — Shareholder's Share of Income, Deductions, Credits, etc.",
            ["1120S"],
            notes="Each shareholder receives a K-1. Boxes correspond to K lines. Subject to basis/at-risk/passive limitations.",
        )

        self._upsert_facts(form, [
            {"fact_key": "shareholder_name", "label": "Shareholder's name", "data_type": "string", "required": True, "sort_order": 1},
            {"fact_key": "shareholder_tin", "label": "Shareholder's TIN", "data_type": "string", "required": True, "sort_order": 2},
            {"fact_key": "shares_owned_start", "label": "Shares owned — beginning of year", "data_type": "integer", "sort_order": 3},
            {"fact_key": "shares_owned_end", "label": "Shares owned — end of year", "data_type": "integer", "sort_order": 4},
            {"fact_key": "ownership_percentage", "label": "Shareholder's percentage of stock ownership", "data_type": "decimal", "required": True, "sort_order": 5},
            # Box values (allocated from K)
            {"fact_key": "box_1_ordinary_income", "label": "Box 1 — Ordinary business income (loss)", "data_type": "decimal", "sort_order": 10},
            {"fact_key": "box_2_rental_real_estate", "label": "Box 2 — Net rental real estate income (loss)", "data_type": "decimal", "sort_order": 11},
            {"fact_key": "box_3_other_rental", "label": "Box 3 — Other net rental income (loss)", "data_type": "decimal", "sort_order": 12},
            {"fact_key": "box_4_interest", "label": "Box 4 — Interest income", "data_type": "decimal", "sort_order": 13},
            {"fact_key": "box_5a_ordinary_dividends", "label": "Box 5a — Ordinary dividends", "data_type": "decimal", "sort_order": 14},
            {"fact_key": "box_5b_qualified_dividends", "label": "Box 5b — Qualified dividends", "data_type": "decimal", "sort_order": 15},
            {"fact_key": "box_6_royalties", "label": "Box 6 — Royalties", "data_type": "decimal", "sort_order": 16},
            {"fact_key": "box_7_net_stcg", "label": "Box 7 — Net short-term capital gain (loss)", "data_type": "decimal", "sort_order": 17},
            {"fact_key": "box_8a_net_ltcg", "label": "Box 8a — Net long-term capital gain (loss)", "data_type": "decimal", "sort_order": 18},
            {"fact_key": "box_8b_collectibles", "label": "Box 8b — Collectibles (28%) gain (loss)", "data_type": "decimal", "sort_order": 19},
            {"fact_key": "box_8c_unrecaptured_1250", "label": "Box 8c — Unrecaptured §1250 gain", "data_type": "decimal", "sort_order": 20},
            {"fact_key": "box_9_net_1231", "label": "Box 9 — Net §1231 gain (loss)", "data_type": "decimal", "sort_order": 21},
            {"fact_key": "box_10_other_income", "label": "Box 10 — Other income (loss)", "data_type": "decimal", "sort_order": 22},
            {"fact_key": "box_11_section_179", "label": "Box 11 — §179 deduction", "data_type": "decimal", "sort_order": 23},
            {"fact_key": "box_12_other_deductions", "label": "Box 12 — Other deductions (coded)", "data_type": "decimal", "sort_order": 24},
            {"fact_key": "box_13_credits", "label": "Box 13 — Credits (coded)", "data_type": "decimal", "sort_order": 25},
            {"fact_key": "box_16a_tax_exempt_interest", "label": "Box 16a — Tax-exempt interest income", "data_type": "decimal", "sort_order": 26},
            {"fact_key": "box_16c_nondeductible", "label": "Box 16c — Nondeductible expenses", "data_type": "decimal", "sort_order": 27},
            {"fact_key": "box_16d_distributions", "label": "Box 16d — Distributions", "data_type": "decimal", "sort_order": 28},
            {"fact_key": "box_17_other_info", "label": "Box 17 — Other information (QBI, investment)", "data_type": "decimal", "sort_order": 29},
            # Basis limitation inputs
            {"fact_key": "stock_basis_boy", "label": "Stock basis — beginning of year", "data_type": "decimal", "sort_order": 40},
            {"fact_key": "debt_basis", "label": "Debt basis — direct loans to S-Corp", "data_type": "decimal", "sort_order": 41},
            {"fact_key": "at_risk_amount", "label": "At-risk amount (Form 6198)", "data_type": "decimal", "sort_order": 42},
        ])

        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "Box 1 allocation", "rule_type": "calculation",
             "formula": "k_line_1 * ownership_percentage",
             "inputs": ["ordinary_business_income", "ownership_percentage"], "outputs": ["box_1_ordinary_income"],
             "description": "Box 1 = shareholder's pro rata share of Schedule K Line 1.", "sort_order": 1, "precedence": 1},
            {"rule_id": "R002", "title": "Box 2 allocation", "rule_type": "calculation",
             "formula": "k_line_2 * ownership_percentage",
             "inputs": ["net_rental_real_estate_income", "ownership_percentage"], "outputs": ["box_2_rental_real_estate"],
             "description": "Box 2 = shareholder's share of K Line 2.", "sort_order": 2, "precedence": 1},
            {"rule_id": "R007", "title": "Box 7 allocation — STCG", "rule_type": "calculation",
             "formula": "k_line_7 * ownership_percentage",
             "inputs": ["net_short_term_capital_gain", "ownership_percentage"], "outputs": ["box_7_net_stcg"],
             "description": "Box 7 = shareholder's share of K Line 7 (net STCG).", "sort_order": 7, "precedence": 1},
            {"rule_id": "R008", "title": "Box 8a allocation — LTCG", "rule_type": "calculation",
             "formula": "k_line_8a * ownership_percentage",
             "inputs": ["net_long_term_capital_gain", "ownership_percentage"], "outputs": ["box_8a_net_ltcg"],
             "description": "Box 8a = shareholder's share of K Line 8a (net LTCG).", "sort_order": 8, "precedence": 1},
            {"rule_id": "R009", "title": "Box 9 allocation — §1231", "rule_type": "calculation",
             "formula": "k_line_9 * ownership_percentage",
             "inputs": ["net_section_1231_gain", "ownership_percentage"], "outputs": ["box_9_net_1231"],
             "description": "Box 9 = shareholder's share of K Line 9.", "sort_order": 9, "precedence": 1},
            {"rule_id": "R011", "title": "Box 11 allocation — §179", "rule_type": "calculation",
             "formula": "k_line_11 * ownership_percentage",
             "inputs": ["section_179_deduction", "ownership_percentage"], "outputs": ["box_11_section_179"],
             "description": "Box 11 = shareholder's share of §179. Subject to shareholder's own §179 limits.", "sort_order": 11, "precedence": 1},
            {"rule_id": "R017", "title": "Box 17 allocation — QBI", "rule_type": "calculation",
             "formula": "k_line_17_qbi_items * ownership_percentage",
             "inputs": ["qbi_ordinary_income", "qbi_w2_wages", "qbi_ubia", "ownership_percentage"],
             "outputs": ["box_17_other_info"],
             "description": "Box 17 QBI items = shareholder's share. Used for §199A computation on 1040.", "sort_order": 17, "precedence": 1},
            {"rule_id": "R018", "title": "Basis limitation check", "rule_type": "validation",
             "formula": "total_losses <= stock_basis_boy + debt_basis",
             "inputs": ["box_1_ordinary_income", "stock_basis_boy", "debt_basis"],
             "outputs": ["deductible_loss", "suspended_loss"],
             "description": "Shareholder cannot deduct losses exceeding stock + debt basis. Losses limited in order: (1) ordinary loss, (2) separately stated losses, (3) capital losses. Form 7203 required.",
             "notes": "NEEDS REVIEW — ordering of loss limitation categories across all box types.",
             "sort_order": 18, "precedence": 10},
            {"rule_id": "R019", "title": "At-risk limitation (post-basis)", "rule_type": "validation",
             "formula": "deductible_after_basis <= at_risk_amount",
             "inputs": ["deductible_loss", "at_risk_amount"], "outputs": ["deductible_after_at_risk"],
             "description": "After basis limitation, remaining deductible amounts are further limited to at-risk amount under §465. Form 6198.",
             "sort_order": 19, "precedence": 11},
            {"rule_id": "R020", "title": "Passive activity limitation (post-at-risk)", "rule_type": "validation",
             "formula": "passive losses limited under §469",
             "inputs": ["deductible_after_at_risk"], "outputs": ["final_deductible_loss"],
             "description": "After at-risk, passive losses limited under §469. Three-tier ordering: basis → at-risk → passive. Form 8582.",
             "sort_order": 20, "precedence": 12},
        ])

        self._upsert_links(rules, sources, [
            ("R001", "IRC_1366", "primary", "§1366(a) — shareholder reports pro rata share"),
            ("R001", "IRC_1377", "primary", "§1377(a) — per share per day allocation"),
            ("R001", "IRS_2025_1120S_K1_INSTR", "secondary", "Box 1 instructions — ordinary income → Sch E Part II"),
            ("R002", "IRC_1366", "primary", "§1366(a) — pro rata share of rental income"),
            ("R002", "IRS_2025_1120S_K1_INSTR", "secondary", "Box 2 instructions"),
            ("R007", "IRC_1366", "primary", "§1366(a) — pro rata share of STCG"),
            ("R007", "IRS_2025_1120S_K1_INSTR", "secondary", "Box 7 → Schedule D line 5"),
            ("R008", "IRC_1366", "primary", "§1366(a) — pro rata share of LTCG"),
            ("R008", "IRS_2025_1120S_K1_INSTR", "secondary", "Box 8a → Schedule D line 12"),
            ("R009", "IRC_1366", "primary", "§1366(a) — pro rata share of §1231"),
            ("R009", "IRS_2025_1120S_K1_INSTR", "secondary", "Box 9 → Form 4797 Part I"),
            ("R011", "IRC_179", "primary", "§179(d)(4) — §179 passes through to shareholder"),
            ("R011", "IRS_2025_1120S_K1_INSTR", "secondary", "Box 11 instructions"),
            ("R017", "IRC_199A", "primary", "§199A QBI items for shareholder computation"),
            ("R017", "IRS_2025_1120S_K1_INSTR", "secondary", "Box 17 — other information"),
            ("R018", "IRC_1366", "primary", "§1366(d) — loss limited to stock + debt basis"),
            ("R018", "IRS_2025_7203_INSTR", "secondary", "Form 7203 — basis computation and loss limitation"),
            ("R019", "IRC_465", "primary", "§465 — at-risk limitation"),
            ("R020", "IRC_469", "primary", "§469 — passive activity loss limitation"),
        ])

        self._upsert_lines(form, [
            {"line_number": "Box1", "description": "Ordinary business income (loss)", "line_type": "calculated", "source_rules": ["R001"], "destination_form": "Schedule E Part II, Line 28", "sort_order": 1},
            {"line_number": "Box2", "description": "Net rental real estate income (loss)", "line_type": "calculated", "source_rules": ["R002"], "destination_form": "Schedule E Part II (passive)", "sort_order": 2},
            {"line_number": "Box3", "description": "Other net rental income (loss)", "line_type": "calculated", "destination_form": "Schedule E Part II", "sort_order": 3},
            {"line_number": "Box4", "description": "Interest income", "line_type": "calculated", "destination_form": "Schedule B or Form 1040 Line 2b", "sort_order": 4},
            {"line_number": "Box5a", "description": "Ordinary dividends", "line_type": "calculated", "destination_form": "Form 1040 Line 3b", "sort_order": 5},
            {"line_number": "Box5b", "description": "Qualified dividends", "line_type": "calculated", "destination_form": "Form 1040 Line 3a", "sort_order": 6},
            {"line_number": "Box6", "description": "Royalties", "line_type": "calculated", "destination_form": "Schedule E Page 1", "sort_order": 7},
            {"line_number": "Box7", "description": "Net short-term capital gain (loss)", "line_type": "calculated", "source_rules": ["R007"], "destination_form": "Schedule D Line 5", "sort_order": 8},
            {"line_number": "Box8a", "description": "Net long-term capital gain (loss)", "line_type": "calculated", "source_rules": ["R008"], "destination_form": "Schedule D Line 12", "sort_order": 9},
            {"line_number": "Box8b", "description": "Collectibles (28%) gain (loss)", "line_type": "calculated", "destination_form": "Schedule D Line 18 (28% Rate Gain Worksheet)", "sort_order": 10},
            {"line_number": "Box8c", "description": "Unrecaptured §1250 gain", "line_type": "calculated", "destination_form": "Schedule D Line 19 (Unrecaptured §1250 Gain Worksheet)", "sort_order": 11},
            {"line_number": "Box9", "description": "Net §1231 gain (loss)", "line_type": "calculated", "source_rules": ["R009"], "destination_form": "Form 4797 Part I", "sort_order": 12},
            {"line_number": "Box10", "description": "Other income (loss)", "line_type": "calculated", "destination_form": "See K-1 instructions for codes", "sort_order": 13},
            {"line_number": "Box11", "description": "§179 deduction", "line_type": "calculated", "source_rules": ["R011"], "destination_form": "Form 4562 (shareholder's own)", "sort_order": 14},
            {"line_number": "Box12", "description": "Other deductions (coded: A=cash charitable, B=noncash, C=inv interest, etc.)", "line_type": "calculated", "destination_form": "Schedule A / Form 4952 / etc. per code", "sort_order": 15},
            {"line_number": "Box13", "description": "Credits (coded: A-G per type)", "line_type": "calculated", "destination_form": "Form 3800 / Form 1116 / etc. per code", "sort_order": 16},
            {"line_number": "Box16", "description": "Items affecting shareholder basis (A=tax-exempt interest, C=nondeductible, D=distributions)", "line_type": "calculated", "destination_form": "Form 7203", "sort_order": 17},
            {"line_number": "Box17", "description": "Other information — §199A QBI, investment income/expenses", "line_type": "calculated", "source_rules": ["R017"], "destination_form": "Form 8995 or 8995-A", "sort_order": 18},
        ])

        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D001", "title": "Loss exceeds basis", "severity": "error",
             "condition": "total_allocated_losses > stock_basis_boy + debt_basis",
             "message": "Shareholder's deductible losses cannot exceed the sum of stock basis and debt basis. Use Form 7203 to compute. Excess losses are suspended and carry forward."},
            {"diagnostic_id": "D002", "title": "Missing Form 7203", "severity": "warning",
             "condition": "any allocated loss exists AND no Form 7203 prepared",
             "message": "Shareholder has allocated losses. Form 7203 (S Corporation Shareholder Stock and Debt Basis Limitations) is required when claiming a loss deduction."},
            {"diagnostic_id": "D003", "title": "Passive activity indicator", "severity": "info",
             "condition": "shareholder does not materially participate",
             "message": "Reminder: if the shareholder does not materially participate in the S corporation's activities, losses may be subject to passive activity limitations under §469. Check Form 8582."},
        ])

        self._upsert_tests(form, [
            {"scenario_name": "Simple K-1 — all income, no limitations",
             "scenario_type": "normal",
             "inputs": {"ownership_percentage": 1.0, "ordinary_business_income": 200000, "section_179_deduction": 50000, "net_long_term_capital_gain": 30000},
             "expected_outputs": {"box_1_ordinary_income": 200000, "box_11_section_179": 50000, "box_8a_net_ltcg": 30000},
             "notes": "100% shareholder, all income flows through 1:1.", "sort_order": 1},
            {"scenario_name": "Loss limitation triggered",
             "scenario_type": "edge",
             "inputs": {"ownership_percentage": 0.5, "ordinary_business_income": -80000, "stock_basis_boy": 30000, "debt_basis": 0},
             "expected_outputs": {"box_1_ordinary_income": -40000, "deductible_loss": -30000, "suspended_loss": -10000},
             "notes": "50% of -80K = -40K allocated. Stock basis 30K limits deduction to -30K, 10K suspended.", "sort_order": 2},
        ])

        self._upsert_form_links("K1_1120S", sources, [
            ("IRS_2025_1120S_K1_INSTR", "governs"),
            ("IRC_1366", "governs"),
            ("IRC_1377", "governs"),
            ("IRS_2025_7203_INSTR", "informs"),
        ])

        self.stdout.write(self.style.SUCCESS("  Schedule K-1 complete."))

    # ─────────────────────────────────────────────────────────────────────────
    # Form 3: Schedule D (Form 1120-S)
    # ─────────────────────────────────────────────────────────────────────────

    def _load_schedule_d(self, sources):
        form = self._upsert_form(
            "SCHD_1120S",
            "Schedule D (Form 1120-S) — Capital Gains and Losses and Built-in Gains",
            ["1120S"],
            notes="Aggregates capital gains/losses from Form 8949. BIG tax computation if applicable.",
        )

        self._upsert_facts(form, [
            # Per-transaction inputs (from Form 8949)
            {"fact_key": "description", "label": "Description of property", "data_type": "string", "required": True, "sort_order": 1},
            {"fact_key": "date_acquired", "label": "Date acquired", "data_type": "date", "required": True, "sort_order": 2},
            {"fact_key": "date_sold", "label": "Date sold", "data_type": "date", "required": True, "sort_order": 3},
            {"fact_key": "proceeds", "label": "Sales price (proceeds)", "data_type": "decimal", "required": True, "sort_order": 4},
            {"fact_key": "cost_basis", "label": "Cost or other basis", "data_type": "decimal", "required": True, "sort_order": 5},
            {"fact_key": "adjustment_code", "label": "Adjustment code", "data_type": "choice", "choices": ["B", "T", "W", "O"], "sort_order": 6},
            {"fact_key": "adjustment_amount", "label": "Adjustment amount", "data_type": "decimal", "sort_order": 7},
            # Aggregated totals
            {"fact_key": "total_short_term_gain_loss", "label": "Total net short-term capital gain (loss)", "data_type": "decimal", "sort_order": 10},
            {"fact_key": "total_long_term_gain_loss", "label": "Total net long-term capital gain (loss)", "data_type": "decimal", "sort_order": 11},
            # BIG tax
            {"fact_key": "built_in_gains_tax_applicable", "label": "Built-in gains tax applicable (§1374)", "data_type": "boolean", "default_value": "false", "sort_order": 20},
            {"fact_key": "s_election_date", "label": "Date of S election", "data_type": "date", "sort_order": 21},
            {"fact_key": "net_unrealized_built_in_gain", "label": "Net unrealized built-in gain at conversion", "data_type": "decimal", "sort_order": 22},
            {"fact_key": "net_recognized_built_in_gain", "label": "Net recognized built-in gain (current year)", "data_type": "decimal", "sort_order": 23},
        ])

        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "Short-term vs long-term classification", "rule_type": "classification",
             "formula": 'if holding_period_months > 12 then "long_term" else "short_term"',
             "inputs": ["date_acquired", "date_sold"], "outputs": ["holding_period_class"],
             "description": "Property held more than 1 year is long-term. 1 year or less is short-term.",
             "sort_order": 1, "precedence": 1},
            {"rule_id": "R002", "title": "Aggregate short-term", "rule_type": "calculation",
             "formula": "sum of all short-term gains/losses from Form 8949 Part I",
             "inputs": ["short_term_transactions"], "outputs": ["total_short_term_gain_loss"],
             "description": "Sum all short-term capital gains and losses from Form 8949 categories.",
             "sort_order": 2, "precedence": 5},
            {"rule_id": "R003", "title": "Aggregate long-term", "rule_type": "calculation",
             "formula": "sum of all long-term gains/losses from Form 8949 Part II",
             "inputs": ["long_term_transactions"], "outputs": ["total_long_term_gain_loss"],
             "description": "Sum all long-term capital gains and losses from Form 8949 categories.",
             "sort_order": 3, "precedence": 5},
            {"rule_id": "R004", "title": "Flow to Schedule K", "rule_type": "routing",
             "formula": "total_short_term_gain_loss → K Line 7; total_long_term_gain_loss → K Line 8a",
             "inputs": ["total_short_term_gain_loss", "total_long_term_gain_loss"],
             "outputs": ["k_line_7", "k_line_8a"],
             "description": "Net STCG → K Line 7, Net LTCG → K Line 8a. These are separately stated items.",
             "sort_order": 4, "precedence": 10},
            {"rule_id": "R005", "title": "Built-in gains tax (§1374)", "rule_type": "calculation",
             "formula": "net_recognized_built_in_gain * 0.21",
             "conditions": {"when": "built_in_gains_tax_applicable == true AND within recognition period (5 years)"},
             "inputs": ["built_in_gains_tax_applicable", "net_recognized_built_in_gain", "net_unrealized_built_in_gain"],
             "outputs": ["big_tax"],
             "description": "C-Corp converting to S-Corp may owe BIG tax on built-in gains recognized within 5-year recognition period. Tax is at 21% corporate rate. Limited to net unrealized built-in gain at conversion.",
             "notes": "NEEDS REVIEW — recognition period rules, net unrealized built-in gain limitation, and carryover of unused BIG.",
             "sort_order": 5, "precedence": 15},
        ])

        self._upsert_links(rules, sources, [
            ("R001", "IRC_1222", "primary", "§1222 defines short-term vs long-term"),
            ("R002", "IRS_2025_1120S_SCHD_INSTR", "primary", "Schedule D Part I — short-term aggregation"),
            ("R002", "IRS_2025_8949_INSTR", "secondary", "Form 8949 provides individual transactions"),
            ("R003", "IRS_2025_1120S_SCHD_INSTR", "primary", "Schedule D Part II — long-term aggregation"),
            ("R003", "IRS_2025_8949_INSTR", "secondary", "Form 8949 provides individual transactions"),
            ("R004", "IRS_2025_1120S_INSTR", "primary", "1120-S instructions — Schedule K Lines 7-8"),
            ("R004", "IRS_2025_1120S_SCHD_INSTR", "secondary", "Schedule D totals flow to K"),
            ("R005", "IRC_1374", "primary", "§1374 — built-in gains tax"),
            ("R005", "IRS_2025_1120S_SCHD_INSTR", "secondary", "Part III — BIG tax computation"),
        ])

        self._upsert_lines(form, [
            {"line_number": "1a", "description": "Short-term totals from Form 8949, Box A (basis reported to IRS)", "line_type": "input", "sort_order": 1},
            {"line_number": "1b", "description": "Short-term totals from Form 8949, Box B (basis NOT reported)", "line_type": "input", "sort_order": 2},
            {"line_number": "1c", "description": "Short-term totals from Form 8949, Box C (no 1099-B)", "line_type": "input", "sort_order": 3},
            {"line_number": "2", "description": "Short-term capital gain from installment sales (Form 6252)", "line_type": "input", "sort_order": 4},
            {"line_number": "3", "description": "Short-term capital gain from like-kind exchanges (Form 8824)", "line_type": "input", "sort_order": 5},
            {"line_number": "5", "description": "Net short-term capital gain (loss) — combine lines 1 through 4", "line_type": "subtotal", "source_rules": ["R002"], "sort_order": 6},
            {"line_number": "6", "description": "Enter amount from line 5 on Schedule K, line 7", "line_type": "total", "source_rules": ["R004"], "destination_form": "Schedule K Line 7 → K-1 Box 7", "sort_order": 7},
            {"line_number": "7a", "description": "Long-term totals from Form 8949, Box D (basis reported)", "line_type": "input", "sort_order": 10},
            {"line_number": "7b", "description": "Long-term totals from Form 8949, Box E (basis NOT reported)", "line_type": "input", "sort_order": 11},
            {"line_number": "7c", "description": "Long-term totals from Form 8949, Box F (no 1099-B)", "line_type": "input", "sort_order": 12},
            {"line_number": "8", "description": "Long-term capital gain from installment sales (Form 6252)", "line_type": "input", "sort_order": 13},
            {"line_number": "9", "description": "Long-term capital gain from like-kind exchanges (Form 8824)", "line_type": "input", "sort_order": 14},
            {"line_number": "11", "description": "Net long-term capital gain (loss) — combine lines 7 through 10", "line_type": "subtotal", "source_rules": ["R003"], "sort_order": 15},
            {"line_number": "12", "description": "Enter amount from line 11 on Schedule K, line 8a", "line_type": "total", "source_rules": ["R004"], "destination_form": "Schedule K Line 8a → K-1 Box 8a", "sort_order": 16},
            # Part III — BIG tax
            {"line_number": "13", "description": "Net recognized built-in gain (Part III)", "line_type": "input", "source_facts": ["net_recognized_built_in_gain"], "sort_order": 20, "notes": "Only if §1374 applies"},
            {"line_number": "15", "description": "Net unrealized built-in gain limitation", "line_type": "input", "source_facts": ["net_unrealized_built_in_gain"], "sort_order": 21},
            {"line_number": "19", "description": "Tax — multiply taxable income by 21%", "line_type": "calculated", "source_rules": ["R005"], "calculation": "net_recognized_built_in_gain * 0.21", "sort_order": 22},
        ])

        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D001", "title": "BIG tax applicability", "severity": "info",
             "condition": "S election within last 5 years AND was C-Corp",
             "message": "This S corporation may be subject to the built-in gains tax under §1374. Check if any assets disposed of have built-in gain from the C-Corp period."},
            {"diagnostic_id": "D002", "title": "8949 category mismatch", "severity": "warning",
             "condition": "basis_reported_to_irs inconsistent with reporting category",
             "message": "The Form 8949 reporting category does not match the basis reporting indicator. Verify whether the IRS received the basis on the 1099-B."},
        ])

        self._upsert_tests(form, [
            {"scenario_name": "Two ST transactions, one LT — correct aggregation",
             "scenario_type": "normal",
             "inputs": {
                 "transactions": [
                     {"type": "short_term", "proceeds": 10000, "cost_basis": 8000, "gain_loss": 2000},
                     {"type": "short_term", "proceeds": 5000, "cost_basis": 6000, "gain_loss": -1000},
                     {"type": "long_term", "proceeds": 20000, "cost_basis": 12000, "gain_loss": 8000},
                 ],
             },
             "expected_outputs": {"total_short_term_gain_loss": 1000, "total_long_term_gain_loss": 8000, "k_line_7": 1000, "k_line_8a": 8000},
             "notes": "ST net = 2000-1000 = 1000. LT net = 8000. Each flows to its K line.", "sort_order": 1},
            {"scenario_name": "BIG tax scenario — C→S conversion, asset sold within 5 years",
             "scenario_type": "edge",
             "inputs": {"built_in_gains_tax_applicable": True, "net_recognized_built_in_gain": 100000, "net_unrealized_built_in_gain": 150000},
             "expected_outputs": {"big_tax": 21000},
             "notes": "NEEDS REVIEW — BIG tax = 100K × 21% = 21K. Limited to NUBIG of 150K (not exceeded here).", "sort_order": 2},
        ])

        self._upsert_form_links("SCHD_1120S", sources, [
            ("IRS_2025_1120S_SCHD_INSTR", "governs"),
            ("IRC_1222", "governs"),
            ("IRC_1374", "governs"),
            ("IRS_2025_8949_INSTR", "informs"),
        ])

        self.stdout.write(self.style.SUCCESS("  Schedule D complete."))

    # ─────────────────────────────────────────────────────────────────────────
    # Form 4: Form 8949
    # ─────────────────────────────────────────────────────────────────────────

    def _load_form_8949(self, sources):
        form = self._upsert_form(
            "8949",
            "Form 8949 — Sales and Other Dispositions of Capital Assets",
            ["1120S", "1065", "1120", "1040"],
            notes="Per-transaction detail for capital asset sales. Feeds Schedule D.",
        )

        self._upsert_facts(form, [
            {"fact_key": "description", "label": "Description of property", "data_type": "string", "required": True, "sort_order": 1},
            {"fact_key": "date_acquired", "label": "Date acquired", "data_type": "date", "required": True, "sort_order": 2},
            {"fact_key": "date_sold", "label": "Date sold or disposed of", "data_type": "date", "required": True, "sort_order": 3},
            {"fact_key": "proceeds", "label": "Proceeds (sales price)", "data_type": "decimal", "required": True, "validation_rule": "must be >= 0", "sort_order": 4},
            {"fact_key": "cost_basis", "label": "Cost or other basis", "data_type": "decimal", "required": True, "sort_order": 5},
            {"fact_key": "adjustment_code", "label": "Adjustment code(s)", "data_type": "choice", "choices": ["B", "T", "W", "O"], "sort_order": 6},
            {"fact_key": "adjustment_amount", "label": "Amount of adjustment", "data_type": "decimal", "sort_order": 7},
            {"fact_key": "gain_or_loss", "label": "Gain or (loss)", "data_type": "decimal", "sort_order": 8},
            {"fact_key": "reporting_category", "label": "Reporting category", "data_type": "choice",
             "choices": ["A", "B", "C", "D", "E", "F"], "required": True, "sort_order": 9,
             "notes": "A=ST basis reported, B=ST not reported, C=ST no 1099-B, D=LT basis reported, E=LT not reported, F=LT no 1099-B"},
            {"fact_key": "basis_reported_to_irs", "label": "Was basis reported to IRS on 1099-B?", "data_type": "boolean", "sort_order": 10},
        ])

        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "Determine reporting category", "rule_type": "classification",
             "formula": 'category based on (1) ST vs LT holding period, (2) whether basis reported on 1099-B',
             "inputs": ["date_acquired", "date_sold", "basis_reported_to_irs"],
             "outputs": ["reporting_category"],
             "description": "Category A/B/C (short-term) or D/E/F (long-term) based on holding period and 1099-B basis reporting.",
             "sort_order": 1, "precedence": 1},
            {"rule_id": "R002", "title": "Calculate gain or loss per transaction", "rule_type": "calculation",
             "formula": "proceeds - cost_basis + adjustment_amount",
             "inputs": ["proceeds", "cost_basis", "adjustment_amount"],
             "outputs": ["gain_or_loss"],
             "description": "Gain/loss = proceeds minus cost basis plus/minus adjustments (adjustments can be positive or negative).",
             "sort_order": 2, "precedence": 5},
            {"rule_id": "R003", "title": "Adjustment codes", "rule_type": "classification",
             "formula": "code depends on type of adjustment",
             "inputs": ["adjustment_code"], "outputs": ["adjustment_treatment"],
             "description": "Code B = basis incorrect on 1099-B (correction amount). Code T = wash sale (loss disallowed under §1091). Code W = collectibles (28% rate). Code O = other.",
             "sort_order": 3, "precedence": 1},
            {"rule_id": "R004", "title": "Aggregate to Schedule D", "rule_type": "routing",
             "formula": "Part I totals → Schedule D Part I; Part II totals → Schedule D Part II",
             "inputs": ["reporting_category", "gain_or_loss"],
             "outputs": ["schedule_d_part_i", "schedule_d_part_ii"],
             "description": "Part I (ST categories A/B/C) totals → Schedule D Part I lines 1a/1b/1c. Part II (LT categories D/E/F) totals → Schedule D Part II lines 7a/7b/7c.",
             "sort_order": 4, "precedence": 10},
        ])

        self._upsert_links(rules, sources, [
            ("R001", "IRS_2025_8949_INSTR", "primary", "Form 8949 instructions — reporting category determination"),
            ("R001", "IRC_1222", "secondary", "§1222 — ST vs LT holding period definitions"),
            ("R002", "IRS_2025_8949_INSTR", "primary", "Column (h) instructions — gain/loss computation"),
            ("R003", "IRS_2025_8949_INSTR", "primary", "Column (f)/(g) instructions — adjustment codes"),
            ("R004", "IRS_2025_8949_INSTR", "primary", "Totals flow to Schedule D"),
            ("R004", "IRS_2025_1120S_SCHD_INSTR", "secondary", "Schedule D receives 8949 totals"),
        ])

        self._upsert_lines(form, [
            {"line_number": "1a_col_d", "description": "Part I, Column (d) — Proceeds", "line_type": "input", "source_facts": ["proceeds"], "sort_order": 1},
            {"line_number": "1a_col_e", "description": "Part I, Column (e) — Cost or other basis", "line_type": "input", "source_facts": ["cost_basis"], "sort_order": 2},
            {"line_number": "1a_col_f", "description": "Part I, Column (f) — Adjustment code", "line_type": "input", "source_facts": ["adjustment_code"], "sort_order": 3},
            {"line_number": "1a_col_g", "description": "Part I, Column (g) — Amount of adjustment", "line_type": "input", "source_facts": ["adjustment_amount"], "sort_order": 4},
            {"line_number": "1a_col_h", "description": "Part I, Column (h) — Gain or (loss) = (d) - (e) + (g)", "line_type": "calculated", "source_rules": ["R002"], "calculation": "proceeds - cost_basis + adjustment_amount", "sort_order": 5},
            {"line_number": "2", "description": "Part I totals — Short-term", "line_type": "subtotal", "source_rules": ["R004"], "destination_form": "Schedule D Part I (lines 1a-1c by category)", "sort_order": 6},
            {"line_number": "3a_col_d", "description": "Part II, Column (d) — Proceeds", "line_type": "input", "source_facts": ["proceeds"], "sort_order": 10},
            {"line_number": "3a_col_e", "description": "Part II, Column (e) — Cost or other basis", "line_type": "input", "source_facts": ["cost_basis"], "sort_order": 11},
            {"line_number": "3a_col_f", "description": "Part II, Column (f) — Adjustment code", "line_type": "input", "source_facts": ["adjustment_code"], "sort_order": 12},
            {"line_number": "3a_col_g", "description": "Part II, Column (g) — Amount of adjustment", "line_type": "input", "source_facts": ["adjustment_amount"], "sort_order": 13},
            {"line_number": "3a_col_h", "description": "Part II, Column (h) — Gain or (loss)", "line_type": "calculated", "source_rules": ["R002"], "calculation": "proceeds - cost_basis + adjustment_amount", "sort_order": 14},
            {"line_number": "4", "description": "Part II totals — Long-term", "line_type": "subtotal", "source_rules": ["R004"], "destination_form": "Schedule D Part II (lines 7a-7c by category)", "sort_order": 15},
        ])

        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D001", "title": "Proceeds differ from 1099-B", "severity": "warning",
             "condition": "basis_reported_to_irs == true AND adjustment needed but no code entered",
             "message": "Proceeds or basis on 1099-B may differ from actual amounts. If basis is incorrect, use Code B with the correction in column (g)."},
            {"diagnostic_id": "D002", "title": "Wash sale not coded", "severity": "warning",
             "condition": "same security sold at loss within 30-day window",
             "message": "A wash sale may apply. If the same or substantially identical security was purchased within 30 days before or after this sale at a loss, use Code T and enter the disallowed loss in column (g)."},
            {"diagnostic_id": "D003", "title": "Missing date acquired", "severity": "error",
             "condition": "date_acquired is null",
             "message": "Date acquired is required to determine holding period (short-term vs long-term) and correct reporting category."},
        ])

        self._upsert_tests(form, [
            {"scenario_name": "Simple stock sale — basis correct, no adjustments",
             "scenario_type": "normal",
             "inputs": {"description": "100 shares XYZ Corp", "date_acquired": "2023-01-15", "date_sold": "2025-06-01",
                         "proceeds": 15000, "cost_basis": 10000, "adjustment_code": None, "adjustment_amount": 0,
                         "basis_reported_to_irs": True},
             "expected_outputs": {"reporting_category": "D", "gain_or_loss": 5000},
             "notes": "Held >1yr = LT. Basis reported = category D. Gain = 15K-10K = 5K.", "sort_order": 1},
            {"scenario_name": "Basis adjustment — 1099-B shows wrong basis",
             "scenario_type": "normal",
             "inputs": {"description": "200 shares ABC Inc", "date_acquired": "2024-03-01", "date_sold": "2025-02-15",
                         "proceeds": 8000, "cost_basis": 6000, "adjustment_code": "B", "adjustment_amount": -500,
                         "basis_reported_to_irs": True},
             "expected_outputs": {"reporting_category": "A", "gain_or_loss": 1500},
             "notes": "Held ≤1yr = ST. Code B adjusts basis. Gain = 8000-6000+(-500) = 1500.", "sort_order": 2},
            {"scenario_name": "Wash sale — loss disallowed",
             "scenario_type": "edge",
             "inputs": {"description": "50 shares DEF Ltd", "date_acquired": "2025-01-10", "date_sold": "2025-04-05",
                         "proceeds": 4000, "cost_basis": 5000, "adjustment_code": "T", "adjustment_amount": 1000,
                         "basis_reported_to_irs": True},
             "expected_outputs": {"reporting_category": "A", "gain_or_loss": 0},
             "notes": "Loss of $1K disallowed as wash sale. Code T, adjustment +1000. Net = 4000-5000+1000 = 0.", "sort_order": 3},
        ])

        self._upsert_form_links("8949", sources, [
            ("IRS_2025_8949_INSTR", "governs"),
            ("IRC_1222", "governs"),
            ("IRC_1221", "governs"),
        ])

        self.stdout.write(self.style.SUCCESS("  Form 8949 complete."))

    # ─────────────────────────────────────────────────────────────────────────
    # Form 5: Form 4562
    # ─────────────────────────────────────────────────────────────────────────

    def _load_form_4562(self, sources):
        form = self._upsert_form(
            "4562",
            "Form 4562 — Depreciation and Amortization",
            ["1120S", "1065", "1120", "1040"],
            notes="§179 election, bonus depreciation, MACRS, amortization. §179 is separately stated for passthrough entities.",
        )

        self._upsert_facts(form, [
            # Part I — §179
            {"fact_key": "section_179_elected_cost", "label": "§179 — elected cost of property", "data_type": "decimal", "sort_order": 1},
            {"fact_key": "section_179_limitation", "label": "§179 — maximum deduction ($2,500,000 for 2025)", "data_type": "decimal", "default_value": "2500000", "sort_order": 2},
            {"fact_key": "section_179_phaseout_threshold", "label": "§179 — phaseout threshold ($4,000,000 for 2025)", "data_type": "decimal", "default_value": "4000000", "sort_order": 3},
            {"fact_key": "total_section_179_placed_in_service", "label": "Total cost of §179 property placed in service", "data_type": "decimal", "sort_order": 4},
            {"fact_key": "taxable_income_limitation", "label": "Taxable income from active trade or business", "data_type": "decimal", "sort_order": 5},
            # Part II — Bonus
            {"fact_key": "bonus_eligible_basis", "label": "Bonus-eligible property basis (after §179)", "data_type": "decimal", "sort_order": 10},
            {"fact_key": "bonus_percentage", "label": "Applicable bonus percentage", "data_type": "choice", "choices": ["100", "40", "0"], "sort_order": 11,
             "notes": "100% for assets acquired after 1/19/2025, 40% for prior acquisitions"},
            {"fact_key": "bonus_depreciation_amount", "label": "Bonus depreciation amount", "data_type": "decimal", "sort_order": 12},
            {"fact_key": "acquisition_date", "label": "Date property acquired", "data_type": "date", "sort_order": 13,
             "notes": "Determines 100% vs 40% bonus rate under OBBBA binding contract rule"},
            # Part III — MACRS
            {"fact_key": "recovery_period", "label": "MACRS recovery period (years)", "data_type": "choice",
             "choices": ["3", "5", "7", "10", "15", "20", "25", "27.5", "39"], "sort_order": 20},
            {"fact_key": "depreciation_method", "label": "Depreciation method", "data_type": "choice",
             "choices": ["200DB", "150DB", "SL"], "sort_order": 21},
            {"fact_key": "convention", "label": "Convention", "data_type": "choice",
             "choices": ["HY", "MQ", "MM"], "sort_order": 22},
            {"fact_key": "depreciable_basis", "label": "Depreciable basis (after §179 and bonus)", "data_type": "decimal", "sort_order": 23},
            {"fact_key": "current_year_depreciation", "label": "Current year MACRS depreciation", "data_type": "decimal", "sort_order": 24},
            # Part V — Amortization
            {"fact_key": "amortizable_amount", "label": "Amortizable amount", "data_type": "decimal", "sort_order": 30},
            {"fact_key": "amortization_period_months", "label": "Amortization period (months)", "data_type": "integer", "default_value": "180", "sort_order": 31,
             "notes": "180 months for §197 intangibles, §195 start-up, §248 organizational"},
            {"fact_key": "amortization_start_date", "label": "Date amortization begins", "data_type": "date", "sort_order": 32},
            {"fact_key": "current_year_amortization", "label": "Current year amortization", "data_type": "decimal", "sort_order": 33},
            # Entity context
            {"fact_key": "entity_type", "label": "Entity type filing this form", "data_type": "choice",
             "choices": ["1120S", "1065", "1120", "1040"], "required": True, "sort_order": 40},
        ])

        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "§179 limitation", "rule_type": "calculation",
             "formula": "min(elected_cost, max(0, 2500000 - max(0, total_placed_in_service - 4000000)), taxable_income)",
             "inputs": ["section_179_elected_cost", "total_section_179_placed_in_service", "taxable_income_limitation"],
             "outputs": ["allowed_179_deduction"],
             "description": "§179 deduction = lesser of: (a) elected cost, (b) $2,500,000 minus dollar-for-dollar reduction for total placed in service exceeding $4,000,000, (c) taxable income from active business. GA limit is $1,050,000/$2,620,000.",
             "sort_order": 1, "precedence": 1},
            {"rule_id": "R002", "title": "OBBBA bonus depreciation", "rule_type": "calculation",
             "formula": "bonus_eligible_basis * bonus_percentage",
             "conditions": {"when": "bonus_percentage > 0"},
             "inputs": ["bonus_eligible_basis", "bonus_percentage", "acquisition_date"],
             "outputs": ["bonus_depreciation_amount"],
             "description": "100% for assets acquired AND placed in service after 1/19/2025 (permanent under OBBBA). 40% for assets acquired before 1/20/2025 (binding contract rule). Bonus is on remaining basis after §179.",
             "notes": "NEEDS REVIEW — verify binding contract date rules for 40% rate.",
             "sort_order": 2, "precedence": 5},
            {"rule_id": "R003", "title": "MACRS depreciation calculation", "rule_type": "calculation",
             "formula": "depreciable_basis * pub_946_percentage(recovery_period, method, convention, year)",
             "inputs": ["depreciable_basis", "recovery_period", "depreciation_method", "convention"],
             "outputs": ["current_year_depreciation"],
             "description": "Apply IRS Pub 946 tables based on recovery period, method, and convention. Depreciable basis = original cost minus §179 minus bonus.",
             "sort_order": 3, "precedence": 10},
            {"rule_id": "R004", "title": "§179 flows to Schedule K (not Page 1)", "rule_type": "routing",
             "formula": "allowed_179_deduction → Schedule K Line 11 (1120S) or K Line 12 (1065)",
             "conditions": {"when": 'entity_type in ["1120S", "1065"]'},
             "inputs": ["allowed_179_deduction", "entity_type"],
             "outputs": ["schedule_k_179"],
             "description": "For S-Corps and partnerships, §179 is a separately stated item. It does NOT reduce ordinary income. It flows to Schedule K Line 11 (1120-S) or K Line 12 (1065).",
             "sort_order": 4, "precedence": 15},
            {"rule_id": "R005", "title": "Depreciation flows to Page 1", "rule_type": "routing",
             "formula": "current_year_depreciation + bonus_depreciation_amount → Page 1 deduction line",
             "inputs": ["current_year_depreciation", "bonus_depreciation_amount"],
             "outputs": ["page_1_depreciation"],
             "description": "MACRS + bonus depreciation (excluding §179) flows to Page 1 Line 14 (1120-S). Unlike §179, regular depreciation and bonus are NOT separately stated.",
             "sort_order": 5, "precedence": 15},
            {"rule_id": "R006", "title": "§197 amortization", "rule_type": "calculation",
             "formula": "amortizable_amount / 180 * months_in_service_this_year",
             "inputs": ["amortizable_amount", "amortization_period_months", "amortization_start_date"],
             "outputs": ["current_year_amortization"],
             "description": "§197 intangibles amortized over 180 months (15 years) straight-line. Includes goodwill, going concern value, covenants not to compete, franchises, trademarks.",
             "sort_order": 6, "precedence": 10},
        ])

        self._upsert_links(rules, sources, [
            ("R001", "IRC_179", "primary", "§179(b) — limitation and phaseout computation"),
            ("R001", "IRS_2025_4562_INSTR", "secondary", "Part I instructions — §179 election and limits"),
            ("R002", "IRC_168", "primary", "§168(k) — bonus depreciation as amended by OBBBA"),
            ("R002", "IRS_2025_4562_INSTR", "secondary", "Part II instructions — special depreciation allowance"),
            ("R003", "IRC_168", "primary", "§168(a)-(b) — MACRS general rules"),
            ("R003", "IRS_PUB_946", "primary", "Pub 946 — MACRS percentage tables"),
            ("R003", "IRS_2025_4562_INSTR", "secondary", "Part III instructions — MACRS depreciation"),
            ("R004", "IRC_179", "primary", "§179(d)(4) — separately stated for passthrough entities"),
            ("R004", "IRS_2025_1120S_INSTR", "secondary", "Schedule K Line 11 — §179 deduction"),
            ("R005", "IRS_2025_1120S_INSTR", "primary", "Page 1 Line 14 — depreciation (non-§179)"),
            ("R005", "IRS_2025_4562_INSTR", "secondary", "Line 22 total → entity return"),
            ("R006", "IRC_197", "primary", "§197 — 180-month amortization of intangibles"),
            ("R006", "IRS_2025_4562_INSTR", "secondary", "Part V instructions — amortization"),
        ])

        self._upsert_lines(form, [
            # Part I — §179
            {"line_number": "1", "description": "Maximum amount (see limitations) — $2,500,000 for 2025", "line_type": "input", "source_facts": ["section_179_limitation"], "sort_order": 1},
            {"line_number": "2", "description": "Total cost of section 179 property placed in service", "line_type": "input", "source_facts": ["total_section_179_placed_in_service"], "sort_order": 2},
            {"line_number": "3", "description": "Threshold cost of §179 property before reduction — $4,000,000", "line_type": "input", "source_facts": ["section_179_phaseout_threshold"], "sort_order": 3},
            {"line_number": "4", "description": "Reduction in limitation (line 2 minus line 3, if positive)", "line_type": "calculated", "calculation": "max(0, total_placed_in_service - 4000000)", "sort_order": 4},
            {"line_number": "5", "description": "Dollar limitation for tax year (line 1 minus line 4)", "line_type": "calculated", "calculation": "max(0, limitation - reduction)", "sort_order": 5},
            {"line_number": "6", "description": "Listed property — enter amount from line 29", "line_type": "input", "sort_order": 6},
            {"line_number": "7", "description": "Total elected cost of §179 property", "line_type": "input", "source_facts": ["section_179_elected_cost"], "sort_order": 7},
            {"line_number": "8", "description": "Total elected cost of §179 property — enter smaller of line 5 or line 7", "line_type": "calculated", "sort_order": 8},
            {"line_number": "9", "description": "Tentative deduction — enter smaller of line 5 or line 8", "line_type": "calculated", "sort_order": 9},
            {"line_number": "11", "description": "Business income limitation", "line_type": "input", "source_facts": ["taxable_income_limitation"], "sort_order": 10},
            {"line_number": "12", "description": "§179 expense deduction — enter smaller of line 9 or line 11", "line_type": "calculated", "source_rules": ["R001"], "destination_form": "Schedule K Line 11 (1120-S) or Page 1 Line 14 (1040/1120)", "sort_order": 11},
            # Part II — Bonus
            {"line_number": "14", "description": "Special depreciation allowance for qualified property (other than listed)", "line_type": "calculated", "source_rules": ["R002"], "source_facts": ["bonus_depreciation_amount"], "sort_order": 14},
            # Part III — MACRS
            {"line_number": "19a", "description": "3-year property", "line_type": "input", "sort_order": 19},
            {"line_number": "19b", "description": "5-year property", "line_type": "input", "sort_order": 20},
            {"line_number": "19c", "description": "7-year property", "line_type": "input", "sort_order": 21},
            {"line_number": "19d", "description": "10-year property", "line_type": "input", "sort_order": 22},
            {"line_number": "19e", "description": "15-year property", "line_type": "input", "sort_order": 23},
            {"line_number": "19f", "description": "20-year property", "line_type": "input", "sort_order": 24},
            {"line_number": "19g", "description": "25-year property (SL)", "line_type": "input", "sort_order": 25},
            {"line_number": "19h", "description": "Residential rental property — 27.5 years (SL/MM)", "line_type": "input", "sort_order": 26},
            {"line_number": "19i", "description": "Nonresidential real property — 39 years (SL/MM)", "line_type": "input", "sort_order": 27},
            # Summary
            {"line_number": "22", "description": "Total depreciation (add Part III amounts + Part II + prior MACRS)", "line_type": "total", "source_rules": ["R003", "R005"], "destination_form": "Page 1 Line 14 (1120-S) or appropriate deduction line", "sort_order": 30},
            # Part V — Amortization
            {"line_number": "42", "description": "Amortization of costs that begins during current year", "line_type": "input", "source_facts": ["amortizable_amount", "amortization_period_months", "amortization_start_date"], "sort_order": 40},
            {"line_number": "44", "description": "Total amortization — current year and prior", "line_type": "total", "source_rules": ["R006"], "destination_form": "Other deductions or Page 1 deduction line", "sort_order": 42},
        ])

        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D001", "title": "§179 exceeds limitation", "severity": "error",
             "condition": "section_179_elected_cost > allowed_after_phaseout OR section_179_elected_cost > taxable_income",
             "message": "§179 deduction exceeds the allowable limitation. Check the phaseout ($4M threshold) and business income limitation."},
            {"diagnostic_id": "D002", "title": "Bonus depreciation on wrong acquisition date", "severity": "warning",
             "condition": "bonus_percentage == 100 AND acquisition_date <= 2025-01-19",
             "message": "100% bonus depreciation applies only to property acquired AFTER January 19, 2025. Property acquired before 1/20/2025 qualifies for 40% bonus (OBBBA binding contract rule). Verify acquisition date."},
            {"diagnostic_id": "D003", "title": "Listed property >50% business use not documented", "severity": "warning",
             "condition": "listed_property == true AND business_use_percentage not documented",
             "message": "Listed property (vehicles, computers, etc.) must be used more than 50% for business to qualify for §179 and MACRS accelerated rates. If business use ≤50%, must use ADS straight-line."},
            {"diagnostic_id": "D004", "title": "§179 deducted on Page 1 instead of K", "severity": "error",
             "condition": 'entity_type in ["1120S", "1065"] AND section_179 reduces page 1 ordinary income',
             "message": "For S-Corps and partnerships, §179 is a SEPARATELY STATED item. It must flow to Schedule K Line 11 (1120-S) or K Line 12 (1065), NOT reduce ordinary income on Page 1."},
        ])

        self._upsert_tests(form, [
            {"scenario_name": "Basic MACRS — 5-year asset, 200DB, HY, $100K",
             "scenario_type": "normal",
             "inputs": {"depreciable_basis": 100000, "recovery_period": "5", "depreciation_method": "200DB", "convention": "HY", "year_in_service": 1},
             "expected_outputs": {"current_year_depreciation": 20000},
             "notes": "5yr 200DB HY year 1 = 20% × $100K = $20,000 (from Pub 946 tables).", "sort_order": 1},
            {"scenario_name": "§179 + bonus — $200K asset",
             "scenario_type": "normal",
             "inputs": {"section_179_elected_cost": 100000, "bonus_eligible_basis": 100000, "bonus_percentage": "100",
                         "acquisition_date": "2025-03-15", "total_section_179_placed_in_service": 200000,
                         "taxable_income_limitation": 500000, "entity_type": "1120S"},
             "expected_outputs": {"allowed_179_deduction": 100000, "bonus_depreciation_amount": 100000},
             "notes": "§179 = $100K (within limits). Remaining $100K × 100% bonus = $100K. §179→K Line 11, bonus→Page 1.", "sort_order": 2},
            {"scenario_name": "§179 phaseout — total placed in service = $4,200,000",
             "scenario_type": "edge",
             "inputs": {"section_179_elected_cost": 2500000, "total_section_179_placed_in_service": 4200000,
                         "taxable_income_limitation": 5000000},
             "expected_outputs": {"allowed_179_deduction": 2300000},
             "notes": "Phaseout: $4.2M - $4M = $200K excess. $2.5M - $200K = $2.3M allowed.", "sort_order": 3},
            {"scenario_name": "Georgia nonconformity note",
             "scenario_type": "edge",
             "inputs": {"section_179_elected_cost": 2500000, "total_section_179_placed_in_service": 2500000,
                         "taxable_income_limitation": 5000000},
             "expected_outputs": {"allowed_179_deduction": 2500000},
             "notes": "Federal §179 = $2.5M. Georgia limit is $1,050,000/$2,620,000 — GA has NOT adopted OBBBA. State computation would differ. This spec covers federal only.", "sort_order": 4},
        ])

        self._upsert_form_links("4562", sources, [
            ("IRS_2025_4562_INSTR", "governs"),
            ("IRC_179", "governs"),
            ("IRC_168", "governs"),
            ("IRC_197", "governs"),
            ("IRS_PUB_946", "informs"),
        ])

        self.stdout.write(self.style.SUCCESS("  Form 4562 complete."))

    # ─────────────────────────────────────────────────────────────────────────
    # Report
    # ─────────────────────────────────────────────────────────────────────────

    def _report_totals(self):
        def _safe(text):
            """Replace non-ASCII chars for Windows cp1252 console."""
            return text.encode("ascii", errors="replace").decode("ascii")

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("DATABASE TOTALS")
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

        # Check for rules with zero authority links
        all_rules = FormRule.objects.all()
        uncited = [r for r in all_rules if not r.authority_links.exists()]
        if uncited:
            self.stdout.write(self.style.WARNING(f"\nRules with ZERO authority links: {len(uncited)}"))
            for r in uncited:
                self.stdout.write(_safe(f"  {r.tax_form.form_number} {r.rule_id}: {r.title}"))
        else:
            self.stdout.write(self.style.SUCCESS("\nAll rules have authority links."))

        # Rules with NEEDS REVIEW
        needs_review = FormRule.objects.filter(notes__icontains="NEEDS REVIEW")
        if needs_review.exists():
            self.stdout.write(f"\nRules marked NEEDS REVIEW: {needs_review.count()}")
            for r in needs_review:
                self.stdout.write(_safe(f"  {r.tax_form.form_number} {r.rule_id}: {r.title}"))

        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("1120-S family specs loaded successfully."))
