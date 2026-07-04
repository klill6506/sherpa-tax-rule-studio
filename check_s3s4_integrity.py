"""Pre-seed integrity checker for the S3/S4 MeF-ATS-unblock campaign specs:
load_1040_form_4835, load_1040_form_8835, load_1040_form_8936 (8936 + 8936_SCHA).

Run:  poetry run python check_s3s4_integrity.py

Mirrors the check_topic9 / check_schedule_f pattern: validates the authored
module lists WITHOUT touching the DB, then INDEPENDENTLY recomputes every
numeric scenario from its OWN re-typed transcription of the form math (NOT
imported from the loader), so a transcription error in a loader cannot also
pass this checker. Also cross-checks each loader's year-keyed constants
(MAGI caps, §45 rates, credit maxes, OBBBA cutoffs) cell-by-cell against
values re-typed here from the cited FINAL 2025 sources.

Structural gates enforced for every form:
  - rule_id / diagnostic_id / line_number <= 20 chars (RS varchar(20) cap).
  - every FormRule appears in RULE_LINKS (zero-authority rules fail the seed's
    own "all rules cited" gate; caught here pre-seed).
  - every rule input that looks like a fact_key is a declared fact_key.
  - no duplicate ids within a form.
This is the MATH + STRUCTURE gate; it must pass before trusting the seeded specs.
"""
import os
import sys
from decimal import Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_form_4835 as m4835  # noqa: E402
from specs.management.commands import load_1040_form_8835 as m8835  # noqa: E402
from specs.management.commands import load_1040_form_8936 as m8936  # noqa: E402

errors: list[str] = []
checks = 0


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def eq(name, got, want):
    global checks
    checks += 1
    if D(got) != D(want):
        err(f"[MATH] {name}: recomputed {got} != authored {want}")


def truthy(name, cond):
    global checks
    checks += 1
    if not cond:
        err(f"[EXPECT] {name}: authored expected_outputs missing/!=expected")


# ═══════════════════════════════════════════════════════════════════════════
# INDEPENDENT CONSTANTS (re-typed from the cited FINAL 2025 sources; NOT imported)
# ═══════════════════════════════════════════════════════════════════════════

# §469(i) special allowance (4835 loss path)
IND_PAL_ALLOWANCE = 25000
IND_PAL_START = 100000
IND_PAL_END = 150000

# 8936 MAGI caps (form-face chart; i8936)
IND_MAGI_NEW = {"single": 150000, "mfs": 150000, "hoh": 225000, "mfj": 300000, "qss": 300000, "estate_trust": 150000}
IND_MAGI_USED = {"single": 75000, "mfs": 75000, "hoh": 112500, "mfj": 150000, "qss": 150000}
IND_OBBBA_VEHICLE_CUTOFF = "2025-09-30"     # acquired on/before qualifies
IND_USED_RATE = Decimal("0.30")
IND_USED_MAX = 4000
IND_USED_PRICE_CEIL = 25000
IND_COMM_RATE_EV = Decimal("0.30")
IND_COMM_RATE_HYBRID = Decimal("0.15")
IND_COMM_MAX = 7500
IND_COMM_MAX_HEAVY = 40000

# §45 rates (8835; Fed. Reg. 2025-09366 / form pre-print)
IND_RATE_TIER1_POST2021 = Decimal("0.006")
IND_RATE_TIER2_POST2021 = Decimal("0.003")
IND_SEC45_CUTOFF = "2025-01-01"             # construction must begin BEFORE this
IND_X5 = 5
IND_BONUS = Decimal("0.10")


# ═══════════════════════════════════════════════════════════════════════════
# STRUCTURAL GATES
# ═══════════════════════════════════════════════════════════════════════════

