"""Throwaway-SQLite validation for the 8879/8878 signature-authorization pair loader (WO-33, tts s90).

Checks: guard-refusal (sentinel ships False); in-memory flip seeds BOTH forms + twice-run idempotency;
CharField caps; rule-link coverage per form; logic oracles (ALL FOUR 8879 chart rows incl. the
counter-intuitive PP+own-PIN row; ALL FIVE 8878 chart rows incl. the no-EFW-beats-everything negative
and the 2350-never-Part-III pin; PIN hygiene; the $50/$14 re-sign tolerance at/over the boundary both
families; the self-select bars; the stockpiling clock; Part I incl. the 1040-SS line-4-only arm);
scenario outputs recomputed; FAs staged DRAFT; the flagged walk seams asserted PRESENT in the rule text
(the L3 25d recommendation, the R0000-098 mirror, the extract-refusal seam).
ASCII-only. Run: poetry run python scratchpad/validate_8879_8878.py
"""
import os
import sys

PROJECT_ROOT = r"D:\dev\sherpa-tax-rule-studio"
sys.path.insert(0, PROJECT_ROOT)

SQLITE_PATH = os.path.join(PROJECT_ROOT, "scratchpad", "validate_8879_8878.sqlite3")
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
from specs.management.commands import load_8879_8878 as L  # noqa: E402

FAILURES: list[str] = []
PASSES: list[str] = []


def check(cond, ok, bad):
    (PASSES if cond else FAILURES).append(ok if cond else bad)


call_command("migrate", run_syncdb=True, verbosity=0)

# -- Gate-1 guard: the sentinel SHIPS False and the loader refuses --
check(L.READY_TO_SEED is False, "READY_TO_SEED ships False (Gate-1 pending)", "READY_TO_SEED is not False in the shipped file")
try:
    call_command("load_8879_8878", verbosity=0)
    FAILURES.append("guard FAILED to refuse while READY_TO_SEED=False")
except CommandError:
    PASSES.append("guard refuses to seed while the sentinel is off")

L.READY_TO_SEED = True
try:
    call_command("load_8879_8878", verbosity=0)
    PASSES.append("load_8879_8878 ran + seeded into SQLite without error (in-memory flip)")
except Exception as e:  # noqa: BLE001
    FAILURES.append(f"load_8879_8878 raised: {e!r}")
    print("\n".join(FAILURES))
    sys.exit(1)

try:
    call_command("load_8879_8878", verbosity=0)
    PASSES.append("second run idempotent (update_or_create everywhere)")
except Exception as e:  # noqa: BLE001
    FAILURES.append(f"second run raised: {e!r}")
finally:
    L.READY_TO_SEED = False  # leave the module as shipped

form_79 = TaxForm.objects.get(form_number="8879")
form_78 = TaxForm.objects.get(form_number="8878")

# -- CharField caps (both forms) --
CAPS: dict = {"79_title(255)": (form_79.form_title, 255), "78_title(255)": (form_78.form_title, 255)}
for form in (form_79, form_78):
    for r in FormRule.objects.filter(tax_form=form):
        CAPS[f"rule_id={r.rule_id}"] = (r.rule_id, 20)
        CAPS[f"rule_title={r.rule_id}"] = (r.title, 255)
    for d in FormDiagnostic.objects.filter(tax_form=form):
        CAPS[f"diagnostic_id={d.diagnostic_id}"] = (d.diagnostic_id, 20)
        CAPS[f"diag_title={d.diagnostic_id}"] = (d.title, 255)
    for ln in FormLine.objects.filter(tax_form=form):
        CAPS[f"line_number={form.form_number}.{ln.line_number}"] = (ln.line_number, 20)
    for fct in FormFact.objects.filter(tax_form=form):
        CAPS[f"fact_key={form.form_number}.{fct.fact_key}"] = (fct.fact_key, 100)
        CAPS[f"fact_label={form.form_number}.{fct.fact_key}"] = (fct.label, 255)
