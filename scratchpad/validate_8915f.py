"""Throwaway-SQLite validation for the Form 8915-F loader (draft-to-gate, tts s79).

Checks: the Gate-1 guard refuses while READY_TO_SEED=False (as shipped); in-memory flip seeds +
twice-run idempotency; CharField caps; rule-link coverage; logic oracles (the $22k/$100k limit
switch, the 179-day and 180-day period helpers against ALL published IRS date examples incl. the
SECURE-2.0-floor arm, the 1a-1e ladder incl. the single-disaster shortcut and the F8915F-003
boundary, the 5a/5b redesign math, line-7 excess, spread thirds + opt-out + the 11<->22
consistency gate, repayment deadline (3y+1d), the Part IV receipt window both edges, the e-file
year blockers); scenario expected_outputs recomputed from the helpers; FAs staged DRAFT; the
flagged conventions asserted PRESENT in the spec text. ASCII-only.
Run: <RS venv python> scratchpad/validate_8915f.py
"""
import datetime as dt
import os
import sys

PROJECT_ROOT = r"D:\dev\sherpa-tax-rule-studio"
sys.path.insert(0, PROJECT_ROOT)

SQLITE_PATH = os.path.join(PROJECT_ROOT, "scratchpad", "validate_8915f.sqlite3")
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
from specs.management.commands import load_8915f as L  # noqa: E402

FAILURES: list[str] = []
PASSES: list[str] = []


def check(cond, ok, bad):
    (PASSES if cond else FAILURES).append(ok if cond else bad)


call_command("migrate", run_syncdb=True, verbosity=0)

# -- Gate-1 state: Ken APPROVED 2026-07-14 (s83 approve-all, WO-28..32) — the sentinel ships True;
# prove the guard still exists by flipping it off in-memory and expecting the refusal.
check(L.READY_TO_SEED is True, "READY_TO_SEED ships True (Gate-1 APPROVED 2026-07-14)", "READY_TO_SEED is not True post-approval")
L.READY_TO_SEED = False
try:
    call_command("load_8915f", verbosity=0)
    FAILURES.append("guard FAILED to refuse while READY_TO_SEED=False")
except CommandError:
    PASSES.append("guard still refuses when the sentinel is off (mechanism intact)")

L.READY_TO_SEED = True
try:
    call_command("load_8915f", verbosity=0)
    PASSES.append("load_8915f ran + seeded into SQLite without error (in-memory flip)")
except Exception as e:  # noqa: BLE001
    FAILURES.append(f"load_8915f raised: {e!r}")
    print("\n".join(FAILURES))
    sys.exit(1)

try:
    call_command("load_8915f", verbosity=0)
    PASSES.append("second run idempotent (update_or_create everywhere)")
except Exception as e:  # noqa: BLE001
    FAILURES.append(f"second run raised: {e!r}")
finally:
    L.READY_TO_SEED = True

form = TaxForm.objects.get(form_number="8915F")

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
for fa in FlowAssertion.objects.filter(assertion_id__startswith="FA-8915F"):
    CAPS[f"assertion_id={fa.assertion_id}"] = (fa.assertion_id, 20)
for t in AuthorityTopic.objects.all():
    CAPS[f"topic={t.topic_code}"] = (t.topic_name, 255)
viol = [f"{k}: len {len(v)} > {cap}" for k, (v, cap) in CAPS.items() if len(v) > cap]
check(not viol, f"CharField caps OK ({len(CAPS)} checked)", "CAP VIOLATIONS:\n    " + "\n    ".join(viol))

# -- counts + identity --
check(FormFact.objects.filter(tax_form=form).count() == len(L.F8915F_FACTS), f"facts {len(L.F8915F_FACTS)}", "fact count mismatch")
check(FormRule.objects.filter(tax_form=form).count() == len(L.F8915F_RULES), f"rules {len(L.F8915F_RULES)}", "rule count mismatch")
check(FormLine.objects.filter(tax_form=form).count() == len(L.F8915F_LINES), f"lines {len(L.F8915F_LINES)}", "line count mismatch")
check(FormDiagnostic.objects.filter(tax_form=form).count() == len(L.F8915F_DIAGNOSTICS), f"diagnostics {len(L.F8915F_DIAGNOSTICS)}", "diag count mismatch")
check(TestScenario.objects.filter(tax_form=form).count() == len(L.F8915F_SCENARIOS), f"scenarios {len(L.F8915F_SCENARIOS)}", "scenario count mismatch")
check(form.entity_types == ["1040"], "entity_types = ['1040']", f"entity_types wrong: {form.entity_types}")
check(form.status == "draft", "form status draft", f"status {form.status}")

