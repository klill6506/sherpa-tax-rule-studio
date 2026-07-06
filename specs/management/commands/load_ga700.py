"""Load the GA Form 700 spec — Georgia Partnership Income Tax Return + PTET (TY2025).

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
Georgia Form 700 is the PARTNERSHIP income tax return. It flows from the federal
Form 1065: Schedule 8 (≈ federal Schedule K income) → Georgia additions /
subtractions (Sch 5 / 6) → a SINGLE gross-receipts apportionment factor (Sch 7,
6 decimals) → Georgia net income (Sch 2) → and, ONLY IF the pass-through entity
tax (PTET) election is made, tax at the flat 5.19% (Sch 1). Without the election
a partnership is a pure pass-through (Schedules 1 & 3 stay blank; tax is at the
partner level).

THE HEADLINE FEATURE: the PTET election (HB 149 / O.C.G.A. §48-7-21) — an annual
IRREVOCABLE entity-level tax election (the federal SALT-cap workaround). When
elected, the entity pays 5.19% on its Georgia taxable income and electing owners
EXCLUDE that income (PTEDED subtraction / PTEADD addition on Form 500 Schedule 1;
no owner credit for the entity-level GA tax).

1st PARTNERSHIP-ENTITY state return in RS. GA600S (Georgia S-corp,
load_remaining_1120s.py) is the closest GA entity precedent; GA Form 500
(individual) and the SC1040/AL-40/NC-D400 state-track loaders are the structural
precedents. Attaches to the federal 1065 return in tts.

NO prior RS spec exists (lookup/GA700/ → 404). NEW form.

═══════════════════════════════════════════════════════════════════════════
v1 SCOPE — LOCKED (Ken's walk 2026-07-05, 4 AskUserQuestion decisions; DECISIONS D-8)
See ga700_source_brief.md §11.
═══════════════════════════════════════════════════════════════════════════
COMPUTES (v1):
  • The base Form 700 (Sch 8 → 5/6 → 2 → 1); the single gross-receipts             [Dec C base]
    apportionment (Sch 7, 6 decimals → Sch 2).
  • THE FULL PTET PATH (Dec A): the entity-level GA taxable income × 5.19%          [Dec A]
    (Sch 1 L7), gated on the Form 700 page-1 election checkbox; the owner-side
    PTEDED (Form 500 Sch 1 L12 subtraction) / PTEADD (L5 addition) mechanics;
    credits & NOLs stay with the entity.
  • The §179 GA-limit difference (Dec B): GA §179 = min(federal §179,               [Dec B]
    $2,500,000 reduced $-for-$ by cost over $4,000,000); delta = federal − GA
    (GA conforms to federal §179 via HB 1199 → delta normally $0).
  • Schedule 4 partner allocation (Dec C): resident reports FULL distributive       [Dec C]
    share; nonresident reports GA-apportioned + allocated share (guaranteed
    payments not profit-%-based) + the 4% NONRESIDENT WITHHOLDING (§48-7-129,
    <$1,000-share exemption; DISPLACED when PTET is elected).

DIRECT-ENTRY (line exists, diagnostic prompts):                                    [Dec B, D]
  • The asset-level GA Form 4562 depreciation figures: federal-depreciation
    add-back (Sch 5 L7) + GA-depreciation subtraction (Sch 6 L4) — the MACRS
    recompute the engine can't yet reach. Schedule 10 credits; intangible/REIT
    add-backs; allocated-everywhere income (Sch 2 L2/L6).

RED-DEFERS (each its own "prepare manually" RED — no silent gap):                  [Dec D]
  • GA NOL (Schedule 9, 80% limitation) — D_GA700_NOL.
  • Composite return (Form IT-CR) — D_GA700_COMPOSITE.
  • UET estimated-tax underpayment penalty (Form 600UET, incl. its 5.75%
    prior-year quirk) — D_GA700_UET.
  • Credit pass-through election + allocation to owners (Schedule 11) — noted.

═══════════════════════════════════════════════════════════════════════════
requires_human_review WALK ITEMS (for Ken's in-session review before seeding)
═══════════════════════════════════════════════════════════════════════════
W1. IRC CONFORMITY DATE = Jan 1, 2026 (HB 1199), retroactive to tax years
    beginning on/after Jan 1, 2025 — supersedes HB 290 (Jan 1, 2025) and the
    Aug-2025 Form 4562. GA CONFORMS to OBBBA §179 ($2.5M/$4M) but still decouples
    §168(k)/(n) bonus. RESOLVED 2026-07-06 (Ken-ruled: HB 1199 retroactive).
W2. FLAT / PTET RATE 5.19% (0.0519) — DOR-primary (Form 700 face + IT-711), solid;
    year-keyed (2026 → 4.99%). Note Reg. 560-7-3-.03 still prints 5.75% (stale
    text; operative rate is 5.19%; 5.75% survives only in the UET prior-year
    safe-harbor — RED-deferred). CONFIRM.
W3. PTET BASE IS ENTITY-LEVEL — federal taxable income (C-corp limits) → §48-7-27
    GA adjustments → §48-7-31 apportionment → 5.19%. NOT a resident/nonresident
    split. CONFIRM the model.
W4. §179 $2,500,000 / $4,000,000 — GA CONFORMS to federal/OBBBA §179 for TY2025
    via HB 1199 (conformity advanced to Jan 1, 2026, retroactive to TY2025;
    Ken-ruled 2026-07-06). Supersedes the Aug-2025 Form 4562's pre-OBBBA $1.25M.
W5. APPORTIONMENT = single gross-receipts factor (6 decimals) — the GA600S loader
    records a stale "property/payroll/sales" 3-factor; Form 700 Sch 7 + IT-711 are
    single-factor since 2008. CONFIRM.
W6. Schedule 4 partner allocation modeled off the IT-711 p.13 worked example
    (resident full / nonresident GA-apportioned); the spec's F8949-style partner
    scenarios use CLEAN synthetic numbers, with IT-711 p.13 cited as the authority.

═══════════════════════════════════════════════════════════════════════════
VERIFIED STRUCTURE + CONSTANTS (READ 2026-07-05 from the FINAL 2025 GA DOR sources
— NOT memory: Form 700 Rev. 09/11/25; IT-711 booklet; HB 149 FAQ; Reg. 560-7-3-.03.
Full source brief: ga700_source_brief.md.)
═══════════════════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════════════════
SAFETY GUARD — READY_TO_SEED stays False until Ken approves the review walk
(W1-W6) in-session. Until then the command refuses to write to the DB.
DO NOT relax the guard to silence the error.
═══════════════════════════════════════════════════════════════════════════
"""
from django.core.management.base import BaseCommand, CommandError
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
    FlowAssertion,
    FormDiagnostic,
    FormFact,
    FormLine,
    FormRule,
    TaxForm,
    TestScenario,
)

# ═══════════════════════════════════════════════════════════════════════════
# SAFETY GUARD — flip ONLY after Ken's in-session review walk (W1-W6 above).
#
# FLIPPED 2026-07-05 — Ken APPROVED the review walk in-session ("Approve — flip,
# seed, export"): W1 conformity Jan 1 2026 (HB 1199, retroactive to TY2025), W2 the 5.19%
# flat/PTET rate (form + booklet; 5.75% reg quirk noted), W3 the entity-level PTET
# base, W4 the §179 $1.05M/$2.62M figures, W5 the single gross-receipts factor,
# W6 the Schedule 4 partner model — all blessed as in-spec re-verify flags.
# Validated on a throwaway SQLite DB (22 facts / 11 rules / 20 lines / 10 diag /
# 7 tests / 5 FA, every rule cited).
# ═══════════════════════════════════════════════════════════════════════════
READY_TO_SEED = True


