"""Load the FORM_5695 spec — Residential Energy Credits (§25D + §25C), minimal v1.

Phase 2, third common form. Ken: "do the very least we can do on 5695 for 2025"
(2026-06-15). Form 5695 carries two nonrefundable credits:
  Part I  — Residential Clean Energy Credit (§25D) → line 15 → Schedule 3 line 5a.
            30% of solar/wind/geothermal/battery + fuel cell (min(30%×cost,
            $1,000×kW)). Nonrefundable, carries forward (line 16).
  Part II — Energy Efficient Home Improvement Credit (§25C) → line 32 → Sch 3 5b.
            30% with annual caps; no carryforward (excess lost).

KEN'S 2 SCOPE DECISIONS (2026-06-15, AskUserQuestion):
  (1) Both parts, the caps modeled; the worksheet/edge detail deferred.
  (2) Model the tax-liability limit (Credit Limit Worksheet) + the §25D carryforward.

LAW VERIFIED 2026-06-15 (brief tts-tax-app server/specs/_5695_source_brief.md):
  - §25D: 30%, fuel cell capped $500 per ½ kW (= $1,000 × kW). Carries forward.
  - §25C: 30%; doors $250 each/$500 all, windows $600, each energy-property item
    $600, home energy audit $150, the Section A+B AGGREGATE $1,200; heat pumps /
    HP water heaters / biomass a SEPARATE $2,000. §25C annual max $3,200.
  - OBBBA TERMINATES BOTH after Dec 31, 2025 — TY2025 is the last year; a TY2026
    return fires a RED (D_5695_2026).

SAFETY GUARD: READY_TO_SEED stays False until Ken's review walk (the §25D/§25C
caps + the carryforward + the tax-liability limit + the OBBBA termination).
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from sources.models import (
    AuthorityExcerpt,
    AuthorityFormLink,
    AuthoritySource,
    AuthoritySourceTopic,
    AuthorityTopic,
    RuleAuthorityLink,
)
from specs.models import (
    FlowAssertion,
    FormDiagnostic,
    FormFact,
    FormLine,
    FormRule,
    TaxForm,
    TestScenario,
)


READY_TO_SEED = True  # FLIPPED 2026-06-15 — Ken approved the review walk ("Approved — seed it, include render").


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_ENTITY_TYPES = ["1040"]
FORM_STATUS = "draft"


# ═══════════════════════════════════════════════════════════════════════════
# THE MATH (the integrity gate re-types this independently; they share no math).
# ═══════════════════════════════════════════════════════════════════════════

RATE = 0.30
FUEL_CELL_PER_KW = 1000      # $500 per ½ kW
DOORS_CAP = 500
WINDOWS_CAP = 600
ITEM_CAP = 600               # each Section-B energy-property item
AUDIT_CAP = 150
AGG_25C = 1200               # the Section A+B aggregate
HEATPUMP_CAP = 2000          # heat pumps / HP water heaters / biomass (separate)


def _r0(x) -> int:
    return int(round(x))


def credit_25d(solar_elec, solar_water, small_wind, geothermal, battery,
               fuel_cell_cost, fuel_cell_kw, carryforward_prior, tax_limit) -> tuple[int, int]:
    """Part I (§25D). Returns (line15 credit → Sch 3 5a, line16 carryforward-out)."""
    l6b = RATE * (solar_elec + solar_water + small_wind + geothermal + battery)
    fuel = min(RATE * fuel_cell_cost, FUEL_CELL_PER_KW * fuel_cell_kw)
    l13 = _r0(l6b + fuel + carryforward_prior)
    l15 = min(l13, _r0(tax_limit))
    return (l15, l13 - l15)


def credit_25c(insulation, doors, windows, central_ac, water_heater, furnace,
               panelboard, audit, heat_pump_biomass, tax_limit) -> int:
    """Part II (§25C). Returns line32 credit → Sch 3 5b (no carryforward)."""
    envelope = (RATE * insulation
                + min(RATE * doors, DOORS_CAP)
                + min(RATE * windows, WINDOWS_CAP))
    prop = (min(RATE * central_ac, ITEM_CAP)
            + min(RATE * water_heater, ITEM_CAP)
            + min(RATE * furnace, ITEM_CAP)
            + min(RATE * panelboard, ITEM_CAP)
            + min(RATE * audit, AUDIT_CAP))
    group_1200 = min(envelope + prop, AGG_25C)
    group_2000 = min(RATE * heat_pump_biomass, HEATPUMP_CAP)
    l30 = _r0(group_1200 + group_2000)
    return min(l30, _r0(tax_limit))


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("residential_energy_credits", "Residential energy credits (§25D clean energy + §25C home improvement) — Form 5695 → Schedule 3 line 5a/5b; OBBBA terminates both after 2025"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_1040_FORM",
    "IRS_2025_1040_INSTR",
]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_F5695_INSTR",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Form 5695 — Residential Energy Credits",
        "citation": "Instructions for Form 5695 (2025), Parts I and II",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/instructions/i5695",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": "Part I §25D 30% + fuel-cell cap + carryforward; Part II §25C caps ($1,200 aggregate + $2,000 heat-pump group). REQUIRES HUMAN REVIEW: the precise Credit Limit Worksheet credit-ordering is simplified in v1; joint-occupancy + QM-PIN + CEE-tier qualification are preparer-asserted.",
        "topics": ["residential_energy_credits"],
        "excerpts": [
            {
                "excerpt_label": "Part I §25D — 30% + fuel cell + carryforward",
                "location_reference": "i5695 (2025), Part I, lines 1-16",
                "excerpt_text": (
                    "Enter 30% of the costs of qualified solar electric, solar water heating, small wind, "
                    "geothermal heat pump, and battery storage (at least 3 kilowatt hours) property. For fuel "
                    "cell property, the credit is limited to $500 for each one-half kilowatt of capacity. Add "
                    "any credit carryforward from 2024. The credit can't be more than your tax liability; carry "
                    "any unused credit forward to 2026."
                ),
                "summary_text": "§25D = 30% of clean-energy costs (fuel cell $500/½kW) + prior carryforward, limited to tax, excess carries forward.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part II §25C — the caps",
                "location_reference": "i5695 (2025), Part II, lines 17-32",
                "excerpt_text": (
                    "The energy efficient home improvement credit is 30% of the cost of qualified improvements, "
                    "limited to $1,200 per year in the aggregate, with sub-limits of $250 per exterior door "
                    "($500 total), $600 for exterior windows and skylights, and $600 for each item of qualified "
                    "energy property, and $150 for a home energy audit. A separate $2,000 limit applies to heat "
                    "pumps, heat pump water heaters, and biomass stoves and boilers. There is no carryforward."
                ),
                "summary_text": "§25C = 30% capped: $1,200 aggregate (doors $500/windows $600/item $600/audit $150) + a separate $2,000 heat-pump group; no carryforward.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "OBBBA termination after 2025",
                "location_reference": "i5695 (2025), What's New",
                "excerpt_text": (
                    "You can't claim residential clean energy credits for expenditures made after December 31, "
                    "2025. You can't claim energy efficient home improvement credits for expenditures or "
                    "property placed in service after December 31, 2025."
                ),
                "summary_text": "Both credits terminate after 12/31/2025 (OBBBA) — TY2025 is the last year.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_25D",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §25D — Residential Clean Energy Credit",
        "citation": "26 U.S.C. §25D (30% credit; §25D(c) carryforward; OBBBA termination after 2025)",
        "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:25D%20edition:prelim)",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "30% residential clean energy credit; carries forward to the succeeding year; terminated for property placed in service after 2025 (OBBBA §70506).",
        "topics": ["residential_energy_credits"],
        "excerpts": [
            {
                "excerpt_label": "§25D(a) the 30% credit",
                "location_reference": "26 U.S.C. §25D(a)",
                "excerpt_text": (
                    "There shall be allowed as a credit an amount equal to 30 percent of the qualified solar "
                    "electric, solar water heating, fuel cell, small wind energy, geothermal heat pump, and "
                    "battery storage property expenditures."
                ),
                "summary_text": "§25D = 30% of qualified residential clean-energy expenditures.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_25C",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §25C — Energy Efficient Home Improvement Credit",
        "citation": "26 U.S.C. §25C (30%; §25C(b) the $1,200/$2,000 limits; OBBBA termination after 2025)",
        "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:25C%20edition:prelim)",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "30% home-improvement credit; §25C(b) the $1,200 aggregate + $2,000 heat-pump limits; no carryforward; terminated for property placed in service after 2025 (OBBBA §70505).",
        "topics": ["residential_energy_credits"],
        "excerpts": [
            {
                "excerpt_label": "§25C(b) the annual limitation",
                "location_reference": "26 U.S.C. §25C(b)",
                "excerpt_text": (
                    "The credit allowed shall not exceed $1,200 (the aggregate per-taxpayer annual limit), with "
                    "$250 per exterior door and $500 for all doors, $600 for exterior windows and skylights, and "
                    "$600 per item of qualified energy property; a separate $2,000 limit applies to heat pumps, "
                    "heat pump water heaters, and biomass stoves and boilers."
                ),
                "summary_text": "§25C(b): $1,200 aggregate (with door/window/item sub-caps) + a separate $2,000 heat-pump group.",
                "is_key_excerpt": True,
            },
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_F5695_INSTR", "FORM_5695", "governs"),
    ("IRC_25D", "FORM_5695", "governs"),
    ("IRC_25C", "FORM_5695", "governs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM: FORM_5695
# ═══════════════════════════════════════════════════════════════════════════

E_IDENTITY = {
    "form_number": "FORM_5695",
    "form_title": "Form 5695 Residential Energy Credits (§25D + §25C) (TY2025)",
    "notes": (
        "Ken's 2 scope decisions 2026-06-15 ('the very least'). A return-level "
        "FormDefinition on the 1040 (one home; the Schedule-A / 8889 facts "
        "precedent). Part I §25D (30% clean energy + fuel-cell $500/½kW cap + "
        "carryforward) → line 15 → Schedule 3 line 5a. Part II §25C (30% with the "
        "$1,200 aggregate + the $250/$500 doors / $600 windows / $600-per-item / "
        "$150 audit sub-caps + a separate $2,000 heat-pump/biomass group; no "
        "carryforward) → line 32 → Schedule 3 line 5b. The Credit Limit Worksheet "
        "caps each at available tax. OBBBA TERMINATES both after 2025 — a TY2026 "
        "return fires D_5695_2026. Joint occupancy / QM-PIN / CEE-tier are "
        "preparer-asserted (deferred)."
    ),
}

E_FACTS: list[dict] = [
    # ── Part I §25D inputs ──
    {"fact_key": "e5695_solar_electric", "label": "Qualified solar electric property cost",
     "data_type": "decimal", "default_value": "0", "sort_order": 1, "notes": "Line 1 (30%)."},
    {"fact_key": "e5695_solar_water", "label": "Qualified solar water heating property cost",
     "data_type": "decimal", "default_value": "0", "sort_order": 2, "notes": "Line 2 (30%)."},
    {"fact_key": "e5695_small_wind", "label": "Qualified small wind energy property cost",
     "data_type": "decimal", "default_value": "0", "sort_order": 3, "notes": "Line 3 (30%)."},
    {"fact_key": "e5695_geothermal", "label": "Qualified geothermal heat pump property cost",
     "data_type": "decimal", "default_value": "0", "sort_order": 4, "notes": "Line 4 (30%)."},
    {"fact_key": "e5695_battery", "label": "Qualified battery storage (≥3 kWh) cost",
     "data_type": "decimal", "default_value": "0", "sort_order": 5, "notes": "Line 5b (30%)."},
    {"fact_key": "e5695_fuel_cell_cost", "label": "Qualified fuel cell property cost",
     "data_type": "decimal", "default_value": "0", "sort_order": 6, "notes": "Line 8; min(30%, $1,000×kW)."},
    {"fact_key": "e5695_fuel_cell_kw", "label": "Fuel cell capacity (kilowatts)",
     "data_type": "decimal", "default_value": "0", "sort_order": 7, "notes": "Line 10 cap = $1,000 × kW."},
    {"fact_key": "e5695_25d_carryforward", "label": "§25D credit carryforward from 2024",
     "data_type": "decimal", "default_value": "0", "sort_order": 8, "notes": "Line 12."},
    # ── Part II §25C inputs ──
    {"fact_key": "e5695_insulation", "label": "Insulation / air-sealing cost",
     "data_type": "decimal", "default_value": "0", "sort_order": 9, "notes": "Line 18 (30%, no item sub-cap)."},
    {"fact_key": "e5695_doors", "label": "Exterior doors cost",
     "data_type": "decimal", "default_value": "0", "sort_order": 10, "notes": "Line 19 (30%, $500 all doors)."},
    {"fact_key": "e5695_windows", "label": "Exterior windows / skylights cost",
     "data_type": "decimal", "default_value": "0", "sort_order": 11, "notes": "Line 20 (30%, $600)."},
    {"fact_key": "e5695_central_ac", "label": "Central air conditioner cost",
     "data_type": "decimal", "default_value": "0", "sort_order": 12, "notes": "Line 22 (30%, $600)."},
    {"fact_key": "e5695_water_heater", "label": "Gas/propane/oil water heater cost",
     "data_type": "decimal", "default_value": "0", "sort_order": 13, "notes": "Line 23 (30%, $600)."},
    {"fact_key": "e5695_furnace", "label": "Furnace / hot water boiler cost",
     "data_type": "decimal", "default_value": "0", "sort_order": 14, "notes": "Line 24 (30%, $600)."},
    {"fact_key": "e5695_panelboard", "label": "Electrical panelboard / circuit upgrade cost",
     "data_type": "decimal", "default_value": "0", "sort_order": 15, "notes": "Line 25 (30%, $600)."},
    {"fact_key": "e5695_home_audit", "label": "Home energy audit cost",
     "data_type": "decimal", "default_value": "0", "sort_order": 16, "notes": "Line 26 (30%, $150)."},
    {"fact_key": "e5695_heat_pump_biomass", "label": "Heat pump / HP water heater / biomass cost",
     "data_type": "decimal", "default_value": "0", "sort_order": 17, "notes": "Line 29 (30%, separate $2,000)."},
    # ── Edge flag ──
    {"fact_key": "e5695_joint_occupancy", "label": "Joint occupancy (allocation needed)?",
     "data_type": "boolean", "default_value": "false", "sort_order": 18, "notes": "D_5695_JOINT — not modeled."},
    # ── Outputs ──
    {"fact_key": "e5695_line15", "label": "§25D credit → Schedule 3 line 5a",
     "data_type": "decimal", "sort_order": 30, "notes": "OUTPUT. Part I credit."},
    {"fact_key": "e5695_line16", "label": "§25D carryforward to 2026",
     "data_type": "decimal", "sort_order": 31, "notes": "OUTPUT. Line 13 − line 15."},
    {"fact_key": "e5695_line32", "label": "§25C credit → Schedule 3 line 5b",
     "data_type": "decimal", "sort_order": 32, "notes": "OUTPUT. Part II credit (no carryforward)."},
]

E_RULES: list[dict] = [
    {"rule_id": "R-5695-25D", "title": "Part I §25D — 30% clean energy + fuel cell + carryforward", "rule_type": "calculation",
     "precedence": 1, "sort_order": 1,
     "formula": ("l6b = 30% × (solar_elec + solar_water + small_wind + geothermal + battery); fuel = "
                 "min(30%×fuel_cost, $1,000×kW); l13 = l6b + fuel + carryforward_2024; l15 = min(l13, "
                 "tax_limit) → Sch 3 line 5a; l16 = l13 − l15 (carryforward to 2026)."),
     "inputs": ["e5695_solar_electric", "e5695_solar_water", "e5695_small_wind", "e5695_geothermal",
                "e5695_battery", "e5695_fuel_cell_cost", "e5695_fuel_cell_kw", "e5695_25d_carryforward"],
     "outputs": ["e5695_line15", "e5695_line16"],
     "description": "§25D the residential clean energy credit, tax-limited, with carryforward."},
    {"rule_id": "R-5695-25C", "title": "Part II §25C — 30% with the $1,200 + $2,000 caps", "rule_type": "calculation",
     "precedence": 2, "sort_order": 2,
     "formula": ("envelope = 30%×insulation + min(30%×doors,500) + min(30%×windows,600); property = "
                 "Σ min(30%×item,600) [AC/WH/furnace/panel] + min(30%×audit,150); group_1200 = "
                 "min(envelope+property, 1200); group_2000 = min(30%×heat_pump_biomass, 2000); l32 = "
                 "min(group_1200 + group_2000, tax_limit) → Sch 3 line 5b. No carryforward."),
     "inputs": ["e5695_insulation", "e5695_doors", "e5695_windows", "e5695_central_ac",
                "e5695_water_heater", "e5695_furnace", "e5695_panelboard", "e5695_home_audit",
                "e5695_heat_pump_biomass"],
     "outputs": ["e5695_line32"],
     "description": "§25C the energy efficient home improvement credit, capped, no carryforward."},
    {"rule_id": "R-5695-LIMIT", "title": "Credit Limit Worksheet — tax-liability limit", "rule_type": "calculation",
     "precedence": 3, "sort_order": 3,
     "formula": ("Each credit is limited to the tax available after the credits that precede it (Form 5695 "
                 "lines 14 / 31). v1 supplies the available-tax limit from the 1040; §25D excess carries "
                 "forward, §25C excess is lost."),
     "inputs": [], "outputs": [],
     "description": "The nonrefundable tax-liability limit. v1 uses a simplified available-tax amount."},
    {"rule_id": "R-5695-TERM", "title": "OBBBA termination after 2025", "rule_type": "routing",
     "precedence": 4, "sort_order": 4,
     "formula": "If tax_year >= 2026 → both credits = 0 + D_5695_2026 (terminated; prepare manually).",
     "inputs": [], "outputs": [],
     "description": "OBBBA terminates §25D and §25C for expenditures/property after 12/31/2025."},
]

E_LINES: list[dict] = [
    {"line_number": "l1_5", "description": "Part I lines 1-5b: clean-energy costs (solar/wind/geo/battery)", "line_type": "input"},
    {"line_number": "l6b", "description": "Line 6b: 30% of the clean-energy costs", "line_type": "calculated"},
    {"line_number": "l11", "description": "Line 11: fuel cell credit = min(30%×cost, $1,000×kW)", "line_type": "calculated"},
    {"line_number": "l13", "description": "Line 13: 6b + fuel cell + 2024 carryforward", "line_type": "calculated"},
    {"line_number": "l14", "description": "Line 14: tax-liability limit (Credit Limit Worksheet)", "line_type": "input"},
    {"line_number": "l15", "description": "Line 15: §25D credit (smaller of 13 or 14) → Sch 3 5a", "line_type": "total"},
    {"line_number": "l16", "description": "Line 16: §25D carryforward to 2026 (13 − 15)", "line_type": "calculated"},
    {"line_number": "l18_26", "description": "Part II §25C costs (insulation/doors/windows/AC/WH/furnace/panel/audit)", "line_type": "input"},
    {"line_number": "l1200", "description": "§25C Section A+B credit capped at $1,200 aggregate", "line_type": "calculated"},
    {"line_number": "l29", "description": "Line 29: heat-pump/biomass credit = min(30%×cost, $2,000)", "line_type": "calculated"},
    {"line_number": "l30", "description": "Line 30: §25C total before the tax limit ($1,200 + $2,000 groups)", "line_type": "calculated"},
    {"line_number": "l31", "description": "Line 31: tax-liability limit (Credit Limit Worksheet)", "line_type": "input"},
    {"line_number": "l32", "description": "Line 32: §25C credit (smaller of 30 or 31) → Sch 3 5b", "line_type": "total"},
    {"line_number": "sch3_5a", "description": "§25D credit → Schedule 3 line 5a", "line_type": "total"},
    {"line_number": "sch3_5b", "description": "§25C credit → Schedule 3 line 5b", "line_type": "total"},
]

E_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_5695_2026", "title": "Residential energy credits terminated after 2025", "severity": "error",
     "condition": "tax_year >= 2026 AND any 5695 cost is present",
     "message": ("Not supported for 2026+: OBBBA terminated both the Residential Clean Energy Credit (§25D) "
                 "and the Energy Efficient Home Improvement Credit (§25C) for expenditures/property after "
                 "December 31, 2025. Only a §25D carryforward from 2025 may remain — prepare any 2026 "
                 "carryforward manually."),
     "notes": "OBBBA termination. RED for 2026+."},
    {"diagnostic_id": "D_5695_25C_CAP", "title": "§25C credit capped (the $1,200 / $2,000 limits)", "severity": "info",
     "condition": "the §25C 30% gross exceeds the $1,200 aggregate or the $2,000 heat-pump cap",
     "message": ("The energy efficient home improvement credit was capped: the building-envelope + energy-"
                 "property credits are limited to $1,200 in the aggregate, and heat pumps / heat pump water "
                 "heaters / biomass to a separate $2,000 (annual maximum $3,200)."),
     "notes": "§25C(b)."},
    {"diagnostic_id": "D_5695_25C_LOST", "title": "§25C credit reduced by tax — the excess is LOST", "severity": "warning",
     "condition": "the §25C credit (line 30) exceeds the tax-liability limit (line 31)",
     "message": ("The §25C home improvement credit was reduced by the tax-liability limit. Unlike the §25D "
                 "clean energy credit, §25C does NOT carry forward — the excess is permanently lost. Confirm "
                 "the limit before filing."),
     "notes": "§25C has no carryforward."},
    {"diagnostic_id": "D_5695_25D_CFWD", "title": "§25D clean energy credit carries forward to 2026", "severity": "info",
     "condition": "the §25D credit (line 13) exceeds the tax-liability limit (line 14)",
     "message": ("The §25D residential clean energy credit exceeded this year's tax; the unused amount "
                 "carries forward to 2026 (Form 5695 line 16). The carryforward survives even though the "
                 "credit itself is terminated for new 2026 expenditures."),
     "notes": "§25D(c) carryforward."},
    {"diagnostic_id": "D_5695_FUEL_CELL", "title": "Fuel cell credit capped at $500 per ½ kW", "severity": "info",
     "condition": "30% of the fuel cell cost exceeds $1,000 × the kilowatt capacity",
     "message": ("The fuel cell property credit was limited to $500 for each one-half kilowatt of capacity "
                 "($1,000 × kW), which is less than 30% of the cost."),
     "notes": "§25D fuel-cell cap."},
    {"diagnostic_id": "D_5695_JOINT", "title": "Joint occupancy — allocation not modeled", "severity": "warning",
     "condition": "e5695_joint_occupancy is True",
     "message": ("Joint occupancy is indicated. The per-occupant allocation of the residential energy credits "
                 "(Form 5695 lines 7c / 32a) is not modeled — verify each occupant's share manually."),
     "notes": "Deferred edge case."},
]

E_SCENARIOS: list[dict] = [
    {"scenario_name": "E-T1 — §25D solar 30%", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "kind": "25d", "solar_electric": 20000, "tax_limit": 100000},
     "expected_outputs": {"e5695_line15": 6000, "e5695_line16": 0},
     "notes": "30% × 20,000 = 6,000; ample tax → full credit, no carryforward."},
    {"scenario_name": "E-T2 — §25C windows capped $600", "scenario_type": "edge_case", "sort_order": 2,
     "inputs": {"tax_year": 2025, "kind": "25c", "windows": 3000, "tax_limit": 100000},
     "expected_outputs": {"e5695_line32": 600},
     "notes": "30% × 3,000 = 900, capped at $600 (windows)."},
    {"scenario_name": "E-T3 — §25C doors capped $500", "scenario_type": "edge_case", "sort_order": 3,
     "inputs": {"tax_year": 2025, "kind": "25c", "doors": 2000, "tax_limit": 100000},
     "expected_outputs": {"e5695_line32": 500},
     "notes": "30% × 2,000 = 600, capped at $500 (all doors)."},
    {"scenario_name": "E-T4 — §25C $1,200 aggregate cap", "scenario_type": "edge_case", "sort_order": 4,
     "inputs": {"tax_year": 2025, "kind": "25c", "insulation": 5000, "windows": 3000, "tax_limit": 100000},
     "expected_outputs": {"e5695_line32": 1200},
     "notes": "insulation 1,500 + windows min(900,600)=600 → 2,100, capped at $1,200."},
    {"scenario_name": "E-T5 — §25C heat pump separate $2,000", "scenario_type": "edge_case", "sort_order": 5,
     "inputs": {"tax_year": 2025, "kind": "25c", "heat_pump_biomass": 10000, "tax_limit": 100000},
     "expected_outputs": {"e5695_line32": 2000},
     "notes": "30% × 10,000 = 3,000, capped at the separate $2,000 group."},
    {"scenario_name": "E-T6 — §25C annual max $3,200", "scenario_type": "edge_case", "sort_order": 6,
     "inputs": {"tax_year": 2025, "kind": "25c", "insulation": 10000, "heat_pump_biomass": 10000, "tax_limit": 100000},
     "expected_outputs": {"e5695_line32": 3200},
     "notes": "min(3,000 insulation, 1,200) + min(3,000 heat-pump, 2,000) = 1,200 + 2,000 = 3,200."},
    {"scenario_name": "E-T7 — §25D fuel cell cap", "scenario_type": "edge_case", "sort_order": 7,
     "inputs": {"tax_year": 2025, "kind": "25d", "fuel_cell_cost": 10000, "fuel_cell_kw": 2.0, "tax_limit": 100000},
     "expected_outputs": {"e5695_line15": 2000, "e5695_line16": 0},
     "notes": "min(30%×10,000=3,000, $1,000×2kW=2,000) = 2,000."},
    {"scenario_name": "E-T8 — §25D tax-limited → carryforward", "scenario_type": "edge_case", "sort_order": 8,
     "inputs": {"tax_year": 2025, "kind": "25d", "solar_electric": 20000, "tax_limit": 4000},
     "expected_outputs": {"e5695_line15": 4000, "e5695_line16": 2000},
     "notes": "credit 6,000, tax limit 4,000 → line 15 = 4,000; line 16 carryforward = 2,000."},
    {"scenario_name": "E-G1 — TY2026 terminated → RED", "scenario_type": "diagnostic", "sort_order": 9,
     "inputs": {"tax_year": 2026, "kind": "25c", "windows": 3000},
     "expected_outputs": {"D_5695_2026": True},
     "notes": "OBBBA termination → D_5695_2026 (credit not computed for 2026)."},
]

E_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-5695-25D", "IRC_25D", "primary", "§25D 30% + carryforward"),
    ("R-5695-25D", "IRS_2025_F5695_INSTR", "secondary", "Part I lines 1-16"),
    ("R-5695-25C", "IRC_25C", "primary", "§25C(b) the caps"),
    ("R-5695-25C", "IRS_2025_F5695_INSTR", "secondary", "Part II lines 17-32"),
    ("R-5695-LIMIT", "IRS_2025_F5695_INSTR", "primary", "The Credit Limit Worksheet"),
    ("R-5695-TERM", "IRC_25D", "primary", "OBBBA §70506 termination"),
    ("R-5695-TERM", "IRC_25C", "secondary", "OBBBA §70505 termination"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-5695-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "§25D 30% + the fuel-cell $500/½kW cap",
     "description": "Validates R-5695-25D. Bug it catches: the wrong clean-energy rate, or the fuel-cell capacity cap not applied.",
     "definition": {"kind": "formula_check", "form": "FORM_5695",
                    "formula": "l6b = 0.30×Σcosts; fuel = min(0.30×cost, 1000×kW)"},
     "sort_order": 1},
    {"assertion_id": "FA-1040-5695-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "§25C sub-caps + the $1,200 aggregate + the $2,000 heat-pump group",
     "description": "Validates R-5695-25C. Bug it catches: a missing sub-cap (windows $600 / doors $500 / item $600 / audit $150), the $1,200 aggregate not applied, or the $2,000 group not separate.",
     "definition": {"kind": "formula_check", "form": "FORM_5695",
                    "formula": "min(envelope+property,1200) + min(0.30×heatpump,2000); item caps 600/500/600/150"},
     "sort_order": 2},
    {"assertion_id": "FA-1040-5695-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "§25D tax-liability limit + the carryforward to 2026",
     "description": "Validates R-5695-25D + R-5695-LIMIT. Bug it catches: the tax limit not applied, or line 16 carryforward ≠ line 13 − line 15.",
     "definition": {"kind": "formula_check", "form": "FORM_5695",
                    "formula": "l15 = min(l13, tax_limit); l16 = l13 − l15"},
     "sort_order": 3},
    {"assertion_id": "FA-1040-5695-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "§25D → Sch 3 line 5a; §25C → Sch 3 line 5b",
     "description": "Validates the flow targets. Bug it catches: a credit landing on the wrong Schedule 3 line (5a vs 5b swapped).",
     "definition": {"kind": "flow_assertion", "form": "FORM_5695",
                    "checks": [{"source_line": "l15", "must_write_to": ["SCH_3.5a"]},
                               {"source_line": "l32", "must_write_to": ["SCH_3.5b"]}]},
     "sort_order": 4},
    {"assertion_id": "FA-1040-5695-05", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "§25C total = the $1,200 group + the $2,000 group, tax-limited",
     "description": "Validates R-5695-25C. Bug it catches: the two groups not summed, or the $2,000 heat-pump credit folded into the $1,200 cap.",
     "definition": {"kind": "reconciliation", "form": "FORM_5695",
                    "formula": "l32 = min(min(envelope+property,1200) + min(0.30×heatpump,2000), tax_limit)"},
     "sort_order": 5},
    {"assertion_id": "FA-1040-5695-06", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Gates — OBBBA TY2026 termination RED; §25C no carryforward",
     "description": "Validates R-5695-TERM. Bug it catches: the credit computed for 2026, or §25C excess wrongly carried forward.",
     "definition": {"kind": "gating_check", "form": "FORM_5695", "expect": {"red_fires": True},
                    "blockers": ["obbba_terminated_2026"]},
     "sort_order": 6},
]


FORMS: list[dict] = [
    {"identity": E_IDENTITY, "facts": E_FACTS, "rules": E_RULES, "lines": E_LINES,
     "diagnostics": E_DIAGNOSTICS, "scenarios": E_SCENARIOS, "rule_links": E_RULE_LINKS},
]


class Command(BaseCommand):
    help = "Load the FORM_5695 spec (Residential Energy Credits). Refuses until READY_TO_SEED=True."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad FORM_5695 spec (Residential Energy Credits)\n"))
        self._load_topics()
        sources = self._load_sources()
        self._load_new_excerpts_on_existing(sources)
        for spec in FORMS:
            form = self._upsert_form(spec["identity"])
            self._upsert_facts(form, spec["facts"])
            rules = self._upsert_rules(form, spec["rules"])
            self._upsert_authority_links(rules, sources, spec["rule_links"])
            self._upsert_lines(form, spec["lines"])
            self._upsert_diagnostics(form, spec["diagnostics"])
            self._upsert_tests(form, spec["scenarios"])
        self._upsert_form_links(sources)
        self._load_flow_assertions()
        self._report_totals()

    def _guard_against_hollow_seed(self):
        empty = []
        for spec in FORMS:
            fn = spec["identity"]["form_number"]
            for key in ("facts", "rules", "lines", "diagnostics", "scenarios", "rule_links"):
                if not spec[key]:
                    empty.append(f"{fn}.{key}")
        if not FLOW_ASSERTIONS:
            empty.append("FLOW_ASSERTIONS")
        if not READY_TO_SEED or empty:
            still_empty = "\n  ".join(f"- {n}" for n in empty) or "(all populated)"
            raise CommandError(
                "\nREFUSING TO SEED FORM_5695: not cleared to seed.\n\n"
                "Gated until Ken's review walk (the §25D/§25C caps + the carryforward\n"
                "+ the tax-liability limit + the OBBBA termination).\n\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True)\n\n"
                f"Currently empty / placeholder:\n  {still_empty}\n"
            )

    def _load_topics(self):
        ct = 0
        for code, name in AUTHORITY_TOPICS:
            _, created = AuthorityTopic.objects.update_or_create(topic_code=code, defaults={"topic_name": name})
            ct += 1 if created else 0
        self.stdout.write(f"Topics: {ct} new ({len(AUTHORITY_TOPICS)} in batch)")

    def _load_sources(self) -> dict:
        sources: dict = {}
        for src_data in AUTHORITY_SOURCES:
            src_data = dict(src_data)
            excerpts_data = src_data.pop("excerpts", [])
            topic_codes = src_data.pop("topics", [])
            source, _ = AuthoritySource.objects.update_or_create(
                source_code=src_data["source_code"], defaults=src_data)
            sources[source.source_code] = source
            for exc in excerpts_data:
                exc = dict(exc)
                AuthorityExcerpt.objects.update_or_create(
                    authority_source=source, excerpt_label=exc["excerpt_label"], defaults=exc)
            for tc in topic_codes:
                topic = AuthorityTopic.objects.filter(topic_code=tc).first()
                if topic:
                    AuthoritySourceTopic.objects.get_or_create(authority_source=source, authority_topic=topic)
        for code in EXISTING_SOURCES_TO_REFERENCE:
            src = AuthoritySource.objects.filter(source_code=code).first()
            if src:
                sources[code] = src
        self.stdout.write(f"Sources ready: {len(sources)}")
        return sources

    def _load_new_excerpts_on_existing(self, sources):
        for code, exc in NEW_EXCERPTS_ON_EXISTING:
            src = sources.get(code) or AuthoritySource.objects.filter(source_code=code).first()
            if src:
                exc = dict(exc)
                AuthorityExcerpt.objects.update_or_create(
                    authority_source=src, excerpt_label=exc["excerpt_label"], defaults=exc)

    def _upsert_form(self, identity: dict) -> TaxForm:
        form, created = TaxForm.objects.update_or_create(
            form_number=identity["form_number"], jurisdiction=FORM_JURISDICTION,
            tax_year=FORM_TAX_YEAR, version=FORM_VERSION,
            defaults={"form_title": identity["form_title"], "entity_types": FORM_ENTITY_TYPES,
                      "status": FORM_STATUS, "notes": identity["notes"]})
        self.stdout.write(f"{'Created' if created else 'Updated'} {identity['form_number']}")
        return form

    def _upsert_facts(self, form, facts):
        for f in facts:
            f = dict(f)
            FormFact.objects.update_or_create(tax_form=form, fact_key=f.pop("fact_key"), defaults=f)
        self.stdout.write(f"  {len(facts)} facts")

    def _upsert_rules(self, form, rules_data) -> dict:
        created = {}
        for r in rules_data:
            r = dict(r)
            rule, _ = FormRule.objects.update_or_create(tax_form=form, rule_id=r.pop("rule_id"), defaults=r)
            created[rule.rule_id] = rule
        self.stdout.write(f"  {len(created)} rules")
        return created

    def _upsert_authority_links(self, rules, sources, rule_links):
        ct = 0
        for rule_id, source_code, level, note in rule_links:
            rule, source = rules.get(rule_id), sources.get(source_code)
            if rule and source:
                RuleAuthorityLink.objects.get_or_create(
                    form_rule=rule, authority_source=source,
                    defaults={"support_level": level, "relevance_note": note})
                ct += 1
        self.stdout.write(f"  {ct} authority links")

    def _upsert_lines(self, form, lines):
        for ln in lines:
            ln = dict(ln)
            FormLine.objects.update_or_create(tax_form=form, line_number=ln.pop("line_number"), defaults=ln)
        self.stdout.write(f"  {len(lines)} lines")

    def _upsert_diagnostics(self, form, diagnostics):
        for d in diagnostics:
            d = dict(d)
            FormDiagnostic.objects.update_or_create(tax_form=form, diagnostic_id=d.pop("diagnostic_id"), defaults=d)
        self.stdout.write(f"  {len(diagnostics)} diagnostics")

    def _upsert_tests(self, form, scenarios):
        for t in scenarios:
            t = dict(t)
            TestScenario.objects.update_or_create(tax_form=form, scenario_name=t.pop("scenario_name"), defaults=t)
        self.stdout.write(f"  {len(scenarios)} test scenarios")

    def _upsert_form_links(self, sources):
        for source_code, form_code, link_type in AUTHORITY_FORM_LINKS:
            source = sources.get(source_code) or AuthoritySource.objects.filter(source_code=source_code).first()
            if source:
                AuthorityFormLink.objects.get_or_create(
                    authority_source=source, form_code=form_code, link_type=link_type,
                    defaults={"note": f"{source_code} -> {form_code}"})

    def _load_flow_assertions(self):
        for a in FLOW_ASSERTIONS:
            a = dict(a)
            FlowAssertion.objects.update_or_create(assertion_id=a.pop("assertion_id"), defaults=a)
        self.stdout.write(f"  {len(FLOW_ASSERTIONS)} flow assertions")

    def _report_totals(self):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(f"TaxForms: {TaxForm.objects.count()} | FlowAssertions: {FlowAssertion.objects.count()}")
        form = TaxForm.objects.filter(form_number="FORM_5695").first()
        if form:
            uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
            self.stdout.write("FORM_5695: all rules cited" if not uncited
                              else self.style.WARNING(f"FORM_5695 uncited rules: {len(uncited)}"))
