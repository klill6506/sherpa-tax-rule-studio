"""Throwaway-SQLite validation for the Form 9465 loader (payment-cluster batch order 1, tts s77).

Checks: the Gate-1 guard refuses while READY_TO_SEED=False (as shipped); in-memory flip seeds +
twice-run idempotency; CharField caps; rule-link coverage; logic oracles (line-10 ceiling, guaranteed/
streamlined tiers, Part II gate, spouse-lines gate, the e-file blocker router arm-by-arm, the fee
ladder incl. low-income, day window, EFW consistency); scenario expected_outputs recomputed from the
helpers; FAs staged DRAFT; entity_types; the year-keyed fee language pinned in the diagnostics.
ASCII-only. Run: poetry run python scratchpad/validate_9465.py
"""
import os
import sys

PROJECT_ROOT = r"D:\dev\sherpa-tax-rule-studio"
sys.path.insert(0, PROJECT_ROOT)

SQLITE_PATH = os.path.join(PROJECT_ROOT, "scratchpad", "validate_9465.sqlite3")
if os.path.exists(SQLITE_PATH):
    os.remove(SQLITE_PATH)
os.environ["DATABASE_URL"] = f"sqlite:///{SQLITE_PATH}"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

import django  # noqa: E402
django.setup()

from django.core.management import call_command  # noqa: E402
from django.core.management.base import CommandError  # noqa: E402
from specs.models import FlowAssertion, FormDiagnostic, FormFact, FormLine, FormRule, TaxForm, TestScenario  # noqa: E402
from sources.models import AuthorityExcerpt, AuthorityTopic, RuleAuthorityLink  # noqa: E402
from specs.management.commands import load_9465 as L  # noqa: E402

FAILURES: list[str] = []
PASSES: list[str] = []


def check(cond, ok, bad):
    (PASSES if cond else FAILURES).append(ok if cond else bad)


call_command("migrate", run_syncdb=True, verbosity=0)

# -- Gate-1 state: draft ships GATED. Prove the refusal, then seed with an in-memory flip.
check(L.READY_TO_SEED is False, "READY_TO_SEED ships False (Gate-1 PENDING)", "READY_TO_SEED is not False in the draft")
try:
    call_command("load_9465", verbosity=0)
    FAILURES.append("guard FAILED to refuse while READY_TO_SEED=False")
except CommandError:
    PASSES.append("guard refuses to seed while the sentinel is off")

L.READY_TO_SEED = True
try:
    call_command("load_9465", verbosity=0)
    PASSES.append("load_9465 ran + seeded into SQLite without error (in-memory flip)")
except Exception as e:  # noqa: BLE001
    FAILURES.append(f"load_9465 raised: {e!r}")
    print("\n".join(FAILURES))
    sys.exit(1)

try:
    call_command("load_9465", verbosity=0)
    PASSES.append("second run idempotent (update_or_create everywhere)")
except Exception as e:  # noqa: BLE001
    FAILURES.append(f"second run raised: {e!r}")
finally:
    L.READY_TO_SEED = False

form = TaxForm.objects.get(form_number="9465")

# -- CharField caps --
CAPS: dict = {"form_number(50)": (form.form_number, 50), "form_title(255)": (form.form_title, 255)}
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
for fa in FlowAssertion.objects.filter(assertion_id__startswith="FA-9465"):
    CAPS[f"assertion_id={fa.assertion_id}"] = (fa.assertion_id, 20)
for t in AuthorityTopic.objects.all():
    CAPS[f"topic={t.topic_code}"] = (t.topic_name, 255)
viol = [f"{k}: len {len(v)} > {cap}" for k, (v, cap) in CAPS.items() if len(v) > cap]
check(not viol, f"CharField caps OK ({len(CAPS)} checked)", "CAP VIOLATIONS:\n    " + "\n    ".join(viol))

# -- counts + identity --
check(FormFact.objects.filter(tax_form=form).count() == len(L.F9465_FACTS), f"facts {len(L.F9465_FACTS)}", "fact count mismatch")
check(FormRule.objects.filter(tax_form=form).count() == len(L.F9465_RULES), f"rules {len(L.F9465_RULES)}", "rule count mismatch")
check(FormLine.objects.filter(tax_form=form).count() == len(L.F9465_LINES), f"lines {len(L.F9465_LINES)}", "line count mismatch")
check(FormDiagnostic.objects.filter(tax_form=form).count() == len(L.F9465_DIAGNOSTICS), f"diagnostics {len(L.F9465_DIAGNOSTICS)}", "diag count mismatch")
check(TestScenario.objects.filter(tax_form=form).count() == len(L.F9465_SCENARIOS), f"scenarios {len(L.F9465_SCENARIOS)}", "scenario count mismatch")
check(form.entity_types == ["1040"], "entity_types = ['1040']", f"entity_types wrong: {form.entity_types}")
check(form.status == "draft", "form status draft", f"status {form.status}")

