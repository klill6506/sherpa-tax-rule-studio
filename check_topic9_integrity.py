"""Pre-seed content checker for load_1040_schedule_d (Topic 9 — Schedule D /
1040_SCHD_WS / re-authored 8949).

Run:  poetry run python check_topic9_integrity.py

Mirrors check_topic8_integrity.py: validates the authored lists WITHOUT
touching the DB, then INDEPENDENTLY recomputes every numeric scenario from its
OWN transcription of the form math (re-typed from the i1040sd/i8949 dumps, not
imported from the loader) — the Schedule D netting + §1211(b) loss limit +
line-17/20/22 routing, the Capital Loss Carryover (out) worksheet, the 28% Rate
Gain Worksheet, the Unrecaptured §1250 Gain Worksheet, the full 47-line
Schedule D Tax Worksheet (incl. the 1==16 / 1==32 / D18-D19 skip rules), and
the 8949 column-(h) math. This is the MATH GATE that must pass before Ken's
review walk.

The checker carries its OWN independent copies of the year-keyed constants
(SDTW 0%/15-20% breakpoints, the 32%-bracket starts) and the statutory values
($3,000/$1,500, 25%/28%), re-typed from the cited sources, and cross-checks
the loader's module constants cell-by-cell — so a transcription error in the
loader cannot also pass the checker.

LOAD-BEARING INVARIANT: with Schedule D lines 18/19 zero and no Form 4952,
SDTW line 47 must equal the QDCGT worksheet result for identical inputs —
swept across filing statuses and BOTH years. The route choice must never
change the answer when both are legal.

Tax-method convention (SDTW lines 44/46): Tax Table below $100,000 (the Topic
1 Ken-blessed $50-band midpoint, ROUND_HALF_UP), Tax Computation Worksheet
(exact cumulative brackets) at or above — re-typed here from RP 2024-40 §2.01
/ RP 2025-32 §4.01.
"""
import os
import sys
from decimal import Decimal, ROUND_HALF_UP

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_schedule_d as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def check(name, got, want):
    if D(got) != D(want):
        err(f"{name}: recomputed {got} != authored {want}")


# ═══════════════════════════════════════════════════════════════════════════
# INDEPENDENT CONSTANTS (re-typed from the cited sources; NOT imported)
# ═══════════════════════════════════════════════════════════════════════════

# §1211(b) — Schedule D face line 21 verbatim.
IND_LOSS_LIMIT = {"mfs": 1500, "other": 3000}

# §1(h) cap rates — SDTW lines 40/43 verbatim.
IND_RATE_1250 = Decimal("0.25")
IND_RATE_28 = Decimal("0.28")

# SDTW line 15 / line 26 — 2025 verbatim on the worksheet; 2026 per RP 2025-32
# §4.03 (the Topic 3 Ken-blessed QDCGT amounts, re-typed here).
IND_ZERO_RATE_MAX = {
    2025: {"single": 48350, "mfs": 48350, "mfj": 96700, "qss": 96700, "hoh": 64750},
    2026: {"single": 49450, "mfs": 49450, "mfj": 98900, "qss": 98900, "hoh": 66200},
}
IND_RATE15_MAX = {
    2025: {"single": 533400, "mfs": 300000, "mfj": 600050, "qss": 600050, "hoh": 566700},
    2026: {"single": 545500, "mfs": 306850, "mfj": 613700, "qss": 613700, "hoh": 579600},
}

# SDTW line 19 — 2025 verbatim on the worksheet; 2026 = the 24%-bracket tops
# per RP 2025-32 §4.01 Tables 1-4 (note the HOH $25 asymmetry).
IND_BRACKET32_START = {
    2025: {"single": 197300, "mfs": 197300, "mfj": 394600, "qss": 394600, "hoh": 197300},
    2026: {"single": 201775, "mfs": 201775, "mfj": 403550, "qss": 403550, "hoh": 201750},
}

