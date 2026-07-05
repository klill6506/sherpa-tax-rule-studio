"""Load the Form 1041 spine spec — U.S. Income Tax Return for Estates and Trusts (TY2025).

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
Form 1041 is the fiduciary income tax return. This loader seeds ONE consolidated
`1041` form covering the three tightly-coupled physical pages:
  • PAGE 1  — income (L1-9), deductions (L10-16), adjusted total income (L17),
    the distribution/exemption block (L18-22), taxable income (L23), total tax (L24).
  • SCHEDULE B (page 2) — the DNI / Income Distribution Deduction engine
    (§643(a) DNI → the §651/§661 deduction, capped at DNI via the L15 smaller-of).
  • SCHEDULE G (page 2) — tax computation (rate schedule / cap-gain worksheet;
    ESBT separate tax L4; §1411 NIIT L5; credits; total tax → page-1 L24).

They are one form because L18 IDD ← Sch B L15 and L24 tax ← Sch G L9. The
beneficiary K-1 (`SCHEDULE_K1_1041`) and GA Form 501 (`GA501`) are separate legs.

Greenfield: no prior 1041 spec (lookup/1041/ → 404 at the 2026-07-05 gap-check).

═══════════════════════════════════════════════════════════════════════════
v1 SCOPE — LOCKED (Ken's Gate-1 walk 2026-07-05; DECISIONS D-10). See f1041_source_brief.md.
═══════════════════════════════════════════════════════════════════════════
COMPUTES (v1):
  • Core 4 entity types — decedent's estate, simple trust, complex trust, QDisT —
    full page-1 → Sch B → Sch G → tax, with the §642(b) exemption by type.
  • ESBT — the S-portion separate tax at the top trust rate → Sch G Part I L4.
  • The FULL distribution engine (Dec Q2): §643(a) DNI; §651/§661 IDD capped at
    DNI (Sch B L15 smaller-of L13/L14); §662 two-tier allocation (L9 first-tier /
    L10 second-tier, DNI applied tier-1-first); §663(c) separate-share DNI; the
    §663(b) 65-day election (Question 6); proportional character retention to beneficiaries.
  • Schedule G: rate-schedule tax (or the cap-gain 0/15/20% path when net cap gain /
    qualified dividends present); §1411 NIIT (Form 8960 L21 → Sch G L5, threshold $15,650).
DIRECT-ENTRY (line exists, diagnostic prompts) — Dec Q3:
  • Capital gains IN DNI (Sch B L3) — the preparer enters gains attributable to
    income / treated-as-distributed; the three Reg. §1.643(a)-3(b) circumstances are a
    diagnostic (default = corpus-excluded per §643(a)(3)). The instrument + local law drive it.
  • Form 8960 NIIT amount (L5); the Schedule A charitable deduction (L13); credits (Sch G L2).
STRUCTURE + FLAG (no compute):
  • Grantor-type trust → grantor-letter reporting path (entity info only, NO K-1) — D_1041_GRANTOR.
  • Pooled income fund → routed to the Form 5227 leg (WO-10); does NOT complete Sch B — D_1041_PIF.
  • OBBBA §1062 qualified-farmland 4-installment election (Form 1062, page-1 L25b / Sch G 18c) — D_1041_1062.
RED-DEFERS (loud diagnostic, no silent gap):
  • Schedule I AMT (D-2, ruled 2026-07-04) — D_1041_AMT. Do NOT author the compute.
  • Bankruptcy estate (ch. 7/11) — essentially an individual 1040 — D_1041_BANKR.
  • Accumulation distribution / Schedule J throwback — D_1041_SCHJ.

═══════════════════════════════════════════════════════════════════════════
requires_human_review WALK ITEMS (Ken's in-session review before seeding)
═══════════════════════════════════════════════════════════════════════════
W1. TY2025 CONSTANTS — §1(e) rate schedule (10/24/35/37%, top bracket $15,650), §642(b)
    exemptions ($600/$300/$100, QDisT $5,100), cap-gain breakpoints ($3,250/$15,900),
    NIIT threshold ($15,650). ALL verified verbatim vs FINAL 2025 Form 1041 + i1041 (Mar 5
    2026) + Rev. Proc. 2024-40. Rev. Proc. 2025-32 confirmed = TY2026 (does NOT touch 2025). CONFIRM.
W2. DISTRIBUTION ENGINE DEPTH — Dec Q2 = FULL (§662 tiers + §663(c) separate-share + §663(b)
    65-day + character). The separate-share + multi-tier compute is the heaviest surface; if a
    real return needs per-share data the spec can't reach, that sub-leg falls back to structured
    diagnostic (a reconcile-leg call). CONFIRM the modeling.
W3. CAP-GAINS-IN-DNI = direct-entry + 3-circumstance diagnostic (Dec Q3). Default corpus-excluded.
    Sch B L3 is preparer-entered; the §1.643(a)-3(b) determination hinges on the governing
    instrument + local law the spec cannot read. CONFIRM the direct-entry choice.
W4. ESBT — the S-portion is taxed separately at the top trust rate via the ESBT Tax Worksheet →
    Sch G L4. v1 computes a simplified top-rate ESBT tax on a direct-entered S-portion taxable
    income; the full worksheet (separate NII, cap-gain rates within the S-portion) is a later
    refinement. CONFIRM the simplification.
W5. Line numbering mapped to the FINAL 2025 f1041 face (page-1 L1-24 incl. QBI L20 / exemption
    L21; Sch B L1-15; Sch G Part I L1a-9). §1062 (L25b) is OBBBA-new — structure + flag only.

═══════════════════════════════════════════════════════════════════════════
VERIFIED STRUCTURE + CONSTANTS (READ 2026-07-05 from FINAL 2025 IRS sources — NOT memory:
Form 1041 Created 10/28/25; i1041 Mar 5 2026; Sch K-1 Created 5/2/25; Rev. Proc. 2024-40;
IRC §643/651/661/662/663/642(b)/1(e)/1411; Reg. §1.643(a)-3. Full brief: f1041_source_brief.md.)
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
# FLIPPED 2026-07-05 — Ken APPROVED the review walk in-session ("Approve — flip,
# seed, export"): W1 the TY2025 constants (rate schedule / exemptions / cap-gain /
# NIIT, verified verbatim; Rev. Proc. 2025-32 = TY2026), W2 the full §662/§663
# distribution engine, W3 the cap-gains-in-DNI direct-entry + 3-circumstance
# diagnostic, W4 the simplified ESBT top-rate tax (full worksheet deferred),
# W5 the line numbering — all blessed. Validated on throwaway SQLite
# (scratchpad/validate_1041.py, 17 pass / 0 fail; 35 facts / 15 rules / 39 lines /
# 11 diag / 9 tests / 6 FA, every rule cited).
# ═══════════════════════════════════════════════════════════════════════════
READY_TO_SEED = True


FORM_JURISDICTION = "federal"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1041"]


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED TY2025 CONSTANTS (year-keyed; cited in f1041_source_brief.md; never memory)
# ═══════════════════════════════════════════════════════════════════════════

# §1(e) estate & trust rate schedule (Rev. Proc. 2024-40 Table 5; re-confirmed i1041
# "2025 Tax Rate Schedule"). Tuples: (bracket floor, base tax at floor, marginal rate).
RATE_SCHEDULE_2025: list[tuple[int, str, str]] = [
    (0,      "0",     "0.10"),
    (3150,   "315",   "0.24"),
    (11450,  "2307",  "0.35"),
    (15650,  "3777",  "0.37"),
]

# §642(b) exemptions by entity type (i1041 What's New; QDisT per Rev. Proc. 2024-40 §2.35).
EXEMPTION_2025: dict[str, int] = {
    "estate": 600,
    "simple_trust": 300,
    "complex_trust": 100,
    "qdist": 5100,          # qualified disability trust — not subject to phaseout
    # ESBT: the S-portion computes with no exemption; the non-S portion uses its base type.
}

# Maximum capital-gains rate breakpoints for estates & trusts (Rev. Proc. 2024-40 §2.03).
CAPGAIN_0_CEILING_2025 = 3250      # 0% up to this
CAPGAIN_15_CEILING_2025 = 15900    # 15% up to this; 20% above

# §1411 NIIT threshold for a trust/estate = start of the top §1(e) bracket (i1041 / i8960).
NIIT_THRESHOLD_2025 = 15650
NIIT_RATE = "0.038"

# Bankruptcy estate (ch. 7/11) gross-income filing threshold (i1041 What's New).
BANKRUPTCY_FILING_THRESHOLD_2025 = 15750


def _rate_schedule_tax(taxable_income: int) -> int:
    """2025 §1(e) compressed schedule (ordinary path; cap-gain path handled separately).

    Rounds half-UP to the nearest dollar (IRS convention), not Python's banker's rounding.
    """
    import math
    ti = max(0, taxable_income)
    floor, base, rate = 0, 0.0, 0.10
    for f, b, r in RATE_SCHEDULE_2025:
        if ti >= f:
            floor, base, rate = f, float(b), float(r)
    return int(math.floor(base + (ti - floor) * rate + 0.5))


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY TOPICS / SOURCES
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("fiduciary_income_tax", "Form 1041 estates & trusts: §643(a) DNI; §651/§661 distribution "
     "deduction capped at DNI; §662 tiers / §663(c) separate-share / §663(b) 65-day; Schedule G "
     "tax (rate schedule, ESBT L4, §1411 NIIT); §1(e) rate schedule + §642(b) exemptions."),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []  # spine is self-owned; K-1 leg reuses these

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_F1041",
        "source_type": "federal_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "US",
        "title": "2025 Form 1041 — U.S. Income Tax Return for Estates and Trusts",
        "citation": "Form 1041 (2025), Cat. No. 11370H, Created 10/28/25",
        "issuer": "Internal Revenue Service",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f1041.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.8,
        "topics": ["fiduciary_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "Page 1 — income, deductions, distribution block (2025 verbatim)",
                "excerpt_text": (
                    "Section A 'Check all that apply' (9 types): Decedent's estate; Simple trust; Complex "
                    "trust; Qualified disability trust; ESBT (S portion only); Grantor type trust; Bankruptcy "
                    "estate-Ch. 7; Bankruptcy estate-Ch. 11; Pooled income fund. INCOME: L1 Interest; L2a "
                    "Total ordinary dividends; L2b Qualified dividends allocable to (1) beneficiaries / (2) "
                    "estate or trust; L3 Business income (Sch C); L4 Capital gain (Sch D); L5 Rents, "
                    "royalties, partnerships, other estates & trusts (Sch E); L6 Farm (Sch F); L7 Ordinary "
                    "gain (4797); L8 Other income; L9 Total income (combine L1, 2a, 3-8). DEDUCTIONS: L10 "
                    "Interest; L11 Taxes; L12 Fiduciary fees (if only a portion deductible under §67(e), see "
                    "instructions); L13 Charitable deduction (Sch A L7); L14 Attorney/accountant/return-"
                    "preparer fees (§67(e) cue); L15a Other deductions (§67(e) cue); L15b NOL; L16 Add L10-"
                    "15b; L17 Adjusted total income (L9-L16); L18 Income distribution deduction (Sch B L15); "
                    "L19 Estate tax deduction; L20 Qualified business income deduction (8995/8995-A); L21 "
                    "Exemption; L22 Add L18-21; L23 Taxable income (L17-L22); L24 Total tax (Sch G Part I L9). "
                    "L25b OBBBA §1062 first installment (Form 1062 L15)."
                ),
                "summary_text": "Form 1041 (2025) page 1: 9 entity-type checkboxes; income L1-9; deductions L10-16; adjusted total income L17; distribution/exemption block L18-22; taxable income L23; total tax L24.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule B (Income Distribution Deduction) L1-15 (2025 verbatim)",
                "excerpt_text": (
                    "L1 Adjusted total income (see instructions); L2 Adjusted tax-exempt interest; L3 Total "
                    "net gain from Sch D line 19 col (1); L4 Enter amount from Sch A line 4 (minus allocable "
                    "§1202 exclusion); L5 Capital gains for the tax year included on Sch A line 1; L6 Enter "
                    "any gain from page 1 line 4 as a NEGATIVE (or a page-1-line-4 loss as a positive); L7 "
                    "Distributable net income — combine L1-6, if zero or less enter -0-; L8 If a complex "
                    "trust, enter accounting income; L9 Income required to be distributed currently; L10 "
                    "Other amounts paid, credited, or otherwise required to be distributed; L11 Total "
                    "distributions (add L9+L10; if greater than L8 see instructions); L12 Tax-exempt income "
                    "included on L11; L13 Tentative IDD (L11-L12); L14 Tentative IDD (L7-L2, if zero or less "
                    "-0-); L15 Income distribution deduction — enter the SMALLER of L13 or L14, here and on "
                    "page 1 line 18."
                ),
                "summary_text": "Schedule B: DNI on L7 (combine L1-6); IDD on L15 = smaller of L13 (distributions net of tax-exempt) or L14 (DNI net of adjusted tax-exempt interest) → page-1 L18. The DNI limitation.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule G Part I (Tax Computation) L1a-9 (2025 verbatim)",
                "excerpt_text": (
                    "L1a Tax (see instructions — 2025 Tax Rate Schedule, or Sch D Tax Worksheet / Qualified "
                    "Dividends Tax Worksheet when net cap gain / qualified dividends, or Sch J for an "
                    "accumulation distribution); L1b Tax on lump-sum distributions (Form 4972); L1c "
                    "Alternative minimum tax (Sch I line 54); L1d Form 4255 Part I; L1e Total L1a-1d; L2a "
                    "Foreign tax credit (1116); L2b General business credit (3800); L2c Prior year minimum "
                    "tax (8801); L2d Bond credits (8912); L2e Total credits; L3 Subtract L2e from L1e; L4 Tax "
                    "on the ESBT portion of the trust (from ESBT Tax Worksheet line 17); L5 Net investment "
                    "income tax from Form 8960 line 21; L6a-c recapture; L7 Household employment taxes; L8 "
                    "Other taxes; L9 Total tax (add L3-8) → page 1 line 24."
                ),
                "summary_text": "Schedule G Part I: L1a tax (rate schedule / cap-gain worksheet); L4 ESBT separate tax; L5 NIIT (Form 8960 L21); L9 total tax → page-1 L24.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "2025 §1(e) Tax Rate Schedule + exemptions + cap-gain breakpoints (i1041 What's New)",
                "excerpt_text": (
                    "2025 Tax Rate Schedule (estates & trusts): $0-$3,150 = 10%; over $3,150 = $315 + 24% of "
                    "excess; over $11,450 = $2,307 + 35% of excess; over $15,650 = $3,777 + 37% of excess. "
                    "Exemption: decedent's estate $600; simple trust $300; complex trust $100; qualified "
                    "disability trust $5,100 (not subject to phaseout). Capital gains: 0% up to $3,250; 15% "
                    "over $3,250 up to $15,900; 20% above $15,900. Bankruptcy estate files if gross income >= "
                    "$15,750. §1411 NIIT threshold = the dollar amount at which the highest §1(e) bracket "
                    "begins ($15,650 for 2025)."
                ),
                "summary_text": "TY2025: rate 10/24/35/37% (top at $15,650); exemptions $600/$300/$100/$5,100 (QDisT); cap-gain 0/15/20% at $3,250/$15,900; NIIT threshold $15,650.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_I1041",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "US",
        "title": "2025 Instructions for Form 1041 and Schedules A, B, G, J, and K-1",
        "citation": "Instructions for Form 1041 (2025), Cat. No. 11372D, dated Mar 5, 2026",
        "issuer": "Internal Revenue Service",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i1041.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.8,
        "topics": ["fiduciary_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "Tiers, separate share, 65-day, character (i1041 pp.31-33, 44)",
                "excerpt_text": (
                    "Line 9 'first-tier distributions' (income required to be distributed currently) are "
                    "deductible to the extent of DNI; the beneficiary includes them to the extent of their "
                    "proportionate share of DNI. Line 10 'second-tier distributions' (any other amounts paid, "
                    "credited, or required to be distributed — incl. discretionary corpus and in-kind) are "
                    "included by the beneficiary only to the extent of the EXCESS of DNI over the income "
                    "required to be distributed currently (DNI applied to tier 1 first, then tier 2; Reg. "
                    "§§1.652(c)-4, 1.662(c)-4). Separate share rule (§663(c)): if a single trust/estate has "
                    "beneficiaries with substantially separate and independent shares, the shares are treated "
                    "as separate trusts/estates for the SOLE purpose of determining DNI allocable to the "
                    "respective beneficiaries. 65-day election (§663(b)): a fiduciary of a complex trust or "
                    "decedent's estate may elect to treat amounts paid or credited within 65 days after the "
                    "close of the tax year as paid or credited on the last day of that year (checkbox at "
                    "Question 6; irrevocable). Character: the beneficiary's income has the same proportion of "
                    "each class of items entering DNI that the total of each class has to DNI. Directly "
                    "attributable deductions first; indirect deductions allocated with a reasonable portion "
                    "to tax-exempt; the charitable deduction ratably apportioned among each class."
                ),
                "summary_text": "§662 tiers (L9 first / L10 second, DNI applied tier-1-first); §663(c) separate-share DNI; §663(b) 65-day election (Q6, irrevocable); character retention proportional by DNI class.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule B line computations + ESBT / grantor / PIF (i1041 pp.13-14, 31-33, 43)",
                "excerpt_text": (
                    "Sch B L1 Adjusted total income = generally page-1 L17 (if both page-1 L4 and L17 are "
                    "losses, enter the SMALLER loss; if L4 is zero/gain and L17 a loss, enter zero; simple "
                    "trust subtracts extraordinary/taxable stock dividends allocable to corpus). L2 Adjusted "
                    "tax-exempt interest = tax-exempt interest minus (Sch A L2 tax-exempt allocated to "
                    "charity + §212 expenses allocable + interest expense allocable to tax-exempt). L8 skip "
                    "for a decedent's estate or a simple trust (complex trust only). L12 removes the tax-"
                    "exempt portion of distributions (fraction distributions/DNI when distributions < DNI). "
                    "ESBT (S portion only) is taxed separately at the highest trust rate via the ESBT Tax "
                    "Worksheet flowing to Sch G Part I line 4. Grantor type trusts do NOT use Schedule K-1 "
                    "and don't show dollar amounts on the form itself — dollars go on an attachment (grantor "
                    "letter). Pooled income funds do NOT complete Schedule B (attach a statement; file Form 5227)."
                ),
                "summary_text": "Sch B L1 from page-1 L17 (loss-netting rules); L2 adjusted tax-exempt interest; L8 complex-trust-only; ESBT separate tax → Sch G L4; grantor = grantor letter (no K-1); PIF skips Sch B (Form 5227).",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_SUBCHAPTER_J",
        "source_type": "statute",
        "source_rank": "controlling",
        "jurisdiction_code": "US",
        "title": "IRC §§642(b), 643(a), 651, 661, 662, 663 — estates, trusts, and beneficiaries",
        "citation": "26 U.S.C. §§642(b), 643(a), 651, 661, 662, 663",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/643",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["fiduciary_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "§643(a) DNI modifications; §651/§661 deduction; §642(b) exemption",
                "excerpt_text": (
                    "§643(a) DNI = taxable income with modifications: (1) no §651/§661 distribution "
                    "deduction; (2) no §642(b) personal exemption; (3) capital gains excluded to the extent "
                    "allocated to corpus and not paid/credited/required to be distributed nor set aside for "
                    "§642(c) charity (losses excluded except to offset included gains); (4) simple-trust "
                    "extraordinary/taxable stock dividends allocable to corpus excluded; (5) tax-exempt "
                    "interest INCLUDED, reduced by §265-disallowed expenses and the §642(c) portion; (6) "
                    "foreign trust adjustments; (7) anti-abuse. §651 (simple trust): deduction for income "
                    "required to be distributed currently, capped at DNI. §661 (estate/complex trust): "
                    "deduction for (a)(1) amounts required to be distributed currently PLUS (a)(2) other "
                    "amounts properly paid/credited/required, capped at DNI. §642(b) exemption: $600 estate, "
                    "$300 simple trust ('required to distribute all income'), $100 complex trust; QDisT gets "
                    "a personal-exemption-equivalent ($5,100 for 2025)."
                ),
                "summary_text": "§643(a): DNI = taxable income + add back distribution deduction + exemption, exclude corpus cap gains, include tax-exempt interest net of §265/§642(c). §651/§661 deduction capped at DNI. §642(b) exemptions $600/$300/$100.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§662 tiers; §663(b) 65-day; §663(c) separate share",
                "excerpt_text": (
                    "§662(a): a beneficiary includes (1) the amount of income required to be distributed "
                    "currently (first tier), limited to their proportionate share of DNI, and (2) all other "
                    "amounts properly paid/credited/required (second tier), limited to the excess of DNI over "
                    "the first-tier amounts. §663(b): amounts paid or credited within the first 65 days of "
                    "the following tax year may be elected to be treated as paid/credited on the last day of "
                    "the preceding tax year (complex trust / decedent's estate; irrevocable election). "
                    "§663(c): substantially separate and independent shares of different beneficiaries are "
                    "treated as separate trusts/estates solely for determining DNI allocable to the "
                    "respective beneficiaries."
                ),
                "summary_text": "§662 two-tier beneficiary inclusion (DNI to tier 1 first); §663(b) 65-day election; §663(c) separate-share DNI.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "REG_1_643_A_3",
        "source_type": "regulation",
        "source_rank": "controlling",
        "jurisdiction_code": "US",
        "title": "Treas. Reg. §1.643(a)-3 — Capital gains and losses (inclusion in DNI)",
        "citation": "26 CFR §1.643(a)-3(b)",
        "issuer": "U.S. Department of the Treasury",
        "official_url": "https://www.law.cornell.edu/cfr/text/26/1.643(a)-3",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.3,
        "topics": ["fiduciary_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "Three circumstances capital gains ARE in DNI — §1.643(a)-3(b)",
                "excerpt_text": (
                    "Capital gains are ordinarily EXCLUDED from DNI (§1.643(a)-3(a)). They ARE included to "
                    "the extent that, pursuant to the terms of the governing instrument and applicable local "
                    "law, or a reasonable and impartial exercise of discretion by the fiduciary, they are: "
                    "(1) allocated to income (with the unitrust-consistency caveat where local law defines "
                    "income as a unitrust amount); (2) allocated to corpus but treated consistently by the "
                    "fiduciary on its books, records, and tax returns as part of a distribution to a "
                    "beneficiary; or (3) allocated to corpus but actually distributed to the beneficiary or "
                    "utilized by the fiduciary in determining the amount distributed or required to be "
                    "distributed to a beneficiary."
                ),
                "summary_text": "Corpus capital gains enter DNI only if (1) allocated to income, (2) consistently treated as part of a distribution, or (3) actually distributed / used in determining the distribution — instrument + local law + reasonable discretion.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_1411_NIIT",
        "source_type": "statute",
        "source_rank": "controlling",
        "jurisdiction_code": "US",
        "title": "IRC §1411 + Form 8960 — Net Investment Income Tax (estates and trusts)",
        "citation": "26 U.S.C. §1411; 2025 Instructions for Form 8960",
        "issuer": "U.S. Congress / Internal Revenue Service",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/1411",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.3,
        "topics": ["fiduciary_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "§1411 NIIT on estates & trusts — 2025 threshold $15,650",
                "excerpt_text": (
                    "An estate or trust owes the 3.8% net investment income tax on the LESSER of (a) its "
                    "undistributed net investment income, or (b) the excess of its adjusted gross income over "
                    "the dollar amount at which the highest §1(e) tax bracket begins. For 2025 that threshold "
                    "is $15,650. Computed on Form 8960; the result (Form 8960 line 21) flows to Form 1041 "
                    "Schedule G Part I line 5."
                ),
                "summary_text": "Trust/estate NIIT = 3.8% × lesser of (undistributed NII) or (AGI − $15,650 for 2025); Form 8960 L21 → Sch G L5.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "RP_2024_40",
        "source_type": "revenue_procedure",
        "source_rank": "primary_official",
        "jurisdiction_code": "US",
        "title": "Rev. Proc. 2024-40 — 2025 inflation-adjusted amounts (estates & trusts)",
        "citation": "Rev. Proc. 2024-40, §§2.03, 2.35, Table 5",
        "issuer": "Internal Revenue Service",
        "official_url": "https://www.irs.gov/pub/irs-drop/rp-24-40.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["fiduciary_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "Governs TY2025 (NOT Rev. Proc. 2025-32, which is TY2026)",
                "excerpt_text": (
                    "Rev. Proc. 2024-40 provides the TY2025 inflation adjustments: Table 5 (§1(j)(2)(E) "
                    "estates & trusts) the 10/24/35/37% schedule with breakpoints $3,150/$11,450/$15,650; "
                    "§2.03 the estate/trust maximum capital gains rate amounts $3,250 (0% ceiling) / $15,900 "
                    "(15% ceiling); §2.35 the §642(b)(2)(C)(i) qualified disability trust exemption $5,100. "
                    "Rev. Proc. 2025-32 (issued after OBBBA) provides the TY2026 figures and does NOT alter "
                    "these 2025 amounts — the FINAL 2025 Form 1041 instructions re-confirm them verbatim."
                ),
                "summary_text": "Rev. Proc. 2024-40 is the governing TY2025 procedure for the rate schedule, cap-gain breakpoints, and QDisT exemption; 2025-32 is TY2026 and leaves 2025 unchanged.",
                "is_key_excerpt": True,
            },
        ],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_F1041", "1041", "governs"),
    ("IRS_2025_I1041", "1041", "governs"),
    ("IRC_SUBCHAPTER_J", "1041", "governs"),
    ("REG_1_643_A_3", "1041", "governs"),
    ("IRC_1411_NIIT", "1041", "governs"),
    ("RP_2024_40", "1041", "governs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM — 1041 spine (page 1 + Schedule B + Schedule G)
# ═══════════════════════════════════════════════════════════════════════════

F1041_FACTS: list[dict] = [
    # Entity type + elections
    {"fact_key": "entity_type", "label": "Entity type (Form 1041 page-1 Section A)", "data_type": "choice", "required": True, "sort_order": 1,
     "choices": ["estate", "simple_trust", "complex_trust", "qdist", "esbt", "grantor", "pooled_income_fund", "bankruptcy_ch7", "bankruptcy_ch11"],
     "notes": "Dec Q1. Core 4 (estate/simple/complex/qdist) + ESBT computed; grantor=structure; PIF→5227; bankruptcy=RED-defer."},
    {"fact_key": "sec645_election", "label": "§645 election — QRT treated as part of the estate (box G(1))", "data_type": "boolean", "required": False, "sort_order": 2},
    {"fact_key": "sec663b_65day_election", "label": "§663(b) 65-day election — treat early-following-year distributions as prior-year (Question 6)", "data_type": "boolean", "required": False, "sort_order": 3,
     "notes": "Dec Q2. Complex trust / decedent's estate only; irrevocable."},
    {"fact_key": "separate_share_applies", "label": "§663(c) separate-share rule applies (substantially separate & independent beneficiary shares)?", "data_type": "boolean", "required": False, "sort_order": 4,
     "notes": "Dec Q2. When True, DNI is determined per share."},
    # Page-1 INCOME (L1-8)
    {"fact_key": "interest_income", "label": "Interest income (page-1 L1)", "data_type": "decimal", "required": False, "sort_order": 10},
    {"fact_key": "ordinary_dividends", "label": "Total ordinary dividends (page-1 L2a)", "data_type": "decimal", "required": False, "sort_order": 11},
    {"fact_key": "qualified_dividends", "label": "Qualified dividends (page-1 L2b)", "data_type": "decimal", "required": False, "sort_order": 12,
     "notes": "Subset of L2a; drives the cap-gain worksheet path in Sch G L1a."},
    {"fact_key": "business_income", "label": "Business income/(loss) — Sch C (page-1 L3)", "data_type": "decimal", "required": False, "sort_order": 13},
    {"fact_key": "capital_gain", "label": "Capital gain/(loss) — Sch D (page-1 L4)", "data_type": "decimal", "required": False, "sort_order": 14},
    {"fact_key": "rents_royalties_passthrough", "label": "Rents, royalties, partnerships, other estates & trusts — Sch E (page-1 L5)", "data_type": "decimal", "required": False, "sort_order": 15},
    {"fact_key": "farm_income", "label": "Farm income/(loss) — Sch F (page-1 L6)", "data_type": "decimal", "required": False, "sort_order": 16},
    {"fact_key": "ordinary_gain_4797", "label": "Ordinary gain/(loss) — Form 4797 (page-1 L7)", "data_type": "decimal", "required": False, "sort_order": 17},
    {"fact_key": "other_income", "label": "Other income (page-1 L8)", "data_type": "decimal", "required": False, "sort_order": 18},
    # Page-1 DEDUCTIONS (L10-15b, 19-20)
    {"fact_key": "interest_deduction", "label": "Interest deduction (page-1 L10)", "data_type": "decimal", "required": False, "sort_order": 20},
    {"fact_key": "taxes", "label": "Taxes (page-1 L11)", "data_type": "decimal", "required": False, "sort_order": 21},
    {"fact_key": "fiduciary_fees", "label": "Fiduciary fees — §67(e)-deductible portion (page-1 L12)", "data_type": "decimal", "required": False, "sort_order": 22,
     "notes": "Enter only the §67(e) administration portion (costs that would not have been incurred but for the trust/estate). Bundled-fee split is a preparer determination — D_1041_67E."},
    {"fact_key": "charitable_deduction", "label": "Charitable deduction — Schedule A line 7 (page-1 L13, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 23},
    {"fact_key": "attorney_accountant_fees", "label": "Attorney, accountant, return-preparer fees — §67(e) portion (page-1 L14)", "data_type": "decimal", "required": False, "sort_order": 24},
    {"fact_key": "other_deductions_67e", "label": "Other deductions allowable under §67(e) (page-1 L15a)", "data_type": "decimal", "required": False, "sort_order": 25},
    {"fact_key": "nol_deduction", "label": "Net operating loss deduction (page-1 L15b)", "data_type": "decimal", "required": False, "sort_order": 26},
    {"fact_key": "estate_tax_deduction", "label": "Estate tax deduction incl. certain GST taxes (page-1 L19)", "data_type": "decimal", "required": False, "sort_order": 27},
    {"fact_key": "qbi_deduction", "label": "Qualified business income deduction — Form 8995/8995-A (page-1 L20, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 28},
    # Schedule B distribution inputs
    {"fact_key": "accounting_income", "label": "Fiduciary accounting income — complex trust (Sch B L8)", "data_type": "decimal", "required": False, "sort_order": 40,
     "notes": "Complex trust only; skip for a decedent's estate or simple trust (§643(b) FAI per the governing instrument + local law)."},
    {"fact_key": "income_required_distributed", "label": "Income required to be distributed currently — first tier (Sch B L9)", "data_type": "decimal", "required": False, "sort_order": 41,
     "notes": "Dec Q2. §662(a)(1). For a simple trust = all income."},
    {"fact_key": "other_amounts_distributed", "label": "Other amounts paid, credited, or required to be distributed — second tier (Sch B L10)", "data_type": "decimal", "required": False, "sort_order": 42,
     "notes": "Dec Q2. §662(a)(2). Discretionary/corpus/in-kind distributions."},
    {"fact_key": "tax_exempt_interest", "label": "Tax-exempt interest received (§103)", "data_type": "decimal", "required": False, "sort_order": 43},
    {"fact_key": "tax_exempt_expenses_allocable", "label": "Expenses allocable to tax-exempt income (§265 / §642(c) portion)", "data_type": "decimal", "required": False, "sort_order": 44,
     "notes": "Reduces adjusted tax-exempt interest (Sch B L2) per Reg. §1.643(a)-5 / §1.265-1."},
    {"fact_key": "tax_exempt_in_distributions", "label": "Tax-exempt income included in distributions (Sch B L12)", "data_type": "decimal", "required": False, "sort_order": 45},
    {"fact_key": "capital_gains_in_dni", "label": "Capital gains attributable to income / treated as distributed — Sch B L3 (direct-entry)", "data_type": "decimal", "required": False, "sort_order": 46,
     "notes": "Dec Q3. Default 0 (corpus-excluded, §643(a)(3)). Preparer enters per the three §1.643(a)-3(b) circumstances — D_1041_CG_DNI."},
    # Schedule G inputs
    {"fact_key": "esbt_s_portion_taxable_income", "label": "ESBT S-portion taxable income (for the separate top-rate tax → Sch G L4, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 60,
     "notes": "Dec Q1/W4. ESBT S-portion is taxed separately at the top trust rate; v1 simplifies the ESBT Tax Worksheet."},
    {"fact_key": "lump_sum_tax_4972", "label": "Tax on lump-sum distributions — Form 4972 (Sch G L1b, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 61},
    {"fact_key": "total_credits_schg", "label": "Total credits — FTC/GBC/prior-year-min-tax/bond (Sch G L2e, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 62},
    {"fact_key": "niit_form8960", "label": "Net investment income tax — Form 8960 line 21 (Sch G L5, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 63,
     "notes": "3.8% × lesser of undistributed NII or (AGI − $15,650). Computed on Form 8960; direct-entered here. D_1041_NIIT."},
    {"fact_key": "other_taxes_schg", "label": "Other taxes + household employment (Sch G L6-8, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 64},
    {"fact_key": "sec1062_installment", "label": "OBBBA §1062 first installment — qualified farmland (page-1 L25b, Form 1062, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 65,
     "notes": "OBBBA-new, low frequency. Structure + flag only — D_1041_1062."},
]

F1041_RULES: list[dict] = [
    {"rule_id": "R-1041-TOTINC", "title": "Total income (page-1 L9)", "rule_type": "calculation",
     "formula": "L9 = interest_income + ordinary_dividends + business_income + capital_gain + rents_royalties_passthrough + farm_income + ordinary_gain_4797 + other_income",
     "inputs": ["interest_income", "ordinary_dividends", "business_income", "capital_gain", "rents_royalties_passthrough", "farm_income", "ordinary_gain_4797", "other_income"],
     "outputs": ["L9"], "sort_order": 10,
     "description": "f1041 page-1 L9 = combine L1, 2a, and 3-8. (Qualified dividends L2b is a subset of L2a, not separately added.)"},
    {"rule_id": "R-1041-TOTDED", "title": "Total deductions (page-1 L16)", "rule_type": "calculation",
     "formula": "L16 = interest_deduction + taxes + fiduciary_fees + charitable_deduction + attorney_accountant_fees + other_deductions_67e + nol_deduction",
     "inputs": ["interest_deduction", "taxes", "fiduciary_fees", "charitable_deduction", "attorney_accountant_fees", "other_deductions_67e", "nol_deduction"],
     "outputs": ["L16"], "sort_order": 11,
     "description": "f1041 page-1 L16 = add L10-15b. §67(e) fees (L12/14/15a) are the administration-portion only (§67(g) suspends 2% misc; §67(e) costs remain deductible)."},
    {"rule_id": "R-1041-ATI", "title": "Adjusted total income (page-1 L17)", "rule_type": "calculation",
     "formula": "L17 = L9 - L16",
     "inputs": [], "outputs": ["L17"], "sort_order": 12,
     "description": "f1041 page-1 L17 = L9 − L16. Feeds Schedule B L1 (with the loss-netting rule) and is the base for GA Form 501 L1."},
    {"rule_id": "R-1041-DNI", "title": "Distributable net income (Schedule B L7) — §643(a)", "rule_type": "calculation",
     "formula": ("SchB_L1 = adjusted_total_income (L17, loss-netted) ; "
                 "SchB_L2 = max(0, tax_exempt_interest - tax_exempt_expenses_allocable) ; "
                 "SchB_L3 = capital_gains_in_dni (direct-entry) ; "
                 "SchB_L6 = -capital_gain (back out page-1 L4 corpus gains) ; "
                 "DNI (L7) = max(0, SchB_L1 + SchB_L2 + SchB_L3 + SchB_L4 - SchB_L5 + SchB_L6)"),
     "inputs": ["capital_gains_in_dni", "tax_exempt_interest", "tax_exempt_expenses_allocable", "capital_gain"],
     "outputs": ["SchB_L2", "SchB_L7_DNI"], "sort_order": 13,
     "description": "§643(a): start from taxable income, add back the distribution deduction + §642(b) exemption (implicit in starting from L17 pre-L18/L21), include tax-exempt interest net of §265/§642(c) (L2), EXCLUDE corpus capital gains (L6 backs out page-1 L4) except those attributable to income (L3 direct-entry). If zero or less, -0-."},
    {"rule_id": "R-1041-IDD", "title": "Income distribution deduction (Sch B L15 → page-1 L18)", "rule_type": "calculation",
     "formula": ("total_distributions (L11) = income_required_distributed + other_amounts_distributed ; "
                 "L13 = total_distributions - tax_exempt_in_distributions ; "
                 "L14 = max(0, SchB_L7_DNI - SchB_L2) ; "
                 "IDD (L15) = min(L13, L14) -> page-1 L18"),
     "inputs": ["income_required_distributed", "other_amounts_distributed", "tax_exempt_in_distributions"],
     "outputs": ["SchB_L15_IDD", "L18"], "sort_order": 14,
     "description": "§651/§661 deduction capped at DNI. L15 = SMALLER of L13 (distributions net of tax-exempt) or L14 (DNI net of adjusted tax-exempt interest). The DNI limitation is the core of Subchapter J."},
    {"rule_id": "R-1041-TIERS", "title": "§662 two-tier beneficiary allocation (DNI to tier 1 first)", "rule_type": "calculation",
     "formula": ("dni_for_beneficiaries = SchB_L7_DNI - SchB_L2 (taxable DNI) ; "
                 "tier1_included = min(income_required_distributed, dni_for_beneficiaries) ; "
                 "tier2_included = min(other_amounts_distributed, max(0, dni_for_beneficiaries - income_required_distributed)) ; "
                 "each beneficiary's inclusion = their proportionate share of the applicable tier"),
     "inputs": ["income_required_distributed", "other_amounts_distributed"],
     "outputs": ["tier1_included", "tier2_included"], "sort_order": 15,
     "description": "Dec Q2. §662(a): first-tier (L9) included up to proportionate DNI share; second-tier (L10) included up to the EXCESS of DNI over first-tier (Reg. §§1.652(c)-4, 1.662(c)-4)."},
    {"rule_id": "R-1041-SEPSHARE", "title": "§663(c) separate-share DNI determination", "rule_type": "conditional",
     "formula": "if separate_share_applies: compute DNI per substantially-separate-and-independent share; a deduction/loss of one share is NOT available to another. Applies for the SOLE purpose of allocating DNI.",
     "inputs": ["separate_share_applies"], "outputs": ["per_share_dni"], "sort_order": 16,
     "description": "Dec Q2. §663(c). Prevents a distribution to one beneficiary from carrying out DNI attributable to another share's income."},
    {"rule_id": "R-1041-65DAY", "title": "§663(b) 65-day election", "rule_type": "conditional",
     "formula": "if sec663b_65day_election and entity_type in (complex_trust, estate): amounts paid/credited within 65 days after year-end are treated as distributed on the last day of the prior year (increase L10, up to DNI).",
     "inputs": ["sec663b_65day_election", "entity_type"], "outputs": ["other_amounts_distributed"], "sort_order": 17,
     "description": "Dec Q2. §663(b). Irrevocable; complex trust / decedent's estate only. Shifts that income's taxation to the beneficiary in the earlier year."},
    {"rule_id": "R-1041-CHAR", "title": "Character retention of DNI classes to beneficiaries", "rule_type": "calculation",
     "formula": "each beneficiary's share of each income class (interest / dividends / cap gain / tax-exempt / business) = (class amount in DNI / DNI) x beneficiary's DNI inclusion. Directly-attributable deductions net against their class first; indirect allocated with a reasonable portion to tax-exempt; charitable ratably apportioned.",
     "inputs": [], "outputs": ["k1_character_by_class"], "sort_order": 18,
     "description": "i1041 p.44. Feeds the SCHEDULE_K1_1041 leg (boxes 1-8 by class). No losses in boxes 1-8."},
    {"rule_id": "R-1041-EXEMPT", "title": "§642(b) exemption (page-1 L21)", "rule_type": "calculation",
     "formula": "L21 = {estate:600, simple_trust:300, complex_trust:100, qdist:5100}[entity_type]  (ESBT S-portion: 0)",
     "inputs": ["entity_type"], "outputs": ["L21"], "sort_order": 19,
     "description": "§642(b); QDisT $5,100 per Rev. Proc. 2024-40 §2.35 (not subject to phaseout). A simple trust ('required to distribute all income') = $300; complex = $100."},
    {"rule_id": "R-1041-TAXINC", "title": "Taxable income (page-1 L23)", "rule_type": "calculation",
     "formula": "L22 = L18 (IDD) + estate_tax_deduction + qbi_deduction + L21 (exemption) ; L23 = max(0, L17 - L22)",
     "inputs": ["estate_tax_deduction", "qbi_deduction"], "outputs": ["L22", "L23"], "sort_order": 20,
     "description": "f1041 page-1: L22 = add L18-21; L23 = L17 − L22. Note the QBI deduction (L20) sits inside the distribution/exemption block, unlike a 1040."},
    {"rule_id": "R-1041-TAX", "title": "Tax on taxable income (Sch G L1a)", "rule_type": "calculation",
     "formula": ("if (qualified_dividends > 0 or net_capital_gain > 0): use the cap-gain worksheet — 0% up to "
                 "$3,250, 15% up to $15,900, 20% above, ordinary portion at the rate schedule ; "
                 "else: rate schedule = 10% <=$3,150; $315+24% <=$11,450; $2,307+35% <=$15,650; $3,777+37% above"),
     "inputs": ["qualified_dividends", "capital_gain"], "outputs": ["SchG_L1a"], "sort_order": 21,
     "description": "W1. §1(e) compressed schedule (Rev. Proc. 2024-40 Table 5). The Sch D / Qualified Dividends Tax Worksheet applies the 0/15/20% preferential rates when net cap gain or qualified dividends are present."},
    {"rule_id": "R-1041-ESBT", "title": "ESBT separate tax (Sch G L4)", "rule_type": "calculation",
     "formula": "if entity_type == esbt: SchG_L4 = top-rate tax on esbt_s_portion_taxable_income (37% on the S-portion, per the ESBT Tax Worksheet line 17)",
     "inputs": ["entity_type", "esbt_s_portion_taxable_income"], "outputs": ["SchG_L4"], "sort_order": 22,
     "description": "Dec Q1 / W4. The ESBT S-portion is taxed separately at the highest trust rate and added at Sch G Part I line 4 (v1 simplifies the full worksheet — see W4)."},
    {"rule_id": "R-1041-NIIT", "title": "§1411 NIIT (Sch G L5)", "rule_type": "calculation",
     "formula": "SchG_L5 = niit_form8960  (= 3.8% x lesser of undistributed NII or (AGI - 15650); computed on Form 8960 line 21)",
     "inputs": ["niit_form8960"], "outputs": ["SchG_L5"], "sort_order": 23,
     "description": "§1411. Threshold = start of the top §1(e) bracket = $15,650 for 2025. Direct-entered from Form 8960 L21."},
    {"rule_id": "R-1041-TOTTAX", "title": "Total tax (Sch G L9 → page-1 L24)", "rule_type": "calculation",
     "formula": ("SchG_L1e = SchG_L1a + lump_sum_tax_4972 + amt_sch_i(RED-defer=0) ; "
                 "SchG_L3 = max(0, SchG_L1e - total_credits_schg) ; "
                 "SchG_L9 = SchG_L3 + SchG_L4 (ESBT) + SchG_L5 (NIIT) + other_taxes_schg -> page-1 L24"),
     "inputs": ["lump_sum_tax_4972", "total_credits_schg", "other_taxes_schg"], "outputs": ["SchG_L9", "L24"], "sort_order": 24,
     "description": "Sch G Part I total. Sch I AMT (L1c) is RED-deferred to zero (D-2); if AMT indicators present, D_1041_AMT fires."},
]

F1041_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-1041-TOTINC", "IRS_2025_F1041", "primary", "page-1 L9 total income (face arithmetic)"),
    ("R-1041-TOTDED", "IRS_2025_F1041", "primary", "page-1 L16 total deductions"),
    ("R-1041-TOTDED", "IRS_2025_I1041", "secondary", "§67(e) administration-portion deductibility"),
    ("R-1041-ATI", "IRS_2025_F1041", "primary", "page-1 L17 adjusted total income = L9 − L16"),
    ("R-1041-DNI", "IRC_SUBCHAPTER_J", "primary", "§643(a) DNI modifications"),
    ("R-1041-DNI", "IRS_2025_F1041", "secondary", "Schedule B L1-7 face computation"),
    ("R-1041-DNI", "REG_1_643_A_3", "secondary", "capital gains in/out of DNI (L3/L6)"),
    ("R-1041-IDD", "IRC_SUBCHAPTER_J", "primary", "§651/§661 deduction capped at DNI"),
    ("R-1041-IDD", "IRS_2025_F1041", "secondary", "Schedule B L13/L14/L15 smaller-of"),
    ("R-1041-TIERS", "IRC_SUBCHAPTER_J", "primary", "§662(a) two-tier inclusion"),
    ("R-1041-TIERS", "IRS_2025_I1041", "secondary", "tiers pp.32,44 (DNI to tier 1 first)"),
    ("R-1041-SEPSHARE", "IRC_SUBCHAPTER_J", "primary", "§663(c) separate-share rule"),
    ("R-1041-SEPSHARE", "IRS_2025_I1041", "secondary", "separate-share DNI p.31"),
    ("R-1041-65DAY", "IRC_SUBCHAPTER_J", "primary", "§663(b) 65-day election"),
    ("R-1041-65DAY", "IRS_2025_I1041", "secondary", "Question 6 checkbox, irrevocable"),
    ("R-1041-CHAR", "IRS_2025_I1041", "primary", "character retention by DNI class p.44"),
    ("R-1041-EXEMPT", "IRC_SUBCHAPTER_J", "primary", "§642(b) exemption amounts"),
    ("R-1041-EXEMPT", "RP_2024_40", "secondary", "QDisT $5,100 (§2.35)"),
    ("R-1041-TAXINC", "IRS_2025_F1041", "primary", "page-1 L22/L23 (face arithmetic)"),
    ("R-1041-TAX", "RP_2024_40", "primary", "2025 §1(e) rate schedule (Table 5) + cap-gain breakpoints (§2.03)"),
    ("R-1041-TAX", "IRS_2025_I1041", "secondary", "Line 1a tax / worksheet selection"),
    ("R-1041-ESBT", "IRS_2025_F1041", "primary", "Sch G L4 ESBT Tax Worksheet line 17"),
    ("R-1041-ESBT", "IRS_2025_I1041", "secondary", "ESBT S-portion top-rate separate tax"),
    ("R-1041-NIIT", "IRC_1411_NIIT", "primary", "§1411 threshold $15,650; Form 8960 L21 → Sch G L5"),
    ("R-1041-TOTTAX", "IRS_2025_F1041", "primary", "Sch G Part I L1e/L3/L9 → page-1 L24"),
]

F1041_LINES: list[dict] = [
    # Page 1
    {"line_number": "1", "description": "Interest income", "line_type": "input", "source_facts": ["interest_income"], "sort_order": 1},
    {"line_number": "2a", "description": "Total ordinary dividends", "line_type": "input", "source_facts": ["ordinary_dividends"], "sort_order": 2},
    {"line_number": "2b", "description": "Qualified dividends allocable to (1) beneficiaries / (2) estate or trust", "line_type": "input", "source_facts": ["qualified_dividends"], "sort_order": 3},
    {"line_number": "3", "description": "Business income/(loss) — Schedule C", "line_type": "input", "source_facts": ["business_income"], "sort_order": 4},
    {"line_number": "4", "description": "Capital gain/(loss) — Schedule D (Form 1041)", "line_type": "input", "source_facts": ["capital_gain"], "sort_order": 5},
    {"line_number": "5", "description": "Rents, royalties, partnerships, other estates & trusts — Schedule E", "line_type": "input", "source_facts": ["rents_royalties_passthrough"], "sort_order": 6},
    {"line_number": "6", "description": "Farm income/(loss) — Schedule F", "line_type": "input", "source_facts": ["farm_income"], "sort_order": 7},
    {"line_number": "7", "description": "Ordinary gain/(loss) — Form 4797", "line_type": "input", "source_facts": ["ordinary_gain_4797"], "sort_order": 8},
    {"line_number": "8", "description": "Other income", "line_type": "input", "source_facts": ["other_income"], "sort_order": 9},
    {"line_number": "9", "description": "Total income (combine L1, 2a, 3-8)", "line_type": "subtotal", "source_rules": ["R-1041-TOTINC"], "sort_order": 10},
    {"line_number": "10", "description": "Interest", "line_type": "input", "source_facts": ["interest_deduction"], "sort_order": 11},
    {"line_number": "11", "description": "Taxes", "line_type": "input", "source_facts": ["taxes"], "sort_order": 12},
    {"line_number": "12", "description": "Fiduciary fees (§67(e) portion)", "line_type": "input", "source_facts": ["fiduciary_fees"], "sort_order": 13},
    {"line_number": "13", "description": "Charitable deduction (Schedule A L7)", "line_type": "input", "source_facts": ["charitable_deduction"], "sort_order": 14},
    {"line_number": "14", "description": "Attorney, accountant, return-preparer fees (§67(e) portion)", "line_type": "input", "source_facts": ["attorney_accountant_fees"], "sort_order": 15},
    {"line_number": "15a", "description": "Other deductions under §67(e)", "line_type": "input", "source_facts": ["other_deductions_67e"], "sort_order": 16},
    {"line_number": "15b", "description": "Net operating loss deduction", "line_type": "input", "source_facts": ["nol_deduction"], "sort_order": 17},
    {"line_number": "16", "description": "Add lines 10 through 15b", "line_type": "subtotal", "source_rules": ["R-1041-TOTDED"], "sort_order": 18},
    {"line_number": "17", "description": "Adjusted total income/(loss) (L9 − L16)", "line_type": "subtotal", "source_rules": ["R-1041-ATI"], "destination_form": "GA501", "sort_order": 19},
    {"line_number": "18", "description": "Income distribution deduction (Sch B L15)", "line_type": "calculated", "source_rules": ["R-1041-IDD"], "sort_order": 20},
    {"line_number": "19", "description": "Estate tax deduction incl. certain GST taxes", "line_type": "input", "source_facts": ["estate_tax_deduction"], "sort_order": 21},
    {"line_number": "20", "description": "Qualified business income deduction (8995/8995-A)", "line_type": "input", "source_facts": ["qbi_deduction"], "sort_order": 22},
    {"line_number": "21", "description": "Exemption (§642(b))", "line_type": "calculated", "source_rules": ["R-1041-EXEMPT"], "sort_order": 23},
    {"line_number": "22", "description": "Add lines 18 through 21", "line_type": "subtotal", "source_rules": ["R-1041-TAXINC"], "sort_order": 24},
    {"line_number": "23", "description": "Taxable income (L17 − L22)", "line_type": "total", "source_rules": ["R-1041-TAXINC"], "sort_order": 25},
    {"line_number": "24", "description": "Total tax (Schedule G Part I L9)", "line_type": "total", "source_rules": ["R-1041-TOTTAX"], "sort_order": 26},
    {"line_number": "25b", "description": "§1062 first installment (Form 1062 L15) — OBBBA", "line_type": "input", "source_facts": ["sec1062_installment"], "sort_order": 27},
    # Schedule B
    {"line_number": "B-1", "description": "Sch B L1 Adjusted total income (from page-1 L17, loss-netted)", "line_type": "subtotal", "source_rules": ["R-1041-DNI"], "sort_order": 40},
    {"line_number": "B-2", "description": "Sch B L2 Adjusted tax-exempt interest", "line_type": "calculated", "source_rules": ["R-1041-DNI"], "sort_order": 41},
    {"line_number": "B-3", "description": "Sch B L3 Total net gain from Sch D L19 col(1) — gains attributable to income", "line_type": "input", "source_facts": ["capital_gains_in_dni"], "sort_order": 42},
    {"line_number": "B-7", "description": "Sch B L7 Distributable net income (DNI)", "line_type": "subtotal", "source_rules": ["R-1041-DNI"], "sort_order": 43},
    {"line_number": "B-8", "description": "Sch B L8 Accounting income (complex trust)", "line_type": "input", "source_facts": ["accounting_income"], "sort_order": 44},
    {"line_number": "B-9", "description": "Sch B L9 Income required to be distributed currently (first tier)", "line_type": "input", "source_facts": ["income_required_distributed"], "sort_order": 45},
    {"line_number": "B-10", "description": "Sch B L10 Other amounts distributed (second tier)", "line_type": "input", "source_facts": ["other_amounts_distributed"], "sort_order": 46},
    {"line_number": "B-15", "description": "Sch B L15 Income distribution deduction (smaller of L13/L14) → page-1 L18", "line_type": "calculated", "source_rules": ["R-1041-IDD"], "sort_order": 47},
    # Schedule G
    {"line_number": "G-1a", "description": "Sch G L1a Tax (rate schedule / cap-gain worksheet)", "line_type": "calculated", "source_rules": ["R-1041-TAX"], "sort_order": 60},
    {"line_number": "G-4", "description": "Sch G L4 Tax on the ESBT portion (ESBT Tax Worksheet L17)", "line_type": "calculated", "source_rules": ["R-1041-ESBT"], "sort_order": 61},
    {"line_number": "G-5", "description": "Sch G L5 Net investment income tax (Form 8960 L21)", "line_type": "input", "source_facts": ["niit_form8960"], "sort_order": 62},
    {"line_number": "G-9", "description": "Sch G L9 Total tax → page-1 L24", "line_type": "total", "source_rules": ["R-1041-TOTTAX"], "sort_order": 63},
]

F1041_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_1041_AMT", "title": "Schedule I AMT out of scope — prepare manually (RED-defer, D-2)", "severity": "error",
     "condition": "AMT indicators present (large §67(e) deductions, tax-exempt private-activity-bond interest, accelerated depreciation, ISO, etc.) on a trust/estate return",
     "message": "Form 1041 Schedule I (Alternative Minimum Tax — Estates and Trusts) is NOT computed for season one (DECISIONS D-2). If this return has AMT indicators, the AMT must be prepared MANUALLY and entered on Schedule G Part I line 1c. Do not file relying on a $0 AMT without checking Schedule I.",
     "notes": "D-2 (ruled 2026-07-04). The mandated never-silent RED-defer."},
    {"diagnostic_id": "D_1041_CG_DNI", "title": "Capital gains in DNI — verify the three §1.643(a)-3(b) circumstances", "severity": "warning",
     "condition": "capital_gain > 0 and capital_gains_in_dni entered (or the preparer is deciding Sch B L3)",
     "message": "Capital gains are ordinarily EXCLUDED from DNI (allocated to corpus). Include them on Schedule B line 3 ONLY to the extent that, under the governing instrument + local law or the fiduciary's reasonable discretion, they are (1) allocated to income, (2) consistently treated as part of a distribution, or (3) actually distributed / used in determining the distribution (Reg. §1.643(a)-3(b)). Confirm the basis before including.",
     "notes": "Dec Q3. Direct-entry + this diagnostic; default corpus-excluded."},
    {"diagnostic_id": "D_1041_ESBT", "title": "ESBT S-portion is taxed separately at the top trust rate", "severity": "info",
     "condition": "entity_type == esbt",
     "message": "An Electing Small Business Trust's S-corporation portion is taxed SEPARATELY at the highest trust rate (37% for 2025) via the ESBT Tax Worksheet, and the result is entered on Schedule G Part I line 4 — it does not flow through the normal rate schedule. v1 computes a simplified top-rate tax on the direct-entered S-portion taxable income (W4).",
     "notes": "Dec Q1 / W4."},
    {"diagnostic_id": "D_1041_GRANTOR", "title": "Grantor trust — use a grantor letter, not Schedule K-1", "severity": "warning",
     "condition": "entity_type == grantor",
     "message": "A grantor-type trust does NOT report income on the 1041 itself and does NOT issue Schedule K-1. Fill in only the entity information; show dollar amounts on an attachment (the grantor letter) that the fiduciary gives the grantor. The income is taxed directly to the grantor.",
     "notes": "Dec Q1. Structure-only path."},
    {"diagnostic_id": "D_1041_PIF", "title": "Pooled income fund — file Form 5227, do not complete Schedule B", "severity": "warning",
     "condition": "entity_type == pooled_income_fund",
     "message": "A pooled income fund does NOT complete Schedule B and files Form 5227 (Split-Interest Trust Information Return) in addition to Form 1041 (attach a statement). Full split-interest-trust support (PIF + charitable remainder/lead trusts, §664 four-tier ordering) is a separate module — route to the Form 5227 leg (WO-10).",
     "notes": "Dec Q1. Routed to WO-10."},
    {"diagnostic_id": "D_1041_BANKR", "title": "Bankruptcy estate — individual-style computation (RED-defer)", "severity": "error",
     "condition": "entity_type in (bankruptcy_ch7, bankruptcy_ch11)",
     "message": "An individual's chapter 7/11 bankruptcy estate is computed like a Form 1040 (attach a completed 1040), not on the trust rate schedule, and files if gross income >= $15,750 for 2025. This path is NOT computed in v1 — prepare manually.",
     "notes": "Dec Q1 RED-defer."},
    {"diagnostic_id": "D_1041_65DAY", "title": "§663(b) 65-day election available (complex trust / estate)", "severity": "info",
     "condition": "entity_type in (complex_trust, estate) and distributions made within 65 days after year-end",
     "message": "A fiduciary of a complex trust or a decedent's estate may elect to treat amounts paid/credited within the first 65 days of the following year as distributed on the last day of this tax year (Question 6 checkbox). The election is IRREVOCABLE and shifts that income's taxation to the beneficiary in the earlier year (up to DNI).",
     "notes": "Dec Q2. §663(b)."},
    {"diagnostic_id": "D_1041_SEPSHR", "title": "§663(c) separate-share rule may apply", "severity": "info",
     "condition": "separate_share_applies or multiple beneficiaries with substantially separate & independent shares",
     "message": "When a single trust or estate has beneficiaries with substantially separate and independent shares, those shares are treated as separate trusts/estates for the SOLE purpose of determining the DNI allocable to each — a distribution to one beneficiary cannot carry out DNI attributable to another share.",
     "notes": "Dec Q2. §663(c)."},
    {"diagnostic_id": "D_1041_67E", "title": "Split bundled fiduciary fees — only the §67(e) portion is deductible", "severity": "info",
     "condition": "fiduciary_fees or attorney_accountant_fees or other_deductions_67e present",
     "message": "§67(g) suspends 2%-floor miscellaneous itemized deductions through 2025, but §67(e) administration costs (those that would not have been incurred but for the property being held in the estate/trust) remain fully deductible. Bundled fees that cover both must be split — enter only the §67(e) portion on lines 12/14/15a.",
     "notes": "§67(e)/§67(g). Lines 12/14/15a carry the split cue on the face."},
    {"diagnostic_id": "D_1041_NIIT", "title": "§1411 NIIT bites early — threshold is $15,650 for 2025", "severity": "info",
     "condition": "undistributed net investment income and AGI > 15650",
     "message": "A trust/estate owes the 3.8% net investment income tax on the LESSER of undistributed net investment income or (AGI − $15,650 for 2025). Because the threshold is the top-bracket start, trusts hit NIIT at very low income. Compute Form 8960 and enter line 21 on Schedule G line 5.",
     "notes": "§1411. The compressed-threshold trap for trusts."},
    {"diagnostic_id": "D_1041_1062", "title": "§1062 qualified-farmland installment election (OBBBA) — Form 1062", "severity": "info",
     "condition": "qualified farmland sold to a qualified farmer and the §1062 election is made",
     "message": "OBBBA §1062 lets an estate/trust elect to pay the net income tax attributable to gain on qualified farmland sold to a qualified farmer in 4 equal annual installments via Form 1062 (first installment on page-1 line 25b; deferred liability on Schedule G Part II line 18c). v1 provides the structure + this flag; prepare Form 1062 manually.",
     "notes": "OBBBA-new, low frequency. Structure + flag only."},
]

F1041_SCENARIOS: list[dict] = [
    {"scenario_name": "1041-T1 — simple trust, all income distributed (full IDD)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"entity_type": "simple_trust", "interest_income": 10000, "ordinary_dividends": 5000,
                "income_required_distributed": 15000},
     "expected_outputs": {"L9": 15000, "L17": 15000, "SchB_L7_DNI": 15000, "SchB_L15_IDD": 15000, "L21": 300, "L23": 0},
     "notes": "Simple trust distributes all 15,000 income → IDD = min(distributions 15,000, DNI 15,000) = 15,000; taxable income before exemption = 0; exemption 300 (no benefit, L23 floored at 0)."},
    {"scenario_name": "1041-T2 — complex trust, partial distribution (DNI limitation)", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"entity_type": "complex_trust", "interest_income": 30000, "other_amounts_distributed": 10000,
                "accounting_income": 30000},
     "expected_outputs": {"L9": 30000, "L17": 30000, "SchB_L7_DNI": 30000, "SchB_L15_IDD": 10000, "L21": 100, "L23": 19900},
     "notes": "Complex trust distributes 10,000 of 30,000 DNI → IDD = min(10,000, 30,000) = 10,000; taxable income = 30,000 − 10,000 − 100 exemption = 19,900."},
    {"scenario_name": "1041-T3 — decedent's estate, $600 exemption + rate schedule", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"entity_type": "estate", "interest_income": 20000, "income_required_distributed": 0},
     "expected_outputs": {"L17": 20000, "L21": 600, "L23": 19400, "SchG_L1a": 5165},
     "notes": "Estate retains all income; taxable = 20,000 − 600 = 19,400; tax = 3,777 + 37% × (19,400 − 15,650) = 3,777 + 1,387.5 = 5,165 (rounded)."},
    {"scenario_name": "1041-T4 — QDisT $5,100 exemption", "scenario_type": "edge", "sort_order": 4,
     "inputs": {"entity_type": "qdist", "interest_income": 8000},
     "expected_outputs": {"L17": 8000, "L21": 5100, "L23": 2900, "SchG_L1a": 290},
     "notes": "Qualified disability trust gets the $5,100 exemption; taxable = 8,000 − 5,100 = 2,900; tax = 10% × 2,900 = 290."},
    {"scenario_name": "1041-T5 — two-tier distribution (DNI to tier 1 first)", "scenario_type": "edge", "sort_order": 5,
     "inputs": {"entity_type": "complex_trust", "interest_income": 20000, "accounting_income": 20000,
                "income_required_distributed": 12000, "other_amounts_distributed": 15000},
     "expected_outputs": {"SchB_L7_DNI": 20000, "tier1_included": 12000, "tier2_included": 8000, "SchB_L15_IDD": 20000},
     "notes": "§662: DNI 20,000 → tier-1 (required 12,000) fully included; tier-2 (other 15,000) included only up to the excess DNI 20,000 − 12,000 = 8,000. Total distributions 27,000 but IDD capped at DNI 20,000."},
    {"scenario_name": "1041-T6 — 65-day election pulls back a January distribution", "scenario_type": "edge", "sort_order": 6,
     "inputs": {"entity_type": "complex_trust", "interest_income": 25000, "accounting_income": 25000,
                "sec663b_65day_election": True, "other_amounts_distributed": 25000},
     "expected_outputs": {"SchB_L7_DNI": 25000, "SchB_L15_IDD": 25000, "L23": 0},
     "notes": "§663(b): a distribution made within 65 days after year-end is treated as prior-year → other_amounts_distributed 25,000 → IDD = min(25,000, DNI 25,000) = 25,000; trust taxable income 0 (income shifted to the beneficiary in the earlier year)."},
    {"scenario_name": "1041-T7 — ESBT S-portion separate top-rate tax", "scenario_type": "edge", "sort_order": 7,
     "inputs": {"entity_type": "esbt", "interest_income": 4000, "esbt_s_portion_taxable_income": 50000},
     "expected_outputs": {"SchG_L4": 18500},
     "notes": "ESBT S-portion 50,000 taxed at the top trust rate 37% = 18,500 → Sch G L4 (simplified worksheet, W4). The non-S grantor/interest portion is taxed on the normal schedule separately."},
    {"scenario_name": "1041-T8 — cap gains excluded from DNI by default (corpus)", "scenario_type": "edge", "sort_order": 8,
     "inputs": {"entity_type": "complex_trust", "interest_income": 10000, "capital_gain": 40000,
                "capital_gains_in_dni": 0, "accounting_income": 10000, "income_required_distributed": 10000},
     "expected_outputs": {"SchB_L7_DNI": 10000, "SchB_L15_IDD": 10000, "L23": 39900},
     "notes": "Default §643(a)(3): the 40,000 capital gain is allocated to corpus and EXCLUDED from DNI (L6 backs it out) → DNI = 10,000, IDD = 10,000; the trust is taxed on the 40,000 gain (taxable = 10,000+40,000 − 10,000 IDD − 100 = 39,900). Gain would only enter DNI via a §1.643(a)-3(b) circumstance (L3)."},
    {"scenario_name": "1041-T9 — grantor trust routes to a grantor letter (no K-1)", "scenario_type": "failure", "sort_order": 9,
     "inputs": {"entity_type": "grantor", "interest_income": 5000},
     "expected_outputs": {"diagnostic": "D_1041_GRANTOR"},
     "notes": "Grantor trust: no dollar amounts on the 1041, no Schedule K-1 — D_1041_GRANTOR fires; income taxed to the grantor via the attachment."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORMS registry + flow assertions
# ═══════════════════════════════════════════════════════════════════════════

FORMS: list[dict] = [
    {
        "identity": {"form_number": "1041", "form_title": "Form 1041 — U.S. Income Tax Return for Estates and Trusts (spine: page 1 + Schedule B + Schedule G, TY2025)",
                     "notes": "Greenfield fiduciary spine (S-11/WO-09). One consolidated form: page-1 income/deductions → adjusted total income (L17) → distribution/exemption block → taxable income (L23) → total tax (L24); Schedule B DNI/IDD engine (§643(a) DNI, §651/§661 deduction capped at DNI, §662 tiers, §663(c) separate-share, §663(b) 65-day); Schedule G tax (rate schedule / cap-gain worksheet, ESBT L4, §1411 NIIT L5). Core 4 + ESBT computed; grantor=grantor-letter; PIF→Form 5227 (WO-10); bankruptcy=RED-defer; Sch I AMT=RED-defer (D-2). K-1 (SCHEDULE_K1_1041) and GA 501 are separate legs. All constants TY2025-verified (f1041_source_brief.md)."},
        "facts": F1041_FACTS, "rules": F1041_RULES, "rule_links": F1041_RULE_LINKS,
        "lines": F1041_LINES, "diagnostics": F1041_DIAGNOSTICS, "scenarios": F1041_SCENARIOS,
    },
]

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1041-DNI", "title": "DNI = §643(a) modifications of taxable income", "assertion_type": "reconciliation",
     "entity_types": ["1041"], "status": "draft", "sort_order": 1,
     "description": "Schedule B L7 DNI = adjusted total income (L17) + adjusted tax-exempt interest (L2) + capital gains attributable to income (L3) − corpus capital gains (L6), floored at 0. Corpus cap gains are excluded by default (§643(a)(3)).",
     "definition": {"rule": "R-1041-DNI", "check": "SchB_L7 = L1 + L2 + L3 + L4 - L5 + L6, floored at 0"}},
    {"assertion_id": "FA-1041-IDD", "title": "Income distribution deduction = smaller of distributions or DNI (net of tax-exempt)", "assertion_type": "reconciliation",
     "entity_types": ["1041"], "status": "draft", "sort_order": 2,
     "description": "Schedule B L15 (→ page-1 L18) = min(L13 total distributions net of tax-exempt, L14 DNI net of adjusted tax-exempt interest). The §651/§661 DNI limitation.",
     "definition": {"rule": "R-1041-IDD", "check": "L15 = min(L13, L14); L18 = L15"}},
    {"assertion_id": "FA-1041-TIERS", "title": "§662 DNI applied to first-tier before second-tier", "assertion_type": "flow_assertion",
     "entity_types": ["1041"], "status": "draft", "sort_order": 3,
     "description": "First-tier distributions (L9) carry out DNI before second-tier (L10); second-tier beneficiaries include only the excess of DNI over first-tier. Beneficiary inclusion ≤ proportionate DNI share.",
     "definition": {"rule": "R-1041-TIERS", "check": "tier1 = min(L9, DNI); tier2 = min(L10, max(0, DNI - L9))"}},
    {"assertion_id": "FA-1041-EXEMPT", "title": "§642(b) exemption by entity type", "assertion_type": "reconciliation",
     "entity_types": ["1041"], "status": "draft", "sort_order": 4,
     "description": "Page-1 L21 exemption = $600 estate / $300 simple trust / $100 complex trust / $5,100 QDisT (Rev. Proc. 2024-40 §2.35). ESBT S-portion = 0.",
     "definition": {"rule": "R-1041-EXEMPT", "check": "L21 = {estate:600, simple:300, complex:100, qdist:5100}[entity_type]"}},
    {"assertion_id": "FA-1041-TAX", "title": "Sch G L1a tax on the 2025 §1(e) compressed schedule", "assertion_type": "reconciliation",
     "entity_types": ["1041"], "status": "draft", "sort_order": 5,
     "description": "Ordinary-income tax = 10% ≤$3,150; $315+24% ≤$11,450; $2,307+35% ≤$15,650; $3,777+37% above (Rev. Proc. 2024-40 Table 5). Cap-gain / qualified-dividend income uses the 0/15/20% breakpoints $3,250/$15,900.",
     "definition": {"rule": "R-1041-TAX", "check": "top bracket 37% begins at $15,650; cap-gain 0/15/20 at $3,250/$15,900"}},
    {"assertion_id": "FA-1041-NIIT", "title": "§1411 NIIT threshold = top-bracket start ($15,650)", "assertion_type": "reconciliation",
     "entity_types": ["1041"], "status": "draft", "sort_order": 6,
     "description": "Schedule G L5 = Form 8960 L21 = 3.8% × lesser of undistributed NII or (AGI − $15,650). The trust NIIT threshold equals the start of the top §1(e) bracket.",
     "definition": {"rule": "R-1041-NIIT", "check": "SchG_L5 = 0.038 * min(undistributed_NII, AGI - 15650)"}},
]


# ═══════════════════════════════════════════════════════════════════════════
# Command
# ═══════════════════════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = (
        "Load the Form 1041 spine spec (page 1 + Schedule B + Schedule G, TY2025). "
        "Refuses to seed until Ken sets READY_TO_SEED=True after the in-session review walk (W1-W5)."
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad Form 1041 spine spec (page 1 + Schedule B + Schedule G)\n"))
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
                "\nREFUSING TO SEED FORM 1041 SPINE: not cleared to seed.\n\n"
                "Content is authored, but seeding is gated until Ken reviews the packet\n"
                "(W1 the TY2025 constants; W2 the full §662/§663 distribution engine; W3 the\n"
                "cap-gains-in-DNI direct-entry choice; W4 the ESBT simplification; W5 the line\n"
                "numbering) and flips the sentinel.\n\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True to proceed)\n\n"
                f"Currently empty / placeholder:\n  {still_empty}\n\n"
                "To proceed: review the module-level data lists (and f1041_source_brief.md),\n"
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
        self.stdout.write("Form 1041 spine loaded.")
        self.stdout.write(
            f"  1041: facts {len(F1041_FACTS)} / rules {len(F1041_RULES)} / lines {len(F1041_LINES)} / "
            f"diag {len(F1041_DIAGNOSTICS)} / tests {len(F1041_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}"
        )
        self.stdout.write("=" * 60)
