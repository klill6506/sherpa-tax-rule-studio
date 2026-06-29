"""Pre-seed content checker for load_1040_retirement (Topic 5).

Run:  poetry run python check_retirement_integrity.py

Mirrors check_intdiv_integrity.py / check_sch123_integrity.py: validates the
authored lists WITHOUT touching the DB, then INDEPENDENTLY recomputes every
numeric scenario — the full Social Security Benefits Worksheet (18 lines,
transcribed independently from i1040gi p.31), Form 5329 Part I (the 10%/25%
additional tax), and the 1099-R aggregation to 1040 lines 4a/4b/5a/5b/25b.
This is the MATH GATE that must pass before Ken's review walk.

The checker carries its OWN transcription of the worksheet logic and the
statutory §86 constants ($25,000/$32,000 base; $9,000/$12,000 second tier;
50%/85% tiers) so a transcription error in the loader cannot also pass the
checker.
"""
import os
import sys
from decimal import Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_retirement as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def check(name, got, want):
    if D(got) != D(want):
        err(f"{name}: recomputed {got} != authored {want}")


# ═══════════════════════════════════════════════════════════════════════════
# Independent statutory constants (§86 — NON-indexed, identical 2025/2026)
# ═══════════════════════════════════════════════════════════════════════════

SS_BASE = {"mfj": 32000, "single": 25000, "hoh": 25000, "qss": 25000, "mfs": 25000}
SS_SECOND = {"mfj": 12000, "single": 9000, "hoh": 9000, "qss": 9000, "mfs": 9000}
TIER1 = Decimal("0.50")
TIER2 = Decimal("0.85")

# v1 supported sets (Ken-confirmed 2026-06-11) — transcribed independently.
SUPPORTED_CODES = set("1234789BDGHQSY")
SUPPORTED_EXCEPTIONS = {f"{n:02d}" for n in range(1, 24)} | {"99"}  # full i5329 catalog 01-23 + 99
EARLY_CODES = set("1JS")


# ═══════════════════════════════════════════════════════════════════════════
# Independent recomputations
# ═══════════════════════════════════════════════════════════════════════════

def ss_worksheet(ssa_box5, ws3_income, filing_status, mfs_with_spouse=False,
                 ws4_taxexempt=0, ws6_adjustments=0):
    """Social Security Benefits Worksheet (i1040gi p.31), all 18 lines.

    Returns a dict keyed by line number string ("1".."18") plus "6a"/"6b".
    Honors the two worksheet STOP conditions (line 7 and line 9) and the
    MFS-lived-with-spouse short-circuit (skip lines 8-15).
    """
    ws = {}
    ws["1"] = D(ssa_box5)          # -> 1040 line 6a
    ws["2"] = TIER1 * ws["1"]
    ws["3"] = D(ws3_income)        # 1040 1z+2b+3b+4b+5b+7a+8
    ws["4"] = D(ws4_taxexempt)     # 1040 line 2a
    ws["5"] = ws["2"] + ws["3"] + ws["4"]
    ws["6"] = D(ws6_adjustments)   # Sch 1 lines 11-20 + 23 + 25
    ws["6a"] = ws["1"]
    # Line 7: "Is line 6 less than line 5?" No -> none taxable.
    if ws["6"] >= ws["5"]:
        ws["7"] = Decimal("0")
        ws["6b"] = Decimal("0")
        return ws
    ws["7"] = ws["5"] - ws["6"]
    # MFS lived with spouse: skip 8-15, tax 85% from dollar one.
    if mfs_with_spouse:
        ws["16"] = TIER2 * ws["7"]
        ws["17"] = TIER2 * ws["1"]
        ws["18"] = min(ws["16"], ws["17"])
        ws["6b"] = ws["18"]
        return ws
    ws["8"] = D(SS_BASE[filing_status])
    # Line 9: "Is line 8 less than line 7?" No -> none taxable.
    if ws["8"] >= ws["7"]:
        ws["9"] = Decimal("0")
        ws["6b"] = Decimal("0")
        return ws
    ws["9"] = ws["7"] - ws["8"]
    ws["10"] = D(SS_SECOND[filing_status])
    ws["11"] = max(Decimal("0"), ws["9"] - ws["10"])
    ws["12"] = min(ws["9"], ws["10"])
    ws["13"] = TIER1 * ws["12"]
    ws["14"] = min(ws["2"], ws["13"])
    ws["15"] = TIER2 * ws["11"]
    ws["16"] = ws["14"] + ws["15"]
    ws["17"] = TIER2 * ws["1"]
    ws["18"] = min(ws["16"], ws["17"])
    ws["6b"] = ws["18"]
    return ws


