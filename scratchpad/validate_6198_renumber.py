"""Throwaway-SQLite validation for the Form 6198 renumber (audit unit #6, 2026-07-12).

Checks: the renumbered fact/line/rule/diagnostic/scenario sets against the
Rev. November 2025 face (f6198.pdf, pymupdf-verified); stale fabricated rows
really deleted — runs the loader TWICE against a pre-polluted DB to prove the
self-heal; every rule has >= 1 authority link (links refresh-deleted, no stale
notes); arithmetic oracles from all seven scenarios including the three
published i6198 Line 21 examples and the p.3 Line 5 income-offset example;
the verbatim excerpt labels present and the paraphrase text gone; CharField
caps that SQLite ignores. ASCII-only prints.

Run: <rs-venv>/Scripts/python.exe scratchpad/validate_6198_renumber.py
"""
import os
import sys

PROJECT_ROOT = r"D:\dev\sherpa-tax-rule-studio"
sys.path.insert(0, PROJECT_ROOT)

SQLITE_PATH = os.path.join(PROJECT_ROOT, "scratchpad", "validate_6198.sqlite3")
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

# Stub the EXISTING_SOURCES codes (loaded by load_all_federal in prod).
from specs.management.commands.load_1120s_complete import EXISTING_SOURCES  # noqa: E402
for code in EXISTING_SOURCES:
    AuthoritySource.objects.get_or_create(
        source_code=code,
        defaults={"source_type": "statute", "source_rank": "primary_official",
                  "jurisdiction_code": "FED", "title": f"stub {code}",
                  "citation": code, "issuer": "IRS", "current_status": "active"})

# ── First seed run ──────────────────────────────────────────────────────────
call_command("load_1120s_complete", verbosity=0)

form = TaxForm.objects.get(form_number="6198", tax_year=2025)

# ── Pollute with the pre-renumber fabricated shapes, then re-run ────────────
FormFact.objects.get_or_create(tax_form=form, fact_key="cash_invested",
                               defaults={"label": "stale fabricated", "data_type": "decimal"})
FormFact.objects.get_or_create(tax_form=form, fact_key="allowable_loss",
                               defaults={"label": "stale output-as-fact", "data_type": "decimal"})
FormLine.objects.get_or_create(tax_form=form, line_number="2",
                               defaults={"description": "Prior year unallowed losses (FABRICATED)",
                                         "line_type": "input"})
FormLine.objects.get_or_create(tax_form=form, line_number="10",
                               defaults={"description": "stale pre-face row", "line_type": "input"})
FormRule.objects.get_or_create(tax_form=form, rule_id="R099",
                               defaults={"title": "stale rule", "rule_type": "validation",
                                         "formula": "x", "inputs": [], "outputs": []})
FormDiagnostic.objects.get_or_create(tax_form=form, diagnostic_id="D099",
                                     defaults={"title": "stale", "severity": "error",
                                               "condition": "x", "message": "stale"})
TestScenario.objects.get_or_create(tax_form=form, scenario_name="Standard at-risk — loss within amount",
                                   defaults={"scenario_type": "normal", "inputs": {},
                                             "expected_outputs": {}})

call_command("load_1120s_complete", verbosity=0)

# ── Line set == the Rev. 11-2025 face ───────────────────────────────────────
FACE_LINES = {"1", "2a", "2b", "2c", "3", "4", "5", "6", "7", "8", "9", "10a", "10b",
              "11", "12", "13", "14", "15", "16", "17", "18", "19a", "19b", "20", "21"}
got = set(FormLine.objects.filter(tax_form=form).values_list("line_number", flat=True))
check(got == FACE_LINES, "6198 line set == Rev. 11-2025 face (25 rows)",
      f"6198 line set mismatch: extra={sorted(got - FACE_LINES)} missing={sorted(FACE_LINES - got)}")

l5 = FormLine.objects.get(tax_form=form, line_number="5")
check("Combine lines 1 through 4" in l5.description, "L5 = combine 1-4 (face verbatim)",
      f"L5 wrong: {l5.description!r}")
