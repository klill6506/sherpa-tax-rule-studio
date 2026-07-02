"""Load the FORM_8911 spec — Alternative Fuel Vehicle Refueling Property
Credit (§30C) + Schedule A (Form 8911) → Schedule 3 line 6j (personal part)
and Form 3800 Part III line 1s (business part — RED-deferred, 3800 unbuilt).

Trigger: MeF ATS Scenario 13 (William & Nancy Birch) — the smallest remaining
1040 ATS scenario per Ken's 2026-07-02 smallest-first ruling. Every remaining
scenario needs an unbuilt tax-law form first (the DECISIONS sequencing rule);
this is Scenario 13's form.

⚠️ TERMINATION VERIFIED 2026-07-02 (the SEASON_PLAN appendix-4 OBBBA-sunset
check, done at this spec leg as required): P.L. 119-21 (One Big Beautiful
Bill Act, enacted 7/4/2025) amended §30C(i) — VERBATIM: "This section shall
not apply to any property placed in service after June 30, 2026." So the
credit is FULLY LIVE for TY2025 and HALF-YEAR LIVE for TY2026 (placed in
service 1/1/2026–6/30/2026). NOT zero TY2026 value — S13 survives without a
re-rule. The window is coded EXPLICITLY per year (the GA HB-463 tips/OT
precedent): TY2027+ = nothing qualifies, never a latest-year fallback.

Constants VERIFIED 2026-07-02:
  - §30C(a)/(b)/(c)(3)/(i) — law.cornell.edu/uscode/text/26/30C (the amended
    statute), quoted verbatim in USC_26_30C excerpts.
  - i8911 (Rev. December 2025) — irs.gov/instructions/i8911: termination,
    line 6b credit list (verbatim — see the INTERPRETATION FLAG below),
    line 8 TMT-figured-always, line 10 personal-credit-lost-no-carryover,
    30%/$1,000 personal + 6%/30%-PWA/$100,000 business, post-2022 eligible
    census tract requirement, PWA auto-Yes when construction began before
    January 29, 2023.
  - Form 8911 + Schedule A (Rev. 12-2025) face — as embedded in the ATS-13
    scenario PDF (docs/mef/scenarios/1040-mef-ats-scenario-13.pdf; DRAFT
    watermark — the official f8911.pdf is downloaded/verified at the tts
    render leg).

⚠️ INTERPRETATION FLAG for Ken (Authoritative-Source Rule #4): the line 6b
instruction says Schedule 3 "lines 2 through 5, and 7 (reduced by any general
business credit reported on line 6a, any credit for prior-year minimum tax
reported on line 6b, or any credit to holders of tax credit bonds reported on
line 6k)". Schedule 3 line 7 = the sum of 6a–6z, which INCLUDES 8911's own
line 6j — read literally it is circular. Encoded reading: at the moment 8911
is computed, its own 6j is not yet on Schedule 3 (credit ordering), so
line 6b = 1040 line 19 + Sch 3 lines 2/3/4/5a/5b + the OTHER 6x credits
EXCLUDING 6a (GBC), 6b (8801), 6k (bonds) — i.e. the credits ordered BEFORE
8911. Ken must bless this reading at the review walk.

v1 SCOPE BOUNDARIES (stated, not silent):
  - Business/investment-use part (line 3) and K-1 passthrough (line 2)
    compute on the form but CANNOT flow — Form 3800 is unbuilt → D_8911_004
    RED "prepare Form 3800 manually". Scenario 13 is personal-only.
  - Census-tract eligibility (Sch A line 6a) is a PREPARER ASSERTION; the
    software validates the GEOID format (11 digits) but does NOT adjudicate
    against i8911 Appendix A/B. Stated in D_8911_001/005 + the fact notes.
  - Elective payment / transfer elections (Sch A line 1 registration number)
    out of scope v1 — input stored, no compute effect.
  - Form 7220 (PWA verification) not modeled; line 13 is a preparer fact.

SAFETY GUARD: READY_TO_SEED flipped 2026-07-02 — Ken approved the review walk
in-session (all four judgment items: the line-6b ordering reading, the
census-tract preparer assertion, the 3800 RED-defer, the T1 enacted-law-vs-
ATS-answer-key divergence noted).
"""

from datetime import date

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


READY_TO_SEED = True  # FLIPPED 2026-07-02 — Ken approved the review walk in-session ("Approve — flip, seed, build"): the line-6b ordering reading, the census-tract preparer assertion, the 3800 RED-defer, and the T1 enacted-law pins.


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1040"]


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS (§30C as amended by P.L. 119-21; i8911 Rev. 12-2025)
# ═══════════════════════════════════════════════════════════════════════════

# §30C(i) as amended by P.L. 119-21: "This section shall not apply to any
# property placed in service after June 30, 2026." (verbatim, fetched
# 2026-07-02). EXPLICIT terminal date — no property placed in service after
# this date qualifies, in ANY tax year.
SECTION_30C_TERMINATION = date(2026, 6, 30)

# §30C(a): "30 percent (6 percent in the case of property of a character
# subject to depreciation)"; i8911: 30% business rate if PWA requirements met.
PERSONAL_RATE = "0.30"
BUSINESS_RATE_BASE = "0.06"
BUSINESS_RATE_PWA = "0.30"

# §30C(b): "$100,000 in the case of any such item of property of a character
# subject to an allowance for depreciation"; "$1,000 in any other case".
# PER SINGLE ITEM of qualified property (per Schedule A).
PERSONAL_CAP = 1000
BUSINESS_CAP = 100000

# i8911 Sch A line 13: construction begun before January 29, 2023 → answer
# "Yes" to the PWA question without meeting the requirements.
PWA_AUTO_YES_BEFORE = date(2023, 1, 29)

# i8911 Sch A line 6b: the 11-digit census tract GEOID (2020 census tracts).
GEOID_LENGTH = 11