# -- authority links --
ruleless = [r.rule_id for r in FormRule.objects.filter(tax_form=form)
            if not RuleAuthorityLink.objects.filter(form_rule=r).exists()]
check(not ruleless, f"all {FormRule.objects.filter(tax_form=form).count()} rules have >= 1 authority link", f"ruleless: {ruleless}")
defined = {r["rule_id"] for r in L.F8915F_RULES}
linked = {rl[0] for rl in L.F8915F_RULE_LINKS}
check(not (linked - defined), "rule_links reference defined rules", f"orphan: {linked - defined}")
check(not (defined - linked), "every rule appears in rule_links", f"unlinked: {defined - linked}")
check(AuthorityExcerpt.objects.filter(authority_source__source_code__in=["IRS_F8915F", "IRS_I8915F", "MEF_8915F"]).count() >= 8,
      "8+ excerpts across the three sources", "excerpt count short")

# -- FAs staged DRAFT --
fas = list(FlowAssertion.objects.filter(assertion_id__startswith="FA-8915F"))
check(len(fas) == 3, "3 FA-8915F assertions", f"FA count {len(fas)}")
notdraft = [fa.assertion_id for fa in fas if fa.status != "draft"]
check(not notdraft, "all FA-8915F staged DRAFT (the new-FAs-default-ACTIVE trap)", f"NOT draft: {notdraft}")

# -- limit switch --
check(L._qdd_limit(2025) == 22000, "2025 disasters -> $22,000 limit", "limit 2025 wrong")
check(L._qdd_limit(2021) == 22000, "2021 disasters -> $22,000", "limit 2021 wrong")
check(L._qdd_limit(2020) == 100000, "2020 vintage -> $100,000", "limit 2020 wrong")

# -- the 179-day distribution period: ALL published IRS example pins --
D = dt.date
check(L._qdd_period_end(D(2022, 11, 3), D(2023, 1, 12)) == D(2023, 7, 10),
      "DR-4682-WA -> 7/10/2023 (179d after the 1/12/23 declaration)", "DR-4682-WA period wrong")
check(L._qdd_period_end(D(2022, 10, 1), D(2022, 12, 30)) == D(2023, 6, 27),
      "DR-4681 -> 6/27/2023 (179d after 12/30/22)", "DR-4681 period wrong")
check(L._qdd_period_end(D(2023, 1, 12), D(2023, 1, 16)) == D(2023, 7, 14),
      "DR-4685-GA -> 7/14/2023 (179d after 1/16/23)", "DR-4685-GA period wrong")
check(L._qdd_period_end(D(2022, 1, 2), D(2022, 3, 11)) == D(2023, 6, 26),
      "DR-4644-VA -> 6/26/2023 (the SECURE-2.0 12/29/22 floor arm; published)", "SECURE floor arm wrong")

# -- the 180-day Part IV repayment period: the one-day asymmetry pinned --
check(L._qd_repayment_period_end(D(2022, 11, 3), D(2023, 1, 12)) == D(2023, 7, 11),
      "DR-4682-WA repay -> 7/11/2023 (180d — one day past the Part I end)", "DR-4682-WA repay wrong")
check(L._qd_repayment_period_end(D(2022, 10, 1), D(2022, 12, 30)) == D(2023, 6, 28),
      "DR-4681 repay -> 6/28/2023", "DR-4681 repay wrong")
check(L._qd_repayment_period_end(D(2023, 1, 12), D(2023, 1, 16)) == D(2023, 7, 15),
      "DR-4685-GA repay -> 7/15/2023", "DR-4685-GA repay wrong")
check(L._qd_repayment_period_end(D(2022, 1, 2), D(2022, 3, 11)) == D(2023, 6, 27),
      "DR-4644-VA repay -> 6/27/2023 (published: 180d after 12/29/22)", "VA repay floor wrong")
check(L.QDD_PERIOD_DAYS == 179 and L.QD_REPAY_PERIOD_DAYS == 180,
      "constants: 179-day distributions / 180-day repayments (the Appendix-D class)", "period constants drifted")

