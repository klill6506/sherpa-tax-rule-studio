"""Authority source models — the knowledge base that grounds every rule in cited law."""
import uuid

from django.db import models


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SourceType(models.TextChoices):
    CODE_SECTION = "code_section", "IRC Section"
    REGULATION = "regulation", "Treasury Regulation"
    OFFICIAL_FORM = "official_form", "Official Form"
    OFFICIAL_INSTRUCTION = "official_instruction", "Form Instructions"
    OFFICIAL_PUBLICATION = "official_publication", "IRS Publication"
    OFFICIAL_NOTICE = "official_notice", "IRS Notice"
    OFFICIAL_REVENUE_RULING = "official_revenue_ruling", "Revenue Ruling"
    OFFICIAL_REVENUE_PROCEDURE = "official_revenue_procedure", "Revenue Procedure"
    MEF_SCHEMA = "mef_schema", "MeF XML Schema"
    MEF_BUSINESS_RULE = "mef_business_rule", "MeF Business Rule"
    MEF_RELEASE_MEMO = "mef_release_memo", "MeF Release Memo"
    STATE_STATUTE = "state_statute", "State Statute"
    STATE_REGULATION = "state_regulation", "State Regulation"
    STATE_FORM = "state_form", "State Form"
    STATE_INSTRUCTION = "state_instruction", "State Instructions"
    STATE_EFILE_SPEC = "state_efile_spec", "State E-File Spec"
    STATE_VENDOR_GUIDE = "state_vendor_guide", "State Vendor Guide"
    STATE_CONFORMITY_NOTICE = "state_conformity_notice", "State Conformity Notice"
    INTERNAL_MEMO = "internal_memo", "Internal Memo"
    INTERNAL_EXAMPLE = "internal_example", "Worked Example"
    INTERNAL_TEST_CASE = "internal_test_case", "Internal Test Case"


class SourceRank(models.TextChoices):
    CONTROLLING = "controlling", "Controlling"
    PRIMARY_OFFICIAL = "primary_official", "Primary Official"
    IMPLEMENTATION_OFFICIAL = "implementation_official", "Implementation Official"
    INTERNAL_INTERPRETATION = "internal_interpretation", "Internal Interpretation"
    REFERENCE_ONLY = "reference_only", "Reference Only"


class SourceStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    SUPERSEDED = "superseded", "Superseded"
    DRAFT = "draft", "Draft"
    ARCHIVED = "archived", "Archived"


class LinkType(models.TextChoices):
    GOVERNS = "governs", "Governs"
    INFORMS = "informs", "Informs"
    VALIDATES = "validates", "Validates"
    MAPPING_ONLY = "mapping_only", "Mapping Only"
    OVERRIDES = "overrides", "Overrides"


class SupportLevel(models.TextChoices):
    PRIMARY = "primary", "Primary"
    SECONDARY = "secondary", "Secondary"
    INTERPRETIVE = "interpretive", "Interpretive"
    IMPLEMENTATION = "implementation", "Implementation"


class ConformityType(models.TextChoices):
    ROLLING = "rolling", "Rolling"
    STATIC = "static", "Static"
    PARTIAL = "partial", "Partial"
    DECOUPLED = "decoupled", "Decoupled"


class FeedType(models.TextChoices):
    HTML_INDEX = "html_index", "HTML Index"
    PDF_LIST = "pdf_list", "PDF List"
    XML_REPO = "xml_repo", "XML Repository"
    MANUAL_UPLOAD = "manual_upload", "Manual Upload"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class AuthoritySource(models.Model):
    """Central record for a tax law source document."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_code = models.CharField(max_length=100, unique=True, help_text="e.g. IRC_1231, IRS_2025_4797_INSTR")
    source_type = models.CharField(max_length=40, choices=SourceType.choices)
    source_rank = models.CharField(max_length=30, choices=SourceRank.choices)
    jurisdiction_code = models.CharField(max_length=10, help_text="FED, GA, CA, etc.")
    tax_year_start = models.IntegerField(blank=True, null=True)
    tax_year_end = models.IntegerField(blank=True, null=True)
    entity_type_code = models.CharField(max_length=20, blank=True, null=True, help_text="1040, 1120S, shared")
    title = models.TextField()
    citation = models.CharField(max_length=255, blank=True, null=True, help_text="e.g. IRC §1231(a)(1)")
    issuer = models.CharField(max_length=100, help_text="IRS, GA DOR, etc.")
    official_url = models.TextField(blank=True, null=True)
    publication_date = models.DateField(blank=True, null=True)
    effective_date_start = models.DateField(blank=True, null=True)
    effective_date_end = models.DateField(blank=True, null=True)
    superseded_by = models.ForeignKey("self", on_delete=models.SET_NULL, blank=True, null=True, related_name="supersedes")
    current_status = models.CharField(max_length=20, choices=SourceStatus.choices, default=SourceStatus.ACTIVE)
    checksum_sha256 = models.CharField(max_length=64, blank=True, null=True)
    is_substantive_authority = models.BooleanField(default=False)
    is_filing_authority = models.BooleanField(default=False)
    is_internal_only = models.BooleanField(default=False)
    requires_human_review = models.BooleanField(default=True)
    trust_score = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["source_code"]

    def __str__(self):
        return f"{self.source_code}: {self.title[:80]}"


class AuthorityExcerpt(models.Model):
    """Citation-ready chunk of a source — the table the rule builder searches most."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    authority_source = models.ForeignKey(AuthoritySource, on_delete=models.CASCADE, related_name="excerpts")
    excerpt_label = models.CharField(max_length=255, blank=True, null=True, help_text="e.g. 'Part III instructions'")
    location_reference = models.CharField(max_length=255, blank=True, null=True, help_text="Page/section/line/XML path")
    excerpt_text = models.TextField()
    summary_text = models.TextField(blank=True, null=True)
    topic_tags = models.JSONField(default=list, blank=True)
    line_or_page_start = models.CharField(max_length=50, blank=True, null=True)
    line_or_page_end = models.CharField(max_length=50, blank=True, null=True)
    effective_year_start = models.IntegerField(blank=True, null=True)
    effective_year_end = models.IntegerField(blank=True, null=True)
    is_key_excerpt = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["authority_source", "excerpt_label"]

    def __str__(self):
        label = self.excerpt_label or "Excerpt"
        return f"{self.authority_source.source_code} — {label}"


