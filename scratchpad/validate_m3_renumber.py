"""Throwaway-SQLite validation for the 1120S_M3 renumber (audit unit #7, 2026-07-12).

Checks: the renumbered fact/line/rule/diagnostic/scenario sets against the
Rev. December 2019 face (f1120ss3.pdf, pymupdf-verified — NOT irs.gov's
f1120sm3.pdf, which is the C-corp 1120 M-3); stale fabricated rows really
deleted — runs the loader TWICE against a pre-polluted DB; every rule linked
(links refresh-deleted); arithmetic oracles for the scenarios incl. the Part I
combine and the P3 L32 sign-flip; the SCHB stale "$50M" link note gone; the
M3_INSTR verbatim excerpt labels present; CharField caps. ASCII-only prints.

Run: <rs-venv>/Scripts/python.exe scratchpad/validate_m3_renumber.py
"""
import os
import sys

PROJECT_ROOT = r"D:\dev\sherpa-tax-rule-studio"
sys.path.insert(0, PROJECT_ROOT)

SQLITE_PATH = os.path.join(PROJECT_ROOT, "scratchpad", "validate_m3.sqlite3")
if os.path.exists(SQLITE_PATH):
    os.remove(SQLITE_PATH)
os.environ["DATABASE_URL"] = f"sqlite:///{SQLITE_PATH}"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

import django  # noqa: E402
django.setup()

from django.core.management import call_command  # noqa: E402
from specs.models import (  # noqa: E402
    FormDiagnostic, FormFact, FormLine, FormRule, TaxForm, TestScenario,
)
from sources.models import AuthorityExcerpt, AuthoritySource, RuleAuthorityLink  # noqa: E402

FAILURES: list[str] = []
PASSES: list[str] = []


def check(cond, ok, bad):
    (PASSES if cond else FAILURES).append(ok if cond else bad)


call_command("migrate", run_syncdb=True, verbosity=0)

from specs.management.commands.load_1120s_complete import EXISTING_SOURCES  # noqa: E402
for code in EXISTING_SOURCES:
    AuthoritySource.objects.get_or_create(
        source_code=code,
        defaults={"source_type": "statute", "source_rank": "primary_official",
                  "jurisdiction_code": "FED", "title": f"stub {code}",
                  "citation": code, "issuer": "IRS", "current_status": "active"})

# ── First seed run ──────────────────────────────────────────────────────────
call_command("load_1120s_complete", verbosity=0)

form = TaxForm.objects.get(form_number="1120S_M3", tax_year=2025)
schb = TaxForm.objects.get(form_number="1120S_SCHB", tax_year=2025)

# ── Pollute with the pre-renumber fabricated shapes, then re-run ────────────
FormFact.objects.get_or_create(tax_form=form, fact_key="income_book_amount",
                               defaults={"label": "stale aggregate", "data_type": "decimal"})
FormFact.objects.get_or_create(tax_form=form, fact_key="m3_reconciliation_total",
                               defaults={"label": "stale aggregate", "data_type": "decimal"})
FormLine.objects.get_or_create(tax_form=form, line_number="P3-36",
                               defaults={"description": "fabricated reconciliation totals row",
                                         "line_type": "total"})
FormLine.objects.get_or_create(tax_form=form, line_number="P1-FS",
                               defaults={"description": "fabricated FS-type row", "line_type": "informational"})
FormRule.objects.get_or_create(tax_form=form, rule_id="R099",
                               defaults={"title": "stale rule", "rule_type": "validation",
                                         "formula": "x", "inputs": [], "outputs": []})
FormDiagnostic.objects.get_or_create(tax_form=form, diagnostic_id="D099",
                                     defaults={"title": "stale", "severity": "error",
                                               "condition": "x", "message": "stale"})
