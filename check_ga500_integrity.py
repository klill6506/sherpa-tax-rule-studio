"""Pre-seed math gate for load_ga500_form_500 (Georgia Form 500 — individual
income tax).

Run:  <rs-venv>/Scripts/python.exe check_ga500_integrity.py

Independently recomputes every COMPUTABLE scenario from its OWN transcription of
the Georgia Form 500 assembly — federal-AGI start, Schedule 1 GA additions/
subtractions (the retirement income exclusion standard + military worksheets, the
taxable-SS subtraction), the standard/itemized deduction (the 12b SALT back-out),
the dependent exemption, the Schedule 3 part-year/nonresident proration, the
Schedule 4 GA NOL 80% limitation, the flat tax, the Low Income Credit, and the
IND-CR 202 child-care credit — and cross-checks the loader's year-keyed constants
+ helpers. The loader and this gate share NO math (the loader carries only the
authored scenarios + constants; this gate re-derives them from scratch).
"""
import os
from decimal import ROUND_HALF_UP, Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_ga500_form_500 as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def r0(x):
    """Whole-dollar rounding (the GA form rounds; ROUND_HALF_UP)."""
    return D(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def check(name, got, want):
    if D(got) != D(want):
        err(f"{name}: recomputed {got} != authored {want}")


# ── Independent constants (re-typed from the GA-DOR 2025 Form 500 / IT-511 + HB 463) ──
IND_RATE = {2025: "0.0519", 2026: "0.0499"}
IND_STD_MFJ = {2025: 24000, 2026: 30000}   # HB 463: $30,000 MFJ for TY2026
IND_STD_OTHER = {2025: 12000, 2026: 15000}  # HB 463: $15,000 single/MFS/HOH for TY2026
IND_DEP = {2025: 4000, 2026: 5000}
IND_RIE_62_64 = {2025: 35000, 2026: 35000}
IND_RIE_65 = {2025: 65000, 2026: 65000}
IND_RIE_EARNED_CAP = {2025: 5000, 2026: 5000}
IND_MIL_BASE = {2025: 17500, 2026: 17500}
IND_LIC_CEIL = {2025: 20000, 2026: 20000}
IND_SALT = {2025: 10000, 2026: 10000}
IND_SALT_MFS = {2025: 5000, 2026: 5000}
IND_NOL_PCT = Decimal("0.80")
IND_LIC_TABLE = [(5999, 26), (7999, 20), (9999, 14), (14999, 8), (19999, 5)]


def ind_std(year, fs):
    return D(IND_STD_MFJ[year]) if fs == "B" else D(IND_STD_OTHER[year])


def ind_lic_credit(fagi):
    for ceiling, credit in IND_LIC_TABLE:
        if fagi <= ceiling:
            return credit
    return 0


def _rie(inp, year, prefix):
    """RIE standard worksheet for one person → (exclusion, worksheet dict)."""
    if not inp.get(f"g_{prefix}_rie_applies"):
        return Decimal(0), {}
    earned = D(inp.get(f"g_{prefix}_rie_salary_wages")) + D(inp.get(f"g_{prefix}_rie_other_earned"))
    l5 = max(Decimal(0), min(earned, D(IND_RIE_EARNED_CAP[year])))
    unearned = sum(
        D(inp.get(f"g_{prefix}_rie_{k}"))
        for k in ("interest", "dividends", "alimony", "capital_gains", "other_income", "taxable_ira", "taxable_pension", "rental_etc")
    )
    l14 = max(Decimal(0), unearned)
    l15 = l5 + l14
    cap = D(IND_RIE_65[year]) if inp.get(f"g_{prefix}_age_65_plus") else D(IND_RIE_62_64[year])
    l17 = min(l15, cap)
    return l17, {"RIE-5": l5, "RIE-14": l14, "RIE-15": l15, "RIE-17": l17}


def _mil(inp, year, prefix):
    """Military RIE worksheet for one person → (total exclusion, worksheet dict)."""
    if not inp.get(f"g_{prefix}_military_under62"):
        return Decimal(0), {}
    mret = D(inp.get(f"g_{prefix}_military_retirement"))
    if mret <= 0:
        return Decimal(0), {}
    base = D(IND_MIL_BASE[year])
    l3 = min(mret, base)
    ga_earned = D(inp.get(f"g_{prefix}_military_ga_earned"))
    if mret < 17501 or ga_earned < 17501:
        l7 = Decimal(0)
        l8 = Decimal(0)
    else:
        l7 = base
        l8 = min(mret, l7)
    return l3 + l8, {"MIL-3": l3, "MIL-7": l7, "MIL-8": l8}


def recompute(inp):
    """Independent re-derivation of the computable GA Form 500 assembly."""
    year = int(inp.get("tax_year", 2025))
    fs = inp.get("g_filing_status", "A")
    residency = inp.get("g_residency_status", "full_year")
    out = {}

    fed_agi = D(inp.get("g_federal_agi"))
    out["8"] = fed_agi

    # — Schedule 1 subtractions: RIE (std + military), taxable SS —
    tp_rie, tp_ws = _rie(inp, year, "tp")
    sp_rie, _ = _rie(inp, year, "sp")
    out.update(tp_ws)
    tp_mil, tp_mws = _mil(inp, year, "tp")
    sp_mil, _ = _mil(inp, year, "sp")
    out.update(tp_mws)
    ss = D(inp.get("g_federal_taxable_ss"))
    out["S1-8"] = ss
    s1_7 = tp_rie + sp_rie + tp_mil + sp_mil  # retirement exclusion line (7a-7f)
    out["S1-7"] = s1_7

    additions = sum(D(inp.get(k)) for k in (
        "g_add_non_ga_muni_interest", "g_add_lump_sum", "g_add_depreciation", "g_add_federal_nol", "g_add_other"))
    subtractions = s1_7 + ss + sum(D(inp.get(k)) for k in (
        "g_sub_path2college", "g_sub_us_obligation_interest", "g_sub_depreciation", "g_sub_other"))
    net_adj = additions - subtractions

    dep_exemption = D(IND_DEP[year])
    num_deps = D(inp.get("g_num_dependents"))

    if residency in ("part_year", "nonresident"):
        # — Schedule 3 (3-column proration) —
        a_agi = D(inp.get("g_s3_total_income_federal")) + D(inp.get("g_s3_adj_1040_federal")) + D(inp.get("g_s3_adj_500_federal"))
        c_agi = D(inp.get("g_s3_total_income_ga")) + D(inp.get("g_s3_adj_1040_ga")) + D(inp.get("g_s3_adj_500_ga"))
        out["S3-8"] = a_agi
        if c_agi <= 0:
            ratio = Decimal(0)
        elif a_agi <= 0:
            ratio = Decimal(1)
        else:
            ratio = c_agi / a_agi
        ratio = max(Decimal(0), min(Decimal(1), ratio))
        out["S3-9"] = ratio
        ded = ind_std(year, fs)  # scenarios use the standard deduction for the PY/NR path
        out["S3-10"] = ded
        s3_dep = num_deps * dep_exemption
        out["S3-11"] = s3_dep
        s3_12 = ded + s3_dep
        out["S3-12"] = s3_12
        s3_13 = r0(s3_12 * ratio)
        out["S3-13"] = s3_13
        l15a = c_agi - s3_13
        out["S3-14"] = l15a
    else:
        l9 = net_adj
        out["9"] = l9
        l10 = fed_agi + l9
        out["10"] = l10
        if inp.get("g_itemize"):
            l12a = D(inp.get("g_federal_itemized"))
            ost = D(inp.get("g_other_state_income_tax"))
            l5d = D(inp.get("g_sch_a_line5d_total"))
            cap = D(IND_SALT_MFS[year]) if fs == "C" else D(IND_SALT[year])
            l12b = r0((ost / l5d) * min(l5d, cap)) if l5d > 0 else Decimal(0)
            l12c = l12a - l12b
            out["12a"] = l12a
            out["12b"] = l12b
            out["12c"] = l12c
            ded = l12c
        else:
            ded = ind_std(year, fs)
            out["11"] = ded
        l13 = l10 - ded
        out["13"] = l13
        l14 = num_deps * dep_exemption
        out["14"] = l14
        l15a = l13 - l14

    out["15a"] = l15a

    # — GA NOL 80% limitation —
    nol_pre = D(inp.get("g_nol_carryforward_pre2018"))
    nol_post = D(inp.get("g_nol_carryforward_2018plus"))
    base = max(Decimal(0), l15a)
    pre_applied = min(nol_pre, base)
    remaining = base - pre_applied
    post_applied = min(nol_post, IND_NOL_PCT * base, remaining)
    l15b = pre_applied + post_applied
    out["15b"] = l15b
    l15c = l15a - l15b
    out["15c"] = l15c

    # — tax (flat rate) —
    l16 = r0(max(Decimal(0), l15c) * D(IND_RATE[year]))
    out["16"] = l16

    # — Low Income Credit —
    lic = Decimal(0)
    if fed_agi < D(IND_LIC_CEIL[year]) and inp.get("g_lic_not_dependent") and l16 > 0:
        base_ex = 1 + (1 if fs == "B" else 0) + int(num_deps)
        ex = base_ex + int(D(inp.get("g_lic_age65_count")))
        credit = ind_lic_credit(int(fed_agi))
        out["17a"] = Decimal(ex)
        out["17b"] = Decimal(credit)
        out["17c"] = Decimal(ex * credit)
        lic = Decimal(ex * credit)

    # — IND-CR 202 child & dependent care (50% of federal §21) —
    cc = r0(D(inp.get("g_federal_dependent_care_credit")) * Decimal("0.50"))
    l20 = cc + D(inp.get("g_indcr_other_credits"))
    if cc > 0:
        out["CC-3"] = cc
    if l20 > 0:
        out["20"] = l20

    # — total credits, balance —
    credits = lic + D(inp.get("g_other_state_credit")) + D(inp.get("g_eligible_itemizer_credit")) + l20 + D(inp.get("g_schedule2_credits"))
    l22 = min(credits, l16)
    out["22"] = l22
    out["23"] = max(Decimal(0), l16 - l22)

    # — Payments → balance due / overpayment → amount due / refund —
    l28 = sum((D(inp.get(k)) for k in (
        "g_ga_withholding_wages_1099", "g_ga_withholding_other",
        "g_estimated_payments", "g_refundable_credits_2b")), Decimal(0))
    out["28"] = l28
    out["29"] = max(Decimal(0), out["23"] - l28)   # balance due
    out["30"] = max(Decimal(0), l28 - out["23"])   # overpayment
    # Lines 31-44 reduce the refund / add to the amount due (per the 2025 face):
    #   L45 (amount due)  = L29 + Σ(L32..L44)
    #   L46 (refund)      = max(0, L30 − Σ(L31..L44))
    applied = D(inp.get("g_amount_applied_next_year"))            # L31
    checkoffs = D(inp.get("g_gift_contributions_total"))         # L32-41
    penalties = (D(inp.get("g_uet_penalty"))                    # L42
                 + D(inp.get("g_late_payment_penalty"))         # L43
                 + D(inp.get("g_interest")))                    # L44
    out["45"] = out["29"] + checkoffs + penalties
    out["46"] = max(Decimal(0), out["30"] - applied - checkoffs - penalties)
    return out


# ── 1. Loader constants vs the independent transcription ──
for yr in (2025, 2026):
    check(f"GA_TAX_RATE[{yr}]", m.GA_TAX_RATE[yr], IND_RATE[yr])
    check(f"GA_STD_DED_MFJ[{yr}]", m.GA_STD_DED_MFJ[yr], IND_STD_MFJ[yr])
    check(f"GA_STD_DED_OTHER[{yr}]", m.GA_STD_DED_OTHER[yr], IND_STD_OTHER[yr])
    check(f"GA_DEPENDENT_EXEMPTION[{yr}]", m.GA_DEPENDENT_EXEMPTION[yr], IND_DEP[yr])
    check(f"GA_RIE_62_64[{yr}]", m.GA_RIE_62_64[yr], IND_RIE_62_64[yr])
    check(f"GA_RIE_65[{yr}]", m.GA_RIE_65[yr], IND_RIE_65[yr])
    check(f"GA_RIE_EARNED_CAP[{yr}]", m.GA_RIE_EARNED_CAP[yr], IND_RIE_EARNED_CAP[yr])
    check(f"GA_MILITARY_RIE_BASE[{yr}]", m.GA_MILITARY_RIE_BASE[yr], IND_MIL_BASE[yr])
    check(f"GA_LIC_FAGI_CEILING[{yr}]", m.GA_LIC_FAGI_CEILING[yr], IND_LIC_CEIL[yr])
    check(f"GA_SALT_CAP[{yr}]", m.GA_SALT_CAP[yr], IND_SALT[yr])
    check(f"GA_SALT_CAP_MFS[{yr}]", m.GA_SALT_CAP_MFS[yr], IND_SALT_MFS[yr])
check("GA_NOL_LIMIT_PCT", m.GA_NOL_LIMIT_PCT, IND_NOL_PCT)

# ── 2. Loader helpers vs the independent math ──
for yr in (2025, 2026, 2099):
    if m.ga_rate_for(yr) != (IND_RATE.get(yr) or IND_RATE[2026]):
        err(f"ga_rate_for({yr}) = {m.ga_rate_for(yr)}")
    if m.ga_std_ded_for(yr, "B") != (IND_STD_MFJ.get(yr) or IND_STD_MFJ[2026]):
        err(f"ga_std_ded_for({yr}, B) = {m.ga_std_ded_for(yr, 'B')}")
    if m.ga_std_ded_for(yr, "A") != (IND_STD_OTHER.get(yr) or IND_STD_OTHER[2026]):
        err(f"ga_std_ded_for({yr}, A) = {m.ga_std_ded_for(yr, 'A')}")
    if m.ga_dependent_exemption_for(yr) != (IND_DEP.get(yr) or IND_DEP[2026]):
        err(f"ga_dependent_exemption_for({yr}) = {m.ga_dependent_exemption_for(yr)}")
    if m.ga_rie_max_for(yr, True) != (IND_RIE_65.get(yr) or IND_RIE_65[2026]):
        err(f"ga_rie_max_for({yr}, 65+) = {m.ga_rie_max_for(yr, True)}")
    if m.ga_rie_max_for(yr, False) != (IND_RIE_62_64.get(yr) or IND_RIE_62_64[2026]):
        err(f"ga_rie_max_for({yr}, 62-64) = {m.ga_rie_max_for(yr, False)}")

for fagi, want in [(5000, 26), (7000, 20), (9000, 14), (12000, 8), (18000, 5), (25000, 0)]:
    if m.ga_lic_credit_for(fagi) != want:
        err(f"ga_lic_credit_for({fagi}) = {m.ga_lic_credit_for(fagi)} != {want}")

# ── 3. Scenarios — independent recompute ──
spec = m.FORMS[0]
for s in spec["scenarios"]:
    name = s["scenario_name"].split(" ")[0]
    inp, exp = s["inputs"], s["expected_outputs"]
    got = recompute(inp)
    for k, want in exp.items():
        if want is None:
            continue
        if k not in got:
            err(f"{name}: expected key '{k}' not produced by recompute (authored {want})")
            continue
        check(f"{name}.{k}", got[k], want)


# ── Report ──
if errors:
    print(f"\nGA500 INTEGRITY GATE: {len(errors)} FAILURE(S)\n")
    for e in errors:
        print(f"  [X] {e}")
    raise SystemExit(1)
print("\nGA500 INTEGRITY GATE: ALL CHECKS PASS")
print(f"  constants (2 yrs) + helpers + LIC table + {len(spec['scenarios'])} scenarios "
      f"(the GA Form 500 assembly: Sch 1 / RIE std+military / deduction / Sch 3 / NOL 80% / "
      f"flat tax / LIC / child-care) re-derived independently.")
