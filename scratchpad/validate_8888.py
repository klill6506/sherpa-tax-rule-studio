"""Throwaway-SQLite validation for the Form 8888 loader (payment-cluster batch order 2, tts s77).

Checks: guard-refusal (sentinel ships False); in-memory flip seeds + twice-run idempotency; caps;
rule-link coverage; logic oracles (two-way tie, $1 minimum, single-account routing, RTN prefix,
uniqueness, the PRINTED decrease/increase examples, BFS lowest-routing ordering, e-file blockers);
scenario outputs recomputed; FAs staged DRAFT; the bonds-discontinued language pinned.
ASCII-only. Run: poetry run python scratchpad/validate_8888.py
"""
import os
import sys

PROJECT_ROOT = r"D:\dev\sherpa-tax-rule-studio"
sys.path.insert(0, PROJECT_ROOT)

SQLITE_PATH = os.path.join(PROJECT_ROOT, "scratchpad", "validate_8888.sqlite3")
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
from specs.management.commands import load_8888 as L  # noqa: E402

FAILURES: list[str] = []
PASSES: list[str] = []


def check(cond, ok, bad):
    (PASSES if cond else FAILURES).append(ok if cond else bad)


call_command("migrate", run_syncdb=True, verbosity=0)

check(L.READY_TO_SEED is True, "READY_TO_SEED ships True (Gate-1 APPROVED 2026-07-14)", "READY_TO_SEED is not True post-approval")
L.READY_TO_SEED = False
try:
    call_command("load_8888", verbosity=0)
    FAILURES.append("guard FAILED to refuse while READY_TO_SEED=False")
except CommandError:
    PASSES.append("guard still refuses when the sentinel is off (mechanism intact)")

L.READY_TO_SEED = True
try:
    call_command("load_8888", verbosity=0)
    PASSES.append("load_8888 ran + seeded into SQLite without error (in-memory flip)")
except Exception as e:  # noqa: BLE001
    FAILURES.append(f"load_8888 raised: {e!r}")
    print("\n".join(FAILURES))
    sys.exit(1)

try:
    call_command("load_8888", verbosity=0)
    PASSES.append("second run idempotent (update_or_create everywhere)")
except Exception as e:  # noqa: BLE001
    FAILURES.append(f"second run raised: {e!r}")
finally:
    L.READY_TO_SEED = True

form = TaxForm.objects.get(form_number="8888")

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
for fa in FlowAssertion.objects.filter(assertion_id__startswith="FA-8888"):
    CAPS[f"assertion_id={fa.assertion_id}"] = (fa.assertion_id, 20)
for t in AuthorityTopic.objects.all():
    CAPS[f"topic={t.topic_code}"] = (t.topic_name, 255)
viol = [f"{k}: len {len(v)} > {cap}" for k, (v, cap) in CAPS.items() if len(v) > cap]
check(not viol, f"CharField caps OK ({len(CAPS)} checked)", "CAP VIOLATIONS:\n    " + "\n    ".join(viol))

# -- counts + identity --
check(FormFact.objects.filter(tax_form=form).count() == len(L.F8888_FACTS), f"facts {len(L.F8888_FACTS)}", "fact count mismatch")
check(FormRule.objects.filter(tax_form=form).count() == len(L.F8888_RULES), f"rules {len(L.F8888_RULES)}", "rule count mismatch")
check(FormLine.objects.filter(tax_form=form).count() == len(L.F8888_LINES), f"lines {len(L.F8888_LINES)}", "line count mismatch")
check(FormDiagnostic.objects.filter(tax_form=form).count() == len(L.F8888_DIAGNOSTICS), f"diagnostics {len(L.F8888_DIAGNOSTICS)}", "diag count mismatch")
check(TestScenario.objects.filter(tax_form=form).count() == len(L.F8888_SCENARIOS), f"scenarios {len(L.F8888_SCENARIOS)}", "scenario count mismatch")
check(form.entity_types == ["1040"], "entity_types = ['1040']", f"entity_types wrong: {form.entity_types}")
check(form.status == "draft", "form status draft", f"status {form.status}")

