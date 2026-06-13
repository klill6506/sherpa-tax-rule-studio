"""Pre-seed math gate for load_1040_simplified_method (NEXT-UP #1).

Run:  poetry run python check_simplified_method_integrity.py

Mirrors check_topic9_integrity.py: validates the authored lists WITHOUT
touching the DB, then INDEPENDENTLY recomputes every numeric scenario from its
OWN transcription of the Simplified Method Worksheet (re-typed, not imported)
— the Table 1/Table 2 number-of-payments lookup, cost ÷ payments, the
months multiplier, the post-1986 cost cap (line 8 = smaller of line 5 / line
7), the taxable = box1 − tax-free, and the recovered-through-year / balance
carryover — plus the scope gates (pre-1996 / pre-1987 / joint-no-survivor /
IRA). The checker carries its OWN copies of the two tables (re-typed from Pub
575) and cross-checks the loader's tables cell-by-cell.

This is the MATH GATE that must pass before Ken's review walk.
"""
import os
import sys
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_simplified_method as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def check(name, got, want):
    if D(got) != D(want):
        err(f"{name}: recomputed {got} != authored {want}")


# ═══════════════════════════════════════════════════════════════════════════
# INDEPENDENT CONSTANTS (re-typed from Pub 575 (2025); NOT imported)
# ═══════════════════════════════════════════════════════════════════════════

IND_TABLE_1 = [(55, 360), (60, 310), (65, 260), (70, 210), (200, 160)]
IND_TABLE_2 = [(110, 410), (120, 360), (130, 310), (140, 260), (999, 210)]
IND_SIMPLIFIED_START = date(1996, 11, 19)
IND_TABLE2_START = date(1998, 1, 1)
IND_PRE1987 = date(1987, 1, 1)


def ind_lookup(table, age):
    for upper, payments in table:
        if age <= upper:
            return payments
    return table[-1][1]


