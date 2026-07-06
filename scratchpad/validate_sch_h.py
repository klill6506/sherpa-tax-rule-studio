"""Throwaway-SQLite validation for the Schedule H loader (WO-15).

Checks CharField caps; every rule >= 1 authority link; rule_link coverage; arithmetic oracles
(Part I FICA, Section A FUTA, Section B credit-reduction, gating, total); key diagnostics; entity_types.
ASCII-only. Run: poetry run python scratchpad/validate_sch_h.py
"""
import os
import sys

PROJECT_ROOT = r"D:\dev\sherpa-tax-rule-studio"
sys.path.insert(0, PROJECT_ROOT)

SQLITE_PATH = os.path.join(PROJECT_ROOT, "scratchpad", "validate_sch_h.sqlite3")
if os.path.exists(SQLITE_PATH):
    os.remove(SQLITE_PATH)
os.environ["DATABASE_URL"] = f"sqlite:///{SQLITE_PATH}"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

import django  # noqa: E402
django.setup()

from django.core.management import call_command  # noqa: E402
from specs.models import FlowAssertion, FormDiagnostic, FormFact, FormLine, FormRule, TaxForm  # noqa: E402
from sources.models import AuthorityTopic, RuleAuthorityLink  # noqa: E402
from specs.management.commands import load_sch_h as L  # noqa: E402

FAILURES: list[str] = []
PASSES: list[str] = []


def check(cond, ok, bad):
    (PASSES if cond else FAILURES).append(ok if cond else bad)


call_command("migrate", run_syncdb=True, verbosity=0)
L.READY_TO_SEED = True
try:
    call_command("load_sch_h", verbosity=0)
    PASSES.append("load_sch_h ran + seeded into SQLite without error")
except Exception as e:  # noqa: BLE001
    FAILURES.append(f"load_sch_h raised: {e!r}")
    print("\n".join(FAILURES))
    sys.exit(1)

form = TaxForm.objects.get(form_number="SCHEDULE_H")

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
for fa in FlowAssertion.objects.filter(assertion_id__startswith="FA-SCHH"):
    CAPS[f"assertion_id={fa.assertion_id}"] = (fa.assertion_id, 20)
for t in AuthorityTopic.objects.all():
    CAPS[f"topic={t.topic_code}"] = (t.topic_name, 255)
viol = [f"{k}: len {len(v)} > {cap}" for k, (v, cap) in CAPS.items() if len(v) > cap]
check(not viol, f"CharField caps OK ({len(CAPS)} checked)", "CAP VIOLATIONS:\n    " + "\n    ".join(viol))

# -- authority links --
ruleless = [r.rule_id for r in FormRule.objects.filter(tax_form=form)
            if not RuleAuthorityLink.objects.filter(form_rule=r).exists()]
check(not ruleless, f"all {FormRule.objects.filter(tax_form=form).count()} rules have >= 1 authority link", f"ruleless: {ruleless}")
defined = {r["rule_id"] for r in L.SCHH_RULES}
linked = {rl[0] for rl in L.SCHH_RULE_LINKS}
check(not (linked - defined), "rule_links reference defined rules", f"orphan: {linked - defined}")
check(not (defined - linked), "every rule appears in rule_links", f"unlinked: {defined - linked}")