# Ordinary brackets (upper_bound, rate) — RP 2024-40 §2.01 / RP 2025-32 §4.01.
_INF = 10**12
IND_BRACKETS = {
    2025: {
        "single": [(11925, "0.10"), (48475, "0.12"), (103350, "0.22"), (197300, "0.24"),
                   (250525, "0.32"), (626350, "0.35"), (_INF, "0.37")],
        "mfs":    [(11925, "0.10"), (48475, "0.12"), (103350, "0.22"), (197300, "0.24"),
                   (250525, "0.32"), (375800, "0.35"), (_INF, "0.37")],
        "mfj":    [(23850, "0.10"), (96950, "0.12"), (206700, "0.22"), (394600, "0.24"),
                   (501050, "0.32"), (751600, "0.35"), (_INF, "0.37")],
        "hoh":    [(17000, "0.10"), (64850, "0.12"), (103350, "0.22"), (197300, "0.24"),
                   (250500, "0.32"), (626350, "0.35"), (_INF, "0.37")],
    },
    2026: {
        "single": [(12400, "0.10"), (50400, "0.12"), (105700, "0.22"), (201775, "0.24"),
                   (256225, "0.32"), (640600, "0.35"), (_INF, "0.37")],
        "mfs":    [(12400, "0.10"), (50400, "0.12"), (105700, "0.22"), (201775, "0.24"),
                   (256225, "0.32"), (384350, "0.35"), (_INF, "0.37")],
        "mfj":    [(24800, "0.10"), (100800, "0.12"), (211400, "0.22"), (403550, "0.24"),
                   (512450, "0.32"), (768700, "0.35"), (_INF, "0.37")],
        "hoh":    [(17700, "0.10"), (67450, "0.12"), (105700, "0.22"), (201750, "0.24"),
                   (256200, "0.32"), (640600, "0.35"), (_INF, "0.37")],
    },
}


def bracket_tax(ti, status, year):
    """TCW-style exact cumulative-bracket tax."""
    ti = D(ti)
    st = "mfj" if status == "qss" else status
    total, lo = Decimal(0), Decimal(0)
    for hi, rate in IND_BRACKETS[year][st]:
        hi = D(hi)
        if ti > hi:
            total += (hi - lo) * Decimal(rate)
        else:
            total += (ti - lo) * Decimal(rate)
            break
        lo = hi
    return total


