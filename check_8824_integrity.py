"""Pre-seed math gate for load_8824 (Like-Kind Exchanges + §1043, FULL v1).

Run:  poetry run python check_8824_integrity.py

Independently recomputes every scenario from its OWN transcription of the §1031 like-kind model:
the §1.1031(d)-2 liability netting, realized/recognized/deferred gain, the COMPUTED §1245(b)(4)/
§1250(d)(4) recapture limits, the 25a/b/c basis allocation, the §1031(f) related-party 2-year
acceleration, and the Part IV §1043 divestiture. The loader and this gate share NO math — both must
agree with the authored expected_outputs. Cross-checked against the i8824 (2025) worked examples
(Taylor §1245 → L21 35000 / Finley §1250 → L21 30000, 25a 131250 / 25b 43750).
"""
import os
import sys
from decimal import Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_8824 as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def check(name, got, want):
    if D(got) != D(want):
        err(f"{name}: recomputed {got} != authored {want}")


# ── Independent recompute (re-typed, shares no code with the loader) ──
def ind_8824(fmv_other_given_up=0, basis_other_given_up=0,
             cash_received=0, fmv_nonlike_received=0, exchange_expenses=0,
             liabilities_assumed_by_other=0, liabilities_you_assumed=0,
             cash_you_paid=0, fmv_nonlike_given_up=0,
             fmv_likekind_received=0, basis_likekind_given_up=0,
             depreciation_1245=0, fmv_1245_lk_received=0,
             additional_depreciation_1250=0, fmv_1250_lk_received=0, fmv_intangible_lk_received=0,
             property_character="capital", holding_period_months=0,
             related_party=False, is_followup_year=False, related_party_disposed=False,
             rp_exception="", prior_year_deferred_gain=0,
             days_to_identify=None, days_to_receive=None,
             is_1043=False, sales_price_divested=0, basis_divested=0,
             cost_replacement_60day=0, recapture_1043=0, character_1043="capital",
             multi_asset=False, property_used_as_home=False, is_real_property=True, **_):
    if multi_asset or property_used_as_home or not is_real_property:
        return {"red_defer": True}
    lt = int(holding_period_months or 0) > 12

    # ── Part IV §1043 ──
    if is_1043:
        l30 = D(sales_price_divested); l31 = D(basis_divested)
        l32 = l30 - l31
        l33 = D(cost_replacement_60day)
        l34 = max(D(0), l30 - l33)
        l35 = D(recapture_1043)
        l36 = max(D(0), l34 - l35)
        l37 = l32 - (l35 + l36)
        l38 = l33 - l37
        sch_d_st = sch_d_lt = f4797_line2 = D(0)
        if character_1043 == "capital":
            if lt:
                sch_d_lt = l36
            else:
                sch_d_st = l36
        else:
            f4797_line2 = l36
        return {"l32": l32, "l34": l34, "l35": l35, "l36": l36, "l37": l37, "l38": l38,
                "f4797_line10": l35, "f4797_line2": f4797_line2,
                "sch_d_st": sch_d_st, "sch_d_lt": sch_d_lt, "is_1043": True}

    # ── Part III §1031 ──
    l14 = D(fmv_other_given_up) - D(basis_other_given_up)
    net_relief = D(liabilities_assumed_by_other) - (D(liabilities_you_assumed) + D(cash_you_paid) + D(fmv_nonlike_given_up))
    net_liab_to_you = max(D(0), net_relief)
    net_paid_to_other = max(D(0), -net_relief)
    gross_15 = D(cash_received) + D(fmv_nonlike_received) + net_liab_to_you
    l15 = max(D(0), gross_15 - D(exchange_expenses))
    exp_remaining = D(exchange_expenses) - (gross_15 - l15)
    l16 = D(fmv_likekind_received)
    l17 = l15 + l16
    l18 = D(basis_likekind_given_up) + exp_remaining + net_paid_to_other
    l19 = l17 - l18
    l20 = max(D(0), min(l15, l19))
    # computed recapture
    recap_1245 = D(0)
    if D(depreciation_1245) > 0:
        test1 = min(D(depreciation_1245), max(D(0), l19))
        test2 = l20 + (l16 - D(fmv_1245_lk_received))
        recap_1245 = min(test1, test2)
    recap_1250 = D(0)
    if D(additional_depreciation_1250) > 0:
        addl = D(additional_depreciation_1250)
        recap_1250 = min(addl, max(l20, addl - D(fmv_1250_lk_received)))
    l21 = recap_1245 + recap_1250
    l22 = max(D(0), l20 - l21)
    l23 = l21 + l22
    l24 = l19 if l19 < 0 else (l19 - l23)
    l25 = (l18 + l23) - l15
    if l16 > 0:
        l25a = l25 * D(fmv_1250_lk_received) / l16
        l25b = l25 * D(fmv_1245_lk_received) / l16
        l25c = l25 * D(fmv_intangible_lk_received) / l16
    else:
        l25a = l25b = l25c = D(0)
    # routing
    f4797_line16 = l21
    f4797_line5 = sch_d_st = sch_d_lt = ord_l22 = D(0)
    if property_character == "business_1231" and lt:
        f4797_line5 = l22
    elif property_character == "ordinary" or not lt:
        ord_l22 = l22
    else:
        if lt:
            sch_d_lt = l22
        else:
            sch_d_st = l22
    f4797_line16 = f4797_line16 + ord_l22
    # §1031(f) acceleration
    if related_party and is_followup_year and related_party_disposed and not rp_exception:
        accel = max(D(0), D(prior_year_deferred_gain))
        if property_character == "business_1231" and lt:
            f4797_line5 += accel
        elif property_character == "ordinary" or not lt:
            f4797_line16 += accel
        elif lt:
            sch_d_lt += accel
        else:
            sch_d_st += accel
    return {"l14": l14, "l15": l15, "l16": l16, "l17": l17, "l18": l18, "l19": l19, "l20": l20,
            "l21": l21, "l22": l22, "l23": l23, "l24": l24,
            "l25": l25, "l25a": l25a, "l25b": l25b, "l25c": l25c,
            "f4797_line5": f4797_line5, "f4797_line16": f4797_line16,
            "sch_d_st": sch_d_st, "sch_d_lt": sch_d_lt, "is_loss_deferred": l19 < 0}


