"""Pre-seed math gate for load_1040_minister (Minister/Clergy §107 / §1402).

Run:  poetry run python check_minister_integrity.py

Independently re-types the clergy worksheet — the §107 least-of-three income-tax
exclusion + the taxable excess (→ Form 1040 line 1h), and the §1402(a)(8) clergy
net SE earnings (→ Schedule SE line 2, pre-0.9235; Form 4361 zeroes it) — and
cross-checks the loader's compute_minister helper + every scenario + every
diagnostic condition. The loader and this gate share NO math.
"""
import os
import sys
from decimal import ROUND_HALF_UP, Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_minister as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def rnd(x):
    return D(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def check(name, got, want):
    if D(got) != D(want):
        err(f"{name}: recomputed {got} != authored {want}")


# ── Independent math (re-typed; shares nothing with the loader) ──
def ind_minister(wages=0, housing_allowance=0, housing_used=0, housing_frv=0,
                 parsonage_frv=0, unreimbursed_expenses=0, form_4361_exempt=False):
    w = D(wages)
    ha = D(housing_allowance)
    hu = D(housing_used)
    hf = D(housing_frv)
    pf = D(parsonage_frv)
    ue = D(unreimbursed_expenses)

    incomplete = ha > 0 and (hu <= 0 or hf <= 0)
    if ha <= 0 or incomplete:
        excl = D(0)
    else:
        # least-of-three without using min() — independent transcription
        excl = ha
        if hu < excl:
            excl = hu
        if hf < excl:
            excl = hf
    excess = ha - excl
    if excess < 0:
        excess = D(0)

    se = w + ha + pf - ue
    if se < 0:
        se = D(0)
    if form_4361_exempt:
        se = D(0)

    return {"line5_exclusion": rnd(excl), "line6_excess": rnd(excess),
            "line9_se_line2": rnd(se), "housing_incomplete": incomplete}


# Independent diagnostic conditions.
def ind_diags(inp, lines):
    fired = set()
    ha = D(inp.get("housing_allowance", 0))
    hu = D(inp.get("housing_used", 0))
    hf = D(inp.get("housing_frv", 0))
    pf = D(inp.get("parsonage_frv", 0))
    ue = D(inp.get("unreimbursed_expenses", 0))
    exempt = bool(inp.get("form_4361_exempt"))
    excl = D(lines.get("line5_exclusion", 0))
    excess = D(lines.get("line6_excess", 0))
    se = D(lines.get("line9_se_line2", 0))
    if ha > 0 and (hu <= 0 or hf <= 0):
        fired.add("D_MIN_HOUSING_INC")
    if excess > 0:
        fired.add("D_MIN_EXCESS")
    if exempt:
        fired.add("D_MIN_4361")
    if se > 0 and not exempt:
        fired.add("D_MIN_SECA")
    if excl > 0 or pf > 0:
        fired.add("D_MIN_REASONABLE")
    if ue > 0 and (excl > 0 or pf > 0):
        fired.add("D_MIN_DEASON")
    return fired


# ── 1. Loader helper vs the independent transcription ──
HELPER_CASES = [
    dict(wages=40000, housing_allowance=20000, housing_used=20000, housing_frv=22000),
    dict(wages=40000, housing_allowance=25000, housing_used=20000, housing_frv=22000),
    dict(wages=35000, parsonage_frv=18000),
    dict(wages=40000, housing_allowance=20000, housing_used=20000, housing_frv=25000, form_4361_exempt=True),
    dict(wages=50000, housing_allowance=24000, housing_used=24000, housing_frv=26000, unreimbursed_expenses=4000),
    dict(wages=40000, housing_allowance=18000, housing_used=0, housing_frv=0),
    # extra edges: expenses drive the SE base negative → floor 0; designated below FRV/used
    dict(wages=2000, housing_allowance=1000, housing_used=1000, housing_frv=5000, unreimbursed_expenses=9000),
    dict(wages=30000, housing_allowance=15000, housing_used=18000, housing_frv=16000),
]
for kw in HELPER_CASES:
    g = m.compute_minister(**kw)
    w = ind_minister(**kw)
    for k in w:
        if k not in g:
            err(f"compute_minister({kw}): missing key {k}")
        elif k == "housing_incomplete":
            if bool(g[k]) != bool(w[k]):
                err(f"compute_minister({kw}).{k}: recomputed {g[k]} != authored {w[k]}")
        else:
            check(f"compute_minister({kw}).{k}", g[k], w[k])

# ── 2. Scenarios — independent recompute + diagnostics ──
DIAG_KEYS = {d["diagnostic_id"] for d in m.FORMS[0]["diagnostics"]}
OUT_MAP = {"min_housing_exclusion": "line5_exclusion", "min_excess_allowance": "line6_excess",
           "min_se_line2": "line9_se_line2"}
spec = m.FORMS[0]
for s in spec["scenarios"]:
    name = s["scenario_name"].split(" ")[0]
    inp = {k: v for k, v in s["inputs"].items() if k != "tax_year"}
    exp = s["expected_outputs"]
    got = ind_minister(**inp)
    fired = ind_diags(inp, got)
    for k, want in exp.items():
        if k in DIAG_KEYS:
            if want and k not in fired:
                err(f"{name}: expected diagnostic {k} but the independent condition did not fire")
            continue
        if k not in OUT_MAP:
            err(f"{name}.{k}: no independent recompute mapped")
            continue
        check(f"{name}.{k}", got[OUT_MAP[k]], want)

# ── 3. Structural checks ──
known_sources = {s["source_code"] for s in m.AUTHORITY_SOURCES} | set(m.EXISTING_SOURCES_TO_REFERENCE)
for key, idk in (("facts", "fact_key"), ("rules", "rule_id"), ("lines", "line_number"),
                 ("diagnostics", "diagnostic_id"), ("scenarios", "scenario_name")):
    ids = [x[idk] for x in spec[key]]
    if len(ids) != len(set(ids)):
        err(f"MINISTER.{key}: duplicate ids")
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
for sc in spec["scenarios"]:
    for k in sc["expected_outputs"]:
        if k.startswith("D_MIN_") and k not in DIAG_KEYS:
            err(f"{sc['scenario_name']}: expects unknown diagnostic {k}")
fa_ids = [a["assertion_id"] for a in m.FLOW_ASSERTIONS]
if len(fa_ids) != len(set(fa_ids)):
    err("duplicate flow-assertion ids")
# every flow-assertion form is MINISTER
for a in m.FLOW_ASSERTIONS:
    if a["definition"].get("form") != "MINISTER":
        err(f"flow assertion {a['assertion_id']} not bound to MINISTER")

# ── Report ──
print("MINISTER (facts/rules/lines/diagnostics/scenarios/links):",
      (len(spec["facts"]), len(spec["rules"]), len(spec["lines"]),
       len(spec["diagnostics"]), len(spec["scenarios"]), len(spec["rule_links"])))
print(f"Flow assertions: {len(m.FLOW_ASSERTIONS)}; authority sources: {len(m.AUTHORITY_SOURCES)}")
print("Independently recomputed — T1 excl 20k/excess 0/SE 60k; T2 excess 5k/SE 65k; "
      "T3 parsonage SE 53k; T4 4361 SE 0; T5 expenses SE 70k; T6 incomplete RED excl 0/SE 58k; "
      "+ negative-floor + below-FRV edges; the 6 diagnostic conditions cross-checked.")

if errors:
    print("\nFAILURES:")
    for e in errors:
        print(f"  X {e}")
    sys.exit(1)
print("\nALL CHECKS PASS")