for fa in FlowAssertion.objects.filter(assertion_id__in=["FA-8879-NEED", "FA-8879-RESIGN", "FA-8878-EFW"]):
    CAPS[f"assertion_id={fa.assertion_id}"] = (fa.assertion_id, 20)
for t in AuthorityTopic.objects.all():
    CAPS[f"topic={t.topic_code}"] = (t.topic_name, 255)
viol = [f"{k}: len {len(v)} > {cap}" for k, (v, cap) in CAPS.items() if len(v) > cap]
check(not viol, f"CharField caps OK ({len(CAPS)} checked)", "CAP VIOLATIONS:\n    " + "\n    ".join(viol))

# -- counts + identity --
check(FormFact.objects.filter(tax_form=form_79).count() == len(L.F79_FACTS), f"8879 facts {len(L.F79_FACTS)}", "8879 fact count mismatch")
check(FormRule.objects.filter(tax_form=form_79).count() == len(L.F79_RULES), f"8879 rules {len(L.F79_RULES)}", "8879 rule count mismatch")
check(FormDiagnostic.objects.filter(tax_form=form_79).count() == len(L.F79_DIAGNOSTICS), f"8879 diagnostics {len(L.F79_DIAGNOSTICS)}", "8879 diag count mismatch")
check(TestScenario.objects.filter(tax_form=form_79).count() == len(L.F79_SCENARIOS), f"8879 scenarios {len(L.F79_SCENARIOS)}", "8879 scenario count mismatch")
check(FormLine.objects.filter(tax_form=form_79).count() == len(L.F79_LINES), f"8879 lines {len(L.F79_LINES)}", "8879 line count mismatch")
check(FormFact.objects.filter(tax_form=form_78).count() == len(L.F78_FACTS), f"8878 facts {len(L.F78_FACTS)}", "8878 fact count mismatch")
check(FormRule.objects.filter(tax_form=form_78).count() == len(L.F78_RULES), f"8878 rules {len(L.F78_RULES)}", "8878 rule count mismatch")
check(FormDiagnostic.objects.filter(tax_form=form_78).count() == len(L.F78_DIAGNOSTICS), f"8878 diagnostics {len(L.F78_DIAGNOSTICS)}", "8878 diag count mismatch")
check(TestScenario.objects.filter(tax_form=form_78).count() == len(L.F78_SCENARIOS), f"8878 scenarios {len(L.F78_SCENARIOS)}", "8878 scenario count mismatch")
check(FormLine.objects.filter(tax_form=form_78).count() == len(L.F78_LINES), f"8878 lines {len(L.F78_LINES)}", "8878 line count mismatch")
check(form_79.entity_types == ["1040"] and form_78.entity_types == ["1040"], "entity_types ['1040'] both", "entity_types wrong")
check(form_79.status == "draft" and form_78.status == "draft", "both TaxForms status=draft", "TaxForm status not draft")

# -- authority links (both forms) --
for form, rules, links, tag in ((form_79, L.F79_RULES, L.F79_RULE_LINKS, "8879"), (form_78, L.F78_RULES, L.F78_RULE_LINKS, "8878")):
    ruleless = [r.rule_id for r in FormRule.objects.filter(tax_form=form)
                if not RuleAuthorityLink.objects.filter(form_rule=r).exists()]
    check(not ruleless, f"{tag}: all rules have >= 1 authority link", f"{tag} ruleless: {ruleless}")
    defined = {r["rule_id"] for r in rules}
    linked = {rl[0] for rl in links}
    check(not (linked - defined) and not (defined - linked), f"{tag}: rule_links bidirectionally complete", f"{tag} link drift: {linked ^ defined}")

# -- FAs staged DRAFT --
fas = list(FlowAssertion.objects.filter(assertion_id__in=["FA-8879-NEED", "FA-8879-RESIGN", "FA-8878-EFW"]))
check(len(fas) == 3, "3 pair assertions", f"FA count {len(fas)}")
notdraft = [fa.assertion_id for fa in fas if fa.status != "draft"]
check(not notdraft, "all pair FAs staged DRAFT (the new-FAs-default-ACTIVE trap)", f"NOT draft: {notdraft}")

