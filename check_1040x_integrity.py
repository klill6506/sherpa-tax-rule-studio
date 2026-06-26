"""Pre-seed math + structure gate for load_1040_form_1040x (Form 1040-X — the
amended-return three-column A/B/C delta).

Run:  <rs-venv>/Scripts/python.exe check_1040x_integrity.py

Independently re-derives every scenario from its OWN transcription of the 1040-X
mechanics — column B = column C − column A per line, the subtotals (lines 3/5/8/
11), and the amended refund-due / amount-owed (lines 17/19/20/21) — and runs
structural checks (no duplicate ids; scenario expected_outputs reference real
lines; rule_links reference real rules + sources; flow-assertion ids unique). The
loader carries only the authored scenarios; this gate re-derives them from scratch
(no shared math). It verifies the AUTHORED spec is internally consistent BEFORE
Ken's review — READY_TO_SEED stays False regardless.
"""
import os
from decimal import Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_1040_form_1040x as m  # noqa: E402

errors: list[str] = []
ZERO = Decimal(0)


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def check(label, got, want):
    if D(got) != D(want):
        err(f"{label}: got {got}, want {want}")


# ── Independent recompute of the 1040-X delta + recompute (no shared math) ──

def recompute(inp: dict) -> dict:
    """Re-derive the computed 1040-X lines from the scenario's A/C leaf inputs."""
    def g(k):
        return D(inp.get(k))

    out: dict = {}

    # Column B = column C − column A on every A/B/C line present in inputs.
    for base in ("1", "2", "4a", "4b", "6", "7", "10", "12", "13", "14", "15", "25", "27"):
        if f"{base}A" in inp or f"{base}C" in inp:
            out[f"{base}B"] = g(f"{base}C") - g(f"{base}A")

    # Subtotals, per column.
    for col in ("A", "B", "C"):
        out[f"3{col}"] = g(f"1{col}") - g(f"2{col}") if (f"1{col}" in inp or f"2{col}" in inp) else None
    # line 3 B can also be derived as 3C - 3A; recompute B from C - A for consistency
    if out.get("3A") is not None and out.get("3C") is not None:
        out["3B"] = out["3C"] - out["3A"]

    for col in ("A", "C"):
        l3 = g(f"3{col}") if f"3{col}" not in out or out[f"3{col}"] is None else out[f"3{col}"]
        ti = l3 - (g(f"4a{col}") + g(f"4b{col}"))
        if col == "C":
            ti = max(ZERO, ti)        # column C taxable income floored at -0-
        out[f"5{col}"] = ti
    if "5A" in out and "5C" in out:
        out["5B"] = out["5C"] - out["5A"]

    for col in ("A", "C"):
        out[f"8{col}"] = max(ZERO, g(f"6{col}") - g(f"7{col}"))
    if "8A" in out and "8C" in out:
        out["8B"] = out["8C"] - out["8A"]

    for col in ("A", "C"):
        out[f"11{col}"] = out.get(f"8{col}", ZERO) + g(f"10{col}")
    if "11A" in out and "11C" in out:
        out["11B"] = out["11C"] - out["11A"]

    # Payments → refund/owe (single column).
    l17 = g("12C") + g("13C") + g("14C") + g("15C") + g("x_amount_paid_with_original")
    out["17"] = l17
    l19 = l17 - g("x_overpayment_on_original")
    out["19"] = l19
    l11c = out.get("11C", ZERO)
    out["20"] = max(ZERO, l11c - l19)   # amount you owe
    out["21"] = max(ZERO, l19 - l11c)   # overpayment on this return

    # drop the None placeholders
    return {k: v for k, v in out.items() if v is not None}


# ── 1. Scenario recompute (independent) ──
spec = m.FORMS[0]
for s in spec["scenarios"]:
    name = s["scenario_name"].split(" ")[0]
    got = recompute(s["inputs"])
    for k, want in s["expected_outputs"].items():
        if want is None:
            continue
        if k not in got:
            err(f"{name}: expected key '{k}' not produced by recompute (authored {want})")
            continue
        check(f"{name}.{k}", got[k], want)

# ── 2. Structural integrity ──
def _dups(ids):
    seen, dups = set(), set()
    for i in ids:
        if i in seen:
            dups.add(i)
        seen.add(i)
    return dups

line_ids = [ln["line_number"] for ln in spec["lines"]]
if _dups(line_ids):
    err(f"duplicate line_numbers: {_dups(line_ids)}")
rule_ids = [r["rule_id"] for r in spec["rules"]]
if _dups(rule_ids):
    err(f"duplicate rule_ids: {_dups(rule_ids)}")
diag_ids = [d["diagnostic_id"] for d in spec["diagnostics"]]
if _dups(diag_ids):
    err(f"duplicate diagnostic_ids: {_dups(diag_ids)}")
fact_keys = [f["fact_key"] for f in spec["facts"]]
if _dups(fact_keys):
    err(f"duplicate fact_keys: {_dups(fact_keys)}")
fa_ids = [a["assertion_id"] for a in m.FLOW_ASSERTIONS]
if _dups(fa_ids):
    err(f"duplicate flow-assertion ids: {_dups(fa_ids)}")

# id-length cap (RS varchar(20) on rule_id / diagnostic_id / line_number)
for label, ids in (("rule_id", rule_ids), ("diagnostic_id", diag_ids), ("line_number", line_ids)):
    too_long = [i for i in ids if len(i) > 20]
    if too_long:
        err(f"{label} over 20 chars (RS varchar cap): {too_long}")

# rule_links must reference real rules + real sources
source_codes = {s["source_code"] for s in m.AUTHORITY_SOURCES} | set(m.EXISTING_SOURCES_TO_REFERENCE)
for rid, scode, _level, _note in spec["rule_links"]:
    if rid not in rule_ids:
        err(f"rule_link references unknown rule {rid}")
    if scode not in source_codes:
        err(f"rule_link references unknown source {scode}")

# every authored rule has at least one authority link
linked_rules = {rid for rid, *_ in spec["rule_links"]}
for rid in rule_ids:
    if rid not in linked_rules:
        err(f"rule {rid} has no authority link")

# scenario expected_outputs reference real lines (ignore facts)
line_set = set(line_ids)
for s in spec["scenarios"]:
    for k in s["expected_outputs"]:
        if k not in line_set and not k.startswith("x_"):
            err(f"scenario {s['scenario_name'].split(' ')[0]}: expected key '{k}' is not a real line")

# every fact referenced in rule.inputs exists
for r in spec["rules"]:
    for fk in r.get("inputs", []):
        if fk.startswith("x_") and fk not in fact_keys:
            err(f"rule {r['rule_id']} references unknown fact {fk}")

# READY_TO_SEED flipped True 2026-06-25 after Ken's W1-W6 review approval — the
# spec is now seeded + the compute leg builds against it.


# ── Report ──
if errors:
    print(f"\n1040-X INTEGRITY GATE: {len(errors)} FAILURE(S)\n")
    for e in errors:
        print(f"  [X] {e}")
    raise SystemExit(1)
print("\n1040-X INTEGRITY GATE: ALL CHECKS PASS")
print(f"  {len(spec['scenarios'])} scenarios re-derived (delta B=C-A + subtotals "
      f"3/5/8/11 + refund/owe 17/19/20/21); structure clean "
      f"({len(spec['facts'])} facts / {len(spec['rules'])} rules / {len(spec['lines'])} lines / "
      f"{len(spec['diagnostics'])} diagnostics / {len(m.FLOW_ASSERTIONS)} FA). "
      f"READY_TO_SEED={m.READY_TO_SEED} (approved 2026-06-25).")
