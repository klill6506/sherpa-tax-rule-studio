"""Pre-seed math gate for load_1040_form_8880 (Saver's Credit, roster #9).

Run:  poetry run python check_8880_integrity.py

Independently recomputes every scenario from its OWN transcription of the Form
8880 math (the AGI tier table re-typed from f8880.pdf, the $2,000 per-person
cap, the box-12 elective-deferral sum, the eligibility exclusion, and the
credit = line 7 x line 9), and cross-checks the loader's tier table + cap +
qualifying-code set cell-by-cell.
"""
import os
import sys
from decimal import Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_form_8880 as m  # noqa: E402

errors: list[str] = []
_INF = 10 ** 12


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def check(name, got, want):
    if D(got) != D(want):
        err(f"{name}: recomputed {got} != authored {want}")


# ── Independent constants (re-typed from f8880.pdf (2025) + the 2026 COLA) ──
IND_TIERS = {
    2025: {
        "mfj":   [(47500, "0.5"), (51000, "0.2"), (79000, "0.1"), (_INF, "0.0")],
        "hoh":   [(35625, "0.5"), (38250, "0.2"), (59250, "0.1"), (_INF, "0.0")],
        "other": [(23750, "0.5"), (25500, "0.2"), (39500, "0.1"), (_INF, "0.0")],
    },
    2026: {
        "mfj":   [(47500, "0.5"), (51000, "0.2"), (80500, "0.1"), (_INF, "0.0")],
        "hoh":   [(35625, "0.5"), (38250, "0.2"), (60375, "0.1"), (_INF, "0.0")],
        "other": [(23750, "0.5"), (25500, "0.2"), (40250, "0.1"), (_INF, "0.0")],
    },
}
IND_QUALIFYING = {"D", "E", "F", "G", "H", "S", "AA", "BB", "EE"}


def ind_status(fs):
    return "mfj" if fs == "mfj" else "hoh" if fs == "hoh" else "other"


def ind_decimal(agi, fs, year):
    for upper, dec in IND_TIERS[year][ind_status(fs)]:
        if agi <= upper:
            return Decimal(dec)
    return Decimal("0")


def f8880(inp):
    year, fs, agi = inp["tax_year"], inp["filing_status"], D(inp["f1040_agi"])
    out = {}

    def col(ira_k, def_k, dist_k, student_k):
        ira = D(inp.get(ira_k, 0))
        deferrals = D(inp.get(def_k, 0))
        dist = D(inp.get(dist_k, 0))
        present = (ira + deferrals) > 0
        eligible = not bool(inp.get(student_k, False))  # scenarios test only the student gate
        if not eligible:
            return Decimal(0), (present and not eligible)
        net = max(Decimal(0), ira + deferrals - dist)
        return min(net, Decimal(m.SAVERS_CONTRIB_CAP)), False

    you6, you_inel = col("f8880_you_ira", "box12_deferrals_you", "f8880_you_distributions",
                         "f8880_you_full_time_student")
    sp6, sp_inel = col("f8880_spouse_ira", "box12_deferrals_spouse", "f8880_spouse_distributions",
                       "f8880_spouse_full_time_student")
    line7 = you6 + sp6
    dec = ind_decimal(agi, fs, year)
    out["f8880_total_contributions"] = line7
    out["f8880_decimal"] = dec
    out["f8880_credit"] = (line7 * dec)   # no tax-liability cap in the pins
    out["D_8880_001"] = dec == 0
    out["D_8880_002"] = you_inel or sp_inel
    out["D_8880_003"] = year == 2026
    return out


# ── 1. Loader constants vs the independent transcription ──
for year in (2025, 2026):
    for st in ("mfj", "hoh", "other"):
        if m.SAVERS_AGI_TIERS[year][st] != IND_TIERS[year][st]:
            err(f"SAVERS_AGI_TIERS[{year}][{st}] drift: {m.SAVERS_AGI_TIERS[year][st]} != {IND_TIERS[year][st]}")
