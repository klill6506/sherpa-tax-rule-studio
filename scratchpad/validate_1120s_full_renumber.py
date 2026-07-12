"""Throwaway-SQLite validation for the 1120S PAGE1 + M-1 + M-2 renumber (unit #5, 2026-07-12).

Checks: CharField caps; the renumbered fact/line/rule/diagnostic sets (stale rows
really deleted — runs the loader TWICE against a pre-polluted DB to prove the
self-heal); every rule has >= 1 authority link; arithmetic oracles from all the
scenarios (including the corrected M-2 R002 net-negative-adjustment cap against
the published i1120s pp.50-51 example and the divergence pin); the new verbatim
excerpt labels present + the fabricated/composite labels gone. ASCII-only prints.

Run: poetry run python scratchpad/validate_1120s_full_renumber.py
"""
import os
import sys

PROJECT_ROOT = r"D:\dev\sherpa-tax-rule-studio"
sys.path.insert(0, PROJECT_ROOT)

SQLITE_PATH = os.path.join(PROJECT_ROOT, "scratchpad", "validate_1120s_full.sqlite3")
if os.path.exists(SQLITE_PATH):
    os.remove(SQLITE_PATH)
os.environ["DATABASE_URL"] = f"sqlite:///{SQLITE_PATH}"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

import django  # noqa: E402
django.setup()

from django.core.management import call_command  # noqa: E402
from specs.models import (  # noqa: E402
    FormDiagnostic, FormFact, FormLine, FormRule, TaxForm, TestScenario,
)
from sources.models import AuthorityExcerpt, AuthoritySource, RuleAuthorityLink  # noqa: E402

FAILURES: list[str] = []
PASSES: list[str] = []


def check(cond, ok, bad):
    (PASSES if cond else FAILURES).append(ok if cond else bad)


call_command("migrate", run_syncdb=True, verbosity=0)

# Stub the EXISTING_SOURCES codes (loaded by load_all_federal in prod) so the
# rule->source links that target them are exercised here too.
from specs.management.commands.load_1120s_full import EXISTING_SOURCES  # noqa: E402
for code in EXISTING_SOURCES:
    AuthoritySource.objects.get_or_create(
        source_code=code,
        defaults={"source_type": "statute", "source_rank": "primary_official",
                  "jurisdiction_code": "FED", "title": f"stub {code}",
                  "citation": code, "issuer": "IRS", "current_status": "active"})

# ── First seed run ──────────────────────────────────────────────────────────
call_command("load_1120s_full", verbosity=0)

page1 = TaxForm.objects.get(form_number="1120S_PAGE1", tax_year=2025)
m1 = TaxForm.objects.get(form_number="1120S_M1", tax_year=2025)
m2 = TaxForm.objects.get(form_number="1120S_M2", tax_year=2025)

# ── Pollute with the pre-renumber stale shapes, then re-run to prove self-heal ─
FormFact.objects.get_or_create(tax_form=m1, fact_key="guaranteed_payments",
                               defaults={"label": "stale 1065 line", "data_type": "decimal"})
FormFact.objects.get_or_create(tax_form=m1, fact_key="line_6_subtotal",
                               defaults={"label": "stale renamed subtotal", "data_type": "decimal"})
FormFact.objects.get_or_create(tax_form=m2, fact_key="retained_earnings_beginning",
                               defaults={"label": "stale Sch L item", "data_type": "decimal"})
FormLine.objects.get_or_create(tax_form=m1, line_number="5b",
                               defaults={"description": "stale pre-face row", "line_type": "input"})
FormRule.objects.get_or_create(tax_form=m1, rule_id="R006",
                               defaults={"title": "stale guaranteed payments rule",
                                         "rule_type": "validation", "formula": "x",
                                         "inputs": [], "outputs": []})
FormDiagnostic.objects.get_or_create(tax_form=m1, diagnostic_id="D003",
                                     defaults={"title": "stale", "severity": "error",
                                               "condition": "x", "message": "stale"})
src = AuthoritySource.objects.get(source_code="IRS_2025_1120S_INSTR_FULL")
AuthorityExcerpt.objects.get_or_create(
    authority_source=src, excerpt_label="Schedule M-1 — Reconciliation of income per books with income per return",
    defaults={"excerpt_text": "stale fabricated"})
AuthorityExcerpt.objects.get_or_create(
    authority_source=src, excerpt_label="Page 1 Lines 7-20 — Deductions",
    defaults={"excerpt_text": "stale wrong numbering"})

call_command("load_1120s_full", verbosity=0)

