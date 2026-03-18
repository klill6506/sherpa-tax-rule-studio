"""Authority sources needed by the 1120-S family spec loader.

Creates IRC sections and IRS instruction sources that don't already exist
in the federal_data modules. Sources already loaded by load_all_federal
are referenced by source_code — not duplicated here.
"""

# ── IRC sections not yet in irc_sections.py ─────────────────────────────────

NEW_IRC_SOURCES = [
    {
        "source_code": "IRC_179",
        "source_type": "code_section",
        "source_rank": "controlling",
        "jurisdiction_code": "FED",
        "title": "IRC §179 — Election to Expense Certain Depreciable Business Assets",
        "citation": "26 U.S.C. §179",
        "issuer": "Congress",
        "current_status": "active",
        "is_substantive_authority": True,
        "requires_human_review": True,
        "trust_score": 10.0,
        "notes": "OBBBA 2025 raised limits to $2,500,000/$4,000,000. GA does NOT conform.",
        "topics": ["section_179", "depreciation"],
        "excerpts": [
            {
                "excerpt_label": "§179(a)-(b) — Election and limitations",
                "location_reference": "§179(a)-(b)",
                "excerpt_text": (
                    "A taxpayer may elect to treat the cost of any section 179 property as an expense "
                    "not chargeable to capital account. The aggregate cost which may be taken into "
                    "account shall not exceed $2,500,000 (as amended by OBBBA 2025). This amount is "
                    "reduced dollar-for-dollar by the amount by which the cost of section 179 property "
                    "placed in service during the taxable year exceeds $4,000,000. The deduction is "
                    "also limited to the aggregate amount of taxable income derived from the active "
                    "conduct of any trade or business."
                ),
                "summary_text": "$2.5M limit, $4M phaseout (OBBBA 2025). Limited to business taxable income.",
                "is_key_excerpt": True,
                "topic_tags": ["section_179", "depreciation"],
            },
            {
                "excerpt_label": "§179(d)(4) — S-Corp/partnership passthrough",
                "location_reference": "§179(d)(4)",
                "excerpt_text": (
                    "In the case of an S corporation, the §179 limitations apply at both the "
                    "entity level and the shareholder level. The S corporation's §179 deduction "
                    "is a separately stated item that passes through to shareholders on Schedule K-1. "
                    "It is NOT deducted on the S corporation's page 1 in computing ordinary income."
                ),
                "summary_text": "§179 is separately stated for S-Corps — flows to K-1, NOT page 1 ordinary income.",
                "is_key_excerpt": True,
                "topic_tags": ["section_179", "s_corporation", "schedule_k1"],
            },
        ],
    },
    {
        "source_code": "IRC_168",
        "source_type": "code_section",
        "source_rank": "controlling",
        "jurisdiction_code": "FED",
        "title": "IRC §168 — Accelerated Cost Recovery System (MACRS)",
        "citation": "26 U.S.C. §168",
        "issuer": "Congress",
        "current_status": "active",
        "is_substantive_authority": True,
        "requires_human_review": True,
        "trust_score": 10.0,
        "notes": "OBBBA 2025 restored 100% bonus for assets acquired after 1/19/2025. 40% for prior acquisitions.",
        "topics": ["depreciation", "macrs", "bonus_depreciation"],
        "excerpts": [
            {
                "excerpt_label": "§168(a)-(b) — MACRS general rules",
                "location_reference": "§168(a)-(b)",
                "excerpt_text": (
                    "Property to which this section applies shall be treated as having a deduction "
                    "equal to the applicable depreciation method applied to the applicable recovery "
                    "period using the applicable convention. Recovery periods: 3-year, 5-year, 7-year, "
                    "10-year, 15-year, 20-year, 25-year, 27.5-year residential rental, 39-year "
                    "nonresidential real property. Methods: 200% declining balance (3-20yr personal), "
                    "150% declining balance (farm/ADS), straight-line (real property, ADS)."
                ),
                "summary_text": "MACRS: recovery periods 3-39yr, methods 200DB/150DB/SL, conventions HY/MQ/MM.",
                "is_key_excerpt": True,
                "topic_tags": ["depreciation", "macrs"],
            },
            {
                "excerpt_label": "§168(k) — Bonus depreciation (OBBBA 2025)",
                "location_reference": "§168(k)",
                "excerpt_text": (
                    "Under §168(k) as amended by OBBBA (signed July 4, 2025): 100% additional "
                    "first-year depreciation is allowed for qualified property acquired AND placed "
                    "in service after January 19, 2025. For property acquired before January 20, 2025 "
                    "(binding contract rule), the applicable percentage is 40%. The previous TCJA "
                    "phasedown (80%→60%→40%→20%→0%) is superseded for post-1/19/2025 acquisitions. "
                    "Georgia does NOT conform to §168(k) bonus depreciation."
                ),
                "summary_text": "OBBBA: 100% bonus for post-1/19/2025 acquisitions (permanent). 40% for prior. GA decoupled.",
                "is_key_excerpt": True,
                "topic_tags": ["bonus_depreciation", "depreciation"],
            },
        ],
    },
    {
        "source_code": "IRC_1222",
        "source_type": "code_section",
        "source_rank": "controlling",
        "jurisdiction_code": "FED",
        "title": "IRC §1222 — Other Terms Relating to Capital Gains and Losses",
        "citation": "26 U.S.C. §1222",
        "issuer": "Congress",
        "current_status": "active",
        "is_substantive_authority": True,
        "requires_human_review": True,
        "trust_score": 10.0,
        "topics": ["capital_gains", "holding_period"],
        "excerpts": [
            {
                "excerpt_label": "§1222 — ST/LT definitions",
                "location_reference": "§1222(1)-(4)",
                "excerpt_text": (
                    "Short-term capital gain: gain from the sale or exchange of a capital asset held "
                    "for not more than 1 year. Short-term capital loss: loss from same. Long-term "
                    "capital gain: gain from the sale or exchange of a capital asset held for more "
                    "than 1 year. Long-term capital loss: loss from same."
                ),
                "summary_text": "ST = held ≤1 year. LT = held >1 year.",
                "is_key_excerpt": True,
                "topic_tags": ["capital_gains", "holding_period"],
            },
        ],
    },
    {
        "source_code": "IRC_1377",
        "source_type": "code_section",
        "source_rank": "controlling",
        "jurisdiction_code": "FED",
        "title": "IRC §1377 — Definitions and Special Rule",
        "citation": "26 U.S.C. §1377",
        "issuer": "Congress",
        "current_status": "active",
        "is_substantive_authority": True,
        "requires_human_review": True,
        "trust_score": 10.0,
        "topics": ["s_corporation", "passthrough"],
        "excerpts": [
            {
                "excerpt_label": "§1377(a) — Pro rata share allocation",
                "location_reference": "§1377(a)",
                "excerpt_text": (
                    "Each shareholder's pro rata share of any item for any taxable year shall be "
                    "the sum of the amounts determined with respect to the shareholder by assigning "
                    "an equal portion of such item to each day of the taxable year, and then by "
                    "dividing that portion pro rata among the shares outstanding on such day. "
                    "Unlike partnerships, S corporations CANNOT make special allocations — all "
                    "items must be allocated per share per day."
                ),
                "summary_text": "Pro rata = per share per day. No special allocations allowed (unlike partnerships).",
                "is_key_excerpt": True,
                "topic_tags": ["s_corporation", "passthrough"],
            },
        ],
    },
]