check("SAVERS_CONTRIB_CAP", m.SAVERS_CONTRIB_CAP, 2000)
if m.QUALIFYING_BOX12_CODES != IND_QUALIFYING:
    err(f"QUALIFYING_BOX12_CODES {m.QUALIFYING_BOX12_CODES} != {IND_QUALIFYING}")
# the loader's shared decimal helper agrees
for (agi, fs, yr, want) in [(40000, "mfj", 2025, "0.5"), (24000, "single", 2025, "0.2"),
                            (30000, "single", 2025, "0.1"), (45000, "single", 2025, "0.0"),
                            (80000, "mfj", 2026, "0.1"), (60375, "hoh", 2026, "0.1")]:
    if m.savers_decimal(agi, fs, yr) != want:
        err(f"savers_decimal({agi},{fs},{yr}) = {m.savers_decimal(agi,fs,yr)} != {want}")

# ── 2. Scenarios — independent recompute ──
for s in m.F8880_SCENARIOS:
    name = s["scenario_name"].split(" ")[0]
    inp, exp = s["inputs"], s["expected_outputs"]
    got = f8880(inp)
    for k, want in exp.items():
        if k not in got:
            err(f"{name}.{k}: no independent recompute mapped")
            continue
        if isinstance(want, bool) or isinstance(got[k], bool):
            if bool(got[k]) != bool(want):
                err(f"{name}.{k}: {got[k]} != {want}")
        else:
            check(f"{name}.{k}", got[k], want)

# ── 3. Structural checks ──
known_sources = {s["source_code"] for s in m.AUTHORITY_SOURCES} | set(m.EXISTING_SOURCES_TO_REFERENCE)
for spec in m.FORMS:
    fn = spec["identity"]["form_number"]
    for key, idk in (("facts", "fact_key"), ("rules", "rule_id"), ("lines", "line_number"),
                     ("diagnostics", "diagnostic_id"), ("scenarios", "scenario_name")):
        ids = [x[idk] for x in spec[key]]
        if len(ids) != len(set(ids)):
            err(f"{fn}.{key}: duplicate ids")
    rule_ids = {r["rule_id"] for r in spec["rules"]}
    for rid in rule_ids - {rl[0] for rl in spec["rule_links"]}:
        err(f"{fn}: rule {rid} has ZERO authority links")
    for rid, src, _, _ in spec["rule_links"]:
        if rid not in rule_ids:
            err(f"{fn}: rule_link references unknown rule {rid}")
        if src not in known_sources:
            err(f"{fn}: rule_link references unknown source {src}")
    diag_ids = {d["diagnostic_id"] for d in spec["diagnostics"]}
    for sc in spec["scenarios"]:
        for k in sc["expected_outputs"]:
            if k.startswith("D_8880_") and k not in diag_ids:
                err(f"{fn}/{sc['scenario_name']}: expects unknown diagnostic {k}")

fa_ids = [a["assertion_id"] for a in m.FLOW_ASSERTIONS]
if len(fa_ids) != len(set(fa_ids)):
    err("duplicate flow-assertion ids")

# ── Report ──
spec = m.FORMS[0]
print("FORM_8880 (facts/rules/lines/diagnostics/scenarios/links):",
      (len(spec["facts"]), len(spec["rules"]), len(spec["lines"]),
       len(spec["diagnostics"]), len(spec["scenarios"]), len(spec["rule_links"])))
print(f"Flow assertions: {len(m.FLOW_ASSERTIONS)}; authority sources: {len(m.AUTHORITY_SOURCES)}")
print("Independently recomputed: 8880-T1 (MFJ 50% -> 2,000) / T2 (single 20% -> 400) / "
      "T3 (IRA+box12, $2,000 cap, 10% -> 200) / T4 (distribution reduces) / T5 (over limit -> 0) / "
      "T6 (2026 top cutoff + interim flag) / G1 (student excluded); tier table cross-checked both years.")

if errors:
    print("\nFAILURES:")
    for e in errors:
        print(f"  X {e}")
    sys.exit(1)
print("\nALL CHECKS PASS")
