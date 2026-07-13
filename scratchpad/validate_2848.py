"""Throwaway-SQLite validation for the Form 2848 loader (WO-27, SPINE S-20c).

Checks: the Gate-1 guard refuses while READY_TO_SEED=False; twice-run idempotency; CharField caps;
rule-link coverage; logic oracles (future-period clock, 45/60-day signature window, URP gate, rep/notice
counts, 'modified'-CAF, filing route); scenario expected_outputs recomputed from the helpers; FAs staged
DRAFT; entity_types; the Rec-Dev-08-Jul-2026 language pinned in the MODCAF/L4CAF diagnostics.
ASCII-only. Run: poetry run python scratchpad/validate_2848.py
"""
import os
import sys

PROJECT_ROOT = r"D:\dev\sherpa-tax-rule-studio"
sys.path.insert(0, PROJECT_ROOT)

SQLITE_PATH = os.path.join(PROJECT_ROOT, "scratchpad", "validate_2848.sqlite3")
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
from specs.management.commands import load_2848 as L  # noqa: E402

FAILURES: list[str] = []
PASSES: list[str] = []


def check(cond, ok, bad):
    (PASSES if cond else FAILURES).append(ok if cond else bad)


call_command("migrate", run_syncdb=True, verbosity=0)

# -- Gate-1 state: Ken APPROVED 2026-07-12 (s68 live walk) — the sentinel ships True; prove the
# guard still exists by flipping it off in-memory and expecting the refusal.
check(L.READY_TO_SEED is True, "READY_TO_SEED ships True (Gate-1 APPROVED 2026-07-12)", "READY_TO_SEED is not True post-approval")
L.READY_TO_SEED = False
try:
    call_command("load_2848", verbosity=0)
    FAILURES.append("guard FAILED to refuse while READY_TO_SEED=False")
except CommandError:
    PASSES.append("guard still refuses when the sentinel is off (mechanism intact)")
L.READY_TO_SEED = True
try:
    call_command("load_2848", verbosity=0)
    PASSES.append("load_2848 ran + seeded into SQLite without error")
except Exception as e:  # noqa: BLE001
    FAILURES.append(f"load_2848 raised: {e!r}")
    print("\n".join(FAILURES))
    sys.exit(1)

try:
    call_command("load_2848", verbosity=0)
    PASSES.append("second run idempotent (update_or_create everywhere)")
except Exception as e:  # noqa: BLE001
    FAILURES.append(f"second run raised: {e!r}")

form = TaxForm.objects.get(form_number="2848")

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
for fa in FlowAssertion.objects.filter(assertion_id__startswith="FA-2848"):
    CAPS[f"assertion_id={fa.assertion_id}"] = (fa.assertion_id, 20)
for t in AuthorityTopic.objects.all():
    CAPS[f"topic={t.topic_code}"] = (t.topic_name, 255)
viol = [f"{k}: len {len(v)} > {cap}" for k, (v, cap) in CAPS.items() if len(v) > cap]
check(not viol, f"CharField caps OK ({len(CAPS)} checked)", "CAP VIOLATIONS:\n    " + "\n    ".join(viol))

# -- counts + identity --
check(FormFact.objects.filter(tax_form=form).count() == len(L.F2848_FACTS), f"facts {len(L.F2848_FACTS)}", "fact count mismatch")
check(FormRule.objects.filter(tax_form=form).count() == len(L.F2848_RULES), f"rules {len(L.F2848_RULES)}", "rule count mismatch")
check(FormLine.objects.filter(tax_form=form).count() == len(L.F2848_LINES), f"lines {len(L.F2848_LINES)}", "line count mismatch")
check(FormDiagnostic.objects.filter(tax_form=form).count() == len(L.F2848_DIAGNOSTICS), f"diagnostics {len(L.F2848_DIAGNOSTICS)}", "diag count mismatch")
check(form.entity_types == ["1040", "1120S", "1065", "1120", "1041", "709"], "entity_types = all six suite types", f"entity_types wrong: {form.entity_types}")

# -- authority links --
ruleless = [r.rule_id for r in FormRule.objects.filter(tax_form=form)
            if not RuleAuthorityLink.objects.filter(form_rule=r).exists()]
check(not ruleless, f"all {FormRule.objects.filter(tax_form=form).count()} rules have >= 1 authority link", f"ruleless: {ruleless}")
defined = {r["rule_id"] for r in L.F2848_RULES}
linked = {rl[0] for rl in L.F2848_RULE_LINKS}
check(not (linked - defined), "rule_links reference defined rules", f"orphan: {linked - defined}")
check(not (defined - linked), "every rule appears in rule_links", f"unlinked: {defined - linked}")

