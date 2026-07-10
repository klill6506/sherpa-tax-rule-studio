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
                "excerpt_label": "Schedule B — 2025 face question list (verified vs f1120s.pdf 2025)",
                "excerpt_text": (
                    "Schedule B (Form 1120-S 2025), Other Information, pages 2-3 of the form. "
                    "Questions on the 2025 face: 1 — check accounting method (cash / accrual / other); "
                    "2 — business activity and product or service; 3 — any shareholder a disregarded "
                    "entity, trust, estate, or nominee (if Yes, attach Schedule B-1); 4a/4b — 20%/50% "
                    "ownership of any corporation / partnership; 5a/5b — outstanding restricted stock / "
                    "stock options, warrants, or similar instruments; 6 — Form 8918 material advisor "
                    "disclosure; 7 — checkbox, publicly offered debt instruments with OID; 8 — net "
                    "unrealized built-in gain in excess of prior-year recognized built-in gain (dollar "
                    "entry); 9 — section 163(j) real-property/farming election; 10 — Form 8990 "
                    "conditions (pass-through EBIE / $31M gross receipts / tax shelter); 11 — total "
                    "receipts AND total assets both under $250,000 (see the Question 11 excerpt); "
                    "12 — non-shareholder debt cancelled, forgiven, or modified (plus principal "
                    "reduction amount); 13 — QSub election terminated or revoked; 14a/14b — Form(s) "
                    "1099 required / filed; 15 — Qualified Opportunity Fund self-certification (plus "
                    "Form 8996 line 15 amount); 16 — digital assets received or disposed; 17 — "
                    "reserved for future use. (This excerpt SUPERSEDES the pre-2026-07-09 paraphrase "
                    "that carried a stale, non-face numbering — e.g. an 'AE&P' question 11 that does "
                    "not exist on the 2025 Schedule B.)"
                ),
                "summary_text": "2025 Schedule B face: questions 1-17 as printed (Q11 = the $250K receipts+assets test).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Question 11 — face text and total receipts definition (verbatim)",
                "excerpt_text": (
                    "Form 1120-S (2025) Schedule B, question 11 (face, verbatim): 'Does the "
                    "corporation satisfy both of the following conditions? a. The corporation's "
                    "total receipts (see instructions) for the tax year were less than $250,000. "
                    "b. The corporation's total assets at the end of the tax year were less than "
                    "$250,000. If “Yes,” the corporation is not required to complete "
                    "Schedules L and M-1.' Instructions for Form 1120-S (2025), Question 11 "
                    "(verbatim): 'Total receipts is the sum of the following amounts. • Gross "
                    "receipts or sales (page 1, line 1a). • All other income (page 1, lines 4 "
                    "and 5). • Income reported on Schedule K, lines 3a, 4, 5a, and 6. • "
                    "Income or net gain reported on Schedule K, lines 7, 8a, 9, and 10. • "
                    "Income or net gain reported on Form 8825, lines 2, 21, and 22a.'"
                ),
                "summary_text": "Q11 verbatim: both receipts AND EOY assets < $250K; total-receipts component list from the 2025 instructions.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule B — M-3 threshold and accounting method",
                "excerpt_text": (
                    "Instructions for Form 1120-S (2025), p.49 (verbatim): 'Corporations with total "
                    "assets of $10 million or more on the last day of the tax year must file "
                    "Schedule M-3 (Form 1120-S) instead of Schedule M-1.' (The pre-2026-07-09 "
                    "paraphrase said $50 million — a tax-law error.) The accounting method reported "
                    "on Schedule B question 1 must be consistent with the method used throughout "
                    "the return; a method change requires Form 3115."
                ),
                "summary_text": "M-3 required if total assets >= $10M (i1120s p.49 verbatim). Accounting method must be consistent.",
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
                    "Instructions for Form 1120-S (2025), p.49 (verbatim): 'Corporations with total "
                    "assets of $10 million or more on the last day of the tax year must file "
                    "Schedule M-3 (Form 1120-S) instead of Schedule M-1.' And from the Schedule M-1 "
                    "instructions (same page, verbatim): 'A corporation filing Form 1120-S that "
                    "isn't required to file Schedule M-3 may voluntarily file Schedule M-3 instead "
                    "of Schedule M-1.' (The pre-2026-07-09 paraphrase carried a $50 million "
                    "threshold — a tax-law error corrected in the retrospective-B face audit.) "
                    "Structure: Part I reconciles financial statement net income; Parts II/III "
                    "detail income and expense items in book / temporary difference / permanent "
                    "difference / tax return columns. ⚠ The M-3 face PDF is not yet in the template "
                    "repo — Part/line numbering in this spec is UNVERIFIED against the face."
                ),
                "summary_text": "M-3 required if assets >= $10M (i1120s 2025 p.49 verbatim); voluntary below. Line numbering unverified pending the face template.",
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
            self._load_6198(sources)
            self._load_3800(sources)
            self._load_m3(sources)
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
        # 2026-07-09 RENUMBERED TO THE 2025 FACE (verified verbatim vs
        # f1120s.pdf 2025 pages 2-3). The original block carried a stale,
        # non-face numbering (~20 questions incl. an "AE&P" B11 that does not
        # exist on the 2025 Schedule B). Stale fact/line rows are DELETED
        # in-loader below (update_or_create can't remove rows — the F4797-G2
        # lesson). Same session: NEW R006, the Question 11 auto-answer
        # (Ken ruling 2026-07-09, tts usability item 12).
        form = self._upsert_form(
            "1120S_SCHB", "Schedule B (Form 1120-S) — Other Information",
            ["1120S"],
            notes="Pages 2-3 of the 2025 Form 1120-S. Questions 1-16 (+17 reserved) as printed "
                  "on the 2025 face. Q1/Q2 (accounting method, activity/product) live on the "
                  "return header in implementations; Q3-Q16 are the yes/no + amount items.",
        )
        self._upsert_facts(form, [
            # ── 2025 face questions ──
            {"fact_key": "b1_accounting_method", "label": "Q1 — Accounting method (cash / accrual / other)", "data_type": "choice",
             "choices": ["cash", "accrual", "other"], "required": True, "sort_order": 1},
            {"fact_key": "b2_business_activity", "label": "Q2a — Business activity", "data_type": "string", "sort_order": 2},
            {"fact_key": "b2_product_service", "label": "Q2b — Product or service", "data_type": "string", "sort_order": 3},
            {"fact_key": "b3_nominee_shareholder", "label": "Q3 — Any shareholder a disregarded entity, trust, estate, or nominee? (Yes → Schedule B-1)", "data_type": "boolean", "sort_order": 4},
            {"fact_key": "b4a_own_corp_20_50", "label": "Q4a — Own 20% directly / 50% directly-or-indirectly of any corporation?", "data_type": "boolean", "sort_order": 5},
            {"fact_key": "b4b_own_pship_20_50", "label": "Q4b — Own 20% directly / 50% directly-or-indirectly of any partnership or trust?", "data_type": "boolean", "sort_order": 6},
            {"fact_key": "b5a_restricted_stock", "label": "Q5a — Outstanding shares of restricted stock at year end?", "data_type": "boolean", "sort_order": 7},
            {"fact_key": "b5b_options_warrants", "label": "Q5b — Outstanding stock options, warrants, or similar instruments at year end?", "data_type": "boolean", "sort_order": 8},
            {"fact_key": "b6_form_8918", "label": "Q6 — Filed or required to file Form 8918 (material advisor disclosure)?", "data_type": "boolean", "sort_order": 9},
            {"fact_key": "b7_public_oid_debt", "label": "Q7 — Checkbox: issued publicly offered debt instruments with OID", "data_type": "boolean", "sort_order": 10},
            {"fact_key": "b8_nubig_amount", "label": "Q8 — Net unrealized built-in gain over prior-year recognized built-in gain ($)", "data_type": "decimal", "sort_order": 11},
            {"fact_key": "b9_163j_election", "label": "Q9 — Section 163(j) real-property/farming election in effect?", "data_type": "boolean", "sort_order": 12},
            {"fact_key": "b10_form_8990_test", "label": "Q10 — Satisfies one or more Form 8990 conditions (pass-through EBIE / $31M receipts / tax shelter)?", "data_type": "boolean", "sort_order": 13},
            {"fact_key": "b11_under_250k", "label": "Q11 — Total receipts < $250,000 AND EOY total assets < $250,000? (DERIVED, overridable)", "data_type": "boolean", "sort_order": 14,
             "notes": "Auto-answered by R006 (Ken ruling 2026-07-09). YELLOW derived value; a preparer override always wins."},
            {"fact_key": "b12_debt_forgiven", "label": "Q12 — Non-shareholder debt cancelled, forgiven, or modified?", "data_type": "boolean", "sort_order": 15},
            {"fact_key": "b12_principal_reduction", "label": "Q12 — Amount of principal reduction ($)", "data_type": "decimal", "sort_order": 16},
            {"fact_key": "b13_qsub_terminated", "label": "Q13 — QSub election terminated or revoked during the year?", "data_type": "boolean", "sort_order": 17},
            {"fact_key": "b14a_1099_required", "label": "Q14a — Payments made that require Form(s) 1099?", "data_type": "boolean", "sort_order": 18},
            {"fact_key": "b14b_1099_filed", "label": "Q14b — If Yes, did/will the corporation file the required Form(s) 1099?", "data_type": "boolean", "sort_order": 19},
            {"fact_key": "b15_qof", "label": "Q15 — Intends to self-certify as a Qualified Opportunity Fund (attach Form 8996)?", "data_type": "boolean", "sort_order": 20},
            {"fact_key": "b15_8996_penalty", "label": "Q15 — Form 8996 line 15 amount ($)", "data_type": "decimal", "sort_order": 21},
            {"fact_key": "b16_digital_assets", "label": "Q16 — Received or disposed of a digital asset (or financial interest in one)?", "data_type": "boolean", "sort_order": 22},
            # ── Q11 derivation inputs ──
            {"fact_key": "q11_total_receipts", "label": "Q11 — Total receipts (derived per the Question 11 instruction definition)", "data_type": "decimal", "sort_order": 23,
             "notes": "Sum: page 1 line 1a; page 1 lines 4 and 5; Schedule K lines 3a, 4, 5a, 6; "
                      "Schedule K lines 7, 8a, 9, 10 (income or net gain only); Form 8825 lines 2, 21, 22a "
                      "(income or net gain only)."},
            {"fact_key": "l15_total_assets_eoy", "label": "Total assets at end of year (Schedule L line 15, EOY column — cross-form)", "data_type": "decimal", "sort_order": 24},
            # ── practice facts (NOT 2025 Schedule B face questions) ──
            {"fact_key": "aep_from_ccorp", "label": "Practice — outstanding AE&P from C-Corp years (not a 2025 Sch B question)", "data_type": "boolean", "sort_order": 25,
             "notes": "Kept for the §1375 practice rule R004. The pre-2026-07-09 spec mislabeled this as face question 11."},
            {"fact_key": "excess_net_passive_income", "label": "Practice — excess net passive income present (§1375)", "data_type": "boolean", "sort_order": 26},
            {"fact_key": "shareholder_count", "label": "Practice — number of shareholders (page 1, item I — not a Sch B question)", "data_type": "integer", "sort_order": 27},
            {"fact_key": "actual_shareholder_count", "label": "Practice — actual number of shareholder records entered in the return", "data_type": "integer", "sort_order": 28,
             "notes": "Cross-check against page 1 item I."},
        ])

        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "Accounting method consistency", "rule_type": "validation",
             "formula": "b1_accounting_method must match method used on Page 1",
             "inputs": ["b1_accounting_method"], "outputs": [], "precedence": 1, "sort_order": 1,
             "description": "Accounting method on Schedule B question 1 must be consistent with the method used throughout the return."},
            {"rule_id": "R002", "title": "Shareholder count cross-check (page 1 item I)", "rule_type": "validation",
             "formula": "shareholder_count == actual_shareholder_count",
             "inputs": ["shareholder_count", "actual_shareholder_count"], "outputs": [], "precedence": 2, "sort_order": 2,
             "description": "PRACTICE RULE — the shareholder count lives on page 1 item I of the 2025 face "
                            "(not on Schedule B; the pre-2026-07-09 spec misplaced it here as 'B3'). It should "
                            "match the number of K-1s prepared."},
            {"rule_id": "R003", "title": "M-3 filing threshold", "rule_type": "conditional",
             "formula": "if l15_total_assets_eoy >= 10000000 then must_file_m3 = True",
             "inputs": ["l15_total_assets_eoy"], "outputs": ["must_file_m3"], "precedence": 3, "sort_order": 3,
             "description": "If total assets on the last day of the tax year are $10 MILLION or more, "
                            "Schedule M-3 is required instead of Schedule M-1 (i1120s 2025 p.49 verbatim; "
                            "corrected 2026-07-09 — the prior spec's $50M was a tax-law error; not a "
                            "Schedule B face question)."},
            {"rule_id": "R004", "title": "Section 1375 passive income tax trigger", "rule_type": "conditional",
             "formula": "if aep_from_ccorp AND excess_net_passive_income then section_1375_tax_applies",
             "inputs": ["aep_from_ccorp", "excess_net_passive_income"], "outputs": [], "precedence": 4, "sort_order": 4,
             "description": "PRACTICE RULE — §1375 tax applies when the S corporation has AE&P from C-Corp "
                            "years AND excess net passive income. (AE&P is not a 2025 Schedule B face question.)"},
            {"rule_id": "R005", "title": "100-shareholder limit check", "rule_type": "validation",
             "formula": "shareholder_count <= 100",
             "inputs": ["shareholder_count"], "outputs": [], "precedence": 5, "sort_order": 5,
             "description": "S corporations cannot have more than 100 shareholders (family members may elect to be treated as one)."},
            {"rule_id": "R006", "title": "Question 11 auto-answer (derived, overridable)", "rule_type": "calculation",
             "formula": "b11_under_250k = (q11_total_receipts < 250000) AND (l15_total_assets_eoy < 250000). "
                        "q11_total_receipts = p1_1a + p1_4 + p1_5 + K3a + K4 + K5a + K6 + K7 + K8a + K9 + K10 "
                        "+ f8825_2 + f8825_21 + f8825_22a, where the 'income or net gain' components "
                        "(K7/K8a/K9/K10, 8825 21/22a) and the 'all other income' components (p1 4/5) enter "
                        "only when positive — losses are excluded.",
             "inputs": ["q11_total_receipts", "l15_total_assets_eoy"], "outputs": ["b11_under_250k"],
             "precedence": 6, "sort_order": 6,
             "description": "Ken ruling 2026-07-09 (usability item 12): question 11 is AUTO-ANSWERED from "
                            "return context — a DERIVED value (YELLOW) the preparer can override; an "
                            "override always wins and is never recomputed over. SCHEDULE L AND M-1 BEHAVIOR "
                            "IS UNCHANGED: the derived Yes answers the face question only — it does NOT "
                            "suppress Schedule L/M-1 computation, printing, or balance diagnostics "
                            "(1120S_SCHL R007 remains the separate statement of the filing exception). "
                            "Component definition per the Instructions for Form 1120-S (2025), Question 11 "
                            "(see the verbatim excerpt). INTERPRETIVE NOTE: the instruction wording "
                            "'income or net gain' is read as include-only-when-positive; 'all other income "
                            "(page 1, lines 4 and 5)' is read the same way. Implementations that do not "
                            "capture Schedule K line 3a gross (only the 3c net) may substitute the net "
                            "when positive — an understatement flagged for review.",
             "notes": "TY2026 re-verify: thresholds are statutory-instruction values ($250,000) — confirm on the 2026 face."},
        ])
        self._upsert_links(rules, sources, [
            ("R001", "IRS_2025_1120S_SCHB_INSTR", "primary", "Accounting method consistency requirement"),
            ("R002", "IRS_2025_1120S_INSTR_FULL", "secondary", "Page 1 item I shareholder count vs K-1s (practice cross-check)"),
            ("R003", "IRS_2025_1120S_M3_INSTR", "primary", "M-3 threshold: $50M total assets"),
            ("R004", "IRC_1374", "primary", "Section 1375 tax on excess net passive income with AE&P"),
            ("R005", "IRC_1361", "primary", "100-shareholder limit for S-Corp eligibility"),
            ("R006", "IRS_2025_1120S_SCHB_INSTR", "primary", "Q11 face text + total-receipts definition (verbatim excerpt)"),
        ])
        self._upsert_lines(form, [
            {"line_number": "B1", "description": "Check accounting method: cash / accrual / other (specify)", "line_type": "input", "sort_order": 1},
            {"line_number": "B2a", "description": "Business activity", "line_type": "input", "sort_order": 2},
            {"line_number": "B2b", "description": "Product or service", "line_type": "input", "sort_order": 3},
            {"line_number": "B3", "description": "Any shareholder a disregarded entity, trust, estate, or nominee? (Yes → attach Schedule B-1)", "line_type": "input", "sort_order": 4},
            {"line_number": "B4a", "description": "Own directly 20% or more, or directly/indirectly 50% or more, of any corporation? (complete (i)-(v))", "line_type": "input", "sort_order": 5},
            {"line_number": "B4b", "description": "Own directly 20% or more, or directly/indirectly 50% or more, of any partnership or beneficial interest of a trust? (complete (i)-(v))", "line_type": "input", "sort_order": 6},
            {"line_number": "B5a", "description": "Outstanding shares of restricted stock at year end? (if Yes: (i) restricted, (ii) non-restricted share counts)", "line_type": "input", "sort_order": 7},
            {"line_number": "B5b", "description": "Outstanding stock options, warrants, or similar instruments at year end? (if Yes: (i) shares outstanding, (ii) fully-diluted)", "line_type": "input", "sort_order": 8},
            {"line_number": "B6", "description": "Filed, or required to file, Form 8918 (Material Advisor Disclosure Statement)?", "line_type": "input", "sort_order": 9},
            {"line_number": "B7", "description": "Checkbox: issued publicly offered debt instruments with original issue discount (may need Form 8281)", "line_type": "input", "sort_order": 10},
            {"line_number": "B8", "description": "Net unrealized built-in gain reduced by net recognized built-in gain from prior years ($ entry)", "line_type": "input", "sort_order": 11},
            {"line_number": "B9", "description": "Section 163(j) election for real property trade/business or farming in effect?", "line_type": "input", "sort_order": 12},
            {"line_number": "B10", "description": "Satisfies one or more Form 8990 conditions (a) pass-through EBIE (b) $31M gross receipts (c) tax shelter? (Yes → attach Form 8990)", "line_type": "input", "sort_order": 13},
            {"line_number": "B11", "description": "Both conditions: (a) total receipts < $250,000 AND (b) EOY total assets < $250,000? (Yes → Schedules L and M-1 not required)", "line_type": "input", "source_rules": ["R006"], "sort_order": 14,
             "notes": "DERIVED default (R006) — YELLOW, preparer-overridable. Answering Yes does not change Schedule L/M-1 behavior in the implementation (Ken ruling 2026-07-09)."},
            {"line_number": "B12", "description": "Non-shareholder debt cancelled, forgiven, or modified to reduce principal?", "line_type": "input", "sort_order": 15},
            {"line_number": "B12_amount", "description": "If Yes, amount of principal reduction ($)", "line_type": "input", "sort_order": 16},
            {"line_number": "B13", "description": "QSub election terminated or revoked during the year?", "line_type": "input", "sort_order": 17},
            {"line_number": "B14a", "description": "Payments made that would require Form(s) 1099?", "line_type": "input", "sort_order": 18},
            {"line_number": "B14b", "description": "If Yes, did or will the corporation file required Form(s) 1099?", "line_type": "input", "sort_order": 19},
            {"line_number": "B15", "description": "Intends to self-certify as a Qualified Opportunity Fund? (Yes → attach Form 8996)", "line_type": "input", "sort_order": 20},
            {"line_number": "B15_amount", "description": "Form 8996 line 15 amount ($)", "line_type": "input", "sort_order": 21},
            {"line_number": "B16", "description": "Received (reward/award/payment) or sold/exchanged/disposed of a digital asset (or financial interest)?", "line_type": "input", "sort_order": 22},
            {"line_number": "B17", "description": "Reserved for future use", "line_type": "informational", "sort_order": 23},
        ])
        # In-loader stale-row DELETE — the pre-2026-07-09 numbering left rows
        # (B2, B4, B5, B18-B20 lines; b3_shareholder_count-style facts) that
        # update_or_create cannot remove and that contradict the 2025 face.
        _2025_B_LINES = {"B1", "B2a", "B2b", "B3", "B4a", "B4b", "B5a", "B5b", "B6", "B7",
                         "B8", "B9", "B10", "B11", "B12", "B12_amount", "B13", "B14a",
                         "B14b", "B15", "B15_amount", "B16", "B17"}
        stale_lines = FormLine.objects.filter(tax_form=form).exclude(line_number__in=_2025_B_LINES)
        if stale_lines.exists():
            self.stdout.write(f"  deleting {stale_lines.count()} stale pre-2025-face line rows")
            stale_lines.delete()
        _2025_B_FACTS = {
            "b1_accounting_method", "b2_business_activity", "b2_product_service",
            "b3_nominee_shareholder", "b4a_own_corp_20_50", "b4b_own_pship_20_50",
            "b5a_restricted_stock", "b5b_options_warrants", "b6_form_8918",
            "b7_public_oid_debt", "b8_nubig_amount", "b9_163j_election",
            "b10_form_8990_test", "b11_under_250k", "b12_debt_forgiven",
            "b12_principal_reduction", "b13_qsub_terminated", "b14a_1099_required",
            "b14b_1099_filed", "b15_qof", "b15_8996_penalty", "b16_digital_assets",
            "q11_total_receipts", "l15_total_assets_eoy",
            "aep_from_ccorp", "excess_net_passive_income",
            "shareholder_count", "actual_shareholder_count",
        }
        stale_facts = FormFact.objects.filter(tax_form=form).exclude(fact_key__in=_2025_B_FACTS)
        if stale_facts.exists():
            self.stdout.write(f"  deleting {stale_facts.count()} stale fact rows")
            stale_facts.delete()

        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D001", "title": "AE&P without tracking", "severity": "warning",
             "condition": "aep_from_ccorp == True AND no_aep_tracking_module",
             "message": "AE&P from C-Corp years is present but no AE&P tracking is set up."},
            {"diagnostic_id": "D002", "title": "Built-in gain without computation", "severity": "warning",
             "condition": "b8_nubig_amount > 0 AND no_section_1374_computation",
             "message": "Question 8 reports net unrealized built-in gain but no Section 1374 computation found."},
            {"diagnostic_id": "D003", "title": "1099 non-compliance", "severity": "warning",
             "condition": "b14a_1099_required == True AND b14b_1099_filed == False",
             "message": "Question 14a answered Yes but 14b answered No — required Form(s) 1099 not filed. Compliance risk."},
            {"diagnostic_id": "D004", "title": "Shareholder count mismatch", "severity": "error",
             "condition": "shareholder_count != actual_shareholder_count",
             "message": "Page 1 item I shareholder count does not match the actual number of shareholders entered."},
        ])
        self._upsert_tests(form, [
            {"scenario_name": "Standard S-Corp — all standard answers", "scenario_type": "normal",
             "inputs": {"b1_accounting_method": "cash", "shareholder_count": 2,
                        "b14a_1099_required": True, "b14b_1099_filed": True,
                        "aep_from_ccorp": False, "b8_nubig_amount": 0,
                        "l15_total_assets_eoy": 400000, "actual_shareholder_count": 2},
             "expected_outputs": {"must_file_m3": False, "shareholder_count_matches": True}, "sort_order": 1},
            {"scenario_name": "C-Corp conversion scenario", "scenario_type": "edge",
             "inputs": {"b1_accounting_method": "accrual", "shareholder_count": 1,
                        "aep_from_ccorp": True, "b8_nubig_amount": 120000,
                        "l15_total_assets_eoy": 400000, "actual_shareholder_count": 1},
             "expected_outputs": {"must_file_m3": False, "aep_tracking_required": True, "big_tax_applies": True}, "sort_order": 2},
            {"scenario_name": "Large entity — M-3 required", "scenario_type": "edge",
             "inputs": {"shareholder_count": 50, "l15_total_assets_eoy": 75000000,
                        "actual_shareholder_count": 50},
             "expected_outputs": {"must_file_m3": True}, "sort_order": 3},
            {"scenario_name": "Q11 auto-answer — small corp (Yes)", "scenario_type": "normal",
             "inputs": {"q11_total_receipts": 180000, "l15_total_assets_eoy": 90000},
             "expected_outputs": {"b11_under_250k": True}, "sort_order": 4,
             "notes": "R006: both under $250,000 → derived Yes. Schedule L/M-1 computation unchanged."},
            {"scenario_name": "Q11 auto-answer — assets at threshold (No)", "scenario_type": "edge",
             "inputs": {"q11_total_receipts": 249999, "l15_total_assets_eoy": 250000},
             "expected_outputs": {"b11_under_250k": False}, "sort_order": 5,
             "notes": "R006: 'less than' is strict — assets exactly $250,000 fail condition (b)."},
        ])
        self._upsert_form_links("1120S_SCHB", sources, [
            ("IRS_2025_1120S_SCHB_INSTR", "governs"),
            ("IRS_2025_1120S_INSTR", "informs"),
        ])
        self.stdout.write(self.style.SUCCESS("  Schedule B complete (2025 face + R006 Q11 auto-answer)."))

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
            {"fact_key": "f1125a_boy_inventory", "label": "Form 1125-A line 1 beginning inventory (cross-form, for the R008 no-prior-year default)", "data_type": "decimal", "sort_order": 51},
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
             "description": "L3 inventories BOY should equal prior year L3 inventories EOY. "
                            "(When no prior-year return exists, R008 supplies the default.)"},
            {"rule_id": "R007", "title": "Small corporation exception", "rule_type": "conditional",
             "formula": "schedule_l_not_required = (total_receipts < 250000 AND l14_total_assets_eoy < 250000)",
             "inputs": ["total_receipts", "l14_total_assets_eoy"], "outputs": ["schedule_l_not_required"], "precedence": 0, "sort_order": 7,
             "description": "Schedule L not required if total receipts < $250K AND total assets < $250K."},
            {"rule_id": "R008", "title": "BOY inventory default when no prior-year return", "rule_type": "conditional",
             "formula": "IF no prior-year return prepared AND l3_inventories_boy is blank "
                        "THEN l3_inventories_boy defaults to f1125a_boy_inventory (fill-blank-only; preparer entry always wins)",
             "inputs": ["f1125a_boy_inventory"], "outputs": ["l3_inventories_boy"], "precedence": 7, "sort_order": 8,
             "description": "Ken ruling 2026-07-09: BOY inventory normally carries from the prior-year EOY (R006). "
                            "Only when no prior-year return was prepared does BOY inventory default from Form "
                            "1125-A line 1 (beginning inventory). Fill-blank-only — never overwrites a preparer "
                            "entry; the preparer may change or clear it."},
        ])
        self._upsert_links(rules, sources, [
            ("R001", "IRS_2025_1120S_SCHL_INSTR", "primary", "Asset line summation"),
            ("R002", "IRS_2025_1120S_SCHL_INSTR", "primary", "Liability line summation"),
            ("R003", "IRS_2025_1120S_SCHL_INSTR", "primary", "L&SE = liabilities + equity"),
            ("R004", "IRS_2025_1120S_SCHL_INSTR", "primary", "L14 must equal L27"),
            ("R005", "IRS_2025_1120S_SCHL_INSTR", "primary", "L24 ties to M-2 ending balance"),
            ("R006", "IRS_2025_1120S_INSTR", "secondary", "BOY should equal prior year EOY"),
            ("R007", "IRS_2025_1120S_SCHL_INSTR", "primary", "Small corp exception: <$250K receipts AND assets"),
            ("R008", "IRS_2025_1120S_SCHL_INSTR", "secondary",
             "Line 3 = inventories per the instructions; the no-prior-year default from 1125-A line 1 "
             "is practice logic (Ken ruling 2026-07-09)"),
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
            notes="Required when total assets >= $10 MILLION (i1120s 2025 p.49 verbatim: 'Corporations "
                  "with total assets of $10 million or more on the last day of the tax year must file "
                  "Schedule M-3 (Form 1120-S) instead of Schedule M-1.'). The pre-2026-07-09 spec said "
                  "$50M — a tax-law error corrected in the retrospective-B face audit. Detailed book-tax "
                  "reconciliation. Lower priority for Ken's target market. ⚠ line_map is UNVERIFIED "
                  "against the M-3 face (no f1120ssm3 template in the repo) — treat P1-*/P2-*/P3-* "
                  "numbering as suspect until the face is downloaded and audited (2026-07-09 ledger).",
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
            {"fact_key": "voluntary_filing", "label": "Filing voluntarily (assets < $10M)?", "data_type": "boolean", "sort_order": 12},
            {"fact_key": "financial_statement_type", "label": "Type of financial statements", "data_type": "choice",
             "choices": ["certified_audited", "compiled", "internal", "sec_10k", "other"], "sort_order": 13},
            {"fact_key": "restatement_indicator", "label": "Financial statements restated for this year?", "data_type": "boolean", "sort_order": 14},
            {"fact_key": "m3_reconciliation_total", "label": "Total reconciliation (book to tax)", "data_type": "decimal", "sort_order": 15},
        ])

        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "Required if total assets >= $10M", "rule_type": "conditional",
             "formula": "if total_assets_eoy >= 10000000 then must_file_m3 = True",
             "inputs": ["total_assets_eoy"], "outputs": ["must_file_m3"], "precedence": 1, "sort_order": 1,
             "description": "Schedule M-3 is required instead of Schedule M-1 when total assets on the "
                            "last day of the tax year are $10 MILLION or more (i1120s 2025 p.49 verbatim; "
                            "corrected 2026-07-09 from the prior spec's erroneous $50M — the tts engine "
                            "was already correct at $10M in rules_entity_boundary/rules_1065_l)."},
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
            ("R001", "IRS_2025_1120S_M3_INSTR", "primary", "M-3 filing threshold: $10M total assets (i1120s 2025 p.49)"),
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
             "condition": "total_assets_eoy >= 10000000 AND filing_m1_instead_of_m3",
             "message": "Total assets >= $10 million but filing Schedule M-1 instead of M-3. Schedule M-3 is required (i1120s 2025 p.49)."},
            {"diagnostic_id": "D002", "title": "M-3 filed voluntarily", "severity": "info",
             "condition": "total_assets_eoy < 10000000 AND filing_m3",
             "message": "Schedule M-3 filed but total assets < $10 million. Voluntary filing is allowed (i1120s: a corporation not required to file M-3 may do so instead of M-1)."},
        ])
        self._upsert_tests(form, [
            {"scenario_name": "Threshold check — M-3 required", "scenario_type": "normal",
             "inputs": {"total_assets_eoy": 75000000},
             "expected_outputs": {"must_file_m3": True},
             "sort_order": 1,
             "notes": "$75M total assets — above the $10M threshold, M-3 required."},
            {"scenario_name": "Threshold check — $12M filer (the $10M-$50M band)", "scenario_type": "edge",
             "inputs": {"total_assets_eoy": 12000000},
             "expected_outputs": {"must_file_m3": True},
             "sort_order": 2,
             "notes": "The band the pre-2026-07-09 $50M threshold silently mis-gated: a $12M filer "
                      "MUST file M-3 per i1120s 2025 p.49."},
        ])
        self._upsert_form_links("1120S_M3", sources, [
            ("IRS_2025_1120S_M3_INSTR", "governs"),
            ("IRS_2025_1120S_INSTR", "informs"),
        ])
        self.stdout.write(self.style.SUCCESS("  Schedule M-3 complete."))

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
