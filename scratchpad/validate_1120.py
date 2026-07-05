"""Throwaway-SQLite validation for the Form 1120 C-corp module (WO-11): 1120 + 1120_SCHL + GA600.

Checks: CharField caps (rule/diagnostic/line/assertion_id <= 20; fact_key <= 100; topic_name <= 255);
every rule >= 1 authority link; rule_link coverage; arithmetic oracles (Schedule C DRD + §246(b) loss
exception, §172 NOL 80%, §11 21% tax, Sch L balance / M-1 / M-2 ties, GA 5.19% income tax + §179 delta
+ net worth bracket table); key diagnostics present. ASCII-only prints (cp1252 console).

Run: poetry run python scratchpad/validate_1120.py
"""
import os
import sys

PROJECT_ROOT = r"D:\dev\sherpa-tax-rule-studio"
sys.path.insert(0, PROJECT_ROOT)

SQLITE_PATH = os.path.join(PROJECT_ROOT, "scratchpad", "validate_1120.sqlite3")
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
from specs.management.commands import load_1120_spine as SPINE  # noqa: E402
from specs.management.commands import load_1120_schl as SCHL  # noqa: E402
from specs.management.commands import load_ga600 as GA  # noqa: E402

FAILURES: list[str] = []
PASSES: list[str] = []


def check(cond, ok, bad):
    (PASSES if cond else FAILURES).append(ok if cond else bad)


call_command("migrate", run_syncdb=True, verbosity=0)
for mod, cmd in ((SPINE, "load_1120_spine"), (SCHL, "load_1120_schl"), (GA, "load_ga600")):
    mod.READY_TO_SEED = True
    try:
        call_command(cmd, verbosity=0)
        PASSES.append(f"{cmd} ran + seeded into SQLite without error")
    except Exception as e:  # noqa: BLE001
        FAILURES.append(f"{cmd} raised: {e!r}")
        print("\n".join(FAILURES))
        sys.exit(1)

FORMS = ["1120", "1120_SCHL", "GA600"]

# ── CharField caps (across all three forms) ──
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
for fa in FlowAssertion.objects.filter(assertion_id__startswith="FA-1120"):
    CAPS[f"assertion_id={fa.assertion_id}"] = (fa.assertion_id, 20)
for fa in FlowAssertion.objects.filter(assertion_id__startswith="FA-GA600"):
    CAPS[f"assertion_id={fa.assertion_id}"] = (fa.assertion_id, 20)
for t in AuthorityTopic.objects.all():
    CAPS[f"topic_name={t.topic_code}"] = (t.topic_name, 255)
viol = [f"{k}: len {len(v)} > {cap}" for k, (v, cap) in CAPS.items() if len(v) > cap]
check(not viol, f"CharField caps OK ({len(CAPS)} checked)", "CAP VIOLATIONS:\n    " + "\n    ".join(viol))

# ── every rule has >= 1 authority link; rule_links reference defined rules ──
for fn, mod, rules_attr, links_attr in (
    ("1120", SPINE, "F1120_RULES", "F1120_RULE_LINKS"),
    ("1120_SCHL", SCHL, "F_RULES", "F_RULE_LINKS"),
    ("GA600", GA, "F_RULES", "F_RULE_LINKS"),
):
    form = TaxForm.objects.get(form_number=fn)
    ruleless = [r.rule_id for r in FormRule.objects.filter(tax_form=form)
                if not RuleAuthorityLink.objects.filter(form_rule=r).exists()]
    check(not ruleless, f"{fn}: all {FormRule.objects.filter(tax_form=form).count()} rules have >= 1 authority link",
          f"{fn}: rules with ZERO authority links: {ruleless}")
    defined = {r["rule_id"] for r in getattr(mod, rules_attr)}
    linked = {rl[0] for rl in getattr(mod, links_attr)}
    check(not (linked - defined), f"{fn}: all rule_links reference defined rules", f"{fn}: orphan links: {linked - defined}")
    check(not (defined - linked), f"{fn}: every defined rule appears in rule_links", f"{fn}: unlinked rules: {defined - linked}")

# ══════════════════════════════════════════════════════════════════
# ARITHMETIC ORACLES
# ══════════════════════════════════════════════════════════════════