def aggregate(docs):
    """1099-R aggregation to 1040 lines 4a/4b (IRA) and 5a/5b (pension) + 25b."""
    out = {"4a": Decimal("0"), "4b": Decimal("0"),
           "5a": Decimal("0"), "5b": Decimal("0"), "25b": Decimal("0")}
    for d in docs:
        box1 = D(d.get("box1", 0))
        box2a = D(d.get("box2a", 0))
        roll = D(d.get("rollover", 0))
        qcd = D(d.get("qcd", 0))
        out["25b"] += D(d.get("box4", 0))
        if d.get("ira", False):
            out["4a"] += box1
            out["4b"] += max(Decimal("0"), box2a - roll - qcd)
        else:
            out["5a"] += box1
            out["5b"] += max(Decimal("0"), box2a - roll)
    return out


def early_from_docs(docs):
    """5329 line 1 source: taxable amount of early-code (1/J/S) docs, net of
    rollover; plus whether any SIMPLE-first-2-years (code S) is present (25%)."""
    total = Decimal("0")
    simple = False
    for d in docs:
        code = str(d.get("code", ""))
        if any(c in EARLY_CODES for c in code):
            total += max(Decimal("0"), D(d.get("box2a", 0)) - D(d.get("rollover", 0)))
        if "S" in code:
            simple = True
    return total, simple


def f5329_part1(line1, line2=0, simple=False):
    l3 = max(Decimal("0"), D(line1) - D(line2))
    rate = Decimal("0.25") if simple else Decimal("0.10")
    return {"3": l3, "4": rate * l3}


def f5329_generated(line2, docs):
    """R-5329-03 generation gate: exception claimed OR any J/S code OR >1 doc."""
    any_js = any(("J" in str(d.get("code", "")) or "S" in str(d.get("code", "")))
                 for d in docs)
    return (D(line2) > 0) or any_js or (len(docs) > 1)


def _opt(i, key):
    """Nullable account-value fact: absent -> None (no smaller-of cap)."""
    v = i.get(key)
    return None if v is None else D(v)


def _excess_part(prior, addends, curr, value):
    """Parts III-VIII excess-contribution chain. Returns (add, rem, total, tax).
    rem = max(0, prior - Σaddends); total = rem + curr; tax = 6% of min(total, value)
    (value None => no cap, tax on the full total — the conservative default)."""
    add = sum((D(a) for a in addends), Decimal("0"))
    rem = max(Decimal("0"), D(prior) - add)
    total = rem + D(curr)
    cap = total if value is None else min(total, value)
    return add, rem, total, Decimal("0.06") * cap


