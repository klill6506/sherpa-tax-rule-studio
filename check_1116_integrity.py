"""Pre-seed math gate for load_1040_form_1116 (Foreign Tax Credit §901/§904).

Run:  poetry run python check_1116_integrity.py

Independently recomputes every scenario from its OWN transcription of the §904(j)
election, the Part I deduction apportionment, and the §904 limitation (L21 = L20 ×
L17/L18, L24 = min(L14, L23)). The loader and this gate share NO math.
"""
import os
import sys
from decimal import ROUND_HALF_UP, Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_form_1116 as m  # noqa: E402

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


# ── Independent constants (re-typed) ──
IND_CEIL, IND_CEIL_MFJ = 300, 600
IND_GAIN_CEIL = 20000
IND_TI = {
    2025: {"mfj": 394600, "qss": 394600, "single": 197300, "mfs": 197300, "hoh": 197300},
    2026: {"mfj": 403500, "qss": 403500, "single": 201750, "mfs": 201750, "hoh": 201750},
}


def ind_ti(year, fs):
    t = IND_TI.get(int(year)) or IND_TI[2026]
    return D(t.get((fs or "single").lower(), t["single"]))


def ind_ceiling(fs):
    return IND_CEIL_MFJ if (fs or "single").lower() in ("mfj", "qss") else IND_CEIL


def ind_defer(category="passive", has_form_2555=False, foreign_qd=0, foreign_net_cap_gain=0,
              tax_year=2025, filing_status="single", taxable_income=0, **_):
    reasons = []
    if (category or "passive").lower() != "passive":
        reasons.append("non_passive_category")
    pref = D(foreign_qd) + D(foreign_net_cap_gain)
    if pref > 0 and not (D(taxable_income) <= ind_ti(tax_year, filing_status) and pref < IND_GAIN_CEIL):
        reasons.append("qd_adjustment_above_exception")
    if has_form_2555:
        reasons.append("form_2555_reduction")
    return reasons


def ind_compute(tax_year=2025, filing_status="single", elect_simplified=False, foreign_tax_total=0,
                regular_tax=0, foreign_source_income=0, definitely_related=0, deduction_apportion=0,
                other_deductions=0, gross_income_all=0, gross_foreign_source=0, home_mortgage_interest=0,
                other_interest=0, foreign_losses=0, carryover=0, taxable_income=0, senior_deduction=0,
                **gates):
    if ind_defer(tax_year=tax_year, filing_status=filing_status, taxable_income=taxable_income, **gates):
        return {"credit": None, "carryforward": D(0)}
    ceil = ind_ceiling(filing_status)
    if elect_simplified:
        if D(foreign_tax_total) > ceil:
            return {"credit": None, "carryforward": D(0)}
        c = min(D(foreign_tax_total), D(regular_tax))
        return {"l35": c, "credit": c, "carryforward": D(0)}
    # full Passive limitation
    l3c = D(deduction_apportion) + D(other_deductions)
    l3d = D(gross_foreign_source or foreign_source_income)
    l3e = D(gross_income_all)
    l3f = (l3d / l3e).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP) if l3e > 0 else D(0)
    l3g = D(r0(l3c * l3f))
    l6 = D(definitely_related) + l3g + D(home_mortgage_interest) + D(other_interest) + D(foreign_losses)
    l7 = D(foreign_source_income) - l6
    l14 = D(foreign_tax_total) + D(carryover)
    l17 = l7
    l18 = max(D(0), D(taxable_income) + D(senior_deduction))
    if l17 <= 0 or l18 <= 0:
        l19 = D(0)
    elif l17 > l18:
        l19 = D(1)
    else:
        l19 = (l17 / l18).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    l20 = D(regular_tax)
    l21 = D(r0(l20 * l19))
    l24 = min(l14, l21)
    l33 = min(l20, l24)
    return {"l7": l7, "l14": l14, "l18": l18, "l19": l19, "l21": l21, "l24": l24,
            "l35": l33, "credit": l33, "carryforward": max(D(0), l14 - l24)}


# ── 1. Loader constants vs the independent transcription ──
check("ELECT_CEILING", m.ELECT_CEILING, IND_CEIL)
check("ELECT_CEILING_MFJ", m.ELECT_CEILING_MFJ, IND_CEIL_MFJ)
check("ADJ_EXCEPTION_GAIN_CEILING", m.ADJ_EXCEPTION_GAIN_CEILING, IND_GAIN_CEIL)
for yr in (2025, 2026):
    for fs in ("mfj", "single", "mfs", "hoh", "qss"):
        check(f"ADJ_EXCEPTION_TI[{yr}][{fs}]", m.adj_exception_ti(yr, fs), IND_TI[yr][fs])