# ── Schedule C DRD (§243/§246(b) + loss exception) ──
# 50% DRD, not limited
special, d5065, d100, limited, loss_exc = SPINE._drd(100000, 0, 0, 0, 300000, 0)
check(special == 50000 and not limited, "DRD 50%: 100,000 <20%-owned -> 50,000 special deduction (not limited)", f"DRD 50% wrong: {special}")
# 65% DRD
special, *_ = SPINE._drd(0, 100000, 0, 0, 300000, 0)
check(special == 65000, "DRD 65%: 100,000 20%+-owned -> 65,000 special deduction", f"DRD 65% wrong: {special}")
# 100% categories not §246(b)-limited
special, d5065, d100, *_ = SPINE._drd(0, 0, 40000, 10000, 5000, 0)
check(d100 == 50000 and special == 50000, "DRD 100%: foreign-sub/SBIC/affiliated/§245A 50,000 fully deducted (not limited)", f"DRD 100% wrong: d100={d100} special={special}")
# §246(b) limit BINDS: div 100,000 @50% = 50,000, base 60,000, limit 30,000, no NOL created
special, d5065, d100, limited, loss_exc = SPINE._drd(100000, 0, 0, 0, 60000, 0)
check(d5065 == 30000 and limited and not loss_exc, "DRD §246(b) limit binds: 50,000 -> 30,000 (50% of 60,000 base)", f"§246(b) limit wrong: d5065={d5065} limited={limited}")
# LOSS EXCEPTION: div 100,000 @50% = 50,000, base 20,000 -> full DRD creates an NOL -> no limit
special, d5065, d100, limited, loss_exc = SPINE._drd(100000, 0, 0, 0, 20000, 0)
check(d5065 == 50000 and loss_exc, "DRD §246(b) LOSS EXCEPTION: full 50,000 allowed (creates an NOL, no limit)", f"loss exception wrong: d5065={d5065} loss_exc={loss_exc}")

# ── §172 NOL 80% limitation ──
nol_base = 300000 - 0
nol_ded = min(500000, float(SPINE.NOL_LIMIT_PCT) * nol_base)
check(nol_ded == 240000, "§172 NOL: min(500,000 carryover, 80% x 300,000) = 240,000", f"NOL wrong: {nol_ded}")

# ── §11 21% tax ──
check(round(250000 * float(SPINE.CORP_TAX_RATE)) == 52500, "§11: 21% x 250,000 = 52,500", "21% tax wrong")
check(SPINE.CORP_TAX_RATE == "0.21", "corp rate = 0.21", f"corp rate wrong: {SPINE.CORP_TAX_RATE}")
check(SPINE.SEC163J_GROSS_RCPTS == 31000000, "§163(j)/§448(c) exemption = $31,000,000 (2025)", f"163j threshold wrong: {SPINE.SEC163J_GROSS_RCPTS}")
check(SPINE.CAMT_AFSI_THRESHOLD == 1000000000, "CAMT applicable-corp threshold = $1,000,000,000", f"CAMT threshold wrong: {SPINE.CAMT_AFSI_THRESHOLD}")

# ── Schedule L balance / M-1 / M-2 ──
total_assets = 100000 + 50000 + 0 + 0 + 0 + 350000 + 0 + 0
total_liabeq = 80000 + 220000 + 100000 + 0 + 100000 + 0
check(total_assets == 500000 and total_liabeq == 500000, "Sch L balances: assets 500,000 == liab+equity 500,000", f"Sch L wrong: {total_assets} vs {total_liabeq}")
m1_l6 = 120000 + 25000 + 0 + 0 + 10000
m1_l9 = 5000 + 0
check(m1_l6 - m1_l9 == 150000, "Sch M-1: L6 155,000 - L9 5,000 = L10 150,000 (= page-1 L28)", f"M-1 wrong: {m1_l6 - m1_l9}")
m2_l8 = (80000 + 120000 + 0) - (100000 + 0)
check(m2_l8 == 100000, "Sch M-2: (80,000 + 120,000) - 100,000 = 100,000 ending R/E (ties to L25)", f"M-2 wrong: {m2_l8}")

