"""DRF serializers for form specification models."""
from rest_framework import serializers

from .models import FormDiagnostic, FormFact, FormLine, FormRule, TaxForm, TestScenario


class FormFactSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormFact
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class FormRuleSerializer(serializers.ModelSerializer):
    authority_link_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = FormRule
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class FormLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormLine
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class FormDiagnosticSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormDiagnostic
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class TestScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestScenario
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class TaxFormListSerializer(serializers.ModelSerializer):
    fact_count = serializers.IntegerField(read_only=True, default=0)
    rule_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = TaxForm
        fields = [
            "id", "jurisdiction", "form_number", "form_title",
            "entity_types", "tax_year", "version", "status",
            "notes", "created_at", "updated_at",
            "fact_count", "rule_count",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class TaxFormDetailSerializer(serializers.ModelSerializer):
    facts = FormFactSerializer(many=True, read_only=True)
    rules = FormRuleSerializer(many=True, read_only=True)
    lines = FormLineSerializer(many=True, read_only=True)
    diagnostics = FormDiagnosticSerializer(many=True, read_only=True)
    test_scenarios = TestScenarioSerializer(many=True, read_only=True)

    class Meta:
        model = TaxForm
        fields = [
            "id", "jurisdiction", "form_number", "form_title",
            "entity_types", "tax_year", "version", "status",
            "notes", "created_at", "updated_at",
            "facts", "rules", "lines", "diagnostics", "test_scenarios",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class TaxFormWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxForm
        fields = [
            "id", "jurisdiction", "form_number", "form_title",
            "entity_types", "tax_year", "version", "status",
            "notes", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
