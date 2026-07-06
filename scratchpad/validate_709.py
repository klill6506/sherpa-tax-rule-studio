"""Throwaway-SQLite validation for the Form 709 loader (WO-21).

Checks CharField caps; every rule >= 1 authority link; rule_link coverage; arithmetic oracles
(§2001(c) rate schedule incl. the $5,541,800 applicable-credit derivation, cumulative engine,
Schedule A reconciliation, gift-splitting, GST 40% x inclusion ratio); key diagnostics; entity_types.
ASCII-only. Run: poetry run python scratchpad/validate_709.py
"""
import os
import sys

PROJECT_ROOT = r"D:\dev\sherpa-tax-rule-studio"
sys.path.insert(0, PROJECT_ROOT)

SQLITE_PATH = os.path.join(PROJECT_ROOT, "scratchpad", "validate_709.sqlite3")
if os.path.exists(SQLITE_PATH):
    os.remove(SQLITE_PATH)
os.environ["DATABASE_URL"] = f"sqlite:///{SQLITE_PATH}"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

import django  # noqa: E402
django.setup()

from django.core.management import call_command  # noqa: E402
from specs.models import FlowAssertion, FormDiagnostic, FormFact, FormLine, FormRule, TaxForm  # noqa: E402
from sources.models import AuthorityTopic, RuleAuthorityLink  # noqa: E402
from specs.management.commands import load_709 as L  # noqa: E402

FAILURES: list[str] = []
PASSES: list[str] = []


def check(cond, ok, bad):
    (PASSES if cond else FAILURES).append(ok if cond else bad)


call_command("migrate", run_syncdb=True, verbosity=0)
L.READY_TO_SEED = True
try:
    call_command("load_709", verbosity=0)
    PASSES.append("load_709 ran + seeded into SQLite without error")
except Exception as e:  # noqa: BLE001
    FAILURES.append(f"load_709 raised: {e!r}")
    print("\n".join(FAILURES))
    sys.exit(1)

form = TaxForm.objects.get(form_number="709")

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
for fa in FlowAssertion.objects.filter(assertion_id__startswith="FA-709"):
    CAPS[f"assertion_id={fa.assertion_id}"] = (fa.assertion_id, 20)
for t in AuthorityTopic.objects.all():
    CAPS[f"topic={t.topic_code}"] = (t.topic_name, 255)
viol = [f"{k}: len {len(v)} > {cap}" for k, (v, cap) in CAPS.items() if len(v) > cap]
check(not viol, f"CharField caps OK ({len(CAPS)} checked)", "CAP VIOLATIONS:\n    " + "\n    ".join(viol))

# -- authority links --
ruleless = [r.rule_id for r in FormRule.objects.filter(tax_form=form)
            if not RuleAuthorityLink.objects.filter(form_rule=r).exists()]
check(not ruleless, f"all {FormRule.objects.filter(tax_form=form).count()} rules have >= 1 authority link", f"ruleless: {ruleless}")
defined = {r["rule_id"] for r in L.F709_RULES}
linked = {rl[0] for rl in L.F709_RULE_LINKS}
check(not (linked - defined), "rule_links reference defined rules", f"orphan: {linked - defined}")
check(not (defined - linked), "every rule appears in rule_links", f"unlinked: {defined - linked}")

# -- rate schedule oracles --
check(L._tentative_tax(1000000) == 345800.0, "rate: tentative(1,000,000) = 345,800", f"1M wrong: {L._tentative_tax(1000000)}")
check(L._tentative_tax(13990000) == 5541800.0, "rate: tentative(13,990,000 BEA) = 5,541,800 = the applicable credit", f"BEA wrong: {L._tentative_tax(13990000)}")
check(L.APPLICABLE_CREDIT == 5541800, "applicable credit constant = $5,541,800 (2025, not the 2024 $5,389,800)", f"credit wrong: {L.APPLICABLE_CREDIT}")
check(L._tentative_tax(10000) == 1800.0, "rate: tentative(10,000) = 1,800", f"10k wrong: {L._tentative_tax(10000)}")
check(L._tentative_tax(250000) == 70800.0, "rate: tentative(250,000) = 70,800", f"250k wrong: {L._tentative_tax(250000)}")
check(L._tentative_tax(0) == 0.0, "rate: tentative(0) = 0", "0 wrong")