class AuthorityTopic(models.Model):
    """Hierarchical topic tag for organizing sources."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic_code = models.CharField(max_length=100, unique=True, help_text="e.g. 'depreciation', '1231'")
    topic_name = models.CharField(max_length=255)
    parent_topic = models.ForeignKey("self", on_delete=models.SET_NULL, blank=True, null=True, related_name="children")
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["topic_code"]

    def __str__(self):
        return self.topic_name


class AuthoritySourceTopic(models.Model):
    """Join table — sources ↔ topics."""

    authority_source = models.ForeignKey(AuthoritySource, on_delete=models.CASCADE, related_name="source_topics")
    authority_topic = models.ForeignKey(AuthorityTopic, on_delete=models.CASCADE, related_name="source_topics")

    class Meta:
        unique_together = [("authority_source", "authority_topic")]

    def __str__(self):
        return f"{self.authority_source.source_code} → {self.authority_topic.topic_code}"


class AuthorityFormLink(models.Model):
    """Connects sources to forms/lines."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    authority_source = models.ForeignKey(AuthoritySource, on_delete=models.CASCADE, related_name="form_links")
    form_code = models.CharField(max_length=50, help_text="e.g. '4797', 'SCH_D', 'GA_600'")
    form_part_code = models.CharField(max_length=50, blank=True, null=True)
    line_code = models.CharField(max_length=20, blank=True, null=True)
    link_type = models.CharField(max_length=20, choices=LinkType.choices)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["form_code", "line_code"]

    def __str__(self):
        return f"{self.authority_source.source_code} → {self.form_code} ({self.link_type})"


class RuleAuthorityLink(models.Model):
    """Connects rules to their supporting authority sources."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form_rule = models.ForeignKey("specs.FormRule", on_delete=models.CASCADE, related_name="authority_links")
    authority_source = models.ForeignKey(AuthoritySource, on_delete=models.CASCADE, related_name="rule_links")
    authority_excerpt = models.ForeignKey(
        AuthorityExcerpt, on_delete=models.SET_NULL, blank=True, null=True, related_name="rule_links",
    )
    support_level = models.CharField(max_length=20, choices=SupportLevel.choices)
    relevance_note = models.TextField(blank=True, null=True)
    sort_order = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.form_rule.rule_id} ← {self.authority_source.source_code} ({self.support_level})"


class AuthorityVersion(models.Model):
    """Tracks source versions over time — MeF materials can have multiple per filing season."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    authority_source = models.ForeignKey(AuthoritySource, on_delete=models.CASCADE, related_name="versions")
    version_label = models.CharField(max_length=100, help_text="e.g. 'TY2025 v3.0'")
    version_date = models.DateField(blank=True, null=True)
    retrieval_url = models.TextField(blank=True, null=True)
    retrieval_timestamp = models.DateTimeField(blank=True, null=True)
    file_type = models.CharField(max_length=20, help_text="pdf, html, xml, zip, json")
    file_path = models.TextField(blank=True, null=True)
    checksum_sha256 = models.CharField(max_length=64, blank=True, null=True)
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version_date", "-created_at"]

    def __str__(self):
        return f"{self.authority_source.source_code} — {self.version_label}"


class JurisdictionConformitySource(models.Model):
    """State conformity tracking with proper authority citations."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    jurisdiction_code = models.CharField(max_length=10, help_text="GA, CA, etc.")
    tax_year = models.IntegerField()
    federal_reference_note = models.TextField(blank=True, null=True)
    conformity_type = models.CharField(max_length=20, choices=ConformityType.choices)
    authority_source = models.ForeignKey(
        AuthoritySource, on_delete=models.SET_NULL, blank=True, null=True, related_name="conformity_records",
    )
    summary = models.TextField(blank=True, null=True)
    decoupled_items = models.JSONField(
        default=list, blank=True,
        help_text="Structured list of items where state diverges from federal. "
        "Each entry: {item, federal_treatment, state_treatment, authority_source_id, notes}",
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["jurisdiction_code", "tax_year"]
        verbose_name_plural = "jurisdiction conformity sources"

    def __str__(self):
        return f"{self.jurisdiction_code} TY{self.tax_year} ({self.conformity_type})"


class SourceFeedDefinition(models.Model):
    """Where to pull source updates from — for future automated ingestion."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    feed_code = models.CharField(max_length=100, unique=True)
    feed_name = models.CharField(max_length=255)
    jurisdiction_code = models.CharField(max_length=10)
    source_family = models.CharField(max_length=50, help_text="IRS_FORMS, IRS_MEF, GA_FORMS, etc.")
    base_url = models.TextField(blank=True, null=True)
    feed_type = models.CharField(max_length=20, choices=FeedType.choices)
    refresh_frequency = models.CharField(max_length=20, help_text="daily, weekly, manual, seasonal")
    parser_strategy = models.CharField(max_length=50, help_text="html_scrape, manual_clip, zip_unpack, pdf_register")
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["feed_code"]

    def __str__(self):
        return f"{self.feed_code}: {self.feed_name}"
