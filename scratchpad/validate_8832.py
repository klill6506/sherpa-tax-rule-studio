"""Throwaway-SQLite validation for the Form 8832 loader (WO-22).

Checks CharField caps; every rule >= 1 authority link; rule_link coverage; logic oracles
(eligibility tree, default classification domestic/foreign, available classifications, effective-date
clamp); key diagnostics; entity_types. ASCII-only. Run: poetry run python scratchpad/validate_8832.py
"""
import os
import sys

PROJECT_ROOT = r"D:\dev\sherpa-tax-rule-studio"
sys.path.insert(0, PROJECT_ROOT)

SQLITE_PATH = os.path.join(PROJECT_ROOT, "scratchpad", "validate_8832.sqlite3")
if os.path.exists(SQLITE_PATH):
    os.remove(SQLITE_PATH)
os.environ["DATABASE_URL"] = f"sqlite:///{SQLITE_PATH}"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

import django  # noqa: E402
django.setup()

from django.core.management import call_command  # noqa: E402
from specs.models import FlowAssertion, FormDiagnostic, FormFact, FormLine, FormRule, TaxForm  # noqa: E402
from sources.models import AuthorityTopic, RuleAuthorityLink  # noqa: E402
from specs.management.commands import load_8832 as L  # noqa: E402

FAILURES: list[str] = []
PASSES: list[str] = []


def check(cond, ok, bad):
    (PASSES if cond else FAILURES).append(ok if cond else bad)


call_command("migrate", run_syncdb=True, verbosity=0)
L.READY_TO_SEED = True
try:
    call_command("load_8832", verbosity=0)
    PASSES.append("load_8832 ran + seeded into SQLite without error")
except Exception as e:  # noqa: BLE001
    FAILURES.append(f"load_8832 raised: {e!r}")
    print("\n".join(FAILURES))
    sys.exit(1)

form = TaxForm.objects.get(form_number="8832")

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
for fa in FlowAssertion.objects.filter(assertion_id__startswith="FA-8832"):
    CAPS[f"assertion_id={fa.assertion_id}"] = (fa.assertion_id, 20)
for t in AuthorityTopic.objects.all():
    CAPS[f"topic={t.topic_code}"] = (t.topic_name, 255)
viol = [f"{k}: len {len(v)} > {cap}" for k, (v, cap) in CAPS.items() if len(v) > cap]
check(not viol, f"CharField caps OK ({len(CAPS)} checked)", "CAP VIOLATIONS:\n    " + "\n    ".join(viol))

# -- authority links --
ruleless = [r.rule_id for r in FormRule.objects.filter(tax_form=form)
            if not RuleAuthorityLink.objects.filter(form_rule=r).exists()]
check(not ruleless, f"all {FormRule.objects.filter(tax_form=form).count()} rules have >= 1 authority link", f"ruleless: {ruleless}")
defined = {r["rule_id"] for r in L.F8832_RULES}
linked = {rl[0] for rl in L.F8832_RULE_LINKS}
check(not (linked - defined), "rule_links reference defined rules", f"orphan: {linked - defined}")
check(not (defined - linked), "every rule appears in rule_links", f"unlinked: {defined - linked}")

# -- eligibility oracles --
check(L._is_eligible_to_elect(False, "initial", False, False) == (True, "eligible"), "A: domestic initial -> eligible", "A elig wrong")
check(L._is_eligible_to_elect(False, "change", True, False) == (False, "sixty_month_block"), "C: change + prior<60mo (not newform) -> 60-month block", "C elig wrong")
check(L._is_eligible_to_elect(False, "change", True, True) == (True, "eligible"), "D: 60-month exception (prior newform initial) -> eligible", "D elig wrong")
check(L._is_eligible_to_elect(True, "initial", False, False) == (False, "per_se_corp"), "E: per-se corp -> not eligible", "E elig wrong")
check(L._is_eligible_to_elect(False, "change", False, False) == (True, "eligible"), "change with no prior 60-mo election -> eligible", "change-noprior wrong")

# -- default classification oracles --
check(L._default_classification(True, 1, False) == "disregarded", "A: domestic 1 owner -> disregarded", "A default wrong")
check(L._default_classification(True, 2, False) == "partnership", "B: domestic 2 owners -> partnership", "B default wrong")
check(L._default_classification(False, 2, True) == "corporation", "F: foreign 2 all-LL -> corporation", "F default wrong")
check(L._default_classification(False, 2, False) == "partnership", "foreign 2 not-all-LL -> partnership", "foreign-2-notLL wrong")
check(L._default_classification(False, 1, False) == "disregarded", "foreign 1 no-LL -> disregarded", "foreign-1 wrong")

# -- available classifications --
check(L._available_classifications(2) == ["partnership", "corporation"], "options: >1 owner -> partnership/corporation", "options>1 wrong")
check(L._available_classifications(1) == ["corporation", "disregarded"], "options: 1 owner -> corporation/disregarded", "options1 wrong")

# -- effective-date clamp --
check(L._clamp_days_before(100) == 75.0, "G: 100 days before -> clamps to 75", f"clamp wrong: {L._clamp_days_before(100)}")
check(L._clamp_days_before(30) == 30.0, "clamp: 30 days before -> 30 (within window)", "clamp-30 wrong")

# -- constants --
check(L.SIXTY_MONTH_LIMITATION == 60 and L.EFF_DATE_DAYS_BEFORE == 75 and L.EFF_DATE_MONTHS_AFTER == 12, "60-month / 75-day / 12-month constants", "constants wrong")
check(L.LATE_RELIEF_YEARS == 3 and L.LATE_RELIEF_DAYS == 75, "late relief 3 years 75 days", "late-relief wrong")
check(L.FILING_ADDRESSES["eastern"] == "Kansas City, MO 64999" and L.FILING_ADDRESSES["western"] == "Ogden, UT 84201", "updated addresses Kansas City / Ogden", "addresses wrong")

# -- key diagnostics + entity_types --
for did in ("D_8832_PERSE", "D_8832_60MONTH", "D_8832_DEFAULT", "D_8832_EFFDATE", "D_8832_LATE", "D_8832_2553", "D_8832_FILING", "D_8832_FOREIGN"):
    check(FormDiagnostic.objects.filter(tax_form=form, diagnostic_id=did).exists(), f"{did} present", f"{did} MISSING")
check(form.entity_types == ["1065", "1120", "1120S", "1040"], "entity_types = [1065,1120,1120S,1040]", f"entity_types wrong: {form.entity_types}")

# -- report --
print("\n" + "=" * 66)
print(f"  8832: facts {FormFact.objects.filter(tax_form=form).count()} / rules {FormRule.objects.filter(tax_form=form).count()} / "
      f"lines {FormLine.objects.filter(tax_form=form).count()} / diag {FormDiagnostic.objects.filter(tax_form=form).count()} / "
      f"tests {form.test_scenarios.count()} / FA {FlowAssertion.objects.filter(assertion_id__startswith='FA-8832').count()}")
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
