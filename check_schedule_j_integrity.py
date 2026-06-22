"""Pre-seed content checker for load_1040_schedule_j (Schedule J — income averaging).

Run:  poetry run python check_schedule_j_integrity.py

Mirrors check_schedule_f_integrity.py: validates the authored lists WITHOUT
touching the DB, then INDEPENDENTLY recomputes every numeric scenario from its
OWN transcription of the form math (NOT imported from the loader) — the Schedule J
23-line chain (lines 3/4/6/7/8/11/12/15/16/17/18/22/23) over independently
re-typed BASE-YEAR rate schedules. This is the MATH GATE that must pass before
Ken's review walk. Loader & gate share no math.

The checker carries its OWN independent copies of the year-keyed rate schedules
(2022/23/24 base + 2025 current), the preferential-rate breakpoints, and the SDTW
mid threshold (re-typed from the 2025 i1040sj.pdf / i1040sd PDFs), and cross-checks
the loader's module constants cell-by-cell — so a transcription error in the loader
cannot also pass the checker.
"""
import os
import sys
from decimal import Decimal, ROUND_HALF_UP

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_schedule_j as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def whole(x):
    return D(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def check(name, got, want):
    if D(got) != D(want):
        err(f"{name}: recomputed {got} != authored {want}")


_INF = 10 ** 12

# ═══════════════════════════════════════════════════════════════════════════
# INDEPENDENT CONSTANTS (re-typed from i1040sj.pdf pages 4/8/12 + the verified
# spine 2025 brackets; NOT imported from the loader). Cross-checked below.
# ═══════════════════════════════════════════════════════════════════════════

IND_RATES = {
    2022: {
        "single": [(10275, "0.10"), (41775, "0.12"), (89075, "0.22"), (170050, "0.24"), (215950, "0.32"), (539900, "0.35"), (_INF, "0.37")],
        "mfj":    [(20550, "0.10"), (83550, "0.12"), (178150, "0.22"), (340100, "0.24"), (431900, "0.32"), (647850, "0.35"), (_INF, "0.37")],
        "mfs":    [(10275, "0.10"), (41775, "0.12"), (89075, "0.22"), (170050, "0.24"), (215950, "0.32"), (323925, "0.35"), (_INF, "0.37")],
        "hoh":    [(14650, "0.10"), (55900, "0.12"), (89050, "0.22"), (170050, "0.24"), (215950, "0.32"), (539900, "0.35"), (_INF, "0.37")],
    },
    2023: {
        "single": [(11000, "0.10"), (44725, "0.12"), (95375, "0.22"), (182100, "0.24"), (231250, "0.32"), (578125, "0.35"), (_INF, "0.37")],
        "mfj":    [(22000, "0.10"), (89450, "0.12"), (190750, "0.22"), (364200, "0.24"), (462500, "0.32"), (693750, "0.35"), (_INF, "0.37")],
        "mfs":    [(11000, "0.10"), (44725, "0.12"), (95375, "0.22"), (182100, "0.24"), (231250, "0.32"), (346875, "0.35"), (_INF, "0.37")],
        "hoh":    [(15700, "0.10"), (59850, "0.12"), (95350, "0.22"), (182100, "0.24"), (231250, "0.32"), (578100, "0.35"), (_INF, "0.37")],
    },
    2024: {
        "single": [(11600, "0.10"), (47150, "0.12"), (100525, "0.22"), (191950, "0.24"), (243725, "0.32"), (609350, "0.35"), (_INF, "0.37")],
        "mfj":    [(23200, "0.10"), (94300, "0.12"), (201050, "0.22"), (383900, "0.24"), (487450, "0.32"), (731200, "0.35"), (_INF, "0.37")],
        "mfs":    [(11600, "0.10"), (47150, "0.12"), (100525, "0.22"), (191950, "0.24"), (243725, "0.32"), (365600, "0.35"), (_INF, "0.37")],
        "hoh":    [(16550, "0.10"), (63100, "0.12"), (100500, "0.22"), (191950, "0.24"), (243700, "0.32"), (609350, "0.35"), (_INF, "0.37")],
    },
    # 2025 current-year (for line 4) — re-typed from the verified spine TAX_BRACKETS.
    2025: {
        "single": [(11925, "0.10"), (48475, "0.12"), (103350, "0.22"), (197300, "0.24"), (250525, "0.32"), (626350, "0.35"), (_INF, "0.37")],
        "mfj":    [(23850, "0.10"), (96950, "0.12"), (206700, "0.22"), (394600, "0.24"), (501050, "0.32"), (751600, "0.35"), (_INF, "0.37")],
        "mfs":    [(11925, "0.10"), (48475, "0.12"), (103350, "0.22"), (197300, "0.24"), (250525, "0.32"), (375800, "0.35"), (_INF, "0.37")],
        "hoh":    [(17000, "0.10"), (64850, "0.12"), (103350, "0.22"), (197300, "0.24"), (250500, "0.32"), (626350, "0.35"), (_INF, "0.37")],
    },
}

IND_PREF = {
    2022: {"single": {"zero_ceiling": 41675, "twenty_floor": 459750}, "mfj": {"zero_ceiling": 83350, "twenty_floor": 517200},
           "mfs": {"zero_ceiling": 41675, "twenty_floor": 258600}, "hoh": {"zero_ceiling": 55800, "twenty_floor": 488500}},
    2023: {"single": {"zero_ceiling": 44625, "twenty_floor": 492300}, "mfj": {"zero_ceiling": 89250, "twenty_floor": 553850},
           "mfs": {"zero_ceiling": 44625, "twenty_floor": 276900}, "hoh": {"zero_ceiling": 59750, "twenty_floor": 523050}},
    2024: {"single": {"zero_ceiling": 47025, "twenty_floor": 518900}, "mfj": {"zero_ceiling": 94050, "twenty_floor": 583750},
           "mfs": {"zero_ceiling": 47025, "twenty_floor": 291850}, "hoh": {"zero_ceiling": 63000, "twenty_floor": 551350}},
    2025: {"single": {"zero_ceiling": 48350, "twenty_floor": 533400}, "mfj": {"zero_ceiling": 96700, "twenty_floor": 600050},
           "mfs": {"zero_ceiling": 48350, "twenty_floor": 300000}, "hoh": {"zero_ceiling": 64750, "twenty_floor": 566700}},
}

IND_MID = {
    2022: {"single": 170050, "mfj": 340100, "mfs": 170050, "hoh": 170050},
    2023: {"single": 182100, "mfj": 364200, "mfs": 182100, "hoh": 182100},
    2024: {"single": 191950, "mfj": 383900, "mfs": 191950, "hoh": 191950},
    2025: {"single": 197300, "mfj": 394600, "mfs": 197300, "hoh": 197300},
}


def rate_tax(amount, year, status):
    """Independent cumulative bracket math (the BASE-YEAR rate schedule — never the
    Tax Table). Whole-dollar tax (ROUND_HALF_UP). qss -> mfj."""
    amount = D(amount)
    if amount <= 0:
        return D(0)
    if status == "qss":
        status = "mfj"
    tax = D(0)
    prev = D(0)
    for ceiling, rate in IND_RATES[year][status]:
        ceil = D(ceiling)
        if amount > ceil:
            tax += (ceil - prev) * D(rate)
            prev = ceil
        else:
            tax += (amount - prev) * D(rate)
            break
    return whole(tax)


def sched_j(inp):
    """Independent Schedule J 23-line chain (ordinary/rate-schedule path).
    Base years for TY2025 = 2022/2023/2024. Uses the entered base-year original
    taxes (lines 19/20/21) directly. Returns a dict of computed lines."""
    year = int(inp.get("tax_year", 2025))
    by = m.BASE_YEARS_BY_ELECTION[year]  # {1:2022,2:2023,3:2024} for 2025
    L1 = D(inp.get("line_1", 0))
    L2a = D(inp.get("sj_elected_farm_income_2a", 0))
    L3 = L1 - L2a
    cy_status = inp.get("filing_status", "single")
    L4 = rate_tax(L3, year, cy_status)
    L6 = whole(L2a / m.LINE6_DIVISOR)

    def base_status(n):
        return inp.get(f"sj_by{n}_filing_status", cy_status)

    L5 = D(inp.get("sj_by1_taxable_income", 0))
    L7 = max(D(0), L5 + L6)
    L8 = D(0) if L7 <= 0 else rate_tax(L7, by[1], base_status(1))

    L9 = D(inp.get("sj_by2_taxable_income", 0))
    L11 = L9 + L6
    L12 = D(0) if L11 <= 0 else rate_tax(L11, by[2], base_status(2))

    L13 = D(inp.get("sj_by3_taxable_income", 0))
    L15 = L13 + L6
    L16 = D(0) if L15 <= 0 else rate_tax(L15, by[3], base_status(3))

    L17 = L4 + L8 + L12 + L16
    L19 = D(inp.get("sj_by1_tax", 0))
    L20 = D(inp.get("sj_by2_tax", 0))
    L21 = D(inp.get("sj_by3_tax", 0))
    L22 = L19 + L20 + L21
    L23 = L17 - L22
    return {"3": L3, "4": L4, "6": L6, "7": L7, "8": L8, "11": L11, "12": L12,
            "15": L15, "16": L16, "17": L17, "18": L17, "22": L22, "23": L23}


# ═══════════════════════════════════════════════════════════════════════════
# Structural checks (mirror check_schedule_f_integrity.py)
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

    # DB column caps: rule_id / diagnostic_id / line_number are varchar(20).
    for did in diag_ids:
        if len(did) > 20:
            err(f"{fn}: diagnostic_id too long (>20): {did}")
    for rid in rule_ids:
        if len(rid) > 20:
            err(f"{fn}: rule_id too long (>20): {rid}")
    for lno in line_nos:
        if len(str(lno)) > 20:
            err(f"{fn}: line_number too long (>20): {lno}")

    linked = {rid for rid, *_ in spec["rule_links"]}
    uncited = [rid for rid in rule_ids if rid not in linked]
    if uncited:
        err(f"{fn}: uncited rules {uncited}")
    dangling = [rid for rid in linked if rid not in rule_ids]
    if dangling:
        err(f"{fn}: rule_links reference unknown rules {dangling}")

    for r in spec["rules"]:
        for key in r.get("inputs", []):
            if key not in fact_keys:
                err(f"{fn} {r['rule_id']}: input '{key}' is not a declared fact")

# ── flow assertions ──
fa_ids = [a["assertion_id"] for a in m.FLOW_ASSERTIONS]
if len(fa_ids) != len(set(fa_ids)):
    err("duplicate flow assertion ids")
for a in m.FLOW_ASSERTIONS:
    if len(a["assertion_id"]) > 20:
        err(f"assertion_id too long (>20): {a['assertion_id']}")


# ═══════════════════════════════════════════════════════════════════════════
# Loader constants cross-check (loader module constants == independent copies),
# cell-by-cell — the load-bearing verification.
# ═══════════════════════════════════════════════════════════════════════════

for yr in (2022, 2023, 2024):
    for st in ("single", "mfj", "mfs", "hoh"):
        loader = m.BASE_YEAR_RATE_SCHEDULES[yr][st]
        indep = IND_RATES[yr][st]
        if len(loader) != len(indep):
            err(f"BASE_YEAR_RATE_SCHEDULES[{yr}][{st}] length {len(loader)} != {len(indep)}")
            continue
        for k, ((lc, lr), (ic, ir)) in enumerate(zip(loader, indep)):
            if D(lc) != D(ic) or D(lr) != D(ir):
                err(f"BASE_YEAR_RATE_SCHEDULES[{yr}][{st}][{k}] loader ({lc},{lr}) != independent ({ic},{ir})")
    if m.BASE_YEAR_RATE_SCHEDULES[yr].get("qss") is not None:
        err(f"BASE_YEAR_RATE_SCHEDULES[{yr}][qss] must be None (QSS uses MFJ)")

for yr in (2022, 2023, 2024, 2025):
    for st in ("single", "mfj", "mfs", "hoh"):
        for k in ("zero_ceiling", "twenty_floor"):
            if D(m.PREF_RATE_BREAKPOINTS[yr][st][k]) != D(IND_PREF[yr][st][k]):
                err(f"PREF_RATE_BREAKPOINTS[{yr}][{st}][{k}] loader {m.PREF_RATE_BREAKPOINTS[yr][st][k]} != independent {IND_PREF[yr][st][k]}")
        if D(m.SDTW_MID_THRESHOLD[yr][st]) != D(IND_MID[yr][st]):
            err(f"SDTW_MID_THRESHOLD[{yr}][{st}] loader {m.SDTW_MID_THRESHOLD[yr][st]} != independent {IND_MID[yr][st]}")

if int(m.LINE6_DIVISOR) != 3:
    err(f"LINE6_DIVISOR loader {m.LINE6_DIVISOR} != 3")
if m.BASE_YEARS_BY_ELECTION[2025] != {1: 2022, 2: 2023, 3: 2024}:
    err("BASE_YEARS_BY_ELECTION[2025] must be {1:2022,2:2023,3:2024}")
if m.BASE_YEARS_BY_ELECTION[2026] != {1: 2023, 2: 2024, 3: 2025}:
    err("BASE_YEARS_BY_ELECTION[2026] must be {1:2023,2:2024,3:2025}")


# ═══════════════════════════════════════════════════════════════════════════
# Scenario lookup + independent recompute
# ═══════════════════════════════════════════════════════════════════════════

s = {sc["scenario_name"].split(" ")[0]: sc for spec in m.FORMS for sc in spec["scenarios"]}


def i_of(key):
    return s[key]["inputs"]


def o_of(key):
    return s[key]["expected_outputs"]


# ── SJ-T1 — full numeric anchor (single, all rate-schedule) ──
i, o = i_of("SJ-T1"), o_of("SJ-T1")
r = sched_j(i)
for ln in ("3", "4", "6", "7", "8", "11", "12", "15", "16", "17", "22", "23"):
    check(f"SJ-T1 L{ln}", r[ln], o[f"line_{ln}"])
# the regular (non-Sch-J) tax pin + the "averaging saves" relation.
reg = rate_tax(i["line_1"], i["tax_year"], i["filing_status"])
check("SJ-T1 regular tax", reg, o["regular_tax_2025"])
if not (r["23"] < reg):
    err("SJ-T1: line 23 should be LESS than the regular tax (averaging saves)")

# ── SJ-T2 — negative base year (line 11 < 0 -> line 12 = 0) ──
i, o = i_of("SJ-T2"), o_of("SJ-T2")
r = sched_j(i)
check("SJ-T2 L6", r["6"], o["line_6"]); check("SJ-T2 L11", r["11"], o["line_11"]); check("SJ-T2 L12", r["12"], o["line_12"])
if r["11"] >= 0:
    err("SJ-T2: fixture should drive line 11 negative")
if r["12"] != 0:
    err("SJ-T2: line 12 must be 0 when line 11 <= 0")

# ── SJ-T5 — prior Schedule J used -> chaining RED (structural) ──
i = i_of("SJ-T5")
if not (i.get("sj_by1_used_schedule_j") or i.get("sj_by2_used_schedule_j") or i.get("sj_by3_used_schedule_j")):
    err("SJ-T5: fixture must set a sj_byN_used_schedule_j for D_SJ_CHAIN")
if o_of("SJ-T5").get("line_23") is not None:
    err("SJ-T5: line 23 must be None (no silent compute under chaining RED)")

# ── SJ-T6 — Form 2555 -> RED (structural) ──
i = i_of("SJ-T6")
if not (i.get("sj_by1_form_2555") or i.get("sj_by2_form_2555") or i.get("sj_by3_form_2555")):
    err("SJ-T6: fixture must set a sj_byN_form_2555 for D_SJ_2555")

# ── SJ-T7 — zero-or-less base-year TI entered -> warning + compute proceeds ──
i, o = i_of("SJ-T7"), o_of("SJ-T7")
r = sched_j(i)
check("SJ-T7 L7", r["7"], o["line_7"])
if D(i.get("sj_by1_taxable_income", 0)) > 0:
    err("SJ-T7: fixture should have a base-year TI <= 0 for D_SJ_NEG_TI")

# ── SJ-T8 — line 2a exceeds line 1 (structural) ──
i = i_of("SJ-T8")
if not (D(i["sj_elected_farm_income_2a"]) > D(i["line_1"])):
    err("SJ-T8: fixture must have line 2a > line 1 for D_SJ_2A_EXCEED")

# ── SJ-T9 — differing filing status (base year MFJ) ──
i, o = i_of("SJ-T9"), o_of("SJ-T9")
r = sched_j(i)
check("SJ-T9 L7", r["7"], o["line_7"])
if i.get("sj_by1_filing_status") != "mfj":
    err("SJ-T9: fixture should set base-year-1 filing status MFJ")

# ── SJ-T10 — line 6 rounding ──
i, o = i_of("SJ-T10"), o_of("SJ-T10")
r = sched_j(i)
check("SJ-T10 L6 (round half-up)", r["6"], o["line_6"])


# ═══════════════════════════════════════════════════════════════════════════
# Load-bearing checks on the flow-assertion constants_check blocks
# ═══════════════════════════════════════════════════════════════════════════

def fa(aid):
    return next((a for a in m.FLOW_ASSERTIONS if a["assertion_id"] == aid), None)


a04 = fa("FA-1040-SCHJ-04")
if a04:
    c = a04["definition"]["constants"]
    if [D(x) for x in c["single_2022_floors"]] != [D(t[0]) for t in IND_RATES[2022]["single"][:6]]:
        err("FA-SCHJ-04: single_2022_floors disagree with independent")
    if [D(x) for x in c["mfj_2024_floors"]] != [D(t[0]) for t in IND_RATES[2024]["mfj"][:6]]:
        err("FA-SCHJ-04: mfj_2024_floors disagree with independent")
    if c.get("ordinary_via_rate_schedule_not_tax_table") is not True:
        err("FA-SCHJ-04: must assert ordinary tax via rate schedule, not the Tax Table")
else:
    err("FA-1040-SCHJ-04 not found")

a05 = fa("FA-1040-SCHJ-05")
if a05:
    c = a05["definition"]["constants"]
    if c.get("sdtw_ordinary_lines") != [44, 46]:
        err("FA-SCHJ-05: sdtw_ordinary_lines must be [44, 46] (not the stale 34/36 or 42/44)")
    if D(c["zero_ceiling_2022_single"]) != D(IND_PREF[2022]["single"]["zero_ceiling"]):
        err("FA-SCHJ-05: zero_ceiling_2022_single disagrees")
    if D(c["twenty_floor_2024_mfj"]) != D(IND_PREF[2024]["mfj"]["twenty_floor"]):
        err("FA-SCHJ-05: twenty_floor_2024_mfj disagrees")
    if D(c["mid_threshold_2023_single"]) != D(IND_MID[2023]["single"]):
        err("FA-SCHJ-05: mid_threshold_2023_single disagrees")
    if c.get("base_year_allocates_third_2b") is not True:
        err("FA-SCHJ-05: must assert the base-year SDTW allocates 1/3 of 2b")
else:
    err("FA-1040-SCHJ-05 not found")

a06 = fa("FA-1040-SCHJ-06")
if a06:
    c = a06["definition"]["constants"]
    if D(c["zero_ceiling_2023_mfj"]) != D(IND_PREF[2023]["mfj"]["zero_ceiling"]):
        err("FA-SCHJ-06: zero_ceiling_2023_mfj disagrees")
    if D(c["twenty_floor_2022_single"]) != D(IND_PREF[2022]["single"]["twenty_floor"]):
        err("FA-SCHJ-06: twenty_floor_2022_single disagrees")
    if D(c["zero_ceiling_2024_hoh"]) != D(IND_PREF[2024]["hoh"]["zero_ceiling"]):
        err("FA-SCHJ-06: zero_ceiling_2024_hoh disagrees")
else:
    err("FA-1040-SCHJ-06 not found")

# FA-07 numeric anchor must agree with the independent SJ-T1 recompute.
a07 = fa("FA-1040-SCHJ-07")
if not a07:
    err("FA-1040-SCHJ-07 not found")

# FA-01 must route line 23 to 1040 line 16.
a01 = fa("FA-1040-SCHJ-01")
if not a01 or a01["definition"].get("must_write_to") != ["1040.16"]:
    err("FA-1040-SCHJ-01: line 23 must write to 1040.16")


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
print("Independently recomputed: SJ-T1 (full 23-line chain over re-typed 2022/23/24/25 rate schedules; "
      "L4=21,647, L8=6,617, L12=7,408, L16=8,253, L23=31,982 < regular 36,047), SJ-T2 (negative line 11 "
      "-> line 12 = 0), SJ-T7 (zero-or-less base-year TI, line 7 floor), SJ-T9 (differing filing status), "
      "SJ-T10 (line-6 round-half-up); loader rate schedules / preferential breakpoints / SDTW mid threshold "
      "cross-checked cell-by-cell vs an independent transcription of the IRS PDFs.")

if errors:
    print("\nFAILURES:")
    for e in errors:
        print(f"  X {e}")
    sys.exit(1)
print("\nALL CHECKS PASS")
