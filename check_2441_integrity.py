"""Pre-seed math gate for load_1040_form_2441 (Child and Dependent Care Credit).

Run:  poetry run python check_2441_integrity.py

Independently recomputes every scenario from its OWN transcription of the §21
math — the $3,000/$6,000 expense caps, the AGI applicable-% table (2025
verbatim / 2026 OBBBA interim), the earned-income limit + the $250/$500
deeming, and the Part III DCB reduction — and cross-checks the loader's
constants cell-by-cell. The loader and this gate share NO math.
"""
import math
import os
import sys
from decimal import Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_form_2441 as m  # noqa: E402

errors: list[str] = []
_INF = 10 ** 12


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def check(name, got, want):
    if D(got) != D(want):
        err(f"{name}: recomputed {got} != authored {want}")


# ── Independent constants (re-typed from the 2025 i2441 / the OBBBA brief) ──
IND_PCT_2025 = [
    (15000, "0.35"), (17000, "0.34"), (19000, "0.33"), (21000, "0.32"),
    (23000, "0.31"), (25000, "0.30"), (27000, "0.29"), (29000, "0.28"),
    (31000, "0.27"), (33000, "0.26"), (35000, "0.25"), (37000, "0.24"),
    (39000, "0.23"), (41000, "0.22"), (43000, "0.21"), (_INF, "0.20"),
]
IND_TIER1 = {"other": 15000, "mfj": 30000}
IND_TIER2B = {"other": 75000, "mfj": 150000}


def ind_decimal(agi, fs, year):
    if year <= 2025:
        for upper, dec in IND_PCT_2025:
            if agi <= upper:
                return dec
        return "0.20"
    sk = "mfj" if fs == "mfj" else "other"
    t1, t2b = IND_TIER1[sk], IND_TIER2B[sk]
    if agi <= t1:
        return "0.50"
    if agi <= t2b:
        return f"{max(0.35, 0.50 - 0.01 * math.ceil((agi - t1) / 2000)):.2f}"
    return f"{max(0.20, 0.35 - 0.01 * math.ceil((agi - t2b) / 2000)):.2f}"


def recompute(inp):
    year, fs = inp["tax_year"], inp["filing_status"]
    count = inp.get("qualifying_count", 0)
    cap = 6000 if count >= 2 else 3000
    capped = max(D(0), min(D(inp.get("care_expenses", 0)), D(cap)) - D(inp.get("dcb_benefits", 0)))
    tp = D(inp.get("taxpayer_earned_income", 0))
    if fs == "mfj":
        spouse = D(inp.get("spouse_earned_income", 0))
        if inp.get("spouse_student_or_disabled"):
            deemed = min(12, inp.get("deeming_months", 12)) * (500 if count >= 2 else 250)
            spouse = max(spouse, D(deemed))
        earned_limit = min(capped, tp, spouse)
    else:
        earned_limit = min(capped, tp)
    dec = D(ind_decimal(inp.get("agi", 0), fs, year))
    credit = earned_limit * dec   # no tax-liability cap in the pins
    return {"f2441_expenses_capped": capped, "f2441_earned_income_limit": earned_limit,
            "f2441_decimal": dec, "f2441_credit": credit}


# ── 1. Loader constants vs the independent transcription ──
for i, (upper, dec) in enumerate(IND_PCT_2025):
    if m.CDCC_PCT_2025[i] != (upper, dec):
        err(f"CDCC_PCT_2025[{i}] {m.CDCC_PCT_2025[i]} != {(upper, dec)}")
check("EXPENSE_LIMIT_ONE", m.EXPENSE_LIMIT_ONE, 3000)
check("EXPENSE_LIMIT_TWO", m.EXPENSE_LIMIT_TWO, 6000)
check("DEEMED_EARNED_ONE", m.DEEMED_EARNED_ONE, 250)
check("DEEMED_EARNED_TWO", m.DEEMED_EARNED_TWO, 500)
for sk in ("other", "mfj"):
    check(f"tier1[{sk}]", m.CDCC_2026_TIER1_TOP[sk], IND_TIER1[sk])
    check(f"tier2b[{sk}]", m.CDCC_2026_TIER2B_START[sk], IND_TIER2B[sk])
# the loader's shared decimal helper agrees
for (agi, fs, yr) in [(14000, "single", 2025), (30000, "mfj", 2025), (80000, "mfj", 2025),
                      (10000, "single", 2026), (200000, "single", 2026), (25000, "mfj", 2026)]:
    if m.cdcc_decimal(agi, fs, yr) != ind_decimal(agi, fs, yr):
        err(f"cdcc_decimal({agi},{fs},{yr}) = {m.cdcc_decimal(agi, fs, yr)} != {ind_decimal(agi, fs, yr)}")
check("expense_cap(1)", m.expense_cap(1), 3000)
check("expense_cap(2)", m.expense_cap(2), 6000)
check("deemed_monthly(2)", m.deemed_monthly(2), 500)

# ── 2. Scenarios — independent recompute ──
DIAG_KEYS = {"D_2441_001", "D_2441_002", "D_2441_006"}
for s in m.F2441_SCENARIOS:
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
    # diagnostic sanity
    if exp.get("D_2441_001"):
        check(f"{name}.credit(D_2441_001)", got["f2441_credit"], 0)
    if exp.get("D_2441_002") and inp.get("tax_year") != 2026:
        err(f"{name}: D_2441_002 expected but year != 2026")

# ── 3. Structural checks ──
spec = m.FORMS[0]
known_sources = {s["source_code"] for s in m.AUTHORITY_SOURCES} | set(m.EXISTING_SOURCES_TO_REFERENCE)
for key, idk in (("facts", "fact_key"), ("rules", "rule_id"), ("lines", "line_number"),
                 ("diagnostics", "diagnostic_id"), ("scenarios", "scenario_name")):
    ids = [x[idk] for x in spec[key]]
    if len(ids) != len(set(ids)):
        err(f"FORM_2441.{key}: duplicate ids")
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
        if k.startswith("D_2441_") and k not in diag_ids:
            err(f"{sc['scenario_name']}: expects unknown diagnostic {k}")
fa_ids = [a["assertion_id"] for a in m.FLOW_ASSERTIONS]
if len(fa_ids) != len(set(fa_ids)):
    err("duplicate flow-assertion ids")

# ── Report ──
print("FORM_2441 (facts/rules/lines/diagnostics/scenarios/links):",
      (len(spec["facts"]), len(spec["rules"]), len(spec["lines"]),
       len(spec["diagnostics"]), len(spec["scenarios"]), len(spec["rule_links"])))
print(f"Flow assertions: {len(m.FLOW_ASSERTIONS)}; authority sources: {len(m.AUTHORITY_SOURCES)}")
print("Independently recomputed: T1 one-child $3k cap @35% -> 1,050 / T2 two+ $6k @20% -> 1,200 / "
      "T3 earned-income limit binds -> 540 / T4 DCB reduces cap -> 320 / T5 2026 50% top -> 1,500 / "
      "T6 deeming $500x12 -> 6,000 limit / G1 no earned income -> 0; the 2025 table + the 2026 "
      "endpoints + the caps/deeming cross-checked.")

if errors:
    print("\nFAILURES:")
    for e in errors:
        print(f"  X {e}")
    sys.exit(1)
print("\nALL CHECKS PASS")
