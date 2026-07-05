"""Throwaway-SQLite validation for the state C-corp batch (WO-12): SC1120 + AL_FORM_20C + NC_CD405.

Checks CharField caps; every rule >= 1 authority link; rule_link coverage; arithmetic oracles
(SC 5% income + license fee + §179 excess; AL 6.5% + apportioned FIT deduction + GILTI; NC 2.25%
income + net-worth franchise table + 85% bonus/§179 add-back); key diagnostics; entity_types/jurisdiction.
ASCII-only prints. Run: poetry run python scratchpad/validate_state_ccorp.py
"""
import os
import sys

PROJECT_ROOT = r"D:\dev\sherpa-tax-rule-studio"
sys.path.insert(0, PROJECT_ROOT)

SQLITE_PATH = os.path.join(PROJECT_ROOT, "scratchpad", "validate_state_ccorp.sqlite3")
if os.path.exists(SQLITE_PATH):
    os.remove(SQLITE_PATH)
os.environ["DATABASE_URL"] = f"sqlite:///{SQLITE_PATH}"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

import django  # noqa: E402
django.setup()

from django.core.management import call_command  # noqa: E402
from specs.models import FlowAssertion, FormDiagnostic, FormFact, FormLine, FormRule, TaxForm  # noqa: E402
from sources.models import AuthorityTopic, RuleAuthorityLink  # noqa: E402
from specs.management.commands import load_sc1120 as SC  # noqa: E402
from specs.management.commands import load_al_form20c as AL  # noqa: E402
from specs.management.commands import load_nc_cd405 as NC  # noqa: E402

FAILURES: list[str] = []
PASSES: list[str] = []


def check(cond, ok, bad):
    (PASSES if cond else FAILURES).append(ok if cond else bad)


call_command("migrate", run_syncdb=True, verbosity=0)
for mod, cmd in ((SC, "load_sc1120"), (AL, "load_al_form20c"), (NC, "load_nc_cd405")):
    mod.READY_TO_SEED = True
    try:
        call_command(cmd, verbosity=0)
        PASSES.append(f"{cmd} ran + seeded into SQLite without error")
    except Exception as e:  # noqa: BLE001
        FAILURES.append(f"{cmd} raised: {e!r}")
        print("\n".join(FAILURES))
        sys.exit(1)

FORMS = {"SC1120": "SC", "AL_FORM_20C": "AL", "NC_CD405": "NC"}

# ── CharField caps ──
CAPS: dict = {}
for fn in FORMS:
    form = TaxForm.objects.get(form_number=fn)
    CAPS[f"form_number={fn}"] = (form.form_number, 50)
    for r in FormRule.objects.filter(tax_form=form):
        CAPS[f"rule_id={r.rule_id}"] = (r.rule_id, 20)
    for d in FormDiagnostic.objects.filter(tax_form=form):
        CAPS[f"diagnostic_id={d.diagnostic_id}"] = (d.diagnostic_id, 20)
    for ln in FormLine.objects.filter(tax_form=form):
        CAPS[f"line_number={ln.line_number}"] = (ln.line_number, 20)
    for fct in FormFact.objects.filter(tax_form=form):
        CAPS[f"fact_key={fct.fact_key}"] = (fct.fact_key, 100)
for pre in ("FA-SC1120", "FA-AL20C", "FA-NC405"):
    for fa in FlowAssertion.objects.filter(assertion_id__startswith=pre):
        CAPS[f"assertion_id={fa.assertion_id}"] = (fa.assertion_id, 20)
for t in AuthorityTopic.objects.all():
    CAPS[f"topic={t.topic_code}"] = (t.topic_name, 255)
viol = [f"{k}: len {len(v)} > {cap}" for k, (v, cap) in CAPS.items() if len(v) > cap]
check(not viol, f"CharField caps OK ({len(CAPS)} checked)", "CAP VIOLATIONS:\n    " + "\n    ".join(viol))

