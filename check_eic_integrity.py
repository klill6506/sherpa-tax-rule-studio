"""Pre-seed content checker for load_1040_eic (Topic 7).

Run:  poetry run python check_eic_integrity.py

Mirrors check_retirement_integrity.py / check_intdiv_integrity.py: validates the
authored lists WITHOUT touching the DB, then INDEPENDENTLY recomputes every
numeric scenario — the EIC Table $50-bracket midpoint lookup (the piecewise §32
credit function), the Step-5 earned income, the mainstream Worksheet-B SE earned
income, the lower-of-AGI/earned-income rule, and the investment-income / RED gates.
This is the MATH GATE that must pass before Ken's review walk.

The checker carries its OWN independent transcription of the §32 EIC parameter
tables (re-typed here from the same Rev Procs, NOT imported from the loader) and
its own EIC Table evaluator, so a transcription error in the loader cannot also
pass the checker. The loader's m.EIC_PARAMS is then cross-checked cell-by-cell
against this independent copy.
"""
import os
import sys
from decimal import Decimal, ROUND_HALF_UP

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_eic as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def check(name, got, want):
    if D(got) != D(want):
        err(f"{name}: recomputed {got} != authored {want}")


# ═══════════════════════════════════════════════════════════════════════════
# INDEPENDENT §32 PARAMETER TABLES (re-typed from RP 2024-40 §2.06 / RP 2025-32
# §2.06; columns "0"/"1"/"2"/"3+"). NOT imported from the loader.
# ═══════════════════════════════════════════════════════════════════════════

IND_PARAMS: dict[int, dict] = {
    2025: {
        "earned_income_amount": {"0": 8490, "1": 12730, "2": 17880, "3+": 17880},
        "max_credit":           {"0": 649,  "1": 4328,  "2": 7152,  "3+": 8046},
        "threshold_mfj":        {"0": 17730, "1": 30470, "2": 30470, "3+": 30470},
        "completed_mfj":        {"0": 26214, "1": 57554, "2": 64430, "3+": 68675},
        "threshold_other":      {"0": 10620, "1": 23350, "2": 23350, "3+": 23350},
        "completed_other":      {"0": 19104, "1": 50434, "2": 57310, "3+": 61555},
        "investment_income_limit": 11950,
    },
    2026: {
        "earned_income_amount": {"0": 8680, "1": 13020, "2": 18290, "3+": 18290},
        "max_credit":           {"0": 664,  "1": 4427,  "2": 7316,  "3+": 8231},
        "threshold_mfj":        {"0": 18140, "1": 31160, "2": 31160, "3+": 31160},
        "completed_mfj":        {"0": 26820, "1": 58863, "2": 65899, "3+": 70244},
        "threshold_other":      {"0": 10860, "1": 23890, "2": 23890, "3+": 23890},
        "completed_other":      {"0": 19540, "1": 51593, "2": 58629, "3+": 62974},
        "investment_income_limit": 12200,
    },
}

# Statutory §32(b)(1) percentages — same both years, NOT indexed.
IND_CREDIT_RATE = {"0": Decimal("0.0765"), "1": Decimal("0.34"), "2": Decimal("0.40"), "3+": Decimal("0.45")}
IND_PHASEOUT_RATE = {"0": Decimal("0.0765"), "1": Decimal("0.1598"), "2": Decimal("0.2106"), "3+": Decimal("0.2106")}

IND_CHILDLESS_AGE_MIN = 25
IND_CHILDLESS_AGE_MAX_EXCLUSIVE = 65


# ═══════════════════════════════════════════════════════════════════════════
# Independent recomputations
# ═══════════════════════════════════════════════════════════════════════════

def qc_col(qc: int) -> str:
    return "3+" if int(qc) >= 3 else str(int(qc))


def status_key(status: str) -> str:
    """EIC column rule: MFJ uses 'mfj'; single/HOH/QSS/MFS(§32(d)) use 'other'.
    QSS uses 'other' (NOT MFJ — unlike QDCGT)."""
    return "mfj" if status == "mfj" else "other"


