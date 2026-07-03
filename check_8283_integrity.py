"""Pre-seed math gate for load_1040_form_8283 (noncash charitable contributions,
ATS Scenario 2).

Run:  poetry run python check_8283_integrity.py

Independently recomputes every scenario from its OWN transcription of the
§170(f)(11)/(f)(12) rules (Section A/B routing incl. the readily-valued
exceptions; the substantiation withholds; the 50%/30% bucket totals; the
>$500 engagement gate; the Schedule A line-12 feeder with per-field GREEN
overrides; the T6 Pub 526 bucket-limit worksheet), cross-checks the loader's
scenario pins cell-by-cell, and enforces the varchar(20) id caps on
rule_id / diagnostic_id / line_number (the check_schedule_f_integrity guards).
"""
import os
from decimal import Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_form_8283 as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def check(name, got, want):
    if isinstance(want, bool) or isinstance(got, bool):
        if bool(got) != bool(want):
            err(f"{name}: recomputed {got} != authored {want}")
    elif isinstance(want, list):
        if list(got) != list(want):
            err(f"{name}: recomputed {got} != authored {want}")
    else:
        if D(got) != D(want):
            err(f"{name}: recomputed {got} != authored {want}")


# ── Independent constants (re-typed from §170(f)(11)/(12), i8283 Rev. 12-2025,
#    and the SCHEDULE_A spec's Pub 526 buckets) ──
IND_FILE_THRESHOLD = Decimal(500)        # §170(f)(11)(B)
IND_SECTION_B_OVER = Decimal(5000)       # §170(f)(11)(C)
IND_ART_ATTACH = Decimal(20000)          # i8283: art valued $20,000 or more
IND_BIG_ATTACH = Decimal(500000)         # §170(f)(11)(D)
IND_VEHICLE_CWA = Decimal(500)           # §170(f)(12)(A)
IND_NOTGOOD_MIN = Decimal(500)           # §170(f)(16) / i8283 not-good-condition
IND_CASH_PCT = Decimal("0.60")           # Pub 526 (matches SCHEDULE_A CHARITABLE)
IND_FIFTY_PCT = Decimal("0.50")
IND_CAPGAIN_PCT = Decimal("0.30")

CONSERVATION_TYPES = {"conservation", "historic"}


def row_section(r):
    amount = D(r.get("amount", 0))
    if r.get("property_type") in CONSERVATION_TYPES:
        return "B"
    if r.get("not_good_condition") and amount > IND_NOTGOOD_MIN:
        return "B"
    readily_valued = (
        r.get("public_security") or r.get("intellectual") or r.get("inventory_1221")
        or (r.get("is_vehicle") and not r.get("vehicle_fmv_exception") and r.get("ack_1098c"))
    )
    if amount > IND_SECTION_B_OVER and not readily_valued:
        return "B"
    return "A"


def attach_tier(r):
    amount = D(r.get("amount", 0))
    if r.get("property_type") == "art20k":
        return True
    if r.get("property_type") == "art_lt20k" and amount >= IND_ART_ATTACH:
        return True
    if amount > IND_BIG_ATTACH:
        return True
    if r.get("not_good_condition") and amount > IND_NOTGOOD_MIN:
        return True
    return False


def row_flags(r):
    """Returns (section, withheld, diags_dict) for one row.

    J6 RULED warn-only-feed-anyway (Ken 2026-07-03): substantiation gaps fire
    their ERRORs but never withhold; the ONLY withhold is the J4 conservation
    defer."""
    amount = D(r.get("amount", 0))
    sec = row_section(r)
    diags = {k: False for k in ("D_8283_002", "D_8283_003", "D_8283_004", "D_8283_005",
                                "D_8283_006", "D_8283_009", "D_8283_013")}
    withheld = False
    if r.get("property_type") in CONSERVATION_TYPES:
        diags["D_8283_006"] = True
        withheld = True
    if sec == "B" and not r.get("appraisal_obtained") and not diags["D_8283_006"]:
        diags["D_8283_002"] = True
    if r.get("is_vehicle") and amount > IND_VEHICLE_CWA and not r.get("ack_1098c"):
        diags["D_8283_003"] = True
    if attach_tier(r) and not r.get("appraisal_attached") and not diags["D_8283_006"]:
        diags["D_8283_004"] = True
    if r.get("not_good_condition") and amount <= IND_NOTGOOD_MIN:
        diags["D_8283_013"] = True
    if (sec == "A" and amount > IND_FILE_THRESHOLD and not r.get("public_security")
            and (not r.get("date_acquired") or not r.get("how_acquired")
                 or r.get("cost_basis") is None)):
        diags["D_8283_005"] = True
    capgain = r.get("capgain_property", None)
    if capgain is not True and r.get("cost_basis") is not None and amount > D(r.get("cost_basis")):
        diags["D_8283_009"] = True
    return sec, withheld, diags