# ── every rule >= 1 authority link; rule_links reference defined rules ──
for fn, mod in ((("SC1120"), SC), (("AL_FORM_20C"), AL), (("NC_CD405"), NC)):
    form = TaxForm.objects.get(form_number=fn)
    ruleless = [r.rule_id for r in FormRule.objects.filter(tax_form=form)
                if not RuleAuthorityLink.objects.filter(form_rule=r).exists()]
    check(not ruleless, f"{fn}: all {FormRule.objects.filter(tax_form=form).count()} rules have >= 1 authority link",
          f"{fn}: rules with ZERO links: {ruleless}")
    defined = {r["rule_id"] for r in mod.F_RULES}
    linked = {rl[0] for rl in mod.F_RULE_LINKS}
    check(not (linked - defined), f"{fn}: rule_links reference defined rules", f"{fn}: orphan links {linked - defined}")
    check(not (defined - linked), f"{fn}: every rule appears in rule_links", f"{fn}: unlinked {defined - linked}")

# ══════════════════ ARITHMETIC ORACLES ══════════════════

# ── SC1120 ──
_, sc_tax = SC._sc_income_tax(200000, 0, 0, 0, 1.0)
check(round(sc_tax) == 10000, "SC: 200,000 x 5% = 10,000", f"SC tax wrong: {sc_tax}")
check(SC._sc_license_fee(500000) == 515, "SC license: 500,000×.001 + 15 = 515", f"SC license wrong: {SC._sc_license_fee(500000)}")
check(SC._sc_license_fee(5000) == 25, "SC license min: 5,000 -> $25", f"SC license min wrong: {SC._sc_license_fee(5000)}")
sc_179_excess = max(0, 2000000 - SC.SC_179_LIMIT)
_, sc_tax2 = SC._sc_income_tax(500000, sc_179_excess, 0, 0, 1.0)
check(sc_179_excess == 750000 and round(sc_tax2) == 62500, "SC §179 excess: 750,000 add -> 1,250,000 x 5% = 62,500", f"SC §179 wrong: {sc_179_excess}/{sc_tax2}")
check(SC.SC_179_LIMIT == 1250000 and SC.SC_179_PHASEOUT == 3130000, "SC §179 pre-OBBBA $1.25M/$3.13M", "SC §179 constants wrong")
sc_ti, _ = SC._sc_income_tax(300000, 0, 0, 100000, 1.0)
check(round(sc_ti) == 200000, "SC NOL: 300,000 - 100,000 = 200,000", f"SC NOL wrong: {sc_ti}")
check(FormDiagnostic.objects.filter(tax_form=TaxForm.objects.get(form_number="SC1120"), diagnostic_id="D_SC1120_H3368").exists(),
      "SC H.3368 live-wire diagnostic present", "SC H.3368 diagnostic missing")

# ── AL Form 20C ──
_, al_tax = AL._al_income_tax(1000000, 0, 0, 210000, 0, 1.0)
check(round(al_tax) == 51350, "AL: (1,000,000 - 210,000 FIT) x 6.5% = 51,350", f"AL tax wrong: {al_tax}")
al_ti, al_tax2 = AL._al_income_tax(1000000, 0, 0, 210000, 0, 0.25)
check(round(al_ti) == 197500 and round(al_tax2, 1) == 12837.5, "AL multistate: apportioned FIT 52,500 -> taxable 197,500 x 6.5% = 12,837.50", f"AL multistate wrong: {al_ti}/{al_tax2}")
_, al_tax3 = AL._al_income_tax(500000, 50000, 100000, 0, 0, 1.0)
check(round(al_tax3) == 29250, "AL GILTI: +50,000 §250 -100,000 §951A = 450,000 x 6.5% = 29,250", f"AL GILTI wrong: {al_tax3}")
_, al_tax4 = AL._al_income_tax(300000, 0, 0, 0, 0, 1.0)
check(round(al_tax4) == 19500, "AL no depr add-back (conforms): 300,000 x 6.5% = 19,500", f"AL no-depr wrong: {al_tax4}")
check(AL.AL_RATE == "0.065", "AL rate 6.5%", f"AL rate wrong: {AL.AL_RATE}")
check(FormDiagnostic.objects.filter(tax_form=TaxForm.objects.get(form_number="AL_FORM_20C"), diagnostic_id="D_AL20C_FIT").exists(),
      "AL FIT-deduction diagnostic present (constitutional)", "AL FIT diagnostic missing")