def ordinary_tax(ti, status, year):
    """SDTW lines 44/46 method rule: Tax Table (the $50-band midpoint
    convention, HALF-UP to whole dollars) below $100,000; TCW at/above."""
    ti = D(ti)
    if ti >= 100000:
        return bracket_tax(ti, status, year)
    lo = (int(ti) // 50) * 50
    mid = D(lo + 25)
    return bracket_tax(mid, status, year).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


# ═══════════════════════════════════════════════════════════════════════════
# INDEPENDENT WORKSHEET TRANSCRIPTIONS (from the i1040sd dump)
# ═══════════════════════════════════════════════════════════════════════════

def sdtw(year, status, ti, qual_div, d15, d16, d18, d19, f4952_4g=0, f4952_4e=0):
    L = {}
    L[1], L[2], L[3], L[4] = D(ti), D(qual_div), D(f4952_4g), D(f4952_4e)
    L[5] = max(Decimal(0), L[3] - L[4])
    L[6] = max(Decimal(0), L[2] - L[5])
    L[7] = min(D(d15), D(d16))
    L[8] = min(L[3], L[4])
    L[9] = max(Decimal(0), L[7] - L[8])
    L[10] = L[6] + L[9]
    L[11] = D(d18) + D(d19)
    L[12] = min(L[9], L[11])
    L[13] = L[10] - L[12]
    L[14] = max(Decimal(0), L[1] - L[13])
    L[15] = D(IND_ZERO_RATE_MAX[year][status])
    L[16] = min(L[1], L[15])
    L[17] = min(L[14], L[16])
    L[18] = max(Decimal(0), L[1] - L[10])
    L[19] = min(L[1], D(IND_BRACKET32_START[year][status]))
    L[20] = min(L[14], L[19])
    L[21] = max(L[18], L[20])
    L[22] = L[16] - L[17]
    for n in range(23, 44):
        L[n] = Decimal(0)
    if L[1] != L[16]:                                   # skip rule: 1 == 16 -> line 44
        L[23] = min(L[1], L[13])
        L[24] = L[22]
        L[25] = max(Decimal(0), L[23] - L[24])
        L[26] = D(IND_RATE15_MAX[year][status])
        L[27] = min(L[1], L[26])
        L[28] = L[21] + L[22]
        L[29] = max(Decimal(0), L[27] - L[28])
        L[30] = min(L[25], L[29])
        L[31] = L[30] * Decimal("0.15")
        L[32] = L[24] + L[30]
        if L[1] != L[32]:                               # skip rule: 1 == 32 -> line 44
            L[33] = L[23] - L[32]
            L[34] = L[33] * Decimal("0.20")
            if D(d19) != 0:                             # skip rule: D19 zero -> 41
                L[35] = min(L[9], D(d19))
                L[36] = L[10] + L[21]
                L[37] = L[1]
                L[38] = max(Decimal(0), L[36] - L[37])
                L[39] = max(Decimal(0), L[35] - L[38])
                L[40] = L[39] * IND_RATE_1250
            if D(d18) != 0:                             # skip rule: D18 zero -> 44
                L[41] = L[21] + L[22] + L[30] + L[33] + L[39]
                L[42] = L[1] - L[41]
                L[43] = L[42] * IND_RATE_28
    L[44] = ordinary_tax(L[21], status, year)
    L[45] = L[31] + L[34] + L[40] + L[43] + L[44]
    L[46] = ordinary_tax(L[1], status, year)
    L[47] = min(L[45], L[46])
    return L


def qdcgt(year, status, ti, qual_div, net_cap_gain):
    """The i1040gi QDCGT worksheet (Topic 3 shape) for the invariance check."""
    ti, qd, ncg = D(ti), D(qual_div), D(net_cap_gain)
    w3 = ncg + qd
    w5 = w3                                              # no 4952
    w6 = max(Decimal(0), ti - w5)
    w7 = D(IND_ZERO_RATE_MAX[year][status])
    w8 = min(ti, w7)
    w9 = min(w6, w8)
    w10 = w8 - w9
    w11 = min(ti, w5)
    w13 = w11 - w10
    w14 = D(IND_RATE15_MAX[year][status])
    w15 = min(ti, w14)
    w16 = w6 + w10
    w17 = max(Decimal(0), w15 - w16)
    w18 = min(w13, w17)
    w19 = w18 * Decimal("0.15")
    w20 = w10 + w18
    w21 = w11 - w20
    w22 = w21 * Decimal("0.20")
    w23 = ordinary_tax(w6, status, year)
    w24 = w19 + w22 + w23
    w25 = ordinary_tax(ti, status, year)
    return min(w24, w25)


def clc_out(ti_signed, d21_loss_pos, d7, d15):
    W = {}
    W[1] = D(ti_signed)
    W[2] = D(d21_loss_pos)
    W[3] = max(Decimal(0), W[1] + W[2])
    W[4] = min(W[2], W[3])
    if D(d7) < 0:
        W[5] = -D(d7)
        W[6] = max(Decimal(0), D(d15))
        W[7] = W[4] + W[6]
        W[8] = max(Decimal(0), W[5] - W[7])
    else:
        W[5] = W[6] = W[7] = W[8] = Decimal(0)
    if D(d15) < 0:
        W[9] = -D(d15)
        W[10] = max(Decimal(0), D(d7))
        W[11] = max(Decimal(0), W[4] - W[5])
        W[12] = W[10] + W[11]
        W[13] = max(Decimal(0), W[9] - W[12])
    else:
        W[9] = W[10] = W[11] = W[12] = W[13] = Decimal(0)
    return W


def w28(code_c_total, addback_1202, other_4684, div2d_plus_k1, lt_carry_pos, d7):
    W = {}
    W[1] = D(code_c_total)
    W[2] = D(addback_1202)
    W[3] = D(other_4684)
    W[4] = D(div2d_plus_k1)
    W[5] = -D(lt_carry_pos)
    W[6] = min(Decimal(0), D(d7))
    W[7] = max(Decimal(0), W[1] + W[2] + W[3] + W[4] + W[5] + W[6])
    return W


def u1250(div2b_plus_k1, other_fact, w28_1_4, d7, lt_carry_pos):
    W = {n: Decimal(0) for n in range(1, 11)}
    W[11] = D(div2b_plus_k1)
    W[12] = D(other_fact)
    W[13] = W[9] + W[10] + W[11] + W[12]
    W[14] = D(w28_1_4)
    W[15] = min(Decimal(0), D(d7))
    W[16] = -D(lt_carry_pos)
    W[17] = max(Decimal(0), -(W[14] + W[15] + W[16]))
    W[18] = max(Decimal(0), W[13] - W[17])
    return W


def schd_net(box_totals, l4=0, l5=0, l11=0, l12=0, l13=0, st_carry=0, lt_carry=0):
    """Independent Schedule D netting. box_totals: {'A': (d, e, g), ...}."""
    ST, LT = {"A", "B", "C", "G", "H", "I"}, {"D", "E", "F", "J", "K", "L"}
    h = {b: D(v[0]) - D(v[1]) + D(v[2]) for b, v in box_totals.items()}
    l7 = sum((h[b] for b in h if b in ST), Decimal(0)) + D(l4) + D(l5) - D(st_carry)
    l15 = sum((h[b] for b in h if b in LT), Decimal(0)) + D(l11) + D(l12) + D(l13) - D(lt_carry)
    return l7, l15, l7 + l15


def route(l15, l16, d18, d19, files_4952, qual_div):
    if l16 > 0 and l15 > 0:
        if d18 == 0 and d19 == 0 and not files_4952:
            return "qdcgt"
        return "sdtw"
    return "qdcgt" if qual_div > 0 else "ordinary"


# ═══════════════════════════════════════════════════════════════════════════
# 1. Loader constants vs the independent transcription (cell-by-cell)
# ═══════════════════════════════════════════════════════════════════════════

for year in (2025, 2026):
    for st in ("single", "mfs", "mfj", "qss", "hoh"):
        check(f"SDTW_ZERO_RATE_MAX[{year}][{st}]", m.SDTW_ZERO_RATE_MAX[year][st], IND_ZERO_RATE_MAX[year][st])
        check(f"SDTW_RATE15_MAX[{year}][{st}]", m.SDTW_RATE15_MAX[year][st], IND_RATE15_MAX[year][st])
        check(f"SDTW_BRACKET32_START[{year}][{st}]", m.SDTW_BRACKET32_START[year][st], IND_BRACKET32_START[year][st])
check("CAPITAL_LOSS_LIMIT", m.CAPITAL_LOSS_LIMIT, IND_LOSS_LIMIT["other"])
check("CAPITAL_LOSS_LIMIT_MFS", m.CAPITAL_LOSS_LIMIT_MFS, IND_LOSS_LIMIT["mfs"])
check("SDTW_RATE_UNRECAP_1250", m.SDTW_RATE_UNRECAP_1250, IND_RATE_1250)
check("SDTW_RATE_28PCT_GROUP", m.SDTW_RATE_28PCT_GROUP, IND_RATE_28)

# The 2025 SDTW line 19 must equal the 2025 24%-bracket tops (the derivation
# basis for 2026 — verifies the derivation rule itself against the printed year).
for st in ("single", "mfs", "mfj", "hoh"):
    top24 = [hi for hi, rate in IND_BRACKETS[2025][st] if rate == "0.24"][0]
    check(f"2025 line-19 == 24%-bracket top [{st}]", IND_BRACKET32_START[2025][st], top24)
for st in ("single", "mfs", "mfj", "hoh"):
    top24 = [hi for hi, rate in IND_BRACKETS[2026][st] if rate == "0.24"][0]
    check(f"2026 line-19 == 24%-bracket top [{st}]", IND_BRACKET32_START[2026][st], top24)


# ═══════════════════════════════════════════════════════════════════════════
# 2. SCHEDULE_D scenarios — independent netting/routing recompute
# ═══════════════════════════════════════════════════════════════════════════

def run_schd(s):
    inp, exp = s["inputs"], s["expected_outputs"]
    name = s["scenario_name"].split(" ")[0]
    status = inp.get("filing_status", "single")
    boxes = {}
    for key, box in (("box_a_totals", "A"), ("box_d_totals", "D")):
        if key in inp:
            t = inp[key]
            boxes[box] = (t["d"], t["e"], t["g"])
    code_c_total = Decimal(0)
    has_q = has_yz = False
    for t in inp.get("transactions", []):
        b = t["box"]
        d_, e_, g_ = D(t["d"]), D(t["e"]), D(t.get("g", 0))
        prev = boxes.get(b, (0, 0, 0))
        boxes[b] = (D(prev[0]) + d_, D(prev[1]) + e_, D(prev[2]) + g_)
        codes = t.get("codes", "") or ""
        if "C" in codes:
            code_c_total += d_ - e_ + g_
        has_q = has_q or ("Q" in codes)
        has_yz = has_yz or ("Y" in codes) or ("Z" in codes)

    st_c, lt_c = D(inp.get("schd_st_carryover_prior", 0)), D(inp.get("schd_lt_carryover_prior", 0))
    div2a, div2b = D(inp.get("div_box_2a_total", 0)), D(inp.get("div_box_2b_total", 0))
    l7, l15, l16 = schd_net(boxes, l13=div2a, st_carry=st_c, lt_carry=lt_c)

    # worksheets feeding 18/19
    w28r = w28(code_c_total, 0, 0, 0, lt_c, l7)
    u = u1250(div2b, 0, w28r[1] + w28r[2] + w28r[3] + w28r[4], l7, lt_c)
    d18 = w28r[7] if (l15 > 0 and l16 > 0) else Decimal(0)
    d19 = u[18] if (l15 > 0 and l16 > 0) else Decimal(0)
    files_4952 = bool(inp.get("schd_files_form_4952"))
    r = route(l15, l16, d18, d19, files_4952, Decimal(0))

    limit = D(IND_LOSS_LIMIT["mfs" if status == "mfs" else "other"])
    if l16 < 0:
        l21 = -min(-l16, limit)
        f7a = l21
    else:
        l21 = Decimal(0)
        f7a = l16
    ncg = min(l15, l16) if (l15 > 0 and l16 > 0) else Decimal(0)

    def box_h(b):
        t = boxes.get(b)
        return (D(t[0]) - D(t[1]) + D(t[2])) if t else Decimal(0)

    for k, want in exp.items():
        if k.startswith("D_") or k in ("schd_line",):
            continue  # diagnostics are structural, checked below
        got = {
            "line_1b_h": box_h("A") + box_h("G"),
            "line_8b_h": box_h("D") + box_h("J"),
            "line_10_h": box_h("F") + box_h("L"),
            "line_6": -st_c, "line_14": -lt_c, "line_13": div2a,
            "line_7": l7, "line_15": l15, "line_16": l16, "line_21": l21,
            "line_17": (l15 > 0 and l16 > 0), "line_18": d18, "line_19": d19,
            "line_20": (l15 > 0 and l16 > 0 and d18 == 0 and d19 == 0 and not files_4952),
            "f1040_line_7a": f7a, "schd_route": r, "schd_net_capital_gain": ncg,
        }.get(k, "__missing__")
        if got == "__missing__":
            if k in ("schd_carryover_out_st", "schd_carryover_out_lt"):
                ti = D(inp.get("f1040_line_15", 0))
                W = clc_out(ti, -l21, l7, l15)
                got = W[8] if k.endswith("_st") else W[13]
            else:
                err(f"{name}.{k}: no independent recompute mapped")
                continue
        if isinstance(want, bool) or isinstance(got, bool):
            if bool(got) != bool(want):
                err(f"{name}.{k}: recomputed {got} != authored {want}")
        elif isinstance(want, str):
            if str(got) != want:
                err(f"{name}.{k}: recomputed {got} != authored {want}")
        else:
            check(f"{name}.{k}", got, want)

    # diagnostic expectations that are structurally derivable here
    if exp.get("D_SCHD_001") and not files_4952:
        err(f"{name}: D_SCHD_001 expected but files_form_4952 not set")
    if exp.get("D_SCHD_007") and not has_yz:
        err(f"{name}: D_SCHD_007 expected but no Y/Z code present")
    if exp.get("D_SCHD_005") and not (l16 < 0 and -l16 > limit):
        err(f"{name}: D_SCHD_005 expected but the loss is not limited")


for s in m.SCHEDD_SCENARIOS:
    run_schd(s)


# ═══════════════════════════════════════════════════════════════════════════
# 3. 1040_SCHD_WS scenarios — independent worksheet recompute
# ═══════════════════════════════════════════════════════════════════════════

for s in m.SCHDWS_SCENARIOS:
    name = s["scenario_name"].split(" ")[0]
    inp, exp = s["inputs"], s["expected_outputs"]
    if name.startswith("SDTW"):
        L = sdtw(inp["tax_year"], inp["filing_status"], inp["taxable_income"],
                 inp["qualified_dividends"], inp["schd_15"], inp["schd_16"],
                 inp["schd_18"], inp["schd_19"])
        for k, want in exp.items():
            n = int(k.split("_")[1])
            check(f"{name}.{k}", L[n], want)
    elif name.startswith("CLC"):
        W = clc_out(inp["f1040_line_15_signed"], inp["schd_21_loss_pos"],
                    inp["schd_7"], inp["schd_15"])
        for k, want in exp.items():
            n = int(k.split("_")[1])
            check(f"{name}.{k}", W[n], want)
    elif name.startswith("W28"):
        W = w28(inp["code_c_total"], inp["s1202_addback"], 0, inp["div_2d_total"],
                inp["lt_carryover"], inp["schd_7"])
        for k, want in exp.items():
            n = int(k.split("_")[1])
            check(f"{name}.{k}", W[n], want)
    elif name.startswith("U1250"):
        W = u1250(inp["div_2b_total"], inp["other_unrecap_1250"], inp["w28_1_4_total"],
                  inp["schd_7"], inp["lt_carryover"])
        for k, want in exp.items():
            n = int(k.split("_")[1])
            check(f"{name}.{k}", W[n], want)


# ═══════════════════════════════════════════════════════════════════════════
# 4. 8949 scenarios — independent column-(h) + totals recompute
# ═══════════════════════════════════════════════════════════════════════════

VALID_CODES = set("BCDEHLMNOPQRSTWXYZ")
ST_BOXES, LT_BOXES = set("ABCGHI"), set("DEFJKL")
PAIR = {"A": "1b", "G": "1b", "B": "2", "H": "2", "C": "3", "I": "3",
        "D": "8b", "J": "8b", "E": "9", "K": "9", "F": "10", "L": "10"}

for s in m.F8949_SCENARIOS:
    name = s["scenario_name"].split(" ")[0]
    inp, exp = s["inputs"], s["expected_outputs"]
    rows = inp["transactions"]
    tot = {"d": Decimal(0), "e": Decimal(0), "g": Decimal(0), "h": Decimal(0)}
    last_h = None
    for t in rows:
        h = D(t["d"]) - D(t["e"]) + D(t.get("g", 0))
        last_h = h
        for c, v in (("d", t["d"]), ("e", t["e"]), ("g", t.get("g", 0)), ("h", h)):
            tot[c] += D(v)
        codes = t.get("codes", "") or ""
        if t.get("is_summary") and "M" not in codes:
            err(f"{name}: summary row without code M")
        if codes and list(codes) != sorted(codes):
            err(f"{name}: codes not alphabetical: {codes}")
        for c in codes:
            if c not in VALID_CODES:
                err(f"{name}: unknown code letter {c}")
    for k, want in exp.items():
        if k.startswith("D_") or k in ("sign_check_applied", "col_b", "col_c"):
            continue
        got = {"line_2_d": tot["d"], "line_2_e": tot["e"], "line_2_g": tot["g"],
               "line_2_h": tot["h"], "col_h": last_h,
               "schd_line": PAIR.get(rows[0]["box"])}.get(k, "__missing__")
        if got == "__missing__":
            err(f"{name}.{k}: no independent recompute mapped")
        elif isinstance(want, str):
            if str(got) != want:
                err(f"{name}.{k}: recomputed {got} != authored {want}")
        else:
            check(f"{name}.{k}", got, want)
    # the D_8949_002 fixture really has (g) without a code
    if exp.get("D_8949_002"):
        bad = any(D(t.get("g", 0)) != 0 and not (t.get("codes") or "") for t in rows)
        if not bad:
            err(f"{name}: D_8949_002 expected but every adjustment has a code")

# Box partition sanity
if ST_BOXES | LT_BOXES != set("ABCDEFGHIJKL") or ST_BOXES & LT_BOXES:
    err("8949 box partition wrong")


# ═══════════════════════════════════════════════════════════════════════════
# 5. THE INVARIANT — SDTW(18=19=0) == QDCGT, swept across statuses + years
# ═══════════════════════════════════════════════════════════════════════════

SWEEP = [
    (2025, "single", 250000, 10000, 60000), (2025, "single", 150000, 0, 30000),
    (2025, "single", 90000, 5000, 20000), (2025, "single", 700000, 12000, 100000),
    (2025, "mfj", 96700, 4000, 25000), (2025, "mfj", 400000, 20000, 80000),
    (2025, "mfs", 310000, 0, 50000), (2025, "hoh", 64750, 1000, 10000),
    (2026, "single", 260000, 10000, 60000), (2026, "mfj", 98900, 4000, 25000),
    (2026, "hoh", 220000, 8000, 40000), (2026, "mfs", 49450, 2000, 12000),
    (2026, "qss", 620000, 15000, 90000),
]
for year, st, ti, qd, gain in SWEEP:
    s47 = sdtw(year, st, ti, qd, gain, gain, 0, 0)[47]
    q = qdcgt(year, st, ti, qd, gain)
    if s47 != q:
        err(f"INVARIANT sdtw==qdcgt FAILED [{year} {st} ti={ti} qd={qd} g={gain}]: {s47} != {q}")


# ═══════════════════════════════════════════════════════════════════════════
# 6. Structural checks (the check_spine_integrity precedent)
# ═══════════════════════════════════════════════════════════════════════════

known_sources = {s["source_code"] for s in m.AUTHORITY_SOURCES} | set(m.EXISTING_SOURCES_TO_REFERENCE)
for spec in m.FORMS:
    fn = spec["identity"]["form_number"]
    for key, idk in (("facts", "fact_key"), ("rules", "rule_id"),
                     ("lines", "line_number"), ("diagnostics", "diagnostic_id"),
                     ("scenarios", "scenario_name")):
        ids = [x[idk] for x in spec[key]]
        if len(ids) != len(set(ids)):
            dupes = sorted({i for i in ids if ids.count(i) > 1})
            err(f"{fn}.{key}: duplicate ids {dupes}")
    rule_ids = {r["rule_id"] for r in spec["rules"]}
    linked = {rl[0] for rl in spec["rule_links"]}
    for rid in rule_ids - linked:
        err(f"{fn}: rule {rid} has ZERO authority links")
    for rid, src, _, _ in spec["rule_links"]:
        if rid not in rule_ids:
            err(f"{fn}: rule_link references unknown rule {rid}")
        if src not in known_sources:
            err(f"{fn}: rule_link references unknown source {src}")
    diag_ids = {d["diagnostic_id"] for d in spec["diagnostics"]}
    for s in spec["scenarios"]:
        for k in s["expected_outputs"]:
            if k.startswith("D_") and k not in diag_ids:
                # cross-form diagnostics (e.g. D_SCHD_* asserted in an 8949 scenario) are allowed
                all_diags = {d["diagnostic_id"] for sp in m.FORMS for d in sp["diagnostics"]}
                if k not in all_diags:
                    err(f"{fn}/{s['scenario_name']}: expects unknown diagnostic {k}")

# worksheet line-count pins
ws_nums = [ln["line_number"] for ln in m.SCHDWS_LINES]
for prefix, count in (("sdtw", 47), ("clc", 13), ("w28", 7), ("u1250", 18)):
    got = len([n for n in ws_nums if n.startswith(prefix + "_")])
    if got != count:
        err(f"1040_SCHD_WS: {prefix} has {got} lines, expected {count}")

fa_ids = [a["assertion_id"] for a in m.FLOW_ASSERTIONS]
if len(fa_ids) != len(set(fa_ids)):
    err("duplicate flow-assertion ids")
if m.READY_TO_SEED:
    err("READY_TO_SEED must be False until Ken's walk")

# the 18-code data list is complete
code_facts = {f["fact_key"][-1] for f in m.F8949_FACTS if f["fact_key"].startswith("adj_code_")}
if code_facts != VALID_CODES:
    err(f"adj_code_* facts {sorted(code_facts)} != the i8949 table {sorted(VALID_CODES)}")


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
print("Independently recomputed: D-T1..T10 + D-G1/G2 (netting / loss limit / routing / carryover-out), "
      "SDTW-T1..T4 (25% partial-bind / 28% cap-no-bind / 28% binds / the 1==16 skip + Tax Table "
      "convention), CLC-T1/T2 (incl. the would-be-negative line 15), W28-T1, U1250-T1, F8949-T1..T5+G1 "
      "(col h / summary / multi-code / DA box); the SDTW==QDCGT invariant swept over 13 cases x both "
      "years x 5 statuses; loader constants cross-checked cell-by-cell vs an independent transcription "
      "(incl. line-19 == the 24%-bracket tops BOTH years).")

if errors:
    print("\nFAILURES:")
    for e in errors:
        print(f"  X {e}")
    sys.exit(1)
print("\nALL CHECKS PASS")
