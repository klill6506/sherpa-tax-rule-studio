"""Pre-seed content checker for load_1040_intdiv_qdcgt (Topic 3).

Run:  poetry run python check_intdiv_integrity.py
Mirrors check_sch123_integrity.py: validates the authored lists WITHOUT
touching the DB, then INDEPENDENTLY recomputes every scenario — the full
QDCGT worksheet (25 lines) from its own bracket/breakpoint transcription,
plus the aggregation and Schedule B arithmetic.
"""
import os
import sys
from decimal import Decimal, ROUND_HALF_UP

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_intdiv_qdcgt as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


# ── per-form structural checks ──
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

    for ln in spec["lines"]:
        for rid in ln.get("source_rules", []):
            if rid not in rule_ids:
                err(f"{fn} line {ln['line_number']}: unknown source_rule {rid}")

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

# ── independent QDCGT recomputation ──
# Brackets transcribed INDEPENDENTLY here (RP 2024-40 §2.01 / RP 2025-32 §4.01,
# matching the spine-verified compute.TAX_BRACKETS).
INF = Decimal("999999999999")
BRACKETS = {
    (2025, "single"): [(11925, "0.10"), (48475, "0.12"), (103350, "0.22"), (197300, "0.24"),
                       (250525, "0.32"), (626350, "0.35"), (INF, "0.37")],
    (2025, "mfs"): [(11925, "0.10"), (48475, "0.12"), (103350, "0.22"), (197300, "0.24"),
                    (250525, "0.32"), (375800, "0.35"), (INF, "0.37")],
    (2025, "mfj"): [(23850, "0.10"), (96950, "0.12"), (206700, "0.22"), (394600, "0.24"),
                    (501050, "0.32"), (751600, "0.35"), (INF, "0.37")],
    (2025, "hoh"): [(17000, "0.10"), (64850, "0.12"), (103350, "0.22"), (197300, "0.24"),
                    (250500, "0.32"), (626350, "0.35"), (INF, "0.37")],
    (2026, "mfj"): [(24800, "0.10"), (100800, "0.12"), (211400, "0.22"), (403550, "0.24"),
                    (512450, "0.32"), (768700, "0.35"), (INF, "0.37")],
}
# QDCGT breakpoints transcribed INDEPENDENTLY (RP 2024-40 §2.03 / RP 2025-32 §4.03).
ZERO_MAX = {(2025, "single"): 48350, (2025, "mfs"): 48350, (2025, "mfj"): 96700,
            (2025, "qss"): 96700, (2025, "hoh"): 64750,
            (2026, "single"): 49450, (2026, "mfs"): 49450, (2026, "mfj"): 98900,
            (2026, "qss"): 98900, (2026, "hoh"): 66200}
MAX_15 = {(2025, "single"): 533400, (2025, "mfs"): 300000, (2025, "mfj"): 600050,
          (2025, "qss"): 600050, (2025, "hoh"): 566700,
          (2026, "single"): 545500, (2026, "mfs"): 306850, (2026, "mfj"): 613700,
          (2026, "qss"): 613700, (2026, "hoh"): 579600}


def D(x):
    return Decimal(str(x))


def bracket_tax(ti, status, year):
    tax = Decimal("0")
    prev = Decimal("0")
    for upper, rate in BRACKETS[(year, status)]:
        upper = D(upper)
        if ti <= prev:
            break
        tax += (min(ti, upper) - prev) * Decimal(rate)
        prev = upper
    return tax