# -- FAs staged DRAFT --
fas = list(FlowAssertion.objects.filter(assertion_id__startswith="FA-2848"))
check(len(fas) == 3, "3 FA-2848 assertions", f"FA count {len(fas)}")
notactive = [fa.assertion_id for fa in fas if fa.status != "active"]
check(not notactive, "all FA-2848 ACTIVE (s69 print unit; runners live in tts)", f"NOT active: {notactive}")

# -- future-period clock oracles --
check(L._future_period_recordable(2026, 2029) is True, "received 2026 -> 2029 recordable (Dec 31 + 3)", "future 2029 wrong")
check(L._future_period_recordable(2026, 2030) is False, "received 2026 -> 2030 NOT recordable", "future 2030 wrong")
check(L._future_period_recordable(2026, 2026) is True, "current year always recordable", "current-year wrong")

# -- signature window oracles --
check(L._rep_sign_deadline_days(False) == 45 and L._rep_sign_deadline_days(True) == 60, "window = 45 domestic / 60 abroad", "deadline days wrong")
check(L._rep_signature_timely(10, False) is True, "day 10 domestic -> timely", "day-10 wrong")
check(L._rep_signature_timely(45, False) is True, "day 45 domestic (boundary) -> timely", "day-45 wrong")
check(L._rep_signature_timely(46, False) is False, "day 46 domestic -> late", "day-46 wrong")
check(L._rep_signature_timely(50, False) is False, "day 50 domestic -> late", "day-50-dom wrong")
check(L._rep_signature_timely(50, True) is True, "day 50 abroad -> timely (60-day window)", "day-50-abroad wrong")
check(L._rep_signature_timely(61, True) is False, "day 61 abroad -> late", "day-61 wrong")
check(L._rep_signature_timely(400, False, rep_signed_first=True) is True, "rep-signed-first -> no time limit", "rep-first wrong")

# -- URP gate oracles --
check(L._urp_can_represent(True, True, True, True) is True, "URP all four -> can represent (limited)", "urp-all wrong")
check(L._urp_can_represent(True, True, True, False) is False, "URP missing rep-year AFSP -> cannot", "urp-repyear wrong")
check(L._urp_can_represent(True, False, True, True) is False, "URP didn't prepare+sign -> cannot", "urp-prep wrong")
check(L._urp_can_represent(False, True, True, True) is False, "URP no PTIN -> cannot", "urp-ptin wrong")

# -- rep/notice count oracles --
check(L._rep_count_ok(4, False) is True and L._rep_count_ok(5, False) is False and L._rep_count_ok(6, True) is True,
      "rep count: 4 ok / 5 needs attachment / 6+attached ok", "rep-count wrong")
check(L._notice_copy_ok(2) is True and L._notice_copy_ok(3) is False, "notice copies: 2 ok / 3 fails", "notice-copy wrong")

# -- modified-CAF + filing-route oracles --
check(L._modified_caf(False, False) is False, "clean 5a/5b -> not modified", "modcaf-clean wrong")
check(L._modified_caf(True, False) is True and L._modified_caf(False, True) is True, "5a-other or any-5b -> modified", "modcaf wrong")
check(L._filing_route(True, False) == "office_handling_matter", "line 4 -> office handling the matter", "route-l4 wrong")
check(L._filing_route(False, True) == "online_only", "e-signature -> online only", "route-esign wrong")
check(L._filing_route(False, False) == "online_fax_or_mail", "handwritten -> online/fax/mail", "route-hand wrong")

# -- verified constants --
check(L.MAX_REPS_ON_FORM == 4 and L.MAX_NOTICE_COPY_REPS == 2, "4 rep blocks / 2 notice copies", "rep constants wrong")
check(L.FUTURE_PERIOD_YEARS == 3 and L.REP_SIGN_DAYS_DOMESTIC == 45 and L.REP_SIGN_DAYS_ABROAD == 60, "3yr clock / 45 / 60", "window constants wrong")
check(L.STUDENT_CAF_PURGE_DAYS == 130, "student CAF purge = 130 days", "purge constant wrong")
check("855-214-7519" in L.FILING_ADDRESSES["memphis"] and "855-214-7522" in L.FILING_ADDRESSES["ogden"]
      and "855-772-3156" in L.FILING_ADDRESSES["international"], "chart fax numbers verbatim", "fax numbers wrong")

