"""Load the Form 4952 spec — Investment Interest Expense Deduction (2025, Created 5/28/25).
WO-17, 4th item in the SPINE S-16 federal-forms queue (after 8990 + Schedule H + 4684). Greenfield.

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
Form 4952 limits the investment interest expense deduction to net investment income (§163(d)). The
compute is relational: L3 total investment interest (current + indefinite prior-year carryforward) vs
L6 net investment income (investment income − investment expenses); the deduction (L8) = the smaller,
and the excess (L7) carries forward INDEFINITELY. The one judgment lever is the L4g election to include
qualified dividends (L4b) and net capital gain (L4e) in investment income — raising the L6 ceiling at
the cost of the preferential QD/cap-gain rate on the elected amount.

§163(d) is UNCHANGED by OBBBA for TY2025 (no "What's New" on the form). OBBBA's interest changes are
§163(j) BUSINESS interest (Form 8990) — a different provision. The only adjacent OBBBA item is §67(g)
misc-itemized-deduction permanence (affects the L5 exclusion, already true for 2025).

Greenfield: 4952 not in the 113-form prod set at the 2026-07-06 gap-check (downstream Sch A / Sch D /
QDCGT route TO 4952 but none authors it).

═══════════════════════════════════════════════════════════════════════════
v1 SCOPE — LOCKED (Ken's Gate-1 walk 2026-07-06; DECISIONS D-19). See f4952_source_brief.md.
═══════════════════════════════════════════════════════════════════════════
COMPUTES: (Q4) full Parts I-III — L3 = L1+L2; L4c/L4f/L4h; L6 = max(0, L4h-L5); L8 = min(L3, L6); L7 = max(0,
L3-L6) indefinite. (Q1) the L4g election mechanic (elected amount capped at 4b+4e, ordering 4e-then-4b) + rate-
tradeoff diagnostic. (Q2) entity_types 1040/1041, route L8 -> Sch A L9 / 1041 L10 + filing-exception diagnostic.
(Q3) L5 misc-itemized-suspension diagnostic + investment-interest exclusion diagnostic.

requires_human_review WALK ITEMS (W1-W4):
W1. §163(d) limitation: L8 = smaller of total investment interest (L3) or net investment income (L6); disallowed
    (L7 = L3 - L6) carries forward INDEFINITELY (L2 pulls prior-year L7). CONFIRM the min + indefinite carryforward.
W2. Investment income: L4h = L4c (4a-4b ordinary) + L4f (4d-4e short-term/ordinary gain) + L4g (elected-in). QD (4b)
    and net capital gain (4e) EXCLUDED unless elected. CONFIRM the 4c/4f/4h build.
W3. L4g election: elect up to 4b+4e into investment income; elected amount loses the preferential QD/cap-gain rate
    (Sch D Tax Worksheet coordination). CONFIRM the cap + rate consequence.
W4. L5 excludes 2%-floor misc itemized (TCJA-suspended through 2025, OBBBA-permanent); investment interest excludes
    QRI/passive/tax-exempt/§264/§263A. CONFIRM.

CARRIED [UNVERIFIED]: none — all facts verbatim vs FINAL 2025 Form 4952 (Created 5/28/25, instructions pp. 3-4) +
§163(d). The §67(g) misc-itemized permanence point is from secondary sources (no compute impact for 2025).

SAFETY GUARD — READY_TO_SEED stays False until Ken approves the review walk (W1-W4).
FLIPPED 2026-07-06 — Ken APPROVED ("Approve — flip, seed, export"): W1 §163(d) limit (L8 = min(L3, L6))
+ indefinite carryforward (L7), W2 investment income 4c/4f/4h, W3 the 4g election cap (<= 4b+4e) + rate
consequence, W4 L5 misc-itemized suspension + investment-interest exclusions. Validated (scratchpad/validate_4952.py, 26/0).
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from sources.models import (
    AuthorityExcerpt, AuthorityFormLink, AuthoritySource, AuthoritySourceTopic,
    AuthorityTopic, RuleAuthorityLink,
)
from specs.models import (
    FlowAssertion, FormDiagnostic, FormFact, FormLine, FormRule, TaxForm, TestScenario,
)

READY_TO_SEED = True

FORM_JURISDICTION = "federal"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1040", "1041"]

# Verified: no dollar constants (§163(d) is relational). Year-keyed note only.
MISC_ITEMIZED_SUSPENDED_THROUGH = 2025  # TCJA §67(g) 2%-floor misc suspension; OBBBA made it permanent


def _line3(l1, l2) -> float:
    """L3 total investment interest expense = current-year (L1) + prior-year disallowed carryforward (L2)."""
    return round(float(l1) + float(l2), 2)


def _investment_income(l4a, l4b, l4d, l4e, l4g) -> dict:
    """Part II: L4c = 4a - 4b; L4f = 4d - 4e; L4h = 4c + 4f + 4g (QD 4b + net cap gain 4e excluded unless in 4g)."""
    l4c = round(float(l4a) - float(l4b), 2)
    l4f = round(float(l4d) - float(l4e), 2)
    l4h = round(l4c + l4f + float(l4g), 2)
    return {"L4c": l4c, "L4f": l4f, "L4h": l4h}


def _net_investment_income(l4h, l5) -> float:
    """L6 net investment income = L4h - L5, floored at 0."""
    return round(max(0.0, float(l4h) - float(l5)), 2)


def _deduction(l3, l6) -> float:
    """L8 investment interest expense deduction = smaller of L3 or L6 (§163(d)(1))."""
    return round(min(float(l3), float(l6)), 2)


def _carryforward(l3, l6) -> float:
    """L7 disallowed carryforward = L3 - L6, floored at 0; carries forward INDEFINITELY (§163(d)(2))."""
    return round(max(0.0, float(l3) - float(l6)), 2)


def _elect_4g_cap(l4b, l4e) -> float:
    """L4g may not exceed the sum of L4b (qualified dividends) + L4e (net capital gain)."""
    return round(float(l4b) + float(l4e), 2)


AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("investment_interest_163d", "Form 4952 investment interest expense deduction (§163(d)): limited to net investment "
     "income (L8 = min(L3, L6)); indefinite carryforward (L7); the L4g election to include QD + net capital gain "
     "(loses the preferential rate)."),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_F4952", "source_type": "federal_form", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Form 4952 (2025) — Investment Interest Expense Deduction (instructions pp. 3-4)",
        "citation": "Form 4952 (2025), Cat. No. 13177Y, Created 5/28/25, Attach. Seq. No. 51 (no separate i4952 — instructions pp. 3-4)",
        "issuer": "Internal Revenue Service", "official_url": "https://www.irs.gov/pub/irs-pdf/f4952.pdf",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.6, "topics": ["investment_interest_163d"],
        "excerpts": [{
            "excerpt_label": "Full line map — Parts I-III (2025 verbatim)",
            "excerpt_text": (
                "Part I Total Investment Interest Expense: L1 investment interest expense paid or accrued in 2025; "
                "L2 disallowed investment interest expense from 2024 Form 4952, line 7; L3 = add lines 1 and 2. "
                "Part II Net Investment Income: L4a gross income from property held for investment (excluding any "
                "net gain from disposition); L4b qualified dividends included on 4a; L4c = 4a - 4b; L4d net gain "
                "from disposition of investment property; L4e smaller of 4d or net capital gain from that "
                "disposition; L4f = 4d - 4e; L4g amount from 4b and 4e elected to include in investment income "
                "(don't enter more than 4b + 4e); L4h investment income = add 4c, 4f, and 4g; L5 investment "
                "expenses; L6 net investment income = 4h - 5 (if zero or less, -0-). Part III: L7 disallowed "
                "investment interest expense carried forward to 2026 = line 3 - line 6 (if zero or less, -0-); "
                "L8 investment interest expense deduction = smaller of line 3 or line 6."
            ),
            "summary_text": "L3=1+2; L4c=4a-4b; L4f=4d-4e; L4h=4c+4f+4g; L6=max(0,4h-5); L7=max(0,3-6) indefinite; L8=min(3,6).",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "4g election + line 5 misc-itemized + routing (instructions pp. 3-4 verbatim substance)",
            "excerpt_text": (
                "In general, qualified dividends and net capital gain from the disposition of investment property "
                "are excluded from investment income; you can elect to include part or all on line 4g (don't enter "
                "more than 4b + 4e). CAUTION: the qualified dividends and net capital gain you elect to include on "
                "line 4g aren't eligible to be taxed at the qualified dividends or capital gains rates; also enter "
                "the 4g amount on the Schedule D Tax Worksheet line 3 (or Sch D (1041) line 25 / QD Tax Worksheet). "
                "The 4g amount is treated as attributable first to net capital gain (4e), then qualified dividends "
                "(4b). Line 5 investment expenses: allowed non-interest deductions directly connected with producing "
                "investment income; CAUTION - don't include miscellaneous itemized deductions, not allowed for tax "
                "years beginning after 12/31/2017 and before 1/1/2026. Line 8: individuals enter on Schedule A "
                "(Form 1040) line 9; estates and trusts enter on Form 1041 line 10. No 4952 required if investment "
                "income (interest + ordinary dividends - qualified dividends) exceeds investment interest expense, "
                "there are no other investment expenses, and no carryover of disallowed interest from 2024."
            ),
            "summary_text": "4g election loses preferential rate (Sch D Tax Wksht coord); L5 excludes 2%-misc (through 2025); L8 -> Sch A L9 (1040) / 1041 L10; filing exception (3 conditions).",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "IRC_163D", "source_type": "statute", "source_rank": "controlling",
        "jurisdiction_code": "US", "title": "IRC §163(d) — limitation on investment interest",
        "citation": "26 U.S.C. §163(d)(1)-(5)", "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/163",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.4, "topics": ["investment_interest_163d"],
        "excerpts": [{
            "excerpt_label": "§163(d)(1)/(2)/(4) — limitation, carryforward, net investment income (verbatim substance)",
            "excerpt_text": (
                "§163(d)(1): the deduction for investment interest for any taxable year is limited to the "
                "taxpayer's net investment income for that year. §163(d)(2): the amount disallowed is treated as "
                "investment interest paid or accrued in the succeeding taxable year (indefinite carryforward). "
                "§163(d)(4): net investment income = the excess of investment income over investment expenses; "
                "investment income means gross income from property held for investment plus the excess of net "
                "gain over net capital gain from disposition of investment property, PLUS so much of the net "
                "capital gain (and qualified dividend income) as the taxpayer ELECTS to take into account "
                "(§163(d)(4)(B) - the elected amount is not eligible for the §1(h) preferential rates); "
                "investment expenses are the deductions (other than interest) directly connected with the "
                "production of investment income. §163(d)(5): property held for investment excludes an interest "
                "in a passive activity."
            ),
            "summary_text": "§163(d)(1) deduction <= net investment income; (2) indefinite carryforward; (4) NII = investment income - expenses, with the elective cap-gain/QD inclusion (loses §1(h) rate); (5) excludes passive.",
            "is_key_excerpt": True,
        }],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_F4952", "4952", "governs"), ("IRC_163D", "4952", "governs"),
]


F4952_FACTS: list[dict] = [
    # Part I
    {"fact_key": "inv_interest_current", "label": "Investment interest expense paid/accrued in 2025 (L1)", "data_type": "decimal", "required": False, "sort_order": 1},
    {"fact_key": "disallowed_cf_prior", "label": "Disallowed investment interest carryforward from 2024 Form 4952 line 7 (L2)", "data_type": "decimal", "required": False, "sort_order": 2},
    # Part II
    {"fact_key": "gross_inv_income", "label": "Gross income from property held for investment, EXCLUDING net disposition gain (L4a)", "data_type": "decimal", "required": False, "sort_order": 3},
    {"fact_key": "qualified_dividends", "label": "Qualified dividends included on line 4a (L4b) — excluded from investment income unless elected", "data_type": "decimal", "required": False, "sort_order": 4},
    {"fact_key": "net_gain_disposition", "label": "Net gain from disposition of investment property (L4d)", "data_type": "decimal", "required": False, "sort_order": 5},
    {"fact_key": "net_capital_gain", "label": "Net capital gain from that disposition — smaller of 4d or net cap gain (L4e); excluded unless elected", "data_type": "decimal", "required": False, "sort_order": 6},
    {"fact_key": "elect_4g", "label": "Amount from 4b + 4e ELECTED to include in investment income (L4g; <= 4b + 4e)", "data_type": "decimal", "required": False, "sort_order": 7,
     "notes": "W3. Elected amount loses the preferential QD/cap-gain rate; ordering = net capital gain (4e) first, then qualified dividends (4b)."},
    {"fact_key": "investment_expenses", "label": "Investment expenses — non-interest, directly connected (e.g., depreciation/depletion); NOT 2%-floor misc (L5)", "data_type": "decimal", "required": False, "sort_order": 8,
     "notes": "W4. 2%-floor miscellaneous itemized deductions are suspended through 2025 (OBBBA-permanent) — excluded."},
    # routing
    {"fact_key": "filer_entity_type", "label": "Filer type (drives L8 routing: 1040 -> Sch A L9; 1041 -> Form 1041 L10)", "data_type": "choice", "required": False, "sort_order": 9,
     "choices": ["1040", "1041"]},
]

F4952_RULES: list[dict] = [
    {"rule_id": "R-4952-L3", "title": "Total investment interest expense (L3)", "rule_type": "calculation",
     "formula": "L3 = inv_interest_current + disallowed_cf_prior",
     "inputs": ["inv_interest_current", "disallowed_cf_prior"], "outputs": ["l3_total_interest"], "sort_order": 1,
     "description": "Part I: L3 total investment interest = L1 current-year investment interest + L2 disallowed carryforward from the 2024 Form 4952 line 7."},
    {"rule_id": "R-4952-INCOME", "title": "Investment income (L4c/L4f/L4h)", "rule_type": "calculation",
     "formula": "L4c = gross_inv_income - qualified_dividends ; L4f = net_gain_disposition - net_capital_gain ; L4h = L4c + L4f + elect_4g",
     "inputs": ["gross_inv_income", "qualified_dividends", "net_gain_disposition", "net_capital_gain", "elect_4g"], "outputs": ["l4c", "l4f", "l4h_investment_income"], "sort_order": 2,
     "description": "W2. Part II: L4c = 4a - 4b (ordinary investment income net of QD); L4f = 4d - 4e (short-term/ordinary disposition gain); L4h investment income = 4c + 4f + 4g. Qualified dividends (4b) and net capital gain (4e) are EXCLUDED unless elected in on 4g."},
    {"rule_id": "R-4952-NII", "title": "Net investment income (L6)", "rule_type": "calculation",
     "formula": "L6 = max(0, l4h_investment_income - investment_expenses)",
     "inputs": ["investment_expenses"], "outputs": ["l6_net_investment_income"], "sort_order": 3,
     "description": "W1. L6 net investment income = L4h investment income - L5 investment expenses, floored at 0. L5 excludes 2%-floor miscellaneous itemized deductions (suspended through 2025)."},
    {"rule_id": "R-4952-DEDUCT", "title": "§163(d) deduction + indefinite carryforward (L8/L7)", "rule_type": "calculation",
     "formula": "L8 = min(l3_total_interest, l6_net_investment_income) ; L7 = max(0, l3_total_interest - l6_net_investment_income)",
     "inputs": [], "outputs": ["l8_deduction", "l7_carryforward"], "sort_order": 4,
     "description": "W1. Part III: L8 investment interest expense deduction = smaller of L3 or L6 (§163(d)(1)) -> Schedule A line 9 (1040) / Form 1041 line 10. L7 disallowed = L3 - L6 (floored at 0) carries forward INDEFINITELY (§163(d)(2); feeds next year's L2)."},
    {"rule_id": "R-4952-4G", "title": "L4g election — include QD + net capital gain (cap + rate consequence)", "rule_type": "calculation",
     "formula": "elect_4g <= qualified_dividends + net_capital_gain ; elected amount taxed at ordinary rates (not §1(h)); attributed 4e first then 4b",
     "inputs": ["qualified_dividends", "net_capital_gain", "elect_4g"], "outputs": ["elect_4g_cap"], "sort_order": 5,
     "description": "W3. The L4g election raises the L6 ceiling by including qualified dividends (4b) and net capital gain (4e) in investment income (capped at 4b + 4e), attributed first to net capital gain then qualified dividends. The elected amount is NOT eligible for the preferential QD/capital-gains rate (§163(d)(4)(B)/§1(h)) — coordinate via the Schedule D Tax Worksheet."},
]

F4952_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-4952-L3", "IRS_2025_F4952", "primary", "Part I L1-3"),
    ("R-4952-INCOME", "IRS_2025_F4952", "primary", "Part II L4a-4h"),
    ("R-4952-INCOME", "IRC_163D", "secondary", "§163(d)(4) investment income"),
    ("R-4952-NII", "IRS_2025_F4952", "primary", "L5-6"),
    ("R-4952-NII", "IRC_163D", "secondary", "§163(d)(4) net investment income"),
    ("R-4952-DEDUCT", "IRS_2025_F4952", "primary", "Part III L7-8"),
    ("R-4952-DEDUCT", "IRC_163D", "primary", "§163(d)(1)/(2) limit + indefinite carryforward"),
    ("R-4952-4G", "IRS_2025_F4952", "primary", "L4g election + CAUTION"),
    ("R-4952-4G", "IRC_163D", "secondary", "§163(d)(4)(B) elective inclusion loses §1(h) rate"),
]

F4952_LINES: list[dict] = [
    {"line_number": "L3", "description": "Total investment interest expense (L1 + L2)", "line_type": "subtotal", "source_rules": ["R-4952-L3"], "sort_order": 1},
    {"line_number": "L4h", "description": "Investment income (4c + 4f + 4g)", "line_type": "subtotal", "source_rules": ["R-4952-INCOME"], "sort_order": 2},
    {"line_number": "L6", "description": "Net investment income (4h - 5)", "line_type": "subtotal", "source_rules": ["R-4952-NII"], "sort_order": 3},
    {"line_number": "L7", "description": "Disallowed carryforward to 2026 (indefinite)", "line_type": "calculated", "source_rules": ["R-4952-DEDUCT"], "sort_order": 4},
    {"line_number": "L8", "description": "Investment interest expense deduction -> Sch A L9 / 1041 L10", "line_type": "calculated", "source_rules": ["R-4952-DEDUCT"], "sort_order": 5},
]

F4952_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_4952_LIMIT", "title": "Investment interest limited to net investment income (excess carries forward)", "severity": "info",
     "condition": "l7_carryforward > 0",
     "message": "The investment interest expense deduction is limited to net investment income (§163(d)). The excess (line 7 = total investment interest - net investment income) is disallowed this year but carries forward INDEFINITELY - it becomes investment interest 'paid or accrued' next year (enter it on the 2026 Form 4952 line 2). Track the carryforward.",
     "notes": "W1."},
    {"diagnostic_id": "D_4952_4G_RATE", "title": "The 4g election loses the preferential QD/capital-gains rate", "severity": "warning",
     "condition": "elect_4g > 0",
     "message": "By electing (line 4g) to include qualified dividends and/or net capital gain in investment income, you increase the investment interest you can deduct now - but the elected amount is NO LONGER eligible for the preferential qualified-dividends / long-term capital-gains rate; it is taxed at ordinary rates. Enter the 4g amount on the Schedule D Tax Worksheet line 3 (or the Qualified Dividends Tax Worksheet). Weigh the extra deduction against the rate cost.",
     "notes": "W3."},
    {"diagnostic_id": "D_4952_4G_CAP", "title": "Line 4g cannot exceed qualified dividends + net capital gain", "severity": "error",
     "condition": "elect_4g > qualified_dividends + net_capital_gain",
     "message": "The amount elected on line 4g may not exceed the sum of line 4b (qualified dividends) + line 4e (net capital gain). Reduce line 4g to at most 4b + 4e. The election is attributed first to net capital gain (4e), then to qualified dividends (4b).",
     "notes": "W3."},
    {"diagnostic_id": "D_4952_MISC", "title": "Line 5 excludes 2%-floor miscellaneous itemized deductions", "severity": "info",
     "condition": "investment_expenses > 0",
     "message": "Line 5 investment expenses are non-interest deductions directly connected with producing investment income (e.g., depreciation or depletion on investment-income property). Do NOT include 2%-floor miscellaneous itemized deductions - they are suspended for tax years 2018-2025 (and OBBBA §67(g) made the suspension permanent). Include a Schedule K-1 investment expense only if it is otherwise deductible.",
     "notes": "W4."},
    {"diagnostic_id": "D_4952_EXCL", "title": "Investment interest excludes several interest categories", "severity": "info",
     "condition": "inv_interest_current > 0",
     "message": "Line 1 investment interest does NOT include: personal or qualified-residence interest (§163(h)); interest allocable to a passive activity (see Form 8582, §469); capitalized interest (§263A); interest allocable to tax-exempt income (§265); or §264 interest on post-6/8/1997 insurance/annuity contracts. Property held for investment excludes an interest in a passive activity.",
     "notes": "W4."},
    {"diagnostic_id": "D_4952_FILE_EXC", "title": "Form 4952 not required if the 3-part exception applies", "severity": "info",
     "condition": "disallowed_cf_prior == 0 and investment_expenses == 0",
     "message": "You don't have to file Form 4952 if ALL apply: (1) your investment income (interest + ordinary dividends minus qualified dividends) is more than your investment interest expense; (2) you have no other deductible investment expenses; and (3) you have no carryover of disallowed investment interest from 2024. You may then deduct the investment interest directly on Schedule A line 9.",
     "notes": "Q2 exception."},
    {"diagnostic_id": "D_4952_ROUTE", "title": "Line 8 routing (individual vs estate/trust)", "severity": "info",
     "condition": "l8_deduction > 0",
     "message": "Carry the line 8 investment interest expense deduction to: Schedule A (Form 1040) line 9 for individuals; Form 1041 line 10 for estates and trusts. The part attributable to royalties goes to Schedule E; the part attributable to a non-passive trade or business goes to that business's schedule.",
     "notes": "Q2 routing."},
]

F4952_SCENARIOS: list[dict] = [
    {"scenario_name": "4952-A — limited to net investment income (carryforward)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"inv_interest_current": 10000, "gross_inv_income": 6000},
     "expected_outputs": {"l3_total_interest": 10000.0, "l4h_investment_income": 6000.0, "l6_net_investment_income": 6000.0, "l8_deduction": 6000.0, "l7_carryforward": 4000.0},
     "notes": "L3 10,000; investment income 6,000; L8 = min(10,000, 6,000) = 6,000; L7 = 4,000 disallowed carries forward indefinitely."},
    {"scenario_name": "4952-B — fully deductible (interest < income)", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"inv_interest_current": 3000, "gross_inv_income": 6000},
     "expected_outputs": {"l3_total_interest": 3000.0, "l6_net_investment_income": 6000.0, "l8_deduction": 3000.0, "l7_carryforward": 0.0},
     "notes": "Interest 3,000 < income 6,000 -> fully deductible; no carryforward. (Filing exception may apply.)"},
    {"scenario_name": "4952-C — prior-year carryforward stacks (L2)", "scenario_type": "edge", "sort_order": 3,
     "inputs": {"inv_interest_current": 5000, "disallowed_cf_prior": 4000, "gross_inv_income": 6000},
     "expected_outputs": {"l3_total_interest": 9000.0, "l6_net_investment_income": 6000.0, "l8_deduction": 6000.0, "l7_carryforward": 3000.0},
     "notes": "L3 = 5,000 + 4,000 prior = 9,000; income 6,000; L8 = 6,000; L7 = 3,000 rolls to next year (indefinite)."},
    {"scenario_name": "4952-D — 4g election frees deduction (at ordinary rate)", "scenario_type": "edge", "sort_order": 4,
     "inputs": {"inv_interest_current": 5000, "gross_inv_income": 2000, "qualified_dividends": 1500, "net_gain_disposition": 8000, "net_capital_gain": 8000, "elect_4g": 5000},
     "expected_outputs": {"l4c": 500.0, "l4f": 0.0, "l4h_investment_income": 5500.0, "l6_net_investment_income": 5500.0, "l8_deduction": 5000.0, "l7_carryforward": 0.0, "diagnostic": "D_4952_4G_RATE"},
     "notes": "4c = 2,000-1,500 = 500; 4f = 8,000-8,000 = 0; elect 4g 5,000 (<= 4b 1,500 + 4e 8,000 = 9,500); 4h = 5,500; L8 = min(5,000, 5,500) = 5,000 fully deductible. Without the election 4h = 500 -> L8 only 500 (election freed 4,500 at ordinary rates)."},
    {"scenario_name": "4952-E — expenses exceed income (net investment income 0)", "scenario_type": "edge", "sort_order": 5,
     "inputs": {"inv_interest_current": 4000, "gross_inv_income": 2000, "investment_expenses": 3000},
     "expected_outputs": {"l4h_investment_income": 2000.0, "l6_net_investment_income": 0.0, "l8_deduction": 0.0, "l7_carryforward": 4000.0},
     "notes": "L5 3,000 > L4h 2,000 -> L6 = 0; L8 = 0; entire L3 4,000 carries forward."},
]

FORMS: list[dict] = [
    {
        "identity": {"form_number": "4952", "form_title": "Form 4952 — Investment Interest Expense Deduction (2025)",
                     "notes": "WO-17 (SPINE S-16, 4th; DECISIONS D-19). §163(d): L3 total investment interest (L1 current + L2 indefinite carryforward) vs L6 net investment income (L4h investment income - L5 expenses); L8 deduction = min(L3, L6) -> Schedule A L9 (1040) / Form 1041 L10 (estate/trust); L7 = max(0, L3 - L6) carries forward INDEFINITELY. L4g election includes qualified dividends (4b) + net capital gain (4e) in investment income (cap 4b+4e, ordering 4e-then-4b) at the cost of the preferential rate. L5 excludes 2%-floor misc itemized (suspended through 2025, OBBBA-permanent). §163(d) UNCHANGED by OBBBA (that's §163(j)/8990). entity_types 1040/1041."},
        "facts": F4952_FACTS, "rules": F4952_RULES, "rule_links": F4952_RULE_LINKS,
        "lines": F4952_LINES, "diagnostics": F4952_DIAGNOSTICS, "scenarios": F4952_SCENARIOS,
    },
]

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-4952-LIMIT", "title": "Investment interest deduction = min(total interest, net investment income)", "assertion_type": "reconciliation",
     "entity_types": ["1040", "1041"], "status": "draft", "sort_order": 1,
     "description": "Form 4952 line 8 = smaller of line 3 (total investment interest) or line 6 (net investment income) -> Schedule A line 9 / Form 1041 line 10.",
     "definition": {"rule": "R-4952-DEDUCT", "check": "l8_deduction = min(l3_total_interest, l6_net_investment_income)"}},
    {"assertion_id": "FA-4952-CF", "title": "Disallowed investment interest carries forward indefinitely", "assertion_type": "reconciliation",
     "entity_types": ["1040", "1041"], "status": "draft", "sort_order": 2,
     "description": "Line 7 = max(0, line 3 - line 6) is disallowed this year and carries to next year's line 2 with no expiration (§163(d)(2)).",
     "definition": {"rule": "R-4952-DEDUCT", "check": "l7_carryforward = max(0, l3_total_interest - l6_net_investment_income)"}},
    {"assertion_id": "FA-4952-4G", "title": "4g election includes QD + net cap gain (loses preferential rate)", "assertion_type": "reconciliation",
     "entity_types": ["1040", "1041"], "status": "draft", "sort_order": 3,
     "description": "L4h investment income = 4c + 4f + 4g, where 4g (<= 4b + 4e) is the electively-included qualified dividends / net capital gain, which then lose the §1(h) preferential rate.",
     "definition": {"rule": "R-4952-INCOME", "check": "l4h = (4a-4b) + (4d-4e) + elect_4g ; elect_4g <= 4b + 4e"}},
]


class Command(BaseCommand):
    help = "Load the Form 4952 spec (Investment Interest Expense Deduction, 2025). Refuses to seed until READY_TO_SEED=True (W1-W4)."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad Form 4952 spec (Investment Interest Expense Deduction)\n"))
        self._load_topics()
        sources = self._load_sources()
        for spec in FORMS:
            form = self._upsert_form(spec["identity"])
            self._upsert_facts(form, spec["facts"])
            rules = self._upsert_rules(form, spec["rules"])
            self._upsert_links(rules, sources, spec["rule_links"])
            self._upsert_lines(form, spec["lines"])
            self._upsert_diag(form, spec["diagnostics"])
            self._upsert_tests(form, spec["scenarios"])
        self._upsert_form_links(sources)
        self._load_fa()
        self._report()

    def _guard(self):
        empty = []
        for spec in FORMS:
            fn = spec["identity"]["form_number"]
            for key in ("facts", "rules", "lines", "diagnostics", "scenarios", "rule_links"):
                if not spec[key]:
                    empty.append(f"{fn}.{key}")
        if not FLOW_ASSERTIONS:
            empty.append("FLOW_ASSERTIONS")
        if not READY_TO_SEED or empty:
            still = "\n  ".join(f"- {n}" for n in empty) or "(all populated)"
            raise CommandError(
                "\nREFUSING TO SEED FORM 4952: not cleared.\n\n"
                "Gated until Ken reviews (W1 §163(d) limit + indefinite carryforward; W2 investment\n"
                "income 4c/4f/4h; W3 the 4g election cap + rate consequence; W4 L5 misc-itemized +\n"
                f"exclusions) and flips the sentinel.\n\nREADY_TO_SEED = {READY_TO_SEED}\n\nEmpty:\n  {still}\n"
            )

    def _load_topics(self):
        ct = 0
        for code, name in AUTHORITY_TOPICS:
            _, created = AuthorityTopic.objects.update_or_create(topic_code=code, defaults={"topic_name": name})
            ct += 1 if created else 0
        self.stdout.write(f"Topics: {ct} new")

    def _load_sources(self) -> dict:
        sources: dict = {}
        for sd in AUTHORITY_SOURCES:
            sd = dict(sd)
            exc = sd.pop("excerpts", [])
            tcs = sd.pop("topics", [])
            src, _ = AuthoritySource.objects.update_or_create(source_code=sd["source_code"], defaults=sd)
            sources[src.source_code] = src
            for e in exc:
                e = dict(e)
                AuthorityExcerpt.objects.update_or_create(authority_source=src, excerpt_label=e["excerpt_label"], defaults=e)
            for tc in tcs:
                t = AuthorityTopic.objects.filter(topic_code=tc).first()
                if t:
                    AuthoritySourceTopic.objects.get_or_create(authority_source=src, authority_topic=t)
        self.stdout.write(f"Sources ready: {len(sources)}")
        return sources

    def _upsert_form(self, identity: dict) -> TaxForm:
        form, created = TaxForm.objects.update_or_create(
            form_number=identity["form_number"], jurisdiction=FORM_JURISDICTION, tax_year=FORM_TAX_YEAR, version=FORM_VERSION,
            defaults={"form_title": identity["form_title"], "entity_types": FORM_ENTITY_TYPES, "status": FORM_STATUS, "notes": identity["notes"]},
        )
        self.stdout.write(f"{'Created' if created else 'Updated'} {identity['form_number']} {FORM_ENTITY_TYPES}")
        return form

    def _upsert_facts(self, form, facts):
        for f in facts:
            f = dict(f)
            FormFact.objects.update_or_create(tax_form=form, fact_key=f.pop("fact_key"), defaults=f)
        self.stdout.write(f"  {len(facts)} facts")

    def _upsert_rules(self, form, rules_data) -> dict:
        created = {}
        for r in rules_data:
            r = dict(r)
            rule, _ = FormRule.objects.update_or_create(tax_form=form, rule_id=r.pop("rule_id"), defaults=r)
            created[rule.rule_id] = rule
        self.stdout.write(f"  {len(created)} rules")
        return created

    def _upsert_links(self, rules, sources, rule_links):
        ct = 0
        for rid, sc, lvl, note in rule_links:
            rule, src = rules.get(rid), sources.get(sc)
            if rule and src:
                RuleAuthorityLink.objects.get_or_create(form_rule=rule, authority_source=src, defaults={"support_level": lvl, "relevance_note": note})
                ct += 1
        self.stdout.write(f"  {ct} authority links")

    def _upsert_lines(self, form, lines):
        for ln in lines:
            ln = dict(ln)
            FormLine.objects.update_or_create(tax_form=form, line_number=ln.pop("line_number"), defaults=ln)
        self.stdout.write(f"  {len(lines)} lines")

    def _upsert_diag(self, form, diags):
        for d in diags:
            d = dict(d)
            FormDiagnostic.objects.update_or_create(tax_form=form, diagnostic_id=d.pop("diagnostic_id"), defaults=d)
        self.stdout.write(f"  {len(diags)} diagnostics")

    def _upsert_tests(self, form, scenarios):
        for t in scenarios:
            t = dict(t)
            TestScenario.objects.update_or_create(tax_form=form, scenario_name=t.pop("scenario_name"), defaults=t)
        self.stdout.write(f"  {len(scenarios)} test scenarios")

    def _upsert_form_links(self, sources):
        for sc, fc, lt in AUTHORITY_FORM_LINKS:
            src = sources.get(sc) or AuthoritySource.objects.filter(source_code=sc).first()
            if src:
                AuthorityFormLink.objects.get_or_create(authority_source=src, form_code=fc, link_type=lt, defaults={"note": f"{sc} -> {fc}"})

    def _load_fa(self):
        for a in FLOW_ASSERTIONS:
            a = dict(a)
            FlowAssertion.objects.update_or_create(assertion_id=a.pop("assertion_id"), defaults=a)
        self.stdout.write(f"  {len(FLOW_ASSERTIONS)} flow assertions")

    def _report(self):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("Form 4952 loaded.")
        self.stdout.write(f"  4952: facts {len(F4952_FACTS)} / rules {len(F4952_RULES)} / lines {len(F4952_LINES)} / diag {len(F4952_DIAGNOSTICS)} / tests {len(F4952_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}")
        self.stdout.write("=" * 60)
