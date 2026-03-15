from django.contrib import admin

from .models import (
    AuthorityExcerpt,
    AuthorityFormLink,
    AuthoritySource,
    AuthoritySourceTopic,
    AuthorityTopic,
    AuthorityVersion,
    JurisdictionConformitySource,
    RuleAuthorityLink,
    SourceFeedDefinition,
)


@admin.register(AuthoritySource)
class AuthoritySourceAdmin(admin.ModelAdmin):
    list_display = ["source_code", "source_type", "source_rank", "jurisdiction_code", "current_status"]
    list_filter = ["source_type", "source_rank", "jurisdiction_code", "current_status"]
    search_fields = ["source_code", "title", "citation"]


@admin.register(AuthorityExcerpt)
class AuthorityExcerptAdmin(admin.ModelAdmin):
    list_display = ["excerpt_label", "authority_source", "is_key_excerpt"]
    list_filter = ["is_key_excerpt"]
    search_fields = ["excerpt_text", "summary_text", "excerpt_label"]


@admin.register(AuthorityTopic)
class AuthorityTopicAdmin(admin.ModelAdmin):
    list_display = ["topic_code", "topic_name", "parent_topic"]
    search_fields = ["topic_code", "topic_name"]


@admin.register(AuthoritySourceTopic)
class AuthoritySourceTopicAdmin(admin.ModelAdmin):
    list_display = ["authority_source", "authority_topic"]


@admin.register(AuthorityFormLink)
class AuthorityFormLinkAdmin(admin.ModelAdmin):
    list_display = ["authority_source", "form_code", "link_type"]
    list_filter = ["link_type"]


@admin.register(RuleAuthorityLink)
class RuleAuthorityLinkAdmin(admin.ModelAdmin):
    list_display = ["form_rule", "authority_source", "support_level"]
    list_filter = ["support_level"]


@admin.register(AuthorityVersion)
class AuthorityVersionAdmin(admin.ModelAdmin):
    list_display = ["authority_source", "version_label", "is_current"]
    list_filter = ["is_current"]


@admin.register(JurisdictionConformitySource)
class JurisdictionConformitySourceAdmin(admin.ModelAdmin):
    list_display = ["jurisdiction_code", "tax_year", "conformity_type"]
    list_filter = ["jurisdiction_code", "conformity_type"]


@admin.register(SourceFeedDefinition)
class SourceFeedDefinitionAdmin(admin.ModelAdmin):
    list_display = ["feed_code", "feed_name", "jurisdiction_code", "is_active"]
    list_filter = ["jurisdiction_code", "is_active", "feed_type"]