# ── PAGE1 sets ──────────────────────────────────────────────────────────────
P1_LINES = {"1a", "1b", "1c", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11",
            "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22",
            "23a", "23b", "23c", "24a", "24b", "24c", "24d", "24z", "25", "26",
            "27", "28a", "28b", "28c", "28d", "28e"}
got = set(FormLine.objects.filter(tax_form=page1).values_list("line_number", flat=True))
check(got == P1_LINES, "PAGE1 line set == 2025 face (40 rows)",
      f"PAGE1 line set mismatch: extra={sorted(got - P1_LINES)} missing={sorted(P1_LINES - got)}")

l19 = FormLine.objects.get(tax_form=page1, line_number="19")
check("Energy efficient" in l19.description, "PAGE1 line 19 = Form 7205 deduction",
      f"PAGE1 line 19 wrong: {l19.description!r}")
l20 = FormLine.objects.get(tax_form=page1, line_number="20")
check("Other deductions" in l20.description, "PAGE1 line 20 = other deductions",
      f"PAGE1 line 20 wrong: {l20.description!r}")
l21 = FormLine.objects.get(tax_form=page1, line_number="21")
check("7 through 20" in l21.description, "PAGE1 line 21 = total deductions (add 7-20)",
      f"PAGE1 line 21 wrong: {l21.description!r}")
l22 = FormLine.objects.get(tax_form=page1, line_number="22")
check("Ordinary business income" in l22.description and "line 21" in l22.description,
      "PAGE1 line 22 = OBI (6 minus 21)", f"PAGE1 line 22 wrong: {l22.description!r}")

p1_rules = {r.rule_id: r for r in FormRule.objects.filter(tax_form=page1)}
check(set(p1_rules) == {"R001", "R002", "R003", "R004", "R005", "R006", "R007",
                          "R008", "R009", "R010", "R011", "R012", "R013", "R014", "R015"},
      "PAGE1 rules R001-R015 present", f"PAGE1 rule set: {sorted(p1_rules)}")
check("energy_efficient_bldg_ded" in p1_rules["R005"].formula,
      "R005 total-deductions formula includes line 19 (7205)",
      "R005 formula missing energy_efficient_bldg_ded")
check("Line 22" in p1_rules["R006"].description,
      "R006 OBI describes line 22", "R006 still references the old line 21")
check("Line 20" in p1_rules["R009"].title,
      "R009 meals tied to Line 20", f"R009 title: {p1_rules['R009'].title!r}")

p1_facts = set(FormFact.objects.filter(tax_form=page1).values_list("fact_key", flat=True))
for k in ["energy_efficient_bldg_ded", "excess_net_passive_tax", "schd_big_tax",
          "total_tax", "est_tax_payments", "form7004_deposit", "fuels_credit_4136",
          "elective_payment_3800", "total_payments", "est_tax_penalty",
          "form_2220_attached", "amount_owed", "overpayment", "credited_to_next_year",
          "refunded", "refund_routing_number", "refund_account_type", "refund_account_number"]:
    check(k in p1_facts, f"PAGE1 fact {k} present", f"PAGE1 fact {k} MISSING")

# ── PAGE1 arithmetic oracles ────────────────────────────────────────────────
def page1_compute(i):
    net_receipts = i.get("gross_receipts", 0) - i.get("returns_allowances", 0)
    gross_profit = net_receipts - i.get("cost_of_goods_sold", 0)
    # R003 routing: line 4 defaults from Form 4797 Part II line 17 when given.
    net_gain_4797 = i.get("net_gain_4797", i.get("form_4797_part2_line17", 0))
    total_income = gross_profit + net_gain_4797 + i.get("other_income", 0)
    meals_component = (1.00 * i.get("meals_100pct", 0) + 0.80 * i.get("meals_dot_80pct", 0)
                       + 0.50 * i.get("meals_50pct", 0))
    total_deductions = meals_component + sum(i.get(k, 0) for k in [
        "officer_compensation", "salaries_wages", "repairs_maintenance", "bad_debts",
        "rents", "taxes_licenses", "interest", "depreciation", "depletion",
        "advertising", "pension_plans", "employee_benefits",
        "energy_efficient_bldg_ded", "other_deductions"])
    obi = total_income - total_deductions
    total_tax = i.get("excess_net_passive_tax", 0) + i.get("schd_big_tax", 0)
    total_payments = (i.get("est_tax_payments", 0) + i.get("form7004_deposit", 0)
                      + i.get("fuels_credit_4136", 0) + i.get("elective_payment_3800", 0))
    owed = max(0, total_tax + i.get("est_tax_penalty", 0) - total_payments)
    over = max(0, total_payments - total_tax - i.get("est_tax_penalty", 0))
    refunded = over - i.get("credited_to_next_year", 0)
    meals_ded = (1.00 * i.get("meals_100pct", 0) + 0.80 * i.get("meals_dot_80pct", 0)
                 + 0.50 * i.get("meals_50pct", 0))
    meals_nonded = (0.50 * i.get("meals_50pct", 0) + 0.20 * i.get("meals_dot_80pct", 0)
                    + 1.00 * i.get("entertainment_0pct", 0))
    return {"net_receipts": net_receipts, "gross_profit": gross_profit,
            "total_income": total_income, "total_deductions": total_deductions,
            "ordinary_business_income": obi, "total_tax": total_tax,
            "total_payments": total_payments, "amount_owed": owed, "overpayment": over,
            "refunded": refunded, "meals_deductible_total": meals_ded,
            "meals_nondeductible_total": meals_nonded}

