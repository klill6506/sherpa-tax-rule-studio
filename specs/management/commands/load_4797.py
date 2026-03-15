"""Load Form 4797 (Sales of Business Property) — full spec with real IRS content.

Sources are loaded with content fetched from irs.gov (2025 instructions).
IRC section text marked requires_human_review=True since statutory text
cannot be directly fetched in clean form.
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


class Command(BaseCommand):
    help = "Load Form 4797 spec with real IRS authority sources"

    def handle(self, *_args, **_options):
        with transaction.atomic():
            self._load_topics()
            sources = self._load_sources()
            form = self._load_form()
            self._load_facts(form)
            rules = self._load_rules(form)
            self._link_authorities(rules, sources)
            self._load_lines(form)
            self._load_diagnostics(form)
            self._load_tests(form)
            self._load_form_links(sources)
        self.stdout.write(self.style.SUCCESS("Form 4797 loaded successfully."))

    def _load_topics(self):
        new_topics = [
            ("4797", "Form 4797", None),
            ("capital_gains", "Capital Gains", None),
            ("ordinary_income", "Ordinary Income", None),
            ("holding_period", "Holding Period", None),
            ("section_179_recapture", "Section 179 Recapture", "recapture"),
        ]
        for code, name, parent_code in new_topics:
            parent = None
            if parent_code:
                parent = AuthorityTopic.objects.filter(topic_code=parent_code).first()
            AuthorityTopic.objects.get_or_create(
                topic_code=code, defaults={"topic_name": name, "parent_topic": parent},
            )
        self.stdout.write("Topics loaded.")

    def _load_sources(self) -> dict[str, AuthoritySource]:
        sources_data = [
            # --- IRC Sections (statutory text not directly fetchable) ---
            {
                "source_code": "IRC_1231",
                "source_type": "code_section",
                "source_rank": "controlling",
                "jurisdiction_code": "FED",
                "title": "IRC §1231 — Property Used in the Trade or Business",
                "citation": "26 U.S.C. §1231",
                "issuer": "Congress",
                "current_status": "active",
                "is_substantive_authority": True,
                "requires_human_review": True,
                "trust_score": 10.0,
                "notes": "Statutory text not fetched from web — excerpts derived from IRS instructions and Pub 544 which quote/paraphrase the statute. Ken to verify exact statutory language.",
                "topics": ["1231", "dispositions", "capital_gains"],
                "excerpts": [
                    {
                        "excerpt_label": "§1231 netting rule (from Pub 544)",
                        "location_reference": "§1231(a)",
                        "excerpt_text": (
                            "Section 1231 transactions include gains and losses from property used in business "
                            "held over one year. Net gains from Section 1231 transactions receive capital gain "
                            "treatment; net losses are treated as ordinary losses. The 'nonrecaptured section 1231 "
                            "losses' from prior 5 years cause current gains to be treated as ordinary income."
                        ),
                        "summary_text": "Net §1231 gains = LTCG. Net §1231 losses = ordinary. 5-year lookback applies.",
                        "is_key_excerpt": True,
                        "topic_tags": ["1231", "capital_gains"],
                    },
                    {
                        "excerpt_label": "§1231 property definition (from Pub 544)",
                        "location_reference": "§1231(b)",
                        "excerpt_text": (
                            "Section 1231 property includes depreciable property and real property used in a "
                            "trade or business and held for more than 1 year. It also includes certain involuntary "
                            "conversions of business property and capital assets held in connection with a trade "
                            "or business."
                        ),
                        "summary_text": "§1231 = depreciable/real property used in business, held >1 year.",
                        "is_key_excerpt": True,
                        "topic_tags": ["1231", "holding_period"],
                    },
                ],
            },
            {
                "source_code": "IRC_1245",
                "source_type": "code_section",
                "source_rank": "controlling",
                "jurisdiction_code": "FED",
                "title": "IRC §1245 — Gain from Dispositions of Certain Depreciable Property",
                "citation": "26 U.S.C. §1245",
                "issuer": "Congress",
                "current_status": "active",
                "is_substantive_authority": True,
                "requires_human_review": True,
                "trust_score": 10.0,
                "notes": "Statutory text not directly fetched. Excerpts from Pub 544 and 4797 instructions.",
                "topics": ["1245", "recapture", "depreciation", "ordinary_income"],
                "excerpts": [
                    {
                        "excerpt_label": "§1245 recapture rule (from Pub 544)",
                        "location_reference": "§1245(a)(1)",
                        "excerpt_text": (
                            "Section 1245 property includes tangible depreciable personal property. Gain is "
                            "treated as ordinary income to the extent of 'depreciation allowed or allowable.' "
                            "The rule recaptures ALL depreciation taken, not just excess over straight-line."
                        ),
                        "summary_text": "§1245 recaptures ALL depreciation as ordinary income on gain.",
                        "is_key_excerpt": True,
                        "topic_tags": ["1245", "recapture", "ordinary_income"],
                    },
                ],
            },
            {
                "source_code": "IRC_1250",
                "source_type": "code_section",
                "source_rank": "controlling",
                "jurisdiction_code": "FED",
                "title": "IRC §1250 — Gain from Dispositions of Certain Depreciable Realty",
                "citation": "26 U.S.C. §1250",
                "issuer": "Congress",
                "current_status": "active",
                "is_substantive_authority": True,
                "requires_human_review": True,
                "trust_score": 10.0,
                "notes": "Statutory text not directly fetched. Excerpts from Pub 544.",
                "topics": ["1250", "recapture", "depreciation"],
                "excerpts": [
                    {
                        "excerpt_label": "§1250 additional depreciation recapture (from Pub 544)",
                        "location_reference": "§1250(a)",
                        "excerpt_text": (
                            "Section 1250 property is depreciable real property. 'Additional Depreciation' "
                            "subject to recapture is limited by an 'Applicable Percentage' based on holding "
                            "period and property type. For post-1986 MACRS real property depreciated using "
                            "straight-line, additional depreciation is zero, so §1250 ordinary recapture is "
                            "typically zero."
                        ),
                        "summary_text": "§1250 recaptures only excess depreciation over SL. Usually zero for post-1986 MACRS.",
                        "is_key_excerpt": True,
                        "topic_tags": ["1250", "recapture"],
                    },
                ],
            },
            {
                "source_code": "IRC_1_H_1_E",
                "source_type": "code_section",
                "source_rank": "controlling",
                "jurisdiction_code": "FED",
                "title": "IRC §1(h)(1)(E) — Unrecaptured Section 1250 Gain (25% Rate)",
                "citation": "26 U.S.C. §1(h)(1)(E)",
                "issuer": "Congress",
                "current_status": "active",
                "is_substantive_authority": True,
                "requires_human_review": True,
                "trust_score": 10.0,
                "topics": ["1250", "recapture", "capital_gains"],
                "excerpts": [
                    {
                        "excerpt_label": "Unrecaptured §1250 gain — 25% max rate",
                        "location_reference": "§1(h)(1)(E)",
                        "excerpt_text": (
                            "Unrecaptured section 1250 gain is the amount of long-term capital gain that "
                            "would be treated as ordinary income if section 1250(b)(1) included ALL depreciation. "
                            "This gain — attributable to depreciation on real property but not ordinary under "
                            "§1250 — is taxed at a maximum rate of 25%."
                        ),
                        "summary_text": "Gain attributable to depreciation on §1250 property, not ordinary under §1250, taxed at max 25%.",
                        "is_key_excerpt": True,
                        "topic_tags": ["1250", "capital_gains"],
                    },
                ],
            },
            # --- IRS Instructions (content fetched from irs.gov) ---
            {
                "source_code": "IRS_2025_4797_INSTR",
                "source_type": "official_instruction",
                "source_rank": "primary_official",
                "jurisdiction_code": "FED",
                "tax_year_start": 2025, "tax_year_end": 2025,
                "entity_type_code": "shared",
                "title": "Instructions for Form 4797 (2025) — Sales of Business Property",
                "citation": "Instructions for Form 4797 (2025)",
                "issuer": "IRS",
                "official_url": "https://www.irs.gov/instructions/i4797",
                "current_status": "active",
                "is_substantive_authority": True,
                "is_filing_authority": True,
                "requires_human_review": False,
                "trust_score": 9.5,
                "topics": ["4797", "1231", "1245", "1250", "dispositions", "recapture"],
                "excerpts": [
                    {
                        "excerpt_label": "General Instructions — What goes on 4797",
                        "location_reference": "General Instructions",
                        "excerpt_text": (
                            "Use Form 4797 to report: the sale or exchange of property used in your trade or "
                            "business; involuntary conversions from other than casualty or theft; disposition of "
                            "noncapital assets; the section 179 expense deduction recapture when business use drops "
                            "to 50% or less. Do NOT use Form 4797 for property held for personal use — use "
                            "Schedule D. Other forms that may be required instead of or in addition to 4797 include "
                            "Forms 4684, 6252, 8824, and 8949."
                        ),
                        "summary_text": "Form 4797 covers business property dispositions, not personal capital assets.",
                        "is_key_excerpt": True,
                        "topic_tags": ["4797", "dispositions"],
                    },
                    {
                        "excerpt_label": "Part I — Property held more than 1 year (§1231)",
                        "location_reference": "Part I Instructions",
                        "excerpt_text": (
                            "Report on Part I the sale or exchange of property held more than 1 year that is NOT "
                            "reported on Part III. This includes §1231 property where there is no depreciation "
                            "recapture, or the excess gain after recapture from Part III line 32. "
                            "The net gain or loss from Part I is combined: net gain is reported as long-term "
                            "capital gain on Schedule D (for individuals) or the appropriate schedule/line for "
                            "other entity types. Net loss is ordinary."
                        ),
                        "summary_text": "Part I = long-term §1231 property, after recapture handled in Part III. Net gain → LTCG, net loss → ordinary.",
                        "is_key_excerpt": True,
                        "topic_tags": ["4797", "1231"],
                    },
                    {
                        "excerpt_label": "Part II — Ordinary gains and losses",
                        "location_reference": "Part II Instructions",
                        "excerpt_text": (
                            "Report on Part II: property held 1 year or less; ordinary gain from Part III line 31 "
                            "(depreciation recapture); other ordinary gains and losses not required to be reported "
                            "elsewhere. The total from Part II is reported as ordinary income or loss on the "
                            "appropriate line of the entity's return (e.g., Form 1120-S page 1 line 4 for other "
                            "income/loss)."
                        ),
                        "summary_text": "Part II = short-term property + recapture from Part III. All ordinary.",
                        "is_key_excerpt": True,
                        "topic_tags": ["4797", "ordinary_income"],
                    },
                    {
                        "excerpt_label": "Part III — Gain from §1245, §1250, etc. disposition",
                        "location_reference": "Part III Instructions",
                        "excerpt_text": (
                            "Report on Part III each property with a gain where depreciation recapture may apply "
                            "under §§1245, 1250, 1252, 1254, or 1255. For §1245 property, the ordinary income "
                            "portion is the lesser of the gain or the total depreciation allowed or allowable. "
                            "For §1250 property, the ordinary income is the lesser of the gain or the additional "
                            "depreciation (excess over straight-line). The ordinary portion flows to Part II "
                            "line 13. Any excess gain over the recapture amount flows to Part I line 2."
                        ),
                        "summary_text": "Part III computes recapture: ordinary to Part II line 13, excess gain to Part I line 2.",
                        "is_key_excerpt": True,
                        "topic_tags": ["4797", "1245", "1250", "recapture"],
                    },
                    {
                        "excerpt_label": "Part IV — §179 and §280F recapture",
                        "location_reference": "Part IV Instructions",
                        "excerpt_text": (
                            "Part IV is used to figure the recapture amount when business use of §179 or listed "
                            "property (§280F) drops to 50% or less. The recapture is reported as other income on "
                            "the entity's return. This applies when property for which a §179 deduction was claimed "
                            "is no longer used predominantly (>50%) in a trade or business."
                        ),
                        "summary_text": "Part IV handles §179/§280F recapture when business use drops below 50%.",
                        "topic_tags": ["4797", "section_179_recapture"],
                    },
                ],
            },
            {
                "source_code": "IRS_PUB_544",
                "source_type": "official_publication",
                "source_rank": "primary_official",
                "jurisdiction_code": "FED",
                "tax_year_start": 2025, "tax_year_end": 2025,
                "title": "IRS Publication 544 — Sales and Other Dispositions of Assets",
                "citation": "Publication 544 (2025)",
                "issuer": "IRS",
                "official_url": "https://www.irs.gov/publications/p544",
                "current_status": "active",
                "is_substantive_authority": True,
                "requires_human_review": False,
                "trust_score": 9.0,
                "topics": ["dispositions", "1231", "1245", "1250", "capital_gains"],
                "excerpts": [
                    {
                        "excerpt_label": "Ordinary or Capital distinction",
                        "location_reference": "Chapter — Ordinary or Capital Gain and Loss",
                        "excerpt_text": (
                            "Whether gain or loss on disposition of business property is ordinary or capital "
                            "depends on the type of property and the holding period. Depreciable personal "
                            "property (§1245) recaptures all depreciation as ordinary. Depreciable real "
                            "property (§1250) recaptures only excess depreciation. The §1231 netting rule "
                            "then determines whether remaining gain is capital or ordinary. Noncapital assets "
                            "include property held mainly for sale to customers and accounts/notes receivable "
                            "from business operations."
                        ),
                        "summary_text": "Property type and holding period determine ordinary vs. capital treatment.",
                        "is_key_excerpt": True,
                        "topic_tags": ["dispositions", "1231", "1245", "1250"],
                    },
                    {
                        "excerpt_label": "Dispositions covered",
                        "location_reference": "Introduction",
                        "excerpt_text": (
                            "You dispose of property when any of the following occur: You sell property. You "
                            "exchange property for other property. Your property is condemned or disposed of "
                            "under threat of condemnation. Your property is repossessed. You abandon property. "
                            "You give property away."
                        ),
                        "summary_text": "Covers all disposition types: sale, exchange, condemnation, repossession, abandonment, gift.",
                        "is_key_excerpt": False,
                        "topic_tags": ["dispositions"],
                    },
                ],
            },
        ]

        created: dict[str, AuthoritySource] = {}
        for src_data in sources_data:
            excerpts_data = src_data.pop("excerpts", [])
            topic_codes = src_data.pop("topics", [])
            source, _ = AuthoritySource.objects.update_or_create(
                source_code=src_data["source_code"], defaults=src_data,
            )
            created[source.source_code] = source
            for exc in excerpts_data:
                AuthorityExcerpt.objects.update_or_create(
                    authority_source=source, excerpt_label=exc["excerpt_label"], defaults=exc,
                )
            for tc in topic_codes:
                topic = AuthorityTopic.objects.filter(topic_code=tc).first()
                if topic:
                    AuthoritySourceTopic.objects.get_or_create(authority_source=source, authority_topic=topic)
        self.stdout.write(f"Loaded {len(created)} authority sources.")
        return created

    def _load_form(self) -> TaxForm:
        form, created = TaxForm.objects.update_or_create(
            form_number="4797", jurisdiction="FED", tax_year=2025, version=1,
            defaults={
                "form_title": "Sales of Business Property",
                "entity_types": ["1120S", "1065", "1120", "1040"],
                "status": "draft",
                "notes": "First form loaded for validation. Some rules marked NEEDS REVIEW. IRC excerpts derived from IRS instructions/publications — Ken to verify statutory language.",
            },
        )
        self.stdout.write(f"{'Created' if created else 'Updated'} Form 4797 TY2025 v1.")
        return form

    def _load_facts(self, form: TaxForm):
        facts = [
            {"fact_key": "property_description", "label": "Description of Property", "data_type": "string", "required": True, "sort_order": 1},
            {"fact_key": "date_acquired", "label": "Date Acquired", "data_type": "date", "required": True, "sort_order": 2},
            {"fact_key": "date_sold", "label": "Date Sold or Disposed Of", "data_type": "date", "required": True, "sort_order": 3},
            {"fact_key": "sale_price", "label": "Gross Sales Price", "data_type": "decimal", "required": True, "validation_rule": "must be >= 0", "sort_order": 4},
            {"fact_key": "cost_or_basis", "label": "Cost or Other Basis Plus Improvements", "data_type": "decimal", "required": True, "sort_order": 5},
            {"fact_key": "depreciation_allowed", "label": "Depreciation Allowed or Allowable", "data_type": "decimal", "required": True, "validation_rule": "must be >= 0", "sort_order": 6},
            {"fact_key": "adjusted_basis", "label": "Adjusted Basis (cost minus depreciation)", "data_type": "decimal", "required": True, "sort_order": 7},
            {"fact_key": "property_type", "label": "Property Type for Recapture", "data_type": "choice", "required": True, "choices": ["1245", "1250", "1231", "other"], "sort_order": 8},
            {"fact_key": "holding_period_months", "label": "Holding Period (months)", "data_type": "integer", "required": True, "sort_order": 9},
            {"fact_key": "is_section_179_property", "label": "Section 179 Property?", "data_type": "boolean", "default_value": "false", "sort_order": 10},
            {"fact_key": "section_179_claimed", "label": "Section 179 Deduction Claimed", "data_type": "decimal", "default_value": "0", "sort_order": 11},
            {"fact_key": "depreciation_method", "label": "Depreciation Method", "data_type": "choice", "choices": ["MACRS_200DB", "MACRS_150DB", "SL", "other"], "sort_order": 12},
            {"fact_key": "entity_type", "label": "Entity Type", "data_type": "choice", "required": True, "choices": ["1120S", "1065", "1120", "1040"], "sort_order": 13},
            {"fact_key": "total_1231_gains", "label": "Total §1231 Gains", "data_type": "decimal", "sort_order": 20, "notes": "Aggregated across all properties"},
            {"fact_key": "total_1231_losses", "label": "Total §1231 Losses", "data_type": "decimal", "sort_order": 21},
            {"fact_key": "net_1231_gain_loss", "label": "Net §1231 Gain or Loss", "data_type": "decimal", "sort_order": 22},
            {"fact_key": "total_ordinary_gain_1245", "label": "Total §1245 Ordinary Income", "data_type": "decimal", "sort_order": 23},
            {"fact_key": "total_ordinary_gain_1250", "label": "Total §1250 Ordinary Income", "data_type": "decimal", "sort_order": 24},
            {"fact_key": "total_unrecaptured_1250", "label": "Total Unrecaptured §1250 Gain", "data_type": "decimal", "sort_order": 25},
        ]
        for f in facts:
            FormFact.objects.update_or_create(tax_form=form, fact_key=f["fact_key"], defaults={k: v for k, v in f.items() if k != "fact_key"})
        self.stdout.write(f"Loaded {len(facts)} facts.")

    def _load_rules(self, form: TaxForm) -> dict[str, FormRule]:
        rules_data = [
            {"rule_id": "R004", "title": "Calculate adjusted basis", "rule_type": "calculation", "formula": "cost_or_basis - depreciation_allowed", "inputs": ["cost_or_basis", "depreciation_allowed"], "outputs": ["adjusted_basis"], "precedence": 0, "sort_order": 0, "description": "Adjusted basis = original cost minus all depreciation allowed or allowable.", "notes": "Runs first (precedence 0) since other rules depend on adjusted_basis."},
            {"rule_id": "R001", "title": "Determine holding period classification", "rule_type": "classification", "formula": 'if holding_period_months > 12 then "long_term" else "short_term"', "inputs": ["holding_period_months"], "outputs": ["holding_period_class"], "precedence": 1, "sort_order": 1, "description": "Classify as long-term (>12 months) or short-term (<=12 months). Determines routing between Part I/III vs Part II."},
            {"rule_id": "R003", "title": "Calculate gain or loss", "rule_type": "calculation", "formula": "sale_price - adjusted_basis", "inputs": ["sale_price", "adjusted_basis"], "outputs": ["gain_or_loss"], "precedence": 2, "sort_order": 2, "description": "Basic gain/loss calculation: sale price minus adjusted basis."},
            {"rule_id": "R002", "title": "Route to correct Part", "rule_type": "routing", "formula": 'if holding_period_class == "short_term" then "Part II" else "Part I"', "inputs": ["holding_period_class", "property_type", "gain_or_loss"], "outputs": ["form_part_destination"], "precedence": 5, "sort_order": 3, "description": "Core routing: Short-term → Part II. Long-term with §1245/§1250 gain → Part III first (recapture), excess to Part I. Long-term gain without recapture → Part I. Long-term loss → Part I.", "notes": "NEEDS REVIEW — Simplified to long/short split. Full routing needs Part III → Part I overflow for recapture scenarios with gain on §1245/§1250 property."},
            {"rule_id": "R005", "title": "Section 1245 recapture — ordinary income", "rule_type": "calculation", "formula": "min(gain_or_loss, depreciation_allowed)", "conditions": {"when": 'property_type == "1245" and gain_or_loss > 0'}, "inputs": ["gain_or_loss", "depreciation_allowed", "property_type"], "outputs": ["ordinary_income_1245"], "precedence": 10, "sort_order": 5, "description": "For §1245 property, ALL gain up to total depreciation is recaptured as ordinary income. §1245 does not distinguish between straight-line and accelerated."},
            {"rule_id": "R006", "title": "Section 1245 excess gain → §1231", "rule_type": "calculation", "formula": "max(0, gain_or_loss - depreciation_allowed)", "conditions": {"when": 'property_type == "1245" and gain_or_loss > 0'}, "inputs": ["gain_or_loss", "depreciation_allowed", "property_type"], "outputs": ["section_1231_gain_excess"], "precedence": 11, "sort_order": 6, "description": "If gain exceeds total depreciation on §1245 property, the excess is §1231 gain flowing to Part I."},
            {"rule_id": "R007", "title": "Section 1250 recapture — ordinary income (additional depreciation)", "rule_type": "calculation", "formula": "0", "conditions": {"when": 'property_type == "1250" and gain_or_loss > 0'}, "inputs": ["gain_or_loss", "depreciation_allowed", "property_type"], "outputs": ["ordinary_income_1250"], "precedence": 10, "sort_order": 7, "description": "For §1250 property, only ADDITIONAL depreciation (excess over straight-line) is recaptured as ordinary. For post-1986 MACRS real property using SL, additional depreciation is zero.", "notes": "NEEDS REVIEW — Formula hardcoded to 0 because post-1986 MACRS real property uses SL. Pre-1987 or accelerated method property would need the actual additional depreciation calculation."},
            {"rule_id": "R008", "title": "Unrecaptured §1250 gain (25% rate bucket)", "rule_type": "calculation", "formula": "min(gain_or_loss, depreciation_allowed) - ordinary_income_1250", "conditions": {"when": 'property_type == "1250" and gain_or_loss > 0'}, "inputs": ["gain_or_loss", "depreciation_allowed", "ordinary_income_1250", "property_type"], "outputs": ["unrecaptured_1250_gain"], "precedence": 12, "sort_order": 8, "description": "Gain attributable to depreciation on §1250 property, NOT ordinary under §1250, taxed at max 25%. Equals min(gain, total_depreciation) minus §1250 ordinary recapture.", "notes": "NEEDS REVIEW — verify the split between unrecaptured §1250 and excess §1231 for complex scenarios."},
            {"rule_id": "R010", "title": "Net §1231 gain/loss netting", "rule_type": "calculation", "formula": "total_1231_gains - total_1231_losses", "conditions": {"when": "total_1231_gains >= 0"}, "inputs": ["total_1231_gains", "total_1231_losses"], "outputs": ["net_1231_gain_loss"], "precedence": 50, "sort_order": 10, "description": "All §1231 gains and losses are netted. Net gain → LTCG. Net loss → ordinary. Subject to 5-year lookback rule under §1231(c).", "notes": "Only runs when aggregation inputs are provided (not per-property)."},
        ]
        created: dict[str, FormRule] = {}
        for r in rules_data:
            rule, _ = FormRule.objects.update_or_create(tax_form=form, rule_id=r["rule_id"], defaults={k: v for k, v in r.items() if k != "rule_id"})
            created[r["rule_id"]] = rule
        self.stdout.write(f"Loaded {len(created)} rules.")
        return created

    def _link_authorities(self, rules: dict[str, FormRule], sources: dict[str, AuthoritySource]):
        links = [
            ("R001", "IRC_1231", "primary", "§1231 requires holding period >1 year for Part I treatment"),
            ("R001", "IRS_2025_4797_INSTR", "secondary", "General Instructions — routing between Parts"),
            ("R002", "IRS_2025_4797_INSTR", "primary", "General Instructions and Part I/II/III intros define routing"),
            ("R003", "IRS_2025_4797_INSTR", "primary", "Basic gain/loss per form instructions"),
            ("R004", "IRS_2025_4797_INSTR", "primary", "Adjusted basis definition — Part III line 24"),
            ("R005", "IRC_1245", "primary", "§1245(a)(1) — ordinary recapture of all depreciation"),
            ("R005", "IRS_2025_4797_INSTR", "secondary", "Part III instructions — §1245 recapture computation"),
            ("R006", "IRC_1231", "primary", "Excess gain over depreciation is §1231 gain"),
            ("R006", "IRS_2025_4797_INSTR", "secondary", "Part III line 32 → Part I flow"),
            ("R007", "IRC_1250", "primary", "§1250(a) — additional depreciation recapture"),
            ("R008", "IRC_1_H_1_E", "primary", "Defines unrecaptured §1250 gain at 25% max rate"),
            ("R008", "IRC_1250", "secondary", "§1250 provides the base recapture calculation"),
            ("R010", "IRC_1231", "primary", "§1231(a) netting rule — net gain is LTCG, net loss is ordinary"),
        ]
        count = 0
        for rule_id, source_code, level, note in links:
            rule = rules.get(rule_id)
            source = sources.get(source_code)
            if rule and source:
                RuleAuthorityLink.objects.get_or_create(form_rule=rule, authority_source=source, defaults={"support_level": level, "relevance_note": note})
                count += 1
        self.stdout.write(f"Created {count} rule-authority links.")

    def _load_lines(self, form: TaxForm):
        lines = [
            {"line_number": "2", "description": "Property held >1 year — description, dates, price, depreciation, cost, gain/loss", "line_type": "input", "notes": "Individual property entries (lines 2-6)", "sort_order": 10},
            {"line_number": "7", "description": "Combine amounts on lines 2 through 6 in column (g)", "line_type": "subtotal", "calculation": "Sum of lines 2-6 gain/loss", "source_rules": ["R003"], "sort_order": 17},
            {"line_number": "8", "description": "Net §1231 gain — if line 7 is more than zero", "line_type": "total", "source_rules": ["R010"], "destination_form": "Schedule D (1040) or Schedule K line 8a/9a (1120S/1065)", "sort_order": 18},
            {"line_number": "9", "description": "Net §1231 loss — if line 7 is zero or less", "line_type": "total", "source_rules": ["R010"], "destination_form": "Ordinary income line of entity return", "sort_order": 19},
            {"line_number": "10", "description": "Ordinary gains and losses — property held 1 year or less", "line_type": "input", "notes": "Short-term property entries", "sort_order": 20},
            {"line_number": "13", "description": "Gain from Form 4797, Part III, line 31", "line_type": "calculated", "calculation": "From Part III line 31", "source_rules": ["R005", "R007"], "sort_order": 23},
            {"line_number": "17", "description": "Combine lines 10 through 16", "line_type": "subtotal", "sort_order": 27},
            {"line_number": "18a", "description": "For all except individual returns, enter amount from line 17 on the return", "line_type": "total", "destination_form": "Form 1120-S page 1 line 4 (other income/loss)", "sort_order": 28},
            {"line_number": "19", "description": "Description of §1245, §1250, §1252, §1254, or §1255 property", "line_type": "input", "source_facts": ["property_description"], "sort_order": 30},
            {"line_number": "20", "description": "Date acquired (mm/dd/yyyy)", "line_type": "input", "source_facts": ["date_acquired"], "sort_order": 31},
            {"line_number": "21", "description": "Date sold (mm/dd/yyyy)", "line_type": "input", "source_facts": ["date_sold"], "sort_order": 32},
            {"line_number": "22", "description": "Cost or other basis, plus improvements and expense of sale", "line_type": "input", "source_facts": ["cost_or_basis"], "sort_order": 33},
            {"line_number": "23", "description": "Depreciation (or depletion) allowed or allowable", "line_type": "input", "source_facts": ["depreciation_allowed"], "sort_order": 34},
            {"line_number": "24", "description": "Adjusted basis. Subtract line 23 from line 22", "line_type": "calculated", "calculation": "Line 22 - Line 23", "source_rules": ["R004"], "source_facts": ["adjusted_basis"], "sort_order": 35},
            {"line_number": "25a", "description": "Applicable percentage for §1250 property", "line_type": "input", "notes": "100% for property held >1 year", "sort_order": 36},
            {"line_number": "25b", "description": "§1250 additional depreciation (line 25a × additional depreciation after 1975)", "line_type": "calculated", "source_rules": ["R007"], "sort_order": 37},
            {"line_number": "26", "description": "§1245 property — depreciation allowed or allowable from line 23", "line_type": "input", "source_facts": ["depreciation_allowed"], "notes": "For §1245, this is the full recapture amount", "sort_order": 38},
            {"line_number": "27", "description": "Enter the smaller of line 24g or 25b or 26 (recapture amount)", "line_type": "calculated", "calculation": "Recapture = min(gain, applicable recapture amount)", "source_rules": ["R005", "R007"], "sort_order": 39},
            {"line_number": "31", "description": "Add lines 27 through 30g — total ordinary gain from recapture", "line_type": "total", "source_rules": ["R005", "R007"], "destination_form": "Part II line 13", "sort_order": 43},
            {"line_number": "32", "description": "Subtract line 31 from line 24g — excess gain to Part I", "line_type": "calculated", "calculation": "Gain minus recapture → §1231 gain", "source_rules": ["R006"], "destination_form": "Part I line 2", "sort_order": 44},
            {"line_number": "33", "description": "§179 expense deduction or depreciation allowable in prior years", "line_type": "input", "source_facts": ["section_179_claimed"], "sort_order": 50},
            {"line_number": "35", "description": "Recapture amount (§179 and §280F)", "line_type": "calculated", "destination_form": "Other income line of entity return", "sort_order": 52, "notes": "NEEDS REVIEW — §179 recapture when business use drops below 50%"},
        ]
        for ln in lines:
            FormLine.objects.update_or_create(tax_form=form, line_number=ln["line_number"], defaults={k: v for k, v in ln.items() if k != "line_number"})
        self.stdout.write(f"Loaded {len(lines)} lines.")

    def _load_diagnostics(self, form: TaxForm):
        diagnostics = [
            {"diagnostic_id": "D001", "title": "Missing holding period", "severity": "error", "condition": "holding_period_months is null or 0", "message": "Holding period is required to determine correct Part routing."},
            {"diagnostic_id": "D002", "title": "Depreciation not entered for depreciable property", "severity": "warning", "condition": 'property_type in ["1245", "1250"] AND depreciation_allowed == 0', "message": "Depreciation is zero for depreciable property. Verify this is correct — if depreciation was allowed, it must be reported even if not claimed (depreciation 'allowable')."},
            {"diagnostic_id": "D003", "title": "Gain on §1245 property with no recapture", "severity": "warning", "condition": 'property_type == "1245" AND gain_or_loss > 0 AND depreciation_allowed == 0', "message": "Gain on §1245 property but no depreciation to recapture. Verify basis and depreciation."},
            {"diagnostic_id": "D004", "title": "Sale price is zero", "severity": "warning", "condition": "sale_price == 0", "message": "Sale price is zero. If this was a disposal (abandonment, casualty), verify the correct reporting method."},
            {"diagnostic_id": "D005", "title": "Long-term §1231 loss — check 5-year lookback", "severity": "info", "condition": 'holding_period_class == "long_term" AND gain_or_loss < 0', "message": "Net §1231 loss is ordinary. Note: if there were net §1231 gains in the prior 5 years treated as capital gains, the lookback rule under §1231(c) may require recharacterization."},
        ]
        for d in diagnostics:
            FormDiagnostic.objects.update_or_create(tax_form=form, diagnostic_id=d["diagnostic_id"], defaults={k: v for k, v in d.items() if k != "diagnostic_id"})
        self.stdout.write(f"Loaded {len(diagnostics)} diagnostics.")

    def _load_tests(self, form: TaxForm):
        tests = [
            {"scenario_name": "Basic §1245 gain — all recapture", "scenario_type": "normal", "inputs": {"sale_price": 50000, "cost_or_basis": 100000, "depreciation_allowed": 60000, "adjusted_basis": 40000, "property_type": "1245", "holding_period_months": 36}, "expected_outputs": {"gain_or_loss": 10000, "ordinary_income_1245": 10000, "section_1231_gain_excess": 0}, "notes": "Gain $10K < depreciation $60K → all $10K is ordinary under §1245.", "sort_order": 1},
            {"scenario_name": "§1245 gain exceeding depreciation — partial recapture + §1231", "scenario_type": "normal", "inputs": {"sale_price": 120000, "cost_or_basis": 100000, "depreciation_allowed": 30000, "adjusted_basis": 70000, "holding_period_months": 60, "property_type": "1245"}, "expected_outputs": {"gain_or_loss": 50000, "ordinary_income_1245": 30000, "section_1231_gain_excess": 20000}, "notes": "$50K gain, $30K recaptured as ordinary, $20K excess to Part I as §1231 gain.", "sort_order": 2},
            {"scenario_name": "§1231 loss — no recapture", "scenario_type": "normal", "inputs": {"sale_price": 30000, "cost_or_basis": 100000, "depreciation_allowed": 50000, "adjusted_basis": 50000, "holding_period_months": 48, "property_type": "1245"}, "expected_outputs": {"gain_or_loss": -20000}, "notes": "Loss = no recapture, goes to Part I as §1231 loss.", "sort_order": 3},
            {"scenario_name": "Short-term gain — all ordinary (Part II)", "scenario_type": "normal", "inputs": {"sale_price": 60000, "adjusted_basis": 40000, "holding_period_months": 6, "property_type": "1245", "cost_or_basis": 80000, "depreciation_allowed": 40000}, "expected_outputs": {"gain_or_loss": 20000, "holding_period_class": "short_term", "form_part_destination": "Part II"}, "notes": "Short-term bypasses §1231/recapture entirely.", "sort_order": 4},
            {"scenario_name": "§1250 property — unrecaptured gain (25% rate)", "scenario_type": "edge", "inputs": {"sale_price": 500000, "cost_or_basis": 400000, "depreciation_allowed": 100000, "adjusted_basis": 300000, "holding_period_months": 120, "property_type": "1250", "depreciation_method": "SL"}, "expected_outputs": {"gain_or_loss": 200000, "ordinary_income_1250": 0, "unrecaptured_1250_gain": 100000}, "notes": "NEEDS REVIEW — SL = no additional depreciation, so §1250 ordinary is 0. Unrecaptured = min(gain, depr) - 0 = $100K.", "sort_order": 5},
            {"scenario_name": "Zero gain — no reporting", "scenario_type": "edge", "inputs": {"sale_price": 40000, "adjusted_basis": 40000, "holding_period_months": 24, "property_type": "1245", "cost_or_basis": 60000, "depreciation_allowed": 20000}, "expected_outputs": {"gain_or_loss": 0}, "notes": "No gain or loss.", "sort_order": 6},
        ]
        for t in tests:
            TestScenario.objects.update_or_create(tax_form=form, scenario_name=t["scenario_name"], defaults={k: v for k, v in t.items() if k != "scenario_name"})
        self.stdout.write(f"Loaded {len(tests)} test scenarios.")

    def _load_form_links(self, sources: dict[str, AuthoritySource]):
        links = [("IRC_1231", "governs"), ("IRC_1245", "governs"), ("IRC_1250", "governs"), ("IRC_1_H_1_E", "governs"), ("IRS_2025_4797_INSTR", "governs"), ("IRS_PUB_544", "informs")]
        for source_code, link_type in links:
            source = sources.get(source_code)
            if source:
                AuthorityFormLink.objects.get_or_create(authority_source=source, form_code="4797", link_type=link_type, defaults={"note": f"{source_code} → Form 4797"})
        self.stdout.write(f"Created {len(links)} form links.")