def f5329_full(i):
    """Recompute every computed line of the FULL Form 5329 (Parts I-IX) +
    schedule_2_line_8 (the all-parts sum, R-5329-12) from the direct facts."""
    o = {}
    # Part I
    l1 = D(i.get("f5329_line1_early_in_income", 0))
    l2 = D(i.get("f5329_line2_exception_amount", 0))
    o["3"] = max(Decimal("0"), l1 - l2)
    o["4"] = (Decimal("0.25") if i.get("f5329_simple_25pct") else Decimal("0.10")) * o["3"]
    # Part II
    o["7"] = max(Decimal("0"), D(i.get("f5329_line5_edu_able_dist", 0)) - D(i.get("f5329_line6_edu_able_not_subject", 0)))
    o["8"] = Decimal("0.10") * o["7"]
    # Part III (3 addends: L10/L11/L12)
    a, r, t, tax = _excess_part(i.get("f5329_line9_tira_prior_excess", 0),
                                [i.get("f5329_line10_tira_absorb", 0), i.get("f5329_line11_tira_dist", 0),
                                 i.get("f5329_line12_tira_prior_excess_dist", 0)],
                                i.get("f5329_line15_tira_curr_excess", 0), _opt(i, "f5329_tira_value"))
    o["13"], o["14"], o["16"], o["17"] = a, r, t, tax
    # Part IV
    a, r, t, tax = _excess_part(i.get("f5329_line18_roth_prior_excess", 0),
                                [i.get("f5329_line19_roth_absorb", 0), i.get("f5329_line20_roth_dist", 0)],
                                i.get("f5329_line23_roth_curr_excess", 0), _opt(i, "f5329_roth_value"))
    o["21"], o["22"], o["24"], o["25"] = a, r, t, tax
    # Part V
    a, r, t, tax = _excess_part(i.get("f5329_line26_coverdell_prior_excess", 0),
                                [i.get("f5329_line27_coverdell_absorb", 0), i.get("f5329_line28_coverdell_dist", 0)],
                                i.get("f5329_line31_coverdell_curr_excess", 0), _opt(i, "f5329_coverdell_value"))
    o["29"], o["30"], o["32"], o["33"] = a, r, t, tax
    # Part VI
    a, r, t, tax = _excess_part(i.get("f5329_line34_msa_prior_excess", 0),
                                [i.get("f5329_line35_msa_absorb", 0), i.get("f5329_line36_msa_dist", 0)],
                                i.get("f5329_line39_msa_curr_excess", 0), _opt(i, "f5329_msa_value"))
    o["37"], o["38"], o["40"], o["41"] = a, r, t, tax
    # Part VII
    a, r, t, tax = _excess_part(i.get("f5329_line42_hsa_prior_excess", 0),
                                [i.get("f5329_line43_hsa_absorb", 0), i.get("f5329_line44_hsa_dist", 0)],
                                i.get("f5329_line47_hsa_curr_excess", 0), _opt(i, "f5329_hsa_value"))
    o["45"], o["46"], o["48"], o["49"] = a, r, t, tax
    # Part VIII (no chain)
    able_curr = D(i.get("f5329_line50_able_curr_excess", 0))
    able_val = _opt(i, "f5329_able_value")
    o["51"] = Decimal("0.06") * (able_curr if able_val is None else min(able_curr, able_val))
    # Part IX (SECURE 2.0 10%/25%)
    o["54a"] = Decimal("0.10") * max(Decimal("0"), D(i.get("f5329_line52a_rmd_window", 0)) - D(i.get("f5329_line53a_dist_window", 0)))
    o["54b"] = Decimal("0.25") * max(Decimal("0"), D(i.get("f5329_line52b_rmd_other", 0)) - D(i.get("f5329_line53b_dist_other", 0)))
    o["55"] = o["54a"] + o["54b"]
    # Aggregate -> Schedule 2 line 8 (R-5329-12)
    o["schedule_2_line_8"] = o["4"] + o["8"] + o["17"] + o["25"] + o["33"] + o["41"] + o["49"] + o["51"] + o["55"]
    return o


# ── Lump-Sum Election (Pub 915 Worksheets 2 + 4) — independent transcription ──
# Carries its OWN copy of the worksheet logic + the §86 thresholds so a loader
# transcription error can't also pass the checker (the bridge-gate discipline).

def _ss_tiers(L1, L8, mfj, mfs_with_spouse):
    """Shared 50%/85% tier block used by SS WS1/WS2/WS4 (lines 2 + 9-19 of the
    Pub 915 worksheets). Given L1 (benefits for the calc) and L8 (provisional
    excess over adjustments), returns the 'smaller of L17 or L18' result."""
    L2 = TIER1 * D(L1)
    base = Decimal("32000") if mfj else Decimal("25000")
    tier = Decimal("12000") if mfj else Decimal("9000")
    if mfs_with_spouse:
        L17 = TIER2 * max(Decimal("0"), D(L8))
        L18 = TIER2 * D(L1)
        return min(L17, L18)
    if D(L8) <= base:
        return Decimal("0")
    L10 = D(L8) - base
    L12 = max(Decimal("0"), L10 - tier)
    L13 = min(L10, tier)
    L14 = TIER1 * L13
    L15 = min(L2, L14)
    L16 = TIER2 * L12
    L17 = L15 + L16
    L18 = TIER2 * D(L1)
    return min(L17, L18)


def ws2_additional(row):
    """Pub 915 Worksheet 2: additional taxable benefits for one earlier year."""
    L1 = D(row.get("earlier_net_benefits", 0)) + D(row.get("lump_for_year", 0))
    if L1 <= 0:
        return Decimal("0")
    L6 = (TIER1 * L1) + D(row.get("agi", 0)) + D(row.get("adjustments", 0)) + D(row.get("taxexempt", 0))
    prior = D(row.get("prior_taxable_ss", 0))
    L8 = L6 - prior
    mfj = bool(row.get("mfj", False))
    mfs = bool(row.get("mfs_with_spouse", False))
    # Worksheet 2 line 10 "No" (L8 <= base, non-MFS path) -> line 21 = 0 directly.
    base = Decimal("32000") if mfj else Decimal("25000")
    if not mfs and L8 <= base:
        return Decimal("0")
    L19 = _ss_tiers(L1, L8, mfj, mfs)
    return max(Decimal("0"), L19 - prior)


