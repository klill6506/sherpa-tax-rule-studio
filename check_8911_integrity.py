"""Pre-seed math gate for load_1040_form_8911 (§30C refueling credit, ATS Scenario 13).

Run:  poetry run python check_8911_integrity.py

Independently recomputes every scenario from its OWN transcription of the
Form 8911 + Schedule A math (the §30C(i) 6/30/2026 window, the claim-year
gate, the census-tract assertion gate, 30%/$1,000 personal, 6%/30%-PWA/
$100,000 business with the §179 backout and the 1/29/2023 auto-Yes, and the
L5-L10 tax/TMT limitation chain), cross-checks the loader's constants
cell-by-cell, and enforces the varchar(20) id caps on rule_id /
diagnostic_id / line_number (the check_schedule_f_integrity guards).
"""
import os
import sys
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_form_8911 as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def rnd(x):
    """Whole-dollar, half-up (the suite convention)."""
    return D(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def check(name, got, want):
    if D(got) != D(want):
        err(f"{name}: recomputed {got} != authored {want}")


# ── Independent constants (re-typed from §30C + i8911 Rev. 12-2025) ──
IND_TERMINATION = date(2026, 6, 30)      # §30C(i), P.L. 119-21 (verbatim fetched 2026-07-02)
IND_PERSONAL_RATE = Decimal("0.30")      # §30C(a)
IND_BUSINESS_RATE = Decimal("0.06")      # §30C(a) depreciable property
IND_BUSINESS_RATE_PWA = Decimal("0.30")  # i8911 (PWA requirements met)
IND_PERSONAL_CAP = Decimal(1000)         # §30C(b) per item
IND_BUSINESS_CAP = Decimal(100000)       # §30C(b) per item
IND_PWA_AUTO_YES = date(2023, 1, 29)     # i8911 Sch A line 13
IND_GEOID_LEN = 11


def _d(s):
    return date.fromisoformat(s) if isinstance(s, str) else s


def ind_qualifies(pis, tax_year):
    pis = _d(pis)
    return pis is not None and pis.year == tax_year and pis <= IND_TERMINATION


def f8911(inp):
    """Independent transcription of the whole form."""
    year = inp["tax_year"]
    out = {"D_8911_001": False, "D_8911_002": False, "D_8911_003": False,
           "D_8911_004": False, "D_8911_006": False}
    line1 = Decimal(0)
    line4 = Decimal(0)
    first_cells = {}
    for i, p in enumerate(inp.get("properties", [])):
        cost = D(p.get("cost", 0))
        pct = D(p.get("business_pct", 0)) / Decimal(100)
        pis = _d(p.get("pis_date"))
        tract = p.get("census_tract_ok", None)
        if cost > 0 and tract is None:
            out["D_8911_001"] = True
        if pis is not None and pis > IND_TERMINATION:
            out["D_8911_002"] = True
        if pis is not None and pis.year != year:
            out["D_8911_006"] = True
        qualifies = ind_qualifies(pis, year) and tract is True
        a10 = rnd(cost * pct)
        a12 = max(Decimal(0), a10 - D(p.get("s179", 0)))
        pwa = bool(p.get("pwa_met", False)) or (
            _d(p.get("construction_began")) is not None and _d(p.get("construction_began")) < IND_PWA_AUTO_YES)
        a14 = rnd(a12 * (IND_BUSINESS_RATE_PWA if pwa else IND_BUSINESS_RATE))
        a16 = min(a14, IND_BUSINESS_CAP)
        a18 = cost - a10
        a19 = rnd(a18 * IND_PERSONAL_RATE)
        a21 = min(a19, IND_PERSONAL_CAP) if p.get("main_home", False) else Decimal(0)
        if not qualifies:
            a14 = a16 = a19 = a21 = Decimal(0)
        if i == 0:
            first_cells = {"A-10": a10, "A-14": a14, "A-16": a16, "A-18": a18, "A-19": a19, "A-21": a21}
        line1 += a16
        line4 += a21
    line3 = line1 + D(inp.get("f8911_k1_credit", 0))
    line5 = D(inp.get("f1040_line16", 0)) + D(inp.get("sch2_1z", 0))
    line6c = D(inp.get("sch3_line1_ftc", 0)) + D(inp.get("f1040_line19", 0)) + D(inp.get("sch3_before_6j", 0))
    line7 = max(Decimal(0), line5 - line6c)
    line8 = D(inp.get("tmt", 0))
    line9 = max(Decimal(0), line7 - line8)
    line10 = min(line4, line9)
    out.update(first_cells)
    out["f8911_business_credit"] = line3
    out["f8911_personal_total"] = line4
    out["f8911_net_regular_tax"] = line7
    out["f8911_tmt"] = line8
    out["f8911_allowed_personal"] = line10
    out["D_8911_003"] = line4 > 0 and line9 < line4
    out["D_8911_004"] = line3 > 0
    return out


# ── 1. Loader constants vs the independent transcription ──
if m.SECTION_30C_TERMINATION != IND_TERMINATION:
    err(f"SECTION_30C_TERMINATION {m.SECTION_30C_TERMINATION} != {IND_TERMINATION}")
check("PERSONAL_RATE", m.PERSONAL_RATE, IND_PERSONAL_RATE)
check("BUSINESS_RATE_BASE", m.BUSINESS_RATE_BASE, IND_BUSINESS_RATE)
check("BUSINESS_RATE_PWA", m.BUSINESS_RATE_PWA, IND_BUSINESS_RATE_PWA)
check("PERSONAL_CAP", m.PERSONAL_CAP, IND_PERSONAL_CAP)
check("BUSINESS_CAP", m.BUSINESS_CAP, IND_BUSINESS_CAP)
if m.PWA_AUTO_YES_BEFORE != IND_PWA_AUTO_YES:
    err(f"PWA_AUTO_YES_BEFORE {m.PWA_AUTO_YES_BEFORE} != {IND_PWA_AUTO_YES}")
check("GEOID_LENGTH", m.GEOID_LENGTH, IND_GEOID_LEN)

# the loader's shared window helper agrees with the independent gate
for (pis, yr, want) in [
    (date(2025, 3, 1), 2025, True),      # T1 Birch
    (date(2025, 12, 31), 2025, True),    # TY2025 full year
    (date(2026, 6, 30), 2026, True),     # the boundary day qualifies
    (date(2026, 7, 1), 2026, False),     # the day after the termination
    (date(2024, 5, 1), 2025, False),     # claim-year mismatch (G2)
    (date(2026, 6, 30), 2025, False),    # right window, wrong return year
    (date(2027, 1, 15), 2027, False),    # TY2027+: nothing, explicitly
]:
    if m.refueling_property_qualifies(pis, yr) != want:
        err(f"refueling_property_qualifies({pis}, {yr}) != {want}")

# ── 2. varchar(20) id caps (the check_schedule_f_integrity guards) ──
for r in m.F8911_RULES:
    if len(r["rule_id"]) > 20:
        err(f"rule_id too long (>20): {r['rule_id']}")
for d in m.F8911_DIAGNOSTICS:
    if len(d["diagnostic_id"]) > 20:
        err(f"diagnostic_id too long (>20): {d['diagnostic_id']}")
for ln in m.F8911_LINES:
    if len(ln["line_number"]) > 20:
        err(f"line_number too long (>20): {ln['line_number']}")

# ── 3. Scenarios — independent recompute ──
for s in m.F8911_SCENARIOS:
    name = s["scenario_name"].split(" ")[0]
    inp, exp = s["inputs"], s["expected_outputs"]
    got = f8911(inp)
    for k, want in exp.items():
        if k not in got:
            err(f"{name}.{k}: no independent recompute mapped")
            continue
        if isinstance(want, bool) or isinstance(got[k], bool):
            if bool(got[k]) != bool(want):
                err(f"{name}.{k}: recomputed {got[k]} != authored {want}")
        else:
            check(f"{name}.{k}", got[k], want)

# ── 4. Structural sanity ──
fact_keys = {f["fact_key"] for f in m.F8911_FACTS}
for r in m.F8911_RULES:
    for io in list(r.get("inputs", [])) + list(r.get("outputs", [])):
        if io not in fact_keys:
            err(f"{r['rule_id']}: references unknown fact '{io}'")
linked_rules = {rl[0] for rl in m.F8911_RULE_LINKS}
for r in m.F8911_RULES:
    if r["rule_id"] not in linked_rules:
        err(f"{r['rule_id']}: no authority link (every rule must be cited)")
# READY_TO_SEED approval state: Ken approved 2026-07-02 in-session — no gate on the flag.

print("=" * 64)
if errors:
    print(f"CHECK FAILED — {len(errors)} problem(s):")
    for e in errors:
        print(f"  ✗ {e}")
    sys.exit(1)
print("ALL CHECKS PASS — FORM_8911 loader internally consistent")
print(f"  scenarios: {len(m.F8911_SCENARIOS)} | rules: {len(m.F8911_RULES)} | "
      f"diagnostics: {len(m.F8911_DIAGNOSTICS)} | lines: {len(m.F8911_LINES)} | "
      f"FAs: {len(m.FLOW_ASSERTIONS)}")
print(f"READY_TO_SEED = {m.READY_TO_SEED} (Ken approved 2026-07-02)")
