"""IRS form instruction sources for the 1120-S (S-Corporation) family.

Content derived from IRS instructions at irs.gov. Instruction sources marked
requires_human_review=False; content verified against published instructions.
"""


def _instr(source_code, title, citation, url, entity_type, excerpts, topics, form_links,
           requires_review=False, trust_score=9.5):
    """Return a standard IRS instruction source dict."""
    return {
        "source_code": source_code,
        "source_type": "official_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "entity_type_code": entity_type,
        "title": title,
        "citation": citation,
        "issuer": "IRS",
        "official_url": url,
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": True,
        "requires_human_review": requires_review,
        "trust_score": trust_score,
        "topics": topics,
        "excerpts": excerpts,
        "form_links": form_links,
    }


SOURCES_1120S = [
    # ───────────────────────────────────────────────────────────────────────
    # Form 1120-S Instructions
    # ───────────────────────────────────────────────────────────────────────
    _instr(
        "IRS_2025_1120S_INSTR",
        "Instructions for Form 1120-S — U.S. Income Tax Return for an S Corporation",
        "Form 1120-S Instructions (2025)",
        "https://www.irs.gov/instructions/i1120s",
        "1120S",
        excerpts=[
            {
                "excerpt_label": "Who must file",
                "location_reference": "General Instructions — Who Must File",
                "excerpt_text": (
                    "A corporation or other entity must file Form 1120-S if it elected to be an "
                    "S corporation by filing Form 2553 and the IRS accepted the election. An entity "
                    "eligible to elect S status must be a domestic corporation (or eligible entity), "
                    "have only allowable shareholders (individuals, certain trusts, estates), have no "
                    "more than 100 shareholders, have only one class of stock, and not be an ineligible "
                    "corporation (certain financial institutions, insurance companies, domestic "
                    "international sales corporations). File Form 1120-S by the 15th day of the 3rd "
                    "month after the end of the tax year (March 15 for calendar year)."
                ),
                "summary_text": "File 1120-S if S election accepted. Due March 15 for calendar year. Max 100 shareholders, 1 class of stock.",
                "is_key_excerpt": True,
                "topic_tags": ["s_corporation", "form_1120s"],
            },
            {
                "excerpt_label": "Income — Lines 1a through 6",
                "location_reference": "Line Instructions — Income",
                "excerpt_text": (
                    "Line 1a: Gross receipts or sales. Enter gross receipts or sales from all business "
                    "operations. Line 1b: Returns and allowances. Line 1c: Net (line 1a minus 1b). "
                    "Line 2: Cost of goods sold (from Form 1125-A). Line 3: Gross profit (line 1c "
                    "minus line 2). Line 4: Net gain (loss) from Form 4797 — enter the net gain or "
                    "loss from the sale of business property from Form 4797 Part II line 17. If the "
                    "corporation has a net §1231 gain, it flows through Schedule K to shareholders. "
                    "Line 5: Other income (loss) — includes income not reportable elsewhere such as "
                    "interest on accounts receivable, recoveries of bad debts, and income from "
                    "oil/gas/mineral royalties. Line 6: Total income."
                ),
                "summary_text": "Income lines: gross receipts, COGS, gross profit, Form 4797 gains, other income.",
                "is_key_excerpt": True,
                "topic_tags": ["form_1120s"],
            },
            {
                "excerpt_label": "Deductions — Lines 7 through 19",
                "location_reference": "Line Instructions — Deductions",
                "excerpt_text": (
                    "Line 7: Compensation of officers (from Form 1125-E if total receipts ≥ $500K). "
                    "Line 8: Salaries and wages (less employment credits). Line 9: Repairs and "
                    "maintenance. Line 10: Bad debts. Line 11: Rents. Line 12: Taxes and licenses "
                    "(do not include federal income taxes or taxes reported elsewhere). Line 13: "
                    "Interest (subject to §163(j) limitation — use Form 8990). Line 14: Depreciation "
                    "not claimed elsewhere or on Form 1125-A (attach Form 4562). Line 15: Depletion "
                    "(do not deduct oil/gas — passed through to shareholders). Line 16: Advertising. "
                    "Line 17: Pension, profit-sharing plans. Line 18: Employee benefit programs. "
                    "Line 19: Other deductions (attach statement). Line 20: Total deductions. "
                    "Line 21: Ordinary business income (loss) — this amount flows to Schedule K, "
                    "line 1, and then to each shareholder's K-1."
                ),
                "summary_text": "Deduction lines: officer comp, wages, rent, taxes, interest (§163(j)), depreciation, benefits, other.",
                "is_key_excerpt": True,
                "topic_tags": ["form_1120s"],
            },
            {
                "excerpt_label": "Schedule K — Shareholders' Pro Rata Share Items",
                "location_reference": "Schedule K Instructions",
                "excerpt_text": (
                    "Schedule K is a summary schedule of all shareholders' shares of the S corporation's "
                    "income, deductions, credits, and other items. These items are then allocated to "
                    "each shareholder on Schedule K-1 based on pro rata share. Key lines: Line 1: "
                    "Ordinary business income (loss) from page 1 line 21. Lines 2-3: Net rental real "
                    "estate income/loss and other net rental income/loss. Lines 4-5d: Interest, "
                    "dividends, royalties. Lines 6-7: Net short-term and long-term capital gain/loss. "
                    "Lines 8a-9: Net §1231 gain/loss and other income/loss. Lines 10-12d: §179 "
                    "deduction, charitable contributions, investment interest expense, and other "
                    "deductions. Lines 13a-13g: Credits — low-income housing, rehabilitation, "
                    "other rental, foreign tax, and other credits. Lines 14a-14c: Self-employment "
                    "items. Lines 15a-15f: Alternative minimum tax items. Lines 16a-16d: Items "
                    "affecting shareholder basis — tax-exempt income, nondeductible expenses, "
                    "distributions, repayment of loans from shareholders."
                ),
                "summary_text": "Schedule K summarizes all pass-through items: income, deductions, credits, AMT, basis adjustments.",
                "is_key_excerpt": True,
                "topic_tags": ["form_1120s", "schedule_k1", "passthrough"],
            },
            {
                "excerpt_label": "Schedule B — Other Information",
                "location_reference": "Schedule B Instructions",
                "excerpt_text": (
                    "Schedule B asks questions about the corporation's status and activities: "
                    "accounting method (cash, accrual, other), business activity code, product or "
                    "service, whether the corporation was a C corporation in a prior year (relevant "
                    "for built-in gains tax and accumulated E&P), number of shareholders during the "
                    "year, and whether the corporation made any distributions during the year. "
                    "Question 9: Does the corporation have accumulated earnings and profits (E&P) "
                    "from C corporation years? If yes, the distribution ordering rules of §1368(c) "
                    "apply instead of §1368(b)."
                ),
                "summary_text": "Schedule B: accounting method, C-Corp history (BIG tax/E&P implications), shareholder count, distributions.",
                "is_key_excerpt": True,
                "topic_tags": ["form_1120s", "s_corporation"],
            },
            {
                "excerpt_label": "Schedules M-1, M-2 — Reconciliation",
                "location_reference": "Schedule M-1/M-2 Instructions",
                "excerpt_text": (
                    "Schedule M-1: Reconciliation of Income (Loss) per Books With Income (Loss) per "
                    "Return. Required unless Schedule M-3 is filed (total assets ≥ $50 million). "
                    "Line 1: Net income (loss) per books. Common adjustments include: tax-exempt "
                    "interest, meals (50% limitation), depreciation differences, tax penalties. "
                    "Schedule M-2: Analysis of Accumulated Adjustments Account (AAA), Other "
                    "Adjustments Account (OAA), and Shareholders' Undistributed Taxable Income "
                    "Previously Taxed (UTIP/PTI). AAA tracks the cumulative undistributed net income "
                    "that has been taxed to shareholders. AAA is increased by income items and "
                    "decreased by losses, deductions, and nondividend distributions. OAA tracks "
                    "items such as tax-exempt income and related expenses."
                ),
                "summary_text": "M-1: book-to-tax reconciliation. M-2: AAA/OAA/PTI tracking for distribution ordering.",
                "is_key_excerpt": True,
                "topic_tags": ["form_1120s", "s_corporation"],
            },
            {
                "excerpt_label": "Schedule L — Balance Sheet per Books",
                "location_reference": "Schedule L Instructions",
                "excerpt_text": (
                    "Schedule L presents the balance sheet per books at the beginning and end of the "
                    "tax year. Required unless the corporation: (a) has total receipts less than "
                    "$250,000, AND (b) total assets less than $250,000. Assets include: cash, trade "
                    "notes and accounts receivable, inventories, federal and state government "
                    "obligations, other current assets, loans to shareholders, mortgage and real "
                    "estate loans, other investments, buildings and other depreciable assets (less "
                    "accumulated depreciation), land, intangible assets (less accumulated "
                    "amortization), and other assets. Liabilities include: accounts payable, "
                    "mortgages, other liabilities, and loans from shareholders."
                ),
                "summary_text": "Balance sheet per books. Required if receipts ≥ $250K or assets ≥ $250K.",
                "is_key_excerpt": True,
                "topic_tags": ["form_1120s"],
            },
        ],
        topics=["form_1120s", "s_corporation"],
        form_links=[{"form_code": "1120S", "link_type": "governs"}],
    ),

    # ───────────────────────────────────────────────────────────────────────
    # Schedule K-1 (Form 1120-S) Instructions
    # ───────────────────────────────────────────────────────────────────────
    _instr(
        "IRS_2025_1120S_K1_INSTR",
        "Instructions for Schedule K-1 (Form 1120-S) — Shareholder's Share of Income, Deductions, Credits, etc.",
        "Schedule K-1 (Form 1120-S) Instructions (2025)",
        "https://www.irs.gov/instructions/i1120ssk",
        "1120S",
        excerpts=[
            {
                "excerpt_label": "Boxes 1-4 — Income and loss items",
                "location_reference": "Box Instructions",
                "excerpt_text": (
                    "Box 1: Ordinary business income (loss) — report on Schedule E Part II. This is "
                    "the shareholder's pro rata share of the S corporation's ordinary income from "
                    "trade or business activities. Not subject to self-employment tax. Box 2: Net "
                    "rental real estate income (loss) — report on Schedule E Part II. Subject to "
                    "passive activity rules. Box 3: Other net rental income (loss). Box 4: Interest "
                    "income — report on Schedule B or directly on Form 1040 line 2b."
                ),
                "summary_text": "Box 1: ordinary income → Sch E Part II (no SE tax). Box 2: rental income (passive). Box 4: interest.",
                "is_key_excerpt": True,
                "topic_tags": ["schedule_k1", "form_1120s"],
            },
            {
                "excerpt_label": "Boxes 5-10 — Dividends, capital gains, §1231, other",
                "location_reference": "Box Instructions",
                "excerpt_text": (
                    "Box 5a: Ordinary dividends — report on Form 1040 line 3b. Box 5b: Qualified "
                    "dividends — eligible for preferential capital gains rates. Box 6: Royalties — "
                    "report on Schedule E page 1. Box 7: Net short-term capital gain (loss) — report "
                    "on Schedule D line 5. Box 8a: Net long-term capital gain (loss) — Schedule D "
                    "line 12. Box 8b: Collectibles (28%) gain (loss). Box 8c: Unrecaptured §1250 "
                    "gain — taxed at maximum 25%. Box 9: Net §1231 gain (loss) — report on Form "
                    "4797 Part I. If net §1231 gain, treated as long-term capital gain; if net "
                    "loss, treated as ordinary loss. Box 10: Other income (loss) — may include "
                    "other portfolio income, involuntary conversions, §1256 contracts."
                ),
                "summary_text": "Boxes 5-10: dividends, capital gains (ST/LT/28%/§1250), §1231, royalties, other income.",
                "is_key_excerpt": True,
                "topic_tags": ["schedule_k1", "capital_gains", "1231"],
            },
            {
                "excerpt_label": "Boxes 11-13 — Deductions and credits",
                "location_reference": "Box Instructions",
                "excerpt_text": (
                    "Box 11: §179 deduction — shareholder's share of the S corporation's §179 "
                    "deduction. Subject to shareholder's own §179 limits and the aggregate business "
                    "income limitation. Box 12: Other deductions — includes various items that must "
                    "be separately stated: (A) cash charitable contributions, (B) noncash "
                    "contributions, (C) investment interest expense (§163(d)), (D)-(E) §59(e)(2) "
                    "expenditures, (H) unreimbursed partnership expenses, and other items. "
                    "Box 13: Credits — includes (A) low-income housing credit (§42), (B) low-income "
                    "housing credit from pre-2008 buildings, (C) qualified rehabilitation expenditures, "
                    "(D) other rental real estate credits, (E) other rental credits, (F) foreign "
                    "tax credit, and (G) other credits."
                ),
                "summary_text": "Box 11: §179. Box 12: charitable, investment interest, other deductions. Box 13: credits (LIHTC, foreign tax, etc.).",
                "is_key_excerpt": True,
                "topic_tags": ["schedule_k1", "section_179", "charitable"],
            },
            {
                "excerpt_label": "Boxes 14-17 — SE, AMT, basis items, other info",
                "location_reference": "Box Instructions",
                "excerpt_text": (
                    "Box 14: Self-employment earnings (loss) — S corporation shareholders generally "
                    "do NOT owe self-employment tax on ordinary income (unlike partnerships). Box 14 "
                    "codes apply only in limited situations. Box 15: Alternative minimum tax (AMT) "
                    "items — including (A) post-1986 depreciation adjustment, (B) adjusted gain or "
                    "loss, (C) depletion, (D) oil/gas/geothermal deductions, (E) other AMT items. "
                    "Box 16: Items affecting shareholder basis — (A) tax-exempt interest income, "
                    "(B) other tax-exempt income, (C) nondeductible expenses, (D) distributions, "
                    "(E) repayment of loans from shareholders. These are critical for Form 7203 "
                    "basis computation. Box 17: Other information — includes §199A QBI items, "
                    "investment income/expenses for Form 4952, and other items."
                ),
                "summary_text": "Box 14: SE (rare for S-Corp). Box 15: AMT. Box 16: basis items (tax-exempt, nondeductible, distributions). Box 17: QBI.",
                "is_key_excerpt": True,
                "topic_tags": ["schedule_k1", "form_1120s", "s_corp_basis"],
            },
            {
                "excerpt_label": "Basis limitation rules for shareholders",
                "location_reference": "General Information",
                "excerpt_text": (
                    "A shareholder's deduction for their pro rata share of losses and deductions is "
                    "limited to the adjusted basis of the shareholder's stock and any debt owed by "
                    "the S corporation to the shareholder (§1366(d)). Shareholders must use Form "
                    "7203 to compute basis. Loss limitation ordering: (1) first against stock basis, "
                    "(2) then against debt basis. Losses exceeding combined stock and debt basis "
                    "are suspended and carry forward indefinitely. In addition to the basis "
                    "limitation, the at-risk rules (§465) and passive activity rules (§469) may "
                    "further limit deductions."
                ),
                "summary_text": "Losses limited to stock + debt basis (Form 7203). Then at-risk (§465), then passive (§469).",
                "is_key_excerpt": True,
                "topic_tags": ["s_corp_basis", "schedule_k1"],
            },
        ],
        topics=["schedule_k1", "form_1120s", "s_corporation"],
        form_links=[{"form_code": "K1_1120S", "link_type": "governs"}],
    ),

    # ───────────────────────────────────────────────────────────────────────
    # Form 7203 Instructions
    # ───────────────────────────────────────────────────────────────────────
    _instr(
        "IRS_2025_7203_INSTR",
        "Instructions for Form 7203 — S Corporation Shareholder Stock and Debt Basis Limitations",
        "Form 7203 Instructions (2025)",
        "https://www.irs.gov/instructions/i7203",
        "1120S",
        excerpts=[
            {
                "excerpt_label": "Purpose and who must file",
                "location_reference": "General Instructions",
                "excerpt_text": (
                    "Form 7203 is used by S corporation shareholders to figure their stock and debt "
                    "basis. You must file Form 7203 if you are claiming a deduction for your share "
                    "of an aggregate loss, you received a non-dividend distribution, you disposed of "
                    "stock, or you received a loan repayment from the S corporation. The form tracks "
                    "basis from the beginning of the year through all adjustments to determine the "
                    "allowable loss and deduction items."
                ),
                "summary_text": "Form 7203: required when S-Corp shareholder has losses, distributions, dispositions, or loan repayments.",
                "is_key_excerpt": True,
                "topic_tags": ["form_7203", "s_corp_basis"],
            },
            {
                "excerpt_label": "Part I — Stock basis computation",
                "location_reference": "Part I Instructions",
                "excerpt_text": (
                    "Stock basis at beginning of year (line 1). Increases: (a) stock purchased or "
                    "contributed during the year, (b) income items — ordinary income, separately "
                    "stated income items, tax-exempt income, excess depletion. Decreases (applied in "
                    "this order after increases): (1) nondividend distributions (limited to basis "
                    "before this item), (2) nondeductible/noncapital expenses, (3) deduction items — "
                    "ordinary loss, separately stated loss/deduction items, oil/gas depletion. "
                    "Stock basis cannot be reduced below zero. The ordering of decreases is critical: "
                    "distributions reduce basis before losses and deductions."
                ),
                "summary_text": "Stock basis: increase for income/contributions, decrease for distributions (first), then losses. Never below zero.",
                "is_key_excerpt": True,
                "topic_tags": ["s_corp_basis", "form_7203"],
            },
            {
                "excerpt_label": "Part II — Debt basis and restoration",
                "location_reference": "Part II Instructions",
                "excerpt_text": (
                    "Debt basis applies ONLY to direct loans from the shareholder to the S corporation. "
                    "Guarantees and loans from related parties do not create debt basis. Debt basis "
                    "at beginning of year. Net increase: if there is a net increase (income items "
                    "exceed losses/deductions after reducing stock basis), debt basis is restored up "
                    "to original loan balance. If there is a net decrease (losses exceed income after "
                    "reducing stock basis to zero), debt basis is reduced. When the S corporation "
                    "repays the loan, gain is recognized to the extent the repayment exceeds the "
                    "reduced debt basis."
                ),
                "summary_text": "Debt basis: direct loans only (no guarantees). Restored by net income, reduced by excess losses.",
                "is_key_excerpt": True,
                "topic_tags": ["s_corp_basis", "form_7203"],
            },
            {
                "excerpt_label": "Part III — Loss limitation and carryover",
                "location_reference": "Part III Instructions",
                "excerpt_text": (
                    "Allowable loss is limited to the sum of stock basis (after distributions) and "
                    "debt basis. Loss limitation ordering: (1) first apply against stock basis, "
                    "(2) then against debt basis. Character of items is pro rata if limitation "
                    "applies. Disallowed losses and deductions carry forward to the next year and "
                    "are treated as incurred in the subsequent year (applied when basis is restored). "
                    "Carryforward is indefinite. After the basis limitation, losses may be further "
                    "limited by the at-risk rules (Form 6198) and passive activity rules (Form 8582)."
                ),
                "summary_text": "Losses: first vs stock basis, then debt basis. Disallowed carries forward indefinitely. Then at-risk → passive.",
                "is_key_excerpt": True,
                "topic_tags": ["s_corp_basis", "form_7203", "at_risk", "passive_activity"],
            },
        ],
        topics=["form_7203", "s_corp_basis", "s_corporation"],
        form_links=[
            {"form_code": "7203", "link_type": "governs"},
            {"form_code": "1120S", "link_type": "informs", "note": "K-1 data feeds Form 7203 basis computation"},
        ],
    ),
]
