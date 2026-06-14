"""Pre-seed math gate for load_1040_form_8962 (Premium Tax Credit).

Run:  poetry run python check_8962_integrity.py

Independently recomputes every scenario from its OWN transcription of the §36B /
i8962 math — the 2024 FPL tables, line 5 (truncate, cap 401), the Table 2
applicable figure, lines 8a/8b, the monthly PTC, the §36B(f) reconciliation, and
the Table 5 repayment limitation — and cross-checks the loader's helper
functions + constants cell-by-cell. The loader and this gate share NO math.
"""
import os
import sys
from decimal import Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_form_8962 as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def check(name, got, want):
    if D(got) != D(want):
        err(f"{name}: recomputed {got} != authored {want}")


# ── Independent constants (re-typed from the 2025 i8962 PDF) ──
IND_FPL = {
    "contiguous": (15060, 5380),
    "alaska": (18810, 6730),
    "hawaii": (17310, 6190),
}
IND_REPAY = [(200, 375, 750), (300, 975, 1950), (400, 1625, 3250)]


def ind_fpl_amount(state, size):
    base, inc = IND_FPL[state]
    return base + max(0, size - 1) * inc


def ind_fpl_pct(income, fpl):
    if fpl <= 0:
        return 0
    p = int((income / fpl) * 100)
    return 401 if p > 400 else p


def ind_af(p):
    if p < 150:
        f = 0.0
    elif p < 200:
        f = (p - 150) * 0.0004
    elif p < 250:
        f = 0.02 + (p - 200) * 0.0004
    elif p < 300:
        f = 0.04 + (p - 250) * 0.0004
    elif p < 400:
        f = 0.06 + (p - 300) * 0.00025
    else:
        f = 0.085
    return round(f, 4)


def ind_repay_limit(p, fs):
    if p >= 400:
        return None
    single = (fs or "").lower() == "single"
    for upper, s, o in IND_REPAY:
        if p < upper:
            return s if single else o
    return None


def recompute(inp):
    fs = inp["filing_status"]
    state = inp.get("state", "contiguous")
    size = inp.get("family_size", 1)
    income = inp.get("household_income", 0)
    fpl = ind_fpl_amount(state, size)
    p = ind_fpl_pct(income, fpl)
    af = ind_af(p)
    contrib = round(income * af)            # line 8a
    out = {"f8962_fpl": fpl, "f8962_fpl_pct": p, "f8962_applicable_figure": af,
           "f8962_annual_contribution": contrib}
    if "premium_annual" in inp:
        premium, slcsp, aptc = inp["premium_annual"], inp["slcsp_annual"], inp["aptc_annual"]
        ptc = min(premium, max(0, slcsp - contrib))
        out["f8962_total_ptc"] = ptc
        if ptc >= aptc:
            out["f8962_net_ptc"] = ptc - aptc
        else:
            excess = aptc - ptc
            limit = ind_repay_limit(p, fs)
            out["f8962_excess_aptc"] = excess
            out["f8962_repayment"] = excess if limit is None else min(excess, limit)
    return out


# ── 1. Loader constants + helpers vs the independent transcription ──
for st in ("contiguous", "alaska", "hawaii"):
    if m.FPL_2024[st] != IND_FPL[st]:
        err(f"FPL_2024[{st}] {m.FPL_2024[st]} != {IND_FPL[st]}")
if m.REPAYMENT_LIMIT_2025 != IND_REPAY:
    err(f"REPAYMENT_LIMIT_2025 {m.REPAYMENT_LIMIT_2025} != {IND_REPAY}")
# helper agreement at sample points
for (st, size) in [("contiguous", 1), ("contiguous", 4), ("alaska", 2), ("hawaii", 3)]:
    check(f"fpl_amount({st},{size})", m.fpl_amount(st, size), ind_fpl_amount(st, size))
for (inc, fpl) in [(37650, 15060), (90000, 20440), (26355, 15060), (50000, 15060), (10000, 15060)]:
    check(f"fpl_pct({inc},{fpl})", m.fpl_pct(inc, fpl), ind_fpl_pct(inc, fpl))
for p in (100, 150, 175, 200, 250, 300, 332, 350, 399, 400, 401):
    if str(m.applicable_figure(p)) != f"{ind_af(p):.4f}":
        err(f"applicable_figure({p}) = {m.applicable_figure(p)} != {ind_af(p):.4f}")
for (p, fs) in [(185, "single"), (332, "single"), (332, "mfj"), (250, "other"), (400, "single"), (401, "single")]:
    if m.repayment_limit(p, fs) != ind_repay_limit(p, fs):
        err(f"repayment_limit({p},{fs}) = {m.repayment_limit(p, fs)} != {ind_repay_limit(p, fs)}")
for (a, b, c) in [(7200, 7800, 1506), (6000, 3100, 3400), (5000, 1000, 392)]:
    # monthly_ptc(premium, slcsp, contribution) = min(premium, max(0, slcsp-contribution))
    want = min(a, max(0, b - c))
    if m.monthly_ptc(a, b, c) != want:
        err(f"monthly_ptc({a},{b},{c}) = {m.monthly_ptc(a, b, c)} != {want}")

# ── 2. Scenarios — independent recompute ──
DIAG_KEYS = {"D_8962_2026"}
spec = m.FORMS[0]
for s in spec["scenarios"]:
    name = s["scenario_name"].split(" ")[0]
    inp, exp = s["inputs"], s["expected_outputs"]
    got = recompute(inp)
    for k, want in exp.items():
        if k in DIAG_KEYS:
            continue
        if k not in got:
            err(f"{name}.{k}: no independent recompute mapped")
            continue
        check(f"{name}.{k}", got[k], want)
    if exp.get("D_8962_2026") and inp.get("tax_year") != 2026:
        err(f"{name}: D_8962_2026 expected but year != 2026")

# ── 3. Structural checks ──
known_sources = {s["source_code"] for s in m.AUTHORITY_SOURCES} | set(m.EXISTING_SOURCES_TO_REFERENCE)
for key, idk in (("facts", "fact_key"), ("rules", "rule_id"), ("lines", "line_number"),
                 ("diagnostics", "diagnostic_id"), ("scenarios", "scenario_name")):
    ids = [x[idk] for x in spec[key]]
    if len(ids) != len(set(ids)):
        err(f"FORM_8962.{key}: duplicate ids")
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
        if k.startswith("D_8962_") and k not in diag_ids:
            err(f"{sc['scenario_name']}: expects unknown diagnostic {k}")
fa_ids = [a["assertion_id"] for a in m.FLOW_ASSERTIONS]
if len(fa_ids) != len(set(fa_ids)):
    err("duplicate flow-assertion ids")

# ── Report ──
print("FORM_8962 (facts/rules/lines/diagnostics/scenarios/links):",
      (len(spec["facts"]), len(spec["rules"]), len(spec["lines"]),
       len(spec["diagnostics"]), len(spec["scenarios"]), len(spec["rule_links"])))
print(f"Flow assertions: {len(m.FLOW_ASSERTIONS)}; authority sources: {len(m.AUTHORITY_SOURCES)}")
print("Independently recomputed — T1 250%/AF .04 net 2,294 / T2 332% excess 1,900 cap 1,625 / "
      "T3 >400% AF .085 / T4 175% AF .0100 / T5 185% cap 375; the 2024 FPL + Table 5 + the "
      "Table-2 interpolation + line-5 truncation cross-checked.")

if errors:
    print("\nFAILURES:")
    for e in errors:
        print(f"  X {e}")
    sys.exit(1)
print("\nALL CHECKS PASS")