# -- authority links --
ruleless = [r.rule_id for r in FormRule.objects.filter(tax_form=form)
            if not RuleAuthorityLink.objects.filter(form_rule=r).exists()]
check(not ruleless, f"all {FormRule.objects.filter(tax_form=form).count()} rules have >= 1 authority link", f"ruleless: {ruleless}")
defined = {r["rule_id"] for r in L.F8888_RULES}
linked = {rl[0] for rl in L.F8888_RULE_LINKS}
check(not (linked - defined), "rule_links reference defined rules", f"orphan: {linked - defined}")
check(not (defined - linked), "every rule appears in rule_links", f"unlinked: {defined - linked}")

# -- FAs staged DRAFT --
fas = list(FlowAssertion.objects.filter(assertion_id__startswith="FA-8888"))
check(len(fas) == 3, "3 FA-8888 assertions", f"FA count {len(fas)}")
notdraft = [fa.assertion_id for fa in fas if fa.status != "draft"]
check(not notdraft, "all FA-8888 staged DRAFT (the new-FAs-default-ACTIVE trap)", f"NOT draft: {notdraft}")

# -- allocation oracles --
check(L._total_allocation([1000, 2000, 500]) == 3500, "total 1000+2000+500 = 3500", "total wrong")
check(L._total_allocation([1000, None, ""]) == 1000, "blank rows contribute nothing", "blank-row total wrong")
check(L._allocation_valid([1000, 2000, 500], 3500) is True, "tie holds -> valid (8888-A)", "valid tie wrong")
check(L._allocation_valid([1000, 2000, 400], 3500) is False, "3400 vs 3500 -> invalid (8888-B)", "mismatch wrong")
check(L._allocation_valid([1000, 0.5, 0], 1000.5) is False, "a $0.50 deposit fails the $1 minimum", "min-deposit wrong")
check(L._allocation_valid([3500, 0, 0], 3500) is True, "single-row tie still sums (routing is a separate gate)", "single-row sum wrong")

# -- split-appropriate routing --
check(L._split_appropriate(2) is True and L._split_appropriate(3) is True, "2-3 accounts -> 8888", "split 2/3 wrong")
check(L._split_appropriate(1) is False, "1 account -> the return's DD lines (8888-C)", "split 1 wrong")

# -- RTN prefix oracles (shared with the S-17b direct-deposit rule) --
check(L._rtn_valid("061000104") is True, "061000104 valid (prefix 06)", "rtn 06 wrong")
check(L._rtn_valid("253177049") is True, "253177049 valid (prefix 25)", "rtn 25 wrong")
check(L._rtn_valid("133177049") is False, "prefix 13 invalid (gap between 12 and 21)", "rtn 13 wrong")
check(L._rtn_valid("003177049") is False, "prefix 00 invalid", "rtn 00 wrong")
check(L._rtn_valid("33177049") is False, "8 digits invalid", "rtn len wrong")

# -- uniqueness (F8888-015/-016) --
check(L._accounts_unique_ok(["111", "222", "333"]) is True, "unique numbers pass", "unique wrong")
check(L._accounts_unique_ok(["111", "111"]) is False, "duplicate refuses (8888-D)", "dup wrong")
check(L._accounts_unique_ok(["000000"]) is False, "all-zeros refuses (F8888-016)", "zeros wrong")
check(L._accounts_unique_ok(["111", None, ""]) is True, "blank rows ignored", "blank unique wrong")

# -- the PRINTED examples --
check(L._decrease_ordering([100, 100, 100], 150) == [100, 50, 0], "printed decrease example: 100/100/100 -150 -> 100/50/0 (8888-G)", "decrease example wrong")
check(L._decrease_ordering([100, 100, 100], 250) == [50, 0, 0], "deeper strip: -250 -> 50/0/0", "deep decrease wrong")
check(L._decrease_ordering([100, 100, 0], 150) == [50, 0, 0], "two-account strip: line 2 first when line 3 empty", "two-acct decrease wrong")
check(L._increase_target_index([100, 100, 100]) == 2, "printed increase example: +$50 -> line 3 (8888-H)", "increase target wrong")
check(L._increase_target_index([100, 100, 0]) == 1, "two-account split: increase -> line 2", "two-acct increase wrong")