def struct_checks(mod, form_keys):
    """form_keys: list of (form_number, facts, rules, lines, diags, scenarios, rule_links)."""
    global checks
    for fn, facts, rules, lines, diags, scenarios, rule_links in form_keys:
        fact_keys = {f["fact_key"] for f in facts}
        rule_ids = [r["rule_id"] for r in rules]
        diag_ids = [d["diagnostic_id"] for d in diags]
        line_nos = [ln["line_number"] for ln in lines]

        # id length cap (<= 20)
        for rid in rule_ids:
            checks += 1
            if len(rid) > 20:
                err(f"[IDCAP] {fn}: rule_id '{rid}' is {len(rid)} chars (> 20)")
        for did in diag_ids:
            checks += 1
            if len(did) > 20:
                err(f"[IDCAP] {fn}: diagnostic_id '{did}' is {len(did)} chars (> 20)")
        for lno in line_nos:
            checks += 1
            if len(str(lno)) > 20:
                err(f"[IDCAP] {fn}: line_number '{lno}' is {len(str(lno))} chars (> 20)")

        # duplicate ids
        for label, ids in (("rule_id", rule_ids), ("diagnostic_id", diag_ids), ("line_number", line_nos)):
            checks += 1
            dupes = {x for x in ids if ids.count(x) > 1}
            if dupes:
                err(f"[DUP] {fn}: duplicate {label}(s): {sorted(dupes)}")

        # every rule cited (appears in rule_links)
        linked = {rl[0] for rl in rule_links}
        for rid in rule_ids:
            checks += 1
            if rid not in linked:
                err(f"[CITE] {fn}: rule '{rid}' has NO authority link (would fail the seed's all-cited gate)")

        # rule inputs that look like fact_keys must be declared
        prefix = facts[0]["fact_key"].split("_")[0] if facts else ""
        for r in rules:
            for inp in r.get("inputs", []):
                if inp.startswith(prefix + "_") if prefix else False:
                    checks += 1
                    if inp not in fact_keys:
                        err(f"[INPUT] {fn}: rule '{r['rule_id']}' input '{inp}' is not a declared fact_key")


def _forms_of(mod):
    out = []
    for spec in mod.FORMS:
        out.append((
            spec["identity"]["form_number"], spec["facts"], spec["rules"],
            spec["lines"], spec["diagnostics"], spec["scenarios"], spec["rule_links"],
        ))
    return out


for mod in (m4835, m8835, m8936):
    struct_checks(mod, _forms_of(mod))


# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTS CROSS-CHECK (loader module constants vs. independently re-typed)
# ═══════════════════════════════════════════════════════════════════════════

# 8936 caps
for status, want in IND_MAGI_NEW.items():
    eq(f"8936 MAGI_CAP_NEW[{status}]", m8936.MAGI_CAP_NEW_2025.get(status), want)
for status, want in IND_MAGI_USED.items():
    eq(f"8936 MAGI_CAP_USED[{status}]", m8936.MAGI_CAP_USED_2025.get(status), want)
truthy("8936 OBBBA_ACQUIRED_CUTOFF[2025]", m8936.OBBBA_ACQUIRED_CUTOFF[2025] == IND_OBBBA_VEHICLE_CUTOFF)
eq("8936 USED_CREDIT_MAX", m8936.USED_CREDIT_MAX, IND_USED_MAX)
eq("8936 USED_PRICE_CEILING", m8936.USED_PRICE_CEILING, IND_USED_PRICE_CEIL)
eq("8936 COMMERCIAL_MAX", m8936.COMMERCIAL_MAX, IND_COMM_MAX)
eq("8936 COMMERCIAL_MAX_HEAVY", m8936.COMMERCIAL_MAX_HEAVY, IND_COMM_MAX_HEAVY)
eq("8936 USED_CREDIT_RATE", Decimal(m8936.USED_CREDIT_RATE), IND_USED_RATE)
eq("8936 COMMERCIAL_RATE_EV", Decimal(m8936.COMMERCIAL_RATE_EV), IND_COMM_RATE_EV)
eq("8936 COMMERCIAL_RATE_HYBRID", Decimal(m8936.COMMERCIAL_RATE_HYBRID), IND_COMM_RATE_HYBRID)

# 8835 rates
eq("8835 solar post_2021 rate", Decimal(m8835.RATE_2025["solar"]["post_2021"]), IND_RATE_TIER1_POST2021)
eq("8835 wind post_2021 rate", Decimal(m8835.RATE_2025["wind"]["post_2021"]), IND_RATE_TIER1_POST2021)
eq("8835 open_loop_biomass post_2021 rate", Decimal(m8835.RATE_2025["open_loop_biomass"]["post_2021"]), IND_RATE_TIER2_POST2021)
eq("8835 hydropower post_2022 rate", Decimal(m8835.RATE_2025["hydropower"]["post_2022"]), Decimal("0.006"))
truthy("8835 SEC45 cutoff[2025]", m8835.SEC45_BEGIN_CONSTRUCTION_CUTOFF[2025] == IND_SEC45_CUTOFF)
eq("8835 INCREASED_CREDIT_MULTIPLIER", m8835.INCREASED_CREDIT_MULTIPLIER, IND_X5)
eq("8835 DOMESTIC_CONTENT_BONUS", Decimal(m8835.DOMESTIC_CONTENT_BONUS), IND_BONUS)
eq("8835 ENERGY_COMMUNITY_BONUS", Decimal(m8835.ENERGY_COMMUNITY_BONUS), IND_BONUS)
eq("8835 PIS_WINDOW_YEARS_FOR_4E", m8835.PIS_WINDOW_YEARS_FOR_4E, 4)


