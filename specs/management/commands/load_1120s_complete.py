"""Load remaining 1120-S forms to complete S-Corp spec coverage.

Session 11: Adds the missing 9 forms/schedules:
  - Schedule B (Other Information — Pages 3-4 of 1120-S)
  - Schedule L (Balance Sheet per Books)
  - Form 8995 (QBI Deduction — Simplified)
  - Form 8995-A (QBI Deduction — Full Computation)
  - Form 8582 (Passive Activity Loss Limitations)
  - Form 6198 (At-Risk Limitations)
  - Form 3800 (General Business Credit)
  - Schedule M-3 (Net Income Reconciliation for Large Filers)
  - Form 8283 (Noncash Charitable Contributions)

Existing authority sources are referenced by source_code.
New instruction sources created for Schedule B, L, M-3, and 8283.
Idempotent: uses update_or_create throughout.
"""
from django.core.management.base import BaseCommand
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
    FormDiagnostic,
    FormFact,
    FormLine,
    FormRule,
    TaxForm,
    TestScenario,
)


# ═══════════════════════════════════════════════════════════════════════════
# New authority sources (detailed instruction excerpts for forms not yet
# covered by existing instruction sources)
# ═══════════════════════════════════════════════════════════════════════════

FRESH_SOURCES = [
    {
        "source_code": "IRS_2025_1120S_SCHB_INSTR",
        "source_type": "official_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "Instructions for Form 1120-S Schedule B — Other Information (2025)",
        "citation": "Form 1120-S Instructions — Schedule B (2025)",
        "issuer": "IRS",
        "current_status": "active",
        "is_substantive_authority": True,
        "requires_human_review": True,
        "trust_score": 9.0,
        "topics": ["1120s", "schedule_b"],
        "excerpts": [
            {
                "excerpt_label": "Schedule B — 2025 face question list (verified vs f1120s.pdf 2025)",
                "excerpt_text": (
                    "Schedule B (Form 1120-S 2025), Other Information, pages 2-3 of the form. "
                    "Questions on the 2025 face: 1 — check accounting method (cash / accrual / other); "
                    "2 — business activity and product or service; 3 — any shareholder a disregarded "
                    "entity, trust, estate, or nominee (if Yes, attach Schedule B-1); 4a/4b — 20%/50% "
                    "ownership of any corporation / partnership; 5a/5b — outstanding restricted stock / "
                    "stock options, warrants, or similar instruments; 6 — Form 8918 material advisor "
                    "disclosure; 7 — checkbox, publicly offered debt instruments with OID; 8 — net "
                    "unrealized built-in gain in excess of prior-year recognized built-in gain (dollar "
                    "entry); 9 — section 163(j) real-property/farming election; 10 — Form 8990 "
                    "conditions (pass-through EBIE / $31M gross receipts / tax shelter); 11 — total "
                    "receipts AND total assets both under $250,000 (see the Question 11 excerpt); "
                    "12 — non-shareholder debt cancelled, forgiven, or modified (plus principal "
                    "reduction amount); 13 — QSub election terminated or revoked; 14a/14b — Form(s) "
                    "1099 required / filed; 15 — Qualified Opportunity Fund self-certification (plus "
                    "Form 8996 line 15 amount); 16 — digital assets received or disposed; 17 — "
                    "reserved for future use. (This excerpt SUPERSEDES the pre-2026-07-09 paraphrase "
                    "that carried a stale, non-face numbering — e.g. an 'AE&P' question 11 that does "
                    "not exist on the 2025 Schedule B.)"
                ),
                "summary_text": "2025 Schedule B face: questions 1-17 as printed (Q11 = the $250K receipts+assets test).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Question 11 — face text and total receipts definition (verbatim)",
                "excerpt_text": (
                    "Form 1120-S (2025) Schedule B, question 11 (face, verbatim): 'Does the "
                    "corporation satisfy both of the following conditions? a. The corporation's "
                    "total receipts (see instructions) for the tax year were less than $250,000. "
                    "b. The corporation's total assets at the end of the tax year were less than "
                    "$250,000. If “Yes,” the corporation is not required to complete "
                    "Schedules L and M-1.' Instructions for Form 1120-S (2025), Question 11 "
                    "(verbatim): 'Total receipts is the sum of the following amounts. • Gross "
                    "receipts or sales (page 1, line 1a). • All other income (page 1, lines 4 "
                    "and 5). • Income reported on Schedule K, lines 3a, 4, 5a, and 6. • "
                    "Income or net gain reported on Schedule K, lines 7, 8a, 9, and 10. • "
                    "Income or net gain reported on Form 8825, lines 2, 21, and 22a.'"
                ),
                "summary_text": "Q11 verbatim: both receipts AND EOY assets < $250K; total-receipts component list from the 2025 instructions.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule B — M-3 threshold and accounting method",
                "excerpt_text": (
                    "Instructions for Form 1120-S (2025), p.49 (verbatim): 'Corporations with total "
                    "assets of $10 million or more on the last day of the tax year must file "
                    "Schedule M-3 (Form 1120-S) instead of Schedule M-1.' (The pre-2026-07-09 "
                    "paraphrase said $50 million — a tax-law error.) The accounting method reported "
                    "on Schedule B question 1 must be consistent with the method used throughout "
                    "the return; a method change requires Form 3115."
                ),
                "summary_text": "M-3 required if total assets >= $10M (i1120s p.49 verbatim). Accounting method must be consistent.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_1120S_SCHL_INSTR",
        "source_type": "official_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "Instructions for Form 1120-S Schedule L — Balance Sheet per Books (2025)",
        "citation": "Form 1120-S Instructions — Schedule L (2025)",
        "issuer": "IRS",
        "current_status": "active",
        "is_substantive_authority": True,
        "requires_human_review": True,
        "trust_score": 9.0,
        "topics": ["1120s", "balance_sheet"],
        "excerpts": [
            {
                "excerpt_label": "Schedule L — structure and line descriptions",
                "location_reference": "i1120s (2025) p.49, Schedule L + the f1120s 2025 face p.4",
                "excerpt_text": (
                    "i1120s p.49 verbatim: \"The balance sheets should agree with the corporation's "
                    "books and records. Schedule L isn't required to be completed if the corporation "
                    "answered 'Yes' to question 11 on Schedule B. If the corporation is required to "
                    "complete Schedule L, include total assets reported on Schedule L, line 15, "
                    "column (d), on page 1, item F.\" 2025 face rows (f1120s p.4 verbatim): assets "
                    "1 Cash · 2a Trade notes and accounts receivable / 2b Less allowance for bad "
                    "debts · 3 Inventories · 4 U.S. government obligations · 5 Tax-exempt securities "
                    "· 6 Other current assets · 7 Loans to shareholders · 8 Mortgage and real estate "
                    "loans · 9 Other investments · 10a Buildings and other depreciable assets / 10b "
                    "Less accumulated depreciation · 11a Depletable assets / 11b Less accumulated "
                    "depletion · 12 Land (net of any amortization) · 13a Intangible assets "
                    "(amortizable only) / 13b Less accumulated amortization · 14 Other assets · "
                    "15 Total assets; liabilities 16 Accounts payable · 17 Mortgages, notes, bonds "
                    "payable in less than 1 year · 18 Other current liabilities · 19 Loans from "
                    "shareholders · 20 Mortgages, notes, bonds payable in 1 year or more · 21 Other "
                    "liabilities; equity 22 Capital stock · 23 Additional paid-in capital · 24 "
                    "Retained earnings · 25 Adjustments to shareholders' equity · 26 Less cost of "
                    "treasury stock · 27 Total liabilities and shareholders' equity. There is NO "
                    "total-liabilities subtotal line on the face."
                ),
                "summary_text": "2025 Schedule L: assets 1-15, liabilities 16-21 (no subtotal), equity 22-26, total 27; L15(d) → page 1 item F; not required if Sch B Q11 is Yes.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule L — small corporation exception and cross-checks",
                "location_reference": "i1120s (2025) p.49, Schedule L / Line 24 / Line 25",
                "excerpt_text": (
                    "\"Schedule L isn't required to be completed if the corporation answered 'Yes' to "
                    "question 11 on Schedule B.\" (Question 11: receipts AND total assets each under "
                    "$250,000 — see 1120S_SCHB.) \"Line 24. Retained Earnings — If the corporation "
                    "maintains separate accounts for appropriated and unappropriated retained "
                    "earnings, it may want to continue such accounting for purposes of preparing its "
                    "financial balance sheet.\" \"Line 25. Adjustments to Shareholders' Equity — The "
                    "following are some examples of adjustments to report on this line: unrealized "
                    "gains and losses on securities held 'available for sale'; foreign currency "
                    "translation adjustments; the excess of additional pension liability over "
                    "unrecognized prior service cost; guarantees of employee stock ownership plan "
                    "(ESOP) debt; compensation related to employee stock award plans. If the total "
                    "adjustment to be entered is a negative amount, enter the amount in parentheses.\""
                ),
                "summary_text": "Not required if Sch B Q11 Yes; Line 24 retained-earnings and Line 25 adjustments guidance (verbatim).",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_1120S_M3_INSTR",
        "source_type": "official_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "Instructions for Schedule M-3 (Form 1120-S) — Net Income (Loss) Reconciliation (Rev. December 2019, current)",
        "citation": "Instructions for Schedule M-3 (Form 1120-S) (Rev. December 2019)",
        "issuer": "IRS",
        "current_status": "active",
        "is_substantive_authority": True,
        "requires_human_review": True,
        "trust_score": 9.0,
        "topics": ["1120s", "book_tax_reconciliation"],
        # Excerpts rebuilt 2026-07-12 (renumber unit #7): the face (f1120ss3.pdf,
        # Rev. 12-2019 — the CURRENT revision) + its instructions (i1120ss3, also
        # Rev. 12-2019) were downloaded from irs.gov and pymupdf-extracted; the
        # old "UNVERIFIED against the face" warning is retired. ⚠ irs.gov
        # filename trap: f1120sm3.pdf is the Form 1120 (C-corp) M-3 — the
        # 1120-S schedule is f1120ss3.pdf.
        "excerpts": [
            {
                "excerpt_label": "Schedule M-3 — filing threshold and structure",
                "excerpt_text": (
                    "Instructions for Schedule M-3 (Form 1120-S) (Rev. 12-2019), Who Must File "
                    "(verbatim): 'Any corporation required to file Form 1120-S, U.S. Income Tax "
                    "Return for an S Corporation, that reports on Schedule L of Form 1120-S total "
                    "assets at the end of the corporation's tax year that equal or exceed $10 "
                    "million must file Schedule M-3 (Form 1120-S). A corporation or group of "
                    "corporations that completes Parts II and III of Schedule M-3, isn't required "
                    "to complete Form 1120-S, Schedule M-1... A U.S. corporation filing Form 1120-S "
                    "that isn't required to file Schedule M-3 may voluntarily file Schedule M-3 "
                    "instead of Schedule M-1.' i1120s (2025) p.49 agrees: 'Corporations with total "
                    "assets of $10 million or more on the last day of the tax year must file "
                    "Schedule M-3 (Form 1120-S) instead of Schedule M-1.' (The pre-2026-07-09 "
                    "paraphrase put the FILING threshold at $50 million — a tax-law error; $50M is "
                    "the complete-ENTIRELY threshold, see the Completing excerpt.) The threshold "
                    "reads SCHEDULE L total assets — published Example 1: consolidated financial-"
                    "statement assets of $12 million with Schedule L assets of $8 million is NOT "
                    "required to file (may file voluntarily)."
                ),
                "summary_text": "M-3 required when SCHEDULE L EOY total assets >= $10M (i1120ss3 Who Must File verbatim); voluntary below; Parts II/III replace M-1.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Completing Schedule M-3 — the $50M entirely / through-Part-I tiers (verbatim)",
                "excerpt_text": (
                    "i1120ss3 (Rev. 12-2019), Completing Schedule M-3 (verbatim): 'A corporation "
                    "that is required to file Schedule M-3 (Form 1120-S) and has at least $50 "
                    "million total assets at the end of the tax year must complete Schedule M-3 "
                    "(Form 1120-S) entirely. A corporation that (a) is required to file "
                    "Schedule M-3 (Form 1120-S) and has less than $50 million total assets at the "
                    "end of the tax year or (b) isn't required to file Schedule M-3 (Form 1120-S) "
                    "and voluntarily files Schedule M-3 (Form 1120-S) must either (i) complete "
                    "Schedule M-3 (Form 1065) entirely or (ii) complete Schedule M-3 (Form 1120-S) "
                    "through Part I and complete Form 1120-S, Schedule M-1 instead of completing "
                    "Parts II and III of Schedule M-3 (Form 1120-S). If the corporation chooses to "
                    "complete Form 1120-S, Schedule M-1 instead of completing Parts II and III of "
                    "Schedule M-3 (Form 1120-S), line 1 of Form 1120-S, Schedule M-1 must equal "
                    "line 11 of Part I of Schedule M-3 (Form 1120-S).' [NOTE: the '(Form 1065)' in "
                    "clause (i) is the IRS's own typo in the published instructions — context makes "
                    "it (Form 1120-S); transcribed verbatim, do not propagate the 1065 reference.] "
                    "For any part completed, all columns must be completed and all applicable "
                    "questions answered."
                ),
                "summary_text": ">= $50M: complete the M-3 ENTIRELY. $10-50M required, or voluntary: entirely OR through Part I + Schedule M-1 (M-1 line 1 must equal Part I line 11). Distinct from the $10M FILING threshold.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Purpose — Part I line 11 reconciles to Schedule K line 18 (verbatim)",
                "excerpt_text": (
                    "i1120ss3 (Rev. 12-2019), Purpose of Schedule (verbatim): 'Schedule M-3, "
                    "Parts II and III, reconcile financial statement net income (loss) for the "
                    "U.S. tax return (per Schedule M-3, Part I, line 11) to total income (loss) on "
                    "Form 1120-S, Schedule K, line 18.' Face notes (f1120ss3 Rev. 12-2019, "
                    "verbatim): Part I: 'Note: Part I, line 11, must equal Part II, line 26, "
                    "column (a); or Schedule M-1, line 1.' Part II line 26: 'Note: Line 26, "
                    "column (a), must equal Part I, line 11, and column (d) must equal Form "
                    "1120-S, Schedule K, line 18.' Part I line 11 (face): 'Net income (loss) per "
                    "income statement of the corporation. Combine lines 4 through 10.'"
                ),
                "summary_text": "The tie chain: P1 L11 = P2 L26(a) (or M-1 L1); P2 L26(d) = Schedule K line 18 (the same K18 anchor as M-1 line 8). P1 L11 = combine 4-10.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part III line 32 — sign-flip carry to Part II line 24 (face verbatim)",
                "excerpt_text": (
                    "f1120ss3 (Rev. 12-2019) Part III line 32 (verbatim): 'Total expense/deduction "
                    "items. Combine lines 1 through 31. Enter here and on Part II, line 24, "
                    "reporting positive amounts as negative and negative amounts as positive.' "
                    "Part II line 23 (verbatim): 'Total income (loss) items. Combine lines 1 "
                    "through 22.' Part II line 26 (verbatim): 'Reconciliation totals. Combine "
                    "lines 23 through 25.' Each Part II/III row carries four columns: (a) Income "
                    "(Loss)/Expense per Income Statement, (b) Temporary Difference, (c) Permanent "
                    "Difference, (d) Income (Loss)/Deduction per Tax Return."
                ),
                "summary_text": "P3 L32 = combine 1-31, carried to P2 L24 SIGN-FLIPPED; P2 L23 = combine 1-22; P2 L26 = combine 23-25; every row has the (a)/(b)/(c)/(d) columns.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Item C checkbox — M-3 attached (verbatim)",
                "excerpt_text": (
                    "i1120ss3 (Rev. 12-2019), Who Must File (verbatim): 'Any corporation filing "
                    "Schedule M-3 must check the box on Form 1120-S, item C, indicating that "
                    "Schedule M-3 is attached (whether required or voluntary).'"
                ),
                "summary_text": "Page-1 item C box must be checked whenever an M-3 is attached, required or voluntary.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_8283_INSTR",
        "source_type": "official_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "Instructions for Form 8283 — Noncash Charitable Contributions (2025)",
        "citation": "Form 8283 Instructions (2025)",
        "issuer": "IRS",
        "current_status": "active",
        "is_substantive_authority": True,
        "requires_human_review": True,
        "trust_score": 9.0,
        "topics": ["charitable_contributions", "noncash_contributions"],
        "excerpts": [
            {
                "excerpt_label": "Form 8283 — filing requirement and sections",
                "excerpt_text": (
                    "Form 8283 is required when the total deduction claimed for all noncash "
                    "charitable contributions exceeds $500. Section A covers items (or groups of "
                    "similar items) for which the deduction is $5,000 or less — requires description, "
                    "date of contribution, date acquired, donor's cost or basis, FMV, and method of "
                    "determining FMV. Section B covers items for which the deduction is more than "
                    "$5,000 (except publicly traded securities) — requires a qualified appraisal by "
                    "a qualified appraiser. Publicly traded securities use FMV on date of "
                    "contribution regardless of amount and do not require an appraisal."
                ),
                "summary_text": "Required if noncash contributions > $500. Section A: <= $5K. Section B: > $5K (appraisal required).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Form 8283 — S-Corp passthrough and special rules",
                "excerpt_text": (
                    "For S corporations, the charitable contribution deduction is not taken at the "
                    "entity level — it passes through to shareholders on Schedule K-1 Box 12a. The "
                    "S corporation must still file Form 8283 if total noncash contributions exceed "
                    "$500. Special rules apply for vehicles (Form 1098-C required), art valued over "
                    "$20,000 (attach appraisal), and intellectual property (basis limitation applies "
                    "in year of contribution, additional deductions in later years based on income)."
                ),
                "summary_text": "S-Corp: contributions pass through to K-1 Box 12a. Entity still files 8283 if > $500.",
                "is_key_excerpt": True,
            },
        ],
    },
]

# ═══════════════════════════════════════════════════════════════════════════
# Form 6198 — verbatim i6198 (Rev. November 2025) excerpts, pymupdf-extracted
# from the fetched irs.gov PDF 2026-07-12. These REPLACE the pre-2026-07-12
# "At-risk computation" paraphrase (the fabricated-excerpt class): same label
# kept where a row exists (update_or_create keys on label), text now verbatim.
# forms_supporting.py mirrors this set for load_all_federal reruns.
# ═══════════════════════════════════════════════════════════════════════════

_6198_INSTR_EXCERPTS = [
    {
        "excerpt_label": "At-risk computation",
        "location_reference": "Purpose of Form (Rev. 11-2025), p.1",
        "excerpt_text": (
            "Instructions for Form 6198 (Rev. November 2025), Purpose of Form (verbatim): "
            "'Use Form 6198 to figure: • The profit (loss) from an at-risk activity for the "
            "current year (Part I), • The amount at risk for the current year (Part II or "
            "Part III), and • The deductible loss for the current year (Part IV). The at-risk "
            "rules of section 465 limit the amount of the loss you can deduct to the amount "
            "at risk. For more details, see Pub. 925, Passive Activity and At-Risk Rules.' "
            "(This excerpt SUPERSEDES the pre-2026-07-12 paraphrase under the same label, "
            "which carried a non-face structural summary.)"
        ),
        "summary_text": "Purpose of Form verbatim: Part I profit/loss, Part II/III amount at risk, Part IV deductible loss; §465 caps the loss at the amount at risk.",
        "is_key_excerpt": True,
    },
    {
        "excerpt_label": "Part I — prior year nondeductible amounts (verbatim)",
        "location_reference": "Part I instructions (Rev. 11-2025), p.2",
        "excerpt_text": (
            "'Partners and S corporation shareholders. If you have a loss or a deduction "
            "from an earlier tax year that you could not deduct because of the at-risk "
            "rules, these losses and deductions must be included in the current year "
            "amounts you enter in Part I. For example, if your prior year Schedule K-1 had "
            "a $1,500 loss in box 1, but because of the at-risk rules your loss was limited "
            "to $500, include both the $1,000 loss from your prior year and the amount from "
            "your current year Schedule K-1 on line 1 of Form 6198.' Taxpayers other than "
            "partners or S corporation shareholders instead include the disallowed amounts "
            "'on the appropriate form or schedule of your current year tax return before "
            "starting Part I.'"
        ),
        "summary_text": "Prior-year at-risk-disallowed losses ride the CURRENT-year Part I entries (K-1 filers) or the source schedule (others) — there is no 'prior year unallowed losses' face line.",
        "is_key_excerpt": True,
    },
    {
        "excerpt_label": "Qualified nonrecourse financing (verbatim)",
        "location_reference": "General Instructions (Rev. 11-2025), pp.1-2",
        "excerpt_text": (
            "'Qualified nonrecourse financing is financing for which no one is personally "
            "liable for repayment and is: • Borrowed by you in connection with holding real "
            "property; • Secured by real property used in the activity; • Not convertible "
            "debt; and • Loaned or guaranteed by any federal, state, or local government, or "
            "borrowed by you from a qualified person (defined below). See Regulations "
            "section 1.465-27 for details... A qualified person is a person who actively and "
            "regularly engages in the business of lending money (for example, a bank or "
            "savings and loan association). A qualified person is not: • A person related to "
            "you unless the person would be a qualified person but for the relationship and "
            "the nonrecourse financing is commercially reasonable and on the same terms as "
            "loans to unrelated persons, • The seller of the property (or a person related "
            "to the seller), or • A person who receives a fee as a result of your investment "
            "in the property (or a person related to that person).'"
        ),
        "summary_text": "QNF (§465(b)(6)/Reg. 1.465-27) verbatim: no personal liability, real-property activity, secured by activity realty, not convertible, government or qualified-person lender.",
        "is_key_excerpt": True,
    },
    {
        "excerpt_label": "Line 15 — prior-year 19b caution (verbatim)",
        "location_reference": "Line 15 instructions (Rev. 11-2025), p.7",
        "excerpt_text": (
            "'If you completed Part III of Form 6198 for the prior tax year, check box b and "
            "enter the amount from line 19b of the prior year form on this line. [CAUTION] "
            "Do not enter the amount from line 10b of the prior year tax form. Also, do not "
            "include on this line any amounts that are not at risk.' The face box b text "
            "agrees: 'From your prior year Form 6198, line 19b. Do not enter the amount from "
            "line 10b of your prior year form.'"
        ),
        "summary_text": "Line 15 box b carries the prior-year 19b — never the prior-year 10b, and never not-at-risk amounts.",
        "is_key_excerpt": True,
    },
    {
        "excerpt_label": "Line 21 — deductible loss and examples (verbatim)",
        "location_reference": "Part IV, Line 21 instructions (Rev. 11-2025), p.8",
        "excerpt_text": (
            "'If the loss on line 5 is equal to or less than the amount on line 20, report "
            "the items in Part I in full on your return, subject to any other limitations "
            "such as the passive activity and capital loss limitations. ... If the loss on "
            "line 5 is more than the amount on line 20, you must limit your deductible loss "
            "to the amount on line 20, subject to any other limitations. Examples. (a) If "
            "line 5 is a loss of $400 and line 20 is $1,000, enter ($400) on line 21. (b) If "
            "line 5 is a loss of $1,600 and line 20 is $1,200, enter ($1,200) on line 21. "
            "(c) If line 5 is a loss of $800 and line 20 is zero, enter -0- on line 21. "
            "[TIP] When comparing lines 5 and 20, treat the loss on line 5 as a positive "
            "number only for purposes of determining the amount to enter on line 21. ... If "
            "the amount on line 21 is made up of more than one deduction or loss item in "
            "Part I (such as a Schedule C loss and a Schedule D loss), a portion of each "
            "such deduction or loss item is allowed (subject to other limitations) for the "
            "year. Determine this portion by multiplying the loss on line 21 by a fraction. "
            "Figure the fraction by dividing each item of deduction or loss from the "
            "activity by the total loss from the activity on line 5. The remaining portion "
            "of each deduction or loss item from the activity is disallowed and must be "
            "carried over to next year.'"
        ),
        "summary_text": "Line 21 = smaller of the line-5 loss (as positive) or line 20; three published examples; multi-item pro-rata allocation; excess carries over.",
        "is_key_excerpt": True,
    },
    {
        "excerpt_label": "Line 10b / Line 5 — Part III and recapture cautions (verbatim)",
        "location_reference": "Line 10b (p.4) + Line 5 (p.3) instructions (Rev. 11-2025)",
        "excerpt_text": (
            "Line 10b: 'If the amount on this line is smaller than your overall loss from "
            "the activity (line 5), you may want to complete Part III to see if Part III "
            "gives you a larger amount at risk. [CAUTION] If the amount on line 10b is "
            "zero, you may be subject to the recapture rules. See Pub. 925.' Line 5: "
            "'[CAUTION] Even if you have a current year profit on line 5, you may have "
            "recapture income if you received a distribution or had a transaction during "
            "the year that reduced your amount at risk in the activity to less than zero "
            "at the close of the tax year. See Pub. 925 for information on the recapture "
            "rules.' Line 19b agrees: 'If the amount on line 19b is zero, you may be "
            "subject to the recapture rules. See Pub. 925.'"
        ),
        "summary_text": "Part III may beat Part II; a zero 10b/19b (or an at-risk amount below zero, even in a profit year) routes to the Pub. 925 §465(e) recapture rules.",
        "is_key_excerpt": True,
    },
]

# Sources already in the database — referenced by source_code
EXISTING_SOURCES = [
    "IRS_2025_1120S_INSTR", "IRS_2025_1120S_INSTR_FULL",
    "IRS_2025_8995_INSTR", "IRS_2025_8995A_INSTR",
    "IRS_2025_8582_INSTR", "IRS_2025_6198_INSTR", "IRS_2025_3800_INSTR",
    "IRC_199A", "IRC_469", "IRC_465", "IRC_38", "IRC_170",
    "IRC_1361", "IRC_1363", "IRC_1366", "IRC_1367", "IRC_1374",
]


class Command(BaseCommand):
    help = "Load remaining 1120-S forms to complete S-Corp spec coverage (Session 11)"

    def handle(self, *_args, **_options):
        with transaction.atomic():
            sources = self._load_sources()
            self._load_schedule_b(sources)
            self._load_schedule_l(sources)
            self._load_6198(sources)
            self._load_3800(sources)
            self._load_m3(sources)
        self._report_totals()

    # ─────────────────────────────────────────────────────────────────────────
    # Sources
    # ─────────────────────────────────────────────────────────────────────────

    def _load_sources(self) -> dict[str, AuthoritySource]:
        sources: dict[str, AuthoritySource] = {}
        for src_data in FRESH_SOURCES:
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
        for code in EXISTING_SOURCES:
            src = AuthoritySource.objects.filter(source_code=code).first()
            if src:
                sources[code] = src
        self.stdout.write(f"Sources ready: {len(sources)}")
        return sources

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _upsert_form(self, form_number, form_title, entity_types, jurisdiction="FED", notes="") -> TaxForm:
        form, created = TaxForm.objects.update_or_create(
            form_number=form_number, jurisdiction=jurisdiction, tax_year=2025, version=1,
            defaults={"form_title": form_title, "entity_types": entity_types,
                       "status": "draft", "notes": notes},
        )
        self.stdout.write(f"{'Created' if created else 'Updated'} {form_number}")
        return form

    def _upsert_facts(self, form, facts_data):
        for f in facts_data:
            f = dict(f)
            FormFact.objects.update_or_create(tax_form=form, fact_key=f.pop("fact_key"), defaults=f)
        self.stdout.write(f"  {len(facts_data)} facts")

    def _upsert_rules(self, form, rules_data) -> dict[str, FormRule]:
        created = {}
        for r in rules_data:
            r = dict(r)
            rule, _ = FormRule.objects.update_or_create(tax_form=form, rule_id=r.pop("rule_id"), defaults=r)
            created[rule.rule_id] = rule
        self.stdout.write(f"  {len(created)} rules")
        return created

    def _upsert_links(self, rules, sources, links_data):
        ct = 0
        for rule_id, source_code, level, note in links_data:
            rule, source = rules.get(rule_id), sources.get(source_code)
            if rule and source:
                RuleAuthorityLink.objects.get_or_create(
                    form_rule=rule, authority_source=source,
                    defaults={"support_level": level, "relevance_note": note})
                ct += 1
        self.stdout.write(f"  {ct} authority links")

    def _upsert_lines(self, form, lines_data):
        for ln in lines_data:
            ln = dict(ln)
            FormLine.objects.update_or_create(tax_form=form, line_number=ln.pop("line_number"), defaults=ln)
        self.stdout.write(f"  {len(lines_data)} lines")

    def _upsert_diagnostics(self, form, diags_data):
        for d in diags_data:
            d = dict(d)
            FormDiagnostic.objects.update_or_create(tax_form=form, diagnostic_id=d.pop("diagnostic_id"), defaults=d)
        self.stdout.write(f"  {len(diags_data)} diagnostics")

    def _upsert_tests(self, form, tests_data):
        for t in tests_data:
            t = dict(t)
            TestScenario.objects.update_or_create(tax_form=form, scenario_name=t.pop("scenario_name"), defaults=t)
        self.stdout.write(f"  {len(tests_data)} test scenarios")

    def _upsert_form_links(self, form_code, sources, links):
        for source_code, link_type in links:
            source = sources.get(source_code)
            if source:
                AuthorityFormLink.objects.get_or_create(
                    authority_source=source, form_code=form_code, link_type=link_type,
                    defaults={"note": f"{source_code} -> {form_code}"})

    # ═══════════════════════════════════════════════════════════════════════════
    # Schedule B — Other Information (Pages 3-4 of 1120-S)
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_schedule_b(self, sources):
        # 2026-07-09 RENUMBERED TO THE 2025 FACE (verified verbatim vs
        # f1120s.pdf 2025 pages 2-3). The original block carried a stale,
        # non-face numbering (~20 questions incl. an "AE&P" B11 that does not
        # exist on the 2025 Schedule B). Stale fact/line rows are DELETED
        # in-loader below (update_or_create can't remove rows — the F4797-G2
        # lesson). Same session: NEW R006, the Question 11 auto-answer
        # (Ken ruling 2026-07-09, tts usability item 12).
        form = self._upsert_form(
            "1120S_SCHB", "Schedule B (Form 1120-S) — Other Information",
            ["1120S"],
            notes="Pages 2-3 of the 2025 Form 1120-S. Questions 1-16 (+17 reserved) as printed "
                  "on the 2025 face. Q1/Q2 (accounting method, activity/product) live on the "
                  "return header in implementations; Q3-Q16 are the yes/no + amount items.",
        )
        self._upsert_facts(form, [
            # ── 2025 face questions ──
            {"fact_key": "b1_accounting_method", "label": "Q1 — Accounting method (cash / accrual / other)", "data_type": "choice",
             "choices": ["cash", "accrual", "other"], "required": True, "sort_order": 1},
            {"fact_key": "b2_business_activity", "label": "Q2a — Business activity", "data_type": "string", "sort_order": 2},
            {"fact_key": "b2_product_service", "label": "Q2b — Product or service", "data_type": "string", "sort_order": 3},
            {"fact_key": "b3_nominee_shareholder", "label": "Q3 — Any shareholder a disregarded entity, trust, estate, or nominee? (Yes → Schedule B-1)", "data_type": "boolean", "sort_order": 4},
            {"fact_key": "b4a_own_corp_20_50", "label": "Q4a — Own 20% directly / 50% directly-or-indirectly of any corporation?", "data_type": "boolean", "sort_order": 5},
            {"fact_key": "b4b_own_pship_20_50", "label": "Q4b — Own 20% directly / 50% directly-or-indirectly of any partnership or trust?", "data_type": "boolean", "sort_order": 6},
            {"fact_key": "b5a_restricted_stock", "label": "Q5a — Outstanding shares of restricted stock at year end?", "data_type": "boolean", "sort_order": 7},
            {"fact_key": "b5b_options_warrants", "label": "Q5b — Outstanding stock options, warrants, or similar instruments at year end?", "data_type": "boolean", "sort_order": 8},
            {"fact_key": "b6_form_8918", "label": "Q6 — Filed or required to file Form 8918 (material advisor disclosure)?", "data_type": "boolean", "sort_order": 9},
            {"fact_key": "b7_public_oid_debt", "label": "Q7 — Checkbox: issued publicly offered debt instruments with OID", "data_type": "boolean", "sort_order": 10},
            {"fact_key": "b8_nubig_amount", "label": "Q8 — Net unrealized built-in gain over prior-year recognized built-in gain ($)", "data_type": "decimal", "sort_order": 11},
            {"fact_key": "b9_163j_election", "label": "Q9 — Section 163(j) real-property/farming election in effect?", "data_type": "boolean", "sort_order": 12},
            {"fact_key": "b10_form_8990_test", "label": "Q10 — Satisfies one or more Form 8990 conditions (pass-through EBIE / $31M receipts / tax shelter)?", "data_type": "boolean", "sort_order": 13},
            {"fact_key": "b11_under_250k", "label": "Q11 — Total receipts < $250,000 AND EOY total assets < $250,000? (DERIVED, overridable)", "data_type": "boolean", "sort_order": 14,
             "notes": "Auto-answered by R006 (Ken ruling 2026-07-09). YELLOW derived value; a preparer override always wins."},
            {"fact_key": "b12_debt_forgiven", "label": "Q12 — Non-shareholder debt cancelled, forgiven, or modified?", "data_type": "boolean", "sort_order": 15},
            {"fact_key": "b12_principal_reduction", "label": "Q12 — Amount of principal reduction ($)", "data_type": "decimal", "sort_order": 16},
            {"fact_key": "b13_qsub_terminated", "label": "Q13 — QSub election terminated or revoked during the year?", "data_type": "boolean", "sort_order": 17},
            {"fact_key": "b14a_1099_required", "label": "Q14a — Payments made that require Form(s) 1099?", "data_type": "boolean", "sort_order": 18},
            {"fact_key": "b14b_1099_filed", "label": "Q14b — If Yes, did/will the corporation file the required Form(s) 1099?", "data_type": "boolean", "sort_order": 19},
            {"fact_key": "b15_qof", "label": "Q15 — Intends to self-certify as a Qualified Opportunity Fund (attach Form 8996)?", "data_type": "boolean", "sort_order": 20},
            {"fact_key": "b15_8996_penalty", "label": "Q15 — Form 8996 line 15 amount ($)", "data_type": "decimal", "sort_order": 21},
            {"fact_key": "b16_digital_assets", "label": "Q16 — Received or disposed of a digital asset (or financial interest in one)?", "data_type": "boolean", "sort_order": 22},
            # ── Q11 derivation inputs ──
            {"fact_key": "q11_total_receipts", "label": "Q11 — Total receipts (derived per the Question 11 instruction definition)", "data_type": "decimal", "sort_order": 23,
             "notes": "Sum: page 1 line 1a; page 1 lines 4 and 5; Schedule K lines 3a, 4, 5a, 6; "
                      "Schedule K lines 7, 8a, 9, 10 (income or net gain only); Form 8825 lines 2, 21, 22a "
                      "(income or net gain only)."},
            {"fact_key": "l15_total_assets_eoy", "label": "Total assets at end of year (Schedule L line 15, EOY column — cross-form)", "data_type": "decimal", "sort_order": 24},
            # ── practice facts (NOT 2025 Schedule B face questions) ──
            {"fact_key": "aep_from_ccorp", "label": "Practice — outstanding AE&P from C-Corp years (not a 2025 Sch B question)", "data_type": "boolean", "sort_order": 25,
             "notes": "Kept for the §1375 practice rule R004. The pre-2026-07-09 spec mislabeled this as face question 11."},
            {"fact_key": "excess_net_passive_income", "label": "Practice — excess net passive income present (§1375)", "data_type": "boolean", "sort_order": 26},
            {"fact_key": "shareholder_count", "label": "Practice — number of shareholders (page 1, item I — not a Sch B question)", "data_type": "integer", "sort_order": 27},
            {"fact_key": "actual_shareholder_count", "label": "Practice — actual number of shareholder records entered in the return", "data_type": "integer", "sort_order": 28,
             "notes": "Cross-check against page 1 item I."},
        ])

        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "Accounting method consistency", "rule_type": "validation",
             "formula": "b1_accounting_method must match method used on Page 1",
             "inputs": ["b1_accounting_method"], "outputs": [], "precedence": 1, "sort_order": 1,
             "description": "Accounting method on Schedule B question 1 must be consistent with the method used throughout the return."},
            {"rule_id": "R002", "title": "Shareholder count cross-check (page 1 item I)", "rule_type": "validation",
             "formula": "shareholder_count == actual_shareholder_count",
             "inputs": ["shareholder_count", "actual_shareholder_count"], "outputs": [], "precedence": 2, "sort_order": 2,
             "description": "PRACTICE RULE — the shareholder count lives on page 1 item I of the 2025 face "
                            "(not on Schedule B; the pre-2026-07-09 spec misplaced it here as 'B3'). It should "
                            "match the number of K-1s prepared."},
            {"rule_id": "R003", "title": "M-3 filing threshold", "rule_type": "conditional",
             "formula": "if l15_total_assets_eoy >= 10000000 then must_file_m3 = True",
             "inputs": ["l15_total_assets_eoy"], "outputs": ["must_file_m3"], "precedence": 3, "sort_order": 3,
             "description": "If total assets on the last day of the tax year are $10 MILLION or more, "
                            "Schedule M-3 is required instead of Schedule M-1 (i1120s 2025 p.49 verbatim; "
                            "corrected 2026-07-09 — the prior spec's $50M was a tax-law error; not a "
                            "Schedule B face question)."},
            {"rule_id": "R004", "title": "Section 1375 passive income tax trigger", "rule_type": "conditional",
             "formula": "if aep_from_ccorp AND excess_net_passive_income then section_1375_tax_applies",
             "inputs": ["aep_from_ccorp", "excess_net_passive_income"], "outputs": [], "precedence": 4, "sort_order": 4,
             "description": "PRACTICE RULE — §1375 tax applies when the S corporation has AE&P from C-Corp "
                            "years AND excess net passive income. (AE&P is not a 2025 Schedule B face question.)"},
            {"rule_id": "R005", "title": "100-shareholder limit check", "rule_type": "validation",
             "formula": "shareholder_count <= 100",
             "inputs": ["shareholder_count"], "outputs": [], "precedence": 5, "sort_order": 5,
             "description": "S corporations cannot have more than 100 shareholders (family members may elect to be treated as one)."},
            {"rule_id": "R006", "title": "Question 11 auto-answer (derived, overridable)", "rule_type": "calculation",
             "formula": "b11_under_250k = (q11_total_receipts < 250000) AND (l15_total_assets_eoy < 250000). "
                        "q11_total_receipts = p1_1a + p1_4 + p1_5 + K3a + K4 + K5a + K6 + K7 + K8a + K9 + K10 "
                        "+ f8825_2 + f8825_21 + f8825_22a, where the 'income or net gain' components "
                        "(K7/K8a/K9/K10, 8825 21/22a) and the 'all other income' components (p1 4/5) enter "
                        "only when positive — losses are excluded.",
             "inputs": ["q11_total_receipts", "l15_total_assets_eoy"], "outputs": ["b11_under_250k"],
             "precedence": 6, "sort_order": 6,
             "description": "Ken ruling 2026-07-09 (usability item 12): question 11 is AUTO-ANSWERED from "
                            "return context — a DERIVED value (YELLOW) the preparer can override; an "
                            "override always wins and is never recomputed over. SCHEDULE L AND M-1 BEHAVIOR "
                            "IS UNCHANGED: the derived Yes answers the face question only — it does NOT "
                            "suppress Schedule L/M-1 computation, printing, or balance diagnostics "
                            "(1120S_SCHL R007 remains the separate statement of the filing exception). "
                            "Component definition per the Instructions for Form 1120-S (2025), Question 11 "
                            "(see the verbatim excerpt). INTERPRETIVE NOTE: the instruction wording "
                            "'income or net gain' is read as include-only-when-positive; 'all other income "
                            "(page 1, lines 4 and 5)' is read the same way. Implementations that do not "
                            "capture Schedule K line 3a gross (only the 3c net) may substitute the net "
                            "when positive — an understatement flagged for review.",
             "notes": "TY2026 re-verify: thresholds are statutory-instruction values ($250,000) — confirm on the 2026 face."},
        ])
        # Refresh authority-link notes (get_or_create keeps stale relevance notes —
        # the s44 R003 $10M fix left this block's "$50M" note behind in prod;
        # caught + corrected in the s62 M-3 renumber trip).
        RuleAuthorityLink.objects.filter(form_rule__tax_form=form).delete()
        self._upsert_links(rules, sources, [
            ("R001", "IRS_2025_1120S_SCHB_INSTR", "primary", "Accounting method consistency requirement"),
            ("R002", "IRS_2025_1120S_INSTR_FULL", "secondary", "Page 1 item I shareholder count vs K-1s (practice cross-check)"),
            ("R003", "IRS_2025_1120S_M3_INSTR", "primary", "M-3 FILING threshold: $10M Schedule L total assets (i1120s 2025 p.49; the $50M figure is the complete-entirely tier)"),
            ("R004", "IRC_1374", "primary", "Section 1375 tax on excess net passive income with AE&P"),
            ("R005", "IRC_1361", "primary", "100-shareholder limit for S-Corp eligibility"),
            ("R006", "IRS_2025_1120S_SCHB_INSTR", "primary", "Q11 face text + total-receipts definition (verbatim excerpt)"),
        ])
        self._upsert_lines(form, [
            {"line_number": "B1", "description": "Check accounting method: cash / accrual / other (specify)", "line_type": "input", "sort_order": 1},
            {"line_number": "B2a", "description": "Business activity", "line_type": "input", "sort_order": 2},
            {"line_number": "B2b", "description": "Product or service", "line_type": "input", "sort_order": 3},
            {"line_number": "B3", "description": "Any shareholder a disregarded entity, trust, estate, or nominee? (Yes → attach Schedule B-1)", "line_type": "input", "sort_order": 4},
            {"line_number": "B4a", "description": "Own directly 20% or more, or directly/indirectly 50% or more, of any corporation? (complete (i)-(v))", "line_type": "input", "sort_order": 5},
            {"line_number": "B4b", "description": "Own directly 20% or more, or directly/indirectly 50% or more, of any partnership or beneficial interest of a trust? (complete (i)-(v))", "line_type": "input", "sort_order": 6},
            {"line_number": "B5a", "description": "Outstanding shares of restricted stock at year end? (if Yes: (i) restricted, (ii) non-restricted share counts)", "line_type": "input", "sort_order": 7},
            {"line_number": "B5b", "description": "Outstanding stock options, warrants, or similar instruments at year end? (if Yes: (i) shares outstanding, (ii) fully-diluted)", "line_type": "input", "sort_order": 8},
            {"line_number": "B6", "description": "Filed, or required to file, Form 8918 (Material Advisor Disclosure Statement)?", "line_type": "input", "sort_order": 9},
            {"line_number": "B7", "description": "Checkbox: issued publicly offered debt instruments with original issue discount (may need Form 8281)", "line_type": "input", "sort_order": 10},
            {"line_number": "B8", "description": "Net unrealized built-in gain reduced by net recognized built-in gain from prior years ($ entry)", "line_type": "input", "sort_order": 11},
            {"line_number": "B9", "description": "Section 163(j) election for real property trade/business or farming in effect?", "line_type": "input", "sort_order": 12},
            {"line_number": "B10", "description": "Satisfies one or more Form 8990 conditions (a) pass-through EBIE (b) $31M gross receipts (c) tax shelter? (Yes → attach Form 8990)", "line_type": "input", "sort_order": 13},
            {"line_number": "B11", "description": "Both conditions: (a) total receipts < $250,000 AND (b) EOY total assets < $250,000? (Yes → Schedules L and M-1 not required)", "line_type": "input", "source_rules": ["R006"], "sort_order": 14,
             "notes": "DERIVED default (R006) — YELLOW, preparer-overridable. Answering Yes does not change Schedule L/M-1 behavior in the implementation (Ken ruling 2026-07-09)."},
            {"line_number": "B12", "description": "Non-shareholder debt cancelled, forgiven, or modified to reduce principal?", "line_type": "input", "sort_order": 15},
            {"line_number": "B12_amount", "description": "If Yes, amount of principal reduction ($)", "line_type": "input", "sort_order": 16},
            {"line_number": "B13", "description": "QSub election terminated or revoked during the year?", "line_type": "input", "sort_order": 17},
            {"line_number": "B14a", "description": "Payments made that would require Form(s) 1099?", "line_type": "input", "sort_order": 18},
            {"line_number": "B14b", "description": "If Yes, did or will the corporation file required Form(s) 1099?", "line_type": "input", "sort_order": 19},
            {"line_number": "B15", "description": "Intends to self-certify as a Qualified Opportunity Fund? (Yes → attach Form 8996)", "line_type": "input", "sort_order": 20},
            {"line_number": "B15_amount", "description": "Form 8996 line 15 amount ($)", "line_type": "input", "sort_order": 21},
            {"line_number": "B16", "description": "Received (reward/award/payment) or sold/exchanged/disposed of a digital asset (or financial interest)?", "line_type": "input", "sort_order": 22},
            {"line_number": "B17", "description": "Reserved for future use", "line_type": "informational", "sort_order": 23},
        ])
        # In-loader stale-row DELETE — the pre-2026-07-09 numbering left rows
        # (B2, B4, B5, B18-B20 lines; b3_shareholder_count-style facts) that
        # update_or_create cannot remove and that contradict the 2025 face.
        _2025_B_LINES = {"B1", "B2a", "B2b", "B3", "B4a", "B4b", "B5a", "B5b", "B6", "B7",
                         "B8", "B9", "B10", "B11", "B12", "B12_amount", "B13", "B14a",
                         "B14b", "B15", "B15_amount", "B16", "B17"}
        stale_lines = FormLine.objects.filter(tax_form=form).exclude(line_number__in=_2025_B_LINES)
        if stale_lines.exists():
            self.stdout.write(f"  deleting {stale_lines.count()} stale pre-2025-face line rows")
            stale_lines.delete()
        _2025_B_FACTS = {
            "b1_accounting_method", "b2_business_activity", "b2_product_service",
            "b3_nominee_shareholder", "b4a_own_corp_20_50", "b4b_own_pship_20_50",
            "b5a_restricted_stock", "b5b_options_warrants", "b6_form_8918",
            "b7_public_oid_debt", "b8_nubig_amount", "b9_163j_election",
            "b10_form_8990_test", "b11_under_250k", "b12_debt_forgiven",
            "b12_principal_reduction", "b13_qsub_terminated", "b14a_1099_required",
            "b14b_1099_filed", "b15_qof", "b15_8996_penalty", "b16_digital_assets",
            "q11_total_receipts", "l15_total_assets_eoy",
            "aep_from_ccorp", "excess_net_passive_income",
            "shareholder_count", "actual_shareholder_count",
        }
        stale_facts = FormFact.objects.filter(tax_form=form).exclude(fact_key__in=_2025_B_FACTS)
        if stale_facts.exists():
            self.stdout.write(f"  deleting {stale_facts.count()} stale fact rows")
            stale_facts.delete()

        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D001", "title": "AE&P without tracking", "severity": "warning",
             "condition": "aep_from_ccorp == True AND no_aep_tracking_module",
             "message": "AE&P from C-Corp years is present but no AE&P tracking is set up."},
            {"diagnostic_id": "D002", "title": "Built-in gain without computation", "severity": "warning",
             "condition": "b8_nubig_amount > 0 AND no_section_1374_computation",
             "message": "Question 8 reports net unrealized built-in gain but no Section 1374 computation found."},
            {"diagnostic_id": "D003", "title": "1099 non-compliance", "severity": "warning",
             "condition": "b14a_1099_required == True AND b14b_1099_filed == False",
             "message": "Question 14a answered Yes but 14b answered No — required Form(s) 1099 not filed. Compliance risk."},
            {"diagnostic_id": "D004", "title": "Shareholder count mismatch", "severity": "error",
             "condition": "shareholder_count != actual_shareholder_count",
             "message": "Page 1 item I shareholder count does not match the actual number of shareholders entered."},
        ])
        self._upsert_tests(form, [
            {"scenario_name": "Standard S-Corp — all standard answers", "scenario_type": "normal",
             "inputs": {"b1_accounting_method": "cash", "shareholder_count": 2,
                        "b14a_1099_required": True, "b14b_1099_filed": True,
                        "aep_from_ccorp": False, "b8_nubig_amount": 0,
                        "l15_total_assets_eoy": 400000, "actual_shareholder_count": 2},
             "expected_outputs": {"must_file_m3": False, "shareholder_count_matches": True}, "sort_order": 1},
            {"scenario_name": "C-Corp conversion scenario", "scenario_type": "edge",
             "inputs": {"b1_accounting_method": "accrual", "shareholder_count": 1,
                        "aep_from_ccorp": True, "b8_nubig_amount": 120000,
                        "l15_total_assets_eoy": 400000, "actual_shareholder_count": 1},
             "expected_outputs": {"must_file_m3": False, "aep_tracking_required": True, "big_tax_applies": True}, "sort_order": 2},
            {"scenario_name": "Large entity — M-3 required", "scenario_type": "edge",
             "inputs": {"shareholder_count": 50, "l15_total_assets_eoy": 75000000,
                        "actual_shareholder_count": 50},
             "expected_outputs": {"must_file_m3": True}, "sort_order": 3},
            {"scenario_name": "Q11 auto-answer — small corp (Yes)", "scenario_type": "normal",
             "inputs": {"q11_total_receipts": 180000, "l15_total_assets_eoy": 90000},
             "expected_outputs": {"b11_under_250k": True}, "sort_order": 4,
             "notes": "R006: both under $250,000 → derived Yes. Schedule L/M-1 computation unchanged."},
            {"scenario_name": "Q11 auto-answer — assets at threshold (No)", "scenario_type": "edge",
             "inputs": {"q11_total_receipts": 249999, "l15_total_assets_eoy": 250000},
             "expected_outputs": {"b11_under_250k": False}, "sort_order": 5,
             "notes": "R006: 'less than' is strict — assets exactly $250,000 fail condition (b)."},
        ])
        self._upsert_form_links("1120S_SCHB", sources, [
            ("IRS_2025_1120S_SCHB_INSTR", "governs"),
            ("IRS_2025_1120S_INSTR", "informs"),
        ])
        self.stdout.write(self.style.SUCCESS("  Schedule B complete (2025 face + R006 Q11 auto-answer)."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Schedule L — Balance Sheet per Books
    # ═══════════════════════════════════════════════════════════════════════════

    # 2025 Schedule L face rows (f1120s.pdf 2025 p.4 verbatim, renumber unit #4
    # 2026-07-11): assets 1-15 (contra pairs 2a/2b, 10a/10b, 11a/11b, 13a/13b),
    # liabilities 16-21 (NO total-liabilities line on the face), equity 22-26,
    # total 27. The old block ran TWO fabricated numbering systems (facts had
    # total assets at l14/liabilities 15-21; the line map invented an L22
    # "Total liabilities" + an L28) — both replaced with the face.
    _SCHL_FACE_ROWS = [
        ("l1_cash", "L1 Cash"),
        ("l2a_trade_receivables", "L2a Trade notes and accounts receivable"),
        ("l2b_allowance", "L2b Less allowance for bad debts"),
        ("l3_inventories", "L3 Inventories"),
        ("l4_us_gov_obligations", "L4 U.S. government obligations"),
        ("l5_tax_exempt_securities", "L5 Tax-exempt securities"),
        ("l6_other_current_assets", "L6 Other current assets (attach statement)"),
        ("l7_loans_to_shareholders", "L7 Loans to shareholders"),
        ("l8_mortgage_re_loans", "L8 Mortgage and real estate loans"),
        ("l9_other_investments", "L9 Other investments (attach statement)"),
        ("l10a_buildings_gross", "L10a Buildings and other depreciable assets"),
        ("l10b_accum_depreciation", "L10b Less accumulated depreciation"),
        ("l11a_depletable_assets", "L11a Depletable assets"),
        ("l11b_accum_depletion", "L11b Less accumulated depletion"),
        ("l12_land", "L12 Land (net of any amortization)"),
        ("l13a_intangibles_gross", "L13a Intangible assets (amortizable only)"),
        ("l13b_accum_amortization", "L13b Less accumulated amortization"),
        ("l14_other_assets", "L14 Other assets (attach statement)"),
        ("l15_total_assets", "L15 Total assets"),
        ("l16_accounts_payable", "L16 Accounts payable"),
        ("l17_mortgages_short", "L17 Mortgages, notes, bonds payable in less than 1 year"),
        ("l18_other_current_liab", "L18 Other current liabilities (attach statement)"),
        ("l19_shareholder_loans", "L19 Loans from shareholders"),
        ("l20_mortgages_long", "L20 Mortgages, notes, bonds payable in 1 year or more"),
        ("l21_other_liabilities", "L21 Other liabilities (attach statement)"),
        ("l22_capital_stock", "L22 Capital stock"),
        ("l23_paid_in_capital", "L23 Additional paid-in capital"),
        ("l24_retained_earnings", "L24 Retained earnings"),
        ("l25_adjustments_equity", "L25 Adjustments to shareholders' equity (attach statement)"),
        ("l26_treasury_stock", "L26 Less cost of treasury stock"),
        ("l27_total_lse", "L27 Total liabilities and shareholders' equity"),
    ]

    def _load_schedule_l(self, sources):
        form = self._upsert_form(
            "1120S_SCHL", "Schedule L (Form 1120-S) — Balance Sheets per Books",
            ["1120S"],
            notes=(
                "BOY and EOY balance sheet, 2025 face (renumbered verbatim 2026-07-11, "
                "audit unit #4): Assets L1-15 (contra pairs 2a/2b, 10a/10b, 11a/11b, "
                "13a/13b), Liabilities L16-21 (the face has NO total-liabilities "
                "subtotal), Equity L22-26, Total L&SE L27. Not required if Schedule B "
                "question 11 is 'Yes' (receipts < $250K AND assets < $250K); when "
                "required, L15 column (d) also goes to page 1 item F (i1120s 2025 p.49)."
            ),
        )
        facts = []
        for i, (key, label) in enumerate(self._SCHL_FACE_ROWS):
            facts.append({"fact_key": f"{key}_boy", "label": f"{label} (BOY)",
                          "data_type": "decimal", "sort_order": 1 + i * 2})
            facts.append({"fact_key": f"{key}_eoy", "label": f"{label} (EOY)",
                          "data_type": "decimal", "sort_order": 2 + i * 2})
        facts += [
            # Cross-check facts
            {"fact_key": "total_receipts", "label": "Total receipts (for the Schedule B question 11 exception)", "data_type": "decimal", "sort_order": 90},
            {"fact_key": "m2_ending_balance", "label": "M-2 ending balance (for retained earnings tie)", "data_type": "decimal", "sort_order": 91},
            {"fact_key": "f1125a_boy_inventory", "label": "Form 1125-A line 1 beginning inventory (cross-form, for the R008 no-prior-year default)", "data_type": "decimal", "sort_order": 92},
        ]
        self._upsert_facts(form, facts)

        # In-loader stale-fact self-heal (the rename-orphan class guard): the old
        # block's second fabricated numbering (l14_total_assets, l15_accounts_
        # payable … l21_total_liabilities, l6_other_investments, l7_buildings…)
        # dies here.
        _SCHL_FACT_KEYS = {f["fact_key"] for f in facts}
        stale_facts = FormFact.objects.filter(tax_form=form).exclude(fact_key__in=_SCHL_FACT_KEYS)
        if stale_facts.exists():
            self.stdout.write(f"  deleting {stale_facts.count()} stale Schedule L facts: "
                              + ", ".join(sorted(stale_facts.values_list("fact_key", flat=True))))
            stale_facts.delete()

        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "L15 Total assets = sum of asset lines (contra rows subtract)", "rule_type": "calculation",
             "formula": ("l15 = l1 + (l2a - l2b) + l3 + l4 + l5 + l6 + l7 + l8 + l9 "
                         "+ (l10a - l10b) + (l11a - l11b) + l12 + (l13a - l13b) + l14 "
                         "(both BOY and EOY; the contra rows 2b/10b/11b/13b print in "
                         "columns (a)/(c) and subtract into (b)/(d))"),
             "inputs": ["l1_cash_boy", "l2a_trade_receivables_boy", "l2b_allowance_boy", "l3_inventories_boy",
                        "l4_us_gov_obligations_boy", "l5_tax_exempt_securities_boy", "l6_other_current_assets_boy",
                        "l7_loans_to_shareholders_boy", "l8_mortgage_re_loans_boy", "l9_other_investments_boy",
                        "l10a_buildings_gross_boy", "l10b_accum_depreciation_boy", "l11a_depletable_assets_boy",
                        "l11b_accum_depletion_boy", "l12_land_boy", "l13a_intangibles_gross_boy",
                        "l13b_accum_amortization_boy", "l14_other_assets_boy"],
             "outputs": ["l15_total_assets_boy", "l15_total_assets_eoy"], "precedence": 1, "sort_order": 1,
             "description": "2025 face: total assets is LINE 15 (the old spec said L14 and omitted lines 4/6/7/8 and the 10-13 contra pairs)."},
            {"rule_id": "R003", "title": "L27 Total liabilities and shareholders' equity", "rule_type": "calculation",
             "formula": ("l27 = l16 + l17 + l18 + l19 + l20 + l21 + l22 + l23 + l24 + l25 - l26 "
                         "(both BOY and EOY). The 2025 face has NO total-liabilities subtotal "
                         "line — liabilities 16-21 sum directly into L27 with the equity block."),
             "inputs": ["l16_accounts_payable_boy", "l17_mortgages_short_boy", "l18_other_current_liab_boy",
                        "l19_shareholder_loans_boy", "l20_mortgages_long_boy", "l21_other_liabilities_boy",
                        "l22_capital_stock_boy", "l23_paid_in_capital_boy", "l24_retained_earnings_boy",
                        "l25_adjustments_equity_boy", "l26_treasury_stock_boy"],
             "outputs": ["l27_total_lse_boy", "l27_total_lse_eoy"], "precedence": 3, "sort_order": 3},
            {"rule_id": "R004", "title": "Balance sheet must balance (L15 = L27)", "rule_type": "validation",
             "formula": "l15_total_assets == l27_total_lse (both BOY and EOY)",
             "inputs": ["l15_total_assets_boy", "l15_total_assets_eoy", "l27_total_lse_boy", "l27_total_lse_eoy"],
             "outputs": [], "precedence": 4, "sort_order": 4,
             "description": "Total assets (L15) must equal total liabilities & shareholders' equity (L27) for both BOY and EOY."},
            {"rule_id": "R005", "title": "Retained earnings tie to M-2", "rule_type": "validation",
             "formula": "l24_retained_earnings_eoy == m2_ending_balance",
             "inputs": ["l24_retained_earnings_eoy", "m2_ending_balance"], "outputs": [], "precedence": 5, "sort_order": 5,
             "description": "L24 (retained earnings) EOY should tie to Schedule M-2 ending balance."},
            {"rule_id": "R006", "title": "BOY inventories tie to prior year EOY", "rule_type": "validation",
             "formula": "l3_inventories_boy == prior_year_l3_inventories_eoy",
             "inputs": ["l3_inventories_boy"], "outputs": [], "precedence": 6, "sort_order": 6,
             "description": "L3 inventories BOY should equal prior year L3 inventories EOY. "
                            "(When no prior-year return exists, R008 supplies the default.)"},
            {"rule_id": "R007", "title": "Small corporation exception (Schedule B question 11)", "rule_type": "conditional",
             "formula": "schedule_l_not_required = (total_receipts < 250000 AND l15_total_assets_eoy < 250000)",
             "inputs": ["total_receipts", "l15_total_assets_eoy"], "outputs": ["schedule_l_not_required"], "precedence": 0, "sort_order": 7,
             "description": ("i1120s 2025 p.49 verbatim: 'Schedule L isn't required to be completed if "
                             "the corporation answered Yes to question 11 on Schedule B.' The $250K "
                             "receipts/assets test itself is the SCHB Q11 derivation (1120S_SCHB R006).")},
            {"rule_id": "R008", "title": "BOY inventory default when no prior-year return", "rule_type": "conditional",
             "formula": "IF no prior-year return prepared AND l3_inventories_boy is blank "
                        "THEN l3_inventories_boy defaults to f1125a_boy_inventory (fill-blank-only; preparer entry always wins)",
             "inputs": ["f1125a_boy_inventory"], "outputs": ["l3_inventories_boy"], "precedence": 7, "sort_order": 8,
             "description": "Ken ruling 2026-07-09: BOY inventory normally carries from the prior-year EOY (R006). "
                            "Only when no prior-year return was prepared does BOY inventory default from Form "
                            "1125-A line 1 (beginning inventory). Fill-blank-only — never overwrites a preparer "
                            "entry; the preparer may change or clear it."},
            {"rule_id": "R009", "title": "L15(d) total assets → page 1 item F", "rule_type": "validation",
             "formula": "page1_item_f == l15_total_assets_eoy",
             "inputs": ["l15_total_assets_eoy"], "outputs": [], "precedence": 8, "sort_order": 9,
             "description": ("i1120s 2025 p.49 verbatim: 'If the corporation is required to complete "
                             "Schedule L, include total assets reported on Schedule L, line 15, "
                             "column (d), on page 1, item F.'")},
        ])

        # In-loader stale-rule self-heal: R002 ("Total liabilities") is DELETED —
        # the 2025 face has no total-liabilities line (it was one of the two
        # fabricated numbering systems).
        _SCHL_RULE_IDS = {"R001", "R003", "R004", "R005", "R006", "R007", "R008", "R009"}
        stale_rules = FormRule.objects.filter(tax_form=form).exclude(rule_id__in=_SCHL_RULE_IDS)
        if stale_rules.exists():
            self.stdout.write(f"  deleting {stale_rules.count()} stale Schedule L rules: "
                              + ", ".join(sorted(stale_rules.values_list("rule_id", flat=True))))
            stale_rules.delete()

        self._upsert_links(rules, sources, [
            ("R001", "IRS_2025_1120S_SCHL_INSTR", "primary", "Asset line summation — total assets = LINE 15 (i1120s p.49: 'total assets reported on Schedule L, line 15, column (d)')"),
            ("R003", "IRS_2025_1120S_SCHL_INSTR", "primary", "L&SE total = liabilities 16-21 + equity 22-25 − 26 (2025 face: no total-liabilities subtotal)"),
            ("R004", "IRS_2025_1120S_SCHL_INSTR", "primary", "L15 must equal L27"),
            ("R005", "IRS_2025_1120S_SCHL_INSTR", "primary", "L24 ties to M-2 ending balance"),
            ("R006", "IRS_2025_1120S_INSTR", "secondary", "BOY should equal prior year EOY"),
            ("R007", "IRS_2025_1120S_SCHL_INSTR", "primary", "i1120s p.49 verbatim: not required if Schedule B question 11 is Yes"),
            ("R008", "IRS_2025_1120S_SCHL_INSTR", "secondary",
             "Line 3 = inventories per the instructions; the no-prior-year default from 1125-A line 1 "
             "is practice logic (Ken ruling 2026-07-09)"),
            ("R009", "IRS_2025_1120S_SCHL_INSTR", "primary", "i1120s p.49 verbatim: L15 column (d) → page 1 item F"),
        ])
        self._upsert_lines(form, [
            {"line_number": "L1", "description": "Cash", "line_type": "input", "sort_order": 1},
            {"line_number": "L2a", "description": "Trade notes and accounts receivable", "line_type": "input", "sort_order": 2},
            {"line_number": "L2b", "description": "Less allowance for bad debts", "line_type": "input", "sort_order": 3},
            {"line_number": "L3", "description": "Inventories", "line_type": "input", "sort_order": 4},
            {"line_number": "L4", "description": "U.S. government obligations", "line_type": "input", "sort_order": 5},
            {"line_number": "L5", "description": "Tax-exempt securities (see instructions)", "line_type": "input", "sort_order": 6},
            {"line_number": "L6", "description": "Other current assets (attach statement)", "line_type": "input", "sort_order": 7},
            {"line_number": "L7", "description": "Loans to shareholders", "line_type": "input", "sort_order": 8},
            {"line_number": "L8", "description": "Mortgage and real estate loans", "line_type": "input", "sort_order": 9},
            {"line_number": "L9", "description": "Other investments (attach statement)", "line_type": "input", "sort_order": 10},
            {"line_number": "L10a", "description": "Buildings and other depreciable assets", "line_type": "input", "sort_order": 11},
            {"line_number": "L10b", "description": "Less accumulated depreciation", "line_type": "input", "sort_order": 12},
            {"line_number": "L11a", "description": "Depletable assets", "line_type": "input", "sort_order": 13},
            {"line_number": "L11b", "description": "Less accumulated depletion", "line_type": "input", "sort_order": 14},
            {"line_number": "L12", "description": "Land (net of any amortization)", "line_type": "input", "sort_order": 15},
            {"line_number": "L13a", "description": "Intangible assets (amortizable only)", "line_type": "input", "sort_order": 16},
            {"line_number": "L13b", "description": "Less accumulated amortization", "line_type": "input", "sort_order": 17},
            {"line_number": "L14", "description": "Other assets (attach statement)", "line_type": "input", "sort_order": 18},
            {"line_number": "L15", "description": "Total assets", "line_type": "total", "source_rules": ["R001"], "sort_order": 19,
             "notes": "Column (d) also goes to page 1 item F when Schedule L is required (i1120s 2025 p.49; R009)."},
            {"line_number": "L16", "description": "Accounts payable", "line_type": "input", "sort_order": 20},
            {"line_number": "L17", "description": "Mortgages, notes, bonds payable in less than 1 year", "line_type": "input", "sort_order": 21},
            {"line_number": "L18", "description": "Other current liabilities (attach statement)", "line_type": "input", "sort_order": 22},
            {"line_number": "L19", "description": "Loans from shareholders", "line_type": "input", "sort_order": 23},
            {"line_number": "L20", "description": "Mortgages, notes, bonds payable in 1 year or more", "line_type": "input", "sort_order": 24},
            {"line_number": "L21", "description": "Other liabilities (attach statement)", "line_type": "input", "sort_order": 25},
            {"line_number": "L22", "description": "Capital stock", "line_type": "input", "sort_order": 26},
            {"line_number": "L23", "description": "Additional paid-in capital", "line_type": "input", "sort_order": 27},
            {"line_number": "L24", "description": "Retained earnings", "line_type": "input", "sort_order": 28},
            {"line_number": "L25", "description": "Adjustments to shareholders' equity (attach statement)", "line_type": "input", "sort_order": 29},
            {"line_number": "L26", "description": "Less cost of treasury stock", "line_type": "input", "sort_order": 30},
            {"line_number": "L27", "description": "Total liabilities and shareholders' equity", "line_type": "total", "source_rules": ["R003"], "sort_order": 31},
        ])

        # In-loader stale-line self-heal: the fabricated L22 "Total liabilities"
        # row is overwritten in place (same line_number, face description); L11
        # (split to 11a/11b) and L28 (the face total is L27) are DELETED.
        _SCHL_LINES = {
            "L1", "L2a", "L2b", "L3", "L4", "L5", "L6", "L7", "L8", "L9",
            "L10a", "L10b", "L11a", "L11b", "L12", "L13a", "L13b", "L14", "L15",
            "L16", "L17", "L18", "L19", "L20", "L21",
            "L22", "L23", "L24", "L25", "L26", "L27",
        }
        stale_lines = FormLine.objects.filter(tax_form=form).exclude(line_number__in=_SCHL_LINES)
        if stale_lines.exists():
            self.stdout.write(f"  deleting {stale_lines.count()} stale Schedule L line rows: "
                              + ", ".join(sorted(stale_lines.values_list("line_number", flat=True))))
            stale_lines.delete()
        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D001", "title": "Balance sheet out of balance (BOY)", "severity": "error",
             "condition": "l15_total_assets_boy != l27_total_lse_boy",
             "message": "BOY balance sheet out of balance: Total assets (L15) does not equal total liabilities & shareholders' equity (L27)."},
            {"diagnostic_id": "D002", "title": "Balance sheet out of balance (EOY)", "severity": "error",
             "condition": "l15_total_assets_eoy != l27_total_lse_eoy",
             "message": "EOY balance sheet out of balance: Total assets (L15) does not equal total liabilities & shareholders' equity (L27)."},
            {"diagnostic_id": "D003", "title": "Retained earnings don't tie to M-2", "severity": "warning",
             "condition": "l24_retained_earnings_eoy != m2_ending_balance",
             "message": "L24 retained earnings (EOY) does not match Schedule M-2 ending balance."},
            {"diagnostic_id": "D004", "title": "Negative cash balance", "severity": "warning",
             "condition": "l1_cash_eoy < 0",
             "message": "Cash balance is negative at end of year. Verify bank accounts and outstanding items."},
            {"diagnostic_id": "D005", "title": "Inventory without COGS", "severity": "warning",
             "condition": "l3_inventories_eoy > 0 AND no_form_1125a",
             "message": "Inventory on L3 but no Form 1125-A (COGS) filed."},
            {"diagnostic_id": "D006", "title": "Shareholder loans without interest", "severity": "warning",
             "condition": "l19_shareholder_loans_eoy > 0 AND page1_interest_expense == 0",
             "message": "Loans from shareholders on L19 but no interest expense on Page 1. Verify below-market loan rules."},
            {"diagnostic_id": "D007", "title": "Total assets don't match page 1 item F", "severity": "warning",
             "condition": "schedule_l_required AND page1_item_f != l15_total_assets_eoy",
             "message": "Page 1 item F should equal Schedule L line 15 column (d) when Schedule L is required (i1120s 2025 p.49)."},
        ])
        self._upsert_tests(form, [
            {"scenario_name": "Balanced balance sheet", "scenario_type": "normal",
             "inputs": {
                 "l1_cash_boy": 50000, "l10a_buildings_gross_boy": 220000, "l10b_accum_depreciation_boy": 20000,
                 "l12_land_boy": 100000, "l15_total_assets_boy": 350000,
                 "l16_accounts_payable_boy": 20000, "l20_mortgages_long_boy": 150000,
                 "l22_capital_stock_boy": 1000, "l24_retained_earnings_boy": 179000, "l27_total_lse_boy": 350000,
             },
             "expected_outputs": {"balance_sheet_balances_boy": True, "balance_sheet_balances_eoy": True},
             "notes": "R001: 50,000 + (220,000 − 20,000) + 100,000 = 350,000 = L27 (16 20,000 + 20 150,000 + 22 1,000 + 24 179,000).",
             "sort_order": 1},
            {"scenario_name": "Out-of-balance balance sheet", "scenario_type": "failure",
             "inputs": {
                 "l15_total_assets_eoy": 500000, "l27_total_lse_eoy": 490000,
             },
             "expected_outputs": {"balance_sheet_balances_eoy": False, "diagnostic_D002_fires": True}, "sort_order": 2},
            {"scenario_name": "Small corporation exception", "scenario_type": "edge",
             "inputs": {"total_receipts": 180000, "l15_total_assets_eoy": 200000},
             "expected_outputs": {"schedule_l_not_required": True}, "sort_order": 3},
            {"scenario_name": "Contra-pair netting — R001 sums the face rows", "scenario_type": "normal",
             "inputs": {
                 "l2a_trade_receivables_eoy": 80000, "l2b_allowance_eoy": 5000,
                 "l11a_depletable_assets_eoy": 40000, "l11b_accum_depletion_eoy": 15000,
                 "l13a_intangibles_gross_eoy": 90000, "l13b_accum_amortization_eoy": 30000,
                 "l4_us_gov_obligations_eoy": 10000, "l7_loans_to_shareholders_eoy": 25000,
             },
             "expected_outputs": {"l15_total_assets_eoy": 195000},
             "notes": ("(80,000−5,000) + (40,000−15,000) + (90,000−30,000) + 10,000 + 25,000 = 195,000. "
                       "Pins the four asset lines (4/6/7/8) and the three contra pairs the old R001 "
                       "omitted entirely."),
             "sort_order": 4},
        ])

        # In-loader stale-scenario self-heal (the RET-G5 rename-orphan guard).
        _SCHL_SCENARIOS = {
            "Balanced balance sheet", "Out-of-balance balance sheet",
            "Small corporation exception", "Contra-pair netting — R001 sums the face rows",
        }
        stale_tests = TestScenario.objects.filter(tax_form=form).exclude(scenario_name__in=_SCHL_SCENARIOS)
        if stale_tests.exists():
            self.stdout.write(f"  deleting {stale_tests.count()} stale Schedule L scenarios: "
                              + ", ".join(sorted(stale_tests.values_list("scenario_name", flat=True))))
            stale_tests.delete()
        self._upsert_form_links("1120S_SCHL", sources, [
            ("IRS_2025_1120S_SCHL_INSTR", "governs"),
            ("IRS_2025_1120S_INSTR", "informs"),
        ])
        self.stdout.write(self.style.SUCCESS("  Schedule L complete."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Form 6198 — At-Risk Limitations
    # Renumbered to the REAL face 2026-07-12 (audit-ledger unit #6): the old block
    # carried a FABRICATED line_map (an invented "prior year unallowed losses"
    # line 2, deductible loss on 20 instead of 21, 13 of 21 face lines missing —
    # matched no published revision). Rebuilt verbatim vs f6198.pdf (Rev. November
    # 2025, resources/irs_forms/2025/, pymupdf-extracted 2026-07-12) + i6198
    # (Rev. November 2025, fetched from irs.gov 2026-07-12). The IRC §465 rule
    # substance (composition / QNF exception / loss cap / recapture / ordering)
    # was sound and is KEPT, re-keyed to the face.
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_6198(self, sources):
        form = self._upsert_form(
            "6198", "Form 6198 — At-Risk Limitations",
            ["1040"],
            notes=(
                "Face = Rev. November 2025 (f6198.pdf, verified verbatim 2026-07-12). "
                "Limits loss deductions to the amount at risk (§465). Filed by individuals "
                "(incl. Schedules C, E, F filers), estates, trusts, and certain closely held "
                "C corporations (i6198 Who Must File) — applied at the PARTNER/SHAREHOLDER "
                "level for 1065/1120-S activities, one form per at-risk activity (see the "
                "aggregation/separation rules). Ordering: basis -> §465 at-risk -> §469 "
                "passive (8582/8810) -> §461(l)."
            ),
        )

        # Refresh the governing-instruction excerpts IN-LOADER so the scoped seed
        # fixes prod: the old "At-risk computation" excerpt was a PARAPHRASE (the
        # fabricated-excerpt class, s58 audit rule). Same labels are kept where a
        # row exists (update_or_create keys on label — a label change would orphan
        # the old row); text replaced with i6198 (Rev. 11-2025) verbatim.
        # forms_supporting.py carries the same excerpts for load_all_federal reruns.
        instr = sources.get("IRS_2025_6198_INSTR")
        if instr:
            AuthoritySource.objects.filter(pk=instr.pk).update(
                citation="Instructions for Form 6198 (Rev. November 2025)")
            for exc in _6198_INSTR_EXCERPTS:
                AuthorityExcerpt.objects.update_or_create(
                    authority_source=instr, excerpt_label=exc["excerpt_label"],
                    defaults=exc)
        self._upsert_facts(form, [
            # ── Header ──
            {"fact_key": "activity_description", "label": "Description of activity", "data_type": "string",
             "required": True, "sort_order": 1,
             "notes": "Face header. i6198: after the description, if applicable, enter the name and identifying number of the partnership or S corporation."},
            # ── Part I — current year profit (loss), INCLUDING prior year nondeductible amounts ──
            {"fact_key": "ordinary_income_loss", "label": "L1 — Ordinary income (loss) from the activity", "data_type": "decimal", "sort_order": 2,
             "notes": "Partners/S-corp shareholders: Schedule K-1 box 1 PLUS any prior year ordinary loss not deducted because of the at-risk rules (i6198 Line 1). Excludes disposition gains/losses (those go on 2a-2c) and casualty/theft + investment interest (2c/4)."},
            {"fact_key": "gain_loss_sched_d", "label": "L2a — Gain (loss) from dispositions reported on Schedule D", "data_type": "decimal", "sort_order": 3,
             "notes": "Sale/other disposition of assets used in the activity (or of the interest in the activity). Entered WITHOUT regard to at-risk, capital-loss, or passive limits (i6198 Lines 2a-2c)."},
            {"fact_key": "gain_loss_4797", "label": "L2b — Gain (loss) from dispositions reported on Form 4797", "data_type": "decimal", "sort_order": 4},
            {"fact_key": "gain_loss_other_form", "label": "L2c — Gain (loss) from dispositions reported on another form or schedule", "data_type": "decimal", "sort_order": 5},
            {"fact_key": "other_form_label", "label": "L2c — form number or schedule letter (dotted-line entry)", "data_type": "string", "sort_order": 6,
             "notes": "Face: 'Enter the form number or schedule letter to the left of the entry space for line 2c' (i6198 p.3; e.g. 'Form 4684')."},
            {"fact_key": "other_income_gains", "label": "L3 — Other income and gains from the activity (Sch K-1) not on lines 1-2c", "data_type": "decimal", "sort_order": 7},
            {"fact_key": "other_deductions_losses", "label": "L4 — Other deductions and losses from the activity not on lines 1-2c (negative)", "data_type": "decimal", "sort_order": 8,
             "notes": "Face prints parentheses (a loss entry). Includes the ALLOWABLE Form 4952 investment interest attributable to the at-risk activity, plus prior-year investment interest limited by at-risk (i6198 Line 4)."},
            # ── Part II — simplified computation ──
            {"fact_key": "adjusted_basis_first_day", "label": "L6 — Adjusted basis (§1011) in the activity on the first day of the tax year", "data_type": "decimal",
             "validation_rule": "must be >= 0 (face: 'Do not enter less than zero')", "sort_order": 9,
             "notes": "Sole proprietors do NOT reduce by liabilities (Pub. 551); partners Pub. 541; S-corp shareholders per the 1120-S instructions (i6198 Line 6)."},
            {"fact_key": "increases_tax_year", "label": "L7 — Increases for the tax year", "data_type": "decimal", "sort_order": 10,
             "notes": "i6198 Line 7 items (1)-(4): net FMV of own non-activity property securing nonrecourse loans; cash + adjusted basis of property contributed; personally-liable loans AND qualified nonrecourse financing; excess percentage depletion. Do NOT include current-year income/gains from lines 1-3."},
            {"fact_key": "qualified_nonrecourse_financing", "label": "Qualified nonrecourse financing component of increases (real property)", "data_type": "decimal", "sort_order": 11,
             "notes": "COMPONENT breakdown of L7/L16 item (3) kept for D002. §465(b)(6) + Reg. 1.465-27: no personal liability, borrowed for holding real property, secured by real property used in the activity, not convertible, government or qualified-person lender."},
            {"fact_key": "decreases_tax_year", "label": "L9 — Decreases for the tax year", "data_type": "decimal", "sort_order": 12,
             "notes": "i6198 Line 9 items (1)-(5): nonrecourse conversions, loss-protected amounts, related/interested-party loans, withdrawals and distributions, contributed-property nonrecourse liabilities. Do NOT include current-year deductions/losses from lines 1-4."},
            # ── Part III — detailed computation ──
            {"fact_key": "investment_at_effective_date", "label": "L11 — Investment in the activity at the effective date", "data_type": "decimal",
             "validation_rule": "must be >= 0 (face: 'Do not enter less than zero')", "sort_order": 13,
             "notes": "Non-partner/shareholder filers use the published Line 11 Worksheet (cash-basis add lines 1,2,4,6,7,8; accrual-basis continue 10a-14). Partners/shareholders: basis of the investment at the effective date (i6198 pp.4-5). Skip 11-14 if Part III was completed for the prior year."},
            {"fact_key": "increases_at_effective_date", "label": "L12 — Increases at effective date", "data_type": "decimal", "sort_order": 14,
             "notes": "Incl. pre-effective-date losses for which there were equal or greater amounts not at risk at year end (the published Line 12 Worksheet, i6198 p.6)."},
            {"fact_key": "decreases_at_effective_date", "label": "L14 — Decreases at effective date", "data_type": "decimal", "sort_order": 15},
            {"fact_key": "line15_basis", "label": "L15 checkbox — amount-at-risk source", "data_type": "choice",
             "choices": ["effective_date", "prior_year_19b"], "sort_order": 16,
             "notes": "Face box a: at effective date = L13 - L14 (not below zero). Box b: prior year Form 6198 line 19b — the face + i6198 CAUTION: 'Do not enter the amount from line 10b of your prior year form.'"},
            {"fact_key": "prior_year_line19b", "label": "L15b — amount from the prior year Form 6198, line 19b", "data_type": "decimal", "sort_order": 17},
            {"fact_key": "increases_since", "label": "L16 — Increases since effective date / end of prior year", "data_type": "decimal", "sort_order": 18,
             "notes": "i6198 Line 16 items (1)-(9) incl. contributions, personally-liable loans + QNF, total net income since (profit years only, not below zero), §465(e) amounts previously recaptured, shareholder loans TO the S corporation. Excludes current-year income/gains."},
            {"fact_key": "since_when_16", "label": "L16 checkbox — increases measured since", "data_type": "choice",
             "choices": ["effective_date", "end_of_prior_year"], "sort_order": 19,
             "notes": "Box b (end of prior year) when Part III was completed for the prior tax year."},
            {"fact_key": "decreases_since", "label": "L18 — Decreases since effective date / end of prior year", "data_type": "decimal", "sort_order": 20,
             "notes": "i6198 Line 18 items (1)-(8) incl. withdrawals/distributions, recourse-to-nonrecourse conversions, net-loss years deducted since ('Your prior tax year line 21 deductible loss reduces your at-risk investment as of the beginning of your current tax year'). Excludes current-year losses/deductions."},
            {"fact_key": "since_when_18", "label": "L18 checkbox — decreases measured since", "data_type": "choice",
             "choices": ["effective_date", "end_of_prior_year"], "sort_order": 21},
        ])

        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "Part I — L5 current year profit (loss) = combine lines 1-4", "rule_type": "calculation",
             "formula": "line_5 = ordinary_income_loss + gain_loss_sched_d + gain_loss_4797 + gain_loss_other_form + other_income_gains + other_deductions_losses  # L4 entered as a negative (face parentheses)",
             "inputs": ["ordinary_income_loss", "gain_loss_sched_d", "gain_loss_4797",
                        "gain_loss_other_form", "other_income_gains", "other_deductions_losses"],
             "outputs": ["current_year_profit_loss"], "precedence": 1, "sort_order": 1,
             "description": "Face L5: 'Current year profit (loss) from the activity. Combine lines 1 through 4.' Amounts include prior-year nondeductible (at-risk-limited) amounts per the Part I heading. If L5 is a PROFIT, the rest of the form may be unnecessary (report Part I items normally, attach the 6198) — but recapture can still apply (R007). If L5 is a loss, income/gains on lines 1-3 remain fully reportable; deductions/losses are allowed to the extent of that income plus the Part II/III amount at risk (i6198 Line 5 + example)."},
            {"rule_id": "R002", "title": "Part II — simplified amount at risk (L6-L10b)", "rule_type": "calculation",
             "formula": "line_8 = adjusted_basis_first_day + increases_tax_year; line_10a = line_8 - decreases_tax_year; line_10b = line_10a if line_10a > 0 else 0",
             "inputs": ["adjusted_basis_first_day", "increases_tax_year", "decreases_tax_year"],
             "outputs": ["amount_at_risk_simplified"], "precedence": 2, "sort_order": 2,
             "description": "Face L6-L10b. Usable only if the adjusted basis in the activity is known (i6198 Part II). L10b face: 'If line 10a is more than zero, enter that amount here and go to line 20 (or complete Part III). Otherwise, enter -0- and see Pub. 925 for information on the recapture rules.' §465(b) composition rides the L7/L9 item lists (see the fact notes): contributions + personally-liable loans + qualified nonrecourse financing increase; nonrecourse/protected/related-party amounts and withdrawals decrease."},
            {"rule_id": "R003", "title": "Part III — detailed amount at risk (L11-L19b)", "rule_type": "calculation",
             "formula": "line_13 = investment_at_effective_date + increases_at_effective_date; line_15 = max(0, line_13 - decreases_at_effective_date) if line15_basis == 'effective_date' else prior_year_line19b; line_17 = line_15 + increases_since; line_19a = line_17 - decreases_since; line_19b = line_19a if line_19a > 0 else 0",
             "inputs": ["investment_at_effective_date", "increases_at_effective_date",
                        "decreases_at_effective_date", "line15_basis", "prior_year_line19b",
                        "increases_since", "decreases_since"],
             "outputs": ["amount_at_risk_detailed"], "precedence": 2, "sort_order": 3,
             "description": "Face L11-L19b. May allow a LARGER amount at risk than Part II (i6198: 'Part III is a longer method... which may allow a larger amount at risk'). L15 box b carries the prior year line 19b — NEVER the prior year 10b (face + i6198 caution). If Part III was completed for the prior year, skip 11-14 and measure 16/18 'since the end of your prior tax year' (boxes b)."},
            {"rule_id": "R004", "title": "L20 amount at risk = larger of 10b or 19b", "rule_type": "calculation",
             "formula": "line_20 = max(line_10b, line_19b)",
             "inputs": [], "outputs": ["amount_at_risk"], "precedence": 3, "sort_order": 4,
             "description": "Face L20 verbatim: 'Amount at risk. Enter the larger of line 10b or line 19b.' A filer may complete both parts and take the larger."},
            {"rule_id": "R005", "title": "L21 deductible loss = smaller of the L5 loss (as positive) or L20", "rule_type": "calculation",
             "formula": "line_21 = -min(abs(line_5), line_20) if line_5 < 0 else None  # no limitation computed on a profit year",
             "inputs": [], "outputs": ["deductible_loss"], "precedence": 4, "sort_order": 5,
             "description": "Face L21: 'Deductible loss. Enter the smaller of the line 5 loss (treated as a positive number) or line 20' — printed in parentheses. Published pins (i6198 Line 21 Examples): L5 (400)/L20 1,000 -> (400); L5 (1,600)/L20 1,200 -> (1,200); L5 (800)/L20 0 -> -0-. The disallowed excess is suspended under §465 and carried to next year; when L21 spans multiple Part I deduction items, each item is allowed pro rata (item / total L5 loss fraction, i6198 p.8)."},
            {"rule_id": "R006", "title": "Nonrecourse amounts not at risk; qualified nonrecourse financing exception", "rule_type": "validation",
             "formula": "nonrecourse loans / loss-protected amounts / interested-or-related-party loans are NOT at risk (i6198 Amounts Not at Risk (1)-(4)); EXCEPTION: qualified nonrecourse financing secured by real property used in an activity of holding real property (other than mineral property) IS at risk",
             "inputs": ["qualified_nonrecourse_financing"], "outputs": [], "precedence": 0, "sort_order": 6,
             "description": "§465(b)(6) + Reg. 1.465-27. QNF = no one personally liable, borrowed in connection with holding real property, secured by real property used in the activity, not convertible debt, and loaned/guaranteed by a government or borrowed from a qualified person (a regular money-lender that is not related, not the seller, and not fee-interested)."},
            {"rule_id": "R007", "title": "Recapture when the amount at risk falls below zero", "rule_type": "conditional",
             "formula": "if amount_at_risk_at_close < 0 then recapture income (§465(e)) — flagged when line_10b == 0 or line_19b == 0; possible EVEN IF line_5 shows a profit",
             "inputs": [], "outputs": [], "precedence": 5, "sort_order": 7,
             "description": "§465(e). Face L10b/L19b route a zero to Pub. 925 recapture. i6198 Line 5 caution verbatim: 'Even if you have a current year profit on line 5, you may have recapture income if you received a distribution or had a transaction during the year that reduced your amount at risk in the activity to less than zero at the close of the tax year.'"},
            {"rule_id": "R008", "title": "Ordering — basis, then §465 at-risk, then §469 passive", "rule_type": "validation",
             "formula": "basis limitation -> §465 at-risk (this form) -> §469 passive (Form 8582 / 8810) -> §461(l)",
             "inputs": [], "outputs": [], "precedence": 0, "sort_order": 8,
             "description": "Face Note after L21 verbatim: 'If the loss is from a passive activity, see the Instructions for Form 8582... or the Instructions for Form 8810... If only part of the loss is subject to the passive activity loss rules, report only that part on Form 8582 or Form 8810, whichever applies.' Reg. 1.469-2T(d)(6) puts §465 before §469; the FORM_8582 spec's R-8582-ATRISK-ORDER routes here."},
            {"rule_id": "R009", "title": "Prior year at-risk-disallowed amounts ride the current-year Part I entries", "rule_type": "validation",
             "formula": "partners / S-corp shareholders: include prior-year at-risk-limited losses IN the amounts entered on lines 1-4; other taxpayers: include them on the current-year form or schedule BEFORE starting Part I",
             "inputs": [], "outputs": [], "precedence": 0, "sort_order": 9,
             "description": "i6198 Part I verbatim (partners/shareholders): 'If you have a loss or a deduction from an earlier tax year that you could not deduct because of the at-risk rules, these losses and deductions must be included in the current year amounts you enter in Part I' — e.g. a prior-year box 1 loss of $1,500 limited to $500 puts the $1,000 plus the current-year box 1 amount on line 1. (This is what the old fabricated 'line 2 — prior year unallowed losses' row distorted: no such face line exists.)"},
        ])

        # Refresh authority-link notes (get_or_create keeps stale relevance notes —
        # the s59 renumber-unit rule).
        RuleAuthorityLink.objects.filter(form_rule__tax_form=form).delete()
        self._upsert_links(rules, sources, [
            ("R001", "IRS_2025_6198_INSTR", "primary", "Part I face lines 1-4 + Line 5 instructions (Rev. 11-2025)"),
            ("R001", "IRC_465", "secondary", "Section 465(a) — the loss being limited"),
            ("R002", "IRS_2025_6198_INSTR", "primary", "Part II face L6-L10b + Line 7/9 item lists"),
            ("R002", "IRC_465", "primary", "Section 465(b) — amounts considered at risk"),
            ("R003", "IRS_2025_6198_INSTR", "primary", "Part III face L11-L19b + the L15 prior-year-19b caution"),
            ("R003", "IRC_465", "secondary", "Section 465(b) — detailed at-risk computation"),
            ("R004", "IRS_2025_6198_INSTR", "primary", "Face L20 — larger of line 10b or line 19b"),
            ("R005", "IRS_2025_6198_INSTR", "primary", "Face L21 + Line 21 instructions and published examples"),
            ("R005", "IRC_465", "primary", "Section 465(a) — loss limited to the amount at risk"),
            ("R006", "IRC_465", "primary", "Section 465(b)(6) — qualified nonrecourse financing exception"),
            ("R006", "IRS_2025_6198_INSTR", "secondary", "Qualified Nonrecourse Financing definition (Reg. 1.465-27)"),
            ("R007", "IRC_465", "primary", "Section 465(e) — recapture when at-risk goes below zero"),
            ("R007", "IRS_2025_6198_INSTR", "secondary", "L10b/L19b zero -> Pub. 925 recapture; Line 5 profit-year caution"),
            ("R008", "IRC_465", "primary", "At-risk before passive activity — ordering rule"),
            ("R008", "IRC_469", "secondary", "Section 469 applies after section 465"),
            ("R008", "IRS_2025_6198_INSTR", "secondary", "Face Note after L21 — route passive losses to 8582/8810"),
            ("R009", "IRS_2025_6198_INSTR", "primary", "Part I — prior year nondeductible amounts (verbatim)"),
        ])
        self._upsert_lines(form, [
            # ── Part I — Current Year Profit (Loss) From the Activity, Including
            #    Prior Year Nondeductible Amounts (face verbatim, Rev. 11-2025) ──
            {"line_number": "1", "description": "Ordinary income (loss) from the activity (see instructions)",
             "line_type": "input", "source_facts": ["ordinary_income_loss"], "sort_order": 1},
            {"line_number": "2a", "description": "Gain (loss) from the sale or other disposition of assets used in the activity (or of your interest in the activity) that you are reporting on: Schedule D",
             "line_type": "input", "source_facts": ["gain_loss_sched_d"], "sort_order": 2},
            {"line_number": "2b", "description": "— reported on Form 4797",
             "line_type": "input", "source_facts": ["gain_loss_4797"], "sort_order": 3},
            {"line_number": "2c", "description": "— reported on other form or schedule (enter the form number or schedule letter to the left of the entry space)",
             "line_type": "input", "source_facts": ["gain_loss_other_form", "other_form_label"], "sort_order": 4},
            {"line_number": "3", "description": "Other income and gains from the activity, from Schedule K-1 (Form 1065) or Schedule K-1 (Form 1120-S), that were not included on lines 1 through 2c",
             "line_type": "input", "source_facts": ["other_income_gains"], "sort_order": 5},
            {"line_number": "4", "description": "Other deductions and losses from the activity, including investment interest expense allowed from Form 4952, that were not included on lines 1 through 2c (parenthesized loss entry)",
             "line_type": "input", "source_facts": ["other_deductions_losses"], "sort_order": 6},
            {"line_number": "5", "description": "Current year profit (loss) from the activity. Combine lines 1 through 4. See the instructions before completing the rest of this form",
             "line_type": "subtotal", "calculation": "combine lines 1 through 4",
             "source_rules": ["R001"], "sort_order": 7},
            # ── Part II — Simplified Computation of Amount at Risk ──
            {"line_number": "6", "description": "Adjusted basis (as defined in section 1011) in the activity (or in your interest in the activity) on the first day of the tax year. Do not enter less than zero",
             "line_type": "input", "source_facts": ["adjusted_basis_first_day"], "sort_order": 8},
            {"line_number": "7", "description": "Increases for the tax year (see instructions)",
             "line_type": "input", "source_facts": ["increases_tax_year"], "sort_order": 9},
            {"line_number": "8", "description": "Add lines 6 and 7",
             "line_type": "subtotal", "calculation": "line 6 + line 7", "source_rules": ["R002"], "sort_order": 10},
            {"line_number": "9", "description": "Decreases for the tax year (see instructions)",
             "line_type": "input", "source_facts": ["decreases_tax_year"], "sort_order": 11},
            {"line_number": "10a", "description": "Subtract line 9 from line 8",
             "line_type": "calculated", "calculation": "line 8 - line 9", "source_rules": ["R002"], "sort_order": 12},
            {"line_number": "10b", "description": "If line 10a is more than zero, enter that amount here and go to line 20 (or complete Part III). Otherwise, enter -0- and see Pub. 925 for information on the recapture rules",
             "line_type": "calculated", "calculation": "max(0, line 10a)", "source_rules": ["R002", "R007"], "sort_order": 13},
            # ── Part III — Detailed Computation of Amount at Risk ──
            {"line_number": "11", "description": "Investment in the activity (or in your interest in the activity) at the effective date. Do not enter less than zero",
             "line_type": "input", "source_facts": ["investment_at_effective_date"], "sort_order": 14,
             "notes": "Skip 11-14 if Part III was completed for the prior year (i6198 Part III intro); the published Line 11 Worksheet feeds this line for non-partner/shareholder filers."},
            {"line_number": "12", "description": "Increases at effective date",
             "line_type": "input", "source_facts": ["increases_at_effective_date"], "sort_order": 15},
            {"line_number": "13", "description": "Add lines 11 and 12",
             "line_type": "subtotal", "calculation": "line 11 + line 12", "source_rules": ["R003"], "sort_order": 16},
            {"line_number": "14", "description": "Decreases at effective date",
             "line_type": "input", "source_facts": ["decreases_at_effective_date"], "sort_order": 17},
            {"line_number": "15", "description": "Amount at risk (check box that applies): a — At effective date (subtract line 14 from line 13; do not enter less than zero); b — From your prior year Form 6198, line 19b (do NOT enter the amount from line 10b of your prior year form)",
             "line_type": "calculated", "calculation": "box a: max(0, line 13 - line 14); box b: prior year line 19b",
             "source_facts": ["line15_basis", "prior_year_line19b"], "source_rules": ["R003"], "sort_order": 18},
            {"line_number": "16", "description": "Increases since (check box that applies): a — Effective date; b — The end of your prior year",
             "line_type": "input", "source_facts": ["increases_since", "since_when_16"], "sort_order": 19},
            {"line_number": "17", "description": "Add lines 15 and 16",
             "line_type": "subtotal", "calculation": "line 15 + line 16", "source_rules": ["R003"], "sort_order": 20},
            {"line_number": "18", "description": "Decreases since (check box that applies): a — Effective date; b — The end of your prior year",
             "line_type": "input", "source_facts": ["decreases_since", "since_when_18"], "sort_order": 21},
            {"line_number": "19a", "description": "Subtract line 18 from line 17",
             "line_type": "calculated", "calculation": "line 17 - line 18", "source_rules": ["R003"], "sort_order": 22},
            {"line_number": "19b", "description": "If line 19a is more than zero, enter that amount here and go to line 20. Otherwise, enter -0- and see Pub. 925 for information on the recapture rules",
             "line_type": "calculated", "calculation": "max(0, line 19a)", "source_rules": ["R003", "R007"], "sort_order": 23},
            # ── Part IV — Deductible Loss ──
            {"line_number": "20", "description": "Amount at risk. Enter the larger of line 10b or line 19b",
             "line_type": "calculated", "calculation": "max(line 10b, line 19b)", "source_rules": ["R004"], "sort_order": 24},
            {"line_number": "21", "description": "Deductible loss. Enter the smaller of the line 5 loss (treated as a positive number) or line 20. See the instructions to find out how to report any deductible loss and any carryover (parenthesized loss entry)",
             "line_type": "total", "calculation": "-min(abs(line 5 loss), line 20)",
             "source_rules": ["R005"], "sort_order": 25,
             "destination_form": "back to the loss source (Sch C/E/F, K-1 forms) per i6198; passive portion routes through Form 8582/8810 (face Note)",
             "notes": "Face Note after line 21: passive-activity losses go to the 8582/8810 instructions to find out if the loss is allowed under the passive rules."},
        ])

        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D001", "title": "Loss exceeds the amount at risk", "severity": "warning",
             "condition": "abs(line_5_loss) > line_20",
             "message": "The line 5 loss exceeds the line 20 amount at risk — line 21 is capped at line 20 and the excess is suspended under §465 and carried to next year (allocated pro rata across the Part I deduction items when more than one)."},
            {"diagnostic_id": "D002", "title": "Qualified nonrecourse financing claimed", "severity": "warning",
             "condition": "qualified_nonrecourse_financing > 0",
             "message": "Nonrecourse financing is being treated as at risk — verify it meets ALL the §465(b)(6)/Reg. 1.465-27 tests: no personal liability, borrowed in connection with holding real property, secured by real property used in the activity, not convertible, and government-loaned/guaranteed or from a qualified person (regular money-lender; not related, not the seller, not fee-interested)."},
            {"diagnostic_id": "D003", "title": "Amount at risk is zero — possible §465(e) recapture", "severity": "warning",
             "condition": "line_10b == 0 or line_19b == 0",
             "message": "Line 10b/19b is -0- — the face routes to Pub. 925: if the amount at risk fell below zero at the close of the year, prior losses may be recaptured as income (§465(e)). Recapture can apply even in a line 5 profit year."},
            {"diagnostic_id": "D004", "title": "Line 15 box b — verify prior year 19b (not 10b)", "severity": "warning",
             "condition": "line15_basis == 'prior_year_19b'",
             "message": "Line 15 box b is checked — the amount must come from the PRIOR year Form 6198 line 19b. Face + i6198 caution: 'Do not enter the amount from line 10b of your prior year form.' Also exclude any amounts not at risk."},
            {"diagnostic_id": "D005", "title": "Part II smaller than the loss — Part III may allow more", "severity": "warning",
             "condition": "line_10b < abs(line_5_loss) and part_iii_not_completed",
             "message": "The simplified (Part II) amount at risk is smaller than the line 5 loss — i6198 Line 10b: 'you may want to complete Part III to see if Part III gives you a larger amount at risk.'"},
            {"diagnostic_id": "D006", "title": "Passive activity — 8582/8810 applies after this form", "severity": "warning",
             "condition": "activity_is_passive and line_21 < 0",
             "message": "The line 21 deductible loss is from a passive activity — it must still pass Form 8582 (or 8810) under §469. Report only the passive-rule-subject part there (face Note after line 21). The FORM_8582 spec's R-8582-ATRISK-ORDER documents the §465-before-§469 ordering."},
        ])

        self._upsert_tests(form, [
            # Published pins — i6198 (Rev. 11-2025) Line 21 Examples, p.8 verbatim.
            {"scenario_name": "L21 example (a) — loss within the amount at risk", "scenario_type": "normal",
             "inputs": {"line_5": -400, "line_20": 1000},
             "expected_outputs": {"line_21": -400},
             "sort_order": 1,
             "notes": "i6198 Line 21 Examples (a) verbatim: 'If line 5 is a loss of $400 and line 20 is $1,000, enter ($400) on line 21.'"},
            {"scenario_name": "L21 example (b) — loss capped at line 20", "scenario_type": "normal",
             "inputs": {"line_5": -1600, "line_20": 1200},
             "expected_outputs": {"line_21": -1200, "suspended_465_carryover": 400},
             "sort_order": 2,
             "notes": "i6198 Line 21 Examples (b) verbatim: 'If line 5 is a loss of $1,600 and line 20 is $1,200, enter ($1,200) on line 21.' The $400 excess is suspended under §465."},
            {"scenario_name": "L21 example (c) — zero at risk", "scenario_type": "edge",
             "inputs": {"line_5": -800, "line_20": 0},
             "expected_outputs": {"line_21": 0, "suspended_465_carryover": 800},
             "sort_order": 3,
             "notes": "i6198 Line 21 Examples (c) verbatim: 'If line 5 is a loss of $800 and line 20 is zero, enter -0- on line 21.' D003 fires (possible recapture)."},
            {"scenario_name": "Line 5 income-offset example (i6198 p.3)", "scenario_type": "normal",
             "inputs": {"ordinary_income_loss": -4600, "gain_loss_sched_d": 3100, "line_20": 600},
             "expected_outputs": {"line_5": -1500, "line_21": -600, "total_loss_allowed": 3700},
             "sort_order": 4,
             "notes": "i6198 Line 5 example verbatim: Schedule C loss $4,600 on line 1, Schedule D gain $3,100 on line 2a -> line 5 loss $1,500. The $3,100 gain is fully reportable and absorbs $3,100 of the loss; Part II/III allows $600 of the $1,500 excess -> total allowed $3,700 ($3,100 + $600)."},
            {"scenario_name": "Part II simplified computation", "scenario_type": "normal",
             "inputs": {"adjusted_basis_first_day": 80000, "increases_tax_year": 5000,
                        "decreases_tax_year": 10000, "line_5": -20000},
             "expected_outputs": {"line_8": 85000, "line_10a": 75000, "line_10b": 75000,
                                  "line_20": 75000, "line_21": -20000},
             "sort_order": 5,
             "notes": "L8 = 80,000 + 5,000; L10a = 85,000 - 10,000 = 75,000 > 0 -> L10b; loss 20,000 within the amount at risk -> fully deductible."},
            {"scenario_name": "Part III detailed + larger-of on line 20", "scenario_type": "normal",
             "inputs": {"investment_at_effective_date": 5000, "increases_at_effective_date": 2000,
                        "decreases_at_effective_date": 1000, "line15_basis": "effective_date",
                        "increases_since": 3000, "decreases_since": 500,
                        "line_10b": 4000, "line_5": -12000},
             "expected_outputs": {"line_13": 7000, "line_15": 6000, "line_17": 9000,
                                  "line_19a": 8500, "line_19b": 8500, "line_20": 8500,
                                  "line_21": -8500, "suspended_465_carryover": 3500},
             "sort_order": 6,
             "notes": "Part III: 13 = 5,000+2,000; 15 box a = 7,000-1,000; 17 = 6,000+3,000; 19a = 9,000-500 = 8,500 -> 19b. L20 = max(4,000, 8,500) = 8,500 — the detailed method allows more than Part II. Loss 12,000 capped at 8,500."},
            {"scenario_name": "Qualified nonrecourse real-estate financing at risk", "scenario_type": "edge",
             "inputs": {"adjusted_basis_first_day": 20000, "increases_tax_year": 180000,
                        "qualified_nonrecourse_financing": 180000, "decreases_tax_year": 0, "line_5": -25000},
             "expected_outputs": {"line_8": 200000, "line_10b": 200000, "line_20": 200000, "line_21": -25000},
             "sort_order": 7,
             "notes": "The kept §465(b)(6) substance re-keyed to the face: $180K qualified nonrecourse financing rides the L7 increases item (3) -> amount at risk $200K; the $25K loss is fully allowed. D002 fires (verify the QNF tests)."},
        ])

        # ── In-loader self-heal (the rename-orphan class, standard since s56/s57):
        # the fabricated pre-face rows must DELETE on reseed, not linger. The 6198
        # TaxForm has a single owner (this loader) — the whitelists are exact.
        _6198_FACTS = {
            "activity_description", "ordinary_income_loss", "gain_loss_sched_d",
            "gain_loss_4797", "gain_loss_other_form", "other_form_label",
            "other_income_gains", "other_deductions_losses", "adjusted_basis_first_day",
            "increases_tax_year", "qualified_nonrecourse_financing", "decreases_tax_year",
            "investment_at_effective_date", "increases_at_effective_date",
            "decreases_at_effective_date", "line15_basis", "prior_year_line19b",
            "increases_since", "since_when_16", "decreases_since", "since_when_18",
        }
        stale_facts = FormFact.objects.filter(tax_form=form).exclude(fact_key__in=_6198_FACTS)
        if stale_facts.exists():
            self.stdout.write(f"  deleting {stale_facts.count()} stale Form 6198 facts: "
                              + ", ".join(sorted(stale_facts.values_list("fact_key", flat=True))))
            stale_facts.delete()

        _6198_LINES = {
            "1", "2a", "2b", "2c", "3", "4", "5", "6", "7", "8", "9", "10a", "10b",
            "11", "12", "13", "14", "15", "16", "17", "18", "19a", "19b", "20", "21",
        }
        stale_lines = FormLine.objects.filter(tax_form=form).exclude(line_number__in=_6198_LINES)
        if stale_lines.exists():
            self.stdout.write(f"  deleting {stale_lines.count()} stale Form 6198 line rows: "
                              + ", ".join(sorted(stale_lines.values_list("line_number", flat=True))))
            stale_lines.delete()

        _6198_RULES = {"R001", "R002", "R003", "R004", "R005", "R006", "R007", "R008", "R009"}
        stale_rules = FormRule.objects.filter(tax_form=form).exclude(rule_id__in=_6198_RULES)
        if stale_rules.exists():
            self.stdout.write(f"  deleting {stale_rules.count()} stale Form 6198 rules: "
                              + ", ".join(sorted(stale_rules.values_list("rule_id", flat=True))))
            stale_rules.delete()

        _6198_DIAGS = {"D001", "D002", "D003", "D004", "D005", "D006"}
        stale_diags = FormDiagnostic.objects.filter(tax_form=form).exclude(diagnostic_id__in=_6198_DIAGS)
        if stale_diags.exists():
            self.stdout.write(f"  deleting {stale_diags.count()} stale Form 6198 diagnostics: "
                              + ", ".join(sorted(stale_diags.values_list("diagnostic_id", flat=True))))
            stale_diags.delete()

        _6198_SCENARIOS = {
            "L21 example (a) — loss within the amount at risk",
            "L21 example (b) — loss capped at line 20",
            "L21 example (c) — zero at risk",
            "Line 5 income-offset example (i6198 p.3)",
            "Part II simplified computation",
            "Part III detailed + larger-of on line 20",
            "Qualified nonrecourse real-estate financing at risk",
        }
        stale_tests = TestScenario.objects.filter(tax_form=form).exclude(scenario_name__in=_6198_SCENARIOS)
        if stale_tests.exists():
            self.stdout.write(f"  deleting {stale_tests.count()} stale Form 6198 scenarios: "
                              + ", ".join(sorted(stale_tests.values_list("scenario_name", flat=True))))
            stale_tests.delete()

        self._upsert_form_links("6198", sources, [
            ("IRS_2025_6198_INSTR", "governs"),
            ("IRC_465", "governs"),
        ])
        self.stdout.write(self.style.SUCCESS("  Form 6198 complete."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Form 3800 — General Business Credit
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_3800(self, sources):
        form = self._upsert_form(
            "3800", "Form 3800 — General Business Credit",
            ["1120S", "1065", "1120", "1040"],
            notes="Aggregates business credits. S-Corp passes credits through to shareholders via K-1 Box 13.",
        )
        self._upsert_facts(form, [
            {"fact_key": "research_credit_41", "label": "Research credit (IRC 41)", "data_type": "decimal", "sort_order": 1},
            {"fact_key": "work_opportunity_credit_51", "label": "Work opportunity credit (IRC 51)", "data_type": "decimal", "sort_order": 2},
            {"fact_key": "small_employer_health_45r", "label": "Small employer health insurance credit (IRC 45R)", "data_type": "decimal", "sort_order": 3},
            {"fact_key": "disabled_access_credit_44", "label": "Disabled access credit (IRC 44)", "data_type": "decimal", "sort_order": 4},
            {"fact_key": "other_business_credits", "label": "Other general business credits", "data_type": "decimal", "sort_order": 5},
            {"fact_key": "total_current_year_credits", "label": "Total current year general business credits", "data_type": "decimal", "sort_order": 6},
            {"fact_key": "carryforward_credits", "label": "Credit carryforward from prior years", "data_type": "decimal", "sort_order": 7},
            {"fact_key": "carryback_credits", "label": "Credit carryback from future years", "data_type": "decimal", "sort_order": 8},
            {"fact_key": "total_credits_available", "label": "Total credits available", "data_type": "decimal", "sort_order": 9},
            {"fact_key": "k1_box13_credits", "label": "Credits flowing to K-1 Box 13 (S-Corp/partnership)", "data_type": "decimal", "sort_order": 10},
            {"fact_key": "net_income_tax", "label": "Net income tax (for credit limitation)", "data_type": "decimal", "sort_order": 11},
            {"fact_key": "tentative_minimum_tax", "label": "Tentative minimum tax", "data_type": "decimal", "sort_order": 12},
        ])

        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "S-Corp passes credits through to shareholders", "rule_type": "routing",
             "formula": "k1_box13_credits = total_current_year_credits (S-Corp does not take credits at entity level)",
             "inputs": ["total_current_year_credits"], "outputs": ["k1_box13_credits"],
             "precedence": 1, "sort_order": 1,
             "description": "S corporations pass business credits through to shareholders on K-1 Box 13 by credit type code. No entity-level credit taken."},
            {"rule_id": "R002", "title": "Carryback 1 year, carryforward 20 years", "rule_type": "validation",
             "formula": "unused credits carryback 1 year, carryforward 20 years",
             "inputs": ["carryforward_credits", "carryback_credits"], "outputs": [],
             "precedence": 0, "sort_order": 2,
             "description": "IRC 39: Unused general business credits carry back 1 year and forward 20 years."},
            {"rule_id": "R003", "title": "Credits reported on K-1 Box 13 by type code", "rule_type": "routing",
             "formula": "each credit type has specific K-1 Box 13 code (R=research, W=work opportunity, etc.)",
             "inputs": ["research_credit_41", "work_opportunity_credit_51", "small_employer_health_45r",
                        "disabled_access_credit_44", "other_business_credits"],
             "outputs": ["k1_box13_credits"], "precedence": 2, "sort_order": 3,
             "description": "Each credit type flows to K-1 Box 13 with a specific type code for the shareholder to claim."},
            {"rule_id": "R004", "title": "Credit limitation formula", "rule_type": "calculation",
             "formula": "credit_allowed = net_income_tax - max(tentative_minimum_tax, 0.25 * max(0, net_regular_tax - 25000))",
             "inputs": ["net_income_tax", "tentative_minimum_tax"], "outputs": [],
             "precedence": 3, "sort_order": 4,
             "description": "Credit limited to net income tax minus greater of TMT or 25% of net regular tax liability over $25K."},
        ])
        self._upsert_links(rules, sources, [
            ("R001", "IRC_1363", "primary", "S-Corp does not take credits at entity level"),
            ("R001", "IRC_38", "secondary", "Section 38 — general business credit components"),
            ("R002", "IRS_2025_3800_INSTR", "primary", "Carryback/carryforward rules"),
            ("R003", "IRS_2025_3800_INSTR", "primary", "K-1 Box 13 credit type codes"),
            ("R004", "IRC_38", "primary", "Section 38(c) — credit limitation formula"),
            ("R004", "IRS_2025_3800_INSTR", "secondary", "Credit limitation computation instructions"),
        ])
        self._upsert_lines(form, [
            {"line_number": "1a", "description": "General business credits from Part I", "line_type": "input", "sort_order": 1},
            {"line_number": "1b", "description": "Passive activity credits from Part II", "line_type": "input", "sort_order": 2},
            {"line_number": "1c", "description": "Total current year general business credits", "line_type": "subtotal", "sort_order": 3},
            {"line_number": "2", "description": "Carryforward of general business credit from prior year(s)", "line_type": "input", "sort_order": 4},
            {"line_number": "3", "description": "Carryback of general business credit (if applicable)", "line_type": "input", "sort_order": 5},
            {"line_number": "4", "description": "Total general business credits", "line_type": "subtotal", "sort_order": 6},
            {"line_number": "5", "description": "Net income tax", "line_type": "input", "sort_order": 7},
            {"line_number": "6", "description": "Tentative minimum tax", "line_type": "input", "sort_order": 8},
            {"line_number": "7", "description": "Net income tax minus tentative minimum tax", "line_type": "calculated", "sort_order": 9},
            {"line_number": "38", "description": "Allowed general business credit", "line_type": "total",
             "source_rules": ["R004"], "destination_form": "K-1 Box 13", "sort_order": 10},
        ])
        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D001", "title": "Credits not flowing to K-1 Box 13", "severity": "warning",
             "condition": "total_current_year_credits > 0 AND k1_box13_credits == 0",
             "message": "Business credits entered but not flowing to K-1 Box 13 for shareholder pass-through."},
            {"diagnostic_id": "D002", "title": "Credit carryforward not tracked", "severity": "warning",
             "condition": "carryforward_credits > 0 AND no_prior_year_tracking",
             "message": "Credit carryforward from prior year not tracked. Verify carryforward amounts."},
        ])
        self._upsert_tests(form, [
            {"scenario_name": "Single credit pass-through to K-1", "scenario_type": "normal",
             "inputs": {"research_credit_41": 15000, "total_current_year_credits": 15000},
             "expected_outputs": {"k1_box13_credits": 15000},
             "sort_order": 1,
             "notes": "$15K R&D credit passes through to shareholders on K-1 Box 13 Code R."},
            {"scenario_name": "Multiple credits", "scenario_type": "normal",
             "inputs": {"research_credit_41": 10000, "work_opportunity_credit_51": 5000,
                        "disabled_access_credit_44": 2500, "total_current_year_credits": 17500},
             "expected_outputs": {"k1_box13_credits": 17500},
             "sort_order": 2,
             "notes": "Three different credits totaling $17.5K all pass through to K-1 Box 13."},
        ])
        self._upsert_form_links("3800", sources, [
            ("IRS_2025_3800_INSTR", "governs"),
            ("IRC_38", "governs"),
        ])
        self.stdout.write(self.style.SUCCESS("  Form 3800 complete."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Schedule M-3 — Net Income Reconciliation for Large Filers
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_m3(self, sources):
        # Renumbered to the REAL face 2026-07-12 (audit-ledger unit #7): the old
        # block's P1-*/P2-*/P3-* line_map was flagged unverifiable (no face in the
        # repo) and proved FABRICATED once the face arrived — Part III ends at 32
        # (the spec had P3-33..36), Part I line 1 is the 1a/1b income-statement
        # questions (the spec called it net income), and the P1-FS/P1-RS/P2-DEP/
        # P3-DEP rows exist on no revision. Rebuilt verbatim vs f1120ss3.pdf
        # (Rev. December 2019 — the CURRENT revision; irs.gov filename trap:
        # f1120sm3.pdf is the Form 1120 C-corp M-3) + i1120ss3 (Rev. 12-2019),
        # both fetched + pymupdf-extracted 2026-07-12. The $10M filing rule
        # (fixed s44) stands; NEW: the $50M complete-ENTIRELY tier the old $50M
        # error had conflated with the filing threshold.
        form = self._upsert_form(
            "1120S_M3", "Schedule M-3 (Form 1120-S) — Net Income (Loss) Reconciliation for S Corporations",
            ["1120S"],
            notes="Face = Rev. December 2019 (f1120ss3.pdf, verified verbatim 2026-07-12; the current "
                  "revision — its instructions are also Rev. 12-2019). FILING: required when SCHEDULE L "
                  "total assets at EOY >= $10 MILLION (i1120ss3 Who Must File + i1120s 2025 p.49, both "
                  "verbatim; the pre-2026-07-09 spec's $50M was a conflation — $50M is the "
                  "complete-ENTIRELY tier, R005). Structure: Part I financial info + net income "
                  "reconciliation (L11 = combine 4-10); Part II income items 1-26 and Part III "
                  "expense/deduction items 1-32, each row in (a) income statement / (b) temporary / "
                  "(c) permanent / (d) tax return columns. Tie chain: P1 L11 = P2 L26(a) (or Schedule "
                  "M-1 L1 under the through-Part-I option); P2 L26(d) = Schedule K line 18 (the same "
                  "K18 anchor as M-1 L8). Filers must check page-1 item C. Lower priority for Ken's "
                  "target market (no tts build leg yet).",
        )
        self._upsert_facts(form, [
            # ── Filing gates ──
            {"fact_key": "total_assets_eoy", "label": "Schedule L total assets at end of tax year (filing gate)", "data_type": "decimal", "required": True, "sort_order": 1,
             "notes": "The $10M filing threshold reads SCHEDULE L total assets (i1120ss3 Who Must File verbatim; published Example 1: $12M consolidated FS assets with $8M Schedule L assets = NOT required). Also drives the $50M complete-entirely tier (R005)."},
            {"fact_key": "voluntary_filing", "label": "Filing voluntarily (Schedule L assets < $10M)?", "data_type": "boolean", "sort_order": 2},
            {"fact_key": "through_part_i_only", "label": "Completing through Part I only (+ Schedule M-1 for Parts II/III)?", "data_type": "boolean", "sort_order": 3,
             "notes": "Allowed only below $50M (required filers) or for voluntary filers (R005). When set, Schedule M-1 line 1 must equal Part I line 11 (D006)."},
            # ── Part I — financial information (face 1a-3b) ──
            {"fact_key": "fs_certified_audited", "label": "L1a — Certified audited non-tax-basis income statement prepared?", "data_type": "boolean", "sort_order": 4,
             "notes": "Yes: skip 1b, complete 2-11 from that statement. No: go to 1b. (Face verbatim.)"},
            {"fact_key": "fs_non_tax_basis", "label": "L1b — Non-tax-basis income statement prepared?", "data_type": "boolean", "sort_order": 5,
             "notes": "Yes: complete 2-11 from that statement. No: skip 2-3b and enter net income (loss) per books and records on line 4a. (Face verbatim.)"},
            {"fact_key": "is_period_beginning", "label": "L2 — Income statement period beginning", "data_type": "date", "sort_order": 6},
            {"fact_key": "is_period_ending", "label": "L2 — Income statement period ending", "data_type": "date", "sort_order": 7},
            {"fact_key": "restated_current_period", "label": "L3a — Income statement restated for the line-2 period?", "data_type": "boolean", "sort_order": 8,
             "notes": "Yes requires an attached explanation with the amount of each item restated."},
            {"fact_key": "restated_preceding_periods", "label": "L3b — Restated for any of the five preceding periods?", "data_type": "boolean", "sort_order": 9,
             "notes": "Yes requires an attached explanation with the amount of each item restated."},
            # ── Part I — reconciliation amounts (face 4a-10) ──
            {"fact_key": "ww_consolidated_net_income", "label": "L4a — Worldwide consolidated net income (loss) per the line-1 income statement source", "data_type": "decimal", "sort_order": 10},
            {"fact_key": "accounting_standard", "label": "L4b — Accounting standard used for line 4a", "data_type": "choice",
             "choices": ["gaap", "ifrs", "tax_basis", "other"], "sort_order": 11,
             "notes": "Face checkboxes (1) GAAP (2) IFRS (3) Tax-basis (4) Other (specify)."},
            {"fact_key": "accounting_standard_other", "label": "L4b(4) — Other accounting standard (specify)", "data_type": "string", "sort_order": 12},
            {"fact_key": "nonincl_foreign_income", "label": "L5a — Net income from nonincludible foreign entities (parenthesized subtraction)", "data_type": "decimal", "sort_order": 13,
             "notes": "Attach statement. Face prints parentheses — a subtraction in the L11 combine."},
            {"fact_key": "nonincl_foreign_loss", "label": "L5b — Net loss from nonincludible foreign entities (enter as positive)", "data_type": "decimal", "sort_order": 14,
             "notes": "Attach statement; face: 'enter as a positive amount' (an addition in the combine)."},
            {"fact_key": "nonincl_us_income", "label": "L6a — Net income from nonincludible U.S. entities (parenthesized subtraction)", "data_type": "decimal", "sort_order": 15,
             "notes": "Attach statement."},
            {"fact_key": "nonincl_us_loss", "label": "L6b — Net loss from nonincludible U.S. entities (enter as positive)", "data_type": "decimal", "sort_order": 16,
             "notes": "Attach statement."},
            {"fact_key": "dre_foreign_ni", "label": "L7a — Net income (loss) of other foreign disregarded entities", "data_type": "decimal", "sort_order": 17,
             "notes": "Attach statement."},
            {"fact_key": "dre_us_ni", "label": "L7b — Net income (loss) of other U.S. disregarded entities (except QSubs)", "data_type": "decimal", "sort_order": 18,
             "notes": "Attach statement."},
            {"fact_key": "qsub_ni", "label": "L7c — Net income (loss) of other qualified subchapter S subsidiaries (QSubs)", "data_type": "decimal", "sort_order": 19,
             "notes": "Attach statement."},
            {"fact_key": "eliminations_adjustment", "label": "L8 — Adjustment to eliminations between includible and nonincludible entities", "data_type": "decimal", "sort_order": 20,
             "notes": "Attach statement."},
            {"fact_key": "period_adjustment", "label": "L9 — Adjustment to reconcile income statement period to tax year", "data_type": "decimal", "sort_order": 21,
             "notes": "Attach statement."},
            {"fact_key": "other_adjustments", "label": "L10 — Other adjustments to reconcile to line 11", "data_type": "decimal", "sort_order": 22,
             "notes": "Attach statement."},
            # ── Part I line 12 — entity asset/liability totals ──
            {"fact_key": "l12a_assets", "label": "L12a — Total assets of entities included on Part I line 4", "data_type": "decimal", "sort_order": 23,
             "notes": "Line 12 header (face): 'Enter the total amount (not just the corporation's share) of the assets and liabilities of all entities included or removed on the following lines.'"},
            {"fact_key": "l12a_liabilities", "label": "L12a — Total liabilities of entities included on Part I line 4", "data_type": "decimal", "sort_order": 24},
            {"fact_key": "l12b_assets", "label": "L12b — Total assets removed on Part I line 5", "data_type": "decimal", "sort_order": 25},
            {"fact_key": "l12b_liabilities", "label": "L12b — Total liabilities removed on Part I line 5", "data_type": "decimal", "sort_order": 26},
            {"fact_key": "l12c_assets", "label": "L12c — Total assets removed on Part I line 6", "data_type": "decimal", "sort_order": 27},
            {"fact_key": "l12c_liabilities", "label": "L12c — Total liabilities removed on Part I line 6", "data_type": "decimal", "sort_order": 28},
            {"fact_key": "l12d_assets", "label": "L12d — Total assets included on Part I line 7", "data_type": "decimal", "sort_order": 29},
            {"fact_key": "l12d_liabilities", "label": "L12d — Total liabilities included on Part I line 7", "data_type": "decimal", "sort_order": 30},
        ])

        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "Required if Schedule L total assets >= $10M", "rule_type": "conditional",
             "formula": "if total_assets_eoy >= 10000000 then must_file_m3 = True  # total_assets_eoy = SCHEDULE L EOY total assets",
             "inputs": ["total_assets_eoy"], "outputs": ["must_file_m3"], "precedence": 1, "sort_order": 1,
             "description": "Schedule M-3 is required instead of Schedule M-1 when SCHEDULE L total assets "
                            "at the end of the tax year equal or exceed $10 MILLION (i1120ss3 Who Must File "
                            "+ i1120s 2025 p.49, both verbatim; corrected 2026-07-09 from the prior spec's "
                            "erroneous $50M — that figure is the complete-ENTIRELY tier, R005). The gate "
                            "reads Schedule L, not financial-statement assets (published Example 1: $12M "
                            "consolidated FS / $8M Schedule L = not required; may file voluntarily). Any "
                            "filer (required or voluntary) checks page-1 item C (see the item C excerpt)."},
            {"rule_id": "R002", "title": "Part I — L11 net income per income statement = combine 4 through 10", "rule_type": "calculation",
             "formula": "line_11 = ww_consolidated_net_income - nonincl_foreign_income + nonincl_foreign_loss - nonincl_us_income + nonincl_us_loss + dre_foreign_ni + dre_us_ni + qsub_ni + eliminations_adjustment + period_adjustment + other_adjustments  # 5a/6a are parenthesized (entered positive, subtracted); 5b/6b entered positive and added",
             "inputs": ["ww_consolidated_net_income", "nonincl_foreign_income", "nonincl_foreign_loss",
                        "nonincl_us_income", "nonincl_us_loss", "dre_foreign_ni", "dre_us_ni", "qsub_ni",
                        "eliminations_adjustment", "period_adjustment", "other_adjustments"],
             "outputs": ["p1_net_income_per_statement"], "precedence": 2, "sort_order": 2,
             "description": "Face L11 verbatim: 'Net income (loss) per income statement of the corporation. "
                            "Combine lines 4 through 10.' Entry routing (face 1a/1b): certified audited "
                            "non-tax-basis statement -> use it; else other non-tax-basis statement -> use "
                            "it; else skip 2-3b and enter net income (loss) per BOOKS AND RECORDS on 4a. "
                            "Face note: 'Part I, line 11, must equal Part II, line 26, column (a); or "
                            "Schedule M-1, line 1.'"},
            {"rule_id": "R003", "title": "Part II — row columns (d)=(a)+(b)+(c); L23 = combine 1-22; L26 = combine 23-25; the L26 ties", "rule_type": "calculation",
             "formula": "per row: col_d = col_a + col_b + col_c; line_23 = combine(lines 1-22); line_26 = combine(lines 23-25); line_26(a) == part_i_line_11; line_26(d) == schedule_k_line_18",
             "inputs": [], "outputs": ["p2_reconciliation_totals"], "precedence": 3, "sort_order": 3,
             "description": "Part II rows 1-22 (incl. the 21a-21g disposition split) each carry (a) income "
                            "(loss) per income statement / (b) temporary difference / (c) permanent "
                            "difference / (d) income (loss) per tax return. L23 verbatim: 'Total income "
                            "(loss) items. Combine lines 1 through 22.' L24 = total expense/deduction items "
                            "FROM Part III line 32 (sign-flipped, R004). L25 = other items with no "
                            "differences. L26 verbatim: 'Reconciliation totals. Combine lines 23 through "
                            "25' with the face note: 'Line 26, column (a), must equal Part I, line 11, and "
                            "column (d) must equal Form 1120-S, Schedule K, line 18' — the same K18 anchor "
                            "as Schedule M-1 line 8."},
            {"rule_id": "R004", "title": "Part III — L32 = combine 1-31, carried to Part II L24 SIGN-FLIPPED", "rule_type": "calculation",
             "formula": "per row: col_d = col_a + col_b + col_c; line_32 = combine(lines 1-31); part_ii_line_24 = -line_32  # face: 'reporting positive amounts as negative and negative amounts as positive'",
             "inputs": [], "outputs": ["p3_total_expense_items"], "precedence": 3, "sort_order": 4,
             "description": "Part III rows 1-31 (incl. 23a/23b depletion; line 22 Reserved) in the same "
                            "four columns ((a) expense per income statement / (d) deduction per tax "
                            "return). L32 verbatim: 'Total expense/deduction items. Combine lines 1 "
                            "through 31. Enter here and on Part II, line 24, reporting positive amounts "
                            "as negative and negative amounts as positive.'"},
            {"rule_id": "R005", "title": "Completion tiers — $50M entirely; below: entirely OR through Part I + M-1", "rule_type": "conditional",
             "formula": "if must_file_m3 and total_assets_eoy >= 50000000 then complete_entirely = REQUIRED; elif must_file_m3 or voluntary_filing then complete_entirely OR (through_part_i_only and schedule_m1_line_1 == part_i_line_11)",
             "inputs": ["total_assets_eoy", "voluntary_filing", "through_part_i_only"],
             "outputs": ["m3_completion_tier"], "precedence": 2, "sort_order": 5,
             "description": "i1120ss3 Completing Schedule M-3 verbatim: at least $50 million total assets "
                            "at the end of the tax year must complete Schedule M-3 ENTIRELY; a required "
                            "filer under $50M, or a voluntary filer, must either complete it entirely or "
                            "complete it through Part I and file Schedule M-1 instead of Parts II/III — in "
                            "which case 'line 1 of Form 1120-S, Schedule M-1 must equal line 11 of Part I "
                            "of Schedule M-3.' (The published text's clause (i) says '(Form 1065)' — the "
                            "IRS's own typo; context makes it (Form 1120-S).) This $50M tier is what the "
                            "pre-2026-07-09 spec had conflated with the $10M FILING threshold. For any "
                            "part completed, all columns must be completed and all applicable questions "
                            "answered."},
        ])

        # Refresh authority-link notes (get_or_create keeps stale relevance notes —
        # the s59 renumber-unit rule).
        RuleAuthorityLink.objects.filter(form_rule__tax_form=form).delete()
        self._upsert_links(rules, sources, [
            ("R001", "IRS_2025_1120S_M3_INSTR", "primary", "Who Must File — $10M SCHEDULE L total assets (i1120ss3 verbatim + i1120s 2025 p.49)"),
            ("R001", "IRS_2025_1120S_SCHB_INSTR", "secondary", "Schedule B references the M-3 threshold"),
            ("R002", "IRS_2025_1120S_M3_INSTR", "primary", "Part I face 1a-11 — the L11 combine + the 1a/1b entry routing"),
            ("R003", "IRS_2025_1120S_M3_INSTR", "primary", "Part II face 1-26 — the four columns + the L26(a)/L26(d) tie notes"),
            ("R004", "IRS_2025_1120S_M3_INSTR", "primary", "Part III face 1-32 — the L32 sign-flip carry to Part II L24"),
            ("R005", "IRS_2025_1120S_M3_INSTR", "primary", "Completing Schedule M-3 — the $50M entirely / through-Part-I tiers (verbatim)"),
        ])
        _P2_COLS = ("Columns: (a) income (loss) per income statement / (b) temporary difference / "
                    "(c) permanent difference / (d) income (loss) per tax return.")
        _P3_COLS = ("Columns: (a) expense per income statement / (b) temporary difference / "
                    "(c) permanent difference / (d) deduction per tax return.")
        self._upsert_lines(form, [
            # ── Part I — Financial Information and Net Income (Loss) Reconciliation ──
            {"line_number": "I-1a", "description": "Did the corporation prepare a certified audited non-tax-basis income statement for the period ending with or within this tax year? Yes: skip 1b, complete 2-11 from that statement. No: go to 1b",
             "line_type": "input", "source_facts": ["fs_certified_audited"], "sort_order": 1},
            {"line_number": "I-1b", "description": "Did the corporation prepare a non-tax-basis income statement for that period? Yes: complete 2-11 from it. No: skip 2-3b and enter net income (loss) per books and records on line 4a",
             "line_type": "input", "source_facts": ["fs_non_tax_basis"], "sort_order": 2},
            {"line_number": "I-2", "description": "Enter the income statement period: Beginning / Ending",
             "line_type": "input", "source_facts": ["is_period_beginning", "is_period_ending"], "sort_order": 3},
            {"line_number": "I-3a", "description": "Has the corporation's income statement been restated for the income statement period on line 2? (Yes: attach explanation + amount of each item restated)",
             "line_type": "input", "source_facts": ["restated_current_period"], "sort_order": 4},
            {"line_number": "I-3b", "description": "Has the income statement been restated for any of the five preceding periods? (Yes: attach explanation + amounts)",
             "line_type": "input", "source_facts": ["restated_preceding_periods"], "sort_order": 5},
            {"line_number": "I-4a", "description": "Worldwide consolidated net income (loss) from income statement source identified in Part I, line 1",
             "line_type": "input", "source_facts": ["ww_consolidated_net_income"], "sort_order": 6},
            {"line_number": "I-4b", "description": "Indicate accounting standard used for line 4a: (1) GAAP (2) IFRS (3) Tax-basis (4) Other (specify)",
             "line_type": "input", "source_facts": ["accounting_standard", "accounting_standard_other"], "sort_order": 7},
            {"line_number": "I-5a", "description": "Net income from nonincludible foreign entities (attach statement) — parenthesized subtraction",
             "line_type": "input", "source_facts": ["nonincl_foreign_income"], "sort_order": 8},
            {"line_number": "I-5b", "description": "Net loss from nonincludible foreign entities (attach statement and enter as a positive amount)",
             "line_type": "input", "source_facts": ["nonincl_foreign_loss"], "sort_order": 9},
            {"line_number": "I-6a", "description": "Net income from nonincludible U.S. entities (attach statement) — parenthesized subtraction",
             "line_type": "input", "source_facts": ["nonincl_us_income"], "sort_order": 10},
            {"line_number": "I-6b", "description": "Net loss from nonincludible U.S. entities (attach statement and enter as a positive amount)",
             "line_type": "input", "source_facts": ["nonincl_us_loss"], "sort_order": 11},
            {"line_number": "I-7a", "description": "Net income (loss) of other foreign disregarded entities (attach statement)",
             "line_type": "input", "source_facts": ["dre_foreign_ni"], "sort_order": 12},
            {"line_number": "I-7b", "description": "Net income (loss) of other U.S. disregarded entities (except qualified subchapter S subsidiaries) (attach statement)",
             "line_type": "input", "source_facts": ["dre_us_ni"], "sort_order": 13},
            {"line_number": "I-7c", "description": "Net income (loss) of other qualified subchapter S subsidiaries (QSubs) (attach statement)",
             "line_type": "input", "source_facts": ["qsub_ni"], "sort_order": 14},
            {"line_number": "I-8", "description": "Adjustment to eliminations of transactions between includible entities and nonincludible entities (attach statement)",
             "line_type": "input", "source_facts": ["eliminations_adjustment"], "sort_order": 15},
            {"line_number": "I-9", "description": "Adjustment to reconcile income statement period to tax year (attach statement)",
             "line_type": "input", "source_facts": ["period_adjustment"], "sort_order": 16},
            {"line_number": "I-10", "description": "Other adjustments to reconcile to amount on line 11 (attach statement)",
             "line_type": "input", "source_facts": ["other_adjustments"], "sort_order": 17},
            {"line_number": "I-11", "description": "Net income (loss) per income statement of the corporation. Combine lines 4 through 10. Note: Part I, line 11, must equal Part II, line 26, column (a); or Schedule M-1, line 1",
             "line_type": "total", "calculation": "combine lines 4 through 10", "source_rules": ["R002"], "sort_order": 18},
            {"line_number": "I-12a", "description": "Total assets / total liabilities of all entities included on Part I, line 4 (total amount, not just the corporation's share)",
             "line_type": "input", "source_facts": ["l12a_assets", "l12a_liabilities"], "sort_order": 19},
            {"line_number": "I-12b", "description": "Total assets / total liabilities removed on Part I, line 5",
             "line_type": "input", "source_facts": ["l12b_assets", "l12b_liabilities"], "sort_order": 20},
            {"line_number": "I-12c", "description": "Total assets / total liabilities removed on Part I, line 6",
             "line_type": "input", "source_facts": ["l12c_assets", "l12c_liabilities"], "sort_order": 21},
            {"line_number": "I-12d", "description": "Total assets / total liabilities included on Part I, line 7",
             "line_type": "input", "source_facts": ["l12d_assets", "l12d_liabilities"], "sort_order": 22},
            # ── Part II — Income (Loss) Items (four columns per row; attach
            #    statements for lines 1 through 10) ──
            {"line_number": "II-1", "description": "Income (loss) from equity method foreign corporations. " + _P2_COLS, "line_type": "input", "sort_order": 30},
            {"line_number": "II-2", "description": "Gross foreign dividends not previously taxed", "line_type": "input", "sort_order": 31},
            {"line_number": "II-3", "description": "Subpart F, QEF, and similar income inclusions", "line_type": "input", "sort_order": 32},
            {"line_number": "II-4", "description": "Gross foreign distributions previously taxed", "line_type": "input", "sort_order": 33},
            {"line_number": "II-5", "description": "Income (loss) from equity method U.S. corporations", "line_type": "input", "sort_order": 34},
            {"line_number": "II-6", "description": "U.S. dividends not eliminated in tax consolidation", "line_type": "input", "sort_order": 35},
            {"line_number": "II-7", "description": "Income (loss) from U.S. partnerships", "line_type": "input", "sort_order": 36},
            {"line_number": "II-8", "description": "Income (loss) from foreign partnerships", "line_type": "input", "sort_order": 37},
            {"line_number": "II-9", "description": "Income (loss) from other pass-through entities", "line_type": "input", "sort_order": 38},
            {"line_number": "II-10", "description": "Items relating to reportable transactions", "line_type": "input", "sort_order": 39},
            {"line_number": "II-11", "description": "Interest income (see instructions)", "line_type": "input", "sort_order": 40},
            {"line_number": "II-12", "description": "Total accrual to cash adjustment", "line_type": "input", "sort_order": 41},
            {"line_number": "II-13", "description": "Hedging transactions", "line_type": "input", "sort_order": 42},
            {"line_number": "II-14", "description": "Mark-to-market income (loss)", "line_type": "input", "sort_order": 43},
            {"line_number": "II-15", "description": "Cost of goods sold (see instructions)", "line_type": "input", "sort_order": 44},
            {"line_number": "II-16", "description": "Sale versus lease (for sellers and/or lessors)", "line_type": "input", "sort_order": 45},
            {"line_number": "II-17", "description": "Section 481(a) adjustments", "line_type": "input", "sort_order": 46},
            {"line_number": "II-18", "description": "Unearned/deferred revenue", "line_type": "input", "sort_order": 47},
            {"line_number": "II-19", "description": "Income recognition from long-term contracts", "line_type": "input", "sort_order": 48},
            {"line_number": "II-20", "description": "Original issue discount and other imputed interest", "line_type": "input", "sort_order": 49},
            {"line_number": "II-21a", "description": "Income statement gain/loss on sale, exchange, abandonment, worthlessness, or other disposition of assets other than inventory and pass-through entities", "line_type": "input", "sort_order": 50},
            {"line_number": "II-21b", "description": "Gross capital gains from Schedule D, excluding amounts from pass-through entities", "line_type": "input", "sort_order": 51},
            {"line_number": "II-21c", "description": "Gross capital losses from Schedule D, excluding amounts from pass-through entities, abandonment losses, and worthless stock losses", "line_type": "input", "sort_order": 52},
            {"line_number": "II-21d", "description": "Net gain/loss reported on Form 4797, line 17, excluding amounts from pass-through entities, abandonment losses, and worthless stock losses", "line_type": "input", "sort_order": 53},
            {"line_number": "II-21e", "description": "Abandonment losses", "line_type": "input", "sort_order": 54},
            {"line_number": "II-21f", "description": "Worthless stock losses (attach statement)", "line_type": "input", "sort_order": 55},
            {"line_number": "II-21g", "description": "Other gain/loss on disposition of assets other than inventory", "line_type": "input", "sort_order": 56},
            {"line_number": "II-22", "description": "Other income (loss) items with differences (attach statement)", "line_type": "input", "sort_order": 57},
            {"line_number": "II-23", "description": "Total income (loss) items. Combine lines 1 through 22",
             "line_type": "subtotal", "calculation": "combine lines 1 through 22", "source_rules": ["R003"], "sort_order": 58},
            {"line_number": "II-24", "description": "Total expense/deduction items (from Part III, line 32) — carried sign-flipped",
             "line_type": "calculated", "calculation": "-(Part III line 32)", "source_rules": ["R004"], "sort_order": 59},
            {"line_number": "II-25", "description": "Other items with no differences", "line_type": "input", "sort_order": 60},
            {"line_number": "II-26", "description": "Reconciliation totals. Combine lines 23 through 25. Note: Line 26, column (a), must equal Part I, line 11, and column (d) must equal Form 1120-S, Schedule K, line 18",
             "line_type": "total", "calculation": "combine lines 23 through 25", "source_rules": ["R003"],
             "destination_form": "col (a) ties Part I line 11; col (d) ties Form 1120-S Schedule K line 18 (the M-1 L8 anchor)", "sort_order": 61},
            # ── Part III — Expense/Deduction Items (four columns per row) ──
            {"line_number": "III-1", "description": "U.S. current income tax expense. " + _P3_COLS, "line_type": "input", "sort_order": 70},
            {"line_number": "III-2", "description": "U.S. deferred income tax expense", "line_type": "input", "sort_order": 71},
            {"line_number": "III-3", "description": "State and local current income tax expense", "line_type": "input", "sort_order": 72},
            {"line_number": "III-4", "description": "State and local deferred income tax expense", "line_type": "input", "sort_order": 73},
            {"line_number": "III-5", "description": "Foreign current income tax expense (other than foreign withholding taxes)", "line_type": "input", "sort_order": 74},
            {"line_number": "III-6", "description": "Foreign deferred income tax expense", "line_type": "input", "sort_order": 75},
            {"line_number": "III-7", "description": "Equity-based compensation", "line_type": "input", "sort_order": 76},
            {"line_number": "III-8", "description": "Meals and entertainment", "line_type": "input", "sort_order": 77},
            {"line_number": "III-9", "description": "Fines and penalties", "line_type": "input", "sort_order": 78},
            {"line_number": "III-10", "description": "Judgments, damages, awards, and similar costs", "line_type": "input", "sort_order": 79},
            {"line_number": "III-11", "description": "Pension and profit-sharing", "line_type": "input", "sort_order": 80},
            {"line_number": "III-12", "description": "Other post-retirement benefits", "line_type": "input", "sort_order": 81},
            {"line_number": "III-13", "description": "Deferred compensation", "line_type": "input", "sort_order": 82},
            {"line_number": "III-14", "description": "Charitable contribution of cash and tangible property", "line_type": "input", "sort_order": 83},
            {"line_number": "III-15", "description": "Charitable contribution of intangible property", "line_type": "input", "sort_order": 84},
            {"line_number": "III-16", "description": "Current year acquisition or reorganization investment banking fees", "line_type": "input", "sort_order": 85},
            {"line_number": "III-17", "description": "Current year acquisition or reorganization legal and accounting fees", "line_type": "input", "sort_order": 86},
            {"line_number": "III-18", "description": "Current year acquisition/reorganization other costs", "line_type": "input", "sort_order": 87},
            {"line_number": "III-19", "description": "Amortization/impairment of goodwill", "line_type": "input", "sort_order": 88},
            {"line_number": "III-20", "description": "Amortization of acquisition, reorganization, and start-up costs", "line_type": "input", "sort_order": 89},
            {"line_number": "III-21", "description": "Other amortization or impairment write-offs", "line_type": "input", "sort_order": 90},
            {"line_number": "III-22", "description": "Reserved", "line_type": "informational", "sort_order": 91},
            {"line_number": "III-23a", "description": "Depletion — Oil & Gas", "line_type": "input", "sort_order": 92},
            {"line_number": "III-23b", "description": "Depletion — Other than Oil & Gas", "line_type": "input", "sort_order": 93},
            {"line_number": "III-24", "description": "Depreciation", "line_type": "input", "sort_order": 94},
            {"line_number": "III-25", "description": "Bad debt expense", "line_type": "input", "sort_order": 95},
            {"line_number": "III-26", "description": "Interest expense (see instructions)", "line_type": "input", "sort_order": 96},
            {"line_number": "III-27", "description": "Corporate-owned life insurance premiums", "line_type": "input", "sort_order": 97},
            {"line_number": "III-28", "description": "Purchase versus lease (for purchasers and/or lessees)", "line_type": "input", "sort_order": 98},
            {"line_number": "III-29", "description": "Research and development costs", "line_type": "input", "sort_order": 99},
            {"line_number": "III-30", "description": "Section 118 exclusion (attach statement)", "line_type": "input", "sort_order": 100},
            {"line_number": "III-31", "description": "Other expense/deduction items with differences (attach statement)", "line_type": "input", "sort_order": 101},
            {"line_number": "III-32", "description": "Total expense/deduction items. Combine lines 1 through 31. Enter here and on Part II, line 24, reporting positive amounts as negative and negative amounts as positive",
             "line_type": "total", "calculation": "combine lines 1 through 31; carry to Part II line 24 sign-flipped",
             "source_rules": ["R004"], "destination_form": "Part II line 24 (sign-flipped)", "sort_order": 102},
        ])

        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D001", "title": "M-3 required but M-1 filed", "severity": "error",
             "condition": "total_assets_eoy >= 10000000 AND filing_m1_instead_of_m3",
             "message": "Schedule L total assets >= $10 million but filing Schedule M-1 instead of M-3. Schedule M-3 is required (i1120ss3 Who Must File; i1120s 2025 p.49)."},
            {"diagnostic_id": "D002", "title": "M-3 filed voluntarily", "severity": "info",
             "condition": "total_assets_eoy < 10000000 AND filing_m3",
             "message": "Schedule M-3 filed but Schedule L total assets < $10 million. Voluntary filing is allowed (may complete entirely, or through Part I with Schedule M-1). Check page-1 item C either way."},
            {"diagnostic_id": "D003", "title": ">= $50M — M-3 must be completed ENTIRELY", "severity": "error",
             "condition": "total_assets_eoy >= 50000000 AND through_part_i_only",
             "message": "Total assets are $50 million or more — the through-Part-I option is not available; Schedule M-3 must be completed entirely (i1120ss3 Completing Schedule M-3, verbatim)."},
            {"diagnostic_id": "D004", "title": "Part II line 26(d) must equal Schedule K line 18", "severity": "error",
             "condition": "parts_ii_iii_completed AND p2_line26_col_d != schedule_k_line_18",
             "message": "Part II, line 26, column (d) does not equal Form 1120-S, Schedule K, line 18 (face note, verbatim). The M-3 reconciles to the same K18 anchor as Schedule M-1 line 8."},
            {"diagnostic_id": "D005", "title": "Part I line 11 must equal Part II line 26(a)", "severity": "error",
             "condition": "parts_ii_iii_completed AND p1_line_11 != p2_line26_col_a",
             "message": "Part I, line 11 does not equal Part II, line 26, column (a) (face note, verbatim)."},
            {"diagnostic_id": "D006", "title": "Through-Part-I option — Schedule M-1 line 1 must equal Part I line 11", "severity": "error",
             "condition": "through_part_i_only AND schedule_m1_line_1 != p1_line_11",
             "message": "Completing Schedule M-3 through Part I with Schedule M-1 for the reconciliation: 'line 1 of Form 1120-S, Schedule M-1 must equal line 11 of Part I of Schedule M-3' (i1120ss3, verbatim)."},
            {"diagnostic_id": "D007", "title": "Item C checkbox not checked with an M-3 attached", "severity": "warning",
             "condition": "filing_m3 AND NOT page1_item_c_checked",
             "message": "An M-3 is attached (required or voluntary) but the Form 1120-S page-1 item C box is not checked (i1120ss3 Who Must File, verbatim)."},
        ])

        self._upsert_tests(form, [
            {"scenario_name": "Threshold check — M-3 required", "scenario_type": "normal",
             "inputs": {"total_assets_eoy": 75000000},
             "expected_outputs": {"must_file_m3": True, "complete_entirely_required": True},
             "sort_order": 1,
             "notes": "$75M Schedule L total assets — above the $10M filing threshold AND the $50M tier: M-3 required and must be completed entirely (R001 + R005)."},
            {"scenario_name": "Threshold check — $12M filer (the $10M-$50M band)", "scenario_type": "edge",
             "inputs": {"total_assets_eoy": 12000000},
             "expected_outputs": {"must_file_m3": True, "complete_entirely_required": False},
             "sort_order": 2,
             "notes": "The band the pre-2026-07-09 $50M threshold silently mis-gated: a $12M filer MUST file M-3 (i1120ss3 Who Must File; i1120s 2025 p.49) but may complete it through Part I + Schedule M-1 (R005)."},
            {"scenario_name": "Schedule L reads the gate — published Example 1", "scenario_type": "edge",
             "inputs": {"consolidated_fs_assets": 12000000, "total_assets_eoy": 8000000},
             "expected_outputs": {"must_file_m3": False, "may_file_voluntarily": True},
             "sort_order": 3,
             "notes": "i1120ss3 Example 1 (published): consolidated financial statements report $12M total assets but Schedule L reports $8M — NOT required to file M-3; may file voluntarily (and then either complete entirely or through Part I + M-1)."},
            {"scenario_name": "Part I line 11 combine (4 through 10)", "scenario_type": "normal",
             "inputs": {"ww_consolidated_net_income": 1000000, "nonincl_foreign_income": 200000,
                        "nonincl_us_loss": 50000, "period_adjustment": 10000},
             "expected_outputs": {"line_11": 860000},
             "sort_order": 4,
             "notes": "L11 = 1,000,000 - 200,000 (5a parenthesized) + 50,000 (6b entered positive) + 10,000 (9) = 860,000. Face: 'Combine lines 4 through 10.'"},
            {"scenario_name": "Part III line 32 sign-flip + the line 26 ties", "scenario_type": "normal",
             "inputs": {"p2_line_23_col_d": 900000, "p3_line_32_col_d": 700000, "p2_line_25": 0,
                        "p1_line_11": 150000, "schedule_k_line_18": 200000},
             "expected_outputs": {"p2_line_24_col_d": -700000, "p2_line_26_col_d": 200000},
             "sort_order": 5,
             "notes": "P3 L32 (700,000 of deductions) carries to P2 L24 as -700,000 (face sign-flip verbatim); L26(d) = 900,000 - 700,000 + 0 = 200,000, which must equal Schedule K line 18 (face note). Col (a) of L26 must equal P1 L11."},
        ])

        # ── In-loader self-heal (the rename-orphan class): the fabricated
        # P1-*/P2-*/P3-* map and the generic aggregate facts must DELETE on
        # reseed. 1120S_M3 has a single owner (this loader) — exact whitelists.
        _M3_FACTS = {
            "total_assets_eoy", "voluntary_filing", "through_part_i_only",
            "fs_certified_audited", "fs_non_tax_basis", "is_period_beginning",
            "is_period_ending", "restated_current_period", "restated_preceding_periods",
            "ww_consolidated_net_income", "accounting_standard", "accounting_standard_other",
            "nonincl_foreign_income", "nonincl_foreign_loss", "nonincl_us_income",
            "nonincl_us_loss", "dre_foreign_ni", "dre_us_ni", "qsub_ni",
            "eliminations_adjustment", "period_adjustment", "other_adjustments",
            "l12a_assets", "l12a_liabilities", "l12b_assets", "l12b_liabilities",
            "l12c_assets", "l12c_liabilities", "l12d_assets", "l12d_liabilities",
        }
        stale_facts = FormFact.objects.filter(tax_form=form).exclude(fact_key__in=_M3_FACTS)
        if stale_facts.exists():
            self.stdout.write(f"  deleting {stale_facts.count()} stale M-3 facts: "
                              + ", ".join(sorted(stale_facts.values_list("fact_key", flat=True))))
            stale_facts.delete()

        _M3_LINES = (
            {"I-1a", "I-1b", "I-2", "I-3a", "I-3b", "I-4a", "I-4b", "I-5a", "I-5b",
             "I-6a", "I-6b", "I-7a", "I-7b", "I-7c", "I-8", "I-9", "I-10", "I-11",
             "I-12a", "I-12b", "I-12c", "I-12d"}
            | {f"II-{n}" for n in list(range(1, 21)) + list(range(22, 27))}
            | {f"II-21{c}" for c in "abcdefg"}
            | {f"III-{n}" for n in list(range(1, 23)) + list(range(24, 33))}
            | {"III-23a", "III-23b"}
        )
        stale_lines = FormLine.objects.filter(tax_form=form).exclude(line_number__in=_M3_LINES)
        if stale_lines.exists():
            self.stdout.write(f"  deleting {stale_lines.count()} stale M-3 line rows: "
                              + ", ".join(sorted(stale_lines.values_list("line_number", flat=True))))
            stale_lines.delete()

        _M3_RULES = {"R001", "R002", "R003", "R004", "R005"}
        stale_rules = FormRule.objects.filter(tax_form=form).exclude(rule_id__in=_M3_RULES)
        if stale_rules.exists():
            self.stdout.write(f"  deleting {stale_rules.count()} stale M-3 rules: "
                              + ", ".join(sorted(stale_rules.values_list("rule_id", flat=True))))
            stale_rules.delete()

        _M3_DIAGS = {"D001", "D002", "D003", "D004", "D005", "D006", "D007"}
        stale_diags = FormDiagnostic.objects.filter(tax_form=form).exclude(diagnostic_id__in=_M3_DIAGS)
        if stale_diags.exists():
            self.stdout.write(f"  deleting {stale_diags.count()} stale M-3 diagnostics: "
                              + ", ".join(sorted(stale_diags.values_list("diagnostic_id", flat=True))))
            stale_diags.delete()

        _M3_SCENARIOS = {
            "Threshold check — M-3 required",
            "Threshold check — $12M filer (the $10M-$50M band)",
            "Schedule L reads the gate — published Example 1",
            "Part I line 11 combine (4 through 10)",
            "Part III line 32 sign-flip + the line 26 ties",
        }
        stale_tests = TestScenario.objects.filter(tax_form=form).exclude(scenario_name__in=_M3_SCENARIOS)
        if stale_tests.exists():
            self.stdout.write(f"  deleting {stale_tests.count()} stale M-3 scenarios: "
                              + ", ".join(sorted(stale_tests.values_list("scenario_name", flat=True))))
            stale_tests.delete()

        self._upsert_form_links("1120S_M3", sources, [
            ("IRS_2025_1120S_M3_INSTR", "governs"),
            ("IRS_2025_1120S_INSTR", "informs"),
        ])
        self.stdout.write(self.style.SUCCESS("  Schedule M-3 complete."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Report
    # ═══════════════════════════════════════════════════════════════════════════

    def _report_totals(self):
        def _safe(text):
            return text.encode("ascii", errors="replace").decode("ascii")

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("DATABASE TOTALS (after load_1120s_complete)")
        self.stdout.write("=" * 60)
        self.stdout.write(f"TaxForms:           {TaxForm.objects.count()}")
        self.stdout.write(f"FormFacts:          {FormFact.objects.count()}")
        self.stdout.write(f"FormRules:          {FormRule.objects.count()}")
        self.stdout.write(f"FormLines:          {FormLine.objects.count()}")
        self.stdout.write(f"FormDiagnostics:    {FormDiagnostic.objects.count()}")
        self.stdout.write(f"TestScenarios:      {TestScenario.objects.count()}")
        self.stdout.write(f"AuthoritySources:   {AuthoritySource.objects.count()}")
        self.stdout.write(f"AuthorityExcerpts:  {AuthorityExcerpt.objects.count()}")
        self.stdout.write(f"RuleAuthorityLinks: {RuleAuthorityLink.objects.count()}")
        self.stdout.write(f"AuthorityFormLinks: {AuthorityFormLink.objects.count()}")

        all_rules = FormRule.objects.all()
        uncited = [r for r in all_rules if not r.authority_links.exists()]
        if uncited:
            self.stdout.write(self.style.WARNING(f"\nRules with ZERO authority links: {len(uncited)}"))
            for r in uncited:
                self.stdout.write(_safe(f"  {r.tax_form.form_number} {r.rule_id}: {r.title}"))
        else:
            self.stdout.write(self.style.SUCCESS("\nAll rules have authority links."))

        needs_review = FormRule.objects.filter(notes__icontains="NEEDS REVIEW")
        if needs_review.exists():
            self.stdout.write(f"\nRules marked NEEDS REVIEW: {needs_review.count()}")
            for r in needs_review:
                self.stdout.write(_safe(f"  {r.tax_form.form_number} {r.rule_id}: {r.title}"))

        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("Session 11: 1120-S complete package loaded successfully."))
