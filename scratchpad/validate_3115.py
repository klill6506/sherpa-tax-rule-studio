"""Throwaway-SQLite validation for the Form 3115 loader (WO-23).

Checks CharField caps; every rule >= 1 authority link; rule_link coverage; logic oracles
(§481(a) spread engine, depreciation catch-up, Schedule A netting, DCN 7 routing); key
diagnostics; entity_types. ASCII-only. Run: poetry run python scratchpad/validate_3115.py
"""
import os
import sys

PROJECT_ROOT = r"D:\dev\sherpa-tax-rule-studio"
sys.path.insert(0, PROJECT_ROOT)

SQLITE_PATH = os.path.join(PROJECT_ROOT, "scratchpad", "validate_3115.sqlite3")
if os.path.exists(SQLITE_PATH):
    os.remove(SQLITE_PATH)
os.environ["DATABASE_URL"] = f"sqlite:///{SQLITE_PATH}"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

import django  # noqa: E402
django.setup()

from django.core.management import call_command  # noqa: E402
from specs.models import FlowAssertion, FormDiagnostic, FormFact, FormLine, FormRule, TaxForm  # noqa: E402
from sources.models import AuthorityTopic, RuleAuthorityLink  # noqa: E402
from specs.management.commands import load_3115 as L  # noqa: E402

FAILURES: list[str] = []
PASSES: list[str] = []


def check(cond, ok, bad):
    (PASSES if cond else FAILURES).append(ok if cond else bad)


call_command("migrate", run_syncdb=True, verbosity=0)
L.READY_TO_SEED = True
try:
    call_command("load_3115", verbosity=0)
    PASSES.append("load_3115 ran + seeded into SQLite without error")
except Exception as e:  # noqa: BLE001
    FAILURES.append(f"load_3115 raised: {e!r}")
    print("\n".join(FAILURES))
    sys.exit(1)

form = TaxForm.objects.get(form_number="3115")

# -- CharField caps --
CAPS: dict = {"form_number(50)": (form.form_number, 50)}
for r in FormRule.objects.filter(tax_form=form):
    CAPS[f"rule_id={r.rule_id}"] = (r.rule_id, 20)
for d in FormDiagnostic.objects.filter(tax_form=form):
    CAPS[f"diagnostic_id={d.diagnostic_id}"] = (d.diagnostic_id, 20)
for ln in FormLine.objects.filter(tax_form=form):
    CAPS[f"line_number={ln.line_number}"] = (ln.line_number, 20)
for fct in FormFact.objects.filter(tax_form=form):
    CAPS[f"fact_key={fct.fact_key}"] = (fct.fact_key, 100)
for fa in FlowAssertion.objects.filter(assertion_id__startswith="FA-3115"):
    CAPS[f"assertion_id={fa.assertion_id}"] = (fa.assertion_id, 20)
for t in AuthorityTopic.objects.all():
    CAPS[f"topic={t.topic_code}"] = (t.topic_name, 255)
viol = [f"{k}: len {len(v)} > {cap}" for k, (v, cap) in CAPS.items() if len(v) > cap]
check(not viol, f"CharField caps OK ({len(CAPS)} checked)", "CAP VIOLATIONS:\n    " + "\n    ".join(viol))

# -- authority links --
ruleless = [r.rule_id for r in FormRule.objects.filter(tax_form=form)
            if not RuleAuthorityLink.objects.filter(form_rule=r).exists()]
check(not ruleless, f"all {FormRule.objects.filter(tax_form=form).count()} rules have >= 1 authority link", f"ruleless: {ruleless}")
defined = {r["rule_id"] for r in L.F3115_RULES}
linked = {rl[0] for rl in L.F3115_RULE_LINKS}
check(not (linked - defined), "rule_links reference defined rules", f"orphan: {linked - defined}")
check(not (defined - linked), "every rule appears in rule_links", f"unlinked: {defined - linked}")

# -- depreciation catch-up oracle (DCN 7): §481(a) = taken - allowable --
check(L._depr_catch_up(8000, 72000) == -64000.0, "A: under-depreciated 8k vs 72k -> -64,000 (negative)", f"A catch-up wrong: {L._depr_catch_up(8000, 72000)}")
check(L._depr_catch_up(120000, 20000) == 100000.0, "B: over-depreciated 120k vs 20k -> +100,000 (positive)", f"B catch-up wrong: {L._depr_catch_up(120000, 20000)}")
check(L._depr_catch_up(50000, 50000) == 0.0, "even: taken == allowable -> 0", "even catch-up wrong")

