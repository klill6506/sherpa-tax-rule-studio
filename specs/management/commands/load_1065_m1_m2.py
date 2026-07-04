"""Load the 1065 Schedule M-1 + M-2 spec — form 3 of the 1065-core campaign.

Fresh-authored 2026-07-04 per D-1. Seeds TWO forms:
  - **1065_M1** — Schedule M-1: Reconciliation of Income (Loss) per Books With Analysis of Net
    Income (Loss) per Return. Line 9 = line 5 − line 8 = **Analysis of Net Income (Loss) per
    Return, line 1** (the face says so verbatim) = SCH_K_1065 R-SCHK-ANALYSIS.
  - **1065_M2** — Schedule M-2: Analysis of Partners' Capital Accounts (TAX BASIS,
    transactional §705/§722/§733). Line 9 = line 5 − line 8 = ending capital.

SOURCE: the line maps are extracted VERBATIM 2026-07-04 from the FINAL 2025 f1065.pdf page 6
(Cat. 11390Z, pymupdf dump) — NOT recollection. Verbatim face structure:
  M-1: 1 net income per books; 2 income on Sch K lines 1,2,3c,5,6a,7,8,9a,10,11 not on books;
       3 guaranteed payments (other than health insurance); 4 expenses on books not on Sch K
       lines 1-13e & 21 (4a depreciation, 4b travel/entertainment); 5 add lines 1-4; 6 income
       on books not on Sch K lines 1-11 (6a tax-exempt interest); 7 deductions on Sch K lines
       1-13e & 21 not on books (7a depreciation); 8 add lines 6 and 7; 9 income (loss)
       (Analysis of Net Income line 1) = line 5 − line 8.
  M-2: 1 balance BOY; 2 capital contributed (2a cash, 2b property); 3 net income (loss) (see
       instructions); 4 other increases; 5 add lines 1-4; 6 distributions (6a cash, 6b
       property); 7 other decreases; 8 add lines 6 and 7; 9 balance EOY = line 5 − line 8.

RECONCILE TARGET (D-1, brief §2): tts `compute.py` FORMULAS_1065 M-1/M-2 block + seed_1065.
What tts does: M1_3 = K4c; M1_5 = Σ(M1_1, M1_2, M1_3, M1_4a, M1_4b, M1_4c); M1_8 = Σ(M1_6,
M1_7a, M1_7b); M1_9 = M1_5 − M1_8. M2_5 = Σ(M2_1, M2_2a, M2_2b, M2_3, M2_4); M2_8 = Σ(M2_6a,
M2_6b, M2_7); M2_9 = M2_5 − M2_8.

RECONCILE FINDINGS logged for the Ken walk (D-1 adjudications):
  1. ⚠ **M2_3 mis-source (candidate tts fix).** tts labels M2_3 "Net income (loss) per books"
     and takes it as a DATA-ENTRY input. The FINAL 2025 face line 3 = "Net income (loss) (see
     instructions)", and the instructions tie it to Analysis of Net Income line 1 (= M-1 line 9,
     per RETURN, on the tax-basis M-2). The spec ties M2_3 = M1_9 = Analysis line 1 (R-M2-3-TIE,
     D_M2_3). Ken adjudicates whether tts should auto-tie M2_3 (like the net-farm fix) or keep it
     open.
  2. tts adds catch-all sublines **M1_4c** (other book expenses) and **M1_7b** (other Sch-K
     deductions) NOT on the 2025 face (face = 4a/4b, 7a). Benign extension; the spec follows the
     face and notes tts's extra rows.
  3. **M2_1 = Σ K-1 item L beginning tax-basis capital**, but the item-L roll-forward is a tts
     RED-defer (K-1 leg, D_K1_ITEML) — so M2_1 cannot auto-derive; it is data-entry. R-M2-1-TIE /
     D_M2_1 carry the K-1 gap home.
  4. **M1_9 = Analysis line 1**, but tts computes NO 1065 Analysis of Net Income (spine reconcile
     gap #6 — K18 is 1120-S-only). The Analysis build-gap must be filled for M-1 to reconcile;
     cross-referenced (D_M1_ANALYSIS).
  5. **Schedule B Q4 small-partnership exemption** (receipts < $250,000 AND assets < $1,000,000
     AND timely K-1s AND not-M-3-required) suppresses Schedules L, M-1, M-2, item F, and K-1 item
     L. Encoded as a gating fact (m_schb_q4_small) + D_M1_EXEMPT / D_M2_EXEMPT. (Schedule M-3
     replaces M-1 at ≥$10M assets / ≥$35M receipts — Decision B RED-defer, flagged not built.)

AUTHORITY: primary IRC §705(a) (M-2 tax-basis capital roll-forward) + §702(a)/(b) (M-1 book-tax
separately-stated differences) re-used verbatim from the K-1 / spine loads; the 2025 f1065 page-6
+ i1065 M-1/M-2 line maps as filing authority (requires_human_review). Verbatim page-6 text
extracted from the FINAL PDF this session.
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


# FRESH-AUTHORED 2026-07-04 (M-1/M-2 leg). Per D-1: READY_TO_SEED=False until the Ken walk
# (the M2_3 mis-source adjudication + reconcile findings), then flip and seed.
READY_TO_SEED = False


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("partnership_1065_core",
     "Partnership return core (Form 1065) — Schedule M-1 (book↔return reconciliation) and "
     "Schedule M-2 (partners' tax-basis capital accounts, §705 transactional)."),
]

AUTHORITY_SOURCES: list[dict] = [
    # ── IRC §705 — partner's basis (M-2 tax-basis capital roll-forward) ──
    {
        "source_code": "IRC_705",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1065",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §705 — Determination of Basis of Partner's Interest (transactional roll-forward)",
        "citation": "26 U.S.C. §705(a)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/705",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "The transactional roll-forward behind M-2 (tax-basis partners' capital): beginning + "
                 "contributions + distributive-share income (incl. tax-exempt) − distributions − loss/"
                 "nondeductible share = ending. M-2 line 3 (net income) = Analysis line 1 = M-1 line 9. "
                 "Re-used from the K-1 load; verbatim.",
        "topics": ["partnership_1065_core"],
        "excerpts": [
            {
                "excerpt_label": "§705(a) — basis increased by income, decreased by distributions/losses",
                "location_reference": "26 U.S.C. §705(a)(1), (2)",
                "excerpt_text": (
                    "The adjusted basis of a partner's interest in a partnership shall, except as provided "
                    "in subsection (b), be the basis of such interest determined under section 722 or "
                    "section 742— (1) increased by the sum of his distributive share for the taxable year "
                    "and prior taxable years of— (A) taxable income of the partnership as determined under "
                    "section 703(a), (B) income of the partnership exempt from tax, and (C) the excess of "
                    "the deductions for depletion over the basis of the property subject to depletion; "
                    "(2) decreased (but not below zero) by distributions by the partnership as provided in "
                    "section 733 and by the sum of his distributive share of— (A) losses of the "
                    "partnership, and (B) expenditures of the partnership not deductible in computing its "
                    "taxable income and not properly chargeable to capital account."
                ),
                "summary_text": "M-2 tax-basis capital roll-forward: BOY + income share (incl. tax-exempt) − "
                                "distributions − loss/nondeductible share = EOY (transactional, §705/§733).",
                "is_key_excerpt": True,
            },
        ],
    },
    # ── IRC §702 — separately-stated items (M-1 book↔return differences) ──
    {
        "source_code": "IRC_702",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1065",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §702 — Income and Credits of Partner (separately stated items; character conduit)",
        "citation": "26 U.S.C. §702(a), (b)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/702",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "M-1 reconciles book net income to the §702(a) separately-stated Schedule K items making "
                 "up Analysis line 1 — the book↔return timing/permanent differences (lines 2/4/6/7). "
                 "Re-used; verbatim.",
        "topics": ["partnership_1065_core"],
        "excerpts": [
            {
                "excerpt_label": "§702(b) — character determined at the partnership level",
                "location_reference": "26 U.S.C. §702(b)",
                "excerpt_text": (
                    "The character of any item of income, gain, loss, deduction, or credit included in a "
                    "partner's distributive share under paragraphs (1) through (7) of subsection (a) shall "
                    "be determined as if such item were realized directly from the source from which "
                    "realized by the partnership, or incurred in the same manner as incurred by the "
                    "partnership."
                ),
                "summary_text": "The Schedule K separately-stated items (which Analysis line 1 combines) keep "
                                "partnership-level character — the return side of the M-1 reconciliation.",
                "is_key_excerpt": False,
            },
        ],
    },
    # ── 2025 Form 1065 page 6 — M-1/M-2 face (filing authority, verbatim) ──
    {
        "source_code": "IRS_2025_F1065",
        "source_type": "official_form",
        "source_rank": "implementation_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1065",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "Form 1065 (2025) page 6 — Schedule M-1 (book↔return reconciliation) + Schedule M-2 "
                 "(partners' capital accounts)",
        "citation": "Form 1065 (2025), Cat. No. 11390Z, page 6, Schedule M-1 lines 1-9 + Schedule M-2 "
                    "lines 1-9",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f1065.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": "M-1/M-2 line structure extracted VERBATIM 2026-07-04 from the FINAL 2025 f1065.pdf page 6 "
                 "(pymupdf). Key: M-1 line 9 = 'Analysis of Net Income (Loss) per Return, line 1' (face "
                 "verbatim); M-2 line 3 = 'Net income (loss) (see instructions)'. REQUIRES HUMAN REVIEW.",
        "topics": ["partnership_1065_core"],
        "excerpts": [
            {
                "excerpt_label": "Schedule M-1 lines 1-9 (verbatim, f1065 2025 p.6)",
                "location_reference": "f1065 (2025) page 6, Schedule M-1",
                "excerpt_text": (
                    "Schedule M-1 Reconciliation of Income (Loss) per Books With Analysis of Net Income "
                    "(Loss) per Return. Note: The partnership may be required to file Schedule M-3. "
                    "1 Net income (loss) per books. 2 Income included on Schedule K, lines 1, 2, 3c, 5, 6a, "
                    "7, 8, 9a, 10, and 11, not recorded on books this year (itemize). 3 Guaranteed payments "
                    "(other than health insurance). 4 Expenses recorded on books this year not included on "
                    "Schedule K, lines 1 through 13e, and 21 (itemize): a Depreciation, b Travel and "
                    "entertainment. 5 Add lines 1 through 4. 6 Income recorded on books this year not "
                    "included on Schedule K, lines 1 through 11 (itemize): a Tax-exempt interest. "
                    "7 Deductions included on Schedule K, lines 1 through 13e, and 21, not charged against "
                    "book income this year (itemize): a Depreciation. 8 Add lines 6 and 7. 9 Income (loss) "
                    "(Analysis of Net Income (Loss) per Return, line 1). Subtract line 8 from line 5."
                ),
                "summary_text": "M-1: 5 = Σ(1-4); 8 = Σ(6-7); 9 = 5 − 8 = Analysis line 1. Face sublines "
                                "4a/4b, 6a, 7a (tts adds 4c/7b catch-alls).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule M-2 lines 1-9 (verbatim, f1065 2025 p.6)",
                "location_reference": "f1065 (2025) page 6, Schedule M-2",
                "excerpt_text": (
                    "Schedule M-2 Analysis of Partners' Capital Accounts. 1 Balance at beginning of year. "
                    "2 Capital contributed: a Cash, b Property. 3 Net income (loss) (see instructions). "
                    "4 Other increases (itemize). 5 Add lines 1 through 4. 6 Distributions: a Cash, "
                    "b Property. 7 Other decreases (itemize). 8 Add lines 6 and 7. 9 Balance at end of "
                    "year. Subtract line 8 from line 5."
                ),
                "summary_text": "M-2 (tax basis): 5 = Σ(1-4); 8 = Σ(6-7); 9 = 5 − 8 = ending capital. Line 3 "
                                "'(see instructions)' = Analysis line 1 = M-1 line 9 (per return).",
                "is_key_excerpt": True,
            },
        ],
    },
    # ── 2025 Instructions — M-2 line 3 tie + the small-partnership exemption (Q4) ──
    {
        "source_code": "IRS_2025_I1065",
        "source_type": "official_instructions",
        "source_rank": "implementation_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1065",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Form 1065 — Schedule M-2 line 3 (= Analysis line 1) + the "
                 "Schedule B Q4 small-partnership exemption + the M-3 threshold",
        "citation": "Instructions for Form 1065 (2025), Cat. No. 11392V, Schedules M-1/M-2 + Schedule B "
                    "question 4",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i1065.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": "M-2 line 3 net income ties to Analysis of Net Income line 1 (per return, tax basis). The "
                 "Schedule B Q4 four-condition test suppresses L/M-1/M-2 + K-1 item L. M-3 replaces M-1 at "
                 "≥$10M assets / ≥$35M receipts (Decision B RED-defer). Per the brief §4.3 verbatim "
                 "transcription. REQUIRES HUMAN REVIEW.",
        "topics": ["partnership_1065_core"],
        "excerpts": [
            {
                "excerpt_label": "Schedule B Q4 — small-partnership exemption (verbatim)",
                "location_reference": "i1065 (2025), Schedule B question 4",
                "excerpt_text": (
                    "Does the partnership satisfy all four of the following conditions? (a) The "
                    "partnership's total receipts for the tax year were less than $250,000. (b) The "
                    "partnership's total assets at the end of the tax year were less than $1 million. "
                    "(c) Schedules K-1 are filed with the return and furnished to the partners on or before "
                    "the due date (including extensions) for the partnership return. (d) The partnership is "
                    "not filing and is not required to file Schedule M-3. If 'Yes,' the partnership is not "
                    "required to complete Schedules L, M-1, and M-2; item F on page 1 of Form 1065; or item "
                    "L on Schedule K-1."
                ),
                "summary_text": "Q4 all-four (receipts < $250k AND assets < $1M AND timely K-1s AND not-M-3) "
                                "→ Schedules L, M-1, M-2, item F, K-1 item L NOT required. Gating fact.",
                "is_key_excerpt": True,
            },
        ],
    },
]

# (source_code, form_code, link_type)
AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_F1065", "1065_M1", "governs"),
    ("IRS_2025_I1065", "1065_M1", "governs"),
    ("IRC_702", "1065_M1", "informs"),
    ("IRS_2025_F1065", "1065_M2", "governs"),
    ("IRS_2025_I1065", "1065_M2", "governs"),
    ("IRC_705", "1065_M2", "governs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 1: 1065_M1 — Schedule M-1 (book ↔ return reconciliation)
# ═══════════════════════════════════════════════════════════════════════════

M1_IDENTITY = {
    "form_number": "1065_M1",
    "entity_types": ["1065"],
    "form_title": "Schedule M-1 (Form 1065, 2025) — Reconciliation of Income (Loss) per Books With "
                  "Analysis of Net Income (Loss) per Return",
    "notes": (
        "FRESH-AUTHORED 2026-07-04 (1065-core, form 3) from the FINAL 2025 f1065 page 6 (pymupdf verbatim). "
        "M-1 book↔return reconciliation: 5 = Σ(1-4); 8 = Σ(6-7); 9 = 5 − 8 = Analysis of Net Income line 1 "
        "(face verbatim) = SCH_K_1065 R-SCHK-ANALYSIS. Face sublines 4a depreciation / 4b travel-entertainment, "
        "6a tax-exempt interest, 7a depreciation. Reconcile: tts M1_3 = K4c (guaranteed payments auto), "
        "M1_4b = meals/entertainment nondeductible; tts adds catch-all M1_4c/M1_7b NOT on the face (benign). "
        "M1_9 ties to Analysis line 1 — which tts does NOT compute (spine reconcile gap #6) → D_M1_ANALYSIS. "
        "Schedule B Q4 small-partnership exemption suppresses M-1 (D_M1_EXEMPT). READY_TO_SEED=False."
    ),
}

M1_FACTS: list[dict] = [
    {"fact_key": "m1_1_book_income", "label": "1 — Net income (loss) per books", "data_type": "decimal",
     "default_value": "0", "sort_order": 1},
    {"fact_key": "m1_2_income_on_k_not_books", "label": "2 — Income on Sch K (1,2,3c,5,6a,7,8,9a,10,11) not on books",
     "data_type": "decimal", "default_value": "0", "sort_order": 2, "notes": "Itemize. Timing/permanent book↔return diff."},
    {"fact_key": "m1_3_guaranteed_payments", "label": "3 — Guaranteed payments (other than health insurance)",
     "data_type": "decimal", "default_value": "0", "sort_order": 3,
     "notes": "YELLOW pull = Sch K line 4c (tts M1_3 = K4c). GP is a return deduction not a book expense."},
    {"fact_key": "m1_4a_depreciation", "label": "4a — Expenses on books not on Sch K: depreciation",
     "data_type": "decimal", "default_value": "0", "sort_order": 4},
    {"fact_key": "m1_4b_travel_entertainment", "label": "4b — Expenses on books not on Sch K: travel & entertainment",
     "data_type": "decimal", "default_value": "0", "sort_order": 5,
     "notes": "tts M1_4b = D_MEALS_NONDED (nondeductible meals/entertainment)."},
    {"fact_key": "m1_5_add_1_to_4", "label": "5 — Add lines 1 through 4", "data_type": "decimal", "sort_order": 6,
     "notes": "OUTPUT. 5 = 1 + 2 + 3 + 4a + 4b."},
    {"fact_key": "m1_6a_taxexempt_interest", "label": "6a — Income on books not on Sch K: tax-exempt interest",
     "data_type": "decimal", "default_value": "0", "sort_order": 7,
     "notes": "Ties to Sch K line 18a (tax-exempt interest)."},
    {"fact_key": "m1_7a_depreciation", "label": "7a — Deductions on Sch K not on books: depreciation",
     "data_type": "decimal", "default_value": "0", "sort_order": 8},
    {"fact_key": "m1_8_add_6_to_7", "label": "8 — Add lines 6 and 7", "data_type": "decimal", "sort_order": 9,
     "notes": "OUTPUT. 8 = 6a + 7a."},
    {"fact_key": "m1_9_income", "label": "9 — Income (loss) = line 5 − line 8 (= Analysis line 1)",
     "data_type": "decimal", "sort_order": 10,
     "notes": "OUTPUT. 9 = 5 − 8 → Analysis of Net Income line 1 (= SCH_K_1065 k_analysis_net_income = M-2 line 3)."},
    {"fact_key": "m_schb_q4_small", "label": "Schedule B Q4 — small-partnership exemption met? (suppresses M-1)",
     "data_type": "boolean", "default_value": "false", "sort_order": 20,
     "notes": "Receipts < $250k AND assets < $1M AND timely K-1s AND not-M-3. If true, M-1 not required (D_M1_EXEMPT)."},
]

M1_RULES: list[dict] = [
    {"rule_id": "R-M1-3", "title": "Line 3 guaranteed payments = Schedule K line 4c", "rule_type": "calculation",
     "precedence": 1, "sort_order": 1,
     "formula": ("M-1 line 3 (guaranteed payments other than health insurance) = Schedule K line 4c (total "
                 "guaranteed payments). A return deduction that is not a book expense — added back on the "
                 "book→return bridge. tts M1_3 = K4c."),
     "inputs": ["m1_3_guaranteed_payments"], "outputs": [],
     "description": "f1065 M-1 line 3. YELLOW pull from Sch K 4c."},
    {"rule_id": "R-M1-5", "title": "Line 5 = add lines 1 through 4", "rule_type": "calculation",
     "precedence": 2, "sort_order": 2,
     "formula": "5 = line 1 (book income) + line 2 (income on K not on books) + line 3 (guaranteed payments) "
                "+ line 4a (book depreciation) + line 4b (travel/entertainment).",
     "inputs": ["m1_1_book_income", "m1_2_income_on_k_not_books", "m1_3_guaranteed_payments",
                "m1_4a_depreciation", "m1_4b_travel_entertainment"],
     "outputs": ["m1_5_add_1_to_4"], "description": "f1065 M-1 line 5."},
    {"rule_id": "R-M1-8", "title": "Line 8 = add lines 6 and 7", "rule_type": "calculation",
     "precedence": 3, "sort_order": 3,
     "formula": "8 = line 6a (tax-exempt interest on books not on Sch K) + line 7a (Sch K depreciation not "
                "charged against book income).",
     "inputs": ["m1_6a_taxexempt_interest", "m1_7a_depreciation"], "outputs": ["m1_8_add_6_to_7"],
     "description": "f1065 M-1 line 8."},
    {"rule_id": "R-M1-9", "title": "Line 9 = line 5 − line 8 → Analysis of Net Income line 1",
     "rule_type": "calculation", "precedence": 4, "sort_order": 4,
     "formula": ("9 = line 5 − line 8. The face labels this 'Income (loss) (Analysis of Net Income (Loss) "
                 "per Return, line 1)' — so M-1 line 9 MUST equal SCH_K_1065 Analysis of Net Income line 1 "
                 "(RECON-M1-ANALYSIS) and Schedule M-2 line 3. ⚠ tts computes NO 1065 Analysis line "
                 "(spine reconcile gap #6) — the Analysis compute must be built for this tie to hold "
                 "(D_M1_ANALYSIS)."),
     "inputs": ["m1_5_add_1_to_4", "m1_8_add_6_to_7"], "outputs": ["m1_9_income"],
     "description": "f1065 M-1 line 9 = Analysis line 1. The load-bearing book↔return tie."},
    {"rule_id": "R-M1-EXEMPT", "title": "Schedule B Q4 small-partnership exemption suppresses M-1",
     "rule_type": "conditional", "precedence": 5, "sort_order": 5,
     "formula": ("If Schedule B Q4 is 'Yes' (total receipts < $250,000 AND total assets < $1,000,000 AND "
                 "Schedules K-1 timely filed/furnished AND not required to file Schedule M-3), the "
                 "partnership is NOT required to complete Schedule M-1. D_M1_EXEMPT surfaces the "
                 "suppression; the schedule may be left blank."),
     "inputs": ["m_schb_q4_small"], "outputs": [],
     "description": "i1065 Schedule B Q4. Gating."},
]

M1_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-M1-3", "IRS_2025_F1065", "primary", "f1065 M-1 line 3 guaranteed payments"),
    ("R-M1-5", "IRS_2025_F1065", "primary", "f1065 M-1 line 5 = Σ lines 1-4"),
    ("R-M1-8", "IRS_2025_F1065", "primary", "f1065 M-1 line 8 = Σ lines 6-7"),
    ("R-M1-9", "IRS_2025_F1065", "primary", "f1065 M-1 line 9 = 5 − 8 = Analysis line 1 (face verbatim)"),
    ("R-M1-9", "IRC_702", "secondary", "§702(a)/(b) — the separately-stated return items Analysis line 1 combines"),
    ("R-M1-EXEMPT", "IRS_2025_I1065", "primary", "i1065 Schedule B Q4 small-partnership exemption"),
]

M1_LINES: list[dict] = [
    {"line_number": "1", "description": "Net income (loss) per books", "line_type": "input", "sort_order": 1,
     "source_facts": ["m1_1_book_income"]},
    {"line_number": "2", "description": "Income on Schedule K (1,2,3c,5,6a,7,8,9a,10,11) not recorded on books",
     "line_type": "input", "sort_order": 2, "source_facts": ["m1_2_income_on_k_not_books"]},
    {"line_number": "3", "description": "Guaranteed payments (other than health insurance)", "line_type": "calculated",
     "sort_order": 3, "source_facts": ["m1_3_guaranteed_payments"], "source_rules": ["R-M1-3"]},
    {"line_number": "4a", "description": "Expenses on books not on Sch K — depreciation", "line_type": "input",
     "sort_order": 4, "source_facts": ["m1_4a_depreciation"]},
    {"line_number": "4b", "description": "Expenses on books not on Sch K — travel and entertainment",
     "line_type": "input", "sort_order": 5, "source_facts": ["m1_4b_travel_entertainment"]},
    {"line_number": "5", "description": "Add lines 1 through 4", "line_type": "subtotal", "sort_order": 6,
     "source_rules": ["R-M1-5"]},
    {"line_number": "6a", "description": "Income on books not on Sch K — tax-exempt interest", "line_type": "input",
     "sort_order": 7, "source_facts": ["m1_6a_taxexempt_interest"]},
    {"line_number": "7a", "description": "Deductions on Sch K not charged against book income — depreciation",
     "line_type": "input", "sort_order": 8, "source_facts": ["m1_7a_depreciation"]},
    {"line_number": "8", "description": "Add lines 6 and 7", "line_type": "subtotal", "sort_order": 9,
     "source_rules": ["R-M1-8"]},
    {"line_number": "9", "description": "Income (loss) (Analysis of Net Income line 1) = line 5 − line 8",
     "line_type": "total", "sort_order": 10, "source_rules": ["R-M1-9"], "destination_form": "1065_M2",
     "notes": "= Analysis of Net Income line 1 = M-2 line 3."},
]

M1_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_M1_ANALYSIS", "title": "M-1 line 9 must equal Analysis of Net Income line 1", "severity": "error",
     "condition": "m1_9_income != SCH_K_1065.k_analysis_net_income",
     "message": ("Schedule M-1 line 9 must equal the Analysis of Net Income (Loss) per Return, line 1 (the "
                 "face says so). Confirm the reconciliation ties. NOTE: tts does not yet compute the 1065 "
                 "Analysis of Net Income (spine reconcile gap) — that compute must be built for this tie to "
                 "hold; until then M-1 line 9 is the reconciliation's own output."),
     "notes": "Backs RECON-M1-ANALYSIS. Cross-refs the spine Analysis build-gap."},
    {"diagnostic_id": "D_M1_EXEMPT", "title": "Small-partnership exemption — Schedule M-1 not required", "severity": "info",
     "condition": "m_schb_q4_small is True",
     "message": ("Schedule B question 4 is answered 'Yes' (receipts < $250,000, assets < $1,000,000, timely "
                 "K-1s, not M-3): the partnership is not required to complete Schedule M-1. Any entries here "
                 "are optional."),
     "notes": "i1065 Q4 gating."},
]

M1_SCENARIOS: list[dict] = [
    {"scenario_name": "M1-1 — book→return reconciliation (9 = 5 − 8)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"m1_1_book_income": 200000, "m1_2_income_on_k_not_books": 5000, "m1_3_guaranteed_payments": 100000,
                "m1_4a_depreciation": 10000, "m1_4b_travel_entertainment": 3000,
                "m1_6a_taxexempt_interest": 2000, "m1_7a_depreciation": 18000},
     "expected_outputs": {"m1_5_add_1_to_4": 318000, "m1_8_add_6_to_7": 20000, "m1_9_income": 298000},
     "notes": "5 = 200k+5k+100k+10k+3k = 318k; 8 = 2k+18k = 20k; 9 = 318k−20k = 298k → Analysis line 1."},
    {"scenario_name": "M1-2 — guaranteed payments pull (line 3 = K4c)", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"m1_1_book_income": 50000, "m1_3_guaranteed_payments": 75000},
     "expected_outputs": {"m1_5_add_1_to_4": 125000, "m1_9_income": 125000},
     "notes": "GP 75k (= Sch K 4c) added on the book→return bridge: 5 = 50k+75k = 125k; 8 = 0; 9 = 125k."},
    {"scenario_name": "M1-3 — small-partnership exemption (Q4) → not required", "scenario_type": "edge", "sort_order": 3,
     "inputs": {"m_schb_q4_small": True, "m1_1_book_income": 40000},
     "expected_outputs": {"D_M1_EXEMPT": True},
     "notes": "Q4 met → D_M1_EXEMPT (info); M-1 optional."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 2: 1065_M2 — Schedule M-2 (partners' capital accounts, tax basis)
# ═══════════════════════════════════════════════════════════════════════════

M2_IDENTITY = {
    "form_number": "1065_M2",
    "entity_types": ["1065"],
    "form_title": "Schedule M-2 (Form 1065, 2025) — Analysis of Partners' Capital Accounts (Tax Basis)",
    "notes": (
        "FRESH-AUTHORED 2026-07-04 (1065-core, form 3) from the FINAL 2025 f1065 page 6 (pymupdf verbatim). "
        "M-2 tax-basis partners' capital (§705 transactional): 5 = Σ(1-4); 8 = Σ(6-7); 9 = 5 − 8 = ending "
        "capital. Line 3 net income (loss) '(see instructions)' = Analysis of Net Income line 1 = M-1 line 9 "
        "(R-M2-3-TIE). Line 1 beginning capital = Σ K-1 item L beginning tax-basis capital (R-M2-1-TIE). "
        "⚠ RECONCILE: tts M2_3 is labeled 'per books' and is DATA-ENTRY (should tie to M1_9/Analysis line 1 "
        "— candidate tts fix, D_M2_3); tts item-L roll-forward is RED-deferred (K-1 leg) so M2_1 cannot "
        "auto-derive (D_M2_1). Schedule B Q4 small-partnership exemption suppresses M-2 (D_M2_EXEMPT). "
        "READY_TO_SEED=False."
    ),
}

M2_FACTS: list[dict] = [
    {"fact_key": "m2_1_boy", "label": "1 — Balance at beginning of year (tax basis)", "data_type": "decimal",
     "default_value": "0", "sort_order": 1,
     "notes": "= Σ K-1 item L beginning tax-basis capital (R-M2-1-TIE). tts item-L roll-forward RED-deferred "
              "→ data-entry (D_M2_1)."},
    {"fact_key": "m2_2a_contrib_cash", "label": "2a — Capital contributed: cash", "data_type": "decimal",
     "default_value": "0", "sort_order": 2},
    {"fact_key": "m2_2b_contrib_property", "label": "2b — Capital contributed: property", "data_type": "decimal",
     "default_value": "0", "sort_order": 3, "notes": "Net of liabilities (tax basis)."},
    {"fact_key": "m2_3_net_income", "label": "3 — Net income (loss) (= Analysis line 1 = M-1 line 9)",
     "data_type": "decimal", "default_value": "0", "sort_order": 4,
     "notes": "Face: '(see instructions)' = Analysis of Net Income line 1 = M-1 line 9 (per RETURN, tax "
              "basis). ⚠ tts labels this 'per books' + takes it as data-entry — candidate tts fix (D_M2_3)."},
    {"fact_key": "m2_4_other_increases", "label": "4 — Other increases (itemize)", "data_type": "decimal",
     "default_value": "0", "sort_order": 5, "notes": "e.g. tax-exempt income adjustments to reach tax-basis capital."},
    {"fact_key": "m2_5_add_1_to_4", "label": "5 — Add lines 1 through 4", "data_type": "decimal", "sort_order": 6,
     "notes": "OUTPUT. 5 = 1 + 2a + 2b + 3 + 4."},
    {"fact_key": "m2_6a_dist_cash", "label": "6a — Distributions: cash", "data_type": "decimal", "default_value": "0",
     "sort_order": 7, "notes": "= Σ K-1 box 19a (distributions)."},
    {"fact_key": "m2_6b_dist_property", "label": "6b — Distributions: property", "data_type": "decimal",
     "default_value": "0", "sort_order": 8},
    {"fact_key": "m2_7_other_decreases", "label": "7 — Other decreases (itemize)", "data_type": "decimal",
     "default_value": "0", "sort_order": 9, "notes": "e.g. nondeductible expenses reducing tax-basis capital."},
    {"fact_key": "m2_8_add_6_to_7", "label": "8 — Add lines 6 and 7", "data_type": "decimal", "sort_order": 10,
     "notes": "OUTPUT. 8 = 6a + 6b + 7."},
    {"fact_key": "m2_9_eoy", "label": "9 — Balance at end of year = line 5 − line 8", "data_type": "decimal",
     "sort_order": 11, "notes": "OUTPUT. 9 = 5 − 8 = Σ K-1 item L ending tax-basis capital."},
    {"fact_key": "m_schb_q4_small", "label": "Schedule B Q4 — small-partnership exemption met? (suppresses M-2)",
     "data_type": "boolean", "default_value": "false", "sort_order": 20,
     "notes": "Same gating fact as M-1/L. If true, M-2 not required (D_M2_EXEMPT)."},
]

M2_RULES: list[dict] = [
    {"rule_id": "R-M2-5", "title": "Line 5 = add lines 1 through 4", "rule_type": "calculation",
     "precedence": 1, "sort_order": 1,
     "formula": "5 = line 1 (BOY) + line 2a (cash contributed) + line 2b (property contributed) + line 3 "
                "(net income) + line 4 (other increases).",
     "inputs": ["m2_1_boy", "m2_2a_contrib_cash", "m2_2b_contrib_property", "m2_3_net_income", "m2_4_other_increases"],
     "outputs": ["m2_5_add_1_to_4"], "description": "f1065 M-2 line 5."},
    {"rule_id": "R-M2-8", "title": "Line 8 = add lines 6 and 7", "rule_type": "calculation",
     "precedence": 2, "sort_order": 2,
     "formula": "8 = line 6a (cash distributions) + line 6b (property distributions) + line 7 (other decreases).",
     "inputs": ["m2_6a_dist_cash", "m2_6b_dist_property", "m2_7_other_decreases"], "outputs": ["m2_8_add_6_to_7"],
     "description": "f1065 M-2 line 8."},
    {"rule_id": "R-M2-9", "title": "Line 9 = line 5 − line 8 (ending capital)", "rule_type": "calculation",
     "precedence": 3, "sort_order": 3,
     "formula": ("9 = line 5 − line 8 = ending tax-basis partners' capital. Ties to Σ K-1 item L ending "
                 "capital and to Schedule L line 21 col (d) if Schedule L is maintained on the tax basis."),
     "inputs": ["m2_5_add_1_to_4", "m2_8_add_6_to_7"], "outputs": ["m2_9_eoy"],
     "description": "f1065 M-2 line 9."},
    {"rule_id": "R-M2-3-TIE", "title": "Line 3 net income = Analysis line 1 = M-1 line 9 (tax basis)",
     "rule_type": "validation", "precedence": 4, "sort_order": 4,
     "formula": ("M-2 line 3 'Net income (loss) (see instructions)' = the Analysis of Net Income (Loss) per "
                 "Return, line 1 = Schedule M-1 line 9 (per RETURN, on the tax-basis M-2). §705 transactional "
                 "roll-forward: the distributive-share income increases tax-basis capital. ⚠ RECONCILE: tts "
                 "labels M2_3 'Net income (loss) per books' and takes it as a free DATA-ENTRY input rather "
                 "than tying it to M1_9/Analysis line 1 — a candidate tts fix (D_M2_3); Ken adjudicates."),
     "inputs": ["m2_3_net_income"], "outputs": [],
     "description": "f1065 M-2 line 3 = Analysis line 1. Reconcile adjudication (tts M2_3 mis-source)."},
    {"rule_id": "R-M2-1-TIE", "title": "Line 1 beginning capital = Σ K-1 item L beginning tax-basis capital",
     "rule_type": "validation", "precedence": 5, "sort_order": 5,
     "formula": ("M-2 line 1 (beginning capital) = the sum over partners of Schedule K-1 item L beginning "
                 "tax-basis capital (§705/§722 transactional). ⚠ RECONCILE: tts stores K-1 item L as "
                 "data-entry with NO roll-forward compute (K-1 leg D_K1_ITEML), so M-2 line 1 cannot "
                 "auto-derive from the K-1s this season — it is data-entry (D_M2_1). The item-L "
                 "roll-forward compute is the path to auto-deriving M-2 line 1."),
     "inputs": ["m2_1_boy"], "outputs": [],
     "description": "M-2 line 1 = Σ K-1 item L beginning. Carries the K-1 item-L RED-defer home."},
    {"rule_id": "R-M2-EXEMPT", "title": "Schedule B Q4 small-partnership exemption suppresses M-2",
     "rule_type": "conditional", "precedence": 6, "sort_order": 6,
     "formula": ("If Schedule B Q4 is 'Yes' (receipts < $250,000 AND assets < $1,000,000 AND timely K-1s "
                 "AND not-M-3), the partnership is NOT required to complete Schedule M-2 (or item L on the "
                 "K-1). D_M2_EXEMPT surfaces the suppression."),
     "inputs": ["m_schb_q4_small"], "outputs": [],
     "description": "i1065 Schedule B Q4. Gating (same as M-1/L)."},
]

M2_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-M2-5", "IRS_2025_F1065", "primary", "f1065 M-2 line 5 = Σ lines 1-4"),
    ("R-M2-8", "IRS_2025_F1065", "primary", "f1065 M-2 line 8 = Σ lines 6-7"),
    ("R-M2-9", "IRS_2025_F1065", "primary", "f1065 M-2 line 9 = 5 − 8 (ending capital)"),
    ("R-M2-3-TIE", "IRS_2025_I1065", "primary", "i1065 M-2 line 3 net income = Analysis line 1 (see instructions)"),
    ("R-M2-3-TIE", "IRC_705", "secondary", "§705 distributive-share income increases tax-basis capital"),
    ("R-M2-1-TIE", "IRC_705", "primary", "§705(a)/§722 transactional beginning tax-basis capital"),
    ("R-M2-1-TIE", "IRS_2025_F1065", "secondary", "f1065 M-2 line 1 = Σ K-1 item L beginning tax-basis capital"),
    ("R-M2-EXEMPT", "IRS_2025_I1065", "primary", "i1065 Schedule B Q4 small-partnership exemption"),
]

M2_LINES: list[dict] = [
    {"line_number": "1", "description": "Balance at beginning of year (tax basis)", "line_type": "input",
     "sort_order": 1, "source_facts": ["m2_1_boy"], "source_rules": ["R-M2-1-TIE"]},
    {"line_number": "2a", "description": "Capital contributed: cash", "line_type": "input", "sort_order": 2,
     "source_facts": ["m2_2a_contrib_cash"]},
    {"line_number": "2b", "description": "Capital contributed: property", "line_type": "input", "sort_order": 3,
     "source_facts": ["m2_2b_contrib_property"]},
    {"line_number": "3", "description": "Net income (loss) (see instructions = Analysis line 1 = M-1 line 9)",
     "line_type": "calculated", "sort_order": 4, "source_facts": ["m2_3_net_income"], "source_rules": ["R-M2-3-TIE"]},
    {"line_number": "4", "description": "Other increases (itemize)", "line_type": "input", "sort_order": 5,
     "source_facts": ["m2_4_other_increases"]},
    {"line_number": "5", "description": "Add lines 1 through 4", "line_type": "subtotal", "sort_order": 6,
     "source_rules": ["R-M2-5"]},
    {"line_number": "6a", "description": "Distributions: cash", "line_type": "input", "sort_order": 7,
     "source_facts": ["m2_6a_dist_cash"]},
    {"line_number": "6b", "description": "Distributions: property", "line_type": "input", "sort_order": 8,
     "source_facts": ["m2_6b_dist_property"]},
    {"line_number": "7", "description": "Other decreases (itemize)", "line_type": "input", "sort_order": 9,
     "source_facts": ["m2_7_other_decreases"]},
    {"line_number": "8", "description": "Add lines 6 and 7", "line_type": "subtotal", "sort_order": 10,
     "source_rules": ["R-M2-8"]},
    {"line_number": "9", "description": "Balance at end of year = line 5 − line 8", "line_type": "total",
     "sort_order": 11, "source_rules": ["R-M2-9"], "notes": "= Σ K-1 item L ending tax-basis capital."},
]

M2_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_M2_3", "title": "M-2 line 3 net income should tie to Analysis line 1 / M-1 line 9",
     "severity": "warning",
     "condition": "m2_3_net_income != 1065_M1.m1_9_income (Analysis line 1)",
     "message": ("Schedule M-2 line 3 'Net income (loss) (see instructions)' should equal the Analysis of "
                 "Net Income line 1 = Schedule M-1 line 9 (per return, tax basis). RECONCILE NOTE: tts "
                 "currently labels this 'Net income (loss) per books' and takes it as a free data-entry — "
                 "confirm it ties to the return amount (candidate tts correction, akin to the net-farm fix)."),
     "notes": "Reconcile adjudication #1 (M2_3 mis-source). Ken call."},
    {"diagnostic_id": "D_M2_1", "title": "M-2 line 1 should equal Σ K-1 item L beginning capital", "severity": "info",
     "condition": "m2_1_boy != sum over partners of SCHEDULE_K1_1065.k1_cap_boy",
     "message": ("Schedule M-2 line 1 (beginning tax-basis capital) should equal the sum of each partner's "
                 "Schedule K-1 item L beginning capital. tts stores item L as data-entry with no "
                 "roll-forward compute (K-1 leg gap), so this cannot auto-derive yet — verify the tie "
                 "manually. Building the item-L roll-forward is the path to auto-deriving M-2 line 1."),
     "notes": "Carries the K-1 item-L RED-defer (D_K1_ITEML) home to M-2 line 1."},
    {"diagnostic_id": "D_M2_EXEMPT", "title": "Small-partnership exemption — Schedule M-2 not required", "severity": "info",
     "condition": "m_schb_q4_small is True",
     "message": ("Schedule B question 4 is 'Yes' (receipts < $250,000, assets < $1,000,000, timely K-1s, "
                 "not M-3): the partnership is not required to complete Schedule M-2 or item L on the K-1."),
     "notes": "i1065 Q4 gating."},
]

M2_SCENARIOS: list[dict] = [
    {"scenario_name": "M2-1 — capital roll-forward (9 = 5 − 8)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"m2_1_boy": 500000, "m2_2a_contrib_cash": 50000, "m2_2b_contrib_property": 0,
                "m2_3_net_income": 298000, "m2_4_other_increases": 0,
                "m2_6a_dist_cash": 120000, "m2_6b_dist_property": 0, "m2_7_other_decreases": 0},
     "expected_outputs": {"m2_5_add_1_to_4": 848000, "m2_8_add_6_to_7": 120000, "m2_9_eoy": 728000},
     "notes": "5 = 500k+50k+298k = 848k; 8 = 120k; 9 = 848k−120k = 728k ending capital."},
    {"scenario_name": "M2-2 — line 3 net income ties to M-1 line 9 / Analysis line 1", "scenario_type": "normal",
     "sort_order": 2,
     "inputs": {"m2_1_boy": 100000, "m2_3_net_income": 215000},
     "expected_outputs": {"m2_5_add_1_to_4": 315000},
     "notes": "M-2 line 3 = 215k = Analysis line 1 (from SCH_K_1065 K-4 scenario) = M-1 line 9; 5 = 100k+215k = 315k."},
    {"scenario_name": "M2-3 — small-partnership exemption (Q4) → not required", "scenario_type": "edge", "sort_order": 3,
     "inputs": {"m_schb_q4_small": True, "m2_1_boy": 30000},
     "expected_outputs": {"D_M2_EXEMPT": True},
     "notes": "Q4 met → D_M2_EXEMPT (info); M-2 + K-1 item L optional."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS (cross-form ties)
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "RECON-M1-ANALYSIS", "assertion_type": "reconciliation", "entity_types": ["1065"],
     "status": "active",
     "title": "Schedule M-1 line 9 = Analysis of Net Income (Loss) per Return, line 1",
     "description": ("The face labels M-1 line 9 'Income (loss) (Analysis of Net Income (Loss) per Return, "
                     "line 1)'. So M-1 line 9 (= line 5 − line 8) must equal SCH_K_1065 Analysis of Net "
                     "Income line 1 (R-SCHK-ANALYSIS) and Schedule M-2 line 3. NOTE: tts does not yet "
                     "compute the 1065 Analysis — that build-gap must be closed for this tie to hold."),
     "definition": {"kind": "reconciliation", "form": "1065_M1",
                    "formula": "1065_M1.m1_9_income == SCH_K_1065.k_analysis_net_income == 1065_M2.m2_3_net_income",
                    "note": "the book↔return tie; tts 1065 Analysis compute is a build-gap (spine #6)"},
     "bug_reference": "tts computes no 1065 Analysis of Net Income (K18 is 1120-S-only)", "sort_order": 1},
    {"assertion_id": "RECON-M2-CAPITAL", "assertion_type": "reconciliation", "entity_types": ["1065"],
     "status": "active",
     "title": "M-2 rolls forward and ties to K-1 item L (beginning + ending)",
     "description": ("M-2 line 1 = Σ K-1 item L beginning tax-basis capital; M-2 line 9 (= 5 − 8) = Σ K-1 "
                     "item L ending tax-basis capital; M-2 line 3 = Analysis line 1 = M-1 line 9. §705 "
                     "transactional. NOTE: tts item-L roll-forward is RED-deferred (K-1 leg), so the "
                     "K-1↔M-2 auto-tie is not yet computable — data-entry with this invariant as the check."),
     "definition": {"kind": "reconciliation", "form": "1065_M2",
                    "formula": "m2_1_boy == sum(k1_cap_boy over partners); m2_9_eoy == sum(k1_cap_eoy over partners); "
                               "m2_3_net_income == 1065_M1.m1_9_income",
                    "note": "carries the K-1 item-L RED-defer (D_K1_ITEML) home"},
     "bug_reference": "tts item L is data-entry (no roll-forward compute)", "sort_order": 2},
    {"assertion_id": "GATE-SMALL-PARTNERSHIP", "assertion_type": "gating_check", "entity_types": ["1065"],
     "status": "active",
     "title": "Schedule B Q4 small-partnership exemption → M-1/M-2 (and L, K-1 item L) not required",
     "description": ("When Schedule B Q4 is 'Yes' (receipts < $250,000 AND assets < $1,000,000 AND timely "
                     "K-1s AND not-M-3-required), Schedules L, M-1, M-2, item F, and K-1 item L are not "
                     "required — D_M1_EXEMPT / D_M2_EXEMPT fire. The studio does not demand a balance sheet "
                     "or reconciliation that isn't required."),
     "definition": {"kind": "gating_check", "form": "1065_M2", "expect": {"exemption_suppresses": True},
                    "when": "m_schb_q4_small is True",
                    "note": "receipts<$250k AND assets<$1M AND timely K-1s AND not-M-3 (i1065 Q4)"},
     "bug_reference": "", "sort_order": 3},
]


class Command(BaseCommand):
    help = ("Load the 1065 Schedule M-1 + M-2 spec (1065_M1 + 1065_M2). Fresh-authored from the FINAL "
            "2025 f1065 page 6 (pymupdf verbatim) + primary IRC (§705/§702). Reconciled against tts "
            "compute FORMULAS_1065 M-1/M-2. Refuses until READY_TO_SEED=True (awaits the Ken walk per D-1).")

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad 1065 Schedule M-1 + M-2 (1065_M1 + 1065_M2)\n"))
        self._load_topics()
        sources = self._load_sources()
        m1 = self._upsert_form(M1_IDENTITY)
        m1_rules = self._upsert_rules(m1, M1_RULES)
        self._upsert_facts(m1, M1_FACTS)
        self._upsert_authority_links(m1_rules, sources, M1_RULE_LINKS)
        self._upsert_lines(m1, M1_LINES)
        self._upsert_diagnostics(m1, M1_DIAGNOSTICS)
        self._upsert_tests(m1, M1_SCENARIOS)
        m2 = self._upsert_form(M2_IDENTITY)
        m2_rules = self._upsert_rules(m2, M2_RULES)
        self._upsert_facts(m2, M2_FACTS)
        self._upsert_authority_links(m2_rules, sources, M2_RULE_LINKS)
        self._upsert_lines(m2, M2_LINES)
        self._upsert_diagnostics(m2, M2_DIAGNOSTICS)
        self._upsert_tests(m2, M2_SCENARIOS)
        self._upsert_form_links(sources)
        self._load_flow_assertions()
        self._report_totals([m1, m2])

    def _guard_against_hollow_seed(self):
        empty = []
        checks = (
            ("sources", AUTHORITY_SOURCES),
            ("m1.facts", M1_FACTS), ("m1.rules", M1_RULES), ("m1.lines", M1_LINES),
            ("m1.diagnostics", M1_DIAGNOSTICS), ("m1.scenarios", M1_SCENARIOS), ("m1.rule_links", M1_RULE_LINKS),
            ("m2.facts", M2_FACTS), ("m2.rules", M2_RULES), ("m2.lines", M2_LINES),
            ("m2.diagnostics", M2_DIAGNOSTICS), ("m2.scenarios", M2_SCENARIOS), ("m2.rule_links", M2_RULE_LINKS),
            ("flow_assertions", FLOW_ASSERTIONS),
        )
        for name, seq in checks:
            if not seq:
                empty.append(f"1065_m1m2.{name}")
        if not READY_TO_SEED or empty:
            still_empty = "\n  ".join(f"- {n}" for n in empty) or "(all populated)"
            raise CommandError(
                "\nREFUSING TO SEED 1065 M-1/M-2: not cleared to seed.\n\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True — flip only after the Ken walk, D-1)\n\n"
                f"Currently empty / placeholder:\n  {still_empty}\n"
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
            source, _ = AuthoritySource.objects.update_or_create(
                source_code=src_data["source_code"], defaults=src_data)
            sources[source.source_code] = source
            for exc in excerpts_data:
                exc = dict(exc)
                AuthorityExcerpt.objects.update_or_create(
                    authority_source=source, excerpt_label=exc["excerpt_label"], defaults=exc)
            for tc in topic_codes:
                topic = AuthorityTopic.objects.filter(topic_code=tc).first()
                if topic:
                    AuthoritySourceTopic.objects.get_or_create(authority_source=source, authority_topic=topic)
        self.stdout.write(f"Sources ready: {len(sources)}")
        return sources

    def _upsert_form(self, identity: dict) -> TaxForm:
        form, created = TaxForm.objects.update_or_create(
            form_number=identity["form_number"], jurisdiction=FORM_JURISDICTION,
            tax_year=FORM_TAX_YEAR, version=FORM_VERSION,
            defaults={"form_title": identity["form_title"], "entity_types": identity["entity_types"],
                      "status": FORM_STATUS, "notes": identity["notes"]})
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
                    defaults={"support_level": level, "relevance_note": note})
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
                    defaults={"note": f"{source_code} -> {form_code}"})

    def _load_flow_assertions(self):
        for a in FLOW_ASSERTIONS:
            a = dict(a)
            FlowAssertion.objects.update_or_create(assertion_id=a.pop("assertion_id"), defaults=a)
        self.stdout.write(f"  {len(FLOW_ASSERTIONS)} flow assertions")

    def _report_totals(self, forms):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(f"TaxForms: {TaxForm.objects.count()} | FlowAssertions: {FlowAssertion.objects.count()}")
        for form in forms:
            uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
            self.stdout.write(f"{form.form_number}: all rules cited" if not uncited
                              else self.style.WARNING(f"{form.form_number} uncited rules: {len(uncited)}"))
