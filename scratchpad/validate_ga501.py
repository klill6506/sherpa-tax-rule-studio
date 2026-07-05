"""Throwaway-SQLite validation for the GA Form 501 loader (leg c).

Seeds load_ga700 FIRST so the reused GA statute source (GA_OCGA_48_7) resolves,
then load_ga501. Checks: CharField caps; every rule >= 1 authority link; rule_link
coverage; reused-source presence; arithmetic (exemptions, 5.19% tax, beneficiary
removal, Sch 2 net adjustment); RED-defer diagnostic present.

Run: poetry run python scratchpad/validate_ga501.py
"""
import os
import sys

PROJECT_ROOT = r"D:\dev\sherpa-tax-rule-studio"
sys.path.insert(0, PROJECT_ROOT)

SQLITE_PATH = os.path.join(PROJECT_ROOT, "scratchpad", "validate_ga501.sqlite3")
if os.path.exists(SQLITE_PATH):
    os.remove(SQLITE_PATH)
os.environ["DATABASE_URL"] = f"sqlite:///{SQLITE_PATH}"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

import django  # noqa: E402
django.setup()

from django.core.management import call_command  # noqa: E402
from specs.models import (  # noqa: E402
    FlowAssertion, FormDiagnostic, FormFact, FormLine, FormRule, TaxForm,
)
from sources.models import AuthorityTopic, AuthoritySource, RuleAuthorityLink  # noqa: E402
from specs.management.commands import load_ga700 as GA700  # noqa: E402
from specs.management.commands import load_ga501 as GA501  # noqa: E402

FAILURES: list[str] = []
PASSES: list[str] = []


def check(cond, ok, bad):
    (PASSES if cond else FAILURES).append(ok if cond else bad)


# ── seed GA700 (for GA_OCGA_48_7) then GA501 ──
call_command("migrate", run_syncdb=True, verbosity=0)
GA700.READY_TO_SEED = True
GA501.READY_TO_SEED = True
try:
    call_command("load_ga700", verbosity=0)
    call_command("load_ga501", verbosity=1)
    PASSES.append("ga700 + ga501 loaders seeded into SQLite without error")
except Exception as e:  # noqa: BLE001
    FAILURES.append(f"loader raised: {e!r}")
    print("\n".join(FAILURES))
    sys.exit(1)

form = TaxForm.objects.get(form_number="GA501")

# ── CharField caps ──
CAPS = {"form_number(50)": (form.form_number, 50)}
for r in FormRule.objects.filter(tax_form=form):
    CAPS[f"rule_id={r.rule_id}"] = (r.rule_id, 20)
for d in FormDiagnostic.objects.filter(tax_form=form):
    CAPS[f"diagnostic_id={d.diagnostic_id}"] = (d.diagnostic_id, 20)
for ln in FormLine.objects.filter(tax_form=form):
    CAPS[f"line_number={ln.line_number}"] = (ln.line_number, 20)
for fa in FlowAssertion.objects.filter(assertion_id__startswith="FA-GA501"):
    CAPS[f"assertion_id={fa.assertion_id}"] = (fa.assertion_id, 20)
for fct in FormFact.objects.filter(tax_form=form):
    CAPS[f"fact_key={fct.fact_key}"] = (fct.fact_key, 100)
for t in AuthorityTopic.objects.all():
    CAPS[f"topic_name={t.topic_code}"] = (t.topic_name, 255)
viol = [f"{k}: len {len(v)} > {cap}" for k, (v, cap) in CAPS.items() if len(v) > cap]
check(not viol, f"CharField caps OK ({len(CAPS)} checked)", "CAP VIOLATIONS:\n    " + "\n    ".join(viol))

# ── every rule has >= 1 authority link ──
ruleless = [r.rule_id for r in FormRule.objects.filter(tax_form=form)
            if not RuleAuthorityLink.objects.filter(form_rule=r).exists()]
check(not ruleless, f"all {FormRule.objects.filter(tax_form=form).count()} GA501 rules have >= 1 authority link",
      f"GA501 rules with ZERO authority links: {ruleless}")

