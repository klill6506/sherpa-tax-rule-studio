"""Throwaway-SQLite validation for the Form 2553 loader (WO-26, SPINE S-20b).

Checks: the Gate-1 guard refuses while READY_TO_SEED=False; CharField caps; every rule >= 1
authority link + full link coverage; logic oracles (the deadline math vs the three published i2553
examples + the no-corresponding-day and leap-year edges; timeliness incl. preceding-year and
invalid-early; shareholder aggregation; the late-relief path chooser; consent scope; Part II
routing); scenario expected_outputs recomputed from the helpers; FAs staged DRAFT; entity_types.
ASCII-only. Run: poetry run python scratchpad/validate_2553.py
"""
import os
import sys
from datetime import date

PROJECT_ROOT = r"D:\dev\sherpa-tax-rule-studio"
sys.path.insert(0, PROJECT_ROOT)

SQLITE_PATH = os.path.join(PROJECT_ROOT, "scratchpad", "validate_2553.sqlite3")
if os.path.exists(SQLITE_PATH):
    os.remove(SQLITE_PATH)
os.environ["DATABASE_URL"] = f"sqlite:///{SQLITE_PATH}"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

import django  # noqa: E402
django.setup()

from django.core.management import call_command  # noqa: E402
from django.core.management.base import CommandError  # noqa: E402
from specs.models import FlowAssertion, FormDiagnostic, FormFact, FormLine, FormRule, TaxForm  # noqa: E402
from sources.models import AuthorityTopic, RuleAuthorityLink  # noqa: E402
from specs.management.commands import load_2553 as L  # noqa: E402

FAILURES: list[str] = []
PASSES: list[str] = []


def check(cond, ok, bad):
    (PASSES if cond else FAILURES).append(ok if cond else bad)


call_command("migrate", run_syncdb=True, verbosity=0)

# -- Gate-1 guard: the file ships READY_TO_SEED=False and the loader refuses --
check(L.READY_TO_SEED is False, "READY_TO_SEED ships False (Gate-1 pending)", "READY_TO_SEED is not False in the file")
try:
    call_command("load_2553", verbosity=0)
    FAILURES.append("guard FAILED to refuse while READY_TO_SEED=False")
except CommandError:
    PASSES.append("guard refuses to seed while READY_TO_SEED=False")

L.READY_TO_SEED = True  # in-memory flip for the throwaway-SQLite run only
try:
    call_command("load_2553", verbosity=0)
    PASSES.append("load_2553 ran + seeded into SQLite without error")
except Exception as e:  # noqa: BLE001
    FAILURES.append(f"load_2553 raised: {e!r}")
    print("\n".join(FAILURES))
    sys.exit(1)

# twice-run idempotency
try:
    call_command("load_2553", verbosity=0)
    PASSES.append("second run idempotent (update_or_create everywhere)")
except Exception as e:  # noqa: BLE001
    FAILURES.append(f"second run raised: {e!r}")

form = TaxForm.objects.get(form_number="2553")

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
for fa in FlowAssertion.objects.filter(assertion_id__startswith="FA-2553"):
    CAPS[f"assertion_id={fa.assertion_id}"] = (fa.assertion_id, 20)
for t in AuthorityTopic.objects.all():
    CAPS[f"topic={t.topic_code}"] = (t.topic_name, 255)
viol = [f"{k}: len {len(v)} > {cap}" for k, (v, cap) in CAPS.items() if len(v) > cap]
check(not viol, f"CharField caps OK ({len(CAPS)} checked)", "CAP VIOLATIONS:\n    " + "\n    ".join(viol))

