"""Pre-seed math gate for load_1040_schedule_e (Schedule E Part I + Form 8582).

Run:  poetry run python check_schedule_e_8582_integrity.py

Independently recomputes every scenario from its OWN transcription of the §469
math — the $25,000 ($12,500 MFS-apart) special allowance, the 50%×($150k/$75k −
MAGI) phaseout (zero at $150k/$75k), the line-1d/2d/3 netting, and the
allowed/suspended split — and cross-checks the loader's constants + its shared
`special_allowance` helper cell-by-cell. The loader and this gate share NO math.
"""
import math
import os
import sys
from decimal import Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_schedule_e as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def check(name, got, want):
    if D(got) != D(want):
        err(f"{name}: recomputed {got} != authored {want}")


# ── Independent constants (re-typed from IRS i8582 / §469(i)) ──
IND_ALLOWANCE_MAX = 25000
IND_ALLOWANCE_MFS = 12500
IND_TOP = 150000
IND_TOP_MFS = 75000
IND_RATE = 0.50
IND_PHASEOUT_START = 100000   # = top − allowance/rate


def ind_special_allowance(net_loss, magi, mfs_apart, mfs_together):
    """The §469(i) active-participation allowance — independent transcription."""
    if mfs_together:
        return 0
    top = IND_TOP_MFS if mfs_apart else IND_TOP
    cap = IND_ALLOWANCE_MFS if mfs_apart else IND_ALLOWANCE_MAX
    if net_loss <= 0:
        return 0
    if magi >= top:
        line8 = 0
    else:
        line8 = min(math.floor(IND_RATE * (top - magi)), cap)
    return min(int(net_loss), line8)


def recompute_8582(inp):
    """Independent 8582: line 4 / line 9 / line 11 / suspended."""
    fs = inp["filing_status"]
    mfs_apart = bool(inp.get("mfs_lived_apart", False))
    mfs_together = (fs == "mfs" and not mfs_apart)
    if inp.get("real_estate_professional"):
        return {}  # RE-pro short-circuits to the RED; no numeric pins
    rental_loss = inp.get("rental_loss", 0)          # line 1b (positive)
    other_income = inp.get("other_income", 0)        # line 2a
    other_loss = inp.get("other_loss", 0)            # line 2b
    rental_prior = inp.get("rental_prior", 0)        # line 1c
    other_prior = inp.get("other_prior", 0)          # line 2c
    line1d = inp.get("rental_income", 0) - rental_loss - rental_prior
    line2d = other_income - other_loss - other_prior
    line3 = line1d + line2d
    # line 4 = smaller of the loss on 1d or the loss on line 3 (positive)
    loss_1d = -line1d if line1d < 0 else 0
    loss_3 = -line3 if line3 < 0 else 0
    line4 = min(loss_1d, loss_3)
    allowance = ind_special_allowance(line4, inp.get("magi", 0), mfs_apart, mfs_together)
    line10_income = inp.get("rental_income", 0) + other_income
    total_allowed = allowance + line10_income
    gross_losses = rental_loss + rental_prior + other_loss + other_prior
    suspended = max(0, gross_losses - total_allowed)
    return {"f8582_smaller_loss": line4, "f8582_special_allowance": allowance,
            "f8582_total_allowed": total_allowed, "f8582_suspended": suspended}