l20 = FormLine.objects.get(tax_form=form, line_number="20")
check("larger of line 10b or line 19b" in l20.description, "L20 = larger of 10b/19b",
      f"L20 wrong: {l20.description!r}")
l21 = FormLine.objects.get(tax_form=form, line_number="21")
check("Deductible loss" in l21.description and "smaller of the line 5 loss" in l21.description,
      "L21 = deductible loss (smaller of L5-as-positive or L20)", f"L21 wrong: {l21.description!r}")
l15 = FormLine.objects.get(tax_form=form, line_number="15")
check("line 19b" in l15.description and "10b" in l15.description,
      "L15 carries the prior-year-19b-not-10b caution", f"L15 wrong: {l15.description!r}")
check(l21.line_type == "total", "L21 line_type = total", f"L21 line_type: {l21.line_type}")

# ── Fact set ────────────────────────────────────────────────────────────────
FACTS = {"activity_description", "ordinary_income_loss", "gain_loss_sched_d",
         "gain_loss_4797", "gain_loss_other_form", "other_form_label",
         "other_income_gains", "other_deductions_losses", "adjusted_basis_first_day",
         "increases_tax_year", "qualified_nonrecourse_financing", "decreases_tax_year",
         "investment_at_effective_date", "increases_at_effective_date",
         "decreases_at_effective_date", "line15_basis", "prior_year_line19b",
         "increases_since", "since_when_16", "decreases_since", "since_when_18"}
got_facts = set(FormFact.objects.filter(tax_form=form).values_list("fact_key", flat=True))
check(got_facts == FACTS, "6198 fact set == the 21 face-keyed facts (fabricated set gone)",
      f"6198 facts mismatch: extra={sorted(got_facts - FACTS)} missing={sorted(FACTS - got_facts)}")

for key in ("line15_basis", "since_when_16", "since_when_18"):
    f = FormFact.objects.get(tax_form=form, fact_key=key)
    check(f.data_type == "choice" and f.choices, f"{key} is a choice fact with choices",
          f"{key} data_type={f.data_type} choices={f.choices}")

# ── Rules R001-R009, all linked ─────────────────────────────────────────────
rules = {r.rule_id: r for r in FormRule.objects.filter(tax_form=form)}
check(set(rules) == {"R001", "R002", "R003", "R004", "R005", "R006", "R007", "R008", "R009"},
      "6198 rules R001-R009 present (stale R099 gone)", f"6198 rule set: {sorted(rules)}")
for rid, rule in sorted(rules.items()):
    n = RuleAuthorityLink.objects.filter(form_rule=rule).count()
    check(n >= 1, f"{rid} has {n} authority link(s)", f"{rid} has NO authority links")
check("max(line_10b, line_19b)" in rules["R004"].formula,
      "R004 formula = larger-of", f"R004 formula: {rules['R004'].formula!r}")
check("prior_year_line19b" in rules["R003"].formula and "line15_basis" in rules["R003"].formula,
      "R003 formula carries the L15 box a/b split", f"R003 formula: {rules['R003'].formula!r}")
check("-min(abs(line_5), line_20)" in rules["R005"].formula,
      "R005 formula = smaller-of, entered negative", f"R005 formula: {rules['R005'].formula!r}")
# No stale pre-renumber link notes survive the refresh-delete
stale_notes = RuleAuthorityLink.objects.filter(
    form_rule__tax_form=form, relevance_note="Form 6198 at-risk computation").count()
check(stale_notes == 0, "no stale pre-renumber link notes", f"{stale_notes} stale link notes survive")

# ── Diagnostics ─────────────────────────────────────────────────────────────
diags = set(FormDiagnostic.objects.filter(tax_form=form).values_list("diagnostic_id", flat=True))
check(diags == {"D001", "D002", "D003", "D004", "D005", "D006"},
      "6198 diagnostics D001-D006 (stale D099 gone)", f"6198 diag set: {sorted(diags)}")

