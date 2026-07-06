"""Load the SC1040 spec — South Carolina Individual Income Tax Return (TY2025).

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
SC1040 is the South Carolina resident / part-year / nonresident individual
income tax return. Unlike GA Form 500 (which starts from federal AGI), SC1040
starts from FEDERAL TAXABLE INCOME (federal 1040 line 15), applies SC
additions (a-e) and subtractions (f-w), reaches "SC income subject to tax"
(line 5), a 3-bracket tax (0/3/6%), nonrefundable credits, then refundable
credits/payments → refund or balance due. Part-year/nonresident filers build
line 5 from Schedule NR (the SC-source proration).

This is the 2nd STATE individual spec (GA Form 500 is the first;
load_ga500_form_500.py is the structural precedent). It attaches to the child
1040 return in tts-tax-app via TaxReturn.federal_return / state_returns (the
GA-600S / GA-500 precedent).

NO prior RS spec exists (lookup/SC1040/, SC_1040 → 404). NEW form.

═══════════════════════════════════════════════════════════════════════════
v1 SCOPE — LOCKED (Ken's walk 2026-07-04, 4 AskUserQuestion decisions; MAXIMAL)
See DECISIONS.md D-6 + sc1040_source_brief.md §9.
═══════════════════════════════════════════════════════════════════════════
COMPUTES (v1):
  • Full-year RESIDENT main form (SC1040 lines 1-34).
  • PART-YEAR / NONRESIDENT — Schedule NR (2-money-column A federal / B SC;
    line 45 proration = L31 Col B ÷ L31 Col A; line 48 → SC1040 line 5).   [Dec A]
  • 3-bracket tax (L6): 0% ≤ $3,560 / 3% to $17,830 / 6% above; ≥$100k uses
    the rate schedule (6% × L5 − $642).
  • The §168(k) BONUS-DEPRECIATION ADD-BACK (line e) — COMPUTED: placed-in-
    service-year add-back = federal depreciation − depreciation-without-bonus;
    the SC subtraction in later years (line v) as SC basis exceeds federal;
    disposition basis-difference adjustment. SC conforms to the IRC as amended
    through 12/31/2024 and did NOT adopt OBBBA.                              [Dec B]
  • The RETIREMENT / MILITARY / AGE-65 deduction stack (the interacting
    reductions): retirement $3,000 (<65) / $10,000 (65+) per taxpayer;
    military retirement 100%; age-65 $15,000 reduced by the retirement +
    military deductions already taken.                                       [Dec C]
  • 44% net long-term capital gain deduction (line i); Social Security fully
    exempt (line o); SC dependent exemption $4,930 × deps (line w) + under-6
    $4,930 × (line t); Child & Dependent Care (L11, 7% of federal 2441, max
    $210/$420); Two Wage Earner credit (L12, 0.7% × lesser($50,000, lower-earner
    SC earned income), max $350); withholding/payments → refund/balance.

DIRECT-ENTRY (line exists, diagnostic prompts, preparer keys the figure):
  • SC1040TC other nonrefundable credits (L13); tuition credit inputs (L21,
    I-319 refundable); niche a-e additions / f-w subtractions not modeled.   [Dec D]

RED-DEFERS (each its own "prepare manually" RED — no silent gap):            [Dec D]
  • Active Trade or Business Income 3% election (I-335; L8 tax + line-l
    deduction) — D_SC1040_ATB.
  • Lump-Sum Distribution tax (SC4972; L7) — D_SC1040_LUMPSUM.
  • Catastrophe Savings Account excess-withdrawal tax (L9) — D_SC1040_CATSAV.
  • SC2210 underpayment penalty (L33) — D_SC1040_SC2210.

═══════════════════════════════════════════════════════════════════════════
requires_human_review WALK ITEMS (for Ken's in-session review before seeding)
═══════════════════════════════════════════════════════════════════════════
W1. §179 CONFORMITY — RESOLVED 2026-07-04 (Ken confirmed the figure). §179 is
    NOT on SC's non-adopted list (§12-6-50 excludes only §168(k), §163(j),
    §199A), so SC conforms to §179 AT THE 12/31/2024 IRC LEVEL — the PRE-OBBBA
    limit $1,250,000 / phaseout $3,130,000 (Rev. Proc. 2024-40), NOT OBBBA's
    $2,500,000/$4,000,000. Ken (depreciation CPA) confirmed these figures and
    chose COMPUTE: the §179-excess add-back is now computed on line e by
    R-SC-179-ADDBACK (SC_179_LIMIT / SC_179_PHASEOUT constants), recovered via SC
    depreciation over the asset life. Business-income limit not modeled (noted).
    (SC's own regime: SC_179 = $1,250,000/$3,130,000, conformity 12/31/2024 — SC did
    NOT adopt OBBBA §179. Do NOT cross-apply the federal/GA $2.5M figure; GA now
    conforms to OBBBA §179 via HB 1199 but SC does not.)
W2. BRACKET THRESHOLDS. The $3,560 / $17,830 dollar breakpoints are corroborated
    by the primary SC1040TT table + the $642 rate-schedule constant, but were
    not printed as round numbers in a DOR PDF (a third-party site supplied the
    exact figures). The 6% top rate + $642 constant ARE primary-verified.
    CONFIRM the thresholds vs SC Code §12-6-510 (inflation-indexed) before lock.
W3. TUITION CREDIT (L21). 50% / max $1,500 / ≤4 yrs / refundable is from SC
    Revenue Ruling 24-3 + the DOR web page, NOT the 2025 SC1040 instructions
    (which route to I-319) — and the 2025 I-319 PDF was not fetched. v1 takes
    L21 as DIRECT-ENTRY; CONFIRM the cap on the final I-319_2025 if it is ever
    computed.
W4. FEDERAL LINE FOR L1. DOR says "your federal form," does not print "line 15."
    L1 ← federal 1040 taxable income (2025 layout = line 15). CONFIRM the tts
    federal handoff pulls taxable income, not AGI.
W5. OBBBA MID-CHANGE RISK. SC did NOT adopt OBBBA for TY2025 (conformity date
    12/31/2024; SCTIED 2025 fn.2 confirms). A 2026 SC session could retroactively
    adopt parts — re-verify next season. A possible SC DOR information letter
    (~1/30/2026) on OBBBA non-conformity was referenced by a secondary source but
    not verified; pull it if it exists (would be the authoritative TY2025 cite).

═══════════════════════════════════════════════════════════════════════════
VERIFIED STRUCTURE + CONSTANTS (READ 2026-07-04 from the FINAL 2025 SC DOR PDFs
via two research passes — NOT memory: SC1040 Rev. 4/21/25; SC1040TT Rev.
6/17/25; SC1040 Instructions ~Aug 2025; Schedule NR Rev. 4/2/25 + instr. Jul
2025; Act 63/S.507 signed 5/22/2025; SCTIED 2025 Ch.2; RR#05-2. Full source
brief: sc1040_source_brief.md.)
═══════════════════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════════════════
SAFETY GUARD — READY_TO_SEED stays False until Ken approves the review walk
(W1-W5) in-session. Until then the command refuses to write to the DB.
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
# SAFETY GUARD — flip ONLY after Ken's in-session review walk (W1-W5 above).
#
# FLIPPED 2026-07-04 — Ken APPROVED the review walk in-session ("seed + export
# now"): W1 §179 conformity RESOLVED (confirmed $1,250,000/$3,130,000 pre-OBBBA,
# COMPUTE via R-SC-179-ADDBACK); W2 bracket thresholds $3,560/$17,830, W3 tuition
# cap, W4 the federal-taxable-income handoff, W5 OBBBA non-adoption re-verify —
# all blessed to proceed as in-spec re-verify flags. Validated on a throwaway DB.
# ═══════════════════════════════════════════════════════════════════════════
READY_TO_SEED = True


FORM_JURISDICTION = "SC"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "active"
FORM_ENTITY_TYPES = ["1040"]


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS (year-keyed; every value cited in the source brief; never
# training memory). Rates as decimal strings (the GA-500 convention).
# ═══════════════════════════════════════════════════════════════════════════

SC_TOP_RATE: dict[int, str] = {2025: "0.06"}              # SC1040TT Rev. 6/17/25 (was 6.4% in 2024)
SC_MIDDLE_RATE: dict[int, str] = {2025: "0.03"}
SC_RATE_SCHED_SUBTRACT: dict[int, int] = {2025: 642}      # ≥$100k: tax = 6% × L5 − $642 (verbatim SC1040TT)
SC_BRACKET_0_TOP: dict[int, int] = {2025: 3560}           # ⚠ W2 — corroborated, re-verify §12-6-510
SC_BRACKET_6_FLOOR: dict[int, int] = {2025: 17830}        # ⚠ W2
SC_CAP_GAIN_DED_PCT: dict[int, str] = {2025: "0.44"}      # 44% net LT capital gain deduction (line i)
SC_RETIREMENT_DED_UNDER65: dict[int, int] = {2025: 3000}  # line p, under 65, per taxpayer
SC_RETIREMENT_DED_65: dict[int, int] = {2025: 10000}      # line p, age 65+, per taxpayer
SC_AGE65_DEDUCTION: dict[int, int] = {2025: 15000}        # line q, per taxpayer 65+, reduced by p + military
SC_DEPENDENT_EXEMPTION: dict[int, int] = {2025: 4930}     # line w, per federal dependent
SC_UNDER6_DEDUCTION: dict[int, int] = {2025: 4930}        # line t, per dependent under age 6 (stacks on w)
SC_CHILDCARE_PCT: dict[int, str] = {2025: "0.07"}         # L11, 7% of federal 2441 expense
SC_CHILDCARE_CAP_1: dict[int, int] = {2025: 210}          # max, 1 dependent
SC_CHILDCARE_CAP_2: dict[int, int] = {2025: 420}          # max, 2+ dependents
SC_TWO_WAGE_PCT: dict[int, str] = {2025: "0.007"}         # L12, 0.7% × lesser($50k, lower-earner SC earned)
SC_TWO_WAGE_BASE_CAP: dict[int, int] = {2025: 50000}      # → max credit $350
SC_TWO_WAGE_MAX: dict[int, int] = {2025: 350}
SC_SALT_ADDBACK_CAP: dict[int, int] = {2025: 40000}       # line a, federal SALT cap referenced ($20k MFS)
SC_TUITION_CREDIT_PCT: dict[int, str] = {2025: "0.50"}    # ⚠ W3 — RR24-3, re-verify I-319_2025
SC_TUITION_CREDIT_CAP: dict[int, int] = {2025: 1500}      # ⚠ W3

# SC IRC conformity (Act 63 / S.507, signed 2025-05-22): "IRC as amended through
# December 31, 2024" → SC did NOT adopt OBBBA (7/4/2025).
SC_CONFORMITY_DATE: str = "2024-12-31"
SC_ADOPTED_OBBBA: bool = False
# §179: SC conforms at the 12/31/2024 (pre-OBBBA) level, NOT OBBBA's $2.5M/$4M.
# W1 RESOLVED 2026-07-04 — Ken confirmed the 2025 pre-OBBBA figures (Rev. Proc.
# 2024-40, adopted by SC's 12/31/2024 conformity): limit $1,250,000 / phaseout
# threshold $3,130,000. The SC §179-excess add-back is COMPUTED on line e (below).
SC_179_LIMIT: dict[int, int] = {2025: 1250000}           # pre-OBBBA 2025 §179 dollar limit (SC conforms)
SC_179_PHASEOUT: dict[int, int] = {2025: 3130000}        # pre-OBBBA 2025 §179 phaseout threshold


def _yk_int(d: dict[int, int], year: int) -> int:
    """Year-keyed int lookup, 2025 fallback (single-year table so far)."""
    return d.get(year) if d.get(year) is not None else d[2025]


def _yk_str(d: dict[int, str], year: int) -> str:
    return d.get(year) if d.get(year) is not None else d[2025]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY TOPICS / SOURCES
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("sc_income_tax", "South Carolina SC1040 individual income tax: federal-taxable-income start, "
     "SC add/subtract, 3-bracket rate, retirement/age-65 stack, §168(k)/§179 decoupling, Schedule NR."),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_1040_FORM",  # L1 ← federal taxable income (1040 L15); federal 2441 for L11; federal net cap gain for line i
]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "SC_2025_FORM_SC1040",
        "source_type": "state_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "SC",
        "title": "2025 SC1040 — Individual Income Tax Return (Rev. 4/21/25)",
        "citation": "South Carolina SC1040 (2025), Rev. 4/21/25, form ID 3075",
        "issuer": "South Carolina Department of Revenue",
        "official_url": "https://dor.sc.gov/sites/dor/files/forms/SC1040_2025.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["sc_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "SC1040 face (2025) — verified line map",
                "excerpt_text": (
                    "L1 Federal taxable income (from your federal form; 0 if <0). Additions a-e → L2 "
                    "total additions; L3 = L1+L2. Subtractions f-w → L4; L5 SOUTH CAROLINA INCOME "
                    "SUBJECT TO TAX = L3−L4 (not <0); nonresident/part-year: L5 ← Schedule NR line 48. "
                    "L6 TAX (SC1040TT); L7 tax on lump-sum (SC4972); L8 tax on active trade/business "
                    "(I-335); L9 tax on excess Catastrophe Savings withdrawals; L10 TOTAL SC TAX "
                    "(6+7+8+9). L11 Child & Dependent Care; L12 Two Wage Earner; L13 other nonref "
                    "(SC1040TC); L14 total nonref; L15 = L10−L14 (not <0). L16 SC withholding; L17 est "
                    "pmts; L18 extension; L19 nonres real-estate (I-290); L20 other wh (1099); L21 "
                    "tuition tax credit (I-319, refundable); L22a-d refundable; L22 total; L23 TOTAL "
                    "PAYMENTS. L24 overpayment; L25 amount due; L26 use tax; L27 to 2026 est; L28 "
                    "check-offs (I-330); L29 total(26-28); L30 REFUND; L31 tax due; L32 late penalties+"
                    "interest; L33 SC2210; L34 BALANCE DUE."
                ),
                "summary_text": "SC1040 (2025) face: federal taxable income → SC add/subtract → L5 SC income → 3-bracket tax → credits → payments → refund/due.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "SC1040 additions a-e (2025)",
                "excerpt_text": (
                    "a State tax addback if itemizing federally (federal SALT cap referenced $40,000 / "
                    "$20,000 MFS); b Out-of-state losses; c Expenses related to National Guard and "
                    "Military Reserve Income; d Interest on obligations of states/political subdivisions "
                    "other than South Carolina; e Other additions — INCLUDES the IRC §168(k) bonus-"
                    "depreciation add-back (difference between federal depreciation and depreciation "
                    "without bonus), SC-larger federal NOL, and accounting-method items."
                ),
                "summary_text": "Additions a-e; line e carries the §168(k) bonus add-back.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "SC1040 key subtractions (2025)",
                "excerpt_text": (
                    "i 44% of net long-term capital gain; o Social Security / railroad retirement "
                    "(fully exempt — subtract the amount taxed federally); p Retirement deduction "
                    "($3,000 under 65 / $10,000 age 65+ per taxpayer on own qualified retirement income; "
                    "p-4/5/6 military retirement 100%, reduces p and q); q Age 65+ deduction $15,000 per "
                    "taxpayer, reduced by the retirement + military deductions already claimed; t "
                    "Dependents under age 6 on Dec 31 = $4,930 each; v later-year additional SC "
                    "depreciation deduction (SC basis > federal after the bonus add-back); w SC "
                    "Dependent Exemption = $4,930 × federal dependents."
                ),
                "summary_text": "Subtractions: 44% cap gain (i), SS (o), retirement/military/age-65 stack (p/q), under-6 (t), dep exemption (w), later-year depreciation (v).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "SC1040 credits L11/L12 (2025)",
                "excerpt_text": (
                    "L11 Child & Dependent Care = 7% of the federal Form 2441 expense, max $210 (1 "
                    "dependent) / $420 (2+); not allowed MFS. L12 Two Wage Earner (MFJ only, both "
                    "spouses SC earned income) = 0.007 × lesser($50,000, lower-earning spouse's SC "
                    "qualified earned income); max $350."
                ),
                "summary_text": "L11 child-care 7% (max $210/$420); L12 two-wage-earner 0.7% (max $350).",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "SC_2025_SC1040TT",
        "source_type": "state_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "SC",
        "title": "2025 South Carolina Individual Income Tax Tables + Rate Schedule (SC1040TT, Rev. 6/17/25)",
        "citation": "SC1040TT (2025), Rev. 6/17/25",
        "issuer": "South Carolina Department of Revenue",
        "official_url": "https://dor.sc.gov/sites/dor/files/forms/SC1040TT_2025.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["sc_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "SC 2025 rate schedule (verbatim)",
                "excerpt_text": (
                    "For taxable income of $100,000 or more: (1) Multiply the amount on SC1040 line 5 by "
                    "6%; (2) Subtract $642 (the rate-schedule constant); (3) Enter the difference on line "
                    "6. Example: $101,000 × 6% = $6,060 − $642 = $5,418. For taxable income under "
                    "$100,000, use the bracketed tax tables. Effective brackets: 0% up to $3,560; 3% from "
                    "$3,561 to $17,830; 6% over $17,830 (all filing statuses). Top rate dropped from 6.4% "
                    "(2024) to 6% (2025) via SC's statutory reduction trigger."
                ),
                "summary_text": "3 brackets 0/3/6% at $3,560/$17,830; ≥$100k: 6%×L5−$642. Top rate 6% for 2025.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "SC_2025_SC1040_INSTR",
        "source_type": "state_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "SC",
        "title": "2025 SC1040 Individual Income Tax Instructions",
        "citation": "SC1040 Instructions (2025), SCDOR (~Aug 2025)",
        "issuer": "South Carolina Department of Revenue",
        "official_url": "https://dor.sc.gov/sites/dor/files/forms/SC1040Instr_2025.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.4,
        "topics": ["sc_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "§168(k) bonus-depreciation decoupling — line e / line v (verbatim)",
                "excerpt_text": (
                    "South Carolina does not recognize bonus depreciation in IRC Section 168(k). With or "
                    "without bonus depreciation, the depreciable life of the property is the same for "
                    "federal and state purposes. For the tax year the property is placed in service, a "
                    "taxpayer must add back, on line e of the SC1040, the difference between the "
                    "depreciation deduction allowed for federal purposes and the deduction that would "
                    "have been allowed without bonus depreciation. The South Carolina adjusted basis will "
                    "then be greater than the federal adjusted basis. For all other years of the "
                    "depreciable life of the property, an additional depreciation deduction is available "
                    "for South Carolina purposes (line v). On disposition, adjust the federal gain or "
                    "loss to reflect the difference in the South Carolina and federal basis."
                ),
                "summary_text": "SC decouples from §168(k): add back bonus in PIS year (line e); extra SC depreciation later (line v); basis-difference on disposition.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Retirement / military / age-65 deduction stack (verbatim rules)",
                "excerpt_text": (
                    "Retirement deduction: up to $3,000 (under 65) or $10,000 (age 65 or older) per "
                    "taxpayer, against that taxpayer's own qualified retirement income; a surviving "
                    "spouse deduction is additional. Military retirement: 100% deductible (no cap); it "
                    "reduces the taxpayer's retirement deduction and the age-65 deduction. Age 65 and "
                    "older deduction: $15,000 per taxpayer age 65+, against any South Carolina income, "
                    "REDUCED by the retirement deduction and military retirement deduction already "
                    "claimed by that taxpayer. Social Security and railroad retirement are fully exempt "
                    "and are not part of the retirement-deduction base."
                ),
                "summary_text": "Retirement $3k/$10k; military 100%; age-65 $15k reduced by retirement + military already taken; SS fully exempt.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "SC_2025_SCHEDULE_NR",
        "source_type": "state_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "SC",
        "title": "2025 SC Schedule NR — Nonresident Schedule (Rev. 4/2/25)",
        "citation": "SC Schedule NR (2025), Rev. 4/2/25",
        "issuer": "South Carolina Department of Revenue",
        "official_url": "https://dor.sc.gov/sites/dor/files/forms/SchNR_2025.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["sc_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "Schedule NR (2025) — columns, proration, line 48 handoff",
                "excerpt_text": (
                    "Two money columns: Column A 'Income as Shown on Federal Return', Column B 'South "
                    "Carolina Income'. Lines 1-16 income; 17-31 adjustments (Col A federal adj / Col B SC "
                    "adj, each line prorated by its own income ratio; 'SC adjustment cannot exceed 100% "
                    "of federal adjustment'); L31 = SC AGI. L32 SC additions (lump); L33-41 SC "
                    "subtractions (33 dependent exemption $4,930×deps; 34 44% cap gain; 35 retirement/"
                    "military; 36 age-65 $15,000 'must be resident for part of the year'; 37 under-6 "
                    "$4,930; 38 Future Scholar; 39 active trade/business; 40 consumer protection; 41 "
                    "other); L42 total subtractions; L43 = L32−L42; L44 SC modified AGI = L31 Col B + "
                    "L43. L45 PRORATION = L31 Col B ÷ L31 Col A (≤100%, 2 decimals). L46 deduction "
                    "(std/itemized, Parts I-IV); L47 = L46 × L45%; L48 SC taxable income = L44 − L47 → "
                    "SC1040 line 5 (0 if negative)."
                ),
                "summary_text": "Schedule NR: Col A federal / Col B SC; L45 ratio prorates ONLY the deduction (L47); L44−L47 = L48 → SC1040 L5.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "SC_ACT63_2025_CONFORMITY",
        "source_type": "state_statute",
        "source_rank": "controlling",
        "jurisdiction_code": "SC",
        "title": "SC Act 63 of 2025 (S.507) — IRC conformity as amended through 12/31/2024",
        "citation": "SC Code §12-6-40(A)(1), as amended by Act 63 of 2025 (S.507), signed 5/22/2025",
        "issuer": "South Carolina General Assembly",
        "official_url": "https://www.scstatehouse.gov/sess126_2025-2026/bills/507.htm",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.6,
        "topics": ["sc_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "SC IRC conformity date + OBBBA non-adoption (verbatim + SCTIED)",
                "excerpt_text": (
                    "§12-6-40(A)(1)(a): 'Internal Revenue Code' means the Internal Revenue Code of 1986, "
                    "as amended through December 31, 2024, and includes the effective date provisions "
                    "contained in it. (c) IRC sections expired 12/31/2024 and extended (not otherwise "
                    "amended) by Congress during 2025 are also extended for SC. Because the conformity "
                    "date (12/31/2024) predates OBBBA (P.L. 119-21, signed 7/4/2025), SC did NOT adopt "
                    "OBBBA for TY2025. SCTIED 2025 Ch.2 fn.2: 'This publication has not been updated to "
                    "discuss federal tax legislation enacted in 2025.' §12-6-50 lists the non-adopted "
                    "IRC sections — including §168(k) bonus depreciation, §163(j), and §199A; §179 is "
                    "NOT on that list (SC conforms to §179 at the 12/31/2024 level, i.e. pre-OBBBA)."
                ),
                "summary_text": "SC conforms to the IRC through 12/31/2024 (Act 63); did NOT adopt OBBBA; §12-6-50 decouples §168(k)/§163(j)/§199A but not §179.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "SC_RR_05_2_DEPR",
        "source_type": "state_regulation",
        "source_rank": "primary_official",
        "jurisdiction_code": "SC",
        "title": "SC Revenue Ruling #05-2 — Bonus Depreciation §168(k) / basis decoupling",
        "citation": "SC Revenue Ruling #05-2 (SC Code §12-6-50(4))",
        "issuer": "South Carolina Department of Revenue",
        "official_url": "https://dor.sc.gov/resources-site/lawandpolicy/Advisory%20Opinions/RR05-2.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.0,
        "topics": ["sc_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "RR #05-2 — separate SC depreciation schedule + disposition basis",
                "excerpt_text": (
                    "A taxpayer claiming bonus depreciation for federal purposes must maintain a separate "
                    "depreciation schedule for South Carolina and adjust the basis of the asset. Upon "
                    "disposition, any gain or loss must be calculated to reflect the difference in the "
                    "federal and South Carolina basis. §12-6-50(4) is the decoupling statute."
                ),
                "summary_text": "RR#05-2: keep a separate SC depreciation schedule; adjust disposition gain/loss for the SC-vs-federal basis difference.",
                "is_key_excerpt": True,
            },
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("SC_2025_FORM_SC1040", "SC1040", "governs"),
    ("SC_2025_SC1040TT", "SC1040", "governs"),
    ("SC_2025_SC1040_INSTR", "SC1040", "governs"),
    ("SC_2025_SCHEDULE_NR", "SC_SCHEDULE_NR", "governs"),
    ("SC_ACT63_2025_CONFORMITY", "SC1040", "governs"),
    ("SC_RR_05_2_DEPR", "SC1040", "informs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 1 — SC1040 (resident main form)
# ═══════════════════════════════════════════════════════════════════════════

SC1040_FACTS: list[dict] = [
    {"fact_key": "federal_taxable_income", "label": "Federal taxable income (1040 line 15)", "data_type": "decimal", "required": True, "sort_order": 1,
     "notes": "SC1040 L1 start. W4: DOR says 'your federal form'; 2025 layout = 1040 line 15. 0 if <0."},
    {"fact_key": "filing_status", "label": "Filing status", "data_type": "choice", "required": True, "sort_order": 2,
     "choices": ["single", "MFJ", "MFS", "HOH", "QSS"]},
    {"fact_key": "is_part_year_or_nonresident", "label": "Part-year or nonresident (files Schedule NR)?", "data_type": "boolean", "required": True, "sort_order": 3,
     "notes": "If True, L5 ← Schedule NR line 48; L1-L4 are bypassed."},
    {"fact_key": "federal_bonus_depreciation", "label": "Federal §168(k) bonus depreciation claimed (this year)", "data_type": "decimal", "required": False, "sort_order": 10},
    {"fact_key": "depreciation_without_bonus", "label": "Depreciation that would be allowed without bonus (SC basis)", "data_type": "decimal", "required": False, "sort_order": 11,
     "notes": "Dec B: SC deduction = regular MACRS on the full (non-bonus-reduced) basis, same recovery period."},
    {"fact_key": "sc_prior_year_bonus_catchup", "label": "Later-year additional SC depreciation (line v subtraction)", "data_type": "decimal", "required": False, "sort_order": 12,
     "notes": "SC basis > federal after the PIS-year add-back → extra SC depreciation in later years."},
    {"fact_key": "federal_179_deducted", "label": "Federal §179 expense deducted (this year)", "data_type": "decimal", "required": False, "sort_order": 13,
     "notes": "W1. Under OBBBA the federal §179 can reach $2.5M; SC's limit is the pre-OBBBA $1.25M."},
    {"fact_key": "section_179_property_total", "label": "Total cost of §179 property placed in service", "data_type": "decimal", "required": False, "sort_order": 14,
     "notes": "Drives the SC §179 phaseout (limit reduced $-for-$ over $3,130,000)."},
    {"fact_key": "state_tax_addback", "label": "State income tax deducted on federal Schedule A (line a)", "data_type": "decimal", "required": False, "sort_order": 13,
     "notes": "Only if itemized federally; federal SALT cap referenced $40,000 / $20,000 MFS."},
    {"fact_key": "other_additions", "label": "Other SC additions (b/c/d and non-modeled line e items)", "data_type": "decimal", "required": False, "sort_order": 14},
    {"fact_key": "net_long_term_capital_gain", "label": "Net long-term capital gain (federal, held >1 yr)", "data_type": "decimal", "required": False, "sort_order": 20},
    {"fact_key": "social_security_taxed_federally", "label": "Social Security / RR retirement taxed on the federal return", "data_type": "decimal", "required": False, "sort_order": 21},
    {"fact_key": "taxpayer_age_65_plus", "label": "Taxpayer is age 65 or older", "data_type": "boolean", "required": False, "sort_order": 22},
    {"fact_key": "spouse_age_65_plus", "label": "Spouse is age 65 or older", "data_type": "boolean", "required": False, "sort_order": 23},
    {"fact_key": "taxpayer_retirement_income", "label": "Taxpayer's own qualified retirement income", "data_type": "decimal", "required": False, "sort_order": 24},
    {"fact_key": "spouse_retirement_income", "label": "Spouse's own qualified retirement income", "data_type": "decimal", "required": False, "sort_order": 25},
    {"fact_key": "taxpayer_military_retirement", "label": "Taxpayer military retirement income (100% deductible)", "data_type": "decimal", "required": False, "sort_order": 26},
    {"fact_key": "spouse_military_retirement", "label": "Spouse military retirement income (100% deductible)", "data_type": "decimal", "required": False, "sort_order": 27},
    {"fact_key": "num_dependents", "label": "Number of federal dependents (dependent exemption)", "data_type": "integer", "required": False, "sort_order": 30},
    {"fact_key": "num_dependents_under_6", "label": "Number of dependents under age 6 on Dec 31", "data_type": "integer", "required": False, "sort_order": 31},
    {"fact_key": "other_subtractions", "label": "Other SC subtractions (f-w items not modeled)", "data_type": "decimal", "required": False, "sort_order": 32},
    {"fact_key": "federal_childcare_expense", "label": "Federal Form 2441 child/dependent-care expense", "data_type": "decimal", "required": False, "sort_order": 40},
    {"fact_key": "num_care_dependents", "label": "Number of dependents for the child-care credit", "data_type": "integer", "required": False, "sort_order": 41},
    {"fact_key": "taxpayer_sc_earned_income", "label": "Taxpayer SC qualified earned income (two-wage-earner)", "data_type": "decimal", "required": False, "sort_order": 42},
    {"fact_key": "spouse_sc_earned_income", "label": "Spouse SC qualified earned income (two-wage-earner)", "data_type": "decimal", "required": False, "sort_order": 43},
    {"fact_key": "other_nonrefundable_credits", "label": "SC1040TC other nonrefundable credits (L13, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 50},
    {"fact_key": "tuition_tax_credit", "label": "Tuition tax credit (L21, I-319, refundable, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 51},
    {"fact_key": "sc_withholding", "label": "SC income tax withheld (W-2/SC41)", "data_type": "decimal", "required": False, "sort_order": 60},
    {"fact_key": "estimated_payments", "label": "2025 SC estimated tax payments", "data_type": "decimal", "required": False, "sort_order": 61},
    {"fact_key": "extension_payment", "label": "Amount paid with SC extension", "data_type": "decimal", "required": False, "sort_order": 62},
    {"fact_key": "other_refundable_credits", "label": "Other refundable credits (L22a-d) + other SC withholding (L20)", "data_type": "decimal", "required": False, "sort_order": 63},
    {"fact_key": "schedule_nr_line48", "label": "Schedule NR line 48 (SC taxable income for PY/NR)", "data_type": "decimal", "required": False, "sort_order": 70,
     "notes": "Dec A: when is_part_year_or_nonresident, L5 ← this."},
]

SC1040_RULES: list[dict] = [
    {"rule_id": "R-SC-DEPR-ADDBACK", "title": "§168(k) bonus-depreciation add-back (line e) — COMPUTED", "rule_type": "calculation",
     "formula": "line_e_depr_addback = max(0, federal_bonus_depreciation - depreciation_without_bonus)",
     "inputs": ["federal_bonus_depreciation", "depreciation_without_bonus"], "outputs": ["line_e_depr_addback"], "sort_order": 10,
     "description": "Dec B. SC does not recognize §168(k); PIS-year add-back = federal depreciation − depreciation without bonus (same recovery period). SC basis then exceeds federal (see line v subtraction + disposition basis adj). Does NOT cover the §179-excess add-back (W1 — direct-entry)."},
    {"rule_id": "R-SC-179-ADDBACK", "title": "§179-excess add-back (line e) — SC conforms at pre-OBBBA $1.25M (W1)", "rule_type": "calculation",
     "formula": ("sc_179_limit = max(0, 1250000 - max(0, section_179_property_total - 3130000)) ; "
                 "sc_179_allowed = min(federal_179_deducted, sc_179_limit) ; "
                 "line_e_179_addback = max(0, federal_179_deducted - sc_179_allowed)"),
     "inputs": ["federal_179_deducted", "section_179_property_total"], "outputs": ["line_e_179_addback"], "sort_order": 10,
     "description": "W1 RESOLVED (Ken confirmed 2026-07-04). SC conforms to §179 at the 12/31/2024 IRC level — limit $1,250,000, phaseout threshold $3,130,000 (Rev. Proc. 2024-40), NOT OBBBA's $2.5M/$4M. Add back federal §179 in excess of the SC-allowed amount on line e; the added-back basis is recovered via SC depreciation over the asset life (line v style). Also subject to the business-income limit (not modeled — note)."},
    {"rule_id": "R-SC-ADDITIONS", "title": "Total additions (L2) and L3", "rule_type": "calculation",
     "formula": "L2 = state_tax_addback + line_e_depr_addback + line_e_179_addback + other_additions ; L3 = L1 + L2",
     "inputs": ["federal_taxable_income", "state_tax_addback", "line_e_depr_addback", "line_e_179_addback", "other_additions"], "outputs": ["L2", "L3"], "sort_order": 11},
    {"rule_id": "R-SC-CAPGAIN", "title": "44% net long-term capital gain deduction (line i)", "rule_type": "calculation",
     "formula": "line_i = 0.44 * max(0, net_long_term_capital_gain)",
     "inputs": ["net_long_term_capital_gain"], "outputs": ["line_i"], "sort_order": 20,
     "description": "44% of net capital gain held >1 year (SC_CAP_GAIN_DED_PCT)."},
    {"rule_id": "R-SC-RETIRE-STACK", "title": "Retirement / military / age-65 deduction stack (interacting)", "rule_type": "calculation",
     "formula": ("per taxpayer: retire_ded = min(own_retirement_income, 10000 if age_65_plus else 3000); "
                 "military_ded = own_military_retirement (100%); "
                 "age65_ded = max(0, 15000 - retire_ded - military_ded) if age_65_plus else 0; "
                 "total per taxpayer = retire_ded + military_ded + age65_ded; sum taxpayer + spouse"),
     "inputs": ["taxpayer_age_65_plus", "spouse_age_65_plus", "taxpayer_retirement_income", "spouse_retirement_income",
                "taxpayer_military_retirement", "spouse_military_retirement"],
     "outputs": ["retirement_stack_deduction"], "sort_order": 21,
     "description": "Dec C. Age-65 $15,000 is REDUCED by that taxpayer's retirement + military deductions already claimed. SS is NOT in the retirement base (subtracted separately, line o). Computed per taxpayer, summed."},
    {"rule_id": "R-SC-SS", "title": "Social Security subtraction (line o)", "rule_type": "calculation",
     "formula": "line_o = social_security_taxed_federally",
     "inputs": ["social_security_taxed_federally"], "outputs": ["line_o"], "sort_order": 22,
     "description": "SC fully exempts Social Security / railroad retirement — subtract the amount taxed federally."},
    {"rule_id": "R-SC-DEP-EXEMPTION", "title": "Dependent exemption (w) + under-6 (t)", "rule_type": "calculation",
     "formula": "line_w = 4930 * num_dependents ; line_t = 4930 * num_dependents_under_6 (stacks on w)",
     "inputs": ["num_dependents", "num_dependents_under_6"], "outputs": ["line_w", "line_t"], "sort_order": 23,
     "description": "$4,930 per federal dependent (w); an ADDITIONAL $4,930 per under-6 dependent (t)."},
    {"rule_id": "R-SC-SUBTRACTIONS", "title": "Total subtractions (L4) and L5", "rule_type": "calculation",
     "formula": ("L4 = line_i + line_o + retirement_stack_deduction + line_w + line_t + "
                 "sc_prior_year_bonus_catchup + other_subtractions ; "
                 "L5 = max(0, L3 - L4)  [resident]  OR  schedule_nr_line48  [PY/NR]"),
     "inputs": ["is_part_year_or_nonresident", "schedule_nr_line48"], "outputs": ["L4", "L5"], "sort_order": 24,
     "description": "L5 = SC income subject to tax. line v later-year depreciation (sc_prior_year_bonus_catchup) is a subtraction. PY/NR bypasses L1-L4."},
    {"rule_id": "R-SC-TAX", "title": "SC tax (L6) — 3-bracket / rate schedule", "rule_type": "calculation",
     "formula": ("if L5 >= 100000: L6 = round(0.06*L5 - 642) ; "
                 "else use SC1040TT bracketed table: 0% to 3560, 3% 3561-17830, 6% over 17830"),
     "inputs": ["L5"], "outputs": ["L6"], "sort_order": 25,
     "description": "Top rate 6% (2025). ≥$100k uses 6%×L5−$642. Thresholds $3,560/$17,830 (W2 re-verify)."},
    {"rule_id": "R-SC-TOTAL-TAX", "title": "Total SC tax (L10)", "rule_type": "calculation",
     "formula": "L10 = L6 + L7 + L8 + L9  (L7 SC4972, L8 I-335, L9 catastrophe — all RED-deferred inputs)",
     "inputs": ["L6"], "outputs": ["L10"], "sort_order": 26},
    {"rule_id": "R-SC-CHILDCARE", "title": "Child & Dependent Care credit (L11)", "rule_type": "calculation",
     "formula": "L11 = min(0.07 * federal_childcare_expense, 210 if num_care_dependents<=1 else 420) ; 0 if MFS",
     "inputs": ["federal_childcare_expense", "num_care_dependents", "filing_status"], "outputs": ["L11"], "sort_order": 30,
     "description": "7% of the federal 2441 expense, capped $210 (1) / $420 (2+). Not allowed MFS. PY/NR: prorate expense by Sch NR line 45."},
    {"rule_id": "R-SC-TWO-WAGE", "title": "Two Wage Earner credit (L12)", "rule_type": "calculation",
     "formula": "L12 = 0.007 * min(50000, lesser(taxpayer_sc_earned_income, spouse_sc_earned_income)) ; MFJ only ; max 350",
     "inputs": ["filing_status", "taxpayer_sc_earned_income", "spouse_sc_earned_income"], "outputs": ["L12"], "sort_order": 31,
     "description": "MFJ only; 0.7% × lesser($50,000, lower-earning spouse SC earned income); max $350."},
    {"rule_id": "R-SC-NET-TAX", "title": "Net tax after nonrefundable credits (L15)", "rule_type": "calculation",
     "formula": "L14 = L11 + L12 + other_nonrefundable_credits ; L15 = max(0, L10 - L14)",
     "inputs": ["other_nonrefundable_credits"], "outputs": ["L14", "L15"], "sort_order": 32},
    {"rule_id": "R-SC-PAYMENTS", "title": "Total payments (L23)", "rule_type": "calculation",
     "formula": "L23 = sc_withholding + estimated_payments + extension_payment + tuition_tax_credit + other_refundable_credits",
     "inputs": ["sc_withholding", "estimated_payments", "extension_payment", "tuition_tax_credit", "other_refundable_credits"], "outputs": ["L23"], "sort_order": 40},
    {"rule_id": "R-SC-REFUND-DUE", "title": "Refund (L30) or balance due (L34)", "rule_type": "calculation",
     "formula": "if L23 > L15: overpayment L24 = L23-L15 → refund L30 (net of use tax L26 / check-offs L28); else amount due L25 = L15-L23 → balance due L34 (+L32 penalties +L33 SC2210)",
     "inputs": ["L15", "L23"], "outputs": ["L30", "L34"], "sort_order": 41},
]

SC1040_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-SC-DEPR-ADDBACK", "SC_2025_SC1040_INSTR", "primary", "§168(k) add-back verbatim, line e"),
    ("R-SC-DEPR-ADDBACK", "SC_ACT63_2025_CONFORMITY", "primary", "SC conformity 12/31/2024; §12-6-50 decouples §168(k)"),
    ("R-SC-DEPR-ADDBACK", "SC_RR_05_2_DEPR", "interpretive", "separate SC depreciation schedule + disposition basis"),
    ("R-SC-179-ADDBACK", "SC_ACT63_2025_CONFORMITY", "primary", "SC conforms to §179 at 12/31/2024 (pre-OBBBA); not on the §12-6-50 non-adopted list"),
    ("R-SC-179-ADDBACK", "SC_2025_SC1040_INSTR", "secondary", "line e additions carry the depreciation/§179 conformity difference"),
    ("R-SC-CAPGAIN", "SC_2025_FORM_SC1040", "primary", "44% net LT capital gain deduction, line i"),
    ("R-SC-RETIRE-STACK", "SC_2025_SC1040_INSTR", "primary", "retirement/military/age-65 stack verbatim rules"),
    ("R-SC-SS", "SC_2025_FORM_SC1040", "primary", "Social Security fully exempt, line o"),
    ("R-SC-DEP-EXEMPTION", "SC_2025_FORM_SC1040", "primary", "$4,930 dependent exemption (w) + under-6 (t)"),
    ("R-SC-SUBTRACTIONS", "SC_2025_FORM_SC1040", "primary", "subtractions f-w → L4 → L5"),
    ("R-SC-TAX", "SC_2025_SC1040TT", "primary", "3-bracket rate + ≥$100k schedule 6%×L5−$642"),
    ("R-SC-CHILDCARE", "SC_2025_FORM_SC1040", "primary", "L11 child-care 7%, max $210/$420"),
    ("R-SC-TWO-WAGE", "SC_2025_FORM_SC1040", "primary", "L12 two-wage-earner 0.7%, max $350"),
    ("R-SC-TAX", "SC_ACT63_2025_CONFORMITY", "secondary", "conformity governs the base"),
]

SC1040_LINES: list[dict] = [
    {"line_number": "1", "description": "Federal taxable income (1040 line 15)", "line_type": "input", "source_facts": ["federal_taxable_income"], "sort_order": 1},
    {"line_number": "e", "description": "Other additions — includes §168(k) bonus-depreciation add-back", "line_type": "calculated", "calculation": "R-SC-DEPR-ADDBACK", "source_rules": ["R-SC-DEPR-ADDBACK"], "sort_order": 2},
    {"line_number": "2", "description": "Total additions (a-e)", "line_type": "subtotal", "source_rules": ["R-SC-ADDITIONS"], "sort_order": 3},
    {"line_number": "3", "description": "Line 1 + line 2", "line_type": "subtotal", "source_rules": ["R-SC-ADDITIONS"], "sort_order": 4},
    {"line_number": "i", "description": "44% net long-term capital gain deduction", "line_type": "calculated", "source_rules": ["R-SC-CAPGAIN"], "sort_order": 5},
    {"line_number": "o", "description": "Social Security / railroad retirement (fully exempt)", "line_type": "calculated", "source_rules": ["R-SC-SS"], "sort_order": 6},
    {"line_number": "p", "description": "Retirement + military retirement deduction", "line_type": "calculated", "source_rules": ["R-SC-RETIRE-STACK"], "sort_order": 7},
    {"line_number": "q", "description": "Age 65 and older deduction ($15,000, reduced by p)", "line_type": "calculated", "source_rules": ["R-SC-RETIRE-STACK"], "sort_order": 8},
    {"line_number": "t", "description": "Dependents under age 6 ($4,930 each)", "line_type": "calculated", "source_rules": ["R-SC-DEP-EXEMPTION"], "sort_order": 9},
    {"line_number": "v", "description": "Later-year additional SC depreciation (SC basis > federal)", "line_type": "input", "source_facts": ["sc_prior_year_bonus_catchup"], "sort_order": 10},
    {"line_number": "w", "description": "SC dependent exemption ($4,930 × dependents)", "line_type": "calculated", "source_rules": ["R-SC-DEP-EXEMPTION"], "sort_order": 11},
    {"line_number": "4", "description": "Total subtractions (f-w)", "line_type": "subtotal", "source_rules": ["R-SC-SUBTRACTIONS"], "sort_order": 12},
    {"line_number": "5", "description": "SC income subject to tax (resident L3-L4; PY/NR ← Sch NR L48)", "line_type": "subtotal", "source_rules": ["R-SC-SUBTRACTIONS"], "sort_order": 13},
    {"line_number": "6", "description": "Tax (SC1040TT / rate schedule)", "line_type": "calculated", "source_rules": ["R-SC-TAX"], "sort_order": 14},
    {"line_number": "7", "description": "Tax on lump-sum distribution (SC4972) — RED-defer", "line_type": "input", "sort_order": 15},
    {"line_number": "8", "description": "Tax on active trade/business income (I-335) — RED-defer", "line_type": "input", "sort_order": 16},
    {"line_number": "9", "description": "Tax on excess catastrophe-savings withdrawals — RED-defer", "line_type": "input", "sort_order": 17},
    {"line_number": "10", "description": "Total SC tax (6+7+8+9)", "line_type": "subtotal", "source_rules": ["R-SC-TOTAL-TAX"], "sort_order": 18},
    {"line_number": "11", "description": "Child & Dependent Care credit", "line_type": "calculated", "source_rules": ["R-SC-CHILDCARE"], "sort_order": 19},
    {"line_number": "12", "description": "Two Wage Earner credit", "line_type": "calculated", "source_rules": ["R-SC-TWO-WAGE"], "sort_order": 20},
    {"line_number": "13", "description": "Other nonrefundable credits (SC1040TC) — direct-entry", "line_type": "input", "source_facts": ["other_nonrefundable_credits"], "sort_order": 21},
    {"line_number": "14", "description": "Total nonrefundable credits", "line_type": "subtotal", "source_rules": ["R-SC-NET-TAX"], "sort_order": 22},
    {"line_number": "15", "description": "Tax after nonrefundable credits (L10 - L14)", "line_type": "subtotal", "source_rules": ["R-SC-NET-TAX"], "sort_order": 23},
    {"line_number": "21", "description": "Tuition tax credit (I-319, refundable) — direct-entry", "line_type": "input", "source_facts": ["tuition_tax_credit"], "sort_order": 24},
    {"line_number": "23", "description": "Total payments", "line_type": "subtotal", "source_rules": ["R-SC-PAYMENTS"], "sort_order": 25},
    {"line_number": "30", "description": "Refund", "line_type": "total", "source_rules": ["R-SC-REFUND-DUE"], "sort_order": 26},
    {"line_number": "34", "description": "Balance due", "line_type": "total", "source_rules": ["R-SC-REFUND-DUE"], "sort_order": 27},
]

SC1040_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_SC1040_179", "title": "§179 add-back computed at SC's pre-OBBBA $1.25M limit", "severity": "info",
     "condition": "federal §179 deducted exceeds SC's $1,250,000 limit (phaseout over $3,130,000)",
     "message": "SC conforms to §179 at the 12/31/2024 IRC level — limit $1,250,000 / phaseout $3,130,000 (NOT OBBBA's $2.5M/$4M). The excess of federal §179 over the SC-allowed amount is added back on line e and recovered via SC depreciation over the asset life. Verify against the business-income limit.",
     "notes": "W1 RESOLVED — Ken confirmed the figure 2026-07-04; computed by R-SC-179-ADDBACK."},
    {"diagnostic_id": "D_SC1040_ATB", "title": "Active Trade/Business 3% election (I-335) — prepare manually", "severity": "info",
     "condition": "taxpayer elects the I-335 active-trade-or-business 3% flat rate",
     "message": "The I-335 Active Trade or Business Income 3% election (L8 tax + line-l deduction) is not computed in v1. Prepare I-335 manually and enter L8.",
     "notes": "Dec D RED-defer."},
    {"diagnostic_id": "D_SC1040_LUMPSUM", "title": "Lump-sum distribution tax (SC4972) — prepare manually", "severity": "info",
     "condition": "SC4972 lump-sum distribution present", "message": "SC4972 lump-sum tax (L7) is not computed in v1. Prepare SC4972 manually.", "notes": "Dec D RED-defer."},
    {"diagnostic_id": "D_SC1040_CATSAV", "title": "Catastrophe Savings excess withdrawal (L9) — prepare manually", "severity": "info",
     "condition": "excess catastrophe-savings withdrawal", "message": "Catastrophe Savings Account excess-withdrawal tax (L9) is not computed in v1.", "notes": "Dec D RED-defer."},
    {"diagnostic_id": "D_SC1040_SC2210", "title": "Underpayment penalty (SC2210, L33) — prepare manually", "severity": "info",
     "condition": "possible underpayment of estimated tax", "message": "The SC2210 underpayment penalty (L33) is not computed in v1.", "notes": "Dec D RED-defer."},
    {"diagnostic_id": "D_SC1040_BRACKET", "title": "Bracket thresholds unverified vs §12-6-510 (W2)", "severity": "info",
     "condition": "always (build note)", "message": "The $3,560/$17,830 bracket thresholds are corroborated by SC1040TT but not printed by DOR — verify vs SC Code §12-6-510 before locking. The 6% rate + $642 constant are primary-verified.", "notes": "W2."},
]

SC1040_SCENARIOS: list[dict] = [
    {"scenario_name": "SC resident, wages only, single, no dependents", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"federal_taxable_income": 50000, "filing_status": "single", "is_part_year_or_nonresident": False},
     "expected_outputs": {"L5": 50000, "L6": 2360},
     "notes": "Table lookup for <$100k. L6 = the published SC1040TT_2025 row for $50,000-$50,050 = $2,360 (verified 138/138 vs the SCDOR table by the tts engine 2026-07-05). The table applies the 3-bracket structure to each $50-bracket MIDPOINT ($50,025): 6%*50025 - 642 = 2359.50 -> $2,360 (half-up). The rate-schedule-at-exact-$50,000 (6%*50000-642 = 2358) is NOT the table value. (Prior pin '≈$2,533' was a wrong placeholder.)"},
    {"scenario_name": "SC resident ≥$100k — rate schedule", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"federal_taxable_income": 101000, "filing_status": "single", "is_part_year_or_nonresident": False},
     "expected_outputs": {"L5": 101000, "L6": 5418},
     "notes": "Verbatim SC1040TT example: 101000 × 6% = 6060 − 642 = 5418."},
    {"scenario_name": "Age-65 stack — retirement + military + age-65 interaction", "scenario_type": "edge", "sort_order": 3,
     "inputs": {"filing_status": "single", "taxpayer_age_65_plus": True, "taxpayer_retirement_income": 8000, "taxpayer_military_retirement": 5000},
     "expected_outputs": {"retirement_stack_deduction": 15000},
     "notes": "retire_ded=min(8000,10000)=8000; military=5000; age65=max(0,15000-8000-5000)=2000; total=8000+5000+2000=15000."},
    {"scenario_name": "§168(k) bonus add-back computed (line e)", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"federal_bonus_depreciation": 40000, "depreciation_without_bonus": 8000},
     "expected_outputs": {"line_e_depr_addback": 32000},
     "notes": "Dec B: 40000 − 8000 = 32000 added back on line e (SC basis then higher; extra SC depreciation later on line v)."},
    {"scenario_name": "§179 add-back — federal $2M vs SC $1.25M limit (W1)", "scenario_type": "edge", "sort_order": 7,
     "inputs": {"federal_179_deducted": 2000000, "section_179_property_total": 2000000},
     "expected_outputs": {"line_e_179_addback": 750000},
     "notes": "SC limit $1,250,000 (property $2M < $3.13M phaseout → no reduction); allowed = min(2000000, 1250000) = 1250000; add-back = 2000000 − 1250000 = 750000."},
    {"scenario_name": "§179 phaseout reduces the SC limit", "scenario_type": "edge", "sort_order": 8,
     "inputs": {"federal_179_deducted": 1250000, "section_179_property_total": 3630000},
     "expected_outputs": {"line_e_179_addback": 500000},
     "notes": "phaseout: SC limit = 1250000 − (3630000 − 3130000 = 500000) = 750000; allowed = min(1250000, 750000) = 750000; add-back = 1250000 − 750000 = 500000."},
    {"scenario_name": "Two-wage-earner credit cap", "scenario_type": "edge", "sort_order": 5,
     "inputs": {"filing_status": "MFJ", "taxpayer_sc_earned_income": 80000, "spouse_sc_earned_income": 60000},
     "expected_outputs": {"L12": 350},
     "notes": "0.007 × min(50000, min(80000,60000)=60000→capped 50000) = 350 (the max)."},
    {"scenario_name": "Child-care credit cap, 2+ dependents", "scenario_type": "normal", "sort_order": 6,
     "inputs": {"federal_childcare_expense": 9000, "num_care_dependents": 2, "filing_status": "MFJ"},
     "expected_outputs": {"L11": 420},
     "notes": "0.07 × 9000 = 630, capped at 420 (2+ dependents)."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 2 — SC Schedule NR (part-year / nonresident) — Dec A
# ═══════════════════════════════════════════════════════════════════════════

SCHNR_FACTS: list[dict] = [
    {"fact_key": "nr_agi_col_a_federal", "label": "Sch NR line 31 Col A — federal AGI", "data_type": "decimal", "required": True, "sort_order": 1},
    {"fact_key": "nr_agi_col_b_sc", "label": "Sch NR line 31 Col B — SC-source AGI", "data_type": "decimal", "required": True, "sort_order": 2},
    {"fact_key": "nr_sc_additions", "label": "Sch NR line 32 — SC additions (Col B, incl. bonus add-back)", "data_type": "decimal", "required": False, "sort_order": 3},
    {"fact_key": "nr_sc_subtractions", "label": "Sch NR line 42 — total SC subtractions (Col B, L33-41)", "data_type": "decimal", "required": False, "sort_order": 4,
     "notes": "Includes dependent exemption (33 $4,930×deps), 44% cap gain (34), retirement/military (35), age-65 (36), under-6 (37) — FULL, not line-45 prorated."},
    {"fact_key": "nr_deduction", "label": "Sch NR line 46 — standard or itemized deduction (Parts I-IV)", "data_type": "decimal", "required": False, "sort_order": 5},
]

SCHNR_RULES: list[dict] = [
    {"rule_id": "R-NR-SCMAGI", "title": "SC modified AGI (line 44)", "rule_type": "calculation",
     "formula": "L43 = nr_sc_additions - nr_sc_subtractions ; L44 = nr_agi_col_b_sc + L43",
     "inputs": ["nr_agi_col_b_sc", "nr_sc_additions", "nr_sc_subtractions"], "outputs": ["L43", "L44"], "sort_order": 1,
     "description": "SC subtractions (dep exemption, retirement, age-65, under-6, 44% cap gain) are FULL in the L33-42 block — NOT prorated by line 45."},
    {"rule_id": "R-NR-PRORATION", "title": "Proration percentage (line 45)", "rule_type": "calculation",
     "formula": "L45 = min(1.00, round(nr_agi_col_b_sc / nr_agi_col_a_federal, 2))  [0 if Col A <= 0]",
     "inputs": ["nr_agi_col_b_sc", "nr_agi_col_a_federal"], "outputs": ["L45"], "sort_order": 2,
     "description": "SC-source ratio = L31 Col B ÷ L31 Col A, ≤100%, 2 decimals. Prorates ONLY the deduction (L47)."},
    {"rule_id": "R-NR-DEDUCTION", "title": "Allowable deduction (line 47)", "rule_type": "calculation",
     "formula": "L47 = round(nr_deduction * L45)",
     "inputs": ["nr_deduction"], "outputs": ["L47"], "sort_order": 3,
     "description": "Only the standard/itemized deduction (L46) is prorated by line 45."},
    {"rule_id": "R-NR-TAXABLE", "title": "SC taxable income (line 48) → SC1040 line 5", "rule_type": "calculation",
     "formula": "L48 = max(0, L44 - L47)  →  SC1040 line 5",
     "inputs": [], "outputs": ["L48"], "sort_order": 4,
     "description": "Dec A. Line 48 → SC1040 line 5 (0 if negative). The load-bearing handoff."},
]

SCHNR_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-NR-SCMAGI", "SC_2025_SCHEDULE_NR", "primary", "L44 SC modified AGI"),
    ("R-NR-PRORATION", "SC_2025_SCHEDULE_NR", "primary", "L45 proration ratio, ≤100%, 2 decimals"),
    ("R-NR-DEDUCTION", "SC_2025_SCHEDULE_NR", "primary", "L47 = L46 × L45"),
    ("R-NR-TAXABLE", "SC_2025_SCHEDULE_NR", "primary", "L48 → SC1040 L5"),
]

SCHNR_LINES: list[dict] = [
    {"line_number": "31", "description": "Adjusted gross income (Col A federal / Col B SC)", "line_type": "subtotal", "source_facts": ["nr_agi_col_a_federal", "nr_agi_col_b_sc"], "sort_order": 1},
    {"line_number": "32", "description": "SC additions (Col B)", "line_type": "input", "source_facts": ["nr_sc_additions"], "sort_order": 2},
    {"line_number": "42", "description": "Total SC subtractions (L33-41, Col B)", "line_type": "subtotal", "source_facts": ["nr_sc_subtractions"], "sort_order": 3},
    {"line_number": "43", "description": "Total SC adjustments (L32 - L42)", "line_type": "subtotal", "source_rules": ["R-NR-SCMAGI"], "sort_order": 4},
    {"line_number": "44", "description": "SC modified AGI (L31 Col B + L43)", "line_type": "subtotal", "source_rules": ["R-NR-SCMAGI"], "sort_order": 5},
    {"line_number": "45", "description": "Proration % (L31 Col B / L31 Col A, ≤100%)", "line_type": "calculated", "source_rules": ["R-NR-PRORATION"], "sort_order": 6},
    {"line_number": "46", "description": "Standard or itemized deduction (Parts I-IV)", "line_type": "input", "source_facts": ["nr_deduction"], "sort_order": 7},
    {"line_number": "47", "description": "Allowable deduction (L46 × L45)", "line_type": "calculated", "source_rules": ["R-NR-DEDUCTION"], "sort_order": 8},
    {"line_number": "48", "description": "SC taxable income → SC1040 line 5", "line_type": "total", "calculation": "R-NR-TAXABLE", "destination_form": "SC1040", "source_rules": ["R-NR-TAXABLE"], "sort_order": 9},
]

SCHNR_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_SCNR_PRORATE", "title": "Only the deduction is prorated by line 45", "severity": "info",
     "condition": "part-year/nonresident return", "message": "Line 45 prorates ONLY the L46 deduction. Income (Col B) and the SC subtractions (L33-42: dep exemption, retirement, age-65, under-6, 44% cap gain) are already SC-sourced/full and are NOT re-multiplied by line 45.",
     "notes": "Common error — do not double-prorate the subtractions."},
]

SCHNR_SCENARIOS: list[dict] = [
    {"scenario_name": "Part-year, 60% SC-source", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"nr_agi_col_a_federal": 100000, "nr_agi_col_b_sc": 60000, "nr_sc_additions": 0, "nr_sc_subtractions": 5000, "nr_deduction": 14600},
     "expected_outputs": {"L44": 55000, "L45": 0.60, "L47": 8760, "L48": 46240},
     "notes": "L43=0-5000=-5000; L44=60000-5000=55000; L45=60000/100000=0.60; L47=14600*.60=8760; L48=55000-8760=46240 → SC1040 L5."},
    {"scenario_name": "Nonresident, SC ratio capped at 100%", "scenario_type": "edge", "sort_order": 2,
     "inputs": {"nr_agi_col_a_federal": 40000, "nr_agi_col_b_sc": 50000, "nr_sc_additions": 0, "nr_sc_subtractions": 0, "nr_deduction": 14600},
     "expected_outputs": {"L45": 1.00, "L47": 14600},
     "notes": "Ratio 50000/40000=1.25 → capped 1.00; L47 = full deduction."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORMS registry
# ═══════════════════════════════════════════════════════════════════════════

FORMS: list[dict] = [
    {
        "identity": {"form_number": "SC1040", "form_title": "SC1040 — South Carolina Individual Income Tax Return (TY2025)",
                     "notes": "2nd state individual spec. Federal-taxable-income start; 3-bracket tax; §168(k) add-back computed; retirement/military/age-65 stack. v1 MAXIMAL (D-6)."},
        "facts": SC1040_FACTS, "rules": SC1040_RULES, "rule_links": SC1040_RULE_LINKS,
        "lines": SC1040_LINES, "diagnostics": SC1040_DIAGNOSTICS, "scenarios": SC1040_SCENARIOS,
    },
    {
        "identity": {"form_number": "SC_SCHEDULE_NR", "form_title": "SC Schedule NR — Nonresident Schedule (TY2025)",
                     "notes": "Part-year/nonresident SC-source proration; line 48 → SC1040 line 5 (Dec A)."},
        "facts": SCHNR_FACTS, "rules": SCHNR_RULES, "rule_links": SCHNR_RULE_LINKS,
        "lines": SCHNR_LINES, "diagnostics": SCHNR_DIAGNOSTICS, "scenarios": SCHNR_SCENARIOS,
    },
]

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-SC-L1", "title": "SC1040 L1 = federal taxable income (1040 L15)", "assertion_type": "flow_assertion",
     "entity_types": ["1040"], "status": "draft", "sort_order": 1,
     "description": "SC1040 line 1 pulls the child 1040's federal taxable income (line 15). W4: confirm the tts handoff pulls taxable income, not AGI.",
     "definition": {"source": "federal_1040.line_15", "target": "SC1040.L1"}},
    {"assertion_id": "FA-SC-NR-L5", "title": "Sch NR L48 → SC1040 L5 for part-year/nonresident", "assertion_type": "flow_assertion",
     "entity_types": ["1040"], "status": "draft", "sort_order": 2,
     "description": "When is_part_year_or_nonresident, SC1040 line 5 = Schedule NR line 48 (bypassing L1-L4).",
     "definition": {"source": "SC_SCHEDULE_NR.L48", "target": "SC1040.L5", "condition": "is_part_year_or_nonresident"}},
    {"assertion_id": "FA-SC-DEPR", "title": "§168(k) bonus add-back = federal depr − non-bonus depr", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "draft", "sort_order": 3,
     "description": "SC1040 line e add-back reconciles to federal_bonus_depreciation − depreciation_without_bonus (Dec B).",
     "definition": {"rule": "R-SC-DEPR-ADDBACK", "check": "line_e_depr_addback == federal_bonus_depreciation - depreciation_without_bonus"}},
    {"assertion_id": "FA-SC-AGE65", "title": "Age-65 deduction reduced by retirement + military", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "draft", "sort_order": 4,
     "description": "Per taxpayer, age65_ded = max(0, 15000 − retirement_ded − military_ded) (Dec C interacting stack).",
     "definition": {"rule": "R-SC-RETIRE-STACK", "check": "age65 = max(0, 15000 - retire - military)"}},
    {"assertion_id": "FA-SC-CHILDCARE", "title": "SC child-care credit = 7% federal 2441, capped", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "draft", "sort_order": 5,
     "description": "L11 = min(0.07 × federal 2441 expense, $210/$420); PY/NR prorates the expense by Sch NR line 45.",
     "definition": {"rule": "R-SC-CHILDCARE", "check": "L11 = min(0.07*expense, cap)"}},
]


# ═══════════════════════════════════════════════════════════════════════════
# Command
# ═══════════════════════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = (
        "Load the SC1040 spec (South Carolina Individual Income Tax, TY2025) + Schedule NR. "
        "Refuses to seed until Ken sets READY_TO_SEED=True after the in-session review walk (W1-W5)."
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()

        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad SC1040 spec (South Carolina Individual Income Tax + Schedule NR)\n"))

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
                "\nREFUSING TO SEED SC1040: not cleared to seed.\n\n"
                "Content is authored, but seeding is gated until Ken reviews the packet\n"
                "(W1 §179 conformity / the $1.25M-vs-$2.5M limit + compute-vs-direct-entry;\n"
                "W2 the bracket thresholds vs §12-6-510; W3 the tuition credit cap; W4 the\n"
                "federal-taxable-income handoff; W5 the OBBBA non-adoption re-verify) and flips\n"
                "the sentinel.\n\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True to proceed)\n\n"
                f"Currently empty / placeholder:\n  {still_empty}\n\n"
                "To proceed: review the module-level data lists (and sc1040_source_brief.md),\n"
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
        self.stdout.write("SC1040 + Schedule NR loaded.")
        self.stdout.write(
            f"  SC1040: facts {len(SC1040_FACTS)} / rules {len(SC1040_RULES)} / lines {len(SC1040_LINES)} / "
            f"diag {len(SC1040_DIAGNOSTICS)} / tests {len(SC1040_SCENARIOS)}"
        )
        self.stdout.write(
            f"  Sch NR: facts {len(SCHNR_FACTS)} / rules {len(SCHNR_RULES)} / lines {len(SCHNR_LINES)} / "
            f"diag {len(SCHNR_DIAGNOSTICS)} / tests {len(SCHNR_SCENARIOS)}"
        )
        self.stdout.write(f"  Flow assertions: {len(FLOW_ASSERTIONS)}")
        self.stdout.write("=" * 60)