# ═══════════════════════════════════════════════════════════════════════════
# INDEPENDENT SCENARIO RE-DERIVATION — pull inputs from the authored scenarios,
# recompute outputs from re-typed math, compare to the authored expected_outputs.
# ═══════════════════════════════════════════════════════════════════════════

def scen(mod, form_number, name):
    for spec in mod.FORMS:
        if spec["identity"]["form_number"] != form_number:
            continue
        for s in spec["scenarios"]:
            if s["scenario_name"].startswith(name):
                return s["inputs"], s["expected_outputs"]
    err(f"[SCEN] {form_number}: scenario '{name}' not found")
    return {}, {}


def pal_allowance(magi):
    """§469(i) $25k special allowance with the 50%-over-$100k phaseout."""
    if magi <= IND_PAL_START:
        return IND_PAL_ALLOWANCE
    if magi >= IND_PAL_END:
        return 0
    return IND_PAL_ALLOWANCE - (magi - IND_PAL_START) // 2


# ---- 4835 -----------------------------------------------------------------
i, e = scen(m4835, "4835", "F4835-S3")
L31 = i["line_9"] + i["line_14"] + i["line_17"] + i["line_23"] + i["line_26"]
L7 = i["line_1"]
eq("4835 S3 line_31", L31, e["line_31"]); eq("4835 S3 line_7", L7, e["line_7"])
eq("4835 S3 line_32", L7 - L31, e["line_32"])

i, e = scen(m4835, "4835", "F4835-T2")
L7 = i["line_1"] + i["line_2b"] + i["line_3b"] + i["line_4a"] + i["line_4c"] + i["line_5b"] + i["line_5d"] + i["line_6"]
eq("4835 T2 line_7 (right-column sum)", L7, e["line_7"])
eq("4835 T2 line_32", L7 - i["line_27"], e["line_32"])

# loss-path re-derivation (T3/T4/T5/T6)
for nm, magi, loss, at_risk_34b, at_risk_amt, active in (
    ("F4835-T3", 90000, 20000, False, 0, True),
    ("F4835-T4", 130000, 40000, False, 0, True),
    ("F4835-T5", 90000, 40000, True, 25000, True),
    ("F4835-T6", 90000, 20000, False, 0, False),
):
    i, e = scen(m4835, "4835", nm)
    step1 = min(loss, at_risk_amt) if at_risk_34b else loss     # §465 at-risk
    allow = pal_allowance(magi) if active else 0                # §469(i)
    allowed = min(step1, allow)                                 # no other passive income in these vectors
    eq(f"4835 {nm} line_34c", -allowed, e["line_34c"])
    eq(f"4835 {nm} suspended_pal", step1 - allowed, e["f4835_suspended_pal"])

i, e = scen(m4835, "4835", "F4835-T10")
L31 = (i["line_27"] + i["line_26"]) - i["line_30g"]
eq("4835 T10 line_31 (30g reduces)", L31, e["line_31"])
eq("4835 T10 line_32", i["line_1"] - L31, e["line_32"])

# ---- 8835 -----------------------------------------------------------------
def rate_of(res, pis_year):
    tbl = m8835.RATE_2025[res]  # tier lookup is the loader's; value cross-checked above
    if res in ("hydropower", "marine_hydrokinetic") and pis_year and pis_year > 2022:
        return Decimal(tbl["post_2022"])
    if pis_year and pis_year >= 2022:
        return Decimal(tbl["post_2021"])
    return Decimal(tbl.get("pre_2022", tbl["post_2021"]))