# ── 2. Scenarios — independent recompute + cross-check the loader ──
DIAG_KEYS = {d["diagnostic_id"] for d in m.FORMS[0]["diagnostics"]}
OUT_MAP = {"f1116_line7": "l7", "f1116_line24": "l24", "f1116_line35": "credit",
           "f1116_carryforward": "carryforward"}
spec = m.FORMS[0]
for s in spec["scenarios"]:
    name = s["scenario_name"].split(" ")[0]
    inp = {k: v for k, v in s["inputs"].items()}
    exp = s["expected_outputs"]
    diag_expected = {k for k in exp if k in DIAG_KEYS}
    if diag_expected:
        # verify the diagnostic condition independently
        fs = inp.get("filing_status", "single")
        if "D_1116_002" in diag_expected:
            if not (inp.get("elect_simplified") and D(inp.get("foreign_tax_total", 0)) > ind_ceiling(fs)):
                err(f"{name}: D_1116_002 expected but election not over ceiling")
        if "D_1116_001" in diag_expected:
            tot = D(inp.get("foreign_tax_total", 0))
            if not (0 < tot <= ind_ceiling(fs)):
                err(f"{name}: D_1116_001 expected but foreign tax not within ceiling")
        if "D_1116_003" in diag_expected and "non_passive_category" not in ind_defer(**{k: v for k, v in inp.items() if k != "tax_year"}, tax_year=inp.get("tax_year", 2025)):
            err(f"{name}: D_1116_003 expected but category is passive")
        if "D_1116_004" in diag_expected and "qd_adjustment_above_exception" not in ind_defer(**{k: v for k, v in inp.items() if k != "tax_year"}, tax_year=inp.get("tax_year", 2025)):
            err(f"{name}: D_1116_004 expected but adjustment exception holds")
        if "D_1116_005" in diag_expected and D(inp.get("carryover", 0)) <= 0:
            err(f"{name}: D_1116_005 expected but no carryover")
        continue
    got = ind_compute(**inp)
    gl = m.compute_1116(**inp)
    for k, want in exp.items():
        if k in DIAG_KEYS:
            continue
        if k not in OUT_MAP:
            err(f"{name}.{k}: no independent recompute mapped")
            continue
        check(f"{name}.{k} (ind)", got.get(OUT_MAP[k]), want)
        check(f"{name}.{k} (loader)", gl.get(OUT_MAP[k]), want)

# ── 3. Structural checks ──
known_sources = {s["source_code"] for s in m.AUTHORITY_SOURCES} | set(m.EXISTING_SOURCES_TO_REFERENCE)
for key, idk in (("facts", "fact_key"), ("rules", "rule_id"), ("lines", "line_number"),
                 ("diagnostics", "diagnostic_id"), ("scenarios", "scenario_name")):
    ids = [x[idk] for x in spec[key]]
    if len(ids) != len(set(ids)):
        err(f"FORM_1116.{key}: duplicate ids")
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
        if k.startswith("D_1116_") and k not in diag_ids:
            err(f"{sc['scenario_name']}: expects unknown diagnostic {k}")
fa_ids = [a["assertion_id"] for a in m.FLOW_ASSERTIONS]
if len(fa_ids) != len(set(fa_ids)):
    err("duplicate flow-assertion ids")

# ── Report ──
print("FORM_1116 (facts/rules/lines/diagnostics/scenarios/links):",
      (len(spec["facts"]), len(spec["rules"]), len(spec["lines"]),
       len(spec["diagnostics"]), len(spec["scenarios"]), len(spec["rule_links"])))
print(f"Flow assertions: {len(m.FLOW_ASSERTIONS)}; authority sources: {len(m.AUTHORITY_SOURCES)}")
print("Independently recomputed - T1 election 250 / T2 MFJ 550 / T4 limit-binds 1361 cf 139 / "
      "T5 full-credit 1000 cf 0 / T8 L17<=0 -> 0 cf 200; the 904(j) ceilings + the 904 "
      "limitation (L21 = L20 x L17/L18, L24 = min(L14,L23)) cross-checked.")

if errors:
    print("\nFAILURES:")
    for e in errors:
        print(f"  X {e}")
    sys.exit(1)
print("\nALL CHECKS PASS")
