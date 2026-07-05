"""Throwaway-SQLite validation for the Form 5227 loader (WO-10).

Checks: CharField caps; every rule >= 1 authority link; rule_link coverage;
arithmetic (§664(b) four-tier ordering, accumulation carryforward, §664(c)(2) UBTI
excise); key diagnostics present. ASCII-only prints (cp1252 console).

Run: poetry run python scratchpad/validate_5227.py
"""
import os
import sys

PROJECT_ROOT = r"D:\dev\sherpa-tax-rule-studio"
sys.path.insert(0, PROJECT_ROOT)

SQLITE_PATH = os.path.join(PROJECT_ROOT, "scratchpad", "validate_5227.sqlite3")
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
from sources.models import AuthorityTopic, RuleAuthorityLink  # noqa: E402
from specs.management.commands import load_5227 as L  # noqa: E402

FAILURES: list[str] = []
PASSES: list[str] = []


def check(cond, ok, bad):
    (PASSES if cond else FAILURES).append(ok if cond else bad)


call_command("migrate", run_syncdb=True, verbosity=0)
L.READY_TO_SEED = True
try:
    call_command("load_5227", verbosity=1)
    PASSES.append("loader ran + seeded into SQLite without error")
except Exception as e:  # noqa: BLE001
    FAILURES.append(f"loader raised: {e!r}")
    print("\n".join(FAILURES))
    sys.exit(1)

form = TaxForm.objects.get(form_number="5227")

# ── CharField caps ──
CAPS = {"form_number(50)": (form.form_number, 50)}
for r in FormRule.objects.filter(tax_form=form):
    CAPS[f"rule_id={r.rule_id}"] = (r.rule_id, 20)
for d in FormDiagnostic.objects.filter(tax_form=form):
    CAPS[f"diagnostic_id={d.diagnostic_id}"] = (d.diagnostic_id, 20)
for ln in FormLine.objects.filter(tax_form=form):
    CAPS[f"line_number={ln.line_number}"] = (ln.line_number, 20)
for fa in FlowAssertion.objects.filter(assertion_id__startswith="FA-5227"):
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
check(not ruleless, f"all {FormRule.objects.filter(tax_form=form).count()} rules have >= 1 authority link",
      f"rules with ZERO authority links: {ruleless}")
defined = {r["rule_id"] for r in L.F5227_RULES}
linked = {rl[0] for rl in L.F5227_RULE_LINKS}
check(not (linked - defined), "all rule_links reference defined rules", f"orphan links: {linked - defined}")
check(not (defined - linked), "every defined rule appears in rule_links", f"unlinked rules: {defined - linked}")

# ── arithmetic: four-tier ordering (the loader's own helper) ──
# T1 CRUT: ord 10k, cap 20k, dist 25k
t1 = L._four_tier(25000, 10000, 20000, 0)
check(t1 == (10000, 15000, 0, 0), "T1 tiers: ord 10,000 / capgain 15,000 / other 0 / corpus 0",
      f"T1 wrong: {t1}")
carry_cap = max(0, 20000 - t1[1])
check(carry_cap == 5000, "T1 accum: capital gain carryforward 5,000", f"T1 carry wrong: {carry_cap}")
# T2 corpus reached: ord 5k, cap 3k, dist 12k
t2 = L._four_tier(12000, 5000, 3000, 0)
check(t2 == (5000, 3000, 0, 4000), "T2 tiers: ord 5,000 / capgain 3,000 / corpus 4,000 (reaches corpus)",
      f"T2 wrong: {t2}")
# T3 accumulation: prior ord 8k + current 4k, dist 10k
avail_ord = 8000 + 4000
t3 = L._four_tier(10000, avail_ord, 0, 0)
carry_ord = max(0, avail_ord - t3[0])
check(t3[0] == 10000 and carry_ord == 2000,
      "T3 accum: prior undistributed ordinary carries into Tier 1 (t1 10,000 / carry 2,000)",
      f"T3 wrong: t1={t3[0]} carry={carry_ord}")
# tiers sum to distribution
check(sum(t2) == 12000, "tiers sum to the distribution amount (t1+t2+t3+t4)", f"tier sum wrong: {sum(t2)}")

# T4 UBTI excise = 100%
ubti = 5000
check(round(ubti * float(L.UBTI_EXCISE_RATE)) == 5000, "T4 UBTI: §664(c)(2) excise = 100% of 5,000 = 5,000",
      "T4 UBTI excise wrong")
check(L.UBTI_POST2006_YEAR == 2007, "UBTI year-keyed post-2006 (2007)", f"UBTI year wrong: {L.UBTI_POST2006_YEAR}")

# ── constants + diagnostics ──
check(L.CRT_PAYOUT_MIN == "0.05" and L.CRT_PAYOUT_MAX == "0.50", "payout range 5%-50%", "payout range wrong")
check(L.CRT_MIN_REMAINDER == "0.10" and L.CRT_EXHAUSTION_MAX == "0.05",
      "10% min remainder / 5% exhaustion", "remainder/exhaustion constants wrong")
for did in ("D_5227_TIERS", "D_5227_UBTI", "D_5227_QUAL_PAY", "D_5227_PIF", "D_5227_CLT", "D_5227_NETTING"):
    check(FormDiagnostic.objects.filter(tax_form=form, diagnostic_id=did).exists(),
          f"{did} present", f"{did} missing")

# ── report ──
print("\n" + "=" * 68)
print(f"  5227: facts {FormFact.objects.filter(tax_form=form).count()} / "
      f"rules {FormRule.objects.filter(tax_form=form).count()} / "
      f"lines {FormLine.objects.filter(tax_form=form).count()} / "
      f"diag {FormDiagnostic.objects.filter(tax_form=form).count()} / "
      f"tests {form.test_scenarios.count()} / FA {FlowAssertion.objects.filter(assertion_id__startswith='FA-5227').count()}")
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