# ── 1. Scenarios — independent recompute + cross-check the loader ──
spec = m.FORMS[0]
DIAG_KEYS = {d["diagnostic_id"] for d in spec["diagnostics"]}
OUT_MAP = {
    "f8824_line19": "l19", "f8824_line23": "l23", "f8824_line24": "l24", "f8824_line25": "l25",
    "f8824_line25a": "l25a", "f8824_line25b": "l25b", "f8824_line25c": "l25c",
    "f8824_line15": "l15", "f8824_line32": "l32", "f8824_line34": "l34", "f8824_line37": "l37",
    "f8824_line38": "l38",
    "f8824_f4797_line5": "f4797_line5", "f8824_f4797_line16": "f4797_line16",
    "f8824_f4797_line10": "f4797_line10",
    "sch_d_st": "sch_d_st", "sch_d_lt": "sch_d_lt",
}

for s in spec["scenarios"]:
    name = s["scenario_name"].split(" ")[0]
    inp = dict(s["inputs"])
    exp = s["expected_outputs"]
    diag_expected = {k for k in exp if k in DIAG_KEYS}
    if diag_expected:
        # gate scenarios: the RED/condition flag must be set in the inputs (no silent gap)
        if "D_8824_007" in diag_expected and not inp.get("multi_asset"):
            err(f"{name}: D_8824_007 expected but multi_asset not set")
        if "D_8824_008" in diag_expected and not inp.get("property_used_as_home"):
            err(f"{name}: D_8824_008 expected but property_used_as_home not set")
        if "D_8824_009" in diag_expected and inp.get("is_real_property", True):
            err(f"{name}: D_8824_009 expected but is_real_property not False")
        if "D_8824_005" in diag_expected:  # like-kind loss
            got = ind_8824(**inp)
            if got.get("red_defer") or not got.get("is_loss_deferred"):
                err(f"{name}: D_8824_005 expected but line 19 is not a loss")
        if "D_8824_004" in diag_expected:  # §1031(f) acceleration
            if not (inp.get("is_followup_year") and inp.get("related_party_disposed")
                    and not inp.get("rp_exception")):
                err(f"{name}: D_8824_004 expected but the §1031(f) trigger is not set")
        # value outputs may ALSO be present on a diagnostic scenario (e.g. T5, T8) — fall through

    got = ind_8824(**inp)
    gl = m.compute_8824(**inp)
    if got.get("red_defer") or gl.get("red_defer"):
        if not diag_expected:
            err(f"{name}: unexpected red_defer")
        continue
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
        err(f"8824.{key}: duplicate ids")
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
        if k.startswith("D_8824_") and k not in diag_ids:
            err(f"{sc['scenario_name']}: expects unknown diagnostic {k}")
fa_ids = [a["assertion_id"] for a in m.FLOW_ASSERTIONS]
if len(fa_ids) != len(set(fa_ids)):
    err("duplicate flow-assertion ids")

# ── Report ──
print("Form 8824 (facts/rules/lines/diagnostics/scenarios/links):",
      (len(spec["facts"]), len(spec["rules"]), len(spec["lines"]),
       len(spec["diagnostics"]), len(spec["scenarios"]), len(spec["rule_links"])))
print(f"Flow assertions: {len(m.FLOW_ASSERTIONS)}; authority sources: {len(m.AUTHORITY_SOURCES)}")
print("Independently recomputed - T1 all-deferred L24 20000 / T2 boot L19 120000 basis 170000 / "
      "T3 sec1245 L21 35000->4797 L16, L22 5000->4797 L5 / T4 sec1250 Finley L21 30000, 25a 131250 25b 43750 / "
      "T5 loss -20000 deferred / T6 capital->Sch D 30000 / T7 sec1043 L37 130000 / T8 sec1031(f) accel 60000; "
      "the liability netting + computed recapture + 25a/b/c allocation + sec1043 + acceleration cross-checked.")

if errors:
    print("\nFAILURES:")
    for e in errors:
        print(f"  X {e}")
    sys.exit(1)
print("\nALL CHECKS PASS")
