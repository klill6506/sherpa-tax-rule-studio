"""DRF viewsets for authority source models."""
from django.db.models import Count, Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

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
from .serializers import (
    AuthorityExcerptSerializer,
    AuthorityFormLinkSerializer,
    AuthoritySourceDetailSerializer,
    AuthoritySourceListSerializer,
    AuthoritySourceTopicSerializer,
    AuthoritySourceWriteSerializer,
    AuthorityTopicSerializer,
    AuthorityVersionSerializer,
    ExcerptSearchSerializer,
    JurisdictionConformitySourceSerializer,
    RuleAuthorityLinkSerializer,
    SourceFeedDefinitionSerializer,
)


class AuthoritySourceViewSet(viewsets.ModelViewSet):
    queryset = AuthoritySource.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return AuthoritySourceListSerializer
        if self.action in ("create", "update", "partial_update"):
            return AuthoritySourceWriteSerializer
        return AuthoritySourceDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == "list":
            qs = qs.annotate(excerpt_count=Count("excerpts"))
            for param, field in [
                ("jurisdiction", "jurisdiction_code"),
                ("source_type", "source_type"),
                ("source_rank", "source_rank"),
                ("status", "current_status"),
            ]:
                val = self.request.query_params.get(param)
                if val:
                    qs = qs.filter(**{field: val})
            q = self.request.query_params.get("q")
            if q:
                qs = qs.filter(
                    Q(source_code__icontains=q) | Q(title__icontains=q) | Q(citation__icontains=q)
                )
        return qs


class SourceChildMixin:
    """Scopes queryset to parent AuthoritySource."""

    def get_queryset(self):
        source_pk = self.kwargs.get("source_pk")
        if source_pk:
            return super().get_queryset().filter(authority_source_id=source_pk)
        return super().get_queryset()

    def perform_create(self, serializer):
        source_pk = self.kwargs.get("source_pk")
        if source_pk:
            serializer.save(authority_source_id=source_pk)
        else:
            serializer.save()


class AuthorityExcerptViewSet(SourceChildMixin, viewsets.ModelViewSet):
    queryset = AuthorityExcerpt.objects.all()
    serializer_class = AuthorityExcerptSerializer


class AuthorityVersionViewSet(SourceChildMixin, viewsets.ModelViewSet):
    queryset = AuthorityVersion.objects.all()
    serializer_class = AuthorityVersionSerializer


class AuthorityTopicViewSet(viewsets.ModelViewSet):
    queryset = AuthorityTopic.objects.all()
    serializer_class = AuthorityTopicSerializer


class AuthoritySourceTopicViewSet(viewsets.ModelViewSet):
    queryset = AuthoritySourceTopic.objects.all()
    serializer_class = AuthoritySourceTopicSerializer


class AuthorityFormLinkViewSet(viewsets.ModelViewSet):
    queryset = AuthorityFormLink.objects.all()
    serializer_class = AuthorityFormLinkSerializer

    def get_queryset(self):
        qs = super().get_queryset().select_related("authority_source")
        form_code = self.request.query_params.get("form_code")
        if form_code:
            qs = qs.filter(form_code=form_code)
        source_id = self.request.query_params.get("source_id")
        if source_id:
            qs = qs.filter(authority_source_id=source_id)
        return qs


class RuleAuthorityLinkViewSet(viewsets.ModelViewSet):
    queryset = RuleAuthorityLink.objects.all().select_related("authority_source", "authority_excerpt")
    serializer_class = RuleAuthorityLinkSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        rule_id = self.request.query_params.get("rule_id")
        if rule_id:
            qs = qs.filter(form_rule_id=rule_id)
        return qs


class JurisdictionConformitySourceViewSet(viewsets.ModelViewSet):
    queryset = JurisdictionConformitySource.objects.all()
    serializer_class = JurisdictionConformitySourceSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        jurisdiction = self.request.query_params.get("jurisdiction")
        if jurisdiction:
            qs = qs.filter(jurisdiction_code=jurisdiction)
        tax_year = self.request.query_params.get("tax_year")
        if tax_year:
            qs = qs.filter(tax_year=tax_year)
        return qs


class SourceFeedDefinitionViewSet(viewsets.ModelViewSet):
    queryset = SourceFeedDefinition.objects.all()
    serializer_class = SourceFeedDefinitionSerializer


class ExcerptSearchView(APIView):
    """Full-text search across AuthorityExcerpts."""

    def get(self, request):
        q = request.query_params.get("q", "").strip()
        if not q:
            return Response({"results": [], "count": 0})

        qs = AuthorityExcerpt.objects.select_related("authority_source").filter(
            Q(excerpt_text__icontains=q)
            | Q(summary_text__icontains=q)
            | Q(excerpt_label__icontains=q)
            | Q(topic_tags__contains=[q])
        )

        # Optional filters
        jurisdiction = request.query_params.get("jurisdiction")
        if jurisdiction:
            qs = qs.filter(authority_source__jurisdiction_code=jurisdiction)
        source_type = request.query_params.get("source_type")
        if source_type:
            qs = qs.filter(authority_source__source_type=source_type)

        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(qs, request)
        serializer = ExcerptSearchSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