# ============================================================
# Logic oracles
# ============================================================

# -- PIN hygiene --
check(L._pin_valid("12345") is True, "PIN 12345 valid", "PIN 12345 rejected")
check(L._pin_valid("00000") is False, "all-zero PIN rejected (face verbatim)", "all-zero PIN accepted")
check(L._pin_valid("1234") is False and L._pin_valid("123456") is False, "4/6-digit PINs rejected", "wrong-length PIN accepted")
check(L._pin_valid("1234a") is False and L._pin_valid(None) is False, "non-digit/None PIN rejected", "junk PIN accepted")
check(L._ero_efin_pin_valid("612345", "98765") is True, "EFIN(6)+PIN(5) valid (Part III, 11 digits)", "valid EFIN/PIN rejected")
check(L._ero_efin_pin_valid("61234", "98765") is False, "5-digit EFIN rejected", "short EFIN accepted")
check(L._ero_efin_pin_valid("612345", "00000") is False, "ERO all-zero PIN rejected ('don't enter all zeros')", "ERO zero PIN accepted")

# -- the 8879 chart, ALL FOUR rows --
check(L._f8879_needed("self_select_practitioner", False) is False, "row 1: self-select + own PIN -> NO 8879 (the only skip)", "row 1 wrong")
check(L._f8879_needed("self_select_practitioner", True) is True and L._f8879_parts("self_select_practitioner", True) == ("I", "II"),
      "row 2: self-select + ERO enters -> Parts I, II (no Part III)", "row 2 wrong")
check(L._f8879_needed("practitioner", True) is True and L._f8879_parts("practitioner", True) == ("I", "II", "III"),
      "row 3: PP + ERO enters -> Parts I, II, III", "row 3 wrong")
check(L._f8879_needed("practitioner", False) is True and L._f8879_parts("practitioner", False) == ("I", "II", "III"),
      "row 4: PP + taxpayer keys OWN PIN -> STILL Parts I, II, III (Pub 1345 always-sign)", "row 4 wrong - the counter-intuitive row")
check(L._f8879_parts("self_select_practitioner", False) == (), "skip row emits no parts", "skip row emitted parts")

# -- the 8878 chart, ALL FIVE rows --
check(L._f8878_needed("4868", True, "self_select_practitioner", False) is False, "row 1: 4868+EFW+own-PIN+non-PP -> no 8878", "8878 row 1 wrong")
check(L._f8878_needed("4868", False, "practitioner", True) is False,
      "row 2: NO EFW beats everything - even PP + ERO-entered (the s88 R0000-098 mirror)", "8878 row 2 wrong - the load-bearing negative")
check(L._f8878_needed("4868", True, "self_select_practitioner", True) is True and L._f8878_parts("4868", True, "self_select_practitioner", True) == ("I", "II"),
      "row 3: 4868+EFW+ERO-entered+non-PP -> Parts I, II", "8878 row 3 wrong")
check(L._f8878_needed("2350", False, "self_select_practitioner", True) is True and L._f8878_parts("2350", False, "self_select_practitioner", True) == ("I", "II"),
      "row 4: 2350 + ERO enters -> Parts I, II (EFW irrelevant to the 2350 arm)", "8878 row 4 wrong")
check(L._f8878_needed("4868", True, "practitioner", False) is True and L._f8878_parts("4868", True, "practitioner", False) == ("I", "II", "III"),
      "row 5: 4868+EFW+PP -> Parts I, II, III (who enters is irrelevant on the PP row)", "8878 row 5 wrong")
check(L._f8878_parts("2350", True, "practitioner", True) == ("I", "II"),
      "2350 NEVER reaches Part III even under the PP method ('Form 4868 Only')", "2350 reached Part III")
check(L._f8878_needed("2350", False, "practitioner", False) is False,
      "2350 + taxpayer keys own -> no 8878 (PP alone never creates a 2350 need)", "2350 PP-alone wrong")

