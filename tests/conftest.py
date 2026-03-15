import pytest


@pytest.fixture
def sample_form_data():
    """Minimal valid data for creating a TaxForm."""
    return {
        "jurisdiction": "federal",
        "form_number": "4797",
        "form_title": "Sales of Business Property",
        "entity_types": ["1120S", "1065", "1040"],
        "tax_year": 2025,
        "version": 1,
        "status": "draft",
        "notes": "",
    }


@pytest.fixture
def sample_fact_data():
    """Minimal valid data for creating a FormFact."""
    return {
        "fact_key": "sale_price",
        "label": "Sale Price",
        "data_type": "decimal",
        "required": True,
        "sort_order": 1,
    }
