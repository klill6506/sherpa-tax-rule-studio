"""Load the 1065 core SPINE — Form 1065 page 1 (ordinary business income) + Schedule K
(partners' distributive share). The first unit of the July 1065-core authoring campaign.

Authoring input: the pre-staged, source-verified transcription map
  D:\\dev\\sherpa-tax-rule-studio\\1065_core_source_brief.md  (§4.1 + §4.2)
which was fetched + verified VERBATIM 2026-07-04 off the FINAL 2025 IRS PDFs (f1065.pdf
Cat. 11390Z "Created 11/25/25"; i1065.pdf Cat. 11392V dated Jan 14 2026). This loader is a
FRESH authoring pass per **D-1** (author fresh from IRS primary sources → Ken walk →
reconcile against tts compute → seed). It is NOT a silent unblock. The brief is a
transcription AID, not a spec; the RULES here are grounded in the primary statute quoted
verbatim below.

WHAT THIS GOVERNS (the two forms this loader seeds):
  1. **1065_PAGE1** — Form 1065 page 1 income (1a-8) & deductions (9-22); the key output is
     **line 23 ordinary business income = line 8 − line 22 → Schedule K line 1** (the entity→K
     handoff). ⚠ 2025 face correction (brief §4.1): ordinary business income is **line 23**
     (not 22); total deductions is **line 22**; the tax/payment block is 24-32; 32b/32c/32d
     direct-deposit are NEW for 2025 (Exec. Order 14247).
  2. **SCH_K_1065** — Schedule K (Form 1065 page 5), "Total amount" column, lines 1-21 +
     Analysis of Net Income (Loss) per Return. The distributive-share SPINE. The per-partner
     split (K → K-1) and the §704 allocation MATH are the NEXT leg (Schedule K-1 + allocation
     engine) — this spine encodes the entity totals, the character-conduit structure, and the
     K→K-1 correspondence as a routing rule (math deferred, per Ken's scope call).

KEN SCOPE DECISIONS — LOCKED (AskUserQuestion, 2026-07-04, this session):
  A. **K-2/K-3 (international) → RED-DEFER.** Schedule K line 16 / K-1 box 16 is a checkbox
     pointing to Schedules K-2/K-3 (all intl detail moved there post-2021). Season one models
     box 16 as a K-3-attached checkbox only + a RED diagnostic (D_SCHK_K3) flagging that
     K-2/K-3 line detail is out of scope. (Brief §4.2 / §3.)
  B. **Schedule M-3 → RED-DEFER.** M-3 (≥$10M assets / ≥$35M receipts / 50% reportable-entity-
     partner) is out of season-one scope; it belongs to the L/M-1/M-2 leg. Encoded there as a
     threshold gating fact + RED diagnostic — flagged in this spine's notes, not built here.
  C. **§704(b)/(c) → ENCODE STRUCTURE, DEFER MATH.** Capture the allocation structure (§704(a)
     agreement → §704(b) substantial-economic-effect fallback → §704(c) built-in-gain; §706(d)
     varying-interest) as a cited routing rule + gating flags (items M/N). The special-allocation
     MATH is deferred to the tts `k1_allocator` (reconcile what it handles vs. RED-defer per D-1;
     D_SCHK_704C surfaces the item-M/N case). Full SEE / traditional-curative-remedial math is
     NOT authored this season.

AUTHORITY QUOTING (CLAUDE.md Authoritative-Source Rule): the operative IRC subsections
(§702(a)(8)/(b), §703(a)/(b), §704(a)/(b), §707(c)) were read DIRECTLY from the U.S. Code and
quoted VERBATIM 2026-07-04 (Cornell LII mirror of the official text — eCFR/govinfo block
automated fetches; the §702/§707 excerpts are re-used from the vetted 1065_SE load). The
2025 FORM/INSTRUCTION line maps (filing authority, requires_human_review=True) are the brief
§4.1/§4.2 verbatim transcription of the FINAL 2025 f1065/i1065 — RE-VERIFY at the Ken walk
against the live PDFs before seeding.

RECONCILE TARGETS (D-1, brief §2 — do at the walk, BEFORE flipping READY_TO_SEED):
  - `server/apps/returns/compute.py` — the entity-side page-1 ordinary income / Schedule K
    aggregation (survey the page-1 line 23 → Sch K line 1 path).
  - `server/apps/returns/compute_schedule_k1.py` — the recipient-side K-1 aggregation consumers
    (line-by-line box map; reconcile the K→K-1 correspondence rule R-SCHK-KMAP against these).
  - `server/apps/returns/k1_allocator.py` — the allocation engine (the §704 structure reconcile
    is the NEXT leg's job; note here what it already models vs. RED-defer).
  Log every computed-formula mismatch as a Ken adjudication (D-1). This spine is entity-total
  only, so the reconcile surface is small (page-1 arithmetic + Analysis); the allocation
  reconcile lands with the K-1 leg.
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


# FRESH-AUTHORED 2026-07-04 (Schedule K spine leg). Per D-1 + brief §5: authored with
# READY_TO_SEED=False; Ken walked the scope decisions (A/B/C above) + the reconcile
# (1065_core_reconcile_log — net-farm #7 CONFIRMED+FIXED in tts f61cfec; page-1 numbering
# + box-9c left as tts-side build items, not RS-spec blockers). Ken: "flip seed export"
# 2026-07-04 → FLIPPED.
READY_TO_SEED = True


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("partnership_1065_core",
     "Partnership return core (Form 1065) — page-1 ordinary business income (§703), the "
     "Schedule K distributive-share spine (§702 separately-stated items; §702(b) character "
     "conduit), and the §704/§706(d) allocation structure that drives the K → K-1 split."),
]

AUTHORITY_SOURCES: list[dict] = [
    # ── 1. IRC §702 — distributive share + character conduit (why Schedule K exists) ──
    {
        "source_code": "IRC_702",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1065",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §702 — Income and Credits of Partner (separately stated distributive share; "
                 "character conduit)",
        "citation": "26 U.S.C. §702(a), (a)(8), (b)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/702",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "The statute behind the Schedule K line structure: §702(a) requires each partner to "
                 "take into account separately his distributive share of enumerated items (→ the "
                 "separately-stated Schedule K lines); §702(a)(8) is the residual trade-or-business "
                 "income (→ Sch K line 1); §702(b) is the character conduit (each item keeps its "
                 "partnership-level character). §702(a)(8)/(b) quoted verbatim from the U.S. Code "
                 "2026-07-01 (re-used); the §702(a) opening added verbatim 2026-07-04.",
        "topics": ["partnership_1065_core"],
        "excerpts": [
            {
                "excerpt_label": "§702(a) — separately stated distributive share (opening)",
                "location_reference": "26 U.S.C. §702(a) (opening flush)",
                "excerpt_text": (
                    "In determining his income tax, each partner shall take into account separately his "
                    "distributive share of the partnership's— (1) gains and losses from sales or exchanges "
                    "of capital assets held for not more than 1 year, (2) gains and losses from sales or "
                    "exchanges of capital assets held for more than 1 year, (3) gains and losses from sales "
                    "or exchanges of property described in section 1231, (4) charitable contributions, "
                    "(5) dividends with respect to which section 1(h)(11) or part VIII of subchapter B "
                    "applies, (6) taxes, described in section 901, paid or accrued to foreign countries and "
                    "to possessions of the United States, (7) other items of income, gain, loss, deduction, "
                    "or credit, to the extent provided by regulations prescribed by the Secretary, and "
                    "(8) taxable income or loss, exclusive of items requiring separate computation under "
                    "other paragraphs of this subsection."
                ),
                "summary_text": "§702(a) requires each partner to separately state his distributive share of "
                                "the enumerated items (capital gains ST/LT, §1231, charitable, dividends, "
                                "foreign taxes, other regulatory items) plus (8) the residual trade/business "
                                "income — this IS the Schedule K line structure.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§702(a)(8) — taxable income/loss distributive share (→ Sch K line 1)",
                "location_reference": "26 U.S.C. §702(a)(8)",
                "excerpt_text": (
                    "taxable income or loss, exclusive of items requiring separate computation under other "
                    "paragraphs of this subsection."
                ),
                "summary_text": "§702(a)(8) is the residual ordinary trade-or-business income/loss — page-1 "
                                "line 23 → Schedule K line 1.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§702(b) — character determined at the partnership level",
                "location_reference": "26 U.S.C. §702(b)",
                "excerpt_text": (
                    "The character of any item of income, gain, loss, deduction, or credit included in a "
                    "partner's distributive share under paragraphs (1) through (7) of subsection (a) shall "
                    "be determined as if such item were realized directly from the source from which "
                    "realized by the partnership, or incurred in the same manner as incurred by the "
                    "partnership."
                ),
                "summary_text": "Each separately-stated item keeps its partnership-level character in the "
                                "partner's hands — the reason Schedule K lines 2-21 are broken out rather "
                                "than folded into ordinary income.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ── 2. IRC §703 — partnership taxable income (the page-1 computation) ──
    {
        "source_code": "IRC_703",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1065",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §703 — Partnership Computations (taxable income computed as an individual; "
                 "separately-stated carve-outs; disallowed deductions)",
        "citation": "26 U.S.C. §703(a), (a)(1), (a)(2), (b)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/703",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "The page-1 computation basis: partnership taxable income is figured as for an individual "
                 "EXCEPT (1) §702(a) items are separately stated (→ pulled off page 1 onto Schedule K) and "
                 "(2) six deductions are disallowed at the entity level (personal exemptions, foreign "
                 "taxes, charitable, NOL, individual itemized, oil/gas depletion). Text READ DIRECTLY and "
                 "quoted VERBATIM 2026-07-04 from the U.S. Code.",
        "topics": ["partnership_1065_core"],
        "excerpts": [
            {
                "excerpt_label": "§703(a) — taxable income as an individual, with two exceptions",
                "location_reference": "26 U.S.C. §703(a), (a)(1), (a)(2)",
                "excerpt_text": (
                    "The taxable income of a partnership shall be computed in the same manner as in the case "
                    "of an individual except that— (1) the items described in section 702(a) shall be "
                    "separately stated, and (2) the following deductions shall not be allowed to the "
                    "partnership: (A) the deductions for personal exemptions provided in section 151, "
                    "(B) the deduction for taxes provided in section 164(a) with respect to taxes, described "
                    "in section 901, paid or accrued to foreign countries and to possessions of the United "
                    "States, (C) the deduction for charitable contributions provided in section 170, "
                    "(D) the net operating loss deduction provided in section 172, (E) the additional "
                    "itemized deductions for individuals provided in part VII of subchapter B (sec. 211 and "
                    "following), and (F) the deduction for depletion under section 611 with respect to oil "
                    "and gas wells."
                ),
                "summary_text": "Page-1 ordinary business income is partnership taxable income computed as an "
                                "individual, minus the §702(a) separately-stated items (which go to Sch K) "
                                "and minus the six disallowed entity-level deductions.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§703(b) — elections made at the partnership level",
                "location_reference": "26 U.S.C. §703(b)",
                "excerpt_text": (
                    "Any election affecting the computation of taxable income derived from a partnership "
                    "shall be made by the partnership, except that any election under— (1) subsection (b)(5) "
                    "or (c)(3) of section 108 (relating to income from discharge of indebtedness), "
                    "(2) section 617 (relating to deduction and recapture of certain mining exploration "
                    "expenditures), or (3) section 901 (relating to taxes of foreign countries and "
                    "possessions of the United States), shall be made by each partner separately."
                ),
                "summary_text": "Tax elections are made by the partnership (entity-level) except the three "
                                "partner-level carve-outs (§108 COD, §617 mining, §901 foreign tax credit).",
                "is_key_excerpt": False,
            },
        ],
    },
    # ── 3. IRC §704 — distributive share allocation (STRUCTURE; math deferred per Decision C) ──
    {
        "source_code": "IRC_704",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1065",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §704 — Partner's Distributive Share (agreement controls; substantial-economic-"
                 "effect fallback; §704(c) built-in gain)",
        "citation": "26 U.S.C. §704(a), (b), (c)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/704",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "The allocation STRUCTURE the K → K-1 split follows: §704(a) the partnership agreement "
                 "controls the distributive share; §704(b) if the agreement is silent or an allocation "
                 "lacks substantial economic effect, allocate by the partner's interest in the partnership; "
                 "§704(c) built-in gain/loss on contributed property is allocated to the contributing "
                 "partner (items M/N on the K-1). Per Ken Decision C (2026-07-04): encode this as cited "
                 "structure + gating flags; the special-allocation MATH is deferred to the tts k1_allocator "
                 "(the K-1 leg reconciles it). §704(a)/(b) quoted VERBATIM 2026-07-04 from the U.S. Code.",
        "topics": ["partnership_1065_core"],
        "excerpts": [
            {
                "excerpt_label": "§704(a) — the partnership agreement controls",
                "location_reference": "26 U.S.C. §704(a)",
                "excerpt_text": (
                    "A partner's distributive share of income, gain, loss, deduction, or credit shall, "
                    "except as otherwise provided in this chapter, be determined by the partnership "
                    "agreement."
                ),
                "summary_text": "The default: distributive share is whatever the partnership agreement says "
                                "(subject to §704(b)).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§704(b) — partner's-interest fallback (no SEE)",
                "location_reference": "26 U.S.C. §704(b)(1), (2)",
                "excerpt_text": (
                    "A partner's distributive share of income, gain, loss, deduction, or credit (or item "
                    "thereof) shall be determined in accordance with the partner's interest in the "
                    "partnership (determined by taking into account all facts and circumstances), if— "
                    "(1) the partnership agreement does not provide as to the partner's distributive share "
                    "of income, gain, loss, deduction, or credit (or item thereof), or (2) the allocation "
                    "to a partner under the agreement of income, gain, loss, deduction, or credit (or item "
                    "thereof) does not have substantial economic effect."
                ),
                "summary_text": "If the agreement is silent OR an allocation lacks substantial economic "
                                "effect, allocate by the partner's interest in the partnership (facts and "
                                "circumstances). The SEE test math is RED-deferred to k1_allocator.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ── 4. IRC §707(c) — guaranteed payments (page-1 line 10, Sch K line 4a/4b/4c) ──
    {
        "source_code": "IRC_707C",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1065",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §707(c) — Guaranteed Payments (services or use of capital)",
        "citation": "26 U.S.C. §707(c)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/707",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "Guaranteed payments for services OR use of capital are deducted at the entity level "
                 "(page-1 line 10) and separately stated on Schedule K line 4 (4a services + 4b capital = "
                 "4c total). Re-used from the vetted 1065_SE load; quoted verbatim 2026-07-01.",
        "topics": ["partnership_1065_core"],
        "excerpts": [
            {
                "excerpt_label": "§707(c) — guaranteed payments for services or use of capital",
                "location_reference": "26 U.S.C. §707(c)",
                "excerpt_text": (
                    "To the extent determined without regard to the income of the partnership, payments to "
                    "a partner for services or the use of capital shall be considered as made to one who is "
                    "not a member of the partnership, but only for the purposes of section 61(a) (relating "
                    "to gross income) and, subject to section 263, for purposes of section 162(a) (relating "
                    "to trade or business expenses)."
                ),
                "summary_text": "Guaranteed payments (services 4a / capital 4b) are entity-level deductions "
                                "(page-1 line 10) and separately stated on Sch K line 4c.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ── 5. 2025 Form 1065 (the face) — line map, FILING authority, verbatim off the FINAL PDF ──
    {
        "source_code": "IRS_2025_F1065",
        "source_type": "official_form",
        "source_rank": "implementation_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1065",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "Form 1065 (2025) — U.S. Return of Partnership Income (page 1 income/deductions; "
                 "page 5 Schedule K + Analysis of Net Income)",
        "citation": "Form 1065 (2025), Cat. No. 11390Z (\"Created 11/25/25\"), page 1 lines 1a-32 + "
                    "page 5 Schedule K lines 1-21 + Analysis",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f1065.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": "The line numbers/labels here are the 1065_core_source_brief §4.1/§4.2 verbatim "
                 "transcription of the FINAL 2025 f1065.pdf (fetched 2026-07-04). REQUIRES HUMAN REVIEW: "
                 "re-verify the page-1 line 23 = ordinary business income (NOT 22) and the Schedule K "
                 "line map against the live PDF at the Ken walk before seeding.",
        "topics": ["partnership_1065_core"],
        "excerpts": [
            {
                "excerpt_label": "Page 1 — income lines 1a-8 (verbatim labels)",
                "location_reference": "f1065 (2025) page 1, Income, lines 1a-8",
                "excerpt_text": (
                    "1a Gross receipts or sales. 1b Returns and allowances. 1c Balance. Subtract line 1b "
                    "from line 1a. 2 Cost of goods sold (attach Form 1125-A). 3 Gross profit. Subtract line "
                    "2 from line 1c. 4 Ordinary income (loss) from other partnerships, estates, and trusts "
                    "(attach statement). 5 Net farm profit (loss) (attach Schedule F (Form 1040)). 6 Net "
                    "gain (loss) from Form 4797, Part II, line 17. 7 Other income (loss) (attach statement). "
                    "8 Total income (loss). Add lines 3 through 7."
                ),
                "summary_text": "Income: 1c = 1a − 1b; 3 = 1c − 2 (COGS ← 1125-A); 8 = Σ lines 3-7. Line 5 ← "
                                "Schedule F, line 6 ← Form 4797 Part II line 17.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Page 1 — deductions 9-22 + ordinary business income 23 (verbatim labels)",
                "location_reference": "f1065 (2025) page 1, Deductions, lines 9-23",
                "excerpt_text": (
                    "9 Salaries and wages (other than to partners) (less employment credits). 10 Guaranteed "
                    "payments to partners. 11 Repairs and maintenance. 12 Bad debts. 13 Rent. 14 Taxes and "
                    "licenses. 15 Interest (see instructions). 16a Depreciation (if required, attach Form "
                    "4562). 16b Less depreciation reported on Form 1125-A and elsewhere on return. 16c "
                    "[balance]. 17 Depletion (Do not deduct oil and gas depletion.). 18 Retirement plans, "
                    "etc. 19 Employee benefit programs. 20 Energy efficient commercial buildings deduction "
                    "(attach Form 7205). 21 Other deductions (attach statement). 22 Total deductions. Add "
                    "the amounts shown in the far right column for lines 9 through 21. 23 Ordinary business "
                    "income (loss). Subtract line 22 from line 8."
                ),
                "summary_text": "Deductions: 16c = 16a − 16b; 22 = Σ lines 9-21; ORDINARY BUSINESS INCOME = "
                                "line 23 = line 8 − line 22 → Schedule K line 1. (2025 face: 23 is ordinary "
                                "income, NOT 22.)",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule K (page 5) — distributive share items, Total amount column",
                "location_reference": "f1065 (2025) page 5, Schedule K lines 1-21",
                "excerpt_text": (
                    "1 Ordinary business income (loss). 2 Net rental real estate income (loss) (attach Form "
                    "8825). 3a Other gross rental income (loss). 3b Expenses from other rental activities. "
                    "3c Other net rental income (loss). 4a Guaranteed payments for services. 4b Guaranteed "
                    "payments for capital. 4c Total guaranteed payments. 5 Interest income. 6a Ordinary "
                    "dividends. 6b Qualified dividends. 6c Dividend equivalents. 7 Royalties. 8 Net "
                    "short-term capital gain (loss) (attach Schedule D (Form 1065)). 9a Net long-term "
                    "capital gain (loss). 9b Collectibles (28%) gain (loss). 9c Unrecaptured section 1250 "
                    "gain. 10 Net section 1231 gain (loss) (attach Form 4797). 11 Other income (loss). "
                    "12 Section 179 deduction (attach Form 4562). 13a Contributions. 13b Investment "
                    "interest expense. 13c Section 59(e)(2) expenditures. 13d Other deductions. 14a Net "
                    "earnings (loss) from self-employment. 14b Gross farming or fishing income. 14c Gross "
                    "nonfarm income. 15 Credits. 16 Schedule K-3 is attached if checked. 17 Alternative "
                    "minimum tax (AMT) items. 18 Tax-exempt income and nondeductible expenses. 19 "
                    "Distributions. 20 Other information. 21 Total foreign taxes paid or accrued."
                ),
                "summary_text": "The Schedule K distributive-share spine (Total amount col): income/loss 1-11, "
                                "deductions 12-13, SE 14a-c, credits 15, K-3 checkbox 16, AMT 17, "
                                "tax-exempt/nondeductible 18, distributions 19, other 20, foreign taxes 21. "
                                "Line 16 is a K-3-attached CHECKBOX (all intl detail on K-2/K-3).",
                "is_key_excerpt": True,
            },
        ],
    },
    # ── 6. 2025 Instructions for Form 1065 — aggregation/Analysis rules + OBBBA What's New ──
    {
        "source_code": "IRS_2025_I1065",
        "source_type": "official_instructions",
        "source_rank": "implementation_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1065",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Form 1065 — Analysis of Net Income (Loss), the K → K-1 "
                 "correspondence, and the OBBBA (P.L. 119-21) What's New",
        "citation": "Instructions for Form 1065 (2025), Cat. No. 11392V (dated Jan 14 2026), "
                    "Analysis of Net Income + What's New + allocation (pp. 31/34)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i1065.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": "The Analysis-of-Net-Income formula, the allocation mechanics (§706(d) varying interest; "
                 "§704(c) reasonable method), and the OBBBA What's New (§174A R&E, §181 sound recording "
                 "→ line 13e code X, §1062 farmland → line 20c code ZZ) are the brief §4.1/§4.2 verbatim "
                 "transcription of the FINAL 2025 i1065.pdf. REQUIRES HUMAN REVIEW: re-verify at the walk. "
                 "The full ~200 K-1 coded-box code lists are the K-1 authoring leg (brief §4.2).",
        "topics": ["partnership_1065_core"],
        "excerpts": [
            {
                "excerpt_label": "Analysis of Net Income (Loss) per Return, line 1 (verbatim)",
                "location_reference": "i1065 (2025), Analysis of Net Income (Loss), line 1",
                "excerpt_text": (
                    "For each line item, combine the amounts on Schedule K, lines 1 through 11. From the "
                    "result, subtract the sum of Schedule K, lines 12 through 13e, plus line 21."
                ),
                "summary_text": "Analysis of Net Income line 1 = (Σ Schedule K lines 1-11) − (Σ lines 12-13e "
                                "+ line 21). This equals Schedule M-1 line 9 / M-2 line 3.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "K → K-1 correspondence + §704/§706(d) allocation mechanics (verbatim)",
                "location_reference": "i1065 (2025) pp. 31/34, Analysis + Specific Instructions",
                "excerpt_text": (
                    "Allocate to each partner a proportionate share of each item reported on Schedule K "
                    "unless the partnership agreement provides for a special allocation. Specially allocated "
                    "items are reported on the applicable line of the partner's Schedule K-1 and are "
                    "included in the total on the corresponding line of Schedule K, not on the numbered "
                    "lines of page 1. If a partner's interest changed during the year, figure the "
                    "distributive share using the interim closing of the books method or, by agreement, the "
                    "proration method (section 706(d)). Allocations of contributed property with a built-in "
                    "gain or loss must be made under a reasonable method (section 704(c))."
                ),
                "summary_text": "Schedule K totals are allocated to partners per the agreement (special "
                                "allocations go on the applicable K-1 line and into the Sch K total, not "
                                "page 1); §706(d) governs mid-year interest changes; §704(c) built-in gain "
                                "uses a reasonable method. The MATH is deferred to k1_allocator (Decision C).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Line 21 Special Rules — Travel, meals, and entertainment (fetched 2026-07-09)",
                "location_reference": "i1065 (2025) pp. 24-25, Specific Instructions — Special Rules",
                "excerpt_text": (
                    "Subject to limitations and restrictions discussed below, a partnership can deduct "
                    "ordinary and necessary travel and non-entertainment-related meal expenses paid or "
                    "incurred in its trade or business. Generally, entertainment expenses, membership "
                    "dues, and facilities used in connection with these activities can't be deducted. ... "
                    "Meals. Generally, the partnership can deduct only 50% of the amount otherwise "
                    "allowable for non-entertainment meal expenses paid or incurred in its trade or "
                    "business. Entertainment-related meals are generally disallowed. In addition (subject "
                    "to exceptions under section 274(k)(2)): Meals must not be lavish or extravagant, and "
                    "a partner or employee of the partnership must be present at the meal. See section "
                    "274(n)(3) for a special rule that applies to expenses for meals consumed by "
                    "individuals subject to the hours of service limits of the Department of "
                    "Transportation. ... Amounts treated as compensation. Generally, the partnership may "
                    "be able to deduct otherwise nondeductible entertainment, amusement, or recreation "
                    "expenses if the amounts are treated as compensation to the recipient and reported on "
                    "Form W-2 for an employee or on Form 1099-NEC for an independent contractor."
                ),
                "summary_text": "Meals: 50% general (§274(n)(1), §274(k) partner/employee-present). DOT "
                                "hours-of-service = §274(n)(3) (80% per Pub 463). Entertainment (incl. "
                                "entertainment-related meals): nondeductible (§274(a)). "
                                "Compensation-treated amounts: deductible.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "TY2025 What's New — OBBBA (P.L. 119-21) partnership touches",
                "location_reference": "i1065 (2025), What's New",
                "excerpt_text": (
                    "Section 174A domestic research or experimental expenditures paid or incurred in tax "
                    "years beginning after 2024 may be currently deducted (or amortized over not less than "
                    "60 months by election under section 174A(c)). Qualified sound recording production "
                    "costs under section 181 may be elected as an expense and are reported on Schedule K/K-1 "
                    "line 13e using code X. Gain on the sale of qualified farmland to a qualified farmer "
                    "under section 1062 with a 4-installment election is reported on Schedule K/K-1 line 20c "
                    "using code ZZ."
                ),
                "summary_text": "OBBBA 2025: §174A R&E current deduction (page-1 other deductions), §181 sound "
                                "recording → Sch K line 13e code X, §1062 farmland → line 20c code ZZ. "
                                "Flagged (D_1065P1_174A / notes) — coded-item detail is the K-1 leg.",
                "is_key_excerpt": False,
            },
        ],
    },
]

# (source_code, form_code, link_type)
AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRC_703", "1065_PAGE1", "governs"),
    ("IRC_702", "1065_PAGE1", "informs"),
    ("IRC_707C", "1065_PAGE1", "informs"),
    ("IRS_2025_F1065", "1065_PAGE1", "governs"),
    ("IRS_2025_I1065", "1065_PAGE1", "governs"),
    ("IRC_702", "SCH_K_1065", "governs"),
    ("IRC_703", "SCH_K_1065", "informs"),
    ("IRC_704", "SCH_K_1065", "governs"),
    ("IRC_707C", "SCH_K_1065", "informs"),
    ("IRS_2025_F1065", "SCH_K_1065", "governs"),
    ("IRS_2025_I1065", "SCH_K_1065", "governs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 1: 1065_PAGE1 — Form 1065 page 1 (income & deductions → ordinary business income)
# ═══════════════════════════════════════════════════════════════════════════

PAGE1_IDENTITY = {
    "form_number": "1065_PAGE1",
    "entity_types": ["1065"],
    "form_title": "Form 1065 (2025) Page 1 — Ordinary Business Income (Income 1a-8, Deductions 9-22, "
                  "Line 23 → Schedule K line 1)",
    "notes": (
        "FRESH-AUTHORED 2026-07-04 (1065-core campaign, Schedule K spine leg) from the "
        "1065_core_source_brief §4.1 verbatim transcription of the FINAL 2025 f1065/i1065 "
        "(Cat. 11390Z / 11392V). Page-1 partnership taxable-income computation (§703): income "
        "1a-8 (1c = 1a−1b; 3 = 1c−2 COGS←1125-A; 8 = Σ3-7; line 5 ← Sch F; line 6 ← Form 4797 "
        "Part II line 17), deductions 9-22 (16c = 16a−16b depr←4562; 20 ← Form 7205; 22 = Σ9-21), "
        "and the key output ORDINARY BUSINESS INCOME = line 23 = line 8 − line 22 → Schedule K "
        "line 1 (the entity→K handoff, R-1065P1-23). ⚠ 2025 face: line 23 is ordinary income (NOT "
        "22); tax/payment block 24-32 (32b/c/d direct-deposit NEW 2025) carried as informational "
        "lines only. OBBBA §174A R&E current deduction flagged (D_1065P1_174A). RECONCILE (D-1) "
        "against tts compute.py page-1 path before seeding. READY_TO_SEED=False."
    ),
}

PAGE1_FACTS: list[dict] = [
    # Income
    {"fact_key": "p1_1a_gross_receipts", "label": "1a — Gross receipts or sales", "data_type": "decimal",
     "default_value": "0", "sort_order": 1},
    {"fact_key": "p1_1b_returns_allowances", "label": "1b — Returns and allowances", "data_type": "decimal",
     "default_value": "0", "sort_order": 2},
    {"fact_key": "p1_1c_balance", "label": "1c — Balance (1a − 1b)", "data_type": "decimal", "sort_order": 3,
     "notes": "OUTPUT. 1c = 1a − 1b."},
    {"fact_key": "p1_2_cogs", "label": "2 — Cost of goods sold (← Form 1125-A)", "data_type": "decimal",
     "default_value": "0", "sort_order": 4, "notes": "YELLOW pull from Form 1125-A line 8. D_1065P1_COGS nudges."},
    {"fact_key": "p1_3_gross_profit", "label": "3 — Gross profit (1c − 2)", "data_type": "decimal", "sort_order": 5,
     "notes": "OUTPUT. 3 = 1c − 2."},
    {"fact_key": "p1_4_other_ptr_income", "label": "4 — Ordinary income (loss) from other partnerships/estates/trusts",
     "data_type": "decimal", "default_value": "0", "sort_order": 6, "notes": "Attach statement."},
    {"fact_key": "p1_5_net_farm", "label": "5 — Net farm profit (loss) (← Schedule F)", "data_type": "decimal",
     "default_value": "0", "sort_order": 7, "notes": "YELLOW pull from Schedule F (Form 1040) line 34."},
    {"fact_key": "p1_6_net_gain_4797", "label": "6 — Net gain (loss) from Form 4797, Part II, line 17",
     "data_type": "decimal", "default_value": "0", "sort_order": 8,
     "notes": "YELLOW pull from Form 4797 Part II line 17. ⚠ Couples to the SE base (1065_SE worksheet 1d/2) "
              "and the §1245/§1250 recapture classification. D_1065P1_4797 guards."},
    {"fact_key": "p1_7_other_income", "label": "7 — Other income (loss)", "data_type": "decimal",
     "default_value": "0", "sort_order": 9, "notes": "Attach statement."},
    {"fact_key": "p1_8_total_income", "label": "8 — Total income (loss) (Σ lines 3-7)", "data_type": "decimal",
     "sort_order": 10, "notes": "OUTPUT. 8 = 3 + 4 + 5 + 6 + 7."},
    # Deductions
    {"fact_key": "p1_9_salaries_wages", "label": "9 — Salaries and wages (less employment credits)",
     "data_type": "decimal", "default_value": "0", "sort_order": 11, "notes": "Other than to partners."},
    {"fact_key": "p1_10_guaranteed_payments", "label": "10 — Guaranteed payments to partners (§707(c))",
     "data_type": "decimal", "default_value": "0", "sort_order": 12,
     "notes": "Ties to Schedule K line 4c (4a services + 4b capital). §707(c)."},
    {"fact_key": "p1_11_repairs", "label": "11 — Repairs and maintenance", "data_type": "decimal",
     "default_value": "0", "sort_order": 13},
    {"fact_key": "p1_12_bad_debts", "label": "12 — Bad debts", "data_type": "decimal", "default_value": "0",
     "sort_order": 14},
    {"fact_key": "p1_13_rent", "label": "13 — Rent", "data_type": "decimal", "default_value": "0", "sort_order": 15},
    {"fact_key": "p1_14_taxes_licenses", "label": "14 — Taxes and licenses", "data_type": "decimal",
     "default_value": "0", "sort_order": 16},
    {"fact_key": "p1_15_interest", "label": "15 — Interest", "data_type": "decimal", "default_value": "0",
     "sort_order": 17, "notes": "§163(j) business-interest limit tested on Schedule B Q24 / Form 8990 (L/M-B leg)."},
    {"fact_key": "p1_16a_depreciation", "label": "16a — Depreciation (← Form 4562)", "data_type": "decimal",
     "default_value": "0", "sort_order": 18, "notes": "YELLOW pull from Form 4562. Carries OBBBA bonus/§179 (rides 4562)."},
    {"fact_key": "p1_16b_depr_on_1125a", "label": "16b — Less depreciation reported on 1125-A/elsewhere",
     "data_type": "decimal", "default_value": "0", "sort_order": 19},
    {"fact_key": "p1_16c_depr_balance", "label": "16c — Depreciation balance (16a − 16b)", "data_type": "decimal",
     "sort_order": 20, "notes": "OUTPUT. 16c = 16a − 16b."},
    {"fact_key": "p1_17_depletion", "label": "17 — Depletion (no oil/gas)", "data_type": "decimal",
     "default_value": "0", "sort_order": 21, "notes": "Oil/gas depletion disallowed at entity (§703(a)(2)(F))."},
    {"fact_key": "p1_18_retirement", "label": "18 — Retirement plans, etc.", "data_type": "decimal",
     "default_value": "0", "sort_order": 22},
    {"fact_key": "p1_19_employee_benefits", "label": "19 — Employee benefit programs", "data_type": "decimal",
     "default_value": "0", "sort_order": 23},
    {"fact_key": "p1_20_energy_efficient", "label": "20 — Energy efficient commercial buildings (← Form 7205)",
     "data_type": "decimal", "default_value": "0", "sort_order": 24, "notes": "§179D. YELLOW pull from Form 7205."},
    {"fact_key": "p1_21_other_deductions", "label": "21 — Other deductions (attach statement)", "data_type": "decimal",
     "default_value": "0", "sort_order": 25,
     "notes": "Carries OBBBA §174A domestic R&E current deduction (tax years beginning after 2024). D_1065P1_174A."},
    {"fact_key": "p1_22_total_deductions", "label": "22 — Total deductions (Σ lines 9-21)", "data_type": "decimal",
     "sort_order": 26, "notes": "OUTPUT. 22 = 9+10+11+12+13+14+15+16c+17+18+19+20+21."},
    {"fact_key": "p1_23_ordinary_business_income", "label": "23 — Ordinary business income (loss) (8 − 22)",
     "data_type": "decimal", "sort_order": 27,
     "notes": "OUTPUT. THE key handoff: 23 = 8 − 22 → Schedule K line 1 (R-1065P1-23 / RECON-P1-K1)."},
    # Meals & entertainment four-tier worksheet — a line-21 component
    # (100% tier added by Ken ruling 2026-07-09, tts s41 usability item 9; mirrors 1120S_PAGE1 R009/R010)
    {"fact_key": "p1_21_meals_100pct", "label": "21(a) — Meals, 100% deductible (§274(n)(2)/(e) exception categories only)",
     "data_type": "decimal", "default_value": "0", "sort_order": 28,
     "notes": "ONLY the Pub 463 (2025) ch. 2 exceptions: treated as compensation (W-2/1099-NEC); reimbursed under an "
              "accountable arrangement; recreational/social employee events (holiday party, picnic); meals provided "
              "to the general public (advertising); meals sold to customers. The temporary 100% restaurant deduction "
              "(2021-2022) is EXPIRED."},
    {"fact_key": "p1_21_meals_dot_80pct", "label": "21(b) — Meals, DOT hours-of-service (80% deductible)",
     "data_type": "decimal", "default_value": "0", "sort_order": 29,
     "notes": "§274(n)(3); Pub 463 (2025): 'The percentage is 80%.'"},
    {"fact_key": "p1_21_meals_50pct", "label": "21(c) — Meals, standard business (50% deductible)",
     "data_type": "decimal", "default_value": "0", "sort_order": 30,
     "notes": "§274(n)(1) general rule per i1065 2025: 'the partnership can deduct only 50% of the amount otherwise "
              "allowable for non-entertainment meal expenses.' Not lavish; partner/employee present (§274(k))."},
    {"fact_key": "p1_21_entertainment_0pct", "label": "21(d) — Entertainment, nondeductible (0%)",
     "data_type": "decimal", "default_value": "0", "sort_order": 31,
     "notes": "§274(a) post-TCJA per i1065 2025: entertainment (incl. entertainment-related meals) can't be deducted."},
    {"fact_key": "p1_21_meals_deductible", "label": "21(e) — Meals & entertainment deductible portion (component of line 21)",
     "data_type": "decimal", "sort_order": 32, "notes": "OUTPUT of R-1065P1-MEALS."},
    {"fact_key": "p1_21_meals_nondeductible", "label": "21(f) — Meals & entertainment nondeductible portion (→ Sch K 18c, M-1 4b)",
     "data_type": "decimal", "sort_order": 33, "notes": "OUTPUT of R-1065P1-MEALSND."},
]

PAGE1_RULES: list[dict] = [
    {"rule_id": "R-1065P1-1C", "title": "Line 1c balance = 1a − 1b", "rule_type": "calculation",
     "precedence": 1, "sort_order": 1,
     "formula": "1c = line 1a (gross receipts/sales) − line 1b (returns and allowances).",
     "inputs": ["p1_1a_gross_receipts", "p1_1b_returns_allowances"], "outputs": ["p1_1c_balance"],
     "description": "f1065 page 1 line 1c."},
    {"rule_id": "R-1065P1-3", "title": "Gross profit = 1c − 2 (COGS)", "rule_type": "calculation",
     "precedence": 2, "sort_order": 2,
     "formula": "3 = line 1c − line 2 (cost of goods sold ← Form 1125-A).",
     "inputs": ["p1_1c_balance", "p1_2_cogs"], "outputs": ["p1_3_gross_profit"],
     "description": "f1065 page 1 line 3."},
    {"rule_id": "R-1065P1-8", "title": "Total income = Σ lines 3-7", "rule_type": "calculation",
     "precedence": 3, "sort_order": 3,
     "formula": ("8 = line 3 (gross profit) + line 4 (other partnerships/estates/trusts) + line 5 (net farm "
                 "← Sch F) + line 6 (net gain ← Form 4797 Part II line 17) + line 7 (other income)."),
     "inputs": ["p1_3_gross_profit", "p1_4_other_ptr_income", "p1_5_net_farm", "p1_6_net_gain_4797",
                "p1_7_other_income"],
     "outputs": ["p1_8_total_income"], "description": "f1065 page 1 line 8."},
    {"rule_id": "R-1065P1-16C", "title": "Depreciation balance 16c = 16a − 16b", "rule_type": "calculation",
     "precedence": 4, "sort_order": 4,
     "formula": "16c = line 16a (depreciation ← Form 4562) − line 16b (depr. reported on 1125-A/elsewhere).",
     "inputs": ["p1_16a_depreciation", "p1_16b_depr_on_1125a"], "outputs": ["p1_16c_depr_balance"],
     "description": "f1065 page 1 line 16c. Avoids double-counting COGS depreciation."},
    {"rule_id": "R-1065P1-22", "title": "Total deductions = Σ lines 9-21 (16c for 16)", "rule_type": "calculation",
     "precedence": 5, "sort_order": 5,
     "formula": ("22 = line 9 + 10 + 11 + 12 + 13 + 14 + 15 + 16c + 17 + 18 + 19 + 20 + 21. §703(a)(2) "
                 "disallows six deductions at the entity level (personal exemptions, foreign taxes, "
                 "charitable, NOL, individual itemized, oil/gas depletion) — none appear on page 1; "
                 "charitable + §179 are separately stated on Schedule K instead."),
     "inputs": ["p1_9_salaries_wages", "p1_10_guaranteed_payments", "p1_11_repairs", "p1_12_bad_debts",
                "p1_13_rent", "p1_14_taxes_licenses", "p1_15_interest", "p1_16c_depr_balance",
                "p1_17_depletion", "p1_18_retirement", "p1_19_employee_benefits", "p1_20_energy_efficient",
                "p1_21_other_deductions"],
     "outputs": ["p1_22_total_deductions"], "description": "f1065 page 1 line 22 (§703(a))."},
    {"rule_id": "R-1065P1-23", "title": "Ordinary business income = line 8 − line 22 → Schedule K line 1",
     "rule_type": "calculation", "precedence": 6, "sort_order": 6,
     "formula": ("23 = line 8 (total income) − line 22 (total deductions). This IS the partnership's ordinary "
                 "trade-or-business income (§702(a)(8) / §703(a)) and flows to Schedule K line 1 (the entity→K "
                 "handoff; RECON-P1-K1). ⚠ 2025 face: ordinary business income is line 23, NOT line 22."),
     "inputs": ["p1_8_total_income", "p1_22_total_deductions"], "outputs": ["p1_23_ordinary_business_income"],
     "description": "f1065 page 1 line 23 → Sch K line 1. The load-bearing handoff."},
    {"rule_id": "R-1065P1-MEALS", "title": "Meals & entertainment worksheet — deductible portion (line 21 component)",
     "rule_type": "calculation", "precedence": 4, "sort_order": 8,
     "formula": ("p1_21_meals_deductible = 1.00*p1_21_meals_100pct + 0.80*p1_21_meals_dot_80pct + "
                 "0.50*p1_21_meals_50pct + 0.00*p1_21_entertainment_0pct"),
     "inputs": ["p1_21_meals_100pct", "p1_21_meals_dot_80pct", "p1_21_meals_50pct", "p1_21_entertainment_0pct"],
     "outputs": ["p1_21_meals_deductible"],
     "description": ("Four-tier meal/entertainment limitation worksheet (mirrors 1120S_PAGE1 R009). Deductible "
                     "portion = 100% of §274(n)(2)(A)/(e) exception-category meals + 80% of DOT hours-of-service "
                     "meals (§274(n)(3)) + 50% of standard business meals (§274(n)(1)) + 0% of entertainment "
                     "(§274(a)). The result is a COMPONENT of line 21 other deductions. 100% tier NEW per Ken "
                     "ruling 2026-07-09 (tts s41 usability item 9). Verified verbatim: i1065 (2025) pp. 24-25 "
                     "Special Rules; Pub 463 (2025) ch. 2 Exceptions 1-6 + DOT 80%. TY2026 WATCH: §274(o) "
                     "(employer-convenience meals) applies to amounts paid after 12/31/2025 — re-verify at the "
                     "2026 spec cut.")},
    {"rule_id": "R-1065P1-MEALSND", "title": "Meals & entertainment worksheet — nondeductible portion routing",
     "rule_type": "routing", "precedence": 4, "sort_order": 9,
     "formula": ("p1_21_meals_nondeductible = 0.50*p1_21_meals_50pct + 0.20*p1_21_meals_dot_80pct + "
                 "1.00*p1_21_entertainment_0pct"),
     "inputs": ["p1_21_meals_50pct", "p1_21_meals_dot_80pct", "p1_21_entertainment_0pct"],
     "outputs": ["p1_21_meals_nondeductible"],
     "description": ("Nondeductible portion = 50% of standard meals + 20% of DOT meals + 100% of entertainment "
                     "(the 100% tier contributes nothing). Routes to Schedule K line 18c (nondeductible expenses) "
                     "and M-1 line 4b (positive add-back). Never a page-1 deduction. Deductible + nondeductible "
                     "must sum to the four-tier book total.")},
    {"rule_id": "R-1065P1-174A", "title": "OBBBA §174A domestic R&E — current deduction (flag)",
     "rule_type": "conditional", "precedence": 7, "sort_order": 7,
     "formula": ("OBBBA (P.L. 119-21): domestic research or experimental expenditures paid/incurred in tax "
                 "years beginning after 2024 may be CURRENTLY deducted (line 21 other deductions) or "
                 "amortized over ≥60 months by election under §174A(c). NEW for 2025 — a treatment choice, "
                 "flagged (D_1065P1_174A), not auto-applied. (Foreign R&E stays §174 15-yr amortization.)"),
     "inputs": ["p1_21_other_deductions"], "outputs": [],
     "description": "i1065 2025 What's New (OBBBA). Surfaces the §174A election as a preparer determination."},
]

PAGE1_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-1065P1-1C", "IRS_2025_F1065", "primary", "f1065 page 1 line 1c = 1a − 1b"),
    ("R-1065P1-3", "IRS_2025_F1065", "primary", "f1065 page 1 line 3 = 1c − 2 (COGS ← 1125-A)"),
    ("R-1065P1-8", "IRS_2025_F1065", "primary", "f1065 page 1 line 8 = Σ lines 3-7"),
    ("R-1065P1-8", "IRC_703", "secondary", "§703(a) partnership taxable income computed as an individual"),
    ("R-1065P1-16C", "IRS_2025_F1065", "primary", "f1065 page 1 line 16c = 16a − 16b"),
    ("R-1065P1-22", "IRS_2025_F1065", "primary", "f1065 page 1 line 22 = Σ lines 9-21"),
    ("R-1065P1-22", "IRC_703", "primary", "§703(a)(1)/(a)(2) separately-stated items + disallowed deductions"),
    ("R-1065P1-23", "IRS_2025_F1065", "primary", "f1065 page 1 line 23 = 8 − 22 → Sch K line 1"),
    ("R-1065P1-23", "IRC_702", "secondary", "§702(a)(8) residual trade-or-business income"),
    ("R-1065P1-23", "IRC_703", "secondary", "§703(a) partnership taxable income"),
    ("R-1065P1-174A", "IRS_2025_I1065", "primary", "i1065 2025 What's New — §174A domestic R&E current deduction"),
    ("R-1065P1-MEALS", "IRS_2025_I1065", "primary", "i1065 (2025) pp. 24-25 Special Rules — meals 50% general; §274(n)(3) DOT; entertainment nondeductible; compensation-treated deductible"),
    ("R-1065P1-MEALS", "IRS_2025_PUB463", "primary", "Pub 463 (2025) ch. 2 — Exceptions 1-6 to the 50% limit (the 100% tier) + DOT 80%"),
    ("R-1065P1-MEALS", "IRC_274", "secondary", "§274(a)/(k)/(n)(1)/(n)(2)/(n)(3) statutory tiers"),
    ("R-1065P1-MEALSND", "IRS_2025_I1065", "primary", "Nondeductible portion → Schedule K 18c / M-1 4b add-back"),
    ("R-1065P1-MEALSND", "IRC_274", "secondary", "§274 disallowed portion — permanent book-tax difference"),
]

PAGE1_LINES: list[dict] = [
    {"line_number": "1a", "description": "Gross receipts or sales", "line_type": "input", "sort_order": 1,
     "source_facts": ["p1_1a_gross_receipts"]},
    {"line_number": "1b", "description": "Returns and allowances", "line_type": "input", "sort_order": 2,
     "source_facts": ["p1_1b_returns_allowances"]},
    {"line_number": "1c", "description": "Balance (1a − 1b)", "line_type": "subtotal", "sort_order": 3,
     "source_rules": ["R-1065P1-1C"]},
    {"line_number": "2", "description": "Cost of goods sold (attach Form 1125-A)", "line_type": "calculated",
     "sort_order": 4, "source_facts": ["p1_2_cogs"], "notes": "YELLOW pull from Form 1125-A line 8."},
    {"line_number": "3", "description": "Gross profit (1c − 2)", "line_type": "subtotal", "sort_order": 5,
     "source_rules": ["R-1065P1-3"]},
    {"line_number": "4", "description": "Ordinary income (loss) from other partnerships, estates, and trusts",
     "line_type": "input", "sort_order": 6, "source_facts": ["p1_4_other_ptr_income"]},
    {"line_number": "5", "description": "Net farm profit (loss) (attach Schedule F)", "line_type": "calculated",
     "sort_order": 7, "source_facts": ["p1_5_net_farm"]},
    {"line_number": "6", "description": "Net gain (loss) from Form 4797, Part II, line 17", "line_type": "calculated",
     "sort_order": 8, "source_facts": ["p1_6_net_gain_4797"]},
    {"line_number": "7", "description": "Other income (loss) (attach statement)", "line_type": "input",
     "sort_order": 9, "source_facts": ["p1_7_other_income"]},
    {"line_number": "8", "description": "Total income (loss) (Σ lines 3-7)", "line_type": "subtotal",
     "sort_order": 10, "source_rules": ["R-1065P1-8"]},
    {"line_number": "9", "description": "Salaries and wages (less employment credits)", "line_type": "input",
     "sort_order": 11, "source_facts": ["p1_9_salaries_wages"]},
    {"line_number": "10", "description": "Guaranteed payments to partners", "line_type": "input", "sort_order": 12,
     "source_facts": ["p1_10_guaranteed_payments"]},
    {"line_number": "11", "description": "Repairs and maintenance", "line_type": "input", "sort_order": 13,
     "source_facts": ["p1_11_repairs"]},
    {"line_number": "12", "description": "Bad debts", "line_type": "input", "sort_order": 14,
     "source_facts": ["p1_12_bad_debts"]},
    {"line_number": "13", "description": "Rent", "line_type": "input", "sort_order": 15, "source_facts": ["p1_13_rent"]},
    {"line_number": "14", "description": "Taxes and licenses", "line_type": "input", "sort_order": 16,
     "source_facts": ["p1_14_taxes_licenses"]},
    {"line_number": "15", "description": "Interest", "line_type": "input", "sort_order": 17,
     "source_facts": ["p1_15_interest"]},
    {"line_number": "16a", "description": "Depreciation (attach Form 4562)", "line_type": "calculated",
     "sort_order": 18, "source_facts": ["p1_16a_depreciation"]},
    {"line_number": "16b", "description": "Less depreciation reported on 1125-A and elsewhere", "line_type": "input",
     "sort_order": 19, "source_facts": ["p1_16b_depr_on_1125a"]},
    {"line_number": "16c", "description": "Depreciation balance (16a − 16b)", "line_type": "subtotal",
     "sort_order": 20, "source_rules": ["R-1065P1-16C"]},
    {"line_number": "17", "description": "Depletion (do not deduct oil and gas depletion)", "line_type": "input",
     "sort_order": 21, "source_facts": ["p1_17_depletion"]},
    {"line_number": "18", "description": "Retirement plans, etc.", "line_type": "input", "sort_order": 22,
     "source_facts": ["p1_18_retirement"]},
    {"line_number": "19", "description": "Employee benefit programs", "line_type": "input", "sort_order": 23,
     "source_facts": ["p1_19_employee_benefits"]},
    {"line_number": "20", "description": "Energy efficient commercial buildings deduction (attach Form 7205)",
     "line_type": "calculated", "sort_order": 24, "source_facts": ["p1_20_energy_efficient"]},
    {"line_number": "21", "description": "Other deductions (attach statement)", "line_type": "input", "sort_order": 25,
     "source_facts": ["p1_21_other_deductions"], "source_rules": ["R-1065P1-174A", "R-1065P1-MEALS"],
     "notes": "Includes ONLY the deductible portion of meals per the R-1065P1-MEALS four-tier worksheet "
              "(100%/80%/50%/0%); the nondeductible portion routes to Sch K 18c / M-1 4b (R-1065P1-MEALSND)."},
    {"line_number": "22", "description": "Total deductions (Σ lines 9-21)", "line_type": "subtotal", "sort_order": 26,
     "source_rules": ["R-1065P1-22"]},
    {"line_number": "23", "description": "Ordinary business income (loss) (line 8 − line 22)", "line_type": "total",
     "sort_order": 27, "source_rules": ["R-1065P1-23"], "destination_form": "SCH_K_1065",
     "notes": "→ Schedule K line 1 (the entity→K handoff)."},
    # Tax & payment block (informational only — carried for completeness, brief §4.1)
    {"line_number": "24", "description": "Interest due under the look-back method (Form 8697)", "line_type": "input",
     "sort_order": 30, "notes": "Tax/payment block — informational (not computed this leg)."},
    {"line_number": "25", "description": "Interest due under the look-back method — income forecast (Form 8866)",
     "line_type": "input", "sort_order": 31, "notes": "Informational."},
    {"line_number": "26", "description": "BBA AAR imputed underpayment", "line_type": "input", "sort_order": 32,
     "notes": "Informational."},
    {"line_number": "29", "description": "Elective payment election amount (from Form 3800)", "line_type": "input",
     "sort_order": 33, "notes": "Informational — ties to the S3/S4 credits (Form 3800)."},
    {"line_number": "32", "description": "Overpayment + direct-deposit routing/type/account (32a-32d)",
     "line_type": "input", "sort_order": 34, "notes": "32b/32c/32d NEW for 2025 (Exec. Order 14247). Informational."},
]

PAGE1_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_1065P1_COGS", "title": "COGS present — confirm from Form 1125-A", "severity": "warning",
     "condition": "p1_2_cogs != 0 AND Form 1125-A not attached/linked",
     "message": ("Line 2 cost of goods sold should carry from Form 1125-A line 8. Confirm 1125-A is prepared "
                 "and its line 8 ties to this amount — page-1 gross profit (line 3) depends on it."),
     "notes": "Nudge — 1125-A is a separate form not built this leg."},
    {"diagnostic_id": "D_1065P1_4797", "title": "Line 6 net gain must come from Form 4797 Part II line 17",
     "severity": "warning",
     "condition": "p1_6_net_gain_4797 != 0",
     "message": ("Line 6 net gain (loss) carries from Form 4797, Part II, line 17. This amount feeds ordinary "
                 "business income (line 23 → Schedule K line 1) AND the self-employment base (1065_SE "
                 "worksheet lines 1d/2 back it out). Confirm the Form 4797 Part II §1245/§1250 recapture "
                 "classification is correct — box 14a and line 23 both depend on it."),
     "notes": "Couples page 1 → SE base (1065_SE) → the §1245/§1250 verification. Cross-form dependency flag."},
    {"diagnostic_id": "D_1065P1_174A", "title": "OBBBA §174A domestic R&E — deduct or amortize?", "severity": "info",
     "condition": "domestic R&E present in line 21",
     "message": ("OBBBA (2025): domestic research/experimental expenditures (tax years beginning after 2024) "
                 "may be currently deducted here on line 21 or amortized over ≥60 months by §174A(c) "
                 "election. This is a preparer/taxpayer choice — confirm the intended treatment. (Foreign "
                 "R&E remains §174 15-year amortization.)"),
     "notes": "OBBBA What's New flag. Not auto-applied (treatment election)."},
    {"diagnostic_id": "D_1065P1_MEALS100", "title": "100% meals tier is exception-only", "severity": "warning",
     "condition": "p1_21_meals_100pct > 0",
     "message": ("Amounts on the 100% meals line must fit a section 274(n)(2)/(e) exception: treated as "
                 "compensation (W-2/1099-NEC), reimbursed under an accountable arrangement, recreational or "
                 "social employee events (e.g., holiday party), meals provided to the general public, or meals "
                 "sold to customers. Standard business meals are 50% — the temporary 100% restaurant deduction "
                 "expired after 2022. Verify the classification."),
     "notes": "Mirrors 1120S_PAGE1 D004 (Ken ruling 2026-07-09, tts s41 usability item 9)."},
]

PAGE1_SCENARIOS: list[dict] = [
    {"scenario_name": "P1-1 — ordinary business income baseline (23 = 8 − 22)", "scenario_type": "normal",
     "sort_order": 1,
     "inputs": {"p1_1a_gross_receipts": 1000000, "p1_1b_returns_allowances": 0, "p1_2_cogs": 400000,
                "p1_9_salaries_wages": 200000, "p1_10_guaranteed_payments": 100000, "p1_13_rent": 50000,
                "p1_16a_depreciation": 30000},
     "expected_outputs": {"p1_1c_balance": 1000000, "p1_3_gross_profit": 600000, "p1_8_total_income": 600000,
                          "p1_22_total_deductions": 380000, "p1_23_ordinary_business_income": 220000},
     "notes": "1c=1M; 3=1M−400k=600k; 8=600k; 22=200k+100k+50k+30k=380k; 23=600k−380k=220k → Sch K line 1."},
    {"scenario_name": "P1-2 — returns + 16b depreciation offset", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"p1_1a_gross_receipts": 500000, "p1_1b_returns_allowances": 20000, "p1_2_cogs": 180000,
                "p1_16a_depreciation": 40000, "p1_16b_depr_on_1125a": 15000, "p1_9_salaries_wages": 90000},
     "expected_outputs": {"p1_1c_balance": 480000, "p1_3_gross_profit": 300000, "p1_16c_depr_balance": 25000,
                          "p1_8_total_income": 300000, "p1_22_total_deductions": 115000,
                          "p1_23_ordinary_business_income": 185000},
     "notes": "1c=480k; 3=300k; 16c=40k−15k=25k (COGS depr removed); 22=90k+25k=115k; 23=185k."},
    {"scenario_name": "P1-3 — 4797 Part II gain in ordinary income (couples to SE)", "scenario_type": "edge",
     "sort_order": 3,
     "inputs": {"p1_3_gross_profit": 0, "p1_1a_gross_receipts": 0, "p1_6_net_gain_4797": 30000,
                "p1_11_repairs": 5000},
     "expected_outputs": {"p1_8_total_income": 30000, "p1_22_total_deductions": 5000,
                          "p1_23_ordinary_business_income": 25000, "D_1065P1_4797": True},
     "notes": "4797 Part II line 17 net gain 30k flows into line 8 → line 23 = 25k. D_1065P1_4797 fires "
              "(the SE base 1065_SE will back it out at worksheet line 2)."},
    {"scenario_name": "P1-4 — ordinary LOSS (line 23 negative)", "scenario_type": "edge", "sort_order": 4,
     "inputs": {"p1_1a_gross_receipts": 300000, "p1_2_cogs": 150000, "p1_9_salaries_wages": 120000,
                "p1_13_rent": 60000, "p1_16a_depreciation": 20000},
     "expected_outputs": {"p1_3_gross_profit": 150000, "p1_8_total_income": 150000,
                          "p1_22_total_deductions": 200000, "p1_23_ordinary_business_income": -50000},
     "notes": "3=150k; 22=120k+60k+20k=200k; 23=150k−200k=(50k) ordinary loss → Sch K line 1 negative."},
    {"scenario_name": "P1-5 — M&E four-tier worksheet split", "scenario_type": "normal", "sort_order": 5,
     "inputs": {"p1_21_meals_100pct": 2000, "p1_21_meals_dot_80pct": 1000, "p1_21_meals_50pct": 10000,
                "p1_21_entertainment_0pct": 3000},
     "expected_outputs": {"p1_21_meals_deductible": 7800, "p1_21_meals_nondeductible": 8200},
     "notes": "2,000x100% + 1,000x80% + 10,000x50% + 3,000x0% = 7,800 deductible (component of line 21); "
              "5,000 + 200 + 3,000 = 8,200 nondeductible (Sch K 18c / M-1 4b). Portions sum to the 16,000 "
              "book total. 100% tier per Ken ruling 2026-07-09."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 2: SCH_K_1065 — Schedule K distributive-share spine + Analysis of Net Income
# ═══════════════════════════════════════════════════════════════════════════

SCHK_IDENTITY = {
    "form_number": "SCH_K_1065",
    "entity_types": ["1065"],
    "form_title": "Schedule K (Form 1065, 2025) — Partners' Distributive Share Items (Total amount) + "
                  "Analysis of Net Income (Loss)",
    "notes": (
        "FRESH-AUTHORED 2026-07-04 (1065-core campaign, spine leg) from the 1065_core_source_brief "
        "§4.2 verbatim transcription of the FINAL 2025 f1065 page 5 / i1065 (Cat. 11390Z / 11392V). "
        "The distributive-share SPINE, 'Total amount' column: income/loss 1-11 (line 1 ← 1065_PAGE1 "
        "line 23; 3c = 3a−3b; 4c = 4a+4b; 8/9a ← Sch D; 9c unrecaptured §1250 ← 4797; 10 ← Form 4797; "
        "14a = the 1065_SE spec), deductions 12-13, SE 14a-c, credits 15, line 16 = Schedule K-3 "
        "checkbox, AMT 17, tax-exempt/nondeductible 18, distributions 19, other 20, foreign taxes 21. "
        "Analysis of Net Income line 1 = (Σ K lines 1-11) − (Σ 12-13e + 21). SCOPE (Ken 2026-07-04): "
        "A. K-2/K-3 RED-DEFER (line 16 checkbox only + D_SCHK_K3); C. §704(b)/(c) STRUCTURE ONLY "
        "(R-SCHK-ALLOC cites §704(a)/(b)/§706(d); per-partner MATH deferred to k1_allocator, item M/N "
        "→ D_SCHK_704C). The K → K-1 per-partner split + full coded-box code lists are the NEXT leg "
        "(Schedule K-1 + allocation engine). RECONCILE (D-1) against compute_schedule_k1 box map + "
        "k1_allocator before seeding. READY_TO_SEED=False."
    ),
}

SCHK_FACTS: list[dict] = [
    # Income (loss) 1-11
    {"fact_key": "k_1_ordinary", "label": "1 — Ordinary business income (loss) (← 1065_PAGE1 line 23)",
     "data_type": "decimal", "default_value": "0", "sort_order": 1,
     "notes": "YELLOW pull from Form 1065 page-1 line 23 (RECON-P1-K1). §702(a)(8)."},
    {"fact_key": "k_2_net_rental_re", "label": "2 — Net rental real estate income (loss) (← Form 8825)",
     "data_type": "decimal", "default_value": "0", "sort_order": 2, "notes": "YELLOW pull from Form 8825 (specced)."},
    {"fact_key": "k_3a_other_gross_rental", "label": "3a — Other gross rental income (loss)", "data_type": "decimal",
     "default_value": "0", "sort_order": 3},
    {"fact_key": "k_3b_other_rental_exp", "label": "3b — Expenses from other rental activities", "data_type": "decimal",
     "default_value": "0", "sort_order": 4},
    {"fact_key": "k_3c_other_net_rental", "label": "3c — Other net rental income (loss) (3a − 3b)",
     "data_type": "decimal", "sort_order": 5, "notes": "OUTPUT. 3c = 3a − 3b. Feeds the 1065_SE base (worksheet 1c)."},
    {"fact_key": "k_4a_gp_services", "label": "4a — Guaranteed payments for services (§707(c))", "data_type": "decimal",
     "default_value": "0", "sort_order": 6},
    {"fact_key": "k_4b_gp_capital", "label": "4b — Guaranteed payments for capital (§707(c))", "data_type": "decimal",
     "default_value": "0", "sort_order": 7},
    {"fact_key": "k_4c_gp_total", "label": "4c — Total guaranteed payments (4a + 4b)", "data_type": "decimal",
     "sort_order": 8, "notes": "OUTPUT. 4c = 4a + 4b. Ties to page-1 line 10; feeds 1065_SE worksheet 4a."},
    {"fact_key": "k_5_interest", "label": "5 — Interest income", "data_type": "decimal", "default_value": "0",
     "sort_order": 9, "notes": "Portfolio — not SE (§1402(a)(2))."},
    {"fact_key": "k_6a_ordinary_div", "label": "6a — Ordinary dividends", "data_type": "decimal", "default_value": "0",
     "sort_order": 10},
    {"fact_key": "k_6b_qualified_div", "label": "6b — Qualified dividends", "data_type": "decimal", "default_value": "0",
     "sort_order": 11, "notes": "Subset of 6a; character conduit §702(b)."},
    {"fact_key": "k_6c_dividend_equiv", "label": "6c — Dividend equivalents", "data_type": "decimal",
     "default_value": "0", "sort_order": 12},
    {"fact_key": "k_7_royalties", "label": "7 — Royalties", "data_type": "decimal", "default_value": "0",
     "sort_order": 13},
    {"fact_key": "k_8_net_st_capgain", "label": "8 — Net short-term capital gain (loss) (← Schedule D (1065))",
     "data_type": "decimal", "default_value": "0", "sort_order": 14},
    {"fact_key": "k_9a_net_lt_capgain", "label": "9a — Net long-term capital gain (loss) (← Schedule D (1065))",
     "data_type": "decimal", "default_value": "0", "sort_order": 15},
    {"fact_key": "k_9b_collectibles_28", "label": "9b — Collectibles (28%) gain (loss)", "data_type": "decimal",
     "default_value": "0", "sort_order": 16},
    {"fact_key": "k_9c_unrecap_1250", "label": "9c — Unrecaptured section 1250 gain (← Form 4797)",
     "data_type": "decimal", "default_value": "0", "sort_order": 17,
     "notes": "YELLOW pull from the 4797 aggregate (tts K9c fix f23dc54). Passes to K-1 box 9c (the open "
              "tts verification). D_SCHK_9C surfaces it."},
    {"fact_key": "k_10_net_1231", "label": "10 — Net section 1231 gain (loss) (← Form 4797)", "data_type": "decimal",
     "default_value": "0", "sort_order": 18},
    {"fact_key": "k_11_other_income", "label": "11 — Other income (loss) (coded)", "data_type": "decimal",
     "default_value": "0", "sort_order": 19, "notes": "Coded K-1 box 11 (code detail = K-1 leg)."},
    # Deductions 12-13
    {"fact_key": "k_12_section_179", "label": "12 — Section 179 deduction (← Form 4562)", "data_type": "decimal",
     "default_value": "0", "sort_order": 20, "notes": "Separately stated (partner-level limit); §179 not on page 1."},
    {"fact_key": "k_13a_contributions", "label": "13a — Contributions (charitable)", "data_type": "decimal",
     "default_value": "0", "sort_order": 21, "notes": "§703(a)(2)(C) disallowed at entity → separately stated here."},
    {"fact_key": "k_13b_invest_interest", "label": "13b — Investment interest expense (§163(d))", "data_type": "decimal",
     "default_value": "0", "sort_order": 22},
    {"fact_key": "k_13c_section_59e2", "label": "13c — Section 59(e)(2) expenditures", "data_type": "decimal",
     "default_value": "0", "sort_order": 23},
    {"fact_key": "k_13e_other_deductions", "label": "13e — Other deductions (coded; incl. OBBBA §181 code X)",
     "data_type": "decimal", "default_value": "0", "sort_order": 24,
     "notes": "Coded K-1 box 13. OBBBA §181 qualified sound-recording → code X (i1065 What's New)."},
    # Self-employment 14
    {"fact_key": "k_14a_se_earnings", "label": "14a — Net earnings (loss) from self-employment (= 1065_SE spec)",
     "data_type": "decimal", "default_value": "0", "sort_order": 25,
     "notes": "Governed by the 1065_SE spec (do NOT recompute here — cross-ref R-SCHK-14A)."},
    {"fact_key": "k_14b_gross_farming", "label": "14b — Gross farming or fishing income", "data_type": "decimal",
     "default_value": "0", "sort_order": 26, "notes": "OUT OF SCOPE for compute (1065_SE §14.4) — carried as a line."},
    {"fact_key": "k_14c_gross_nonfarm", "label": "14c — Gross nonfarm income", "data_type": "decimal",
     "default_value": "0", "sort_order": 27, "notes": "OUT OF SCOPE for compute (1065_SE §14.4)."},
    # Credits 15
    {"fact_key": "k_15_credits", "label": "15 — Credits (coded; incl. S3/S4 pass-through credits)",
     "data_type": "decimal", "default_value": "0", "sort_order": 28,
     "notes": "Coded K-1 box 15. Carries the S3/S4 credits: AY 8936 new clean vehicle, AZ 8936 commercial, "
              "AB 8835 renewable electricity, W §45Y. Code detail = K-1 leg."},
    # International 16 — K-2/K-3 RED-DEFER (Decision A)
    {"fact_key": "k_16_k3_attached", "label": "16 — Schedule K-3 is attached (checkbox)", "data_type": "boolean",
     "default_value": "false", "sort_order": 29,
     "notes": "Decision A (RED-DEFER): line 16 is only a K-3-attached checkbox; all international detail lives "
              "on Schedules K-2/K-3, which are OUT of season-one scope. D_SCHK_K3 fires (RED) when checked."},
    # AMT / other 17-21
    {"fact_key": "k_17_amt_items", "label": "17 — Alternative minimum tax (AMT) items (coded)", "data_type": "decimal",
     "default_value": "0", "sort_order": 30},
    {"fact_key": "k_18a_taxexempt_interest", "label": "18a — Tax-exempt interest income", "data_type": "decimal",
     "default_value": "0", "sort_order": 31, "notes": "Feeds M-1 line 6a / M-2 (L/M leg). Character conduit."},
    {"fact_key": "k_18b_other_taxexempt", "label": "18b — Other tax-exempt income", "data_type": "decimal",
     "default_value": "0", "sort_order": 32},
    {"fact_key": "k_18c_nondeductible", "label": "18c — Nondeductible expenses", "data_type": "decimal",
     "default_value": "0", "sort_order": 33},
    {"fact_key": "k_19a_distributions_cash", "label": "19a — Distributions of cash and marketable securities",
     "data_type": "decimal", "default_value": "0", "sort_order": 34, "notes": "Feeds M-2 line 6a (L/M leg)."},
    {"fact_key": "k_19b_distributions_property", "label": "19b — Distributions of other property", "data_type": "decimal",
     "default_value": "0", "sort_order": 35, "notes": "Feeds M-2 line 6b (L/M leg)."},
    {"fact_key": "k_20_other_information", "label": "20 — Other information (coded; incl. §199A code Z, OBBBA ZZ)",
     "data_type": "decimal", "default_value": "0", "sort_order": 36,
     "notes": "Coded K-1 box 20: §199A (Z), §704(c) (AA), §751 (AB), §163(j) (N/AE/AF), §461(l) EBL (AJ, "
              "partner-level), OBBBA §1062 farmland (ZZ). Code detail = K-1 leg."},
    {"fact_key": "k_21_foreign_taxes", "label": "21 — Total foreign taxes paid or accrued", "data_type": "decimal",
     "default_value": "0", "sort_order": 37, "notes": "Reduces Analysis line 1. §901 election is partner-level (§703(b))."},
    # §704(c) structure flags (Decision C — structure, math deferred)
    {"fact_key": "k_has_704c_property", "label": "§704(c) — contributed built-in-gain/loss property present? (item M)",
     "data_type": "boolean", "default_value": "false", "sort_order": 40,
     "notes": "Gating flag (K-1 item M). If true, §704(c) reasonable-method allocation applies — MATH deferred "
              "to k1_allocator (Decision C). D_SCHK_704C surfaces."},
    {"fact_key": "k_has_special_alloc", "label": "Special allocation present (not pro-rata by interest)?",
     "data_type": "boolean", "default_value": "false", "sort_order": 41,
     "notes": "Gating flag. If true, §704(b) substantial-economic-effect must be tested — deferred to "
              "k1_allocator; reconcile what it handles vs. RED-defer (D-1)."},
    # Analysis of Net Income (Loss)
    {"fact_key": "k_analysis_net_income", "label": "Analysis of Net Income (Loss) per Return, line 1",
     "data_type": "decimal", "sort_order": 50,
     "notes": "OUTPUT. = (Σ K lines 1-11) − (Σ lines 12-13e + 21). = M-1 line 9 / M-2 line 3 (L/M leg)."},
]

SCHK_RULES: list[dict] = [
    {"rule_id": "R-SCHK-1", "title": "Schedule K line 1 = 1065 page-1 line 23 (the entity→K handoff)",
     "rule_type": "routing", "precedence": 1, "sort_order": 1,
     "formula": ("Schedule K line 1 (ordinary business income) = Form 1065 page-1 line 23. §702(a)(8): the "
                 "residual trade-or-business distributive share. RECON-P1-K1 enforces equality; a break fires "
                 "D_SCHK_HANDOFF. This is the single load-bearing tie between page 1 and the K spine."),
     "inputs": ["k_1_ordinary"], "outputs": [],
     "description": "f1065 Sch K line 1 = page-1 line 23. §702(a)(8)."},
    {"rule_id": "R-SCHK-3C", "title": "Other net rental 3c = 3a − 3b", "rule_type": "calculation",
     "precedence": 2, "sort_order": 2,
     "formula": "3c = line 3a (other gross rental) − line 3b (other rental expenses). Feeds 1065_SE worksheet 1c.",
     "inputs": ["k_3a_other_gross_rental", "k_3b_other_rental_exp"], "outputs": ["k_3c_other_net_rental"],
     "description": "f1065 Sch K line 3c."},
    {"rule_id": "R-SCHK-4C", "title": "Total guaranteed payments 4c = 4a + 4b", "rule_type": "calculation",
     "precedence": 3, "sort_order": 3,
     "formula": ("4c = line 4a (guaranteed payments for services) + line 4b (guaranteed payments for capital). "
                 "§707(c). Ties to page-1 line 10; feeds the 1065_SE worksheet 4a GP pool."),
     "inputs": ["k_4a_gp_services", "k_4b_gp_capital"], "outputs": ["k_4c_gp_total"],
     "description": "f1065 Sch K line 4c. §707(c)."},
    {"rule_id": "R-SCHK-SEPARATE", "title": "Separately-stated items retain partnership-level character",
     "rule_type": "classification", "precedence": 4, "sort_order": 4,
     "formula": ("Schedule K lines 2-21 are the §702(a)(1)-(7) separately-stated items pulled OFF page-1 "
                 "ordinary income (§703(a)(1)). Each retains its partnership-level character in the partner's "
                 "hands (§702(b)) — rental stays rental, portfolio stays portfolio, capital gain stays capital "
                 "gain, charitable + §179 are separately stated (disallowed at entity per §703(a)(2)). This is "
                 "why they are broken out rather than folded into line 1."),
     "inputs": ["k_2_net_rental_re", "k_5_interest", "k_7_royalties", "k_8_net_st_capgain",
                "k_9a_net_lt_capgain", "k_12_section_179", "k_13a_contributions"], "outputs": [],
     "description": "§702(a)/(b) + §703(a). The character-conduit structural rule behind the K spine."},
    {"rule_id": "R-SCHK-ALLOC", "title": "Distributive share allocated per agreement (§704 structure; math deferred)",
     "rule_type": "routing", "precedence": 5, "sort_order": 5,
     "formula": ("Each Schedule K total is allocated to partners for the K-1 per the partnership agreement "
                 "(§704(a)); if the agreement is silent or an allocation lacks substantial economic effect, "
                 "by the partner's interest (§704(b)). §704(c) built-in gain on contributed property (item M) "
                 "uses a reasonable method; §706(d) governs mid-year interest changes (interim-closing or "
                 "proration). SCOPE (Ken Decision C, 2026-07-04): STRUCTURE + gating flags only "
                 "(k_has_704c_property, k_has_special_alloc); the special-allocation MATH is deferred to the "
                 "tts k1_allocator (the Schedule K-1 leg reconciles it; item M/N → D_SCHK_704C)."),
     "inputs": ["k_has_704c_property", "k_has_special_alloc"], "outputs": [],
     "description": "§704(a)/(b)/(c) + §706(d). The allocation structure; per-partner math is the K-1 leg."},
    {"rule_id": "R-SCHK-KMAP", "title": "K → K-1 correspondence (1:1 for 1-10; coded-collapse for 11/13/14/15/17-20)",
     "rule_type": "routing", "precedence": 6, "sort_order": 6,
     "formula": ("The K → K-1 box map: Schedule K lines 1-10 (and 3c/4c/6/9 sub-lines) map 1:1 to K-1 boxes "
                 "1-10. Each Schedule K DETAIL grouping (lines 11, 13a-e, 14a-c, 15a-f, 17a-f, 18a-c, 19a-b, "
                 "20a-c) COLLAPSES into a single coded K-1 box (11, 13, 14, 15, 17, 18, 19, 20) where a letter "
                 "code (A-ZZ) identifies the item. The one real difference: Sch K line 16 → Schedule K-2 "
                 "(entity intl detail); K-1 box 16 → Schedule K-3-attached checkbox (partner copy). Reconcile "
                 "against tts compute_schedule_k1 box consumers (D-1). Full code lists = the K-1 leg."),
     "inputs": [], "outputs": [],
     "description": "i1065 K → K-1 correspondence. Routing spec for the K-1 leg; reconcile target."},
    {"rule_id": "R-SCHK-K2K3", "title": "Line 16 international → Schedule K-2/K-3 (RED-DEFER)", "rule_type": "routing",
     "precedence": 7, "sort_order": 7,
     "formula": ("Post-2021, all international line detail moved OFF Schedule K line 16 onto Schedules K-2 "
                 "(entity) and K-3 (partner). Schedule K line 16 / K-1 box 16 is now only a 'Schedule K-3 is "
                 "attached if checked' checkbox. SCOPE (Ken Decision A, 2026-07-04): K-2/K-3 line detail is "
                 "RED-DEFERRED — out of season-one scope. When k_16_k3_attached is true, D_SCHK_K3 (error/RED) "
                 "flags that the K-2/K-3 international detail must be handled outside the studio this season."),
     "inputs": ["k_16_k3_attached"], "outputs": [],
     "description": "f1065 Sch K line 16 checkbox. Decision A RED-defer."},
    {"rule_id": "R-SCHK-14A", "title": "Line 14a self-employment = the 1065_SE spec (cross-ref, do not recompute)",
     "rule_type": "routing", "precedence": 8, "sort_order": 8,
     "formula": ("Schedule K line 14a (net earnings/loss from self-employment) is fully governed by the "
                 "1065_SE spec (the i1065 2025 p.45 SE Worksheet + the §1402(a)(13) functional-analysis "
                 "classification). This spine carries k_14a_se_earnings as an input only and does NOT "
                 "recompute it — the derivation, per-partner box 14a, and RECON-14A live in 1065_SE. "
                 "14b/14c (gross farming/nonfarm) remain out of compute scope (1065_SE §14.4)."),
     "inputs": ["k_14a_se_earnings"], "outputs": [],
     "description": "Cross-reference to the 1065_SE spec (already seeded/exported). No duplication."},
    {"rule_id": "R-SCHK-9C", "title": "Line 9c unrecaptured §1250 gain ← Form 4797 (K-1 box 9c pass-through)",
     "rule_type": "routing", "precedence": 9, "sort_order": 9,
     "formula": ("Schedule K line 9c (unrecaptured §1250 gain) carries from the entity 4797 aggregate "
                 "(aggregate_dispositions → K9c; tts fix f23dc54 form-branched 1065 to K9c, not the 1120-S "
                 "K8c). It allocates to each partner's K-1 box 9c via k1_allocator (LT-capital category). "
                 "⚠ The downstream box-9c partner pass-through is the STILL-OPEN tts verification (STATUS "
                 "Next-up) — D_SCHK_9C surfaces line 9c so the allocation is confirmed."),
     "inputs": ["k_9c_unrecap_1250"], "outputs": [],
     "description": "f1065 Sch K line 9c ← 4797. Ties to the open K-1 box 9c pass-through verification."},
    {"rule_id": "R-SCHK-ANALYSIS", "title": "Analysis of Net Income line 1 = (Σ K 1-11) − (Σ 12-13e + 21)",
     "rule_type": "calculation", "precedence": 10, "sort_order": 10,
     "formula": ("Analysis of Net Income (Loss) per Return, line 1 = (combine Schedule K lines 1 through 11) "
                 "− (Schedule K lines 12 through 13e + line 21). i1065 verbatim. This equals Schedule M-1 "
                 "line 9 and Schedule M-2 line 3 (the L/M leg tie-out). RECON-ANALYSIS enforces it."),
     "inputs": ["k_1_ordinary", "k_2_net_rental_re", "k_3c_other_net_rental", "k_4c_gp_total", "k_5_interest",
                "k_6a_ordinary_div", "k_7_royalties", "k_8_net_st_capgain", "k_9a_net_lt_capgain", "k_10_net_1231",
                "k_11_other_income", "k_12_section_179", "k_13a_contributions", "k_13b_invest_interest",
                "k_13c_section_59e2", "k_13e_other_deductions", "k_21_foreign_taxes"],
     "outputs": ["k_analysis_net_income"],
     "description": "i1065 Analysis of Net Income line 1. Ties to M-1 line 9 / M-2 line 3."},
    {"rule_id": "R-SCHK-OBBBA", "title": "OBBBA coded items — §181 (13e code X), §1062 (20c code ZZ) (flag)",
     "rule_type": "conditional", "precedence": 11, "sort_order": 11,
     "formula": ("OBBBA (P.L. 119-21) 2025 coded distributive-share items: §181 qualified sound-recording "
                 "production costs elected as an expense → Schedule K/K-1 line 13e code X (productions "
                 "commencing after 7/4/2025, before 2026); §1062 gain on sale of qualified farmland to a "
                 "qualified farmer with a 4-installment election → line 20c code ZZ. Flagged for the K-1 "
                 "coded-box leg; carried in k_13e_other_deductions / k_20_other_information."),
     "inputs": ["k_13e_other_deductions", "k_20_other_information"], "outputs": [],
     "description": "i1065 2025 What's New (OBBBA). Coded-item detail is the K-1 leg."},
]

SCHK_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-SCHK-1", "IRC_702", "primary", "§702(a)(8) residual trade-or-business distributive share → Sch K line 1"),
    ("R-SCHK-1", "IRS_2025_F1065", "primary", "f1065 Sch K line 1 = page-1 line 23"),
    ("R-SCHK-3C", "IRS_2025_F1065", "primary", "f1065 Sch K line 3c = 3a − 3b"),
    ("R-SCHK-4C", "IRC_707C", "primary", "§707(c) guaranteed payments for services + capital"),
    ("R-SCHK-4C", "IRS_2025_F1065", "primary", "f1065 Sch K line 4c = 4a + 4b"),
    ("R-SCHK-SEPARATE", "IRC_702", "primary", "§702(a) separately-stated items; §702(b) character conduit"),
    ("R-SCHK-SEPARATE", "IRC_703", "primary", "§703(a)(1) separately stated; §703(a)(2) entity-disallowed deductions"),
    ("R-SCHK-ALLOC", "IRC_704", "primary", "§704(a) agreement controls; §704(b) partner's-interest fallback; §704(c)"),
    ("R-SCHK-ALLOC", "IRS_2025_I1065", "secondary", "i1065 allocation mechanics + §706(d) varying interest"),
    ("R-SCHK-KMAP", "IRS_2025_I1065", "primary", "i1065 K → K-1 correspondence (1:1 vs coded-collapse; box 16 → K-3)"),
    ("R-SCHK-K2K3", "IRS_2025_F1065", "primary", "f1065 Sch K line 16 = Schedule K-3-attached checkbox"),
    ("R-SCHK-14A", "IRS_2025_F1065", "secondary", "f1065 Sch K line 14a (governed by the 1065_SE spec)"),
    ("R-SCHK-9C", "IRS_2025_F1065", "primary", "f1065 Sch K line 9c unrecaptured §1250 gain"),
    ("R-SCHK-ANALYSIS", "IRS_2025_I1065", "primary", "i1065 Analysis of Net Income (Loss) line 1 formula"),
    ("R-SCHK-OBBBA", "IRS_2025_I1065", "primary", "i1065 2025 What's New — §181 code X, §1062 code ZZ"),
]

SCHK_LINES: list[dict] = [
    {"line_number": "1", "description": "Ordinary business income (loss) (← page-1 line 23)", "line_type": "calculated",
     "sort_order": 1, "source_facts": ["k_1_ordinary"], "source_rules": ["R-SCHK-1"]},
    {"line_number": "2", "description": "Net rental real estate income (loss) (attach Form 8825)",
     "line_type": "calculated", "sort_order": 2, "source_facts": ["k_2_net_rental_re"]},
    {"line_number": "3a", "description": "Other gross rental income (loss)", "line_type": "input", "sort_order": 3,
     "source_facts": ["k_3a_other_gross_rental"]},
    {"line_number": "3b", "description": "Expenses from other rental activities", "line_type": "input", "sort_order": 4,
     "source_facts": ["k_3b_other_rental_exp"]},
    {"line_number": "3c", "description": "Other net rental income (loss) (3a − 3b)", "line_type": "subtotal",
     "sort_order": 5, "source_rules": ["R-SCHK-3C"]},
    {"line_number": "4a", "description": "Guaranteed payments for services", "line_type": "input", "sort_order": 6,
     "source_facts": ["k_4a_gp_services"]},
    {"line_number": "4b", "description": "Guaranteed payments for capital", "line_type": "input", "sort_order": 7,
     "source_facts": ["k_4b_gp_capital"]},
    {"line_number": "4c", "description": "Total guaranteed payments (4a + 4b)", "line_type": "subtotal", "sort_order": 8,
     "source_rules": ["R-SCHK-4C"]},
    {"line_number": "5", "description": "Interest income", "line_type": "input", "sort_order": 9,
     "source_facts": ["k_5_interest"]},
    {"line_number": "6a", "description": "Ordinary dividends", "line_type": "input", "sort_order": 10,
     "source_facts": ["k_6a_ordinary_div"]},
    {"line_number": "6b", "description": "Qualified dividends", "line_type": "input", "sort_order": 11,
     "source_facts": ["k_6b_qualified_div"]},
    {"line_number": "6c", "description": "Dividend equivalents", "line_type": "input", "sort_order": 12,
     "source_facts": ["k_6c_dividend_equiv"]},
    {"line_number": "7", "description": "Royalties", "line_type": "input", "sort_order": 13,
     "source_facts": ["k_7_royalties"]},
    {"line_number": "8", "description": "Net short-term capital gain (loss) (attach Schedule D)", "line_type": "calculated",
     "sort_order": 14, "source_facts": ["k_8_net_st_capgain"]},
    {"line_number": "9a", "description": "Net long-term capital gain (loss) (attach Schedule D)", "line_type": "calculated",
     "sort_order": 15, "source_facts": ["k_9a_net_lt_capgain"]},
    {"line_number": "9b", "description": "Collectibles (28%) gain (loss)", "line_type": "input", "sort_order": 16,
     "source_facts": ["k_9b_collectibles_28"]},
    {"line_number": "9c", "description": "Unrecaptured section 1250 gain (← Form 4797)", "line_type": "calculated",
     "sort_order": 17, "source_facts": ["k_9c_unrecap_1250"], "source_rules": ["R-SCHK-9C"]},
    {"line_number": "10", "description": "Net section 1231 gain (loss) (attach Form 4797)", "line_type": "calculated",
     "sort_order": 18, "source_facts": ["k_10_net_1231"]},
    {"line_number": "11", "description": "Other income (loss) (coded)", "line_type": "input", "sort_order": 19,
     "source_facts": ["k_11_other_income"]},
    {"line_number": "12", "description": "Section 179 deduction (attach Form 4562)", "line_type": "calculated",
     "sort_order": 20, "source_facts": ["k_12_section_179"]},
    {"line_number": "13a", "description": "Contributions (charitable)", "line_type": "input", "sort_order": 21,
     "source_facts": ["k_13a_contributions"]},
    {"line_number": "13b", "description": "Investment interest expense", "line_type": "input", "sort_order": 22,
     "source_facts": ["k_13b_invest_interest"]},
    {"line_number": "13c", "description": "Section 59(e)(2) expenditures", "line_type": "input", "sort_order": 23,
     "source_facts": ["k_13c_section_59e2"]},
    {"line_number": "13e", "description": "Other deductions (coded; OBBBA §181 code X)", "line_type": "input",
     "sort_order": 24, "source_facts": ["k_13e_other_deductions"], "source_rules": ["R-SCHK-OBBBA"]},
    {"line_number": "14a", "description": "Net earnings (loss) from self-employment (= 1065_SE spec)",
     "line_type": "calculated", "sort_order": 25, "source_facts": ["k_14a_se_earnings"], "source_rules": ["R-SCHK-14A"]},
    {"line_number": "14b", "description": "Gross farming or fishing income", "line_type": "input", "sort_order": 26,
     "source_facts": ["k_14b_gross_farming"]},
    {"line_number": "14c", "description": "Gross nonfarm income", "line_type": "input", "sort_order": 27,
     "source_facts": ["k_14c_gross_nonfarm"]},
    {"line_number": "15", "description": "Credits (coded; S3/S4 pass-through)", "line_type": "input", "sort_order": 28,
     "source_facts": ["k_15_credits"]},
    {"line_number": "16", "description": "Schedule K-3 is attached (checkbox) — international (K-2/K-3, RED-defer)",
     "line_type": "input", "sort_order": 29, "source_facts": ["k_16_k3_attached"], "source_rules": ["R-SCHK-K2K3"]},
    {"line_number": "17", "description": "Alternative minimum tax (AMT) items (coded)", "line_type": "input",
     "sort_order": 30, "source_facts": ["k_17_amt_items"]},
    {"line_number": "18a", "description": "Tax-exempt interest income", "line_type": "input", "sort_order": 31,
     "source_facts": ["k_18a_taxexempt_interest"]},
    {"line_number": "18b", "description": "Other tax-exempt income", "line_type": "input", "sort_order": 32,
     "source_facts": ["k_18b_other_taxexempt"]},
    {"line_number": "18c", "description": "Nondeductible expenses", "line_type": "input", "sort_order": 33,
     "source_facts": ["k_18c_nondeductible"]},
    {"line_number": "19a", "description": "Distributions of cash and marketable securities", "line_type": "input",
     "sort_order": 34, "source_facts": ["k_19a_distributions_cash"]},
    {"line_number": "19b", "description": "Distributions of other property", "line_type": "input", "sort_order": 35,
     "source_facts": ["k_19b_distributions_property"]},
    {"line_number": "20", "description": "Other information (coded; §199A code Z, OBBBA §1062 code ZZ)",
     "line_type": "input", "sort_order": 36, "source_facts": ["k_20_other_information"], "source_rules": ["R-SCHK-OBBBA"]},
    {"line_number": "21", "description": "Total foreign taxes paid or accrued", "line_type": "input", "sort_order": 37,
     "source_facts": ["k_21_foreign_taxes"]},
    {"line_number": "Analysis-1", "description": "Analysis of Net Income (Loss) per Return, line 1 "
                                                 "((Σ lines 1-11) − (Σ 12-13e + 21))",
     "line_type": "total", "sort_order": 40, "source_rules": ["R-SCHK-ANALYSIS"],
     "notes": "= Schedule M-1 line 9 / M-2 line 3 (the L/M leg tie-out)."},
]

SCHK_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_SCHK_HANDOFF", "title": "Schedule K line 1 ≠ page-1 line 23", "severity": "error",
     "condition": "k_1_ordinary != 1065_PAGE1.p1_23_ordinary_business_income",
     "message": ("Schedule K line 1 (ordinary business income) must equal Form 1065 page-1 line 23. This is "
                 "the entity→K handoff (§702(a)(8)); a break means the ordinary income didn't carry. "
                 "Recheck the page-1 line 23 computation and the pull to Schedule K line 1."),
     "notes": "Backs RECON-P1-K1. The single load-bearing tie between the two forms this leg seeds."},
    {"diagnostic_id": "D_SCHK_K3", "title": "Schedule K-3 attached — international detail is OUT of season-one scope",
     "severity": "error",
     "condition": "k_16_k3_attached is True",
     "message": ("This partnership has international items requiring Schedules K-2/K-3 (line 16 checked). "
                 "Schedules K-2/K-3 are NOT modeled in season one (RED-DEFER, Ken 2026-07-04). The "
                 "international line detail must be prepared outside the Rule Studio for this filing. Only "
                 "the K-3-attached checkbox is captured here."),
     "notes": "Decision A RED-defer. A hard flag so the scope boundary is explicit, not silent."},
    {"diagnostic_id": "D_SCHK_704C", "title": "§704(c) / special allocation — per-partner math deferred to k1_allocator",
     "severity": "warning",
     "condition": "k_has_704c_property is True OR k_has_special_alloc is True",
     "message": ("This partnership has contributed built-in-gain property (§704(c), K-1 item M) and/or a "
                 "special allocation not pro-rata by interest. Per season-one scope (Ken 2026-07-04), the "
                 "special-allocation MATH is handled by the tts k1_allocator, not the Rule Studio spine — "
                 "confirm the allocation engine models this case (§704(b) substantial economic effect / "
                 "§704(c) reasonable method). Reconcile what it handles vs. RED-defer (D-1)."),
     "notes": "Decision C. Surfaces the item M/N case for the K-1 leg's allocation reconcile."},
    {"diagnostic_id": "D_SCHK_9C", "title": "Unrecaptured §1250 gain present — confirm K-1 box 9c pass-through",
     "severity": "info",
     "condition": "k_9c_unrecap_1250 != 0",
     "message": ("Schedule K line 9c (unrecaptured §1250 gain) is non-zero. It carries from the entity 4797 "
                 "aggregate (tts fix f23dc54: 1065 → K9c) and must allocate to each partner's K-1 box 9c via "
                 "k1_allocator (LT-capital category). The downstream box-9c pass-through is the still-open "
                 "tts verification (STATUS Next-up) — confirm each partner's box 9c and that Σ = line 9c."),
     "notes": "Ties the spine to the open K-1 box 9c pass-through verification (STATUS Next-up item)."},
]

SCHK_SCENARIOS: list[dict] = [
    {"scenario_name": "K-1 — handoff: line 1 = page-1 line 23", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"k_1_ordinary": 220000, "p1_23_ordinary_business_income": 220000},
     "expected_outputs": {"k_1_ordinary": 220000},
     "notes": "RECON-P1-K1: Sch K line 1 carries page-1 line 23 (220k from scenario P1-1). No break."},
    {"scenario_name": "K-2 — other net rental 3c = 3a − 3b", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"k_3a_other_gross_rental": 50000, "k_3b_other_rental_exp": 18000},
     "expected_outputs": {"k_3c_other_net_rental": 32000},
     "notes": "3c = 50k − 18k = 32k (feeds the 1065_SE base worksheet 1c)."},
    {"scenario_name": "K-3 — total guaranteed payments 4c = 4a + 4b", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"k_4a_gp_services": 60000, "k_4b_gp_capital": 15000},
     "expected_outputs": {"k_4c_gp_total": 75000},
     "notes": "4c = 60k services + 15k capital = 75k (ties to page-1 line 10; §707(c))."},
    {"scenario_name": "K-4 — Analysis of Net Income line 1 = (Σ 1-11) − (Σ 12-13e + 21)", "scenario_type": "normal",
     "sort_order": 4,
     "inputs": {"k_1_ordinary": 220000, "k_2_net_rental_re": 10000, "k_5_interest": 5000, "k_7_royalties": 3000,
                "k_9a_net_lt_capgain": 12000, "k_12_section_179": 25000, "k_13a_contributions": 8000,
                "k_21_foreign_taxes": 2000},
     "expected_outputs": {"k_analysis_net_income": 215000},
     "notes": "(220k+10k+5k+3k+12k = 250k lines 1-11) − (25k+8k+2k = 35k lines 12-13e+21) = 215k. = M-1 line 9."},
    {"scenario_name": "K-5 — Schedule K-3 attached → RED-defer fires", "scenario_type": "edge", "sort_order": 5,
     "inputs": {"k_16_k3_attached": True, "k_1_ordinary": 100000},
     "expected_outputs": {"D_SCHK_K3": True},
     "notes": "Decision A: line 16 checked → D_SCHK_K3 (error/RED). K-2/K-3 detail out of season-one scope."},
    {"scenario_name": "K-6 — §704(c) contributed property → allocation deferred", "scenario_type": "edge",
     "sort_order": 6,
     "inputs": {"k_has_704c_property": True, "k_1_ordinary": 100000},
     "expected_outputs": {"D_SCHK_704C": True},
     "notes": "Decision C: item M present → D_SCHK_704C (warning). Special-allocation math deferred to k1_allocator."},
    {"scenario_name": "K-7 — unrecaptured §1250 gain → box 9c pass-through flag", "scenario_type": "edge",
     "sort_order": 7,
     "inputs": {"k_9c_unrecap_1250": 80000},
     "expected_outputs": {"D_SCHK_9C": True},
     "notes": "Line 9c = 80k (the C1 shape from the open verification) → D_SCHK_9C (info): confirm K-1 box 9c "
              "allocation (48k/32k at 60/40) sums back to 80k."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS (cross-form + intra-form invariants)
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "RECON-P1-K1", "assertion_type": "reconciliation", "entity_types": ["1065"], "status": "active",
     "title": "Schedule K line 1 = Form 1065 page-1 line 23 (ordinary business income handoff)",
     "description": ("The entity→K handoff: Schedule K line 1 (ordinary business income) must equal Form 1065 "
                     "page-1 line 23 (= line 8 total income − line 22 total deductions). §702(a)(8). A break "
                     "fires D_SCHK_HANDOFF."),
     "definition": {"kind": "reconciliation", "form": "SCH_K_1065",
                    "formula": "SCH_K_1065.k_1_ordinary == 1065_PAGE1.p1_23_ordinary_business_income",
                    "note": "the single load-bearing tie between the two forms this leg seeds"},
     "bug_reference": "", "sort_order": 1},
    {"assertion_id": "RECON-ANALYSIS", "assertion_type": "reconciliation", "entity_types": ["1065"], "status": "active",
     "title": "Analysis of Net Income line 1 = (Σ Sch K 1-11) − (Σ 12-13e + 21)",
     "description": ("Analysis of Net Income (Loss) per Return line 1 = combine Schedule K lines 1-11, minus "
                     "(lines 12-13e + line 21). i1065 verbatim. Equals Schedule M-1 line 9 / M-2 line 3 — the "
                     "tie-out the L/M leg depends on. A break fires (Analysis miscomputed)."),
     "definition": {"kind": "reconciliation", "form": "SCH_K_1065",
                    "formula": "k_analysis_net_income == (sum(lines 1-11)) - (sum(lines 12-13e) + line 21)",
                    "note": "ties to M-1 line 9 / M-2 line 3 (L/M leg)"},
     "bug_reference": "", "sort_order": 2},
    {"assertion_id": "INV-K-CHARACTER", "assertion_type": "table_invariant", "entity_types": ["1065"],
     "status": "active",
     "title": "Separately-stated Schedule K items retain partnership-level character (§702(b))",
     "description": ("Table invariant: the §702(a)(1)-(7) separately-stated items (Sch K lines 2-21) are pulled "
                     "OFF page-1 ordinary income and each keeps its partnership-level character (§702(b)) — "
                     "they are never folded into line 1. Catches an item being double-counted in both line 1 "
                     "and its separate Schedule K line."),
     "definition": {"kind": "table_invariant", "form": "SCH_K_1065",
                    "invariant": "Sch K lines 2-21 are disjoint from line 1 (no separately-stated item is also "
                                 "in ordinary business income)"},
     "bug_reference": "", "sort_order": 3},
    {"assertion_id": "GATE-K2K3-DEFER", "assertion_type": "gating_check", "entity_types": ["1065"], "status": "active",
     "title": "Line 16 Schedule K-3 checkbox → RED-defer gate (K-2/K-3 out of season-one scope)",
     "description": ("Season-one scope gate (Ken Decision A, 2026-07-04): when Schedule K line 16 (K-3 "
                     "attached) is checked, the international K-2/K-3 line detail is RED-deferred — D_SCHK_K3 "
                     "must fire. The studio captures only the checkbox, not the international detail."),
     "definition": {"kind": "gating_check", "form": "SCH_K_1065", "expect": {"red_fires": True},
                    "when": "k_16_k3_attached is True", "note": "Decision A RED-defer boundary"},
     "bug_reference": "", "sort_order": 4},
]


class Command(BaseCommand):
    help = ("Load the 1065-core SPINE: Form 1065 page 1 (ordinary business income) + Schedule K "
            "(distributive share) + Analysis of Net Income. Fresh-authored from the 1065_core_source_brief "
            "(FINAL 2025 f1065/i1065 verbatim) + primary IRC. Refuses until READY_TO_SEED=True (awaits the "
            "Ken walk + tts reconcile per D-1).")

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING(
            "\nLoad 1065 core SPINE (1065_PAGE1 + SCH_K_1065)\n"))
        self._load_topics()
        sources = self._load_sources()
        # ── Form 1: 1065_PAGE1 ──
        p1 = self._upsert_form(PAGE1_IDENTITY)
        self._upsert_facts(p1, PAGE1_FACTS)
        p1_rules = self._upsert_rules(p1, PAGE1_RULES)
        self._upsert_authority_links(p1_rules, sources, PAGE1_RULE_LINKS)
        self._upsert_lines(p1, PAGE1_LINES)
        self._upsert_diagnostics(p1, PAGE1_DIAGNOSTICS)
        self._upsert_tests(p1, PAGE1_SCENARIOS)
        # ── Form 2: SCH_K_1065 ──
        k = self._upsert_form(SCHK_IDENTITY)
        self._upsert_facts(k, SCHK_FACTS)
        k_rules = self._upsert_rules(k, SCHK_RULES)
        self._upsert_authority_links(k_rules, sources, SCHK_RULE_LINKS)
        self._upsert_lines(k, SCHK_LINES)
        self._upsert_diagnostics(k, SCHK_DIAGNOSTICS)
        self._upsert_tests(k, SCHK_SCENARIOS)
        # ── shared ──
        self._upsert_form_links(sources)
        self._load_flow_assertions()
        self._report_totals([p1, k])

    def _guard_against_hollow_seed(self):
        empty = []
        checks = (
            ("sources", AUTHORITY_SOURCES),
            ("page1.facts", PAGE1_FACTS), ("page1.rules", PAGE1_RULES), ("page1.lines", PAGE1_LINES),
            ("page1.diagnostics", PAGE1_DIAGNOSTICS), ("page1.scenarios", PAGE1_SCENARIOS),
            ("page1.rule_links", PAGE1_RULE_LINKS),
            ("schk.facts", SCHK_FACTS), ("schk.rules", SCHK_RULES), ("schk.lines", SCHK_LINES),
            ("schk.diagnostics", SCHK_DIAGNOSTICS), ("schk.scenarios", SCHK_SCENARIOS),
            ("schk.rule_links", SCHK_RULE_LINKS),
            ("flow_assertions", FLOW_ASSERTIONS),
        )
        for name, seq in checks:
            if not seq:
                empty.append(f"1065_spine.{name}")
        if not READY_TO_SEED or empty:
            still_empty = "\n  ".join(f"- {n}" for n in empty) or "(all populated)"
            raise CommandError(
                "\nREFUSING TO SEED 1065 spine: not cleared to seed.\n\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True — flip only after the Ken walk + tts reconcile, D-1)\n\n"
                f"Currently empty / placeholder:\n  {still_empty}\n"
            )

    def _load_topics(self):
        ct = 0
        for code, name in AUTHORITY_TOPICS:
            _, created = AuthorityTopic.objects.update_or_create(topic_code=code, defaults={"topic_name": name})
            ct += 1 if created else 0
        self.stdout.write(f"Topics: {ct} new ({len(AUTHORITY_TOPICS)} in batch)")

    def _load_sources(self) -> dict:
        sources: dict = {}
        for src_data in AUTHORITY_SOURCES:
            src_data = dict(src_data)
            excerpts_data = src_data.pop("excerpts", [])
            topic_codes = src_data.pop("topics", [])
            source, _ = AuthoritySource.objects.update_or_create(
                source_code=src_data["source_code"], defaults=src_data)
            sources[source.source_code] = source
            for exc in excerpts_data:
                exc = dict(exc)
                AuthorityExcerpt.objects.update_or_create(
                    authority_source=source, excerpt_label=exc["excerpt_label"], defaults=exc)
            for tc in topic_codes:
                topic = AuthorityTopic.objects.filter(topic_code=tc).first()
                if topic:
                    AuthoritySourceTopic.objects.get_or_create(authority_source=source, authority_topic=topic)
        # Existing sources authored elsewhere (IRC_274 via load_all_federal; PUB463 via
        # load_1120s_full — run that loader first so the meals rule links resolve).
        for code in ("IRC_274", "IRS_2025_PUB463"):
            src = AuthoritySource.objects.filter(source_code=code).first()
            if src:
                sources[code] = src
        self.stdout.write(f"Sources ready: {len(sources)}")
        return sources

    def _upsert_form(self, identity: dict) -> TaxForm:
        form, created = TaxForm.objects.update_or_create(
            form_number=identity["form_number"], jurisdiction=FORM_JURISDICTION,
            tax_year=FORM_TAX_YEAR, version=FORM_VERSION,
            defaults={"form_title": identity["form_title"], "entity_types": identity["entity_types"],
                      "status": FORM_STATUS, "notes": identity["notes"]})
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
                    defaults={"support_level": level, "relevance_note": note})
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
                    defaults={"note": f"{source_code} -> {form_code}"})

    def _load_flow_assertions(self):
        for a in FLOW_ASSERTIONS:
            a = dict(a)
            FlowAssertion.objects.update_or_create(assertion_id=a.pop("assertion_id"), defaults=a)
        self.stdout.write(f"  {len(FLOW_ASSERTIONS)} flow assertions")

    def _report_totals(self, forms):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(f"TaxForms: {TaxForm.objects.count()} | FlowAssertions: {FlowAssertion.objects.count()}")
        for form in forms:
            uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
            self.stdout.write(f"{form.form_number}: all rules cited" if not uncited
                              else self.style.WARNING(f"{form.form_number} uncited rules: {len(uncited)}"))
