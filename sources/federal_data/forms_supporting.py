"""IRS form instruction sources for commonly used supporting forms."""

from sources.federal_data.forms_1120s import _instr


SOURCES_SUPPORTING = [
    # ───────────────────────────────────────────────────────────────────────
    # Form 2106 — Employee Business Expenses
    # ───────────────────────────────────────────────────────────────────────
    _instr(
        "IRS_2025_2106_INSTR",
        "Instructions for Form 2106 — Employee Business Expenses",
        "Form 2106 Instructions (2025)",
        "https://www.irs.gov/instructions/i2106",
        "1040",
        excerpts=[
            {
                "excerpt_label": "Who can file — post-TCJA limitations",
                "location_reference": "General Instructions",
                "excerpt_text": (
                    "For 2018 through 2025, unreimbursed employee business expenses are generally "
                    "NOT deductible (TCJA suspended miscellaneous itemized deductions subject to the "
                    "2% AGI floor). Form 2106 may still be used ONLY by: (1) Armed Forces reservists, "
                    "(2) qualified performing artists, (3) fee-basis state or local government "
                    "officials, and (4) employees with impairment-related work expenses. These "
                    "eligible employees report their deduction on Schedule 1 line 12, not on "
                    "Schedule A. Allowable expenses include transportation, travel, meals (50%), "
                    "and other business expenses."
                ),
                "summary_text": "Post-TCJA: only reservists, performing artists, fee-basis officials, disability can use 2106.",
                "is_key_excerpt": True,
                "topic_tags": ["employee_expenses", "form_2106"],
            },
        ],
        topics=["form_2106", "employee_expenses"],
        form_links=[{"form_code": "2106", "link_type": "governs"}],
    ),

    # ───────────────────────────────────────────────────────────────────────
    # Form 2441 — Child and Dependent Care Expenses
    # ───────────────────────────────────────────────────────────────────────
    _instr(
        "IRS_2025_2441_INSTR",
        "Instructions for Form 2441 — Child and Dependent Care Expenses",
        "Form 2441 Instructions (2025)",
        "https://www.irs.gov/instructions/i2441",
        "1040",
        excerpts=[
            {
                "excerpt_label": "Qualifying individuals and credit computation",
                "location_reference": "General and Line Instructions",
                "excerpt_text": (
                    "The credit is for expenses paid for the care of qualifying individuals to "
                    "enable you to work (or look for work). Qualifying individuals: (1) your "
                    "qualifying child under age 13 whom you can claim as a dependent, (2) your "
                    "spouse who is physically or mentally incapable of self-care and lived with you "
                    "more than half the year, (3) any person incapable of self-care who is your "
                    "dependent (or would be except for income/joint return tests). Maximum expenses: "
                    "$3,000 for one qualifying individual, $6,000 for two or more. Credit percentage: "
                    "35% for AGI up to $15,000, reduced by 1% for each $2,000 of AGI above $15,000, "
                    "minimum 20% for AGI above $43,000. The credit is nonrefundable. Expenses must "
                    "be reduced by any dependent care benefits excluded from income (up to $5,000)."
                ),
                "summary_text": "Credit: 20-35% of $3K/$6K expenses. Qualifying: child <13, disabled spouse/dependent. Nonrefundable.",
                "is_key_excerpt": True,
                "topic_tags": ["child_dependent_care", "form_2441"],
            },
        ],
        topics=["form_2441", "child_dependent_care"],
        form_links=[{"form_code": "2441", "link_type": "governs"}],
    ),

    # ───────────────────────────────────────────────────────────────────────
    # Form 3800 — General Business Credit
    # ───────────────────────────────────────────────────────────────────────
    _instr(
        "IRS_2025_3800_INSTR",
        "Instructions for Form 3800 — General Business Credit",
        "Form 3800 Instructions (2025)",
        "https://www.irs.gov/instructions/i3800",
        "shared",
        excerpts=[
            {
                "excerpt_label": "How credits are aggregated",
                "location_reference": "General Instructions",
                "excerpt_text": (
                    "Form 3800 aggregates all general business credits into a single credit with a "
                    "unified limitation. Component credits include: investment credit (§46), work "
                    "opportunity credit (§51), biofuel producer credit, research credit (§41), "
                    "low-income housing credit (§42), disabled access credit (§44), renewable "
                    "electricity production credit (§45), Indian employment credit, orphan drug "
                    "credit, new markets credit, small employer pension startup credit (§45E), "
                    "employer-provided childcare credit (§45F), energy credits (§48, §45Q, §45V, "
                    "§45X, §45Y, §45Z), and many others."
                ),
                "summary_text": "Form 3800 aggregates 30+ business credits into unified credit with single limitation.",
                "is_key_excerpt": True,
                "topic_tags": ["form_3800"],
            },
            {
                "excerpt_label": "Credit limitation and carryback/carryforward",
                "location_reference": "Part II Instructions",
                "excerpt_text": (
                    "The general business credit cannot exceed the net income tax minus the greater "
                    "of: (1) the tentative minimum tax, or (2) 25% of net regular tax liability "
                    "exceeding $25,000. Certain credits are not subject to this limitation "
                    "(e.g., certain energy credits elected under §6417). Credits that exceed the "
                    "limitation are carried back 1 year and then forward 20 years (FIFO ordering). "
                    "Special ordering: credits from carryforward years are used first, then current "
                    "year credits, then carryback credits."
                ),
                "summary_text": "Limitation: net tax minus greater of TMT or 25% of net tax > $25K. Carryback 1yr, forward 20yr (FIFO).",
                "is_key_excerpt": True,
                "topic_tags": ["form_3800"],
            },
        ],
        topics=["form_3800"],
        form_links=[
            {"form_code": "3800", "link_type": "governs"},
            {"form_code": "1120", "link_type": "informs"},
            {"form_code": "1120S", "link_type": "informs"},
            {"form_code": "1065", "link_type": "informs"},
        ],
    ),

    # ───────────────────────────────────────────────────────────────────────
    # Form 4684 — Casualties and Thefts
    # ───────────────────────────────────────────────────────────────────────
    _instr(
        "IRS_2025_4684_INSTR",
        "Instructions for Form 4684 — Casualties and Thefts",
        "Form 4684 Instructions (2025)",
        "https://www.irs.gov/instructions/i4684",
        "shared",
        excerpts=[
            {
                "excerpt_label": "Casualty loss rules — federally declared disasters",
                "location_reference": "General Instructions",
                "excerpt_text": (
                    "A casualty is the damage, destruction, or loss of property resulting from an "
                    "identifiable event that is sudden, unexpected, or unusual — such as a flood, "
                    "hurricane, tornado, fire, earthquake, or volcanic eruption. A theft includes "
                    "larceny, robbery, embezzlement, extortion, and kidnapping for ransom. "
                    "For individuals: personal-use property casualty/theft losses are deductible "
                    "ONLY if attributable to a federally declared disaster (post-TCJA). Each loss "
                    "is reduced by $100, and total net losses must exceed 10% of AGI. Business "
                    "and income-producing property losses are fully deductible regardless of disaster "
                    "status. Section A: Personal-use property. Section B: Business and income-"
                    "producing property. The loss equals the lesser of the decrease in FMV or the "
                    "adjusted basis of the property, reduced by any insurance or reimbursement."
                ),
                "summary_text": "Personal: federally declared disaster only, $100 per event + 10% AGI floor. Business: fully deductible.",
                "is_key_excerpt": True,
                "topic_tags": ["casualty_theft", "form_4684"],
            },
        ],
        topics=["form_4684", "casualty_theft", "losses"],
        form_links=[{"form_code": "4684", "link_type": "governs"}],
    ),

    # ───────────────────────────────────────────────────────────────────────
    # Form 4835 — Farm Rental Income and Expenses
    # ───────────────────────────────────────────────────────────────────────
    _instr(
        "IRS_2025_4835_INSTR",
        "Instructions for Form 4835 — Farm Rental Income and Expenses",
        "Form 4835 Instructions (2025)",
        "https://www.irs.gov/instructions/i4835",
        "1040",
        excerpts=[
            {
                "excerpt_label": "Who files and how it differs from Schedule F",
                "location_reference": "General Instructions",
                "excerpt_text": (
                    "Use Form 4835 to report farm rental income and expenses if you are an "
                    "individual who received rental income based on crops or livestock produced by "
                    "a tenant, and you did NOT materially participate in the operation or management "
                    "of the farm. If you materially participated, use Schedule F instead. Farm "
                    "rental income reported on Form 4835 is generally NOT subject to self-employment "
                    "tax (§1402(a)(1) excludes rentals from real estate from SE income). However, "
                    "it may be subject to passive activity rules (§469). The NET (line 32) flows to "
                    "Schedule E line 40, and the GROSS (line 7) to Schedule E line 42 (the farming/"
                    "fishing reconciliation memo) — NOT to Schedule F. Expenses include insurance, "
                    "repairs, taxes, utilities, depreciation, and the landlord's share of production costs."
                ),
                "summary_text": "Form 4835: farm rental without material participation. Not SE income. Net → Sch E line 40; gross → Sch E line 42. Schedule F if participating.",
                "is_key_excerpt": True,
                "topic_tags": ["farm_rental", "form_4835"],
            },
        ],
        topics=["form_4835", "farm_rental", "farm_income"],
        form_links=[{"form_code": "4835", "link_type": "governs"}],
    ),

    # ───────────────────────────────────────────────────────────────────────
    # Form 6198 — At-Risk Limitations
    # ───────────────────────────────────────────────────────────────────────
    # Excerpts replaced 2026-07-12 (renumber unit #6): the old "At-risk computation"
    # row was a PARAPHRASE (the fabricated-excerpt class). This set is now VERBATIM
    # from i6198 (Rev. November 2025), pymupdf-extracted from the fetched irs.gov
    # PDF, and MIRRORS `_6198_INSTR_EXCERPTS` in specs/management/commands/
    # load_1120s_complete.py (the renumber loader upserts the same rows in prod —
    # keep the two lists in agreement).
    _instr(
        "IRS_2025_6198_INSTR",
        "Instructions for Form 6198 — At-Risk Limitations",
        "Instructions for Form 6198 (Rev. November 2025)",
        "https://www.irs.gov/instructions/i6198",
        "shared",
        excerpts=[
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
                "topic_tags": ["at_risk", "form_6198"],
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
                "topic_tags": ["at_risk", "form_6198"],
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
                "topic_tags": ["at_risk", "form_6198"],
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
                "topic_tags": ["at_risk", "form_6198"],
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
                "topic_tags": ["at_risk", "form_6198"],
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
                "topic_tags": ["at_risk", "form_6198"],
            },
        ],
        topics=["form_6198", "at_risk"],
        form_links=[{"form_code": "6198", "link_type": "governs"}],
    ),

    # ───────────────────────────────────────────────────────────────────────
    # Form 6252 — Installment Sale Income
    # ───────────────────────────────────────────────────────────────────────
    _instr(
        "IRS_2025_6252_INSTR",
        "Instructions for Form 6252 — Installment Sale Income",
        "Form 6252 Instructions (2025)",
        "https://www.irs.gov/instructions/i6252",
        "shared",
        excerpts=[
            {
                "excerpt_label": "Installment method rules",
                "location_reference": "General Instructions",
                "excerpt_text": (
                    "Use Form 6252 to report income from an installment sale — a sale of property "
                    "where you receive at least one payment after the year of sale. The installment "
                    "method allows you to defer gain by reporting a portion of the gain as each "
                    "payment is received. Gross profit percentage = (gross profit / contract price) "
                    "× 100. Each year: taxable gain = payments received × gross profit percentage. "
                    "The installment method does NOT apply to: sales of inventory, sales of stocks "
                    "or securities traded on an established market, or dealer dispositions. You may "
                    "elect out of the installment method on a timely filed return."
                ),
                "summary_text": "Installment sale: defer gain over payments. Gain = payment × (gross profit / contract price).",
                "is_key_excerpt": True,
                "topic_tags": ["installment_sale", "form_6252"],
            },
            {
                "excerpt_label": "Related party and interest rules",
                "location_reference": "Part III and Special Rules",
                "excerpt_text": (
                    "Related party sales (§453(e)): if you sell to a related person and that person "
                    "disposes of the property within 2 years, you must recognize gain in the year of "
                    "the second disposition (up to the amount of remaining gain). Related persons: "
                    "family members (spouse, children, grandchildren, parents), controlled "
                    "corporations/partnerships (>50% ownership). §453A interest charge: if the "
                    "sale price exceeds $150,000 and the total outstanding installment obligations "
                    "arising during and outstanding at year-end exceeds $5 million, interest is "
                    "charged on the deferred tax liability at the underpayment rate."
                ),
                "summary_text": "Related party: 2-year resale acceleration. §453A: interest charge if sale >$150K and obligations >$5M.",
                "is_key_excerpt": True,
                "topic_tags": ["installment_sale", "related_party"],
            },
        ],
        topics=["form_6252", "installment_sale"],
        form_links=[{"form_code": "6252", "link_type": "governs"}],
    ),

    # ───────────────────────────────────────────────────────────────────────
    # Form 8582 — Passive Activity Loss Limitations
    # ───────────────────────────────────────────────────────────────────────
    _instr(
        "IRS_2025_8582_INSTR",
        "Instructions for Form 8582 — Passive Activity Loss Limitations",
        "Form 8582 Instructions (2025)",
        "https://www.irs.gov/instructions/i8582",
        "1040",
        excerpts=[
            {
                "excerpt_label": "Passive activity rules overview",
                "location_reference": "General Instructions",
                "excerpt_text": (
                    "Form 8582 is used by individuals, estates, and trusts that have passive activity "
                    "losses or credits. A passive activity is any trade or business activity in which "
                    "you did not materially participate during the year. Rental activities are "
                    "treated as passive regardless of your participation, with two exceptions: "
                    "(1) real estate professionals (§469(c)(7)), and (2) the $25,000 special "
                    "allowance for active participation in rental real estate. Passive losses can "
                    "only offset passive income. Disallowed losses are suspended and carried forward "
                    "until you have passive income or completely dispose of the activity."
                ),
                "summary_text": "Passive losses only offset passive income. Rental = passive (exceptions: RE professional, $25K allowance).",
                "is_key_excerpt": True,
                "topic_tags": ["passive_activity", "form_8582"],
            },
            {
                "excerpt_label": "$25,000 rental real estate exception",
                "location_reference": "Worksheet 1 and 2",
                "excerpt_text": (
                    "If you actively participated in a rental real estate activity, you may be able "
                    "to deduct up to $25,000 of loss against nonpassive income. Active participation "
                    "requires: at least 10% ownership interest and involvement in management decisions "
                    "(approving tenants, terms, repairs, expenditures) — a lower standard than "
                    "material participation. The $25,000 allowance is reduced by 50% of AGI over "
                    "$100,000 and fully phased out at $150,000 AGI. Married filing separately: "
                    "generally $0 allowance (unless lived apart all year, then $12,500 phased out "
                    "at $50,000-$75,000)."
                ),
                "summary_text": "$25K rental exception: active participation + 10% ownership. Phases out $100K-$150K AGI.",
                "is_key_excerpt": True,
                "topic_tags": ["passive_activity", "rental_income"],
            },
            {
                "excerpt_label": "Material participation tests",
                "location_reference": "Active Participation / Material Participation",
                "excerpt_text": (
                    "Material participation — you participate on a regular, continuous, and "
                    "substantial basis. You materially participate if you meet ANY of these tests: "
                    "(1) more than 500 hours during the year, (2) your participation constituted "
                    "substantially all of the participation, (3) more than 100 hours and at least "
                    "as much as any other individual, (4) significant participation activities "
                    "aggregate to more than 500 hours, (5) materially participated in any 5 of the "
                    "prior 10 years, (6) personal service activity — materially participated in any "
                    "3 prior years, (7) all facts and circumstances (more than 100 hours, no one "
                    "else participated more). Grouping: taxpayers may group activities that form "
                    "an appropriate economic unit for measuring participation."
                ),
                "summary_text": "7 material participation tests. 500+ hours is most common. Grouping of activities allowed.",
                "is_key_excerpt": True,
                "topic_tags": ["passive_activity"],
            },
        ],
        topics=["form_8582", "passive_activity", "rental_income"],
        form_links=[{"form_code": "8582", "link_type": "governs"}],
    ),

    # ───────────────────────────────────────────────────────────────────────
    # Form 8606 — Nondeductible IRAs
    # ───────────────────────────────────────────────────────────────────────
    _instr(
        "IRS_2025_8606_INSTR",
        "Instructions for Form 8606 — Nondeductible IRAs",
        "Form 8606 Instructions (2025)",
        "https://www.irs.gov/instructions/i8606",
        "1040",
        excerpts=[
            {
                "excerpt_label": "Purpose and when to file",
                "location_reference": "General Instructions",
                "excerpt_text": (
                    "File Form 8606 if: (1) you made nondeductible contributions to a traditional "
                    "IRA, (2) you received distributions from a traditional, SEP, or SIMPLE IRA and "
                    "you have a cost basis (nondeductible contributions), (3) you converted a "
                    "traditional, SEP, or SIMPLE IRA to a Roth IRA, or (4) you received distributions "
                    "from a Roth IRA. Part I: Nondeductible contributions and basis tracking. "
                    "Part II: Roth IRA conversions — the taxable amount equals the conversion amount "
                    "minus the nontaxable portion (basis). Pro-rata rule: you cannot convert only "
                    "the after-tax portion — the taxable/nontaxable ratio is based on ALL your "
                    "traditional/SEP/SIMPLE IRAs. Part III: Distributions from Roth IRAs."
                ),
                "summary_text": "Track nondeductible IRA basis. Pro-rata rule applies to conversions. Parts for traditional, Roth, conversions.",
                "is_key_excerpt": True,
                "topic_tags": ["ira", "form_8606"],
            },
        ],
        topics=["form_8606", "ira"],
        form_links=[{"form_code": "8606", "link_type": "governs"}],
    ),

    # ───────────────────────────────────────────────────────────────────────
    # Form 8995 — QBI Deduction (Simplified)
    # ───────────────────────────────────────────────────────────────────────
    _instr(
        "IRS_2025_8995_INSTR",
        "Instructions for Form 8995 — Qualified Business Income Deduction Simplified Computation",
        "Form 8995 Instructions (2025)",
        "https://www.irs.gov/instructions/i8995",
        "1040",
        excerpts=[
            {
                "excerpt_label": "Simplified computation — who can use",
                "location_reference": "General Instructions",
                "excerpt_text": (
                    "Use Form 8995 if your taxable income before the QBI deduction is at or below "
                    "the threshold amount: $197,300 for all filing statuses other than MFJ, "
                    "$394,600 for MFJ (2025 amounts). Below the threshold, "
                    "there is no W-2 wage or UBIA limitation and no SSTB phase-out. The simplified "
                    "deduction is simply 20% of total QBI (the lesser of combined QBI or 20% of "
                    "taxable income minus net capital gain). If your taxable income exceeds the "
                    "threshold, you must use Form 8995-A instead."
                ),
                "summary_text": "Simplified 8995: below $197,300/$394,600. Deduction = 20% of QBI (no W-2/UBIA limits, no SSTB issue).",
                "is_key_excerpt": True,
                "topic_tags": ["qbi_deduction", "form_8995"],
            },
        ],
        topics=["form_8995", "qbi_deduction"],
        form_links=[{"form_code": "8995", "link_type": "governs"}],
    ),

    # ───────────────────────────────────────────────────────────────────────
    # Form 8995-A — QBI Deduction (Full Computation)
    # ───────────────────────────────────────────────────────────────────────
    _instr(
        "IRS_2025_8995A_INSTR",
        "Instructions for Form 8995-A — Qualified Business Income Deduction",
        "Form 8995-A Instructions (2025)",
        "https://www.irs.gov/instructions/i8995a",
        "1040",
        excerpts=[
            {
                "excerpt_label": "Full computation — W-2/UBIA limitations",
                "location_reference": "General Instructions",
                "excerpt_text": (
                    "Use Form 8995-A if taxable income exceeds the threshold ($197,300/$394,600 for "
                    "2025). The QBI deduction for each qualified trade or business is the lesser of: "
                    "(A) 20% of QBI from that business, or (B) the greater of: (i) 50% of W-2 wages "
                    "paid by the business, or (ii) 25% of W-2 wages plus 2.5% of UBIA (unadjusted "
                    "basis immediately after acquisition) of qualified property. The limitations are "
                    "phased in over a $50,000 range ($100,000 for MFJ) above the threshold."
                ),
                "summary_text": "Above threshold: QBI deduction limited to 50% W-2 or 25% W-2 + 2.5% UBIA. Phase-in over $50K/$100K.",
                "is_key_excerpt": True,
                "topic_tags": ["qbi_deduction", "form_8995"],
            },
            {
                "excerpt_label": "SSTB rules",
                "location_reference": "Schedule A (Form 8995-A)",
                "excerpt_text": (
                    "Specified Service Trades or Businesses (SSTBs): health, law, accounting, "
                    "actuarial science, performing arts, consulting, athletics, financial services, "
                    "brokerage services, or any trade or business where the principal asset is the "
                    "reputation or skill of one or more of its employees or owners. For taxpayers "
                    "with taxable income within the phase-in range above the threshold: a percentage "
                    "of the SSTB's QBI, W-2 wages, and UBIA is taken into account (decreasing from "
                    "100% to 0% over the $50K/$100K range). For taxable income above the full "
                    "phase-in: ZERO deduction for SSTBs. Engineering and architecture are specifically "
                    "excluded from the SSTB definition."
                ),
                "summary_text": "SSTBs phased out above threshold. Health, law, accounting, consulting, financial, athletics = SSTB. Not engineering/architecture.",
                "is_key_excerpt": True,
                "topic_tags": ["qbi_deduction"],
            },
        ],
        topics=["form_8995", "qbi_deduction"],
        form_links=[{"form_code": "8995A", "link_type": "governs"}],
    ),

    # ───────────────────────────────────────────────────────────────────────
    # Form 8863 — Education Credits
    # ───────────────────────────────────────────────────────────────────────
    _instr(
        "IRS_2025_8863_INSTR",
        "Instructions for Form 8863 — Education Credits",
        "Form 8863 Instructions (2025)",
        "https://www.irs.gov/instructions/i8863",
        "1040",
        excerpts=[
            {
                "excerpt_label": "American Opportunity and Lifetime Learning credits",
                "location_reference": "General Instructions",
                "excerpt_text": (
                    "American Opportunity Tax Credit (AOTC): per eligible student — 100% of the "
                    "first $2,000 + 25% of the next $2,000 = maximum $2,500. Available for the "
                    "first 4 years of postsecondary education. Student must be enrolled at least "
                    "half-time for at least one academic period. 40% refundable (up to $1,000). "
                    "MAGI phase-out: $80,000-$90,000 (single), $160,000-$180,000 (MFJ). "
                    "Lifetime Learning Credit (LLC): per tax return (not per student) — 20% of up "
                    "to $10,000 of qualified tuition and fees = maximum $2,000. No limit on number "
                    "of years claimed. Available for undergraduate, graduate, and professional degree "
                    "courses. Nonrefundable. Same MAGI phase-out as AOTC. Cannot claim both credits "
                    "for the same student in the same year."
                ),
                "summary_text": "AOTC: $2,500/student, 4 years, 40% refundable. LLC: $2,000/return, unlimited years, nonrefundable.",
                "is_key_excerpt": True,
                "topic_tags": ["education_credits", "form_8863"],
            },
        ],
        topics=["form_8863", "education_credits"],
        form_links=[{"form_code": "8863", "link_type": "governs"}],
    ),

    # ───────────────────────────────────────────────────────────────────────
    # Form 8962 — Premium Tax Credit
    # ───────────────────────────────────────────────────────────────────────
    _instr(
        "IRS_2025_8962_INSTR",
        "Instructions for Form 8962 — Premium Tax Credit (PTC)",
        "Form 8962 Instructions (2025)",
        "https://www.irs.gov/instructions/i8962",
        "1040",
        excerpts=[
            {
                "excerpt_label": "PTC calculation and reconciliation",
                "location_reference": "General Instructions",
                "excerpt_text": (
                    "The Premium Tax Credit helps eligible individuals and families cover the cost "
                    "of premiums for health insurance purchased through the Health Insurance "
                    "Marketplace. To be eligible: (1) enroll in a qualified health plan through the "
                    "Marketplace, (2) household income between 100% and 400% of the federal poverty "
                    "line (FPL) — enhanced subsidies through the Inflation Reduction Act may extend "
                    "or modify this range, (3) cannot be claimed as a dependent, (4) if married, "
                    "must file jointly. The credit equals the lesser of: (a) the premiums for the "
                    "qualified plan, or (b) the benchmark plan premium minus the expected "
                    "contribution (applicable percentage × household income). If advance payments "
                    "were received (APTC from Form 1095-A), the credit must be reconciled on Form "
                    "8962. Excess APTC must be repaid (subject to repayment caps based on income)."
                ),
                "summary_text": "PTC: Marketplace coverage. Credit = benchmark premium minus expected contribution. Reconcile APTC on 8962.",
                "is_key_excerpt": True,
                "topic_tags": ["premium_tax_credit", "form_8962"],
            },
        ],
        topics=["form_8962", "premium_tax_credit"],
        form_links=[{"form_code": "8962", "link_type": "governs"}],
    ),

    # ───────────────────────────────────────────────────────────────────────
    # Form 8959 — Additional Medicare Tax
    # ───────────────────────────────────────────────────────────────────────
    _instr(
        "IRS_2025_8959_INSTR",
        "Instructions for Form 8959 — Additional Medicare Tax",
        "Form 8959 Instructions (2025)",
        "https://www.irs.gov/instructions/i8959",
        "1040",
        excerpts=[
            {
                "excerpt_label": "Additional Medicare Tax computation",
                "location_reference": "General Instructions",
                "excerpt_text": (
                    "A 0.9% Additional Medicare Tax applies to: (1) Medicare wages (from W-2 box 5), "
                    "(2) railroad retirement (RRTA) compensation, and (3) self-employment income "
                    "that exceeds the threshold amount. Thresholds: $200,000 for single and HOH, "
                    "$250,000 for MFJ, $125,000 for MFS. The tax applies to the combined amount of "
                    "these income types above the threshold. Employers are required to withhold the "
                    "0.9% on wages exceeding $200,000 (regardless of filing status), but the actual "
                    "liability is computed on Form 8959 based on filing status thresholds. Any "
                    "excess withholding is credited against total tax liability."
                ),
                "summary_text": "0.9% Additional Medicare: wages + SE income > $200K (S), $250K (MFJ), $125K (MFS). Employer withholds at $200K.",
                "is_key_excerpt": True,
                "topic_tags": ["additional_medicare", "form_8959", "fica"],
            },
        ],
        topics=["form_8959", "additional_medicare", "fica"],
        form_links=[{"form_code": "8959", "link_type": "governs"}],
    ),

    # ───────────────────────────────────────────────────────────────────────
    # Form 8960 — Net Investment Income Tax
    # ───────────────────────────────────────────────────────────────────────
    _instr(
        "IRS_2025_8960_INSTR",
        "Instructions for Form 8960 — Net Investment Income Tax — Individuals, Estates, and Trusts",
        "Form 8960 Instructions (2025)",
        "https://www.irs.gov/instructions/i8960",
        "1040",
        excerpts=[
            {
                "excerpt_label": "NIIT computation and included income",
                "location_reference": "General Instructions",
                "excerpt_text": (
                    "The Net Investment Income Tax (NIIT) is 3.8% imposed on the lesser of: "
                    "(A) net investment income, or (B) the excess of modified adjusted gross income "
                    "(MAGI) over the threshold amount. Thresholds: $200,000 (single), $250,000 "
                    "(MFJ), $125,000 (MFS). Net investment income includes: (1) gross income from "
                    "interest, dividends, annuities, royalties, and rents (unless derived from an "
                    "active trade or business), (2) other gross income from passive activities, "
                    "(3) net gain from disposition of property (other than property held in an "
                    "active trade or business). NOT included: wages, self-employment income, "
                    "active business income (if materially participating), Social Security benefits, "
                    "tax-exempt interest, distributions from qualified retirement plans (401(k), "
                    "IRA), and Alaska Permanent Fund dividends."
                ),
                "summary_text": "NIIT: 3.8% on investment income above $200K/$250K MAGI. Includes interest, dividends, passive income, cap gains. Not wages/SE/active business.",
                "is_key_excerpt": True,
                "topic_tags": ["niit", "form_8960"],
            },
        ],
        topics=["form_8960", "niit"],
        form_links=[{"form_code": "8960", "link_type": "governs"}],
    ),
]
