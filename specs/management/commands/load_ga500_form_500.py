"""Load the GA Form 500 spec — Georgia Individual Income Tax Return.

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
Georgia Form 500 is the resident / part-year / nonresident individual income
tax return. It starts from FEDERAL AGI (1040 line 11), applies Georgia
additions/subtractions (Schedule 1 — the retirement-income exclusion is its
center of gravity), a flat standard or itemized deduction, a per-dependent
exemption, Georgia NOL (Schedule 4), then a FLAT tax rate, then credits
(Low Income Credit, Other-State credit, IND-CR, Schedule 2 series-100) and
withholding/payments → refund or balance due.

This is the FIRST STATE individual spec (all prior RS specs are federal). It
attaches to the child 1040 return in tts-tax-app via the existing
TaxReturn.federal_return FK / state_returns relation (the GA-600S precedent).

NO prior RS spec exists (lookup/500/, GA_500, GA500 → all 404). NEW form.

═══════════════════════════════════════════════════════════════════════════
v1 SCOPE (Ken-approved kickoff — 4 AskUserQuestion decisions 2026-06-25; MAXIMAL)
═══════════════════════════════════════════════════════════════════════════
COMPUTES (v1):
  • Full-year RESIDENT main form (lines 8-46).
  • PART-YEAR / NONRESIDENT — Schedule 3 (the 3-column GA-source proration,
    ratio = GA AGI ÷ federal AGI applied to deductions+exemptions).
  • BOTH retirement exclusions — the standard Retirement Income Exclusion
    worksheet (Sch 1 p2; $35,000 age 62-64 or perm. disabled / $65,000 age 65+;
    ≤$5,000 earned) AND the Military Retirement Exclusion worksheet (Sch 1 p3;
    under 62; $17,500 base → up to $35,000).
  • Schedule 4 GEORGIA NOL — Part I loss computation, Part II nonbusiness
    income/deductions, the 80%-of-GA-income limitation → line 15b.
  • LOW INCOME CREDIT (line 17, FAGI < $20,000 × the exemption table).
  • IND-CR 202 GA CHILD & DEPENDENT CARE credit (50% of the federal §21 credit).
  • Taxable Social Security subtraction (← federal 1040 line 6b).
  • Tax (flat rate × GA taxable income), dependent exemption, std/itemized
    (the 12b SALT back-out), withholding aggregation, refund/balance due.

DIRECT-ENTRY (no silent gap — the line exists, accepts entry, a diagnostic
prompts; the preparer keys the GA-vs-federal figure):
  • Schedule 1 DEPRECIATION add-back (L3) + subtraction (L11) — the §168(k)/§179
    / OBBBA decoupling difference. GA conforms to the IRC as of 1/1/2025 and did
    NOT adopt OBBBA (signed 7/4/2025); it disallows §168(k) bonus. v1 takes the
    GA depreciation adjustment as preparer direct-entry (the depreciation
    engine's existing Asset.state_* fields auto-populate it in a later
    integration). W1 below.
  • Sch 1 other additions/subtractions (L5/L12), non-GA muni interest (L1),
    lump-sum (L2), federal-NOL-carryover add-back (L4), Path2College 529 (L9,
    cap-checked), US-obligation interest (L10), other-state-credit inputs,
    Eligible-Itemizer credit (L19), Schedule 2 series-100 (L21), Schedule 2B
    refundable (L27), gift check-offs (L32-41), penalties/interest (L42-44).

RED-DEFERS (each its own "prepare manually" RED — no silent gap):
  • Form 500 UET underpayment-penalty computation (L42) — D_GA500_010.
  • Schedule 4 Part III multi-year carryover APPLICATION across prior years when
    the prior-year GA returns are not in the system — the preparer asserts the
    carryforward amounts; Part I/II + the 80% current-year limit ARE computed.
    D_GA500_009.

PREPARER-ASSERTED / FEDERAL HANDOFFS:
  • L8 ← federal 1040 line 11 (AGI). Taxable SS ← 1040 line 6b. RIE pension/IRA
    ← 1040 4b/5b. Child-care credit ← the federal Form 2441 §21 result. GA
    withholding ← W-2/1099 state_tax_withheld where state = GA.

═══════════════════════════════════════════════════════════════════════════
VERIFIED STRUCTURE + CONSTANTS (READ DIRECTLY 2026-06-25 from the GA-DOR 2025
Form 500 (Rev. 07/09/25) + 2025 IT-511 booklet PDFs — NOT memory; O.C.G.A.
Title 48 Ch. 7; HB 111 (TY2025 rate); HB 463 "Georgia Economic Growth and Tax
Relief Act of 2026" (TY2026). Full source brief + every line/worksheet:
tts-tax-app/server/specs/_ga500_source_brief.md.)
═══════════════════════════════════════════════════════════════════════════
Form 500 face: L8 federal AGI → L9 Sch1 net adj → L10 GA AGI → L11 std / L12c
itemized → L13 → L14 dependents×exemption → L15a/b/c (NOL) → L16 tax (×rate) →
L17 LIC / L18 other-state / L19 elig-itemizer / L20 IND-CR / L21 Sch2 → L22/23
→ L24-28 payments → L29 due / L30 overpay → L31 applied / L32-41 gift check-offs /
L42 UET / L43 late penalty / L44 interest → L45 amount due / L46 refund.

CONSTANTS (year-keyed; cited):
  Flat rate            2025 5.19% (HB 111) / 2026 4.99% (HB 463)
  Std ded MFJ          2025 $24,000 / 2026 $24,000  (→$30,000 in 2027)
  Std ded other        2025 $12,000 / 2026 $12,000  (→$15,000 in 2027)
  Dependent exemption  2025 $4,000  / 2026 $5,000  (HB 463, eff. TY2026)
  Retirement excl 62-64/disabled  $35,000 (→$70,000 in 2027)
  Retirement excl 65+             $65,000 (→$70,000 in 2027)
  RIE earned-income cap           $5,000
  Military RIE base / max         $17,500 / $35,000
  Path2College 529 cap            $4,000/beneficiary ($8,000 MFJ)
  Low Income Credit FAGI ceiling  < $20,000
  LIC credit per exemption        $26 (<6k) / $20 (6-7,999) / $14 (8-9,999)
                                  / $8 (10-14,999) / $5 (15-19,999) / $0 (20k+)
  GA NOL limitation               80% of GA income before NOL (2018+ NOLs)
  SALT 12b back-out cap           $10,000 ($5,000 MFS)
  NO age-65/blind additional std deduction; NO personal exemption (HB 1437).

═══════════════════════════════════════════════════════════════════════════
requires_human_review WALK ITEMS (for Ken's in-session review)
═══════════════════════════════════════════════════════════════════════════
W1. DEPRECIATION / CONFORMITY DECOUPLING. GA conforms to the IRC as of 1/1/2025,
    did NOT adopt OBBBA, and disallows §168(k) bonus + uses a GA §179 limit. The
    IT-511's enumerated depreciation text only details the legacy 1981-1986
    window, but the Schedule 1 depreciation LINES (L3 add / L11 sub) are the
    general home for the modern §168(k)/§179/OBBBA depreciation difference. v1 =
    PREPARER DIRECT-ENTRY on L3/L11 (the engine's Asset.state_* fields
    auto-populate later). CONFIRM the boundary + the GA §179 limit per year.
    (Ken = depreciation CPA.)
W2. TY2026 CONSTANTS vs HB 463 bill text. CONFIRM rate 4.99%, dependent
    exemption $5,000 effective TY2026 (NOT 2027), std deduction + retirement
    exclusion UNCHANGED for 2026 (the $15k/$30k + $70k bumps start 2027).
W3. SCHEDULE 4 NOL CARRYOVER SCOPE. Part I/II + the 80% current-year limit are
    computed; the multi-year Part III carryover APPLICATION needs prior GA
    returns → v1 = preparer-asserted carryforward amounts (D_GA500_009).
    CONFIRM this v1 boundary.
W4. SALT 12b BACK-OUT. OBBBA changed the federal SALT cap; GA non-conforms.
    CONFIRM the $10,000 ($5,000 MFS) figure GA uses for the 12b adjustment per
    year, and the formula (other-state income tax ÷ Sch A 5d total × lesser(5d,
    cap)).
W5. RETIREMENT-EXCLUSION CLASSIFICATION. The RIE worksheet routes S-corp w/
    material participation + FICA/SE-taxed rental to EARNED (L2), not L13; income
    is split 50/50 for jointly-owned property; each spouse qualifies separately.
    Taxable SS subtraction = 1040 6b + RR Tier 1/2. CONFIRM.
W6. PART-YEAR / NONRESIDENT proration. Ratio = GA AGI ÷ federal AGI (bounded
    0-100%, special zero/negative rules), applied to deductions+exemptions; the
    RIE earned & unearned portions are prorated SEPARATELY by GA-source ratio.
    CONFIRM the Schedule 3 mechanics.

═══════════════════════════════════════════════════════════════════════════
SAFETY GUARD — READY_TO_SEED stays False until Ken approves the review walk
in-session. Until then the command refuses to write to the DB (zero writes).
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
# SAFETY GUARD — flip ONLY after Ken's in-session review walk (W1–W6 above).
# Until then the command writes nothing.
#
# FLIPPED 2026-06-25 — Ken APPROVED the review walk in-session ("Approve as
# drafted — seed + export"): W1 the depreciation/conformity decoupling direct-
# entry boundary (GA conforms to the IRC as of 1/1/2025, not OBBBA; §168(k)/§179
# difference on Sch 1 L3/L11 = preparer direct-entry in v1) blessed; W2 the TY2026
# HB 463 constants (rate 4.99%, dependent exemption $5,000 eff. 2026, std/RIE
# unchanged for 2026) blessed; W3 the Schedule 4 NOL carryover scope (Part I/II +
# 80% current-year limit computed; multi-year carryover application preparer-
# asserted) blessed; W4 the 12b SALT back-out blessed; W5 the RIE classification
# + taxable-SS sourcing blessed; W6 the Schedule 3 PY/NR proration blessed. Math
# gate check_ga500_integrity.py ALL CHECKS PASS (constants + helpers + LIC table
# + 12 scenarios re-derived independently).
# ═══════════════════════════════════════════════════════════════════════════
READY_TO_SEED = True


FORM_JURISDICTION = "GA"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1040"]


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS (year-keyed; every value cited above; never training memory)
# ═══════════════════════════════════════════════════════════════════════════

GA_TAX_RATE: dict[int, str] = {2025: "0.0519", 2026: "0.0499"}          # HB 111 / HB 463
GA_STD_DED_MFJ: dict[int, int] = {2025: 24000, 2026: 30000}            # status B; HB 463 → $30,000 in 2026
GA_STD_DED_OTHER: dict[int, int] = {2025: 12000, 2026: 15000}         # status A/C/D; HB 463 → $15,000 in 2026
GA_DEPENDENT_EXEMPTION: dict[int, int] = {2025: 4000, 2026: 5000}     # HB 463 → $5,000 in 2026
# HB 463 (Georgia Economic Growth and Tax Relief Act of 2026, signed 2026-05-11):
# for taxable years beginning on/after 2026-01-01 the standard deduction rises to
# $15,000 (single/MFS/HOH) / $30,000 (MFJ) and the dependent exemption to $5,000,
# with annual step-ups (+$375/$750 std, +$125 dep) beginning 2027. Effective-year
# CONFIRMED WITH KEN 2026-06-25 (sources conflicted: BIP Wealth/BDO = TY2026 vs
# GBPI = TY2027; Ken chose TY2026 — verify vs the bill text when convenient).
GA_RIE_62_64: dict[int, int] = {2025: 35000, 2026: 35000}            # age 62-64 or perm. disabled <62
GA_RIE_65: dict[int, int] = {2025: 65000, 2026: 65000}              # age 65+
GA_RIE_EARNED_CAP: dict[int, int] = {2025: 5000, 2026: 5000}        # RIE worksheet line 4
GA_MILITARY_RIE_BASE: dict[int, int] = {2025: 17500, 2026: 17500}  # Military worksheet line 2
GA_MILITARY_RIE_MAX: dict[int, int] = {2025: 35000, 2026: 35000}   # base + additional
GA_PATH2COLLEGE_CAP: dict[int, int] = {2025: 4000, 2026: 4000}     # per beneficiary
GA_PATH2COLLEGE_CAP_MFJ: dict[int, int] = {2025: 8000, 2026: 8000}
GA_LIC_FAGI_CEILING: dict[int, int] = {2025: 20000, 2026: 20000}   # < this to qualify
GA_NOL_LIMIT_PCT: str = "0.80"                                      # 2018+ NOLs, 80% of GA income
GA_SALT_CAP: dict[int, int] = {2025: 10000, 2026: 10000}           # 12b back-out (MFS $5,000)
GA_SALT_CAP_MFS: dict[int, int] = {2025: 5000, 2026: 5000}

# Low Income Credit table — credit per exemption by federal AGI (IT-511 p35, verified).
# (ceiling_inclusive, credit) — first bracket whose ceiling the FAGI does NOT exceed.
GA_LIC_TABLE: list[tuple[int, int]] = [
    (5999, 26),     # under $6,000
    (7999, 20),     # $6,000 – not more than $7,999
    (9999, 14),     # $8,000 – not more than $9,999
    (14999, 8),     # $10,000 – not more than $14,999
    (19999, 5),     # $15,000 – not more than $19,999
]


def _yk(d: dict[int, int], year: int) -> int:
    """Year-keyed lookup with a 2026 fallback (the kiddie-spec convention)."""
    return d.get(year) if d.get(year) is not None else d[2026]


def ga_rate_for(year: int) -> str:
    return GA_TAX_RATE.get(year) or GA_TAX_RATE[2026]


def ga_std_ded_for(year: int, filing_status: str) -> int:
    """filing_status A/C/D → $12,000 ; B (MFJ) → $24,000."""
    return _yk(GA_STD_DED_MFJ, year) if filing_status == "B" else _yk(GA_STD_DED_OTHER, year)


def ga_dependent_exemption_for(year: int) -> int:
    return _yk(GA_DEPENDENT_EXEMPTION, year)


def ga_rie_max_for(year: int, age_65_plus: bool) -> int:
    return _yk(GA_RIE_65, year) if age_65_plus else _yk(GA_RIE_62_64, year)


def ga_lic_credit_for(fagi: int) -> int:
    """Credit per exemption from the FAGI table; 0 if FAGI >= $20,000."""
    for ceiling, credit in GA_LIC_TABLE:
        if fagi <= ceiling:
            return credit
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY TOPICS / SOURCES
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("georgia_income_tax", "Georgia Form 500 — individual income tax: federal-AGI start, Schedule 1 GA additions/subtractions, the retirement-income exclusion, the flat tax rate, the dependent exemption, GA NOL, the Low Income Credit, and part-year/nonresident proration (Schedule 3)"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_1040_FORM",  # the federal AGI (1040 L11) / 6b / 4b / 5b cross-form handoffs
]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "GA_2025_FORM_500",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "GA",
        "title": "2025 Georgia Form 500 — Individual Income Tax Return (Rev. 07/09/25)",
        "citation": "Georgia Form 500 (2025), Rev. 07/09/25",
        "issuer": "Georgia Department of Revenue",
        "official_url": "https://dor.georgia.gov/500-individual-income-tax-return",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["georgia_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "Form 500 face (2025) — verified line map",
                "excerpt_text": (
                    "L8 Federal AGI (from Federal Form 1040); L9 Adjustments from Schedule 1; "
                    "L10 Georgia AGI (net of L8+L9); L11 Standard Deduction ($12,000 if status A/C/D, "
                    "$24,000 if B); L12a-c Itemized (Federal Sch A less adjustments); L13 L10 less "
                    "(L11 or L12c); L14 dependents (L7c) × $4,000; L15a income before GA NOL; L15b GA "
                    "NOL utilized; L15c GA taxable income; L16 Tax = L15c × 5.19% (round to nearest $); "
                    "L17a-c Low Income Credit; L18 Other State(s) Tax Credit; L19 Eligible Itemizer "
                    "Credit; L20 IND-CR credits; L21 Schedule 2 credits; L22 total credits (≤ L16); "
                    "L23 balance; L24-28 withholding/estimated/IT-560/Sch 2B; L29 balance due; L30 "
                    "overpayment; L31 applied-to-next-year; L32-41 gift check-offs; L42 UET; L43 late "
                    "penalty; L44 interest; L45 amount due (L29 + L32-44); L46 refund (L30 − L31-44)."
                ),
                "summary_text": "Form 500 (2025) line-by-line face: federal-AGI start → Sch 1 adj → GA AGI → deduction → dependent exemption → NOL → flat tax → credits → payments → refund/due.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule 1 (2025) — GA additions & subtractions",
                "excerpt_text": (
                    "ADDITIONS: 1 Interest on Non-Georgia Municipal and State Bonds; 2 Lump Sum "
                    "Distributions; 3 Depreciation; 4 Net operating loss carryover deducted on Federal "
                    "return; 5 Other; 6 Total Additions. SUBTRACTIONS: 7 Retirement Income Exclusion "
                    "(7a-7f); 8 Social Security Benefits (taxable portion from Federal return); 9 "
                    "Path2College 529 Plan; 10 Interest on United States Obligations; 11 Depreciation; "
                    "12 Other Adjustments; 13 Total Subtractions; 14 Net Adjustments (L6 − L13) → Form "
                    "500 line 9."
                ),
                "summary_text": "Schedule 1 additions (1-6) and subtractions (7-14) → net to Form 500 L9.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Retirement Income Exclusion worksheet (Sch 1 p2, 2025)",
                "excerpt_text": (
                    "Per taxpayer and per spouse (each qualifies separately): 1 Salary and wages; 2 "
                    "Other earned income; 3 Total earned income; 4 Maximum Earned Income $5,000; 5 "
                    "lesser(L3,L4); 6 Interest; 7 Dividends; 8 Alimony; 9 Capital gains; 10 Other "
                    "income; 11 Taxable IRA distributions; 12 Taxable pensions; 13 Rental/Royalty/"
                    "Partnership/S-corp; 14 sum(L6..L13) (≥0); 15 L5+L14; 16 Maximum Allowable "
                    "Exclusion ($35,000 age 62-64 or perm. disabled, $65,000 age 65+); 17 lesser(L15,"
                    "L16) → Sch 1 L7a&d (or 7c&f for disability)."
                ),
                "summary_text": "RIE worksheet: earned (≤$5,000) + unearned, capped at $35,000/$65,000 by age.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Military Retirement Exclusion worksheet (Sch 1 p3, 2025)",
                "excerpt_text": (
                    "Under age 62 only. 1 Taxable military retirement (1099-R); 2 Base Military "
                    "Exclusion $17,500; 3 lesser(L1,L2) — if taxable military retirement < $17,501 STOP, "
                    "enter L3 on Sch 1 L7b/7e. 4 Taxable GA salary/wages; 5 Other earned GA income; 6 "
                    "Total GA earned income — if < $17,501 STOP, enter L3. 7 Total additional military "
                    "exclusion allowed (up to +$17,500); 8 lesser(L1,L7) → Sch 1 L7b/7e. Total exclusion "
                    "= L3 + L8 (max $35,000); entered on Sch 1 L9 as negative."
                ),
                "summary_text": "Military RIE (under 62): $17,500 base + up to $17,500 more once GA earned ≥ $17,501.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule 3 part-year/nonresident (2025)",
                "excerpt_text": (
                    "3 columns: A federal income, B not-taxable-to-GA, C Georgia income (A = B + C). "
                    "Lines 1-4 wages/interest&dividends/business/other; 5 total income; 6 adjustments "
                    "from 1040 Sch 1; 7 adjustments from Form 500 Sch 1; 8 AGI = L5±L6±L7. L9 ratio = L8 "
                    "Col C ÷ L8 Col A (0 if GA AGI ≤0; 100% if federal AGI ≤0; ≤100%, ≥0%). L10 std or "
                    "itemized; L11 L7c × $4,000; L12 L10+L11; L13 L12 × ratio(L9); L14 L8 Col C − L13 → "
                    "Form 500 L15a."
                ),
                "summary_text": "Schedule 3: GA-source ratio prorates the deduction + exemptions for PY/NR filers.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule 4 GA NOL + 80% limitation (2025)",
                "excerpt_text": (
                    "Part I: 1 income before NOL (L15a); 2 GA exemption (L14); 3 excess nonbusiness "
                    "deductions (Part II L18); 4 excess nonbusiness capital losses (after $3,000 fed "
                    "limit); 6 total of L1-L4; 7 IRC §461(l) loss carried forward (compute GA income "
                    "with the §168(k) disallowance first); 8 total loss. Part II nonbusiness income "
                    "(L1-L10) and deductions (L11-L17) → L18 excess. 80% LIMIT: NOLs for 2018+ applied "
                    "to GA income cannot exceed 80% of GA income before NOLs (L15a) → line 15b."
                ),
                "summary_text": "Schedule 4 GA NOL: Part I loss, Part II nonbusiness split, 80% current-year limit → L15b.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Low Income Credit table + worksheet (IT-511 p35, 2025)",
                "excerpt_text": (
                    "Eligible if Federal AGI < $20,000 and not claimed/eligible as a dependent. "
                    "Worksheet: L2 exemptions (self+spouse+dependents, excluding unborn); L3 age-65 "
                    "count (1 if you/spouse 65+, 2 if both); L4 = L2+L3 → Form 500 L17a. L5 credit per "
                    "exemption from the table → L17b: under $6,000 $26; $6,000-7,999 $20; $8,000-9,999 "
                    "$14; $10,000-14,999 $8; $15,000-19,999 $5. L6 = L4 × L5 → L17c. Credit ≤ tax (L16)."
                ),
                "summary_text": "Low Income Credit = #exemptions × per-FAGI-bracket credit ($26/$20/$14/$8/$5).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "IND-CR 202 GA Child & Dependent Care credit (2025)",
                "excerpt_text": (
                    "O.C.G.A. §48-7-29.10: a credit equal to 50% of the federal child & dependent care "
                    "credit allowed under IRC §21 and claimed on the federal return. L1 federal §21 "
                    "credit; L2 GA rate 50%; L3 = L1 × .50; L4 credit used → IND-CR Summary Worksheet "
                    "→ Form 500 line 20. Cannot be carried forward."
                ),
                "summary_text": "GA child-care credit = 50% of the federal Form 2441 §21 credit → Form 500 L20.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Other State(s) Tax Credit worksheet (IT-511 p34, 2025)",
                "excerpt_text": (
                    "Credit for state/DC/US-local net income tax paid to another state on income also "
                    "taxed by GA (not foreign/possession). Income for the credit × GA rate, vs tax paid "
                    "to the other state (reduced by other-state credits); credit = the lesser → Form 500 "
                    "line 18. Must attach the other state's return."
                ),
                "summary_text": "Other-state credit = lesser(GA tax on doubly-taxed income, other-state tax) → L18.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "GA_2025_IT511",
        "source_type": "instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "GA",
        "title": "2025 IT-511 Individual Income Tax Instruction Booklet",
        "citation": "Georgia IT-511 (2025)",
        "issuer": "Georgia Department of Revenue",
        "official_url": "https://dor.georgia.gov/it-511-individual-income-tax-instruction-booklet",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["georgia_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "GA conformity to the IRC (IT-511 2025)",
                "excerpt_text": (
                    "Georgia conforms to the Internal Revenue Code, as amended, provided for in federal "
                    "law enacted on or before January 1, 2025. Georgia has not adopted the federal tax "
                    "law changes in the federal One Big Beautiful Bill Act because the Act was signed on "
                    "July 4, 2025."
                ),
                "summary_text": "GA conforms to the IRC as of 1/1/2025; did NOT adopt OBBBA → GA decouples from OBBBA + §168(k) bonus.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Standard deduction + dependent exemption (IT-511 2025)",
                "excerpt_text": (
                    "Standard deduction: Married filing jointly $24,000; Single / Married filing "
                    "separately / Head of household / Qualifying surviving spouse $12,000. (No age-65 or "
                    "blindness additional standard deduction; no personal exemption — HB 1437.) "
                    "Dependent exemption (line 14): multiply the number of dependents on line 7c by "
                    "$4,000."
                ),
                "summary_text": "Std deduction $24,000 MFJ / $12,000 else; dependent exemption $4,000 × dependents; no age/blind add-on, no personal exemption.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Tax rate + 12b SALT adjustment (IT-511 2025)",
                "excerpt_text": (
                    "Tax (line 16): multiply line 15c by 5.19%, round to the nearest dollar. Line 12b: "
                    "if state & local income taxes were limited on the Federal return to $10,000 ($5,000 "
                    "if MFS), the disallowed other-state income tax = other-state income taxes ÷ total "
                    "taxes on Schedule A line 5d × lesser(Schedule A line 5d, $10,000 [$5,000 MFS])."
                ),
                "summary_text": "Rate 5.19% (2025); the 12b itemized adjustment backs out other-state income tax under the SALT cap proration.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "GA_OCGA_48_7",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "GA",
        "title": "O.C.G.A. Title 48, Chapter 7 — Georgia Income Tax",
        "citation": "Ga. Code Ann. §48-7-1 et seq. (incl. §48-7-20 rate, §48-7-27 RIE, §48-7-29.10 child-care credit)",
        "issuer": "Georgia General Assembly",
        "official_url": "https://law.justia.com/codes/georgia/title-48/chapter-7/",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 10.0,
        "topics": ["georgia_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "§48-7-27 retirement income exclusion",
                "excerpt_text": (
                    "O.C.G.A. §48-7-27(a)(5): retirement income exclusion of up to $35,000 (age 62-64 or "
                    "permanently and totally disabled) / $65,000 (age 65+); up to $5,000 of the maximum "
                    "may be earned income. §48-7-27(a)(5.1): military retirement exclusion for taxpayers "
                    "under 62 ($17,500 base, additional $17,500 with ≥ $17,500 GA earned income)."
                ),
                "summary_text": "Statutory basis for the retirement income exclusion ($35k/$65k, ≤$5k earned) and the military exclusion.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "GA_HB463_2026",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "GA",
        "title": "Georgia HB 463 — Georgia Economic Growth and Tax Relief Act of 2026",
        "citation": "Ga. HB 463 (2026), signed May 2026",
        "issuer": "Georgia General Assembly",
        "official_url": "https://www.legis.ga.gov/legislation/70350",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.0,
        "topics": ["georgia_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "HB 463 — TY2026 rate + dependent exemption",
                "excerpt_text": (
                    "Lowers the Georgia individual income tax rate from 5.19% to 4.99% beginning January "
                    "1, 2026 (then −0.125 percentage points annually toward 3.99%). Increases the "
                    "dependent exemption from $4,000 to $5,000 effective for taxable years beginning "
                    "January 1, 2026 (then +$125 annually beginning 2027 toward $6,000). The standard "
                    "deduction increase ($15,000/$30,000) and the retirement-exclusion increase "
                    "($70,000) take effect beginning 2027 (NOT 2026)."
                ),
                "summary_text": "HB 463: TY2026 rate 4.99%, dependent exemption $5,000; std deduction + retirement exclusion unchanged for 2026.",
                "is_key_excerpt": True,
            },
        ],
    },
]

# New excerpts to add to sources that already exist in the RS DB.
NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []

# Source → form links (this spec's sources support form "500").
AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("GA_2025_FORM_500", "500", "primary"),
    ("GA_2025_IT511", "500", "primary"),
    ("GA_OCGA_48_7", "500", "primary"),
    ("GA_HB463_2026", "500", "primary"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FACTS  (g_ prefix — the genuine inputs: preparer-asserted + federal handoffs +
#         direct-entry GA adjustments)
# ═══════════════════════════════════════════════════════════════════════════

GA500_FACTS: list[dict] = [
    # — status / residency / dependents —
    {"fact_key": "g_residency_status", "label": "Residency status (full_year / part_year / nonresident)", "data_type": "choice", "default_value": "full_year", "sort_order": 1, "notes": "Form 500 line 4. part_year/nonresident → Schedule 3 path (omit Form 500 L9-L14)."},
    {"fact_key": "g_filing_status", "label": "Filing status (A Single / B MFJ / C MFS / D HOH-QSS)", "data_type": "choice", "default_value": "A", "sort_order": 2, "notes": "Form 500 line 5. Drives the standard deduction (B → $24,000, else $12,000)."},
    {"fact_key": "g_num_dependents", "label": "Number of qualified dependents (line 7c)", "data_type": "integer", "default_value": "0", "sort_order": 3, "notes": "Form 500 line 7c (excludes self/spouse/unborn). Drives line 14 = L7c × the dependent exemption."},
    {"fact_key": "g_num_unborn_dependents", "label": "Number of unborn dependents (line 7b)", "data_type": "integer", "default_value": "0", "sort_order": 4, "notes": "Form 500 line 7b. Counts as a dependent for line 14 but is EXCLUDED from the Low Income Credit exemption count."},

    # — federal handoff —
    {"fact_key": "g_federal_agi", "label": "Federal adjusted gross income (Form 500 line 8)", "data_type": "decimal", "default_value": "0", "sort_order": 10, "notes": "← federal 1040 line 11. The GA computation starting point."},
    {"fact_key": "g_federal_taxable_ss", "label": "Taxable Social Security from the federal return (1040 line 6b)", "data_type": "decimal", "default_value": "0", "sort_order": 11, "notes": "← 1040 line 6b. Feeds the Schedule 1 line 8 subtraction (+ RR Tier 1/2). W5."},

    # — deduction —
    {"fact_key": "g_itemize", "label": "Use Georgia itemized deduction (else standard)", "data_type": "boolean", "default_value": "false", "sort_order": 20, "notes": "If true, use line 12c; else the standard deduction (line 11). Use ONE."},
    {"fact_key": "g_federal_itemized", "label": "Federal itemized deductions (Schedule A) — line 12a", "data_type": "decimal", "default_value": "0", "sort_order": 21, "notes": "Form 500 line 12a (when itemizing)."},
    {"fact_key": "g_other_state_income_tax", "label": "Other-state income tax included in Schedule A (for the 12b back-out)", "data_type": "decimal", "default_value": "0", "sort_order": 22, "notes": "Numerator of the 12b SALT proration. W4."},
    {"fact_key": "g_sch_a_line5d_total", "label": "Schedule A line 5d total state/local taxes (for the 12b back-out)", "data_type": "decimal", "default_value": "0", "sort_order": 23, "notes": "Denominator of the 12b SALT proration; the cap applies to lesser(5d, $10,000 / $5,000 MFS). W4."},

    # — Schedule 1 additions (direct-entry) —
    {"fact_key": "g_add_non_ga_muni_interest", "label": "Sch 1 add: interest on non-Georgia municipal/state bonds (L1)", "data_type": "decimal", "default_value": "0", "sort_order": 30, "notes": "Schedule 1 line 1 (addition)."},
    {"fact_key": "g_add_lump_sum", "label": "Sch 1 add: lump-sum distributions (L2)", "data_type": "decimal", "default_value": "0", "sort_order": 31, "notes": "Schedule 1 line 2 (Form 4972 lump-sum)."},
    {"fact_key": "g_add_depreciation", "label": "Sch 1 add: depreciation difference (§168(k)/§179) add-back (L3)", "data_type": "decimal", "default_value": "0", "sort_order": 32, "notes": "Schedule 1 line 3. v1 DIRECT-ENTRY (W1): preparer enters the GA-vs-federal depreciation add-back; engine integration later."},
    {"fact_key": "g_add_federal_nol", "label": "Sch 1 add: federal NOL carryover deducted on the federal return (L4)", "data_type": "decimal", "default_value": "0", "sort_order": 33, "notes": "Schedule 1 line 4 (federal NOL added back; GA computes its own NOL on Schedule 4)."},
    {"fact_key": "g_add_other", "label": "Sch 1 add: other additions (L5)", "data_type": "decimal", "default_value": "0", "sort_order": 34, "notes": "Schedule 1 line 5 catch-all (incl. OBBBA AGI-affecting back-outs). Direct-entry."},

    # — Schedule 1 subtractions (some computed, some direct-entry) —
    {"fact_key": "g_sub_path2college", "label": "Sch 1 sub: Path2College 529 contributions (L9)", "data_type": "decimal", "default_value": "0", "sort_order": 40, "notes": "Schedule 1 line 9. Capped $4,000/beneficiary ($8,000 MFJ) — diagnostic on the cap. Direct-entry."},
    {"fact_key": "g_sub_us_obligation_interest", "label": "Sch 1 sub: interest on U.S. obligations (L10)", "data_type": "decimal", "default_value": "0", "sort_order": 41, "notes": "Schedule 1 line 10 (reduced by related interest expense; FNMA/GNMA/FHLMC/repo NOT eligible). Direct-entry."},
    {"fact_key": "g_sub_depreciation", "label": "Sch 1 sub: depreciation difference (GA depreciation) (L11)", "data_type": "decimal", "default_value": "0", "sort_order": 42, "notes": "Schedule 1 line 11. v1 DIRECT-ENTRY (W1)."},
    {"fact_key": "g_sub_other", "label": "Sch 1 sub: other adjustments (L12)", "data_type": "decimal", "default_value": "0", "sort_order": 43, "notes": "Schedule 1 line 12 catch-all. Direct-entry."},

    # — RIE: taxpayer —
    {"fact_key": "g_tp_rie_applies", "label": "Taxpayer qualifies for the retirement income exclusion", "data_type": "boolean", "default_value": "false", "sort_order": 50, "notes": "Age 62-64, or 65+, or <62 and permanently disabled. DOB required (date of disability if disability)."},
    {"fact_key": "g_tp_age_65_plus", "label": "Taxpayer is age 65 or older (→ $65,000 cap)", "data_type": "boolean", "default_value": "false", "sort_order": 51, "notes": "Selects the $65,000 vs $35,000 maximum allowable exclusion (worksheet line 16)."},
    {"fact_key": "g_tp_rie_disability", "label": "Taxpayer's RIE is a disability exclusion (<62, permanently disabled)", "data_type": "boolean", "default_value": "false", "sort_order": 52, "notes": "Routes the result to Sch 1 L7c (vs L7a). $35,000 cap."},
    {"fact_key": "g_tp_rie_salary_wages", "label": "TP RIE worksheet L1 — salary and wages (earned)", "data_type": "decimal", "default_value": "0", "sort_order": 53, "notes": "RIE worksheet line 1."},
    {"fact_key": "g_tp_rie_other_earned", "label": "TP RIE worksheet L2 — other earned income (incl. material-participation S-corp / SE-taxed rental)", "data_type": "decimal", "default_value": "0", "sort_order": 54, "notes": "RIE worksheet line 2. W5 classification."},
    {"fact_key": "g_tp_rie_interest", "label": "TP RIE worksheet L6 — interest income", "data_type": "decimal", "default_value": "0", "sort_order": 55, "notes": "RIE worksheet line 6 (unearned)."},
    {"fact_key": "g_tp_rie_dividends", "label": "TP RIE worksheet L7 — dividend income", "data_type": "decimal", "default_value": "0", "sort_order": 56, "notes": "RIE worksheet line 7 (unearned)."},
    {"fact_key": "g_tp_rie_alimony", "label": "TP RIE worksheet L8 — alimony", "data_type": "decimal", "default_value": "0", "sort_order": 57, "notes": "RIE worksheet line 8 (unearned)."},
    {"fact_key": "g_tp_rie_capital_gains", "label": "TP RIE worksheet L9 — capital gains (losses)", "data_type": "decimal", "default_value": "0", "sort_order": 58, "notes": "RIE worksheet line 9 (unearned)."},
    {"fact_key": "g_tp_rie_other_income", "label": "TP RIE worksheet L10 — other income (losses)", "data_type": "decimal", "default_value": "0", "sort_order": 59, "notes": "RIE worksheet line 10 (unearned)."},
    {"fact_key": "g_tp_rie_taxable_ira", "label": "TP RIE worksheet L11 — taxable IRA distributions", "data_type": "decimal", "default_value": "0", "sort_order": 60, "notes": "RIE worksheet line 11 (← 1040 4b portion)."},
    {"fact_key": "g_tp_rie_taxable_pension", "label": "TP RIE worksheet L12 — taxable pensions", "data_type": "decimal", "default_value": "0", "sort_order": 61, "notes": "RIE worksheet line 12 (← 1040 5b portion)."},
    {"fact_key": "g_tp_rie_rental_etc", "label": "TP RIE worksheet L13 — rental/royalty/partnership/S-corp (non-material-participation)", "data_type": "decimal", "default_value": "0", "sort_order": 62, "notes": "RIE worksheet line 13 (unearned). W5."},

    # — RIE: spouse —
    {"fact_key": "g_sp_rie_applies", "label": "Spouse qualifies for the retirement income exclusion", "data_type": "boolean", "default_value": "false", "sort_order": 70, "notes": "Each spouse qualifies separately."},
    {"fact_key": "g_sp_age_65_plus", "label": "Spouse is age 65 or older (→ $65,000 cap)", "data_type": "boolean", "default_value": "false", "sort_order": 71, "notes": "Selects $65,000 vs $35,000."},
    {"fact_key": "g_sp_rie_disability", "label": "Spouse's RIE is a disability exclusion (<62, permanently disabled)", "data_type": "boolean", "default_value": "false", "sort_order": 72, "notes": "Routes to Sch 1 L7f (vs L7d)."},
    {"fact_key": "g_sp_rie_salary_wages", "label": "Spouse RIE L1 — salary and wages", "data_type": "decimal", "default_value": "0", "sort_order": 73, "notes": "Spouse RIE worksheet line 1."},
    {"fact_key": "g_sp_rie_other_earned", "label": "Spouse RIE L2 — other earned income", "data_type": "decimal", "default_value": "0", "sort_order": 74, "notes": "Spouse RIE worksheet line 2."},
    {"fact_key": "g_sp_rie_interest", "label": "Spouse RIE L6 — interest income", "data_type": "decimal", "default_value": "0", "sort_order": 75, "notes": "Spouse RIE worksheet line 6."},
    {"fact_key": "g_sp_rie_dividends", "label": "Spouse RIE L7 — dividend income", "data_type": "decimal", "default_value": "0", "sort_order": 76, "notes": "Spouse RIE worksheet line 7."},
    {"fact_key": "g_sp_rie_alimony", "label": "Spouse RIE L8 — alimony", "data_type": "decimal", "default_value": "0", "sort_order": 77, "notes": "Spouse RIE worksheet line 8."},
    {"fact_key": "g_sp_rie_capital_gains", "label": "Spouse RIE L9 — capital gains (losses)", "data_type": "decimal", "default_value": "0", "sort_order": 78, "notes": "Spouse RIE worksheet line 9."},
    {"fact_key": "g_sp_rie_other_income", "label": "Spouse RIE L10 — other income (losses)", "data_type": "decimal", "default_value": "0", "sort_order": 79, "notes": "Spouse RIE worksheet line 10."},
    {"fact_key": "g_sp_rie_taxable_ira", "label": "Spouse RIE L11 — taxable IRA distributions", "data_type": "decimal", "default_value": "0", "sort_order": 80, "notes": "Spouse RIE worksheet line 11."},
    {"fact_key": "g_sp_rie_taxable_pension", "label": "Spouse RIE L12 — taxable pensions", "data_type": "decimal", "default_value": "0", "sort_order": 81, "notes": "Spouse RIE worksheet line 12."},
    {"fact_key": "g_sp_rie_rental_etc", "label": "Spouse RIE L13 — rental/royalty/partnership/S-corp", "data_type": "decimal", "default_value": "0", "sort_order": 82, "notes": "Spouse RIE worksheet line 13."},

    # — Military RIE: taxpayer / spouse —
    {"fact_key": "g_tp_military_under62", "label": "Taxpayer is under age 62 (military exclusion gate)", "data_type": "boolean", "default_value": "false", "sort_order": 90, "notes": "Military RIE requires under 62."},
    {"fact_key": "g_tp_military_retirement", "label": "TP taxable military retirement (1099-R) — military worksheet L1", "data_type": "decimal", "default_value": "0", "sort_order": 91, "notes": "Military worksheet line 1."},
    {"fact_key": "g_tp_military_ga_earned", "label": "TP total Georgia earned income — military worksheet L6", "data_type": "decimal", "default_value": "0", "sort_order": 92, "notes": "Military worksheet line 6 (GA salary/wages + other GA earned). ≥ $17,501 unlocks the additional exclusion."},
    {"fact_key": "g_sp_military_under62", "label": "Spouse is under age 62 (military exclusion gate)", "data_type": "boolean", "default_value": "false", "sort_order": 93, "notes": "Military RIE requires under 62."},
    {"fact_key": "g_sp_military_retirement", "label": "Spouse taxable military retirement (1099-R)", "data_type": "decimal", "default_value": "0", "sort_order": 94, "notes": "Spouse military worksheet line 1."},
    {"fact_key": "g_sp_military_ga_earned", "label": "Spouse total Georgia earned income", "data_type": "decimal", "default_value": "0", "sort_order": 95, "notes": "Spouse military worksheet line 6."},

    # — Schedule 3 (PY/NR) GA-source columns —
    {"fact_key": "g_s3_total_income_federal", "label": "Sch 3 L5 Col A — total income (federal)", "data_type": "decimal", "default_value": "0", "sort_order": 100, "notes": "Schedule 3 line 5, Column A."},
    {"fact_key": "g_s3_total_income_ga", "label": "Sch 3 L5 Col C — total income (Georgia source)", "data_type": "decimal", "default_value": "0", "sort_order": 101, "notes": "Schedule 3 line 5, Column C."},
    {"fact_key": "g_s3_adj_1040_federal", "label": "Sch 3 L6 Col A — adjustments from 1040 Sch 1 (federal)", "data_type": "decimal", "default_value": "0", "sort_order": 102, "notes": "Schedule 3 line 6, Column A."},
    {"fact_key": "g_s3_adj_1040_ga", "label": "Sch 3 L6 Col C — adjustments from 1040 Sch 1 (Georgia)", "data_type": "decimal", "default_value": "0", "sort_order": 103, "notes": "Schedule 3 line 6, Column C."},
    {"fact_key": "g_s3_adj_500_federal", "label": "Sch 3 L7 Col A — adjustments from Form 500 Sch 1 (federal)", "data_type": "decimal", "default_value": "0", "sort_order": 104, "notes": "Schedule 3 line 7, Column A."},
    {"fact_key": "g_s3_adj_500_ga", "label": "Sch 3 L7 Col C — adjustments from Form 500 Sch 1 (Georgia)", "data_type": "decimal", "default_value": "0", "sort_order": 105, "notes": "Schedule 3 line 7, Column C."},

    # — GA NOL (Schedule 4) —
    {"fact_key": "g_nol_carryforward_pre2018", "label": "GA NOL carryforward available — pre-2018 (no 80% limit)", "data_type": "decimal", "default_value": "0", "sort_order": 110, "notes": "80%-limit worksheet line 1. W3 (carryforward preparer-asserted)."},
    {"fact_key": "g_nol_carryforward_2018plus", "label": "GA NOL carryforward available — 2018 and later (80% limit)", "data_type": "decimal", "default_value": "0", "sort_order": 111, "notes": "80%-limit worksheet line 2; applied ≤ 80% of GA income before NOL. W3."},

    # — Low Income Credit —
    {"fact_key": "g_lic_not_dependent", "label": "Taxpayer is NOT claimed/eligible as a dependent (LIC eligibility)", "data_type": "boolean", "default_value": "true", "sort_order": 120, "notes": "LIC requires the taxpayer not be a dependent on another return."},
    {"fact_key": "g_lic_age65_count", "label": "LIC worksheet L3 — age-65 count (1 if you/spouse 65+, 2 if both)", "data_type": "integer", "default_value": "0", "sort_order": 121, "notes": "Added to the base exemption count for the Low Income Credit."},

    # — Child & dependent care credit (IND-CR 202) —
    {"fact_key": "g_federal_dependent_care_credit", "label": "Federal child & dependent care credit (§21) claimed on the 1040", "data_type": "decimal", "default_value": "0", "sort_order": 130, "notes": "← federal Form 2441 §21 result. GA credit = 50% → Form 500 line 20."},

    # — other credits (direct-entry) —
    {"fact_key": "g_other_state_credit", "label": "Other State(s) Tax Credit — direct (if not using the worksheet)", "data_type": "decimal", "default_value": "0", "sort_order": 140, "notes": "Form 500 line 18 (the worksheet computes this when its inputs are present)."},
    {"fact_key": "g_other_state_income_for_credit", "label": "Income taxed by another state while a GA resident (other-state worksheet)", "data_type": "decimal", "default_value": "0", "sort_order": 141, "notes": "Other-state credit worksheet input."},
    {"fact_key": "g_other_state_tax_paid", "label": "Tax paid to the other state(s) on the doubly-taxed income", "data_type": "decimal", "default_value": "0", "sort_order": 142, "notes": "Other-state credit worksheet input (reduced by other-state credits)."},
    {"fact_key": "g_eligible_itemizer_credit", "label": "Georgia Eligible Itemizer Tax Credit (L19) — direct", "data_type": "decimal", "default_value": "0", "sort_order": 143, "notes": "Form 500 line 19. Direct-entry."},
    {"fact_key": "g_indcr_other_credits", "label": "Other IND-CR credits (besides child-care) → line 20", "data_type": "decimal", "default_value": "0", "sort_order": 144, "notes": "Form 500 line 20 (IND-CR Summary), excluding the computed child-care credit. Direct-entry."},
    {"fact_key": "g_schedule2_credits", "label": "Schedule 2 series-100 Georgia tax credits (L21) — direct", "data_type": "decimal", "default_value": "0", "sort_order": 145, "notes": "Form 500 line 21 (e-file required). Direct-entry."},

    # — payments / withholding —
    {"fact_key": "g_ga_withholding_wages_1099", "label": "Georgia income tax withheld on wages & 1099s (L24)", "data_type": "decimal", "default_value": "0", "sort_order": 150, "notes": "← W-2/1099 state_tax_withheld where state = GA."},
    {"fact_key": "g_ga_withholding_other", "label": "Other Georgia income tax withheld — G2-A/FL/LP/RP (L25)", "data_type": "decimal", "default_value": "0", "sort_order": 151, "notes": "Form 500 line 25. Direct-entry."},
    {"fact_key": "g_estimated_payments", "label": "Estimated tax paid for the year + Form IT-560 (L26)", "data_type": "decimal", "default_value": "0", "sort_order": 152, "notes": "Form 500 line 26."},
    {"fact_key": "g_refundable_credits_2b", "label": "Schedule 2B refundable tax credits (L27)", "data_type": "decimal", "default_value": "0", "sort_order": 153, "notes": "Form 500 line 27 (e-file). Direct-entry."},
    {"fact_key": "g_amount_applied_next_year", "label": "Amount applied to next year's estimated tax (L31)", "data_type": "decimal", "default_value": "0", "sort_order": 154, "notes": "Form 500 line 31 (reduces the refund)."},
    {"fact_key": "g_gift_contributions_total", "label": "Charitable gift check-offs total (lines 32-41)", "data_type": "decimal", "default_value": "0", "sort_order": 155, "notes": "Sum of the 10 voluntary-contribution check-offs (Form 500 lines 32-41). On the form each fund is its own line (32-41); the line_map carries the 10 individual lines, and this total is the rule input. Reduces the refund / adds to the amount owed."},
    {"fact_key": "g_uet_penalty", "label": "Form 500 UET estimated-tax penalty (L42) — direct", "data_type": "decimal", "default_value": "0", "sort_order": 156, "notes": "Form 500 line 42. v1 RED-defers the UET computation (D_GA500_010); preparer enters."},
    {"fact_key": "g_late_payment_penalty", "label": "Penalty: late payment and/or late filing (L43) — direct", "data_type": "decimal", "default_value": "0", "sort_order": 157, "notes": "Form 500 line 43. Direct-entry."},
    {"fact_key": "g_interest", "label": "Interest on unpaid tax (L44) — direct", "data_type": "decimal", "default_value": "0", "sort_order": 158, "notes": "Form 500 line 44. Direct-entry."},
]


# ═══════════════════════════════════════════════════════════════════════════
# RULES  (R-GA500-* — the §2-§11 computations from the source brief)
# ═══════════════════════════════════════════════════════════════════════════

GA500_RULES: list[dict] = [
    {"rule_id": "R-GA500-SCOPE", "title": "Scope gate — GA Form 500 engaged", "rule_type": "routing", "precedence": 0, "sort_order": 1,
     "formula": "Form 500 is computed for a 1040 filer with Georgia residency or Georgia-source income. Full-year residents use the main form (L8-L46); part-year/nonresidents use Schedule 3 (which omits Form 500 L9-L14 and lands at L15a).",
     "inputs": ["g_residency_status", "g_federal_agi"], "outputs": [],
     "description": "GA residency / source-income gate. Attaches to the child 1040 return via the state_returns relation."},

    {"rule_id": "R-GA500-L8-AGI", "title": "Line 8 — federal AGI handoff", "rule_type": "calculation", "precedence": 1, "sort_order": 2,
     "formula": "Line 8 = federal Form 1040 line 11 (Georgia does NOT use federal taxable income).",
     "inputs": ["g_federal_agi"], "outputs": ["8"],
     "description": "The GA computation starts from federal AGI. Sourced from the child 1040's persisted line 11."},

    {"rule_id": "R-GA500-L9-S1", "title": "Line 9 — Schedule 1 net adjustments", "rule_type": "calculation", "precedence": 2, "sort_order": 3,
     "formula": "Line 9 = Schedule 1 line 14 = (Σ additions L1-L5) − (Σ subtractions L7-L12). May be negative.",
     "inputs": ["g_add_non_ga_muni_interest", "g_add_lump_sum", "g_add_depreciation", "g_add_federal_nol", "g_add_other", "g_sub_path2college", "g_sub_us_obligation_interest", "g_sub_depreciation", "g_sub_other"], "outputs": ["9", "S1-6", "S1-13", "S1-14"],
     "description": "Schedule 1 additions less subtractions. The RIE (L7) and taxable SS (L8) subtractions are computed by R-GA500-RIE / R-GA500-MIL / R-GA500-SS; depreciation L3/L11 are direct-entry (W1)."},

    {"rule_id": "R-GA500-SS", "title": "Schedule 1 line 8 — taxable Social Security subtraction", "rule_type": "calculation", "precedence": 2, "sort_order": 4,
     "formula": "Schedule 1 line 8 = federal taxable Social Security (1040 line 6b) + Railroad Retirement Tier 1/2. Fully subtracted (GA does not tax Social Security / RR retirement).",
     "inputs": ["g_federal_taxable_ss"], "outputs": ["S1-8"],
     "description": "GA subtracts the federally-taxable Social Security and Railroad Retirement included in federal AGI. W5."},

    {"rule_id": "R-GA500-RIE", "title": "Schedule 1 line 7 — Retirement Income Exclusion (standard worksheet)", "rule_type": "calculation", "precedence": 2, "sort_order": 5,
     "formula": "Per qualifying person: L5 = min(salary+other earned, $5,000); L14 = max(0, Σ unearned [interest+dividends+alimony+cap gains+other+IRA+pension+rental]); L15 = L5 + L14; L17 = min(L15, max allowable [$35,000 age 62-64/disabled, $65,000 age 65+]). Taxpayer L17 → Sch 1 L7a (or L7c disability); spouse L17 → L7d (or L7f). Each spouse qualifies separately; jointly-owned income split 50/50.",
     "inputs": ["g_tp_rie_applies", "g_tp_age_65_plus", "g_tp_rie_disability", "g_tp_rie_salary_wages", "g_tp_rie_other_earned", "g_tp_rie_interest", "g_tp_rie_dividends", "g_tp_rie_alimony", "g_tp_rie_capital_gains", "g_tp_rie_other_income", "g_tp_rie_taxable_ira", "g_tp_rie_taxable_pension", "g_tp_rie_rental_etc", "g_sp_rie_applies", "g_sp_age_65_plus", "g_sp_rie_disability", "g_sp_rie_salary_wages", "g_sp_rie_other_earned", "g_sp_rie_interest", "g_sp_rie_dividends", "g_sp_rie_alimony", "g_sp_rie_capital_gains", "g_sp_rie_other_income", "g_sp_rie_taxable_ira", "g_sp_rie_taxable_pension", "g_sp_rie_rental_etc"], "outputs": ["S1-7", "RIE-5", "RIE-14", "RIE-15", "RIE-17"],
     "description": "The retirement income exclusion (§48-7-27(a)(5)). The center of gravity of the GA return. W5."},

    {"rule_id": "R-GA500-MIL", "title": "Schedule 1 line 7 — Military Retirement Exclusion worksheet", "rule_type": "calculation", "precedence": 2, "sort_order": 6,
     "formula": "Under 62 only. L3 = min(military retirement, $17,500). If military retirement < $17,501 OR GA earned income < $17,501: additional = 0. Else L7 additional = $17,500; L8 = min(military retirement, L7). Total military exclusion = L3 + L8 (max $35,000) → Sch 1 L7b/7e, entered on Sch 1 L9 as a subtraction.",
     "inputs": ["g_tp_military_under62", "g_tp_military_retirement", "g_tp_military_ga_earned", "g_sp_military_under62", "g_sp_military_retirement", "g_sp_military_ga_earned"], "outputs": ["MIL-3", "MIL-7", "MIL-8"],
     "description": "Military retirement exclusion (§48-7-27(a)(5.1)) for under-62 retirees."},

    {"rule_id": "R-GA500-L10", "title": "Line 10 — Georgia AGI", "rule_type": "calculation", "precedence": 3, "sort_order": 7,
     "formula": "Line 10 = Line 8 + Line 9 (may be negative).",
     "inputs": [], "outputs": ["10"],
     "description": "Georgia adjusted gross income."},

    {"rule_id": "R-GA500-DED", "title": "Lines 11-13 — standard or itemized deduction", "rule_type": "calculation", "precedence": 4, "sort_order": 8,
     "formula": "Standard (line 11) = $24,000 (status B) else $12,000; no age-65/blind add-on. Itemized (line 12c) = federal Sch A (12a) − 12b adjustment, where 12b = other-state income tax + investment interest for GA-exempt income; the SALT back-out = (other-state income tax ÷ Sch A 5d total) × lesser(5d, $10,000 [$5,000 MFS]). Line 13 = Line 10 − (L11 or L12c).",
     "inputs": ["g_itemize", "g_federal_itemized", "g_other_state_income_tax", "g_sch_a_line5d_total", "g_filing_status"], "outputs": ["11", "12a", "12b", "12c", "13"],
     "description": "GA standard ($12k/$24k) or itemized (federal Sch A less the SALT/other-state back-out). W4."},

    {"rule_id": "R-GA500-L14-DEP", "title": "Line 14 — dependent exemption", "rule_type": "calculation", "precedence": 5, "sort_order": 9,
     "formula": "Line 14 = line 7c (number of dependents) × the dependent exemption ($4,000 for 2025, $5,000 for 2026 per HB 463). No personal exemption for taxpayer/spouse.",
     "inputs": ["g_num_dependents"], "outputs": ["14"],
     "description": "Per-dependent exemption (HB 1437 removed the personal exemption; HB 463 raised the dependent amount to $5,000 for 2026). W2."},

    {"rule_id": "R-GA500-S3", "title": "Schedule 3 — part-year / nonresident proration", "rule_type": "calculation", "precedence": 5, "sort_order": 10,
     "formula": "Col A AGI (L8) = total income (Col A) ± adjustments; Col C AGI = GA-source total ± GA adjustments. L9 ratio = L8 Col C ÷ L8 Col A (0% if GA AGI ≤0; 100% if federal AGI ≤0; bounded 0-100%). L10 deduction + L11 dependents ($4,000/$5,000 × L7c) → L12; L13 = L12 × ratio; L14 = L8 Col C − L13 → Form 500 L15a. RIE earned & unearned portions prorated separately by GA-source ratio.",
     "inputs": ["g_residency_status", "g_s3_total_income_federal", "g_s3_total_income_ga", "g_s3_adj_1040_federal", "g_s3_adj_1040_ga", "g_s3_adj_500_federal", "g_s3_adj_500_ga", "g_num_dependents", "g_filing_status", "g_itemize"], "outputs": ["S3-8", "S3-9", "S3-10", "S3-11", "S3-12", "S3-13", "S3-14", "15a"],
     "description": "The 3-column GA-source proration for part-year/nonresident filers. Replaces Form 500 L9-L14; result → L15a. W6."},

    {"rule_id": "R-GA500-NOL", "title": "Schedule 4 — Georgia NOL (Part I/II)", "rule_type": "calculation", "precedence": 6, "sort_order": 11,
     "formula": "Part I loss = f(income before NOL L15a, GA exemption L14, excess nonbusiness deductions [Part II L18 = max(0, nonbusiness deductions − nonbusiness income)], excess nonbusiness capital losses, §461(l) loss). Part II splits nonbusiness income (cap gains, dividends, interest, alimony, pensions, GA RIE/US-interest/non-GA-muni adjustments) vs nonbusiness deductions (std/itemized less casualty/2106/SALT, Keogh, alimony paid, early-withdrawal penalty, IRA).",
     "inputs": ["g_nol_carryforward_pre2018", "g_nol_carryforward_2018plus"], "outputs": ["S4-8", "S4-NB-18"],
     "description": "GA NOL computation. Part I/II computed; multi-year carryover application = preparer-asserted (W3, D_GA500_009)."},

    {"rule_id": "R-GA500-NOL80", "title": "Line 15b — GA NOL 80% limitation", "rule_type": "calculation", "precedence": 7, "sort_order": 12,
     "formula": "NOL applied (line 15b) = pre-2018 carryforward (no cap) + min(2018+ carryforward, 80% × line 15a), capped overall at line 15a. Line 15c = line 15a − line 15b.",
     "inputs": ["g_nol_carryforward_pre2018", "g_nol_carryforward_2018plus"], "outputs": ["15b", "15c"],
     "description": "2018+ NOLs applied to GA income cannot exceed 80% of GA income before NOL (line 15a)."},

    {"rule_id": "R-GA500-L16-TAX", "title": "Line 16 — Georgia income tax (flat rate)", "rule_type": "calculation", "precedence": 8, "sort_order": 13,
     "formula": "Line 16 = round(max(0, line 15c) × rate), to the nearest dollar. Rate = 5.19% (2025) / 4.99% (2026).",
     "inputs": [], "outputs": ["16"],
     "description": "The Georgia flat income tax. HB 111 (2025) / HB 463 (2026). W2."},

    {"rule_id": "R-GA500-LIC", "title": "Line 17 — Low Income Credit", "rule_type": "calculation", "precedence": 9, "sort_order": 14,
     "formula": "Eligible if federal AGI (L8) < $20,000 and not a dependent. L17a = exemptions (self + spouse + dependents [exclude unborn] + age-65 count); L17b = per-exemption credit from the FAGI table ($26/$20/$14/$8/$5); L17c = L17a × L17b (≤ line 16).",
     "inputs": ["g_federal_agi", "g_lic_not_dependent", "g_filing_status", "g_num_dependents", "g_lic_age65_count"], "outputs": ["17a", "17b", "17c"],
     "description": "The Low Income Credit (a per-exemption credit that phases out at $20,000 federal AGI)."},

    {"rule_id": "R-GA500-OSC", "title": "Line 18 — Other State(s) Tax Credit", "rule_type": "calculation", "precedence": 9, "sort_order": 15,
     "formula": "Credit = lesser( income taxed by both GA and the other state × GA rate, tax actually paid to the other state on that income [reduced by other-state credits] ). → line 18.",
     "inputs": ["g_other_state_income_for_credit", "g_other_state_tax_paid", "g_other_state_credit"], "outputs": ["18", "OSC-7", "OSC-9"],
     "description": "Credit for tax paid to another state on doubly-taxed income (state/DC/US-local net income tax only)."},

    {"rule_id": "R-GA500-CC", "title": "Line 20 — IND-CR 202 child & dependent care credit", "rule_type": "calculation", "precedence": 9, "sort_order": 16,
     "formula": "GA child-care credit = 50% × the federal §21 child & dependent care credit claimed on the 1040 (Form 2441 result). → IND-CR Summary → Form 500 line 20. Not carried forward.",
     "inputs": ["g_federal_dependent_care_credit", "g_indcr_other_credits"], "outputs": ["20", "CC-3"],
     "description": "O.C.G.A. §48-7-29.10. Computed from the federal Form 2441 result."},

    {"rule_id": "R-GA500-L22-CR", "title": "Lines 22-23 — total credits and balance", "rule_type": "calculation", "precedence": 10, "sort_order": 17,
     "formula": "Line 22 = Σ(L17c + L18 + L19 + L20 + L21), capped at line 16. Line 23 = max(0, line 16 − line 22).",
     "inputs": ["g_eligible_itemizer_credit", "g_schedule2_credits"], "outputs": ["22", "23"],
     "description": "Total credits used (cannot exceed line 16) → balance."},

    {"rule_id": "R-GA500-PAY", "title": "Lines 24-30 — payments, balance due, overpayment", "rule_type": "calculation", "precedence": 11, "sort_order": 18,
     "formula": "Line 28 = L24 + L25 + L26 + L27. If line 23 > line 28: line 29 (balance due) = L23 − L28. If line 28 > line 23: line 30 (overpayment) = L28 − L23.",
     "inputs": ["g_ga_withholding_wages_1099", "g_ga_withholding_other", "g_estimated_payments", "g_refundable_credits_2b"], "outputs": ["24", "28", "29", "30"],
     "description": "Withholding + estimated + IT-560 + refundable credits → balance due or overpayment."},

    {"rule_id": "R-GA500-AMTDUE", "title": "Line 45 — amount due", "rule_type": "calculation", "precedence": 12, "sort_order": 19,
     "formula": "Line 45 (amount due, if you owe) = line 29 (balance due) + the sum of lines 32 through 44 = L29 + gift check-offs [L32-41] + UET [L42] + late-payment penalty [L43] + interest [L44]. Per the 2025 Form 500 face: 'Add Lines 29, 32 through 44.'",
     "inputs": ["g_gift_contributions_total", "g_uet_penalty", "g_late_payment_penalty", "g_interest"], "outputs": ["45"],
     "description": "The total amount owed: balance due plus voluntary contributions and penalties/interest."},

    {"rule_id": "R-GA500-REFUND", "title": "Line 46 — refund", "rule_type": "calculation", "precedence": 13, "sort_order": 20,
     "formula": "Line 46 (refund, if due) = max(0, line 30 (overpayment) − the sum of lines 31 through 44) = max(0, L30 − amount applied to next year [L31] − gift check-offs [L32-41] − UET [L42] − late-payment penalty [L43] − interest [L44]). Per the 2025 Form 500 face: 'Subtract the sum of Lines 31 thru 44 from Line 30.'",
     "inputs": ["g_amount_applied_next_year", "g_gift_contributions_total", "g_uet_penalty", "g_late_payment_penalty", "g_interest"], "outputs": ["46"],
     "description": "The refund after applied amounts, voluntary contributions, and penalties/interest."},

    {"rule_id": "R-GA500-DEPR", "title": "Depreciation / conformity decoupling (direct-entry boundary)", "rule_type": "validation", "precedence": 2, "sort_order": 21,
     "formula": "GA conforms to the IRC as of 1/1/2025 and did NOT adopt OBBBA; §168(k) bonus is disallowed and GA uses its own §179 limit. The GA-vs-federal depreciation difference is entered on Schedule 1 L3 (add) / L11 (sub) as preparer direct-entry in v1 (the depreciation engine's Asset.state_* fields auto-populate later).",
     "inputs": ["g_add_depreciation", "g_sub_depreciation"], "outputs": ["S1-3", "S1-11"],
     "description": "v1 depreciation boundary (W1). No silent gap — the lines accept entry and D_GA500_008 reminds the preparer."},
]


# ═══════════════════════════════════════════════════════════════════════════
# LINES  (Form 500 face + Schedule 1/3/4 + the RIE/military/LIC/other-state/
#         child-care worksheets; line_number unique per form, varchar(20))
# ═══════════════════════════════════════════════════════════════════════════

GA500_LINES: list[dict] = [
    # — Form 500 main face —
    {"line_number": "5", "description": "Filing status (A Single / B MFJ / C MFS / D HOH-QSS)", "line_type": "input"},
    {"line_number": "7a", "description": "Number of qualified dependents", "line_type": "input"},
    {"line_number": "7b", "description": "Number of unborn dependents", "line_type": "input"},
    {"line_number": "7c", "description": "Total number of dependents", "line_type": "input"},
    {"line_number": "8", "description": "Federal adjusted gross income (from Federal Form 1040 line 11)", "line_type": "input"},
    {"line_number": "9", "description": "Adjustments from Form 500 Schedule 1", "line_type": "calculated"},
    {"line_number": "10", "description": "Georgia adjusted gross income (net of line 8 and line 9)", "line_type": "calculated"},
    {"line_number": "11", "description": "Standard deduction ($12,000 A/C/D, $24,000 B)", "line_type": "calculated"},
    {"line_number": "12a", "description": "Federal itemized deductions (Schedule A)", "line_type": "input"},
    {"line_number": "12b", "description": "Less adjustments (other-state income tax / SALT back-out)", "line_type": "calculated"},
    {"line_number": "12c", "description": "Georgia total itemized deductions (12a − 12b)", "line_type": "calculated"},
    {"line_number": "13", "description": "Line 10 less (line 11 or line 12c)", "line_type": "calculated"},
    {"line_number": "14", "description": "Dependent exemption (line 7c × $4,000 / $5,000)", "line_type": "calculated"},
    {"line_number": "15a", "description": "Income before Georgia NOL (line 13 − line 14, or Schedule 3 line 14)", "line_type": "calculated"},
    {"line_number": "15b", "description": "Georgia NOL utilized (≤ line 15a and the 80% limit)", "line_type": "calculated"},
    {"line_number": "15c", "description": "Georgia taxable income (line 15a − line 15b)", "line_type": "calculated"},
    {"line_number": "16", "description": "Tax (line 15c × the flat rate, rounded)", "line_type": "calculated"},
    {"line_number": "17a", "description": "Low Income Credit — number of exemptions", "line_type": "calculated"},
    {"line_number": "17b", "description": "Low Income Credit — credit per exemption (table)", "line_type": "calculated"},
    {"line_number": "17c", "description": "Low Income Credit (17a × 17b)", "line_type": "calculated"},
    {"line_number": "18", "description": "Other State(s) Tax Credit", "line_type": "calculated"},
    {"line_number": "19", "description": "Georgia Eligible Itemizer Tax Credit", "line_type": "input"},
    {"line_number": "20", "description": "Credits used from the IND-CR Summary Worksheet (incl. child-care)", "line_type": "calculated"},
    {"line_number": "21", "description": "Total credits used from Schedule 2 (series-100)", "line_type": "input"},
    {"line_number": "22", "description": "Total credits used (sum of 17-21, ≤ line 16)", "line_type": "calculated"},
    {"line_number": "23", "description": "Balance (line 16 − line 22, ≥ 0)", "line_type": "calculated"},
    {"line_number": "24", "description": "Georgia income tax withheld on wages and 1099s", "line_type": "input"},
    {"line_number": "25", "description": "Other Georgia income tax withheld (G2-A/FL/LP/RP)", "line_type": "input"},
    {"line_number": "26", "description": "Estimated tax paid + Form IT-560", "line_type": "input"},
    {"line_number": "27", "description": "Schedule 2B refundable tax credits", "line_type": "input"},
    {"line_number": "28", "description": "Total prepayment credits (24+25+26+27)", "line_type": "calculated"},
    {"line_number": "29", "description": "Balance due (line 23 − line 28, if positive)", "line_type": "calculated"},
    {"line_number": "30", "description": "Overpayment (line 28 − line 23, if positive)", "line_type": "calculated"},
    {"line_number": "31", "description": "Amount to be credited to next year's estimated tax", "line_type": "input"},
    {"line_number": "32", "description": "Georgia Wildlife Conservation Fund (gift check-off)", "line_type": "input"},
    {"line_number": "33", "description": "Georgia Fund for Children and Elderly (gift check-off)", "line_type": "input"},
    {"line_number": "34", "description": "Georgia Cancer Research Fund (gift check-off)", "line_type": "input"},
    {"line_number": "35", "description": "Georgia Land Conservation Program (gift check-off)", "line_type": "input"},
    {"line_number": "36", "description": "Georgia National Guard Foundation (gift check-off)", "line_type": "input"},
    {"line_number": "37", "description": "Dog & Cat Sterilization Fund (gift check-off)", "line_type": "input"},
    {"line_number": "38", "description": "Saving the Cure Fund (gift check-off)", "line_type": "input"},
    {"line_number": "39", "description": "Realizing Educational Achievement Can Happen (REACH) Program (gift check-off)", "line_type": "input"},
    {"line_number": "40", "description": "Public Safety Memorial Fund (gift check-off)", "line_type": "input"},
    {"line_number": "41", "description": "Disabled Veterans' Scholarship Fund (gift check-off)", "line_type": "input"},
    {"line_number": "42", "description": "Form 500 UET (estimated tax penalty)", "line_type": "input"},
    {"line_number": "43", "description": "Penalty: late payment and/or late filing", "line_type": "input"},
    {"line_number": "44", "description": "Interest on unpaid tax", "line_type": "input"},
    {"line_number": "45", "description": "Amount due (line 29 + the sum of lines 32 through 44)", "line_type": "calculated"},
    {"line_number": "46", "description": "Refund (line 30 − the sum of lines 31 through 44)", "line_type": "calculated"},

    # — Schedule 1 —
    {"line_number": "S1-1", "description": "Sch 1 add: interest on non-Georgia municipal/state bonds", "line_type": "input"},
    {"line_number": "S1-2", "description": "Sch 1 add: lump-sum distributions", "line_type": "input"},
    {"line_number": "S1-3", "description": "Sch 1 add: depreciation difference (§168(k)/§179)", "line_type": "input"},
    {"line_number": "S1-4", "description": "Sch 1 add: federal NOL carryover deducted on the federal return", "line_type": "input"},
    {"line_number": "S1-5", "description": "Sch 1 add: other additions", "line_type": "input"},
    {"line_number": "S1-6", "description": "Sch 1 total additions (sum of L1-L5)", "line_type": "subtotal"},
    {"line_number": "S1-7", "description": "Sch 1 sub: retirement income exclusion (7a-7f)", "line_type": "calculated"},
    {"line_number": "S1-8", "description": "Sch 1 sub: taxable Social Security (from the federal return)", "line_type": "calculated"},
    {"line_number": "S1-9", "description": "Sch 1 sub: Path2College 529 plan", "line_type": "input"},
    {"line_number": "S1-10", "description": "Sch 1 sub: interest on U.S. obligations", "line_type": "input"},
    {"line_number": "S1-11", "description": "Sch 1 sub: depreciation difference (GA depreciation)", "line_type": "input"},
    {"line_number": "S1-12", "description": "Sch 1 sub: other adjustments", "line_type": "input"},
    {"line_number": "S1-13", "description": "Sch 1 total subtractions (sum of L7-L12)", "line_type": "subtotal"},
    {"line_number": "S1-14", "description": "Sch 1 net adjustments (L6 − L13) → Form 500 line 9", "line_type": "total"},

    # — RIE worksheet (Sch 1 p2) —
    {"line_number": "RIE-3", "description": "RIE worksheet: total earned income (L1+L2)", "line_type": "calculated"},
    {"line_number": "RIE-4", "description": "RIE worksheet: maximum earned income ($5,000)", "line_type": "informational"},
    {"line_number": "RIE-5", "description": "RIE worksheet: lesser of earned income or $5,000", "line_type": "calculated"},
    {"line_number": "RIE-14", "description": "RIE worksheet: total unearned income (L6-L13, ≥0)", "line_type": "calculated"},
    {"line_number": "RIE-15", "description": "RIE worksheet: L5 + L14", "line_type": "calculated"},
    {"line_number": "RIE-16", "description": "RIE worksheet: maximum allowable exclusion ($35,000 / $65,000)", "line_type": "informational"},
    {"line_number": "RIE-17", "description": "RIE worksheet: exclusion = lesser(L15, L16) → Sch 1 L7", "line_type": "calculated"},

    # — Military RIE worksheet (Sch 1 p3) —
    {"line_number": "MIL-2", "description": "Military worksheet: base military exclusion ($17,500)", "line_type": "informational"},
    {"line_number": "MIL-3", "description": "Military worksheet: lesser of military retirement or $17,500", "line_type": "calculated"},
    {"line_number": "MIL-7", "description": "Military worksheet: additional exclusion allowed (≤ $17,500)", "line_type": "calculated"},
    {"line_number": "MIL-8", "description": "Military worksheet: additional = lesser(L1, L7) → Sch 1 L7b/7e", "line_type": "calculated"},

    # — Schedule 3 (PY/NR) —
    {"line_number": "S3-8", "description": "Sch 3: adjusted gross income (Col A / Col C)", "line_type": "calculated"},
    {"line_number": "S3-9", "description": "Sch 3: ratio (Col C AGI ÷ Col A AGI), bounded 0-100%", "line_type": "calculated"},
    {"line_number": "S3-10", "description": "Sch 3: standard or itemized deduction", "line_type": "calculated"},
    {"line_number": "S3-11", "description": "Sch 3: dependent exemption (L7c × amount)", "line_type": "calculated"},
    {"line_number": "S3-12", "description": "Sch 3: total deductions + exemptions (L10 + L11)", "line_type": "calculated"},
    {"line_number": "S3-13", "description": "Sch 3: prorated deductions/exemptions (L12 × ratio)", "line_type": "calculated"},
    {"line_number": "S3-14", "description": "Sch 3: income before GA NOL (Col C AGI − L13) → Form 500 L15a", "line_type": "total"},

    # — Schedule 4 NOL —
    {"line_number": "S4-8", "description": "Sch 4 Part I: total Georgia NOL (loss year)", "line_type": "calculated"},
    {"line_number": "S4-NB-18", "description": "Sch 4 Part II: excess nonbusiness deductions (L17 − L10, ≥0)", "line_type": "calculated"},

    # — Low Income Credit worksheet —
    {"line_number": "LIC-4", "description": "LIC worksheet: total exemptions (base + age-65 count) → L17a", "line_type": "calculated"},
    {"line_number": "LIC-5", "description": "LIC worksheet: credit per exemption (table) → L17b", "line_type": "calculated"},
    {"line_number": "LIC-6", "description": "LIC worksheet: credit (L4 × L5) → L17c", "line_type": "calculated"},

    # — Other-state credit worksheet —
    {"line_number": "OSC-7", "description": "Other-state worksheet: tax at the GA rate on the doubly-taxed income", "line_type": "calculated"},
    {"line_number": "OSC-9", "description": "Other-state worksheet: credit = lesser(L7, tax paid to other state) → L18", "line_type": "calculated"},

    # — Child-care credit —
    {"line_number": "CC-3", "description": "IND-CR 202: GA child & dependent care credit = 50% of the federal §21 credit", "line_type": "calculated"},
]


# ═══════════════════════════════════════════════════════════════════════════
# DIAGNOSTICS  (D_GA500_*)
# ═══════════════════════════════════════════════════════════════════════════

GA500_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_GA500_001", "title": "Georgia Form 500 computed", "severity": "info",
     "condition": "Form 500 engaged (residency or GA-source income) AND line 16 computed",
     "message": "Georgia Form 500 individual income tax computed: GA taxable income (line 15c) × the flat rate (line 16).",
     "notes": "Info — the computed GA return summary."},
    {"diagnostic_id": "D_GA500_002", "title": "Retirement income exclusion — date of birth required", "severity": "error",
     "condition": "g_tp_rie_applies or g_sp_rie_applies is True AND the corresponding date of birth (or date of disability) is missing",
     "message": "The retirement income exclusion requires the taxpayer's/spouse's date of birth (and date of disability if claiming the disability exclusion). Enter it before the exclusion will compute.",
     "notes": "Error — RIE needs DOB to verify the age band and the $35,000 vs $65,000 cap."},
    {"diagnostic_id": "D_GA500_003", "title": "Retirement income exclusion applied", "severity": "info",
     "condition": "RIE worksheet line 17 > 0 for the taxpayer or spouse",
     "message": "A Georgia retirement income exclusion was applied on Schedule 1 line 7. The exclusion is capped at $35,000 (age 62-64 or permanently disabled) / $65,000 (age 65+), of which up to $5,000 may be earned income.",
     "notes": "Info — the computed RIE."},
    {"diagnostic_id": "D_GA500_004", "title": "Military retirement exclusion — age 62+ does not qualify", "severity": "warning",
     "condition": "g_tp_military_retirement or g_sp_military_retirement > 0 AND the corresponding under-62 flag is False",
     "message": "The Georgia Military Retirement Exclusion is available only to taxpayers under age 62. At age 62+, military retirement is covered by the regular retirement income exclusion instead.",
     "notes": "Warning — routes the user to the correct exclusion."},
    {"diagnostic_id": "D_GA500_005", "title": "Low Income Credit eligibility", "severity": "info",
     "condition": "federal AGI (line 8) < $20,000 AND not a dependent AND line 16 > 0",
     "message": "Eligible for the Georgia Low Income Credit (federal AGI under $20,000). The credit is the number of exemptions × a per-bracket amount and cannot exceed the tax on line 16.",
     "notes": "Info — the LIC was computed."},
    {"diagnostic_id": "D_GA500_006", "title": "Path2College 529 subtraction over the cap", "severity": "warning",
     "condition": "g_sub_path2college > $4,000 ($8,000 MFJ) per beneficiary",
     "message": "The Path2College 529 subtraction is limited to $4,000 per beneficiary ($8,000 if married filing jointly). The amount entered may exceed the cap.",
     "notes": "Warning — the 529 subtraction cap. Per-beneficiary; the preparer confirms the beneficiary count."},
    {"diagnostic_id": "D_GA500_007", "title": "GA NOL limited to 80% of Georgia income", "severity": "info",
     "condition": "g_nol_carryforward_2018plus > 0 AND line 15b was limited by 80% of line 15a",
     "message": "The 2018-and-later Georgia NOL applied to this year was limited to 80% of Georgia income before the NOL (line 15a). The remainder carries forward.",
     "notes": "Info — the 80% NOL limitation engaged."},
    {"diagnostic_id": "D_GA500_008", "title": "Georgia depreciation / conformity adjustment — verify", "severity": "warning",
     "condition": "the return has depreciable assets (Schedule C/E/F) AND Schedule 1 depreciation lines 3/11 are both blank",
     "message": "Georgia does not conform to federal §168(k) bonus depreciation or OBBBA, and uses its own §179 limit. Enter the Georgia-vs-federal depreciation difference on Schedule 1 line 3 (add) / line 11 (subtract). v1 does not auto-compute this.",
     "notes": "Warning — the W1 direct-entry boundary; no silent gap."},
    {"diagnostic_id": "D_GA500_009", "title": "Georgia NOL carryover — prepare manually", "severity": "error",
     "condition": "a GA NOL carryforward is claimed but prior-year GA returns are not in the system",
     "message": "Not supported — prepare manually: the multi-year Georgia NOL carryover application (Schedule 4 Part III) requires the prior-year Georgia returns. Enter the available carryforward amounts directly; v1 computes Part I/II and the current-year 80% limit only.",
     "notes": "RED — no silent gap on the multi-year carryover application (W3)."},
    {"diagnostic_id": "D_GA500_010", "title": "Form 500 UET penalty — prepare manually", "severity": "error",
     "condition": "an underpayment of estimated tax exists and a UET penalty (line 42) is indicated",
     "message": "Not supported — prepare manually: the Form 500 UET estimated-tax underpayment penalty is not computed in v1. Enter the penalty on line 42 directly (or attach the 500 UET exception).",
     "notes": "RED — no silent gap on the UET penalty."},
    {"diagnostic_id": "D_GA500_011", "title": "Part-year / nonresident — Schedule 3 in use", "severity": "info",
     "condition": "g_residency_status is part_year or nonresident",
     "message": "Part-year/nonresident return: Georgia taxable income is computed on Schedule 3 (the GA-source ratio prorates the deduction and exemptions). Form 500 lines 9-14 are omitted.",
     "notes": "Info — the Schedule 3 path is active."},
    {"diagnostic_id": "D_GA500_012", "title": "Total credits exceed the tax", "severity": "warning",
     "condition": "the sum of credits (lines 17-21) exceeds line 16",
     "message": "Total nonrefundable credits used (lines 17-21) cannot exceed the tax on line 16. The credit used has been capped at the tax.",
     "notes": "Warning — the line 22 cap engaged."},
]


# ═══════════════════════════════════════════════════════════════════════════
# TEST SCENARIOS  (re-derived independently by check_ga500_integrity.py)
# ═══════════════════════════════════════════════════════════════════════════

GA500_SCENARIOS: list[dict] = [
    {"scenario_name": "GA500-T1 — full-year single, standard deduction, no dependents (2025)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "g_residency_status": "full_year", "g_filing_status": "A", "g_num_dependents": 0, "g_federal_agi": 60000},
     "expected_outputs": {"8": 60000, "9": 0, "10": 60000, "11": 12000, "13": 48000, "14": 0, "15a": 48000, "15b": 0, "15c": 48000, "16": 2491, "22": 0, "23": 2491},
     "notes": "Baseline. 48,000 × 5.19% = 2,491.20 → 2,491."},
    {"scenario_name": "GA500-T2 — full-year MFJ, standard deduction, 2 dependents (2025)", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"tax_year": 2025, "g_residency_status": "full_year", "g_filing_status": "B", "g_num_dependents": 2, "g_federal_agi": 100000},
     "expected_outputs": {"10": 100000, "11": 24000, "13": 76000, "14": 8000, "15a": 68000, "15c": 68000, "16": 3529},
     "notes": "MFJ std 24,000; 2 deps × 4,000 = 8,000. 68,000 × 5.19% = 3,529.20 → 3,529."},
    {"scenario_name": "GA500-T3 — retirement income exclusion, age 65+ (2025)", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"tax_year": 2025, "g_residency_status": "full_year", "g_filing_status": "A", "g_num_dependents": 0, "g_federal_agi": 88000,
                "g_tp_rie_applies": True, "g_tp_age_65_plus": True, "g_tp_rie_salary_wages": 8000, "g_tp_rie_interest": 30000, "g_tp_rie_taxable_pension": 50000},
     "expected_outputs": {"RIE-5": 5000, "RIE-14": 80000, "RIE-15": 85000, "RIE-17": 65000, "S1-7": 65000, "9": -65000, "10": 23000, "11": 12000, "13": 11000, "15c": 11000, "16": 571},
     "notes": "Earned 8,000 capped at 5,000; unearned 30,000+50,000=80,000; L15=85,000 capped at 65,000. GA AGI 23,000 − 12,000 = 11,000 × 5.19% = 570.90 → 571."},
    {"scenario_name": "GA500-T4 — retirement income exclusion, age 62-64 ($35k cap) (2025)", "scenario_type": "edge_case", "sort_order": 4,
     "inputs": {"tax_year": 2025, "g_residency_status": "full_year", "g_filing_status": "A", "g_num_dependents": 0, "g_federal_agi": 88000,
                "g_tp_rie_applies": True, "g_tp_age_65_plus": False, "g_tp_rie_salary_wages": 8000, "g_tp_rie_interest": 30000, "g_tp_rie_taxable_pension": 50000},
     "expected_outputs": {"RIE-15": 85000, "RIE-17": 35000, "S1-7": 35000, "9": -35000, "10": 53000, "13": 41000, "15c": 41000, "16": 2128},
     "notes": "Same income but the 62-64 cap is 35,000. 53,000 − 12,000 = 41,000 × 5.19% = 2,127.90 → 2,128."},
    {"scenario_name": "GA500-T5 — military retirement exclusion, under 62 (2025)", "scenario_type": "normal", "sort_order": 5,
     "inputs": {"tax_year": 2025, "g_residency_status": "full_year", "g_filing_status": "A", "g_num_dependents": 0, "g_federal_agi": 60000,
                "g_tp_military_under62": True, "g_tp_military_retirement": 40000, "g_tp_military_ga_earned": 20000},
     "expected_outputs": {"MIL-3": 17500, "MIL-7": 17500, "MIL-8": 17500, "S1-7": 35000, "9": -35000, "10": 25000, "13": 13000, "15c": 13000, "16": 675},
     "notes": "Base 17,500 + additional 17,500 (GA earned 20,000 ≥ 17,501) = 35,000. 25,000 − 12,000 = 13,000 × 5.19% = 674.70 → 675."},
    {"scenario_name": "GA500-T6 — Low Income Credit (2025)", "scenario_type": "edge_case", "sort_order": 6,
     "inputs": {"tax_year": 2025, "g_residency_status": "full_year", "g_filing_status": "A", "g_num_dependents": 0, "g_federal_agi": 18000, "g_lic_not_dependent": True, "g_lic_age65_count": 0},
     "expected_outputs": {"10": 18000, "11": 12000, "13": 6000, "15c": 6000, "16": 311, "17a": 1, "17b": 5, "17c": 5, "22": 5, "23": 306},
     "notes": "FAGI 18,000 → LIC bracket 15,000-19,999 = $5/exemption × 1 exemption = 5. Tax 6,000 × 5.19% = 311.40 → 311; balance 306."},
    {"scenario_name": "GA500-T7 — itemized with the 12b SALT back-out (2025)", "scenario_type": "normal", "sort_order": 7,
     "inputs": {"tax_year": 2025, "g_residency_status": "full_year", "g_filing_status": "A", "g_num_dependents": 0, "g_federal_agi": 80000,
                "g_itemize": True, "g_federal_itemized": 30000, "g_other_state_income_tax": 6000, "g_sch_a_line5d_total": 15000},
     "expected_outputs": {"12a": 30000, "12b": 4000, "12c": 26000, "13": 54000, "15c": 54000, "16": 2803},
     "notes": "12b = (6,000/15,000) × lesser(15,000, 10,000) = 0.4 × 10,000 = 4,000. 30,000 − 4,000 = 26,000 GA itemized. 80,000 − 26,000 = 54,000 × 5.19% = 2,802.60 → 2,803."},
    {"scenario_name": "GA500-T8 — nonresident Schedule 3 proration (2025)", "scenario_type": "edge_case", "sort_order": 8,
     "inputs": {"tax_year": 2025, "g_residency_status": "nonresident", "g_filing_status": "A", "g_num_dependents": 0,
                "g_s3_total_income_federal": 50000, "g_s3_total_income_ga": 25000},
     "expected_outputs": {"S3-8": 50000, "S3-9": "0.5000", "S3-10": 12000, "S3-11": 0, "S3-12": 12000, "S3-13": 6000, "S3-14": 19000, "15a": 19000, "15c": 19000, "16": 986},
     "notes": "Ratio 25,000/50,000 = 50%. Deduction+exemption 12,000 × 50% = 6,000 prorated. GA income 25,000 − 6,000 = 19,000 × 5.19% = 986.10 → 986."},
    {"scenario_name": "GA500-T9 — GA NOL with the 80% limitation (2025)", "scenario_type": "edge_case", "sort_order": 9,
     "inputs": {"tax_year": 2025, "g_residency_status": "full_year", "g_filing_status": "A", "g_num_dependents": 0, "g_federal_agi": 62000, "g_nol_carryforward_2018plus": 60000},
     "expected_outputs": {"10": 62000, "11": 12000, "13": 50000, "15a": 50000, "15b": 40000, "15c": 10000, "16": 519},
     "notes": "Income before NOL 50,000; 2018+ NOL 60,000 limited to 80% × 50,000 = 40,000. 50,000 − 40,000 = 10,000 × 5.19% = 519.00 → 519."},
    {"scenario_name": "GA500-T10 — IND-CR 202 child & dependent care credit (2025)", "scenario_type": "normal", "sort_order": 10,
     "inputs": {"tax_year": 2025, "g_residency_status": "full_year", "g_filing_status": "A", "g_num_dependents": 0, "g_federal_agi": 70000, "g_federal_dependent_care_credit": 1200},
     "expected_outputs": {"13": 58000, "15c": 58000, "16": 3010, "CC-3": 600, "20": 600, "22": 600, "23": 2410},
     "notes": "GA child-care = 50% × 1,200 = 600. Tax 58,000 × 5.19% = 3,010.20 → 3,010; balance 2,410."},
    {"scenario_name": "GA500-T11 — TY2026 constants (rate 4.99%, std $30k MFJ, dependent $5,000)", "scenario_type": "normal", "sort_order": 11,
     "inputs": {"tax_year": 2026, "g_residency_status": "full_year", "g_filing_status": "B", "g_num_dependents": 2, "g_federal_agi": 100000},
     "expected_outputs": {"10": 100000, "11": 30000, "13": 70000, "14": 10000, "15a": 60000, "15c": 60000, "16": 2994},
     "notes": "2026 (HB 463): std deduction MFJ 30,000; dependent exemption 5,000 → 2 × 5,000 = 10,000; rate 4.99%. 70,000 − 10,000 = 60,000 × 4.99% = 2,994.00 → 2,994."},
    {"scenario_name": "GA500-T12 — taxable Social Security subtraction (2025)", "scenario_type": "normal", "sort_order": 12,
     "inputs": {"tax_year": 2025, "g_residency_status": "full_year", "g_filing_status": "A", "g_num_dependents": 0, "g_federal_agi": 50000, "g_federal_taxable_ss": 10000},
     "expected_outputs": {"S1-8": 10000, "9": -10000, "10": 40000, "11": 12000, "13": 28000, "15c": 28000, "16": 1453},
     "notes": "Taxable SS 10,000 subtracted. GA AGI 40,000 − 12,000 = 28,000 × 5.19% = 1,453.20 → 1,453."},
    {"scenario_name": "GA500-T13 — overpayment → refund, with amount applied next year (2025)", "scenario_type": "normal", "sort_order": 13,
     "inputs": {"tax_year": 2025, "g_residency_status": "full_year", "g_filing_status": "A", "g_num_dependents": 0, "g_federal_agi": 60000,
                "g_ga_withholding_wages_1099": 5000, "g_amount_applied_next_year": 500},
     "expected_outputs": {"16": 2491, "23": 2491, "28": 5000, "29": 0, "30": 2509, "45": 0, "46": 2009},
     "notes": "Tax 2,491; withholding 5,000 → overpayment 2,509. L46 refund = 2,509 − 500 applied = 2,009; no balance due so L45 = 0."},
    {"scenario_name": "GA500-T14 — balance due → amount due with check-offs + penalties (2025)", "scenario_type": "edge_case", "sort_order": 14,
     "inputs": {"tax_year": 2025, "g_residency_status": "full_year", "g_filing_status": "A", "g_num_dependents": 0, "g_federal_agi": 60000,
                "g_ga_withholding_wages_1099": 2000, "g_gift_contributions_total": 50,
                "g_uet_penalty": 30, "g_late_payment_penalty": 10, "g_interest": 5},
     "expected_outputs": {"16": 2491, "23": 2491, "28": 2000, "29": 491, "30": 0, "45": 586, "46": 0},
     "notes": "Tax 2,491; withholding 2,000 → balance due 491. L45 amount due = 491 + 50 check-offs + (30+10+5) penalties/interest = 586; no overpayment so L46 = 0. UET=line 42, late=line 43, interest=line 44 (the 2025 form-face line numbers)."},
]


# ═══════════════════════════════════════════════════════════════════════════
# RULE → AUTHORITY LINKS  (rule_id, source_code, support_level, note)
# ═══════════════════════════════════════════════════════════════════════════

GA500_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-GA500-L8-AGI", "GA_2025_FORM_500", "primary", "Form 500 line 8 = federal AGI"),
    ("R-GA500-L8-AGI", "IRS_2025_1040_FORM", "supporting", "Federal 1040 line 11 source"),
    ("R-GA500-L9-S1", "GA_2025_FORM_500", "primary", "Schedule 1 additions/subtractions → line 9"),
    ("R-GA500-SS", "GA_2025_IT511", "primary", "Schedule 1 line 8 taxable Social Security subtraction"),
    ("R-GA500-RIE", "GA_OCGA_48_7", "primary", "§48-7-27(a)(5) retirement income exclusion"),
    ("R-GA500-RIE", "GA_2025_FORM_500", "primary", "RIE worksheet (Schedule 1 page 2)"),
    ("R-GA500-MIL", "GA_OCGA_48_7", "primary", "§48-7-27(a)(5.1) military retirement exclusion"),
    ("R-GA500-MIL", "GA_2025_FORM_500", "primary", "Military RIE worksheet (Schedule 1 page 3)"),
    ("R-GA500-DED", "GA_2025_IT511", "primary", "Standard deduction + the 12b SALT adjustment"),
    ("R-GA500-L14-DEP", "GA_2025_IT511", "primary", "Dependent exemption $4,000 (2025)"),
    ("R-GA500-L14-DEP", "GA_HB463_2026", "primary", "Dependent exemption $5,000 (2026)"),
    ("R-GA500-S3", "GA_2025_FORM_500", "primary", "Schedule 3 part-year/nonresident proration"),
    ("R-GA500-NOL", "GA_2025_FORM_500", "primary", "Schedule 4 GA NOL Part I/II"),
    ("R-GA500-NOL80", "GA_2025_IT511", "primary", "GA NOL 80% limitation worksheet"),
    ("R-GA500-L16-TAX", "GA_2025_IT511", "primary", "Tax = line 15c × 5.19% (2025)"),
    ("R-GA500-L16-TAX", "GA_HB463_2026", "primary", "Rate 4.99% (2026)"),
    ("R-GA500-LIC", "GA_2025_IT511", "primary", "Low Income Credit worksheet + table"),
    ("R-GA500-OSC", "GA_2025_IT511", "primary", "Other-state tax credit worksheet"),
    ("R-GA500-CC", "GA_2025_FORM_500", "primary", "IND-CR 202 child & dependent care credit"),
    ("R-GA500-CC", "GA_OCGA_48_7", "primary", "§48-7-29.10 child & dependent care credit (50%)"),
    ("R-GA500-DEPR", "GA_2025_IT511", "primary", "GA conformity (IRC 1/1/2025, no OBBBA, §168(k) disallowance)"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS  (FA-GA500-* — exported, wired in tts-tax-app)
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-GA500-01", "assertion_type": "flow_assertion", "entity_types": ["1040"], "sort_order": 1,
     "title": "Form 500 line 8 ← federal 1040 line 11", "description": "Validates R-GA500-L8-AGI. Form 500 line 8 (Georgia's starting point) equals the child 1040's federal AGI (line 11).",
     "definition": {"kind": "flow_assertion", "form": "500", "target_line": "8", "must_read_from": ["1040.11"]}},
    {"assertion_id": "FA-GA500-02", "assertion_type": "flow_assertion", "entity_types": ["1040"], "sort_order": 2,
     "title": "Schedule 1 line 14 → Form 500 line 9", "description": "Validates R-GA500-L9-S1. Schedule 1 net adjustments (additions − subtractions) flow to Form 500 line 9.",
     "definition": {"kind": "flow_assertion", "form": "500", "source_line": "S1-14", "must_write_to": ["500.9"]}},
    {"assertion_id": "FA-GA500-03", "assertion_type": "flow_assertion", "entity_types": ["1040"], "sort_order": 3,
     "title": "Line 16 = line 15c × the flat rate", "description": "Validates R-GA500-L16-TAX. The GA tax is GA taxable income (line 15c) × the flat rate (5.19% 2025 / 4.99% 2026), rounded.",
     "definition": {"kind": "flow_assertion", "form": "500", "source_line": "15c", "must_write_to": ["500.16"]}},
    {"assertion_id": "FA-GA500-04", "assertion_type": "flow_assertion", "entity_types": ["1040"], "sort_order": 4,
     "title": "RIE worksheet line 17 → Schedule 1 line 7", "description": "Validates R-GA500-RIE. The retirement income exclusion (worksheet line 17, capped $35k/$65k, ≤$5k earned) flows to Schedule 1 line 7.",
     "definition": {"kind": "flow_assertion", "form": "500", "source_line": "RIE-17", "must_write_to": ["500.S1-7"]}},
    {"assertion_id": "FA-GA500-05", "assertion_type": "table_invariant", "entity_types": ["1040"], "sort_order": 5,
     "title": "GA NOL applied ≤ 80% of GA income before NOL", "description": "Validates R-GA500-NOL80. The 2018+ GA NOL applied on line 15b cannot exceed 80% of line 15a.",
     "definition": {"kind": "table_invariant", "form": "500", "rule": "line_15b_2018plus <= 0.80 * line_15a"}},
    {"assertion_id": "FA-GA500-06", "assertion_type": "flow_assertion", "entity_types": ["1040"], "sort_order": 6,
     "title": "GA child-care credit = 50% × federal §21", "description": "Validates R-GA500-CC. The IND-CR 202 GA child & dependent care credit equals 50% of the federal Form 2441 §21 credit, → Form 500 line 20.",
     "definition": {"kind": "flow_assertion", "form": "500", "source_line": "CC-3", "must_write_to": ["500.20"]}},
    {"assertion_id": "FA-GA500-07", "assertion_type": "table_invariant", "entity_types": ["1040"], "sort_order": 7,
     "title": "Total credits used ≤ line 16", "description": "Validates R-GA500-L22-CR. The sum of nonrefundable credits (lines 17-21) on line 22 cannot exceed the tax on line 16.",
     "definition": {"kind": "table_invariant", "form": "500", "rule": "line_22 <= line_16"}},
    {"assertion_id": "FA-GA500-08", "assertion_type": "flow_assertion", "entity_types": ["1040"], "sort_order": 8,
     "title": "Low Income Credit = exemptions × table credit", "description": "Validates R-GA500-LIC. Line 17c = line 17a (exemptions) × line 17b (the per-FAGI-bracket credit), eligible only when federal AGI < $20,000.",
     "definition": {"kind": "flow_assertion", "form": "500", "source_line": "17c", "must_write_to": ["500.22"]}},
    {"assertion_id": "FA-GA500-09", "assertion_type": "table_invariant", "entity_types": ["1040"], "sort_order": 9,
     "title": "Schedule 3 ratio is bounded 0-100%", "description": "Validates R-GA500-S3. The part-year/nonresident ratio (line 9 = GA AGI ÷ federal AGI) is ≥ 0% and ≤ 100%, and prorates the deductions+exemptions (line 13).",
     "definition": {"kind": "table_invariant", "form": "500", "rule": "0 <= line_S3_9 <= 1"}},
    {"assertion_id": "FA-GA500-10", "assertion_type": "reconciliation", "entity_types": ["1040"], "sort_order": 10,
     "title": "Constants pinned both years", "description": "Pins the verified constants: rate 5.19% (2025) / 4.99% (2026); std deduction $12k/$24k; dependent exemption $4,000 (2025) / $5,000 (2026); RIE $35k/$65k (≤$5k earned); military $17,500/$35,000; LIC table $26/$20/$14/$8/$5.",
     "definition": {"kind": "reconciliation", "form": "500", "constants": {"rate_2025": "0.0519", "rate_2026": "0.0499", "std_mfj": 24000, "std_other": 12000, "dep_2025": 4000, "dep_2026": 5000, "rie_62_64": 35000, "rie_65": 65000, "rie_earned_cap": 5000, "mil_base": 17500, "mil_max": 35000}}},
    {"assertion_id": "FA-GA500-11", "assertion_type": "flow_assertion", "entity_types": ["1040"], "sort_order": 11,
     "title": "Taxable SS subtracted on Schedule 1 line 8", "description": "Validates R-GA500-SS. The federally-taxable Social Security (1040 line 6b) is fully subtracted on Schedule 1 line 8 (GA does not tax Social Security).",
     "definition": {"kind": "flow_assertion", "form": "500", "source_line": "1040.6b", "must_write_to": ["500.S1-8"]}},
    {"assertion_id": "FA-GA500-12", "assertion_type": "table_invariant", "entity_types": ["1040"], "sort_order": 12,
     "title": "No silent gap — depreciation / UET / NOL-carryover RED-defers", "description": "Validates the v1 boundaries: the §168(k)/§179 depreciation difference (D_GA500_008), the UET penalty (D_GA500_010), and the multi-year NOL carryover (D_GA500_009) are flagged for manual entry, never silently computed wrong.",
     "definition": {"kind": "table_invariant", "form": "500", "rule": "depreciation_and_uet_and_nol_carryover_are_flagged_not_silent"}},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORMS container
# ═══════════════════════════════════════════════════════════════════════════

FORMS: list[dict] = [
    {
        "identity": {
            "form_number": "500",
            "form_title": "Georgia Form 500 — Individual Income Tax Return (TY2025)",
            "notes": (
                "NEW spec (no prior RS draft — lookup/500, GA_500, GA500 all 404). The FIRST state "
                "individual spec. Georgia Form 500: federal AGI (1040 L11) → Schedule 1 GA "
                "additions/subtractions (the retirement income exclusion is the center of gravity) → "
                "standard/itemized deduction → dependent exemption → GA NOL (Schedule 4, 80% limit) → "
                "flat tax (5.19% 2025 / 4.99% 2026) → credits (Low Income, Other-State, IND-CR 202 "
                "child-care = 50% of federal §21, Schedule 2) → withholding/payments → refund/due. v1 "
                "COMPUTES resident + part-year/nonresident (Schedule 3), both retirement exclusions "
                "(standard + military), the GA NOL, the LIC, and the child-care credit. DIRECT-ENTRY: "
                "the §168(k)/§179/OBBBA depreciation difference (Sch 1 L3/L11 — GA conforms to the IRC "
                "as of 1/1/2025, not OBBBA; W1) + the other Sch 1 adjustments + series-100 credits. "
                "RED-defers the UET penalty + the multi-year NOL carryover application. Attaches to the "
                "child 1040 via the state_returns relation (the GA-600S precedent). Constants verified "
                "vs the GA-DOR 2025 Form 500 + IT-511 PDFs + HB 111 + HB 463 (TY2026). Full source "
                "brief: tts-tax-app/server/specs/_ga500_source_brief.md."
            ),
        },
        "facts": GA500_FACTS,
        "rules": GA500_RULES,
        "lines": GA500_LINES,
        "diagnostics": GA500_DIAGNOSTICS,
        "scenarios": GA500_SCENARIOS,
        "rule_links": GA500_RULE_LINKS,
    },
]


class Command(BaseCommand):
    help = (
        "Load the GA Form 500 spec (Georgia individual income tax — federal AGI "
        "start, Schedule 1 GA adjustments, the retirement income exclusion, the "
        "flat tax rate, GA NOL, the Low Income Credit, part-year/nonresident "
        "Schedule 3). Refuses to seed until Ken sets READY_TO_SEED=True after the "
        "in-session review walk."
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()

        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad GA FORM 500 spec (Georgia Individual Income Tax)\n"))

        self._load_topics()
        sources = self._load_sources()
        self._load_new_excerpts_on_existing(sources)
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

    # ─────────────────────────────────────────────────────────────────────────
    # Safety guard
    # ─────────────────────────────────────────────────────────────────────────

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
                "\nREFUSING TO SEED GA FORM 500: not cleared to seed.\n\n"
                "Content is authored, but seeding is gated until Ken reviews the packet\n"
                "(W1 the depreciation/conformity decoupling direct-entry boundary; W2 the\n"
                "TY2026 HB 463 constants; W3 the Schedule 4 NOL carryover scope; W4 the 12b\n"
                "SALT back-out; W5 the RIE classification + taxable-SS sourcing; W6 the\n"
                "Schedule 3 part-year/nonresident proration) and flips the sentinel.\n\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True to proceed)\n\n"
                f"Currently empty / placeholder:\n  {still_empty}\n\n"
                "To proceed: review the module-level data lists (and the source brief at\n"
                "tts-tax-app/server/specs/_ga500_source_brief.md), then set READY_TO_SEED\n"
                "= True. Idempotent via update_or_create — safe to re-run after edits."
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Topics / sources (mirror load_1040_form_8615.py exactly)
    # ─────────────────────────────────────────────────────────────────────────

    def _load_topics(self):
        ct = 0
        for code, name in AUTHORITY_TOPICS:
            _, created = AuthorityTopic.objects.update_or_create(
                topic_code=code, defaults={"topic_name": name},
            )
            if created:
                ct += 1
        self.stdout.write(f"Topics: {ct} new ({len(AUTHORITY_TOPICS)} total in batch)")

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
                    AuthoritySourceTopic.objects.get_or_create(
                        authority_source=source, authority_topic=topic,
                    )
        for code in EXISTING_SOURCES_TO_REFERENCE:
            src = AuthoritySource.objects.filter(source_code=code).first()
            if src:
                sources[code] = src
            else:
                self.stdout.write(self.style.WARNING(f"  existing source {code} NOT FOUND — links to it will be skipped"))
        self.stdout.write(f"Sources ready: {len(sources)}")
        return sources

    def _load_new_excerpts_on_existing(self, sources):
        ct = 0
        for code, exc in NEW_EXCERPTS_ON_EXISTING:
            src = sources.get(code) or AuthoritySource.objects.filter(source_code=code).first()
            if not src:
                self.stdout.write(self.style.WARNING(f"  source {code} not found — skipping new excerpt"))
                continue
            exc = dict(exc)
            AuthorityExcerpt.objects.update_or_create(
                authority_source=src, excerpt_label=exc["excerpt_label"], defaults=exc,
            )
            ct += 1
        if ct:
            self.stdout.write(f"  {ct} new excerpts on existing sources")

    # ─────────────────────────────────────────────────────────────────────────
    # Per-form helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _upsert_form(self, identity: dict) -> TaxForm:
        form, created = TaxForm.objects.update_or_create(
            form_number=identity["form_number"],
            jurisdiction=FORM_JURISDICTION,
            tax_year=FORM_TAX_YEAR,
            version=FORM_VERSION,
            defaults={
                "form_title": identity["form_title"],
                "entity_types": FORM_ENTITY_TYPES,
                "status": FORM_STATUS,
                "notes": identity["notes"],
            },
        )
        self.stdout.write(f"{'Created' if created else 'Updated'} {identity['form_number']}")
        return form

    def _upsert_facts(self, form, facts):
        for f in facts:
            f = dict(f)
            FormFact.objects.update_or_create(
                tax_form=form, fact_key=f.pop("fact_key"), defaults=f,
            )
        self.stdout.write(f"  {len(facts)} facts")

    def _upsert_rules(self, form, rules_data) -> dict:
        created = {}
        for r in rules_data:
            r = dict(r)
            rule, _ = FormRule.objects.update_or_create(
                tax_form=form, rule_id=r.pop("rule_id"), defaults=r,
            )
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
            FormLine.objects.update_or_create(
                tax_form=form, line_number=ln.pop("line_number"), defaults=ln,
            )
        self.stdout.write(f"  {len(lines)} lines")

    def _upsert_diagnostics(self, form, diagnostics):
        for d in diagnostics:
            d = dict(d)
            FormDiagnostic.objects.update_or_create(
                tax_form=form, diagnostic_id=d.pop("diagnostic_id"), defaults=d,
            )
        self.stdout.write(f"  {len(diagnostics)} diagnostics")

    def _upsert_tests(self, form, scenarios):
        for t in scenarios:
            t = dict(t)
            TestScenario.objects.update_or_create(
                tax_form=form, scenario_name=t.pop("scenario_name"), defaults=t,
            )
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
            FlowAssertion.objects.update_or_create(
                assertion_id=a.pop("assertion_id"), defaults=a,
            )
        self.stdout.write(f"  {len(FLOW_ASSERTIONS)} flow assertions")

    def _report_totals(self):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("GA FORM 500 loaded.")
        self.stdout.write(
            f"  facts {len(GA500_FACTS)} / rules {len(GA500_RULES)} / lines {len(GA500_LINES)} / "
            f"diagnostics {len(GA500_DIAGNOSTICS)} / tests {len(GA500_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}"
        )
        self.stdout.write("=" * 60)