def refueling_property_qualifies(pis_date: date, tax_year: int) -> bool:
    """§30C(i) window + claim-year gate (shared traceability; the integrity
    gate re-types it). A property qualifies for THIS return iff it was placed
    in service during the return's tax year AND on/before June 30, 2026.
    TY2025: the full year. TY2026: Jan 1 – Jun 30 only. TY2027+: nothing —
    explicit, never a latest-year fallback."""
    if pis_date is None:
        return False
    if pis_date.year != tax_year:
        return False
    return pis_date <= SECTION_30C_TERMINATION


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("refueling_credit",
     "Alternative Fuel Vehicle Refueling Property Credit (§30C) — Form 8911 + Schedule A -> Sch 3 line 6j / Form 3800"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_1040_FORM",
]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "USC_26_30C",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2023,
        "tax_year_end": 2026,
        "title": "26 U.S.C. §30C — Alternative fuel vehicle refueling property credit (as amended by P.L. 119-21)",
        "citation": "IRC §30C (as amended by P.L. 119-21, the One Big Beautiful Bill Act, enacted July 4, 2025)",
        "issuer": "US Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/30C",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": True,
        "notes": (
            "Fetched 2026-07-02 (law.cornell.edu, the post-OBBBA text). The SEASON_PLAN appendix-4 "
            "sunset check for Form 8911, done at this spec leg: §30C(i) terminates the credit for "
            "property placed in service after June 30, 2026 — HALF-YEAR live for TY2026, fully live "
            "TY2025. REQUIRES HUMAN REVIEW: Ken confirms the termination reading + the per-item "
            "(not per-return) reading of the (b) limits."
        ),
        "topics": ["refueling_credit"],
        "excerpts": [
            {
                "excerpt_label": "§30C(i) termination (verbatim, as amended by P.L. 119-21)",
                "location_reference": "26 U.S.C. §30C(i)",
                "excerpt_text": "This section shall not apply to any property placed in service after June 30, 2026.",
                "summary_text": (
                    "The OBBBA termination: NO credit for property placed in service after 6/30/2026 — "
                    "TY2025 full year, TY2026 Jan-Jun only, TY2027+ nothing. Coded as an explicit window."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§30C(a)/(b) credit rate + per-item limits (verbatim)",
                "location_reference": "26 U.S.C. §30C(a), (b)",
                "excerpt_text": (
                    "(a) ... 30 percent (6 percent in the case of property of a character subject to "
                    "depreciation) ... (b) ... shall not exceed— $100,000 in the case of any such item "
                    "of property of a character subject to an allowance for depreciation, and $1,000 "
                    "in any other case."
                ),
                "summary_text": (
                    "Personal (non-depreciable) 30% capped $1,000 PER ITEM; business (depreciable) 6% "
                    "capped $100,000 PER ITEM (30% with PWA per §30C(g)/i8911)."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§30C(c)(3) eligible census tract requirement (verbatim)",
                "location_reference": "26 U.S.C. §30C(c)(3)",
                "excerpt_text": (
                    "Property shall not be treated as qualified alternative fuel vehicle refueling "
                    "property unless such property is placed in service in an eligible census tract."
                ),
                "summary_text": "Post-2022 property must sit in an eligible census tract (low-income or non-urban).",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_8911_INSTR",
        "source_type": "official_guidance",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "Instructions for Form 8911 (Rev. December 2025) — Alternative Fuel Vehicle Refueling Property Credit",
        "citation": "i8911 (Rev. 12-2025)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/instructions/i8911",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": (
            "Fetched 2026-07-02. REQUIRES HUMAN REVIEW for the line-6b reading: the verbatim text "
            "sums Schedule 3 'lines 2 through 5, and 7' with a parenthetical removing 6a/6b/6k — "
            "line 7 read literally includes 8911's own 6j (circular). Encoded reading = the credits "
            "ordered BEFORE 8911 (Sch 3 2/3/4/5a/5b + 6c/6d/6f/6g/6h/6i/6l/6m/6z), never its own "
            "6j. Ken blesses at the review walk."
        ),
        "topics": ["refueling_credit"],
        "excerpts": [
            {
                "excerpt_label": "Termination — P.L. 119-21 (verbatim)",
                "location_reference": "i8911 (Rev. 12-2025), What's New / Purpose",
                "excerpt_text": (
                    "P.L. 119-21, commonly known as the One Big Beautiful Bill Act changed the "
                    "termination date for the section 30C alternative fuel vehicle refueling property "
                    "credit from December 31, 2032, to June 30, 2026. You can't claim the credit for "
                    "alternative fuel vehicle refueling property placed in service after June 30, 2026."
                ),
                "summary_text": "The instruction-level statement of the §30C(i) OBBBA termination.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Line 6b — certain allowable credits (verbatim)",
                "location_reference": "i8911 (Rev. 12-2025), Part II, line 6b",
                "excerpt_text": (
                    "Enter the total of any credits or adjustments on Form 1040, 1040-SR, or 1040-NR, "
                    "line 19, and Schedule 3 (Form 1040), lines 2 through 5, and 7 (reduced by any "
                    "general business credit reported on line 6a, any credit for prior-year minimum "
                    "tax reported on line 6b, or any credit to holders of tax credit bonds reported "
                    "on line 6k)."
                ),
                "summary_text": (
                    "6b = 1040 L19 (CTC/ODC) + Sch 3 L2-L5 + [L7 minus 6a GBC, 6b 8801, 6k bonds] — "
                    "i.e. every Part-I credit ordered before 8911; its own 6j is excluded by ordering "
                    "(the INTERPRETATION FLAG — Ken review)."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Line 8 — TMT must be figured even with no AMT (verbatim)",
                "location_reference": "i8911 (Rev. 12-2025), Part II, line 8",
                "excerpt_text": (
                    "Although you may not owe alternative minimum tax (AMT), you must still figure "
                    "the tentative minimum tax (TMT) to figure your credit."
                ),
                "summary_text": (
                    "Line 8 = Form 6251 line 9 (TMT), computed UNCONDITIONALLY — the tts compute must "
                    "source compute_6251 line 9 even when AMT is not engaged."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Line 10 — unused personal credit is lost (verbatim)",
                "location_reference": "i8911 (Rev. 12-2025), Part II, line 10",
                "excerpt_text": (
                    "If you can't use part of the personal portion of the credit because of the tax "
                    "liability limit, the unused credit is lost. The unused personal portion of the "
                    "credit can't be carried back or forward to other tax years."
                ),
                "summary_text": "No carryback/carryforward of the personal part — D_8911_003 transparency.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Rates, per-item caps, census tract, PWA (verbatim)",
                "location_reference": "i8911 (Rev. 12-2025), General Instructions + Sch A lines 6/13",
                "excerpt_text": (
                    "For property of a character not subject to depreciation and which is placed in "
                    "service at your main home (personal use property), the credit is 30% of the cost "
                    "of the property, limited to $1,000 for each single item of qualified alternative "
                    "fuel vehicle refueling property. For property of a character subject to "
                    "depreciation (business/investment use property), the credit is 6% (30% if PWA "
                    "requirements are met) of the property's cost, limited to $100,000, for each "
                    "single item of qualified alternative fuel vehicle refueling property. Property "
                    "placed in service after 2022 will not be treated as qualified alternative fuel "
                    "vehicle refueling property unless it was placed in service in an eligible census "
                    "tract. [Sch A line 13:] construction of which begins prior to January 29, 2023 "
                    "[→ answer Yes]. [Sch A line 5:] Generally, property is placed in service when it "
                    "is ready and available for a specific use, regardless of whether or not it is "
                    "actually used at the time."
                ),
                "summary_text": (
                    "30%/$1,000 personal at main home; 6% (30% PWA)/$100,000 business; per ITEM. "
                    "Census tract via the 11-digit GEOID (Appendix A/B — preparer-adjudicated in v1). "
                    "Construction pre-1/29/2023 = PWA auto-Yes."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_8911_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "Form 8911 + Schedule A (Form 8911) (Rev. December 2025)",
        "citation": "Form 8911 (Rev. 12-2025), Attachment Sequence No. 151; Schedule A (Form 8911), Sequence No. 151A",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f8911.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": (
            "Face transcribed 2026-07-02 from the copy embedded in the ATS-13 scenario PDF "
            "(docs/mef/scenarios/1040-mef-ats-scenario-13.pdf — TREASURY/IRS DRAFT watermark). The "
            "official f8911.pdf is downloaded + hash-recorded at the tts render leg; re-verify the "
            "line structure then."
        ),
        "topics": ["refueling_credit"],
        "excerpts": [
            {
                "excerpt_label": "Part II structure — lines 5/8/10 sourcing (verbatim)",
                "location_reference": "Form 8911 (Rev. 12-2025), Part II",
                "excerpt_text": (
                    "5 Regular tax before credits: Individuals. Enter the sum of the amounts from "
                    "Form 1040, 1040-SR, or 1040-NR, line 16; and Schedule 2 (Form 1040), line 1z. "
                    "... 8 Tentative minimum tax (see instructions): Individuals. Enter the amount "
                    "from Form 6251, line 9. ... 10 Personal use part of credit. Enter the smaller "
                    "of line 4 or line 9 here and on Schedule 3 (Form 1040), line 6j."
                ),
                "summary_text": "L5 = 1040 L16 + Sch2 L1z; L8 = 6251 L9; L10 = min(L4, L9) -> Sch 3 6j.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Schedule A stop rules — census tract + main home (verbatim)",
                "location_reference": "Schedule A (Form 8911) (Rev. 12-2025), lines 6a and 17",
                "excerpt_text": (
                    "6a Was the refueling property placed in service in an eligible census tract? ... "
                    "No. Stop here. Refueling property must be placed in service in an eligible census "
                    "tract to qualify for the credit. ... 17 Was the refueling property installed on "
                    "property used as your main home? ... No. Stop here. Refueling property not "
                    "installed on property used as your main home does not qualify for the personal "
                    "use part of the credit."
                ),
                "summary_text": (
                    "Two face-level stop rules: tract-No kills the property entirely; main-home-No "
                    "kills only the personal part."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("USC_26_30C", "FORM_8911", "governs"),
    ("IRS_2025_8911_INSTR", "FORM_8911", "governs"),
    ("IRS_2025_8911_FORM", "FORM_8911", "governs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM: FORM_8911
# ═══════════════════════════════════════════════════════════════════════════

F8911_IDENTITY = {
    "form_number": "FORM_8911",
    "form_title": "Form 8911 + Schedule A — Alternative Fuel Vehicle Refueling Property Credit (§30C) (TY2025)",
    "notes": (
        "ATS Scenario 13's form (smallest-first, Ken 2026-07-02). One Schedule A "
        "per qualified property (a per-return LIST model at the tts build leg — "
        "the InstallmentSale/LikeKindExchange row pattern); Form 8911 aggregates. "
        "Personal path FULL (30%/$1,000/item, main-home + census-tract gates, "
        "tax-and-TMT limitation, unused credit LOST) -> Schedule 3 line 6j. "
        "Business path (6%/30%-PWA, $100,000/item, §179 backout) computes but "
        "RED-defers to the unbuilt Form 3800 (D_8911_004). §30C(i) termination "
        "coded as an EXPLICIT window: PIS on/before 2026-06-30 AND within the "
        "return year — TY2025 full, TY2026 Jan-Jun, TY2027+ nothing."
    ),
}

F8911_FACTS: list[dict] = [
    # ── Per-property inputs (one Schedule A per property — a tts list model) ──
    {"fact_key": "f8911_description", "label": "Sch A 2a — description of refueling property",
     "data_type": "string", "sort_order": 1, "notes": "PER-PROPERTY INPUT."},
    {"fact_key": "f8911_cost", "label": "Sch A 8 — cost of the qualified refueling property",
     "data_type": "decimal", "default_value": "0", "sort_order": 2, "notes": "PER-PROPERTY INPUT."},
    {"fact_key": "f8911_business_pct", "label": "Sch A 9 — business/investment use percentage (0-100)",
     "data_type": "decimal", "default_value": "0", "sort_order": 3,
     "notes": "PER-PROPERTY INPUT. 0 = fully personal; 100 = fully business (personal part skipped per line 16)."},
    {"fact_key": "f8911_s179", "label": "Sch A 11 — section 179 expense deduction taken on the property",
     "data_type": "decimal", "default_value": "0", "sort_order": 4,
     "notes": "PER-PROPERTY INPUT. Backed out of the business base (line 12 = line 10 − line 11)."},
    {"fact_key": "f8911_construction_began", "label": "Sch A 4 — date construction began",
     "data_type": "date", "sort_order": 5,
     "notes": "PER-PROPERTY INPUT. Before 2023-01-29 -> PWA auto-Yes (i8911 line 13)."},
    {"fact_key": "f8911_pis_date", "label": "Sch A 5 — date placed in service",
     "data_type": "date", "sort_order": 6,
     "notes": ("PER-PROPERTY INPUT. Drives the §30C(i) window (on/before 2026-06-30) AND the claim-year "
               "gate (PIS year must equal the return tax year).")},
    {"fact_key": "f8911_census_tract_ok", "label": "Sch A 6a — placed in service in an eligible census tract?",
     "data_type": "boolean", "sort_order": 7,
     "notes": ("PER-PROPERTY PREPARER ASSERTION (nullable). None = unanswered -> D_8911_001 RED, property "
               "excluded. False = the face's 'No. Stop here.' -> excluded, quiet. The software does NOT "
               "adjudicate Appendix A/B (v1 boundary).")},
    {"fact_key": "f8911_census_geoid", "label": "Sch A 6b — 11-digit census tract GEOID",
     "data_type": "string", "sort_order": 8,
     "notes": "PER-PROPERTY INPUT. Format-validated (exactly 11 digits) when the credit is claimed — D_8911_005."},
    {"fact_key": "f8911_main_home", "label": "Sch A 17 — installed on property used as your main home?",
     "data_type": "boolean", "default_value": "false", "sort_order": 9,
     "notes": "PER-PROPERTY INPUT. False -> personal part = 0 (the face's line-17 stop), business part unaffected."},
    {"fact_key": "f8911_pwa_met", "label": "Sch A 13 — prevailing wage & apprenticeship requirements met?",
     "data_type": "boolean", "default_value": "false", "sort_order": 10,
     "notes": ("PER-PROPERTY PREPARER ASSERTION. Auto-Yes when construction began before 2023-01-29. "
               "True -> 30% business rate; False -> 6%. Form 7220 not modeled (v1).")},
    # ── Return-level ──
    {"fact_key": "f8911_k1_credit", "label": "Line 2 — refueling credit from partnerships / S corporations (K-1)",
     "data_type": "decimal", "default_value": "0", "sort_order": 11,
     "notes": "RETURN-LEVEL INPUT. Part of line 3 -> Form 3800 (unbuilt) -> D_8911_004 RED when present."},
    # ── Outputs ──
    {"fact_key": "f8911_business_credit", "label": "Line 3 — business/investment use part (Σ Sch A line 16 + line 2)",
     "data_type": "decimal", "sort_order": 20,
     "notes": "OUTPUT. -> Form 3800 Part III line 1s — RED-DEFERRED (D_8911_004); never lands on Sch 3."},
    {"fact_key": "f8911_personal_total", "label": "Line 4 — personal use part before limitation (Σ Sch A line 21)",
     "data_type": "decimal", "sort_order": 21, "notes": "OUTPUT."},
    {"fact_key": "f8911_net_regular_tax", "label": "Line 7 — net regular tax (line 5 − line 6c)",
     "data_type": "decimal", "sort_order": 22, "notes": "OUTPUT. L5 = 1040 L16 + Sch 2 L1z; L6c = L6a FTC + L6b."},
    {"fact_key": "f8911_tmt", "label": "Line 8 — tentative minimum tax (Form 6251 line 9, figured always)",
     "data_type": "decimal", "sort_order": 23,
     "notes": "OUTPUT. Sourced from FORM_6251 line 9 UNCONDITIONALLY (i8911 line 8 verbatim)."},
    {"fact_key": "f8911_allowed_personal", "label": "Line 10 — allowed personal credit -> Schedule 3 line 6j",
     "data_type": "decimal", "sort_order": 24,
     "notes": "OUTPUT. min(line 4, line 9); the unused excess is LOST (no carryover)."},
]

F8911_RULES: list[dict] = [
    {"rule_id": "R-8911-QUALIFY",
     "title": "Per-property qualification: §30C(i) window + claim year + eligible census tract",
     "rule_type": "routing", "precedence": 1, "sort_order": 1,
     "formula": (
         "A property qualifies iff: pis_date.year == tax_year AND pis_date <= 2026-06-30 (§30C(i), "
         "P.L. 119-21 — EXPLICIT window: TY2025 full year, TY2026 Jan-Jun, TY2027+ nothing, never a "
         "latest-year fallback) AND census_tract_ok is True (§30C(c)(3); preparer assertion — None -> "
         "D_8911_001 RED + excluded; False -> excluded quiet per the face's 'No. Stop here.'). "
         "A non-qualifying property contributes 0 to BOTH parts. PIS after 6/30/2026 -> D_8911_002; "
         "PIS year != tax_year -> D_8911_006."),
     "inputs": ["f8911_pis_date", "f8911_census_tract_ok"], "outputs": [],
     "description": ("The gate every other rule sits behind. The sunset check (SEASON_PLAN appendix 4) "
                     "resolved at this spec leg: half-year TY2026 life, not zero.")},
    {"rule_id": "R-8911-SCHA-PERS",
     "title": "Schedule A Part III — personal use part per property (30%, $1,000/item, main-home gate)",
     "rule_type": "calculation", "precedence": 2, "sort_order": 2,
     "formula": (
         "Per QUALIFYING property: A-10 = cost × business_pct; A-18 = cost − A-10; A-19 = A-18 × 0.30 "
         "(whole-dollar, half-up); A-21 = min(A-19, 1000). main_home == False -> personal part = 0 "
         "(the face's line-17 stop). business_pct == 100 -> A-18 = 0 naturally (the line-16 'stop "
         "here' path). Form 8911 line 4 = Σ A-21 over qualifying properties."),
     "inputs": ["f8911_cost", "f8911_business_pct", "f8911_main_home"], "outputs": ["f8911_personal_total"],
     "description": "§30C(a)/(b): 30% / $1,000 PER ITEM (per Schedule A), not per return."},
    {"rule_id": "R-8911-SCHA-BUS",
     "title": "Schedule A Part II — business/investment use part per property (6%/30% PWA, $100,000/item, §179 backout)",
     "rule_type": "calculation", "precedence": 3, "sort_order": 3,
     "formula": (
         "Per QUALIFYING property: A-10 = cost × business_pct; A-11 = s179; A-12 = max(0, A-10 − A-11); "
         "rate = 0.30 if (pwa_met OR construction_began < 2023-01-29) else 0.06; A-14 = A-12 × rate "
         "(whole-dollar, half-up); A-15 = 100000; A-16 = min(A-14, A-15). Form 8911 line 1 = Σ A-16; "
         "line 3 = line 1 + line 2 (K-1). Line 3 > 0 -> D_8911_004 RED (Form 3800 unbuilt — v1 "
         "boundary); the amount NEVER lands on Schedule 3."),
     "inputs": ["f8911_cost", "f8911_business_pct", "f8911_s179", "f8911_pwa_met",
                "f8911_construction_began", "f8911_k1_credit"],
     "outputs": ["f8911_business_credit"],
     "description": "Computed for the form face + the future 3800 hookup; flow is RED-deferred, stated not silent."},
    {"rule_id": "R-8911-TAXLIM",
     "title": "Part II lines 5-9 — the tax-liability + TMT limitation",
     "rule_type": "calculation", "precedence": 4, "sort_order": 4,
     "formula": (
         "L5 = 1040 line 16 + Sch 2 line 1z. L6a = Sch 3 line 1 (FTC). L6b = 1040 line 19 + Sch 3 "
         "lines 2 + 3 + 4 + 5a + 5b + (6c + 6d + 6f + 6g + 6h + 6i + 6l + 6m + 6z) — i.e. the i8911 "
         "verbatim 'lines 2 through 5, and 7 (reduced by 6a/6b/6k)', with 8911's own 6j excluded by "
         "credit ordering (the INTERPRETATION FLAG — Ken review). L6c = L6a + L6b. L7 = max(0, L5 − "
         "L6c). L8 = FORM_6251 line 9 (TMT), figured UNCONDITIONALLY even when no AMT is owed. "
         "L9 = max(0, L7 − L8)."),
     "inputs": [], "outputs": ["f8911_net_regular_tax", "f8911_tmt"],
     "description": ("Compute ordering: AFTER compute_1116/2441/8863/8880/5695/8812 (line 19) and "
                     "compute_6251, BEFORE the Schedule 3 line 7/8 totals.")},
    {"rule_id": "R-8911-SCH3-6J",
     "title": "Line 10 — allowed personal credit = min(line 4, line 9) -> Schedule 3 line 6j; excess LOST",
     "rule_type": "calculation", "precedence": 5, "sort_order": 5,
     "formula": (
         "L10 = min(L4, L9) -> Schedule 3 line 6j (joins the existing Sch 3 6a-6z -> line 7 -> line 8 "
         "-> 1040 line 20 aggregation). If L9 < L4: D_8911_003 info — the unused personal portion is "
         "PERMANENTLY LOST (no carryback/carryforward, i8911 line 10 verbatim)."),
     "inputs": [], "outputs": ["f8911_allowed_personal"],
     "description": "The landing rule Scenario 13 exercises (Birch: min(300, net tax) -> Sch 3 6j)."},
]

F8911_LINES: list[dict] = [
    # ── Form 8911 face ──
    {"line_number": "A", "description": "A Total number of qualified refueling properties (count of Schedule A rows)", "line_type": "calculated"},
    {"line_number": "1", "description": "1 Total business/investment credit from Part II of Schedule(s) A (Σ A-16)", "line_type": "calculated"},
    {"line_number": "2", "description": "2 Refueling property credit from partnerships and S corporations (K-1)", "line_type": "input"},
    {"line_number": "3", "description": "3 Business/investment use part. Add lines 1 and 2 -> Form 3800 Part III 1s (RED-deferred v1)", "line_type": "total"},
    {"line_number": "4", "description": "4 Total personal credit from Part III of Schedule(s) A (Σ A-21)", "line_type": "calculated"},
    {"line_number": "5", "description": "5 Regular tax before credits (1040 line 16 + Schedule 2 line 1z)", "line_type": "calculated"},
    {"line_number": "6a", "description": "6a Foreign tax credit (Schedule 3 line 1)", "line_type": "calculated"},
    {"line_number": "6b", "description": "6b Certain allowable credits (1040 L19 + Sch 3 L2-5 + L7 excl. 6a/6b/6k/own 6j)", "line_type": "calculated"},
    {"line_number": "6c", "description": "6c Add lines 6a and 6b", "line_type": "subtotal"},
    {"line_number": "7", "description": "7 Net regular tax. Subtract line 6c from line 5 (not < 0)", "line_type": "calculated"},
    {"line_number": "8", "description": "8 Tentative minimum tax (Form 6251 line 9 — figured always)", "line_type": "calculated"},
    {"line_number": "9", "description": "9 Subtract line 8 from line 7 (not < 0)", "line_type": "calculated"},
    {"line_number": "10", "description": "10 Personal use part of credit: smaller of line 4 or line 9 -> Schedule 3 line 6j", "line_type": "total"},
    # ── Schedule A (Form 8911) face — one per property, "A-" prefix ──
    {"line_number": "A-1", "description": "Sch A 1 Elective payment/transfer registration number (stored; no compute effect v1)", "line_type": "input"},
    {"line_number": "A-2a", "description": "Sch A 2a Description of refueling property", "line_type": "input"},
    {"line_number": "A-3a", "description": "Sch A 3a Address of refueling property", "line_type": "input"},
    {"line_number": "A-4", "description": "Sch A 4 Date construction began", "line_type": "input"},
    {"line_number": "A-5", "description": "Sch A 5 Date placed in service (the §30C(i) window + claim-year driver)", "line_type": "input"},
    {"line_number": "A-6a", "description": "Sch A 6a Eligible census tract? (preparer assertion; No/unanswered -> excluded)", "line_type": "input"},
    {"line_number": "A-6b", "description": "Sch A 6b 11-digit census tract GEOID", "line_type": "input"},
    {"line_number": "A-7", "description": "Sch A 7 Certification/permit number (stored; no compute effect)", "line_type": "input"},
    {"line_number": "A-8", "description": "Sch A 8 Cost of the qualified refueling property", "line_type": "input"},
    {"line_number": "A-9", "description": "Sch A 9 Business/investment use percentage", "line_type": "input"},
    {"line_number": "A-10", "description": "Sch A 10 Line 8 × line 9 (business base)", "line_type": "calculated"},
    {"line_number": "A-11", "description": "Sch A 11 Section 179 expense deduction", "line_type": "input"},
    {"line_number": "A-12", "description": "Sch A 12 Line 10 − line 11", "line_type": "calculated"},
    {"line_number": "A-13", "description": "Sch A 13 PWA requirements met? (auto-Yes if construction began before 1/29/2023)", "line_type": "input"},
    {"line_number": "A-14", "description": "Sch A 14 Line 12 × 6% (30% if line 13 Yes)", "line_type": "calculated"},
    {"line_number": "A-15", "description": "Sch A 15 Maximum business credit per item ($100,000)", "line_type": "static"},
    {"line_number": "A-16", "description": "Sch A 16 Smaller of line 14 or 15 -> Form 8911 line 1", "line_type": "calculated"},
    {"line_number": "A-17", "description": "Sch A 17 Installed at your main home? (No -> no personal part)", "line_type": "input"},
    {"line_number": "A-18", "description": "Sch A 18 Line 8 − line 10 (personal base)", "line_type": "calculated"},
    {"line_number": "A-19", "description": "Sch A 19 Line 18 × 30%", "line_type": "calculated"},
    {"line_number": "A-20", "description": "Sch A 20 Maximum personal credit per item ($1,000)", "line_type": "static"},
    {"line_number": "A-21", "description": "Sch A 21 Smaller of line 19 or 20 -> Form 8911 line 4", "line_type": "calculated"},
]

F8911_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_8911_001", "title": "Census-tract eligibility unanswered — property excluded", "severity": "error",
     "condition": "a Schedule A property with cost > 0 has census_tract_ok = None (unanswered)",
     "message": ("The eligible-census-tract question (Schedule A line 6a) is unanswered for a refueling "
                 "property. §30C(c)(3) requires the property to sit in an eligible census tract — verify "
                 "the 11-digit GEOID against the i8911 appendices (the software does not adjudicate the "
                 "tract list) and answer Yes or No. Until answered the property is excluded from the credit."),
     "notes": "The no-silent-gap gate on the preparer assertion. Answered No = the face's stop rule, quiet."},
    {"diagnostic_id": "D_8911_002", "title": "Placed in service after June 30, 2026 — §30C terminated", "severity": "warning",
     "condition": "a Schedule A property has pis_date > 2026-06-30",
     "message": ("This refueling property was placed in service after June 30, 2026. P.L. 119-21 terminated "
                 "the §30C credit for property placed in service after that date ('This section shall not "
                 "apply to any property placed in service after June 30, 2026') — no credit is allowed for "
                 "this property. Verify the placed-in-service date."),
     "notes": "The OBBBA sunset, surfaced not silent. Warning (a date typo is the likely cause on a claimed row)."},
    {"diagnostic_id": "D_8911_003", "title": "Personal credit limited by tax liability — excess permanently lost", "severity": "info",
     "condition": "line 9 < line 4 (the allowed credit on line 10 is less than the tentative personal credit)",
     "message": ("The personal-use refueling credit is limited by the tax-liability limit (Form 8911 line 9, "
                 "net regular tax minus tentative minimum tax). The unused portion is permanently lost — it "
                 "cannot be carried back or forward to other tax years (i8911 line 10)."),
     "notes": "Transparency on the lost excess (Birch/T1: 300 tentative -> 11 allowed, 289 lost)."},
    {"diagnostic_id": "D_8911_004", "title": "Business/investment refueling credit — Form 3800 not supported", "severity": "error",
     "condition": "line 3 > 0 (Σ Schedule A business parts + the K-1 passthrough)",
     "message": ("Not supported — prepare manually: the business/investment use part of the refueling credit "
                 "(Form 8911 line 3) flows to Form 3800 Part III line 1s, and Form 3800 is not yet built. "
                 "The amount is computed on the form face but does NOT flow to the return — prepare Form "
                 "3800 and the general business credit manually."),
     "notes": "v1 RED-defer (the SPRINT no-silent-gap rule). Scenario 13 is personal-only and never fires this."},
    {"diagnostic_id": "D_8911_005", "title": "Census tract GEOID missing or malformed", "severity": "error",
     "condition": "a property claims the credit (census_tract_ok True, credit > 0) and census_geoid is not exactly 11 digits",
     "message": ("The census tract GEOID (Schedule A line 6b) must be the 11-digit 2020-census GEOID for a "
                 "property claiming the refueling credit — it is required on the face and in the e-file "
                 "schema. Enter the 11-digit GEOID from the Census geocoder."),
     "notes": "Format-only validation (v1); eligibility itself stays the line-6a preparer assertion."},
    {"diagnostic_id": "D_8911_006", "title": "Placed-in-service year is not this return's tax year", "severity": "error",
     "condition": "a Schedule A property has pis_date.year != tax_year",
     "message": ("This refueling property's placed-in-service date falls outside the return's tax year. The "
                 "§30C credit is claimed for the year the property is placed in service — a prior-year "
                 "install belongs on that year's return (amend if needed). The property is excluded from "
                 "this return's credit."),
     "notes": "The claim-year trap (a preparer keys last year's charger onto this year's return)."},
]

F8911_SCENARIOS: list[dict] = [
    {"scenario_name": "8911-T1 — ATS Scenario 13 (Birch) under ENACTED law", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "filing_status": "mfj",
                "properties": [{"cost": 1000, "business_pct": 0, "main_home": True, "census_tract_ok": True,
                                "census_geoid": "48201110000", "pis_date": "2025-03-01",
                                "construction_began": "2025-03-01"}],
                "f1040_line16": 11, "sch2_1z": 0, "f1040_line19": 0, "sch3_before_6j": 0, "tmt": 0},
     "expected_outputs": {"A-19": 300, "A-21": 300, "f8911_personal_total": 300,
                          "f8911_net_regular_tax": 11, "f8911_tmt": 0, "f8911_allowed_personal": 11,
                          "D_8911_003": True},
     "notes": ("HAND-COMPUTED. The ATS-13 facts under ENACTED OBBBA law: W-2 31,620 − std ded 31,500 (MFJ "
               "2025, Rev. Proc./OBBBA) = 120 taxable -> Tax Table (100-125 midpoint) tax 11 -> L10 = "
               "min(300, 11) = 11, 289 lost (D_003). ⚠️ The IRS scenario answer key shows tax 162 because "
               "it used the PRE-OBBBA 30,000 std deduction — the engine follows enacted law; ATS acceptance "
               "is schema + business rules, not answer-key match. Flagged to Ken at the review walk.")},
    {"scenario_name": "8911-T2 — personal $1,000 per-item cap", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"tax_year": 2025, "filing_status": "single",
                "properties": [{"cost": 4000, "business_pct": 0, "main_home": True, "census_tract_ok": True,
                                "census_geoid": "13059000100", "pis_date": "2025-06-15",
                                "construction_began": "2025-05-01"}],
                "f1040_line16": 5000, "sch2_1z": 0, "f1040_line19": 0, "sch3_before_6j": 0, "tmt": 0},
     "expected_outputs": {"A-19": 1200, "A-21": 1000, "f8911_personal_total": 1000, "f8911_allowed_personal": 1000},
     "notes": "HAND-COMPUTED. 4,000 × 30% = 1,200 -> capped at the §30C(b) $1,000 per item; ample tax."},
    {"scenario_name": "8911-T3 — TMT bites the limitation", "scenario_type": "edge_case", "sort_order": 3,
     "inputs": {"tax_year": 2025, "filing_status": "single",
                "properties": [{"cost": 1000, "business_pct": 0, "main_home": True, "census_tract_ok": True,
                                "census_geoid": "13059000100", "pis_date": "2025-04-01",
                                "construction_began": "2025-04-01"}],
                "f1040_line16": 3000, "sch2_1z": 0, "f1040_line19": 0, "sch3_before_6j": 0, "tmt": 2900},
     "expected_outputs": {"f8911_personal_total": 300, "f8911_net_regular_tax": 3000, "f8911_tmt": 2900,
                          "f8911_allowed_personal": 100, "D_8911_003": True},
     "notes": ("HAND-COMPUTED. L9 = 3,000 − 2,900 = 100 -> L10 = min(300, 100) = 100; 200 permanently lost. "
               "Pins the i8911 line-8 rule that TMT limits the credit even when NO AMT is owed (TMT < regular tax).")},
    {"scenario_name": "8911-T4 — §30C(i) window boundary pair (TY2026)", "scenario_type": "edge_case", "sort_order": 4,
     "inputs": {"tax_year": 2026, "filing_status": "mfj",
                "properties": [{"cost": 1000, "business_pct": 0, "main_home": True, "census_tract_ok": True,
                                "census_geoid": "48201110000", "pis_date": "2026-06-30",
                                "construction_began": "2026-05-01"},
                               {"cost": 1000, "business_pct": 0, "main_home": True, "census_tract_ok": True,
                                "census_geoid": "48201110000", "pis_date": "2026-07-01",
                                "construction_began": "2026-05-01"}],
                "f1040_line16": 4000, "sch2_1z": 0, "f1040_line19": 0, "sch3_before_6j": 0, "tmt": 0},
     "expected_outputs": {"f8911_personal_total": 300, "f8911_allowed_personal": 300, "D_8911_002": True},
     "notes": ("HAND-COMPUTED boundary pair. PIS 6/30/2026 qualifies (300); PIS 7/1/2026 is past the §30C(i) "
               "termination -> contributes 0 + D_8911_002. Line 4 = 300 only. The half-year TY2026 life.")},
    {"scenario_name": "8911-T5 — census tract answered No (the face's stop rule)", "scenario_type": "normal", "sort_order": 5,
     "inputs": {"tax_year": 2025, "filing_status": "single",
                "properties": [{"cost": 1000, "business_pct": 0, "main_home": True, "census_tract_ok": False,
                                "census_geoid": "", "pis_date": "2025-04-01", "construction_began": "2025-04-01"}],
                "f1040_line16": 2000, "sch2_1z": 0, "f1040_line19": 0, "sch3_before_6j": 0, "tmt": 0},
     "expected_outputs": {"f8911_personal_total": 0, "f8911_allowed_personal": 0,
                          "D_8911_001": False, "D_8911_002": False},
     "notes": "An answered No excludes the property QUIETLY (the preparer followed the face's 'No. Stop here.')."},
    {"scenario_name": "8911-T6 — business property, PWA met (RED-deferred to 3800)", "scenario_type": "diagnostic", "sort_order": 6,
     "inputs": {"tax_year": 2025, "filing_status": "single",
                "properties": [{"cost": 50000, "business_pct": 100, "main_home": False, "census_tract_ok": True,
                                "census_geoid": "13059000100", "pis_date": "2025-08-01",
                                "construction_began": "2025-03-01", "pwa_met": True}],
                "f1040_line16": 20000, "sch2_1z": 0, "f1040_line19": 0, "sch3_before_6j": 0, "tmt": 0},
     "expected_outputs": {"A-14": 15000, "A-16": 15000, "f8911_business_credit": 15000,
                          "f8911_personal_total": 0, "f8911_allowed_personal": 0, "D_8911_004": True},
     "notes": ("HAND-COMPUTED. 50,000 × 30% (PWA) = 15,000 -> line 3; Form 3800 unbuilt -> D_8911_004 RED, "
               "nothing lands on Sch 3 (100% business also skips the personal part per the line-16 stop).")},
    {"scenario_name": "8911-T7 — mixed-use property (both parts + the 6% arm)", "scenario_type": "normal", "sort_order": 7,
     "inputs": {"tax_year": 2025, "filing_status": "mfj",
                "properties": [{"cost": 10000, "business_pct": 60, "main_home": True, "census_tract_ok": True,
                                "census_geoid": "48201110000", "pis_date": "2025-09-01",
                                "construction_began": "2025-02-01", "pwa_met": False}],
                "f1040_line16": 8000, "sch2_1z": 0, "f1040_line19": 0, "sch3_before_6j": 0, "tmt": 0},
     "expected_outputs": {"A-10": 6000, "A-14": 360, "A-16": 360, "A-18": 4000, "A-19": 1200, "A-21": 1000,
                          "f8911_business_credit": 360, "f8911_personal_total": 1000,
                          "f8911_allowed_personal": 1000, "D_8911_004": True},
     "notes": ("HAND-COMPUTED. Business: 10,000 × 60% = 6,000 × 6% (no PWA, construction 2/2025 ≥ 1/29/2023) "
               "= 360 (RED-deferred). Personal: 10,000 − 6,000 = 4,000 × 30% = 1,200 -> capped 1,000.")},
    {"scenario_name": "8911-T8 — line 6b credits reduce the limitation (exact fit)", "scenario_type": "normal", "sort_order": 8,
     "inputs": {"tax_year": 2025, "filing_status": "mfj",
                "properties": [{"cost": 1000, "business_pct": 0, "main_home": True, "census_tract_ok": True,
                                "census_geoid": "48201110000", "pis_date": "2025-05-01",
                                "construction_began": "2025-05-01"}],
                "f1040_line16": 2500, "sch2_1z": 0, "f1040_line19": 2000, "sch3_line1_ftc": 200,
                "sch3_before_6j": 0, "tmt": 0},
     "expected_outputs": {"f8911_personal_total": 300, "f8911_net_regular_tax": 300,
                          "f8911_allowed_personal": 300, "D_8911_003": False},
     "notes": ("HAND-COMPUTED. L5 2,500; 6a FTC 200 + 6b CTC 2,000 = 6c 2,200; L7 = 300; TMT 0 -> L9 300; "
               "L10 = min(300, 300) = 300 exact fit, no D_003. Pins the 6b composition (1040 L19 included).")},
    {"scenario_name": "8911-G1 — census tract UNANSWERED (RED gate)", "scenario_type": "diagnostic", "sort_order": 9,
     "inputs": {"tax_year": 2025, "filing_status": "single",
                "properties": [{"cost": 1000, "business_pct": 0, "main_home": True, "census_tract_ok": None,
                                "census_geoid": "", "pis_date": "2025-04-01", "construction_began": "2025-04-01"}],
                "f1040_line16": 2000, "sch2_1z": 0, "f1040_line19": 0, "sch3_before_6j": 0, "tmt": 0},
     "expected_outputs": {"f8911_personal_total": 0, "f8911_allowed_personal": 0, "D_8911_001": True},
     "notes": "Unanswered ≠ No: the property is excluded AND D_8911_001 RED demands the assertion."},
    {"scenario_name": "8911-G2 — placed-in-service year mismatch (claim-year trap)", "scenario_type": "diagnostic", "sort_order": 10,
     "inputs": {"tax_year": 2025, "filing_status": "single",
                "properties": [{"cost": 1000, "business_pct": 0, "main_home": True, "census_tract_ok": True,
                                "census_geoid": "13059000100", "pis_date": "2024-05-01",
                                "construction_began": "2024-04-01"}],
                "f1040_line16": 2000, "sch2_1z": 0, "f1040_line19": 0, "sch3_before_6j": 0, "tmt": 0},
     "expected_outputs": {"f8911_personal_total": 0, "f8911_allowed_personal": 0, "D_8911_006": True},
     "notes": "A 2024 install on the 2025 return -> excluded + D_8911_006 (claim it on the 2024 return / amend)."},
]

F8911_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-8911-QUALIFY", "USC_26_30C", "primary", "§30C(i) termination (verbatim) + §30C(c)(3) census tract"),
    ("R-8911-QUALIFY", "IRS_2025_8911_INSTR", "secondary", "Termination + post-2022 tract requirement + PIS definition"),
    ("R-8911-SCHA-PERS", "USC_26_30C", "primary", "§30C(a)/(b): 30% / $1,000 per item"),
    ("R-8911-SCHA-PERS", "IRS_2025_8911_FORM", "secondary", "Sch A Part III face (lines 17-21, the main-home stop)"),
    ("R-8911-SCHA-BUS", "USC_26_30C", "primary", "§30C(a)/(b): 6% / $100,000 per item"),
    ("R-8911-SCHA-BUS", "IRS_2025_8911_INSTR", "secondary", "30% PWA rate + the 1/29/2023 auto-Yes + §179 backout"),
    ("R-8911-TAXLIM", "IRS_2025_8911_INSTR", "primary", "Line 6b verbatim list + line 8 TMT-figured-always"),
    ("R-8911-TAXLIM", "IRS_2025_8911_FORM", "secondary", "Part II face: L5 = 1040 L16 + Sch2 L1z; L8 = 6251 L9"),
    ("R-8911-SCH3-6J", "IRS_2025_8911_FORM", "primary", "L10 = min(L4, L9) -> Schedule 3 line 6j (face verbatim)"),
    ("R-8911-SCH3-6J", "IRS_2025_8911_INSTR", "secondary", "Line 10: the unused personal portion is lost (verbatim)"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS (loader-homed — the FA-needs-an-RS-home lesson)
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-8911-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Schedule A personal parts (Σ A-21) -> Form 8911 line 4 -> line 10 -> Schedule 3 line 6j",
     "description": ("Validates R-8911-SCHA-PERS + R-8911-SCH3-6J: the per-property personal credits sum to "
                     "line 4 and the ALLOWED amount (min with line 9) lands on Schedule 3 line 6j, joining "
                     "the 6a-6z -> line 7 -> line 8 -> 1040 line 20 chain. Bug it catches: the tentative "
                     "(uncapped) line 4 landing on Sch 3, or the credit skipping the Sch 3 totals."),
     "definition": {"kind": "flow_assertion", "form": "FORM_8911",
                    "checks": [{"source_line": "10", "must_write_to": ["SCH_3.6j"]}]},
     "sort_order": 1},
    {"assertion_id": "FA-1040-8911-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "The limitation chain: L7 = max(0, L5 − L6c); L9 = max(0, L7 − L8); L10 = min(L4, L9)",
     "description": ("Validates R-8911-TAXLIM. Bug it catches: TMT ignored (L10 = min(L4, L7)), the 6b "
                     "credits not subtracted, or a negative line clamped wrong (8911-T3 pins 100)."),
     "definition": {"kind": "formula_check", "form": "FORM_8911",
                    "formula": "line_7 == max(0, line_5 - line_6c); line_9 == max(0, line_7 - line_8); line_10 == min(line_4, line_9)"},
     "sort_order": 2},
    {"assertion_id": "FA-1040-8911-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "§30C constants: termination 2026-06-30; 30%/$1,000 personal; 6%/30%-PWA/$100,000 business",
     "description": ("Validates the verified constants. Bug it catches: a drifted cap/rate, or the "
                     "termination window silently extended past June 30, 2026 (the sunset check's teeth)."),
     "definition": {"kind": "constants_check", "form": "FORM_8911",
                    "constants": {"termination_date": "2026-06-30", "personal_rate": 0.30, "personal_cap": 1000,
                                  "business_rate_base": 0.06, "business_rate_pwa": 0.30, "business_cap": 100000,
                                  "pwa_auto_yes_before": "2023-01-29", "geoid_length": 11}},
     "sort_order": 3},
    {"assertion_id": "FA-1040-8911-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Business part (line 3 > 0) fires D_8911_004 RED and never lands on Schedule 3 (no silent gap)",
     "description": ("Validates R-8911-SCHA-BUS's v1 boundary: Form 3800 is unbuilt, so a business/K-1 "
                     "refueling credit must surface RED and must NOT leak into Schedule 3 line 6j."),
     "definition": {"kind": "gating_check", "form": "FORM_8911", "expect": {"red_fires": True},
                    "blockers": ["business_credit_no_3800", "k1_passthrough_no_3800"]},
     "sort_order": 4},
]


FORMS: list[dict] = [
    {"identity": F8911_IDENTITY, "facts": F8911_FACTS, "rules": F8911_RULES, "lines": F8911_LINES,
     "diagnostics": F8911_DIAGNOSTICS, "scenarios": F8911_SCENARIOS, "rule_links": F8911_RULE_LINKS},
]


class Command(BaseCommand):
    help = "Load the FORM_8911 spec (§30C refueling credit, ATS Scenario 13). Refuses until READY_TO_SEED=True."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad FORM_8911 spec (§30C refueling credit, ATS Scenario 13)\n"))
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
                "\nREFUSING TO SEED FORM_8911: not cleared to seed.\n\n"
                "Gated until Ken's review walk (the §30C(i) 6/30/2026 termination window; the line-6b\n"
                "self-exclusion reading; the census-tract preparer assertion; the 3800 RED-defer; the\n"
                "T1 enacted-law-vs-ATS-answer-key divergence).\n\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True)\n\n"
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
        for code in EXISTING_SOURCES_TO_REFERENCE:
            src = AuthoritySource.objects.filter(source_code=code).first()
            if src:
                sources[code] = src
        self.stdout.write(f"Sources ready: {len(sources)}")
        return sources

    def _load_new_excerpts_on_existing(self, sources):
        for code, exc in NEW_EXCERPTS_ON_EXISTING:
            src = sources.get(code) or AuthoritySource.objects.filter(source_code=code).first()
            if src:
                exc = dict(exc)
                AuthorityExcerpt.objects.update_or_create(
                    authority_source=src, excerpt_label=exc["excerpt_label"], defaults=exc)

    def _upsert_form(self, identity: dict) -> TaxForm:
        form, created = TaxForm.objects.update_or_create(
            form_number=identity["form_number"], jurisdiction=FORM_JURISDICTION,
            tax_year=FORM_TAX_YEAR, version=FORM_VERSION,
            defaults={"form_title": identity["form_title"], "entity_types": FORM_ENTITY_TYPES,
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

    def _report_totals(self):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(f"TaxForms: {TaxForm.objects.count()} | FlowAssertions: {FlowAssertion.objects.count()}")
        form = TaxForm.objects.filter(form_number="FORM_8911").first()
        if form:
            uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
            self.stdout.write("FORM_8911: all rules cited" if not uncited
                              else self.style.WARNING(f"FORM_8911 uncited rules: {len(uncited)}"))
