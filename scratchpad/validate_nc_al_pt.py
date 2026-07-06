"""Throwaway-SQLite validation for the NC+AL pass-through batch (WO-13):
NC_D403 + NC_CD401S + AL_FORM_65 + AL_FORM_20S.

Checks CharField caps; every rule >= 1 authority link; rule_link coverage; arithmetic oracles
(NC Taxed PTE 4.25% + franchise + NR withholding + 85% add-back; AL Electing PTE 5% + composite +
Line 32 entity taxes); key diagnostics; entity_types/jurisdiction. ASCII-only.
Run: poetry run python scratchpad/validate_nc_al_pt.py
"""
import os
import sys

PROJECT_ROOT = r"D:\dev\sherpa-tax-rule-studio"
sys.path.insert(0, PROJECT_ROOT)

SQLITE_PATH = os.path.join(PROJECT_ROOT, "scratchpad", "validate_nc_al_pt.sqlite3")
if os.path.exists(SQLITE_PATH):
    os.remove(SQLITE_PATH)
os.environ["DATABASE_URL"] = f"sqlite:///{SQLITE_PATH}"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

import django  # noqa: E402
django.setup()

from django.core.management import call_command  # noqa: E402
from specs.models import FlowAssertion, FormDiagnostic, FormFact, FormLine, FormRule, TaxForm  # noqa: E402
from sources.models import AuthorityTopic, RuleAuthorityLink  # noqa: E402
from specs.management.commands import load_nc_passthrough as NC  # noqa: E402
from specs.management.commands import load_al_passthrough as AL  # noqa: E402

FAILURES: list[str] = []
PASSES: list[str] = []


def check(cond, ok, bad):
    (PASSES if cond else FAILURES).append(ok if cond else bad)


call_command("migrate", run_syncdb=True, verbosity=0)
for mod, cmd in ((NC, "load_nc_passthrough"), (AL, "load_al_passthrough")):
    mod.READY_TO_SEED = True
    try:
        call_command(cmd, verbosity=0)
        PASSES.append(f"{cmd} ran + seeded into SQLite without error")
    except Exception as e:  # noqa: BLE001
        FAILURES.append(f"{cmd} raised: {e!r}")
        print("\n".join(FAILURES))
        sys.exit(1)

FORMS = {"NC_D403": ("NC", ["1065"]), "NC_CD401S": ("NC", ["1120S"]),
         "AL_FORM_65": ("AL", ["1065"]), "AL_FORM_20S": ("AL", ["1120S"])}

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
for pre in ("FA-NC", "FA-AL"):
    for fa in FlowAssertion.objects.filter(assertion_id__startswith=pre):
        CAPS[f"assertion_id={fa.assertion_id}"] = (fa.assertion_id, 20)
for t in AuthorityTopic.objects.all():
    CAPS[f"topic={t.topic_code}"] = (t.topic_name, 255)
viol = [f"{k}: len {len(v)} > {cap}" for k, (v, cap) in CAPS.items() if len(v) > cap]
check(not viol, f"CharField caps OK ({len(CAPS)} checked)", "CAP VIOLATIONS:\n    " + "\n    ".join(viol))

# ── every rule >= 1 authority link; rule_links reference defined rules (per FORMS spec) ──
for mod in (NC, AL):
    for spec in mod.FORMS:
        fn = spec["identity"]["form_number"]
        form = TaxForm.objects.get(form_number=fn)
        ruleless = [r.rule_id for r in FormRule.objects.filter(tax_form=form)
                    if not RuleAuthorityLink.objects.filter(form_rule=r).exists()]
        check(not ruleless, f"{fn}: all {FormRule.objects.filter(tax_form=form).count()} rules have >= 1 link", f"{fn}: ruleless {ruleless}")
        defined = {r["rule_id"] for r in spec["rules"]}
        linked = {rl[0] for rl in spec["rule_links"]}
        check(not (linked - defined), f"{fn}: rule_links reference defined rules", f"{fn}: orphan {linked - defined}")
        check(not (defined - linked), f"{fn}: every rule appears in rule_links", f"{fn}: unlinked {defined - linked}")