# Re-create the stale SCHB "$50M" link note shape (the s44 leftover)
schb_r003 = FormRule.objects.get(tax_form=schb, rule_id="R003")
m3_src = AuthoritySource.objects.get(source_code="IRS_2025_1120S_M3_INSTR")
RuleAuthorityLink.objects.get_or_create(
    form_rule=schb_r003, authority_source=m3_src,
    defaults={"support_level": "primary", "relevance_note": "M-3 threshold: $50M total assets"})
RuleAuthorityLink.objects.filter(form_rule=schb_r003, authority_source=m3_src).update(
    relevance_note="M-3 threshold: $50M total assets")

call_command("load_1120s_complete", verbosity=0)

# ── Line set == the Rev. 12-2019 face ───────────────────────────────────────
FACE_LINES = (
    {"I-1a", "I-1b", "I-2", "I-3a", "I-3b", "I-4a", "I-4b", "I-5a", "I-5b",
     "I-6a", "I-6b", "I-7a", "I-7b", "I-7c", "I-8", "I-9", "I-10", "I-11",
     "I-12a", "I-12b", "I-12c", "I-12d"}
    | {f"II-{n}" for n in list(range(1, 21)) + list(range(22, 27))}
    | {f"II-21{c}" for c in "abcdefg"}
    | {f"III-{n}" for n in list(range(1, 23)) + list(range(24, 33))}
    | {"III-23a", "III-23b"}
)
got = set(FormLine.objects.filter(tax_form=form).values_list("line_number", flat=True))
check(got == FACE_LINES, f"M-3 line set == Rev. 12-2019 face ({len(FACE_LINES)} rows)",
      f"M-3 line set mismatch: extra={sorted(got - FACE_LINES)} missing={sorted(FACE_LINES - got)}")
check(len(FACE_LINES) == 87, "face row count = 87 (22 + 32 + 33)", f"row count {len(FACE_LINES)}")

l11 = FormLine.objects.get(tax_form=form, line_number="I-11")
check("Combine lines 4 through 10" in l11.description and "line 26, column (a)" in l11.description,
      "I-11 = combine 4-10 + the tie note", f"I-11 wrong: {l11.description!r}")
l26 = FormLine.objects.get(tax_form=form, line_number="II-26")
check("Schedule K, line 18" in l26.description, "II-26 carries the K18 tie note",
      f"II-26 wrong: {l26.description!r}")
l32 = FormLine.objects.get(tax_form=form, line_number="III-32")
check("positive amounts as negative" in l32.description, "III-32 carries the sign-flip verbatim",
      f"III-32 wrong: {l32.description!r}")
l22r = FormLine.objects.get(tax_form=form, line_number="III-22")
check(l22r.line_type == "informational" and "Reserved" in l22r.description,
      "III-22 = Reserved (informational)", f"III-22: {l22r.line_type} {l22r.description!r}")

# ── Facts ───────────────────────────────────────────────────────────────────
FACTS = {"total_assets_eoy", "voluntary_filing", "through_part_i_only",
         "fs_certified_audited", "fs_non_tax_basis", "is_period_beginning",
         "is_period_ending", "restated_current_period", "restated_preceding_periods",
         "ww_consolidated_net_income", "accounting_standard", "accounting_standard_other",
         "nonincl_foreign_income", "nonincl_foreign_loss", "nonincl_us_income",
         "nonincl_us_loss", "dre_foreign_ni", "dre_us_ni", "qsub_ni",
         "eliminations_adjustment", "period_adjustment", "other_adjustments",
         "l12a_assets", "l12a_liabilities", "l12b_assets", "l12b_liabilities",
         "l12c_assets", "l12c_liabilities", "l12d_assets", "l12d_liabilities"}
got_facts = set(FormFact.objects.filter(tax_form=form).values_list("fact_key", flat=True))
check(got_facts == FACTS, "M-3 fact set == the 30 face-keyed facts (generic aggregates gone)",
      f"M-3 facts mismatch: extra={sorted(got_facts - FACTS)} missing={sorted(FACTS - got_facts)}")
acct = FormFact.objects.get(tax_form=form, fact_key="accounting_standard")
check(acct.data_type == "choice" and set(acct.choices) == {"gaap", "ifrs", "tax_basis", "other"},
      "accounting_standard = the 4b choice list", f"accounting_standard: {acct.choices}")