def half_up_dollar(x):
    return x.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def tax_method(amount, status, year):
    """Table semantics below $100K (here: the >=3,000 $50-band only — every
    scenario sits there); TCW == exact brackets at/above."""
    amount = D(amount)
    if amount >= 100000:
        return bracket_tax(amount, status, year)
    if amount < 3000:
        raise AssertionError("checker only implements the $50 band — scenario out of range")
    mid = (amount // 50) * 50 + 25
    return half_up_dollar(bracket_tax(mid, status, year))


def qdcgt(ti, qd, cgd, status, year):
    ws = {}
    ws["1"] = D(ti); ws["2"] = D(qd); ws["3"] = D(cgd)
    ws["4"] = ws["2"] + ws["3"]
    ws["5"] = max(Decimal("0"), ws["1"] - ws["4"])
    ws["6"] = D(ZERO_MAX[(year, status)])
    ws["7"] = min(ws["1"], ws["6"])
    ws["8"] = min(ws["5"], ws["7"])
    ws["9"] = ws["7"] - ws["8"]
    ws["10"] = min(ws["1"], ws["4"])
    ws["11"] = ws["9"]
    ws["12"] = ws["10"] - ws["11"]
    ws["13"] = D(MAX_15[(year, status)])
    ws["14"] = min(ws["1"], ws["13"])
    ws["15"] = ws["5"] + ws["9"]
    ws["16"] = max(Decimal("0"), ws["14"] - ws["15"])
    ws["17"] = min(ws["12"], ws["16"])
    ws["18"] = half_up_dollar(Decimal("0.15") * ws["17"])
    ws["19"] = ws["9"] + ws["17"]
    ws["20"] = ws["10"] - ws["19"]
    ws["21"] = half_up_dollar(Decimal("0.20") * ws["20"])
    ws["22"] = tax_method(ws["5"], status, year)
    ws["23"] = ws["18"] + ws["21"] + ws["22"]
    ws["24"] = tax_method(ws["1"], status, year)
    ws["25"] = min(ws["23"], ws["24"])
    return ws


def check(name, got, want):
    if D(got) != D(want):
        err(f"{name}: recomputed {got} != authored {want}")


s = {sc["scenario_name"].split(" ")[0]: sc for spec in m.FORMS for sc in spec["scenarios"]}

# QDCGT scenarios
for key in ("ID-Q1", "ID-Q2", "ID-Q3", "ID-Q4", "ID-Q9", "ID-Q10", "ID-Q11", "ID-Q12"):
    sc = s[key]
    i = sc["inputs"]
    ws = qdcgt(i["ws1_taxable_income"], i["ws2_qd"], i["ws3_cgd"], i["filing_status"], i["tax_year"])
    for out_key, want in sc["expected_outputs"].items():
        if out_key.startswith("ws_"):
            check(f"{key} {out_key}", ws[out_key.removeprefix("ws_")], want)
        elif out_key == "1040_line_16":
            check(f"{key} line16", ws["25"], want)
    # partition identity on every run (FA-1040-INTDIV-07)
    if ws["9"] + ws["17"] + ws["20"] != ws["10"]:
        err(f"{key}: partition identity WS9+WS17+WS20 != WS10")

# rounding pin is load-bearing (ID-Q9 must actually hit a fractional product)
ws_q9 = qdcgt(50000, 10000, 0, "single", 2025)
if (Decimal("0.15") * ws_q9["17"]) == half_up_dollar(Decimal("0.15") * ws_q9["17"]):
    err("ID-Q9: 0.15 x WS17 is whole — the rounding pin would not catch a convention change")

# boundary pair actually brackets the breakpoint
if qdcgt(48350, 5000, 0, "mfs", 2025)["12"] != 0:
    err("ID-Q10: lower boundary should leave WS12 == 0 (all QD at 0%)")
if qdcgt(48550, 5000, 0, "mfs", 2025)["17"] != 200:
    err("ID-Q11: upper boundary should put exactly 200 at 15%")

# ── aggregation scenarios ──
def int_net(doc):
    return (doc.get("box1", 0) + doc.get("box3", 0) + doc.get("box10", 0)
            - doc.get("box11", 0) - doc.get("box12", 0)
            - doc.get("nominee", 0) - doc.get("accrued", 0))


i = s["ID-T1"]["inputs"]
two_b = sum(int_net(d) for d in i["int_docs"]) - i.get("sch_b_line_3_8815", 0)
two_a = sum(max(0, d.get("box8", 0) - d.get("box13", 0)) for d in i["int_docs"]) \
    + sum(d.get("box12", 0) for d in i["div_docs"])
check("ID-T1 2b", two_b, s["ID-T1"]["expected_outputs"]["1040_line_2b"])
check("ID-T1 2a", two_a, s["ID-T1"]["expected_outputs"]["1040_line_2a"])
# trap: the pin must catch box-3-as-subset and premium-sign bugs
if two_b == sum(int_net(d) - d.get("box3", 0) for d in i["int_docs"]) - i.get("sch_b_line_3_8815", 0):
    err("ID-T1: pin would not catch dropping box 3")
if two_b == sum(int_net(d) + 2 * (d.get("box11", 0) + d.get("box12", 0)) for d in i["int_docs"]) - i["sch_b_line_3_8815"]:
    err("ID-T1: pin would not catch premium sign flip")

i = s["ID-T2"]["inputs"]
three_b = sum(d.get("box1a", 0) - d.get("nominee", 0) for d in i["div_docs"])
three_a = sum(d.get("box1b", 0) for d in i["div_docs"])
wh = sum(d.get("box4", 0) for d in i["int_docs"]) + sum(d.get("box4", 0) for d in i["div_docs"])
check("ID-T2 3b", three_b, s["ID-T2"]["expected_outputs"]["1040_line_3b"])
check("ID-T2 3a", three_a, s["ID-T2"]["expected_outputs"]["1040_line_3a"])
check("ID-T2 25b", wh, s["ID-T2"]["expected_outputs"]["1040_line_25b"])
if three_a > three_b:
    err("ID-T2: fixture accidentally violates 3a <= 3b")

i = s["ID-T3"]["inputs"]
docs_clean = all(d.get("box2b", 0) == d.get("box2c", 0) == d.get("box2d", 0) == 0 for d in i["div_docs"])
seven_a = sum(d.get("box2a", 0) for d in i["div_docs"]) if (i.get("capital_gain_distributions_only") and docs_clean) else None
check("ID-T3 7a", seven_a, s["ID-T3"]["expected_outputs"]["1040_line_7a"])

# SCH_B scenarios
i = s["SB-T1"]["inputs"]
l2 = sum(int_net(d) for d in i["int_docs"])
l4 = l2 - i["form_8815_exclusion"]
check("SB-T1 L2", l2, s["SB-T1"]["expected_outputs"]["2"])
check("SB-T1 L4", l4, s["SB-T1"]["expected_outputs"]["4"])
check("SB-T1 ties 2b", l4, s["SB-T1"]["expected_outputs"]["1040_line_2b"])
# cross-fixture consistency with ID-T1 (same roster, both presentations)
check("SB-T1 == ID-T1 2b", l4, s["ID-T1"]["expected_outputs"]["1040_line_2b"])

i = s["SB-T2"]["inputs"]
l6 = sum(d.get("box1a", 0) - d.get("nominee", 0) for d in i["div_docs"])
check("SB-T2 L6", l6, s["SB-T2"]["expected_outputs"]["6"])

i = s["SB-T3"]["inputs"]
req = (sum(int_net(d) for d in i["int_docs"]) > 1500) or (sum(d.get("box1a", 0) for d in i["div_docs"]) > 1500)
if req != s["SB-T3"]["expected_outputs"]["schedule_b_required"]:
    err("SB-T3: required-gate recomputation mismatch")

i = s["SB-DG1"]["inputs"]
if not sum(int_net(d) for d in i["int_docs"]) > 1500:
    err("SB-DG1: fixture does not cross the $1,500 threshold")

# ── report ──
counts = {spec["identity"]["form_number"]: (len(spec["facts"]), len(spec["rules"]),
          len(spec["lines"]), len(spec["diagnostics"]), len(spec["scenarios"]),
          len(spec["rule_links"])) for spec in m.FORMS}

print("Per-form counts (facts/rules/lines/diagnostics/scenarios/links):")
for fn, c in counts.items():
    print(f"  {fn}: {c}")
print(f"Flow assertions: {len(m.FLOW_ASSERTIONS)}")
print(f"Authority sources (new): {len(m.AUTHORITY_SOURCES)}; topics: {len(m.AUTHORITY_TOPICS)}; "
      f"new excerpts on existing: {len(m.NEW_EXCERPTS_ON_EXISTING)}")

if errors:
    print("\nFAILURES:")
    for e in errors:
        print(f"  X {e}")
    sys.exit(1)
print("\nALL CHECKS PASS")
