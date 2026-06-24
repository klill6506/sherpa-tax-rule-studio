"""Pre-seed math gate for load_1040_form_6251 (Alternative Minimum Tax).

Run:  poetry run python check_6251_integrity.py

Independently recomputes every COMPUTABLE scenario from its OWN transcription of
the §55-59 / i6251 math — the AMTI base (taxable income + the standard-deduction-
or-SALT add-back + the senior-deduction add-back + PAB/depreciation preferences −
refund; QBI retained), the exemption phaseout (base − rate × max(0, AMTI −
threshold), year-keyed; 2026 OBBBA 50% / $500k-$1M), the 26/28% tentative minimum
tax, and AMT = max(0, TMT − regular tax) → Schedule 2 line 2 — and cross-checks the
loader's helper functions + constants cell-by-cell. The RED-defer (ISO) and Part III
(capital-gains) scenarios assert the routing intent. The loader and this gate share
NO math.
"""
import os
from decimal import ROUND_HALF_UP, Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_form_6251 as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def check(name, got, want):
    if D(got) != D(want):
        err(f"{name}: recomputed {got} != authored {want}")


def _r0(x):
    """Whole-dollar rounding (the form rounds; ROUND_HALF_UP)."""
    return int(D(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


# ── Independent constants (re-typed from the 2025 f6251 / i6251 / RP 2025-32 / OBBBA) ──
IND_EXEMPTION = {
    2025: {"single": 88100, "mfj": 137000, "mfs": 68500},
    2026: {"single": 90100, "mfj": 140200, "mfs": 70100},
}
IND_THRESHOLD = {
    2025: {"single": 626350, "mfj": 1252700, "mfs": 626350},
    2026: {"single": 500000, "mfj": 1000000, "mfs": 500000},
}
IND_RATE = {2025: 0.25, 2026: 0.50}
IND_BREAKPOINT = {
    2025: {"single": 239100, "mfj": 239100, "mfs": 119550},
    2026: {"single": 244500, "mfj": 244500, "mfs": 122250},
}
IND_26, IND_28 = 0.26, 0.28


def ind_key(fs):
    fs = (fs or "").lower()
    if fs in ("mfj", "qss"):
        return "mfj"
    if fs == "mfs":
        return "mfs"
    return "single"


def ind_exemption(year, fs, amti):
    k = ind_key(fs)
    base = IND_EXEMPTION[year][k]
    over = max(0, amti - IND_THRESHOLD[year][k])
    return max(0, base - IND_RATE[year] * over)


def ind_tmt_ordinary(year, fs, excess):
    bp = IND_BREAKPOINT[year][ind_key(fs)]
    if excess <= bp:
        return excess * IND_26
    return excess * IND_28 - bp * (IND_28 - IND_26)


def ind_amti(inp):
    """AMTI line 4 (computable path): taxable income + the line-2a add-back
    (SALT if itemizing else the standard deduction) + senior-deduction add-back +
    PAB (2g) + depreciation (2l) − refund (2b)."""
    ti = inp.get("a_taxable_income", 0)
    add_2a = inp.get("a_salt_deduction", 0) if inp.get("a_itemizing") else inp.get("a_standard_deduction", 0)
    return (ti + add_2a + inp.get("a_senior_deduction", 0)
            + inp.get("a_pab_interest", 0) + inp.get("a_amt_depreciation_adj", 0)
            - inp.get("a_tax_refund", 0))


def recompute(inp):
    year, fs = inp["tax_year"], inp["filing_status"]
    l4 = ind_amti(inp)
    l5 = _r0(ind_exemption(year, fs, l4))
    l6 = max(0, l4 - l5)
    l7 = _r0(ind_tmt_ordinary(year, fs, l6))
    l9 = l7  # AMT FTC = 0 in v1
    l11 = max(0, l9 - inp.get("a_regular_tax_for_amt", 0))
    return {"line_2a": (inp.get("a_salt_deduction", 0) if inp.get("a_itemizing") else inp.get("a_standard_deduction", 0)),
            "line_2l": inp.get("a_amt_depreciation_adj", 0),
            "line_4": l4, "line_5": l5, "line_6": l6, "line_7": l7, "line_11": l11}


# ── 1. Loader constants vs the independent transcription ──
for yr in (2025, 2026):
    for k in ("single", "mfj", "mfs"):
        check(f"AMT_EXEMPTION[{yr}][{k}]", m.AMT_EXEMPTION[yr][k], IND_EXEMPTION[yr][k])
        check(f"AMT_PHASEOUT_THRESHOLD[{yr}][{k}]", m.AMT_PHASEOUT_THRESHOLD[yr][k], IND_THRESHOLD[yr][k])
        check(f"AMT_BREAKPOINT[{yr}][{k}]", m.AMT_BREAKPOINT[yr][k], IND_BREAKPOINT[yr][k])
    check(f"AMT_PHASEOUT_RATE[{yr}]", m.AMT_PHASEOUT_RATE[yr], IND_RATE[yr])
check("AMT_RATE_LOW", m.AMT_RATE_LOW, IND_26)
check("AMT_RATE_HIGH", m.AMT_RATE_HIGH, IND_28)

# ── 2. Loader helpers vs the independent math (sample points) ──
for (yr, fs, amti) in [(2025, "single", 100000), (2025, "single", 700000), (2025, "mfj", 540000),
                       (2026, "single", 576100), (2026, "mfj", 1100000), (2025, "mfs", 700000)]:
    g, w = m.amt_exemption_amount(yr, fs, amti), ind_exemption(yr, fs, amti)
    if abs(g - w) > 1e-6:
        err(f"amt_exemption_amount({yr},{fs},{amti}) = {g} != {w}")
for (yr, fs, exc) in [(2025, "single", 26900), (2025, "single", 406900), (2025, "mfs", 200000),
                      (2026, "single", 524050), (2025, "mfj", 403000)]:
    g, w = m.tentative_minimum_tax_ordinary(yr, fs, exc), ind_tmt_ordinary(yr, fs, exc)
    if abs(g - w) > 1e-6:
        err(f"tentative_minimum_tax_ordinary({yr},{fs},{exc}) = {g} != {w}")
for (fs, exp) in [("single", "single"), ("hoh", "single"), ("mfj", "mfj"), ("qss", "mfj"), ("mfs", "mfs")]:
    if m._status_key(fs) != exp:
        err(f"_status_key({fs}) = {m._status_key(fs)} != {exp}")

# ── 3. Scenarios — independent recompute ──
DIAG_KEYS = {f"D_6251_{n:03d}" for n in range(1, 9)}
ROUTING = {"Part_III"}
spec = m.FORMS[0]
for s in spec["scenarios"]:
    name = s["scenario_name"].split(" ")[0]
    inp, exp = s["inputs"], s["expected_outputs"]

    # RED-defer scenario (ISO etc.) — assert the routing intent, not the numbers.
    if exp.get("D_6251_001"):
        if not inp.get("a_iso_exercise"):
            err(f"{name}: D_6251_001 expected but no a_iso_exercise input")
        if "line_11" in exp and exp["line_11"] is not None:
            err(f"{name}: a RED-defer scenario must blank line 11 (expected None)")
        continue

    got = recompute(inp)
    for k, want in exp.items():
        if k in ROUTING:
            if k == "Part_III" and not inp.get("a_net_capital_gain"):
                err(f"{name}: Part_III expected but no a_net_capital_gain")
            continue
        if k == "D_6251_007":
            if bool(want) != (got["line_11"] > 0):
                err(f"{name}: D_6251_007 {want} but recomputed line_11 = {got['line_11']}")
            continue
        if k in DIAG_KEYS:
            continue
        if k not in got:
            continue  # Part III sub-lines not recomputed by the ordinary gate
        check(f"{name}.{k}", got[k], want)


# ── Report ──
if errors:
    print(f"\n6251 INTEGRITY GATE: {len(errors)} FAILURE(S)\n")
    for e in errors:
        print(f"  [X] {e}")
    raise SystemExit(1)
print("\n6251 INTEGRITY GATE: ALL CHECKS PASS")
print(f"  constants (2 yrs × 3 status × exemption/threshold/breakpoint + rate) + helpers + "
      f"{len(spec['scenarios'])} scenarios re-derived independently.")
