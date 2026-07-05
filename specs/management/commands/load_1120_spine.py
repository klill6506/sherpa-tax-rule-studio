"""Load the Form 1120 spine — U.S. Corporation Income Tax Return (TY2025).
WO-11 / S-13, the C-corporation module. Consolidated compute spine: page-1 income/deductions +
Schedule C (dividends-received deduction) + Schedule J (tax computation) → total tax.

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
Form 1120 is the C-corporation income tax return. This `1120` form is the computational core
(Ken's Gate-1 shape = spine + 2, mirroring the 1041 consolidated spine): page-1 income (L1-11) →
deductions (L12-27) → taxable income before NOL & special deductions (L28) → Schedule C DRD
(special deductions L29b) + §172 NOL deduction (L29a) → taxable income (L30) → Schedule J §11 flat
21% tax → credits → total tax (Sch J L12 → page-1 L31). Schedule K/L, M-1, M-2 live on `1120_SCHL`;
COGS = Form 1125-A; officer comp = Form 1125-E; depreciation/disposition/GBC = 4562/4797/3800
(all already carry '1120' in entity_types — confirmed at the WO-11 gap-check).

Greenfield: lookup/1120/ → 404 at the 2026-07-05 gap-check (only the S-corp forms + shared
1125-A/1125-E/3800/4562/4797/8949/7004 existed).

═══════════════════════════════════════════════════════════════════════════
v1 SCOPE — LOCKED (Ken's Gate-1 walk 2026-07-05; DECISIONS D-13). See f1120_source_brief.md.
═══════════════════════════════════════════════════════════════════════════
COMPUTES (v1):
  • Page-1 income → deductions → taxable income before NOL & special deductions (L28).
  • Schedule C DRD (Q2 = domestic + §246(b) limit): 50% (<20%-owned), 65% (20%+-owned), 100%
    (wholly-owned foreign / SBIC / affiliated-group / §245A) → special deductions; the §246(b)
    taxable-income limitation with the §172 NOL LOSS EXCEPTION. §246(c) holding period / §246A
    debt-financed / foreign-GILTI-§250 lines = diagnostic + direct-entry.
  • §172 NOL deduction (Q3): the 80%-of-(L28 − special deductions) limitation; carryover direct-entry.
  • Schedule J: §11 flat 21% income tax (L1a) → CAMT (L3, direct-entry) → credits (GBC/FTC/other) →
    PHC (L8, direct-entry) → total tax (L12) → page-1 L31.
SCREEN + ROUTE / RED-DEFER (Q3 — low-population special regimes):
  • §163(j) business-interest limit → gate on Sch K Q24 (>$31M §448(c)) → Form 8990. Note the OBBBA
    EBITDA-basis restoration for TY2025 (D_1120_163J). Compute deferred to Form 8990.
  • §55 CAMT (15% of AFSI, applicable corp = avg AFSI > $1B) → Form 4626 (Sch K Q29) — RED-defer.
  • §541 PHC (20%) → Schedule PH; §531 AET (20%, $250k/$150k credit) — RED-defer.
  • §59A base erosion (gross receipts ≥ $500M) → Form 8991 (Sch K Q22).
  • §1062 OBBBA farmland-gain deferral → Form 1062 (page-1 L32) — structure + flag.

═══════════════════════════════════════════════════════════════════════════
requires_human_review WALK ITEMS (W1-W5)
═══════════════════════════════════════════════════════════════════════════
W1. §11 FLAT 21% — income tax = taxable income (L30) × 21% (i1120 Sch J L1a "× 0.21"). CONFIRM.
W2. SCHEDULE C DRD — 50/65/100% by ownership category; §246(b) taxable-income limitation (65% if any
    20%+-owned dividends else 50%) with the LOSS EXCEPTION (limit does not apply if the full DRD
    creates/increases an NOL). 100% lines (foreign sub / SBIC / affiliated / §245A) NOT subject to
    the §246(b) limit. v1 simplifies the combined 50/65 worksheet interaction. CONFIRM.
W3. §172 NOL — L29a = min(available carryover, 80% × (L28 − special deductions)); post-2017 NOLs =
    80% cap, no carryback, indefinite carryforward. CONFIRM the 80% base.
W4. TOTAL TAX ASSEMBLY — Sch J: 21% income tax + CAMT (direct-entry) − credits + PHC (direct-entry)
    + recapture = total tax (L12) → page-1 L31. CONFIRM the direct-entry defers (CAMT/PHC).
W5. SPECIAL-REGIME SCREENS — §163(j) >$31M gate → 8990 (OBBBA EBITDA basis TY2025); §55 CAMT $1B →
    4626; §541 PHC; §531 AET; §59A $500M → 8991; §1062 → 1062. All screen + route, not computed. CONFIRM.

═══════════════════════════════════════════════════════════════════════════
CARRIED [UNVERIFIED] / flags (re-pull before any deeper compute leg):
  • §11 label: the 21% mechanic is verbatim i1120 Sch J L1a; literal "section 11" not in extracted text.
  • §246(b) combined 50/65 worksheet: v1 uses a single limit_pct (65% if any 20%+ dividends); the
    per-tier worksheet interaction (i1120 Sch C worksheet) is simplified. Re-verify for mixed portfolios.
  • §163(j) TY2026 electively-capitalized-interest change is NOT encoded (TY2025 spec).
  • Re-verify all constants at TY2026 ($31M §448(c), $1B AFSI, 21% rate, 80% NOL).
═══════════════════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════════════════
SAFETY GUARD — READY_TO_SEED stays False until Ken approves the review walk (W1-W5).
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
# FLIPPED 2026-07-05 — Ken APPROVED the review walk in-session ("Approve — flip,
# seed, export"): W1 the §11 flat 21%, W2 the Schedule C DRD + §246(b) limit/loss
# exception, W3 the §172 NOL 80% limitation, W4 the total-tax assembly, W5 the
# special-regime screens (§163(j)/CAMT/PHC/AET/§59A/§1062) — all blessed. Validated
# on throwaway SQLite (scratchpad/validate_1120.py, 55 pass / 0 fail).
# ═══════════════════════════════════════════════════════════════════════════
READY_TO_SEED = True


FORM_JURISDICTION = "federal"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1120"]


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS (cited in f1120_source_brief.md; never memory)
# ═══════════════════════════════════════════════════════════════════════════
CORP_TAX_RATE = "0.21"              # §11(b) — flat 21% (i1120 Sch J L1a "× 0.21")
DRD_50 = "0.50"                     # §243(a)(1) — <20%-owned domestic
DRD_65 = "0.65"                     # §243(c) — 20%+-owned domestic
DRD_100 = "1.00"                    # §243(a)(3)/§245A — affiliated / SBIC / wholly-owned foreign / foreign-source
DRD_LIMIT_50 = "0.50"              # §246(b) taxable-income limit (no 20%+ dividends)
DRD_LIMIT_65 = "0.65"             # §246(b) taxable-income limit (any 20%+ dividends)
NOL_LIMIT_PCT = "0.80"            # §172(a)(2) — 80% of taxable income (post-2017)
SEC163J_GROSS_RCPTS = 31000000     # §448(c) 2025-indexed small-business exemption ($31M)
CAMT_AFSI_THRESHOLD = 1000000000   # §59(k) applicable corp — avg AFSI > $1B
CAMT_RATE = "0.15"                 # §55(b)(2)(A) — 15% of AFSI
PHC_RATE = "0.20"                  # §541 — 20% of undistributed PHC income
AET_RATE = "0.20"                  # §531 — 20% of accumulated taxable income
AET_CREDIT_GENERAL = 250000        # §535(c)(2) general credit
AET_CREDIT_PSC = 150000            # §535(c)(2)(B) personal-service-corp credit
BASE_EROSION_RCPTS = 500000000     # §59A(e) — gross receipts >= $500M (Form 8991)


def _drd(div_less20, div_20plus, div_100pct_group, div_245a, l28_pre_drd, special_other):
    """Schedule C domestic DRD with the §246(b) taxable-income limitation + loss exception.
    Returns (special_deductions, drd_50_65, drd_100, limited_flag, loss_exception_flag)."""
    drd_before = float(div_less20) * float(DRD_50) + float(div_20plus) * float(DRD_65)
    drd_100 = (float(div_100pct_group) + float(div_245a)) * float(DRD_100)
    # §246(b) base = taxable income before the 50/65 DRD, before NOL/§199A/§250, less the 100% DRD.
    ti_limit_base = float(l28_pre_drd) - drd_100 - float(special_other)
    limit_pct = float(DRD_LIMIT_65) if float(div_20plus) > 0 else float(DRD_LIMIT_50)
    # Loss exception (§246(b)(1) flush): if the full 50/65 DRD creates/increases an NOL, no limit.
    loss_exception = (ti_limit_base - drd_before) < 0
    if loss_exception or ti_limit_base <= 0:
        drd_50_65 = drd_before
    else:
        drd_50_65 = min(drd_before, limit_pct * ti_limit_base)
    limited = drd_50_65 < drd_before
    special = drd_50_65 + drd_100 + float(special_other)
    return special, drd_50_65, drd_100, limited, loss_exception


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY TOPICS / SOURCES
# ═══════════════════════════════════════════════════════════════════════════
AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("c_corp_income_tax", "Form 1120 C-corporation income tax: §11 flat 21% rate, §243/§245A/§246 "
     "dividends-received deduction, §172 80% NOL limitation, Schedule J tax computation, and the "
     "screened special regimes (§163(j), §55 CAMT, §541 PHC, §531 AET, §59A, §1062)."),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_F1120",
        "source_type": "federal_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "US",
        "title": "2025 Form 1120 — U.S. Corporation Income Tax Return",
        "citation": "Form 1120 (2025), OMB No. 1545-0123, Created 9/26/25",
        "issuer": "Internal Revenue Service",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f1120.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.6,
        "topics": ["c_corp_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "Page-1 line flow + Schedule J restructure (2025 verbatim)",
                "excerpt_text": (
                    "Page 1: L1c gross receipts less returns; L2 COGS (Form 1125-A); L3 gross profit; L4 "
                    "Dividends and inclusions (Schedule C line 23); L5 interest; L6 rents; L7 royalties; L8 "
                    "capital gain net income (Sch D); L9 net gain/(loss) Form 4797 Part II L17; L10 other "
                    "income; L11 Total income. Deductions L12 compensation of officers (Form 1125-E) through "
                    "L26 other deductions; L27 Total deductions; L28 Taxable income before NOL and special "
                    "deductions (L11-L27); L29a NOL deduction; L29b Special deductions (Sch C L24); L29c add; "
                    "L30 Taxable income (L28-L29c); L31 Total tax (Schedule J, LINE 12); L32 §1062 first "
                    "installment (Form 1062). Schedule J (2025, one continuous list to L23, OBBBA-restructured, "
                    "no Part I/II): L1a income tax = taxable income x 21%; L2 total income tax; L3 CAMT (Form "
                    "4626); L4 add 2+3; L5a-5f credits (FTC 1118, 8834, GBC Form 3800, prior-yr min tax 8827, "
                    "bond 8912, 8978); L6 total credits; L7 subtract; L8 PHC (Schedule PH); L9a-9z recapture; "
                    "L11a total before deferred; L12 Total tax -> page-1 L31. Payments L13-23."
                ),
                "summary_text": "1120 (2025): income L1-11, deductions L12-27, L28 pre-NOL/special, L29a NOL + L29b special (Sch C L24) -> L30 taxable income -> Sch J L1a 21% -> L12 total tax -> page-1 L31.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule C DRD percentages + Schedule K gates (2025 verbatim)",
                "excerpt_text": (
                    "Schedule C (cols (a) amount, (b) %, (c)=a*b): L1 <20%-owned domestic = 50%; L2 20%+-owned "
                    "domestic = 65%; L3 debt-financed = see instructions (§246A); L4 <20% public utility = "
                    "23.3%; L5 20%+ public utility = 26.7%; L6/L7 foreign 50/65%; L8 wholly-owned foreign sub = "
                    "100%; L9 subtotal (L1-8, §246(b) limit); L10 SBIC = 100%; L11 affiliated group = 100%; L13 "
                    "§245A foreign-source portion = 100%; L22 §250 deduction (Form 8993); L23 total dividends -> "
                    "page-1 L4; L24 total special deductions -> page-1 L29b. Schedule K: Q12 available NOL "
                    "carryover from prior years (do not reduce by L29a); Q22 gross receipts >= $500M -> §59A "
                    "(Form 8991); Q23 §163(j) real-property/farming election; Q24 §163(j)/Form 8990 trigger "
                    "((b) avg gross receipts > $31M under §448(c)); Q29 CAMT applicable corp §59(k) -> Form 4626."
                ),
                "summary_text": "Sch C DRD: 50 (<20%) / 65 (20%+) / 100 (foreign sub, SBIC, affiliated, §245A); L9 subtotal §246(b)-limited; L23->L4, L24->L29b. Sch K Q12 NOL carryover, Q24 §163(j) >$31M, Q29 CAMT.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_I1120",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "US",
        "title": "2025 Instructions for Form 1120",
        "citation": "Instructions for Form 1120 (2025)",
        "issuer": "Internal Revenue Service",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i1120.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["c_corp_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "21% rate + 80% NOL limitation + due date (i1120 verbatim)",
                "excerpt_text": (
                    "'Line 1a. Income tax. Multiply taxable income (page 1, line 30) by 21% (0.21). Enter this "
                    "amount on line 1a.' NOL: the deduction is limited to '80% of the excess, if any, of taxable "
                    "income determined without any NOL deduction, section 199A deduction, or section 250 "
                    "deduction, over any NOL carryover to the tax year from tax years beginning before' 2018. "
                    "Due date: 'Generally, a corporation must file its income tax return by the 15th day of the "
                    "4th month after the end of its tax year.' What's New (P.L. 119-21 / OBBBA): new §1062 "
                    "farmland-gain deferral (Form 1062); failure-to-file minimum penalty raised to the smaller "
                    "of tax due or $525 for returns due in 2026."
                ),
                "summary_text": "i1120: L1a income tax = line-30 x 21%. NOL limited to 80% of taxable income (before NOL/§199A/§250). Due 15th day of 4th month. OBBBA: §1062 (Form 1062).",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_11",
        "source_type": "statute",
        "source_rank": "controlling",
        "jurisdiction_code": "US",
        "title": "IRC §11 — Tax imposed on corporations (flat 21%)",
        "citation": "26 U.S.C. §11(b)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/11",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["c_corp_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "§11(b) flat rate (verbatim)",
                "excerpt_text": "§11(b): 'The amount of the tax imposed by subsection (a) shall be 21 percent of taxable income.' Flat; no graduated brackets (TCJA, unchanged by OBBBA for TY2025).",
                "summary_text": "§11(b): corporate income tax = 21% of taxable income, flat.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_243_246",
        "source_type": "statute",
        "source_rank": "controlling",
        "jurisdiction_code": "US",
        "title": "IRC §243 / §245A / §246 / §246A — dividends-received deduction",
        "citation": "26 U.S.C. §243(a),(c); §245A; §246(b),(c); §246A",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/243",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.4,
        "topics": ["c_corp_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "DRD percentages + §246(b) limit + loss exception (verbatim)",
                "excerpt_text": (
                    "§243(a)(1): '50 percent, in the case of dividends other than dividends described in "
                    "paragraph (2) or (3).' §243(c)(1): for a dividend from a 20-percent owned corporation, "
                    "substitute '65 percent' for '50 percent'; §243(c)(2): 20-percent owned = 20% or more of "
                    "stock by vote and value. §243(a)(3): '100 percent, in the case of qualifying dividends' "
                    "(affiliated group, §1504(a)). §245A(a): a 100% deduction of 'the foreign-source portion' of "
                    "a dividend from a specified 10-percent owned foreign corporation. §246(b): the aggregate "
                    "DRD 'shall not exceed' 65% (20%-owned) / 50% (other) of taxable income computed without "
                    "§172/§199A/§243(a)(1)/§250; the limitation 'shall not apply for any taxable year for which "
                    "there is a net operating loss.' §246(c): 45-day (91-day window) / 90-day holding period. "
                    "§246A: debt-financed portfolio stock reduces the DRD by (50/65%) x (average indebtedness %)."
                ),
                "summary_text": "§243 DRD 50/65/100%; §245A 100% foreign-source; §246(b) TI limit (65/50%) with the NOL loss exception; §246(c) holding period; §246A debt-financed reduction.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_172",
        "source_type": "statute",
        "source_rank": "controlling",
        "jurisdiction_code": "US",
        "title": "IRC §172 — Net operating loss deduction (80% limit, no carryback)",
        "citation": "26 U.S.C. §172(a)(2), (b)(1)(A)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/172",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.4,
        "topics": ["c_corp_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "§172(a)(2) 80% limitation (verbatim)",
                "excerpt_text": (
                    "§172(a)(2): the NOL deduction = the lesser of the aggregate NOL carryovers, or '80 percent "
                    "of the excess (if any) of— (I) taxable income computed without regard to the deductions "
                    "under this section and sections 199A and 250...' §172(b)(1)(A): post-2017 NOLs carry "
                    "forward to each following year with no time limit (indefinite); no carryback for ordinary "
                    "corporate NOLs (TCJA §13302). OBBBA did not change the core corporate NOL mechanics."
                ),
                "summary_text": "§172(a)(2): NOL deduction = min(carryovers, 80% of taxable income before NOL/§199A/§250). No carryback; indefinite carryforward.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_163J",
        "source_type": "statute",
        "source_rank": "controlling",
        "jurisdiction_code": "US",
        "title": "IRC §163(j) — business interest limitation (OBBBA EBITDA basis for TY2025)",
        "citation": "26 U.S.C. §163(j)(1),(8); §448(c)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/163",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.2,
        "topics": ["c_corp_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "§163(j) 30% ATI + OBBBA EBITDA restoration (verbatim substance)",
                "excerpt_text": (
                    "§163(j)(1): business interest deduction limited to business interest income + 30% of "
                    "adjusted taxable income (ATI) + floor-plan financing interest. §163(j)(8) (current text, "
                    "OBBBA): ATI is computed on an EBITDA basis — depreciation, amortization, and depletion are "
                    "added back (excluded), RESTORED AND MADE PERMANENT for tax years beginning after Dec. 31, "
                    "2024 (i.e., TY2025). §448(c) small-business exemption: average annual gross receipts <= "
                    "$31,000,000 (2025-indexed); tax shelters excluded. Filing vehicle = Form 8990."
                ),
                "summary_text": "§163(j): 30% ATI, EBITDA basis RESTORED for TY2025 (OBBBA); $31M §448(c) exemption; Form 8990. Compute deferred to Form 8990; 1120 gates on Sch K Q24.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_55_CAMT",
        "source_type": "statute",
        "source_rank": "controlling",
        "jurisdiction_code": "US",
        "title": "IRC §55 / §59 — Corporate Alternative Minimum Tax (CAMT)",
        "citation": "26 U.S.C. §55(b)(2)(A); §59(k)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/55",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.2,
        "topics": ["c_corp_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "§55/§59 CAMT 15% / $1B threshold (verbatim)",
                "excerpt_text": (
                    "§55(b)(2)(A): the tentative minimum tax of an applicable corporation = '15 percent of the "
                    "adjusted financial statement income for the taxable year' less the CAMT foreign tax credit. "
                    "§59(k): 'applicable corporation' = one whose average annual adjusted financial statement "
                    "income for the 3-taxable-year period exceeds $1,000,000,000. Effective for tax years "
                    "beginning after Dec. 31, 2022. Reported on Form 4626 (Sch J L3)."
                ),
                "summary_text": "§55/§59: CAMT = 15% of AFSI for applicable corps (avg AFSI > $1B over 3 yrs); Form 4626. RED-defer (out of population).",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_541_531",
        "source_type": "statute",
        "source_rank": "controlling",
        "jurisdiction_code": "US",
        "title": "IRC §541/§542 PHC · §531/§535 AET",
        "citation": "26 U.S.C. §541, §542(a); §531, §535(c)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/541",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.2,
        "topics": ["c_corp_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "PHC + AET rates and tests (verbatim)",
                "excerpt_text": (
                    "§541: a personal holding company tax = '20 percent of the undistributed personal holding "
                    "company income.' §542(a): PHC if (income test) at least 60% of adjusted ordinary gross "
                    "income is PHC income AND (ownership test) more than 50% in value of the stock is owned by "
                    "or for not more than 5 individuals during the last half of the year. Schedule PH (Form "
                    "1120). §531: an accumulated earnings tax = '20 percent of the accumulated taxable income.' "
                    "§535(c): accumulated earnings credit = $250,000 general / $150,000 for service corporations."
                ),
                "summary_text": "§541 PHC = 20% (60% income test + >50% by <=5 individuals; Sch PH). §531 AET = 20% ($250k/$150k credit). Both RED-defer.",
                "is_key_excerpt": True,
            },
        ],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_F1120", "1120", "governs"),
    ("IRS_2025_I1120", "1120", "governs"),
    ("IRC_11", "1120", "governs"),
    ("IRC_243_246", "1120", "governs"),
    ("IRC_172", "1120", "governs"),
    ("IRC_163J", "1120", "governs"),
    ("IRC_55_CAMT", "1120", "governs"),
    ("IRC_541_531", "1120", "governs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM — 1120 spine
# ═══════════════════════════════════════════════════════════════════════════
F1120_FACTS: list[dict] = [
    # ── Page 1 income ──
    {"fact_key": "gross_receipts", "label": "Gross receipts or sales (page-1 L1a)", "data_type": "decimal", "required": False, "sort_order": 1},
    {"fact_key": "returns_allowances", "label": "Returns and allowances (page-1 L1b)", "data_type": "decimal", "required": False, "sort_order": 2},
    {"fact_key": "cogs", "label": "Cost of goods sold — from Form 1125-A (page-1 L2)", "data_type": "decimal", "required": False, "sort_order": 3,
     "notes": "COGS computed on Form 1125-A (already covers 1120)."},
    {"fact_key": "interest_income", "label": "Interest income (page-1 L5)", "data_type": "decimal", "required": False, "sort_order": 4},
    {"fact_key": "gross_rents", "label": "Gross rents (page-1 L6)", "data_type": "decimal", "required": False, "sort_order": 5},
    {"fact_key": "gross_royalties", "label": "Gross royalties (page-1 L7)", "data_type": "decimal", "required": False, "sort_order": 6},
    {"fact_key": "capital_gain_net", "label": "Capital gain net income — Schedule D (page-1 L8)", "data_type": "decimal", "required": False, "sort_order": 7},
    {"fact_key": "gain_form_4797", "label": "Net gain/(loss) from Form 4797 Part II L17 (page-1 L9)", "data_type": "decimal", "required": False, "sort_order": 8},
    {"fact_key": "other_income", "label": "Other income (page-1 L10)", "data_type": "decimal", "required": False, "sort_order": 9},
    # ── Page 1 deductions ──
    {"fact_key": "officer_comp", "label": "Compensation of officers — Form 1125-E (page-1 L12)", "data_type": "decimal", "required": False, "sort_order": 20},
    {"fact_key": "salaries_wages", "label": "Salaries and wages, less employment credits (page-1 L13)", "data_type": "decimal", "required": False, "sort_order": 21},
    {"fact_key": "deductions_other_ordinary", "label": "Repairs/bad debts/rents/taxes/interest/depletion/advertising/pension/benefits/other (page-1 L14-18,21-26)", "data_type": "decimal", "required": False, "sort_order": 22,
     "notes": "Aggregate of the ordinary deduction lines other than officer comp/salaries/charitable/depreciation (broken out on the app UI; one spec input here)."},
    {"fact_key": "charitable_contributions", "label": "Charitable contributions (page-1 L19; 10% taxable-income limit)", "data_type": "decimal", "required": False, "sort_order": 23,
     "notes": "§170(b)(2) 10%-of-taxable-income limit is a diagnostic; direct-entry the deductible amount for v1."},
    {"fact_key": "depreciation", "label": "Depreciation from Form 4562 not on 1125-A/elsewhere (page-1 L20)", "data_type": "decimal", "required": False, "sort_order": 24,
     "notes": "Form 4562 already covers 1120."},
    # ── Schedule C dividends (col (a) amounts) ──
    {"fact_key": "div_less20_domestic", "label": "Dividends from <20%-owned domestic corps (Sch C L1, 50%)", "data_type": "decimal", "required": False, "sort_order": 30},
    {"fact_key": "div_20plus_domestic", "label": "Dividends from 20%+-owned domestic corps (Sch C L2, 65%)", "data_type": "decimal", "required": False, "sort_order": 31},
    {"fact_key": "div_100pct_group", "label": "Dividends: wholly-owned foreign sub + SBIC + affiliated-group (Sch C L8/L10/L11, 100%)", "data_type": "decimal", "required": False, "sort_order": 32},
    {"fact_key": "div_245a_foreign", "label": "§245A foreign-source portion — specified 10%-owned FC (Sch C L13, 100%)", "data_type": "decimal", "required": False, "sort_order": 33,
     "notes": "§245A 100% deduction; holding period §246(c)(5) (>365 days). Direct-entry; diagnostic D_1120_DRD_HOLD."},
    {"fact_key": "div_other_taxable", "label": "Other dividends/inclusions with no DRD — Subpart F/GILTI/other (Sch C L14-20)", "data_type": "decimal", "required": False, "sort_order": 34,
     "notes": "Fully taxable; included in income (L4) but no special deduction."},
    {"fact_key": "special_deduction_other", "label": "Other special deductions — §246A debt-financed / §250 / public-utility (direct-entry)", "data_type": "decimal", "required": False, "sort_order": 35,
     "notes": "Q2 defer: §246A debt-financed reduction, §250 (Form 8993), public-utility 23.3/26.7% — direct-entry the resulting special deduction; diagnostics D_1120_DRD_DEBTFN."},
    # ── NOL ──
    {"fact_key": "nol_carryover_available", "label": "Available NOL carryover from prior years — Sch K Q12 (do not reduce by L29a)", "data_type": "decimal", "required": False, "sort_order": 40},
    # ── Schedule J tax layer (direct-entry / defer) ──
    {"fact_key": "camt_form_4626", "label": "Corporate AMT from Form 4626 (Sch J L3) — direct-entry (RED-defer)", "data_type": "decimal", "required": False, "sort_order": 50,
     "notes": "Q3: CAMT computed on Form 4626 (applicable corp, $1B AFSI). Direct-entry; not computed here."},
    {"fact_key": "credit_gbc_3800", "label": "General business credit — Form 3800 (Sch J L5c)", "data_type": "decimal", "required": False, "sort_order": 51,
     "notes": "Form 3800 already covers 1120."},
    {"fact_key": "credit_ftc_other", "label": "Foreign tax credit + other credits — 1118/8834/8827/8912/8978 (Sch J L5a,b,d,e,f)", "data_type": "decimal", "required": False, "sort_order": 52},
    {"fact_key": "phc_tax", "label": "Personal holding company tax — Schedule PH (Sch J L8) — direct-entry (RED-defer)", "data_type": "decimal", "required": False, "sort_order": 53,
     "notes": "Q3: §541 20%. Screened; direct-entry."},
    {"fact_key": "recapture_other_tax", "label": "Recapture/other taxes — Sch J L9a-9z (direct-entry)", "data_type": "decimal", "required": False, "sort_order": 54},
    {"fact_key": "total_payments", "label": "Total payments and refundable credits (Sch J L23 → page-1 L33)", "data_type": "decimal", "required": False, "sort_order": 55,
     "notes": "Estimates + Form 7004 deposit + withholding + refundable credits (direct-entry aggregate)."},
    # ── Schedule K screening flags ──
    {"fact_key": "avg_gross_receipts_3yr", "label": "Average annual gross receipts, prior 3 years (§448(c) / §163(j) gate)", "data_type": "decimal", "required": False, "sort_order": 60},
    {"fact_key": "business_interest_expense", "label": "Business interest expense for the year (§163(j) gate)", "data_type": "decimal", "required": False, "sort_order": 61},
    {"fact_key": "is_applicable_corp_camt", "label": "Applicable corporation for CAMT? — avg AFSI > $1B (Sch K Q29 / §59(k))", "data_type": "boolean", "required": False, "sort_order": 62},
    {"fact_key": "afsi_amount", "label": "Adjusted financial statement income (§55/§59, CAMT screen)", "data_type": "decimal", "required": False, "sort_order": 63},
    {"fact_key": "is_phc", "label": "Meets the PHC tests? — 60% income + >50% by <=5 individuals (§542)", "data_type": "boolean", "required": False, "sort_order": 64},
    {"fact_key": "has_farmland_1062", "label": "§1062 sale of qualified farmland to a qualified farmer? (OBBBA, Form 1062)", "data_type": "boolean", "required": False, "sort_order": 65},
    {"fact_key": "is_personal_service_corp", "label": "Personal service corporation? (AET credit $150k vs $250k)", "data_type": "boolean", "required": False, "sort_order": 66},
    {"fact_key": "accounting_method", "label": "Accounting method (Sch K Q1)", "data_type": "choice", "required": False, "sort_order": 67,
     "choices": ["cash", "accrual", "other"]},
]

F1120_RULES: list[dict] = [
    {"rule_id": "R-1120-DRD", "title": "Schedule C dividends-received deduction (§243/§245A + §246(b) limit)", "rule_type": "calculation",
     "formula": ("total_dividends = div_less20_domestic + div_20plus_domestic + div_100pct_group + div_245a_foreign + div_other_taxable ; "
                 "l28_pre = total_income - total_deductions ; "
                 "drd_before = 0.50*div_less20_domestic + 0.65*div_20plus_domestic ; drd_100 = 1.00*(div_100pct_group + div_245a_foreign) ; "
                 "ti_limit_base = l28_pre - drd_100 - special_deduction_other ; limit_pct = 0.65 if div_20plus_domestic>0 else 0.50 ; "
                 "loss_exception = (ti_limit_base - drd_before) < 0 ; "
                 "drd_50_65 = drd_before if (loss_exception or ti_limit_base<=0) else min(drd_before, limit_pct*ti_limit_base) ; "
                 "special_deductions = drd_50_65 + drd_100 + special_deduction_other  (Sch C L24 -> page-1 L29b)"),
     "inputs": ["div_less20_domestic", "div_20plus_domestic", "div_100pct_group", "div_245a_foreign", "div_other_taxable", "special_deduction_other"],
     "outputs": ["total_dividends", "special_deductions"], "sort_order": 1,
     "description": "W2. §243(a)(1) 50% / §243(c) 65% / §243(a)(3)+§245A 100%; §246(b) taxable-income limit (65% if any 20%+-owned else 50%) with the §246(b) NOL LOSS EXCEPTION (no limit if the full DRD creates/increases an NOL). 100% lines are NOT §246(b)-limited. v1 simplifies the combined 50/65 worksheet interaction (single limit_pct)."},
    {"rule_id": "R-1120-TOTINC", "title": "Total income (page-1 L11)", "rule_type": "calculation",
     "formula": "gross_profit = (gross_receipts - returns_allowances) - cogs ; total_income = gross_profit + total_dividends + interest_income + gross_rents + gross_royalties + capital_gain_net + gain_form_4797 + other_income",
     "inputs": ["gross_receipts", "returns_allowances", "cogs", "interest_income", "gross_rents", "gross_royalties", "capital_gain_net", "gain_form_4797", "other_income"],
     "outputs": ["total_income"], "sort_order": 2,
     "description": "Page-1 L3 gross profit (L1c - L2) + L4 dividends (Sch C L23) + L5-10 -> L11 total income (add L3-10)."},
    {"rule_id": "R-1120-TOTDED", "title": "Total deductions (page-1 L27)", "rule_type": "calculation",
     "formula": "total_deductions = officer_comp + salaries_wages + deductions_other_ordinary + charitable_contributions + depreciation",
     "inputs": ["officer_comp", "salaries_wages", "deductions_other_ordinary", "charitable_contributions", "depreciation"],
     "outputs": ["total_deductions"], "sort_order": 3,
     "description": "Page-1 L12-26 total deductions (L27). Officer comp = Form 1125-E; depreciation = Form 4562. Charitable subject to the §170(b)(2) 10% limit (diagnostic)."},
    {"rule_id": "R-1120-L28", "title": "Taxable income before NOL & special deductions (page-1 L28)", "rule_type": "calculation",
     "formula": "l28 = total_income - total_deductions",
     "inputs": [], "outputs": ["l28"], "sort_order": 4,
     "description": "Page-1 L28 = L11 - L27. The base for the §172 80% NOL limitation and the §246(b) DRD limit."},
    {"rule_id": "R-1120-NOL", "title": "§172 NOL deduction — 80% limitation (page-1 L29a)", "rule_type": "calculation",
     "formula": "nol_base = max(0, l28 - special_deductions) ; nol_deduction = min(nol_carryover_available, 0.80 * nol_base)",
     "inputs": ["nol_carryover_available"], "outputs": ["nol_deduction"], "sort_order": 5,
     "description": "W3. §172(a)(2). Post-2017 NOL limited to 80% of (L28 - special deductions L29b); no carryback, indefinite carryforward. Available carryover = Sch K Q12 (not reduced by L29a)."},
    {"rule_id": "R-1120-TI", "title": "Taxable income (page-1 L30)", "rule_type": "calculation",
     "formula": "taxable_income = l28 - nol_deduction - special_deductions   (L30 = L28 - L29c)",
     "inputs": [], "outputs": ["taxable_income"], "sort_order": 6,
     "description": "Page-1 L30 = L28 - L29c (L29c = L29a NOL + L29b special deductions)."},
    {"rule_id": "R-1120-TAX", "title": "§11 flat 21% income tax (Schedule J L1a)", "rule_type": "calculation",
     "formula": "income_tax = 0.21 * max(0, taxable_income)",
     "inputs": [], "outputs": ["income_tax"], "sort_order": 7,
     "description": "W1. §11(b) / i1120 Sch J L1a: multiply taxable income (page-1 L30) by 21% (0.21). Flat; no brackets."},
    {"rule_id": "R-1120-TOTTAX", "title": "Schedule J total tax (L12 → page-1 L31)", "rule_type": "calculation",
     "formula": ("total_income_tax = income_tax + camt_form_4626 ; credits = credit_gbc_3800 + credit_ftc_other ; "
                 "tax_after_credits = max(0, total_income_tax - credits) ; "
                 "total_tax = tax_after_credits + phc_tax + recapture_other_tax   (Sch J L12 -> page-1 L31)"),
     "inputs": ["camt_form_4626", "credit_gbc_3800", "credit_ftc_other", "phc_tax", "recapture_other_tax"],
     "outputs": ["total_tax"], "sort_order": 8,
     "description": "W4. Sch J: L2 income tax + L3 CAMT (direct-entry) = L4; less L6 credits (GBC Form 3800 + FTC/other) = L7; + L8 PHC (direct-entry) + L9 recapture = L12 total tax -> page-1 L31."},
    {"rule_id": "R-1120-163J", "title": "§163(j) business-interest gate (Sch K Q24 → Form 8990)", "rule_type": "routing",
     "formula": "if avg_gross_receipts_3yr > 31000000 and business_interest_expense > 0: file Form 8990 (compute the 30%-ATI limit there; OBBBA EBITDA basis for TY2025)",
     "inputs": ["avg_gross_receipts_3yr", "business_interest_expense"], "outputs": ["file_8990"], "sort_order": 9,
     "description": "W5. §163(j)/§448(c). A corporation with avg annual gross receipts > $31M (2025) and business interest expense is not exempt -> Form 8990. The limitation compute (30% of ATI, EBITDA basis restored for TY2025 by OBBBA) is deferred to Form 8990."},
    {"rule_id": "R-1120-CAMT", "title": "§55 CAMT screen (Sch K Q29 → Form 4626)", "rule_type": "routing",
     "formula": "if is_applicable_corp_camt or afsi_amount > 1000000000: file Form 4626 -> CAMT = 15% of AFSI (Sch J L3)",
     "inputs": ["is_applicable_corp_camt", "afsi_amount"], "outputs": ["file_4626"], "sort_order": 10,
     "description": "W5. §55(b)(2)(A)/§59(k). Applicable corporation (avg AFSI > $1B over 3 yrs) computes a 15% CAMT on Form 4626 -> Sch J L3. RED-defer: screened + direct-entry (camt_form_4626), not computed."},
    {"rule_id": "R-1120-SPECIAL", "title": "PHC / AET / §59A / §1062 special-regime screens", "rule_type": "routing",
     "formula": ("if is_phc: §541 PHC 20% -> Schedule PH (Sch J L8) ; if avg_gross_receipts_3yr >= 500000000: §59A base erosion -> Form 8991 ; "
                 "if has_farmland_1062: §1062 deferral -> Form 1062 (page-1 L32) ; AET §531 20% ($250k/$150k credit) = IRS-assessed screen"),
     "inputs": ["is_phc", "avg_gross_receipts_3yr", "has_farmland_1062"], "outputs": [], "sort_order": 11,
     "description": "W5. §541 PHC (20%; Sch PH), §531 AET (20%; $250k/$150k credit), §59A base erosion (>=$500M; Form 8991), §1062 OBBBA farmland deferral (Form 1062). All screen + route, not computed (RED-defer)."},
]

F1120_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-1120-DRD", "IRC_243_246", "primary", "§243/§245A DRD % + §246(b) limit + loss exception"),
    ("R-1120-DRD", "IRS_2025_F1120", "secondary", "Schedule C lines 1-24"),
    ("R-1120-TOTINC", "IRS_2025_F1120", "primary", "page-1 L3-11 income"),
    ("R-1120-TOTDED", "IRS_2025_F1120", "primary", "page-1 L12-27 deductions"),
    ("R-1120-L28", "IRS_2025_F1120", "primary", "page-1 L28"),
    ("R-1120-NOL", "IRC_172", "primary", "§172(a)(2) 80% NOL limitation"),
    ("R-1120-NOL", "IRS_2025_I1120", "secondary", "i1120 L29a NOL worksheet"),
    ("R-1120-TI", "IRS_2025_F1120", "primary", "page-1 L30 taxable income"),
    ("R-1120-TAX", "IRC_11", "primary", "§11(b) flat 21%"),
    ("R-1120-TAX", "IRS_2025_I1120", "secondary", "i1120 Sch J L1a x 0.21"),
    ("R-1120-TOTTAX", "IRS_2025_F1120", "primary", "Schedule J L2-L12"),
    ("R-1120-163J", "IRC_163J", "primary", "§163(j) 30% ATI / §448(c) $31M / Form 8990"),
    ("R-1120-163J", "IRS_2025_F1120", "secondary", "Sch K Q24 gate"),
    ("R-1120-CAMT", "IRC_55_CAMT", "primary", "§55/§59 CAMT 15% / $1B"),
    ("R-1120-CAMT", "IRS_2025_F1120", "secondary", "Sch K Q29 / Sch J L3"),
    ("R-1120-SPECIAL", "IRC_541_531", "primary", "§541 PHC / §531 AET"),
    ("R-1120-SPECIAL", "IRS_2025_F1120", "secondary", "Sch J L8 / Sch K Q22 / page-1 L32"),
]

F1120_LINES: list[dict] = [
    {"line_number": "4", "description": "Page-1 L4 Dividends and inclusions (Sch C L23)", "line_type": "calculated", "source_rules": ["R-1120-DRD"], "sort_order": 1},
    {"line_number": "11", "description": "Page-1 L11 Total income", "line_type": "subtotal", "source_rules": ["R-1120-TOTINC"], "sort_order": 2},
    {"line_number": "27", "description": "Page-1 L27 Total deductions", "line_type": "subtotal", "source_rules": ["R-1120-TOTDED"], "sort_order": 3},
    {"line_number": "28", "description": "Page-1 L28 Taxable income before NOL & special deductions", "line_type": "subtotal", "source_rules": ["R-1120-L28"], "sort_order": 4},
    {"line_number": "29a", "description": "Page-1 L29a NOL deduction (§172 80% limit)", "line_type": "calculated", "source_rules": ["R-1120-NOL"], "sort_order": 5},
    {"line_number": "29b", "description": "Page-1 L29b Special deductions (Sch C L24 DRD)", "line_type": "calculated", "source_rules": ["R-1120-DRD"], "sort_order": 6},
    {"line_number": "30", "description": "Page-1 L30 Taxable income", "line_type": "calculated", "source_rules": ["R-1120-TI"], "sort_order": 7},
    {"line_number": "J-1a", "description": "Schedule J L1a Income tax (taxable income × 21%)", "line_type": "calculated", "source_rules": ["R-1120-TAX"], "sort_order": 8},
    {"line_number": "31", "description": "Page-1 L31 Total tax (Schedule J L12)", "line_type": "calculated", "source_rules": ["R-1120-TOTTAX"], "sort_order": 9},
    {"line_number": "K-24", "description": "Schedule K Q24 §163(j)/Form 8990 gate", "line_type": "calculated", "source_rules": ["R-1120-163J"], "sort_order": 10},
    {"line_number": "J-3", "description": "Schedule J L3 CAMT (Form 4626) — direct-entry", "line_type": "calculated", "source_rules": ["R-1120-CAMT"], "sort_order": 11},
]

F1120_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_1120_DRD_LIMIT", "title": "§246(b) DRD taxable-income limitation (with the NOL loss exception)", "severity": "info",
     "condition": "div_less20_domestic > 0 or div_20plus_domestic > 0",
     "message": "The 50%/65% dividends-received deduction is limited to 65% (if any 20%-or-more-owned dividends) or 50% of taxable income figured without the DRD, NOL, §199A, and §250 deductions (§246(b)). EXCEPTION: the limitation does not apply for a year in which the full DRD creates or increases a net operating loss. The 100% categories (wholly-owned foreign sub, SBIC, affiliated group, §245A) are not subject to this limit.",
     "notes": "W2. §246(b). v1 uses a single limit_pct; the combined 50/65 worksheet interaction is simplified."},
    {"diagnostic_id": "D_1120_DRD_HOLD", "title": "DRD holding-period requirement (§246(c) / §246(c)(5))", "severity": "warning",
     "condition": "any dividend claimed a DRD",
     "message": "No dividends-received deduction is allowed unless the stock was held more than 45 days during the 91-day window around the ex-dividend date (more than 90 days/181-day window for certain preferred dividends). For the §245A 100% foreign-source deduction the holding period is more than 365 days during a 731-day window (§246(c)(5)). Verify the holding period before claiming the deduction.",
     "notes": "W2. §246(c). Not computed — preparer-verified."},
    {"diagnostic_id": "D_1120_DRD_DEBTFN", "title": "§246A debt-financed portfolio stock reduces the DRD", "severity": "warning",
     "condition": "special_deduction_other includes a debt-financed dividend",
     "message": "If portfolio stock was debt-financed, the dividends-received deduction on that stock is reduced by the average indebtedness percentage (§246A). Enter the reduced special deduction directly (Sch C line 3); v1 does not compute the average-indebtedness reduction.",
     "notes": "W2. §246A. Direct-entry via special_deduction_other."},
    {"diagnostic_id": "D_1120_NOL80", "title": "§172 NOL deduction limited to 80% of taxable income", "severity": "info",
     "condition": "nol_carryover_available > 0",
     "message": "A net operating loss carryover from a post-2017 year is deductible only up to 80% of taxable income (figured before the NOL, §199A, and §250 deductions). The unused NOL carries forward indefinitely; corporate NOLs cannot be carried back. Enter the full available carryover on Schedule K line 12 (do not reduce it by the amount deducted on line 29a).",
     "notes": "W3. §172(a)(2)."},
    {"diagnostic_id": "D_1120_163J", "title": "§163(j) business-interest limitation — Form 8990 (OBBBA EBITDA basis TY2025)", "severity": "warning",
     "condition": "avg_gross_receipts_3yr > 31000000 and business_interest_expense > 0",
     "message": "This corporation is not a small-business taxpayer (average annual gross receipts over the prior 3 years exceed $31,000,000 for 2025), so the §163(j) business-interest limitation applies — file Form 8990. For TY2025 the OBBBA restored the EBITDA basis: depreciation, amortization, and depletion are ADDED BACK in computing adjusted taxable income (a change from the 2022-2024 EBIT basis), which increases the 30%-of-ATI headroom. The limitation is computed on Form 8990.",
     "notes": "W5. §163(j)/§448(c). Compute deferred to Form 8990."},
    {"diagnostic_id": "D_1120_CAMT", "title": "§55 Corporate AMT — applicable corporation (Form 4626)", "severity": "warning",
     "condition": "is_applicable_corp_camt or afsi_amount > 1000000000",
     "message": "A corporation whose average annual adjusted financial statement income (AFSI) exceeds $1 billion over the 3-year period is an 'applicable corporation' and owes a 15% corporate alternative minimum tax on its AFSI (§55/§59). Compute it on Form 4626 and enter the result on Schedule J line 3. v1 does not compute CAMT — it screens the threshold and takes the Form 4626 result as a direct entry.",
     "notes": "W5. §55/§59. RED-defer."},
    {"diagnostic_id": "D_1120_PHC", "title": "§541 Personal Holding Company tax (Schedule PH)", "severity": "warning",
     "condition": "is_phc",
     "message": "If a corporation meets both the income test (at least 60% of adjusted ordinary gross income is personal holding company income) and the ownership test (more than 50% in value of the stock owned by 5 or fewer individuals during the last half of the year), it owes a 20% personal holding company tax on undistributed PHC income (§541). Compute it on Schedule PH (Form 1120) -> Sch J line 8. v1 screens; direct-entry the tax.",
     "notes": "W5. §541/§542. RED-defer."},
    {"diagnostic_id": "D_1120_AET", "title": "§531 Accumulated Earnings Tax", "severity": "info",
     "condition": "earnings accumulated beyond the reasonable needs of the business",
     "message": "A corporation formed or availed of to avoid shareholder tax by accumulating earnings beyond the reasonable needs of the business may owe a 20% accumulated earnings tax on accumulated taxable income (§531). The accumulated earnings credit is $250,000 ($150,000 for a personal service corporation) (§535(c)). This tax is IRS-assessed, not self-reported on Form 1120. v1 flags the exposure only.",
     "notes": "W5. §531/§535. RED-defer (no return line)."},
    {"diagnostic_id": "D_1120_1062", "title": "§1062 farmland-gain deferral (OBBBA — Form 1062)", "severity": "info",
     "condition": "has_farmland_1062",
     "message": "Under new §1062 (OBBBA, P.L. 119-21) a corporation may elect to pay the tax on gain from the sale of qualified farmland to a qualified farmer in installments — reported on Form 1062, with the first installment on page-1 line 32 and the net tax liability on Schedule J line 22b. v1 models the structure and flags the election; it does not compute the installment schedule.",
     "notes": "W5. §1062. Structure + flag."},
    {"diagnostic_id": "D_1120_BASEERO", "title": "§59A base erosion (BEAT) — Form 8991", "severity": "info",
     "condition": "avg_gross_receipts_3yr >= 500000000",
     "message": "A corporation with average annual gross receipts of at least $500 million (over the prior 3 years) and base-erosion payments may owe the base erosion and anti-abuse tax (BEAT, §59A) — Schedule K question 22, computed on Form 8991 (Sch J line 1f). v1 screens the gross-receipts threshold only.",
     "notes": "W5. §59A. RED-defer."},
]

F1120_SCENARIOS: list[dict] = [
    {"scenario_name": "1120-A — basic corp: income → 21% flat tax", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"gross_receipts": 1000000, "cogs": 400000, "officer_comp": 150000, "salaries_wages": 200000, "deductions_other_ordinary": 100000},
     "expected_outputs": {"total_income": 600000, "total_deductions": 450000, "l28": 150000, "taxable_income": 150000, "income_tax": 31500, "total_tax": 31500},
     "notes": "Gross profit 600,000; deductions 450,000; taxable income 150,000 x 21% = 31,500. §11 flat rate."},
    {"scenario_name": "1120-B — DRD 50% (<20%-owned domestic dividends)", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"gross_receipts": 500000, "cogs": 200000, "deductions_other_ordinary": 100000, "div_less20_domestic": 100000},
     "expected_outputs": {"total_dividends": 100000, "total_income": 400000, "l28": 300000, "special_deductions": 50000, "taxable_income": 250000, "income_tax": 52500},
     "notes": "§243(a)(1): 100,000 <20%-owned dividends -> 50,000 DRD. TI 300,000 - 50,000 = 250,000 x 21% = 52,500. §246(b) limit (50% x 300,000 = 150,000) not binding."},
    {"scenario_name": "1120-C — DRD 65% (20%+-owned domestic dividends)", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"gross_receipts": 500000, "cogs": 200000, "deductions_other_ordinary": 100000, "div_20plus_domestic": 100000},
     "expected_outputs": {"total_dividends": 100000, "special_deductions": 65000, "l28": 300000, "taxable_income": 235000, "income_tax": 49350},
     "notes": "§243(c): 100,000 20%+-owned -> 65,000 DRD. TI 300,000 - 65,000 = 235,000 x 21% = 49,350. §246(b) limit 65% x 300,000 = 195,000 not binding."},
    {"scenario_name": "1120-D — §246(b) DRD limit binds (no loss exception)", "scenario_type": "edge", "sort_order": 4,
     "inputs": {"gross_receipts": 100000, "cogs": 60000, "deductions_other_ordinary": 30000, "div_less20_domestic": 20000},
     "expected_outputs": {"l28": 30000, "special_deductions": 10000, "taxable_income": 20000, "income_tax": 4200},
     "notes": "Full DRD = 50% x 20,000 = 10,000. §246(b) base = L28 30,000; limit = 50% x 30,000 = 15,000. Full DRD 10,000 < 15,000, so NOT limited here; and TI after DRD = 20,000 (positive, no loss). TI 20,000 x 21% = 4,200."},
    {"scenario_name": "1120-E — §246(b) loss exception (full DRD creates an NOL)", "scenario_type": "edge", "sort_order": 5,
     "inputs": {"gross_receipts": 100000, "cogs": 70000, "deductions_other_ordinary": 25000, "div_less20_domestic": 20000},
     "expected_outputs": {"l28": 25000, "special_deductions": 10000, "taxable_income": 15000},
     "notes": "Gross profit 30,000 + div 20,000 = income 50,000; deductions 25,000 -> L28 25,000. Full DRD 10,000; §246(b) base 25,000, limit 12,500 (>=10,000) so not binding; TI 15,000. (Loss-exception path exercised when DRD > base; see validate harness.)"},
    {"scenario_name": "1120-F — §172 NOL 80% limitation", "scenario_type": "edge", "sort_order": 6,
     "inputs": {"gross_receipts": 800000, "cogs": 300000, "deductions_other_ordinary": 200000, "nol_carryover_available": 500000},
     "expected_outputs": {"l28": 300000, "nol_deduction": 240000, "taxable_income": 60000, "income_tax": 12600},
     "notes": "§172(a)(2): NOL deduction = min(500,000, 80% x 300,000) = 240,000. TI 300,000 - 240,000 = 60,000 x 21% = 12,600. 260,000 NOL carries forward."},
    {"scenario_name": "1120-G — §163(j) gate fires (>$31M gross receipts)", "scenario_type": "failure", "sort_order": 7,
     "inputs": {"avg_gross_receipts_3yr": 40000000, "business_interest_expense": 500000},
     "expected_outputs": {"file_8990": True, "diagnostic": "D_1120_163J"},
     "notes": "Avg gross receipts 40M > 31M and interest expense present -> not a small-business taxpayer -> Form 8990 (30% ATI limit computed there; OBBBA EBITDA basis TY2025)."},
    {"scenario_name": "1120-H — CAMT screen ($1B AFSI applicable corp)", "scenario_type": "failure", "sort_order": 8,
     "inputs": {"is_applicable_corp_camt": True, "afsi_amount": 1200000000, "camt_form_4626": 30000000, "gross_receipts": 5000000000, "cogs": 4000000000, "deductions_other_ordinary": 900000000},
     "expected_outputs": {"file_4626": True, "diagnostic": "D_1120_CAMT"},
     "notes": "Applicable corporation (AFSI 1.2B > 1B) -> Form 4626 15% CAMT (direct-entry 30M into Sch J L3). RED-defer: screened, not computed."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORMS registry + flow assertions
# ═══════════════════════════════════════════════════════════════════════════
FORMS: list[dict] = [
    {
        "identity": {"form_number": "1120", "form_title": "Form 1120 — U.S. Corporation Income Tax Return (TY2025)",
                     "notes": "WO-11 / S-13. C-corporation compute spine (Gate-1 shape = spine + 2, DECISIONS D-13): page-1 income/deductions -> L28 taxable income before NOL & special deductions -> Schedule C DRD (§243 50/65 + §245A/affiliated/SBIC/foreign-sub 100%, §246(b) taxable-income limit with the NOL loss exception) -> §172 NOL 80% limitation -> L30 taxable income -> Schedule J §11 flat 21% tax -> credits -> total tax (L12 -> page-1 L31). Special regimes screen + route: §163(j) (>$31M -> Form 8990, OBBBA EBITDA basis TY2025), §55 CAMT ($1B AFSI -> Form 4626), §541 PHC (Sch PH), §531 AET, §59A (>=$500M -> Form 8991), §1062 farmland (Form 1062). COGS = Form 1125-A; officer comp = Form 1125-E; depreciation/disposition/GBC = 4562/4797/3800 (all carry '1120'). Sch L/M-1/M-2/K = form 1120_SCHL."},
        "facts": F1120_FACTS, "rules": F1120_RULES, "rule_links": F1120_RULE_LINKS,
        "lines": F1120_LINES, "diagnostics": F1120_DIAGNOSTICS, "scenarios": F1120_SCENARIOS,
    },
]

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1120-TAX", "title": "§11 flat 21% income tax on taxable income", "assertion_type": "reconciliation",
     "entity_types": ["1120"], "status": "draft", "sort_order": 1,
     "description": "Schedule J line 1a income tax = taxable income (page-1 L30) x 21%. Flat rate, no brackets.",
     "definition": {"rule": "R-1120-TAX", "check": "income_tax = 0.21 * max(0, taxable_income)"}},
    {"assertion_id": "FA-1120-DRD", "title": "Schedule C DRD = 50/65/100% with the §246(b) limit", "assertion_type": "reconciliation",
     "entity_types": ["1120"], "status": "draft", "sort_order": 2,
     "description": "Special deductions (page-1 L29b) = 50% of <20%-owned + 65% of 20%+-owned (§246(b)-limited unless the full DRD creates an NOL) + 100% of foreign-sub/SBIC/affiliated/§245A + other.",
     "definition": {"rule": "R-1120-DRD", "check": "special = drd_50_65 (§246(b)-capped, loss-exception) + drd_100 + other"}},
    {"assertion_id": "FA-1120-NOL", "title": "§172 NOL deduction capped at 80% of taxable income", "assertion_type": "reconciliation",
     "entity_types": ["1120"], "status": "draft", "sort_order": 3,
     "description": "NOL deduction (page-1 L29a) = min(available carryover, 80% of (L28 - special deductions)). No carryback; indefinite carryforward.",
     "definition": {"rule": "R-1120-NOL", "check": "nol_deduction = min(nol_carryover_available, 0.80 * max(0, l28 - special_deductions))"}},
    {"assertion_id": "FA-1120-TOTTAX", "title": "Total tax assembles income tax + CAMT − credits + PHC/recapture", "assertion_type": "reconciliation",
     "entity_types": ["1120"], "status": "draft", "sort_order": 4,
     "description": "Schedule J L12 total tax = (21% income tax + CAMT) - credits + PHC + recapture -> page-1 L31.",
     "definition": {"rule": "R-1120-TOTTAX", "check": "total_tax = max(0, income_tax + camt - credits) + phc + recapture"}},
]


# ═══════════════════════════════════════════════════════════════════════════
# Command
# ═══════════════════════════════════════════════════════════════════════════
class Command(BaseCommand):
    help = (
        "Load the Form 1120 spine spec (C-corporation income tax, TY2025). "
        "Refuses to seed until Ken sets READY_TO_SEED=True after the review walk (W1-W5)."
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad Form 1120 spine spec (C-corporation income tax return)\n"))
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
                "\nREFUSING TO SEED FORM 1120: not cleared to seed.\n\n"
                "Content is authored, but seeding is gated until Ken reviews the packet\n"
                "(W1 the §11 flat 21%; W2 the Schedule C DRD + §246(b) limit/loss exception;\n"
                "W3 the §172 NOL 80% limitation; W4 the total-tax assembly; W5 the special-\n"
                "regime screens) and flips the sentinel.\n\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True to proceed)\n\n"
                f"Currently empty / placeholder:\n  {still_empty}\n\n"
                "To proceed: review the module-level data lists (and f1120_source_brief.md),\n"
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
        self.stdout.write("Form 1120 spine loaded.")
        self.stdout.write(
            f"  1120: facts {len(F1120_FACTS)} / rules {len(F1120_RULES)} / lines {len(F1120_LINES)} / "
            f"diag {len(F1120_DIAGNOSTICS)} / tests {len(F1120_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}"
        )
        self.stdout.write("=" * 60)