def ws1_line19(box5, ws1_other_income, ws1_taxexempt, ws1_adjustments, filing_status, mfs_with_spouse):
    """Pub 915 Worksheet 1 line 19 (= the regular taxable SS). Reuses ss_worksheet."""
    return ss_worksheet(box5, ws1_other_income, filing_status,
                        mfs_with_spouse=mfs_with_spouse, ws4_taxexempt=ws1_taxexempt,
                        ws6_adjustments=ws1_adjustments)["6b"]


def ws4_lse(inp):
    """Pub 915 Worksheet 4: taxable benefits under the lump-sum election method.
    Returns {'19': WS4 L19, '21': WS4 L21 (the election total)}."""
    lump_total = sum((D(r.get("lump_for_year", 0)) for r in inp["earlier_years"]), Decimal("0"))
    mfj = inp["filing_status"] == "mfj"
    mfs = bool(inp.get("mfs_lived_with_spouse", False))
    L1 = D(inp["ssa_box5_2025"]) - lump_total
    if L1 <= 0:
        L19 = Decimal("0")
    else:
        # WS4 L6 = 0.5*L1 + WS1.L3(income) + WS1.L4(2a) + WS1.L5(excl=0); L8 = L6 - WS1.L7(adj).
        L6 = (TIER1 * L1) + D(inp.get("ws1_other_income", 0)) + D(inp.get("ws1_taxexempt", 0))
        L8 = L6 - D(inp.get("ws1_adjustments", 0))
        L19 = _ss_tiers(L1, L8, mfj, mfs)
    add_total = sum((ws2_additional(r) for r in inp["earlier_years"]), Decimal("0"))
    return {"19": L19, "21": L19 + add_total}


# ═══════════════════════════════════════════════════════════════════════════
# Structural checks (mirror check_intdiv_integrity.py)
# ═══════════════════════════════════════════════════════════════════════════

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

    linked = {rid for rid, *_ in spec["rule_links"]}
    uncited = [rid for rid in rule_ids if rid not in linked]
    if uncited:
        err(f"{fn}: uncited rules {uncited}")
    dangling = [rid for rid in linked if rid not in rule_ids]
    if dangling:
        err(f"{fn}: rule_links reference unknown rules {dangling}")

    for ln in spec["lines"]:
        for rid in ln.get("source_rules", []):
            if rid not in rule_ids:
                err(f"{fn} line {ln['line_number']}: unknown source_rule {rid}")

    for r in spec["rules"]:
        for key in r.get("inputs", []):
            if key not in fact_keys:
                err(f"{fn} {r['rule_id']}: input '{key}' is not a declared fact")

    for f in spec["facts"]:
        if f["data_type"] == "choice" and not f.get("choices"):
            err(f"{fn} fact {f['fact_key']}: choice type without choices")

# ── flow assertions ──
fa_ids = [a["assertion_id"] for a in m.FLOW_ASSERTIONS]
if len(fa_ids) != len(set(fa_ids)):
    err("duplicate flow assertion ids")
for a in m.FLOW_ASSERTIONS:
    if len(a["assertion_id"]) > 20:
        err(f"assertion_id too long (>20): {a['assertion_id']}")


# ═══════════════════════════════════════════════════════════════════════════
# Scenario lookup (key on the first token of scenario_name)
# ═══════════════════════════════════════════════════════════════════════════

s = {sc["scenario_name"].split(" ")[0]: sc for spec in m.FORMS for sc in spec["scenarios"]}


def ss_recompute(sc):
    i = sc["inputs"]
    return ss_worksheet(
        i["ssa_box5"], i["other_ws3_income"], i["filing_status"],
        mfs_with_spouse=i.get("mfs_lived_with_spouse", False),
    )


