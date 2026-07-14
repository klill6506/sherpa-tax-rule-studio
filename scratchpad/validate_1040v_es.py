"""Throwaway-SQLite validation for the 1040-V / 1040-ES voucher-pair loader (batch order 3, tts s77).

Checks: guard-refusal (sentinel ships False); in-memory flip seeds BOTH forms + twice-run idempotency;
caps; rule-link coverage per form; logic oracles (V emission/EFW suppression, $100M split, BOTH address
charts incl. the GA 1214-vs-1300 drift pin, the RAP arms (90/100/110/66-2/3) with the scenario pins,
the $1,000 gate + no-liability exception, joint bars, Q4 skip, voucher-box exclusion); scenario outputs
recomputed; FAs staged DRAFT; the not-the-return-address language pinned.
ASCII-only. Run: poetry run python scratchpad/validate_1040v_es.py
"""
import os
import sys

PROJECT_ROOT = r"D:\dev\sherpa-tax-rule-studio"
sys.path.insert(0, PROJECT_ROOT)

SQLITE_PATH = os.path.join(PROJECT_ROOT, "scratchpad", "validate_1040v_es.sqlite3")
if os.path.exists(SQLITE_PATH):
    os.remove(SQLITE_PATH)
os.environ["DATABASE_URL"] = f"sqlite:///{SQLITE_PATH}"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

import django  # noqa: E402
django.setup()

from django.core.management import call_command  # noqa: E402
from django.core.management.base import CommandError  # noqa: E402
from specs.models import FlowAssertion, FormDiagnostic, FormFact, FormLine, FormRule, TaxForm, TestScenario  # noqa: E402
from sources.models import AuthorityTopic, RuleAuthorityLink  # noqa: E402
from specs.management.commands import load_1040v_es as L  # noqa: E402

FAILURES: list[str] = []
PASSES: list[str] = []


def check(cond, ok, bad):
    (PASSES if cond else FAILURES).append(ok if cond else bad)


call_command("migrate", run_syncdb=True, verbosity=0)

check(L.READY_TO_SEED is True, "READY_TO_SEED ships True (Gate-1 APPROVED 2026-07-14)", "READY_TO_SEED is not True post-approval")
L.READY_TO_SEED = False
try:
    call_command("load_1040v_es", verbosity=0)
    FAILURES.append("guard FAILED to refuse while READY_TO_SEED=False")
except CommandError:
    PASSES.append("guard still refuses when the sentinel is off (mechanism intact)")

L.READY_TO_SEED = True
try:
    call_command("load_1040v_es", verbosity=0)
    PASSES.append("load_1040v_es ran + seeded into SQLite without error (in-memory flip)")
except Exception as e:  # noqa: BLE001
    FAILURES.append(f"load_1040v_es raised: {e!r}")
    print("\n".join(FAILURES))
    sys.exit(1)

try:
    call_command("load_1040v_es", verbosity=0)
    PASSES.append("second run idempotent (update_or_create everywhere)")
except Exception as e:  # noqa: BLE001
    FAILURES.append(f"second run raised: {e!r}")
finally:
    L.READY_TO_SEED = True

form_v = TaxForm.objects.get(form_number="1040V")
form_es = TaxForm.objects.get(form_number="1040ES")

# -- CharField caps (both forms) --
CAPS: dict = {"v_title(255)": (form_v.form_title, 255), "es_title(255)": (form_es.form_title, 255)}
for form in (form_v, form_es):
    for r in FormRule.objects.filter(tax_form=form):
        CAPS[f"rule_id={r.rule_id}"] = (r.rule_id, 20)
        CAPS[f"rule_title={r.rule_id}"] = (r.title, 255)
    for d in FormDiagnostic.objects.filter(tax_form=form):
        CAPS[f"diagnostic_id={d.diagnostic_id}"] = (d.diagnostic_id, 20)
        CAPS[f"diag_title={d.diagnostic_id}"] = (d.title, 255)
    for ln in FormLine.objects.filter(tax_form=form):
        CAPS[f"line_number={ln.line_number}"] = (ln.line_number, 20)
    for fct in FormFact.objects.filter(tax_form=form):
        CAPS[f"fact_key={fct.fact_key}"] = (fct.fact_key, 100)
        CAPS[f"fact_label={fct.fact_key}"] = (fct.label, 255)
