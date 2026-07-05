"""Throwaway-SQLite validation harness for the Form 1041 spine loader (leg a).

Mirrors the established validate_ga/validate_nc pattern:
  - seeds the loader into a fresh SQLite DB (catches structural/JSON/unique errors),
  - explicitly enforces the CharField caps SQLite ignores but Postgres enforces
    (rule_id/diagnostic_id/line_number/assertion_id <= 20; topic_name <= 255;
     fact_key <= 100; form_number <= 50),
  - checks every FormRule has >= 1 authority link (the zero-link warning-badge rule),
  - spot-checks the scenario arithmetic (exemptions, rate schedule, DNI, IDD, tiers).

Run: poetry run python scratchpad/validate_1041.py
"""
import os
import sys

PROJECT_ROOT = r"D:\dev\sherpa-tax-rule-studio"
sys.path.insert(0, PROJECT_ROOT)

# Throwaway SQLite — never touches Supabase.
SQLITE_PATH = os.path.join(PROJECT_ROOT, "scratchpad", "validate_1041.sqlite3")
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
from specs.management.commands import load_1041_spine as L  # noqa: E402

FAILURES: list[str] = []
PASSES: list[str] = []


def check(cond: bool, ok: str, bad: str):
    (PASSES if cond else FAILURES).append(ok if cond else bad)


# ── 1. migrate + seed (patch the READY_TO_SEED guard for the throwaway DB) ──
call_command("migrate", run_syncdb=True, verbosity=0)
L.READY_TO_SEED = True
try:
    call_command("load_1041_spine", verbosity=1)
    PASSES.append("loader ran + seeded into SQLite without error")
except Exception as e:  # noqa: BLE001
    FAILURES.append(f"loader raised: {e!r}")
    print("\n".join(FAILURES))
    sys.exit(1)

form = TaxForm.objects.get(form_number="1041")

# ── 2. CharField caps (SQLite ignores; Postgres enforces) ──
CAPS = {
    "form_number(50)": (form.form_number, 50),
}
for fn, cap in [("rule_id", 20)]:
    for r in FormRule.objects.filter(tax_form=form):
        CAPS[f"rule_id={r.rule_id}"] = (r.rule_id, cap)
for d in FormDiagnostic.objects.filter(tax_form=form):
    CAPS[f"diagnostic_id={d.diagnostic_id}"] = (d.diagnostic_id, 20)
for ln in FormLine.objects.filter(tax_form=form):
    CAPS[f"line_number={ln.line_number}"] = (ln.line_number, 20)
for fa in FlowAssertion.objects.all():
    CAPS[f"assertion_id={fa.assertion_id}"] = (fa.assertion_id, 20)
for fct in FormFact.objects.filter(tax_form=form):
    CAPS[f"fact_key={fct.fact_key}"] = (fct.fact_key, 100)
for t in AuthorityTopic.objects.all():
    CAPS[f"topic_name={t.topic_code}"] = (t.topic_name, 255)

cap_violations = [f"{k}: len {len(v)} > {cap}" for k, (v, cap) in CAPS.items() if len(v) > cap]
check(not cap_violations, f"CharField caps OK ({len(CAPS)} checked)",
      "CAP VIOLATIONS:\n    " + "\n    ".join(cap_violations))

# ── 3. every rule has >= 1 authority link ──
ruleless = []
for r in FormRule.objects.filter(tax_form=form):
    if not RuleAuthorityLink.objects.filter(form_rule=r).exists():
        ruleless.append(r.rule_id)
check(not ruleless, f"all {FormRule.objects.filter(tax_form=form).count()} rules have >= 1 authority link",
      f"rules with ZERO authority links: {ruleless}")

# rule_links reference only defined rules
defined_rules = {r["rule_id"] for r in L.F1041_RULES}
linked_rules = {rl[0] for rl in L.F1041_RULE_LINKS}
orphan_links = linked_rules - defined_rules
check(not orphan_links, "all rule_links reference defined rules",
      f"rule_links reference undefined rules: {orphan_links}")
unlinked = defined_rules - linked_rules
check(not unlinked, "every defined rule appears in rule_links",
      f"defined rules missing from rule_links: {unlinked}")

# ── 4. arithmetic spot-checks (the scenario oracles) ──
# exemptions
check(L.EXEMPTION_2025 == {"estate": 600, "simple_trust": 300, "complex_trust": 100, "qdist": 5100},
      "exemptions $600/$300/$100/$5,100 correct", f"exemptions wrong: {L.EXEMPTION_2025}")

# rate schedule (half-up): T3 estate taxable 19,400 -> 5,165 ; T4 qdist 2,900 -> 290
check(L._rate_schedule_tax(19400) == 5165, "rate: tax(19,400) = 5,165 (3,777 + 37% x 3,750, half-up)",
      f"rate: tax(19,400) = {L._rate_schedule_tax(19400)} (want 5,165)")
