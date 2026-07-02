"""Load Schedule 1-A (SCH_1A) spec — "Additional Deductions", TY 2025.

Session 16 (2026-06-03): Content authored by transcription from the finalized
2025 Schedule 1-A (f1040s1a.pdf, created 11/4/25) plus the verified IRS/statutory
sources Ken supplied. Every value, line number, threshold, and citation in this
file was transcribed from that supplied content — none was invented or supplied
from model knowledge.

Schedule 1-A implements the OBBBA (P.L. 119-21) below-the-line deductions for
TY 2025–2028:
  Part I   — MAGI (lines 1–3)
  Part II  — Tips           · IRC §224 (OBBBA §70201)   (lines 4–13)
  Part III — Overtime       · IRC §225 (OBBBA §70202)   (lines 14–21)
  Part IV  — Car Loan/QPVLI · IRC §163(h)(4) (OBBBA §70203) (lines 22–30)
  Part V   — Senior         · IRC §151(d)(5) (OBBBA §70103) (lines 31–37)
  Part VI  — Total (line 38 → Form 1040 line 13b / 1040-NR line 13c)

Structurally mirrors `load_1040_ctc.py`: same record types, same helper methods,
same idempotent update_or_create pattern, same RuleAuthorityLink wiring.

Safety guard — STILL ENGAGED
----------------------------
`READY_TO_SEED = False`. The content lists below are populated, but Ken reviews,
flips the sentinel, and seeds himself. Until then the command refuses to write to
the DB (CommandError raised BEFORE any DB operation). This is per the standing
rule: no live-RS-DB writes without Ken's explicit go.

Authoring notes
---------------
- TEST_SCENARIOS (21) were added in Session 17, transcribed verbatim from values
  computed independently from the 2025 Schedule 1-A line math and reviewed by Ken.
  They exist to VALIDATE the rules and are deliberately NOT derived from them.
- Diagnostic severities are Ken's calls. The supplied effect words map to the
  model's {error, warning, info} enum as: BLOCK→error; NOT QUALIFIED(+flag)→warning;
  WARNING→warning. Each diagnostic's notes restate the supplied effect so Ken can
  re-grade.
- Authority excerpts are structured summaries transcribed from the supplied
  content; statute/PL/notice/reg records carry requires_human_review=True pending
  verbatim-text confirmation against the cited source.

POST-SEED CHECK (for Ken, after flipping READY_TO_SEED and loading):
  - lookup/SCH_1A/export/ resolves and returns all six parts.
  - Exported constants match compute_sch_1a.py for Parts I/II/III/V/VI. Part IV is
    intentionally spec-ahead-of-compute (compute stubs line 30 at 0) — not a mismatch.

Idempotent via update_or_create — safe to re-run after edits.

DO NOT relax the safety guard to silence the error.
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
# SAFETY GUARD — flipped to True 2026-06-10 on Ken's in-session approval of
# the review packet (constants, rounding directions, diagnostics severities,
# 21 scenarios, and the five documented v1 deviations).
# ═══════════════════════════════════════════════════════════════════════════

READY_TO_SEED = True


# ═══════════════════════════════════════════════════════════════════════════
# FORM IDENTITY
# ═══════════════════════════════════════════════════════════════════════════

FORM_NUMBER = "SCH_1A"
FORM_TITLE = "Additional Deductions"
FORM_JURISDICTION = "FED"
FORM_ENTITY_TYPES = ["1040"]
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_NOTES = (
    "Schedule 1-A (Form 1040), 'Additional Deductions'. OBBBA (P.L. 119-21) below-the-line "
    "deductions, effective TY 2025–2028. Reduces taxable income (NOT AGI); allowed whether or "
    "not itemizing. Six parts: I MAGI; II Tips (§224); III Overtime (§225); IV Car Loan/QPVLI "
    "(§163(h)(4)); V Senior (§151(d)(5)); VI Total → Form 1040 line 13b. Caps/thresholds stable "
    "2025–2028; only the Part V senior age cutoff rolls by year (_constants_for_year pattern). "
    "Common gates for tips/overtime/senior: valid SSN; MFS ineligible. NOTE: tts-tax-app "
    "currently stubs Part IV (line 30) at 0 — spec leads compute here; expected, not a mismatch."
)

# Existing sources to REUSE (looked up, not modified). New excerpts attach via
# NEW_EXCERPTS_ON_EXISTING below.
EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRC_151",  # §151(d)(5) enhanced senior deduction (Part V)
    "IRC_63",   # §63(b)(7) non-itemizer below-the-line treatment (Part IV / shared)
]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY TOPICS  (organizational tags derived from the supplied part names)
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("additional_deductions", "Additional Deductions (Schedule 1-A)"),
    ("tips_deduction", "Tips Deduction (IRC §224)"),
    ("overtime_deduction", "Overtime Deduction (IRC §225)"),
    ("car_loan_interest_deduction", "Car Loan Interest Deduction / QPVLI (IRC §163(h)(4))"),
    ("senior_deduction", "Senior Deduction (IRC §151(d)(5))"),
    # "obbba" topic already exists (created Session 14) — reused, not recreated.
    ("obbba", "One Big Beautiful Bill Act (P.L. 119-21)"),
]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY SOURCES (with embedded excerpts) — CREATE
# Excerpt text transcribed from the supplied content; statute/PL/notice/reg
# records carry requires_human_review=True pending verbatim confirmation.
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_SOURCES: list[dict] = [
    # ─── 2025 Schedule 1-A form ───
    {
        "source_code": "IRS_2025_SCH_1A_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Schedule 1-A (Form 1040) — Additional Deductions",
        "citation": "Schedule 1-A (Form 1040) (2025); f1040s1a.pdf (created 11/4/25)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f1040s1a.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": "Defines the canonical line numbering and arithmetic for all six parts.",
        "topics": ["additional_deductions"],
        "excerpts": [
            {
                "excerpt_label": "Part I — MAGI (lines 1–3)",
                "location_reference": "Sch 1-A (2025), Part I, lines 1–3",
                "excerpt_text": (
                    "L1 = Form 1040/1040-SR/1040-NR line 11b (AGI). L2a = excluded Puerto Rico income; "
                    "L2b = Form 2555 line 45; L2c = Form 2555 line 50; L2d = Form 4563 line 15. "
                    "L2e = L2a+L2b+L2c+L2d. L3 = L1 + L2e = MAGI."
                ),
                "summary_text": "Part I assembles MAGI = AGI + §911/§931/§933 add-backs.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part II — Tips (lines 4–13)",
                "location_reference": "Sch 1-A (2025), Part II, lines 4–13",
                "excerpt_text": (
                    "L4a W-2 box 7 qualified tips; L4b Form 4137 line 1; L4c = larger of L4a/L4b "
                    "(single employer); L5 trade/business tips; L6 = L4c+L5; L7 = min(L6, $25,000); "
                    "L8 = L3; L9 = $150,000 ($300,000 MFJ); L10 = L8−L9; L11 = floor(L10/1000); "
                    "L12 = L11×$100; L13 = max(0, L7−L12) = tips deduction."
                ),
                "summary_text": "Part II tips: cap $25,000 then phaseout (round DOWN ×$100).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part III — Overtime (lines 14–21)",
                "location_reference": "Sch 1-A (2025), Part III, lines 14–21",
                "excerpt_text": (
                    "L14a W-2 box 1 qualified OT; L14b 1099-NEC box1 / 1099-MISC box3; L14c = sum; "
                    "L15 = min(L14c, $12,500 single / $25,000 MFJ); L16 = L3; L17 = $150,000 "
                    "($300,000 MFJ); L18 = L16−L17; L19 = floor(L18/1000); L20 = L19×$100; "
                    "L21 = max(0, L15−L20) = overtime deduction."
                ),
                "summary_text": "Part III overtime: cap $12,500/$25,000 then phaseout (round DOWN ×$100).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part IV — Car Loan / QPVLI (lines 22–30)",
                "location_reference": "Sch 1-A (2025), Part IV, lines 22–30",
                "excerpt_text": (
                    "L22 rows a/b: (i) VIN, (ii) amount deducted on Sch C/E/F, (iii) Schedule 1-A "
                    "amount = total QPVLI paid 2025 − col (ii). L23 = sum of col (iii); "
                    "L24 = min(L23, $10,000); L25 = L3; L26 = $100,000 ($200,000 MFJ); L27 = L25−L26; "
                    "L28 = ceil(L27/1000) [ROUND UP]; L29 = L28×$200; L30 = max(0, L24−L29) = QPVLI deduction."
                ),
                "summary_text": "Part IV car loan: cap $10,000 then phaseout (round UP ×$200 — opposite of II/III).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part V — Senior (lines 31–37)",
                "location_reference": "Sch 1-A (2025), Part V, lines 31–37",
                "excerpt_text": (
                    "L31 = L3; L32 = $75,000 ($150,000 MFJ); L33 = L31−L32 (if ≤0, enter $6,000 on L35); "
                    "L34 = L33 × 6% (0.06) [continuous, no rounding]; L35 = max(0, $6,000 − L34); "
                    "L36a = L35 if taxpayer has valid SSN AND born before Jan 2 of (tax_year−64); "
                    "L36b = L35 if MFJ AND spouse has valid SSN AND spouse born before Jan 2 of (tax_year−64); "
                    "L37 = L36a + L36b = enhanced senior deduction."
                ),
                "summary_text": "Part V senior: $6,000 base, continuous 6% phaseout over $75,000/$150,000, per qualifying spouse.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part VI — Total (line 38)",
                "location_reference": "Sch 1-A (2025), Part VI, line 38",
                "excerpt_text": (
                    "L38 = L13 + L21 + L30 + L37 → Form 1040/1040-SR line 13b (Form 1040-NR line 13c)."
                ),
                "summary_text": "Part VI total of all four deductions → Form 1040 line 13b.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ─── IRC §224 — Tips ───
    {
        "source_code": "IRC_224",
        "source_type": "code_section",
        "source_rank": "controlling",
        "jurisdiction_code": "FED",
        "title": "IRC §224 — Deduction for Qualified Tips",
        "citation": "26 U.S.C. §224 (added by P.L. 119-21 §70201)",
        "issuer": "Congress",
        "current_status": "active",
        "effective_date_start": "2025-01-01",
        "effective_date_end": "2028-12-31",
        "is_substantive_authority": True,
        "trust_score": 10.00,
        "requires_human_review": True,
        "notes": "Added by OBBBA §70201. Effective TY 2025–2028.",
        "topics": ["tips_deduction", "obbba"],
        "excerpts": [
            {
                "excerpt_label": "§224(b)(1) — Cap; §224(b)(2) — MAGI phaseout",
                "location_reference": "26 U.S.C. §224(b)(1)–(2)",
                "excerpt_text": (
                    "§224(b)(1): maximum deduction $25,000. §224(b)(2): phaseout begins at MAGI "
                    "$150,000 ($300,000 MFJ); reduced $100 for each $1,000 (rounded down) of excess. "
                    "MAGI defined per §224(b)(2)."
                ),
                "summary_text": "Cap $25,000; phaseout over $150,000/$300,000 at $100 per $1,000 (round down).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§224(d)(1)–(2) qualified tips/occupations; §224(e) SSN; SE limit",
                "location_reference": "26 U.S.C. §224(d)(1), (d)(2), (e)",
                "excerpt_text": (
                    "§224(d)(1): limited to tips received in occupations that customarily and regularly "
                    "received tips (IRS published list per OBBBA §70201(h); REG-110032-25). §224(d)(2): "
                    "qualified tips defined. §224(e): valid SSN required. SE filers: deduction ≤ "
                    "trade/business gross income (including tips) minus other allocable deductions."
                ),
                "summary_text": "Qualified-occupation list, qualified-tips definition, SSN requirement, SE gross-income limit.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ─── IRC §225 — Overtime ───
    {
        "source_code": "IRC_225",
        "source_type": "code_section",
        "source_rank": "controlling",
        "jurisdiction_code": "FED",
        "title": "IRC §225 — Deduction for Qualified Overtime Compensation",
        "citation": "26 U.S.C. §225 (added by P.L. 119-21 §70202)",
        "issuer": "Congress",
        "current_status": "active",
        "effective_date_start": "2025-01-01",
        "effective_date_end": "2028-12-31",
        "is_substantive_authority": True,
        "trust_score": 10.00,
        "requires_human_review": True,
        "notes": "Added by OBBBA §70202. Effective TY 2025–2028.",
        "topics": ["overtime_deduction", "obbba"],
        "excerpts": [
            {
                "excerpt_label": "§225(b)(1) — Cap; §225(b)(2) — MAGI phaseout",
                "location_reference": "26 U.S.C. §225(b)(1)–(2)",
                "excerpt_text": (
                    "§225(b)(1): maximum deduction $12,500 ($25,000 MFJ). §225(b)(2): phaseout begins at "
                    "MAGI $150,000 ($300,000 MFJ); reduced $100 for each $1,000 (rounded down) of excess."
                ),
                "summary_text": "Cap $12,500/$25,000 MFJ; phaseout over $150,000/$300,000 at $100 per $1,000 (round down).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§225(c)(1) — Qualified overtime = FLSA premium only",
                "location_reference": "26 U.S.C. §225(c)(1)",
                "excerpt_text": (
                    "Qualified overtime is the FLSA PREMIUM ONLY: the excess over the regular rate "
                    "required by 29 U.S.C. §207 (the 'half' of time-and-a-half); not gross overtime and "
                    "not voluntary double-time. Reported per §6041(d)(4) / §6051(a)(19)."
                ),
                "summary_text": "Qualified amount is the FLSA half-premium over the regular rate, not gross OT.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ─── IRC §163 — Car loan / QPVLI ───
    {
        "source_code": "IRC_163",
        "source_type": "code_section",
        "source_rank": "controlling",
        "jurisdiction_code": "FED",
        "title": "IRC §163(h)(4) — Qualified Passenger Vehicle Loan Interest (QPVLI)",
        "citation": "26 U.S.C. §163(h)(4) (added by P.L. 119-21 §70203(a))",
        "issuer": "Congress",
        "current_status": "active",
        "effective_date_start": "2025-01-01",
        "effective_date_end": "2028-12-31",
        "is_substantive_authority": True,
        "trust_score": 10.00,
        "requires_human_review": True,
        "notes": "QPVLI deduction added by OBBBA §70203(a). Effective TY 2025–2028.",
        "topics": ["car_loan_interest_deduction", "obbba"],
        "excerpts": [
            {
                "excerpt_label": "§163(h)(4) — Cap and MAGI phaseout",
                "location_reference": "26 U.S.C. §163(h)(4)",
                "excerpt_text": (
                    "Deduction for qualified passenger vehicle loan interest. Cap $10,000. Phaseout begins "
                    "at MAGI $100,000 ($200,000 MFJ); reduced $200 for each $1,000 (rounded UP) of excess."
                ),
                "summary_text": "Cap $10,000; phaseout over $100,000/$200,000 at $200 per $1,000 (round UP).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§163(h)(4) — Vehicle and loan conditions",
                "location_reference": "26 U.S.C. §163(h)(4)",
                "excerpt_text": (
                    "Conditions: new vehicle (original use begins with taxpayer); final assembly in U.S.; "
                    "≥2 wheels, primarily for public roads, GVWR < 14,000 lbs, motor vehicle under the "
                    "Clean Air Act; personal use; loan incurred after 12/31/2024, first lien secured by the "
                    "vehicle, not owed to a related party; leases excluded; refinance eligible up to the "
                    "balance still owed if it remains a first lien; VIN reported on the return."
                ),
                "summary_text": "New US-assembled personal vehicle; post-2024 first-lien loan, non-related-party; leases out; VIN reported.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ─── IRC §911 — FEIE / housing (MAGI add-back) ───
    {
        "source_code": "IRC_911",
        "source_type": "code_section",
        "source_rank": "controlling",
        "jurisdiction_code": "FED",
        "title": "IRC §911 — Foreign Earned Income / Housing Exclusion",
        "citation": "26 U.S.C. §911",
        "issuer": "Congress",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 10.00,
        "requires_human_review": True,
        "notes": "Form 2555 line 45 (FEIE) and line 50 (housing) are added back to AGI to compute MAGI for Schedule 1-A.",
        "topics": ["additional_deductions"],
        "excerpts": [
            {
                "excerpt_label": "§911 — FEIE and housing exclusion add-back",
                "location_reference": "26 U.S.C. §911; Form 2555 lines 45, 50",
                "excerpt_text": (
                    "Foreign earned income exclusion (§911) and housing exclusion/deduction. For Schedule "
                    "1-A MAGI: Form 2555 line 45 (FEIE) added on L2b and Form 2555 line 50 (housing) on L2c."
                ),
                "summary_text": "§911 FEIE (2555 L45) and housing (2555 L50) added back for MAGI.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ─── IRC §931 — American Samoa (MAGI add-back) ───
    {
        "source_code": "IRC_931",
        "source_type": "code_section",
        "source_rank": "controlling",
        "jurisdiction_code": "FED",
        "title": "IRC §931 — Income from American Samoa",
        "citation": "26 U.S.C. §931",
        "issuer": "Congress",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 10.00,
        "requires_human_review": True,
        "notes": "Form 4563 line 15 excluded amount added back to AGI to compute MAGI for Schedule 1-A.",
        "topics": ["additional_deductions"],
        "excerpts": [
            {
                "excerpt_label": "§931 — American Samoa exclusion add-back",
                "location_reference": "26 U.S.C. §931; Form 4563 line 15",
                "excerpt_text": (
                    "Exclusion of income from sources within American Samoa (§931). For Schedule 1-A MAGI: "
                    "Form 4563 line 15 excluded amount added on L2d."
                ),
                "summary_text": "§931 American Samoa exclusion (4563 L15) added back for MAGI.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ─── IRC §933 — Puerto Rico (MAGI add-back) ───
    {
        "source_code": "IRC_933",
        "source_type": "code_section",
        "source_rank": "controlling",
        "jurisdiction_code": "FED",
        "title": "IRC §933 — Income from Puerto Rico",
        "citation": "26 U.S.C. §933",
        "issuer": "Congress",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 10.00,
        "requires_human_review": True,
        "notes": "Excluded Puerto Rico income added back to AGI to compute MAGI for Schedule 1-A.",
        "topics": ["additional_deductions"],
        "excerpts": [
            {
                "excerpt_label": "§933 — Puerto Rico exclusion add-back",
                "location_reference": "26 U.S.C. §933",
                "excerpt_text": (
                    "Exclusion of income from sources within Puerto Rico for bona fide residents (§933). "
                    "For Schedule 1-A MAGI: excluded Puerto Rico income added on L2a."
                ),
                "summary_text": "§933 Puerto Rico exclusion added back for MAGI.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ─── IRC §6041 — Overtime info reporting ───
    {
        "source_code": "IRC_6041",
        "source_type": "code_section",
        "source_rank": "controlling",
        "jurisdiction_code": "FED",
        "title": "IRC §6041 — Information at Source (Overtime Reporting)",
        "citation": "26 U.S.C. §6041(d)(4)",
        "issuer": "Congress",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 10.00,
        "requires_human_review": True,
        "notes": "§6041(d)(4): reporting of qualified overtime compensation.",
        "topics": ["overtime_deduction"],
        "excerpts": [
            {
                "excerpt_label": "§6041(d)(4) — Overtime reporting",
                "location_reference": "26 U.S.C. §6041(d)(4)",
                "excerpt_text": "Information returns must report qualified overtime compensation per §6041(d)(4).",
                "summary_text": "§6041(d)(4) requires reporting of qualified overtime.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ─── IRC §6051 — W-2 overtime reporting ───
    {
        "source_code": "IRC_6051",
        "source_type": "code_section",
        "source_rank": "controlling",
        "jurisdiction_code": "FED",
        "title": "IRC §6051 — Receipts for Employees (W-2 Overtime Reporting)",
        "citation": "26 U.S.C. §6051(a)(19)",
        "issuer": "Congress",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 10.00,
        "requires_human_review": True,
        "notes": "§6051(a)(19): W-2 reporting of qualified overtime compensation.",
        "topics": ["overtime_deduction"],
        "excerpts": [
            {
                "excerpt_label": "§6051(a)(19) — W-2 overtime reporting",
                "location_reference": "26 U.S.C. §6051(a)(19)",
                "excerpt_text": "Form W-2 must report qualified overtime compensation per §6051(a)(19).",
                "summary_text": "§6051(a)(19) requires W-2 reporting of qualified overtime.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ─── IRC §6050AA — QPVLI reporting ───
    {
        "source_code": "IRC_6050AA",
        "source_type": "code_section",
        "source_rank": "controlling",
        "jurisdiction_code": "FED",
        "title": "IRC §6050AA — Returns Relating to Qualified Passenger Vehicle Loan Interest",
        "citation": "26 U.S.C. §6050AA (added by P.L. 119-21 §70203(c))",
        "issuer": "Congress",
        "current_status": "active",
        "effective_date_start": "2025-01-01",
        "effective_date_end": "2028-12-31",
        "is_substantive_authority": True,
        "trust_score": 10.00,
        "requires_human_review": True,
        "notes": "Added by OBBBA §70203(c). Reporting of QPVLI received.",
        "topics": ["car_loan_interest_deduction", "obbba"],
        "excerpts": [
            {
                "excerpt_label": "§6050AA — QPVLI reporting",
                "location_reference": "26 U.S.C. §6050AA",
                "excerpt_text": (
                    "Returns relating to qualified passenger vehicle loan interest received (added by "
                    "OBBBA §70203(c))."
                ),
                "summary_text": "§6050AA requires reporting of QPVLI received.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ─── 29 U.S.C. §207 — FLSA overtime ───
    {
        "source_code": "USC_29_207",
        "source_type": "code_section",
        "source_rank": "controlling",
        "jurisdiction_code": "FED",
        "title": "29 U.S.C. §207 — Fair Labor Standards Act: Maximum Hours / Overtime",
        "citation": "29 U.S.C. §207",
        "issuer": "Congress",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 10.00,
        "requires_human_review": True,
        "notes": "Defines the overtime premium (the 'half' over the regular rate) referenced by IRC §225(c)(1).",
        "topics": ["overtime_deduction"],
        "excerpts": [
            {
                "excerpt_label": "29 U.S.C. §207 — Overtime premium over regular rate",
                "location_reference": "29 U.S.C. §207",
                "excerpt_text": (
                    "FLSA §207 requires overtime pay above the regular rate. The premium (the 'half' of "
                    "time-and-a-half) is the qualified overtime amount under IRC §225(c)(1)."
                ),
                "summary_text": "FLSA §207 premium over the regular rate = qualified overtime per §225(c)(1).",
                "is_key_excerpt": True,
            },
        ],
    },
    # ─── OBBBA §70103 — Senior ───
    {
        "source_code": "PL_119_21_70103",
        "source_type": "code_section",
        "source_rank": "controlling",
        "jurisdiction_code": "FED",
        "title": "Public Law 119-21 §70103 — Enhanced Deduction for Seniors (OBBBA)",
        "citation": "P.L. 119-21 §70103; 139 Stat. 72",
        "issuer": "Congress",
        "official_url": "https://www.congress.gov/119/plaws/publ21/PLAW-119publ21.pdf",
        "publication_date": "2025-07-04",
        "effective_date_start": "2025-01-01",
        "effective_date_end": "2028-12-31",
        "is_substantive_authority": True,
        "trust_score": 10.00,
        "requires_human_review": True,
        "notes": "Adds/amends IRC §151(d)(5). Effective TY 2025–2028.",
        "topics": ["senior_deduction", "obbba"],
        "excerpts": [
            {
                "excerpt_label": "§70103 — Enhanced senior deduction",
                "location_reference": "P.L. 119-21 §70103",
                "excerpt_text": (
                    "Enhanced deduction for seniors via IRC §151(d)(5): $6,000 base; 6% (continuous) "
                    "phaseout of MAGI over $75,000 ($150,000 MFJ); below-the-line; in addition to the "
                    "age-65 additional standard deduction; MFS ineligible. Effective TY 2025–2028."
                ),
                "summary_text": "$6,000 senior deduction, 6% phaseout over $75,000/$150,000, per qualifying spouse.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ─── OBBBA §70201 — Tips ───
    {
        "source_code": "PL_119_21_70201",
        "source_type": "code_section",
        "source_rank": "controlling",
        "jurisdiction_code": "FED",
        "title": "Public Law 119-21 §70201 — No Tax on Tips (OBBBA)",
        "citation": "P.L. 119-21 §70201; 139 Stat. 72",
        "issuer": "Congress",
        "official_url": "https://www.congress.gov/119/plaws/publ21/PLAW-119publ21.pdf",
        "publication_date": "2025-07-04",
        "effective_date_start": "2025-01-01",
        "effective_date_end": "2028-12-31",
        "is_substantive_authority": True,
        "trust_score": 10.00,
        "requires_human_review": True,
        "notes": "Adds IRC §224. §70201(h): Treasury publishes the qualified-occupation list (REG-110032-25). Effective TY 2025–2028.",
        "topics": ["tips_deduction", "obbba"],
        "excerpts": [
            {
                "excerpt_label": "§70201 — Adds IRC §224; occupation list",
                "location_reference": "P.L. 119-21 §70201, §70201(h)",
                "excerpt_text": (
                    "Adds IRC §224 (deduction for qualified tips). §70201(h): the Secretary publishes the "
                    "list of occupations that customarily and regularly received tips (see REG-110032-25). "
                    "Effective TY 2025–2028."
                ),
                "summary_text": "Creates §224 tips deduction; directs Treasury occupation list.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ─── OBBBA §70202 — Overtime ───
    {
        "source_code": "PL_119_21_70202",
        "source_type": "code_section",
        "source_rank": "controlling",
        "jurisdiction_code": "FED",
        "title": "Public Law 119-21 §70202 — No Tax on Overtime (OBBBA)",
        "citation": "P.L. 119-21 §70202; 139 Stat. 72",
        "issuer": "Congress",
        "official_url": "https://www.congress.gov/119/plaws/publ21/PLAW-119publ21.pdf",
        "publication_date": "2025-07-04",
        "effective_date_start": "2025-01-01",
        "effective_date_end": "2028-12-31",
        "is_substantive_authority": True,
        "trust_score": 10.00,
        "requires_human_review": True,
        "notes": "Adds IRC §225. Effective TY 2025–2028.",
        "topics": ["overtime_deduction", "obbba"],
        "excerpts": [
            {
                "excerpt_label": "§70202 — Adds IRC §225",
                "location_reference": "P.L. 119-21 §70202",
                "excerpt_text": (
                    "Adds IRC §225 (deduction for qualified overtime compensation). Effective TY 2025–2028."
                ),
                "summary_text": "Creates §225 overtime deduction.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ─── OBBBA §70203 — Car loan ───
    {
        "source_code": "PL_119_21_70203",
        "source_type": "code_section",
        "source_rank": "controlling",
        "jurisdiction_code": "FED",
        "title": "Public Law 119-21 §70203 — Car Loan Interest Deduction (OBBBA)",
        "citation": "P.L. 119-21 §70203; 139 Stat. 72",
        "issuer": "Congress",
        "official_url": "https://www.congress.gov/119/plaws/publ21/PLAW-119publ21.pdf",
        "publication_date": "2025-07-04",
        "effective_date_start": "2025-01-01",
        "effective_date_end": "2028-12-31",
        "is_substantive_authority": True,
        "trust_score": 10.00,
        "requires_human_review": True,
        "notes": "(a) adds IRC §163(h)(4); (b) §63(b)(7) non-itemizer treatment; (c) §6050AA reporting. Effective TY 2025–2028.",
        "topics": ["car_loan_interest_deduction", "obbba"],
        "excerpts": [
            {
                "excerpt_label": "§70203 — QPVLI deduction, non-itemizer, reporting",
                "location_reference": "P.L. 119-21 §70203(a)–(c)",
                "excerpt_text": (
                    "(a) adds IRC §163(h)(4) qualified passenger vehicle loan interest; (b) §63(b)(7) makes "
                    "it available to non-itemizers (below-the-line); (c) adds §6050AA reporting. "
                    "Effective TY 2025–2028."
                ),
                "summary_text": "Creates QPVLI deduction (§163(h)(4)), non-itemizer treatment (§63(b)(7)), reporting (§6050AA).",
                "is_key_excerpt": True,
            },
        ],
    },
    # ─── IRS Notice 2025-69 — Tips & overtime ───
    {
        "source_code": "IRS_NOTICE_2025_69",
        "source_type": "official_notice",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRS Notice 2025-69 — Tips and Overtime Deductions (Interim Guidance)",
        "citation": "Notice 2025-69",
        "issuer": "IRS",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.00,
        "requires_human_review": True,
        "notes": "Interim guidance on the §224 (tips) and §225 (overtime) deductions for TY 2025.",
        "topics": ["tips_deduction", "overtime_deduction"],
        "excerpts": [
            {
                "excerpt_label": "Notice 2025-69 — Tips/overtime interim guidance",
                "location_reference": "Notice 2025-69",
                "excerpt_text": (
                    "Interim/transition guidance implementing the no-tax-on-tips (§224) and "
                    "no-tax-on-overtime (§225) deductions for tax year 2025."
                ),
                "summary_text": "IRS interim guidance for §224 and §225 (TY 2025).",
                "is_key_excerpt": True,
            },
        ],
    },
    # ─── REG-110032-25 — Tips occupations ───
    {
        "source_code": "IRS_REG_110032_25",
        "source_type": "regulation",
        "source_rank": "implementation_official",
        "jurisdiction_code": "FED",
        "title": "REG-110032-25 — Proposed Regulations: Tipped Occupations (IRC §224(d)(1))",
        "citation": "REG-110032-25",
        "issuer": "Treasury",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.00,
        "requires_human_review": True,
        "notes": "Proposed regs: list of occupations that customarily and regularly received tips for §224(d)(1) (per OBBBA §70201(h)).",
        "topics": ["tips_deduction"],
        "excerpts": [
            {
                "excerpt_label": "REG-110032-25 — Qualified tipped occupations",
                "location_reference": "REG-110032-25",
                "excerpt_text": (
                    "Proposed regulations identifying the occupations that customarily and regularly "
                    "received tips for purposes of IRC §224(d)(1) (per OBBBA §70201(h))."
                ),
                "summary_text": "Proposed list of qualified tipped occupations under §224(d)(1).",
                "is_key_excerpt": True,
            },
        ],
    },
    # ─── REG-113515-25 — Car loan ───
    {
        "source_code": "IRS_REG_113515_25",
        "source_type": "regulation",
        "source_rank": "implementation_official",
        "jurisdiction_code": "FED",
        "title": "REG-113515-25 — Proposed Regulations: Car Loan Interest Deduction (QPVLI)",
        "citation": "REG-113515-25",
        "issuer": "Treasury",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.00,
        "requires_human_review": True,
        "notes": "Proposed regs implementing IRC §163(h)(4) QPVLI and §6050AA reporting.",
        "topics": ["car_loan_interest_deduction"],
        "excerpts": [
            {
                "excerpt_label": "REG-113515-25 — QPVLI implementation",
                "location_reference": "REG-113515-25",
                "excerpt_text": (
                    "Proposed regulations implementing the qualified passenger vehicle loan interest "
                    "deduction (IRC §163(h)(4)) and §6050AA reporting."
                ),
                "summary_text": "Proposed QPVLI implementation regs.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ─── IR-2025-129 — Car loan news release ───
    {
        "source_code": "IRS_IR_2025_129",
        "source_type": "official_publication",
        "source_rank": "reference_only",
        "jurisdiction_code": "FED",
        "title": "IR-2025-129 — IRS News Release: Car Loan Interest Deduction",
        "citation": "IR-2025-129",
        "issuer": "IRS",
        "current_status": "active",
        "is_substantive_authority": False,
        "trust_score": 8.00,
        "requires_human_review": True,
        "notes": "IRS news release (informational, not controlling) on the QPVLI deduction.",
        "topics": ["car_loan_interest_deduction"],
        "excerpts": [
            {
                "excerpt_label": "IR-2025-129 — QPVLI announcement",
                "location_reference": "IR-2025-129",
                "excerpt_text": "IRS news release describing the car loan interest deduction (QPVLI).",
                "summary_text": "IRS news release on the QPVLI deduction.",
                "is_key_excerpt": False,
            },
        ],
    },
]

# Excerpts to ADD to EXISTING sources (reuse without clobbering their records).
NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = [
    ("IRC_151", {
        "excerpt_label": "§151(d)(5) — Enhanced senior deduction (SCH_1A)",
        "location_reference": "26 U.S.C. §151(d)(5) (per P.L. 119-21 §70103)",
        "excerpt_text": (
            "Enhanced deduction for seniors: $6,000 base; phaseout 6% (continuous, no rounding) of MAGI "
            "over $75,000 ($150,000 MFJ); below-the-line; in addition to the age-65 additional standard "
            "deduction; MFS ineligible. Claimed per qualifying taxpayer/spouse with a valid SSN who was "
            "born before Jan 2 of (tax_year − 64). Age cutoffs roll: TY2025 1961-01-02, 2026 1962-01-02, "
            "2027 1963-01-02, 2028 1964-01-02."
        ),
        "summary_text": "§151(d)(5) enhanced senior deduction: $6,000, 6% phaseout, per qualifying spouse.",
        "is_key_excerpt": True,
    }),
    ("IRC_63", {
        "excerpt_label": "§63(b)(7) — Non-itemizer below-the-line deductions (SCH_1A)",
        "location_reference": "26 U.S.C. §63(b)(7) (per P.L. 119-21 §70203(b))",
        "excerpt_text": (
            "The Schedule 1-A additional deductions (including QPVLI per OBBBA §70203(b)) are allowed in "
            "computing taxable income whether or not the taxpayer itemizes — below-the-line, reducing "
            "taxable income but not AGI."
        ),
        "summary_text": "§63(b)(7): Schedule 1-A deductions allowed below-the-line for non-itemizers.",
        "is_key_excerpt": True,
    }),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM FACTS
# Return-level unless the note says per-row. Car-loan rows are per-vehicle.
# ═══════════════════════════════════════════════════════════════════════════

FORM_FACTS: list[dict] = [
    # ── Shared (gates) ──
    {"fact_key": "filing_status", "label": "Filing status", "data_type": "choice",
     "choices": ["single", "mfj", "mfs", "hoh", "qss"], "required": True, "sort_order": 1,
     "notes": "Return-level. MFS is ineligible for tips/overtime/senior (Parts II/III/V)."},
    {"fact_key": "taxpayer_has_valid_ssn", "label": "Taxpayer has valid SSN", "data_type": "boolean",
     "required": True, "sort_order": 2, "notes": "Return-level. Required gate for tips/overtime/senior."},
    {"fact_key": "spouse_has_valid_ssn", "label": "Spouse has valid SSN (MFJ)", "data_type": "boolean",
     "sort_order": 3, "notes": "Return-level. Material on MFJ for the senior spouse amount (L36b)."},

    # ── Part I — MAGI ──
    {"fact_key": "agi_1040_line_11b", "label": "AGI (Form 1040/1040-SR/1040-NR line 11b)",
     "data_type": "decimal", "required": True, "sort_order": 10, "notes": "Return-level. Schedule 1-A L1."},
    {"fact_key": "pr_excluded_income", "label": "Excluded Puerto Rico income (§933)",
     "data_type": "decimal", "default_value": "0", "sort_order": 11, "notes": "Return-level. Schedule 1-A L2a."},
    {"fact_key": "feie_2555_line_45", "label": "Form 2555 line 45 — FEIE (§911)",
     "data_type": "decimal", "default_value": "0", "sort_order": 12, "notes": "Return-level. Schedule 1-A L2b."},
    {"fact_key": "housing_2555_line_50", "label": "Form 2555 line 50 — housing (§911)",
     "data_type": "decimal", "default_value": "0", "sort_order": 13, "notes": "Return-level. Schedule 1-A L2c."},
    {"fact_key": "american_samoa_4563_line_15", "label": "Form 4563 line 15 — American Samoa (§931)",
     "data_type": "decimal", "default_value": "0", "sort_order": 14, "notes": "Return-level. Schedule 1-A L2d."},

    # ── Part II — Tips ──
    {"fact_key": "tips_w2_box_7", "label": "Qualified tips — W-2 box 7", "data_type": "decimal",
     "default_value": "0", "sort_order": 20, "notes": "Return-level. Schedule 1-A L4a."},
    {"fact_key": "tips_form_4137_line_1", "label": "Tips — Form 4137 line 1", "data_type": "decimal",
     "default_value": "0", "sort_order": 21, "notes": "Return-level. Schedule 1-A L4b."},
    {"fact_key": "tips_trade_business", "label": "Trade/business tips (1099-NEC box1 / 1099-MISC box3 / 1099-K box1a, ≤ net profit)",
     "data_type": "decimal", "default_value": "0", "sort_order": 22, "notes": "Return-level. Schedule 1-A L5."},
    {"fact_key": "tips_occupation_on_irs_list", "label": "Tips occupation on the IRS qualified-occupation list (§224(d)(1))",
     "data_type": "boolean", "sort_order": 23, "notes": "Return-level. Per REG-110032-25. Off-list tips are not qualified."},
    {"fact_key": "tips_w2_box_5_medicare_wages", "label": "W-2 box 5 Medicare wages (for tips special-handling check)",
     "data_type": "decimal", "default_value": "0", "sort_order": 24, "notes": "Return-level. Drives diagnostic: box 5 > $176,100."},
    {"fact_key": "tips_multiple_employers_or_occupations", "label": "Tips across multiple employers or occupations",
     "data_type": "boolean", "sort_order": 25, "notes": "Return-level. Drives the multiple-employer/occupation warning."},
    {"fact_key": "tips_se_trade_business_gross_income", "label": "SE trade/business gross income (incl. tips)",
     "data_type": "decimal", "default_value": "0", "sort_order": 26, "notes": "Return-level. SE limit input."},
    {"fact_key": "tips_se_other_allocable_deductions", "label": "Other deductions allocable to the SE trade/business",
     "data_type": "decimal", "default_value": "0", "sort_order": 27, "notes": "Return-level. SE limit input."},

    # ── Part III — Overtime ──
    {"fact_key": "ot_w2_box_1_qualified", "label": "Qualified overtime — W-2 box 1", "data_type": "decimal",
     "default_value": "0", "sort_order": 30, "notes": "Return-level. Schedule 1-A L14a. FLSA premium only."},
    {"fact_key": "ot_1099", "label": "Qualified overtime — 1099-NEC box1 / 1099-MISC box3", "data_type": "decimal",
     "default_value": "0", "sort_order": 31, "notes": "Return-level. Schedule 1-A L14b. FLSA premium only."},

    # ── Part IV — Car Loan Interest (per-vehicle rows) ──
    {"fact_key": "car_row_vin", "label": "Vehicle identification number (VIN)", "data_type": "string",
     "sort_order": 40, "notes": "Per-Vehicle (Schedule 1-A L22 rows a/b col i). VIN reported on the return."},
    {"fact_key": "car_row_amount_deducted_sch_cef", "label": "QPVLI already deducted on Sch C/E/F",
     "data_type": "decimal", "default_value": "0", "sort_order": 41,
     "notes": "Per-Vehicle (L22 col ii). Subtracted to avoid double-deduction."},
    {"fact_key": "car_row_sch1a_amount", "label": "Schedule 1-A QPVLI amount (total QPVLI paid 2025 − col ii)",
     "data_type": "decimal", "default_value": "0", "sort_order": 42, "notes": "Per-Vehicle (L22 col iii)."},
    {"fact_key": "car_row_vehicle_qualifies", "label": "Vehicle meets QPVLI conditions",
     "data_type": "boolean", "sort_order": 43,
     "notes": ("Per-Vehicle. New (original use begins with taxpayer); final assembly in U.S.; ≥2 wheels; "
               "primarily for public roads; GVWR < 14,000 lbs; motor vehicle under the Clean Air Act; personal use.")},
    {"fact_key": "car_row_loan_qualifies", "label": "Loan meets QPVLI conditions",
     "data_type": "boolean", "sort_order": 44,
     "notes": ("Per-Vehicle. Loan incurred after 12/31/2024; first lien secured by the vehicle; not owed to a "
               "related party; leases excluded; refinance eligible up to the balance still owed if it remains a first lien.")},

    # ── Part V — Senior ──
    {"fact_key": "senior_taxpayer_born_before_cutoff", "label": "Taxpayer born before Jan 2 of (tax_year − 64)",
     "data_type": "boolean", "sort_order": 50,
     "notes": "Return-level. TY2025 cutoff 1961-01-02 (rolls yearly). Gates L36a."},
    {"fact_key": "senior_spouse_born_before_cutoff", "label": "Spouse born before Jan 2 of (tax_year − 64)",
     "data_type": "boolean", "sort_order": 51,
     "notes": "Return-level. MFJ only. TY2025 cutoff 1961-01-02 (rolls yearly). Gates L36b."},

    # ── Calculated outputs (traceability) ──
    {"fact_key": "magi", "label": "Modified AGI (Schedule 1-A L3)", "data_type": "decimal", "sort_order": 60,
     "notes": "Calculated. L1 + L2e."},
    {"fact_key": "tips_deduction", "label": "Tips deduction (L13)", "data_type": "decimal", "sort_order": 61,
     "notes": "Calculated. Part II output."},
    {"fact_key": "overtime_deduction", "label": "Overtime deduction (L21)", "data_type": "decimal", "sort_order": 62,
     "notes": "Calculated. Part III output."},
    {"fact_key": "qpvli_deduction", "label": "Car loan / QPVLI deduction (L30)", "data_type": "decimal", "sort_order": 63,
     "notes": "Calculated. Part IV output. (tts-tax-app currently stubs this at 0.)"},
    {"fact_key": "senior_deduction", "label": "Enhanced senior deduction (L37)", "data_type": "decimal", "sort_order": 64,
     "notes": "Calculated. Part V output."},
    {"fact_key": "total_additional_deductions", "label": "Total additional deductions (L38)", "data_type": "decimal", "sort_order": 65,
     "notes": "Calculated. Part VI output → Form 1040 line 13b."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM RULES
# ═══════════════════════════════════════════════════════════════════════════

FORM_RULES: list[dict] = [
    # ── Part I — MAGI ──
    {"rule_id": "R-MAGI-01", "title": "MAGI add-backs (L2e)", "rule_type": "calculation",
     "precedence": 1, "sort_order": 1,
     "formula": "L2e = L2a + L2b + L2c + L2d",
     "inputs": ["pr_excluded_income", "feie_2555_line_45", "housing_2555_line_50", "american_samoa_4563_line_15"],
     "outputs": ["L2e"],
     "description": ("ONCE PER RETURN. Sums the §933 (L2a), §911 FEIE (L2b), §911 housing (L2c), and "
                     "§931 American Samoa (L2d) exclusions added back for MAGI.")},
    {"rule_id": "R-MAGI-02", "title": "MAGI (L3)", "rule_type": "calculation",
     "precedence": 2, "sort_order": 2,
     "formula": "magi = L3 = L1 + L2e",
     "inputs": ["agi_1040_line_11b", "L2e"], "outputs": ["magi", "L3"],
     "description": "ONCE PER RETURN. MAGI = AGI (L1) + add-backs (L2e). Used by all four deduction phaseouts."},

    # ── Part II — Tips (IRC §224, OBBBA §70201) ──
    {"rule_id": "R-TIPS-01", "title": "Tips — single-employer W-2/4137 (L4c)", "rule_type": "calculation",
     "precedence": 3, "sort_order": 10,
     "formula": "L4c = larger of L4a, L4b   (single employer)",
     "inputs": ["tips_w2_box_7", "tips_form_4137_line_1"], "outputs": ["L4c"],
     "description": "ONCE PER RETURN. Larger of W-2 box 7 (L4a) or Form 4137 line 1 (L4b) for a single employer."},
    {"rule_id": "R-TIPS-02", "title": "Tips — total qualified tips (L6)", "rule_type": "calculation",
     "precedence": 4, "sort_order": 11,
     "formula": "L6 = L4c + L5",
     "inputs": ["L4c", "tips_trade_business"], "outputs": ["L6"],
     "description": "ONCE PER RETURN. Wage tips (L4c) plus trade/business tips (L5)."},
    {"rule_id": "R-TIPS-03", "title": "Tips — cap (L7)", "rule_type": "calculation",
     "precedence": 5, "sort_order": 12,
     "formula": "L7 = min(L6, 25000)",
     "inputs": ["L6"], "outputs": ["L7"],
     "description": "ONCE PER RETURN. §224(b)(1) cap of $25,000. Cap applied BEFORE the phaseout."},
    {"rule_id": "R-TIPS-04", "title": "Tips — phaseout threshold (L9)", "rule_type": "calculation",
     "precedence": 6, "sort_order": 13,
     "formula": "L9 = 300000 if filing_status == 'mfj' else 150000",
     "inputs": ["filing_status"], "outputs": ["L9"],
     "description": "ONCE PER RETURN. §224(b)(2) MAGI threshold: $150,000 ($300,000 MFJ)."},
    {"rule_id": "R-TIPS-05", "title": "Tips — phaseout excess (L10)", "rule_type": "calculation",
     "precedence": 7, "sort_order": 14,
     "formula": "L10 = max(0, L8 - L9)   where L8 = L3 (MAGI); if <= 0, deduction = L7",
     "inputs": ["L3", "L9"], "outputs": ["L10"],
     "description": "ONCE PER RETURN. Excess of MAGI over threshold. If zero, no phaseout (deduction = L7)."},
    {"rule_id": "R-TIPS-06", "title": "Tips — phaseout reduction (L11, L12) — ROUND DOWN", "rule_type": "calculation",
     "precedence": 8, "sort_order": 15,
     "formula": "L11 = floor(L10 / 1000);  L12 = L11 * 100",
     "inputs": ["L10"], "outputs": ["L11", "L12"],
     "description": "ONCE PER RETURN. Round the $1,000 excess DOWN (floor), then x $100. Reduction lands on L12."},
    {"rule_id": "R-TIPS-07", "title": "Tips deduction (L13)", "rule_type": "calculation",
     "precedence": 9, "sort_order": 16,
     "formula": "L13 = max(0, L7 - L12)",
     "inputs": ["L7", "L12"], "outputs": ["tips_deduction", "L13"],
     "description": "ONCE PER RETURN. Tips deduction after phaseout."},
    {"rule_id": "R-TIPS-08", "title": "Tips — eligibility gate", "rule_type": "validation",
     "precedence": 0, "sort_order": 17,
     "formula": "eligible = taxpayer_has_valid_ssn AND filing_status != 'mfs'",
     "inputs": ["taxpayer_has_valid_ssn", "filing_status"], "outputs": [],
     "description": "ONCE PER RETURN. §224(e) valid SSN required; MFS ineligible."},
    {"rule_id": "R-TIPS-09", "title": "Tips — qualified occupation", "rule_type": "classification",
     "precedence": 0, "sort_order": 18,
     "formula": "qualified_tips require tips_occupation_on_irs_list == True",
     "inputs": ["tips_occupation_on_irs_list"], "outputs": [],
     "description": ("ONCE PER RETURN. §224(d)(1): only tips in occupations on the IRS published list "
                     "(REG-110032-25) are qualified; off-list tips are excluded.")},
    {"rule_id": "R-TIPS-10", "title": "Tips — self-employment gross-income limit", "rule_type": "validation",
     "precedence": 10, "sort_order": 19,
     "formula": "tips_deduction <= tips_se_trade_business_gross_income - tips_se_other_allocable_deductions",
     "inputs": ["tips_se_trade_business_gross_income", "tips_se_other_allocable_deductions"], "outputs": [],
     "description": ("ONCE PER RETURN (SE filers). Deduction limited to trade/business gross income "
                     "(including tips) minus other allocable deductions.")},

    # ── Part III — Overtime (IRC §225, OBBBA §70202) ──
    {"rule_id": "R-OT-01", "title": "Overtime — total qualified OT (L14c)", "rule_type": "calculation",
     "precedence": 3, "sort_order": 20,
     "formula": "L14c = L14a + L14b",
     "inputs": ["ot_w2_box_1_qualified", "ot_1099"], "outputs": ["L14c"],
     "description": "ONCE PER RETURN. W-2 box 1 qualified OT (L14a) + 1099 qualified OT (L14b)."},
    {"rule_id": "R-OT-02", "title": "Overtime — cap (L15)", "rule_type": "calculation",
     "precedence": 4, "sort_order": 21,
     "formula": "L15 = min(L14c, 25000 if filing_status == 'mfj' else 12500)",
     "inputs": ["L14c", "filing_status"], "outputs": ["L15"],
     "description": "ONCE PER RETURN. §225(b)(1) cap: $12,500 single / $25,000 MFJ. Cap applied BEFORE phaseout."},
    {"rule_id": "R-OT-03", "title": "Overtime — phaseout threshold (L17)", "rule_type": "calculation",
     "precedence": 6, "sort_order": 22,
     "formula": "L17 = 300000 if filing_status == 'mfj' else 150000",
     "inputs": ["filing_status"], "outputs": ["L17"],
     "description": "ONCE PER RETURN. §225(b)(2) MAGI threshold: $150,000 ($300,000 MFJ)."},
    {"rule_id": "R-OT-04", "title": "Overtime — phaseout excess (L18)", "rule_type": "calculation",
     "precedence": 7, "sort_order": 23,
     "formula": "L18 = max(0, L16 - L17)   where L16 = L3 (MAGI); if <= 0, deduction = L15",
     "inputs": ["L3", "L17"], "outputs": ["L18"],
     "description": "ONCE PER RETURN. Excess of MAGI over threshold. If zero, no phaseout (deduction = L15)."},
    {"rule_id": "R-OT-05", "title": "Overtime — phaseout reduction (L19, L20) — ROUND DOWN", "rule_type": "calculation",
     "precedence": 8, "sort_order": 24,
     "formula": "L19 = floor(L18 / 1000);  L20 = L19 * 100",
     "inputs": ["L18"], "outputs": ["L19", "L20"],
     "description": "ONCE PER RETURN. Round the $1,000 excess DOWN (floor), then x $100. Reduction lands on L20."},
    {"rule_id": "R-OT-06", "title": "Overtime deduction (L21)", "rule_type": "calculation",
     "precedence": 9, "sort_order": 25,
     "formula": "L21 = max(0, L15 - L20)",
     "inputs": ["L15", "L20"], "outputs": ["overtime_deduction", "L21"],
     "description": "ONCE PER RETURN. Overtime deduction after phaseout."},
    {"rule_id": "R-OT-07", "title": "Overtime — qualified amount is FLSA premium only", "rule_type": "classification",
     "precedence": 0, "sort_order": 26,
     "formula": "qualified_ot = FLSA premium over the regular rate required by 29 USC 207 (the 'half' of time-and-a-half)",
     "inputs": ["ot_w2_box_1_qualified", "ot_1099"], "outputs": [],
     "description": ("ONCE PER RETURN. §225(c)(1): only the FLSA premium (excess over the regular rate) is "
                     "qualified; not gross OT, not voluntary double-time. Reported per §6041(d)(4) / §6051(a)(19).")},
    {"rule_id": "R-OT-08", "title": "Overtime — eligibility gate", "rule_type": "validation",
     "precedence": 0, "sort_order": 27,
     "formula": "eligible = taxpayer_has_valid_ssn AND filing_status != 'mfs'",
     "inputs": ["taxpayer_has_valid_ssn", "filing_status"], "outputs": [],
     "description": "ONCE PER RETURN. Valid SSN required; MFS ineligible."},

    # ── Part IV — Car Loan / QPVLI (IRC §163(h)(4), OBBBA §70203) ──
    {"rule_id": "R-CAR-01", "title": "Car loan — total Schedule 1-A QPVLI (L23)", "rule_type": "calculation",
     "precedence": 4, "sort_order": 30,
     "formula": "L23 = sum over vehicle rows of car_row_sch1a_amount (col iii)",
     "inputs": ["car_row_sch1a_amount"], "outputs": ["L23"],
     "description": ("AGGREGATE OVER VEHICLE ROWS. Each row col (iii) = total QPVLI paid 2025 − amount already "
                     "deducted on Sch C/E/F (col ii). Sum across rows.")},
    {"rule_id": "R-CAR-02", "title": "Car loan — cap (L24)", "rule_type": "calculation",
     "precedence": 5, "sort_order": 31,
     "formula": "L24 = min(L23, 10000)",
     "inputs": ["L23"], "outputs": ["L24"],
     "description": "ONCE PER RETURN. Cap of $10,000. Cap applied BEFORE the phaseout."},
    {"rule_id": "R-CAR-03", "title": "Car loan — phaseout threshold (L26)", "rule_type": "calculation",
     "precedence": 6, "sort_order": 32,
     "formula": "L26 = 200000 if filing_status == 'mfj' else 100000",
     "inputs": ["filing_status"], "outputs": ["L26"],
     "description": "ONCE PER RETURN. MAGI threshold: $100,000 ($200,000 MFJ)."},
    {"rule_id": "R-CAR-04", "title": "Car loan — phaseout excess (L27)", "rule_type": "calculation",
     "precedence": 7, "sort_order": 33,
     "formula": "L27 = max(0, L25 - L26)   where L25 = L3 (MAGI); if <= 0, deduction = L24",
     "inputs": ["L3", "L26"], "outputs": ["L27"],
     "description": "ONCE PER RETURN. Excess of MAGI over threshold. If zero, no phaseout (deduction = L24)."},
    {"rule_id": "R-CAR-05", "title": "Car loan — phaseout reduction (L28, L29) — ROUND UP", "rule_type": "calculation",
     "precedence": 8, "sort_order": 34,
     "formula": "L28 = ceil(L27 / 1000);  L29 = L28 * 200",
     "inputs": ["L27"], "outputs": ["L28", "L29"],
     "description": ("ONCE PER RETURN. Round the $1,000 excess UP (ceil) — OPPOSITE of tips/overtime — then "
                     "x $200. Reduction lands on L29.")},
    {"rule_id": "R-CAR-06", "title": "Car loan / QPVLI deduction (L30)", "rule_type": "calculation",
     "precedence": 9, "sort_order": 35,
     "formula": "L30 = max(0, L24 - L29)",
     "inputs": ["L24", "L29"], "outputs": ["qpvli_deduction", "L30"],
     "description": "ONCE PER RETURN. QPVLI deduction after phaseout. (tts-tax-app currently stubs this at 0.)"},
    {"rule_id": "R-CAR-07", "title": "Car loan — vehicle qualification", "rule_type": "classification",
     "precedence": 0, "sort_order": 36,
     "formula": "vehicle qualifies if: new (original use begins with taxpayer); final assembly in U.S.; "
                ">=2 wheels; primarily public roads; GVWR < 14000 lbs; motor vehicle under Clean Air Act; personal use",
     "inputs": ["car_row_vehicle_qualifies"], "outputs": [],
     "description": "PER VEHICLE ROW. Vehicle eligibility conditions for QPVLI."},
    {"rule_id": "R-CAR-08", "title": "Car loan — loan qualification", "rule_type": "classification",
     "precedence": 0, "sort_order": 37,
     "formula": "loan qualifies if: incurred after 12/31/2024; first lien secured by the vehicle; not owed to a "
                "related party; not a lease; refinance eligible up to balance still owed if it remains a first lien; VIN reported",
     "inputs": ["car_row_loan_qualifies", "car_row_vin"], "outputs": [],
     "description": "PER VEHICLE ROW. Loan eligibility conditions for QPVLI."},

    # ── Part V — Senior (IRC §151(d)(5), OBBBA §70103) ──
    {"rule_id": "R-SEN-01", "title": "Senior — phaseout threshold (L32)", "rule_type": "calculation",
     "precedence": 6, "sort_order": 40,
     "formula": "L32 = 150000 if filing_status == 'mfj' else 75000",
     "inputs": ["filing_status"], "outputs": ["L32"],
     "description": "ONCE PER RETURN. MAGI threshold: $75,000 ($150,000 MFJ)."},
    {"rule_id": "R-SEN-02", "title": "Senior — phaseout excess (L33)", "rule_type": "calculation",
     "precedence": 7, "sort_order": 41,
     "formula": "L33 = max(0, L31 - L32)   where L31 = L3 (MAGI); if <= 0, enter 6000 on L35",
     "inputs": ["L3", "L32"], "outputs": ["L33"],
     "description": "ONCE PER RETURN. Excess of MAGI over threshold. If zero, full $6,000 flows to L35."},
    {"rule_id": "R-SEN-03", "title": "Senior — phaseout amount (L34) — CONTINUOUS 6%", "rule_type": "calculation",
     "precedence": 8, "sort_order": 42,
     "formula": "L34 = L33 * 0.06",
     "inputs": ["L33"], "outputs": ["L34"],
     "description": "ONCE PER RETURN. Continuous 6% of the excess — NO rounding (unlike Parts II/III/IV)."},
    {"rule_id": "R-SEN-04", "title": "Senior — net deduction before SSN/age gates (L35)", "rule_type": "calculation",
     "precedence": 9, "sort_order": 43,
     "formula": "L35 = max(0, 6000 - L34)",
     "inputs": ["L34"], "outputs": ["L35"],
     "description": "ONCE PER RETURN. $6,000 base minus the 6% phaseout. One phaseout computed once on L35."},
    {"rule_id": "R-SEN-05", "title": "Senior — taxpayer amount (L36a)", "rule_type": "calculation",
     "precedence": 10, "sort_order": 44,
     "formula": "L36a = L35 if (taxpayer_has_valid_ssn AND senior_taxpayer_born_before_cutoff) else 0",
     "inputs": ["L35", "taxpayer_has_valid_ssn", "senior_taxpayer_born_before_cutoff"], "outputs": ["L36a"],
     "description": ("ONCE PER RETURN. Taxpayer's L35 if valid SSN AND born before Jan 2 of (tax_year − 64). "
                     "TY2025 cutoff: 1961-01-02.")},
    {"rule_id": "R-SEN-06", "title": "Senior — spouse amount (L36b)", "rule_type": "calculation",
     "precedence": 10, "sort_order": 45,
     "formula": "L36b = L35 if (filing_status == 'mfj' AND spouse_has_valid_ssn AND senior_spouse_born_before_cutoff) else 0",
     "inputs": ["L35", "filing_status", "spouse_has_valid_ssn", "senior_spouse_born_before_cutoff"], "outputs": ["L36b"],
     "description": ("ONCE PER RETURN. Spouse's L35 if MFJ AND spouse valid SSN AND spouse born before Jan 2 of "
                     "(tax_year − 64). The phaseout is computed once (L35) and claimed per qualifying spouse.")},
    {"rule_id": "R-SEN-07", "title": "Senior deduction (L37)", "rule_type": "calculation",
     "precedence": 11, "sort_order": 46,
     "formula": "L37 = L36a + L36b",
     "inputs": ["L36a", "L36b"], "outputs": ["senior_deduction", "L37"],
     "description": "ONCE PER RETURN. Enhanced senior deduction = taxpayer (L36a) + spouse (L36b)."},
    {"rule_id": "R-SEN-08", "title": "Senior — age cutoff rolls by year", "rule_type": "classification",
     "precedence": 0, "sort_order": 47,
     "formula": "born_before = Jan 2 of (tax_year - 64): TY2025=1961-01-02, 2026=1962-01-02, 2027=1963-01-02, 2028=1964-01-02",
     "inputs": [], "outputs": [],
     "description": ("ONCE PER RETURN. _constants_for_year pattern: ONLY the senior age cutoff rolls; all caps and "
                     "thresholds are stable 2025–2028.")},
    {"rule_id": "R-SEN-09", "title": "Senior — eligibility / stacking", "rule_type": "validation",
     "precedence": 0, "sort_order": 48,
     "formula": "MFS ineligible; below-the-line; on top of the existing age-65 additional standard deduction",
     "inputs": ["filing_status"], "outputs": [],
     "description": ("ONCE PER RETURN. Below-the-line; in addition to the age-65 additional standard deduction; "
                     "MFS ineligible.")},

    # ── Part VI — Total ──
    {"rule_id": "R-TOT-01", "title": "Total additional deductions (L38)", "rule_type": "calculation",
     "precedence": 20, "sort_order": 50,
     "formula": "L38 = L13 + L21 + L30 + L37",
     "inputs": ["L13", "L21", "L30", "L37"], "outputs": ["total_additional_deductions", "L38"],
     "description": ("ONCE PER RETURN. Sum of tips + overtime + QPVLI + senior. Flows to Form 1040/1040-SR "
                     "line 13b (Form 1040-NR line 13c). Below-the-line — reduces taxable income, not AGI.")},
]


# ═══════════════════════════════════════════════════════════════════════════
# RULE → AUTHORITY LINKS  (100% coverage — every rule links to ≥ 1 source)
# ═══════════════════════════════════════════════════════════════════════════

RULE_AUTHORITY_LINKS: list[tuple[str, str, str, str]] = [
    # ── Part I — MAGI ──
    ("R-MAGI-01", "IRC_933", "primary", "§933 Puerto Rico exclusion add-back (L2a)"),
    ("R-MAGI-01", "IRC_911", "primary", "§911 FEIE + housing add-back (L2b/L2c)"),
    ("R-MAGI-01", "IRC_931", "primary", "§931 American Samoa add-back (L2d)"),
    ("R-MAGI-01", "IRS_2025_SCH_1A_FORM", "primary", "Schedule 1-A Part I line structure"),
    ("R-MAGI-02", "IRC_224", "primary", "§224(b)(2) MAGI definition"),
    ("R-MAGI-02", "IRC_225", "primary", "§225(b)(2) MAGI definition"),
    ("R-MAGI-02", "IRS_2025_SCH_1A_FORM", "primary", "Schedule 1-A L3 = L1 + L2e"),

    # ── Part II — Tips ──
    ("R-TIPS-01", "IRS_2025_SCH_1A_FORM", "primary", "L4c larger-of, single employer"),
    ("R-TIPS-02", "IRS_2025_SCH_1A_FORM", "primary", "L6 = L4c + L5"),
    ("R-TIPS-03", "IRC_224", "primary", "§224(b)(1) $25,000 cap"),
    ("R-TIPS-03", "PL_119_21_70201", "primary", "OBBBA §70201 enacts §224"),
    ("R-TIPS-04", "IRC_224", "primary", "§224(b)(2) threshold $150,000/$300,000"),
    ("R-TIPS-05", "IRC_224", "primary", "§224(b)(2) phaseout excess"),
    ("R-TIPS-06", "IRC_224", "primary", "§224(b)(2) $100 per $1,000, round down"),
    ("R-TIPS-06", "IRS_2025_SCH_1A_FORM", "secondary", "L11 floor(L10/1000), L12 = L11×$100"),
    ("R-TIPS-07", "IRC_224", "primary", "§224 tips deduction"),
    ("R-TIPS-07", "IRS_2025_SCH_1A_FORM", "secondary", "L13 = max(0, L7 − L12)"),
    ("R-TIPS-08", "IRC_224", "primary", "§224(e) SSN requirement; MFS ineligible"),
    ("R-TIPS-08", "IRS_NOTICE_2025_69", "secondary", "Interim guidance on eligibility"),
    ("R-TIPS-09", "IRC_224", "primary", "§224(d)(1) qualified occupations"),
    ("R-TIPS-09", "IRS_REG_110032_25", "implementation", "Proposed qualified-occupation list"),
    ("R-TIPS-09", "PL_119_21_70201", "secondary", "§70201(h) directs the occupation list"),
    ("R-TIPS-10", "IRC_224", "primary", "§224 SE gross-income limit"),

    # ── Part III — Overtime ──
    ("R-OT-01", "IRS_2025_SCH_1A_FORM", "primary", "L14c = L14a + L14b"),
    ("R-OT-02", "IRC_225", "primary", "§225(b)(1) cap $12,500/$25,000"),
    ("R-OT-02", "PL_119_21_70202", "primary", "OBBBA §70202 enacts §225"),
    ("R-OT-03", "IRC_225", "primary", "§225(b)(2) threshold $150,000/$300,000"),
    ("R-OT-04", "IRC_225", "primary", "§225(b)(2) phaseout excess"),
    ("R-OT-05", "IRC_225", "primary", "§225(b)(2) $100 per $1,000, round down"),
    ("R-OT-05", "IRS_2025_SCH_1A_FORM", "secondary", "L19 floor(L18/1000), L20 = L19×$100"),
    ("R-OT-06", "IRC_225", "primary", "§225 overtime deduction"),
    ("R-OT-06", "IRS_2025_SCH_1A_FORM", "secondary", "L21 = max(0, L15 − L20)"),
    ("R-OT-07", "IRC_225", "primary", "§225(c)(1) FLSA premium only"),
    ("R-OT-07", "USC_29_207", "primary", "FLSA §207 overtime premium"),
    ("R-OT-07", "IRC_6041", "secondary", "§6041(d)(4) reporting"),
    ("R-OT-07", "IRC_6051", "secondary", "§6051(a)(19) W-2 reporting"),
    ("R-OT-08", "IRC_225", "primary", "SSN required; MFS ineligible"),
    ("R-OT-08", "IRS_NOTICE_2025_69", "secondary", "Interim guidance on eligibility"),

    # ── Part IV — Car Loan / QPVLI ──
    ("R-CAR-01", "IRS_2025_SCH_1A_FORM", "primary", "L23 = sum of col (iii); col (iii) = total − col (ii)"),
    ("R-CAR-02", "IRC_163", "primary", "§163(h)(4) $10,000 cap"),
    ("R-CAR-02", "PL_119_21_70203", "primary", "OBBBA §70203(a) enacts §163(h)(4)"),
    ("R-CAR-03", "IRC_163", "primary", "§163(h)(4) threshold $100,000/$200,000"),
    ("R-CAR-04", "IRC_163", "primary", "§163(h)(4) phaseout excess"),
    ("R-CAR-05", "IRC_163", "primary", "§163(h)(4) $200 per $1,000, round UP"),
    ("R-CAR-05", "IRS_2025_SCH_1A_FORM", "secondary", "L28 ceil(L27/1000), L29 = L28×$200"),
    ("R-CAR-06", "IRC_163", "primary", "§163(h)(4) QPVLI deduction"),
    ("R-CAR-06", "IRS_2025_SCH_1A_FORM", "secondary", "L30 = max(0, L24 − L29)"),
    ("R-CAR-06", "IRC_63", "secondary", "§63(b)(7) below-the-line (non-itemizer)"),
    ("R-CAR-07", "IRC_163", "primary", "§163(h)(4) vehicle conditions"),
    ("R-CAR-07", "IRS_REG_113515_25", "implementation", "Proposed QPVLI regs"),
    ("R-CAR-08", "IRC_163", "primary", "§163(h)(4) loan conditions"),
    ("R-CAR-08", "IRC_6050AA", "secondary", "§6050AA QPVLI reporting; VIN on return"),
    ("R-CAR-08", "PL_119_21_70203", "secondary", "§70203(c) reporting"),
    ("R-CAR-08", "IRS_IR_2025_129", "interpretive", "IRS news release on QPVLI"),

    # ── Part V — Senior ──
    ("R-SEN-01", "IRC_151", "primary", "§151(d)(5) threshold $75,000/$150,000"),
    ("R-SEN-02", "IRC_151", "primary", "§151(d)(5) phaseout excess"),
    ("R-SEN-03", "IRC_151", "primary", "§151(d)(5) continuous 6%"),
    ("R-SEN-04", "IRC_151", "primary", "§151(d)(5) $6,000 base less phaseout"),
    ("R-SEN-04", "PL_119_21_70103", "primary", "OBBBA §70103 enhanced senior deduction"),
    ("R-SEN-05", "IRC_151", "primary", "§151(d)(5) taxpayer amount; SSN + age"),
    ("R-SEN-06", "IRC_151", "primary", "§151(d)(5) spouse amount; MFJ + SSN + age"),
    ("R-SEN-07", "IRS_2025_SCH_1A_FORM", "primary", "L37 = L36a + L36b"),
    ("R-SEN-08", "PL_119_21_70103", "primary", "OBBBA §70103 age cutoff rolls 2025–2028"),
    ("R-SEN-09", "IRC_151", "primary", "§151(d)(5) MFS ineligible; stacks on age-65 add'l std deduction"),

    # ── Part VI — Total ──
    ("R-TOT-01", "IRS_2025_SCH_1A_FORM", "primary", "L38 sum → Form 1040 line 13b; below-the-line"),
    ("R-TOT-01", "IRC_63", "secondary", "§63(b)(7) below-the-line treatment"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM LINES (line_map)
# ═══════════════════════════════════════════════════════════════════════════

FORM_LINES: list[dict] = [
    # ── Part I — MAGI ──
    {"line_number": "1", "description": "AGI (Form 1040/1040-SR/1040-NR line 11b)", "line_type": "input", "sort_order": 1},
    {"line_number": "2a", "description": "Excluded Puerto Rico income (§933)", "line_type": "input", "sort_order": 2},
    {"line_number": "2b", "description": "Form 2555 line 45 — FEIE (§911)", "line_type": "input", "sort_order": 3},
    {"line_number": "2c", "description": "Form 2555 line 50 — housing (§911)", "line_type": "input", "sort_order": 4},
    {"line_number": "2d", "description": "Form 4563 line 15 — American Samoa (§931)", "line_type": "input", "sort_order": 5},
    {"line_number": "2e", "description": "Add lines 2a–2d", "line_type": "subtotal", "source_rules": ["R-MAGI-01"], "sort_order": 6},
    {"line_number": "3", "description": "MAGI = Line 1 + Line 2e", "line_type": "calculated", "source_rules": ["R-MAGI-02"], "sort_order": 7},

    # ── Part II — Tips ──
    {"line_number": "4a", "description": "Qualified tips — W-2 box 7", "line_type": "input", "sort_order": 10},
    {"line_number": "4b", "description": "Tips — Form 4137 line 1", "line_type": "input", "sort_order": 11},
    {"line_number": "4c", "description": "Larger of 4a or 4b (single employer)", "line_type": "calculated", "source_rules": ["R-TIPS-01"], "sort_order": 12},
    {"line_number": "5", "description": "Trade/business tips (1099-NEC box1 / 1099-MISC box3 / 1099-K box1a, ≤ net profit)", "line_type": "input", "sort_order": 13},
    {"line_number": "6", "description": "Total qualified tips (Line 4c + Line 5)", "line_type": "subtotal", "source_rules": ["R-TIPS-02"], "sort_order": 14},
    {"line_number": "7", "description": "Tips cap — min(Line 6, $25,000)", "line_type": "calculated", "source_rules": ["R-TIPS-03"], "sort_order": 15},
    {"line_number": "8", "description": "MAGI (from Line 3)", "line_type": "calculated", "source_rules": ["R-TIPS-05"], "sort_order": 16},
    {"line_number": "9", "description": "Threshold ($150,000 / $300,000 MFJ)", "line_type": "calculated", "source_rules": ["R-TIPS-04"], "sort_order": 17},
    {"line_number": "10", "description": "Line 8 − Line 9 (if ≤ 0, deduction = Line 7)", "line_type": "calculated", "source_rules": ["R-TIPS-05"], "sort_order": 18},
    {"line_number": "11", "description": "floor(Line 10 / 1,000) [ROUND DOWN]", "line_type": "calculated", "source_rules": ["R-TIPS-06"], "sort_order": 19},
    {"line_number": "12", "description": "Line 11 × $100", "line_type": "calculated", "source_rules": ["R-TIPS-06"], "sort_order": 20},
    {"line_number": "13", "description": "Tips deduction — max(0, Line 7 − Line 12)", "line_type": "total", "source_rules": ["R-TIPS-07"], "sort_order": 21},

    # ── Part III — Overtime ──
    {"line_number": "14a", "description": "Qualified overtime — W-2 box 1 (FLSA premium only)", "line_type": "input", "sort_order": 30},
    {"line_number": "14b", "description": "Qualified overtime — 1099-NEC box1 / 1099-MISC box3", "line_type": "input", "sort_order": 31},
    {"line_number": "14c", "description": "Line 14a + Line 14b", "line_type": "subtotal", "source_rules": ["R-OT-01"], "sort_order": 32},
    {"line_number": "15", "description": "Overtime cap — min(Line 14c, $12,500 / $25,000 MFJ)", "line_type": "calculated", "source_rules": ["R-OT-02"], "sort_order": 33},
    {"line_number": "16", "description": "MAGI (from Line 3)", "line_type": "calculated", "source_rules": ["R-OT-04"], "sort_order": 34},
    {"line_number": "17", "description": "Threshold ($150,000 / $300,000 MFJ)", "line_type": "calculated", "source_rules": ["R-OT-03"], "sort_order": 35},
    {"line_number": "18", "description": "Line 16 − Line 17 (if ≤ 0, deduction = Line 15)", "line_type": "calculated", "source_rules": ["R-OT-04"], "sort_order": 36},
    {"line_number": "19", "description": "floor(Line 18 / 1,000) [ROUND DOWN]", "line_type": "calculated", "source_rules": ["R-OT-05"], "sort_order": 37},
    {"line_number": "20", "description": "Line 19 × $100", "line_type": "calculated", "source_rules": ["R-OT-05"], "sort_order": 38},
    {"line_number": "21", "description": "Overtime deduction — max(0, Line 15 − Line 20)", "line_type": "total", "source_rules": ["R-OT-06"], "sort_order": 39},

    # ── Part IV — Car Loan / QPVLI ──
    {"line_number": "22", "description": "Per-vehicle rows a/b: (i) VIN, (ii) amount deducted on Sch C/E/F, (iii) Schedule 1-A amount = total QPVLI paid 2025 − col (ii)", "line_type": "input", "sort_order": 40},
    {"line_number": "23", "description": "Sum of column (iii)", "line_type": "subtotal", "source_rules": ["R-CAR-01"], "sort_order": 41},
    {"line_number": "24", "description": "Car loan cap — min(Line 23, $10,000)", "line_type": "calculated", "source_rules": ["R-CAR-02"], "sort_order": 42},
    {"line_number": "25", "description": "MAGI (from Line 3)", "line_type": "calculated", "source_rules": ["R-CAR-04"], "sort_order": 43},
    {"line_number": "26", "description": "Threshold ($100,000 / $200,000 MFJ)", "line_type": "calculated", "source_rules": ["R-CAR-03"], "sort_order": 44},
    {"line_number": "27", "description": "Line 25 − Line 26 (if ≤ 0, deduction = Line 24)", "line_type": "calculated", "source_rules": ["R-CAR-04"], "sort_order": 45},
    {"line_number": "28", "description": "ceil(Line 27 / 1,000) [ROUND UP — opposite of tips/overtime]", "line_type": "calculated", "source_rules": ["R-CAR-05"], "sort_order": 46},
    {"line_number": "29", "description": "Line 28 × $200", "line_type": "calculated", "source_rules": ["R-CAR-05"], "sort_order": 47},
    {"line_number": "30", "description": "QPVLI deduction — max(0, Line 24 − Line 29). NOTE: tts-tax-app stubs this at 0.", "line_type": "total", "source_rules": ["R-CAR-06"], "sort_order": 48},

    # ── Part V — Senior ──
    {"line_number": "31", "description": "MAGI (from Line 3)", "line_type": "calculated", "source_rules": ["R-SEN-02"], "sort_order": 50},
    {"line_number": "32", "description": "Threshold ($75,000 / $150,000 MFJ)", "line_type": "calculated", "source_rules": ["R-SEN-01"], "sort_order": 51},
    {"line_number": "33", "description": "Line 31 − Line 32 (if ≤ 0, enter $6,000 on Line 35)", "line_type": "calculated", "source_rules": ["R-SEN-02"], "sort_order": 52},
    {"line_number": "34", "description": "Line 33 × 6% (0.06) [CONTINUOUS — no rounding]", "line_type": "calculated", "source_rules": ["R-SEN-03"], "sort_order": 53},
    {"line_number": "35", "description": "max(0, $6,000 − Line 34)", "line_type": "calculated", "source_rules": ["R-SEN-04"], "sort_order": 54},
    {"line_number": "36a", "description": "Line 35 if taxpayer has valid SSN AND born before Jan 2 of (tax_year−64)", "line_type": "calculated", "source_rules": ["R-SEN-05"], "sort_order": 55},
    {"line_number": "36b", "description": "Line 35 if MFJ AND spouse has valid SSN AND spouse born before Jan 2 of (tax_year−64)", "line_type": "calculated", "source_rules": ["R-SEN-06"], "sort_order": 56},
    {"line_number": "37", "description": "Enhanced senior deduction (Line 36a + Line 36b)", "line_type": "total", "source_rules": ["R-SEN-07"], "sort_order": 57},

    # ── Part VI — Total ──
    {"line_number": "38", "description": "Total additional deductions (Line 13 + 21 + 30 + 37)", "line_type": "total",
     "source_rules": ["R-TOT-01"], "destination_form": "Form 1040/1040-SR line 13b (Form 1040-NR line 13c)", "sort_order": 60},
]


# ═══════════════════════════════════════════════════════════════════════════
# DIAGNOSTICS
# severity ∈ {error, warning, info}. Severities are Ken's calls; supplied effect
# words map as BLOCK→error, NOT QUALIFIED(+flag)→warning, WARNING→warning.
# ═══════════════════════════════════════════════════════════════════════════

FORM_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_SCH1A_001", "title": "MFS claiming tips/overtime/senior", "severity": "error",
     "condition": "filing_status == 'mfs' AND (tips_deduction > 0 OR overtime_deduction > 0 OR senior_deduction > 0)",
     "message": "Married filing separately is ineligible for the tips, overtime, and senior deductions. Claim blocked.",
     "notes": "Supplied effect: BLOCK. (Severity Ken's call.)"},
    {"diagnostic_id": "D_SCH1A_002", "title": "Missing SSN where required", "severity": "error",
     "condition": "NOT taxpayer_has_valid_ssn AND (tips_deduction > 0 OR overtime_deduction > 0 OR senior_deduction > 0)",
     "message": "A valid SSN is required to claim the tips, overtime, or senior deduction. Claim blocked.",
     "notes": "Supplied effect: BLOCK. (Severity Ken's call.)"},
    {"diagnostic_id": "D_SCH1A_003", "title": "Tips occupation not on the IRS list", "severity": "warning",
     "condition": "tips_occupation_on_irs_list == False AND (tips_w2_box_7 > 0 OR tips_form_4137_line_1 > 0 OR tips_trade_business > 0)",
     "message": "Tips were received in an occupation not on the IRS qualified-occupation list (§224(d)(1)). Those tips are NOT qualified — exclude them.",
     "notes": "Supplied effect: NOT QUALIFIED (exclude those tips; flag). (Severity Ken's call.)"},
    {"diagnostic_id": "D_SCH1A_004", "title": "Senior claimant born on/after the cutoff", "severity": "warning",
     "condition": "claiming senior AND born on/after Jan 2 of (tax_year − 64)",
     "message": "An individual claiming the senior deduction was born on/after Jan 2 of (tax_year − 64). That individual's senior amount is $0.",
     "notes": "Supplied effect: NOT QUALIFIED (that individual's senior amount = 0; flag). (Severity Ken's call.)"},
    {"diagnostic_id": "D_SCH1A_005", "title": "Tips with W-2 box 5 over $176,100", "severity": "warning",
     "condition": "tips_w2_box_5_medicare_wages > 176100 AND (tips_w2_box_7 > 0 OR tips_form_4137_line_1 > 0)",
     "message": "W-2 box 5 (Medicare wages) exceeds $176,100 — route to special handling for the tips deduction.",
     "notes": "Supplied effect: WARNING (route to special handling). (Severity Ken's call.)"},
    {"diagnostic_id": "D_SCH1A_006", "title": "Multiple-employer or multiple-occupation tips", "severity": "warning",
     "condition": "tips_multiple_employers_or_occupations == True",
     "message": "Tips span multiple employers or occupations — route to the Schedule 1-A instructions for allocation.",
     "notes": "Supplied effect: WARNING (route to instructions). (Severity Ken's call.)"},
]


# ═══════════════════════════════════════════════════════════════════════════
# TEST SCENARIOS
# NOT SUPPLIED in this authoring session. Left as an explicit TODO rather than
# guessed (per the standing rule: flag missing content, do not invent values).
# Ken adds verified input/expected pairs before relying on these.
# ═══════════════════════════════════════════════════════════════════════════

# 21 scenarios (Session 17). Expected values TRANSCRIBED VERBATIM — computed
# independently from the authoritative 2025 Schedule 1-A line math and reviewed by
# Ken; they exist to VALIDATE the rules, so they are NOT derived from the rules here.
#
# Input-key conventions (per task STEP 2):
#   - MAGI is set with no foreign add-backs: "agi_1040_line_11b" = MAGI and the four
#     exclusion facts = 0, so L3 (R-MAGI-02) computes to MAGI.
#   - Part aggregate inputs are injected at the line level the task specifies:
#       Tips → "6" (L6);  Overtime → "14c" (L14c);  Car loan → "23" (L23, col iii total).
#   - Senior uses MAGI + DOB(s): "taxpayer_dob" / "spouse_dob" (ISO date), so the
#     born-before-Jan-2-1961 (TY2025) cutoff is exercised, not pre-computed.
#   - "taxpayer_has_valid_ssn"/"spouse_has_valid_ssn" = True and non-MFS status are the
#     standing eligibility preconditions (Session-16 common gates) so the math is
#     exercised rather than blocked.
# Expected-output keys are the form's output line numbers: Tips "13", Overtime "21",
# Car "30", Senior "37", Total "38" (Total also asserts components 13/21/30/37).
TEST_SCENARIOS: list[dict] = [
    # ── Part II — Tips (assert L13) ──
    {"scenario_name": "T1 — single, tips $12,000, MAGI $90,000 → L13 $12,000",
     "scenario_type": "normal", "sort_order": 1,
     "inputs": {"filing_status": "single", "taxpayer_has_valid_ssn": True,
                "agi_1040_line_11b": 90000, "pr_excluded_income": 0, "feie_2555_line_45": 0,
                "housing_2555_line_50": 0, "american_samoa_4563_line_15": 0, "6": 12000},
     "expected_outputs": {"13": 12000},
     "notes": "Below cap and below phaseout threshold. Verbatim expected value (Ken-reviewed)."},
    {"scenario_name": "T2 — single, tips $30,000, MAGI $120,000 → L13 $25,000",
     "scenario_type": "normal", "sort_order": 2,
     "inputs": {"filing_status": "single", "taxpayer_has_valid_ssn": True,
                "agi_1040_line_11b": 120000, "pr_excluded_income": 0, "feie_2555_line_45": 0,
                "housing_2555_line_50": 0, "american_samoa_4563_line_15": 0, "6": 30000},
     "expected_outputs": {"13": 25000},
     "notes": "$25,000 cap binds; below phaseout threshold. Verbatim (Ken-reviewed)."},
    {"scenario_name": "T3 — single, tips $30,000, MAGI $163,400 → L13 $23,700",
     "scenario_type": "normal", "sort_order": 3,
     "inputs": {"filing_status": "single", "taxpayer_has_valid_ssn": True,
                "agi_1040_line_11b": 163400, "pr_excluded_income": 0, "feie_2555_line_45": 0,
                "housing_2555_line_50": 0, "american_samoa_4563_line_15": 0, "6": 30000},
     "expected_outputs": {"13": 23700},
     "notes": "Cap $25,000 then phaseout (round DOWN ×$100). Verbatim (Ken-reviewed)."},
    {"scenario_name": "T4 — MFJ, tips $20,000, MAGI $312,500 → L13 $18,800",
     "scenario_type": "normal", "sort_order": 4,
     "inputs": {"filing_status": "mfj", "taxpayer_has_valid_ssn": True, "spouse_has_valid_ssn": True,
                "agi_1040_line_11b": 312500, "pr_excluded_income": 0, "feie_2555_line_45": 0,
                "housing_2555_line_50": 0, "american_samoa_4563_line_15": 0, "6": 20000},
     "expected_outputs": {"13": 18800},
     "notes": "MFJ threshold $300,000; phaseout round DOWN ×$100. Verbatim (Ken-reviewed)."},
    {"scenario_name": "T5 — single, tips $25,000, MAGI $400,000 → L13 $0",
     "scenario_type": "edge", "sort_order": 5,
     "inputs": {"filing_status": "single", "taxpayer_has_valid_ssn": True,
                "agi_1040_line_11b": 400000, "pr_excluded_income": 0, "feie_2555_line_45": 0,
                "housing_2555_line_50": 0, "american_samoa_4563_line_15": 0, "6": 25000},
     "expected_outputs": {"13": 0},
     "notes": "Phaseout fully eliminates the deduction. Verbatim (Ken-reviewed)."},

    # ── Part III — Overtime (assert L21) ──
    {"scenario_name": "O1 — single, overtime $8,000, MAGI $100,000 → L21 $8,000",
     "scenario_type": "normal", "sort_order": 6,
     "inputs": {"filing_status": "single", "taxpayer_has_valid_ssn": True,
                "agi_1040_line_11b": 100000, "pr_excluded_income": 0, "feie_2555_line_45": 0,
                "housing_2555_line_50": 0, "american_samoa_4563_line_15": 0, "14c": 8000},
     "expected_outputs": {"21": 8000},
     "notes": "Below cap and threshold. Verbatim (Ken-reviewed)."},
    {"scenario_name": "O2 — MFJ, overtime $30,000, MAGI $310,000 → L21 $24,000",
     "scenario_type": "normal", "sort_order": 7,
     "inputs": {"filing_status": "mfj", "taxpayer_has_valid_ssn": True, "spouse_has_valid_ssn": True,
                "agi_1040_line_11b": 310000, "pr_excluded_income": 0, "feie_2555_line_45": 0,
                "housing_2555_line_50": 0, "american_samoa_4563_line_15": 0, "14c": 30000},
     "expected_outputs": {"21": 24000},
     "notes": "MFJ cap $25,000 then phaseout (round DOWN ×$100). Verbatim (Ken-reviewed)."},
    {"scenario_name": "O3 — single, overtime $12,500, MAGI $158,700 → L21 $11,700",
     "scenario_type": "normal", "sort_order": 8,
     "inputs": {"filing_status": "single", "taxpayer_has_valid_ssn": True,
                "agi_1040_line_11b": 158700, "pr_excluded_income": 0, "feie_2555_line_45": 0,
                "housing_2555_line_50": 0, "american_samoa_4563_line_15": 0, "14c": 12500},
     "expected_outputs": {"21": 11700},
     "notes": "Single cap $12,500 then phaseout (round DOWN ×$100). Verbatim (Ken-reviewed)."},

    # ── Part IV — Car Loan / QPVLI (assert L30) — ceil() rounding ──
    {"scenario_name": "C1 — single, QPVLI $6,000, MAGI $90,000 → L30 $6,000",
     "scenario_type": "normal", "sort_order": 9,
     "inputs": {"filing_status": "single", "taxpayer_has_valid_ssn": True,
                "agi_1040_line_11b": 90000, "pr_excluded_income": 0, "feie_2555_line_45": 0,
                "housing_2555_line_50": 0, "american_samoa_4563_line_15": 0, "23": 6000},
     "expected_outputs": {"30": 6000},
     "notes": "Below cap and threshold. Verbatim (Ken-reviewed)."},
    {"scenario_name": "C2 — single, QPVLI $8,000, MAGI $103,500 → L30 $7,200",
     "scenario_type": "edge", "sort_order": 10,
     "inputs": {"filing_status": "single", "taxpayer_has_valid_ssn": True,
                "agi_1040_line_11b": 103500, "pr_excluded_income": 0, "feie_2555_line_45": 0,
                "housing_2555_line_50": 0, "american_samoa_4563_line_15": 0, "23": 8000},
     "expected_outputs": {"30": 7200},
     "notes": "ROUND-UP edge: excess 3500 → ceil 4 × $200 = 800. Verbatim (Ken-reviewed)."},
    {"scenario_name": "C3 — MFJ, QPVLI $12,000, MAGI $222,000 → L30 $5,600",
     "scenario_type": "normal", "sort_order": 11,
     "inputs": {"filing_status": "mfj", "taxpayer_has_valid_ssn": True, "spouse_has_valid_ssn": True,
                "agi_1040_line_11b": 222000, "pr_excluded_income": 0, "feie_2555_line_45": 0,
                "housing_2555_line_50": 0, "american_samoa_4563_line_15": 0, "23": 12000},
     "expected_outputs": {"30": 5600},
     "notes": "MFJ threshold $200,000; cap $10,000 then phaseout (round UP ×$200). Verbatim (Ken-reviewed)."},
    {"scenario_name": "C4 — single, QPVLI $10,000, MAGI $150,000 → L30 $0",
     "scenario_type": "edge", "sort_order": 12,
     "inputs": {"filing_status": "single", "taxpayer_has_valid_ssn": True,
                "agi_1040_line_11b": 150000, "pr_excluded_income": 0, "feie_2555_line_45": 0,
                "housing_2555_line_50": 0, "american_samoa_4563_line_15": 0, "23": 10000},
     "expected_outputs": {"30": 0},
     "notes": "Phaseout fully eliminates the deduction. Verbatim (Ken-reviewed)."},

    # ── Part V — Senior (assert L37) — TY2025 cutoff: born BEFORE Jan 2, 1961 qualifies ──
    {"scenario_name": "S1 — single, MAGI $60,000, DOB 1960-06-01 → L37 $6,000",
     "scenario_type": "normal", "sort_order": 13,
     "inputs": {"filing_status": "single", "taxpayer_has_valid_ssn": True,
                "agi_1040_line_11b": 60000, "pr_excluded_income": 0, "feie_2555_line_45": 0,
                "housing_2555_line_50": 0, "american_samoa_4563_line_15": 0,
                "taxpayer_dob": "1960-06-01"},
     "expected_outputs": {"37": 6000},
     "notes": "Below threshold; full $6,000. Verbatim (Ken-reviewed)."},
    {"scenario_name": "S2 — single, MAGI $80,000, DOB 1960-06-01 → L37 $5,700",
     "scenario_type": "normal", "sort_order": 14,
     "inputs": {"filing_status": "single", "taxpayer_has_valid_ssn": True,
                "agi_1040_line_11b": 80000, "pr_excluded_income": 0, "feie_2555_line_45": 0,
                "housing_2555_line_50": 0, "american_samoa_4563_line_15": 0,
                "taxpayer_dob": "1960-06-01"},
     "expected_outputs": {"37": 5700},
     "notes": "Continuous 6% phaseout (no rounding). Verbatim (Ken-reviewed)."},
    {"scenario_name": "S3 — MFJ, MAGI $200,000, both DOB 1960-06-01 → L37 $6,000 (per-spouse)",
     "scenario_type": "normal", "sort_order": 15,
     "inputs": {"filing_status": "mfj", "taxpayer_has_valid_ssn": True, "spouse_has_valid_ssn": True,
                "agi_1040_line_11b": 200000, "pr_excluded_income": 0, "feie_2555_line_45": 0,
                "housing_2555_line_50": 0, "american_samoa_4563_line_15": 0,
                "taxpayer_dob": "1960-06-01", "spouse_dob": "1960-06-01"},
     "expected_outputs": {"37": 6000},
     "notes": "MFJ threshold $150,000; L35 $3,000 claimed per qualifying spouse (×2). Verbatim (Ken-reviewed)."},
    {"scenario_name": "S4 — MFJ, MAGI $160,000, TP 1960-06-01 / SP 1965-03-01 → L37 $5,400 (one spouse)",
     "scenario_type": "normal", "sort_order": 16,
     "inputs": {"filing_status": "mfj", "taxpayer_has_valid_ssn": True, "spouse_has_valid_ssn": True,
                "agi_1040_line_11b": 160000, "pr_excluded_income": 0, "feie_2555_line_45": 0,
                "housing_2555_line_50": 0, "american_samoa_4563_line_15": 0,
                "taxpayer_dob": "1960-06-01", "spouse_dob": "1965-03-01"},
     "expected_outputs": {"37": 5400},
     "notes": "Only the taxpayer qualifies by age; spouse (1965) does not. Verbatim (Ken-reviewed)."},
    {"scenario_name": "S5 — single, MAGI $60,000, DOB 1961-01-01 → L37 $6,000 (boundary: qualifies)",
     "scenario_type": "edge", "sort_order": 17,
     "inputs": {"filing_status": "single", "taxpayer_has_valid_ssn": True,
                "agi_1040_line_11b": 60000, "pr_excluded_income": 0, "feie_2555_line_45": 0,
                "housing_2555_line_50": 0, "american_samoa_4563_line_15": 0,
                "taxpayer_dob": "1961-01-01"},
     "expected_outputs": {"37": 6000},
     "notes": "Boundary: born before Jan 2, 1961 → qualifies. Verbatim (Ken-reviewed)."},
    {"scenario_name": "S6 — single, MAGI $60,000, DOB 1961-01-02 → L37 $0 (boundary: NOT before Jan 2)",
     "scenario_type": "edge", "sort_order": 18,
     "inputs": {"filing_status": "single", "taxpayer_has_valid_ssn": True,
                "agi_1040_line_11b": 60000, "pr_excluded_income": 0, "feie_2555_line_45": 0,
                "housing_2555_line_50": 0, "american_samoa_4563_line_15": 0,
                "taxpayer_dob": "1961-01-02"},
     "expected_outputs": {"37": 0},
     "notes": "Boundary: NOT born before Jan 2, 1961 → does not qualify. Verbatim (Ken-reviewed)."},
    {"scenario_name": "S7 — single, MAGI $175,000, DOB 1960-06-01 → L37 $0 (income zero-out)",
     "scenario_type": "edge", "sort_order": 19,
     "inputs": {"filing_status": "single", "taxpayer_has_valid_ssn": True,
                "agi_1040_line_11b": 175000, "pr_excluded_income": 0, "feie_2555_line_45": 0,
                "housing_2555_line_50": 0, "american_samoa_4563_line_15": 0,
                "taxpayer_dob": "1960-06-01"},
     "expected_outputs": {"37": 0},
     "notes": "Continuous 6% phaseout reduces $6,000 to $0 at this MAGI. Verbatim (Ken-reviewed)."},

    # ── Part VI — Total (assert L13/L21/L30/L37/L38 → Form 1040 line 13b) ──
    {"scenario_name": "TOT1 — single, MAGI $70,000, DOB 1960-06-01, tips $10,000 / OT $5,000 / QPVLI $4,000 → L38 $25,000",
     "scenario_type": "normal", "sort_order": 20,
     "inputs": {"filing_status": "single", "taxpayer_has_valid_ssn": True,
                "agi_1040_line_11b": 70000, "pr_excluded_income": 0, "feie_2555_line_45": 0,
                "housing_2555_line_50": 0, "american_samoa_4563_line_15": 0,
                "taxpayer_dob": "1960-06-01", "6": 10000, "14c": 5000, "23": 4000},
     "expected_outputs": {"13": 10000, "21": 5000, "30": 4000, "37": 6000, "38": 25000},
     "notes": "All four parts active; L38 → Form 1040 line 13b. Verbatim (Ken-reviewed)."},
    {"scenario_name": "TOT2 — single, MAGI $160,000, DOB 1960-06-01, tips $30,000 → L38 $24,900",
     "scenario_type": "normal", "sort_order": 21,
     "inputs": {"filing_status": "single", "taxpayer_has_valid_ssn": True,
                "agi_1040_line_11b": 160000, "pr_excluded_income": 0, "feie_2555_line_45": 0,
                "housing_2555_line_50": 0, "american_samoa_4563_line_15": 0,
                "taxpayer_dob": "1960-06-01", "6": 30000, "14c": 0, "23": 0},
     "expected_outputs": {"13": 24000, "21": 0, "30": 0, "37": 900, "38": 24900},
     "notes": "Tips phaseout + senior phaseout both active; L38 → Form 1040 line 13b. Verbatim (Ken-reviewed)."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-SCH1A-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "SCH_1A line 38 must equal Form 1040 line 13b",
     "description": "Cross-form flow. Validates R-TOT-01. Bug it catches: senior deduction computed but never written to the 1040.",
     "definition": {"form": "SCH_1A", "kind": "cross_form_flow"},
     "sort_order": 1},
    {"assertion_id": "FA-SCH1A-02", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "SCH_1A line 38 == line 13 + line 21 + line 30 + line 37",
     "description": "Part VI reconciliation. Validates R-TOT-01 internal sum. Bug it catches: Parts II-IV stubs leak non-zero values; line 37 not added.",
     "definition": {"form": "SCH_1A", "kind": "sum_check"},
     "sort_order": 2},
    {"assertion_id": "FA-SCH1A-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Form 1040 line 14 formula must include 13b",
     "description": "Cross-form flow check. Validates that the 1040 deductions subtotal includes the senior deduction. Bug it catches: 13b orphaned (computed but never propagated into taxable income).",
     "definition": {"form": "SCH_1A", "kind": "formula_check"},
     "sort_order": 3},
    {"assertion_id": "FA-SCH1A-04", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "0 <= senior_deduction <= 12000; per_person <= 6000",
     "description": "Universal bound. Bug it catches: phaseout sign-flip; double-application of per-person amount.",
     "definition": {"form": "SCH_1A", "kind": "invariant"},
     "sort_order": 4},
    {"assertion_id": "FA-SCH1A-05", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "senior_deduction == 0 at/above elimination point (175K single / 250K MFJ)",
     "description": "Phaseout elimination invariant. Bug it catches: phaseout cap missing \u2014 deduction goes negative or stays positive past elimination.",
     "definition": {"form": "SCH_1A", "kind": "elimination_check"},
     "sort_order": 5},
    {"assertion_id": "FA-SCH1A-06", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "spouse_amount (line 36b) == 0 whenever filing_status != MFJ",
     "description": "MFJ gate. Validates R-SEN-07 filing-status precondition. Bug it catches: single/HOH/MFS filer accidentally getting 2x deduction.",
     "definition": {"form": "SCH_1A", "kind": "mfj_gate_check"},
     "sort_order": 6},
    {"assertion_id": "FA-SCH1A-TIPS-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Tips deduction (line 13) capped at $25,000 (line 7)",
     "description": "Validates the per-return cap. Bug it catches: cap removed or applied per-spouse.",
     "definition": {"form": "SCH_1A", "kind": "tips_cap_check"},
     "sort_order": 7},
    {"assertion_id": "FA-SCH1A-TIPS-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Tips phaseout rounds DOWN (vs Schedule 8812 which rounds UP)",
     "description": "Validates ROUND_DOWN behavior on line 11. Bug it catches: ceil/floor confusion between Schedule 8812 and Schedule 1-A.",
     "definition": {"form": "SCH_1A", "kind": "tips_rounding_check"},
     "sort_order": 8},
    {"assertion_id": "FA-SCH1A-TIPS-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Tips ineligible filers (no valid SSN, not attesting, MFS) get $0",
     "description": "Validates the eligibility gates. Bug it catches: gate skipped \u2014 disqualified filer still gets deduction.",
     "definition": {"form": "SCH_1A", "kind": "tips_eligibility_gates"},
     "sort_order": 9},
    {"assertion_id": "FA-SCH1A-TIPS-04", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "Tips deduction (L_13) contributes to Part VI total (L_38)",
     "description": "Validates the Part VI sum picks up Part II output (not just Part V). Bug it catches: L_38 = L_37 (only senior) when tips claimed.",
     "definition": {"form": "SCH_1A", "kind": "tips_in_part_vi_sum"},
     "sort_order": 10},
    {"assertion_id": "FA-SCH1A-OT-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Overtime deduction (line 21) capped at line 15 ($12,500 / $25,000 MFJ)",
     "description": "Validates the Part III cap, which DOUBLES for MFJ (unlike the flat tips cap). Bug it catches: cap removed, wrong cap, or MFJ doubling dropped.",
     "definition": {"form": "SCH_1A", "kind": "overtime_cap_check"},
     "sort_order": 11},
    {"assertion_id": "FA-SCH1A-OT-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Overtime phaseout rounds DOWN (line 19)",
     "description": "Validates ROUND_DOWN on line 19 (divide by $1,000, decrease to next lower whole number). Bug it catches: ceil/floor confusion vs Schedule 8812 (which rounds UP).",
     "definition": {"form": "SCH_1A", "kind": "overtime_rounding_check"},
     "sort_order": 12},
    {"assertion_id": "FA-SCH1A-OT-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Overtime ineligible filers (no valid SSN, MFS) get $0",
     "description": "Validates the Part III eligibility gates: valid SSN required, MFS short-circuits to 0. Note overtime has NO occupation/SSTB attestation (unlike tips). Bug it catches: gate skipped.",
     "definition": {"form": "SCH_1A", "kind": "overtime_eligibility_gates"},
     "sort_order": 13},
    {"assertion_id": "FA-SCH1A-OT-04", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "Overtime deduction (L_21) contributes to Part VI total (L_38)",
     "description": "Validates the Part VI sum picks up Part III output sourced from compute (not the old stub FormFieldValue read). Bug it catches: L_38 ignores L_21, or L_21 still read from the seeded stub.",
     "definition": {"form": "SCH_1A", "kind": "overtime_in_part_vi_sum"},
     "sort_order": 14},
    # Legacy-id records 05/06/07 are RETAINED — the canonical tts gate file
    # still carries them (only 01..04 were superseded/renamed).
    {"assertion_id": "FA-1040-SCH1A-05", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Car loan phaseout rounds the $1,000 excess UP, x$200 (opposite of II/III)",
     "description": "Validates R-CAR-05. L28 = ceil(L27/1000); L29 = L28 x $200. Bug it catches: copying the tips/overtime floor x$100 mechanics into Part IV \u2014 OBBBA sibling provisions do NOT share rounding.",
     "definition": {"form": "SCH_1A", "kind": "rounding_check", "line": "L28", "behavior": "ceiling_to_1000", "multiplier": 200, "reduction_line": "L29"},
     "sort_order": 15},
    {"assertion_id": "FA-1040-SCH1A-06", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Senior phaseout is continuous 6% (no rounding); one phaseout, per qualifying spouse",
     "description": "Validates R-SEN-03/04/05/06/07. L34 = L33 x 0.06 with NO bracket rounding; L35 computed once; L37 = L36a + L36b claimed per qualifying spouse. Bug it catches: bracket rounding sneaking into the senior phaseout, or the phaseout computed per-spouse.",
     "definition": {"form": "SCH_1A", "kind": "formula_check", "formula": "L34 == L33 * 0.06 (continuous) AND L35 == max(0, 6000 - L34) AND L37 == L36a + L36b", "no_rounding": True, "per_qualifying_spouse": True},
     "sort_order": 16},
    {"assertion_id": "FA-1040-SCH1A-07", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Parts II/III/IV are cap-first, then phaseout",
     "description": "Validates ordering for tips/overtime/car-loan: the cap (L7/L15/L24) is applied BEFORE the MAGI phaseout reduction is subtracted. Bug it catches: phaseout applied to the uncapped amount (overstates the deduction for high earners over the cap).",
     "definition": {"form": "SCH_1A", "kind": "ordering_check", "sequence": [{"part": "II", "cap_line": "L7", "then_phaseout_line": "L12", "result_line": "L13"}, {"part": "III", "cap_line": "L15", "then_phaseout_line": "L20", "result_line": "L21"}, {"part": "IV", "cap_line": "L24", "then_phaseout_line": "L29", "result_line": "L30"}]},
     "sort_order": 17},
]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY FORM LINKS  (source_code, link_type)
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_FORM_LINKS: list[tuple[str, str]] = [
    ("IRS_2025_SCH_1A_FORM", "governs"),
    ("IRC_224", "governs"),
    ("IRC_225", "governs"),
    ("IRC_163", "governs"),
    ("IRC_151", "governs"),
    ("IRC_63", "governs"),
    ("IRC_911", "informs"),
    ("IRC_931", "informs"),
    ("IRC_933", "informs"),
    ("IRC_6041", "informs"),
    ("IRC_6051", "informs"),
    ("IRC_6050AA", "informs"),
    ("USC_29_207", "informs"),
    ("PL_119_21_70103", "governs"),
    ("PL_119_21_70201", "governs"),
    ("PL_119_21_70202", "governs"),
    ("PL_119_21_70203", "governs"),
    ("IRS_NOTICE_2025_69", "informs"),
    ("IRS_REG_110032_25", "informs"),
    ("IRS_REG_113515_25", "informs"),
    ("IRS_IR_2025_129", "informs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# Command
# ═══════════════════════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = (
        "Load Schedule 1-A (SCH_1A) spec into Rule Studio. "
        "Content authored (Session 16); refuses to seed until Ken sets READY_TO_SEED=True."
    )

    # The minimum-content gate. The form is structurally hollow without at least
    # one entry in each of these. Adjust this list if/when authoring intentionally
    # leaves a category empty (e.g. no diagnostics for a given form).
    REQUIRED_CONTENT_LISTS: tuple[tuple[str, list], ...] = (
        ("AUTHORITY_SOURCES",     AUTHORITY_SOURCES),
        ("FORM_RULES",            FORM_RULES),
        ("FORM_LINES",            FORM_LINES),
        ("RULE_AUTHORITY_LINKS",  RULE_AUTHORITY_LINKS),
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        # ─── SAFETY GUARD — runs BEFORE any DB operation ────────────────────
        self._guard_against_hollow_seed()
        # ─── End guard ──────────────────────────────────────────────────────

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\nLoad {FORM_NUMBER} spec\n"
        ))

        self._load_topics()
        sources = self._load_sources()
        self._load_new_excerpts_on_existing(sources)
        form = self._upsert_form()
        self._upsert_facts(form)
        rules = self._upsert_rules(form)
        self._upsert_authority_links(rules, sources)
        self._upsert_lines(form)
        self._upsert_diagnostics(form)
        self._upsert_tests(form)
        self._upsert_form_links(sources)
        self._load_flow_assertions()
        self._report_totals()

    # ─────────────────────────────────────────────────────────────────────────
    # Safety guard
    # ─────────────────────────────────────────────────────────────────────────

    def _guard_against_hollow_seed(self):
        """Refuse to write anything until Ken has authored content AND flipped READY_TO_SEED."""
        empty = [name for name, lst in self.REQUIRED_CONTENT_LISTS if not lst]

        # Title check — placeholder strings must be replaced.
        title_is_placeholder = "[TODO" in FORM_TITLE
        if title_is_placeholder:
            empty.append("FORM_TITLE (still a [TODO] placeholder)")

        if not READY_TO_SEED or empty:
            checklist = "\n  ".join(f"- {name}" for name, lst in self.REQUIRED_CONTENT_LISTS) or "(none required)"
            still_empty = "\n  ".join(f"- {n}" for n in empty) or "(all populated)"
            raise CommandError(
                "\n"
                f"REFUSING TO SEED {FORM_NUMBER}: not cleared to seed.\n"
                "\n"
                "Content is authored (Session 16), but seeding is gated until Ken reviews\n"
                "and flips the sentinel. This guard prevents an unreviewed or hollow form\n"
                "from registering — an empty/unverified spec that resolves would falsely\n"
                "satisfy tts-tax-app's spec-first gate ('stop if no spec').\n"
                "\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True to proceed)\n"
                "\n"
                "Content checklist (required lists):\n"
                f"  {checklist}\n"
                "\n"
                "Currently empty / placeholder:\n"
                f"  {still_empty}\n"
                "\n"
                "To proceed: review the module-level data lists at the top of this file,\n"
                "then set READY_TO_SEED = True. Idempotent via update_or_create — safe to\n"
                "re-run after edits."
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Topics
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

    # ─────────────────────────────────────────────────────────────────────────
    # Sources
    # ─────────────────────────────────────────────────────────────────────────

    def _load_sources(self) -> dict[str, AuthoritySource]:
        sources: dict[str, AuthoritySource] = {}
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
        self.stdout.write(f"Sources ready: {len(sources)}")
        return sources

    def _load_new_excerpts_on_existing(self, sources):
        ct = 0
        for code, exc in NEW_EXCERPTS_ON_EXISTING:
            src = sources.get(code) or AuthoritySource.objects.filter(source_code=code).first()
            if not src:
                self.stdout.write(self.style.WARNING(
                    f"  source {code} not found — skipping new excerpt"
                ))
                continue
            exc = dict(exc)
            AuthorityExcerpt.objects.update_or_create(
                authority_source=src, excerpt_label=exc["excerpt_label"], defaults=exc,
            )
            ct += 1
        if ct:
            self.stdout.write(f"  {ct} new excerpts on existing sources")

    # ─────────────────────────────────────────────────────────────────────────
    # Form helpers (mirror load_1040_ctc.py exactly)
    # ─────────────────────────────────────────────────────────────────────────

    def _upsert_form(self) -> TaxForm:
        form, created = TaxForm.objects.update_or_create(
            form_number=FORM_NUMBER,
            jurisdiction=FORM_JURISDICTION,
            tax_year=FORM_TAX_YEAR,
            version=FORM_VERSION,
            defaults={
                "form_title": FORM_TITLE,
                "entity_types": FORM_ENTITY_TYPES,
                "status": FORM_STATUS,
                "notes": FORM_NOTES,
            },
        )
        self.stdout.write(f"{'Created' if created else 'Updated'} {FORM_NUMBER}")
        return form

    def _upsert_facts(self, form):
        for f in FORM_FACTS:
            f = dict(f)
            FormFact.objects.update_or_create(
                tax_form=form, fact_key=f.pop("fact_key"), defaults=f,
            )
        self.stdout.write(f"  {len(FORM_FACTS)} facts")

    def _upsert_rules(self, form) -> dict[str, FormRule]:
        created = {}
        for r in FORM_RULES:
            r = dict(r)
            rule, _ = FormRule.objects.update_or_create(
                tax_form=form, rule_id=r.pop("rule_id"), defaults=r,
            )
            created[rule.rule_id] = rule
        self.stdout.write(f"  {len(created)} rules")
        return created

    def _upsert_authority_links(self, rules, sources):
        ct = 0
        for rule_id, source_code, level, note in RULE_AUTHORITY_LINKS:
            rule, source = rules.get(rule_id), sources.get(source_code)
            if rule and source:
                RuleAuthorityLink.objects.get_or_create(
                    form_rule=rule, authority_source=source,
                    defaults={"support_level": level, "relevance_note": note},
                )
                ct += 1
        self.stdout.write(f"  {ct} authority links")

    def _upsert_lines(self, form):
        for ln in FORM_LINES:
            ln = dict(ln)
            FormLine.objects.update_or_create(
                tax_form=form, line_number=ln.pop("line_number"), defaults=ln,
            )
        self.stdout.write(f"  {len(FORM_LINES)} lines")

    def _upsert_diagnostics(self, form):
        for d in FORM_DIAGNOSTICS:
            d = dict(d)
            FormDiagnostic.objects.update_or_create(
                tax_form=form, diagnostic_id=d.pop("diagnostic_id"), defaults=d,
            )
        self.stdout.write(f"  {len(FORM_DIAGNOSTICS)} diagnostics")

    def _upsert_tests(self, form):
        for t in TEST_SCENARIOS:
            t = dict(t)
            TestScenario.objects.update_or_create(
                tax_form=form, scenario_name=t.pop("scenario_name"), defaults=t,
            )
        self.stdout.write(f"  {len(TEST_SCENARIOS)} test scenarios")

    def _upsert_form_links(self, sources):
        for source_code, link_type in AUTHORITY_FORM_LINKS:
            source = sources.get(source_code) or AuthoritySource.objects.filter(
                source_code=source_code,
            ).first()
            if source:
                AuthorityFormLink.objects.get_or_create(
                    authority_source=source, form_code=FORM_NUMBER, link_type=link_type,
                    defaults={"note": f"{source_code} -> {FORM_NUMBER}"},
                )

    # ─────────────────────────────────────────────────────────────────────────
    # Flow assertions
    # ─────────────────────────────────────────────────────────────────────────

    def _load_flow_assertions(self):
        # The original FA-1040-SCH1A-* ids were superseded by the canonical
        # FA-SCH1A-* set (the tts flow_assertions_1040.json gate file is
        # canonical — REVIEW_QUEUE 2026-07-01, resolved 2026-07-02). Disable,
        # don't delete: the export serves status="active" only, and the old
        # rows stay auditable in admin.
        # Only 01..04 were superseded by the renamed FA-SCH1A-* scheme; the
        # canonical file still carries the legacy-id 05/06/07 (kept in
        # FLOW_ASSERTIONS above).
        superseded = (
            "FA-1040-SCH1A-01", "FA-1040-SCH1A-02",
            "FA-1040-SCH1A-03", "FA-1040-SCH1A-04",
        )
        stale = FlowAssertion.objects.filter(
            assertion_id__in=superseded
        ).exclude(status="disabled").update(status="disabled")
        if stale:
            self.stdout.write(f"  {stale} superseded FA-1040-SCH1A-01..04 disabled")
        for a in FLOW_ASSERTIONS:
            a = dict(a)
            FlowAssertion.objects.update_or_create(
                assertion_id=a.pop("assertion_id"), defaults=a,
            )
        # Everything this block owns is by definition active canon — undoes
        # any stray manual/blanket disable.
        FlowAssertion.objects.filter(
            assertion_id__in=[a["assertion_id"] for a in FLOW_ASSERTIONS]
        ).exclude(status="active").update(status="active")
        self.stdout.write(f"  {len(FLOW_ASSERTIONS)} flow assertions")

    # ─────────────────────────────────────────────────────────────────────────
    # Report
    # ─────────────────────────────────────────────────────────────────────────

    def _report_totals(self):
        def _safe(text):
            return text.encode("ascii", errors="replace").decode("ascii")

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(f"DATABASE TOTALS (after load_{FORM_NUMBER.lower()})")
        self.stdout.write("=" * 60)
        self.stdout.write(f"TaxForms:           {TaxForm.objects.count()}")
        self.stdout.write(f"FormFacts:          {FormFact.objects.count()}")
        self.stdout.write(f"FormRules:          {FormRule.objects.count()}")
        self.stdout.write(f"FormLines:          {FormLine.objects.count()}")
        self.stdout.write(f"FormDiagnostics:    {FormDiagnostic.objects.count()}")
        self.stdout.write(f"TestScenarios:      {TestScenario.objects.count()}")
        self.stdout.write(f"AuthoritySources:   {AuthoritySource.objects.count()}")
        self.stdout.write(f"AuthorityExcerpts:  {AuthorityExcerpt.objects.count()}")
        self.stdout.write(f"RuleAuthorityLinks: {RuleAuthorityLink.objects.count()}")
        self.stdout.write(f"AuthorityFormLinks: {AuthorityFormLink.objects.count()}")
        self.stdout.write(f"FlowAssertions:     {FlowAssertion.objects.count()}")

        all_rules = FormRule.objects.filter(tax_form__form_number=FORM_NUMBER)
        uncited = [r for r in all_rules if not r.authority_links.exists()]
        if uncited:
            self.stdout.write(self.style.WARNING(
                f"\n{FORM_NUMBER} rules with ZERO authority links: {len(uncited)}"
            ))
            for r in uncited[:20]:
                self.stdout.write(_safe(f"  {r.rule_id}: {r.title}"))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"\nAll {FORM_NUMBER} rules have authority links."
            ))

        self.stdout.write("=" * 60)