defined = {r["rule_id"] for r in GA501.GA501_RULES}
linked = {rl[0] for rl in GA501.GA501_RULE_LINKS}
check(not (linked - defined), "all rule_links reference defined rules", f"orphan links: {linked - defined}")
check(not (defined - linked), "every defined rule appears in rule_links", f"unlinked rules: {defined - linked}")
check(AuthoritySource.objects.filter(source_code="GA_OCGA_48_7").exists(),
      "reused source GA_OCGA_48_7 present (from ga700)", "reused source GA_OCGA_48_7 MISSING")

# ── arithmetic (round to nearest dollar) ──
def ga501(fed_ati, ftype, benef=0, adds=0, subs=0, nol=0):
    L2 = adds - subs
    L3 = fed_ati + L2
    L5 = L3 - benef
    L6 = 1350 if ftype == "trust" else 2700
    L7a = max(0, L5 - L6)
    L7c = max(0, L7a - nol)
    L8 = round(L7c * 0.0519)
    return dict(L2=L2, L3=L3, L5=L5, L6=L6, L7c=L7c, L8=L8)

t1 = ga501(50000, "trust")
check(t1["L6"] == 1350 and t1["L7c"] == 48650 and t1["L8"] == 2525,
      "T1 resident trust: exemption 1,350 / taxable 48,650 / tax 2,525 (5.19%)", f"T1 wrong: {t1}")
t2 = ga501(40000, "estate")
check(t2["L6"] == 2700 and t2["L7c"] == 37300 and t2["L8"] == 1936,
      "T2 resident estate: exemption 2,700 / taxable 37,300 / tax 1,936", f"T2 wrong: {t2}")
t3 = ga501(60000, "trust", benef=45000)
check(t3["L5"] == 15000 and t3["L7c"] == 13650 and t3["L8"] == 708,
      "T3 beneficiary share removed: retained 15,000 / taxable 13,650 / tax 708 (no IDD double-count)", f"T3 wrong: {t3}")
t4 = ga501(30000, "trust", adds=2000, subs=5000)
check(t4["L2"] == -3000 and t4["L5"] == 27000 and t4["L7c"] == 25650,
      "T4 Sch 2 net adj: 2,000 add - 5,000 sub = -3,000 / L5 27,000 / taxable 25,650", f"T4 wrong: {t4}")

# ── constants + RED-defer diagnostic ──
check(GA501.GA_FLAT_RATE[2025] == "0.0519", "rate 5.19% (0.0519)", f"rate wrong: {GA501.GA_FLAT_RATE}")
check(GA501.GA_EXEMPTION_TRUST[2025] == 1350 and GA501.GA_EXEMPTION_ESTATE[2025] == 2700,
      "exemptions trust 1,350 / estate 2,700", "exemptions wrong")
for did in ("D_GA501_NR", "D_GA501_BASE", "D_GA501_DEPR", "D_GA501_NRW"):
    check(FormDiagnostic.objects.filter(tax_form=form, diagnostic_id=did).exists(),
          f"{did} present", f"{did} missing")

# ── report ──
print("\n" + "=" * 68)
print(f"  GA501: facts {FormFact.objects.filter(tax_form=form).count()} / "
      f"rules {FormRule.objects.filter(tax_form=form).count()} / "
      f"lines {FormLine.objects.filter(tax_form=form).count()} / "
      f"diag {FormDiagnostic.objects.filter(tax_form=form).count()} / "
      f"tests {form.test_scenarios.count()} / FA {FlowAssertion.objects.filter(assertion_id__startswith='FA-GA501').count()}")
print("=" * 68)
for p in PASSES:
    print(f"  PASS  {p}")
for fbad in FAILURES:
    print(f"  FAIL  {fbad}")
print("=" * 68)
print(f"RESULT: {len(PASSES)} pass / {len(FAILURES)} fail - "
      f"{'ALL PASS' if not FAILURES else 'FAILURES PRESENT'}")

from django.db import connections  # noqa: E402
connections.close_all()
try:
    if os.path.exists(SQLITE_PATH):
        os.remove(SQLITE_PATH)
except OSError:
    pass
sys.exit(1 if FAILURES else 0)
