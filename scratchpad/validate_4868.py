"""Throwaway-SQLite validation for the Form 4868 loader (draft-to-gate, tts s78).

Checks: the Gate-1 guard refuses while READY_TO_SEED=False (as shipped); in-memory flip seeds +
twice-run idempotency; CharField caps; rule-link coverage; logic oracles (L6 floor math, filing
windows/deadlines incl. the OOC and NR arms, the extended-due-date landings incl. the derived
Dec-15, the 90% safe harbor at the boundary, the FPYMT-052-02 EFW tie, the payment-triggered
signature rule, the jurat ladder, the joint-ampersand rule both directions, the address chart
incl. roster partition + the four-way Charlotte divergence); scenario expected_outputs recomputed
from the helpers; FAs staged DRAFT; the flagged seams (FPYMT-088-11 staleness + version seam)
present in the spec text. ASCII-only. Run: <RS venv python> scratchpad/validate_4868.py
"""
import os
import sys

PROJECT_ROOT = r"D:\dev\sherpa-tax-rule-studio"
sys.path.insert(0, PROJECT_ROOT)

SQLITE_PATH = os.path.join(PROJECT_ROOT, "scratchpad", "validate_4868.sqlite3")
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
from specs.management.commands import load_4868 as L  # noqa: E402

FAILURES: list[str] = []
PASSES: list[str] = []


def check(cond, ok, bad):
    (PASSES if cond else FAILURES).append(ok if cond else bad)


call_command("migrate", run_syncdb=True, verbosity=0)

# -- Gate-1 state: draft ships GATED. Prove the refusal, then seed with an in-memory flip.
check(L.READY_TO_SEED is False, "READY_TO_SEED ships False (Gate-1 PENDING)", "READY_TO_SEED is not False in the draft")
try:
    call_command("load_4868", verbosity=0)
    FAILURES.append("guard FAILED to refuse while READY_TO_SEED=False")
except CommandError:
    PASSES.append("guard refuses to seed while the sentinel is off")

L.READY_TO_SEED = True
try:
    call_command("load_4868", verbosity=0)
    PASSES.append("load_4868 ran + seeded into SQLite without error (in-memory flip)")
except Exception as e:  # noqa: BLE001
    FAILURES.append(f"load_4868 raised: {e!r}")
    print("\n".join(FAILURES))
    sys.exit(1)

try:
    call_command("load_4868", verbosity=0)
    PASSES.append("second run idempotent (update_or_create everywhere)")
except Exception as e:  # noqa: BLE001
    FAILURES.append(f"second run raised: {e!r}")
finally:
    L.READY_TO_SEED = False

form = TaxForm.objects.get(form_number="4868")

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
for fa in FlowAssertion.objects.filter(assertion_id__startswith="FA-4868"):
    CAPS[f"assertion_id={fa.assertion_id}"] = (fa.assertion_id, 20)
for t in AuthorityTopic.objects.all():
    CAPS[f"topic={t.topic_code}"] = (t.topic_name, 255)
viol = [f"{k}: len {len(v)} > {cap}" for k, (v, cap) in CAPS.items() if len(v) > cap]
check(not viol, f"CharField caps OK ({len(CAPS)} checked)", "CAP VIOLATIONS:\n    " + "\n    ".join(viol))

# -- counts + identity --
check(FormFact.objects.filter(tax_form=form).count() == len(L.F4868_FACTS), f"facts {len(L.F4868_FACTS)}", "fact count mismatch")
check(FormRule.objects.filter(tax_form=form).count() == len(L.F4868_RULES), f"rules {len(L.F4868_RULES)}", "rule count mismatch")
check(FormLine.objects.filter(tax_form=form).count() == len(L.F4868_LINES), f"lines {len(L.F4868_LINES)}", "line count mismatch")
check(FormDiagnostic.objects.filter(tax_form=form).count() == len(L.F4868_DIAGNOSTICS), f"diagnostics {len(L.F4868_DIAGNOSTICS)}", "diag count mismatch")
check(TestScenario.objects.filter(tax_form=form).count() == len(L.F4868_SCENARIOS), f"scenarios {len(L.F4868_SCENARIOS)}", "scenario count mismatch")
check(form.entity_types == ["1040"], "entity_types = ['1040']", f"entity_types wrong: {form.entity_types}")
check(form.status == "draft", "form status draft", f"status {form.status}")

