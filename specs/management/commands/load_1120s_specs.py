"""Load 1120-S family form specs — Schedule K, K-1, Schedule D, Form 4562.

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
    help = "Load 1120-S family form specs (Schedule K, K-1, Schedule D, 4562)"

    def handle(self, *_args, **_options):
        with transaction.atomic():
            sources = self._load_sources()
            self._load_schedule_k(sources)
            self._load_k1(sources)
            self._load_schedule_d(sources)
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

        # 2025-face renumber (2026-07-11): rebuilt verbatim against
        # resources/irs_forms/2025/f1120s.pdf pages 3-4 (pymupdf extraction).
        # Fixed from the s44 audit: fabricated 13f FTC (face 13f = biofuel;
        # foreign taxes live on 16f), rehab credit on 13d (face: 13c),
        # 12d/12e misassignment, "page 1 line 21" refs (face: 22), the
        # missing 3b/3c 8b/8c 13b/13e 14a/b 15a-f 16e/16f rows, and the
        # 17a-d split (17c AE&P dividends — i1120s 2025 p.40).
        self._upsert_facts(form, [
            # Income/Loss (K lines 1-10)
            {"fact_key": "ordinary_business_income", "label": "Ordinary business income (loss) — from Page 1 Line 22", "data_type": "decimal", "required": True, "sort_order": 1},
            {"fact_key": "net_rental_real_estate_income", "label": "Net rental real estate income (loss) — from Form 8825", "data_type": "decimal", "sort_order": 2},
            {"fact_key": "other_gross_rental_income", "label": "Other gross rental income (loss) — line 3a", "data_type": "decimal", "sort_order": 3},
            {"fact_key": "other_rental_expenses", "label": "Expenses from other rental activities (attach statement) — line 3b", "data_type": "decimal", "sort_order": 4},
            {"fact_key": "other_net_rental_income", "label": "Other net rental income (loss) — line 3c = 3a minus 3b", "data_type": "decimal", "sort_order": 5},
            {"fact_key": "interest_income", "label": "Interest income", "data_type": "decimal", "sort_order": 6},
            {"fact_key": "dividend_income", "label": "Ordinary dividends", "data_type": "decimal", "sort_order": 7},
            {"fact_key": "qualified_dividends", "label": "Qualified dividends", "data_type": "decimal", "sort_order": 8},
            {"fact_key": "royalties", "label": "Royalties", "data_type": "decimal", "sort_order": 9},
            {"fact_key": "net_short_term_capital_gain", "label": "Net short-term capital gain (loss) — from Schedule D", "data_type": "decimal", "sort_order": 10},
            {"fact_key": "net_long_term_capital_gain", "label": "Net long-term capital gain (loss) — from Schedule D", "data_type": "decimal", "sort_order": 11},
            {"fact_key": "collectibles_28_gain", "label": "Collectibles (28%) gain (loss) — line 8b", "data_type": "decimal", "sort_order": 12},
            {"fact_key": "unrecaptured_1250_gain", "label": "Unrecaptured section 1250 gain (attach statement) — line 8c", "data_type": "decimal", "sort_order": 13},
            {"fact_key": "net_section_1231_gain", "label": "Net §1231 gain (loss) — from Form 4797 Part I", "data_type": "decimal", "sort_order": 14},
            {"fact_key": "other_income", "label": "Other income (loss)", "data_type": "decimal", "sort_order": 15},
            # Deductions (K lines 11-12e)
            {"fact_key": "section_179_deduction", "label": "§179 deduction — from Form 4562", "data_type": "decimal", "sort_order": 16},
            {"fact_key": "charitable_contributions_cash", "label": "Cash charitable contributions — line 12a", "data_type": "decimal", "sort_order": 17},
            {"fact_key": "charitable_contributions_noncash", "label": "Noncash charitable contributions — line 12b", "data_type": "decimal", "sort_order": 18},
            {"fact_key": "investment_interest_expense", "label": "Investment interest expense §163(d) — line 12c", "data_type": "decimal", "sort_order": 19},
            {"fact_key": "section_59e2_expenditures", "label": "Section 59(e)(2) expenditures — line 12d", "data_type": "decimal", "sort_order": 20},
            {"fact_key": "other_deductions", "label": "Other deductions — line 12e", "data_type": "decimal", "sort_order": 21},
            # Credits (K lines 13a-13g)
            {"fact_key": "low_income_housing_credit", "label": "Low-income housing credit (section 42(j)(5)) — line 13a", "data_type": "decimal", "sort_order": 22},
            {"fact_key": "low_income_housing_other", "label": "Low-income housing credit (other) — line 13b", "data_type": "decimal", "sort_order": 23},
            {"fact_key": "rehabilitation_credit", "label": "Qualified rehabilitation expenditures (rental real estate) — line 13c", "data_type": "decimal", "sort_order": 24},
            {"fact_key": "other_rental_re_credits", "label": "Other rental real estate credits — line 13d", "data_type": "decimal", "sort_order": 25},
            {"fact_key": "other_rental_credits", "label": "Other rental credits — line 13e", "data_type": "decimal", "sort_order": 26},
            {"fact_key": "biofuel_producer_credit", "label": "Biofuel producer credit (attach Form 6478) — line 13f", "data_type": "decimal", "sort_order": 27},
            {"fact_key": "other_credits", "label": "Other credits — line 13g", "data_type": "decimal", "sort_order": 28},
            # International (K lines 14a-14b)
            {"fact_key": "k2_attached", "label": "Schedule K-2 attached — line 14a checkbox", "data_type": "boolean", "sort_order": 29},
            {"fact_key": "k2_exception", "label": "Qualified for Schedule K-2 filing exception — line 14b checkbox", "data_type": "boolean", "sort_order": 30},
            # AMT items (K lines 15a-15f)
            {"fact_key": "post1986_depr_adjustment", "label": "Post-1986 depreciation adjustment — line 15a", "data_type": "decimal", "sort_order": 31},
            {"fact_key": "amt_adjusted_gain_loss", "label": "Adjusted gain or loss — line 15b", "data_type": "decimal", "sort_order": 32},
            {"fact_key": "amt_depletion", "label": "Depletion (other than oil and gas) — line 15c", "data_type": "decimal", "sort_order": 33},
            {"fact_key": "oil_gas_gross_income", "label": "Oil, gas, and geothermal properties — gross income — line 15d", "data_type": "decimal", "sort_order": 34},
            {"fact_key": "oil_gas_deductions", "label": "Oil, gas, and geothermal properties — deductions — line 15e", "data_type": "decimal", "sort_order": 35},
            {"fact_key": "other_amt_items", "label": "Other AMT items (attach statement) — line 15f", "data_type": "decimal", "sort_order": 36},
            # Items affecting shareholder basis (K lines 16a-16f)
            {"fact_key": "tax_exempt_interest", "label": "Tax-exempt interest income — line 16a", "data_type": "decimal", "sort_order": 37},
            {"fact_key": "other_tax_exempt_income", "label": "Other tax-exempt income — line 16b", "data_type": "decimal", "sort_order": 38},
            {"fact_key": "nondeductible_expenses", "label": "Nondeductible expenses — line 16c", "data_type": "decimal", "sort_order": 39},
            {"fact_key": "distributions_cash", "label": "Distributions — cash and marketable securities (line 16d)", "data_type": "decimal", "sort_order": 40},
            {"fact_key": "distributions_property", "label": "Distributions — other property (line 16d)", "data_type": "decimal", "sort_order": 41},
            {"fact_key": "loan_repayments", "label": "Repayment of loans from shareholders — line 16e", "data_type": "decimal", "sort_order": 42},
            {"fact_key": "foreign_taxes_paid", "label": "Foreign taxes paid or accrued — line 16f", "data_type": "decimal", "sort_order": 43},
            # Other information (K lines 17a-17d)
            {"fact_key": "investment_income", "label": "Investment income for Form 4952 — line 17a", "data_type": "decimal", "sort_order": 44},
            {"fact_key": "investment_expenses", "label": "Investment expenses for Form 4952 — line 17b", "data_type": "decimal", "sort_order": 45},
            {"fact_key": "aep_distributions", "label": "Dividend distributions paid from accumulated earnings and profits — line 17c", "data_type": "decimal", "sort_order": 46},
            {"fact_key": "qbi_ordinary_income", "label": "§199A QBI — ordinary income component (line 17d statement)", "data_type": "decimal", "sort_order": 47},
            {"fact_key": "qbi_w2_wages", "label": "§199A QBI — W-2 wages (line 17d statement)", "data_type": "decimal", "sort_order": 48},
            {"fact_key": "qbi_ubia", "label": "§199A QBI — UBIA of qualified property (line 17d statement)", "data_type": "decimal", "sort_order": 49},
            {"fact_key": "qbi_sstb_indicator", "label": "§199A — Specified service trade or business (SSTB) indicator (line 17d statement)", "data_type": "boolean", "sort_order": 50},
            # Allocation inputs
            {"fact_key": "total_shares_outstanding", "label": "Total shares outstanding", "data_type": "integer", "required": True, "sort_order": 60},
            {"fact_key": "days_in_year", "label": "Days in tax year", "data_type": "integer", "default_value": "365", "sort_order": 61},
        ])

        # Stale fact rows superseded by the 2025-face rebuild: the fabricated
        # 13f "foreign_tax_credit" (face 13f = biofuel producer credit; foreign
        # taxes are line 16f = foreign_taxes_paid). update_or_create cannot
        # remove rows, so a reseed self-heals here.
        stale_facts = FormFact.objects.filter(
            tax_form=form, fact_key__in=["foreign_tax_credit"],
        )
        if stale_facts.exists():
            self.stdout.write(f"  deleting {stale_facts.count()} stale fact rows (foreign_tax_credit)")
            stale_facts.delete()

        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "Ordinary business income passthrough", "rule_type": "routing",
             "formula": "ordinary_business_income",
             "inputs": ["ordinary_business_income"], "outputs": ["k_line_1"],
             "description": "Page 1 Line 22 flows directly to Schedule K Line 1. No modification. (2025 face: 'Ordinary business income (loss) (page 1, line 22)'.)",
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

            {"rule_id": "R009", "title": "Other net rental income — line 3c netting", "rule_type": "calculation",
             "formula": "other_gross_rental_income - other_rental_expenses",
             "inputs": ["other_gross_rental_income", "other_rental_expenses"],
             "outputs": ["k_line_3c"],
             "description": "2025 face line 3c: 'Other net rental income (loss). Subtract line 3b from line 3a.' Only the NET (3c) flows to K-1 Box 3; 3a/3b are the on-face worksheet columns.",
             "sort_order": 9, "precedence": 5},

            {"rule_id": "R019", "title": "Line 18 income (loss) reconciliation", "rule_type": "calculation",
             "formula": "sum(k_lines_1_to_10) - sum(k_lines_11_to_12e) - k_line_16f",
             "inputs": ["ordinary_business_income", "net_rental_real_estate_income", "other_net_rental_income", "interest_income", "dividend_income", "royalties", "net_short_term_capital_gain", "net_long_term_capital_gain", "net_section_1231_gain", "other_income", "section_179_deduction", "charitable_contributions_cash", "charitable_contributions_noncash", "investment_interest_expense", "section_59e2_expenditures", "other_deductions", "foreign_taxes_paid"],
             "outputs": ["k_line_18"],
             "description": "2025 face line 18: 'Combine the total amounts on lines 1 through 10. From the result, subtract the sum of the amounts on lines 11 through 12e and 16f.' Per i1120s (2025) p.49 the result must equal Schedule M-1 line 8 (or Schedule M-3 Part II line 26(d)). It does NOT generally equal Page 1 line 22 — separately stated items differ. Lines 5b, 8b, 8c are sub-detail of 5a/8a and are NOT added again.",
             "sort_order": 19, "precedence": 20},
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
            ("R009", "IRS_2025_1120S_INSTR", "primary", "2025 face line 3c — subtract line 3b from line 3a"),
            ("R019", "IRS_2025_1120S_INSTR", "primary", "i1120s (2025) p.49 Line 18 — combine 1-10, subtract 11-12e and 16f; must equal M-1 line 8"),
        ])

        self._upsert_lines(form, [
            {"line_number": "1", "description": "Ordinary business income (loss) (page 1, line 22)", "line_type": "input", "source_facts": ["ordinary_business_income"], "source_rules": ["R001"], "destination_form": "Schedule K-1 Box 1", "sort_order": 1},
            {"line_number": "2", "description": "Net rental real estate income (loss) (attach Form 8825)", "line_type": "input", "source_facts": ["net_rental_real_estate_income"], "source_rules": ["R002"], "destination_form": "Schedule K-1 Box 2", "sort_order": 2},
            {"line_number": "3a", "description": "Other gross rental income (loss)", "line_type": "input", "source_facts": ["other_gross_rental_income"], "sort_order": 3, "notes": "On-face worksheet column; only the 3c net flows onward."},
            {"line_number": "3b", "description": "Expenses from other rental activities (attach statement)", "line_type": "input", "source_facts": ["other_rental_expenses"], "sort_order": 4, "notes": "On-face worksheet column; only the 3c net flows onward."},
            {"line_number": "3c", "description": "Other net rental income (loss). Subtract line 3b from line 3a", "line_type": "total", "source_facts": ["other_net_rental_income"], "source_rules": ["R009"], "calculation": "line 3a - line 3b", "destination_form": "Schedule K-1 Box 3", "sort_order": 5},
            {"line_number": "4", "description": "Interest income", "line_type": "input", "source_facts": ["interest_income"], "destination_form": "Schedule K-1 Box 4", "sort_order": 6},
            {"line_number": "5a", "description": "Ordinary dividends", "line_type": "input", "source_facts": ["dividend_income"], "destination_form": "Schedule K-1 Box 5a", "sort_order": 7},
            {"line_number": "5b", "description": "Qualified dividends", "line_type": "input", "source_facts": ["qualified_dividends"], "destination_form": "Schedule K-1 Box 5b", "sort_order": 8, "notes": "Sub-detail of 5a — not added again in line 18."},
            {"line_number": "6", "description": "Royalties", "line_type": "input", "source_facts": ["royalties"], "destination_form": "Schedule K-1 Box 6", "sort_order": 9},
            {"line_number": "7", "description": "Net short-term capital gain (loss) (attach Schedule D (Form 1120-S))", "line_type": "input", "source_facts": ["net_short_term_capital_gain"], "source_rules": ["R003"], "destination_form": "Schedule K-1 Box 7", "sort_order": 10},
            {"line_number": "8a", "description": "Net long-term capital gain (loss) (attach Schedule D (Form 1120-S))", "line_type": "input", "source_facts": ["net_long_term_capital_gain"], "source_rules": ["R003"], "destination_form": "Schedule K-1 Box 8a", "sort_order": 11},
            {"line_number": "8b", "description": "Collectibles (28%) gain (loss)", "line_type": "input", "source_facts": ["collectibles_28_gain"], "destination_form": "Schedule K-1 Box 8b", "sort_order": 12, "notes": "Sub-detail of 8a — not added again in line 18."},
            {"line_number": "8c", "description": "Unrecaptured section 1250 gain (attach statement)", "line_type": "input", "source_facts": ["unrecaptured_1250_gain"], "destination_form": "Schedule K-1 Box 8c", "sort_order": 13, "notes": "Sub-detail of 8a — not added again in line 18."},
            {"line_number": "9", "description": "Net section 1231 gain (loss) (attach Form 4797)", "line_type": "input", "source_facts": ["net_section_1231_gain"], "source_rules": ["R004"], "destination_form": "Schedule K-1 Box 9", "sort_order": 14},
            {"line_number": "10", "description": "Other income (loss) (see instructions)", "line_type": "input", "source_facts": ["other_income"], "destination_form": "Schedule K-1 Box 10", "sort_order": 15},
            {"line_number": "11", "description": "Section 179 deduction (attach Form 4562)", "line_type": "input", "source_facts": ["section_179_deduction"], "source_rules": ["R005"], "destination_form": "Schedule K-1 Box 11", "sort_order": 16},
            {"line_number": "12a", "description": "Cash charitable contributions", "line_type": "input", "source_facts": ["charitable_contributions_cash"], "source_rules": ["R006"], "destination_form": "Schedule K-1 Box 12", "sort_order": 17},
            {"line_number": "12b", "description": "Noncash charitable contributions", "line_type": "input", "source_facts": ["charitable_contributions_noncash"], "source_rules": ["R006"], "destination_form": "Schedule K-1 Box 12", "sort_order": 18},
            {"line_number": "12c", "description": "Investment interest expense", "line_type": "input", "source_facts": ["investment_interest_expense"], "destination_form": "Schedule K-1 Box 12", "sort_order": 19},
            {"line_number": "12d", "description": "Section 59(e)(2) expenditures", "line_type": "input", "source_facts": ["section_59e2_expenditures"], "destination_form": "Schedule K-1 Box 12", "sort_order": 20},
            {"line_number": "12e", "description": "Other deductions (see instructions)", "line_type": "input", "source_facts": ["other_deductions"], "destination_form": "Schedule K-1 Box 12", "sort_order": 21},
            {"line_number": "13a", "description": "Low-income housing credit (section 42(j)(5))", "line_type": "input", "source_facts": ["low_income_housing_credit"], "destination_form": "Schedule K-1 Box 13", "sort_order": 22},
            {"line_number": "13b", "description": "Low-income housing credit (other)", "line_type": "input", "source_facts": ["low_income_housing_other"], "destination_form": "Schedule K-1 Box 13", "sort_order": 23},
            {"line_number": "13c", "description": "Qualified rehabilitation expenditures (rental real estate) (attach Form 3468, if applicable)", "line_type": "input", "source_facts": ["rehabilitation_credit"], "destination_form": "Schedule K-1 Box 13", "sort_order": 24},
            {"line_number": "13d", "description": "Other rental real estate credits (see instructions)", "line_type": "input", "source_facts": ["other_rental_re_credits"], "destination_form": "Schedule K-1 Box 13", "sort_order": 25},
            {"line_number": "13e", "description": "Other rental credits (see instructions)", "line_type": "input", "source_facts": ["other_rental_credits"], "destination_form": "Schedule K-1 Box 13", "sort_order": 26},
            {"line_number": "13f", "description": "Biofuel producer credit (attach Form 6478)", "line_type": "input", "source_facts": ["biofuel_producer_credit"], "destination_form": "Schedule K-1 Box 13", "sort_order": 27},
            {"line_number": "13g", "description": "Other credits (see instructions)", "line_type": "input", "source_facts": ["other_credits"], "destination_form": "Schedule K-1 Box 13", "sort_order": 28},
            {"line_number": "14a", "description": "Attach Schedule K-2 (Form 1120-S) and check this box to indicate international tax relevance", "line_type": "input", "source_facts": ["k2_attached"], "sort_order": 29, "notes": "Checkbox line — K-2/K-3 carry the international detail."},
            {"line_number": "14b", "description": "Check this box if you qualified for an exception to filing Schedule K-2 (Form 1120-S)", "line_type": "input", "source_facts": ["k2_exception"], "sort_order": 30, "notes": "Checkbox line."},
            {"line_number": "15a", "description": "Post-1986 depreciation adjustment", "line_type": "input", "source_facts": ["post1986_depr_adjustment"], "destination_form": "Schedule K-1 Box 15", "sort_order": 31},
            {"line_number": "15b", "description": "Adjusted gain or loss", "line_type": "input", "source_facts": ["amt_adjusted_gain_loss"], "destination_form": "Schedule K-1 Box 15", "sort_order": 32},
            {"line_number": "15c", "description": "Depletion (other than oil and gas)", "line_type": "input", "source_facts": ["amt_depletion"], "destination_form": "Schedule K-1 Box 15", "sort_order": 33},
            {"line_number": "15d", "description": "Oil, gas, and geothermal properties — gross income", "line_type": "input", "source_facts": ["oil_gas_gross_income"], "destination_form": "Schedule K-1 Box 15", "sort_order": 34},
            {"line_number": "15e", "description": "Oil, gas, and geothermal properties — deductions", "line_type": "input", "source_facts": ["oil_gas_deductions"], "destination_form": "Schedule K-1 Box 15", "sort_order": 35},
            {"line_number": "15f", "description": "Other AMT items (attach statement)", "line_type": "input", "source_facts": ["other_amt_items"], "destination_form": "Schedule K-1 Box 15", "sort_order": 36},
            {"line_number": "16a", "description": "Tax-exempt interest income", "line_type": "input", "source_facts": ["tax_exempt_interest"], "destination_form": "Schedule K-1 Box 16", "sort_order": 37},
            {"line_number": "16b", "description": "Other tax-exempt income", "line_type": "input", "source_facts": ["other_tax_exempt_income"], "destination_form": "Schedule K-1 Box 16", "sort_order": 38},
            {"line_number": "16c", "description": "Nondeductible expenses", "line_type": "input", "source_facts": ["nondeductible_expenses"], "destination_form": "Schedule K-1 Box 16", "sort_order": 39},
            {"line_number": "16d", "description": "Distributions (attach statement if required) (see instructions)", "line_type": "input", "source_facts": ["distributions_cash", "distributions_property"], "destination_form": "Schedule K-1 Box 16", "sort_order": 40, "notes": "Distributions OTHER than the line 17c AE&P dividends (i1120s 2025 p.40)."},
            {"line_number": "16e", "description": "Repayment of loans from shareholders", "line_type": "input", "source_facts": ["loan_repayments"], "destination_form": "Schedule K-1 Box 16", "sort_order": 41},
            {"line_number": "16f", "description": "Foreign taxes paid or accrued", "line_type": "input", "source_facts": ["foreign_taxes_paid"], "destination_form": "Schedule K-1 Box 16", "sort_order": 42, "notes": "Subtracted in the line 18 reconciliation per the face."},
            {"line_number": "17a", "description": "Investment income", "line_type": "input", "source_facts": ["investment_income"], "destination_form": "Schedule K-1 Box 17", "sort_order": 43},
            {"line_number": "17b", "description": "Investment expenses", "line_type": "input", "source_facts": ["investment_expenses"], "destination_form": "Schedule K-1 Box 17", "sort_order": 44},
            {"line_number": "17c", "description": "Dividend distributions paid from accumulated earnings and profits", "line_type": "input", "source_facts": ["aep_distributions"], "destination_form": "Form 1099-DIV (NOT Schedule K-1)", "sort_order": 45, "notes": "i1120s (2025) p.40: report these dividends to shareholders on Form 1099-DIV; do NOT report them on Schedule K-1."},
            {"line_number": "17d", "description": "Other items and amounts (attach statement)", "line_type": "input", "source_facts": ["qbi_ordinary_income", "qbi_w2_wages", "qbi_ubia", "qbi_sstb_indicator"], "source_rules": ["R007"], "destination_form": "Schedule K-1 Box 17 (statement)", "sort_order": 46, "notes": "§199A QBI package and other statement items ride 17d."},
            {"line_number": "18", "description": "Income (loss) reconciliation. Combine the total amounts on lines 1 through 10. From the result, subtract the sum of the amounts on lines 11 through 12e and 16f", "line_type": "total", "source_rules": ["R019"], "calculation": "sum(lines 1-10) - sum(lines 11-12e) - line 16f", "sort_order": 47, "notes": "Must equal Schedule M-1 line 8 (or M-3 Part II line 26(d)) per i1120s (2025) p.49. NOT generally equal to Page 1 line 22."},
        ])

        # Stale line rows superseded by the 2025-face rebuild: the pre-rebuild
        # catch-all "17" (now split 17a-17d). The allow-set includes the
        # K*->Box* informational rows added by load_1120s_full so a base
        # reseed never deletes the amendment loader's rows (s48 lesson).
        _2025_K_LINES = {
            "1", "2", "3a", "3b", "3c", "4", "5a", "5b", "6", "7",
            "8a", "8b", "8c", "9", "10", "11",
            "12a", "12b", "12c", "12d", "12e",
            "13a", "13b", "13c", "13d", "13e", "13f", "13g",
            "14a", "14b",
            "15a", "15b", "15c", "15d", "15e", "15f",
            "16a", "16b", "16c", "16d", "16e", "16f",
            "17a", "17b", "17c", "17d", "18",
        } | {
            "K1->Box1", "K2->Box2", "K3->Box3", "K4->Box4", "K5->Box5",
            "K6->Box6", "K7->Box7", "K8->Box8", "K9->Box9", "K10->Box10",
            "K11->Box11", "K12->Box12", "K13->Box13", "K16->Box16", "K17->Box17",
        }
        stale = FormLine.objects.filter(tax_form=form).exclude(line_number__in=_2025_K_LINES)
        if stale.exists():
            self.stdout.write(f"  deleting {stale.count()} stale pre-rebuild K line rows: "
                              + ", ".join(sorted(stale.values_list("line_number", flat=True))))
            stale.delete()

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
             "message": "Ordinary business income exists but no §199A QBI information on line 17d. Most S-Corps must report QBI items for the shareholder's §199A computation."},
            {"diagnostic_id": "D005", "title": "AE&P dividends on 17c — 1099-DIV, not K-1", "severity": "info",
             "condition": "aep_distributions > 0",
             "message": "Line 17c dividend distributions paid from accumulated earnings and profits must be reported to shareholders on Form 1099-DIV — do NOT report them on Schedule K-1, and do NOT include them in line 16d distributions (i1120s 2025 p.40)."},
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
            {"scenario_name": "Other rental netting — line 3c = 3a minus 3b",
             "scenario_type": "normal",
             "inputs": {"other_gross_rental_income": 12000, "other_rental_expenses": 4000},
             "expected_outputs": {"k_line_3c": 8000},
             "notes": "Face line 3c: subtract 3b from 3a. Only the 8,000 net flows to K-1 Box 3.",
             "sort_order": 4},
            {"scenario_name": "Line 18 reconciliation — separately stated items and 16f",
             "scenario_type": "normal",
             "inputs": {"ordinary_business_income": 150000, "interest_income": 5000, "section_179_deduction": 30000, "charitable_contributions_cash": 10000, "foreign_taxes_paid": 2000},
             "expected_outputs": {"k_line_18": 113000},
             "notes": "150,000 + 5,000 (lines 1-10) - 40,000 (lines 11-12e) - 2,000 (16f) = 113,000. K18 equals M-1 line 8, NOT Page 1 line 22 (which stays 150,000).",
             "sort_order": 5},
            {"scenario_name": "AE&P dividend distributions — 17c to 1099-DIV",
             "scenario_type": "normal",
             "inputs": {"ordinary_business_income": 80000, "aep_distributions": 25000},
             "expected_outputs": {"k_line_17c": 25000},
             "notes": "17c dividends from accumulated E&P are 1099-DIV items — never on the K-1 and never in 16d.",
             "sort_order": 6},
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
            notes=(
                "Each shareholder receives a K-1. Subject to basis/at-risk/passive "
                "limitations. 2025-face renumber (2026-07-11, audit unit #3): rebuilt "
                "verbatim vs f1120ssk.pdf 2025 (Part I A-D, Part II E-I, Part III "
                "boxes 1-19) + the i1120s 2025 pp.30-48 code tables. The box 12/13 "
                "code letters are NOT the Schedule K sub-line letters: 13a→C, 13b→D, "
                "13c→E, 13d→F, 13e→G, 13f→I; box 13 codes A/B mean the nuclear "
                "power credits (2023+ re-lettering)."
            ),
        )

        # 2025 face Part I item D + Part II items E-I (f1120ssk.pdf 2025 verbatim);
        # Part III box facts; basis-limitation inputs.
        self._upsert_facts(form, [
            {"fact_key": "shareholder_name", "label": "Item F1 — Shareholder's name, address, city, state, and ZIP code", "data_type": "string", "required": True, "sort_order": 1},
            {"fact_key": "shareholder_tin", "label": "Item E — Shareholder's identifying number", "data_type": "string", "required": True, "sort_order": 2},
            {"fact_key": "responsible_party_tin", "label": "Item F2 — Responsible party TIN (disregarded entity/trust/estate/nominee shareholder)", "data_type": "string", "sort_order": 3},
            {"fact_key": "responsible_party_name", "label": "Item F2 — Responsible party name", "data_type": "string", "sort_order": 4},
            {"fact_key": "shareholder_entity_type", "label": "Item F3 — What type of entity is this shareholder?", "data_type": "string", "sort_order": 5},
            {"fact_key": "ownership_percentage", "label": "Item G — Current year allocation percentage", "data_type": "decimal", "required": True, "sort_order": 6},
            {"fact_key": "shares_owned_start", "label": "Item H — Shareholder's number of shares, beginning of tax year", "data_type": "integer", "sort_order": 7},
            {"fact_key": "shares_owned_end", "label": "Item H — Shareholder's number of shares, end of tax year", "data_type": "integer", "sort_order": 8},
            {"fact_key": "loans_from_shareholder_boy", "label": "Item I — Loans from shareholder, beginning of tax year", "data_type": "decimal", "sort_order": 9},
            {"fact_key": "loans_from_shareholder_eoy", "label": "Item I — Loans from shareholder, end of tax year", "data_type": "decimal", "sort_order": 10},
            {"fact_key": "corp_total_shares_boy", "label": "Item D — Corporation's total number of shares, beginning of tax year", "data_type": "integer", "sort_order": 11},
            {"fact_key": "corp_total_shares_eoy", "label": "Item D — Corporation's total number of shares, end of tax year", "data_type": "integer", "sort_order": 12},
            # Box values (allocated from K)
            {"fact_key": "box_1_ordinary_income", "label": "Box 1 — Ordinary business income (loss)", "data_type": "decimal", "sort_order": 20},
            {"fact_key": "box_2_rental_real_estate", "label": "Box 2 — Net rental real estate income (loss)", "data_type": "decimal", "sort_order": 21},
            {"fact_key": "box_3_other_rental", "label": "Box 3 — Other net rental income (loss)", "data_type": "decimal", "sort_order": 22},
            {"fact_key": "box_4_interest", "label": "Box 4 — Interest income", "data_type": "decimal", "sort_order": 23},
            {"fact_key": "box_5a_ordinary_dividends", "label": "Box 5a — Ordinary dividends", "data_type": "decimal", "sort_order": 24},
            {"fact_key": "box_5b_qualified_dividends", "label": "Box 5b — Qualified dividends", "data_type": "decimal", "sort_order": 25},
            {"fact_key": "box_6_royalties", "label": "Box 6 — Royalties", "data_type": "decimal", "sort_order": 26},
            {"fact_key": "box_7_net_stcg", "label": "Box 7 — Net short-term capital gain (loss)", "data_type": "decimal", "sort_order": 27},
            {"fact_key": "box_8a_net_ltcg", "label": "Box 8a — Net long-term capital gain (loss)", "data_type": "decimal", "sort_order": 28},
            {"fact_key": "box_8b_collectibles", "label": "Box 8b — Collectibles (28%) gain (loss)", "data_type": "decimal", "sort_order": 29},
            {"fact_key": "box_8c_unrecaptured_1250", "label": "Box 8c — Unrecaptured §1250 gain", "data_type": "decimal", "sort_order": 30},
            {"fact_key": "box_9_net_1231", "label": "Box 9 — Net §1231 gain (loss)", "data_type": "decimal", "sort_order": 31},
            {"fact_key": "box_10_other_income", "label": "Box 10 — Other income (loss) (codes A–ZZ)", "data_type": "decimal", "sort_order": 32},
            {"fact_key": "box_11_section_179", "label": "Box 11 — §179 deduction", "data_type": "decimal", "sort_order": 33},
            {"fact_key": "box_12_other_deductions", "label": "Box 12 — Other deductions (codes A–ZZ)", "data_type": "decimal", "sort_order": 34},
            {"fact_key": "box_13_credits", "label": "Box 13 — Credits (codes per the 2025 table — see R013)", "data_type": "decimal", "sort_order": 35},
            {"fact_key": "box_14_k3_attached", "label": "Box 14 — Schedule K-3 is attached if checked", "data_type": "boolean", "default_value": "false", "sort_order": 36},
            {"fact_key": "box_15_amt_items", "label": "Box 15 — Alternative minimum tax (AMT) items (codes A–F)", "data_type": "decimal", "sort_order": 37},
            {"fact_key": "box_16a_tax_exempt_interest", "label": "Box 16 code A — Tax-exempt interest income", "data_type": "decimal", "sort_order": 38},
            {"fact_key": "box_16b_other_tax_exempt", "label": "Box 16 code B — Other tax-exempt income", "data_type": "decimal", "sort_order": 39},
            {"fact_key": "box_16c_nondeductible", "label": "Box 16 code C — Nondeductible expenses", "data_type": "decimal", "sort_order": 40},
            {"fact_key": "box_16d_distributions", "label": "Box 16 code D — Distributions (per-recipient actuals, never allocated)", "data_type": "decimal", "sort_order": 41},
            {"fact_key": "box_16e_loan_repayment", "label": "Box 16 code E — Repayment of loans from shareholders (per-recipient actuals)", "data_type": "decimal", "sort_order": 42},
            {"fact_key": "box_16f_foreign_taxes", "label": "Box 16 code F — Foreign taxes paid or accrued", "data_type": "decimal", "sort_order": 43},
            {"fact_key": "box_17a_investment_income", "label": "Box 17 code A — Investment income", "data_type": "decimal", "sort_order": 44},
            {"fact_key": "box_17b_investment_expenses", "label": "Box 17 code B — Investment expenses", "data_type": "decimal", "sort_order": 45},
            {"fact_key": "box_17_other_info", "label": "Box 17 — Other information (17d statement items, codes C–BA + ZZ; V = §199A)", "data_type": "decimal", "sort_order": 46},
            {"fact_key": "box_18_multiple_at_risk", "label": "Box 18 — More than one activity for at-risk purposes (see attached statement)", "data_type": "boolean", "default_value": "false", "sort_order": 47},
            {"fact_key": "box_19_multiple_passive", "label": "Box 19 — More than one activity for passive activity purposes (see attached statement)", "data_type": "boolean", "default_value": "false", "sort_order": 48},
            # Basis limitation inputs
            {"fact_key": "stock_basis_boy", "label": "Stock basis — beginning of year", "data_type": "decimal", "sort_order": 50},
            {"fact_key": "debt_basis", "label": "Debt basis — direct loans to S-Corp", "data_type": "decimal", "sort_order": 51},
            {"fact_key": "at_risk_amount", "label": "At-risk amount (Form 6198)", "data_type": "decimal", "sort_order": 52},
        ])

        # In-loader stale-fact self-heal (the s56 rename-orphan class guard).
        _K1_FACT_KEYS = {
            "shareholder_name", "shareholder_tin", "responsible_party_tin",
            "responsible_party_name", "shareholder_entity_type",
            "ownership_percentage", "shares_owned_start", "shares_owned_end",
            "loans_from_shareholder_boy", "loans_from_shareholder_eoy",
            "corp_total_shares_boy", "corp_total_shares_eoy",
            "box_1_ordinary_income", "box_2_rental_real_estate", "box_3_other_rental",
            "box_4_interest", "box_5a_ordinary_dividends", "box_5b_qualified_dividends",
            "box_6_royalties", "box_7_net_stcg", "box_8a_net_ltcg", "box_8b_collectibles",
            "box_8c_unrecaptured_1250", "box_9_net_1231", "box_10_other_income",
            "box_11_section_179", "box_12_other_deductions", "box_13_credits",
            "box_14_k3_attached", "box_15_amt_items",
            "box_16a_tax_exempt_interest", "box_16b_other_tax_exempt",
            "box_16c_nondeductible", "box_16d_distributions", "box_16e_loan_repayment",
            "box_16f_foreign_taxes", "box_17a_investment_income",
            "box_17b_investment_expenses", "box_17_other_info",
            "box_18_multiple_at_risk", "box_19_multiple_passive",
            "stock_basis_boy", "debt_basis", "at_risk_amount",
        }
        stale_facts = FormFact.objects.filter(tax_form=form).exclude(fact_key__in=_K1_FACT_KEYS)
        if stale_facts.exists():
            self.stdout.write(f"  deleting {stale_facts.count()} stale K-1 facts: "
                              + ", ".join(sorted(stale_facts.values_list("fact_key", flat=True))))
            stale_facts.delete()

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
            {"rule_id": "R017", "title": "Box 17 allocation — QBI (code V)", "rule_type": "calculation",
             "formula": "k_line_17_qbi_items * ownership_percentage",
             "inputs": ["qbi_ordinary_income", "qbi_w2_wages", "qbi_ubia", "ownership_percentage"],
             "outputs": ["box_17_other_info"],
             "description": ("Box 17 code V = §199A information. i1120s 2025 p.43 verbatim: use the "
                             "code with an asterisk (V*) in box 17 and enter 'STMT' — the statement "
                             "separately identifies the shareholder's pro rata share of qualified items, "
                             "W-2 wages, and UBIA. Used for the §199A computation on the 1040."),
             "sort_order": 17, "precedence": 1},
            # ── 2025 CODE-ASSIGNMENT RULES (renumber unit #3, 2026-07-11) ──
            # The K-1 box code letters come from the i1120s 2025 code tables,
            # NOT from the Schedule K sub-line letters.
            {"rule_id": "R012", "title": "Box 12 code assignment (2025 table)", "rule_type": "calculation",
             "formula": ("K 12a cash charitable → code A (60% limit) or B (30% limit); noncash "
                         "charitable (K 12b) → codes C (50%), D (30%), E (cap-gain property to 50% "
                         "org, 30%), F (cap-gain property, 20%), G (100%); K 12c investment interest "
                         "expense → code H; K 12d section 59(e)(2) expenditures → code J; K 12e other "
                         "deductions → per-item codes I/L/M/O/W/X/Y/Z/AA/AB/AC or ZZ (catch-all)."),
             "inputs": ["box_12_other_deductions"], "outputs": [],
             "description": ("i1120s 2025 pp.32-34 verbatim: 'Report each shareholder's pro rata share "
                             "of cash charitable contributions in box 12 of Schedule K-1 using code A "
                             "or B, as applicable' · noncash 'using codes C through G' · investment "
                             "interest 'using code H' · §59(e) 'using code J'. Code I = Deductions—"
                             "royalty income; code L = Deductions—portfolio (other) — NEITHER is the "
                             "§59(e)/other-deductions code. ZZ items print ZZ* with a typed statement. "
                             "Codes K, N, P–V, AD–AJ are reserved for future use (2025)."),
             "sort_order": 12, "precedence": 1},
            {"rule_id": "R013", "title": "Box 13 code assignment (2025 table)", "rule_type": "calculation",
             "formula": ("K 13a LIH §42(j)(5) → code C; K 13b LIH other → code D; K 13c qualified "
                         "rehab (rental RE) → code E; K 13d other rental RE credits → code F; K 13e "
                         "other rental credits → code G; K 13f biofuel producer → code I; K 13g other "
                         "credits → the credit's own code (A, B, H, or J through BC; 8941 = BA) or ZZ."),
             "inputs": ["box_13_credits"], "outputs": [],
             "description": ("i1120s 2025 pp.34-37 verbatim per line ('Use code C…', 'Use code D…', "
                             "'using code E/F/G/I', 13g: 'Enter the applicable code, A, B, H, or J "
                             "through BC'). ⚠ The 2025 box 13 alphabet is NOT the Schedule K sub-line "
                             "letters: codes A/B = zero-emission nuclear / advanced nuclear (2023+ "
                             "re-lettering); printing A for LIH §42(j)(5) claims the wrong credit. "
                             "8941 small-employer health premiums = code BA. Codes AN, BD–BG reserved."),
             "sort_order": 13, "precedence": 1},
            {"rule_id": "R014", "title": "Box 14 — Schedule K-3 checkbox", "rule_type": "validation",
             "formula": "box_14_k3_attached = (a Schedule K-3 is attached for this shareholder)",
             "inputs": ["box_14_k3_attached"], "outputs": [],
             "description": "2025 face box 14: 'Schedule K-3 is attached if checked.' Check when international items require a K-3.",
             "sort_order": 14, "precedence": 1},
            {"rule_id": "R015", "title": "Box 15 AMT codes A–F", "rule_type": "calculation",
             "formula": "K 15a–15f → box 15 codes A–F respectively (pro rata)",
             "inputs": ["box_15_amt_items"], "outputs": [],
             "description": ("i1120s 2025 p.39 verbatim: 'Report each shareholder's pro rata share of "
                             "amounts reported on lines 15a through 15f in box 15 of Schedule K-1 "
                             "using codes A through F, respectively.' Multiple 15f items → F* + STMT."),
             "sort_order": 15, "precedence": 1},
            {"rule_id": "R016", "title": "Box 16 codes A–F; D/E per-recipient", "rule_type": "calculation",
             "formula": ("K 16a/16b/16c/16f → box 16 codes A/B/C/F pro rata; 16d distributions → code "
                         "D and 16e loan repayments → code E on the RECEIVING shareholder's K-1 only "
                         "(actuals, never allocated)."),
             "inputs": ["box_16a_tax_exempt_interest", "box_16b_other_tax_exempt", "box_16c_nondeductible",
                        "box_16d_distributions", "box_16e_loan_repayment", "box_16f_foreign_taxes"],
             "outputs": [],
             "description": ("i1120s 2025 pp.39-40 verbatim: lines 16a/16b/16c/16f report 'using codes "
                             "A, B, C, and F, respectively'; 'Report property distributions (line 16d) "
                             "and repayment of loans from shareholders (line 16e) on the Schedule K-1 "
                             "of the shareholder(s) that received the distributions or repayments "
                             "(using codes D and E).'"),
             "sort_order": 16, "precedence": 1},
            {"rule_id": "R021", "title": "Box 17 codes — 2025 table", "rule_type": "calculation",
             "formula": ("K 17a investment income → code A; K 17b investment expenses → code B; 17d "
                         "statement items → own codes C–BA (V = §199A, K = §179-property dispositions, "
                         "AC = §448(c) gross receipts, BA = domestic research expenditures) or ZZ. "
                         "K 17c AE&P dividends are NEVER on the K-1 (Form 1099-DIV only)."),
             "inputs": ["box_17a_investment_income", "box_17b_investment_expenses", "box_17_other_info"],
             "outputs": [],
             "description": ("i1120s 2025 pp.40-48: 17a/17b report 'using codes A and B, respectively'; "
                             "17d items carry the pp.40-48 code list (C rehab non-rental, D energy-"
                             "property basis, E/F LIH recapture, G/H credit recapture, I/J look-back, "
                             "K/L §179 dispositions/recapture, M–R info items, U NII, V §199A, AA/AB "
                             "§163(j) items, AC §448(c) gross receipts, AJ excess business loss, AN "
                             "farming/fishing, AP inversion gain, AS–AV credit-property bases, AW "
                             "reportable transactions, BA domestic research, ZZ other). >2%-shareholder "
                             "health insurance has NO enumerated code — i1120s p.17: it is a W-2 box 14 "
                             "information item; on the K-1 it may ride only as a ZZ other-information "
                             "statement item, never code AC."),
             "sort_order": 21, "precedence": 1},
            # ── ROUNDING LEG (2026-07-08, Ken ruling: residual-offset allocator) ──
            {"rule_id": "R-K1-ROUND", "title": "Whole-dollar K-1 rounding — residual to the LAST shareholder", "rule_type": "calculation",
             "formula": ("For each Schedule K dollar line: every shareholder EXCEPT the last (canonical "
                         "K-1 order) gets round_half_up(K_line × ownership_pct) to whole dollars; the "
                         "LAST shareholder gets K_line − Σ(the other shareholders' rounded shares) — the "
                         "whole-dollar rounding residual — so Σ over all shareholders == the Schedule K "
                         "line EXACTLY."),
             "inputs": ["ownership_percentage"], "outputs": [],
             "description": ("§1377(a) strict per-share-per-day pro-rata plus whole-dollar reporting "
                             "necessarily puts a $1 offset SOMEWHERE on an odd split — independent "
                             "per-shareholder rounding instead drifts Σ K-1 vs Schedule K (a 50/50 split "
                             "of 3,575 rounds to 1,788+1,788=3,576). The IRS ATS 1120-S Scenario-5 key "
                             "penny-offsets to the second shareholder (K-1s print 1,788/1,787 · "
                             "5,732/5,731). Applies to every pro-rated dollar box (1-17) and the QBI "
                             "statement dollar items; shareholder-specific amounts (box 16 codes D/E "
                             "distributions and loan repayments, the box 17 health-insurance "
                             "information item — a ZZ statement item, NOT code AC, which means §448(c) "
                             "gross receipts on the 2025 table) are never allocated so never carry a "
                             "residual. Ken ruling 2026-07-08 (tax-app REVIEW_QUEUE)."),
             "sort_order": 21, "precedence": 2},
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
            ("R012", "IRS_2025_1120S_INSTR", "primary", "pp.32-34 — box 12 code assignments (A/B cash, C-G noncash, H investment interest, J §59(e)(2), ZZ other; verbatim excerpts)"),
            ("R013", "IRS_2025_1120S_INSTR", "primary", "pp.34-37 — box 13 code assignments (13a→C … 13f→I; 13g own codes A/B/H/J-BC incl. 8941=BA; verbatim excerpts)"),
            ("R014", "IRS_2025_1120S_INSTR", "primary", "2025 face box 14 — Schedule K-3 attached checkbox"),
            ("R015", "IRS_2025_1120S_INSTR", "primary", "p.39 — box 15 codes A-F respectively (verbatim excerpt)"),
            ("R016", "IRS_2025_1120S_INSTR", "primary", "pp.39-40 — box 16 codes A/B/C/F pro rata; D/E per-recipient (verbatim excerpt)"),
            ("R021", "IRS_2025_1120S_INSTR", "primary", "pp.40-48 — box 17 code list (A/B, C-BA, ZZ); p.17 health insurance = W-2 box 14 item (verbatim excerpts)"),
            ("R-K1-ROUND", "IRC_1377", "primary", "§1377(a) strict pro-rata — whole-dollar reporting forces the residual somewhere; last-shareholder offset keeps Σ == Schedule K"),
            ("R-K1-ROUND", "IRS_2025_1120S_K1_INSTR", "secondary", "Whole-dollar reporting convention; the ATS Scenario-5 key's 1,788/1,787 residual-offset behavior"),
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
            {"line_number": "Box10", "description": "Other income (loss) (codes A–ZZ)", "line_type": "calculated", "destination_form": "See K-1 instructions per code", "sort_order": 13,
             "notes": ("2025 codes (i1120s pp.30-31): A other portfolio income · B involuntary conversions · "
                       "C §1256 contracts/straddles · D mining exploration recapture · E §951A(a) inclusions · "
                       "F subpart F inclusions · G §951(a)(1)(B) inclusions · I oil/gas/geothermal disposition "
                       "gain (loss) · J tax-benefit recoveries · K gambling gains/losses · M/N §1045 rollover "
                       "gain · O QSB §1202 exclusion · S non-portfolio capital gain (loss) · ZZ other "
                       "(ZZ* + typed statement). H, L, P–R, T–X reserved (2025).")},
            {"line_number": "Box11", "description": "§179 deduction", "line_type": "calculated", "source_rules": ["R011"], "destination_form": "Form 4562 (shareholder's own)", "sort_order": 14},
            {"line_number": "Box12", "description": "Other deductions (codes A–ZZ per the 2025 table)", "line_type": "calculated", "source_rules": ["R012"], "destination_form": "Schedule A / Form 4952 / etc. per code", "sort_order": 15,
             "notes": ("2025 codes (i1120s pp.32-34): A cash charitable 60% · B cash charitable 30% · C noncash "
                       "50% · D noncash 30% · E cap-gain property to 50% org (30%) · F cap-gain property 20% · "
                       "G contributions 100% · H investment interest expense · I deductions—royalty income · "
                       "J §59(e)(2) expenditures · L deductions—portfolio (other) · M preproductive period · "
                       "O reforestation · W soil/water conservation · X film/TV/sound production · Y barrier "
                       "removal · Z itemized deductions · AA CCF contributions · AB early-withdrawal penalty · "
                       "AC interest on debt-financed distributions · ZZ other (ZZ* + typed statement). "
                       "K, N, P–V, AD–AJ reserved (2025).")},
            {"line_number": "Box13", "description": "Credits (2025 codes: 13a→C, 13b→D, 13c→E, 13d→F, 13e→G, 13f→I; 13g per-credit)", "line_type": "calculated", "source_rules": ["R013"], "destination_form": "Form 3800 / source-form per code", "sort_order": 16,
             "notes": ("2025 codes (i1120s pp.34-37): C LIH §42(j)(5) · D LIH other · E qualified rehab (rental "
                       "RE) · F other rental RE credits · G other rental credits · I biofuel producer. 13g "
                       "credits carry their OWN codes: A zero-emission nuclear · B advanced nuclear · H "
                       "undistributed capital gains · J work opportunity · K disabled access · L empowerment "
                       "zone · M research · N employer SS/Medicare tips · O backup withholding · P–U unused "
                       "investment credits from cooperatives · V advanced manufacturing production · W clean "
                       "electricity production · X clean fuel · Y clean hydrogen · Z orphan drug · AA enhanced "
                       "oil recovery · AB renewable electricity · AC biodiesel/SAF · AD new markets · AE small-"
                       "employer pension startup · AF auto-enrollment · AG military spouse · AH employer "
                       "childcare · AI low-sulfur diesel · AJ railroad track maintenance · AK marginal wells · "
                       "AL distilled spirits · AM energy-efficient home · AO alt-fuel refueling · AP–AU bond "
                       "credits · AV differential wage · AW/AX carbon oxide sequestration · AY new clean "
                       "vehicle · AZ commercial clean vehicle · BA small-employer health insurance (8941) · "
                       "BB paid family/medical leave · BC §6418 transferred credits · ZZ other. ⚠ NOT the "
                       "Schedule K sub-line letters — A≠LIH on the 2025 face.")},
            {"line_number": "Box14", "description": "Schedule K-3 is attached if checked", "line_type": "input", "source_rules": ["R014"], "source_facts": ["box_14_k3_attached"], "destination_form": "Schedule K-3", "sort_order": 17},
            {"line_number": "Box15", "description": "Alternative minimum tax (AMT) items (codes A–F = K lines 15a–15f)", "line_type": "calculated", "source_rules": ["R015"], "destination_form": "Form 6251", "sort_order": 18,
             "notes": "A post-1986 depreciation adjustment · B adjusted gain/loss · C depletion (non-oil/gas) · D oil/gas/geothermal gross income · E oil/gas/geothermal deductions · F other AMT items (F* + STMT when multiple)."},
            {"line_number": "Box16", "description": "Items affecting shareholder basis (codes A–F)", "line_type": "calculated", "source_rules": ["R016"], "destination_form": "Form 7203", "sort_order": 19,
             "notes": "A tax-exempt interest · B other tax-exempt income · C nondeductible expenses · D distributions (per-recipient) · E repayment of loans from shareholders (per-recipient) · F foreign taxes paid or accrued."},
            {"line_number": "Box17", "description": "Other information (codes A–BA + ZZ; V = §199A)", "line_type": "calculated", "source_rules": ["R017", "R021"], "destination_form": "Form 8995/8995-A (V) / per code", "sort_order": 20,
             "notes": ("A investment income · B investment expenses · C qualified rehab (non-rental) · D energy-"
                       "property basis · E/F LIH recapture · G investment-credit recapture · H other credit "
                       "recapture · I/J look-back interest · K §179-property dispositions · L §179 recapture · "
                       "M §453(l)(3) · N §453A(c) · O §1260(b) · P production-expenditure interest · Q CCF "
                       "withdrawals · R oil/gas depletion · U net investment income · V §199A (V* + STMT) · "
                       "AA excess taxable income · AB excess business interest income · AC §448(c) gross "
                       "receipts · AJ excess business loss · AN farming/fishing · AP inversion gain · AS–AV "
                       "credit-property bases · AW reportable transactions · BA domestic research expenditures · "
                       "ZZ other information. W–Z, AD–AI, AK–AM, AO, AQ–AR, AX–AZ reserved (2025). K line 17c "
                       "AE&P dividends NEVER print here (1099-DIV only).")},
            {"line_number": "Box18", "description": "More than one activity for at-risk purposes (checkbox; attach statement)", "line_type": "input", "source_facts": ["box_18_multiple_at_risk"], "destination_form": "Form 6198 (per activity)", "sort_order": 21},
            {"line_number": "Box19", "description": "More than one activity for passive activity purposes (checkbox; attach statement)", "line_type": "input", "source_facts": ["box_19_multiple_passive"], "destination_form": "Form 8582 (per activity)", "sort_order": 22},
            # Part I / Part II header items (2025 face)
            {"line_number": "ItemA", "description": "Part I A — Corporation's employer identification number", "line_type": "input", "sort_order": 30},
            {"line_number": "ItemB", "description": "Part I B — Corporation's name, address, city, state, and ZIP code", "line_type": "input", "sort_order": 31},
            {"line_number": "ItemC", "description": "Part I C — IRS Center where corporation filed return", "line_type": "input", "sort_order": 32},
            {"line_number": "ItemD", "description": "Part I D — Corporation's total number of shares (beginning/end of tax year)", "line_type": "input", "source_facts": ["corp_total_shares_boy", "corp_total_shares_eoy"], "sort_order": 33},
            {"line_number": "ItemE", "description": "Part II E — Shareholder's identifying number", "line_type": "input", "source_facts": ["shareholder_tin"], "sort_order": 34},
            {"line_number": "ItemF1", "description": "Part II F1 — Shareholder's name, address, city, state, and ZIP code", "line_type": "input", "source_facts": ["shareholder_name"], "sort_order": 35},
            {"line_number": "ItemF2", "description": "Part II F2 — Responsible party (disregarded entity/trust/estate/nominee shareholder): TIN + name", "line_type": "input", "source_facts": ["responsible_party_tin", "responsible_party_name"], "sort_order": 36},
            {"line_number": "ItemF3", "description": "Part II F3 — What type of entity is this shareholder?", "line_type": "input", "source_facts": ["shareholder_entity_type"], "sort_order": 37},
            {"line_number": "ItemG", "description": "Part II G — Current year allocation percentage", "line_type": "input", "source_facts": ["ownership_percentage"], "sort_order": 38},
            {"line_number": "ItemH", "description": "Part II H — Shareholder's number of shares (beginning/end of tax year)", "line_type": "input", "source_facts": ["shares_owned_start", "shares_owned_end"], "sort_order": 39},
            {"line_number": "ItemI", "description": "Part II I — Loans from shareholder (beginning/end of tax year)", "line_type": "input", "source_facts": ["loans_from_shareholder_boy", "loans_from_shareholder_eoy"], "sort_order": 40},
        ])

        # In-loader stale-line self-heal (2025 face set; the s56 rename-orphan guard).
        _K1_LINES = {
            "Box1", "Box2", "Box3", "Box4", "Box5a", "Box5b", "Box6", "Box7",
            "Box8a", "Box8b", "Box8c", "Box9", "Box10", "Box11", "Box12", "Box13",
            "Box14", "Box15", "Box16", "Box17", "Box18", "Box19",
            "ItemA", "ItemB", "ItemC", "ItemD", "ItemE", "ItemF1", "ItemF2",
            "ItemF3", "ItemG", "ItemH", "ItemI",
        }
        stale_lines = FormLine.objects.filter(tax_form=form).exclude(line_number__in=_K1_LINES)
        if stale_lines.exists():
            self.stdout.write(f"  deleting {stale_lines.count()} stale K-1 line rows: "
                              + ", ".join(sorted(stale_lines.values_list("line_number", flat=True))))
            stale_lines.delete()

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
            {"diagnostic_id": "D004", "title": "Pre-2023 box 13 code letters", "severity": "error",
             "condition": "box 13 code letters mirror the Schedule K sub-line letters (A=LIH §42(j)(5), B=LIH other, C=rehab, D=other rental RE, F=biofuel)",
             "message": "The 2025 K-1 box 13 codes are NOT the Schedule K sub-line letters: 13a→C, 13b→D, 13c→E, 13d→F, 13e→G, 13f→I (i1120s 2025 pp.34-37). On the 2025 table, codes A/B mean the zero-emission / advanced nuclear power credits — printing A for a low-income housing credit claims the wrong credit."},
            {"diagnostic_id": "D005", "title": "Health insurance is not box 17 code AC", "severity": "error",
             "condition": ">2%-shareholder health insurance premiums reported in box 17 under code AC",
             "message": "i1120s 2025 p.17: report >2%-shareholder health insurance as an information item in box 14 of that shareholder's Form W-2. It has NO enumerated K-1 code; box 17 code AC means gross receipts for section 448(c) on the 2025 table. If shown on the K-1 at all, it rides code ZZ (other information) with a statement."},
            {"diagnostic_id": "D006", "title": "Charitable code A assumes 60%-limit cash", "severity": "warning",
             "condition": "all charitable contributions coded A without a limitation-category split",
             "message": "Box 12 code A = cash contributions (60% AGI limit) only. 30%-limit cash = code B; noncash = codes C–G by category (i1120s 2025 pp.32-33). Verify the contribution category before coding."},
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
            # ── ROUNDING LEG (2026-07-08) ──
            {"scenario_name": "Residual-offset rounding — 50/50 split of an odd K line (ATS S5 K2)",
             "scenario_type": "edge",
             "inputs": {"shareholders": [{"ownership_percentage": 0.5}, {"ownership_percentage": 0.5}],
                        "net_rental_real_estate_income": 3575},
             "expected_outputs": {"box_2_first_shareholder": 1788, "box_2_last_shareholder": 1787,
                                  "box_2_sum": 3575},
             "notes": ("R-K1-ROUND: first shareholder = round_half_up(3,575 × 0.5) = 1,788; LAST "
                       "shareholder = 3,575 − 1,788 = 1,787 (the residual). Σ == Schedule K line 2 "
                       "EXACTLY (never 1,788+1,788=3,576). Matches the ATS Scenario-5 key. Same "
                       "mechanics: K11 11,463 → 5,732/5,731."), "sort_order": 3},
            # ── 2025 CODE-TABLE PINS (renumber unit #3, 2026-07-11) ──
            {"scenario_name": "Box 13 code letters — 2025 table",
             "scenario_type": "normal",
             "inputs": {"ownership_percentage": 1.0, "lih_credit_42j5": 5000, "biofuel_producer_credit": 1200, "credit_8941": 51014},
             "expected_outputs": {"box13_code_lih_42j5": "C", "box13_code_biofuel": "I", "box13_code_8941": "BA"},
             "notes": ("R013: K 13a → box 13 code C (NOT A — A means zero-emission nuclear on the 2025 "
                       "table); 13f biofuel → code I (NOT F — F means other rental RE credits); the 8941 "
                       "small-employer health premium credit on 13g → code BA (i8941 2025 verbatim)."),
             "sort_order": 4},
            {"scenario_name": "Box 12 code letters — H / J / ZZ",
             "scenario_type": "normal",
             "inputs": {"ownership_percentage": 1.0, "investment_interest_expense": 3000, "sec_59e2_expenditures": 8000, "other_deductions": 500},
             "expected_outputs": {"box12_code_inv_interest": "H", "box12_code_59e2": "J", "box12_code_other": "ZZ"},
             "notes": ("R012: investment interest → H; §59(e)(2) → J (NOT I — I means deductions—royalty "
                       "income); an uncategorized other-deductions amount → ZZ (ZZ* + typed statement), "
                       "NOT L (L means deductions—portfolio (other))."),
             "sort_order": 5},
            {"scenario_name": "Box 16 D/E per-recipient — never allocated",
             "scenario_type": "edge",
             "inputs": {"shareholders": [{"ownership_percentage": 0.5, "distributions": 30000},
                                          {"ownership_percentage": 0.5, "distributions": 10000}]},
             "expected_outputs": {"box16d_first_shareholder": 30000, "box16d_last_shareholder": 10000},
             "notes": "R016: 16d/16e go on the RECEIVING shareholder's K-1 as actuals (codes D/E) — a 50/50 ownership split does NOT split a 40,000 distribution 20,000/20,000.",
             "sort_order": 6},
            {"scenario_name": "Health insurance — ZZ information item, never AC",
             "scenario_type": "edge",
             "inputs": {"ownership_percentage": 1.0, "shareholder_health_insurance_premiums": 12000},
             "expected_outputs": {"box17_code_health_insurance": "ZZ", "w2_box14_item": 12000},
             "notes": ("R021/D005: i1120s 2025 p.17 — the official channel is W-2 box 14; box 17 code AC "
                       "means §448(c) gross receipts. Any K-1 presentation rides ZZ + statement."),
             "sort_order": 7},
        ])

        # In-loader stale-scenario self-heal (the RET-G5 rename-orphan guard).
        _K1_SCENARIOS = {
            "Simple K-1 — all income, no limitations",
            "Loss limitation triggered",
            "Residual-offset rounding — 50/50 split of an odd K line (ATS S5 K2)",
            "Box 13 code letters — 2025 table",
            "Box 12 code letters — H / J / ZZ",
            "Box 16 D/E per-recipient — never allocated",
            "Health insurance — ZZ information item, never AC",
        }
        stale_tests = TestScenario.objects.filter(tax_form=form).exclude(scenario_name__in=_K1_SCENARIOS)
        if stale_tests.exists():
            self.stdout.write(f"  deleting {stale_tests.count()} stale K-1 scenarios: "
                              + ", ".join(sorted(stale_tests.values_list("scenario_name", flat=True))))
            stale_tests.delete()

        # Verbatim i1120s 2025 code-table excerpts on the existing corporation-
        # instructions source (fetched from resources/irs_forms/2025/i1120s.pdf,
        # pymupdf extraction 2026-07-11).
        instr = sources.get("IRS_2025_1120S_INSTR")
        if instr:
            for exc in [
                {"excerpt_label": "K-1 box 13 code assignments — 13a→C … 13f→I (2025)",
                 "location_reference": "i1120s (2025) pp.34-35, Lines 13a-13f Schedule K-1 paragraphs",
                 "excerpt_text": (
                     "Line 13a: \"Report in box 13 of Schedule K-1 each shareholder's pro rata share of the "
                     "low-income housing credit reported on Schedule K, line 13a. Use code C to report the "
                     "portion of the credit attributable to buildings placed in service after 2007.\" · Line "
                     "13b: \"Use code D…\" · Line 13c: \"Report each shareholder's pro rata share of qualified "
                     "rehabilitation expenditures related to rental real estate activities in box 13 of "
                     "Schedule K-1 using code E.\" · Line 13d: \"…other rental real estate credits using code "
                     "F.\" · Line 13e: \"…other rental credits using code G.\" · Line 13f: \"Report in box 13 of "
                     "Schedule K-1 each shareholder's pro rata share of the biofuel producer credit reported "
                     "on line 13f using code I.\""),
                 "summary_text": "2025 box 13 codes: 13a→C, 13b→D, 13c→E, 13d→F, 13e→G, 13f→I — NOT the Schedule K sub-line letters.",
                 "is_key_excerpt": True},
                {"excerpt_label": "K-1 box 13g — own code alphabet incl. 8941 = BA (2025)",
                 "location_reference": "i1120s (2025) pp.35-37, Line 13g",
                 "excerpt_text": (
                     "\"Enter the applicable code, A, B, H, or J through BC, in the column to the left of the "
                     "dollar amount entry space.\" The category list assigns: \"Zero-emission nuclear power "
                     "production credit (code A)\" · \"Credit for production from advanced nuclear power "
                     "facilities (code B)\" · … · \"Credit for small employer health insurance premiums "
                     "(code BA)\" · \"Employer credit for paid family and medical leave (code BB)\" · \"Eligible "
                     "credits from transferor(s) under section 6418 (code BC)\" · \"Other credits (code ZZ)\"."),
                 "summary_text": "13g credits carry their own codes (A, B, H, J–BC + ZZ); the 8941 credit = code BA.",
                 "is_key_excerpt": True},
                {"excerpt_label": "K-1 box 12 code assignments (2025)",
                 "location_reference": "i1120s (2025) pp.32-34, Lines 12a-12e",
                 "excerpt_text": (
                     "\"Report each shareholder's pro rata share of cash charitable contributions in box 12 of "
                     "Schedule K-1 using code A or B, as applicable.\" · \"Report each shareholder's pro rata "
                     "share of charitable contributions in box 12 of Schedule K-1 using codes C through G for "
                     "each of the contribution categories shown earlier.\" · \"Report each shareholder's pro "
                     "rata share of investment interest expense in box 12 of Schedule K-1 using code H.\" · "
                     "\"Report each shareholder's pro rata share of section 59(e) expenditures in box 12 of "
                     "Schedule K-1 using code J.\" · \"Deductions—Royalty income (code I).\" · \"Deductions—"
                     "Portfolio income (other) (code L).\" · \"Other deductions (code ZZ).\""),
                 "summary_text": "2025 box 12: cash charitable A/B, noncash C–G, investment interest H, §59(e)(2) J (not I), other ZZ (not L).",
                 "is_key_excerpt": True},
                {"excerpt_label": "K-1 box 15 codes A–F respectively (2025)",
                 "location_reference": "i1120s (2025) p.39, Schedule K-1 AMT paragraph",
                 "excerpt_text": (
                     "Report each shareholder's pro rata share of amounts reported on lines 15a through 15f "
                     "in box 15 of Schedule K-1 using codes A through F, respectively."),
                 "summary_text": "Box 15 AMT items: K 15a–15f → codes A–F respectively.",
                 "is_key_excerpt": True},
                {"excerpt_label": "K-1 box 16 codes — A/B/C/F pro rata; D/E per-recipient (2025)",
                 "location_reference": "i1120s (2025) pp.39-40, Lines 16a-16f Schedule K-1 paragraphs",
                 "excerpt_text": (
                     "\"Report each shareholder's pro rata share of amounts reported on lines 16a, 16b, 16c, "
                     "and 16f (concerning items affecting shareholder basis) in box 16 of Schedule K-1 using "
                     "codes A, B, C, and F, respectively.\" · \"Report property distributions (line 16d) and "
                     "repayment of loans from shareholders (line 16e) on the Schedule K-1 of the "
                     "shareholder(s) that received the distributions or repayments (using codes D and E).\""),
                 "summary_text": "Box 16: A/B/C/F allocated pro rata; D (distributions) and E (loan repayments) are per-recipient actuals.",
                 "is_key_excerpt": True},
                {"excerpt_label": "K-1 box 17 codes A/B; 17d list runs C–BA + ZZ (2025)",
                 "location_reference": "i1120s (2025) pp.40-48, Lines 17a-17d",
                 "excerpt_text": (
                     "\"Report each shareholder's pro rata share of amounts reported on lines 17a and 17b "
                     "(investment income and expenses) in box 17 of Schedule K-1 using codes A and B, "
                     "respectively.\" Line 17d items carry their own codes, including \"Dispositions of "
                     "property with section 179 deductions (code K)\" · \"Net investment income (code U)\" · "
                     "\"Section 199A information (code V)\" · \"Gross receipts for section 448(c) (code AC)\" · "
                     "\"Domestic research or experimental expenditures (code BA)\" · \"Other information "
                     "(code ZZ)\"."),
                 "summary_text": "Box 17: 17a→A, 17b→B; 17d statement items C–BA + ZZ (V=§199A, K=§179 dispositions, AC=§448(c) gross receipts).",
                 "is_key_excerpt": True},
                {"excerpt_label": ">2%-shareholder health insurance → W-2 box 14 (2025)",
                 "location_reference": "i1120s (2025) p.17, Line 8 wages",
                 "excerpt_text": (
                     "Report amounts paid for health insurance coverage for a more-than-2% shareholder "
                     "(including that shareholder's spouse, dependents, and any children under age 27 who "
                     "aren't dependents) as an information item in box 14 of that shareholder's Form W-2."),
                 "summary_text": "Health insurance for >2% shareholders is a W-2 box 14 information item — no enumerated K-1 code exists (box 17 AC = §448(c) gross receipts).",
                 "is_key_excerpt": True},
            ]:
                AuthorityExcerpt.objects.update_or_create(
                    authority_source=instr, excerpt_label=exc["excerpt_label"], defaults=exc,
                )
            self.stdout.write("  7 i1120s code-table excerpts")

        self._upsert_form_links("K1_1120S", sources, [
            ("IRS_2025_1120S_INSTR", "governs"),
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
            # Header
            {"fact_key": "qof_disposal", "label": "Disposed of any investment in a qualified opportunity fund during the tax year?", "data_type": "boolean", "default_value": "false", "sort_order": 0,
             "notes": "Face header question (2025). Yes → attach Form 8949 with the QOF reporting."},
            # Per-transaction inputs (from Form 8949)
            {"fact_key": "description", "label": "Description of property", "data_type": "string", "required": True, "sort_order": 1},
            {"fact_key": "date_acquired", "label": "Date acquired", "data_type": "date", "required": True, "sort_order": 2},
            {"fact_key": "date_sold", "label": "Date sold", "data_type": "date", "required": True, "sort_order": 3},
            {"fact_key": "proceeds", "label": "Sales price (proceeds)", "data_type": "decimal", "required": True, "sort_order": 4},
            {"fact_key": "cost_basis", "label": "Cost or other basis", "data_type": "decimal", "required": True, "sort_order": 5},
            {"fact_key": "adjustment_code", "label": "Adjustment code", "data_type": "choice", "choices": ["B", "T", "W", "O"], "sort_order": 6},
            {"fact_key": "adjustment_amount", "label": "Adjustment amount", "data_type": "decimal", "sort_order": 7},
            # Other-form inflows (lines 4/5/6 short-term, 11/12/13/14 long-term)
            {"fact_key": "st_gain_6252", "label": "Short-term capital gain from installment sales (Form 6252) — line 4", "data_type": "decimal", "sort_order": 8},
            {"fact_key": "st_gain_8824", "label": "Short-term capital gain or (loss) from like-kind exchanges (Form 8824) — line 5", "data_type": "decimal", "sort_order": 9},
            # Aggregated totals
            {"fact_key": "total_short_term_gain_loss", "label": "Total net short-term capital gain (loss)", "data_type": "decimal", "sort_order": 10},
            {"fact_key": "total_long_term_gain_loss", "label": "Total net long-term capital gain (loss)", "data_type": "decimal", "sort_order": 11},
            {"fact_key": "lt_gain_6252", "label": "Long-term capital gain from installment sales (Form 6252) — line 11", "data_type": "decimal", "sort_order": 12},
            {"fact_key": "lt_gain_8824", "label": "Long-term capital gain or (loss) from like-kind exchanges (Form 8824) — line 12", "data_type": "decimal", "sort_order": 13},
            {"fact_key": "capital_gain_distributions", "label": "Capital gain distributions — line 13", "data_type": "decimal", "sort_order": 14},
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
             "formula": "L18 = min(L16, L17, SchB_line8_NUBIG); L20 = max(0, L18 - L19_1374b2_deduction); L21 = L20 * 0.21; L23 = max(0, L21 - L22_1374b3_credits) -> page 1 line 23b",
             "conditions": {"when": "built_in_gains_tax_applicable == true AND within the §1374(d)(7) 5-year recognition period"},
             "inputs": ["built_in_gains_tax_applicable", "net_recognized_built_in_gain", "net_unrealized_built_in_gain"],
             "outputs": ["big_tax"],
             "description": "C-Corp converting to S-Corp may owe BIG tax on built-in gains recognized within the 5-year recognition period. Part III chain (2025 face): line 18 = smallest of line 16 (excess recognized BIG), line 17 (taxable income), or Schedule B line 8 (net unrealized built-in gain); line 20 = 18 minus the §1374(b)(2) deduction; line 21 = 21%; line 23 = 21 minus §1374(b)(3) C-year credit carryforwards → Form 1120-S page 1 line 23b.",
             "notes": "NEEDS REVIEW — recognition period rules and carryover of unused BIG remain unreviewed; the line chain is 2025-face-verbatim (renumbered 2026-07-08).",
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

        # 2025-face line numbering (renumbered 2026-07-08, verified verbatim vs
        # f1120ssd.pdf 2025 + IRS1120SScheduleD.xsd LineNumber annotations; the
        # prior map carried a stale pre-2025 layout: 1a/1b/1c = the 8949 boxes,
        # 2/3 = 6252/8824, net ST on line 5 — the 2025 face nets on line 7).
        self._upsert_lines(form, [
            {"line_number": "QOF", "description": "Header: Did the corporation dispose of any investment(s) in a qualified opportunity fund during the tax year? (Yes → attach Form 8949 and see its instructions)", "line_type": "input", "source_facts": ["qof_disposal"], "sort_order": 0},
            # Part I — short-term
            {"line_number": "1a", "description": "Totals for all short-term transactions reported on Form 1099-B or Form 1099-DA for which basis was reported to the IRS and for which you have no adjustments (direct entry — no Form 8949; optional: may instead ride line 1b via 8949)", "line_type": "input", "sort_order": 1},
            {"line_number": "1b", "description": "Totals for all transactions reported on Form(s) 8949 with Box A or Box G checked", "line_type": "input", "sort_order": 2},
            {"line_number": "2", "description": "Totals for all transactions reported on Form(s) 8949 with Box B or Box H checked", "line_type": "input", "sort_order": 3},
            {"line_number": "3", "description": "Totals for all transactions reported on Form(s) 8949 with Box C or Box I checked", "line_type": "input", "sort_order": 4},
            {"line_number": "4", "description": "Short-term capital gain from installment sales from Form 6252, line 26 or 37", "line_type": "input", "source_facts": ["st_gain_6252"], "sort_order": 5},
            {"line_number": "5", "description": "Short-term capital gain or (loss) from like-kind exchanges from Form 8824", "line_type": "input", "source_facts": ["st_gain_8824"], "sort_order": 6},
            {"line_number": "6", "description": "Tax on short-term capital gain included on line 23 below (entered as a reduction)", "line_type": "input", "sort_order": 7},
            {"line_number": "7", "description": "Net short-term capital gain or (loss). Combine lines 1a through 6 in column (h). Enter here and on Form 1120-S, Schedule K, line 7 or 10", "line_type": "total", "source_rules": ["R002", "R004"], "destination_form": "Schedule K Line 7 → K-1 Box 7", "sort_order": 8},
            # Part II — long-term
            {"line_number": "8a", "description": "Totals for all long-term transactions reported on Form 1099-B or Form 1099-DA for which basis was reported to the IRS and for which you have no adjustments (direct entry — no Form 8949)", "line_type": "input", "sort_order": 10},
            {"line_number": "8b", "description": "Totals for all transactions reported on Form(s) 8949 with Box D or Box J checked", "line_type": "input", "sort_order": 11},
            {"line_number": "9", "description": "Totals for all transactions reported on Form(s) 8949 with Box E or Box K checked", "line_type": "input", "sort_order": 12},
            {"line_number": "10", "description": "Totals for all transactions reported on Form(s) 8949 with Box F or Box L checked", "line_type": "input", "sort_order": 13},
            {"line_number": "11", "description": "Long-term capital gain from installment sales from Form 6252, line 26 or 37", "line_type": "input", "source_facts": ["lt_gain_6252"], "sort_order": 14},
            {"line_number": "12", "description": "Long-term capital gain or (loss) from like-kind exchanges from Form 8824", "line_type": "input", "source_facts": ["lt_gain_8824"], "sort_order": 15},
            {"line_number": "13", "description": "Capital gain distributions", "line_type": "input", "source_facts": ["capital_gain_distributions"], "sort_order": 16},
            {"line_number": "14", "description": "Tax on long-term capital gain included on line 23 below (entered as a reduction)", "line_type": "input", "sort_order": 17},
            {"line_number": "15", "description": "Net long-term capital gain or (loss). Combine lines 8a through 14 in column (h). Enter here and on Form 1120-S, Schedule K, line 8a or 10", "line_type": "total", "source_rules": ["R003", "R004"], "destination_form": "Schedule K Line 8a → K-1 Box 8a", "sort_order": 18},
            # Part III — built-in gains tax
            {"line_number": "16", "description": "Excess of recognized built-in gains over recognized built-in losses (attach computation statement)", "line_type": "input", "sort_order": 20, "notes": "Only if §1374 applies"},
            {"line_number": "17", "description": "Taxable income (attach computation statement)", "line_type": "input", "sort_order": 21},
            {"line_number": "18", "description": "Net recognized built-in gain. Enter the smallest of line 16, line 17, or line 8 of Schedule B", "line_type": "calculated", "source_rules": ["R005"], "source_facts": ["net_recognized_built_in_gain", "net_unrealized_built_in_gain"], "sort_order": 22},
            {"line_number": "19", "description": "Section 1374(b)(2) deduction", "line_type": "input", "sort_order": 23},
            {"line_number": "20", "description": "Subtract line 19 from line 18. If zero or less, enter -0- here and on line 23", "line_type": "calculated", "source_rules": ["R005"], "sort_order": 24},
            {"line_number": "21", "description": "Enter 21% (0.21) of line 20", "line_type": "calculated", "source_rules": ["R005"], "calculation": "line_20 * 0.21", "sort_order": 25},
            {"line_number": "22", "description": "Section 1374(b)(3) business credit and minimum tax credit carryforwards from C corporation years", "line_type": "input", "sort_order": 26},
            {"line_number": "23", "description": "Tax. Subtract line 22 from line 21 (if zero or less, enter -0-). Enter here and on Form 1120-S, page 1, line 23b", "line_type": "total", "source_rules": ["R005"], "destination_form": "Form 1120-S page 1 line 23b", "sort_order": 27},
        ])
        # Stale pre-2025 line rows (1c/7a/7b/7c and re-purposed numbers now
        # re-described above) — delete anything not in the new map so a reseed
        # self-heals the DB (update_or_create alone cannot remove rows).
        _2025_LINES = {"QOF", "1a", "1b", "2", "3", "4", "5", "6", "7",
                       "8a", "8b", "9", "10", "11", "12", "13", "14", "15",
                       "16", "17", "18", "19", "20", "21", "22", "23"}
        stale = FormLine.objects.filter(tax_form=form).exclude(line_number__in=_2025_LINES)
        if stale.exists():
            self.stdout.write(f"  deleting {stale.count()} stale pre-2025 line rows")
            stale.delete()

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
    # Form 5: Form 4562
    # ─────────────────────────────────────────────────────────────────────────

    def _load_form_4562(self, sources):
        # ── 2025-face renumber (2026-07-10, the s44 early-era face audit) ─────
        # Rebuilt VERBATIM vs resources/irs_forms/2025/f4562.pdf (rev "Created
        # 10/9/25", pymupdf dump) + IRS4562.xsd 2025v6.2 LineNumber annotations.
        # The prior block carried a fabricated pre-2025 shape: line 6/7 swapped
        # (face: 6 = the §179 property table, 7 = listed property from line 29),
        # line 8 as a "smaller of" (face: ADD column (c) lines 6 and 7), and the
        # pre-2025 line-19 lettering. THE 2025 FACE CHANGE: new 19h "50-year
        # property" row (50 yrs./MM/S,L), shifting residential rental → 19i and
        # nonresidential real → 19j; Section C (ADS) adds 20e "50-year".
        # Lines 10-13 (§179 carryover chain) are OWNED by
        # load_4562_section179_carryover (Ken-approved 2026-06-22) — the rows
        # here mirror that loader verbatim so reseed order can never regress it.
        # R010-R015 / D010-D014 live in load_remaining_1120s +
        # load_4562_section179_carryover — ids deliberately not reused here.
        form = self._upsert_form(
            "4562",
            "Form 4562 — Depreciation and Amortization",
            ["1120S", "1065", "1120", "1040"],
            notes="§179 election, bonus depreciation, MACRS, amortization. §179 is separately stated for passthrough entities. Line map = the 2025 face (19h 50-year row NEW; residential 19i, nonresidential 19j; ADS adds 20e).",
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
            {"fact_key": "bonus_eligible", "label": "Qualified property under §168(k)(2) (bonus-eligible)", "data_type": "boolean",
             "default_value": "true", "sort_order": 14,
             "notes": "Per-asset. Default true: for 2025 placed-in-service dates, virtually all MACRS "
                      "property with a recovery period of 20 years or less (plus §167(f)(1) software and "
                      "water utility property) is qualified property, including USED property meeting the "
                      "§168(k)(2)(E)(ii) acquisition requirements. Set false only when the property was "
                      "NEVER eligible: a used acquisition failing §168(k)(2)(E)(ii)/§179(d)(2) "
                      "(related-party, carryover basis), property of an electing §163(j)(7) real-property/"
                      "farming business required onto ADS, floor-plan-financing property (§168(k)(9)), or "
                      "listed property ≤50% business use. Drives R007: ELIGIBILITY (not claiming) controls "
                      "the AMT adjustment for post-2015 property (i6251 2025 line 2l), and Rev. Proc. "
                      "2025-16 §2.03(3) keys Table 2 on the same acquisition-requirements test."},
            {"fact_key": "bonus_electout_classes", "label": "§168(k)(7) election out — classes of property", "data_type": "text",
             "sort_order": 15,
             "notes": "RETURN-LEVEL (one election per class per tax year, made by the entity itself — "
                      "i4562 2025 p.7: 'The election must be made separately by each person owning "
                      "qualified property (for example, by the partnership, by the S corporation…)'). "
                      "List of elected-out property classes; tokens = the recovery-period classes the "
                      "engine supports ('3','5','7','10','15','20','25') plus 'software' (§167(f)(1)). "
                      "The election covers ALL qualified property in the class placed in service during "
                      "the year (D008 on conflict). Effects encoded in R009: bonus forced to 0; NO AMT "
                      "adjustment anyway for post-2015 property (i6251 2025 2l); §280F Table 2 for "
                      "under-6000 autos (RP 2025-16 §2.03(2)); GA §168(k) add-back eliminated (no "
                      "federal bonus taken → nothing to add back). Finer class definitions live in "
                      "Reg. §1.168(k)-2(f)(1) — NOT fetched/verified; the recovery-period classes above "
                      "match the i4562 qualified-property list and the firm's asset base."},
            # Part I — listed-property §179 (line 7 ← line 29)
            {"fact_key": "listed_sec179_elected", "label": "Listed property elected §179 cost — from line 29 (Part V column (i))", "data_type": "decimal", "sort_order": 6},
            # Part III — MACRS (method/life/vehicle-class per Ken's dropdown
            # list, delivered 2026-07-10 — the depreciation-methods unit)
            {"fact_key": "recovery_period", "label": "Recovery period (years)", "data_type": "choice",
             "choices": ["3", "5", "7", "10", "15", "20", "25", "27.5", "30", "31.5", "39", "40", "50"], "sort_order": 20,
             "notes": "Preparer dropdown (Ken 2026-07-10): 3/5/7/10/15/20/27.5/31.5 (legacy)/39. "
                      "31.5 = legacy nonresidential real (PIS after 1986, before 5/13/1993 — Pub 946 "
                      "(2025) Table A-7). 30/40 = ADS real property (residential-after-2017 Table A-13 "
                      "/ Table A-13a) — required by the AMT real-property matrix even though not on "
                      "the recommended GDS dropdown. 25 (water utility) and 50 (2025-face 19h/20e) "
                      "stay for face completeness. ADS personal-property lives (Pub 946 Table B) are "
                      "free-entry beyond this list."},
            {"fact_key": "depreciation_method", "label": "Depreciation method", "data_type": "choice",
             "choices": ["200DB", "150DB", "SL", "SL_RES", "SL_NONRES", "ADS_SL", "NONE"], "sort_order": 21,
             "notes": "Ken's dropdown (2026-07-10), display labels: 200DB='MACRS 200% DB' (GDS 3/5/7/10 — "
                      "Tables A-1/A-2..A-5), 150DB='MACRS 150% DB' (required for most 15/20-yr — A-1/"
                      "A-2..A-5; elective for eligible 3/5/7/10-yr — A-14/A-15..A-18), SL='MACRS "
                      "straight line' (GDS SL election, HY/MQ — A-8..A-12), SL_RES='Residential rental "
                      "SL' (27.5 yrs MM — A-6), SL_NONRES='Nonresidential real property SL' (39 yrs MM "
                      "— A-7a; life 31.5 = legacy — A-7), ADS_SL='ADS straight line' (SL over the ADS "
                      "life; real property 30/40 MM — A-13/A-13a; personal property HY/MQ), "
                      "NONE='None' (land / non-depreciable). Ken ruling: passenger auto is NOT a "
                      "method — it is an asset classification (vehicle_classification) layered onto a "
                      "5-year method, because the same automobile can use 200DB, 150DB, GDS SL, or "
                      "ADS SL, and vehicles are separately identified for Part V listed-property "
                      "reporting and §280F limits."},
            {"fact_key": "convention", "label": "Convention", "data_type": "choice",
             "choices": ["HY", "MQ", "MM"], "sort_order": 22},
            {"fact_key": "depreciable_basis", "label": "Depreciable basis (after §179 and bonus)", "data_type": "decimal", "sort_order": 23},
            {"fact_key": "current_year_depreciation", "label": "Current year MACRS depreciation", "data_type": "decimal", "sort_order": 24},
            {"fact_key": "vehicle_classification", "label": "Vehicle classification (listed property)", "data_type": "choice",
             "choices": ["under_6000", "work_truck_6ft", "over_6000"], "sort_order": 25,
             "notes": "Ken's dropdown (2026-07-10): under_6000='Vehicles Under 6000 lbs' (§280F(d)(5) "
                      "passenger automobile — Rev. Proc. 2025-16 annual caps apply, incl. §179), "
                      "work_truck_6ft='Work Truck – 6 Ft bed Specially Equipped' (>6,000 lbs GVWR with "
                      "a §179(b)(5)(B)(ii)(II) cargo area ≥6 ft interior length not readily accessible "
                      "from the passenger compartment — NO §280F caps, NO §179 SUV cap), "
                      "over_6000='Truck or SUV Over 6000 lbs' (no §280F caps; §179 capped at $31,300 "
                      "for 2025 under §179(b)(5)(A) / Rev. Proc. 2024-40 §2.25). Classification does "
                      "NOT change the recovery period (5-year) or method."},
            {"fact_key": "amt_method", "label": "AMT depreciation method (derived)", "data_type": "choice",
             "choices": ["SAME", "150DB"], "sort_order": 26,
             "notes": "Derived by R007 (post-1998 matrix, i6251 line 2l), preparer-overridable: 150DB "
                      "only when regular tax uses 200DB AND the property was NEVER ELIGIBLE for a "
                      "special depreciation allowance (bonus_eligible=false); everything else SAME — "
                      "including bonus claimed, bonus zeroed, and §168(k)(7) elected-out property "
                      "placed in service after 2015 (i6251 2025 2l verbatim; corrected 2026-07-10). "
                      "AMT recovery period and convention always equal regular tax for post-1998 "
                      "property."},
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
             "description": "§179 deduction = lesser of: (a) elected cost, (b) $2,500,000 minus dollar-for-dollar reduction for total placed in service exceeding $4,000,000, (c) taxable income from active business. Face chain: line 4 = max(0, line 2 − line 3); line 5 = max(0, line 1 − line 4); line 9 = min(line 5, line 8). The prior-year-carryover consumption (lines 10/12/13 — face: 12 = add lines 9 and 10, capped at 11; 13 = 9 + 10 − 12) is R014/R015 (load_4562_section179_carryover). GA conforms to the same §179 limit for TY2025 ($2,500,000/$4,000,000) via HB 1199; GA still decouples from §168(k)/(n) bonus.",
             "sort_order": 1, "precedence": 1},
            {"rule_id": "R002", "title": "OBBBA bonus depreciation", "rule_type": "calculation",
             "formula": "bonus_eligible_basis * bonus_percentage",
             "conditions": {"when": "bonus_percentage > 0"},
             "inputs": ["bonus_eligible_basis", "bonus_percentage", "acquisition_date"],
             "outputs": ["bonus_depreciation_amount"],
             "description": "100% for assets acquired AND placed in service after 1/19/2025 (permanent under OBBBA). 40% for assets acquired before 1/20/2025 (binding contract rule). Bonus is on remaining basis after §179.",
             "notes": "NEEDS REVIEW — verify binding contract date rules for 40% rate.",
             "sort_order": 2, "precedence": 5},
            {"rule_id": "R003", "title": "MACRS depreciation calculation (published tables only)", "rule_type": "calculation",
             "formula": "depreciable_basis * pub_946_percentage(recovery_period, method, convention, year)",
             "inputs": ["depreciable_basis", "recovery_period", "depreciation_method", "convention"],
             "outputs": ["current_year_depreciation"],
             "description": "Apply the printed Pub 946 (2025) Appendix A percentage per Chart 1/Chart 2 routing — "
                            "NEVER derived declining-balance arithmetic (2026-07-10: derived MQ tables and a "
                            "wrong 150DB 10-yr SL-switch year were found live; the published columns are the "
                            "law). Routing: 200DB GDS 3/5/7/10 → A-1 (HY) / A-2..A-5 (MQ Q1-Q4); 150DB GDS "
                            "15/20 (required) → A-1 / A-2..A-5; 150DB elective GDS 3/5/7/10 → A-14 (HY) / "
                            "A-15..A-18 (MQ); GDS or ADS SL personal → A-8 (HY) / A-9..A-12 (MQ); residential "
                            "rental 27.5 MM → A-6; nonresidential real 39 MM → A-7a; LEGACY nonresidential "
                            "31.5 MM (PIS after 1986, before 5/13/1993) → A-7; ADS residential-after-2017 30 "
                            "MM → A-13; ADS real 40 MM → A-13a. An unmapped (method, life, convention) "
                            "combination must REFUSE/flag (D007), never silently return 0%. Depreciable basis "
                            "= cost minus §179 minus bonus.",
             "sort_order": 3, "precedence": 10},
            {"rule_id": "R007", "title": "AMT depreciation method (post-1998 matrix, derived + overridable)", "rule_type": "calculation",
             "formula": "amt_method = '150DB' if (depreciation_method == '200DB' and not bonus_eligible) else 'SAME'; amt_life = recovery_period; amt_convention = convention",
             "inputs": ["depreciation_method", "recovery_period", "convention", "bonus_eligible"],
             "outputs": ["amt_method", "amt_current_depreciation"],
             "description": "For property placed in service after 1998 (i6251 line 2l, quoted 2026-07-10): "
                            "property depreciated 200DB for regular tax is refigured for AMT using the 150% "
                            "declining balance method over the SAME recovery period and convention, switching "
                            "to straight line the first year it gives a larger deduction — i.e. the SAME "
                            "published A-14/A-15..A-18 (3/5/7/10-yr) or A-1/A-2..A-5 (15/20-yr) columns. NO "
                            "AMT adjustment (amt = regular) for: residential rental property; nonresidential "
                            "real / other §1250 property depreciated SL; ANY property depreciated 150DB, SL, "
                            "or ADS for regular tax; and qualified property that IS OR WAS ELIGIBLE for a "
                            "special depreciation allowance — WHETHER OR NOT CLAIMED. i6251 (2025) line 2l, "
                            "verbatim: 'If you elected not to have any special depreciation allowance apply, "
                            "the property may be subject to an AMT adjustment for depreciation if it was "
                            "placed in service before 2016. It isn't subject to an AMT adjustment for "
                            "depreciation if it was placed in service after 2015.' i4562 (2025) p.7 Election "
                            "out Note agrees: 'the property placed in service during the tax year will not "
                            "be subject to an AMT adjustment for depreciation.' Statutory mechanism: "
                            "§168(k)(7) switches off only paragraphs (1) and (2)(F) — the property remains "
                            "qualified property, so the §168(k)(2)(G) AMT exemption still applies "
                            "(eligibility controls post-PATH Act, for PIS after 2015). ⚠ CORRECTED "
                            "2026-07-10 (same day as authored): the original R007 arm keyed 150DB on "
                            "'bonus not claimed' (incl. a (k)(7) election-out) — contrary to both 2025 "
                            "instructions. The 150DB recompute bites ONLY for 200DB property NEVER ELIGIBLE "
                            "for any special allowance (bonus_eligible=false: used acquisitions failing "
                            "§168(k)(2)(E)(ii), §168(k)(9) floor-plan/utility exclusions). ≤50%-business "
                            "listed property is forced to ADS SL anyway (never 200DB). Vehicles keep their "
                            "5-year recovery period for AMT — vehicle_classification drives §280F dollar "
                            "caps only, never the AMT life (Ken's matrix, 2026-07-10; the election-out arm "
                            "of that matrix reversed on the verbatim sources — flagged for Ken's "
                            "ratification). Pre-1999 §1250 accelerated property (AMT SL over 40 yrs) is "
                            "OUT OF SCOPE — flag, don't compute. Pre-2016-PIS elected-out property (AMT "
                            "adjustment DOES apply) is also out of scope — flag, don't compute.",
             "sort_order": 7, "precedence": 12},
            {"rule_id": "R009", "title": "§168(k)(7) election out of the special depreciation allowance (per class)", "rule_type": "conditional",
             "formula": "for each class in bonus_electout_classes: bonus_percentage = 0 for ALL qualified property in that class placed in service this year; election statement attaches to the timely filed return; under-6000 autos in an elected-out class use RP 2025-16 Table 2; amt_method stays SAME (post-2015 PIS); GA §168(k) add-back = 0 for the elected-out assets",
             "conditions": {"when": "bonus_electout_classes is non-empty"},
             "inputs": ["bonus_electout_classes", "recovery_period", "bonus_eligible"],
             "outputs": ["bonus_depreciation_amount", "election_statement_required"],
             "description": "i4562 (2025) p.7, verbatim: 'You can elect, for any class of property, to not "
                            "deduct any special depreciation allowance for all such property in such class "
                            "placed in service during the tax year. To make an election, attach a statement "
                            "to your timely filed return (including extensions) indicating the class of "
                            "property for which you are making the election and that, for such class, you "
                            "are not to claim any special depreciation allowance. The election must be made "
                            "separately by each person owning qualified property (for example, by the "
                            "partnership, by the S corporation…).' Late cure: amended return within 6 "
                            "months of the unextended due date, marked 'Filed pursuant to section "
                            "301.9100-2'. Once made, irrevocable without IRS consent. FOUR ENGINE EFFECTS: "
                            "(1) bonus_depreciation_amount = 0 for every qualified asset in the class — the "
                            "election covers ALL such property (D008 errors a conflicting per-asset bonus); "
                            "(2) NO AMT adjustment anyway — see R007 (i4562 p.7 Note + i6251 2l, post-2015 "
                            "PIS); (3) under-6000 passenger autos flip to RP 2025-16 Table 2 ($12,200 year "
                            "1) per §2.03(2) — §168(k)(7) also switches off §168(k)(2)(F); (4) the GA "
                            "§168(k) add-back disappears for those assets because no federal bonus is "
                            "taken (GA-600S Schedule 1 adds back only bonus actually deducted federally) — "
                            "this is the firm's primary reason for electing out. WHY THE ELECTION MATTERS "
                            "vs just zeroing bonus: §168(k)(1) applies automatically to qualified property "
                            "('shall include an allowance'); without the election, depreciation 'allowed or "
                            "allowable' (§1016(a)(2)) still reduces basis — D009 warns. TRANSITIONAL "
                            "ALTERNATIVE (documented, NOT implemented): for the first tax year ending after "
                            "1/19/2025 only, a 40% allowance (60% LPP/aircraft) may be elected instead of "
                            "100% — i4562 (2025) p.6 verbatim in sources; i4562 states NO statement "
                            "mechanics for it (unlike (k)(5)/(k)(7)) — spec-silent, REVIEW_QUEUE for Ken; "
                            "do not improvise a statement.",
             "sort_order": 9, "precedence": 4},
            {"rule_id": "R008", "title": "§280F / §179(b)(5) vehicle dollar caps by classification", "rule_type": "calculation",
             "formula": "under_6000: annual_cap = rp_2025_16_table(year_in_service, bonus_claimed) * business_pct; over_6000: sec_179 <= 31300; work_truck_6ft: no caps",
             "inputs": ["vehicle_classification", "bonus_depreciation_amount", "section_179_elected_cost"],
             "outputs": ["capped_depreciation"],
             "description": "under_6000 ('Vehicles Under 6000 lbs' — §280F(d)(5) passenger automobile, "
                            "including trucks and vans per Rev. Proc. 2025-16 §1): total year deduction "
                            "(§179 + bonus + MACRS) capped at Table 1 ($20,200/$19,600/$11,800/$7,060) when "
                            "the §168(k) allowance applies, Table 2 ($12,200 first year) when it does not "
                            "(≤50% business use, §168(k)(7) election-out, or non-qualifying acquisition — "
                            "RP 2025-16 §2.03). Caps prorate by business-use percentage. over_6000 ('Truck "
                            "or SUV Over 6000 lbs'): NO §280F caps; §179 limited to $31,300 (2025, "
                            "§179(b)(5)(A) / Rev. Proc. 2024-40 §2.25) for SUVs ≤14,000 lbs GVWR. "
                            "work_truck_6ft ('Work Truck – 6 Ft bed Specially Equipped'): >6,000 lbs with a "
                            "≥6-ft interior-length cargo area not readily accessible from the passenger "
                            "compartment — §179(b)(5)(B)(ii)(II) exception: NO SUV cap and NO §280F caps. "
                            "Classification never changes method/life; it is orthogonal to the method "
                            "dropdown (Ken ruling 2026-07-10).",
             "sort_order": 8, "precedence": 13},
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
             "description": "MACRS + bonus depreciation (excluding §179) flows to Page 1 Line 14 (1120-S). Unlike §179, regular depreciation and bonus are NOT separately stated. Face line 22 (2025, verbatim): 'Total. Add amounts from line 12, lines 14 through 17, lines 19 and 20 in column (g), and line 21. Enter here and on the appropriate lines of your return. Partnerships and S corporations—see instructions' — for 1120-S/1065 the line-12 §179 component rides Schedule K, never page 1.",
             "sort_order": 5, "precedence": 15},
            {"rule_id": "R006", "title": "§197 amortization", "rule_type": "calculation",
             "formula": "amortizable_amount / 180 * months_in_service_this_year",
             "inputs": ["amortizable_amount", "amortization_period_months", "amortization_start_date"],
             "outputs": ["current_year_amortization"],
             "description": "§197 intangibles amortized over 180 months (15 years) straight-line. Includes goodwill, going concern value, covenants not to compete, franchises, trademarks. Amortization is Part VI on the face (lines 42-44); Part V is Listed Property.",
             "sort_order": 6, "precedence": 10},
        ])

        self._upsert_links(rules, sources, [
            ("R001", "IRC_179", "primary", "§179(b) — limitation and phaseout computation"),
            ("R001", "IRS_2025_4562_INSTR", "secondary", "Part I instructions — §179 election and limits"),
            ("R002", "IRC_168", "primary", "§168(k) — bonus depreciation as amended by OBBBA"),
            ("R002", "IRS_2025_4562_INSTR", "secondary", "Part II instructions — special depreciation allowance"),
            ("R003", "IRC_168", "primary", "§168(a)-(b) — MACRS general rules"),
            ("R003", "IRS_PUB_946", "primary", "Pub 946 (2025) Appendix A — Chart 1 routing + printed percentage tables (verbatim excerpts)"),
            ("R003", "IRS_2025_4562_INSTR", "secondary", "Part III instructions — MACRS depreciation"),
            ("R007", "IRS_2025_6251_INSTR", "primary", "i6251 line 2l — post-1998 AMT depreciation matrix; verbatim: elected-out property PIS after 2015 'isn't subject to an AMT adjustment' (eligibility controls, not claiming)"),
            ("R007", "IRC_168", "secondary", "§168(k)(2)(G) — no AMT adjustment for qualified property; (k)(7) switches off only paras (1)/(2)(F), so (2)(G) survives an election-out"),
            ("R007", "IRS_PUB_946", "secondary", "Tables A-14/A-15..A-18 — the AMT 150DB columns"),
            ("R007", "IRS_2025_4562_INSTR", "secondary", "p.7 Election out Note — elected-out property 'will not be subject to an AMT adjustment for depreciation' (verbatim excerpt)"),
            ("R009", "IRS_2025_4562_INSTR", "primary", "p.7 Election out — per-class §168(k)(7) mechanics, statement requirements, 301.9100-2 cure, irrevocability (verbatim excerpt)"),
            ("R009", "IRC_168", "primary", "§168(k)(7) — election out by class; switches off §168(k)(1) and (2)(F) only"),
            ("R009", "IRS_RP_2025_16", "secondary", "§2.03(2) — a (k)(7) election-out moves under-6000 autos to Table 2 (verbatim excerpt)"),
            ("R009", "IRS_2025_6251_INSTR", "secondary", "line 2l — no AMT adjustment for elected-out property placed in service after 2015 (verbatim)"),
            ("R008", "IRC_280F", "primary", "§280F(a)/(d)(5) — passenger-automobile caps and the 6,000-lb line"),
            ("R008", "IRS_RP_2025_16", "primary", "2025 passenger-auto caps — Tables 1/2 verbatim"),
            ("R008", "IRC_179", "primary", "§179(b)(5) — SUV limitation and the ≥6-ft-bed exception"),
            ("R008", "IRS_RP_2024_40", "primary", "2025 SUV cap $31,300 — §2.25 verbatim"),
            ("R004", "IRC_179", "primary", "§179(d)(4) — separately stated for passthrough entities"),
            ("R004", "IRS_2025_1120S_INSTR", "secondary", "Schedule K Line 11 — §179 deduction"),
            ("R005", "IRS_2025_1120S_INSTR", "primary", "Page 1 Line 14 — depreciation (non-§179)"),
            ("R005", "IRS_2025_4562_INSTR", "secondary", "Line 22 total → entity return"),
            ("R006", "IRC_197", "primary", "§197 — 180-month amortization of intangibles"),
            ("R006", "IRS_2025_4562_INSTR", "secondary", "Part VI instructions — amortization"),
        ])

        self._upsert_lines(form, [
            # ── Part I — Election To Expense Certain Property Under Section 179
            # (face note: "If you have any listed property, complete Part V
            # before you complete Part I.")
            {"line_number": "1", "description": "Maximum amount (see instructions) — $2,500,000 for 2025 (OBBBA)", "line_type": "input", "source_facts": ["section_179_limitation"], "sort_order": 1},
            {"line_number": "2", "description": "Total cost of section 179 property placed in service (see instructions)", "line_type": "input", "source_facts": ["total_section_179_placed_in_service"], "sort_order": 2},
            {"line_number": "3", "description": "Threshold cost of section 179 property before reduction in limitation (see instructions) — $4,000,000 for 2025", "line_type": "input", "source_facts": ["section_179_phaseout_threshold"], "sort_order": 3},
            {"line_number": "4", "description": "Reduction in limitation. Subtract line 3 from line 2. If zero or less, enter -0-", "line_type": "calculated", "calculation": "max(0, line_2 - line_3)", "sort_order": 4},
            {"line_number": "5", "description": "Dollar limitation for tax year. Subtract line 4 from line 1. If zero or less, enter -0-. If married filing separately, see instructions", "line_type": "calculated", "calculation": "max(0, line_1 - line_4)", "source_rules": ["R001"], "sort_order": 5},
            {"line_number": "6", "description": "Section 179 property rows — (a) Description of property / (b) Cost (business use only) / (c) Elected cost", "line_type": "input", "source_facts": ["section_179_elected_cost"], "sort_order": 6},
            {"line_number": "7", "description": "Listed property. Enter the amount from line 29", "line_type": "calculated", "calculation": "line_29", "source_facts": ["listed_sec179_elected"], "sort_order": 7},
            {"line_number": "8", "description": "Total elected cost of section 179 property. Add amounts in column (c), lines 6 and 7", "line_type": "calculated", "calculation": "sum(line_6_col_c) + line_7", "sort_order": 8},
            {"line_number": "9", "description": "Tentative deduction. Enter the smaller of line 5 or line 8", "line_type": "calculated", "calculation": "min(line_5, line_8)", "sort_order": 9},
            # Lines 10-13 — the §179 carryover chain. OWNED by
            # load_4562_section179_carryover (Ken-approved 2026-06-22);
            # mirrored VERBATIM here so reseed order can never regress them.
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
            # ── Part II — Special Depreciation Allowance and Other Depreciation
            # (face note: "Don't use Part II or Part III below for listed
            # property. Instead, use Part V.")
            {"line_number": "14", "description": "Special depreciation allowance for qualified property (other than listed property) placed in service during the tax year. See instructions", "line_type": "calculated", "source_rules": ["R002"], "source_facts": ["bonus_depreciation_amount"], "sort_order": 14},
            {"line_number": "15", "description": "Property subject to section 168(f)(1) election", "line_type": "input", "sort_order": 15},
            {"line_number": "16", "description": "Other depreciation (including ACRS)", "line_type": "input", "sort_order": 16},
            # ── Part III — MACRS Depreciation · Section A
            {"line_number": "17", "description": "MACRS deductions for assets placed in service in tax years beginning before 2025", "line_type": "input", "sort_order": 17},
            {"line_number": "18", "description": "If you are electing to group any assets placed in service during the tax year into one or more general asset accounts, check here", "line_type": "input", "sort_order": 18},
            # Section B — Assets Placed in Service During 2025 Tax Year Using
            # the General Depreciation System. Columns: (a) classification /
            # (b) month-year placed in service / (c) basis for depreciation /
            # (d) recovery period / (e) convention / (f) method / (g) deduction.
            # ⚠ 2025 FACE CHANGE: 19h "50-year property" is NEW — residential
            # rental moved h→i and nonresidential real i→j (XSD 2025v6.2:
            # GDS50YearPropertyGrp=19h, GDSResidentialRentalProperty=19i,
            # GDSNonRsdntlRealProp=19j).
            {"line_number": "19a", "description": "3-year property", "line_type": "input", "sort_order": 19},
            {"line_number": "19b", "description": "5-year property", "line_type": "input", "sort_order": 20},
            {"line_number": "19c", "description": "7-year property", "line_type": "input", "sort_order": 21},
            {"line_number": "19d", "description": "10-year property", "line_type": "input", "sort_order": 22},
            {"line_number": "19e", "description": "15-year property", "line_type": "input", "sort_order": 23},
            {"line_number": "19f", "description": "20-year property", "line_type": "input", "sort_order": 24},
            {"line_number": "19g", "description": "25-year property — 25 yrs., S/L", "line_type": "input", "sort_order": 25},
            {"line_number": "19h", "description": "50-year property — 50 yrs., MM, S/L (NEW row on the 2025 face)", "line_type": "input", "sort_order": 26},
            {"line_number": "19i", "description": "Residential rental property — 27.5 yrs., MM, S/L", "line_type": "input", "sort_order": 27},
            {"line_number": "19j", "description": "Nonresidential real property — 39 yrs., MM, S/L", "line_type": "input", "sort_order": 28},
            # Section C — Assets Placed in Service During 2025 Tax Year Using
            # the Alternative Depreciation System (20e is NEW on the 2025 face).
            {"line_number": "20a", "description": "Class life — S/L", "line_type": "input", "sort_order": 29},
            {"line_number": "20b", "description": "12-year — 12 yrs., S/L", "line_type": "input", "sort_order": 30},
            {"line_number": "20c", "description": "30-year — 30 yrs., MM, S/L", "line_type": "input", "sort_order": 31},
            {"line_number": "20d", "description": "40-year — 40 yrs., MM, S/L", "line_type": "input", "sort_order": 32},
            {"line_number": "20e", "description": "50-year — 50 yrs., MM, S/L (NEW row on the 2025 face)", "line_type": "input", "sort_order": 33},
            # ── Part IV — Summary
            {"line_number": "21", "description": "Listed property. Enter amount from line 28", "line_type": "calculated", "calculation": "line_28", "sort_order": 34},
            {"line_number": "22", "description": "Total. Add amounts from line 12, lines 14 through 17, lines 19 and 20 in column (g), and line 21. Enter here and on the appropriate lines of your return. Partnerships and S corporations—see instructions", "line_type": "total", "source_rules": ["R003", "R005"], "destination_form": "Page 1 Line 14 (1120-S) or appropriate deduction line — §179 (line 12) rides Schedule K for passthroughs", "sort_order": 35},
            {"line_number": "23a", "description": "For assets shown in Part III placed in service during the current tax year with costs capitalized under section 263A: basis attributable to interest costs capitalized under section 263A(f)", "line_type": "input", "sort_order": 36},
            {"line_number": "23b", "description": "For assets shown in Part III placed in service during the current tax year with costs capitalized under section 263A: basis attributable to section 263A costs other than 263A(f) interest", "line_type": "input", "sort_order": 37},
            # ── Part V — Listed Property · Section A
            {"line_number": "24a", "description": "Do you have evidence to support the business/investment use claimed? (Yes/No)", "line_type": "input", "sort_order": 38},
            {"line_number": "24b", "description": "If 'Yes,' is the evidence written? (Yes/No)", "line_type": "input", "sort_order": 39},
            {"line_number": "24c", "description": "Do you own, lease, or charter an aircraft? Check all that apply (Own/Lease/Charter) — NEW on the 2025 face", "line_type": "input", "sort_order": 40},
            {"line_number": "25", "description": "Special depreciation allowance for qualified listed property placed in service during the tax year and used more than 50% in a qualified business use", "line_type": "input", "sort_order": 41},
            {"line_number": "26", "description": "Property used more than 50% in a qualified business use — columns (a)-(i) incl. (h) depreciation deduction and (i) elected section 179 cost", "line_type": "input", "sort_order": 42},
            {"line_number": "27", "description": "Property used 50% or less in a qualified business use (S/L only)", "line_type": "input", "sort_order": 43},
            {"line_number": "28", "description": "Add amounts in column (h), lines 25 through 27. Enter here and on line 21", "line_type": "total", "calculation": "line_25 + sum(line_26_col_h) + sum(line_27_col_h)", "destination_form": "Line 21", "sort_order": 44},
            {"line_number": "29", "description": "Add amounts in column (i), line 26. Enter here and on line 7", "line_type": "total", "calculation": "sum(line_26_col_i)", "destination_form": "Line 7", "sort_order": 45},
            # Section B — Information on Use of Vehicles (per-vehicle columns (a)-(f))
            {"line_number": "30", "description": "Total business/investment miles driven during the year (don't include commuting miles)", "line_type": "input", "sort_order": 46},
            {"line_number": "31", "description": "Total commuting miles driven during the year", "line_type": "input", "sort_order": 47},
            {"line_number": "32", "description": "Total other personal (noncommuting) miles driven", "line_type": "input", "sort_order": 48},
            {"line_number": "33", "description": "Total miles driven during the year. Add lines 30 through 32", "line_type": "calculated", "calculation": "line_30 + line_31 + line_32", "sort_order": 49},
            {"line_number": "34", "description": "Was the vehicle available for personal use during off-duty hours? (Yes/No per vehicle)", "line_type": "input", "sort_order": 50},
            {"line_number": "35", "description": "Was the vehicle used primarily by a more than 5% owner or related person? (Yes/No per vehicle)", "line_type": "input", "sort_order": 51},
            {"line_number": "36", "description": "Is another vehicle available for personal use? (Yes/No per vehicle)", "line_type": "input", "sort_order": 52},
            # Section C — Questions for Employers Who Provide Vehicles
            {"line_number": "37", "description": "Do you maintain a written policy statement that prohibits all personal use of vehicles, including commuting, by your employees?", "line_type": "input", "sort_order": 53},
            {"line_number": "38", "description": "Do you maintain a written policy statement that prohibits personal use of vehicles, except commuting, by your employees?", "line_type": "input", "sort_order": 54},
            {"line_number": "39", "description": "Do you treat all use of vehicles by employees as personal use?", "line_type": "input", "sort_order": 55},
            {"line_number": "40", "description": "Do you provide more than five vehicles to your employees, obtain information from your employees about the use of the vehicles, and retain the information received?", "line_type": "input", "sort_order": 56},
            {"line_number": "41", "description": "Do you meet the requirements concerning qualified automobile demonstration use?", "line_type": "input", "sort_order": 57},
            # ── Part VI — Amortization (columns (a)-(f))
            {"line_number": "42", "description": "Amortization of costs that begins during your 2025 tax year", "line_type": "input", "source_facts": ["amortizable_amount", "amortization_period_months", "amortization_start_date"], "sort_order": 58},
            {"line_number": "43", "description": "Amortization of costs that began before your 2025 tax year", "line_type": "input", "sort_order": 59},
            {"line_number": "44", "description": "Total. Add amounts in column (f). See the instructions for where to report", "line_type": "total", "source_rules": ["R006"], "destination_form": "Other deductions or Page 1 deduction line", "sort_order": 60},
        ])

        # In-loader stale-row DELETE (the SCHD/SCHB recipe): update_or_create
        # alone cannot remove rows, so any line row NOT on the 2025 face is
        # removed here — self-heals both DBs on reseed. The keep-set includes
        # lines 10-13 owned by load_4562_section179_carryover.
        _2025_LINES = (
            {str(n) for n in range(1, 19)}
            | {f"19{c}" for c in "abcdefghij"}
            | {f"20{c}" for c in "abcde"}
            | {"21", "22", "23a", "23b", "24a", "24b", "24c"}
            | {str(n) for n in range(25, 45)}
        )
        stale = FormLine.objects.filter(tax_form=form).exclude(line_number__in=_2025_LINES)
        if stale.exists():
            self.stdout.write(f"  deleting {stale.count()} stale pre-2025 4562 line rows: "
                              + ", ".join(sorted(stale.values_list("line_number", flat=True))))
            stale.delete()

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
            {"diagnostic_id": "D005", "title": "Vehicle asset without a vehicle classification", "severity": "warning",
             "condition": "asset group is Vehicles AND vehicle_classification is blank",
             "message": "This vehicle has no classification (Under 6000 lbs / Work Truck 6-ft bed / Over 6000 lbs). The §280F luxury-auto caps and the §179 SUV limit cannot be applied correctly until one is chosen."},
            {"diagnostic_id": "D006", "title": "§179 on an over-6,000-lb SUV exceeds the $31,300 cap", "severity": "error",
             "condition": "vehicle_classification == 'over_6000' AND section_179_elected_cost > 31300",
             "message": "§179 for a sport utility vehicle over 6,000 lbs GVWR cannot exceed $31,300 for 2025 (§179(b)(5)(A); Rev. Proc. 2024-40 §2.25). Reduce the elected §179 — the excess basis depreciates under MACRS (bonus is not capped for >6,000-lb vehicles). A pickup with a ≥6-ft bed qualifies for the §179(b)(5)(B) exception — reclassify as Work Truck if applicable."},
            {"diagnostic_id": "D007", "title": "Method/life/convention combination has no published table", "severity": "error",
             "condition": "pub_946_percentage(recovery_period, method, convention) has no table entry",
             "message": "This method/recovery-period/convention combination has no Pub 946 published-table support in the engine (e.g., 50-year SL/MM, ADS personal-property lives beyond the printed columns). The computed depreciation would be $0 — enter the correct combination or flag for a verified-source unit. Never trust a silent zero."},
            {"diagnostic_id": "D008", "title": "Bonus claimed on an asset in a §168(k)(7) elected-out class", "severity": "error",
             "condition": "asset recovery class in bonus_electout_classes AND asset bonus_pct > 0",
             "message": "This return elects out of the special depreciation allowance for this asset's property class under §168(k)(7), but the asset claims bonus depreciation. The election covers ALL qualified property in the class placed in service during the year (i4562 2025 p.7: 'all such property in such class') — remove the asset's bonus or remove the class from the election."},
            {"diagnostic_id": "D009", "title": "Bonus zeroed without a §168(k)(7) election for the class", "severity": "warning",
             "condition": "asset is bonus_eligible AND bonus_pct == 0 AND asset recovery class NOT in bonus_electout_classes",
             "message": "This qualified asset claims no special depreciation allowance, but its property class is not elected out under §168(k)(7). §168(k)(1) applies automatically to qualified property ('shall include an allowance'), and depreciation allowed OR ALLOWABLE reduces basis (§1016(a)(2)) — skipping bonus without the election risks losing the deduction while still reducing basis. Either claim the allowance or add the class to the §168(k)(7) election (which also produces the required statement)."},
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
             "notes": "Federal §179 = $2.5M. Georgia conforms to the same §179 limit for TY2025 ($2.5M/$4M) via HB 1199; the state difference is §168(k)/(n) bonus only. This spec covers federal only.", "sort_order": 4},
            {"scenario_name": "2025 face re-letter — line 19 classification (h=50-yr, i=residential, j=nonresidential)",
             "scenario_type": "edge",
             "inputs": {"asset_lives": ["27.5", "39", "50"]},
             "expected_outputs": {"line_19_rows": ["19i", "19j", "19h"]},
             "notes": "Structural pin for the 2025 face change: 19h '50-year property' is NEW (50 yrs./MM/S,L), shifting residential rental 27.5-yr → 19i and nonresidential real 39-yr → 19j (pre-2025: h=residential, i=nonresidential). Verified vs f4562.pdf 2025 (rev 10/9/25) + IRS4562.xsd 2025v6.2 LineNumber annotations. Any consumer keying line-19 letters by the pre-2025 layout prints residential amounts in the 50-year row.", "sort_order": 5},
            # ── Depreciation-methods unit scenarios (2026-07-10) — every
            # expected percentage is a PUBLISHED-TABLE value (Pub 946 (2025)
            # Appendix A / Rev. Proc. 2025-16 / Rev. Proc. 2024-40), never
            # derived arithmetic.
            {"scenario_name": "AMT matrix — 200DB 5-yr HY, property NEVER bonus-eligible: AMT refigures at 150DB, same life/convention",
             "scenario_type": "normal",
             "inputs": {"depreciable_basis": 10000, "recovery_period": "5", "depreciation_method": "200DB",
                         "convention": "HY", "bonus_percentage": "0", "bonus_eligible": False, "year_in_service": 1},
             "expected_outputs": {"current_year_depreciation": 2000, "amt_method": "150DB", "amt_current_depreciation": 1500},
             "notes": "The property was NEVER qualified property (e.g., a used acquisition failing §168(k)(2)(E)(ii) — related-party/carryover basis). Regular = Table A-1 5-yr year 1 (20.00%) = 2,000. AMT = Table A-14 5-yr year 1 (15.00%) = 1,500 — same recovery period and convention (i6251 line 2l). Adjustment = 500. CORRECTED 2026-07-10: the original scenario keyed 150DB on bonus_percentage=0 alone — but a bonus-ELIGIBLE asset with bonus zeroed (or elected out) has NO adjustment for post-2015 PIS (i6251 2l verbatim).", "sort_order": 6},
            {"scenario_name": "AMT matrix — 150DB / SL / ADS / residential / nonresidential: SAME as tax (no adjustment)",
             "scenario_type": "normal",
             "inputs": {"methods": ["150DB", "SL", "ADS_SL", "SL_RES", "SL_NONRES"]},
             "expected_outputs": {"amt_method": "SAME", "amt_adjustment": 0},
             "notes": "i6251 line 2l exemption list (post-1998 property): residential rental; nonresidential/other §1250 depreciated SL; any property depreciated 150DB or SL; ADS-elected property. Ken's combo table 2026-07-10 rows 5-14.", "sort_order": 7},
            {"scenario_name": "AMT matrix — 200DB WITH §168(k) bonus claimed: NO AMT adjustment at all",
             "scenario_type": "edge",
             "inputs": {"depreciable_basis": 10000, "recovery_period": "5", "depreciation_method": "200DB",
                         "convention": "HY", "bonus_percentage": "100", "year_in_service": 1},
             "expected_outputs": {"amt_method": "SAME", "amt_adjustment": 0},
             "notes": "Qualified property on which the special depreciation allowance was claimed has identical AMT/regular basis — the allowance is deductible for AMT and the remaining basis needs no adjustment (i6251 2l; §168(k)(2)(G)). The 150DB recompute bites ONLY for 200DB property never eligible for a special allowance (corrected 2026-07-10 — a §168(k)(7) election-out does NOT re-engage it for post-2015 PIS; i6251 2l + i4562 p.7 Note verbatim).", "sort_order": 8},
            {"scenario_name": "Legacy nonresidential 31.5-yr SL/MM — month 6, year 1 = 1.720%",
             "scenario_type": "normal",
             "inputs": {"depreciable_basis": 100000, "recovery_period": "31.5", "depreciation_method": "SL_NONRES",
                         "convention": "MM", "month_placed_in_service": 6, "year_in_service": 1},
             "expected_outputs": {"current_year_depreciation": 1720},
             "notes": "Table A-7 (Pub 946 (2025) p.74) month-6 first-year = 1.720%; full years 3.175%. Applies to nonresidential real PIS after 1986 and before 5/13/1993.", "sort_order": 9},
            {"scenario_name": "ADS real property SL/MM — 40-yr month 1 = 2.396%; 30-yr residential month 7 = 1.528%",
             "scenario_type": "normal",
             "inputs": {"assets": [{"recovery_period": "40", "method": "ADS_SL", "month": 1},
                                    {"recovery_period": "30", "method": "ADS_SL", "month": 7}],
                         "depreciable_basis": 100000},
             "expected_outputs": {"year1_40yr": 2396, "year1_30yr": 1528},
             "notes": "Table A-13a (40-yr) month-1 = 2.396%, full 2.500%. Table A-13 (residential after 2017, 30-yr) month-7 = 1.528%, full 3.333%. AMT = SAME (ADS).", "sort_order": 10},
            {"scenario_name": "Published MQ pin — 200DB 5-yr Q4: year 1 = 5.00%, year 2 = 38.00%, year 6 = 9.58%",
             "scenario_type": "edge",
             "inputs": {"depreciable_basis": 10000, "recovery_period": "5", "depreciation_method": "200DB",
                         "convention": "MQ", "quarter_placed_in_service": 4},
             "expected_outputs": {"year_1": 500, "year_2": 3800, "year_6": 958},
             "notes": "Table A-5 verbatim (5.00/38.00/22.80/13.68/10.94/9.58). Pins the 2026-07-10 finding: the prior engine MQ tables were DERIVED and wrong (its Q4 column summed to 99.00%). All four quarters × 3/5/7/10/15/20-yr columns now come from A-2..A-5.", "sort_order": 11},
            {"scenario_name": "Published 150DB pins — HY 10-yr year 5 = 8.74% (SL switch at yr 5); MQ Q1 5-yr year 1 = 26.25%",
             "scenario_type": "edge",
             "inputs": {"assets": [{"recovery_period": "10", "method": "150DB", "convention": "HY", "year": 5},
                                    {"recovery_period": "5", "method": "150DB", "convention": "MQ", "quarter": 1, "year": 1}],
                         "depreciable_basis": 10000},
             "expected_outputs": {"hy_10yr_year5": 874, "mq_q1_5yr_year1": 2625},
             "notes": "Table A-14 10-yr column switches to SL in YEAR 5 (8.74×6 then 4.37) — the prior engine table kept DB through year 5 (8.52→ wrong 8.53/8.72/4.66 tail). Table A-15 Q1 5-yr year 1 = 26.25%. Elective 150DB now has full MQ support (A-15..A-18).", "sort_order": 12},
            {"scenario_name": "Vehicle caps — under-6000 auto, $80K, bonus claimed: year 1 capped at $20,200",
             "scenario_type": "normal",
             "inputs": {"vehicle_classification": "under_6000", "cost_basis": 80000, "business_pct": 100,
                         "bonus_percentage": "100", "year_in_service": 1},
             "expected_outputs": {"year_1_total_depreciation": 20200},
             "notes": "Rev. Proc. 2025-16 Table 1: 20,200/19,600/11,800/7,060. Without bonus (incl. a §168(k)(7) election-out — RP 2025-16 §2.03) Table 2 first year = 12,200. Prior engine constants (19,500 yr-2 / 12,400 no-bonus yr-1) were WRONG and miscited Rev. Proc. 2025-13.", "sort_order": 13},
            {"scenario_name": "Vehicle caps — over-6000 SUV §179 capped at $31,300; work truck 6-ft bed exempt",
             "scenario_type": "edge",
             "inputs": {"assets": [{"vehicle_classification": "over_6000", "sec_179_elected": 60000},
                                    {"vehicle_classification": "work_truck_6ft", "sec_179_elected": 60000}]},
             "expected_outputs": {"suv_allowed_179": 31300, "suv_diagnostic": "D006", "work_truck_allowed_179": 60000},
             "notes": "§179(b)(5)(A) / Rev. Proc. 2024-40 §2.25: SUV cap $31,300 (2025). The ≥6-ft-interior-length open cargo bed not readily accessible from the passenger compartment is the §179(b)(5)(B)(ii)(II) exception — no SUV cap, and >6,000 lbs GVWR means no §280F caps either. Excess SUV basis still depreciates under MACRS/bonus.", "sort_order": 14},
            # ── §168(k)(7) election-out unit scenarios (2026-07-10) ──────────
            {"scenario_name": "§168(k)(7) election out — 5-yr class: bonus 0, full-basis MACRS, NO AMT adjustment, GA add-back 0, statement attaches",
             "scenario_type": "normal",
             "inputs": {"bonus_electout_classes": ["5"], "depreciable_basis": 10000, "recovery_period": "5",
                         "depreciation_method": "200DB", "convention": "HY", "bonus_eligible": True,
                         "year_in_service": 1, "entity_type": "1120S"},
             "expected_outputs": {"bonus_depreciation_amount": 0, "current_year_depreciation": 2000,
                                   "amt_method": "SAME", "amt_adjustment": 0, "ga_bonus_addback": 0,
                                   "election_statement_required": True},
             "notes": "The firm's standard move (kills the GA §168(k) add-back). Bonus forced to 0 for the whole class; MACRS on full basis = A-1 5-yr 20.00% = 2,000. NO AMT adjustment: i4562 2025 p.7 Note ('will not be subject to an AMT adjustment') + i6251 2025 2l ('isn't subject… if placed in service after 2015'). GA-600S Schedule 1 addition = 0 (no federal bonus taken). The election statement (class + declaration) attaches to the timely filed return.", "sort_order": 15},
            {"scenario_name": "§168(k)(7) conflict — asset claims bonus inside an elected-out class → D008",
             "scenario_type": "error",
             "inputs": {"bonus_electout_classes": ["5"], "recovery_period": "5", "bonus_percentage": "100",
                         "depreciable_basis": 10000},
             "expected_outputs": {"diagnostic": "D008"},
             "notes": "The election covers ALL qualified property in the class placed in service during the year (i4562 p.7 'all such property in such class') — a per-asset bonus inside the class is an error, never a silent zero-out.", "sort_order": 16},
            {"scenario_name": "§168(k)(7) elected-out under-6000 auto — RP 2025-16 Table 2: year 1 capped at $12,200",
             "scenario_type": "edge",
             "inputs": {"bonus_electout_classes": ["5"], "vehicle_classification": "under_6000",
                         "cost_basis": 80000, "business_pct": 100, "year_in_service": 1},
             "expected_outputs": {"year_1_total_depreciation": 12200, "amt_adjustment": 0},
             "notes": "RP 2025-16 §2.03(2): the §168(k) allowance 'does not apply' when the taxpayer 'elected out… pursuant to § 168(k)(7) for the class of property that includes passenger automobiles' → Table 2 first year $12,200 (later years identical to Table 1: 19,600/11,800/7,060). Still no AMT adjustment (post-2015 PIS).", "sort_order": 17},
        ])

        self._upsert_form_links("4562", sources, [
            ("IRS_2025_4562_INSTR", "governs"),
            ("IRC_179", "governs"),
            ("IRC_168", "governs"),
            ("IRC_197", "governs"),
            ("IRC_280F", "governs"),
            ("IRS_PUB_946", "informs"),
            ("IRS_RP_2025_16", "informs"),
            ("IRS_RP_2024_40", "informs"),
            ("IRS_2025_6251_INSTR", "informs"),
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
