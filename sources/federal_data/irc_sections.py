"""IRC section authority source data.

All IRC sections are source_type=code_section, source_rank=controlling,
requires_human_review=True. Excerpts are derived from official IRS guidance
(instructions, publications) rather than raw statutory text.
"""

# ─── helper to reduce boilerplate ────────────────────────────────────────────

def _irc(section, title, citation, excerpts, topics, form_links=None, notes=None):
    """Return a standard IRC source dict."""
    return {
        "source_code": f"IRC_{section}",
        "source_type": "code_section",
        "source_rank": "controlling",
        "jurisdiction_code": "FED",
        "title": f"IRC §{section} — {title}",
        "citation": f"26 U.S.C. §{section}",
        "issuer": "Congress",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "requires_human_review": True,
        "trust_score": 10.0,
        "notes": notes or "Statutory text paraphrased from official IRS guidance. Requires review against current code.",
        "topics": topics,
        "excerpts": excerpts,
        "form_links": form_links or [],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Income / Deduction Fundamentals
# ═══════════════════════════════════════════════════════════════════════════════

IRC_INCOME_DEDUCTION = [
    _irc("61", "Gross Income Defined", "26 U.S.C. §61",
         excerpts=[
             {
                 "excerpt_label": "§61(a) — General definition",
                 "location_reference": "§61(a)",
                 "excerpt_text": (
                     "Except as otherwise provided in this subtitle, gross income means all income "
                     "from whatever source derived, including (but not limited to): (1) Compensation "
                     "for services, including fees, commissions, fringe benefits, and similar items; "
                     "(2) Gross income derived from business; (3) Gains derived from dealings in "
                     "property; (4) Interest; (5) Rents; (6) Royalties; (7) Dividends; (8) Alimony "
                     "and separate maintenance payments (for pre-2019 agreements); (9) Annuities; "
                     "(10) Income from life insurance and endowment contracts; (11) Pensions; "
                     "(12) Income from discharge of indebtedness; (13) Distributive share of "
                     "partnership gross income; (14) Income in respect of a decedent; "
                     "(15) Income from an interest in an estate or trust."
                 ),
                 "summary_text": "Gross income = all income from whatever source derived. 15 enumerated categories.",
                 "is_key_excerpt": True,
                 "topic_tags": ["gross_income"],
             },
         ],
         topics=["gross_income"],
         form_links=[
             {"form_code": "1040", "link_type": "governs"},
             {"form_code": "1120", "link_type": "governs"},
             {"form_code": "1120S", "link_type": "governs"},
             {"form_code": "1065", "link_type": "governs"},
         ]),

    _irc("62", "Adjusted Gross Income Defined", "26 U.S.C. §62",
         excerpts=[
             {
                 "excerpt_label": "§62(a) — Above-the-line deductions",
                 "location_reference": "§62(a)",
                 "excerpt_text": (
                     "Adjusted gross income is gross income minus the following deductions: trade or "
                     "business deductions (§162), certain trade/business deductions of employees "
                     "(performing artists, officials, armed forces reservists), losses from sale of "
                     "property (§165(c)), deductions attributable to rents and royalties, certain "
                     "deductions of life tenants, retirement savings contributions (IRA deductions), "
                     "penalties on early withdrawal of savings, alimony (pre-2019 agreements), "
                     "moving expenses (armed forces only), one-half of self-employment tax, health "
                     "insurance deduction for self-employed, student loan interest (§221), tuition "
                     "and fees (if applicable), and the qualified business income deduction under §199A."
                 ),
                 "summary_text": "AGI = gross income minus above-the-line deductions (§62(a) list).",
                 "is_key_excerpt": True,
                 "topic_tags": ["adjusted_gross_income"],
             },
         ],
         topics=["adjusted_gross_income", "individual"],
         form_links=[{"form_code": "1040", "link_type": "governs"}]),

    _irc("63", "Taxable Income Defined", "26 U.S.C. §63",
         excerpts=[
             {
                 "excerpt_label": "§63(a)-(b) — Taxable income computation",
                 "location_reference": "§63(a)-(b)",
                 "excerpt_text": (
                     "Taxable income means adjusted gross income minus (a) the standard deduction "
                     "or (b) itemized deductions, and minus the deduction for qualified business "
                     "income under §199A. For 2025, standard deduction amounts are indexed for "
                     "inflation. Itemized deductions are claimed on Schedule A in lieu of the "
                     "standard deduction."
                 ),
                 "summary_text": "Taxable income = AGI - (standard or itemized deduction) - §199A QBI deduction.",
                 "is_key_excerpt": True,
                 "topic_tags": ["taxable_income", "standard_deduction", "itemized_deduction"],
             },
         ],
         topics=["taxable_income", "standard_deduction", "itemized_deduction"],
         form_links=[{"form_code": "1040", "link_type": "governs"}]),

    _irc("162", "Trade or Business Expenses", "26 U.S.C. §162",
         excerpts=[
             {
                 "excerpt_label": "§162(a) — General rule",
                 "location_reference": "§162(a)",
                 "excerpt_text": (
                     "There shall be allowed as a deduction all the ordinary and necessary expenses "
                     "paid or incurred during the taxable year in carrying on any trade or business, "
                     "including: (1) a reasonable allowance for salaries or other compensation for "
                     "personal services actually rendered; (2) traveling expenses (including amounts "
                     "expended for meals) while away from home in the pursuit of a trade or business; "
                     "and (3) rentals or other payments required to be made as a condition to the "
                     "continued use or possession of property."
                 ),
                 "summary_text": "Allows deduction for ordinary and necessary business expenses — salaries, travel, rent.",
                 "is_key_excerpt": True,
                 "topic_tags": ["trade_business_expenses"],
             },
             {
                 "excerpt_label": "§162(m) — Excessive employee remuneration",
                 "location_reference": "§162(m)",
                 "excerpt_text": (
                     "No deduction shall be allowed for applicable employee remuneration paid or "
                     "accrued with respect to any covered employee to the extent that such "
                     "remuneration for the taxable year exceeds $1,000,000. Covered employees include "
                     "the CEO, CFO, and the 3 other highest-compensated officers, plus anyone who was "
                     "a covered employee for any preceding taxable year beginning after December 31, 2016."
                 ),
                 "summary_text": "$1M deduction cap per covered employee for publicly held corporations.",
                 "is_key_excerpt": True,
                 "topic_tags": ["trade_business_expenses", "officer_compensation"],
             },
         ],
         topics=["trade_business_expenses"],
         form_links=[
             {"form_code": "1040SC", "link_type": "governs"},
             {"form_code": "1120", "link_type": "governs"},
             {"form_code": "1120S", "link_type": "governs"},
             {"form_code": "1065", "link_type": "governs"},
         ]),

    _irc("163", "Interest", "26 U.S.C. §163",
         excerpts=[
             {
                 "excerpt_label": "§163(a) — General rule",
                 "location_reference": "§163(a)",
                 "excerpt_text": (
                     "There shall be allowed as a deduction all interest paid or accrued within the "
                     "taxable year on indebtedness. Section 163(h) disallows personal interest but "
                     "allows qualified residence interest on acquisition indebtedness up to $750,000 "
                     "($375,000 MFS) for debt incurred after 12/15/2017. Home equity interest is "
                     "deductible only if used to buy, build, or improve the home securing the debt."
                 ),
                 "summary_text": "Interest generally deductible. Personal interest disallowed except qualified residence interest ($750K limit).",
                 "is_key_excerpt": True,
                 "topic_tags": ["interest_deduction", "mortgage_interest"],
             },
             {
                 "excerpt_label": "§163(j) — Business interest limitation",
                 "location_reference": "§163(j)",
                 "excerpt_text": (
                     "The deduction for business interest is limited to the sum of: (1) business "
                     "interest income, (2) 30% of adjusted taxable income (ATI), and (3) floor plan "
                     "financing interest. Disallowed interest carries forward indefinitely. Small "
                     "business exception: taxpayers with average annual gross receipts of $30 million "
                     "or less (indexed) for the 3 prior years are exempt."
                 ),
                 "summary_text": "Business interest limited to 30% of ATI. Small business exemption at $30M gross receipts.",
                 "is_key_excerpt": True,
                 "topic_tags": ["interest_deduction"],
             },
         ],
         topics=["interest_deduction", "mortgage_interest"],
         form_links=[
             {"form_code": "1040SA", "link_type": "governs", "note": "Mortgage interest on Schedule A"},
             {"form_code": "1040SC", "link_type": "governs"},
         ]),

    _irc("164", "Taxes", "26 U.S.C. §164",
         excerpts=[
             {
                 "excerpt_label": "§164(a) — Deductible taxes",
                 "location_reference": "§164(a)",
                 "excerpt_text": (
                     "The following taxes shall be allowed as a deduction for the taxable year within "
                     "which paid or accrued: (1) State, local, and foreign real property taxes; "
                     "(2) State and local personal property taxes; (3) State, local, and foreign "
                     "income, war profits, and excess profits taxes. For individuals, the aggregate "
                     "deduction for state and local taxes is limited to $10,000 ($5,000 MFS) under "
                     "§164(b)(6) (TCJA SALT cap, effective 2018-2025). For tax years beginning after "
                     "December 31, 2025, this limitation is scheduled to expire."
                 ),
                 "summary_text": "SALT deduction capped at $10K for individuals (TCJA). Business taxes fully deductible.",
                 "is_key_excerpt": True,
                 "topic_tags": ["salt"],
             },
         ],
         topics=["salt"],
         form_links=[{"form_code": "1040SA", "link_type": "governs"}]),

    _irc("165", "Losses", "26 U.S.C. §165",
         excerpts=[
             {
                 "excerpt_label": "§165(a)-(c) — Deductible losses",
                 "location_reference": "§165(a)-(c)",
                 "excerpt_text": (
                     "There shall be allowed as a deduction any loss sustained during the taxable "
                     "year and not compensated for by insurance or otherwise. For individuals, "
                     "deductible losses are limited to: (1) losses incurred in a trade or business; "
                     "(2) losses incurred in any transaction entered into for profit (not trade or "
                     "business); (3) casualty or theft losses to the extent they arise from a "
                     "federally declared disaster (post-TCJA, personal casualty losses are only "
                     "deductible for federally declared disasters)."
                 ),
                 "summary_text": "Losses deductible for business, profit-seeking, and federally declared disaster casualties.",
                 "is_key_excerpt": True,
                 "topic_tags": ["losses", "casualty_theft"],
             },
         ],
         topics=["losses", "casualty_theft"],
         form_links=[
             {"form_code": "4684", "link_type": "governs"},
             {"form_code": "4797", "link_type": "governs"},
         ]),

    _irc("166", "Bad Debts", "26 U.S.C. §166",
         excerpts=[
             {
                 "excerpt_label": "§166(a)-(d) — Bad debt deduction",
                 "location_reference": "§166(a)-(d)",
                 "excerpt_text": (
                     "There shall be allowed as a deduction any debt which becomes worthless within "
                     "the taxable year. For wholly worthless debts, the deduction is allowed in the "
                     "year of worthlessness. For partially worthless debts, the deduction is limited "
                     "to the amount charged off. Nonbusiness bad debts (§166(d)) are treated as "
                     "short-term capital losses and are subject to the capital loss limitation."
                 ),
                 "summary_text": "Business bad debts = ordinary deduction. Nonbusiness bad debts = short-term capital loss.",
                 "is_key_excerpt": True,
                 "topic_tags": ["bad_debts"],
             },
         ],
         topics=["bad_debts"],
         form_links=[]),

    _irc("167", "Depreciation — General", "26 U.S.C. §167",
         excerpts=[
             {
                 "excerpt_label": "§167(a) — General rule",
                 "location_reference": "§167(a)",
                 "excerpt_text": (
                     "There shall be allowed as a depreciation deduction a reasonable allowance for "
                     "the exhaustion, wear and tear (including a reasonable allowance for "
                     "obsolescence) of property used in the trade or business or held for the "
                     "production of income. For most tangible property placed in service after 1986, "
                     "depreciation is computed under §168 (MACRS). Section 167 remains the authority "
                     "for property not covered by MACRS, including certain intangible property."
                 ),
                 "summary_text": "General depreciation authority. Most tangible property uses §168 MACRS instead.",
                 "is_key_excerpt": True,
                 "topic_tags": ["depreciation"],
             },
         ],
         topics=["depreciation"],
         form_links=[{"form_code": "4562", "link_type": "governs"}]),

    _irc("170", "Charitable Contributions", "26 U.S.C. §170",
         excerpts=[
             {
                 "excerpt_label": "§170(a)-(b) — Allowance and limitations",
                 "location_reference": "§170(a)-(b)",
                 "excerpt_text": (
                     "There shall be allowed as a deduction any charitable contribution made within "
                     "the taxable year. For individuals: cash contributions to public charities "
                     "limited to 60% of AGI; capital gain property to public charities limited to "
                     "30% of AGI (or 50% if reduced to basis); contributions to private foundations "
                     "limited to 30% of AGI (20% for capital gain property). For corporations: "
                     "limited to 10% of taxable income. Excess contributions carry forward 5 years."
                 ),
                 "summary_text": "Charitable deduction with AGI-based percentage limits. 5-year carryforward for excess.",
                 "is_key_excerpt": True,
                 "topic_tags": ["charitable"],
             },
             {
                 "excerpt_label": "§170(f) — Substantiation requirements",
                 "location_reference": "§170(f)",
                 "excerpt_text": (
                     "No deduction for any contribution of $250 or more unless the taxpayer "
                     "substantiates the contribution with a contemporaneous written acknowledgment "
                     "from the donee organization. Contributions of property valued over $5,000 "
                     "(other than publicly traded securities) require a qualified appraisal. "
                     "Clothing and household items must be in good used condition or better."
                 ),
                 "summary_text": "$250+ needs written acknowledgment. $5K+ non-securities property needs qualified appraisal.",
                 "is_key_excerpt": True,
                 "topic_tags": ["charitable"],
             },
         ],
         topics=["charitable"],
         form_links=[{"form_code": "1040SA", "link_type": "governs"}]),

    _irc("195", "Start-Up Expenditures", "26 U.S.C. §195",
         excerpts=[
             {
                 "excerpt_label": "§195(b) — Election to deduct",
                 "location_reference": "§195(b)",
                 "excerpt_text": (
                     "A taxpayer may elect to deduct up to $5,000 of start-up expenditures in the "
                     "taxable year the active trade or business begins. The $5,000 amount is reduced "
                     "(but not below zero) by the amount by which start-up expenditures exceed "
                     "$50,000. The remainder is amortized over the 180-month period beginning with "
                     "the month the active trade or business begins."
                 ),
                 "summary_text": "$5K immediate deduction (reduced if >$50K total), remainder over 180 months.",
                 "is_key_excerpt": True,
                 "topic_tags": ["start_up_costs"],
             },
         ],
         topics=["start_up_costs"],
         form_links=[{"form_code": "4562", "link_type": "informs"}]),

    _irc("197", "Amortization of Goodwill and Certain Other Intangibles", "26 U.S.C. §197",
         excerpts=[
             {
                 "excerpt_label": "§197(a)-(d) — 15-year amortization",
                 "location_reference": "§197(a)-(d)",
                 "excerpt_text": (
                     "A taxpayer shall be entitled to an amortization deduction with respect to any "
                     "amortizable §197 intangible, ratably over the 15-year period (180 months) "
                     "beginning with the month in which the intangible was acquired. Section 197 "
                     "intangibles include: goodwill, going concern value, workforce in place, "
                     "business books and records, patents, copyrights, formulas, customer-based "
                     "intangibles, supplier-based intangibles, licenses/permits/rights granted by "
                     "governmental units, covenants not to compete, and franchises/trademarks/trade names."
                 ),
                 "summary_text": "§197 intangibles (goodwill, etc.) amortized straight-line over 15 years (180 months).",
                 "is_key_excerpt": True,
                 "topic_tags": ["amortization"],
             },
         ],
         topics=["amortization"],
         form_links=[{"form_code": "4562", "link_type": "governs"}]),

    _irc("199A", "Qualified Business Income Deduction", "26 U.S.C. §199A",
         excerpts=[
             {
                 "excerpt_label": "§199A(a) — QBI deduction allowance",
                 "location_reference": "§199A(a)",
                 "excerpt_text": (
                     "For taxable years beginning after December 31, 2017, an individual taxpayer "
                     "(including through a pass-through entity) is allowed a deduction equal to the "
                     "lesser of: (A) the combined qualified business income amount, or (B) 20% of "
                     "the excess (if any) of taxable income over net capital gain. The deduction is "
                     "available regardless of whether the taxpayer itemizes."
                 ),
                 "summary_text": "20% deduction on qualified business income, limited to taxable income less net capital gain.",
                 "is_key_excerpt": True,
                 "topic_tags": ["qbi_deduction"],
             },
             {
                 "excerpt_label": "§199A(b)-(d) — W-2/UBIA and SSTB limitations",
                 "location_reference": "§199A(b)-(d)",
                 "excerpt_text": (
                     "For taxpayers above the threshold amount ($191,950 single / $383,900 MFJ for "
                     "2025, indexed), the QBI deduction for each qualified trade or business is "
                     "limited to the greater of: (1) 50% of W-2 wages, or (2) 25% of W-2 wages "
                     "plus 2.5% of the unadjusted basis immediately after acquisition (UBIA) of "
                     "qualified property. Specified service trades or businesses (SSTBs) — health, "
                     "law, accounting, actuarial science, performing arts, consulting, athletics, "
                     "financial services, brokerage, or any trade or business where the principal "
                     "asset is the reputation or skill of employees — are phased out entirely above "
                     "the threshold range."
                 ),
                 "summary_text": "Above threshold: W-2/UBIA limits apply. SSTBs phased out entirely above threshold.",
                 "is_key_excerpt": True,
                 "topic_tags": ["qbi_deduction"],
             },
         ],
         topics=["qbi_deduction", "passthrough"],
         form_links=[
             {"form_code": "8995", "link_type": "governs"},
             {"form_code": "8995A", "link_type": "governs"},
         ]),

    _irc("212", "Expenses for Production of Income", "26 U.S.C. §212",
         excerpts=[
             {
                 "excerpt_label": "§212 — Investment expenses (suspended by TCJA)",
                 "location_reference": "§212",
                 "excerpt_text": (
                     "In the case of an individual, there shall be allowed as a deduction all the "
                     "ordinary and necessary expenses paid or incurred during the taxable year for "
                     "the production or collection of income, for the management, conservation, or "
                     "maintenance of property held for the production of income, or in connection "
                     "with the determination, collection, or refund of any tax. NOTE: For tax years "
                     "2018-2025, these deductions are suspended for individuals under TCJA §11045 "
                     "(miscellaneous itemized deductions subject to 2% AGI floor are disallowed)."
                 ),
                 "summary_text": "Investment/tax preparation expenses. Suspended for individuals 2018-2025 by TCJA.",
                 "is_key_excerpt": True,
                 "topic_tags": ["itemized_deduction"],
             },
         ],
         topics=["itemized_deduction"],
         form_links=[]),

    _irc("213", "Medical Expenses", "26 U.S.C. §213",
         excerpts=[
             {
                 "excerpt_label": "§213(a) — 7.5% AGI floor",
                 "location_reference": "§213(a)",
                 "excerpt_text": (
                     "There shall be allowed as a deduction the expenses paid during the taxable "
                     "year, not compensated for by insurance or otherwise, for medical care of the "
                     "taxpayer, spouse, and dependents, to the extent that such expenses exceed 7.5% "
                     "of adjusted gross income. Medical care includes diagnosis, cure, mitigation, "
                     "treatment, or prevention of disease, transportation for medical care, qualified "
                     "long-term care services, and health insurance premiums (including Medicare Part "
                     "B, Part D, and Medicare Advantage)."
                 ),
                 "summary_text": "Medical expenses deductible above 7.5% of AGI. Includes insurance, treatment, transport.",
                 "is_key_excerpt": True,
                 "topic_tags": ["medical_expenses"],
             },
         ],
         topics=["medical_expenses"],
         form_links=[{"form_code": "1040SA", "link_type": "governs"}]),

    _irc("263A", "Uniform Capitalization Rules (UNICAP)", "26 U.S.C. §263A",
         excerpts=[
             {
                 "excerpt_label": "§263A(a)-(b) — Capitalization requirement",
                 "location_reference": "§263A(a)-(b)",
                 "excerpt_text": (
                     "In the case of any property to which this section applies, any costs described "
                     "in §263A(a)(2) shall be included in inventory costs (for property which is "
                     "inventory) or capitalized (for other property). Applies to: real or tangible "
                     "personal property produced by the taxpayer, and real or personal property "
                     "acquired for resale. Small business exception: taxpayers with average annual "
                     "gross receipts of $30 million or less for the 3 prior years are exempt. "
                     "Farm exception under §263A(d): plants with a preproductive period of more than "
                     "2 years; taxpayer may elect out."
                 ),
                 "summary_text": "UNICAP: capitalize production/acquisition costs into inventory/basis. $30M exemption.",
                 "is_key_excerpt": True,
                 "topic_tags": ["unicap", "cost_of_goods_sold"],
             },
         ],
         topics=["unicap", "cost_of_goods_sold"],
         form_links=[{"form_code": "1125A", "link_type": "governs"}]),

    _irc("267", "Related Party Transactions", "26 U.S.C. §267",
         excerpts=[
             {
                 "excerpt_label": "§267(a)-(b) — Loss disallowance and matching",
                 "location_reference": "§267(a)-(b)",
                 "excerpt_text": (
                     "No deduction shall be allowed for losses from sales or exchanges of property "
                     "between related persons as defined in §267(b). Related persons include: family "
                     "members (siblings, spouse, ancestors, lineal descendants), individual and >50% "
                     "owned entity, two entities with >50% common ownership, fiduciary and "
                     "beneficiary of the same trust, corporation and tax-exempt entity if related. "
                     "Accrual-basis payor to cash-basis related payee: deduction deferred until "
                     "amount is includible in payee's income (matching rule)."
                 ),
                 "summary_text": "Losses disallowed between related parties. Accrual/cash timing must match.",
                 "is_key_excerpt": True,
                 "topic_tags": ["related_party", "losses"],
             },
         ],
         topics=["related_party"],
         form_links=[]),

    _irc("274", "Meals and Entertainment Limitations", "26 U.S.C. §274",
         excerpts=[
             {
                 "excerpt_label": "§274(a)-(k) — Current limitations",
                 "location_reference": "§274(a)-(k)",
                 "excerpt_text": (
                     "No deduction is allowed for entertainment, amusement, or recreation expenses "
                     "(§274(a), post-TCJA). Business meals: 50% deductible if directly related to "
                     "or associated with the active conduct of business and not lavish or "
                     "extravagant (§274(k)). The temporary 100% deduction for restaurant meals "
                     "(2021-2022) has expired. Employer-provided meals at a de minimis eating "
                     "facility: 50% deductible. Meals included in compensation: fully deductible. "
                     "Transportation fringe benefits: no deduction for employer-provided parking or "
                     "transit passes under §274(a)(4) (TCJA)."
                 ),
                 "summary_text": "Entertainment: nondeductible. Business meals: 50%. No employer parking/transit deduction.",
                 "is_key_excerpt": True,
                 "topic_tags": ["meals_entertainment"],
             },
         ],
         topics=["meals_entertainment", "trade_business_expenses"],
         form_links=[
             {"form_code": "1040SC", "link_type": "informs"},
             {"form_code": "1120", "link_type": "informs"},
             {"form_code": "1065", "link_type": "informs"},
         ]),

    _irc("280A", "Home Office", "26 U.S.C. §280A",
         excerpts=[
             {
                 "excerpt_label": "§280A(c) — Exclusive use test and exceptions",
                 "location_reference": "§280A(c)",
                 "excerpt_text": (
                     "Home office expenses are deductible only if the portion of the dwelling is "
                     "used exclusively and regularly as: (1) the principal place of business, "
                     "(2) a place to meet patients, clients, or customers, or (3) a separate "
                     "structure not attached to the dwelling used in connection with business. "
                     "Employees: post-TCJA (2018-2025), employee home office deduction is suspended "
                     "(unreimbursed employee expenses are miscellaneous itemized deductions, "
                     "currently disallowed). Self-employed: may use simplified method ($5/sq ft, "
                     "max 300 sq ft = $1,500 max) or actual expense method."
                 ),
                 "summary_text": "Home office: exclusive/regular use required. Employee deduction suspended 2018-2025. Simplified: $5/sqft max $1,500.",
                 "is_key_excerpt": True,
                 "topic_tags": ["home_office"],
             },
         ],
         topics=["home_office"],
         form_links=[{"form_code": "1040SC", "link_type": "governs"}]),
]


# ═══════════════════════════════════════════════════════════════════════════════
# Property Transactions
# ═══════════════════════════════════════════════════════════════════════════════

IRC_PROPERTY = [
    _irc("1001", "Determination of Amount of and Recognition of Gain or Loss", "26 U.S.C. §1001",
         excerpts=[
             {
                 "excerpt_label": "§1001(a)-(c) — Gain/loss computation and recognition",
                 "location_reference": "§1001(a)-(c)",
                 "excerpt_text": (
                     "The gain from the sale or other disposition of property is the excess of the "
                     "amount realized over the adjusted basis (§1011). The loss is the excess of "
                     "adjusted basis over amount realized. Amount realized includes money received "
                     "plus the fair market value of any other property received, plus the amount of "
                     "any liabilities assumed by the buyer. The entire amount of gain or loss is "
                     "recognized except as otherwise provided (e.g., §1031, §1033)."
                 ),
                 "summary_text": "Gain/loss = amount realized minus adjusted basis. Fully recognized unless exception applies.",
                 "is_key_excerpt": True,
                 "topic_tags": ["basis_rules", "dispositions"],
             },
         ],
         topics=["basis_rules", "dispositions"],
         form_links=[{"form_code": "4797", "link_type": "governs"}]),

    _irc("1011", "Adjusted Basis for Determining Gain or Loss", "26 U.S.C. §1011",
         excerpts=[
             {
                 "excerpt_label": "§1011-1016 — Basis rules",
                 "location_reference": "§1011-1016",
                 "excerpt_text": (
                     "Adjusted basis for determining gain or loss: start with cost basis (§1012) "
                     "or other basis as determined under §1014 (inherited = FMV at date of death), "
                     "§1015 (gift = donor's basis, with FMV rule for losses), or §1031/1033 "
                     "(substituted basis). Adjust upward for capital expenditures, improvements. "
                     "Adjust downward for depreciation, amortization, casualty losses, and other "
                     "items of tax-free recovery. §1016 specifies required adjustments."
                 ),
                 "summary_text": "Start with cost/transferred basis. Adjust up for improvements, down for depreciation.",
                 "is_key_excerpt": True,
                 "topic_tags": ["basis_rules"],
             },
         ],
         topics=["basis_rules"],
         form_links=[]),

    _irc("1031", "Like-Kind Exchanges", "26 U.S.C. §1031",
         excerpts=[
             {
                 "excerpt_label": "§1031(a) — Nonrecognition of gain/loss",
                 "location_reference": "§1031(a)",
                 "excerpt_text": (
                     "No gain or loss shall be recognized on the exchange of real property held for "
                     "productive use in a trade or business or for investment if such real property "
                     "is exchanged solely for real property of like kind which is to be held either "
                     "for productive use in a trade or business or for investment. Post-TCJA: "
                     "like-kind exchange treatment applies ONLY to real property (personal property "
                     "exchanges no longer qualify). Identification period: 45 days. Exchange period: "
                     "180 days. Boot received triggers gain recognition."
                 ),
                 "summary_text": "§1031: real property only (post-TCJA). 45-day ID, 180-day completion. Boot = gain.",
                 "is_key_excerpt": True,
                 "topic_tags": ["like_kind_exchange"],
             },
         ],
         topics=["like_kind_exchange"],
         form_links=[{"form_code": "8824", "link_type": "governs"}]),

    _irc("1033", "Involuntary Conversions", "26 U.S.C. §1033",
         excerpts=[
             {
                 "excerpt_label": "§1033(a) — Nonrecognition and replacement period",
                 "location_reference": "§1033(a)",
                 "excerpt_text": (
                     "If property is compulsorily or involuntarily converted (by destruction, theft, "
                     "seizure, condemnation, or threat thereof), gain is recognized only to the "
                     "extent the amount realized exceeds the cost of replacement property that is "
                     "similar or related in service or use. Replacement period: generally 2 years "
                     "from end of taxable year in which gain is realized; 3 years for condemned real "
                     "property held for business or investment. Basis of replacement property is "
                     "reduced by the gain not recognized."
                 ),
                 "summary_text": "Involuntary conversion: defer gain if replaced within 2 years (3 for condemned realty).",
                 "is_key_excerpt": True,
                 "topic_tags": ["involuntary_conversion"],
             },
         ],
         topics=["involuntary_conversion"],
         form_links=[{"form_code": "4797", "link_type": "informs"}]),

    _irc("1211", "Limitation on Capital Losses", "26 U.S.C. §1211",
         excerpts=[
             {
                 "excerpt_label": "§1211(a)-(b) — Capital loss limits",
                 "location_reference": "§1211(a)-(b)",
                 "excerpt_text": (
                     "Corporations: capital losses are allowed only to the extent of capital gains. "
                     "Individuals: capital losses are allowed to the extent of capital gains plus "
                     "$3,000 ($1,500 if MFS) of ordinary income. Excess capital loss carries forward "
                     "to subsequent years (individuals: indefinitely; corporations: back 3 years, "
                     "forward 5 years)."
                 ),
                 "summary_text": "Individuals: $3K ordinary offset + carryforward. Corporations: only vs. gains, 3-back/5-forward.",
                 "is_key_excerpt": True,
                 "topic_tags": ["capital_gains", "losses"],
             },
         ],
         topics=["capital_gains", "losses"],
         form_links=[
             {"form_code": "1040SD", "link_type": "governs"},
             {"form_code": "1120", "link_type": "governs"},
         ]),

    _irc("1212", "Capital Loss Carrybacks and Carryovers", "26 U.S.C. §1212",
         excerpts=[
             {
                 "excerpt_label": "§1212(a)-(b) — Carryover rules",
                 "location_reference": "§1212(a)-(b)",
                 "excerpt_text": (
                     "Corporations: net capital loss may be carried back 3 years and forward 5 years "
                     "as a short-term capital loss. Individuals: net capital loss in excess of the "
                     "$3,000 annual limit ($1,500 MFS) is carried forward to the next taxable year, "
                     "retaining its character as short-term or long-term. Individual capital loss "
                     "carryforward is unlimited in duration."
                 ),
                 "summary_text": "Individuals: unlimited carryforward retaining character. Corps: 3 back, 5 forward as ST.",
                 "is_key_excerpt": True,
                 "topic_tags": ["capital_gains"],
             },
         ],
         topics=["capital_gains"],
         form_links=[{"form_code": "1040SD", "link_type": "governs"}]),

    _irc("1221", "Capital Asset Defined", "26 U.S.C. §1221",
         excerpts=[
             {
                 "excerpt_label": "§1221(a) — Definition by exclusion",
                 "location_reference": "§1221(a)",
                 "excerpt_text": (
                     "The term 'capital asset' means property held by the taxpayer, EXCEPT: "
                     "(1) inventory or property held primarily for sale to customers in the ordinary "
                     "course of business; (2) depreciable property used in a trade or business; "
                     "(3) real property used in a trade or business; (4) certain copyrights, literary "
                     "or artistic compositions; (5) accounts or notes receivable acquired in the "
                     "ordinary course of business; (6) certain U.S. government publications; "
                     "(7) certain commodity derivative financial instruments; (8) certain hedging "
                     "transactions; (9) supplies regularly consumed in business."
                 ),
                 "summary_text": "Capital asset = all property EXCEPT inventory, business realty/personalty, receivables, etc.",
                 "is_key_excerpt": True,
                 "topic_tags": ["capital_asset", "capital_gains"],
             },
         ],
         topics=["capital_asset", "capital_gains"],
         form_links=[
             {"form_code": "8949", "link_type": "governs"},
             {"form_code": "1040SD", "link_type": "governs"},
         ]),

    _irc("453", "Installment Method", "26 U.S.C. §453",
         excerpts=[
             {
                 "excerpt_label": "§453(a)-(c) — Installment method rules",
                 "location_reference": "§453(a)-(c)",
                 "excerpt_text": (
                     "Income from an installment sale is reported using the installment method: "
                     "income recognized in each year = payment received × gross profit ratio "
                     "(gross profit / total contract price). Applies automatically unless taxpayer "
                     "elects out. Does NOT apply to: dealer dispositions (inventory), sales of "
                     "publicly traded property. For related party sales (§453(e)): if related "
                     "purchaser resells within 2 years, original seller accelerates remaining gain."
                 ),
                 "summary_text": "Installment method: gain = payment × gross profit ratio. Related party 2-year resale rule.",
                 "is_key_excerpt": True,
                 "topic_tags": ["installment_sale"],
             },
             {
                 "excerpt_label": "§453A — Interest on deferred tax",
                 "location_reference": "§453A",
                 "excerpt_text": (
                     "If an installment obligation arises from a sale where the sales price exceeds "
                     "$150,000 and the aggregate face amount of all installment obligations arising "
                     "during the year and outstanding at close of year exceeds $5 million, the "
                     "taxpayer must pay interest on the deferred tax liability. This is a special "
                     "charge, not subject to the limitations on interest deductions."
                 ),
                 "summary_text": "Interest charged on deferred tax when sales price >$150K and total obligations >$5M.",
                 "is_key_excerpt": True,
                 "topic_tags": ["installment_sale"],
             },
         ],
         topics=["installment_sale"],
         form_links=[{"form_code": "6252", "link_type": "governs"}]),
]


# ═══════════════════════════════════════════════════════════════════════════════
# Pass-Through Entity — Partnership
# ═══════════════════════════════════════════════════════════════════════════════

IRC_PARTNERSHIP = [
    _irc("701", "Partners, Not Partnership, Subject to Tax", "26 U.S.C. §701",
         excerpts=[
             {
                 "excerpt_label": "§701 — Partnership as conduit",
                 "location_reference": "§701",
                 "excerpt_text": (
                     "A partnership as such shall not be subject to the income tax imposed by this "
                     "chapter. Persons carrying on business as partners shall be liable for income "
                     "tax only in their separate or individual capacities."
                 ),
                 "summary_text": "Partnership is a conduit — not taxed at entity level. Partners taxed individually.",
                 "is_key_excerpt": True,
                 "topic_tags": ["partnership"],
             },
         ],
         topics=["partnership"],
         form_links=[{"form_code": "1065", "link_type": "governs"}]),

    _irc("702", "Income and Credits of Partner", "26 U.S.C. §702",
         excerpts=[
             {
                 "excerpt_label": "§702(a) — Separately stated items",
                 "location_reference": "§702(a)",
                 "excerpt_text": (
                     "In determining income tax, each partner shall take into account separately "
                     "the partner's distributive share of: (1) short-term capital gains/losses, "
                     "(2) long-term capital gains/losses, (3) §1231 gains/losses, (4) charitable "
                     "contributions, (5) dividends eligible for special rates, (6) taxes described "
                     "in §901 (foreign tax credit), (7) other items required to be stated "
                     "separately, and (8) taxable income or loss exclusive of items above."
                 ),
                 "summary_text": "Partners separately account for cap gains/losses, §1231, charitable, foreign tax, and other items.",
                 "is_key_excerpt": True,
                 "topic_tags": ["partnership", "schedule_k1"],
             },
         ],
         topics=["partnership", "schedule_k1"],
         form_links=[{"form_code": "1065", "link_type": "governs"}]),

    _irc("703", "Partnership Computations", "26 U.S.C. §703",
         excerpts=[
             {
                 "excerpt_label": "§703(a) — Prohibited deductions at partnership level",
                 "location_reference": "§703(a)",
                 "excerpt_text": (
                     "The taxable income of a partnership shall be computed in the same manner as "
                     "an individual except: (1) items described in §702(a) shall be separately "
                     "stated, (2) the following deductions shall NOT be allowed to the partnership: "
                     "personal exemptions, foreign taxes (passed through), charitable contributions "
                     "(passed through), net operating losses, and additional itemized deductions."
                 ),
                 "summary_text": "Partnership income computed like individual but without personal exemptions, NOLs, etc.",
                 "is_key_excerpt": True,
                 "topic_tags": ["partnership"],
             },
         ],
         topics=["partnership"],
         form_links=[{"form_code": "1065", "link_type": "governs"}]),

    _irc("704", "Partner's Distributive Share", "26 U.S.C. §704",
         excerpts=[
             {
                 "excerpt_label": "§704(a)-(b) — Allocation rules",
                 "location_reference": "§704(a)-(b)",
                 "excerpt_text": (
                     "A partner's distributive share of income, gain, loss, deduction, or credit "
                     "is determined by the partnership agreement. However, an allocation under the "
                     "agreement will be respected only if it has substantial economic effect. If the "
                     "allocation lacks substantial economic effect, the partner's distributive share "
                     "is determined in accordance with the partner's interest in the partnership, "
                     "considering all facts and circumstances."
                 ),
                 "summary_text": "Allocations per partnership agreement if substantial economic effect; otherwise by partner interest.",
                 "is_key_excerpt": True,
                 "topic_tags": ["partnership", "special_allocations"],
             },
             {
                 "excerpt_label": "§704(d) — Basis limitation on losses",
                 "location_reference": "§704(d)",
                 "excerpt_text": (
                     "A partner's distributive share of partnership loss shall be allowed only to "
                     "the extent of the adjusted basis of such partner's interest in the partnership "
                     "at the end of the partnership year in which such loss occurred. Any excess "
                     "loss is carried forward and allowed in a subsequent year to the extent basis "
                     "is restored."
                 ),
                 "summary_text": "Losses limited to partner's basis. Excess carries forward until basis restored.",
                 "is_key_excerpt": True,
                 "topic_tags": ["partner_basis", "losses"],
             },
         ],
         topics=["partnership", "special_allocations", "partner_basis"],
         form_links=[{"form_code": "1065", "link_type": "governs"}]),

    _irc("705", "Determination of Basis of Partner's Interest", "26 U.S.C. §705",
         excerpts=[
             {
                 "excerpt_label": "§705(a) — Basis adjustments",
                 "location_reference": "§705(a)",
                 "excerpt_text": (
                     "Basis of a partner's interest is increased by: (1) the partner's distributive "
                     "share of taxable income, (2) tax-exempt income, and (3) the excess of "
                     "deductions for depletion over the basis of the depletable property. Basis is "
                     "decreased (but not below zero) by: (1) distributions, (2) the partner's "
                     "distributive share of partnership losses, (3) expenditures not deductible and "
                     "not chargeable to capital, and (4) the partner's deduction for depletion."
                 ),
                 "summary_text": "Basis up for income/tax-exempt. Down for distributions, losses, nondeductible expenses.",
                 "is_key_excerpt": True,
                 "topic_tags": ["partner_basis"],
             },
         ],
         topics=["partner_basis"],
         form_links=[{"form_code": "1065", "link_type": "informs"}]),

    _irc("706", "Taxable Years of Partner and Partnership", "26 U.S.C. §706",
         excerpts=[
             {
                 "excerpt_label": "§706(a)-(b) — Year-end rules",
                 "location_reference": "§706(a)-(b)",
                 "excerpt_text": (
                     "A partner includes items from the partnership for any taxable year of the "
                     "partnership ending within or with the partner's taxable year. A partnership "
                     "must adopt the same taxable year as partners owning a majority interest; if "
                     "no majority, the year of all principal partners; otherwise a year producing "
                     "the least aggregate deferral. A §444 election may allow a different year with "
                     "required payments."
                 ),
                 "summary_text": "Partnership year must match majority partners. §444 allows limited election.",
                 "is_key_excerpt": True,
                 "topic_tags": ["partnership"],
             },
         ],
         topics=["partnership"],
         form_links=[{"form_code": "1065", "link_type": "governs"}]),

    _irc("707", "Transactions Between Partner and Partnership", "26 U.S.C. §707",
         excerpts=[
             {
                 "excerpt_label": "§707(a)-(c) — Partner acting in non-partner capacity and guaranteed payments",
                 "location_reference": "§707(a)-(c)",
                 "excerpt_text": (
                     "If a partner engages in a transaction with a partnership other than in the "
                     "capacity as a member of the partnership, the transaction is treated as between "
                     "the partnership and a non-partner (§707(a)). Guaranteed payments (§707(c)): "
                     "payments to a partner for services or use of capital determined without regard "
                     "to partnership income are treated as made to a non-partner. Guaranteed payments "
                     "are ordinary income to the recipient and deductible by the partnership. "
                     "Disguised sale rules (§707(a)(2)(B)): if a partner contributes property and "
                     "receives a related distribution within 2 years, presumed to be a sale."
                 ),
                 "summary_text": "Guaranteed payments = ordinary income to partner. 2-year disguised sale presumption.",
                 "is_key_excerpt": True,
                 "topic_tags": ["guaranteed_payments", "partnership"],
             },
         ],
         topics=["guaranteed_payments", "partnership"],
         form_links=[{"form_code": "1065", "link_type": "governs"}]),

    _irc("721", "Nonrecognition of Gain or Loss on Contribution", "26 U.S.C. §721",
         excerpts=[
             {
                 "excerpt_label": "§721-723 — Contributions to partnerships",
                 "location_reference": "§721-723",
                 "excerpt_text": (
                     "No gain or loss shall be recognized to a partnership or to any of its "
                     "partners in the case of a contribution of property to the partnership in "
                     "exchange for an interest in the partnership (§721). Basis to the partnership: "
                     "the contributing partner's adjusted basis (§723). Basis to the partner: "
                     "the partner's adjusted basis in contributed property, increased by gain "
                     "recognized (if any) and contributions of money (§722)."
                 ),
                 "summary_text": "Contributions: no gain/loss. Partnership gets carryover basis. Partner basis = contributed basis.",
                 "is_key_excerpt": True,
                 "topic_tags": ["partnership_contributions"],
             },
         ],
         topics=["partnership_contributions"],
         form_links=[{"form_code": "1065", "link_type": "governs"}]),

    _irc("731", "Extent of Recognition of Gain or Loss on Distribution", "26 U.S.C. §731",
         excerpts=[
             {
                 "excerpt_label": "§731-737 — Partnership distributions",
                 "location_reference": "§731-737",
                 "excerpt_text": (
                     "In the case of a distribution by a partnership to a partner: gain is recognized "
                     "only to the extent money (including marketable securities) distributed exceeds "
                     "the partner's adjusted basis (§731(a)(1)). Loss is recognized only on "
                     "liquidating distributions consisting solely of money, unrealized receivables, "
                     "and inventory (§731(a)(2)). Basis of distributed property: generally the "
                     "partnership's adjusted basis, limited to the partner's basis (§732)."
                 ),
                 "summary_text": "Gain only if cash > basis. Loss only on liquidation of money/receivables/inventory.",
                 "is_key_excerpt": True,
                 "topic_tags": ["partnership_distributions"],
             },
         ],
         topics=["partnership_distributions"],
         form_links=[{"form_code": "1065", "link_type": "governs"}]),

    _irc("741", "Recognition and Character of Gain or Loss on Sale of Interest", "26 U.S.C. §741",
         excerpts=[
             {
                 "excerpt_label": "§741-743 — Partnership interest transfers",
                 "location_reference": "§741-743",
                 "excerpt_text": (
                     "Gain or loss from the sale or exchange of an interest in a partnership is "
                     "recognized, and is capital gain/loss except to the extent provided in §751 "
                     "(hot assets). §743(b) optional basis adjustment: if the partnership has a "
                     "§754 election in effect, the transferee partner gets a special basis adjustment "
                     "to the partner's share of partnership property equal to the difference between "
                     "the partner's basis in the interest and the partner's share of inside basis."
                 ),
                 "summary_text": "Sale of interest: capital gain/loss except for §751 hot assets. §754 election → basis step-up/down.",
                 "is_key_excerpt": True,
                 "topic_tags": ["partnership_transfers"],
             },
         ],
         topics=["partnership_transfers"],
         form_links=[{"form_code": "1065", "link_type": "informs"}]),

    _irc("751", "Unrealized Receivables and Inventory Items", "26 U.S.C. §751",
         excerpts=[
             {
                 "excerpt_label": "§751(a)-(d) — Hot assets",
                 "location_reference": "§751(a)-(d)",
                 "excerpt_text": (
                     "On the sale of a partnership interest, the amount realized attributable to "
                     "unrealized receivables and inventory items (collectively 'hot assets') is "
                     "treated as ordinary income/loss rather than capital. Unrealized receivables "
                     "include: rights to payments for services or goods not yet recognized, plus "
                     "§1245/§1250 recapture amounts. Inventory items: any property of the "
                     "partnership that is not a capital asset or §1231 property."
                 ),
                 "summary_text": "Hot assets (receivables + inventory) trigger ordinary income on sale of partnership interest.",
                 "is_key_excerpt": True,
                 "topic_tags": ["partnership_transfers"],
             },
         ],
         topics=["partnership_transfers"],
         form_links=[{"form_code": "1065", "link_type": "governs"}]),

    _irc("752", "Treatment of Certain Liabilities", "26 U.S.C. §752",
         excerpts=[
             {
                 "excerpt_label": "§752(a)-(b) — Liability allocation",
                 "location_reference": "§752(a)-(b)",
                 "excerpt_text": (
                     "Any increase in a partner's share of partnership liabilities is treated as a "
                     "contribution of money by the partner to the partnership (increasing basis). "
                     "Any decrease in a partner's share of partnership liabilities is treated as a "
                     "distribution of money to the partner (decreasing basis; gain if distribution "
                     "exceeds basis). Recourse liabilities are allocated to partners who bear the "
                     "economic risk of loss. Nonrecourse liabilities are allocated based on profit "
                     "sharing ratios (with adjustments for minimum gain and §704(c) built-in gain)."
                 ),
                 "summary_text": "Liability increase = cash contribution (basis up). Decrease = distribution (basis down).",
                 "is_key_excerpt": True,
                 "topic_tags": ["partner_basis", "partnership"],
             },
         ],
         topics=["partner_basis", "partnership"],
         form_links=[{"form_code": "1065", "link_type": "governs"}]),
]


# ═══════════════════════════════════════════════════════════════════════════════
# Pass-Through Entity — S Corporation
# ═══════════════════════════════════════════════════════════════════════════════

IRC_S_CORP = [
    _irc("1361", "S Corporation Defined", "26 U.S.C. §1361",
         excerpts=[
             {
                 "excerpt_label": "§1361(a)-(b) — Eligibility requirements",
                 "location_reference": "§1361(a)-(b)",
                 "excerpt_text": (
                     "An S corporation is a small business corporation that has made an election "
                     "under §1362. A small business corporation is a domestic corporation that: "
                     "(1) has no more than 100 shareholders; (2) has only allowable shareholders "
                     "(individuals, estates, certain trusts, tax-exempt organizations under "
                     "§401(a) or §501(c)(3)); (3) has no nonresident alien shareholders; "
                     "(4) has only one class of stock (differences in voting rights permitted). "
                     "Members of a family (6 generations) may elect to be treated as one shareholder."
                 ),
                 "summary_text": "S-Corp: ≤100 shareholders, one class of stock, domestic, eligible shareholders only.",
                 "is_key_excerpt": True,
                 "topic_tags": ["s_corporation"],
             },
         ],
         topics=["s_corporation"],
         form_links=[{"form_code": "1120S", "link_type": "governs"}]),

    _irc("1362", "Election; Revocation; Termination", "26 U.S.C. §1362",
         excerpts=[
             {
                 "excerpt_label": "§1362(a)-(d) — Election and termination",
                 "location_reference": "§1362(a)-(d)",
                 "excerpt_text": (
                     "An eligible small business corporation may elect S-Corp status by filing Form "
                     "2553 with the consent of all shareholders. Election made by the 15th day of "
                     "the 3rd month of the tax year is effective for that year; later elections are "
                     "effective the next year. Revocation requires consent of shareholders holding "
                     ">50% of shares. Election terminates if the corporation ceases to be a small "
                     "business corporation (eligibility violation) or has excess passive investment "
                     "income for 3 consecutive years while having C-Corp earnings and profits."
                 ),
                 "summary_text": "Elect via Form 2553 (all shareholders consent). Revoke with >50%. Auto-terminates on eligibility violation.",
                 "is_key_excerpt": True,
                 "topic_tags": ["s_corporation"],
             },
         ],
         topics=["s_corporation"],
         form_links=[{"form_code": "1120S", "link_type": "governs"}]),

    _irc("1363", "Effect of Election on Corporation", "26 U.S.C. §1363",
         excerpts=[
             {
                 "excerpt_label": "§1363(a)-(b) — Tax treatment",
                 "location_reference": "§1363(a)-(b)",
                 "excerpt_text": (
                     "An S corporation is generally not subject to income tax. The S corporation's "
                     "taxable income is computed in the same manner as an individual, except: "
                     "items described in §1366(a)(1) (separately stated items) must be separately "
                     "stated. Deductions not allowed at the corporate level include personal "
                     "exemptions, foreign taxes (passed through), charitable contributions (passed "
                     "through), net operating losses, and the §199A deduction (computed at "
                     "shareholder level)."
                 ),
                 "summary_text": "S-Corp not taxed at entity level. Computed like individual. Certain deductions pass through.",
                 "is_key_excerpt": True,
                 "topic_tags": ["s_corporation"],
             },
         ],
         topics=["s_corporation"],
         form_links=[{"form_code": "1120S", "link_type": "governs"}]),

    _irc("1366", "Pass-Through of Items to Shareholders", "26 U.S.C. §1366",
         excerpts=[
             {
                 "excerpt_label": "§1366(a) — Separately stated and nonseparately computed items",
                 "location_reference": "§1366(a)",
                 "excerpt_text": (
                     "In determining the tax of a shareholder, there shall be taken into account "
                     "the shareholder's pro rata share of: (A) items of income (including tax-exempt "
                     "income), loss, deduction, or credit the separate treatment of which could "
                     "affect the liability for tax of any shareholder (separately stated items), and "
                     "(B) the S corporation's nonseparately computed income or loss."
                 ),
                 "summary_text": "Shareholders report pro rata share of separately stated + nonseparately computed items.",
                 "is_key_excerpt": True,
                 "topic_tags": ["s_corporation", "schedule_k1"],
             },
             {
                 "excerpt_label": "§1366(d) — Loss limitations",
                 "location_reference": "§1366(d)",
                 "excerpt_text": (
                     "The aggregate amount of losses and deductions taken into account by a "
                     "shareholder cannot exceed the sum of: (1) the adjusted basis of the "
                     "shareholder's stock, and (2) the shareholder's adjusted basis of any "
                     "indebtedness of the S corporation to the shareholder. Disallowed losses "
                     "carry forward indefinitely and are treated as incurred in the next year."
                 ),
                 "summary_text": "Losses limited to stock basis + debt basis. Excess carries forward indefinitely.",
                 "is_key_excerpt": True,
                 "topic_tags": ["s_corp_basis", "losses"],
             },
         ],
         topics=["s_corporation", "schedule_k1", "s_corp_basis"],
         form_links=[
             {"form_code": "1120S", "link_type": "governs"},
             {"form_code": "7203", "link_type": "governs"},
         ]),

    _irc("1367", "Adjustments to Basis of Stock of Shareholders", "26 U.S.C. §1367",
         excerpts=[
             {
                 "excerpt_label": "§1367(a) — Basis adjustments",
                 "location_reference": "§1367(a)",
                 "excerpt_text": (
                     "Stock basis increased by: (1) separately stated income items, (2) nonseparately "
                     "computed income, and (3) the excess of deductions for depletion over the basis "
                     "of the property subject to depletion. Stock basis decreased (but not below "
                     "zero) by: (1) distributions not includible in income (§1368), (2) separately "
                     "stated loss/deduction items, (3) nonseparately computed loss, (4) any expense "
                     "not deductible and not chargeable to capital account. Order of adjustments: "
                     "increase first, then decrease for distributions, then decrease for losses."
                 ),
                 "summary_text": "Basis up for income, down for distributions then losses. Ordering: income → distributions → losses.",
                 "is_key_excerpt": True,
                 "topic_tags": ["s_corp_basis"],
             },
         ],
         topics=["s_corp_basis"],
         form_links=[
             {"form_code": "7203", "link_type": "governs"},
             {"form_code": "1120S", "link_type": "informs"},
         ]),

    _irc("1368", "Distributions", "26 U.S.C. §1368",
         excerpts=[
             {
                 "excerpt_label": "§1368(a)-(c) — Distribution ordering",
                 "location_reference": "§1368(a)-(c)",
                 "excerpt_text": (
                     "S-Corp with no accumulated E&P (no C-Corp history): distributions are "
                     "nontaxable to the extent of stock basis, then treated as gain from sale of "
                     "stock. S-Corp with accumulated E&P: distributions are first from the "
                     "accumulated adjustments account (AAA) — nontaxable return of basis, then "
                     "from accumulated E&P — taxable as dividends, then from remaining AAA and "
                     "other adjustments account (OAA), then as gain from sale of stock."
                 ),
                 "summary_text": "No E&P: nontaxable to basis, then gain. With E&P: AAA first, then E&P as dividends.",
                 "is_key_excerpt": True,
                 "topic_tags": ["s_corp_distributions", "s_corporation"],
             },
         ],
         topics=["s_corp_distributions", "s_corporation"],
         form_links=[{"form_code": "1120S", "link_type": "governs"}]),

    _irc("1374", "Tax Imposed on Certain Built-in Gains", "26 U.S.C. §1374",
         excerpts=[
             {
                 "excerpt_label": "§1374 — Built-in gains tax",
                 "location_reference": "§1374",
                 "excerpt_text": (
                     "If an S corporation was formerly a C corporation (or received assets from a "
                     "C corporation in a tax-free transaction), a tax is imposed on the net "
                     "recognized built-in gain during the recognition period. The recognition period "
                     "is 5 years beginning on the date of the S election (or asset acquisition). "
                     "The tax rate is the highest corporate rate (21%). Net recognized built-in "
                     "gain is limited to the net unrealized built-in gain at the time of conversion."
                 ),
                 "summary_text": "BIG tax: 21% on built-in gains recognized within 5 years of C→S conversion.",
                 "is_key_excerpt": True,
                 "topic_tags": ["built_in_gains", "s_corporation"],
             },
         ],
         topics=["built_in_gains", "s_corporation"],
         form_links=[{"form_code": "1120S", "link_type": "governs"}]),

    _irc("1375", "Tax Imposed When Passive Investment Income of S Corp Exceeds 25%", "26 U.S.C. §1375",
         excerpts=[
             {
                 "excerpt_label": "§1375 — Excess net passive income tax",
                 "location_reference": "§1375",
                 "excerpt_text": (
                     "If an S corporation has accumulated earnings and profits from C-Corp years "
                     "and passive investment income exceeds 25% of gross receipts, a tax is imposed "
                     "on the excess net passive income at the highest corporate rate (21%). Passive "
                     "investment income includes royalties, rents, dividends, interest, annuities, "
                     "and gain from the sale of stock or securities. This tax can be avoided by "
                     "distributing all accumulated E&P."
                 ),
                 "summary_text": "21% tax on excess passive income (>25% of gross receipts) when S-Corp has C-Corp E&P.",
                 "is_key_excerpt": True,
                 "topic_tags": ["excess_passive_income", "s_corporation"],
             },
         ],
         topics=["excess_passive_income", "s_corporation"],
         form_links=[{"form_code": "1120S", "link_type": "governs"}]),
]


# ═══════════════════════════════════════════════════════════════════════════════
# Employment / Self-Employment
# ═══════════════════════════════════════════════════════════════════════════════

IRC_EMPLOYMENT = [
    _irc("1401", "Rate of Tax on Self-Employment Income", "26 U.S.C. §1401",
         excerpts=[
             {
                 "excerpt_label": "§1401(a)-(b) — SE tax rates",
                 "location_reference": "§1401(a)-(b)",
                 "excerpt_text": (
                     "Self-employment tax consists of: (a) Old-Age, Survivors, and Disability "
                     "Insurance (OASDI): 12.4% on self-employment income up to the OASDI wage "
                     "base ($176,100 for 2025), and (b) Hospital Insurance (Medicare): 2.9% on "
                     "all self-employment income, with no cap. Total: 15.3% up to the wage base, "
                     "2.9% above. An additional 0.9% Medicare tax applies on SE income above "
                     "$200,000 ($250,000 MFJ, $125,000 MFS) under §1401(b)(2)."
                 ),
                 "summary_text": "SE tax: 12.4% OASDI (up to $176,100) + 2.9% Medicare (no cap) + 0.9% additional Medicare.",
                 "is_key_excerpt": True,
                 "topic_tags": ["self_employment"],
             },
         ],
         topics=["self_employment"],
         form_links=[{"form_code": "1040SSE", "link_type": "governs"}]),

    _irc("1402", "Definitions — Self-Employment Income", "26 U.S.C. §1402",
         excerpts=[
             {
                 "excerpt_label": "§1402(a) — Net earnings from self-employment",
                 "location_reference": "§1402(a)",
                 "excerpt_text": (
                     "Net earnings from self-employment means gross income derived from any trade "
                     "or business carried on by the individual, less allowable deductions "
                     "attributable to such trade or business, plus the distributive share (whether "
                     "or not distributed) of income from any trade or business of a partnership of "
                     "which the individual is a member. Exclusions: (1) rental from real estate "
                     "(§1402(a)(1)) unless a real estate dealer, (2) dividends and interest "
                     "(unless a dealer), (3) gain or loss from disposition of property that is not "
                     "inventory, (4) net earnings of less than $400. Limited partners receive "
                     "guaranteed payments only as SE income."
                 ),
                 "summary_text": "SE income = business net income + partnership distributive share. Excludes rents, dividends, capital gains.",
                 "is_key_excerpt": True,
                 "topic_tags": ["self_employment"],
             },
         ],
         topics=["self_employment"],
         form_links=[
             {"form_code": "1040SSE", "link_type": "governs"},
             {"form_code": "1040SC", "link_type": "informs"},
         ]),

    _irc("3101", "Rate of Tax — FICA Employee", "26 U.S.C. §3101",
         excerpts=[
             {
                 "excerpt_label": "§3101-3102 — Employee FICA and Additional Medicare",
                 "location_reference": "§3101-3102",
                 "excerpt_text": (
                     "Employee FICA: 6.2% OASDI on wages up to the Social Security wage base "
                     "($176,100 for 2025), plus 1.45% Medicare on all wages. Additional Medicare "
                     "Tax (§3101(b)(2)): 0.9% on wages exceeding $200,000 ($250,000 MFJ, "
                     "$125,000 MFS). The employer does not match the additional 0.9%. The employer "
                     "share (§3111) is 6.2% OASDI + 1.45% Medicare."
                 ),
                 "summary_text": "Employee: 6.2% OASDI + 1.45% HI + 0.9% additional Medicare. Employer matches base rates only.",
                 "is_key_excerpt": True,
                 "topic_tags": ["fica"],
             },
         ],
         topics=["fica"],
         form_links=[{"form_code": "8959", "link_type": "informs"}]),
]


# ═══════════════════════════════════════════════════════════════════════════════
# Credits
# ═══════════════════════════════════════════════════════════════════════════════

IRC_CREDITS = [
    _irc("21", "Expenses for Household and Dependent Care Services", "26 U.S.C. §21",
         excerpts=[
             {
                 "excerpt_label": "§21(a)-(c) — Credit computation",
                 "location_reference": "§21(a)-(c)",
                 "excerpt_text": (
                     "A credit is allowed for employment-related expenses paid for the care of a "
                     "qualifying individual (child under 13, disabled spouse or dependent) to "
                     "enable the taxpayer to be gainfully employed. The credit is a percentage "
                     "(20%-35%, based on AGI) of employment-related expenses up to $3,000 for one "
                     "qualifying individual or $6,000 for two or more. The percentage decreases "
                     "from 35% by one percentage point for each $2,000 of AGI above $15,000, down "
                     "to a minimum of 20% at AGI above $43,000."
                 ),
                 "summary_text": "20-35% credit on up to $3K/$6K of dependent care expenses. Percentage decreases with AGI.",
                 "is_key_excerpt": True,
                 "topic_tags": ["child_dependent_care"],
             },
         ],
         topics=["child_dependent_care"],
         form_links=[{"form_code": "2441", "link_type": "governs"}]),

    _irc("25A", "Education Credits", "26 U.S.C. §25A",
         excerpts=[
             {
                 "excerpt_label": "§25A(b)-(c) — American Opportunity and Lifetime Learning",
                 "location_reference": "§25A(b)-(c)",
                 "excerpt_text": (
                     "American Opportunity Tax Credit (§25A(b)): 100% of first $2,000 plus 25% of "
                     "next $2,000 = maximum $2,500 per eligible student. Available for first 4 years "
                     "of postsecondary education. 40% is refundable ($1,000 max). Phase-out: "
                     "$80,000-$90,000 single, $160,000-$180,000 MFJ. Lifetime Learning Credit "
                     "(§25A(c)): 20% of up to $10,000 of qualified tuition = maximum $2,000 per "
                     "return (not per student). No limit on years claimed. Nonrefundable. "
                     "Phase-out: $80,000-$90,000 single, $160,000-$180,000 MFJ (2025 amounts)."
                 ),
                 "summary_text": "AOTC: $2,500/student (40% refundable), 4 years. LLC: $2,000/return, unlimited years.",
                 "is_key_excerpt": True,
                 "topic_tags": ["education_credits"],
             },
         ],
         topics=["education_credits"],
         form_links=[{"form_code": "8863", "link_type": "governs"}]),

    _irc("36B", "Refundable Credit for Coverage Under a Qualified Health Plan", "26 U.S.C. §36B",
         excerpts=[
             {
                 "excerpt_label": "§36B(a)-(c) — Premium tax credit",
                 "location_reference": "§36B(a)-(c)",
                 "excerpt_text": (
                     "A refundable credit is allowed for applicable taxpayers who enroll in one or "
                     "more qualified health plans through a Health Insurance Marketplace. The credit "
                     "equals the sum of the premium assistance amounts for each coverage month. "
                     "Premium assistance amount = lesser of: (A) the monthly premiums for the "
                     "qualified health plan, or (B) the excess of the adjusted monthly premium for "
                     "the applicable second lowest cost silver plan (benchmark) over 1/12 of the "
                     "product of the applicable percentage and household income. Household income "
                     "must be between 100%-400% of FPL (enhanced subsidies may modify this)."
                 ),
                 "summary_text": "PTC: refundable credit for Marketplace coverage. Based on benchmark silver plan vs. income.",
                 "is_key_excerpt": True,
                 "topic_tags": ["premium_tax_credit"],
             },
         ],
         topics=["premium_tax_credit"],
         form_links=[{"form_code": "8962", "link_type": "governs"}]),

    _irc("38", "General Business Credit", "26 U.S.C. §38",
         excerpts=[
             {
                 "excerpt_label": "§38(a)-(c) — Aggregation and components",
                 "location_reference": "§38(a)-(c)",
                 "excerpt_text": (
                     "The general business credit is the sum of the current year business credit "
                     "plus the business credit carryforwards and carrybacks. Component credits "
                     "include: investment credit (§46), work opportunity credit (§51), alcohol "
                     "fuels credit, research credit (§41), low-income housing credit (§42), "
                     "enhanced oil recovery credit, disabled access credit (§44), renewable "
                     "electricity production credit (§45), employer Social Security credit, "
                     "small employer pension startup credit (§45E), and many others. "
                     "Credit limitation: generally cannot exceed net income tax minus the greater "
                     "of (1) tentative minimum tax, or (2) 25% of net regular tax liability above "
                     "$25,000. Carryback: 1 year. Carryforward: 20 years."
                 ),
                 "summary_text": "Aggregates all business credits. Limited by tax liability. 1-year back, 20-year forward.",
                 "is_key_excerpt": True,
                 "topic_tags": ["form_3800"],
             },
         ],
         topics=["form_3800"],
         form_links=[{"form_code": "3800", "link_type": "governs"}]),

    _irc("41", "Credit for Increasing Research Activities", "26 U.S.C. §41",
         excerpts=[
             {
                 "excerpt_label": "§41(a)-(c) — Research credit computation",
                 "location_reference": "§41(a)-(c)",
                 "excerpt_text": (
                     "A credit is allowed for qualified research expenses in excess of a base "
                     "amount. The regular credit is 20% of qualified research expenses exceeding "
                     "a base amount (computed using a fixed-base percentage of average gross "
                     "receipts). Alternative simplified credit (ASC): 14% of qualified research "
                     "expenses exceeding 50% of average qualified research expenses for the 3 "
                     "preceding years. Small businesses (≤$5M gross receipts, ≤5 years old) may "
                     "elect to apply up to $500,000 of the credit against payroll tax."
                 ),
                 "summary_text": "R&D credit: 20% regular or 14% ASC. Small business payroll tax offset up to $500K.",
                 "is_key_excerpt": True,
                 "topic_tags": ["research_credit"],
             },
         ],
         topics=["research_credit"],
         form_links=[{"form_code": "3800", "link_type": "informs"}]),

    _irc("469", "Passive Activity Losses and Credits Limited", "26 U.S.C. §469",
         excerpts=[
             {
                 "excerpt_label": "§469(a)-(c) — Passive activity loss limitation",
                 "location_reference": "§469(a)-(c)",
                 "excerpt_text": (
                     "Passive activity losses are not allowed against nonpassive income. A passive "
                     "activity is any trade or business in which the taxpayer does not materially "
                     "participate. Rental activities are generally treated as passive regardless of "
                     "participation. Material participation: individual participates for more than "
                     "500 hours, or constitutes substantially all of the participation, or "
                     "participates for more than 100 hours and no other individual participates more."
                 ),
                 "summary_text": "Passive losses only offset passive income. 500-hour material participation test. Rental = passive.",
                 "is_key_excerpt": True,
                 "topic_tags": ["passive_activity"],
             },
             {
                 "excerpt_label": "§469(i) — $25K rental exception",
                 "location_reference": "§469(i)",
                 "excerpt_text": (
                     "A natural person may offset up to $25,000 of nonpassive income with losses "
                     "from rental real estate activities in which the taxpayer actively participates. "
                     "The $25,000 allowance is reduced by 50% of the amount by which AGI exceeds "
                     "$100,000 and is fully phased out at $150,000 AGI. Active participation "
                     "requires a 10% or more ownership interest and involvement in management "
                     "decisions (lower standard than material participation)."
                 ),
                 "summary_text": "$25K rental loss allowance (active participation). Phases out at $100K-$150K AGI.",
                 "is_key_excerpt": True,
                 "topic_tags": ["passive_activity", "rental_income"],
             },
         ],
         topics=["passive_activity", "rental_income"],
         form_links=[
             {"form_code": "8582", "link_type": "governs"},
             {"form_code": "8825", "link_type": "informs"},
             {"form_code": "1040SE", "link_type": "informs"},
         ]),

    _irc("465", "Deductions Limited to Amount at Risk", "26 U.S.C. §465",
         excerpts=[
             {
                 "excerpt_label": "§465(a)-(b) — At-risk limitation",
                 "location_reference": "§465(a)-(b)",
                 "excerpt_text": (
                     "A taxpayer engaged in an activity to which this section applies shall be "
                     "allowed deductions only to the extent of the aggregate amount the taxpayer "
                     "has at risk at the close of the taxable year. At-risk amount includes: "
                     "(1) money contributed, (2) adjusted basis of property contributed, "
                     "(3) amounts borrowed for which the taxpayer is personally liable, "
                     "(4) amounts borrowed secured by property (other than property used in the "
                     "activity) pledged as security. NOT at risk: nonrecourse financing (except "
                     "qualified nonrecourse financing for real estate — §465(b)(6))."
                 ),
                 "summary_text": "Losses limited to at-risk amount. At-risk = cash + basis contributed + recourse debt.",
                 "is_key_excerpt": True,
                 "topic_tags": ["at_risk"],
             },
         ],
         topics=["at_risk"],
         form_links=[{"form_code": "6198", "link_type": "governs"}]),

    # Additional credits — brief entries
    _irc("1411", "Net Investment Income Tax", "26 U.S.C. §1411",
         excerpts=[
             {
                 "excerpt_label": "§1411(a)-(c) — 3.8% NIIT",
                 "location_reference": "§1411(a)-(c)",
                 "excerpt_text": (
                     "A tax equal to 3.8% is imposed on the lesser of: (A) net investment income, "
                     "or (B) the excess of modified adjusted gross income over the threshold amount. "
                     "Threshold amounts: $250,000 (MFJ), $200,000 (single), $125,000 (MFS). Net "
                     "investment income includes: interest, dividends, capital gains, rents, "
                     "royalties, nonqualified annuities, passive activity income, and income from "
                     "trading financial instruments or commodities. EXCLUDES: wages, SE income, "
                     "active trade/business income, Social Security, tax-exempt interest, and "
                     "distributions from qualified retirement plans."
                 ),
                 "summary_text": "3.8% NIIT on investment income above $200K/$250K MAGI. Excludes wages, SE, active business.",
                 "is_key_excerpt": True,
                 "topic_tags": ["niit"],
             },
         ],
         topics=["niit"],
         form_links=[{"form_code": "8960", "link_type": "governs"}]),

    _irc("408", "Individual Retirement Accounts", "26 U.S.C. §408",
         excerpts=[
             {
                 "excerpt_label": "§408 and §408A — Traditional and Roth IRAs",
                 "location_reference": "§408, §408A",
                 "excerpt_text": (
                     "Traditional IRA (§408): contributions up to $7,000 ($8,000 if age 50+, 2025). "
                     "Deductibility phased out if covered by employer plan: $79,000-$89,000 single, "
                     "$126,000-$146,000 MFJ (2025). Distributions taxed as ordinary income; 10% "
                     "early withdrawal penalty before age 59½ (exceptions apply). RMDs begin at "
                     "age 73 (SECURE 2.0). Roth IRA (§408A): contributions not deductible; qualified "
                     "distributions are tax-free. Contribution phase-out: $150,000-$165,000 single, "
                     "$236,000-$246,000 MFJ (2025). No RMDs during owner's lifetime (SECURE 2.0)."
                 ),
                 "summary_text": "Traditional: $7K/$8K, deductible (income limits). Roth: not deductible, tax-free distributions.",
                 "is_key_excerpt": True,
                 "topic_tags": ["ira"],
             },
         ],
         topics=["ira"],
         form_links=[{"form_code": "8606", "link_type": "governs"}]),

    _irc("528", "Certain Homeowners Associations", "26 U.S.C. §528",
         excerpts=[
             {
                 "excerpt_label": "§528 — HOA tax treatment",
                 "location_reference": "§528",
                 "excerpt_text": (
                     "A homeowners association may elect to be taxed under §528 by filing Form "
                     "1120-H. Exempt function income (dues, assessments from members for exempt "
                     "purposes) is excluded from gross income. Taxable income (interest, rental "
                     "income from non-members, etc.) is taxed at 30% for HOAs (or 32% for timeshare "
                     "associations). No deductions are allowed against exempt function income. "
                     "The association must be organized and operated primarily for the acquisition, "
                     "construction, management, maintenance, and care of common areas."
                 ),
                 "summary_text": "HOA elects Form 1120-H: exempt function income excluded, taxable income at 30%/32%.",
                 "is_key_excerpt": True,
                 "topic_tags": ["homeowners_association"],
             },
         ],
         topics=["homeowners_association"],
         form_links=[{"form_code": "1120H", "link_type": "governs"}]),

    _irc("11", "Tax Imposed — Corporate", "26 U.S.C. §11",
         excerpts=[
             {
                 "excerpt_label": "§11(a)-(b) — Corporate tax rate",
                 "location_reference": "§11(a)-(b)",
                 "excerpt_text": (
                     "A tax is hereby imposed for each taxable year on the taxable income of every "
                     "corporation. The amount of the tax is 21% of taxable income. This flat 21% "
                     "rate was established by the Tax Cuts and Jobs Act of 2017, replacing the "
                     "prior graduated rate structure (15%-35%). The rate applies to all taxable "
                     "income regardless of amount."
                 ),
                 "summary_text": "Flat 21% corporate tax rate on all taxable income (TCJA, permanent).",
                 "is_key_excerpt": True,
                 "topic_tags": ["corporate_tax"],
             },
         ],
         topics=["corporate_tax", "c_corporation"],
         form_links=[{"form_code": "1120", "link_type": "governs"}]),

    _irc("243", "Dividends Received Deduction", "26 U.S.C. §243",
         excerpts=[
             {
                 "excerpt_label": "§243(a)-(c) — DRD percentages",
                 "location_reference": "§243(a)-(c)",
                 "excerpt_text": (
                     "A corporation is allowed a deduction for dividends received from domestic "
                     "corporations. The deduction is: (1) 50% for dividends from corporations where "
                     "the recipient owns less than 20% of stock; (2) 65% for dividends from "
                     "20%-or-more-owned corporations; (3) 100% for dividends from members of the "
                     "same affiliated group (80%+ ownership). The deduction is generally limited to "
                     "a corresponding percentage of taxable income (without regard to NOL, DRD, or "
                     "certain other deductions), but this limitation does not apply if the "
                     "corporation has a net operating loss for the year."
                 ),
                 "summary_text": "DRD: 50% (<20% owned), 65% (≥20%), 100% (affiliated group). Taxable income limitation.",
                 "is_key_excerpt": True,
                 "topic_tags": ["dividends_received", "c_corporation"],
             },
         ],
         topics=["dividends_received", "c_corporation"],
         form_links=[{"form_code": "1120", "link_type": "governs"}]),

    _irc("248", "Organizational Expenditures", "26 U.S.C. §248",
         excerpts=[
             {
                 "excerpt_label": "§248 — Corporation organizational costs",
                 "location_reference": "§248",
                 "excerpt_text": (
                     "A corporation may elect to deduct up to $5,000 of organizational expenditures "
                     "in the taxable year in which the corporation begins business. The $5,000 is "
                     "reduced (but not below zero) by the amount by which organizational expenditures "
                     "exceed $50,000. The remainder is amortized ratably over the 180-month period "
                     "beginning with the month in which the corporation begins business. "
                     "Organizational expenditures include: legal fees for charter/articles, "
                     "accounting fees for setting up books, organizational meeting expenses, "
                     "and filing fees with the state."
                 ),
                 "summary_text": "$5K immediate deduction (reduced if >$50K total), remainder over 180 months. Same structure as §195.",
                 "is_key_excerpt": True,
                 "topic_tags": ["c_corporation", "start_up_costs"],
             },
         ],
         topics=["c_corporation", "start_up_costs"],
         form_links=[{"form_code": "1120", "link_type": "informs"}]),

    _irc("1", "Tax Imposed — Individual Rates", "26 U.S.C. §1",
         excerpts=[
             {
                 "excerpt_label": "§1(a)-(j) — Individual tax rate brackets",
                 "location_reference": "§1(a)-(j)",
                 "excerpt_text": (
                     "Individual tax is imposed at graduated rates on taxable income: 10%, 12%, "
                     "22%, 24%, 32%, 35%, and 37% (TCJA rates, 2018-2025). Bracket thresholds are "
                     "indexed annually for inflation. Separate rate schedules apply for: (a) married "
                     "filing jointly, (b) heads of households, (c) unmarried individuals, "
                     "(d) married filing separately, (e) estates and trusts. Net capital gain is "
                     "taxed at preferential rates under §1(h): 0%, 15%, or 20% based on income level, "
                     "with 25% for unrecaptured §1250 gain and 28% for collectibles gain."
                 ),
                 "summary_text": "7 brackets (10%-37%). Capital gains: 0%/15%/20%. Unrecaptured §1250 = 25%, collectibles = 28%.",
                 "is_key_excerpt": True,
                 "topic_tags": ["individual", "capital_gains"],
             },
         ],
         topics=["individual", "capital_gains"],
         form_links=[{"form_code": "1040", "link_type": "governs"}]),

    _irc("151", "Allowance of Deductions for Personal Exemptions", "26 U.S.C. §151",
         excerpts=[
             {
                 "excerpt_label": "§151-152 — Personal exemptions and dependents",
                 "location_reference": "§151-152",
                 "excerpt_text": (
                     "Personal exemption deduction is $0 for tax years 2018-2025 (suspended by "
                     "TCJA). However, §151/§152 dependency definitions remain relevant for: child "
                     "tax credit, earned income credit, head of household filing status, and "
                     "dependent care credit. Qualifying child: under 19 (24 if student), lives with "
                     "taxpayer more than half the year, does not provide over half own support. "
                     "Qualifying relative: gross income under $5,050 (2025), taxpayer provides "
                     "over half support, any relationship or member of household."
                 ),
                 "summary_text": "Personal exemption suspended 2018-2025 (TCJA). Dependency tests still matter for credits.",
                 "is_key_excerpt": True,
                 "topic_tags": ["individual"],
             },
         ],
         topics=["individual"],
         form_links=[{"form_code": "1040", "link_type": "governs"}]),

    _irc("175", "Soil and Water Conservation Expenditures", "26 U.S.C. §175",
         excerpts=[
             {
                 "excerpt_label": "§175 — Farm conservation deduction",
                 "location_reference": "§175",
                 "excerpt_text": (
                     "A taxpayer engaged in the business of farming may elect to deduct soil and "
                     "water conservation expenditures that are otherwise chargeable to capital "
                     "account (and are not otherwise deductible). The deduction is limited to 25% "
                     "of gross income derived from farming during the taxable year. Expenditures "
                     "include: treatment or moving of earth, construction of terraces, outlets, "
                     "dams, waterways, ponds, and similar projects approved by USDA."
                 ),
                 "summary_text": "Farm conservation costs deductible up to 25% of farm gross income.",
                 "is_key_excerpt": True,
                 "topic_tags": ["farm_income"],
             },
         ],
         topics=["farm_income"],
         form_links=[{"form_code": "1040SF", "link_type": "informs"}]),
]


# ═══════════════════════════════════════════════════════════════════════════════
# Combined export
# ═══════════════════════════════════════════════════════════════════════════════

ALL_IRC_SECTIONS = (
    IRC_INCOME_DEDUCTION
    + IRC_PROPERTY
    + IRC_PARTNERSHIP
    + IRC_S_CORP
    + IRC_EMPLOYMENT
    + IRC_CREDITS
)