# -- authority links --
ruleless = [r.rule_id for r in FormRule.objects.filter(tax_form=form)
            if not RuleAuthorityLink.objects.filter(form_rule=r).exists()]
check(not ruleless, f"all {FormRule.objects.filter(tax_form=form).count()} rules have >= 1 authority link", f"ruleless: {ruleless}")
defined = {r["rule_id"] for r in L.F4868_RULES}
linked = {rl[0] for rl in L.F4868_RULE_LINKS}
check(not (linked - defined), "rule_links reference defined rules", f"orphan: {linked - defined}")
check(not (defined - linked), "every rule appears in rule_links", f"unlinked: {defined - linked}")
check(AuthorityExcerpt.objects.filter(authority_source__source_code__in=["IRS_F4868", "MEF_4868_PKG"]).count() >= 7,
      "7+ excerpts across the two sources", "excerpt count short")

# -- FAs staged DRAFT --
fas = list(FlowAssertion.objects.filter(assertion_id__startswith="FA-4868"))
check(len(fas) == 3, "3 FA-4868 assertions", f"FA count {len(fas)}")
notdraft = [fa.assertion_id for fa in fas if fa.status != "draft"]
check(not notdraft, "all FA-4868 staged DRAFT (the new-FAs-default-ACTIVE trap)", f"NOT draft: {notdraft}")

# -- L6 floor-math oracles --
check(L._balance_due(20000, 15000) == 5000, "L6: 20,000 - 15,000 -> 5,000 (4868-A)", "L6 basic wrong")
check(L._balance_due(20000, 22000) == 0, "L6: payments exceed tax -> -0- floor (4868-B)", "L6 floor wrong")
check(L._balance_due(0, 0) == 0, "L6: zero liability -> 0 (4868-C)", "L6 zero wrong")
check(L._balance_due(40000, 32000) == 8000, "L6: 40,000 - 32,000 -> 8,000 (4868-D)", "L6 partial wrong")
check(L._balance_due(100, 100) == 0, "L6: equal -> 0", "L6 equal wrong")
check(L._balance_due(None, None) == 0, "L6: blanks -> 0", "L6 blank wrong")

# -- filing-deadline / window oracles (F4868-001-02 / -002-01) --
check(L._filing_deadline(False, False) == "2026-04-15", "deadline: no boxes -> 4/15/2026", "deadline base wrong")
check(L._filing_deadline(True, False) == "2026-06-15", "deadline: line 8 -> 6/15/2026", "deadline OOC wrong")
check(L._filing_deadline(False, True) == "2026-06-15", "deadline: line 9 -> 6/15/2026", "deadline NR wrong")
check(L._filing_window_ok("2026-04-15", False, False) is True, "4/15 exactly is timely (on-or-before)", "window boundary wrong")
check(L._filing_window_ok("2026-04-16", False, False) is False, "4/16 without a box is LATE (4868-J)", "window late wrong")
check(L._filing_window_ok("2026-05-20", True, False) is True, "5/20 with line 8 is timely (4868-F)", "window OOC wrong")
check(L._filing_window_ok("2026-06-15", False, True) is True, "6/15 exactly with line 9 is timely (4868-G)", "window NR boundary wrong")
check(L._filing_window_ok("2026-06-16", True, False) is False, "6/16 with line 8 is late", "window OOC late wrong")
check(L._filing_window_ok("2025-12-31", False, False) is False, "the period-end day itself is too early (F4868-001: AFTER TaxPeriodEndDate)", "window early wrong")
check(L._filing_window_ok("2026-01-01", False, False) is True, "1/1/2026 is the first filable day", "window first-day wrong")

# -- extended-due-date landings --
check(L._extended_due_date(False, False) == "2026-10-15", "extension lands 10/15 (6 months)", "ext due base wrong")
check(L._extended_due_date(True, False) == "2026-10-15", "line 8 ALSO lands 10/15 (auto 2 + 4 more)", "ext due OOC wrong")
check(L._extended_due_date(False, True) == "2026-12-15", "line 9 lands 12/15 (derived: 6 months from 6/15)", "ext due NR wrong")
check(L._extended_due_date(True, True) == "2026-10-15", "both boxes -> the line-8 Oct-15 landing", "ext due both wrong")

