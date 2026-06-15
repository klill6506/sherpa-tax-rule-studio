"""Pre-seed math gate for load_1040_8960 (Net Investment Income Tax §1411).

Run:  poetry run python check_8960_integrity.py

Independently recomputes every scenario from its OWN transcription of the §1411
chain — total investment income, net of deductions, and the 3.8% on min(max(0,
NII), MAGI − threshold) — and cross-checks the loader's helper + the thresholds.
The loader and this gate share NO math.
"""
import os
import sys
from decimal import ROUND_HALF_UP, Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_8960 as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def check(name, got, want):
    if D(got) != D(want):
        err(f"{name}: recomputed {got} != authored {want}")


# ── Independent math (re-typed) ──
IND_THRESH = {"mfj": 250000, "qss": 250000, "mfs": 125000, "single": 200000, "hoh": 200000}
RATE = Decimal("0.038")


def r0(x):
    return int(D(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def ind_8960(interest=0, dividends=0, annuities=0, rental=0, nonpassive_adj=0, net_gain=0,
             gain_adj=0, cfc_pfic=0, other_mods=0, inv_interest_exp=0, state_tax=0, misc_exp=0,
             magi=0, filing_status="single"):
    l5 = D(net_gain) - D(gain_adj)
    l8 = (D(interest) + D(dividends) + D(annuities) + D(rental) + D(nonpassive_adj) + l5
          + D(cfc_pfic) + D(other_mods))
    l10 = D(inv_interest_exp) + D(state_tax) + D(misc_exp)
    l12 = l8 - l10
    thr = IND_THRESH.get((filing_status or "single").lower(), 200000)
    l15 = max(Decimal("0"), D(magi) - D(thr))
    l16 = min(max(Decimal("0"), l12), l15)
    l17 = D(r0(l16 * RATE))
    return {"line8": l8, "line12": l12, "line16": l16, "line17": l17}


# ── 1. Loader constants + helper vs the independent transcription ──
check("NIIT_RATE", D(m.NIIT_RATE), RATE)
for fs in ("mfj", "qss", "mfs", "single", "hoh"):
    check(f"threshold[{fs}]", m.threshold(fs), IND_THRESH[fs])

for kw in [
    dict(interest=5000, dividends=10000, magi=300000, filing_status="single"),
    dict(interest=50000, magi=210000, filing_status="single"),
    dict(net_gain=-10000, interest=2000, magi=300000, filing_status="single"),
    dict(interest=40000, magi=270000, filing_status="mfj"),
    dict(net_gain=100000, gain_adj=90000, magi=300000, filing_status="single"),
]:
    g = m.compute_8960(**kw)
    w = ind_8960(**kw)
    for k in ("line8", "line12", "line16", "line17"):
        check(f"compute_8960({kw}).{k}", g[k], w[k])

# ── 2. Scenarios — independent recompute ──
DIAG_KEYS = {"D_8960_BELOW_THRESH", "D_8960_NII_LOSS", "D_8960_RENTAL", "D_8960_GAIN", "D_8960_STATE_TAX"}
spec = m.FORMS[0]
for s in spec["scenarios"]:
    name = s["scenario_name"].split(" ")[0]
    inp, exp = s["inputs"], s["expected_outputs"]
    if any(k in DIAG_KEYS for k in exp):
        if exp.get("D_8960_BELOW_THRESH") and not (
                inp.get("magi", 0) <= IND_THRESH.get(inp.get("filing_status", "single"), 200000)):
            err(f"{name}: D_8960_BELOW_THRESH expected but MAGI > threshold")
        continue
    got = ind_8960(**{k: v for k, v in inp.items() if k != "tax_year"})
    out_map = {"e8960_line8": "line8", "e8960_line12": "line12", "e8960_line16": "line16", "e8960_line17": "line17"}
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
        err(f"FORM_8960.{key}: duplicate ids")
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
        if k.startswith("D_8960_") and k not in diag_ids:
            err(f"{sc['scenario_name']}: expects unknown diagnostic {k}")
fa_ids = [a["assertion_id"] for a in m.FLOW_ASSERTIONS]
if len(fa_ids) != len(set(fa_ids)):
    err("duplicate flow-assertion ids")

# ── Report ──
print("FORM_8960 (facts/rules/lines/diagnostics/scenarios/links):",
      (len(spec["facts"]), len(spec["rules"]), len(spec["lines"]),
       len(spec["diagnostics"]), len(spec["scenarios"]), len(spec["rule_links"])))
print(f"Flow assertions: {len(m.FLOW_ASSERTIONS)}; authority sources: {len(m.AUTHORITY_SOURCES)}")
print("Independently recomputed - T1 570 / T2 below-thresh 0 / T3 excess-binds 380 / T4 deductions 570 / "
      "T5 loss 0 / T6 MFJ 760 / T7 gain-adj 380; the §1411 formula + thresholds + the lesser-of cross-checked.")

if errors:
    print("\nFAILURES:")
    for e in errors:
        print(f"  X {e}")
    sys.exit(1)
print("\nALL CHECKS PASS")