# ── IRS instruction sources for forms not yet loaded ─────────────────────────

NEW_INSTRUCTION_SOURCES = [
    {
        "source_code": "IRS_2025_1120S_SCHD_INSTR",
        "source_type": "official_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "entity_type_code": "1120S",
        "title": "Instructions for Schedule D (Form 1120-S) — Capital Gains and Losses and Built-in Gains",
        "citation": "Schedule D (Form 1120-S) Instructions (2025)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/instructions/i1120ssd",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": True,
        "requires_human_review": False,
        "trust_score": 9.5,
        "topics": ["capital_gains", "form_1120s"],
        "excerpts": [
            {
                "excerpt_label": "General Instructions — who must file",
                "location_reference": "General Instructions",
                "excerpt_text": (
                    "Use Schedule D (Form 1120-S) to report the overall capital gains and losses "
                    "from transactions reported on Form 8949, Sales and Other Dispositions of Capital "
                    "Assets. Also use Schedule D to report the built-in gains tax under §1374 if the "
                    "corporation was formerly a C corporation. Do NOT report sales of business "
                    "property on Schedule D — use Form 4797."
                ),
                "summary_text": "Schedule D (1120-S): aggregate cap gains/losses from 8949. BIG tax (§1374). Not business property (use 4797).",
                "is_key_excerpt": True,
                "topic_tags": ["capital_gains", "form_1120s"],
            },
            {
                "excerpt_label": "Part I — Short-term and Part II — Long-term",
                "location_reference": "Parts I-II Instructions",
                "excerpt_text": (
                    "Part I: Short-term capital gains and losses — assets held 1 year or less. "
                    "Report totals from Form 8949 Parts I (categories A, B, C for entities). "
                    "Part II: Long-term capital gains and losses — assets held more than 1 year. "
                    "Report totals from Form 8949 Parts II (categories D, E, F for entities). "
                    "Net short-term capital gain/loss flows to Schedule K line 7 (then K-1 Box 7). "
                    "Net long-term capital gain/loss flows to Schedule K line 8a (then K-1 Box 8a)."
                ),
                "summary_text": "ST→K Line 7, LT→K Line 8a. From Form 8949 categories.",
                "is_key_excerpt": True,
                "topic_tags": ["capital_gains", "schedule_k1"],
            },
            {
                "excerpt_label": "Part III — Built-in gains tax",
                "location_reference": "Part III Instructions",
                "excerpt_text": (
                    "Part III applies only to S corporations that converted from C corporations "
                    "and are within the 5-year recognition period. The built-in gains tax is "
                    "computed at 21% on the net recognized built-in gain, limited to the net "
                    "unrealized built-in gain at the time of conversion. The tax reduces the "
                    "amount passed through to shareholders."
                ),
                "summary_text": "BIG tax: 21% on recognized built-in gains within 5-year window. Reduces passthrough.",
                "is_key_excerpt": True,
                "topic_tags": ["built_in_gains", "s_corporation"],
            },
        ],
    },
    {
        "source_code": "IRS_2025_8949_INSTR",
        "source_type": "official_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "entity_type_code": "shared",
        "title": "Instructions for Form 8949 — Sales and Other Dispositions of Capital Assets",
        "citation": "Form 8949 Instructions (2025)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/instructions/i8949",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": True,
        "requires_human_review": False,
        "trust_score": 9.5,
        "topics": ["capital_gains", "form_8949"],
        "excerpts": [
            {
                "excerpt_label": "Purpose and reporting categories",
                "location_reference": "General Instructions",
                "excerpt_text": (
                    "Use Form 8949 to report the sale or exchange of a capital asset not reported "
                    "on another form or schedule. Report each transaction on a separate row. "
                    "Reporting categories: for individuals — (A) ST basis reported to IRS, "
                    "(B) ST basis not reported, (C) ST no 1099-B, (D) LT basis reported, "
                    "(E) LT basis not reported, (F) LT no 1099-B. Entities use the same "
                    "categories except they generally won't receive 1099-B. Totals from each "
                    "category flow to the corresponding Schedule D line."
                ),
                "summary_text": "Categories A-F based on ST/LT and whether basis reported on 1099-B. Totals → Schedule D.",
                "is_key_excerpt": True,
                "topic_tags": ["form_8949", "capital_gains"],
            },
            {
                "excerpt_label": "Adjustment codes and column (g)",
                "location_reference": "Column (f) and (g) Instructions",
                "excerpt_text": (
                    "Column (f) — Adjustment code: B = basis incorrect on 1099-B, T = wash sale "
                    "(loss disallowed under §1091), W = collectibles (28% rate gain), O = other. "
                    "Multiple codes may apply. Column (g) — Amount of adjustment: for code B, "
                    "enter the correction to basis (positive or negative). For code T (wash sale), "
                    "enter the disallowed loss as a positive number. The gain/loss in column (h) "
                    "equals (d) proceeds minus (e) basis plus or minus (g) adjustment."
                ),
                "summary_text": "Codes: B=basis correction, T=wash sale, W=collectibles, O=other. Gain = proceeds - basis ± adjustment.",
                "is_key_excerpt": True,
                "topic_tags": ["form_8949", "capital_gains"],
            },
        ],
    },
    {
        "source_code": "IRS_2025_4562_INSTR",
        "source_type": "official_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "entity_type_code": "shared",
        "title": "Instructions for Form 4562 — Depreciation and Amortization",
        "citation": "Form 4562 Instructions (2025)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/instructions/i4562",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": True,
        "requires_human_review": False,
        "trust_score": 9.5,
        "topics": ["depreciation", "section_179", "macrs", "form_4562"],
        "excerpts": [
            {
                "excerpt_label": "Part I — §179 election",
                "location_reference": "Part I Instructions",
                "excerpt_text": (
                    "Use Part I to elect to expense the cost of certain property under §179. "
                    "For 2025 (OBBBA): maximum deduction is $2,500,000. The deduction begins to "
                    "phase out dollar-for-dollar when total cost of §179 property placed in service "
                    "exceeds $4,000,000. The deduction is also limited to the taxable income from "
                    "the active conduct of a trade or business. For S corporations and partnerships, "
                    "the §179 deduction is allocated to shareholders/partners as a separately stated "
                    "item — it does NOT reduce ordinary business income on page 1."
                ),
                "summary_text": "§179: $2.5M limit/$4M phaseout (OBBBA 2025). Separately stated for passthrough entities.",
                "is_key_excerpt": True,
                "topic_tags": ["section_179", "form_4562"],
            },
            {
                "excerpt_label": "Part II — Bonus depreciation §168(k)",
                "location_reference": "Part II Instructions",
                "excerpt_text": (
                    "Use Part II for special depreciation allowance (bonus depreciation) under "
                    "§168(k). For 2025 (OBBBA): 100% for qualified property acquired AND placed "
                    "in service after January 19, 2025. 40% for property acquired before January 20, "
                    "2025 under a binding written contract. The bonus depreciation is claimed in "
                    "addition to regular MACRS depreciation on the remaining basis. Unlike §179, "
                    "bonus depreciation IS included in the entity's depreciation and flows to "
                    "page 1 (not separately stated)."
                ),
                "summary_text": "Bonus: 100% post-1/19/2025, 40% prior. Flows to page 1 (not separately stated like §179).",
                "is_key_excerpt": True,
                "topic_tags": ["bonus_depreciation", "form_4562"],
            },
            {
                "excerpt_label": "Part III — MACRS depreciation",
                "location_reference": "Part III Instructions",
                "excerpt_text": (
                    "Use Part III for MACRS depreciation using GDS (General Depreciation System). "
                    "Group property by recovery period and convention. Lines 19a-19i correspond to "
                    "different recovery periods (3, 5, 7, 10, 15, 20, 25-year, 27.5-year residential "
                    "rental, 39-year nonresidential real). Apply the applicable percentage from "
                    "IRS tables (Publication 946) based on the depreciation method and convention. "
                    "Line 20a-20c: ADS (Alternative Depreciation System) for property required to "
                    "use ADS (e.g., listed property used 50% or less for business, tax-exempt "
                    "use property, property used predominantly outside the US)."
                ),
                "summary_text": "MACRS GDS: group by recovery period, apply Pub 946 tables. ADS for required property.",
                "is_key_excerpt": True,
                "topic_tags": ["macrs", "depreciation", "form_4562"],
            },
            {
                "excerpt_label": "Part V — Amortization",
                "location_reference": "Part V Instructions",
                "excerpt_text": (
                    "Use Part V to report amortization of costs that begins during the current year. "
                    "Section 197 intangibles (goodwill, going concern value, covenants not to compete, "
                    "franchises, trademarks, trade names) are amortized over 180 months (15 years) "
                    "using the straight-line method. Start-up costs under §195 and organizational "
                    "costs under §248 are also amortized over 180 months after the initial expensing "
                    "portion."
                ),
                "summary_text": "§197 intangibles: 180 months SL. §195 start-up and §248 org costs: same after initial expense.",
                "is_key_excerpt": True,
                "topic_tags": ["amortization", "form_4562"],
            },
        ],
    },
    {
        "source_code": "IRS_PUB_946",
        "source_type": "official_publication",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRS Publication 946 — How to Depreciate Property",
        "citation": "Publication 946 (2025)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/publications/p946",
        "current_status": "active",
        "is_substantive_authority": True,
        "requires_human_review": False,
        "trust_score": 9.0,
        "topics": ["depreciation", "macrs", "section_179"],
        "excerpts": [
            {
                "excerpt_label": "MACRS percentage tables",
                "location_reference": "Appendix A — MACRS Percentage Table Guide",
                "excerpt_text": (
                    "The MACRS depreciation tables provide the applicable percentage for each year "
                    "of the recovery period. For 5-year property using 200DB/HY convention: Year 1 = "
                    "20.00%, Year 2 = 32.00%, Year 3 = 19.20%, Year 4 = 11.52%, Year 5 = 11.52%, "
                    "Year 6 = 5.76%. For 7-year property using 200DB/HY: Year 1 = 14.29%, Year 2 = "
                    "24.49%, Year 3 = 17.49%, etc. For 39-year nonresidential real property using "
                    "SL/MM: 2.461% in month 1 placed in service, then 2.564% per year."
                ),
                "summary_text": "MACRS tables: 5yr HY = 20%/32%/19.2%/11.52%/11.52%/5.76%. 39yr SL/MM = ~2.564%/yr.",
                "is_key_excerpt": True,
                "topic_tags": ["macrs", "depreciation"],
            },
        ],
    },
]


# ── Source codes the command needs to reference (already in load_all_federal) ─

EXISTING_SOURCE_CODES = [
    "IRS_2025_1120S_INSTR",
    "IRS_2025_1120S_K1_INSTR",
    "IRS_2025_7203_INSTR",
    "IRS_2025_1040SD_INSTR",
    "IRC_1366",
    "IRC_1363",
    "IRC_1367",
    "IRC_1374",
    "IRC_199A",
    "IRC_469",
    "IRC_465",
    "IRC_1211",
    "IRC_1221",
    "IRC_170",
    "IRC_167",
    "IRC_197",
]