def recompute_per_activity(inp):
    """Independent per-activity 8582 (Parts IV-VIII): line 9 / line C and each LOSS
    activity's allowed + suspended. Mirrors NO loader code — re-typed from the
    f8582.pdf Part IV-VIII line definitions + i8582 (2025)."""
    fs = inp["filing_status"]
    mfs_apart = bool(inp.get("mfs_lived_apart", False))
    mfs_together = (fs == "mfs" and not mfs_apart)
    magi = inp.get("magi", 0)
    acts = []
    for a in inp["activities"]:
        inc, loss, prior = a.get("income", 0), a.get("loss", 0), a.get("prior", 0)
        overall = inc - loss - prior
        acts.append({"name": a["name"], "bucket": a["bucket"], "inc": inc,
                     "col_e": (-overall if overall < 0 else 0),  # overall loss (positive)
                     "gross": loss + prior})                     # Part VIII col (a)
    IV = [a for a in acts if a["bucket"] == "IV"]
    V = [a for a in acts if a["bucket"] == "V"]
    line1d = sum(a["inc"] for a in IV) - sum(a["gross"] for a in IV)
    line2d = sum(a["inc"] for a in V) - sum(a["gross"] for a in V)
    line3 = line1d + line2d
    out = {"f8582_special_allowance": 0, "f8582_line_c": 0,
           "f8582_total_allowed": 0, "f8582_suspended": 0, "per_activity": []}
    if line3 >= 0:                                        # line 3 >= 0 -> all losses allowed
        for a in acts:
            if a["col_e"] > 0:
                out["per_activity"].append({"name": a["name"], "allowed": a["gross"], "suspended": 0})
        out["f8582_total_allowed"] = sum(a["gross"] for a in acts if a["col_e"] > 0)
        return out
    loss_1d = -line1d if line1d < 0 else 0
    loss_3 = -line3 if line3 < 0 else 0
    line4 = min(loss_1d, loss_3)
    line9 = ind_special_allowance(line4, magi, mfs_apart, mfs_together)
    line_c = loss_3 - line9
    # Part VI — allocate line 9 across active-rental loss activities by loss-ratio
    iv_losses = [a for a in IV if a["col_e"] > 0]
    tot_iv = sum(a["col_e"] for a in iv_losses)
    for a in iv_losses:
        a["vi_remaining"] = a["col_e"] - (line9 * a["col_e"] / tot_iv if tot_iv else 0)
    # Part VII — allocate line C across the pool [Part VI col(d) + Part V col(e)] by loss-ratio
    pool = [(a, a["vi_remaining"]) for a in iv_losses] + [(a, a["col_e"]) for a in V if a["col_e"] > 0]
    tot_pool = sum(b for _, b in pool)
    total_allowed = 0
    for a, basis in pool:
        unallowed = (line_c * basis / tot_pool) if tot_pool else 0   # Part VII col (c)
        allowed = a["gross"] - unallowed                              # Part VIII col (c)
        out["per_activity"].append({"name": a["name"], "allowed": allowed, "suspended": unallowed})
        total_allowed += allowed
    out["f8582_special_allowance"] = line9
    out["f8582_line_c"] = line_c
    out["f8582_total_allowed"] = total_allowed
    out["f8582_suspended"] = line_c
    return out


def recompute_sche(inp):
    """Independent Schedule E: line 21 net + line 26 (after the 8582 limit)."""
    before = inp.get("rents", 0) + inp.get("royalties", 0) - inp.get("expenses", 0)
    out = {"sche_income_before_limit": before}
    if before < 0 and inp.get("active_participation"):
        allowed = ind_special_allowance(-before, inp.get("magi", 0), False, False)
        out["sche_deductible_loss"] = -allowed
        out["sche_net"] = -allowed
    else:
        out["sche_net"] = before
    return out


# ── 1. Loader constants vs the independent transcription ──
check("SPECIAL_ALLOWANCE_MAX", m.SPECIAL_ALLOWANCE_MAX, IND_ALLOWANCE_MAX)
check("SPECIAL_ALLOWANCE_MFS", m.SPECIAL_ALLOWANCE_MFS, IND_ALLOWANCE_MFS)
check("PHASEOUT_TOP", m.PHASEOUT_TOP, IND_TOP)
check("PHASEOUT_TOP_MFS", m.PHASEOUT_TOP_MFS, IND_TOP_MFS)
check("PHASEOUT_RATE", m.PHASEOUT_RATE, IND_RATE)
# the phaseout-start identity ($150k − $25k/0.5 = $100k)
if IND_TOP - IND_ALLOWANCE_MAX / IND_RATE != IND_PHASEOUT_START:
    err("phaseout-start identity broken")
# the loader's shared helper agrees at sample points
for (loss, magi, mfs) in [(20000, 80000, False), (40000, 120000, False), (30000, 160000, False),
                          (10000, 40000, True), (3000, 130000, False), (25000, 100000, False)]:
    got = m.special_allowance(loss, magi, mfs)
    want = ind_special_allowance(loss, magi, mfs, False)
    if got != want:
        err(f"special_allowance({loss},{magi},mfs={mfs}) = {got} != {want}")
# property-type table 1-8
if set(m.SCHE_PROPERTY_TYPES) != set(range(1, 9)):
    err(f"SCHE_PROPERTY_TYPES keys {sorted(m.SCHE_PROPERTY_TYPES)} != 1..8")
# the MAGI add-back list is present (9 items, §199A absent)
if len(m.MAGI_ADDBACKS) != 9:
    err(f"MAGI_ADDBACKS has {len(m.MAGI_ADDBACKS)} items, expected 9")
if any("199A" in s for s in m.MAGI_ADDBACKS):
    err("MAGI_ADDBACKS must NOT include §199A")

