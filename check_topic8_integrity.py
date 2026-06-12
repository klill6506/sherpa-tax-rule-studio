"""Pre-seed content checker for load_1040_schedule_c (Topic 8 — Schedule C / SE /
8995 / 8959).

Run:  poetry run python check_topic8_integrity.py

Mirrors check_eic_integrity.py / check_retirement_integrity.py: validates the
authored lists WITHOUT touching the DB, then INDEPENDENTLY recomputes every
numeric scenario from its OWN transcription of the form math (not imported from
the loader) — Schedule SE Part I (incl. the W-2-SS-wage cap interaction), the
Schedule C gross-income / COGS / simplified-home-office chain, the Form 8995 QBI
reduction + income limitation, and the Form 8959 reduced-threshold math. This is
the MATH GATE that must pass before Ken's review walk.

The checker carries its OWN independent copies of the year-keyed constants (SE
wage base, 8995 thresholds) and statutory rates, re-typed from the brief's cited
sources, and cross-checks the loader's module constants cell-by-cell — so a
transcription error in the loader cannot also pass the checker.

Rounding convention: each currency line is rounded to the cent with ROUND_HALF_UP
(the campaign's quantize convention). Settled definitively at the compute leg vs
real TaxWise returns; the cent-level mode is below the to-the-dollar match bar.
"""
import os
import sys
from decimal import Decimal, ROUND_HALF_UP

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_schedule_c as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def cents(x):
    return D(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def check(name, got, want):
    if D(got) != D(want):
        err(f"{name}: recomputed {got} != authored {want}")


# ═══════════════════════════════════════════════════════════════════════════
# INDEPENDENT CONSTANTS (re-typed from the brief's cited sources; NOT imported)
# ═══════════════════════════════════════════════════════════════════════════

IND_SE_WAGE_BASE = {2025: 176100, 2026: 184500}          # Sch SE L7 (2025) / Topic 751 + SSA (2026)
IND_SE_FACTOR = Decimal("0.9235")                         # Sch SE L4a
IND_SE_SS_RATE = Decimal("0.124")                         # Sch SE L10
IND_SE_MEDICARE_RATE = Decimal("0.029")                   # Sch SE L11
IND_SE_HALF = Decimal("0.50")                             # Sch SE L13
IND_SE_FLOOR = 400                                        # Sch SE L4c

IND_ADDL_MED_RATE = Decimal("0.009")                      # 8959 (0.9%)
IND_REG_MED_RATE = Decimal("0.0145")                      # 8959 L21 (1.45%)
IND_ADDL_MED_THRESHOLDS = {"mfj": 250000, "mfs": 125000, "other": 200000}  # i8959 (non-indexed)

IND_QBI_RATE = Decimal("0.20")                            # 8995 (§199A 20%)
IND_QBI_THRESHOLDS = {
    2025: {"mfj": 394600, "mfs": 197300, "other": 197300},   # i8995 (2025)
    2026: {"mfj": 403500, "mfs": 201775, "other": 201750},   # RP 2025-32 §4.26
}

IND_HOME_OFFICE_RATE = 5                                   # $/sqft (Rev. Proc. 2013-13)
IND_HOME_OFFICE_MAX_SQFT = 300


def status_key(status: str) -> str:
    """single / HOH / QSS map to 'other'; mfj / mfs keep their own column."""
    return status if status in ("mfj", "mfs") else "other"


# ═══════════════════════════════════════════════════════════════════════════
# Independent recomputations of the form math
# ═══════════════════════════════════════════════════════════════════════════

def se_part_i(net_profit, w2_ss_wages=0, year=2025, farm_1a=0, crp_1b=0):
    """Schedule SE Part I standard method -> dict of line values (cents)."""
    l3 = D(farm_1a) + D(crp_1b) + D(net_profit)
    l4a = cents(l3 * IND_SE_FACTOR) if l3 > 0 else cents(l3)
    l4c = l4a  # L4b optional = 0 in v1
    out = {"3": l3, "4a": l4a, "4c": l4c}
    if l4c < IND_SE_FLOOR:
        out.update({"6": Decimal("0"), "10": Decimal("0"), "11": Decimal("0"),
                    "12": Decimal("0"), "13": Decimal("0"), "stop": True})
        return out
    l6 = l4c  # L5b church = 0 in v1
    l7 = D(IND_SE_WAGE_BASE[year])
    l8d = D(w2_ss_wages)
    l9 = max(Decimal("0"), l7 - l8d)
    l10 = cents(min(l6, l9) * IND_SE_SS_RATE)
    l11 = cents(l6 * IND_SE_MEDICARE_RATE)
    l12 = cents(l10 + l11)
    l13 = cents(l12 * IND_SE_HALF)
    out.update({"6": l6, "7": l7, "9": l9, "10": l10, "11": l11, "12": l12, "13": l13, "stop": False})
    return out


def sched_c(line_1=0, line_2=0, line_4=0, line_6=0, line_28=0,
            cogs=None, use_simplified=False, home_sqft=0):
    """Schedule C income/expense/home-office/net chain -> dict."""
    out = {}
    if cogs is not None:
        l40 = sum(D(cogs.get(k, 0)) for k in ("35", "36", "37", "38", "39"))
        l42 = l40 - D(cogs.get("41", 0))
        out["40"] = l40
        out["42"] = l42
        line_4 = l42
    l3 = D(line_1) - D(line_2)
    l5 = l3 - D(line_4)
    l7 = l5 + D(line_6)
    l29 = l7 - D(line_28)
    if use_simplified and home_sqft:
        raw = D(min(int(home_sqft), IND_HOME_OFFICE_MAX_SQFT)) * D(IND_HOME_OFFICE_RATE)
        l30 = min(raw, max(Decimal("0"), l29))
    else:
        l30 = Decimal("0")
    l31 = l29 - l30
    out.update({"3": l3, "4": D(line_4), "5": l5, "7": l7, "29": l29, "30": l30, "31": l31})
    return out


def qbi_8995(qbi=0, taxable_before=0, net_cap_gain=0, reit_ptp=0,
             qbi_cf_prior=0, reit_cf_prior=0):
    """Form 8995 lines 2-15 -> dict (single-business QBI passed directly)."""
    l2 = D(qbi)
    l4 = max(Decimal("0"), l2 + D(qbi_cf_prior))
    l5 = cents(l4 * IND_QBI_RATE)
    l8 = max(Decimal("0"), D(reit_ptp) + D(reit_cf_prior))
    l9 = cents(l8 * IND_QBI_RATE)
    l10 = l5 + l9
    l11 = D(taxable_before)
    l12 = D(net_cap_gain)
    l13 = max(Decimal("0"), l11 - l12)
    l14 = cents(l13 * IND_QBI_RATE)
    l15 = min(l10, l14)
    return {"2": l2, "4": l4, "5": l5, "8": l8, "9": l9, "10": l10,
            "11": l11, "12": l12, "13": l13, "14": l14, "15": l15}


def amt_8959(medicare_wages=0, se_income=0, year=2025, status="single", withheld=0):
    """Form 8959 Parts I/II/V -> dict. Threshold reduced by Medicare wages in Part II."""
    thr = D(IND_ADDL_MED_THRESHOLDS[status_key(status)])
    l4 = D(medicare_wages)
    l6 = max(Decimal("0"), l4 - thr)
    l7 = cents(l6 * IND_ADDL_MED_RATE)
    l8 = max(Decimal("0"), D(se_income))
    l11 = max(Decimal("0"), thr - l4)        # threshold reduced by Medicare wages
    l12 = max(Decimal("0"), l8 - l11)
    l13 = cents(l12 * IND_ADDL_MED_RATE)
    l18 = cents(l7 + l13)                     # L17 RRTA = 0 in v1
    l20 = l4 if False else D(medicare_wages)  # L20 = L1 (== medicare_wages here)
    l21 = cents(l20 * IND_REG_MED_RATE)
    l22 = max(Decimal("0"), D(withheld) - l21)
    l24 = cents(l22)                          # L23 RRTA = 0 in v1
    engaged = (l4 + l8) > thr
    return {"4": l4, "6": l6, "7": l7, "8": l8, "11": l11, "12": l12, "13": l13,
            "18": l18, "21": l21, "22": l22, "24": l24, "engaged": engaged}


# ═══════════════════════════════════════════════════════════════════════════
# Structural checks (mirror check_eic_integrity.py)
# ═══════════════════════════════════════════════════════════════════════════

for spec in m.FORMS:
    fn = spec["identity"]["form_number"]

    fact_keys = [f["fact_key"] for f in spec["facts"]]
    if len(fact_keys) != len(set(fact_keys)):
        dupes = sorted({k for k in fact_keys if fact_keys.count(k) > 1})
        err(f"{fn}: duplicate fact keys {dupes}")

    rule_ids = [r["rule_id"] for r in spec["rules"]]
    if len(rule_ids) != len(set(rule_ids)):
        err(f"{fn}: duplicate rule ids")

    line_nos = [ln["line_number"] for ln in spec["lines"]]
    if len(line_nos) != len(set(line_nos)):
        dupes = sorted({k for k in line_nos if line_nos.count(k) > 1})
        err(f"{fn}: duplicate line numbers {dupes}")

    diag_ids = [d["diagnostic_id"] for d in spec["diagnostics"]]
    if len(diag_ids) != len(set(diag_ids)):
        err(f"{fn}: duplicate diagnostic ids")

    linked = {rid for rid, *_ in spec["rule_links"]}
    uncited = [rid for rid in rule_ids if rid not in linked]
    if uncited:
        err(f"{fn}: uncited rules {uncited}")
    dangling = [rid for rid in linked if rid not in rule_ids]
    if dangling:
        err(f"{fn}: rule_links reference unknown rules {dangling}")

    for r in spec["rules"]:
        for key in r.get("inputs", []):
            if key not in fact_keys:
                err(f"{fn} {r['rule_id']}: input '{key}' is not a declared fact")

    for f in spec["facts"]:
        if f["data_type"] == "choice" and not f.get("choices"):
            err(f"{fn} fact {f['fact_key']}: choice type without choices")

# ── flow assertions ──
fa_ids = [a["assertion_id"] for a in m.FLOW_ASSERTIONS]
if len(fa_ids) != len(set(fa_ids)):
    err("duplicate flow assertion ids")
for a in m.FLOW_ASSERTIONS:
    if len(a["assertion_id"]) > 20:
        err(f"assertion_id too long (>20): {a['assertion_id']}")


# ═══════════════════════════════════════════════════════════════════════════
# Loader constants cross-check (loader module constants == independent copies)
# ═══════════════════════════════════════════════════════════════════════════

for year in (2025, 2026):
    if D(m.SE_WAGE_BASE[year]) != D(IND_SE_WAGE_BASE[year]):
        err(f"SE_WAGE_BASE[{year}] loader {m.SE_WAGE_BASE[year]} != independent {IND_SE_WAGE_BASE[year]}")
    for st in ("mfj", "mfs", "other"):
        if D(m.QBI_THRESHOLDS[year][st]) != D(IND_QBI_THRESHOLDS[year][st]):
            err(f"QBI_THRESHOLDS[{year}][{st}] loader {m.QBI_THRESHOLDS[year][st]} != independent {IND_QBI_THRESHOLDS[year][st]}")

for st in ("mfj", "mfs", "other"):
    if D(m.ADDL_MEDICARE_THRESHOLDS[st]) != D(IND_ADDL_MED_THRESHOLDS[st]):
        err(f"ADDL_MEDICARE_THRESHOLDS[{st}] loader {m.ADDL_MEDICARE_THRESHOLDS[st]} != independent {IND_ADDL_MED_THRESHOLDS[st]}")

for nm, lv, iv in (
    ("SE_NET_EARNINGS_FACTOR", m.SE_NET_EARNINGS_FACTOR, IND_SE_FACTOR),
    ("SE_SS_RATE", m.SE_SS_RATE, IND_SE_SS_RATE),
    ("SE_MEDICARE_RATE", m.SE_MEDICARE_RATE, IND_SE_MEDICARE_RATE),
    ("SE_HALF_DEDUCTION_RATE", m.SE_HALF_DEDUCTION_RATE, IND_SE_HALF),
    ("SE_FILING_FLOOR", m.SE_FILING_FLOOR, IND_SE_FLOOR),
    ("ADDL_MEDICARE_RATE", m.ADDL_MEDICARE_RATE, IND_ADDL_MED_RATE),
    ("REGULAR_MEDICARE_RATE", m.REGULAR_MEDICARE_RATE, IND_REG_MED_RATE),
    ("QBI_RATE", m.QBI_RATE, IND_QBI_RATE),
    ("HOME_OFFICE_RATE", m.HOME_OFFICE_RATE, IND_HOME_OFFICE_RATE),
    ("HOME_OFFICE_MAX_SQFT", m.HOME_OFFICE_MAX_SQFT, IND_HOME_OFFICE_MAX_SQFT),
):
    if Decimal(str(lv)) != Decimal(str(iv)):
        err(f"{nm} loader {lv} != independent {iv}")


# ═══════════════════════════════════════════════════════════════════════════
# Scenario lookup (key on the first token of scenario_name)
# ═══════════════════════════════════════════════════════════════════════════

s = {sc["scenario_name"].split(" ")[0]: sc for spec in m.FORMS for sc in spec["scenarios"]}


def i_of(key):
    return s[key]["inputs"]


def o_of(key):
    return s[key]["expected_outputs"]


# ── Schedule C ──
i, o = i_of("SC-T1"), o_of("SC-T1")
r = sched_c(line_1=i["line_1"], line_2=i["line_2"], line_4=i["line_4"], line_6=i["line_6"],
            line_28=i["line_28"], home_sqft=i["sc_home_office_sqft"])
check("SC-T1 L7", r["7"], o["line_7"]); check("SC-T1 L29", r["29"], o["line_29"])
check("SC-T1 L30", r["30"], o["line_30"]); check("SC-T1 L31", r["31"], o["line_31"])

i, o = i_of("SC-T2"), o_of("SC-T2")
r = sched_c(line_1=i["line_1"], line_2=i["line_2"], line_6=i["line_6"], line_28=i["line_28"],
            cogs={k.replace("line_", ""): v for k, v in i.items() if k.startswith("line_3") or k == "line_41"},
            home_sqft=i["sc_home_office_sqft"])
check("SC-T2 L40", r["40"], o["line_40"]); check("SC-T2 L42", r["42"], o["line_42"])
check("SC-T2 L4", r["4"], o["line_4"]); check("SC-T2 L5", r["5"], o["line_5"])
check("SC-T2 L7", r["7"], o["line_7"]); check("SC-T2 L29", r["29"], o["line_29"]); check("SC-T2 L31", r["31"], o["line_31"])

i, o = i_of("SC-T3"), o_of("SC-T3")
r = sched_c(line_1=i["line_1"], line_2=i["line_2"], line_4=i["line_4"], line_6=i["line_6"],
            line_28=i["line_28"], use_simplified=i["sc_use_simplified_home_office"], home_sqft=i["sc_home_office_sqft"])
check("SC-T3 L29", r["29"], o["line_29"]); check("SC-T3 L30 (300 cap)", r["30"], o["line_30"]); check("SC-T3 L31", r["31"], o["line_31"])
if i["sc_home_office_sqft"] <= 300:
    err("SC-T3: fixture sqft must exceed 300 to exercise the cap (D_SC_004)")

i, o = i_of("SC-T4"), o_of("SC-T4")
r = sched_c(line_1=i["line_1"], line_2=i["line_2"], line_4=i["line_4"], line_6=i["line_6"],
            line_28=i["line_28"], use_simplified=i["sc_use_simplified_home_office"], home_sqft=i["sc_home_office_sqft"])
check("SC-T4 L29", r["29"], o["line_29"]); check("SC-T4 L30 (gross-income limited)", r["30"], o["line_30"]); check("SC-T4 L31", r["31"], o["line_31"])
raw = D(min(i["sc_home_office_sqft"], 300)) * 5
if not (raw > r["29"]):
    err(f"SC-T4: gross-income limitation not load-bearing (raw {raw} not > L29 {r['29']})")

i, o = i_of("SC-T5"), o_of("SC-T5")
r = sched_c(line_1=i["line_1"], line_2=i["line_2"], line_4=i["line_4"], line_6=i["line_6"],
            line_28=i["line_28"], home_sqft=i["sc_home_office_sqft"])
check("SC-T5 L29", r["29"], o["line_29"]); check("SC-T5 L30 (loss -> 0)", r["30"], o["line_30"]); check("SC-T5 L31", r["31"], o["line_31"])
if r["31"] >= 0:
    err("SC-T5: fixture should produce a net loss (D_SC_006)")

# SC-T6/T7 are RED-gate fixtures — assert the gate condition is set.
if i_of("SC-T6").get("sc_statutory_employee") is not True:
    err("SC-T6: fixture must set sc_statutory_employee for D_SC_001")
if i_of("SC-T7").get("sc_some_not_at_risk") is not True:
    err("SC-T7: fixture must set sc_some_not_at_risk for D_SC_002")

# ── Schedule SE ──
i, o = i_of("SE-T1"), o_of("SE-T1")
r = se_part_i(i["line_2"], i["se_w2_ss_wages_l8a"], i["tax_year"])
for ln in ("4a", "6", "10", "11", "12", "13"):
    check(f"SE-T1 L{ln}", r[ln], o[f"line_{ln}"])

i, o = i_of("SE-T2"), o_of("SE-T2")
r = se_part_i(i["line_2"], i["se_w2_ss_wages_l8a"], i["tax_year"])
for ln in ("4a", "6", "7", "9", "10", "11", "12"):
    check(f"SE-T2 L{ln}", r[ln], o[f"line_{ln}"])
if not (r["9"] < r["6"]):  # the W-2-SS-wage cap binds (line 10 uses line 9, not line 6)
    err("SE-T2: W-2-SS-wage cap not load-bearing (line 9 not < line 6)")
if r["10"] != cents(r["9"] * IND_SE_SS_RATE):
    err("SE-T2: line 10 did not use the capped line 9")

i, o = i_of("SE-T3"), o_of("SE-T3")
r = se_part_i(i["line_2"], i["se_w2_ss_wages_l8a"], i["tax_year"])
check("SE-T3 L4a", r["4a"], o["line_4a"]); check("SE-T3 L4c", r["4c"], o["line_4c"]); check("SE-T3 L12", r["12"], o["line_12"])
if not r["stop"]:
    err("SE-T3: $400 floor not load-bearing (did not stop)")

i, o = i_of("SE-T4"), o_of("SE-T4")
r = se_part_i(i["line_2"], i["se_w2_ss_wages_l8a"], i["tax_year"])
for ln in ("4a", "6", "7", "9", "10", "11", "12"):
    check(f"SE-T4 L{ln}", r[ln], o[f"line_{ln}"])
if D(IND_SE_WAGE_BASE[2026]) == D(IND_SE_WAGE_BASE[2025]):
    err("SE-T4: SE wage base year-keying not load-bearing (2025 == 2026)")
if r["10"] != cents(D(IND_SE_WAGE_BASE[2026]) * IND_SE_SS_RATE):
    err("SE-T4: line 10 did not cap at the 2026 wage base")

i, o = i_of("SE-T5"), o_of("SE-T5")
r = se_part_i(i["line_2"], i["se_w2_ss_wages_l8a"], i["tax_year"])
check("SE-T5 L4a", r["4a"], o["line_4a"]); check("SE-T5 L12", r["12"], o["line_12"]); check("SE-T5 L13", r["13"], o["line_13"])
if r["13"] != cents(r["12"] * IND_SE_HALF):
    err("SE-T5: line 13 != line 12 x 50%")

# ── Form 8995 ──
i, o = i_of("8995-T1"), o_of("8995-T1")
r = qbi_8995(qbi=i["qbi_business_qbi"], taxable_before=i["qbi_taxable_income_before_qbi"], net_cap_gain=i["qbi_net_capital_gain"])
for ln in ("2", "5", "10", "13", "14", "15"):
    check(f"8995-T1 L{ln}", r[ln], o[f"line_{ln}"])

i, o = i_of("8995-T2"), o_of("8995-T2")
qbi_reduced = D(i["sch_c_net_profit"]) - D(i["half_se_tax"]) - D(i["sehi"])
check("8995-T2 QBI reduced", qbi_reduced, o["qbi_business_qbi"])
r = qbi_8995(qbi=qbi_reduced, taxable_before=i["qbi_taxable_income_before_qbi"], net_cap_gain=i["qbi_net_capital_gain"])
check("8995-T2 L5", r["5"], o["line_5"]); check("8995-T2 L15", r["15"], o["line_15"])

i, o = i_of("8995-T3"), o_of("8995-T3")
r = qbi_8995(qbi=i["qbi_business_qbi"], taxable_before=i["qbi_taxable_income_before_qbi"], net_cap_gain=i["qbi_net_capital_gain"])
for ln in ("10", "13", "14", "15"):
    check(f"8995-T3 L{ln}", r[ln], o[f"line_{ln}"])
if not (r["14"] < r["10"]):
    err("8995-T3: income limitation not binding (L14 not < L10)")

i, o = i_of("8995-T4"), o_of("8995-T4")
r = qbi_8995(qbi=i["qbi_business_qbi"], reit_ptp=i["qbi_reit_ptp_income"], taxable_before=i["qbi_taxable_income_before_qbi"], net_cap_gain=i["qbi_net_capital_gain"])
for ln in ("8", "9", "10", "15"):
    check(f"8995-T4 L{ln}", r[ln], o[f"line_{ln}"])

# 8995-T5: above threshold -> Form 8995-A (gate). Assert the fixture exceeds the year/status threshold.
i = i_of("8995-T5")
thr5 = D(IND_QBI_THRESHOLDS[i["tax_year"]][status_key(i["filing_status"])])
if not (D(i["qbi_taxable_income_before_qbi"]) > thr5):
    err(f"8995-T5: taxable income {i['qbi_taxable_income_before_qbi']} does not exceed threshold {thr5} (D_8995_001 would not fire)")

i, o = i_of("8995-T6"), o_of("8995-T6")
r = qbi_8995(qbi=i["qbi_business_qbi"], taxable_before=i["qbi_taxable_income_before_qbi"], net_cap_gain=i["qbi_net_capital_gain"])
for ln in ("10", "13", "14", "15"):
    check(f"8995-T6 L{ln}", r[ln], o[f"line_{ln}"])
if not (D(i["qbi_net_capital_gain"]) > 0 and r["13"] == D(i["qbi_taxable_income_before_qbi"]) - D(i["qbi_net_capital_gain"])):
    err("8995-T6: net capital gain not load-bearing in the income limitation")

# 8995-T7: TY2026 threshold allows what TY2025 would block (year-keying load-bearing).
i, o = i_of("8995-T7"), o_of("8995-T7")
thr26 = D(IND_QBI_THRESHOLDS[2026][status_key(i["filing_status"])])
thr25 = D(IND_QBI_THRESHOLDS[2025][status_key(i["filing_status"])])
ti = D(i["qbi_taxable_income_before_qbi"])
if not (ti <= thr26 and ti > thr25):
    err(f"8995-T7: year-keying not load-bearing (ti {ti}; 2026 thr {thr26}; 2025 thr {thr25})")
check("8995-T7 L5", cents(D(i["qbi_business_qbi"]) * IND_QBI_RATE), o["line_5"])

# ── Form 8959 ──
i, o = i_of("8959-T1"), o_of("8959-T1")
r = amt_8959(medicare_wages=i["amt_medicare_wages_l1"], se_income=i["amt_se_income_l8"], year=i["tax_year"], status=i["filing_status"])
for ln in ("4", "6", "7", "18"):
    check(f"8959-T1 L{ln}", r[ln], o[f"line_{ln}"])

i, o = i_of("8959-T2"), o_of("8959-T2")
r = amt_8959(medicare_wages=i["amt_medicare_wages_l1"], se_income=i["amt_se_income_l8"], year=i["tax_year"], status=i["filing_status"])
for ln in ("11", "12", "13", "18"):
    check(f"8959-T2 L{ln}", r[ln], o[f"line_{ln}"])

i, o = i_of("8959-T3"), o_of("8959-T3")
r = amt_8959(medicare_wages=i["amt_medicare_wages_l1"], se_income=i["amt_se_income_l8"], year=i["tax_year"], status=i["filing_status"])
for ln in ("6", "7", "11", "12", "13", "18"):
    check(f"8959-T3 L{ln}", r[ln], o[f"line_{ln}"])
# the load-bearing nuance: line 11 = threshold - line 4 (shared threshold)
thr3 = D(IND_ADDL_MED_THRESHOLDS[status_key(i["filing_status"])])
if r["11"] != max(Decimal("0"), thr3 - r["4"]):
    err("8959-T3: Part II threshold not reduced by Medicare wages (line 11 != threshold - line 4)")

i, o = i_of("8959-T4"), o_of("8959-T4")
r = amt_8959(medicare_wages=i["amt_medicare_wages_l1"], se_income=i["amt_se_income_l8"], year=i["tax_year"], status=i["filing_status"])
check("8959-T4 L18 (below threshold)", r["18"], o["line_18"])
if r["engaged"]:
    err("8959-T4: fixture should be below the threshold (engage gate should be False)")

i, o = i_of("8959-T5"), o_of("8959-T5")
r = amt_8959(medicare_wages=i["amt_medicare_wages_l1"], year=i["tax_year"], status=i["filing_status"], withheld=i["amt_medicare_withheld_l19"])
check("8959-T5 L21", r["21"], o["line_21"]); check("8959-T5 L22", r["22"], o["line_22"]); check("8959-T5 L24", r["24"], o["line_24"])


# ═══════════════════════════════════════════════════════════════════════════
# Load-bearing checks on the flow-assertion constants_checks
# ═══════════════════════════════════════════════════════════════════════════

def fa(aid):
    return next((a for a in m.FLOW_ASSERTIONS if a["assertion_id"] == aid), None)

a = fa("FA-1040-SCHSE-03")
if a:
    c = a["definition"]["constants"]
    if D(c["wage_base_2025"]) != D(IND_SE_WAGE_BASE[2025]) or D(c["wage_base_2026"]) != D(IND_SE_WAGE_BASE[2026]):
        err("FA-SCHSE-03: wage base constants disagree with independent")
    if c.get("applies_to_years") != [2025, 2026]:
        err("FA-SCHSE-03: applies_to_years != [2025, 2026]")
else:
    err("FA-1040-SCHSE-03 not found")

a = fa("FA-1040-8995-03")
if a:
    c = a["definition"]["constants"]
    for year in (2025, 2026):
        for st in ("mfj", "mfs", "other"):
            if D(c[str(year)][st]) != D(IND_QBI_THRESHOLDS[year][st]):
                err(f"FA-8995-03: threshold[{year}][{st}] disagrees with independent")
    if D(c["rate"]) != IND_QBI_RATE:
        err("FA-8995-03: QBI rate != 0.20")
else:
    err("FA-1040-8995-03 not found")

a = fa("FA-1040-8959-03")
if a:
    c = a["definition"]["constants"]
    for st in ("mfj", "mfs", "other"):
        if D(c[st]) != D(IND_ADDL_MED_THRESHOLDS[st]):
            err(f"FA-8959-03: threshold[{st}] disagrees with independent")
    if D(c["rate"]) != IND_ADDL_MED_RATE:
        err("FA-8959-03: 0.9% rate mismatch")
else:
    err("FA-1040-8959-03 not found")


# ═══════════════════════════════════════════════════════════════════════════
# Report
# ═══════════════════════════════════════════════════════════════════════════

counts = {spec["identity"]["form_number"]: (len(spec["facts"]), len(spec["rules"]),
          len(spec["lines"]), len(spec["diagnostics"]), len(spec["scenarios"]),
          len(spec["rule_links"])) for spec in m.FORMS}

print("Per-form counts (facts/rules/lines/diagnostics/scenarios/links):")
for fn, c in counts.items():
    print(f"  {fn}: {c}")
print(f"Flow assertions: {len(m.FLOW_ASSERTIONS)}")
print(f"Authority sources (new): {len(m.AUTHORITY_SOURCES)}; topics: {len(m.AUTHORITY_TOPICS)}; "
      f"new excerpts on existing: {len(m.NEW_EXCERPTS_ON_EXISTING)}")
print("Independently recomputed: SC-T1..T7 (gross profit / COGS / simplified home office / loss), "
      "SE-T1..T5 (92.35% / SS cap / Medicare / $400 floor / 1/2-SE; both years), 8995-T1..T7 (QBI "
      "reduction / income limitation / REIT-PTP / above-threshold gate / year-keying), 8959-T1..T5 "
      "(wages / SE threshold-reduced-by-wages / shared threshold / engage gate / withholding); "
      "loader constants cross-checked vs an independent transcription.")

if errors:
    print("\nFAILURES:")
    for e in errors:
        print(f"  X {e}")
    sys.exit(1)
print("\nALL CHECKS PASS")