for fa in FlowAssertion.objects.filter(assertion_id__in=["FA-1040V-EFW", "FA-ES-RAP", "FA-ES-QDEBIT"]):
    CAPS[f"assertion_id={fa.assertion_id}"] = (fa.assertion_id, 20)
for t in AuthorityTopic.objects.all():
    CAPS[f"topic={t.topic_code}"] = (t.topic_name, 255)
viol = [f"{k}: len {len(v)} > {cap}" for k, (v, cap) in CAPS.items() if len(v) > cap]
check(not viol, f"CharField caps OK ({len(CAPS)} checked)", "CAP VIOLATIONS:\n    " + "\n    ".join(viol))

# -- counts + identity --
check(FormFact.objects.filter(tax_form=form_v).count() == len(L.V_FACTS), f"1040V facts {len(L.V_FACTS)}", "V fact count mismatch")
check(FormRule.objects.filter(tax_form=form_v).count() == len(L.V_RULES), f"1040V rules {len(L.V_RULES)}", "V rule count mismatch")
check(FormDiagnostic.objects.filter(tax_form=form_v).count() == len(L.V_DIAGNOSTICS), f"1040V diagnostics {len(L.V_DIAGNOSTICS)}", "V diag count mismatch")
check(TestScenario.objects.filter(tax_form=form_v).count() == len(L.V_SCENARIOS), f"1040V scenarios {len(L.V_SCENARIOS)}", "V scenario count mismatch")
check(FormFact.objects.filter(tax_form=form_es).count() == len(L.ES_FACTS), f"1040ES facts {len(L.ES_FACTS)}", "ES fact count mismatch")
check(FormRule.objects.filter(tax_form=form_es).count() == len(L.ES_RULES), f"1040ES rules {len(L.ES_RULES)}", "ES rule count mismatch")
check(FormDiagnostic.objects.filter(tax_form=form_es).count() == len(L.ES_DIAGNOSTICS), f"1040ES diagnostics {len(L.ES_DIAGNOSTICS)}", "ES diag count mismatch")
check(TestScenario.objects.filter(tax_form=form_es).count() == len(L.ES_SCENARIOS), f"1040ES scenarios {len(L.ES_SCENARIOS)}", "ES scenario count mismatch")
check(form_v.entity_types == ["1040"] and form_es.entity_types == ["1040"], "entity_types ['1040'] both", "entity_types wrong")

# -- authority links (both forms) --
for form, rules, links, tag in ((form_v, L.V_RULES, L.V_RULE_LINKS, "V"), (form_es, L.ES_RULES, L.ES_RULE_LINKS, "ES")):
    ruleless = [r.rule_id for r in FormRule.objects.filter(tax_form=form)
                if not RuleAuthorityLink.objects.filter(form_rule=r).exists()]
    check(not ruleless, f"{tag}: all rules have >= 1 authority link", f"{tag} ruleless: {ruleless}")
    defined = {r["rule_id"] for r in rules}
    linked = {rl[0] for rl in links}
    check(not (linked - defined) and not (defined - linked), f"{tag}: rule_links bidirectionally complete", f"{tag} link drift: {linked ^ defined}")

# -- FAs staged DRAFT --
fas = list(FlowAssertion.objects.filter(assertion_id__in=["FA-1040V-EFW", "FA-ES-RAP", "FA-ES-QDEBIT"]))
check(len(fas) == 3, "3 pair assertions", f"FA count {len(fas)}")
notdraft = [fa.assertion_id for fa in fas if fa.status != "draft"]
check(not notdraft, "all pair FAs staged DRAFT (the new-FAs-default-ACTIVE trap)", f"NOT draft: {notdraft}")

# -- 1040-V emission oracles --
check(L._v_needed(2000, True, False) is True, "balance + check + no EFW -> V prints (1040V-A)", "v_needed base wrong")
check(L._v_needed(2000, False, True) is False, "EFW elected -> V suppressed (1040V-B)", "v_needed EFW wrong")
check(L._v_needed(2000, True, True) is False, "check flag + EFW still suppresses (EFW wins)", "v_needed conflict wrong")
check(L._v_needed(0, True, False) is False, "no balance due -> no voucher", "v_needed zero wrong")