# ── NC CD-405 ──
_, nc_tax = NC._nc_income_tax(400000, 0, 0, 0, 1.0)
check(round(nc_tax) == 9000, "NC: 400,000 x 2.25% = 9,000", f"NC tax wrong: {nc_tax}")
check(NC._nc_franchise(100000) == 200, "NC franchise min: 100,000 -> $200", f"NC franchise min wrong: {NC._nc_franchise(100000)}")
check(NC._nc_franchise(500000) == 500, "NC franchise first-$1M cap: 500,000 -> $500", f"NC franchise cap wrong: {NC._nc_franchise(500000)}")
check(NC._nc_franchise(2000000) == 2000, "NC franchise over $1M: 2,000,000 -> $2,000", f"NC franchise >1M wrong: {NC._nc_franchise(2000000)}")
check(NC._nc_franchise(200000000, is_holding=True) == 150000, "NC franchise holding cap: 200M holding -> $150,000 (299,000 uncapped)", f"NC holding cap wrong: {NC._nc_franchise(200000000, is_holding=True)}")
nc_add_bonus = float(NC.ADDBACK_PCT) * 80000
_, nc_tax2 = NC._nc_income_tax(100000, nc_add_bonus, 0, 0, 1.0)
check(nc_add_bonus == 68000 and round(nc_tax2) == 3780, "NC 85% bonus: 68,000 add -> 168,000 x 2.25% = 3,780", f"NC bonus wrong: {nc_add_bonus}/{nc_tax2}")
nc_add_179 = float(NC.ADDBACK_PCT) * max(0, 100000 - NC.NC_179_LIMIT)
_, nc_tax3 = NC._nc_income_tax(500000, nc_add_179, 0, 0, 1.0)
check(nc_add_179 == 63750 and round(nc_tax3, 3) == 12684.375, "NC §179: 85% of (100,000-25,000)=63,750 -> 563,750 x 2.25% = 12,684.375", f"NC §179 wrong: {nc_add_179}/{nc_tax3}")
check(NC.NC_INCOME_RATE == "0.0225" and NC.NC_179_LIMIT == 25000, "NC rate 2.25% + §179 $25k", "NC constants wrong")
check(FormDiagnostic.objects.filter(tax_form=TaxForm.objects.get(form_number="NC_CD405"), diagnostic_id="D_NC405_FRANCH").exists(),
      "NC franchise diagnostic present", "NC franchise diagnostic missing")

# ── entity_types + jurisdiction ──
for fn, juris in FORMS.items():
    form = TaxForm.objects.get(form_number=fn)
    check(form.entity_types == ["1120"], f"{fn}: entity_types = ['1120']", f"{fn}: entity_types wrong: {form.entity_types}")
    check(form.jurisdiction == juris, f"{fn}: jurisdiction = {juris}", f"{fn}: jurisdiction wrong: {form.jurisdiction!r}")

# ── report ──
print("\n" + "=" * 70)
for fn in FORMS:
    form = TaxForm.objects.get(form_number=fn)
    print(f"  {fn}: facts {FormFact.objects.filter(tax_form=form).count()} / "
          f"rules {FormRule.objects.filter(tax_form=form).count()} / lines {FormLine.objects.filter(tax_form=form).count()} / "
          f"diag {FormDiagnostic.objects.filter(tax_form=form).count()} / tests {form.test_scenarios.count()}")
fa_ct = sum(FlowAssertion.objects.filter(assertion_id__startswith=p).count() for p in ("FA-SC1120", "FA-AL20C", "FA-NC405"))
print(f"  flow assertions: {fa_ct}")
print("=" * 70)
for p in PASSES:
    print(f"  PASS  {p}")
for fbad in FAILURES:
    print(f"  FAIL  {fbad}")
print("=" * 70)
print(f"RESULT: {len(PASSES)} pass / {len(FAILURES)} fail - {'ALL PASS' if not FAILURES else 'FAILURES PRESENT'}")

from django.db import connections  # noqa: E402
connections.close_all()
try:
    if os.path.exists(SQLITE_PATH):
        os.remove(SQLITE_PATH)
except OSError:
    pass
sys.exit(1 if FAILURES else 0)
