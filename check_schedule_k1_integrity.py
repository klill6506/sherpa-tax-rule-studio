"""Pre-seed math gate for load_1040_schedule_k1 (recipient K-1 router + Schedule E p2).

Run:  poetry run python check_schedule_k1_integrity.py

Independently re-types the Schedule E page-2 aggregation (Part II line 28 cols
g/h/i/j/k → 30/31/32; Part III line 33 cols c/d/e/f → 35/36/37; line 41 = 26 +
32 + 37 + 39 + 40) and the cross-form routing (interest/dividends → 1040 2b/3b/3a;
capital gains → Sch D 5/12; SE → Sch SE; §199A → 8995 2/6), then cross-checks the
loader's shared helpers (route_part_ii / route_part_iii / schedule_e_line41 /
route_interest_dividends / route_capital_gains / route_se_and_qbi) cell-by-cell
against every scenario. The loader and this gate share NO math.

Importing the loader module does NOT seed (READY_TO_SEED is False and seeding only
happens inside Command.handle); this gate is read-only.
"""
import os
import sys
from decimal import Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_schedule_k1 as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def check(name, got, want):
    if D(got) != D(want):
        err(f"{name}: recomputed {got} != authored {want}")


def num(x):
    return float(x if x is not None else 0)


# ── Independent re-type of the page-2 math (NO import of the loader's helpers) ──

def ind_part_ii(k1s):
    """Schedule E Part II line 28 cols + line 32. v1: passive loss excluded (RED)."""
    g = h = i = j = k = 0.0
    deferred = []
    for x in k1s:
        if x.get("source_type") not in ("1065", "1120s"):
            continue
        j += num(x.get("section_179"))
        k += num(x.get("guaranteed_payments"))
        net = num(x.get("ordinary")) + num(x.get("net_rental_re")) + num(x.get("other_rental"))
        if x.get("material_participation"):
            if net >= 0:
                k += net
            else:
                i += net
        else:
            if net >= 0:
                h += net
            else:
                deferred.append(net)
    line30 = h + k
    line32 = line30 + (g + i - j)
    return {"30": line30, "32": line32, "g": g, "h": h, "i": i, "j": j, "k": k,
            "passive_loss_deferred": deferred}


def ind_part_iii(k1s):
    """Schedule E Part III cols + line 37. v1: passive loss excluded (RED)."""
    c = d = e = f = 0.0
    deferred = []
    for x in k1s:
        if x.get("source_type") != "1041":
            continue
        f += num(x.get("other_portfolio"))
        net = num(x.get("business")) + num(x.get("net_rental_re")) + num(x.get("other_rental"))
        if x.get("material_participation"):
            if net >= 0:
                f += net
            else:
                e += net
        else:
            if net >= 0:
                d += net
            else:
                deferred.append(net)
    line35 = d + f
    line36 = c + e
    return {"35": line35, "37": line35 + line36, "c": c, "d": d, "e": e, "f": f,
            "passive_loss_deferred": deferred}


def ind_interest_div(k1s):
    return {"2b": sum(num(x.get("interest")) for x in k1s),
            "3b": sum(num(x.get("ordinary_dividends")) for x in k1s),
            "3a": sum(num(x.get("qualified_dividends")) for x in k1s)}


def ind_capgain(k1s):
    return {"schd_5": sum(num(x.get("net_st_capital_gain")) for x in k1s),
            "schd_12": sum(num(x.get("net_lt_capital_gain")) for x in k1s)}


def ind_se_qbi(k1s):
    return {"sch_se_2": sum(num(x.get("se_earnings")) for x in k1s if x.get("source_type") == "1065"),
            "f8995_2": sum(num(x.get("section_199a_qbi")) for x in k1s),
            "f8995_6": sum(num(x.get("section_199a_reit_ptp")) for x in k1s)}


def ind_diagnostics(k1s):
    """Which D_K1_* fire for this scenario (independent of the loader)."""
    fired = set()
    for x in k1s:
        st = x.get("source_type")
        if st in ("1065", "1120s"):
            net = num(x.get("ordinary")) + num(x.get("net_rental_re")) + num(x.get("other_rental"))
        else:
            net = num(x.get("business")) + num(x.get("net_rental_re")) + num(x.get("other_rental"))
        if not x.get("material_participation") and net < 0:
            fired.add("D_K1_PASSIVE_LOSS")
        if num(x.get("section_1231")) != 0:
            fired.add("D_K1_SEC1231")
        if num(x.get("collectibles_28")) != 0 or num(x.get("unrecap_1250")) != 0:
            fired.add("D_K1_SPECIAL_GAIN")
        if x.get("has_amt_items"):
            fired.add("D_K1_AMT")
        if x.get("basis_at_risk_limited"):
            fired.add("D_K1_BASIS")
        if num(x.get("other_income")) != 0:
            fired.add("D_K1_OTHER")
        if x.get("foreign_taxes"):
            fired.add("D_K1_FOREIGN")
    return fired


