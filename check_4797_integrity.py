"""Pre-seed math gate for load_4797 (Sales of Business Property, Broad v1).

Run:  poetry run python check_4797_integrity.py

Independently recomputes every scenario from its OWN transcription of the §1245/§1250/
§1252/§1254/§1255 recapture, the §1231 netting + §1231(c) 5-year lookback, and the Part IV
§179/§280F recapture. The loader and this gate share NO math — both must agree with the
authored expected_outputs.
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from decimal import ROUND_HALF_UP, Decimal  # noqa: E402

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_4797 as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def check(name, got, want):
    if D(got) != D(want):
        err(f"{name}: recomputed {got} != authored {want}")


_PART3 = {"1245", "1250", "1252", "1254", "1255"}


# ── Independent per-property recapture (re-typed, shares no code with the loader) ──
def ind_property(p):
    sp = D(p.get("sales_price"))
    basis = D(p.get("cost_basis")) + D(p.get("expense_of_sale"))
    depr = D(p.get("depreciation_allowed"))
    gain = sp - (basis - depr)                       # L24 = L20 − (L21 − L22)
    months = int(p.get("holding_period_months") or 0)
    ptype = p.get("property_type", "1231")
    if months <= 12:
        return {"bucket": "st", "ordinary": D(0), "s1231": D(0), "ur1250": D(0), "st_ord": gain}
    if gain <= 0 or ptype not in _PART3:
        return {"bucket": "p1", "ordinary": D(0), "s1231": gain, "ur1250": D(0), "st_ord": D(0)}
    ordinary = D(0)
    ur1250 = D(0)
    if ptype == "1245":
        ordinary = min(gain, depr)
    elif ptype == "1250":
        addl = D(p.get("additional_depreciation"))
        pct = D(p.get("applicable_pct_1250", 1))
        ordinary = pct * min(gain, addl)
        ur1250 = max(D(0), min(gain, depr) - ordinary)
    elif ptype == "1252":
        ordinary = min(gain, D(p.get("section_1252_deductions")) * D(p.get("section_1252_pct")))
    elif ptype == "1254":
        ordinary = min(gain, D(p.get("section_1254_costs")))
    elif ptype == "1255":
        ordinary = min(gain, D(p.get("section_1255_excluded")) * D(p.get("section_1255_pct")))
    ordinary = max(D(0), ordinary)
    return {"bucket": "p3", "ordinary": ordinary, "s1231": gain - ordinary, "ur1250": ur1250, "st_ord": D(0)}


def ind_compute(properties=None, nonrecaptured_1231_losses=0, part1_line2_direct=0,
                part4_section_179_recapture=0, part4_section_280f_recapture=0,
                has_form_4684=False, has_form_6252=False, has_form_8824=False, **_):
    properties = properties or []
    if has_form_4684 or has_form_6252 or has_form_8824:
        return {"red_defer": True}
    rs = [ind_property(p) for p in properties]
    st_ord = sum((r["st_ord"] for r in rs), D(0))
    l31 = sum((r["ordinary"] for r in rs), D(0))
    l32 = sum((r["s1231"] for r in rs if r["bucket"] == "p3"), D(0))
    l2 = sum((r["s1231"] for r in rs if r["bucket"] == "p1"), D(0)) + D(part1_line2_direct)
    ur1250 = sum((r["ur1250"] for r in rs), D(0))
    l7 = l2 + l32
    if l7 <= 0:
        l9, l11, l12 = D(0), l7, D(0)
    else:
        l8 = D(nonrecaptured_1231_losses)
        l12 = min(l7, l8)
        l9 = max(D(0), l7 - l8)
        l11 = D(0)
    l17 = st_ord + l11 + l12 + l31
    l18b = l17
    part4 = max(D(0), D(part4_section_179_recapture)) + max(D(0), D(part4_section_280f_recapture))
    return {"l7": l7, "l9": l9, "l18b": l18b, "unrecaptured_1250": ur1250,
            "sch1_line4": l18b + part4}


# ── 1. Scenarios — independent recompute + cross-check the loader ──
spec = m.FORMS[0]
DIAG_KEYS = {d["diagnostic_id"] for d in spec["diagnostics"]}
OUT_MAP = {"f4797_line7": "l7", "f4797_line9": "l9", "f4797_line18b": "l18b",
           "f4797_unrecaptured_1250": "unrecaptured_1250", "f4797_sch1_line4": "sch1_line4"}

for s in spec["scenarios"]:
    name = s["scenario_name"].split(" ")[0]
    inp = dict(s["inputs"])
    exp = s["expected_outputs"]
    diag_expected = {k for k in exp if k in DIAG_KEYS}
    if diag_expected:
        if "D_4797_002" in diag_expected and not inp.get("has_form_4684"):
            err(f"{name}: D_4797_002 expected but no Form 4684")
        if "D_4797_003" in diag_expected and not inp.get("has_form_6252"):
            err(f"{name}: D_4797_003 expected but no Form 6252")
        if "D_4797_004" in diag_expected and not inp.get("has_form_8824"):
            err(f"{name}: D_4797_004 expected but no Form 8824")
        if "D_4797_001" in diag_expected:
            got = ind_compute(**inp)
            if not (not got.get("red_defer") and D(got.get("l7")) > 0
                    and D(inp.get("nonrecaptured_1231_losses", 0)) == 0):
                err(f"{name}: D_4797_001 expected but not a net §1231 gain with no line-8 entry")
        # Classification leg (2026-07-02)
        if "D_4797_ADDL" in diag_expected:
            props = inp.get("properties") or []
            if not any(p.get("property_type") == "1250" and p.get("used_accel_bonus")
                       and D(p.get("additional_depreciation", 0)) == 0 for p in props):
                err(f"{name}: D_4797_ADDL expected but no accel/bonus §1250 property with blank 26a")
        if "D_4797_CLASS" in diag_expected:
            props = inp.get("properties") or []
            if not any(p.get("asset_group") == "Improvements"
                       and int(p.get("holding_period_months") or 0) > 12
                       and D(p.get("sales_price", 0))
                       - (D(p.get("cost_basis", 0)) - D(p.get("depreciation_allowed", 0))) > 0
                       for p in props):
                err(f"{name}: D_4797_CLASS expected but no Improvements-group long-term gain disposition")
        continue
    got = ind_compute(**inp)
    gl = m.compute_4797(**inp)
    for k, want in exp.items():
        if k in DIAG_KEYS:
            continue
        if k not in OUT_MAP:
            err(f"{name}.{k}: no independent recompute mapped")
            continue
        check(f"{name}.{k} (ind)", got.get(OUT_MAP[k]), want)
        check(f"{name}.{k} (loader)", gl.get(OUT_MAP[k]), want)

# ── 2. Structural checks ──
known_sources = {s["source_code"] for s in m.AUTHORITY_SOURCES} | set(m.EXISTING_SOURCES_TO_REFERENCE)
for key, idk in (("facts", "fact_key"), ("rules", "rule_id"), ("lines", "line_number"),
                 ("diagnostics", "diagnostic_id"), ("scenarios", "scenario_name")):
    ids = [x[idk] for x in spec[key]]
    if len(ids) != len(set(ids)):
        err(f"4797.{key}: duplicate ids")
for r in spec["rules"]:
    if len(r["rule_id"]) > 20:
        err(f"rule_id too long ({len(r['rule_id'])} > 20): {r['rule_id']}")
for d in spec["diagnostics"]:
    if len(d["diagnostic_id"]) > 20:
        err(f"diagnostic_id too long ({len(d['diagnostic_id'])} > 20): {d['diagnostic_id']}")
for ln in spec["lines"]:
    if len(str(ln["line_number"])) > 20:
        err(f"line_number too long ({len(str(ln['line_number']))} > 20): {ln['line_number']}")
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
        if k.startswith("D_4797_") and k not in diag_ids:
            err(f"{sc['scenario_name']}: expects unknown diagnostic {k}")
fa_ids = [a["assertion_id"] for a in m.FLOW_ASSERTIONS]
if len(fa_ids) != len(set(fa_ids)):
    err("duplicate flow-assertion ids")

# ── Report ──
print("Form 4797 (facts/rules/lines/diagnostics/scenarios/links):",
      (len(spec["facts"]), len(spec["rules"]), len(spec["lines"]),
       len(spec["diagnostics"]), len(spec["scenarios"]), len(spec["rule_links"])))
print(f"Flow assertions: {len(m.FLOW_ASSERTIONS)}; authority sources: {len(m.AUTHORITY_SOURCES)}")
print("Independently recomputed — T1 §1245 all-ord 10000 / T2 excess→Sch D 20000 / T5 unrecap §1250 "
      "100000 / T6 lookback L9 12000 L18b 38000 / T7 §1252 18000 / T8 §179 recap 7000; the §1231 "
      "netting + 5-yr lookback + the §1245/1250/1252/1254/1255 recapture cross-checked.")
print("Classification leg — C1 150DB land improvement (ord 20000 / unrecap 80000) / C2 SL QIP "
      "(ord 0 / unrecap 100000) / C3 bonused QIP (ord 280000 / unrecap 20000: bonus IS additional "
      "depreciation, i4797 verbatim) / C4 D_4797_ADDL gate / C5 D_4797_CLASS character check.")

if errors:
    print("\nFAILURES:")
    for e in errors:
        print(f"  X {e}")
    sys.exit(1)
print("\nALL CHECKS PASS")
