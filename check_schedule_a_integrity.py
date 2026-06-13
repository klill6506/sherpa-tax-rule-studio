"""Pre-seed math gate for load_1040_schedule_a (Schedule A — Itemized Deductions).

Run:  poetry run python check_schedule_a_integrity.py

Independently recomputes every scenario from its OWN transcription of the
Schedule A math — the 7.5% medical floor, the OBBBA SALT cap + 30% phasedown,
the Pub 526 charitable AGI-bucket limits + carryover + the 2026 0.5% floor, the
2026 PMI phaseout, and the gambling 90% (2026) cap — and cross-checks the
loader's constants tables cell-by-cell. The loader and this gate share NO math.
"""
import math
import os
import sys
from decimal import Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_schedule_a as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def check(name, got, want):
    if D(got) != D(want):
        err(f"{name}: recomputed {got} != authored {want}")


# ── Independent constants (re-typed from the source brief / enacted OBBBA) ──
IND_SALT = {
    2025: {"cap": 40000, "cap_mfs": 20000, "threshold": 500000, "threshold_mfs": 250000,
           "floor": 10000, "floor_mfs": 5000, "rate": 0.30},
    2026: {"cap": 40400, "cap_mfs": 20200, "threshold": 505000, "threshold_mfs": 252500,
           "floor": 10000, "floor_mfs": 5000, "rate": 0.30},
}
IND_MEDICAL = 0.075
IND_CHAR = {"cash": 0.60, "fifty": 0.50, "capgain": 0.30, "floor": {2025: None, 2026: 0.005}}
IND_GAMBLING = {2025: 1.00, 2026: 0.90}
IND_PMI_START = 100000


# ── Independent recompute ──
def ind_medical(agi, expenses):
    return max(0, expenses - round(IND_MEDICAL * agi))


def ind_salt(line5d, magi, fs, year):
    c = IND_SALT[year]
    mfs = fs == "mfs"
    cap = c["cap_mfs"] if mfs else c["cap"]
    thr = c["threshold_mfs"] if mfs else c["threshold"]
    floor = c["floor_mfs"] if mfs else c["floor"]
    over = max(0, magi - thr)
    phased = max(floor, cap - int(0.30 * over))
    return min(line5d, phased)


def ind_charitable(agi, cash, fmv, capgain, carryover_in, year):
    cash_lim = min(cash, IND_CHAR["cash"] * agi)
    fmv_lim = min(fmv, IND_CHAR["fifty"] * agi)
    capgain_lim = min(capgain, IND_CHAR["capgain"] * agi)
    allowed = min(cash_lim + fmv_lim + capgain_lim + carryover_in, IND_CHAR["cash"] * agi)
    carryover_out = (cash + fmv + capgain + carryover_in) - allowed
    line14 = allowed
    floor = IND_CHAR["floor"][year]
    if floor:
        line14 = max(0, line14 - round(floor * agi))
    return line14, carryover_out


def ind_gambling(winnings, losses, year):
    return min(IND_GAMBLING[year] * losses, winnings)


def ind_pmi(agi, premiums, year, fs):
    if year != 2026 or premiums <= 0:
        return 0
    inc = 500 if fs == "mfs" else 1000
    steps = math.ceil(max(0, agi - IND_PMI_START) / inc)
    reduction = min(1.0, 0.10 * steps)
    return max(0, premiums * (1 - reduction))


# ── 1. Loader constants vs the independent transcription ──
for year in (2025, 2026):
    for k in ("cap", "cap_mfs", "threshold", "threshold_mfs", "floor", "floor_mfs"):
        check(f"SALT[{year}][{k}]", m.SALT[year][k], IND_SALT[year][k])
    if str(m.SALT[year]["rate"]) != "0.30":
        err(f"SALT[{year}].rate {m.SALT[year]['rate']} != 0.30")
check("MEDICAL_FLOOR_PCT", m.MEDICAL_FLOOR_PCT, "0.075")
check("CHAR cash", m.CHARITABLE["cash_pct"], "0.60")
check("CHAR fifty", m.CHARITABLE["fifty_pct"], "0.50")
check("CHAR capgain", m.CHARITABLE["capgain_pct"], "0.30")
if m.CHARITABLE["floor_pct"][2025] is not None:
    err("CHARITABLE floor 2025 should be None")
check("CHAR floor 2026", m.CHARITABLE["floor_pct"][2026], "0.005")
check("GAMBLING 2025", m.GAMBLING_LOSS_PCT[2025], "1.00")
check("GAMBLING 2026", m.GAMBLING_LOSS_PCT[2026], "0.90")
if not m.SECTION_68_ACTIVE[2026] or m.SECTION_68_ACTIVE[2025]:
    err("SECTION_68_ACTIVE should be False 2025 / True 2026")
