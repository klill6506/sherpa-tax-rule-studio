"""Pre-seed math gate for load_1040_form_8615 (Tax for Certain Children Who Have
Unearned Income — the kiddie tax, §1(g)).

Run:  <rs-venv>/Scripts/python.exe check_8615_integrity.py

Independently recomputes every COMPUTABLE scenario from its OWN transcription of
the Form 8615 / §1(g) ASSEMBLY — line 2 (the §63(c)(5)(A) amount), net unearned
income (line 5 = min(line 1 − line 2, line 4)), the parent-rate combination
(line 8 = line 5 + line 6 + line 7), the tentative-tax allocation (line 11 = line 9
− line 10; line 13 = line 11 × line 5 ÷ (line 5 + line 7)), and the §1(g)(1)
greater-of (line 18 = max(line 16, line 17)) — and cross-checks the loader's
year-keyed constants + helpers. The lines 9/10/15/17 tax-at-rate VALUES are
scenario inputs (t_l9, k_parent_tax, t_l15, t_l17): the QDCGT / Tax-Table lookups
are the Ken-approved REUSE of the existing engine (compute_qdcgt_worksheet /
tax_table_lookup), NOT re-derived here — this gate owns the §1(g) assembly. The
SDTW / Schedule J / Form 8814 / not-subject scenarios assert the routing intent.
The loader and this gate share NO math.
"""
import os
from decimal import ROUND_HALF_UP, Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_form_8615 as m  # noqa: E402

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


# ── Independent constants (re-typed from i8615 line 2 / Rev. Proc. 2025-32 §3.02) ──
IND_STD_FLOOR = {2025: 1350, 2026: 1350}     # §63(c)(5)(A) base (unchanged 2026)
IND_LINE2 = {2025: 2700, 2026: 2700}         # line 2 / kiddie threshold = 2 × base


def ind_line2(inp):
    """Line 2 — the §63(c)(5)(A) amount (independent of the loader helper)."""
    year = int(inp.get("tax_year", 2025))
    if inp.get("k_child_itemizes"):
        return D(IND_STD_FLOOR.get(year, 1350)) + D(inp.get("k_child_directly_connected_deductions"))
    return D(IND_LINE2.get(year, 2700))


def recompute(inp):
    """Independent re-derivation of the computable Form 8615 §1(g) assembly.
    The lines 9/10/15/17 tax-at-rate values are inputs (the reused QDCGT / Tax
    Table lookups), not re-derived here."""
    g = lambda k: D(inp.get(k))
    l2 = ind_line2(inp)
    l1 = g("k_child_unearned_income")
    l3 = l1 - l2
    l4 = g("k_child_taxable_income")
    l5 = max(Decimal(0), min(l3, l4))
    l6 = g("k_parent_taxable_income")
    l7 = g("k_other_children_net_unearned")
    l8 = l5 + l6 + l7
    l9 = g("t_l9")
    l10 = g("k_parent_tax")
    l11 = l9 - l10
    l12a = l5 + l7
    l12b = (l5 / l12a) if l12a > 0 else Decimal(0)
    l13 = r0(l11 * l12b)
    l14 = l4 - l5
    l15 = g("t_l15")
    l16 = l13 + l15
    l17 = g("t_l17")
    l18 = max(l16, l17)
    return {"line_2": l2, "line_3": l3, "line_5": l5, "line_8": l8, "line_11": l11,
            "line_12a": l12a, "line_12b": l12b, "line_13": l13, "line_14": l14,
            "line_16": l16, "line_18": l18}


PCT_LINES = {"line_12b"}
DIAG_KEYS = {f"D_8615_{n:03d}" for n in range(1, 8)}

# ── 1. Loader constants vs the independent transcription ──
for yr in (2025, 2026):
    check(f"KIDDIE_STD_FLOOR[{yr}]", m.KIDDIE_STD_FLOOR[yr], IND_STD_FLOOR[yr])
    check(f"KIDDIE_LINE2_AMOUNT[{yr}]", m.KIDDIE_LINE2_AMOUNT[yr], IND_LINE2[yr])
# Line 2 = 2 × the §63(c)(5)(A) base (the kiddie-tax relationship).
for yr in (2025, 2026):
    check(f"line2 == 2 × base [{yr}]", m.KIDDIE_LINE2_AMOUNT[yr], 2 * m.KIDDIE_STD_FLOOR[yr])

# ── 2. Loader helpers vs the independent math ──
for yr in (2025, 2026, 2099):
    if m.kiddie_std_floor_for(yr) != IND_STD_FLOOR.get(yr, 1350):
        err(f"kiddie_std_floor_for({yr}) = {m.kiddie_std_floor_for(yr)} != {IND_STD_FLOOR.get(yr, 1350)}")
    if m.kiddie_line2_for(yr) != IND_LINE2.get(yr, 2700):
        err(f"kiddie_line2_for({yr}) = {m.kiddie_line2_for(yr)} != {IND_LINE2.get(yr, 2700)}")

# ── 3. Scenarios — independent recompute / routing intent ──
spec = m.FORMS[0]
for s in spec["scenarios"]:
    name = s["scenario_name"].split(" ")[0]
    inp, exp = s["inputs"], s["expected_outputs"]

    # SDTW / Schedule J / Form 8814 RED-defer — assert the routing intent, not the numbers.
    if exp.get("D_8615_002") or exp.get("D_8615_003") or exp.get("D_8615_004"):
        flag = {"D_8615_002": "k_sdtw_required", "D_8615_003": "k_uses_schedule_j",
                "D_8615_004": "k_form_8814_election"}
        for dcode, fkey in flag.items():
            if exp.get(dcode) and not inp.get(fkey):
                err(f"{name}: {dcode} expected but no {fkey} input")
        if "line_18" in exp and exp["line_18"] is not None:
            err(f"{name}: a RED-defer scenario must blank line 18 (expected None)")
        continue

    # Not-subject (D_8615_006): line 3 = line 1 − line 2 must be ≤ 0; line 5 = 0.
    if exp.get("D_8615_006"):
        got = recompute(inp)
        if got["line_3"] > 0:
            err(f"{name}: D_8615_006 expected but line 3 ({got['line_3']}) > 0 (child IS subject)")
        check(f"{name}.line_5", got["line_5"], 0)
        if "line_2" in exp:
            check(f"{name}.line_2", got["line_2"], exp["line_2"])
        if "line_3" in exp:
            check(f"{name}.line_3", got["line_3"], exp["line_3"])
        continue

    got = recompute(inp)
    for k, want in exp.items():
        if k in DIAG_KEYS or want is None:
            continue
        if k not in got:
            continue
        if k in PCT_LINES:
            check_close(f"{name}.{k}", got[k], want)
        else:
            check(f"{name}.{k}", got[k], want)


# ── Report ──
if errors:
    print(f"\n8615 INTEGRITY GATE: {len(errors)} FAILURE(S)\n")
    for e in errors:
        print(f"  [X] {e}")
    raise SystemExit(1)
print("\n8615 INTEGRITY GATE: ALL CHECKS PASS")
print(f"  §63(c)(5)(A) base + line-2 threshold (2 yrs) + helpers + "
      f"{len(spec['scenarios'])} scenarios (the §1(g) assembly) re-derived independently.")
