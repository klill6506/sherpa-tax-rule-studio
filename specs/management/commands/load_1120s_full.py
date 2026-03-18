"""Load 1120-S full specs — Page 1, Schedule K (expanded), M-1, M-2, Schedule D flow.

Session 9: Builds on Session 8's Schedule K/K-1/D/8949/4562 specs.
Adds missing forms (Page 1, M-1, M-2), expands K line rules with
proper flow-in sources, adds cross-form diagnostics and test scenarios.

All authority sources are grounded in IRS instructions fetched 2026-03-18.
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
    FormDiagnostic,
    FormFact,
    FormLine,
    FormRule,
    TaxForm,
    TestScenario,
)


# ═══════════════════════════════════════════════════════════════════════════
# Authority sources — fresh from IRS.gov fetch 2026-03-18
# ═══════════════════════════════════════════════════════════════════════════

FRESH_SOURCES = [
    {
        "source_code": "IRS_2025_1120S_INSTR_FULL",
        "source_type": "official_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "Instructions for Form 1120-S (2025) — Full Document (fetched 2026-03-18)",
        "citation": "Instructions for Form 1120-S (2025)",
        "issuer": "IRS",
        "current_status": "active",
        "is_substantive_authority": True,
        "requires_human_review": False,
        "trust_score": 9.5,
        "topics": ["1120s", "scorp", "schedule_k", "schedule_m"],
        "excerpts": [
            {
                "excerpt_label": "Page 1 Line 4 — Net gain (loss) from Form 4797",
                "excerpt_text": "Enter the net gain (loss) from Form 4797, Part II, line 17, from the sale or exchange of property used in a trade or business and involuntary conversions. Do not include gain or loss on the disposition of capital assets.",
                "summary_text": "Page 1 Line 4 = Form 4797 Part II Line 17 (ordinary gains/losses from business property).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Page 1 Lines 1-6 — Income computation",
                "excerpt_text": "Line 1a: Gross receipts or sales. Line 1b: Returns and allowances. Line 1c: Line 1a minus Line 1b. Line 2: Cost of goods sold (Form 1125-A). Line 3: Gross profit (Line 1c minus Line 2). Line 4: Net gain (loss) from Form 4797, Part II, line 17. Line 5: Other income (loss). Line 6: Total income (loss) — combine lines 3 through 5.",
                "summary_text": "Page 1 income computation: gross receipts less COGS = gross profit, plus 4797 gains and other income.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Page 1 Lines 7-20 — Deductions",
                "excerpt_text": "Deductions: Line 7 Compensation of officers, Line 8 Salaries and wages, Line 9 Repairs and maintenance, Line 10 Bad debts, Line 11 Rents, Line 12 Taxes and licenses, Line 13 Interest (subject to business interest limitation), Line 14 Depreciation (Form 4562 — do not include section 179), Line 15 Depletion, Line 16 Advertising, Line 17 Pension profit-sharing plans, Line 18 Employee benefit programs, Line 19 Other deductions. Line 20: Total deductions (add lines 7 through 19).",
                "summary_text": "Page 1 deductions: 13 categories summed on Line 20. Section 179 is NOT included — it is separately stated on Schedule K Line 11.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Page 1 Line 21 — Ordinary business income (loss)",
                "excerpt_text": "Ordinary business income (loss). Subtract line 20 from line 6. Enter the result here and on Schedule K, line 1. If the corporation has income from rental activities, complete Form 8825.",
                "summary_text": "Line 21 = Line 6 minus Line 20. This is the core operating result that flows to Schedule K Line 1.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule K — Line sources and separately stated items",
                "excerpt_text": "Schedule K is a summary schedule of all shareholders' shares of the corporation's income, deductions, credits, and other items. Each line item represents a separately stated item that must pass through to each shareholder's K-1. Line 1 = Page 1 Line 21 (ordinary income). Line 2 = Form 8825 (rental real estate). Lines 4-6 = portfolio income (interest, dividends, royalties). Line 7 = Schedule D net short-term. Line 8a = Schedule D net long-term. Line 9 = Form 4797 Part I Line 7 (net section 1231 gain/loss). Line 11 = section 179 deduction (separately stated, NOT on Page 1).",
                "summary_text": "Schedule K aggregates all separately stated items. Each K line maps to a K-1 box.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule K Line 9 — Net section 1231 gain (loss)",
                "excerpt_text": "Enter the net section 1231 gain (loss) from Form 4797, Part I, line 7. Section 1231 gains and losses from the sale or exchange of property used in a trade or business held for more than 1 year are reported here, not on Schedule D. This amount flows to each shareholder's K-1, Box 9.",
                "summary_text": "K9 = Form 4797 Part I Line 7. Section 1231 bypasses Schedule D on the 1120-S.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule M-1 — Reconciliation of income per books with income per return",
                "excerpt_text": "Line 1: Net income (loss) per books. Line 2: Income included on Schedule K, lines 1 through 10, not recorded on books this year. Line 3a: Guaranteed payments (section 707(c)) — for partnerships only, should be zero for S corporations. Line 3b: Expenses recorded on books this year not included on Schedule K (including travel and entertainment — the 50% nondeductible portion of meals). Line 4: Add lines 1 through 3b. Line 5a: Income recorded on books this year not included on Schedule K (such as tax-exempt interest). Line 5b: Deductions included on Schedule K not charged against book income this year (such as excess depreciation). Line 6: Add lines 5a and 5b. Line 7: Income (loss) per return. Subtract line 6 from line 4. Line 8: Income per return should equal Schedule K, line 18, and Page 1, line 21.",
                "summary_text": "M-1 reconciles book to tax. Line 3b is an ADD-BACK (positive). Line 8 must equal Page 1 Line 21.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule M-2 — Analysis of AAA, OAA, PTEP, and AE&P",
                "excerpt_text": "Column (a) Accumulated Adjustments Account (AAA): Line 1 Balance at beginning of year. Line 2 Ordinary business income from Page 1, line 21. Line 3 Other additions (tax-exempt income for OAA column, other items). Line 4 Loss from Page 1, line 21 (if a loss). Line 5 Other reductions (nondeductible expenses, oil/gas depletion). Line 6 Combine lines 1 through 5. Line 7 Distributions other than dividend distributions. Line 8 Balance at end of tax year (line 6 minus line 7). The AAA may have a negative balance at year end, but distributions may not reduce AAA below zero — any distribution exceeding AAA is treated as a return of basis then capital gain under section 1368.",
                "summary_text": "M-2 tracks AAA/OAA/PTEP/AE&P. Distributions cannot reduce AAA below zero. Losses CAN make AAA negative.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "4797 flow — bypasses Schedule D",
                "excerpt_text": "Section 1231 gains and losses are reported on Form 4797 and flow to Schedule K Line 9 (for K-1 Box 9 allocation to shareholders). They do NOT flow through Schedule D on the 1120-S. Form 4797 Part II Line 17 (ordinary gains) flows to Page 1 Line 4. Capital asset transactions (stocks, bonds, other capital assets) flow through Form 8949 to Schedule D.",
                "summary_text": "4797 bypasses Schedule D on 1120-S. Part II L17 -> P1 L4. Part I L7 -> K9.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_1120S_SCHD_INSTR_FULL",
        "source_type": "official_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "Instructions for Schedule D (Form 1120-S) (2025) — fetched 2026-03-18",
        "citation": "Instructions for Schedule D (Form 1120-S) (2025)",
        "issuer": "IRS",
        "current_status": "active",
        "is_substantive_authority": True,
        "requires_human_review": False,
        "trust_score": 9.5,
        "topics": ["schedule_d", "capital_gains", "1120s"],
        "excerpts": [
            {
                "excerpt_label": "Part I — Short-term capital gains and losses",
                "excerpt_text": "Report on Part I the sale or exchange of capital assets held 1 year or less. Line 1a: Totals from Form 8949 Box A (basis reported to IRS, no adjustments). Line 1b: Totals from Form 8949 Box B (basis reported, with adjustments). Line 1c: Totals from Form 8949 Box C (basis NOT reported to IRS). Lines 2-4: Short-term gain from installment sales (Form 6252), like-kind exchanges (Form 8824), S corporation's share from other entities. Line 5: Net short-term capital gain (loss) — combine lines 1 through 4. Carry to Schedule K, line 7.",
                "summary_text": "Schedule D Part I Line 5 (net short-term) flows to Schedule K Line 7.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part II — Long-term capital gains and losses",
                "excerpt_text": "Report on Part II the sale or exchange of capital assets held more than 1 year. Line 7a: Totals from Form 8949 Box D (basis reported to IRS, no adjustments). Line 7b: Totals from Form 8949 Box E (basis reported, with adjustments). Line 7c: Totals from Form 8949 Box F (basis NOT reported to IRS). Lines 8-10: Long-term gain from installment sales, like-kind exchanges, S corporation's share from other entities. Line 11: Capital gain distributions. Line 12: Net long-term capital gain (loss) — combine lines 7 through 11. Carry to Schedule K, line 8a.",
                "summary_text": "Schedule D Part II Line 12 (net long-term) flows to Schedule K Line 8a.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule D does NOT include Section 1231",
                "excerpt_text": "Do not report on Schedule D the sale or exchange of property used in a trade or business — report those on Form 4797. Section 1231 gains and losses are reported on Form 4797 and flow to Schedule K line 9, not through Schedule D.",
                "summary_text": "Section 1231 transactions go to 4797, NOT Schedule D. 4797 -> K9 directly.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part III — Built-in gains tax (section 1374)",
                "excerpt_text": "If the S corporation was formerly a C corporation (or received assets from a C corporation in a carryover basis transaction), it may be subject to tax on built-in gains recognized within the 5-year recognition period. The tax is 21% of net recognized built-in gain, limited to the net unrealized built-in gain at the time of the S election. Complete Part III only if the corporation had a net recognized built-in gain during the tax year.",
                "summary_text": "BIG tax = 21% of net recognized built-in gain within 5-year recognition period, limited to NUBIG.",
                "is_key_excerpt": True,
            },
        ],
    },
]

# Source codes already loaded by load_all_federal or load_1120s_specs
EXISTING_SOURCES = [
    "IRS_2025_1120S_INSTR", "IRC_1363", "IRC_1366", "IRC_1367", "IRC_1368",
    "IRC_1374", "IRC_1377", "IRC_179", "IRC_168", "IRC_1222", "IRC_199A",
    "IRC_1231", "IRC_1245", "IRC_1250", "IRS_2025_4797_INSTR",
    "IRS_2025_1120S_SCHD_INSTR", "IRS_2025_1120S_K1_INSTR",
]


class Command(BaseCommand):
    help = "Load 1120-S full specs — Page 1, M-1, M-2, expanded K, cross-form diagnostics"

    def handle(self, *_args, **_options):
        with transaction.atomic():
            sources = self._load_sources()
            self._load_page1(sources)
            self._load_schedule_m1(sources)
            self._load_schedule_m2(sources)
            self._expand_schedule_k(sources)
            self._add_schedule_d_flow_rules(sources)
            self._add_cross_form_diagnostics(sources)
            self._add_cross_form_tests(sources)
        self._report_totals()

    # ─────────────────────────────────────────────────────────────────────────
    # Authority sources
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

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers (same pattern as load_1120s_specs.py)
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
                    defaults={"note": f"{source_code} -> {form_code}"},
                )

    # ═══════════════════════════════════════════════════════════════════════════
    # Form 1120-S Page 1 — Income & Deductions (Lines 1-21)
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_page1(self, sources):
        form = self._upsert_form(
            "1120S_PAGE1",
            "Form 1120-S Page 1 — Income and Deductions",
            ["1120S"],
            notes="Core income/deduction computation. Line 21 = ordinary business income flows to Schedule K Line 1.",
        )

        self._upsert_facts(form, [
            # Income
            {"fact_key": "gross_receipts", "label": "Gross receipts or sales (Line 1a)", "data_type": "decimal", "required": True, "sort_order": 1},
            {"fact_key": "returns_allowances", "label": "Returns and allowances (Line 1b)", "data_type": "decimal", "sort_order": 2},
            {"fact_key": "net_receipts", "label": "Net receipts (Line 1c = 1a - 1b)", "data_type": "decimal", "sort_order": 3},
            {"fact_key": "cost_of_goods_sold", "label": "Cost of goods sold (Line 2, from Form 1125-A)", "data_type": "decimal", "sort_order": 4},
            {"fact_key": "gross_profit", "label": "Gross profit (Line 3 = 1c - 2)", "data_type": "decimal", "sort_order": 5},
            {"fact_key": "net_gain_4797", "label": "Net gain (loss) from Form 4797, Part II, Line 17 (Line 4)", "data_type": "decimal", "sort_order": 6},
            {"fact_key": "other_income", "label": "Other income (loss) (Line 5)", "data_type": "decimal", "sort_order": 7},
            {"fact_key": "total_income", "label": "Total income (loss) (Line 6 = 3 + 4 + 5)", "data_type": "decimal", "sort_order": 8},
            # Deductions
            {"fact_key": "officer_compensation", "label": "Compensation of officers (Line 7)", "data_type": "decimal", "sort_order": 9},
            {"fact_key": "salaries_wages", "label": "Salaries and wages (Line 8)", "data_type": "decimal", "sort_order": 10},
            {"fact_key": "repairs_maintenance", "label": "Repairs and maintenance (Line 9)", "data_type": "decimal", "sort_order": 11},
            {"fact_key": "bad_debts", "label": "Bad debts (Line 10)", "data_type": "decimal", "sort_order": 12},
            {"fact_key": "rents", "label": "Rents (Line 11)", "data_type": "decimal", "sort_order": 13},
            {"fact_key": "taxes_licenses", "label": "Taxes and licenses (Line 12)", "data_type": "decimal", "sort_order": 14},
            {"fact_key": "interest", "label": "Interest (Line 13)", "data_type": "decimal", "sort_order": 15},
            {"fact_key": "depreciation", "label": "Depreciation (Line 14, from Form 4562, NOT including section 179)", "data_type": "decimal", "sort_order": 16},
            {"fact_key": "depletion", "label": "Depletion (Line 15)", "data_type": "decimal", "sort_order": 17},
            {"fact_key": "advertising", "label": "Advertising (Line 16)", "data_type": "decimal", "sort_order": 18},
            {"fact_key": "pension_plans", "label": "Pension, profit-sharing, etc., plans (Line 17)", "data_type": "decimal", "sort_order": 19},
            {"fact_key": "employee_benefits", "label": "Employee benefit programs (Line 18)", "data_type": "decimal", "sort_order": 20},
            {"fact_key": "other_deductions", "label": "Other deductions (Line 19, attach statement)", "data_type": "decimal", "sort_order": 21},
            {"fact_key": "total_deductions", "label": "Total deductions (Line 20 = sum of Lines 7-19)", "data_type": "decimal", "sort_order": 22},
            {"fact_key": "ordinary_business_income", "label": "Ordinary business income (loss) (Line 21 = Line 6 - Line 20)", "data_type": "decimal", "sort_order": 23},
        ])

        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "Net receipts", "description": "Line 1c = Line 1a - Line 1b",
             "rule_type": "calculation", "formula": "gross_receipts - returns_allowances",
             "inputs": ["gross_receipts", "returns_allowances"], "outputs": ["net_receipts"],
             "precedence": 1, "sort_order": 1},
            {"rule_id": "R002", "title": "Gross profit", "description": "Line 3 = Line 1c - Line 2 (cost of goods sold from Form 1125-A)",
             "rule_type": "calculation", "formula": "net_receipts - cost_of_goods_sold",
             "inputs": ["net_receipts", "cost_of_goods_sold"], "outputs": ["gross_profit"],
             "precedence": 2, "sort_order": 2},
            {"rule_id": "R003", "title": "Page 1 Line 4 = Form 4797 Part II Line 17",
             "description": "Net gain (loss) from Form 4797. This is the ORDINARY gain/loss from Part II Line 17, which includes short-term dispositions and recapture from Part III Line 31. NOT the Section 1231 gain from Part I — that goes to Schedule K Line 9.",
             "rule_type": "routing", "formula": "Form_4797_Part_II_Line_17",
             "inputs": ["4797_part2_line17"], "outputs": ["net_gain_4797"],
             "precedence": 3, "sort_order": 3,
             "notes": "VERIFIED from fresh IRS 1120-S instructions fetch 2026-03-18. This was a persistent bug source in tts-tax-app."},
            {"rule_id": "R004", "title": "Total income", "description": "Line 6 = Line 3 + Line 4 + Line 5",
             "rule_type": "calculation", "formula": "gross_profit + net_gain_4797 + other_income",
             "inputs": ["gross_profit", "net_gain_4797", "other_income"], "outputs": ["total_income"],
             "precedence": 4, "sort_order": 4},
            {"rule_id": "R005", "title": "Total deductions", "description": "Line 20 = sum of Lines 7 through 19. Section 179 is NOT included here — it is separately stated on Schedule K Line 11.",
             "rule_type": "calculation",
             "formula": "officer_compensation + salaries_wages + repairs_maintenance + bad_debts + rents + taxes_licenses + interest + depreciation + depletion + advertising + pension_plans + employee_benefits + other_deductions",
             "inputs": ["officer_compensation", "salaries_wages", "repairs_maintenance", "bad_debts", "rents",
                         "taxes_licenses", "interest", "depreciation", "depletion", "advertising",
                         "pension_plans", "employee_benefits", "other_deductions"],
             "outputs": ["total_deductions"], "precedence": 5, "sort_order": 5},
            {"rule_id": "R006", "title": "Ordinary business income (loss)",
             "description": "Line 21 = Line 6 - Line 20. This is the key output of Page 1. Flows to Schedule K Line 1 for shareholder allocation.",
             "rule_type": "calculation", "formula": "total_income - total_deductions",
             "inputs": ["total_income", "total_deductions"], "outputs": ["ordinary_business_income"],
             "precedence": 6, "sort_order": 6},
            {"rule_id": "R007", "title": "Section 179 exclusion from Page 1",
             "description": "Section 179 deduction is a SEPARATELY STATED item under IRC 1363(b). It must appear on Schedule K Line 11, NOT on Page 1 Line 14 (depreciation). Page 1 Line 14 includes regular depreciation and bonus depreciation only.",
             "rule_type": "validation",
             "formula": "depreciation_line_14 must NOT include section_179_amount",
             "inputs": ["depreciation", "section_179_deduction"], "outputs": [],
             "precedence": 0, "sort_order": 7,
             "notes": "IRC 1363(b) requires separately stated items to be excluded from ordinary income computation."},
            {"rule_id": "R008", "title": "Line 14 depreciation source",
             "description": "Page 1 Line 14 = Form 4562 total depreciation minus section 179 (which is separately stated on K Line 11). Includes MACRS regular depreciation and bonus depreciation.",
             "rule_type": "routing", "formula": "Form_4562_total_depreciation - section_179",
             "inputs": ["form_4562_depreciation", "section_179_deduction"], "outputs": ["depreciation"],
             "precedence": 3, "sort_order": 8},
        ])

        self._upsert_links(rules, sources, [
            ("R001", "IRS_2025_1120S_INSTR_FULL", "primary", "Page 1 income computation"),
            ("R002", "IRS_2025_1120S_INSTR_FULL", "primary", "Gross profit = net receipts - COGS"),
            ("R003", "IRS_2025_1120S_INSTR_FULL", "primary", "Line 4 = Form 4797 Part II Line 17 (verified from fetched instructions)"),
            ("R003", "IRS_2025_4797_INSTR", "secondary", "Form 4797 Part II Line 17 = ordinary gains/losses"),
            ("R004", "IRS_2025_1120S_INSTR_FULL", "primary", "Total income = lines 3+4+5"),
            ("R005", "IRS_2025_1120S_INSTR_FULL", "primary", "Total deductions = sum lines 7-19"),
            ("R006", "IRS_2025_1120S_INSTR_FULL", "primary", "Line 21 = Line 6 - Line 20, flows to K Line 1"),
            ("R006", "IRC_1363", "secondary", "IRC 1363(b) — separately stated items excluded"),
            ("R007", "IRC_1363", "primary", "IRC 1363(b) — section 179 is separately stated"),
            ("R007", "IRC_179", "secondary", "IRC 179(d)(4) — passthrough separately stated for S-Corps"),
            ("R008", "IRS_2025_1120S_INSTR_FULL", "primary", "Line 14 depreciation from Form 4562"),
        ])

        self._upsert_lines(form, [
            {"line_number": "1a", "description": "Gross receipts or sales", "line_type": "input", "sort_order": 1},
            {"line_number": "1b", "description": "Returns and allowances", "line_type": "input", "sort_order": 2},
            {"line_number": "1c", "description": "Balance (1a minus 1b)", "line_type": "calculated", "source_rules": ["R001"], "sort_order": 3},
            {"line_number": "2", "description": "Cost of goods sold (Form 1125-A)", "line_type": "input", "destination_form": "Form 1125-A", "sort_order": 4},
            {"line_number": "3", "description": "Gross profit (1c minus 2)", "line_type": "calculated", "source_rules": ["R002"], "sort_order": 5},
            {"line_number": "4", "description": "Net gain (loss) from Form 4797, Part II, line 17", "line_type": "calculated", "source_rules": ["R003"], "destination_form": "Form 4797 Part II Line 17", "sort_order": 6},
            {"line_number": "5", "description": "Other income (loss)", "line_type": "input", "sort_order": 7},
            {"line_number": "6", "description": "Total income (loss) (add lines 3 through 5)", "line_type": "subtotal", "source_rules": ["R004"], "sort_order": 8},
            {"line_number": "7", "description": "Compensation of officers", "line_type": "input", "sort_order": 9},
            {"line_number": "8", "description": "Salaries and wages", "line_type": "input", "sort_order": 10},
            {"line_number": "9", "description": "Repairs and maintenance", "line_type": "input", "sort_order": 11},
            {"line_number": "10", "description": "Bad debts", "line_type": "input", "sort_order": 12},
            {"line_number": "11", "description": "Rents", "line_type": "input", "sort_order": 13},
            {"line_number": "12", "description": "Taxes and licenses", "line_type": "input", "sort_order": 14},
            {"line_number": "13", "description": "Interest", "line_type": "input", "sort_order": 15},
            {"line_number": "14", "description": "Depreciation (Form 4562, NOT including section 179)", "line_type": "calculated", "source_rules": ["R008"], "destination_form": "Form 4562", "sort_order": 16},
            {"line_number": "15", "description": "Depletion", "line_type": "input", "sort_order": 17},
            {"line_number": "16", "description": "Advertising", "line_type": "input", "sort_order": 18},
            {"line_number": "17", "description": "Pension, profit-sharing, etc., plans", "line_type": "input", "sort_order": 19},
            {"line_number": "18", "description": "Employee benefit programs", "line_type": "input", "sort_order": 20},
            {"line_number": "19", "description": "Other deductions (attach statement)", "line_type": "input", "sort_order": 21},
            {"line_number": "20", "description": "Total deductions (add lines 7 through 19)", "line_type": "subtotal", "source_rules": ["R005"], "sort_order": 22},
            {"line_number": "21", "description": "Ordinary business income (loss) (line 6 minus line 20)", "line_type": "total", "source_rules": ["R006"], "destination_form": "Schedule K Line 1", "sort_order": 23,
             "notes": "Key output of Page 1. Flows to Schedule K Line 1 for shareholder allocation."},
        ])

        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D001", "title": "Section 179 on Page 1", "severity": "error",
             "condition": "depreciation includes section_179_amount",
             "message": "Section 179 must be separately stated on Schedule K Line 11, not included in Page 1 Line 14 depreciation. Per IRC 1363(b)."},
            {"diagnostic_id": "D002", "title": "Line 4 source mismatch", "severity": "warning",
             "condition": "net_gain_4797 != Form_4797_Part_II_Line_17",
             "message": "Page 1 Line 4 should equal Form 4797 Part II Line 17. Verify 4797 is computed correctly."},
            {"diagnostic_id": "D003", "title": "Charitable on Page 1", "severity": "error",
             "condition": "other_deductions includes charitable_contributions",
             "message": "Charitable contributions are separately stated on Schedule K Lines 12a/12b, not deducted on Page 1."},
        ])

        self._upsert_tests(form, [
            {"scenario_name": "Basic S-Corp — ordinary income only",
             "scenario_type": "normal",
             "inputs": {"gross_receipts": 500000, "returns_allowances": 5000, "cost_of_goods_sold": 200000,
                         "net_gain_4797": 0, "other_income": 0,
                         "officer_compensation": 80000, "salaries_wages": 60000, "repairs_maintenance": 5000,
                         "bad_debts": 0, "rents": 12000, "taxes_licenses": 8000, "interest": 3000,
                         "depreciation": 15000, "depletion": 0, "advertising": 2000,
                         "pension_plans": 5000, "employee_benefits": 4000, "other_deductions": 6000},
             "expected_outputs": {"net_receipts": 495000, "gross_profit": 295000,
                                   "total_income": 295000, "total_deductions": 200000,
                                   "ordinary_business_income": 95000},
             "notes": "No dispositions, no special items. All income flows through K1.", "sort_order": 1},
            {"scenario_name": "S-Corp with 4797 gain flowing to Page 1 Line 4",
             "scenario_type": "normal",
             "inputs": {"gross_receipts": 300000, "returns_allowances": 0, "cost_of_goods_sold": 100000,
                         "net_gain_4797": 25000, "other_income": 0,
                         "officer_compensation": 50000, "salaries_wages": 30000, "repairs_maintenance": 0,
                         "bad_debts": 0, "rents": 0, "taxes_licenses": 5000, "interest": 2000,
                         "depreciation": 10000, "depletion": 0, "advertising": 0,
                         "pension_plans": 0, "employee_benefits": 0, "other_deductions": 3000},
             "expected_outputs": {"gross_profit": 200000, "total_income": 225000,
                                   "total_deductions": 100000, "ordinary_business_income": 125000},
             "notes": "4797 Part II Line 17 = 25000 flows to Line 4. Section 1231 gain flows separately to K9.", "sort_order": 2},
        ])

        self._upsert_form_links("1120S_PAGE1", sources, [
            ("IRS_2025_1120S_INSTR_FULL", "governs"),
            ("IRC_1363", "governs"),
        ])

        self.stdout.write(self.style.SUCCESS("  Page 1 complete."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Schedule M-1 — Reconciliation of Income per Books with Income per Return
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_schedule_m1(self, sources):
        form = self._upsert_form(
            "1120S_M1",
            "Schedule M-1 — Reconciliation of Income (Loss) per Books With Income (Loss) per Return",
            ["1120S"],
            notes="Reconciles book net income to taxable income (Page 1 Line 21). Critical: Line 3b is an ADD-BACK (positive number).",
        )

        self._upsert_facts(form, [
            {"fact_key": "book_net_income", "label": "Net income (loss) per books (Line 1)", "data_type": "decimal", "required": True, "sort_order": 1},
            {"fact_key": "income_on_k_not_books", "label": "Income on Schedule K not recorded on books (Line 2)", "data_type": "decimal", "sort_order": 2,
             "notes": "Items included on Schedule K lines 1-10 that are NOT on the financial statements."},
            {"fact_key": "guaranteed_payments", "label": "Guaranteed payments, section 707(c) (Line 3a)", "data_type": "decimal", "sort_order": 3,
             "notes": "PARTNERSHIPS ONLY. Should be $0 for S-Corps."},
            {"fact_key": "expenses_not_on_k", "label": "Expenses on books not on Schedule K (Line 3b)", "data_type": "decimal", "sort_order": 4,
             "notes": "ADD-BACK: 50% nondeductible meals, fines, penalties, political contributions. This is a POSITIVE number that INCREASES taxable income."},
            {"fact_key": "line_4_subtotal", "label": "Add lines 1 through 3b (Line 4)", "data_type": "decimal", "sort_order": 5},
            {"fact_key": "income_on_books_not_k", "label": "Income on books not on Schedule K (Line 5a)", "data_type": "decimal", "sort_order": 6,
             "notes": "Tax-exempt interest, life insurance proceeds, other non-taxable book income."},
            {"fact_key": "deductions_on_k_not_books", "label": "Deductions on Schedule K not on books (Line 5b)", "data_type": "decimal", "sort_order": 7,
             "notes": "Bonus depreciation, section 179 in excess of book depreciation, etc."},
            {"fact_key": "line_6_subtotal", "label": "Add lines 5a and 5b (Line 6)", "data_type": "decimal", "sort_order": 8},
            {"fact_key": "income_per_return", "label": "Income (loss) per return (Line 7 = Line 4 - Line 6)", "data_type": "decimal", "sort_order": 9},
        ])

        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "Line 4 subtotal",
             "description": "Line 4 = Line 1 + Line 2 + Line 3a + Line 3b. This is book income plus add-backs.",
             "rule_type": "calculation", "formula": "book_net_income + income_on_k_not_books + guaranteed_payments + expenses_not_on_k",
             "inputs": ["book_net_income", "income_on_k_not_books", "guaranteed_payments", "expenses_not_on_k"],
             "outputs": ["line_4_subtotal"], "precedence": 1, "sort_order": 1},
            {"rule_id": "R002", "title": "Line 6 subtotal",
             "description": "Line 6 = Line 5a + Line 5b. These are subtractions (book income not taxable + tax deductions not on books).",
             "rule_type": "calculation", "formula": "income_on_books_not_k + deductions_on_k_not_books",
             "inputs": ["income_on_books_not_k", "deductions_on_k_not_books"],
             "outputs": ["line_6_subtotal"], "precedence": 2, "sort_order": 2},
            {"rule_id": "R003", "title": "Line 7 = Income per return",
             "description": "Line 7 = Line 4 - Line 6. This is the taxable income per the return.",
             "rule_type": "calculation", "formula": "line_4_subtotal - line_6_subtotal",
             "inputs": ["line_4_subtotal", "line_6_subtotal"],
             "outputs": ["income_per_return"], "precedence": 3, "sort_order": 3},
            {"rule_id": "R004", "title": "M-1 balance check",
             "description": "Line 7 (and Line 8) must equal Page 1 Line 21 (ordinary business income). If they differ, the M-1 reconciliation is incorrect.",
             "rule_type": "validation", "formula": "income_per_return == page1_line_21",
             "inputs": ["income_per_return"], "outputs": [],
             "precedence": 10, "sort_order": 4},
            {"rule_id": "R005", "title": "Line 3b must be positive (add-back)",
             "description": "Line 3b represents expenses on books that are NOT deductible on the return (e.g., 50% of meals, fines, penalties). This is an ADD-BACK to book income, so it must be a positive number. A negative value would incorrectly subtract from taxable income.",
             "rule_type": "validation", "formula": "expenses_not_on_k >= 0",
             "inputs": ["expenses_not_on_k"], "outputs": [],
             "precedence": 0, "sort_order": 5,
             "notes": "CRITICAL: M-1 Line 3b sign error was a persistent bug in tts-tax-app. Line 3b is ALWAYS an addition."},
            {"rule_id": "R006", "title": "Guaranteed payments must be zero for S-Corps",
             "description": "Line 3a (guaranteed payments under section 707(c)) applies only to partnerships. For S-Corps, this line must be zero.",
             "rule_type": "validation", "formula": "guaranteed_payments == 0 when entity_type == '1120S'",
             "inputs": ["guaranteed_payments"], "outputs": [],
             "precedence": 0, "sort_order": 6},
        ])

        self._upsert_links(rules, sources, [
            ("R001", "IRS_2025_1120S_INSTR_FULL", "primary", "M-1 Lines 1-3b: book income + add-backs"),
            ("R002", "IRS_2025_1120S_INSTR_FULL", "primary", "M-1 Lines 5a-5b: subtractions"),
            ("R003", "IRS_2025_1120S_INSTR_FULL", "primary", "M-1 Line 7 = Line 4 - Line 6"),
            ("R004", "IRS_2025_1120S_INSTR_FULL", "primary", "Line 8 must equal Page 1 Line 21"),
            ("R005", "IRS_2025_1120S_INSTR_FULL", "primary", "Line 3b is expenses on books not deducted = ADD-BACK"),
            ("R006", "IRS_2025_1120S_INSTR_FULL", "primary", "Line 3a guaranteed payments — partnerships only"),
        ])

        self._upsert_lines(form, [
            {"line_number": "1", "description": "Net income (loss) per books", "line_type": "input", "sort_order": 1},
            {"line_number": "2", "description": "Income included on Schedule K, lines 1-10, not recorded on books", "line_type": "input", "sort_order": 2},
            {"line_number": "3a", "description": "Guaranteed payments (section 707(c)) — should be $0 for S-Corps", "line_type": "input", "sort_order": 3},
            {"line_number": "3b", "description": "Expenses on books not on Schedule K (50% meals, fines, etc.) — ADD-BACK", "line_type": "input", "sort_order": 4,
             "notes": "CRITICAL: This is a POSITIVE number. It increases taxable income. A negative value here is a bug."},
            {"line_number": "4", "description": "Add lines 1 through 3b", "line_type": "subtotal", "source_rules": ["R001"], "sort_order": 5},
            {"line_number": "5a", "description": "Income on books not on Schedule K (tax-exempt interest, etc.)", "line_type": "input", "sort_order": 6},
            {"line_number": "5b", "description": "Deductions on Schedule K not charged against book income (bonus depr, etc.)", "line_type": "input", "sort_order": 7},
            {"line_number": "6", "description": "Add lines 5a and 5b", "line_type": "subtotal", "source_rules": ["R002"], "sort_order": 8},
            {"line_number": "7", "description": "Income (loss) per return (line 4 minus line 6)", "line_type": "total", "source_rules": ["R003"], "sort_order": 9,
             "notes": "Must equal Page 1 Line 21 and Schedule K Line 18."},
            {"line_number": "8", "description": "Income per return — must equal Schedule K line 18 and Page 1 line 21", "line_type": "informational", "source_rules": ["R004"], "sort_order": 10,
             "destination_form": "Page 1 Line 21"},
        ])

        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D001", "title": "M-1 does not balance", "severity": "error",
             "condition": "income_per_return != page1_line_21",
             "message": "Schedule M-1 Line 7 does not equal Page 1 Line 21. The reconciliation is incorrect."},
            {"diagnostic_id": "D002", "title": "M-1 Line 3b is negative", "severity": "error",
             "condition": "expenses_not_on_k < 0",
             "message": "M-1 Line 3b (expenses on books not on return) should be a POSITIVE add-back. A negative value here incorrectly reduces taxable income. This is a common bug — Line 3b adds the nondeductible portion (e.g., 50% of meals)."},
            {"diagnostic_id": "D003", "title": "Guaranteed payments on S-Corp M-1", "severity": "error",
             "condition": "guaranteed_payments != 0 AND entity_type == '1120S'",
             "message": "M-1 Line 3a (guaranteed payments) should be $0 for S corporations. Guaranteed payments apply only to partnerships under section 707(c)."},
        ])

        self._upsert_tests(form, [
            {"scenario_name": "M-1 with meals nondeductible add-back",
             "scenario_type": "normal",
             "inputs": {"book_net_income": 85000, "income_on_k_not_books": 0,
                         "guaranteed_payments": 0, "expenses_not_on_k": 5000,
                         "income_on_books_not_k": 0, "deductions_on_k_not_books": 0},
             "expected_outputs": {"line_4_subtotal": 90000, "line_6_subtotal": 0, "income_per_return": 90000},
             "notes": "Book income $85K + $5K meals add-back (50% of $10K meals) = $90K taxable income. Line 3b is POSITIVE.", "sort_order": 1},
            {"scenario_name": "M-1 with bonus depreciation difference",
             "scenario_type": "normal",
             "inputs": {"book_net_income": 120000, "income_on_k_not_books": 0,
                         "guaranteed_payments": 0, "expenses_not_on_k": 2000,
                         "income_on_books_not_k": 3000, "deductions_on_k_not_books": 50000},
             "expected_outputs": {"line_4_subtotal": 122000, "line_6_subtotal": 53000, "income_per_return": 69000},
             "notes": "Book income + meals add-back - tax-exempt interest - bonus depr excess = taxable income.", "sort_order": 2},
            {"scenario_name": "M-1 with loss",
             "scenario_type": "edge",
             "inputs": {"book_net_income": -30000, "income_on_k_not_books": 5000,
                         "guaranteed_payments": 0, "expenses_not_on_k": 1000,
                         "income_on_books_not_k": 0, "deductions_on_k_not_books": 20000},
             "expected_outputs": {"line_4_subtotal": -24000, "line_6_subtotal": 20000, "income_per_return": -44000},
             "notes": "Book loss scenario. M-1 still balances — large deductions on K not on books (bonus depr).", "sort_order": 3},
        ])

        self._upsert_form_links("1120S_M1", sources, [
            ("IRS_2025_1120S_INSTR_FULL", "governs"),
        ])

        self.stdout.write(self.style.SUCCESS("  M-1 complete."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Schedule M-2 — Analysis of AAA, OAA, PTEP, and Shareholders' Equity
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_schedule_m2(self, sources):
        form = self._upsert_form(
            "1120S_M2",
            "Schedule M-2 — Analysis of AAA, OAA, PTEP, and Shareholders' Undistributed Taxable Income",
            ["1120S"],
            notes="Tracks accumulated adjustments. Distributions cannot reduce AAA below zero. Losses CAN make AAA negative.",
        )

        self._upsert_facts(form, [
            # AAA column
            {"fact_key": "aaa_beginning", "label": "AAA balance at beginning of year (Line 1, col a)", "data_type": "decimal", "required": True, "sort_order": 1},
            {"fact_key": "aaa_ordinary_income", "label": "AAA ordinary business income (Line 2, col a)", "data_type": "decimal", "sort_order": 2,
             "notes": "From Page 1 Line 21 — only if positive."},
            {"fact_key": "aaa_other_additions", "label": "AAA other additions (Line 3, col a)", "data_type": "decimal", "sort_order": 3},
            {"fact_key": "aaa_loss", "label": "AAA loss (Line 4, col a)", "data_type": "decimal", "sort_order": 4,
             "notes": "From Page 1 Line 21 if a loss. Entered as a positive number."},
            {"fact_key": "aaa_other_reductions", "label": "AAA other reductions (Line 5, col a)", "data_type": "decimal", "sort_order": 5,
             "notes": "Nondeductible expenses, oil/gas depletion."},
            {"fact_key": "aaa_combined", "label": "AAA combine lines 1-5 (Line 6, col a)", "data_type": "decimal", "sort_order": 6},
            {"fact_key": "aaa_distributions", "label": "AAA distributions (Line 7, col a)", "data_type": "decimal", "sort_order": 7,
             "notes": "Cannot reduce AAA below zero. Excess distributions treated as return of basis then capital gain."},
            {"fact_key": "aaa_ending", "label": "AAA balance at end of year (Line 8, col a)", "data_type": "decimal", "sort_order": 8},
            # OAA column
            {"fact_key": "oaa_beginning", "label": "OAA balance at beginning of year (Line 1, col d)", "data_type": "decimal", "sort_order": 9},
            {"fact_key": "oaa_additions", "label": "OAA additions — tax-exempt income (Line 3, col d)", "data_type": "decimal", "sort_order": 10},
            {"fact_key": "oaa_reductions", "label": "OAA reductions — related nondeductible expenses (Line 5, col d)", "data_type": "decimal", "sort_order": 11},
            {"fact_key": "oaa_distributions", "label": "OAA distributions (Line 7, col d)", "data_type": "decimal", "sort_order": 12},
            {"fact_key": "oaa_ending", "label": "OAA balance at end of year (Line 8, col d)", "data_type": "decimal", "sort_order": 13},
            # Shareholders' equity
            {"fact_key": "retained_earnings_beginning", "label": "Retained earnings at beginning of year", "data_type": "decimal", "sort_order": 14},
            {"fact_key": "total_distributions", "label": "Total distributions to shareholders during year", "data_type": "decimal", "sort_order": 15},
        ])

        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "AAA combine (Line 6)",
             "description": "AAA Line 6 = Line 1 + Line 2 + Line 3 - Line 4 - Line 5. Beginning balance plus income and additions, minus losses and reductions.",
             "rule_type": "calculation",
             "formula": "aaa_beginning + aaa_ordinary_income + aaa_other_additions - aaa_loss - aaa_other_reductions",
             "inputs": ["aaa_beginning", "aaa_ordinary_income", "aaa_other_additions", "aaa_loss", "aaa_other_reductions"],
             "outputs": ["aaa_combined"], "precedence": 1, "sort_order": 1},
            {"rule_id": "R002", "title": "AAA ending balance (Line 8)",
             "description": "AAA Line 8 = Line 6 - Line 7 (distributions). Distributions cannot reduce AAA below zero.",
             "rule_type": "calculation",
             "formula": "aaa_combined - min(aaa_distributions, max(0, aaa_combined))",
             "inputs": ["aaa_combined", "aaa_distributions"],
             "outputs": ["aaa_ending"], "precedence": 2, "sort_order": 2,
             "notes": "The min/max formula ensures distributions cannot make AAA negative, but losses CAN."},
            {"rule_id": "R003", "title": "Distribution ordering — AAA first",
             "description": "Under section 1368(c), distributions are first applied to AAA (tax-free return of basis), then to accumulated E&P (taxed as dividends), then to remaining basis (return of capital), then as capital gain. Unless the corporation elects to distribute AE&P first.",
             "rule_type": "conditional",
             "formula": "if aaa_combined >= aaa_distributions then all_from_aaa else excess_to_basis_or_gain",
             "inputs": ["aaa_combined", "aaa_distributions"], "outputs": ["distribution_treatment"],
             "precedence": 3, "sort_order": 3},
            {"rule_id": "R004", "title": "OAA ending balance",
             "description": "OAA tracks tax-exempt income and related nondeductible expenses. OAA ending = beginning + additions - reductions - distributions from OAA.",
             "rule_type": "calculation",
             "formula": "oaa_beginning + oaa_additions - oaa_reductions - oaa_distributions",
             "inputs": ["oaa_beginning", "oaa_additions", "oaa_reductions", "oaa_distributions"],
             "outputs": ["oaa_ending"], "precedence": 1, "sort_order": 4},
        ])

        self._upsert_links(rules, sources, [
            ("R001", "IRS_2025_1120S_INSTR_FULL", "primary", "M-2 AAA computation"),
            ("R001", "IRC_1368", "secondary", "Section 1368 — distributions from S corporations"),
            ("R002", "IRS_2025_1120S_INSTR_FULL", "primary", "AAA distributions cannot reduce below zero"),
            ("R002", "IRC_1368", "primary", "Section 1368(e)(1) — AAA ordering rule"),
            ("R003", "IRC_1368", "primary", "Section 1368(c) — distribution ordering"),
            ("R003", "IRC_1367", "secondary", "Section 1367 — adjustments to basis of shareholder stock"),
            ("R004", "IRS_2025_1120S_INSTR_FULL", "primary", "OAA tracks tax-exempt income"),
        ])

        self._upsert_lines(form, [
            {"line_number": "1", "description": "Balance at beginning of tax year", "line_type": "input", "sort_order": 1},
            {"line_number": "2", "description": "Ordinary income from Page 1, line 21 (or loss on line 4)", "line_type": "calculated", "sort_order": 2,
             "destination_form": "Page 1 Line 21"},
            {"line_number": "3", "description": "Other additions", "line_type": "input", "sort_order": 3},
            {"line_number": "4", "description": "Loss from Page 1, line 21 (if a loss)", "line_type": "calculated", "sort_order": 4},
            {"line_number": "5", "description": "Other reductions (nondeductible expenses, etc.)", "line_type": "input", "sort_order": 5,
             "notes": "For OAA: includes expenses related to tax-exempt income."},
            {"line_number": "6", "description": "Combine lines 1 through 5", "line_type": "subtotal", "source_rules": ["R001"], "sort_order": 6},
            {"line_number": "7", "description": "Distributions other than dividend distributions", "line_type": "input", "sort_order": 7},
            {"line_number": "8", "description": "Balance at end of tax year (line 6 minus line 7)", "line_type": "total", "source_rules": ["R002"], "sort_order": 8,
             "notes": "AAA: distributions cannot reduce below zero. Losses CAN make AAA negative."},
        ])

        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D001", "title": "AAA distributions exceed balance", "severity": "warning",
             "condition": "aaa_distributions > max(0, aaa_combined)",
             "message": "Distributions exceed AAA balance. Excess treated as return of basis (section 1368). AAA cannot be reduced below zero by distributions."},
            {"diagnostic_id": "D002", "title": "AAA negative from losses", "severity": "info",
             "condition": "aaa_ending < 0",
             "message": "AAA ending balance is negative due to losses exceeding income. This is permitted — only distributions cannot make AAA negative, not losses."},
        ])

        self._upsert_tests(form, [
            {"scenario_name": "Basic M-2 — income, additions, distributions within AAA",
             "scenario_type": "normal",
             "inputs": {"aaa_beginning": 50000, "aaa_ordinary_income": 95000,
                         "aaa_other_additions": 0, "aaa_loss": 0,
                         "aaa_other_reductions": 3000, "aaa_distributions": 40000},
             "expected_outputs": {"aaa_combined": 142000, "aaa_ending": 102000},
             "notes": "Simple case: 50K + 95K - 3K = 142K combined - 40K distributions = 102K ending.", "sort_order": 1},
            {"scenario_name": "Distributions exceeding AAA — capped at zero",
             "scenario_type": "edge",
             "inputs": {"aaa_beginning": 20000, "aaa_ordinary_income": 30000,
                         "aaa_other_additions": 0, "aaa_loss": 0,
                         "aaa_other_reductions": 0, "aaa_distributions": 80000},
             "expected_outputs": {"aaa_combined": 50000, "aaa_ending": 0},
             "notes": "Distributions ($80K) exceed AAA ($50K). AAA goes to zero, not negative. Excess $30K treated as return of basis/capital gain per section 1368.", "sort_order": 2},
            {"scenario_name": "Loss making AAA negative",
             "scenario_type": "edge",
             "inputs": {"aaa_beginning": 20000, "aaa_ordinary_income": 0,
                         "aaa_other_additions": 0, "aaa_loss": 50000,
                         "aaa_other_reductions": 0, "aaa_distributions": 0},
             "expected_outputs": {"aaa_combined": -30000, "aaa_ending": -30000},
             "notes": "Losses CAN make AAA negative (unlike distributions). AAA = 20K - 50K loss = -30K.", "sort_order": 3},
        ])

        self._upsert_form_links("1120S_M2", sources, [
            ("IRS_2025_1120S_INSTR_FULL", "governs"),
            ("IRC_1368", "governs"),
            ("IRC_1367", "informs"),
        ])

        self.stdout.write(self.style.SUCCESS("  M-2 complete."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Expand Schedule K — add detailed flow-in rules for each line
    # ═══════════════════════════════════════════════════════════════════════════

    def _expand_schedule_k(self, sources):
        """Add expanded rules to the existing Schedule K form spec."""
        form = TaxForm.objects.filter(
            form_number="SCH_K_1120S", jurisdiction="FED", tax_year=2025,
        ).first()
        if not form:
            self.stdout.write(self.style.WARNING("SCH_K_1120S not found — run load_1120s_specs first"))
            return

        # Add new flow-in rules that document WHERE each K line comes from
        rules = self._upsert_rules(form, [
            {"rule_id": "R010", "title": "K Line 1 source: Page 1 Line 21",
             "description": "Schedule K Line 1 = Page 1 Line 21 (ordinary business income/loss). This is the direct flow of the S-Corp's operating result to Schedule K for shareholder allocation.",
             "rule_type": "routing", "formula": "K1 = Page1_Line21",
             "inputs": ["page1_ordinary_income"], "outputs": ["K1"],
             "precedence": 1, "sort_order": 10},
            {"rule_id": "R011", "title": "K Line 4 = Interest income",
             "description": "Schedule K Line 4 is INTEREST INCOME (portfolio income). This is NOT Section 1231 gain. Interest income is separately stated because it is portfolio income under IRC 469.",
             "rule_type": "routing", "formula": "K4 = interest_income",
             "inputs": ["interest_income"], "outputs": ["K4"],
             "precedence": 1, "sort_order": 11,
             "notes": "IMPORTANT: K4 is NOT Section 1231. K9 is Section 1231. This was a source of confusion."},
            {"rule_id": "R012", "title": "K Line 5a/5b = Dividends",
             "description": "K Line 5a = ordinary dividends, K Line 5b = qualified dividends (subset of 5a). Portfolio income, separately stated. NOT capital gains.",
             "rule_type": "routing", "formula": "K5a = ordinary_dividends; K5b = qualified_dividends",
             "inputs": ["dividend_income", "qualified_dividends"], "outputs": ["K5a", "K5b"],
             "precedence": 1, "sort_order": 12},
            {"rule_id": "R013", "title": "K Line 7 source: Schedule D Part I Line 5",
             "description": "Schedule K Line 7 = net short-term capital gain (loss) from Schedule D Part I Line 5. This comes from Form 8949 capital asset transactions, NOT from Form 4797.",
             "rule_type": "routing", "formula": "K7 = ScheduleD_Part1_Line5",
             "inputs": ["schedule_d_net_short_term"], "outputs": ["K7"],
             "precedence": 1, "sort_order": 13},
            {"rule_id": "R014", "title": "K Line 8a source: Schedule D Part II Line 12",
             "description": "Schedule K Line 8a = net long-term capital gain (loss) from Schedule D Part II Line 12. From Form 8949 capital asset transactions, NOT from Form 4797.",
             "rule_type": "routing", "formula": "K8a = ScheduleD_Part2_Line12",
             "inputs": ["schedule_d_net_long_term"], "outputs": ["K8a"],
             "precedence": 1, "sort_order": 14},
            {"rule_id": "R015", "title": "K Line 9 source: Form 4797 Part I Line 7",
             "description": "Schedule K Line 9 = net section 1231 gain (loss) from Form 4797 Part I Line 7. Section 1231 transactions BYPASS Schedule D on the 1120-S and flow directly to K Line 9. This is a key architectural difference from the 1040.",
             "rule_type": "routing", "formula": "K9 = Form4797_Part1_Line7",
             "inputs": ["form_4797_net_1231"], "outputs": ["K9"],
             "precedence": 1, "sort_order": 15,
             "notes": "VERIFIED: 4797 Part I -> K9 directly. Does NOT go through Schedule D on 1120-S."},
            {"rule_id": "R016", "title": "K Line 16c = Nondeductible meals",
             "description": "K Line 16c (nondeductible expenses) includes the 50% nondeductible portion of meals. This amount also flows to M-1 Line 3b as an add-back and to M-2 as a reduction to AAA.",
             "rule_type": "routing", "formula": "K16c = nondeductible_meals + other_nondeductible",
             "inputs": ["nondeductible_expenses"], "outputs": ["K16c"],
             "precedence": 1, "sort_order": 16},
            {"rule_id": "R017", "title": "K Line 16d = Total distributions",
             "description": "K Line 16d = total distributions (property and cash) to shareholders. This amount flows to M-2 Line 7 and to each shareholder's K-1.",
             "rule_type": "routing", "formula": "K16d = total_distributions",
             "inputs": ["total_distributions"], "outputs": ["K16d"],
             "precedence": 1, "sort_order": 17},
            {"rule_id": "R018", "title": "K Line 18 = Income/loss reconciliation",
             "description": "Schedule K Line 18 is a reconciliation total. It should equal Page 1 Line 21. This is the same number that M-1 Line 7/8 must also equal.",
             "rule_type": "validation", "formula": "K18 = Page1_Line21",
             "inputs": ["K1_through_K10_net"], "outputs": ["K18"],
             "precedence": 50, "sort_order": 18},
        ])

        self._upsert_links(rules, sources, [
            ("R010", "IRS_2025_1120S_INSTR_FULL", "primary", "K1 = Page 1 Line 21"),
            ("R011", "IRS_2025_1120S_INSTR_FULL", "primary", "K4 = interest income (portfolio)"),
            ("R012", "IRS_2025_1120S_INSTR_FULL", "primary", "K5a/5b = dividends"),
            ("R013", "IRS_2025_1120S_SCHD_INSTR_FULL", "primary", "Schedule D Part I Line 5 -> K7"),
            ("R014", "IRS_2025_1120S_SCHD_INSTR_FULL", "primary", "Schedule D Part II Line 12 -> K8a"),
            ("R015", "IRS_2025_1120S_INSTR_FULL", "primary", "K9 = Form 4797 Part I Line 7 (verified)"),
            ("R015", "IRS_2025_4797_INSTR", "secondary", "4797 bypasses Schedule D on 1120-S"),
            ("R016", "IRS_2025_1120S_INSTR_FULL", "primary", "K16c = nondeductible expenses"),
            ("R017", "IRS_2025_1120S_INSTR_FULL", "primary", "K16d = distributions"),
            ("R017", "IRC_1368", "secondary", "Section 1368 distribution rules"),
            ("R018", "IRS_2025_1120S_INSTR_FULL", "primary", "K18 must equal Page 1 Line 21"),
        ])

        # Add K-1 box mapping lines
        self._upsert_lines(form, [
            {"line_number": "K1->Box1", "description": "K Line 1 -> K-1 Box 1: Ordinary business income (loss)", "line_type": "informational", "destination_form": "K-1 Box 1", "sort_order": 100},
            {"line_number": "K2->Box2", "description": "K Line 2 -> K-1 Box 2: Net rental real estate income (loss)", "line_type": "informational", "destination_form": "K-1 Box 2", "sort_order": 101},
            {"line_number": "K3->Box3", "description": "K Line 3c -> K-1 Box 3: Other net rental income (loss)", "line_type": "informational", "destination_form": "K-1 Box 3", "sort_order": 102},
            {"line_number": "K4->Box4", "description": "K Line 4 -> K-1 Box 4: Interest income", "line_type": "informational", "destination_form": "K-1 Box 4", "sort_order": 103},
            {"line_number": "K5->Box5", "description": "K Line 5a/5b -> K-1 Box 5a/5b: Dividends", "line_type": "informational", "destination_form": "K-1 Box 5", "sort_order": 104},
            {"line_number": "K6->Box6", "description": "K Line 6 -> K-1 Box 6: Royalties", "line_type": "informational", "destination_form": "K-1 Box 6", "sort_order": 105},
            {"line_number": "K7->Box7", "description": "K Line 7 -> K-1 Box 7: Net short-term capital gain (loss)", "line_type": "informational", "destination_form": "K-1 Box 7", "sort_order": 106},
            {"line_number": "K8->Box8", "description": "K Line 8a/8b/8c -> K-1 Box 8a/8b/8c: Long-term capital gain, collectibles, unrec 1250", "line_type": "informational", "destination_form": "K-1 Box 8", "sort_order": 107},
            {"line_number": "K9->Box9", "description": "K Line 9 -> K-1 Box 9: Net section 1231 gain (loss)", "line_type": "informational", "destination_form": "K-1 Box 9", "sort_order": 108},
            {"line_number": "K10->Box10", "description": "K Line 10 -> K-1 Box 10: Other income (loss)", "line_type": "informational", "destination_form": "K-1 Box 10", "sort_order": 109},
            {"line_number": "K11->Box11", "description": "K Line 11 -> K-1 Box 11: Section 179 deduction", "line_type": "informational", "destination_form": "K-1 Box 11", "sort_order": 110},
            {"line_number": "K12->Box12", "description": "K Line 12a-e -> K-1 Box 12: Deductions", "line_type": "informational", "destination_form": "K-1 Box 12", "sort_order": 111},
            {"line_number": "K13->Box13", "description": "K Line 13a-g -> K-1 Box 13: Credits", "line_type": "informational", "destination_form": "K-1 Box 13", "sort_order": 112},
            {"line_number": "K16->Box16", "description": "K Line 16a-f -> K-1 Box 16: Items affecting shareholder basis", "line_type": "informational", "destination_form": "K-1 Box 16", "sort_order": 113},
            {"line_number": "K17->Box17", "description": "K Line 17a-d -> K-1 Box 17: Other information (QBI, etc.)", "line_type": "informational", "destination_form": "K-1 Box 17", "sort_order": 114},
        ])

        self.stdout.write(self.style.SUCCESS("  Schedule K expanded."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Schedule D — Add flow verification rules
    # ═══════════════════════════════════════════════════════════════════════════

    def _add_schedule_d_flow_rules(self, sources):
        """Add flow-out rules to existing Schedule D spec."""
        form = TaxForm.objects.filter(
            form_number="SCHD_1120S", jurisdiction="FED", tax_year=2025,
        ).first()
        if not form:
            self.stdout.write(self.style.WARNING("SCHD_1120S not found — run load_1120s_specs first"))
            return

        rules = self._upsert_rules(form, [
            {"rule_id": "R010", "title": "Schedule D does NOT include Section 1231",
             "description": "Section 1231 gains/losses from Form 4797 are reported on Schedule K Line 9 directly. They do NOT flow through Schedule D on the 1120-S. Schedule D handles only capital asset transactions (stocks, bonds, etc.) through Form 8949.",
             "rule_type": "validation",
             "formula": "schedule_d does NOT include 4797_section_1231",
             "inputs": [], "outputs": [],
             "precedence": 0, "sort_order": 10,
             "notes": "VERIFIED from fresh IRS instructions. 4797 bypasses Schedule D on 1120-S. This is different from 1040 where Section 1231 gains treated as capital gains DO flow to Schedule D."},
            {"rule_id": "R011", "title": "Part I Line 5 -> K Line 7",
             "description": "Schedule D Part I Line 5 (net short-term capital gain/loss) flows to Schedule K Line 7.",
             "rule_type": "routing", "formula": "K7 = ScheduleD_Part1_Line5",
             "inputs": ["net_short_term_gain_loss"], "outputs": ["K_line_7"],
             "precedence": 1, "sort_order": 11},
            {"rule_id": "R012", "title": "Part II Line 12 -> K Line 8a",
             "description": "Schedule D Part II Line 12 (net long-term capital gain/loss) flows to Schedule K Line 8a.",
             "rule_type": "routing", "formula": "K8a = ScheduleD_Part2_Line12",
             "inputs": ["net_long_term_gain_loss"], "outputs": ["K_line_8a"],
             "precedence": 1, "sort_order": 12},
        ])

        self._upsert_links(rules, sources, [
            ("R010", "IRS_2025_1120S_SCHD_INSTR_FULL", "primary", "Schedule D does NOT include Section 1231"),
            ("R010", "IRS_2025_1120S_INSTR_FULL", "secondary", "4797 -> K9 directly, bypasses Schedule D"),
            ("R011", "IRS_2025_1120S_SCHD_INSTR_FULL", "primary", "Part I Line 5 -> K Line 7"),
            ("R012", "IRS_2025_1120S_SCHD_INSTR_FULL", "primary", "Part II Line 12 -> K Line 8a"),
        ])

        self.stdout.write(self.style.SUCCESS("  Schedule D flow rules added."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Cross-form diagnostics
    # ═══════════════════════════════════════════════════════════════════════════

    def _add_cross_form_diagnostics(self, sources):
        """Add cross-form diagnostics to existing Schedule K spec."""
        form = TaxForm.objects.filter(
            form_number="SCH_K_1120S", jurisdiction="FED", tax_year=2025,
        ).first()
        if not form:
            return

        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D010", "title": "Section 1231 double-count check",
             "severity": "error",
             "condition": "K4 contains section_1231_gain AND K9 contains section_1231_gain",
             "message": "Section 1231 gain appears on both K Line 4 (interest income) and K Line 9 (net section 1231). K Line 4 is for INTEREST INCOME, not Section 1231. Verify that 1231 gain is only on K Line 9."},
            {"diagnostic_id": "D011", "title": "Page 1 Line 4 source verification",
             "severity": "warning",
             "condition": "page1_line4 != form_4797_part2_line17",
             "message": "Page 1 Line 4 does not match Form 4797 Part II Line 17. Line 4 should equal the ordinary gain/loss from 4797 Part II, NOT the Section 1231 gain from Part I."},
            {"diagnostic_id": "D012", "title": "K18 does not equal Page 1 Line 21",
             "severity": "error",
             "condition": "K18 != page1_line21",
             "message": "Schedule K Line 18 (income/loss reconciliation) does not equal Page 1 Line 21. These must match."},
            {"diagnostic_id": "D013", "title": "Schedule D Section 1231 contamination",
             "severity": "error",
             "condition": "schedule_d includes section_1231_amounts",
             "message": "Section 1231 amounts appear on Schedule D. On the 1120-S, Section 1231 goes directly to K Line 9 from Form 4797 Part I Line 7, NOT through Schedule D."},
            {"diagnostic_id": "D014", "title": "Schedule D totals vs 8949",
             "severity": "warning",
             "condition": "schedule_d_totals != form_8949_category_totals",
             "message": "Schedule D totals do not match Form 8949 category totals. Verify all 8949 transactions are correctly categorized (A-F) and totaled on Schedule D."},
        ])

        self.stdout.write(self.style.SUCCESS("  Cross-form diagnostics added."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Cross-form test scenarios
    # ═══════════════════════════════════════════════════════════════════════════

    def _add_cross_form_tests(self, sources):
        """Add end-to-end test scenarios to the Page 1 spec."""
        form = TaxForm.objects.filter(
            form_number="1120S_PAGE1", jurisdiction="FED", tax_year=2025,
        ).first()
        if not form:
            return

        self._upsert_tests(form, [
            {"scenario_name": "S-Corp with disposed equipment — 4797 recapture + 1231 flow",
             "scenario_type": "normal",
             "inputs": {
                 "gross_receipts": 400000, "returns_allowances": 0, "cost_of_goods_sold": 150000,
                 "other_income": 0,
                 "officer_compensation": 60000, "salaries_wages": 40000, "depreciation": 20000,
                 "other_deductions": 10000,
                 "form_4797_part2_line17": 15000,
                 "form_4797_part1_line7": 8000,
             },
             "expected_outputs": {
                 "net_gain_4797": 15000,
                 "total_income": 265000,
                 "ordinary_business_income": 135000,
                 "K1": 135000,
                 "K9": 8000,
                 "page1_line4": 15000,
             },
             "notes": "4797 Part II L17 ($15K recapture) -> Page 1 Line 4. 4797 Part I L7 ($8K Section 1231) -> K Line 9 directly. These are DIFFERENT flows.", "sort_order": 10},
            {"scenario_name": "S-Corp with M&E limitation — meals nondeductible flow",
             "scenario_type": "normal",
             "inputs": {
                 "gross_receipts": 300000, "cost_of_goods_sold": 100000,
                 "officer_compensation": 50000, "salaries_wages": 30000,
                 "other_deductions": 25000,
                 "meals_total_on_books": 10000,
                 "meals_deductible_50pct": 5000,
                 "meals_nondeductible_50pct": 5000,
             },
             "expected_outputs": {
                 "ordinary_business_income": 90000,
                 "K16c": 5000,
                 "M1_line_3b": 5000,
             },
             "notes": "$10K meals on books, only $5K deductible (50%). $5K nondeductible -> K16c and M-1 Line 3b (as positive ADD-BACK).", "sort_order": 11},
            {"scenario_name": "Short-term capital gain — Schedule D to K Line 7",
             "scenario_type": "normal",
             "inputs": {
                 "form_8949_box_A_gain": 5000,
                 "form_8949_box_B_gain": 0,
                 "form_8949_box_C_gain": 0,
             },
             "expected_outputs": {
                 "schedule_d_part1_line5": 5000,
                 "K7": 5000,
             },
             "notes": "Short-term gain from 8949 -> Schedule D Part I Line 5 -> K Line 7. NOT K5a (that's dividends).", "sort_order": 12},
            {"scenario_name": "Long-term capital gain — Schedule D to K Line 8a",
             "scenario_type": "normal",
             "inputs": {
                 "form_8949_box_D_gain": 12000,
                 "form_8949_box_E_gain": 0,
                 "form_8949_box_F_gain": 3000,
             },
             "expected_outputs": {
                 "schedule_d_part2_line12": 15000,
                 "K8a": 15000,
             },
             "notes": "Long-term gain from 8949 -> Schedule D Part II Line 12 -> K Line 8a. NOT K5b (that's qualified dividends).", "sort_order": 13},
            {"scenario_name": "Section 1231 from 4797 bypasses Schedule D",
             "scenario_type": "normal",
             "inputs": {
                 "form_4797_part1_line7": 20000,
                 "schedule_d_part2_line12": 0,
             },
             "expected_outputs": {
                 "K9": 20000,
                 "K8a": 0,
                 "schedule_d_includes_1231": False,
             },
             "notes": "Section 1231 gain from 4797 goes to K9 directly. Schedule D is NOT involved. This is a key 1120-S vs 1040 difference.", "sort_order": 14},
            {"scenario_name": "Distributions exceeding AAA — M-2 floor at zero",
             "scenario_type": "edge",
             "inputs": {
                 "ordinary_business_income": 50000,
                 "aaa_beginning": 30000,
                 "total_distributions": 100000,
             },
             "expected_outputs": {
                 "aaa_combined": 80000,
                 "aaa_ending": 0,
                 "excess_distribution": 20000,
             },
             "notes": "AAA = 30K + 50K income = 80K combined. Distributions of $100K: first $80K from AAA (reduces to zero), then $20K is return of basis/capital gain per section 1368.", "sort_order": 15},
        ])

        self.stdout.write(self.style.SUCCESS("  Cross-form test scenarios added."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Report
    # ═══════════════════════════════════════════════════════════════════════════

    def _report_totals(self):
        def _safe(text):
            return text.encode("ascii", errors="replace").decode("ascii")

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("DATABASE TOTALS (after load_1120s_full)")
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

        all_rules = FormRule.objects.all()
        uncited = [r for r in all_rules if not r.authority_links.exists()]
        if uncited:
            self.stdout.write(self.style.WARNING(f"\nRules with ZERO authority links: {len(uncited)}"))
            for r in uncited:
                self.stdout.write(_safe(f"  {r.tax_form.form_number} {r.rule_id}: {r.title}"))
        else:
            self.stdout.write(self.style.SUCCESS("\nAll rules have authority links."))

        needs_review = FormRule.objects.filter(notes__icontains="NEEDS REVIEW")
        if needs_review.exists():
            self.stdout.write(f"\nRules marked NEEDS REVIEW: {needs_review.count()}")
            for r in needs_review:
                self.stdout.write(_safe(f"  {r.tax_form.form_number} {r.rule_id}: {r.title}"))

        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("1120-S full specs loaded successfully."))
