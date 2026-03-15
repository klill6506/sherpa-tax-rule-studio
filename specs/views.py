"""DRF viewsets for form specification models."""
import json
from datetime import datetime, timezone

from django.db import transaction
from django.db.models import Count
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser
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


def _build_export(form: TaxForm) -> dict:
    """Build the full self-contained export package for a form."""
    from sources.models import (
        AuthorityFormLink,
        AuthoritySource,
        JurisdictionConformitySource,
        RuleAuthorityLink,
    )

    # Facts
    facts = list(form.facts.order_by("sort_order").values(
        "fact_key", "label", "data_type", "required", "default_value",
        "validation_rule", "choices", "sort_order", "notes",
    ))

    # Rules with resolved authority chains
    rules_export = []
    for rule in form.rules.order_by("sort_order"):
        authorities = []
        for link in rule.authority_links.select_related("authority_source", "authority_excerpt"):
            src = link.authority_source
            auth_entry = {
                "source_code": src.source_code,
                "title": src.title,
                "citation": src.citation,
                "source_type": src.source_type,
                "source_rank": src.source_rank,
                "support_level": link.support_level,
                "relevance_note": link.relevance_note,
                "excerpt": None,
            }
            if link.authority_excerpt:
                auth_entry["excerpt"] = {
                    "label": link.authority_excerpt.excerpt_label,
                    "text": link.authority_excerpt.excerpt_text,
                    "summary": link.authority_excerpt.summary_text,
                }
            authorities.append(auth_entry)

        rules_export.append({
            "rule_id": rule.rule_id,
            "title": rule.title,
            "description": rule.description,
            "rule_type": rule.rule_type,
            "conditions": rule.conditions,
            "formula": rule.formula,
            "inputs": rule.inputs,
            "outputs": rule.outputs,
            "precedence": rule.precedence,
            "exceptions": rule.exceptions,
            "notes": rule.notes,
            "authorities": authorities,
        })

    # Lines
    lines = list(form.lines.order_by("sort_order").values(
        "line_number", "description", "line_type", "calculation",
        "source_facts", "source_rules", "destination_form", "notes",
    ))

    # Diagnostics
    diagnostics = list(form.diagnostics.order_by("diagnostic_id").values(
        "diagnostic_id", "title", "severity", "condition", "message",
    ))

    # Tests
    tests = list(form.test_scenarios.order_by("sort_order").values(
        "scenario_name", "scenario_type", "inputs", "expected_outputs",
    ))

    # Authority sources linked to this form via AuthorityFormLink
    form_links = AuthorityFormLink.objects.filter(
        form_code=form.form_number
    ).select_related("authority_source")
    source_ids = set(fl.authority_source_id for fl in form_links)
    # Also include sources linked via rules
    rule_link_source_ids = set(
        RuleAuthorityLink.objects.filter(form_rule__tax_form=form)
        .values_list("authority_source_id", flat=True)
    )
    source_ids |= rule_link_source_ids

    authority_sources_export = []
    for src in AuthoritySource.objects.filter(id__in=source_ids):
        topics = list(
            src.source_topics.values_list("authority_topic__topic_code", flat=True)
        )
        excerpts = list(src.excerpts.values(
            "excerpt_label", "excerpt_text", "summary_text", "is_key_excerpt",
        ))
        authority_sources_export.append({
            "source_code": src.source_code,
            "source_type": src.source_type,
            "source_rank": src.source_rank,
            "jurisdiction_code": src.jurisdiction_code,
            "title": src.title,
            "citation": src.citation,
            "issuer": src.issuer,
            "current_status": src.current_status,
            "is_substantive_authority": src.is_substantive_authority,
            "trust_score": float(src.trust_score) if src.trust_score else None,
            "topics": topics,
            "excerpts": excerpts,
        })

    # State conformity (only for non-federal forms)
    state_conformity = None
    if form.jurisdiction.lower() != "federal":
        try:
            conf = JurisdictionConformitySource.objects.get(
                jurisdiction_code=form.jurisdiction, tax_year=form.tax_year,
            )
            state_conformity = {
                "jurisdiction_code": conf.jurisdiction_code,
                "tax_year": conf.tax_year,
                "conformity_type": conf.conformity_type,
                "federal_reference_note": conf.federal_reference_note,
                "summary": conf.summary,
                "decoupled_items": conf.decoupled_items,
                "notes": conf.notes,
            }
        except JurisdictionConformitySource.DoesNotExist:
            pass

    return {
        "export_version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "metadata": {
            "form_number": form.form_number,
            "form_title": form.form_title,
            "jurisdiction": form.jurisdiction,
            "entity_types": form.entity_types,
            "tax_year": form.tax_year,
            "version": form.version,
            "status": form.status,
        },
        "facts": facts,
        "rules": rules_export,
        "line_map": lines,
        "diagnostics": diagnostics,
        "tests": tests,
        "authority_sources": authority_sources_export,
        "state_conformity": state_conformity,
    }


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
        """Export full form spec as a self-contained JSON package."""
        form = self.get_object()
        return Response(_build_export(form))

    @action(detail=False, methods=["post"], parser_classes=[JSONParser])
    def import_spec(self, request):
        """Import a JSON spec package, creating a TaxForm and all children."""
        data = request.data
        if not data or "metadata" not in data:
            return Response({"error": "Invalid spec file"}, status=status.HTTP_400_BAD_REQUEST)

        meta = data["metadata"]
        form_number = meta.get("form_number", "")
        jurisdiction = meta.get("jurisdiction", "")
        tax_year = meta.get("tax_year", 0)

        # Check for existing form
        existing = TaxForm.objects.filter(
            form_number=form_number, jurisdiction=jurisdiction, tax_year=tax_year,
        ).order_by("-version").first()

        version = (existing.version + 1) if existing else meta.get("version", 1)

        try:
            with transaction.atomic():
                form = TaxForm.objects.create(
                    jurisdiction=jurisdiction,
                    form_number=form_number,
                    form_title=meta.get("form_title", ""),
                    entity_types=meta.get("entity_types", []),
                    tax_year=tax_year,
                    version=version,
                    status="draft",
                    notes=meta.get("notes", ""),
                )

                # Facts
                for fact in data.get("facts", []):
                    FormFact.objects.create(
                        tax_form=form,
                        fact_key=fact["fact_key"],
                        label=fact.get("label", ""),
                        data_type=fact.get("data_type", "string"),
                        required=fact.get("required", False),
                        default_value=fact.get("default_value"),
                        validation_rule=fact.get("validation_rule"),
                        choices=fact.get("choices"),
                        sort_order=fact.get("sort_order", 0),
                        notes=fact.get("notes", ""),
                    )

                # Rules
                for rule in data.get("rules", []):
                    FormRule.objects.create(
                        tax_form=form,
                        rule_id=rule["rule_id"],
                        title=rule.get("title", ""),
                        description=rule.get("description", ""),
                        rule_type=rule.get("rule_type", "calculation"),
                        conditions=rule.get("conditions", {}),
                        formula=rule.get("formula", ""),
                        inputs=rule.get("inputs", []),
                        outputs=rule.get("outputs", []),
                        precedence=rule.get("precedence", 0),
                        exceptions=rule.get("exceptions", ""),
                        notes=rule.get("notes", ""),
                        sort_order=rule.get("sort_order", 0),
                    )

                # Lines
                for line in data.get("line_map", []):
                    FormLine.objects.create(
                        tax_form=form,
                        line_number=line["line_number"],
                        description=line.get("description", ""),
                        line_type=line.get("line_type", "input"),
                        calculation=line.get("calculation", ""),
                        source_facts=line.get("source_facts", []),
                        source_rules=line.get("source_rules", []),
                        destination_form=line.get("destination_form"),
                        notes=line.get("notes", ""),
                        sort_order=line.get("sort_order", 0),
                    )

                # Diagnostics
                for diag in data.get("diagnostics", []):
                    FormDiagnostic.objects.create(
                        tax_form=form,
                        diagnostic_id=diag["diagnostic_id"],
                        title=diag.get("title", ""),
                        severity=diag.get("severity", "warning"),
                        condition=diag.get("condition", ""),
                        message=diag.get("message", ""),
                        notes=diag.get("notes", ""),
                    )

                # Tests
                for test in data.get("tests", []):
                    TestScenario.objects.create(
                        tax_form=form,
                        scenario_name=test["scenario_name"],
                        scenario_type=test.get("scenario_type", "normal"),
                        inputs=test.get("inputs", {}),
                        expected_outputs=test.get("expected_outputs", {}),
                        notes=test.get("notes", ""),
                        sort_order=test.get("sort_order", 0),
                    )

            return Response({
                "id": str(form.id),
                "form_number": form.form_number,
                "jurisdiction": form.jurisdiction,
                "tax_year": form.tax_year,
                "version": form.version,
                "existing_version": existing.version if existing else None,
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


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
