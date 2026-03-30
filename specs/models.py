"""Form specification models — the structured decomposition of a tax form."""
import uuid

from django.db import models


class TaxForm(models.Model):
    """Top-level container for a tax form specification."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        REVIEW = "review", "Review"
        APPROVED = "approved", "Approved"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    jurisdiction = models.CharField(max_length=20, help_text="'federal' or state code like 'GA'")
    form_number = models.CharField(max_length=50, help_text="e.g. '4797', 'Schedule D'")
    form_title = models.CharField(max_length=255)
    entity_types = models.JSONField(default=list, help_text="e.g. ['1120S', '1065', '1040']")
    tax_year = models.IntegerField()
    version = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["jurisdiction", "form_number"]
        unique_together = [("jurisdiction", "form_number", "tax_year", "version")]

    def __str__(self):
        return f"{self.jurisdiction} {self.form_number} ({self.tax_year} v{self.version})"


class FormFact(models.Model):
    """An input the form needs — a named, typed data point."""

    class DataType(models.TextChoices):
        STRING = "string", "String"
        INTEGER = "integer", "Integer"
        DECIMAL = "decimal", "Decimal"
        BOOLEAN = "boolean", "Boolean"
        DATE = "date", "Date"
        CHOICE = "choice", "Choice"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tax_form = models.ForeignKey(TaxForm, on_delete=models.CASCADE, related_name="facts")
    fact_key = models.CharField(max_length=100, help_text="snake_case identifier")
    label = models.CharField(max_length=255)
    data_type = models.CharField(max_length=20, choices=DataType.choices)
    required = models.BooleanField(default=False)
    default_value = models.CharField(max_length=255, blank=True, null=True)
    validation_rule = models.TextField(blank=True, null=True, help_text="e.g. 'must be >= 0'")
    choices = models.JSONField(blank=True, null=True, help_text="For choice-type facts")
    sort_order = models.IntegerField(default=0)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "fact_key"]
        unique_together = [("tax_form", "fact_key")]

    def __str__(self):
        return f"{self.fact_key} ({self.data_type})"


class FormRule(models.Model):
    """A logic rule. Authority linkage is via RuleAuthorityLink, not a text field."""

    class RuleType(models.TextChoices):
        CALCULATION = "calculation", "Calculation"
        CLASSIFICATION = "classification", "Classification"
        ROUTING = "routing", "Routing"
        VALIDATION = "validation", "Validation"
        CONDITIONAL = "conditional", "Conditional"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tax_form = models.ForeignKey(TaxForm, on_delete=models.CASCADE, related_name="rules")
    rule_id = models.CharField(max_length=20, help_text="Human-readable code like R001")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    rule_type = models.CharField(max_length=20, choices=RuleType.choices)
    conditions = models.JSONField(default=dict, blank=True, help_text="When does this rule apply?")
    formula = models.TextField(blank=True, default="", help_text="Calculation or logic expression")
    inputs = models.JSONField(default=list, help_text="Array of fact_keys this rule reads")
    outputs = models.JSONField(default=list, help_text="Array of fact_keys/line_numbers this rule writes")
    precedence = models.IntegerField(default=0)
    exceptions = models.TextField(blank=True, default="")
    notes = models.TextField(blank=True, default="")
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "rule_id"]
        unique_together = [("tax_form", "rule_id")]

    def __str__(self):
        return f"{self.rule_id}: {self.title}"


class FormLine(models.Model):
    """Line-by-line map of the actual form."""

    class LineType(models.TextChoices):
        INPUT = "input", "Input"
        CALCULATED = "calculated", "Calculated"
        SUBTOTAL = "subtotal", "Subtotal"
        TOTAL = "total", "Total"
        INFORMATIONAL = "informational", "Informational"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tax_form = models.ForeignKey(TaxForm, on_delete=models.CASCADE, related_name="lines")
    line_number = models.CharField(max_length=20)
    description = models.TextField(blank=True, default="")
    calculation = models.TextField(blank=True, default="")
    source_facts = models.JSONField(default=list)
    source_rules = models.JSONField(default=list)
    destination_form = models.CharField(max_length=255, blank=True, null=True)
    line_type = models.CharField(max_length=20, choices=LineType.choices)
    notes = models.TextField(blank=True, default="")
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "line_number"]
        unique_together = [("tax_form", "line_number")]

    def __str__(self):
        return f"Line {self.line_number}"


class FormDiagnostic(models.Model):
    """A review trigger — something to flag for the preparer."""

    class Severity(models.TextChoices):
        ERROR = "error", "Error"
        WARNING = "warning", "Warning"
        INFO = "info", "Info"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tax_form = models.ForeignKey(TaxForm, on_delete=models.CASCADE, related_name="diagnostics")
    diagnostic_id = models.CharField(max_length=20)
    title = models.CharField(max_length=255)
    severity = models.CharField(max_length=20, choices=Severity.choices)
    condition = models.TextField(blank=True, default="")
    message = models.TextField(blank=True, default="")
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["diagnostic_id"]
        unique_together = [("tax_form", "diagnostic_id")]

    def __str__(self):
        return f"{self.diagnostic_id}: {self.title}"


class TestScenario(models.Model):
    """A verification case — known inputs and expected outputs."""

    class ScenarioType(models.TextChoices):
        NORMAL = "normal", "Normal"
        EDGE = "edge", "Edge Case"
        FAILURE = "failure", "Failure"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tax_form = models.ForeignKey(TaxForm, on_delete=models.CASCADE, related_name="test_scenarios")
    scenario_name = models.CharField(max_length=255)
    scenario_type = models.CharField(max_length=20, choices=ScenarioType.choices, default=ScenarioType.NORMAL)
    inputs = models.JSONField(default=dict)
    expected_outputs = models.JSONField(default=dict)
    notes = models.TextField(blank=True, default="")
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "scenario_name"]

    def __str__(self):
        return self.scenario_name


class FlowAssertion(models.Model):
    """Cross-form validation assertion — exported as JSON, tested in tts-tax-app."""

    class AssertionType(models.TextChoices):
        TABLE_INVARIANT = "table_invariant", "Table Invariant"
        FLOW_ASSERTION = "flow_assertion", "Flow Assertion"
        RECONCILIATION = "reconciliation", "Reconciliation Check"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        DISABLED = "disabled", "Disabled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assertion_id = models.CharField(max_length=20, unique=True,
        help_text="Human-readable code: TI001, FA001, RC001")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    assertion_type = models.CharField(max_length=20, choices=AssertionType.choices)
    entity_types = models.JSONField(default=list,
        help_text="e.g. ['1120S', '1065']. Empty = all entity types.")
    definition = models.JSONField(default=dict,
        help_text="Machine-readable assertion parameters (type-specific)")
    bug_reference = models.CharField(max_length=255, blank=True, default="",
        help_text="What bug this would have caught, e.g. 'Mar 30 — 150DB tables wrong'")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "assertion_id"]

    def __str__(self):
        return f"{self.assertion_id}: {self.title}"
