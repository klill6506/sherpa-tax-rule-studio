"""Throwaway-SQLite validation for the Form 4952 loader (WO-17).

Checks CharField caps; every rule >= 1 authority link; rule_link coverage; arithmetic oracles
(L3, 4c/4f/4h, L6, L8 §163(d) limit, L7 indefinite carryforward, 4g election cap); key diagnostics;
entity_types. ASCII-only. Run: poetry run python scratchpad/validate_4952.py
"""
import os
import sys

PROJECT_ROOT = r"D:\dev\sherpa-tax-rule-studio"
sys.path.insert(0, PROJECT_ROOT)

SQLITE_PATH = os.path.join(PROJECT_ROOT, "scratchpad", "validate_4952.sqlite3")
if os.path.exists(SQLITE_PATH):
    os.remove(SQLITE_PATH)
os.environ["DATABASE_URL"] = f"sqlite:///{SQLITE_PATH}"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

import django  # noqa: E402
django.setup()

from django.core.management import call_command  # noqa: E402
from specs.models import FlowAssertion, FormDiagnostic, FormFact, FormLine, FormRule, TaxForm  # noqa: E402
from sources.models import AuthorityTopic, RuleAuthorityLink  # noqa: E402
from specs.management.commands import load_4952 as L  # noqa: E402

FAILURES: list[str] = []
PASSES: list[str] = []


def check(cond, ok, bad):
    (PASSES if cond else FAILURES).append(ok if cond else bad)


call_command("migrate", run_syncdb=True, verbosity=0)
L.READY_TO_SEED = True
try:
    call_command("load_4952", verbosity=0)
    PASSES.append("load_4952 ran + seeded into SQLite without error")
except Exception as e:  # noqa: BLE001
    FAILURES.append(f"load_4952 raised: {e!r}")
    print("\n".join(FAILURES))
    sys.exit(1)

form = TaxForm.objects.get(form_number="4952")

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
for fa in FlowAssertion.objects.filter(assertion_id__startswith="FA-4952"):
    CAPS[f"assertion_id={fa.assertion_id}"] = (fa.assertion_id, 20)
for t in AuthorityTopic.objects.all():
    CAPS[f"topic={t.topic_code}"] = (t.topic_name, 255)
viol = [f"{k}: len {len(v)} > {cap}" for k, (v, cap) in CAPS.items() if len(v) > cap]
check(not viol, f"CharField caps OK ({len(CAPS)} checked)", "CAP VIOLATIONS:\n    " + "\n    ".join(viol))

# -- authority links --
ruleless = [r.rule_id for r in FormRule.objects.filter(tax_form=form)
            if not RuleAuthorityLink.objects.filter(form_rule=r).exists()]
check(not ruleless, f"all {FormRule.objects.filter(tax_form=form).count()} rules have >= 1 authority link", f"ruleless: {ruleless}")
defined = {r["rule_id"] for r in L.F4952_RULES}
linked = {rl[0] for rl in L.F4952_RULE_LINKS}
check(not (linked - defined), "rule_links reference defined rules", f"orphan: {linked - defined}")
check(not (defined - linked), "every rule appears in rule_links", f"unlinked: {defined - linked}")

# -- arithmetic oracles --
# A: limited to NII
check(L._line3(10000, 0) == 10000.0, "A: L3 = 10,000 + 0 = 10,000", "A L3 wrong")
inc = L._investment_income(6000, 0, 0, 0, 0)
check(inc["L4h"] == 6000.0, "A: L4h investment income 6,000", f"A 4h wrong: {inc}")
nii = L._net_investment_income(6000, 0)
check(nii == 6000.0, "A: L6 net investment income 6,000", f"A L6 wrong: {nii}")
check(L._deduction(10000, 6000) == 6000.0, "A: L8 = min(10,000, 6,000) = 6,000", "A L8 wrong")
check(L._carryforward(10000, 6000) == 4000.0, "A: L7 carryforward = 4,000 (indefinite)", "A L7 wrong")
# B: fully deductible
check(L._deduction(3000, 6000) == 3000.0 and L._carryforward(3000, 6000) == 0.0, "B: interest 3,000 < income 6,000 -> L8 3,000 / L7 0", "B wrong")
# C: prior carryforward stacks
check(L._line3(5000, 4000) == 9000.0 and L._deduction(9000, 6000) == 6000.0 and L._carryforward(9000, 6000) == 3000.0, "C: L3 9,000; L8 6,000; L7 3,000 rolls forward", "C wrong")
# D: 4g election
d = L._investment_income(2000, 1500, 8000, 8000, 5000)
check(d["L4c"] == 500.0 and d["L4f"] == 0.0 and d["L4h"] == 5500.0, "D: 4c 500 / 4f 0 / 4h 5,500 (elect 5,000)", f"D income wrong: {d}")
check(L._deduction(5000, 5500) == 5000.0, "D: L8 = min(5,000, 5,500) = 5,000 (election freed the deduction)", "D L8 wrong")
check(L._elect_4g_cap(1500, 8000) == 9500.0, "D: 4g cap = 4b 1,500 + 4e 8,000 = 9,500 (elect 5,000 <= cap)", "D 4g cap wrong")
# D counterfactual: no election
dne = L._investment_income(2000, 1500, 8000, 8000, 0)
check(L._deduction(5000, L._net_investment_income(dne["L4h"], 0)) == 500.0, "D': without the 4g election L8 only 500 (election freed 4,500)", "D' counterfactual wrong")
# E: expenses exceed income
e = L._investment_income(2000, 0, 0, 0, 0)
check(L._net_investment_income(e["L4h"], 3000) == 0.0, "E: L5 3,000 > L4h 2,000 -> L6 = 0", "E L6 wrong")
check(L._deduction(4000, 0) == 0.0 and L._carryforward(4000, 0) == 4000.0, "E: L8 0 / entire L3 4,000 carries forward", "E wrong")

# -- key diagnostics + entity_types --
for did in ("D_4952_LIMIT", "D_4952_4G_RATE", "D_4952_4G_CAP", "D_4952_MISC", "D_4952_EXCL", "D_4952_FILE_EXC", "D_4952_ROUTE"):
    check(FormDiagnostic.objects.filter(tax_form=form, diagnostic_id=did).exists(), f"{did} present", f"{did} MISSING")
check(form.entity_types == ["1040", "1041"], "entity_types = [1040,1041]", f"entity_types wrong: {form.entity_types}")

# -- report --
print("\n" + "=" * 66)
print(f"  4952: facts {FormFact.objects.filter(tax_form=form).count()} / rules {FormRule.objects.filter(tax_form=form).count()} / "
      f"lines {FormLine.objects.filter(tax_form=form).count()} / diag {FormDiagnostic.objects.filter(tax_form=form).count()} / "
      f"tests {form.test_scenarios.count()} / FA {FlowAssertion.objects.filter(assertion_id__startswith='FA-4952').count()}")
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