def eic_table(lookup, qc, status, year) -> Decimal:
    """Published EIC Table = §32 credit function at the $50-bracket MIDPOINT,
    ROUND_HALF_UP. Bracket for L is [50*floor(L/50), +50); midpoint = lo + 25."""
    col = qc_col(qc)
    p = IND_PARAMS[year]
    eia = D(p["earned_income_amount"][col])
    maxc = D(p["max_credit"][col])
    sk = status_key(status)
    thr = D(p[f"threshold_{sk}"][col])
    comp = D(p[f"completed_{sk}"][col])
    crate = IND_CREDIT_RATE[col]
    prate = IND_PHASEOUT_RATE[col]
    L = D(lookup)
    if L <= 0:
        return Decimal("0")
    lo = (int(L) // 50) * 50
    mid = D(lo) + D(25)
    if mid < eia:
        credit = mid * crate
    elif mid < thr:
        credit = maxc
    elif mid < comp:
        credit = maxc - (mid - thr) * prate
    else:
        credit = Decimal("0")
    if credit < 0:
        credit = Decimal("0")
    return credit.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def threshold(qc, status, year) -> Decimal:
    return D(IND_PARAMS[year][f"threshold_{status_key(status)}"][qc_col(qc)])


def step5_earned(wages_1z, medicaid_waiver=0, include_waiver=False, combat=0, elect_combat=False) -> Decimal:
    l2 = Decimal("0") if include_waiver else D(medicaid_waiver)
    l3 = D(wages_1z) - l2
    l4 = D(combat) if elect_combat else Decimal("0")
    return l3 + l4


def wsb_earned(se_net, se_half, wages=0) -> Decimal:
    """Worksheet B mainstream sole-proprietor: 1e = se_net - se_half; 4b = 1e + wages."""
    l1e = D(se_net) - D(se_half)
    return l1e + D(wages)


def lower_of_credit(earned, agi, qc, status, year) -> Decimal:
    """Worksheet A/B lower-of-AGI rule -> the EIC."""
    le = eic_table(earned, qc, status, year)
    if D(agi) == D(earned):
        return le
    if D(agi) < threshold(qc, status, year):
        return le
    la = eic_table(agi, qc, status, year)
    return min(la, le)


# ═══════════════════════════════════════════════════════════════════════════
# Structural checks (mirror check_retirement_integrity.py)
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
# Loader constants cross-check (loader m.EIC_PARAMS == independent IND_PARAMS)
# ═══════════════════════════════════════════════════════════════════════════

for year in (2025, 2026):
    lp = m.EIC_PARAMS[year]
    ip = IND_PARAMS[year]
    for key in ("earned_income_amount", "max_credit", "threshold_mfj", "completed_mfj",
                "threshold_other", "completed_other"):
        for col in ("0", "1", "2", "3+"):
            if D(lp[key][col]) != D(ip[key][col]):
                err(f"EIC_PARAMS[{year}][{key}][{col}] loader {lp[key][col]} != independent {ip[key][col]}")
    if D(lp["investment_income_limit"]) != D(ip["investment_income_limit"]):
        err(f"EIC_PARAMS[{year}] investment_income_limit loader {lp['investment_income_limit']} "
            f"!= independent {ip['investment_income_limit']}")

for col in ("0", "1", "2", "3+"):
    if Decimal(str(m.EIC_RATES["credit_rate"][col])) != IND_CREDIT_RATE[col]:
        err(f"EIC_RATES credit_rate[{col}] loader {m.EIC_RATES['credit_rate'][col]} != independent {IND_CREDIT_RATE[col]}")
    if Decimal(str(m.EIC_RATES["phaseout_rate"][col])) != IND_PHASEOUT_RATE[col]:
        err(f"EIC_RATES phaseout_rate[{col}] loader {m.EIC_RATES['phaseout_rate'][col]} != independent {IND_PHASEOUT_RATE[col]}")

if m.EIC_CHILDLESS_AGE_MIN != IND_CHILDLESS_AGE_MIN or m.EIC_CHILDLESS_AGE_MAX_EXCLUSIVE != IND_CHILDLESS_AGE_MAX_EXCLUSIVE:
    err("EIC childless age band constants disagree with independent (25 / 65-exclusive)")


# ═══════════════════════════════════════════════════════════════════════════
# §32 internal reconciliation (published amounts vs statutory rate, within $1)
# ═══════════════════════════════════════════════════════════════════════════

for year in (2025, 2026):
    p = IND_PARAMS[year]
    for col in ("0", "1", "2", "3+"):
        eia = D(p["earned_income_amount"][col])
        maxc = D(p["max_credit"][col])
        crate = IND_CREDIT_RATE[col]
        # max_credit ~= earned_income_amount * credit_rate (TY2026 0-QC published 664 vs 663.42 -> allow $1)
        if abs(maxc - eia * crate) > Decimal("1"):
            err(f"{year} {col}: max_credit {maxc} not within $1 of eia*rate {eia * crate}")
        prate = IND_PHASEOUT_RATE[col]
        for sk in ("mfj", "other"):
            thr = D(p[f"threshold_{sk}"][col])
            comp = D(p[f"completed_{sk}"][col])
            # completed ~= threshold + max_credit / phaseout_rate (rounded up to next $1)
            implied = thr + maxc / prate
            if abs(comp - implied) > Decimal("1"):
                err(f"{year} {col} {sk}: completed {comp} not within $1 of threshold+max/rate {implied}")


# ═══════════════════════════════════════════════════════════════════════════
# Scenario lookup (key on the first token of scenario_name)
# ═══════════════════════════════════════════════════════════════════════════

s = {sc["scenario_name"].split(" ")[0]: sc for spec in m.FORMS for sc in spec["scenarios"]}


def i_of(key):
    return s[key]["inputs"]


def o_of(key):
    return s[key]["expected_outputs"]


# ── EIC-T1: 1 QC plateau -> max credit, AGI == earned (no lower-of) ──
i, o = i_of("EIC-T1"), o_of("EIC-T1")
t1_earned = eic_table(i["earned_income"], i["qualifying_children"], i["filing_status"], i["tax_year"])
check("EIC-T1 table@earned", t1_earned, o["eic_table_amount_earned"])
check("EIC-T1 27a", lower_of_credit(i["earned_income"], i["agi"], i["qualifying_children"], i["filing_status"], i["tax_year"]), o["1040_line_27a"])

# ── EIC-T2: 0 QC phaseout -> strictly between 0 and max_credit ──
i = i_of("EIC-T2")
t2 = eic_table(i["earned_income"], 0, i["filing_status"], i["tax_year"])
maxc0 = D(IND_PARAMS[i["tax_year"]]["max_credit"]["0"])
if not (Decimal("0") < t2 < maxc0):
    err(f"EIC-T2: table@14000 {t2} not in the phaseout (0, {maxc0})")
# independent exact pin: 649 - (14025 - 10620)*0.0765 = 388.52 -> 389
if t2 != Decimal("389"):
    err(f"EIC-T2: independent phaseout recompute expected 389, got {t2}")

# ── EIC-T3: lower-of-AGI binds (AGI 40,000 > earned 15,000 and in phaseout) ──
i, o = i_of("EIC-T3"), o_of("EIC-T3")
t3_earned = eic_table(i["earned_income"], i["qualifying_children"], i["filing_status"], i["tax_year"])
t3_credit = lower_of_credit(i["earned_income"], i["agi"], i["qualifying_children"], i["filing_status"], i["tax_year"])
check("EIC-T3 table@earned", t3_earned, o["eic_table_amount_earned"])
if not (t3_credit < t3_earned):
    err(f"EIC-T3: lower-of did not bind (credit {t3_credit} not < table@earned {t3_earned})")
if t3_credit != Decimal("1663"):
    err(f"EIC-T3: independent lower-of recompute expected 1663, got {t3_credit}")

# ── EIC-T4: the i1040gi midpoint pin (1 QC, lookup 2,475 -> 842) ──
i, o = i_of("EIC-T4"), o_of("EIC-T4")
check("EIC-T4 midpoint pin", eic_table(i["earned_income"], i["qualifying_children"], i["filing_status"], i["tax_year"]), o["eic_table_amount_earned"])
# load-bearing: 2475 * 0.34 = 841.5 must ROUND HALF UP to 842 (truncate would give 841)
if eic_table(2475, 1, "single", 2025) != Decimal("842"):
    err("EIC-T4: ROUND_HALF_UP pin not load-bearing (expected 842 from 841.5)")

# ── EIC-T5: investment income over limit -> 0 (gate) ──
i = i_of("EIC-T5")
limit = D(IND_PARAMS[i["tax_year"]]["investment_income_limit"])
if not (D(i["investment_income_total"]) > limit):
    err(f"EIC-T5: fixture inv {i['investment_income_total']} does not exceed limit {limit} (gate would not fire)")
# absent the gate the credit would be nonzero -> proves the gate is what zeroes it
if eic_table(i["earned_income"], i["qualifying_children"], i["filing_status"], i["tax_year"]) <= 0:
    err("EIC-T5: underlying EIC is 0 even before the inv-income gate (gate not isolated)")
check("EIC-T5 27a (gated)", 0, o_of("EIC-T5")["1040_line_27a"])

# ── EIC-T6a/T6b: childless age band fixtures ──
if i_of("EIC-T6a").get("eic_childless_age_qualifies") is not True:
    err("EIC-T6a: fixture must set eic_childless_age_qualifies True (age 25)")
if i_of("EIC-T6b").get("eic_childless_age_qualifies") is not False:
    err("EIC-T6b: fixture must set eic_childless_age_qualifies False (age 24)")
check("EIC-T6b 27a", 0, o_of("EIC-T6b")["1040_line_27a"])

# ── EIC-T7: MFJ column (plateau) vs single (phaseout) for the same earned income ──
i, o = i_of("EIC-T7"), o_of("EIC-T7")
mfj_credit = eic_table(i["earned_income"], i["qualifying_children"], "mfj", i["tax_year"])
other_credit = eic_table(i["earned_income"], i["qualifying_children"], "single", i["tax_year"])
check("EIC-T7 MFJ table", mfj_credit, o["eic_table_amount_earned"])
check("EIC-T7 mfj threshold", threshold(i["qualifying_children"], "mfj", i["tax_year"]), o["uses_mfj_threshold"])
if not (mfj_credit > other_credit):
    err(f"EIC-T7: MFJ column not load-bearing (mfj {mfj_credit} <= other {other_credit})")

# ── EIC-T8: combat-pay election raises Step-5 earned income into the plateau ──
i, o = i_of("EIC-T8"), o_of("EIC-T8")
earned_elected = step5_earned(i["wages_1z"], combat=i["nontaxable_combat_pay"], elect_combat=i["elect_combat_pay"])
check("EIC-T8 earned (elected)", earned_elected, o["eic_earned_income_result"])
check("EIC-T8 table@earned", eic_table(earned_elected, i["qualifying_children"], i["filing_status"], i["tax_year"]), o["eic_table_amount_earned"])
earned_unelected = step5_earned(i["wages_1z"], combat=i["nontaxable_combat_pay"], elect_combat=False)
if not (eic_table(earned_elected, i["qualifying_children"], i["filing_status"], i["tax_year"])
        > eic_table(earned_unelected, i["qualifying_children"], i["filing_status"], i["tax_year"])):
    err("EIC-T8: combat-pay election is not load-bearing (electing did not raise the credit)")

# ── EIC-T9: TY2026 3+ QC plateau (and != TY2025) ──
i, o = i_of("EIC-T9"), o_of("EIC-T9")
t9 = eic_table(i["earned_income"], i["qualifying_children"], i["filing_status"], i["tax_year"])
check("EIC-T9 TY2026 3+ table", t9, o["eic_table_amount_earned"])
check("EIC-T9 27a", lower_of_credit(i["earned_income"], i["agi"], i["qualifying_children"], i["filing_status"], i["tax_year"]), o["1040_line_27a"])
if D(IND_PARAMS[2026]["max_credit"]["3+"]) == D(IND_PARAMS[2025]["max_credit"]["3+"]):
    err("EIC-T9: TY2026 3+ max credit equals TY2025 — year-keying not load-bearing")

# ── EIC-T10: Worksheet B SE earned income ──
i, o = i_of("EIC-T10"), o_of("EIC-T10")
t10 = wsb_earned(i["eic_se_net_earnings"], i["eic_se_half_deduction"], i.get("wages_1z", 0))
check("EIC-T10 wsb_1e", D(i["eic_se_net_earnings"]) - D(i["eic_se_half_deduction"]), o["wsb_1e"])
check("EIC-T10 wsb_4b", t10, o["wsb_4b"])
check("EIC-T10 earned", t10, o["eic_earned_income_result"])

# ── RED-gate fixtures actually satisfy their condition ──
g1 = i_of("EIC-G1")
if not (g1.get("filing_status") == "mfs" and not g1.get("mfs_eic_special_rule")):
    err("EIC-G1: fixture does not satisfy D_EIC_005 (MFS without §32(d))")
if not i_of("EIC-G2").get("files_form_2555"):
    err("EIC-G2: fixture does not set files_form_2555 for D_EIC_006")
if not i_of("EIC-G3").get("eic_form_4797_present"):
    err("EIC-G3: fixture does not set eic_form_4797_present for D_EIC_003")
g4 = i_of("EIC-G4")
if not (g4.get("eic_ban_2yr") or g4.get("eic_ban_10yr")):
    err("EIC-G4: fixture does not set a §32(k) ban for D_EIC_009")
if not i_of("EIC-G5").get("eic_clergy_church_statutory"):
    err("EIC-G5: fixture does not set eic_clergy_church_statutory for D_EIC_015")


# ═══════════════════════════════════════════════════════════════════════════
# Load-bearing checks on the flow assertions
# ═══════════════════════════════════════════════════════════════════════════

# FA-1040-EIC-02 constants_check must equal this checker's independent tables.
fa02 = next((a for a in m.FLOW_ASSERTIONS if a["assertion_id"] == "FA-1040-EIC-02"), None)
if fa02:
    c = fa02["definition"]["constants"]
    for year in (2025, 2026):
        ystr = str(year)
        if ystr not in c:
            err(f"FA-02 missing year {year}")
            continue
        for key in ("earned_income_amount", "max_credit", "threshold_mfj", "completed_mfj",
                    "threshold_other", "completed_other"):
            for col in ("0", "1", "2", "3+"):
                if D(c[ystr][key][col]) != D(IND_PARAMS[year][key][col]):
                    err(f"FA-02 [{year}][{key}][{col}]={c[ystr][key][col]} != independent {IND_PARAMS[year][key][col]}")
        if D(c[ystr]["investment_income_limit"]) != D(IND_PARAMS[year]["investment_income_limit"]):
            err(f"FA-02 [{year}] investment_income_limit mismatch")
    if c.get("applies_to_years") != [2025, 2026]:
        err(f"FA-02 applies_to_years {c.get('applies_to_years')} != [2025, 2026]")
else:
    err("FA-1040-EIC-02 (constants_check) not found")

# FA-1040-EIC-06 childless age band matches the independent constants.
fa06 = next((a for a in m.FLOW_ASSERTIONS if a["assertion_id"] == "FA-1040-EIC-06"), None)
if fa06:
    c = fa06["definition"]["constants"]
    if c.get("childless_age_min") != IND_CHILDLESS_AGE_MIN or c.get("childless_age_max_exclusive") != IND_CHILDLESS_AGE_MAX_EXCLUSIVE:
        err(f"FA-06 age band {c} != independent (25 / 65-exclusive)")
else:
    err("FA-1040-EIC-06 not found")

# FA-1040-EIC-08 column rule: QSS=other (NOT mfj), MFJ=mfj.
fa08 = next((a for a in m.FLOW_ASSERTIONS if a["assertion_id"] == "FA-1040-EIC-08"), None)
if fa08:
    cm = fa08["definition"]["constants"]["column_for_status"]
    if cm.get("qss") != "other":
        err(f"FA-08: QSS column should be 'other', got {cm.get('qss')}")
    if cm.get("mfj") != "mfj":
        err(f"FA-08: MFJ column should be 'mfj', got {cm.get('mfj')}")
    if status_key("qss") != "other" or status_key("mfj") != "mfj":
        err("FA-08: independent status_key disagrees (QSS must map to 'other')")
else:
    err("FA-1040-EIC-08 not found")


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
print("Independently recomputed: EIC-T1..T10 (table lookup, lower-of rule, Step-5 + Worksheet-B "
      "earned income, year-keyed tables), EIC-G1..G5 (RED-gate fixtures); §32 internal reconciliation "
      "both years; loader EIC_PARAMS cross-checked cell-by-cell vs an independent transcription.")

if errors:
    print("\nFAILURES:")
    for e in errors:
        print(f"  X {e}")
    sys.exit(1)
print("\nALL CHECKS PASS")