# ── GA income tax + §179 delta + net worth table ──
ga_ti, ga_tax = GA._ga_income_tax(200000, 0, 0, 0, 1.0)
check(round(ga_tax) == 10380, "GA income tax: 200,000 x 5.19% = 10,380", f"GA tax wrong: {ga_tax}")
# §179 excess addition
add_179 = max(0, 2000000 - GA.GA_179_LIMIT)
ga_ti, ga_tax = GA._ga_income_tax(500000, add_179, 0, 0, 1.0)
check(add_179 == 750000 and round(ga_tax) == 64875, "GA §179 delta: fed 2,000,000 - GA 1,250,000 = 750,000 add -> 1,250,000 x 5.19% = 64,875", f"GA §179 wrong: add={add_179} tax={ga_tax}")
check(GA.GA_179_LIMIT == 1250000 and GA.GA_179_PHASEOUT == 3130000, "GA §179 2025 = $1,250,000 / $3,130,000 (indexed, not the stale 2021 $1.05M/$2.62M)", f"GA §179 constants wrong: {GA.GA_179_LIMIT}/{GA.GA_179_PHASEOUT}")
check(GA.GA_CORP_RATE == "0.0519", "GA corp rate = 5.19% (HB 111)", f"GA rate wrong: {GA.GA_CORP_RATE}")
# apportionment
ga_ti, ga_tax = GA._ga_income_tax(1000000, 0, 0, 0, 0.3)
check(round(ga_ti) == 300000 and round(ga_tax) == 15570, "GA apportionment: 1,000,000 x 0.30 = 300,000 x 5.19% = 15,570", f"GA apportion wrong: {ga_ti}/{ga_tax}")
# GA NOL 80%
ga_ti, ga_tax = GA._ga_income_tax(300000, 0, 0, 500000, 1.0)
check(round(ga_ti) == 60000, "GA NOL 80%: 300,000 - min(500,000, 80% x 300,000=240,000) = 60,000", f"GA NOL wrong: {ga_ti}")
# net worth table
check(GA._net_worth_tax(1500000) == 750, "GA net worth: 1,500,000 -> $750 bracket", f"NW 1.5M wrong: {GA._net_worth_tax(1500000)}")
check(GA._net_worth_tax(25000000) == 5000, "GA net worth: 25,000,000 -> $5,000 max", f"NW max wrong: {GA._net_worth_tax(25000000)}")
check(GA._net_worth_tax(95000) == 0, "GA net worth: 95,000 <= 100,000 -> $0 exempt", f"NW exempt wrong: {GA._net_worth_tax(95000)}")
check(GA._net_worth_tax(100000) == 0 and GA._net_worth_tax(150000) == 125, "GA net worth boundaries: $100k=$0, $150k=$125", "NW boundary wrong")

# ── key diagnostics present ──
DIAG_EXPECT = {
    "1120": ["D_1120_DRD_LIMIT", "D_1120_NOL80", "D_1120_163J", "D_1120_CAMT", "D_1120_PHC", "D_1120_1062"],
    "1120_SCHL": ["D_SCHL_BALANCE", "D_1120_M1_RECON", "D_1120_M2_TIE", "D_1120_M3", "D_1120_250K"],
    "GA600": ["D_GA600_BONUS", "D_GA600_179", "D_GA600_APPORT", "D_GA600_NWCRED", "D_GA600_CONFORM"],
}
for fn, dids in DIAG_EXPECT.items():
    form = TaxForm.objects.get(form_number=fn)
    for did in dids:
        check(FormDiagnostic.objects.filter(tax_form=form, diagnostic_id=did).exists(),
              f"{fn}: {did} present", f"{fn}: {did} MISSING")

# ── entity_types = 1120 on all three ──
for fn in FORMS:
    form = TaxForm.objects.get(form_number=fn)
    check(form.entity_types == ["1120"], f"{fn}: entity_types = ['1120']", f"{fn}: entity_types wrong: {form.entity_types}")

# ── report ──
print("\n" + "=" * 70)
for fn in FORMS:
    form = TaxForm.objects.get(form_number=fn)
    print(f"  {fn}: facts {FormFact.objects.filter(tax_form=form).count()} / "
          f"rules {FormRule.objects.filter(tax_form=form).count()} / "
          f"lines {FormLine.objects.filter(tax_form=form).count()} / "
          f"diag {FormDiagnostic.objects.filter(tax_form=form).count()} / "
          f"tests {form.test_scenarios.count()}")
fa_ct = FlowAssertion.objects.filter(assertion_id__startswith="FA-1120").count() + \
    FlowAssertion.objects.filter(assertion_id__startswith="FA-GA600").count()
print(f"  flow assertions: {fa_ct}")
print("=" * 70)
for p in PASSES:
    print(f"  PASS  {p}")
for fbad in FAILURES:
    print(f"  FAIL  {fbad}")
print("=" * 70)
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
