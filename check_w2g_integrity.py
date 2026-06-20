"""Pre-seed math gate for load_1040_w2g (Form W-2G certain gambling winnings).

Run:  poetry run python check_w2g_integrity.py

Independently recomputes every scenario from its OWN transcription of §61 full
inclusion (Σ box-1 winnings + any non-W-2G winnings, summed across documents) and
the box-4 → line-25c aggregation, and cross-checks the loader's helper function.
The loader and this gate share NO math.
"""
import os
import sys
from decimal import Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_w2g as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def check(name, got, want):
    if D(got) != D(want):
        err(f"{name}: recomputed {got} != authored {want}")


# ── Independent math (re-typed; §61 full inclusion, no exclusion/constants) ──
def ind_aggregate(docs, other=0):
    line8b = sum(float(d.get("box1", 0) or 0) for d in docs) + float(other or 0)
    line25c = sum(float(d.get("box4", 0) or 0) for d in docs)
    return (line8b, line25c)


# ── 1. Loader helper vs the independent transcription ──
for docs, other in [
    ([{"box1": 5000, "box4": 0}], 0),
    ([{"box1": 5000, "box4": 1000}], 0),
    ([{"box1": 5000, "box4": 1000}, {"box1": 3000, "box4": 500}], 0),
    ([{"box1": 2000, "box4": 0}], 500),
    ([{"box1": 0, "box4": 200}], 0),
]:
    g = m.aggregate_w2g(docs, other)
    w = ind_aggregate(docs, other)
    for i, lbl in enumerate(("line8b", "line25c")):
        check(f"aggregate_w2g({docs},{other})[{lbl}]", g[i], w[i])

# §61 invariant — NO exclusion is ever applied (the full box-1 winnings are included).
check("no-exclusion full inclusion", m.aggregate_w2g([{"box1": 100000}])[0], 100000)
# The non-W-2G winnings addend lands on line 8b (not dropped, not on 25c).
check("non-W-2G winnings on 8b", m.aggregate_w2g([{"box1": 0}], 750)[0], 750)
check("non-W-2G winnings not on 25c", m.aggregate_w2g([{"box1": 0}], 750)[1], 0)

# ── 2. Scenarios — independent recompute ──
DIAG_KEYS = {"D_W2G_WH_ONLY", "D_W2G_LOSS_SCHA"}
spec = m.FORMS[0]
for s in spec["scenarios"]:
    name = s["scenario_name"].split(" ")[0]
    inp, exp = s["inputs"], s["expected_outputs"]
    if any(k in DIAG_KEYS for k in exp):
        if exp.get("D_W2G_WH_ONLY"):
            docs = inp.get("docs", [])
            if not any(float(d.get("box4", 0) or 0) > 0 and float(d.get("box1", 0) or 0) == 0 for d in docs):
                err(f"{name}: D_W2G_WH_ONLY expected but no doc has box4>0 AND box1==0")
        continue
    line8b, line25c = ind_aggregate(inp["docs"], inp.get("other_gambling_winnings", 0))
    got = {"wg_sch1_line8b": line8b, "wg_line_25c": line25c}
    for k, want in exp.items():
        if k in DIAG_KEYS:
            continue
        if k not in got:
            err(f"{name}.{k}: no independent recompute mapped")
            continue
        check(f"{name}.{k}", got[k], want)

# ── 3. Structural checks ──
known_sources = {s["source_code"] for s in m.AUTHORITY_SOURCES} | set(m.EXISTING_SOURCES_TO_REFERENCE)
for key, idk in (("facts", "fact_key"), ("rules", "rule_id"), ("lines", "line_number"),
                 ("diagnostics", "diagnostic_id"), ("scenarios", "scenario_name")):
    ids = [x[idk] for x in spec[key]]
    if len(ids) != len(set(ids)):
        err(f"FORM_W2G.{key}: duplicate ids")
for r in spec["rules"]:
    if len(r["rule_id"]) > 20:
        err(f"rule_id too long ({len(r['rule_id'])} > 20): {r['rule_id']}")
for d in spec["diagnostics"]:
    if len(d["diagnostic_id"]) > 20:
        err(f"diagnostic_id too long ({len(d['diagnostic_id'])} > 20): {d['diagnostic_id']}")
rule_ids = {r["rule_id"] for r in spec["rules"]}
for rid in rule_ids - {rl[0] for rl in spec["rule_links"]}:
    err(f"rule {rid} has ZERO authority links")
for rid, src, _, _ in spec["rule_links"]:
    if rid not in rule_ids:
        err(f"rule_link references unknown rule {rid}")
    if src not in known_sources:
        err(f"rule_link references unknown source {src}")
diag_ids = {d["diagnostic_id"] for d in spec["diagnostics"]}
for sc in spec["scenarios"]:
    for k in sc["expected_outputs"]:
        if k.startswith("D_W2G_") and k not in diag_ids:
            err(f"{sc['scenario_name']}: expects unknown diagnostic {k}")
fa_ids = [a["assertion_id"] for a in m.FLOW_ASSERTIONS]
if len(fa_ids) != len(set(fa_ids)):
    err("duplicate flow-assertion ids")

# ── Report ──
print("FORM_W2G (facts/rules/lines/diagnostics/scenarios/links):",
      (len(spec["facts"]), len(spec["rules"]), len(spec["lines"]),
       len(spec["diagnostics"]), len(spec["scenarios"]), len(spec["rule_links"])))
print(f"Flow assertions: {len(m.FLOW_ASSERTIONS)}; authority sources: {len(m.AUTHORITY_SOURCES)}")
print("Independently recomputed - T1 5,000 / T2 25c=1,000 / T3 multi 8,000 25c=1,500 / "
      "T4 non-W-2G 2,000+500=2,500 / T5 WH-only warning; the sec.61 full-inclusion (no "
      "exclusion) + the non-W-2G addend on 8b + the box-4 -> 25c aggregation cross-checked.")

if errors:
    print("\nFAILURES:")
    for e in errors:
        print(f"  X {e}")
    sys.exit(1)
print("\nALL CHECKS PASS")