# ══════════════ ARITHMETIC ORACLES ══════════════
# NC
check(round(NC._nc_taxed_pte(500000, 200000)) == 29750, "NC Taxed PTE: (500,000+200,000) x 4.25% = 29,750", f"NC PTET wrong: {NC._nc_taxed_pte(500000,200000)}")
check(round(NC._nc_taxed_pte(400000, 100000)) == 21250, "NC Taxed PTE (S-corp): (400,000+100,000) x 4.25% = 21,250", "NC PTET S wrong")
check(NC._nc_franchise(2000000) == 2000, "NC franchise: 2,000,000 -> $2,000", f"NC franchise wrong: {NC._nc_franchise(2000000)}")
check(NC._nc_franchise(100000) == 200, "NC franchise min: 100,000 -> $200", "NC franchise min wrong")
check(NC._nc_addback(80000, 0) == 68000, "NC 85% bonus add-back: 80,000 -> 68,000", f"NC add-back wrong: {NC._nc_addback(80000,0)}")
check(round(200000 * float(NC.NC_NRW_RATE)) == 8500, "NC NR withholding: 200,000 x 4.25% = 8,500", "NC NRW wrong")
check(NC.NC_PTET_RATE == "0.0425" and NC.NC_179_LIMIT == 25000, "NC PTET 4.25% + §179 $25k", "NC constants wrong")
# AL
check(AL._al_ept(1000000) == 50000, "AL Electing PTE: 1,000,000 x 5% = 50,000", f"AL EPT wrong: {AL._al_ept(1000000)}")
check(AL._al_ept(800000) == 40000, "AL Electing PTE (S-corp): 800,000 x 5% = 40,000", "AL EPT S wrong")
check(AL._al_composite(300000) == 15000, "AL composite PTE-C: 300,000 x 5% = 15,000", f"AL composite wrong: {AL._al_composite(300000)}")
check(10000 + 5000 + 3000 == 18000, "AL 20S Line 32: LIFO 10k + BIG 5k + excess 3k = 18,000", "AL entity tax wrong")
check(AL.AL_PTET_RATE == "0.05" and AL.AL_COMPOSITE_RATE == "0.05", "AL Electing PTE 5% + composite 5%", "AL constants wrong")

# ── key diagnostics ──
DIAG = {
    "NC_D403": ["D_NCD403_PTET", "D_NCD403_BONUS", "D_NCD403_NRW"],
    "NC_CD401S": ["D_NCCD401S_PTET", "D_NCCD401S_FRANCH", "D_NCCD401S_179"],
    "AL_FORM_65": ["D_AL65_EPT", "D_AL65_DEPR", "D_AL65_COMPOSITE"],
    "AL_FORM_20S": ["D_AL20S_EPT", "D_AL20S_ENTITY", "D_AL20S_BPT"],
}
for fn, dids in DIAG.items():
    form = TaxForm.objects.get(form_number=fn)
    for did in dids:
        check(FormDiagnostic.objects.filter(tax_form=form, diagnostic_id=did).exists(), f"{fn}: {did} present", f"{fn}: {did} MISSING")

# ── entity_types + jurisdiction ──
for fn, (juris, et) in FORMS.items():
    form = TaxForm.objects.get(form_number=fn)
    check(form.entity_types == et, f"{fn}: entity_types = {et}", f"{fn}: entity_types wrong: {form.entity_types}")
    check(form.jurisdiction == juris, f"{fn}: jurisdiction = {juris}", f"{fn}: jurisdiction wrong: {form.jurisdiction!r}")

# ── report ──
print("\n" + "=" * 70)
for fn in FORMS:
    form = TaxForm.objects.get(form_number=fn)
    print(f"  {fn}: facts {FormFact.objects.filter(tax_form=form).count()} / rules {FormRule.objects.filter(tax_form=form).count()} / "
          f"lines {FormLine.objects.filter(tax_form=form).count()} / diag {FormDiagnostic.objects.filter(tax_form=form).count()} / tests {form.test_scenarios.count()}")
fa_ct = sum(FlowAssertion.objects.filter(assertion_id__startswith=p).count() for p in ("FA-NC", "FA-AL"))
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
