"""Pre-seed content checker for load_4562_section179_carryover (the §179 prior-year
carryover amendment to Form 4562 Part I).

Run:  poetry run python check_4562_section179_integrity.py

Mirrors check_schedule_f_integrity.py: validates the authored lists WITHOUT
touching the DB, then INDEPENDENTLY recomputes every numeric scenario from its OWN
transcription of the Form 4562 Part I carryover math (NOT imported from the loader):

    line_12 = min(line_9 + line_10, line_11)          # §179 expense deduction
    line_13 = (line_9 + line_10) - line_12            # carryover to next year

verified verbatim off the 2025 Form 4562 face (resources/irs_forms/2025/f4562.pdf):
    L12 "Section 179 expense deduction. Add lines 9 and 10, but don't enter more
         than line 11."
    L13 "Carryover of disallowed deduction to 2026. Add lines 9 and 10, less line 12."

This is the MATH GATE that must pass before Ken's review walk. Loader & gate share
no math. It also text-pins the loader rules/lines so a transcription error there
(e.g. reverting line 12 to the old wrong "smaller of line 9 or line 11") is caught.
"""
import os
import sys
from decimal import Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from specs.management.commands import load_4562_section179_carryover as m  # noqa: E402

errors: list[str] = []


def err(msg):
    errors.append(msg)


def D(x):
    return Decimal(str(x if x is not None else 0))


def check(name, got, want):
    if D(got) != D(want):
        err(f"{name}: recomputed {got} != authored {want}")


# ═══════════════════════════════════════════════════════════════════════════
# INDEPENDENT recomputation of the Form 4562 Part I carryover math
# (re-typed from the 2025 form face; NOT imported from the loader)
# ═══════════════════════════════════════════════════════════════════════════

def line_12(l9, l10, l11):
    """§179 expense deduction = add lines 9 and 10, capped at line 11."""
    return min(D(l9) + D(l10), D(l11))


def line_13(l9, l10, l12):
    """Carryover to next year = (line 9 + line 10) less line 12."""
    return (D(l9) + D(l10)) - D(l12)


# ═══════════════════════════════════════════════════════════════════════════
# Structural checks
# ═══════════════════════════════════════════════════════════════════════════

fact_keys = [f["fact_key"] for f in m.NEW_FACTS]
if len(fact_keys) != len(set(fact_keys)):
    err(f"duplicate fact keys {fact_keys}")
if "section_179_carryover_prior" not in fact_keys:
    err("NEW_FACTS missing section_179_carryover_prior (the line-10 carry field)")

rule_ids = [r["rule_id"] for r in m.RULES]
if len(rule_ids) != len(set(rule_ids)):
    err("duplicate rule ids")
for rid in ("R011", "R014", "R015"):
    if rid not in rule_ids:
        err(f"RULES missing {rid}")

line_nos = [str(ln["line_number"]) for ln in m.LINES]
if len(line_nos) != len(set(line_nos)):
    err(f"duplicate line numbers {line_nos}")
for lno in ("10", "11", "12", "13"):
    if lno not in line_nos:
        err(f"LINES missing line {lno}")

diag_ids = [d["diagnostic_id"] for d in m.DIAGNOSTICS]
if len(diag_ids) != len(set(diag_ids)):
    err("duplicate diagnostic ids")

# DB column caps: rule_id / diagnostic_id / line_number are varchar(20).
for did in diag_ids:
    if len(did) > 20:
        err(f"diagnostic_id too long (>20): {did}")
for rid in rule_ids:
    if len(rid) > 20:
        err(f"rule_id too long (>20): {rid}")
for lno in line_nos:
    if len(lno) > 20:
        err(f"line_number too long (>20): {lno}")
for f in m.NEW_FACTS:
    if len(f["fact_key"]) > 50:
        err(f"fact_key suspiciously long: {f['fact_key']}")

# every authored rule must be cited
linked = {rid for rid, *_ in m.RULE_LINKS}
uncited = [rid for rid in rule_ids if rid not in linked]
if uncited:
    err(f"uncited rules {uncited}")
dangling = [rid for rid in linked if rid not in rule_ids]
if dangling:
    err(f"rule_links reference rules not in this amendment {dangling}")

# choice facts need choices
for f in m.NEW_FACTS:
    if f.get("data_type") == "choice" and not f.get("choices"):
        err(f"fact {f['fact_key']}: choice type without choices")

# flow assertions
fa_ids = [a["assertion_id"] for a in m.FLOW_ASSERTIONS]
if len(fa_ids) != len(set(fa_ids)):
    err("duplicate flow assertion ids")
for a in m.FLOW_ASSERTIONS:
    if len(a["assertion_id"]) > 20:
        err(f"assertion_id too long (>20): {a['assertion_id']}")

