"""Throwaway-SQLite validation for the Form 8379 loader (WO-18).

Checks CharField caps; every rule >= 1 authority link; rule_link coverage; logic oracles
(Part I decision tree -> is_injured_spouse + reason; Part III col a = b + c; std deduction 50/50;
community-property states); key diagnostics; entity_types. ASCII-only. Run: poetry run python scratchpad/validate_8379.py
"""
import os
import sys

PROJECT_ROOT = r"D:\dev\sherpa-tax-rule-studio"
sys.path.insert(0, PROJECT_ROOT)

SQLITE_PATH = os.path.join(PROJECT_ROOT, "scratchpad", "validate_8379.sqlite3")
if os.path.exists(SQLITE_PATH):
    os.remove(SQLITE_PATH)
os.environ["DATABASE_URL"] = f"sqlite:///{SQLITE_PATH}"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

import django  # noqa: E402
django.setup()

from django.core.management import call_command  # noqa: E402
from specs.models import FlowAssertion, FormDiagnostic, FormFact, FormLine, FormRule, TaxForm  # noqa: E402
from sources.models import AuthorityTopic, RuleAuthorityLink  # noqa: E402
from specs.management.commands import load_8379 as L  # noqa: E402

FAILURES: list[str] = []
PASSES: list[str] = []


def check(cond, ok, bad):
    (PASSES if cond else FAILURES).append(ok if cond else bad)


call_command("migrate", run_syncdb=True, verbosity=0)
L.READY_TO_SEED = True
try:
    call_command("load_8379", verbosity=0)
    PASSES.append("load_8379 ran + seeded into SQLite without error")
except Exception as e:  # noqa: BLE001
    FAILURES.append(f"load_8379 raised: {e!r}")
    print("\n".join(FAILURES))
    sys.exit(1)

form = TaxForm.objects.get(form_number="8379")

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
for fa in FlowAssertion.objects.filter(assertion_id__startswith="FA-8379"):
    CAPS[f"assertion_id={fa.assertion_id}"] = (fa.assertion_id, 20)
for t in AuthorityTopic.objects.all():
    CAPS[f"topic={t.topic_code}"] = (t.topic_name, 255)
viol = [f"{k}: len {len(v)} > {cap}" for k, (v, cap) in CAPS.items() if len(v) > cap]
check(not viol, f"CharField caps OK ({len(CAPS)} checked)", "CAP VIOLATIONS:\n    " + "\n    ".join(viol))

# -- authority links --
ruleless = [r.rule_id for r in FormRule.objects.filter(tax_form=form)
            if not RuleAuthorityLink.objects.filter(form_rule=r).exists()]
check(not ruleless, f"all {FormRule.objects.filter(tax_form=form).count()} rules have >= 1 authority link", f"ruleless: {ruleless}")
defined = {r["rule_id"] for r in L.F8379_RULES}
linked = {rl[0] for rl in L.F8379_RULE_LINKS}
check(not (linked - defined), "rule_links reference defined rules", f"orphan: {linked - defined}")
check(not (defined - linked), "every rule appears in rule_links", f"unlinked: {defined - linked}")

# -- logic oracles: Part I decision tree --
# A: qualifies via payments
check(L._is_injured_spouse(True, True, False, False, True, False, False) == (True, "made_payments"), "A: joint+spouse-debt+not-obligated+payments -> injured (made_payments)", "A wrong")
# B: legally obligated
check(L._is_injured_spouse(True, True, True, False, True, False, False) == (False, "legally_obligated"), "B: legally obligated -> not injured (legally_obligated)", "B wrong")
# C: debt not spouse-only
check(L._is_injured_spouse(True, False, False, True, True, True, True) == (False, "debt_not_spouse_only"), "C: debt not spouse-only -> not injured", "C wrong")
# D: community property (skip L6-9)
check(L._is_injured_spouse(True, True, False, True, False, False, False) == (True, "community_property"), "D: community-property resident -> injured (community_property)", "D wrong")
# not joint
check(L._is_injured_spouse(False, True, False, True, True, True, True) == (False, "not_joint"), "not-joint -> not injured", "not-joint wrong")
# G: no qualifying path
check(L._is_injured_spouse(True, True, False, False, False, False, False) == (False, "no_qualifying_path"), "G: no qualifying path -> not injured", "G wrong")
# qualifies via EIC/ACTC and via other refundable credit
check(L._is_injured_spouse(True, True, False, False, False, True, False) == (True, "eic_actc"), "qualify via EIC/ACTC", "eic_actc wrong")
check(L._is_injured_spouse(True, True, False, False, False, False, True) == (True, "refundable_credit"), "qualify via other refundable credit", "refundable_credit wrong")

# -- Part III allocation constraint --
check(L._allocation_balances(60000, 40000, 20000) is True, "E: 60,000 = 40,000 + 20,000 balances", "E balance wrong")
check(L._allocation_balances(8000, 5000, 3000) is True, "E: withholding 8,000 = 5,000 + 3,000 balances", "E wh wrong")
check(L._allocation_balances(60000, 40000, 15000) is False, "F: 60,000 != 40,000 + 15,000 -> imbalance", "F imbalance wrong")
check(L._std_deduction_half(30000) == 15000.0, "E: standard deduction 30,000 -> 15,000 each", "std ded wrong")

# -- constants --
check(L.COMMUNITY_PROPERTY_STATES == ["AZ", "CA", "ID", "LA", "NV", "NM", "TX", "WA", "WI"], "9 community-property states AZ/CA/ID/LA/NV/NM/TX/WA/WI", f"CP states wrong: {L.COMMUNITY_PROPERTY_STATES}")
check(L.FILE_LIMIT_YEARS_FROM_FILING == 3 and L.FILE_LIMIT_YEARS_FROM_PAYMENT == 2, "time limit 3yr-from-filing / 2yr-from-payment", "time limit wrong")
check(len(L.OFFSET_DEBT_TYPES) == 6, "6 offsettable past-due debt types", f"debt types wrong: {L.OFFSET_DEBT_TYPES}")

# -- key diagnostics + entity_types --
for did in ("D_8379_NOTINJURED", "D_8379_8857", "D_8379_ALLOC_BALANCE", "D_8379_WITHHOLDING", "D_8379_STDDED", "D_8379_CP", "D_8379_EIC", "D_8379_TIMELIMIT"):
    check(FormDiagnostic.objects.filter(tax_form=form, diagnostic_id=did).exists(), f"{did} present", f"{did} MISSING")
check(form.entity_types == ["1040"], "entity_types = [1040]", f"entity_types wrong: {form.entity_types}")

# -- report --
print("\n" + "=" * 66)
print(f"  8379: facts {FormFact.objects.filter(tax_form=form).count()} / rules {FormRule.objects.filter(tax_form=form).count()} / "
      f"lines {FormLine.objects.filter(tax_form=form).count()} / diag {FormDiagnostic.objects.filter(tax_form=form).count()} / "
      f"tests {form.test_scenarios.count()} / FA {FlowAssertion.objects.filter(assertion_id__startswith='FA-8379').count()}")
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
