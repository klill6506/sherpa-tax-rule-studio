"""Pre-seed math gate for load_6252 (Installment Sale Income, Broad v1).

Run:  poetry run python check_6252_integrity.py

Independently recomputes every scenario from its OWN transcription of the §453 installment
method (gross profit %, contract price, payments × ratio), the §1245/1250 recapture added to
basis (line 12), the Part III §453(e) related-party acceleration, and the §453A interest on
deferred tax (Pub 537). The loader and this gate share NO math — both must agree with the
authored expected_outputs.
"""
import os
import sys
from decimal import ROUND_HALF_UP, Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_6252 as m  # noqa: E402

errors: list[str] = []

_FIVE_M = Decimal("5000000")
_PRICE = Decimal("150000")


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def r0(x):
    return Decimal(D(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def check(name, got, want):
    if D(got) != D(want):
        err(f"{name}: recomputed {got} != authored {want}")


# ── Independent recompute (re-typed, shares no code with the loader) ──
def ind_6252(selling_price=0, mortgages_assumed=0, cost_basis=0, depreciation_allowed=0,
             commissions_expenses=0, recapture_from_4797=0, excluded_gain_main_home=0,
             is_year_of_sale=True, payments_current_year=0, payments_prior_years=0,
             ordinary_recapture_portion=0, prior_gross_profit_pct=None,
             property_character="capital", holding_period_months=0, unrecaptured_1250_portion=0,
             related_party=False, related_party_resold=False, rp_exception="",
             rp_selling_price=0, rp_ordinary_recapture=0,
             aggregate_obligations_year_end=0, section_6621_rate=0,
             max_rate_ordinary="0.37", max_rate_ltcg="0.20",
             price_not_determinable=False, depreciable_to_related_person=False, **_):
    if price_not_determinable or depreciable_to_related_person:
        return {"red_defer": True}
    l5 = D(selling_price); l6 = D(mortgages_assumed)
    l7 = l5 - l6
    l10 = D(cost_basis) - D(depreciation_allowed)
    l13 = l10 + D(commissions_expenses) + D(recapture_from_4797)
    l14 = l5 - l13
    l16 = max(D(0), l14 - D(excluded_gain_main_home))
    l17 = max(D(0), l6 - l13)
    l18 = l7 + l17
    l19 = (l16 / l18 if l18 > 0 else D(0)) if is_year_of_sale else D(prior_gross_profit_pct)
    l20 = l17 if is_year_of_sale else D(0)
    l22 = l20 + D(payments_current_year)
    l23 = D(payments_prior_years)
    l24 = max(D(0), l22 * l19)
    l25 = D(ordinary_recapture_portion)
    l26 = l24 - l25
    # Part III
    if related_party and related_party_resold and not rp_exception:
        l32 = min(D(rp_selling_price), l18)
        l34 = max(D(0), l32 - (l22 + l23))
        l35 = l34 * l19
        l37 = l35 - D(rp_ordinary_recapture)
    else:
        l35 = l37 = D(0)
    gain = l26 + l37
    f4797_line15 = l25 + D(rp_ordinary_recapture if (related_party and related_party_resold and not rp_exception) else 0)
    lt = int(holding_period_months or 0) > 12
    f4797_line4 = f4797_line10 = sch_d_st = sch_d_lt = D(0)
    if property_character == "business_1231" and lt:
        f4797_line4 = gain
    elif property_character == "ordinary" or not lt:
        f4797_line10 = gain
    else:
        if lt:
            sch_d_lt = gain
        else:
            sch_d_st = gain
    # §453A
    s453a = D(0)
    if l5 > _PRICE and D(aggregate_obligations_year_end) > _FIVE_M:
        outstanding = max(D(0), l18 - (l22 + l23))
        unrec = outstanding * l19
        rate = D(max_rate_ltcg) if (property_character in ("capital", "business_1231") and lt) else D(max_rate_ordinary)
        dtl = unrec * rate
        agg = D(aggregate_obligations_year_end)
        appl = (agg - _FIVE_M) / agg if agg > 0 else D(0)
        s453a = r0(dtl * appl * D(section_6621_rate))
    return {"l13": l13, "l16": l16, "l19": l19, "l24": l24, "l26": l26, "l35": l35, "l37": l37,
            "f4797_line4": f4797_line4, "f4797_line10": f4797_line10, "f4797_line15": f4797_line15,
            "sch_d_st": sch_d_st, "sch_d_lt": sch_d_lt, "section_453a_interest": s453a,
            "not_installment": l14 <= 0}


# ── 1. Scenarios — independent recompute + cross-check the loader ──
spec = m.FORMS[0]
DIAG_KEYS = {d["diagnostic_id"] for d in spec["diagnostics"]}
OUT_MAP = {"f6252_line13": "l13", "f6252_line16": "l16", "f6252_line19": "l19",
           "f6252_line24": "l24", "f6252_line26": "l26", "f6252_line35": "l35", "f6252_line37": "l37",
           "f4797_line4": "f4797_line4", "f4797_line10": "f4797_line10", "f4797_line15": "f4797_line15",
           "sch_d_st": "sch_d_st", "sch_d_lt": "sch_d_lt", "section_453a_interest": "section_453a_interest"}

for s in spec["scenarios"]:
    name = s["scenario_name"].split(" ")[0]
    inp = dict(s["inputs"])
    exp = s["expected_outputs"]
    diag_expected = {k for k in exp if k in DIAG_KEYS}
    if diag_expected:
        if "D_6252_001" in diag_expected and not inp.get("price_not_determinable"):
            err(f"{name}: D_6252_001 expected but price_not_determinable not set")
        if "D_6252_004" in diag_expected and not inp.get("depreciable_to_related_person"):
            err(f"{name}: D_6252_004 expected but depreciable_to_related_person not set")
        if "D_6252_002" in diag_expected:
            got = ind_6252(**inp)
            if got.get("red_defer") or not got.get("not_installment"):
                err(f"{name}: D_6252_002 expected but line 14 is not ≤ 0")
        continue
    got = ind_6252(**inp)
    gl = m.compute_6252(**inp)
    if got.get("red_defer") or gl.get("red_defer"):
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
        err(f"6252.{key}: duplicate ids")
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
        if k.startswith("D_6252_") and k not in diag_ids:
            err(f"{sc['scenario_name']}: expects unknown diagnostic {k}")
fa_ids = [a["assertion_id"] for a in m.FLOW_ASSERTIONS]
if len(fa_ids) != len(set(fa_ids)):
    err("duplicate flow-assertion ids")

# ── Report ──
print("Form 6252 (facts/rules/lines/diagnostics/scenarios/links):",
      (len(spec["facts"]), len(spec["rules"]), len(spec["lines"]),
       len(spec["diagnostics"]), len(spec["scenarios"]), len(spec["rule_links"])))
print(f"Flow assertions: {len(m.FLOW_ASSERTIONS)}; authority sources: {len(m.AUTHORITY_SOURCES)}")
print("Independently recomputed — T1 cap 8000 / T2 frozen-GP% 8000 / T3 §1245 split L24 10000→4797 L4 / "
      "T4 business §1231 20000→4797 L4 / T5 §453A interest 51200 / T6 related-party L35 24000 Sch D 32000; "
      "the GP%/contract-price arithmetic + Part III acceleration + §453A worksheet cross-checked.")

if errors:
    print("\nFAILURES:")
    for e in errors:
        print(f"  X {e}")
    sys.exit(1)
print("\nALL CHECKS PASS")
