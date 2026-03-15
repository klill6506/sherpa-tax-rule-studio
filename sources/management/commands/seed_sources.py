"""Seed initial SourceFeedDefinitions and AuthorityTopics."""
from django.core.management.base import BaseCommand

from sources.models import AuthorityTopic, SourceFeedDefinition


FEEDS = [
    {
        "feed_code": "IRS_FORMS_INSTRUCTIONS",
        "feed_name": "IRS Forms & Instructions",
        "jurisdiction_code": "FED",
        "source_family": "IRS_FORMS",
        "base_url": "https://www.irs.gov/forms-instructions",
        "feed_type": "html_index",
        "refresh_frequency": "seasonal",
        "parser_strategy": "html_scrape",
        "is_active": True,
    },
    {
        "feed_code": "IRS_MEF_GENERAL",
        "feed_name": "IRS MeF Schemas & Business Rules",
        "jurisdiction_code": "FED",
        "source_family": "IRS_MEF",
        "base_url": "https://www.irs.gov/e-file-providers/modernized-e-file-mef-schemas-and-business-rules",
        "feed_type": "html_index",
        "refresh_frequency": "seasonal",
        "parser_strategy": "zip_unpack",
        "is_active": True,
    },
    {
        "feed_code": "GA_DOR_FORMS",
        "feed_name": "Georgia DOR Forms",
        "jurisdiction_code": "GA",
        "source_family": "GA_FORMS",
        "base_url": "https://dor.georgia.gov/documents/forms",
        "feed_type": "html_index",
        "refresh_frequency": "seasonal",
        "parser_strategy": "html_scrape",
        "is_active": True,
    },
    {
        "feed_code": "FTA_STATE_EFILE_INDEX",
        "feed_name": "FTA State E-File Index",
        "jurisdiction_code": "FED",
        "source_family": "FTA",
        "base_url": "https://taxadmin.org/electronic-filing-information/",
        "feed_type": "html_index",
        "refresh_frequency": "weekly",
        "parser_strategy": "html_scrape",
        "is_active": True,
    },
    {
        "feed_code": "INTERNAL_RULE_MEMOS",
        "feed_name": "Internal Rule Memos & Interpretations",
        "jurisdiction_code": "FED",
        "source_family": "INTERNAL",
        "base_url": None,
        "feed_type": "manual_upload",
        "refresh_frequency": "manual",
        "parser_strategy": "manual_clip",
        "is_active": True,
    },
]

# Hierarchical topics: (code, name, parent_code)
TOPICS = [
    ("depreciation", "Depreciation", None),
    ("macrs", "MACRS", "depreciation"),
    ("bonus_depreciation", "Bonus Depreciation", "depreciation"),
    ("section_179", "Section 179", "depreciation"),
    ("section_197", "Section 197 Amortization", "depreciation"),
    ("basis", "Basis", None),
    ("adjusted_basis", "Adjusted Basis", "basis"),
    ("cost_basis", "Cost Basis", "basis"),
    ("dispositions", "Dispositions", None),
    ("1231", "Section 1231", "dispositions"),
    ("1245", "Section 1245 Recapture", "dispositions"),
    ("1250", "Section 1250 Recapture", "dispositions"),
    ("like_kind_exchange", "Like-Kind Exchange (1031)", "dispositions"),
    ("recapture", "Recapture", None),
    ("apportionment", "Apportionment", None),
    ("conformity", "State Conformity", None),
    ("ga_conformity", "Georgia Conformity", "conformity"),
    ("income", "Income", None),
    ("deductions", "Deductions", None),
    ("startup_costs", "Startup Costs (Section 195)", "deductions"),
    ("passthrough", "Passthrough Entities", None),
    ("k1", "Schedule K-1", "passthrough"),
    ("efile", "E-Filing", None),
    ("mef", "MeF", "efile"),
    ("state_efile", "State E-File", "efile"),
]


class Command(BaseCommand):
    help = "Seed initial SourceFeedDefinitions and AuthorityTopics"

    def handle(self, *_args, **_options):
        # Feeds
        created_feeds = 0
        for feed_data in FEEDS:
            _, created = SourceFeedDefinition.objects.get_or_create(
                feed_code=feed_data["feed_code"],
                defaults=feed_data,
            )
            if created:
                created_feeds += 1
        self.stdout.write(f"Feeds: {created_feeds} created, {len(FEEDS) - created_feeds} already existed")

        # Topics (two-pass: create all, then set parents)
        topic_map: dict[str, AuthorityTopic] = {}
        created_topics = 0
        for code, name, _ in TOPICS:
            obj, created = AuthorityTopic.objects.get_or_create(
                topic_code=code,
                defaults={"topic_name": name},
            )
            topic_map[code] = obj
            if created:
                created_topics += 1

        # Set parent relationships
        for code, _, parent_code in TOPICS:
            if parent_code and parent_code in topic_map:
                topic = topic_map[code]
                topic.parent_topic = topic_map[parent_code]
                topic.save(update_fields=["parent_topic"])

        self.stdout.write(f"Topics: {created_topics} created, {len(TOPICS) - created_topics} already existed")
        self.stdout.write(self.style.SUCCESS("Seed complete."))