# -- 90% safe-harbor oracles (prong 1) --
check(L._safe_harbor_met(40000, 36000) is True, "exactly 90% paid meets 'at least 90%' (4868-E)", "harbor boundary wrong")
check(L._safe_harbor_met(40000, 34000) is False, "85% paid misses the harbor (4868-D)", "harbor miss wrong")
check(L._safe_harbor_met(40000, 35999) is False, "one dollar under 90% misses", "harbor near-miss wrong")
check(L._safe_harbor_met(0, 0) is True, "zero tax -> harbor trivially met", "harbor zero wrong")

# -- EFW tie (FPYMT-052-02) --
check(L._efw_amount_consistent(5000, 5000) is True, "L7 5,000 == EFW 5,000 -> consistent (4868-A)", "efw match wrong")
check(L._efw_amount_consistent(3000, 2500) is False, "L7 3,000 != EFW 2,500 -> refuses (4868-H)", "efw mismatch wrong")
check(L._efw_amount_consistent(3000, None) is True, "no EFW record -> L7 unconstrained", "efw none wrong")

# -- signature story (R0000-098) + jurat ladder (F4868-007/8/9) --
check(L._signature_required(True) is True, "payment record -> PIN required", "sig with payment wrong")
check(L._signature_required(False) is False, "no payment record -> NO signature at all", "sig without payment wrong")
check(L._jurat_code("Practitioner") == "Form 4868 with Practitioner PIN and EFW", "Practitioner jurat (F4868-008)", "jurat practitioner wrong")
check(L._jurat_code("Self-Select Practitioner") == "Form 4868", "Self-Select Practitioner jurat (F4868-007)", "jurat ssp wrong")
check(L._jurat_code("Self-Select On-Line") == "Form 4868", "Self-Select On-Line jurat (F4868-009)", "jurat sso wrong")
check(len(set(L.JURAT_CODES.values())) == 2, "the header enum has exactly two jurat values", "jurat enum wrong")

# -- joint-ampersand rule (F4868-003 / R0000-123, both directions) --
check(L._joint_name_ok("KEN & JAN EXAMPLE", "400-00-1111") is True, "spouse SSN + ampersand -> OK", "amp ok wrong")
check(L._joint_name_ok("KEN EXAMPLE", "400-00-1111") is False, "spouse SSN without ampersand -> refuses (4868-I)", "amp missing wrong")
check(L._joint_name_ok("KEN & JAN EXAMPLE", None) is False, "ampersand without spouse SSN -> refuses (R0000-123)", "amp converse wrong")
check(L._joint_name_ok("KEN EXAMPLE", None) is True, "single name, no spouse -> OK", "amp single wrong")

# -- address chart oracles (year-watched; the four-way Charlotte trap) --
check(L._mailing_address("GA", True) == "CHARLOTTE_1302", "GA with payment -> Charlotte Box 1302", "GA payment wrong")
check(L._mailing_address("GA", False) == "AUSTIN_0045", "GA without payment -> Austin 73301-0045", "GA no-payment wrong")
check(L._mailing_address("NY", True) == "LOUISVILLE_931300", "NY with payment -> Louisville 931300", "NY payment wrong")
check(L._mailing_address("NY", False) == "KANSAS_CITY_0045", "NY without payment -> Kansas City", "NY no-payment wrong")
check(L._mailing_address("CA", False) == "OGDEN_0045", "CA without payment -> Ogden", "CA no-payment wrong")
check(L._mailing_address("AZ", False) == "AUSTIN_0045", "AZ without payment -> Austin 0045", "AZ no-payment wrong")
check(L._mailing_address("TX", True) == "CHARLOTTE_1302", "TX with payment -> Charlotte 1302 (southern row)", "TX payment wrong")
check(L._mailing_address("GA", True, foreign_or_territory=True) == "CHARLOTTE_1303", "foreign flag overrides -> Charlotte 1303", "foreign payment wrong")
check(L._mailing_address("GA", False, foreign_or_territory=True) == "AUSTIN_0215", "foreign no payment -> Austin 0215", "foreign no-payment wrong")
# roster hygiene: payment rosters and no-payment rosters both partition the 50 states + DC
pay_union = L.ADDR_CHARLOTTE_1302 | L.ADDR_LOUISVILLE
nopay_union = L.ADDR_NOPAY_AUSTIN | L.ADDR_NOPAY_KC | L.ADDR_NOPAY_OGDEN
check(len(L.ADDR_CHARLOTTE_1302) == 9, "Charlotte-1302 roster = 9 southern states", f"1302 roster {len(L.ADDR_CHARLOTTE_1302)}")
check(len(pay_union) == 51 and not (L.ADDR_CHARLOTTE_1302 & L.ADDR_LOUISVILLE),
      "payment rosters partition 50 states + DC (disjoint, 51)", f"payment union {len(pay_union)}")
