"""IRS form instruction sources for Form 1040 and core individual schedules."""

from sources.federal_data.forms_1120s import _instr


SOURCES_1040 = [
    # ───────────────────────────────────────────────────────────────────────
    # Form 1040 Instructions
    # ───────────────────────────────────────────────────────────────────────
    _instr(
        "IRS_2025_1040_INSTR",
        "Instructions for Form 1040 — U.S. Individual Income Tax Return",
        "Form 1040 Instructions (2025)",
        "https://www.irs.gov/instructions/i1040gi",
        "1040",
        excerpts=[
            {
                "excerpt_label": "Filing status",
                "location_reference": "Filing Status",
                "excerpt_text": (
                    "Five filing statuses: (1) Single — unmarried or legally separated on Dec 31. "
                    "(2) Married Filing Jointly (MFJ) — both spouses report all income; both are "
                    "jointly and severally liable. (3) Married Filing Separately (MFS) — may result "
                    "in higher tax; certain credits/deductions are reduced or disallowed. "
                    "(4) Head of Household (HOH) — unmarried on Dec 31, paid more than half the cost "
                    "of keeping up a home for a qualifying person. (5) Qualifying Surviving Spouse — "
                    "spouse died in one of the two prior tax years, has a dependent child, and has "
                    "not remarried. Filing status determines: standard deduction amount, tax bracket "
                    "thresholds, eligibility for credits and deductions."
                ),
                "summary_text": "5 filing statuses: Single, MFJ, MFS, HOH, QSS. Determines brackets, std deduction, credit eligibility.",
                "is_key_excerpt": True,
                "topic_tags": ["filing_status", "individual"],
            },
            {
                "excerpt_label": "Income overview",
                "location_reference": "Income Section",
                "excerpt_text": (
                    "Line 1: Wages, salaries, tips (from W-2). Line 2a: Tax-exempt interest. "
                    "Line 2b: Taxable interest (Schedule B if > $1,500). Line 3a: Qualified dividends. "
                    "Line 3b: Ordinary dividends (Schedule B if > $1,500). Line 4a: IRA distributions. "
                    "Line 4b: Taxable IRA distributions. Line 5a: Pensions and annuities. "
                    "Line 5b: Taxable pensions. Line 6a: Social Security benefits. Line 6b: Taxable "
                    "Social Security (up to 85% may be taxable). Line 7: Capital gain or loss "
                    "(Schedule D, or directly if only Form 1099-B with no adjustments). Line 8: "
                    "Other income from Schedule 1 (business income, rental, farm, unemployment, "
                    "alimony received pre-2019, gambling, etc.). Line 9: Total income."
                ),
                "summary_text": "Income: wages, interest, dividends, IRA/pensions, Social Security, capital gains, Sch 1 other income.",
                "is_key_excerpt": True,
                "topic_tags": ["form_1040", "gross_income"],
            },
            {
                "excerpt_label": "Adjustments to income and standard deduction",
                "location_reference": "Adjusted Gross Income / Deductions",
                "excerpt_text": (
                    "Line 10: Adjustments to income from Schedule 1 Part II — includes educator "
                    "expenses ($300), HSA deduction, self-employment tax deduction (50%), "
                    "self-employed SEP/SIMPLE/qualified plans, self-employed health insurance "
                    "deduction, penalty on early withdrawal of savings, IRA deduction, student loan "
                    "interest deduction ($2,500 max), and other above-the-line deductions. "
                    "Line 11: Adjusted gross income (AGI). Line 12: Standard deduction or itemized "
                    "deductions (Schedule A). Standard deduction for 2025: $15,750 Single/MFS, "
                    "$31,500 MFJ/QSS, $23,625 HOH. Additional "
                    "standard deduction for age 65+ or blind: $1,600 (married) / $2,000 (unmarried)."
                ),
                "summary_text": "Above-the-line: educator, HSA, SE tax, IRA, student loan. Std deduction $15,750/$31,500/$23,625 (2025).",
                "is_key_excerpt": True,
                "topic_tags": ["adjusted_gross_income", "standard_deduction", "form_1040"],
            },
            {
                "excerpt_label": "Tax computation and credits",
                "location_reference": "Tax and Credits",
                "excerpt_text": (
                    "Line 13: Qualified business income deduction (§199A) — 20% of QBI from "
                    "Form 8995 or 8995-A. Line 14: Total deductions. Line 15: Taxable income. "
                    "Line 16: Tax — from Tax Table, Tax Computation Worksheet, or Qualified "
                    "Dividends and Capital Gain Tax Worksheet (preferential rates for LTCG and "
                    "qualified dividends). Schedule 2 Part I: AMT (Form 6251), excess premium tax "
                    "credit repayment. Line 19: Child tax credit ($2,200 per qualifying child per "
                    "OBBBA, up from $2,000) / credit for other dependents "
                    "(Schedule 8812). Line 21: Total credits from Schedule 3 — foreign tax credit, "
                    "education credits (Form 8863), retirement savings credit, child/dependent care "
                    "credit (Form 2441), energy credits, and other nonrefundable credits."
                ),
                "summary_text": "Tax on taxable income (brackets or cap gains rates). Credits: child tax, education, foreign tax, energy.",
                "is_key_excerpt": True,
                "topic_tags": ["form_1040", "individual"],
            },
        ],
        topics=["form_1040", "individual", "filing_status", "standard_deduction"],
        form_links=[{"form_code": "1040", "link_type": "governs"}],
    ),

    # ───────────────────────────────────────────────────────────────────────
    # Schedule A — Itemized Deductions
    # ───────────────────────────────────────────────────────────────────────
    _instr(
        "IRS_2025_1040SA_INSTR",
        "Instructions for Schedule A (Form 1040) — Itemized Deductions",
        "Schedule A Instructions (2025)",
        "https://www.irs.gov/instructions/i1040sca",
        "1040",
        excerpts=[
            {
                "excerpt_label": "Medical and dental expenses",
                "location_reference": "Lines 1-4",
                "excerpt_text": (
                    "Deduct medical and dental expenses that exceed 7.5% of AGI (line 11 of Form "
                    "1040). Eligible expenses include: doctors, dentists, surgeons, hospital services, "
                    "laboratory fees, prescription drugs, insulin, eyeglasses, hearing aids, "
                    "transportation for medical care (standard mileage rate: 22 cents per mile for "
                    "2025), health insurance premiums (including Medicare Part B/D and Medicare "
                    "Advantage), and qualified long-term care insurance premiums (subject to age-based "
                    "limits). NOT deductible: cosmetic surgery (unless due to disfigurement from "
                    "disease, accident, or congenital abnormality), general health expenses, "
                    "nonprescription drugs (except insulin)."
                ),
                "summary_text": "Medical: deductible above 7.5% AGI. Includes Rx, insurance, transport. Not cosmetic or OTC drugs.",
                "is_key_excerpt": True,
                "topic_tags": ["medical_expenses", "itemized_deduction"],
            },
            {
                "excerpt_label": "Taxes — SALT cap",
                "location_reference": "Lines 5-7",
                "excerpt_text": (
                    "Deduct state and local income taxes (or general sales taxes in lieu of income "
                    "taxes), state and local real estate taxes, and state and local personal property "
                    "taxes. The total deduction for state and local taxes is limited to $40,000 "
                    "($20,000 if married filing separately) under OBBBA amendments to §164(b)(6). "
                    "The $40,000 cap is reduced (but not below $10,000/$5,000 MFS) for MAGI "
                    "exceeding $500,000 ($250,000 MFS). Foreign real property taxes are NOT deductible "
                    "for individuals. Taxes paid on property held for business or rental purposes are "
                    "deductible on the appropriate business schedule, not on Schedule A, and are "
                    "NOT subject to the SALT cap."
                ),
                "summary_text": "$40K SALT cap ($20K MFS) per OBBBA. Phased down above $500K MAGI to $10K floor. Business taxes exempt.",
                "is_key_excerpt": True,
                "topic_tags": ["salt", "itemized_deduction"],
            },
            {
                "excerpt_label": "Interest — mortgage and investment",
                "location_reference": "Lines 8-10",
                "excerpt_text": (
                    "Home mortgage interest: deductible on acquisition indebtedness up to $750,000 "
                    "($375,000 MFS) for mortgages taken out after December 15, 2017. Mortgages "
                    "originated on or before that date: $1,000,000 limit. Home equity loan interest "
                    "is deductible only if the loan proceeds were used to buy, build, or substantially "
                    "improve the home securing the debt. Mortgage interest and points are reported on "
                    "Form 1098. Investment interest expense (Form 4952): deductible up to net "
                    "investment income. Excess carries forward. Taxpayer may elect to treat qualified "
                    "dividends and long-term capital gains as investment income (giving up preferential "
                    "rate treatment)."
                ),
                "summary_text": "Mortgage interest: $750K acquisition debt ($1M pre-12/15/2017). Home equity only if used for home. Investment interest ≤ net investment income.",
                "is_key_excerpt": True,
                "topic_tags": ["mortgage_interest", "interest_deduction", "itemized_deduction"],
            },
            {
                "excerpt_label": "Charitable contributions",
                "location_reference": "Lines 11-14",
                "excerpt_text": (
                    "Cash contributions to qualifying organizations: deductible up to 30% of AGI "
                    "(OBBBA reduced from 60%). "
                    "Noncash contributions: capital gain property to public charities limited to "
                    "20% of AGI. Excess carries "
                    "forward 5 years. Substantiation: cash — bank record or written receipt required "
                    "for any amount; $250+ requires contemporaneous written acknowledgment. Noncash "
                    "over $500: Form 8283 required. Over $5,000 (non-securities): qualified appraisal "
                    "required. Clothing/household items must be in good used condition."
                ),
                "summary_text": "Cash: 30% AGI limit (OBBBA). Capital gain property: 20%. $250+ needs acknowledgment. $5K+ needs appraisal.",
                "is_key_excerpt": True,
                "topic_tags": ["charitable", "itemized_deduction"],
            },
            {
                "excerpt_label": "Casualty and theft losses",
                "location_reference": "Line 15",
                "excerpt_text": (
                    "Personal casualty and theft losses are deductible only if attributable to a "
                    "federally declared disaster (post-TCJA, 2018-2025). Each loss must exceed $100, "
                    "and total net casualty losses must exceed 10% of AGI. Use Form 4684 to compute "
                    "the deductible amount. Business and income-producing property casualty losses "
                    "remain fully deductible on the appropriate business schedule."
                ),
                "summary_text": "Personal casualty/theft: federally declared disasters only. $100 per event + 10% AGI floor.",
                "is_key_excerpt": True,
                "topic_tags": ["casualty_theft", "itemized_deduction"],
            },
        ],
        topics=["schedule_a", "itemized_deduction", "individual"],
        form_links=[{"form_code": "1040SA", "link_type": "governs"}],
    ),

    # ───────────────────────────────────────────────────────────────────────
    # Schedule B — Interest and Ordinary Dividends
    # ───────────────────────────────────────────────────────────────────────
    _instr(
        "IRS_2025_1040SB_INSTR",
        "Instructions for Schedule B (Form 1040) — Interest and Ordinary Dividends",
        "Schedule B Instructions (2025)",
        "https://www.irs.gov/instructions/i1040sb",
        "1040",
        excerpts=[
            {
                "excerpt_label": "Filing requirement and reporting",
                "location_reference": "General Instructions",
                "excerpt_text": (
                    "You must complete Schedule B if you had over $1,500 of taxable interest or "
                    "ordinary dividends, or you received interest from a seller-financed mortgage "
                    "and the buyer used the property as a personal residence, or you have accrued "
                    "interest from a bond, or you are reporting OID in an amount less than the OID "
                    "shown on Form 1099-OID, or you had a financial interest in or signature "
                    "authority over a foreign financial account (FBAR reporting), or you received a "
                    "distribution from a foreign trust. Part I lists each payer of interest. Part II "
                    "lists each payer of ordinary dividends. Part III asks about foreign accounts "
                    "and trusts."
                ),
                "summary_text": "Schedule B required if interest/dividends > $1,500, or foreign account/trust reporting needed.",
                "is_key_excerpt": True,
                "topic_tags": ["schedule_b_interest", "individual"],
            },
        ],
        topics=["schedule_b_interest", "individual"],
        form_links=[{"form_code": "1040SB", "link_type": "governs"}],
    ),

    # ───────────────────────────────────────────────────────────────────────
    # Schedule C — Profit or Loss from Business
    # ───────────────────────────────────────────────────────────────────────
    _instr(
        "IRS_2025_1040SC_INSTR",
        "Instructions for Schedule C (Form 1040) — Profit or Loss from Business (Sole Proprietorship)",
        "Schedule C Instructions (2025)",
        "https://www.irs.gov/instructions/i1040sc",
        "1040",
        excerpts=[
            {
                "excerpt_label": "Who files",
                "location_reference": "General Instructions",
                "excerpt_text": (
                    "Use Schedule C to report income or loss from a business you operated or a "
                    "profession you practiced as a sole proprietor. Also use Schedule C if you were "
                    "a statutory employee (box 13 on Form W-2 checked), or you were a minister "
                    "reporting non-employee income. File a separate Schedule C for each business. "
                    "Net profit from Schedule C flows to: (1) Form 1040 line 8 (via Schedule 1), "
                    "(2) Schedule SE for self-employment tax, and (3) may qualify for the §199A "
                    "QBI deduction."
                ),
                "summary_text": "Sole proprietors and statutory employees. Net profit → Schedule 1 → SE tax → §199A QBI.",
                "is_key_excerpt": True,
                "topic_tags": ["schedule_c", "self_employment"],
            },
            {
                "excerpt_label": "Income and expenses",
                "location_reference": "Line Instructions",
                "excerpt_text": (
                    "Income: Line 1 — gross receipts or sales. Line 2 — returns and allowances. "
                    "Line 4 — cost of goods sold (if applicable). Line 6 — other income. "
                    "Expenses (lines 8-27): advertising, car and truck (standard mileage rate: "
                    "70 cents/mile for 2025, or actual expenses), commissions, contract labor, "
                    "depletion, depreciation (Form 4562), employee benefit programs, insurance, "
                    "interest (mortgage on business property, other), legal and professional services, "
                    "office expense, pension/profit-sharing, rent (vehicles/equipment, other), "
                    "repairs and maintenance, supplies, taxes and licenses, travel, meals (50%), "
                    "utilities, wages, and other expenses. Line 31: Net profit or loss."
                ),
                "summary_text": "Gross receipts minus COGS and expenses. 70¢/mile (2025). Meals 50%. Depreciation via 4562.",
                "is_key_excerpt": True,
                "topic_tags": ["schedule_c", "trade_business_expenses"],
            },
            {
                "excerpt_label": "Home office deduction",
                "location_reference": "Line 30 Instructions",
                "excerpt_text": (
                    "If you use part of your home for business, you may be able to deduct expenses "
                    "for the business use of your home. You must use the area exclusively and "
                    "regularly as: (1) your principal place of business, (2) a place where you meet "
                    "clients/customers, or (3) a separate structure. Two methods: Simplified method — "
                    "$5 per square foot of home used for business, maximum 300 square feet ($1,500 "
                    "maximum deduction). Regular method — Form 8829 (actual expenses: mortgage "
                    "interest, insurance, utilities, repairs, depreciation, allocated by business "
                    "percentage of home). The deduction cannot exceed the gross income from the "
                    "business use minus other business expenses."
                ),
                "summary_text": "Home office: exclusive/regular use. Simplified: $5/sqft max $1,500. Regular: Form 8829 actual expenses.",
                "is_key_excerpt": True,
                "topic_tags": ["home_office", "schedule_c"],
            },
        ],
        topics=["schedule_c", "self_employment", "trade_business_expenses", "home_office"],
        form_links=[{"form_code": "1040SC", "link_type": "governs"}],
    ),

    # ───────────────────────────────────────────────────────────────────────
    # Schedule D (Form 1040) — Capital Gains and Losses
    # ───────────────────────────────────────────────────────────────────────
    _instr(
        "IRS_2025_1040SD_INSTR",
        "Instructions for Schedule D (Form 1040) — Capital Gains and Losses",
        "Schedule D (Form 1040) Instructions (2025)",
        "https://www.irs.gov/instructions/i1040sd",
        "1040",
        excerpts=[
            {
                "excerpt_label": "Short-term vs long-term and reporting",
                "location_reference": "General Instructions",
                "excerpt_text": (
                    "Report all capital gains and losses on Schedule D and Form 8949. Part I: "
                    "Short-term capital gains and losses (assets held 1 year or less). Part II: "
                    "Long-term capital gains and losses (assets held more than 1 year). Sources of "
                    "capital gain/loss include: Form 8949 (individual transactions), Schedule K-1 "
                    "(partnership/S-Corp/estate/trust pass-through), Form 4797 Part I (§1231 gains "
                    "treated as long-term), Form 6252 (installment sale), Form 8824 (like-kind "
                    "exchange), and capital gain distributions from mutual funds (Form 1099-DIV "
                    "box 2a — reported directly on line 13 without Form 8949)."
                ),
                "summary_text": "Part I: ST (≤1yr). Part II: LT (>1yr). Sources: 8949, K-1, 4797, 6252, 8824, mutual fund CGDs.",
                "is_key_excerpt": True,
                "topic_tags": ["schedule_d_1040", "capital_gains"],
            },
            {
                "excerpt_label": "28% rate gain and unrecaptured §1250",
                "location_reference": "Lines 18-19",
                "excerpt_text": (
                    "Line 18: 28% rate gain or loss — includes gain from collectibles (art, antiques, "
                    "stamps, coins, gems, metals, certain ETFs) and §1202 exclusion gain on qualified "
                    "small business stock (the taxable portion). Collectibles gain is taxed at a "
                    "maximum rate of 28%. Line 19: Unrecaptured §1250 gain — the portion of gain on "
                    "the sale of §1250 property (depreciable real property) attributable to prior "
                    "depreciation that was not already recaptured as ordinary income under §1250. "
                    "Taxed at a maximum rate of 25%. Worksheet in instructions computes this amount. "
                    "For S-Corp/partnership pass-throughs, this appears on K-1 Box 8c/9c."
                ),
                "summary_text": "28% rate: collectibles, §1202 taxable portion. 25% rate: unrecaptured §1250 (depreciation on realty).",
                "is_key_excerpt": True,
                "topic_tags": ["capital_gains", "recapture"],
            },
            {
                "excerpt_label": "Capital loss limitation and carryover",
                "location_reference": "Lines 16, 21, and Capital Loss Carryover Worksheet",
                "excerpt_text": (
                    "Net capital loss is deductible against ordinary income up to $3,000 per year "
                    "($1,500 if married filing separately). Excess carries forward to the next year "
                    "indefinitely, retaining its short-term or long-term character. Use the Capital "
                    "Loss Carryover Worksheet in the instructions to figure the carryover amount. "
                    "Netting rules: short-term gains/losses are netted first, then long-term "
                    "gains/losses, then net short-term and net long-term are combined."
                ),
                "summary_text": "$3K annual cap loss deduction ($1.5K MFS). Excess carries forward indefinitely retaining character.",
                "is_key_excerpt": True,
                "topic_tags": ["capital_gains", "losses"],
            },
            {
                "excerpt_label": "Qualified Dividends and Capital Gain Tax Worksheet",
                "location_reference": "Tax Computation Instructions",
                "excerpt_text": (
                    "If you have qualified dividends or net capital gain, use the Qualified Dividends "
                    "and Capital Gain Tax Worksheet (or Schedule D Tax Worksheet if you have 28% rate "
                    "gain or unrecaptured §1250 gain). Preferential rates for 2025: 0% if taxable "
                    "income (including the gain) falls in the 10%/12% brackets, 15% in the 22%/24%/ "
                    "32%/35% brackets, 20% in the 37% bracket. The threshold amounts for 2025 "
                    "(approximate, indexed): 0% up to $48,350 single / $96,700 MFJ; 15% up to "
                    "$533,400 single / $600,050 MFJ; 20% above those amounts."
                ),
                "summary_text": "LTCG/qualified dividends: 0%/15%/20% based on income. Special worksheets for 28% and §1250 gain.",
                "is_key_excerpt": True,
                "topic_tags": ["capital_gains", "schedule_d_1040"],
            },
        ],
        topics=["schedule_d_1040", "capital_gains", "individual"],
        form_links=[{"form_code": "1040SD", "link_type": "governs"}],
    ),

    # ───────────────────────────────────────────────────────────────────────
    # Schedule E — Supplemental Income
    # ───────────────────────────────────────────────────────────────────────
    _instr(
        "IRS_2025_1040SE_INSTR",
        "Instructions for Schedule E (Form 1040) — Supplemental Income and Loss",
        "Schedule E Instructions (2025)",
        "https://www.irs.gov/instructions/i1040se",
        "1040",
        excerpts=[
            {
                "excerpt_label": "Part I — Rental real estate and royalty income",
                "location_reference": "Part I Instructions",
                "excerpt_text": (
                    "Part I reports income and expenses from rental real estate, royalties, and "
                    "partnerships/S corporations (for royalties). For each rental property: report "
                    "gross rents received, then deduct: advertising, auto and travel, cleaning and "
                    "maintenance, commissions, insurance, legal and professional fees, management "
                    "fees, mortgage interest, other interest, repairs, taxes, utilities, depreciation "
                    "(Form 4562), and other expenses. Net rental income or loss per property. "
                    "Rental real estate activities are generally passive under §469. At-risk "
                    "limitation (§465) may apply. Use Form 8582 to figure the allowable passive "
                    "activity loss."
                ),
                "summary_text": "Part I: rental income minus expenses per property. Generally passive (§469). At-risk (§465) applies.",
                "is_key_excerpt": True,
                "topic_tags": ["schedule_e", "rental_income", "passive_activity"],
            },
            {
                "excerpt_label": "Part II — Income or loss from partnerships and S corporations",
                "location_reference": "Part II Instructions",
                "excerpt_text": (
                    "Part II reports the income or loss from partnerships and S corporations shown "
                    "on Schedule K-1. For each entity: report the employer identification number, "
                    "whether the activity is passive, and the net income or loss from K-1 Box 1 "
                    "(ordinary income/loss for 1065) or Box 1 (ordinary income/loss for 1120-S). "
                    "Passive activity: if the taxpayer did not materially participate, the income/ "
                    "loss is passive and subject to the §469 limitation. Nonpassive: if the taxpayer "
                    "materially participated, the income/loss is nonpassive. Loss limitations apply "
                    "in this order: (1) basis limitation (§704(d) for partnerships, §1366(d) for "
                    "S-Corps), (2) at-risk limitation (§465, Form 6198), (3) passive activity "
                    "limitation (§469, Form 8582), (4) excess business loss limitation (§461(l))."
                ),
                "summary_text": "Part II: K-1 income/loss. Passive if no material participation. Loss limits: basis → at-risk → passive → excess.",
                "is_key_excerpt": True,
                "topic_tags": ["schedule_e", "schedule_k1", "passive_activity", "at_risk"],
            },
        ],
        topics=["schedule_e", "rental_income", "passive_activity", "individual"],
        form_links=[{"form_code": "1040SE", "link_type": "governs"}],
    ),

    # ───────────────────────────────────────────────────────────────────────
    # Schedule F — Profit or Loss from Farming
    # ───────────────────────────────────────────────────────────────────────
    _instr(
        "IRS_2025_1040SF_INSTR",
        "Instructions for Schedule F (Form 1040) — Profit or Loss From Farming",
        "Schedule F Instructions (2025)",
        "https://www.irs.gov/instructions/i1040sf",
        "1040",
        excerpts=[
            {
                "excerpt_label": "Who files and income reporting",
                "location_reference": "General Instructions",
                "excerpt_text": (
                    "Use Schedule F to report farm income and expenses if you cultivated, operated, "
                    "or managed a farm for profit, either as owner or tenant. Farm income includes: "
                    "sales of livestock, produce, grains, and other products you raised; cooperative "
                    "distributions; agricultural program payments; Commodity Credit Corporation (CCC) "
                    "loans reported as income; crop insurance proceeds and federal crop disaster "
                    "payments; custom hire (machine work) income; and other farm income. Accounting "
                    "method: most farmers use cash method. Accrual method required if the farm has "
                    "a corporation or partnership owner (with certain exceptions)."
                ),
                "summary_text": "Schedule F: farm profit/loss for owners/tenants. Cash method typical. Includes sales, co-op, crop insurance.",
                "is_key_excerpt": True,
                "topic_tags": ["schedule_f", "farm_income"],
            },
            {
                "excerpt_label": "Farm expenses",
                "location_reference": "Expense Instructions",
                "excerpt_text": (
                    "Farm expenses include: car and truck expenses, chemicals, conservation expenses "
                    "(§175), custom hire, depreciation (Form 4562), employee benefit programs, feed, "
                    "fertilizers and lime, freight and trucking, gasoline/fuel/oil, insurance, "
                    "interest (mortgage and other), labor hired, pension/profit-sharing plans, "
                    "rent (vehicles/equipment and other land/animals), repairs and maintenance, "
                    "seeds and plants, storage and warehousing, supplies, taxes, utilities, and "
                    "veterinary/breeding/medicine. Special rules: §180 allows current deduction of "
                    "fertilizer and lime costs that are normally capital. §263A(d) exempts most "
                    "farming operations from UNICAP rules for plants with a preproductive period "
                    "of 2 years or less."
                ),
                "summary_text": "Farm expenses: feed, seed, fertilizer (§180 deduction), labor, depreciation. §263A(d) UNICAP farm exemption.",
                "is_key_excerpt": True,
                "topic_tags": ["farm_income", "schedule_f"],
            },
        ],
        topics=["schedule_f", "farm_income", "individual"],
        form_links=[{"form_code": "1040SF", "link_type": "governs"}],
    ),

    # ───────────────────────────────────────────────────────────────────────
    # Schedule SE — Self-Employment Tax
    # ───────────────────────────────────────────────────────────────────────
    _instr(
        "IRS_2025_1040SSE_INSTR",
        "Instructions for Schedule SE (Form 1040) — Self-Employment Tax",
        "Schedule SE Instructions (2025)",
        "https://www.irs.gov/instructions/i1040sse",
        "1040",
        excerpts=[
            {
                "excerpt_label": "Who must file",
                "location_reference": "General Instructions",
                "excerpt_text": (
                    "You must file Schedule SE if: (1) your net earnings from self-employment "
                    "(other than church employee income) were $400 or more, or (2) you had church "
                    "employee income of $108.28 or more. Net earnings from self-employment include: "
                    "net profit from Schedule C or Schedule F, your share of partnership net income "
                    "if you are a general partner, and guaranteed payments for services from a "
                    "partnership. S corporation shareholders do NOT report Box 1 income on Schedule "
                    "SE (S-Corp income is not subject to self-employment tax)."
                ),
                "summary_text": "File SE if net SE earnings ≥ $400. Includes Sch C, Sch F, general partner share, GP for services. Not S-Corp income.",
                "is_key_excerpt": True,
                "topic_tags": ["self_employment", "schedule_se"],
            },
            {
                "excerpt_label": "SE tax computation",
                "location_reference": "Line Instructions",
                "excerpt_text": (
                    "Step 1: Multiply net earnings by 92.35% (this approximates the employee-equivalent "
                    "portion — the employer half of SE tax is deductible). Step 2: OASDI portion — "
                    "12.4% on the first $176,100 of combined wages + SE income (2025 wage base). If "
                    "you also have wages subject to Social Security, reduce the $176,100 threshold by "
                    "those wages. Step 3: Medicare portion — 2.9% on all SE earnings (no cap). "
                    "Step 4: Additional Medicare Tax — 0.9% on SE income above $200,000 ($250,000 "
                    "MFJ, $125,000 MFS). Total SE tax is reported on Schedule 2 line 4. The "
                    "deductible portion (50% of SE tax) goes on Schedule 1 line 15."
                ),
                "summary_text": "SE tax: 92.35% × earnings → 12.4% OASDI (up to $176,100) + 2.9% Medicare + 0.9% additional Medicare. 50% deductible.",
                "is_key_excerpt": True,
                "topic_tags": ["self_employment", "schedule_se", "fica"],
            },
        ],
        topics=["schedule_se", "self_employment", "fica", "individual"],
        form_links=[{"form_code": "1040SSE", "link_type": "governs"}],
    ),
]