# -- the three-way address drift pins --
check("P.O. Box 1214" in L._v_address("GA", False), "GA V address = Charlotte Box 1214", "GA V address wrong")
check("P.O. Box 1300" in L._es_address("GA", False), "GA ES address = Charlotte Box 1300 (NOT 1214 — the drift pin)", "GA ES address wrong")
check(L._v_address("GA", False) != L._es_address("GA", False), "the V and ES charts DIFFER for GA (the trap is real)", "GA charts identical?!")
check("Louisville" in L._v_address("OH", False) and "931000" in L._v_address("OH", False), "OH V -> Louisville 931000", "OH V wrong")
check("P.O. Box 1300" in L._es_address("OH", False), "OH ES -> Charlotte 1300 (OH is on the ES Charlotte list)", "OH ES wrong")
check("931100" in L._es_address("NY", False), "NY ES -> Louisville 931100", "NY ES wrong")
check("P.O. Box 1303" in L._v_address("GA", True) and "P.O. Box 1303" in L._es_address("GA", True), "foreign -> Charlotte 1303 on BOTH charts", "foreign address wrong")
check(len(L.ES_CHARLOTTE_STATES) == 29 and len(L.ES_LOUISVILLE_STATES) == 22, "ES chart rosters: 29 Charlotte + 22 Louisville (+DC)", f"ES rosters {len(L.ES_CHARLOTTE_STATES)}/{len(L.ES_LOUISVILLE_STATES)}")
check(len(L.V_SOUTH_STATES) == 9, "V Charlotte roster: 9 states", f"V roster {len(L.V_SOUTH_STATES)}")

# -- $100M split --
check(L._check_splits_required(2000) == 1, "normal check -> 1", "split base wrong")
check(L._check_splits_required(100_000_000) == 2, "$100M exactly -> 2 checks (1040V-C)", "split 100M wrong")
check(L._check_splits_required(250_000_000) >= 3, "$250M -> 3+ checks", "split 250M wrong")

# -- RAP oracles (the scenario pins) --
check(L._required_annual_payment(60000, 40000, 200000, False, False) == 44000,
      "1040ES-B: min(54,000, 110% x 40,000) = 44,000", "RAP 110% arm wrong")
check(L._required_annual_payment(60000, 40000, 100000, False, False) == 40000,
      "AGI 100,000 -> plain 100% arm = 40,000", "RAP 100% arm wrong")
check(L._required_annual_payment(30000, 28000, 200000, False, True) == 20000,
      "1040ES-C: farmer 2/3 x 30,000 = 20,000, and NO 110% despite AGI 200,000", "RAP farmer arm wrong")
check(L._required_annual_payment(60000, 40000, 80000, True, False) == 44000,
      "MFS: AGI 80,000 > 75,000 -> the 110% arm", "RAP MFS threshold wrong")
check(L._required_annual_payment(60000, 40000, 150000, False, False) == 40000,
      "AGI 150,000 exactly is NOT 'more than $150,000'", "RAP 150k boundary wrong")

# -- estimates-required gate --
rap = L._required_annual_payment(10000, 9000, 100000, False, False)  # min(9000, 9000) = 9000
check(L._estimates_required(2000, 7000, rap, False) is True, "owe 2,000 + withholding 7,000 < RAP 9,000 -> required", "gate base wrong")
check(L._estimates_required(900, 7000, rap, False) is False, "owe 900 < $1,000 gate -> not required", "gate 1000 wrong")
check(L._estimates_required(2000, 9500, rap, False) is False, "withholding 9,500 >= RAP 9,000 -> not required", "gate wh wrong")
check(L._estimates_required(5000, 0, rap, True) is False, "no-2025-liability exception wins (1040ES-D)", "gate exception wrong")

# -- joint bars --
check(L._joint_voucher_barred(True, False, False, False) is True, "NRA spouse bars (1040ES-E)", "bar NRA wrong")
check(L._joint_voucher_barred(False, True, False, False) is True, "divorce decree bars", "bar decree wrong")
check(L._joint_voucher_barred(False, False, True, False) is True, "different tax years bar", "bar years wrong")
check(L._joint_voucher_barred(False, False, False, True) is True, "RDP/civil union bars", "bar RDP wrong")
check(L._joint_voucher_barred(False, False, False, False) is False, "ordinary joint couple -> allowed", "bar clean wrong")

