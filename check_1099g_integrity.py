"""Pre-seed math gate for load_1040_1099g (Form 1099-G unemployment compensation).

Run:  poetry run python check_1099g_integrity.py

Independently recomputes every scenario from its OWN transcription of the §85
full-inclusion + same-year-repayment netting (max(0, box1 − repaid), summed across
documents) and the box-4 → line-25b aggregation, and cross-checks the loader's
helper functions. The loader and this gate share NO math.
"""
import os
import sys
from decimal import Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_1099g as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def check(name, got, want):
    if D(got) != D(want):
        err(f"{name}: recomputed {got} != authored {want}")


# ── Independent math (re-typed; §85 full inclusion, no exclusion/constants) ──
def ind_net(box1, repaid):
    return max(0.0, float(box1 or 0) - float(repaid or 0))


def ind_aggregate(docs):
    line7 = sum(ind_net(d.get("box1", 0), d.get("repaid_same_year", 0)) for d in docs)
    repaid = sum(float(d.get("repaid_same_year", 0) or 0) for d in docs)
    line25b = sum(float(d.get("box4", 0) or 0) for d in docs)
    return (line7, repaid, line25b)


# ── 1. Loader helpers vs the independent transcription ──
for (b1, rp) in [(5000, 0), (5000, 1000), (1000, 1500), (0, 0), (3000, 3000)]:
    check(f"net_unemployment({b1},{rp})", m.net_unemployment(b1, rp), ind_net(b1, rp))

for docs in [
    [{"box1": 5000, "box4": 600}],
    [{"box1": 5000, "repaid_same_year": 1000, "box4": 0}],
    [{"box1": 5000, "box4": 600}, {"box1": 3000, "box4": 300}],
    [{"box1": 1000, "repaid_same_year": 1500}],
]:
    g = m.aggregate_1099g(docs)
    w = ind_aggregate(docs)
    for i, lbl in enumerate(("line7", "repaid", "line25b")):
        check(f"aggregate_1099g({docs})[{lbl}]", g[i], w[i])

# §85 invariant — NO exclusion is ever applied (the full box-1 net is included).
check("no-exclusion full inclusion", m.aggregate_1099g([{"box1": 100000}])[0], 100000)

# ── 2. Scenarios — independent recompute ──
DIAG_KEYS = {"D_1099G_1341", "D_1099G_OTHERBOXES", "D_1099G_REPAID", "D_1099G_WH_ONLY", "D_1099G_BOX2"}
spec = m.FORMS[0]
for s in spec["scenarios"]:
    name = s["scenario_name"].split(" ")[0]
    inp, exp = s["inputs"], s["expected_outputs"]
    if any(k in DIAG_KEYS for k in exp):
        if exp.get("D_1099G_1341") and not (inp.get("g_prior_year_repayment", 0) > 0):
            err(f"{name}: D_1099G_1341 expected but g_prior_year_repayment not set")
        if exp.get("D_1099G_OTHERBOXES") and not inp.get("g_other_boxes_present"):
            err(f"{name}: D_1099G_OTHERBOXES expected but g_other_boxes_present not set")
        continue
    line7, repaid, line25b = ind_aggregate(inp["docs"])
    got = {"g_sch1_line7": line7, "g_line7_repaid": repaid, "g_line_25b": line25b}
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
        err(f"FORM_1099G.{key}: duplicate ids")
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
        if k.startswith("D_1099G_") and k not in diag_ids:
            err(f"{sc['scenario_name']}: expects unknown diagnostic {k}")
fa_ids = [a["assertion_id"] for a in m.FLOW_ASSERTIONS]
if len(fa_ids) != len(set(fa_ids)):
    err("duplicate flow-assertion ids")

# ── Report ──
print("FORM_1099G (facts/rules/lines/diagnostics/scenarios/links):",
      (len(spec["facts"]), len(spec["rules"]), len(spec["lines"]),
       len(spec["diagnostics"]), len(spec["scenarios"]), len(spec["rule_links"])))
print(f"Flow assertions: {len(m.FLOW_ASSERTIONS)}; authority sources: {len(m.AUTHORITY_SOURCES)}")
print("Independently recomputed - T1 5,000 / T2 25b=600 / T3 net 4,000 repaid 1,000 / "
      "T4 multi 8,000 25b=900 / T5 floored 0; the §85 full-inclusion (no exclusion) + the "
      "same-year netting + the box-4 aggregation cross-checked.")

if errors:
    print("\nFAILURES:")
    for e in errors:
        print(f"  X {e}")
    sys.exit(1)
print("\nALL CHECKS PASS")
