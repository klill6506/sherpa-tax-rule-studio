"""Pre-seed content checker for load_1040_form_8995a (Form 8995-A — above-threshold QBI).

Run:  poetry run python check_8995a_integrity.py
  (or call the venv python directly if `poetry run` hangs — see the dev-loop memory.)

Mirrors check_topic8_integrity.py: validates the authored lists WITHOUT touching the
DB, then INDEPENDENTLY recomputes every numeric scenario from its OWN transcription of
the Form 8995-A math (Schedule A SSTB applicable %, Schedule B aggregation combine,
Schedule C loss netting, Part II W-2/UBIA limit, Part III phase-in, Part IV income
limit). This is the MATH GATE that must pass before Ken's review walk. The checker
carries its OWN copies of the year-keyed constants and cross-checks the loader's module
constants cell-by-cell, so a transcription error in the loader cannot also pass here.
"""
import os
import re
from decimal import Decimal, ROUND_HALF_UP

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_form_8995a as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def cents(x):
    return D(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def check(name, got, want):
    if cents(got) != cents(want):
        err(f"{name}: recomputed {got} != authored {want}")


# ═══════════════════════════════════════════════════════════════════════════
# INDEPENDENT CONSTANTS (re-typed from the cited sources; NOT imported)
# ═══════════════════════════════════════════════════════════════════════════

IND_RATE = Decimal("0.20")
IND_THRESHOLDS = {
    2025: {"mfj": 394600, "mfs": 197300, "other": 197300},   # i8995a (2025)
    2026: {"mfj": 403500, "mfs": 201775, "other": 201750},   # RP 2025-32 §4.26
}
IND_RANGE = {"mfj": 100000, "mfs": 50000, "other": 50000}    # §199A(b)(3)(B)(ii)


def skey(status):
    return status if status in ("mfj", "mfs") else "other"


def threshold(year, status):
    return IND_THRESHOLDS[year][skey(status)]


def prange(status):
    return IND_RANGE[skey(status)]


def ceiling(year, status):
    return threshold(year, status) + prange(status)


# ═══════════════════════════════════════════════════════════════════════════
# INDEPENDENT 8995-A ENGINE (own transcription)
# ═══════════════════════════════════════════════════════════════════════════

def compute_8995a(year, status, ti, ncg, businesses, reit_income=0, reit_cf_prior=0,
                  qbi_cf_prior=0):
    ti = D(ti)
    thr = D(threshold(year, status))
    rng = D(prange(status))
    ceil = D(ceiling(year, status))

    # ---- normalize business dicts (copies) ----
    biz = [dict(qbi=D(b.get("qbi", 0)), w2=D(b.get("w2", 0)), ubia=D(b.get("ubia", 0)),
                sstb=bool(b.get("sstb")), patron=bool(b.get("patron")), agg=b.get("agg"))
           for b in businesses]

    # ---- Schedule A: SSTB applicable % (in-band reduction / above-ceiling exclusion) ----
    if rng > 0:
        applicable = max(Decimal(0), min(Decimal(1), (ceil - ti) / rng))
    else:
        applicable = Decimal(1)
    for b in biz:
        if b["sstb"]:
            b["qbi"] *= applicable
            b["w2"] *= applicable
            b["ubia"] *= applicable

    # ---- Schedule B: aggregation combine (group members sharing 'agg') ----
    groups: dict = {}
    standalone = []
    for b in biz:
        if b["agg"]:
            groups.setdefault(b["agg"], []).append(b)
        else:
            standalone.append(b)
    agg_combined = {}
    columns = []
    for gid, members in groups.items():
        col = dict(qbi=sum((mm["qbi"] for mm in members), Decimal(0)),
                   w2=sum((mm["w2"] for mm in members), Decimal(0)),
                   ubia=sum((mm["ubia"] for mm in members), Decimal(0)))
        agg_combined[gid] = col
        columns.append(col)
    columns += [dict(qbi=b["qbi"], w2=b["w2"], ubia=b["ubia"]) for b in standalone]

    # ---- Schedule C: loss netting (apportion total loss pro-rata by QBI) ----
    total_loss = D(qbi_cf_prior) + sum((c["qbi"] for c in columns if c["qbi"] < 0), Decimal(0))
    pos = [c for c in columns if c["qbi"] > 0]
    sum_pos = sum((c["qbi"] for c in pos), Decimal(0))
    carryforward_out = Decimal(0)
    if total_loss < 0:
        if sum_pos > 0:
            net = sum_pos + total_loss
            if net <= 0:
                for c in pos:
                    c["adj"] = Decimal(0)
                carryforward_out = net  # negative remainder
            else:
                for c in pos:
                    c["adj"] = c["qbi"] + total_loss * (c["qbi"] / sum_pos)
        else:
            carryforward_out = total_loss  # nothing to absorb it
        for c in columns:
            if c["qbi"] <= 0:
                c["adj"] = Decimal(0)
    else:
        for c in columns:
            c["adj"] = max(c["qbi"], Decimal(0))

    # adjusted QBI ≤ 0 ⇒ that column's W-2/UBIA = 0 (i8995a)
    for c in columns:
        if c["adj"] <= 0:
            c["w2"] = Decimal(0)
            c["ubia"] = Decimal(0)

    # ---- Part II / III per column ----
    in_band = thr < ti <= ceil
    col_lines = []
    for c in columns:
        L2 = c["adj"]
        L3 = L2 * IND_RATE
        L4 = c["w2"]
        L5 = L4 * Decimal("0.50")
        L6 = L4 * Decimal("0.25")
        L7 = c["ubia"]
        L8 = L7 * Decimal("0.025")
        L9 = L6 + L8
        L10 = max(L5, L9)
        L11 = min(L3, L10)
        # Part III phase-in (per column)
        L12 = None
        L24 = L25 = L26 = None
        if in_band and L10 < L3:
            L19 = L3 - L10
            L22 = ti - thr
            L24 = L22 / rng
            L25 = L19 * L24
            L26 = L3 - L25
            L12 = L26
        L13 = max(L11, L12) if L12 is not None else L11
        L14 = Decimal(0)  # patron RED-defer
        L15 = L13 - L14
        col_lines.append(dict(L2=L2, L3=L3, L4=L4, L5=L5, L6=L6, L7=L7, L8=L8, L9=L9,
                              L10=L10, L11=L11, L12=L12, L13=L13, L15=L15, L24=L24,
                              L25=L25, L26=L26))

    L16 = sum((cl["L15"] for cl in col_lines), Decimal(0))

    # ---- Part IV ----
    L27 = L16
    L28 = D(reit_income)
    L29 = D(reit_cf_prior)
    L30 = max(Decimal(0), L28 + L29)
    L31 = L30 * IND_RATE
    L32 = L27 + L31
    L33 = ti
    L34 = D(ncg)
    L35 = max(Decimal(0), L33 - L34)
    L36 = L35 * IND_RATE
    L37 = min(L32, L36)
    L38 = Decimal(0)  # DPAD RED-defer
    L39 = L37 + L38
    L40 = min(Decimal(0), L28 + L29)

    # primary column = the one with the largest adjusted QBI (the dominant business)
    primary = max(col_lines, key=lambda cl: cl["L2"]) if col_lines else {}

    return dict(applicable=applicable, columns=columns, col_lines=col_lines,
                agg_combined=agg_combined, carryforward_out=carryforward_out,
                primary=primary, L16=L16, L27=L27, L28=L28, L30=L30, L31=L31,
                L32=L32, L33=L33, L34=L34, L35=L35, L36=L36, L37=L37, L39=L39, L40=L40)


# ═══════════════════════════════════════════════════════════════════════════
# 1. CONSTANT CROSS-CHECK (loader vs independent)
# ═══════════════════════════════════════════════════════════════════════════

if D(m.QBI_RATE) != IND_RATE:
    err(f"QBI_RATE: loader {m.QBI_RATE} != {IND_RATE}")
for yr in (2025, 2026):
    for st in ("mfj", "mfs", "other"):
        if m.QBI_THRESHOLDS[yr][st] != IND_THRESHOLDS[yr][st]:
            err(f"threshold[{yr}][{st}]: loader {m.QBI_THRESHOLDS[yr][st]} != {IND_THRESHOLDS[yr][st]}")
        if m.PHASE_IN_RANGE[st] != IND_RANGE[st]:
            err(f"range[{st}]: loader {m.PHASE_IN_RANGE[st]} != {IND_RANGE[st]}")
# ceiling derivation sanity
if m.ceiling_for(2025, "single") != 247300:
    err(f"ceiling_for(2025,single) {m.ceiling_for(2025,'single')} != 247300")
if m.ceiling_for(2025, "mfj") != 494600:
    err(f"ceiling_for(2025,mfj) {m.ceiling_for(2025,'mfj')} != 494600")


# ═══════════════════════════════════════════════════════════════════════════
# 2. STRUCTURAL CHECKS (RS varchar(20) id cap; required keys; uniqueness)
# ═══════════════════════════════════════════════════════════════════════════

for r in m.F8995A_RULES:
    if len(r["rule_id"]) > 20:
        err(f"rule_id too long (>20): {r['rule_id']} ({len(r['rule_id'])})")
for d in m.F8995A_DIAGNOSTICS:
    if len(d["diagnostic_id"]) > 20:
        err(f"diagnostic_id too long (>20): {d['diagnostic_id']} ({len(d['diagnostic_id'])})")
for ln in m.F8995A_LINES:
    if len(ln["line_number"]) > 20:
        err(f"line_number too long (>20): {ln['line_number']} ({len(ln['line_number'])})")

# rule_links reference real rules + a known source set
rule_ids = {r["rule_id"] for r in m.F8995A_RULES}
for rid, *_ in m.F8995A_RULE_LINKS:
    if rid not in rule_ids:
        err(f"rule_link references unknown rule_id {rid}")

# every fact referenced by a rule input/output that is a fact_key must exist
fact_keys = {f["fact_key"] for f in m.F8995A_FACTS}
for r in m.F8995A_RULES:
    for fk in r.get("inputs", []):
        if fk.startswith("a_") and fk not in fact_keys:
            err(f"rule {r['rule_id']} input {fk} not a declared fact")

# line uniqueness
seen = set()
for ln in m.F8995A_LINES:
    if ln["line_number"] in seen:
        err(f"duplicate line_number {ln['line_number']}")
    seen.add(ln["line_number"])


# ═══════════════════════════════════════════════════════════════════════════
# 3. SCENARIO RE-DERIVATION (the math gate)
# ═══════════════════════════════════════════════════════════════════════════

PER_COL = {"line_2", "line_3", "line_4", "line_5", "line_6", "line_7", "line_8",
           "line_9", "line_10", "line_11", "line_12", "line_13", "line_15",
           "line_24", "line_25", "line_26"}
AGG = {"line_16", "line_27", "line_30", "line_31", "line_32", "line_33", "line_34",
       "line_35", "line_36", "line_37", "line_39", "line_40"}

for sc in m.F8995A_SCENARIOS:
    name = sc["scenario_name"]
    inp = sc["inputs"]
    exp = sc["expected_outputs"]
    res = compute_8995a(
        inp["tax_year"], inp["filing_status"], inp["a_taxable_income_before_qbi"],
        inp.get("a_net_capital_gain", 0), inp.get("businesses", []),
        reit_income=inp.get("a_reit_ptp_income", 0),
        reit_cf_prior=inp.get("a_reit_ptp_carryforward_prior", 0),
        qbi_cf_prior=inp.get("a_qbi_loss_carryforward_prior", 0),
    )
    prim = res["primary"]
    for key, want in exp.items():
        if key in ("D_8995A_001", "D_8995A_004"):
            # diagnostic booleans
            if key == "D_8995A_001":
                got = any(b.get("patron") for b in inp.get("businesses", []))
            else:  # D_8995A_004: SSTB above ceiling
                got = any(b.get("sstb") for b in inp.get("businesses", [])) and \
                    D(inp["a_taxable_income_before_qbi"]) > ceiling(inp["tax_year"], inp["filing_status"])
            if bool(got) != bool(want):
                err(f"{name} :: {key} recomputed {got} != authored {want}")
        elif key == "a_sstb_applicable_pct":
            if cents(res["applicable"]) != cents(want):
                err(f"{name} :: applicable% {res['applicable']} != {want}")
        elif key.startswith("SC-1C_business"):
            idx = int(re.search(r"(\d+)$", key).group(1))
            got = res["columns"][idx]["adj"] if idx < len(res["columns"]) else None
            check(f"{name} :: {key}", got, want)
        elif key in ("SB-AGG-QBI", "SB-AGG-W2", "SB-AGG-UBIA"):
            if not res["agg_combined"]:
                err(f"{name} :: {key} — no aggregation group computed")
            else:
                col = list(res["agg_combined"].values())[0]
                fld = {"SB-AGG-QBI": "qbi", "SB-AGG-W2": "w2", "SB-AGG-UBIA": "ubia"}[key]
                check(f"{name} :: {key}", col[fld], want)
        elif key == "line_14":
            # patron reduction — RED-deferred, always 0 in v1
            check(f"{name} :: line_14 (patron reduction, v1=0)", 0, want)
        elif key == "a_qbi_carryforward_out":
            check(f"{name} :: carryforward_out", res["carryforward_out"], want)
        elif key in AGG:
            check(f"{name} :: {key}", res[key.replace("line_", "L")], want)
        elif key in PER_COL:
            lk = key.replace("line_", "L")
            got = prim.get(lk)
            if got is None:
                err(f"{name} :: {key} — primary column has no {lk} (Part III not triggered?)")
            else:
                check(f"{name} :: {key}", got, want)
        else:
            err(f"{name} :: unhandled expected key {key}")


# ═══════════════════════════════════════════════════════════════════════════
# 4. TEXT PINS (guard the verified line semantics against drift)
# ═══════════════════════════════════════════════════════════════════════════

line_desc = {ln["line_number"]: ln["description"].lower() for ln in m.F8995A_LINES}
if "smaller of line 3 or line 10" not in line_desc.get("11", ""):
    err("line 11 description drifted from 'smaller of line 3 or line 10'")
if "greater of line 11 or line 12" not in line_desc.get("13", ""):
    err("line 13 description drifted from 'greater of line 11 or line 12'")
if "form 1040 line 13" not in line_desc.get("39", ""):
    err("line 39 must route to Form 1040 line 13")


# ═══════════════════════════════════════════════════════════════════════════
print("=" * 64)
if errors:
    print(f"FAIL - {len(errors)} issue(s):")
    for e in errors:
        print(f"  x {e}")
    raise SystemExit(1)
print("check_8995a_integrity: ALL CHECKS PASS")
print(f"  {len(m.F8995A_SCENARIOS)} scenarios re-derived; "
      f"{len(m.F8995A_RULES)} rules / {len(m.F8995A_LINES)} lines / "
      f"{len(m.F8995A_DIAGNOSTICS)} diagnostics / {len(m.FLOW_ASSERTIONS)} FA")
print("=" * 64)