# -- the 1a-1e ladder --
check(L._line1e(2025, 1, 0, 0) == (0, 0, 0, 0, 22000), "single NEW disaster -> the 1e = $22,000 shortcut", "shortcut wrong")
check(L._line1e(2025, 2, 0, 0) == (0, 0, 0, 44000, 44000), "two new disasters -> 1d = 1e = 44,000", "two-disaster ladder wrong")
check(L._line1e(2025, 0, 1, 8000) == (22000, 8000, 14000, 0, 14000), "repeat disaster w/ 8,000 prior -> 1c = 1e = 14,000", "repeat ladder wrong")
check(L._line1e(2020, 1, 0, 0) == (0, 0, 0, 0, 100000), "2020 vintage single -> 1e = $100,000", "2020 ladder wrong")
check(L._line1d_cap_ok(44000, 2025, 2) is True, "1d = 44,000 with 2 disasters -> AT the F8915F-003 cap (8915F-D)", "cap boundary wrong")
check(L._line1d_cap_ok(44001, 2025, 2) is False, "1d = 44,001 -> exceeds the cap", "cap over wrong")
check(L._line1d_cap_ok(100000, 2020, 1) is True, "2020 vintage: 100,000 x 1 OK", "cap 2020 wrong")

# -- the 5a/5b redesign + line 7 --
check(L._line5b(18000, 0, 22000) == (18000, 18000), "5b: 18,000 under the 22,000 cap (8915F-A)", "5b under-cap wrong")
check(L._line5b(30000, 0, 22000) == (30000, 22000), "5b: 30,000 caps at 22,000 (8915F-C)", "5b cap wrong")
check(L._line5b(30000, 12000, 22000) == (18000, 18000), "5b: the NEW 5a carve-out (30,000 - 12,000 non-QDD)", "5a carve-out wrong")
check(L._line7_excess(30000, 22000) == 8000, "line 7 = 8,000 excess (8915F-C)", "line 7 wrong")
check(L._line7_excess(18000, 18000) == 0, "line 7 = 0 when fully qualified", "line 7 zero wrong")

# -- spread + opt-out consistency --
check(L._spread_amount(18000, False) == 6000, "18,000 / 3.0 = 6,000 (8915F-A)", "spread wrong")
check(L._spread_amount(18000, True) == 18000, "opt-out -> the full 18,000 (8915F-B)", "opt-out wrong")
check(L._spread_amount(9000, False) == 3000, "9,000 / 3.0 = 3,000 (8915F-G)", "spread G wrong")
check(L._optout_boxes_consistent(True, True, True, True) is True, "both boxes checked -> consistent", "optout both wrong")
check(L._optout_boxes_consistent(True, True, True, False) is False, "11 checked, 22 not, both parts -> INCONSISTENT", "optout mismatch wrong")
check(L._optout_boxes_consistent(True, True, False, False) is True, "Part III not engaged -> the pairing rule is moot (8915F-B)", "optout moot wrong")
check(L._optout_boxes_consistent(True, False, True, True) is False, "22 checked, 11 not -> inconsistent (the converse)", "optout converse wrong")

# -- taxable floors --
check(L._part_taxable(5000, 3000) == 2000, "15/26 math: 5,000 - 3,000 = 2,000 (8915F-F)", "taxable wrong")
check(L._part_taxable(5000, 6000) == 0, "repayments exceed income -> -0- floor", "taxable floor wrong")

# -- repayment deadline (3 years from the day after receipt) --
check(L._repayment_deadline(D(2025, 3, 10)) == D(2028, 3, 11), "received 3/10/25 -> repay through 3/11/28 (3y from the day after)", "repay deadline wrong")

# -- Part IV receipt window (both edges) --
begin, end = D(2025, 9, 26), D(2025, 10, 4)
check(L._qd_receipt_window_ok(D(2025, 3, 30), begin, end) is True, "receipt at begin-180d exactly -> in window", "window lo edge wrong")
check(L._qd_receipt_window_ok(D(2025, 3, 29), begin, end) is False, "receipt 181d before -> out", "window lo out wrong")
check(L._qd_receipt_window_ok(D(2025, 11, 3), begin, end) is True, "receipt at end+30d exactly -> in window", "window hi edge wrong")
check(L._qd_receipt_window_ok(D(2025, 11, 4), begin, end) is False, "receipt 31d after -> out", "window hi out wrong")

# -- e-file year blockers --
check(L._efile_year_blockers("2026", "2026") == ["F8915F-002-01", "F8915F-001-01"],
      "item A 2026 + item B 2026 -> both year rejects (8915F-J)", "year blockers wrong")
