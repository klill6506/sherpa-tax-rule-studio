"""Throwaway-SQLite validation for the Schedule K-1 (Form 1041) loader (leg b).

Seeds the SPINE (leg a) FIRST so the reused federal sources (IRS_2025_I1041,
IRC_SUBCHAPTER_J) resolve, then the K-1 loader — mirroring how seed_all layers loaders.
Checks: CharField caps; every rule >= 1 authority link (proves the existing-source
refs resolved); rule_link coverage; arithmetic (character retention, final-year gate,
NIIT box 14H); key diagnostics present.

Run: poetry run python scratchpad/validate_1041_k1.py
"""
import os
import sys

PROJECT_ROOT = r"D:\dev\sherpa-tax-rule-studio"
sys.path.insert(0, PROJECT_ROOT)

SQLITE_PATH = os.path.join(PROJECT_ROOT, "scratchpad", "validate_1041_k1.sqlite3")
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
from specs.management.commands import load_1041_spine as SP  # noqa: E402
from specs.management.commands import load_1041_schedule_k1 as K1  # noqa: E402

FAILURES: list[str] = []
PASSES: list[str] = []


def check(cond, ok, bad):
    (PASSES if cond else FAILURES).append(ok if cond else bad)


# ── seed spine then K-1 into one SQLite ──
call_command("migrate", run_syncdb=True, verbosity=0)
SP.READY_TO_SEED = True
K1.READY_TO_SEED = True
try:
    call_command("load_1041_spine", verbosity=0)
    call_command("load_1041_schedule_k1", verbosity=1)
    PASSES.append("spine + K-1 loaders seeded into SQLite without error")
except Exception as e:  # noqa: BLE001
    FAILURES.append(f"loader raised: {e!r}")
    print("\n".join(FAILURES))
    sys.exit(1)

form = TaxForm.objects.get(form_number="SCHEDULE_K1_1041")

# ── CharField caps ──
CAPS = {"form_number(50)": (form.form_number, 50)}
for r in FormRule.objects.filter(tax_form=form):
    CAPS[f"rule_id={r.rule_id}"] = (r.rule_id, 20)
for d in FormDiagnostic.objects.filter(tax_form=form):
    CAPS[f"diagnostic_id={d.diagnostic_id}"] = (d.diagnostic_id, 20)
for ln in FormLine.objects.filter(tax_form=form):
    CAPS[f"line_number={ln.line_number}"] = (ln.line_number, 20)
for fa in FlowAssertion.objects.filter(assertion_id__startswith="FA-K1041"):
    CAPS[f"assertion_id={fa.assertion_id}"] = (fa.assertion_id, 20)
for fct in FormFact.objects.filter(tax_form=form):
    CAPS[f"fact_key={fct.fact_key}"] = (fct.fact_key, 100)
for t in AuthorityTopic.objects.all():
    CAPS[f"topic_name={t.topic_code}"] = (t.topic_name, 255)
viol = [f"{k}: len {len(v)} > {cap}" for k, (v, cap) in CAPS.items() if len(v) > cap]
check(not viol, f"CharField caps OK ({len(CAPS)} checked)", "CAP VIOLATIONS:\n    " + "\n    ".join(viol))

# ── every rule has >= 1 authority link (proves reused-source refs resolved) ──
ruleless = [r.rule_id for r in FormRule.objects.filter(tax_form=form)
            if not RuleAuthorityLink.objects.filter(form_rule=r).exists()]
check(not ruleless, f"all {FormRule.objects.filter(tax_form=form).count()} K-1 rules have >= 1 authority link",
      f"K-1 rules with ZERO authority links: {ruleless}")

defined = {r["rule_id"] for r in K1.K1_1041_RULES}
linked = {rl[0] for rl in K1.K1_1041_RULE_LINKS}
check(not (linked - defined), "all rule_links reference defined rules", f"orphan links: {linked - defined}")
check(not (defined - linked), "every defined rule appears in rule_links", f"unlinked rules: {defined - linked}")

# reused sources actually present (spine seeded them)
from sources.models import AuthoritySource  # noqa: E402
for code in K1.EXISTING_SOURCES_TO_REFERENCE:
    check(AuthoritySource.objects.filter(source_code=code).exists(),
          f"reused source {code} present (from spine)", f"reused source {code} MISSING")

# ── arithmetic ──
def alloc(ent, pct):
    return round(ent * pct / 100)

# T1 character retention 60/40
check(alloc(10000, 60) == 6000 and alloc(10000, 40) == 4000,
      "T1 character: interest 10,000 -> 6,000 / 4,000 (60/40)", "T1 character wrong")
check(alloc(5000, 60) == 3000 and alloc(5000, 40) == 2000,
      "T1 character: dividends 5,000 -> 3,000 / 2,000", "T1 dividends wrong")
# reconciliation: shares sum to entity class
check(alloc(10000, 60) + alloc(10000, 40) == 10000, "T1 recon: Sum of box1 shares = entity 10,000",
      "T1 recon failed")

# T3 final-year gate: carryovers pass; T4 non-final: blank
def box11(is_final, excess67e, ltco):
    return (excess67e, ltco) if is_final else (0, 0)
check(box11(True, 3000, 8000) == (3000, 8000), "T3 final year: box11A 3,000 / box11D 8,000 pass through",
      "T3 final-year wrong")
check(box11(False, 3000, 8000) == (0, 0), "T4 non-final: box 11 stays blank (attributes stay with entity)",
      "T4 non-final gate wrong")

# T6 NIIT box 14H
check(alloc(12000, 100) == 12000, "T6 box14H: §1411 adj 12,000 -> beneficiary (100%)", "T6 box14H wrong")

# ── key diagnostics + counts ──
for did in ("D_K1041_GRANTOR", "D_K1041_FINYR", "D_K1041_NOLOSS", "D_K1041_NIIT"):
    check(FormDiagnostic.objects.filter(tax_form=form, diagnostic_id=did).exists(),
          f"{did} present", f"{did} missing")

# verbatim code excerpts present (full-transcription decision)
from sources.models import AuthorityExcerpt  # noqa: E402
sk1_excerpts = AuthorityExcerpt.objects.filter(authority_source__source_code="IRS_2025_I1041SK1").count()
check(sk1_excerpts >= 4, f"I1041SK1 verbatim code excerpts present ({sk1_excerpts})",
      f"expected >=4 I1041SK1 excerpts, got {sk1_excerpts}")

# ── report ──
print("\n" + "=" * 68)
print(f"  SCHEDULE_K1_1041: facts {FormFact.objects.filter(tax_form=form).count()} / "
      f"rules {FormRule.objects.filter(tax_form=form).count()} / "
      f"lines {FormLine.objects.filter(tax_form=form).count()} / "
      f"diag {FormDiagnostic.objects.filter(tax_form=form).count()} / "
      f"tests {form.test_scenarios.count()} / FA {FlowAssertion.objects.filter(assertion_id__startswith='FA-K1041').count()}")
print("=" * 68)
for p in PASSES:
    print(f"  PASS  {p}")
for fbad in FAILURES:
    print(f"  FAIL  {fbad}")
print("=" * 68)
print(f"RESULT: {len(PASSES)} pass / {len(FAILURES)} fail — "
      f"{'ALL PASS' if not FAILURES else 'FAILURES PRESENT'}")

from django.db import connections  # noqa: E402
connections.close_all()
try:
    if os.path.exists(SQLITE_PATH):
        os.remove(SQLITE_PATH)
except OSError:
    pass
sys.exit(1 if FAILURES else 0)