# -- Q4 skip + voucher box --
check(L._q4_skippable(True, True) is True, "file by Feb 1 + pay full -> Q4 skippable (1040ES-G)", "q4 skip wrong")
check(L._q4_skippable(True, False) is False, "file early WITHOUT full pay -> Q4 still due", "q4 partial wrong")
check(L._voucher_amount(1000, 500) == 1000, "voucher box = the check amount only (credit excluded)", "box exclusion wrong")

# -- due-date constants (= the s76 FPYMT-088-11 calendar) --
check(L.ES_DUE_DATES == ("2026-04-15", "2026-06-15", "2026-09-15", "2027-01-15"),
      "due dates Apr/Jun/Sep 15 2026 + Jan 15 2027", f"dates drifted: {L.ES_DUE_DATES}")
check(L.ES_OWE_GATE == 1000 and L.HIGH_AGI_THRESHOLD == 150000 and L.HIGH_AGI_THRESHOLD_MFS == 75000,
      "constants: $1,000 gate / $150k / $75k MFS", "threshold constants drifted")
check(abs(L.FARMER_PCT - 2 / 3) < 1e-9 and L.SAFE_HARBOR_PCT == 0.90 and L.PRIOR_YEAR_PCT_HIGH == 1.10,
      "percent arms: 90 / 110 / 66-2/3", "pct constants drifted")

# -- scenario outputs recomputed --
scenB = next(s for s in L.ES_SCENARIOS if s["scenario_name"].startswith("1040ES-B"))
b = scenB["inputs"]
check(L._required_annual_payment(b["expected_tax_2026"], b["prior_year_tax"], b["prior_year_agi"], b["filing_status_mfs_2026"], b["farmer_fisher"]) == scenB["expected_outputs"]["required_annual_payment"],
      "1040ES-B RAP recomputes (44,000)", "1040ES-B drifted")
scenC = next(s for s in L.ES_SCENARIOS if s["scenario_name"].startswith("1040ES-C"))
c = scenC["inputs"]
check(L._required_annual_payment(c["expected_tax_2026"], c["prior_year_tax"], c["prior_year_agi"], c["filing_status_mfs_2026"], c["farmer_fisher"]) == scenC["expected_outputs"]["required_annual_payment"],
      "1040ES-C farmer RAP recomputes (20,000)", "1040ES-C drifted")
scenVA = next(s for s in L.V_SCENARIOS if s["scenario_name"].startswith("1040V-A"))
va = scenVA["inputs"]
check(L._v_needed(va["balance_due"], va["paying_by_check"], va["efw_elected"]) is True, "1040V-A emission recomputes", "1040V-A drifted")
check(scenVA["expected_outputs"]["v_mailing_address_contains"] in L._v_address(va["state_of_residence"], va["foreign_or_territory"]),
      "1040V-A GA address recomputes (Box 1214)", "1040V-A address drifted")

# -- diagnostic language pins --
addr = FormDiagnostic.objects.get(tax_form=form_es, diagnostic_id="D_ES_ADDR")
check("P.O. Box 1300" in addr.message and "1214" in addr.message and "Form 1040 instructions" in addr.message,
      "ES address diagnostic carries the three-way drift warning", "ES address diagnostic weak")
efw = FormDiagnostic.objects.get(tax_form=form_v, diagnostic_id="D_V_EFWCONFL")
check("suppressed" in efw.message and "double-pay" in efw.message, "V EFW diagnostic carries the suppression + double-pay language", "V EFW diagnostic weak")
deb = FormDiagnostic.objects.get(tax_form=form_es, diagnostic_id="D_ES_DEBITED")
check("IRSESPayment" in deb.message, "ES debited diagnostic names the s76 record", "ES debited diagnostic weak")

print("\n" + "=" * 70)
print(f"PASS {len(PASSES)} / FAIL {len(FAILURES)}")
if FAILURES:
    print("\nFAILURES:")
    for f in FAILURES:
        print(f"  - {f}")
    sys.exit(1)
for p in PASSES:
    print(f"  ok: {p}")
