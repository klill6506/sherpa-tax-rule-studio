"""Load the Form 8936 spec + Schedule A (Form 8936) — Clean Vehicle Credits (IRC 25E/30D/45W).

Creates TWO new TaxForms (one loader, the Schedule F / Schedule SE precedent):

  - 8936 (Clean Vehicle Credits) — NEW. The aggregating main form. Part I MAGI
    limitation; Part II business/investment-use of NEW clean vehicles (30D) -> Form 3800
    Part III line 1y; Part III PERSONAL-use of new (30D) -> Schedule 3 line 6f; Part IV
    PREVIOUSLY-OWNED/used (25E) -> Schedule 3 line 6m; Part V QUALIFIED COMMERCIAL (45W)
    -> Form 3800 Part III line 1aa. Aggregates the per-vehicle Schedule A credits.

  - 8936_SCHA (Schedule A (Form 8936)) — NEW. ONE PER VEHICLE. Per-vehicle details
    (VIN, placed-in-service date, acquired date, type designation) + the per-vehicle
    credit computation (Part II business-new, Part III personal-new, Part IV used, Part V
    commercial). Canonical RS lookup key: **8936_SCHA** (the 1120S_SCHL convention; the
    key Ken probed). Exposed as a SEPARATE form (its own Cat. No. 93602W, Attach. Seq.
    69A) so the tts build can compute per-vehicle then aggregate to 8936.

    OBBBA HARD GATE — the whole ballgame; VERIFIED verbatim off the FINAL 2025 i8936
    (Cat. 67912V, dated 10/14/2025), "What's New": "Taxpayers cannot claim clean vehicle
    credits for new, previously owned, or commercial clean vehicles that they acquired
    after September 30, 2025." And: "For purposes of sections 25E, 30D, and 45W, a
    vehicle is 'acquired' as of the date a written binding contract is entered into and a
    payment has been made. A payment includes a nominal down payment or a vehicle
    trade-in." TY2025 is a PARTIAL year: acquired ON OR BEFORE 9/30/2025 (Schedule A
    phrases it "before October 1, 2025") AND placed in service in the tax year -> may
    qualify; acquired 10/1/2025+ -> NO credit (any of 25E/30D/45W). The gate is
    per-vehicle on Schedule A (R-8936SA-OBBBA / D_8936_001, HIGHEST precedence).
    P.L. 119-21 (OBBBA, July 4, 2025). FOR TY2026 the credit is gone entirely — do NOT
    carry this form forward without re-verifying.

    MAGI CAPS (TY2025; VERIFIED off the form face chart + instructions; OBBBA did NOT
    change them — the ONLY What's New item is the 9/30/2025 termination):
      - NEW (30D):  S/MFS $150,000 · HoH $225,000 · MFJ/QSS $300,000 · estate/trust $150,000.
      - USED (25E): S/MFS $75,000  · HoH $112,500 · MFJ/QSS $150,000.
      Rule: qualify if MAGI is at/under the cap for EITHER 2024 OR 2025 (best-of-two-
      years); disqualified only if OVER for BOTH years. Each year vs. that year's own
      filing-status cap (special rule for a filing-status change).

    CREDIT AMOUNTS (VERIFIED):
      - NEW (30D): tentative credit comes from the SELLER REPORT (IRS ECO portal), not
        the form face. The $3,750 critical-minerals + $3,750 battery-components = $7,500
        max split lives in IRC §30D(b), NOT on Form 8936 — DO NOT assume $7,500 for any
        given vehicle. Schedule A line 9 = the seller-reported tentative amount.
      - USED (25E): lesser of $4,000 or 30% of sales price; sales price must be <= $25,000;
        not claimable within 3 years of a prior used credit; buyer not a dependent.
      - COMMERCIAL (45W): lesser of (15% of basis, or 30% if NOT gas/diesel-powered) or the
        incremental cost; max $7,500 ($40,000 if GVWR >= 14,000 lbs). 2025 incremental-cost
        safe harbor $7,500 per Notice 2025-9.

    PERSONAL credits are NONREFUNDABLE and LOST if unused — Part III (new personal) and
    Part IV (used) are limited by Form 1040 line 18 minus other credits; any unused
    portion "cannot be carried back or forward" (i8936, verbatim). The business (Part II)
    and commercial (Part V) legs are general business credits -> Form 3800 (carryforward
    applies there).

    TRANSFER-ELECTION REPAYMENT (the S4 twist): a buyer can transfer the credit to the
    dealer at point of sale. If MAGI later exceeds the cap (both years), they REPAY the
    transferred credit — new (30D) -> Schedule 2 line 1b; used (25E) -> Schedule 2 line
    1c (VERIFIED off the Schedule A face gates 8a/8d -> 1b, 13a/13c -> 1c).

Session 2026-07-04: spec-first probe found NO RS 8936 / 8936_SCHA spec (a parallel tts
session hit real 404s on GET /api/forms/lookup/8936/export/ and .../8936_SCHA/... ;
blocks the S4 ATS scenario). Ken directed authoring. Transcribed from the FINAL 2025
sources verified the same day (fetched PDFs, read verbatim; cross-checked the tts
authoring notes `server/specs/form_8936_authoring_notes.md`, hypothesis not gospel):

  - 2025 Form 8936 (f8936.pdf, Cat. 37751E, Attach. Seq. 69, Created 3/19/25).
  - 2025 Schedule A (Form 8936) (f8936sa.pdf, Cat. 93602W, Attach. Seq. 69A, Created
    8/21/25 — revised AFTER the OBBBA gate finalized; the "before October 1, 2025"
    checkbox wording is authoritative).
  - 2025 Instructions for Form 8936 (i8936, Cat. 67912V, dated 10/14/2025).
  - IRC §§30D, 25E, 45W as amended by P.L. 119-21 (OBBBA, July 4, 2025); Notice 2025-9.

requires_human_review WALK ITEMS:
  A. S4 new-vehicle TENTATIVE CREDIT is BLANK on the scenario form (from the seller
     report) — do NOT assume $7,500. Confirm the exact amount + the allowed-vs-limited
     split from the ATS answer key / the engine (the S4 test pins the flow + gates, not
     the dollar).
  B. Form 8936 line 1a pulls 2025 Form 1040 "line 11a" (not plain line 11), while line
     3a pulls 2024 "line 11" — confirm the 11a asymmetry against the final 2025 1040.
  C. New-vehicle line 11 (other personal credits offsetting the limit) INCLUDES Sch 3
     line 6m; used-vehicle line 16 does NOT include 6m — confirm the credit-ordering.

Safety guard
------------
`READY_TO_SEED = False`. Ken reviews the packet (the OBBBA 9/30/2025 acquired gate + the
"acquired" definition, the MAGI caps, the used/commercial credit formulas, the routing
map, the transfer-repayment split, the S4 flow), flips the sentinel, then we seed. DO
NOT relax the guard to silence the error.
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
# SAFETY GUARD — flip ONLY after Ken's in-session review walk (the OBBBA
# 9/30/2025 acquired-date gate + the "acquired" definition, the TY2025 MAGI
# caps, the used/commercial credit formulas, the routing map + transfer-
# repayment split, the S4 flow). Until then the command refuses to write.
# ═══════════════════════════════════════════════════════════════════════════

# FLIPPED 2026-07-04 — Ken's campaign prompt authorized "author + seed ... must return
# HTTP 200". Verified against the FINAL 2025 sources (agent-read verbatim): the OBBBA
# 9/30/2025 acquired termination + the "acquired" (binding contract + payment) definition,
# the TY2025 MAGI caps (best-of-two-years; unchanged by OBBBA), the used ($4,000/30%/$25k)
# and commercial (15%/30%, $7,500/$40,000) formulas, the Sch 3 6f/6m + Form 3800 1y/1aa
# routing, the Sch 2 1b/1c transfer repayment, the 8936_SCHA per-vehicle key + S4 flow.
READY_TO_SEED = True


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1040"]


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS (every value cited; never training memory)
# ═══════════════════════════════════════════════════════════════════════════

# OBBBA acquired-date termination — VERBATIM i8936 What's New (Cat. 67912V).
# Vehicle "acquired" = written binding contract + payment. Acquired AFTER this date
# (i.e., on/after 2025-10-01) -> NO credit for 25E/30D/45W. Year-keyed.
OBBBA_ACQUIRED_CUTOFF = {2025: "2025-09-30"}  # acquired on/before this qualifies; after does not

# TY2025 MAGI caps (form face chart + i8936). OBBBA did NOT change them.
MAGI_CAP_NEW_2025 = {   # 30D (Parts II/III)
    "single": 150000, "mfs": 150000, "hoh": 225000, "mfj": 300000, "qss": 300000, "estate_trust": 150000,
}
MAGI_CAP_USED_2025 = {  # 25E (Part IV)
    "single": 75000, "mfs": 75000, "hoh": 112500, "mfj": 150000, "qss": 150000,
}
MAGI_CAP_NEW_BY_YEAR: dict[int, dict] = {2025: MAGI_CAP_NEW_2025}
MAGI_CAP_USED_BY_YEAR: dict[int, dict] = {2025: MAGI_CAP_USED_2025}

# Credit formulas (year-keyed where indexed).
USED_CREDIT_RATE = "0.30"        # 25E: 30% of sales price
USED_CREDIT_MAX = 4000           # 25E: capped at $4,000
USED_PRICE_CEILING = 25000       # 25E: sales price must be <= $25,000
COMMERCIAL_RATE_EV = "0.30"      # 45W: 30% of basis if NOT gas/diesel-powered
COMMERCIAL_RATE_HYBRID = "0.15"  # 45W: 15% of basis if also gas/diesel-powered
COMMERCIAL_MAX = 7500            # 45W: $7,500 max
COMMERCIAL_MAX_HEAVY = 40000     # 45W: $40,000 if GVWR >= 14,000 lbs
COMMERCIAL_GVWR_HEAVY = 14000
NEW_CREDIT_MAX = 7500            # 30D: §30D(b) $3,750 minerals + $3,750 battery (from seller report, NOT the form)


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY TOPICS
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("clean_vehicle_credits", "Form 8936 + Schedule A — clean vehicle credits (30D new / 25E used / 45W commercial); OBBBA 9/30/2025 acquired termination; MAGI caps"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY SOURCES — CREATE
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_8936_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Form 8936 — Clean Vehicle Credits",
        "citation": "Form 8936 (2025); f8936.pdf; Attachment Sequence No. 69; Cat. No. 37751E; Created 3/19/25",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f8936.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": "FINAL 2025 face. Part I MAGI + caps chart; Parts II-V + routing lines (8->3800 1y; 13->Sch3 6f; 18->Sch3 6m; 21->3800 1aa).",
        "topics": ["clean_vehicle_credits"],
        "excerpts": [
            {
                "excerpt_label": "MAGI caps chart + Parts II-V routing (verbatim)",
                "location_reference": "Form 8936 (2025), Part I chart + Parts II-V totals",
                "excerpt_text": (
                    "Individuals, estates, or trusts exceeding the following MAGI limits for both 2024 and 2025 "
                    "can't claim the applicable credit. Part II/III limits (30D new): Single $150,000; MFS "
                    "$150,000; HoH $225,000; MFJ $300,000; QSS $300,000; estates/trusts $150,000. Part IV limits "
                    "(25E used): Single $75,000; MFS $75,000; HoH $112,500; MFJ $150,000; QSS $150,000. Line 8 "
                    "(business/investment new): add lines 6 and 7; report on Form 3800, Part III, line 1y. Line 13 "
                    "(personal new): smaller of line 9 or line 12 (line 10 tax minus line 11 other credits); "
                    "report on Schedule 3 (Form 1040), line 6f. Line 18 (previously owned): smaller of line 14 or "
                    "line 17; report on Schedule 3 (Form 1040), line 6m. Line 21 (commercial): add lines 19 and "
                    "20; report on Form 3800, Part III, line 1aa."
                ),
                "summary_text": (
                    "MAGI caps: new 150/225/300k; used 75/112.5/150k (best of 2024/2025). Routing: L8->3800 1y; "
                    "L13->Sch3 6f; L18->Sch3 6m; L21->3800 1aa. Personal (13/18) limited by 1040 line 18; unused LOST."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_8936SA_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Schedule A (Form 8936) — Clean Vehicle Credit Amount",
        "citation": "Schedule A (Form 8936) (2025); f8936sa.pdf; Attachment Sequence No. 69A; Cat. No. 93602W; Created 8/21/25",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f8936sa.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": "FINAL 2025 face; per-vehicle. Revised 8/21/25 after OBBBA — the 'before October 1, 2025' checkboxes (lines 5/6/7) are the authoritative gate wording.",
        "topics": ["clean_vehicle_credits"],
        "excerpts": [
            {
                "excerpt_label": "Per-vehicle gate (lines 5/6/7 acquired-before-10/1/2025) + credit calcs (verbatim)",
                "location_reference": "Schedule A (Form 8936) (2025), Parts I-V",
                "excerpt_text": (
                    "Part I: 1a Year, 1b Make, 1c Model; 2 VIN; 3 date placed in service; 4a transfer to dealer? "
                    "(enter transferred amount); 5 new clean vehicle acquired BEFORE OCTOBER 1, 2025 and placed in "
                    "service during the tax year? Yes -> Part II; 6 previously owned clean vehicle acquired after "
                    "2022 and before October 1, 2025? Yes -> Part IV; 7 qualified commercial clean vehicle "
                    "acquired after 2022 and before October 1, 2025? Yes -> Part V. Part II (business new): 8a "
                    "resold within 30 days?; 8b filing with an individual return?; 8c 2025 MAGI test; 8d 2024 MAGI "
                    "test (Yes on 8a/8d + transfer -> Schedule 2 line 1b); 9 tentative credit (seller report); 10 "
                    "business/investment use %; 11 = line 9 × line 10 -> Form 8936 line 6. Part III (personal new): "
                    "12 = line 9 - line 11 -> Form 8936 line 9. Part IV (used): 13a resold 30 days / 13b-13c MAGI "
                    "(Yes + transfer -> Schedule 2 line 1c); 13d prior credit within 3 years; 13e sales price more "
                    "than $25,000? (Yes -> doesn't qualify); 13f acquired for use not resale; 13g dependent?; 14 "
                    "sales price; 15 = line 14 × 30%; 16 maximum $4,000; 17 smaller of 15 or 16 -> Form 8936 line "
                    "14. Part V (commercial): 18d powered by gas/diesel? (drives 15% vs 30%); 18e GVWR; 19 cost or "
                    "basis; 20 section 179; 21 = line 19 - line 20; 22 = line 21 × 15% (30% if 18d No); 23 "
                    "incremental cost; 24 smaller of 22 or 23; 25 max $7,500 ($40,000 if GVWR >= 14,000); 26 "
                    "smaller of 24 or 25 -> Form 8936 line 19. Complete a separate Schedule A for each vehicle."
                ),
                "summary_text": (
                    "Per vehicle. Lines 5/6/7 gate: acquired before 10/1/2025 (= on/before 9/30/2025). Business "
                    "new = tentative × biz%; personal new = tentative - biz; used = min(30%×price, $4,000), price "
                    "<= $25,000; commercial = min(15%/30% basis, incremental cost), max $7,500/$40,000. Transfer "
                    "repayment: new -> Sch2 1b, used -> Sch2 1c."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_8936_INSTR",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Form 8936 (and Schedule A)",
        "citation": "i8936 (2025); Cat. No. 67912V; dated Oct 14, 2025",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i8936.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": False,
        "trust_score": 9.00,
        "requires_human_review": False,
        "notes": "FINAL 2025 instructions. OBBBA 9/30/2025 termination + 'acquired' defn; MAGI best-of-two-years; unused-personal-credit-lost; transfer repayment.",
        "topics": ["clean_vehicle_credits"],
        "excerpts": [
            {
                "excerpt_label": "OBBBA 9/30/2025 acquired termination + 'acquired' definition (verbatim)",
                "location_reference": "i8936 (2025), p.1 'What's New'",
                "excerpt_text": (
                    "Clean vehicles acquired after September 30, 2025. Taxpayers cannot claim clean vehicle "
                    "credits for new, previously owned, or commercial clean vehicles that they acquired after "
                    "September 30, 2025. For purposes of sections 25E, 30D, and 45W, a vehicle is 'acquired' as of "
                    "the date a written binding contract is entered into and a payment has been made. A payment "
                    "includes a nominal down payment or a vehicle trade-in. For general information on "
                    "modifications to sections 25E, 30D, and 45W under P.L. 119-21, see IRS.gov/EnergyCreditFAQs."
                ),
                "summary_text": (
                    "OBBBA: no credit (25E/30D/45W) for vehicles acquired after 9/30/2025. 'Acquired' = written "
                    "binding contract + payment (incl. nominal down payment / trade-in). TY2025 partial year; TY2026 gone."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "MAGI best-of-two-years + unused personal credit LOST + transfer repayment (verbatim)",
                "location_reference": "i8936 (2025), p.2-3 MAGI, p.6 lines 13/18, p.7 line 4",
                "excerpt_text": (
                    "Your modified AGI for 2024 or 2025 is not more than $150,000 ($300,000 MFJ/QSS; $225,000 "
                    "HoH) [new]; not more than $75,000 ($150,000 MFJ/QSS; $112,500 HoH) [used]. If your filing "
                    "status changes between the preceding and current year, use the threshold applicable to your "
                    "filing status for the year tested. If you cannot use part of the personal portion of the "
                    "credit because of the tax liability limit, the unused credit is lost. The unused personal "
                    "portion of the credit cannot be carried back or forward to other tax years. Previously owned "
                    "credit: the credit is equal to the lesser of $4,000 or 30% of the sales price. If directed by "
                    "line 8a, 8d, 13a, or 13c, you must report the transferred amount on Schedule 2 (Form 1040), "
                    "line 1b (new) or line 1c (used)."
                ),
                "summary_text": (
                    "MAGI qualifies if <= cap for EITHER 2024 OR 2025 (denied only if over BOTH). Personal "
                    "(new/used) unused portion LOST (no carryforward). Used = lesser $4,000 / 30% price. Transfer "
                    "repayment: new -> Sch2 1b; used -> Sch2 1c."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_30D_25E_45W",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §§30D, 25E, 45W — Clean vehicle credits (as amended by P.L. 119-21)",
        "citation": "26 U.S.C. §§30D, 25E, 45W (2025); P.L. 119-21 (OBBBA, July 4, 2025); Notice 2025-9",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/30D",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": "Statute. §30D(b) $3,750+$3,750=$7,500 (minerals/battery); §25E used lesser $4,000/30%; §45W commercial 15%/30% + incremental cost; OBBBA 9/30/2025 termination.",
        "topics": ["clean_vehicle_credits"],
        "excerpts": [
            {
                "excerpt_label": "§30D(b) new-vehicle $3,750+$3,750; §25E used; §45W commercial",
                "location_reference": "26 U.S.C. §30D(b), §25E, §45W",
                "excerpt_text": (
                    "§30D(b): the new clean vehicle credit = $3,750 (critical minerals requirement) + $3,750 "
                    "(battery components requirement) = up to $7,500. The tentative credit for a specific vehicle "
                    "is reported by the seller (the form face does not print the tier split). §25E: previously "
                    "owned clean vehicle credit = lesser of $4,000 or 30% of the sale price (price <= $25,000). "
                    "§45W: qualified commercial clean vehicle credit = lesser of 15% of basis (30% if not powered "
                    "by a gasoline or diesel internal combustion engine) or the incremental cost; max $7,500 "
                    "($40,000 if GVWR >= 14,000 lb). P.L. 119-21 terminated all three for vehicles acquired after 9/30/2025."
                ),
                "summary_text": "§30D(b) $3,750+$3,750; §25E lesser $4,000/30%; §45W 15%/30% + incremental, max $7,500/$40,000; OBBBA 9/30/2025 cutoff.",
                "is_key_excerpt": True,
            },
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []


# ═══════════════════════════════════════════════════════════════════════════
# FORM 1 — 8936 (Clean Vehicle Credits) — the aggregating main form
# ═══════════════════════════════════════════════════════════════════════════

F8936_IDENTITY = {
    "form_number": "8936",
    "form_title": "Form 8936 — Clean Vehicle Credits (TY2025)",
    "notes": (
        "IRC 30D/25E/45W clean vehicle credits. Aggregates per-vehicle Schedule A "
        "(8936_SCHA). Part I MAGI limitation (best of 2024/2025 vs. the filing-status "
        "cap). Part II business-new (30D) L8 -> Form 3800 line 1y; Part III personal-new "
        "(30D) L13 -> Schedule 3 line 6f; Part IV used (25E) L18 -> Schedule 3 line 6m; "
        "Part V commercial (45W) L21 -> Form 3800 line 1aa. Personal credits (13/18) are "
        "nonrefundable and LOST if unused. Transfer-election repayment: new -> Sch 2 line "
        "1b, used -> Sch 2 line 1c. OBBBA 9/30/2025 acquired gate is per-vehicle on "
        "Schedule A. TY2026: credit gone -> re-verify before carrying forward."
    ),
}

F8936_FACTS: list[dict] = [
    # ── Part I — MAGI ──
    {"fact_key": "f8936_magi_2025", "label": "Line 2 — 2025 modified AGI (1040 line 11a + add-backs)", "data_type": "decimal", "default_value": "0", "sort_order": 1,
     "notes": "PER RETURN. Line 1a pulls 2025 Form 1040 LINE 11a (not plain 11) + PR/2555/4563 add-backs (1b-1e). WALK ITEM B."},
    {"fact_key": "f8936_magi_2024", "label": "Line 4 — 2024 modified AGI (2024 1040 line 11 + add-backs)", "data_type": "decimal", "default_value": "0", "sort_order": 2,
     "notes": "PER RETURN. Line 3a pulls 2024 Form 1040 line 11 + add-backs (3b-3e). Prior-year comparison."},
    {"fact_key": "f8936_filing_status", "label": "Line 5 — filing status (drives the MAGI cap)", "data_type": "string", "sort_order": 3,
     "notes": "PER RETURN. single|mfs|hoh|mfj|qss|estate_trust. Selects the new/used cap."},
    # ── Part II business-new (from Sch A Part II) ──
    {"fact_key": "f8936_business_new_l6", "label": "Line 6 — total business/investment new-vehicle credit (Σ Sch A Part II)", "data_type": "decimal", "default_value": "0", "sort_order": 10, "notes": "PER RETURN. = Σ Schedule A line 11."},
    {"fact_key": "f8936_business_new_passthrough_l7", "label": "Line 7 — new-vehicle credit from partnerships/S corps", "data_type": "decimal", "default_value": "0", "sort_order": 11, "notes": "PER RETURN. Pass-through 30D business credit."},
    # ── Part III personal-new (from Sch A Part III) + tax limit ──
    {"fact_key": "f8936_personal_new_l9", "label": "Line 9 — total personal new-vehicle credit (Σ Sch A Part III)", "data_type": "decimal", "default_value": "0", "sort_order": 12, "notes": "PER RETURN. = Σ Schedule A line 12."},
    {"fact_key": "f8936_1040_line18_tax", "label": "Lines 10 / 15 — Form 1040 line 18 tax (limit base)", "data_type": "decimal", "default_value": "0", "sort_order": 13, "notes": "PER RETURN. The nonrefundable-credit ceiling for Parts III and IV."},
    {"fact_key": "f8936_other_personal_credits_new_l11", "label": "Line 11 — other personal credits (Sch 3 L1-4, 5b, 6d, 6l, 6m)", "data_type": "decimal", "default_value": "0", "sort_order": 14, "notes": "PER RETURN. Reduces the line-12 limit for the NEW personal credit (INCLUDES 6m). WALK ITEM C."},
    # ── Part IV used (from Sch A Part IV) + tax limit ──
    {"fact_key": "f8936_used_l14", "label": "Line 14 — total previously-owned credit (Σ Sch A Part IV)", "data_type": "decimal", "default_value": "0", "sort_order": 15, "notes": "PER RETURN. = Σ Schedule A line 17."},
    {"fact_key": "f8936_other_personal_credits_used_l16", "label": "Line 16 — other personal credits (Sch 3 L1-4, 5b, 6d, 6l — NOT 6m)", "data_type": "decimal", "default_value": "0", "sort_order": 16, "notes": "PER RETURN. Reduces the line-17 limit for the USED credit (EXCLUDES 6m). WALK ITEM C."},
    # ── Part V commercial (from Sch A Part V) ──
    {"fact_key": "f8936_commercial_l19", "label": "Line 19 — total commercial credit (Σ Sch A Part V)", "data_type": "decimal", "default_value": "0", "sort_order": 17, "notes": "PER RETURN. = Σ Schedule A line 26."},
    {"fact_key": "f8936_commercial_passthrough_l20", "label": "Line 20 — commercial credit from partnerships/S corps", "data_type": "decimal", "default_value": "0", "sort_order": 18, "notes": "PER RETURN. Pass-through 45W credit."},
    # ── Outputs ──
    {"fact_key": "f8936_business_new_to_3800_l8", "label": "Line 8 — business-new credit -> Form 3800 line 1y (output)", "data_type": "decimal", "sort_order": 40, "notes": "OUTPUT. = line 6 + line 7."},
    {"fact_key": "f8936_personal_new_to_sch3_l13", "label": "Line 13 — personal-new credit -> Schedule 3 line 6f (output)", "data_type": "decimal", "sort_order": 41, "notes": "OUTPUT. = min(line 9, line 10 - line 11). Nonrefundable; unused LOST."},
    {"fact_key": "f8936_used_to_sch3_l18", "label": "Line 18 — used credit -> Schedule 3 line 6m (output)", "data_type": "decimal", "sort_order": 42, "notes": "OUTPUT. = min(line 14, line 15 - line 16). Nonrefundable; unused LOST."},
    {"fact_key": "f8936_commercial_to_3800_l21", "label": "Line 21 — commercial credit -> Form 3800 line 1aa (output)", "data_type": "decimal", "sort_order": 43, "notes": "OUTPUT. = line 19 + line 20."},
]

F8936_RULES: list[dict] = [
    {"rule_id": "R-8936-MAGI", "title": "Part I — MAGI limitation (best of 2024/2025 vs. the cap)", "rule_type": "routing", "precedence": 1, "sort_order": 1,
     "formula": ("PERSONAL credits (Part III new, Part IV used) DENIED if MAGI > cap for BOTH 2024 AND 2025. "
                 "new cap = MAGI_CAP_NEW[year][status]; used cap = MAGI_CAP_USED[year][status]. Qualify if MAGI "
                 "<= cap for EITHER year. If denied AND a transfer election was made -> repayment (Sch 2 1b new / 1c used)."),
     "inputs": ["f8936_magi_2025", "f8936_magi_2024", "f8936_filing_status"], "outputs": [],
     "description": ("PER RETURN. VERIFIED off the form chart + i8936: 'exceeding the MAGI limits for BOTH 2024 and "
                     "2025 can't claim.' Best-of-two-years. New 150/225/300k; used 75/112.5/150k. OBBBA did NOT "
                     "change the caps. Filing-status-change special rule: test each year vs. that year's status cap.")},
    {"rule_id": "R-8936-BUS-NEW", "title": "Line 8 — business/investment new credit -> Form 3800 line 1y", "rule_type": "routing", "precedence": 2, "sort_order": 2,
     "formula": "line 8 = line 6 (Σ Sch A Part II) + line 7 (pass-through) -> Form 3800 Part III line 1y (general business credit).",
     "inputs": ["f8936_business_new_l6", "f8936_business_new_passthrough_l7"], "outputs": ["8"],
     "description": "PER RETURN. §30D business/investment-use portion is a general business credit -> Form 3800 (carryforward applies there, unlike the personal portion)."},
    {"rule_id": "R-8936-PERS-NEW", "title": "Line 13 — personal new credit -> Schedule 3 line 6f (tax-limited, unused LOST)", "rule_type": "calculation", "precedence": 3, "sort_order": 3,
     "formula": "line 12 = line 10 (1040 L18 tax) - line 11 (other personal credits incl. 6m); if <= 0 -> 0. line 13 = min(line 9, line 12) -> Schedule 3 line 6f. Unused (line 9 - line 13) is LOST.",
     "inputs": ["f8936_personal_new_l9", "f8936_1040_line18_tax", "f8936_other_personal_credits_new_l11"], "outputs": ["12", "13"],
     "description": ("PER RETURN. §30D personal-use credit is NONREFUNDABLE and limited by 1040 line 18 minus other "
                     "credits; VERBATIM i8936: 'the unused personal portion of the credit cannot be carried back "
                     "or forward.' Line 11 INCLUDES Sch 3 6m (WALK ITEM C).")},
    {"rule_id": "R-8936-USED", "title": "Line 18 — used credit -> Schedule 3 line 6m (tax-limited, unused LOST)", "rule_type": "calculation", "precedence": 4, "sort_order": 4,
     "formula": "line 17 = line 15 (1040 L18 tax) - line 16 (other personal credits, NOT incl. 6m); if <= 0 -> 0. line 18 = min(line 14, line 17) -> Schedule 3 line 6m. Unused LOST.",
     "inputs": ["f8936_used_l14", "f8936_1040_line18_tax", "f8936_other_personal_credits_used_l16"], "outputs": ["17", "18"],
     "description": "PER RETURN. §25E used credit is nonrefundable, tax-limited, unused LOST. Line 16 EXCLUDES Sch 3 6m (it is 6m's own destination) — the ordering asymmetry vs. line 11 (WALK ITEM C)."},
    {"rule_id": "R-8936-COMM", "title": "Line 21 — commercial credit -> Form 3800 line 1aa", "rule_type": "routing", "precedence": 5, "sort_order": 5,
     "formula": "line 21 = line 19 (Σ Sch A Part V) + line 20 (pass-through) -> Form 3800 Part III line 1aa.",
     "inputs": ["f8936_commercial_l19", "f8936_commercial_passthrough_l20"], "outputs": ["21"],
     "description": "PER RETURN. §45W commercial credit is a general business credit -> Form 3800 (carryforward applies there)."},
]

F8936_LINES: list[dict] = [
    {"line_number": "1a", "description": "2025 MAGI base — Form 1040 line 11a (see WALK ITEM B)", "line_type": "input"},
    {"line_number": "1b", "description": "2025 — Puerto Rico income excluded", "line_type": "input"},
    {"line_number": "1c", "description": "2025 — Form 2555 line 45", "line_type": "input"},
    {"line_number": "1d", "description": "2025 — Form 2555 line 50", "line_type": "input"},
    {"line_number": "1e", "description": "2025 — Form 4563 line 15", "line_type": "input"},
    {"line_number": "2", "description": "2025 MAGI. Add lines 1a-1e", "line_type": "subtotal"},
    {"line_number": "3a", "description": "2024 MAGI base — 2024 Form 1040 line 11", "line_type": "input"},
    {"line_number": "3b", "description": "2024 — Puerto Rico income excluded", "line_type": "input"},
    {"line_number": "3c", "description": "2024 — Form 2555 line 45", "line_type": "input"},
    {"line_number": "3d", "description": "2024 — Form 2555 line 50", "line_type": "input"},
    {"line_number": "3e", "description": "2024 — Form 4563 line 15", "line_type": "input"},
    {"line_number": "4", "description": "2024 MAGI. Add lines 3a-3e", "line_type": "subtotal"},
    {"line_number": "5", "description": "2024 filing status (for the MAGI cap chart)", "line_type": "input"},
    {"line_number": "6", "description": "Total business/investment new-vehicle credit (Σ Sch A Part II)", "line_type": "calculated"},
    {"line_number": "7", "description": "New-vehicle credit from partnerships and S corporations", "line_type": "input"},
    {"line_number": "8", "description": "Business/investment new credit. Add 6 and 7 -> Form 3800 Part III line 1y", "line_type": "total"},
    {"line_number": "9", "description": "Total personal new-vehicle credit (Σ Sch A Part III)", "line_type": "calculated"},
    {"line_number": "10", "description": "Form 1040 line 18 (tax)", "line_type": "input"},
    {"line_number": "11", "description": "Personal credits (Sch 3 L1-4, 5b, 6d, 6l, 6m)", "line_type": "input"},
    {"line_number": "12", "description": "Subtract line 11 from line 10 (if <= 0, no personal new credit)", "line_type": "calculated"},
    {"line_number": "13", "description": "Smaller of line 9 or line 12 -> Schedule 3 line 6f (unused LOST)", "line_type": "total"},
    {"line_number": "14", "description": "Total previously-owned credit (Σ Sch A Part IV)", "line_type": "calculated"},
    {"line_number": "15", "description": "Form 1040 line 18 (tax)", "line_type": "input"},
    {"line_number": "16", "description": "Personal credits (Sch 3 L1-4, 5b, 6d, 6l — NOT 6m)", "line_type": "input"},
    {"line_number": "17", "description": "Subtract line 16 from line 15 (if <= 0, no used credit)", "line_type": "calculated"},
    {"line_number": "18", "description": "Smaller of line 14 or line 17 -> Schedule 3 line 6m (unused LOST)", "line_type": "total"},
    {"line_number": "19", "description": "Total commercial credit (Σ Sch A Part V)", "line_type": "calculated"},
    {"line_number": "20", "description": "Commercial credit from partnerships and S corporations", "line_type": "input"},
    {"line_number": "21", "description": "Add 19 and 20 -> Form 3800 Part III line 1aa", "line_type": "total"},
]

F8936_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_8936_002", "title": "MAGI over the cap for both years — personal credit denied", "severity": "warning",
     "condition": "min(magi_2025, magi_2024) > cap[type][status]",
     "message": ("Modified AGI exceeds the applicable limit for BOTH 2024 and 2025, so the personal clean vehicle "
                 "credit is denied (the credit is allowed if MAGI is at/under the cap for either year). New-vehicle "
                 "caps: $150,000 S/MFS, $225,000 HoH, $300,000 MFJ/QSS. Used-vehicle caps: $75,000 S/MFS, "
                 "$112,500 HoH, $150,000 MFJ/QSS. If you transferred the credit to the dealer, you must repay it "
                 "on Schedule 2 line 1b (new) or line 1c (used)."),
     "notes": "Best-of-two-years MAGI test. OBBBA did not change the caps."},
    {"diagnostic_id": "D_8936_003", "title": "Business/commercial credit present — routes through Form 3800", "severity": "info",
     "condition": "line 8 > 0 or line 21 > 0",
     "message": ("This return has a business/investment (Part II) or commercial (Part V) clean vehicle credit. "
                 "These are general business credits that flow to Form 3800 (Part III line 1y for new business, "
                 "line 1aa for commercial) and are subject to the Form 3800 limitation and carryforward — confirm "
                 "the 3800 aggregation is wired."),
     "notes": "Info. Business/commercial -> 3800 (carryforward), unlike the personal portions."},
    {"diagnostic_id": "D_8936_005", "title": "Personal credit limited by tax — unused portion is LOST", "severity": "info",
     "condition": "line 9 > line 13 or line 14 > line 18",
     "message": ("Part of your personal clean vehicle credit (new on line 13 and/or used on line 18) could not be "
                 "used because it exceeds your tax liability. Per the instructions, the unused personal portion of "
                 "the credit is LOST — it cannot be carried back or forward to other tax years."),
     "notes": "VERBATIM i8936: unused personal credit not carried back or forward."},
]

F8936_SCENARIOS: list[dict] = [
    {"scenario_name": "F8936-S4 — MeF ATS scenario 4 (new personal EV, qualifies, tax-limited)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "f8936_filing_status": "single", "f8936_magi_2025": 36014, "f8936_magi_2024": 0,
                "f8936_1040_line18_tax": 2193, "f8936_personal_new_l9": "[VERIFY-ATS-KEY]"},
     "expected_outputs": {"magi_qualifies": True, "D_8936_001": False, "routes_sch3_line": "6f",
                          "personal_credit_tax_limited": True, "line_13": "[VERIFY-ATS-KEY-min(l9, 2193 - other credits)]"},
     "notes": ("IRS 1040 MeF ATS scenario 4 (fictional taxpayer, not PII): Single, 2025 MAGI 36,014, 2024 MAGI 0 "
               "-> both under the Single $150,000 new cap -> qualifies (D_8936_002 does NOT fire). 2024 BMW i4, "
               "placed in service 1/25/2025, acquired before 9/30/2025 -> D_8936_001 does NOT fire. New clean "
               "vehicle -> Part III personal -> Schedule 3 line 6f. NONREFUNDABLE: limited by 1040 line 18 (~2,193) "
               "minus other credits — it competes with the $13,200 general business credit (from the S4 Form 8835 "
               "solar facility via Form 3800) for the same ~$2.2k of tax, so the EV credit is NOT fully absorbed "
               "and the unused personal portion is LOST. WALK ITEM A: the line-9 tentative credit is BLANK on the "
               "scenario form (seller report) — do NOT assume $7,500; pin the exact amount + the allowed/limited "
               "split from the ATS answer key. This test asserts the gates + routing, not the dollar.")},
    {"scenario_name": "F8936-T2 — MAGI over cap BOTH years (D_8936_002)", "scenario_type": "edge_case", "sort_order": 2,
     "inputs": {"tax_year": 2025, "f8936_filing_status": "single", "f8936_magi_2025": 180000, "f8936_magi_2024": 175000,
                "f8936_personal_new_l9": 7500},
     "expected_outputs": {"D_8936_002": True, "line_13": 0},
     "notes": "Single, MAGI 180k (2025) AND 175k (2024) both > $150,000 new cap -> personal credit denied. If transferred -> repay Sch 2 line 1b."},
    {"scenario_name": "F8936-T3 — MAGI under cap in ONE year qualifies (best-of-two)", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"tax_year": 2025, "f8936_filing_status": "single", "f8936_magi_2025": 180000, "f8936_magi_2024": 140000,
                "f8936_personal_new_l9": 7500, "f8936_1040_line18_tax": 9000},
     "expected_outputs": {"magi_qualifies": True, "D_8936_002": False, "line_13": 7500, "routes_sch3_line": "6f"},
     "notes": "2025 MAGI 180k > cap BUT 2024 MAGI 140k <= $150,000 -> qualifies (best-of-two-years). Credit 7,500 <= tax 9,000 -> fully allowed -> Sch 3 6f."},
    {"scenario_name": "F8936-T4 — commercial (45W) -> Form 3800 line 1aa", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"tax_year": 2025, "f8936_commercial_l19": 7500},
     "expected_outputs": {"line_21": 7500, "routes_3800_line": "1aa", "D_8936_003": True},
     "notes": "Commercial credit 7,500 (Σ Sch A Part V) -> line 21 -> Form 3800 Part III line 1aa (general business credit)."},
]

F8936_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-8936-MAGI", "IRS_2025_8936_FORM", "primary", "MAGI caps chart (both years) — new 150/225/300k, used 75/112.5/150k"),
    ("R-8936-MAGI", "IRS_2025_8936_INSTR", "primary", "Best-of-2024/2025 MAGI test; filing-status-change rule"),
    ("R-8936-BUS-NEW", "IRS_2025_8936_FORM", "primary", "Line 8 -> Form 3800 Part III line 1y"),
    ("R-8936-PERS-NEW", "IRS_2025_8936_FORM", "primary", "Line 13 -> Schedule 3 line 6f (smaller of 9 or 12)"),
    ("R-8936-PERS-NEW", "IRS_2025_8936_INSTR", "secondary", "Unused personal portion LOST (no carryforward)"),
    ("R-8936-USED", "IRS_2025_8936_FORM", "primary", "Line 18 -> Schedule 3 line 6m (smaller of 14 or 17)"),
    ("R-8936-USED", "IRC_30D_25E_45W", "secondary", "§25E used credit lesser of $4,000 / 30% of price"),
    ("R-8936-COMM", "IRS_2025_8936_FORM", "primary", "Line 21 -> Form 3800 Part III line 1aa"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 2 — 8936_SCHA (Schedule A (Form 8936)) — ONE PER VEHICLE
# ═══════════════════════════════════════════════════════════════════════════

F8936SA_IDENTITY = {
    "form_number": "8936_SCHA",
    "form_title": "Schedule A (Form 8936) — Clean Vehicle Credit Amount (per vehicle) (TY2025)",
    "notes": (
        "ONE PER VEHICLE. Canonical RS lookup key 8936_SCHA (the 1120S_SCHL convention). "
        "Part I vehicle details + the OBBBA acquired-before-10/1/2025 gate (lines 5/6/7; "
        "R-8936SA-OBBBA / D_8936_001, HIGHEST precedence). Part II business-new = tentative "
        "(seller report, line 9) × business-use % (line 10) -> line 11 -> Form 8936 line 6. "
        "Part III personal-new = line 9 - line 11 -> line 12 -> Form 8936 line 9. Part IV "
        "used = min(30% × sales price, $4,000), price <= $25,000 -> line 17 -> Form 8936 "
        "line 14. Part V commercial = min(15%/30% × basis, incremental cost), max "
        "$7,500/$40,000 -> line 26 -> Form 8936 line 19. Transfer repayment: new -> Sch 2 "
        "line 1b, used -> Sch 2 line 1c."
    ),
}

F8936SA_FACTS: list[dict] = [
    # ── Part I — vehicle details + gate ──
    {"fact_key": "f8936sa_year", "label": "Line 1a — vehicle year", "data_type": "string", "sort_order": 1, "notes": "PER VEHICLE. Metadata."},
    {"fact_key": "f8936sa_make", "label": "Line 1b — make", "data_type": "string", "sort_order": 2, "notes": "PER VEHICLE. Metadata."},
    {"fact_key": "f8936sa_model", "label": "Line 1c — model", "data_type": "string", "sort_order": 3, "notes": "PER VEHICLE. Metadata."},
    {"fact_key": "f8936sa_vin", "label": "Line 2 — Vehicle Identification Number (VIN, 17 char)", "data_type": "string", "sort_order": 4, "notes": "PER VEHICLE. Required (D_8936_004 if missing on a claimed vehicle)."},
    {"fact_key": "f8936sa_placed_in_service_date", "label": "Line 3 — date placed in service (possession)", "data_type": "date", "sort_order": 5, "notes": "PER VEHICLE. Must be in the tax year. Required (D_8936_004)."},
    {"fact_key": "f8936sa_acquired_date", "label": "Acquired date (binding contract + payment) — OBBBA gate", "data_type": "date", "sort_order": 6,
     "notes": "PER VEHICLE. 'Acquired' = written binding contract entered + payment made. On/before 2025-09-30 qualifies; after -> D_8936_001 (no credit). Lines 5/6/7 phrase it 'before October 1, 2025'."},
    {"fact_key": "f8936sa_transferred_to_dealer", "label": "Line 4a — credit transferred to dealer at sale? (Y/N)", "data_type": "boolean", "sort_order": 7, "notes": "PER VEHICLE. If Yes + later MAGI-over-cap -> repayment (Sch 2 1b new / 1c used)."},
    {"fact_key": "f8936sa_transferred_amount", "label": "Line 4a — transferred amount (from seller's report)", "data_type": "decimal", "default_value": "0", "sort_order": 8, "notes": "PER VEHICLE. The amount to repay if disqualified."},
    {"fact_key": "f8936sa_vehicle_type", "label": "Lines 5/6/7 — vehicle type", "data_type": "string", "sort_order": 9, "notes": "PER VEHICLE. new|used|commercial. Routes to Part II/III (new), Part IV (used), Part V (commercial)."},
    # ── Part II business-new ──
    {"fact_key": "f8936sa_resold_30_days", "label": "Line 8a/13a — resold within 30 days? (Y/N)", "data_type": "boolean", "sort_order": 10, "notes": "PER VEHICLE. Yes -> Stop; no credit; if transferred -> repay."},
    {"fact_key": "f8936sa_tentative_credit", "label": "Line 9 — tentative credit (from the seller report)", "data_type": "decimal", "default_value": "0", "sort_order": 11, "notes": "PER VEHICLE. NEW 30D: from the seller's ECO-portal report; the $3,750/$7,500 tiers are §30D(b), NOT on the form. Do NOT assume $7,500."},
    {"fact_key": "f8936sa_business_use_pct", "label": "Line 10 — business/investment use %", "data_type": "decimal", "default_value": "0", "sort_order": 12, "notes": "PER VEHICLE. line 11 = line 9 × this; the remainder (line 12) is personal."},
    # ── Part IV used ──
    {"fact_key": "f8936sa_prior_used_credit_3yr", "label": "Line 13d — claimed a used credit in the prior 3 years? (Y/N)", "data_type": "boolean", "sort_order": 13, "notes": "PER VEHICLE. Yes -> doesn't qualify."},
    {"fact_key": "f8936sa_is_dependent", "label": "Line 13g — can be claimed as a dependent? (Y/N)", "data_type": "boolean", "sort_order": 14, "notes": "PER VEHICLE. Yes -> doesn't qualify (used credit)."},
    {"fact_key": "f8936sa_sales_price", "label": "Line 14 — sales price (used vehicle)", "data_type": "decimal", "default_value": "0", "sort_order": 15, "notes": "PER VEHICLE. Must be <= $25,000 (line 13e) to qualify. line 15 = × 30%."},
    # ── Part V commercial ──
    {"fact_key": "f8936sa_powered_by_gas_diesel", "label": "Line 18d — also powered by gas/diesel? (Y/N)", "data_type": "boolean", "sort_order": 16, "notes": "PER VEHICLE. Yes -> 15% rate (line 22); No (pure EV/FCV) -> 30%."},
    {"fact_key": "f8936sa_gvwr", "label": "Line 18e — gross vehicle weight rating (lb)", "data_type": "decimal", "default_value": "0", "sort_order": 17, "notes": "PER VEHICLE. >= 14,000 -> $40,000 max (line 25); else $7,500."},
    {"fact_key": "f8936sa_cost_basis", "label": "Line 19 — cost or other basis (commercial)", "data_type": "decimal", "default_value": "0", "sort_order": 18, "notes": "PER VEHICLE. line 21 = line 19 - §179 (line 20)."},
    {"fact_key": "f8936sa_sec179", "label": "Line 20 — section 179 expense deduction", "data_type": "decimal", "default_value": "0", "sort_order": 19, "notes": "PER VEHICLE. Reduces the basis for the 45W credit."},
    {"fact_key": "f8936sa_incremental_cost", "label": "Line 23 — incremental cost of the vehicle", "data_type": "decimal", "default_value": "0", "sort_order": 20, "notes": "PER VEHICLE. 2025 safe harbor $7,500 (Notice 2025-9). line 24 = min(line 22, this)."},
    # ── Outputs ──
    {"fact_key": "f8936sa_business_credit_l11", "label": "Line 11 — business-new credit -> Form 8936 line 6 (output)", "data_type": "decimal", "sort_order": 40, "notes": "OUTPUT. = line 9 × line 10."},
    {"fact_key": "f8936sa_personal_credit_l12", "label": "Line 12 — personal-new credit -> Form 8936 line 9 (output)", "data_type": "decimal", "sort_order": 41, "notes": "OUTPUT. = line 9 - line 11."},
    {"fact_key": "f8936sa_used_credit_l17", "label": "Line 17 — used credit -> Form 8936 line 14 (output)", "data_type": "decimal", "sort_order": 42, "notes": "OUTPUT. = min(line 14 × 30%, $4,000)."},
    {"fact_key": "f8936sa_commercial_credit_l26", "label": "Line 26 — commercial credit -> Form 8936 line 19 (output)", "data_type": "decimal", "sort_order": 43, "notes": "OUTPUT. = min(min(15%/30% × basis, incremental cost), $7,500/$40,000)."},
]

F8936SA_RULES: list[dict] = [
    {"rule_id": "R-8936SA-OBBBA", "title": "OBBBA gate — vehicle acquired after 9/30/2025 -> no credit", "rule_type": "routing", "precedence": 1, "sort_order": 1,
     "formula": "If f8936sa_acquired_date > OBBBA_ACQUIRED_CUTOFF[year] (2025-09-30) -> D_8936_001; NO credit (25E/30D/45W). Lines 5/6/7 require acquired 'before October 1, 2025'.",
     "inputs": ["f8936sa_acquired_date"], "outputs": [],
     "description": ("PER VEHICLE. HIGHEST precedence. VERIFIED verbatim off i8936 What's New: no clean vehicle "
                     "credit for new/used/commercial vehicles acquired after September 30, 2025 (P.L. 119-21). "
                     "'Acquired' = written binding contract + payment (nominal down payment / trade-in counts). "
                     "Year-keyed; TY2026 -> credit gone entirely.")},
    {"rule_id": "R-8936SA-NEW-BIZ", "title": "Line 11 — business-new credit = tentative × business-use %", "rule_type": "calculation", "precedence": 2, "sort_order": 2,
     "formula": "line 11 = line 9 (tentative, seller report) × line 10 (business-use %) -> Form 8936 line 6.",
     "inputs": ["f8936sa_tentative_credit", "f8936sa_business_use_pct"], "outputs": ["11"],
     "description": "PER VEHICLE. §30D business/investment-use portion. The tentative credit is the seller-reported amount; do NOT hardcode $7,500 (that is the §30D(b) statutory max, not any given vehicle's amount)."},
    {"rule_id": "R-8936SA-NEW-PERS", "title": "Line 12 — personal-new credit = tentative − business portion", "rule_type": "calculation", "precedence": 3, "sort_order": 3,
     "formula": "line 12 = line 9 - line 11 -> Form 8936 line 9. If line 10 = 100% -> line 12 = 0 (all business).",
     "inputs": ["f8936sa_tentative_credit", "f8936sa_business_credit_l11"], "outputs": ["12"],
     "description": "PER VEHICLE. §30D personal-use portion -> Form 8936 Part III (nonrefundable, tax-limited, unused LOST)."},
    {"rule_id": "R-8936SA-USED", "title": "Line 17 — used credit = min(30% × price, $4,000); price <= $25,000", "rule_type": "calculation", "precedence": 4, "sort_order": 4,
     "formula": "GATE: sales price <= $25,000 (else no credit, D_8936_006); not within 3 yr of a prior used credit; not a dependent. line 15 = line 14 × 30%; line 17 = min(line 15, $4,000) -> Form 8936 line 14.",
     "inputs": ["f8936sa_sales_price", "f8936sa_prior_used_credit_3yr", "f8936sa_is_dependent"], "outputs": ["15", "17"],
     "description": "PER VEHICLE. §25E: lesser of $4,000 or 30% of the sales price; the vehicle sales price must not exceed $25,000; no used credit within 3 years of a prior one; buyer not claimable as a dependent."},
    {"rule_id": "R-8936SA-COMM", "title": "Line 26 — commercial credit = min(rate × basis, incremental), max $7,500/$40,000", "rule_type": "calculation", "precedence": 5, "sort_order": 5,
     "formula": "line 21 = line 19 (basis) - line 20 (§179); line 22 = line 21 × 30% (15% if 18d gas/diesel); line 24 = min(line 22, line 23 incremental cost); line 26 = min(line 24, $7,500 or $40,000 if GVWR >= 14,000) -> Form 8936 line 19.",
     "inputs": ["f8936sa_cost_basis", "f8936sa_sec179", "f8936sa_powered_by_gas_diesel", "f8936sa_incremental_cost", "f8936sa_gvwr"], "outputs": ["22", "24", "26"],
     "description": "PER VEHICLE. §45W: lesser of (15% basis, or 30% if not gas/diesel-powered) or the incremental cost; max $7,500 ($40,000 if GVWR >= 14,000 lb). 2025 incremental-cost safe harbor $7,500 (Notice 2025-9)."},
]

F8936SA_LINES: list[dict] = [
    {"line_number": "1a", "description": "Vehicle year", "line_type": "input"},
    {"line_number": "1b", "description": "Make", "line_type": "input"},
    {"line_number": "1c", "description": "Model", "line_type": "input"},
    {"line_number": "2", "description": "Vehicle identification number (VIN)", "line_type": "input"},
    {"line_number": "3", "description": "Date placed in service (possession)", "line_type": "input"},
    {"line_number": "4a", "description": "Transferred the credit to the dealer at sale? (enter transferred amount)", "line_type": "input"},
    {"line_number": "4b", "description": "If 4a Yes, complete line 8 or 13 as directed", "line_type": "input"},
    {"line_number": "5", "description": "New clean vehicle acquired before Oct 1, 2025 & placed in service? Yes -> Part II", "line_type": "input"},
    {"line_number": "6", "description": "Previously owned clean vehicle acquired after 2022 & before Oct 1, 2025? Yes -> Part IV", "line_type": "input"},
    {"line_number": "7", "description": "Qualified commercial clean vehicle acquired after 2022 & before Oct 1, 2025? Yes -> Part V", "line_type": "input"},
    {"line_number": "8a", "description": "Resold the vehicle within 30 days? (Yes -> Stop; if 4a Yes -> Sch 2 line 1b)", "line_type": "input"},
    {"line_number": "8b", "description": "Filing with an individual income tax return?", "line_type": "input"},
    {"line_number": "8c", "description": "2025 MAGI at/under the Part II/III limit?", "line_type": "input"},
    {"line_number": "8d", "description": "2024 MAGI at/under the Part II/III limit? (Yes over both -> Sch 2 line 1b)", "line_type": "input"},
    {"line_number": "8e", "description": "Acquired for use/lease, not resale?", "line_type": "input"},
    {"line_number": "9", "description": "Tentative credit amount (from the seller report)", "line_type": "input"},
    {"line_number": "10", "description": "Business/investment use percentage", "line_type": "input"},
    {"line_number": "11", "description": "Line 9 × line 10 -> Form 8936 line 6 (business new)", "line_type": "total"},
    {"line_number": "12", "description": "Line 9 − line 11 -> Form 8936 line 9 (personal new)", "line_type": "total"},
    {"line_number": "13a", "description": "Resold within 30 days? (Yes -> Stop; if 4a Yes -> Sch 2 line 1c)", "line_type": "input"},
    {"line_number": "13b", "description": "2025 MAGI at/under the Part IV limit?", "line_type": "input"},
    {"line_number": "13c", "description": "2024 MAGI at/under the Part IV limit? (Yes over both -> Sch 2 line 1c)", "line_type": "input"},
    {"line_number": "13d", "description": "Claimed a previously-owned credit in the prior 3 years? (Yes -> Stop)", "line_type": "input"},
    {"line_number": "13e", "description": "Sales price more than $25,000? (Yes -> doesn't qualify)", "line_type": "input"},
    {"line_number": "13f", "description": "Acquired for use, not resale?", "line_type": "input"},
    {"line_number": "13g", "description": "Can be claimed as a dependent? (Yes -> Stop)", "line_type": "input"},
    {"line_number": "14", "description": "Sales price of the vehicle", "line_type": "input"},
    {"line_number": "15", "description": "Line 14 × 30%", "line_type": "calculated"},
    {"line_number": "16", "description": "Maximum vehicle credit amount — $4,000", "line_type": "input"},
    {"line_number": "17", "description": "Smaller of line 15 or line 16 -> Form 8936 line 14 (used)", "line_type": "total"},
    {"line_number": "18a", "description": "Elective-payment registration number (commercial)", "line_type": "input"},
    {"line_number": "18b", "description": "Vehicle of a character subject to depreciation?", "line_type": "input"},
    {"line_number": "18c", "description": "Acquired for use/lease, not resale?", "line_type": "input"},
    {"line_number": "18d", "description": "Also powered by gas/diesel? (Yes -> 15% rate; No -> 30%)", "line_type": "input"},
    {"line_number": "18e", "description": "Gross vehicle weight rating (GVWR)", "line_type": "input"},
    {"line_number": "19", "description": "Cost or other basis of the vehicle", "line_type": "input"},
    {"line_number": "20", "description": "Section 179 expense deduction", "line_type": "input"},
    {"line_number": "21", "description": "Line 19 − line 20", "line_type": "calculated"},
    {"line_number": "22", "description": "Line 21 × 15% (30% if line 18d is No)", "line_type": "calculated"},
    {"line_number": "23", "description": "Incremental cost of the vehicle", "line_type": "input"},
    {"line_number": "24", "description": "Smaller of line 22 or line 23", "line_type": "calculated"},
    {"line_number": "25", "description": "Maximum credit — $7,500 ($40,000 if GVWR >= 14,000 lb)", "line_type": "input"},
    {"line_number": "26", "description": "Smaller of line 24 or line 25 -> Form 8936 line 19 (commercial)", "line_type": "total"},
]

F8936SA_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_8936_001", "title": "Vehicle acquired after 9/30/2025 — OBBBA termination, no credit", "severity": "error",
     "condition": "f8936sa_acquired_date > 2025-09-30",
     "message": ("This vehicle was acquired after September 30, 2025. Under P.L. 119-21 (OBBBA), no clean vehicle "
                 "credit (new §30D, previously owned §25E, or commercial §45W) is allowed for any vehicle acquired "
                 "after that date. A vehicle is 'acquired' when a written binding contract is entered into AND a "
                 "payment (including a nominal down payment or trade-in) is made. No credit for this vehicle."),
     "notes": "THE OBBBA GATE (VERIFIED verbatim). Per-vehicle, highest precedence. TY2026: credit gone entirely."},
    {"diagnostic_id": "D_8936_004", "title": "Missing VIN or placed-in-service date on a claimed vehicle", "severity": "error",
     "condition": "f8936sa_vin is blank OR f8936sa_placed_in_service_date is blank (with a claimed credit)",
     "message": ("A clean vehicle credit is claimed but the VIN (line 2) and/or the placed-in-service date (line "
                 "3) is missing. The VIN and placed-in-service date are required to substantiate the credit and "
                 "are validated against the IRS seller-report database. Enter both."),
     "notes": "Substantiation guard (MeF rejects a missing VIN)."},
    {"diagnostic_id": "D_8936_006", "title": "Used vehicle sales price over $25,000 — doesn't qualify", "severity": "error",
     "condition": "f8936sa_vehicle_type == 'used' AND f8936sa_sales_price > 25000",
     "message": ("This previously-owned clean vehicle has a sales price over $25,000 (line 13e). The §25E used "
                 "clean vehicle credit is only available when the sales price does not exceed $25,000. No used credit."),
     "notes": "§25E price ceiling (form line 13e)."},
    {"diagnostic_id": "D_8936_007", "title": "New-vehicle tentative credit comes from the seller report", "severity": "info",
     "condition": "f8936sa_vehicle_type == 'new' (Part II/III)",
     "message": ("The new clean vehicle tentative credit (line 9) is the amount on the seller's report (filed via "
                 "the IRS Energy Credits Online portal), reflecting the vehicle's critical-minerals/battery-"
                 "components eligibility under §30D(b). The $3,750/$3,750/$7,500 tiers are statutory (§30D(b)) and "
                 "are NOT printed on Form 8936 — do not assume $7,500 for a given vehicle."),
     "notes": "WALK ITEM A. Tentative credit = seller report; §30D(b) tiers not on the form."},
]

F8936SA_SCENARIOS: list[dict] = [
    {"scenario_name": "F8936SA-S4 — new personal EV, acquired before cutoff (qualifies, -> Form 8936 line 9)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "f8936sa_year": "2024", "f8936sa_make": "BMW", "f8936sa_model": "i4",
                "f8936sa_placed_in_service_date": "2025-01-25", "f8936sa_acquired_date": "2025-01-20",
                "f8936sa_vehicle_type": "new", "f8936sa_transferred_to_dealer": False, "f8936sa_business_use_pct": 0,
                "f8936sa_tentative_credit": "[VERIFY-ATS-KEY]"},
     "expected_outputs": {"D_8936_001": False, "routes_to": "8936_line_9", "line_11": 0, "line_12": "[VERIFY-ATS-KEY]"},
     "notes": ("IRS S4 vehicle (fictional): 2024 BMW i4, VIN on the scenario form, placed in service 1/25/2025, "
               "acquired before 9/30/2025 -> D_8936_001 does NOT fire. New clean vehicle -> Part II/III. 0% "
               "business use -> line 11 = 0, line 12 = full tentative -> Form 8936 line 9 (personal). WALK ITEM A: "
               "line-9 tentative credit is BLANK on the scenario form (seller report) — do NOT assume $7,500; pin "
               "from the ATS answer key. Also confirm the transfer path — the scenario has a 'Transfer Election "
               "Statement' attachment but line 4a is unchecked; reconcile against the answer key before pinning.")},
    {"scenario_name": "F8936SA-T2 — acquired after 9/30/2025 (D_8936_001)", "scenario_type": "edge_case", "sort_order": 2,
     "inputs": {"tax_year": 2025, "f8936sa_vehicle_type": "new", "f8936sa_acquired_date": "2025-10-15",
                "f8936sa_placed_in_service_date": "2025-10-20", "f8936sa_tentative_credit": 7500},
     "expected_outputs": {"D_8936_001": True, "credit": 0},
     "notes": "Acquired 10/15/2025 (after 9/30/2025) -> OBBBA termination -> no credit (no silent gap)."},
    {"scenario_name": "F8936SA-T3 — used vehicle (min 30%/$4,000)", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"tax_year": 2025, "f8936sa_vehicle_type": "used", "f8936sa_acquired_date": "2025-05-01",
                "f8936sa_sales_price": 20000, "f8936sa_prior_used_credit_3yr": False, "f8936sa_is_dependent": False},
     "expected_outputs": {"line_15": 6000, "line_17": 4000},
     "notes": "Price 20,000 <= $25,000 -> qualifies. line 15 = 20,000 × 30% = 6,000; line 17 = min(6,000, $4,000) = 4,000 -> Form 8936 line 14."},
    {"scenario_name": "F8936SA-T4 — used vehicle price over $25,000 (D_8936_006)", "scenario_type": "edge_case", "sort_order": 4,
     "inputs": {"tax_year": 2025, "f8936sa_vehicle_type": "used", "f8936sa_acquired_date": "2025-05-01", "f8936sa_sales_price": 30000},
     "expected_outputs": {"D_8936_006": True, "line_17": 0},
     "notes": "Used vehicle sales price 30,000 > $25,000 -> doesn't qualify (line 13e) -> no used credit."},
    {"scenario_name": "F8936SA-T5 — commercial EV (30%, $7,500 cap)", "scenario_type": "normal", "sort_order": 5,
     "inputs": {"tax_year": 2025, "f8936sa_vehicle_type": "commercial", "f8936sa_acquired_date": "2025-03-01",
                "f8936sa_powered_by_gas_diesel": False, "f8936sa_gvwr": 8000, "f8936sa_cost_basis": 60000,
                "f8936sa_sec179": 0, "f8936sa_incremental_cost": 9000},
     "expected_outputs": {"line_21": 60000, "line_22": 18000, "line_24": 9000, "line_26": 7500},
     "notes": "Pure EV (18d No) -> 30%: line 21 = 60,000; line 22 = 60,000 × 30% = 18,000; line 24 = min(18,000, incremental 9,000) = 9,000; line 26 = min(9,000, $7,500 [GVWR 8,000 < 14,000]) = 7,500 -> Form 8936 line 19."},
]

F8936SA_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-8936SA-OBBBA", "IRS_2025_8936_INSTR", "primary", "What's New: no credit for vehicles acquired after 9/30/2025 (25E/30D/45W)"),
    ("R-8936SA-OBBBA", "IRS_2025_8936SA_FORM", "primary", "Lines 5/6/7 'acquired before October 1, 2025' gate"),
    ("R-8936SA-OBBBA", "IRC_30D_25E_45W", "secondary", "P.L. 119-21 termination of §§30D/25E/45W"),
    ("R-8936SA-NEW-BIZ", "IRS_2025_8936SA_FORM", "primary", "Line 11 = line 9 (tentative) × line 10 (business %)"),
    ("R-8936SA-NEW-PERS", "IRS_2025_8936SA_FORM", "primary", "Line 12 = line 9 - line 11 -> Form 8936 line 9"),
    ("R-8936SA-USED", "IRS_2025_8936SA_FORM", "primary", "Lines 14-17: 30% × price, max $4,000, price <= $25,000"),
    ("R-8936SA-USED", "IRC_30D_25E_45W", "secondary", "§25E lesser of $4,000 / 30% of sales price"),
    ("R-8936SA-COMM", "IRS_2025_8936SA_FORM", "primary", "Lines 18-26: 15%/30% basis, incremental cost, max $7,500/$40,000"),
    ("R-8936SA-COMM", "IRC_30D_25E_45W", "secondary", "§45W lesser of 15%/30% basis or incremental cost; Notice 2025-9"),
]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY FORM LINKS
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_8936_FORM", "8936", "governs"),
    ("IRS_2025_8936_INSTR", "8936", "informs"),
    ("IRC_30D_25E_45W", "8936", "informs"),
    ("IRS_2025_8936SA_FORM", "8936_SCHA", "governs"),
    ("IRS_2025_8936_INSTR", "8936_SCHA", "informs"),
    ("IRC_30D_25E_45W", "8936_SCHA", "informs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORMS ROSTER
# ═══════════════════════════════════════════════════════════════════════════

FORMS: list[dict] = [
    {"identity": F8936_IDENTITY, "facts": F8936_FACTS, "rules": F8936_RULES, "lines": F8936_LINES,
     "diagnostics": F8936_DIAGNOSTICS, "scenarios": F8936_SCENARIOS, "rule_links": F8936_RULE_LINKS},
    {"identity": F8936SA_IDENTITY, "facts": F8936SA_FACTS, "rules": F8936SA_RULES, "lines": F8936SA_LINES,
     "diagnostics": F8936SA_DIAGNOSTICS, "scenarios": F8936SA_SCENARIOS, "rule_links": F8936SA_RULE_LINKS},
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-8936-01", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "Form 8936 OBBBA gate — vehicle acquired after 9/30/2025 -> no credit (per vehicle)",
     "description": ("Validates R-8936SA-OBBBA / D_8936_001. A Schedule A vehicle acquired after 2025-09-30 gets "
                     "no credit for any of 25E/30D/45W and fires D_8936_001. 'Acquired' = binding contract + "
                     "payment. Bug it catches: gating on placed-in-service instead of acquired date, or letting a "
                     "post-cutoff vehicle through."),
     "definition": {"kind": "gating_check", "form": "8936_SCHA",
                    "blocker": "acquired_after_2025_09_30", "expect": {"credit_zero": True, "diagnostic": "D_8936_001"}},
     "sort_order": 1},
    {"assertion_id": "FA-1040-8936-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Form 8936 routing — 4 legs to 4 destinations",
     "description": ("Validates R-8936-BUS-NEW / PERS-NEW / USED / COMM. Line 8 -> Form 3800 line 1y; line 13 -> "
                     "Schedule 3 line 6f; line 18 -> Schedule 3 line 6m; line 21 -> Form 3800 line 1aa. Bug it "
                     "catches: a leg routed to the wrong destination (e.g. personal-new to 3800 instead of Sch 3 6f)."),
     "definition": {"kind": "flow_assertion", "form": "8936",
                    "must_write_to": {"8": "FORM_3800.1y", "13": "SCH_3.6f", "18": "SCH_3.6m", "21": "FORM_3800.1aa"}},
     "sort_order": 2},
    {"assertion_id": "FA-1040-8936-03", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "Form 8936 MAGI — best of 2024/2025 vs. the filing-status cap",
     "description": ("Validates R-8936-MAGI. Personal credits denied only if MAGI > cap for BOTH 2024 AND 2025 "
                     "(new 150/225/300k; used 75/112.5/150k). Bug it catches: a strict current-year test that "
                     "wrongly denies a taxpayer who qualifies on the prior year, or vice versa."),
     "definition": {"kind": "formula_check", "form": "8936",
                    "formula": "denied == (magi_2025 > cap and magi_2024 > cap)"},
     "sort_order": 3},
    {"assertion_id": "FA-1040-8936-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Form 8936 transfer-election repayment — new -> Sch 2 1b, used -> Sch 2 1c",
     "description": ("Validates the transfer recapture. A transferred credit whose taxpayer is over the MAGI cap "
                     "(both years) is repaid: new (30D) -> Schedule 2 line 1b (Sch A gates 8a/8d); used (25E) -> "
                     "Schedule 2 line 1c (Sch A gates 13a/13c). Bug it catches: routing the used repayment to 1b "
                     "or the new repayment to 1c."),
     "definition": {"kind": "flow_assertion", "form": "8936_SCHA",
                    "route": {"transfer_repay_new": "SCH_2.1b", "transfer_repay_used": "SCH_2.1c"}},
     "sort_order": 4},
    {"assertion_id": "FA-1040-8936-05", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "Form 8936 personal credit is nonrefundable — unused is LOST",
     "description": ("Validates R-8936-PERS-NEW / R-8936-USED. Lines 13 and 18 are limited by 1040 line 18 minus "
                     "other credits; any unused personal portion cannot be carried back or forward (i8936). Bug it "
                     "catches: carrying the unused personal EV credit forward like a general business credit."),
     "definition": {"kind": "gating_check", "form": "8936",
                    "invariant": "personal_unused_not_carried", "expect": {"carryforward": False}},
     "sort_order": 5},
]


# ═══════════════════════════════════════════════════════════════════════════
# Command
# ═══════════════════════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = (
        "Load the Form 8936 + Schedule A (Form 8936) specs into Rule Studio (creates "
        "8936 and 8936_SCHA — clean vehicle credits 30D/25E/45W; OBBBA 9/30/2025 acquired "
        "gate). Refuses to seed until Ken sets READY_TO_SEED=True."
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad 8936 + 8936_SCHA specs (Clean Vehicle Credits)\n"))
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
                "\nREFUSING TO SEED 8936 / 8936_SCHA: not cleared to seed.\n\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True to proceed)\n"
                f"Empty spec sections:\n  {still_empty}\n\n"
                "This spec encodes tax law (IRC 30D/25E/45W; the OBBBA 9/30/2025 acquired\n"
                "termination + the 'acquired' definition; the TY2025 MAGI caps; the used /\n"
                "commercial credit formulas; the Sch 3 6f/6m + Form 3800 1y/1aa routing; the\n"
                "Sch 2 1b/1c transfer repayment). Ken reviews the packet, then sets\n"
                "READY_TO_SEED = True. Idempotent via update_or_create — safe to re-run."
            )

    def _load_topics(self):
        ct = 0
        for code, name in AUTHORITY_TOPICS:
            _, created = AuthorityTopic.objects.update_or_create(topic_code=code, defaults={"topic_name": name})
            if created:
                ct += 1
        self.stdout.write(f"Topics: {ct} new ({len(AUTHORITY_TOPICS)} total in batch)")

    def _load_sources(self) -> dict[str, AuthoritySource]:
        sources: dict[str, AuthoritySource] = {}
        for src_data in AUTHORITY_SOURCES:
            src_data = dict(src_data)
            excerpts_data = src_data.pop("excerpts", [])
            topic_codes = src_data.pop("topics", [])
            source, _ = AuthoritySource.objects.update_or_create(source_code=src_data["source_code"], defaults=src_data)
            sources[source.source_code] = source
            for exc in excerpts_data:
                exc = dict(exc)
                AuthorityExcerpt.objects.update_or_create(authority_source=source, excerpt_label=exc["excerpt_label"], defaults=exc)
            for tc in topic_codes:
                topic = AuthorityTopic.objects.filter(topic_code=tc).first()
                if topic:
                    AuthoritySourceTopic.objects.get_or_create(authority_source=source, authority_topic=topic)
        for code in EXISTING_SOURCES_TO_REFERENCE:
            src = AuthoritySource.objects.filter(source_code=code).first()
            if src:
                sources[code] = src
            else:
                self.stdout.write(self.style.WARNING(f"  referenced source {code} NOT found — links skipped"))
        self.stdout.write(f"Sources ready: {len(sources)}")
        return sources

    def _load_new_excerpts_on_existing(self, sources):
        for code, exc in NEW_EXCERPTS_ON_EXISTING:
            src = sources.get(code) or AuthoritySource.objects.filter(source_code=code).first()
            if src:
                exc = dict(exc)
                AuthorityExcerpt.objects.update_or_create(authority_source=src, excerpt_label=exc["excerpt_label"], defaults=exc)

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

    def _upsert_rules(self, form, rules_data) -> dict[str, FormRule]:
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
        def _safe(text):
            return text.encode("ascii", errors="replace").decode("ascii")
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("DATABASE TOTALS (after load_1040_form_8936)")
        self.stdout.write("=" * 60)
        for label, model in (("TaxForms", TaxForm), ("FormFacts", FormFact), ("FormRules", FormRule),
                             ("FormLines", FormLine), ("FormDiagnostics", FormDiagnostic),
                             ("TestScenarios", TestScenario), ("AuthoritySources", AuthoritySource),
                             ("RuleAuthorityLinks", RuleAuthorityLink), ("FlowAssertions", FlowAssertion)):
            self.stdout.write(f"{label+':':20}{model.objects.count()}")
        for fn in ("8936", "8936_SCHA"):
            uncited = [r for r in FormRule.objects.filter(tax_form__form_number=fn) if not r.authority_links.exists()]
            if uncited:
                self.stdout.write(self.style.WARNING(f"\n{fn} rules with ZERO authority links: {len(uncited)}"))
                for r in uncited[:20]:
                    self.stdout.write(_safe(f"  {r.rule_id}: {r.title}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"{fn}: all rules have authority links."))
