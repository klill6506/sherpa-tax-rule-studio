import pytest

from specs.models import FlowAssertion


@pytest.mark.django_db
class TestFlowAssertionModel:
    def test_create_assertion(self):
        a = FlowAssertion.objects.create(
            assertion_id="TEST001",
            title="Test assertion",
            assertion_type="table_invariant",
            entity_types=["1120S"],
            definition={"table_name": "MACRS_200DB_HY", "check": "sum_equals_one"},
        )
        assert a.assertion_id == "TEST001"
        assert a.status == "active"

    def test_seed_creates_20_assertions(self):
        from django.core.management import call_command

        call_command("seed_flow_assertions")
        assert FlowAssertion.objects.count() == 20
        assert FlowAssertion.objects.filter(assertion_type="table_invariant").count() == 4
        assert FlowAssertion.objects.filter(assertion_type="flow_assertion").count() == 9
        assert FlowAssertion.objects.filter(assertion_type="reconciliation").count() == 7
