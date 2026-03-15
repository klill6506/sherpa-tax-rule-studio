"""IRS form instruction sources for the 1065 (Partnership) family."""

from sources.federal_data.forms_1120s import _instr


SOURCES_1065 = [
    # ───────────────────────────────────────────────────────────────────────
    # Form 1065 Instructions
    # ───────────────────────────────────────────────────────────────────────
    _instr(
        "IRS_2025_1065_INSTR",
        "Instructions for Form 1065 — U.S. Return of Partnership Income",
        "Form 1065 Instructions (2025)",
        "https://www.irs.gov/instructions/i1065",
        "1065",
        excerpts=[
            {
                "excerpt_label": "Who must file",
                "location_reference": "General Instructions — Who Must File",
                "excerpt_text": (
                    "Every domestic partnership must file Form 1065, unless it neither receives income "
                    "nor incurs any expenditures treated as deductions or credits for federal income "
                    "tax purposes. A partnership is the relationship between two or more persons who "
                    "join to carry on a trade or business, with each person contributing money, "
                    "property, labor, or skill and each expecting to share in the profits and losses. "
                    "A joint venture or other contractual arrangement may create a partnership for "
                    "federal tax purposes even without a formal agreement. File by the 15th day of "
                    "the 3rd month after the end of the partnership's tax year (March 15 for "
                    "calendar year). The return is an information return; the partnership itself "
                    "is not subject to income tax (§701)."
                ),
                "summary_text": "All domestic partnerships file 1065 (information return). Due March 15 for calendar year.",
                "is_key_excerpt": True,
                "topic_tags": ["partnership", "form_1065"],
            },
            {
                "excerpt_label": "Income — Lines 1a through 8",
                "location_reference": "Line Instructions — Income",
                "excerpt_text": (
                    "Line 1a: Gross receipts or sales. Line 1b: Returns and allowances. Line 1c: "
                    "Balance. Line 2: Cost of goods sold (Form 1125-A). Line 3: Gross profit. "
                    "Line 4: Ordinary gain (loss) from Form 4797 Part II line 17. Line 5: Net farm "
                    "profit (loss) from Form 1065-B if applicable. Line 6: Net gain (loss) from "
                    "Form 4797 Part I — net §1231 gain or loss. Line 7: Other income (loss) — "
                    "includes income not elsewhere reported such as interest on trade notes, "
                    "recoveries, and minor miscellaneous income. Line 8: Total income (loss)."
                ),
                "summary_text": "Income: gross receipts, COGS, gross profit, 4797 gains, farm profit, other income.",
                "is_key_excerpt": True,
                "topic_tags": ["form_1065"],
            },
            {
                "excerpt_label": "Deductions — Lines 9 through 21",
                "location_reference": "Line Instructions — Deductions",
                "excerpt_text": (
                    "Line 9: Salaries and wages (other than to partners). Do NOT include guaranteed "
                    "payments to partners — those go on line 10. Line 10: Guaranteed payments to "
                    "partners for services or use of capital (§707(c)). Line 11: Repairs and "
                    "maintenance. Line 12: Bad debts. Line 13: Rent. Line 14: Taxes and licenses "
                    "(not self-employment tax or federal income tax). Line 15: Interest — includes "
                    "business interest expense subject to §163(j) limitation. Line 16a: Depreciation "
                    "(from Form 4562 if required). Line 16b: Less depreciation reported on Form "
                    "1125-A and elsewhere. Line 16c: Balance. Line 17: Depletion (do NOT deduct "
                    "oil/gas — pass through to partners). Line 18: Retirement plans, etc. "
                    "Line 19: Employee benefit programs. Line 20: Other deductions (attach statement). "
                    "Line 21: Total deductions. Line 22: Ordinary business income (loss) — flows "
                    "to Schedule K line 1."
                ),
                "summary_text": "Deductions: wages, guaranteed payments (line 10), rent, taxes, interest (§163(j)), depreciation, benefits.",
                "is_key_excerpt": True,
                "topic_tags": ["form_1065", "guaranteed_payments"],
            },
            {
                "excerpt_label": "Schedule K — Partners' Distributive Share Items",
                "location_reference": "Schedule K Instructions",
                "excerpt_text": (
                    "Schedule K reports the partnership's total income, deductions, credits, and "
                    "other items that must be passed through to partners on Schedule K-1. Items "
                    "that must be separately stated (§702(a)): short-term and long-term capital "
                    "gains/losses, §1231 gains/losses, charitable contributions, §179 deduction, "
                    "foreign taxes, tax-exempt income, investment income/expenses, and rental "
                    "activities. Key lines: 1 — ordinary business income; 2 — net rental real estate "
                    "income (loss) from Form 8825; 3a — other gross rental income; 4 — guaranteed "
                    "payments (both for services and use of capital); 5-7 — interest, dividends, "
                    "royalties; 8-9a — capital gains/losses; 10 — net §1231 gain/loss; 11 — other "
                    "income/loss; 12 — §179 deduction; 13a-d — charitable contributions; 14a-c — "
                    "self-employment items; 15-17 — credits; 18-20 — foreign transactions; "
                    "21 — AMT items."
                ),
                "summary_text": "Schedule K: total of all separately stated + nonseparately computed items flowing to K-1s.",
                "is_key_excerpt": True,
                "topic_tags": ["form_1065", "schedule_k1", "partnership"],
            },
            {
                "excerpt_label": "Schedule B — Other Information",
                "location_reference": "Schedule B Instructions",
                "excerpt_text": (
                    "Schedule B requires information about the partnership's operations: type of "
                    "partnership (general, limited, LLC), principal business activity and product/ "
                    "service, accounting method, number of partners, whether Schedule M-3 is required "
                    "(total assets ≥ $10 million), and questions about foreign transactions, "
                    "tax shelter registration, and reportable transactions. Important: Question 4 "
                    "asks whether the partnership meets all four requirements to qualify for the "
                    "small partnership exception from Schedules L, M-1, M-2: (a) total receipts < "
                    "$250,000, (b) total assets < $250,000, (c) K-1s filed when due, (d) not filing "
                    "or required to file Schedule M-3."
                ),
                "summary_text": "Schedule B: partnership type, business info, small partnership exception ($250K tests), M-3 requirement.",
                "is_key_excerpt": True,
                "topic_tags": ["form_1065", "partnership"],
            },
            {
                "excerpt_label": "Schedule M-1 and M-2",
                "location_reference": "Schedule M-1/M-2 Instructions",
                "excerpt_text": (
                    "Schedule M-1: Reconciliation of Income (Loss) per Books With Income (Loss) per "
                    "Return. Adds back items deducted on books but not on return (e.g., 50% of meals, "
                    "tax penalties, book depreciation exceeding tax depreciation). Subtracts items on "
                    "return not on books (e.g., tax depreciation exceeding book). Schedule M-2: "
                    "Analysis of Partners' Capital Accounts. Reports the total of all partners' "
                    "capital accounts at beginning of year, contributions, net income/loss per books, "
                    "other increases, withdrawals and distributions, other decreases, and ending "
                    "balance. Since 2020, tax basis capital reporting is required for Schedule K-1 "
                    "Item L if the partnership reports capital accounts to partners."
                ),
                "summary_text": "M-1: book-tax reconciliation. M-2: partners' capital accounts. Tax basis capital required on K-1.",
                "is_key_excerpt": True,
                "topic_tags": ["form_1065", "partnership"],
            },
        ],
        topics=["form_1065", "partnership"],
        form_links=[{"form_code": "1065", "link_type": "governs"}],
    ),

    # ───────────────────────────────────────────────────────────────────────
    # Schedule K-1 (Form 1065) Instructions
    # ───────────────────────────────────────────────────────────────────────
    _instr(
        "IRS_2025_1065_K1_INSTR",
        "Instructions for Schedule K-1 (Form 1065) — Partner's Share of Income, Deductions, Credits, etc.",
        "Schedule K-1 (Form 1065) Instructions (2025)",
        "https://www.irs.gov/instructions/i1065sk1",
        "1065",
        excerpts=[
            {
                "excerpt_label": "Box 1 — Ordinary business income (loss)",
                "location_reference": "Box 1 Instructions",
                "excerpt_text": (
                    "Box 1 reports the partner's distributive share of the partnership's ordinary "
                    "business income or loss. This amount is reported on Schedule E Part II. "
                    "General partners: Box 1 income is generally subject to self-employment tax "
                    "(reported on Schedule SE) unless the partner is a limited partner. Limited "
                    "partners: Box 1 income is generally NOT subject to self-employment tax "
                    "(§1402(a)(13)), but guaranteed payments for services (Box 4) ARE subject to "
                    "SE tax regardless of partner status."
                ),
                "summary_text": "Box 1 → Sch E Part II. General partners: subject to SE tax. Limited partners: generally no SE tax.",
                "is_key_excerpt": True,
                "topic_tags": ["schedule_k1", "self_employment", "form_1065"],
            },
            {
                "excerpt_label": "Box 4 — Guaranteed payments",
                "location_reference": "Box 4 Instructions",
                "excerpt_text": (
                    "Box 4 reports guaranteed payments — amounts paid to the partner for services or "
                    "use of capital that are determined without regard to partnership income (§707(c)). "
                    "Guaranteed payments for services are ordinary income to the partner and are "
                    "subject to self-employment tax (reported on Schedule SE). Guaranteed payments "
                    "for the use of capital are treated as interest income — they are ordinary income "
                    "but generally NOT subject to self-employment tax. The total of Box 4 is also "
                    "included in Box 1 for financial accounting purposes but is broken out separately "
                    "because of the different SE tax treatment."
                ),
                "summary_text": "Guaranteed payments: services = SE tax; capital use = no SE tax. Both are ordinary income.",
                "is_key_excerpt": True,
                "topic_tags": ["guaranteed_payments", "self_employment"],
            },
            {
                "excerpt_label": "Boxes 5-11 — Investment income, capital gains, §1231, deductions",
                "location_reference": "Box Instructions",
                "excerpt_text": (
                    "Box 5: Interest income. Box 6a: Ordinary dividends. Box 6b: Qualified dividends. "
                    "Box 7: Royalties → Schedule E page 1. Box 8: Net short-term capital gain (loss) "
                    "→ Schedule D line 5. Box 9a: Net long-term capital gain (loss) → Schedule D "
                    "line 12. Box 9b: Collectibles (28%) gain (loss). Box 9c: Unrecaptured §1250 "
                    "gain. Box 10: Net §1231 gain (loss) → Form 4797 Part I. Box 11: Other income "
                    "(loss) — various codes including cancellation of debt income, recoveries, and "
                    "mining exploration costs recapture."
                ),
                "summary_text": "Boxes 5-11: interest, dividends, royalties, capital gains (ST/LT/28%/§1250), §1231, other income.",
                "is_key_excerpt": True,
                "topic_tags": ["schedule_k1", "capital_gains"],
            },
            {
                "excerpt_label": "Box 14 — Self-employment earnings (loss)",
                "location_reference": "Box 14 Instructions",
                "excerpt_text": (
                    "Box 14 provides codes for self-employment earnings: Code A — Net earnings (loss) "
                    "from self-employment. General partners include their share of ordinary income "
                    "plus guaranteed payments for services. Limited partners include only guaranteed "
                    "payments for services. Code B — Gross farming or fishing income (for purposes "
                    "of estimated tax). Code C — Gross nonfarm income (for estimated tax). SE income "
                    "is subject to 15.3% self-employment tax (12.4% OASDI up to wage base + 2.9% "
                    "Medicare + 0.9% Additional Medicare above threshold)."
                ),
                "summary_text": "Box 14: SE earnings — general partners: ordinary income + GP for services. Limited: GP for services only.",
                "is_key_excerpt": True,
                "topic_tags": ["self_employment", "schedule_k1"],
            },
            {
                "excerpt_label": "Box 20 — §199A QBI information",
                "location_reference": "Box 20 Instructions",
                "excerpt_text": (
                    "Box 20 with various codes provides information needed to compute the qualified "
                    "business income deduction under §199A at the partner level. Code Z — §199A "
                    "information: includes the partner's share of QBI (or qualified loss), W-2 wages, "
                    "UBIA of qualified property, and whether the activity is an SSTB. Code AH — §199A "
                    "SSTB reporting. Partners use this information on Form 8995 (simplified) or "
                    "Form 8995-A (detailed) to compute their individual QBI deduction."
                ),
                "summary_text": "Box 20 Code Z: QBI, W-2 wages, UBIA, SSTB status for partner's §199A deduction calculation.",
                "is_key_excerpt": True,
                "topic_tags": ["qbi_deduction", "schedule_k1"],
            },
        ],
        topics=["schedule_k1", "form_1065", "partnership"],
        form_links=[{"form_code": "K1_1065", "link_type": "governs"}],
    ),

    # ───────────────────────────────────────────────────────────────────────
    # Form 8825 Instructions
    # ───────────────────────────────────────────────────────────────────────
    _instr(
        "IRS_2025_8825_INSTR",
        "Instructions for Form 8825 — Rental Real Estate Income and Expenses of a Partnership or an S Corporation",
        "Form 8825 Instructions (2025)",
        "https://www.irs.gov/instructions/i8825",
        "shared",
        excerpts=[
            {
                "excerpt_label": "Purpose and who files",
                "location_reference": "General Instructions",
                "excerpt_text": (
                    "Form 8825 is used by partnerships and S corporations to report income and "
                    "deductible expenses from rental real estate activities. Each rental real estate "
                    "property is listed separately with its own income and expense detail. The net "
                    "income or loss from all properties is totaled and flows to Schedule K: for "
                    "Form 1065 line 2, for Form 1120-S line 2. Rental real estate activities are "
                    "generally passive activities under §469, regardless of the taxpayer's "
                    "participation level."
                ),
                "summary_text": "Form 8825: rental real estate income/expenses by property. Net flows to Schedule K. Generally passive.",
                "is_key_excerpt": True,
                "topic_tags": ["form_8825", "rental_income"],
            },
            {
                "excerpt_label": "Income and expense reporting",
                "location_reference": "Line Instructions",
                "excerpt_text": (
                    "For each property: gross rents received, expenses (advertising, auto and travel, "
                    "cleaning and maintenance, commissions, insurance, legal and professional fees, "
                    "management fees, mortgage interest, other interest, repairs, taxes, utilities, "
                    "depreciation, other). Net income or loss per property = gross rents minus total "
                    "expenses. Total net income or loss from all properties is combined. If the "
                    "entity has income or expenses from personal property leased with real property, "
                    "those amounts are reported on a separate line."
                ),
                "summary_text": "Per-property: gross rents minus expenses (insurance, mortgage interest, repairs, taxes, depreciation, etc.).",
                "is_key_excerpt": True,
                "topic_tags": ["rental_income", "form_8825"],
            },
            {
                "excerpt_label": "Flow to Schedule K and passive activity treatment",
                "location_reference": "General Instructions",
                "excerpt_text": (
                    "The total net rental real estate income or loss from Form 8825 flows to "
                    "Schedule K, line 2 (Form 1065 or 1120-S). From there it is allocated to "
                    "partners/shareholders on their K-1s. At the partner/shareholder level, rental "
                    "real estate income is generally passive under §469. The $25,000 rental loss "
                    "allowance (§469(i)) for active participants applies at the individual level, "
                    "not at the entity level. Partners/shareholders must also consider the at-risk "
                    "rules (§465) and basis limitations."
                ),
                "summary_text": "Net → Sch K line 2 → K-1. Passive at individual level. $25K exception for active participants.",
                "is_key_excerpt": True,
                "topic_tags": ["rental_income", "passive_activity", "form_8825"],
            },
        ],
        topics=["form_8825", "rental_income", "passive_activity"],
        form_links=[
            {"form_code": "8825", "link_type": "governs"},
            {"form_code": "1065", "link_type": "informs", "note": "Form 8825 net flows to 1065 Schedule K line 2"},
            {"form_code": "1120S", "link_type": "informs", "note": "Form 8825 net flows to 1120-S Schedule K line 2"},
        ],
    ),
]
