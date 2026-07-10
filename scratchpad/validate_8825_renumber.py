"""Throwaway-SQLite validation for the 8825 Dec-2025 face renumber (2026-07-10).

Checks: CharField caps; the renumbered fact/line sets (stale rows really deleted —
runs the loader TWICE against a pre-polluted form to prove self-heal); R001-R007
present with >= 1 authority link each; arithmetic oracles from the 5 scenarios;
D001-D005; the 8 re-fetched excerpt labels. ASCII-only prints (cp1252 console).

Run: poetry run python scratchpad/validate_8825_renumber.py
"""
import os
import sys

PROJECT_ROOT = r"D:\dev\sherpa-tax-rule-studio"
sys.path.insert(0, PROJECT_ROOT)

SQLITE_PATH = os.path.join(PROJECT_ROOT, "scratchpad", "validate_8825.sqlite3")
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

# First seed run
call_command("load_remaining_1120s", verbosity=0)
form = TaxForm.objects.get(form_number="8825", tax_year=2025)

# Pollute with a fake stale row set (simulating the pre-renumber DB), then
# re-run the loader to prove the in-loader deletes self-heal.
FormFact.objects.get_or_create(tax_form=form, fact_key="property_address",
                               defaults={"label": "stale", "data_type": "string"})
FormLine.objects.get_or_create(tax_form=form, line_number="2",
                               defaults={"description": "stale bare-2 row", "line_type": "input"})
call_command("load_remaining_1120s", verbosity=0)

EXPECTED_FACTS = {
    "property_street", "property_city", "property_state", "property_zip",
    "property_type", "other_info_code", "fair_rental_days", "personal_use_days",
    "gross_rents", "other_rental_income", "total_property_income",
    "advertising", "auto_travel", "cleaning", "commissions", "insurance",
    "mortgage_interest", "other_interest", "legal_professional", "taxes",
    "repairs", "utilities", "wages_salaries", "depreciation", "other_expenses",
    "schedule_a_category", "total_expenses", "net_rent",
    "total_gross_rents", "total_expenses_all", "gain_4797_rental",
    "passthrough_net_rental", "passthrough_identities", "total_net_rental",
}
facts = set(FormFact.objects.filter(tax_form=form).values_list("fact_key", flat=True))
check(facts == EXPECTED_FACTS,
      f"fact set exact ({len(facts)})",
      f"fact set mismatch: extra={facts - EXPECTED_FACTS} missing={EXPECTED_FACTS - facts}")

EXPECTED_LINES = ({"1", "2a", "2b", "2c"} | {str(n) for n in range(3, 20)}
                  | {"20a", "20b", "21", "22a", "22b", "23"}
                  | {f"A{n}" for n in range(1, 32)})
lines = set(FormLine.objects.filter(tax_form=form).values_list("line_number", flat=True))
check(lines == EXPECTED_LINES,
      f"line set exact ({len(lines)} rows incl. Schedule A A1-A31)",
      f"line set mismatch: extra={lines - EXPECTED_LINES} missing={EXPECTED_LINES - lines}")
check("2" not in lines, "stale bare-2 line deleted", "stale bare-2 line SURVIVED")
check("property_address" not in facts, "stale property_address fact deleted",
      "stale property_address fact SURVIVED")

rules = {r.rule_id: r for r in FormRule.objects.filter(tax_form=form)}
check(set(rules) == {f"R00{i}" for i in range(1, 8)},
      "rules R001-R007 exact", f"rule set mismatch: {sorted(rules)}")
for rid, rule in rules.items():
    n = RuleAuthorityLink.objects.filter(form_rule=rule).count()
    check(n >= 1, f"{rid} has {n} authority link(s)", f"{rid} has NO authority link")

r3 = rules.get("R003")
check(r3 and "line_21" in r3.formula and "line_22a" in r3.formula,
      "R003 formula includes lines 21/22a (the corrected combine)",
      f"R003 formula wrong: {r3.formula if r3 else 'MISSING'}")
check(r3 and set(r3.inputs) == {"total_gross_rents", "total_expenses_all",
                                "gain_4797_rental", "passthrough_net_rental"},
      "R003 inputs = 20a/20b/21/22a facts", f"R003 inputs wrong: {r3.inputs if r3 else '-'}")

