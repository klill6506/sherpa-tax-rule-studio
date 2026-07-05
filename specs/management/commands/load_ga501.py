"""Load the GA Form 501 spec — Georgia Fiduciary Income Tax Return (TY2025).
Leg (c) of the 1041 module (S-11 / WO-09) — the state fiduciary companion to the federal 1041.

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
GA Form 501 is the Georgia return for resident estates and trusts. It starts from
the FEDERAL 1041 "Adjusted Total Income" (federal 1041 line 17, PRE income-distribution
deduction), applies Georgia additions/subtractions (Schedule 2), removes the
beneficiaries' share of income (Schedule 3 → Form 501 line 4) so the fiduciary is taxed
only on income RETAINED at the trust/estate level, subtracts the GA exemption, and taxes
the result at the flat 5.19% (line 8).

Key: GA subtracts the beneficiary share SEPARATELY at line 4 — it does NOT re-derive DNI
and does NOT use the federal income distribution deduction. Do not double-count the IDD.

Attaches to the federal 1041 (GA requires the federal return + schedules attached). There
is NO separate Georgia fiduciary K-1 — beneficiary detail lives in Schedule 3; credit
allocation in Schedule 6; the federal K-1 is attached.

Greenfield: lookup/GA501/ → 404 at the 2026-07-05 gap-check.

═══════════════════════════════════════════════════════════════════════════
v1 SCOPE — RESIDENT-ONLY (DECISIONS D-10). See f1041_source_brief.md §GA-501.
═══════════════════════════════════════════════════════════════════════════
COMPUTES (v1):
  • The full-year RESIDENT Form 501: L1 federal ATI → L2 Sch 2 net adjustment → L3 →
    L4 beneficiaries' share (Sch 3) → L5 → L6 exemption ($1,350 trust / $2,700 estate) →
    L7a/L7c GA taxable → L8 tax (× 5.19%) → L9 credits → L10 → L11b withholding credit.
  • Schedule 2 additions (non-GA muni interest, GA-decoupled items) / subtractions
    (US-obligation interest) as a net adjustment.
RED-DEFERS (loud diagnostic, no silent gap) — per D-10:
  • Schedule 4 NONRESIDENT / part-year source allocation — D_GA501_NR.
  • The §168(k) / §179 GA-nonconformity depreciation add-back (no dedicated Form 501
    line; rides generic Sch 2 "Other" under §48-7-27) — D_GA501_DEPR.
  • GA NOL (Schedule 7) — D_GA501_NOL (direct-entry line exists).
STRUCTURE + FLAG:
  • §48-7-129 4% nonresident withholding is OWNER-level (trust as a NR member of a PTE, or
    a GA-realty sale G2-RP) — it does NOT reach trust→beneficiary distributions; it surfaces
    on Form 501 line 11b as a CREDIT — D_GA501_NRW.
  • Grantor trust → GA follows federal grantor treatment — D_GA501_GRANTOR.
  • PTET is N/A at the fiduciary level (HB 149 is a PTE-level election) — D_GA501_NOPTET.

═══════════════════════════════════════════════════════════════════════════
requires_human_review WALK ITEMS (W1-W3)
═══════════════════════════════════════════════════════════════════════════
W1. RATE 5.19% (0.0519) + exemptions Trust $1,350 / Estate $2,700 — FINAL 2025 Form 501
    (Rev. 07/09/25) + booklet. Year-keyed (2026 → 4.99%). CONFIRM.
W2. FEDERAL BASE = 1041 Adjusted Total Income (line 17), PRE-IDD; GA removes the
    beneficiary share at line 4 (Schedule 3), NOT via the federal distribution deduction.
    CONFIRM the no-double-count modeling.
W3. CONFORMITY = IRC on/before Jan 1, 2025; OBBBA NOT adopted (booklet "What's New"). The
    depreciation add-back is RED-deferred to generic Sch 2 Other (§48-7-27) for v1. Re-verify
    the 2025 GA conformity bill.

═══════════════════════════════════════════════════════════════════════════
SAFETY GUARD — READY_TO_SEED stays False until Ken approves the review walk (W1-W3).
═══════════════════════════════════════════════════════════════════════════
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from sources.models import (
    AuthorityExcerpt,
    AuthorityFormLink,
    AuthoritySource,
    AuthoritySourceTopic,
    AuthorityTopic,
    RuleAuthorityLink,
)
from specs.models import (
    FlowAssertion,
    FormDiagnostic,
    FormFact,
    FormLine,
    FormRule,
    TaxForm,
    TestScenario,
)

# ═══════════════════════════════════════════════════════════════════════════
# SAFETY GUARD — flip ONLY after Ken's in-session review walk (W1-W3 above).
#
# FLIPPED 2026-07-05 — Ken APPROVED the review walk in-session ("Approve — flip,
# seed, export (completes S-11)"): W1 the 5.19% rate + $1,350/$2,700 exemptions,
# W2 the federal-ATI base + beneficiary-share-at-L4 no-double-count, W3 the Jan 1
# 2025 conformity (OBBBA not adopted) — all blessed. Validated on throwaway SQLite
# (scratchpad/validate_ga501.py, 16 pass / 0 fail; seeds ga700 first for GA_OCGA_48_7).
# ═══════════════════════════════════════════════════════════════════════════
READY_TO_SEED = True


FORM_JURISDICTION = "GA"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1041"]


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS (year-keyed; cited in f1041_source_brief.md; never memory)
# ═══════════════════════════════════════════════════════════════════════════

GA_FLAT_RATE: dict[int, str] = {2025: "0.0519"}          # W1 — TY2026 steps to 4.99%
GA_EXEMPTION_TRUST: dict[int, int] = {2025: 1350}         # Form 501 L6a
GA_EXEMPTION_ESTATE: dict[int, int] = {2025: 2700}        # Form 501 L6b
GA_NRW_RATE: dict[int, str] = {2025: "0.04"}             # §48-7-129 (owner-level)
GA_CONFORMITY_DATE = "2025-01-01"                         # W3 — IRC on/before Jan 1 2025; OBBBA NOT adopted


def _rate(year: int) -> str:
    return GA_FLAT_RATE.get(year, GA_FLAT_RATE[2025])


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY TOPICS / SOURCES
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("ga_fiduciary_501", "Georgia Form 501 fiduciary tax: federal 1041 Adjusted Total Income start, "
     "Sch 2 GA add/subtract, beneficiary-share removal at L4, $1,350/$2,700 exemptions, flat 5.19%, "
     "§48-7-129 owner-level withholding; OBBBA not adopted (conformity Jan 1 2025)."),
]

# Reuse the GA statute source the GA-700 loader already seeded.
EXISTING_SOURCES_TO_REFERENCE: list[str] = ["GA_OCGA_48_7"]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "GA_2025_FORM_501",
        "source_type": "state_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "GA",
        "title": "2025 Georgia Form 501 — Fiduciary Income Tax Return",
        "citation": "Georgia Form 501 (2025), Rev. 07/09/25 (Approved web version)",
        "issuer": "Georgia Department of Revenue",
        "official_url": "https://apps.dor.ga.gov/FillableForms/webpdf/examples/2025GA501.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["ga_fiduciary_501"],
        "excerpts": [
            {
                "excerpt_label": "Form 501 Schedule 1 flow + rate + exemptions (2025 verbatim)",
                "excerpt_text": (
                    "L1 Income of fiduciary (Adjusted total income from attached Form 1041); L2 Net "
                    "adjustment (Schedule 2); L3 Total; L4 Beneficiaries' Share of Income (total of Schedule "
                    "3); L5 Balance (L3 − L4); L6 Exemption (6a Trust $1,350 / 6b Estate $2,700); L7a Georgia "
                    "taxable income before NOL (L5 − L6); L7b Georgia NOL; L7c Georgia net taxable income; L8 "
                    "'Multiply the amount on Line 7c by 5.19%. Round to the nearest dollar.'; L9 Credits (9a "
                    "other state(s) tax credit / 9b Schedule 5 nonrefundable); L10 Tax less credits; L11b Tax "
                    "Withheld (1099, G2-A, G2-LP and/or G2-RP). THE FIDUCIARY MUST ATTACH A COPY OF ITS "
                    "FEDERAL RETURN AND SUPPORTING SCHEDULES. Page-1 boxes: residency (Full-Year / Part Year "
                    "/ Nonresident); Grantor Trust; Qualified Funeral Trust; Bankruptcy Estate."
                ),
                "summary_text": "Form 501 Sch 1: L1 federal ATI → L2 Sch 2 net adj → L4 beneficiary share (Sch 3) → L6 exemption ($1,350 trust / $2,700 estate) → L8 tax (× 5.19%) → L9 credits → L11b withholding.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule 2 additions/subtractions (2025 verbatim)",
                "excerpt_text": (
                    "Schedule 2 ADDITIONS: (1) Municipal bond interest — Other states; (2) Income tax "
                    "deduction other than Georgia; (3) Expense allocable to exempt income; (4) NOL carryover "
                    "deducted on the Federal return; (5) Other. SUBTRACTIONS: (7) Interest — U.S. Government "
                    "Obligations (reduced by direct/indirect interest expense; FNMA/GNMA/FHLMC/repos are "
                    "taxable); (8) Income tax refund other than Georgia; (9) Reserved; (10) Other; (12) Net "
                    "adjustment → Schedule 1 Line 2. Georgia taxable income of a fiduciary is its Federal "
                    "adjusted total income with the O.C.G.A. §48-7-27 adjustments."
                ),
                "summary_text": "Sch 2 additions: non-GA muni interest, non-GA income tax, exempt-income expense, fed NOL, other. Subtractions: US-obligation interest, non-GA refund, other. Net → Sch 1 L2.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "GA_2025_501_INSTR",
        "source_type": "state_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "GA",
        "title": "2025 Georgia 501 and 501X Fiduciary Income Tax Forms and Instructions Booklet",
        "citation": "Georgia 501/501X Fiduciary Instructions (2025)",
        "issuer": "Georgia Department of Revenue",
        "official_url": "https://dor.georgia.gov/501-and-501x-fiduciary-income-tax-instruction-booklet",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["ga_fiduciary_501"],
        "excerpts": [
            {
                "excerpt_label": "Rate 5.19%, conformity Jan 1 2025 (OBBBA not adopted), NR withholding (booklet What's New / pp.7-12)",
                "excerpt_text": (
                    "'2025 Income Tax Changes: Effective January 1, 2025, the income tax rate is 5.19%.' "
                    "'Georgia conforms to the Internal Revenue Code, as amended, provided for in Federal law "
                    "enacted on or before January 1, 2025. Georgia has not adopted the Federal tax law "
                    "changes in The Act of 2025 (also known as the One Big Beautiful Bill Act) due to it "
                    "being signed on July 4, 2025.' Line 1: 'Enter Adjusted total income (gross income less "
                    "the itemized deductions shown on the Federal Form 1041).' Nonresident/part-year: leave "
                    "Sch 1 L1-6 blank and complete Schedule 4. §48-7-129 withholding on nonresident MEMBERS "
                    "of a pass-through entity (4%, <$1,000 exempt) is claimed on Line 11b when the trust is a "
                    "member; it does not apply to trust→beneficiary distributions. Bankruptcy estate files "
                    "if gross income ≥ $13,850. No PTET at the fiduciary level; grantor trusts follow the "
                    "federal grantor treatment; no separate Georgia fiduciary K-1 (Schedule 3 lists "
                    "beneficiaries; Schedule 6 allocates credits; the federal return/K-1 is attached)."
                ),
                "summary_text": "5.19% rate; conformity Jan 1 2025 (OBBBA not adopted); base = federal ATI; §48-7-129 4% withholding is owner-level (Line 11b credit); no fiduciary PTET / no GA K-1.",
                "is_key_excerpt": True,
            },
        ],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("GA_2025_FORM_501", "GA501", "governs"),
    ("GA_2025_501_INSTR", "GA501", "governs"),
    ("GA_OCGA_48_7", "GA501", "governs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM — GA Form 501
# ═══════════════════════════════════════════════════════════════════════════

GA501_FACTS: list[dict] = [
    {"fact_key": "fiduciary_type", "label": "Fiduciary type (drives the exemption)", "data_type": "choice", "required": True, "sort_order": 1,
     "choices": ["trust", "estate"], "notes": "W1. Trust exemption $1,350 (L6a); estate $2,700 (L6b)."},
    {"fact_key": "residency", "label": "Residency (Form 501 page 1)", "data_type": "choice", "required": True, "sort_order": 2,
     "choices": ["full_year_resident", "part_year", "nonresident"],
     "notes": "D-10. v1 computes full_year_resident; part_year/nonresident (Schedule 4) RED-deferred — D_GA501_NR."},
    {"fact_key": "is_grantor_trust", "label": "Grantor trust (page-1 box)?", "data_type": "boolean", "required": False, "sort_order": 3},
    {"fact_key": "is_bankruptcy_estate", "label": "Bankruptcy estate (page-1 box)? (files if gross income ≥ $13,850)", "data_type": "boolean", "required": False, "sort_order": 4},
    # L1 federal base
    {"fact_key": "fed_adjusted_total_income", "label": "Federal 1041 Adjusted Total Income — Form 1041 line 17 (Form 501 L1)", "data_type": "decimal", "required": True, "sort_order": 10,
     "notes": "W2. PRE income-distribution deduction. GA removes the beneficiary share separately at L4."},
    # Schedule 2 additions
    {"fact_key": "ga_add_muni_interest", "label": "Municipal bond interest — other states (Sch 2 add L1)", "data_type": "decimal", "required": False, "sort_order": 20},
    {"fact_key": "ga_add_other_state_tax", "label": "Income tax deduction other than Georgia (Sch 2 add L2)", "data_type": "decimal", "required": False, "sort_order": 21},
    {"fact_key": "ga_add_exempt_expense", "label": "Expense allocable to exempt income (Sch 2 add L3)", "data_type": "decimal", "required": False, "sort_order": 22},
    {"fact_key": "ga_add_fed_nol", "label": "NOL carryover deducted on the federal return (Sch 2 add L4)", "data_type": "decimal", "required": False, "sort_order": 23},
    {"fact_key": "ga_add_other", "label": "Other GA additions incl. §168(k)/§179 add-back — RED-defer (Sch 2 add L5)", "data_type": "decimal", "required": False, "sort_order": 24,
     "notes": "D-10. No dedicated depreciation line; the §168(k)/§179 conformity add-back rides here (§48-7-27) — D_GA501_DEPR."},
    # Schedule 2 subtractions
    {"fact_key": "ga_sub_us_obligations", "label": "Interest on U.S. Government obligations (Sch 2 sub L7)", "data_type": "decimal", "required": False, "sort_order": 30,
     "notes": "Reduced by direct/indirect interest expense; FNMA/GNMA/FHLMC/repos are taxable (not exempt)."},
    {"fact_key": "ga_sub_nonga_refund", "label": "Income tax refund other than Georgia (Sch 2 sub L8)", "data_type": "decimal", "required": False, "sort_order": 31},
    {"fact_key": "ga_sub_other", "label": "Other GA subtractions (Sch 2 sub L10)", "data_type": "decimal", "required": False, "sort_order": 32},
    # L4 beneficiary share, L7b NOL, credits, withholding
    {"fact_key": "beneficiaries_share", "label": "Beneficiaries' share of income — total of Schedule 3 (Form 501 L4)", "data_type": "decimal", "required": False, "sort_order": 40,
     "notes": "W2. Removes the distributable share so the fiduciary is taxed on RETAINED income. Direct-entry from the federal beneficiary allocation. Do NOT also subtract the federal IDD."},
    {"fact_key": "ga_nol_deduction", "label": "Georgia NOL deduction — Schedule 7 (Form 501 L7b, direct-entry / RED-defer)", "data_type": "decimal", "required": False, "sort_order": 41,
     "notes": "D-10. GA NOL (Sch 7) computed separately from federal — RED-defer v1 (D_GA501_NOL)."},
    {"fact_key": "other_state_tax_credit", "label": "Other state(s) tax credit (Form 501 L9a, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 42},
    {"fact_key": "schedule5_credits", "label": "Schedule 5 nonrefundable credits (Form 501 L9b, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 43},
    {"fact_key": "withholding_credit", "label": "Tax withheld — 1099/G2-A/G2-LP/G2-RP (Form 501 L11b, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 44,
     "notes": "§48-7-129 owner-level withholding when the trust is a NR member of a PTE or sold GA realty (G2-RP)."},
    {"fact_key": "estimated_payments", "label": "Estimated + extension payments (Form 501 L11a)", "data_type": "decimal", "required": False, "sort_order": 45},
]

GA501_RULES: list[dict] = [
    {"rule_id": "R-GA501-BASE", "title": "Federal base (Form 501 L1)", "rule_type": "routing",
     "formula": "L1 = fed_adjusted_total_income (federal Form 1041 line 17, PRE income-distribution deduction)",
     "inputs": ["fed_adjusted_total_income"], "outputs": ["GA501_L1"], "sort_order": 1,
     "description": "W2. GA fiduciary base is the federal 1041 Adjusted Total Income (line 17). The beneficiary share is removed at L4, NOT via the federal distribution deduction (no double-count)."},
    {"rule_id": "R-GA501-SCH2", "title": "Schedule 2 net adjustment (Form 501 L2)", "rule_type": "calculation",
     "formula": ("additions = ga_add_muni_interest + ga_add_other_state_tax + ga_add_exempt_expense + ga_add_fed_nol + ga_add_other ; "
                 "subtractions = ga_sub_us_obligations + ga_sub_nonga_refund + ga_sub_other ; "
                 "L2 = additions - subtractions"),
     "inputs": ["ga_add_muni_interest", "ga_add_other_state_tax", "ga_add_exempt_expense", "ga_add_fed_nol", "ga_add_other",
                "ga_sub_us_obligations", "ga_sub_nonga_refund", "ga_sub_other"],
     "outputs": ["GA501_L2"], "sort_order": 2,
     "description": "§48-7-27 Georgia adjustments. Additions (non-GA muni interest, non-GA income tax, exempt-income expense, fed NOL, other incl. depreciation add-back) minus subtractions (US-obligation interest, non-GA refund, other)."},
    {"rule_id": "R-GA501-L5", "title": "Balance after beneficiary share (Form 501 L3/L5)", "rule_type": "calculation",
     "formula": "L3 = L1 + L2 ; L5 = L3 - beneficiaries_share",
     "inputs": ["beneficiaries_share"], "outputs": ["GA501_L3", "GA501_L5"], "sort_order": 3,
     "description": "W2. L4 (Schedule 3 total) is the beneficiaries' distributable share, removed so the fiduciary is taxed only on retained income."},
    {"rule_id": "R-GA501-EXEMPT", "title": "Georgia exemption (Form 501 L6)", "rule_type": "calculation",
     "formula": "L6 = 1350 if fiduciary_type == trust else 2700",
     "inputs": ["fiduciary_type"], "outputs": ["GA501_L6"], "sort_order": 4,
     "description": "W1. Trust $1,350 (L6a) / estate $2,700 (L6b)."},
    {"rule_id": "R-GA501-TAXABLE", "title": "Georgia net taxable income (Form 501 L7a/L7c)", "rule_type": "calculation",
     "formula": "L7a = max(0, L5 - L6) ; L7c = max(0, L7a - ga_nol_deduction)",
     "inputs": ["ga_nol_deduction"], "outputs": ["GA501_L7a", "GA501_L7c"], "sort_order": 5,
     "description": "L7a GA taxable before NOL; L7c net taxable after the GA NOL (Sch 7, RED-deferred v1)."},
    {"rule_id": "R-GA501-TAX", "title": "Georgia income tax (Form 501 L8) — flat 5.19%", "rule_type": "calculation",
     "formula": "L8 = round(L7c * 0.0519)  [round to the nearest dollar]",
     "inputs": [], "outputs": ["GA501_L8"], "sort_order": 6,
     "description": "W1. Form 501 L8: 'Multiply the amount on Line 7c by 5.19%.' Year-keyed (2026 → 4.99%)."},
    {"rule_id": "R-GA501-CREDITS", "title": "Tax less credits (Form 501 L10)", "rule_type": "calculation",
     "formula": "L10 = max(0, L8 - other_state_tax_credit - schedule5_credits)",
     "inputs": ["other_state_tax_credit", "schedule5_credits"], "outputs": ["GA501_L10"], "sort_order": 7,
     "description": "L9a other-state credit + L9b Schedule 5 nonrefundable credits (direct-entry). Refundable Sch 5B (Timber) and withholding (L11b) are payments, not L9 credits."},
]

GA501_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-GA501-BASE", "GA_2025_FORM_501", "primary", "L1 federal Adjusted Total Income start"),
    ("R-GA501-BASE", "GA_2025_501_INSTR", "secondary", "Line 1 = federal ATI (gross income less itemized)"),
    ("R-GA501-SCH2", "GA_2025_FORM_501", "primary", "Schedule 2 additions/subtractions → L2"),
    ("R-GA501-SCH2", "GA_OCGA_48_7", "secondary", "§48-7-27 Georgia adjustments"),
    ("R-GA501-L5", "GA_2025_FORM_501", "primary", "L3 = L1+L2 ; L5 = L3 − beneficiary share (Sch 3)"),
    ("R-GA501-EXEMPT", "GA_2025_FORM_501", "primary", "L6 exemption $1,350 trust / $2,700 estate"),
    ("R-GA501-TAXABLE", "GA_2025_FORM_501", "primary", "L7a/L7c GA taxable (face arithmetic)"),
    ("R-GA501-TAX", "GA_2025_501_INSTR", "primary", "5.19% rate (What's New) / L8 multiply"),
    ("R-GA501-TAX", "GA_OCGA_48_7", "secondary", "§48-7-20 income tax rate"),
    ("R-GA501-CREDITS", "GA_2025_FORM_501", "primary", "L9a/L9b credits → L10"),
]

GA501_LINES: list[dict] = [
    {"line_number": "1", "description": "Income of fiduciary (federal 1041 Adjusted Total Income, line 17)", "line_type": "input", "source_facts": ["fed_adjusted_total_income"], "sort_order": 1},
    {"line_number": "2", "description": "Net adjustment (Schedule 2)", "line_type": "calculated", "source_rules": ["R-GA501-SCH2"], "sort_order": 2},
    {"line_number": "3", "description": "Total (L1 + L2)", "line_type": "subtotal", "source_rules": ["R-GA501-L5"], "sort_order": 3},
    {"line_number": "4", "description": "Beneficiaries' share of income (total of Schedule 3)", "line_type": "input", "source_facts": ["beneficiaries_share"], "sort_order": 4},
    {"line_number": "5", "description": "Balance (L3 − L4)", "line_type": "subtotal", "source_rules": ["R-GA501-L5"], "sort_order": 5},
    {"line_number": "6", "description": "Exemption (6a Trust $1,350 / 6b Estate $2,700)", "line_type": "calculated", "source_rules": ["R-GA501-EXEMPT"], "sort_order": 6},
    {"line_number": "7a", "description": "Georgia taxable income before NOL (L5 − L6)", "line_type": "subtotal", "source_rules": ["R-GA501-TAXABLE"], "sort_order": 7},
    {"line_number": "7b", "description": "Georgia NOL (Schedule 7)", "line_type": "input", "source_facts": ["ga_nol_deduction"], "sort_order": 8},
    {"line_number": "7c", "description": "Georgia net taxable income (L7a − L7b)", "line_type": "subtotal", "source_rules": ["R-GA501-TAXABLE"], "sort_order": 9},
    {"line_number": "8", "description": "Income tax (L7c × 5.19%)", "line_type": "calculated", "source_rules": ["R-GA501-TAX"], "sort_order": 10},
    {"line_number": "9a", "description": "Other state(s) tax credit", "line_type": "input", "source_facts": ["other_state_tax_credit"], "sort_order": 11},
    {"line_number": "9b", "description": "Schedule 5 nonrefundable credits", "line_type": "input", "source_facts": ["schedule5_credits"], "sort_order": 12},
    {"line_number": "10", "description": "Tax less credits (L8 − L9)", "line_type": "total", "source_rules": ["R-GA501-CREDITS"], "sort_order": 13},
    {"line_number": "11b", "description": "Tax withheld (1099 / G2-A / G2-LP / G2-RP)", "line_type": "input", "source_facts": ["withholding_credit"], "sort_order": 14},
]

GA501_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_GA501_BASE", "title": "GA base = federal 1041 ATI (line 17); beneficiary share removed at L4", "severity": "info",
     "condition": "always",
     "message": "Georgia Form 501 starts from the federal 1041 Adjusted Total Income (line 17, PRE income-distribution deduction) and removes the beneficiaries' distributable share separately at Line 4 (Schedule 3). Do NOT also subtract the federal income distribution deduction — that would double-count the beneficiary income.",
     "notes": "W2. The key modeling guard."},
    {"diagnostic_id": "D_GA501_NR", "title": "Nonresident / part-year (Schedule 4) — prepare manually (RED-defer)", "severity": "error",
     "condition": "residency in (part_year, nonresident)",
     "message": "This return is part-year or nonresident. Georgia source allocation via Schedule 4 (Total vs Georgia-source columns, ratio at Line 9) is NOT computed in v1 — prepare Schedule 4 manually. The full-year resident computation does not apply.",
     "notes": "D-10 RED-defer."},
    {"diagnostic_id": "D_GA501_DEPR", "title": "GA §168(k)/§179 add-back rides generic Sch 2 Other — prepare manually", "severity": "warning",
     "condition": "federal bonus depreciation or §179 in the federal 1041 numbers",
     "message": "Georgia has not adopted §168(k) bonus depreciation or OBBBA (conformity frozen at Jan 1, 2025). Form 501 has NO dedicated depreciation line — add back federal bonus/§179 excess and enter the GA depreciation difference on the generic Schedule 2 'Other' addition/subtraction lines under §48-7-27. Not computed in v1.",
     "notes": "D-10 RED-defer. Ken's specialty."},
    {"diagnostic_id": "D_GA501_NRW", "title": "§48-7-129 4% withholding is OWNER-level, not trust→beneficiary", "severity": "info",
     "condition": "the trust is a nonresident member of a PTE, or sold GA real property (G2-RP)",
     "message": "The §48-7-129 4% nonresident withholding applies to the trust as a MEMBER of a pass-through entity (or on a GA real-property sale, G2-RP) — it does NOT apply to distributions from the trust to its beneficiaries. Withholding taken FROM the trust is claimed as a credit on Form 501 Line 11b.",
     "notes": "Owner-level only. Surfaces on L11b."},
    {"diagnostic_id": "D_GA501_NOL", "title": "Georgia NOL (Schedule 7) — prepare manually", "severity": "info",
     "condition": "ga_nol_deduction claimed",
     "message": "The Georgia NOL (Schedule 7, computed separately from the federal NOL, 80% limitation) is not computed in v1 — prepare Schedule 7 manually and enter the result on Line 7b.",
     "notes": "D-10 RED-defer."},
    {"diagnostic_id": "D_GA501_GRANTOR", "title": "Grantor trust — GA follows the federal grantor treatment", "severity": "info",
     "condition": "is_grantor_trust",
     "message": "For a grantor trust, Georgia follows the federal treatment — the income is taxed to the grantor. There is no separate Georgia fiduciary K-1; the federal grantor letter / return is attached.",
     "notes": "Mirrors the federal grantor path."},
    {"diagnostic_id": "D_GA501_NOPTET", "title": "No PTET at the fiduciary level", "severity": "info",
     "condition": "always",
     "message": "Georgia's pass-through entity tax (HB 149) is a partnership/S-corp election, NOT available on Form 501. A trust only sees PTET as a member/owner of an electing PTE (reflected in the federal numbers flowing to Line 1). There is no PTET election, addback, or subtraction on Form 501.",
     "notes": "Confirmed N/A."},
    {"diagnostic_id": "D_GA501_CONFORM", "title": "GA conformity Jan 1 2025 (OBBBA not adopted) — re-verify 2025 bill", "severity": "warning",
     "condition": "conformity-sensitive item present",
     "message": "Georgia conforms to the IRC as enacted on or before January 1, 2025 and has NOT adopted OBBBA (signed July 4, 2025). Depreciation, §179, and other OBBBA items follow pre-OBBBA federal law. GA passes an annual conformity bill each spring — re-verify before relying on the conformity date.",
     "notes": "W3."},
]

GA501_SCENARIOS: list[dict] = [
    {"scenario_name": "GA501-T1 — resident trust, $1,350 exemption, 5.19%", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"fiduciary_type": "trust", "residency": "full_year_resident", "fed_adjusted_total_income": 50000,
                "beneficiaries_share": 0},
     "expected_outputs": {"GA501_L5": 50000, "GA501_L6": 1350, "GA501_L7c": 48650, "GA501_L8": 2525},
     "notes": "Resident trust retains all 50,000; exemption 1,350; taxable 48,650; tax = round(48,650 × 0.0519) = 2,524.935 → 2,525."},
    {"scenario_name": "GA501-T2 — resident estate, $2,700 exemption", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"fiduciary_type": "estate", "residency": "full_year_resident", "fed_adjusted_total_income": 40000},
     "expected_outputs": {"GA501_L6": 2700, "GA501_L7c": 37300, "GA501_L8": 1936},
     "notes": "Estate exemption 2,700; taxable 37,300; tax = round(37,300 × 0.0519) = 1,935.87 → 1,936."},
    {"scenario_name": "GA501-T3 — beneficiary share removed at L4 (no double-count)", "scenario_type": "edge", "sort_order": 3,
     "inputs": {"fiduciary_type": "trust", "residency": "full_year_resident", "fed_adjusted_total_income": 60000,
                "beneficiaries_share": 45000},
     "expected_outputs": {"GA501_L3": 60000, "GA501_L5": 15000, "GA501_L7c": 13650, "GA501_L8": 708},
     "notes": "Trust distributes 45,000 to beneficiaries (removed at L4); retained 15,000; exemption 1,350; taxable 13,650; tax = round(13,650 × 0.0519) = 708.435 → 708. (The 45,000 is taxed to the beneficiaries, not the trust.)"},
    {"scenario_name": "GA501-T4 — Schedule 2 net adjustment (US-obligation subtraction)", "scenario_type": "edge", "sort_order": 4,
     "inputs": {"fiduciary_type": "trust", "residency": "full_year_resident", "fed_adjusted_total_income": 30000,
                "ga_add_muni_interest": 2000, "ga_sub_us_obligations": 5000},
     "expected_outputs": {"GA501_L2": -3000, "GA501_L5": 27000, "GA501_L7c": 25650},
     "notes": "Additions 2,000 (non-GA muni) − subtractions 5,000 (US obligations) = −3,000 net; L5 = 30,000 − 3,000 = 27,000; taxable 25,650."},
    {"scenario_name": "GA501-T5 — nonresident routes to RED-defer", "scenario_type": "failure", "sort_order": 5,
     "inputs": {"fiduciary_type": "trust", "residency": "nonresident", "fed_adjusted_total_income": 40000},
     "expected_outputs": {"diagnostic": "D_GA501_NR"},
     "notes": "Nonresident/part-year → Schedule 4 allocation is RED-deferred in v1; D_GA501_NR fires (prepare Schedule 4 manually)."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORMS registry + flow assertions
# ═══════════════════════════════════════════════════════════════════════════

FORMS: list[dict] = [
    {
        "identity": {"form_number": "GA501", "form_title": "GA Form 501 — Georgia Fiduciary Income Tax Return (TY2025)",
                     "notes": "Leg (c) of the 1041 module (S-11/WO-09). Georgia resident fiduciary return: federal 1041 Adjusted Total Income (line 17, pre-IDD) → Schedule 2 GA add/subtract → beneficiary share removed at L4 (Schedule 3, no double-count with the federal IDD) → $1,350/$2,700 exemption → flat 5.19% (L8) → credits → L11b withholding. Resident-only v1 (Schedule 4 nonresident allocation + §168(k)/§179 conformity add-backs RED-deferred, D-10). OBBBA not adopted (conformity Jan 1 2025); §48-7-129 4% withholding is owner-level (L11b credit); no fiduciary PTET; no separate GA K-1 (Schedule 3 + federal K-1 attached). Reuses the GA §48-7 statute source from GA700."},
        "facts": GA501_FACTS, "rules": GA501_RULES, "rule_links": GA501_RULE_LINKS,
        "lines": GA501_LINES, "diagnostics": GA501_DIAGNOSTICS, "scenarios": GA501_SCENARIOS,
    },
]

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-GA501-BASE", "title": "GA 501 base = federal 1041 Adjusted Total Income (line 17)", "assertion_type": "flow_assertion",
     "entity_types": ["1041"], "status": "draft", "sort_order": 1,
     "description": "Form 501 Line 1 = federal Form 1041 line 17 (Adjusted Total Income, pre income-distribution deduction). The beneficiary share is removed at Line 4, not via the federal IDD.",
     "definition": {"rule": "R-GA501-BASE", "check": "GA501_L1 = f1041_L17"}},
    {"assertion_id": "FA-GA501-BENE", "title": "Beneficiary share removed once (at L4), no IDD double-count", "assertion_type": "reconciliation",
     "entity_types": ["1041"], "status": "draft", "sort_order": 2,
     "description": "L5 = (L1 + L2) − beneficiaries' share (Schedule 3). The federal income distribution deduction is NOT separately subtracted on Form 501.",
     "definition": {"rule": "R-GA501-L5", "check": "GA501_L5 = L1 + L2 - beneficiaries_share"}},
    {"assertion_id": "FA-GA501-EXEMPT", "title": "GA exemption $1,350 trust / $2,700 estate", "assertion_type": "reconciliation",
     "entity_types": ["1041"], "status": "draft", "sort_order": 3,
     "description": "Form 501 L6 = $1,350 for a trust / $2,700 for an estate.",
     "definition": {"rule": "R-GA501-EXEMPT", "check": "GA501_L6 = 1350 if trust else 2700"}},
    {"assertion_id": "FA-GA501-TAX", "title": "GA tax = net taxable × 5.19%", "assertion_type": "reconciliation",
     "entity_types": ["1041"], "status": "draft", "sort_order": 4,
     "description": "Form 501 L8 = round(L7c × 0.0519). Flat 5.19% for TY2025 (year-keyed; 2026 → 4.99%).",
     "definition": {"rule": "R-GA501-TAX", "check": "GA501_L8 = round(GA501_L7c * 0.0519)"}},
]


# ═══════════════════════════════════════════════════════════════════════════
# Command
# ═══════════════════════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = (
        "Load the GA Form 501 spec (Georgia Fiduciary Income Tax Return, TY2025). "
        "Refuses to seed until Ken sets READY_TO_SEED=True after the review walk (W1-W3)."
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad GA Form 501 spec (Georgia Fiduciary Income Tax Return)\n"))
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
                "\nREFUSING TO SEED GA FORM 501: not cleared to seed.\n\n"
                "Content is authored, but seeding is gated until Ken reviews the packet\n"
                "(W1 the 5.19% rate + $1,350/$2,700 exemptions; W2 the federal-ATI base +\n"
                "beneficiary-share-at-L4 no-double-count; W3 the Jan 1 2025 conformity) and\n"
                "flips the sentinel.\n\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True to proceed)\n\n"
                f"Currently empty / placeholder:\n  {still_empty}\n\n"
                "To proceed: review the module-level data lists (and f1041_source_brief.md),\n"
                "then set READY_TO_SEED = True. Idempotent via update_or_create."
            )

    def _load_topics(self):
        ct = 0
        for code, name in AUTHORITY_TOPICS:
            _, created = AuthorityTopic.objects.update_or_create(topic_code=code, defaults={"topic_name": name})
            if created:
                ct += 1
        self.stdout.write(f"Topics: {ct} new ({len(AUTHORITY_TOPICS)} in batch)")

    def _load_sources(self) -> dict:
        sources: dict = {}
        for src_data in AUTHORITY_SOURCES:
            src_data = dict(src_data)
            excerpts_data = src_data.pop("excerpts", [])
            topic_codes = src_data.pop("topics", [])
            source, _ = AuthoritySource.objects.update_or_create(
                source_code=src_data["source_code"], defaults=src_data,
            )
            sources[source.source_code] = source
            for exc in excerpts_data:
                exc = dict(exc)
                AuthorityExcerpt.objects.update_or_create(
                    authority_source=source, excerpt_label=exc["excerpt_label"], defaults=exc,
                )
            for tc in topic_codes:
                topic = AuthorityTopic.objects.filter(topic_code=tc).first()
                if topic:
                    AuthoritySourceTopic.objects.get_or_create(authority_source=source, authority_topic=topic)
        for code in EXISTING_SOURCES_TO_REFERENCE:
            src = AuthoritySource.objects.filter(source_code=code).first()
            if src:
                sources[code] = src
            else:
                self.stdout.write(self.style.WARNING(f"  existing source {code} NOT FOUND — links to it will be skipped"))
        self.stdout.write(f"Sources ready: {len(sources)}")
        return sources

    def _upsert_form(self, identity: dict) -> TaxForm:
        form, created = TaxForm.objects.update_or_create(
            form_number=identity["form_number"], jurisdiction=FORM_JURISDICTION,
            tax_year=FORM_TAX_YEAR, version=FORM_VERSION,
            defaults={"form_title": identity["form_title"], "entity_types": FORM_ENTITY_TYPES,
                      "status": FORM_STATUS, "notes": identity["notes"]},
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
                RuleAuthorityLink.objects.get_or_create(
                    form_rule=rule, authority_source=source,
                    defaults={"support_level": level, "relevance_note": note},
                )
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
                AuthorityFormLink.objects.get_or_create(
                    authority_source=source, form_code=form_code, link_type=link_type,
                    defaults={"note": f"{source_code} -> {form_code}"},
                )

    def _load_flow_assertions(self):
        for a in FLOW_ASSERTIONS:
            a = dict(a)
            FlowAssertion.objects.update_or_create(assertion_id=a.pop("assertion_id"), defaults=a)
        self.stdout.write(f"  {len(FLOW_ASSERTIONS)} flow assertions")

    def _report_totals(self):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("GA Form 501 loaded.")
        self.stdout.write(
            f"  GA501: facts {len(GA501_FACTS)} / rules {len(GA501_RULES)} / lines {len(GA501_LINES)} / "
            f"diag {len(GA501_DIAGNOSTICS)} / tests {len(GA501_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}"
        )
        self.stdout.write("=" * 60)
