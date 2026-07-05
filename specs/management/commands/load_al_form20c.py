"""Load the Alabama Form 20C spec — Corporation Income Tax Return (TY2025).
WO-12, the reuse-state C-corp batch (form 2 of 3). Extends the federal 1120 module (WO-11).

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
Alabama Form 20C is the AL C-corporation income tax return: 6.5% flat rate on Alabama taxable
income (federal-TI start + Schedule A add/subtract + single-sales-factor apportionment − the
FEDERAL INCOME TAX DEDUCTION). Two AL signatures this spec must get right:
  1. The FEDERAL INCOME TAX DEDUCTION (L11a / Schedule E) is CONSTITUTIONALLY PROTECTED
     (Amendment 662) — it was NOT repealed by Act 2021-1. Both AL Form 40 (individuals) and
     Form 20C (corps) keep it. Encode L11a + the apportioned Schedule E computation.
  2. Alabama CONFORMS to §168(k)/§179 (rolling conformity; OBBBA flows through) — there is NO
     GA-style depreciation add-back. The real AL decouples are GILTI (§40-18-35.2) and §174 R&E
     (§40-18-62).

Greenfield: no `AL_FORM_20C` at the 2026-07-05 gap-check (only the individual AL_FORM_40 existed).

═══════════════════════════════════════════════════════════════════════════
v1 SCOPE — LOCKED (Ken's Gate-1 walk 2026-07-05; DECISIONS D-14). See state_ccorp_batch_source_brief.md.
═══════════════════════════════════════════════════════════════════════════
COMPUTES: 6.5% income tax (federal-TI + Sch A add/subtract -> single-sales-factor apportionment -> AL
income before FIT -> minus the APPORTIONED FIT deduction (Q2: federal tax × AL ratio) -> AL NOL -> 6.5%).
GILTI (§951A subtract / §250 add-back) and §174 R&E (deduct / federal-amort add-back) = Schedule A
lines + diagnostics, direct-entry (Q4). NO depreciation add-back (AL conforms).

═══════════════════════════════════════════════════════════════════════════
requires_human_review WALK ITEMS (W4-W6)
═══════════════════════════════════════════════════════════════════════════
W4. ⚠ FIT DEDUCTION (L11a / Schedule E) — NOT repealed; constitutionally protected (Amendment 662).
    Computed as federal income tax × AL apportionment ratio (Schedule E line 9). CONFIRM the mechanic +
    that it stays in the spec (a future editor recalling Act 2021-1 must not remove it).
W5. AL CONFORMS to §168(k)/§179 (rolling conformity, §40-18-1.1) — NO depreciation add-back for 2025
    assets (only the legacy 2008-Stimulus-Act basis difference decouples). CONFIRM (opposite of SC/NC/GA).
W6. AL decouples = GILTI (§40-18-35.2: §951A subtract / §250 add-back) + §174 R&E (§40-18-62: full R&E
    deduct / federal-amort add-back), Schedule A lines + diagnostics, direct-entry. CONFIRM.

═══════════════════════════════════════════════════════════════════════════
CARRIED [UNVERIFIED]: Schedule E consolidated-filer lines 1-5 simplified (direct ratio); AL 20C due one
month after federal = May 15 2026. Re-verify rate/conformity at TY2026.
═══════════════════════════════════════════════════════════════════════════

SAFETY GUARD — READY_TO_SEED stays False until Ken approves the review walk (W4-W6).
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from sources.models import (
    AuthorityExcerpt, AuthorityFormLink, AuthoritySource, AuthoritySourceTopic,
    AuthorityTopic, RuleAuthorityLink,
)
from specs.models import (
    FlowAssertion, FormDiagnostic, FormFact, FormLine, FormRule, TaxForm, TestScenario,
)

# FLIPPED 2026-07-05 — Ken APPROVED ("Seed all three now"): W4 the constitutional FIT
# deduction (Amendment 662, L11a/Sch E — NOT repealed), W5 AL conforms to §168(k)/§179
# (no add-back), W6 the GILTI/§174 decouples. Validated (validate_state_ccorp.py, 41/0).
READY_TO_SEED = True

FORM_JURISDICTION = "AL"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1120"]

# Verified constants (state_ccorp_batch_source_brief.md; 2025 Form 20C / instructions / ALDOR OBBBA summary)
AL_RATE = "0.065"                  # §40-18-31 / Form 20C L15 — 6.5% flat (capped by Amendment 662)


def _al_income_tax(fed_ti, additions, subtractions, federal_income_tax, nol, ratio):
    """AL 20C path. FIT deduction (Sch E) is apportioned by the AL ratio. Returns (al_taxable, income_tax)."""
    apportioned = (float(fed_ti) + float(additions) - float(subtractions)) * float(ratio)
    fit_deduction = float(federal_income_tax) * float(ratio)   # Schedule E line 10 = federal tax × AL ratio
    al_taxable = apportioned - fit_deduction - min(float(nol), max(0.0, apportioned - fit_deduction))
    return al_taxable, max(0.0, al_taxable) * float(AL_RATE)


AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("al_corp_tax", "Alabama Form 20C C-corporation: 6.5% income tax (federal-TI + Schedule A add/subtract + "
     "single-sales-factor apportionment - the constitutional federal income tax deduction), AL conformity to "
     "§168(k)/§179, and the GILTI/§174 decouples."),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "AL_2025_FORM_20C", "source_type": "state_form", "source_rank": "primary_official",
        "jurisdiction_code": "AL", "title": "2025 Alabama Form 20C — Corporation Income Tax Return",
        "citation": "Alabama Form 20C (2025)", "issuer": "Alabama Department of Revenue",
        "official_url": "https://www.revenue.alabama.gov/",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.5, "topics": ["al_corp_tax"],
        "excerpts": [{
            "excerpt_label": "Form 20C line flow + 6.5% + FIT deduction (2025 verbatim)",
            "excerpt_text": (
                "L1 'FEDERAL TAXABLE INCOME' (before federal NOL); Schedule A additions (L9 §250 FDII/GILTI "
                "add-back; L10 other/§174 federal-amort add-back) and deductions (L23 §951A GILTI; L24 §174 R&E; "
                "L13 US-obligation interest); L7 'Alabama apportionment factor (from line 9, Schedule D-1)'; L10 "
                "'Alabama income before federal income tax deduction'; L11a 'Federal income tax deduction/"
                "(refund) (from line 12, Schedule E)'; L14 Alabama taxable income; L15 'Alabama Income Tax (6.5% "
                "of line 14)'. Schedule E computes the FIT deduction: line 9 = federal income tax ratio (AL "
                "income / adjusted total income), line 10 = federal tax × that ratio -> L11a. Schedule D-1 = "
                "single sales factor (AL sales / everywhere sales). NOL = Schedule B, 15-yr carryforward, no "
                "carryback. Page-4 Other Info L10 = Business Privilege Tax checkbox (separate Form CPT)."
            ),
            "summary_text": "20C: L1 fed TI -> Sch A add/sub -> L7 single sales factor -> L10 AL income before FIT -> L11a FIT deduction (Sch E, apportioned) -> L14 AL taxable -> L15 x 6.5%. BPT = separate Form CPT.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "AL_2025_20C_INSTR", "source_type": "official_instructions", "source_rank": "primary_official",
        "jurisdiction_code": "AL", "title": "2025 Alabama Form 20C Instructions (+ ALDOR OBBBA Executive Summary)",
        "citation": "Form 20C Instructions (2025); ALDOR OBBBA Executive Summary (Nov 10, 2025)", "issuer": "Alabama Department of Revenue",
        "official_url": "https://www.revenue.alabama.gov/",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.4, "topics": ["al_corp_tax"],
        "excerpts": [{
            "excerpt_label": "AL conforms to §168(k)/§179; GILTI/§174 decouple; due date (verbatim substance)",
            "excerpt_text": (
                "ALDOR OBBBA summary (corporate, p.25-27), §40-18-33, all 'Tied to Federal: Yes': OBBBA "
                "'permanently restores the 100 percent bonus depreciation for property acquired and placed into "
                "service on or after January 19, 2025' and 'increases the maximum amount a taxpayer may expense "
                "under Code section 179 to $2.5 million ... phaseout ... to $4 million' — Alabama CONFORMS "
                "(rolling conformity, §40-18-1.1). NO general bonus/§179 add-back; only the 2008 Economic "
                "Stimulus Act basis difference decouples (Sch A L21). Decouples that survive: GILTI/§951A "
                "(§40-18-35.2 — Sch A L23 subtract §951A, L9 add back §250) and §174/§174A R&E (§40-18-62 — Sch "
                "A L24 deduct full R&E, L10 add back federal amortization). Instructions 'When To File': the "
                "return is due one month following the federal due date (calendar-year 2025 = May 15, 2026); "
                "extension is file-only."
            ),
            "summary_text": "AL conforms to §168(k)/§179 (no add-back). Decouples = GILTI (§40-18-35.2) + §174 R&E (§40-18-62). Due one month after federal (May 15, 2026).",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "AL_AMEND_662", "source_type": "statute", "source_rank": "controlling",
        "jurisdiction_code": "AL", "title": "Alabama Constitution Amendment 662 — federal income tax deduction (corporate)",
        "citation": "Ala. Const. Amend. 662 (2000); Code of Ala. §40-18-35(a)(2)", "issuer": "Alabama (Constitution)",
        "official_url": "https://www.revenue.alabama.gov/",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.5, "topics": ["al_corp_tax"],
        "excerpts": [{
            "excerpt_label": "FIT deduction is constitutional — NOT repealed (verbatim substance)",
            "excerpt_text": (
                "Amendment 662 (ratified June 19, 2000): 'all federal income taxes paid or accrued within the "
                "taxable year ... shall always be deductible' (apportioned for multistate corporations). Because "
                "the deduction is constitutionally mandated, Act 2021-1 did NOT and could not repeal it — the "
                "C-corporation federal income tax deduction remains on Form 20C (L11a / Schedule E) under "
                "§40-18-35(a)(2) / Rule 810-3-35-.01. (Act 2021-1 changed apportionment/throwback/GILTI, not the "
                "FIT deduction.) Encode L11a; do not remove it citing Act 2021-1."
            ),
            "summary_text": "Amendment 662: federal income taxes 'shall always be deductible' — the FIT deduction is constitutional; Act 2021-1 did NOT repeal it. Keep L11a/Schedule E.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "AL_CODE_40_18", "source_type": "statute", "source_rank": "controlling",
        "jurisdiction_code": "AL", "title": "Code of Ala. §40-18-1.1 (conformity) · §40-18-33 (AL TI) · §40-18-35.2 (GILTI) · §40-18-62 (§174)",
        "citation": "Code of Ala. §40-18-1.1; §40-18-33; §40-18-35.2; §40-18-62", "issuer": "Alabama Legislature",
        "official_url": "https://law.justia.com/codes/alabama/title-40/",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.2, "topics": ["al_corp_tax"],
        "excerpts": [{
            "excerpt_label": "AL conformity + single sales factor + decouples (substance)",
            "excerpt_text": (
                "§40-18-1.1: the IRC is defined as amended and in effect (rolling conformity) — OBBBA flows "
                "through automatically for 'tied' items. §40-18-33: AL taxable income = federal taxable income "
                "(without the federal NOL) plus specific additions and less specific deductions. §40-18-35.2: AL "
                "decouples from §951A (GILTI). §40-18-62: AL decouples from §174 capitalization (deduct full "
                "R&E). Apportionment (post-Act 2021-1, effective 1/1/2021): single sales factor (Schedule D-1); "
                "throwback repealed. Factor-presence nexus thresholds indexed (Act 2015-505)."
            ),
            "summary_text": "§40-18-1.1 rolling conformity; §40-18-33 AL TI = fed TI ± adjustments; §40-18-35.2 GILTI decouple; §40-18-62 §174 decouple; single sales factor.",
            "is_key_excerpt": True,
        }],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("AL_2025_FORM_20C", "AL_FORM_20C", "governs"), ("AL_2025_20C_INSTR", "AL_FORM_20C", "governs"),
    ("AL_AMEND_662", "AL_FORM_20C", "governs"), ("AL_CODE_40_18", "AL_FORM_20C", "governs"),
]


F_FACTS: list[dict] = [
    {"fact_key": "federal_taxable_income", "label": "Federal taxable income (before federal NOL) — Form 20C L1", "data_type": "decimal", "required": False, "sort_order": 1},
    {"fact_key": "al_additions_other", "label": "Other AL additions — taxes measured by income, non-AL bond interest, etc. (Sch A)", "data_type": "decimal", "required": False, "sort_order": 2},
    {"fact_key": "sec250_addback", "label": "§250 FDII/GILTI deduction add-back (Sch A L9)", "data_type": "decimal", "required": False, "sort_order": 3,
     "notes": "W6. AL decouples GILTI — the federal §250 deduction is added back."},
    {"fact_key": "rd_174_fed_amort_addback", "label": "§174 federally-amortized R&E add-back (Sch A L10)", "data_type": "decimal", "required": False, "sort_order": 4,
     "notes": "W6. AL decouples §174 — add back the federal amortization, deduct full R&E (Sch A L24)."},
    {"fact_key": "al_subtractions_other", "label": "Other AL subtractions — US-obligation interest, >20% foreign dividends (§243), §78 gross-up, etc. (Sch A)", "data_type": "decimal", "required": False, "sort_order": 5},
    {"fact_key": "gilti_951a_subtract", "label": "§951A GILTI subtraction (Sch A L23)", "data_type": "decimal", "required": False, "sort_order": 6,
     "notes": "W6. AL decouples §951A GILTI — subtract the GILTI included federally."},
    {"fact_key": "rd_174_deduct", "label": "§174 full R&E deduction (Sch A L24)", "data_type": "decimal", "required": False, "sort_order": 7,
     "notes": "W6. §40-18-62 — deduct full R&E (AL does not require §174 capitalization)."},
    {"fact_key": "federal_income_tax", "label": "Federal income tax paid/accrued (Schedule E FIT deduction base)", "data_type": "decimal", "required": False, "sort_order": 8,
     "notes": "W4. Amendment 662 — apportioned by the AL ratio to the L11a deduction."},
    {"fact_key": "is_multistate", "label": "Multistate corporation (apportion)? — if no, AL ratio = 100%", "data_type": "boolean", "required": False, "sort_order": 9},
    {"fact_key": "sales_al", "label": "Sales within Alabama (Schedule D-1 numerator)", "data_type": "decimal", "required": False, "sort_order": 10},
    {"fact_key": "sales_everywhere", "label": "Sales everywhere (Schedule D-1 denominator)", "data_type": "decimal", "required": False, "sort_order": 11},
    {"fact_key": "al_nol_carryover", "label": "AL net operating loss carryover (Schedule B; 15-yr, no carryback)", "data_type": "decimal", "required": False, "sort_order": 12},
]

F_RULES: list[dict] = [
    {"rule_id": "R-AL20C-ADD", "title": "AL additions (Schedule A) — incl. §250/§174 add-backs", "rule_type": "calculation",
     "formula": "additions = al_additions_other + sec250_addback + rd_174_fed_amort_addback",
     "inputs": ["al_additions_other", "sec250_addback", "rd_174_fed_amort_addback"], "outputs": ["additions"], "sort_order": 1,
     "description": "W6. Schedule A additions: general AL additions + the §250 FDII/GILTI deduction add-back (L9) + the §174 federally-amortized R&E add-back (L10). NO depreciation add-back — AL conforms to §168(k)/§179."},
    {"rule_id": "R-AL20C-SUB", "title": "AL subtractions (Schedule A) — incl. §951A/§174", "rule_type": "calculation",
     "formula": "subtractions = al_subtractions_other + gilti_951a_subtract + rd_174_deduct",
     "inputs": ["al_subtractions_other", "gilti_951a_subtract", "rd_174_deduct"], "outputs": ["subtractions"], "sort_order": 2,
     "description": "W6. Schedule A deductions: general AL subtractions + the §951A GILTI subtraction (L23, §40-18-35.2) + the full §174 R&E deduction (L24, §40-18-62)."},
    {"rule_id": "R-AL20C-APPORT", "title": "Single sales factor (Schedule D-1)", "rule_type": "calculation",
     "formula": "al_ratio = 1.0 if not is_multistate else (sales_al / sales_everywhere)",
     "inputs": ["is_multistate", "sales_al", "sales_everywhere"], "outputs": ["al_ratio"], "sort_order": 3,
     "description": "AL apportions by a single sales factor (Schedule D-1, post-Act 2021-1; throwback repealed)."},
    {"rule_id": "R-AL20C-FIT", "title": "Federal income tax deduction (L11a / Schedule E) — apportioned", "rule_type": "calculation",
     "formula": "fit_deduction = federal_income_tax * al_ratio",
     "inputs": ["federal_income_tax", "al_ratio"], "outputs": ["fit_deduction"], "sort_order": 4,
     "description": "W4. Amendment 662 (constitutional — NOT repealed by Act 2021-1). Schedule E: the federal income tax paid/accrued, apportioned by the AL income ratio (line 9), is deducted at L11a. Consolidated-filer Schedule E lines 1-5 are simplified to the direct ratio."},
    {"rule_id": "R-AL20C-INCOME", "title": "AL income tax — 6.5% (Form 20C L15)", "rule_type": "calculation",
     "formula": ("apportioned = (federal_taxable_income + additions - subtractions) * al_ratio ; "
                 "al_taxable = apportioned - fit_deduction - min(al_nol_carryover, max(0, apportioned - fit_deduction)) ; "
                 "income_tax = max(0, al_taxable) * 0.065"),
     "inputs": ["federal_taxable_income", "al_nol_carryover"], "outputs": ["al_taxable_income", "income_tax"], "sort_order": 5,
     "description": "W4/W5. §40-18-31/§40-18-33. Federal TI + Sch A additions - subtractions, apportioned (single sales factor) = AL income before FIT (L10); minus the apportioned federal income tax deduction (L11a); minus AL NOL (15-yr, no carryback) = AL taxable income (L14); times 6.5% (L15)."},
]

F_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-AL20C-ADD", "AL_2025_FORM_20C", "primary", "Schedule A additions L9/L10"),
    ("R-AL20C-ADD", "AL_CODE_40_18", "secondary", "§40-18-33 AL TI"),
    ("R-AL20C-SUB", "AL_CODE_40_18", "primary", "§40-18-35.2 GILTI / §40-18-62 §174"),
    ("R-AL20C-SUB", "AL_2025_FORM_20C", "secondary", "Schedule A deductions L23/L24"),
    ("R-AL20C-APPORT", "AL_CODE_40_18", "primary", "single sales factor (Schedule D-1)"),
    ("R-AL20C-FIT", "AL_AMEND_662", "primary", "Amendment 662 constitutional FIT deduction"),
    ("R-AL20C-FIT", "AL_2025_FORM_20C", "secondary", "L11a / Schedule E"),
    ("R-AL20C-INCOME", "AL_2025_FORM_20C", "primary", "L15 6.5% tax"),
    ("R-AL20C-INCOME", "AL_2025_20C_INSTR", "secondary", "AL conforms §168(k)/§179"),
]

F_LINES: list[dict] = [
    {"line_number": "AL-7", "description": "Form 20C L7 Alabama apportionment factor (Schedule D-1)", "line_type": "calculated", "source_rules": ["R-AL20C-APPORT"], "sort_order": 1},
    {"line_number": "AL-10", "description": "Form 20C L10 Alabama income before federal income tax deduction", "line_type": "calculated", "source_rules": ["R-AL20C-INCOME"], "sort_order": 2},
    {"line_number": "AL-11a", "description": "Form 20C L11a Federal income tax deduction (Schedule E)", "line_type": "calculated", "source_rules": ["R-AL20C-FIT"], "sort_order": 3},
    {"line_number": "AL-14", "description": "Form 20C L14 Alabama taxable income", "line_type": "calculated", "source_rules": ["R-AL20C-INCOME"], "sort_order": 4},
    {"line_number": "AL-15", "description": "Form 20C L15 Alabama income tax (× 6.5%)", "line_type": "calculated", "source_rules": ["R-AL20C-INCOME"], "sort_order": 5},
]

F_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_AL20C_FIT", "title": "AL federal income tax deduction is CONSTITUTIONAL (not repealed)", "severity": "info",
     "condition": "federal_income_tax > 0",
     "message": "Alabama allows corporations a deduction for federal income tax paid/accrued (Form 20C line 11a, Schedule E), apportioned by the Alabama income ratio. This deduction is CONSTITUTIONALLY MANDATED (Amendment 662, 'federal income taxes ... shall always be deductible') and was NOT repealed by Act 2021-1 — do not remove it. Both AL Form 40 (individuals) and Form 20C (corporations) retain it.",
     "notes": "W4."},
    {"diagnostic_id": "D_AL20C_DEPR", "title": "AL conforms to §168(k)/§179 — no depreciation add-back", "severity": "info",
     "condition": "always (informational)",
     "message": "Unlike Georgia, South Carolina, and North Carolina, Alabama CONFORMS to federal §168(k) bonus depreciation and §179 (rolling conformity, §40-18-1.1; OBBBA flows through — AL §179 = $2.5M/$4M for 2025). Do NOT apply a bonus/§179 add-back for 2025 assets. Only the legacy 2008 Economic Stimulus Act basis difference decouples (Schedule A line 21).",
     "notes": "W5."},
    {"diagnostic_id": "D_AL20C_GILTI", "title": "AL GILTI decouple (§40-18-35.2)", "severity": "info",
     "condition": "gilti_951a_subtract > 0 or sec250_addback > 0",
     "message": "Alabama decouples from §951A GILTI (§40-18-35.2): subtract the GILTI included in federal taxable income (Schedule A line 23) and add back the federal §250 FDII/GILTI deduction (Schedule A line 9). The §250 deduction applies only to the extent the same income is in Alabama taxable income.",
     "notes": "W6."},
    {"diagnostic_id": "D_AL20C_174", "title": "AL §174 R&E decouple (§40-18-62)", "severity": "info",
     "condition": "rd_174_deduct > 0 or rd_174_fed_amort_addback > 0",
     "message": "Alabama decouples from §174 R&E capitalization (§40-18-62): deduct the full research & experimental expenditures (Schedule A line 24) and add back the federally-amortized amount (Schedule A line 10).",
     "notes": "W6."},
    {"diagnostic_id": "D_AL20C_BPT", "title": "AL Business Privilege Tax is a separate return (Form CPT)", "severity": "info",
     "condition": "always (informational)",
     "message": "The Alabama Business Privilege Tax is a SEPARATE filing (Form CPT for C-corps) and is not computed on Form 20C — Form 20C only carries an informational checkbox (page 4, Other Information line 10). Do not compute the privilege tax here.",
     "notes": "Scope boundary."},
    {"diagnostic_id": "D_AL20C_DUE", "title": "AL 20C due one month after federal (May 15)", "severity": "info",
     "condition": "always (informational)",
     "message": "Form 20C is due one month following the federal due date — for calendar-year 2025 corporations, May 15, 2026 (not April 15). The extension is file-only; the full tax is due by the original date.",
     "notes": "Filing note."},
]

F_SCENARIOS: list[dict] = [
    {"scenario_name": "AL20C-A — AL-only corp: 6.5% with FIT deduction", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"federal_taxable_income": 1000000, "federal_income_tax": 210000},
     "expected_outputs": {"fit_deduction": 210000, "al_taxable_income": 790000, "income_tax": 51350},
     "notes": "AL-only (ratio 100%): FIT deduction 210,000; AL taxable 1,000,000 - 210,000 = 790,000 x 6.5% = 51,350."},
    {"scenario_name": "AL20C-B — multistate: apportioned FIT deduction", "scenario_type": "edge", "sort_order": 2,
     "inputs": {"federal_taxable_income": 1000000, "federal_income_tax": 210000, "is_multistate": True, "sales_al": 250000, "sales_everywhere": 1000000},
     "expected_outputs": {"al_ratio": 0.25, "fit_deduction": 52500, "al_taxable_income": 197500, "income_tax": 12837.5},
     "notes": "Ratio 0.25: apportioned income 250,000; FIT deduction 210,000 × 0.25 = 52,500; AL taxable 197,500 x 6.5% = 12,837.50."},
    {"scenario_name": "AL20C-C — GILTI decouple", "scenario_type": "edge", "sort_order": 3,
     "inputs": {"federal_taxable_income": 500000, "gilti_951a_subtract": 100000, "sec250_addback": 50000, "federal_income_tax": 0},
     "expected_outputs": {"additions": 50000, "subtractions": 100000, "al_taxable_income": 450000, "income_tax": 29250},
     "notes": "GILTI: subtract 100,000 §951A, add back 50,000 §250: 500,000 + 50,000 - 100,000 = 450,000 x 6.5% = 29,250."},
    {"scenario_name": "AL20C-D — no depreciation add-back (AL conforms)", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"federal_taxable_income": 300000, "federal_income_tax": 0},
     "expected_outputs": {"additions": 0, "al_taxable_income": 300000, "income_tax": 19500},
     "notes": "AL conforms to §168(k)/§179 — no bonus/§179 add-back. 300,000 x 6.5% = 19,500."},
]


FORMS: list[dict] = [
    {
        "identity": {"form_number": "AL_FORM_20C", "form_title": "Alabama Form 20C — Corporation Income Tax Return (TY2025)",
                     "notes": "WO-12 (form 2 of 3, DECISIONS D-14). AL C-corp: 6.5% income tax (federal-TI + Schedule A add/subtract -> single-sales-factor apportionment -> AL income before FIT -> minus the APPORTIONED federal income tax deduction (L11a/Sch E, CONSTITUTIONAL per Amendment 662 — NOT repealed by Act 2021-1) -> AL NOL 15-yr -> 6.5%). AL CONFORMS to §168(k)/§179 (no depreciation add-back); the decouples are GILTI (§40-18-35.2) + §174 R&E (§40-18-62). Business Privilege Tax = separate Form CPT. Due May 15 (1 mo after federal)."},
        "facts": F_FACTS, "rules": F_RULES, "rule_links": F_RULE_LINKS,
        "lines": F_LINES, "diagnostics": F_DIAGNOSTICS, "scenarios": F_SCENARIOS,
    },
]

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-AL20C-INCOME", "title": "AL income tax = 6.5% of AL taxable income (after FIT deduction)", "assertion_type": "reconciliation",
     "entity_types": ["1120"], "status": "draft", "sort_order": 1,
     "description": "Federal TI + Sch A add − sub, apportioned by the single sales factor, minus the apportioned FIT deduction, minus AL NOL, times 6.5%.",
     "definition": {"rule": "R-AL20C-INCOME", "check": "income_tax = max(0, (fed_ti+add-sub)*ratio - fit - nol) * 0.065"}},
    {"assertion_id": "FA-AL20C-FIT", "title": "FIT deduction = federal income tax × AL ratio (constitutional)", "assertion_type": "reconciliation",
     "entity_types": ["1120"], "status": "draft", "sort_order": 2,
     "description": "The Amendment-662 federal income tax deduction (L11a/Schedule E) equals federal income tax apportioned by the AL income ratio.",
     "definition": {"rule": "R-AL20C-FIT", "check": "fit_deduction = federal_income_tax * al_ratio"}},
]


class Command(BaseCommand):
    help = "Load the AL Form 20C spec (AL C-corp income tax, TY2025). Refuses to seed until READY_TO_SEED=True (W4-W6)."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad Alabama Form 20C spec (Corporation Income Tax Return)\n"))
        self._load_topics()
        sources = self._load_sources()
        for spec in FORMS:
            form = self._upsert_form(spec["identity"])
            self._upsert_facts(form, spec["facts"])
            rules = self._upsert_rules(form, spec["rules"])
            self._upsert_authority_links(rules, sources, spec["rule_links"])
            self._upsert_lines(form, spec["lines"])
            self._upsert_diagnostics(form, spec["diagnostics"])
            self._upsert_tests(form, spec["scenarios"])
        self._upsert_form_links(sources)
        self._load_flow_assertions()
        self._report_totals()

    def _guard_against_hollow_seed(self):
        empty = []
        for spec in FORMS:
            fn = spec["identity"]["form_number"]
            for key in ("facts", "rules", "lines", "diagnostics", "scenarios", "rule_links"):
                if not spec[key]:
                    empty.append(f"{fn}.{key}")
        if not FLOW_ASSERTIONS:
            empty.append("FLOW_ASSERTIONS")
        if not READY_TO_SEED or empty:
            still_empty = "\n  ".join(f"- {n}" for n in empty) or "(all populated)"
            raise CommandError(
                "\nREFUSING TO SEED AL_FORM_20C: not cleared to seed.\n\n"
                "Gated until Ken reviews (W4 the constitutional FIT deduction; W5 AL conforms to\n"
                "§168(k)/§179 — no add-back; W6 the GILTI/§174 decouples) and flips the sentinel.\n\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True)\n\nEmpty:\n  {still_empty}\n"
            )

    def _load_topics(self):
        ct = 0
        for code, name in AUTHORITY_TOPICS:
            _, created = AuthorityTopic.objects.update_or_create(topic_code=code, defaults={"topic_name": name})
            ct += 1 if created else 0
        self.stdout.write(f"Topics: {ct} new ({len(AUTHORITY_TOPICS)} in batch)")

    def _load_sources(self) -> dict:
        sources: dict = {}
        for src_data in AUTHORITY_SOURCES:
            src_data = dict(src_data)
            excerpts_data = src_data.pop("excerpts", [])
            topic_codes = src_data.pop("topics", [])
            source, _ = AuthoritySource.objects.update_or_create(source_code=src_data["source_code"], defaults=src_data)
            sources[source.source_code] = source
            for exc in excerpts_data:
                exc = dict(exc)
                AuthorityExcerpt.objects.update_or_create(authority_source=source, excerpt_label=exc["excerpt_label"], defaults=exc)
            for tc in topic_codes:
                topic = AuthorityTopic.objects.filter(topic_code=tc).first()
                if topic:
                    AuthoritySourceTopic.objects.get_or_create(authority_source=source, authority_topic=topic)
        for code in EXISTING_SOURCES_TO_REFERENCE:
            src = AuthoritySource.objects.filter(source_code=code).first()
            if src:
                sources[code] = src
        self.stdout.write(f"Sources ready: {len(sources)}")
        return sources

    def _upsert_form(self, identity: dict) -> TaxForm:
        form, created = TaxForm.objects.update_or_create(
            form_number=identity["form_number"], jurisdiction=FORM_JURISDICTION, tax_year=FORM_TAX_YEAR, version=FORM_VERSION,
            defaults={"form_title": identity["form_title"], "entity_types": FORM_ENTITY_TYPES, "status": FORM_STATUS, "notes": identity["notes"]},
        )
        self.stdout.write(f"{'Created' if created else 'Updated'} {identity['form_number']}")
        return form

    def _upsert_facts(self, form, facts):
        for f in facts:
            f = dict(f)
            FormFact.objects.update_or_create(tax_form=form, fact_key=f.pop("fact_key"), defaults=f)
        self.stdout.write(f"  {len(facts)} facts")

    def _upsert_rules(self, form, rules_data) -> dict:
        created = {}
        for r in rules_data:
            r = dict(r)
            rule, _ = FormRule.objects.update_or_create(tax_form=form, rule_id=r.pop("rule_id"), defaults=r)
            created[rule.rule_id] = rule
        self.stdout.write(f"  {len(created)} rules")
        return created

    def _upsert_authority_links(self, rules, sources, rule_links):
        ct = 0
        for rule_id, source_code, level, note in rule_links:
            rule, source = rules.get(rule_id), sources.get(source_code)
            if rule and source:
                RuleAuthorityLink.objects.get_or_create(form_rule=rule, authority_source=source, defaults={"support_level": level, "relevance_note": note})
                ct += 1
        self.stdout.write(f"  {ct} authority links")

    def _upsert_lines(self, form, lines):
        for ln in lines:
            ln = dict(ln)
            FormLine.objects.update_or_create(tax_form=form, line_number=ln.pop("line_number"), defaults=ln)
        self.stdout.write(f"  {len(lines)} lines")

    def _upsert_diagnostics(self, form, diagnostics):
        for d in diagnostics:
            d = dict(d)
            FormDiagnostic.objects.update_or_create(tax_form=form, diagnostic_id=d.pop("diagnostic_id"), defaults=d)
        self.stdout.write(f"  {len(diagnostics)} diagnostics")

    def _upsert_tests(self, form, scenarios):
        for t in scenarios:
            t = dict(t)
            TestScenario.objects.update_or_create(tax_form=form, scenario_name=t.pop("scenario_name"), defaults=t)
        self.stdout.write(f"  {len(scenarios)} test scenarios")

    def _upsert_form_links(self, sources):
        for source_code, form_code, link_type in AUTHORITY_FORM_LINKS:
            source = sources.get(source_code) or AuthoritySource.objects.filter(source_code=source_code).first()
            if source:
                AuthorityFormLink.objects.get_or_create(authority_source=source, form_code=form_code, link_type=link_type, defaults={"note": f"{source_code} -> {form_code}"})

    def _load_flow_assertions(self):
        for a in FLOW_ASSERTIONS:
            a = dict(a)
            FlowAssertion.objects.update_or_create(assertion_id=a.pop("assertion_id"), defaults=a)
        self.stdout.write(f"  {len(FLOW_ASSERTIONS)} flow assertions")

    def _report_totals(self):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("AL Form 20C loaded.")
        self.stdout.write(f"  AL_FORM_20C: facts {len(F_FACTS)} / rules {len(F_RULES)} / lines {len(F_LINES)} / diag {len(F_DIAGNOSTICS)} / tests {len(F_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}")
        self.stdout.write("=" * 60)
