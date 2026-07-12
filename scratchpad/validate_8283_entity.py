"""Throwaway-SQLite validation for the 8283 ENTITY-ARM amendment (tts Spine
S-20a RS leg, 2026-07-12).

Checks: the amendment is purely ADDITIVE on the 2026-07-03 authored spec
(rules 5->9, diagnostics 13->16, scenarios 13->16, FAs 5->7) with D_8283_010
re-scoped in place; the two new i8283 Rev-12-2025 PTE excerpts land verbatim
on IRS_2025_8283_INSTR; the new FA-ENT-8283-01/02 stage as DRAFT (the
new-FAs-default-ACTIVE trap — the tts export-verbatim mirrors must not pick
them up before their runners land); arithmetic oracles for T14/T15/T16;
every new rule linked; id caps; loader runs TWICE clean (idempotent) against
a pre-polluted D_8283_010 old title. ASCII-only prints.

Run: <rs-venv>/Scripts/python.exe scratchpad/validate_8283_entity.py
"""
import os
import sys

PROJECT_ROOT = r"D:\dev\sherpa-tax-rule-studio"
sys.path.insert(0, PROJECT_ROOT)

SQLITE_PATH = os.path.join(PROJECT_ROOT, "scratchpad", "validate_8283_entity.sqlite3")
if os.path.exists(SQLITE_PATH):
    os.remove(SQLITE_PATH)
os.environ["DATABASE_URL"] = f"sqlite:///{SQLITE_PATH}"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

import django  # noqa: E402
django.setup()

from django.core.management import call_command  # noqa: E402
from specs.models import (  # noqa: E402
    FlowAssertion, FormDiagnostic, FormFact, FormLine, FormRule, TaxForm, TestScenario,
)
from sources.models import AuthorityExcerpt, AuthoritySource, RuleAuthorityLink  # noqa: E402

FAILURES: list[str] = []
PASSES: list[str] = []


def check(cond, ok, bad):
    (PASSES if cond else FAILURES).append(ok if cond else bad)


call_command("migrate", run_syncdb=True, verbosity=0)

# The loader references two sources it does not author — stub them.
for code in ("IRS_PUB526_2025", "IRS_2025_SCHA_INSTR"):
    AuthoritySource.objects.get_or_create(
        source_code=code,
        defaults={"source_type": "irs_publication", "source_rank": "primary_official",
                  "jurisdiction_code": "FED", "title": f"stub {code}",
                  "citation": code, "issuer": "IRS", "current_status": "active"})

# ── Pre-pollute: the OLD D_8283_010 shape (pre-amendment title) ─────────────
form_stub, _ = TaxForm.objects.get_or_create(
    form_number="8283", tax_year=2025,
    defaults={"form_title": "old title", "jurisdiction": "FED",
              "entity_types": ["1120S", "1065", "1040"], "version": 1, "status": "draft"})
FormDiagnostic.objects.get_or_create(
    tax_form=form_stub, diagnostic_id="D_8283_010",
    defaults={"title": "Pass-through-entity 8283 mechanics not modeled (stated boundary)",
              "severity": "info", "condition": "old", "message": "old"})

# ── First run ───────────────────────────────────────────────────────────────
call_command("load_1040_form_8283", verbosity=0)
form = TaxForm.objects.get(form_number="8283", tax_year=2025)

counts1 = dict(
    rules=FormRule.objects.filter(tax_form=form).count(),
    diags=FormDiagnostic.objects.filter(tax_form=form).count(),
    scen=TestScenario.objects.filter(tax_form=form).count(),
    facts=FormFact.objects.filter(tax_form=form).count(),
    lines=FormLine.objects.filter(tax_form=form).count(),
    fas=FlowAssertion.objects.filter(assertion_id__contains="8283").count(),
)

# ── Second run (idempotence) ────────────────────────────────────────────────
call_command("load_1040_form_8283", verbosity=0)
counts2 = dict(
    rules=FormRule.objects.filter(tax_form=form).count(),
    diags=FormDiagnostic.objects.filter(tax_form=form).count(),
    scen=TestScenario.objects.filter(tax_form=form).count(),
    facts=FormFact.objects.filter(tax_form=form).count(),
    lines=FormLine.objects.filter(tax_form=form).count(),
    fas=FlowAssertion.objects.filter(assertion_id__contains="8283").count(),
)
check(counts1 == counts2, f"idempotent twice-run: {counts1}",
      f"twice-run drift: {counts1} != {counts2}")

