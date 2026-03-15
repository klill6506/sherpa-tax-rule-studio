"""Load all federal authority sources — IRS form instructions and IRC sections.

Creates AuthoritySource, AuthorityExcerpt, AuthorityFormLink, and AuthoritySourceTopic
records for comprehensive federal tax law coverage. Idempotent — safe to re-run.

Content fetched from irs.gov instruction pages. IRC sections marked requires_human_review=True
as statutory text is paraphrased from official guidance.
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
from sources.federal_data.topics import TOPICS
from sources.federal_data.irc_sections import ALL_IRC_SECTIONS
from sources.federal_data.forms_1120s import SOURCES_1120S
from sources.federal_data.forms_1065 import SOURCES_1065
from sources.federal_data.forms_1120 import SOURCES_1120
from sources.federal_data.forms_1040 import SOURCES_1040
from sources.federal_data.forms_supporting import SOURCES_SUPPORTING


class Command(BaseCommand):
    help = "Load all federal authority sources (IRS instructions + IRC sections)"

    def handle(self, *_args, **_options):
        self.sources_loaded = 0
        self.excerpts_loaded = 0
        self.topics_loaded = 0
        self.form_links_loaded = 0
        self.review_count = 0
        self.failed = []

        with transaction.atomic():
            self._load_topics()
            self.stdout.write("")

            self.stdout.write(self.style.MIGRATE_HEADING("Loading 1120-S family sources..."))
            self._load_source_list(SOURCES_1120S)

            self.stdout.write(self.style.MIGRATE_HEADING("Loading 1065 family sources..."))
            self._load_source_list(SOURCES_1065)

            self.stdout.write(self.style.MIGRATE_HEADING("Loading 1120 family sources..."))
            self._load_source_list(SOURCES_1120)

            self.stdout.write(self.style.MIGRATE_HEADING("Loading 1040 schedules..."))
            self._load_source_list(SOURCES_1040)

            self.stdout.write(self.style.MIGRATE_HEADING("Loading supporting forms..."))
            self._load_source_list(SOURCES_SUPPORTING)

            self.stdout.write(self.style.MIGRATE_HEADING("Loading IRC sections..."))
            self._load_source_list(ALL_IRC_SECTIONS)

        self._report_totals()

    # ───────────── topics ─────────────

    def _load_topics(self):
        self.stdout.write(self.style.MIGRATE_HEADING("Loading topics..."))
        created_count = 0

        # First pass: create all topics
        for code, name, _ in TOPICS:
            _, created = AuthorityTopic.objects.get_or_create(
                topic_code=code, defaults={"topic_name": name},
            )
            if created:
                created_count += 1

        # Second pass: set parent relationships
        for code, _, parent_code in TOPICS:
            if parent_code:
                parent = AuthorityTopic.objects.filter(topic_code=parent_code).first()
                if parent:
                    AuthorityTopic.objects.filter(topic_code=code).update(parent_topic=parent)

        self.topics_loaded = created_count
        self.stdout.write(f"  Topics: {created_count} new (total: {AuthorityTopic.objects.count()})")

    # ───────────── source loading ─────────────

    def _load_source_list(self, sources_data):
        """Load a list of source dicts, each with excerpts/topics/form_links."""
        for data in sources_data:
            # Make a copy so we don't mutate the module-level data
            data = dict(data)
            try:
                self._upsert_source(data)
            except Exception as e:
                code = data.get("source_code", "UNKNOWN")
                self.failed.append(code)
                self.stderr.write(self.style.ERROR(f"  FAILED: {code} — {e}"))

    def _upsert_source(self, data):
        """Create or update a single source with its excerpts, topics, and form links."""
        excerpts = data.pop("excerpts", [])
        topic_codes = data.pop("topics", [])
        form_links = data.pop("form_links", [])

        source, created = AuthoritySource.objects.update_or_create(
            source_code=data["source_code"], defaults=data,
        )
        self.sources_loaded += 1
        if source.requires_human_review:
            self.review_count += 1

        exc_count = 0
        for exc in excerpts:
            AuthorityExcerpt.objects.update_or_create(
                authority_source=source,
                excerpt_label=exc["excerpt_label"],
                defaults=exc,
            )
            exc_count += 1
            self.excerpts_loaded += 1

        for tc in topic_codes:
            topic = AuthorityTopic.objects.filter(topic_code=tc).first()
            if topic:
                AuthoritySourceTopic.objects.get_or_create(
                    authority_source=source, authority_topic=topic,
                )

        for fl in form_links:
            AuthorityFormLink.objects.get_or_create(
                authority_source=source,
                form_code=fl["form_code"],
                link_type=fl["link_type"],
                defaults={
                    "note": fl.get("note", ""),
                    "form_part_code": fl.get("form_part_code", ""),
                    "line_code": fl.get("line_code", ""),
                },
            )
            self.form_links_loaded += 1

        verb = "Created" if created else "Updated"
        self.stdout.write(f"  {verb} {data['source_code']}: {exc_count} excerpts")

    # ───────────── report ─────────────

    def _report_totals(self):
        total_sources = AuthoritySource.objects.count()
        total_excerpts = AuthorityExcerpt.objects.count()
        total_topics = AuthorityTopic.objects.count()
        total_form_links = AuthorityFormLink.objects.count()
        review_sources = AuthoritySource.objects.filter(requires_human_review=True).count()

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("LOAD COMPLETE"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(f"  Sources loaded this run:   {self.sources_loaded}")
        self.stdout.write(f"  Excerpts loaded this run:  {self.excerpts_loaded}")
        self.stdout.write(f"  New topics created:        {self.topics_loaded}")
        self.stdout.write(f"  Form links loaded:         {self.form_links_loaded}")
        self.stdout.write("")
        self.stdout.write(f"  TOTAL AuthoritySources:    {total_sources}")
        self.stdout.write(f"  TOTAL AuthorityExcerpts:   {total_excerpts}")
        self.stdout.write(f"  TOTAL AuthorityTopics:     {total_topics}")
        self.stdout.write(f"  TOTAL AuthorityFormLinks:  {total_form_links}")
        self.stdout.write(f"  Needs human review:        {review_sources}")
        self.stdout.write("")
        if self.failed:
            self.stdout.write(self.style.ERROR(f"  FAILED sources ({len(self.failed)}):"))
            for code in self.failed:
                self.stdout.write(self.style.ERROR(f"    - {code}"))
        else:
            self.stdout.write(self.style.SUCCESS("  No failures."))
        self.stdout.write(self.style.SUCCESS("=" * 60))