check(L._rate_schedule_tax(2900) == 290, "rate: tax(2,900) = 290 (10%)",
      f"rate: tax(2,900) = {L._rate_schedule_tax(2900)} (want 290)")
# bracket boundaries
check(L._rate_schedule_tax(3150) == 315, "rate: tax(3,150) = 315 (bracket 1 top)",
      f"rate: tax(3,150) = {L._rate_schedule_tax(3150)} (want 315)")
check(L._rate_schedule_tax(15650) == 3777, "rate: tax(15,650) = 3,777 (top bracket start)",
      f"rate: tax(15,650) = {L._rate_schedule_tax(15650)} (want 3,777)")


# DNI / IDD / tiers recomputation (mirrors R-1041-DNI / R-1041-IDD / R-1041-TIERS)
def compute(entity, *, income=0, cap_gain=0, cg_in_dni=0, tax_exempt=0, te_exp=0,
            required=0, other=0, te_in_dist=0):
    l17 = income + cap_gain
    dni = max(0, l17 + max(0, tax_exempt - te_exp) + cg_in_dni - cap_gain)
    l2 = max(0, tax_exempt - te_exp)
    distributions = required + other
    l13 = distributions - te_in_dist
    l14 = max(0, dni - l2)
    idd = min(l13, l14)
    taxable_dni = dni - l2
    tier1 = min(required, taxable_dni)
    tier2 = min(other, max(0, taxable_dni - required))
    exemption = L.EXEMPTION_2025.get(entity, 0)
    l23 = max(0, l17 - idd - exemption)
    return dict(L17=l17, DNI=dni, IDD=idd, tier1=tier1, tier2=tier2, L21=exemption, L23=l23)

# T1 simple trust all distributed
t1 = compute("simple_trust", income=15000, required=15000)
check(t1["DNI"] == 15000 and t1["IDD"] == 15000 and t1["L23"] == 0,
      "T1 simple trust: DNI 15,000 / IDD 15,000 / L23 0", f"T1 wrong: {t1}")
# T2 complex partial
t2 = compute("complex_trust", income=30000, other=10000)
check(t2["DNI"] == 30000 and t2["IDD"] == 10000 and t2["L23"] == 19900,
      "T2 complex trust: DNI 30,000 / IDD 10,000 / L23 19,900", f"T2 wrong: {t2}")
# T5 two-tier
t5 = compute("complex_trust", income=20000, required=12000, other=15000)
check(t5["tier1"] == 12000 and t5["tier2"] == 8000 and t5["IDD"] == 20000,
      "T5 tiers: tier1 12,000 / tier2 8,000 (DNI 20,000) / IDD 20,000", f"T5 wrong: {t5}")
# T8 corpus cap gain excluded from DNI
t8 = compute("complex_trust", income=10000, cap_gain=40000, cg_in_dni=0, required=10000)
check(t8["DNI"] == 10000 and t8["IDD"] == 10000 and t8["L23"] == 39900,
      "T8 corpus cap gain excluded: DNI 10,000 / IDD 10,000 / L23 39,900 (trust taxed on gain)",
      f"T8 wrong: {t8}")

# ── 5. counts + NIIT/capgain constants ──
check(L.NIIT_THRESHOLD_2025 == 15650, "NIIT threshold = $15,650 (top-bracket start)",
      f"NIIT threshold wrong: {L.NIIT_THRESHOLD_2025}")
check(L.CAPGAIN_0_CEILING_2025 == 3250 and L.CAPGAIN_15_CEILING_2025 == 15900,
      "cap-gain breakpoints $3,250 / $15,900", "cap-gain breakpoints wrong")
check(FormDiagnostic.objects.filter(tax_form=form, diagnostic_id="D_1041_AMT").exists(),
      "D_1041_AMT (Sch I RED-defer, D-2) present", "D_1041_AMT missing")

# ── report ──
print("\n" + "=" * 68)
print(f"  1041 spine: facts {FormFact.objects.filter(tax_form=form).count()} / "
      f"rules {FormRule.objects.filter(tax_form=form).count()} / "
      f"lines {FormLine.objects.filter(tax_form=form).count()} / "
      f"diag {FormDiagnostic.objects.filter(tax_form=form).count()} / "
      f"tests {form.test_scenarios.count()} / FA {FlowAssertion.objects.count()}")
print("=" * 68)
for p in PASSES:
    print(f"  PASS  {p}")
for fbad in FAILURES:
    print(f"  FAIL  {fbad}")
print("=" * 68)
print(f"RESULT: {len(PASSES)} pass / {len(FAILURES)} fail — "
      f"{'ALL PASS' if not FAILURES else 'FAILURES PRESENT'}")
from django.db import connections  # noqa: E402
connections.close_all()
try:
    if os.path.exists(SQLITE_PATH):
        os.remove(SQLITE_PATH)
except OSError:
    pass  # throwaway; harmless if still locked
sys.exit(1 if FAILURES else 0)