# new excerpts target the existing 4562 instructions source
for code, exc in m.NEW_EXCERPTS_ON_EXISTING:
    if code != "IRS_2025_4562_INSTR_FULL":
        err(f"unexpected excerpt source {code} (expected IRS_2025_4562_INSTR_FULL)")
    if not exc.get("excerpt_text"):
        err(f"excerpt {exc.get('excerpt_label')} has no text")


# ═══════════════════════════════════════════════════════════════════════════
# Text-pins — guard against reverting the loader to the wrong line-12 formula
# ═══════════════════════════════════════════════════════════════════════════

rules_by_id = {r["rule_id"]: r for r in m.RULES}
lines_by_no = {str(ln["line_number"]): ln for ln in m.LINES}

# R014 (line 12) must ADD lines 9 and 10, cap at 11 — never "smaller of 9 or 11".
r14 = rules_by_id["R014"]["formula"].lower()
if not ("line_9" in r14 and "line_10" in r14 and "min(" in r14 and "line_11" in r14):
    err(f"R014 formula not 'min(L9+L10, L11)': {rules_by_id['R014']['formula']}")
# R015 (line 13) = (L9 + L10) - L12.
r15 = rules_by_id["R015"]["formula"].lower()
if not ("line_9" in r15 and "line_10" in r15 and "line_12" in r15 and "-" in r15):
    err(f"R015 formula not '(L9+L10) - L12': {rules_by_id['R015']['formula']}")

# Line 12 description must say "add lines 9 and 10" (the fix), NOT the old bug.
l12desc = lines_by_no["12"]["description"].lower()
if "add lines 9 and 10" not in l12desc:
    err(f"line 12 description does not say 'add lines 9 and 10': {lines_by_no['12']['description']}")
if "smaller of line 9 or line 11" in l12desc:
    err("line 12 still has the WRONG pre-amendment formula ('smaller of line 9 or line 11')")

# Line 11 (individuals) must reference wages / Form 1040 line 1a.
l11blob = (lines_by_no["11"]["description"] + " " + lines_by_no["11"].get("notes", "")).lower()
if "1a" not in l11blob and "wage" not in l11blob:
    err("line 11 does not reference W-2 wages / 1040 line 1a (the Individuals definition)")

# Line 10 must source the new carry fact.
if "section_179_carryover_prior" not in lines_by_no["10"].get("source_facts", []):
    err("line 10 does not source section_179_carryover_prior")


# ═══════════════════════════════════════════════════════════════════════════
# Scenario recomputation (every authored §179 carryover scenario)
# ═══════════════════════════════════════════════════════════════════════════

for sc in m.SCENARIOS:
    name = sc["scenario_name"]
    i, o = sc["inputs"], sc["expected_outputs"]
    l9 = D(i["line_9_tentative"])
    l10 = D(i["section_179_carryover_prior"])
    l11 = D(i["line_11_business_income_limit"])

    l12 = line_12(l9, l10, l11)
    l13 = line_13(l9, l10, l12)

    check(f"{name} :: L12", l12, o["section_179_expense_deduction"])
    check(f"{name} :: L13", l13, o["section_179_carryover_next"])

    # invariants (independent of the authored expected values)
    if l12 > l11:
        err(f"{name}: L12 {l12} exceeds the business income limit L11 {l11}")
    if l12 > l9 + l10:
        err(f"{name}: L12 {l12} exceeds L9+L10 {l9 + l10}")
    if l13 < 0:
        err(f"{name}: L13 {l13} is negative")
    if l12 + l13 != l9 + l10:
        err(f"{name}: L12+L13 {l12 + l13} != L9+L10 {l9 + l10} (carryover not conserved)")
    # zero prior carryover must reduce to the pre-amendment line 12 = min(L9, L11)
    if l10 == 0 and l12 != min(l9, l11):
        err(f"{name}: with no carryover L12 should equal min(L9, L11) — regression risk")

# at least one scenario must exercise a NONZERO carryover and an income-limited cap
if not any(D(sc["inputs"]["section_179_carryover_prior"]) > 0 for sc in m.SCENARIOS):
    err("no scenario exercises a nonzero §179 prior-year carryover")
if not any(
    D(sc["inputs"]["line_9_tentative"]) + D(sc["inputs"]["section_179_carryover_prior"])
    > D(sc["inputs"]["line_11_business_income_limit"])
    for sc in m.SCENARIOS
):
    err("no scenario exercises an income-limited carryover (L13 > 0)")


# ═══════════════════════════════════════════════════════════════════════════
# Report
# ═══════════════════════════════════════════════════════════════════════════

print("=" * 64)
if errors:
    print(f"FAIL — {len(errors)} issue(s):")
    for e in errors:
        print(f"  - {e}")
    print("=" * 64)
    sys.exit(1)
else:
    n = len(m.SCENARIOS)
    print(f"ALL CHECKS PASS — {n} §179 carryover scenarios recomputed; "
          "structure + text-pins + invariants green.")
    print("Form 4562 Part I: L12 = min(L9+L10, L11); L13 = (L9+L10) - L12.")
    print("=" * 64)
