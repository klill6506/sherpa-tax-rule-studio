"""Tests for the form lookup-by-form-number API and import flexibility."""
import pytest
from django.test import Client

from specs.models import FlowAssertion, FormFact, FormLine, FormRule, TaxForm


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def form_8825_v1():
    return TaxForm.objects.create(
        jurisdiction="FED",
        form_number="8825",
        form_title="Rental Real Estate (old revision)",
        entity_types=["1120S", "1065"],
        tax_year=2025,
        version=1,
        status="draft",
    )


@pytest.fixture
def form_8825_v2(form_8825_v1):
    form = TaxForm.objects.create(
        jurisdiction="FED",
        form_number="8825",
        form_title="Rental Real Estate (Dec 2025 revision)",
        entity_types=["1120S", "1065"],
        tax_year=2025,
        version=2,
        status="draft",
    )
    FormFact.objects.create(
        tax_form=form, fact_key="gross_rents", label="Gross rents", data_type="decimal", sort_order=1,
    )
    FormRule.objects.create(
        tax_form=form, rule_id="R001", title="Total rental income per property",
        rule_type="calculation", formula="total_rental_income = gross_rents + other_rental_income",
        inputs=["gross_rents", "other_rental_income"], outputs=["total_rental_income"],
        sort_order=1,
    )
    FormLine.objects.create(
        tax_form=form, line_number="2c", description="Total rental income",
        line_type="calculated", source_rules=["R001"], sort_order=1,
    )
    return form


@pytest.mark.django_db
class TestFormLookup:
    def test_lookup_endpoint(self, client, form_8825_v2):
        resp = client.get("/api/forms/lookup/8825/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["form_number"] == "8825"
        assert data["version"] == 2

    def test_lookup_export(self, client, form_8825_v2):
        resp = client.get("/api/forms/lookup/8825/export/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["metadata"]["form_number"] == "8825"
        assert data["metadata"]["version"] == 2
        assert len(data["rules"]) >= 1
        assert len(data["line_map"]) >= 1

    def test_lookup_not_found(self, client):
        resp = client.get("/api/forms/lookup/FAKE_FORM/")
        assert resp.status_code == 404
        assert "No spec found" in resp.json()["error"]

    def test_lookup_latest_version(self, client, form_8825_v2):
        """With both v1 and v2, lookup returns v2."""
        resp = client.get("/api/forms/lookup/8825/")
        assert resp.status_code == 200
        assert resp.json()["version"] == 2

    def test_lookup_case_insensitive(self, client, form_8825_v2):
        resp = client.get("/api/forms/lookup/8825/")
        assert resp.status_code == 200

    def test_lookup_tax_year_filter(self, client, form_8825_v2):
        resp = client.get("/api/forms/lookup/8825/?tax_year=2025")
        assert resp.status_code == 200
        resp2 = client.get("/api/forms/lookup/8825/?tax_year=2020")
        assert resp2.status_code == 404


@pytest.mark.django_db
class TestImportFlexibleKeys:
    def test_import_with_form_lines_key(self, client):
        """Import endpoint accepts 'form_lines' as an alternative to 'line_map'."""
        spec = {
            "metadata": {
                "form_number": "TEST_FLEX",
                "form_title": "Test Flexible Import",
                "jurisdiction": "FED",
                "entity_types": ["1120S"],
                "tax_year": 2025,
                "version": 1,
            },
            "facts": [],
            "rules": [],
            "form_lines": [
                {"line_number": "1", "description": "Test line", "line_type": "input", "sort_order": 1},
                {"line_number": "2", "description": "Another line", "line_type": "input", "sort_order": 2},
            ],
            "diagnostics": [],
            "tests": [],
        }
        resp = client.post(
            "/api/forms/import_spec/",
            data=spec,
            content_type="application/json",
        )
        assert resp.status_code == 201
        form = TaxForm.objects.get(form_number="TEST_FLEX")
        assert form.lines.count() == 2


@pytest.mark.django_db
class TestFlowAssertionsCount:
    def test_seed_creates_20_assertions(self):
        from django.core.management import call_command

        call_command("seed_flow_assertions")
        assert FlowAssertion.objects.count() == 20
        assert FlowAssertion.objects.filter(assertion_type="table_invariant").count() == 4
        assert FlowAssertion.objects.filter(assertion_type="flow_assertion").count() == 9
        assert FlowAssertion.objects.filter(assertion_type="reconciliation").count() == 7
