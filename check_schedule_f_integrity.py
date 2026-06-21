"""Pre-seed content checker for load_1040_schedule_f (Schedule F + the Schedule SE
farm-optional amendment).

Run:  poetry run python check_schedule_f_integrity.py

Mirrors check_topic8_integrity.py: validates the authored lists WITHOUT touching
the DB, then INDEPENDENTLY recomputes every numeric scenario from its OWN
transcription of the form math (NOT imported from the loader) — the Schedule F
cash-method income/expense/net chain (line 1c, the verified line-9 right-column
sum, line 33, line 34) and the Schedule SE farm optional method (2/3 of gross farm
income, capped at the year's maximum). This is the MATH GATE that must pass before
Ken's review walk. Loader & gate share no math.

The checker carries its OWN independent copies of the year-keyed farm-optional
constants (re-typed from the 2025 Schedule SE Part II face) and cross-checks the
loader's module constants — so a transcription error in the loader cannot also
pass the checker.
"""
import os
import sys
from decimal import Decimal, ROUND_HALF_UP

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_schedule_f as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def whole(x):
    return D(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def check(name, got, want):
    if D(got) != D(want):
        err(f"{name}: recomputed {got} != authored {want}")


# ═══════════════════════════════════════════════════════════════════════════
# INDEPENDENT CONSTANTS (re-typed from the 2025 Schedule SE Part II face; NOT imported)
# ═══════════════════════════════════════════════════════════════════════════

IND_FARM_OPT_MAX = {2025: 7240}             # Sch SE line 14 ("Maximum income for optional methods")
IND_FARM_OPT_GROSS_CEILING = {2025: 10860}  # eligibility: gross farm income not more than
IND_FARM_OPT_PROFIT_FLOOR = {2025: 7840}    # eligibility: OR net farm profit less than
IND_FARM_OPT_FRACTION = "2/3"               # statutory two-thirds (non-indexed)


# ═══════════════════════════════════════════════════════════════════════════
# Independent recomputations of the form math
# ═══════════════════════════════════════════════════════════════════════════

def sf_val(inp, ln):
    return D(inp.get(f"line_{ln}", 0))


def sched_f(inp):
    """Schedule F cash-method income/expense/net chain -> dict."""
    l1c = sf_val(inp, "1a") - sf_val(inp, "1b")
    l9 = (l1c + sf_val(inp, "2") + sf_val(inp, "3b") + sf_val(inp, "4b") + sf_val(inp, "5a")
          + sf_val(inp, "5c") + sf_val(inp, "6b") + sf_val(inp, "6d") + sf_val(inp, "7") + sf_val(inp, "8"))
    l33 = sf_val(inp, "33")
    l34 = l9 - l33
    return {"1c": l1c, "9": l9, "33": l33, "34": l34}


def farm_optional(gross, year):
    """Schedule SE Part II farm optional method -> dict (or RED for an unpublished year)."""
    if year not in IND_FARM_OPT_MAX:
        return {"red_year": True}
    l14 = D(IND_FARM_OPT_MAX[year])
    raw = whole(D(gross) * 2 / 3)              # two-thirds of gross farm income, whole dollars
    l15 = min(raw, l14)
    return {"14": l14, "15": l15, "raw": raw, "red_year": False}


def farm_opt_eligible(gross, net, year=2025):
    return (D(gross) <= D(IND_FARM_OPT_GROSS_CEILING[year])) or (D(net) < D(IND_FARM_OPT_PROFIT_FLOOR[year]))


# ═══════════════════════════════════════════════════════════════════════════
# Structural checks (mirror check_topic8_integrity.py)
# ═══════════════════════════════════════════════════════════════════════════

for spec in m.FORMS:
    fn = spec["identity"]["form_number"]

    fact_keys = [f["fact_key"] for f in spec["facts"]]
    if len(fact_keys) != len(set(fact_keys)):
        dupes = sorted({k for k in fact_keys if fact_keys.count(k) > 1})
        err(f"{fn}: duplicate fact keys {dupes}")

    rule_ids = [r["rule_id"] for r in spec["rules"]]
    if len(rule_ids) != len(set(rule_ids)):
        err(f"{fn}: duplicate rule ids")

    line_nos = [ln["line_number"] for ln in spec["lines"]]
    if len(line_nos) != len(set(line_nos)):
        dupes = sorted({k for k in line_nos if line_nos.count(k) > 1})
        err(f"{fn}: duplicate line numbers {dupes}")

    diag_ids = [d["diagnostic_id"] for d in spec["diagnostics"]]
    if len(diag_ids) != len(set(diag_ids)):
        err(f"{fn}: duplicate diagnostic ids")

    linked = {rid for rid, *_ in spec["rule_links"]}
    uncited = [rid for rid in rule_ids if rid not in linked]
    if uncited:
        err(f"{fn}: uncited rules {uncited}")
    dangling = [rid for rid in linked if rid not in rule_ids]
    if dangling:
        err(f"{fn}: rule_links reference unknown rules {dangling}")

    for r in spec["rules"]:
        for key in r.get("inputs", []):
            if key not in fact_keys:
                err(f"{fn} {r['rule_id']}: input '{key}' is not a declared fact")

    for f in spec["facts"]:
        if f["data_type"] == "choice" and not f.get("choices"):
            err(f"{fn} fact {f['fact_key']}: choice type without choices")

# ── flow assertions ──
fa_ids = [a["assertion_id"] for a in m.FLOW_ASSERTIONS]
if len(fa_ids) != len(set(fa_ids)):
    err("duplicate flow assertion ids")
for a in m.FLOW_ASSERTIONS:
    if len(a["assertion_id"]) > 20:
        err(f"assertion_id too long (>20): {a['assertion_id']}")


# ═══════════════════════════════════════════════════════════════════════════
# Loader constants cross-check (loader module constants == independent copies)
# ═══════════════════════════════════════════════════════════════════════════

if D(m.FARM_OPT_MAX_INCOME[2025]) != D(IND_FARM_OPT_MAX[2025]):
    err(f"FARM_OPT_MAX_INCOME[2025] loader {m.FARM_OPT_MAX_INCOME[2025]} != independent {IND_FARM_OPT_MAX[2025]}")
if D(m.FARM_OPT_GROSS_CEILING[2025]) != D(IND_FARM_OPT_GROSS_CEILING[2025]):
    err(f"FARM_OPT_GROSS_CEILING[2025] loader {m.FARM_OPT_GROSS_CEILING[2025]} != independent {IND_FARM_OPT_GROSS_CEILING[2025]}")
if D(m.FARM_OPT_PROFIT_FLOOR[2025]) != D(IND_FARM_OPT_PROFIT_FLOOR[2025]):
    err(f"FARM_OPT_PROFIT_FLOOR[2025] loader {m.FARM_OPT_PROFIT_FLOOR[2025]} != independent {IND_FARM_OPT_PROFIT_FLOOR[2025]}")
if m.FARM_OPT_FRACTION != IND_FARM_OPT_FRACTION:
    err(f"FARM_OPT_FRACTION loader {m.FARM_OPT_FRACTION} != independent {IND_FARM_OPT_FRACTION}")
# 2026 must be UNPUBLISHED (no silent stale carry).
if 2026 in m.FARM_OPT_MAX_INCOME:
    err("FARM_OPT_MAX_INCOME has a 2026 entry — 2026 amounts are unpublished and must fire RED, not compute")


# ═══════════════════════════════════════════════════════════════════════════
# Scenario lookup (key on the first token of scenario_name)
# ═══════════════════════════════════════════════════════════════════════════

s = {sc["scenario_name"].split(" ")[0]: sc for spec in m.FORMS for sc in spec["scenarios"]}


def i_of(key):
    return s[key]["inputs"]


def o_of(key):
    return s[key]["expected_outputs"]


# ── Schedule F ──
i, o = i_of("SF-T1"), o_of("SF-T1")
r = sched_f(i)
check("SF-T1 L9", r["9"], o["line_9"]); check("SF-T1 L34", r["34"], o["line_34"])

i, o = i_of("SF-T2"), o_of("SF-T2")
r = sched_f(i)
check("SF-T2 L1c", r["1c"], o["line_1c"]); check("SF-T2 L9", r["9"], o["line_9"]); check("SF-T2 L34", r["34"], o["line_34"])

i, o = i_of("SF-T3"), o_of("SF-T3")
r = sched_f(i)
check("SF-T3 L9", r["9"], o["line_9"]); check("SF-T3 L34", r["34"], o["line_34"])
if r["34"] >= 0:
    err("SF-T3: fixture should produce a net farm loss (D_SF_LOSS)")

# SF-T4 — accrual RED gate.
if i_of("SF-T4").get("sf_accounting_method") != "accrual":
    err("SF-T4: fixture must set sf_accounting_method='accrual' for D_SF_ACCRUAL")

i, o = i_of("SF-T5"), o_of("SF-T5")
r = sched_f(i)
check("SF-T5 L9", r["9"], o["line_9"]); check("SF-T5 L34", r["34"], o["line_34"])
if not (D(i.get("line_5a", 0)) > 0):
    err("SF-T5: fixture must set line_5a > 0 for D_SF_CCC_ELECTION")
# the CCC-elected amount (5a) must be INSIDE line 9 (verified right-column membership).
if r["9"] != (r["9"] - D(i.get("line_5a", 0)) + D(i.get("line_5a", 0))):
    err("SF-T5: line 5a not in the line-9 sum")  # tautology guard; real coverage below
if sched_f({**i, "line_5a": 0})["9"] != r["9"] - D(i["line_5a"]):
    err("SF-T5: removing line 5a did not reduce line 9 by 5a (5a not summed)")

i, o = i_of("SF-T6"), o_of("SF-T6")
r = sched_f(i)
check("SF-T6 L9", r["9"], o["line_9"]); check("SF-T6 L34", r["34"], o["line_34"])
if i.get("sf_crop_insurance_defer_election_6c") is not True:
    err("SF-T6: fixture must set sf_crop_insurance_defer_election_6c for D_SF_CROPINS_DEFER")
# 6b (taxable) is summed; 6a (received) is NOT.
if sched_f({**i, "line_6a": 999999})["9"] != r["9"]:
    err("SF-T6: line 6a (received) leaked into line 9 — only 6b (taxable) belongs")

i, o = i_of("SF-T7"), o_of("SF-T7")
r = sched_f(i)
check("SF-T7 L34", r["34"], o["line_34"])
if i.get("sf_material_participation") is not False:
    err("SF-T7: fixture must set sf_material_participation=False for D_SF_PASSIVE")
if r["34"] >= 0:
    err("SF-T7: passive fixture should be a net loss")

i, o = i_of("SF-T8"), o_of("SF-T8")
r = sched_f(i)
check("SF-T8 L34", r["34"], o["line_34"])
if i.get("sf_some_not_at_risk_36b") is not True:
    err("SF-T8: fixture must set sf_some_not_at_risk_36b for D_SF_ATRISK")

i, o = i_of("SF-T9"), o_of("SF-T9")
r = sched_f(i)
check("SF-T9 L9", r["9"], o["line_9"]); check("SF-T9 L34", r["34"], o["line_34"])
if not (D(i.get("line_14", 0)) > 0 and D(i["line_14"]) <= D(i["line_33"])):
    err("SF-T9: depreciation (line 14) must be > 0 and within total expenses (line 33)")

# SF-T10 — multi-farm aggregation.
i, o = i_of("SF-T10"), o_of("SF-T10")
agg = sum(D(farm["line_34"]) for farm in i["farms"])
check("SF-T10 Sch 1 L6 (sum farms)", agg, o["sch1_l6"])
check("SF-T10 Sch SE L1a (sum farms, same proprietor)", agg, o["schse_l1a"])

# ── Schedule SE farm optional method ──
i, o = i_of("SE-FARMOPT-1"), o_of("SE-FARMOPT-1")
r = farm_optional(i["se_gross_farm_income"], i["tax_year"])
check("SE-FARMOPT-1 L14", r["14"], o["line_14"]); check("SE-FARMOPT-1 L15", r["15"], o["line_15"])
check("SE-FARMOPT-1 -> line 4b", r["15"], o["line_4b"])
if not farm_opt_eligible(i["se_gross_farm_income"], 0, i["tax_year"]):
    err("SE-FARMOPT-1: fixture should be eligible (gross <= ceiling)")
if not (r["raw"] < r["14"]):
    err("SE-FARMOPT-1: the 2/3 fraction should bind below the cap (raw < max)")

i, o = i_of("SE-FARMOPT-2"), o_of("SE-FARMOPT-2")
r = farm_optional(i["se_gross_farm_income"], i["tax_year"])
check("SE-FARMOPT-2 L14", r["14"], o["line_14"]); check("SE-FARMOPT-2 L15", r["15"], o["line_15"])
check("SE-FARMOPT-2 -> line 4b", r["15"], o["line_4b"])
if not (r["raw"] >= r["14"]):
    err("SE-FARMOPT-2: the $7,240 cap should bind (raw >= max)")

# SE-FARMOPT-3 — 2026 RED gate (constants unpublished).
i = i_of("SE-FARMOPT-3")
r = farm_optional(i["se_gross_farm_income"], i["tax_year"])
if not r.get("red_year"):
    err("SE-FARMOPT-3: 2026 farm optional should RED (constants unpublished), not compute")
if i["tax_year"] in IND_FARM_OPT_MAX:
    err("SE-FARMOPT-3: fixture year must be an unpublished year (2026)")

# SE-FARMOPT-4 — ineligible election.
i = i_of("SE-FARMOPT-4")
if farm_opt_eligible(i["se_gross_farm_income"], i["se_net_farm_profit"], 2025):
    err("SE-FARMOPT-4: fixture should be INELIGIBLE (gross > ceiling AND net profit >= floor)")


# ═══════════════════════════════════════════════════════════════════════════
# Load-bearing checks on the flow-assertion constants_check
# ═══════════════════════════════════════════════════════════════════════════

def fa(aid):
    return next((a for a in m.FLOW_ASSERTIONS if a["assertion_id"] == aid), None)


a = fa("FA-1040-SCHF-08")
if a:
    c = a["definition"]["constants"]
    if D(c["max_2025"]) != D(IND_FARM_OPT_MAX[2025]):
        err("FA-SCHF-08: max_2025 disagrees with independent")
    if D(c["gross_ceiling_2025"]) != D(IND_FARM_OPT_GROSS_CEILING[2025]):
        err("FA-SCHF-08: gross_ceiling_2025 disagrees with independent")
    if D(c["profit_floor_2025"]) != D(IND_FARM_OPT_PROFIT_FLOOR[2025]):
        err("FA-SCHF-08: profit_floor_2025 disagrees with independent")
    if c.get("fraction") != IND_FARM_OPT_FRACTION:
        err("FA-SCHF-08: fraction != 2/3")
    if c.get("supported_years") != [2025]:
        err("FA-SCHF-08: supported_years != [2025]")
else:
    err("FA-1040-SCHF-08 not found")

# the line-34 -> Sch 1 L6 + Sch SE L1a dual-write assertion must be present.
a01 = fa("FA-1040-SCHF-01")
if not a01 or set(a01["definition"].get("must_write_to", [])) != {"SCH_1.6", "SCHEDULE_SE.1a"}:
    err("FA-1040-SCHF-01: line 34 must write to BOTH SCH_1.6 and SCHEDULE_SE.1a")


# ═══════════════════════════════════════════════════════════════════════════
# Report
# ═══════════════════════════════════════════════════════════════════════════

counts = {spec["identity"]["form_number"]: (len(spec["facts"]), len(spec["rules"]),
          len(spec["lines"]), len(spec["diagnostics"]), len(spec["scenarios"]),
          len(spec["rule_links"])) for spec in m.FORMS}

print("Per-form counts (facts/rules/lines/diagnostics/scenarios/links):")
for fn, c in counts.items():
    print(f"  {fn}: {c}")
print(f"Flow assertions: {len(m.FLOW_ASSERTIONS)}")
print(f"Authority sources (new): {len(m.AUTHORITY_SOURCES)}; topics: {len(m.AUTHORITY_TOPICS)}; "
      f"new excerpts on existing: {len(m.NEW_EXCERPTS_ON_EXISTING)}")
print("Independently recomputed: SF-T1..T10 (line 1c / the verified line-9 right-column sum / "
      "line 33 / line 34; 5a-in-9 + 6a-not-in-9 membership; multi-farm aggregation), SE-FARMOPT-1..4 "
      "(2/3 of gross farm income, $7,240 cap, eligibility, 2026 RED); loader constants cross-checked "
      "vs an independent transcription of the 2025 Schedule SE Part II face.")

if errors:
    print("\nFAILURES:")
    for e in errors:
        print(f"  X {e}")
    sys.exit(1)
print("\nALL CHECKS PASS")