check(L._efile_year_blockers("2025", "2025") == [], "2025/2025 -> clean", "clean year wrong")
check(L._efile_year_blockers("2025", "2024") == [], "continuation year (A 2025 / B 2024) -> clean (8915F-E)", "continuation year wrong")

# -- scenario expected_outputs recomputed from the helpers --
scenA = next(s for s in L.F8915F_SCENARIOS if s["scenario_name"].startswith("8915F-A"))
_, _, _, _, l1e_A = L._line1e(2025, scenA["inputs"]["new_disaster_count"], scenA["inputs"]["repeat_disaster_count"], scenA["inputs"]["prior_year_qdds"])
check(l1e_A == scenA["expected_outputs"]["line1e"], "8915F-A 1e recomputes (22,000)", "8915F-A 1e drifted")
_, l5bb_A = L._line5b(scenA["inputs"]["dist_other_than_ira"], scenA["inputs"]["nonqualified_portion"], l1e_A)
check(l5bb_A == scenA["expected_outputs"]["line5b_b"] == scenA["expected_outputs"]["line6"], "8915F-A 5b(b)/6 recompute (18,000)", "8915F-A 5b drifted")
check(L._spread_amount(l5bb_A, scenA["inputs"]["opt_out_spread_p2"]) == scenA["expected_outputs"]["line11"], "8915F-A line 11 recomputes (6,000)", "8915F-A spread drifted")
scenC = next(s for s in L.F8915F_SCENARIOS if s["scenario_name"].startswith("8915F-C"))
_, l5bb_C = L._line5b(scenC["inputs"]["dist_other_than_ira"], scenC["inputs"]["nonqualified_portion"], 22000)
check(l5bb_C == scenC["expected_outputs"]["line5b_b"], "8915F-C cap recomputes (22,000)", "8915F-C cap drifted")
check(L._line7_excess(scenC["inputs"]["dist_other_than_ira"], l5bb_C) == scenC["expected_outputs"]["line7"], "8915F-C line 7 recomputes (8,000)", "8915F-C line7 drifted")
scenD = next(s for s in L.F8915F_SCENARIOS if s["scenario_name"].startswith("8915F-D"))
_, _, _, l1d_D, l1e_D = L._line1e(2025, scenD["inputs"]["new_disaster_count"], scenD["inputs"]["repeat_disaster_count"], scenD["inputs"]["prior_year_qdds"])
check(l1d_D == scenD["expected_outputs"]["line1d"] and l1e_D == scenD["expected_outputs"]["line1e"], "8915F-D ladder recomputes (44,000)", "8915F-D ladder drifted")
check(L._line1d_cap_ok(l1d_D, 2025, 2) is scenD["expected_outputs"]["cap_ok"], "8915F-D cap-boundary recomputes", "8915F-D cap drifted")
scenF = next(s for s in L.F8915F_SCENARIOS if s["scenario_name"].startswith("8915F-F"))
check(L._part_taxable(scenF["inputs"]["prior_year_income_p2"], scenF["inputs"]["repayments_p2"]) == scenF["expected_outputs"]["line15"],
      "8915F-F line 15 recomputes (2,000)", "8915F-F drifted")
scenG = next(s for s in L.F8915F_SCENARIOS if s["scenario_name"].startswith("8915F-G"))
l21_G = scenG["inputs"]["f8606_line15b"] + scenG["inputs"]["f8606_line25b"] + scenG["inputs"]["line20_not_on_8606"]
check(l21_G == scenG["expected_outputs"]["line21"], "8915F-G line 21 recomputes (9,000)", "8915F-G 21 drifted")
check(L._spread_amount(l21_G, scenG["inputs"]["opt_out_spread_p3"]) == scenG["expected_outputs"]["line22"], "8915F-G line 22 recomputes (3,000)", "8915F-G 22 drifted")
scenH = next(s for s in L.F8915F_SCENARIOS if s["scenario_name"].startswith("8915F-H"))
hb = dt.date.fromisoformat(scenH["inputs"]["disaster_begin_date"])
hd = dt.date.fromisoformat(scenH["inputs"]["disaster_declaration_date"])
check(L._qdd_period_end(hb, hd).isoformat() == scenH["expected_outputs"]["qdd_period_end"], "8915F-H period pin recomputes (7/10)", "8915F-H period drifted")
check(L._qd_repayment_period_end(hb, hd).isoformat() == scenH["expected_outputs"]["qd_repay_period_end"], "8915F-H repay pin recomputes (7/11)", "8915F-H repay drifted")
scenI = next(s for s in L.F8915F_SCENARIOS if s["scenario_name"].startswith("8915F-I"))
l30_I = scenI["inputs"]["mainhome_distributions"] - scenI["inputs"]["mainhome_cost"]
check(l30_I == scenI["expected_outputs"]["line30"], "8915F-I line 30 recomputes (15,000)", "8915F-I 30 drifted")
check(L._part_taxable(l30_I, scenI["inputs"]["mainhome_repayments"]) == scenI["expected_outputs"]["line32"], "8915F-I line 32 recomputes (0)", "8915F-I 32 drifted")
scenJ = next(s for s in L.F8915F_SCENARIOS if s["scenario_name"].startswith("8915F-J"))
check(L._efile_year_blockers(scenJ["inputs"]["item_a_tax_year"], scenJ["inputs"]["item_b_disaster_year"]) == scenJ["expected_outputs"]["efile_blockers"],
      "8915F-J blockers recompute", "8915F-J blockers drifted")

