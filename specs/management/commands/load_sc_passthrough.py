"""Load the SC pass-through entity specs — SC1065 (Partnership) + SC1120S (S-Corp) + SC PTET (TY2025).

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
Two South Carolina pass-through ENTITY returns, sharing the SC "Active Trade or
Business" (ATB) elective entity-level tax — the SC PTET (S.C. Code §12-6-545(G),
Act 61 of 2021), computed on Form I-435 at a FLAT 3%:

  • SC1065  — Partnership Return (Rev. 6/18/25). Federal Schedule K → Schedule
    SC-K (SC adjustments + allocation/apportionment) → SC-taxable net business
    income (SC-K L21 → page-1 L1). ATB election (page-1 checkbox) taxes ATB
    income at 3% at the ENTITY level (L2→L3), which then DROPS OUT of both the
    partners' taxable income AND the 5% nonresident-withholding base (L6 = L1−L2).

  • SC1120S — S Corporation Income Tax Return (Rev. 6/17/25). Two-part return:
    Part I income tax (federal 1120-S Sch K → SC adjustments → the same I-435 3%
    ATB tax on L5/L6 + a GENERAL 5% SC income tax on non-ATB SC net income L9) +
    Part II the LICENSE FEE (capital & paid-in surplus × .001 + $15, min $25).
    Nonresident shareholder withholding rides a SEPARATE SC1120S-WH form (5%).

THE HEADLINE FEATURE: the SC PTET / ATB election. Unlike GA's 5.19% irrevocable
election, SC's is an ANNUAL NON-BINDING page-1 checkbox taxing ATB income (only)
at 3%. The owner side is an EXCLUSION, not a credit (§12-6-545(G)(3)): the owner
SUBTRACTS the entity-taxed amount on I-335 line 6 (partner ← SC1065 K-1 line 14;
shareholder ← SC1120S K-1 line 13). Entity-taxed ATB is also exempt from the 5%
nonresident withholding.

This extends the GA-700 + PTET work to Georgia's neighbors (Ken: "states adjacent
to Georgia"). GA-700 (load_ga700.py) is the direct partnership+PTET structural
precedent; SC1040 (load_sc1040.py) supplies the reusable SC conformity/depreciation
authority sources (SC_ACT63_2025_CONFORMITY, SC_RR_05_2_DEPR). Attaches to the
federal 1065 / 1120-S returns in tts via state_returns.

NO prior RS spec exists (lookup/SC1065/, lookup/SC1120S/ → 404). NEW forms.

═══════════════════════════════════════════════════════════════════════════
v1 SCOPE — LOCKED (Ken's walk 2026-07-05, 4 AskUserQuestion decisions; DECISIONS D-9)
See sc1065_source_brief.md §8.
═══════════════════════════════════════════════════════════════════════════
Q1 = BOTH SC1065 and SC1120S this session.
Q2 = COMPUTE the §168(k) bonus add-back structure + the §179 conformity delta
     (direct-entry the asset-level SC-4562 figures the engine can't reach).
Q3 = §179 2025 cap = the INDEXED $1,250,000 / $3,130,000 (Reading A — conformed
     IRC §179 incl. its indexing provision; Rev. Proc. 2024-40; pending SCDOR
     confirmation). NOT the conservative 2024 $1,220,000 / $3,050,000.
Q4 = COMPUTE apportionment methods 1 (sales-only, TPP dealers) & 2 (gross-receipts,
     service/financial) via a business-type selector (4 decimals) + the 5%
     nonresident withholding with the full exemption set; RED-defer special/
     individualized apportionment + the composite return; direct-entry SC1040TC credits.

COMPUTES (v1):
  • SC1065: Schedule SC-K net business income (L21→L1); dual-method apportionment
    (L19 factor, 4 decimals); the 3% ATB entity tax (L2→L3→L5); the owner-exclusion
    flow (K-1 L14 → I-335 L6); the withholding displacement (L6 = L1−L2); the 5%
    nonresident withholding (L8→L9); total tax (L10).
  • SC1120S: Part I (L3 = L1+L2 SC adjustments; L4 apportioned; the 3% ATB tax
    L5/L6; the 5% general SC income tax on non-ATB net L8→L9; total L10); Part II
    the LICENSE FEE (L20 = L19 × .001 + $15, min $25).
  • Both: the §168(k) bonus add-back (year-1 add-back + remaining-life SC subtraction)
    and the §179 conformity delta (federal − SC-capped, separately stated to owners).

DIRECT-ENTRY (line exists, diagnostic prompts, preparer keys the figure):
  • Asset-level SC-4562 depreciation figures (bonus add-back / SC subtraction);
    SC1040TC nonrefundable credits; the ATB income active/passive split (I-435
    Col C — "reasonably related to personal services" is a judgment call, W4).

RED-DEFERS (each its own "prepare manually" RED — no silent gap):
  • Special / individualized apportionment (§12-6-2310 / §12-6-2320).
  • Composite return (I-348 filing instr. / I-338 affidavit; extension SC4868).
  • SC1120S multi-state license-fee apportionment (Schedules E/H); Schedule D Annual Report.

═══════════════════════════════════════════════════════════════════════════
requires_human_review WALK ITEMS (for Ken's in-session review before seeding)
═══════════════════════════════════════════════════════════════════════════
W1. §179 2025 DOLLAR CAP — Ken chose Reading A: the INDEXED $1,250,000 / $3,130,000
    (Rev. Proc. 2024-40), flowing through the conformed IRC §179 indexing provision.
    SCDOR states NO §179 dollar figure — cited to conformed IRC §179 at 12/31/2024,
    pending SCDOR confirmation. Matches the SC1040 pin. CONFIRM.
W2. H.3368 CONFORMITY LIVE WIRE — a pending SC bill would conform SC to OBBBA
    mid-season (§179 → $2.5M/$4M, bonus treatment changes). ALL depreciation/§179
    logic is stale if enacted. Re-verify before relying. CONFIRM the 12/31/2024 date holds.
W3. ATB RATE 3% (I-435 L17) + NRW RATE 5% (SC1065 instr. p.1) + S-corp GENERAL rate
    5% (SC1120S L9) + LICENSE FEE .001 + $15 (min $25) — all primary-verified verbatim.
    Year-keyed. CONFIRM.
W4. ATB ACTIVE/PASSIVE SEGREGATION (I-435 Col C) is preparer judgment ("reasonably
    related to personal services"); v1 direct-enters the ATB income, computes the 3% + flow.
W5. APPORTIONMENT METHOD SELECTION by business type (TPP → sales-only; service/
    financial → gross-receipts); 4 decimals. Special/individualized RED-deferred. CONFIRM.

═══════════════════════════════════════════════════════════════════════════
VERIFIED STRUCTURE + CONSTANTS (READ 2026-07-05 from the FINAL 2025 SCDOR PDFs —
NOT memory: I-435 Rev. 1/30/25; SC1065 Rev. 6/18/25; SC1120S Rev. 6/17/25; I-335
Rev. 6/17/25; SC1120I "What's New"; §12-6-545; RR #21-15/#22-5. Full source brief:
sc1065_source_brief.md.)
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
# seed, export"): W1 §179 = INDEXED $1.25M/$3.13M (Reading A, his Q3 pick; pending
# SCDOR confirmation), W2 the 12/31/2024 conformity + the H.3368 live wire, W3 the
# 3% ATB / 5% NRW / 5% S-corp / license-fee (×.001 + $15, min $25) rates, W4 the ATB
# active/passive direct-entry, W5 the dual-method apportionment — all blessed as
# in-spec re-verify flags. Validated on a throwaway SQLite DB (SC1065: 25 facts /
# 8 rules / 16 lines / 10 diag / 7 tests; SC1120S: 14 facts / 9 rules / 13 lines /
# 6 diag / 6 tests; 8 FA; every rule cited; CharField caps clean).
# ═══════════════════════════════════════════════════════════════════════════
READY_TO_SEED = True


FORM_JURISDICTION = "SC"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS (year-keyed; cited in sc1065_source_brief.md; never memory)
# ═══════════════════════════════════════════════════════════════════════════

# ATB (PTET) flat rate — I-435 L17 "multiply line 16 by 3%". W3. Stable/permanent.
SC_ATB_RATE: dict[int, str] = {2025: "0.03"}

# General S-corp SC income tax rate — SC1120S L9 (L8 × 5%). W3.
SC_SCORP_RATE: dict[int, str] = {2025: "0.05"}

# Nonresident partner/shareholder withholding — SC1065 L9 / SC1120S-WH. W3.
SC_NRW_RATE: dict[int, str] = {2025: "0.05"}

# License fee (SC1120S Part II L20) — capital & paid-in surplus × .001 + $15, min $25. W3.
SC_LICENSE_FEE_RATE = "0.001"
SC_LICENSE_FEE_ADD = 15
SC_LICENSE_FEE_MIN = 25

# SC §179 (conformed IRC §179 at 12/31/2024; Reading A = 2025 INDEXED, Rev. Proc. 2024-40). W1.
# SC did NOT adopt OBBBA ($2.5M/$4M). Pending SCDOR confirmation.
SC_179_LIMIT: dict[int, int] = {2025: 1250000}
SC_179_PHASEOUT: dict[int, int] = {2025: 3130000}

# Apportionment factor precision (SC-K L19 / Schedule H). W5.
SC_APPORT_DECIMALS = 4

# Individual I-335 no-benefit floor — "do not complete I-335 if SC taxable income ≤ $17,830". Diagnostic only.
SC_I335_FLOOR: dict[int, int] = {2025: 17830}

# IRC conformity date (SC1120I "What's New"; Act 63 of 2025). W2.
SC_CONFORMITY_DATE = "2024-12-31"


def _yk(d: dict, year: int):
    return d.get(year) if d.get(year) is not None else d[2025]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY TOPICS / SOURCES
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("sc_passthrough_ptet", "SC pass-through returns (SC1065 / SC1120S) + §12-6-545(G) Active Trade or "
     "Business entity-level tax (SC PTET): SC-K adjustments, dual-method apportionment, 3% ATB tax, owner "
     "exclusion, 5% nonresident withholding, license fee."),
]

# Reused from load_sc1040.py — the SC conformity + §168(k) depreciation decoupling sources.
EXISTING_SOURCES_TO_REFERENCE: list[str] = ["SC_ACT63_2025_CONFORMITY", "SC_RR_05_2_DEPR"]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "SC_2025_I435",
        "source_type": "state_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "SC",
        "title": "2025 SC I-435 — Active Trade or Business Income Reduced Rate Computation (entity-level ATB / PTET)",
        "citation": "SC Form I-435 (2025), Rev. 1/30/25",
        "issuer": "South Carolina Department of Revenue",
        "official_url": "https://dor.sc.gov/sites/dor/files/forms/I435.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["sc_passthrough_ptet"],
        "excerpts": [
            {
                "excerpt_label": "I-435 — flat 3% ATB rate + base + annual election (verbatim)",
                "excerpt_text": (
                    "I-435 is a 17-line, 3-column computation (Col A = federal Schedule K; Col B = Schedule "
                    "SC-K; Col C = SC active trade or business income). Line 14 = total active trade or "
                    "business income; Line 15 = ATB income already taxed by another electing pass-through "
                    "(tiered relief); Line 16 = taxable ATB income; Line 17 = 'Active Trade or Business "
                    "Income Tax (multiply line 16 by 3%).' Instructions p.2: 'a qualified entity can elect "
                    "to have its active trade or business income taxed at a 3% flat tax rate imposed on the "
                    "entity itself.' The base is ACTIVE trade or business income ONLY — it excludes passive "
                    "investment income and related expenses, capital gains/losses, IRC §707(c) service "
                    "payments, and amounts reasonably related to personal services; it is apportioned per "
                    "SC Code §12-6-2240 (Col C ≤ Col B). 'Qualified entities elect each year whether or not "
                    "to have the active trade or business income taxed at the entity level'; the election is "
                    "made by the return due date incl. extensions. I-435 line 14 → SC1065 L2 / SC1120S L5; "
                    "I-435 line 17 → SC1065 L3 / SC1120S L6."
                ),
                "summary_text": "I-435: entity-level ATB income (only) × 3% (L16→L17); annual non-binding election; L14→SC1065 L2/SC1120S L5, L17→L3/L6.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "SC_2025_SC1065",
        "source_type": "state_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "SC",
        "title": "2025 SC1065 — Partnership Return (+ Schedule SC-K, instructions)",
        "citation": "SC Form SC1065 (2025), Rev. 6/18/25",
        "issuer": "South Carolina Department of Revenue",
        "official_url": "https://dor.sc.gov/sites/dor/files/forms/SC1065_2025.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["sc_passthrough_ptet"],
        "excerpts": [
            {
                "excerpt_label": "SC1065 face line map + ATB election checkbox (verbatim)",
                "excerpt_text": (
                    "Page 1: '[ ] Check for Active Trade or Business election' checkbox. L1 Total SC business "
                    "income (← Schedule SC-K line 21); L2 Active Trade or Business Income (← I-435 line 14); "
                    "L3 ATB Income Tax (← I-435 line 17); L4 Nonrefundable credits (← SC1040TC line 18); L5 "
                    "ATB tax due (L3 − L4); L6 SC income taxable to partners (L1 − L2); L7 Income exempt from "
                    "withholding; L8 Income subject to nonresident withholding (L6 − L7); L9 Nonresident "
                    "Withholding Tax (L8 × 5%); L10 Total tax (L5 + L9); L11 tax withheld (I-290/1099); L12 "
                    "SC8736 extension; L13 estimated; L15 total payments; L16-18 refund; L19-21 balance due. "
                    "If electing, 'be sure to also check the box on all of the SC1065 K-1s you provide to "
                    "your partners.' Schedule SC-K (page 2): L16 income allocated to SC; L17 income subject "
                    "to apportionment; L18 SC vs total sales/gross receipts; L19 apportionment factor (FOUR "
                    "decimals); L20 = L17 × L19; L21 = L16 + L20 (SC-taxable net business income → L1)."
                ),
                "summary_text": "SC1065: L1←SC-K L21; L2←I-435 L14; L3←I-435 L17 (3%); L5=L3−L4; L6=L1−L2; L8=L6−L7; L9=L8×5%; L10=L5+L9. SC-K L21 = allocated-SC (L16) + apportioned (L20 = L17×factor, 4 dec).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "SC1065 — 5% nonresident withholding, exemptions, bonus add-back (instr. verbatim)",
                "excerpt_text": (
                    "Instructions p.1: 'Partnerships are required to withhold 5% of the South Carolina "
                    "taxable income of partners who are nonresidents of South Carolina.' No withholding for: "
                    "SC-resident partners; nonresident partners who file an I-309 affidavit; partners on a "
                    "composite return; partners tax-exempt under IRC 501(a); and 'Active trade or business "
                    "income taxed at the partnership level is not subject to nonresident withholding.' Each "
                    "nonresident partner receives a 1099-MISC 'SC Only.' Composite return: I-348 (filing "
                    "instructions) / I-338 (affidavit); composite extension SC4868. Depreciation (p.4): 'For "
                    "the year an asset is placed in service, add back the difference between the depreciation "
                    "taken and the depreciation that would have been allowed without bonus depreciation. A "
                    "subtraction resulting from a higher South Carolina basis applies to all remaining years "
                    "of depreciation.' Apportionment (p.3): sales-only (single sales factor) for taxpayers "
                    "dealing in tangible personal property; gross-receipts ratio for those NOT dealing in "
                    "TPP (financial/service); special (§12-6-2310) and individualized (§12-6-2320) methods."
                ),
                "summary_text": "5% NR withholding on nonresident partners; exempt = residents/I-309/composite/501(a)/entity-taxed ATB. §168(k) year-1 add-back, remaining-life SC subtraction. Apportionment: sales-only (TPP) or gross-receipts (service/financial).",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "SC_2025_SC1120S",
        "source_type": "state_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "SC",
        "title": "2025 SC1120S — S Corporation Income Tax Return (Part I income tax + Part II license fee)",
        "citation": "SC Form SC1120S (2025), Rev. 6/17/25",
        "issuer": "South Carolina Department of Revenue",
        "official_url": "https://dor.sc.gov/forms-site/forms/sc1120s.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["sc_passthrough_ptet"],
        "excerpts": [
            {
                "excerpt_label": "SC1120S Part I income tax + Part II license fee (verbatim)",
                "excerpt_text": (
                    "Page 1: '[ ] Check for Active Trade or Business election'. PART I — L1 'Total of line 1 "
                    "through 12, Schedule K of the federal 1120S'; L2 net adjustment from Schedule A and B "
                    "(SC additions/deductions to federal taxable income); L3 = L1 + L2; L4 = if multistate, "
                    "from Schedule G line 6, else L3; L5 Active Trade or Business Income (← I-435 line 14); "
                    "L6 Active Trade or Business Tax (← I-435 line 17); L7 Income taxed to shareholders; L8 "
                    "SC net taxable income (L4 − L5 − L7); L9 Tax (L8 × 5%); L10 Total income tax (L6 + L9). "
                    "PART II (page 2) — LICENSE FEE: L19 total capital and paid-in surplus; L20 License Fee "
                    "= line 19 × .001, then add $15 (minimum $25). Nonresident shareholder withholding (5%) "
                    "is remitted on a SEPARATE SC1120S-WH. Schedule D Annual Report is required of ALL "
                    "corporations. Multi-state apportionment via Schedules E / H-1 (sales) / H-2 (gross "
                    "receipts) / H-3 (§12-6-2310)."
                ),
                "summary_text": "SC1120S Part I: L3=L1+L2; L4 apportioned; L5/L6←I-435 (3% ATB); L8=L4−L5−L7; L9=L8×5% general rate; L10=L6+L9. Part II license fee L20 = L19×.001 + $15 (min $25). NR shareholder WH on separate SC1120S-WH.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "SC_2025_I335",
        "source_type": "state_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "SC",
        "title": "2025 SC I-335 — Active Trade or Business Income Reduced Rate Computation (OWNER side — the exclusion)",
        "citation": "SC Form I-335 (2025), Rev. 6/17/25",
        "issuer": "South Carolina Department of Revenue",
        "official_url": "https://dor.sc.gov/sites/dor/files/forms/I335_2025.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.2,
        "topics": ["sc_passthrough_ptet"],
        "excerpts": [
            {
                "excerpt_label": "I-335 — owner EXCLUSION of entity-taxed ATB income + the $17,830 floor (verbatim)",
                "excerpt_text": (
                    "I-335 line 6 'Amounts taxed at entity level (from SC K-1s)' is SUBTRACTED (line 7 = "
                    "line 5 − line 6): 'If you're a partner in a Partnership, you can find this amount on line "
                    "14 of your SC1065 K-1. If you're a shareholder of an S Corporation, you can find this "
                    "amount on line 13 of your SC1120S K-1.' Line 8 applies the reduced rate '3% (.03)'. The "
                    "owner is not taxed again on income already taxed at the entity level — the exclusion is "
                    "the mechanism (§12-6-545(G)(3): a qualified owner 'shall exclude active trade or "
                    "business income from an electing qualified entity provided that the qualified entity "
                    "properly filed an income tax return and paid the taxes'). NO owner credit. Gotcha (p.4): "
                    "for TY2025 'Do not complete the I-335 if your South Carolina taxable income is less than "
                    "or equal to $17,830' (the top graduated bracket is already 3% at that income) — except "
                    "partners/shareholders/members who would otherwise pay a flat 6%. Safe harbor (individual "
                    "only): if ATB from personal-service entities ≤ $100,000, may treat 50% as not "
                    "personal-service."
                ),
                "summary_text": "Owner EXCLUDES entity-taxed ATB (I-335 L6 subtracts SC1065 K-1 L14 / SC1120S K-1 L13); no owner credit (§12-6-545(G)(3)). Individual I-335 has no benefit if SC taxable income ≤ $17,830.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "SC_2025_SC1120I",
        "source_type": "state_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "SC",
        "title": "2025 SC1120I — C & S Corporation Instructions ('What's New — Conformity')",
        "citation": "SC1120I (2025)",
        "issuer": "South Carolina Department of Revenue",
        "official_url": "https://dor.sc.gov/sites/dor/files/forms/SC1120I.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.3,
        "topics": ["sc_passthrough_ptet"],
        "excerpts": [
            {
                "excerpt_label": "IRC conformity 12/31/2024 + OBBBA non-adoption + H.3368 pending (verbatim)",
                "excerpt_text": (
                    "'South Carolina recognizes the Internal Revenue Code (IRC) as amended through December "
                    "31, 2024, except as otherwise provided. If IRC sections adopted by South Carolina that "
                    "expired on December 31, 2024 are extended, but otherwise not amended, by congressional "
                    "enactment during 2025, these sections are also extended for South Carolina purposes in "
                    "the same manner that they are extended for federal Income Tax purposes.' Because the SC "
                    "legislature did not enact conformity to OBBBA (P.L. 119-21, signed 7/4/2025) before "
                    "adjourning the 2025 session, OBBBA is NOT adopted for TY2025 (taxpayers add back / "
                    "adjust). SCDOR notes a pending bill H.3368 that WOULD conform to the current IRC "
                    "including OBBBA 'if passed,' with additional guidance to follow. §168(k) bonus "
                    "depreciation is specifically not adopted (add-back). §179 is NOT on the non-adopted "
                    "list — SC conforms to §179 as of 12/31/2024; the booklet states no §179 dollar figure."
                ),
                "summary_text": "SC IRC conformity = 12/31/2024; OBBBA NOT adopted TY2025; H.3368 pending would conform (re-verify). §168(k) not adopted (add-back); §179 conforms (no SCDOR dollar figure stated).",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "SC_CODE_12_6_545",
        "source_type": "state_statute",
        "source_rank": "controlling",
        "jurisdiction_code": "SC",
        "title": "S.C. Code §12-6-545 — Active Trade or Business income reduced rate + (G) entity-level election",
        "citation": "S.C. Code Ann. §12-6-545 (esp. (A)(1), (G)); Act 61 of 2021",
        "issuer": "South Carolina General Assembly",
        "official_url": "https://law.justia.com/codes/south-carolina/title-12/chapter-6/section-12-6-545/",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.0,
        "topics": ["sc_passthrough_ptet"],
        "excerpts": [
            {
                "excerpt_label": "§12-6-545 — ATB definition, 3% rate, entity election (G), owner exclusion",
                "excerpt_text": (
                    "§12-6-545 imposes a reduced flat rate (3%) on 'active trade or business income' — pass-"
                    "through income from a trade or business, EXCLUDING passive investment income, capital "
                    "gains, and amounts reasonably related to personal services (§707(c) payments). "
                    "Subsection (G) (added by Act 61 of 2021) authorizes a QUALIFIED ENTITY to elect ANNUALLY "
                    "to have its active trade or business income taxed at the entity level at the same 3% "
                    "rate; (G)(2) the election is made by the return due date incl. extensions; (G)(3) a "
                    "qualified owner excludes the entity-taxed active trade or business income provided the "
                    "entity filed and paid. Governing SCDOR guidance: SC Revenue Rulings #21-15 and #22-5. "
                    "The individual-side election (non-electing entity) is I-335; the entity election flows "
                    "through I-435 to SC1065 / SC1120S."
                ),
                "summary_text": "§12-6-545: 3% on ATB income (excl. passive/capital-gain/personal-service); (G) entity-level annual election (Act 61/2021); (G)(3) owner excludes entity-taxed ATB. RR #21-15/#22-5.",
                "is_key_excerpt": True,
            },
        ],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("SC_2025_I435", "SC1065", "governs"),
    ("SC_2025_I435", "SC1120S", "governs"),
    ("SC_2025_SC1065", "SC1065", "governs"),
    ("SC_2025_SC1120S", "SC1120S", "governs"),
    ("SC_2025_I335", "SC1065", "informs"),
    ("SC_2025_I335", "SC1120S", "informs"),
    ("SC_2025_SC1120I", "SC1065", "governs"),
    ("SC_2025_SC1120I", "SC1120S", "governs"),
    ("SC_CODE_12_6_545", "SC1065", "governs"),
    ("SC_CODE_12_6_545", "SC1120S", "governs"),
    ("SC_ACT63_2025_CONFORMITY", "SC1065", "governs"),
    ("SC_ACT63_2025_CONFORMITY", "SC1120S", "governs"),
    ("SC_RR_05_2_DEPR", "SC1065", "informs"),
    ("SC_RR_05_2_DEPR", "SC1120S", "informs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 1 — SC1065 (Partnership Return)
# ═══════════════════════════════════════════════════════════════════════════

SC1065_FACTS: list[dict] = [
    {"fact_key": "atb_election", "label": "ATB election — pay tax on active trade/business income at the entity level? (SC1065 page 1)", "data_type": "boolean", "required": False, "sort_order": 1,
     "notes": "Q2/Q3. Annual NON-BINDING. If True, also check the box on every SC1065 K-1. If False, ATB lines blank (pure pass-through)."},
    {"fact_key": "is_composite_return", "label": "Composite return filed (I-348/I-338)?", "data_type": "boolean", "required": False, "sort_order": 2,
     "notes": "Alternative to nonresident withholding for the covered partners. RED-defer the composite compute."},
    # Schedule SC-K — federal Sch K + SC adjustments
    {"fact_key": "sck_federal_income", "label": "Federal Schedule K income (Sch SC-K Col A total)", "data_type": "decimal", "required": False, "sort_order": 10,
     "notes": "Aggregate of the federal 1065 Schedule K distributive items entering the SC business-income base."},
    {"fact_key": "bonus_depr_addback", "label": "§168(k) bonus depreciation add-back — SC-4562 (Sch SC-K addition, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 11,
     "notes": "Q2. Year an asset is placed in service: federal depreciation − depreciation-without-bonus. SC decouples from §168(k)."},
    {"fact_key": "sc_depr_subtraction", "label": "SC depreciation subtraction (higher SC basis, remaining years) — SC-4562 (Sch SC-K subtraction, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 12,
     "notes": "Q2. Later-year subtraction as SC basis exceeds federal (RR #05-2 separate SC depreciation schedule)."},
    {"fact_key": "other_state_muni_interest", "label": "Interest from other states' obligations (Sch SC-K addition)", "data_type": "decimal", "required": False, "sort_order": 13},
    {"fact_key": "us_obligation_interest", "label": "U.S. government obligation interest (Sch SC-K subtraction)", "data_type": "decimal", "required": False, "sort_order": 14},
    {"fact_key": "other_sc_additions", "label": "Other SC additions (Sch SC-K Col B, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 15},
    {"fact_key": "other_sc_subtractions", "label": "Other SC subtractions (Sch SC-K Col B, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 16},
    # Allocation / apportionment
    {"fact_key": "income_allocated_sc", "label": "Nonbusiness income directly allocated to SC (Sch SC-K L16)", "data_type": "decimal", "required": False, "sort_order": 20},
    {"fact_key": "income_allocated_other", "label": "Nonbusiness income allocated to other states (Sch SC-K)", "data_type": "decimal", "required": False, "sort_order": 21},
    {"fact_key": "apportionment_method", "label": "Apportionment method: sales_only (TPP) / gross_receipts (service/financial) / special / individualized", "data_type": "text", "required": False, "sort_order": 22,
     "notes": "Q4/W5. §12-6-2240 et seq. special (§12-6-2310) + individualized (§12-6-2320) RED-deferred."},
    {"fact_key": "sc_sales", "label": "SC sales — tangible personal property, destination (Sch SC-K L18 numerator, sales-only)", "data_type": "decimal", "required": False, "sort_order": 23},
    {"fact_key": "total_sales", "label": "Total sales everywhere (Sch SC-K L18 denominator, sales-only)", "data_type": "decimal", "required": False, "sort_order": 24},
    {"fact_key": "sc_gross_receipts", "label": "SC gross receipts (Sch SC-K L18 numerator, gross-receipts method)", "data_type": "decimal", "required": False, "sort_order": 25},
    {"fact_key": "total_gross_receipts", "label": "Total gross receipts everywhere (Sch SC-K L18 denominator, gross-receipts method)", "data_type": "decimal", "required": False, "sort_order": 26},
    # §179 (compute the SC-limit delta)
    {"fact_key": "federal_sec179_deduction", "label": "Federal IRC §179 expense (separately stated)", "data_type": "decimal", "required": False, "sort_order": 30,
     "notes": "Q2/W1. SC delta = federal − min(federal, SC $1,250,000 phased over $3,130,000)."},
    {"fact_key": "sec179_property_cost", "label": "Total §179 property placed in service (for the $3,130,000 SC phaseout)", "data_type": "decimal", "required": False, "sort_order": 31},
    # ATB (I-435)
    {"fact_key": "atb_income", "label": "Active trade or business income — I-435 line 14 (Col C, direct-entry, W4)", "data_type": "decimal", "required": False, "sort_order": 40,
     "notes": "Q2/W4. Active only (excl. passive/investment, capital gains, §707(c)); SC-apportioned. The active/passive split is preparer judgment."},
    {"fact_key": "atb_already_taxed", "label": "ATB income already taxed by another electing PTE (I-435 line 15, tiered relief)", "data_type": "decimal", "required": False, "sort_order": 41},
    {"fact_key": "nonrefundable_credits", "label": "Nonrefundable credits — SC1040TC line 18 (SC1065 L4, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 42},
    # Withholding
    {"fact_key": "income_exempt_from_withholding", "label": "SC income exempt from nonresident withholding (SC1065 L7: residents/I-309/composite/501(a))", "data_type": "decimal", "required": False, "sort_order": 50,
     "notes": "Q4. Entity-taxed ATB is already removed at L6 = L1 − L2; L7 captures resident/I-309/composite/501(a) shares."},
    # Payments
    {"fact_key": "tax_withheld_in", "label": "SC tax withheld on the partnership — I-290 / 1099 (SC1065 L11)", "data_type": "decimal", "required": False, "sort_order": 51},
    {"fact_key": "extension_payment", "label": "SC8736 extension payment (SC1065 L12)", "data_type": "decimal", "required": False, "sort_order": 52},
    {"fact_key": "estimated_payments", "label": "Estimated tax payments (SC1065 L13)", "data_type": "decimal", "required": False, "sort_order": 53},
]

SC1065_RULES: list[dict] = [
    {"rule_id": "R-SC1065-SCK", "title": "Schedule SC-K — SC-taxable net business income (L21 → L1)", "rule_type": "calculation",
     "formula": ("sck_col_c = sck_federal_income + bonus_depr_addback + other_state_muni_interest + other_sc_additions "
                 "- sc_depr_subtraction - us_obligation_interest - other_sc_subtractions ; "
                 "L17_apportionable = sck_col_c - income_allocated_sc - income_allocated_other ; "
                 "L20 = round(L17_apportionable * apport_factor) ; L21 = income_allocated_sc + L20  (→ SC1065 L1)"),
     "inputs": ["sck_federal_income", "bonus_depr_addback", "other_state_muni_interest", "other_sc_additions",
                "sc_depr_subtraction", "us_obligation_interest", "other_sc_subtractions", "income_allocated_sc", "income_allocated_other"],
     "outputs": ["sck_col_c", "SCK_L17", "SCK_L20", "SCK_L21", "SC1065_L1"], "sort_order": 10,
     "description": "Q2. Federal Sch K → SC adjustments (Col B) → Col C; apportionable = Col C − directly-allocated income; SC-taxable = allocated-to-SC + apportioned share."},
    {"rule_id": "R-SC1065-APPORT", "title": "Apportionment factor (dual method, 4 decimals)", "rule_type": "calculation",
     "formula": ("if apportionment_method == 'sales_only':   apport_factor = round(sc_sales / total_sales, 4) ; "
                 "elif apportionment_method == 'gross_receipts': apport_factor = round(sc_gross_receipts / total_gross_receipts, 4) ; "
                 "else: RED-defer (special §12-6-2310 / individualized §12-6-2320) — D_SC1065_SPECIAL"),
     "inputs": ["apportionment_method", "sc_sales", "total_sales", "sc_gross_receipts", "total_gross_receipts"],
     "outputs": ["apport_factor"], "sort_order": 11,
     "description": "Q4/W5. §12-6-2240 et seq. Sales-only (single sales factor) for TPP dealers; gross-receipts ratio for service/financial. Factor to FOUR decimals (SC-K L19)."},
    {"rule_id": "R-SC1065-179", "title": "SC §179 conformity delta (separately stated to partners)", "rule_type": "calculation",
     "formula": ("sc_limit = max(0, 1250000 - max(0, sec179_property_cost - 3130000)) ; "
                 "sc_sec179 = min(federal_sec179_deduction, sc_limit) ; "
                 "sec179_delta = federal_sec179_deduction - sc_sec179  (separately stated on the SC1065 K-1; recovered via SC depreciation)"),
     "inputs": ["federal_sec179_deduction", "sec179_property_cost"], "outputs": ["sc_sec179", "sec179_delta"], "sort_order": 12,
     "description": "Q2/Q3/W1. SC §179 = INDEXED $1,250,000 / $3,130,000 (conformed IRC §179 at 12/31/2024; Reading A; pending SCDOR confirmation). SC did NOT adopt OBBBA. §179 is separately stated for partnerships."},
    {"rule_id": "R-SC1065-ATB", "title": "ATB entity tax — I-435 3% (SC1065 L2/L3), gated on the election", "rule_type": "calculation",
     "formula": ("if atb_election: L2 = atb_income  (I-435 L14) ; I435_L16 = max(0, atb_income - atb_already_taxed) ; "
                 "L3 = round(I435_L16 * 0.03)  (I-435 L17) ; else: L2 = L3 = 0 (ATB lines blank; pure pass-through)"),
     "inputs": ["atb_election", "atb_income", "atb_already_taxed"], "outputs": ["SC1065_L2", "SC1065_L3"], "sort_order": 13,
     "description": "Q2/W3. THE HEADLINE. Entity-level ATB income (only) × 3% via I-435. Annual non-binding election. Excludes passive/investment income, capital gains, §707(c)."},
    {"rule_id": "R-SC1065-DUE", "title": "ATB tax due (SC1065 L5)", "rule_type": "calculation",
     "formula": "L5 = max(0, SC1065_L3 - nonrefundable_credits)  (L5 = L3 − L4)",
     "inputs": ["nonrefundable_credits"], "outputs": ["SC1065_L5"], "sort_order": 14,
     "description": "L4 nonrefundable credits (SC1040TC line 18) reduce the entity ATB tax."},
    {"rule_id": "R-SC1065-WH", "title": "Nonresident withholding 5% (SC1065 L6/L8/L9); ATB displaces it", "rule_type": "calculation",
     "formula": ("L6 = SC1065_L1 - SC1065_L2  (SC income taxable to partners; entity-taxed ATB removed) ; "
                 "L8 = max(0, L6 - income_exempt_from_withholding)  (subject to NR withholding) ; "
                 "L9 = round(L8 * 0.05)  (Form 1099-MISC 'SC Only' per nonresident partner)"),
     "inputs": ["income_exempt_from_withholding"], "outputs": ["SC1065_L6", "SC1065_L8", "SC1065_L9"], "sort_order": 15,
     "description": "Q4. 5% on nonresident partners' SC taxable income. Exempt: residents/I-309/composite/501(a) (L7) + entity-taxed ATB (removed at L6). ATB election OR composite displaces per-partner withholding."},
    {"rule_id": "R-SC1065-TOTAL", "title": "Total tax (SC1065 L10)", "rule_type": "calculation",
     "formula": "L10 = SC1065_L5 + SC1065_L9",
     "inputs": [], "outputs": ["SC1065_L10"], "sort_order": 16,
     "description": "Total tax = entity ATB tax due (L5) + nonresident withholding (L9)."},
    {"rule_id": "R-SC1065-OWNER", "title": "Owner exclusion — SC1065 K-1 line 14 → I-335 line 6 (no owner credit)", "rule_type": "routing",
     "formula": ("if atb_election: each partner's share of entity-taxed ATB income -> SC1065 K-1 line 14 -> the "
                 "owner SUBTRACTS it on I-335 line 6 (excluded from the owner's SC taxable income). NO owner credit "
                 "for the entity-level 3% tax (§12-6-545(G)(3))."),
     "inputs": ["atb_election"], "outputs": [], "sort_order": 17,
     "description": "Q2. The owner side of the SALT-cap workaround — an EXCLUSION, not a credit. Analogous to GA-700's PTEDED, but via I-335 line 6."},
]

SC1065_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-SC1065-SCK", "SC_2025_SC1065", "primary", "Schedule SC-K L16-L21 net-business-income build"),
    ("R-SC1065-SCK", "SC_RR_05_2_DEPR", "secondary", "§168(k) basis decoupling feeding the SC-K add-back"),
    ("R-SC1065-APPORT", "SC_2025_SC1065", "primary", "sales-only / gross-receipts apportionment, 4 decimals"),
    ("R-SC1065-179", "SC_ACT63_2025_CONFORMITY", "primary", "SC conforms to §179 at 12/31/2024 (pre-OBBBA)"),
    ("R-SC1065-ATB", "SC_2025_I435", "primary", "I-435 L14/L16/L17 — ATB income × 3%"),
    ("R-SC1065-ATB", "SC_CODE_12_6_545", "secondary", "§12-6-545(G) entity-level 3% election"),
    ("R-SC1065-DUE", "SC_2025_SC1065", "primary", "SC1065 L5 = L3 − L4"),
    ("R-SC1065-WH", "SC_2025_SC1065", "primary", "5% nonresident withholding, exemptions, L6=L1−L2 displacement"),
    ("R-SC1065-TOTAL", "SC_2025_SC1065", "primary", "SC1065 L10 = L5 + L9"),
    ("R-SC1065-OWNER", "SC_2025_I335", "primary", "owner excludes entity-taxed ATB on I-335 L6 (K-1 L14); no credit"),
    ("R-SC1065-OWNER", "SC_CODE_12_6_545", "secondary", "§12-6-545(G)(3) owner exclusion"),
]

SC1065_LINES: list[dict] = [
    {"line_number": "SCK-16", "description": "Sch SC-K L16 Income allocated to SC", "line_type": "input", "source_facts": ["income_allocated_sc"], "sort_order": 1},
    {"line_number": "SCK-17", "description": "Sch SC-K L17 Income subject to apportionment", "line_type": "calculated", "source_rules": ["R-SC1065-SCK"], "sort_order": 2},
    {"line_number": "SCK-19", "description": "Sch SC-K L19 Apportionment factor (4 decimals)", "line_type": "calculated", "source_rules": ["R-SC1065-APPORT"], "sort_order": 3},
    {"line_number": "SCK-20", "description": "Sch SC-K L20 Income apportioned to SC (L17 × L19)", "line_type": "calculated", "source_rules": ["R-SC1065-SCK"], "sort_order": 4},
    {"line_number": "SCK-21", "description": "Sch SC-K L21 SC-taxable net business income (→ page-1 L1)", "line_type": "subtotal", "source_rules": ["R-SC1065-SCK"], "sort_order": 5},
    {"line_number": "1", "description": "L1 Total SC business income (from Sch SC-K L21)", "line_type": "subtotal", "source_rules": ["R-SC1065-SCK"], "sort_order": 6},
    {"line_number": "2", "description": "L2 Active Trade or Business Income (from I-435 L14)", "line_type": "calculated", "source_rules": ["R-SC1065-ATB"], "sort_order": 7},
    {"line_number": "3", "description": "L3 ATB Income Tax (I-435 L17, 3%)", "line_type": "calculated", "calculation": "R-SC1065-ATB", "source_rules": ["R-SC1065-ATB"], "sort_order": 8},
    {"line_number": "4", "description": "L4 Nonrefundable credits (SC1040TC line 18)", "line_type": "input", "source_facts": ["nonrefundable_credits"], "sort_order": 9},
    {"line_number": "5", "description": "L5 ATB tax due (L3 − L4)", "line_type": "subtotal", "source_rules": ["R-SC1065-DUE"], "sort_order": 10},
    {"line_number": "6", "description": "L6 SC income taxable to partners (L1 − L2)", "line_type": "calculated", "source_rules": ["R-SC1065-WH"], "sort_order": 11},
    {"line_number": "7", "description": "L7 Income exempt from withholding (residents/I-309/composite/501(a))", "line_type": "input", "source_facts": ["income_exempt_from_withholding"], "sort_order": 12},
    {"line_number": "8", "description": "L8 Income subject to nonresident withholding (L6 − L7)", "line_type": "calculated", "source_rules": ["R-SC1065-WH"], "sort_order": 13},
    {"line_number": "9", "description": "L9 Nonresident Withholding Tax (L8 × 5%)", "line_type": "calculated", "calculation": "R-SC1065-WH", "source_rules": ["R-SC1065-WH"], "sort_order": 14},
    {"line_number": "10", "description": "L10 Total tax (L5 + L9)", "line_type": "subtotal", "source_rules": ["R-SC1065-TOTAL"], "sort_order": 15},
    {"line_number": "11", "description": "L11 SC tax withheld on the partnership (I-290/1099)", "line_type": "input", "source_facts": ["tax_withheld_in"], "sort_order": 16},
]

SC1065_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_SC1065_ATB", "title": "ATB is an entity-level 3% election — owners EXCLUDE via I-335 line 6", "severity": "info",
     "condition": "atb_election is True (or the preparer is weighing the election)", "message": "The Active Trade or Business election (§12-6-545(G)) is an ANNUAL, NON-BINDING election to pay SC tax on ACTIVE trade or business income at the entity level (3%, via I-435). If electing, ALSO check the box on every SC1065 K-1. Electing partners EXCLUDE that income — subtract it on I-335 line 6 (from SC1065 K-1 line 14); there is NO owner credit for the entity-level tax. Entity-taxed ATB is also exempt from the 5% nonresident withholding (L6 = L1 − L2). If NOT electing, leave the ATB lines blank (pure pass-through).",
     "notes": "Q2. The headline SALT-cap-workaround feature."},
    {"diagnostic_id": "D_SC1065_DEPR", "title": "SC decouples from §168(k) bonus — add back / recompute depreciation", "severity": "info",
     "condition": "bonus depreciation or §179 present", "message": "SC did NOT adopt IRC §168(k) bonus depreciation. In the placed-in-service year, add back (Sch SC-K) the difference between federal depreciation and depreciation without bonus; maintain a separate SC depreciation schedule (RR #05-2) and take the offsetting subtraction over the asset's remaining life as SC basis exceeds federal. Adjust disposition gain/loss for the SC-vs-federal basis difference.",
     "notes": "Q2/W2. Ken's specialty. Conformity 12/31/2024."},
    {"diagnostic_id": "D_SC1065_179", "title": "SC §179 = $1,250,000 / $3,130,000 (pre-OBBBA; SCDOR states no figure)", "severity": "warning",
     "condition": "§179 deduction present", "message": "SC conforms to IRC §179 as of 12/31/2024 (pre-OBBBA), NOT the OBBBA $2,500,000 / $4,000,000. v1 pins the INDEXED 2025 figures $1,250,000 / $3,130,000 (Rev. Proc. 2024-40) per Ken's Reading A — but SCDOR states no §179 dollar figure, so treat this as pending SCDOR confirmation. The §179 excess over the SC limit is separately stated to partners and recovered via SC depreciation.",
     "notes": "Q3/W1."},
    {"diagnostic_id": "D_SC1065_179LIMIT", "title": "§179 property over the $3,130,000 SC phaseout", "severity": "warning",
     "condition": "sec179_property_cost > 3130000", "message": "SC's $1,250,000 §179 limit phases down dollar-for-dollar once §179 property placed in service exceeds $3,130,000. Verify the phased SC §179 against the asset-level SC-4562 before locking the §179 difference.",
     "notes": "W1."},
    {"diagnostic_id": "D_SC1065_CONFORM", "title": "SC IRC conformity = 12/31/2024 — H.3368 could conform to OBBBA mid-season", "severity": "warning",
     "condition": "depreciation / §179 / conformity-sensitive item present", "message": "SC's IRC conformity date is December 31, 2024 (did NOT adopt OBBBA for TY2025). A pending bill (H.3368) WOULD conform SC to the current IRC including OBBBA — if enacted mid-season, the §179 figures ($1.25M/$3.13M → $2.5M/$4M) and bonus-depreciation treatment change. Re-verify the conformity status before relying on the depreciation/§179 logic.",
     "notes": "W2. The biggest open verify item."},
    {"diagnostic_id": "D_SC1065_APPORT", "title": "Apportionment method is by business type (TPP vs service/financial)", "severity": "info",
     "condition": "apportionment computed", "message": "SC is NOT universally single-sales-factor. Taxpayers dealing in tangible personal property (manufacture/sell/rent TPP) use the SALES-ONLY (single sales factor) method; financial and service businesses (installers/repairers, contractors) use the GROSS-RECEIPTS ratio (§§12-6-2290/2295). The factor is carried to FOUR decimal places. Choose the method by the entity's business type.",
     "notes": "Q4/W5."},
    {"diagnostic_id": "D_SC1065_SPECIAL", "title": "Special / individualized apportionment — prepare manually", "severity": "info",
     "condition": "apportionment_method in ('special','individualized')", "message": "Special-industry apportionment (§12-6-2310 — railroads, telephone, pipeline, airlines, shipping) and individualized apportionment (§12-6-2320, on application) are not computed in v1 — determine the factor manually and enter it.",
     "notes": "Q4 RED-defer."},
    {"diagnostic_id": "D_SC1065_NRW", "title": "5% nonresident partner withholding (unless resident/I-309/composite/501(a)/ATB)", "severity": "info",
     "condition": "nonresident partner present", "message": "SC requires 5% withholding on each nonresident partner's SC taxable income (reported on the SC1065 face, 1099-MISC 'SC Only' per partner). No withholding for SC-resident partners, nonresident partners who file an I-309 affidavit, partners on a composite return, IRC 501(a)-exempt partners, or active trade or business income taxed at the entity level (removed at L6 = L1 − L2).",
     "notes": "Q4. Instr. p.1."},
    {"diagnostic_id": "D_SC1065_COMPOSITE", "title": "Composite return (I-348/I-338) — prepare manually", "severity": "info",
     "condition": "composite return elected in lieu of withholding", "message": "The nonresident composite return (I-348 filing instructions / I-338 affidavit; composite extension SC4868) alternative to per-partner withholding is not computed in v1 — prepare it manually. (Covered partners are then exempt from the 5% withholding at L7.)",
     "notes": "Q4 RED-defer."},
    {"diagnostic_id": "D_SC1065_I335", "title": "Individual I-335 has no benefit at SC taxable income ≤ $17,830", "severity": "info",
     "condition": "non-electing entity; partner weighing the individual I-335 3% election", "message": "If the entity does NOT elect, a partner may still elect the individual 3% flat rate on their ATB share via I-335 — but for TY2025 there is no benefit if the partner's SC taxable income is ≤ $17,830 (the top graduated bracket is already 3% there), except for partners who would otherwise pay a flat 6%. Do not complete I-335 below that floor.",
     "notes": "W4. Owner-side note."},
]

SC1065_SCENARIOS: list[dict] = [
    {"scenario_name": "SC1065-T1 — non-electing partnership (pass-through, ATB lines blank)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"atb_election": False, "sck_federal_income": 300000, "apportionment_method": "gross_receipts",
                "sc_gross_receipts": 1000000, "total_gross_receipts": 1000000, "income_exempt_from_withholding": 0},
     "expected_outputs": {"SC1065_L1": 300000, "SC1065_L3": 0, "SC1065_L6": 300000, "SC1065_L9": 15000},
     "notes": "No ATB election → L2/L3 = 0; L1 = 300,000 (100% SC); L6 = L1 − L2 = 300,000; nonresident share fully subject → L9 = 300,000 × 5% = 15,000."},
    {"scenario_name": "SC1065-T2 — ATB elected, 3% entity tax", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"atb_election": True, "sck_federal_income": 300000, "atb_income": 300000, "atb_already_taxed": 0,
                "apportionment_method": "gross_receipts", "sc_gross_receipts": 1000000, "total_gross_receipts": 1000000,
                "nonrefundable_credits": 0, "income_exempt_from_withholding": 0},
     "expected_outputs": {"SC1065_L2": 300000, "SC1065_L3": 9000, "SC1065_L5": 9000, "SC1065_L6": 0, "SC1065_L9": 0},
     "notes": "ATB elected: L2 = 300,000; L3 = round(300,000 × 0.03) = 9,000; L5 = 9,000; L6 = L1 − L2 = 0 → no withholding base (entity tax covers it)."},
    {"scenario_name": "SC1065-T3 — §168(k) bonus depreciation add-back", "scenario_type": "edge", "sort_order": 3,
     "inputs": {"atb_election": True, "sck_federal_income": 200000, "bonus_depr_addback": 85000, "sc_depr_subtraction": 20000,
                "atb_income": 265000, "apportionment_method": "gross_receipts", "sc_gross_receipts": 1000000, "total_gross_receipts": 1000000},
     "expected_outputs": {"sck_col_c": 265000, "SC1065_L1": 265000},
     "notes": "SC-K Col C = 200,000 + 85,000 add-back − 20,000 SC subtraction = 265,000 (100% SC → L1 = 265,000). Net SC add = 65,000."},
    {"scenario_name": "SC1065-T4 — §179 SC-limit difference ($1.25M cap)", "scenario_type": "edge", "sort_order": 4,
     "inputs": {"federal_sec179_deduction": 1400000, "sec179_property_cost": 2500000},
     "expected_outputs": {"sc_sec179": 1250000, "sec179_delta": 150000},
     "notes": "Cost 2,500,000 < 3,130,000 phaseout → SC limit 1,250,000; SC §179 = min(1,400,000, 1,250,000) = 1,250,000; delta = 150,000 (separately stated to partners; SC did NOT adopt OBBBA)."},
    {"scenario_name": "SC1065-T5 — sales-only apportionment (TPP dealer, 4 decimals)", "scenario_type": "edge", "sort_order": 5,
     "inputs": {"atb_election": False, "sck_federal_income": 500000, "apportionment_method": "sales_only",
                "sc_sales": 375000, "total_sales": 1000000, "income_allocated_sc": 0, "income_allocated_other": 0},
     "expected_outputs": {"apport_factor": 0.375, "SCK_L20": 187500, "SC1065_L1": 187500},
     "notes": "TPP dealer → sales-only. Factor = 375,000 / 1,000,000 = 0.3750; apportioned = 500,000 × 0.375 = 187,500 → L1."},
    {"scenario_name": "SC1065-T6 — gross-receipts apportionment (service business)", "scenario_type": "edge", "sort_order": 6,
     "inputs": {"atb_election": False, "sck_federal_income": 400000, "apportionment_method": "gross_receipts",
                "sc_gross_receipts": 250000, "total_gross_receipts": 1000000, "income_allocated_sc": 0, "income_allocated_other": 0},
     "expected_outputs": {"apport_factor": 0.25, "SCK_L20": 100000, "SC1065_L1": 100000},
     "notes": "Service business → gross-receipts. Factor = 250,000 / 1,000,000 = 0.2500; apportioned = 400,000 × 0.25 = 100,000 → L1."},
    {"scenario_name": "SC1065-T7 — 5% nonresident withholding + exemptions + ATB displacement", "scenario_type": "edge", "sort_order": 7,
     "inputs": {"atb_election": False, "is_composite_return": False, "sck_federal_income": 500000,
                "apportionment_method": "gross_receipts", "sc_gross_receipts": 1000000, "total_gross_receipts": 1000000,
                "income_exempt_from_withholding": 200000},
     "expected_outputs": {"SC1065_L6": 500000, "SC1065_L8": 300000, "SC1065_L9": 15000},
     "notes": "L6 = 500,000; L7 exempt 200,000 (resident/I-309 partners) → L8 = 300,000; L9 = 300,000 × 5% = 15,000. If ATB were elected, entity-taxed ATB drops out at L6 first."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 2 — SC1120S (S Corporation Income Tax Return)
# ═══════════════════════════════════════════════════════════════════════════

SC1120S_FACTS: list[dict] = [
    {"fact_key": "atb_election", "label": "ATB election — pay tax on active trade/business income at the entity level? (SC1120S page 1)", "data_type": "boolean", "required": False, "sort_order": 1,
     "notes": "Q2. Annual NON-BINDING. Shareholders exclude via I-335 line 6 (from SC1120S K-1 line 13)."},
    {"fact_key": "is_multistate", "label": "Multi-state S corporation (apportion via Schedule G)?", "data_type": "boolean", "required": False, "sort_order": 2},
    # Part I income
    {"fact_key": "fed_1120s_sch_k", "label": "Total federal 1120S Schedule K lines 1-12 (SC1120S L1)", "data_type": "decimal", "required": False, "sort_order": 10},
    {"fact_key": "sc_adjustment", "label": "Net SC adjustment — Schedule A & B additions/deductions (SC1120S L2, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 11,
     "notes": "Q2. Includes the §168(k) bonus add-back; SC additions to / deductions from federal taxable income."},
    {"fact_key": "bonus_depr_addback", "label": "§168(k) bonus depreciation add-back — SC-4562 (Schedule A&B addition, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 12,
     "notes": "Q2. Component of the L2 Schedule A&B net adjustment (surfaced for the depreciation diagnostic)."},
    {"fact_key": "sch_g_income", "label": "SC apportioned/allocated income — Schedule G line 6 (SC1120S L4, if multistate)", "data_type": "decimal", "required": False, "sort_order": 13,
     "notes": "Multi-state: L4 = Schedule G line 6. Single-state: L4 = L3."},
    # ATB (I-435)
    {"fact_key": "atb_income", "label": "Active trade or business income — I-435 line 14 (SC1120S L5, Col C direct-entry, W4)", "data_type": "decimal", "required": False, "sort_order": 20},
    {"fact_key": "atb_already_taxed", "label": "ATB income already taxed by another electing PTE (I-435 line 15)", "data_type": "decimal", "required": False, "sort_order": 21},
    {"fact_key": "income_taxed_to_shareholders", "label": "Income taxed to shareholders (SC1120S L7)", "data_type": "decimal", "required": False, "sort_order": 22,
     "notes": "The pass-through portion taxed at the shareholder level (removed from the entity 5% base)."},
    {"fact_key": "nonrefundable_credits", "label": "Nonrefundable credits — SC1040TC (direct-entry)", "data_type": "decimal", "required": False, "sort_order": 23},
    # §179
    {"fact_key": "federal_sec179_deduction", "label": "Federal IRC §179 expense (separately stated)", "data_type": "decimal", "required": False, "sort_order": 30},
    {"fact_key": "sec179_property_cost", "label": "Total §179 property placed in service (for the $3,130,000 SC phaseout)", "data_type": "decimal", "required": False, "sort_order": 31},
    # Part II license fee
    {"fact_key": "capital_paid_in_surplus", "label": "Total capital and paid-in surplus (SC1120S Part II L19)", "data_type": "decimal", "required": False, "sort_order": 40,
     "notes": "License fee base. Multi-state: apportioned via Schedule E (RED-defer the multi-state fee apportionment)."},
    # Nonresident shareholder withholding (SC1120S-WH)
    {"fact_key": "nonresident_sh_income", "label": "Nonresident shareholders' SC taxable income (→ SC1120S-WH, 5%)", "data_type": "decimal", "required": False, "sort_order": 50,
     "notes": "Withholding remitted on the SEPARATE SC1120S-WH. Exempt: I-309 / composite / 501(a) / entity-taxed ATB."},
]

SC1120S_RULES: list[dict] = [
    {"rule_id": "R-SC1120S-INC", "title": "SC net income before apportionment (Part I L3)", "rule_type": "calculation",
     "formula": "L3 = fed_1120s_sch_k + sc_adjustment  (L1 + L2, Schedule A&B net)",
     "inputs": ["fed_1120s_sch_k", "sc_adjustment"], "outputs": ["SC1120S_L3"], "sort_order": 10,
     "description": "Q2. L1 = federal 1120S Schedule K lines 1-12; L2 = Schedule A&B SC adjustments (incl. the §168(k) add-back)."},
    {"rule_id": "R-SC1120S-APPT", "title": "SC apportioned income (Part I L4)", "rule_type": "calculation",
     "formula": "if is_multistate: L4 = sch_g_income  (Schedule G line 6; Sch H-1 sales / H-2 gross receipts) ; else: L4 = SC1120S_L3",
     "inputs": ["is_multistate", "sch_g_income"], "outputs": ["SC1120S_L4"], "sort_order": 11,
     "description": "Q4/W5. Multi-state apportionment via Schedule G (same sales-only / gross-receipts methods as SC1065, Schedules H-1/H-2). Single-state → L4 = L3."},
    {"rule_id": "R-SC1120S-ATB", "title": "ATB entity tax — I-435 3% (SC1120S L5/L6), gated on the election", "rule_type": "calculation",
     "formula": ("if atb_election: L5 = atb_income (I-435 L14) ; I435_L16 = max(0, atb_income - atb_already_taxed) ; "
                 "L6 = round(I435_L16 * 0.03) (I-435 L17) ; else: L5 = L6 = 0"),
     "inputs": ["atb_election", "atb_income", "atb_already_taxed"], "outputs": ["SC1120S_L5", "SC1120S_L6"], "sort_order": 12,
     "description": "Q2/W3. Same I-435 3% ATB engine as SC1065. Shareholders exclude via I-335 line 6 (SC1120S K-1 line 13)."},
    {"rule_id": "R-SC1120S-NET", "title": "SC net taxable income (Part I L8)", "rule_type": "calculation",
     "formula": "L8 = max(0, SC1120S_L4 - SC1120S_L5 - income_taxed_to_shareholders)  (L4 − L5 − L7)",
     "inputs": ["income_taxed_to_shareholders"], "outputs": ["SC1120S_L8"], "sort_order": 13,
     "description": "Non-ATB, non-shareholder SC income remaining at the entity (e.g. built-in gains / passive investment income taxed to the S-corp)."},
    {"rule_id": "R-SC1120S-TAX", "title": "SC income tax 5% + total (Part I L9/L10)", "rule_type": "calculation",
     "formula": "L9 = round(SC1120S_L8 * 0.05)  (general SC corporate/S-corp rate) ; L10 = SC1120S_L6 + L9",
     "inputs": [], "outputs": ["SC1120S_L9", "SC1120S_L10"], "sort_order": 14,
     "description": "Q4/W3. L9 = general 5% SC income tax on the remaining SC net taxable income; total income tax L10 = ATB tax (L6, 3%) + L9 (5%)."},
    {"rule_id": "R-SC1120S-LIC", "title": "License fee (Part II L20) — capital × .001 + $15, min $25", "rule_type": "calculation",
     "formula": "L20 = max(25, round(capital_paid_in_surplus * 0.001) + 15)",
     "inputs": ["capital_paid_in_surplus"], "outputs": ["SC1120S_L20"], "sort_order": 15,
     "description": "Q1/W3. SC1120S Part II. Required of all corporations; $25 minimum. Multi-state fee apportionment (Schedule E) is RED-deferred."},
    {"rule_id": "R-SC1120S-179", "title": "SC §179 conformity delta (separately stated to shareholders)", "rule_type": "calculation",
     "formula": ("sc_limit = max(0, 1250000 - max(0, sec179_property_cost - 3130000)) ; "
                 "sc_sec179 = min(federal_sec179_deduction, sc_limit) ; sec179_delta = federal_sec179_deduction - sc_sec179"),
     "inputs": ["federal_sec179_deduction", "sec179_property_cost"], "outputs": ["sc_sec179", "sec179_delta"], "sort_order": 16,
     "description": "Q2/Q3/W1. Same SC §179 = $1,250,000 / $3,130,000 (Reading A; conformed IRC §179 at 12/31/2024; pending SCDOR confirmation)."},
    {"rule_id": "R-SC1120S-WH", "title": "Nonresident shareholder withholding 5% (SC1120S-WH)", "rule_type": "calculation",
     "formula": ("if not atb_election-covered: SC1120S_WH = round(nonresident_sh_income * 0.05)  (remitted on the SEPARATE "
                 "SC1120S-WH form) ; exempt: I-309 / composite / 501(a) / entity-taxed ATB"),
     "inputs": ["nonresident_sh_income"], "outputs": ["SC1120S_WH"], "sort_order": 17,
     "description": "Q4. 5% on nonresident shareholders' SC taxable income — UNLIKE the partnership (on-face L9), the S-corp remits on a SEPARATE SC1120S-WH form."},
    {"rule_id": "R-SC1120S-OWN", "title": "Owner exclusion — SC1120S K-1 line 13 → I-335 line 6 (no owner credit)", "rule_type": "routing",
     "formula": ("if atb_election: each shareholder's share of entity-taxed ATB income -> SC1120S K-1 line 13 -> the "
                 "shareholder SUBTRACTS it on I-335 line 6. NO owner credit (§12-6-545(G)(3))."),
     "inputs": ["atb_election"], "outputs": [], "sort_order": 18,
     "description": "Q2. S-corp analog of SC1065 R-SC1065-OWNER, but the K-1 pointer is line 13 (not 14)."},
]

SC1120S_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-SC1120S-INC", "SC_2025_SC1120S", "primary", "Part I L1 federal 1120S Sch K + L2 Schedule A&B adjustments"),
    ("R-SC1120S-INC", "SC_RR_05_2_DEPR", "secondary", "§168(k) basis decoupling feeding Schedule A&B"),
    ("R-SC1120S-APPT", "SC_2025_SC1120S", "primary", "Part I L4 Schedule G apportionment (Sch H-1/H-2)"),
    ("R-SC1120S-ATB", "SC_2025_I435", "primary", "I-435 L14/L17 — ATB income × 3% (L5/L6)"),
    ("R-SC1120S-ATB", "SC_CODE_12_6_545", "secondary", "§12-6-545(G) entity-level election"),
    ("R-SC1120S-NET", "SC_2025_SC1120S", "primary", "Part I L8 = L4 − L5 − L7"),
    ("R-SC1120S-TAX", "SC_2025_SC1120S", "primary", "L9 = L8 × 5%; L10 = L6 + L9"),
    ("R-SC1120S-LIC", "SC_2025_SC1120S", "primary", "Part II L20 license fee = L19 × .001 + $15 (min $25)"),
    ("R-SC1120S-179", "SC_ACT63_2025_CONFORMITY", "primary", "SC conforms to §179 at 12/31/2024 (pre-OBBBA)"),
    ("R-SC1120S-WH", "SC_2025_SC1120S", "primary", "nonresident shareholder 5% withholding on SC1120S-WH"),
    ("R-SC1120S-OWN", "SC_2025_I335", "primary", "shareholder excludes entity-taxed ATB on I-335 L6 (K-1 L13)"),
]

SC1120S_LINES: list[dict] = [
    {"line_number": "1", "description": "Part I L1 Total federal 1120S Schedule K lines 1-12", "line_type": "input", "source_facts": ["fed_1120s_sch_k"], "sort_order": 1},
    {"line_number": "2", "description": "Part I L2 Schedule A&B net SC adjustment", "line_type": "input", "source_facts": ["sc_adjustment"], "sort_order": 2},
    {"line_number": "3", "description": "Part I L3 Total net income (L1 + L2)", "line_type": "subtotal", "source_rules": ["R-SC1120S-INC"], "sort_order": 3},
    {"line_number": "4", "description": "Part I L4 SC apportioned income (Schedule G line 6, or L3)", "line_type": "calculated", "source_rules": ["R-SC1120S-APPT"], "sort_order": 4},
    {"line_number": "5", "description": "Part I L5 Active Trade or Business Income (from I-435 L14)", "line_type": "calculated", "source_rules": ["R-SC1120S-ATB"], "sort_order": 5},
    {"line_number": "6", "description": "Part I L6 Active Trade or Business Tax (I-435 L17, 3%)", "line_type": "calculated", "calculation": "R-SC1120S-ATB", "source_rules": ["R-SC1120S-ATB"], "sort_order": 6},
    {"line_number": "7", "description": "Part I L7 Income taxed to shareholders", "line_type": "input", "source_facts": ["income_taxed_to_shareholders"], "sort_order": 7},
    {"line_number": "8", "description": "Part I L8 SC net taxable income (L4 − L5 − L7)", "line_type": "subtotal", "source_rules": ["R-SC1120S-NET"], "sort_order": 8},
    {"line_number": "9", "description": "Part I L9 Income tax (L8 × 5%)", "line_type": "calculated", "calculation": "R-SC1120S-TAX", "source_rules": ["R-SC1120S-TAX"], "sort_order": 9},
    {"line_number": "10", "description": "Part I L10 Total income tax (L6 + L9)", "line_type": "subtotal", "source_rules": ["R-SC1120S-TAX"], "sort_order": 10},
    {"line_number": "19", "description": "Part II L19 Total capital and paid-in surplus", "line_type": "input", "source_facts": ["capital_paid_in_surplus"], "sort_order": 11},
    {"line_number": "20", "description": "Part II L20 License fee (L19 × .001 + $15, min $25)", "line_type": "calculated", "calculation": "R-SC1120S-LIC", "source_rules": ["R-SC1120S-LIC"], "sort_order": 12},
    {"line_number": "WH", "description": "SC1120S-WH Nonresident shareholder withholding (5%)", "line_type": "calculated", "source_rules": ["R-SC1120S-WH"], "sort_order": 13},
]

SC1120S_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_SC1120S_ATB", "title": "ATB is an entity-level 3% election — shareholders EXCLUDE via I-335 line 6", "severity": "info",
     "condition": "atb_election is True", "message": "The Active Trade or Business election (§12-6-545(G)) taxes active trade or business income at the entity level at 3% (via I-435, SC1120S L5/L6). Electing shareholders EXCLUDE that income — subtract it on I-335 line 6 (from SC1120S K-1 line 13); NO shareholder credit. This is separate from the general 5% SC income tax (L9) on any remaining SC net taxable income.",
     "notes": "Q2."},
    {"diagnostic_id": "D_SC1120S_LICENSE", "title": "License fee required of ALL corporations — $25 minimum", "severity": "info",
     "condition": "always (SC1120S Part II)", "message": "Every S corporation owes the SC license fee (Part II): total capital and paid-in surplus × .001, plus $15, with a $25 MINIMUM. Multi-state corporations apportion the fee base via Schedule E (not computed in v1 — determine manually). This is in addition to the income tax (Part I).",
     "notes": "Q1/W3."},
    {"diagnostic_id": "D_SC1120S_WH", "title": "Nonresident shareholder withholding rides a SEPARATE SC1120S-WH (5%)", "severity": "info",
     "condition": "nonresident shareholder present", "message": "Unlike the partnership (which computes withholding on the SC1065 face), the S corporation remits 5% nonresident shareholder withholding on a SEPARATE form, SC1120S-WH, due the 15th day of the 3rd month after year-end. Exempt: shareholders filing an I-309 affidavit, composite shareholders, IRC 501(a)-exempt shareholders, and ATB income taxed at the entity level.",
     "notes": "Q4."},
    {"diagnostic_id": "D_SC1120S_ANNUAL", "title": "Schedule D Annual Report required of all corporations", "severity": "info",
     "condition": "always", "message": "The SC1120S includes the Schedule D Annual Report, required of ALL corporations. It is not modeled in v1 (informational/registration data) — complete it on the return.",
     "notes": "Q1 RED-defer."},
    {"diagnostic_id": "D_SC1120S_DEPR", "title": "SC decouples from §168(k) bonus — add back via Schedule A&B", "severity": "info",
     "condition": "bonus depreciation or §179 present", "message": "SC did NOT adopt IRC §168(k) bonus depreciation. Add back the placed-in-service-year bonus difference on Schedule A&B (the L2 adjustment), keep a separate SC depreciation schedule (RR #05-2), and take the offsetting subtraction over the asset's remaining life. Adjust disposition gain/loss for the SC-vs-federal basis difference. SC §179 = $1,250,000 / $3,130,000 (pre-OBBBA; pending SCDOR confirmation) — see D_SC1120S_179.",
     "notes": "Q2/W2."},
    {"diagnostic_id": "D_SC1120S_179", "title": "SC §179 = $1,250,000 / $3,130,000 (pre-OBBBA; SCDOR states no figure)", "severity": "warning",
     "condition": "§179 deduction present", "message": "SC conforms to IRC §179 as of 12/31/2024 (pre-OBBBA), NOT the OBBBA $2,500,000 / $4,000,000. v1 pins the indexed 2025 figures $1,250,000 / $3,130,000 (Reading A; Rev. Proc. 2024-40); SCDOR states no §179 dollar figure — pending confirmation. Monitor H.3368 (would conform to OBBBA).",
     "notes": "Q3/W1/W2."},
]

SC1120S_SCENARIOS: list[dict] = [
    {"scenario_name": "SC1120S-T1 — ATB elected, 3% entity tax + no residual 5%", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"atb_election": True, "fed_1120s_sch_k": 400000, "sc_adjustment": 0, "is_multistate": False,
                "atb_income": 400000, "atb_already_taxed": 0, "income_taxed_to_shareholders": 0},
     "expected_outputs": {"SC1120S_L3": 400000, "SC1120S_L4": 400000, "SC1120S_L6": 12000, "SC1120S_L8": 0, "SC1120S_L9": 0, "SC1120S_L10": 12000},
     "notes": "L3 = 400,000; single-state L4 = 400,000; ATB L5 = 400,000 → L6 = round(400,000 × 0.03) = 12,000; L8 = 400,000 − 400,000 − 0 = 0 → L9 = 0; L10 = 12,000."},
    {"scenario_name": "SC1120S-T2 — general 5% SC income tax on non-ATB net (built-in gains)", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"atb_election": False, "fed_1120s_sch_k": 100000, "sc_adjustment": 0, "is_multistate": False,
                "atb_income": 0, "income_taxed_to_shareholders": 0},
     "expected_outputs": {"SC1120S_L4": 100000, "SC1120S_L6": 0, "SC1120S_L8": 100000, "SC1120S_L9": 5000, "SC1120S_L10": 5000},
     "notes": "No ATB election; the whole SC net taxable income (e.g. built-in gains taxed at the entity) → L8 = 100,000; L9 = 100,000 × 5% = 5,000; L10 = 5,000."},
    {"scenario_name": "SC1120S-T3 — license fee computed (capital × .001 + $15)", "scenario_type": "edge", "sort_order": 3,
     "inputs": {"capital_paid_in_surplus": 2000000},
     "expected_outputs": {"SC1120S_L20": 2015},
     "notes": "License fee = 2,000,000 × .001 = 2,000, + $15 = 2,015 (well above the $25 minimum)."},
    {"scenario_name": "SC1120S-T4 — license fee $25 minimum floor", "scenario_type": "edge", "sort_order": 4,
     "inputs": {"capital_paid_in_surplus": 5000},
     "expected_outputs": {"SC1120S_L20": 25},
     "notes": "5,000 × .001 = 5, + $15 = 20 → below the $25 minimum → L20 = 25."},
    {"scenario_name": "SC1120S-T5 — §179 SC-limit difference ($1.25M cap)", "scenario_type": "edge", "sort_order": 5,
     "inputs": {"federal_sec179_deduction": 1400000, "sec179_property_cost": 2500000},
     "expected_outputs": {"sc_sec179": 1250000, "sec179_delta": 150000},
     "notes": "Same as SC1065-T4: SC §179 capped at 1,250,000; delta 150,000 separately stated to shareholders."},
    {"scenario_name": "SC1120S-T6 — nonresident shareholder 5% withholding (SC1120S-WH)", "scenario_type": "edge", "sort_order": 6,
     "inputs": {"atb_election": False, "nonresident_sh_income": 120000},
     "expected_outputs": {"SC1120S_WH": 6000},
     "notes": "Nonresident shareholders' SC taxable income 120,000 × 5% = 6,000, remitted on the separate SC1120S-WH."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORMS registry + flow assertions
# ═══════════════════════════════════════════════════════════════════════════

FORMS: list[dict] = [
    {
        "identity": {"form_number": "SC1065", "form_title": "SC1065 — South Carolina Partnership Return + ATB/PTET (TY2025)",
                     "entity_types": ["1065"],
                     "notes": "SC partnership return. Federal Sch K → Schedule SC-K (SC adjustments + dual-method apportionment, 4 decimals) → SC-taxable net business income (SC-K L21 → L1). The SC PTET is the §12-6-545(G) Active Trade or Business election (page-1 checkbox): ATB income (only) × 3% at the entity level (I-435 → L2/L3), which drops out of both partners' income and the 5% nonresident-withholding base (L6 = L1 − L2). Owner side is an EXCLUSION (I-335 L6, from SC1065 K-1 L14), not a credit. SC decouples from §168(k); SC §179 $1.25M/$3.13M (pre-OBBBA)."},
        "facts": SC1065_FACTS, "rules": SC1065_RULES, "rule_links": SC1065_RULE_LINKS,
        "lines": SC1065_LINES, "diagnostics": SC1065_DIAGNOSTICS, "scenarios": SC1065_SCENARIOS,
    },
    {
        "identity": {"form_number": "SC1120S", "form_title": "SC1120S — South Carolina S Corporation Income Tax Return + ATB/PTET + License Fee (TY2025)",
                     "entity_types": ["1120S"],
                     "notes": "SC S-corp return. Two parts: Part I income tax (federal 1120S Sch K + Schedule A&B SC adjustments → apportioned L4; the same I-435 3% ATB tax on L5/L6 + a general 5% SC income tax on non-ATB net income L8→L9; total L10) + Part II the LICENSE FEE (capital × .001 + $15, min $25). Nonresident shareholder withholding (5%) rides a SEPARATE SC1120S-WH. Shareholders exclude entity-taxed ATB via I-335 L6 (from SC1120S K-1 L13). ~80% shares the SC1065 SC-K/apportionment/I-435 engine."},
        "facts": SC1120S_FACTS, "rules": SC1120S_RULES, "rule_links": SC1120S_RULE_LINKS,
        "lines": SC1120S_LINES, "diagnostics": SC1120S_DIAGNOSTICS, "scenarios": SC1120S_SCENARIOS,
    },
]

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-SC1065-ATB", "title": "SC1065 ATB entity tax = ATB income × 3%, gated on the election", "assertion_type": "reconciliation",
     "entity_types": ["1065"], "status": "draft", "sort_order": 1,
     "description": "When atb_election, SC1065 L3 = round((ATB income − ATB already taxed) × 0.03) via I-435 L16/L17; when not elected, the ATB lines are blank (pure pass-through).",
     "definition": {"rule": "R-SC1065-ATB", "check": "L3 = round(max(0, atb_income - atb_already_taxed) * 0.03) if atb_election else blank"}},
    {"assertion_id": "FA-SC1065-OWNER", "title": "Partners exclude entity-taxed ATB via I-335 line 6 (SC1065 K-1 line 14)", "assertion_type": "flow_assertion",
     "entity_types": ["1065"], "status": "draft", "sort_order": 2,
     "description": "When ATB is elected, each partner's share of entity-taxed ATB income (SC1065 K-1 line 14) is SUBTRACTED on I-335 line 6 — an exclusion, not a credit (§12-6-545(G)(3)).",
     "definition": {"rule": "R-SC1065-OWNER", "check": "partner K-1 L14 -> I-335 L6 subtraction; no owner credit"}},
    {"assertion_id": "FA-SC1065-NRW", "title": "SC1065 5% nonresident withholding, ATB/exemptions displace it", "assertion_type": "reconciliation",
     "entity_types": ["1065"], "status": "draft", "sort_order": 3,
     "description": "SC1065 L9 = round((L6 − L7) × 0.05) where L6 = L1 − L2 (entity-taxed ATB removed) and L7 = exempt shares (residents/I-309/composite/501(a)).",
     "definition": {"rule": "R-SC1065-WH", "check": "L9 = round(max(0, (L1 - L2) - L7) * 0.05)"}},
    {"assertion_id": "FA-SC1065-DEPR", "title": "SC decouples from §168(k): SC-K bonus add-back / remaining-life subtraction", "assertion_type": "flow_assertion",
     "entity_types": ["1065"], "status": "draft", "sort_order": 4,
     "description": "Federal bonus depreciation is added back on Schedule SC-K in the placed-in-service year and recovered via a higher-SC-basis subtraction over the remaining life; SC §179 capped at $1.25M/$3.13M (pre-OBBBA).",
     "definition": {"rule": "R-SC1065-SCK", "check": "sck_col_c includes bonus_depr_addback (+) and sc_depr_subtraction (−)"}},
    {"assertion_id": "FA-SC1065-APPORT", "title": "SC1065 dual-method apportionment (sales-only vs gross-receipts, 4 decimals)", "assertion_type": "reconciliation",
     "entity_types": ["1065"], "status": "draft", "sort_order": 5,
     "description": "Sales-only (TPP dealers) or gross-receipts (service/financial) factor to four decimals; SC-K L20 = apportionable income × factor.",
     "definition": {"rule": "R-SC1065-APPORT", "check": "factor = round(sc_num / total_den, 4) by business-type method"}},
    {"assertion_id": "FA-SC1120S-ATB", "title": "SC1120S ATB entity tax = ATB income × 3%; shareholders exclude (K-1 L13)", "assertion_type": "reconciliation",
     "entity_types": ["1120S"], "status": "draft", "sort_order": 6,
     "description": "When atb_election, SC1120S L6 = round((ATB income − ATB already taxed) × 0.03); shareholders exclude entity-taxed ATB on I-335 line 6 (from SC1120S K-1 line 13).",
     "definition": {"rule": "R-SC1120S-ATB", "check": "L6 = round(max(0, atb_income - atb_already_taxed) * 0.03) if atb_election else blank; K-1 L13 -> I-335 L6"}},
    {"assertion_id": "FA-SC1120S-5PCT", "title": "SC1120S general 5% SC income tax on non-ATB net; total = L6 + L9", "assertion_type": "reconciliation",
     "entity_types": ["1120S"], "status": "draft", "sort_order": 7,
     "description": "SC1120S L9 = round(L8 × 0.05) where L8 = L4 − L5 − L7 (SC net taxable income remaining at the entity); total income tax L10 = L6 (3% ATB) + L9 (5%).",
     "definition": {"rule": "R-SC1120S-TAX", "check": "L9 = round(max(0, L4 - L5 - L7) * 0.05); L10 = L6 + L9"}},
    {"assertion_id": "FA-SC1120S-LIC", "title": "SC1120S license fee = capital × .001 + $15 (min $25)", "assertion_type": "reconciliation",
     "entity_types": ["1120S"], "status": "draft", "sort_order": 8,
     "description": "SC1120S Part II L20 = max(25, round(capital_paid_in_surplus × 0.001) + 15). Required of all corporations, in addition to the income tax.",
     "definition": {"rule": "R-SC1120S-LIC", "check": "L20 = max(25, round(capital * 0.001) + 15)"}},
]


# ═══════════════════════════════════════════════════════════════════════════
# Command
# ═══════════════════════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = (
        "Load the SC pass-through specs (SC1065 + SC1120S + SC PTET/ATB, TY2025). "
        "Refuses to seed until Ken sets READY_TO_SEED=True after the in-session review walk (W1-W5)."
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad SC pass-through specs (SC1065 + SC1120S + SC ATB/PTET)\n"))
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
                "\nREFUSING TO SEED SC PASS-THROUGH: not cleared to seed.\n\n"
                "Content is authored, but seeding is gated until Ken reviews the packet\n"
                "(W1 the §179 $1.25M/$3.13M Reading-A pin; W2 the 12/31/2024 conformity +\n"
                "the H.3368 live wire; W3 the 3% ATB / 5% NRW / 5% S-corp / license-fee rates;\n"
                "W4 the ATB active/passive split; W5 the dual-method apportionment) and flips\n"
                "the sentinel.\n\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True to proceed)\n\n"
                f"Currently empty / placeholder:\n  {still_empty}\n\n"
                "To proceed: review the module-level data lists (and sc1065_source_brief.md),\n"
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
            defaults={"form_title": identity["form_title"], "entity_types": identity.get("entity_types", ["1065"]),
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
        self.stdout.write("SC pass-through specs loaded.")
        for spec in FORMS:
            fn = spec["identity"]["form_number"]
            self.stdout.write(
                f"  {fn}: facts {len(spec['facts'])} / rules {len(spec['rules'])} / lines {len(spec['lines'])} / "
                f"diag {len(spec['diagnostics'])} / tests {len(spec['scenarios'])}"
            )
        self.stdout.write(f"  Flow assertions: {len(FLOW_ASSERTIONS)}")
        self.stdout.write("=" * 60)
