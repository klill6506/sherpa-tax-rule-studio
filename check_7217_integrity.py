"""Pre-seed math gate for load_1040_form_7217 (§732 distributed-property basis,
ATS Scenario 12).

Run:  poetry run python check_7217_integrity.py

Independently recomputes every scenario from its OWN transcription of the
Form 7217 math — Part I lines 3/5b/5c/6/7/9/10 (§§731(a), 732(a)/(b), the
i7217 line-9 §737 include and 5a-only subtraction) and the FULL §732(c)
allocation waterfall (tier-1 hot assets at basis with the (c)(1)(A)(ii)
decrease, tier-2 other property with the (c)(2) increase / (c)(3) decrease,
the J4 rounding convention) — written against the statute text directly, NOT
copied from the loader. Cross-checks every scenario's expected_outputs,
verifies the diagnostics fire where asserted, and enforces the varchar(20)
id caps on rule_id / diagnostic_id / line_number (the
check_schedule_f_integrity guards).
"""
import os
import sys
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_form_7217 as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def rnd(x):
    """Whole-dollar, half-up (the suite convention; J4)."""
    return D(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def _d(s):
    return date.fromisoformat(s) if isinstance(s, str) else s


# ═══════════════════════════════════════════════════════════════════════════
# Independent §732(c) waterfall — transcribed from 26 U.S.C. §732(c)(1)-(3)
# (fetched verbatim 2026-07-02), NOT from the loader.
# ═══════════════════════════════════════════════════════════════════════════

def _apply_decrease(assigned, fmv, decrease):
    """§732(c)(3): (A) first to properties with unrealized depreciation in
    proportion to their respective amounts (capped at each property's
    depreciation); (B) then in proportion to their respective adjusted bases
    as adjusted under (A). `assigned` maps row-index -> current basis."""
    dep = {i: max(Decimal(0), assigned[i] - fmv[i]) for i in assigned}
    dep_total = sum(dep.values())
    if dep_total >= decrease > 0:
        for i in assigned:
            if dep_total:
                assigned[i] -= decrease * dep[i] / dep_total
        return assigned
    # (A) in full, then (B) over the adjusted bases
    for i in assigned:
        assigned[i] -= dep[i]
    excess = decrease - dep_total
    adj_total = sum(assigned.values())
    if excess > 0 and adj_total > 0:
        for i in assigned:
            assigned[i] -= excess * assigned[i] / adj_total
    return assigned


def _apply_increase(assigned, fmv, increase):
    """§732(c)(2): (A) first to properties with unrealized appreciation in
    proportion to their respective amounts (capped at each property's
    appreciation); (B) then in proportion to their respective FMVs."""
    app = {i: max(Decimal(0), fmv[i] - assigned[i]) for i in assigned}
    app_total = sum(app.values())
    if app_total >= increase > 0:
        for i in assigned:
            if app_total:
                assigned[i] += increase * app[i] / app_total
        return assigned
    for i in assigned:
        assigned[i] += app[i]
    excess = increase - app_total
    fmv_total = sum(fmv[i] for i in assigned)
    if excess > 0 and fmv_total > 0:
        for i in assigned:
            assigned[i] += excess * fmv[i] / fmv_total
    return assigned


def alloc_732c(props, allocable):
    """Returns (exact col-(e) list, withheld: bool). Withheld when any row is
    unclassified (J5). Tier-1 = 'hot' rows at basis, decrease-only;
    tier-2 = 'other' rows at basis with increase/decrease."""
    n = len(props)
    if any(p.get("category") is None for p in props):
        return [Decimal(0)] * n, True
    e = [Decimal(0)] * n
    basis = {i: D(props[i].get("pship_basis", 0)) for i in range(n)}
    fmv = {i: D(props[i].get("fmv", 0)) for i in range(n)}
    hot = [i for i in range(n) if props[i]["category"] == "hot"]
    other = [i for i in range(n) if props[i]["category"] == "other"]
    hot_total = sum(basis[i] for i in hot)
    if allocable < hot_total:
        assigned = _apply_decrease({i: basis[i] for i in hot}, fmv, hot_total - allocable)
        for i in hot:
            e[i] = assigned[i]
        return e, False  # tier-2 gets nothing (§732(c)(1)(B): no basis remains)
    for i in hot:
        e[i] = basis[i]
    remaining = allocable - hot_total
    if not other:
        return e, False  # the §731(a)(2) loss edge leaves remaining unallocated
    other_total = sum(basis[i] for i in other)
    assigned = {i: basis[i] for i in other}
    if remaining > other_total:
        assigned = _apply_increase(assigned, fmv, remaining - other_total)
    elif remaining < other_total:
        assigned = _apply_decrease(assigned, fmv, other_total - remaining)
    for i in other:
        e[i] = assigned[i]
    return e, False


def round_col_e(exact):
    """J4: round each half-up; force the rounded sum back to the exact sum
    (itself whole given whole-dollar inputs) on the largest-allocation row."""
    rounded = [rnd(x) for x in exact]
    target = rnd(sum(exact))
    residue = target - sum(rounded)
    if residue != 0 and rounded:
        idx = max(range(len(rounded)), key=lambda i: rounded[i])
        rounded[idx] += residue
    return rounded


def f7217(inp):
    """Independent transcription of the whole form."""
    year = inp["tax_year"]
    props = inp.get("properties", [])
    out = {}
    line4 = D(inp.get("outside_basis", 0))
    line5a = D(inp.get("cash_received", 0))
    sec_fmv = sum(D(p.get("fmv", 0)) for p in props if p.get("is_security", False))
    override = D(inp.get("securities_fmv_override", 0))
    line5b = override if override > 0 else sec_fmv
    line5c = line5a + line5b
    line6 = min(line4, line5c)
    line7 = line5c - line6
    gain737 = D(inp.get("gain_737", 0))
    line9 = max(Decimal(0), line4 - line5a) + gain737
    line3 = sum(D(p.get("pship_basis", 0)) for p in props)
    liq = bool(inp.get("liquidating", False))
    line10 = line9 if liq else min(line3, line9)
    exact_e, withheld = alloc_732c(props, line10)
    col_e = [Decimal(0)] * len(props) if withheld else round_col_e(exact_e)
    sum_e = sum(exact_e)
    loss = max(Decimal(0), line10 - sum_e) if (liq and not withheld) else Decimal(0)
    money_only = (not props) or all(p.get("is_security", False) for p in props)
    dd = _d(inp.get("distribution_date"))
    # J1 wire: the 8949 feed, gated on the holding-period assertion
    held = inp.get("interest_held_lt", None)
    feed_st = line7 if (line7 > 0 and held is False) else Decimal(0)
    feed_lt = line7 if (line7 > 0 and held is True) else Decimal(0)
    out.update({
        "f7217_line3": line3, "f7217_line5b": line5b, "f7217_line5c": line5c,
        "f7217_line6": line6, "f7217_line7": line7, "f7217_line9": line9,
        "f7217_line10": line10, "col_e": col_e, "f7217_loss_731a2": loss,
        "f7217_8949_st": feed_st, "f7217_8949_lt": feed_lt,
        "D_7217_001": inp.get("sec751b") is True,
        "D_7217_002": line7 > 0 and held is not None,
        "D_7217_003": money_only,
        "D_7217_004": (inp.get("outside_basis") is None or inp.get("liquidating") is None
                       or inp.get("sec751b") is None),
        "D_7217_005": bool(props) and line10 != line3,
        "D_7217_006": loss > 0,
        "D_7217_007": line7 > 0 and inp.get("us_tax_on_gain", None) is None,
        "D_7217_008": withheld,
        "D_7217_009": gain737 > 0,
        "D_7217_010": dd is not None and dd.year != year,
        "D_7217_011": line7 > 0 and held is None,
    })
    return out


# ═══════════════════════════════════════════════════════════════════════════
# 1. Statute-example self-test (the checker checks ITSELF against the IRS's
#    own worked Example 2 before checking the loader)
# ═══════════════════════════════════════════════════════════════════════════
_ex2, _wh = alloc_732c(
    [{"category": "hot", "pship_basis": 100, "fmv": 200},
     {"category": "other", "pship_basis": 50, "fmv": 400},
     {"category": "other", "pship_basis": 100, "fmv": 100}],
    Decimal(650))
if _wh or round_col_e(_ex2) != [Decimal(100), Decimal(440), Decimal(110)]:
    err(f"SELF-TEST: i7217 Example 2 waterfall -> {round_col_e(_ex2)} != [100, 440, 110]")

# ═══════════════════════════════════════════════════════════════════════════
# 2. Per-scenario recompute vs authored expected_outputs
# ═══════════════════════════════════════════════════════════════════════════
for sc in m.F7217_SCENARIOS:
    name = sc["scenario_name"].split(" — ")[0]
    got = f7217(sc["inputs"])
    for key, want in sc["expected_outputs"].items():
        if key == "col_e":
            g = [int(x) for x in got["col_e"]]
            if g != list(want):
                err(f"{name}.col_e: recomputed {g} != authored {want}")
        elif key.startswith("D_7217_"):
            if bool(got.get(key)) != bool(want):
                err(f"{name}.{key}: recomputed {got.get(key)} != authored {want}")
        else:
            if D(got.get(key)) != D(want):
                err(f"{name}.{key}: recomputed {got.get(key)} != authored {want}")

# ═══════════════════════════════════════════════════════════════════════════
# 3. Structural checks
# ═══════════════════════════════════════════════════════════════════════════
spec = m.FORMS[0]
fact_keys = {f["fact_key"] for f in spec["facts"]}
rule_ids = {r["rule_id"] for r in spec["rules"]}
diag_ids = {d["diagnostic_id"] for d in spec["diagnostics"]}
line_nums = {ln["line_number"] for ln in spec["lines"]}

# varchar(20) caps (the RS DataError guards)
for rid in rule_ids:
    if len(rid) > 20:
        err(f"rule_id too long (>20): {rid}")
for did in diag_ids:
    if len(did) > 20:
        err(f"diagnostic_id too long (>20): {did}")
for ln in line_nums:
    if len(ln) > 20:
        err(f"line_number too long (>20): {ln}")

# every rule input/output is a declared fact
for r in spec["rules"]:
    for k in list(r.get("inputs", [])) + list(r.get("outputs", [])):
        if k not in fact_keys:
            err(f"{r['rule_id']}: references undeclared fact '{k}'")

# every rule carries >=1 authority link; links reference real rules/sources
linked = {rl[0] for rl in spec["rule_links"]}
source_codes = {s["source_code"] for s in m.AUTHORITY_SOURCES} | set(m.EXISTING_SOURCES_TO_REFERENCE)
for rid in rule_ids - linked:
    err(f"rule {rid} has NO authority link")
for rl in spec["rule_links"]:
    if rl[0] not in rule_ids:
        err(f"rule_link references unknown rule '{rl[0]}'")
    if rl[1] not in source_codes:
        err(f"rule_link references unknown source '{rl[1]}'")

# every diagnostic asserted in a scenario exists; every diagnostic is exercised
asserted = set()
for sc in m.F7217_SCENARIOS:
    for key in sc["expected_outputs"]:
        if key.startswith("D_7217_"):
            asserted.add(key)
            if key not in diag_ids:
                err(f"{sc['scenario_name']}: asserts unknown diagnostic {key}")
for did in sorted(diag_ids - asserted):
    err(f"diagnostic {did} is never exercised by any scenario")

# FA sanity
fa_ids = [a["assertion_id"] for a in m.FLOW_ASSERTIONS]
if len(fa_ids) != len(set(fa_ids)):
    err("duplicate flow-assertion ids")
for aid in fa_ids:
    if not aid.startswith("FA-1040-7217-"):
        err(f"unexpected FA id prefix: {aid}")

# expected_output keys must be known outputs / diagnostics / col_e
known_out = {f["fact_key"] for f in spec["facts"]} | {"col_e"} | diag_ids
for sc in m.F7217_SCENARIOS:
    for key in sc["expected_outputs"]:
        if key not in known_out:
            err(f"{sc['scenario_name']}: expected key '{key}' is not a declared fact/diagnostic/col_e")

# ═══════════════════════════════════════════════════════════════════════════
print(f"READY_TO_SEED = {m.READY_TO_SEED}")
print(f"Scenarios checked: {len(m.F7217_SCENARIOS)} | facts {len(fact_keys)} | rules {len(rule_ids)} | "
      f"lines {len(line_nums)} | diagnostics {len(diag_ids)} | FAs {len(fa_ids)}")
if errors:
    print(f"\nFAILED — {len(errors)} error(s):")
    for e in errors:
        print(f"  [X] {e}")
    sys.exit(1)
print("\nALL CHECKS PASS")
