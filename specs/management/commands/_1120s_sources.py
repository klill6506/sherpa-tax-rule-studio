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
            {
                "excerpt_label": "§179(b)(5) — SUV limitation and exceptions",
                "location_reference": "§179(b)(5)",
                "excerpt_text": (
                    "§179(b)(5)(A): The cost of any sport utility vehicle for any taxable year which "
                    "may be taken into account under this section shall not exceed $25,000 (inflation-"
                    "indexed under §179(b)(6) — $31,300 for taxable years beginning in 2025 per Rev. "
                    "Proc. 2024-40 §2.25). §179(b)(5)(B): 'sport utility vehicle' means any 4-wheeled "
                    "vehicle primarily designed to carry passengers over public streets, not subject "
                    "to §280F(a) (i.e., GVWR over 6,000 pounds), and rated at not more than 14,000 "
                    "pounds gross vehicle weight — but DOES NOT INCLUDE any vehicle that (I) is "
                    "designed to seat more than 9 persons behind the driver's seat, (II) is equipped "
                    "with a cargo area of at least 6 feet in interior length which is an open area or "
                    "is designed for use as an open area but is enclosed by a cap and is not readily "
                    "accessible directly from the passenger compartment, or (III) has an integral "
                    "enclosure fully enclosing the driver compartment and load carrying device, does "
                    "not have seating rearward of the driver's seat, and has no body section "
                    "protruding more than 30 inches ahead of the leading edge of the windshield."
                ),
                "summary_text": "SUV §179 cap ($31,300 for 2025) hits >6,000-lb SUVs/trucks ≤14,000 lbs — EXCEPT ≥6-ft-bed pickups, 9+-passenger vans, and enclosed cargo vans.",
                "is_key_excerpt": True,
                "topic_tags": ["section_179", "depreciation", "listed_property"],
            },
        ],
    },
    {
        "source_code": "IRC_280F",
        "source_type": "code_section",
        "source_rank": "controlling",
        "jurisdiction_code": "FED",
        "title": "IRC §280F — Limitation on Depreciation for Luxury Automobiles; Listed Property",
        "citation": "26 U.S.C. §280F",
        "issuer": "Congress",
        "current_status": "active",
        "is_substantive_authority": True,
        "requires_human_review": True,
        "trust_score": 10.0,
        "notes": "Annual dollar caps published by revenue procedure (2025 = Rev. Proc. 2025-16).",
        "topics": ["depreciation", "listed_property"],
        "excerpts": [
            {
                "excerpt_label": "§280F(a), (d)(5) — caps apply to passenger automobiles (≤6,000 lbs GVW)",
                "location_reference": "§280F(a), (d)(5)",
                "excerpt_text": (
                    "§280F(a) imposes annual dollar limitations on the depreciation deduction "
                    "(including §179) for any passenger automobile. §280F(d)(5)(A): 'passenger "
                    "automobile' means any 4-wheeled vehicle which is manufactured primarily for use "
                    "on public streets, roads, and highways, and which is rated at 6,000 pounds "
                    "unloaded gross vehicle weight or less (for a truck or van, substitute 'gross "
                    "vehicle weight' for 'unloaded gross vehicle weight'). §280F(d)(5)(B) excepts "
                    "ambulances/hearses used directly in a trade or business, vehicles used directly "
                    "in the trade or business of transporting persons or property for compensation or "
                    "hire, and (under regulations) trucks or vans which are qualified nonpersonal use "
                    "vehicles. §280F(b): listed property used 50% or less in a qualified business use "
                    "must be depreciated under the alternative depreciation system (straight line)."
                ),
                "summary_text": "§280F caps apply only at/under 6,000 lbs GVW(R); >6,000-lb trucks/SUVs escape the caps (but may hit the §179(b)(5) SUV cap). ≤50% business use forces ADS SL.",
                "is_key_excerpt": True,
                "topic_tags": ["depreciation", "listed_property"],
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
            {
                "excerpt_label": "Election out — §168(k)(7) (verbatim, p.7)",
                "location_reference": "Instructions for Form 4562 (2025), p.7 — Election out",
                "excerpt_text": (
                    "Election out. You can elect, for any class of property, to not deduct any "
                    "special depreciation allowance for all such property in such class placed in "
                    "service during the tax year. To make an election, attach a statement to your "
                    "timely filed return (including extensions) indicating the class of property "
                    "for which you are making the election and that, for such class, you are not "
                    "to claim any special depreciation allowance. The election must be made "
                    "separately by each person owning qualified property (for example, by the "
                    "partnership, by the S corporation, or for each member of a consolidated group "
                    "by the common parent of the group). If you timely filed your return without "
                    "making an election, you can still make the election by filing an amended "
                    "return within 6 months of the due date of the return (excluding extensions). "
                    "Enter “Filed pursuant to section 301.9100-2” on the amended return. "
                    "Once made, the election cannot be revoked without IRS consent. "
                    "Note: If you elect to not have any special depreciation allowance apply, the "
                    "property placed in service during the tax year will not be subject to an AMT "
                    "adjustment for depreciation."
                ),
                "summary_text": "§168(k)(7): per-class, all property in the class, statement on a timely filed return, "
                                "301.9100-2 six-month cure, irrevocable without consent — and NO AMT adjustment "
                                "for the elected-out property.",
                "is_key_excerpt": True,
                "topic_tags": ["bonus_depreciation", "form_4562", "elections"],
            },
            {
                "excerpt_label": "Qualified property acquired after 1/19/2025 — 100% + the 40%/60% transitional election (verbatim, p.6)",
                "location_reference": "Instructions for Form 4562 (2025), p.6 — Certain qualified property acquired after January 19, 2025",
                "excerpt_text": (
                    "Certain qualified property (defined below) acquired after January 19, 2025, is "
                    "eligible for a 100% special depreciation allowance. However, you can elect to "
                    "take a 40% special depreciation allowance for certain qualified property (60% "
                    "for property with a long production period and certain aircraft), instead of "
                    "the 100% special depreciation allowance in the first tax year ending after "
                    "January 19, 2025."
                ),
                "summary_text": "OBBBA transitional election: 40% (60% LPP/aircraft) instead of 100%, first tax year "
                                "ending after 1/19/2025 ONLY. i4562 (2025) states NO statement mechanics for this "
                                "election (unlike §168(k)(5)/(k)(7)) — flagged, do not improvise.",
                "is_key_excerpt": True,
                "topic_tags": ["bonus_depreciation", "form_4562", "elections"],
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
            # ── Depreciation-methods unit (2026-07-10, Ken's method list) ────
            # Every percentage below was transcribed from the printed tables in
            # Publication 946 (2025), Appendix A (pymupdf extraction of
            # https://www.irs.gov/pub/irs-pdf/p946.pdf, fetched 2026-07-10) —
            # NEVER derived arithmetic. Each annual column sums to 100%.
            {
                "excerpt_label": "Chart 1 — MACRS Percentage Table Guide (method → table routing)",
                "location_reference": "Appendix A, Chart 1 (Publication 946 (2025) p.70)",
                "excerpt_text": (
                    "Chart 1 (verbatim structure): GDS 200% / GDS 3,5,7,10 / Half-Year → Table A-1; "
                    "Mid-Quarter Q1-Q4 → Tables A-2, A-3, A-4, A-5. GDS 150% / GDS 3,5,7,10 / "
                    "Half-Year → Table A-14; Mid-Quarter Q1-Q4 → Tables A-15, A-16, A-17, A-18. "
                    "GDS 150% / GDS 15, 20 / Half-Year → Table A-1; Mid-Quarter → Tables A-2 through "
                    "A-5. GDS or ADS SL / Half-Year → Table A-8; Mid-Quarter → Tables A-9 through "
                    "A-12. ADS 150% → Tables A-14 through A-18. Chart 2: GDS SL GDS/27.5 Mid-Month "
                    "Residential Rental → Table A-6; GDS SL GDS/31.5 and GDS/39 Mid-Month "
                    "Nonresidential Real → Tables A-7 and A-7a; ADS SL ADS/30 Mid-Month Residential "
                    "Rental → Table A-13; ADS SL ADS/40 Mid-Month → Table A-13a."
                ),
                "summary_text": "The IRS's own method→table routing. 15/20-yr GDS property uses 150DB and lives in A-1/A-2..A-5; elective 150DB for 3-10yr lives in A-14/A-15..A-18.",
                "is_key_excerpt": True,
                "topic_tags": ["macrs", "depreciation"],
            },
            {
                "excerpt_label": "Table A-14 — 150% DB Half-Year (3/5/7/10-year columns, verbatim)",
                "location_reference": "Appendix A, Table A-14 (Publication 946 (2025) p.85)",
                "excerpt_text": (
                    "150% Declining Balance Method, Half-Year Convention. 3-year: 25.00%, 37.50, "
                    "25.00, 12.50. 5-year: 15.00%, 25.50, 17.85, 16.66, 16.66, 8.33. 7-year: "
                    "10.71%, 19.13, 15.03, 12.25, 12.25, 12.25, 12.25, 6.13. 10-year: 7.50%, "
                    "13.88, 11.79, 10.02, 8.74, 8.74, 8.74, 8.74, 8.74, 8.74, 4.37. NOTE: the "
                    "10-year column switches to straight line in YEAR 5 (8.74 = remaining basis "
                    "56.81% over the remaining 6.5-year life) — an engine that keeps declining "
                    "balance through year 5 (8.52%) and switches later is WRONG."
                ),
                "summary_text": "A-14 verbatim 3/5/7/10-yr 150DB HY columns. 10-yr SL switch is at year 5 (8.74×6 then 4.37).",
                "is_key_excerpt": True,
                "topic_tags": ["macrs", "depreciation"],
            },
            {
                "excerpt_label": "Tables A-2..A-5 — 200% DB Mid-Quarter (all columns, verbatim)",
                "location_reference": "Appendix A, Tables A-2 to A-5 (Publication 946 (2025) pp.71-73)",
                "excerpt_text": (
                    "A-2 (Q1) — 3yr: 58.33%, 27.78, 12.35, 1.54; 5yr: 35.00%, 26.00, 15.60, 11.01, "
                    "11.01, 1.38; 7yr: 25.00%, 21.43, 15.31, 10.93, 8.75, 8.74, 8.75, 1.09; 10yr: "
                    "17.50%, 16.50, 13.20, 10.56, 8.45, 6.76, 6.55, 6.55, 6.56, 6.55, 0.82; 15yr: "
                    "8.75%, 9.13, 8.21, 7.39, 6.65, 5.99, 5.90, 5.91, 5.90, 5.91, 5.90, 5.91, 5.90, "
                    "5.91, 5.90, 0.74; 20yr: 6.563%, 7.000, 6.482, 5.996, 5.546, 5.130, 4.746, "
                    "4.459, 4.459, 4.459, 4.459, 4.460, 4.459, 4.460, 4.459, 4.460, 4.459, 4.460, "
                    "4.459, 4.460, 0.565. "
                    "A-3 (Q2) — 3yr: 41.67%, 38.89, 14.14, 5.30; 5yr: 25.00%, 30.00, 18.00, 11.37, "
                    "11.37, 4.26; 7yr: 17.85%, 23.47, 16.76, 11.97, 8.87, 8.87, 8.87, 3.34; 10yr: "
                    "12.50%, 17.50, 14.00, 11.20, 8.96, 7.17, 6.55, 6.55, 6.56, 6.55, 2.46; 15yr: "
                    "6.25%, 9.38, 8.44, 7.59, 6.83, 6.15, 5.91, 5.90, 5.91, 5.90, 5.91, 5.90, 5.91, "
                    "5.90, 5.91, 2.21; 20yr: 4.688%, 7.148, 6.612, 6.116, 5.658, 5.233, 4.841, "
                    "4.478, 4.463, 4.463, 4.463, 4.463, 4.463, 4.463, 4.462, 4.463, 4.462, 4.463, "
                    "4.462, 4.463, 1.673. "
                    "A-4 (Q3) — 3yr: 25.00%, 50.00, 16.67, 8.33; 5yr: 15.00%, 34.00, 20.40, 12.24, "
                    "11.30, 7.06; 7yr: 10.71%, 25.51, 18.22, 13.02, 9.30, 8.85, 8.86, 5.53; 10yr: "
                    "7.50%, 18.50, 14.80, 11.84, 9.47, 7.58, 6.55, 6.55, 6.56, 6.55, 4.10; 15yr: "
                    "3.75%, 9.63, 8.66, 7.80, 7.02, 6.31, 5.90, 5.90, 5.91, 5.90, 5.91, 5.90, 5.91, "
                    "5.90, 5.91, 3.69; 20yr: 2.813%, 7.289, 6.742, 6.237, 5.769, 5.336, 4.936, "
                    "4.566, 4.460, 4.460, 4.460, 4.460, 4.461, 4.460, 4.461, 4.460, 4.461, 4.460, "
                    "4.461, 4.460, 2.788. "
                    "A-5 (Q4) — 3yr: 8.33%, 61.11, 20.37, 10.19; 5yr: 5.00%, 38.00, 22.80, 13.68, "
                    "10.94, 9.58; 7yr: 3.57%, 27.55, 19.68, 14.06, 10.04, 8.73, 8.73, 7.64; 10yr: "
                    "2.50%, 19.50, 15.60, 12.48, 9.98, 7.99, 6.55, 6.55, 6.56, 6.55, 5.74; 15yr: "
                    "1.25%, 9.88, 8.89, 8.00, 7.20, 6.48, 5.90, 5.90, 5.90, 5.91, 5.90, 5.91, 5.90, "
                    "5.91, 5.90, 5.17; 20yr: 0.938%, 7.430, 6.872, 6.357, 5.880, 5.439, 5.031, "
                    "4.654, 4.458, 4.458, 4.458, 4.458, 4.458, 4.458, 4.458, 4.458, 4.458, 4.459, "
                    "4.458, 4.459, 3.901."
                ),
                "summary_text": "The four published 200DB (and 150DB for 15/20-yr) mid-quarter tables, all six recovery-period columns each.",
                "is_key_excerpt": True,
                "topic_tags": ["macrs", "depreciation"],
            },
            {
                "excerpt_label": "Tables A-15..A-18 — 150% DB Mid-Quarter (3/5/7/10-year columns, verbatim)",
                "location_reference": "Appendix A, Tables A-15 to A-18 (Publication 946 (2025) pp.87-93)",
                "excerpt_text": (
                    "A-15 (Q1) — 3yr: 43.75%, 28.13, 25.00, 3.12; 5yr: 26.25%, 22.13, 16.52, 16.52, "
                    "16.52, 2.06; 7yr: 18.75%, 17.41, 13.68, 12.16, 12.16, 12.16, 12.16, 1.52; 10yr: "
                    "13.13%, 13.03, 11.08, 9.41, 8.71, 8.71, 8.71, 8.71, 8.71, 8.71, 1.09. "
                    "A-16 (Q2) — 3yr: 31.25%, 34.38, 25.00, 9.37; 5yr: 18.75%, 24.38, 17.06, 16.76, "
                    "16.76, 6.29; 7yr: 13.39%, 18.56, 14.58, 12.22, 12.22, 12.22, 12.23, 4.58; 10yr: "
                    "9.38%, 13.59, 11.55, 9.82, 8.73, 8.73, 8.73, 8.73, 8.73, 8.73, 3.28. "
                    "A-17 (Q3) — 3yr: 18.75%, 40.63, 25.00, 15.62; 5yr: 11.25%, 26.63, 18.64, 16.56, "
                    "16.57, 10.35; 7yr: 8.04%, 19.71, 15.48, 12.27, 12.28, 12.27, 12.28, 7.67; 10yr: "
                    "5.63%, 14.16, 12.03, 10.23, 8.75, 8.75, 8.75, 8.74, 8.75, 8.74, 5.47. "
                    "A-18 (Q4) — 3yr: 6.25%, 46.88, 25.00, 21.87; 5yr: 3.75%, 28.88, 20.21, 16.40, "
                    "16.41, 14.35; 7yr: 2.68%, 20.85, 16.39, 12.87, 12.18, 12.18, 12.19, 10.66; "
                    "10yr: 1.88%, 14.72, 12.51, 10.63, 9.04, 8.72, 8.72, 8.72, 8.72, 8.71, 7.63."
                ),
                "summary_text": "Published 150DB mid-quarter tables (elective 150DB for GDS 3/5/7/10-yr property).",
                "is_key_excerpt": True,
                "topic_tags": ["macrs", "depreciation"],
            },
            {
                "excerpt_label": "Table A-7 — Nonresidential Real 31.5-Year SL/MM (legacy, verbatim)",
                "location_reference": "Appendix A, Table A-7 (Publication 946 (2025) p.74)",
                "excerpt_text": (
                    "Nonresidential Real Property, Mid-Month Convention, Straight Line — 31.5 Years. "
                    "Year 1 by month placed in service: month 1 = 3.042%, 2 = 2.778%, 3 = 2.513%, "
                    "4 = 2.249%, 5 = 1.984%, 6 = 1.720%, 7 = 1.455%, 8 = 1.190%, 9 = 0.926%, "
                    "10 = 0.661%, 11 = 0.397%, 12 = 0.132%. Full years alternate 3.175/3.174 "
                    "(1/31.5). Applies to nonresidential real property generally placed in service "
                    "after 1986 and before May 13, 1993 (the 39-year Table A-7a applies on/after "
                    "May 13, 1993)."
                ),
                "summary_text": "The legacy 31.5-yr nonresidential SL/MM table (PIS after 1986, before 5/13/1993).",
                "is_key_excerpt": True,
                "topic_tags": ["macrs", "depreciation"],
            },
            {
                "excerpt_label": "Tables A-13 / A-13a — ADS real property SL/MM 30-Year and 40-Year (verbatim)",
                "location_reference": "Appendix A, Tables A-13 and A-13a (Publication 946 (2025) p.85)",
                "excerpt_text": (
                    "Table A-13 — Residential Rental Property Placed in Service After 2017, Straight "
                    "Line — 30 Years, Mid-Month Convention. Year 1 by month: 3.204%, 2.926%, 2.649%, "
                    "2.371%, 2.093%, 1.815%, 1.528%, 1.250%, 0.972%, 0.694%, 0.417%, 0.139%; years "
                    "2-30 = 3.333%. Table A-13a — Straight Line — 40 Years, Mid-Month Convention "
                    "(ADS real property). Year 1 by month: 2.396%, 2.188%, 1.979%, 1.771%, 1.563%, "
                    "1.354%, 1.146%, 0.938%, 0.729%, 0.521%, 0.313%, 0.104%; years 2-40 = 2.500%."
                ),
                "summary_text": "ADS SL/MM real-property tables: residential 30-yr (post-2017) and 40-yr.",
                "is_key_excerpt": True,
                "topic_tags": ["macrs", "depreciation", "ads"],
            },
        ],
    },
    {
        "source_code": "IRS_RP_2025_16",
        "source_type": "official_revenue_procedure",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "Rev. Proc. 2025-16 — §280F Depreciation Limitations for Passenger Automobiles Placed in Service in 2025",
        "citation": "Rev. Proc. 2025-16",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-drop/rp-25-16.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "requires_human_review": False,
        "trust_score": 9.5,
        "notes": "Fetched + extracted 2026-07-10. 'For purposes of this revenue procedure, the term "
                 "passenger automobiles includes trucks and vans.' NOT Rev. Proc. 2025-13 (that is the "
                 "§831(b) micro-captive revocation procedure — a prior engine comment miscited it).",
        "topics": ["depreciation", "listed_property"],
        "excerpts": [
            {
                "excerpt_label": "Table 1 — §168(k) bonus applies (verbatim)",
                "location_reference": "Section 4.01(2), Table 1",
                "excerpt_text": (
                    "REV. PROC. 2025-16 TABLE 1 — DEPRECIATION LIMITATIONS FOR PASSENGER AUTOMOBILES "
                    "ACQUIRED AFTER SEPTEMBER 27, 2017, AND PLACED IN SERVICE DURING CALENDAR YEAR "
                    "2025, FOR WHICH THE § 168(k) ADDITIONAL FIRST YEAR DEPRECIATION DEDUCTION "
                    "APPLIES: 1st Tax Year $20,200; 2nd Tax Year $19,600; 3rd Tax Year $11,800; "
                    "Each Succeeding Year $7,060."
                ),
                "summary_text": "2025 auto caps WITH bonus: 20,200 / 19,600 / 11,800 / 7,060.",
                "is_key_excerpt": True,
                "topic_tags": ["depreciation", "listed_property"],
            },
            {
                "excerpt_label": "Table 2 — no §168(k) bonus (verbatim)",
                "location_reference": "Section 4.01(2), Table 2",
                "excerpt_text": (
                    "REV. PROC. 2025-16 TABLE 2 — DEPRECIATION LIMITATIONS FOR PASSENGER AUTOMOBILES "
                    "PLACED IN SERVICE DURING CALENDAR YEAR 2025 FOR WHICH NO § 168(k) ADDITIONAL "
                    "FIRST YEAR DEPRECIATION DEDUCTION APPLIES: 1st Tax Year $12,200; 2nd Tax Year "
                    "$19,600; 3rd Tax Year $11,800; Each Succeeding Year $7,060."
                ),
                "summary_text": "2025 auto caps WITHOUT bonus: 12,200 / 19,600 / 11,800 / 7,060.",
                "is_key_excerpt": True,
                "topic_tags": ["depreciation", "listed_property"],
            },
            {
                "excerpt_label": "§3.03 — when Table 2 applies (incl. §168(k)(7) election out)",
                "location_reference": "Section 2.03",
                "excerpt_text": (
                    "The § 168(k) additional first year depreciation deduction does not apply for "
                    "2025 if the taxpayer: (1) did not use the passenger automobile during 2025 more "
                    "than 50 percent for business purposes; (2) elected out of the § 168(k) "
                    "additional first year depreciation deduction pursuant to § 168(k)(7) for the "
                    "class of property that includes passenger automobiles; (3) acquired the "
                    "passenger automobile used and the acquisition of such property did not meet the "
                    "acquisition requirements in § 168(k)(2)(E)(ii) and § 1.168(k)-2(b)(3)(iii) of "
                    "the Income Tax Regulations; or (4) acquired the passenger automobile before "
                    "September 28, 2017, and placed it in service after 2019."
                ),
                "summary_text": "A §168(k)(7) election-out (or ≤50% business use, or non-qualifying used acquisition) moves the vehicle to Table 2.",
                "is_key_excerpt": True,
                "topic_tags": ["depreciation", "listed_property", "bonus_depreciation"],
            },
        ],
    },
    {
        "source_code": "IRS_RP_2024_40",
        "source_type": "official_revenue_procedure",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "Rev. Proc. 2024-40 — 2025 Inflation Adjustments (§179(b)(5)(A) SUV limitation)",
        "citation": "Rev. Proc. 2024-40, §2.25",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-drop/rp-24-40.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "requires_human_review": False,
        "trust_score": 9.5,
        "notes": "Fetched + extracted 2026-07-10. The §179(b)(1)/(b)(2) figures in §2.25 ($1,250,000 / "
                 "$3,130,000) are SUPERSEDED by OBBBA's statutory $2,500,000 / $4,000,000 for 2025 "
                 "(Ken-ruled, already encoded). The (b)(5)(A) SUV amount was NOT amended by OBBBA and stands.",
        "topics": ["section_179", "depreciation"],
        "excerpts": [
            {
                "excerpt_label": "§2.25 — §179(b)(5)(A) SUV limitation for 2025 (verbatim)",
                "location_reference": "Section 2.25",
                "excerpt_text": (
                    "Election to Expense Certain Depreciable Assets. For taxable years beginning in "
                    "2025 ... under § 179(b)(5)(A), the cost of any sport utility vehicle that may "
                    "be taken into account under § 179 cannot exceed $31,300."
                ),
                "summary_text": "2025 §179 SUV cap = $31,300.",
                "is_key_excerpt": True,
                "topic_tags": ["section_179", "depreciation"],
            },
        ],
    },
]


# ── Source codes the command needs to reference (already in load_all_federal) ─

EXISTING_SOURCE_CODES = [
    "IRS_2025_6251_INSTR",   # i6251 line 2l — the post-1998 AMT depreciation matrix
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
