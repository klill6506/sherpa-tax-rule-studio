from django.contrib import admin

from .models import FlowAssertion, FormDiagnostic, FormFact, FormLine, FormRule, TaxForm, TestScenario


@admin.register(TaxForm)
class TaxFormAdmin(admin.ModelAdmin):
    list_display = ["form_number", "jurisdiction", "tax_year", "version", "status"]
    list_filter = ["jurisdiction", "status", "tax_year"]
    search_fields = ["form_number", "form_title"]


@admin.register(FormFact)
class FormFactAdmin(admin.ModelAdmin):
    list_display = ["fact_key", "label", "data_type", "required", "tax_form"]
    list_filter = ["data_type", "required"]


@admin.register(FormRule)
class FormRuleAdmin(admin.ModelAdmin):
    list_display = ["rule_id", "title", "rule_type", "precedence", "tax_form"]
    list_filter = ["rule_type"]


@admin.register(FormLine)
class FormLineAdmin(admin.ModelAdmin):
    list_display = ["line_number", "line_type", "tax_form"]
    list_filter = ["line_type"]


@admin.register(FormDiagnostic)
class FormDiagnosticAdmin(admin.ModelAdmin):
    list_display = ["diagnostic_id", "title", "severity", "tax_form"]
    list_filter = ["severity"]


@admin.register(TestScenario)
class TestScenarioAdmin(admin.ModelAdmin):
    list_display = ["scenario_name", "scenario_type", "tax_form"]
    list_filter = ["scenario_type"]


@admin.register(FlowAssertion)
class FlowAssertionAdmin(admin.ModelAdmin):
    list_display = ["assertion_id", "title", "assertion_type", "status", "entity_types"]
    list_filter = ["assertion_type", "status"]
    search_fields = ["assertion_id", "title", "description"]
    ordering = ["sort_order", "assertion_id"]