# ── 1. Cross-check the loader's shared helpers vs the independent re-type ──
HELPER_SAMPLES = [
    [{"source_type": "1065", "material_participation": True, "ordinary": 50000}],
    [{"source_type": "1065", "material_participation": True, "ordinary": 40000, "guaranteed_payments": 10000, "section_179": 6000}],
    [{"source_type": "1065", "material_participation": False, "ordinary": 12000}],
    [{"source_type": "1065", "material_participation": False, "ordinary": -15000}],
    [{"source_type": "1120s", "material_participation": True, "ordinary": 60000, "se_earnings": 60000}],
    [{"source_type": "1041", "material_participation": False, "business": 9000, "other_portfolio": 1000}],
    [{"source_type": "1041", "material_participation": True, "business": -4000}],
]
for s in HELPER_SAMPLES:
    a, b = m.route_part_ii(s), ind_part_ii(s)
    check(f"route_part_ii.32 {s[0].get('source_type')}", a["32"], b["32"])
    check(f"route_part_ii.30 {s[0].get('source_type')}", a["30"], b["30"])
    a3, b3 = m.route_part_iii(s), ind_part_iii(s)
    check(f"route_part_iii.37 {s[0].get('source_type')}", a3["37"], b3["37"])
    if len(a.get("passive_loss_deferred", [])) != len(b["passive_loss_deferred"]):
        err(f"route_part_ii passive-defer mismatch for {s}")
    ai, bi = m.route_interest_dividends(s), ind_interest_div(s)
    for kk in ("2b", "3a", "3b"):
        check(f"interest_div.{kk}", ai[kk], bi[kk])
    ac, bc = m.route_capital_gains(s), ind_capgain(s)
    for kk in ("schd_5", "schd_12"):
        check(f"capgain.{kk}", ac[kk], bc[kk])
    asq, bsq = m.route_se_and_qbi(s), ind_se_qbi(s)
    for kk in ("sch_se_2", "f8995_2", "f8995_6"):
        check(f"se_qbi.{kk}", asq[kk], bsq[kk])

# line 41 helper
check("schedule_e_line41", m.schedule_e_line41(7000, 30000, 5000), 42000)
check("schedule_e_line41 zeros", m.schedule_e_line41(0, 0, 0), 0)

# ── 2. SCHEDULE_K1 scenarios — independent recompute ──
DIAG_KEYS = {d["diagnostic_id"] for d in m.K1_DIAGNOSTICS}
k1_spec = next(s for s in m.FORMS if s["identity"]["form_number"] == "SCHEDULE_K1")
for s in k1_spec["scenarios"]:
    name = s["scenario_name"].split(" ")[0]
    inp, exp = s["inputs"], s["expected_outputs"]
    k1s = inp["k1s"]
    line26 = inp.get("line26", 0)
    pii, piii = ind_part_ii(k1s), ind_part_iii(k1s)
    line41 = num(line26) + pii["32"] + piii["37"]
    got = {"k1_sche_line32": pii["32"], "k1_sche_line37": piii["37"], "k1_sche_line41": line41}
    got.update(ind_interest_div(k1s))
    got.update(ind_capgain(k1s))
    got.update(ind_se_qbi(k1s))
    fired = ind_diagnostics(k1s)
    for kk, want in exp.items():
        if kk.startswith("D_"):
            if kk not in fired:
                err(f"{name}: expected diagnostic {kk} did not fire (independent recompute)")
            continue
        if kk not in got:
            err(f"{name}.{kk}: no independent recompute mapped")
            continue
        check(f"{name}.{kk}", got[kk], want)

# ── 3. Structural checks (both forms) ──
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
        for kk in sc["expected_outputs"]:
            if kk.startswith("D_") and kk not in diag_ids:
                err(f"{fn}/{sc['scenario_name']}: expects unknown diagnostic {kk}")

fa_ids = [a["assertion_id"] for a in m.FLOW_ASSERTIONS]
if len(fa_ids) != len(set(fa_ids)):
    err("duplicate flow-assertion ids")

# Every K1_FACTS output referenced by a rule output exists as a fact
fact_keys = {f["fact_key"] for f in m.K1_FACTS}
for r in m.K1_RULES:
    for o in r.get("outputs", []):
        if o not in fact_keys:
            err(f"R {r['rule_id']} outputs unknown fact {o}")

# ── Report ──
for spec in m.FORMS:
    fn = spec["identity"]["form_number"]
    print(f"{fn} (facts/rules/lines/diagnostics/scenarios/links):",
          (len(spec["facts"]), len(spec["rules"]), len(spec["lines"]),
           len(spec["diagnostics"]), len(spec["scenarios"]), len(spec["rule_links"])))
print(f"Flow assertions: {len(m.FLOW_ASSERTIONS)}; authority sources: {len(m.AUTHORITY_SOURCES)}")
print("Independently recomputed -- Part II: nonpassive income->(k)->line32; nonpassive loss->(i); passive "
      "income->(h); passive loss EXCLUDED (RED) -> line32=0. Part III (1041): box5->(f), box6/7/8 passive->(d) "
      "/ nonpassive->(f)/(e). line41 = 26+32+37. Interest->2b, div->3b/3a, ST->SchD5, LT->SchD12, 1065-only "
      "SE->SchSE, sec199A->8995 2/6. RED-defer set re-derived per scenario.")

if errors:
    print("\nFAILURES:")
    for e in errors:
        print(f"  X {e}")
    sys.exit(1)
print("\nALL CHECKS PASS")
