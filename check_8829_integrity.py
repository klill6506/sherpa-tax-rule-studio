"""Pre-seed math gate for load_1040_form_8829 (Expenses for Business Use of Home).

Run:  <rs-venv>/Scripts/python.exe check_8829_integrity.py

Independently recomputes every COMPUTABLE scenario from its OWN transcription of
the Form 8829 / §280A(c)(5) math — Part I business % (area; daycare hours-of-use),
the 3-tier gross-income limitation (deductible-anyway 9-14 → operating 16-27 →
casualty+depreciation 29-33, each tier limited to the income remaining), the Line 11
Worksheet RE-tax SALT split (reusing a flat cap for the non-iterating case), the
39-yr nonresidential mid-month depreciation (Part III), and the Part IV carryover —
and cross-checks the loader's depreciation table + helpers. The casualty-RED-defer
and the >$500k MAGI-iteration scenarios assert the routing intent. The loader and
this gate share NO math.
"""
import os
from decimal import ROUND_HALF_UP, Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_form_8829 as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def r0(x):
    """Whole-dollar rounding (the form rounds; ROUND_HALF_UP)."""
    return D(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def check(name, got, want):
    if D(got) != D(want):
        err(f"{name}: recomputed {got} != authored {want}")


def check_close(name, got, want, tol=Decimal("0.0005")):
    if abs(D(got) - D(want)) > tol:
        err(f"{name}: recomputed {got} != authored {want} (tol {tol})")


# ── Independent constants (re-typed from i8829 line-41 / Pub 946 / compute_schedule_a) ──
IND_DEPR_FIRST = {1: "2.461", 2: "2.247", 3: "2.033", 4: "1.819", 5: "1.605", 6: "1.391",
                  7: "1.177", 8: "0.963", 9: "0.749", 10: "0.535", 11: "0.321", 12: "0.107"}
IND_DEPR_SUBSEQUENT = "2.564"
IND_DAYCARE_HOURS = {2025: 8760, 2026: 8760}
IND_SALT_CAP = {
    2025: {"cap": 40000, "cap_mfs": 20000, "threshold": 500000, "threshold_mfs": 250000,
           "floor": 10000, "floor_mfs": 5000, "rate": "0.30"},
    2026: {"cap": 40400, "cap_mfs": 20200, "threshold": 505000, "threshold_mfs": 252500,
           "floor": 10000, "floor_mfs": 5000, "rate": "0.30"},
}


def ind_depr_pct(first_use_year, tax_year, month):
    if int(first_use_year) == int(tax_year):
        return IND_DEPR_FIRST[int(month) or 1]
    return IND_DEPR_SUBSEQUENT


def recompute(inp):
    """Independent re-derivation of the computable Form 8829 lines."""
    g = lambda k: D(inp.get(k))
    # ── Part I — business % ──
    l1, l2 = g("h_area_business"), g("h_area_total")
    l3 = (l1 / l2) if l2 else Decimal(0)
    if inp.get("h_is_daycare"):
        avail = g("h_daycare_hours_available") or Decimal(8760)
        l6 = (g("h_daycare_hours") / avail) if avail else Decimal(0)
        l7 = l6 * l3
    else:
        l6 = Decimal(0)
        l7 = l3
    # ── Part II line 8 (§280A cap) ──
    l8 = g("h_sch_c_line29") + g("h_home_business_gain") - g("h_non_home_loss")
    itemize = bool(inp.get("h_itemizing"))
    # ── RE-tax SALT split (Line 11 Worksheet; non-iterating, flat cap) ──
    if itemize:
        ws6 = r0(g("h_re_taxes_home") * l7)
        cap = g("h_salt_cap_ref")
        ws9 = max(Decimal(0), cap - g("h_personal_salt_other"))
        l11_a = min(ws6, ws9)
        l17_a = ws6 - l11_a
        l17_b = Decimal(0)
        l10_b = g("h_mortgage_deductible")
        l16_b = g("h_excess_mortgage")
    else:
        l11_a = Decimal(0)
        l17_a = Decimal(0)
        l17_b = g("h_excess_re_taxes")   # standard deduction → full home RE tax, col (b)
        l10_b = Decimal(0)
        l16_b = g("h_excess_mortgage")
    l11 = l11_a            # line 11 (col a for itemizer; 0 for standard)
    l17 = l17_a + l17_b
    # ── Tier 1 (9-14) — deductible-anyway ──
    l12_a = g("h_casualty_direct") + l11_a                 # mortgage never col (a)
    l12_b = g("h_casualty_indirect") + l10_b               # line 11 col (b) = 0
    l13 = r0(l12_b * l7)
    l14 = l12_a + l13
    l15 = max(Decimal(0), l8 - l14)
    # ── Tier 2 (16-27) — operating ──
    l23_a = (l17_a + g("h_insurance_direct") + g("h_repairs_direct")
             + g("h_utilities_direct") + g("h_other_direct"))   # excess mortgage never col (a)
    l23_b = (l16_b + l17_b + g("h_insurance_indirect") + g("h_rent_indirect")
             + g("h_repairs_indirect") + g("h_utilities_indirect") + g("h_other_indirect"))
    l24 = r0(l23_b * l7)
    l26 = l23_a + l24 + g("h_carryover_operating_prior")
    l27 = min(l15, l26)
    l28 = l15 - l27
    # ── Part III depreciation → line 30 ──
    if g("h_basis_or_fmv") > 0:
        l39 = g("h_basis_or_fmv") - g("h_land_value")
        l40 = r0(l39 * l7)
        l41 = D(ind_depr_pct(inp.get("h_first_use_year", 0), inp["tax_year"], inp.get("h_month_first_used", 1)))
        l42 = r0(l40 * l41 / Decimal(100))
    else:
        l39 = l40 = l41 = l42 = Decimal(0)
    l30 = l42 if g("h_basis_or_fmv") > 0 else g("h_depreciation")
    # ── Tier 3 (29-33) ──
    l32 = g("h_excess_casualty") + l30 + g("h_carryover_casdep_prior")
    l33 = min(l28, l32)
    # ── 34-36 ──
    l34 = l14 + l27 + l33
    l35 = Decimal(0)        # casualty → Form 4684 RED-deferred
    l36 = l34 - l35
    # ── Part IV ──
    l43 = max(Decimal(0), l26 - l27)
    l44 = max(Decimal(0), l32 - l33)
    return {"line_3": l3, "line_6": l6, "line_7": l7, "line_8": l8, "line_11": l11, "line_14": l14,
            "line_15": l15, "line_17": l17, "line_24": l24, "line_26": l26, "line_27": l27,
            "line_28": l28, "line_32": l32, "line_33": l33, "line_34": l34, "line_36": l36,
            "line_39": l39, "line_40": l40, "line_41": l41, "line_42": l42, "line_43": l43, "line_44": l44}


PCT_LINES = {"line_3", "line_6", "line_7", "line_41"}
DIAG_KEYS = {f"D_8829_{n:03d}" for n in range(1, 9)}
ROUTING = {"SALT_iteration"}

# ── 1. Loader constants vs the independent transcription ──
for mth in range(1, 13):
    check(f"DEPRECIATION_FIRST_YEAR_PCT[{mth}]", m.DEPRECIATION_FIRST_YEAR_PCT[mth], IND_DEPR_FIRST[mth])
check("DEPRECIATION_SUBSEQUENT_PCT", m.DEPRECIATION_SUBSEQUENT_PCT, IND_DEPR_SUBSEQUENT)
for yr in (2025, 2026):
    check(f"DAYCARE_HOURS_PER_YEAR[{yr}]", m.DAYCARE_HOURS_PER_YEAR[yr], IND_DAYCARE_HOURS[yr])
    for k in ("cap", "cap_mfs", "threshold", "threshold_mfs", "floor", "floor_mfs", "rate"):
        check(f"SALT_CAP_REF[{yr}][{k}]", m.SALT_CAP_REF[yr][k], IND_SALT_CAP[yr][k])

# ── 2. Loader helpers vs the independent math (sample points) ──
for (fy, ty, mo) in [(2025, 2025, 1), (2025, 2025, 6), (2025, 2025, 12), (2022, 2025, 6), (2020, 2026, 3)]:
    g, w = m.depreciation_pct(fy, ty, mo), ind_depr_pct(fy, ty, mo)
    if g != w:
        err(f"depreciation_pct({fy},{ty},{mo}) = {g} != {w}")
for yr in (2025, 2026, 2099):
    if m.daycare_hours_for(yr) != IND_DAYCARE_HOURS.get(yr, 8760):
        err(f"daycare_hours_for({yr}) = {m.daycare_hours_for(yr)} != 8760")

# ── 3. Scenarios — independent recompute ──
spec = m.FORMS[0]
for s in spec["scenarios"]:
    name = s["scenario_name"].split(" ")[0]
    inp, exp = s["inputs"], s["expected_outputs"]

    # Casualty RED-defer scenario — assert the routing intent, not the numbers.
    if exp.get("D_8829_002"):
        if not (inp.get("h_casualty_direct") or inp.get("h_casualty_indirect") or inp.get("h_excess_casualty")):
            err(f"{name}: D_8829_002 expected but no casualty input")
        if "line_36" in exp and exp["line_36"] is not None:
            err(f"{name}: a casualty RED-defer scenario must blank line 36 (expected None)")
        continue

    # >$500k MAGI iteration scenario — assert the routing intent.
    if exp.get("D_8829_005") or exp.get("SALT_iteration"):
        if not inp.get("magi_over_threshold"):
            err(f"{name}: D_8829_005/iteration expected but no magi_over_threshold input")
        continue

    got = recompute(inp)
    for k, want in exp.items():
        if k in DIAG_KEYS or k in ROUTING:
            continue
        if k not in got:
            continue
        if k in PCT_LINES:
            check_close(f"{name}.{k}", got[k], want)
        else:
            check(f"{name}.{k}", got[k], want)


# ── Report ──
if errors:
    print(f"\n8829 INTEGRITY GATE: {len(errors)} FAILURE(S)\n")
    for e in errors:
        print(f"  [X] {e}")
    raise SystemExit(1)
print("\n8829 INTEGRITY GATE: ALL CHECKS PASS")
print(f"  depreciation table (12 months + subsequent) + daycare + SALT cap (2 yrs) + helpers + "
      f"{len(spec['scenarios'])} scenarios re-derived independently.")
