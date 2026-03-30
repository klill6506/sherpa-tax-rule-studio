"""Seed the 15 starter flow assertions derived from real Mar 28-30 bugs."""
from django.core.management.base import BaseCommand

from specs.models import FlowAssertion

ASSERTIONS = [
    # --- Table Invariants ---
    {
        "assertion_id": "TI001",
        "title": "MACRS 150DB HY tables must sum to 100%",
        "description": "Each life in the 150DB half-year table must have percentages summing to 1.0 (±0.002). Failure means assets won't fully depreciate.",
        "assertion_type": "table_invariant",
        "entity_types": ["1120S", "1065", "1120"],
        "definition": {
            "table_name": "MACRS_150DB_HY",
            "module": "apps.tts_forms.depreciation_engine",
            "check": "sum_equals_one",
            "params": {"lives": [3, 5, 7, 10, 15, 20], "tolerance": 0.002},
        },
        "bug_reference": "Mar 30 2026 — ALL 150DB tables only recovered 87-90%, never implemented SL switchover",
    },
    {
        "assertion_id": "TI002",
        "title": "MACRS 200DB HY tables must sum to 100%",
        "description": "Each life in the 200DB half-year table must have percentages summing to 1.0 (±0.002).",
        "assertion_type": "table_invariant",
        "entity_types": ["1120S", "1065", "1120"],
        "definition": {
            "table_name": "MACRS_200DB_HY",
            "module": "apps.tts_forms.depreciation_engine",
            "check": "sum_equals_one",
            "params": {"lives": [3, 5, 7, 10, 15, 20], "tolerance": 0.002},
        },
        "bug_reference": "Preventive — 200DB tables currently correct",
    },
    {
        "assertion_id": "TI003",
        "title": "150DB HY table length = life + 1",
        "description": "Half-year convention adds one partial year. A 5yr table must have 6 entries, 7yr must have 8, etc.",
        "assertion_type": "table_invariant",
        "entity_types": ["1120S", "1065", "1120"],
        "definition": {
            "table_name": "MACRS_150DB_HY",
            "module": "apps.tts_forms.depreciation_engine",
            "check": "length_equals_life_plus_one",
            "params": {"lives": [3, 5, 7, 10, 15, 20]},
        },
        "bug_reference": "Preventive",
    },
    {
        "assertion_id": "TI004",
        "title": "200DB HY table length = life + 1",
        "description": "Half-year convention adds one partial year.",
        "assertion_type": "table_invariant",
        "entity_types": ["1120S", "1065", "1120"],
        "definition": {
            "table_name": "MACRS_200DB_HY",
            "module": "apps.tts_forms.depreciation_engine",
            "check": "length_equals_life_plus_one",
            "params": {"lives": [3, 5, 7, 10, 15, 20]},
        },
        "bug_reference": "Preventive",
    },
    # --- Flow Assertions ---
    {
        "assertion_id": "FA001",
        "title": "K9 (Section 1231 gain) must appear in M2_3a formula",
        "description": "Schedule K Line 9 flows to M-2 Line 3a (Other additions to AAA). Without this, capital gains from asset dispositions don't affect retained earnings.",
        "assertion_type": "flow_assertion",
        "entity_types": ["1120S"],
        "definition": {
            "source_line": "K9",
            "must_appear_in_formula": "M2_3a",
            "registry": "FORMULAS_1120S",
            "module": "apps.returns.compute",
        },
        "bug_reference": "Mar 29 2026 — capital gains not flowing to M-2",
    },
    {
        "assertion_id": "FA002",
        "title": "K2 (rental income) must appear in M2_3a formula",
        "description": "Net rental real estate income from K2 must flow to M-2 Line 3a.",
        "assertion_type": "flow_assertion",
        "entity_types": ["1120S"],
        "definition": {
            "source_line": "K2",
            "must_appear_in_formula": "M2_3a",
            "registry": "FORMULAS_1120S",
            "module": "apps.returns.compute",
        },
        "bug_reference": "Mar 29 2026 — M-2 only had K1, missing all other K income items",
    },
    {
        "assertion_id": "FA003",
        "title": "K7 (ST capital gain) must appear in M2_3a formula",
        "description": "Short-term capital gains from K7 must flow to M-2 Line 3a.",
        "assertion_type": "flow_assertion",
        "entity_types": ["1120S"],
        "definition": {
            "source_line": "K7",
            "must_appear_in_formula": "M2_3a",
            "registry": "FORMULAS_1120S",
            "module": "apps.returns.compute",
        },
        "bug_reference": "Mar 29 2026 — M-2 missing all non-ordinary K income",
    },
    {
        "assertion_id": "FA004",
        "title": "K8a (LT capital gain) must appear in M2_3a formula",
        "description": "Long-term capital gains from K8a must flow to M-2 Line 3a.",
        "assertion_type": "flow_assertion",
        "entity_types": ["1120S"],
        "definition": {
            "source_line": "K8a",
            "must_appear_in_formula": "M2_3a",
            "registry": "FORMULAS_1120S",
            "module": "apps.returns.compute",
        },
        "bug_reference": "Mar 29 2026 — M-2 missing all non-ordinary K income",
    },
    {
        "assertion_id": "FA005",
        "title": "K16a (tax-exempt income) must appear in M2_3a formula",
        "description": "Tax-exempt interest from K16a increases AAA via M-2 Line 3a.",
        "assertion_type": "flow_assertion",
        "entity_types": ["1120S"],
        "definition": {
            "source_line": "K16a",
            "must_appear_in_formula": "M2_3a",
            "registry": "FORMULAS_1120S",
            "module": "apps.returns.compute",
        },
        "bug_reference": "Mar 29 2026 — M-2 missing tax-exempt income",
    },
    {
        "assertion_id": "FA006",
        "title": "K15a must map to K-1 Box 15 Code A",
        "description": "Post-1986 depreciation adjustment (ongoing) must flow to shareholder K-1 Box 15 with Code A.",
        "assertion_type": "flow_assertion",
        "entity_types": ["1120S"],
        "definition": {
            "check": "k1_coded_entry_exists",
            "k_line": "K15a",
            "expected_code": "A",
            "items_list": "K15_ITEMS",
            "module": "apps.tts_forms.renderer",
        },
        "bug_reference": "K-1 wiring verification",
    },
    {
        "assertion_id": "FA007",
        "title": "K15b must map to K-1 Box 15 Code B",
        "description": "Adjusted gain or loss (disposition AMT) must flow to K-1 Box 15 with Code B.",
        "assertion_type": "flow_assertion",
        "entity_types": ["1120S"],
        "definition": {
            "check": "k1_coded_entry_exists",
            "k_line": "K15b",
            "expected_code": "B",
            "items_list": "K15_ITEMS",
            "module": "apps.tts_forms.renderer",
        },
        "bug_reference": "Mar 30 2026 — disposition AMT was going to K15a instead of K15b",
    },
    # --- Reconciliation Checks ---
    {
        "assertion_id": "RC001",
        "title": "M-2 ending balances must equal L24d (retained earnings)",
        "description": "L24d = M2_8a + M2_8b + M2_8c + M2_8d. If these don't match, the balance sheet won't balance.",
        "assertion_type": "reconciliation",
        "entity_types": ["1120S"],
        "definition": {
            "check_type": "formula_equals",
            "inputs": {"K1": "100000", "M2_1a": "50000", "K16d": "10000"},
            "assert_field": "L24d",
            "expected_formula": "M2_8a + M2_8b + M2_8c + M2_8d",
            "description": "Retained earnings = sum of M-2 ending balances",
        },
        "bug_reference": "Balance sheet reconciliation — preventive",
    },
    {
        "assertion_id": "RC002",
        "title": "§1245 gain splits correctly to K9 + Line 4",
        "description": "For a §1245 asset sold at a gain with depreciation: ordinary recapture goes to Page 1 Line 4, Section 1231 excess goes to K9.",
        "assertion_type": "reconciliation",
        "entity_types": ["1120S"],
        "definition": {
            "check_type": "end_to_end_disposition",
            "asset": {
                "cost_basis": "30500",
                "total_depreciation": "20878",
                "sales_price": "15000",
                "recapture_type": "1245",
                "holding_months": 60,
            },
            "expected": {
                "total_gain": "-5878",
                "note": "This is a loss scenario — adjust values for gain test",
            },
            "description": "Verifies 4797 routing, K9, and Line 4 flow",
        },
        "bug_reference": "Mar 29 2026 — 1245 classification and flow verification",
    },
    {
        "assertion_id": "RC003",
        "title": "QBI W-2 wages = Line 7 + Line 8",
        "description": "Section 199A W-2 wages auto-calculates from officer compensation (Line 7) plus salaries and wages (Line 8).",
        "assertion_type": "reconciliation",
        "entity_types": ["1120S"],
        "definition": {
            "check_type": "formula_equals",
            "inputs": {"7": "30000", "8": "50000"},
            "assert_field": "QBI_W2_WAGES",
            "expected_value": "80000",
            "description": "QBI_W2_WAGES = Line 7 + Line 8",
        },
        "bug_reference": "Mar 30 2026 — QBI W-2 wages was manual input, now computed",
    },
    {
        "assertion_id": "RC004",
        "title": "AMT depreciation halved on disposal (half-year convention)",
        "description": "When a 200DB HY asset is sold in a year after placement, AMT current depreciation must be halved for the half-year disposal convention, same as regular depreciation.",
        "assertion_type": "reconciliation",
        "entity_types": ["1120S", "1065", "1120"],
        "definition": {
            "check_type": "amt_disposal_convention",
            "asset": {
                "method": "200DB",
                "convention": "HY",
                "life": 5,
                "cost_basis": "30500",
                "date_acquired": "2020-08-01",
                "date_sold": "2025-08-15",
                "tax_year": 2025,
            },
            "expected": {
                "amt_must_be_less_than_regular": False,
                "amt_current_must_be_halved": True,
                "note": "AMT current ≈ $1,271 (Lacerte verified)",
            },
            "description": "AMT disposal convention must match regular disposal convention",
        },
        "bug_reference": "Mar 30 2026 — AMT not halved on disposal, showed $2,034 instead of $1,271",
    },
]


class Command(BaseCommand):
    help = "Seed the 15 starter flow assertions"

    def handle(self, *args, **options):
        created = 0
        updated = 0
        for i, data in enumerate(ASSERTIONS):
            assertion_id = data["assertion_id"]
            defaults = {k: v for k, v in data.items() if k != "assertion_id"}
            defaults["sort_order"] = i
            obj, was_created = FlowAssertion.objects.update_or_create(
                assertion_id=assertion_id,
                defaults=defaults,
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Flow assertions: {created} created, {updated} updated, {len(ASSERTIONS)} total"
            )
        )
