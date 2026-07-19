"""Load the 1065 Schedule L + Schedule B spec — form 4 of the 1065-core campaign.

Fresh-authored 2026-07-04 per D-1. Seeds TWO forms:
  - **1065_L** — Schedule L: Balance Sheets per Books (BOY/EOY). Assets lines 1-14, Liabilities &
    Capital lines 15-22. Line 14 total assets = Σ asset lines (contra accounts netted); line 22
    total liab & capital = Σ lines 15-21. The load-bearing checks: **L14 == L22 (balance)** and
    **L21 partners' capital EOY = Schedule M-2 line 9** (tax-basis ending capital).
  - **1065_B** — Schedule B: Other Information (the 33 Yes/No/data questions). The load-bearing
    computed piece: **Q4 small-partnership exemption** (all four conditions → suppress Schedules L,
    M-1, M-2, item F, K-1 item L) + **Q24 §163(j) $31M test → Form 8990**.

SOURCE: line maps extracted VERBATIM 2026-07-04 from the FINAL 2025 f1065.pdf — Schedule L on page 6
(Cat. 11390Z, pymupdf dump); Schedule B on pages 2-4 (33 questions). NOT recollection. Confirms the
brief §4.3 (Schedule L) + §4.1 (Schedule B 33 Qs) transcription.

RECONCILE TARGET (D-1, brief §2): tts `compute.py` (Schedule L totals, ~lines 313-329;
`compute_schedule_l()` ~1619-1715) + `seed_1065.py` (L/B field seed). Survey done 2026-07-04.
What tts does:
  - Schedule L totals: L15 (total assets) = Σ asset lines with contra accounts (L2a-L2b etc.)
    netted; L24 (total liab & capital) = Σ(L16..L23). BOY (a-col) + EOY (d-col).
  - `compute_schedule_l()` AUTO-COMPUTES the EOY depreciable/intangible roll-forward from the
    DepreciationAsset model: L10d/L10e (buildings gross / accum depr) and L13d/L13e (intangibles /
    accum amort) — tts is AHEAD here (RS models these as computed-pull YELLOW).
  - Schedule B: 18 condensed questions (B1-B18) seeded; B6 = the small-partnership exemption
    (= face Q4), B16 = the §163(j) $31M test (= face Q24). All data-entry booleans.

RECONCILE FINDINGS logged for the Ken walk (D-1 adjudications) — see 1065_core_reconcile_log.md:
  1. ⚠ **tts Schedule L numbering is OFFSET from the 2025 face** (tts L1-L24 vs face 1-22): tts
     splits face 7a/7b into whole lines L7/L8 and face 19a/19b into L20/L21, shifting the tail by
     one (tts L15=face 14 total assets; tts L24=face 22 total liab&cap; tts L23=face 21 partners'
     capital). SAME KIND of label mismatch as the page-1 off-by-one (spine reconcile #1). Arithmetic
     identical. Ken call: map at build vs renumber tts to the face.
  2. 🔨 **NO balance check in tts** (L15 vs L24 never compared; no out-of-balance diagnostic). The
     spec introduces R-L-BALANCE + D_L_BALANCE_{BOY,EOY}. Build-gap for tts.
  3. 🔨 **Q4 gate stored but NOT enforced.** tts stores B6 (=Q4) as a data-entry boolean but no rule
     auto-suppresses L/M-1/M-2 on it. The spec makes Q4 a COMPUTED gate (R-B4-SMALL = all four
     conditions) feeding m_schb_q4_small. Build-gap.
  4. 🔨 **No $31M M-3/§163(j) threshold logic.** tts stores B16 (=Q24) as data-entry; no $31M
     compute, no M-3 ($10M/$35M) threshold. R-B24-8990 computes the Form 8990 trigger; R-L-M3 flags
     the M-3 threshold (Decision B RED-defer). Build-gap.
  5. ⚠ **L21 (partners' capital) EOY vs M-2 line 9 — no tie in tts** (L23d data-entry, M2_9 computed,
     no reconciliation). The spec adds R-L-21-TIE + D_L_21_M2_TIE. Carries the M-2 leg's tie home.
  6. ✅ **tts Schedule B = 18 condensed questions; the 2025 face = 33.** The spec is authored to the
     FULL 33-question face (authority); tts's condensed set is a build-mapping concern (Ken call —
     expand tts to 33 or keep the condensed map). Notable face-only Qs not in tts's 18: Q22 §267A,
     Q25 QOF (Form 8996), Q29 Form 7208 stock-repurchase excise, Q26 §864(c)(8), Q27 Reg 1.707-8.

SCOPE DECISIONS proposed for the Ken walk (carry the spine leg's A/B/C posture):
  - **D (Sch L numbering):** author to the 2025 FACE (1-22); log tts's L1-L24 offset as a build
    remap (finding #1). RECOMMEND face.
  - **E (§754 / §743(b) / §734(b) basis-adjustment MATH, Q10):** RED-defer — structure + cited
    authority + flag only; the basis-adjustment computation is a future leg. Brief §4.1 says defer.
  - **F (Schedule M-3 + B-1/B-2/B-3 sub-schedules):** RED-defer (carry Decision B). M-3 threshold
    (L14 ≥ $10M / receipts ≥ $35M) surfaces as an INFO diagnostic (R-L-M3); B-1/B-2/PR modeled as
    attachment-trigger flags, not full sub-schedules.
  - **G (Sch L depth):** FULL a/b sub-lines (2a/2b, 9a/9b, 10a/10b, 12a/12b) — matches the 1120S_SCHL
    precedent + tts + Ken's depreciation focus (accum. depreciation on 9b is load-bearing).

AUTHORITY: primary IRC §705(a) (L21↔M-2 tax-basis capital tie; re-used verbatim) + §754/§743/§734
(Q10 election + optional basis adjustments) + §448(c) (the $31M gross-receipts test behind Q24
§163(j)) + §6221(b) (Q33 centralized-audit election out) — all quoted VERBATIM from Cornell LII this
session; the 2025 f1065 page-6 (Schedule L) + pages 2-4 (Schedule B) face as filing authority
(requires_human_review). Verbatim face text extracted from the FINAL PDF this session.
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


# FRESH-AUTHORED 2026-07-04 (L/B leg). Per D-1: authored READY_TO_SEED=False; Ken walked the
# reconcile findings + scope decisions (2026-07-04): D=author to the face, E=§754 basis-adjust math
# RED-defer, F=M-3/B-1/B-2 RED-defer, G=full a/b Sch L sub-lines — all approved; "flip seed export".
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
     "Partnership return core (Form 1065) — Schedule L (balance sheet per books) and Schedule B "
     "(other information; the 33 Yes/No/data questions incl. the small-partnership exemption)."),
]

AUTHORITY_SOURCES: list[dict] = [
    # ── IRC §705 — partner's basis (Schedule L line 21 ↔ M-2 tax-basis capital tie) ──
    {
        "source_code": "IRC_705",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1065",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §705 — Determination of Basis of Partner's Interest (tax-basis capital roll-forward)",
        "citation": "26 U.S.C. §705(a)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/705",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "Schedule L line 21 (partners' capital accounts) on a tax-basis L ties to Schedule M-2 "
                 "line 9 (ending) / line 1 (beginning) — the §705 transactional roll-forward. Re-used from "
                 "the M-1/M-2 + K-1 loads; verbatim.",
        "topics": ["partnership_1065_core"],
        "excerpts": [
            {
                "excerpt_label": "§705(a) — basis increased by income, decreased by distributions/losses",
                "location_reference": "26 U.S.C. §705(a)(1), (2)",
                "excerpt_text": (
                    "The adjusted basis of a partner's interest in a partnership shall, except as provided "
                    "in subsection (b), be the basis of such interest determined under section 722 or "
                    "section 742— (1) increased by the sum of his distributive share for the taxable year "
                    "and prior taxable years of— (A) taxable income of the partnership as determined under "
                    "section 703(a), (B) income of the partnership exempt from tax, and (C) the excess of "
                    "the deductions for depletion over the basis of the property subject to depletion; "
                    "(2) decreased (but not below zero) by distributions by the partnership as provided in "
                    "section 733 and by the sum of his distributive share of— (A) losses of the "
                    "partnership, and (B) expenditures of the partnership not deductible in computing its "
                    "taxable income and not properly chargeable to capital account."
                ),
                "summary_text": "Tax-basis capital roll-forward behind Schedule L line 21 = M-2 line 9: BOY + "
                                "income share − distributions − loss/nondeductible = EOY (§705/§733).",
                "is_key_excerpt": True,
            },
        ],
    },
    # ── IRC §754 — optional basis adjustment election (Schedule B Q10) ──
    {
        "source_code": "IRC_754",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1065",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §754 — Manner of Electing Optional Adjustment to Basis of Partnership Property",
        "citation": "26 U.S.C. §754 (with §734(b) distributions / §743(b) transfers)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/754",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "Schedule B Q10a (§754 election) triggers §734(b) (distributions) + §743(b) (transfers of a "
                 "partnership interest) optional basis adjustments (Q10b/10c/10d). The basis-adjustment MATH "
                 "is RED-deferred (Decision E) — structure + flag only this leg. Verbatim from Cornell LII.",
        "topics": ["partnership_1065_core"],
        "excerpts": [
            {
                "excerpt_label": "§754 — the election (verbatim)",
                "location_reference": "26 U.S.C. §754",
                "excerpt_text": (
                    "If a partnership files an election, in accordance with regulations prescribed by the "
                    "Secretary, the basis of partnership property shall be adjusted, in the case of a "
                    "distribution of property, in the manner provided in section 734 and, in the case of a "
                    "transfer of a partnership interest, in the manner provided in section 743. Such an "
                    "election shall apply with respect to all distributions of property by the partnership "
                    "and to all transfers of interests in the partnership during the taxable year with "
                    "respect to which such election was filed and all subsequent taxable years. Such "
                    "election may be revoked by the partnership, subject to such limitations as may be "
                    "provided by regulations prescribed by the Secretary."
                ),
                "summary_text": "A §754 election → §734(b) (on distributions) + §743(b) (on interest transfers) "
                                "optional basis adjustments; applies to all such events for the year + all "
                                "subsequent years until revoked. (Sch B Q10; basis-adjust math RED-deferred.)",
                "is_key_excerpt": True,
            },
        ],
    },
    # ── IRC §448(c) — the gross-receipts test ($31M behind Sch B Q24 / §163(j)) ──
    {
        "source_code": "IRC_448C",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1065",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §448(c) — Gross Receipts Test ($25M base, inflation-adjusted to $31M for 2025)",
        "citation": "26 U.S.C. §448(c)(1), (c)(4)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/448",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "Schedule B Q24b tests aggregate average annual gross receipts (§448(c)) for the 3 prior "
                 "years > $31 million (+ business interest expense) → §163(j) applies → attach Form 8990. "
                 "The $31M figure IS the §448(c)(1) $25,000,000 base as inflation-adjusted under §448(c)(4) "
                 "for tax years beginning in 2025 (the 2025 face states '$31 million' verbatim). Verbatim "
                 "from Cornell LII.",
        "topics": ["partnership_1065_core"],
        "excerpts": [
            {
                "excerpt_label": "§448(c)(1) — the $25M base + (c)(4) inflation adjustment (verbatim)",
                "location_reference": "26 U.S.C. §448(c)(1), (c)(4)",
                "excerpt_text": (
                    "(c)(1) In general. A corporation or partnership meets the gross receipts test of this "
                    "subsection for any taxable year if the average annual gross receipts of such entity for "
                    "the 3-taxable-year period ending with the taxable year which precedes such taxable year "
                    "does not exceed $25,000,000. ... (c)(4) Adjustment for inflation. In the case of any "
                    "taxable year beginning after December 31, 2018, the dollar amount in paragraph (1) "
                    "shall be increased by an amount equal to— (A) such dollar amount, multiplied by (B) the "
                    "cost-of-living adjustment determined under section 1(f)(3) for the calendar year in "
                    "which the taxable year begins, by substituting 'calendar year 2017' for 'calendar year "
                    "2016' in subparagraph (A)(ii) thereof. If any amount as increased under the preceding "
                    "sentence is not a multiple of $1,000,000, such amount shall be rounded to the nearest "
                    "multiple of $1,000,000."
                ),
                "summary_text": "§448(c) gross-receipts test: $25M base (3-yr avg annual gross receipts), "
                                "inflation-adjusted to $31M for TY2025 (the §163(j) small-business exemption "
                                "figure the Sch B Q24 face states verbatim).",
                "is_key_excerpt": True,
            },
        ],
    },
    # ── IRC §6221(b) — election out of the centralized partnership audit regime (Sch B Q33) ──
    {
        "source_code": "IRC_6221",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1065",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §6221 — Determination at Partnership Level; §6221(b) Election Out (BBA)",
        "citation": "26 U.S.C. §6221(a), (b)(1)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/6221",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "Schedule B Q33 — a partnership furnishing 100 or fewer K-1s with only eligible partners "
                 "(individual / C corp / eligible foreign entity / S corp / estate of a deceased partner) "
                 "may elect out of the BBA centralized audit regime (attach Schedule B-2). If NOT electing "
                 "out, the Partnership Representative designation block must be completed. Verbatim from "
                 "Cornell LII.",
        "topics": ["partnership_1065_core"],
        "excerpts": [
            {
                "excerpt_label": "§6221(a) partnership-level determination + (b)(1) election out (verbatim)",
                "location_reference": "26 U.S.C. §6221(a), (b)(1)",
                "excerpt_text": (
                    "(a) In general. Any adjustment to a partnership-related item shall be determined, and "
                    "any tax attributable thereto shall be assessed and collected, and the applicability of "
                    "any penalty, addition to tax, or additional amount which relates to an adjustment to "
                    "any such item shall be determined, at the partnership level, except to the extent "
                    "otherwise provided in this subchapter. (b)(1) In general. This subchapter shall not "
                    "apply with respect to any partnership for any taxable year if— (A) the partnership "
                    "elects the application of this subsection for such taxable year, (B) for such taxable "
                    "year the partnership is required to furnish 100 or fewer statements under section "
                    "6031(b) with respect to its partners, (C) each of the partners of such partnership is "
                    "an individual, a C corporation, any foreign entity that would be treated as a C "
                    "corporation were it domestic, an S corporation, or an estate of a deceased partner, "
                    "(D) the election— (i) is made with a timely filed return for such taxable year, and "
                    "(ii) includes (in the manner prescribed by the Secretary) a disclosure of the name and "
                    "taxpayer identification number of each partner of such partnership, and (E) the "
                    "partnership notifies each such partner of such election in the manner prescribed by "
                    "the Secretary."
                ),
                "summary_text": "BBA audits are partnership-level unless a ≤100-K-1, all-eligible-partner "
                                "partnership elects out (§6221(b), Schedule B-2). Sch B Q33.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ── 2025 Form 1065 page 6 — Schedule L face (filing authority, verbatim) ──
    {
        "source_code": "IRS_2025_F1065",
        "source_type": "official_form",
        "source_rank": "implementation_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1065",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "Form 1065 (2025) — Schedule L (page 6, balance sheet) + Schedule B (pages 2-4, other "
                 "information, 33 questions)",
        "citation": "Form 1065 (2025), Cat. No. 11390Z, page 6 Schedule L lines 1-22; pages 2-4 Schedule B "
                    "questions 1-33",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f1065.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": "Schedule L + Schedule B line/question structure extracted VERBATIM 2026-07-04 from the "
                 "FINAL 2025 f1065.pdf (page 6 = Schedule L; pages 2-4 = Schedule B 33 Qs; pymupdf). Key: "
                 "L14 total assets, L22 total liab & capital, L21 partners' capital; Q4 four-condition "
                 "small-partnership exemption, Q24 §163(j) $31M test. REQUIRES HUMAN REVIEW.",
        "topics": ["partnership_1065_core"],
        "excerpts": [
            {
                "excerpt_label": "Schedule L Assets lines 1-14 (verbatim, f1065 2025 p.6)",
                "location_reference": "f1065 (2025) page 6, Schedule L — Assets",
                "excerpt_text": (
                    "Schedule L Balance Sheets per Books. Beginning of tax year (a)(b) / End of tax year "
                    "(c)(d). Assets: 1 Cash. 2a Trade notes and accounts receivable, b Less allowance for "
                    "bad debts. 3 Inventories. 4 U.S. Government obligations. 5 Tax-exempt securities. 6 "
                    "Other current assets (attach statement). 7a Loans to partners (or persons related to "
                    "partners), b Mortgage and real estate loans. 8 Other investments (attach statement). "
                    "9a Buildings and other depreciable assets, b Less accumulated depreciation. 10a "
                    "Depletable assets, b Less accumulated depletion. 11 Land (net of any amortization). "
                    "12a Intangible assets (amortizable only), b Less accumulated amortization. 13 Other "
                    "assets (attach statement). 14 Total assets."
                ),
                "summary_text": "Sch L Assets 1-14: paired lines 2a/2b, 9a/9b, 10a/10b, 12a/12b net to the "
                                "column; 14 total assets = Σ net asset lines (contra accounts netted).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule L Liabilities & Capital lines 15-22 (verbatim, f1065 2025 p.6)",
                "location_reference": "f1065 (2025) page 6, Schedule L — Liabilities and Capital",
                "excerpt_text": (
                    "Liabilities and Capital: 15 Accounts payable. 16 Mortgages, notes, bonds payable in "
                    "less than 1 year. 17 Other current liabilities (attach statement). 18 All nonrecourse "
                    "loans. 19a Loans from partners (or persons related to partners), b Mortgages, notes, "
                    "bonds payable in 1 year or more. 20 Other liabilities (attach statement). 21 Partners' "
                    "capital accounts. 22 Total liabilities and capital."
                ),
                "summary_text": "Sch L Liab & Capital 15-22: 21 partners' capital (tax-basis → M-2 line 9); "
                                "22 total liab & capital = Σ lines 15-21. Balance: line 14 == line 22.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule B Q4 small-partnership exemption (verbatim, f1065 2025 p.2)",
                "location_reference": "f1065 (2025) page 2, Schedule B question 4",
                "excerpt_text": (
                    "4 Does the partnership satisfy all four of the following conditions? a The "
                    "partnership's total receipts for the tax year were less than $250,000. b The "
                    "partnership's total assets at the end of the tax year were less than $1 million. c "
                    "Schedules K-1 are filed with the return and furnished to the partners on or before the "
                    "due date (including extensions) for the partnership return. d The partnership is not "
                    "filing and is not required to file Schedule M-3. If 'Yes,' the partnership is not "
                    "required to complete Schedules L, M-1, and M-2; item F on page 1 of Form 1065; or item "
                    "L on Schedule K-1."
                ),
                "summary_text": "Q4 all-four (receipts < $250k AND assets < $1M AND timely K-1s AND not-M-3) → "
                                "Schedules L, M-1, M-2, item F, K-1 item L NOT required. The gating fact.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule B Q23/Q24 §163(j) + Q10 §754 + Q30/Q32/Q33 (verbatim, f1065 2025 pp.2-4)",
                "location_reference": "f1065 (2025) pages 2-4, Schedule B questions 10, 23, 24, 30, 32, 33",
                "excerpt_text": (
                    "10a Is the partnership making, or had it previously made (and not revoked), a section "
                    "754 election? ... b ... optional basis adjustment under section 743(b)? ... c ... "
                    "section 734(b)? ... d ... substantial built-in loss (section 743(d)) or substantial "
                    "basis reduction (section 734(d))? 23 Did the partnership have an election under section "
                    "163(j) for any real property trade or business or any farming business in effect during "
                    "the tax year? 24 Does the partnership satisfy one or more of the following? ... b The "
                    "partnership's aggregate average annual gross receipts (determined under section 448(c)) "
                    "for the 3 tax years preceding the current tax year are more than $31 million and the "
                    "partnership has business interest expense. ... If 'Yes' to any, complete and attach "
                    "Form 8990. 30 At any time during this tax year, did the partnership (a) receive ... or "
                    "(b) sell, exchange, or otherwise dispose of a digital asset ...? 32 Check this box if an "
                    "election out of subchapter K under section 761 is being made. 33 Is the partnership "
                    "electing out of the centralized partnership audit regime under section 6221(b)? If "
                    "'Yes,' the partnership must complete Schedule B-2 (Form 1065). ... If 'No,' complete "
                    "Designation of Partnership Representative below."
                ),
                "summary_text": "Sch B load-bearing Qs: 10 §754/§743(b)/§734(b) (basis-adjust math RED-defer); "
                                "23/24 §163(j) $31M → Form 8990; 30 digital asset; 32 §761 out; 33 §6221(b) "
                                "audit election out → Sch B-2 / else PR designation.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ── 2025 Instructions — the balance-sheet-must-balance rule + M-3 threshold ──
    {
        "source_code": "IRS_2025_I1065",
        "source_type": "official_instructions",
        "source_rank": "implementation_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1065",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Form 1065 — Schedule L (tax-basis/book balance sheet, M-2 tie) + "
                 "the Schedule M-3 threshold + the Schedule B Q4 exemption",
        "citation": "Instructions for Form 1065 (2025), Cat. No. 11392V, Schedule L + Schedules M-1/M-2/M-3 "
                    "+ Schedule B question 4",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i1065.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": "Schedule L must balance (line 14 total assets = line 22 total liab & capital); line 21 "
                 "partners' capital ties to Schedule M-2 line 9 when L is on the tax basis. Schedule M-3 "
                 "replaces M-1 at total assets ≥ $10M (or adjusted total assets ≥ $10M / total receipts ≥ "
                 "$35M / a reportable-entity-partner ≥ 50%) — Decision F RED-defer, flagged. Q4 exemption "
                 "per the brief §4.1/§4.3 verbatim. REQUIRES HUMAN REVIEW.",
        "topics": ["partnership_1065_core"],
        "excerpts": [
            {
                "excerpt_label": "Schedule M-3 threshold (Decision F RED-defer)",
                "location_reference": "i1065 (2025), Schedule L / Schedule M-3 who-must-file",
                "excerpt_text": (
                    "A partnership must complete Schedule M-3 (Form 1065) instead of Schedule M-1 if any of "
                    "the following apply: total assets at the end of the tax year (Schedule L, line 14, "
                    "column (d)) are $10 million or more; adjusted total assets are $10 million or more; "
                    "total receipts for the tax year are $35 million or more; or an entity that is a "
                    "reportable entity partner owns or is deemed to own, directly or indirectly, an interest "
                    "of 50% or more in the partnership's capital, profit, or loss."
                ),
                "summary_text": "M-3 replaces M-1 at ≥$10M total (or adjusted) assets / ≥$35M receipts / a "
                                "≥50% reportable-entity-partner. Season-one RED-defer (Decision F) — flagged "
                                "via R-L-M3 / D_L_M3, not built. Per the brief §4.3 transcription.",
                "is_key_excerpt": False,
            },
        ],
    },
]

# (source_code, form_code, link_type)
AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_F1065", "1065_L", "governs"),
    ("IRS_2025_I1065", "1065_L", "governs"),
    ("IRC_705", "1065_L", "informs"),
    ("IRS_2025_F1065", "1065_B", "governs"),
    ("IRS_2025_I1065", "1065_B", "governs"),
    ("IRC_754", "1065_B", "informs"),
    ("IRC_448C", "1065_B", "informs"),
    ("IRC_6221", "1065_B", "informs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 1: 1065_L — Schedule L (Balance Sheets per Books, BOY/EOY)
# ═══════════════════════════════════════════════════════════════════════════

L_IDENTITY = {
    "form_number": "1065_L",
    "entity_types": ["1065"],
    "form_title": "Schedule L (Form 1065, 2025) — Balance Sheets per Books",
    "notes": (
        "FRESH-AUTHORED 2026-07-04 (1065-core, form 4) from the FINAL 2025 f1065 page 6 (pymupdf verbatim). "
        "BOY/EOY balance sheet: Assets 1-14, Liabilities & Capital 15-22. Line 14 total assets = Σ asset "
        "lines (paired contra accounts 2a/2b, 9a/9b, 10a/10b, 12a/12b netted); line 22 total liab & "
        "capital = Σ lines 15-21. Load-bearing: R-L-BALANCE (14 == 22, both columns) + R-L-21-TIE (line 21 "
        "partners' capital EOY = M-2 line 9, BOY = M-2 line 1, tax basis). Small-partnership exemption "
        "(Sch B Q4) suppresses L (D_L_EXEMPT). ⚠ RECONCILE: tts numbers Schedule L L1-L24 (OFFSET one from "
        "the 2025 face — tts splits face 7a/7b→L7/L8, 19a/19b→L20/L21; tts L15=face14, L24=face22, "
        "L23=face21); tts has NO balance check and NO L21↔M-2 tie (build-gaps); tts auto-computes the "
        "9b/12b depreciable-asset EOY roll-forward from DepreciationAsset (AHEAD — modeled here as "
        "computed-pull). Decision D = author to the FACE. READY_TO_SEED=False."
    ),
}

# Facts: BOY + EOY for each face line. Paired lines carry the gross + the 'less' contra separately.
L_FACTS: list[dict] = [
    # ── Assets — Beginning of year ──
    {"fact_key": "l_1_cash_boy", "label": "1 (BOY) — Cash", "data_type": "decimal", "default_value": "0", "sort_order": 1},
    {"fact_key": "l_2a_receivables_boy", "label": "2a (BOY) — Trade notes and accounts receivable", "data_type": "decimal", "default_value": "0", "sort_order": 2},
    {"fact_key": "l_2b_allowance_boy", "label": "2b (BOY) — Less allowance for bad debts", "data_type": "decimal", "default_value": "0", "sort_order": 3, "notes": "Contra — subtracted from 2a."},
    {"fact_key": "l_3_inventories_boy", "label": "3 (BOY) — Inventories", "data_type": "decimal", "default_value": "0", "sort_order": 4},
    {"fact_key": "l_4_us_govt_boy", "label": "4 (BOY) — U.S. Government obligations", "data_type": "decimal", "default_value": "0", "sort_order": 5},
    {"fact_key": "l_5_tax_exempt_sec_boy", "label": "5 (BOY) — Tax-exempt securities", "data_type": "decimal", "default_value": "0", "sort_order": 6},
    {"fact_key": "l_6_other_current_boy", "label": "6 (BOY) — Other current assets", "data_type": "decimal", "default_value": "0", "sort_order": 7},
    {"fact_key": "l_7a_loans_partners_boy", "label": "7a (BOY) — Loans to partners (or related persons)", "data_type": "decimal", "default_value": "0", "sort_order": 8},
    {"fact_key": "l_7b_mortgage_re_loans_boy", "label": "7b (BOY) — Mortgage and real estate loans", "data_type": "decimal", "default_value": "0", "sort_order": 9},
    {"fact_key": "l_8_other_investments_boy", "label": "8 (BOY) — Other investments", "data_type": "decimal", "default_value": "0", "sort_order": 10},
    {"fact_key": "l_9a_buildings_boy", "label": "9a (BOY) — Buildings and other depreciable assets", "data_type": "decimal", "default_value": "0", "sort_order": 11},
    {"fact_key": "l_9b_accum_depr_boy", "label": "9b (BOY) — Less accumulated depreciation", "data_type": "decimal", "default_value": "0", "sort_order": 12, "notes": "Contra — subtracted from 9a. tts auto-computes the EOY roll-forward from DepreciationAsset."},
    {"fact_key": "l_10a_depletable_boy", "label": "10a (BOY) — Depletable assets", "data_type": "decimal", "default_value": "0", "sort_order": 13},
    {"fact_key": "l_10b_accum_depletion_boy", "label": "10b (BOY) — Less accumulated depletion", "data_type": "decimal", "default_value": "0", "sort_order": 14, "notes": "Contra — subtracted from 10a."},
    {"fact_key": "l_11_land_boy", "label": "11 (BOY) — Land (net of any amortization)", "data_type": "decimal", "default_value": "0", "sort_order": 15},
    {"fact_key": "l_12a_intangibles_boy", "label": "12a (BOY) — Intangible assets (amortizable only)", "data_type": "decimal", "default_value": "0", "sort_order": 16},
    {"fact_key": "l_12b_accum_amort_boy", "label": "12b (BOY) — Less accumulated amortization", "data_type": "decimal", "default_value": "0", "sort_order": 17, "notes": "Contra — subtracted from 12a. tts auto-computes the EOY roll-forward from DepreciationAsset."},
    {"fact_key": "l_13_other_assets_boy", "label": "13 (BOY) — Other assets", "data_type": "decimal", "default_value": "0", "sort_order": 18},
    {"fact_key": "l_14_total_assets_boy", "label": "14 (BOY) — Total assets", "data_type": "decimal", "sort_order": 19, "notes": "OUTPUT. = Σ asset lines with contra accounts netted."},
    # ── Assets — End of year ──
    {"fact_key": "l_1_cash_eoy", "label": "1 (EOY) — Cash", "data_type": "decimal", "default_value": "0", "sort_order": 20},
    {"fact_key": "l_2a_receivables_eoy", "label": "2a (EOY) — Trade notes and accounts receivable", "data_type": "decimal", "default_value": "0", "sort_order": 21},
    {"fact_key": "l_2b_allowance_eoy", "label": "2b (EOY) — Less allowance for bad debts", "data_type": "decimal", "default_value": "0", "sort_order": 22, "notes": "Contra — subtracted from 2a."},
    {"fact_key": "l_3_inventories_eoy", "label": "3 (EOY) — Inventories", "data_type": "decimal", "default_value": "0", "sort_order": 23},
    {"fact_key": "l_4_us_govt_eoy", "label": "4 (EOY) — U.S. Government obligations", "data_type": "decimal", "default_value": "0", "sort_order": 24},
    {"fact_key": "l_5_tax_exempt_sec_eoy", "label": "5 (EOY) — Tax-exempt securities", "data_type": "decimal", "default_value": "0", "sort_order": 25},
    {"fact_key": "l_6_other_current_eoy", "label": "6 (EOY) — Other current assets", "data_type": "decimal", "default_value": "0", "sort_order": 26},
    {"fact_key": "l_7a_loans_partners_eoy", "label": "7a (EOY) — Loans to partners (or related persons)", "data_type": "decimal", "default_value": "0", "sort_order": 27},
    {"fact_key": "l_7b_mortgage_re_loans_eoy", "label": "7b (EOY) — Mortgage and real estate loans", "data_type": "decimal", "default_value": "0", "sort_order": 28},
    {"fact_key": "l_8_other_investments_eoy", "label": "8 (EOY) — Other investments", "data_type": "decimal", "default_value": "0", "sort_order": 29},
    {"fact_key": "l_9a_buildings_eoy", "label": "9a (EOY) — Buildings and other depreciable assets", "data_type": "decimal", "default_value": "0", "sort_order": 30, "notes": "YELLOW — tts computes from DepreciationAsset (BOY + additions − dispositions)."},
    {"fact_key": "l_9b_accum_depr_eoy", "label": "9b (EOY) — Less accumulated depreciation", "data_type": "decimal", "default_value": "0", "sort_order": 31, "notes": "Contra. YELLOW — tts computes (BOY accum + current-yr depr − disposed accum)."},
    {"fact_key": "l_10a_depletable_eoy", "label": "10a (EOY) — Depletable assets", "data_type": "decimal", "default_value": "0", "sort_order": 32},
    {"fact_key": "l_10b_accum_depletion_eoy", "label": "10b (EOY) — Less accumulated depletion", "data_type": "decimal", "default_value": "0", "sort_order": 33, "notes": "Contra — subtracted from 10a."},
    {"fact_key": "l_11_land_eoy", "label": "11 (EOY) — Land (net of any amortization)", "data_type": "decimal", "default_value": "0", "sort_order": 34},
    {"fact_key": "l_12a_intangibles_eoy", "label": "12a (EOY) — Intangible assets (amortizable only)", "data_type": "decimal", "default_value": "0", "sort_order": 35, "notes": "YELLOW — tts computes from DepreciationAsset."},
    {"fact_key": "l_12b_accum_amort_eoy", "label": "12b (EOY) — Less accumulated amortization", "data_type": "decimal", "default_value": "0", "sort_order": 36, "notes": "Contra. YELLOW — tts computes (BOY accum + current-yr amort − disposed accum)."},
    {"fact_key": "l_13_other_assets_eoy", "label": "13 (EOY) — Other assets", "data_type": "decimal", "default_value": "0", "sort_order": 37},
    {"fact_key": "l_14_total_assets_eoy", "label": "14 (EOY) — Total assets", "data_type": "decimal", "sort_order": 38, "notes": "OUTPUT. = Σ asset lines with contra accounts netted. Feeds the M-3 threshold."},
    # ── Liabilities and Capital — Beginning of year ──
    {"fact_key": "l_15_accounts_payable_boy", "label": "15 (BOY) — Accounts payable", "data_type": "decimal", "default_value": "0", "sort_order": 39},
    {"fact_key": "l_16_mortgages_short_boy", "label": "16 (BOY) — Mortgages, notes, bonds payable in less than 1 year", "data_type": "decimal", "default_value": "0", "sort_order": 40},
    {"fact_key": "l_17_other_current_liab_boy", "label": "17 (BOY) — Other current liabilities", "data_type": "decimal", "default_value": "0", "sort_order": 41},
    {"fact_key": "l_18_nonrecourse_boy", "label": "18 (BOY) — All nonrecourse loans", "data_type": "decimal", "default_value": "0", "sort_order": 42, "notes": "Ties to K-1 item K nonrecourse liabilities (§752)."},
    {"fact_key": "l_19a_loans_from_partners_boy", "label": "19a (BOY) — Loans from partners (or related persons)", "data_type": "decimal", "default_value": "0", "sort_order": 43},
    {"fact_key": "l_19b_mortgages_long_boy", "label": "19b (BOY) — Mortgages, notes, bonds payable in 1 year or more", "data_type": "decimal", "default_value": "0", "sort_order": 44},
    {"fact_key": "l_20_other_liabilities_boy", "label": "20 (BOY) — Other liabilities", "data_type": "decimal", "default_value": "0", "sort_order": 45},
    {"fact_key": "l_21_partners_capital_boy", "label": "21 (BOY) — Partners' capital accounts", "data_type": "decimal", "default_value": "0", "sort_order": 46, "notes": "Tax basis → M-2 line 1 (beginning) = Σ K-1 item L beginning (R-L-21-TIE)."},
    {"fact_key": "l_22_total_liab_capital_boy", "label": "22 (BOY) — Total liabilities and capital", "data_type": "decimal", "sort_order": 47, "notes": "OUTPUT. = Σ lines 15-21."},
    # ── Liabilities and Capital — End of year ──
    {"fact_key": "l_15_accounts_payable_eoy", "label": "15 (EOY) — Accounts payable", "data_type": "decimal", "default_value": "0", "sort_order": 48},
    {"fact_key": "l_16_mortgages_short_eoy", "label": "16 (EOY) — Mortgages, notes, bonds payable in less than 1 year", "data_type": "decimal", "default_value": "0", "sort_order": 49},
    {"fact_key": "l_17_other_current_liab_eoy", "label": "17 (EOY) — Other current liabilities", "data_type": "decimal", "default_value": "0", "sort_order": 50},
    {"fact_key": "l_18_nonrecourse_eoy", "label": "18 (EOY) — All nonrecourse loans", "data_type": "decimal", "default_value": "0", "sort_order": 51, "notes": "Ties to K-1 item K nonrecourse liabilities (§752)."},
    {"fact_key": "l_19a_loans_from_partners_eoy", "label": "19a (EOY) — Loans from partners (or related persons)", "data_type": "decimal", "default_value": "0", "sort_order": 52},
    {"fact_key": "l_19b_mortgages_long_eoy", "label": "19b (EOY) — Mortgages, notes, bonds payable in 1 year or more", "data_type": "decimal", "default_value": "0", "sort_order": 53},
    {"fact_key": "l_20_other_liabilities_eoy", "label": "20 (EOY) — Other liabilities", "data_type": "decimal", "default_value": "0", "sort_order": 54},
    {"fact_key": "l_21_partners_capital_eoy", "label": "21 (EOY) — Partners' capital accounts", "data_type": "decimal", "default_value": "0", "sort_order": 55, "notes": "Tax basis → M-2 line 9 (ending) = Σ K-1 item L ending (R-L-21-TIE)."},
    {"fact_key": "l_22_total_liab_capital_eoy", "label": "22 (EOY) — Total liabilities and capital", "data_type": "decimal", "sort_order": 56, "notes": "OUTPUT. = Σ lines 15-21."},
    # ── Cross-refs + gating ──
    {"fact_key": "m2_9_ending_capital", "label": "Schedule M-2 line 9 ending capital (for the L21 tie)", "data_type": "decimal", "default_value": "0", "sort_order": 60, "notes": "Cross-ref from 1065_M2 for R-L-21-TIE."},
    {"fact_key": "m2_1_beginning_capital", "label": "Schedule M-2 line 1 beginning capital (for the L21 BOY tie)", "data_type": "decimal", "default_value": "0", "sort_order": 61, "notes": "Cross-ref from 1065_M2 for R-L-21-TIE."},
    {"fact_key": "m_schb_q4_small", "label": "Schedule B Q4 — small-partnership exemption met? (suppresses L)", "data_type": "boolean", "default_value": "false", "sort_order": 62, "notes": "Receipts < $250k AND assets < $1M AND timely K-1s AND not-M-3. If true, Schedule L not required (D_L_EXEMPT)."},
]

L_RULES: list[dict] = [
    {"rule_id": "R-L-14", "title": "Line 14 total assets = Σ asset lines (contra accounts netted)",
     "rule_type": "calculation", "precedence": 1, "sort_order": 1,
     "formula": ("14 = line 1 + (2a − 2b) + 3 + 4 + 5 + 6 + 7a + 7b + 8 + (9a − 9b) + (10a − 10b) + 11 + "
                 "(12a − 12b) + 13 — computed for BOTH the beginning (col b) and end-of-year (col d) "
                 "columns. Contra accounts (2b allowance, 9b accum. depreciation, 10b accum. depletion, "
                 "12b accum. amortization) are subtracted from their gross line."),
     "inputs": ["l_1_cash_boy", "l_2a_receivables_boy", "l_2b_allowance_boy", "l_3_inventories_boy",
                "l_4_us_govt_boy", "l_5_tax_exempt_sec_boy", "l_6_other_current_boy", "l_7a_loans_partners_boy",
                "l_7b_mortgage_re_loans_boy", "l_8_other_investments_boy", "l_9a_buildings_boy",
                "l_9b_accum_depr_boy", "l_10a_depletable_boy", "l_10b_accum_depletion_boy", "l_11_land_boy",
                "l_12a_intangibles_boy", "l_12b_accum_amort_boy", "l_13_other_assets_boy"],
     "outputs": ["l_14_total_assets_boy", "l_14_total_assets_eoy"],
     "description": "f1065 Schedule L line 14. tts L15 = the same net sum."},
    {"rule_id": "R-L-22", "title": "Line 22 total liabilities and capital = Σ lines 15-21",
     "rule_type": "calculation", "precedence": 2, "sort_order": 2,
     "formula": ("22 = line 15 + 16 + 17 + 18 + 19a + 19b + 20 + 21 — computed for both the beginning "
                 "(col b) and end-of-year (col d) columns."),
     "inputs": ["l_15_accounts_payable_boy", "l_16_mortgages_short_boy", "l_17_other_current_liab_boy",
                "l_18_nonrecourse_boy", "l_19a_loans_from_partners_boy", "l_19b_mortgages_long_boy",
                "l_20_other_liabilities_boy", "l_21_partners_capital_boy"],
     "outputs": ["l_22_total_liab_capital_boy", "l_22_total_liab_capital_eoy"],
     "description": "f1065 Schedule L line 22. tts L24 = the same sum."},
    {"rule_id": "R-L-BALANCE", "title": "Balance sheet must balance: line 14 = line 22 (both columns)",
     "rule_type": "validation", "precedence": 3, "sort_order": 3,
     "formula": ("Total assets (line 14) must equal total liabilities and capital (line 22) for BOTH the "
                 "beginning and end-of-year columns. ⚠ tts has NO balance check (build-gap #2) — this "
                 "validation + D_L_BALANCE_{BOY,EOY} are new."),
     "inputs": ["l_14_total_assets_boy", "l_14_total_assets_eoy", "l_22_total_liab_capital_boy",
                "l_22_total_liab_capital_eoy"],
     "outputs": [], "description": "Balance-sheet identity. Build-gap in tts."},
    {"rule_id": "R-L-21-TIE", "title": "Line 21 partners' capital ties to Schedule M-2 (tax basis)",
     "rule_type": "validation", "precedence": 4, "sort_order": 4,
     "formula": ("On a tax-basis Schedule L: line 21 partners' capital EOY (col d) = Schedule M-2 line 9 "
                 "(ending capital = Σ K-1 item L ending); line 21 BOY (col b) = Schedule M-2 line 1 "
                 "(beginning = Σ K-1 item L beginning). §705 transactional. ⚠ tts stores L23d (=face 21) "
                 "data-entry and M2_9 computed with NO reconciliation between them (build-gap #5)."),
     "inputs": ["l_21_partners_capital_eoy", "l_21_partners_capital_boy", "m2_9_ending_capital",
                "m2_1_beginning_capital"],
     "outputs": [], "description": "L21 ↔ M-2 tie. Carries the M-2 leg's capital tie home."},
    {"rule_id": "R-L-EXEMPT", "title": "Schedule B Q4 small-partnership exemption suppresses Schedule L",
     "rule_type": "conditional", "precedence": 5, "sort_order": 5,
     "formula": ("If Schedule B Q4 is 'Yes' (total receipts < $250,000 AND total assets < $1,000,000 AND "
                 "Schedules K-1 timely filed/furnished AND not required to file Schedule M-3), the "
                 "partnership is NOT required to complete Schedule L (or item F, or K-1 item L). D_L_EXEMPT "
                 "surfaces the suppression."),
     "inputs": ["m_schb_q4_small"], "outputs": [],
     "description": "i1065 Schedule B Q4. Gating (same fact as M-1/M-2)."},
    {"rule_id": "R-L-M3", "title": "Schedule M-3 threshold — total assets ≥ $10M (Decision F RED-defer)",
     "rule_type": "conditional", "precedence": 6, "sort_order": 6,
     "formula": ("If Schedule L line 14 col (d) total assets ≥ $10,000,000 (or adjusted total assets ≥ "
                 "$10M, or total receipts ≥ $35M, or a reportable-entity-partner owns ≥ 50%), the "
                 "partnership must file Schedule M-3 (Form 1065) in place of M-1. Season-one RED-DEFER "
                 "(Decision F): D_L_M3 FLAGS the threshold; the M-3 schedule itself is not built."),
     "inputs": ["l_14_total_assets_eoy"], "outputs": [],
     "description": "i1065 M-3 who-must-file. Flag only (RED-defer)."},
]

L_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-L-14", "IRS_2025_F1065", "primary", "f1065 Schedule L line 14 = Σ asset lines (contra netted)"),
    ("R-L-22", "IRS_2025_F1065", "primary", "f1065 Schedule L line 22 = Σ lines 15-21"),
    ("R-L-BALANCE", "IRS_2025_I1065", "primary", "i1065 Schedule L — balance sheet must balance (14 = 22)"),
    ("R-L-21-TIE", "IRC_705", "primary", "§705(a)/§722 transactional tax-basis partners' capital"),
    ("R-L-21-TIE", "IRS_2025_I1065", "secondary", "i1065 — line 21 partners' capital = M-2 line 9 (tax basis)"),
    ("R-L-EXEMPT", "IRS_2025_F1065", "primary", "f1065 Schedule B Q4 small-partnership exemption"),
    ("R-L-M3", "IRS_2025_I1065", "primary", "i1065 Schedule M-3 who-must-file threshold (≥$10M / ≥$35M)"),
]

L_LINES: list[dict] = [
    {"line_number": "1", "description": "Cash", "line_type": "input", "sort_order": 1, "source_facts": ["l_1_cash_boy", "l_1_cash_eoy"]},
    {"line_number": "2a", "description": "Trade notes and accounts receivable", "line_type": "input", "sort_order": 2, "source_facts": ["l_2a_receivables_boy", "l_2a_receivables_eoy"]},
    {"line_number": "2b", "description": "Less allowance for bad debts", "line_type": "input", "sort_order": 3, "source_facts": ["l_2b_allowance_boy", "l_2b_allowance_eoy"]},
    {"line_number": "3", "description": "Inventories", "line_type": "input", "sort_order": 4, "source_facts": ["l_3_inventories_boy", "l_3_inventories_eoy"]},
    {"line_number": "4", "description": "U.S. Government obligations", "line_type": "input", "sort_order": 5, "source_facts": ["l_4_us_govt_boy", "l_4_us_govt_eoy"]},
    {"line_number": "5", "description": "Tax-exempt securities", "line_type": "input", "sort_order": 6, "source_facts": ["l_5_tax_exempt_sec_boy", "l_5_tax_exempt_sec_eoy"]},
    {"line_number": "6", "description": "Other current assets (attach statement)", "line_type": "input", "sort_order": 7, "source_facts": ["l_6_other_current_boy", "l_6_other_current_eoy"]},
    {"line_number": "7a", "description": "Loans to partners (or persons related to partners)", "line_type": "input", "sort_order": 8, "source_facts": ["l_7a_loans_partners_boy", "l_7a_loans_partners_eoy"]},
    {"line_number": "7b", "description": "Mortgage and real estate loans", "line_type": "input", "sort_order": 9, "source_facts": ["l_7b_mortgage_re_loans_boy", "l_7b_mortgage_re_loans_eoy"]},
    {"line_number": "8", "description": "Other investments (attach statement)", "line_type": "input", "sort_order": 10, "source_facts": ["l_8_other_investments_boy", "l_8_other_investments_eoy"]},
    {"line_number": "9a", "description": "Buildings and other depreciable assets", "line_type": "input", "sort_order": 11, "source_facts": ["l_9a_buildings_boy", "l_9a_buildings_eoy"]},
    {"line_number": "9b", "description": "Less accumulated depreciation", "line_type": "input", "sort_order": 12, "source_facts": ["l_9b_accum_depr_boy", "l_9b_accum_depr_eoy"], "notes": "tts auto-computes the EOY roll-forward from DepreciationAsset."},
    {"line_number": "10a", "description": "Depletable assets", "line_type": "input", "sort_order": 13, "source_facts": ["l_10a_depletable_boy", "l_10a_depletable_eoy"]},
    {"line_number": "10b", "description": "Less accumulated depletion", "line_type": "input", "sort_order": 14, "source_facts": ["l_10b_accum_depletion_boy", "l_10b_accum_depletion_eoy"]},
    {"line_number": "11", "description": "Land (net of any amortization)", "line_type": "input", "sort_order": 15, "source_facts": ["l_11_land_boy", "l_11_land_eoy"]},
    {"line_number": "12a", "description": "Intangible assets (amortizable only)", "line_type": "input", "sort_order": 16, "source_facts": ["l_12a_intangibles_boy", "l_12a_intangibles_eoy"]},
    {"line_number": "12b", "description": "Less accumulated amortization", "line_type": "input", "sort_order": 17, "source_facts": ["l_12b_accum_amort_boy", "l_12b_accum_amort_eoy"]},
    {"line_number": "13", "description": "Other assets (attach statement)", "line_type": "input", "sort_order": 18, "source_facts": ["l_13_other_assets_boy", "l_13_other_assets_eoy"]},
    {"line_number": "14", "description": "Total assets", "line_type": "total", "sort_order": 19, "source_rules": ["R-L-14"], "notes": "= Σ asset lines (contra netted). Feeds the M-3 threshold."},
    {"line_number": "15", "description": "Accounts payable", "line_type": "input", "sort_order": 20, "source_facts": ["l_15_accounts_payable_boy", "l_15_accounts_payable_eoy"]},
    {"line_number": "16", "description": "Mortgages, notes, bonds payable in less than 1 year", "line_type": "input", "sort_order": 21, "source_facts": ["l_16_mortgages_short_boy", "l_16_mortgages_short_eoy"]},
    {"line_number": "17", "description": "Other current liabilities (attach statement)", "line_type": "input", "sort_order": 22, "source_facts": ["l_17_other_current_liab_boy", "l_17_other_current_liab_eoy"]},
    {"line_number": "18", "description": "All nonrecourse loans", "line_type": "input", "sort_order": 23, "source_facts": ["l_18_nonrecourse_boy", "l_18_nonrecourse_eoy"]},
    {"line_number": "19a", "description": "Loans from partners (or persons related to partners)", "line_type": "input", "sort_order": 24, "source_facts": ["l_19a_loans_from_partners_boy", "l_19a_loans_from_partners_eoy"]},
    {"line_number": "19b", "description": "Mortgages, notes, bonds payable in 1 year or more", "line_type": "input", "sort_order": 25, "source_facts": ["l_19b_mortgages_long_boy", "l_19b_mortgages_long_eoy"]},
    {"line_number": "20", "description": "Other liabilities (attach statement)", "line_type": "input", "sort_order": 26, "source_facts": ["l_20_other_liabilities_boy", "l_20_other_liabilities_eoy"]},
    {"line_number": "21", "description": "Partners' capital accounts", "line_type": "input", "sort_order": 27, "source_facts": ["l_21_partners_capital_boy", "l_21_partners_capital_eoy"], "source_rules": ["R-L-21-TIE"], "destination_form": "1065_M2", "notes": "Tax basis → M-2 line 9 (ending) / line 1 (beginning)."},
    {"line_number": "22", "description": "Total liabilities and capital", "line_type": "total", "sort_order": 28, "source_rules": ["R-L-22", "R-L-BALANCE"], "notes": "= Σ lines 15-21. Must equal line 14."},
]

L_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_L_BALANCE_BOY", "title": "Balance sheet out of balance (beginning of year)", "severity": "error",
     "condition": "l_14_total_assets_boy != l_22_total_liab_capital_boy",
     "message": ("Beginning-of-year Schedule L is out of balance: total assets (line 14) does not equal total "
                 "liabilities and capital (line 22). Verify the balance sheet. NOTE: tts does not yet "
                 "implement a balance check — this is a new studio validation."),
     "notes": "Backs R-L-BALANCE / RECON-L-BALANCE. Build-gap in tts."},
    {"diagnostic_id": "D_L_BALANCE_EOY", "title": "Balance sheet out of balance (end of year)", "severity": "error",
     "condition": "l_14_total_assets_eoy != l_22_total_liab_capital_eoy",
     "message": ("End-of-year Schedule L is out of balance: total assets (line 14) does not equal total "
                 "liabilities and capital (line 22). Verify the balance sheet."),
     "notes": "Backs R-L-BALANCE. Build-gap in tts."},
    {"diagnostic_id": "D_L_21_M2_TIE", "title": "Line 21 partners' capital (EOY) should equal Schedule M-2 line 9", "severity": "warning",
     "condition": "l_21_partners_capital_eoy != m2_9_ending_capital",
     "message": ("On a tax-basis Schedule L, line 21 partners' capital (end of year) should equal Schedule "
                 "M-2 line 9 (ending capital = Σ K-1 item L ending). tts stores these separately with no "
                 "reconciliation — verify the tie manually. If Schedule L is book-basis and differs, attach "
                 "a reconciliation."),
     "notes": "Carries the M-2 leg's capital tie home. Build-gap #5."},
    {"diagnostic_id": "D_L_EXEMPT", "title": "Small-partnership exemption — Schedule L not required", "severity": "info",
     "condition": "m_schb_q4_small is True",
     "message": ("Schedule B question 4 is answered 'Yes' (receipts < $250,000, assets < $1,000,000, timely "
                 "K-1s, not M-3): the partnership is not required to complete Schedule L (or item F, or K-1 "
                 "item L). Any entries here are optional."),
     "notes": "i1065 Q4 gating."},
    {"diagnostic_id": "D_L_M3", "title": "Schedule M-3 threshold met — M-1 replaced by M-3 (RED-deferred)", "severity": "warning",
     "condition": "l_14_total_assets_eoy >= 10000000",
     "message": ("Total assets (line 14, end of year) are $10 million or more — the partnership must file "
                 "Schedule M-3 (Form 1065) in place of Schedule M-1 (also triggered by adjusted total "
                 "assets ≥ $10M, total receipts ≥ $35M, or a ≥50% reportable-entity-partner). Schedule M-3 "
                 "is RED-DEFERRED for season one (Decision F) — flagged, not built."),
     "notes": "i1065 M-3 who-must-file. Decision F RED-defer flag."},
]

L_SCENARIOS: list[dict] = [
    {"scenario_name": "L-1 — balanced sheet (14 = 22, both columns)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"l_1_cash_boy": 50000, "l_9a_buildings_boy": 300000, "l_9b_accum_depr_boy": 100000,
                "l_11_land_boy": 100000,
                "l_1_cash_eoy": 80000, "l_9a_buildings_eoy": 300000, "l_9b_accum_depr_eoy": 130000,
                "l_11_land_eoy": 100000,
                "l_16_mortgages_short_boy": 50000, "l_19b_mortgages_long_boy": 100000, "l_21_partners_capital_boy": 200000,
                "l_16_mortgages_short_eoy": 40000, "l_19b_mortgages_long_eoy": 80000, "l_21_partners_capital_eoy": 230000},
     "expected_outputs": {"l_14_total_assets_boy": 350000, "l_22_total_liab_capital_boy": 350000,
                          "l_14_total_assets_eoy": 350000, "l_22_total_liab_capital_eoy": 350000},
     "notes": "BOY assets = 50k + (300k−100k) + 100k = 350k; liab&cap = 50k+100k+200k = 350k. EOY assets = "
              "80k + (300k−130k) + 100k = 350k; liab&cap = 40k+80k+230k = 350k. Balances both columns."},
    {"scenario_name": "L-2 — out of balance (EOY)", "scenario_type": "failure", "sort_order": 2,
     "inputs": {"l_1_cash_eoy": 500000, "l_16_mortgages_short_eoy": 100000, "l_21_partners_capital_eoy": 390000},
     "expected_outputs": {"l_14_total_assets_eoy": 500000, "l_22_total_liab_capital_eoy": 490000,
                          "D_L_BALANCE_EOY": True},
     "notes": "Assets 500k vs liab&cap 490k → out of balance → D_L_BALANCE_EOY fires (error)."},
    {"scenario_name": "L-3 — line 21 ties to M-2 line 9", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"l_21_partners_capital_eoy": 728000, "m2_9_ending_capital": 728000,
                "l_21_partners_capital_boy": 500000, "m2_1_beginning_capital": 500000},
     "expected_outputs": {"D_L_21_M2_TIE": False},
     "notes": "L21 EOY 728k = M-2 line 9 728k (from the M2-1 scenario); no tie diagnostic."},
    {"scenario_name": "L-4 — small-partnership exemption (Q4) → not required", "scenario_type": "edge", "sort_order": 4,
     "inputs": {"m_schb_q4_small": True, "l_1_cash_eoy": 40000},
     "expected_outputs": {"D_L_EXEMPT": True},
     "notes": "Q4 met → D_L_EXEMPT (info); Schedule L optional."},
    {"scenario_name": "L-5 — Schedule M-3 threshold (assets ≥ $10M)", "scenario_type": "edge", "sort_order": 5,
     "inputs": {"l_14_total_assets_eoy": 12000000, "l_22_total_liab_capital_eoy": 12000000,
                "l_1_cash_eoy": 12000000, "l_21_partners_capital_eoy": 12000000},
     "expected_outputs": {"D_L_M3": True},
     "notes": "Total assets $12M ≥ $10M → D_L_M3 (M-3 required; RED-deferred, flag only)."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 2: 1065_B — Schedule B (Other Information; 33 Yes/No/data questions)
# ═══════════════════════════════════════════════════════════════════════════

B_IDENTITY = {
    "form_number": "1065_B",
    "entity_types": ["1065"],
    "form_title": "Schedule B (Form 1065, 2025) — Other Information",
    "notes": (
        "FRESH-AUTHORED 2026-07-04 (1065-core, form 4) from the FINAL 2025 f1065 pages 2-4 (pymupdf verbatim, "
        "33 questions). The load-bearing computed piece: R-B4-SMALL (Q4 = all four conditions → the "
        "m_schb_q4_small gate that suppresses Schedules L, M-1, M-2, item F, K-1 item L) + R-B24-8990 (Q24 "
        "§163(j) $31M / §448(c) test → attach Form 8990). Q10 §754 election → §743(b)/§734(b) optional "
        "basis adjustments flagged, MATH RED-deferred (Decision E, D_B10_754). Q33 §6221(b) audit election "
        "out → Sch B-2 / else PR designation (R-B33-PR). ⚠ RECONCILE: tts seeds only 18 condensed questions "
        "(B1-B18; B6=Q4 exemption, B16=Q24 §163(j)) as data-entry booleans with NO gating logic — the Q4 "
        "gate and the $31M/M-3 thresholds are build-gaps (findings #3, #4, #6). Authored to the FULL 33-Q "
        "face (authority). READY_TO_SEED=False."
    ),
}

B_FACTS: list[dict] = [
    {"fact_key": "b1_entity_type", "label": "1 — Entity type filing this return", "data_type": "choice", "sort_order": 1,
     "choices": ["domestic_general_partnership", "domestic_limited_partnership", "domestic_llc",
                 "domestic_llp", "foreign_partnership", "other"],
     "notes": "1a general / 1b limited / 1c LLC / 1d LLP / 1e foreign / 1f other."},
    {"fact_key": "b2a_50pct_entity_owner", "label": "2a — Corp/partnership/trust/exempt/foreign-gov owns ≥50%? (→ Sch B-1)", "data_type": "boolean", "default_value": "false", "sort_order": 2},
    {"fact_key": "b2b_50pct_individual_owner", "label": "2b — Individual or estate owns ≥50%? (→ Sch B-1)", "data_type": "boolean", "default_value": "false", "sort_order": 3},
    {"fact_key": "b3a_owns_corp_stock", "label": "3a — Owns ≥20%/50% of a corporation's voting stock?", "data_type": "boolean", "default_value": "false", "sort_order": 4},
    {"fact_key": "b3b_owns_partnership_interest", "label": "3b — Owns ≥20%/50% interest in a partnership/trust?", "data_type": "boolean", "default_value": "false", "sort_order": 5},
    # ── Q4 — the small-partnership exemption (the load-bearing gate) ──
    {"fact_key": "b4a_receipts_under_250k", "label": "4a — Total receipts for the year < $250,000?", "data_type": "boolean", "default_value": "false", "sort_order": 6},
    {"fact_key": "b4b_assets_under_1m", "label": "4b — Total assets at end of year < $1 million?", "data_type": "boolean", "default_value": "false", "sort_order": 7},
    {"fact_key": "b4c_k1s_timely", "label": "4c — Schedules K-1 filed & furnished timely?", "data_type": "boolean", "default_value": "false", "sort_order": 8},
    {"fact_key": "b4d_not_m3", "label": "4d — Not filing and not required to file Schedule M-3?", "data_type": "boolean", "default_value": "false", "sort_order": 9},
    {"fact_key": "b4_small_partnership", "label": "4 — Small-partnership exemption met (all four a-d)?", "data_type": "boolean", "sort_order": 10,
     "notes": "OUTPUT = a AND b AND c AND d. Feeds m_schb_q4_small → suppresses L/M-1/M-2/item F/K-1 item L."},
    {"fact_key": "b5_ptp", "label": "5 — Publicly traded partnership (§469(k)(2))?", "data_type": "boolean", "default_value": "false", "sort_order": 11},
    {"fact_key": "b6_debt_canceled", "label": "6 — Any debt canceled, forgiven, or terms modified to reduce principal?", "data_type": "boolean", "default_value": "false", "sort_order": 12},
    {"fact_key": "b7_form_8918", "label": "7 — Filed/required to file Form 8918 (Material Advisor Disclosure)?", "data_type": "boolean", "default_value": "false", "sort_order": 13},
    {"fact_key": "b8_foreign_account", "label": "8 — Interest/authority over a foreign financial account (FBAR/FinCEN 114)?", "data_type": "boolean", "default_value": "false", "sort_order": 14},
    {"fact_key": "b8_foreign_country", "label": "8 — Name of the foreign country (if Yes)", "data_type": "string", "sort_order": 15},
    {"fact_key": "b9_foreign_trust", "label": "9 — Distribution from / grantor of / transferor to a foreign trust (Form 3520)?", "data_type": "boolean", "default_value": "false", "sort_order": 16},
    # ── Q10 — §754 election + §743(b)/§734(b) basis adjustments (Decision E RED-defer math) ──
    {"fact_key": "b10a_section_754", "label": "10a — §754 election in effect (making or previously made)?", "data_type": "boolean", "default_value": "false", "sort_order": 17},
    {"fact_key": "b10a_754_effective_date", "label": "10a — §754 election effective date (if Yes)", "data_type": "date", "sort_order": 18},
    {"fact_key": "b10b_743b_adj", "label": "10b — Optional basis adjustment under §743(b) (transfers)?", "data_type": "boolean", "default_value": "false", "sort_order": 19, "notes": "Enter net positive / net negative amounts. Basis-adjust MATH RED-deferred (Decision E)."},
    {"fact_key": "b10c_734b_adj", "label": "10c — Optional basis adjustment under §734(b) (distributions)?", "data_type": "boolean", "default_value": "false", "sort_order": 20, "notes": "Basis-adjust MATH RED-deferred (Decision E)."},
    {"fact_key": "b10d_substantial_builtin_loss", "label": "10d — Mandatory basis adjustment (substantial built-in loss §743(d) / basis reduction §734(d))?", "data_type": "boolean", "default_value": "false", "sort_order": 21},
    {"fact_key": "b11_likekind_property", "label": "11 — Distributed/contributed property received in a like-kind exchange?", "data_type": "boolean", "default_value": "false", "sort_order": 22},
    {"fact_key": "b12_tenancy_in_common", "label": "12 — Distributed a tenancy-in-common or other undivided interest in partnership property?", "data_type": "boolean", "default_value": "false", "sort_order": 23},
    {"fact_key": "b13a_form_8858_count", "label": "13a — Number of Forms 8858 attached (FDEs/FBs)", "data_type": "integer", "default_value": "0", "sort_order": 24},
    {"fact_key": "b14_foreign_partners", "label": "14 — Any foreign partners? (→ number of Forms 8805, §1446 withholding)", "data_type": "boolean", "default_value": "false", "sort_order": 25},
    {"fact_key": "b14_form_8805_count", "label": "14 — Number of Forms 8805 filed (if Yes)", "data_type": "integer", "default_value": "0", "sort_order": 26},
    {"fact_key": "b15_form_8865_count", "label": "15 — Number of Forms 8865 attached", "data_type": "integer", "default_value": "0", "sort_order": 27},
    {"fact_key": "b16a_1099_required", "label": "16a — Made payments in 2025 requiring Form(s) 1099?", "data_type": "boolean", "default_value": "false", "sort_order": 28},
    {"fact_key": "b16b_1099_filed", "label": "16b — Did/will you file the required Form(s) 1099?", "data_type": "boolean", "default_value": "false", "sort_order": 29},
    {"fact_key": "b17_form_5471_count", "label": "17 — Number of Forms 5471 attached", "data_type": "integer", "default_value": "0", "sort_order": 30},
    {"fact_key": "b18_foreign_govt_partners", "label": "18 — Number of partners that are foreign governments (§892)", "data_type": "integer", "default_value": "0", "sort_order": 31},
    {"fact_key": "b19_foreign_partner_payments", "label": "19 — Payments to/from foreign partners requiring Forms 1042/1042-S (ch.3/ch.4)?", "data_type": "boolean", "default_value": "false", "sort_order": 32},
    {"fact_key": "b20_form_8938", "label": "20 — Specified domestic entity required to file Form 8938?", "data_type": "boolean", "default_value": "false", "sort_order": 33},
    {"fact_key": "b21_section_721c", "label": "21 — A §721(c) partnership (Reg 1.721(c)-1(b)(14))?", "data_type": "boolean", "default_value": "false", "sort_order": 34},
    {"fact_key": "b22_section_267a", "label": "22 — Paid/accrued interest or royalty with a §267A disallowed deduction?", "data_type": "boolean", "default_value": "false", "sort_order": 35},
    {"fact_key": "b22_267a_amount", "label": "22 — Total disallowed §267A deductions (if Yes)", "data_type": "decimal", "default_value": "0", "sort_order": 36},
    {"fact_key": "b23_section_163j_election", "label": "23 — §163(j) election for a real property trade or business / farming business in effect?", "data_type": "boolean", "default_value": "false", "sort_order": 37},
    # ── Q24 — the §163(j) / Form 8990 test (the second computed gate) ──
    {"fact_key": "b24a_passthrough_ebie", "label": "24a — Owns a pass-through with current/carryover excess business interest expense?", "data_type": "boolean", "default_value": "false", "sort_order": 38},
    {"fact_key": "b24b_receipts_over_31m", "label": "24b — 3-yr avg annual gross receipts (§448(c)) > $31M AND has business interest expense?", "data_type": "boolean", "default_value": "false", "sort_order": 39},
    {"fact_key": "b24c_tax_shelter", "label": "24c — A tax shelter with business interest expense?", "data_type": "boolean", "default_value": "false", "sort_order": 40},
    {"fact_key": "b24_form_8990_required", "label": "24 — Form 8990 required (any of 24a/24b/24c)?", "data_type": "boolean", "sort_order": 41,
     "notes": "OUTPUT = a OR b OR c → §163(j) applies → attach Form 8990."},
    {"fact_key": "b25_qof_self_certify", "label": "25 — Intends to self-certify as a qualified opportunity fund (Form 8996)?", "data_type": "boolean", "default_value": "false", "sort_order": 42},
    {"fact_key": "b26_section_864c8_count", "label": "26 — Number of foreign partners subject to §864(c)(8) (→ Sch K-3 Part XIII)", "data_type": "integer", "default_value": "0", "sort_order": 43},
    {"fact_key": "b27_section_707_8_transfers", "label": "27 — Transfers between partnership and partners subject to Reg 1.707-8 disclosure?", "data_type": "boolean", "default_value": "false", "sort_order": 44},
    {"fact_key": "b28_section_7874", "label": "28 — §7874 foreign-corp acquisition (since 12/22/2017) with ownership >50%?", "data_type": "boolean", "default_value": "false", "sort_order": 45},
    {"fact_key": "b29a_form_7208_foreign", "label": "29a — Required to file Form 7208 (stock-repurchase excise, foreign corp rules)?", "data_type": "boolean", "default_value": "false", "sort_order": 46},
    {"fact_key": "b29b_form_7208_surrogate", "label": "29b — Required to file Form 7208 (covered surrogate foreign corp rules)?", "data_type": "boolean", "default_value": "false", "sort_order": 47},
    {"fact_key": "b30_digital_asset", "label": "30 — Received or disposed of a digital asset (or financial interest in one)?", "data_type": "boolean", "default_value": "false", "sort_order": 48, "notes": "Required question — must be answered Yes/No."},
    # Q31 reserved for future use — omitted (no fact).
    {"fact_key": "b32_section_761_election", "label": "32 — Electing out of subchapter K under §761?", "data_type": "boolean", "default_value": "false", "sort_order": 49},
    {"fact_key": "b33_section_6221b_election", "label": "33 — Electing out of the centralized audit regime (§6221(b))?", "data_type": "boolean", "default_value": "false", "sort_order": 50,
     "notes": "If Yes → complete Schedule B-2. If No → complete the Partnership Representative designation."},
    {"fact_key": "b33_pr_designated", "label": "33 — Partnership Representative designation completed (if not electing out)?", "data_type": "boolean", "default_value": "false", "sort_order": 51},
]

B_RULES: list[dict] = [
    {"rule_id": "R-B4-SMALL", "title": "Q4 small-partnership exemption = all four conditions (the gate)",
     "rule_type": "calculation", "precedence": 1, "sort_order": 1,
     "formula": ("Q4 'Yes' (b4_small_partnership) = 4a (total receipts < $250,000) AND 4b (total assets at "
                 "end of year < $1,000,000) AND 4c (Schedules K-1 filed & furnished timely) AND 4d (not "
                 "filing and not required to file Schedule M-3). When 'Yes,' the partnership is NOT required "
                 "to complete Schedules L, M-1, M-2, item F, or K-1 item L — this drives the "
                 "m_schb_q4_small gate on 1065_L / 1065_M1 / 1065_M2. tts: build-gap #3 CLOSED — B6 (=Q4) "
                 "is auto-answered per R-B4-AUTO (derived/YELLOW, overridable) and the 'Yes' gate is live "
                 "(D_L_EXEMPT / D_M1_EXEMPT / D_M2_EXEMPT suppress the L/M-1/M-2 checks; GATE-SMALL-PTNR "
                 "pins it)."),
     "inputs": ["b4a_receipts_under_250k", "b4b_assets_under_1m", "b4c_k1s_timely", "b4d_not_m3"],
     "outputs": ["b4_small_partnership"],
     "description": "f1065 Schedule B Q4. THE load-bearing gate (feeds L/M-1/M-2)."},
    {"rule_id": "R-B4-AUTO", "title": "Q4 auto-answer — derive the four conditions from return data (YELLOW, overridable)",
     "rule_type": "calculation", "precedence": 1, "sort_order": 6,
     "formula": ("The app DERIVES Q4 as a preparer-overridable default (derived/YELLOW; a typed answer sets "
                 "the override flag, always wins, and is never recomputed over — the 1120S_SCHB R006 "
                 "recipe; Ken ruling 2026-07-09, extended to the 1065 per the s71 ratified queue). "
                 "4a — 'Total receipts' per i1065 (2025) Question 4 VERBATIM: the sum of gross receipts or "
                 "sales (page 1, line 1a); all other income (page 1, lines 4 through 7); income reported on "
                 "Schedule K, lines 3a, 5, 6a, and 7; income or net gain reported on Schedule K, lines 8, "
                 "9a, 10, and 11; and income or net gain reported on Form 8825, lines 2, 21, and 22a. "
                 "Components are read POSITIVE-ONLY (loss components excluded — the interpretive "
                 "'income'/'income or net gain' reading, mirroring 1120S_SCHB R006); 4a = receipts "
                 "< $250,000 STRICT (exactly $250,000 fails). "
                 "4b — 'Total assets' per i1065 Q4 = the amount that would be reported in item F = "
                 "Schedule L line 14 column (d) (app key L15d); 4b = assets < $1,000,000 STRICT. "
                 "4c — PRESUMED TRUE (Ken-ratified practitioner-conduct presumption: the app cannot "
                 "observe filing/furnishing dates; the preparer override is the escape hatch). "
                 "4d — derived TRUE when 4a AND 4b hold: the app prepares no Schedule M-3, and the i1065 "
                 "item J M-3 requirements (Sch L assets ≥ $10M / adjusted total assets ≥ $10M / total "
                 "receipts ≥ $35M) are unreachable when receipts < $250K and assets < $1M. The "
                 "reportable-entity-partner prong (a ≥50% reportable entity partner forces M-3 regardless "
                 "of size) is NOT capturable from return data — documented edge; such a partnership "
                 "answers 'No' by preparer override."),
     "inputs": [],
     "outputs": ["b4a_receipts_under_250k", "b4b_assets_under_1m", "b4c_k1s_timely", "b4d_not_m3"],
     "description": "f1065 Schedule B Q4 auto-answer (S-21c): derive 4a-4d from return data; feeds R-B4-SMALL."},
    {"rule_id": "R-B24-8990", "title": "Q24 §163(j) test → Form 8990 required = any of 24a/24b/24c",
     "rule_type": "calculation", "precedence": 2, "sort_order": 2,
     "formula": ("Q24 'Yes' (b24_form_8990_required) = 24a (owns a pass-through with current or carryover "
                 "excess business interest expense) OR 24b (3-yr average annual gross receipts under "
                 "§448(c) > $31 million AND has business interest expense) OR 24c (a tax shelter with "
                 "business interest expense). If 'Yes' to any, §163(j) applies and Form 8990 must be "
                 "attached. The $31M is the §448(c)(1) $25M base inflation-adjusted for TY2025. ⚠ tts "
                 "stores B16 (=Q24) with no $31M threshold logic (build-gap #4)."),
     "inputs": ["b24a_passthrough_ebie", "b24b_receipts_over_31m", "b24c_tax_shelter"],
     "outputs": ["b24_form_8990_required"],
     "description": "f1065 Schedule B Q24. §163(j)/§448(c) $31M → Form 8990."},
    {"rule_id": "R-B10-754", "title": "Q10 §754 election → §743(b)/§734(b) basis adjustments (MATH RED-deferred)",
     "rule_type": "conditional", "precedence": 3, "sort_order": 3,
     "formula": ("If Q10a is 'Yes' (a §754 election is in effect), the partnership adjusts the basis of "
                 "partnership property under §743(b) on transfers of a partnership interest (Q10b) and "
                 "§734(b) on distributions (Q10c); a mandatory adjustment also applies for a substantial "
                 "built-in loss / basis reduction (Q10d, §743(d)/§734(d)). D_B10_754 flags the election. "
                 "SCOPE (Decision E): the basis-adjustment COMPUTATION is RED-DEFERRED for season one — "
                 "the election + amounts are captured and flagged; the §743(b)/§734(b) allocation math is "
                 "a future leg."),
     "inputs": ["b10a_section_754", "b10b_743b_adj", "b10c_734b_adj", "b10d_substantial_builtin_loss"],
     "outputs": [], "description": "f1065 Schedule B Q10. §754 flag; basis-adjust math RED-deferred."},
    {"rule_id": "R-B33-PR", "title": "Q33 §6221(b) election out → Sch B-2; else PR designation required",
     "rule_type": "conditional", "precedence": 4, "sort_order": 4,
     "formula": ("If Q33 is 'Yes' (electing out of the BBA centralized partnership audit regime under "
                 "§6221(b) — available only to partnerships furnishing ≤100 K-1s with all eligible "
                 "partners), the partnership must complete Schedule B-2 (Form 1065). If 'No,' the "
                 "Designation of Partnership Representative block MUST be completed (a PR is mandatory for "
                 "every BBA partnership). D_B33_PR surfaces the required action."),
     "inputs": ["b33_section_6221b_election", "b33_pr_designated"], "outputs": [],
     "description": "f1065 Schedule B Q33. §6221(b) election out / PR designation."},
    {"rule_id": "R-B30-DIGITAL", "title": "Q30 digital-asset question must be answered",
     "rule_type": "validation", "precedence": 5, "sort_order": 5,
     "formula": ("The Q30 digital-asset question (received as reward/award/payment, or sold/exchanged/"
                 "disposed of a digital asset or financial interest in one) is a REQUIRED question and must "
                 "be answered Yes or No on every Form 1065."),
     "inputs": ["b30_digital_asset"], "outputs": [],
     "description": "f1065 Schedule B Q30. Required digital-asset question."},
]

B_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-B4-SMALL", "IRS_2025_F1065", "primary", "f1065 Schedule B Q4 four-condition small-partnership exemption"),
    ("R-B4-SMALL", "IRS_2025_I1065", "secondary", "i1065 Q4 — suppresses L/M-1/M-2/item F/K-1 item L"),
    ("R-B4-AUTO", "IRS_2025_I1065", "primary", "i1065 Q4 verbatim total-receipts definition (p1 1a; p1 4-7; K 3a/5/6a/7; K 8/9a/10/11 net-gain; 8825 2/21/22a) + total assets = the item F amount"),
    ("R-B4-AUTO", "IRS_2025_F1065", "secondary", "f1065 Schedule B Q4 four conditions + the item-F waiver on 'Yes'"),
    ("R-B24-8990", "IRS_2025_F1065", "primary", "f1065 Schedule B Q24 §163(j) test → Form 8990"),
    ("R-B24-8990", "IRC_448C", "secondary", "§448(c) $25M base → $31M inflation-adjusted (2025)"),
    ("R-B10-754", "IRS_2025_F1065", "primary", "f1065 Schedule B Q10 §754 / §743(b) / §734(b)"),
    ("R-B10-754", "IRC_754", "secondary", "§754 election → §734/§743 optional basis adjustments"),
    ("R-B33-PR", "IRS_2025_F1065", "primary", "f1065 Schedule B Q33 §6221(b) election out / PR designation"),
    ("R-B33-PR", "IRC_6221", "secondary", "§6221(a) partnership-level / §6221(b) election out (≤100 K-1s)"),
    ("R-B30-DIGITAL", "IRS_2025_F1065", "primary", "f1065 Schedule B Q30 digital-asset question"),
]

B_LINES: list[dict] = [
    {"line_number": "1", "description": "Type of entity filing this return", "line_type": "input", "sort_order": 1, "source_facts": ["b1_entity_type"]},
    {"line_number": "2", "description": "50%-or-more owners (→ Schedule B-1)", "line_type": "input", "sort_order": 2, "source_facts": ["b2a_50pct_entity_owner", "b2b_50pct_individual_owner"]},
    {"line_number": "3", "description": "Partnership's ownership of corporations / partnerships", "line_type": "input", "sort_order": 3, "source_facts": ["b3a_owns_corp_stock", "b3b_owns_partnership_interest"]},
    {"line_number": "4", "description": "Small-partnership exemption (all four conditions)", "line_type": "calculated", "sort_order": 4, "source_facts": ["b4_small_partnership"], "source_rules": ["R-B4-SMALL", "R-B4-AUTO"], "notes": "→ suppresses Schedules L, M-1, M-2, item F, K-1 item L. Auto-answered from return data (R-B4-AUTO, YELLOW/overridable)."},
    {"line_number": "5", "description": "Publicly traded partnership (§469(k)(2))", "line_type": "input", "sort_order": 5, "source_facts": ["b5_ptp"]},
    {"line_number": "6", "description": "Debt canceled/forgiven/modified", "line_type": "input", "sort_order": 6, "source_facts": ["b6_debt_canceled"]},
    {"line_number": "7", "description": "Form 8918 (Material Advisor Disclosure)", "line_type": "input", "sort_order": 7, "source_facts": ["b7_form_8918"]},
    {"line_number": "8", "description": "Foreign financial account (FBAR/FinCEN 114)", "line_type": "input", "sort_order": 8, "source_facts": ["b8_foreign_account", "b8_foreign_country"]},
    {"line_number": "9", "description": "Foreign trust distribution/grantor/transferor (Form 3520)", "line_type": "input", "sort_order": 9, "source_facts": ["b9_foreign_trust"]},
    {"line_number": "10", "description": "§754 election / §743(b) / §734(b) basis adjustments", "line_type": "input", "sort_order": 10, "source_facts": ["b10a_section_754", "b10b_743b_adj", "b10c_734b_adj", "b10d_substantial_builtin_loss"], "source_rules": ["R-B10-754"]},
    {"line_number": "11", "description": "Like-kind exchange property distributed/contributed", "line_type": "input", "sort_order": 11, "source_facts": ["b11_likekind_property"]},
    {"line_number": "12", "description": "Tenancy-in-common/undivided interest distributed", "line_type": "input", "sort_order": 12, "source_facts": ["b12_tenancy_in_common"]},
    {"line_number": "13a", "description": "Number of Forms 8858 attached", "line_type": "input", "sort_order": 13, "source_facts": ["b13a_form_8858_count"]},
    {"line_number": "14", "description": "Foreign partners / Forms 8805 (§1446)", "line_type": "input", "sort_order": 14, "source_facts": ["b14_foreign_partners", "b14_form_8805_count"]},
    {"line_number": "15", "description": "Number of Forms 8865 attached", "line_type": "input", "sort_order": 15, "source_facts": ["b15_form_8865_count"]},
    {"line_number": "16", "description": "Payments requiring Form(s) 1099", "line_type": "input", "sort_order": 16, "source_facts": ["b16a_1099_required", "b16b_1099_filed"]},
    {"line_number": "17", "description": "Number of Forms 5471 attached", "line_type": "input", "sort_order": 17, "source_facts": ["b17_form_5471_count"]},
    {"line_number": "18", "description": "Foreign-government partners (§892)", "line_type": "input", "sort_order": 18, "source_facts": ["b18_foreign_govt_partners"]},
    {"line_number": "19", "description": "Payments to/from foreign partners (Forms 1042/1042-S)", "line_type": "input", "sort_order": 19, "source_facts": ["b19_foreign_partner_payments"]},
    {"line_number": "20", "description": "Specified domestic entity (Form 8938)", "line_type": "input", "sort_order": 20, "source_facts": ["b20_form_8938"]},
    {"line_number": "21", "description": "§721(c) partnership", "line_type": "input", "sort_order": 21, "source_facts": ["b21_section_721c"]},
    {"line_number": "22", "description": "§267A disallowed interest/royalty deduction", "line_type": "input", "sort_order": 22, "source_facts": ["b22_section_267a", "b22_267a_amount"]},
    {"line_number": "23", "description": "§163(j) RPTB/farming election in effect", "line_type": "input", "sort_order": 23, "source_facts": ["b23_section_163j_election"]},
    {"line_number": "24", "description": "§163(j) test → Form 8990 (incl. $31M §448(c) gross receipts)", "line_type": "calculated", "sort_order": 24, "source_facts": ["b24_form_8990_required"], "source_rules": ["R-B24-8990"]},
    {"line_number": "25", "description": "Qualified opportunity fund self-certification (Form 8996)", "line_type": "input", "sort_order": 25, "source_facts": ["b25_qof_self_certify"]},
    {"line_number": "26", "description": "Foreign partners subject to §864(c)(8) (→ Sch K-3 Part XIII)", "line_type": "input", "sort_order": 26, "source_facts": ["b26_section_864c8_count"]},
    {"line_number": "27", "description": "Transfers subject to Reg 1.707-8 disclosure", "line_type": "input", "sort_order": 27, "source_facts": ["b27_section_707_8_transfers"]},
    {"line_number": "28", "description": "§7874 foreign-corp acquisition (>50%)", "line_type": "input", "sort_order": 28, "source_facts": ["b28_section_7874"]},
    {"line_number": "29", "description": "Form 7208 excise tax on stock repurchase", "line_type": "input", "sort_order": 29, "source_facts": ["b29a_form_7208_foreign", "b29b_form_7208_surrogate"]},
    {"line_number": "30", "description": "Digital asset received or disposed of", "line_type": "input", "sort_order": 30, "source_facts": ["b30_digital_asset"], "source_rules": ["R-B30-DIGITAL"]},
    {"line_number": "32", "description": "§761 election out of subchapter K", "line_type": "input", "sort_order": 32, "source_facts": ["b32_section_761_election"]},
    {"line_number": "33", "description": "§6221(b) election out of centralized audit regime / PR designation", "line_type": "input", "sort_order": 33, "source_facts": ["b33_section_6221b_election", "b33_pr_designated"], "source_rules": ["R-B33-PR"]},
]

B_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_B4_SMALL", "title": "Small-partnership exemption met — Schedules L/M-1/M-2 not required", "severity": "info",
     "condition": "b4_small_partnership is True",
     "message": ("All four Q4 conditions are met (receipts < $250,000, assets < $1,000,000, timely K-1s, "
                 "not M-3): the partnership is not required to complete Schedules L, M-1, and M-2; item F on "
                 "page 1; or item L on Schedule K-1."),
     "notes": "Drives m_schb_q4_small on 1065_L / 1065_M1 / 1065_M2. tts surfaces: D_L_EXEMPT / D_M1_EXEMPT / D_M2_EXEMPT; B6 auto-answered per R-B4-AUTO (build-gap #3 closed, S-21c)."},
    {"diagnostic_id": "D_B24_8990", "title": "§163(j) applies — Form 8990 required", "severity": "warning",
     "condition": "b24_form_8990_required is True",
     "message": ("The partnership answered 'Yes' to Q24 (owns a pass-through with excess business interest "
                 "expense, OR 3-yr average annual gross receipts > $31 million with business interest "
                 "expense, OR a tax shelter with business interest expense): §163(j) applies — complete and "
                 "attach Form 8990."),
     "notes": "Build-gap #4 (tts has no $31M threshold logic)."},
    {"diagnostic_id": "D_B10_754", "title": "§754 election in effect — basis adjustments apply (math RED-deferred)", "severity": "warning",
     "condition": "b10a_section_754 is True OR b10b_743b_adj is True OR b10c_734b_adj is True OR b10d_substantial_builtin_loss is True",
     "message": ("A §754 election is in effect (or a mandatory basis adjustment applies): the partnership "
                 "adjusts the basis of partnership property under §743(b) (transfers) and/or §734(b) "
                 "(distributions) and must attach a statement showing the computation and allocation of "
                 "each basis adjustment. NOTE: the basis-adjustment computation is RED-deferred for season "
                 "one — the election and amounts are captured; the §743(b)/§734(b) math is a future leg."),
     "notes": "Decision E RED-defer. Ken adjudicates whether to build the basis-adjust math."},
    {"diagnostic_id": "D_B33_PR", "title": "Partnership Representative designation required (if not electing out)", "severity": "error",
     "condition": "b33_section_6221b_election is False AND b33_pr_designated is False",
     "message": ("The partnership is NOT electing out of the centralized audit regime (Q33 'No'), so the "
                 "Designation of Partnership Representative block MUST be completed — a PR is mandatory for "
                 "every BBA partnership. If electing out (Q33 'Yes'), complete Schedule B-2 (Form 1065) "
                 "instead."),
     "notes": "f1065 Q33 / §6221. PR is mandatory unless electing out."},
    {"diagnostic_id": "D_B2_B1", "title": "50%-or-more owner — attach Schedule B-1", "severity": "info",
     "condition": "b2a_50pct_entity_owner is True OR b2b_50pct_individual_owner is True",
     "message": ("A partner owns, directly or indirectly, 50% or more of the profit, loss, or capital of "
                 "the partnership (Q2a or Q2b 'Yes'): attach Schedule B-1 (Information on Partners Owning "
                 "50% or More of the Partnership). Schedule B-1 is RED-deferred (attachment flag only)."),
     "notes": "Decision F — B-1 modeled as an attachment-trigger flag, not a full sub-schedule."},
]

B_SCENARIOS: list[dict] = [
    {"scenario_name": "B-1 — small partnership (all four Q4 conditions met)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"b4a_receipts_under_250k": True, "b4b_assets_under_1m": True, "b4c_k1s_timely": True, "b4d_not_m3": True},
     "expected_outputs": {"b4_small_partnership": True, "D_B4_SMALL": True},
     "notes": "All four → Q4 Yes → suppresses L/M-1/M-2/item F/K-1 item L."},
    {"scenario_name": "B-2 — not exempt (assets $2M fails condition b)", "scenario_type": "edge", "sort_order": 2,
     "inputs": {"b4a_receipts_under_250k": True, "b4b_assets_under_1m": False, "b4c_k1s_timely": True, "b4d_not_m3": True},
     "expected_outputs": {"b4_small_partnership": False},
     "notes": "One condition fails (assets ≥ $1M) → Q4 No → Schedules L/M-1/M-2 required."},
    {"scenario_name": "B-3 — §163(j) applies (receipts > $31M) → Form 8990", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"b24b_receipts_over_31m": True},
     "expected_outputs": {"b24_form_8990_required": True, "D_B24_8990": True},
     "notes": "24b (3-yr avg gross receipts > $31M + business interest) → §163(j) → Form 8990."},
    {"scenario_name": "B-4 — §754 election active → basis-adjustment flag", "scenario_type": "edge", "sort_order": 4,
     "inputs": {"b10a_section_754": True, "b10b_743b_adj": True},
     "expected_outputs": {"D_B10_754": True},
     "notes": "§754 election + §743(b) adjustment → D_B10_754 (basis-adjust math RED-deferred)."},
    {"scenario_name": "B-5 — no audit election-out → PR designation required", "scenario_type": "edge", "sort_order": 5,
     "inputs": {"b33_section_6221b_election": False, "b33_pr_designated": False},
     "expected_outputs": {"D_B33_PR": True},
     "notes": "Not electing out + PR not designated → D_B33_PR (error): PR is mandatory."},
    {"scenario_name": "B-6 — Q4 auto-answer boundary: receipts exactly $250,000 fails 4a", "scenario_type": "edge", "sort_order": 6,
     "inputs": {"b4a_receipts_under_250k": False, "b4b_assets_under_1m": True, "b4c_k1s_timely": True, "b4d_not_m3": True},
     "expected_outputs": {"b4_small_partnership": False},
     "notes": "R-B4-AUTO strict-<: total receipts of exactly $250,000 is NOT < $250,000 → 4a False → Q4 No. "
              "Identical strictness for 4b at exactly $1,000,000. Loss components excluded from the receipts "
              "sum (positive-only)."},
    {"scenario_name": "B-7 — Q4 auto-answer derived Yes ($249,999 / $999,999; 4c presumed, 4d derived)", "scenario_type": "normal", "sort_order": 7,
     "inputs": {"b4a_receipts_under_250k": True, "b4b_assets_under_1m": True, "b4c_k1s_timely": True, "b4d_not_m3": True},
     "expected_outputs": {"b4_small_partnership": True, "D_B4_SMALL": True},
     "notes": "R-B4-AUTO: receipts $249,999 (< $250K) + assets $999,999 (< $1M); 4c PRESUMED TRUE "
              "(Ken-ratified); 4d derived TRUE (no M-3 prepared; item-J thresholds unreachable under 4a·4b; "
              "reportable-entity-partner edge → preparer override). The derived answer is YELLOW/overridable "
              "— a preparer click is never recomputed over."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS (cross-form ties)
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "GATE-SMALL-PTNR-B", "assertion_type": "gating_check", "entity_types": ["1065"],
     "status": "active",
     "title": "Schedule B Q4 (computed) → suppresses Schedules L, M-1, M-2, item F, K-1 item L",
     "description": ("Schedule B Q4 (b4_small_partnership = 4a AND 4b AND 4c AND 4d) is the computed gate: "
                     "when 'Yes' (receipts < $250,000 AND assets < $1,000,000 AND timely K-1s AND "
                     "not-M-3-required), the partnership is not required to complete Schedules L, M-1, M-2, "
                     "item F, or K-1 item L. Feeds the m_schb_q4_small fact on 1065_L / 1065_M1 / 1065_M2. "
                     "tts: B6 (=Q4) is auto-answered from return data (R-B4-AUTO, YELLOW/overridable) and "
                     "the 'Yes' gate suppresses the L/M-1/M-2 checks (D_L_EXEMPT / D_M1_EXEMPT / "
                     "D_M2_EXEMPT)."),
     "definition": {"kind": "gating_check", "form": "1065_B",
                    "formula": "b4_small_partnership == (b4a AND b4b AND b4c AND b4d)",
                    "expect": {"suppresses": ["1065_L", "1065_M1", "1065_M2", "item_F", "k1_item_L"]},
                    "when": "b4_small_partnership is True",
                    "note": "the Q4 four-condition gate; tts B6 auto-answered (R-B4-AUTO) + gated (build-gap #3 closed, S-21c)"},
     "bug_reference": "closed S-21c: tts auto-answers Q4 (B6) and gates L/M-1/M-2 on it", "sort_order": 1},
    {"assertion_id": "RECON-L-BALANCE", "assertion_type": "reconciliation", "entity_types": ["1065"],
     "status": "active",
     "title": "Schedule L must balance: line 14 (total assets) = line 22 (total liab & capital)",
     "description": ("Schedule L line 14 total assets must equal line 22 total liabilities and capital for "
                     "both the beginning and end-of-year columns (the balance-sheet identity). ⚠ tts "
                     "computes L15 (assets) and L24 (liab & capital) but NEVER compares them — no balance "
                     "check, no out-of-balance diagnostic (build-gap). R-L-BALANCE + D_L_BALANCE_{BOY,EOY} "
                     "introduce it."),
     "definition": {"kind": "reconciliation", "form": "1065_L",
                    "formula": "l_14_total_assets_boy == l_22_total_liab_capital_boy; "
                               "l_14_total_assets_eoy == l_22_total_liab_capital_eoy",
                    "note": "tts has no balance check (build-gap #2)"},
     "bug_reference": "tts Schedule L has no L15==L24 balance validation", "sort_order": 2},
    {"assertion_id": "RECON-L21-M2", "assertion_type": "reconciliation", "entity_types": ["1065"],
     "status": "active",
     "title": "Schedule L line 21 partners' capital = Schedule M-2 (tax basis)",
     "description": ("On a tax-basis Schedule L, line 21 partners' capital ties to Schedule M-2: EOY (col d) "
                     "= M-2 line 9 (ending capital = Σ K-1 item L ending); BOY (col b) = M-2 line 1 "
                     "(beginning = Σ K-1 item L beginning). §705 transactional. ⚠ tts stores L23d "
                     "(=face line 21) data-entry and M2_9 computed with NO reconciliation — verify "
                     "manually (build-gap)."),
     "definition": {"kind": "reconciliation", "form": "1065_L",
                    "formula": "l_21_partners_capital_eoy == 1065_M2.m2_9_eoy; "
                               "l_21_partners_capital_boy == 1065_M2.m2_1_boy",
                    "note": "carries the M-2 capital tie home; tts has no L21↔M-2 reconciliation"},
     "bug_reference": "tts L23d (partners' capital) and M2_9 are not reconciled", "sort_order": 3},
    {"assertion_id": "GATE-8990-163J", "assertion_type": "gating_check", "entity_types": ["1065"],
     "status": "active",
     "title": "Schedule B Q24 (computed) → §163(j) applies → Form 8990 required",
     "description": ("Schedule B Q24 (b24_form_8990_required = 24a OR 24b OR 24c) is the computed §163(j) "
                     "gate: a pass-through with excess business interest expense, OR 3-yr average annual "
                     "gross receipts under §448(c) > $31 million with business interest expense, OR a tax "
                     "shelter with business interest expense → §163(j) applies, attach Form 8990. The $31M "
                     "is the §448(c)(1) $25M base inflation-adjusted for TY2025. ⚠ tts stores B16 (=Q24) "
                     "with no $31M threshold logic (build-gap)."),
     "definition": {"kind": "gating_check", "form": "1065_B",
                    "formula": "b24_form_8990_required == (b24a OR b24b OR b24c)",
                    "expect": {"attach": "Form 8990"},
                    "when": "b24_form_8990_required is True",
                    "note": "§448(c) $31M inflation-adjusted; tts has no threshold logic (build-gap #4)"},
     "bug_reference": "tts stores Q24 (B16) but computes no $31M / §163(j) threshold", "sort_order": 4},
]


class Command(BaseCommand):
    help = ("Load the 1065 Schedule L + Schedule B spec (1065_L + 1065_B). Fresh-authored from the FINAL "
            "2025 f1065 page 6 (Schedule L) + pages 2-4 (Schedule B, 33 Qs, pymupdf verbatim) + primary "
            "IRC (§705/§754/§448(c)/§6221). Reconciled against tts compute Schedule L totals + seed_1065 "
            "B1-B18. Refuses until READY_TO_SEED=True (awaits the Ken walk of decisions D/E/F/G per D-1).")

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad 1065 Schedule L + Schedule B (1065_L + 1065_B)\n"))
        self._load_topics()
        sources = self._load_sources()
        l = self._upsert_form(L_IDENTITY)
        l_rules = self._upsert_rules(l, L_RULES)
        self._upsert_facts(l, L_FACTS)
        self._upsert_authority_links(l_rules, sources, L_RULE_LINKS)
        self._upsert_lines(l, L_LINES)
        self._upsert_diagnostics(l, L_DIAGNOSTICS)
        self._upsert_tests(l, L_SCENARIOS)
        b = self._upsert_form(B_IDENTITY)
        b_rules = self._upsert_rules(b, B_RULES)
        self._upsert_facts(b, B_FACTS)
        self._upsert_authority_links(b_rules, sources, B_RULE_LINKS)
        self._upsert_lines(b, B_LINES)
        self._upsert_diagnostics(b, B_DIAGNOSTICS)
        self._upsert_tests(b, B_SCENARIOS)
        self._upsert_form_links(sources)
        self._load_flow_assertions()
        self._report_totals([l, b])

    def _guard_against_hollow_seed(self):
        empty = []
        checks = (
            ("sources", AUTHORITY_SOURCES),
            ("l.facts", L_FACTS), ("l.rules", L_RULES), ("l.lines", L_LINES),
            ("l.diagnostics", L_DIAGNOSTICS), ("l.scenarios", L_SCENARIOS), ("l.rule_links", L_RULE_LINKS),
            ("b.facts", B_FACTS), ("b.rules", B_RULES), ("b.lines", B_LINES),
            ("b.diagnostics", B_DIAGNOSTICS), ("b.scenarios", B_SCENARIOS), ("b.rule_links", B_RULE_LINKS),
            ("flow_assertions", FLOW_ASSERTIONS),
        )
        for name, seq in checks:
            if not seq:
                empty.append(f"1065_l_b.{name}")
        if not READY_TO_SEED or empty:
            still_empty = "\n  ".join(f"- {n}" for n in empty) or "(all populated)"
            raise CommandError(
                "\nREFUSING TO SEED 1065 L/B: not cleared to seed.\n\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True — flip only after the Ken walk of "
                "decisions D/E/F/G, D-1)\n\n"
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
