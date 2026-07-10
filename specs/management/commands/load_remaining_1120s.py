"""Load remaining 1120-S family forms + GA-600S state return specs.

Session 10: Builds specs for forms NOT covered by Sessions 8-9:
  - Form 4562 expansion (Section 179, bonus, MACRS details)
  - Form 1125-A (Cost of Goods Sold)
  - Form 1125-E (Compensation of Officers)
  - Form 8825 (Rental Real Estate Income and Expenses)
  - Form 7203 (S Corporation Shareholder Stock and Debt Basis Limitation)
  - GA-600S (Georgia S-Corporation Tax Return)
  - Form 7004, Form 8879-S, Form 8453-S (procedural, light specs)

Authority sources fetched from irs.gov on 2026-03-18.
Georgia rates from verified CLAUDE.md values (GA DOR site returned 404).
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
    JurisdictionConformitySource,
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
# Fresh authority sources
# ═══════════════════════════════════════════════════════════════════════════

FRESH_SOURCES = [
    {
        "source_code": "IRS_2025_4562_INSTR_FULL",
        "source_type": "official_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "Instructions for Form 4562 (2025) — Depreciation and Amortization (fetched 2026-03-18)",
        "citation": "Instructions for Form 4562 (2025)",
        "issuer": "IRS",
        "current_status": "active",
        "is_substantive_authority": True,
        "requires_human_review": False,
        "trust_score": 9.5,
        "topics": ["depreciation", "section_179", "bonus_depreciation", "macrs"],
        "excerpts": [
            {
                "excerpt_label": "Part I Section 179 — 2025 limits (OBBBA)",
                "excerpt_text": "The maximum section 179 deduction is $2,500,000 for property placed in service during tax years beginning in 2025 (P.L. 119-21, OBBBA). The investment limitation threshold is $4,000,000. The deduction is reduced dollar-for-dollar for investments exceeding the threshold. The deduction is further limited to taxable income from the active conduct of a trade or business.",
                "summary_text": "Section 179: $2,500,000 max, $4,000,000 threshold (OBBBA 2025). Limited by business income.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part II Bonus depreciation — OBBBA 2025 rates",
                "excerpt_text": "100% bonus depreciation for qualified property acquired after January 19, 2025 (P.L. 119-21, OBBBA — permanent). 40% for property acquired before January 20, 2025 (binding contract rule applies). Qualified property includes MACRS property with recovery period of 20 years or less, computer software, water utility property, and qualified film/television productions.",
                "summary_text": "Bonus: 100% post-1/19/2025 (permanent, OBBBA), 40% pre-1/20/2025. Applies to <=20yr MACRS property.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Section 179 flow for S-Corps",
                "excerpt_text": "For S corporations, the section 179 deduction is a separately stated item reported on Schedule K-1, line 11. It does not reduce the corporation's ordinary business income on page 1. Each shareholder applies their own business income limitation on their individual Form 4562.",
                "summary_text": "S-Corp section 179 -> K-1 line 11 (separately stated). NOT on Page 1 Line 14.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part III MACRS — GDS vs ADS",
                "excerpt_text": "General Depreciation System (GDS) is the default for most property. Alternative Depreciation System (ADS) is required for property used predominantly outside the U.S., tax-exempt bond financed property, and property used in a farming business (if electing out of bonus). ADS uses straight-line method with longer recovery periods. MACRS conventions: half-year (default), mid-quarter (if >40% placed in service in Q4), mid-month (real property).",
                "summary_text": "GDS default, ADS required for foreign/tax-exempt/farming. Conventions: HY, MQ, MM.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_1125A_INSTR",
        "source_type": "official_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "Instructions for Form 1125-A (2025) — Cost of Goods Sold",
        "citation": "Form 1125-A Instructions (2025)",
        "issuer": "IRS",
        "current_status": "active",
        "is_substantive_authority": True,
        "requires_human_review": False,
        "trust_score": 9.5,
        "topics": ["cogs", "inventory"],
        "excerpts": [
            {
                "excerpt_label": "Who must file Form 1125-A",
                "excerpt_text": "Filers of Form 1120, 1120-C, 1120-F, 1120-S, 1065, or 1065-B must complete and attach Form 1125-A if they report a deduction for cost of goods sold.",
                "summary_text": "Required when COGS is deducted. Line 8 flows to the entity return.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "COGS computation and section 263A",
                "excerpt_text": "Line 1: Inventory at beginning of year. Line 2: Purchases. Line 3: Cost of labor. Line 4: Additional section 263A costs (uniform capitalization). Line 5: Other costs. Line 6: Total (lines 1-5). Line 7: Inventory at end of year. Line 8: Cost of goods sold (line 6 minus line 7). Line 8 flows to Form 1120-S Page 1 Line 2. Section 263A requires certain indirect costs to be capitalized into inventory.",
                "summary_text": "COGS = beginning inventory + purchases + labor + 263A costs + other - ending inventory. -> Page 1 Line 2.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_1125E_INSTR",
        "source_type": "official_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "Instructions for Form 1125-E (2025) — Compensation of Officers",
        "citation": "Form 1125-E Instructions (2025)",
        "issuer": "IRS",
        "current_status": "active",
        "is_substantive_authority": True,
        "requires_human_review": False,
        "trust_score": 9.5,
        "topics": ["officer_compensation", "1120s"],
        "excerpts": [
            {
                "excerpt_label": "Filing requirement and total flow",
                "excerpt_text": "Form 1125-E must be attached when total receipts are $500,000 or more and the entity deducts compensation for officers. Include salaries, commissions, bonuses, and taxable fringe benefits. For S corporations, include fringe benefits for >2% shareholders. Line 4 total flows to Form 1120-S Page 1 Line 7 (Compensation of officers).",
                "summary_text": "Required when receipts >= $500K. Line 4 total -> Page 1 Line 7.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_8825_INSTR_FULL",
        "source_type": "official_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "Instructions for Form 8825 and Schedule A (Rev. December 2025) — Rental Real Estate Income and Expenses (i8825.pdf fetched 2026-07-10)",
        "citation": "Instructions for Form 8825 and Schedule A (Rev. December 2025)",
        "issuer": "IRS",
        "current_status": "active",
        "is_substantive_authority": True,
        "requires_human_review": False,
        "trust_score": 9.5,
        "topics": ["rental_real_estate", "8825", "passive_activity"],
        "excerpts": [
            {
                "excerpt_label": "What's New (Rev. 12-2025) — which version, col (c) codes, 2a/2b split, Schedule A",
                "excerpt_text": "Which version to use. For tax years beginning in 2025, use the December 2025 revision of Form 8825. Use the November 2018 revision of Form 8825 for tax years beginning in 2018, before 2025. [...] Allowable codes for other information. New codes were added to provide additional information relating to gain or (loss) associated with acquisitions, dispositions, or other transactions. Enter applicable codes in column (c) of line 1. Line 2. Report rental real estate gross rents and other income related to rental real estate activity separately on lines 2a and 2b. Schedule A (Form 8825). If you're a partnership or S corporation that is required to file Schedule M-3, you must use new Schedule A (Form 8825), Rental Real Estate Other Deductions, to report other deductions and include the total amount on Form 8825, line 17.",
                "summary_text": "Dec-2025 revision for TY2025: 2a/2b income split, new col (c) A-I codes, new Schedule A (Form 8825) for M-3 filers -> line 17.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Line 1 — address, type codes 1-8, col (c) M-3-only note, codes A-I",
                "excerpt_text": "For each property in column (a), enter the street address, city or town, and ZIP code. If the property is located outside the United States, enter the postal code and country. Specify the type of property by entering one of the following codes in column (b). Allowable Codes for Type of Property: 1—Single-family residence; 2—Multi-family residence; 3—Vacation or short-term rental; 4—Commercial; 5—Land; 6—Royalties; 7—Self-rental; 8—Other (include description with the code on Form 8825 or on a separate statement). Note: Column (c) is only required for partnerships and S corporations that have a Schedule M-3 filing requirement. For each property, in column (c), provide any applicable other information outlined by the following codes. Allowable Codes for Other Information: A—Nontaxable contribution (sections 721 and 351); B—Other exchange (sections 1031, 1033, etc.); C—Taxable acquisition (section 1012); D—New construction/renovation or other basis addition/subtraction; E—Reserved for future use; F—Nontaxable distribution (section 731); G—Taxable disposition (section 1001 gain/loss); H—Abandonment; I—Other/supplement. For each property, enter the number of days rented at fair market value in column (d) and number of days with personal use in column (e). For details, see section 280A.",
                "summary_text": "Col (a) street/city/ZIP; col (b) type 1-8; col (c) A-I acquisition/disposition codes REQUIRED ONLY for M-3 filers; cols (d)/(e) days.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Line 17 Other Deductions + Schedule A (Form 8825) — M-3 conditional",
                "excerpt_text": "Line 17—Other Deductions. For partnerships and S corporations that don't have a Schedule M-3 filing requirement, enter all other deductions for each property listed. All others, see Schedule A next. Schedule A (Form 8825), Rental Real Estate Other Deductions: For partnerships and S corporations with a Schedule M-3 filing requirement, complete and attach Schedule(s) A (Form 8825) for each property listed on Form 8825. Enter the total amount on Form 8825, line 17, for each property.",
                "summary_text": "Non-M-3 filers: enter other deductions directly on line 17. M-3 filers: Schedule A (Form 8825) per property, total -> line 17.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Line 14 Depreciation — Form 4562 attachment",
                "excerpt_text": "The partnership or S corporation may claim a depreciation deduction each year for rental property (except for land, which is not depreciable). If the partnership or S corporation placed property in service during the current tax year or claimed depreciation on any vehicle or other listed property, complete and attach Form 4562, Depreciation and Amortization.",
                "summary_text": "Rental depreciation on 8825 line 14; attach Form 4562 when current-year PIS or listed property.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Line 8 Interest — section 163(j) pointer",
                "excerpt_text": "Line 8—Interest. Your interest expense may be limited. See the Instructions for Form 8990, Limitation on Business Interest Expense Under Section 163(j), for more information.",
                "summary_text": "Line 8 interest may be limited under section 163(j) (Form 8990).",
                "is_key_excerpt": False,
            },
            {
                "excerpt_label": "Specific Instructions — pages, 20a-23 once, scope exclusions",
                "excerpt_text": "If you have more than four rental real estate properties, page 2 of Form 8825 has been redesigned to allow four additional entries. Complete and attach as many additional pages needed to list all your rental real estate properties. Complete lines 1 through 19 for each property. Complete lines 20a through 23 on page 1 only once. The figures on lines 20a and 20b should be the combined totals from all pages. [...] Don't report on Form 8825 any of the following: Income or deductions from a trade or business activity or a rental activity other than rental real estate. Portfolio income or deductions. Section 179 expense deduction. Other items that must be reported separately to the partners or shareholders. Commercial revitalization deductions.",
                "summary_text": "Lines 1-19 per property (4/page); 20a-23 once on page 1 combining all pages. No trade/business items, portfolio, or section 179 here.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Form 8825 (Rev. 12-2025) face — expense/summary line labels verbatim",
                "excerpt_text": "2a Gross rents. 2b Other income related to rental real estate activity. 2c Total rental real estate income for each property. Add lines 2a and 2b. 3 Advertising. 4 Auto and travel. 5 Cleaning and maintenance. 6 Commissions. 7 Insurance. 8 Interest (see instructions). 9 Legal and other professional fees. 10 Real estate taxes. 11 Repairs. 12 Utilities. 13 Wages and salaries. 14 Depreciation (see instructions). 15 Reserved for future use. 16 Reserved for future use. 17 Other deductions (attach Schedule A (Form 8825)). 18 Total rental real estate expenses for each property. Add lines 3 through 17. 19 Income or (loss) from each rental real estate property. Subtract line 18 from line 2c. 20a Total rental real estate income. Add total rental real estate income from line 2c. 20b Total rental real estate expenses. Add total rental real estate expenses from line 18. 21 Net gain (loss) from Form 4797, Part II, line 17, from the disposition of property from rental real estate activities. 22a Net income (loss) from rental real estate activities from partnerships, estates, and trusts in which this partnership or S corporation is a partner or beneficiary (from Schedule K-1). 22b Identify below the partnerships, estates, or trusts from which net income (loss) is shown on line 22a. 23 Net rental real estate income (loss). Combine lines 20a through 22a. Enter the result here and on Schedule K, line 2, of Form 1065 or 1120-S.",
                "summary_text": "Dec-2025 face: income 2a-2c, expenses 3-17 (15/16 reserved), 18 total, 19 net; 20a/20b/21/22a/22b/23 summary; 23 = combine 20a-22a -> Sch K line 2.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule A (Form 8825) (12-2025) face — 31 lines verbatim",
                "excerpt_text": "SCHEDULE A (Form 8825) (December 2025) — Rental Real Estate Other Deductions. Attach to Form 8825. 1 Asset management fee. 2 Bad debt expense. 3 Building maintenance. 4 Common charges. 5 Contract services. 6 Debt extinguishment costs. 7 Ground rent. 8 Grounds maintenance. 9 Homeowner association fee. 10 Incentive fee. 11 Landscaping. 12 Leased employee expense. 13 Management fee. 14 Other taxes. 15 Prepayment penalty. 16 Reimbursed wages/salaries (reimbursed to management co.). 17 Section 481(a) adjustments. 18 Tenant renovations. 19 Tenant services. 20 Turnover expenses. 21-29 Reserved for future use. 30 Other. 31 Total (Enter the total here and on Form 8825, line 17.)",
                "summary_text": "Schedule A: 20 named other-deduction categories + line 30 Other; line 31 total -> Form 8825 line 17 (per property columns).",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_7203_INSTR_FULL",
        "source_type": "official_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "Instructions for Form 7203 (2025) — S Corporation Shareholder Stock and Debt Basis Limitation (fetched 2026-03-18)",
        "citation": "Instructions for Form 7203 (2025)",
        "issuer": "IRS",
        "current_status": "active",
        "is_substantive_authority": True,
        "requires_human_review": False,
        "trust_score": 9.5,
        "topics": ["7203", "shareholder_basis", "loss_limitation"],
        "excerpts": [
            {
                "excerpt_label": "Basis adjustment ordering rules",
                "excerpt_text": "Stock basis is adjusted in this mandatory order: (1) Increased by income items (line 3). (2) Decreased by distributions (line 6) — but not below zero. (3) Decreased by nondeductible expenses and oil/gas depletion (lines 7-8) — but not below zero. (4) Decreased by losses and deductions (Part III) — first from stock basis, then from debt basis. Stock basis cannot go below zero. Losses exceeding stock plus debt basis are suspended and carried forward indefinitely.",
                "summary_text": "Order: income -> distributions -> nondeductible -> losses. Stock basis floor = zero. Excess suspended.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Debt basis and restoration",
                "excerpt_text": "Debt basis arises only from direct loans by the shareholder to the corporation — guarantees and indirect borrowings do not create debt basis. When stock basis is exhausted, losses reduce debt basis. Debt basis is restored by net income increases in subsequent years. Upon loan repayment with reduced debt basis, gain is recognized (capital gain for formal notes, ordinary gain for open accounts).",
                "summary_text": "Debt basis = direct loans only. Losses reduce debt after stock. Restoration via net income.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Who must file Form 7203",
                "excerpt_text": "File Form 7203 if: claiming a deduction for S corp losses, received a non-dividend distribution, disposed of S corp stock, or received loan repayment from S corp. Recommended for all shareholders to maintain basis tracking.",
                "summary_text": "Required when claiming losses, receiving distributions, disposing stock, or receiving loan repayments.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "GA_2025_600S_INSTR",
        "source_type": "state_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "GA",
        "title": "Georgia Form GA-600S Instructions (2025) — S Corporation Tax Return",
        "citation": "GA-600S Instructions (2025)",
        "issuer": "GA DOR",
        "current_status": "active",
        "is_substantive_authority": True,
        "requires_human_review": True,
        "trust_score": 8.0,
        "topics": ["georgia", "state_return", "scorp"],
        "excerpts": [
            {
                "excerpt_label": "Georgia depreciation nonconformity",
                "excerpt_text": "Georgia does NOT conform to IRC section 168(k)/(n) bonus depreciation. Federal bonus depreciation taken must be added back on GA-600S Schedule 1. Georgia DOES conform to the OBBBA IRC section 179 limit for TY2025 via HB 1199 (IRC conformity advanced to January 1, 2026, retroactive to tax years beginning on/after January 1, 2025) — Georgia section 179 = $2,500,000 with phaseout beginning at $4,000,000, equal to federal. (HB 1199 supersedes the pre-OBBBA figures on the Aug-2025 GA Form 4562.)",
                "summary_text": "GA does NOT conform to federal bonus (§168(k)/(n)) but DOES conform to OBBBA §179 via HB 1199. GA Section 179: $2,500,000/$4,000,000 (= federal).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "PTET election and rate",
                "excerpt_text": "Georgia Pass-Through Entity Tax (PTET) is an elective entity-level tax at 5.19% (the TY2025 flat rate). Applies to the entity's Georgia-source taxable income allocated to electing shareholders. This is an entity-level election, not automatic.",
                "summary_text": "PTET: 5.19% (TY2025) elective entity-level tax on GA-source income.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "GA-600S schedule structure",
                "excerpt_text": "Schedule 1: Georgia taxable income (federal income +/- GA additions/subtractions). Schedule 2: PTET computation. Schedule 3: Net worth tax (based on net worth, year = income year + 1). Schedule 4: Apportionment (single gross-receipts factor, §48-7-31). Schedules 5-8: Credits, balance sheet, shareholder info, other.",
                "summary_text": "8 schedules: income adjustments, PTET, net worth tax, apportionment, credits, balance sheet, shareholders, other.",
                "is_key_excerpt": True,
            },
        ],
    },
]

EXISTING_SOURCES = [
    "IRS_2025_1120S_INSTR", "IRS_2025_1120S_INSTR_FULL",
    "IRC_179", "IRC_168", "IRC_197", "IRC_1363", "IRC_1366", "IRC_1367", "IRC_1368",
    "IRS_2025_4562_INSTR", "IRS_PUB_946", "IRC_263A",
    "IRC_465", "IRC_469",
]


class Command(BaseCommand):
    help = "Load remaining 1120-S forms + GA-600S specs"

    def handle(self, *_args, **_options):
        with transaction.atomic():
            sources = self._load_sources()
            self._load_1125a(sources)
            self._load_1125e(sources)
            self._load_8825(sources)
            self._load_7203(sources)
            self._expand_4562(sources)
            self._load_ga600s(sources)
            self._load_procedural_forms(sources)
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

        # Georgia conformity record
        JurisdictionConformitySource.objects.update_or_create(
            jurisdiction_code="GA", tax_year=2025,
            defaults={
                "conformity_type": "partial",
                "authority_source": sources.get("GA_2025_600S_INSTR"),
                "summary": "Georgia partially conforms to federal tax law (IRC conformity Jan 1, 2026 via HB 1199, retroactive to TY2025). Does NOT conform to IRC 168(k)/(n) bonus depreciation (full addback). DOES conform to the OBBBA Section 179 limit: $2,500,000/$4,000,000, equal to federal. PTET at 5.19% (TY2025) is elective.",
                "decoupled_items": [
                    {"item": "IRC 168(k)/(n) bonus depreciation", "treatment": "Full addback required on Schedule 1"},
                    {"item": "Section 179 limits", "treatment": "GA CONFORMS via HB 1199: $2,500,000/$4,000,000 = federal (retroactive to TY2025)"},
                ],
            },
        )
        self.stdout.write("  Georgia conformity record created.")
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
    # Form 1125-A — Cost of Goods Sold
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_1125a(self, sources):
        form = self._upsert_form("1125A", "Form 1125-A — Cost of Goods Sold",
                                  ["1120S", "1065", "1120"],
                                  notes="Required when COGS is deducted. Line 8 -> 1120-S Page 1 Line 2.")
        self._upsert_facts(form, [
            {"fact_key": "inventory_beginning", "label": "Inventory at beginning of year (Line 1)", "data_type": "decimal", "required": True, "sort_order": 1},
            {"fact_key": "purchases", "label": "Purchases (Line 2)", "data_type": "decimal", "sort_order": 2},
            {"fact_key": "cost_of_labor", "label": "Cost of labor (Line 3)", "data_type": "decimal", "sort_order": 3},
            {"fact_key": "section_263a_costs", "label": "Additional section 263A costs (Line 4)", "data_type": "decimal", "sort_order": 4, "notes": "Uniform capitalization (UNICAP) — indirect costs that must be capitalized into inventory."},
            {"fact_key": "other_costs", "label": "Other costs (Line 5)", "data_type": "decimal", "sort_order": 5},
            {"fact_key": "total_line6", "label": "Total (Line 6 = Lines 1-5)", "data_type": "decimal", "sort_order": 6},
            {"fact_key": "inventory_ending", "label": "Inventory at end of year (Line 7)", "data_type": "decimal", "sort_order": 7},
            {"fact_key": "cogs", "label": "Cost of goods sold (Line 8 = Line 6 - Line 7)", "data_type": "decimal", "sort_order": 8},
            {"fact_key": "inventory_method", "label": "Inventory valuation method (Line 9a)", "data_type": "choice", "choices": ["cost", "lower_of_cost_or_market", "other"], "sort_order": 9},
            {"fact_key": "inventory_subelection", "label": "Inventory subelection — FIFO, LIFO, etc. (Lines 9b-9d)", "data_type": "choice", "choices": ["FIFO", "LIFO", "weighted_average", "specific_identification"], "sort_order": 10},
        ])

        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "Total costs (Line 6)", "rule_type": "calculation",
             "formula": "inventory_beginning + purchases + cost_of_labor + section_263a_costs + other_costs",
             "inputs": ["inventory_beginning", "purchases", "cost_of_labor", "section_263a_costs", "other_costs"],
             "outputs": ["total_line6"], "precedence": 1, "sort_order": 1},
            {"rule_id": "R002", "title": "COGS (Line 8)", "rule_type": "calculation",
             "formula": "total_line6 - inventory_ending",
             "inputs": ["total_line6", "inventory_ending"], "outputs": ["cogs"], "precedence": 2, "sort_order": 2},
            {"rule_id": "R003", "title": "Flow to 1120-S Page 1 Line 2", "rule_type": "routing",
             "formula": "Page1_Line2 = cogs", "inputs": ["cogs"], "outputs": ["page1_line2"], "precedence": 3, "sort_order": 3,
             "description": "Form 1125-A Line 8 (COGS) flows to Form 1120-S Page 1 Line 2."},
        ])
        self._upsert_links(rules, sources, [
            ("R001", "IRS_2025_1125A_INSTR", "primary", "Lines 1-6 COGS computation"),
            ("R002", "IRS_2025_1125A_INSTR", "primary", "Line 8 = Line 6 - Line 7"),
            ("R003", "IRS_2025_1125A_INSTR", "primary", "Line 8 -> Page 1 Line 2"),
        ])
        self._upsert_lines(form, [
            {"line_number": "1", "description": "Inventory at beginning of year", "line_type": "input", "sort_order": 1},
            {"line_number": "2", "description": "Purchases", "line_type": "input", "sort_order": 2},
            {"line_number": "3", "description": "Cost of labor", "line_type": "input", "sort_order": 3},
            {"line_number": "4", "description": "Additional section 263A costs", "line_type": "input", "sort_order": 4},
            {"line_number": "5", "description": "Other costs", "line_type": "input", "sort_order": 5},
            {"line_number": "6", "description": "Total (add lines 1 through 5)", "line_type": "subtotal", "source_rules": ["R001"], "sort_order": 6},
            {"line_number": "7", "description": "Inventory at end of year", "line_type": "input", "sort_order": 7},
            {"line_number": "8", "description": "Cost of goods sold (line 6 minus line 7)", "line_type": "total", "source_rules": ["R002"], "destination_form": "1120-S Page 1 Line 2", "sort_order": 8},
        ])
        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D001", "title": "Beginning inventory mismatch", "severity": "warning",
             "condition": "inventory_beginning != prior_year_inventory_ending",
             "message": "Beginning inventory should equal prior year ending inventory."},
            {"diagnostic_id": "D002", "title": "Negative COGS", "severity": "error",
             "condition": "cogs < 0", "message": "COGS is negative (ending inventory exceeds total). Verify inventory amounts."},
            {"diagnostic_id": "D003", "title": "Inventory method not specified", "severity": "warning",
             "condition": "inventory_method is null", "message": "Inventory valuation method not specified on Line 9a."},
        ])
        self._upsert_tests(form, [
            {"scenario_name": "Basic COGS calculation", "scenario_type": "normal",
             "inputs": {"inventory_beginning": 50000, "purchases": 200000, "cost_of_labor": 30000, "section_263a_costs": 5000, "other_costs": 2000, "inventory_ending": 55000},
             "expected_outputs": {"total_line6": 287000, "cogs": 232000}, "sort_order": 1},
            {"scenario_name": "Service company — zero COGS", "scenario_type": "edge",
             "inputs": {"inventory_beginning": 0, "purchases": 0, "cost_of_labor": 0, "section_263a_costs": 0, "other_costs": 0, "inventory_ending": 0},
             "expected_outputs": {"total_line6": 0, "cogs": 0}, "sort_order": 2},
        ])
        self._upsert_form_links("1125A", sources, [("IRS_2025_1125A_INSTR", "governs")])
        self.stdout.write(self.style.SUCCESS("  1125-A complete."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Form 1125-E — Compensation of Officers
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_1125e(self, sources):
        form = self._upsert_form("1125E", "Form 1125-E — Compensation of Officers",
                                  ["1120S", "1120"],
                                  notes="Required when total receipts >= $500,000. Line 4 -> Page 1 Line 7.")
        self._upsert_facts(form, [
            {"fact_key": "officer_name", "label": "Officer name", "data_type": "string", "required": True, "sort_order": 1},
            {"fact_key": "officer_ssn", "label": "Officer SSN", "data_type": "string", "sort_order": 2},
            {"fact_key": "pct_time_devoted", "label": "Percent of time devoted to business", "data_type": "decimal", "sort_order": 3},
            {"fact_key": "pct_stock_owned", "label": "Percent of corporation stock owned", "data_type": "decimal", "sort_order": 4},
            {"fact_key": "compensation_amount", "label": "Amount of compensation", "data_type": "decimal", "required": True, "sort_order": 5},
            {"fact_key": "total_compensation", "label": "Total compensation of all officers (Line 4)", "data_type": "decimal", "sort_order": 6},
            {"fact_key": "total_receipts", "label": "Total receipts (for filing threshold)", "data_type": "decimal", "sort_order": 7},
        ])
        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "Total compensation (Line 4)", "rule_type": "calculation",
             "formula": "sum(compensation_amount for each officer)",
             "inputs": ["compensation_amount"], "outputs": ["total_compensation"], "precedence": 1, "sort_order": 1},
            {"rule_id": "R002", "title": "Flow to Page 1 Line 7", "rule_type": "routing",
             "formula": "Page1_Line7 = total_compensation", "inputs": ["total_compensation"], "outputs": ["page1_line7"],
             "precedence": 2, "sort_order": 2, "description": "Total officer compensation -> 1120-S Page 1 Line 7."},
            {"rule_id": "R003", "title": "Filing threshold", "rule_type": "validation",
             "formula": "required when total_receipts >= 500000", "inputs": ["total_receipts"], "outputs": [],
             "precedence": 0, "sort_order": 3, "description": "Form 1125-E required when total receipts >= $500,000."},
        ])
        self._upsert_links(rules, sources, [
            ("R001", "IRS_2025_1125E_INSTR", "primary", "Sum of officer compensation"),
            ("R002", "IRS_2025_1125E_INSTR", "primary", "Line 4 -> Page 1 Line 7"),
            ("R003", "IRS_2025_1125E_INSTR", "primary", "$500K receipts threshold"),
        ])
        self._upsert_lines(form, [
            {"line_number": "1", "description": "Officer details (name, SSN, % time, % stock, compensation)", "line_type": "input", "sort_order": 1},
            {"line_number": "4", "description": "Total compensation of officers", "line_type": "total", "source_rules": ["R001"], "destination_form": "1120-S Page 1 Line 7", "sort_order": 2},
        ])
        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D001", "title": "Threshold not met", "severity": "info",
             "condition": "total_receipts < 500000", "message": "Total receipts < $500K but Form 1125-E is being filed. Filing is optional below threshold."},
            {"diagnostic_id": "D002", "title": "Missing 1125-E", "severity": "warning",
             "condition": "total_receipts >= 500000 AND no 1125E data", "message": "Total receipts >= $500K — Form 1125-E is required."},
            {"diagnostic_id": "D003", "title": "Zero compensation officer", "severity": "warning",
             "condition": "compensation_amount == 0", "message": "Officer listed but compensation is $0. Verify this is correct."},
        ])
        self._upsert_tests(form, [
            {"scenario_name": "Single officer, 100% shareholder", "scenario_type": "normal",
             "inputs": {"officers": [{"name": "John Smith", "pct_time": 100, "pct_stock": 100, "compensation": 80000}]},
             "expected_outputs": {"total_compensation": 80000}, "sort_order": 1},
            {"scenario_name": "Multiple officers", "scenario_type": "normal",
             "inputs": {"officers": [{"name": "A", "compensation": 60000}, {"name": "B", "compensation": 40000}]},
             "expected_outputs": {"total_compensation": 100000}, "sort_order": 2},
        ])
        self._upsert_form_links("1125E", sources, [("IRS_2025_1125E_INSTR", "governs")])
        self.stdout.write(self.style.SUCCESS("  1125-E complete."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Form 8825 — Rental Real Estate Income and Expenses
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_8825(self, sources):
        # Renumbered VERBATIM to the December 2025 revision (f8825.pdf Rev.
        # 12-2025 + i8825.pdf Rev. 12-2025, both fetched 2026-07-10; IRS8825.xsd
        # 2025v6.2 element/LineNumber map agrees). The original Session-10 block
        # carried a pre-2025 numbering (other 15 / total 16 / net 17 / total-net
        # 21) that matches NO published revision of the form — early-era drift,
        # same class as the 2026-07-09 face audit findings. Stale fact/line rows
        # are DELETED in-loader so a reseed self-heals.
        form = self._upsert_form("8825", "Form 8825 — Rental Real Estate Income and Expenses of a Partnership or an S Corporation",
                                  ["1120S", "1065"],
                                  notes="Rev. December 2025 face (use for tax years beginning in 2025). Per-property "
                                        "income 2a-2c / expenses 3-17 (15/16 reserved) / 18 total / 19 net; summary "
                                        "20a-23 once on page 1; line 23 = combine 20a-22a -> Schedule K line 2. "
                                        "Rental depreciation on line 14 HERE, never Page 1. NEW in 12-2025: line 2b "
                                        "other income, column (c) A-I other-information codes (M-3 filers only), and "
                                        "Schedule A (Form 8825) other-deductions detail (M-3 filers only) -> line 17.")
        self._upsert_facts(form, [
            # Line 1 — property table, columns (a)-(e)
            {"fact_key": "property_street", "label": "Street address (Line 1(a))", "data_type": "string", "sort_order": 1,
             "notes": "i8825 12-2025: 'enter the street address, city or town, and ZIP code. If the property is located outside the United States, enter the postal code and country.'"},
            {"fact_key": "property_city", "label": "City or town (Line 1(a))", "data_type": "string", "sort_order": 2},
            {"fact_key": "property_state", "label": "State (Line 1(a))", "data_type": "string", "sort_order": 3},
            {"fact_key": "property_zip", "label": "ZIP code (Line 1(a))", "data_type": "string", "sort_order": 4},
            {"fact_key": "property_type", "label": "Type of property — code 1-8 (Line 1(b))", "data_type": "choice", "sort_order": 5,
             "choices": {"1": "Single-family residence", "2": "Multi-family residence", "3": "Vacation or short-term rental",
                          "4": "Commercial", "5": "Land", "6": "Royalties", "7": "Self-rental",
                          "8": "Other (include description with the code on Form 8825 or on a separate statement)"},
             "notes": "Codes verbatim from the Rev. 12-2025 face page 2 / i8825."},
            {"fact_key": "other_info_code", "label": "Other information — code A-I (Line 1(c))", "data_type": "choice", "sort_order": 6,
             "choices": {"A": "Nontaxable contribution (sections 721 and 351)", "B": "Other exchange (sections 1031, 1033, etc.)",
                          "C": "Taxable acquisition (section 1012)", "D": "New construction/renovation or other basis addition/subtraction",
                          "E": "Reserved for future use", "F": "Nontaxable distribution (section 731)",
                          "G": "Taxable disposition (section 1001 gain/loss)", "H": "Abandonment", "I": "Other/supplement"},
             "notes": "i8825 12-2025 Note VERBATIM: 'Column (c) is only required for partnerships and S corporations "
                      "that have a Schedule M-3 filing requirement.' For codes A-I include relevant supplementary "
                      "description on Form 8825 or on a separate statement (face page 2)."},
            {"fact_key": "fair_rental_days", "label": "Fair rental days (Line 1(d))", "data_type": "integer", "sort_order": 7},
            {"fact_key": "personal_use_days", "label": "Personal-use days (Line 1(e))", "data_type": "integer", "sort_order": 8,
             "notes": "See section 280A (i8825)."},
            # Income — lines 2a-2c
            {"fact_key": "gross_rents", "label": "Gross rents (Line 2a)", "data_type": "decimal", "required": True, "sort_order": 9},
            {"fact_key": "other_rental_income", "label": "Other income related to rental real estate activity (Line 2b)", "data_type": "decimal", "sort_order": 10,
             "notes": "NEW on the 12-2025 face: 'Report rental real estate gross rents and other income related to rental real estate activity separately on lines 2a and 2b.'"},
            {"fact_key": "total_property_income", "label": "Total rental real estate income for each property (Line 2c = 2a + 2b)", "data_type": "decimal", "sort_order": 11},
            # Expenses — lines 3-17 (15/16 reserved)
            {"fact_key": "advertising", "label": "Advertising (Line 3)", "data_type": "decimal", "sort_order": 12},
            {"fact_key": "auto_travel", "label": "Auto and travel (Line 4)", "data_type": "decimal", "sort_order": 13},
            {"fact_key": "cleaning", "label": "Cleaning and maintenance (Line 5)", "data_type": "decimal", "sort_order": 14},
            {"fact_key": "commissions", "label": "Commissions (Line 6)", "data_type": "decimal", "sort_order": 15},
            {"fact_key": "insurance", "label": "Insurance (Line 7)", "data_type": "decimal", "sort_order": 16},
            {"fact_key": "mortgage_interest", "label": "Interest — mortgage component (Line 8)", "data_type": "decimal", "sort_order": 17,
             "notes": "The 12-2025 face has ONE interest line (8, 'Interest (see instructions)'); the mortgage/other "
                      "split is app-side modeling shared with Schedule E — both components land on line 8. "
                      "i8825: interest may be limited under section 163(j) (Form 8990)."},
            {"fact_key": "other_interest", "label": "Interest — other component (Line 8)", "data_type": "decimal", "sort_order": 18,
             "notes": "Second component of face line 8 — see mortgage_interest note."},
            {"fact_key": "legal_professional", "label": "Legal and other professional fees (Line 9)", "data_type": "decimal", "sort_order": 19},
            {"fact_key": "taxes", "label": "Real estate taxes (Line 10)", "data_type": "decimal", "sort_order": 20},
            {"fact_key": "repairs", "label": "Repairs (Line 11)", "data_type": "decimal", "sort_order": 21},
            {"fact_key": "utilities", "label": "Utilities (Line 12)", "data_type": "decimal", "sort_order": 22},
            {"fact_key": "wages_salaries", "label": "Wages and salaries (Line 13)", "data_type": "decimal", "sort_order": 23},
            {"fact_key": "depreciation", "label": "Depreciation (Line 14)", "data_type": "decimal", "sort_order": 24,
             "notes": "Rental property depreciation — appears HERE, NOT on Page 1 Line 14. Attach Form 4562 when "
                      "current-year placed-in-service or listed property (i8825 Line 14)."},
            {"fact_key": "other_expenses", "label": "Other deductions (Line 17)", "data_type": "decimal", "sort_order": 25,
             "notes": "Non-M-3 filers enter all other deductions directly; M-3 filers must detail on Schedule A "
                      "(Form 8825) per property and carry line A31 here (i8825 Line 17 / Schedule A, verbatim in R006)."},
            {"fact_key": "schedule_a_category", "label": "Schedule A (Form 8825) other-deduction category", "data_type": "choice", "sort_order": 26,
             "choices": {"A1": "Asset management fee", "A2": "Bad debt expense", "A3": "Building maintenance",
                          "A4": "Common charges", "A5": "Contract services", "A6": "Debt extinguishment costs",
                          "A7": "Ground rent", "A8": "Grounds maintenance", "A9": "Homeowner association fee",
                          "A10": "Incentive fee", "A11": "Landscaping", "A12": "Leased employee expense",
                          "A13": "Management fee", "A14": "Other taxes", "A15": "Prepayment penalty",
                          "A16": "Reimbursed wages/salaries (reimbursed to management co.)",
                          "A17": "Section 481(a) adjustments", "A18": "Tenant renovations", "A19": "Tenant services",
                          "A20": "Turnover expenses", "A30": "Other"},
             "notes": "Fixed category list verbatim from the Schedule A (Form 8825) 12-2025 face (lines 21-29 "
                      "reserved). Per-property MULTIPLE detail rows (category + amount, description for A30 Other) "
                      "are app-side input mechanics; their sum = line A31 = Form 8825 line 17."},
            # Per-property computed
            {"fact_key": "total_expenses", "label": "Total rental real estate expenses for each property (Line 18)", "data_type": "decimal", "sort_order": 27},
            {"fact_key": "net_rent", "label": "Income or (loss) from each rental real estate property (Line 19 = 2c - 18)", "data_type": "decimal", "sort_order": 28},
            # Summary — page 1 once
            {"fact_key": "total_gross_rents", "label": "Total rental real estate income (Line 20a)", "data_type": "decimal", "sort_order": 29},
            {"fact_key": "total_expenses_all", "label": "Total rental real estate expenses (Line 20b)", "data_type": "decimal", "sort_order": 30},
            {"fact_key": "gain_4797_rental", "label": "Net gain (loss) from Form 4797, Part II, line 17, from rental real estate dispositions (Line 21)", "data_type": "decimal", "sort_order": 31},
            {"fact_key": "passthrough_net_rental", "label": "Net rental income (loss) from partnerships, estates, trusts (Line 22a)", "data_type": "decimal", "sort_order": 32},
            {"fact_key": "passthrough_identities", "label": "Partnerships/estates/trusts on line 22a — name + EIN (Line 22b)", "data_type": "string", "sort_order": 33,
             "notes": "Attach a statement if more space is needed (face 22b)."},
            {"fact_key": "total_net_rental", "label": "Net rental real estate income (loss) (Line 23 = combine 20a-22a)", "data_type": "decimal", "sort_order": 34},
        ])
        # Stale pre-renumber fact rows — delete anything not in the new set so
        # a reseed self-heals (update_or_create alone cannot remove rows).
        _2025_FACTS = {
            "property_street", "property_city", "property_state", "property_zip",
            "property_type", "other_info_code", "fair_rental_days", "personal_use_days",
            "gross_rents", "other_rental_income", "total_property_income",
            "advertising", "auto_travel", "cleaning", "commissions", "insurance",
            "mortgage_interest", "other_interest", "legal_professional", "taxes",
            "repairs", "utilities", "wages_salaries", "depreciation", "other_expenses",
            "schedule_a_category", "total_expenses", "net_rent",
            "total_gross_rents", "total_expenses_all", "gain_4797_rental",
            "passthrough_net_rental", "passthrough_identities", "total_net_rental",
        }
        stale_facts = FormFact.objects.filter(tax_form=form).exclude(fact_key__in=_2025_FACTS)
        if stale_facts.exists():
            self.stdout.write(f"  deleting {stale_facts.count()} stale pre-renumber fact rows")
            stale_facts.delete()
        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "Total expenses per property (Line 18)", "rule_type": "calculation",
             "formula": "line_18 = sum(lines 3 through 17)",
             "inputs": ["advertising", "auto_travel", "cleaning", "commissions", "insurance", "mortgage_interest",
                         "other_interest", "legal_professional", "taxes", "repairs", "utilities", "wages_salaries",
                         "depreciation", "other_expenses"],
             "outputs": ["total_expenses"], "precedence": 2, "sort_order": 1,
             "description": "Face verbatim: 'Total rental real estate expenses for each property. Add lines 3 through 17.' Lines 15/16 are Reserved for future use on the 12-2025 face."},
            {"rule_id": "R002", "title": "Income or (loss) per property (Line 19)", "rule_type": "calculation",
             "formula": "line_19 = line_2c - line_18", "inputs": ["total_property_income", "total_expenses"],
             "outputs": ["net_rent"], "precedence": 3, "sort_order": 2,
             "description": "Face verbatim: 'Income or (loss) from each rental real estate property. Subtract line 18 from line 2c.'"},
            {"rule_id": "R003", "title": "Line 23 combines 20a-22a -> Schedule K Line 2", "rule_type": "routing",
             "formula": "line_23 = line_20a - line_20b + line_21 + line_22a; K2 = line_23",
             "inputs": ["total_gross_rents", "total_expenses_all", "gain_4797_rental", "passthrough_net_rental"],
             "outputs": ["total_net_rental", "K_line_2"], "precedence": 4, "sort_order": 3,
             "description": "Face verbatim: 'Net rental real estate income (loss). Combine lines 20a through 22a. "
                            "Enter the result here and on Schedule K, line 2, of Form 1065 or 1120-S.' 20a = sum of "
                            "all line 2c; 20b = sum of all line 18 (shown in parentheses — subtract); 21 = Form 4797 "
                            "Part II line 17 rental dispositions; 22a = pass-through rental from K-1s received. "
                            "Lines 20a-23 are completed on page 1 ONLY ONCE, combining all pages. (The pre-renumber "
                            "formula 'K2 = sum(all net_rent)' omitted lines 21/22a — corrected 2026-07-10.)"},
            {"rule_id": "R004", "title": "Rental depreciation stays on 8825", "rule_type": "validation",
             "formula": "rental_depreciation NOT on Page1_Line14",
             "inputs": ["depreciation"], "outputs": [], "precedence": 0, "sort_order": 4,
             "description": "Rental property depreciation is reported on Form 8825 Line 14, not on Form 4562/Page 1 Line 14. This keeps rental and trade/business depreciation separate for passive activity purposes. Attach Form 4562 when current-year placed-in-service or listed property (i8825 Line 14)."},
            {"rule_id": "R005", "title": "Total income per property (Line 2c)", "rule_type": "calculation",
             "formula": "line_2c = line_2a + line_2b", "inputs": ["gross_rents", "other_rental_income"],
             "outputs": ["total_property_income"], "precedence": 1, "sort_order": 5,
             "description": "Face verbatim: 'Total rental real estate income for each property. Add lines 2a and 2b.' "
                            "i8825 What's New: 'Report rental real estate gross rents and other income related to "
                            "rental real estate activity separately on lines 2a and 2b.' (2b is NEW on the 12-2025 face.)"},
            {"rule_id": "R006", "title": "Schedule A (Form 8825) other-deductions detail — M-3 filers", "rule_type": "conditional",
             "formula": "if schedule_m3_required: line_17 = ScheduleA_line_31 (per property, Schedule A attached); else line_17 = direct entry",
             "inputs": ["other_expenses", "schedule_a_category"], "outputs": [], "precedence": 5, "sort_order": 6,
             "description": "i8825 12-2025 VERBATIM: 'Line 17—Other Deductions. For partnerships and S corporations "
                            "that don't have a Schedule M-3 filing requirement, enter all other deductions for each "
                            "property listed. All others, see Schedule A next.' And: 'For partnerships and S "
                            "corporations with a Schedule M-3 filing requirement, complete and attach Schedule(s) A "
                            "(Form 8825) for each property listed on Form 8825. Enter the total amount on Form 8825, "
                            "line 17, for each property.' Schedule A line 31 = total of the fixed category lines 1-20 "
                            "plus line 30 Other (21-29 reserved). The M-3 requirement is the i1120s/i1065 $10M "
                            "total-assets test (corrected 2026-07-09). App note: management-fee-type amounts belong "
                            "on Schedule A line 13 when the schedule applies.",
             "exceptions": "Non-M-3 filers may still keep per-row detail as an app-side statement; only the OFFICIAL Schedule A attachment is conditioned on M-3."},
            {"rule_id": "R007", "title": "Column (c) other-information codes — M-3 filers only", "rule_type": "validation",
             "formula": "other_info_code required only when schedule_m3_required; codes A-I",
             "inputs": ["other_info_code"], "outputs": [], "precedence": 0, "sort_order": 7,
             "description": "i8825 12-2025 Note VERBATIM: 'Column (c) is only required for partnerships and S "
                            "corporations that have a Schedule M-3 filing requirement.' New 12-2025 codes for gain/"
                            "(loss) events: A contribution 721/351, B other exchange 1031/1033, C taxable acquisition "
                            "1012, D new construction/renovation or basis addition/subtraction, E reserved, F "
                            "nontaxable distribution 731, G taxable disposition 1001, H abandonment, I other/"
                            "supplement. For codes A-I include relevant supplementary description on Form 8825 or on "
                            "a separate statement (face page 2)."},
        ])
        self._upsert_links(rules, sources, [
            ("R001", "IRS_2025_8825_INSTR_FULL", "primary", "Line 18 = add lines 3 through 17 (face verbatim)"),
            ("R002", "IRS_2025_8825_INSTR_FULL", "primary", "Line 19 = line 2c minus line 18 (face verbatim)"),
            ("R003", "IRS_2025_8825_INSTR_FULL", "primary", "Line 23 = combine 20a-22a -> Schedule K line 2 (face verbatim)"),
            ("R003", "IRS_2025_8825_INSTR", "secondary", "Net -> Sch K line 2 -> K-1; passive at owner level"),
            ("R004", "IRS_2025_8825_INSTR_FULL", "primary", "Rental depreciation on 8825 line 14, not Page 1; attach 4562"),
            ("R005", "IRS_2025_8825_INSTR_FULL", "primary", "Line 2c = 2a + 2b; 2a/2b split is new (What's New verbatim)"),
            ("R006", "IRS_2025_8825_INSTR_FULL", "primary", "Schedule A (Form 8825) M-3-conditional mechanics (verbatim)"),
            ("R007", "IRS_2025_8825_INSTR_FULL", "primary", "Column (c) codes A-I; M-3-only Note (verbatim)"),
        ])
        self._upsert_lines(form, [
            {"line_number": "1", "description": "Physical address of each property — street, city, state, ZIP (col a); type code 1-8 (col b); other-information code A-I (col c); fair rental days (col d); personal-use days (col e)", "line_type": "input", "source_facts": ["property_street", "property_city", "property_state", "property_zip", "property_type", "other_info_code", "fair_rental_days", "personal_use_days"], "sort_order": 1},
            {"line_number": "2a", "description": "Gross rents", "line_type": "input", "source_facts": ["gross_rents"], "sort_order": 2},
            {"line_number": "2b", "description": "Other income related to rental real estate activity", "line_type": "input", "source_facts": ["other_rental_income"], "sort_order": 3},
            {"line_number": "2c", "description": "Total rental real estate income for each property. Add lines 2a and 2b", "line_type": "calculated", "source_rules": ["R005"], "sort_order": 4},
            {"line_number": "3", "description": "Advertising", "line_type": "input", "source_facts": ["advertising"], "sort_order": 5},
            {"line_number": "4", "description": "Auto and travel", "line_type": "input", "source_facts": ["auto_travel"], "sort_order": 6},
            {"line_number": "5", "description": "Cleaning and maintenance", "line_type": "input", "source_facts": ["cleaning"], "sort_order": 7},
            {"line_number": "6", "description": "Commissions", "line_type": "input", "source_facts": ["commissions"], "sort_order": 8},
            {"line_number": "7", "description": "Insurance", "line_type": "input", "source_facts": ["insurance"], "sort_order": 9},
            {"line_number": "8", "description": "Interest (see instructions)", "line_type": "input", "source_facts": ["mortgage_interest", "other_interest"], "sort_order": 10,
             "notes": "One face line; the app's mortgage/other split both land here. Section 163(j) may limit (Form 8990)."},
            {"line_number": "9", "description": "Legal and other professional fees", "line_type": "input", "source_facts": ["legal_professional"], "sort_order": 11},
            {"line_number": "10", "description": "Real estate taxes", "line_type": "input", "source_facts": ["taxes"], "sort_order": 12},
            {"line_number": "11", "description": "Repairs", "line_type": "input", "source_facts": ["repairs"], "sort_order": 13},
            {"line_number": "12", "description": "Utilities", "line_type": "input", "source_facts": ["utilities"], "sort_order": 14},
            {"line_number": "13", "description": "Wages and salaries", "line_type": "input", "source_facts": ["wages_salaries"], "sort_order": 15},
            {"line_number": "14", "description": "Depreciation (see instructions)", "line_type": "input", "source_facts": ["depreciation"], "source_rules": ["R004"], "sort_order": 16},
            {"line_number": "15", "description": "Reserved for future use", "line_type": "informational", "sort_order": 17},
            {"line_number": "16", "description": "Reserved for future use", "line_type": "informational", "sort_order": 18},
            {"line_number": "17", "description": "Other deductions (attach Schedule A (Form 8825))", "line_type": "input", "source_facts": ["other_expenses"], "source_rules": ["R006"], "sort_order": 19},
            {"line_number": "18", "description": "Total rental real estate expenses for each property. Add lines 3 through 17", "line_type": "subtotal", "source_rules": ["R001"], "sort_order": 20},
            {"line_number": "19", "description": "Income or (loss) from each rental real estate property. Subtract line 18 from line 2c", "line_type": "calculated", "source_rules": ["R002"], "sort_order": 21},
            {"line_number": "20a", "description": "Total rental real estate income. Add total rental real estate income from line 2c", "line_type": "subtotal", "source_rules": ["R003"], "sort_order": 22},
            {"line_number": "20b", "description": "Total rental real estate expenses. Add total rental real estate expenses from line 18 (shown in parentheses)", "line_type": "subtotal", "source_rules": ["R003"], "sort_order": 23},
            {"line_number": "21", "description": "Net gain (loss) from Form 4797, Part II, line 17, from the disposition of property from rental real estate activities", "line_type": "input", "source_facts": ["gain_4797_rental"], "source_rules": ["R003"], "sort_order": 24},
            {"line_number": "22a", "description": "Net income (loss) from rental real estate activities from partnerships, estates, and trusts in which this partnership or S corporation is a partner or beneficiary (from Schedule K-1)", "line_type": "input", "source_facts": ["passthrough_net_rental"], "source_rules": ["R003"], "sort_order": 25},
            {"line_number": "22b", "description": "Identify the partnerships, estates, or trusts from which net income (loss) is shown on line 22a — (1) Name, (2) EIN. Attach a statement if more space is needed", "line_type": "input", "source_facts": ["passthrough_identities"], "sort_order": 26},
            {"line_number": "23", "description": "Net rental real estate income (loss). Combine lines 20a through 22a. Enter the result here and on Schedule K, line 2, of Form 1065 or 1120-S", "line_type": "total", "source_rules": ["R003"], "destination_form": "Schedule K Line 2", "sort_order": 27},
            # Schedule A (Form 8825) (12-2025) — Rental Real Estate Other Deductions
            {"line_number": "A1", "description": "Asset management fee", "line_type": "input", "sort_order": 28},
            {"line_number": "A2", "description": "Bad debt expense", "line_type": "input", "sort_order": 29},
            {"line_number": "A3", "description": "Building maintenance", "line_type": "input", "sort_order": 30},
            {"line_number": "A4", "description": "Common charges", "line_type": "input", "sort_order": 31},
            {"line_number": "A5", "description": "Contract services", "line_type": "input", "sort_order": 32},
            {"line_number": "A6", "description": "Debt extinguishment costs", "line_type": "input", "sort_order": 33},
            {"line_number": "A7", "description": "Ground rent", "line_type": "input", "sort_order": 34},
            {"line_number": "A8", "description": "Grounds maintenance", "line_type": "input", "sort_order": 35},
            {"line_number": "A9", "description": "Homeowner association fee", "line_type": "input", "sort_order": 36},
            {"line_number": "A10", "description": "Incentive fee", "line_type": "input", "sort_order": 37},
            {"line_number": "A11", "description": "Landscaping", "line_type": "input", "sort_order": 38},
            {"line_number": "A12", "description": "Leased employee expense", "line_type": "input", "sort_order": 39},
            {"line_number": "A13", "description": "Management fee", "line_type": "input", "sort_order": 40},
            {"line_number": "A14", "description": "Other taxes", "line_type": "input", "sort_order": 41},
            {"line_number": "A15", "description": "Prepayment penalty", "line_type": "input", "sort_order": 42},
            {"line_number": "A16", "description": "Reimbursed wages/salaries (reimbursed to management co.)", "line_type": "input", "sort_order": 43},
            {"line_number": "A17", "description": "Section 481(a) adjustments", "line_type": "input", "sort_order": 44},
            {"line_number": "A18", "description": "Tenant renovations", "line_type": "input", "sort_order": 45},
            {"line_number": "A19", "description": "Tenant services", "line_type": "input", "sort_order": 46},
            {"line_number": "A20", "description": "Turnover expenses", "line_type": "input", "sort_order": 47},
            {"line_number": "A21", "description": "Reserved for future use", "line_type": "informational", "sort_order": 48},
            {"line_number": "A22", "description": "Reserved for future use", "line_type": "informational", "sort_order": 49},
            {"line_number": "A23", "description": "Reserved for future use", "line_type": "informational", "sort_order": 50},
            {"line_number": "A24", "description": "Reserved for future use", "line_type": "informational", "sort_order": 51},
            {"line_number": "A25", "description": "Reserved for future use", "line_type": "informational", "sort_order": 52},
            {"line_number": "A26", "description": "Reserved for future use", "line_type": "informational", "sort_order": 53},
            {"line_number": "A27", "description": "Reserved for future use", "line_type": "informational", "sort_order": 54},
            {"line_number": "A28", "description": "Reserved for future use", "line_type": "informational", "sort_order": 55},
            {"line_number": "A29", "description": "Reserved for future use", "line_type": "informational", "sort_order": 56},
            {"line_number": "A30", "description": "Other", "line_type": "input", "sort_order": 57},
            {"line_number": "A31", "description": "Total (Enter the total here and on Form 8825, line 17.)", "line_type": "total", "source_rules": ["R006"], "destination_form": "Form 8825 line 17", "sort_order": 58},
        ])
        # Stale pre-renumber line rows (bare "2", and any other row not on the
        # 12-2025 face map) — delete so a reseed self-heals.
        _2025_LINES = ({"1", "2a", "2b", "2c"} | {str(n) for n in range(3, 20)}
                       | {"20a", "20b", "21", "22a", "22b", "23"}
                       | {f"A{n}" for n in range(1, 32)})
        stale_lines = FormLine.objects.filter(tax_form=form).exclude(line_number__in=_2025_LINES)
        if stale_lines.exists():
            self.stdout.write(f"  deleting {stale_lines.count()} stale pre-renumber line rows")
            stale_lines.delete()
        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D001", "title": "No rents on property", "severity": "warning",
             "condition": "gross_rents == 0 AND other_rental_income == 0", "message": "Property listed but line 2c income = $0. Verify this property had rental activity."},
            {"diagnostic_id": "D002", "title": "Missing rental depreciation", "severity": "warning",
             "condition": "depreciation == 0 AND property has depreciable improvements", "message": "Rental property has no depreciation. Buildings and improvements should be depreciated."},
            {"diagnostic_id": "D003", "title": "More than 8 properties", "severity": "info",
             "condition": "property_count > 8", "message": "More than 8 rental properties — complete and attach as many additional pages of Form 8825 as needed (lines 20a-23 on page 1 only once, combining all pages)."},
            {"diagnostic_id": "D004", "title": "M-3 filer needs Schedule A (Form 8825)", "severity": "warning",
             "condition": "schedule_m3_required AND line_17 != 0 AND no Schedule A detail rows",
             "message": "This return has a Schedule M-3 filing requirement and amounts on Form 8825 line 17 — Schedule A (Form 8825) must be completed and attached for each property (i8825 Rev. 12-2025)."},
            {"diagnostic_id": "D005", "title": "Other-information code needs description", "severity": "info",
             "condition": "other_info_code in A-I", "message": "Line 1 column (c) code entered — include the relevant supplementary description on Form 8825 or on a separate statement (codes A-I; face page 2)."},
        ])
        self._upsert_tests(form, [
            {"scenario_name": "Single rental property — net income", "scenario_type": "normal",
             "inputs": {"gross_rents": 24000, "insurance": 1200, "mortgage_interest": 6000, "repairs": 800, "taxes": 3000, "depreciation": 5000, "utilities": 0, "other_expenses": 500},
             "expected_outputs": {"total_property_income": 24000, "total_expenses": 16500, "net_rent": 7500}, "sort_order": 1},
            {"scenario_name": "Net rental loss", "scenario_type": "normal",
             "inputs": {"gross_rents": 12000, "mortgage_interest": 8000, "taxes": 4000, "depreciation": 10000, "insurance": 2000},
             "expected_outputs": {"total_property_income": 12000, "total_expenses": 24000, "net_rent": -12000}, "sort_order": 2},
            {"scenario_name": "Line 2b other income + line 13 wages (new 12-2025 rows)", "scenario_type": "normal",
             "inputs": {"gross_rents": 10000, "other_rental_income": 500, "wages_salaries": 2000, "repairs": 1000},
             "expected_outputs": {"total_property_income": 10500, "total_expenses": 3000, "net_rent": 7500}, "sort_order": 3},
            {"scenario_name": "Line 23 combines 20a through 22a (21/22a included)", "scenario_type": "normal",
             "inputs": {"total_gross_rents": 34000, "total_expenses_all": 28500, "gain_4797_rental": 1200, "passthrough_net_rental": 300},
             "expected_outputs": {"total_net_rental": 7000}, "sort_order": 4},
            {"scenario_name": "Schedule A detail rows total to line 17", "scenario_type": "normal",
             "inputs": {"schedule_a_rows": [{"category": "A13", "amount": 1500}, {"category": "A11", "amount": 700}, {"category": "A30", "description": "Supplies", "amount": 300}]},
             "expected_outputs": {"schedule_a_total": 2500, "other_expenses": 2500}, "sort_order": 5},
        ])
        self._upsert_form_links("8825", sources, [("IRS_2025_8825_INSTR_FULL", "governs")])
        # Stale excerpts on the re-fetched instruction source (the 2026-03-18
        # fetch described a numbering that matches no published revision).
        _KEEP_LABELS = {
            "What's New (Rev. 12-2025) — which version, col (c) codes, 2a/2b split, Schedule A",
            "Line 1 — address, type codes 1-8, col (c) M-3-only note, codes A-I",
            "Line 17 Other Deductions + Schedule A (Form 8825) — M-3 conditional",
            "Line 14 Depreciation — Form 4562 attachment",
            "Line 8 Interest — section 163(j) pointer",
            "Specific Instructions — pages, 20a-23 once, scope exclusions",
            "Form 8825 (Rev. 12-2025) face — expense/summary line labels verbatim",
            "Schedule A (Form 8825) (12-2025) face — 31 lines verbatim",
        }
        src = sources.get("IRS_2025_8825_INSTR_FULL")
        if src is not None:
            stale_exc = AuthorityExcerpt.objects.filter(authority_source=src).exclude(excerpt_label__in=_KEEP_LABELS)
            if stale_exc.exists():
                self.stdout.write(f"  deleting {stale_exc.count()} stale 2026-03-18 excerpts")
                stale_exc.delete()
        self.stdout.write(self.style.SUCCESS("  8825 complete (Rev. 12-2025 face)."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Form 7203 — S Corporation Shareholder Stock and Debt Basis Limitation
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_7203(self, sources):
        form = self._upsert_form("7203", "Form 7203 — S Corporation Shareholder Stock and Debt Basis Limitation",
                                  ["1120S"],
                                  notes="Per-shareholder basis tracking. Stock basis cannot go below zero. Ordering: income -> distributions -> nondeductible -> losses.")
        self._upsert_facts(form, [
            {"fact_key": "stock_basis_boy", "label": "Stock basis at beginning of year (Line 1)", "data_type": "decimal", "required": True, "sort_order": 1},
            {"fact_key": "additional_stock", "label": "Stock acquired during year (Line 2)", "data_type": "decimal", "sort_order": 2},
            {"fact_key": "income_items", "label": "Pro rata share of income items from K-1 (Line 3)", "data_type": "decimal", "sort_order": 3},
            {"fact_key": "stock_basis_before_decreases", "label": "Subtotal before decreases (Line 4)", "data_type": "decimal", "sort_order": 4},
            {"fact_key": "distributions", "label": "Nondividend distributions from K-1 (Line 6)", "data_type": "decimal", "sort_order": 5},
            {"fact_key": "nondeductible_expenses", "label": "Nondeductible expenses from K-1 (Lines 7-8)", "data_type": "decimal", "sort_order": 6},
            {"fact_key": "losses_deductions", "label": "Losses and deductions from K-1 (Part III)", "data_type": "decimal", "sort_order": 7},
            {"fact_key": "stock_basis_eoy", "label": "Stock basis at end of year (Line 10)", "data_type": "decimal", "sort_order": 8},
            {"fact_key": "debt_basis_boy", "label": "Debt basis at beginning of year (Line 21)", "data_type": "decimal", "sort_order": 9},
            {"fact_key": "new_loans", "label": "New loans to corporation during year (Line 22)", "data_type": "decimal", "sort_order": 10},
            {"fact_key": "debt_basis_restoration", "label": "Debt basis restoration from net income (Line 23)", "data_type": "decimal", "sort_order": 11},
            {"fact_key": "debt_basis_eoy", "label": "Debt basis at end of year", "data_type": "decimal", "sort_order": 12},
            {"fact_key": "suspended_losses", "label": "Losses suspended (carried forward)", "data_type": "decimal", "sort_order": 13},
            {"fact_key": "prior_suspended_losses", "label": "Suspended losses from prior years", "data_type": "decimal", "sort_order": 14},
        ])
        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "Stock basis before decreases (Line 4)", "rule_type": "calculation",
             "formula": "stock_basis_boy + additional_stock + income_items",
             "inputs": ["stock_basis_boy", "additional_stock", "income_items"],
             "outputs": ["stock_basis_before_decreases"], "precedence": 1, "sort_order": 1},
            {"rule_id": "R002", "title": "Distributions reduce basis first (Line 6)", "rule_type": "calculation",
             "formula": "stock_after_dist = max(0, stock_basis_before_decreases - distributions)",
             "inputs": ["stock_basis_before_decreases", "distributions"],
             "outputs": ["stock_after_distributions"], "precedence": 2, "sort_order": 2,
             "description": "Distributions reduce stock basis but not below zero. Excess distributions are return of basis/capital gain per section 1368."},
            {"rule_id": "R003", "title": "Nondeductible expenses reduce next (Lines 7-8)", "rule_type": "calculation",
             "formula": "stock_after_nonded = max(0, stock_after_distributions - nondeductible_expenses)",
             "inputs": ["stock_after_distributions", "nondeductible_expenses"],
             "outputs": ["stock_after_nondeductible"], "precedence": 3, "sort_order": 3},
            {"rule_id": "R004", "title": "Losses reduce last — stock then debt (Part III)", "rule_type": "calculation",
             "formula": "allowed_from_stock = min(losses_deductions, stock_after_nondeductible); allowed_from_debt = min(remaining, debt_basis); suspended = total - allowed",
             "inputs": ["losses_deductions", "stock_after_nondeductible", "debt_basis_boy"],
             "outputs": ["stock_basis_eoy", "debt_basis_eoy", "suspended_losses"], "precedence": 4, "sort_order": 4,
             "description": "Losses first reduce stock basis to zero, then debt basis. Excess is suspended and carried forward indefinitely with character retained."},
            {"rule_id": "R005", "title": "Stock basis floor at zero", "rule_type": "validation",
             "formula": "stock_basis_eoy >= 0",
             "inputs": ["stock_basis_eoy"], "outputs": [], "precedence": 0, "sort_order": 5,
             "description": "Stock basis cannot go below zero. If computed negative, there is a calculation error."},
            {"rule_id": "R006", "title": "Debt basis restoration", "rule_type": "calculation",
             "formula": "debt_restoration = min(net_income_increase, prior_debt_reduction)",
             "inputs": ["income_items", "debt_basis_boy"], "outputs": ["debt_basis_restoration"],
             "precedence": 5, "sort_order": 6,
             "description": "Net income increases restore previously reduced debt basis, up to original loan face value."},
            {"rule_id": "R007", "title": "Distribution excess = capital gain", "rule_type": "conditional",
             "formula": "if distributions > stock_basis_before_decreases then excess = capital_gain",
             "inputs": ["distributions", "stock_basis_before_decreases"],
             "outputs": ["distribution_capital_gain"], "precedence": 2, "sort_order": 7,
             "description": "Distributions exceeding stock basis are treated as capital gain per section 1368. Report on Schedule D/Form 8949."},
        ])
        self._upsert_links(rules, sources, [
            ("R001", "IRS_2025_7203_INSTR_FULL", "primary", "Stock basis computation"),
            ("R001", "IRC_1367", "secondary", "Section 1367 — adjustments to basis"),
            ("R002", "IRS_2025_7203_INSTR_FULL", "primary", "Distributions reduce first, floor at zero"),
            ("R002", "IRC_1368", "secondary", "Section 1368 — distributions"),
            ("R003", "IRS_2025_7203_INSTR_FULL", "primary", "Nondeductible expenses reduce next"),
            ("R004", "IRS_2025_7203_INSTR_FULL", "primary", "Losses reduce last — stock then debt"),
            ("R004", "IRC_1366", "secondary", "Section 1366(d) — loss limitation"),
            ("R005", "IRS_2025_7203_INSTR_FULL", "primary", "Stock basis cannot be negative"),
            ("R006", "IRS_2025_7203_INSTR_FULL", "primary", "Debt basis restoration via net income"),
            ("R007", "IRC_1368", "primary", "Section 1368 — excess distributions = capital gain"),
        ])
        self._upsert_lines(form, [
            {"line_number": "1", "description": "Stock basis at beginning of tax year", "line_type": "input", "sort_order": 1},
            {"line_number": "2", "description": "Stock acquired during year", "line_type": "input", "sort_order": 2},
            {"line_number": "3", "description": "Pro rata share of all income items (from K-1)", "line_type": "calculated", "sort_order": 3},
            {"line_number": "4", "description": "Subtotal — stock basis before decreases", "line_type": "subtotal", "source_rules": ["R001"], "sort_order": 4},
            {"line_number": "6", "description": "Nondividend distributions (K-1 Box 16d)", "line_type": "input", "sort_order": 5},
            {"line_number": "7-8", "description": "Nondeductible expenses and oil/gas depletion", "line_type": "input", "sort_order": 6},
            {"line_number": "10", "description": "Stock basis at end of year (cannot be below zero)", "line_type": "total", "source_rules": ["R004"], "sort_order": 7},
            {"line_number": "21", "description": "Debt basis at beginning of year", "line_type": "input", "sort_order": 8},
            {"line_number": "22", "description": "New loans during year", "line_type": "input", "sort_order": 9},
            {"line_number": "23", "description": "Debt basis restoration", "line_type": "calculated", "source_rules": ["R006"], "sort_order": 10},
        ])
        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D001", "title": "Stock basis negative", "severity": "error",
             "condition": "stock_basis_eoy < 0", "message": "Stock basis computed as negative — this is a calculation error. Stock basis cannot go below zero."},
            {"diagnostic_id": "D002", "title": "Losses suspended", "severity": "info",
             "condition": "suspended_losses > 0", "message": "Losses exceed stock + debt basis and are suspended. Carried forward indefinitely with character retained."},
            {"diagnostic_id": "D003", "title": "Distribution exceeds basis", "severity": "warning",
             "condition": "distributions > stock_basis_before_decreases", "message": "Distributions exceed stock basis. Excess is capital gain to shareholder per section 1368."},
            {"diagnostic_id": "D004", "title": "No beginning basis", "severity": "warning",
             "condition": "stock_basis_boy == 0 AND additional_stock == 0", "message": "Beginning stock basis is $0 with no additions. All income/loss items will be limited."},
        ])
        self._upsert_tests(form, [
            {"scenario_name": "Sufficient basis — all items flow", "scenario_type": "normal",
             "inputs": {"stock_basis_boy": 100000, "additional_stock": 0, "income_items": 50000, "distributions": 30000, "nondeductible_expenses": 2000, "losses_deductions": 0},
             "expected_outputs": {"stock_basis_before_decreases": 150000, "stock_basis_eoy": 118000, "suspended_losses": 0}, "sort_order": 1},
            {"scenario_name": "Distribution exceeds basis — capital gain", "scenario_type": "edge",
             "inputs": {"stock_basis_boy": 20000, "additional_stock": 0, "income_items": 10000, "distributions": 50000, "nondeductible_expenses": 0, "losses_deductions": 0},
             "expected_outputs": {"stock_basis_before_decreases": 30000, "stock_basis_eoy": 0, "distribution_capital_gain": 20000}, "sort_order": 2},
            {"scenario_name": "Losses suspended — insufficient basis", "scenario_type": "edge",
             "inputs": {"stock_basis_boy": 15000, "additional_stock": 0, "income_items": 5000, "distributions": 0, "nondeductible_expenses": 0, "losses_deductions": 30000, "debt_basis_boy": 5000},
             "expected_outputs": {"stock_basis_eoy": 0, "debt_basis_eoy": 0, "suspended_losses": 5000}, "sort_order": 3,
             "notes": "20K stock basis absorbs 20K of losses. 5K debt basis absorbs 5K more. 5K suspended."},
            {"scenario_name": "Debt basis restoration", "scenario_type": "edge",
             "inputs": {"stock_basis_boy": 0, "income_items": 25000, "distributions": 0, "nondeductible_expenses": 0, "losses_deductions": 0, "debt_basis_boy": 10000, "prior_debt_reduction": 8000},
             "expected_outputs": {"stock_basis_eoy": 25000, "debt_basis_restoration": 8000}, "sort_order": 4,
             "notes": "Net income increase restores previously reduced debt basis."},
        ])
        self._upsert_form_links("7203", sources, [("IRS_2025_7203_INSTR_FULL", "governs"), ("IRC_1366", "governs"), ("IRC_1367", "governs"), ("IRC_1368", "informs")])
        self.stdout.write(self.style.SUCCESS("  7203 complete."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Expand Form 4562 — add OBBBA bonus and Section 179 detail rules
    # ═══════════════════════════════════════════════════════════════════════════

    def _expand_4562(self, sources):
        form = TaxForm.objects.filter(form_number="4562", jurisdiction="FED", tax_year=2025).first()
        if not form:
            self.stdout.write(self.style.WARNING("4562 not found — run load_1120s_specs first"))
            return
        rules = self._upsert_rules(form, [
            {"rule_id": "R010", "title": "Section 179 dollar limit (OBBBA 2025)", "rule_type": "calculation",
             "formula": "max_179 = 2500000; threshold = 4000000; reduction = max(0, total_placed - threshold); allowed = max(0, max_179 - reduction)",
             "inputs": ["total_section_179_placed_in_service"], "outputs": ["section_179_dollar_limit"],
             "precedence": 1, "sort_order": 10,
             "description": "OBBBA 2025: Section 179 max = $2,500,000, phaseout threshold = $4,000,000. Dollar-for-dollar reduction above threshold."},
            {"rule_id": "R011", "title": "Section 179 business income limitation", "rule_type": "calculation",
             "formula": "final_179 = min(dollar_limited_179, taxable_income_from_active_business)",
             "inputs": ["section_179_dollar_limit", "taxable_income_limitation"], "outputs": ["allowed_179_deduction"],
             "precedence": 2, "sort_order": 11,
             "description": "Section 179 cannot exceed taxable income from active conduct of trade or business. Excess carries forward."},
            {"rule_id": "R012", "title": "Bonus depreciation rate determination (OBBBA)", "rule_type": "conditional",
             "formula": "if acquired_after_2025_01_19 then 100%; elif acquired_before_2025_01_20 then 40%; else 0%",
             "inputs": ["acquisition_date"], "outputs": ["bonus_percentage"],
             "precedence": 1, "sort_order": 12,
             "description": "OBBBA: 100% for post-1/19/2025 acquisitions (permanent). 40% for pre-1/20/2025 (binding contract rule). Applies to MACRS property with recovery period <= 20 years.",
             "notes": "Georgia does NOT conform to federal bonus depreciation. GA addback required."},
            {"rule_id": "R013", "title": "Depreciation by destination (S-Corp)", "rule_type": "routing",
             "formula": "Page1_Line14 = trade_business_depr; Form8825_Line14 = rental_depr; ScheduleF = farm_depr; K_Line11 = section_179",
             "inputs": ["depreciation_by_activity"], "outputs": ["page1_line14", "form_8825_line14", "sched_f_depr", "k_line11"],
             "precedence": 5, "sort_order": 13,
             "description": "S-Corp depreciation is split by destination: trade/business -> Page 1 Line 14, rental -> Form 8825 Line 14, farm -> Schedule F, Section 179 -> K Line 11 (separately stated)."},
        ])
        self._upsert_links(rules, sources, [
            ("R010", "IRS_2025_4562_INSTR_FULL", "primary", "OBBBA 2025: $2.5M/$4M Section 179 limits"),
            ("R010", "IRC_179", "secondary", "IRC 179 election and limitations"),
            ("R011", "IRS_2025_4562_INSTR_FULL", "primary", "Business income limitation for Section 179"),
            ("R011", "IRC_179", "secondary", "IRC 179(b) — income limitation"),
            ("R012", "IRS_2025_4562_INSTR_FULL", "primary", "OBBBA bonus rates: 100%/40%"),
            ("R012", "IRC_168", "secondary", "IRC 168(k) bonus depreciation"),
            ("R013", "IRS_2025_4562_INSTR_FULL", "primary", "S-Corp depreciation by destination"),
            ("R013", "IRC_1363", "secondary", "IRC 1363(b) — separately stated items"),
        ])
        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D010", "title": "Section 179 exceeds dollar limit", "severity": "error",
             "condition": "elected_179 > 2500000", "message": "Section 179 election exceeds $2,500,000 OBBBA limit."},
            {"diagnostic_id": "D011", "title": "Section 179 limited by income", "severity": "warning",
             "condition": "elected_179 > taxable_income_limitation", "message": "Section 179 limited by business income. Excess carries forward to next year."},
            {"diagnostic_id": "D012", "title": "Bonus rate mismatch", "severity": "warning",
             "condition": "bonus_percentage != expected_rate_for_acquisition_date",
             "message": "Bonus depreciation rate does not match OBBBA rules for the acquisition date. Post-1/19/2025 = 100%, pre-1/20/2025 = 40%."},
            {"diagnostic_id": "D013", "title": "No depreciation destination", "severity": "error",
             "condition": "depreciation > 0 AND no destination specified",
             "message": "Depreciation claimed but not allocated to any destination (Page 1/8825/Schedule F)."},
        ])
        self._upsert_tests(form, [
            {"scenario_name": "MACRS 5-year property — annual deduction", "scenario_type": "normal",
             "inputs": {"cost_basis": 50000, "recovery_period": 5, "method": "200DB", "convention": "HY", "year_in_service": 1},
             "expected_outputs": {"current_year_depreciation": 10000},
             "notes": "Year 1 rate = 20% (Pub 946 Table A-1). $50,000 x 20% = $10,000.", "sort_order": 10},
            {"scenario_name": "Section 179 within limit — flows to K Line 11", "scenario_type": "normal",
             "inputs": {"elected_cost": 100000, "total_placed": 500000, "taxable_income_limitation": 200000},
             "expected_outputs": {"section_179_dollar_limit": 100000, "allowed_179_deduction": 100000, "destination": "K_Line_11"},
             "notes": "Under $2.5M limit, under $4M threshold, under income limit. Full amount to K Line 11.", "sort_order": 11},
            {"scenario_name": "Section 179 exceeds income limit — carryover", "scenario_type": "edge",
             "inputs": {"elected_cost": 150000, "total_placed": 500000, "taxable_income_limitation": 80000},
             "expected_outputs": {"section_179_dollar_limit": 150000, "allowed_179_deduction": 80000, "carryover": 70000},
             "notes": "$150K elected, income limit $80K. Deduct $80K this year, carry $70K forward.", "sort_order": 12},
            {"scenario_name": "Bonus depreciation — OBBBA 100% post-1/19/2025", "scenario_type": "normal",
             "inputs": {"cost_basis": 200000, "acquisition_date": "2025-06-15", "recovery_period": 7},
             "expected_outputs": {"bonus_percentage": 100, "bonus_amount": 200000},
             "notes": "Post-1/19/2025 acquisition: 100% bonus (permanent under OBBBA).", "sort_order": 13},
            {"scenario_name": "Mixed assets — split by destination", "scenario_type": "normal",
             "inputs": {"trade_business_depr": 15000, "rental_depr": 8000, "section_179": 25000},
             "expected_outputs": {"page1_line14": 15000, "form_8825_line14": 8000, "k_line11": 25000},
             "notes": "Trade/business depr -> Page 1 L14, rental depr -> 8825 L14, S179 -> K L11.", "sort_order": 14},
        ])
        self.stdout.write(self.style.SUCCESS("  4562 expanded."))

    # ═══════════════════════════════════════════════════════════════════════════
    # GA-600S — Georgia S-Corporation Tax Return
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_ga600s(self, sources):
        form = self._upsert_form("GA600S", "GA-600S — Georgia S-Corporation Tax Return", ["1120S"],
                                  jurisdiction="GA",
                                  notes="Georgia S-Corp return. GA does NOT conform to federal §168(k)/(n) bonus (addback), but CONFORMS to the OBBBA §179 limit ($2.5M/$4M) via HB 1199. PTET at 5.19% (TY2025) is elective.")
        self._upsert_facts(form, [
            # Schedule 1 — GA Taxable Income
            {"fact_key": "federal_taxable_income", "label": "Federal taxable income (from 1120-S Page 1 Line 21)", "data_type": "decimal", "required": True, "sort_order": 1},
            {"fact_key": "ga_addition_bonus_depr", "label": "Georgia addition: federal bonus depreciation (addback)", "data_type": "decimal", "sort_order": 2,
             "notes": "GA does NOT conform to IRC 168(k). Federal bonus depreciation must be added back."},
            {"fact_key": "ga_addition_other", "label": "Georgia addition: other items", "data_type": "decimal", "sort_order": 3},
            {"fact_key": "ga_subtraction_depr", "label": "Georgia subtraction: GA depreciation (computed under pre-bonus rules)", "data_type": "decimal", "sort_order": 4},
            {"fact_key": "ga_subtraction_other", "label": "Georgia subtraction: other items", "data_type": "decimal", "sort_order": 5},
            {"fact_key": "ga_taxable_income", "label": "Georgia taxable income (Schedule 1 result)", "data_type": "decimal", "sort_order": 6},
            # Schedule 2 — PTET
            {"fact_key": "ptet_elected", "label": "PTET election made?", "data_type": "boolean", "sort_order": 7},
            {"fact_key": "ptet_rate", "label": "PTET rate", "data_type": "decimal", "default_value": "5.19", "sort_order": 8},
            {"fact_key": "ptet_taxable_income", "label": "Income subject to PTET", "data_type": "decimal", "sort_order": 9},
            {"fact_key": "ptet_tax", "label": "PTET computed tax", "data_type": "decimal", "sort_order": 10},
            # Schedule 3 — Net Worth Tax
            {"fact_key": "total_assets", "label": "Total assets (from balance sheet)", "data_type": "decimal", "sort_order": 11},
            {"fact_key": "total_liabilities", "label": "Total liabilities (from balance sheet)", "data_type": "decimal", "sort_order": 12},
            {"fact_key": "net_worth", "label": "Net worth (assets - liabilities)", "data_type": "decimal", "sort_order": 13},
            {"fact_key": "net_worth_tax", "label": "Net worth tax (year = income year + 1)", "data_type": "decimal", "sort_order": 14,
             "notes": "NEEDS REVIEW: net worth tax brackets not fetched from GA DOR (site returned 404)."},
            # Schedule 4 — Apportionment
            {"fact_key": "ga_apportionment_pct", "label": "Georgia apportionment percentage", "data_type": "decimal", "default_value": "100.00", "sort_order": 15},
            {"fact_key": "property_factor", "label": "Property factor", "data_type": "decimal", "sort_order": 16},
            {"fact_key": "payroll_factor", "label": "Payroll factor", "data_type": "decimal", "sort_order": 17},
            {"fact_key": "sales_factor", "label": "Sales factor", "data_type": "decimal", "sort_order": 18},
        ])
        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "Schedule 1 — GA taxable income", "rule_type": "calculation",
             "formula": "federal_taxable_income + ga_addition_bonus_depr + ga_addition_other - ga_subtraction_depr - ga_subtraction_other",
             "inputs": ["federal_taxable_income", "ga_addition_bonus_depr", "ga_addition_other", "ga_subtraction_depr", "ga_subtraction_other"],
             "outputs": ["ga_taxable_income"], "precedence": 1, "sort_order": 1,
             "description": "Start with federal income, add GA additions (bonus depr addback), subtract GA subtractions (GA depreciation)."},
            {"rule_id": "R002", "title": "Georgia bonus depreciation addback", "rule_type": "calculation",
             "formula": "ga_addition_bonus_depr = federal_bonus_depreciation_taken",
             "inputs": ["federal_bonus_depreciation"], "outputs": ["ga_addition_bonus_depr"], "precedence": 0, "sort_order": 2,
             "description": "Georgia does NOT conform to IRC 168(k). ALL federal bonus depreciation must be added back on Schedule 1. Georgia computes its own depreciation under pre-bonus rules."},
            {"rule_id": "R003", "title": "Schedule 2 — PTET computation", "rule_type": "calculation",
             "formula": "ptet_tax = ptet_taxable_income * 0.0519",
             "inputs": ["ptet_taxable_income", "ptet_rate"], "outputs": ["ptet_tax"], "precedence": 2, "sort_order": 3,
             "description": "Pass-Through Entity Tax = GA taxable income * 5.19% (the flat rate for TY2025). Elective entity-level tax (HB 149).",
             "notes": "Rate CORRECTED 2026-07-05 (was 5.49%): Form 600S Rev. 09/11/25 hardcodes 5.19% for 2025 (same as Form 700; verified in the GA-700 research). Year-keyed — 2026 steps to 4.99%."},
            {"rule_id": "R004", "title": "Schedule 3 — Net worth tax", "rule_type": "calculation",
             "formula": "net_worth = total_assets - total_liabilities; tax = bracket_lookup(net_worth)",
             "inputs": ["total_assets", "total_liabilities"], "outputs": ["net_worth", "net_worth_tax"], "precedence": 3, "sort_order": 4,
             "description": "Net worth tax based on total assets minus liabilities. Bracket table applies. Net worth tax year = income tax year + 1.",
             "notes": "NEEDS REVIEW: Georgia net worth tax brackets not fetched (GA DOR site returned 404). Bracket table needs manual entry."},
            {"rule_id": "R005", "title": "Schedule 4 — Apportionment (single gross-receipts factor)", "rule_type": "calculation",
             "formula": "ga_apportionment_pct = ga_gross_receipts / total_gross_receipts (to six decimals)",
             "inputs": ["ga_gross_receipts", "total_gross_receipts"], "outputs": ["ga_apportionment_pct"],
             "precedence": 1, "sort_order": 5,
             "description": "CORRECTED 2026-07-05 (was a 3-factor property/payroll/sales average): Georgia apportions by a SINGLE gross-receipts factor for all taxpayers since 2008 (§48-7-31; IT-611 S-corp booklet, same rule as Form 700 Sch 7). Most single-state GA S-Corps = 100%."},
            {"rule_id": "R006", "title": "Georgia Section 179 limits", "rule_type": "validation",
             "formula": "ga_179_limit = 2500000; ga_179_phaseout = 4000000",
             "inputs": ["section_179_elected"], "outputs": [], "precedence": 0, "sort_order": 6,
             "description": "Georgia Section 179 limit is $2,500,000 with phaseout at $4,000,000 — EQUAL to federal. Georgia CONFORMS to the OBBBA Section 179 limit for TY2025 via HB 1199 (IRC conformity Jan 1, 2026, retroactive to tax years beginning on/after Jan 1, 2025), superseding the pre-OBBBA figures on the Aug-2025 GA Form 4562. (GA still decouples from §168(k)/(n) bonus.)"},
        ])
        self._upsert_links(rules, sources, [
            ("R001", "GA_2025_600S_INSTR", "primary", "Schedule 1 GA taxable income computation"),
            ("R002", "GA_2025_600S_INSTR", "primary", "GA does NOT conform to IRC 168(k) bonus"),
            ("R003", "GA_2025_600S_INSTR", "primary", "PTET at 5.19% (TY2025) — elective"),
            ("R004", "GA_2025_600S_INSTR", "primary", "Net worth tax — bracket lookup"),
            ("R005", "GA_2025_600S_INSTR", "primary", "single gross-receipts factor apportionment (§48-7-31)"),
            ("R006", "GA_2025_600S_INSTR", "primary", "GA Section 179: $2,500,000/$4,000,000 (conforms via HB 1199)"),
        ])
        self._upsert_lines(form, [
            {"line_number": "S1_1", "description": "Federal taxable income (from 1120-S Page 1 Line 21)", "line_type": "input", "destination_form": "1120-S Page 1 Line 21", "sort_order": 1},
            {"line_number": "S1_2", "description": "Georgia additions (bonus depreciation addback, etc.)", "line_type": "input", "sort_order": 2},
            {"line_number": "S1_3", "description": "Georgia subtractions (GA depreciation, etc.)", "line_type": "input", "sort_order": 3},
            {"line_number": "S1_4", "description": "Georgia taxable income", "line_type": "total", "source_rules": ["R001"], "sort_order": 4},
            {"line_number": "S2_1", "description": "PTET election and computation", "line_type": "calculated", "source_rules": ["R003"], "sort_order": 5},
            {"line_number": "S3_1", "description": "Net worth (assets - liabilities)", "line_type": "calculated", "source_rules": ["R004"], "sort_order": 6},
            {"line_number": "S3_2", "description": "Net worth tax (year = income year + 1)", "line_type": "calculated", "source_rules": ["R004"], "sort_order": 7},
            {"line_number": "S4_1", "description": "Georgia apportionment percentage", "line_type": "calculated", "source_rules": ["R005"], "sort_order": 8},
        ])
        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D001", "title": "Missing bonus depreciation addback", "severity": "error",
             "condition": "federal_bonus > 0 AND ga_addition_bonus_depr == 0",
             "message": "Federal return has bonus depreciation but no Georgia addback. GA does NOT conform to IRC 168(k)."},
            {"diagnostic_id": "D002", "title": "PTET rate verification", "severity": "info",
             "condition": "ptet_rate != 5.19", "message": "PTET rate is not 5.19% (the TY2025 Georgia flat rate). Verify against the current GA DOR Form 600S.",
             "notes": "Rate is year-keyed: 2024 = 5.39%, 2025 = 5.19%, 2026 = 4.99%. Re-verify each season."},
            {"diagnostic_id": "D003", "title": "Net worth tax year", "severity": "warning",
             "condition": "nw_tax_year != income_tax_year + 1", "message": "Net worth tax year should equal income tax year + 1."},
            {"diagnostic_id": "D004", "title": "100% apportionment but out-of-state activity", "severity": "warning",
             "condition": "ga_apportionment_pct == 100 AND has_out_of_state_activity",
             "message": "Apportionment is 100% but entity appears to have out-of-state activity. Verify."},
            {"diagnostic_id": "D005", "title": "GA nonconformity items", "severity": "info",
             "condition": "federal_return_has_obbba_items AND no_ga_adjustment",
             "message": "Federal return includes depreciation that Georgia does not conform to — chiefly §168(k)/(n) bonus (full addback on Schedule 1). Note GA DOES conform to the OBBBA §179 limit ($2.5M/$4M) via HB 1199. Review for required adjustments."},
        ])
        self._upsert_tests(form, [
            {"scenario_name": "Single-state GA S-Corp — no bonus difference", "scenario_type": "normal",
             "inputs": {"federal_taxable_income": 95000, "ga_addition_bonus_depr": 0, "ga_subtraction_depr": 0, "ga_apportionment_pct": 100},
             "expected_outputs": {"ga_taxable_income": 95000}, "sort_order": 1,
             "notes": "No bonus depreciation, so GA income = federal income."},
            {"scenario_name": "S-Corp with bonus depreciation — GA addback", "scenario_type": "normal",
             "inputs": {"federal_taxable_income": 50000, "ga_addition_bonus_depr": 100000, "ga_subtraction_depr": 14286, "ga_apportionment_pct": 100},
             "expected_outputs": {"ga_taxable_income": 135714}, "sort_order": 2,
             "notes": "Federal took $100K bonus. GA adds back $100K, subtracts $14,286 GA depreciation (7yr SL year 1). GA income much higher."},
            {"scenario_name": "PTET election", "scenario_type": "normal",
             "inputs": {"ptet_elected": True, "ptet_taxable_income": 200000, "ptet_rate": 5.19},
             "expected_outputs": {"ptet_tax": 10380}, "sort_order": 3,
             "notes": "$200K * 5.19% = $10,380 PTET (TY2025 rate)."},
            {"scenario_name": "Multi-state — 60% GA apportionment", "scenario_type": "edge",
             "inputs": {"federal_taxable_income": 200000, "ga_apportionment_pct": 60},
             "expected_outputs": {"ga_apportioned_income": 120000}, "sort_order": 4,
             "notes": "60% of $200K = $120K subject to GA tax."},
        ])
        self._upsert_form_links("GA600S", sources, [("GA_2025_600S_INSTR", "governs")])
        self.stdout.write(self.style.SUCCESS("  GA-600S complete."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Procedural Forms — Light Specs
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_procedural_forms(self, sources):
        # Form 7004 — Extension
        form = self._upsert_form("7004", "Form 7004 — Application for Automatic Extension of Time to File",
                                  ["1120S", "1065", "1120"],
                                  notes="Automatic 6-month extension. S-Corp due 3/15, extended to 9/15.")
        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "Automatic 6-month extension", "rule_type": "validation",
             "formula": "extended_due_date = original_due_date + 6_months",
             "inputs": ["original_due_date"], "outputs": ["extended_due_date"], "precedence": 1, "sort_order": 1,
             "description": "S-Corp original due: March 15. Extended due: September 15. No estimated tax payment required (pass-through entity)."},
            {"rule_id": "R002", "title": "Inclusion in print packages", "rule_type": "conditional",
             "formula": "include_in_print = extension_filed == True",
             "inputs": ["extension_filed"], "outputs": ["include_form_7004"], "precedence": 0, "sort_order": 2,
             "description": "Form 7004 only included in printed return if extension was filed."},
        ])
        self._upsert_links(rules, sources, [
            ("R001", "IRS_2025_1120S_INSTR", "primary", "1120-S filing deadlines"),
            ("R002", "IRS_2025_1120S_INSTR", "primary", "Extension filing requirement"),
        ])
        self._upsert_lines(form, [
            {"line_number": "1", "description": "Form code (25 for 1120-S)", "line_type": "input", "sort_order": 1},
            {"line_number": "5a", "description": "Tentative total tax (usually $0 for S-Corps)", "line_type": "input", "sort_order": 2},
        ])
        self.stdout.write(self.style.SUCCESS("  7004 complete (light)."))

        # Form 8879-S — IRS e-file Signature Authorization
        form = self._upsert_form("8879S", "Form 8879-S — IRS e-file Signature Authorization for Form 1120-S",
                                  ["1120S"], notes="Authorizes ERO to e-file. Requires taxpayer signature or PIN.")
        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "Signature authorization", "rule_type": "validation",
             "formula": "requires_officer_signature OR pin",
             "inputs": ["officer_signature", "pin"], "outputs": [], "precedence": 1, "sort_order": 1,
             "description": "Corporate officer must sign or provide PIN to authorize e-filing."},
        ])
        self._upsert_links(rules, sources, [("R001", "IRS_2025_1120S_INSTR", "primary", "E-file signature requirements")])
        self.stdout.write(self.style.SUCCESS("  8879-S complete (light)."))

        # Form 8453-S — E-file Declaration
        form = self._upsert_form("8453S", "Form 8453-S — U.S. S Corporation Income Tax Declaration for an IRS e-file Return",
                                  ["1120S"], notes="Declares what is being transmitted electronically.")
        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "E-file declaration", "rule_type": "validation",
             "formula": "lists_all_attached_schedules_and_forms",
             "inputs": ["attached_forms"], "outputs": [], "precedence": 1, "sort_order": 1,
             "description": "Lists all forms/schedules being transmitted electronically."},
        ])
        self._upsert_links(rules, sources, [("R001", "IRS_2025_1120S_INSTR", "primary", "E-file declaration requirements")])
        self.stdout.write(self.style.SUCCESS("  8453-S complete (light)."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Report
    # ═══════════════════════════════════════════════════════════════════════════

    def _report_totals(self):
        def _safe(text):
            return text.encode("ascii", errors="replace").decode("ascii")

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("DATABASE TOTALS (after load_remaining_1120s)")
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
        self.stdout.write(self.style.SUCCESS("Remaining 1120-S forms + GA-600S loaded successfully."))
