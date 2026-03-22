"""Load remaining 1120-S forms to complete S-Corp spec coverage.

Session 11: Adds the missing 9 forms/schedules:
  - Schedule B (Other Information — Pages 3-4 of 1120-S)
  - Schedule L (Balance Sheet per Books)
  - Form 8995 (QBI Deduction — Simplified)
  - Form 8995-A (QBI Deduction — Full Computation)
  - Form 8582 (Passive Activity Loss Limitations)
  - Form 6198 (At-Risk Limitations)
  - Form 3800 (General Business Credit)
  - Schedule M-3 (Net Income Reconciliation for Large Filers)
  - Form 8283 (Noncash Charitable Contributions)

Existing authority sources are referenced by source_code.
New instruction sources created for Schedule B, L, M-3, and 8283.
Idempotent: uses update_or_create throughout.
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
# New authority sources (detailed instruction excerpts for forms not yet
# covered by existing instruction sources)
# ═══════════════════════════════════════════════════════════════════════════

FRESH_SOURCES = [
    {
        "source_code": "IRS_2025_1120S_SCHB_INSTR",
        "source_type": "official_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "Instructions for Form 1120-S Schedule B — Other Information (2025)",
        "citation": "Form 1120-S Instructions — Schedule B (2025)",
        "issuer": "IRS",
        "current_status": "active",
        "is_substantive_authority": True,
        "requires_human_review": True,
        "trust_score": 9.0,
        "topics": ["1120s", "schedule_b"],
        "excerpts": [
            {
                "excerpt_label": "Schedule B — overview and question list",
                "excerpt_text": (
                    "Schedule B (Form 1120-S) consists of approximately 20 yes/no questions "
                    "on pages 3-4 of the 1120-S. These are informational questions about the "
                    "entity's tax situation including: B1 — accounting method (cash, accrual, other); "
                    "B3 — number of shareholders at end of tax year; B5 — controlled group membership; "
                    "B7 — foreign corporation shareholder status; B8 — cancelled/forgiven debt; "
                    "B9 — section 263A UNICAP applicability; B10 — 1099 filing compliance; "
                    "B11 — outstanding AE&P from C-Corp years; B12 — built-in gains tax (section 1374); "
                    "B14 — total receipts test for Schedule M-3 (>$50M total assets)."
                ),
                "summary_text": "Schedule B: ~20 yes/no informational questions about entity tax situation on pages 3-4.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule B — M-3 threshold and accounting method",
                "excerpt_text": (
                    "If total assets at end of tax year are $50 million or more, the corporation "
                    "must file Schedule M-3 (Form 1120-S) instead of Schedule M-1. The accounting "
                    "method reported on Schedule B line 1 must be consistent with the method used "
                    "throughout the return. If the entity changed its accounting method during the "
                    "year, Form 3115 must be filed."
                ),
                "summary_text": "M-3 required if total assets >= $50M. Accounting method must be consistent.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_1120S_SCHL_INSTR",
        "source_type": "official_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "Instructions for Form 1120-S Schedule L — Balance Sheet per Books (2025)",
        "citation": "Form 1120-S Instructions — Schedule L (2025)",
        "issuer": "IRS",
        "current_status": "active",
        "is_substantive_authority": True,
        "requires_human_review": True,
        "trust_score": 9.0,
        "topics": ["1120s", "balance_sheet"],
        "excerpts": [
            {
                "excerpt_label": "Schedule L — structure and line descriptions",
                "excerpt_text": (
                    "Schedule L reports the balance sheet per books with beginning-of-year (BOY) "
                    "and end-of-year (EOY) columns. Assets (Lines 1-15): Cash (L1), Trade notes & "
                    "accounts receivable net of allowance (L2a/2b), Inventories (L3), Tax-exempt "
                    "securities (L5), Other investments (L6), Buildings & depreciable assets net (L7), "
                    "Intangible assets net (L8), Land (L9), Other assets (L10a/10b), Total assets (L14). "
                    "Liabilities (Lines 15-21): Accounts payable (L15), Mortgages <1yr (L16), Other "
                    "current liabilities (L17), Shareholder loans (L18), Mortgages >=1yr (L19), Other "
                    "liabilities (L20), Total liabilities (L21). Equity (Lines 22-27): Capital stock "
                    "(L22), Additional paid-in capital (L23), Retained earnings (L24), Adjustments to "
                    "shareholders' equity (L25), Less treasury stock (L26), Total L&SE (L27)."
                ),
                "summary_text": "Schedule L: BOY/EOY balance sheet. Assets L1-14, Liabilities L15-21, Equity L22-27.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule L — small corporation exception and cross-checks",
                "excerpt_text": (
                    "Schedule L is not required if: (a) total receipts for the tax year are less "
                    "than $250,000, AND (b) total assets at end of tax year are less than $250,000. "
                    "However, the corporation must still answer the Schedule B question about total "
                    "assets. Line 24 (retained earnings) EOY should tie to Schedule M-2 ending "
                    "balance. Line 7 (depreciable assets) should be consistent with the "
                    "depreciation module. Line 27 (total L&SE) must equal Line 14 (total assets) "
                    "for both BOY and EOY columns."
                ),
                "summary_text": "Small corp exception: receipts <$250K AND assets <$250K. L24 ties to M-2. L27 = L14.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_1120S_M3_INSTR",
        "source_type": "official_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "Instructions for Schedule M-3 (Form 1120-S) — Net Income Reconciliation (2025)",
        "citation": "Schedule M-3 (Form 1120-S) Instructions (2025)",
        "issuer": "IRS",
        "current_status": "active",
        "is_substantive_authority": True,
        "requires_human_review": True,
        "trust_score": 9.0,
        "topics": ["1120s", "book_tax_reconciliation"],
        "excerpts": [
            {
                "excerpt_label": "Schedule M-3 — filing threshold and structure",
                "excerpt_text": (
                    "Schedule M-3 (Form 1120-S) is required instead of Schedule M-1 when the "
                    "corporation's total assets at the end of the tax year are $50 million or more. "
                    "Part I reconciles financial statement net income to net income per income tax "
                    "return. Part II details income/loss items showing book amount, temporary "
                    "differences, permanent differences, and income/loss per tax return. Part III "
                    "details expense/deduction items with the same columns. Corporations with total "
                    "assets less than $50 million may voluntarily file Schedule M-3."
                ),
                "summary_text": "M-3 required if assets >= $50M. Parts I-III: financial statement to tax return reconciliation.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_8283_INSTR",
        "source_type": "official_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "Instructions for Form 8283 — Noncash Charitable Contributions (2025)",
        "citation": "Form 8283 Instructions (2025)",
        "issuer": "IRS",
        "current_status": "active",
        "is_substantive_authority": True,
        "requires_human_review": True,
        "trust_score": 9.0,
        "topics": ["charitable_contributions", "noncash_contributions"],
        "excerpts": [
            {
                "excerpt_label": "Form 8283 — filing requirement and sections",
                "excerpt_text": (
                    "Form 8283 is required when the total deduction claimed for all noncash "
                    "charitable contributions exceeds $500. Section A covers items (or groups of "
                    "similar items) for which the deduction is $5,000 or less — requires description, "
                    "date of contribution, date acquired, donor's cost or basis, FMV, and method of "
                    "determining FMV. Section B covers items for which the deduction is more than "
                    "$5,000 (except publicly traded securities) — requires a qualified appraisal by "
                    "a qualified appraiser. Publicly traded securities use FMV on date of "
                    "contribution regardless of amount and do not require an appraisal."
                ),
                "summary_text": "Required if noncash contributions > $500. Section A: <= $5K. Section B: > $5K (appraisal required).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Form 8283 — S-Corp passthrough and special rules",
                "excerpt_text": (
                    "For S corporations, the charitable contribution deduction is not taken at the "
                    "entity level — it passes through to shareholders on Schedule K-1 Box 12a. The "
                    "S corporation must still file Form 8283 if total noncash contributions exceed "
                    "$500. Special rules apply for vehicles (Form 1098-C required), art valued over "
                    "$20,000 (attach appraisal), and intellectual property (basis limitation applies "
                    "in year of contribution, additional deductions in later years based on income)."
                ),
                "summary_text": "S-Corp: contributions pass through to K-1 Box 12a. Entity still files 8283 if > $500.",
                "is_key_excerpt": True,
            },
        ],
    },
]

# Sources already in the database — referenced by source_code
EXISTING_SOURCES = [
    "IRS_2025_1120S_INSTR", "IRS_2025_1120S_INSTR_FULL",
    "IRS_2025_8995_INSTR", "IRS_2025_8995A_INSTR",
    "IRS_2025_8582_INSTR", "IRS_2025_6198_INSTR", "IRS_2025_3800_INSTR",
    "IRC_199A", "IRC_469", "IRC_465", "IRC_38", "IRC_170",
    "IRC_1361", "IRC_1363", "IRC_1366", "IRC_1367", "IRC_1374",
]


class Command(BaseCommand):
    help = "Load remaining 1120-S forms to complete S-Corp spec coverage (Session 11)"

    def handle(self, *_args, **_options):
        with transaction.atomic():
            sources = self._load_sources()
            self._load_schedule_b(sources)
            self._load_schedule_l(sources)
            self._load_8995(sources)
            self._load_8995a(sources)
            self._load_8582(sources)
            self._load_6198(sources)
            self._load_3800(sources)
            self._load_m3(sources)
            self._load_8283(sources)
        self._report_totals()

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

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers
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
    # Schedule B — Other Information (Pages 3-4 of 1120-S)
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_schedule_b(self, sources):
        form = self._upsert_form(
            "1120S_SCHB", "Schedule B (Form 1120-S) — Other Information",
            ["1120S"],
            notes="Pages 3-4 of 1120-S. ~20 yes/no informational questions about entity tax situation.",
        )
        self._upsert_facts(form, [
            {"fact_key": "b1_accounting_method", "label": "B1 — Accounting method", "data_type": "choice",
             "choices": ["cash", "accrual", "other"], "required": True, "sort_order": 1},
            {"fact_key": "b2_business_activity_code", "label": "B2 — Business activity code", "data_type": "string", "sort_order": 2},
            {"fact_key": "b3_shareholder_count", "label": "B3 — Number of shareholders at end of tax year", "data_type": "integer", "required": True, "sort_order": 3},
            {"fact_key": "b4_shareholder_count_mid_year", "label": "B4 — Number of shareholders during any part of the year", "data_type": "integer", "sort_order": 4},
            {"fact_key": "b5_controlled_group", "label": "B5 — Was the corporation a member of a controlled group?", "data_type": "boolean", "sort_order": 5},
            {"fact_key": "b6_owned_50pct_entity", "label": "B6 — Does the corporation own 50%+ of another entity?", "data_type": "boolean", "sort_order": 6},
            {"fact_key": "b7_foreign_corp_shareholder", "label": "B7 — Shareholder in a foreign corporation?", "data_type": "boolean", "sort_order": 7},
            {"fact_key": "b8_cancelled_debt", "label": "B8 — Any debt cancelled, forgiven, or modified?", "data_type": "boolean", "sort_order": 8},
            {"fact_key": "b9_section_263a", "label": "B9 — Section 263A UNICAP applies?", "data_type": "boolean", "sort_order": 9},
            {"fact_key": "b10_filed_all_1099s", "label": "B10 — Did the corporation file all required 1099s?", "data_type": "boolean", "sort_order": 10},
            {"fact_key": "b11_aep_from_ccorp", "label": "B11 — Outstanding AE&P from C-Corp years?", "data_type": "boolean", "sort_order": 11},
            {"fact_key": "b12_built_in_gains", "label": "B12 — Built-in gains tax (Section 1374) applies?", "data_type": "boolean", "sort_order": 12},
            {"fact_key": "b13_tax_exempt_interest", "label": "B13 — Tax-exempt interest or other tax-exempt income?", "data_type": "boolean", "sort_order": 13},
            {"fact_key": "b14_total_assets_50m", "label": "B14 — Total assets >= $50M (M-3 required)?", "data_type": "boolean", "sort_order": 14},
            {"fact_key": "b15_issued_publicly_traded", "label": "B15 — Corporation's stock publicly traded?", "data_type": "boolean", "sort_order": 15},
            {"fact_key": "b16_election_year", "label": "B16 — First year of S election?", "data_type": "boolean", "sort_order": 16},
            {"fact_key": "b17_short_year", "label": "B17 — Short tax year?", "data_type": "boolean", "sort_order": 17},
            {"fact_key": "b18_excess_net_passive_income", "label": "B18 — Section 1375 tax on excess net passive income?", "data_type": "boolean", "sort_order": 18},
            {"fact_key": "b19_tax_shelter", "label": "B19 — Tax shelter registration?", "data_type": "boolean", "sort_order": 19},
            {"fact_key": "b20_foreign_accounts", "label": "B20 — Foreign financial accounts (FBAR)?", "data_type": "boolean", "sort_order": 20},
            {"fact_key": "actual_shareholder_count", "label": "Actual number of shareholders entered in return", "data_type": "integer", "sort_order": 21,
             "notes": "Cross-check against B3."},
            {"fact_key": "total_assets_eoy", "label": "Total assets at end of year (from Schedule L)", "data_type": "decimal", "sort_order": 22,
             "notes": "Cross-check for M-3 threshold."},
        ])

        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "Accounting method consistency", "rule_type": "validation",
             "formula": "b1_accounting_method must match method used on Page 1",
             "inputs": ["b1_accounting_method"], "outputs": [], "precedence": 1, "sort_order": 1,
             "description": "Accounting method on Schedule B must be consistent with the method used throughout the return."},
            {"rule_id": "R002", "title": "Shareholder count cross-check", "rule_type": "validation",
             "formula": "b3_shareholder_count == actual_shareholder_count",
             "inputs": ["b3_shareholder_count", "actual_shareholder_count"], "outputs": [], "precedence": 2, "sort_order": 2,
             "description": "B3 shareholder count should match the actual number of K-1s prepared."},
            {"rule_id": "R003", "title": "M-3 filing threshold", "rule_type": "conditional",
             "formula": "if total_assets_eoy >= 50000000 then must_file_m3 = True",
             "inputs": ["total_assets_eoy", "b14_total_assets_50m"], "outputs": ["must_file_m3"], "precedence": 3, "sort_order": 3,
             "description": "If total assets >= $50M, must file Schedule M-3 instead of M-1."},
            {"rule_id": "R004", "title": "Section 1375 passive income tax trigger", "rule_type": "conditional",
             "formula": "if b11_aep_from_ccorp AND excess_net_passive_income then section_1375_tax_applies",
             "inputs": ["b11_aep_from_ccorp", "b18_excess_net_passive_income"], "outputs": [], "precedence": 4, "sort_order": 4,
             "description": "Section 1375 tax applies when S-Corp has AE&P from C-Corp years AND excess net passive income."},
            {"rule_id": "R005", "title": "100-shareholder limit check", "rule_type": "validation",
             "formula": "b3_shareholder_count <= 100",
             "inputs": ["b3_shareholder_count"], "outputs": [], "precedence": 5, "sort_order": 5,
             "description": "S corporations cannot have more than 100 shareholders (family members may elect to be treated as one)."},
        ])
        self._upsert_links(rules, sources, [
            ("R001", "IRS_2025_1120S_SCHB_INSTR", "primary", "Accounting method consistency requirement"),
            ("R002", "IRS_2025_1120S_SCHB_INSTR", "primary", "B3 shareholder count must match K-1s"),
            ("R003", "IRS_2025_1120S_SCHB_INSTR", "primary", "M-3 threshold: $50M total assets"),
            ("R004", "IRC_1374", "primary", "Section 1375 tax on excess net passive income with AE&P"),
            ("R004", "IRS_2025_1120S_INSTR_FULL", "secondary", "B11/B18 cross-reference"),
            ("R005", "IRC_1361", "primary", "100-shareholder limit for S-Corp eligibility"),
        ])
        self._upsert_lines(form, [
            {"line_number": "B1", "description": "Accounting method (cash, accrual, other)", "line_type": "input", "sort_order": 1},
            {"line_number": "B2", "description": "Business activity code", "line_type": "input", "sort_order": 2},
            {"line_number": "B3", "description": "Number of shareholders at end of tax year", "line_type": "input", "sort_order": 3},
            {"line_number": "B4", "description": "Number of shareholders during any part of the year", "line_type": "input", "sort_order": 4},
            {"line_number": "B5", "description": "Member of a controlled group?", "line_type": "input", "sort_order": 5},
            {"line_number": "B6", "description": "Own 50%+ of another entity?", "line_type": "input", "sort_order": 6},
            {"line_number": "B7", "description": "Shareholder in a foreign corporation?", "line_type": "input", "sort_order": 7},
            {"line_number": "B8", "description": "Debt cancelled, forgiven, or modified?", "line_type": "input", "sort_order": 8},
            {"line_number": "B9", "description": "Section 263A UNICAP applies?", "line_type": "input", "sort_order": 9},
            {"line_number": "B10", "description": "Filed all required 1099s?", "line_type": "input", "sort_order": 10},
            {"line_number": "B11", "description": "Outstanding AE&P from C-Corp years?", "line_type": "input", "sort_order": 11},
            {"line_number": "B12", "description": "Built-in gains tax applies?", "line_type": "input", "sort_order": 12},
            {"line_number": "B13", "description": "Tax-exempt interest or income?", "line_type": "input", "sort_order": 13},
            {"line_number": "B14", "description": "Total assets >= $50M?", "line_type": "input", "sort_order": 14},
            {"line_number": "B15", "description": "Stock publicly traded?", "line_type": "input", "sort_order": 15},
            {"line_number": "B16", "description": "First year of S election?", "line_type": "input", "sort_order": 16},
            {"line_number": "B17", "description": "Short tax year?", "line_type": "input", "sort_order": 17},
            {"line_number": "B18", "description": "Section 1375 tax on excess net passive income?", "line_type": "input", "sort_order": 18},
            {"line_number": "B19", "description": "Tax shelter registration?", "line_type": "input", "sort_order": 19},
            {"line_number": "B20", "description": "Foreign financial accounts (FBAR)?", "line_type": "input", "sort_order": 20},
        ])
        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D001", "title": "AE&P without tracking", "severity": "warning",
             "condition": "b11_aep_from_ccorp == True AND no_aep_tracking_module",
             "message": "B11 indicates AE&P from C-Corp years but no AE&P tracking is set up."},
            {"diagnostic_id": "D002", "title": "Built-in gains without computation", "severity": "warning",
             "condition": "b12_built_in_gains == True AND no_section_1374_computation",
             "message": "B12 indicates built-in gains tax applies but no Section 1374 computation found."},
            {"diagnostic_id": "D003", "title": "1099 non-compliance", "severity": "warning",
             "condition": "b10_filed_all_1099s == False",
             "message": "B10 answered NO — corporation did not file all required 1099s. Compliance risk."},
            {"diagnostic_id": "D004", "title": "Shareholder count mismatch", "severity": "error",
             "condition": "b3_shareholder_count != actual_shareholder_count",
             "message": "B3 shareholder count does not match the actual number of shareholders entered."},
        ])
        self._upsert_tests(form, [
            {"scenario_name": "Standard S-Corp — all standard answers", "scenario_type": "normal",
             "inputs": {"b1_accounting_method": "cash", "b3_shareholder_count": 2, "b5_controlled_group": False,
                        "b10_filed_all_1099s": True, "b11_aep_from_ccorp": False, "b12_built_in_gains": False,
                        "b14_total_assets_50m": False, "actual_shareholder_count": 2},
             "expected_outputs": {"must_file_m3": False, "shareholder_count_matches": True}, "sort_order": 1},
            {"scenario_name": "C-Corp conversion scenario", "scenario_type": "edge",
             "inputs": {"b1_accounting_method": "accrual", "b3_shareholder_count": 1, "b11_aep_from_ccorp": True,
                        "b12_built_in_gains": True, "b16_election_year": True, "b14_total_assets_50m": False,
                        "actual_shareholder_count": 1},
             "expected_outputs": {"must_file_m3": False, "aep_tracking_required": True, "big_tax_applies": True}, "sort_order": 2},
            {"scenario_name": "Large entity — M-3 required", "scenario_type": "edge",
             "inputs": {"b3_shareholder_count": 50, "b14_total_assets_50m": True, "total_assets_eoy": 75000000,
                        "actual_shareholder_count": 50},
             "expected_outputs": {"must_file_m3": True}, "sort_order": 3},
        ])
        self._upsert_form_links("1120S_SCHB", sources, [
            ("IRS_2025_1120S_SCHB_INSTR", "governs"),
            ("IRS_2025_1120S_INSTR", "informs"),
        ])
        self.stdout.write(self.style.SUCCESS("  Schedule B complete."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Schedule L — Balance Sheet per Books
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_schedule_l(self, sources):
        form = self._upsert_form(
            "1120S_SCHL", "Schedule L (Form 1120-S) — Balance Sheet per Books",
            ["1120S"],
            notes="BOY and EOY balance sheet. Assets L1-14, Liabilities L15-21, Equity L22-27. Small corp exception if receipts < $250K AND assets < $250K.",
        )
        self._upsert_facts(form, [
            # Assets — BOY
            {"fact_key": "l1_cash_boy", "label": "L1 Cash (BOY)", "data_type": "decimal", "sort_order": 1},
            {"fact_key": "l2a_trade_receivables_boy", "label": "L2a Trade notes & accounts receivable (BOY)", "data_type": "decimal", "sort_order": 2},
            {"fact_key": "l2b_allowance_boy", "label": "L2b Less allowance for bad debts (BOY)", "data_type": "decimal", "sort_order": 3},
            {"fact_key": "l3_inventories_boy", "label": "L3 Inventories (BOY)", "data_type": "decimal", "sort_order": 4},
            {"fact_key": "l5_tax_exempt_securities_boy", "label": "L5 Tax-exempt securities (BOY)", "data_type": "decimal", "sort_order": 5},
            {"fact_key": "l6_other_investments_boy", "label": "L6 Other investments (BOY)", "data_type": "decimal", "sort_order": 6},
            {"fact_key": "l7_buildings_depreciable_boy", "label": "L7 Buildings & depreciable assets net (BOY)", "data_type": "decimal", "sort_order": 7},
            {"fact_key": "l8_intangible_assets_boy", "label": "L8 Intangible assets net (BOY)", "data_type": "decimal", "sort_order": 8},
            {"fact_key": "l9_land_boy", "label": "L9 Land (BOY)", "data_type": "decimal", "sort_order": 9},
            {"fact_key": "l10_other_assets_boy", "label": "L10 Other assets (BOY)", "data_type": "decimal", "sort_order": 10},
            {"fact_key": "l14_total_assets_boy", "label": "L14 Total assets (BOY)", "data_type": "decimal", "sort_order": 11},
            # Assets — EOY
            {"fact_key": "l1_cash_eoy", "label": "L1 Cash (EOY)", "data_type": "decimal", "sort_order": 12},
            {"fact_key": "l2a_trade_receivables_eoy", "label": "L2a Trade notes & accounts receivable (EOY)", "data_type": "decimal", "sort_order": 13},
            {"fact_key": "l2b_allowance_eoy", "label": "L2b Less allowance for bad debts (EOY)", "data_type": "decimal", "sort_order": 14},
            {"fact_key": "l3_inventories_eoy", "label": "L3 Inventories (EOY)", "data_type": "decimal", "sort_order": 15},
            {"fact_key": "l5_tax_exempt_securities_eoy", "label": "L5 Tax-exempt securities (EOY)", "data_type": "decimal", "sort_order": 16},
            {"fact_key": "l6_other_investments_eoy", "label": "L6 Other investments (EOY)", "data_type": "decimal", "sort_order": 17},
            {"fact_key": "l7_buildings_depreciable_eoy", "label": "L7 Buildings & depreciable assets net (EOY)", "data_type": "decimal", "sort_order": 18},
            {"fact_key": "l8_intangible_assets_eoy", "label": "L8 Intangible assets net (EOY)", "data_type": "decimal", "sort_order": 19},
            {"fact_key": "l9_land_eoy", "label": "L9 Land (EOY)", "data_type": "decimal", "sort_order": 20},
            {"fact_key": "l10_other_assets_eoy", "label": "L10 Other assets (EOY)", "data_type": "decimal", "sort_order": 21},
            {"fact_key": "l14_total_assets_eoy", "label": "L14 Total assets (EOY)", "data_type": "decimal", "sort_order": 22},
            # Liabilities — BOY
            {"fact_key": "l15_accounts_payable_boy", "label": "L15 Accounts payable (BOY)", "data_type": "decimal", "sort_order": 23},
            {"fact_key": "l16_mortgages_short_boy", "label": "L16 Mortgages, notes, bonds < 1 year (BOY)", "data_type": "decimal", "sort_order": 24},
            {"fact_key": "l17_other_current_liab_boy", "label": "L17 Other current liabilities (BOY)", "data_type": "decimal", "sort_order": 25},
            {"fact_key": "l18_shareholder_loans_boy", "label": "L18 Loans from shareholders (BOY)", "data_type": "decimal", "sort_order": 26},
            {"fact_key": "l19_mortgages_long_boy", "label": "L19 Mortgages, notes, bonds >= 1 year (BOY)", "data_type": "decimal", "sort_order": 27},
            {"fact_key": "l20_other_liabilities_boy", "label": "L20 Other liabilities (BOY)", "data_type": "decimal", "sort_order": 28},
            {"fact_key": "l21_total_liabilities_boy", "label": "L21 Total liabilities (BOY)", "data_type": "decimal", "sort_order": 29},
            # Liabilities — EOY
            {"fact_key": "l15_accounts_payable_eoy", "label": "L15 Accounts payable (EOY)", "data_type": "decimal", "sort_order": 30},
            {"fact_key": "l16_mortgages_short_eoy", "label": "L16 Mortgages, notes, bonds < 1 year (EOY)", "data_type": "decimal", "sort_order": 31},
            {"fact_key": "l17_other_current_liab_eoy", "label": "L17 Other current liabilities (EOY)", "data_type": "decimal", "sort_order": 32},
            {"fact_key": "l18_shareholder_loans_eoy", "label": "L18 Loans from shareholders (EOY)", "data_type": "decimal", "sort_order": 33},
            {"fact_key": "l19_mortgages_long_eoy", "label": "L19 Mortgages, notes, bonds >= 1 year (EOY)", "data_type": "decimal", "sort_order": 34},
            {"fact_key": "l20_other_liabilities_eoy", "label": "L20 Other liabilities (EOY)", "data_type": "decimal", "sort_order": 35},
            {"fact_key": "l21_total_liabilities_eoy", "label": "L21 Total liabilities (EOY)", "data_type": "decimal", "sort_order": 36},
            # Equity — BOY
            {"fact_key": "l22_capital_stock_boy", "label": "L22 Capital stock (BOY)", "data_type": "decimal", "sort_order": 37},
            {"fact_key": "l23_paid_in_capital_boy", "label": "L23 Additional paid-in capital (BOY)", "data_type": "decimal", "sort_order": 38},
            {"fact_key": "l24_retained_earnings_boy", "label": "L24 Retained earnings (BOY)", "data_type": "decimal", "sort_order": 39},
            {"fact_key": "l25_adjustments_equity_boy", "label": "L25 Adjustments to shareholders' equity (BOY)", "data_type": "decimal", "sort_order": 40},
            {"fact_key": "l26_treasury_stock_boy", "label": "L26 Less cost of treasury stock (BOY)", "data_type": "decimal", "sort_order": 41},
            {"fact_key": "l27_total_lse_boy", "label": "L27 Total liabilities & shareholders' equity (BOY)", "data_type": "decimal", "sort_order": 42},
            # Equity — EOY
            {"fact_key": "l22_capital_stock_eoy", "label": "L22 Capital stock (EOY)", "data_type": "decimal", "sort_order": 43},
            {"fact_key": "l23_paid_in_capital_eoy", "label": "L23 Additional paid-in capital (EOY)", "data_type": "decimal", "sort_order": 44},
            {"fact_key": "l24_retained_earnings_eoy", "label": "L24 Retained earnings (EOY)", "data_type": "decimal", "sort_order": 45},
            {"fact_key": "l25_adjustments_equity_eoy", "label": "L25 Adjustments to shareholders' equity (EOY)", "data_type": "decimal", "sort_order": 46},
            {"fact_key": "l26_treasury_stock_eoy", "label": "L26 Less cost of treasury stock (EOY)", "data_type": "decimal", "sort_order": 47},
            {"fact_key": "l27_total_lse_eoy", "label": "L27 Total liabilities & shareholders' equity (EOY)", "data_type": "decimal", "sort_order": 48},
            # Cross-check facts
            {"fact_key": "total_receipts", "label": "Total receipts (for small corp exception)", "data_type": "decimal", "sort_order": 49},
            {"fact_key": "m2_ending_balance", "label": "M-2 ending balance (for retained earnings tie)", "data_type": "decimal", "sort_order": 50},
        ])

        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "Total assets = sum of asset lines", "rule_type": "calculation",
             "formula": "l14 = l1 + (l2a - l2b) + l3 + l5 + l6 + l7 + l8 + l9 + l10 (both BOY and EOY)",
             "inputs": ["l1_cash_boy", "l2a_trade_receivables_boy", "l2b_allowance_boy", "l3_inventories_boy",
                        "l5_tax_exempt_securities_boy", "l6_other_investments_boy", "l7_buildings_depreciable_boy",
                        "l8_intangible_assets_boy", "l9_land_boy", "l10_other_assets_boy"],
             "outputs": ["l14_total_assets_boy", "l14_total_assets_eoy"], "precedence": 1, "sort_order": 1},
            {"rule_id": "R002", "title": "Total liabilities = sum of liability lines", "rule_type": "calculation",
             "formula": "l21 = l15 + l16 + l17 + l18 + l19 + l20 (both BOY and EOY)",
             "inputs": ["l15_accounts_payable_boy", "l16_mortgages_short_boy", "l17_other_current_liab_boy",
                        "l18_shareholder_loans_boy", "l19_mortgages_long_boy", "l20_other_liabilities_boy"],
             "outputs": ["l21_total_liabilities_boy", "l21_total_liabilities_eoy"], "precedence": 2, "sort_order": 2},
            {"rule_id": "R003", "title": "Total L&SE = liabilities + equity", "rule_type": "calculation",
             "formula": "l27 = l21 + l22 + l23 + l24 + l25 - l26 (both BOY and EOY)",
             "inputs": ["l21_total_liabilities_boy", "l22_capital_stock_boy", "l23_paid_in_capital_boy",
                        "l24_retained_earnings_boy", "l25_adjustments_equity_boy", "l26_treasury_stock_boy"],
             "outputs": ["l27_total_lse_boy", "l27_total_lse_eoy"], "precedence": 3, "sort_order": 3},
            {"rule_id": "R004", "title": "Balance sheet must balance (L14 = L27)", "rule_type": "validation",
             "formula": "l14_total_assets == l27_total_lse (both BOY and EOY)",
             "inputs": ["l14_total_assets_boy", "l14_total_assets_eoy", "l27_total_lse_boy", "l27_total_lse_eoy"],
             "outputs": [], "precedence": 4, "sort_order": 4,
             "description": "Total assets must equal total liabilities & shareholders' equity for both BOY and EOY."},
            {"rule_id": "R005", "title": "Retained earnings tie to M-2", "rule_type": "validation",
             "formula": "l24_retained_earnings_eoy == m2_ending_balance",
             "inputs": ["l24_retained_earnings_eoy", "m2_ending_balance"], "outputs": [], "precedence": 5, "sort_order": 5,
             "description": "L24 (retained earnings) EOY should tie to Schedule M-2 ending balance."},
            {"rule_id": "R006", "title": "BOY inventories tie to prior year EOY", "rule_type": "validation",
             "formula": "l3_inventories_boy == prior_year_l3_inventories_eoy",
             "inputs": ["l3_inventories_boy"], "outputs": [], "precedence": 6, "sort_order": 6,
             "description": "L3 inventories BOY should equal prior year L3 inventories EOY."},
            {"rule_id": "R007", "title": "Small corporation exception", "rule_type": "conditional",
             "formula": "schedule_l_not_required = (total_receipts < 250000 AND l14_total_assets_eoy < 250000)",
             "inputs": ["total_receipts", "l14_total_assets_eoy"], "outputs": ["schedule_l_not_required"], "precedence": 0, "sort_order": 7,
             "description": "Schedule L not required if total receipts < $250K AND total assets < $250K."},
        ])
        self._upsert_links(rules, sources, [
            ("R001", "IRS_2025_1120S_SCHL_INSTR", "primary", "Asset line summation"),
            ("R002", "IRS_2025_1120S_SCHL_INSTR", "primary", "Liability line summation"),
            ("R003", "IRS_2025_1120S_SCHL_INSTR", "primary", "L&SE = liabilities + equity"),
            ("R004", "IRS_2025_1120S_SCHL_INSTR", "primary", "L14 must equal L27"),
            ("R005", "IRS_2025_1120S_SCHL_INSTR", "primary", "L24 ties to M-2 ending balance"),
            ("R006", "IRS_2025_1120S_INSTR", "secondary", "BOY should equal prior year EOY"),
            ("R007", "IRS_2025_1120S_SCHL_INSTR", "primary", "Small corp exception: <$250K receipts AND assets"),
        ])
        self._upsert_lines(form, [
            {"line_number": "L1", "description": "Cash", "line_type": "input", "sort_order": 1},
            {"line_number": "L2a", "description": "Trade notes & accounts receivable", "line_type": "input", "sort_order": 2},
            {"line_number": "L2b", "description": "Less allowance for bad debts", "line_type": "input", "sort_order": 3},
            {"line_number": "L3", "description": "Inventories", "line_type": "input", "sort_order": 4},
            {"line_number": "L4", "description": "U.S. government obligations", "line_type": "input", "sort_order": 5},
            {"line_number": "L5", "description": "Tax-exempt securities", "line_type": "input", "sort_order": 6},
            {"line_number": "L6", "description": "Other current assets", "line_type": "input", "sort_order": 7},
            {"line_number": "L7", "description": "Loans to shareholders", "line_type": "input", "sort_order": 8},
            {"line_number": "L8", "description": "Mortgage and real estate loans", "line_type": "input", "sort_order": 9},
            {"line_number": "L9", "description": "Other investments", "line_type": "input", "sort_order": 10},
            {"line_number": "L10a", "description": "Buildings and other depreciable assets (gross)", "line_type": "input", "sort_order": 11},
            {"line_number": "L10b", "description": "Less accumulated depreciation", "line_type": "input", "sort_order": 12},
            {"line_number": "L11", "description": "Depletable assets", "line_type": "input", "sort_order": 13},
            {"line_number": "L12", "description": "Land (net of any amortization)", "line_type": "input", "sort_order": 14},
            {"line_number": "L13a", "description": "Intangible assets (amortizable only, gross)", "line_type": "input", "sort_order": 15},
            {"line_number": "L13b", "description": "Less accumulated amortization", "line_type": "input", "sort_order": 16},
            {"line_number": "L14", "description": "Other assets", "line_type": "input", "sort_order": 17},
            {"line_number": "L15", "description": "Total assets", "line_type": "total", "source_rules": ["R001"], "sort_order": 18},
            {"line_number": "L16", "description": "Accounts payable", "line_type": "input", "sort_order": 19},
            {"line_number": "L17", "description": "Mortgages, notes, bonds payable < 1 year", "line_type": "input", "sort_order": 20},
            {"line_number": "L18", "description": "Other current liabilities", "line_type": "input", "sort_order": 21},
            {"line_number": "L19", "description": "Loans from shareholders", "line_type": "input", "sort_order": 22},
            {"line_number": "L20", "description": "Mortgages, notes, bonds payable >= 1 year", "line_type": "input", "sort_order": 23},
            {"line_number": "L21", "description": "Other liabilities", "line_type": "input", "sort_order": 24},
            {"line_number": "L22", "description": "Total liabilities", "line_type": "total", "source_rules": ["R002"], "sort_order": 25},
            {"line_number": "L23", "description": "Capital stock", "line_type": "input", "sort_order": 26},
            {"line_number": "L24", "description": "Additional paid-in capital", "line_type": "input", "sort_order": 27},
            {"line_number": "L25", "description": "Retained earnings", "line_type": "input", "sort_order": 28},
            {"line_number": "L26", "description": "Adjustments to shareholders' equity", "line_type": "input", "sort_order": 29},
            {"line_number": "L27", "description": "Less cost of treasury stock", "line_type": "input", "sort_order": 30},
            {"line_number": "L28", "description": "Total liabilities and shareholders' equity", "line_type": "total", "source_rules": ["R003"], "sort_order": 31},
        ])
        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D001", "title": "Balance sheet out of balance (BOY)", "severity": "error",
             "condition": "l14_total_assets_boy != l27_total_lse_boy",
             "message": "BOY balance sheet out of balance: Total assets does not equal total liabilities & shareholders' equity."},
            {"diagnostic_id": "D002", "title": "Balance sheet out of balance (EOY)", "severity": "error",
             "condition": "l14_total_assets_eoy != l27_total_lse_eoy",
             "message": "EOY balance sheet out of balance: Total assets does not equal total liabilities & shareholders' equity."},
            {"diagnostic_id": "D003", "title": "Retained earnings don't tie to M-2", "severity": "warning",
             "condition": "l24_retained_earnings_eoy != m2_ending_balance",
             "message": "L24 retained earnings (EOY) does not match Schedule M-2 ending balance."},
            {"diagnostic_id": "D004", "title": "Negative cash balance", "severity": "warning",
             "condition": "l1_cash_eoy < 0",
             "message": "Cash balance is negative at end of year. Verify bank accounts and outstanding items."},
            {"diagnostic_id": "D005", "title": "Inventory without COGS", "severity": "warning",
             "condition": "l3_inventories_eoy > 0 AND no_form_1125a",
             "message": "Inventory on L3 but no Form 1125-A (COGS) filed."},
            {"diagnostic_id": "D006", "title": "Shareholder loans without interest", "severity": "warning",
             "condition": "l18_shareholder_loans_eoy > 0 AND page1_interest_expense == 0",
             "message": "Shareholder loans on L18 but no interest expense on Page 1. Verify below-market loan rules."},
        ])
        self._upsert_tests(form, [
            {"scenario_name": "Balanced balance sheet", "scenario_type": "normal",
             "inputs": {
                 "l1_cash_boy": 50000, "l7_buildings_depreciable_boy": 200000, "l9_land_boy": 100000,
                 "l14_total_assets_boy": 350000,
                 "l15_accounts_payable_boy": 20000, "l19_mortgages_long_boy": 150000, "l21_total_liabilities_boy": 170000,
                 "l22_capital_stock_boy": 1000, "l24_retained_earnings_boy": 179000, "l27_total_lse_boy": 350000,
             },
             "expected_outputs": {"balance_sheet_balances_boy": True, "balance_sheet_balances_eoy": True}, "sort_order": 1},
            {"scenario_name": "Out-of-balance balance sheet", "scenario_type": "failure",
             "inputs": {
                 "l14_total_assets_eoy": 500000, "l27_total_lse_eoy": 490000,
             },
             "expected_outputs": {"balance_sheet_balances_eoy": False, "diagnostic_D002_fires": True}, "sort_order": 2},
            {"scenario_name": "Small corporation exception", "scenario_type": "edge",
             "inputs": {"total_receipts": 180000, "l14_total_assets_eoy": 200000},
             "expected_outputs": {"schedule_l_not_required": True}, "sort_order": 3},
        ])
        self._upsert_form_links("1120S_SCHL", sources, [
            ("IRS_2025_1120S_SCHL_INSTR", "governs"),
            ("IRS_2025_1120S_INSTR", "informs"),
        ])
        self.stdout.write(self.style.SUCCESS("  Schedule L complete."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Form 8995 — Qualified Business Income Deduction (Simplified)
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_8995(self, sources):
        form = self._upsert_form(
            "8995", "Form 8995 — Qualified Business Income Deduction Simplified Computation",
            ["1040"],
            notes="Simplified QBI deduction. Used when taxable income <= $197,300 (single) / $394,600 (MFJ). Flows to K-1 Box 17 Code V.",
        )
        self._upsert_facts(form, [
            {"fact_key": "trade_business_name", "label": "Line 1 — Trade or business name", "data_type": "string", "sort_order": 1},
            {"fact_key": "trade_business_tin", "label": "Line 1 — Taxpayer identification number", "data_type": "string", "sort_order": 2},
            {"fact_key": "qualified_business_income", "label": "Line 2 — Qualified business income (from K-1)", "data_type": "decimal", "required": True, "sort_order": 3},
            {"fact_key": "qualified_reit_dividends", "label": "Line 3 — Qualified REIT dividends and PTP income", "data_type": "decimal", "sort_order": 4},
            {"fact_key": "total_qbi", "label": "Line 4 — Total QBI (Line 2 + Line 3)", "data_type": "decimal", "sort_order": 5},
            {"fact_key": "qbi_deduction", "label": "Line 5 — QBI deduction (20% of Line 4)", "data_type": "decimal", "sort_order": 6},
            {"fact_key": "taxable_income_before_qbi", "label": "Taxable income before QBI deduction", "data_type": "decimal", "required": True, "sort_order": 7},
            {"fact_key": "net_capital_gain", "label": "Net capital gain", "data_type": "decimal", "sort_order": 8},
            {"fact_key": "filing_status", "label": "Filing status", "data_type": "choice",
             "choices": ["single", "mfj", "mfs", "hoh", "qss"], "sort_order": 9},
            {"fact_key": "is_sstb", "label": "Is the trade/business a specified service trade or business (SSTB)?", "data_type": "boolean", "sort_order": 10},
        ])

        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "QBI deduction = 20% of qualified business income", "rule_type": "calculation",
             "formula": "qbi_deduction = 0.20 * total_qbi",
             "inputs": ["total_qbi"], "outputs": ["qbi_deduction"], "precedence": 1, "sort_order": 1,
             "description": "IRC section 199A: QBI deduction = 20% of qualified business income."},
            {"rule_id": "R002", "title": "Threshold check — simplified vs full form", "rule_type": "conditional",
             "formula": "if taxable_income_before_qbi > threshold then use_form_8995a",
             "inputs": ["taxable_income_before_qbi", "filing_status"], "outputs": ["use_form_8995a"], "precedence": 0, "sort_order": 2,
             "description": "Thresholds: $197,300 (single) / $394,600 (MFJ) for 2025. Above threshold must use Form 8995-A."},
            {"rule_id": "R003", "title": "QBI cannot exceed taxable income limitation", "rule_type": "validation",
             "formula": "qbi_deduction <= 0.20 * (taxable_income_before_qbi - net_capital_gain)",
             "inputs": ["qbi_deduction", "taxable_income_before_qbi", "net_capital_gain"], "outputs": [], "precedence": 2, "sort_order": 3,
             "description": "QBI deduction cannot exceed 20% of taxable income minus net capital gains."},
            {"rule_id": "R004", "title": "SSTB phase-out applies near threshold", "rule_type": "conditional",
             "formula": "if is_sstb AND taxable_income between threshold and threshold + 50000/100000 then apply_phaseout",
             "inputs": ["is_sstb", "taxable_income_before_qbi", "filing_status"], "outputs": [], "precedence": 3, "sort_order": 4,
             "description": "SSTB: QBI phases out between threshold and threshold + $50K (single) / $100K (MFJ)."},
            {"rule_id": "R005", "title": "Section 199A made permanent by OBBBA", "rule_type": "validation",
             "formula": "section_199a_active = True (permanent after OBBBA)",
             "inputs": [], "outputs": [], "precedence": 0, "sort_order": 5,
             "description": "Section 199A QBI deduction was made permanent by OBBBA (P.L. 119-21). Previously set to expire after 2025."},
        ])
        self._upsert_links(rules, sources, [
            ("R001", "IRC_199A", "primary", "Section 199A(a) — 20% QBI deduction"),
            ("R002", "IRS_2025_8995_INSTR", "primary", "Simplified threshold check"),
            ("R002", "IRC_199A", "secondary", "Section 199A threshold amounts"),
            ("R003", "IRC_199A", "primary", "Section 199A(a) — taxable income limitation"),
            ("R004", "IRC_199A", "primary", "Section 199A(d) — SSTB phase-out"),
            ("R005", "IRC_199A", "primary", "OBBBA made section 199A permanent"),
        ])
        self._upsert_lines(form, [
            {"line_number": "1", "description": "Trade or business name and TIN", "line_type": "input", "sort_order": 1},
            {"line_number": "2", "description": "Qualified business income (from K-1 Box 1)", "line_type": "input", "sort_order": 2},
            {"line_number": "3", "description": "Qualified REIT dividends and publicly traded partnership income", "line_type": "input", "sort_order": 3},
            {"line_number": "4", "description": "Total QBI (Line 2 + Line 3)", "line_type": "subtotal", "source_rules": ["R001"], "sort_order": 4},
            {"line_number": "5", "description": "QBI deduction (20% of Line 4, limited by taxable income)", "line_type": "total",
             "source_rules": ["R001", "R003"], "destination_form": "1040 Line 13", "sort_order": 5},
            {"line_number": "6", "description": "Total QBI component of the QBI deduction", "line_type": "calculated", "sort_order": 6},
            {"line_number": "7", "description": "REIT/PTP component of the QBI deduction", "line_type": "calculated", "sort_order": 7},
            {"line_number": "8", "description": "Total QBI deduction (Line 6 + Line 7)", "line_type": "total", "sort_order": 8},
        ])
        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D001", "title": "QBI without K-1 Box 17 Code V", "severity": "warning",
             "condition": "qbi_deduction > 0 AND no_k1_box17_code_v",
             "message": "QBI deduction claimed but no K-1 Box 17 Code V data found."},
            {"diagnostic_id": "D002", "title": "Exceeds simplified threshold", "severity": "warning",
             "condition": "taxable_income_before_qbi > simplified_threshold",
             "message": "Taxable income exceeds simplified threshold — should use Form 8995-A instead."},
            {"diagnostic_id": "D003", "title": "SSTB without phase-out", "severity": "warning",
             "condition": "is_sstb == True AND in_phaseout_range AND no_phaseout_applied",
             "message": "SSTB indicated but no phase-out applied within the applicable range."},
        ])
        self._upsert_tests(form, [
            {"scenario_name": "Below threshold — standard QBI", "scenario_type": "normal",
             "inputs": {"qualified_business_income": 100000, "qualified_reit_dividends": 0,
                        "taxable_income_before_qbi": 150000, "filing_status": "mfj", "is_sstb": False},
             "expected_outputs": {"total_qbi": 100000, "qbi_deduction": 20000}, "sort_order": 1,
             "notes": "$100K QBI * 20% = $20K deduction. Well below $394,600 MFJ threshold."},
            {"scenario_name": "At threshold — must check form", "scenario_type": "edge",
             "inputs": {"qualified_business_income": 200000, "taxable_income_before_qbi": 394600,
                        "filing_status": "mfj", "is_sstb": False},
             "expected_outputs": {"total_qbi": 200000, "qbi_deduction": 40000, "use_form_8995a": False}, "sort_order": 2,
             "notes": "Exactly at $394,600 MFJ threshold. Simplified form still OK."},
            {"scenario_name": "SSTB in phase-out range", "scenario_type": "edge",
             "inputs": {"qualified_business_income": 50000, "taxable_income_before_qbi": 220000,
                        "filing_status": "single", "is_sstb": True},
             "expected_outputs": {"phaseout_applies": True}, "sort_order": 3,
             "notes": "$220K single, SSTB. Between $197,300 and $247,300 — phase-out applies."},
        ])
        self._upsert_form_links("8995", sources, [
            ("IRS_2025_8995_INSTR", "governs"),
            ("IRC_199A", "governs"),
        ])
        self.stdout.write(self.style.SUCCESS("  Form 8995 complete."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Form 8995-A — QBI Deduction (Full Computation)
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_8995a(self, sources):
        form = self._upsert_form(
            "8995A", "Form 8995-A — Qualified Business Income Deduction",
            ["1040"],
            notes="Full QBI computation when taxable income exceeds threshold. W-2 wage and UBIA limitations apply.",
        )
        self._upsert_facts(form, [
            {"fact_key": "trade_business_name", "label": "Trade or business name", "data_type": "string", "sort_order": 1},
            {"fact_key": "trade_business_tin", "label": "Taxpayer identification number", "data_type": "string", "sort_order": 2},
            {"fact_key": "qualified_business_income", "label": "Qualified business income", "data_type": "decimal", "required": True, "sort_order": 3},
            {"fact_key": "w2_wages", "label": "W-2 wages from the qualified trade/business", "data_type": "decimal", "sort_order": 4},
            {"fact_key": "ubia_qualified_property", "label": "UBIA of qualified property", "data_type": "decimal", "sort_order": 5,
             "notes": "Unadjusted basis immediately after acquisition. Depreciable period = greater of 10 years or recovery period."},
            {"fact_key": "taxable_income_before_qbi", "label": "Taxable income before QBI deduction", "data_type": "decimal", "required": True, "sort_order": 6},
            {"fact_key": "net_capital_gain", "label": "Net capital gain", "data_type": "decimal", "sort_order": 7},
            {"fact_key": "filing_status", "label": "Filing status", "data_type": "choice",
             "choices": ["single", "mfj", "mfs", "hoh", "qss"], "sort_order": 8},
            {"fact_key": "is_sstb", "label": "Is SSTB?", "data_type": "boolean", "sort_order": 9},
            {"fact_key": "qbi_20pct", "label": "20% of QBI", "data_type": "decimal", "sort_order": 10},
            {"fact_key": "w2_wage_limit_50pct", "label": "50% of W-2 wages", "data_type": "decimal", "sort_order": 11},
            {"fact_key": "w2_ubia_limit", "label": "25% of W-2 wages + 2.5% of UBIA", "data_type": "decimal", "sort_order": 12},
            {"fact_key": "greater_of_limits", "label": "Greater of W-2 limit or W-2+UBIA limit", "data_type": "decimal", "sort_order": 13},
            {"fact_key": "qbi_deduction_per_entity", "label": "QBI deduction per entity", "data_type": "decimal", "sort_order": 14},
            {"fact_key": "total_qbi_deduction", "label": "Total QBI deduction", "data_type": "decimal", "sort_order": 15},
            {"fact_key": "phaseout_pct", "label": "Phase-in percentage (for taxpayers between thresholds)", "data_type": "decimal", "sort_order": 16},
            {"fact_key": "qualified_reit_dividends", "label": "Qualified REIT dividends and PTP income", "data_type": "decimal", "sort_order": 17},
            {"fact_key": "sstb_applicable_pct", "label": "SSTB applicable percentage", "data_type": "decimal", "sort_order": 18,
             "notes": "Reduces QBI, W-2 wages, and UBIA for SSTBs in phase-out range."},
            {"fact_key": "threshold_amount", "label": "Threshold amount for filing status", "data_type": "decimal", "sort_order": 19},
            {"fact_key": "excess_over_threshold", "label": "Excess of taxable income over threshold", "data_type": "decimal", "sort_order": 20},
        ])

        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "Greater-of test: W-2 wages or W-2+UBIA", "rule_type": "calculation",
             "formula": "greater_of_limits = max(0.50 * w2_wages, 0.25 * w2_wages + 0.025 * ubia_qualified_property)",
             "inputs": ["w2_wages", "ubia_qualified_property"], "outputs": ["w2_wage_limit_50pct", "w2_ubia_limit", "greater_of_limits"],
             "precedence": 1, "sort_order": 1,
             "description": "IRC 199A(b)(2): QBI deduction limited to greater of 50% of W-2 wages OR 25% of W-2 wages + 2.5% of UBIA."},
            {"rule_id": "R002", "title": "QBI deduction = lesser of 20% QBI or W-2/UBIA limit", "rule_type": "calculation",
             "formula": "qbi_deduction_per_entity = min(0.20 * qualified_business_income, greater_of_limits)",
             "inputs": ["qualified_business_income", "greater_of_limits"], "outputs": ["qbi_deduction_per_entity"],
             "precedence": 2, "sort_order": 2,
             "description": "Per-entity QBI deduction is lesser of 20% of QBI or the W-2/UBIA limit."},
            {"rule_id": "R003", "title": "SSTB full exclusion above threshold + range", "rule_type": "conditional",
             "formula": "if is_sstb AND taxable_income > threshold + 50000/100000 then qbi_deduction = 0",
             "inputs": ["is_sstb", "taxable_income_before_qbi", "filing_status"], "outputs": ["qbi_deduction_per_entity"],
             "precedence": 3, "sort_order": 3,
             "description": "If SSTB and taxable income fully above threshold + $50K/$100K, QBI deduction is $0."},
            {"rule_id": "R004", "title": "Phase-in between threshold and threshold + range", "rule_type": "calculation",
             "formula": "phaseout_pct = (threshold + range - taxable_income) / range; applicable_amount = qbi_20pct - (qbi_20pct - greater_of_limits) * (1 - phaseout_pct)",
             "inputs": ["taxable_income_before_qbi", "filing_status", "qbi_20pct", "greater_of_limits"],
             "outputs": ["phaseout_pct", "qbi_deduction_per_entity"], "precedence": 2, "sort_order": 4,
             "description": "For taxpayers between threshold and threshold + $50K/$100K, the W-2/UBIA limitation phases in."},
            {"rule_id": "R005", "title": "UBIA = unadjusted basis immediately after acquisition", "rule_type": "validation",
             "formula": "ubia = cost_of_property_at_acquisition (not adjusted for depreciation)",
             "inputs": ["ubia_qualified_property"], "outputs": [], "precedence": 0, "sort_order": 5,
             "description": "UBIA is the unadjusted basis immediately after acquisition of qualified property still within its depreciable period."},
            {"rule_id": "R006", "title": "W-2 wages = wages reported on W-3", "rule_type": "validation",
             "formula": "w2_wages should equal total from W-3 for the trade/business",
             "inputs": ["w2_wages"], "outputs": [], "precedence": 0, "sort_order": 6,
             "description": "W-2 wages are wages reported on Form W-3 that are properly allocable to QBI."},
        ])
        self._upsert_links(rules, sources, [
            ("R001", "IRC_199A", "primary", "Section 199A(b)(2) — W-2/UBIA greater-of test"),
            ("R001", "IRS_2025_8995A_INSTR", "secondary", "Form 8995-A Part II instructions"),
            ("R002", "IRC_199A", "primary", "Section 199A(b)(2) — lesser of 20% QBI or limit"),
            ("R003", "IRC_199A", "primary", "Section 199A(d) — SSTB full exclusion"),
            ("R003", "IRS_2025_8995A_INSTR", "secondary", "SSTB rules on Form 8995-A"),
            ("R004", "IRC_199A", "primary", "Section 199A(b)(3) — phase-in computation"),
            ("R005", "IRC_199A", "secondary", "UBIA definition from 199A(b)(6)"),
            ("R006", "IRS_2025_8995A_INSTR", "secondary", "W-2 wages determination"),
        ])
        self._upsert_lines(form, [
            {"line_number": "1", "description": "Trade or business name and TIN", "line_type": "input", "sort_order": 1},
            {"line_number": "2", "description": "Qualified business income", "line_type": "input", "sort_order": 2},
            {"line_number": "3", "description": "20% of QBI (Line 2 * 0.20)", "line_type": "calculated", "source_rules": ["R002"], "sort_order": 3},
            {"line_number": "4", "description": "W-2 wages from trade/business", "line_type": "input", "sort_order": 4},
            {"line_number": "5", "description": "50% of W-2 wages", "line_type": "calculated", "source_rules": ["R001"], "sort_order": 5},
            {"line_number": "6", "description": "25% of W-2 wages", "line_type": "calculated", "source_rules": ["R001"], "sort_order": 6},
            {"line_number": "7", "description": "UBIA of qualified property", "line_type": "input", "sort_order": 7},
            {"line_number": "8", "description": "2.5% of UBIA", "line_type": "calculated", "source_rules": ["R001"], "sort_order": 8},
            {"line_number": "9", "description": "Line 6 + Line 8 (25% W-2 + 2.5% UBIA)", "line_type": "subtotal", "source_rules": ["R001"], "sort_order": 9},
            {"line_number": "10", "description": "Greater of Line 5 or Line 9", "line_type": "calculated", "source_rules": ["R001"], "sort_order": 10},
            {"line_number": "11", "description": "Lesser of Line 3 or Line 10 (QBI deduction before phase-in)", "line_type": "calculated", "source_rules": ["R002"], "sort_order": 11},
            {"line_number": "12", "description": "Qualified REIT dividends and PTP income", "line_type": "input", "sort_order": 12},
            {"line_number": "13", "description": "20% of Line 12", "line_type": "calculated", "sort_order": 13},
            {"line_number": "14", "description": "Total QBI deduction (Line 11 + Line 13)", "line_type": "total",
             "destination_form": "1040 Line 13", "sort_order": 14},
            {"line_number": "15", "description": "Taxable income limitation (20% of taxable income minus net capital gain)", "line_type": "calculated", "sort_order": 15},
        ])
        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D001", "title": "W-2 wages are zero", "severity": "warning",
             "condition": "w2_wages == 0 AND qualified_business_income > 0",
             "message": "W-2 wages entered as zero — this may significantly limit the QBI deduction above the threshold."},
            {"diagnostic_id": "D002", "title": "UBIA is zero", "severity": "warning",
             "condition": "ubia_qualified_property == 0 AND qualified_business_income > 0",
             "message": "UBIA entered as zero — verify that the business has no qualified property within its depreciable period."},
            {"diagnostic_id": "D003", "title": "QBI exceeds taxable income limitation", "severity": "error",
             "condition": "total_qbi_deduction > 0.20 * (taxable_income_before_qbi - net_capital_gain)",
             "message": "QBI deduction exceeds 20% of taxable income minus net capital gain. Deduction must be limited."},
            {"diagnostic_id": "D004", "title": "SSTB not indicated but may apply", "severity": "warning",
             "condition": "is_sstb == False AND business_type_suggests_sstb",
             "message": "SSTB not indicated but business type suggests it may be a specified service trade or business (professional services, consulting, etc.)."},
        ])
        self._upsert_tests(form, [
            {"scenario_name": "Above threshold — W-2 wage limitation applies", "scenario_type": "normal",
             "inputs": {"qualified_business_income": 300000, "w2_wages": 100000, "ubia_qualified_property": 200000,
                        "taxable_income_before_qbi": 500000, "filing_status": "mfj", "is_sstb": False},
             "expected_outputs": {"qbi_20pct": 60000, "w2_wage_limit_50pct": 50000,
                                  "w2_ubia_limit": 30000, "greater_of_limits": 50000, "qbi_deduction_per_entity": 50000},
             "sort_order": 1,
             "notes": "20% of $300K = $60K. 50% of $100K = $50K. 25% of $100K + 2.5% of $200K = $30K. Greater = $50K. Lesser of $60K or $50K = $50K."},
            {"scenario_name": "SSTB — full exclusion above range", "scenario_type": "edge",
             "inputs": {"qualified_business_income": 200000, "w2_wages": 80000, "ubia_qualified_property": 0,
                        "taxable_income_before_qbi": 500000, "filing_status": "single", "is_sstb": True},
             "expected_outputs": {"qbi_deduction_per_entity": 0},
             "sort_order": 2,
             "notes": "$500K single SSTB. Threshold $197,300 + $50K = $247,300. Fully above. QBI = $0."},
            {"scenario_name": "SSTB — phase-in range", "scenario_type": "edge",
             "inputs": {"qualified_business_income": 150000, "w2_wages": 60000, "ubia_qualified_property": 100000,
                        "taxable_income_before_qbi": 420000, "filing_status": "mfj", "is_sstb": True},
             "expected_outputs": {"sstb_phaseout_applies": True},
             "sort_order": 3,
             "notes": "$420K MFJ SSTB. Between $394,600 and $494,600. Phase-out applies: ($494,600 - $420,000) / $100,000 = 74.6% applicable."},
            {"scenario_name": "UBIA greater-of test wins", "scenario_type": "normal",
             "inputs": {"qualified_business_income": 500000, "w2_wages": 40000, "ubia_qualified_property": 2000000,
                        "taxable_income_before_qbi": 600000, "filing_status": "mfj", "is_sstb": False},
             "expected_outputs": {"w2_wage_limit_50pct": 20000, "w2_ubia_limit": 60000, "greater_of_limits": 60000,
                                  "qbi_deduction_per_entity": 60000},
             "sort_order": 4,
             "notes": "50% of $40K = $20K. 25% of $40K + 2.5% of $2M = $10K + $50K = $60K. Greater = $60K. 20% of $500K = $100K. Lesser = $60K."},
        ])
        self._upsert_form_links("8995A", sources, [
            ("IRS_2025_8995A_INSTR", "governs"),
            ("IRC_199A", "governs"),
        ])
        self.stdout.write(self.style.SUCCESS("  Form 8995-A complete."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Form 8582 — Passive Activity Loss Limitations
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_8582(self, sources):
        form = self._upsert_form(
            "8582", "Form 8582 — Passive Activity Loss Limitations",
            ["1040"],
            notes="Determines allowable passive activity losses at shareholder level. Rental activities passive per se unless RE professional.",
        )
        self._upsert_facts(form, [
            {"fact_key": "rental_income", "label": "Rental real estate income (with active participation)", "data_type": "decimal", "sort_order": 1},
            {"fact_key": "rental_loss", "label": "Rental real estate loss (with active participation)", "data_type": "decimal", "sort_order": 2},
            {"fact_key": "other_passive_income", "label": "Other passive income", "data_type": "decimal", "sort_order": 3},
            {"fact_key": "other_passive_loss", "label": "Other passive loss", "data_type": "decimal", "sort_order": 4},
            {"fact_key": "total_passive_income", "label": "Total passive income", "data_type": "decimal", "sort_order": 5},
            {"fact_key": "total_passive_loss", "label": "Total passive loss", "data_type": "decimal", "sort_order": 6},
            {"fact_key": "net_passive_loss", "label": "Net passive loss", "data_type": "decimal", "sort_order": 7},
            {"fact_key": "modified_agi", "label": "Modified adjusted gross income (MAGI)", "data_type": "decimal", "sort_order": 8},
            {"fact_key": "special_allowance_25k", "label": "$25,000 special allowance", "data_type": "decimal", "sort_order": 9},
            {"fact_key": "allowable_passive_loss", "label": "Allowable passive loss", "data_type": "decimal", "sort_order": 10},
            {"fact_key": "suspended_passive_loss", "label": "Suspended passive loss (carried forward)", "data_type": "decimal", "sort_order": 11},
            {"fact_key": "active_participation", "label": "Active participation in rental real estate?", "data_type": "boolean", "sort_order": 12},
            {"fact_key": "real_estate_professional", "label": "Real estate professional status?", "data_type": "boolean", "sort_order": 13},
            {"fact_key": "complete_disposition", "label": "Fully taxable disposition of activity?", "data_type": "boolean", "sort_order": 14},
            {"fact_key": "prior_year_suspended", "label": "Prior year suspended passive losses", "data_type": "decimal", "sort_order": 15},
        ])

        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "Rental activities passive per se", "rule_type": "classification",
             "formula": "rental_activity_is_passive = True (unless real_estate_professional)",
             "inputs": ["real_estate_professional"], "outputs": [], "precedence": 1, "sort_order": 1,
             "description": "IRC 469(c)(2): Rental activities are passive per se unless the taxpayer qualifies as a real estate professional."},
            {"rule_id": "R002", "title": "$25K special allowance for active participation", "rule_type": "calculation",
             "formula": "special_allowance = max(0, min(25000, 25000 - 0.50 * max(0, modified_agi - 100000)))",
             "inputs": ["modified_agi", "active_participation"], "outputs": ["special_allowance_25k"],
             "precedence": 2, "sort_order": 2,
             "description": "$25K allowance phases out at $0.50/$1 of MAGI over $100K. Fully phased out at $150K MAGI."},
            {"rule_id": "R003", "title": "Material participation — 7 tests", "rule_type": "classification",
             "formula": "material_participation = any of 7 tests from Reg 1.469-5T",
             "inputs": [], "outputs": [], "precedence": 0, "sort_order": 3,
             "description": "7 tests: (1) >500 hrs, (2) substantially all participation, (3) >100 hrs and not less than any other, (4) significant participation aggregating >500 hrs, (5) 5 of 10 prior years, (6) personal service activity 3 prior years, (7) facts and circumstances >100 hrs."},
            {"rule_id": "R004", "title": "Passive losses suspended if exceeding passive income", "rule_type": "calculation",
             "formula": "suspended_passive_loss = max(0, total_passive_loss - total_passive_income - special_allowance_25k)",
             "inputs": ["total_passive_loss", "total_passive_income", "special_allowance_25k"],
             "outputs": ["suspended_passive_loss", "allowable_passive_loss"], "precedence": 3, "sort_order": 4,
             "description": "Passive losses exceeding passive income (after $25K allowance) are suspended and carried forward."},
            {"rule_id": "R005", "title": "Complete disposition releases suspended losses", "rule_type": "conditional",
             "formula": "if complete_disposition then release all suspended_passive_loss for that activity",
             "inputs": ["complete_disposition", "prior_year_suspended"], "outputs": ["allowable_passive_loss"],
             "precedence": 4, "sort_order": 5,
             "description": "IRC 469(g): A fully taxable disposition of an entire interest releases all suspended passive losses."},
            {"rule_id": "R006", "title": "Grouping election", "rule_type": "conditional",
             "formula": "activities may be grouped under Reg 1.469-4 for material participation testing",
             "inputs": [], "outputs": [], "precedence": 0, "sort_order": 6,
             "description": "Reg 1.469-4: Taxpayer may elect to group activities as a single activity for material participation purposes."},
        ])
        self._upsert_links(rules, sources, [
            ("R001", "IRC_469", "primary", "Section 469(c)(2) — rental activities passive per se"),
            ("R001", "IRS_2025_8582_INSTR", "secondary", "Form 8582 passive activity rules overview"),
            ("R002", "IRC_469", "primary", "Section 469(i) — $25K rental real estate exception"),
            ("R002", "IRS_2025_8582_INSTR", "secondary", "$25K exception instructions"),
            ("R003", "IRS_2025_8582_INSTR", "primary", "Material participation tests from instructions"),
            ("R004", "IRC_469", "primary", "Section 469(a) — disallowance of passive losses"),
            ("R005", "IRC_469", "primary", "Section 469(g) — dispositions of entire interests"),
            ("R006", "IRS_2025_8582_INSTR", "secondary", "Grouping election instructions"),
        ])
        self._upsert_lines(form, [
            {"line_number": "1a", "description": "Rental real estate activities with active participation — income", "line_type": "input", "sort_order": 1},
            {"line_number": "1b", "description": "Rental real estate activities with active participation — loss", "line_type": "input", "sort_order": 2},
            {"line_number": "1c", "description": "Net rental (combine 1a and 1b)", "line_type": "calculated", "sort_order": 3},
            {"line_number": "2a", "description": "Commercial revitalization deduction — income", "line_type": "input", "sort_order": 4},
            {"line_number": "2b", "description": "Commercial revitalization deduction — loss", "line_type": "input", "sort_order": 5},
            {"line_number": "3a", "description": "All other passive activities — income", "line_type": "input", "sort_order": 6},
            {"line_number": "3b", "description": "All other passive activities — loss", "line_type": "input", "sort_order": 7},
            {"line_number": "3c", "description": "Net other passive (combine 3a and 3b)", "line_type": "calculated", "sort_order": 8},
            {"line_number": "4", "description": "Combine lines 1c, 2c, and 3c", "line_type": "subtotal", "sort_order": 9},
            {"line_number": "5", "description": "Allowable passive activity loss (from worksheets)", "line_type": "total",
             "source_rules": ["R002", "R004"], "sort_order": 10},
            {"line_number": "6", "description": "Suspended passive activity loss (carried to next year)", "line_type": "informational",
             "source_rules": ["R004"], "sort_order": 11},
            {"line_number": "7", "description": "Special allowance for rental real estate", "line_type": "calculated",
             "source_rules": ["R002"], "sort_order": 12},
        ])
        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D001", "title": "Rental loss without passive computation", "severity": "warning",
             "condition": "rental_loss > 0 AND no_passive_activity_computation",
             "message": "Rental loss reported but no passive activity computation at shareholder level."},
            {"diagnostic_id": "D002", "title": "Passive losses suspended", "severity": "warning",
             "condition": "suspended_passive_loss > 0",
             "message": "Passive losses suspended — K-1 should report to shareholder for basis and at-risk tracking."},
            {"diagnostic_id": "D003", "title": "Real estate professional claimed", "severity": "warning",
             "condition": "real_estate_professional == True",
             "message": "Real estate professional status claimed — verify 750-hour test and >50% of services in real property trades or businesses."},
        ])
        self._upsert_tests(form, [
            {"scenario_name": "Passive loss with passive income offset", "scenario_type": "normal",
             "inputs": {"rental_loss": 30000, "other_passive_income": 20000, "modified_agi": 80000,
                        "active_participation": True},
             "expected_outputs": {"net_passive_loss": 10000, "special_allowance_25k": 25000, "allowable_passive_loss": 30000},
             "sort_order": 1,
             "notes": "$30K loss, $20K income, $10K net loss. MAGI $80K (below $100K). Full $25K allowance available. All $30K allowed."},
            {"scenario_name": "$25K allowance phase-out", "scenario_type": "edge",
             "inputs": {"rental_loss": 30000, "other_passive_income": 0, "modified_agi": 130000,
                        "active_participation": True},
             "expected_outputs": {"special_allowance_25k": 10000, "allowable_passive_loss": 10000, "suspended_passive_loss": 20000},
             "sort_order": 2,
             "notes": "MAGI $130K. Allowance = $25K - 0.50 * ($130K - $100K) = $25K - $15K = $10K. Only $10K of $30K loss allowed."},
            {"scenario_name": "Complete disposition releases losses", "scenario_type": "edge",
             "inputs": {"complete_disposition": True, "prior_year_suspended": 50000, "rental_loss": 10000},
             "expected_outputs": {"allowable_passive_loss": 60000},
             "sort_order": 3,
             "notes": "Complete disposition releases all $50K prior suspended + $10K current = $60K fully deductible."},
        ])
        self._upsert_form_links("8582", sources, [
            ("IRS_2025_8582_INSTR", "governs"),
            ("IRC_469", "governs"),
        ])
        self.stdout.write(self.style.SUCCESS("  Form 8582 complete."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Form 6198 — At-Risk Limitations
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_6198(self, sources):
        form = self._upsert_form(
            "6198", "Form 6198 — At-Risk Limitations",
            ["1040"],
            notes="Limits loss deductions to amount at risk. Applied BEFORE passive activity rules (8582). At shareholder level.",
        )
        self._upsert_facts(form, [
            {"fact_key": "cash_invested", "label": "Cash invested in the activity", "data_type": "decimal", "sort_order": 1},
            {"fact_key": "basis_property_contributed", "label": "Adjusted basis of property contributed", "data_type": "decimal", "sort_order": 2},
            {"fact_key": "personal_liability_debt", "label": "Amounts borrowed for which personally liable", "data_type": "decimal", "sort_order": 3},
            {"fact_key": "qualified_nonrecourse_financing", "label": "Qualified nonrecourse financing (real estate only)", "data_type": "decimal", "sort_order": 4,
             "notes": "IRC 465(b)(6): Qualified nonrecourse financing secured by real property used in the activity."},
            {"fact_key": "income_from_activity", "label": "Income included from the activity (current year)", "data_type": "decimal", "sort_order": 5},
            {"fact_key": "prior_year_at_risk", "label": "At-risk amount at beginning of year", "data_type": "decimal", "sort_order": 6},
            {"fact_key": "distributions_received", "label": "Distributions/withdrawals during year", "data_type": "decimal", "sort_order": 7},
            {"fact_key": "loss_from_activity", "label": "Loss from the activity (current year)", "data_type": "decimal", "sort_order": 8},
            {"fact_key": "at_risk_amount", "label": "At-risk amount at end of year", "data_type": "decimal", "sort_order": 9},
            {"fact_key": "allowable_loss", "label": "Deductible loss (limited to at-risk amount)", "data_type": "decimal", "sort_order": 10},
        ])

        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "At-risk = contributions + personal liability debt", "rule_type": "calculation",
             "formula": "at_risk_amount = cash_invested + basis_property_contributed + personal_liability_debt + qualified_nonrecourse_financing + income_from_activity - distributions_received - prior_losses_allowed",
             "inputs": ["cash_invested", "basis_property_contributed", "personal_liability_debt",
                        "qualified_nonrecourse_financing", "income_from_activity", "distributions_received"],
             "outputs": ["at_risk_amount"], "precedence": 1, "sort_order": 1,
             "description": "IRC 465(b): At-risk amount = cash + basis of contributed property + amounts for which taxpayer is personally liable + qualified nonrecourse financing (real estate)."},
            {"rule_id": "R002", "title": "Nonrecourse debt excluded unless qualified RE financing", "rule_type": "validation",
             "formula": "nonrecourse_debt NOT included in at_risk unless qualified_nonrecourse_financing for real_estate",
             "inputs": ["qualified_nonrecourse_financing"], "outputs": [], "precedence": 0, "sort_order": 2,
             "description": "IRC 465(b)(6): Nonrecourse debt generally NOT at risk. Exception for qualified nonrecourse financing secured by real property."},
            {"rule_id": "R003", "title": "Loss limited to at-risk amount", "rule_type": "calculation",
             "formula": "allowable_loss = min(loss_from_activity, at_risk_amount)",
             "inputs": ["loss_from_activity", "at_risk_amount"], "outputs": ["allowable_loss"],
             "precedence": 2, "sort_order": 3,
             "description": "Loss deduction limited to the amount the taxpayer has at risk. Excess is suspended."},
            {"rule_id": "R004", "title": "Recapture if at-risk drops below zero", "rule_type": "conditional",
             "formula": "if at_risk_amount < 0 then recapture_income = abs(at_risk_amount)",
             "inputs": ["at_risk_amount"], "outputs": [], "precedence": 3, "sort_order": 4,
             "description": "IRC 465(e): If at-risk amount drops below zero, income must be recaptured."},
            {"rule_id": "R005", "title": "Applied BEFORE passive activity limitations", "rule_type": "validation",
             "formula": "at_risk_limitation applied before passive_activity_limitation (ordering)",
             "inputs": [], "outputs": [], "precedence": 0, "sort_order": 5,
             "description": "At-risk limitations (section 465) are applied BEFORE passive activity limitations (section 469). The ordering is: (1) basis, (2) at-risk, (3) passive activity."},
        ])
        self._upsert_links(rules, sources, [
            ("R001", "IRC_465", "primary", "Section 465(b) — amounts at risk"),
            ("R001", "IRS_2025_6198_INSTR", "secondary", "Form 6198 at-risk computation"),
            ("R002", "IRC_465", "primary", "Section 465(b)(6) — qualified nonrecourse financing exception"),
            ("R003", "IRC_465", "primary", "Section 465(a) — loss limited to at-risk amount"),
            ("R004", "IRC_465", "primary", "Section 465(e) — recapture when at-risk goes below zero"),
            ("R005", "IRC_465", "primary", "At-risk before passive activity — ordering rule"),
            ("R005", "IRC_469", "secondary", "Section 469 applies after section 465"),
        ])
        self._upsert_lines(form, [
            {"line_number": "1", "description": "Current year profit (loss) from the activity", "line_type": "input", "sort_order": 1},
            {"line_number": "2", "description": "Prior year unallowed losses", "line_type": "input", "sort_order": 2},
            {"line_number": "3", "description": "Current year overall gain or loss (Line 1 + Line 2)", "line_type": "subtotal", "sort_order": 3},
            {"line_number": "5", "description": "Investment in the activity at the effective date", "line_type": "input", "sort_order": 4},
            {"line_number": "6", "description": "Increases at effective date", "line_type": "input", "sort_order": 5},
            {"line_number": "10", "description": "Decreases at effective date", "line_type": "input", "sort_order": 6},
            {"line_number": "15", "description": "Amount at risk (effective date)", "line_type": "calculated", "source_rules": ["R001"], "sort_order": 7},
            {"line_number": "20", "description": "Deductible loss (limited to at-risk amount)", "line_type": "total", "source_rules": ["R003"], "sort_order": 8},
        ])
        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D001", "title": "Loss exceeds at-risk amount", "severity": "warning",
             "condition": "loss_from_activity > at_risk_amount",
             "message": "Loss exceeds shareholder at-risk amount — excess losses should be suspended and carried forward."},
            {"diagnostic_id": "D002", "title": "Nonrecourse debt in at-risk", "severity": "warning",
             "condition": "qualified_nonrecourse_financing > 0",
             "message": "Nonrecourse financing included in at-risk amount — verify it qualifies as qualified nonrecourse financing for real estate."},
        ])
        self._upsert_tests(form, [
            {"scenario_name": "Standard at-risk — loss within amount", "scenario_type": "normal",
             "inputs": {"cash_invested": 50000, "personal_liability_debt": 30000, "loss_from_activity": 20000,
                        "at_risk_amount": 80000},
             "expected_outputs": {"allowable_loss": 20000},
             "sort_order": 1,
             "notes": "At-risk $80K ($50K cash + $30K personal debt). $20K loss fully allowed."},
            {"scenario_name": "Nonrecourse real estate exception", "scenario_type": "edge",
             "inputs": {"cash_invested": 20000, "qualified_nonrecourse_financing": 180000, "loss_from_activity": 25000,
                        "at_risk_amount": 200000},
             "expected_outputs": {"allowable_loss": 25000},
             "sort_order": 2,
             "notes": "At-risk = $20K cash + $180K qualified nonrecourse RE = $200K. $25K loss fully allowed."},
        ])
        self._upsert_form_links("6198", sources, [
            ("IRS_2025_6198_INSTR", "governs"),
            ("IRC_465", "governs"),
        ])
        self.stdout.write(self.style.SUCCESS("  Form 6198 complete."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Form 3800 — General Business Credit
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_3800(self, sources):
        form = self._upsert_form(
            "3800", "Form 3800 — General Business Credit",
            ["1120S", "1065", "1120", "1040"],
            notes="Aggregates business credits. S-Corp passes credits through to shareholders via K-1 Box 13.",
        )
        self._upsert_facts(form, [
            {"fact_key": "research_credit_41", "label": "Research credit (IRC 41)", "data_type": "decimal", "sort_order": 1},
            {"fact_key": "work_opportunity_credit_51", "label": "Work opportunity credit (IRC 51)", "data_type": "decimal", "sort_order": 2},
            {"fact_key": "small_employer_health_45r", "label": "Small employer health insurance credit (IRC 45R)", "data_type": "decimal", "sort_order": 3},
            {"fact_key": "disabled_access_credit_44", "label": "Disabled access credit (IRC 44)", "data_type": "decimal", "sort_order": 4},
            {"fact_key": "other_business_credits", "label": "Other general business credits", "data_type": "decimal", "sort_order": 5},
            {"fact_key": "total_current_year_credits", "label": "Total current year general business credits", "data_type": "decimal", "sort_order": 6},
            {"fact_key": "carryforward_credits", "label": "Credit carryforward from prior years", "data_type": "decimal", "sort_order": 7},
            {"fact_key": "carryback_credits", "label": "Credit carryback from future years", "data_type": "decimal", "sort_order": 8},
            {"fact_key": "total_credits_available", "label": "Total credits available", "data_type": "decimal", "sort_order": 9},
            {"fact_key": "k1_box13_credits", "label": "Credits flowing to K-1 Box 13 (S-Corp/partnership)", "data_type": "decimal", "sort_order": 10},
            {"fact_key": "net_income_tax", "label": "Net income tax (for credit limitation)", "data_type": "decimal", "sort_order": 11},
            {"fact_key": "tentative_minimum_tax", "label": "Tentative minimum tax", "data_type": "decimal", "sort_order": 12},
        ])

        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "S-Corp passes credits through to shareholders", "rule_type": "routing",
             "formula": "k1_box13_credits = total_current_year_credits (S-Corp does not take credits at entity level)",
             "inputs": ["total_current_year_credits"], "outputs": ["k1_box13_credits"],
             "precedence": 1, "sort_order": 1,
             "description": "S corporations pass business credits through to shareholders on K-1 Box 13 by credit type code. No entity-level credit taken."},
            {"rule_id": "R002", "title": "Carryback 1 year, carryforward 20 years", "rule_type": "validation",
             "formula": "unused credits carryback 1 year, carryforward 20 years",
             "inputs": ["carryforward_credits", "carryback_credits"], "outputs": [],
             "precedence": 0, "sort_order": 2,
             "description": "IRC 39: Unused general business credits carry back 1 year and forward 20 years."},
            {"rule_id": "R003", "title": "Credits reported on K-1 Box 13 by type code", "rule_type": "routing",
             "formula": "each credit type has specific K-1 Box 13 code (R=research, W=work opportunity, etc.)",
             "inputs": ["research_credit_41", "work_opportunity_credit_51", "small_employer_health_45r",
                        "disabled_access_credit_44", "other_business_credits"],
             "outputs": ["k1_box13_credits"], "precedence": 2, "sort_order": 3,
             "description": "Each credit type flows to K-1 Box 13 with a specific type code for the shareholder to claim."},
            {"rule_id": "R004", "title": "Credit limitation formula", "rule_type": "calculation",
             "formula": "credit_allowed = net_income_tax - max(tentative_minimum_tax, 0.25 * max(0, net_regular_tax - 25000))",
             "inputs": ["net_income_tax", "tentative_minimum_tax"], "outputs": [],
             "precedence": 3, "sort_order": 4,
             "description": "Credit limited to net income tax minus greater of TMT or 25% of net regular tax liability over $25K."},
        ])
        self._upsert_links(rules, sources, [
            ("R001", "IRC_1363", "primary", "S-Corp does not take credits at entity level"),
            ("R001", "IRC_38", "secondary", "Section 38 — general business credit components"),
            ("R002", "IRS_2025_3800_INSTR", "primary", "Carryback/carryforward rules"),
            ("R003", "IRS_2025_3800_INSTR", "primary", "K-1 Box 13 credit type codes"),
            ("R004", "IRC_38", "primary", "Section 38(c) — credit limitation formula"),
            ("R004", "IRS_2025_3800_INSTR", "secondary", "Credit limitation computation instructions"),
        ])
        self._upsert_lines(form, [
            {"line_number": "1a", "description": "General business credits from Part I", "line_type": "input", "sort_order": 1},
            {"line_number": "1b", "description": "Passive activity credits from Part II", "line_type": "input", "sort_order": 2},
            {"line_number": "1c", "description": "Total current year general business credits", "line_type": "subtotal", "sort_order": 3},
            {"line_number": "2", "description": "Carryforward of general business credit from prior year(s)", "line_type": "input", "sort_order": 4},
            {"line_number": "3", "description": "Carryback of general business credit (if applicable)", "line_type": "input", "sort_order": 5},
            {"line_number": "4", "description": "Total general business credits", "line_type": "subtotal", "sort_order": 6},
            {"line_number": "5", "description": "Net income tax", "line_type": "input", "sort_order": 7},
            {"line_number": "6", "description": "Tentative minimum tax", "line_type": "input", "sort_order": 8},
            {"line_number": "7", "description": "Net income tax minus tentative minimum tax", "line_type": "calculated", "sort_order": 9},
            {"line_number": "38", "description": "Allowed general business credit", "line_type": "total",
             "source_rules": ["R004"], "destination_form": "K-1 Box 13", "sort_order": 10},
        ])
        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D001", "title": "Credits not flowing to K-1 Box 13", "severity": "warning",
             "condition": "total_current_year_credits > 0 AND k1_box13_credits == 0",
             "message": "Business credits entered but not flowing to K-1 Box 13 for shareholder pass-through."},
            {"diagnostic_id": "D002", "title": "Credit carryforward not tracked", "severity": "warning",
             "condition": "carryforward_credits > 0 AND no_prior_year_tracking",
             "message": "Credit carryforward from prior year not tracked. Verify carryforward amounts."},
        ])
        self._upsert_tests(form, [
            {"scenario_name": "Single credit pass-through to K-1", "scenario_type": "normal",
             "inputs": {"research_credit_41": 15000, "total_current_year_credits": 15000},
             "expected_outputs": {"k1_box13_credits": 15000},
             "sort_order": 1,
             "notes": "$15K R&D credit passes through to shareholders on K-1 Box 13 Code R."},
            {"scenario_name": "Multiple credits", "scenario_type": "normal",
             "inputs": {"research_credit_41": 10000, "work_opportunity_credit_51": 5000,
                        "disabled_access_credit_44": 2500, "total_current_year_credits": 17500},
             "expected_outputs": {"k1_box13_credits": 17500},
             "sort_order": 2,
             "notes": "Three different credits totaling $17.5K all pass through to K-1 Box 13."},
        ])
        self._upsert_form_links("3800", sources, [
            ("IRS_2025_3800_INSTR", "governs"),
            ("IRC_38", "governs"),
        ])
        self.stdout.write(self.style.SUCCESS("  Form 3800 complete."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Schedule M-3 — Net Income Reconciliation for Large Filers
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_m3(self, sources):
        form = self._upsert_form(
            "1120S_M3", "Schedule M-3 (Form 1120-S) — Net Income (Loss) Reconciliation for S Corporations",
            ["1120S"],
            notes="Required when total assets >= $50M. Detailed book-tax reconciliation. Lower priority for Ken's target market.",
        )
        self._upsert_facts(form, [
            {"fact_key": "total_assets_eoy", "label": "Total assets at end of tax year", "data_type": "decimal", "required": True, "sort_order": 1},
            {"fact_key": "net_income_per_books", "label": "Part I — Net income (loss) per financial statements", "data_type": "decimal", "sort_order": 2},
            {"fact_key": "net_income_per_tax_return", "label": "Part I — Net income (loss) per income tax return", "data_type": "decimal", "sort_order": 3},
            {"fact_key": "income_temporary_diff", "label": "Part II — Income items: temporary differences", "data_type": "decimal", "sort_order": 4},
            {"fact_key": "income_permanent_diff", "label": "Part II — Income items: permanent differences", "data_type": "decimal", "sort_order": 5},
            {"fact_key": "income_book_amount", "label": "Part II — Income items: book amount", "data_type": "decimal", "sort_order": 6},
            {"fact_key": "income_tax_amount", "label": "Part II — Income items: per tax return", "data_type": "decimal", "sort_order": 7},
            {"fact_key": "expense_temporary_diff", "label": "Part III — Expense items: temporary differences", "data_type": "decimal", "sort_order": 8},
            {"fact_key": "expense_permanent_diff", "label": "Part III — Expense items: permanent differences", "data_type": "decimal", "sort_order": 9},
            {"fact_key": "expense_book_amount", "label": "Part III — Expense items: book amount", "data_type": "decimal", "sort_order": 10},
            {"fact_key": "expense_tax_amount", "label": "Part III — Expense items: per tax return", "data_type": "decimal", "sort_order": 11},
            {"fact_key": "voluntary_filing", "label": "Filing voluntarily (assets < $50M)?", "data_type": "boolean", "sort_order": 12},
            {"fact_key": "financial_statement_type", "label": "Type of financial statements", "data_type": "choice",
             "choices": ["certified_audited", "compiled", "internal", "sec_10k", "other"], "sort_order": 13},
            {"fact_key": "restatement_indicator", "label": "Financial statements restated for this year?", "data_type": "boolean", "sort_order": 14},
            {"fact_key": "m3_reconciliation_total", "label": "Total reconciliation (book to tax)", "data_type": "decimal", "sort_order": 15},
        ])

        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "Required if total assets >= $50M", "rule_type": "conditional",
             "formula": "if total_assets_eoy >= 50000000 then must_file_m3 = True",
             "inputs": ["total_assets_eoy"], "outputs": ["must_file_m3"], "precedence": 1, "sort_order": 1,
             "description": "Schedule M-3 is required instead of Schedule M-1 when total assets at end of tax year are $50 million or more."},
            {"rule_id": "R002", "title": "Part I — Financial information reconciliation", "rule_type": "calculation",
             "formula": "net_income_per_tax_return = net_income_per_books + temporary_differences + permanent_differences",
             "inputs": ["net_income_per_books", "income_temporary_diff", "income_permanent_diff"],
             "outputs": ["net_income_per_tax_return"], "precedence": 2, "sort_order": 2,
             "description": "Part I reconciles financial statement net income to net income per income tax return."},
            {"rule_id": "R003", "title": "Part II — Income items (book vs tax)", "rule_type": "calculation",
             "formula": "income_tax_amount = income_book_amount + income_temporary_diff + income_permanent_diff",
             "inputs": ["income_book_amount", "income_temporary_diff", "income_permanent_diff"],
             "outputs": ["income_tax_amount"], "precedence": 3, "sort_order": 3,
             "description": "Part II details each income item showing book amount, temporary and permanent differences, and tax return amount."},
            {"rule_id": "R004", "title": "Part III — Expense items (book vs tax)", "rule_type": "calculation",
             "formula": "expense_tax_amount = expense_book_amount + expense_temporary_diff + expense_permanent_diff",
             "inputs": ["expense_book_amount", "expense_temporary_diff", "expense_permanent_diff"],
             "outputs": ["expense_tax_amount"], "precedence": 4, "sort_order": 4,
             "description": "Part III details each expense/deduction item showing book amount, temporary and permanent differences, and tax return amount."},
        ])
        self._upsert_links(rules, sources, [
            ("R001", "IRS_2025_1120S_M3_INSTR", "primary", "M-3 filing threshold: $50M total assets"),
            ("R001", "IRS_2025_1120S_SCHB_INSTR", "secondary", "Schedule B references M-3 threshold"),
            ("R002", "IRS_2025_1120S_M3_INSTR", "primary", "Part I — financial statement reconciliation"),
            ("R003", "IRS_2025_1120S_M3_INSTR", "primary", "Part II — income items"),
            ("R004", "IRS_2025_1120S_M3_INSTR", "primary", "Part III — expense items"),
        ])
        self._upsert_lines(form, [
            {"line_number": "P1-1", "description": "Part I Line 1 — Net income (loss) per financial statements", "line_type": "input", "sort_order": 1},
            {"line_number": "P1-2", "description": "Part I Line 2 — Net income of includible entities not on financial statements", "line_type": "input", "sort_order": 2},
            {"line_number": "P1-3", "description": "Part I Line 3 — Net income of entities on financial statements not included", "line_type": "input", "sort_order": 3},
            {"line_number": "P1-4", "description": "Part I Line 4 — Adjustments to reconcile", "line_type": "input", "sort_order": 4},
            {"line_number": "P1-11", "description": "Part I Line 11 — Net income per income tax return", "line_type": "total", "source_rules": ["R002"], "sort_order": 5},
            {"line_number": "P2-1", "description": "Part II Line 1 — Income (loss) from equity method foreign corps", "line_type": "input", "sort_order": 6},
            {"line_number": "P2-2", "description": "Part II Line 2 — Gross foreign dividends not included in Part I", "line_type": "input", "sort_order": 7},
            {"line_number": "P2-25", "description": "Part II Line 25 — Other income items with differences", "line_type": "input", "sort_order": 8},
            {"line_number": "P2-26", "description": "Part II Line 26 — Total income items", "line_type": "subtotal", "source_rules": ["R003"], "sort_order": 9},
            {"line_number": "P3-1", "description": "Part III Line 1 — U.S. current income tax expense", "line_type": "input", "sort_order": 10},
            {"line_number": "P3-2", "description": "Part III Line 2 — U.S. deferred income tax expense", "line_type": "input", "sort_order": 11},
            {"line_number": "P3-3", "description": "Part III Line 3 — State and local income tax expense", "line_type": "input", "sort_order": 12},
            {"line_number": "P3-33", "description": "Part III Line 33 — Other expense/deduction items with differences", "line_type": "input", "sort_order": 13},
            {"line_number": "P3-34", "description": "Part III Line 34 — Total expense/deduction items", "line_type": "subtotal", "source_rules": ["R004"], "sort_order": 14},
            {"line_number": "P3-35", "description": "Part III Line 35 — Other items with no differences", "line_type": "input", "sort_order": 15},
            {"line_number": "P3-36", "description": "Part III Line 36 — Reconciliation totals", "line_type": "total", "sort_order": 16},
            {"line_number": "P1-FS", "description": "Part I — Type of financial statements", "line_type": "informational", "sort_order": 17},
            {"line_number": "P1-RS", "description": "Part I — Restatement indicator", "line_type": "informational", "sort_order": 18},
            {"line_number": "P2-DEP", "description": "Part II — Depreciation book vs tax differences", "line_type": "input", "sort_order": 19},
            {"line_number": "P3-DEP", "description": "Part III — Depreciation expense differences", "line_type": "input", "sort_order": 20},
        ])
        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D001", "title": "M-3 required but M-1 filed", "severity": "error",
             "condition": "total_assets_eoy >= 50000000 AND filing_m1_instead_of_m3",
             "message": "Total assets >= $50M but filing Schedule M-1 instead of M-3. Schedule M-3 is required."},
            {"diagnostic_id": "D002", "title": "M-3 filed voluntarily", "severity": "info",
             "condition": "total_assets_eoy < 50000000 AND filing_m3",
             "message": "Schedule M-3 filed but total assets < $50M. Voluntary filing is allowed but unusual."},
        ])
        self._upsert_tests(form, [
            {"scenario_name": "Threshold check — M-3 required", "scenario_type": "normal",
             "inputs": {"total_assets_eoy": 75000000},
             "expected_outputs": {"must_file_m3": True},
             "sort_order": 1,
             "notes": "$75M total assets. Above $50M threshold, M-3 required."},
        ])
        self._upsert_form_links("1120S_M3", sources, [
            ("IRS_2025_1120S_M3_INSTR", "governs"),
            ("IRS_2025_1120S_INSTR", "informs"),
        ])
        self.stdout.write(self.style.SUCCESS("  Schedule M-3 complete."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Form 8283 — Noncash Charitable Contributions
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_8283(self, sources):
        form = self._upsert_form(
            "8283", "Form 8283 — Noncash Charitable Contributions",
            ["1120S", "1065", "1040"],
            notes="Required when total noncash charitable contributions > $500. Section A: <= $5K. Section B: > $5K (appraisal required).",
        )
        self._upsert_facts(form, [
            {"fact_key": "total_noncash_contributions", "label": "Total noncash charitable contributions", "data_type": "decimal", "required": True, "sort_order": 1},
            {"fact_key": "section_a_items", "label": "Section A — Items with deduction <= $5,000", "data_type": "decimal", "sort_order": 2},
            {"fact_key": "section_b_items", "label": "Section B — Items with deduction > $5,000", "data_type": "decimal", "sort_order": 3},
            {"fact_key": "donee_organization", "label": "Donee organization name and address", "data_type": "string", "sort_order": 4},
            {"fact_key": "property_description", "label": "Description of donated property", "data_type": "string", "sort_order": 5},
            {"fact_key": "date_contributed", "label": "Date of contribution", "data_type": "date", "sort_order": 6},
            {"fact_key": "date_acquired", "label": "Date property acquired by donor", "data_type": "date", "sort_order": 7},
            {"fact_key": "donor_cost_or_basis", "label": "Donor's cost or adjusted basis", "data_type": "decimal", "sort_order": 8},
            {"fact_key": "fair_market_value", "label": "Fair market value", "data_type": "decimal", "sort_order": 9},
            {"fact_key": "fmv_method", "label": "Method used to determine FMV", "data_type": "string", "sort_order": 10},
        ])

        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "Filing threshold: noncash > $500", "rule_type": "conditional",
             "formula": "if total_noncash_contributions > 500 then form_8283_required = True",
             "inputs": ["total_noncash_contributions"], "outputs": [],
             "precedence": 1, "sort_order": 1,
             "description": "IRC 170(f)(11): Form 8283 required when total noncash charitable contributions exceed $500."},
            {"rule_id": "R002", "title": "Section A: items <= $5,000", "rule_type": "classification",
             "formula": "items with deduction <= 5000 go to Section A (description, FMV, method required)",
             "inputs": ["fair_market_value"], "outputs": [],
             "precedence": 2, "sort_order": 2,
             "description": "Section A covers items (or groups of similar items) with deduction of $5,000 or less."},
            {"rule_id": "R003", "title": "Section B: items > $5,000 — appraisal required", "rule_type": "validation",
             "formula": "items with deduction > 5000 require qualified appraisal (except publicly traded securities)",
             "inputs": ["fair_market_value", "property_description"], "outputs": [],
             "precedence": 3, "sort_order": 3,
             "description": "Section B: Items over $5,000 require qualified appraisal by qualified appraiser. Exception for publicly traded securities."},
            {"rule_id": "R004", "title": "Publicly traded securities — no appraisal needed", "rule_type": "conditional",
             "formula": "if property_type == publicly_traded_securities then appraisal_not_required AND use fmv_on_contribution_date",
             "inputs": ["property_description", "fair_market_value"], "outputs": [],
             "precedence": 2, "sort_order": 4,
             "description": "Publicly traded securities use FMV on date of contribution regardless of amount — no appraisal needed."},
            {"rule_id": "R005", "title": "S-Corp passthrough to K-1 Box 12a", "rule_type": "routing",
             "formula": "charitable_contribution_deduction flows to K-1 Box 12a (S-Corp does not deduct at entity level)",
             "inputs": ["total_noncash_contributions"], "outputs": [],
             "precedence": 4, "sort_order": 5,
             "description": "For S corporations, charitable contributions pass through to shareholders on K-1 Box 12a. Entity still files Form 8283."},
        ])
        self._upsert_links(rules, sources, [
            ("R001", "IRC_170", "primary", "Section 170(f)(11) — noncash contribution substantiation"),
            ("R001", "IRS_2025_8283_INSTR", "secondary", "Form 8283 filing requirement"),
            ("R002", "IRS_2025_8283_INSTR", "primary", "Section A instructions — items <= $5K"),
            ("R003", "IRS_2025_8283_INSTR", "primary", "Section B instructions — items > $5K with appraisal"),
            ("R003", "IRC_170", "secondary", "Section 170(f)(11)(C) — qualified appraisal requirement"),
            ("R004", "IRS_2025_8283_INSTR", "primary", "Publicly traded securities exception"),
            ("R005", "IRC_1366", "primary", "Section 1366 — separately stated items pass through"),
            ("R005", "IRS_2025_8283_INSTR", "secondary", "S-Corp passthrough to K-1 Box 12a"),
        ])
        self._upsert_lines(form, [
            {"line_number": "SA-1", "description": "Section A — Donee organization name and address", "line_type": "input", "sort_order": 1},
            {"line_number": "SA-2", "description": "Section A — Description of donated property", "line_type": "input", "sort_order": 2},
            {"line_number": "SA-3", "description": "Section A — Date of contribution", "line_type": "input", "sort_order": 3},
            {"line_number": "SA-4", "description": "Section A — Date acquired by donor", "line_type": "input", "sort_order": 4},
            {"line_number": "SA-5", "description": "Section A — Donor's cost or adjusted basis", "line_type": "input", "sort_order": 5},
            {"line_number": "SA-6", "description": "Section A — Fair market value", "line_type": "input", "sort_order": 6},
            {"line_number": "SA-7", "description": "Section A — Method used to determine FMV", "line_type": "input", "sort_order": 7},
            {"line_number": "SB-1", "description": "Section B — Donee acknowledgement and appraisal summary", "line_type": "input", "sort_order": 8},
        ])
        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D001", "title": "Noncash > $500 without Form 8283", "severity": "warning",
             "condition": "total_noncash_contributions > 500 AND no_form_8283",
             "message": "Noncash charitable contributions exceed $500 but no Form 8283 attached."},
            {"diagnostic_id": "D002", "title": "Item > $5,000 — verify appraisal", "severity": "warning",
             "condition": "section_b_items > 0",
             "message": "Item(s) over $5,000 — verify that a qualified appraisal was obtained (unless publicly traded securities)."},
            {"diagnostic_id": "D003", "title": "Vehicle/art/collectible donation", "severity": "warning",
             "condition": "property_type in (vehicle, art, collectible)",
             "message": "Vehicle, art, or collectible donation — special rules may apply (Form 1098-C for vehicles, appraisal for art > $20K)."},
        ])
        self._upsert_tests(form, [
            {"scenario_name": "Section A items — under $5K", "scenario_type": "normal",
             "inputs": {"total_noncash_contributions": 3000, "section_a_items": 3000, "section_b_items": 0,
                        "property_description": "Office furniture", "fair_market_value": 3000, "donor_cost_or_basis": 5000},
             "expected_outputs": {"form_8283_required": True, "section": "A", "appraisal_required": False},
             "sort_order": 1,
             "notes": "$3K noncash > $500. All items under $5K, so Section A. No appraisal needed."},
            {"scenario_name": "Section B items — over $5K with appraisal", "scenario_type": "normal",
             "inputs": {"total_noncash_contributions": 25000, "section_a_items": 2000, "section_b_items": 23000,
                        "property_description": "Commercial equipment", "fair_market_value": 23000},
             "expected_outputs": {"form_8283_required": True, "section": "B", "appraisal_required": True},
             "sort_order": 2,
             "notes": "$23K item goes to Section B. Qualified appraisal required."},
        ])
        self._upsert_form_links("8283", sources, [
            ("IRS_2025_8283_INSTR", "governs"),
            ("IRC_170", "governs"),
        ])
        self.stdout.write(self.style.SUCCESS("  Form 8283 complete."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Report
    # ═══════════════════════════════════════════════════════════════════════════

    def _report_totals(self):
        def _safe(text):
            return text.encode("ascii", errors="replace").decode("ascii")

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("DATABASE TOTALS (after load_1120s_complete)")
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
        self.stdout.write(self.style.SUCCESS("Session 11: 1120-S complete package loaded successfully."))
