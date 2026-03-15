"""IRS form instruction sources for the 1120 (C-Corporation) family."""

from sources.federal_data.forms_1120s import _instr


SOURCES_1120 = [
    # ───────────────────────────────────────────────────────────────────────
    # Form 1120 Instructions
    # ───────────────────────────────────────────────────────────────────────
    _instr(
        "IRS_2025_1120_INSTR",
        "Instructions for Form 1120 — U.S. Corporation Income Tax Return",
        "Form 1120 Instructions (2025)",
        "https://www.irs.gov/instructions/i1120",
        "1120",
        excerpts=[
            {
                "excerpt_label": "Who must file",
                "location_reference": "General Instructions — Who Must File",
                "excerpt_text": (
                    "Unless exempt under §501, all domestic corporations (including corporations in "
                    "bankruptcy) must file an income tax return whether or not they have taxable "
                    "income. A corporation that has dissolved must file a return for the short period "
                    "ending on the date of dissolution. S corporations file Form 1120-S instead. "
                    "Due date: 15th day of the 4th month after end of tax year (April 15 for "
                    "calendar year corporations). A corporation with total assets of $10 million or "
                    "more must file Schedule M-3 instead of Schedule M-1."
                ),
                "summary_text": "All domestic C-Corps file 1120 unless exempt. Due April 15 (calendar year). M-3 required if assets ≥ $10M.",
                "is_key_excerpt": True,
                "topic_tags": ["c_corporation", "form_1120"],
            },
            {
                "excerpt_label": "Income section",
                "location_reference": "Line Instructions — Income",
                "excerpt_text": (
                    "Line 1a: Gross receipts or sales. Line 2: Cost of goods sold (Form 1125-A). "
                    "Line 3: Gross profit. Line 4: Dividends (Schedule C). Line 5: Interest. "
                    "Line 6: Gross rents. Line 7: Gross royalties. Line 8: Capital gain net income "
                    "(Schedule D). Corporations cannot use capital losses to offset ordinary income — "
                    "capital losses only offset capital gains. Line 9: Net gain or loss from Form "
                    "4797. Line 10: Other income. Line 11: Total income."
                ),
                "summary_text": "Income: receipts, COGS, dividends (Sch C), interest, rents, royalties, cap gains (Sch D), 4797 gains.",
                "is_key_excerpt": True,
                "topic_tags": ["form_1120", "c_corporation"],
            },
            {
                "excerpt_label": "Deductions section",
                "location_reference": "Line Instructions — Deductions",
                "excerpt_text": (
                    "Line 12: Compensation of officers (Form 1125-E if total receipts ≥ $500K). "
                    "Line 13: Salaries and wages (less employment credits). Line 14: Repairs and "
                    "maintenance. Line 15: Bad debts. Line 16: Rents. Line 17: Taxes and licenses. "
                    "Line 18: Interest (subject to §163(j) — use Form 8990). Line 19: Charitable "
                    "contributions (limited to 10% of taxable income computed without the contribution "
                    "deduction, NOL carryback, DRD, and certain other items). Line 20: Depreciation "
                    "(Form 4562). Line 21: Depletion. Line 22: Advertising. Line 23: Pension, "
                    "profit-sharing, etc. Line 24: Employee benefit programs. Line 25: Reserved. "
                    "Line 26: Other deductions. Line 27: Total deductions. Line 28: Taxable income "
                    "before NOL and special deductions."
                ),
                "summary_text": "Deductions: officer comp, wages, interest (§163(j)), charitable (10% limit), depreciation, benefits.",
                "is_key_excerpt": True,
                "topic_tags": ["form_1120", "c_corporation"],
            },
            {
                "excerpt_label": "Tax computation — Schedule J",
                "location_reference": "Schedule J Instructions",
                "excerpt_text": (
                    "Schedule J computes the corporation's tax. Line 2: Income tax — 21% of taxable "
                    "income (flat rate, all brackets eliminated by TCJA). Line 5b: General business "
                    "credit (Form 3800). Line 5c: Credit for prior year minimum tax (Form 8827). "
                    "Line 7: Total tax after credits. Line 8-15: Payments — estimated tax payments, "
                    "extensions, amounts applied from prior year overpayment, backup withholding, "
                    "other credits. Estimated tax: required if expected tax liability is $500 or more. "
                    "Pay in four installments: 4/15, 6/15, 9/15, 12/15."
                ),
                "summary_text": "Schedule J: 21% flat rate. Credits (Form 3800). Estimated tax required if ≥ $500.",
                "is_key_excerpt": True,
                "topic_tags": ["corporate_tax", "form_1120", "estimated_tax"],
            },
            {
                "excerpt_label": "Schedule C — Dividends, Inclusions, and Special Deductions",
                "location_reference": "Schedule C Instructions",
                "excerpt_text": (
                    "Schedule C computes the dividends received deduction (DRD). Column (a): "
                    "dividends received. Column (b): applicable percentage. Column (c): deduction. "
                    "DRD percentages: 50% for <20% ownership, 65% for 20%-79% ownership, 100% for "
                    "80%+ ownership (affiliated group). Special rules: the 50% and 65% DRDs are "
                    "limited to the corresponding percentage of taxable income (computed without the "
                    "DRD, NOL deduction, and certain other items). This limitation does not apply if "
                    "the DRD creates or increases a net operating loss."
                ),
                "summary_text": "Schedule C: DRD — 50%/65%/100% based on ownership. Taxable income limitation unless creates NOL.",
                "is_key_excerpt": True,
                "topic_tags": ["dividends_received", "c_corporation"],
            },
            {
                "excerpt_label": "Schedule M-1/M-2 — Reconciliation",
                "location_reference": "Schedule M-1/M-2 Instructions",
                "excerpt_text": (
                    "Schedule M-1: Reconciliation of Income (Loss) per Books With Income per Return. "
                    "Common book-to-tax differences: federal income tax per books (add back — not "
                    "deductible), excess of capital losses over capital gains (add back), meals "
                    "(50% nondeductible portion), tax penalties, depreciation differences, "
                    "tax-exempt interest (subtract). Schedule M-2: Analysis of Unappropriated "
                    "Retained Earnings per Books. Tracks beginning balance + net income per books "
                    "- distributions + other increases - other decreases = ending balance."
                ),
                "summary_text": "M-1: book-tax reconciliation (federal tax, meals, depreciation differences). M-2: retained earnings.",
                "is_key_excerpt": True,
                "topic_tags": ["form_1120", "c_corporation"],
            },
        ],
        topics=["form_1120", "c_corporation", "corporate_tax"],
        form_links=[{"form_code": "1120", "link_type": "governs"}],
    ),

    # ───────────────────────────────────────────────────────────────────────
    # Form 1120-H Instructions
    # ───────────────────────────────────────────────────────────────────────
    _instr(
        "IRS_2025_1120H_INSTR",
        "Instructions for Form 1120-H — U.S. Income Tax Return for Homeowners Associations",
        "Form 1120-H Instructions (2025)",
        "https://www.irs.gov/instructions/i1120h",
        "1120H",
        excerpts=[
            {
                "excerpt_label": "Who qualifies and election requirements",
                "location_reference": "General Instructions",
                "excerpt_text": (
                    "A homeowners association (as defined in §528) can elect to file Form 1120-H "
                    "and be taxed on only its nonexempt function income. To qualify: (1) it must be "
                    "organized and operated primarily for the acquisition, construction, management, "
                    "maintenance, and care of association property; (2) at least 60% of its gross "
                    "income must consist of amounts received as membership dues, fees, or assessments "
                    "from owners of residential units or lots (exempt function income); (3) at least "
                    "90% of its expenditures must be for the acquisition, construction, management, "
                    "maintenance, and care of association property; (4) no part of its net earnings "
                    "may inure to the benefit of any private shareholder or individual. The election "
                    "is made simply by filing Form 1120-H — no separate election statement is needed. "
                    "The election applies only for that tax year."
                ),
                "summary_text": "HOA files 1120-H if: 60% income from member dues, 90% expenses for common areas, no private benefit.",
                "is_key_excerpt": True,
                "topic_tags": ["homeowners_association", "form_1120h"],
            },
            {
                "excerpt_label": "Exempt function income and taxable income",
                "location_reference": "Line Instructions",
                "excerpt_text": (
                    "Exempt function income: membership dues, fees, and assessments received from "
                    "owners of residential units or lots. This income is excluded from gross income "
                    "under §528. Taxable income: all other income — interest on investments, rental "
                    "income from non-members, income from use of facilities by non-members, capital "
                    "gains. Taxable income is taxed at a flat rate of 30% for homeowners associations "
                    "or 32% for timeshare associations. A specific deduction of $100 is allowed. "
                    "The only deductions allowed against taxable income are expenses directly connected "
                    "with the production of that taxable income — no deductions are allowed against "
                    "exempt function income."
                ),
                "summary_text": "Exempt function income (dues) excluded. Taxable income (interest, rent) at 30% (32% timeshare). $100 deduction.",
                "is_key_excerpt": True,
                "topic_tags": ["homeowners_association", "form_1120h"],
            },
        ],
        topics=["form_1120h", "homeowners_association"],
        form_links=[{"form_code": "1120H", "link_type": "governs"}],
    ),

    # ───────────────────────────────────────────────────────────────────────
    # Form 1125-A Instructions
    # ───────────────────────────────────────────────────────────────────────
    _instr(
        "IRS_2025_1125A_INSTR",
        "Instructions for Form 1125-A — Cost of Goods Sold",
        "Form 1125-A Instructions (2025)",
        "https://www.irs.gov/instructions/i1125a",
        "shared",
        excerpts=[
            {
                "excerpt_label": "Who must file",
                "location_reference": "General Instructions",
                "excerpt_text": (
                    "Form 1125-A is used by business return filers (Form 1120, 1120-C, 1120-F, "
                    "1120S, 1065, etc.) to calculate and report the cost of goods sold. An entity "
                    "must complete Form 1125-A if it reports a deduction for cost of goods sold on "
                    "its return. Cost of goods sold applies to businesses that produce, purchase, or "
                    "sell merchandise as an income-producing factor."
                ),
                "summary_text": "File 1125-A if claiming COGS deduction. For all entity types that sell/produce merchandise.",
                "is_key_excerpt": True,
                "topic_tags": ["cost_of_goods_sold"],
            },
            {
                "excerpt_label": "Inventory methods and computation",
                "location_reference": "Line Instructions",
                "excerpt_text": (
                    "Line 1: Inventory at beginning of year. Line 2: Purchases. Line 3: Cost of "
                    "labor. Line 4: Additional §263A costs (UNICAP). Line 5: Other costs. Line 6: "
                    "Total (add lines 1-5). Line 7: Inventory at end of year. Line 8: Cost of goods "
                    "sold (line 6 minus line 7). Inventory valuation methods: (a) cost, (b) lower "
                    "of cost or market, (c) other (attach explanation). Identification methods: "
                    "(a) FIFO, (b) LIFO (requires Form 970 for election year), (c) other. If LIFO "
                    "is elected, the LIFO value must be used for financial reporting as well "
                    "(conformity requirement). Do not use the cash method for inventories."
                ),
                "summary_text": "COGS = beginning inventory + purchases + labor + §263A costs - ending inventory. FIFO/LIFO/cost-or-market.",
                "is_key_excerpt": True,
                "topic_tags": ["cost_of_goods_sold"],
            },
            {
                "excerpt_label": "§263A Uniform Capitalization (UNICAP)",
                "location_reference": "Line 4 Instructions",
                "excerpt_text": (
                    "Section 263A generally requires producers and resellers to capitalize certain "
                    "costs to inventory that might otherwise be currently deductible. Additional "
                    "§263A costs on line 4 include: indirect costs required to be capitalized such "
                    "as rent, utilities, indirect labor, officers' salaries allocable to production, "
                    "depreciation on production equipment, and other indirect production costs. "
                    "Small business exception: taxpayers with average annual gross receipts of "
                    "$30 million or less for the 3 preceding tax years are exempt from §263A. "
                    "The simplified production method and simplified resale method are available "
                    "as alternatives to specific identification of additional costs."
                ),
                "summary_text": "§263A UNICAP: capitalize indirect costs to inventory. Exempt if ≤ $30M avg gross receipts.",
                "is_key_excerpt": True,
                "topic_tags": ["unicap", "cost_of_goods_sold"],
            },
        ],
        topics=["cost_of_goods_sold", "unicap"],
        form_links=[
            {"form_code": "1125A", "link_type": "governs"},
            {"form_code": "1120", "link_type": "informs", "note": "COGS flows to Form 1120 line 2"},
            {"form_code": "1120S", "link_type": "informs", "note": "COGS flows to Form 1120-S line 2"},
            {"form_code": "1065", "link_type": "informs", "note": "COGS flows to Form 1065 line 2"},
        ],
    ),
]