# -- the $50/$14 re-sign tolerance (Pub 1345 'differ by MORE than') --
check(L._resign_required(50, 0) is False and L._resign_required(0, 14) is False,
      "AT the tolerance exactly ($50 AGI / $14 tax) -> no re-sign", "boundary re-sign wrong")
check(L._resign_required(51, 0) is True, "$51 AGI delta -> re-sign", "$51 AGI missed")
check(L._resign_required(0, 15) is True, "$15 tax-family delta -> re-sign", "$15 tax missed")
check(L._resign_required(-51, 0) is True and L._resign_required(0, -15) is True,
      "negative deltas count (abs)", "negative delta missed")
check(L._resign_required(40, 10) is False, "$40/$10 inside both tolerances -> no re-sign", "inside-tolerance re-sign wrong")

# -- self-select bars + stockpiling --
check(L._self_select_barred(True, False, False) is True and L._self_select_barred(False, True, False) is True
      and L._self_select_barred(False, False, True) is True, "each self-select bar trips alone (under-16 x2, dup-SSN)", "a bar failed to trip")
check(L._self_select_barred(False, False, False) is False, "no bar -> self-select open", "false-positive bar")
check(L._stockpiling(3) is False and L._stockpiling(4) is True, "stockpiling clock: 3 days OK, 4 days trips ('more than three')", "stockpiling boundary wrong")

# -- Part I amounts (incl. the 1040-SS arm) --
p1 = L._part1_amounts(88450, 9200, 11650, 2450, 0)
check(p1 == {"1": 88450, "2": 9200, "3": 11650, "4": 2450, "5": 0}, "Part I full mapping (8879-E pin)", f"Part I wrong: {p1}")
ss = L._part1_amounts(88450, 9200, 11650, 2450, 0, is_1040ss=True)
check(ss == {"4": 2450}, "1040-SS filers use LINE 4 ONLY (face note; app boundary)", f"1040-SS arm wrong: {ss}")

# -- scenario outputs recomputed from the seeded rows --
sc = {s.scenario_name.split(" - ")[0]: s for s in TestScenario.objects.filter(tax_form__in=[form_79, form_78])}
a = sc["8879-A"].inputs
check(L._f8879_needed(a["pin_method"], a["primary_pin_entered_by"] == "ero" or a["spouse_pin_entered_by"] == "ero") is True
      and list(L._f8879_parts(a["pin_method"], True)) == sc["8879-A"].expected_outputs["f8879_parts"],
      "8879-A recomputed (PP MFJ ERO-entered -> I/II/III)", "8879-A drifted")
b = sc["8879-B"].inputs
check(L._f8879_needed(b["pin_method"], b["primary_pin_entered_by"] == "ero") is sc["8879-B"].expected_outputs["f8879_needed"],
      "8879-B recomputed (the skip row)", "8879-B drifted")
d = sc["8879-D"].inputs
check(list(L._f8879_parts(d["pin_method"], d["primary_pin_entered_by"] == "ero")) == sc["8879-D"].expected_outputs["f8879_parts"],
      "8879-D recomputed (PP + own PIN still I/II/III)", "8879-D drifted")
e = sc["8879-E"].inputs
check(L._part1_amounts(e["signed_agi"], e["signed_total_tax"], e["signed_withholding"], e["signed_refund"], e["signed_owed"])
      == sc["8879-E"].expected_outputs["part1_amounts"], "8879-E recomputed (Part I amounts)", "8879-E drifted")
f = sc["8879-F"].inputs
check(L._resign_required(f["delta_agi_case1"], f["delta_tax_case1"]) is sc["8879-F"].expected_outputs["case1_resign"]
      and L._resign_required(f["delta_agi_case2"], 0) is sc["8879-F"].expected_outputs["case2_resign"]
      and L._resign_required(0, f["delta_tax_case3"]) is sc["8879-F"].expected_outputs["case3_resign"],
      "8879-F recomputed (tolerance three cases)", "8879-F drifted")