# ── Rules R001-R005, linked, threshold semantics ────────────────────────────
rules = {r.rule_id: r for r in FormRule.objects.filter(tax_form=form)}
check(set(rules) == {"R001", "R002", "R003", "R004", "R005"},
      "M-3 rules R001-R005 (stale R099 gone)", f"M-3 rule set: {sorted(rules)}")
for rid, rule in sorted(rules.items()):
    n = RuleAuthorityLink.objects.filter(form_rule=rule).count()
    check(n >= 1, f"{rid} has {n} authority link(s)", f"{rid} has NO authority links")
check("10000000" in rules["R001"].formula, "R001 filing threshold = $10M",
      f"R001 formula: {rules['R001'].formula!r}")
check("50000000" in rules["R005"].formula and "through_part_i_only" in rules["R005"].formula,
      "R005 = the $50M entirely tier + the through-Part-I option",
      f"R005 formula: {rules['R005'].formula!r}")
check("Form 1065" in rules["R005"].description and "typo" in rules["R005"].description,
      "R005 flags the published (Form 1065) typo without propagating it",
      "R005 missing the typo flag")
check("schedule_k_line_18" in rules["R003"].formula,
      "R003 carries the L26(d) = K18 tie", f"R003 formula: {rules['R003'].formula!r}")
check("-line_32" in rules["R004"].formula.replace(" ", ""),
      "R004 carries the sign-flip", f"R004 formula: {rules['R004'].formula!r}")

# ── SCHB stale link note healed ─────────────────────────────────────────────
stale = RuleAuthorityLink.objects.filter(
    form_rule__tax_form=schb, relevance_note="M-3 threshold: $50M total assets").count()
check(stale == 0, "the SCHB '$50M' stale link note is gone (refresh-delete)",
      f"{stale} stale SCHB link note(s) survive")
fresh = RuleAuthorityLink.objects.filter(
    form_rule=schb_r003, relevance_note__icontains="$10M Schedule L").count()
check(fresh == 1, "SCHB R003 -> M3_INSTR note now says $10M Schedule L",
      f"SCHB R003 fresh-note count: {fresh}")

# ── Diagnostics ─────────────────────────────────────────────────────────────
diags = set(FormDiagnostic.objects.filter(tax_form=form).values_list("diagnostic_id", flat=True))
check(diags == {"D001", "D002", "D003", "D004", "D005", "D006", "D007"},
      "M-3 diagnostics D001-D007 (stale D099 gone)", f"M-3 diag set: {sorted(diags)}")

# ── Scenarios + oracles ─────────────────────────────────────────────────────
scen = {t.scenario_name: t for t in TestScenario.objects.filter(tax_form=form)}
check(len(scen) == 5, "5 scenarios", f"scenarios: {sorted(scen)}")

t = scen["Part I line 11 combine (4 through 10)"]
calc = (t.inputs["ww_consolidated_net_income"] - t.inputs["nonincl_foreign_income"]
        + t.inputs["nonincl_us_loss"] + t.inputs["period_adjustment"])
check(calc == t.expected_outputs["line_11"] == 860000,
      "P1 L11 oracle: 1,000,000 - 200,000 + 50,000 + 10,000 = 860,000",
      f"P1 L11 mismatch: {calc} vs {t.expected_outputs}")

t = scen["Part III line 32 sign-flip + the line 26 ties"]
l24 = -t.inputs["p3_line_32_col_d"]
l26d = t.inputs["p2_line_23_col_d"] + l24 + t.inputs["p2_line_25"]
check(l24 == t.expected_outputs["p2_line_24_col_d"] == -700000
      and l26d == t.expected_outputs["p2_line_26_col_d"] == 200000
      and l26d == t.inputs["schedule_k_line_18"],
      "sign-flip oracle: L24 = -700,000; L26(d) = 200,000 = Schedule K L18",
      f"sign-flip mismatch: l24={l24} l26d={l26d} vs {t.expected_outputs}")