# ── Counts: additive amendment ──────────────────────────────────────────────
check(counts1["rules"] == 9, "rules = 9 (5 + 4 entity)", f"rules = {counts1['rules']} != 9")
check(counts1["diags"] == 16, "diagnostics = 16 (13 + 3 entity)", f"diags = {counts1['diags']} != 16")
check(counts1["scen"] == 16, "scenarios = 16 (13 + T14-T16)", f"scen = {counts1['scen']} != 16")
check(counts1["facts"] == 51, "facts unchanged at 51", f"facts = {counts1['facts']} != 51")
check(counts1["fas"] == 7, "8283 FAs = 7 (5 + 2 entity)", f"8283 FAs = {counts1['fas']} != 7")

# ── New rules present, linked, id-capped ────────────────────────────────────
ENT_RULES = ["R-8283-ENTFILE", "R-8283-ENTSECB", "R-8283-ENTFEED", "R-8283-ENTCOPY"]
for rid in ENT_RULES:
    r = FormRule.objects.filter(tax_form=form, rule_id=rid).first()
    check(r is not None, f"{rid} present", f"{rid} MISSING")
    check(len(rid) <= 20, f"{rid} id <= 20 chars", f"{rid} id exceeds varchar(20)")
    if r:
        n = RuleAuthorityLink.objects.filter(form_rule=r).count()
        check(n >= 1, f"{rid} linked ({n})", f"{rid} has NO authority links")

r_secb = FormRule.objects.get(tax_form=form, rule_id="R-8283-ENTSECB")
check("$5,000 or less" in r_secb.formula,
      "ENTSECB carries the no-per-member-division verbatim phrase",
      "ENTSECB missing the '$5,000 or less' pin")
r_feed = FormRule.objects.get(tax_form=form, rule_id="R-8283-ENTFEED")
check("NO FEED" in r_feed.formula and "13a" in r_feed.formula,
      "ENTFEED encodes the 1065 no-feed arm",
      "ENTFEED lost the 1065 no-feed arm")

# ── D_8283_010 re-scoped IN PLACE (pre-polluted old title overwritten) ─────
d10 = FormDiagnostic.objects.get(tax_form=form, diagnostic_id="D_8283_010")
check(d10.title.startswith("Member-of-PTE"),
      "D_8283_010 re-scoped to the member side (old title overwritten)",
      f"D_8283_010 title stale: {d10.title!r}")

# ── New diagnostics: severities ─────────────────────────────────────────────
for did, sev in (("D_8283_014", "error"), ("D_8283_015", "info"), ("D_8283_016", "warning")):
    d = FormDiagnostic.objects.filter(tax_form=form, diagnostic_id=did).first()
    check(d is not None and d.severity == sev,
          f"{did} present, severity {sev}",
          f"{did} missing or wrong severity ({getattr(d, 'severity', None)})")

# ── Scenarios: arithmetic oracles ───────────────────────────────────────────
t14 = TestScenario.objects.filter(tax_form=form, scenario_name__startswith="8283-T14").first()
check(t14 is not None, "T14 present", "T14 MISSING")
if t14:
    rows = t14.inputs["rows"]
    total = sum(r["amount"] for r in rows)
    check(total == 3000 and t14.expected_outputs["k12b_default"] == 3000,
          "T14 oracle: rows 3,000 == k12b_default 3,000",
          f"T14 oracle broken: rows {total} vs expected {t14.expected_outputs}")
    check(t14.expected_outputs["k12b_with_typed_override_2500"] == 2500,
          "T14 GREEN-override oracle: typed 2,500 wins",
          "T14 override oracle broken")
    check(total > 500 and t14.expected_outputs["f8283_engaged"] is True,
          "T14 engagement oracle: 3,000 > 500", "T14 engagement oracle broken")

