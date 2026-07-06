"""Load the Schedule H (Form 1040) spec — Household Employment Taxes (2025, Created 4/15/25).
WO-15, 2nd item in the SPINE S-16 federal-forms queue (after 8990). Greenfield.

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
Schedule H computes the household employer's federal employment taxes on cash wages paid to a
household employee: Social Security (12.4% combined) + Medicare (2.9% combined) + Additional
Medicare Tax withholding (0.9% over $200,000) + any voluntary federal income tax withheld (Part I),
plus FUTA (Part II — Section A single-state 0.6%, or Section B multi-state / credit-reduction), then
the total (Part III) flows to Schedule 2 (Form 1040) line 9. A filer not otherwise filing a 1040
signs Part IV and files Schedule H standalone.

The load-bearing 2025 constant is the CASH-WAGE TRIGGER = $2,800 (up from $2,700 in 2024 — the
training-data figure is stale). The year-sensitive item is the FUTA credit-reduction state list
(2025 = CA 1.2%, VI 4.5%; Fed. Reg. 2026-00342).

Greenfield: SCHEDULE_H not in the 111-form federal prod set at the 2026-07-05 gap-check.

═══════════════════════════════════════════════════════════════════════════
v1 SCOPE — LOCKED (Ken's Gate-1 walk 2026-07-05; DECISIONS D-17). See sch_h_source_brief.md.
═══════════════════════════════════════════════════════════════════════════
COMPUTES: (Q1) FUTA Section A (L16 = wages × 0.6%) + the year-keyed credit-reduction path (net = wages ×
(0.6% + reduction), CA 1.2% / VI 4.5% for 2025); direct-entry the multi-state L17 table / L19, L24 = L21 − L23.
(Q2) line A/B/C who-must-file routing + $2,800 / $1,000-per-quarter tests from qualifying wages; exclusions
(spouse/child<21/parent/under-18) = diagnostics. (Q3) one SCHEDULE_H form, entity_types ['1040']; total → Schedule
2 line 9; Part IV standalone + EIN = diagnostics. (Q4) full Part I (SS 12.4% / Medicare 2.9% / Add'l Med 0.9% over
$200k / FIT); diagnostic when L1 per-employee SS wages > $176,100 base.

requires_human_review WALK ITEMS (W1-W4):
W1. Part I — L2 = SS wages × 12.4%; L4 = Medicare wages × 2.9%; L6 = Add'l-Medicare wages × 0.9%; L8 = L2+L4+L6+L7.
    CONFIRM the combined (employer+employee) FICA rates and the 0.9% Additional Medicare over $200,000.
W2. FUTA — Section A L16 = FUTA wages × 0.6%; credit-reduction net = FUTA wages × (0.6% + reduction rate);
    Section B L24 = L21 (×6%) − L23 (smaller of L19 or L22 ×5.4%). CONFIRM the 0.6% / 6.0% / 5.4% and CA/VI rates.
W3. Gating — $2,800 (any one employee) triggers Part I; $1,000 any-quarter (all employees) triggers FUTA;
    exclusions (spouse/child<21/parent-with-exceptions/under-18-not-principal). CONFIRM the 2025 $2,800 trigger.
W4. Total → Schedule 2 line 9 (L26 = FUTA + FICA total; L25 = 0 if line C "Yes"). CONFIRM the Schedule 2 line 9 route.

CARRIED [UNVERIFIED]: none — all facts verbatim vs FINAL 2025 Schedule H + i-Sch-H + Pub 926 + Fed. Reg. 2026-00342.
Year-keyed constants ($2,800 / $176,100 / $200,000 / $7,000 / CA 1.2% / VI 4.5%) force a TY2026 re-verify.

SAFETY GUARD — READY_TO_SEED stays False until Ken approves the review walk (W1-W4).
FLIPPED 2026-07-05 — Ken APPROVED ("Approve — flip, seed, export"): W1 Part I FICA (SS 12.4% /
Medicare 2.9% / Add'l Medicare 0.9% over $200k / $176,100 SS-base diagnostic), W2 FUTA 0.6% /
Section B credit-reduction (CA 1.2% / VI 4.5%), W3 the $2,800 / $1,000 gating + exclusions,
W4 total -> Schedule 2 line 9. Validated (scratchpad/validate_sch_h.py, 31/0).
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

READY_TO_SEED = True

FORM_JURISDICTION = "federal"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1040"]

# ── Verified 2025 constants (sch_h_source_brief.md; Schedule H 2025 Created 4/15/25 / i1040sh / Pub 926 / Fed. Reg. 2026-00342) ──
SS_RATE = "0.124"                  # L2 — Social Security, combined employer+employee (i1040sh)
MEDICARE_RATE = "0.029"            # L4 — Medicare, combined (no wage cap)
ADDL_MEDICARE_RATE = "0.009"       # L6 — Additional Medicare Tax withholding (employee portion, over $200k)
FUTA_GROSS_RATE = "0.06"           # L21 — FUTA gross rate
FUTA_MAX_CREDIT_RATE = "0.054"     # L22 — maximum state-contribution credit
FUTA_NET_RATE = "0.006"            # L16 — net FUTA (Section A)
CASH_WAGE_THRESHOLD = 2800         # line A — SS/Medicare trigger, any one employee (2025; was $2,700 in 2024)
FUTA_QUARTER_THRESHOLD = 1000      # lines C/9 — FUTA trigger, any calendar quarter of 2024 or 2025
SS_WAGE_BASE = 176100              # 2025 Social Security wage base (per-employee cap on L1)
FUTA_WAGE_BASE = 7000              # per-employee FUTA wage base
ADDL_MEDICARE_THRESHOLD = 200000   # Additional Medicare Tax withholding threshold
# Year-keyed — the most-likely-to-change item. 2025 per Fed. Reg. 2026-00342 (2026-01-12).
CREDIT_REDUCTION_STATES_2025 = {"CA": "0.012", "VI": "0.045"}


def _fica(ss_wages, medicare_wages, addl_med_wages, fit_withheld) -> dict:
    """Part I: L2 = SS wages × 12.4%; L4 = Medicare wages × 2.9%; L6 = Add'l-Med wages × 0.9%; L8 total."""
    l2 = round(float(ss_wages) * float(SS_RATE), 2)
    l4 = round(float(medicare_wages) * float(MEDICARE_RATE), 2)
    l6 = round(float(addl_med_wages) * float(ADDL_MEDICARE_RATE), 2)
    l8 = round(l2 + l4 + l6 + float(fit_withheld), 2)
    return {"L2": l2, "L4": l4, "L6": l6, "L8": l8}