check(len(nopay_union) == 51 and pay_union == nopay_union,
      "no-payment rosters cover the SAME 51 jurisdictions", f"no-payment union {len(nopay_union)}")
# the cluster divergence: the 4868 box is neither the V box (1214) nor the ES box (1300)
addr_diag = FormDiagnostic.objects.get(tax_form=form, diagnostic_id="D_4868_ADDR")
for token in ("1302", "1214", "1300"):
    check(token in addr_diag.message, f"address diagnostic names Box {token} (the cluster trap)", f"address diagnostic missing {token}")

# -- scenario expected_outputs recomputed from the helpers --
scenA = next(s for s in L.F4868_SCENARIOS if s["scenario_name"].startswith("4868-A"))
check(L._balance_due(scenA["inputs"]["estimated_total_tax"], scenA["inputs"]["estimated_payments"]) == scenA["expected_outputs"]["balance_due"],
      "4868-A balance recomputes (5,000)", "4868-A balance drifted")
check(L._efw_amount_consistent(scenA["inputs"]["amount_paying"], scenA["inputs"]["efw_payment_amount"]) is scenA["expected_outputs"]["efw_consistent"],
      "4868-A EFW pin recomputes", "4868-A EFW drifted")
check(L._jurat_code(scenA["inputs"]["pin_type"]) == scenA["expected_outputs"]["jurat_code"],
      "4868-A jurat recomputes", "4868-A jurat drifted")
scenB = next(s for s in L.F4868_SCENARIOS if s["scenario_name"].startswith("4868-B"))
check(L._balance_due(scenB["inputs"]["estimated_total_tax"], scenB["inputs"]["estimated_payments"]) == scenB["expected_outputs"]["balance_due"],
      "4868-B floor recomputes (0)", "4868-B floor drifted")
check(L._signature_required(scenB["inputs"]["efw_payment_amount"] is not None) is scenB["expected_outputs"]["signature_required"],
      "4868-B no-payment-no-signature recomputes", "4868-B signature drifted")
scenD = next(s for s in L.F4868_SCENARIOS if s["scenario_name"].startswith("4868-D"))
paid_D = scenD["inputs"]["estimated_payments"] + scenD["inputs"]["amount_paying"]
check(L._safe_harbor_met(scenD["inputs"]["estimated_total_tax"], paid_D) is scenD["expected_outputs"]["safe_harbor_met"],
      "4868-D harbor miss recomputes (85%)", "4868-D harbor drifted")
scenE = next(s for s in L.F4868_SCENARIOS if s["scenario_name"].startswith("4868-E"))
paid_E = scenE["inputs"]["estimated_payments"] + scenE["inputs"]["amount_paying"]
check(L._safe_harbor_met(scenE["inputs"]["estimated_total_tax"], paid_E) is scenE["expected_outputs"]["safe_harbor_met"],
      "4868-E harbor boundary recomputes (90% exactly)", "4868-E harbor drifted")
scenF = next(s for s in L.F4868_SCENARIOS if s["scenario_name"].startswith("4868-F"))
check(L._filing_window_ok(scenF["inputs"]["filed_date"], True, False) is scenF["expected_outputs"]["window_ok"],
      "4868-F OOC window recomputes", "4868-F window drifted")
check(L._extended_due_date(True, False) == scenF["expected_outputs"]["extended_due_date"],
      "4868-F Oct-15 landing recomputes", "4868-F landing drifted")
scenG = next(s for s in L.F4868_SCENARIOS if s["scenario_name"].startswith("4868-G"))
check(L._extended_due_date(False, True) == scenG["expected_outputs"]["extended_due_date"],
      "4868-G Dec-15 landing recomputes (derived)", "4868-G landing drifted")
scenH = next(s for s in L.F4868_SCENARIOS if s["scenario_name"].startswith("4868-H"))
check(L._efw_amount_consistent(scenH["inputs"]["amount_paying"], scenH["inputs"]["efw_payment_amount"]) is scenH["expected_outputs"]["efw_consistent"],
      "4868-H EFW mismatch recomputes", "4868-H EFW drifted")
