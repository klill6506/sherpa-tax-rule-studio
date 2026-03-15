"""DRF viewsets for form specification models."""
from django.db.models import Count
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import FormDiagnostic, FormFact, FormLine, FormRule, TaxForm, TestScenario
from .serializers import (
    FormDiagnosticSerializer,
    FormFactSerializer,
    FormLineSerializer,
    FormRuleSerializer,
    TaxFormDetailSerializer,
    TaxFormListSerializer,
    TaxFormWriteSerializer,
    TestScenarioSerializer,
)


class TaxFormViewSet(viewsets.ModelViewSet):
    queryset = TaxForm.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return TaxFormListSerializer
        if self.action in ("create", "update", "partial_update"):
            return TaxFormWriteSerializer
        return TaxFormDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == "list":
            qs = qs.annotate(fact_count=Count("facts"), rule_count=Count("rules"))
            for param, field in [("jurisdiction", "jurisdiction"), ("entity_type", "entity_types__contains"),
                                 ("tax_year", "tax_year"), ("status", "status")]:
                val = self.request.query_params.get(param)
                if val:
                    if param == "entity_type":
                        qs = qs.filter(**{field: [val]})
                    else:
                        qs = qs.filter(**{field: val})
        return qs

    @action(detail=True, methods=["get"])
    def export(self, request, pk=None):
        """Export full form spec as a JSON package."""
        form = self.get_object()
        detail = TaxFormDetailSerializer(form).data
        # Include authority links for each rule
        from sources.models import RuleAuthorityLink
        from sources.serializers import RuleAuthorityLinkSerializer
        rule_ids = [r["id"] for r in detail["rules"]]
        links = RuleAuthorityLink.objects.filter(form_rule_id__in=rule_ids).select_related(
            "authority_source", "authority_excerpt"
        )
        return Response({
            "metadata": {
                "id": str(form.id),
                "jurisdiction": form.jurisdiction,
                "form_number": form.form_number,
                "form_title": form.form_title,
                "entity_types": form.entity_types,
                "tax_year": form.tax_year,
                "version": form.version,
                "status": form.status,
            },
            "facts": detail["facts"],
            "rules": detail["rules"],
            "line_map": detail["lines"],
            "diagnostics": detail["diagnostics"],
            "tests": detail["test_scenarios"],
            "rule_authority_links": RuleAuthorityLinkSerializer(links, many=True).data,
        })


class FormChildMixin:
    """Scopes queryset to the parent form and auto-sets tax_form on create."""

    def get_queryset(self):
        form_pk = self.kwargs.get("form_pk")
        if form_pk:
            return super().get_queryset().filter(tax_form_id=form_pk)
        return super().get_queryset()

    def perform_create(self, serializer):
        form_pk = self.kwargs.get("form_pk")
        if form_pk:
            serializer.save(tax_form_id=form_pk)
        else:
            serializer.save()


class FormFactViewSet(FormChildMixin, viewsets.ModelViewSet):
    queryset = FormFact.objects.all()
    serializer_class = FormFactSerializer


class FormRuleViewSet(FormChildMixin, viewsets.ModelViewSet):
    queryset = FormRule.objects.all()
    serializer_class = FormRuleSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == "list":
            qs = qs.annotate(authority_link_count=Count("authority_links"))
        return qs


class FormLineViewSet(FormChildMixin, viewsets.ModelViewSet):
    queryset = FormLine.objects.all()
    serializer_class = FormLineSerializer


class FormDiagnosticViewSet(FormChildMixin, viewsets.ModelViewSet):
    queryset = FormDiagnostic.objects.all()
    serializer_class = FormDiagnosticSerializer


class TestScenarioViewSet(FormChildMixin, viewsets.ModelViewSet):
    queryset = TestScenario.objects.all()
    serializer_class = TestScenarioSerializer