ORACLE_SCOPE_P1 = {"net_receipts", "gross_profit", "total_income", "total_deductions",
                   "ordinary_business_income", "total_tax", "total_payments",
                   "amount_owed", "overpayment", "refunded",
                   "meals_deductible_total", "meals_nondeductible_total"}
for sc in TestScenario.objects.filter(tax_form=page1):
    computed = page1_compute(sc.inputs)
    for key, want in sc.expected_outputs.items():
        if key not in ORACLE_SCOPE_P1:
            continue
        got_v = computed[key]
        check(abs(got_v - want) < 0.01,
              f"PAGE1 oracle [{sc.scenario_name[:40]}] {key} = {want}",
              f"PAGE1 oracle [{sc.scenario_name[:40]}] {key}: spec {want} vs computed {got_v}")

# ── M-1 sets ────────────────────────────────────────────────────────────────
M1_LINES = {"1", "2", "3", "3a", "3b", "4", "5", "5a", "6", "6a", "7", "8"}
got = set(FormLine.objects.filter(tax_form=m1).values_list("line_number", flat=True))
check(got == M1_LINES, "M-1 line set == 2025 face (incl. 3/3a/3b/5/5a/6/6a; 5b gone)",
      f"M-1 line set mismatch: extra={sorted(got - M1_LINES)} missing={sorted(M1_LINES - got)}")

m1_3a = FormLine.objects.get(tax_form=m1, line_number="3a")
check("Depreciation" in m1_3a.description, "M-1 3a = Depreciation (not guaranteed payments)",
      f"M-1 3a wrong: {m1_3a.description!r}")
m1_8 = FormLine.objects.get(tax_form=m1, line_number="8")
check("Schedule K, line 18" in m1_8.description, "M-1 line 8 ties Schedule K line 18",
      f"M-1 line 8 wrong: {m1_8.description!r}")

m1_facts = set(FormFact.objects.filter(tax_form=m1).values_list("fact_key", flat=True))
check("guaranteed_payments" not in m1_facts, "M-1 guaranteed_payments fact DELETED",
      "M-1 guaranteed_payments fact still present")
check("line_6_subtotal" not in m1_facts, "M-1 line_6_subtotal fact DELETED (renamed line_7_subtotal)",
      "M-1 line_6_subtotal fact still present")
check("line_7_subtotal" in m1_facts and "m1_3a_depreciation" in m1_facts
      and "m1_3b_travel_ent" in m1_facts and "m1_5a_tax_exempt_interest" in m1_facts
      and "m1_6a_depreciation" in m1_facts,
      "M-1 new face facts present", f"M-1 facts: {sorted(m1_facts)}")

m1_rules = set(FormRule.objects.filter(tax_form=m1).values_list("rule_id", flat=True))
check(m1_rules == {"R001", "R002", "R003", "R004", "R005", "R007", "R008"},
      "M-1 rule set (R006 guaranteed-payments deleted; R007/R008 added)",
      f"M-1 rules: {sorted(m1_rules)}")
m1_r004 = FormRule.objects.get(tax_form=m1, rule_id="R004")
check("schedule_k_line_18" in m1_r004.formula and "21" not in m1_r004.formula,
      "M-1 R004 balance check ties K18 (not page-1)", f"R004 formula: {m1_r004.formula!r}")

m1_diags = set(FormDiagnostic.objects.filter(tax_form=m1).values_list("diagnostic_id", flat=True))
check(m1_diags == {"D001", "D002", "D004", "D005"},
      "M-1 diagnostic set (D003 guaranteed-payments deleted)", f"M-1 diags: {sorted(m1_diags)}")