def _q(amount):
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def sm(start, age, joint, survivor_age, cost, prior, months, box1, ira=False):
    """Independent Simplified Method Worksheet recompute. Returns the line
    dict, or a {diagnostic: True} dict for the RED-defer gates."""
    if ira:
        return {"D_SM_006": True}
    if start < IND_PRE1987:
        return {"D_SM_002": True}
    if start < IND_SIMPLIFIED_START:
        return {"D_SM_001": True}
    table = 2 if (joint and start >= IND_TABLE2_START) else 1
    if table == 2 and survivor_age is None:
        return {"D_SM_003": True}
    combined = age + (survivor_age or 0)
    number = ind_lookup(IND_TABLE_2 if table == 2 else IND_TABLE_1,
                        combined if table == 2 else age)
    per = _q(D(cost) / D(number))
    line5 = _q(per * D(months))
    line7 = D(cost) - D(prior)
    line8 = min(line5, line7)
    taxable = max(Decimal(0), D(box1) - line8)
    line10 = D(prior) + line8
    line11 = D(cost) - line10
    return {
        "sm_table_used": table, "sm_number_of_payments": number,
        "sm_tax_free_per_payment": per, "sm_tax_free_this_year": line8,
        "sm_taxable": taxable, "sm_recovered_through_year": line10,
        "sm_balance_of_cost": line11,
        "D_SM_004": line11 == 0,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 1. Loader tables vs the independent transcription (cell-by-cell)
# ═══════════════════════════════════════════════════════════════════════════

if m.SM_TABLE_1 != IND_TABLE_1:
    err(f"SM_TABLE_1 {m.SM_TABLE_1} != independent {IND_TABLE_1}")
if m.SM_TABLE_2 != IND_TABLE_2:
    err(f"SM_TABLE_2 {m.SM_TABLE_2} != independent {IND_TABLE_2}")
if m.SM_SIMPLIFIED_START != IND_SIMPLIFIED_START:
    err("SM_SIMPLIFIED_START boundary drift")
if m.SM_TABLE2_START != IND_TABLE2_START:
    err("SM_TABLE2_START boundary drift")
if m.SM_PRE1987 != IND_PRE1987:
    err("SM_PRE1987 boundary drift")

# The loader's shared lookup helper agrees with the independent one.
for tbl_loader, tbl_ind in ((m.SM_TABLE_1, IND_TABLE_1), (m.SM_TABLE_2, IND_TABLE_2)):
    for age in (40, 55, 56, 60, 65, 66, 70, 71, 90, 110, 111, 130, 141, 200):
        if m.sm_lookup_payments(tbl_loader, age) != ind_lookup(tbl_ind, age):
            err(f"sm_lookup_payments disagree at age {age}")


# ═══════════════════════════════════════════════════════════════════════════
# 2. SIMPLIFIED_METHOD scenarios — independent recompute
# ═══════════════════════════════════════════════════════════════════════════

def _date(s):
    return date.fromisoformat(s)


for s in m.SM_SCENARIOS:
    name = s["scenario_name"].split(" ")[0]
    inp, exp = s["inputs"], s["expected_outputs"]
    got = sm(
        _date(inp["sm_annuity_start_date"]),
        inp.get("sm_age_at_start", 0),
        bool(inp.get("sm_is_joint_survivor", False)),
        inp.get("sm_survivor_age_at_start"),
        inp.get("sm_cost_in_plan", 0),
        inp.get("sm_prior_recovered_tax_free", 0),
        inp.get("sm_months_paid_this_year", 12),
        inp.get("box1_gross", 0),
        bool(inp.get("ira_sep_simple", False)),
    )
    for k, want in exp.items():
        if k.startswith("D_SM_"):
            if bool(got.get(k)) is not bool(want):
                err(f"{name}.{k}: recomputed {got.get(k)} != authored {want}")
            continue
        if k not in got:
            err(f"{name}.{k}: no independent recompute mapped")
            continue
        if isinstance(want, bool) or isinstance(got[k], bool):
            if bool(got[k]) != bool(want):
                err(f"{name}.{k}: {got[k]} != {want}")
        else:
            check(f"{name}.{k}", got[k], want)


# ═══════════════════════════════════════════════════════════════════════════
# 3. Structural checks
# ═══════════════════════════════════════════════════════════════════════════

known_sources = {s["source_code"] for s in m.AUTHORITY_SOURCES} | set(m.EXISTING_SOURCES_TO_REFERENCE)
for spec in m.FORMS:
    fn = spec["identity"]["form_number"]
    for key, idk in (("facts", "fact_key"), ("rules", "rule_id"), ("lines", "line_number"),
                     ("diagnostics", "diagnostic_id"), ("scenarios", "scenario_name")):
        ids = [x[idk] for x in spec[key]]
        if len(ids) != len(set(ids)):
            err(f"{fn}.{key}: duplicate ids")
    rule_ids = {r["rule_id"] for r in spec["rules"]}
    linked = {rl[0] for rl in spec["rule_links"]}
    for rid in rule_ids - linked:
        err(f"{fn}: rule {rid} has ZERO authority links")
    for rid, src, _, _ in spec["rule_links"]:
        if rid not in rule_ids:
            err(f"{fn}: rule_link references unknown rule {rid}")
        if src not in known_sources:
            err(f"{fn}: rule_link references unknown source {src}")
    diag_ids = {d["diagnostic_id"] for d in spec["diagnostics"]}
    for sc in spec["scenarios"]:
        for k in sc["expected_outputs"]:
            if k.startswith("D_SM_") and k not in diag_ids:
                err(f"{fn}/{sc['scenario_name']}: expects unknown diagnostic {k}")

# worksheet line-count pin (sm_1..sm_11)
ws_nums = [ln["line_number"] for ln in m.SM_LINES]
if len([n for n in ws_nums if n.startswith("sm_")]) != 11:
    err(f"SIMPLIFIED_METHOD: expected 11 sm_* lines, got {len(ws_nums)}")

fa_ids = [a["assertion_id"] for a in m.FLOW_ASSERTIONS]
if len(fa_ids) != len(set(fa_ids)):
    err("duplicate flow-assertion ids")
if m.READY_TO_SEED:
    err("READY_TO_SEED must be False until Ken's walk")


# ═══════════════════════════════════════════════════════════════════════════
# Report
# ═══════════════════════════════════════════════════════════════════════════

spec = m.FORMS[0]
print("SIMPLIFIED_METHOD (facts/rules/lines/diagnostics/scenarios/links):",
      (len(spec["facts"]), len(spec["rules"]), len(spec["lines"]),
       len(spec["diagnostics"]), len(spec["scenarios"]), len(spec["rule_links"])))
print(f"Flow assertions: {len(m.FLOW_ASSERTIONS)}; authority sources (new): {len(m.AUTHORITY_SOURCES)}")
print("Independently recomputed: SM-T1 (single age 66), SM-T2 (joint combined 130), "
      "SM-T3 (cost cap binds -> balance 0 / D_SM_004), SM-T4 (partial 7-month, age 71); "
      "SM-G1/G2/G3 gates; both Pub-575 tables cross-checked cell-by-cell + the boundary dates.")

if errors:
    print("\nFAILURES:")
    for e in errors:
        print(f"  X {e}")
    sys.exit(1)
print("\nALL CHECKS PASS")
