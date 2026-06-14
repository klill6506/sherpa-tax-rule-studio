"""Pre-seed math gate for load_1040_form_8889 (Health Savings Accounts — §223).

Run:  poetry run python check_8889_integrity.py

Independently recomputes every scenario from its OWN transcription of the §223 /
i8889 math — the year-keyed contribution limits, the monthly proration + the
last-month rule, the $1,000 catch-up, the deduction = min(own, limit − employer),
the taxable distribution + the 20% tax (with the exception), and the Part III
testing-period failure + the 10% tax — and cross-checks the loader's helper
functions + constants. The loader and this gate share NO math.
"""
import os
import sys
from decimal import Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_form_8889 as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def check(name, got, want):
    if D(got) != D(want):
        err(f"{name}: recomputed {got} != authored {want}")


# ── Independent constants (re-typed from Rev. Proc. 2024-25 / 2025-19) ──
IND_LIMIT = {2025: {"self": 4300, "family": 8550}, 2026: {"self": 4400, "family": 8750}}
IND_CATCH = 1000


def ind_annual(year, coverage):
    return IND_LIMIT.get(year, IND_LIMIT[2025])["family" if coverage == "family" else "self"]


def ind_prorate(amount, months, lmr):
    if lmr:
        return amount
    return round(amount * max(0, min(12, int(months))) / 12)


def ind_deduction(year, coverage, months, lmr, own, employer, age55, alloc=None):
    line3 = ind_prorate(ind_annual(year, coverage), months, lmr)
    line6 = alloc if alloc is not None else line3
    line7 = ind_prorate(IND_CATCH, months, lmr) if age55 else 0
    line8 = line6 + line7
    line12 = max(0, line8 - employer)
    return min(own, line12)


def ind_taxable(total, rollovers, medical):
    return max(0, max(0, total - rollovers) - medical)


def ind_dist_tax(taxable, exc):
    return 0 if exc else round(taxable * 0.20)


def ind_testing_tax(failure):
    return round(failure * 0.10)


def recompute(inp):
    out = {}
    if "own_contrib" in inp:
        out["hsa_deduction"] = ind_deduction(
            inp["tax_year"], inp.get("coverage", "self"), inp.get("eligible_months", 12),
            inp.get("last_month_rule", False), inp["own_contrib"], inp.get("employer_contrib", 0),
            inp.get("age_55", False), inp.get("family_alloc"))
    if "total_dist" in inp:
        tx = ind_taxable(inp["total_dist"], inp.get("rollovers", 0), inp.get("qualified_medical", 0))
        out["hsa_taxable_dist"] = tx
        out["hsa_addl_tax_20"] = ind_dist_tax(tx, inp.get("exception", False))
    if "testing_failure" in inp:
        out["hsa_testing_income"] = inp["testing_failure"]
        out["hsa_addl_tax_10"] = ind_testing_tax(inp["testing_failure"])
    return out


# ── 1. Loader constants + helpers vs the independent transcription ──
for yr in (2025, 2026):
    for cov in ("self", "family"):
        check(f"annual_limit({yr},{cov})", m.annual_limit(yr, cov), ind_annual(yr, cov))
check("CATCH_UP", m.CATCH_UP, IND_CATCH)
check("DIST_TAX", m.DIST_TAX, 0.20)
check("TESTING_TAX", m.TESTING_TAX, 0.10)

for (amt, mo, lmr) in [(4300, 12, False), (4300, 6, False), (4300, 1, True), (1000, 6, False), (8550, 3, False)]:
    check(f"_prorate({amt},{mo},{lmr})", m._prorate(amt, mo, lmr), ind_prorate(amt, mo, lmr))
for args in [(2025, "self", 12, False, 4300, 0, False, None), (2025, "self", 12, False, 2000, 2000, False, None),
             (2025, "self", 12, False, 5300, 0, True, None), (2025, "family", 12, False, 4275, 0, False, 4275),
             (2026, "self", 12, False, 4400, 0, False, None)]:
    check(f"hsa_deduction{args}", m.hsa_deduction(*args), ind_deduction(*args))
for (t, r, med) in [(3000, 0, 2000), (5000, 0, 5000), (1000, 200, 0)]:
    check(f"taxable_distribution({t},{r},{med})", m.taxable_distribution(t, r, med), ind_taxable(t, r, med))
check("dist_addl_tax(1000,False)", m.dist_addl_tax(1000, False), 200)
check("dist_addl_tax(1000,True)", m.dist_addl_tax(1000, True), 0)
check("testing_failure_tax(1000)", m.testing_failure_tax(1000), 100)

# ── 2. Scenarios — independent recompute ──
DIAG_KEYS = {"D_8889_EXCESS", "D_8889_FUNDING", "D_8889_MEDICARE", "D_8889_HDHP",
             "D_8889_TESTING", "D_8889_TY2026"}
spec = m.FORMS[0]
for s in spec["scenarios"]:
    name = s["scenario_name"].split(" ")[0]
    inp, exp = s["inputs"], s["expected_outputs"]
    got = recompute(inp)
    for k, want in exp.items():
        if k in DIAG_KEYS:
            if k == "D_8889_EXCESS" and not (inp.get("own_contrib", 0) > got.get("hsa_deduction", 0)):
                err(f"{name}: D_8889_EXCESS expected but own <= deduction")
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
        err(f"FORM_8889.{key}: duplicate ids")
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
        if k.startswith("D_8889_") and k not in diag_ids:
            err(f"{sc['scenario_name']}: expects unknown diagnostic {k}")
fa_ids = [a["assertion_id"] for a in m.FLOW_ASSERTIONS]
if len(fa_ids) != len(set(fa_ids)):
    err("duplicate flow-assertion ids")

# ── Report ──
print("FORM_8889 (facts/rules/lines/diagnostics/scenarios/links):",
      (len(spec["facts"]), len(spec["rules"]), len(spec["lines"]),
       len(spec["diagnostics"]), len(spec["scenarios"]), len(spec["rule_links"])))
print(f"Flow assertions: {len(m.FLOW_ASSERTIONS)}; authority sources: {len(m.AUTHORITY_SOURCES)}")
print("Independently recomputed - T1 4,300 / T2 prorated 2,150 / T3 last-month 4,300 / T4 employer 2,000 / "
      "T5 catch-up 5,300 / T6 dist 1,000 + 20% 200 / T7 exception 0 / T8 testing 1,000 + 10% 100 / "
      "T9 family split 4,275 / T10 2026 4,400; the 223 limits + proration + the distribution/Part-III math cross-checked.")

if errors:
    print("\nFAILURES:")
    for e in errors:
        print(f"  X {e}")
    sys.exit(1)
print("\nALL CHECKS PASS")