def m1_compute(i):
    l4 = i.get("book_net_income", 0) + i.get("income_on_k_not_books", 0) + i.get("expenses_not_on_k", 0)
    l7 = i.get("income_on_books_not_k", 0) + i.get("deductions_on_k_not_books", 0)
    return {"line_4_subtotal": l4, "line_7_subtotal": l7, "income_per_return": l4 - l7}

for sc in TestScenario.objects.filter(tax_form=m1):
    computed = m1_compute(sc.inputs)
    for key, want in sc.expected_outputs.items():
        check(computed[key] == want,
              f"M-1 oracle [{sc.scenario_name[:40]}] {key} = {want}",
              f"M-1 oracle [{sc.scenario_name[:40]}] {key}: spec {want} vs computed {computed[key]}")

# ── M-2 sets ────────────────────────────────────────────────────────────────
m2_facts = set(FormFact.objects.filter(tax_form=m2).values_list("fact_key", flat=True))
check("retained_earnings_beginning" not in m2_facts, "M-2 retained_earnings fact DELETED",
      "M-2 retained_earnings_beginning still present")
for k in ["ptep_beginning", "ptep_distributions", "ptep_ending", "aep_beginning",
          "aep_dividend_distributions", "aep_other_adjustments", "aep_ending"]:
    check(k in m2_facts, f"M-2 fact {k} present", f"M-2 fact {k} MISSING")

m2_l2 = FormLine.objects.get(tax_form=m2, line_number="2")
check("line 22" in m2_l2.description, "M-2 line 2 ties page 1 line 22",
      f"M-2 line 2 wrong: {m2_l2.description!r}")
m2_l4 = FormLine.objects.get(tax_form=m2, line_number="4")
check("line 22" in m2_l4.description, "M-2 line 4 ties page 1 line 22",
      f"M-2 line 4 wrong: {m2_l4.description!r}")

m2_rules = set(FormRule.objects.filter(tax_form=m2).values_list("rule_id", flat=True))
check(m2_rules == {"R001", "R002", "R003", "R004", "R005", "R006", "R007"},
      "M-2 rules R001-R007 present", f"M-2 rules: {sorted(m2_rules)}")

def m2_compute(i):
    inc = i.get("aaa_ordinary_income", 0) + i.get("aaa_other_additions", 0)
    dec = i.get("aaa_loss", 0) + i.get("aaa_other_reductions", 0)
    combined = i.get("aaa_beginning", 0) + inc - dec
    cap = max(0, i.get("aaa_beginning", 0) + max(0, inc - dec))
    charged = min(i.get("total_distributions", 0), cap)
    out = {"aaa_combined": combined, "aaa_distributions": charged,
           "aaa_ending": combined - charged}
    if "oaa_additions" in i or "oaa_beginning" in i:
        out["oaa_ending"] = (i.get("oaa_beginning", 0) + i.get("oaa_additions", 0)
                             - i.get("oaa_reductions", 0) - i.get("oaa_distributions", 0))
    return out

for sc in TestScenario.objects.filter(tax_form=m2):
    computed = m2_compute(sc.inputs)
    for key, want in sc.expected_outputs.items():
        check(computed.get(key) == want,
              f"M-2 oracle [{sc.scenario_name[:40]}] {key} = {want}",
              f"M-2 oracle [{sc.scenario_name[:40]}] {key}: spec {want} vs computed {computed.get(key)}")

# The published-example sanity anchor, independent of the scenario table:
pub = m2_compute({"aaa_beginning": 0, "aaa_ordinary_income": 10000,
                  "aaa_other_additions": 20000, "aaa_loss": 0,
                  "aaa_other_reductions": 36000, "total_distributions": 65000})
check(pub == {"aaa_combined": -6000, "aaa_distributions": 0, "aaa_ending": -6000},
      "Published i1120s pp.50-51 example reproduces ((6,000)/0/(6,000))",
      f"Published example mismatch: {pub}")
div = m2_compute({"aaa_beginning": 10000, "aaa_ordinary_income": 10000,
                  "aaa_other_additions": 20000, "aaa_loss": 0,
                  "aaa_other_reductions": 36000, "total_distributions": 65000})
check(div == {"aaa_combined": 4000, "aaa_distributions": 10000, "aaa_ending": -6000},
      "R002-correction divergence pin (cap 10,000 not 4,000)",
      f"Divergence pin mismatch: {div}")