# ── Scenarios: names + arithmetic oracles ───────────────────────────────────
scen = {t.scenario_name: t for t in TestScenario.objects.filter(tax_form=form)}
check(len(scen) == 7 and "Standard at-risk — loss within amount" not in scen,
      "7 scenarios; the old fabricated names deleted", f"scenarios: {sorted(scen)}")

def oracle_l21(line5, line20):
    return -min(abs(line5), line20) if line5 < 0 else None

# Published L21 examples (a)/(b)/(c)
for name, l5v, l20v, want in [
    ("L21 example (a) — loss within the amount at risk", -400, 1000, -400),
    ("L21 example (b) — loss capped at line 20", -1600, 1200, -1200),
    ("L21 example (c) — zero at risk", -800, 0, 0),
]:
    t = scen.get(name)
    if not t:
        check(False, "", f"missing scenario: {name}")
        continue
    got21 = t.expected_outputs.get("line_21")
    calc = oracle_l21(t.inputs["line_5"], t.inputs["line_20"])
    check(t.inputs["line_5"] == l5v and t.inputs["line_20"] == l20v and got21 == want == calc,
          f"published pin holds: {name} -> line_21 {want}",
          f"{name}: inputs {t.inputs} expected {t.expected_outputs} oracle {calc}")

# Line 5 income-offset example (i6198 p.3)
t = scen["Line 5 income-offset example (i6198 p.3)"]
l5_calc = t.inputs["ordinary_income_loss"] + t.inputs["gain_loss_sched_d"]
check(l5_calc == t.expected_outputs["line_5"] == -1500,
      "L5 example: -4600 + 3100 = -1500", f"L5 example mismatch: {l5_calc} vs {t.expected_outputs}")
check(oracle_l21(-1500, t.inputs["line_20"]) == t.expected_outputs["line_21"] == -600,
      "L5 example: line_21 = -600 (at-risk 600)", f"L5 example line_21: {t.expected_outputs}")
check(t.expected_outputs["total_loss_allowed"] == 3100 + 600 == 3700,
      "L5 example: total allowed 3,700 (3,100 offset + 600)", "L5 example total mismatch")

# Part II simplified
t = scen["Part II simplified computation"]
l8 = t.inputs["adjusted_basis_first_day"] + t.inputs["increases_tax_year"]
l10a = l8 - t.inputs["decreases_tax_year"]
l10b = max(0, l10a)
check(l8 == t.expected_outputs["line_8"] and l10a == t.expected_outputs["line_10a"]
      and l10b == t.expected_outputs["line_10b"] == t.expected_outputs["line_20"],
      "Part II oracle: 8=85000, 10a=75000, 10b=20=75000",
      f"Part II mismatch: l8={l8} l10a={l10a} l10b={l10b} vs {t.expected_outputs}")
check(oracle_l21(t.inputs["line_5"], l10b) == t.expected_outputs["line_21"] == -20000,
      "Part II oracle: line_21 = -20000 (fully allowed)", f"Part II line_21: {t.expected_outputs}")

# Part III detailed + larger-of
t = scen["Part III detailed + larger-of on line 20"]
l13 = t.inputs["investment_at_effective_date"] + t.inputs["increases_at_effective_date"]
l15v = max(0, l13 - t.inputs["decreases_at_effective_date"])
l17 = l15v + t.inputs["increases_since"]
l19a = l17 - t.inputs["decreases_since"]
l19b = max(0, l19a)
l20v = max(t.inputs["line_10b"], l19b)
check(l13 == t.expected_outputs["line_13"] and l15v == t.expected_outputs["line_15"]
      and l17 == t.expected_outputs["line_17"] and l19a == t.expected_outputs["line_19a"]
      and l19b == t.expected_outputs["line_19b"] and l20v == t.expected_outputs["line_20"] == 8500,
      "Part III oracle: 13=7000, 15=6000, 17=9000, 19a=19b=8500, 20=max(4000,8500)=8500",
      f"Part III mismatch: 13={l13} 15={l15v} 17={l17} 19a={l19a} 19b={l19b} 20={l20v} vs {t.expected_outputs}")
