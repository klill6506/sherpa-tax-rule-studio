"""
Load the Form 1040-X spec — Amended U.S. Individual Income Tax Return (TY2025).

WHAT 1040-X IS (the architecture that matters)
----------------------------------------------
1040-X is not a normal compute form — it is a THREE-COLUMN DELTA. For each
affected 1040 line:
  • Column A  = the amount on the return AS ORIGINALLY FILED (or as previously
                adjusted by the IRS) — sourced from a FROZEN as-filed baseline
                snapshot of the original return (tts: AsFiledBaseline).
  • Column C  = the CORRECT amount — sourced from the amended (corrected) 1040.
  • Column B  = the NET CHANGE = Column C − Column A (increase or decrease).
Plus a Part II free-text "Explanation of Changes", a recomputed refund-due /
amount-owed (lines 16-23), and a Part I dependents recap (lines 24-30).

LINE SET (verified against the actual Form 1040-X, Rev. December 2025 PDF — read
directly from resources/irs_forms/2025/f1040x.pdf, NOT memory):
  INCOME & DEDUCTIONS (A/B/C):
    1   Adjusted gross income (NOL carryback → explain in Part II)
    2   Itemized deductions or standard deduction
    3   Subtract line 2 from line 1
    4a  Qualified business income deduction
    4b  Deductions for tips, overtime, car loan interest, and seniors
        (Schedule 1-A, Form 1040)  ← OBBBA
    5   Taxable income = line 3 − (line 4a + line 4b)
  TAX LIABILITY (A/B/C):
    6   Tax (+ method[s] used)            7  Nonrefundable credits
    8   line 6 − line 7 (≥ 0)            9  Reserved for future use
    10  Other taxes                      11 Total tax = line 8 + line 10
  PAYMENTS (A/B/C):
    12  Federal income tax withheld + excess SS / tier-1 RRTA
    13  Estimated tax payments (incl. prior-year applied)
    14  Earned income credit (EIC)
    15  Refundable credits from Schedule 8812 / Form(s) 2439 / 4136 / etc.
  REFUND OR AMOUNT YOU OWE (single column — the amended bottom line):
    16  Total paid with extension/original + additional payments after filing
    17  Total payments = (lines 12-15, column C) + line 16
    18  Overpayment, if any, on the original return / as previously adjusted
    19  Subtract line 18 from line 17
    20  Amount you owe        (if line 11 column C > line 19)
    21  Overpayment on this return (if line 11 column C < line 19)
    22  Amount of line 21 refunded to you
    23  Amount of line 21 applied to next year's estimated tax (enter year)
  PART I — DEPENDENTS (A/B/C; 24/26/28/29 reserved):
    25  Your dependent children who lived with you (number)
    27  Other dependents (number)        30  List ALL dependents (table)
  PART II — Explanation of Changes (free text; REQUIRED).

═══════════════════════════════════════════════════════════════════════════
v1 SCOPE — the common amendment (compute leg is HELD for Ken's review)
═══════════════════════════════════════════════════════════════════════════
IN (v1, when the compute leg is built):
  • Change income / deductions / credits / payments on the corrected 1040,
    capture Column A from the frozen as-filed baseline, compute Column B = C − A
    per line, recompute the subtotals (3, 5, 8, 11) and the refund-due /
    amount-owed (17, 19, 20, 21), surface the Part II explanation.
RED-DEFERRED (each its own "Not supported — prepare manually" RED, never silent):
  • NOL carryback claims (line 1 NOL carryback / Form 1045 territory) — D_1040X_001.
  • General business credit carryback (line 7) — D_1040X_002.
  • Superseding returns (filed before the due date — different mechanics, not a
    1040-X) — D_1040X_003.
  • Amendment-driven cascades beyond the common set (e.g. re-running Form 8962
    PTC reconciliation, a fresh EIC qualification adjudication, multi-form
    recomputation chains) — D_1040X_008.
  • Interest and penalties are OUT of scope by design (the IRS bills them; the
    preparer handles) — D_1040X_007 (info).

═══════════════════════════════════════════════════════════════════════════
requires_human_review WALK ITEMS (for Ken's in-session review — READY_TO_SEED
stays False until he approves)
═══════════════════════════════════════════════════════════════════════════
W1. AS-FILED BASELINE (Column A source) — the architecture. Column A must come
    from a FROZEN snapshot of the original return captured at "mark as filed"
    time (tts model AsFiledBaseline — see DECISIONS.md). CONFIRM: amend-in-place
    (one return, a baseline freezes the original, Column C = the now-corrected
    live values) vs a separate amended-return clone. v1 recommendation =
    amend-in-place + a dedicated baseline table (mirrors PriorYearReturn + the
    snapshot-copy philosophy).
W2. COLUMN-B SEMANTICS. Column B = Column C − Column A on every A/B/C line, and
    the form's recompute (lines 3/5/8/11/17/19) operates per column. CONFIRM the
    sign convention (B is a signed increase/decrease; line 5 floors column C at
    -0-; line 8 floors at 0) and that no interest/penalty enters the math.
W3. REFUND-ALREADY-RECEIVED vs ADDITIONAL-TAX-OWED. Line 18 (overpayment on the
    original return) and line 16 (amounts already paid) drive whether the
    amendment yields an additional refund (line 21→22) or balance owed (line 20).
    CONFIRM the line 17-23 arithmetic and the "if less than zero, see
    instructions" branch on line 19.
W4. v1 IN/OUT SCOPE FORKS. CONFIRM the RED-deferral list above is the right v1
    boundary: (a) NOL carrybacks out; (b) general-business-credit carrybacks
    out; (c) superseding returns out; (d) PTC/EIC/multi-form recompute cascades
    out (the common case recomputes tax + refund/owe from the changed lines, but
    does NOT re-adjudicate eligibility for other credits). Is there a common
    amendment archetype at the firm (heavy EIC / retiree) that needs a cascade
    IN for v1?
W5. YEAR HANDLING. 1040-X is year-keyed: amending a TY2025 return uses TY2025
    rules; the corrected 1040 it attaches to carries the year. CONFIRM the
    parameterization (no 1040-X-specific constants — it is pure structure +
    arithmetic; the tax recompute reuses the amended 1040's own year rules).
W6. EXPLANATION-OF-CHANGES REQUIREMENT. Part II free text is REQUIRED on every
    1040-X (D_1040X_004 errors when blank). CONFIRM that's the right severity
    (error vs warning) and whether per-line explanation prompts are wanted.

NOTE — this is the SPEC + SCAFFOLD pass only. READY_TO_SEED = False. The rules
below are AUTHORED for Ken's review; the delta-compute leg is built only after
he approves. Do NOT seed or build compute against this unapproved spec.
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
# SAFETY GUARD — flip ONLY after Ken's in-session review walk (W1–W6 above).
#
# FLIPPED 2026-06-25 — Ken APPROVED the review walk in-session: W1 amend-in-place +
# a dedicated as-filed baseline table (snapshot-copy, not a separate amended-return
# clone) blessed; W2 the column-B delta semantics (B = C − A per column; line 5 col C
# floored at -0-, line 8 at 0; no interest/penalty) blessed; W3 the refund/owe
# arithmetic (lines 17-23 + the line-19<0 branch) blessed; W4 the v1 scope boundary
# CONFIRMED (RED-defer NOL/GBC carrybacks, superseding, and multi-form cascades like
# 8962 PTC re-reconciliation — EIC/CTC/tax auto-recompute on the 1040 and read into
# column C, not a cascade) blessed; W5 year handling (pure structure + arithmetic,
# reuse the amended 1040's own year rules) blessed; W6 the required Part II
# explanation (error when blank) blessed. Math gate check_1040x_integrity.py ALL PASS.
# ═══════════════════════════════════════════════════════════════════════════
READY_TO_SEED = True


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1040"]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("amended_returns", "Amended Returns (Form 1040-X)"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_FORM_1040X",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "Form 1040-X — Amended U.S. Individual Income Tax Return (Rev. December 2025)",
        "citation": "Form 1040-X (Rev. December 2025)",
        "issuer": "Internal Revenue Service",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f1040x.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["amended_returns"],
        "excerpts": [
            {
                "excerpt_label": "Form 1040-X face — three-column A/B/C line map (Rev. Dec 2025)",
                "excerpt_text": (
                    "Three columns: A = original amount (or as previously adjusted); B = net change "
                    "(increase or decrease — explain in Part II); C = correct amount. INCOME & "
                    "DEDUCTIONS: 1 Adjusted gross income; 2 Itemized or standard deduction; 3 Subtract "
                    "line 2 from line 1; 4a Qualified business income deduction; 4b Deductions for tips, "
                    "overtime, car loan interest, and seniors (Schedule 1-A); 5 Taxable income = line 3 "
                    "− (4a+4b), column C floored at -0-. TAX LIABILITY: 6 Tax (enter method[s]); 7 "
                    "Nonrefundable credits; 8 line 6 − line 7 (≥0); 9 Reserved; 10 Other taxes; 11 Total "
                    "tax = line 8 + line 10. PAYMENTS: 12 Federal income tax withheld + excess SS/RRTA; "
                    "13 Estimated tax payments; 14 EIC; 15 Refundable credits (Sch 8812 / 2439 / 4136). "
                    "REFUND OR AMOUNT YOU OWE (single column): 16 Total paid with extension/original + "
                    "additional; 17 Total payments = (lines 12-15 col C) + line 16; 18 Overpayment on "
                    "original/as adjusted; 19 line 17 − line 18; 20 Amount you owe (if line 11 col C > "
                    "line 19); 21 Overpayment on this return (if line 11 col C < line 19); 22 line 21 "
                    "refunded; 23 line 21 applied to estimated tax."
                ),
                "summary_text": "1040-X face: A=original, C=correct, B=C−A; recompute tax + refund/owe (lines 17-23).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Form 1040-X page 2 — Part I dependents + Part II explanation",
                "excerpt_text": (
                    "PART I DEPENDENTS (columns A/B/C): 24 Reserved; 25 Your dependent children who "
                    "lived with you (number); 26 Reserved; 27 Other dependents (number); 28 Reserved; "
                    "29 Reserved; 30 List ALL dependents (children and others) claimed on this amended "
                    "return (name / SSN / relationship / qualifies-for checkboxes). PART II EXPLANATION "
                    "OF CHANGES: explain in detail the reason for each change; attach supporting forms "
                    "and schedules. You must complete Part II and explain any changes."
                ),
                "summary_text": "Page 2: Part I dependents (A/B/C counts) + Part II free-text explanation (required).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Form 1040-X header — 'You must' attach a corrected 1040",
                "excerpt_text": (
                    "You must: • Attach a completed Form 1040, 1040-SR, or 1040-NR, with your changes, "
                    "for the return year entered below; and • Attach any supporting documents and new or "
                    "changed forms and schedules and complete Part II. See instructions. Use Form 1040-X "
                    "to correct a previously filed Form 1040, 1040-SR, or 1040-NR (NOT to file a "
                    "superseding return before the due date)."
                ),
                "summary_text": "1040-X corrects a previously FILED 1040; a corrected 1040 is attached; complete Part II.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_INSTR_1040X",
        "source_type": "instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "Instructions for Form 1040-X (Rev. 2025)",
        "citation": "Instructions for Form 1040-X (2025)",
        "issuer": "Internal Revenue Service",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i1040x.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.0,
        "topics": ["amended_returns"],
        "excerpts": [
            {
                "excerpt_label": "1040-X instructions — column conventions + refund/owe (requires_human_review)",
                "excerpt_text": (
                    "Column A: enter the amounts from your original return or as previously adjusted. "
                    "Column B: enter the net increase or decrease for each line you are changing, and "
                    "explain each change in Part II (show a decrease in parentheses). Column C: add the "
                    "increase in column B to column A, or subtract the decrease, and enter the result. "
                    "If there is no change, enter the column A amount in column C. Carrybacks (NOL, "
                    "general business credit): see the special instructions / Form 1045. Interest and "
                    "penalties: the IRS will figure interest and any penalty and bill you. REQUIRES "
                    "HUMAN REVIEW: verify the exact line 17-23 refund/owe arithmetic and the column-C "
                    "floors against the current-year instructions before the compute leg."
                ),
                "summary_text": "Col A=original, B=net change (parens=decrease), C=A±B; carrybacks special; IRS bills interest.",
                "is_key_excerpt": True,
            },
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_FORM_1040X", "1040X", "defines"),
    ("IRS_2025_INSTR_1040X", "1040X", "explains"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FACTS  (amendment-level; the compute leg consumes these — authored, not seeded)
# ═══════════════════════════════════════════════════════════════════════════

X_FACTS: list[dict] = [
    {"fact_key": "x_amendment_year", "label": "Tax year being amended", "data_type": "integer", "default_value": "0", "sort_order": 1,
     "notes": "The return year entered at the top of Form 1040-X. The corrected 1040 it attaches to carries this year; the tax recompute uses this year's rules (W5)."},
    {"fact_key": "x_explanation_of_changes", "label": "Part II — Explanation of changes (free text, REQUIRED)", "data_type": "text", "default_value": "", "sort_order": 2,
     "notes": "Form 1040-X Part II. Required on every 1040-X — D_1040X_004 errors when blank (W6)."},
    {"fact_key": "x_tax_method", "label": "Line 6 — method(s) used to figure tax", "data_type": "text", "default_value": "", "sort_order": 3,
     "notes": "Form 1040-X line 6 free text (e.g. 'Tax Table', 'QDCGT Wksht', 'Sch D Tax Wksht'). Carried from the corrected 1040's tax method."},
    {"fact_key": "x_amount_paid_with_original", "label": "Line 16 — total paid with extension/original + after filing", "data_type": "decimal", "default_value": "0", "sort_order": 4,
     "notes": "Form 1040-X line 16 (single column). Preparer-entered: extension payment + tax paid with the original return + additional tax paid after it was filed."},
    {"fact_key": "x_overpayment_on_original", "label": "Line 18 — overpayment on the original return / as adjusted", "data_type": "decimal", "default_value": "0", "sort_order": 5,
     "notes": "Form 1040-X line 18 (single column). The refund already received (or applied) on the original return, or as previously adjusted by the IRS (W3)."},
    {"fact_key": "x_refundable_credit_sources", "label": "Line 15 — refundable-credit source forms (8812 / 2439 / 4136 / other)", "data_type": "text", "default_value": "", "sort_order": 6,
     "notes": "Form 1040-X line 15 checkbox group — which refundable-credit forms the column-C amount comes from."},
    {"fact_key": "x_applied_to_year", "label": "Line 23 — year the overpayment is applied to (estimated tax)", "data_type": "integer", "default_value": "0", "sort_order": 7,
     "notes": "Form 1040-X line 23 — the estimated-tax year an overpayment (line 21) is applied to."},
    # — RED-defer flags (each fires a 'prepare manually' RED — no silent gap) —
    {"fact_key": "x_has_nol_carryback", "label": "Amendment includes a net operating loss (NOL) carryback", "data_type": "boolean", "default_value": "false", "sort_order": 10,
     "notes": "Line 1 NOL carryback. v1 RED-defers (D_1040X_001) — carryback claims are out of the common-case scope (Form 1045 territory)."},
    {"fact_key": "x_has_gbc_carryback", "label": "Amendment includes a general business credit carryback", "data_type": "boolean", "default_value": "false", "sort_order": 11,
     "notes": "Line 7 general-business-credit carryback. v1 RED-defers (D_1040X_002)."},
    {"fact_key": "x_is_superseding", "label": "This is a superseding return (filed before the due date)", "data_type": "boolean", "default_value": "false", "sort_order": 12,
     "notes": "A superseding return (filed before the original due date) is NOT a 1040-X — different mechanics. v1 RED-defers (D_1040X_003)."},
    {"fact_key": "x_has_credit_cascade", "label": "Change re-adjudicates other credits (PTC/EIC/CTC cascade)", "data_type": "boolean", "default_value": "false", "sort_order": 13,
     "notes": "When a change forces re-running Form 8962 PTC reconciliation, a fresh EIC qualification, or a multi-form recompute chain beyond the common set. v1 RED-defers (D_1040X_008); the common case recomputes tax + refund/owe from the changed lines without re-adjudicating other-credit eligibility (W4)."},
    {"fact_key": "x_baseline_captured", "label": "As-filed baseline snapshot exists (Column A source)", "data_type": "boolean", "default_value": "false", "sort_order": 14,
     "notes": "True when a frozen as-filed baseline of the original return has been captured (tts AsFiledBaseline). Column A cannot be populated without it — D_1040X_005 (W1)."},
]


# ═══════════════════════════════════════════════════════════════════════════
# RULES  (the A/B/C delta + recompute — AUTHORED for Ken's review; the compute
#         leg implements these only after he approves. NOT seeded — READY_TO_SEED
#         is False.)
# ═══════════════════════════════════════════════════════════════════════════

X_RULES: list[dict] = [
    {"rule_id": "R-1040X-COLA", "title": "Column A ← the as-filed baseline snapshot", "rule_type": "calculation", "precedence": 1, "sort_order": 1,
     "formula": "For every A/B/C line N, column A (N-A) = the value of the corresponding 1040 line in the FROZEN as-filed baseline snapshot of the original return (captured at 'mark as filed'). If the baseline is missing, D_1040X_005 fires and column A cannot be computed.",
     "inputs": ["x_baseline_captured"], "outputs": ["1A", "2A", "3A", "5A", "6A", "7A", "8A", "10A", "11A", "12A", "13A", "14A", "15A"],
     "description": "Column A is the original/as-filed amount — a frozen snapshot, never the live current return (snapshot-copy; W1)."},
    {"rule_id": "R-1040X-COLC", "title": "Column C ← the amended (corrected) 1040", "rule_type": "calculation", "precedence": 2, "sort_order": 2,
     "formula": "For every A/B/C line N, column C (N-C) = the corresponding line of the amended (corrected) 1040: 1C←1040 AGI (line 11); 2C←1040 deduction (line 12); 4a-C←1040 QBI (line 13); 4b-C←1040 Sch 1-A deductions (line 13b); 5C←1040 taxable income (line 15); 6C←1040 tax (line 16+Sch 2 lines per the 1040-X mapping); 7C←nonrefundable credits; 10C←other taxes; 12C←withholding; 13C←estimated; 14C←EIC; 15C←refundable credits.",
     "inputs": [], "outputs": ["1C", "2C", "4aC", "4bC", "5C", "6C", "7C", "10C", "12C", "13C", "14C", "15C"],
     "description": "Column C is the now-correct return — the amended 1040's current line values (W2). The exact 1040→1040-X line map is verified at the compute leg."},
    {"rule_id": "R-1040X-DELTA", "title": "Column B = column C − column A", "rule_type": "calculation", "precedence": 3, "sort_order": 3,
     "formula": "For every A/B/C line N: column B (N-B) = column C (N-C) − column A (N-A). B is a SIGNED net change (a decrease shows in parentheses). When a line is unchanged, B = 0 and C = A.",
     "inputs": [], "outputs": ["1B", "2B", "3B", "4aB", "4bB", "5B", "6B", "7B", "8B", "10B", "11B", "12B", "13B", "14B", "15B"],
     "description": "The net-change column — the heart of the 1040-X (W2). No interest/penalty enters this math."},
    {"rule_id": "R-1040X-L3", "title": "Line 3 = line 1 − line 2 (per column)", "rule_type": "calculation", "precedence": 4, "sort_order": 4,
     "formula": "For each column X in {A, B, C}: line 3-X = line 1-X − line 2-X.",
     "inputs": [], "outputs": ["3A", "3B", "3C"], "description": "AGI less deductions, per column."},
    {"rule_id": "R-1040X-L5", "title": "Line 5 = line 3 − (line 4a + line 4b); column C floored at -0-", "rule_type": "calculation", "precedence": 5, "sort_order": 5,
     "formula": "For each column X: line 5-X = line 3-X − (line 4a-X + line 4b-X). If the column-C result is zero or less, enter -0- in column C.",
     "inputs": [], "outputs": ["5A", "5B", "5C"], "description": "Taxable income, per column (column C floored at 0)."},
    {"rule_id": "R-1040X-L8", "title": "Line 8 = line 6 − line 7 (≥ 0, per column)", "rule_type": "calculation", "precedence": 6, "sort_order": 6,
     "formula": "For each column X: line 8-X = max(0, line 6-X − line 7-X).",
     "inputs": [], "outputs": ["8A", "8B", "8C"], "description": "Tax after nonrefundable credits, per column."},
    {"rule_id": "R-1040X-L11", "title": "Line 11 = line 8 + line 10 (total tax, per column)", "rule_type": "calculation", "precedence": 7, "sort_order": 7,
     "formula": "For each column X: line 11-X = line 8-X + line 10-X.",
     "inputs": [], "outputs": ["11A", "11B", "11C"], "description": "Total tax, per column."},
    {"rule_id": "R-1040X-L17", "title": "Line 17 = (lines 12-15, column C) + line 16", "rule_type": "calculation", "precedence": 8, "sort_order": 8,
     "formula": "Line 17 (single column) = line 12-C + line 13-C + line 14-C + line 15-C + line 16.",
     "inputs": ["x_amount_paid_with_original"], "outputs": ["17"], "description": "Total payments on the amended return."},
    {"rule_id": "R-1040X-L19", "title": "Line 19 = line 17 − line 18", "rule_type": "calculation", "precedence": 9, "sort_order": 9,
     "formula": "Line 19 = line 17 − line 18 (overpayment already received/applied on the original return). If less than zero, see instructions (W3).",
     "inputs": ["x_overpayment_on_original"], "outputs": ["19"], "description": "Net payments after backing out the original overpayment."},
    {"rule_id": "R-1040X-L20-OWE", "title": "Line 20 — amount you owe (if line 11 col C > line 19)", "rule_type": "calculation", "precedence": 10, "sort_order": 10,
     "formula": "If line 11 column C (corrected total tax) > line 19: line 20 (amount you owe) = line 11-C − line 19. Else line 20 = 0. Interest/penalty NOT included (the IRS bills them — D_1040X_007).",
     "inputs": [], "outputs": ["20"], "description": "Additional tax owed with the amendment (W3)."},
    {"rule_id": "R-1040X-L21-OVERPAY", "title": "Line 21 — overpayment on this return (if line 11 col C < line 19)", "rule_type": "calculation", "precedence": 11, "sort_order": 11,
     "formula": "If line 11 column C < line 19: line 21 = line 19 − line 11-C. Else line 21 = 0. Line 21 = line 22 (refunded to you) + line 23 (applied to next year's estimated tax).",
     "inputs": [], "outputs": ["21"], "description": "Additional refund from the amendment, split between refund (22) and applied-forward (23) (W3)."},
    {"rule_id": "R-1040X-DEFER", "title": "RED-defer boundaries (no silent gap)", "rule_type": "validation", "precedence": 2, "sort_order": 12,
     "formula": "NOL carryback (D_1040X_001), general-business-credit carryback (D_1040X_002), superseding return (D_1040X_003), and other-credit cascades / PTC-EIC re-adjudication (D_1040X_008) are OUT of the v1 common case and each fire a RED 'prepare manually'. A missing as-filed baseline (D_1040X_005) blocks column A. A blank Part II explanation (D_1040X_004) errors.",
     "inputs": ["x_has_nol_carryback", "x_has_gbc_carryback", "x_is_superseding", "x_has_credit_cascade", "x_baseline_captured", "x_explanation_of_changes"], "outputs": [],
     "description": "v1 boundaries — every unsupported path is a RED, never a wrong number computed quietly (W4)."},
]


# ═══════════════════════════════════════════════════════════════════════════
# LINES  (line_number unique per form; A/B/C columns carried as N-A/N-B/N-C)
# ═══════════════════════════════════════════════════════════════════════════

def _abc(num: str, desc: str, *, a_type: str = "input", c_type: str = "input") -> list[dict]:
    """A/B/C triple for a 1040-X line. Column A = original (from baseline), column
    B = net change (= C − A, computed), column C = correct amount."""
    return [
        {"line_number": f"{num}A", "description": f"Line {num} — {desc} (column A: original / as previously adjusted)", "line_type": a_type},
        {"line_number": f"{num}B", "description": f"Line {num} — {desc} (column B: net change = C − A)", "line_type": "calculated"},
        {"line_number": f"{num}C", "description": f"Line {num} — {desc} (column C: correct amount)", "line_type": c_type},
    ]


X_LINES: list[dict] = (
    # — Income & deductions (A/B/C) —
    _abc("1", "Adjusted gross income")
    + _abc("2", "Itemized deductions or standard deduction")
    + _abc("3", "Subtract line 2 from line 1", c_type="calculated")
    + _abc("4a", "Qualified business income deduction")
    + _abc("4b", "Deductions for tips, overtime, car loan interest, and seniors (Schedule 1-A)")
    + _abc("5", "Taxable income (line 3 − lines 4a+4b; column C floored at -0-)", c_type="calculated")
    # — Tax liability (A/B/C) —
    + [{"line_number": "6_method", "description": "Line 6 — method(s) used to figure tax (free text)", "line_type": "input"}]
    + _abc("6", "Tax")
    + _abc("7", "Nonrefundable credits")
    + _abc("8", "Subtract line 7 from line 6 (zero or less = -0-)", c_type="calculated")
    + [{"line_number": "9", "description": "Line 9 — Reserved for future use", "line_type": "input"}]
    + _abc("10", "Other taxes")
    + _abc("11", "Total tax (line 8 + line 10)", c_type="calculated")
    # — Payments (A/B/C) —
    + _abc("12", "Federal income tax withheld and excess social security / tier-1 RRTA")
    + _abc("13", "Estimated tax payments (including prior-year applied)")
    + _abc("14", "Earned income credit (EIC)")
    + _abc("15", "Refundable credits (Schedule 8812 / Form(s) 2439 / 4136 / etc.)")
    # — Refund or amount you owe (single column) —
    + [
        {"line_number": "16", "description": "Line 16 — Total amount paid with extension/original return + additional tax paid after filing", "line_type": "input"},
        {"line_number": "17", "description": "Line 17 — Total payments (lines 12-15 column C + line 16)", "line_type": "calculated"},
        {"line_number": "18", "description": "Line 18 — Overpayment on the original return / as previously adjusted by the IRS", "line_type": "input"},
        {"line_number": "19", "description": "Line 19 — Subtract line 18 from line 17", "line_type": "calculated"},
        {"line_number": "20", "description": "Line 20 — Amount you owe (if line 11 column C > line 19)", "line_type": "calculated"},
        {"line_number": "21", "description": "Line 21 — Overpayment on this return (if line 11 column C < line 19)", "line_type": "calculated"},
        {"line_number": "22", "description": "Line 22 — Amount of line 21 refunded to you", "line_type": "input"},
        {"line_number": "23", "description": "Line 23 — Amount of line 21 applied to next year's estimated tax (enter year)", "line_type": "input"},
    ]
    # — Part I dependents (A/B/C; 24/26/28/29 reserved) —
    + _abc("25", "Your dependent children who lived with you (number)")
    + _abc("27", "Other dependents (number)")
)


# ═══════════════════════════════════════════════════════════════════════════
# DIAGNOSTICS  (RED-deferrals + required-field checks — no silent gap)
# ═══════════════════════════════════════════════════════════════════════════

X_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_1040X_001", "title": "NOL carryback — prepare manually", "severity": "error",
     "condition": "the amendment includes a net operating loss carryback (x_has_nol_carryback)",
     "message": "Not supported — prepare manually: a Form 1040-X net-operating-loss carryback claim is not computed in this version. See the Form 1040-X / Form 1045 instructions and prepare the carryback manually.",
     "notes": "RED — carryback claims are out of the v1 common case (W4)."},
    {"diagnostic_id": "D_1040X_002", "title": "General business credit carryback — prepare manually", "severity": "error",
     "condition": "the amendment includes a general business credit carryback (x_has_gbc_carryback)",
     "message": "Not supported — prepare manually: a general business credit carryback on Form 1040-X line 7 is not computed in this version.",
     "notes": "RED — GBC carrybacks are out of the v1 common case (W4)."},
    {"diagnostic_id": "D_1040X_003", "title": "Superseding return — not a 1040-X", "severity": "error",
     "condition": "the return is marked as superseding (x_is_superseding)",
     "message": "Not supported — prepare manually: a superseding return (filed before the original due date) is not a Form 1040-X and uses different mechanics. File a corrected original return instead.",
     "notes": "RED — superseding returns are out of scope (W4)."},
    {"diagnostic_id": "D_1040X_004", "title": "Explanation of changes (Part II) is required", "severity": "error",
     "condition": "Part II explanation of changes (x_explanation_of_changes) is blank while any column-B amount is nonzero",
     "message": "Form 1040-X requires a Part II explanation of changes. Enter the reason for each change before filing.",
     "notes": "RED — Part II is mandatory on every 1040-X (W6)."},
    {"diagnostic_id": "D_1040X_005", "title": "No as-filed baseline — column A cannot be populated", "severity": "error",
     "condition": "no frozen as-filed baseline snapshot exists for the original return (NOT x_baseline_captured)",
     "message": "Not supported — prepare manually: this return has no captured as-filed baseline, so Form 1040-X column A (the original amounts) cannot be populated. Mark the original return as filed (capturing its baseline) first.",
     "notes": "RED — column A requires a frozen baseline (W1)."},
    {"diagnostic_id": "D_1040X_006", "title": "Attach the corrected 1040", "severity": "info",
     "condition": "always (a reminder on every 1040-X)",
     "message": "Attach a completed corrected Form 1040 (or 1040-SR/1040-NR) for the amended year, plus any new or changed forms and schedules.",
     "notes": "INFO — the 1040-X header 'You must' requirement."},
    {"diagnostic_id": "D_1040X_007", "title": "Interest and penalties are out of scope", "severity": "info",
     "condition": "the amendment results in additional tax owed (line 20 > 0)",
     "message": "Interest and any penalty are not computed on Form 1040-X — the IRS will figure and bill them. Line 20 is the additional tax only.",
     "notes": "INFO — interest/penalty intentionally out of scope (W3)."},
    {"diagnostic_id": "D_1040X_008", "title": "Other-credit cascade — verify manually", "severity": "error",
     "condition": "the change re-adjudicates other credits (x_has_credit_cascade): PTC (8962), EIC qualification, or a multi-form recompute chain",
     "message": "Not supported — prepare manually: this change cascades into other credits (e.g. Form 8962 PTC reconciliation, EIC qualification, or a multi-form recompute) beyond the common case. Verify the affected forms manually.",
     "notes": "RED — the v1 common case recomputes tax + refund/owe from the changed lines but does not re-adjudicate other-credit eligibility (W4)."},
]


# ═══════════════════════════════════════════════════════════════════════════
# SCENARIOS  (delta mechanics — for the integrity checker; the compute leg
#             implements the recompute. Column A = baseline, C = corrected.)
# ═══════════════════════════════════════════════════════════════════════════

X_SCENARIOS: list[dict] = [
    {"scenario_name": "X1 — added income increases AGI, tax, and balance owed", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"x_amendment_year": 2025,
                "1A": 50000, "1C": 55000, "2A": 14600, "2C": 14600, "4aA": 0, "4aC": 0, "4bA": 0, "4bC": 0,
                "6A": 3500, "6C": 4100, "7A": 0, "7C": 0, "10A": 0, "10C": 0,
                "12A": 4000, "12C": 4000, "13A": 0, "13C": 0, "14A": 0, "14C": 0, "15A": 0, "15C": 0,
                "x_amount_paid_with_original": 0, "x_overpayment_on_original": 500},
     "expected_outputs": {"1B": 5000, "3A": 35400, "3C": 40400, "5A": 35400, "5C": 40400,
                          "8A": 3500, "8C": 4100, "11A": 3500, "11C": 4100, "11B": 600,
                          "17": 4000, "19": 3500, "20": 600, "21": 0},
     "notes": "AGI +5,000 → taxable +5,000 → total tax +600 (col B). Payments 4,000 − original overpayment 500 = line 19 3,500; line 11 col C 4,100 > 3,500 → owe 600."},
    {"scenario_name": "X2 — decreased income yields an additional refund", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"x_amendment_year": 2025,
                "1A": 60000, "1C": 56000, "2A": 14600, "2C": 14600, "4aA": 0, "4aC": 0, "4bA": 0, "4bC": 0,
                "6A": 5000, "6C": 4520, "7A": 0, "7C": 0, "10A": 0, "10C": 0,
                "12A": 6000, "12C": 6000, "13A": 0, "13C": 0, "14A": 0, "14C": 0, "15A": 0, "15C": 0,
                "x_amount_paid_with_original": 0, "x_overpayment_on_original": 1000},
     "expected_outputs": {"1B": -4000, "5A": 45400, "5C": 41400, "11A": 5000, "11C": 4520, "11B": -480,
                          "17": 6000, "19": 5000, "20": 0, "21": 480},
     "notes": "AGI −4,000 → total tax −480. Payments 6,000 − original overpayment 1,000 = line 19 5,000; line 11 col C 4,520 < 5,000 → overpayment-on-this-return 480 (refund)."},
]


X_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-1040X-COLA", "IRS_2025_INSTR_1040X", "primary", "Column A = original / as previously adjusted (1040-X instructions)."),
    ("R-1040X-COLC", "IRS_2025_FORM_1040X", "primary", "Column C = correct amount (the amended 1040)."),
    ("R-1040X-DELTA", "IRS_2025_INSTR_1040X", "primary", "Column B = net change = C − A (parentheses for a decrease)."),
    ("R-1040X-L3", "IRS_2025_FORM_1040X", "primary", "Line 3 = line 1 − line 2."),
    ("R-1040X-L5", "IRS_2025_FORM_1040X", "primary", "Line 5 = line 3 − (4a+4b); column C floored at -0-."),
    ("R-1040X-L8", "IRS_2025_FORM_1040X", "primary", "Line 8 = line 6 − line 7 (≥0)."),
    ("R-1040X-L11", "IRS_2025_FORM_1040X", "primary", "Line 11 = line 8 + line 10."),
    ("R-1040X-L17", "IRS_2025_FORM_1040X", "primary", "Line 17 = lines 12-15 col C + line 16."),
    ("R-1040X-L19", "IRS_2025_FORM_1040X", "primary", "Line 19 = line 17 − line 18."),
    ("R-1040X-L20-OWE", "IRS_2025_FORM_1040X", "primary", "Line 20 = line 11 col C − line 19 (if positive)."),
    ("R-1040X-L21-OVERPAY", "IRS_2025_FORM_1040X", "primary", "Line 21 = line 19 − line 11 col C (if positive)."),
    ("R-1040X-DEFER", "IRS_2025_INSTR_1040X", "primary", "Carrybacks / superseding / cascades are out of the v1 common case."),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS  (the inter-form flows the compute leg must honor)
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040X-01", "assertion_type": "flow_assertion", "entity_types": ["1040"], "sort_order": 1,
     "title": "Column A ← the as-filed baseline snapshot", "description": "Validates R-1040X-COLA. Each 1040-X column-A value equals the corresponding 1040 line in the frozen as-filed baseline of the original return (not the live current return).",
     "definition": {"kind": "flow_assertion", "form": "1040X", "target_line": "1A", "must_read_from": ["as_filed_baseline.1040.11"]}},
    {"assertion_id": "FA-1040X-02", "assertion_type": "flow_assertion", "entity_types": ["1040"], "sort_order": 2,
     "title": "Column C ← the amended 1040", "description": "Validates R-1040X-COLC. Column C line 1 (AGI) = the amended 1040 line 11; column C tracks the corrected current return.",
     "definition": {"kind": "flow_assertion", "form": "1040X", "target_line": "1C", "must_read_from": ["1040.11"]}},
    {"assertion_id": "FA-1040X-03", "assertion_type": "table_invariant", "entity_types": ["1040"], "sort_order": 3,
     "title": "Column B = column C − column A (per line)", "description": "Validates R-1040X-DELTA. For every A/B/C line, the net-change column equals correct minus original.",
     "definition": {"kind": "table_invariant", "form": "1040X", "rule": "for_each_line: col_B == col_C - col_A"}},
    {"assertion_id": "FA-1040X-04", "assertion_type": "table_invariant", "entity_types": ["1040"], "sort_order": 4,
     "title": "Total tax = line 8 + line 10 (per column)", "description": "Validates R-1040X-L11. Line 11 total tax equals tax-after-nonrefundable-credits plus other taxes, in each column.",
     "definition": {"kind": "table_invariant", "form": "1040X", "rule": "line_11 == line_8 + line_10"}},
    {"assertion_id": "FA-1040X-05", "assertion_type": "table_invariant", "entity_types": ["1040"], "sort_order": 5,
     "title": "Refund / owe from line 11 col C vs line 19", "description": "Validates R-1040X-L20/L21. The amended bottom line: owe (line 20) when corrected total tax exceeds net payments (line 19); refund (line 21) when it is less. Line 17 = lines 12-15 col C + line 16.",
     "definition": {"kind": "table_invariant", "form": "1040X", "rule": "line_20 = max(0, line_11C - line_19); line_21 = max(0, line_19 - line_11C)"}},
    {"assertion_id": "FA-1040X-06", "assertion_type": "table_invariant", "entity_types": ["1040"], "sort_order": 6,
     "title": "No silent gap — carrybacks / superseding / cascades RED-defer", "description": "Validates R-1040X-DEFER. NOL carryback (D_1040X_001), GBC carryback (D_1040X_002), superseding (D_1040X_003), missing baseline (D_1040X_005), blank explanation (D_1040X_004), and other-credit cascades (D_1040X_008) are flagged, never silently mis-computed.",
     "definition": {"kind": "table_invariant", "form": "1040X", "rule": "carryback_and_superseding_and_cascade_and_missing_baseline_are_flagged_not_silent"}},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORMS container
# ═══════════════════════════════════════════════════════════════════════════

FORMS: list[dict] = [
    {
        "identity": {
            "form_number": "1040X",
            "form_title": "Form 1040-X — Amended U.S. Individual Income Tax Return (TY2025)",
            "notes": (
                "NEW spec (no prior RS draft). Form 1040-X is a THREE-COLUMN DELTA, not a normal compute "
                "form: column A = original/as-filed (from a frozen as-filed baseline snapshot), column C "
                "= correct (the amended 1040), column B = net change (C − A). Recomputes the subtotals "
                "(lines 3/5/8/11) and the amended refund-due / amount-owed (lines 17-23), and carries a "
                "Part II free-text explanation (required) + a Part I dependents recap. v1 COMMON CASE: "
                "change income/deductions/credits/payments, recompute tax + refund/owe from the changed "
                "lines. RED-DEFERS NOL carrybacks (D_1040X_001), general-business-credit carrybacks "
                "(002), superseding returns (003), missing baseline (005), and other-credit cascades / "
                "PTC-EIC re-adjudication (008). Interest/penalty out of scope (the IRS bills them). Line "
                "set verified vs the actual Form 1040-X (Rev. December 2025) PDF. SPEC + SCAFFOLD pass "
                "only — READY_TO_SEED is False; the delta-compute leg waits for Ken's review (W1-W6)."
            ),
        },
        "facts": X_FACTS,
        "rules": X_RULES,
        "lines": X_LINES,
        "diagnostics": X_DIAGNOSTICS,
        "scenarios": X_SCENARIOS,
        "rule_links": X_RULE_LINKS,
    },
]


# ═══════════════════════════════════════════════════════════════════════════
# Command — the standard upsert flow (mirrors load_ga500_form_500.py exactly)
# ═══════════════════════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = (
        "Load the Form 1040-X spec (Amended U.S. Individual Income Tax Return — "
        "the three-column A/B/C delta over a previously filed 1040). Refuses to "
        "seed until Ken sets READY_TO_SEED=True after the in-session review walk "
        "(W1-W6). This is the remote-safe spec authoring pass; the delta-compute "
        "leg is built only after approval."
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()

        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad FORM 1040-X spec (Amended Individual Income Tax Return)\n"))

        self._load_topics()
        sources = self._load_sources()
        self._load_new_excerpts_on_existing(sources)
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

    # ─────────────────────────────────────────────────────────────────────────
    # Safety guard
    # ─────────────────────────────────────────────────────────────────────────

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
                "\nREFUSING TO SEED FORM 1040-X: not cleared to seed.\n\n"
                "Content is authored, but seeding is gated until Ken reviews the packet\n"
                "(W1 the as-filed-baseline architecture; W2 the column-B delta semantics;\n"
                "W3 the refund-received vs additional-tax-owed arithmetic; W4 the v1 in/out\n"
                "scope forks — carrybacks / superseding / cascades out; W5 year handling;\n"
                "W6 the Part II explanation requirement) and flips the sentinel.\n\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True to proceed)\n\n"
                f"Currently empty / placeholder:\n  {still_empty}\n\n"
                "To proceed: walk Ken through the W-items + the source brief, then set\n"
                "READY_TO_SEED = True. Idempotent via update_or_create — safe to re-run."
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Topics / sources
    # ─────────────────────────────────────────────────────────────────────────

    def _load_topics(self):
        ct = 0
        for code, name in AUTHORITY_TOPICS:
            _, created = AuthorityTopic.objects.update_or_create(
                topic_code=code, defaults={"topic_name": name},
            )
            if created:
                ct += 1
        self.stdout.write(f"Topics: {ct} new ({len(AUTHORITY_TOPICS)} total in batch)")

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
                    AuthoritySourceTopic.objects.get_or_create(
                        authority_source=source, authority_topic=topic,
                    )
        for code in EXISTING_SOURCES_TO_REFERENCE:
            src = AuthoritySource.objects.filter(source_code=code).first()
            if src:
                sources[code] = src
            else:
                self.stdout.write(self.style.WARNING(f"  existing source {code} NOT FOUND — links to it will be skipped"))
        self.stdout.write(f"Sources ready: {len(sources)}")
        return sources

    def _load_new_excerpts_on_existing(self, sources):
        ct = 0
        for code, exc in NEW_EXCERPTS_ON_EXISTING:
            src = sources.get(code) or AuthoritySource.objects.filter(source_code=code).first()
            if not src:
                self.stdout.write(self.style.WARNING(f"  source {code} not found — skipping new excerpt"))
                continue
            exc = dict(exc)
            AuthorityExcerpt.objects.update_or_create(
                authority_source=src, excerpt_label=exc["excerpt_label"], defaults=exc,
            )
            ct += 1
        if ct:
            self.stdout.write(f"  {ct} new excerpts on existing sources")

    # ─────────────────────────────────────────────────────────────────────────
    # Per-form helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _upsert_form(self, identity: dict) -> TaxForm:
        form, created = TaxForm.objects.update_or_create(
            form_number=identity["form_number"],
            jurisdiction=FORM_JURISDICTION,
            tax_year=FORM_TAX_YEAR,
            version=FORM_VERSION,
            defaults={
                "form_title": identity["form_title"],
                "entity_types": FORM_ENTITY_TYPES,
                "status": FORM_STATUS,
                "notes": identity["notes"],
            },
        )
        self.stdout.write(f"{'Created' if created else 'Updated'} {identity['form_number']}")
        return form

    def _upsert_facts(self, form, facts):
        for f in facts:
            f = dict(f)
            FormFact.objects.update_or_create(
                tax_form=form, fact_key=f.pop("fact_key"), defaults=f,
            )
        self.stdout.write(f"  {len(facts)} facts")

    def _upsert_rules(self, form, rules_data) -> dict:
        created = {}
        for r in rules_data:
            r = dict(r)
            rule, _ = FormRule.objects.update_or_create(
                tax_form=form, rule_id=r.pop("rule_id"), defaults=r,
            )
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
            FormLine.objects.update_or_create(
                tax_form=form, line_number=ln.pop("line_number"), defaults=ln,
            )
        self.stdout.write(f"  {len(lines)} lines")

    def _upsert_diagnostics(self, form, diagnostics):
        for d in diagnostics:
            d = dict(d)
            FormDiagnostic.objects.update_or_create(
                tax_form=form, diagnostic_id=d.pop("diagnostic_id"), defaults=d,
            )
        self.stdout.write(f"  {len(diagnostics)} diagnostics")

    def _upsert_tests(self, form, scenarios):
        for t in scenarios:
            t = dict(t)
            TestScenario.objects.update_or_create(
                tax_form=form, scenario_name=t.pop("scenario_name"), defaults=t,
            )
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
            FlowAssertion.objects.update_or_create(
                assertion_id=a.pop("assertion_id"), defaults=a,
            )
        self.stdout.write(f"  {len(FLOW_ASSERTIONS)} flow assertions")

    def _report_totals(self):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("FORM 1040-X loaded.")
        spec = FORMS[0]
        self.stdout.write(
            f"  facts {len(spec['facts'])} / rules {len(spec['rules'])} / "
            f"lines {len(spec['lines'])} / diagnostics {len(spec['diagnostics'])} / "
            f"tests {len(spec['scenarios'])} / FA {len(FLOW_ASSERTIONS)}"
        )
        self.stdout.write("=" * 60 + "\n")