def check_ss(key):
    sc = s[key]
    ws = ss_recompute(sc)
    for out_key, want in sc["expected_outputs"].items():
        if out_key.startswith("ws_"):
            line = out_key.removeprefix("ws_")
            if line not in ws:
                err(f"{key} {out_key}: worksheet line {line} not reached (recompute STOPped early)")
            else:
                check(f"{key} {out_key}", ws[line], want)
        elif out_key == "1040_line_6a":
            check(f"{key} 6a", ws["6a"], want)
        elif out_key == "1040_line_6b":
            check(f"{key} 6b", ws["6b"], want)
    # invariant FA-1040-RET-05: 6b <= 85% of net benefits, and 6b <= WS1
    if D(ws["6b"]) > TIER2 * D(ws["1"]):
        err(f"{key}: 6b exceeds 85% of WS1 (cap violated)")
    if D(ws["6b"]) > D(ws["1"]):
        err(f"{key}: 6b exceeds WS1 (net benefits)")


# ── Social Security worksheet scenarios ──
for key in ("SS-1", "SS-2", "SS-3", "SS-4", "SS-5"):
    check_ss(key)

# ── 1099-R aggregation scenarios ──
for key in ("RET-T1", "RET-T2", "RET-T3", "RET-T4", "RET-T5"):
    sc = s[key]
    out = aggregate(sc["inputs"]["r_docs"])
    for line in ("4a", "4b", "5a", "5b", "25b"):
        ek = f"1040_line_{line}"
        if ek in sc["expected_outputs"]:
            check(f"{key} {line}", out[line], sc["expected_outputs"][ek])
    # literal flags must be consistent with a nonzero rollover/qcd in the docs
    eo = sc["expected_outputs"]
    if eo.get("rollover_literal") and not any(D(d.get("rollover", 0)) > 0 for d in sc["inputs"]["r_docs"]):
        err(f"{key}: rollover_literal asserted but no doc has a rollover amount")
    if eo.get("qcd_literal") and not any(D(d.get("qcd", 0)) > 0 for d in sc["inputs"]["r_docs"]):
        err(f"{key}: qcd_literal asserted but no doc has a QCD amount")

# ── Form 5329 early-distribution scenarios (doc-driven) ──
for key in ("RET-5329-1", "RET-5329-2", "RET-5329-3"):
    sc = s[key]
    i = sc["inputs"]
    eo = sc["expected_outputs"]
    line1, simple = early_from_docs(i["r_docs"])
    line2 = D(i.get("exception_amount_5329", 0))
    parts = f5329_part1(line1, line2, simple)
    if "5329_line_1" in eo:
        check(f"{key} L1", line1, eo["5329_line_1"])
    if "5329_line_2" in eo:
        check(f"{key} L2", line2, eo["5329_line_2"])
    if "5329_line_3" in eo:
        check(f"{key} L3", parts["3"], eo["5329_line_3"])
    if "5329_line_4" in eo:
        check(f"{key} L4", parts["4"], eo["5329_line_4"])
    if "schedule_2_line_8" in eo:
        check(f"{key} Sch2 L8", parts["4"], eo["schedule_2_line_8"])
    if "form_5329_generated" in eo:
        got = f5329_generated(line2, i["r_docs"])
        if got != eo["form_5329_generated"]:
            err(f"{key}: form_5329_generated recomputed {got} != authored {eo['form_5329_generated']}")
    if "D_RET_007_fires" in eo and eo["D_RET_007_fires"] != simple:
        err(f"{key}: D_RET_007 (SIMPLE 25%) expected {eo['D_RET_007_fires']} but recompute simple={simple}")

# ── Form 5329 direct-fact scenarios (FULL FORM, Parts I-IX) ──
for key in ("F5329-T1", "F5329-T2", "F5329-T3", "F5329-T4", "F5329-T5",
            "F5329-T6", "F5329-T7", "F5329-T8", "F5329-T9", "F5329-T10"):
    sc = s[key]
    o = f5329_full(sc["inputs"])
    for out_key, want in sc["expected_outputs"].items():
        if out_key not in o:
            err(f"{key}: expected output '{out_key}' is not a recomputed line")
        else:
            check(f"{key} L{out_key}", o[out_key], want)

