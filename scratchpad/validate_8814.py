"""Throwaway-SQLite validation for the Form 8814 loader (WO-19).

Checks CharField caps; every rule >= 1 authority link; rule_link coverage; arithmetic oracles
(line 4, Part I proportional allocation + carries, Part II tax $135/10%, eligibility gates); key
diagnostics; entity_types. ASCII-only. Run: poetry run python scratchpad/validate_8814.py
"""
import os
import sys

PROJECT_ROOT = r"D:\dev\sherpa-tax-rule-studio"
sys.path.insert(0, PROJECT_ROOT)

SQLITE_PATH = os.path.join(PROJECT_ROOT, "scratchpad", "validate_8814.sqlite3")
if os.path.exists(SQLITE_PATH):
    os.remove(SQLITE_PATH)
os.environ["DATABASE_URL"] = f"sqlite:///{SQLITE_PATH}"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

import django  # noqa: E402
django.setup()

from django.core.management import call_command  # noqa: E402
from specs.models import FlowAssertion, FormDiagnostic, FormFact, FormLine, FormRule, TaxForm  # noqa: E402
from sources.models import AuthorityTopic, RuleAuthorityLink  # noqa: E402
from specs.management.commands import load_8814 as L  # noqa: E402

FAILURES: list[str] = []
PASSES: list[str] = []


def check(cond, ok, bad):
    (PASSES if cond else FAILURES).append(ok if cond else bad)


call_command("migrate", run_syncdb=True, verbosity=0)
L.READY_TO_SEED = True
try:
    call_command("load_8814", verbosity=0)
    PASSES.append("load_8814 ran + seeded into SQLite without error")
except Exception as e:  # noqa: BLE001
    FAILURES.append(f"load_8814 raised: {e!r}")
    print("\n".join(FAILURES))
    sys.exit(1)

form = TaxForm.objects.get(form_number="8814")

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
for fa in FlowAssertion.objects.filter(assertion_id__startswith="FA-8814"):
    CAPS[f"assertion_id={fa.assertion_id}"] = (fa.assertion_id, 20)
for t in AuthorityTopic.objects.all():
    CAPS[f"topic={t.topic_code}"] = (t.topic_name, 255)
viol = [f"{k}: len {len(v)} > {cap}" for k, (v, cap) in CAPS.items() if len(v) > cap]
check(not viol, f"CharField caps OK ({len(CAPS)} checked)", "CAP VIOLATIONS:\n    " + "\n    ".join(viol))

# -- authority links --
ruleless = [r.rule_id for r in FormRule.objects.filter(tax_form=form)
            if not RuleAuthorityLink.objects.filter(form_rule=r).exists()]
check(not ruleless, f"all {FormRule.objects.filter(tax_form=form).count()} rules have >= 1 authority link", f"ruleless: {ruleless}")
defined = {r["rule_id"] for r in L.F8814_RULES}
linked = {rl[0] for rl in L.F8814_RULE_LINKS}
check(not (linked - defined), "rule_links reference defined rules", f"orphan: {linked - defined}")
check(not (defined - linked), "every rule appears in rule_links", f"unlinked: {defined - linked}")

# -- arithmetic oracles --
# A: full allocation
l4 = L._line4(2000, 2000, 1000)
check(l4 == 5000.0, "A: L4 = 2,000+2,000+1,000 = 5,000", f"A L4 wrong: {l4}")
alloc = L._part1_allocation(5000, 1000, 1000)
check(alloc["L6"] == 2300.0 and alloc["L9"] == 460.0 and alloc["L10"] == 460.0 and alloc["L12"] == 1380.0,
      "A: L6 2,300 / L9 460 QD / L10 460 capgain / L12 1,380 ordinary", f"A alloc wrong: {alloc}")
check(round(alloc["L9"] + alloc["L10"] + alloc["L12"], 2) == alloc["L6"], "A: L9+L10+L12 == L6 (character split conserves)", "A conservation wrong")
check(L._part2_tax(5000) == 135.0, "A: Part II L14 3,650 >= 1,350 -> L15 $135", "A tax wrong")
# B: <= 2700 Part II only
check(L._line4(2000, 500, 0) == 2500.0 and L._part1_allocation(2500, 0, 0)["L6"] == 0.0, "B: L4 2,500 <= 2,700 -> Part I skipped", "B skip wrong")
check(L._part2_tax(2500) == 115.0, "B: L14 1,150 < 1,350 -> L15 = 1,150 x 10% = 115", f"B tax wrong: {L._part2_tax(2500)}")
# C: >= 13500 don't file
check(L._line4(14000, 0, 0) == 14000.0, "C: L4 14,000 (>= 13,500 -> don't file)", "C L4 wrong")
# E: second tier under 1350
check(L._part2_tax(2000) == 65.0, "E: L14 650 < 1,350 -> L15 = 650 x 10% = 65", f"E tax wrong: {L._part2_tax(2000)}")
# boundary: exactly 2700 -> Part II only, L14 1350 -> 135
check(L._part2_tax(2700) == 135.0, "boundary: L4 2,700 -> L14 1,350 -> L15 $135 (flat)", f"boundary wrong: {L._part2_tax(2700)}")
# D/F: eligibility
check(L._can_elect(True, True, 5000, True, True, True, False, True) is False, "D: withholding present -> can_elect False", "D elig wrong")
check(L._can_elect(True, True, 5000, True, True, True, True, True) is True, "F: all 8 conditions + gross 5,000<13,500 -> can_elect True", "F elig wrong")
check(L._can_elect(True, True, 13500, True, True, True, True, True) is False, "gross 13,500 (not < 13,500) -> can_elect False", "gross-boundary wrong")
# constants
check(L.BASE_AMOUNT == 2700 and L.NOT_TAXED == 1350 and L.SECOND_TIER_FLAT_TAX == 135 and L.DONT_FILE_CEILING == 13500,
      "2025 figures $2,700 / $1,350 / $135 / $13,500", "constants wrong")

# -- key diagnostics + entity_types --
for did in ("D_8814_ELIG", "D_8814_DONTFILE", "D_8814_SKIP", "D_8814_CHEAPER", "D_8814_8615", "D_8814_CARRY", "D_8814_MULTI"):
    check(FormDiagnostic.objects.filter(tax_form=form, diagnostic_id=did).exists(), f"{did} present", f"{did} MISSING")
check(form.entity_types == ["1040"], "entity_types = [1040]", f"entity_types wrong: {form.entity_types}")

# -- report --
print("\n" + "=" * 66)
print(f"  8814: facts {FormFact.objects.filter(tax_form=form).count()} / rules {FormRule.objects.filter(tax_form=form).count()} / "
      f"lines {FormLine.objects.filter(tax_form=form).count()} / diag {FormDiagnostic.objects.filter(tax_form=form).count()} / "
      f"tests {form.test_scenarios.count()} / FA {FlowAssertion.objects.filter(assertion_id__startswith='FA-8814').count()}")
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
