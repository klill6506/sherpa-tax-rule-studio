"""Throwaway-SQLite validation for the Form 4684 loader (WO-16).

Checks CharField caps; every rule >= 1 authority link; rule_link coverage; arithmetic oracles
(per-property loss/gain, Section A FDD gate + floors, qualified disaster, Section B total-destruction +
§1231 routing, Ponzi 95%/75%); key diagnostics; entity_types. ASCII-only. Run: poetry run python scratchpad/validate_4684.py
"""
import os
import sys

PROJECT_ROOT = r"D:\dev\sherpa-tax-rule-studio"
sys.path.insert(0, PROJECT_ROOT)

SQLITE_PATH = os.path.join(PROJECT_ROOT, "scratchpad", "validate_4684.sqlite3")
if os.path.exists(SQLITE_PATH):
    os.remove(SQLITE_PATH)
os.environ["DATABASE_URL"] = f"sqlite:///{SQLITE_PATH}"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

import django  # noqa: E402
django.setup()

from django.core.management import call_command  # noqa: E402
from specs.models import FlowAssertion, FormDiagnostic, FormFact, FormLine, FormRule, TaxForm  # noqa: E402
from sources.models import AuthorityTopic, RuleAuthorityLink  # noqa: E402
from specs.management.commands import load_4684 as L  # noqa: E402

FAILURES: list[str] = []
PASSES: list[str] = []


def check(cond, ok, bad):
    (PASSES if cond else FAILURES).append(ok if cond else bad)


call_command("migrate", run_syncdb=True, verbosity=0)
L.READY_TO_SEED = True
try:
    call_command("load_4684", verbosity=0)
    PASSES.append("load_4684 ran + seeded into SQLite without error")
except Exception as e:  # noqa: BLE001
    FAILURES.append(f"load_4684 raised: {e!r}")
    print("\n".join(FAILURES))
    sys.exit(1)

form = TaxForm.objects.get(form_number="4684")

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
for fa in FlowAssertion.objects.filter(assertion_id__startswith="FA-4684"):
    CAPS[f"assertion_id={fa.assertion_id}"] = (fa.assertion_id, 20)
for t in AuthorityTopic.objects.all():
    CAPS[f"topic={t.topic_code}"] = (t.topic_name, 255)
viol = [f"{k}: len {len(v)} > {cap}" for k, (v, cap) in CAPS.items() if len(v) > cap]
check(not viol, f"CharField caps OK ({len(CAPS)} checked)", "CAP VIOLATIONS:\n    " + "\n    ".join(viol))

# -- authority links --
ruleless = [r.rule_id for r in FormRule.objects.filter(tax_form=form)
            if not RuleAuthorityLink.objects.filter(form_rule=r).exists()]
check(not ruleless, f"all {FormRule.objects.filter(tax_form=form).count()} rules have >= 1 authority link", f"ruleless: {ruleless}")
defined = {r["rule_id"] for r in L.F4684_RULES}
linked = {rl[0] for rl in L.F4684_RULE_LINKS}
check(not (linked - defined), "rule_links reference defined rules", f"orphan: {linked - defined}")
check(not (defined - linked), "every rule appears in rule_links", f"unlinked: {defined - linked}")