# ── Lump-Sum Election scenarios (LSE-1 Terry worked example, LSE-2 not-beneficial) ──
for key in ("LSE-1", "LSE-2"):
    sc = s[key]
    i = sc["inputs"]
    eo = sc["expected_outputs"]
    fs = i["filing_status"]
    mfs = i.get("mfs_lived_with_spouse", False)
    w1 = ws1_line19(i["ssa_box5_2025"], i["ws1_other_income"], i["ws1_taxexempt"],
                    i["ws1_adjustments"], fs, mfs)
    w4 = ws4_lse(i)
    if "ws1_line19" in eo:
        check(f"{key} WS1 L19", w1, eo["ws1_line19"])
    if "ws2_21" in eo:
        got = [ws2_additional(r) for r in i["earlier_years"]]
        for n, (g, w) in enumerate(zip(got, eo["ws2_21"])):
            check(f"{key} WS2[{n}] L21", g, w)
    if "ws4_line19" in eo:
        check(f"{key} WS4 L19", w4["19"], eo["ws4_line19"])
    if "ws4_line21" in eo:
        check(f"{key} WS4 L21", w4["21"], eo["ws4_line21"])
    beneficial = D(w4["21"]) < D(w1)
    if "beneficial" in eo and beneficial != eo["beneficial"]:
        err(f"{key}: beneficial recomputed {beneficial} != authored {eo['beneficial']}")
    # elected 6b = WS4 L21 when the toggle is on, else the regular WS1 L19.
    elected_6b = w4["21"] if i.get("election") else w1
    if "elected_6b" in eo:
        check(f"{key} elected 6b", elected_6b, eo["elected_6b"])

# Load-bearing: the election BENEFIT must be real (LSE-1 lower, LSE-2 higher).
_l1 = s["LSE-1"]["inputs"]
if not (D(ws4_lse(_l1)["21"]) < D(ws1_line19(_l1["ssa_box5_2025"], _l1["ws1_other_income"],
        _l1["ws1_taxexempt"], _l1["ws1_adjustments"], _l1["filing_status"], False))):
    err("LSE-1: WS4 not lower than WS1 — the election benefit is not load-bearing")
_l2 = s["LSE-2"]["inputs"]
if not (D(ws4_lse(_l2)["21"]) > D(ws1_line19(_l2["ssa_box5_2025"], _l2["ws1_other_income"],
        _l2["ws1_taxexempt"], _l2["ws1_adjustments"], _l2["filing_status"], False))):
    err("LSE-2: WS4 not higher than WS1 — the not-beneficial branch is not load-bearing")

# ── RED-gate fixtures actually trigger their condition ──
g1 = s["RET-G1"]["inputs"]["r_docs"][0]
if not ((g1.get("box2a") is None or g1.get("box2b_not_determined"))
        and (D(g1.get("box5", 0)) > 0 or D(g1.get("box9b", 0)) > 0)):
    err("RET-G1: fixture does not satisfy D_RET_001 (box-2a-blank + basis)")

g2 = s["RET-G2"]["inputs"]["r_docs"][0]
if not D(g2.get("box6", 0)) > 0:
    err("RET-G2: fixture has no NUA (box 6) to fire D_RET_002")

g3 = s["RET-G3"]["inputs"]["r_docs"][0]
if all(c in SUPPORTED_CODES for c in str(g3.get("code", ""))):
    err("RET-G3: fixture code is fully supported — D_RET_003 would not fire")

if not s["RET-G4"]["inputs"].get("ssa_lump_sum_prior_year"):
    err("RET-G4: fixture does not set ssa_lump_sum_prior_year for D_RET_004")

g5_exc = str(s["RET-G5"]["inputs"].get("exception_number_5329", ""))
if g5_exc in SUPPORTED_EXCEPTIONS:
    err(f"RET-G5: exception {g5_exc} is in the supported set — D_RET_006 would not fire")


# ═══════════════════════════════════════════════════════════════════════════
# Load-bearing checks (the pins must actually be able to catch a regression)
# ═══════════════════════════════════════════════════════════════════════════

# 1. The 85% cap (WS17) is binding in SS-3 — WS16 > WS17, so min() matters.
ws3 = ss_worksheet(20000, 40000, "single")
if not (ws3["16"] > ws3["17"]):
    err("SS-3: WS16 <= WS17 — the 85% cap pin is not load-bearing here")

# 2. The MFS-lived-with-spouse branch differs from the normal path.
mfs_branch = ss_worksheet(10000, 5000, "mfs", mfs_with_spouse=True)["6b"]
mfs_normal = ss_worksheet(10000, 5000, "mfs", mfs_with_spouse=False)["6b"]
if mfs_branch == mfs_normal:
    err("SS-5: the MFS-with-spouse branch produces the same 6b as the normal path — branch not load-bearing")