old_cap_charged = min(65000, max(0, div["aaa_combined"]))
check(old_cap_charged == 4000 and old_cap_charged != div["aaa_distributions"],
      "Old formula provably diverges on the pin (4,000 vs 10,000)",
      "Old formula did not diverge — pin is not a real correction case")

# ── Authority links: every rebuilt rule cited ───────────────────────────────
for form, name in [(page1, "PAGE1"), (m1, "M-1"), (m2, "M-2")]:
    uncited = [r.rule_id for r in FormRule.objects.filter(tax_form=form)
               if not RuleAuthorityLink.objects.filter(form_rule=r).exists()]
    check(not uncited, f"{name}: every rule has >= 1 authority link",
          f"{name}: uncited rules {uncited}")

# ── Excerpts: new labels present, fabricated/composite labels gone ──────────
NEW_LABELS = [
    "Page 1 face — Income lines 1a-6 (2025)",
    "Page 1 face — Deductions lines 7-22 (2025)",
    "Page 1 face — Tax and Payments lines 23a-28e (2025)",
    "Line 19 instruction — Energy Efficient Commercial Buildings Deduction (2025)",
    "Line 20 instruction — Other Deductions (2025)",
    "Line 20 Special Rules — Travel, meals, and entertainment (2025)",
    "Line 22 instruction — Ordinary Business Income (Loss) (2025)",
    "Line 23b/23c instructions — BIG tax + additional taxes (2025)",
    "Line 24d instruction — Elective Payment Election from Form 3800 (2025)",
    "Lines 25-28a instructions — penalty, owed, overpayment, credited (2025)",
    "Schedule M-1 face rows (2025)",
    "Schedule M-1 applicability — B Q11 / $10M M-3 / 2025 partial option (2025)",
    "Schedule M-1 Line 2 + Line 3b + 16f tip instructions (2025)",
    "Schedule M-2 face rows and four columns (2025)",
    "M-2 Column (a) AAA — year-end adjustment order (2025)",
    "M-2 Columns (b) PTEP and (c) AE&P (2025)",
    "M-2 Column (d) OAA + AE&P adjustments (2025)",
    "M-2 Distributions — general ordering rule (2025)",
    "M-2 worksheet example — published figures (2025)",
]
STALE_LABELS = [
    "Page 1 Lines 1-6 — Income computation",
    "Page 1 Lines 7-20 — Deductions",
    "Line 19 Special Rules — Travel, meals, and entertainment (fetched 2026-07-09)",
    "Page 1 Line 21 — Ordinary business income (loss)",
    "Schedule K — Line sources and separately stated items",
    "Schedule M-1 — Reconciliation of income per books with income per return",
    "Schedule M-2 — Analysis of AAA, OAA, PTEP, and AE&P",
    "4797 flow — bypasses Schedule D",
]
for lbl in NEW_LABELS:
    check(AuthorityExcerpt.objects.filter(authority_source=src, excerpt_label=lbl).exists(),
          f"excerpt present: {lbl[:60]}", f"excerpt MISSING: {lbl}")
for lbl in STALE_LABELS:
    check(not AuthorityExcerpt.objects.filter(authority_source=src, excerpt_label=lbl).exists(),
          f"stale excerpt gone: {lbl[:60]}", f"stale excerpt SURVIVED: {lbl}")

# ── CharField caps ──────────────────────────────────────────────────────────
for form in (page1, m1, m2):
    for r in FormRule.objects.filter(tax_form=form):
        check(len(r.rule_id) <= 20, f"rule id cap ok {r.rule_id}", f"rule id too long: {r.rule_id}")
    for ln in FormLine.objects.filter(tax_form=form):
        check(len(ln.line_number) <= 20, f"line cap ok {ln.line_number}", f"line too long: {ln.line_number}")
    for d in FormDiagnostic.objects.filter(tax_form=form):
        check(len(d.diagnostic_id) <= 20, f"diag id cap ok {d.diagnostic_id}", f"diag id too long: {d.diagnostic_id}")
    for f in FormFact.objects.filter(tax_form=form):
        check(len(f.label) <= 255, f"fact label cap ok {f.fact_key}", f"fact label too long: {f.fact_key} ({len(f.label)})")

# ── Report ──────────────────────────────────────────────────────────────────
def _safe(t):
    return t.encode("ascii", errors="replace").decode("ascii")

print(f"\n{'=' * 70}\nPASS {len(PASSES)}  FAIL {len(FAILURES)}")
if FAILURES:
    print("\nFAILURES:")
    for f in FAILURES:
        print("  FAIL:", _safe(f))
    sys.exit(1)
print("ALL CHECKS PASS")