# -- arithmetic oracles --
# A: personal disaster loss
a = L._casualty_item(30000, 30000, 10000, 5000)
check(a["loss"] == 15000.0, "A: item loss = min(30000, 20000 decline) - 5000 = 15,000", f"A item wrong: {a}")
ad = L._section_a_deduction(15000, 0, True, False, 60000)
check(ad == 8900.0, "A: Section A deductible = 14,900 - 6,000 (10% AGI) = 8,900", f"A deduction wrong: {ad}")
# B: non-disaster personal -> 0
check(L._section_a_deduction(15000, 0, False, False, 60000) == 0.0, "B: non-disaster personal loss -> 0 (FDD gate)", "B FDD gate wrong")
# C: qualified disaster ($500, no AGI)
cd = L._section_a_deduction(20000, 0, True, True, 60000)
check(cd == 19500.0, "C: qualified disaster 20,000 - 500 floor, no AGI = 19,500", f"C qual-dis wrong: {cd}")
# D: business total destruction -> full basis
d = L._casualty_item(50000, 45000, 0, 20000, total_destruction=True)
check(d["loss"] == 30000.0, "D: total destruction full basis 50,000 - 20,000 = 30,000 (FMV ignored)", f"D item wrong: {d}")
check(L._section_b_route(0, 30000, True) == "4797_L14_ordinary", "D: >1yr loss>gain -> 4797 L14 ordinary", "D route wrong")
# D counterfactual: partial casualty would use FMV decline
dpart = L._casualty_item(50000, 45000, 0, 20000, total_destruction=False)
check(dpart["loss"] == 25000.0, "D': partial (not total) uses FMV decline 45,000 - 20,000 = 25,000", f"D' wrong: {dpart}")
# E: casualty gain (insurance > basis)
e = L._casualty_item(20000, 40000, 0, 35000)
check(e["gain"] == 15000.0 and e["loss"] == 0.0, "E: insurance 35,000 > basis 20,000 -> gain 15,000", f"E wrong: {e}")
check(L._section_b_route(15000, 0, True) == "4797_L3_1231", "E: >1yr gain>=loss -> 4797 L3 §1231", "E route wrong")
# F: Ponzi 95% / 75%
check(L._ponzi_deduction(100000, False, 10000, 0) == 85000.0, "F: Ponzi 95% x 100,000 - 10,000 = 85,000", "F Ponzi 95 wrong")
check(L._ponzi_deduction(100000, True, 10000, 0) == 65000.0, "F': Ponzi 75% (pursuing recovery) x 100,000 - 10,000 = 65,000", "F' Ponzi 75 wrong")
# G: financial scam -> Section B loss, no FDD gate
g = L._casualty_item(40000, 40000, 0, 0)
check(g["loss"] == 40000.0, "G: financial-scam Section B loss 40,000 (not FDD-limited)", f"G wrong: {g}")
# constants
check(L.PERSONAL_FLOOR == 100 and L.QUALIFIED_DISASTER_FLOOR == 500 and L.AGI_FLOOR_PCT == "0.10", "floors $100 / $500 / 10% AGI", "floor constants wrong")
check(L.PONZI_FACTOR_NO_RECOVERY == "0.95" and L.PONZI_FACTOR_POTENTIAL_RECOVERY == "0.75", "Ponzi factors 95% / 75%", "Ponzi constants wrong")
check(L.QUALIFIED_DISASTER_WINDOW["declared_end"] == "2025-09-02", "qualified-disaster window ends 2025-09-02 (OBBBA)", f"window wrong: {L.QUALIFIED_DISASTER_WINDOW}")

# -- key diagnostics + entity_types --
for did in ("D_4684_FDD", "D_4684_QUALDIS", "D_4684_TOTALDEST", "D_4684_1231", "D_4684_PONZI", "D_4684_SCAM", "D_4684_165I", "D_4684_RECOVERY"):
    check(FormDiagnostic.objects.filter(tax_form=form, diagnostic_id=did).exists(), f"{did} present", f"{did} MISSING")
check(form.entity_types == ["1040", "1065", "1120S", "1120"], "entity_types = [1040,1065,1120S,1120]", f"entity_types wrong: {form.entity_types}")

# -- report --
print("\n" + "=" * 66)
print(f"  4684: facts {FormFact.objects.filter(tax_form=form).count()} / rules {FormRule.objects.filter(tax_form=form).count()} / "
      f"lines {FormLine.objects.filter(tax_form=form).count()} / diag {FormDiagnostic.objects.filter(tax_form=form).count()} / "
      f"tests {form.test_scenarios.count()} / FA {FlowAssertion.objects.filter(assertion_id__startswith='FA-4684').count()}")
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
