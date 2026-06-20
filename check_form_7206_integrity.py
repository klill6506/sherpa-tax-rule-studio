"""Pre-seed math gate for load_1040_form_7206 (Self-Employed Health Insurance §162(l)).

Run:  poetry run python check_form_7206_integrity.py

Independently re-types Form 7206 (2025) — the two earned-income limit paths (Sch C
lines 4-10 with the apportioned ½-SE-tax + SEP; the S-corp Box-5 line 11) and the
smaller-of (line 14) → Schedule 1 line 17 — and cross-checks the loader's helper +
every scenario + every diagnostic condition. The loader and this gate share NO math.
"""
import os
import sys
from decimal import ROUND_HALF_UP, Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_form_7206 as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def check(name, got, want):
    if D(got) != D(want):
        err(f"{name}: recomputed {got} != authored {want}")


# ── Independent math (re-typed; shares nothing with the loader) ──
def rnd(x):
    return D(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def ind_7206(premiums=0, ltc=0, is_scorp=False, net_profit=0, all_net_profits=0,
             half_se_tax=0, sep_attributable=0, scorp_box5=0, form2555=0):
    l3 = D(premiums) + D(ltc)
    if is_scorp:
        l11 = D(scorp_box5)
        l13 = l11 - D(form2555)
        l14 = rnd(min(l3, max(D(0), l13)))
        return {"line3": l3, "line11": l11, "line13": l13, "line14": l14}
    l4 = D(net_profit)
    l5 = D(all_net_profits)
    l6 = (l4 / l5) if l5 > 0 else D(0)
    l7 = rnd(D(half_se_tax) * l6)
    l8 = l4 - l7
    l10 = l8 - D(sep_attributable)
    l13 = l10 - D(form2555)
    l14 = rnd(min(l3, max(D(0), l13)))
    return {"line3": l3, "line4": l4, "line6": l6, "line7": l7, "line8": l8,
            "line10": l10, "line13": l13, "line14": l14}


# Independent diagnostic conditions.
def ind_diags(inp, lines):
    fired = set()
    is_scorp = bool(inp.get("is_scorp"))
    prem = D(inp.get("premiums", 0))
    box5 = D(inp.get("scorp_box5", 0))
    if is_scorp and prem > 0 and box5 <= 0:
        fired.add("D_7206_SCORP_NOWAGE")
    if is_scorp and box5 > 0 and prem > box5:
        fired.add("D_7206_SCORP_LIM")
    if not is_scorp and prem > D(lines.get("line10", 0)):
        fired.add("D_7206_SC_LIM")
    return fired


# ── 1. Loader helper vs the independent transcription ──
HELPER_CASES = [
    dict(premiums=8000, is_scorp=True, scorp_box5=60000),
    dict(premiums=15000, is_scorp=True, scorp_box5=10000),
    dict(premiums=5000, is_scorp=True, scorp_box5=0),
    dict(premiums=6000, net_profit=50000, all_net_profits=50000, half_se_tax=4000),
    dict(premiums=6000, net_profit=5000, all_net_profits=5000, half_se_tax=700),
    dict(premiums=6000, net_profit=50000, all_net_profits=50000, half_se_tax=4000, sep_attributable=44000),
    dict(premiums=9500, net_profit=10000, all_net_profits=50000, half_se_tax=5000),
]
for kw in HELPER_CASES:
    g = m.compute_7206(**kw)
    w = ind_7206(**kw)
    for k in w:
        if k in g:
            check(f"compute_7206({kw}).{k}", g[k], w[k])

# ── 2. Scenarios — independent recompute + diagnostics ──
DIAG_KEYS = {d["diagnostic_id"] for d in m.FORMS[0]["diagnostics"]}
OUT_MAP = {"f7206_line3": "line3", "f7206_line6": "line6", "f7206_line7": "line7",
           "f7206_line10": "line10", "f7206_line13": "line13", "f7206_line14": "line14"}
spec = m.FORMS[0]
for s in spec["scenarios"]:
    name = s["scenario_name"].split(" ")[0]
    inp = {k: v for k, v in s["inputs"].items() if k != "tax_year"}
    exp = s["expected_outputs"]
    got = ind_7206(**inp)
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
        err(f"FORM_7206.{key}: duplicate ids")
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
        if k.startswith("D_7206_") and k not in DIAG_KEYS:
            err(f"{sc['scenario_name']}: expects unknown diagnostic {k}")
fa_ids = [a["assertion_id"] for a in m.FLOW_ASSERTIONS]
if len(fa_ids) != len(set(fa_ids)):
    err("duplicate flow-assertion ids")

# ── Report ──
print("FORM_7206 (facts/rules/lines/diagnostics/scenarios/links):",
      (len(spec["facts"]), len(spec["rules"]), len(spec["lines"]),
       len(spec["diagnostics"]), len(spec["scenarios"]), len(spec["rule_links"])))
print(f"Flow assertions: {len(m.FLOW_ASSERTIONS)}; authority sources: {len(m.AUTHORITY_SOURCES)}")
print("Independently recomputed — S-corp: T1 full 8000 / T2 limited-to-Box5 10000 / T3 no-wage 0 / "
      "T4 LTC 5000; Sch C: T5 full 6000 / T6 fix-binds 4300 / T7 SEP 2000 / T8 apportion 9000; "
      "the smaller-of + both earned-income limits + the 3 limit diagnostics cross-checked.")

if errors:
    print("\nFAILURES:")
    for e in errors:
        print(f"  X {e}")
    sys.exit(1)
print("\nALL CHECKS PASS")