# -- authority links --
ruleless = [r.rule_id for r in FormRule.objects.filter(tax_form=form)
            if not RuleAuthorityLink.objects.filter(form_rule=r).exists()]
check(not ruleless, f"all {FormRule.objects.filter(tax_form=form).count()} rules have >= 1 authority link", f"ruleless: {ruleless}")
defined = {r["rule_id"] for r in L.F9465_RULES}
linked = {rl[0] for rl in L.F9465_RULE_LINKS}
check(not (linked - defined), "rule_links reference defined rules", f"orphan: {linked - defined}")
check(not (defined - linked), "every rule appears in rule_links", f"unlinked: {defined - linked}")
check(AuthorityExcerpt.objects.filter(authority_source__source_code__in=["IRS_F9465", "IRS_I9465", "IRS_PAYPLAN", "MEF_9465_BR"]).count() >= 8,
      "8+ excerpts across the four sources", "excerpt count short")

# -- FAs staged DRAFT --
fas = list(FlowAssertion.objects.filter(assertion_id__startswith="FA-9465"))
check(len(fas) == 3, "3 FA-9465 assertions", f"FA count {len(fas)}")
notdraft = [fa.assertion_id for fa in fas if fa.status != "draft"]
check(not notdraft, "all FA-9465 staged DRAFT (the new-FAs-default-ACTIVE trap)", f"NOT draft: {notdraft}")

# -- line-10 minimum oracles (whole-dollar ceiling) --
check(L._monthly_minimum(8400) == 117, "8400/72 -> 117 (ceil of 116.67)", "8400 minimum wrong")
check(L._monthly_minimum(30000) == 417, "30000/72 -> 417 (ceil of 416.67)", "30000 minimum wrong")
check(L._monthly_minimum(50000) == 695, "50000/72 -> 695 (ceil of 694.44)", "50000 minimum wrong")
check(L._monthly_minimum(8000) == 112, "8000/72 -> 112 (ceil of 111.11; the 9465-H pin)", "8000 minimum wrong")
check(L._monthly_minimum(7200) == 100, "7200/72 -> 100 (exact division, no bump)", "7200 minimum wrong")
check(L._monthly_minimum(7201) == 101, "7201/72 -> 101 (any remainder bumps)", "7201 minimum wrong")
check(L._monthly_minimum(0) == 0, "zero balance -> zero minimum", "zero minimum wrong")

# -- guaranteed-tier oracles --
check(L._guaranteed_eligible(10000, True, True, True) is True, "10,000 exactly + compliance -> guaranteed", "guaranteed boundary wrong")
check(L._guaranteed_eligible(10001, True, True, True) is False, "10,001 -> not guaranteed", "guaranteed over wrong")
check(L._guaranteed_eligible(8000, False, True, True) is False, "5-yr compliance missing -> not guaranteed", "guaranteed compliance wrong")
check(L._guaranteed_eligible(8000, True, False, True) is False, "no 3-yr full-pay agreement -> not guaranteed", "guaranteed 3yr wrong")

# -- streamlined-tier oracles --
check(L._streamlined_eligible(25000, False, False) is True, "25,000 no DD -> streamlined (tier 1)", "streamlined t1 wrong")
check(L._streamlined_eligible(25001, False, False) is False, "25,001 no DD/payroll -> NOT streamlined", "streamlined band wrong")
check(L._streamlined_eligible(25001, True, False) is True, "25,001 with DD -> streamlined (tier 2)", "streamlined DD wrong")
check(L._streamlined_eligible(50000, False, True) is True, "50,000 with payroll -> streamlined", "streamlined payroll wrong")
check(L._streamlined_eligible(50001, True, False) is False, "50,001 -> never streamlined", "streamlined cap wrong")

# -- Part II gate oracles (all three conditions; each-absent stays off) --
check(L._part2_required(True, 30000, True) is True, "defaulted + band + below-min -> Part II", "part2 all-three wrong")
check(L._part2_required(False, 30000, True) is False, "no default -> Part II off", "part2 no-default wrong")
check(L._part2_required(True, 20000, True) is False, "owed 20,000 (not in band) -> Part II off", "part2 low-band wrong")
check(L._part2_required(True, 60000, True) is False, "owed 60,000 (over band) -> Part II off", "part2 high-band wrong")
check(L._part2_required(True, 30000, False) is False, "payment meets minimum -> Part II off", "part2 min-met wrong")
check(L._part2_required(True, 25000, True) is False, "25,000 exactly is NOT 'more than $25,000'", "part2 25k boundary wrong")

