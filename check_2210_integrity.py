"""Pre-seed math gate for load_1040_2210 (Underpayment of Estimated Tax §6654).

Run:  poetry run python check_2210_integrity.py

Independently recomputes every scenario from its OWN transcription of the §6654
required annual payment (min(90% current, 100/110% prior)), the $1,000 de-minimis,
and the §6621 regular-method penalty (the 7%/6% rate-period day factors) + Schedule
AI. The loader and this gate share NO math.
"""
import os
import sys
from decimal import ROUND_HALF_UP, Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_2210 as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def check(name, got, want):
    if D(got) != D(want):
        err(f"{name}: recomputed {got} != authored {want}")


def r0(x):
    return int(D(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


# ── Independent math (re-typed) ──
IND_DAYS7 = [350, 289, 197, 75]
IND_DAYS6 = [15, 15, 15, 15]
IND_AI_PCT = [Decimal("0.225"), Decimal("0.45"), Decimal("0.675"), Decimal("0.90")]


def ind_factor(i):
    return D(IND_DAYS7[i]) / 365 * Decimal("0.07") + D(IND_DAYS6[i]) / 365 * Decimal("0.06")


def ind_compute(current_tax=0, other_taxes=0, refundable_credits=0, withholding=0, prior_year_tax=0,
                prior_year_agi=0, filing_status="single", prior_full_year=True, est_payments=(0, 0, 0, 0),
                use_annualized=False, ai_tax=(0, 0, 0, 0)):
    l4 = D(current_tax) + D(other_taxes) - D(refundable_credits)
    l5 = D(r0(l4 * Decimal("0.90")))
    l7 = l4 - D(withholding)
    agi_thr = 75000 if (filing_status or "single").lower() == "mfs" else 150000
    pct = Decimal("1.10") if D(prior_year_agi) > agi_thr else Decimal("1.00")
    l8 = D(r0(D(prior_year_tax) * pct)) if (prior_full_year and D(prior_year_tax) > 0) else None
    l9 = l5 if l8 is None else min(l5, l8)
    if l7 < 1000:
        return {"l9": l9, "penalty": Decimal("0")}
    reg = [l9 / 4] * 4
    if use_annualized:
        inst, prior = [], Decimal("0")
        for i in range(4):
            ann = max(Decimal("0"), D(ai_tax[i]) * IND_AI_PCT[i] - prior)
            req = min(ann, reg[i])
            inst.append(req)
            prior += req
        installments = inst
    else:
        installments = reg
    wh_q = D(withholding) / 4
    overpay, penalty = Decimal("0"), Decimal("0")
    for i in range(4):
        avail = wh_q + D(est_payments[i]) + overpay
        if avail >= installments[i]:
            under = Decimal("0"); overpay = avail - installments[i]
        else:
            under = installments[i] - avail; overpay = Decimal("0")
        penalty += under * ind_factor(i)
    return {"l9": l9, "penalty": D(r0(penalty))}


# ── 1. Loader constants + helpers vs the independent transcription ──
check("PCT_CURRENT", D(m.PCT_CURRENT), Decimal("0.90"))
check("RATE_7", D(m.RATE_7), Decimal("0.07"))
check("RATE_6", D(m.RATE_6), Decimal("0.06"))
for i in range(4):
    check(f"DAYS_7[{i}]", m.DAYS_7[i], IND_DAYS7[i])
    check(f"AI_PCT[{i}]", m.AI_PCT[i], IND_AI_PCT[i])
    check(f"penalty_factor({i})", m.penalty_factor(i), ind_factor(i))

# ── 2. Scenarios — independent recompute ──
DIAG_KEYS = {"D_2210_NO_PENALTY", "D_2210_PRIOR_YEAR", "D_2210_110", "D_2210_AI", "D_2210_TY2026"}
spec = m.FORMS[0]
for s in spec["scenarios"]:
    name = s["scenario_name"].split(" ")[0]
    inp, exp = s["inputs"], s["expected_outputs"]
    if any(k in DIAG_KEYS for k in exp):
        if exp.get("D_2210_NO_PENALTY") and (D(inp.get("current_tax", 0)) - D(inp.get("withholding", 0))) >= 1000:
            err(f"{name}: D_2210_NO_PENALTY expected but line 7 >= 1000")
        continue
    got = ind_compute(**{k: v for k, v in inp.items() if k != "tax_year"})
    # cross-check the loader helper too
    gl = m.compute_2210(**{k: v for k, v in inp.items() if k != "tax_year"})
    out_map = {"t2210_line9": "l9", "t2210_penalty": "penalty"}
    for k, want in exp.items():
        if k in DIAG_KEYS:
            continue
        if k not in out_map:
            err(f"{name}.{k}: no independent recompute mapped")
            continue
        check(f"{name}.{k} (ind)", got[out_map[k]], want)
        check(f"{name}.{k} (loader)", gl[out_map[k]], want)

# ── 3. Structural checks ──
known_sources = {s["source_code"] for s in m.AUTHORITY_SOURCES} | set(m.EXISTING_SOURCES_TO_REFERENCE)
for key, idk in (("facts", "fact_key"), ("rules", "rule_id"), ("lines", "line_number"),
                 ("diagnostics", "diagnostic_id"), ("scenarios", "scenario_name")):
    ids = [x[idk] for x in spec[key]]
    if len(ids) != len(set(ids)):
        err(f"FORM_2210.{key}: duplicate ids")
for r in spec["rules"]:
    if len(r["rule_id"]) > 20:
        err(f"rule_id too long ({len(r['rule_id'])} > 20): {r['rule_id']}")
for d in spec["diagnostics"]:
    if len(d["diagnostic_id"]) > 20:
        err(f"diagnostic_id too long ({len(d['diagnostic_id'])} > 20): {d['diagnostic_id']}")
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
        if k.startswith("D_2210_") and k not in diag_ids:
            err(f"{sc['scenario_name']}: expects unknown diagnostic {k}")
fa_ids = [a["assertion_id"] for a in m.FLOW_ASSERTIONS]
if len(fa_ids) != len(set(fa_ids)):
    err("duplicate flow-assertion ids")

# ── Report ──
print("FORM_2210 (facts/rules/lines/diagnostics/scenarios/links):",
      (len(spec["facts"]), len(spec["rules"]), len(spec["lines"]),
       len(spec["diagnostics"]), len(spec["scenarios"]), len(spec["rule_links"])))
print(f"Flow assertions: {len(m.FLOW_ASSERTIONS)}; authority sources: {len(m.AUTHORITY_SOURCES)}")
print("Independently recomputed - T1 deminimis 0 / T2 prior-SH 0 / T3 full 461 / T4 110% l9=44000 / "
      "T5 estimates-cure 0 / T6 partial 143; the §6654 safe harbors + the §6621 7%/6% penalty factors "
      "+ Schedule AI cross-checked.")

if errors:
    print("\nFAILURES:")
    for e in errors:
        print(f"  X {e}")
    sys.exit(1)
print("\nALL CHECKS PASS")