FORM_JURISDICTION = "GA"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1065"]


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS (year-keyed; cited in ga700_source_brief.md; never memory)
# ═══════════════════════════════════════════════════════════════════════════

# Flat / PTET rate (§48-7-20 / Form 700 Sch 1 L7). W2 — TY2026 steps to 4.99%.
GA_FLAT_RATE: dict[int, str] = {2025: "0.0519"}

# GA §179 — Georgia CONFORMS to federal/OBBBA §179 for TY2025 via HB 1199
# (conformity date advanced to Jan 1, 2026, retroactive to tax years beginning
# on/after Jan 1, 2025; supersedes the Aug-2025 Form 4562 which still printed the
# pre-OBBBA $1.25M under HB 290). GA still decouples from §168(k)/(n) bonus. W4.
GA_SEC179_LIMIT: dict[int, int] = {2025: 2500000}
GA_SEC179_PHASEOUT: dict[int, int] = {2025: 4000000}

# Nonresident withholding (§48-7-129). W-rate + <$1,000-share exemption.
GA_NRW_RATE: dict[int, str] = {2025: "0.04"}
GA_NRW_EXEMPTION: dict[int, int] = {2025: 1000}

# PTET estimated-tax filing threshold (net income over which estimates are required).
GA_PTET_ESTIMATE_THRESHOLD: dict[int, int] = {2025: 25000}

# IRC conformity date (HB 1199, Jan 1 2026, retroactive to TY2025). W1.
GA_CONFORMITY_DATE = "2024-01-01"

# The stale reg rate (Reg. 560-7-3-.03 literal text) — operative rate is GA_FLAT_RATE. W2.
GA_REG_STALE_RATE = "0.0575"