# -- spouse-lines gate --
check(L._spouse_lines_required(True, True, False) is True, "married + shares expenses -> L21/22", "spouse shares wrong")
check(L._spouse_lines_required(True, False, True) is True, "married + community property -> L21/22", "spouse CP wrong")
check(L._spouse_lines_required(True, False, False) is False, "married, separate households, common law -> off", "spouse off wrong")
check(L._spouse_lines_required(False, True, True) is False, "unmarried -> off regardless", "spouse unmarried wrong")

# -- e-file blocker router, arm by arm --
CLEAN = dict(owed_total=30000, payroll_deduction=False, cannot_increase=False, proposed=500, revised=0,
             minimum=417, has_phone=True, routing="061000104", account="123456789", low_income_no_dd=False)
check(L._efile_blockers(**CLEAN) == [], "clean 30k DD return -> no blockers (9465-B)", f"clean blockers: {L._efile_blockers(**CLEAN)}")
check(L._efile_blockers(**{**CLEAN, "owed_total": 62000}) and "F9465-001-03" in L._efile_blockers(**{**CLEAN, "owed_total": 62000}),
      "62,000 -> F9465-001-03", "50k arm wrong")
check("F9465-026-01" in L._efile_blockers(**{**CLEAN, "payroll_deduction": True}), "payroll box -> F9465-026-01", "payroll arm wrong")
check("F9465-037-01" in L._efile_blockers(**{**CLEAN, "cannot_increase": True}), "can't-increase -> F9465-037-01", "no-increase arm wrong")
check("F9465-027-01" in L._efile_blockers(**{**CLEAN, "proposed": 300}), "11a 300 < 417 -> F9465-027-01", "below-min arm wrong")
check("F9465-039-01" in L._efile_blockers(**{**CLEAN, "proposed": 300, "revised": 400}), "11b 400 < 417 -> F9465-039-01", "revised arm wrong")
check(L._efile_blockers(**{**CLEAN, "proposed": 300, "revised": 450}) == [], "11a 300 but 11b 450 >= 417 -> clean (9465-E)", "revised-clears arm wrong")
check("F9465-018-01" in L._efile_blockers(**{**CLEAN, "has_phone": False}), "no phone -> F9465-018-01", "phone arm wrong")
check("F9465-016-01" in L._efile_blockers(**{**CLEAN, "account": ""}), "routing without account -> F9465-016-01", "pair arm wrong")
check("F9465-040" in L._efile_blockers(**{**CLEAN, "low_income_no_dd": True}), "13c with routing -> F9465-040", "13c arm wrong")
band_nodd = L._efile_blockers(**{**CLEAN, "routing": "", "account": ""})
check("F9465-044" in band_nodd, "25k-50k band without DD -> F9465-044 (9465-C)", f"band arm wrong: {band_nodd}")
small_nodd = L._efile_blockers(**{**CLEAN, "owed_total": 12000, "minimum": 167, "routing": "", "account": ""})
check(small_nodd == [], "12,000 without DD -> no band blocker (under 25k)", f"under-band wrong: {small_nodd}")

# -- fee-ladder oracles (July-2024 schedule; year-keyed) --
check(L._user_fee(True, True, False, False) == 22, "OPA + DD -> $22", "fee opa-dd wrong")
check(L._user_fee(True, False, False, False) == 69, "OPA no DD -> $69", "fee opa wrong")
check(L._user_fee(False, True, False, False) == 107, "form channel + DD -> $107", "fee form-dd wrong")
check(L._user_fee(False, False, False, False) == 178, "form channel no DD -> $178", "fee form wrong")
check(L._user_fee(False, False, False, True) == 178, "payroll deduction (2159) -> $178", "fee payroll wrong")
check(L._user_fee(False, True, True, False) == 0, "low-income + DDIA -> WAIVED ($0)", "fee li-ddia wrong")
check(L._user_fee(False, False, True, False) == 43, "low-income no DD -> $43 reduced (9465-J)", "fee li wrong")
check(L.FEE_MODIFY == 89 and L.FEE_MODIFY_OPA == 10, "modify $89 / OPA reinstate $10", "modify fees wrong")