# Arithmetic oracles over the seeded scenarios
sc = {t.scenario_name: t for t in TestScenario.objects.filter(tax_form=form)}
check(len(sc) == 5, "5 scenarios seeded", f"scenario count {len(sc)}")

def _oracle_property(inputs):
    income = inputs.get("gross_rents", 0) + inputs.get("other_rental_income", 0)
    exp = sum(inputs.get(k, 0) for k in (
        "advertising", "auto_travel", "cleaning", "commissions", "insurance",
        "mortgage_interest", "other_interest", "legal_professional", "taxes",
        "repairs", "utilities", "wages_salaries", "depreciation", "other_expenses"))
    return income, exp, income - exp

for name in ("Single rental property — net income", "Net rental loss",
             "Line 2b other income + line 13 wages (new 12-2025 rows)"):
    t = sc.get(name)
    if not t:
        FAILURES.append(f"scenario missing: {name}")
        continue
    income, exp, net = _oracle_property(t.inputs)
    eo = t.expected_outputs
    ok = (eo.get("total_property_income") == income
          and eo.get("total_expenses") == exp and eo.get("net_rent") == net)
    check(ok, f"oracle ok: {name} (2c={income} 18={exp} 19={net})",
          f"oracle MISMATCH: {name} computed ({income},{exp},{net}) vs pinned {eo}")

t4 = sc.get("Line 23 combines 20a through 22a (21/22a included)")
if t4:
    i = t4.inputs
    line23 = (i["total_gross_rents"] - i["total_expenses_all"]
              + i["gain_4797_rental"] + i["passthrough_net_rental"])
    check(t4.expected_outputs.get("total_net_rental") == line23,
          f"oracle ok: line 23 combine = {line23}",
          f"oracle MISMATCH: line 23 {line23} vs pinned {t4.expected_outputs}")
else:
    FAILURES.append("scenario missing: line 23 combine")

t5 = sc.get("Schedule A detail rows total to line 17")
if t5:
    total = sum(r["amount"] for r in t5.inputs["schedule_a_rows"])
    check(t5.expected_outputs.get("schedule_a_total") == total
          and t5.expected_outputs.get("other_expenses") == total,
          f"oracle ok: Schedule A rows -> A31 = line 17 = {total}",
          f"oracle MISMATCH: Schedule A total {total} vs pinned {t5.expected_outputs}")
else:
    FAILURES.append("scenario missing: Schedule A rows")

diags = set(FormDiagnostic.objects.filter(tax_form=form).values_list("diagnostic_id", flat=True))
check(diags == {f"D00{i}" for i in range(1, 6)},
      "diagnostics D001-D005 exact", f"diagnostic set mismatch: {sorted(diags)}")

# Caps (SQLite ignores CharField max_length — enforce by hand)
for ln in lines:
    check(len(ln) <= 20, f"line_number cap ok: {ln}", f"line_number OVER CAP: {ln}")
for fk in facts:
    check(len(fk) <= 100, f"fact_key cap ok: {fk}", f"fact_key OVER CAP: {fk}")
for rid in rules:
    check(len(rid) <= 20, f"rule_id cap ok: {rid}", f"rule_id OVER CAP: {rid}")

# Re-fetched excerpts
src = AuthoritySource.objects.get(source_code="IRS_2025_8825_INSTR_FULL")
labels = set(AuthorityExcerpt.objects.filter(authority_source=src)
             .values_list("excerpt_label", flat=True))
check(len(labels) == 8, f"8 excerpts on the re-fetched source", f"excerpt labels: {sorted(labels)}")
check(not any("lines 3-15" in e for e in AuthorityExcerpt.objects.filter(
          authority_source=src).values_list("excerpt_text", flat=True)),
      "stale pre-2025 numbering excerpt gone", "stale 'lines 3-15' excerpt SURVIVED")
check("Rev. December 2025" in src.title or "December 2025" in src.title,
      "source title carries the Dec-2025 revision", f"source title stale: {src.title}")

print(f"\nPASS {len(PASSES)}  FAIL {len(FAILURES)}")
for f in FAILURES:
    print("FAIL:", f)
sys.exit(1 if FAILURES else 0)
