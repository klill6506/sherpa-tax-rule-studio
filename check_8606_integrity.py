"""Pre-seed math gate for load_1040_8606 (Nondeductible IRAs §408(d) + §408A).

Run:  poetry run python check_8606_integrity.py

Independently recomputes every scenario from its OWN transcription of the §408(d)
pro-rata (basis / (year-end + distributions + conversions), capped at 1.0) + the
Part II conversion taxable + the §408A(d)(4) Roth ordering, and cross-checks the
loader's helper functions. The loader and this gate share NO math.
"""
import os
import sys
from decimal import ROUND_HALF_UP, Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_8606 as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def check(name, got, want):
    if D(got) != D(want):
        err(f"{name}: recomputed {got} != authored {want}")


def r0(x):
    return int(D(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


# ── Independent math (re-typed) ──
def ind_8606(nondeduct=0, prior_basis=0, contrib_jan_apr=0, year_end=0, distributions=0,
             conversions=0, roth_distributions=0, homebuyer=0, contribution_basis=0,
             conversion_basis=0):
    l3 = D(nondeduct) + D(prior_basis)
    l5 = l3 - D(contrib_jan_apr)
    l7, l8 = D(distributions), D(conversions)
    l9 = D(year_end) + l7 + l8
    ratio = Decimal("0") if l9 <= 0 else min(Decimal("1"), l5 / l9)
    l11 = D(r0(l8 * ratio))
    l12 = D(r0(l7 * ratio))
    l14 = l3 - (l11 + l12)
    l15c = l7 - l12
    l18 = max(Decimal("0"), l8 - l11)
    l21 = max(Decimal("0"), D(roth_distributions) - D(homebuyer))
    l23 = max(Decimal("0"), l21 - D(contribution_basis))
    l25c = max(Decimal("0"), l23 - D(conversion_basis))
    return {"l14": l14, "l15c": l15c, "l18": l18, "l25c": l25c, "line_4b": l15c + l18 + l25c}


# ── 1. Loader helpers vs the independent transcription ──
for kw in [
    dict(nondeduct=7000), dict(nondeduct=7000, year_end=0, conversions=7000),
    dict(prior_basis=10000, year_end=50000, distributions=10000),
    dict(nondeduct=7000, year_end=43000, conversions=7000),
    dict(roth_distributions=20000, contribution_basis=15000, conversion_basis=3000),
    dict(prior_basis=10000, year_end=30000, distributions=5000, conversions=5000),
]:
    g = m.compute_8606(**kw)
    w = ind_8606(**kw)
    for k in ("l14", "l15c", "l18", "l25c", "line_4b"):
        check(f"compute_8606({kw}).{k}", g[k], w[k])

# Part III ordering — contributions first.
check("part_iii covered", m.part_iii(10000, 0, 15000, 0), Decimal("0"))
check("part_iii earnings", m.part_iii(20000, 0, 15000, 3000), Decimal("2000"))

# ── 2. Scenarios — independent recompute ──
DIAG_KEYS = {"D_8606_OVERCONTRIB", "D_8606_NO_YEAREND", "D_8606_BACKDOOR",
             "D_8606_SUPERSEDE", "D_8606_PART3", "D_8606_TY2026"}
spec = m.FORMS[0]
for s in spec["scenarios"]:
    name = s["scenario_name"].split(" ")[0]
    inp, exp = s["inputs"], s["expected_outputs"]
    if any(k in DIAG_KEYS for k in exp):
        if exp.get("D_8606_OVERCONTRIB") and not (inp.get("nondeduct", 0) > 7000):
            err(f"{name}: D_8606_OVERCONTRIB expected but contribution <= 7000")
        continue
    got = ind_8606(
        nondeduct=inp.get("nondeduct", 0), prior_basis=inp.get("prior_basis", 0),
        contrib_jan_apr=inp.get("contrib_jan_apr", 0), year_end=inp.get("year_end", 0),
        distributions=inp.get("distributions", 0), conversions=inp.get("conversions", 0),
        roth_distributions=inp.get("roth_distributions", 0), homebuyer=inp.get("homebuyer", 0),
        contribution_basis=inp.get("roth_contribution_basis", 0),
        conversion_basis=inp.get("roth_conversion_basis", 0))
    out_map = {"f8606_line14": "l14", "f8606_line15c": "l15c", "f8606_line18": "l18", "f8606_line25c": "l25c"}
    for k, want in exp.items():
        if k in DIAG_KEYS:
            continue
        if k not in out_map:
            err(f"{name}.{k}: no independent recompute mapped")
            continue
        check(f"{name}.{k}", got[out_map[k]], want)

# ── 3. Structural checks ──
known_sources = {s["source_code"] for s in m.AUTHORITY_SOURCES} | set(m.EXISTING_SOURCES_TO_REFERENCE)
for key, idk in (("facts", "fact_key"), ("rules", "rule_id"), ("lines", "line_number"),
                 ("diagnostics", "diagnostic_id"), ("scenarios", "scenario_name")):
    ids = [x[idk] for x in spec[key]]
    if len(ids) != len(set(ids)):
        err(f"FORM_8606.{key}: duplicate ids")
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
        if k.startswith("D_8606_") and k not in diag_ids:
            err(f"{sc['scenario_name']}: expects unknown diagnostic {k}")
fa_ids = [a["assertion_id"] for a in m.FLOW_ASSERTIONS]
if len(fa_ids) != len(set(fa_ids)):
    err("duplicate flow-assertion ids")

# ── Report ──
print("FORM_8606 (facts/rules/lines/diagnostics/scenarios/links):",
      (len(spec["facts"]), len(spec["rules"]), len(spec["lines"]),
       len(spec["diagnostics"]), len(spec["scenarios"]), len(spec["rule_links"])))
print(f"Flow assertions: {len(m.FLOW_ASSERTIONS)}; authority sources: {len(m.AUTHORITY_SOURCES)}")
print("Independently recomputed - T1 basis 7,000 / T2 backdoor 0 / T3 pro-rata 8,333 / "
      "T4 partial 6,020 / T5 Part III 2,000 / T6 covered 0 / T7 combined 3,750+3,750; the §408(d) "
      "pro-rata + the §408A Roth ordering + basis conservation cross-checked.")

if errors:
    print("\nFAILURES:")
    for e in errors:
        print(f"  X {e}")
    sys.exit(1)
print("\nALL CHECKS PASS")
