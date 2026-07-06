"""Throwaway-SQLite validation for the Form 8990 loader (WO-14).

Checks CharField caps; every rule >= 1 authority link; rule_link coverage; arithmetic oracles
(total BIE, ATI EBITDA basis, 30% limitation, allowable/disallowed, partnership ETI/EBIE); key
diagnostics; entity_types. ASCII-only. Run: poetry run python scratchpad/validate_8990.py
"""
import os
import sys

PROJECT_ROOT = r"D:\dev\sherpa-tax-rule-studio"
sys.path.insert(0, PROJECT_ROOT)

SQLITE_PATH = os.path.join(PROJECT_ROOT, "scratchpad", "validate_8990.sqlite3")
if os.path.exists(SQLITE_PATH):
    os.remove(SQLITE_PATH)
os.environ["DATABASE_URL"] = f"sqlite:///{SQLITE_PATH}"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

import django  # noqa: E402
django.setup()

from django.core.management import call_command  # noqa: E402
from specs.models import FlowAssertion, FormDiagnostic, FormFact, FormLine, FormRule, TaxForm  # noqa: E402
from sources.models import AuthorityTopic, RuleAuthorityLink  # noqa: E402
from specs.management.commands import load_8990 as L  # noqa: E402

FAILURES: list[str] = []
PASSES: list[str] = []


def check(cond, ok, bad):
    (PASSES if cond else FAILURES).append(ok if cond else bad)


call_command("migrate", run_syncdb=True, verbosity=0)
L.READY_TO_SEED = True
try:
    call_command("load_8990", verbosity=0)
    PASSES.append("load_8990 ran + seeded into SQLite without error")
except Exception as e:  # noqa: BLE001
    FAILURES.append(f"load_8990 raised: {e!r}")
    print("\n".join(FAILURES))
    sys.exit(1)

form = TaxForm.objects.get(form_number="8990")

# ── CharField caps ──
CAPS: dict = {"form_number(50)": (form.form_number, 50)}
for r in FormRule.objects.filter(tax_form=form):
    CAPS[f"rule_id={r.rule_id}"] = (r.rule_id, 20)
for d in FormDiagnostic.objects.filter(tax_form=form):
    CAPS[f"diagnostic_id={d.diagnostic_id}"] = (d.diagnostic_id, 20)
for ln in FormLine.objects.filter(tax_form=form):
    CAPS[f"line_number={ln.line_number}"] = (ln.line_number, 20)
for fct in FormFact.objects.filter(tax_form=form):
    CAPS[f"fact_key={fct.fact_key}"] = (fct.fact_key, 100)
for fa in FlowAssertion.objects.filter(assertion_id__startswith="FA-8990"):
    CAPS[f"assertion_id={fa.assertion_id}"] = (fa.assertion_id, 20)
for t in AuthorityTopic.objects.all():
    CAPS[f"topic={t.topic_code}"] = (t.topic_name, 255)
viol = [f"{k}: len {len(v)} > {cap}" for k, (v, cap) in CAPS.items() if len(v) > cap]
check(not viol, f"CharField caps OK ({len(CAPS)} checked)", "CAP VIOLATIONS:\n    " + "\n    ".join(viol))

# ── authority links ──
ruleless = [r.rule_id for r in FormRule.objects.filter(tax_form=form)
            if not RuleAuthorityLink.objects.filter(form_rule=r).exists()]
check(not ruleless, f"all {FormRule.objects.filter(tax_form=form).count()} rules have >= 1 authority link", f"ruleless: {ruleless}")
defined = {r["rule_id"] for r in L.F8990_RULES}
linked = {rl[0] for rl in L.F8990_RULE_LINKS}
check(not (linked - defined), "rule_links reference defined rules", f"orphan: {linked - defined}")
check(not (defined - linked), "every rule appears in rule_links", f"unlinked: {defined - linked}")

# ── arithmetic oracles ──
tot = L._total_bie(500000, 0, 0, 0)
check(tot == 500000, "total BIE: 500,000", f"total_bie wrong: {tot}")
ati = L._ati(1000000, 300000, 0)
check(ati == 1300000, "ATI EBITDA basis: 1,000,000 + 300,000 dep add-back = 1,300,000", f"ATI wrong: {ati}")
lim = L._limitation(20000, 1300000, 0)
check(lim == 410000, "limit: 30% × 1,300,000 + 20,000 BII = 410,000", f"limit wrong: {lim}")
allow = min(500000, lim)
disallowed = max(0, 500000 - lim)
check(allow == 410000 and disallowed == 90000, "allowable 410,000 / disallowed carryforward 90,000", f"allow/disallow wrong: {allow}/{disallowed}")
# EBIT-basis counterfactual: without the add-back, disallowed would be 180,000
ati_ebit = L._ati(1000000, 0, 0)
lim_ebit = L._limitation(20000, ati_ebit, 0)
check(max(0, 500000 - lim_ebit) == 180000, "EBIT counterfactual: no add-back -> disallowed 180,000 (add-back saves 90,000)", f"EBIT wrong: {max(0,500000-lim_ebit)}")
# partnership ETI
eti = L._eti(60000, 0, 0, 1000000)
check(round(eti) == 800000, "partnership ETI: (240,000/300,000) × 1,000,000 = 800,000", f"ETI wrong: {eti}")
# partnership EBIE
ati2 = L._ati(100000, 0, 0)
lim2 = L._limitation(0, ati2, 0)
check(max(0, 50000 - lim2) == 20000, "partnership EBIE: BIE 50,000 − limit 30,000 = 20,000 passes to partners", f"EBIE wrong: {max(0,50000-lim2)}")
check(L.LIMIT_PCT == "0.30" and L.EXEMPT_GROSS_RECEIPTS == 31000000, "30% limit + $31M §448(c) exemption", "constants wrong")

# ── key diagnostics + entity_types ──
for did in ("D_8990_EBITDA", "D_8990_DISALLOW", "D_8990_EXEMPT", "D_8990_EXCEPTED", "D_8990_EBIE"):
    check(FormDiagnostic.objects.filter(tax_form=form, diagnostic_id=did).exists(), f"{did} present", f"{did} MISSING")
check(form.entity_types == ["1120", "1065", "1120S", "1040"], "entity_types = [1120,1065,1120S,1040]", f"entity_types wrong: {form.entity_types}")

# ── report ──
print("\n" + "=" * 66)
print(f"  8990: facts {FormFact.objects.filter(tax_form=form).count()} / rules {FormRule.objects.filter(tax_form=form).count()} / "
      f"lines {FormLine.objects.filter(tax_form=form).count()} / diag {FormDiagnostic.objects.filter(tax_form=form).count()} / "
      f"tests {form.test_scenarios.count()} / FA {FlowAssertion.objects.filter(assertion_id__startswith='FA-8990').count()}")
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