check(oracle_l21(t.inputs["line_5"], l20v) == t.expected_outputs["line_21"] == -8500
      and t.expected_outputs["suspended_465_carryover"] == 12000 - 8500,
      "Part III oracle: line_21 = -8500, suspended 3500", f"Part III tail: {t.expected_outputs}")

# QNF scenario
t = scen["Qualified nonrecourse real-estate financing at risk"]
l8 = t.inputs["adjusted_basis_first_day"] + t.inputs["increases_tax_year"]
check(l8 == 200000 == t.expected_outputs["line_10b"] == t.expected_outputs["line_20"]
      and oracle_l21(t.inputs["line_5"], 200000) == t.expected_outputs["line_21"] == -25000,
      "QNF oracle: 20000+180000=200000 at risk; -25000 fully allowed",
      f"QNF mismatch: l8={l8} vs {t.expected_outputs}")

# ── Excerpts: verbatim labels present, paraphrase text gone ─────────────────
src = AuthoritySource.objects.get(source_code="IRS_2025_6198_INSTR")
labels = set(AuthorityExcerpt.objects.filter(authority_source=src).values_list("excerpt_label", flat=True))
WANT_LABELS = {"At-risk computation",
               "Part I — prior year nondeductible amounts (verbatim)",
               "Qualified nonrecourse financing (verbatim)",
               "Line 15 — prior-year 19b caution (verbatim)",
               "Line 21 — deductible loss and examples (verbatim)",
               "Line 10b / Line 5 — Part III and recapture cautions (verbatim)"}
check(WANT_LABELS <= labels, "all 6 verbatim excerpt labels present",
      f"excerpt labels missing: {sorted(WANT_LABELS - labels)}")
atrisk = AuthorityExcerpt.objects.get(authority_source=src, excerpt_label="At-risk computation")
check("Use Form 6198 to figure" in atrisk.excerpt_text
      and "adjusted basis of property contributed + money contributed" not in atrisk.excerpt_text,
      "the 'At-risk computation' label now carries Purpose-of-Form verbatim (paraphrase gone)",
      "the paraphrase text survives under 'At-risk computation'")
check(src.citation == "Instructions for Form 6198 (Rev. November 2025)",
      "source citation updated to Rev. November 2025", f"citation: {src.citation!r}")

# ── CharField caps SQLite ignores ───────────────────────────────────────────
for f in FormFact.objects.filter(tax_form=form):
    check(len(f.fact_key) <= 100, f"fact_key len ok: {f.fact_key}",
          f"fact_key too long ({len(f.fact_key)}): {f.fact_key}")
    check(len(f.label) <= 255, f"label len ok: {f.fact_key}",
          f"label too long ({len(f.label)}): {f.fact_key}")
for ln in FormLine.objects.filter(tax_form=form):
    check(len(ln.line_number) <= 20, f"line_number len ok: {ln.line_number}",
          f"line_number too long: {ln.line_number}")
for r in FormRule.objects.filter(tax_form=form):
    check(len(r.rule_id) <= 20, f"rule_id len ok: {r.rule_id}", f"rule_id too long: {r.rule_id}")
    check(len(r.title) <= 255, f"rule title len ok: {r.rule_id}",
          f"rule title too long ({len(r.title)}): {r.rule_id}")
for d in FormDiagnostic.objects.filter(tax_form=form):
    check(len(d.diagnostic_id) <= 20, f"diagnostic_id len ok: {d.diagnostic_id}",
          f"diagnostic_id too long: {d.diagnostic_id}")
    check(len(d.title) <= 255, f"diag title len ok: {d.diagnostic_id}",
          f"diag title too long: {d.diagnostic_id}")
for t in TestScenario.objects.filter(tax_form=form):
    check(len(t.scenario_name) <= 255, f"scenario name len ok: {t.scenario_name[:40]}",
          f"scenario name too long: {t.scenario_name[:60]}")

# ── Report ──────────────────────────────────────────────────────────────────
print(f"\n{len(PASSES)} pass / {len(FAILURES)} fail")
if FAILURES:
    print("\nFAILURES:")
    for f in FAILURES:
        print("  FAIL:", f)
    sys.exit(1)
print("ALL CHECKS PASS")