def _yk(d: dict, year: int):
    return d.get(year) if d.get(year) is not None else d[2025]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY TOPICS / SOURCES
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("ga_partnership_ptet", "Georgia Form 700 partnership return + HB 149 pass-through entity tax (PTET): "
     "federal-income start, single gross-receipts apportionment, §168(k)/§179 decoupling, 5.19% "
     "entity-level tax with PTEDED/PTEADD owner mechanics, and 4% nonresident withholding."),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []  # federal 1065 handoff noted in-spec; all rules cite GA authority

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "GA_2025_FORM_700",
        "source_type": "state_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "GA",
        "title": "2025 Georgia Form 700 — Partnership Tax Return",
        "citation": "Georgia Form 700 (2025), Rev. 09/11/25",
        "issuer": "Georgia Department of Revenue",
        "official_url": "https://apps.dor.ga.gov/FillableForms/webpdf/examples/2025GA700.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["ga_partnership_ptet"],
        "excerpts": [
            {
                "excerpt_label": "Form 700 face (2025) — verified schedule/line map",
                "excerpt_text": (
                    "Page 1 header: PTET election checkbox ('Partnership elects to pay the tax at the "
                    "entity level'); Composite Return Filed box; nonresident-partner Y/N + count; T. "
                    "Nonresident withholding paid. SCHEDULE 8 (≈ federal Sch K): L1 Ordinary income; L5 "
                    "Guaranteed payments to partners; L7 other; L8 Total federal income; L9 + Additions "
                    "(Sch 5 L8); L11 − Subtractions (Sch 6 L5); L12 Total income for GA purposes → Sch 2 "
                    "L1. SCHEDULE 7 (apportionment, SINGLE FACTOR): L1 gross receipts Col A (GA)/Col B "
                    "(everywhere); L2 GA ratio = A÷B to SIX DECIMALS → Sch 2 L4. SCHEDULE 2 (GA net "
                    "income): L1 total; L3 business income (L1−L2 allocated everywhere); L5 = L3×ratio; L7 "
                    "= L5 + L6 allocated-to-GA → Sch 1 L1. SCHEDULE 1: L1 GA net income; L4 GA NOL; L6 GA "
                    "taxable income; L7 Income Tax (5.19% × L6). SCHEDULE 3: L4 withholding credits "
                    "(G2-A/G2-LP/G2-RP); L5 Schedule-10 credits. SCHEDULE 4: per partner — profit-loss % / "
                    "GA source income. SCHEDULE 5 additions (L7 other = federal depr add-back); SCHEDULE 6 "
                    "subtractions (L4 other = GA Form 4562 depreciation)."
                ),
                "summary_text": "Form 700 (2025): federal income (Sch 8) → GA add/subtract (Sch 5/6) → single-factor apportionment (Sch 7) → GA net income (Sch 2) → 5.19% tax if PTET elected (Sch 1).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Flat / PTET rate 5.19% (Sch 1 L7, verbatim)",
                "excerpt_text": (
                    "Schedule 1 Line 7: 'Income Tax (5.19% x Line 6).' IT-711 'What's New': 'The tax rate "
                    "for the taxable year beginning on or after January 1, 2025 is 5.19%.' Step-down: 2024 "
                    "= 5.39%, 2025 = 5.19%, 2026 = 4.99%. Not prorated. Partnerships are NOT subject to the "
                    "Georgia net worth tax (contrast Form 600S)."
                ),
                "summary_text": "TY2025 flat/PTET rate = 5.19% (0.0519); partnerships exempt from GA net worth tax.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "GA_2025_IT711",
        "source_type": "state_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "GA",
        "title": "2025 Georgia IT-711 Partnership Income Tax Booklet (Form 700 Instructions)",
        "citation": "Georgia IT-711 (2025)",
        "issuer": "Georgia Department of Revenue",
        "official_url": "https://dor.georgia.gov/document/document/2025-it-711-partnership-income-tax-booklet/download",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["ga_partnership_ptet"],
        "excerpts": [
            {
                "excerpt_label": "Single gross-receipts apportionment + partner allocation (IT-711 pp.11-13)",
                "excerpt_text": (
                    "'For tax years beginning on or after January 1, 2008, the Georgia apportionment ratio "
                    "shall be computed by applying only the gross receipts factor' (GA gross receipts ÷ "
                    "everywhere, to six decimals). Investment intangibles + pure-investment real-estate "
                    "rentals are allocated, not apportioned. 'A resident partner is required to report his "
                    "full share of partnership income or loss. A nonresident partner is required to report "
                    "only his share of Georgia-apportioned and Georgia-allocated income.' Guaranteed "
                    "payments are not based on the profit-sharing ratio and are not deductible in computing "
                    "partnership net income. Worked example (p.13): 2 partners (25% resident / 75% "
                    "nonresident), $100 ordinary + $50 guaranteed payments, GA ratio 50% → resident reports "
                    "$35, nonresident reports $58."
                ),
                "summary_text": "Single gross-receipts factor (6 decimals); resident reports full share, nonresident reports GA-apportioned+allocated; guaranteed payments not profit-%-based.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Nonresident withholding 4% + PTET election mechanics (IT-711 pp.11-13)",
                "excerpt_text": (
                    "Nonresident withholding (O.C.G.A. §48-7-129): 'The withholding tax rate is 4%' on each "
                    "nonresident partner's Georgia-source taxable income; no withholding if the partner's "
                    "annual GA-source share is less than $1,000; remitted via Form G-2-A (credited Sch 3 "
                    "L4). Alternative: composite return on Form IT-CR. PTET: 'A partnership may annually "
                    "make an irrevocable election to pay income tax at the entity level instead of passing "
                    "the income tax liability through to the partners' by checking the box on Form 700 by "
                    "the (extended) due date. When the election is made, a composite return is not filed "
                    "and the entity tax covers the nonresident partners. Estimates on Form 602-ES if net "
                    "income reasonably expected to exceed $25,000."
                ),
                "summary_text": "4% nonresident withholding (<$1,000 exempt, G-2-A); PTET is an annual irrevocable page-1 election that displaces nonresident withholding/composite.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Georgia depreciation decoupling + §179 (DOR Federal Tax Changes, verbatim)",
                "excerpt_text": (
                    "Georgia has not adopted the 30%, 50%, and 100% bonus depreciation rules, I.R.C. "
                    "Section 168(k). 'Federal depreciation should be added back to Georgia income by "
                    "entering it on the other addition line of the return. Depreciation must then be "
                    "computed for Georgia purposes on Georgia Form 4562 which should be attached to the "
                    "Georgia return. Georgia depreciation should be entered on the other subtraction line.' "
                    "Georgia §179: $2,500,000 deduction with $4,000,000 phaseout — GA CONFORMS to the OBBBA "
                    "§179 limit for TY2025 via HB 1199 (conformity 'as amended and in effect on January 1, "
                    "2026', retroactive to TY2025; supersedes the Aug-2025 Form 4562's pre-OBBBA $1.25M). "
                    "Georgia follows §163(j) as it existed before the 2017 TCJA; no "
                    "§199A QBI deduction."
                ),
                "summary_text": "GA decouples from §168(k) bonus (add federal depr on Sch 5 L7, subtract GA Form 4562 depr on Sch 6 L4); GA §179 = $2.5M/$4M (conforms to OBBBA via HB 1199); conformity Jan 1, 2026 (HB 1199, retroactive to TY2025).",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "GA_HB149_PTET_FAQ",
        "source_type": "state_guidance",
        "source_rank": "primary_official",
        "jurisdiction_code": "GA",
        "title": "Georgia DOR HB 149 Pass-Through Entity Tax FAQ",
        "citation": "GA DOR HB 149 PTE Tax FAQ (2025)",
        "issuer": "Georgia Department of Revenue",
        "official_url": "https://dor.georgia.gov/hb-149-pass-through-entity-tax-faq",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.0,
        "topics": ["ga_partnership_ptet"],
        "excerpts": [
            {
                "excerpt_label": "PTET owner treatment + attributes stay with the entity (FAQ)",
                "excerpt_text": (
                    "Electing owners exclude their share of entity-taxed income: on Form 500 Schedule 1, "
                    "share of income taxed at the entity level is a subtraction on Line 12 ('PTEDED'); "
                    "share of loss is an addition on Line 5 ('PTEADD'). 'The owners are not eligible to "
                    "claim a credit for taxes paid to Georgia with respect to income taxed at the entity "
                    "level by Georgia.' Tax attributes (credits and NOLs) do not pass through — they remain "
                    "with the electing entity; the entity MAY make a separate irrevocable election to pass "
                    "through credits generated that year EXCEPT the Qualified Education Expense, Qualified "
                    "Education Donation, and Qualified Rural Hospital Expense credits. For tax years "
                    "beginning on or after Jan 1, 2023, all partnerships are eligible regardless of "
                    "ownership. When the election is NOT made, Form 700 Schedules 1 and 3 should not be "
                    "completed."
                ),
                "summary_text": "Electing owners: PTEDED subtraction / PTEADD addition on Form 500 Sch 1, no owner credit; credits/NOLs stay with the entity; leave Form 700 Sch 1/3 blank if not electing.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "GA_REG_560_7_3_03",
        "source_type": "state_regulation",
        "source_rank": "controlling",
        "jurisdiction_code": "GA",
        "title": "Ga. Comp. R. & Regs. 560-7-3-.03 — Election to Pay Tax at the Pass-Through Entity Level",
        "citation": "Ga. Comp. R. & Regs. 560-7-3-.03",
        "issuer": "Georgia Department of Revenue",
        "official_url": "https://rules.sos.ga.gov/gac/560-7-3",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 8.8,
        "topics": ["ga_partnership_ptet"],
        "excerpts": [
            {
                "excerpt_label": "PTET base is ENTITY-LEVEL (Reg. .03(6), verbatim key points)",
                "excerpt_text": (
                    "The base is the partnership's federal taxable income including separately stated items "
                    "(charitable, §179, etc.), limited to what a C-corporation would be allowed; NO IRC "
                    "§743(b) deduction; NO self-employment, self-employed-health, Keogh or SEP deductions. "
                    "Then the O.C.G.A. §48-7-27 adjustments arrive at Georgia taxable income before "
                    "apportionment and allocation, which is then apportioned and allocated pursuant to "
                    "§48-7-31 to arrive at 'the income that is taxed at the entity level.' No §48-7-26 "
                    "exemptions, standard deductions, or natural-person deductions. The entity 'shall "
                    "multiply its income taxed at the entity level by 5.75 percent or, if subsequently "
                    "changed, the applicable statutory income tax rate' (the applicable 2025 rate is "
                    "5.19%). A SINGLE entity-level number for all owners — NOT a resident/nonresident split."
                ),
                "summary_text": "PTET base = federal taxable income (C-corp limits) → §48-7-27 GA adjustments → §48-7-31 apportionment → one entity-level number × the applicable rate (5.19% for 2025; reg text says 5.75%).",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "GA_OCGA_48_7",
        "source_type": "state_statute",
        "source_rank": "controlling",
        "jurisdiction_code": "GA",
        "title": "O.C.G.A. §48-7-20/21/27/31/129 — GA income tax rate, PTE election, adjustments, apportionment, NR withholding",
        "citation": "O.C.G.A. §48-7-20, -21, -27, -31, -129 (2025)",
        "issuer": "Georgia General Assembly",
        "official_url": "https://law.justia.com/codes/georgia/title-48/chapter-7/",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 8.8,
        "topics": ["ga_partnership_ptet"],
        "excerpts": [
            {
                "excerpt_label": "Statutory backing (per IT-711 / reg citations, W-flagged provenance)",
                "excerpt_text": (
                    "§48-7-20 imposes the individual/PTE income tax rate (flat, 5.19% for TY2025). §48-7-21 "
                    "authorizes the pass-through entity tax election (HB 149). §48-7-27 supplies the Georgia "
                    "adjustments to federal income (additions/subtractions — Form 700 Sch 5/6, incl. the "
                    "§168(k) bonus add-back and §179 difference). §48-7-31 provides apportionment/allocation "
                    "(single gross-receipts factor). §48-7-129 requires 4% withholding on nonresident "
                    "members' Georgia-source income. Statute characterizations taken from the IT-711 "
                    "booklet + Reg. 560-7-3-.03 citations (W-flagged; not fetched verbatim from ncleg-"
                    "equivalent — see brief §10 flag 6)."
                ),
                "summary_text": "§48-7-20 rate / §48-7-21 PTE election / §48-7-27 GA adjustments / §48-7-31 single-factor apportionment / §48-7-129 4% NR withholding.",
                "is_key_excerpt": True,
            },
        ],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("GA_2025_FORM_700", "GA700", "governs"),
    ("GA_2025_IT711", "GA700", "governs"),
    ("GA_HB149_PTET_FAQ", "GA700", "governs"),
    ("GA_REG_560_7_3_03", "GA700", "governs"),
    ("GA_OCGA_48_7", "GA700", "governs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM — GA Form 700
# ═══════════════════════════════════════════════════════════════════════════

GA700_FACTS: list[dict] = [
    {"fact_key": "ptet_election", "label": "PTET election — pay tax at the entity level? (Form 700 page 1)", "data_type": "boolean", "required": False, "sort_order": 1,
     "notes": "Dec A. Annual IRREVOCABLE. If False, Schedules 1 & 3 stay BLANK (pure pass-through)."},
    {"fact_key": "is_composite_return", "label": "Composite return filed (Form IT-CR)?", "data_type": "boolean", "required": False, "sort_order": 2,
     "notes": "Alternative to nonresident withholding; displaced when PTET is elected. RED-defer."},
    # Federal income (Schedule 8 ≈ federal Schedule K)
    {"fact_key": "fed_ordinary_income", "label": "Federal ordinary business income (Sch 8 L1)", "data_type": "decimal", "required": False, "sort_order": 10},
    {"fact_key": "fed_guaranteed_payments", "label": "Federal guaranteed payments to partners (Sch 8 L5)", "data_type": "decimal", "required": False, "sort_order": 11,
     "notes": "Not profit-%-based; not deductible in computing partnership net income."},
    {"fact_key": "fed_other_income", "label": "Federal other income — rental/portfolio/§1231/other (Sch 8 L2-4,6,7)", "data_type": "decimal", "required": False, "sort_order": 12},
    # GA additions (Schedule 5)
    {"fact_key": "ga_add_muni_interest", "label": "Non-GA state/municipal bond interest (Sch 5 L1)", "data_type": "decimal", "required": False, "sort_order": 20},
    {"fact_key": "federal_depreciation_addback", "label": "Federal depreciation add-back — GA Form 4562 (Sch 5 L7, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 21,
     "notes": "Dec B. GA decouples from §168(k); add back ALL federal depreciation (incl. bonus)."},
    {"fact_key": "ga_other_additions", "label": "Other GA additions — intangible/REIT/other (Sch 5, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 22},
    # GA subtractions (Schedule 6)
    {"fact_key": "ga_sub_us_obligations", "label": "Interest on U.S. obligations (Sch 6 L1)", "data_type": "decimal", "required": False, "sort_order": 30},
    {"fact_key": "ga_depreciation_subtraction", "label": "Georgia depreciation subtraction — GA Form 4562 (Sch 6 L4, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 31,
     "notes": "Dec B. GA-recomputed depreciation (no bonus, GA §179 limits)."},
    {"fact_key": "ga_other_subtractions", "label": "Other GA subtractions (Sch 6, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 32},
    # §179 (compute the GA-limit delta)
    {"fact_key": "federal_sec179_deduction", "label": "Federal IRC §179 expense (separately stated)", "data_type": "decimal", "required": False, "sort_order": 40,
     "notes": "Dec B. GA delta = federal − min(federal, GA $2,500,000 phased over $4,000,000); GA conforms → delta normally $0."},
    {"fact_key": "sec179_property_cost", "label": "Total §179 property placed in service (for the $4,000,000 GA phaseout)", "data_type": "decimal", "required": False, "sort_order": 41},
    # Apportionment (Schedule 7) + allocation (Schedule 2)
    {"fact_key": "ga_gross_receipts", "label": "Georgia gross receipts (Sch 7 L1 Col A)", "data_type": "decimal", "required": False, "sort_order": 50},
    {"fact_key": "total_gross_receipts", "label": "Everywhere gross receipts (Sch 7 L1 Col B)", "data_type": "decimal", "required": False, "sort_order": 51},
    {"fact_key": "income_allocated_everywhere", "label": "Income allocated everywhere (Sch 2 L2, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 52},
    {"fact_key": "income_allocated_to_ga", "label": "Income allocated to Georgia (Sch 2 L6, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 53},
    # GA taxable income adjustments (Schedule 1)
    {"fact_key": "ga_nol_deduction", "label": "Georgia NOL deduction (Sch 1 L4, 80% limit — direct-entry / RED-defer)", "data_type": "decimal", "required": False, "sort_order": 60},
    {"fact_key": "ga_passive_capital_loss", "label": "Passive/capital loss deduction (Sch 1 L5, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 61},
    # Credits / payments (Schedule 3)
    {"fact_key": "schedule_10_credits", "label": "Schedule 10 credits (Sch 3 L5, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 70},
    {"fact_key": "estimated_payments", "label": "Estimated + extension payments (Form 602-ES / IT-560C)", "data_type": "decimal", "required": False, "sort_order": 71},
    {"fact_key": "nonresident_withholding_paid", "label": "Nonresident withholding already paid (header T / Sch 3 L4)", "data_type": "decimal", "required": False, "sort_order": 72},
]

GA700_RULES: list[dict] = [
    {"rule_id": "R-GA700-FED-INC", "title": "Total federal income (Sch 8 L8)", "rule_type": "calculation",
     "formula": "L8 = fed_ordinary_income + fed_guaranteed_payments + fed_other_income",
     "inputs": ["fed_ordinary_income", "fed_guaranteed_payments", "fed_other_income"], "outputs": ["Sch8_L8"], "sort_order": 10,
     "description": "Schedule 8 ≈ federal Schedule K income (Form 1065). Guaranteed payments (L5) are included, not deducted."},
    {"rule_id": "R-GA700-ADD", "title": "Georgia additions (Sch 5 → Sch 8 L9)", "rule_type": "calculation",
     "formula": "Sch5_total = ga_add_muni_interest + federal_depreciation_addback + ga_other_additions ; Sch8_L9 = Sch5_total",
     "inputs": ["ga_add_muni_interest", "federal_depreciation_addback", "ga_other_additions"], "outputs": ["Sch5_L8", "Sch8_L9"], "sort_order": 11,
     "description": "Dec B/D. L7 'other additions' carries the federal depreciation add-back (GA decouples from §168(k))."},
    {"rule_id": "R-GA700-SUB", "title": "Georgia subtractions (Sch 6 → Sch 8 L11)", "rule_type": "calculation",
     "formula": "Sch6_total = ga_sub_us_obligations + ga_depreciation_subtraction + ga_other_subtractions ; Sch8_L11 = Sch6_total",
     "inputs": ["ga_sub_us_obligations", "ga_depreciation_subtraction", "ga_other_subtractions"], "outputs": ["Sch6_L5", "Sch8_L11"], "sort_order": 12,
     "description": "Dec B/D. L4 'other subtractions' carries the GA Form 4562 depreciation (no bonus, GA §179 limits)."},
    {"rule_id": "R-GA700-GA-INC", "title": "Total income for Georgia purposes (Sch 8 L12)", "rule_type": "calculation",
     "formula": "Sch8_L12 = Sch8_L8 + Sch8_L9 - Sch8_L11",
     "inputs": [], "outputs": ["Sch8_L12"], "sort_order": 13,
     "description": "Flows to Schedule 2 Line 1."},
    {"rule_id": "R-GA700-179", "title": "Georgia §179 limit difference (separately stated)", "rule_type": "calculation",
     "formula": ("ga_limit = max(0, 2500000 - max(0, sec179_property_cost - 4000000)) ; "
                 "ga_sec179 = min(federal_sec179_deduction, ga_limit) ; "
                 "sec179_delta = federal_sec179_deduction - ga_sec179  (separately stated to partners; GA K-1)"),
     "inputs": ["federal_sec179_deduction", "sec179_property_cost"], "outputs": ["ga_sec179", "sec179_delta"], "sort_order": 14,
     "description": "Dec B / W4. GA §179 $2,500,000 / $4,000,000 — Georgia CONFORMS to federal/OBBBA §179 for TY2025 (HB 1199). Because GA now equals federal, the separately-stated GA K-1 §179 delta is normally $0; the remaining GA depreciation difference is §168(k) bonus only."},
    {"rule_id": "R-GA700-APPORT", "title": "Single gross-receipts apportionment (Sch 7 → Sch 2)", "rule_type": "calculation",
     "formula": ("ga_ratio = round(ga_gross_receipts / total_gross_receipts, 6)  [six decimals, no rounding up] ; "
                 "Sch2_L3 = Sch2_L1 - income_allocated_everywhere ; Sch2_L5 = round(Sch2_L3 * ga_ratio) ; "
                 "Sch2_L7 = Sch2_L5 + income_allocated_to_ga  (= GA net income → Sch 1 L1)"),
     "inputs": ["ga_gross_receipts", "total_gross_receipts", "income_allocated_everywhere", "income_allocated_to_ga"],
     "outputs": ["ga_ratio", "Sch2_L7"], "sort_order": 15,
     "description": "W5. §48-7-31. SINGLE gross-receipts factor since 2008 (the GA600S 3-factor note is stale). Investment intangibles / pure-investment RE rentals are allocated, not apportioned."},
    {"rule_id": "R-GA700-TAXABLE", "title": "Georgia taxable income (Sch 1 L6)", "rule_type": "calculation",
     "formula": "Sch1_L1 = Sch2_L7 ; Sch1_L6 = max(0, Sch1_L1 - ga_nol_deduction - ga_passive_capital_loss)",
     "inputs": ["ga_nol_deduction", "ga_passive_capital_loss"], "outputs": ["Sch1_L6"], "sort_order": 16},
    {"rule_id": "R-GA700-PTET", "title": "PTET entity-level tax (Sch 1 L7) — 5.19%, gated on the election", "rule_type": "calculation",
     "formula": ("if ptet_election: Sch1_L7 = round(Sch1_L6 * 0.0519)  [the entity pays; §48-7-21] ; "
                 "else: Schedules 1 & 3 BLANK (pure pass-through; tax at the partner level)"),
     "inputs": ["ptet_election"], "outputs": ["Sch1_L7"], "sort_order": 17,
     "description": "Dec A / W2/W3. THE HEADLINE. Entity-level GA taxable income × 5.19% (Reg. says 5.75% 'or the applicable statutory rate'). Base is a single entity-level number, not a resident/nonresident split."},
    {"rule_id": "R-GA700-PTET-OWN", "title": "PTET owner treatment — PTEDED / PTEADD (Form 500 Sch 1)", "rule_type": "routing",
     "formula": ("if ptet_election: each electing owner's share of entity-taxed INCOME -> Form 500 Sch 1 L12 "
                 "subtraction 'PTEDED' ; share of LOSS -> Sch 1 L5 addition 'PTEADD' ; NO owner credit for the "
                 "entity-level GA tax. Credits & NOLs stay with the entity (separate pass-through election "
                 "possible except QEE/QED/QRHE credits)."),
     "inputs": ["ptet_election"], "outputs": [], "sort_order": 18,
     "description": "Dec A. The owner-side of the SALT-cap workaround. Displaces nonresident withholding/composite."},
    {"rule_id": "R-GA700-PARTNERS", "title": "Schedule 4 partner allocation — resident full / nonresident GA-source", "rule_type": "calculation",
     "formula": ("per partner: resident -> reports FULL distributive share (ordinary × profit% + guaranteed "
                 "payments) ; nonresident -> reports GA-source only = (ordinary share × ga_ratio) + (guaranteed "
                 "payments share × ga_ratio) + GA-allocated share. Guaranteed payments allocated per agreement, "
                 "not profit%."),
     "inputs": ["ga_ratio"], "outputs": ["partner_ga_source"], "sort_order": 19,
     "description": "Dec C / W6. IT-711 p.11-13 (the p.13 worked example is the authority: 25%/75%, $100 ord + $50 GP, 50% ratio → resident $35 / nonresident $58)."},
    {"rule_id": "R-GA700-NRW", "title": "Nonresident withholding (4%, <$1,000 exempt; displaced by PTET)", "rule_type": "calculation",
     "formula": ("if NOT ptet_election and NOT is_composite_return: per nonresident partner with GA-source share "
                 ">= 1000 -> withholding = round(ga_source_share * 0.04) (Form G-2-A) ; share < 1000 -> exempt. "
                 "PTET election OR composite return displaces per-partner withholding."),
     "inputs": ["ptet_election", "is_composite_return"], "outputs": ["nrw_withholding"], "sort_order": 20,
     "description": "Dec C. §48-7-129. 4% on nonresident GA-source income; <$1,000-share exemption."},
]

GA700_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-GA700-FED-INC", "GA_2025_FORM_700", "primary", "Schedule 8 ≈ federal Schedule K income map"),
    ("R-GA700-ADD", "GA_2025_IT711", "primary", "Sch 5 additions incl. the federal depreciation add-back"),
    ("R-GA700-ADD", "GA_OCGA_48_7", "secondary", "§48-7-27 Georgia adjustments"),
    ("R-GA700-SUB", "GA_2025_IT711", "primary", "Sch 6 subtractions incl. GA Form 4562 depreciation"),
    ("R-GA700-GA-INC", "GA_2025_FORM_700", "primary", "Sch 8 L12 = L8 + additions − subtractions"),
    ("R-GA700-179", "GA_2025_IT711", "primary", "GA §179 $2,500,000 / $4,000,000 (conforms via HB 1199)"),
    ("R-GA700-APPORT", "GA_2025_IT711", "primary", "single gross-receipts factor, 6 decimals"),
    ("R-GA700-APPORT", "GA_OCGA_48_7", "secondary", "§48-7-31 apportionment/allocation"),
    ("R-GA700-TAXABLE", "GA_2025_FORM_700", "primary", "Sch 1 L6 GA taxable income (face arithmetic)"),
    ("R-GA700-PTET", "GA_REG_560_7_3_03", "primary", "entity-level base × applicable rate (5.19% for 2025)"),
    ("R-GA700-PTET", "GA_2025_FORM_700", "secondary", "Sch 1 L7 'Income Tax (5.19% x Line 6)'"),
    ("R-GA700-PTET", "GA_OCGA_48_7", "secondary", "§48-7-21 PTE election / §48-7-20 rate"),
    ("R-GA700-PTET-OWN", "GA_HB149_PTET_FAQ", "primary", "PTEDED/PTEADD owner mechanics; no owner credit; attributes stay with entity"),
    ("R-GA700-PARTNERS", "GA_2025_IT711", "primary", "resident full / nonresident GA-apportioned; p.13 worked example"),
    ("R-GA700-NRW", "GA_2025_IT711", "primary", "4% nonresident withholding, <$1,000 exemption, G-2-A"),
    ("R-GA700-NRW", "GA_OCGA_48_7", "secondary", "§48-7-129 nonresident withholding"),
]

GA700_LINES: list[dict] = [
    {"line_number": "8-1", "description": "Sch 8 L1 Ordinary business income (federal)", "line_type": "input", "source_facts": ["fed_ordinary_income"], "sort_order": 1},
    {"line_number": "8-5", "description": "Sch 8 L5 Guaranteed payments to partners (federal)", "line_type": "input", "source_facts": ["fed_guaranteed_payments"], "sort_order": 2},
    {"line_number": "8-8", "description": "Sch 8 L8 Total federal income", "line_type": "subtotal", "source_rules": ["R-GA700-FED-INC"], "sort_order": 3},
    {"line_number": "8-9", "description": "Sch 8 L9 Additions (Schedule 5)", "line_type": "subtotal", "source_rules": ["R-GA700-ADD"], "sort_order": 4},
    {"line_number": "5-7", "description": "Sch 5 L7 Other additions (federal depreciation add-back)", "line_type": "input", "source_facts": ["federal_depreciation_addback"], "sort_order": 5},
    {"line_number": "8-11", "description": "Sch 8 L11 Subtractions (Schedule 6)", "line_type": "subtotal", "source_rules": ["R-GA700-SUB"], "sort_order": 6},
    {"line_number": "6-4", "description": "Sch 6 L4 Other subtractions (GA Form 4562 depreciation)", "line_type": "input", "source_facts": ["ga_depreciation_subtraction"], "sort_order": 7},
    {"line_number": "8-12", "description": "Sch 8 L12 Total income for Georgia purposes", "line_type": "subtotal", "source_rules": ["R-GA700-GA-INC"], "sort_order": 8},
    {"line_number": "7-1", "description": "Sch 7 L1 Gross receipts — Col A (GA) / Col B (everywhere)", "line_type": "input", "source_facts": ["ga_gross_receipts", "total_gross_receipts"], "sort_order": 9},
    {"line_number": "7-2", "description": "Sch 7 L2 Georgia ratio (A ÷ B, six decimals)", "line_type": "calculated", "source_rules": ["R-GA700-APPORT"], "sort_order": 10},
    {"line_number": "2-1", "description": "Sch 2 L1 Total income for GA purposes", "line_type": "subtotal", "source_rules": ["R-GA700-GA-INC"], "sort_order": 11},
    {"line_number": "2-5", "description": "Sch 2 L5 Net business income apportioned to Georgia", "line_type": "calculated", "source_rules": ["R-GA700-APPORT"], "sort_order": 12},
    {"line_number": "2-7", "description": "Sch 2 L7 Georgia net income", "line_type": "subtotal", "source_rules": ["R-GA700-APPORT"], "sort_order": 13},
    {"line_number": "1-1", "description": "Sch 1 L1 Georgia net income (from Sch 2 L7)", "line_type": "subtotal", "source_rules": ["R-GA700-TAXABLE"], "sort_order": 14},
    {"line_number": "1-4", "description": "Sch 1 L4 Georgia NOL deduction (80% limit)", "line_type": "input", "source_facts": ["ga_nol_deduction"], "sort_order": 15},
    {"line_number": "1-6", "description": "Sch 1 L6 Total Georgia taxable income", "line_type": "subtotal", "source_rules": ["R-GA700-TAXABLE"], "sort_order": 16},
    {"line_number": "1-7", "description": "Sch 1 L7 Income Tax (5.19% × L6) — PTET only", "line_type": "calculated", "calculation": "R-GA700-PTET", "source_rules": ["R-GA700-PTET"], "sort_order": 17},
    {"line_number": "3-4", "description": "Sch 3 L4 Withholding credits (G2-A/G2-LP/G2-RP)", "line_type": "input", "source_facts": ["nonresident_withholding_paid"], "sort_order": 18},
    {"line_number": "4", "description": "Sch 4 Income to partners — profit-loss % / GA source income", "line_type": "calculated", "source_rules": ["R-GA700-PARTNERS"], "sort_order": 19},
    {"line_number": "T", "description": "Page 1 T — Nonresident withholding paid by the partnership", "line_type": "calculated", "source_rules": ["R-GA700-NRW"], "sort_order": 20},
]

GA700_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_GA700_PTET", "title": "PTET is an entity-level 5.19% election — owners use PTEDED/PTEADD", "severity": "info",
     "condition": "ptet_election is True (or the preparer is weighing the election)", "message": "The pass-through entity tax is an ANNUAL IRREVOCABLE election to pay Georgia tax at the entity level (5.19% on GA taxable income). Electing owners EXCLUDE that income — PTEDED subtraction (Form 500 Sch 1 L12) / PTEADD addition (L5); NO owner credit for the entity-level GA tax. Credits & NOLs stay with the entity. If NOT electing, leave Form 700 Schedules 1 & 3 BLANK.",
     "notes": "Dec A. The headline SALT-cap-workaround feature."},
    {"diagnostic_id": "D_GA700_DEPR", "title": "Georgia decouples from §168(k) bonus — add back / recompute depreciation", "severity": "info",
     "condition": "federal depreciation or §179 present", "message": "GA does NOT conform to IRC §168(k)/(n) bonus. Add back ALL federal bonus/accelerated depreciation on Sch 5 L7, recompute Georgia depreciation on the Georgia Form 4562, and enter it on Sch 6 L4. GA DOES conform to the OBBBA §179 limit ($2,500,000 / $4,000,000) for TY2025 (HB 1199), so there is normally no separate GA §179 add-back — the difference is bonus depreciation only.",
     "notes": "Dec B / W4. Ken's specialty. Conformity Jan 1, 2026 (HB 1199, retroactive to TY2025)."},
    {"diagnostic_id": "D_GA700_179LIMIT", "title": "§179 property over the $4,000,000 phaseout", "severity": "warning",
     "condition": "sec179_property_cost > 4000000", "message": "Georgia conforms to the OBBBA §179 limit for TY2025 (HB 1199): the $2,500,000 limit phases down dollar-for-dollar once §179 property placed in service exceeds $4,000,000, mirroring federal. Because GA equals federal, the separately-stated GA K-1 §179 delta is normally $0.",
     "notes": "W4."},
    {"diagnostic_id": "D_GA700_APPORT", "title": "Apportionment is a SINGLE gross-receipts factor (6 decimals)", "severity": "info",
     "condition": "apportionment computed", "message": "Georgia apportions by a single gross-receipts factor (GA receipts ÷ everywhere, to six decimals, do not round). The GA600S loader's 'property/payroll/sales' 3-factor note is STALE. Investment intangibles and pure-investment real-estate rentals are allocated, not apportioned.",
     "notes": "W5."},
    {"diagnostic_id": "D_GA700_NRW", "title": "4% nonresident withholding (unless PTET/composite)", "severity": "info",
     "condition": "nonresident partner present and NOT ptet_election and NOT is_composite_return", "message": "Georgia requires 4% withholding on each nonresident partner's Georgia-source income (Form G-2-A), UNLESS the partner's GA-source share is under $1,000. A PTET election OR a composite return (Form IT-CR) displaces per-partner withholding.",
     "notes": "Dec C. §48-7-129."},
    {"diagnostic_id": "D_GA700_NETWORTH", "title": "Partnerships are NOT subject to GA net worth tax", "severity": "info",
     "condition": "always (contrast Form 600S)", "message": "Unlike an S-corporation (Form 600S Schedule 3), a partnership filing Form 700 is NOT subject to the Georgia net worth tax. Do not compute a net worth tax on Form 700.",
     "notes": "Contrast GA600S."},
    {"diagnostic_id": "D_GA700_NOL", "title": "Georgia NOL (Schedule 9, 80% limit) — prepare manually", "severity": "info",
     "condition": "GA NOL claimed", "message": "The Georgia net operating loss deduction (Schedule 9, 80% limitation, no carryback for normal losses) is not computed in v1 — prepare Schedule 9 manually and enter the result on Sch 1 L4.",
     "notes": "Dec D RED-defer."},
    {"diagnostic_id": "D_GA700_COMPOSITE", "title": "Composite return (Form IT-CR) — prepare manually", "severity": "info",
     "condition": "composite return elected in lieu of withholding", "message": "The nonresident composite return (Form IT-CR) alternative to per-partner withholding is not computed in v1 — prepare Form IT-CR manually. (Displaced entirely if the PTET election is made.)",
     "notes": "Dec D RED-defer."},
    {"diagnostic_id": "D_GA700_UET", "title": "Estimated-tax underpayment penalty (Form 600UET) — prepare manually", "severity": "info",
     "condition": "electing entity underpaid estimates (net income > $25,000)", "message": "The Form 600UET estimated-tax underpayment penalty is not computed in v1. Note: for the 100%-of-prior-year safe harbor, if the entity did not elect last year the prior-year hypothetical tax is computed at 5.75% (the reg's legacy rate). Prepare Form 600UET manually.",
     "notes": "Dec D RED-defer. W2 (the 5.75% reg quirk)."},
    {"diagnostic_id": "D_GA700_CONFORM", "title": "GA IRC conformity = Jan 1, 2026 (HB 1199) — §168(k) bonus add-back", "severity": "warning",
     "condition": "depreciation / §179 / conformity-sensitive item present", "message": "For TY2025 Georgia's IRC conformity date is January 1, 2026 (HB 1199, retroactive to tax years beginning on/after Jan 1, 2025) — GA conforms to the OBBBA §179 limit ($2,500,000 / $4,000,000) but still decouples from §168(k)/(n) bonus (add-back required). Verify the §168(k) bonus add-back on Schedule 5.",
     "notes": "W1. RESOLVED 2026-07-06 (HB 1199 retroactive)."},
]

GA700_SCENARIOS: list[dict] = [
    {"scenario_name": "GA700-T1 — non-electing partnership (pass-through, Sch 1/3 blank)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"ptet_election": False, "fed_ordinary_income": 200000, "fed_guaranteed_payments": 0, "fed_other_income": 0,
                "ga_gross_receipts": 500000, "total_gross_receipts": 1000000},
     "expected_outputs": {"Sch8_L8": 200000, "Sch1_L7": 0},
     "notes": "No PTET election → Schedules 1 & 3 blank; entity pays no tax (pure pass-through). Sch 8 L8 = 200,000."},
    {"scenario_name": "GA700-T2 — PTET elected, entity tax at 5.19%", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"ptet_election": True, "fed_ordinary_income": 100000, "ga_gross_receipts": 1000000, "total_gross_receipts": 1000000,
                "income_allocated_everywhere": 0, "income_allocated_to_ga": 0},
     "expected_outputs": {"ga_ratio": 1.0, "Sch2_L7": 100000, "Sch1_L6": 100000, "Sch1_L7": 5190},
     "notes": "100% GA (ratio 1.0); GA net income 100,000; L7 = round(100,000 × 0.0519) = 5,190."},
    {"scenario_name": "GA700-T3 — depreciation add-back / subtraction (§168(k) decoupling)", "scenario_type": "edge", "sort_order": 3,
     "inputs": {"ptet_election": True, "fed_ordinary_income": 100000, "federal_depreciation_addback": 85000, "ga_depreciation_subtraction": 20000,
                "ga_gross_receipts": 1000000, "total_gross_receipts": 1000000},
     "expected_outputs": {"Sch8_L9": 85000, "Sch8_L11": 20000, "Sch8_L12": 165000},
     "notes": "Add back federal depr 85,000 (Sch 5 L7 → Sch 8 L9); subtract GA depr 20,000 (Sch 6 L4 → Sch 8 L11); L12 = 100,000 + 85,000 − 20,000 = 165,000. Net GA add = 65,000."},
    {"scenario_name": "GA700-T4 — §179 conforms to federal (no delta)", "scenario_type": "edge", "sort_order": 4,
     "inputs": {"federal_sec179_deduction": 1200000, "sec179_property_cost": 2000000},
     "expected_outputs": {"ga_sec179": 1200000, "sec179_delta": 0},
     "notes": "GA conforms to OBBBA §179 (HB 1199): cost 2,000,000 < 4,000,000 phaseout → GA limit 2,500,000; GA §179 = min(1,200,000, 2,500,000) = 1,200,000; delta = 0 (GA equals federal → nothing separately stated)."},
    {"scenario_name": "GA700-T5 — single-factor apportionment (six decimals)", "scenario_type": "edge", "sort_order": 5,
     "inputs": {"ptet_election": True, "fed_ordinary_income": 200000, "ga_gross_receipts": 400000, "total_gross_receipts": 1000000,
                "income_allocated_everywhere": 0, "income_allocated_to_ga": 0},
     "expected_outputs": {"ga_ratio": 0.4, "Sch2_L5": 80000, "Sch2_L7": 80000},
     "notes": "GA ratio = 400,000 / 1,000,000 = 0.400000; business income 200,000 × 0.4 = 80,000 apportioned to GA."},
    {"scenario_name": "GA700-T6 — Schedule 4 partner allocation (resident full / nonresident GA-source)", "scenario_type": "normal", "sort_order": 6,
     "inputs": {"ptet_election": False, "fed_ordinary_income": 100000, "ga_gross_receipts": 500000, "total_gross_receipts": 1000000,
                "partners": [{"name": "A (GA resident)", "profit_pct": 60, "resident": True},
                             {"name": "B (nonresident)", "profit_pct": 40, "resident": False}]},
     "expected_outputs": {"ga_ratio": 0.5, "partner_A_ga_source": 60000, "partner_B_ga_source": 20000},
     "notes": "Clean synthetic (IT-711 p.13 is the authority). Resident A reports full 60% × 100,000 = 60,000; nonresident B reports GA-source only = 40% × 100,000 × 0.5 ratio = 20,000."},
    {"scenario_name": "GA700-T7 — 4% nonresident withholding + <$1,000 exemption + PTET displacement", "scenario_type": "edge", "sort_order": 7,
     "inputs": {"ptet_election": False, "is_composite_return": False,
                "partners": [{"name": "B", "resident": False, "ga_source": 20000},
                             {"name": "C", "resident": False, "ga_source": 500}]},
     "expected_outputs": {"partner_B_nrw": 800, "partner_C_nrw": 0},
     "notes": "B: 20,000 × 4% = 800 withholding (G-2-A). C: GA-source 500 < 1,000 → exempt. If ptet_election were True, both would be 0 (PTET displaces withholding)."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORMS registry + flow assertions
# ═══════════════════════════════════════════════════════════════════════════

FORMS: list[dict] = [
    {
        "identity": {"form_number": "GA700", "form_title": "GA Form 700 — Georgia Partnership Tax Return + PTET (TY2025)",
                     "notes": "1st partnership-entity state spec. Federal-income start (Sch 8) → GA add/subtract (Sch 5/6) → single gross-receipts apportionment (Sch 7) → GA net income (Sch 2) → flat 5.19% tax IF the PTET election is made (Sch 1). PTET (HB 149) is the headline: entity-level SALT-cap workaround with PTEDED/PTEADD owner mechanics. GA decouples from §168(k)/OBBBA; GA §179 $1.05M/$2.62M; 4% nonresident withholding. Partnerships exempt from GA net worth tax."},
        "facts": GA700_FACTS, "rules": GA700_RULES, "rule_links": GA700_RULE_LINKS,
        "lines": GA700_LINES, "diagnostics": GA700_DIAGNOSTICS, "scenarios": GA700_SCENARIOS,
    },
]

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-GA700-PTET", "title": "PTET entity tax = GA taxable income × 5.19%, gated on the election", "assertion_type": "reconciliation",
     "entity_types": ["1065"], "status": "draft", "sort_order": 1,
     "description": "When ptet_election, Form 700 Sch 1 L7 = round(GA taxable income (Sch 1 L6) × 0.0519); when not elected, Schedules 1 & 3 are blank (pure pass-through). The base is a single entity-level number.",
     "definition": {"rule": "R-GA700-PTET", "check": "L7 = round(Sch1_L6 * 0.0519) if ptet_election else blank"}},
    {"assertion_id": "FA-GA700-PTEDED", "title": "Electing owners exclude entity-taxed income via PTEDED/PTEADD (Form 500)", "assertion_type": "flow_assertion",
     "entity_types": ["1065"], "status": "draft", "sort_order": 2,
     "description": "When PTET is elected, each owner's share of entity-taxed income is a PTEDED subtraction (Form 500 Sch 1 L12) / PTEADD addition (L5), with NO owner credit for the entity-level GA tax. Credits & NOLs stay with the entity.",
     "definition": {"rule": "R-GA700-PTET-OWN", "check": "owner PTEDED/PTEADD on Form 500 Sch 1; no owner credit"}},
    {"assertion_id": "FA-GA700-APPORT", "title": "GA apportionment is a single gross-receipts factor (6 decimals)", "assertion_type": "reconciliation",
     "entity_types": ["1065"], "status": "draft", "sort_order": 3,
     "description": "Sch 7 GA ratio = GA gross receipts ÷ everywhere gross receipts, to six decimals; Sch 2 L5 = business income × ratio. Single factor since 2008 (not 3-factor).",
     "definition": {"rule": "R-GA700-APPORT", "check": "ga_ratio = round(ga_gross_receipts / total_gross_receipts, 6)"}},
    {"assertion_id": "FA-GA700-DEPR", "title": "GA decouples from §168(k): federal depr add-back (Sch 5) / GA depr subtraction (Sch 6)", "assertion_type": "flow_assertion",
     "entity_types": ["1065"], "status": "draft", "sort_order": 4,
     "description": "Federal depreciation (incl. §168(k) bonus) is added back on Sch 5 L7 and Georgia-recomputed depreciation (GA Form 4562, GA §179 $1.05M/$2.62M) is subtracted on Sch 6 L4. GA did not adopt OBBBA.",
     "definition": {"rule": "R-GA700-ADD", "check": "Sch5_L7 = federal_depreciation_addback ; Sch6_L4 = ga_depreciation_subtraction"}},
    {"assertion_id": "FA-GA700-NRW", "title": "4% nonresident withholding, <$1,000 exempt, displaced by PTET", "assertion_type": "reconciliation",
     "entity_types": ["1065"], "status": "draft", "sort_order": 5,
     "description": "Each nonresident partner with a GA-source share ≥ $1,000 is withheld at 4% (Form G-2-A) unless the PTET election or a composite return is made.",
     "definition": {"rule": "R-GA700-NRW", "check": "nrw = round(ga_source * 0.04) if ga_source >= 1000 and not ptet_election and not composite else 0"}},
]


# ═══════════════════════════════════════════════════════════════════════════
# Command
# ═══════════════════════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = (
        "Load the GA Form 700 spec (Georgia Partnership Income Tax + PTET, TY2025). "
        "Refuses to seed until Ken sets READY_TO_SEED=True after the in-session review walk (W1-W6)."
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad GA Form 700 spec (Georgia Partnership Income Tax + PTET)\n"))
        self._load_topics()
        sources = self._load_sources()
        for spec in FORMS:
            form = self._upsert_form(spec["identity"])
            self._upsert_facts(form, spec["facts"])
            rules = self._upsert_rules(form, spec["rules"])
            self._upsert_authority_links(rules, sources, spec["rule_links"])
            self._upsert_lines(form, spec["lines"])
            self._upsert_diagnostics(form, spec["diagnostics"])
            self._upsert_tests(form, spec["scenarios"])
        self._upsert_form_links(sources)
        self._load_flow_assertions()
        self._report_totals()

    def _guard_against_hollow_seed(self):
        empty = []
        for spec in FORMS:
            fn = spec["identity"]["form_number"]
            for key in ("facts", "rules", "lines", "diagnostics", "scenarios", "rule_links"):
                if not spec[key]:
                    empty.append(f"{fn}.{key}")
        if not FLOW_ASSERTIONS:
            empty.append("FLOW_ASSERTIONS")
        if not READY_TO_SEED or empty:
            still_empty = "\n  ".join(f"- {n}" for n in empty) or "(all populated)"
            raise CommandError(
                "\nREFUSING TO SEED GA FORM 700: not cleared to seed.\n\n"
                "Content is authored, but seeding is gated until Ken reviews the packet\n"
                "(W1 the Jan 1 2024 conformity date; W2 the 5.19% flat/PTET rate + the 5.75%\n"
                "reg quirk; W3 the entity-level PTET base; W4 the §179 $1.05M/$2.62M figures;\n"
                "W5 the single gross-receipts apportionment; W6 the Schedule 4 partner model)\n"
                "and flips the sentinel.\n\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True to proceed)\n\n"
                f"Currently empty / placeholder:\n  {still_empty}\n\n"
                "To proceed: review the module-level data lists (and ga700_source_brief.md),\n"
                "then set READY_TO_SEED = True. Idempotent via update_or_create."
            )

    def _load_topics(self):
        ct = 0
        for code, name in AUTHORITY_TOPICS:
            _, created = AuthorityTopic.objects.update_or_create(topic_code=code, defaults={"topic_name": name})
            if created:
                ct += 1
        self.stdout.write(f"Topics: {ct} new ({len(AUTHORITY_TOPICS)} in batch)")

    def _load_sources(self) -> dict:
        sources: dict = {}
        for src_data in AUTHORITY_SOURCES:
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
                    AuthoritySourceTopic.objects.get_or_create(authority_source=source, authority_topic=topic)
        for code in EXISTING_SOURCES_TO_REFERENCE:
            src = AuthoritySource.objects.filter(source_code=code).first()
            if src:
                sources[code] = src
            else:
                self.stdout.write(self.style.WARNING(f"  existing source {code} NOT FOUND — links to it will be skipped"))
        self.stdout.write(f"Sources ready: {len(sources)}")
        return sources

    def _upsert_form(self, identity: dict) -> TaxForm:
        form, created = TaxForm.objects.update_or_create(
            form_number=identity["form_number"], jurisdiction=FORM_JURISDICTION,
            tax_year=FORM_TAX_YEAR, version=FORM_VERSION,
            defaults={"form_title": identity["form_title"], "entity_types": FORM_ENTITY_TYPES,
                      "status": FORM_STATUS, "notes": identity["notes"]},
        )
        self.stdout.write(f"{'Created' if created else 'Updated'} {identity['form_number']}")
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

    def _upsert_authority_links(self, rules, sources, rule_links):
        ct = 0
        for rule_id, source_code, level, note in rule_links:
            rule, source = rules.get(rule_id), sources.get(source_code)
            if rule and source:
                RuleAuthorityLink.objects.get_or_create(
                    form_rule=rule, authority_source=source,
                    defaults={"support_level": level, "relevance_note": note},
                )
                ct += 1
        self.stdout.write(f"  {ct} authority links")

    def _upsert_lines(self, form, lines):
        for ln in lines:
            ln = dict(ln)
            FormLine.objects.update_or_create(tax_form=form, line_number=ln.pop("line_number"), defaults=ln)
        self.stdout.write(f"  {len(lines)} lines")

    def _upsert_diagnostics(self, form, diagnostics):
        for d in diagnostics:
            d = dict(d)
            FormDiagnostic.objects.update_or_create(tax_form=form, diagnostic_id=d.pop("diagnostic_id"), defaults=d)
        self.stdout.write(f"  {len(diagnostics)} diagnostics")

    def _upsert_tests(self, form, scenarios):
        for t in scenarios:
            t = dict(t)
            TestScenario.objects.update_or_create(tax_form=form, scenario_name=t.pop("scenario_name"), defaults=t)
        self.stdout.write(f"  {len(scenarios)} test scenarios")

    def _upsert_form_links(self, sources):
        for source_code, form_code, link_type in AUTHORITY_FORM_LINKS:
            source = sources.get(source_code) or AuthoritySource.objects.filter(source_code=source_code).first()
            if source:
                AuthorityFormLink.objects.get_or_create(
                    authority_source=source, form_code=form_code, link_type=link_type,
                    defaults={"note": f"{source_code} -> {form_code}"},
                )

    def _load_flow_assertions(self):
        for a in FLOW_ASSERTIONS:
            a = dict(a)
            FlowAssertion.objects.update_or_create(assertion_id=a.pop("assertion_id"), defaults=a)
        self.stdout.write(f"  {len(FLOW_ASSERTIONS)} flow assertions")

    def _report_totals(self):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("GA Form 700 loaded.")
        self.stdout.write(
            f"  GA700: facts {len(GA700_FACTS)} / rules {len(GA700_RULES)} / lines {len(GA700_LINES)} / "
            f"diag {len(GA700_DIAGNOSTICS)} / tests {len(GA700_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}"
        )
        self.stdout.write("=" * 60)
