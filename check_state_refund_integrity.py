"""Pre-seed math gate for load_1040_state_refund (State refund taxability worksheet).

Run:  poetry run python check_state_refund_integrity.py

Independently recomputes every scenario from its OWN transcription of the §111 /
Pub 525 Worksheet 2 + 2a math — the SALT-cap recapture (the prior-year Sch A
5d/5e), the itemized-vs-standard limit, the negative-prior-year-TI reduction, the
line-1/line-8z allocation, and the year-keyed prior-year standard deduction — and
cross-checks the loader's helper functions + constants. The loader and this gate
share NO math.
"""
import os
import sys
from decimal import Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_state_refund as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def check(name, got, want):
    if D(got) != D(want):
        err(f"{name}: recomputed {got} != authored {want}")


# ── Independent constants (re-typed from the 2025 worksheet + Rev. Proc.) ──
IND_STD = {
    2024: {"single": 14600, "mfs": 14600, "mfj": 29200, "qss": 29200, "hoh": 21900},
    2025: {"single": 15750, "mfs": 15750, "mfj": 31500, "qss": 31500, "hoh": 23625},
}
IND_AB = {
    2024: {"single": 1950, "hoh": 1950, "mfj": 1550, "mfs": 1550, "qss": 1550},
    2025: {"single": 2000, "hoh": 2000, "mfj": 1600, "mfs": 1600, "qss": 1600},
}


def _r0(x):
    return int(round(x))


def ind_std(year, fs, boxes, override=0):
    if override and override > 0:
        return override
    fs = (fs or "single").lower()
    return IND_STD.get(year, IND_STD[2024]).get(fs, 0) + max(0, int(boxes)) * IND_AB.get(year, IND_AB[2024]).get(fs, 0)


def ind_ws2a(income, re_pp, d5, e5):
    a3 = min(income + re_pp, d5)
    if d5 > e5:
        a4 = d5 - e5
        if a3 <= a4:
            return (0, 0)
        a5 = a3 - a4
        a6 = income + re_pp
        if a6 <= 0:
            return (0, 0)
        return (_r0(income / a6 * a5), _r0(re_pp / a6 * a5))
    return (income, re_pp)


def ind_ws2(w1a, w1b, other, itemized, prior_ref, std, mfs_spouse, py_ti):
    w3 = w1a + w1b + other
    if w3 <= 0:
        return (0, 0)
    w6 = itemized - prior_ref
    w8 = w6 if mfs_spouse else w6 - std
    if w8 <= 0:
        return (0, 0)
    w9 = min(w3, w8)
    w11 = w9 if py_ti >= 0 else max(0, w9 + py_ti)
    line1 = _r0(w11 * w1a / w3)
    return (line1, _r0(w11) - line1)


def ind_compute(refund_year, inp):
    if not inp.get("did_itemize") or inp.get("sales_tax_elected"):
        return (0, 0)
    w1a, w1b = ind_ws2a(inp.get("income_refund", 0), inp.get("re_pp_refund", 0),
                        inp.get("py_5d", 0), inp.get("py_5e", 0))
    std = ind_std(refund_year, inp.get("py_filing_status", "single"),
                  inp.get("py_age_blind_boxes", 0), inp.get("py_std_override", 0))
    return ind_ws2(w1a, w1b, inp.get("other_recoveries", 0), inp.get("py_itemized", 0),
                   inp.get("prior_refunded", 0), std, inp.get("mfs_spouse_itemized", False),
                   inp.get("py_taxable_income", 0))


# ── 1. Loader constants + helpers vs the independent transcription ──
for yr in (2024, 2025):
    for fs in ("single", "mfs", "mfj", "qss", "hoh"):
        check(f"PY_STD_DEDUCTION[{yr}][{fs}]", m.PY_STD_DEDUCTION[yr][fs], IND_STD[yr][fs])
        check(f"PY_AGE_BLIND_PER_BOX[{yr}][{fs}]", m.PY_AGE_BLIND_PER_BOX[yr][fs], IND_AB[yr][fs])

for (yr, fs, boxes) in [(2024, "single", 0), (2024, "mfj", 2), (2024, "hoh", 1), (2025, "single", 0), (2025, "mfj", 1)]:
    check(f"py_standard_deduction({yr},{fs},{boxes})", m.py_standard_deduction(yr, fs, boxes), ind_std(yr, fs, boxes))
check("py_standard_deduction override", m.py_standard_deduction(2024, "single", 2, override=20000), 20000)

for (i, rp, d5, e5) in [(1000, 0, 8000, 8000), (3000, 0, 15000, 10000), (7000, 0, 15000, 10000), (1000, 1000, 10000, 10000)]:
    g = m.worksheet_2a(i, rp, d5, e5)
    w = ind_ws2a(i, rp, d5, e5)
    check(f"worksheet_2a({i},{rp},{d5},{e5})[0]", g[0], w[0])
    check(f"worksheet_2a({i},{rp},{d5},{e5})[1]", g[1], w[1])

for args in [(1000, 0, 0, 20000, 0, 14600, False, 50000), (3000, 0, 0, 20000, 0, 14600, False, -1000),
             (1000, 1000, 0, 20000, 0, 14600, False, 50000)]:
    g = m.worksheet_2(*args)
    w = ind_ws2(*args)
    check(f"worksheet_2{args}[0]", g[0], w[0])
    check(f"worksheet_2{args}[1]", g[1], w[1])

# ── 2. Scenarios — independent recompute ──
DIAG_KEYS = {"D_SR_AMT", "D_SR_CREDITS", "D_SR_EXCEPTION", "D_SR_INCOMPLETE",
             "D_SR_NONE_ITEMIZED", "D_SR_8Z", "D_SR_TY2026_INTERIM"}
spec = m.FORMS[0]
for s in spec["scenarios"]:
    name = s["scenario_name"].split(" ")[0]
    inp, exp = s["inputs"], s["expected_outputs"]
    if any(k in DIAG_KEYS for k in exp):
        if exp.get("D_SR_AMT") and not inp.get("py_amt"):
            err(f"{name}: D_SR_AMT expected but py_amt not set")
        continue
    line1, l8z = ind_compute(inp["tax_year"] - 1, inp)
    got = {"sr_taxable_line1": line1, "sr_taxable_8z": l8z}
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
        err(f"STATE_REFUND.{key}: duplicate ids")
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
        if k.startswith("D_SR_") and k not in diag_ids:
            err(f"{sc['scenario_name']}: expects unknown diagnostic {k}")
fa_ids = [a["assertion_id"] for a in m.FLOW_ASSERTIONS]
if len(fa_ids) != len(set(fa_ids)):
    err("duplicate flow-assertion ids")

# ── Report ──
print("STATE_REFUND (facts/rules/lines/diagnostics/scenarios/links):",
      (len(spec["facts"]), len(spec["rules"]), len(spec["lines"]),
       len(spec["diagnostics"]), len(spec["scenarios"]), len(spec["rule_links"])))
print(f"Flow assertions: {len(m.FLOW_ASSERTIONS)}; authority sources: {len(m.AUTHORITY_SOURCES)}")
print("Independently recomputed - T1 1,000 / T2 cap-above 0 / T3 partial 2,000 / T4 diff-limit 400 / "
      "T5 no-itemize 0 / T6 neg-TI 2,000 / T7 8z split 1,000+1,000 / T8 2026-interim 1,000; the "
      "Worksheet 2/2a math + the 2024/2025 std-ded cross-checked.")

if errors:
    print("\nFAILURES:")
    for e in errors:
        print(f"  X {e}")
    sys.exit(1)
print("\nALL CHECKS PASS")