# -- cumulative engine oracles --
# A: under exclusion
check(L._taxable_gifts(5019000, 19000, 0, 0) == 5000000.0, "A: taxable gifts 5,019,000 - 19,000 = 5,000,000", "A taxable wrong")
check(L._gift_tax_due(5000000, 0, 0) == 0.0, "A: 5M taxable, credit shelters -> $0 gift tax", f"A tax wrong: {L._gift_tax_due(5000000,0,0)}")
# B: over BEA
check(L._gift_tax_due(20000000, 0, 0) == 2404000.0, "B: 20M taxable -> tax 2,404,000 (= (20M-13.99M) x 40%)", f"B tax wrong: {L._gift_tax_due(20000000,0,0)}")
# C: cumulative with prior
check(L._tentative_tax(15000000) == 5945800.0 and L._tentative_tax(10000000) == 3945800.0, "C: tentative(15M)=5,945,800 / tentative(10M)=3,945,800", "C tentatives wrong")
check(L._gift_tax_due(5000000, 10000000, 0) == 404000.0, "C: current 5M on top of prior 10M -> tax 404,000 (cumulative)", f"C tax wrong: {L._gift_tax_due(5000000,10000000,0)}")
# D: Schedule A
check(L._taxable_gifts(100000, 38000, 0, 0) == 62000.0, "D: 100,000 - 38,000 excl = 62,000 taxable", "D wrong")
# E: gift-splitting
check(L._annual_exclusion(50000, True) == 38000.0 and L._annual_exclusion(50000, False) == 19000.0, "E: split exclusion 38,000 vs 19,000", "E split wrong")
# F: GST
check(L._gst_tax(5000000, 3000000) == 800000.0, "F: GST 5M, exemption 3M -> inclusion 0.4 -> tax 800,000", f"F GST wrong: {L._gst_tax(5000000,3000000)}")
check(L._gst_tax(5000000, 5000000) == 0.0, "F': full exemption -> inclusion 0 -> GST tax 0", "F' GST wrong")
# DSUE increases credit
check(L._gift_tax_due(20000000, 0, 1000000) < L._gift_tax_due(20000000, 0, 0), "DSUE increases the credit -> lower gift tax", "DSUE wrong")
# constants
check(L.ANNUAL_EXCLUSION == 19000 and L.BEA == 13990000 and L.NONCITIZEN_SPOUSE_EXCLUSION == 190000 and L.GST_EXEMPTION == 13990000,
      "2025 figures $19,000 / $13,990,000 BEA / $190,000 noncitizen / $13,990,000 GST", "constants wrong")
check(L.BEA_2026_OBBBA == 15000000, "OBBBA $15,000,000 BEA year-keyed for 2026 (not 2025)", "OBBBA 2026 wrong")

# -- key diagnostics + entity_types --
for did in ("D_709_MUSTFILE", "D_709_ANNUAL_EXCL", "D_709_SPLIT", "D_709_MARITAL", "D_709_BEA", "D_709_GST", "D_709_DSUE", "D_709_UNVERIFIED"):
    check(FormDiagnostic.objects.filter(tax_form=form, diagnostic_id=did).exists(), f"{did} present", f"{did} MISSING")
check(form.entity_types == ["709"], "entity_types = [709]", f"entity_types wrong: {form.entity_types}")

# -- report --
print("\n" + "=" * 66)
print(f"  709: facts {FormFact.objects.filter(tax_form=form).count()} / rules {FormRule.objects.filter(tax_form=form).count()} / "
      f"lines {FormLine.objects.filter(tax_form=form).count()} / diag {FormDiagnostic.objects.filter(tax_form=form).count()} / "
      f"tests {form.test_scenarios.count()} / FA {FlowAssertion.objects.filter(assertion_id__startswith='FA-709').count()}")
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