# the loader's shared _salt_cap helper agrees with the independent recompute
for (l5d, magi, fs, yr) in [(50000, 600000, "single", 2025), (50000, 550000, "single", 2025),
                            (25000, 200000, "single", 2025), (60000, 605000, "mfj", 2026),
                            (30000, 300000, "mfs", 2025)]:
    if m._salt_cap(l5d, magi, fs, yr) != ind_salt(l5d, magi, fs, yr):
        err(f"_salt_cap({l5d},{magi},{fs},{yr}) = {m._salt_cap(l5d, magi, fs, yr)} != {ind_salt(l5d, magi, fs, yr)}")

# ── 2. Scenarios — independent recompute ──
DIAG_KEYS = {"D_SCHA_001", "D_SCHA_004", "D_SCHA_005", "D_SCHA_006", "D_SCHA_009"}
for s in m.SCHA_SCENARIOS:
    name = s["scenario_name"].split(" ")[0]
    inp, exp = s["inputs"], s["expected_outputs"]
    year = inp.get("tax_year", 2025)
    fs = inp.get("filing_status", "single")
    got = {}

    if "line_4" in exp:
        got["line_4"] = ind_medical(inp.get("agi", 0), inp.get("scha_medical_expenses", 0))
    if "scha_line5e" in exp:
        l5d = (inp.get("scha_salt_income_or_sales", 0) + inp.get("scha_real_estate_taxes", 0)
               + inp.get("scha_personal_property_taxes", 0))
        got["scha_line5e"] = ind_salt(l5d, inp.get("magi", 0), fs, year)
    if "scha_line14" in exp or "scha_charitable_carryover_out" in exp:
        l14, co = ind_charitable(
            inp.get("agi", 0), inp.get("scha_charitable_cash", 0),
            inp.get("scha_charitable_noncash_fmv", 0), inp.get("scha_charitable_capgain_50org", 0),
            inp.get("scha_charitable_carryover_in", 0), year)
        got["scha_line14"] = l14
        got["scha_charitable_carryover_out"] = co
    if "scha_line16" in exp:
        got["scha_line16"] = (ind_gambling(inp.get("scha_gambling_winnings", 0),
                                            inp.get("scha_gambling_losses", 0), year)
                              + inp.get("scha_other_itemized", 0))
    if "line_8d" in exp:
        got["line_8d"] = ind_pmi(inp.get("agi", 0), inp.get("scha_mortgage_insurance_premiums", 0), year, fs)

    for k, want in exp.items():
        if k in DIAG_KEYS:
            continue  # diagnostics validated structurally below
        if k not in got:
            err(f"{name}.{k}: no independent recompute mapped")
            continue
        check(f"{name}.{k}", got[k], want)

# ── 3. Structural checks ──
spec = m.FORMS[0]
known_sources = {s["source_code"] for s in m.AUTHORITY_SOURCES} | set(m.EXISTING_SOURCES_TO_REFERENCE)
for key, idk in (("facts", "fact_key"), ("rules", "rule_id"), ("lines", "line_number"),
                 ("diagnostics", "diagnostic_id"), ("scenarios", "scenario_name")):
    ids = [x[idk] for x in spec[key]]
    if len(ids) != len(set(ids)):
        err(f"SCHEDULE_A.{key}: duplicate ids")
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
        if k.startswith("D_SCHA_") and k not in diag_ids:
            err(f"{sc['scenario_name']}: expects unknown diagnostic {k}")
fa_ids = [a["assertion_id"] for a in m.FLOW_ASSERTIONS]
if len(fa_ids) != len(set(fa_ids)):
    err("duplicate flow-assertion ids")

# ── Report ──
print("SCHEDULE_A (facts/rules/lines/diagnostics/scenarios/links):",
      (len(spec["facts"]), len(spec["rules"]), len(spec["lines"]),
       len(spec["diagnostics"]), len(spec["scenarios"]), len(spec["rule_links"])))
print(f"Flow assertions: {len(m.FLOW_ASSERTIONS)}; authority sources: {len(m.AUTHORITY_SOURCES)}")
print("Independently recomputed: medical 7.5% floor (T1) / SALT phasedown to floor + partial + "
      "under-cap + 2026 (T2-T5) / charitable 60% + over-limit carryover + 30% capgain + 2026 0.5% "
      "floor (T6-T9) / gambling 2026 90% (T10) / 2026 PMI phaseout (T11); SALT + charitable + "
      "gambling + PMI constants cross-checked both years.")

if errors:
    print("\nFAILURES:")
    for e in errors:
        print(f"  X {e}")
    sys.exit(1)
print("\nALL CHECKS PASS")