def run_scenario(inp):
    rows = inp.get("rows", [])
    sections, withhelds = [], []
    diags = {}
    bucket_50 = bucket_30 = Decimal(0)
    for r in rows:
        sec, wh, dd = row_flags(r)
        sections.append(sec)
        withhelds.append(wh)
        for k, v in dd.items():
            diags[k] = diags.get(k, False) or v
        if not wh:
            if r.get("capgain_property") is True:
                bucket_30 += D(r.get("amount", 0))
            else:
                bucket_50 += D(r.get("amount", 0))
    total = bucket_50 + bucket_30
    engaged = total > IND_FILE_THRESHOLD
    flat_noncash = D(inp.get("scha_charitable_noncash_fmv_entered", 0))
    flat_capgain = D(inp.get("scha_charitable_capgain_50org_entered", 0))
    noncash_input = flat_noncash if flat_noncash > 0 else bucket_50
    capgain_input = flat_capgain if flat_capgain > 0 else bucket_30
    out = {
        "f8283_total": total, "f8283_bucket_50": bucket_50, "f8283_bucket_30": bucket_30,
        "f8283_engaged": engaged, "row_sections": sections, "f8283_row_withheld": withhelds,
        "scha_line12_default": noncash_input + capgain_input,
        "scha_line12_noncash_input": noncash_input,
        **diags,
        "D_8283_001": False,  # rows present in every scenario -> never fires here
    }
    # The T6 Schedule A bucket-limit worksheet (TY2025 -- no 0.5% floor)
    if "agi" in inp:
        agi = D(inp["agi"])
        cash = D(inp.get("scha_charitable_cash", 0))
        cin = D(inp.get("scha_charitable_carryover_in", 0))
        cash_lim = min(cash, IND_CASH_PCT * agi)
        fifty_lim = min(noncash_input, IND_FIFTY_PCT * agi)
        capgain_lim = min(capgain_input, IND_CAPGAIN_PCT * agi)
        allowed = min(cash_lim + fifty_lim + capgain_lim + cin, IND_CASH_PCT * agi)
        out["scha_line14"] = allowed
        out["scha_charitable_carryover_out"] = (cash + noncash_input + capgain_input + cin) - allowed
        # D_8283_008: any defaulted row + binding limitation
        defaulted = any(r.get("capgain_property", None) is None for r in rows)
        out["D_8283_008"] = defaulted and out["scha_charitable_carryover_out"] > 0
    return out


print("=" * 70)
print("check_8283_integrity -- independent recompute of every authored scenario")
print("=" * 70)

for sc in m.F8283_SCENARIOS:
    name = sc["scenario_name"]
    got = run_scenario(sc["inputs"])
    for key, want in sc["expected_outputs"].items():
        if key not in got:
            err(f"{name} :: {key}: expected key not produced by the transcription")
            continue
        check(f"{name} :: {key}", got[key], want)

# ── The S2 sanity pins (the scenario PDF's own numbers, re-typed) ──
t1 = run_scenario(m.F8283_SCENARIOS[0]["inputs"])
check("S2 pin :: line-12 default", t1["scha_line12_default"], 700)
check("S2 pin :: engaged", t1["f8283_engaged"], True)

# ── varchar(20) id caps (the check_schedule_f_integrity guards) ──
for r in m.F8283_RULES:
    if len(r["rule_id"]) > 20:
        err(f"rule_id too long (>20): {r['rule_id']}")
for d in m.F8283_DIAGNOSTICS:
    if len(d["diagnostic_id"]) > 20:
        err(f"diagnostic_id too long (>20): {d['diagnostic_id']}")
for ln in m.F8283_LINES:
    if len(ln["line_number"]) > 20:
        err(f"line_number too long (>20): {ln['line_number']}")

# ── Structural: every diagnostic id named in a rule formula exists; every rule cited ──
diag_ids = {d["diagnostic_id"] for d in m.F8283_DIAGNOSTICS}
import re  # noqa: E402
for r in m.F8283_RULES:
    for ref in re.findall(r"D_8283_\d{3}", r["formula"]):
        if ref not in diag_ids:
            err(f"{r['rule_id']} references undefined diagnostic {ref}")
linked_rules = {rid for rid, *_ in m.F8283_RULE_LINKS}
for r in m.F8283_RULES:
    if r["rule_id"] not in linked_rules:
        err(f"rule {r['rule_id']} has no authority link")

print()
if errors:
    print(f"FAIL: {len(errors)} FAILURE(S):")
    for e in errors:
        print("  -", e)
    raise SystemExit(1)
print("OK: ALL CHECKS PASS -- scenarios recompute independently; ids within caps; all rules cited.")