# -- day window --
check(L._payment_day_ok(1) and L._payment_day_ok(28), "days 1 and 28 legal", "day boundary wrong")
check(not L._payment_day_ok(29) and not L._payment_day_ok(0), "days 0 and 29 illegal", "day out-of-range wrong")

# -- EFW consistency (F9465-019-02) --
check(L._efw_amount_consistent(1000, 1000) is True, "line 8 1,000 == EFW 1,000 -> consistent (9465-H)", "efw match wrong")
check(L._efw_amount_consistent(500, 1000) is False, "line 8 500 != EFW 1,000 -> refuses", "efw mismatch wrong")
check(L._efw_amount_consistent(500, None) is True, "no EFW record -> line 8 unconstrained", "efw none wrong")

# -- scenario expected_outputs recomputed from the helpers --
scenA = next(s for s in L.F9465_SCENARIOS if s["scenario_name"].startswith("9465-A"))
check(L._monthly_minimum(scenA["inputs"]["amount_owed_returns"]) == scenA["expected_outputs"]["monthly_minimum"],
      "9465-A minimum recomputes (117)", "9465-A minimum drifted")
check(L._guaranteed_eligible(8400, True, True, True) is scenA["expected_outputs"]["guaranteed_eligible"],
      "9465-A guaranteed recomputes", "9465-A guaranteed drifted")
scenB = next(s for s in L.F9465_SCENARIOS if s["scenario_name"].startswith("9465-B"))
check(L._monthly_minimum(scenB["inputs"]["amount_owed_returns"]) == scenB["expected_outputs"]["monthly_minimum"],
      "9465-B minimum recomputes (417)", "9465-B minimum drifted")
check(L._user_fee(False, True, False, False) == scenB["expected_outputs"]["user_fee"],
      "9465-B fee recomputes ($107)", "9465-B fee drifted")
scenH = next(s for s in L.F9465_SCENARIOS if s["scenario_name"].startswith("9465-H"))
h_in = scenH["inputs"]
check(L._efw_amount_consistent(h_in["payment_with_request"], h_in["efw_payment_amount"]) is True,
      "9465-H EFW pin recomputes", "9465-H EFW drifted")
check(L._monthly_minimum(h_in["amount_owed_returns"] - h_in["payment_with_request"]) == scenH["expected_outputs"]["monthly_minimum"],
      "9465-H L9-basis minimum recomputes (112)", "9465-H minimum drifted")
scenJ = next(s for s in L.F9465_SCENARIOS if s["scenario_name"].startswith("9465-J"))
check(L._user_fee(False, True, True, False) == scenJ["expected_outputs"]["user_fee_ddia"], "9465-J DDIA waiver recomputes (0)", "9465-J waiver drifted")
check(L._user_fee(False, False, True, False) == scenJ["expected_outputs"]["user_fee_no_dd"], "9465-J reduced fee recomputes (43)", "9465-J reduced drifted")

# -- diagnostic language pins (year-keyed fee + the EFW rule cite) --
fee_diag = FormDiagnostic.objects.get(tax_form=form, diagnostic_id="D_9465_FEE")
for token in ("$107", "$178", "$43", "250%"):
    check(token in fee_diag.message, f"fee diagnostic carries {token}", f"fee diagnostic missing {token}")
efw_diag = FormDiagnostic.objects.get(tax_form=form, diagnostic_id="D_9465_EFWMATCH")
check("F9465-019-02" in efw_diag.message, "EFW diagnostic cites F9465-019-02", "EFW diagnostic missing the rule id")
ef50 = FormDiagnostic.objects.get(tax_form=form, diagnostic_id="D_9465_EFILE50")
check("433-F" in ef50.message and "$50,000" in ef50.message, "50k diagnostic carries 433-F + threshold", "50k diagnostic weak")

# -- constants sanity --
check(L.EFILE_MAX_BALANCE == 50000 and L.GUARANTEED_MAX == 10000 and L.FULL_PAY_MONTHS == 72,
      "constants: 50k e-file cap / 10k guaranteed / 72 months", "constants drifted")
check(L.MAX_PAYMENT_DAY == 28 and L.LOW_INCOME_POVERTY_PCT == 250, "constants: day 28 / 250% poverty", "day/poverty constants drifted")

print("\n" + "=" * 70)
print(f"PASS {len(PASSES)} / FAIL {len(FAILURES)}")
if FAILURES:
    print("\nFAILURES:")
    for f in FAILURES:
        print(f"  - {f}")
    sys.exit(1)
for p in PASSES:
    print(f"  ok: {p}")