i, e = scen(m8835, "8835", "F8835-S4")
L2 = D(i["f8835_kwh_produced"]) * Decimal(i["f8835_applicable_rate"])
L9 = L2 * IND_X5  # 8a/8b/8c all Yes
eq("8835 S4 line_2", L2, e["line_2"]); eq("8835 S4 line_9 (x5)", L9, e["line_9"])
eq("8835 S4 line_12", L9, e["line_12"]); eq("8835 S4 line_15", L9, e["line_15"])
# PIS 2023-09-22 -> TY2025 within 4-yr window -> 4e
truthy("8835 S4 route 4e", e["route_3800_line"] == "4e")

i, e = scen(m8835, "8835", "F8835-T3")
L8 = D(i["f8835_kwh_produced"]) * Decimal(i["f8835_applicable_rate"])
eq("8835 T3 line_9 (no x5)", L8, e["line_9"])  # 8d -> no multiplier

i, e = scen(m8835, "8835", "F8835-T5")
L8 = D(i["f8835_kwh_produced"]) * Decimal(i["f8835_applicable_rate"])
L9 = L8 * IND_X5
L10 = L9 * IND_BONUS
L11 = L9 * IND_BONUS
eq("8835 T5 line_9", L9, e["line_9"]); eq("8835 T5 line_10", L10, e["line_10"])
eq("8835 T5 line_11", L11, e["line_11"]); eq("8835 T5 line_12", L9 + L10 + L11, e["line_12"])

# ---- 8936 (main) ----------------------------------------------------------
def denied(magi_2025, magi_2024, cap):
    return magi_2025 > cap and magi_2024 > cap

i, e = scen(m8936, "8936", "F8936-T2")
cap = IND_MAGI_NEW[i["f8936_filing_status"]]
truthy("8936 T2 denied both years", denied(i["f8936_magi_2025"], i["f8936_magi_2024"], cap) is True)
eq("8936 T2 line_13", 0, e["line_13"])

i, e = scen(m8936, "8936", "F8936-T3")
cap = IND_MAGI_NEW[i["f8936_filing_status"]]
truthy("8936 T3 qualifies (best of two)", denied(i["f8936_magi_2025"], i["f8936_magi_2024"], cap) is False)
eq("8936 T3 line_13 (min credit,tax)", min(i["f8936_personal_new_l9"], i["f8936_1040_line18_tax"]), e["line_13"])

# ---- 8936_SCHA (per vehicle) ---------------------------------------------
i, e = scen(m8936, "8936_SCHA", "F8936SA-T3")   # used
L15 = D(i["f8936sa_sales_price"]) * IND_USED_RATE
L17 = min(L15, IND_USED_MAX)
eq("8936_SCHA T3 line_15", L15, e["line_15"]); eq("8936_SCHA T3 line_17", L17, e["line_17"])

i, e = scen(m8936, "8936_SCHA", "F8936SA-T5")   # commercial EV
L21 = D(i["f8936sa_cost_basis"]) - D(i["f8936sa_sec179"])
rate = IND_COMM_RATE_HYBRID if i["f8936sa_powered_by_gas_diesel"] else IND_COMM_RATE_EV
L22 = L21 * rate
L24 = min(L22, D(i["f8936sa_incremental_cost"]))
cap = IND_COMM_MAX_HEAVY if D(i["f8936sa_gvwr"]) >= 14000 else IND_COMM_MAX
L26 = min(L24, cap)
eq("8936_SCHA T5 line_21", L21, e["line_21"]); eq("8936_SCHA T5 line_22", L22, e["line_22"])
eq("8936_SCHA T5 line_24", L24, e["line_24"]); eq("8936_SCHA T5 line_26", L26, e["line_26"])

# used-price-ceiling gate direction (T4 should flag > $25,000)
i, e = scen(m8936, "8936_SCHA", "F8936SA-T4")
truthy("8936_SCHA T4 over-ceiling flags", D(i["f8936sa_sales_price"]) > IND_USED_PRICE_CEIL and e.get("D_8936_006") is True)


# ═══════════════════════════════════════════════════════════════════════════
# REPORT
# ═══════════════════════════════════════════════════════════════════════════

print("=" * 68)
print(f"S3/S4 spec integrity — {checks} checks run")
print("=" * 68)
if errors:
    print(f"FAIL — {len(errors)} issue(s):")
    for msg in errors:
        print(f"  - {msg}")
    sys.exit(1)
else:
    print("PASS — all structural + math + constant checks green.")
    print("  forms: 4835, 8835, 8936, 8936_SCHA")
    print("  gates: id<=20, all-rules-cited, fact-key inputs, no-dupes,")
    print("         constants cross-check, independent scenario re-derivation.")
