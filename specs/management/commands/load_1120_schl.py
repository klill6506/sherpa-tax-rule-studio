"""Load the Form 1120 Schedule L / M-1 / M-2 / Schedule K spec (TY2025).
WO-11 / S-13, the C-corporation module (form 2 of 3 per Gate-1 shape = spine + 2, DECISIONS D-13).

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
The balance-sheet / book-tax-reconciliation / other-information cluster of Form 1120, pages 5-6:
  • Schedule L — Balance Sheets per Books (assets L1-15, liab/equity L16-28), with the L15==L28
    balance check and the L25 unappropriated-retained-earnings tie to Schedule M-2.
  • Schedule M-1 — Reconciliation of Income (Loss) per Books with Income per Return: L10 = L6 - L9,
    which must equal page-1 L28 (taxable income before NOL & special deductions).
  • Schedule M-2 — Analysis of Unappropriated Retained Earnings: L8 ending = L4 - L7 (beginning +
    net income + other increases - distributions - other decreases); ties to Schedule L L25.
  • Schedule K other-information gates surfaced here: Q13 (<$250k receipts AND assets -> skip
    L/M-1/M-2) and the Schedule M-3 threshold (total assets >= $10M -> Schedule M-3 required).

The compute spine (income -> DRD -> NOL -> 21% tax) is form `1120` (load_1120_spine.py). The
§163(j)/CAMT Schedule K gates live on the spine; this form carries the balance-sheet-oriented Sch K.

Greenfield: no `1120_SCHL` at the 2026-07-05 gap-check.

═══════════════════════════════════════════════════════════════════════════
v1 SCOPE — LOCKED (Ken's Gate-1 walk 2026-07-05; DECISIONS D-13, Q1 form shape).
═══════════════════════════════════════════════════════════════════════════
COMPUTES: Schedule L total assets / total liab+equity + balance check; M-1 book->return
reconciliation (-> page-1 L28); M-2 unappropriated R/E roll-forward (-> Sch L L25); the Q13 $250k
skip gate; the Schedule M-3 $10M-total-assets threshold.

═══════════════════════════════════════════════════════════════════════════
requires_human_review WALK ITEMS (W6-W7)
═══════════════════════════════════════════════════════════════════════════
W6. BALANCE + TIES — Sch L L15 (total assets) == L28 (total liab + equity); Sch M-2 L8 ending
    unappropriated R/E == Sch L L25; Sch M-1 L10 == page-1 L28. CONFIRM the three ties.
W7. GATES — Q13: if total receipts AND total assets are both < $250,000, Schedule L/M-1/M-2 are not
    required. Schedule M-3 replaces M-1 when total assets >= $10,000,000. CONFIRM the thresholds.

═══════════════════════════════════════════════════════════════════════════
SAFETY GUARD — READY_TO_SEED stays False until Ken approves the review walk (W6-W7).
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
# SAFETY GUARD — flip ONLY after Ken's in-session review walk (W6-W7 above).
#
# FLIPPED 2026-07-05 — Ken APPROVED ("Approve — flip, seed, export"): W6 the
# Schedule L balance (L15==L28) + M-1 (L10=page-1 L28) + M-2 (L8 ties to L25)
# ties, W7 the $250k skip gate + $10M Schedule M-3 threshold. Validated on
# throwaway SQLite (scratchpad/validate_1120.py, 55 pass / 0 fail).
# ═══════════════════════════════════════════════════════════════════════════
READY_TO_SEED = True


FORM_JURISDICTION = "federal"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1120"]

# Verified constants (f1120_source_brief.md)
SCHK_SMALL_THRESHOLD = 250000      # Sch K Q13 — skip L/M-1/M-2 if receipts AND assets both < $250k
SCHM3_ASSET_THRESHOLD = 10000000   # Schedule M-3 required when total assets >= $10M


AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("c_corp_balance_recon", "Form 1120 Schedule L balance sheet, M-1 book-tax reconciliation, M-2 "
     "unappropriated retained-earnings analysis, and the Schedule K Q13 $250k / Schedule M-3 $10M gates."),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_F1120",
        "source_type": "federal_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "US",
        "title": "2025 Form 1120 — U.S. Corporation Income Tax Return",
        "citation": "Form 1120 (2025), OMB No. 1545-0123, Created 9/26/25",
        "issuer": "Internal Revenue Service",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f1120.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.6,
        "topics": ["c_corp_balance_recon"],
        "excerpts": [
            {
                "excerpt_label": "Schedule L / M-1 / M-2 (2025 verbatim)",
                "excerpt_text": (
                    "Schedule L Balance Sheets per Books: Assets L1-15 (L15 = Total assets); Liabilities and "
                    "Shareholders' Equity L16-28 (L25 = Retained earnings—Unappropriated; L28 = Total). "
                    "Schedule M-1 Reconciliation of Income per Books with Income per Return: L1 net income per "
                    "books; L2 federal income tax per books; L3 excess capital losses; L4 income subject to tax "
                    "not on books; L5 book expenses not deducted (a depreciation, b charitable, c T&E); L6 add "
                    "1-5; L7 book income not on return (tax-exempt interest); L8 return deductions not on books "
                    "(a depreciation, b charitable); L9 add 7+8; L10 = L6 - L9 (equals page-1 L28). Schedule M-2 "
                    "Analysis of Unappropriated Retained Earnings (Schedule L L25): L1 beginning balance; L2 net "
                    "income per books; L3 other increases; L4 add 1+2+3; L5 distributions (a cash, b stock, c "
                    "property); L6 other decreases; L7 add 5+6; L8 ending balance = L4 - L7. Schedule K Q13: if "
                    "total receipts and total assets are both under $250,000, Schedule L, M-1, and M-2 are not "
                    "required."
                ),
                "summary_text": "Sch L assets L1-15/L15 total, liab+equity L16-28/L28 total, L25 unapprop R/E. M-1 L10=L6-L9=page-1 L28. M-2 L8=L4-L7 ties to L25. Q13 $250k skip gate.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_I1120",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "US",
        "title": "2025 Instructions for Form 1120",
        "citation": "Instructions for Form 1120 (2025)",
        "issuer": "Internal Revenue Service",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i1120.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["c_corp_balance_recon"],
        "excerpts": [
            {
                "excerpt_label": "Schedule M-3 $10M threshold (i1120 / iSchM-3 verbatim substance)",
                "excerpt_text": (
                    "A corporation with total assets of $10 million or more on the last day of the tax year must "
                    "complete Schedule M-3 (Form 1120) in place of Schedule M-1. A corporation with total assets "
                    "of less than $10 million may voluntarily file Schedule M-3. When Schedule M-3 is required, "
                    "Schedule M-1 is not completed."
                ),
                "summary_text": "Schedule M-3 required when total assets >= $10M (replaces M-1). i1120.",
                "is_key_excerpt": True,
            },
        ],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_F1120", "1120_SCHL", "governs"),
    ("IRS_2025_I1120", "1120_SCHL", "governs"),
]


F_FACTS: list[dict] = [
    # ── Schedule L — assets (EOY) ──
    {"fact_key": "schl_cash", "label": "Sch L Cash (L1)", "data_type": "decimal", "required": False, "sort_order": 1},
    {"fact_key": "schl_receivables_net", "label": "Sch L Trade notes & accounts receivable, net of allowance (L2)", "data_type": "decimal", "required": False, "sort_order": 2},
    {"fact_key": "schl_inventories", "label": "Sch L Inventories (L3)", "data_type": "decimal", "required": False, "sort_order": 3},
    {"fact_key": "schl_other_current_assets", "label": "Sch L US obligations + other current assets (L4-6)", "data_type": "decimal", "required": False, "sort_order": 4},
    {"fact_key": "schl_investments", "label": "Sch L Loans to shareholders + mortgage/real estate loans + other investments (L7-9)", "data_type": "decimal", "required": False, "sort_order": 5},
    {"fact_key": "schl_fixed_assets_net", "label": "Sch L Buildings & other depreciable/depletable assets + land, net of accumulated depreciation (L10-12)", "data_type": "decimal", "required": False, "sort_order": 6},
    {"fact_key": "schl_intangibles_net", "label": "Sch L Intangible assets net of amortization (L13)", "data_type": "decimal", "required": False, "sort_order": 7},
    {"fact_key": "schl_other_assets", "label": "Sch L Other assets (L14)", "data_type": "decimal", "required": False, "sort_order": 8},
    # ── Schedule L — liabilities & equity (EOY) ──
    {"fact_key": "schl_current_liabilities", "label": "Sch L Accounts payable + short-term notes + other current liabilities (L16-18)", "data_type": "decimal", "required": False, "sort_order": 10},
    {"fact_key": "schl_long_term_liabilities", "label": "Sch L Loans from shareholders + long-term mortgages/notes + other liabilities (L19-21)", "data_type": "decimal", "required": False, "sort_order": 11},
    {"fact_key": "schl_capital_stock", "label": "Sch L Capital stock — preferred + common (L22a/b)", "data_type": "decimal", "required": False, "sort_order": 12},
    {"fact_key": "schl_paid_in_capital", "label": "Sch L Additional paid-in capital (L23)", "data_type": "decimal", "required": False, "sort_order": 13},
    {"fact_key": "schl_retained_earnings_unapprop", "label": "Sch L Retained earnings — Unappropriated (L25) — ties to M-2 L8", "data_type": "decimal", "required": False, "sort_order": 14},
    {"fact_key": "schl_other_equity_net", "label": "Sch L Appropriated R/E (L24) + equity adjustments (L26) − treasury stock (L27), net", "data_type": "decimal", "required": False, "sort_order": 15,
     "notes": "Treasury stock (L27) is a contra (subtracted); may be negative."},
    # ── Schedule M-1 ──
    {"fact_key": "m1_net_income_books", "label": "M-1 L1 Net income (loss) per books", "data_type": "decimal", "required": False, "sort_order": 20},
    {"fact_key": "m1_federal_tax_books", "label": "M-1 L2 Federal income tax per books", "data_type": "decimal", "required": False, "sort_order": 21},
    {"fact_key": "m1_excess_capital_losses", "label": "M-1 L3 Excess of capital losses over capital gains", "data_type": "decimal", "required": False, "sort_order": 22},
    {"fact_key": "m1_income_taxed_not_books", "label": "M-1 L4 Income subject to tax not recorded on books", "data_type": "decimal", "required": False, "sort_order": 23},
    {"fact_key": "m1_book_expenses_not_deducted", "label": "M-1 L5 Book expenses not deducted (depreciation/charitable/T&E)", "data_type": "decimal", "required": False, "sort_order": 24},
    {"fact_key": "m1_book_income_not_return", "label": "M-1 L7 Book income not on return (tax-exempt interest)", "data_type": "decimal", "required": False, "sort_order": 25},
    {"fact_key": "m1_return_deductions_not_books", "label": "M-1 L8 Return deductions not charged against book income (depreciation/charitable)", "data_type": "decimal", "required": False, "sort_order": 26},
    {"fact_key": "taxable_income_l28", "label": "Page-1 L28 taxable income before NOL & special deductions (cross-ref from form 1120)", "data_type": "decimal", "required": False, "sort_order": 27,
     "notes": "M-1 L10 must equal this. Direct-entry the spine's L28 for the reconciliation check."},
    # ── Schedule M-2 ──
    {"fact_key": "m2_beginning_balance", "label": "M-2 L1 Balance at beginning of year", "data_type": "decimal", "required": False, "sort_order": 30},
    {"fact_key": "m2_other_increases", "label": "M-2 L3 Other increases", "data_type": "decimal", "required": False, "sort_order": 31},
    {"fact_key": "m2_distributions", "label": "M-2 L5 Distributions (cash/stock/property)", "data_type": "decimal", "required": False, "sort_order": 32},
    {"fact_key": "m2_other_decreases", "label": "M-2 L6 Other decreases", "data_type": "decimal", "required": False, "sort_order": 33},
    # ── Schedule K gates ──
    {"fact_key": "total_receipts", "label": "Total receipts (Sch K Q13 $250k gate)", "data_type": "decimal", "required": False, "sort_order": 40},
]

F_RULES: list[dict] = [
    {"rule_id": "R-SCHL-ASSETS", "title": "Schedule L total assets (L15)", "rule_type": "calculation",
     "formula": "total_assets = schl_cash + schl_receivables_net + schl_inventories + schl_other_current_assets + schl_investments + schl_fixed_assets_net + schl_intangibles_net + schl_other_assets",
     "inputs": ["schl_cash", "schl_receivables_net", "schl_inventories", "schl_other_current_assets", "schl_investments", "schl_fixed_assets_net", "schl_intangibles_net", "schl_other_assets"],
     "outputs": ["total_assets"], "sort_order": 1,
     "description": "Schedule L L15 total assets (sum of the EOY asset lines, net of contra allowances/accumulated depreciation)."},
    {"rule_id": "R-SCHL-LIABEQ", "title": "Schedule L total liabilities + equity (L28)", "rule_type": "calculation",
     "formula": "total_liab_equity = schl_current_liabilities + schl_long_term_liabilities + schl_capital_stock + schl_paid_in_capital + schl_retained_earnings_unapprop + schl_other_equity_net",
     "inputs": ["schl_current_liabilities", "schl_long_term_liabilities", "schl_capital_stock", "schl_paid_in_capital", "schl_retained_earnings_unapprop", "schl_other_equity_net"],
     "outputs": ["total_liab_equity"], "sort_order": 2,
     "description": "Schedule L L28 total liabilities + shareholders' equity (treasury stock L27 is a contra within schl_other_equity_net)."},
    {"rule_id": "R-SCHL-BAL", "title": "Schedule L balance check (L15 == L28)", "rule_type": "validation",
     "formula": "total_assets == total_liab_equity",
     "inputs": ["total_assets", "total_liab_equity"], "outputs": [], "sort_order": 3,
     "description": "W6. The Schedule L balance sheet must balance: total assets (L15) equals total liabilities and shareholders' equity (L28)."},
    {"rule_id": "R-1120-M1", "title": "Schedule M-1 reconciliation (L10 = L6 − L9 = page-1 L28)", "rule_type": "calculation",
     "formula": ("m1_l6 = m1_net_income_books + m1_federal_tax_books + m1_excess_capital_losses + m1_income_taxed_not_books + m1_book_expenses_not_deducted ; "
                 "m1_l9 = m1_book_income_not_return + m1_return_deductions_not_books ; m1_l10 = m1_l6 - m1_l9   (must equal page-1 L28)"),
     "inputs": ["m1_net_income_books", "m1_federal_tax_books", "m1_excess_capital_losses", "m1_income_taxed_not_books", "m1_book_expenses_not_deducted", "m1_book_income_not_return", "m1_return_deductions_not_books"],
     "outputs": ["m1_l10"], "sort_order": 4,
     "description": "W6. Schedule M-1: book net income + federal tax + excess capital losses + book-not-return income + book expenses not deducted (L6), less book-not-return income + return-not-book deductions (L9) = L10, which reconciles to page-1 L28 (taxable income before NOL & special deductions)."},
    {"rule_id": "R-1120-M2", "title": "Schedule M-2 unappropriated R/E roll-forward (L8 = L4 − L7)", "rule_type": "calculation",
     "formula": ("m2_l4 = m2_beginning_balance + m1_net_income_books + m2_other_increases ; m2_l7 = m2_distributions + m2_other_decreases ; "
                 "m2_l8 = m2_l4 - m2_l7   (must equal Sch L L25 schl_retained_earnings_unapprop)"),
     "inputs": ["m2_beginning_balance", "m1_net_income_books", "m2_other_increases", "m2_distributions", "m2_other_decreases"],
     "outputs": ["m2_l8"], "sort_order": 5,
     "description": "W6. Schedule M-2: beginning unappropriated R/E + net income per books + other increases (L4), less distributions + other decreases (L7) = ending balance (L8), which ties to Schedule L line 25."},
    {"rule_id": "R-SCHK-250K", "title": "Schedule K Q13 — $250k skip gate", "rule_type": "routing",
     "formula": "if total_receipts < 250000 and total_assets < 250000: Schedule L, M-1, and M-2 are not required",
     "inputs": ["total_receipts", "total_assets"], "outputs": ["skip_l_m1_m2"], "sort_order": 6,
     "description": "W7. Sch K Q13: a corporation with both total receipts and total assets under $250,000 is not required to complete Schedule L, M-1, or M-2."},
    {"rule_id": "R-SCHK-M3", "title": "Schedule M-3 threshold ($10M total assets)", "rule_type": "routing",
     "formula": "if total_assets >= 10000000: Schedule M-3 (Form 1120) is required in place of Schedule M-1",
     "inputs": ["total_assets"], "outputs": ["require_m3"], "sort_order": 7,
     "description": "W7. A corporation with total assets of $10 million or more on the last day of the tax year must file Schedule M-3 in place of Schedule M-1."},
]

F_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-SCHL-ASSETS", "IRS_2025_F1120", "primary", "Schedule L assets L1-15"),
    ("R-SCHL-LIABEQ", "IRS_2025_F1120", "primary", "Schedule L liab/equity L16-28"),
    ("R-SCHL-BAL", "IRS_2025_F1120", "primary", "Schedule L L15 == L28"),
    ("R-1120-M1", "IRS_2025_F1120", "primary", "Schedule M-1 L1-10"),
    ("R-1120-M2", "IRS_2025_F1120", "primary", "Schedule M-2 L1-8"),
    ("R-SCHK-250K", "IRS_2025_F1120", "primary", "Schedule K Q13"),
    ("R-SCHK-M3", "IRS_2025_I1120", "primary", "Schedule M-3 $10M threshold"),
]

F_LINES: list[dict] = [
    {"line_number": "L-15", "description": "Schedule L L15 Total assets", "line_type": "subtotal", "source_rules": ["R-SCHL-ASSETS"], "sort_order": 1},
    {"line_number": "L-28", "description": "Schedule L L28 Total liabilities + shareholders' equity", "line_type": "subtotal", "source_rules": ["R-SCHL-LIABEQ"], "sort_order": 2},
    {"line_number": "M1-10", "description": "Schedule M-1 L10 (= page-1 L28)", "line_type": "calculated", "source_rules": ["R-1120-M1"], "sort_order": 3},
    {"line_number": "M2-8", "description": "Schedule M-2 L8 Ending unappropriated R/E (= Sch L L25)", "line_type": "calculated", "source_rules": ["R-1120-M2"], "sort_order": 4},
    {"line_number": "K-13", "description": "Schedule K Q13 $250k skip gate", "line_type": "calculated", "source_rules": ["R-SCHK-250K"], "sort_order": 5},
]

F_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_SCHL_BALANCE", "title": "Schedule L must balance (assets = liabilities + equity)", "severity": "error",
     "condition": "total_assets != total_liab_equity",
     "message": "Schedule L is out of balance: total assets (line 15) must equal total liabilities and shareholders' equity (line 28). Review the balance-sheet entries.",
     "notes": "W6."},
    {"diagnostic_id": "D_1120_M1_RECON", "title": "Schedule M-1 line 10 must equal page-1 line 28", "severity": "error",
     "condition": "m1_l10 != taxable_income_l28",
     "message": "The Schedule M-1 reconciliation (line 10) must equal taxable income before NOL and special deductions (page-1 line 28). A mismatch means a book-tax difference is missing or miskeyed.",
     "notes": "W6."},
    {"diagnostic_id": "D_1120_M2_TIE", "title": "Schedule M-2 ending balance must tie to Schedule L line 25", "severity": "warning",
     "condition": "m2_l8 != schl_retained_earnings_unapprop",
     "message": "The Schedule M-2 ending unappropriated retained earnings (line 8) should equal Schedule L line 25 (Retained earnings—Unappropriated). Reconcile the roll-forward (beginning + net income + other increases − distributions − other decreases).",
     "notes": "W6."},
    {"diagnostic_id": "D_1120_250K", "title": "Schedule L/M-1/M-2 not required under $250k (Sch K Q13)", "severity": "info",
     "condition": "total_receipts < 250000 and total_assets < 250000",
     "message": "Both total receipts and total assets are under $250,000, so Schedule L, Schedule M-1, and Schedule M-2 are not required (Schedule K, question 13). They may still be completed voluntarily.",
     "notes": "W7."},
    {"diagnostic_id": "D_1120_M3", "title": "Schedule M-3 required — total assets ≥ $10 million", "severity": "warning",
     "condition": "total_assets >= 10000000",
     "message": "Total assets are $10 million or more on the last day of the tax year, so Schedule M-3 (Form 1120) must be filed in place of Schedule M-1. Schedule M-3 provides a more detailed book-tax reconciliation.",
     "notes": "W7."},
]

F_SCENARIOS: list[dict] = [
    {"scenario_name": "SCHL-A — balanced balance sheet", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"schl_cash": 100000, "schl_receivables_net": 50000, "schl_fixed_assets_net": 350000,
                "schl_current_liabilities": 80000, "schl_long_term_liabilities": 220000, "schl_capital_stock": 100000, "schl_retained_earnings_unapprop": 100000},
     "expected_outputs": {"total_assets": 500000, "total_liab_equity": 500000},
     "notes": "Assets 500,000 = liabilities 300,000 + equity 200,000. Balances (L15 == L28)."},
    {"scenario_name": "SCHL-B — M-1 reconciles to page-1 L28", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"m1_net_income_books": 120000, "m1_federal_tax_books": 25000, "m1_book_expenses_not_deducted": 10000, "m1_book_income_not_return": 5000, "taxable_income_l28": 150000},
     "expected_outputs": {"m1_l10": 150000},
     "notes": "M-1 L6 = 120,000 + 25,000 + 10,000 = 155,000; L9 = 5,000; L10 = 150,000 = page-1 L28. Reconciles."},
    {"scenario_name": "SCHL-C — M-2 R/E roll-forward ties to Sch L L25", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"m2_beginning_balance": 80000, "m1_net_income_books": 120000, "m2_distributions": 100000, "schl_retained_earnings_unapprop": 100000},
     "expected_outputs": {"m2_l8": 100000},
     "notes": "M-2: 80,000 + 120,000 = 200,000 (L4); distributions 100,000 (L7); ending 100,000 (L8) = Sch L L25. Ties."},
    {"scenario_name": "SCHL-D — Schedule M-3 required ($10M assets)", "scenario_type": "edge", "sort_order": 4,
     "inputs": {"schl_fixed_assets_net": 12000000},
     "expected_outputs": {"total_assets": 12000000, "require_m3": True, "diagnostic": "D_1120_M3"},
     "notes": "Total assets 12M >= 10M -> Schedule M-3 required in place of M-1."},
    {"scenario_name": "SCHL-E — small corp skips L/M-1/M-2 (Q13)", "scenario_type": "edge", "sort_order": 5,
     "inputs": {"total_receipts": 180000, "schl_cash": 200000},
     "expected_outputs": {"total_assets": 200000, "skip_l_m1_m2": True, "diagnostic": "D_1120_250K"},
     "notes": "Receipts 180,000 < 250k and assets 200,000 < 250k -> Schedule L/M-1/M-2 not required (Q13)."},
    {"scenario_name": "SCHL-F — out-of-balance sheet flags an error", "scenario_type": "failure", "sort_order": 6,
     "inputs": {"schl_cash": 500000, "schl_current_liabilities": 80000, "schl_capital_stock": 100000, "schl_retained_earnings_unapprop": 100000},
     "expected_outputs": {"total_assets": 500000, "total_liab_equity": 280000, "diagnostic": "D_SCHL_BALANCE"},
     "notes": "Assets 500,000 != liab+equity 280,000 -> D_SCHL_BALANCE error. Balance sheet must balance."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORMS registry + flow assertions
# ═══════════════════════════════════════════════════════════════════════════
FORMS: list[dict] = [
    {
        "identity": {"form_number": "1120_SCHL", "form_title": "Form 1120 Schedule L / M-1 / M-2 / K (Balance Sheet & Reconciliation, TY2025)",
                     "notes": "WO-11 / S-13 (form 2 of 3, DECISIONS D-13 Q1). Schedule L balance sheet (assets L1-15 == liab/equity L16-28), Schedule M-1 book-tax reconciliation (L10 = L6-L9 = page-1 L28), Schedule M-2 unappropriated R/E roll-forward (L8 = L4-L7, ties to Sch L L25), and the balance-sheet Schedule K gates (Q13 $250k skip; Schedule M-3 $10M-total-assets threshold). Compute spine (income->DRD->NOL->21% tax) = form 1120; §163(j)/CAMT Sch K gates live there."},
        "facts": F_FACTS, "rules": F_RULES, "rule_links": F_RULE_LINKS,
        "lines": F_LINES, "diagnostics": F_DIAGNOSTICS, "scenarios": F_SCENARIOS,
    },
]

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1120-BALANCE", "title": "Schedule L balances (L15 = L28)", "assertion_type": "reconciliation",
     "entity_types": ["1120"], "status": "draft", "sort_order": 1,
     "description": "Total assets (Schedule L line 15) equal total liabilities and shareholders' equity (line 28).",
     "definition": {"rule": "R-SCHL-BAL", "check": "total_assets == total_liab_equity"}},
    {"assertion_id": "FA-1120-M1", "title": "Schedule M-1 reconciles to page-1 L28", "assertion_type": "reconciliation",
     "entity_types": ["1120"], "status": "draft", "sort_order": 2,
     "description": "Schedule M-1 line 10 (L6 − L9) equals taxable income before NOL and special deductions (page-1 line 28).",
     "definition": {"rule": "R-1120-M1", "check": "m1_l10 == taxable_income_l28"}},
    {"assertion_id": "FA-1120-M2", "title": "Schedule M-2 ending R/E ties to Schedule L L25", "assertion_type": "reconciliation",
     "entity_types": ["1120"], "status": "draft", "sort_order": 3,
     "description": "Schedule M-2 ending unappropriated retained earnings (line 8 = L4 − L7) equals Schedule L line 25.",
     "definition": {"rule": "R-1120-M2", "check": "m2_l8 == schl_retained_earnings_unapprop"}},
]


# ═══════════════════════════════════════════════════════════════════════════
# Command
# ═══════════════════════════════════════════════════════════════════════════
class Command(BaseCommand):
    help = (
        "Load the Form 1120 Schedule L/M-1/M-2/K spec (TY2025). "
        "Refuses to seed until Ken sets READY_TO_SEED=True after the review walk (W6-W7)."
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad Form 1120 Schedule L / M-1 / M-2 / K spec\n"))
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
                "\nREFUSING TO SEED FORM 1120_SCHL: not cleared to seed.\n\n"
                "Content is authored, but seeding is gated until Ken reviews the packet\n"
                "(W6 the Schedule L balance + M-1/M-2 ties; W7 the $250k and $10M M-3\n"
                "thresholds) and flips the sentinel.\n\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True to proceed)\n\n"
                f"Currently empty / placeholder:\n  {still_empty}\n\n"
                "To proceed: review the module-level data lists (and f1120_source_brief.md),\n"
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
        self.stdout.write("Form 1120_SCHL loaded.")
        self.stdout.write(
            f"  1120_SCHL: facts {len(F_FACTS)} / rules {len(F_RULES)} / lines {len(F_LINES)} / "
            f"diag {len(F_DIAGNOSTICS)} / tests {len(F_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}"
        )
        self.stdout.write("=" * 60)
