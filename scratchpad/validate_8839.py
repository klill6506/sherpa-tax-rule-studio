"""Throwaway-SQLite validation for the Form 8839 loader (WO-20).

Checks CharField caps; every rule >= 1 authority link; rule_link coverage; arithmetic oracles
(credit base + special-needs, MAGI phaseout, refundable split $5,000, nonrefundable + tax limit +
carryforward, Part III exclusion + taxable); key diagnostics; entity_types. ASCII-only.
Run: poetry run python scratchpad/validate_8839.py
"""
import os
import sys

PROJECT_ROOT = r"D:\dev\sherpa-tax-rule-studio"
sys.path.insert(0, PROJECT_ROOT)

SQLITE_PATH = os.path.join(PROJECT_ROOT, "scratchpad", "validate_8839.sqlite3")
if os.path.exists(SQLITE_PATH):
    os.remove(SQLITE_PATH)
os.environ["DATABASE_URL"] = f"sqlite:///{SQLITE_PATH}"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

import django  # noqa: E402
django.setup()

from django.core.management import call_command  # noqa: E402
from specs.models import FlowAssertion, FormDiagnostic, FormFact, FormLine, FormRule, TaxForm  # noqa: E402
from sources.models import AuthorityTopic, RuleAuthorityLink  # noqa: E402
from specs.management.commands import load_8839 as L  # noqa: E402

FAILURES: list[str] = []
PASSES: list[str] = []


def check(cond, ok, bad):
    (PASSES if cond else FAILURES).append(ok if cond else bad)


call_command("migrate", run_syncdb=True, verbosity=0)
L.READY_TO_SEED = True
try:
    call_command("load_8839", verbosity=0)
    PASSES.append("load_8839 ran + seeded into SQLite without error")
except Exception as e:  # noqa: BLE001
    FAILURES.append(f"load_8839 raised: {e!r}")
    print("\n".join(FAILURES))
    sys.exit(1)

form = TaxForm.objects.get(form_number="8839")

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
for fa in FlowAssertion.objects.filter(assertion_id__startswith="FA-8839"):
    CAPS[f"assertion_id={fa.assertion_id}"] = (fa.assertion_id, 20)
for t in AuthorityTopic.objects.all():
    CAPS[f"topic={t.topic_code}"] = (t.topic_name, 255)
viol = [f"{k}: len {len(v)} > {cap}" for k, (v, cap) in CAPS.items() if len(v) > cap]
check(not viol, f"CharField caps OK ({len(CAPS)} checked)", "CAP VIOLATIONS:\n    " + "\n    ".join(viol))

# -- authority links --
ruleless = [r.rule_id for r in FormRule.objects.filter(tax_form=form)
            if not RuleAuthorityLink.objects.filter(form_rule=r).exists()]
check(not ruleless, f"all {FormRule.objects.filter(tax_form=form).count()} rules have >= 1 authority link", f"ruleless: {ruleless}")
defined = {r["rule_id"] for r in L.F8839_RULES}
linked = {rl[0] for rl in L.F8839_RULE_LINKS}
check(not (linked - defined), "rule_links reference defined rules", f"orphan: {linked - defined}")
check(not (defined - linked), "every rule appears in rule_links", f"unlinked: {defined - linked}")

# -- arithmetic oracles --
# A: no phaseout
b = L._line6_credit_base(0, 20000, False)
check(b == 17280.0, "A: L6 = min(17,280, 20,000) = 17,280", f"A base wrong: {b}")
l11a = L._credit_after_phaseout(17280, 100000)
check(l11a == 17280.0, "A: MAGI 100k -> no phaseout -> L11a 17,280", f"A L11a wrong: {l11a}")
check(L._refundable(17280) == 5000.0, "A: refundable = min(17,280, 5,000) = 5,000", "A refund wrong")
check(L._nonrefundable(17280, 5000, 0, 15000) == 12280.0, "A: nonrefundable min(12,280, 15,000) = 12,280", "A nonref wrong")
# B: phaseout 0.5
check(L._phaseout_fraction(279190) == 0.5, "B: fraction (279,190-259,190)/40,000 = 0.5", f"B frac wrong: {L._phaseout_fraction(279190)}")
check(L._credit_after_phaseout(17280, 279190) == 8640.0, "B: L11a = 17,280 x 0.5 = 8,640", f"B L11a wrong: {L._credit_after_phaseout(17280,279190)}")
check(L._nonrefundable(8640, 5000, 0, 15000) == 3640.0, "B: nonrefundable 8,640-5,000 = 3,640", "B nonref wrong")
# C: fully phased out
check(L._phaseout_fraction(299190) == 1.0 and L._credit_after_phaseout(17280, 299190) == 0.0, "C: MAGI 299,190 -> fraction 1.0 -> L11a 0", "C phaseout wrong")
check(L._phaseout_fraction(259190) == 0.0, "C': MAGI exactly 259,190 -> fraction 0 (no phaseout)", "C' boundary wrong")
# D: special needs, no expenses
check(L._line6_credit_base(0, 0, True) == 17280.0, "D: special needs, $0 expenses -> full 17,280", f"D special wrong: {L._line6_credit_base(0,0,True)}")
# E: exclusion
ex = L._exclusion_after_phaseout(min(17280, 20000), 100000)
check(ex == 17280.0, "E: excluded = min(17,280, 20,000), no phaseout = 17,280", f"E excl wrong: {ex}")
check(round(20000 - ex, 2) == 2720.0, "E: taxable = 20,000 - 17,280 = 2,720 -> 1040 L1f", "E taxable wrong")
# F: tax-limit caps nonrefundable
check(L._nonrefundable(17280, 5000, 0, 5000) == 5000.0, "F: nonrefundable L16 12,280 capped by tax limit 5,000 -> 5,000", "F nonref wrong")
check(round((17280 - 5000) - 5000, 2) == 7280.0, "F: carryforward = 12,280 - 5,000 = 7,280 (5 yrs)", "F carryforward wrong")
# constants
check(L.MAX_CREDIT == 17280 and L.PHASEOUT_START == 259190 and L.PHASEOUT_DIVISOR == 40000 and L.REFUNDABLE_CAP == 5000,
      "2025 figures $17,280 / $259,190 / $40,000 / $5,000", "constants wrong")
check(L.PHASEOUT_FULL == 299190 and L.CARRYFORWARD_YEARS == 5, "fully phased out $299,190 / 5-yr carryforward", "phaseout-full/carry wrong")

# -- key diagnostics + entity_types --
for did in ("D_8839_REFUND", "D_8839_PHASEOUT", "D_8839_SPECIALNEEDS", "D_8839_BOTH", "D_8839_MFS", "D_8839_CARRYFWD", "D_8839_EXCLUSION", "D_8839_INDEXED"):
    check(FormDiagnostic.objects.filter(tax_form=form, diagnostic_id=did).exists(), f"{did} present", f"{did} MISSING")
check(form.entity_types == ["1040"], "entity_types = [1040]", f"entity_types wrong: {form.entity_types}")

# -- report --
print("\n" + "=" * 66)
print(f"  8839: facts {FormFact.objects.filter(tax_form=form).count()} / rules {FormRule.objects.filter(tax_form=form).count()} / "
      f"lines {FormLine.objects.filter(tax_form=form).count()} / diag {FormDiagnostic.objects.filter(tax_form=form).count()} / "
      f"tests {form.test_scenarios.count()} / FA {FlowAssertion.objects.filter(assertion_id__startswith='FA-8839').count()}")
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