# -- BFS lowest-routing ordering --
check(L._bfs_offset_first_account(["253177049", "061000104", "999999999"]) == 1, "BFS offset hits the LOWEST routing number first", "bfs ordering wrong")

# -- e-file blockers --
clean = L._efile_blockers([1000, 2000, 500], 3500, ["111", "222", "333"], False, False)
check(clean == [], "clean three-way split -> no blockers", f"clean blockers: {clean}")
check("F8888-002-03" in L._efile_blockers([1000, 2000, 400], 3500, ["1", "2", "3"], False, False), "total mismatch -> F8888-002-03", "tie blocker wrong")
check("F8888-015" in L._efile_blockers([1000, 500, 0], 1500, ["111", "111"], False, False), "duplicate -> F8888-015", "dup blocker wrong")
check("8379-SPLIT-BAR" in L._efile_blockers([1000, 500, 0], 1500, ["1", "2"], True, False), "8379 -> split bar (8888-F)", "8379 blocker wrong")
check("BONDS-RETIRED" in L._efile_blockers([1000, 500, 0], 1500, ["1", "2"], False, True), "bond ask -> retired refusal (8888-E)", "bond blocker wrong")

# -- scenario outputs recomputed --
scenA = next(s for s in L.F8888_SCENARIOS if s["scenario_name"].startswith("8888-A"))
a_in = scenA["inputs"]
check(L._total_allocation([a_in["acct1_amount"], a_in["acct2_amount"], a_in["acct3_amount"]]) == scenA["expected_outputs"]["total_allocation"],
      "8888-A total recomputes (3500)", "8888-A total drifted")
check(L._allocation_valid([a_in["acct1_amount"], a_in["acct2_amount"], a_in["acct3_amount"]], a_in["return_refund_amount"]) is True,
      "8888-A validity recomputes", "8888-A validity drifted")
scenG = next(s for s in L.F8888_SCENARIOS if s["scenario_name"].startswith("8888-G"))
g_in = scenG["inputs"]
check(L._decrease_ordering([g_in["acct1_amount"], g_in["acct2_amount"], g_in["acct3_amount"]], g_in["decrease"]) == scenG["expected_outputs"]["adjusted"],
      "8888-G printed example recomputes ([100, 50, 0])", "8888-G drifted")

# -- diagnostic language pins --
bonds = FormDiagnostic.objects.get(tax_form=form, diagnostic_id="D_8888_BONDS")
check("DISCONTINUED" in bonds.message and "Reserved for future use" in bonds.message,
      "bonds diagnostic carries the discontinuation + line-4 language", "bonds diagnostic weak")
tie = FormDiagnostic.objects.get(tax_form=form, diagnostic_id="D_8888_TIE")
check("F8888-001-04" in tie.message and "F8888-002-03" in tie.message, "tie diagnostic cites both rules", "tie diagnostic missing rule ids")
last = FormDiagnostic.objects.get(tax_form=form, diagnostic_id="D_8888_LASTVALID")
check("LAST valid account" in last.message and "lowest routing" in last.message.lower(), "fallback diagnostic carries both orderings", "fallback diagnostic weak")

# -- constants sanity --
check(L.MAX_ACCOUNTS == 3 and L.MIN_DEPOSIT == 1 and L.MAX_ACCOUNT_CHARS == 17, "constants: 3 accounts / $1 / 17 chars", "constants drifted")
check(L.DEPOSITS_PER_ACCOUNT_YEAR == 3 and L.AMENDED_TOTAL_CAP == 999_999_999, "constants: 3/yr limit / amended cap", "limit constants drifted")

print("\n" + "=" * 70)
print(f"PASS {len(PASSES)} / FAIL {len(FAILURES)}")
if FAILURES:
    print("\nFAILURES:")
    for f in FAILURES:
        print(f"  - {f}")
    sys.exit(1)
for p in PASSES:
    print(f"  ok: {p}")