def _futa_section_a(futa_wages) -> float:
    """Part II Section A: L16 = total FUTA cash wages × 0.6% (single state, timely, all state-taxable)."""
    return round(float(futa_wages) * float(FUTA_NET_RATE), 2)


def _futa_section_b(futa_wages, section_b_credit, credit_reduction_rate) -> float:
    """Part II Section B: L21 = wages × 6.0%; L22 = wages × 5.4%; L23 = min(L19, L22) − credit reduction;
    L24 = L21 − L23. For a timely single credit-reduction state (section_b_credit >= L22) this reduces to
    wages × (0.6% + reduction rate) — e.g. CA 1.8%, VI 5.1%."""
    l21 = round(float(futa_wages) * float(FUTA_GROSS_RATE), 2)
    l22 = round(float(futa_wages) * float(FUTA_MAX_CREDIT_RATE), 2)
    reduction = round(float(futa_wages) * float(credit_reduction_rate), 2)
    l23 = round(min(float(section_b_credit), l22) - reduction, 2)
    if l23 < 0:
        l23 = 0.0
    return round(l21 - l23, 2)


def _total_hh_tax(fica_total, futa_tax, line_c_only) -> float:
    """Part III: L26 = FUTA (L16 or L24) + L25 (= L8, or 0 if line C 'Yes' so Part I was skipped)."""
    l25 = 0.0 if line_c_only else round(float(fica_total), 2)
    return round(float(futa_tax) + l25, 2)


def _must_file(max_one_employee_wages, withheld_fit, max_quarter_wages_all) -> bool:
    """Who must file: line A ($2,800 to any one employee) OR line B (withheld FIT) OR line C ($1,000/quarter)."""
    return (float(max_one_employee_wages) >= CASH_WAGE_THRESHOLD
            or bool(withheld_fit)
            or float(max_quarter_wages_all) >= FUTA_QUARTER_THRESHOLD)


AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("household_employment_tax", "Schedule H (Form 1040) household employment taxes: FICA (SS 12.4% + Medicare "
     "2.9% + Add'l Medicare 0.9%) on cash wages >= $2,800; FUTA (Section A 0.6% / Section B credit-reduction "
     "CA/VI); total to Schedule 2 line 9."),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_SCHH", "source_type": "federal_form", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Schedule H (Form 1040) 2025 — Household Employment Taxes",
        "citation": "Schedule H (Form 1040) 2025, Cat. No. 12187K, Created 4/15/25, Attach. Seq. No. 44",
        "issuer": "Internal Revenue Service", "official_url": "https://www.irs.gov/pub/irs-pdf/f1040sh.pdf",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.6, "topics": ["household_employment_tax"],
        "excerpts": [{
            "excerpt_label": "Line map — gating A/B/C + Part I FICA (2025 verbatim)",
            "excerpt_text": (
                "Line A: 'Did you pay any one household employee cash wages of $2,800 or more in 2025?' Line B: "
                "'Did you withhold federal income tax during 2025 for any household employee?' Line C: 'Did you "
                "pay total cash wages of $1,000 or more in any calendar quarter of 2024 or 2025 to all household "
                "employees?' Part I: L1 total cash wages subject to social security tax; L2 = L1 × 12.4% (0.124); "
                "L3 cash wages subject to Medicare tax; L4 = L3 × 2.9% (0.029); L5 cash wages subject to "
                "Additional Medicare Tax withholding; L6 = L5 × 0.9% (0.009); L7 federal income tax withheld, if "
                "any; L8 = add lines 2, 4, 6, and 7; L9 = the $1,000-any-quarter question (No: stop, put L8 on "
                "Schedule 2 line 9; Yes: go to line 10)."
            ),
            "summary_text": "Line A $2,800 trigger; L2 SS ×12.4%; L4 Medicare ×2.9%; L6 Add'l Med ×0.9%; L8 total = 2+4+6+7 -> Schedule 2 line 9.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "Part II FUTA (Section A / Section B) + Part III/IV (2025 verbatim)",
            "excerpt_text": (
                "Part II qualifiers: L10 contributions to only one state? (a credit-reduction-state employer "
                "checks No); L11 all 2025 state contributions paid by April 15, 2026?; L12 all FUTA-taxable wages "
                "also taxable for state unemployment? 'If Yes on all three, complete Section A; if No on any, "
                "complete Section B.' Section A: L15 total cash wages subject to FUTA; L16 = L15 × 0.6% (0.006). "
                "Section B: L17 per-state table cols (a)-(h) with (e)=(b)×0.054; L19 = col(g)+col(h); L20 FUTA "
                "wages; L21 = L20 × 6.0%; L22 = L20 × 5.4%; L23 = smaller of L19 or L22 (adjust for late/credit-"
                "reduction); L24 = L21 − L23. Part III: L25 = L8 (or -0- if line C Yes); L26 = L16 (or L24) + L25; "
                "L27 required to file 1040? Yes -> L26 to Schedule 2 line 9. Part IV: address + signature for a "
                "filer not filing Form 1040/1040-SR/1040-SS/1040-NR/1041."
            ),
            "summary_text": "Part II: all-Yes -> Section A L16 = FUTA wages ×0.6%; any-No -> Section B L24 = L21(×6%) − L23(min L19/L22 ×5.4%). L26 -> Schedule 2 line 9. Part IV standalone.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "IRS_2025_ISCHH", "source_type": "official_instructions", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "2025 Instructions for Schedule H (Form 1040)",
        "citation": "Instructions for Schedule H (Form 1040), 2025", "issuer": "Internal Revenue Service",
        "official_url": "https://www.irs.gov/instructions/i1040sh",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.5, "topics": ["household_employment_tax"],
        "excerpts": [{
            "excerpt_label": "What's New + household-employee scope + exclusions (i1040sh verbatim substance)",
            "excerpt_text": (
                "What's New (2025): the cash-wage threshold for social security and Medicare taxes is $2,800 (up "
                "from $2,700); the social security wage base is $176,100. A household employee is a worker you "
                "control (what work is done and how) doing household work in or around your home. Cash wages "
                "EXCLUDED from the $2,800 test: wages paid to your spouse, your child under age 21, your parent "
                "(exceptions apply), and an employee under age 18 at any time in 2025 whose principal occupation "
                "is not household work. You need an EIN (not your SSN) to report household employment taxes. If "
                "you are not required to file a 2025 tax return, file Schedule H by itself and complete Part IV. "
                "2025 FUTA credit reduction states: California and the U.S. Virgin Islands (use Worksheet 2)."
            ),
            "summary_text": "2025: $2,800 trigger / $176,100 SS base. Exclusions: spouse, child<21, parent, under-18-not-principal. EIN required. Standalone -> Part IV. CR states CA/VI.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "FR_FUTA_CR_2025", "source_type": "official_guidance", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Federal Register — FUTA Credit Reductions Applicable for 2025",
        "citation": "Notice of the FUTA Credit Reductions Applicable for 2025, 2026-00342 (published 2026-01-12)",
        "issuer": "U.S. Department of Labor", "official_url": "https://www.federalregister.gov/documents/2026/01/12/2026-00342/",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.4, "topics": ["household_employment_tax"],
        "excerpts": [{
            "excerpt_label": "2025 credit-reduction states + rates (verbatim)",
            "excerpt_text": (
                "For calendar year 2025 the FUTA credit reduction applies to: California (CA) — credit reduction "
                "1.2% (0.012), effective FUTA rate 1.8%; U.S. Virgin Islands (VI) — credit reduction 4.5% (0.045), "
                "effective FUTA rate 5.1%. An employer that paid state unemployment tax to a credit-reduction "
                "state must reduce its FUTA credit by the applicable amount (Schedule H: check No on line 10, use "
                "Section B and Worksheet 2)."
            ),
            "summary_text": "2025 FUTA credit reduction: CA 1.2% (eff. 1.8%), VI 4.5% (eff. 5.1%). Year-keyed — re-verify each season.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "IRC_3111_3301", "source_type": "statute", "source_rank": "controlling",
        "jurisdiction_code": "US", "title": "IRC §3101/§3111 (FICA), §3301 (FUTA), §3510 (Schedule H reporting)",
        "citation": "26 U.S.C. §3101, §3111, §3301, §3306, §3401, §3510", "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/3510",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.3, "topics": ["household_employment_tax"],
        "excerpts": [{
            "excerpt_label": "FICA/FUTA rates + household-employment reporting (verbatim substance)",
            "excerpt_text": (
                "§3101/§3111: the FICA tax is 6.2% (each of employer and employee) for old-age/survivors/"
                "disability (social security, on wages up to the contribution and benefit base) and 1.45% (each) "
                "for hospital insurance (Medicare, no cap); §3101(b)(2) adds the 0.9% Additional Medicare Tax on "
                "wages over the threshold ($200,000 for a single household employee's withholding). §3301: the "
                "FUTA tax is 6.0% of the first $7,000 of wages, with a credit up to 5.4% for state unemployment "
                "contributions (§3302), reduced for credit-reduction states. §3510: employment taxes on domestic "
                "service in a private home are paid via the employer's income tax return (Schedule H)."
            ),
            "summary_text": "§3101/§3111 FICA 6.2%+1.45% each + 0.9% Add'l Medicare; §3301 FUTA 6.0% on $7,000, 5.4% credit; §3510 Schedule H reporting.",
            "is_key_excerpt": True,
        }],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_SCHH", "SCHEDULE_H", "governs"), ("IRS_2025_ISCHH", "SCHEDULE_H", "governs"),
    ("FR_FUTA_CR_2025", "SCHEDULE_H", "governs"), ("IRC_3111_3301", "SCHEDULE_H", "governs"),
]


SCHH_FACTS: list[dict] = [
    # Gating (who must file)
    {"fact_key": "max_one_employee_cash_wages", "label": "Highest cash wages paid to any one household employee in 2025 (line A $2,800 test)", "data_type": "decimal", "required": False, "sort_order": 1,
     "notes": "Qualifying wages only — exclude spouse, your child under 21, your parent (exceptions), under-18-not-principal."},
    {"fact_key": "withheld_fit", "label": "Withheld federal income tax for a household employee in 2025? (line B)", "data_type": "boolean", "required": False, "sort_order": 2},
    {"fact_key": "max_quarter_wages_all", "label": "Highest total cash wages to ALL household employees in any calendar quarter of 2024/2025 (line C $1,000 test)", "data_type": "decimal", "required": False, "sort_order": 3},
    {"fact_key": "line_c_only", "label": "Line A 'No' but line C 'Yes' — FUTA only, Part I skipped (L25 = 0)", "data_type": "boolean", "required": False, "sort_order": 4},
    # Part I — FICA
    {"fact_key": "ss_wages", "label": "Total cash wages subject to Social Security tax (L1)", "data_type": "decimal", "required": False, "sort_order": 5,
     "notes": "Per employee, capped at the $176,100 (2025) SS wage base."},
    {"fact_key": "medicare_wages", "label": "Total cash wages subject to Medicare tax (L3)", "data_type": "decimal", "required": False, "sort_order": 6},
    {"fact_key": "addl_medicare_wages", "label": "Cash wages subject to Additional Medicare Tax withholding — over $200,000 (L5)", "data_type": "decimal", "required": False, "sort_order": 7},
    {"fact_key": "fit_withheld", "label": "Federal income tax withheld, if any — voluntary (L7)", "data_type": "decimal", "required": False, "sort_order": 8},
    # Part II — FUTA
    {"fact_key": "futa_wages", "label": "Total cash wages subject to FUTA tax (L15/L20; $7,000/employee base)", "data_type": "decimal", "required": False, "sort_order": 9},
    {"fact_key": "futa_single_state", "label": "Paid unemployment contributions to only ONE state, not a credit-reduction state, all timely, all state-taxable? (L10-12 all Yes -> Section A)", "data_type": "boolean", "required": False, "sort_order": 10},
    {"fact_key": "credit_reduction_state", "label": "State where FUTA-taxable wages were paid IS a 2025 credit-reduction state (CA/VI)? (drives Section B)", "data_type": "choice", "required": False, "sort_order": 11,
     "choices": ["none", "CA", "VI"]},
    {"fact_key": "section_b_credit", "label": "Section B allowable credit before reduction — L19 (col g + col h); direct-entry the multi-state table", "data_type": "decimal", "required": False, "sort_order": 12,
     "notes": "For a timely single credit-reduction state this equals the state contributions paid (>= L22); the per-state L17 experience-rate table is direct-entry."},
    {"fact_key": "state_contributions_paid", "label": "Contributions paid to state unemployment fund(s) (L14/col h)", "data_type": "decimal", "required": False, "sort_order": 13},
    # Filing
    {"fact_key": "required_to_file_1040", "label": "Required to file a 2025 Form 1040 (Yes -> attach; No -> Part IV standalone)? (L27)", "data_type": "boolean", "required": False, "sort_order": 14},
    {"fact_key": "has_ein", "label": "Household employer has an EIN (required to report)", "data_type": "boolean", "required": False, "sort_order": 15},
]

SCHH_RULES: list[dict] = [
    {"rule_id": "R-SCHH-FILE", "title": "Who must file Schedule H (line A/B/C)", "rule_type": "routing",
     "formula": "must_file = (max_one_employee_cash_wages >= 2800) or withheld_fit or (max_quarter_wages_all >= 1000)",
     "inputs": ["max_one_employee_cash_wages", "withheld_fit", "max_quarter_wages_all"], "outputs": ["must_file"], "sort_order": 1,
     "description": "W3. Must file Schedule H if line A ($2,800+ cash wages to any one household employee in 2025), line B (withheld federal income tax), or line C ($1,000+ cash wages in any calendar quarter of 2024/2025 to all household employees). If none, don't file."},
    {"rule_id": "R-SCHH-FICA", "title": "Part I — SS + Medicare + Add'l Medicare + FIT (L2/L4/L6/L8)", "rule_type": "calculation",
     "formula": "L2 = ss_wages*0.124 ; L4 = medicare_wages*0.029 ; L6 = addl_medicare_wages*0.009 ; L8 = L2+L4+L6+fit_withheld",
     "inputs": ["ss_wages", "medicare_wages", "addl_medicare_wages", "fit_withheld"], "outputs": ["L2", "L4", "L6", "fica_total"], "sort_order": 2,
     "description": "W1. Part I: L2 social security = L1 × 12.4% (combined employer+employee); L4 Medicare = L3 × 2.9%; L6 Additional Medicare = L5 × 0.9% (employee portion, wages over $200,000); L8 = L2 + L4 + L6 + L7 (FIT withheld)."},
    {"rule_id": "R-SCHH-FUTA-A", "title": "Part II Section A — FUTA single-state (L16)", "rule_type": "calculation",
     "formula": "L16 = futa_wages * 0.006",
     "inputs": ["futa_wages"], "outputs": ["futa_tax_a"], "sort_order": 3,
     "description": "W2. Section A (L10-12 all Yes: one state, timely, all state-taxable): L16 = total FUTA cash wages × 0.6% (net FUTA after the full 5.4% state credit)."},
    {"rule_id": "R-SCHH-FUTA-B", "title": "Part II Section B — credit-reduction / multi-state (L21/L22/L23/L24)", "rule_type": "calculation",
     "formula": "L21 = futa_wages*0.06 ; L22 = futa_wages*0.054 ; reduction = futa_wages*credit_reduction_rate ; L23 = max(0, min(section_b_credit, L22) - reduction) ; L24 = L21 - L23  # timely single CR state -> futa_wages*(0.006+rate): CA 1.8%, VI 5.1%",
     "inputs": ["futa_wages", "section_b_credit", "credit_reduction_state"], "outputs": ["futa_tax_b"], "sort_order": 4,
     "description": "W2. Section B (any L10-12 No): L21 = FUTA wages × 6.0%; L22 = × 5.4%; L23 = smaller of L19 (col g+h, direct-entry) or L22, reduced by the credit-reduction amount (FUTA wages × the CA 1.2% / VI 4.5% 2025 rate); L24 = L21 − L23. For a timely single credit-reduction state this is FUTA wages × (0.6% + reduction rate)."},
    {"rule_id": "R-SCHH-TOTAL", "title": "Part III — total household employment taxes -> Schedule 2 line 9 (L26)", "rule_type": "calculation",
     "formula": "L25 = 0 if line_c_only else fica_total ; futa_tax = L16 (Section A) or L24 (Section B) ; L26 = futa_tax + L25",
     "inputs": ["line_c_only"], "outputs": ["total_hh_tax"], "sort_order": 5,
     "description": "W4. Part III: L25 = L8 (Part I total), or -0- if line C 'Yes' (Part I skipped); L26 = L16 (or L24) + L25. If required to file Form 1040, L26 flows to Schedule 2 (Form 1040) line 9; otherwise complete Part IV and file standalone."},
]

SCHH_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-SCHH-FILE", "IRS_2025_SCHH", "primary", "Lines A/B/C"),
    ("R-SCHH-FILE", "IRS_2025_ISCHH", "secondary", "Who must file / $2,800 / $1,000"),
    ("R-SCHH-FICA", "IRS_2025_SCHH", "primary", "Part I L1-8"),
    ("R-SCHH-FICA", "IRC_3111_3301", "secondary", "§3101/§3111 FICA + 0.9% Add'l Medicare"),
    ("R-SCHH-FUTA-A", "IRS_2025_SCHH", "primary", "Part II Section A L15-16"),
    ("R-SCHH-FUTA-A", "IRC_3111_3301", "secondary", "§3301 FUTA 6.0%/5.4% credit"),
    ("R-SCHH-FUTA-B", "IRS_2025_SCHH", "primary", "Part II Section B L17-24"),
    ("R-SCHH-FUTA-B", "FR_FUTA_CR_2025", "primary", "2025 CA 1.2% / VI 4.5% credit reduction"),
    ("R-SCHH-TOTAL", "IRS_2025_SCHH", "primary", "Part III L25-27 -> Schedule 2 line 9"),
]

SCHH_LINES: list[dict] = [
    {"line_number": "L2", "description": "Social Security tax (L1 x 12.4%)", "line_type": "calculated", "source_rules": ["R-SCHH-FICA"], "sort_order": 1},
    {"line_number": "L4", "description": "Medicare tax (L3 x 2.9%)", "line_type": "calculated", "source_rules": ["R-SCHH-FICA"], "sort_order": 2},
    {"line_number": "L6", "description": "Additional Medicare Tax withholding (L5 x 0.9%)", "line_type": "calculated", "source_rules": ["R-SCHH-FICA"], "sort_order": 3},
    {"line_number": "L8", "description": "Total SS, Medicare, and federal income taxes (2+4+6+7)", "line_type": "subtotal", "source_rules": ["R-SCHH-FICA"], "sort_order": 4},
    {"line_number": "L16", "description": "FUTA tax — Section A (L15 x 0.6%)", "line_type": "calculated", "source_rules": ["R-SCHH-FUTA-A"], "sort_order": 5},
    {"line_number": "L24", "description": "FUTA tax — Section B (L21 - L23)", "line_type": "calculated", "source_rules": ["R-SCHH-FUTA-B"], "sort_order": 6},
    {"line_number": "L26", "description": "Total household employment taxes -> Schedule 2 line 9", "line_type": "subtotal", "source_rules": ["R-SCHH-TOTAL"], "sort_order": 7},
]

SCHH_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_SCHH_FILE", "title": "Household employer must file Schedule H", "severity": "info",
     "condition": "max_one_employee_cash_wages >= 2800 or withheld_fit or max_quarter_wages_all >= 1000",
     "message": "You must file Schedule H if in 2025 you paid any one household employee cash wages of $2,800 or more, withheld federal income tax for a household employee, or paid total cash wages of $1,000 or more in any calendar quarter of 2024 or 2025 to all household employees. Schedule H attaches to Form 1040 (total to Schedule 2, line 9).",
     "notes": "W3."},
    {"diagnostic_id": "D_SCHH_EXCL", "title": "Cash wages excluded from the $2,800 test", "severity": "info",
     "condition": "max_one_employee_cash_wages > 0",
     "message": "Do NOT count wages paid to: your spouse; your child under age 21; your parent (unless the parent cares for your child under 18 or a disabled dependent while you are widowed/divorced or your spouse is disabled); or an employee under age 18 at any time in 2025 whose principal occupation is not household work (e.g., a student). Enter only qualifying household-employee cash wages.",
     "notes": "W3. The relationship/age determination needs data the spec cannot read — apply per employee."},
    {"diagnostic_id": "D_SCHH_SSBASE", "title": "Line-1 SS wages exceed the $176,100 wage base", "severity": "warning",
     "condition": "ss_wages > 176100",
     "message": "Cash wages subject to Social Security tax (line 1) are capped at the 2025 Social Security wage base of $176,100 PER EMPLOYEE. If line 1 exceeds $176,100 for a single employee, only $176,100 is subject to the 12.4% social security tax (Medicare on line 3 has no cap). Verify line 1 is the per-employee-capped total.",
     "notes": "W1. Year-keyed 2025 = $176,100."},
    {"diagnostic_id": "D_SCHH_ADDLMED", "title": "Additional Medicare Tax withholding (0.9% over $200,000)", "severity": "info",
     "condition": "addl_medicare_wages > 0",
     "message": "A household employer must withhold the 0.9% Additional Medicare Tax on cash wages paid to an employee in excess of $200,000 in 2025 (line 5 = the excess over $200,000; line 6 = line 5 × 0.9%). There is no employer match for the Additional Medicare Tax.",
     "notes": "W1."},
    {"diagnostic_id": "D_SCHH_CREDREDUX", "title": "2025 FUTA credit-reduction state — use Section B", "severity": "warning",
     "condition": "credit_reduction_state != none",
     "message": "For 2025, California (credit reduction 1.2%, effective FUTA 1.8%) and the U.S. Virgin Islands (4.5%, effective 5.1%) are FUTA credit-reduction states (Fed. Reg. 2026-00342). If you paid state unemployment tax there, check 'No' on line 10, complete Part II Section B, and use Worksheet 2: net FUTA = FUTA wages × (0.6% + the credit-reduction rate). This list changes annually — re-verify each season.",
     "notes": "W2. Year-keyed."},
    {"diagnostic_id": "D_SCHH_STANDALONE", "title": "Not filing Form 1040 — complete Part IV and file standalone", "severity": "info",
     "condition": "not required_to_file_1040",
     "message": "If you are not required to file a 2025 Form 1040/1040-SR/1040-SS/1040-NR/1041, do NOT carry the total to Schedule 2. Instead complete Part IV (address and signature) and file Schedule H by itself, and pay the household employment taxes with it.",
     "notes": "W4."},
    {"diagnostic_id": "D_SCHH_EIN", "title": "EIN required to report household employment taxes", "severity": "warning",
     "condition": "not has_ein",
     "message": "A household employer must have an Employer Identification Number (EIN) — not a Social Security number — to report household employment taxes on Schedule H. Apply for an EIN (Form SS-4 or online) before filing.",
     "notes": "W3."},
]

SCHH_SCENARIOS: list[dict] = [
    {"scenario_name": "SCHH-A — nanny, single state (Part I + Section A)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"max_one_employee_cash_wages": 25000, "ss_wages": 25000, "medicare_wages": 25000, "futa_wages": 7000, "futa_single_state": True},
     "expected_outputs": {"L2": 3100.0, "L4": 725.0, "L8": 3825.0, "futa_tax_a": 42.0, "total_hh_tax": 3867.0},
     "notes": "L2 = 25,000 × 12.4% = 3,100; L4 = 25,000 × 2.9% = 725; L8 = 3,825; Section A FUTA = 7,000 × 0.6% = 42; total = 3,867 -> Schedule 2 line 9."},
    {"scenario_name": "SCHH-B — Additional Medicare Tax over $200,000", "scenario_type": "edge", "sort_order": 2,
     "inputs": {"max_one_employee_cash_wages": 250000, "ss_wages": 176100, "medicare_wages": 250000, "addl_medicare_wages": 50000, "futa_wages": 7000, "futa_single_state": True},
     "expected_outputs": {"L2": 21836.4, "L4": 7250.0, "L6": 450.0, "futa_tax_a": 42.0},
     "notes": "SS capped at 176,100 × 12.4% = 21,836.40; Medicare 250,000 × 2.9% = 7,250; Add'l Medicare 50,000 (over 200k) × 0.9% = 450; D_SCHH_SSBASE + D_SCHH_ADDLMED fire."},
    {"scenario_name": "SCHH-C — California credit-reduction state (Section B)", "scenario_type": "edge", "sort_order": 3,
     "inputs": {"max_one_employee_cash_wages": 30000, "ss_wages": 30000, "medicare_wages": 30000, "futa_wages": 7000, "credit_reduction_state": "CA", "section_b_credit": 378, "state_contributions_paid": 378},
     "expected_outputs": {"futa_tax_b": 126.0, "diagnostic": "D_SCHH_CREDREDUX"},
     "notes": "Timely single CR state: net FUTA = 7,000 × (0.6% + 1.2%) = 7,000 × 1.8% = 126. (L21 = 420; L22 = 378; reduction = 84; L23 = 378 − 84 = 294; L24 = 420 − 294 = 126.)"},
    {"scenario_name": "SCHH-D — below all thresholds, don't file", "scenario_type": "failure", "sort_order": 4,
     "inputs": {"max_one_employee_cash_wages": 2000, "withheld_fit": False, "max_quarter_wages_all": 800},
     "expected_outputs": {"must_file": False},
     "notes": "$2,000 < $2,800 (line A), no FIT (line B), $800 < $1,000/quarter (line C) -> Stop, don't file Schedule H."},
    {"scenario_name": "SCHH-E — FUTA only (line C Yes, Part I skipped)", "scenario_type": "edge", "sort_order": 5,
     "inputs": {"max_one_employee_cash_wages": 2000, "max_quarter_wages_all": 1500, "line_c_only": True, "futa_wages": 4000, "futa_single_state": True},
     "expected_outputs": {"futa_tax_a": 24.0, "total_hh_tax": 24.0},
     "notes": "No one employee hit $2,800 (Part I skipped, L25 = 0) but $1,500 in a quarter >= $1,000 -> FUTA only: 4,000 × 0.6% = 24; total = 24."},
    {"scenario_name": "SCHH-F — standalone filer, not filing 1040 (Part IV)", "scenario_type": "edge", "sort_order": 6,
     "inputs": {"max_one_employee_cash_wages": 12000, "ss_wages": 12000, "medicare_wages": 12000, "futa_wages": 7000, "futa_single_state": True, "required_to_file_1040": False, "has_ein": False},
     "expected_outputs": {"L8": 1836.0, "futa_tax_a": 42.0, "total_hh_tax": 1878.0, "diagnostic": "D_SCHH_STANDALONE"},
     "notes": "L2 = 1,488 + L4 = 348 -> L8 = 1,836; FUTA 42; total 1,878. Not filing 1040 -> Part IV standalone (D_SCHH_STANDALONE) + EIN required (D_SCHH_EIN)."},
]

FORMS: list[dict] = [
    {
        "identity": {"form_number": "SCHEDULE_H", "form_title": "Schedule H (Form 1040) — Household Employment Taxes (2025)",
                     "notes": "WO-15 (SPINE S-16, 2nd; DECISIONS D-17). Part I: SS (L2 = L1 × 12.4%) + Medicare (L4 = L3 × 2.9%) + Additional Medicare (L6 = L5 × 0.9% over $200k) + FIT withheld (L7) -> L8. Part II FUTA: Section A (L16 = FUTA wages × 0.6%) or Section B credit-reduction (net = FUTA wages × (0.6% + rate); 2025 CA 1.2% / VI 4.5%) — multi-state L17 table direct-entry. Part III: L26 = FUTA + L8 (L25 = 0 if line C Yes) -> Schedule 2 line 9. Who-must-file A/B/C: $2,800 any one employee / withheld FIT / $1,000 any quarter. Exclusions (spouse/child<21/parent/under-18) + Part IV standalone + EIN = diagnostics. Load-bearing: $2,800 trigger (was $2,700 in 2024). Year-keyed constants force TY2026 re-verify."},
        "facts": SCHH_FACTS, "rules": SCHH_RULES, "rule_links": SCHH_RULE_LINKS,
        "lines": SCHH_LINES, "diagnostics": SCHH_DIAGNOSTICS, "scenarios": SCHH_SCENARIOS,
    },
]

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-SCHH-S2", "title": "Total household employment taxes flow to Schedule 2 line 9", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "draft", "sort_order": 1,
     "description": "Schedule H line 26 (FUTA + FICA total) is carried to Schedule 2 (Form 1040) line 9 when the taxpayer files Form 1040.",
     "definition": {"rule": "R-SCHH-TOTAL", "check": "total_hh_tax = futa_tax + (0 if line_c_only else fica_total) -> Schedule 2 line 9"}},
    {"assertion_id": "FA-SCHH-FICA", "title": "FICA at combined rates (SS 12.4% + Medicare 2.9% + Add'l 0.9%)", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "draft", "sort_order": 2,
     "description": "Part I FICA = SS wages × 12.4% + Medicare wages × 2.9% + Add'l-Medicare wages × 0.9% + FIT withheld; the household employer owes both employer and employee halves of SS/Medicare.",
     "definition": {"rule": "R-SCHH-FICA", "check": "L8 = ss*0.124 + med*0.029 + addl*0.009 + fit"}},
    {"assertion_id": "FA-SCHH-FUTA", "title": "FUTA = 0.6% (Section A) or credit-reduction net (Section B)", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "draft", "sort_order": 3,
     "description": "Section A FUTA = FUTA wages × 0.6%; a timely single credit-reduction state (2025 CA/VI) = FUTA wages × (0.6% + credit-reduction rate) via L24 = L21 − L23.",
     "definition": {"rule": "R-SCHH-FUTA-B", "check": "credit-reduction net = futa_wages * (0.006 + rate)"}},
]


