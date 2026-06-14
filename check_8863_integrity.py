"""Pre-seed math gate for load_1040_form_8863 (Education Credits — AOTC + LLC).

Run:  poetry run python check_8863_integrity.py

Independently recomputes every scenario from its OWN transcription of the §25A /
i8863 math — the per-student AOTC tiers (100% first $2,000 + 25% next $2,000, cap
$4,000), the shared phaseout ((ceiling − MAGI) / divisor, capped 1.000), the LLC
(20% of up to $10,000, max $2,000), the 40% refundable split + the line-7 lockout,
and the Credit Limit Worksheet — and cross-checks the loader's helper functions +
constants cell-by-cell. The loader and this gate share NO math.
"""
import os
import sys
from decimal import Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_form_8863 as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def check(name, got, want):
    if D(got) != D(want):
        err(f"{name}: recomputed {got} != authored {want}")


# ── Independent constants (re-typed from the 2025 f8863 / i8863 / Pub 970) ──
IND_AOTC_TIER1 = 2000
IND_AOTC_TIER2_RATE = 0.25
IND_AOTC_EXP_CAP = 4000
IND_AOTC_MAX = 2500
IND_AOTC_REFUND_RATE = 0.40
IND_AOTC_REFUND_CAP = 1000
IND_LLC_RATE = 0.20
IND_LLC_EXP_CAP = 10000
IND_LLC_MAX = 2000
IND_CEILING = {"other": 90000, "mfj": 180000}
IND_DIVISOR = {"other": 10000, "mfj": 20000}


def _r0(x):
    return int(round(x))


def ind_student_l30(exp):
    l27 = min(exp, IND_AOTC_EXP_CAP)
    l28 = max(0, l27 - IND_AOTC_TIER1)
    l29 = _r0(l28 * IND_AOTC_TIER2_RATE)
    return l27 if l28 == 0 else l29 + IND_AOTC_TIER1


def ind_ratio(magi, fs):
    key = "mfj" if (fs or "").lower() == "mfj" else "other"
    diff = IND_CEILING[key] - magi
    if diff <= 0:
        return 0.0
    if diff >= IND_DIVISOR[key]:
        return 1.0
    return round(diff / IND_DIVISOR[key], 3)


def ind_aotc_part1(sum_l30, magi, fs, lockout):
    ratio = ind_ratio(magi, fs)
    l7 = 0 if ratio <= 0 else _r0(sum_l30 * ratio)
    if lockout:
        return {"l7": l7, "l8": 0, "l9": l7}
    l8 = _r0(l7 * IND_AOTC_REFUND_RATE)
    return {"l7": l7, "l8": l8, "l9": l7 - l8}


def ind_llc_l18(exp, magi, fs):
    if exp <= 0:
        return 0
    l11 = min(exp, IND_LLC_EXP_CAP)
    l12 = _r0(l11 * IND_LLC_RATE)
    ratio = ind_ratio(magi, fs)
    return 0 if ratio <= 0 else _r0(l12 * ratio)


def ind_credit_limit(l18, l9, tax, prior):
    return min(l18 + l9, max(0, tax - prior))


def recompute(inp):
    fs = inp["filing_status"]
    magi = inp.get("magi", 0)
    lockout = inp.get("lockout", False)
    students = inp.get("aotc_students", [])
    sum_l30 = sum(ind_student_l30(e) for e in students)
    p1 = ind_aotc_part1(sum_l30, magi, fs, lockout)
    l18 = ind_llc_l18(inp.get("llc_expenses", 0), magi, fs)
    tax = inp.get("tax", 99999)
    prior = inp.get("prior_credits", 0)
    l19 = ind_credit_limit(l18, p1["l9"], tax, prior)
    return {
        "f8863_total_aotc": p1["l7"],
        "f8863_aotc_refundable": p1["l8"],
        "f8863_aotc_nonref": p1["l9"],
        "f8863_llc": l18,
        "f8863_education_credit": l19,
    }


# ── 1. Loader constants + helpers vs the independent transcription ──
check("AOTC.tier1", m.AOTC["tier1"], IND_AOTC_TIER1)
check("AOTC.max", m.AOTC["max"], IND_AOTC_MAX)
check("AOTC.expense_cap", m.AOTC["expense_cap"], IND_AOTC_EXP_CAP)
check("AOTC.refundable_rate", m.AOTC["refundable_rate"], IND_AOTC_REFUND_RATE)
check("AOTC.refundable_cap", m.AOTC["refundable_cap"], IND_AOTC_REFUND_CAP)
check("AOTC.tier2_rate", m.AOTC["tier2_rate"], IND_AOTC_TIER2_RATE)
check("LLC.rate", m.LLC["rate"], IND_LLC_RATE)
check("LLC.expense_cap", m.LLC["expense_cap"], IND_LLC_EXP_CAP)
check("LLC.max", m.LLC["max"], IND_LLC_MAX)
for key in ("other", "mfj"):
    check(f"PHASEOUT[{key}].ceiling", m.PHASEOUT[key][0], IND_CEILING[key])
    check(f"PHASEOUT[{key}].divisor", m.PHASEOUT[key][1], IND_DIVISOR[key])

