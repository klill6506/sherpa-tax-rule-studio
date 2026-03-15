"""DRF serializers for authority source models."""
from rest_framework import serializers

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


class AuthorityExcerptSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthorityExcerpt
        fields = "__all__"
        read_only_fields = ["id", "created_at"]


class AuthorityVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthorityVersion
        fields = "__all__"
        read_only_fields = ["id", "created_at"]


class AuthoritySourceListSerializer(serializers.ModelSerializer):
    excerpt_count = serializers.IntegerField(read_only=True, default=0)
    topics = serializers.SerializerMethodField()

    class Meta:
        model = AuthoritySource
        fields = [
            "id", "source_code", "source_type", "source_rank",
            "jurisdiction_code", "tax_year_start", "tax_year_end",
            "entity_type_code", "title", "citation", "issuer",
            "current_status", "is_substantive_authority", "is_filing_authority",
            "trust_score", "excerpt_count", "topics",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_topics(self, obj: AuthoritySource) -> list[str]:
        return list(obj.source_topics.values_list("authority_topic__topic_code", flat=True))


class AuthoritySourceDetailSerializer(serializers.ModelSerializer):
    excerpts = AuthorityExcerptSerializer(many=True, read_only=True)
    versions = AuthorityVersionSerializer(many=True, read_only=True)
    topics = serializers.SerializerMethodField()

    class Meta:
        model = AuthoritySource
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_topics(self, obj: AuthoritySource) -> list[str]:
        return list(obj.source_topics.values_list("authority_topic__topic_code", flat=True))


class AuthoritySourceWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthoritySource
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class AuthorityTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthorityTopic
        fields = "__all__"
        read_only_fields = ["id"]


class AuthoritySourceTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthoritySourceTopic
        fields = "__all__"


class AuthorityFormLinkSerializer(serializers.ModelSerializer):
    source_code = serializers.CharField(source="authority_source.source_code", read_only=True)

    class Meta:
        model = AuthorityFormLink
        fields = "__all__"
        read_only_fields = ["id", "created_at"]


class RuleAuthorityLinkSerializer(serializers.ModelSerializer):
    source_code = serializers.CharField(source="authority_source.source_code", read_only=True)
    source_title = serializers.CharField(source="authority_source.title", read_only=True)
    excerpt_label = serializers.CharField(source="authority_excerpt.excerpt_label", read_only=True, allow_null=True)

    class Meta:
        model = RuleAuthorityLink
        fields = "__all__"
        read_only_fields = ["id", "created_at"]


class JurisdictionConformitySourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = JurisdictionConformitySource
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class SourceFeedDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceFeedDefinition
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class ExcerptSearchSerializer(serializers.ModelSerializer):
    """Serializer for excerpt search results with source context."""
    source_code = serializers.CharField(source="authority_source.source_code", read_only=True)
    source_title = serializers.CharField(source="authority_source.title", read_only=True)
    source_rank = serializers.CharField(source="authority_source.source_rank", read_only=True)

    class Meta:
        model = AuthorityExcerpt
        fields = [
            "id", "authority_source", "source_code", "source_title", "source_rank",
            "excerpt_label", "location_reference", "excerpt_text", "summary_text",
            "topic_tags", "is_key_excerpt", "created_at",
        ]