t15 = TestScenario.objects.filter(tax_form=form, scenario_name__startswith="8283-T15").first()
check(t15 is not None, "T15 present", "T15 MISSING")
if t15:
    amt = t15.inputs["rows"][0]["amount"]
    pcts = [s["pct"] for s in t15.inputs["shareholders"]]
    per = amt * pcts[0] // 100
    check(amt > 5000 and t15.expected_outputs["row_sections"] == ["B"],
          "T15 oracle: 6,000 > 5,000 -> Section B at entity level",
          "T15 Section-B oracle broken")
    check(per == 3000 == t15.expected_outputs["per_member_allocation"] and per <= 5000,
          "T15 oracle: per-member 3,000 (<= 5,000) — the division-first regression pin",
          f"T15 per-member oracle broken ({per})")

t16 = TestScenario.objects.filter(tax_form=form, scenario_name__startswith="8283-T16").first()
check(t16 is not None, "T16 present", "T16 MISSING")
if t16:
    check(t16.inputs["entity_type"] == "1065"
          and t16.expected_outputs["k13a_after_compute"] == 0
          and t16.expected_outputs["D_8283_016"] is True,
          "T16 oracle: 1065 no-feed (13a stays 0) + D_8283_016 fires",
          "T16 no-feed oracle broken")

# ── FAs: staged DRAFT (the new-FAs-default-ACTIVE trap) ─────────────────────
for aid in ("FA-ENT-8283-01", "FA-ENT-8283-02"):
    fa = FlowAssertion.objects.filter(assertion_id=aid).first()
    check(fa is not None and fa.status == "draft",
          f"{aid} staged DRAFT (export excludes until the tts runners land)",
          f"{aid} missing or NOT draft ({getattr(fa, 'status', None)}) — would break the tts export-verbatim mirrors")
for aid in [f"FA-1040-8283-0{i}" for i in range(1, 6)]:
    fa = FlowAssertion.objects.filter(assertion_id=aid).first()
    check(fa is not None and fa.status == "active",
          f"{aid} still active", f"{aid} regressed ({getattr(fa, 'status', None)})")
check(FlowAssertion.objects.get(assertion_id="FA-ENT-8283-02").entity_types == ["1120S", "1065"],
      "FA-ENT-8283-02 scoped 1120S+1065", "FA-ENT-8283-02 entity scope wrong")

# ── Excerpts: the two PTE passages verbatim on IRS_2025_8283_INSTR ─────────
src = AuthoritySource.objects.get(source_code="IRS_2025_8283_INSTR")
exc = {e.excerpt_label: e for e in AuthorityExcerpt.objects.filter(authority_source=src)}
pte = [e for label, e in exc.items() if label.startswith("Partnerships and S corporations")]
mem = [e for label, e in exc.items() if label.startswith("Members of pass-through entities")]
check(len(pte) == 1 and "must file Form 8283 (Section A or Section B) with its Form 1065 or 1120-S"
      in pte[0].excerpt_text,
      "PTE excerpt present, filing-gate phrase verbatim", "PTE excerpt missing/mangled")
check(len(pte) == 1 and "is $5,000 or less" in pte[0].excerpt_text
      and "completed copy of Form 8283" in pte[0].excerpt_text,
      "PTE excerpt carries the Section-B + copy-to-members phrases verbatim",
      "PTE excerpt missing the Section-B/copy phrases")
check(len(mem) == 1 and "Section B, Part I, line 3, Column(c)" in mem[0].excerpt_text,
      "Members excerpt present with the K-1-amounts exception verbatim",
      "Members excerpt missing/mangled")

# ── entity_types preserved on the shared form ───────────────────────────────
check(sorted(form.entity_types) == sorted(["1120S", "1065", "1040"]),
      "shared form entity_types preserved (1120S/1065/1040)",
      f"entity_types clobbered: {form.entity_types}")

# ── Report ──────────────────────────────────────────────────────────────────
print(f"\n{'='*70}\nPASS {len(PASSES)} / FAIL {len(FAILURES)}")
for p in PASSES:
    print("  ok:", p)
if FAILURES:
    print("-" * 70)
    for f in FAILURES:
        print("  FAIL:", f)
    sys.exit(1)
print("ALL CHECKS GREEN")
