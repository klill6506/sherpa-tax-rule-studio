import pytest
from specs.models import FormFact, FormRule, TaxForm
from sources.models import AuthoritySource, AuthorityExcerpt, AuthorityTopic, RuleAuthorityLink


@pytest.mark.django_db
class TestTaxForm:
    def test_create_tax_form(self, sample_form_data):
        form = TaxForm.objects.create(**sample_form_data)
        assert form.pk is not None
        assert form.jurisdiction == "federal"
        assert form.form_number == "4797"
        assert form.status == "draft"
        assert form.entity_types == ["1120S", "1065", "1040"]

    def test_tax_form_str(self, sample_form_data):
        form = TaxForm.objects.create(**sample_form_data)
        assert str(form) == "federal 4797 (2025 v1)"

    def test_tax_form_unique_constraint(self, sample_form_data):
        TaxForm.objects.create(**sample_form_data)
        with pytest.raises(Exception):
            TaxForm.objects.create(**sample_form_data)


@pytest.mark.django_db
class TestFormFact:
    def test_create_fact(self, sample_form_data, sample_fact_data):
        form = TaxForm.objects.create(**sample_form_data)
        fact = FormFact.objects.create(tax_form=form, **sample_fact_data)
        assert fact.pk is not None
        assert fact.fact_key == "sale_price"
        assert fact.data_type == "decimal"

    def test_fact_unique_per_form(self, sample_form_data, sample_fact_data):
        form = TaxForm.objects.create(**sample_form_data)
        FormFact.objects.create(tax_form=form, **sample_fact_data)
        with pytest.raises(Exception):
            FormFact.objects.create(tax_form=form, **sample_fact_data)


@pytest.mark.django_db
class TestFormRule:
    def test_create_rule(self, sample_form_data):
        form = TaxForm.objects.create(**sample_form_data)
        rule = FormRule.objects.create(
            tax_form=form,
            rule_id="R001",
            title="Determine gain type",
            rule_type="classification",
            inputs=["sale_price", "adjusted_basis"],
            outputs=["gain_type"],
        )
        assert rule.pk is not None
        assert rule.rule_id == "R001"

    def test_rule_has_no_authority_text_field(self, sample_form_data):
        """Authority linkage is via RuleAuthorityLink, not a text field."""
        form = TaxForm.objects.create(**sample_form_data)
        rule = FormRule.objects.create(
            tax_form=form, rule_id="R002", title="Test", rule_type="calculation",
        )
        assert not hasattr(rule, "authority")


@pytest.mark.django_db
class TestAuthoritySource:
    def test_create_source(self):
        source = AuthoritySource.objects.create(
            source_code="IRC_1231",
            source_type="code_section",
            source_rank="controlling",
            jurisdiction_code="FED",
            title="IRC Section 1231 — Property Used in Trade or Business",
            issuer="IRS",
            is_substantive_authority=True,
        )
        assert source.pk is not None
        assert source.source_code == "IRC_1231"

    def test_create_excerpt(self):
        source = AuthoritySource.objects.create(
            source_code="IRS_2025_4797_INSTR",
            source_type="official_instruction",
            source_rank="primary_official",
            jurisdiction_code="FED",
            title="Instructions for Form 4797 (2025)",
            issuer="IRS",
        )
        excerpt = AuthorityExcerpt.objects.create(
            authority_source=source,
            excerpt_label="Part III overview",
            excerpt_text="Explains recapture treatment for depreciable property.",
            is_key_excerpt=True,
        )
        assert excerpt.pk is not None
        assert excerpt.authority_source == source


@pytest.mark.django_db
class TestRuleAuthorityLink:
    def test_link_rule_to_source(self, sample_form_data):
        form = TaxForm.objects.create(**sample_form_data)
        rule = FormRule.objects.create(
            tax_form=form, rule_id="R001", title="Gain classification", rule_type="classification",
        )
        source = AuthoritySource.objects.create(
            source_code="IRC_1231",
            source_type="code_section",
            source_rank="controlling",
            jurisdiction_code="FED",
            title="IRC §1231",
            issuer="IRS",
        )
        link = RuleAuthorityLink.objects.create(
            form_rule=rule,
            authority_source=source,
            support_level="primary",
        )
        assert link.pk is not None
        assert rule.authority_links.count() == 1


@pytest.mark.django_db
class TestAuthorityTopic:
    def test_create_topic_hierarchy(self):
        parent = AuthorityTopic.objects.create(topic_code="depreciation", topic_name="Depreciation")
        child = AuthorityTopic.objects.create(
            topic_code="macrs", topic_name="MACRS", parent_topic=parent,
        )
        assert child.parent_topic == parent
        assert parent.children.count() == 1