scenI = next(s for s in L.F4868_SCENARIOS if s["scenario_name"].startswith("4868-I"))
check(L._joint_name_ok(scenI["inputs"]["name_line"], scenI["inputs"]["spouse_ssn"]) is scenI["expected_outputs"]["joint_name_ok"],
      "4868-I ampersand refusal recomputes", "4868-I ampersand drifted")
scenJ = next(s for s in L.F4868_SCENARIOS if s["scenario_name"].startswith("4868-J"))
check(L._filing_window_ok(scenJ["inputs"]["filed_date"], False, False) is scenJ["expected_outputs"]["window_ok"],
      "4868-J late-filing refusal recomputes", "4868-J window drifted")

# -- diagnostic language pins --
efw_diag = FormDiagnostic.objects.get(tax_form=form, diagnostic_id="D_4868_EFWTIE")
check("FPYMT-052-02" in efw_diag.message, "EFW diagnostic cites FPYMT-052-02", "EFW diagnostic missing the rule id")
late_diag = FormDiagnostic.objects.get(tax_form=form, diagnostic_id="D_4868_LATE")
check("April 15, 2026" in late_diag.message, "late diagnostic carries the year-keyed 4/15/2026", "late diagnostic missing the date")
partial_diag = FormDiagnostic.objects.get(tax_form=form, diagnostic_id="D_4868_PARTIAL")
check("90%" in partial_diag.message and "1/2%" in partial_diag.message, "partial-pay diagnostic carries 90% + 1/2%", "partial diagnostic weak")
sign_diag = FormDiagnostic.objects.get(tax_form=form, diagnostic_id="D_4868_SIGN")
check("R0000-098" in sign_diag.message, "signature diagnostic cites R0000-098", "signature diagnostic missing the rule id")

# -- the flagged seams live in the spec text (walk items, not silent) --
efile_rule = FormRule.objects.get(tax_form=form, rule_id="R-4868-EFILE")
check("FPYMT-088-11" in efile_rule.formula and "stale" in efile_rule.formula,
      "R-4868-EFILE flags the stale FPYMT-088-11 ES-date list", "the FPYMT-088-11 flag is missing")
check("VERSION SEAM" in efile_rule.formula, "R-4868-EFILE flags the 2025-face/TY2026-package seam", "the version-seam flag is missing")
check("R0000-195" in efile_rule.formula, "R-4868-EFILE carries the no-binary-attachment refusal", "the attachment refusal is missing")
extent_rule = FormRule.objects.get(tax_form=form, rule_id="R-4868-EXTENT")
check("DERIVED" in extent_rule.formula, "R-4868-EXTENT marks the Dec-15 arm as derived", "the derived flag is missing")

# -- constants sanity --
check(L.SAFE_HARBOR_PCT == 90 and L.PENALTY_MAX_PCT == 25, "constants: 90% harbor / 25% caps", "harbor constants drifted")
check(L.MIN_LATE_FILE_PENALTY == 525, "constant: $525 minimum late-file penalty (YEAR-KEYED TY2025)", "penalty minimum drifted")
check(L.EXTENSION_MONTHS == 6 and L.OOC_EXTRA_MONTHS == 4, "constants: 6 months / +4 OOC", "month constants drifted")
check(L.ES_MAX_RECORDS == 4, "constant: IRSESPayment maxOccurs=4", "ES max drifted")
check(L.CREDIT_LINE == "SCH3_10", "constant: credit routes to Schedule 3 line 10", "credit line drifted")
check(L.DUE_DATE == "2026-04-15" and L.OOC_DUE_DATE == "2026-06-15" and L.EXTENDED_DUE == "2026-10-15"
      and L.NR_EXTENDED_DUE == "2026-12-15" and L.PERIOD_END == "2025-12-31",
      "date constants: 4/15 / 6/15 / 10/15 / 12/15 / period end (YEAR-KEYED)", "date constants drifted")

print("\n" + "=" * 70)
print(f"PASS {len(PASSES)} / FAIL {len(FAILURES)}")
if FAILURES:
    print("\nFAILURES:")
    for f in FAILURES:
        print(f"  - {f}")
    sys.exit(1)
for p in PASSES:
    print(f"  ok: {p}")
