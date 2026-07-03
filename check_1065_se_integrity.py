"""Pre-seed content checker for load_1065_se (leg 2 — the 14a SE-base sub-spec).

Run:  poetry run python check_1065_se_integrity.py

Mirrors check_schedule_f_integrity.py: validates the authored lists WITHOUT
touching the DB, then INDEPENDENTLY recomputes every numeric scenario from its
OWN transcription of the form math (NOT imported from the loader):

  - the classification model (T1-T10): active → box1 + GPsvc + GPcap;
    passive → GPsvc only; undetermined → active safety net; non-individual → 0
    (re-typed from the locked spec §3/§4 table + the i1065 Code A instruction)
  - the SE-base worksheet (B1-B6): 1e = 1a+1b+1c+1d; 3a = 1e − 2
    (re-typed from the i1065 2025 p.45 worksheet face)

Loader & gate share no math. Also enforces: id-length ≤ 20 (varchar(20)),
every rule carries ≥1 authority link, every diagnostic referenced by a
scenario exists, and the leg-2 additions are present and complete.
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from decimal import Decimal  # noqa: E402

import django  # noqa: E402

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1065_se as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


# ═══════════════════════════════════════════════════════════════════════════
# INDEPENDENT MATH (re-typed from the spec §3/§4 table + the i1065 2025 p.45
# worksheet face — NOT imported from the loader)
# ═══════════════════════════════════════════════════════════════════════════

def ind_partner_14a(inputs: dict) -> Decimal:
    """Per-partner box 14a per the locked classification table."""
    if inputs.get("se_is_individual") is False:
        return D(0)  # Code A: no box 14a for non-individual partners
    ptype = inputs.get("se_partner_type", "general")
    cls = inputs.get("se_classification", "undetermined")
    if ptype == "general":
        cls = "active"
    elif cls not in ("active", "passive"):
        cls = "active"  # Decision 1 safety net (fires D_SE_UNDET upstream)
    box1 = D(inputs.get("se_box1_ordinary", 0))
    gps = D(inputs.get("se_gp_services", 0))
    gpc = D(inputs.get("se_gp_capital", 0))
    if cls == "passive":
        return gps
    return box1 + gps + gpc


def ind_base(inputs: dict) -> dict:
    """Worksheet 1e/3a from the face: 1e = 1a+1b+1c+1d; 3a = 1e − 2."""
    l1e = (D(inputs.get("se_ws_1a_k1", 0)) + D(inputs.get("se_ws_1b_rental_se", 0))
           + D(inputs.get("se_ws_1c_k3c", 0)) + D(inputs.get("se_ws_1d_4797_loss", 0)))
    l3a = l1e - D(inputs.get("se_ws_2_4797_gain", 0))
    return {"se_ws_1e": l1e, "se_ws_3a": l3a}


# ═══════════════════════════════════════════════════════════════════════════
# 1. Scenario recomputation
# ═══════════════════════════════════════════════════════════════════════════

for s in m.SCENARIOS:
    name = s["scenario_name"]
    inp, exp = s["inputs"], s["expected_outputs"]
    if "partners" in inp:  # T7 — entity Σ
        got = sum(D(p["se_k1_box14a"]) for p in inp["partners"])
        want = D(exp["sched_k_line14a"])
        if got != want:
            err(f"{name}: entity Σ {got} != authored {want}")
        continue
    if "se_ws_1a_k1" in inp:  # B1-B6 — base worksheet
        got = ind_base(inp)
        for key in ("se_ws_1e", "se_ws_3a"):
            if key in exp and got[key] != D(exp[key]):
                err(f"{name}: {key} recomputed {got[key]} != authored {exp[key]}")
        continue
    # T1-T10 + B7 — per-partner
    if "se_k1_box14a" in exp:
        got = ind_partner_14a(inp)
        if got != D(exp["se_k1_box14a"]):
            err(f"{name}: 14a recomputed {got} != authored {exp['se_k1_box14a']}")

# Diagnostic-condition flags asserted by scenarios
for s in m.SCENARIOS:
    inp, exp = s["inputs"], s["expected_outputs"]
    if exp.get("D_SE_UNDET"):
        ok = (inp.get("se_partner_type") in ("limited", "llc_member")
              and D(inp.get("se_box1_ordinary", 0)) != 0
              and inp.get("se_classification") == "undetermined")
        if not ok:
            err(f"{s['scenario_name']}: asserts D_SE_UNDET but its condition doesn't hold")
    if exp.get("D_SE_GPCHAR"):
        ok = (D(inp.get("se_gp_capital", 0)) > 0 and D(inp.get("se_gp_services", 0)) == 0
              and (inp.get("se_classification") == "active" or inp.get("se_partner_type") == "general"))
        if not ok:
            err(f"{s['scenario_name']}: asserts D_SE_GPCHAR but its condition doesn't hold")
    if exp.get("D_SE_NONIND"):
        if inp.get("se_is_individual") is not False:
            err(f"{s['scenario_name']}: asserts D_SE_NONIND but se_is_individual isn't False")

# ═══════════════════════════════════════════════════════════════════════════
# 2. Structural checks
# ═══════════════════════════════════════════════════════════════════════════

for r in m.RULES:
    if len(r["rule_id"]) > 20:
        err(f"rule_id too long (>20): {r['rule_id']}")
for d in m.DIAGNOSTICS:
    if len(d["diagnostic_id"]) > 20:
        err(f"diagnostic_id too long (>20): {d['diagnostic_id']}")
for a in m.FLOW_ASSERTIONS:
    if len(a["assertion_id"]) > 20:
        err(f"assertion_id too long (>20): {a['assertion_id']}")
for ln in m.LINES:
    if len(ln["line_number"]) > 20:
        err(f"line_number too long (>20): {ln['line_number']}")

linked_rule_ids = {rid for rid, *_ in m.RULE_LINKS}
for r in m.RULES:
    if r["rule_id"] not in linked_rule_ids:
        err(f"UNCITED rule (no RULE_LINKS entry): {r['rule_id']}")

known_sources = {s["source_code"] for s in m.AUTHORITY_SOURCES}
for rid, code, level, _note in m.RULE_LINKS:
    if code not in known_sources:
        err(f"RULE_LINKS references unknown source: {rid} -> {code}")
    if level not in ("primary", "secondary", "interpretive", "implementation"):
        err(f"bad support_level {level!r} on {rid} -> {code}")

rule_ids = {r["rule_id"] for r in m.RULES}
for rid, *_ in m.RULE_LINKS:
    if rid not in rule_ids:
        err(f"RULE_LINKS references unknown rule: {rid}")

diag_ids = {d["diagnostic_id"] for d in m.DIAGNOSTICS}
for s in m.SCENARIOS:
    for key, val in s["expected_outputs"].items():
        if key.startswith("D_SE_") and val is True and key not in diag_ids:
            err(f"{s['scenario_name']}: asserts unknown diagnostic {key}")

fact_keys = {f["fact_key"] for f in m.FACTS}
for r in m.RULES:
    for fk in list(r.get("inputs", [])) + list(r.get("outputs", [])):
        if fk not in fact_keys:
            err(f"rule {r['rule_id']} references unknown fact: {fk}")

# Leg-2 completeness pins
EXPECT_LEG2 = {
    "rules": {"R-SE-BASE-1B", "R-SE-BASE-1C", "R-SE-BASE-4797", "R-SE-BASE-3A", "R-SE-NONIND"},
    "diags": {"D_SE_RENT1B", "D_SE_4797ORD", "D_SE_NONIND"},
    "facts": {"se_ws_1a_k1", "se_ws_1b_rental_se", "se_ws_1c_k3c", "se_ws_1d_4797_loss",
              "se_ws_2_4797_gain", "se_ws_1e", "se_ws_3a"},
    "lines": {"WS1a", "WS1b", "WS1c", "WS1d", "WS1e", "WS2", "WS3a", "WS3b", "WS3c",
              "WS4a", "WS4b", "WS4c", "WS5"},
}
if not EXPECT_LEG2["rules"] <= rule_ids:
    err(f"missing leg-2 rules: {EXPECT_LEG2['rules'] - rule_ids}")
if not EXPECT_LEG2["diags"] <= diag_ids:
    err(f"missing leg-2 diagnostics: {EXPECT_LEG2['diags'] - diag_ids}")
if not EXPECT_LEG2["facts"] <= fact_keys:
    err(f"missing leg-2 facts: {EXPECT_LEG2['facts'] - fact_keys}")
line_nums = {ln["line_number"] for ln in m.LINES}
if not EXPECT_LEG2["lines"] <= line_nums:
    err(f"missing leg-2 worksheet lines: {EXPECT_LEG2['lines'] - line_nums}")

scenario_names = [s["scenario_name"] for s in m.SCENARIOS]
if len(scenario_names) != len(set(scenario_names)):
    err("duplicate scenario names")
if sum(1 for n in scenario_names if n.startswith("B")) != 7:
    err("expected 7 leg-2 base scenarios (B1-B7)")
if sum(1 for n in scenario_names if n.startswith("T")) != 10:
    err("expected the 10 locked leg-1 scenarios (T1-T10)")

fa_ids = {a["assertion_id"] for a in m.FLOW_ASSERTIONS}
if "INV-SE-BASE" not in fa_ids:
    err("missing INV-SE-BASE flow assertion")
for a in m.FLOW_ASSERTIONS:
    if a["assertion_id"] == "FLOW-14A-SE" and a.get("status") != "disabled":
        err("FLOW-14A-SE must stay status=disabled")

# ═══════════════════════════════════════════════════════════════════════════
print("=" * 64)
if errors:
    print(f"CHECKS FAILED ({len(errors)}):")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
print(f"ALL CHECKS PASS — {len(m.SCENARIOS)} scenarios recomputed independently "
      f"({sum(1 for n in scenario_names if n.startswith('T'))} classification + "
      f"{sum(1 for n in scenario_names if n.startswith('B'))} base), "
      f"{len(m.RULES)} rules all cited, {len(m.LINES)} lines, "
      f"{len(m.DIAGNOSTICS)} diagnostics, {len(m.FLOW_ASSERTIONS)} flow assertions.")