# -- scenario expected_outputs recomputed from the helpers --
for s in L.F2848_SCENARIOS:
    name, inp, exp = s["scenario_name"], s["inputs"], s["expected_outputs"]
    if "rep_signature_timely" in exp:
        got = L._rep_signature_timely(inp.get("days_rep_after_taxpayer", 0), inp.get("taxpayer_abroad", False),
                                      inp.get("rep_signed_first", False))
        check(got == exp["rep_signature_timely"], f"scenario sign-window OK: {name[:58]}", f"scenario sign-window WRONG ({name[:58]})")
    if "future_recordable" in exp:
        got = L._future_period_recordable(inp["receipt_year"], inp["latest_future_period_year"])
        check(got == exp["future_recordable"], f"scenario future-clock OK: {name[:58]}", f"scenario future-clock WRONG ({name[:58]})")
    if "modified_caf" in exp:
        got = L._modified_caf(inp.get("l5a_other_acts", False), inp.get("l5b_any_limits", False))
        check(got == exp["modified_caf"], f"scenario modcaf OK: {name[:58]}", f"scenario modcaf WRONG ({name[:58]})")
    if "urp_can_represent" in exp:
        got = L._urp_can_represent(inp.get("urp_has_ptin", False), inp.get("urp_prepared_signed", False),
                                   inp.get("urp_afsp_prep_year", False), inp.get("urp_afsp_rep_year", False))
        check(got == exp["urp_can_represent"], f"scenario URP OK: {name[:58]}", f"scenario URP WRONG ({name[:58]})")
    if "filing_route" in exp:
        got = L._filing_route(inp.get("line4_specific_use", False), inp.get("has_electronic_signature", False))
        check(got == exp["filing_route"], f"scenario route OK: {name[:58]}", f"scenario route WRONG ({name[:58]}): {got}")
    if "line3_valid" in exp:
        got = not inp.get("has_general_reference", False)
        check(got == exp["line3_valid"], f"scenario line-3 OK: {name[:58]}", f"scenario line-3 WRONG ({name[:58]})")
    if "retention_valid" in exp:
        got = not (inp.get("line6_retain_prior", False) and not inp.get("prior_poa_attached", False))
        check(got == exp["retention_valid"], f"scenario retention OK: {name[:58]}", f"scenario retention WRONG ({name[:58]})")

# -- key diagnostics present with the right severities --
SEV = {"D_2848_GENREF": "error", "D_2848_L3REQ": "error", "D_2848_FUTURE3": "warning", "D_2848_REP5": "error",
       "D_2848_NOTICE2": "error", "D_2848_SIGN45": "error", "D_2848_ESIGN": "error", "D_2848_UNSIGNED": "error",
       "D_2848_URP": "warning", "D_2848_SIGNRET": "warning", "D_2848_MODCAF": "warning", "D_2848_L4CAF": "warning",
       "D_2848_RETAIN": "error", "D_2848_REVOKEALL": "info", "D_2848_JOINT": "warning", "D_2848_ADDRESS": "info",
       "D_2848_STUDENT": "info"}
for did, sev in SEV.items():
    d = FormDiagnostic.objects.filter(tax_form=form, diagnostic_id=did).first()
    check(d is not None and d.severity == sev, f"{did} present ({sev})", f"{did} missing or severity != {sev}")

# -- the 08-Jul-2026 Recent Development language pinned --
modcaf = FormDiagnostic.objects.get(tax_form=form, diagnostic_id="D_2848_MODCAF")
check("Transcript Delivery System" in modcaf.message and "Tax Pro Account" in modcaf.message and "08-Jul-2026" in modcaf.message,
      "MODCAF message carries TDS + Tax Pro Account + the 08-Jul-2026 date", "MODCAF message missing the Rec-Dev substance")
l4caf = FormDiagnostic.objects.get(tax_form=form, diagnostic_id="D_2848_L4CAF")
check("never check line 4" in l4caf.message, "L4CAF carries the 'never check line 4' caution verbatim", "L4CAF missing the caution")

print(f"\n{'=' * 64}\nPASS {len(PASSES)} / FAIL {len(FAILURES)}\n{'=' * 64}")
for p in PASSES:
    print(f"  ok  {p}")
if FAILURES:
    print("\nFAILURES:")
    for f in FAILURES:
        print(f"  XX  {f}")
    sys.exit(1)
print("\nALL GREEN — the 2848 draft validates; Gate-1 (Ken) still gates seeding.")