# -- diagnostic language pins --
cap_diag = FormDiagnostic.objects.get(tax_form=form, diagnostic_id="D_8915F_1DCAP")
check("F8915F-003" in cap_diag.message and "$22,000" in cap_diag.message, "1d-cap diagnostic cites F8915F-003 + $22,000", "cap diagnostic weak")
rpy_diag = FormDiagnostic.objects.get(tax_form=form, diagnostic_id="D_8915F_QDRPYEND")
check("180" in rpy_diag.message and "179" in rpy_diag.message, "Part IV repay diagnostic carries the 180-vs-179 asymmetry", "repay diagnostic weak")
land_diag = FormDiagnostic.objects.get(tax_form=form, diagnostic_id="D_8915F_LANDINGS")
check("5b" in land_diag.message and "4b" in land_diag.message, "landings diagnostic names 5b + 4b", "landings diagnostic weak")
wvr_diag = FormDiagnostic.objects.get(tax_form=form, diagnostic_id="D_8915F_WAIVER")
check("5329" in wvr_diag.message, "waiver diagnostic names Form 5329", "waiver diagnostic weak")
opt_diag = FormDiagnostic.objects.get(tax_form=form, diagnostic_id="D_8915F_OPTOUT")
check("line 22" in opt_diag.message, "opt-out diagnostic quotes the box-matching sentence", "opt-out diagnostic weak")

# -- the flagged conventions live in the spec text (walk items, not silent) --
spread_rule = FormRule.objects.get(tax_form=form, rule_id="R-8915F-SPREAD")
check("FLAGGED" in spread_rule.formula and "3.0" in spread_rule.formula,
      "R-8915F-SPREAD flags the /3.0 rounding convention", "the spread convention flag is missing")
p4_rule = FormRule.objects.get(tax_form=form, rule_id="R-8915F-PART4")
check("NOT 179" in p4_rule.formula, "R-8915F-PART4 pins the 180-vs-179 asymmetry", "the Part IV asymmetry flag is missing")
efile_rule = FormRule.objects.get(tax_form=form, rule_id="R-8915F-EFILE")
check("maxOccurs=6" in efile_rule.formula, "R-8915F-EFILE carries the max-6 document count", "the max-6 note is missing")

# -- constants sanity --
check(L.QDD_LIMIT == 22000 and L.QDD_LIMIT_2020 == 100000, "constants: $22,000 / $100,000", "limit constants drifted")
check(L.MEF_MAX_DOCS == 6 and L.SPREAD_YEARS == 3 and L.REPAY_YEARS == 3, "constants: max 6 docs / 3-year spread / 3-year repay", "doc constants drifted")
check(L.QD_WINDOW_BEFORE_DAYS == 180 and L.QD_WINDOW_AFTER_DAYS == 30, "constants: the [-180d, +30d] receipt window", "window constants drifted")
check(L.SECURE20_ENACTED == dt.date(2022, 12, 29), "constant: the 12/29/2022 latest-of floor", "enactment date drifted")
check(L.LANDING_OTHER_THAN_IRA == "1040_5B" and L.LANDING_IRA == "1040_4B", "constants: the 5b/4b landings", "landing constants drifted")

print("\n" + "=" * 70)
print(f"PASS {len(PASSES)} / FAIL {len(FAILURES)}")
if FAILURES:
    print("\nFAILURES:")
    for f in FAILURES:
        print(f"  - {f}")
    sys.exit(1)
for p in PASSES:
    print(f"  ok: {p}")