# -- counts --
check(FormFact.objects.filter(tax_form=form).count() == len(L.F2553_FACTS), f"facts {len(L.F2553_FACTS)}", "fact count mismatch")
check(FormRule.objects.filter(tax_form=form).count() == len(L.F2553_RULES), f"rules {len(L.F2553_RULES)}", "rule count mismatch")
check(FormLine.objects.filter(tax_form=form).count() == len(L.F2553_LINES), f"lines {len(L.F2553_LINES)}", "line count mismatch")
check(FormDiagnostic.objects.filter(tax_form=form).count() == len(L.F2553_DIAGNOSTICS), f"diagnostics {len(L.F2553_DIAGNOSTICS)}", "diag count mismatch")
check(form.entity_types == ["1120S"], "entity_types == ['1120S']", f"entity_types wrong: {form.entity_types}")

# -- authority links (IRC_1361/1362 absent on SQLite -> their secondary links skip; every rule still needs >=1 via the new sources) --
ruleless = [r.rule_id for r in FormRule.objects.filter(tax_form=form)
            if not RuleAuthorityLink.objects.filter(form_rule=r).exists()]
check(not ruleless, f"all {FormRule.objects.filter(tax_form=form).count()} rules have >= 1 authority link (even without IRC_1361/1362)", f"ruleless: {ruleless}")
defined = {r["rule_id"] for r in L.F2553_RULES}
linked = {rl[0] for rl in L.F2553_RULE_LINKS}
check(not (linked - defined), "rule_links reference defined rules", f"orphan: {linked - defined}")
check(not (defined - linked), "every rule appears in rule_links", f"unlinked: {defined - linked}")

# -- FAs staged DRAFT (the new-FAs-default-ACTIVE trap) --
fas = list(FlowAssertion.objects.filter(assertion_id__startswith="FA-2553"))
check(len(fas) == 3, "3 FA-2553 assertions", f"FA count {len(fas)}")
notdraft = [fa.assertion_id for fa in fas if fa.status != "draft"]
check(not notdraft, "all FA-2553 staged DRAFT", f"NOT draft: {notdraft}")

# -- deadline oracles: the three published i2553 examples --
check(L._election_deadline(date(2026, 1, 7)) == date(2026, 3, 21), "Example 1: Jan 7 -> Mar 21", f"Ex1 wrong: {L._election_deadline(date(2026, 1, 7))}")
check(L._election_deadline(date(2026, 1, 1)) == date(2026, 3, 15), "Example 2: Jan 1 -> Mar 15 (non-leap)", f"Ex2 wrong: {L._election_deadline(date(2026, 1, 1))}")
check(L._election_deadline(date(2025, 11, 8)) == date(2026, 1, 22), "Example 3: Nov 8 -> Jan 22", f"Ex3 wrong: {L._election_deadline(date(2025, 11, 8))}")
# leap year: 2-month period ends Feb 29, 2028 (i2553: 'February 28 (29 in leap years)') -> +15 = Mar 15
check(L._election_deadline(date(2028, 1, 1)) == date(2028, 3, 15), "leap year: Jan 1, 2028 -> Mar 15 (Feb 29 + 15)", f"leap wrong: {L._election_deadline(date(2028, 1, 1))}")
# no corresponding day: Dec 31 -> no Feb 31 -> last day of Feb + 15 = Mar 15
check(L._election_deadline(date(2025, 12, 31)) == date(2026, 3, 15), "no-corresponding-day: Dec 31 -> Mar 15", f"nocorr wrong: {L._election_deadline(date(2025, 12, 31))}")
# Dec 31 in a year before a leap Feb: Dec 31, 2027 -> Feb 29, 2028 + 15 = Mar 15, 2028
check(L._election_deadline(date(2027, 12, 31)) == date(2028, 3, 15), "no-corresponding-day into leap Feb: Dec 31, 2027 -> Mar 15, 2028", f"nocorr-leap wrong: {L._election_deadline(date(2027, 12, 31))}")

