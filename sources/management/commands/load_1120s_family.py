"""Load authority sources for 1120-S form family: Schedule D, Form 8949, Form 4562, Form 1125-E.

Source material only — no full specs (rules/line map/tests). These forms interact with
Form 4797 in the S-Corp context. Content fetched from irs.gov 2025 instructions.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from sources.models import (
    AuthorityExcerpt,
    AuthorityFormLink,
    AuthoritySource,
    AuthoritySourceTopic,
    AuthorityTopic,
)


class Command(BaseCommand):
    help = "Load 1120-S family authority sources (Schedule D, 8949, 4562, 1125-E, IRC sections)"

    def handle(self, *_args, **_options):
        with transaction.atomic():
            self._load_topics()
            self._load_sources()
        self.stdout.write(self.style.SUCCESS("1120-S family sources loaded."))

    def _load_topics(self):
        new_topics = [
            ("schedule_d", "Schedule D", None),
            ("form_8949", "Form 8949", None),
            ("form_4562", "Form 4562", None),
            ("form_1125e", "Form 1125-E", None),
            ("officer_compensation", "Officer Compensation", None),
            ("macrs", "MACRS", "depreciation"),
        ]
        for code, name, parent_code in new_topics:
            parent = None
            if parent_code:
                parent = AuthorityTopic.objects.filter(topic_code=parent_code).first()
            AuthorityTopic.objects.get_or_create(
                topic_code=code, defaults={"topic_name": name, "parent_topic": parent},
            )
        self.stdout.write("Topics loaded.")

    def _load_sources(self):
        sources_data = [
            # ---------------------------------------------------------------
            # Schedule D (Form 1120-S)
            # ---------------------------------------------------------------
            {
                "source_code": "IRS_2025_1120S_SCHD_INSTR",
                "source_type": "official_instruction",
                "source_rank": "primary_official",
                "jurisdiction_code": "FED",
                "tax_year_start": 2025, "tax_year_end": 2025,
                "entity_type_code": "1120S",
                "title": "Instructions for Schedule D (Form 1120-S) — Capital Gains and Losses and Built-in Gains",
                "citation": "Schedule D (Form 1120-S) Instructions (2025)",
                "issuer": "IRS",
                "official_url": "https://www.irs.gov/instructions/i1120ssd",
                "current_status": "active",
                "is_substantive_authority": True,
                "is_filing_authority": True,
                "requires_human_review": False,
                "trust_score": 9.5,
                "topics": ["schedule_d", "capital_gains", "1231"],
                "excerpts": [
                    {
                        "excerpt_label": "Purpose — what Schedule D reports",
                        "location_reference": "General Instructions",
                        "excerpt_text": (
                            "Schedule D reports overall capital gains and losses from transactions reported on "
                            "Form 8949 and certain other capital transactions including installment sales, "
                            "like-kind exchanges, distributions of appreciated assets, and built-in gains tax."
                        ),
                        "summary_text": "Schedule D aggregates capital gains/losses from 8949 and other sources.",
                        "is_key_excerpt": True,
                        "topic_tags": ["schedule_d", "capital_gains"],
                    },
                    {
                        "excerpt_label": "Form 4797 → Schedule D flow",
                        "location_reference": "General Instructions",
                        "excerpt_text": (
                            "Form 4797 results feed into Schedule D — gains from Form 4797 Part I "
                            "(net §1231 gain treated as long-term capital gain) are reported on Schedule D. "
                            "Form 4797 handles depreciable business property; Schedule D handles capital assets "
                            "and aggregates the §1231 results."
                        ),
                        "summary_text": "4797 Part I net §1231 gain flows to Schedule D as LTCG.",
                        "is_key_excerpt": True,
                        "topic_tags": ["schedule_d", "4797", "1231"],
                    },
                    {
                        "excerpt_label": "Short-term vs long-term holding periods",
                        "location_reference": "Parts I and II",
                        "excerpt_text": (
                            "Report short-term gains or losses in Part I. Report long-term gains or losses in "
                            "Part II. The holding period for short-term capital gains and losses is generally "
                            "1 year or less. The holding period for long-term capital gains and losses is "
                            "generally more than 1 year. An exception applies for certain sales of applicable "
                            "partnership interests with a 3-year holding threshold under section 1061."
                        ),
                        "summary_text": "Short-term ≤1 year → Part I. Long-term >1 year → Part II.",
                        "is_key_excerpt": True,
                        "topic_tags": ["schedule_d", "holding_period"],
                    },
                    {
                        "excerpt_label": "Schedule D → Schedule K flow",
                        "location_reference": "Schedule K interface",
                        "excerpt_text": (
                            "Schedule D results flow to Schedule K for S-Corp reporting. The 28% rate gain or "
                            "loss goes on Schedule K, line 8b. Net short-term capital gain/loss flows to "
                            "Schedule K line 8a. Net long-term capital gain/loss flows to Schedule K line 9a. "
                            "Investment interest expense reported on Schedule K, line 12c."
                        ),
                        "summary_text": "Sch D → Sch K: line 8a (ST), 8b (28% rate), 9a (LT).",
                        "is_key_excerpt": True,
                        "topic_tags": ["schedule_d", "passthrough"],
                    },
                    {
                        "excerpt_label": "Form 8949 prerequisite",
                        "location_reference": "Line Instructions",
                        "excerpt_text": (
                            "Complete all necessary pages of Form 8949 before you complete line 1b, 2, 3, "
                            "8b, 9, or 10 of Schedule D. Form 8949 handles capital asset transactions; "
                            "Form 4797 covers business property. Transactions cannot be reported on both."
                        ),
                        "summary_text": "Must complete Form 8949 first. 8949 = capital assets, 4797 = business property.",
                        "is_key_excerpt": True,
                        "topic_tags": ["schedule_d", "form_8949"],
                    },
                ],
                "form_links": [
                    {"form_code": "SCHD_1120S", "link_type": "governs"},
                ],
            },
            # ---------------------------------------------------------------
            # IRC §1222 — Capital Gains/Losses definitions
            # ---------------------------------------------------------------
            {
                "source_code": "IRC_1222",
                "source_type": "code_section",
                "source_rank": "controlling",
                "jurisdiction_code": "FED",
                "title": "IRC §1222 — Other Terms Relating to Capital Gains and Losses",
                "citation": "26 U.S.C. §1222",
                "issuer": "Congress",
                "current_status": "active",
                "is_substantive_authority": True,
                "requires_human_review": True,
                "trust_score": 10.0,
                "notes": "Statutory text not directly fetched. Definitions referenced in Schedule D and Form 8949 instructions.",
                "topics": ["capital_gains", "holding_period"],
                "excerpts": [
                    {
                        "excerpt_label": "Short-term and long-term definitions",
                        "location_reference": "§1222(1)-(4)",
                        "excerpt_text": (
                            "Short-term capital gain: gain from sale or exchange of a capital asset held for "
                            "not more than 1 year. Long-term capital gain: held for more than 1 year. "
                            "Short-term capital loss and long-term capital loss follow the same holding period "
                            "distinction. Net capital gain means the excess of net long-term capital gain "
                            "over net short-term capital loss."
                        ),
                        "summary_text": "Defines ST (≤1yr) and LT (>1yr) capital gains/losses and net capital gain.",
                        "is_key_excerpt": True,
                        "topic_tags": ["capital_gains", "holding_period"],
                    },
                ],
                "form_links": [
                    {"form_code": "SCHD_1120S", "link_type": "governs"},
                    {"form_code": "8949", "link_type": "governs"},
                ],
            },
            # ---------------------------------------------------------------
            # Form 8949
            # ---------------------------------------------------------------
            {
                "source_code": "IRS_2025_8949_INSTR",
                "source_type": "official_instruction",
                "source_rank": "primary_official",
                "jurisdiction_code": "FED",
                "tax_year_start": 2025, "tax_year_end": 2025,
                "entity_type_code": "shared",
                "title": "Instructions for Form 8949 — Sales and Other Dispositions of Capital Assets",
                "citation": "Form 8949 Instructions (2025)",
                "issuer": "IRS",
                "official_url": "https://www.irs.gov/instructions/i8949",
                "current_status": "active",
                "is_substantive_authority": True,
                "is_filing_authority": True,
                "requires_human_review": False,
                "trust_score": 9.5,
                "topics": ["form_8949", "capital_gains", "dispositions"],
                "excerpts": [
                    {
                        "excerpt_label": "Purpose and who files",
                        "location_reference": "General Instructions",
                        "excerpt_text": (
                            "Use Form 8949 to report sales and exchanges of capital assets. Form 8949 allows "
                            "you and the IRS to reconcile amounts that were reported to you and the IRS on "
                            "Form 1099-B, Form 1099-DA, or Form 1099-S with the amounts you report on your return. "
                            "File Form 8949 with the Schedule D for the return you are filing."
                        ),
                        "summary_text": "8949 reconciles capital asset sales reported on 1099-B/DA/S with tax return.",
                        "is_key_excerpt": True,
                        "topic_tags": ["form_8949", "capital_gains"],
                    },
                    {
                        "excerpt_label": "8949 vs Schedule D vs Form 4797 distinction",
                        "location_reference": "General Instructions",
                        "excerpt_text": (
                            "Form 8949 handles capital asset dispositions reported on Forms 1099-B/1099-DA/1099-S. "
                            "Form 4797 handles business property dispositions. To report a gain from Form 6252 or "
                            "Part I of Form 4797 goes on Schedule D, not directly on Form 8949. Transactions "
                            "cannot be reported on both Form 8949 and Form 4797 simultaneously."
                        ),
                        "summary_text": "8949 = capital assets. 4797 = business property. 4797 Part I gains → Schedule D.",
                        "is_key_excerpt": True,
                        "topic_tags": ["form_8949", "4797", "schedule_d"],
                    },
                    {
                        "excerpt_label": "Reporting categories (Boxes A-F, G-L)",
                        "location_reference": "Specific Instructions",
                        "excerpt_text": (
                            "Part I (Short-Term): Box A/G — transactions with 1099-B/DA showing reported basis. "
                            "Box B/H — transactions without basis reported to IRS. Box C/I — transactions without "
                            "1099-B/DA. Part II (Long-Term): Box D/J, E/K, F/L follow the same pattern. "
                            "Do not use box C or F to report digital asset transactions — use box I or L instead."
                        ),
                        "summary_text": "6 categories based on basis reporting status and short/long-term.",
                        "is_key_excerpt": True,
                        "topic_tags": ["form_8949"],
                    },
                    {
                        "excerpt_label": "Holding period rules",
                        "location_reference": "Specific Instructions",
                        "excerpt_text": (
                            "The holding period for short-term capital gains and losses is generally 1 year or "
                            "less; report on Part I. Long-term is generally more than 1 year; report on Part II. "
                            "To figure the holding period, begin counting on the day after you received the "
                            "property and include the day you disposed of it. Generally, if you disposed of "
                            "property that you acquired by inheritance, report as long-term regardless of how "
                            "long you held the property."
                        ),
                        "summary_text": "Count from day after acquisition through disposal day. Inherited = always LT.",
                        "is_key_excerpt": True,
                        "topic_tags": ["form_8949", "holding_period"],
                    },
                ],
                "form_links": [
                    {"form_code": "8949", "link_type": "governs"},
                ],
            },
            # ---------------------------------------------------------------
            # Form 4562
            # ---------------------------------------------------------------
            {
                "source_code": "IRS_2025_4562_INSTR",
                "source_type": "official_instruction",
                "source_rank": "primary_official",
                "jurisdiction_code": "FED",
                "tax_year_start": 2025, "tax_year_end": 2025,
                "entity_type_code": "shared",
                "title": "Instructions for Form 4562 — Depreciation and Amortization",
                "citation": "Form 4562 Instructions (2025)",
                "issuer": "IRS",
                "official_url": "https://www.irs.gov/instructions/i4562",
                "current_status": "active",
                "is_substantive_authority": True,
                "is_filing_authority": True,
                "requires_human_review": False,
                "trust_score": 9.5,
                "topics": ["form_4562", "depreciation", "section_179", "bonus_depreciation"],
                "excerpts": [
                    {
                        "excerpt_label": "Purpose and who must file",
                        "location_reference": "General Instructions",
                        "excerpt_text": (
                            "Use Form 4562 to claim your deduction for depreciation and amortization, make the "
                            "election under section 179 to expense certain property, and provide information on "
                            "the business/investment use of automobiles and other listed property. Complete Form "
                            "4562 if claiming depreciation for property placed in service during 2025, a section "
                            "179 expense deduction, depreciation on listed property, or amortization beginning "
                            "in 2025."
                        ),
                        "summary_text": "4562 claims depreciation, §179, and amortization deductions.",
                        "is_key_excerpt": True,
                        "topic_tags": ["form_4562", "depreciation"],
                    },
                    {
                        "excerpt_label": "Part I — Section 179 Expense (OBBBA limits)",
                        "location_reference": "Part I Instructions",
                        "excerpt_text": (
                            "2025 Section 179 limits: Maximum deduction $2,500,000. Phase-out threshold "
                            "$4,000,000 (reduction begins dollar-for-dollar above this). SUV limitation: "
                            "$31,300 maximum. Election must be made on Form 4562 filed with the original "
                            "return. The election applies only to property used predominantly (>50%) in "
                            "active business conduct. Business income limitation: deduction cannot exceed "
                            "taxable income from active business operations. Disallowed amounts carry forward."
                        ),
                        "summary_text": "§179: $2.5M limit, $4M phaseout (OBBBA). Must be >50% business use.",
                        "is_key_excerpt": True,
                        "topic_tags": ["section_179", "form_4562"],
                    },
                    {
                        "excerpt_label": "Part II — Bonus Depreciation (OBBBA)",
                        "location_reference": "Part II Instructions",
                        "excerpt_text": (
                            "The One Big Beautiful Bill Act reinstated the 100% special depreciation allowance "
                            "for certain qualified property acquired and placed in service after January 19, 2025, "
                            "including certain specified plants bearing fruits and nuts planted or grafted after "
                            "January 19, 2025. Taxpayers may elect 40% allowance (60% for long-production-period "
                            "property) instead of 100% in the first tax year ending after that date. For qualified "
                            "property acquired September 27, 2017 through January 20, 2025: limited to 40% of "
                            "depreciable basis (60% for long-production-period property and aircraft). New section "
                            "168(n) allows 100% special depreciation for qualified production property placed in "
                            "service after July 4, 2025, construction begun or acquired after January 19, 2025."
                        ),
                        "summary_text": "OBBBA: 100% bonus for property acquired/placed in service after 1/19/2025. 40% for pre-1/20/2025 acquisitions.",
                        "is_key_excerpt": True,
                        "topic_tags": ["bonus_depreciation", "form_4562"],
                    },
                    {
                        "excerpt_label": "Part III — MACRS Depreciation",
                        "location_reference": "Part III Instructions",
                        "excerpt_text": (
                            "MACRS applies to tangible property placed in service after 1986. Depreciation is "
                            "computed using: recovery period (3, 5, 7, 10, 15, 20, 25, 27.5, 39, or 50 years); "
                            "convention (half-year, mid-quarter, or mid-month); method (200% declining balance, "
                            "150% declining balance, or straight-line). Half-year convention applies unless property "
                            "placed in service in last 3 months exceeds 40% of annual basis (triggering mid-quarter). "
                            "Mid-month applies only to residential rental, nonresidential real, and railroad gradings."
                        ),
                        "summary_text": "MACRS: recovery period + convention + method. HY default, MQ if >40% in Q4, MM for real property.",
                        "is_key_excerpt": True,
                        "topic_tags": ["depreciation", "macrs", "form_4562"],
                    },
                    {
                        "excerpt_label": "Depreciation recapture reference",
                        "location_reference": "General Instructions",
                        "excerpt_text": (
                            "When you dispose of property for which you claimed a special depreciation allowance, "
                            "any gain on the disposition is generally recaptured (included in income) as ordinary "
                            "income up to the amount of the depreciation previously allowed or allowable. For "
                            "listed property, conversion to personal use triggers recapture of excess depreciation "
                            "claimed under accelerated methods. Recapture is reported on Form 4797."
                        ),
                        "summary_text": "Depreciation recapture on disposition → ordinary income → Form 4797.",
                        "is_key_excerpt": True,
                        "topic_tags": ["recapture", "form_4562", "4797"],
                    },
                ],
                "form_links": [
                    {"form_code": "4562", "link_type": "governs"},
                    {"form_code": "4797", "link_type": "informs", "note": "Depreciation from 4562 feeds into 4797 recapture calculations"},
                ],
            },
            # ---------------------------------------------------------------
            # IRC §179
            # ---------------------------------------------------------------
            {
                "source_code": "IRC_179",
                "source_type": "code_section",
                "source_rank": "controlling",
                "jurisdiction_code": "FED",
                "title": "IRC §179 — Election to Expense Certain Depreciable Business Assets",
                "citation": "26 U.S.C. §179",
                "issuer": "Congress",
                "current_status": "active",
                "is_substantive_authority": True,
                "requires_human_review": True,
                "trust_score": 10.0,
                "notes": "Statutory text not directly fetched. Key provisions from 4562 instructions which reflect OBBBA amendments.",
                "topics": ["section_179", "depreciation"],
                "excerpts": [
                    {
                        "excerpt_label": "§179(b) limitations (OBBBA)",
                        "location_reference": "§179(b)",
                        "excerpt_text": (
                            "Section 179(b) limits: maximum deduction $2,500,000 (as amended by OBBBA). "
                            "Phase-out begins at $4,000,000 of property placed in service. The deduction is "
                            "further limited to taxable income from active business operations. Excess carries "
                            "forward to subsequent years."
                        ),
                        "summary_text": "$2.5M limit, $4M phaseout under OBBBA. Business income limitation applies.",
                        "is_key_excerpt": True,
                        "topic_tags": ["section_179"],
                    },
                    {
                        "excerpt_label": "§179(d)(10) — Recapture",
                        "location_reference": "§179(d)(10)",
                        "excerpt_text": (
                            "If property for which a §179 deduction was claimed is no longer used predominantly "
                            "(more than 50%) in a trade or business, the excess §179 deduction is recaptured as "
                            "ordinary income. Reported on Form 4797 Part IV."
                        ),
                        "summary_text": "§179 recapture when business use drops to 50% or less → 4797 Part IV.",
                        "is_key_excerpt": True,
                        "topic_tags": ["section_179", "section_179_recapture", "4797"],
                    },
                ],
                "form_links": [
                    {"form_code": "4562", "link_type": "governs"},
                    {"form_code": "4797", "link_type": "governs", "note": "§179(d)(10) recapture → 4797 Part IV"},
                ],
            },
            # ---------------------------------------------------------------
            # IRC §168 — MACRS / Bonus Depreciation
            # ---------------------------------------------------------------
            {
                "source_code": "IRC_168",
                "source_type": "code_section",
                "source_rank": "controlling",
                "jurisdiction_code": "FED",
                "title": "IRC §168 — Accelerated Cost Recovery System",
                "citation": "26 U.S.C. §168",
                "issuer": "Congress",
                "current_status": "active",
                "is_substantive_authority": True,
                "requires_human_review": True,
                "trust_score": 10.0,
                "notes": "Statutory text not directly fetched. Key provisions from 4562 instructions which reflect OBBBA amendments.",
                "topics": ["depreciation", "bonus_depreciation", "macrs"],
                "excerpts": [
                    {
                        "excerpt_label": "§168(k) — Bonus depreciation (OBBBA)",
                        "location_reference": "§168(k)",
                        "excerpt_text": (
                            "As amended by OBBBA (signed July 4, 2025): 100% special depreciation allowance "
                            "for qualified property acquired AND placed in service after January 19, 2025 "
                            "(permanent). 40% for property acquired before January 20, 2025 (binding contract "
                            "rule applies). Section 168(n) added: 100% for qualified production property placed "
                            "in service after July 4, 2025, construction begun after January 19, 2025."
                        ),
                        "summary_text": "OBBBA: 100% bonus after 1/19/2025 (permanent). 40% for pre-1/20/2025. New §168(n) for production property.",
                        "is_key_excerpt": True,
                        "topic_tags": ["bonus_depreciation"],
                    },
                    {
                        "excerpt_label": "§168(a)-(e) — MACRS general rules",
                        "location_reference": "§168(a)-(e)",
                        "excerpt_text": (
                            "MACRS recovery periods: 3, 5, 7, 10, 15, 20, 25, 27.5, 39, or 50 years depending "
                            "on property class. Methods: 200% DB, 150% DB, or straight-line. Conventions: half-year "
                            "(default), mid-quarter (if >40% placed in service in last quarter), mid-month (real "
                            "property only). Solar/wind energy property removed from 5-year class for property "
                            "beginning construction after December 31, 2024."
                        ),
                        "summary_text": "MACRS classes, methods, conventions. Solar/wind reclassified after 12/31/2024.",
                        "is_key_excerpt": True,
                        "topic_tags": ["depreciation", "macrs"],
                    },
                ],
                "form_links": [
                    {"form_code": "4562", "link_type": "governs"},
                ],
            },
            # ---------------------------------------------------------------
            # Form 1125-E
            # ---------------------------------------------------------------
            {
                "source_code": "IRS_2025_1125E_INSTR",
                "source_type": "official_instruction",
                "source_rank": "primary_official",
                "jurisdiction_code": "FED",
                "tax_year_start": 2025, "tax_year_end": 2025,
                "entity_type_code": "shared",
                "title": "Instructions for Form 1125-E — Compensation of Officers",
                "citation": "Form 1125-E Instructions (2025)",
                "issuer": "IRS",
                "official_url": "https://www.irs.gov/instructions/i1125e",
                "current_status": "active",
                "is_substantive_authority": True,
                "is_filing_authority": True,
                "requires_human_review": False,
                "trust_score": 9.0,
                "topics": ["form_1125e", "officer_compensation"],
                "excerpts": [
                    {
                        "excerpt_label": "Who must file",
                        "location_reference": "General Instructions",
                        "excerpt_text": (
                            "Form 1125-E must be filed with Form 1120, 1120-C, 1120-F, 1120-RIC, 1120-REIT, "
                            "or 1120S when the entity has total receipts of $500,000 or more and deducts officer "
                            "compensation. Total receipts are calculated differently by entity type, generally "
                            "combining gross income lines from the respective corporate return."
                        ),
                        "summary_text": "Required when total receipts ≥$500K and officer compensation is deducted.",
                        "is_key_excerpt": True,
                        "topic_tags": ["form_1125e", "officer_compensation"],
                    },
                    {
                        "excerpt_label": "Compensation included",
                        "location_reference": "Line Instructions",
                        "excerpt_text": (
                            "Column (f) encompasses salaries, commissions, bonuses, and taxable fringe benefits "
                            "provided to officers. For S corporations specifically, fringe benefits must be "
                            "included for officers owning more than 2% of stock but excluded for those owning "
                            "2% or less. Line 3: enter compensation deductible elsewhere on the return, such as "
                            "amounts in cost of goods sold or retirement plan contributions. Line 4: transfer "
                            "total from Line 2 to Form 1120 page 1, line 12 (or applicable entity return line)."
                        ),
                        "summary_text": "Includes salary, bonus, commission, fringe. S-Corp >2% owner fringe included.",
                        "is_key_excerpt": True,
                        "topic_tags": ["officer_compensation", "form_1125e"],
                    },
                    {
                        "excerpt_label": "Reasonable compensation — §162(m)",
                        "location_reference": "Line Instructions",
                        "excerpt_text": (
                            "Section 162(m) limitations: publicly held corporations cannot deduct compensation "
                            "exceeding $1 million for covered employees (principal executive/financial officers, "
                            "three highest-paid officers, or prior covered employees). Exceptions apply for "
                            "pre-1993 binding contracts and certain benefits excluded from employee income."
                        ),
                        "summary_text": "§162(m) $1M cap for public companies. S-Corps subject to reasonable compensation scrutiny.",
                        "is_key_excerpt": True,
                        "topic_tags": ["officer_compensation"],
                    },
                ],
                "form_links": [
                    {"form_code": "1125E", "link_type": "governs"},
                ],
            },
        ]

        count = 0
        for src_data in sources_data:
            excerpts_data = src_data.pop("excerpts", [])
            topic_codes = src_data.pop("topics", [])
            form_links_data = src_data.pop("form_links", [])

            source, _ = AuthoritySource.objects.update_or_create(
                source_code=src_data["source_code"], defaults=src_data,
            )
            count += 1

            for exc in excerpts_data:
                AuthorityExcerpt.objects.update_or_create(
                    authority_source=source, excerpt_label=exc["excerpt_label"], defaults=exc,
                )

            for tc in topic_codes:
                topic = AuthorityTopic.objects.filter(topic_code=tc).first()
                if topic:
                    AuthoritySourceTopic.objects.get_or_create(authority_source=source, authority_topic=topic)

            for fl in form_links_data:
                AuthorityFormLink.objects.get_or_create(
                    authority_source=source, form_code=fl["form_code"], link_type=fl["link_type"],
                    defaults={"note": fl.get("note", f"{source.source_code} → {fl['form_code']}")},
                )

        self.stdout.write(f"Loaded {count} authority sources with excerpts and form links.")