# 3. The SIMPLE 25% rate differs from the 10% rate.
if f5329_part1(10000, 0, simple=True)["4"] == f5329_part1(10000, 0, simple=False)["4"]:
    err("RET-5329-3: 25% and 10% produce the same line 4 — the SIMPLE-rate pin is dead")

# 3b. The smaller-of cap is load-bearing: same excess, capped (value < excess) vs
#     uncapped (value None) must produce DIFFERENT line-17 tax.
_capped = f5329_full({"f5329_line15_tira_curr_excess": 2000, "f5329_tira_value": 1500})["17"]
_uncapped = f5329_full({"f5329_line15_tira_curr_excess": 2000})["17"]
if _capped == _uncapped:
    err("F5329 Part III: the 12/31 smaller-of cap is not load-bearing (capped == uncapped)")

# 3c. The Part IX SECURE 2.0 split is load-bearing: the 10% (window) and 25% (other)
#     buckets must differ on the same shortfall.
_pix = f5329_full({"f5329_line52a_rmd_window": 4000, "f5329_line52b_rmd_other": 4000})
if _pix["54a"] == _pix["54b"]:
    err("F5329 Part IX: the 10%/25% correction-window split is not load-bearing")

# 4. The FA-1040-RET-06 constants_check matches this checker's independent values.
fa06 = next((a for a in m.FLOW_ASSERTIONS if a["assertion_id"] == "FA-1040-RET-06"), None)
if fa06:
    c = fa06["definition"]["constants"]
    for status, amt in SS_BASE.items():
        # the FA uses 'mfs_apart' for the $25,000 MFS row
        fa_key = "mfs_apart" if status == "mfs" else status
        if c["base_amount"].get(fa_key) != amt:
            err(f"FA-06 base_amount[{fa_key}]={c['base_amount'].get(fa_key)} != independent {amt}")
        if c["second_tier"].get(fa_key) != SS_SECOND[status]:
            err(f"FA-06 second_tier[{fa_key}]={c['second_tier'].get(fa_key)} != independent {SS_SECOND[status]}")
    if c["rates"].get("tier1") != float(TIER1) or c["rates"].get("tier2") != float(TIER2):
        err(f"FA-06 rates {c['rates']} != independent {{tier1:{TIER1}, tier2:{TIER2}}}")
    if c.get("applies_to_years") != [2025, 2026]:
        err(f"FA-06 applies_to_years {c.get('applies_to_years')} != [2025, 2026] (statutory non-indexed)")
else:
    err("FA-1040-RET-06 (constants_check) not found")

# 5. Every supported distribution code in the docstring set is single-char and
#    the early set is a subset of supported (1, S supported; J is NOT in v1).
if not EARLY_CODES.issubset(SUPPORTED_CODES | {"J"}):
    err("EARLY_CODES contains a code outside supported∪{J}")
if "J" in SUPPORTED_CODES:
    err("J should NOT be in the v1 supported set (Ken-confirmed set excludes J)")


# ═══════════════════════════════════════════════════════════════════════════
# Report
# ═══════════════════════════════════════════════════════════════════════════

counts = {spec["identity"]["form_number"]: (len(spec["facts"]), len(spec["rules"]),
          len(spec["lines"]), len(spec["diagnostics"]), len(spec["scenarios"]),
          len(spec["rule_links"])) for spec in m.FORMS}

print("Per-form counts (facts/rules/lines/diagnostics/scenarios/links):")
for fn, c in counts.items():
    print(f"  {fn}: {c}")
print(f"Flow assertions: {len(m.FLOW_ASSERTIONS)}")
print(f"Authority sources (new): {len(m.AUTHORITY_SOURCES)}; topics: {len(m.AUTHORITY_TOPICS)}; "
      f"new excerpts on existing: {len(m.NEW_EXCERPTS_ON_EXISTING)}")
print("Independently recomputed: SS-1..5 (18-line worksheet), RET-T1..5 (aggregation), "
      "RET-5329-1..3 (doc-driven Part I) + F5329-T1..10 (FULL Form 5329 Parts I-IX: II edu/ABLE, "
      "III-VIII excess 6% w/ smaller-of cap, IX SECURE 2.0 10%/25%, all-parts Sch 2 L8 sum), "
      "RET-G1..5 (RED-gate fixtures).")

if errors:
    print("\nFAILURES:")
    for e in errors:
        print(f"  X {e}")
    sys.exit(1)
print("\nALL CHECKS PASS")
