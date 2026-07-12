"""Load 1120-S full specs — Page 1, Schedule K (expanded), M-1, M-2, Schedule D flow.

Session 9: Builds on Session 8's Schedule K/K-1/D/8949/4562 specs.
Adds missing forms (Page 1, M-1, M-2), expands K line rules with
proper flow-in sources, adds cross-form diagnostics and test scenarios.

2026-07-12 (renumber unit #5, audit ledger): PAGE1 + M-1 + M-2 rebuilt verbatim
to the 2025 face (f1120s.pdf 2025 + i1120s 2025, both pymupdf-extracted):
- PAGE1: line 19 = Form 7205 energy efficient commercial buildings deduction
  (the NEW row that shifted 19/20/21 -> 20/21/22) + the full Tax and Payments
  block 23a-28e (previously absent).
- M-1: the prior block was FABRICATED — its '3a guaranteed payments (707(c))'
  is a 1065 M-1 line; the real 1120-S face itemizes 3a depreciation / 3b travel
  and entertainment, runs 4 = 1+2+3, 5/5a, 6/6a, 7 = 5+6, and ties line 8 to
  SCHEDULE K LINE 18 (never page-1 OBI).
- M-2: rows 2/4 tie to page 1 LINE 22; columns (b) PTEP and (c) AE&P added;
  R002's AAA distribution cap corrected to the section 1368(e)(1)(C)
  without-net-negative-adjustment base (published p.50-51 example pinned).
Composite/fabricated source "excerpts" replaced with verbatim text; in-loader
stale fact/rule/line/diagnostic/excerpt self-heal added.

Idempotent: uses update_or_create throughout. Safe to re-run.
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
# Authority sources — fresh from IRS.gov fetch 2026-03-18
# ═══════════════════════════════════════════════════════════════════════════

FRESH_SOURCES = [
    {
        "source_code": "IRS_2025_1120S_INSTR_FULL",
        "source_type": "official_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "Instructions for Form 1120-S (2025) — Full Document (fetched 2026-03-18)",
        "citation": "Instructions for Form 1120-S (2025)",
        "issuer": "IRS",
        "current_status": "active",
        "is_substantive_authority": True,
        "requires_human_review": False,
        "trust_score": 9.5,
        "topics": ["1120s", "scorp", "schedule_k", "schedule_m"],
        "excerpts": [
            {
                "excerpt_label": "Page 1 Line 4 — Net gain (loss) from Form 4797",
                "excerpt_text": "Enter the net gain (loss) from Form 4797, Part II, line 17, from the sale or exchange of property used in a trade or business and involuntary conversions. Do not include gain or loss on the disposition of capital assets.",
                "summary_text": "Page 1 Line 4 = Form 4797 Part II Line 17 (ordinary gains/losses from business property).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Page 1 face — Income lines 1a-6 (2025)",
                "location_reference": "f1120s.pdf (2025) page 1, Income section (pymupdf extraction 2026-07-12)",
                "excerpt_text": "Caution: Include only trade or business income and expenses on lines 1a through 22. See the instructions for more information. — 1a Gross receipts or sales · 1b Less returns and allowances · 1c Balance · 2 Cost of goods sold (attach Form 1125-A) · 3 Gross profit. Subtract line 2 from line 1c · 4 Net gain (loss) from Form 4797, Part II, line 17 (attach Form 4797) · 5 Other income (loss) (see instructions—attach statement) · 6 Total income (loss). Add lines 3 through 5",
                "summary_text": "2025 face income rows verbatim. The trade-or-business caution now runs 'lines 1a through 22' (OBI is line 22 on the 2025 face).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Page 1 face — Deductions lines 7-22 (2025)",
                "location_reference": "f1120s.pdf (2025) page 1, Deductions section (pymupdf extraction 2026-07-12)",
                "excerpt_text": "7 Compensation of officers (see instructions—attach Form 1125-E) · 8 Salaries and wages (less employment credits) · 9 Repairs and maintenance · 10 Bad debts · 11 Rents · 12 Taxes and licenses · 13 Interest (see instructions) · 14 Depreciation from Form 4562 not claimed on Form 1125-A or elsewhere on return (attach Form 4562) · 15 Depletion (do not deduct oil and gas depletion) · 16 Advertising · 17 Pension, profit-sharing, etc., plans · 18 Employee benefit programs · 19 Energy efficient commercial buildings deduction (attach Form 7205) · 20 Other deductions (attach statement) · 21 Total deductions. Add lines 7 through 20 · 22 Ordinary business income (loss). Subtract line 21 from line 6",
                "summary_text": "2025 face deduction rows verbatim: 19 = Form 7205 deduction (NEW row), 20 = other deductions, 21 = total (add 7-20), 22 = OBI (line 6 minus line 21). Section 179 never appears — separately stated on Schedule K line 11.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Page 1 face — Tax and Payments lines 23a-28e (2025)",
                "location_reference": "f1120s.pdf (2025) page 1, Tax and Payments section (pymupdf extraction 2026-07-12)",
                "excerpt_text": "23a Excess net passive income or LIFO recapture tax (see instructions) · 23b Tax from Schedule D (Form 1120-S) · 23c Add lines 23a and 23b (see instructions for additional taxes) · 24a Current year's estimated tax payments and preceding year's overpayment credited to the current year · 24b Tax deposited with Form 7004 · 24c Credit for federal tax paid on fuels (attach Form 4136) · 24d Elective payment election amount from Form 3800 · 24z Add lines 24a through 24d · 25 Estimated tax penalty (see instructions). Check if Form 2220 is attached · 26 Amount owed. If line 24z is smaller than the total of lines 23c and 25, enter amount owed · 27 Overpayment. If line 24z is larger than the total of lines 23c and 25, enter amount overpaid · 28 Enter amount from line 27: a Credited to 2026 estimated tax · b Refunded · c Routing number · d Type: Checking / Savings · e Account number",
                "summary_text": "2025 face tax-and-payments rows verbatim: 23a-c taxes, 24a-d/z payments, 25 penalty (2220 checkbox), 26 owed vs 27 overpaid (both compare 24z to 23c+25), 28a credited / 28b refunded + direct-deposit fields 28c/d/e.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Line 19 instruction — Energy Efficient Commercial Buildings Deduction (2025)",
                "location_reference": "i1120s (2025) p.19, Line 19",
                "excerpt_text": "Line 19. Energy Efficient Commercial Buildings Deduction. Complete and attach Form 7205 if claiming the energy efficient commercial building deduction. See the Instructions for Form 7205 for more information. Also, see section 179D.",
                "summary_text": "Page 1 line 19 = the section 179D energy efficient commercial buildings deduction; Form 7205 must be attached.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Line 20 instruction — Other Deductions (2025)",
                "location_reference": "i1120s (2025) p.19, Line 20",
                "excerpt_text": "Line 20. Other Deductions. Enter the total allowable trade or business deductions that aren't deductible elsewhere on Form 1120-S, page 1. Attach a statement listing by type and amount each deduction included on this line.",
                "summary_text": "Other deductions is line 20 on the 2025 face (was line 19 pre-Form-7205); statement required.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Line 20 Special Rules — Travel, meals, and entertainment (2025)",
                "location_reference": "i1120s (2025) p.20, Line 20 Special Rules (fetched 2026-07-09)",
                "excerpt_text": (
                    "Subject to limitations and restrictions discussed below, a corporation can deduct "
                    "ordinary and necessary travel and meal expenses paid or incurred in its trade or "
                    "business. Generally, entertainment expenses, membership dues, and facilities used in "
                    "connection with these activities can't be deducted. ... Meals. Generally, the "
                    "corporation can deduct only 50% of the amount otherwise allowable for meal expenses "
                    "paid or incurred in its trade or business. In addition (subject to exceptions under "
                    "section 274(k)(2)): Meals must not be lavish or extravagant, and an employee of the "
                    "corporation must be present at the meal. See section 274(n)(3) for a special rule "
                    "that applies to expenses for meals consumed by individuals subject to the hours of "
                    "service limits of the Department of Transportation. ... Amounts treated as "
                    "compensation. The corporation may be able to deduct otherwise nondeductible "
                    "entertainment, amusement, or recreation expenses if the amounts are treated as "
                    "compensation to the recipient and reported on Form W-2 for an employee or on Form "
                    "1099-NEC for an independent contractor."
                ),
                "summary_text": "Meals: 50% general (§274(n)(1), §274(k) not-lavish/employee-present). DOT hours-of-service special rule = §274(n)(3) (80% per Pub 463). Entertainment: nondeductible (§274(a)). Compensation-treated amounts: deductible.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Line 22 instruction — Ordinary Business Income (Loss) (2025)",
                "location_reference": "i1120s (2025) p.21, Line 22",
                "excerpt_text": "Line 22. Ordinary Business Income (Loss). Enter this income or loss on Schedule K, line 1. Line 22 income is not used in figuring the excess net passive income or built-in gains taxes. See the instructions for line 23a for figuring taxable income for purposes of these taxes.",
                "summary_text": "OBI is line 22 on the 2025 face; it flows to Schedule K line 1 and is NOT the taxable-income base for the 23a/23b entity-level taxes.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule K Line 9 — Net section 1231 gain (loss)",
                "excerpt_text": "Enter the net section 1231 gain (loss) from Form 4797, Part I, line 7. Section 1231 gains and losses from the sale or exchange of property used in a trade or business held for more than 1 year are reported here, not on Schedule D. This amount flows to each shareholder's K-1, Box 9.",
                "summary_text": "K9 = Form 4797 Part I Line 7. Section 1231 bypasses Schedule D on the 1120-S.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Line 23b/23c instructions — BIG tax + additional taxes (2025)",
                "location_reference": "i1120s (2025) pp.21-22, Lines 23b/23c",
                "excerpt_text": "Line 23b. Tax From Schedule D (Form 1120-S). Enter the built-in gains tax from line 23 of Part III of Schedule D. See the instructions for Part III of Schedule D to determine if the corporation is liable for the tax. — Line 23c. Include the following in the total for line 23c. Form 4255. The corporation is liable for any required investment credit recapture attributable to credits allowed for tax years for which the corporation wasn't an S corporation.",
                "summary_text": "23b = built-in gains tax from Schedule D (1120-S) Part III line 23; 23c = 23a + 23b plus additional taxes (e.g., Form 4255 investment credit recapture from C years).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Line 24d instruction — Elective Payment Election from Form 3800 (2025)",
                "location_reference": "i1120s (2025) p.22, Line 24d",
                "excerpt_text": "Line 24d. Elective Payment Election Amount From Form 3800. Enter the total gross EPE amount from Form 3800, Part III, line 6, column (h). See the Instructions for Form 3800 for more information.",
                "summary_text": "24d = gross elective payment election amount from Form 3800 Part III line 6 column (h).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Lines 25-28a instructions — penalty, owed, overpayment, credited (2025)",
                "location_reference": "i1120s (2025) p.22, Lines 25-28a",
                "excerpt_text": "Line 25. Estimated Tax Penalty. If Form 2220 is attached, check the box on line 25 and enter the amount of any penalty on this line. — Line 26. Amount Owed. Generally, the corporation must pay any tax due in full no later than the due date for filing its tax return (excluding extensions). Payment of the tax due must be made electronically. — Line 27. Overpayment. If there is an overpayment on line 27, enter the amount the corporation wants refunded on line 28b. See Line 28b. Refunded, later. The corporation can also choose to have all or part of the overpayment credited to next year's estimated tax by completing line 28a. — Line 28a. Credited To Estimated Tax. The corporation can elect to apply all or part of the corporation's overpayment to next year's estimated taxes. Enter the amount of any overpayment from line 27 that should be applied to next year's estimated tax.",
                "summary_text": "25 = 2220 penalty (checkbox); 26 = amount owed; 27 = overpayment, split between 28a (credited to next year) and 28b (refunded).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule M-1 face rows (2025)",
                "location_reference": "f1120s.pdf (2025) page 5, Schedule M-1 (pymupdf extraction 2026-07-12)",
                "excerpt_text": "Schedule M-1. Reconciliation of Income (Loss) per Books With Income (Loss) per Return. Note: The corporation may be required to file Schedule M-3. See instructions. — 1 Net income (loss) per books · 2 Income included on Schedule K, lines 1, 2, 3c, 4, 5a, 6, 7, 8a, 9, and 10, not recorded on books this year (itemize) · 3 Expenses recorded on books this year not included on Schedule K, lines 1 through 12e, and 16f (itemize): a Depreciation $ · b Travel and entertainment $ · 4 Add lines 1 through 3 · 5 Income recorded on books this year not included on Schedule K, lines 1 through 10 (itemize): a Tax-exempt interest $ · 6 Deductions included on Schedule K, lines 1 through 12e, and 16f, not charged against book income this year (itemize): a Depreciation $ · 7 Add lines 5 and 6 · 8 Income (loss) (Schedule K, line 18). Subtract line 7 from line 4",
                "summary_text": "2025 M-1 face verbatim: line 3 itemizes 3a depreciation + 3b travel and entertainment (there is NO guaranteed-payments line on the 1120-S M-1 — that is a 1065 line); 4 = 1+2+3; 7 = 5+6; 8 = line 4 minus line 7 and equals Schedule K line 18.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule M-1 applicability — B Q11 / $10M M-3 / 2025 partial option (2025)",
                "location_reference": "i1120s (2025) p.49, Schedule M-1",
                "excerpt_text": "In completing Schedule M-1, the following apply. Schedule M-1 isn't required to be completed if the corporation answered 'Yes' to question 11 on Schedule B. Corporations with total assets of $10 million or more on the last day of the tax year must file Schedule M-3 (Form 1120-S) instead of Schedule M-1. A corporation filing Form 1120-S that isn't required to file Schedule M-3 may voluntarily file Schedule M-3 instead of Schedule M-1. For 2025, corporations that (a) are required to file Schedule M-3 (Form 1120-S) and have less than $50 million total assets at the end of the tax year, or (b) aren't required to file Schedule M-3 (Form 1120-S) and voluntarily file Schedule M-3 (Form 1120-S), must either (i) complete Schedule M-3 (Form 1120-S) entirely, or (ii) complete Schedule M-3 (Form 1120-S) through Part I, and complete Schedule M-1 (Form 1120-S), instead of completing Schedule M-3 (Form 1120-S), Parts II and III. If the corporation chooses to complete Schedule M-1 instead of completing Schedule M-3, Parts II and III, Schedule M-1, line 1, must equal Schedule M-3, Part I, line 11.",
                "summary_text": "M-1 skipped if Sch B Q11 = Yes; $10M+ total assets = M-3 required (the s44-verified threshold); the sub-$50M partial option completes M-3 Part I + M-1 with M-1 L1 = M-3 Part I L11.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule M-1 Line 2 + Line 3b + 16f tip instructions (2025)",
                "location_reference": "i1120s (2025) p.49, Schedule M-1 line instructions",
                "excerpt_text": "Line 2. Report on this line income included on Schedule K, lines 1, 2, 3c, 4, 5a, 6, 7, 8a, 9, and 10 not recorded on the books this year. Describe each such item of income. Attach a statement if necessary. — Line 3b. Travel and Entertainment. Include any of the following applicable expenses. Entertainment expenses not deductible under section 274(a). Meal expenses not deductible under section 274(n). Qualified transportation fringes not deductible under section 274(a)(4). Expenses for the use of an entertainment facility. The part of business gifts over $25. Expenses of an individual over $2,000 that are allocable to conventions on cruise ships. Employee achievement awards of nontangible property or tangible property over $400 ($1,600 if part of a qualified plan). The cost of skyboxes. The part of luxury water travel expenses not deductible under section 274(m). Expenses for travel as a form of education. Nondeductible club dues. Other nondeductible travel and entertainment expenses. — Tip: If the corporation has an amount on Schedule K, line 16f (foreign taxes paid and accrued), take that amount into account for purposes of figuring expenses and deductions to enter on lines 3 and 6.",
                "summary_text": "M-1 3b carries the §274 nondeductible travel/meals/entertainment items (the Page-1 meals worksheet nondeductible portion lands here); K16f foreign taxes factor into lines 3 and 6.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule M-2 face rows and four columns (2025)",
                "location_reference": "f1120s.pdf (2025) page 5, Schedule M-2 (pymupdf extraction 2026-07-12)",
                "excerpt_text": "Schedule M-2. Analysis of Accumulated Adjustments Account, Shareholders' Undistributed Taxable Income Previously Taxed, Accumulated Earnings and Profits, and Other Adjustments Account. Columns: (a) Accumulated adjustments account · (b) Shareholders' undistributed taxable income previously taxed · (c) Accumulated earnings and profits · (d) Other adjustments account. Rows: 1 Balance at beginning of tax year · 2 Ordinary income from page 1, line 22 · 3 Other additions · 4 Loss from page 1, line 22 · 5 Other reductions · 6 Combine lines 1 through 5 · 7 Distributions · 8 Balance at end of tax year. Subtract line 7 from line 6",
                "summary_text": "2025 M-2 face verbatim: FOUR columns (AAA / PTEP / AE&P / OAA); rows 2 and 4 tie to page 1, LINE 22 (the pre-2023 spec text said line 21).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "M-2 Column (a) AAA — year-end adjustment order (2025)",
                "location_reference": "i1120s (2025) p.50, Schedule M-2 Column (a)",
                "excerpt_text": "At the end of the tax year, adjust the AAA for the items as explained below and in the order listed. 1. Increase the AAA by income (other than tax-exempt income) and the excess of the deduction for depletion over the basis of the property subject to depletion. 2. Generally, decrease the AAA by deductible losses and expenses, nondeductible expenses (other than expenses related to tax-exempt income), and the sum of the shareholders' deductions for depletion for any oil or gas property held by the corporation as described in section 1367(a)(2)(E). If the total decreases under (2) exceed the total increases under (1) above, the excess is a 'net negative adjustment.' If the corporation has a net negative adjustment, don't take it into account under (2). Instead, take it into account only under (4) below. 3. Decrease AAA (but not below zero) by property distributions (other than dividend distributions from AE&P), unless the corporation elects to reduce AE&P first. 4. Decrease AAA by any net negative adjustment. Tip: The AAA may have a negative balance at year end. See section 1368(e).",
                "summary_text": "The AAA adjustment ORDER matters: income first, then losses/expenses EXCLUDING any net negative adjustment, then distributions (not below zero, measured before the net negative adjustment), then the net negative adjustment last. Losses can drive AAA negative; distributions cannot.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "M-2 Columns (b) PTEP and (c) AE&P (2025)",
                "location_reference": "i1120s (2025) p.50, Schedule M-2 Columns (b)/(c)",
                "excerpt_text": "Column (b). Shareholders' Undistributed Taxable Income Previously Taxed. The shareholders' undistributed taxable income previously taxed account, also called previously taxed earnings and profits (PTEP), is maintained only if the corporation had a balance in this account at the start of its 2025 tax year. If there is a beginning balance for the 2025 tax year, no adjustments are made to the account except to reduce the account for distributions made under section 1375(d) (as in effect before the enactment of the Subchapter S Revision Act of 1982). — Column (c). Accumulated Earnings and Profits. If the corporation was a C corporation in a prior year, or if it engaged in a tax-free reorganization with a C corporation, enter the amount of any AE&P at the close of its 2023 tax year on line 1 in column (c). For details on figuring AE&P, see section 312. Estimates based on retained earnings at the end of the tax year are acceptable. If the corporation has AE&P, it may be liable for tax imposed on excess net passive income.",
                "summary_text": "PTEP: beginning-balance-only account, reduced solely by §1375(d) distributions. AE&P: C-corporation-era earnings; its presence triggers excess-net-passive-income tax exposure (page 1 line 23a).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "M-2 Column (d) OAA + AE&P adjustments (2025)",
                "location_reference": "i1120s (2025) p.51, Schedule M-2 Column (d) / Distributions",
                "excerpt_text": "Column (d). Other Adjustments Account. The other adjustments account is adjusted for tax-exempt income (and related expenses) and federal taxes attributable to a C corporation tax year. After these adjustments are made, the account is reduced for any distributions made during the year. — The only adjustments that can be made to the AE&P of an S corporation are: a. Reductions for dividend distributions; b. Adjustments for redemptions, liquidations, reorganizations, etc.; and c. Reductions for investment credit recapture tax for which the corporation is liable. See section 1371(c) and (d)(3).",
                "summary_text": "OAA holds tax-exempt income and related expenses (plus C-year federal taxes). AE&P moves only for dividend distributions, redemption/reorg adjustments, and investment credit recapture — dividend distributions from AE&P are what Schedule K 17c reports (1099-DIV).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "M-2 Distributions — general ordering rule (2025)",
                "location_reference": "i1120s (2025) p.51, Distributions",
                "excerpt_text": "General rule. Unless the corporation makes one of the elections described below, property distributions (including cash) are applied in the following order (to reduce accounts of the S corporation that are used to figure the tax effect of distributions made by the corporation to its shareholders). 1. Reduce the AAA determined without regard to any net negative adjustment for the tax year (but not below zero). If distributions during the tax year exceed the AAA at the close of the tax year, determined without regard to any net negative adjustment for the tax year, the AAA is allocated pro rata to each distribution made during the tax year. See section 1368. 2. Reduce shareholders' PTEP account for any section 1375(d) (as in effect before 1983) distributions. 3. Reduce AE&P. 4. Reduce the other adjustments account (OAA). 5. Reduce any remaining shareholders' equity accounts. — Elections relating to source of distributions: election to distribute AE&P first, election to make a deemed dividend, election to forego PTEP (each with the consent of all affected shareholders, section 1368(e)(3)(B); irrevocable, per-tax-year).",
                "summary_text": "Distribution ordering: AAA (measured WITHOUT the net negative adjustment, floor zero, pro rata) → PTEP (§1375(d)) → AE&P (dividends) → OAA → remaining equity; three shareholder-consent elections can modify the order.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "M-2 worksheet example — published figures (2025)",
                "location_reference": "i1120s (2025) pp.50-51, Example + Schedule M-2 Worksheet",
                "excerpt_text": "Items per return are: 1. Page 1, line 22 income—$10,000; 2. Schedule K, line 2 loss—($3,000); 3. Schedule K, line 4 income—$4,000; 4. Schedule K, line 5a income—$16,000; 5. Schedule K, line 12a deduction—$24,000; 6. Schedule K, line 12e deduction—$3,000; 7. Schedule K, line 13g work opportunity credit—$6,000; 8. Schedule K, line 16a tax-exempt interest—$5,000; 9. Schedule K, line 16c nondeductible expenses—$6,000; and 10. Schedule K, line 16d distributions—$65,000. — Worksheet (AAA column): line 2 = 10,000; line 3 = 20,000; line 5 = (36,000); line 6 = (6,000); line 7 = -0-; line 8 = (6,000). (OAA column): line 3 = 5,000; line 6 = 5,000; line 7 = 5,000; line 8 = -0-. The AAA at the end of the tax year (figured without regard to distributions and the net negative adjustment of $6,000) is zero, and distributions can't reduce the AAA below zero. The remaining $60,000 of distributions aren't entered on Schedule M-2.",
                "summary_text": "The published M-2 example: net negative adjustment of $6,000 → the AAA distribution base is ZERO, so line 7 col (a) = 0 even with $65,000 distributed; OAA absorbs $5,000; the remaining $60,000 never appears on M-2.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_1120S_SCHD_INSTR_FULL",
        "source_type": "official_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "Instructions for Schedule D (Form 1120-S) (2025) — fetched 2026-03-18",
        "citation": "Instructions for Schedule D (Form 1120-S) (2025)",
        "issuer": "IRS",
        "current_status": "active",
        "is_substantive_authority": True,
        "requires_human_review": False,
        "trust_score": 9.5,
        "topics": ["schedule_d", "capital_gains", "1120s"],
        "excerpts": [
            {
                "excerpt_label": "Part I — Short-term capital gains and losses",
                "excerpt_text": "Report on Part I the sale or exchange of capital assets held 1 year or less. Line 1a: Totals from Form 8949 Box A (basis reported to IRS, no adjustments). Line 1b: Totals from Form 8949 Box B (basis reported, with adjustments). Line 1c: Totals from Form 8949 Box C (basis NOT reported to IRS). Lines 2-4: Short-term gain from installment sales (Form 6252), like-kind exchanges (Form 8824), S corporation's share from other entities. Line 5: Net short-term capital gain (loss) — combine lines 1 through 4. Carry to Schedule K, line 7.",
                "summary_text": "Schedule D Part I Line 5 (net short-term) flows to Schedule K Line 7.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part II — Long-term capital gains and losses",
                "excerpt_text": "Report on Part II the sale or exchange of capital assets held more than 1 year. Line 7a: Totals from Form 8949 Box D (basis reported to IRS, no adjustments). Line 7b: Totals from Form 8949 Box E (basis reported, with adjustments). Line 7c: Totals from Form 8949 Box F (basis NOT reported to IRS). Lines 8-10: Long-term gain from installment sales, like-kind exchanges, S corporation's share from other entities. Line 11: Capital gain distributions. Line 12: Net long-term capital gain (loss) — combine lines 7 through 11. Carry to Schedule K, line 8a.",
                "summary_text": "Schedule D Part II Line 12 (net long-term) flows to Schedule K Line 8a.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule D does NOT include Section 1231",
                "excerpt_text": "Do not report on Schedule D the sale or exchange of property used in a trade or business — report those on Form 4797. Section 1231 gains and losses are reported on Form 4797 and flow to Schedule K line 9, not through Schedule D.",
                "summary_text": "Section 1231 transactions go to 4797, NOT Schedule D. 4797 -> K9 directly.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part III — Built-in gains tax (section 1374)",
                "excerpt_text": "If the S corporation was formerly a C corporation (or received assets from a C corporation in a carryover basis transaction), it may be subject to tax on built-in gains recognized within the 5-year recognition period. The tax is 21% of net recognized built-in gain, limited to the net unrealized built-in gain at the time of the S election. Complete Part III only if the corporation had a net recognized built-in gain during the tax year.",
                "summary_text": "BIG tax = 21% of net recognized built-in gain within 5-year recognition period, limited to NUBIG.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_PUB463",
        "source_type": "official_publication",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "Publication 463 (2025) — Travel, Gift, and Car Expenses, Chapter 2 Meals and Entertainment (fetched 2026-07-09)",
        "citation": "IRS Publication 463 (2025), Chapter 2",
        "issuer": "IRS",
        "current_status": "active",
        "is_substantive_authority": True,
        "requires_human_review": False,
        "trust_score": 9.5,
        "topics": ["1120s", "scorp"],
        "excerpts": [
            {
                "excerpt_label": "Exceptions to the 50% limit for meals — the six 100% categories",
                "excerpt_text": (
                    "Your meal expense isn't subject to the 50% limit if the expense meets one of the "
                    "following exceptions. Exception 1 — expenses treated as compensation: expenses for "
                    "goods, services, and facilities, to the extent treated by the taxpayer as "
                    "compensation to an employee and as wages for tax purposes. Exception 2 — "
                    "employee's reimbursed expenses (accountable plan). Exception 3 — self-employed "
                    "reimbursed expenses (independent contractor reimbursed by the client with adequate "
                    "records; the CLIENT is then subject to the 50% limit). Exception 4 — recreational "
                    "expenses for employees: recreational, social, or similar activities (including "
                    "facilities) such as a holiday party or a summer picnic. Exception 5 — advertising "
                    "expenses: meals provided to the general public as a means of advertising or "
                    "promoting goodwill in the community. Exception 6 — sale of meals: meals actually "
                    "sold to the public (e.g., a restaurant's food furnished to its customers). "
                    "[Statutory basis: §274(n)(2)(A) — expenses described in §274(e)(2), (3), (4), "
                    "(7), (8), or (9).]"
                ),
                "summary_text": "The 100%-deductible meal categories: compensation-treated, reimbursed (employee/self-employed), recreational/social employee events, meals to the general public (advertising), meals sold to customers. §274(n)(2)(A)/§274(e).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "DOT hours-of-service meals — the percentage is 80%",
                "excerpt_text": (
                    "Individuals subject to 'hours of service' limits. You can deduct a higher "
                    "percentage of your meal expenses while traveling away from your tax home if the "
                    "meals take place during or incident to any period subject to the Department of "
                    "Transportation's 'hours of service' limits. The percentage is 80%. Individuals "
                    "subject to the Department of Transportation's 'hours of service' limits include: "
                    "certain air transportation workers (such as pilots, crew, dispatchers, mechanics, "
                    "and control tower operators) under Federal Aviation Administration regulations; "
                    "interstate truck operators and bus drivers under Department of Transportation "
                    "regulations; certain railroad employees (such as engineers, conductors, train "
                    "crews, dispatchers, and control operations personnel) under Federal Railroad "
                    "Administration regulations; and certain merchant mariners under Coast Guard "
                    "regulations."
                ),
                "summary_text": "DOT hours-of-service meals deductible at 80% (§274(n)(3)); lists the covered worker classes (FAA/DOT/FRA/Coast Guard).",
                "is_key_excerpt": True,
            },
        ],
    },
]

# Source codes already loaded by load_all_federal or load_1120s_specs
EXISTING_SOURCES = [
    "IRS_2025_1120S_INSTR", "IRC_1363", "IRC_1366", "IRC_1367", "IRC_1368",
    "IRC_1374", "IRC_1377", "IRC_179", "IRC_168", "IRC_1222", "IRC_199A",
    "IRC_1231", "IRC_1245", "IRC_1250", "IRC_274", "IRS_2025_4797_INSTR",
    "IRS_2025_1120S_SCHD_INSTR", "IRS_2025_1120S_K1_INSTR",
]


class Command(BaseCommand):
    help = "Load 1120-S full specs — Page 1, M-1, M-2, expanded K, cross-form diagnostics"

    def handle(self, *_args, **_options):
        with transaction.atomic():
            sources = self._load_sources()
            self._load_page1(sources)
            self._load_schedule_m1(sources)
            self._load_schedule_m2(sources)
            self._expand_schedule_k(sources)
            self._add_schedule_d_flow_rules(sources)
            self._add_cross_form_diagnostics(sources)
            self._add_cross_form_tests(sources)
        self._report_totals()

    # ─────────────────────────────────────────────────────────────────────────
    # Authority sources
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

        # In-loader stale-excerpt self-heal (the s58 FABRICATED-EXCERPT class):
        # these labels carried composite/paraphrased "excerpts" with pre-Form-7205
        # page-1 numbering, a 1065 guaranteed-payments line on the 1120-S M-1, and
        # a page-1-line-21 M-2 tie. All replaced 2026-07-12 with verbatim
        # f1120s.pdf (2025) / i1120s (2025) text above.
        stale_labels = [
            "Page 1 Lines 1-6 — Income computation",
            "Page 1 Lines 7-20 — Deductions",
            "Line 19 Special Rules — Travel, meals, and entertainment (fetched 2026-07-09)",
            "Page 1 Line 21 — Ordinary business income (loss)",
            "Schedule K — Line sources and separately stated items",
            "Schedule M-1 — Reconciliation of income per books with income per return",
            "Schedule M-2 — Analysis of AAA, OAA, PTEP, and AE&P",
            "4797 flow — bypasses Schedule D",
        ]
        full_src = sources.get("IRS_2025_1120S_INSTR_FULL")
        if full_src:
            stale = AuthorityExcerpt.objects.filter(
                authority_source=full_src, excerpt_label__in=stale_labels,
            )
            if stale.exists():
                names = ", ".join(sorted(stale.values_list("excerpt_label", flat=True)))
                self.stdout.write(
                    "  deleting {} stale fabricated/renumbered excerpts: {}".format(
                        stale.count(), names.encode("ascii", "replace").decode("ascii"))
                )
                stale.delete()

        self.stdout.write(f"Sources ready: {len(sources)}")
        return sources

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers (same pattern as load_1120s_specs.py)
    # ─────────────────────────────────────────────────────────────────────────

    def _upsert_form(self, form_number, form_title, entity_types, notes="") -> TaxForm:
        form, created = TaxForm.objects.update_or_create(
            form_number=form_number, jurisdiction="FED", tax_year=2025, version=1,
            defaults={"form_title": form_title, "entity_types": entity_types,
                       "status": "draft", "notes": notes},
        )
        self.stdout.write(f"{'Created' if created else 'Updated'} {form_number}")
        return form

    def _upsert_facts(self, form, facts_data):
        for f in facts_data:
            f = dict(f)
            key = f.pop("fact_key")
            FormFact.objects.update_or_create(tax_form=form, fact_key=key, defaults=f)
        self.stdout.write(f"  {len(facts_data)} facts")

    def _upsert_rules(self, form, rules_data) -> dict[str, FormRule]:
        created = {}
        for r in rules_data:
            r = dict(r)
            rid = r.pop("rule_id")
            rule, _ = FormRule.objects.update_or_create(
                tax_form=form, rule_id=rid, defaults=r,
            )
            created[rid] = rule
        self.stdout.write(f"  {len(created)} rules")
        return created

    def _upsert_links(self, rules, sources, links_data):
        count = 0
        for rule_id, source_code, level, note in links_data:
            rule = rules.get(rule_id)
            source = sources.get(source_code)
            if rule and source:
                RuleAuthorityLink.objects.get_or_create(
                    form_rule=rule, authority_source=source,
                    defaults={"support_level": level, "relevance_note": note},
                )
                count += 1
        self.stdout.write(f"  {count} authority links")

    def _upsert_lines(self, form, lines_data):
        for ln in lines_data:
            ln = dict(ln)
            num = ln.pop("line_number")
            FormLine.objects.update_or_create(
                tax_form=form, line_number=num, defaults=ln,
            )
        self.stdout.write(f"  {len(lines_data)} lines")

    def _upsert_diagnostics(self, form, diags_data):
        for d in diags_data:
            d = dict(d)
            did = d.pop("diagnostic_id")
            FormDiagnostic.objects.update_or_create(
                tax_form=form, diagnostic_id=did, defaults=d,
            )
        self.stdout.write(f"  {len(diags_data)} diagnostics")

    def _upsert_tests(self, form, tests_data):
        for t in tests_data:
            t = dict(t)
            name = t.pop("scenario_name")
            TestScenario.objects.update_or_create(
                tax_form=form, scenario_name=name, defaults=t,
            )
        self.stdout.write(f"  {len(tests_data)} test scenarios")

    def _upsert_form_links(self, form_code, sources, links):
        for source_code, link_type in links:
            source = sources.get(source_code)
            if source:
                AuthorityFormLink.objects.get_or_create(
                    authority_source=source, form_code=form_code, link_type=link_type,
                    defaults={"note": f"{source_code} -> {form_code}"},
                )

    # ═══════════════════════════════════════════════════════════════════════════
    # Form 1120-S Page 1 — Income & Deductions (Lines 1-21)
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_page1(self, sources):
        form = self._upsert_form(
            "1120S_PAGE1",
            "Form 1120-S Page 1 — Income, Deductions, Tax and Payments",
            ["1120S"],
            notes="Core income/deduction computation + the Tax and Payments block. 2025 face (renumbered 2026-07-12): line 19 = Form 7205 deduction, 20 = other deductions, 21 = total deductions, 22 = ordinary business income (flows to Schedule K Line 1), 23a-28e = tax and payments.",
        )

        self._upsert_facts(form, [
            # Income
            {"fact_key": "gross_receipts", "label": "Gross receipts or sales (Line 1a)", "data_type": "decimal", "required": True, "sort_order": 1},
            {"fact_key": "returns_allowances", "label": "Returns and allowances (Line 1b)", "data_type": "decimal", "sort_order": 2},
            {"fact_key": "net_receipts", "label": "Net receipts (Line 1c = 1a - 1b)", "data_type": "decimal", "sort_order": 3},
            {"fact_key": "cost_of_goods_sold", "label": "Cost of goods sold (Line 2, from Form 1125-A)", "data_type": "decimal", "sort_order": 4},
            {"fact_key": "gross_profit", "label": "Gross profit (Line 3 = 1c - 2)", "data_type": "decimal", "sort_order": 5},
            {"fact_key": "net_gain_4797", "label": "Net gain (loss) from Form 4797, Part II, Line 17 (Line 4)", "data_type": "decimal", "sort_order": 6},
            {"fact_key": "other_income", "label": "Other income (loss) (Line 5)", "data_type": "decimal", "sort_order": 7},
            {"fact_key": "total_income", "label": "Total income (loss) (Line 6 = 3 + 4 + 5)", "data_type": "decimal", "sort_order": 8},
            # Deductions (2025 face: 19 = Form 7205, 20 = other, 21 = total, 22 = OBI)
            {"fact_key": "officer_compensation", "label": "Compensation of officers (Line 7)", "data_type": "decimal", "sort_order": 9},
            {"fact_key": "salaries_wages", "label": "Salaries and wages (Line 8)", "data_type": "decimal", "sort_order": 10},
            {"fact_key": "repairs_maintenance", "label": "Repairs and maintenance (Line 9)", "data_type": "decimal", "sort_order": 11},
            {"fact_key": "bad_debts", "label": "Bad debts (Line 10)", "data_type": "decimal", "sort_order": 12},
            {"fact_key": "rents", "label": "Rents (Line 11)", "data_type": "decimal", "sort_order": 13},
            {"fact_key": "taxes_licenses", "label": "Taxes and licenses (Line 12)", "data_type": "decimal", "sort_order": 14},
            {"fact_key": "interest", "label": "Interest (Line 13)", "data_type": "decimal", "sort_order": 15},
            {"fact_key": "depreciation", "label": "Depreciation (Line 14, from Form 4562, NOT including section 179)", "data_type": "decimal", "sort_order": 16},
            {"fact_key": "depletion", "label": "Depletion (Line 15)", "data_type": "decimal", "sort_order": 17},
            {"fact_key": "advertising", "label": "Advertising (Line 16)", "data_type": "decimal", "sort_order": 18},
            {"fact_key": "pension_plans", "label": "Pension, profit-sharing, etc., plans (Line 17)", "data_type": "decimal", "sort_order": 19},
            {"fact_key": "employee_benefits", "label": "Employee benefit programs (Line 18)", "data_type": "decimal", "sort_order": 20},
            {"fact_key": "energy_efficient_bldg_ded", "label": "Energy efficient commercial buildings deduction (Line 19, attach Form 7205)", "data_type": "decimal", "sort_order": 21,
             "notes": "Section 179D deduction; Form 7205 required (i1120s 2025 p.19). NEW 2025-face row — this insertion shifted the old 19/20/21 down to 20/21/22."},
            {"fact_key": "other_deductions", "label": "Other deductions (Line 20, attach statement)", "data_type": "decimal", "sort_order": 22},
            {"fact_key": "total_deductions", "label": "Total deductions (Line 21 = sum of Lines 7-20)", "data_type": "decimal", "sort_order": 23},
            {"fact_key": "ordinary_business_income", "label": "Ordinary business income (loss) (Line 22 = Line 6 - Line 21)", "data_type": "decimal", "sort_order": 24},
            # Tax and Payments (2025 face lines 23a-28e)
            {"fact_key": "excess_net_passive_tax", "label": "Excess net passive income or LIFO recapture tax (Line 23a)", "data_type": "decimal", "sort_order": 25,
             "notes": "Entity-level tax; applies only with C-corporation history (AE&P + passive investment income > 25% of gross receipts, or LIFO recapture under Reg. 1.1363-2). Worksheet in i1120s pp.21-22."},
            {"fact_key": "schd_big_tax", "label": "Tax from Schedule D (Form 1120-S) — built-in gains (Line 23b)", "data_type": "decimal", "sort_order": 26,
             "notes": "From Schedule D (1120-S) Part III line 23 (section 1374)."},
            {"fact_key": "total_tax", "label": "Total tax (Line 23c = 23a + 23b + additional taxes)", "data_type": "decimal", "sort_order": 27},
            {"fact_key": "est_tax_payments", "label": "Current year's estimated tax payments and preceding year's overpayment credited (Line 24a)", "data_type": "decimal", "sort_order": 28},
            {"fact_key": "form7004_deposit", "label": "Tax deposited with Form 7004 (Line 24b)", "data_type": "decimal", "sort_order": 29},
            {"fact_key": "fuels_credit_4136", "label": "Credit for federal tax paid on fuels (Line 24c, attach Form 4136)", "data_type": "decimal", "sort_order": 30},
            {"fact_key": "elective_payment_3800", "label": "Elective payment election amount from Form 3800 (Line 24d)", "data_type": "decimal", "sort_order": 31,
             "notes": "Total gross EPE amount from Form 3800, Part III, line 6, column (h) (i1120s 2025 p.22)."},
            {"fact_key": "total_payments", "label": "Total payments (Line 24z = 24a + 24b + 24c + 24d)", "data_type": "decimal", "sort_order": 32},
            {"fact_key": "est_tax_penalty", "label": "Estimated tax penalty (Line 25)", "data_type": "decimal", "sort_order": 33},
            {"fact_key": "form_2220_attached", "label": "Form 2220 attached (Line 25 checkbox)", "data_type": "boolean", "sort_order": 34},
            {"fact_key": "amount_owed", "label": "Amount owed (Line 26, if 24z < 23c + 25)", "data_type": "decimal", "sort_order": 35},
            {"fact_key": "overpayment", "label": "Overpayment (Line 27, if 24z > 23c + 25)", "data_type": "decimal", "sort_order": 36},
            {"fact_key": "credited_to_next_year", "label": "Overpayment credited to 2026 estimated tax (Line 28a)", "data_type": "decimal", "sort_order": 37},
            {"fact_key": "refunded", "label": "Overpayment refunded (Line 28b)", "data_type": "decimal", "sort_order": 38},
            {"fact_key": "refund_routing_number", "label": "Refund direct deposit — routing number (Line 28c)", "data_type": "string", "sort_order": 39},
            {"fact_key": "refund_account_type", "label": "Refund direct deposit — account type (Line 28d)", "data_type": "choice", "sort_order": 40,
             "choices": ["checking", "savings"]},
            {"fact_key": "refund_account_number", "label": "Refund direct deposit — account number (Line 28e)", "data_type": "string", "sort_order": 41},
            # Meals & entertainment four-tier worksheet — a Line 19 component
            # (100% tier added by Ken ruling 2026-07-09, tts s41 usability item 9)
            {"fact_key": "meals_100pct", "label": "Meals — 100% deductible (§274(n)(2)/(e) exception categories only)", "data_type": "decimal", "sort_order": 24,
             "notes": "ONLY the Pub 463 (2025) ch. 2 exception categories: treated as compensation (W-2/1099-NEC); reimbursed under an accountable arrangement; recreational/social employee events (holiday party, summer picnic); meals provided to the general public (advertising/goodwill); meals sold to customers. NOT a general restaurant rate — the temporary 100% restaurant deduction (2021-2022) is expired."},
            {"fact_key": "meals_dot_80pct", "label": "Meals — DOT hours-of-service (80% deductible)", "data_type": "decimal", "sort_order": 25,
             "notes": "§274(n)(3): meals consumed during or incident to a period subject to the Department of Transportation hours-of-service limits. Pub 463 (2025): 'The percentage is 80%.'"},
            {"fact_key": "meals_50pct", "label": "Meals — standard business (50% deductible)", "data_type": "decimal", "sort_order": 26,
             "notes": "§274(n)(1) general rule per i1120s 2025: 'Generally, the corporation can deduct only 50% of the amount otherwise allowable for meal expenses.' Not lavish/extravagant; employee present (§274(k))."},
            {"fact_key": "entertainment_0pct", "label": "Entertainment — nondeductible (0%)", "data_type": "decimal", "sort_order": 27,
             "notes": "§274(a) post-TCJA per i1120s 2025: 'Generally, entertainment expenses, membership dues, and facilities used in connection with these activities can't be deducted.'"},
            {"fact_key": "meals_deductible_total", "label": "Meals & entertainment — deductible portion (component of Line 19)", "data_type": "decimal", "sort_order": 28},
            {"fact_key": "meals_nondeductible_total", "label": "Meals & entertainment — nondeductible portion (→ Schedule K 16c, M-1 3b, M-2 5a)", "data_type": "decimal", "sort_order": 29},
        ])

        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "Net receipts", "description": "Line 1c = Line 1a - Line 1b",
             "rule_type": "calculation", "formula": "gross_receipts - returns_allowances",
             "inputs": ["gross_receipts", "returns_allowances"], "outputs": ["net_receipts"],
             "precedence": 1, "sort_order": 1},
            {"rule_id": "R002", "title": "Gross profit", "description": "Line 3 = Line 1c - Line 2 (cost of goods sold from Form 1125-A)",
             "rule_type": "calculation", "formula": "net_receipts - cost_of_goods_sold",
             "inputs": ["net_receipts", "cost_of_goods_sold"], "outputs": ["gross_profit"],
             "precedence": 2, "sort_order": 2},
            {"rule_id": "R003", "title": "Page 1 Line 4 = Form 4797 Part II Line 17",
             "description": "Net gain (loss) from Form 4797. This is the ORDINARY gain/loss from Part II Line 17, which includes short-term dispositions and recapture from Part III Line 31. NOT the Section 1231 gain from Part I — that goes to Schedule K Line 9.",
             "rule_type": "routing", "formula": "Form_4797_Part_II_Line_17",
             "inputs": ["4797_part2_line17"], "outputs": ["net_gain_4797"],
             "precedence": 3, "sort_order": 3,
             "notes": "VERIFIED from fresh IRS 1120-S instructions fetch 2026-03-18. This was a persistent bug source in tts-tax-app."},
            {"rule_id": "R004", "title": "Total income", "description": "Line 6 = Line 3 + Line 4 + Line 5",
             "rule_type": "calculation", "formula": "gross_profit + net_gain_4797 + other_income",
             "inputs": ["gross_profit", "net_gain_4797", "other_income"], "outputs": ["total_income"],
             "precedence": 4, "sort_order": 4},
            {"rule_id": "R005", "title": "Total deductions", "description": "Line 21 = sum of Lines 7 through 20 (2025 face: 'Total deductions. Add lines 7 through 20'), including the line 19 energy efficient commercial buildings deduction. Section 179 is NOT included here — it is separately stated on Schedule K Line 11.",
             "rule_type": "calculation",
             "formula": "officer_compensation + salaries_wages + repairs_maintenance + bad_debts + rents + taxes_licenses + interest + depreciation + depletion + advertising + pension_plans + employee_benefits + energy_efficient_bldg_ded + other_deductions",
             "inputs": ["officer_compensation", "salaries_wages", "repairs_maintenance", "bad_debts", "rents",
                         "taxes_licenses", "interest", "depreciation", "depletion", "advertising",
                         "pension_plans", "employee_benefits", "energy_efficient_bldg_ded", "other_deductions"],
             "outputs": ["total_deductions"], "precedence": 5, "sort_order": 5},
            {"rule_id": "R006", "title": "Ordinary business income (loss)",
             "description": "Line 22 = Line 6 - Line 21 (2025 face: 'Ordinary business income (loss). Subtract line 21 from line 6'). This is the key output of Page 1. Flows to Schedule K Line 1 for shareholder allocation. Per i1120s (2025) p.21, line 22 income is NOT used in figuring the excess net passive income or built-in gains taxes (those use the line 23a worksheet's taxable income).",
             "rule_type": "calculation", "formula": "total_income - total_deductions",
             "inputs": ["total_income", "total_deductions"], "outputs": ["ordinary_business_income"],
             "precedence": 6, "sort_order": 6},
            {"rule_id": "R007", "title": "Section 179 exclusion from Page 1",
             "description": "Section 179 deduction is a SEPARATELY STATED item under IRC 1363(b). It must appear on Schedule K Line 11, NOT on Page 1 Line 14 (depreciation). Page 1 Line 14 includes regular depreciation and bonus depreciation only.",
             "rule_type": "validation",
             "formula": "depreciation_line_14 must NOT include section_179_amount",
             "inputs": ["depreciation", "section_179_deduction"], "outputs": [],
             "precedence": 0, "sort_order": 7,
             "notes": "IRC 1363(b) requires separately stated items to be excluded from ordinary income computation."},
            {"rule_id": "R008", "title": "Line 14 depreciation source",
             "description": "Page 1 Line 14 = Form 4562 total depreciation minus section 179 (which is separately stated on K Line 11). Includes MACRS regular depreciation and bonus depreciation.",
             "rule_type": "routing", "formula": "Form_4562_total_depreciation - section_179",
             "inputs": ["form_4562_depreciation", "section_179_deduction"], "outputs": ["depreciation"],
             "precedence": 3, "sort_order": 8},
            {"rule_id": "R009", "title": "Meals & entertainment worksheet — deductible portion (Line 20 component)",
             "description": "Four-tier meal/entertainment limitation worksheet. Deductible portion = 100% of exception-category meals (§274(n)(2)(A) via §274(e)(2)/(3)/(4)/(7)/(8)/(9): treated as compensation, reimbursed, recreational/social employee events, provided to the general public, sold to customers) + 80% of DOT hours-of-service meals (§274(n)(3)) + 50% of standard business meals (§274(n)(1)) + 0% of entertainment (§274(a)). The result is a COMPONENT of Line 20 other deductions (2025 face; the pre-renumber text said Line 19) — never a separate face line. The 100% tier is NEW per Ken ruling 2026-07-09 (tts s41 usability item 9).",
             "rule_type": "calculation",
             "formula": "meals_deductible_total = 1.00*meals_100pct + 0.80*meals_dot_80pct + 0.50*meals_50pct + 0.00*entertainment_0pct",
             "inputs": ["meals_100pct", "meals_dot_80pct", "meals_50pct", "entertainment_0pct"],
             "outputs": ["meals_deductible_total"], "precedence": 4, "sort_order": 9,
             "notes": "Verified verbatim 2026-07-09: i1120s (2025) Special Rules — Travel, meals, and entertainment; Pub 463 (2025) ch. 2 Exceptions 1-6 + DOT 80%. TY2026 WATCH: §274(o) disallows employer-operated eating facility / convenience-of-employer meals for amounts paid after 12/31/2025 — re-verify the tiers at the 2026 spec cut."},
            {"rule_id": "R010", "title": "Meals & entertainment worksheet — nondeductible portion routing",
             "description": "Nondeductible portion = 50% of standard business meals + 20% of DOT hours-of-service meals + 100% of entertainment (the 100% tier contributes nothing). Routes to Schedule K Line 16c (nondeductible expenses — see Schedule K R016), M-1 Line 3b (POSITIVE add-back), and M-2 Line 5a (AAA other reductions). Never deducted on Page 1. Deductible + nondeductible portions must sum to the book total of the four tiers.",
             "rule_type": "routing",
             "formula": "meals_nondeductible_total = 0.50*meals_50pct + 0.20*meals_dot_80pct + 1.00*entertainment_0pct",
             "inputs": ["meals_50pct", "meals_dot_80pct", "entertainment_0pct"],
             "outputs": ["meals_nondeductible_total"], "precedence": 4, "sort_order": 10},
            {"rule_id": "R011", "title": "Line 19 = Form 7205 energy efficient commercial buildings deduction",
             "description": "2025 face line 19: 'Energy efficient commercial buildings deduction (attach Form 7205)'. Per i1120s (2025) p.19: complete and attach Form 7205 if claiming the deduction; see section 179D. This NEW face row is what shifted the pre-2023 lines 19/20/21 down to 20/21/22.",
             "rule_type": "routing", "formula": "line_19 = Form_7205_deduction",
             "inputs": ["energy_efficient_bldg_ded"], "outputs": [],
             "precedence": 3, "sort_order": 11,
             "notes": "Form 7205 itself is not yet specced/built — until that unit lands, the amount is preparer-entered with the attachment requirement diagnosed (D006)."},
            {"rule_id": "R012", "title": "Total tax (Line 23c)",
             "description": "Line 23c = line 23a + line 23b, plus additional taxes per i1120s (2025) p.22 (e.g., Form 4255 investment credit recapture attributable to C-corporation-year credits). Face: 'Add lines 23a and 23b (see instructions for additional taxes)'.",
             "rule_type": "calculation", "formula": "total_tax = excess_net_passive_tax + schd_big_tax",
             "inputs": ["excess_net_passive_tax", "schd_big_tax"], "outputs": ["total_tax"],
             "precedence": 7, "sort_order": 12},
            {"rule_id": "R013", "title": "Total payments (Line 24z)",
             "description": "Line 24z = 24a + 24b + 24c + 24d (face: 'Add lines 24a through 24d'). Per i1120s (2025) p.22, a section 643(g) trust-estimated-tax credit is also included in 24z with 'T' on the dotted line.",
             "rule_type": "calculation",
             "formula": "total_payments = est_tax_payments + form7004_deposit + fuels_credit_4136 + elective_payment_3800",
             "inputs": ["est_tax_payments", "form7004_deposit", "fuels_credit_4136", "elective_payment_3800"],
             "outputs": ["total_payments"], "precedence": 8, "sort_order": 13},
            {"rule_id": "R014", "title": "Amount owed / overpayment (Lines 26/27)",
             "description": "Face verbatim: Line 26 'Amount owed. If line 24z is smaller than the total of lines 23c and 25, enter amount owed'; Line 27 'Overpayment. If line 24z is larger than the total of lines 23c and 25, enter amount overpaid'. Exactly one of 26/27 is nonzero (both zero when payments exactly equal tax + penalty).",
             "rule_type": "calculation",
             "formula": "amount_owed = max(0, total_tax + est_tax_penalty - total_payments); overpayment = max(0, total_payments - total_tax - est_tax_penalty)",
             "inputs": ["total_tax", "est_tax_penalty", "total_payments"],
             "outputs": ["amount_owed", "overpayment"], "precedence": 9, "sort_order": 14},
            {"rule_id": "R015", "title": "Line 28 split — credited vs refunded",
             "description": "Line 28: 'Enter amount from line 27' split between 28a (credited to 2026 estimated tax) and 28b (refunded). Per i1120s (2025) p.22 the corporation elects how much of line 27 applies to next year's estimated tax; 28a + 28b must equal line 27. Direct deposit of a 28b refund uses 28c routing / 28d account type / 28e account number.",
             "rule_type": "validation",
             "formula": "credited_to_next_year + refunded == overpayment",
             "inputs": ["credited_to_next_year", "refunded", "overpayment"], "outputs": [],
             "precedence": 10, "sort_order": 15},
        ])

        # Refresh authority-link notes (get_or_create keeps stale relevance notes —
        # e.g. the pre-renumber "Line 21 = Line 6 - Line 20" note on R006).
        RuleAuthorityLink.objects.filter(form_rule__tax_form=form).delete()
        self._upsert_links(rules, sources, [
            ("R001", "IRS_2025_1120S_INSTR_FULL", "primary", "Page 1 income computation"),
            ("R002", "IRS_2025_1120S_INSTR_FULL", "primary", "Gross profit = net receipts - COGS"),
            ("R003", "IRS_2025_1120S_INSTR_FULL", "primary", "Line 4 = Form 4797 Part II Line 17 (verified from fetched instructions)"),
            ("R003", "IRS_2025_4797_INSTR", "secondary", "Form 4797 Part II Line 17 = ordinary gains/losses"),
            ("R004", "IRS_2025_1120S_INSTR_FULL", "primary", "Total income = lines 3+4+5"),
            ("R005", "IRS_2025_1120S_INSTR_FULL", "primary", "Total deductions = sum lines 7-19"),
            ("R006", "IRS_2025_1120S_INSTR_FULL", "primary", "Line 22 = Line 6 - Line 21, flows to K Line 1 (2025 face)"),
            ("R006", "IRC_1363", "secondary", "IRC 1363(b) — separately stated items excluded"),
            ("R011", "IRS_2025_1120S_INSTR_FULL", "primary", "Line 19 = Form 7205 energy efficient commercial buildings deduction (i1120s 2025 p.19; section 179D)"),
            ("R012", "IRS_2025_1120S_INSTR_FULL", "primary", "23c = 23a + 23b + additional taxes (i1120s 2025 p.22)"),
            ("R012", "IRC_1374", "secondary", "Section 1374 built-in gains tax (line 23b)"),
            ("R013", "IRS_2025_1120S_INSTR_FULL", "primary", "24z = add lines 24a through 24d (2025 face)"),
            ("R014", "IRS_2025_1120S_INSTR_FULL", "primary", "Lines 26/27 owed vs overpaid — 24z compared to 23c + 25 (2025 face)"),
            ("R015", "IRS_2025_1120S_INSTR_FULL", "primary", "Line 28a/28b split of the line 27 overpayment (i1120s 2025 p.22)"),
            ("R007", "IRC_1363", "primary", "IRC 1363(b) — section 179 is separately stated"),
            ("R007", "IRC_179", "secondary", "IRC 179(d)(4) — passthrough separately stated for S-Corps"),
            ("R008", "IRS_2025_1120S_INSTR_FULL", "primary", "Line 14 depreciation from Form 4562"),
            ("R009", "IRS_2025_1120S_INSTR_FULL", "primary", "Line 19 Special Rules — meals 50% general; §274(n)(3) DOT; entertainment nondeductible; compensation-treated deductible"),
            ("R009", "IRS_2025_PUB463", "primary", "Pub 463 (2025) ch. 2 — Exceptions 1-6 to the 50% limit (the 100% tier) + DOT 80%"),
            ("R009", "IRC_274", "secondary", "§274(a)/(k)/(n)(1)/(n)(2)/(n)(3) statutory tiers"),
            ("R010", "IRS_2025_1120S_INSTR_FULL", "primary", "Nondeductible portion → Schedule K 16c / M-1 3b add-back"),
            ("R010", "IRC_274", "secondary", "§274 disallowed portion — permanent book-tax difference"),
        ])

        self._upsert_lines(form, [
            {"line_number": "1a", "description": "Gross receipts or sales", "line_type": "input", "sort_order": 1},
            {"line_number": "1b", "description": "Returns and allowances", "line_type": "input", "sort_order": 2},
            {"line_number": "1c", "description": "Balance (1a minus 1b)", "line_type": "calculated", "source_rules": ["R001"], "sort_order": 3},
            {"line_number": "2", "description": "Cost of goods sold (Form 1125-A)", "line_type": "input", "destination_form": "Form 1125-A", "sort_order": 4},
            {"line_number": "3", "description": "Gross profit (1c minus 2)", "line_type": "calculated", "source_rules": ["R002"], "sort_order": 5},
            {"line_number": "4", "description": "Net gain (loss) from Form 4797, Part II, line 17", "line_type": "calculated", "source_rules": ["R003"], "destination_form": "Form 4797 Part II Line 17", "sort_order": 6},
            {"line_number": "5", "description": "Other income (loss)", "line_type": "input", "sort_order": 7},
            {"line_number": "6", "description": "Total income (loss) (add lines 3 through 5)", "line_type": "subtotal", "source_rules": ["R004"], "sort_order": 8},
            {"line_number": "7", "description": "Compensation of officers", "line_type": "input", "sort_order": 9},
            {"line_number": "8", "description": "Salaries and wages", "line_type": "input", "sort_order": 10},
            {"line_number": "9", "description": "Repairs and maintenance", "line_type": "input", "sort_order": 11},
            {"line_number": "10", "description": "Bad debts", "line_type": "input", "sort_order": 12},
            {"line_number": "11", "description": "Rents", "line_type": "input", "sort_order": 13},
            {"line_number": "12", "description": "Taxes and licenses", "line_type": "input", "sort_order": 14},
            {"line_number": "13", "description": "Interest", "line_type": "input", "sort_order": 15},
            {"line_number": "14", "description": "Depreciation (Form 4562, NOT including section 179)", "line_type": "calculated", "source_rules": ["R008"], "destination_form": "Form 4562", "sort_order": 16},
            {"line_number": "15", "description": "Depletion", "line_type": "input", "sort_order": 17},
            {"line_number": "16", "description": "Advertising", "line_type": "input", "sort_order": 18},
            {"line_number": "17", "description": "Pension, profit-sharing, etc., plans", "line_type": "input", "sort_order": 19},
            {"line_number": "18", "description": "Employee benefit programs", "line_type": "input", "sort_order": 20},
            {"line_number": "19", "description": "Energy efficient commercial buildings deduction (attach Form 7205)", "line_type": "input", "sort_order": 21, "source_rules": ["R011"],
             "destination_form": "Form 7205",
             "notes": "NEW 2025-face row (section 179D). This insertion shifted the pre-2023 lines 19/20/21 down to 20/21/22."},
            {"line_number": "20", "description": "Other deductions (attach statement)", "line_type": "input", "sort_order": 22, "source_rules": ["R009"],
             "notes": "Includes ONLY the deductible portion of meals per the R009 four-tier worksheet (100%/80%/50%/0%); the nondeductible portion routes to K 16c / M-1 3b / M-2 5a (R010)."},
            {"line_number": "21", "description": "Total deductions. Add lines 7 through 20", "line_type": "subtotal", "source_rules": ["R005"], "sort_order": 23},
            {"line_number": "22", "description": "Ordinary business income (loss). Subtract line 21 from line 6", "line_type": "total", "source_rules": ["R006"], "destination_form": "Schedule K Line 1", "sort_order": 24,
             "notes": "Key output of Page 1. Flows to Schedule K Line 1 for shareholder allocation. NOT the taxable-income base for the 23a/23b entity-level taxes (i1120s 2025 p.21)."},
            {"line_number": "23a", "description": "Excess net passive income or LIFO recapture tax (see instructions)", "line_type": "input", "sort_order": 25,
             "notes": "Requires C-corporation history (AE&P / LIFO recapture). Figured on the i1120s Line 23a worksheet; computation statement attached."},
            {"line_number": "23b", "description": "Tax from Schedule D (Form 1120-S)", "line_type": "calculated", "sort_order": 26,
             "destination_form": "Schedule D (Form 1120-S) Part III Line 23",
             "notes": "Section 1374 built-in gains tax."},
            {"line_number": "23c", "description": "Add lines 23a and 23b (see instructions for additional taxes)", "line_type": "subtotal", "source_rules": ["R012"], "sort_order": 27},
            {"line_number": "24a", "description": "Current year's estimated tax payments and preceding year's overpayment credited to the current year", "line_type": "input", "sort_order": 28},
            {"line_number": "24b", "description": "Tax deposited with Form 7004", "line_type": "input", "sort_order": 29},
            {"line_number": "24c", "description": "Credit for federal tax paid on fuels (attach Form 4136)", "line_type": "input", "destination_form": "Form 4136", "sort_order": 30},
            {"line_number": "24d", "description": "Elective payment election amount from Form 3800", "line_type": "calculated", "destination_form": "Form 3800 Part III Line 6 column (h)", "sort_order": 31},
            {"line_number": "24z", "description": "Add lines 24a through 24d", "line_type": "subtotal", "source_rules": ["R013"], "sort_order": 32},
            {"line_number": "25", "description": "Estimated tax penalty (see instructions). Check if Form 2220 is attached", "line_type": "input", "destination_form": "Form 2220", "sort_order": 33},
            {"line_number": "26", "description": "Amount owed. If line 24z is smaller than the total of lines 23c and 25, enter amount owed", "line_type": "calculated", "source_rules": ["R014"], "sort_order": 34},
            {"line_number": "27", "description": "Overpayment. If line 24z is larger than the total of lines 23c and 25, enter amount overpaid", "line_type": "calculated", "source_rules": ["R014"], "sort_order": 35},
            {"line_number": "28a", "description": "Amount from line 27 credited to 2026 estimated tax", "line_type": "input", "source_rules": ["R015"], "sort_order": 36},
            {"line_number": "28b", "description": "Amount from line 27 refunded", "line_type": "calculated", "source_rules": ["R015"], "sort_order": 37},
            {"line_number": "28c", "description": "Refund direct deposit — routing number", "line_type": "input", "sort_order": 38},
            {"line_number": "28d", "description": "Refund direct deposit — account type (Checking / Savings)", "line_type": "input", "sort_order": 39},
            {"line_number": "28e", "description": "Refund direct deposit — account number", "line_type": "input", "sort_order": 40},
        ])

        # In-loader stale-row self-heal: the 2025-face set is now authoritative.
        _2025_PAGE1_LINES = {
            "1a", "1b", "1c", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11",
            "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22",
            "23a", "23b", "23c", "24a", "24b", "24c", "24d", "24z", "25", "26",
            "27", "28a", "28b", "28c", "28d", "28e",
        }
        stale_lines = FormLine.objects.filter(tax_form=form).exclude(line_number__in=_2025_PAGE1_LINES)
        if stale_lines.exists():
            names = ", ".join(sorted(stale_lines.values_list("line_number", flat=True)))
            self.stdout.write(f"  deleting {stale_lines.count()} stale PAGE1 line rows: {names}")
            stale_lines.delete()

        _PAGE1_FACT_KEYS = {
            "gross_receipts", "returns_allowances", "net_receipts", "cost_of_goods_sold",
            "gross_profit", "net_gain_4797", "other_income", "total_income",
            "officer_compensation", "salaries_wages", "repairs_maintenance", "bad_debts",
            "rents", "taxes_licenses", "interest", "depreciation", "depletion",
            "advertising", "pension_plans", "employee_benefits", "energy_efficient_bldg_ded",
            "other_deductions", "total_deductions", "ordinary_business_income",
            "excess_net_passive_tax", "schd_big_tax", "total_tax", "est_tax_payments",
            "form7004_deposit", "fuels_credit_4136", "elective_payment_3800",
            "total_payments", "est_tax_penalty", "form_2220_attached", "amount_owed",
            "overpayment", "credited_to_next_year", "refunded", "refund_routing_number",
            "refund_account_type", "refund_account_number",
            "meals_100pct", "meals_dot_80pct", "meals_50pct", "entertainment_0pct",
            "meals_deductible_total", "meals_nondeductible_total",
        }
        stale_facts = FormFact.objects.filter(tax_form=form).exclude(fact_key__in=_PAGE1_FACT_KEYS)
        if stale_facts.exists():
            names = ", ".join(sorted(stale_facts.values_list("fact_key", flat=True)))
            self.stdout.write(f"  deleting {stale_facts.count()} stale PAGE1 facts: {names}")
            stale_facts.delete()

        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D001", "title": "Section 179 on Page 1", "severity": "error",
             "condition": "depreciation includes section_179_amount",
             "message": "Section 179 must be separately stated on Schedule K Line 11, not included in Page 1 Line 14 depreciation. Per IRC 1363(b)."},
            {"diagnostic_id": "D002", "title": "Line 4 source mismatch", "severity": "warning",
             "condition": "net_gain_4797 != Form_4797_Part_II_Line_17",
             "message": "Page 1 Line 4 should equal Form 4797 Part II Line 17. Verify 4797 is computed correctly."},
            {"diagnostic_id": "D003", "title": "Charitable on Page 1", "severity": "error",
             "condition": "other_deductions includes charitable_contributions",
             "message": "Charitable contributions are separately stated on Schedule K Lines 12a/12b, not deducted on Page 1."},
            {"diagnostic_id": "D004", "title": "100% meals tier is exception-only", "severity": "warning",
             "condition": "meals_100pct > 0",
             "message": "Amounts on the 100% meals line must fit a section 274(n)(2)/(e) exception: treated as compensation (W-2/1099-NEC), reimbursed under an accountable arrangement, recreational or social employee events (e.g., holiday party), meals provided to the general public, or meals sold to customers. Standard business meals are 50% — the temporary 100% restaurant deduction expired after 2022. Verify the classification."},
            {"diagnostic_id": "D005", "title": "Line 28 split does not equal line 27", "severity": "error",
             "condition": "credited_to_next_year + refunded != overpayment",
             "message": "Line 28a (credited to next year's estimated tax) plus line 28b (refunded) must equal the line 27 overpayment."},
            {"diagnostic_id": "D006", "title": "Line 19 deduction without Form 7205", "severity": "error",
             "condition": "energy_efficient_bldg_ded > 0 AND form_7205 not attached",
             "message": "The line 19 energy efficient commercial buildings deduction requires Form 7205 to be completed and attached (i1120s 2025 p.19; section 179D)."},
        ])

        self._upsert_tests(form, [
            {"scenario_name": "Basic S-Corp — ordinary income only",
             "scenario_type": "normal",
             "inputs": {"gross_receipts": 500000, "returns_allowances": 5000, "cost_of_goods_sold": 200000,
                         "net_gain_4797": 0, "other_income": 0,
                         "officer_compensation": 80000, "salaries_wages": 60000, "repairs_maintenance": 5000,
                         "bad_debts": 0, "rents": 12000, "taxes_licenses": 8000, "interest": 3000,
                         "depreciation": 15000, "depletion": 0, "advertising": 2000,
                         "pension_plans": 5000, "employee_benefits": 4000, "other_deductions": 6000},
             "expected_outputs": {"net_receipts": 495000, "gross_profit": 295000,
                                   "total_income": 295000, "total_deductions": 200000,
                                   "ordinary_business_income": 95000},
             "notes": "No dispositions, no special items. All income flows through K1.", "sort_order": 1},
            {"scenario_name": "S-Corp with 4797 gain flowing to Page 1 Line 4",
             "scenario_type": "normal",
             "inputs": {"gross_receipts": 300000, "returns_allowances": 0, "cost_of_goods_sold": 100000,
                         "net_gain_4797": 25000, "other_income": 0,
                         "officer_compensation": 50000, "salaries_wages": 30000, "repairs_maintenance": 0,
                         "bad_debts": 0, "rents": 0, "taxes_licenses": 5000, "interest": 2000,
                         "depreciation": 10000, "depletion": 0, "advertising": 0,
                         "pension_plans": 0, "employee_benefits": 0, "other_deductions": 3000},
             "expected_outputs": {"gross_profit": 200000, "total_income": 225000,
                                   "total_deductions": 100000, "ordinary_business_income": 125000},
             "notes": "4797 Part II Line 17 = 25000 flows to Line 4. Section 1231 gain flows separately to K9.", "sort_order": 2},
            {"scenario_name": "M&E four-tier worksheet — deductible/nondeductible split",
             "scenario_type": "normal",
             "inputs": {"meals_100pct": 2000, "meals_dot_80pct": 1000, "meals_50pct": 10000,
                         "entertainment_0pct": 3000},
             "expected_outputs": {"meals_deductible_total": 7800, "meals_nondeductible_total": 8200},
             "notes": "2,000x100% + 1,000x80% + 10,000x50% + 3,000x0% = 7,800 deductible (component of Line 20, 2025 face); 5,000 + 200 + 3,000 = 8,200 nondeductible (K16c / M-1 3b / M-2 5a). The two portions sum to the 16,000 book total. 100% tier per Ken ruling 2026-07-09.", "sort_order": 3},
            {"scenario_name": "Tax and payments — BIG tax, overpayment split 28a/28b",
             "scenario_type": "normal",
             "inputs": {"excess_net_passive_tax": 0, "schd_big_tax": 5000,
                         "est_tax_payments": 12000, "form7004_deposit": 0,
                         "fuels_credit_4136": 500, "elective_payment_3800": 0,
                         "est_tax_penalty": 0, "credited_to_next_year": 5000},
             "expected_outputs": {"total_tax": 5000, "total_payments": 12500,
                                   "amount_owed": 0, "overpayment": 7500, "refunded": 2500},
             "notes": "23c = 0 + 5,000; 24z = 12,000 + 500 = 12,500; 24z > 23c + 25 so line 27 = 7,500 overpaid; 28a = 5,000 credited leaves 28b = 2,500 refunded (R015: 28a + 28b = 27).", "sort_order": 4},
            {"scenario_name": "Tax and payments — amount owed",
             "scenario_type": "normal",
             "inputs": {"excess_net_passive_tax": 3000, "schd_big_tax": 0,
                         "est_tax_payments": 1000, "form7004_deposit": 0,
                         "fuels_credit_4136": 0, "elective_payment_3800": 0,
                         "est_tax_penalty": 200},
             "expected_outputs": {"total_tax": 3000, "total_payments": 1000,
                                   "amount_owed": 2200, "overpayment": 0},
             "notes": "24z (1,000) is smaller than 23c + 25 (3,200) so line 26 = 2,200 owed; line 27 = 0.", "sort_order": 5},
            {"scenario_name": "Line 19 Form 7205 deduction in total deductions",
             "scenario_type": "normal",
             "inputs": {"gross_receipts": 200000, "returns_allowances": 0, "cost_of_goods_sold": 0,
                         "net_gain_4797": 0, "other_income": 0,
                         "officer_compensation": 50000, "salaries_wages": 0, "repairs_maintenance": 0,
                         "bad_debts": 0, "rents": 0, "taxes_licenses": 0, "interest": 0,
                         "depreciation": 0, "depletion": 0, "advertising": 0,
                         "pension_plans": 0, "employee_benefits": 0,
                         "energy_efficient_bldg_ded": 25000, "other_deductions": 5000},
             "expected_outputs": {"net_receipts": 200000, "gross_profit": 200000,
                                   "total_income": 200000, "total_deductions": 80000,
                                   "ordinary_business_income": 120000},
             "notes": "The NEW 2025 line 19 (Form 7205 / section 179D) is inside line 21 total deductions: 50,000 + 25,000 + 5,000 = 80,000; OBI (line 22) = 120,000.", "sort_order": 6},
        ])

        self._upsert_form_links("1120S_PAGE1", sources, [
            ("IRS_2025_1120S_INSTR_FULL", "governs"),
            ("IRC_1363", "governs"),
        ])

        self.stdout.write(self.style.SUCCESS("  Page 1 complete."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Schedule M-1 — Reconciliation of Income per Books with Income per Return
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_schedule_m1(self, sources):
        form = self._upsert_form(
            "1120S_M1",
            "Schedule M-1 — Reconciliation of Income (Loss) per Books With Income (Loss) per Return",
            ["1120S"],
            notes="Reconciles book net income to Schedule K line 18 (2025 face line 8). Rebuilt verbatim to the 2025 face 2026-07-12 — the prior block carried a FABRICATED layout (a '3a guaranteed payments' line that exists only on the 1065 M-1; the 1120-S 3a is Depreciation). Line 3 is an ADD-BACK (positive). Not required if Schedule B question 11 = Yes; $10M+ total assets file Schedule M-3 instead.",
        )

        self._upsert_facts(form, [
            {"fact_key": "book_net_income", "label": "Net income (loss) per books (Line 1)", "data_type": "decimal", "required": True, "sort_order": 1},
            {"fact_key": "income_on_k_not_books", "label": "Income included on Schedule K, lines 1, 2, 3c, 4, 5a, 6, 7, 8a, 9, and 10, not recorded on books this year (Line 2, itemize)", "data_type": "decimal", "sort_order": 2,
             "notes": "Face-verbatim K-line list. Describe each item; attach a statement if necessary (i1120s 2025 p.49)."},
            {"fact_key": "expenses_not_on_k", "label": "Expenses recorded on books this year not included on Schedule K, lines 1 through 12e, and 16f (Line 3 total, itemize)", "data_type": "decimal", "sort_order": 3,
             "notes": "ADD-BACK: the section 274 nondeductible portion of meals/entertainment, fines, penalties, etc. This is a POSITIVE number that INCREASES the reconciled income. Itemized on the face as 3a depreciation and 3b travel and entertainment; other items ride the statement. K16f foreign taxes factor in (p.49 tip)."},
            {"fact_key": "m1_3a_depreciation", "label": "Line 3a — Depreciation (book depreciation in excess of Schedule K deduction)", "data_type": "decimal", "sort_order": 4,
             "notes": "Itemized $ component of line 3. The 2025 face 3a is DEPRECIATION — the prior spec's 'guaranteed payments (section 707(c))' 3a was a 1065 M-1 line that has never existed on the 1120-S face."},
            {"fact_key": "m1_3b_travel_ent", "label": "Line 3b — Travel and entertainment (section 274 nondeductible portion)", "data_type": "decimal", "sort_order": 5,
             "notes": "Itemized $ component of line 3. Receives the Page-1 meals-worksheet nondeductible total (PAGE1 R010) plus the other i1120s p.49 3b items (facility costs, gifts over $25, skyboxes, club dues, etc.)."},
            {"fact_key": "line_4_subtotal", "label": "Add lines 1 through 3 (Line 4)", "data_type": "decimal", "sort_order": 6},
            {"fact_key": "income_on_books_not_k", "label": "Income recorded on books this year not included on Schedule K, lines 1 through 10 (Line 5 total, itemize)", "data_type": "decimal", "sort_order": 7,
             "notes": "Tax-exempt interest (itemized as 5a), life insurance proceeds, other non-taxable book income."},
            {"fact_key": "m1_5a_tax_exempt_interest", "label": "Line 5a — Tax-exempt interest", "data_type": "decimal", "sort_order": 8,
             "notes": "Itemized $ component of line 5. Ties to Schedule K line 16a."},
            {"fact_key": "deductions_on_k_not_books", "label": "Deductions included on Schedule K, lines 1 through 12e, and 16f, not charged against book income this year (Line 6 total, itemize)", "data_type": "decimal", "sort_order": 9,
             "notes": "Bonus depreciation / section 179 in excess of book depreciation (itemized as 6a), etc. K16f foreign taxes factor in (p.49 tip)."},
            {"fact_key": "m1_6a_depreciation", "label": "Line 6a — Depreciation (tax depreciation in excess of book)", "data_type": "decimal", "sort_order": 10,
             "notes": "Itemized $ component of line 6."},
            {"fact_key": "line_7_subtotal", "label": "Add lines 5 and 6 (Line 7)", "data_type": "decimal", "sort_order": 11},
            {"fact_key": "income_per_return", "label": "Income (loss) (Schedule K, line 18) (Line 8 = Line 4 - Line 7)", "data_type": "decimal", "sort_order": 12,
             "notes": "The face labels line 8 'Income (loss) (Schedule K, line 18)' — it ties to K18 (and M-3 Part II line 26(d) when M-3 is filed), NOT to page-1 line 22."},
        ])

        # In-loader stale self-heal: the fabricated 1065-style rows must go.
        _M1_FACT_KEYS = {
            "book_net_income", "income_on_k_not_books", "expenses_not_on_k",
            "m1_3a_depreciation", "m1_3b_travel_ent", "line_4_subtotal",
            "income_on_books_not_k", "m1_5a_tax_exempt_interest",
            "deductions_on_k_not_books", "m1_6a_depreciation", "line_7_subtotal",
            "income_per_return",
        }
        stale_facts = FormFact.objects.filter(tax_form=form).exclude(fact_key__in=_M1_FACT_KEYS)
        if stale_facts.exists():
            names = ", ".join(sorted(stale_facts.values_list("fact_key", flat=True)))
            self.stdout.write(f"  deleting {stale_facts.count()} stale M-1 facts: {names}")
            stale_facts.delete()
        _M1_RULE_IDS = {"R001", "R002", "R003", "R004", "R005", "R007", "R008"}
        stale_rules = FormRule.objects.filter(tax_form=form).exclude(rule_id__in=_M1_RULE_IDS)
        if stale_rules.exists():
            names = ", ".join(sorted(stale_rules.values_list("rule_id", flat=True)))
            self.stdout.write(f"  deleting {stale_rules.count()} stale M-1 rules ({names}) — "
                              "R006 guaranteed payments was a 1065 line, never on the 1120-S face")
            stale_rules.delete()
        _M1_DIAG_IDS = {"D001", "D002", "D004", "D005"}
        stale_diags = FormDiagnostic.objects.filter(tax_form=form).exclude(diagnostic_id__in=_M1_DIAG_IDS)
        if stale_diags.exists():
            names = ", ".join(sorted(stale_diags.values_list("diagnostic_id", flat=True)))
            self.stdout.write(f"  deleting {stale_diags.count()} stale M-1 diagnostics ({names})")
            stale_diags.delete()

        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "Line 4 subtotal",
             "description": "Line 4 = Add lines 1 through 3 (2025 face verbatim). Book income plus the line 2 unbooked-K-income and the line 3 nondeductible-expense add-back. The face itemizes line 3 as 3a depreciation and 3b travel and entertainment.",
             "rule_type": "calculation", "formula": "book_net_income + income_on_k_not_books + expenses_not_on_k",
             "inputs": ["book_net_income", "income_on_k_not_books", "expenses_not_on_k"],
             "outputs": ["line_4_subtotal"], "precedence": 1, "sort_order": 1},
            {"rule_id": "R002", "title": "Line 7 subtotal",
             "description": "Line 7 = Add lines 5 and 6 (2025 face verbatim). These are the subtractions: line 5 book income not on Schedule K (5a tax-exempt interest) and line 6 Schedule K deductions not charged against book income (6a depreciation). K16f foreign taxes factor into lines 3 and 6 (i1120s 2025 p.49 tip).",
             "rule_type": "calculation", "formula": "income_on_books_not_k + deductions_on_k_not_books",
             "inputs": ["income_on_books_not_k", "deductions_on_k_not_books"],
             "outputs": ["line_7_subtotal"], "precedence": 2, "sort_order": 2},
            {"rule_id": "R003", "title": "Line 8 = Income (loss) (Schedule K, line 18)",
             "description": "Line 8 = Line 4 - Line 7 (2025 face: 'Income (loss) (Schedule K, line 18). Subtract line 7 from line 4').",
             "rule_type": "calculation", "formula": "line_4_subtotal - line_7_subtotal",
             "inputs": ["line_4_subtotal", "line_7_subtotal"],
             "outputs": ["income_per_return"], "precedence": 3, "sort_order": 3},
            {"rule_id": "R004", "title": "M-1 balance check — ties Schedule K line 18",
             "description": "Line 8 must equal Schedule K line 18 (or Schedule M-3 (Form 1120-S) Part II line 26(d) when M-3 is filed). CORRECTED 2026-07-12: the prior text tied line 8 to 'Page 1 Line 21' — WRONG twice over (the 2025 OBI line is 22, and separately stated items make K18 differ from OBI; the face itself names Schedule K, line 18).",
             "rule_type": "validation", "formula": "income_per_return == schedule_k_line_18",
             "inputs": ["income_per_return"], "outputs": [],
             "precedence": 10, "sort_order": 4},
            {"rule_id": "R005", "title": "Line 3 must be positive (add-back)",
             "description": "Line 3 represents expenses on books that are NOT deductible on the return (the section 274 nondeductible meals/entertainment portion, fines, penalties). This is an ADD-BACK to book income, so it must be a positive number. A negative value would incorrectly subtract from the reconciled income.",
             "rule_type": "validation", "formula": "expenses_not_on_k >= 0",
             "inputs": ["expenses_not_on_k"], "outputs": [],
             "precedence": 0, "sort_order": 5,
             "notes": "CRITICAL: the M-1 add-back sign error was a persistent bug in tts-tax-app. Line 3 is ALWAYS an addition."},
            {"rule_id": "R007", "title": "M-1 applicability — B Q11 skip / $10M M-3 / 2025 partial option",
             "description": "Per i1120s (2025) p.49 verbatim: M-1 isn't required if the corporation answered Yes to Schedule B question 11; corporations with total assets of $10 million or more on the last day of the tax year must file Schedule M-3 instead; a corporation not required to file M-3 may voluntarily file it. For 2025, required-M-3 filers under $50 million total assets (and voluntary filers) may either complete M-3 entirely, or complete M-3 through Part I and complete M-1 instead of M-3 Parts II/III — in which case M-1 line 1 must equal M-3 Part I line 11.",
             "rule_type": "conditional",
             "formula": "if schb_q11 == 'Yes' then M1 not required; if total_assets >= 10000000 then M3 replaces M1",
             "inputs": [], "outputs": [],
             "precedence": 0, "sort_order": 6,
             "notes": "The $10M threshold is the s44-verified figure (an early-era block had fabricated $50M as the M-3 REQUIREMENT threshold; $50M is only the 2025 partial-completion option boundary)."},
            {"rule_id": "R008", "title": "Line 3b travel and entertainment composition",
             "description": "Line 3b (itemized within line 3) carries the section 274 nondeductible items per i1120s (2025) p.49 verbatim: entertainment not deductible under 274(a); meals not deductible under 274(n); qualified transportation fringes under 274(a)(4); entertainment-facility expenses; business gifts over $25; cruise-ship convention expenses over $2,000; employee achievement awards over $400 ($1,600 qualified plan); skyboxes; luxury water travel under 274(m); travel as education; nondeductible club dues; other nondeductible T&E. The Page-1 meals worksheet nondeductible total (PAGE1 R010) flows here.",
             "rule_type": "routing",
             "formula": "m1_3b_travel_ent includes meals_nondeductible_total (PAGE1 R010) + other 274 items",
             "inputs": ["m1_3b_travel_ent"], "outputs": [],
             "precedence": 1, "sort_order": 7},
        ])

        RuleAuthorityLink.objects.filter(form_rule__tax_form=form).delete()
        self._upsert_links(rules, sources, [
            ("R001", "IRS_2025_1120S_INSTR_FULL", "primary", "M-1 line 4 = add lines 1 through 3 (2025 face)"),
            ("R002", "IRS_2025_1120S_INSTR_FULL", "primary", "M-1 line 7 = add lines 5 and 6 (2025 face); 16f tip"),
            ("R003", "IRS_2025_1120S_INSTR_FULL", "primary", "M-1 line 8 = line 4 minus line 7 (2025 face)"),
            ("R004", "IRS_2025_1120S_INSTR_FULL", "primary", "Line 8 ties Schedule K line 18 / M-3 Part II 26(d) (face + i1120s p.48)"),
            ("R005", "IRS_2025_1120S_INSTR_FULL", "primary", "Line 3 is expenses on books not deducted = ADD-BACK"),
            ("R007", "IRS_2025_1120S_INSTR_FULL", "primary", "M-1 applicability bullets (i1120s 2025 p.49 verbatim)"),
            ("R008", "IRS_2025_1120S_INSTR_FULL", "primary", "Line 3b travel and entertainment item list (i1120s 2025 p.49 verbatim)"),
            ("R008", "IRC_274", "secondary", "Section 274(a)/(k)/(m)/(n) disallowances"),
        ])

        self._upsert_lines(form, [
            {"line_number": "1", "description": "Net income (loss) per books", "line_type": "input", "sort_order": 1},
            {"line_number": "2", "description": "Income included on Schedule K, lines 1, 2, 3c, 4, 5a, 6, 7, 8a, 9, and 10, not recorded on books this year (itemize)", "line_type": "input", "sort_order": 2},
            {"line_number": "3", "description": "Expenses recorded on books this year not included on Schedule K, lines 1 through 12e, and 16f (itemize)", "line_type": "input", "source_rules": ["R005"], "sort_order": 3,
             "notes": "CRITICAL: POSITIVE add-back. Itemized on the face as 3a depreciation and 3b travel and entertainment."},
            {"line_number": "3a", "description": "Depreciation $ (itemized component of line 3)", "line_type": "input", "sort_order": 4,
             "notes": "The 2025 face 3a is DEPRECIATION. The prior spec's 'guaranteed payments (section 707(c))' here was a 1065 M-1 line — fabricated for the 1120-S."},
            {"line_number": "3b", "description": "Travel and entertainment $ (itemized component of line 3)", "line_type": "input", "source_rules": ["R008"], "sort_order": 5,
             "notes": "Receives the Page-1 meals-worksheet nondeductible total (PAGE1 R010)."},
            {"line_number": "4", "description": "Add lines 1 through 3", "line_type": "subtotal", "source_rules": ["R001"], "sort_order": 6},
            {"line_number": "5", "description": "Income recorded on books this year not included on Schedule K, lines 1 through 10 (itemize)", "line_type": "input", "sort_order": 7},
            {"line_number": "5a", "description": "Tax-exempt interest $ (itemized component of line 5)", "line_type": "input", "sort_order": 8,
             "notes": "Ties to Schedule K line 16a."},
            {"line_number": "6", "description": "Deductions included on Schedule K, lines 1 through 12e, and 16f, not charged against book income this year (itemize)", "line_type": "input", "sort_order": 9},
            {"line_number": "6a", "description": "Depreciation $ (itemized component of line 6)", "line_type": "input", "sort_order": 10},
            {"line_number": "7", "description": "Add lines 5 and 6", "line_type": "subtotal", "source_rules": ["R002"], "sort_order": 11},
            {"line_number": "8", "description": "Income (loss) (Schedule K, line 18). Subtract line 7 from line 4", "line_type": "total", "source_rules": ["R003", "R004"], "sort_order": 12,
             "destination_form": "Schedule K Line 18"},
        ])

        _M1_LINES = {"1", "2", "3", "3a", "3b", "4", "5", "5a", "6", "6a", "7", "8"}
        stale_lines = FormLine.objects.filter(tax_form=form).exclude(line_number__in=_M1_LINES)
        if stale_lines.exists():
            names = ", ".join(sorted(stale_lines.values_list("line_number", flat=True)))
            self.stdout.write(f"  deleting {stale_lines.count()} stale M-1 line rows: {names}")
            stale_lines.delete()

        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D001", "title": "M-1 does not balance", "severity": "error",
             "condition": "income_per_return != schedule_k_line_18",
             "message": "Schedule M-1 line 8 does not equal Schedule K line 18 (or Schedule M-3 Part II line 26(d) when M-3 is filed). The reconciliation is incorrect. Note: line 8 does NOT have to equal page 1 line 22 — separately stated items differ."},
            {"diagnostic_id": "D002", "title": "M-1 Line 3 is negative", "severity": "error",
             "condition": "expenses_not_on_k < 0",
             "message": "M-1 line 3 (expenses on books not on the return) should be a POSITIVE add-back. A negative value here incorrectly reduces the reconciled income — line 3 adds the nondeductible portion (e.g., the section 274 meals disallowance)."},
            {"diagnostic_id": "D004", "title": "M-3 required at $10 million total assets", "severity": "error",
             "condition": "total_assets >= 10000000 AND m1_completed",
             "message": "Corporations with total assets of $10 million or more on the last day of the tax year must file Schedule M-3 (Form 1120-S) instead of Schedule M-1 (i1120s 2025 p.49)."},
            {"diagnostic_id": "D005", "title": "M-1 itemized components exceed their line total", "severity": "warning",
             "condition": "m1_3a_depreciation + m1_3b_travel_ent > expenses_not_on_k OR m1_5a_tax_exempt_interest > income_on_books_not_k OR m1_6a_depreciation > deductions_on_k_not_books",
             "message": "An itemized $ component (3a/3b, 5a, or 6a) exceeds its parent line total. The itemized amounts are components of lines 3, 5, and 6 — they cannot exceed the line they itemize."},
        ])

        self._upsert_tests(form, [
            {"scenario_name": "M-1 with meals nondeductible add-back",
             "scenario_type": "normal",
             "inputs": {"book_net_income": 85000, "income_on_k_not_books": 0,
                         "expenses_not_on_k": 5000, "m1_3b_travel_ent": 5000,
                         "income_on_books_not_k": 0, "deductions_on_k_not_books": 0},
             "expected_outputs": {"line_4_subtotal": 90000, "line_7_subtotal": 0, "income_per_return": 90000},
             "notes": "Book income $85K + $5K meals add-back (50% of $10K meals, itemized on 3b) = $90K on line 8 (= Schedule K line 18). Line 3 is POSITIVE.", "sort_order": 1},
            {"scenario_name": "M-1 with bonus depreciation difference",
             "scenario_type": "normal",
             "inputs": {"book_net_income": 120000, "income_on_k_not_books": 0,
                         "expenses_not_on_k": 2000, "m1_3b_travel_ent": 2000,
                         "income_on_books_not_k": 3000, "m1_5a_tax_exempt_interest": 3000,
                         "deductions_on_k_not_books": 50000, "m1_6a_depreciation": 50000},
             "expected_outputs": {"line_4_subtotal": 122000, "line_7_subtotal": 53000, "income_per_return": 69000},
             "notes": "Book income + meals add-back - tax-exempt interest - bonus depreciation excess (itemized 6a) = line 8.", "sort_order": 2},
            {"scenario_name": "M-1 with loss",
             "scenario_type": "edge",
             "inputs": {"book_net_income": -30000, "income_on_k_not_books": 5000,
                         "expenses_not_on_k": 1000, "m1_3b_travel_ent": 1000,
                         "income_on_books_not_k": 0, "deductions_on_k_not_books": 20000,
                         "m1_6a_depreciation": 20000},
             "expected_outputs": {"line_4_subtotal": -24000, "line_7_subtotal": 20000, "income_per_return": -44000},
             "notes": "Book loss scenario. M-1 still balances — large deductions on K not on books (bonus depreciation).", "sort_order": 3},
        ])

        _M1_SCENARIOS = {
            "M-1 with meals nondeductible add-back",
            "M-1 with bonus depreciation difference",
            "M-1 with loss",
        }
        stale_tests = TestScenario.objects.filter(tax_form=form).exclude(scenario_name__in=_M1_SCENARIOS)
        if stale_tests.exists():
            names = ", ".join(sorted(stale_tests.values_list("scenario_name", flat=True)))
            self.stdout.write(f"  deleting {stale_tests.count()} stale M-1 scenarios: {names}")
            stale_tests.delete()

        self._upsert_form_links("1120S_M1", sources, [
            ("IRS_2025_1120S_INSTR_FULL", "governs"),
        ])

        self.stdout.write(self.style.SUCCESS("  M-1 complete."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Schedule M-2 — Analysis of AAA, OAA, PTEP, and Shareholders' Equity
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_schedule_m2(self, sources):
        form = self._upsert_form(
            "1120S_M2",
            "Schedule M-2 — Analysis of AAA, Shareholders' Undistributed Taxable Income Previously Taxed, AE&P, and Other Adjustments Account",
            ["1120S"],
            notes="2025 face (rebuilt verbatim 2026-07-12): FOUR columns — (a) AAA, (b) PTEP, (c) AE&P, (d) OAA; rows 2/4 tie to page 1, LINE 22 (the prior block said line 21 and modeled only columns (a)/(d)). Distributions cannot reduce AAA below zero (measured WITHOUT the net negative adjustment); losses CAN make AAA negative.",
        )

        self._upsert_facts(form, [
            # Column (a) — AAA
            {"fact_key": "aaa_beginning", "label": "AAA balance at beginning of tax year (Line 1, col a)", "data_type": "decimal", "required": True, "sort_order": 1},
            {"fact_key": "aaa_ordinary_income", "label": "Ordinary income from page 1, line 22 (Line 2, col a)", "data_type": "decimal", "sort_order": 2,
             "notes": "From page 1 LINE 22 (2025 face) — only if positive."},
            {"fact_key": "aaa_other_additions", "label": "Other additions (Line 3, col a)", "data_type": "decimal", "sort_order": 3,
             "notes": "Separately stated income items other than tax-exempt income (e.g., Schedule K lines 4/5a portfolio income), and the depletion excess (i1120s 2025 p.50 adjustment 1)."},
            {"fact_key": "aaa_loss", "label": "Loss from page 1, line 22 (Line 4, col a)", "data_type": "decimal", "sort_order": 4,
             "notes": "From page 1 LINE 22 if a loss. Entered as a positive number (the face prints it in parentheses)."},
            {"fact_key": "aaa_other_reductions", "label": "Other reductions (Line 5, col a)", "data_type": "decimal", "sort_order": 5,
             "notes": "Separately stated losses/deductions, nondeductible expenses (other than those related to tax-exempt income), oil/gas depletion (i1120s 2025 p.50 adjustment 2)."},
            {"fact_key": "aaa_combined", "label": "Combine lines 1 through 5 (Line 6, col a)", "data_type": "decimal", "sort_order": 6},
            {"fact_key": "aaa_distributions", "label": "Distributions (Line 7, col a)", "data_type": "decimal", "sort_order": 7,
             "notes": "The amount CHARGED to AAA — cannot reduce AAA below zero, measured against the AAA determined WITHOUT regard to any net negative adjustment (i1120s 2025 pp.50-51). Excess distributions move down the section 1368 ordering (PTEP → AE&P → OAA → equity)."},
            {"fact_key": "aaa_ending", "label": "Balance at end of tax year (Line 8, col a = line 6 - line 7)", "data_type": "decimal", "sort_order": 8},
            # Column (b) — PTEP
            {"fact_key": "ptep_beginning", "label": "PTEP balance at beginning of tax year (Line 1, col b)", "data_type": "decimal", "sort_order": 9,
             "notes": "Shareholders' undistributed taxable income previously taxed — maintained only if a balance existed at the start of the 2025 tax year (pre-1983 section 1375(d) account)."},
            {"fact_key": "ptep_distributions", "label": "PTEP distributions (Line 7, col b)", "data_type": "decimal", "sort_order": 10,
             "notes": "The ONLY adjustment to PTEP: reductions for section 1375(d) (as in effect before 1983) distributions."},
            {"fact_key": "ptep_ending", "label": "PTEP balance at end of tax year (Line 8, col b)", "data_type": "decimal", "sort_order": 11},
            # Column (c) — AE&P
            {"fact_key": "aep_beginning", "label": "AE&P balance at beginning of tax year (Line 1, col c)", "data_type": "decimal", "sort_order": 12,
             "notes": "Accumulated earnings and profits from C-corporation years (or C-corp reorganizations); section 312. Its presence triggers excess-net-passive-income tax exposure (page 1 line 23a)."},
            {"fact_key": "aep_dividend_distributions", "label": "AE&P reductions — dividend distributions (Line 7, col c)", "data_type": "decimal", "sort_order": 13,
             "notes": "Dividend distributions from AE&P — reported to shareholders on Form 1099-DIV (Schedule K 17c), NEVER on the K-1 (i1120s 2025 p.40)."},
            {"fact_key": "aep_other_adjustments", "label": "AE&P other adjustments — redemptions/reorganizations/recapture", "data_type": "decimal", "sort_order": 14,
             "notes": "Section 1371(c)/(d)(3): adjustments for redemptions, liquidations, reorganizations, and investment credit recapture tax."},
            {"fact_key": "aep_ending", "label": "AE&P balance at end of tax year (Line 8, col c)", "data_type": "decimal", "sort_order": 15},
            # Column (d) — OAA
            {"fact_key": "oaa_beginning", "label": "OAA balance at beginning of tax year (Line 1, col d)", "data_type": "decimal", "sort_order": 16},
            {"fact_key": "oaa_additions", "label": "OAA other additions — tax-exempt income (Line 3, col d)", "data_type": "decimal", "sort_order": 17},
            {"fact_key": "oaa_reductions", "label": "OAA other reductions — related nondeductible expenses; C-year federal taxes (Line 5, col d)", "data_type": "decimal", "sort_order": 18},
            {"fact_key": "oaa_distributions", "label": "OAA distributions (Line 7, col d)", "data_type": "decimal", "sort_order": 19},
            {"fact_key": "oaa_ending", "label": "OAA balance at end of tax year (Line 8, col d)", "data_type": "decimal", "sort_order": 20},
            # Cross-column input
            {"fact_key": "total_distributions", "label": "Total distributions to shareholders during the year (Schedule K line 16d)", "data_type": "decimal", "sort_order": 21,
             "notes": "The section 1368 ordering allocates this across AAA → PTEP → AE&P → OAA → equity; amounts beyond the accounts are not entered on M-2."},
        ])

        # In-loader stale self-heal (retained_earnings_beginning was a Schedule L
        # item, never an M-2 face row).
        _M2_FACT_KEYS = {
            "aaa_beginning", "aaa_ordinary_income", "aaa_other_additions", "aaa_loss",
            "aaa_other_reductions", "aaa_combined", "aaa_distributions", "aaa_ending",
            "ptep_beginning", "ptep_distributions", "ptep_ending",
            "aep_beginning", "aep_dividend_distributions", "aep_other_adjustments", "aep_ending",
            "oaa_beginning", "oaa_additions", "oaa_reductions", "oaa_distributions", "oaa_ending",
            "total_distributions",
        }
        stale_facts = FormFact.objects.filter(tax_form=form).exclude(fact_key__in=_M2_FACT_KEYS)
        if stale_facts.exists():
            names = ", ".join(sorted(stale_facts.values_list("fact_key", flat=True)))
            self.stdout.write(f"  deleting {stale_facts.count()} stale M-2 facts: {names}")
            stale_facts.delete()

        rules = self._upsert_rules(form, [
            {"rule_id": "R001", "title": "AAA combine (Line 6)",
             "description": "AAA Line 6 = Line 1 + Line 2 + Line 3 - Line 4 - Line 5 (face: 'Combine lines 1 through 5'). Beginning balance plus page-1-line-22 income and other additions, minus the page-1-line-22 loss and other reductions.",
             "rule_type": "calculation",
             "formula": "aaa_beginning + aaa_ordinary_income + aaa_other_additions - aaa_loss - aaa_other_reductions",
             "inputs": ["aaa_beginning", "aaa_ordinary_income", "aaa_other_additions", "aaa_loss", "aaa_other_reductions"],
             "outputs": ["aaa_combined"], "precedence": 1, "sort_order": 1},
            {"rule_id": "R002", "title": "AAA line 7 distribution cap and ending balance (Line 8)",
             "description": "CORRECTED 2026-07-12 (tax-law fix, i1120s 2025 pp.50-51 verbatim + section 1368(e)): the distribution charge to AAA is limited to the AAA determined WITHOUT regard to any net negative adjustment for the tax year (but not below zero). Net negative adjustment = the excess of the p.50 adjustment-(2) decreases (losses/expenses, excluding distributions) over the adjustment-(1) increases. So: distribution cap = max(0, aaa_beginning + max(0, increases - decreases)); line 7 (col a) = min(total distributions, cap); line 8 = line 6 - line 7. The PRIOR formula capped the charge at max(0, line 6) — but line 6 INCLUDES the net negative adjustment, so in an NNA year with positive beginning AAA it UNDER-charges AAA (and leaves line 8 too high): e.g. beginning 10,000, increases 30,000, decreases 36,000, distributions 65,000 -> correct line 7 = 10,000 and line 8 = (6,000); the old formula charged only 4,000. Losses CAN still drive line 8 negative.",
             "rule_type": "calculation",
             "formula": "nna = max(0, (aaa_loss + aaa_other_reductions) - (aaa_ordinary_income + aaa_other_additions)); cap = max(0, aaa_beginning + max(0, (aaa_ordinary_income + aaa_other_additions) - (aaa_loss + aaa_other_reductions))); aaa_distributions = min(total_distributions_remaining, cap); aaa_ending = aaa_combined - aaa_distributions",
             "inputs": ["aaa_combined", "aaa_beginning", "aaa_ordinary_income", "aaa_other_additions", "aaa_loss", "aaa_other_reductions", "total_distributions"],
             "outputs": ["aaa_distributions", "aaa_ending"], "precedence": 2, "sort_order": 2,
             "notes": "Ken ratification pending (REVIEW_QUEUE s59): the old cap formula min(distributions, max(0, line 6)) matches the corrected one whenever there is NO net negative adjustment; with an NNA the corrected cap uses beginning-plus-net-positive only, per the published example and Reg. 1.1368-2."},
            {"rule_id": "R003", "title": "Distribution ordering — AAA, PTEP, AE&P, OAA, equity",
             "description": "General rule per i1120s (2025) p.51 verbatim: property distributions (including cash) are applied in order — 1. Reduce AAA (determined without regard to any net negative adjustment, not below zero; pro rata across distributions if exceeded); 2. Reduce shareholders' PTEP for section 1375(d) distributions; 3. Reduce AE&P (dividend distributions — 1099-DIV / Schedule K 17c); 4. Reduce OAA; 5. Reduce any remaining shareholders' equity accounts. Three shareholder-consent elections modify the order (section 1368(e)(3)(B), each irrevocable and per-tax-year): distribute AE&P first, deemed dividend, forego PTEP.",
             "rule_type": "conditional",
             "formula": "distributions -> AAA (capped, w/o NNA) -> PTEP (1375(d)) -> AE&P (dividends) -> OAA -> equity",
             "inputs": ["total_distributions", "aaa_combined", "ptep_beginning", "aep_beginning", "oaa_beginning"],
             "outputs": ["aaa_distributions", "ptep_distributions", "aep_dividend_distributions", "oaa_distributions"],
             "precedence": 3, "sort_order": 3},
            {"rule_id": "R004", "title": "OAA ending balance (column d)",
             "description": "OAA is adjusted for tax-exempt income (and related expenses) and federal taxes attributable to a C corporation tax year; after those adjustments it is reduced for distributions (i1120s 2025 p.51 verbatim). OAA ending = beginning + additions - reductions - distributions from OAA.",
             "rule_type": "calculation",
             "formula": "oaa_beginning + oaa_additions - oaa_reductions - oaa_distributions",
             "inputs": ["oaa_beginning", "oaa_additions", "oaa_reductions", "oaa_distributions"],
             "outputs": ["oaa_ending"], "precedence": 1, "sort_order": 4},
            {"rule_id": "R005", "title": "PTEP column (b) — beginning-balance-only account",
             "description": "Per i1120s (2025) p.50 verbatim: the PTEP account is maintained only if the corporation had a balance at the start of its 2025 tax year; NO adjustments are made except reductions for section 1375(d) (pre-1983) distributions. PTEP ending = beginning - 1375(d) distributions.",
             "rule_type": "calculation",
             "formula": "ptep_ending = ptep_beginning - ptep_distributions",
             "inputs": ["ptep_beginning", "ptep_distributions"], "outputs": ["ptep_ending"],
             "precedence": 1, "sort_order": 5},
            {"rule_id": "R006", "title": "AE&P column (c) — C-year earnings; three adjustments only",
             "description": "Per i1120s (2025) pp.50-51 verbatim: AE&P exists only from C-corporation years (or C-corp reorganizations); enter the close-of-prior-year AE&P on line 1 col (c). The ONLY adjustments: (a) reductions for dividend distributions, (b) adjustments for redemptions/liquidations/reorganizations, (c) reductions for investment credit recapture tax (section 1371(c)/(d)(3)). Dividend distributions from AE&P are reported on Form 1099-DIV and Schedule K 17c — never on the K-1. AE&P presence exposes the corporation to the excess-net-passive-income tax (page 1 line 23a).",
             "rule_type": "calculation",
             "formula": "aep_ending = aep_beginning - aep_dividend_distributions - aep_other_adjustments",
             "inputs": ["aep_beginning", "aep_dividend_distributions", "aep_other_adjustments"],
             "outputs": ["aep_ending"], "precedence": 1, "sort_order": 6},
            {"rule_id": "R007", "title": "M-2 lines 2/4 source = page 1, line 22",
             "description": "2025 face verbatim: line 2 'Ordinary income from page 1, line 22'; line 4 'Loss from page 1, line 22'. (The pre-renumber spec said line 21 — the Form 7205 insertion shifted OBI to line 22.)",
             "rule_type": "routing", "formula": "aaa_ordinary_income = max(0, page1_line22); aaa_loss = max(0, -page1_line22)",
             "inputs": ["page1_ordinary_business_income"], "outputs": ["aaa_ordinary_income", "aaa_loss"],
             "precedence": 0, "sort_order": 7},
        ])

        RuleAuthorityLink.objects.filter(form_rule__tax_form=form).delete()
        self._upsert_links(rules, sources, [
            ("R001", "IRS_2025_1120S_INSTR_FULL", "primary", "M-2 AAA computation (face rows 1-6)"),
            ("R001", "IRC_1368", "secondary", "Section 1368 — distributions from S corporations"),
            ("R002", "IRS_2025_1120S_INSTR_FULL", "primary", "AAA distribution cap measured WITHOUT the net negative adjustment (i1120s 2025 pp.50-51 + published example)"),
            ("R002", "IRC_1368", "primary", "Section 1368(e)(1)(C) — net negative adjustment excluded from the distribution base"),
            ("R003", "IRS_2025_1120S_INSTR_FULL", "primary", "Distribution ordering 1-5 + the three 1368(e)(3)(B) elections (i1120s 2025 p.51 verbatim)"),
            ("R003", "IRC_1368", "primary", "Section 1368(c) — distribution ordering"),
            ("R003", "IRC_1367", "secondary", "Section 1367 — adjustments to basis of shareholder stock"),
            ("R004", "IRS_2025_1120S_INSTR_FULL", "primary", "OAA: tax-exempt income, related expenses, C-year federal taxes (p.51 verbatim)"),
            ("R005", "IRS_2025_1120S_INSTR_FULL", "primary", "PTEP beginning-balance-only; 1375(d) reductions (p.50 verbatim)"),
            ("R006", "IRS_2025_1120S_INSTR_FULL", "primary", "AE&P three-adjustment rule; 1371(c)/(d)(3); 17c 1099-DIV tie (pp.50-51 verbatim)"),
            ("R007", "IRS_2025_1120S_INSTR_FULL", "primary", "M-2 lines 2/4 = page 1, line 22 (2025 face verbatim)"),
        ])

        self._upsert_lines(form, [
            {"line_number": "1", "description": "Balance at beginning of tax year", "line_type": "input", "sort_order": 1,
             "notes": "Four columns: (a) AAA, (b) PTEP, (c) AE&P, (d) OAA."},
            {"line_number": "2", "description": "Ordinary income from page 1, line 22", "line_type": "calculated", "source_rules": ["R007"], "sort_order": 2,
             "destination_form": "Page 1 Line 22"},
            {"line_number": "3", "description": "Other additions", "line_type": "input", "sort_order": 3},
            {"line_number": "4", "description": "Loss from page 1, line 22", "line_type": "calculated", "source_rules": ["R007"], "sort_order": 4},
            {"line_number": "5", "description": "Other reductions", "line_type": "input", "sort_order": 5,
             "notes": "Col (a): separately stated losses/deductions + nondeductible expenses (other than tax-exempt-related). Col (d): expenses related to tax-exempt income; C-year federal taxes."},
            {"line_number": "6", "description": "Combine lines 1 through 5", "line_type": "subtotal", "source_rules": ["R001"], "sort_order": 6},
            {"line_number": "7", "description": "Distributions", "line_type": "calculated", "source_rules": ["R002", "R003"], "sort_order": 7,
             "notes": "Per-column charge under the section 1368 ordering; col (a) capped at the AAA measured without the net negative adjustment."},
            {"line_number": "8", "description": "Balance at end of tax year. Subtract line 7 from line 6", "line_type": "total", "source_rules": ["R002"], "sort_order": 8,
             "notes": "AAA: distributions cannot reduce below zero; losses CAN make AAA negative."},
        ])

        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D001", "title": "Distributions exceed the AAA distribution base", "severity": "warning",
             "condition": "total_distributions > aaa_distribution_cap",
             "message": "Distributions exceed the AAA available for distributions (measured without regard to any net negative adjustment, floor zero). The excess moves down the section 1368 ordering: PTEP, then AE&P (taxable dividends on 1099-DIV), then OAA, then shareholders' equity."},
            {"diagnostic_id": "D002", "title": "AAA negative from losses", "severity": "info",
             "condition": "aaa_ending < 0",
             "message": "AAA ending balance is negative due to losses exceeding income. This is permitted — only distributions cannot make AAA negative, not losses (i1120s 2025 p.50 Tip; section 1368(e))."},
            {"diagnostic_id": "D003", "title": "PTEP activity without a beginning balance", "severity": "error",
             "condition": "(ptep_distributions != 0 OR ptep_ending != 0) AND ptep_beginning == 0",
             "message": "The PTEP account (column b) is maintained only if the corporation had a balance at the start of the tax year; no additions are ever made to it (i1120s 2025 p.50)."},
            {"diagnostic_id": "D004", "title": "AE&P driven below zero", "severity": "error",
             "condition": "aep_ending < 0",
             "message": "Accumulated earnings and profits cannot be reduced below zero — dividend distributions come from AE&P only to the extent it exists (sections 312/1371)."},
            {"diagnostic_id": "D005", "title": "M-2 line 7 columns exceed total distributions", "severity": "error",
             "condition": "aaa_distributions + ptep_distributions + aep_dividend_distributions + oaa_distributions > total_distributions",
             "message": "The per-column distribution charges on M-2 line 7 exceed the corporation's total distributions (Schedule K line 16d + 17c dividend distributions). Distributions beyond the accounts are simply not entered on M-2 — they cannot exceed what was distributed."},
        ])

        self._upsert_tests(form, [
            {"scenario_name": "Basic M-2 — income, additions, distributions within AAA",
             "scenario_type": "normal",
             "inputs": {"aaa_beginning": 50000, "aaa_ordinary_income": 95000,
                         "aaa_other_additions": 0, "aaa_loss": 0,
                         "aaa_other_reductions": 3000, "total_distributions": 40000},
             "expected_outputs": {"aaa_combined": 142000, "aaa_distributions": 40000, "aaa_ending": 102000},
             "notes": "No net negative adjustment (increases 95K > decreases 3K): cap = 50K + 92K = 142K; distributions 40K all charge AAA; ending 102K.", "sort_order": 1},
            {"scenario_name": "Distributions exceeding AAA — capped at zero",
             "scenario_type": "edge",
             "inputs": {"aaa_beginning": 20000, "aaa_ordinary_income": 30000,
                         "aaa_other_additions": 0, "aaa_loss": 0,
                         "aaa_other_reductions": 0, "total_distributions": 80000},
             "expected_outputs": {"aaa_combined": 50000, "aaa_distributions": 50000, "aaa_ending": 0},
             "notes": "Distributions ($80K) exceed the $50K cap (20K + 30K net positive). Line 7 col (a) = 50K, ending 0. The excess $30K moves down the 1368 ordering (no PTEP/AE&P/OAA here — return of basis / capital gain at the shareholder level).", "sort_order": 2},
            {"scenario_name": "Loss making AAA negative",
             "scenario_type": "edge",
             "inputs": {"aaa_beginning": 20000, "aaa_ordinary_income": 0,
                         "aaa_other_additions": 0, "aaa_loss": 50000,
                         "aaa_other_reductions": 0, "total_distributions": 0},
             "expected_outputs": {"aaa_combined": -30000, "aaa_distributions": 0, "aaa_ending": -30000},
             "notes": "Losses CAN make AAA negative (unlike distributions). AAA = 20K - 50K loss = -30K.", "sort_order": 3},
            {"scenario_name": "Published worksheet example — net negative adjustment blocks the AAA charge",
             "scenario_type": "normal",
             "inputs": {"aaa_beginning": 0, "aaa_ordinary_income": 10000,
                         "aaa_other_additions": 20000, "aaa_loss": 0,
                         "aaa_other_reductions": 36000, "total_distributions": 65000,
                         "oaa_beginning": 0, "oaa_additions": 5000, "oaa_reductions": 0,
                         "oaa_distributions": 5000},
             "expected_outputs": {"aaa_combined": -6000, "aaa_distributions": 0, "aaa_ending": -6000,
                                   "oaa_ending": 0},
             "notes": "i1120s (2025) pp.50-51 PUBLISHED example verbatim: increases 30,000 (line 2 10,000 + line 3 20,000 = K4 4,000 + K5a 16,000), decreases 36,000 (K2 loss 3,000 + 12a 24,000 + 12e 3,000 + 16c 6,000) -> net negative adjustment 6,000; the AAA distribution base (without the NNA, floor zero) is ZERO, so line 7 col (a) = -0- despite 65,000 distributed; line 8 = (6,000). OAA absorbs 5,000 (tax-exempt interest) and ends at -0-; the remaining 60,000 of distributions aren't entered on Schedule M-2. The OLD R002 formula (cap = max(0, line 6)) also yields 0 here — the divergence case is beginning AAA > 0 with an NNA: e.g. beginning 10,000, same year -> old cap max(0, 4,000) = 4,000 but correct cap = 10,000 (beginning + net positive 0), charging 10,000 not 4,000.", "sort_order": 4},
            {"scenario_name": "NNA with positive beginning AAA — corrected cap divergence pin",
             "scenario_type": "edge",
             "inputs": {"aaa_beginning": 10000, "aaa_ordinary_income": 10000,
                         "aaa_other_additions": 20000, "aaa_loss": 0,
                         "aaa_other_reductions": 36000, "total_distributions": 65000},
             "expected_outputs": {"aaa_combined": 4000, "aaa_distributions": 10000, "aaa_ending": -6000},
             "notes": "The R002-correction pin: increases 30,000, decreases 36,000 -> NNA 6,000. Cap = beginning 10,000 + max(0, 30,000-36,000) = 10,000 (section 1368(e)(1)(C): the distribution base ignores the net negative adjustment). Line 6 = 4,000; line 7 = 10,000 (NOT the old formula's 4,000); line 8 = (6,000) — the NNA lands after distributions per the p.50 adjustment order (4).", "sort_order": 5},
        ])

        _M2_SCENARIOS = {
            "Basic M-2 — income, additions, distributions within AAA",
            "Distributions exceeding AAA — capped at zero",
            "Loss making AAA negative",
            "Published worksheet example — net negative adjustment blocks the AAA charge",
            "NNA with positive beginning AAA — corrected cap divergence pin",
        }
        stale_tests = TestScenario.objects.filter(tax_form=form).exclude(scenario_name__in=_M2_SCENARIOS)
        if stale_tests.exists():
            names = ", ".join(sorted(stale_tests.values_list("scenario_name", flat=True)))
            self.stdout.write(
                "  deleting {} stale M-2 scenarios: {}".format(
                    stale_tests.count(), names.encode("ascii", "replace").decode("ascii")))
            stale_tests.delete()

        self._upsert_form_links("1120S_M2", sources, [
            ("IRS_2025_1120S_INSTR_FULL", "governs"),
            ("IRC_1368", "governs"),
            ("IRC_1367", "informs"),
        ])

        self.stdout.write(self.style.SUCCESS("  M-2 complete."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Expand Schedule K — add detailed flow-in rules for each line
    # ═══════════════════════════════════════════════════════════════════════════

    def _expand_schedule_k(self, sources):
        """Add expanded rules to the existing Schedule K form spec."""
        form = TaxForm.objects.filter(
            form_number="SCH_K_1120S", jurisdiction="FED", tax_year=2025,
        ).first()
        if not form:
            self.stdout.write(self.style.WARNING("SCH_K_1120S not found — run load_1120s_specs first"))
            return

        # Add new flow-in rules that document WHERE each K line comes from
        rules = self._upsert_rules(form, [
            {"rule_id": "R010", "title": "K Line 1 source: Page 1 Line 22",
             "description": "Schedule K Line 1 = Page 1 Line 22 (ordinary business income/loss; 2025 face — renumbered 2026-07-11, the prior text said line 21). This is the direct flow of the S-Corp's operating result to Schedule K for shareholder allocation.",
             "rule_type": "routing", "formula": "K1 = Page1_Line22",
             "inputs": ["page1_ordinary_income"], "outputs": ["K1"],
             "precedence": 1, "sort_order": 10},
            {"rule_id": "R011", "title": "K Line 4 = Interest income",
             "description": "Schedule K Line 4 is INTEREST INCOME (portfolio income). This is NOT Section 1231 gain. Interest income is separately stated because it is portfolio income under IRC 469.",
             "rule_type": "routing", "formula": "K4 = interest_income",
             "inputs": ["interest_income"], "outputs": ["K4"],
             "precedence": 1, "sort_order": 11,
             "notes": "IMPORTANT: K4 is NOT Section 1231. K9 is Section 1231. This was a source of confusion."},
            {"rule_id": "R012", "title": "K Line 5a/5b = Dividends",
             "description": "K Line 5a = ordinary dividends, K Line 5b = qualified dividends (subset of 5a). Portfolio income, separately stated. NOT capital gains.",
             "rule_type": "routing", "formula": "K5a = ordinary_dividends; K5b = qualified_dividends",
             "inputs": ["dividend_income", "qualified_dividends"], "outputs": ["K5a", "K5b"],
             "precedence": 1, "sort_order": 12},
            {"rule_id": "R013", "title": "K Line 7 source: Schedule D Part I Line 7",
             "description": "Schedule K Line 7 = net short-term capital gain (loss) from Schedule D Part I Line 7 (2025 face; renumbered 2026-07-08 — the prior text said line 5). This comes from Form 8949 capital asset transactions, NOT from Form 4797.",
             "rule_type": "routing", "formula": "K7 = ScheduleD_Part1_Line7",
             "inputs": ["schedule_d_net_short_term"], "outputs": ["K7"],
             "precedence": 1, "sort_order": 13},
            {"rule_id": "R014", "title": "K Line 8a source: Schedule D Part II Line 15",
             "description": "Schedule K Line 8a = net long-term capital gain (loss) from Schedule D Part II Line 15 (2025 face; renumbered 2026-07-08 — the prior text said line 12). From Form 8949 capital asset transactions, NOT from Form 4797.",
             "rule_type": "routing", "formula": "K8a = ScheduleD_Part2_Line15",
             "inputs": ["schedule_d_net_long_term"], "outputs": ["K8a"],
             "precedence": 1, "sort_order": 14},
            {"rule_id": "R015", "title": "K Line 9 source: Form 4797 Part I Line 7",
             "description": "Schedule K Line 9 = net section 1231 gain (loss) from Form 4797 Part I Line 7. Section 1231 transactions BYPASS Schedule D on the 1120-S and flow directly to K Line 9. This is a key architectural difference from the 1040.",
             "rule_type": "routing", "formula": "K9 = Form4797_Part1_Line7",
             "inputs": ["form_4797_net_1231"], "outputs": ["K9"],
             "precedence": 1, "sort_order": 15,
             "notes": "VERIFIED: 4797 Part I -> K9 directly. Does NOT go through Schedule D on 1120-S."},
            {"rule_id": "R016", "title": "K Line 16c = Nondeductible meals & entertainment",
             "description": "K Line 16c (nondeductible expenses) includes the nondeductible portion from the Page 1 R010 meals worksheet: 50% of standard business meals + 20% of DOT hours-of-service meals + 100% of entertainment (the 100% exception-category tier contributes nothing). This amount also flows to M-1 Line 3b as an add-back and to M-2 as a reduction to AAA.",
             "rule_type": "routing", "formula": "K16c = meals_nondeductible_total + other_nondeductible",
             "inputs": ["nondeductible_expenses"], "outputs": ["K16c"],
             "precedence": 1, "sort_order": 16},
            {"rule_id": "R017", "title": "K Line 16d = Total distributions",
             "description": "K Line 16d = total distributions (property and cash) to shareholders. This amount flows to M-2 Line 7 and to each shareholder's K-1.",
             "rule_type": "routing", "formula": "K16d = total_distributions",
             "inputs": ["total_distributions"], "outputs": ["K16d"],
             "precedence": 1, "sort_order": 17},
            {"rule_id": "R018", "title": "K Line 18 = Income/loss reconciliation",
             "description": "Schedule K Line 18 combines lines 1-10 and subtracts lines 11-12e and 16f (2025 face verbatim). Per i1120s (2025) p.49 it must equal Schedule M-1 line 8 (or M-3 Part II line 26(d)). CORRECTED 2026-07-11: the prior text said K18 should equal Page 1 Line 21 — WRONG; separately stated items (rental, portfolio, capital gains, 179, charitable, 16f) make K18 differ from page-1 ordinary income.",
             "rule_type": "validation", "formula": "K18 = sum(K1..K10) - sum(K11..K12e) - K16f = M1_Line8",
             "inputs": ["K1_through_K10_net"], "outputs": ["K18"],
             "precedence": 50, "sort_order": 18},
        ])

        self._upsert_links(rules, sources, [
            ("R010", "IRS_2025_1120S_INSTR_FULL", "primary", "K1 = Page 1 Line 22 (2025 face)"),
            ("R011", "IRS_2025_1120S_INSTR_FULL", "primary", "K4 = interest income (portfolio)"),
            ("R012", "IRS_2025_1120S_INSTR_FULL", "primary", "K5a/5b = dividends"),
            ("R013", "IRS_2025_1120S_SCHD_INSTR_FULL", "primary", "Schedule D Part I Line 7 -> K7 (2025 face)"),
            ("R014", "IRS_2025_1120S_SCHD_INSTR_FULL", "primary", "Schedule D Part II Line 15 -> K8a (2025 face)"),
            ("R015", "IRS_2025_1120S_INSTR_FULL", "primary", "K9 = Form 4797 Part I Line 7 (verified)"),
            ("R015", "IRS_2025_4797_INSTR", "secondary", "4797 bypasses Schedule D on 1120-S"),
            ("R016", "IRS_2025_1120S_INSTR_FULL", "primary", "K16c = nondeductible expenses"),
            ("R017", "IRS_2025_1120S_INSTR_FULL", "primary", "K16d = distributions"),
            ("R017", "IRC_1368", "secondary", "Section 1368 distribution rules"),
            ("R018", "IRS_2025_1120S_INSTR_FULL", "primary", "K18 must equal M-1 line 8 (i1120s 2025 p.49)"),
        ])

        # Add K-1 box mapping lines
        self._upsert_lines(form, [
            {"line_number": "K1->Box1", "description": "K Line 1 -> K-1 Box 1: Ordinary business income (loss)", "line_type": "informational", "destination_form": "K-1 Box 1", "sort_order": 100},
            {"line_number": "K2->Box2", "description": "K Line 2 -> K-1 Box 2: Net rental real estate income (loss)", "line_type": "informational", "destination_form": "K-1 Box 2", "sort_order": 101},
            {"line_number": "K3->Box3", "description": "K Line 3c -> K-1 Box 3: Other net rental income (loss)", "line_type": "informational", "destination_form": "K-1 Box 3", "sort_order": 102},
            {"line_number": "K4->Box4", "description": "K Line 4 -> K-1 Box 4: Interest income", "line_type": "informational", "destination_form": "K-1 Box 4", "sort_order": 103},
            {"line_number": "K5->Box5", "description": "K Line 5a/5b -> K-1 Box 5a/5b: Dividends", "line_type": "informational", "destination_form": "K-1 Box 5", "sort_order": 104},
            {"line_number": "K6->Box6", "description": "K Line 6 -> K-1 Box 6: Royalties", "line_type": "informational", "destination_form": "K-1 Box 6", "sort_order": 105},
            {"line_number": "K7->Box7", "description": "K Line 7 -> K-1 Box 7: Net short-term capital gain (loss)", "line_type": "informational", "destination_form": "K-1 Box 7", "sort_order": 106},
            {"line_number": "K8->Box8", "description": "K Line 8a/8b/8c -> K-1 Box 8a/8b/8c: Long-term capital gain, collectibles, unrec 1250", "line_type": "informational", "destination_form": "K-1 Box 8", "sort_order": 107},
            {"line_number": "K9->Box9", "description": "K Line 9 -> K-1 Box 9: Net section 1231 gain (loss)", "line_type": "informational", "destination_form": "K-1 Box 9", "sort_order": 108},
            {"line_number": "K10->Box10", "description": "K Line 10 -> K-1 Box 10: Other income (loss)", "line_type": "informational", "destination_form": "K-1 Box 10", "sort_order": 109},
            {"line_number": "K11->Box11", "description": "K Line 11 -> K-1 Box 11: Section 179 deduction", "line_type": "informational", "destination_form": "K-1 Box 11", "sort_order": 110},
            {"line_number": "K12->Box12", "description": "K Line 12a-e -> K-1 Box 12: Deductions", "line_type": "informational", "destination_form": "K-1 Box 12", "sort_order": 111},
            {"line_number": "K13->Box13", "description": "K Line 13a-g -> K-1 Box 13: Credits", "line_type": "informational", "destination_form": "K-1 Box 13", "sort_order": 112},
            {"line_number": "K16->Box16", "description": "K Line 16a-f -> K-1 Box 16: Items affecting shareholder basis", "line_type": "informational", "destination_form": "K-1 Box 16", "sort_order": 113},
            {"line_number": "K17->Box17", "description": "K Line 17a-d -> K-1 Box 17: Other information (QBI, etc.)", "line_type": "informational", "destination_form": "K-1 Box 17", "sort_order": 114},
        ])

        self.stdout.write(self.style.SUCCESS("  Schedule K expanded."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Schedule D — Add flow verification rules
    # ═══════════════════════════════════════════════════════════════════════════

    def _add_schedule_d_flow_rules(self, sources):
        """Add flow-out rules to existing Schedule D spec."""
        form = TaxForm.objects.filter(
            form_number="SCHD_1120S", jurisdiction="FED", tax_year=2025,
        ).first()
        if not form:
            self.stdout.write(self.style.WARNING("SCHD_1120S not found — run load_1120s_specs first"))
            return

        rules = self._upsert_rules(form, [
            {"rule_id": "R010", "title": "Schedule D does NOT include Section 1231",
             "description": "Section 1231 gains/losses from Form 4797 are reported on Schedule K Line 9 directly. They do NOT flow through Schedule D on the 1120-S. Schedule D handles only capital asset transactions (stocks, bonds, etc.) through Form 8949.",
             "rule_type": "validation",
             "formula": "schedule_d does NOT include 4797_section_1231",
             "inputs": [], "outputs": [],
             "precedence": 0, "sort_order": 10,
             "notes": "VERIFIED from fresh IRS instructions. 4797 bypasses Schedule D on 1120-S. This is different from 1040 where Section 1231 gains treated as capital gains DO flow to Schedule D."},
            {"rule_id": "R011", "title": "Part I Line 7 -> K Line 7",
             "description": "Schedule D Part I Line 7 (net short-term capital gain or loss — combine lines 1a through 6) flows to Form 1120-S Schedule K, line 7 or 10. (Renumbered 2026-07-08 to the 2025 face; the prior text said line 5.)",
             "rule_type": "routing", "formula": "K7 = ScheduleD_Part1_Line7",
             "inputs": ["net_short_term_gain_loss"], "outputs": ["K_line_7"],
             "precedence": 1, "sort_order": 11},
            {"rule_id": "R012", "title": "Part II Line 15 -> K Line 8a",
             "description": "Schedule D Part II Line 15 (net long-term capital gain or loss — combine lines 8a through 14) flows to Form 1120-S Schedule K, line 8a or 10. (Renumbered 2026-07-08 to the 2025 face; the prior text said line 12.)",
             "rule_type": "routing", "formula": "K8a = ScheduleD_Part2_Line15",
             "inputs": ["net_long_term_gain_loss"], "outputs": ["K_line_8a"],
             "precedence": 1, "sort_order": 12},
        ])

        self._upsert_links(rules, sources, [
            ("R010", "IRS_2025_1120S_SCHD_INSTR_FULL", "primary", "Schedule D does NOT include Section 1231"),
            ("R010", "IRS_2025_1120S_INSTR_FULL", "secondary", "4797 -> K9 directly, bypasses Schedule D"),
            ("R011", "IRS_2025_1120S_SCHD_INSTR_FULL", "primary", "Part I Line 5 -> K Line 7"),
            ("R012", "IRS_2025_1120S_SCHD_INSTR_FULL", "primary", "Part II Line 12 -> K Line 8a"),
        ])

        self.stdout.write(self.style.SUCCESS("  Schedule D flow rules added."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Cross-form diagnostics
    # ═══════════════════════════════════════════════════════════════════════════

    def _add_cross_form_diagnostics(self, sources):
        """Add cross-form diagnostics to existing Schedule K spec."""
        form = TaxForm.objects.filter(
            form_number="SCH_K_1120S", jurisdiction="FED", tax_year=2025,
        ).first()
        if not form:
            return

        self._upsert_diagnostics(form, [
            {"diagnostic_id": "D010", "title": "Section 1231 double-count check",
             "severity": "error",
             "condition": "K4 contains section_1231_gain AND K9 contains section_1231_gain",
             "message": "Section 1231 gain appears on both K Line 4 (interest income) and K Line 9 (net section 1231). K Line 4 is for INTEREST INCOME, not Section 1231. Verify that 1231 gain is only on K Line 9."},
            {"diagnostic_id": "D011", "title": "Page 1 Line 4 source verification",
             "severity": "warning",
             "condition": "page1_line4 != form_4797_part2_line17",
             "message": "Page 1 Line 4 does not match Form 4797 Part II Line 17. Line 4 should equal the ordinary gain/loss from 4797 Part II, NOT the Section 1231 gain from Part I."},
            {"diagnostic_id": "D012", "title": "K18 does not equal M-1 line 8",
             "severity": "error",
             "condition": "K18 != m1_line_8",
             "message": "Schedule K line 18 (income/loss reconciliation: lines 1-10 minus 11-12e and 16f) does not equal Schedule M-1 line 8 (or M-3 Part II line 26(d)). These must match per i1120s (2025) p.49. Note: K18 does NOT have to equal Page 1 line 22 — separately stated items differ."},
            {"diagnostic_id": "D013", "title": "Schedule D Section 1231 contamination",
             "severity": "error",
             "condition": "schedule_d includes section_1231_amounts",
             "message": "Section 1231 amounts appear on Schedule D. On the 1120-S, Section 1231 goes directly to K Line 9 from Form 4797 Part I Line 7, NOT through Schedule D."},
            {"diagnostic_id": "D014", "title": "Schedule D totals vs 8949",
             "severity": "warning",
             "condition": "schedule_d_totals != form_8949_category_totals",
             "message": "Schedule D totals do not match Form 8949 category totals. Verify all 8949 transactions are correctly categorized (A-F) and totaled on Schedule D."},
        ])

        self.stdout.write(self.style.SUCCESS("  Cross-form diagnostics added."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Cross-form test scenarios
    # ═══════════════════════════════════════════════════════════════════════════

    def _add_cross_form_tests(self, sources):
        """Add end-to-end test scenarios to the Page 1 spec."""
        form = TaxForm.objects.filter(
            form_number="1120S_PAGE1", jurisdiction="FED", tax_year=2025,
        ).first()
        if not form:
            return

        self._upsert_tests(form, [
            {"scenario_name": "S-Corp with disposed equipment — 4797 recapture + 1231 flow",
             "scenario_type": "normal",
             "inputs": {
                 "gross_receipts": 400000, "returns_allowances": 0, "cost_of_goods_sold": 150000,
                 "other_income": 0,
                 "officer_compensation": 60000, "salaries_wages": 40000, "depreciation": 20000,
                 "other_deductions": 10000,
                 "form_4797_part2_line17": 15000,
                 "form_4797_part1_line7": 8000,
             },
             "expected_outputs": {
                 "net_gain_4797": 15000,
                 "total_income": 265000,
                 "ordinary_business_income": 135000,
                 "K1": 135000,
                 "K9": 8000,
                 "page1_line4": 15000,
             },
             "notes": "4797 Part II L17 ($15K recapture) -> Page 1 Line 4. 4797 Part I L7 ($8K Section 1231) -> K Line 9 directly. These are DIFFERENT flows.", "sort_order": 10},
            {"scenario_name": "S-Corp with M&E limitation — meals nondeductible flow",
             "scenario_type": "normal",
             "inputs": {
                 "gross_receipts": 300000, "cost_of_goods_sold": 100000,
                 "officer_compensation": 50000, "salaries_wages": 30000,
                 "other_deductions": 25000,
                 "meals_50pct": 10000,
             },
             "expected_outputs": {
                 "meals_deductible_total": 5000,
                 "meals_nondeductible_total": 5000,
                 "ordinary_business_income": 90000,
                 "K16c": 5000,
                 "M1_line_3b": 5000,
             },
             "notes": "$10K standard business meals (R009 50% tier), only $5K deductible — a component of line 20 other deductions (25,000 + 5,000 = 30,000; line 21 = 110,000; line 22 OBI = 90,000). $5K nondeductible -> K16c and M-1 line 3b (positive ADD-BACK, R010). Re-keyed 2026-07-12 to the R009 worksheet facts (the old meals_total_on_books/meals_deductible_50pct keys predated the s41 four-tier unit).", "sort_order": 11},
            {"scenario_name": "Short-term capital gain — Schedule D to K Line 7",
             "scenario_type": "normal",
             "inputs": {
                 "form_8949_box_A_gain": 5000,
                 "form_8949_box_B_gain": 0,
                 "form_8949_box_C_gain": 0,
             },
             "expected_outputs": {
                 "schedule_d_part1_line5": 5000,
                 "K7": 5000,
             },
             "notes": "Short-term gain from 8949 -> Schedule D Part I Line 5 -> K Line 7. NOT K5a (that's dividends).", "sort_order": 12},
            {"scenario_name": "Long-term capital gain — Schedule D to K Line 8a",
             "scenario_type": "normal",
             "inputs": {
                 "form_8949_box_D_gain": 12000,
                 "form_8949_box_E_gain": 0,
                 "form_8949_box_F_gain": 3000,
             },
             "expected_outputs": {
                 "schedule_d_part2_line12": 15000,
                 "K8a": 15000,
             },
             "notes": "Long-term gain from 8949 -> Schedule D Part II Line 12 -> K Line 8a. NOT K5b (that's qualified dividends).", "sort_order": 13},
            {"scenario_name": "Section 1231 from 4797 bypasses Schedule D",
             "scenario_type": "normal",
             "inputs": {
                 "form_4797_part1_line7": 20000,
                 "schedule_d_part2_line12": 0,
             },
             "expected_outputs": {
                 "K9": 20000,
                 "K8a": 0,
                 "schedule_d_includes_1231": False,
             },
             "notes": "Section 1231 gain from 4797 goes to K9 directly. Schedule D is NOT involved. This is a key 1120-S vs 1040 difference.", "sort_order": 14},
            {"scenario_name": "Distributions exceeding AAA — M-2 floor at zero",
             "scenario_type": "edge",
             "inputs": {
                 "ordinary_business_income": 50000,
                 "aaa_beginning": 30000,
                 "total_distributions": 100000,
             },
             "expected_outputs": {
                 "aaa_combined": 80000,
                 "aaa_ending": 0,
                 "excess_distribution": 20000,
             },
             "notes": "AAA = 30K + 50K income = 80K combined. Distributions of $100K: first $80K from AAA (reduces to zero), then $20K is return of basis/capital gain per section 1368.", "sort_order": 15},
        ])

        # PAGE1 scenario whitelist: the base-block set + the cross-form set above.
        _PAGE1_SCENARIOS = {
            "Basic S-Corp — ordinary income only",
            "S-Corp with 4797 gain flowing to Page 1 Line 4",
            "M&E four-tier worksheet — deductible/nondeductible split",
            "Tax and payments — BIG tax, overpayment split 28a/28b",
            "Tax and payments — amount owed",
            "Line 19 Form 7205 deduction in total deductions",
            "S-Corp with disposed equipment — 4797 recapture + 1231 flow",
            "S-Corp with M&E limitation — meals nondeductible flow",
            "Short-term capital gain — Schedule D to K Line 7",
            "Long-term capital gain — Schedule D to K Line 8a",
            "Section 1231 from 4797 bypasses Schedule D",
            "Distributions exceeding AAA — M-2 floor at zero",
        }
        stale_tests = TestScenario.objects.filter(tax_form=form).exclude(scenario_name__in=_PAGE1_SCENARIOS)
        if stale_tests.exists():
            names = ", ".join(sorted(stale_tests.values_list("scenario_name", flat=True)))
            self.stdout.write(
                "  deleting {} stale PAGE1 scenarios: {}".format(
                    stale_tests.count(), names.encode("ascii", "replace").decode("ascii")))
            stale_tests.delete()

        self.stdout.write(self.style.SUCCESS("  Cross-form test scenarios added."))

    # ═══════════════════════════════════════════════════════════════════════════
    # Report
    # ═══════════════════════════════════════════════════════════════════════════

    def _report_totals(self):
        def _safe(text):
            return text.encode("ascii", errors="replace").decode("ascii")

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("DATABASE TOTALS (after load_1120s_full)")
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
        self.stdout.write(self.style.SUCCESS("1120-S full specs loaded successfully."))
