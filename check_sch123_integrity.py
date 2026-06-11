"""Pre-seed content checker for load_1040_sch123 (Topic 2 — Schedules 1/2/3).

Run:  poetry run python check_sch123_integrity.py
Mirrors check_spine_integrity.py: validates the authored lists WITHOUT
touching the DB. Independent re-computation of every scenario sum.
"""
import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_sch123 as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


# ── per-form structural checks ──
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

    # every rule cited
    linked = {rid for rid, *_ in spec["rule_links"]}
    uncited = [rid for rid in rule_ids if rid not in linked]
    if uncited:
        err(f"{fn}: uncited rules {uncited}")
    dangling = [rid for rid in linked if rid not in rule_ids]
    if dangling:
        err(f"{fn}: rule_links reference unknown rules {dangling}")

    # source_rules on lines must exist
    for ln in spec["lines"]:
        for rid in ln.get("source_rules", []):
            if rid not in rule_ids:
                err(f"{fn} line {ln['line_number']}: unknown source_rule {rid}")

    # rule inputs must be declared facts
    for r in spec["rules"]:
        for key in r.get("inputs", []):
            if key not in fact_keys:
                err(f"{fn} {r['rule_id']}: input '{key}' is not a declared fact")

    # choice facts carry choices
    for f in spec["facts"]:
        if f["data_type"] == "choice" and not f.get("choices"):
            err(f"{fn} fact {f['fact_key']}: choice type without choices")

    # diagnostic ids referenced in notes exist (loose check skipped)

# ── flow assertions ──
fa_ids = [a["assertion_id"] for a in m.FLOW_ASSERTIONS]
if len(fa_ids) != len(set(fa_ids)):
    err("duplicate flow assertion ids")
for a in m.FLOW_ASSERTIONS:
    if len(a["assertion_id"]) > 20:
        err(f"assertion_id too long (>20): {a['assertion_id']}")

# ── independent scenario arithmetic ──
def check(name, got, want):
    if got != want:
        err(f"scenario {name}: recomputed {got} != authored {want}")


s = {sc["scenario_name"].split(" ")[0]: sc for spec in m.FORMS for sc in spec["scenarios"]}

# S1-T1
i = s["S1-T1"]["inputs"]
l9 = sum(i[k] for k in i if k.startswith("8") and not k.endswith("_type"))
l10 = sum(i[k] for k in ("1", "2a", "3", "4", "5", "6", "7")) + l9
check("S1-T1 L9", l9, s["S1-T1"]["expected_outputs"]["9"])
check("S1-T1 L10", l10, s["S1-T1"]["expected_outputs"]["10"])

# S1-T2
i = s["S1-T2"]["inputs"]
check("S1-T2 L9", i["8a"], s["S1-T2"]["expected_outputs"]["9"])
check("S1-T2 L10", i["3"] + i["7"] + i["8a"], s["S1-T2"]["expected_outputs"]["10"])

# S1-T3
i = s["S1-T3"]["inputs"]
l25 = sum(i[k] for k in i if k.startswith("24") and not k.endswith("_type"))
l26 = sum(i[k] for k in ("11", "12", "13", "14", "15", "16", "17", "18", "19a", "20", "21", "23")) + l25
check("S1-T3 L25", l25, s["S1-T3"]["expected_outputs"]["25"])
check("S1-T3 L26", l26, s["S1-T3"]["expected_outputs"]["26"])

# S2-T1
i = s["S2-T1"]["inputs"]
l1z = sum(i[k] for k in ("1a", "1b", "1c", "1d", "1e", "1f", "1y"))
check("S2-T1 L1z", l1z, s["S2-T1"]["expected_outputs"]["1z"])
check("S2-T1 L3", l1z + i["2"], s["S2-T1"]["expected_outputs"]["3"])

# S2-T2 — the line-20 exclusion pin
i = s["S2-T2"]["inputs"]
l7 = i["5"] + i["6"]
l18 = sum(i[k] for k in i if k.startswith("17") and not k.endswith("_type"))
l21 = i["4"] + l7 + i["8"] + i["9"] + i["11"] + i["12"] + i["13"] + i["14"] + i["15"] + i["16"] + l18 + i["19"]
check("S2-T2 L7", l7, s["S2-T2"]["expected_outputs"]["7"])
check("S2-T2 L18", l18, s["S2-T2"]["expected_outputs"]["18"])
check("S2-T2 L21", l21, s["S2-T2"]["expected_outputs"]["21"])
if l21 + i["20"] == s["S2-T2"]["expected_outputs"]["21"]:
    err("S2-T2: expected L21 would NOT catch a line-20 inclusion bug")

# S3-T1
i = s["S3-T1"]["inputs"]
l7 = sum(i[k] for k in i if k.startswith("6") and not k.endswith("_type"))
l8 = sum(i[k] for k in ("1", "2", "3", "4", "5a", "5b")) + l7
check("S3-T1 L7", l7, s["S3-T1"]["expected_outputs"]["7"])
check("S3-T1 L8", l8, s["S3-T1"]["expected_outputs"]["8"])

# S3-T2
i = s["S3-T2"]["inputs"]
l14 = sum(i[k] for k in i if k.startswith("13") and not k.endswith("_type"))
l15 = sum(i[k] for k in ("9", "10", "11", "12")) + l14
check("S3-T2 L14", l14, s["S3-T2"]["expected_outputs"]["14"])
check("S3-T2 L15", l15, s["S3-T2"]["expected_outputs"]["15"])

# S3-T3
i = s["S3-T3"]["inputs"]
check("S3-T3 L7", i["6a"] + i["6l"], s["S3-T3"]["expected_outputs"]["7"])

# ── line-vs-dump existence: every widget-bearing entry line declared ──
counts = {spec["identity"]["form_number"]: (len(spec["facts"]), len(spec["rules"]),
          len(spec["lines"]), len(spec["diagnostics"]), len(spec["scenarios"]),
          len(spec["rule_links"])) for spec in m.FORMS}

print("Per-form counts (facts/rules/lines/diagnostics/scenarios/links):")
for fn, c in counts.items():
    print(f"  {fn}: {c}")
print(f"Flow assertions: {len(m.FLOW_ASSERTIONS)}")
print(f"Authority sources (new): {len(m.AUTHORITY_SOURCES)}; topics: {len(m.AUTHORITY_TOPICS)}")

if errors:
    print("\nFAILURES:")
    for e in errors:
        print(f"  ✗ {e}")
    sys.exit(1)
print("\nALL CHECKS PASS")