# -- timeliness oracles --
check(L._filing_timeliness(date(2026, 1, 7), date(2026, 3, 21), False) == "timely", "filed on the deadline -> timely", "on-deadline wrong")
check(L._filing_timeliness(date(2026, 1, 7), date(2026, 3, 22), False) == "late", "filed the day after -> late", "day-after wrong")
check(L._filing_timeliness(date(2026, 1, 7), date(2026, 1, 2), False) == "invalid_early", "pre-first-day, no prior year -> invalid_early", "invalid-early wrong")
check(L._filing_timeliness(date(2026, 1, 1), date(2025, 6, 15), True) == "timely", "preceding-year filing with a prior year -> timely", "preceding-year wrong")
check(L._filing_timeliness(date(2026, 1, 1), date(2024, 6, 1), True) == "invalid_early", "filed before the preceding year -> invalid_early", "pre-preceding wrong")

# -- shareholder count oracles --
check(L._shareholder_count_result(105, 98) == (True, True), "105 raw / 98 agg -> passes + item G", "famagg wrong")
check(L._shareholder_count_result(110, 103) == (False, False), "110/103 -> fails, no item G", "over-100 wrong")
check(L._shareholder_count_result(90, 90) == (True, False), "90/90 -> passes, no item G", "plain-pass wrong")
check(L._shareholder_count_result(100, 100) == (True, False), "exactly 100 -> passes", "boundary-100 wrong")
check(L._shareholder_count_result(101, 101) == (False, False), "101/101 -> fails", "boundary-101 wrong")

# -- late-relief path oracles --
check(L._late_relief_path(False, True, True, True) == "rp2013_30_corp", "corp within 3y75d + cause + consistent -> corp path", "corp path wrong")
check(L._late_relief_path(True, True, True, True) == "rp2013_30_entity", "entity within 3y75d -> entity path (Part IV)", "entity path wrong")
check(L._late_relief_path(False, False, True, True, True, True) == "rp2013_30_alt", "corp beyond 3y75d + 6a-c -> alternative", "alt path wrong")
check(L._late_relief_path(False, False, True, True, False, True) == "plr_1362b5", "corp beyond 3y75d without 6b -> PLR", "alt-miss wrong")
check(L._late_relief_path(True, False, True, True, True, True) == "plr_1362b5", "entity beyond 3y75d -> PLR (no 6a-c for entities)", "entity-beyond wrong")
check(L._late_relief_path(False, True, False, True) == "plr_1362b5", "no reasonable cause -> PLR", "no-cause wrong")
check(L._late_relief_path(False, True, True, False) == "plr_1362b5", "inconsistent reporting -> PLR", "inconsistent wrong")

# -- consent scope + Part II routing --
check(L._required_consent_scope(True) == "owners_on_election_day", "filed before item E -> election-day owners", "scope-before wrong")
check(L._required_consent_scope(False) == "all_owners_eff_to_file", "filed on/after item E -> all owners in the window", "scope-after wrong")
check(L._part_ii_required("fiscal") is True and L._part_ii_required("5253_other") is True, "F(2)/(4) -> Part II required", "part2-yes wrong")
check(L._part_ii_required("calendar") is False and L._part_ii_required("5253_dec") is False, "F(1)/(3) -> no Part II", "part2-no wrong")

# -- verified constants --
check(L.Q1_USER_FEE == 5750, "Q1 fee $5,750 (Rev. Proc. 2026-1 App. A (A)(3)(a)(ii))", "Q1 fee wrong")
check(L.PLR_1362B5_FEE == 14500, "PLR fee $14,500 ((A)(3)(c)(i))", "PLR fee wrong")
check(L.MAX_SHAREHOLDERS == 100 and L.LATE_RELIEF_YEARS == 3 and L.LATE_RELIEF_DAYS == 75, "100 shareholders / 3yr75d", "constants wrong")
check(L.MARGIN_LEGEND == "FILED PURSUANT TO REV. PROC. 2013-30", "margin legend verbatim", "legend wrong")