class Command(BaseCommand):
    help = "Load the Schedule H (Form 1040) spec (Household Employment Taxes, 2025). Refuses to seed until READY_TO_SEED=True (W1-W4)."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad Schedule H (Form 1040) spec (Household Employment Taxes)\n"))
        self._load_topics()
        sources = self._load_sources()
        for spec in FORMS:
            form = self._upsert_form(spec["identity"])
            self._upsert_facts(form, spec["facts"])
            rules = self._upsert_rules(form, spec["rules"])
            self._upsert_links(rules, sources, spec["rule_links"])
            self._upsert_lines(form, spec["lines"])
            self._upsert_diag(form, spec["diagnostics"])
            self._upsert_tests(form, spec["scenarios"])
        self._upsert_form_links(sources)
        self._load_fa()
        self._report()

    def _guard(self):
        empty = []
        for spec in FORMS:
            fn = spec["identity"]["form_number"]
            for key in ("facts", "rules", "lines", "diagnostics", "scenarios", "rule_links"):
                if not spec[key]:
                    empty.append(f"{fn}.{key}")
        if not FLOW_ASSERTIONS:
            empty.append("FLOW_ASSERTIONS")
        if not READY_TO_SEED or empty:
            still = "\n  ".join(f"- {n}" for n in empty) or "(all populated)"
            raise CommandError(
                "\nREFUSING TO SEED SCHEDULE H: not cleared.\n\n"
                "Gated until Ken reviews (W1 Part I FICA rates; W2 FUTA 0.6%/6%/5.4% + CA/VI credit\n"
                "reduction; W3 $2,800/$1,000 gating + exclusions; W4 total -> Schedule 2 line 9) and\n"
                f"flips the sentinel.\n\nREADY_TO_SEED = {READY_TO_SEED}\n\nEmpty:\n  {still}\n"
            )

    def _load_topics(self):
        ct = 0
        for code, name in AUTHORITY_TOPICS:
            _, created = AuthorityTopic.objects.update_or_create(topic_code=code, defaults={"topic_name": name})
            ct += 1 if created else 0
        self.stdout.write(f"Topics: {ct} new")

    def _load_sources(self) -> dict:
        sources: dict = {}
        for sd in AUTHORITY_SOURCES:
            sd = dict(sd)
            exc = sd.pop("excerpts", [])
            tcs = sd.pop("topics", [])
            src, _ = AuthoritySource.objects.update_or_create(source_code=sd["source_code"], defaults=sd)
            sources[src.source_code] = src
            for e in exc:
                e = dict(e)
                AuthorityExcerpt.objects.update_or_create(authority_source=src, excerpt_label=e["excerpt_label"], defaults=e)
            for tc in tcs:
                t = AuthorityTopic.objects.filter(topic_code=tc).first()
                if t:
                    AuthoritySourceTopic.objects.get_or_create(authority_source=src, authority_topic=t)
        self.stdout.write(f"Sources ready: {len(sources)}")
        return sources

    def _upsert_form(self, identity: dict) -> TaxForm:
        form, created = TaxForm.objects.update_or_create(
            form_number=identity["form_number"], jurisdiction=FORM_JURISDICTION, tax_year=FORM_TAX_YEAR, version=FORM_VERSION,
            defaults={"form_title": identity["form_title"], "entity_types": FORM_ENTITY_TYPES, "status": FORM_STATUS, "notes": identity["notes"]},
        )
        self.stdout.write(f"{'Created' if created else 'Updated'} {identity['form_number']} {FORM_ENTITY_TYPES}")
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

    def _upsert_links(self, rules, sources, rule_links):
        ct = 0
        for rid, sc, lvl, note in rule_links:
            rule, src = rules.get(rid), sources.get(sc)
            if rule and src:
                RuleAuthorityLink.objects.get_or_create(form_rule=rule, authority_source=src, defaults={"support_level": lvl, "relevance_note": note})
                ct += 1
        self.stdout.write(f"  {ct} authority links")

    def _upsert_lines(self, form, lines):
        for ln in lines:
            ln = dict(ln)
            FormLine.objects.update_or_create(tax_form=form, line_number=ln.pop("line_number"), defaults=ln)
        self.stdout.write(f"  {len(lines)} lines")

    def _upsert_diag(self, form, diags):
        for d in diags:
            d = dict(d)
            FormDiagnostic.objects.update_or_create(tax_form=form, diagnostic_id=d.pop("diagnostic_id"), defaults=d)
        self.stdout.write(f"  {len(diags)} diagnostics")

    def _upsert_tests(self, form, scenarios):
        for t in scenarios:
            t = dict(t)
            TestScenario.objects.update_or_create(tax_form=form, scenario_name=t.pop("scenario_name"), defaults=t)
        self.stdout.write(f"  {len(scenarios)} test scenarios")

    def _upsert_form_links(self, sources):
        for sc, fc, lt in AUTHORITY_FORM_LINKS:
            src = sources.get(sc) or AuthoritySource.objects.filter(source_code=sc).first()
            if src:
                AuthorityFormLink.objects.get_or_create(authority_source=src, form_code=fc, link_type=lt, defaults={"note": f"{sc} -> {fc}"})

    def _load_fa(self):
        for a in FLOW_ASSERTIONS:
            a = dict(a)
            FlowAssertion.objects.update_or_create(assertion_id=a.pop("assertion_id"), defaults=a)
        self.stdout.write(f"  {len(FLOW_ASSERTIONS)} flow assertions")

    def _report(self):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("Schedule H loaded.")
        self.stdout.write(f"  SCHEDULE_H: facts {len(SCHH_FACTS)} / rules {len(SCHH_RULES)} / lines {len(SCHH_LINES)} / diag {len(SCHH_DIAGNOSTICS)} / tests {len(SCHH_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}")
        self.stdout.write("=" * 60)