# -- arithmetic oracles --
# SCHH-A: nanny, single state
a = L._fica(25000, 25000, 0, 0)
check(a["L2"] == 3100.0 and a["L4"] == 725.0 and a["L8"] == 3825.0, "A: L2 3,100 / L4 725 / L8 3,825", f"A FICA wrong: {a}")
fa16 = L._futa_section_a(7000)
check(fa16 == 42.0, "A: Section A FUTA 7,000 x 0.6% = 42", f"A FUTA wrong: {fa16}")
check(L._total_hh_tax(a["L8"], fa16, False) == 3867.0, "A: total 3,867", f"A total wrong: {L._total_hh_tax(a['L8'], fa16, False)}")
# SCHH-B: Additional Medicare + SS cap
b = L._fica(176100, 250000, 50000, 0)
check(b["L2"] == 21836.4, "B: SS capped 176,100 x 12.4% = 21,836.40", f"B L2 wrong: {b['L2']}")
check(b["L4"] == 7250.0, "B: Medicare 250,000 x 2.9% = 7,250", f"B L4 wrong: {b['L4']}")
check(b["L6"] == 450.0, "B: Add'l Medicare 50,000 x 0.9% = 450", f"B L6 wrong: {b['L6']}")
# SCHH-C: California credit-reduction (timely single CR state)
c = L._futa_section_b(7000, 378, L.CREDIT_REDUCTION_STATES_2025["CA"])
check(c == 126.0, "C: CA credit-reduction net = 7,000 x (0.6%+1.2%) = 126", f"C FUTA-B wrong: {c}")
# VI cross-check
vi = L._futa_section_b(7000, 378, L.CREDIT_REDUCTION_STATES_2025["VI"])
check(vi == 357.0, "C': VI net = 7,000 x (0.6%+4.5%) = 357 (eff 5.1%)", f"VI wrong: {vi}")
# SCHH-D: below thresholds
check(L._must_file(2000, False, 800) is False, "D: 2,000/no-FIT/800 -> must_file False (don't file)", "D must_file wrong")
check(L._must_file(2800, False, 0) is True, "D': exactly 2,800 -> must file (line A)", "D' 2,800 boundary wrong")
check(L._must_file(0, False, 1000) is True, "D'': 1,000/quarter -> must file (line C)", "D'' 1,000 boundary wrong")
# SCHH-E: FUTA only (line C yes, Part I skipped)
e16 = L._futa_section_a(4000)
check(e16 == 24.0 and L._total_hh_tax(9999, e16, True) == 24.0, "E: FUTA-only 4,000 x 0.6% = 24; L25=0 -> total 24", f"E wrong: {e16}/{L._total_hh_tax(9999, e16, True)}")
# SCHH-F: standalone
f = L._fica(12000, 12000, 0, 0)
check(f["L8"] == 1836.0, "F: L8 12,000 -> 1,488 + 348 = 1,836", f"F L8 wrong: {f['L8']}")
check(L._total_hh_tax(f["L8"], L._futa_section_a(7000), False) == 1878.0, "F: total 1,878", "F total wrong")
# constants
check(L.CASH_WAGE_THRESHOLD == 2800, "cash-wage trigger = $2,800 (2025, not $2,700)", f"threshold wrong: {L.CASH_WAGE_THRESHOLD}")
check(L.SS_WAGE_BASE == 176100 and L.FUTA_WAGE_BASE == 7000 and L.ADDL_MEDICARE_THRESHOLD == 200000, "SS base 176,100 / FUTA base 7,000 / Add'l-Med 200,000", "constants wrong")
check(L.CREDIT_REDUCTION_STATES_2025 == {"CA": "0.012", "VI": "0.045"}, "2025 credit-reduction states CA 1.2% / VI 4.5%", f"CR states wrong: {L.CREDIT_REDUCTION_STATES_2025}")
check(L.SS_RATE == "0.124" and L.MEDICARE_RATE == "0.029" and L.ADDL_MEDICARE_RATE == "0.009" and L.FUTA_NET_RATE == "0.006", "rates 12.4% / 2.9% / 0.9% / 0.6%", "rate constants wrong")

# -- key diagnostics + entity_types --
for did in ("D_SCHH_FILE", "D_SCHH_EXCL", "D_SCHH_SSBASE", "D_SCHH_ADDLMED", "D_SCHH_CREDREDUX", "D_SCHH_STANDALONE", "D_SCHH_EIN"):
    check(FormDiagnostic.objects.filter(tax_form=form, diagnostic_id=did).exists(), f"{did} present", f"{did} MISSING")
check(form.entity_types == ["1040"], "entity_types = [1040]", f"entity_types wrong: {form.entity_types}")

# -- report --
print("\n" + "=" * 66)
print(f"  SCHEDULE_H: facts {FormFact.objects.filter(tax_form=form).count()} / rules {FormRule.objects.filter(tax_form=form).count()} / "
      f"lines {FormLine.objects.filter(tax_form=form).count()} / diag {FormDiagnostic.objects.filter(tax_form=form).count()} / "
      f"tests {form.test_scenarios.count()} / FA {FlowAssertion.objects.filter(assertion_id__startswith='FA-SCHH').count()}")
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