# helper agreement at sample points
for exp in (0, 1500, 2000, 3000, 4000, 5000):
    check(f"aotc_student_l30({exp})", m.aotc_student_l30(exp), ind_student_l30(exp))
for (magi, fs) in [(50000, "single"), (85000, "single"), (95000, "single"), (60000, "single"),
                   (170000, "mfj"), (160000, "mfj"), (185000, "mfj"), (80000, "single")]:
    got = m.phaseout_ratio(magi, fs)
    want = ind_ratio(magi, fs)
    if abs(got - want) > 1e-9:
        err(f"phaseout_ratio({magi},{fs}) = {got} != {want}")
for (s, magi, fs, lk) in [(2500, 50000, "single", False), (2500, 85000, "single", False),
                          (2500, 40000, "single", True), (2500, 95000, "single", False)]:
    g = m.aotc_part1(s, magi, fs, lk)
    w = ind_aotc_part1(s, magi, fs, lk)
    for k in ("l7", "l8", "l9"):
        check(f"aotc_part1({s},{magi},{fs},{lk}).{k}", g[k], w[k])
for (exp, magi, fs) in [(8000, 60000, "single"), (12000, 50000, "single"), (10000, 170000, "mfj"), (0, 50000, "single")]:
    check(f"llc_l18({exp},{magi},{fs})", m.llc_l18(exp, magi, fs), ind_llc_l18(exp, magi, fs))
for (l18, l9, tax, prior) in [(0, 1500, 99999, 0), (0, 1500, 800, 0), (1600, 0, 99999, 0), (2000, 500, 1000, 200)]:
    check(f"credit_limit({l18},{l9},{tax},{prior})", m.credit_limit_l19(l18, l9, tax, prior),
          ind_credit_limit(l18, l9, tax, prior))

# ── 2. Scenarios — independent recompute ──
DIAG_KEYS = {"D_8863_MFS", "D_8863_DEPENDENT", "D_8863_DUAL_STUDENT", "D_8863_NO_CREDIT",
             "D_8863_LOCKOUT", "D_8863_AOTC_INELIGIBLE", "D_8863_TY2026_SSN"}
spec = m.FORMS[0]
for s in spec["scenarios"]:
    name = s["scenario_name"].split(" ")[0]
    inp, exp = s["inputs"], s["expected_outputs"]
    if any(k in DIAG_KEYS for k in exp):
        # diagnostic scenario — assert the routing intent, not the numbers
        if exp.get("D_8863_MFS") and (inp.get("filing_status") or "").lower() != "mfs":
            err(f"{name}: D_8863_MFS expected but filing_status != mfs")
        continue
    got = recompute(inp)
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
        err(f"FORM_8863.{key}: duplicate ids")
# rule_id + diagnostic_id varchar(20) guard (the recurring lesson)
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
        if k.startswith("D_8863_") and k not in diag_ids:
            err(f"{sc['scenario_name']}: expects unknown diagnostic {k}")
fa_ids = [a["assertion_id"] for a in m.FLOW_ASSERTIONS]
if len(fa_ids) != len(set(fa_ids)):
    err("duplicate flow-assertion ids")

# ── Report ──
print("FORM_8863 (facts/rules/lines/diagnostics/scenarios/links):",
      (len(spec["facts"]), len(spec["rules"]), len(spec["lines"]),
       len(spec["diagnostics"]), len(spec["scenarios"]), len(spec["rule_links"])))
print(f"Flow assertions: {len(m.FLOW_ASSERTIONS)}; authority sources: {len(m.AUTHORITY_SOURCES)}")
print("Independently recomputed - T1 AOTC 2,500 (ref 1,000 / nonref 1,500) / T2 phaseout 0.500 -> 1,250 / "
      "T3 LLC 1,600 / T4 LLC cap 2,000 / T5 LLC MFJ 0.500 -> 1,000 / T6 lockout ref 0 nonref 2,500 / "
      "T7 over-ceiling 0 / T8 CLW binds 800; the 25A tiers + the shared phaseout + the CLW cross-checked.")

if errors:
    print("\nFAILURES:")
    for e in errors:
        print(f"  X {e}")
    sys.exit(1)
print("\nALL CHECKS PASS")