# -- scenario expected_outputs recomputed from the helpers --
for s in L.F2553_SCENARIOS:
    name, inp, exp = s["scenario_name"], s["inputs"], s["expected_outputs"]
    if "election_deadline" in exp:
        eff = date.fromisoformat(inp["election_effective_date"])
        got = L._election_deadline(eff).isoformat()
        check(got == exp["election_deadline"], f"scenario deadline OK: {name[:60]}", f"scenario deadline WRONG ({name[:60]}): {got} != {exp['election_deadline']}")
    if "timeliness" in exp:
        eff = date.fromisoformat(inp["election_effective_date"])
        got = L._filing_timeliness(eff, date.fromisoformat(inp["filing_date"]), inp.get("has_prior_tax_year", False))
        check(got == exp["timeliness"], f"scenario timeliness OK: {name[:60]}", f"scenario timeliness WRONG ({name[:60]}): {got} != {exp['timeliness']}")
    if "count_passes" in exp:
        got = L._shareholder_count_result(inp["num_shareholders_raw"], inp["num_shareholders_agg"])
        check(got[0] == exp["count_passes"], f"scenario count OK: {name[:60]}", f"scenario count WRONG ({name[:60]})")
        if "needs_item_g" in exp:
            check(got[1] == exp["needs_item_g"], f"scenario item-G OK: {name[:60]}", f"scenario item-G WRONG ({name[:60]})")
    if "late_relief_path" in exp:
        if "within_3y75d" in inp:
            within = inp["within_3y75d"]
        else:
            eff = date.fromisoformat(inp["election_effective_date"])
            filed = date.fromisoformat(inp["filing_date"])
            within = filed <= eff.replace(year=eff.year + L.LATE_RELIEF_YEARS) and (filed - eff).days <= L.LATE_RELIEF_YEARS * 365 + L.LATE_RELIEF_DAYS + 1
        got = L._late_relief_path(inp.get("is_eligible_entity_filer", False), within, inp.get("reasonable_cause", False),
                                  inp.get("consistent_reporting", False), inp.get("six_months_elapsed", False),
                                  inp.get("no_irs_notice_6mo", False))
        check(got == exp["late_relief_path"], f"scenario relief path OK: {name[:60]}", f"scenario relief WRONG ({name[:60]}): {got} != {exp['late_relief_path']}")
    if "part_ii_required" in exp:
        got = L._part_ii_required(inp["tax_year_type"])
        check(got == exp["part_ii_required"], f"scenario Part II OK: {name[:60]}", f"scenario Part II WRONG ({name[:60]})")

# -- key diagnostics present with the right severities --
SEV = {"D_2553_INELSH": "error", "D_2553_NRA": "error", "D_2553_100SH": "error", "D_2553_FAMAGG": "info",
       "D_2553_INELCORP": "error", "D_2553_EARLY": "error", "D_2553_LATE": "warning", "D_2553_PLR": "warning",
       "D_2553_SIGN": "error", "D_2553_CONSENT": "error", "D_2553_CPSPOUSE": "warning", "D_2553_PART2": "error",
       "D_2553_P1_47MO": "error", "D_2553_Q1FEE": "warning", "D_2553_QSST": "warning", "D_2553_REELECT": "warning",
       "D_2553_NO8832": "info", "D_2553_FOLLOWUP": "info", "D_2553_CLASS1": "info"}
for did, sev in SEV.items():
    d = FormDiagnostic.objects.filter(tax_form=form, diagnostic_id=did).first()
    check(d is not None and d.severity == sev, f"{did} present ({sev})", f"{did} missing or severity != {sev}")

# -- the year-keyed fee stays flagged in the Q1FEE message --
q1 = FormDiagnostic.objects.get(tax_form=form, diagnostic_id="D_2553_Q1FEE")
check("5,750" in q1.message and "6,200" in q1.message, "Q1FEE message carries $5,750 + the superseded $6,200 note", "Q1FEE message missing the fee correction")

print(f"\n{'=' * 64}\nPASS {len(PASSES)} / FAIL {len(FAILURES)}\n{'=' * 64}")
for p in PASSES:
    print(f"  ok  {p}")
if FAILURES:
    print("\nFAILURES:")
    for f in FAILURES:
        print(f"  XX  {f}")
    sys.exit(1)
print("\nALL GREEN — the 2553 draft validates; Gate-1 (Ken) still gates seeding.")