# ── 2. FORM_8582 scenarios — independent recompute (aggregate + per-activity) ──
DIAG_KEYS_8582 = {"D_8582_RE_PRO", "D_8582_MFS_TOGETHER", "D_8582_SUSPENDED",
                  "D_8582_PHASEOUT", "D_8582_005", "D_8582_DISPOSITION", "D_8582_MULTIFORM"}
f8582_spec = next(s for s in m.FORMS if s["identity"]["form_number"] == "FORM_8582")
for s in f8582_spec["scenarios"]:
    name = s["scenario_name"].split(" ")[0]
    inp, exp = s["inputs"], s["expected_outputs"]
    per_activity = "activities" in inp
    got = recompute_per_activity(inp) if per_activity else recompute_8582(inp)
    for k, want in exp.items():
        if k in DIAG_KEYS_8582:
            continue
        if k == "per_activity":
            got_pa = {p["name"]: p for p in got.get("per_activity", [])}
            for wp in want:
                gp = got_pa.get(wp["name"])
                if gp is None:
                    err(f"{name}.per_activity[{wp['name']}]: not recomputed")
                    continue
                check(f"{name}.{wp['name']}.allowed", gp["allowed"], wp["allowed"])
                check(f"{name}.{wp['name']}.suspended", gp["suspended"], wp["suspended"])
            # conservation: sum(allowed) == line 11; sum(suspended) == line C
            check(f"{name}.sum_allowed", sum(p["allowed"] for p in got["per_activity"]), got["f8582_total_allowed"])
            check(f"{name}.sum_suspended", sum(p["suspended"] for p in got["per_activity"]), got["f8582_line_c"])
            continue
        if k not in got:
            err(f"{name}.{k}: no independent recompute mapped")
            continue
        check(f"{name}.{k}", got[k], want)
    if exp.get("D_8582_RE_PRO") and not inp.get("real_estate_professional"):
        err(f"{name}: D_8582_RE_PRO expected without the RE-pro flag")
    if exp.get("D_8582_MFS_TOGETHER") and not (inp.get("filing_status") == "mfs" and not inp.get("mfs_lived_apart")):
        err(f"{name}: D_8582_MFS_TOGETHER expected without the MFS-together condition")
    if exp.get("D_8582_MULTIFORM") and not any(a.get("losses_on_multiple_forms") for a in inp.get("activities", [])):
        err(f"{name}: D_8582_MULTIFORM expected without a multi-form activity flag")

# ── 3. SCHEDULE_E scenarios — independent recompute ──
sche_spec = next(s for s in m.FORMS if s["identity"]["form_number"] == "SCHEDULE_E")
for s in sche_spec["scenarios"]:
    name = s["scenario_name"].split(" ")[0]
    inp, exp = s["inputs"], s["expected_outputs"]
    got = recompute_sche(inp)
    for k, want in exp.items():
        if k not in got:
            err(f"{name}.{k}: no independent recompute mapped")
            continue
        check(f"{name}.{k}", got[k], want)

# ── 4. Structural checks (both forms) ──
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
        for k in sc["expected_outputs"]:
            if k.startswith("D_") and k not in diag_ids:
                err(f"{fn}/{sc['scenario_name']}: expects unknown diagnostic {k}")

fa_ids = [a["assertion_id"] for a in m.FLOW_ASSERTIONS]
if len(fa_ids) != len(set(fa_ids)):
    err("duplicate flow-assertion ids")

# ── Report ──
for spec in m.FORMS:
    fn = spec["identity"]["form_number"]
    print(f"{fn} (facts/rules/lines/diagnostics/scenarios/links):",
          (len(spec["facts"]), len(spec["rules"]), len(spec["lines"]),
           len(spec["diagnostics"]), len(spec["scenarios"]), len(spec["rule_links"])))
print(f"Flow assertions: {len(m.FLOW_ASSERTIONS)}; authority sources: {len(m.AUTHORITY_SOURCES)}")
print("Independently recomputed — 8582: T1 $20k loss MAGI $80k -> all allowed / T2 $40k @120k -> $15k "
      "allowed, $25k suspended / T3 @$160k -> $0 / T4 MFS-apart $10k -> $12,500 cap / T5 income offset "
      "-> $8k allowed; G2 MFS-together -> $0. SchE: T1 +9,000 / T2 active loss -20,000 / T3 phaseout "
      "-15,000 / T4 royalty +4,200. $25k/$12,500 + the $150k/$75k phaseout + the netting cross-checked.")

if errors:
    print("\nFAILURES:")
    for e in errors:
        print(f"  X {e}")
    sys.exit(1)
print("\nALL CHECKS PASS")