# -- adjustment-period oracle --
check(L._adjustment_period(-64000) == 1, "A: negative -> 1 year", f"A period wrong: {L._adjustment_period(-64000)}")
check(L._adjustment_period(100000) == 4, "B: positive default -> 4 years", f"B period wrong: {L._adjustment_period(100000)}")
check(L._adjustment_period(40000, elect_de_minimis=True) == 1, "C: positive < 50k + de minimis -> 1 year", f"C period wrong: {L._adjustment_period(40000, elect_de_minimis=True)}")
check(L._adjustment_period(100000, is_under_examination=True) == 2, "D: positive under exam -> 2 years", f"D period wrong: {L._adjustment_period(100000, is_under_examination=True)}")
check(L._adjustment_period(60000, elect_de_minimis=True) == 4, "de minimis NOT available >= 50k -> 4 years", f"deminimis-cap wrong: {L._adjustment_period(60000, elect_de_minimis=True)}")
check(L._adjustment_period(0) == 1, "zero adjustment -> 1 year", "zero period wrong")
check(L._adjustment_period(40000, elect_de_minimis=True, is_under_examination=True) == 1, "de minimis precedence over under-exam", "deminimis-precedence wrong")

# -- ratable installments --
check(L._spread_installments(100000, 4) == [25000.0, 25000.0, 25000.0, 25000.0], "B: 100k / 4 -> 25k x4", f"B spread wrong: {L._spread_installments(100000, 4)}")
check(L._spread_installments(-64000, 1) == [-64000.0], "A: -64k / 1 -> [-64000]", f"A spread wrong: {L._spread_installments(-64000, 1)}")
check(L._spread_installments(100000, 2) == [50000.0, 50000.0], "D: 100k / 2 -> 50k x2", f"D spread wrong: {L._spread_installments(100000, 2)}")

# -- Schedule A cash->accrual netting --
check(L._schedule_a_net(ar=50000, inventory_deducted=80000, prepaid_deducted=10000, ap=20000) == 120000.0,
      "E: AR 50k + inv 80k + prepaid 10k - AP 20k -> +120,000", f"E Sch A wrong: {L._schedule_a_net(ar=50000, inventory_deducted=80000, prepaid_deducted=10000, ap=20000)}")
check(L._schedule_a_net(ap=30000) == -30000.0, "Sch A: AP-only -> -30,000 (decrease)", f"Sch A AP wrong: {L._schedule_a_net(ap=30000)}")
check(L._schedule_a_net(ar=10000, advance_payments=4000) == 6000.0, "Sch A: AR 10k - advance 4k -> +6,000", f"Sch A advance wrong: {L._schedule_a_net(ar=10000, advance_payments=4000)}")

# -- DCN routing --
check(L._dcn_for_change("automatic", "depreciation_amortization") == "7", "DCN: automatic depreciation -> 7", f"DCN wrong: {L._dcn_for_change('automatic', 'depreciation_amortization')}")
check(L._dcn_for_change("automatic", "overall_method") is None, "DCN: non-depreciation -> none (direct-entry)", "DCN overall wrong")
check(L._dcn_for_change("non_automatic", "depreciation_amortization") is None, "DCN: non-automatic -> none", "DCN non-auto wrong")

# -- constants --
check(L.DE_MINIMIS_THRESHOLD == 50000, "de minimis threshold $50,000", "de minimis const wrong")
check(L.POSITIVE_SPREAD_YEARS == 4 and L.NEGATIVE_SPREAD_YEARS == 1 and L.UNDER_EXAM_SPREAD_YEARS == 2, "spread constants 4/1/2", "spread const wrong")
check(L.DCN_DEPRECIATION_IMPERMISSIBLE == "7" and L.DCN7_MIN_IMPERMISSIBLE_YEARS == 2, "DCN 7 / >= 2 years", "DCN const wrong")

# -- key diagnostics + entity_types --
for did in ("D_3115_NEG_1YR", "D_3115_POS_SPREAD", "D_3115_DEMINIMIS", "D_3115_UNDEREXAM", "D_3115_5YEAR", "D_3115_CUTOFF", "D_3115_DCN7_2YR", "D_3115_USERFEE"):
    check(FormDiagnostic.objects.filter(tax_form=form, diagnostic_id=did).exists(), f"{did} present", f"{did} MISSING")
check(form.entity_types == ["1040", "1065", "1120", "1120S"], "entity_types = [1040,1065,1120,1120S]", f"entity_types wrong: {form.entity_types}")

# -- report --
print("\n" + "=" * 66)
print(f"  3115: facts {FormFact.objects.filter(tax_form=form).count()} / rules {FormRule.objects.filter(tax_form=form).count()} / "
      f"lines {FormLine.objects.filter(tax_form=form).count()} / diag {FormDiagnostic.objects.filter(tax_form=form).count()} / "
      f"tests {form.test_scenarios.count()} / FA {FlowAssertion.objects.filter(assertion_id__startswith='FA-3115').count()}")
print("=" * 66)
def _ascii(s):
    return str(s).encode("ascii", "replace").decode()
for p in PASSES:
    print("  PASS  " + _ascii(p))
for fbad in FAILURES:
    print("  FAIL  " + _ascii(fbad))
print("=" * 66)
print(f"RESULT: {len(PASSES)} pass / {len(FAILURES)} fail - {'ALL PASS' if not FAILURES else 'FAILURES PRESENT'}")

from django.db import connections  # noqa: E402
connections.close_all()
try:
    if os.path.exists(SQLITE_PATH):
        os.remove(SQLITE_PATH)
except OSError:
    pass
sys.exit(1 if FAILURES else 0)