t = scen["Schedule L reads the gate — published Example 1"]
check(t.inputs["total_assets_eoy"] < 10000000 <= t.inputs["consolidated_fs_assets"]
      and t.expected_outputs["must_file_m3"] is False,
      "Example 1 pin: $8M Schedule L / $12M FS -> not required",
      f"Example 1 mismatch: {t.inputs} {t.expected_outputs}")

for name, assets, must, entirely in [
    ("Threshold check — M-3 required", 75000000, True, True),
    ("Threshold check — $12M filer (the $10M-$50M band)", 12000000, True, False),
]:
    t = scen[name]
    check(t.inputs["total_assets_eoy"] == assets
          and t.expected_outputs["must_file_m3"] is must
          and t.expected_outputs["complete_entirely_required"] is entirely
          and (assets >= 10000000) is must and (assets >= 50000000) is entirely,
          f"threshold oracle holds: {name}",
          f"{name}: {t.inputs} {t.expected_outputs}")

# ── Excerpts ────────────────────────────────────────────────────────────────
labels = set(AuthorityExcerpt.objects.filter(authority_source=m3_src).values_list("excerpt_label", flat=True))
WANT = {"Schedule M-3 — filing threshold and structure",
        "Completing Schedule M-3 — the $50M entirely / through-Part-I tiers (verbatim)",
        "Purpose — Part I line 11 reconciles to Schedule K line 18 (verbatim)",
        "Part III line 32 — sign-flip carry to Part II line 24 (face verbatim)",
        "Item C checkbox — M-3 attached (verbatim)"}
check(WANT <= labels, "all 5 M-3 verbatim excerpt labels present",
      f"excerpt labels missing: {sorted(WANT - labels)}")
main = AuthorityExcerpt.objects.get(authority_source=m3_src,
                                    excerpt_label="Schedule M-3 — filing threshold and structure")
check("UNVERIFIED" not in main.excerpt_text and "Schedule L of Form 1120-S total assets" in main.excerpt_text,
      "the threshold excerpt is now Who-Must-File verbatim (UNVERIFIED warning retired)",
      "the threshold excerpt still carries the old text")
check("UNVERIFIED" not in (form.notes or ""), "form notes: UNVERIFIED warning retired",
      f"form notes still say UNVERIFIED: {form.notes[:120]!r}")

# ── CharField caps ──────────────────────────────────────────────────────────
for f in FormFact.objects.filter(tax_form=form):
    check(len(f.fact_key) <= 100 and len(f.label) <= 255, f"fact lens ok: {f.fact_key}",
          f"fact too long: {f.fact_key} ({len(f.fact_key)}/{len(f.label)})")
for ln in FormLine.objects.filter(tax_form=form):
    check(len(ln.line_number) <= 20, f"line_number len ok: {ln.line_number}",
          f"line_number too long: {ln.line_number}")
for r in FormRule.objects.filter(tax_form=form):
    check(len(r.rule_id) <= 20 and len(r.title) <= 255, f"rule lens ok: {r.rule_id}",
          f"rule too long: {r.rule_id} title={len(r.title)}")
for d in FormDiagnostic.objects.filter(tax_form=form):
    check(len(d.diagnostic_id) <= 20 and len(d.title) <= 255, f"diag lens ok: {d.diagnostic_id}",
          f"diag too long: {d.diagnostic_id}")
for t in TestScenario.objects.filter(tax_form=form):
    check(len(t.scenario_name) <= 255, f"scenario name len ok: {t.scenario_name[:40]}",
          f"scenario name too long: {t.scenario_name[:60]}")

# ── Report ──────────────────────────────────────────────────────────────────
print(f"\n{len(PASSES)} pass / {len(FAILURES)} fail")
if FAILURES:
    print("\nFAILURES:")
    for f in FAILURES:
        print("  FAIL:", f)
    sys.exit(1)
print("ALL CHECKS PASS")
