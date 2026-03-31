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
    # --- 8825 + Schedule L Assertions (Session 13) ---
    {
        "assertion_id": "FA008",
        "title": "8825 Line 20a must equal sum of Line 2c across all properties",
        "description": "Line 20a is total GROSS rental income (sum of Line 2c), not net income, not positive-only nets. The December 2025 revision explicitly says 'Add total rental real estate income from line 2c.'",
        "assertion_type": "reconciliation",
        "entity_types": ["1120S", "1065"],
        "definition": {
            "check_type": "aggregation_equals",
            "assert_field": "8825_Line_20a",
            "expected_formula": "sum(RentalProperty.gross_rents + RentalProperty.other_rental_income for all properties)",
            "description": "Line 20a = sum of all Line 2c (gross income), not net",
        },
        "bug_reference": "Mar 30 2026 — CC implemented 20a as positive-only net splits instead of gross income total",
    },
    {
        "assertion_id": "FA009",
        "title": "8825 Line 20b must equal sum of Line 18 across all properties",
        "description": "Line 20b is total GROSS expenses (sum of Line 18), not net losses. Shown in parentheses.",
        "assertion_type": "reconciliation",
        "entity_types": ["1120S", "1065"],
        "definition": {
            "check_type": "aggregation_equals",
            "assert_field": "8825_Line_20b",
            "expected_formula": "sum(RentalProperty.total_expenses for all properties)",
            "description": "Line 20b = sum of all Line 18 (total expenses)",
        },
        "bug_reference": "Mar 30 2026 — CC implemented 20b as negative-only net splits instead of expense total",
    },
    {
        "assertion_id": "FA010",
        "title": "8825 Line 23 = 20a - 20b + 21 + 22a → K Line 2",
        "description": "The final net rental flows to Schedule K Line 2. Must include 4797 disposition gains (Line 21) and pass-through rental (Line 22a), not just property nets.",
        "assertion_type": "flow_assertion",
        "entity_types": ["1120S", "1065"],
        "definition": {
            "check_type": "formula_equals",
            "assert_field": "K2",
            "expected_formula": "8825_Line_20a - 8825_Line_20b + 8825_Line_21 + 8825_Line_22a",
            "description": "K2 = Line 23 = combined Lines 20a through 22a",
        },
        "bug_reference": "Mar 30 2026 — CC collapsed everything into Line 21 as 'total net', missing 4797 and pass-through lines",
    },
    {
        "assertion_id": "FA011",
        "title": "Schedule L Line 10b col (a) must contain accumulated depreciation, not net",
        "description": "The 'Less accumulated depreciation' row uses col (a) for BOY accum depr and col (c) for EOY accum depr. Columns (b) and (d) are the NET book values (gross minus accum).",
        "assertion_type": "reconciliation",
        "entity_types": ["1120S", "1065", "1120"],
        "definition": {
            "check_type": "rendering_column_check",
            "L10b_col_a": "l10b_accum_depr_boy",
            "L10b_col_b": "l10a_gross_boy - l10b_accum_depr_boy",
            "L10b_col_c": "l10b_accum_depr_eoy",
            "L10b_col_d": "l10a_gross_eoy - l10b_accum_depr_eoy",
            "description": "Accum depr in (a)/(c), NET in (b)/(d). Previous bug had accum depr in (b)/(d) and nothing in (a)/(c).",
        },
        "bug_reference": "Mar 30 2026 — CC 'verified correct' but translation map was actually wrong, putting accum depr in net columns",
    },
    {
        "assertion_id": "FA012",
        "title": "Total assets (L15) must use NET depreciable, not gross",
        "description": "Line 15 total assets includes L10 net book value (gross minus accum depr), NOT the gross cost alone. Using gross would overstate total assets.",
        "assertion_type": "flow_assertion",
        "entity_types": ["1120S", "1065", "1120"],
        "definition": {
            "check_type": "formula_component_check",
            "target_formula": "L15",
            "must_use": "l10b_net (gross - accum_depr)",
            "must_not_use": "l10a_gross alone",
            "description": "Total assets uses the NET of buildings/accum depr",
        },
        "bug_reference": "Preventive — if L10 columns are wrong, L15 could use wrong value",
    },
]


class Command(BaseCommand):
    help = "Seed flow assertions (15 original + 5 from Session 13)"

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