g = sc["8879-G"].inputs
check(L._pin_valid(g["primary_pin"]) is False, "8879-G recomputed (all-zero PIN)", "8879-G drifted")
h = sc["8879-H"].inputs
check(L._self_select_barred(h["primary_under16_never_filed"], False, False) is sc["8879-H"].expected_outputs["self_select_barred"],
      "8879-H recomputed (under-16 bar)", "8879-H drifted")
for name in ("8878-A", "8878-B", "8878-C", "8878-D", "8878-E"):
    i = sc[name].inputs
    got = L._f8878_needed(i["extension_form"], i.get("efw_elected", False), i["pin_method"], i.get("primary_pin_entered_by") == "ero")
    want = sc[name].expected_outputs["f8878_needed"]
    check(got is want, f"{name} recomputed (needed={want})", f"{name} drifted: got {got}")
    if want:
        parts = list(L._f8878_parts(i["extension_form"], i.get("efw_elected", False), i["pin_method"], i.get("primary_pin_entered_by") == "ero"))
        check(parts == sc[name].expected_outputs["f8878_parts"], f"{name} parts recomputed", f"{name} parts drifted: {parts}")

# -- the flagged walk seams asserted PRESENT in the seeded rule text --
r_amts = FormRule.objects.get(tax_form=form_79, rule_id="R-8879-AMTS")
check("25d" in r_amts.formula and "25a+25b" in r_amts.formula, "walk seam 1 (L3: 25d recommended, 25a+25b literal) present in R-8879-AMTS", "seam 1 text missing")
check("column-C" in r_amts.formula, "walk seam 2 (1040-X column-C arm) present in R-8879-AMTS", "seam 2 text missing")
r_need78 = FormRule.objects.get(tax_form=form_78, rule_id="R-8878-NEED")
check("R0000-098" in r_need78.formula, "the s88 R0000-098 mirror named in R-8878-NEED", "R0000-098 tie missing")
r_timing = FormRule.objects.get(tax_form=form_79, rule_id="R-8879-TIMING")
check("stockpiling" in r_timing.formula and "9325" in r_timing.formula, "sign-before-transmit + SID/9325 + stockpiling in R-8879-TIMING", "timing rule text missing")
d_unsigned = FormDiagnostic.objects.get(tax_form=form_79, diagnostic_id="D_8879_UNSIGNED")
check(d_unsigned.severity == "error", "D_8879_UNSIGNED is a BLOCKER (walk seam 3 extract-refusal)", "D_8879_UNSIGNED not error")
d_yw = FormDiagnostic.objects.get(tax_form=form_78, diagnostic_id="D_8878_YEARWATCH")
check("YEAR-DATED" in d_yw.message, "the 8878 year-watch diagnostic present", "year-watch missing")

# -- constants pinned --
check(L.RESIGN_TOL_INCOME == 50 and L.RESIGN_TOL_TAX == 14, "tolerance constants $50/$14 (Pub 1345)", "tolerance constants wrong")
check(L.STOCKPILE_DAYS == 3 and L.RETENTION_YEARS == 3, "stockpiling 3 days / retention 3 years", "clock constants wrong")
check(L.PIN_METHODS == ("practitioner", "self_select_practitioner"), "PIN_METHODS excludes Self-Select On-Line (self-filer path)", "PIN_METHODS wrong")

# -- ASCII-only guard on the loader source --
src = open(os.path.join(PROJECT_ROOT, "specs", "management", "commands", "load_8879_8878.py"), "rb").read()
try:
    src.decode("ascii")
    PASSES.append("loader source is pure ASCII")
except UnicodeDecodeError:
    FAILURES.append("loader source contains non-ASCII bytes")

print("\n" + "=" * 70)
for p in PASSES:
    print(f"  PASS  {p}")
for f_ in FAILURES:
    print(f"  FAIL  {f_}")
print("=" * 70)
print(f"\n{len(PASSES)} passed / {len(FAILURES)} failed")
sys.exit(1 if FAILURES else 0)
