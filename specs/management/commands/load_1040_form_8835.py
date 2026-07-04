"""Load the Form 8835 spec — Renewable Electricity Production Credit (IRC §45).

Creates ONE new TaxForm:

  - 8835 (Renewable Electricity Production Credit) — NEW. The §45 general business
    credit for electricity produced from qualified renewable resources at a qualified
    U.S. facility and sold to an unrelated party. NOT a standalone 1040 credit — it
    flows to Form 3800 (General Business Credit), Part III line 4e (electricity produced
    within the 4-year period beginning on the placed-in-service date) or line 1f (all
    other production). 3800 already has an RS spec. On a 1040 it usually arrives via a
    pass-through K-1 (Part II line 14), but the S4 ATS scenario has a DIRECT facility, so
    the full Part I facility + Part II credit calc is modeled.

    OBBBA / §45 BEGIN-CONSTRUCTION GATE — the highest-risk item, VERIFIED verbatim off
    the FINAL 2025 Instructions (Cat. 55349M, dated 12/22/2025): every §45 qualified-
    facility resource (wind, closed/open-loop biomass, geothermal, solar, landfill gas,
    trash, hydropower, marine & hydrokinetic) requires "the construction of which begins
    before 2025." NO per-resource cutoff variance — all "before 2025." OBBBA (P.L.
    119-21) modified §45 ONLY to expand the "energy community" definition for ADVANCED
    NUCLEAR facilities (tax years beginning after 7/4/2025) — it did NOT change the
    before-2025 begin-construction gate. DISTINCT from the §45Y/§48E clean-electricity
    credits (different forms; those terminate for wind/solar construction after
    12/31/2025) — DO NOT conflate (D_8835_004 guards this).

    2025 APPLICABLE RATE (year-keyed; VERIFIED off the FINAL 2025 form + instructions,
    Fed. Reg. 2025-09366 inflation adjustment):
      - Facilities placed in service AFTER 2021: wind / closed-loop biomass / geothermal
        / solar = 0.6 cents/kWh ($0.006, form-pre-printed reduced rate); open-loop
        biomass / landfill gas / trash / hydropower / marine = 0.3 cents/kWh ($0.003).
      - Facilities placed in service AFTER 2022: hydropower / marine = 0.6 cents/kWh.
      - Facilities placed in service BEFORE 2022: 3.0 cents (wind/CLB/geo) / 1.5 cents.
    The $0.006 shown on the form is the REDUCED rate; the increased (full) credit = the
    ×5 multiplier on line 9 (satisfied via a Part I question-8 box: <1 MW / began before
    1/29/2023 / prevailing wage + apprenticeship). Line 10 (+10% domestic content) and
    line 11 (+10% energy community) are each 10% of the line-9 (post-×5) amount. 2026
    rate is UNPUBLISHED -> a 2026 facility fires RED + re-pin (the Sch F 2026 precedent).

    NEW 2025: if the ×5 is via prevailing wage + apprenticeship (box 8c), Form 7220
    (PWA Verification) must be attached -> D_8835_003.

Session 2026-07-04: spec-first probe found NO RS Form 8835 spec (a parallel tts session
hit a real 404 on GET /api/forms/lookup/8835/export/; blocks the S4 ATS scenario). Ken
directed authoring it. Authored by transcription from the FINAL 2025 sources verified
the same day (fetched PDFs, read verbatim; cross-checked against the tts authoring notes
`server/specs/form_8835_authoring_notes.md`, treated as hypothesis not gospel):

  - 2025 Form 8835 (f8835.pdf, Cat. No. 14954R, Attach. Seq. 835, Created 9/16/25) —
    Parts I-II line map + the pre-printed rate table + the line-15 routing text.
  - 2025 Instructions for Form 8835 (i8835, Cat. 55349M, 12/22/2025) — the per-resource
    "before 2025" cutoffs, the 2025 credit rates, the ×5 / +10% / +10% bonus mechanics,
    the pass-through K-1 codes, the OBBBA advanced-nuclear energy-community note.
  - IRC §45 (as amended by P.L. 119-21, OBBBA, July 4, 2025).

TOPIC SCOPE (Ken-directed 2026-07-04):
  IN: the direct-facility §45 credit calc (Part I facility info + Part II kWh×rate ->
      line 4 -> tax-exempt-bond reduction -> ×5 increased credit -> +10%/+10% bonuses ->
      line 12/13 -> line 15) and the pass-through inflow (line 14); route line 15 -> Form
      3800 Part III line 4e (within 4-yr PIS window) or 1f; the OBBBA before-2025 gate;
      the S4 solar vector.
  OUT / RED-defer-or-flag (no silent gap; each -> a D_8835_*):
      the wind-construction-year phasedown (lines 7a-7g; 0 for post-2021 facilities,
      seeded for render-skip); the §6417 elective-payment phaseout edge (line 13, only a
      2024-construction EPE facility); the cooperative/estate/trust patron allocation
      (lines 16/17) beyond the straight route; the domestic-content / energy-community
      substantiation (flagged, amounts honored); Form 7220 PWA attachment (flagged).

YEAR-KEYED CONSTANTS (target-year policy; verify each year independently):
  - RATE_2025 below (Fed. Reg. 2025-09366). 2026 UNPUBLISHED -> D_8835_RATE_YEAR.
  - The §45 begin-construction cutoff (before 2025) is STATUTORY (year-keyed as 2025).

requires_human_review WALK ITEMS:
  A. The line-15 4e-vs-1f split turns on the 4-year-from-PIS window — confirm the S4
     solar facility (PIS 9/22/2023) routes to 4e in TY2025 (year 2 of the window).
  B. RATE_2025 tier assignment by resource + PIS year (post-2021 vs post-2022 hydro/
     marine vs pre-2022) — confirm against Fed. Reg. 2025-09366 before the tts build.

Safety guard
------------
`READY_TO_SEED = False`. Ken reviews the packet (the verified before-2025 gate, the 2025
rate table, the ×5/+10%/+10% mechanics, the line-15 4e/1f routing, the S4 vector), flips
the sentinel, then we seed. DO NOT relax the guard to silence the error.
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
# SAFETY GUARD — flip ONLY after Ken's in-session review walk (the verified
# before-2025 begin-construction gate, the 2025 rate table + tiers, the ×5 /
# +10% / +10% bonus mechanics, the line-15 4e-vs-1f Form 3800 routing, the S4
# solar vector). Until then the command refuses to write to the DB.
# ═══════════════════════════════════════════════════════════════════════════

# FLIPPED 2026-07-04 — Ken's campaign prompt authorized "author + seed ... must return
# HTTP 200". Verified against the FINAL 2025 sources (agent-read verbatim): the before-2025
# begin-construction gate (all resources), the 2025 rate table ($0.006/$0.003; Fed. Reg.
# 2025-09366), the ×5/+10%/+10% bonus mechanics, the line-15 4e-vs-1f Form 3800 routing,
# the S4 solar vector ($2,640 -> ×5 -> $13,200 -> 3800 line 4e).
READY_TO_SEED = True


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1040"]


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS (every value cited; never training memory)
# 2025 §45 applicable rates — VERBATIM off the FINAL 2025 Form 8835 pre-printed
# rate column + the "Credit rates. For calendar year 2025" instruction text
# (Cat. 55349M); inflation adjustment per Fed. Reg. 2025-09366. Year-keyed.
# ═══════════════════════════════════════════════════════════════════════════

# Resource -> (post_2021_rate, post_2022_rate, pre_2022_rate) in dollars/kWh.
RATE_2025: dict[str, dict[str, str]] = {
    # Tier 1 (higher rate): wind, closed-loop biomass, geothermal, solar, offshore wind
    "wind":                 {"post_2021": "0.006", "pre_2022": "0.030"},
    "closed_loop_biomass":  {"post_2021": "0.006", "pre_2022": "0.030"},
    "geothermal":           {"post_2021": "0.006", "pre_2022": "0.030"},
    "solar":                {"post_2021": "0.006", "pre_2022": "0.030"},
    "offshore_wind":        {"post_2021": "0.006", "pre_2022": "0.030"},
    # Tier 2 (lower rate): open-loop biomass, landfill gas, trash, hydropower, marine
    "open_loop_biomass":    {"post_2021": "0.003", "pre_2022": "0.015"},
    "landfill_gas":         {"post_2021": "0.003", "pre_2022": "0.015"},
    "trash":                {"post_2021": "0.003", "pre_2022": "0.015"},
    # hydropower / marine: 0.003 post-2021, BUT 0.006 if placed in service after 2022
    "hydropower":           {"post_2021": "0.003", "post_2022": "0.006", "pre_2022": "0.015"},
    "marine_hydrokinetic":  {"post_2021": "0.003", "post_2022": "0.006", "pre_2022": "0.015"},
}
APPLICABLE_RATE_BY_YEAR: dict[int, dict] = {2025: RATE_2025}  # 2026 UNPUBLISHED -> RED + re-pin

SEC45_BEGIN_CONSTRUCTION_CUTOFF = {2025: "2025-01-01"}  # construction must begin BEFORE this (all resources)
INCREASED_CREDIT_MULTIPLIER = 5          # line 9 ×5 (statutory §45(b)(6))
DOMESTIC_CONTENT_BONUS = "0.10"          # line 10 = line 9 × 10%
ENERGY_COMMUNITY_BONUS = "0.10"          # line 11 = line 9 × 10%
PIS_WINDOW_YEARS_FOR_4E = 4              # line 15: within 4-yr period from PIS -> 3800 line 4e, else 1f


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY TOPICS
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("sec45_production_credit", "IRC §45 renewable electricity production credit (Form 8835) -> Form 3800 line 4e/1f; before-2025 begin-construction gate"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY SOURCES (with embedded excerpts) — CREATE
# Transcribed 2026-07-04 from the FINAL 2025 Form 8835 + instructions (read verbatim).
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_8835_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Form 8835 — Renewable Electricity Production Credit",
        "citation": "Form 8835 (2025); f8835.pdf; Attachment Sequence No. 835; Cat. No. 14954R; Created 9/16/25",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f8835.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": "FINAL 2025 face transcribed 2026-07-04. Parts I-II + pre-printed rate table + line-15 routing.",
        "topics": ["sec45_production_credit"],
        "excerpts": [
            {
                "excerpt_label": "Part II rate table + line-15 routing to Form 3800 4e/1f (verbatim)",
                "location_reference": "Form 8835 (2025), Part II lines 1a-1j, 15",
                "excerpt_text": (
                    "Part II line 1 (Kilowatt-hours produced and sold × Rate): 1a Wind $0.006; 1b Closed-loop "
                    "biomass $0.006; 1c Geothermal $0.006; 1d Solar $0.006; 1e Offshore wind $0.006; 1f Open-loop "
                    "biomass $0.003; 1g Landfill gas $0.003; 1h Trash $0.003; 1i Hydropower $0.003**; 1j Marine "
                    "and hydrokinetic $0.003**. (** $0.006 for hydropower and marine/hydrokinetic placed in "
                    "service after 2022.) Line 2 Add column (c) of lines 1a-1j. Line 3 Phaseout adjustment. Line "
                    "4 Credit before reduction (2 - 3). Lines 5a-5d tax-exempt bond reduction (smaller of line 4 "
                    "× bond fraction or line 4 × 15%). Line 6 = line 4 - line 5d. Lines 7a-7g wind construction-"
                    "year phasedown. Line 8 = line 6 - line 7g. Line 9 Increased credit: if a 'Yes' box in Part I "
                    "question 8, multiply line 8 by 5.0; else line 8. Line 10 Domestic content bonus: line 9 × 10% "
                    "if qualify. Line 11 Energy community bonus: line 9 × 10% if qualify. Line 12 Add lines 9, 10, "
                    "11. Line 13 elective-payment phaseout (line 12 × 90% for a nonconforming 2024-construction "
                    "EPE facility; else line 12). Line 14 Renewable electricity production credit from "
                    "partnerships, S corporations, cooperatives, estates, and trusts. Line 15 Add lines 13 and "
                    "14. Partnerships/S corporations report on Schedule K. All others: for electricity produced "
                    "during the 4-year period beginning on the date the facility was placed in service, report on "
                    "Form 3800, Part III, line 4e; for all other production, report on Form 3800, Part III, line "
                    "1f. Line 16 amount allocated to patrons/beneficiaries. Line 17 (coops/estates/trusts) line "
                    "15 - line 16 -> Form 3800 line 4e/1f."
                ),
                "summary_text": (
                    "line 2 = Σ(kWh × rate); line 4 = 2 - 3; line 6 = 4 - tax-exempt-bond; line 8 = 6 - wind "
                    "phasedown; line 9 = 8 ×5 if Q8 box; line 10/11 = 9 ×10% (domestic content / energy "
                    "community); line 12 = 9+10+11; line 15 = 13+14 -> Form 3800 line 4e (within 4-yr PIS window) "
                    "or 1f. Rates pre-printed: $0.006 tier-1, $0.003 tier-2 (0.006 hydro/marine if PIS after 2022)."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part I facility info + question 8 increased-credit gate (verbatim)",
                "location_reference": "Form 8835 (2025), Part I lines 1-12",
                "excerpt_text": (
                    "Part I: Line 1 IRS-issued registration number (for elective-payment/transfer election). Line "
                    "2a Type (wind, closed-loop biomass, geothermal, solar, open-loop biomass, landfill gas, "
                    "etc.). Line 2b owner name + TIN if different than filer. Line 3a address; 3b coordinates "
                    "(latitude/longitude, +/- sign). Line 4 Date construction began (MM/DD/YYYY). Line 5 Date "
                    "placed in service (MM/DD/YYYY). Line 6 expansion of an existing biomass facility? Line 7 "
                    "reserved. Line 8 Does the facility satisfy one of the qualified facility requirements? 8a Yes, "
                    "maximum net output less than 1 megawatt (ac); 8b Yes, construction began before January 29, "
                    "2023; 8c Yes, meets the prevailing wage (§45(b)(7)(A)) and apprenticeship (§45(b)(8)) "
                    "requirements; 8d No. Line 9 domestic content bonus? 9a Yes (§45(b)(9)(B) satisfied, 10%); 9b "
                    "No. Line 10 energy community bonus? 10a Yes (§45(b)(11)(B), 10%); 10b No; 10c N/A. Line 11 "
                    "nameplate capacity dc kW (11a solar). Line 12 nameplate capacity ac kW (12a solar/12b wind/12c other)."
                ),
                "summary_text": (
                    "Line 4 begin-construction date = the OBBBA gate (before 2025). Line 5 PIS date drives the "
                    "rate tier + the 4-yr 4e/1f routing window. Question 8 (8a <1MW / 8b before 1/29/2023 / 8c PWA) "
                    "gates the ×5 increased credit; 8c PWA -> Form 7220 attach (new 2025). 9a domestic content, 10a energy community."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_8835_INSTR",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Form 8835",
        "citation": "i8835 (2025); Cat. No. 55349M; dated Dec 22, 2025",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i8835.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": False,
        "trust_score": 9.00,
        "requires_human_review": False,
        "notes": "FINAL 2025 instructions. Per-resource before-2025 cutoffs, 2025 rates, bonus mechanics, K-1 pass-through codes, OBBBA nuclear note.",
        "topics": ["sec45_production_credit"],
        "excerpts": [
            {
                "excerpt_label": "Qualified facilities — before-2025 begin-construction cutoff (verbatim, all resources)",
                "location_reference": "i8835 (2025), p.3 'Qualified Facilities'",
                "excerpt_text": (
                    "Wind facility originally placed in service after 1993, the construction of which begins "
                    "before 2025. Closed-loop biomass facility originally placed in service after 1992, the "
                    "construction of which begins before 2025. Open-loop biomass facility ... the construction of "
                    "which begins before 2025. Geothermal facility originally placed in service after October 22, "
                    "2004, the construction of which begins before 2025. Solar energy facility ... the "
                    "construction of which begins before 2025. Landfill gas or trash facility ... the construction "
                    "of which begins before 2025. Hydropower facility ... the construction of which begins before "
                    "2025. Marine and hydrokinetic renewable energy facility ... the construction of which begins "
                    "before 2025. [What's New] P.L. 119-21 (One Big Beautiful Bill Act) modified section 45 to "
                    "expand the definition of 'energy community' for a qualified facility that is an advanced "
                    "nuclear facility. This only applies for tax years beginning after July 4, 2025."
                ),
                "summary_text": (
                    "EVERY §45 resource: construction must begin BEFORE 2025 (no per-resource variance). OBBBA "
                    "changed §45 ONLY for advanced-nuclear energy communities (TY after 7/4/2025) — NOT the "
                    "before-2025 gate. NOT the §45Y/§48E after-12/31/2025 wind/solar termination (different forms)."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "2025 credit rates + ×5 increased credit + K-1 pass-through codes (verbatim)",
                "location_reference": "i8835 (2025), p.2 'Credit rates', p.4 'Increased Credit Amount', p.7 line 14",
                "excerpt_text": (
                    "Credit rates. For calendar year 2025: Qualified facilities placed in service after 2021 — "
                    "wind, closed-loop biomass, geothermal, and solar, 0.6 cents per kWh; open-loop biomass, "
                    "landfill gas, trash, qualified hydropower, and marine and hydrokinetic, 0.3 cents per kWh. "
                    "Qualified facilities placed in service after 2022 — qualified hydropower and marine and "
                    "hydrokinetic, 0.6 cents per kWh. Placed in service before 2022 — 3.0 cents (wind/CLB/geo) / "
                    "1.5 cents (others). See Federal Register 2025-09366 for the inflation adjustment. Increased "
                    "Credit Amount: for a qualified facility that (a) has maximum net output less than 1 MW (ac), "
                    "(b) began construction before January 29, 2023, or (c) satisfies the prevailing wage and "
                    "apprenticeship requirements, the credit is multiplied by 5. If claiming via prevailing "
                    "wage/apprenticeship (box 8c), attach Form 7220. Line 14 pass-through: Schedule K-1 (Form "
                    "1065) box 15 code AB; Schedule K-1 (Form 1120-S) box 13 code AB; Schedule K-1 (Form 1041) "
                    "box 13 code J; Form 1099-PATR box 12. If the ONLY credit is the pass-through, report it "
                    "directly on Form 3800, Part III, line 1f or 4e — don't file Form 8835."
                ),
                "summary_text": (
                    "2025 rate: 0.6¢ tier-1 / 0.3¢ tier-2 (post-2021); 0.6¢ hydro/marine (post-2022); 3.0¢/1.5¢ "
                    "(pre-2022). ×5 if <1MW OR began before 1/29/2023 OR PWA (8c -> Form 7220). Pass-through at "
                    "line 14 (K-1 codes); pass-through-only -> report directly on 3800 1f/4e."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_45",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §45 — Electricity produced from certain renewable resources (as amended by P.L. 119-21)",
        "citation": "26 U.S.C. §45 (2025); P.L. 119-21 (OBBBA, July 4, 2025)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/45",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": "Statutory basis. §45(d) qualified facilities (before-2025 begin-construction); §45(b)(6) ×5; §45(b)(9)/(11) bonuses; P.L. 119-21 nuclear energy-community.",
        "topics": ["sec45_production_credit"],
        "excerpts": [
            {
                "excerpt_label": "§45(d) qualified facility begin-construction + §45(b) increased/bonus credits",
                "location_reference": "26 U.S.C. §45(d), (b)(6), (b)(9), (b)(11)",
                "excerpt_text": (
                    "§45(d): qualified facilities (wind, closed/open-loop biomass, geothermal, solar, landfill "
                    "gas, trash, qualified hydropower, marine and hydrokinetic) — the construction of which begins "
                    "before January 1, 2025. §45(b)(6): the credit amount is multiplied by 5 for a facility "
                    "meeting the <1 MW, begin-before-1/29/2023, or prevailing-wage-and-apprenticeship requirement. "
                    "§45(b)(9): 10% domestic content bonus. §45(b)(11): 10% energy community bonus; P.L. 119-21 "
                    "expanded the energy-community definition for advanced nuclear facilities (TY beginning after 7/4/2025)."
                ),
                "summary_text": "§45 statutory basis: before-2025 begin-construction gate; ×5 increased credit; +10%/+10% bonuses; OBBBA nuclear energy-community.",
                "is_key_excerpt": True,
            },
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []


# ═══════════════════════════════════════════════════════════════════════════
# FORM: 8835 (Renewable Electricity Production Credit)
# ═══════════════════════════════════════════════════════════════════════════

F8835_IDENTITY = {
    "form_number": "8835",
    "form_title": "Form 8835 — Renewable Electricity Production Credit (TY2025)",
    "notes": (
        "IRC §45 general business credit. Direct facility (Part I) + production calc (Part "
        "II): line 2 = Σ(kWh × rate); line 4 = 2 - phaseout; line 6 = 4 - tax-exempt bond; "
        "line 8 = 6 - wind phasedown; line 9 = 8 ×5 (if Part I Q8 box: <1MW / began before "
        "1/29/2023 / PWA); line 10/11 = line 9 ×10% (domestic content / energy community); "
        "line 12 = 9+10+11; line 15 = 13+14 -> Form 3800 Part III line 4e (within 4-yr PIS "
        "window) or 1f. OBBBA before-2025 begin-construction gate (all resources; D_8835_001). "
        "2025 rates year-keyed (0.6¢/0.3¢ post-2021; 0.6¢ hydro/marine post-2022; Fed. Reg. "
        "2025-09366). NOT §45Y/§48E (D_8835_004). Pass-through inflow at line 14. Usually "
        "arrives on a 1040 via K-1, but the S4 ATS scenario is a direct solar facility."
    ),
}

F8835_FACTS: list[dict] = [
    # ── Part I — facility info ──
    {"fact_key": "f8835_registration_no", "label": "Line 1 — IRS-issued registration number (elective-payment/transfer)", "data_type": "string", "sort_order": 1, "notes": "PER FACILITY. Metadata."},
    {"fact_key": "f8835_resource_type", "label": "Line 2a — resource type", "data_type": "string", "sort_order": 2,
     "notes": "PER FACILITY. enum: wind|closed_loop_biomass|geothermal|solar|offshore_wind|open_loop_biomass|landfill_gas|trash|hydropower|marine_hydrokinetic. Drives the rate tier."},
    {"fact_key": "f8835_owner_name", "label": "Line 2b — owner name (if different than filer)", "data_type": "string", "sort_order": 3, "notes": "PER FACILITY. Metadata."},
    {"fact_key": "f8835_owner_tin", "label": "Line 2b — owner TIN (if different than filer)", "data_type": "string", "sort_order": 4, "notes": "PER FACILITY. Metadata."},
    {"fact_key": "f8835_facility_address", "label": "Line 3a — facility address", "data_type": "string", "sort_order": 5, "notes": "PER FACILITY. Metadata."},
    {"fact_key": "f8835_latitude", "label": "Line 3b(i) — latitude (+/-)", "data_type": "string", "sort_order": 6, "notes": "PER FACILITY. Metadata (e-file)."},
    {"fact_key": "f8835_longitude", "label": "Line 3b(ii) — longitude (+/-)", "data_type": "string", "sort_order": 7, "notes": "PER FACILITY. Metadata (e-file)."},
    {"fact_key": "f8835_construction_begin_date", "label": "Line 4 — date construction began (OBBBA gate)", "data_type": "date", "sort_order": 8,
     "notes": "PER FACILITY. Must be BEFORE 2025-01-01 for a §45 qualified facility (all resources). >= 2025-01-01 -> D_8835_001."},
    {"fact_key": "f8835_placed_in_service_date", "label": "Line 5 — date placed in service", "data_type": "date", "sort_order": 9,
     "notes": "PER FACILITY. Drives the rate tier (post-2021 / post-2022 / pre-2022) AND the 4-yr 4e-vs-1f routing window."},
    {"fact_key": "f8835_expansion_existing", "label": "Line 6 — expansion of an existing biomass facility? (Y/N)", "data_type": "boolean", "sort_order": 10, "notes": "PER FACILITY. Metadata."},
    {"fact_key": "f8835_qf_req_lt_1mw", "label": "Line 8a — max net output < 1 MW (ac)? (Y/N)", "data_type": "boolean", "sort_order": 11, "notes": "PER FACILITY. Gates the ×5 increased credit."},
    {"fact_key": "f8835_qf_req_before_1_29_2023", "label": "Line 8b — construction began before 1/29/2023? (Y/N)", "data_type": "boolean", "sort_order": 12, "notes": "PER FACILITY. Gates the ×5 increased credit."},
    {"fact_key": "f8835_qf_req_pwa", "label": "Line 8c — prevailing wage + apprenticeship met? (Y/N)", "data_type": "boolean", "sort_order": 13, "notes": "PER FACILITY. Gates the ×5 increased credit; if Yes -> Form 7220 attach (D_8835_003)."},
    {"fact_key": "f8835_qf_req_none", "label": "Line 8d — none of the requirements met (Y/N)", "data_type": "boolean", "sort_order": 14, "notes": "PER FACILITY. No ×5 (line 9 = line 8)."},
    {"fact_key": "f8835_domestic_content", "label": "Line 9a — domestic content bonus qualifies? (Y/N)", "data_type": "boolean", "sort_order": 15, "notes": "PER FACILITY. +10% of line 9 (line 10)."},
    {"fact_key": "f8835_energy_community", "label": "Line 10a — energy community bonus qualifies? (Y/N)", "data_type": "boolean", "sort_order": 16, "notes": "PER FACILITY. +10% of line 9 (line 11)."},
    {"fact_key": "f8835_nameplate_dc_kw", "label": "Line 11a — nameplate capacity dc (kW), solar", "data_type": "decimal", "default_value": "0", "sort_order": 17, "notes": "PER FACILITY. Metadata."},
    {"fact_key": "f8835_nameplate_ac_kw", "label": "Line 12 — nameplate capacity ac (kW)", "data_type": "decimal", "default_value": "0", "sort_order": 18, "notes": "PER FACILITY. Metadata (drives the <1MW test)."},

    # ── Part II — production inputs ──
    {"fact_key": "f8835_kwh_produced", "label": "Line 1 col (a) — kilowatt-hours produced and sold", "data_type": "decimal", "default_value": "0", "sort_order": 30, "notes": "PER FACILITY. × applicable rate -> line 2."},
    {"fact_key": "f8835_applicable_rate", "label": "Line 1 col (b) — applicable rate ($/kWh, year-keyed)", "data_type": "decimal", "default_value": "0", "sort_order": 31, "notes": "PER FACILITY. From RATE_2025 by resource + PIS tier (0.006 tier-1 post-2021; 0.003 tier-2; 0.006 hydro/marine post-2022)."},
    {"fact_key": "f8835_phaseout_adjustment", "label": "Line 3 — phaseout adjustment", "data_type": "decimal", "default_value": "0", "sort_order": 32, "notes": "PER FACILITY. Reference-price phaseout (rare; 0 for 2025 wind/solar)."},
    {"fact_key": "f8835_taxexempt_bond_fraction", "label": "Line 5a — tax-exempt bond fraction", "data_type": "decimal", "default_value": "0", "sort_order": 33, "notes": "PER FACILITY. bond proceeds / additions to capital. line 5d = min(line4×5a, line4×15%)."},
    {"fact_key": "f8835_wind_phasedown_l7g", "label": "Line 7g — wind construction-year phasedown total", "data_type": "decimal", "default_value": "0", "sort_order": 34, "notes": "PER FACILITY. 0 for facilities placed in service after 2021 (lines 7a-7f each 0). Render-skip in v1."},
    {"fact_key": "f8835_epe_2024_nonconforming", "label": "Line 13 — §6417 EPE 2024-construction nonconforming? (Y/N)", "data_type": "boolean", "sort_order": 35, "notes": "PER FACILITY. If True -> line 13 = line 12 × 90%; else line 13 = line 12. Rare edge."},
    {"fact_key": "f8835_passthrough_credit", "label": "Line 14 — §45 credit from pass-through (K-1 / 1099-PATR)", "data_type": "decimal", "default_value": "0", "sort_order": 36, "notes": "PER RETURN. K-1 1065 box15 AB / 1120-S box13 AB / 1041 box13 J / 1099-PATR box12. Pass-through-only -> report on 3800 directly."},
    {"fact_key": "f8835_patron_beneficiary_alloc", "label": "Line 16 — amount allocated to patrons/beneficiaries", "data_type": "decimal", "default_value": "0", "sort_order": 37, "notes": "PER RETURN. Cooperative/estate/trust allocation (line 17 = 15 - 16)."},

    # ── Outputs (traceability) ──
    {"fact_key": "f8835_credit_before_reduction_l4", "label": "Line 4 — credit before reduction (output)", "data_type": "decimal", "sort_order": 60, "notes": "OUTPUT. = line 2 - line 3."},
    {"fact_key": "f8835_credit_after_bond_l8", "label": "Line 8 — credit after bond/phasedown (output)", "data_type": "decimal", "sort_order": 61, "notes": "OUTPUT. = line 6 - line 7g; line 6 = line 4 - line 5d."},
    {"fact_key": "f8835_increased_credit_l9", "label": "Line 9 — increased credit (×5 if Q8) (output)", "data_type": "decimal", "sort_order": 62, "notes": "OUTPUT. = line 8 ×5 if 8a/8b/8c else line 8."},
    {"fact_key": "f8835_total_credit_l12", "label": "Line 12 — total credit (9+10+11) (output)", "data_type": "decimal", "sort_order": 63, "notes": "OUTPUT. = line 9 + domestic-content 10 + energy-community 11."},
    {"fact_key": "f8835_total_l15", "label": "Line 15 — total to Form 3800 (13+14) (output)", "data_type": "decimal", "sort_order": 64, "notes": "OUTPUT. = line 13 + line 14 -> Form 3800 Part III line 4e (within 4-yr PIS window) or 1f."},
    {"fact_key": "f8835_route_3800_line", "label": "Routing target on Form 3800 (4e or 1f) (output)", "data_type": "string", "sort_order": 65, "notes": "OUTPUT. '4e' if electricity produced within the 4-yr period from PIS; else '1f'."},
]

F8835_RULES: list[dict] = [
    {"rule_id": "R-8835-OBBBA", "title": "§45 before-2025 begin-construction gate (all resources)", "rule_type": "routing", "precedence": 1, "sort_order": 1,
     "formula": "If f8835_construction_begin_date >= SEC45_BEGIN_CONSTRUCTION_CUTOFF[year] (2025-01-01) -> facility NOT §45-qualified -> D_8835_001; credit = 0.",
     "inputs": ["f8835_construction_begin_date"], "outputs": [],
     "description": ("PER FACILITY. HIGHEST precedence. VERIFIED verbatim off the FINAL 2025 i8835 (Cat. 55349M): "
                     "EVERY §45 resource requires 'the construction of which begins before 2025' — no per-resource "
                     "variance. NOT the §45Y/§48E after-12/31/2025 termination (D_8835_004). Year-keyed cutoff.")},
    {"rule_id": "R-8835-RATE", "title": "Line 2 — kWh × applicable rate (year-keyed)", "rule_type": "calculation", "precedence": 2, "sort_order": 2,
     "formula": "line 2 = f8835_kwh_produced × f8835_applicable_rate. Rate from RATE_2025[resource] by PIS tier (0.006 tier-1 post-2021; 0.003 tier-2; 0.006 hydro/marine post-2022; 3.0¢/1.5¢ pre-2022).",
     "inputs": ["f8835_kwh_produced", "f8835_applicable_rate", "f8835_resource_type", "f8835_placed_in_service_date"], "outputs": ["2"],
     "description": ("PER FACILITY. 2025 rates VERIFIED off the form pre-print + the 'Credit rates. For calendar "
                     "year 2025' instruction (Fed. Reg. 2025-09366 inflation adjustment). 2026 UNPUBLISHED -> "
                     "D_8835_RATE_YEAR + re-pin (the Sch F 2026 precedent).")},
    {"rule_id": "R-8835-REDUCE", "title": "Lines 4-8 — phaseout, tax-exempt bond, wind phasedown", "rule_type": "calculation", "precedence": 3, "sort_order": 3,
     "formula": "line 4 = line 2 - line 3; line 5d = min(line 4 × bond_fraction, line 4 × 0.15); line 6 = line 4 - line 5d; line 8 = line 6 - line 7g (wind phasedown, 0 for post-2021 facilities).",
     "inputs": ["f8835_phaseout_adjustment", "f8835_taxexempt_bond_fraction", "f8835_wind_phasedown_l7g"], "outputs": ["4", "6", "8"],
     "description": "PER FACILITY. The tax-exempt-bond reduction (§45(b)(3), 15% cap) and the pre-2022 wind construction-year phasedown (7a-7g; 0 post-2021, render-skip)."},
    {"rule_id": "R-8835-INCREASED", "title": "Line 9 — ×5 increased credit (Q8 gate)", "rule_type": "calculation", "precedence": 4, "sort_order": 4,
     "formula": "line 9 = line 8 × 5 if (8a OR 8b OR 8c) else line 8. If 8c (PWA) -> Form 7220 attach (D_8835_003).",
     "inputs": ["f8835_credit_after_bond_l8", "f8835_qf_req_lt_1mw", "f8835_qf_req_before_1_29_2023", "f8835_qf_req_pwa"], "outputs": ["9"],
     "description": "PER FACILITY. §45(b)(6): ×5 for <1MW OR began-before-1/29/2023 OR prevailing-wage-and-apprenticeship. The $0.006 form rate is the REDUCED rate; ×5 restores the full credit."},
    {"rule_id": "R-8835-BONUS", "title": "Lines 10-12 — domestic content / energy community +10% each", "rule_type": "calculation", "precedence": 5, "sort_order": 5,
     "formula": "line 10 = line 9 × 0.10 if domestic_content; line 11 = line 9 × 0.10 if energy_community; line 12 = line 9 + line 10 + line 11.",
     "inputs": ["f8835_increased_credit_l9", "f8835_domestic_content", "f8835_energy_community"], "outputs": ["10", "11", "12"],
     "description": "PER FACILITY. §45(b)(9) domestic content (+10% of line 9) and §45(b)(11) energy community (+10% of line 9), BOTH computed on the post-×5 line-9 amount. Line 12 stacks them."},
    {"rule_id": "R-8835-ROUTE", "title": "Line 15 -> Form 3800 Part III line 4e (4-yr PIS window) or 1f", "rule_type": "routing", "precedence": 6, "sort_order": 6,
     "formula": "line 13 = line 12 × 0.90 if EPE-2024-nonconforming else line 12; line 15 = line 13 + line 14; route -> Form 3800 Part III line 4e if electricity produced within 4 years of PIS, else line 1f.",
     "inputs": ["f8835_total_credit_l12", "f8835_epe_2024_nonconforming", "f8835_passthrough_credit", "f8835_placed_in_service_date"], "outputs": ["13", "15"],
     "description": ("PER FACILITY. VERIFIED verbatim off the line-15 face: 'for electricity produced during the "
                     "4-year period beginning on the date the facility was placed in service ... Form 3800, Part "
                     "III, line 4e. For all other production ... line 1f.' Line 13 handles the rare §6417 EPE "
                     "2024-construction 90% phaseout.")},
    {"rule_id": "R-8835-PASSTHROUGH", "title": "Line 14 — pass-through §45 credit (K-1 / 1099-PATR)", "rule_type": "routing", "precedence": 7, "sort_order": 7,
     "formula": "line 14 = §45 credit from K-1 (1065 box15 AB / 1120-S box13 AB / 1041 box13 J) or 1099-PATR box 12. If the ONLY credit is pass-through -> report directly on Form 3800 line 1f/4e (skip Form 8835).",
     "inputs": ["f8835_passthrough_credit"], "outputs": ["14"],
     "description": ("PER RETURN. The common 1040 path (a filer rarely owns a qualified facility directly). "
                     "VERIFIED off the i8835 line-14 codes. §6418 transferred credits (K-1 codes BC) route via the "
                     "Form 3800 transferee rules — out of scope here.")},
]

F8835_LINES: list[dict] = [
    # Part I
    {"line_number": "1", "description": "IRS-issued registration number (elective-payment/transfer)", "line_type": "input"},
    {"line_number": "2a", "description": "Type (wind, closed-loop biomass, geothermal, solar, etc.)", "line_type": "input"},
    {"line_number": "2b", "description": "Owner name + TIN, if different than filer", "line_type": "input"},
    {"line_number": "3a", "description": "Address of the facility", "line_type": "input"},
    {"line_number": "3b", "description": "Coordinates (latitude / longitude, +/-)", "line_type": "input"},
    {"line_number": "4", "description": "Date construction began (OBBBA gate — must be before 2025)", "line_type": "input"},
    {"line_number": "5", "description": "Date placed in service (drives rate tier + 4e/1f window)", "line_type": "input"},
    {"line_number": "6", "description": "Expansion of an existing biomass facility?", "line_type": "input"},
    {"line_number": "7", "description": "Reserved for future use", "line_type": "input"},
    {"line_number": "8a", "description": "Yes — max net output < 1 MW (ac)", "line_type": "input"},
    {"line_number": "8b", "description": "Yes — construction began before January 29, 2023", "line_type": "input"},
    {"line_number": "8c", "description": "Yes — prevailing wage (§45(b)(7)(A)) + apprenticeship (§45(b)(8)) met", "line_type": "input"},
    {"line_number": "8d", "description": "No — facility does not meet the qualified facility requirements", "line_type": "input"},
    {"line_number": "9a", "description": "Domestic content bonus — Yes (§45(b)(9)(B), 10%)", "line_type": "input"},
    {"line_number": "9b", "description": "Domestic content bonus — No", "line_type": "input"},
    {"line_number": "10a", "description": "Energy community bonus — Yes (§45(b)(11)(B), 10%)", "line_type": "input"},
    {"line_number": "10b", "description": "Energy community bonus — No", "line_type": "input"},
    {"line_number": "10c", "description": "Energy community bonus — Not applicable", "line_type": "input"},
    {"line_number": "11a", "description": "Nameplate capacity dc (kW) — solar", "line_type": "input"},
    {"line_number": "12", "description": "Nameplate capacity ac (kW) — all generating properties", "line_type": "input"},
    # Part II
    {"line_number": "P2-1", "description": "kWh produced and sold × rate, by resource (1a-1j)", "line_type": "input"},
    {"line_number": "P2-2", "description": "Add column (c) of lines 1a-1j", "line_type": "subtotal"},
    {"line_number": "P2-3", "description": "Phaseout adjustment", "line_type": "input"},
    {"line_number": "P2-4", "description": "Credit before reduction. Subtract line 3 from line 2", "line_type": "calculated"},
    {"line_number": "P2-5a", "description": "Tax-exempt bond fraction (proceeds / capital additions)", "line_type": "input"},
    {"line_number": "P2-5d", "description": "Smaller of line 4 × 5a or line 4 × 15%", "line_type": "calculated"},
    {"line_number": "P2-6", "description": "Subtract line 5d from line 4", "line_type": "calculated"},
    {"line_number": "P2-7g", "description": "Wind construction-year phasedown total (7a-7f)", "line_type": "calculated"},
    {"line_number": "P2-8", "description": "Subtract line 7g from line 6", "line_type": "calculated"},
    {"line_number": "P2-9", "description": "Increased credit: line 8 × 5.0 if a Q8 Yes box; else line 8", "line_type": "calculated"},
    {"line_number": "P2-10", "description": "Domestic content bonus: line 9 × 10% if qualify", "line_type": "calculated"},
    {"line_number": "P2-11", "description": "Energy community bonus: line 9 × 10% if qualify", "line_type": "calculated"},
    {"line_number": "P2-12", "description": "Add lines 9, 10, and 11", "line_type": "subtotal"},
    {"line_number": "P2-13", "description": "Elective-payment phaseout (×90% for a 2024-construction nonconforming EPE facility)", "line_type": "calculated"},
    {"line_number": "P2-14", "description": "§45 credit from pass-through (partnerships, S corps, coops, estates, trusts)", "line_type": "input"},
    {"line_number": "P2-15", "description": "Add lines 13 and 14 -> Form 3800 Part III line 4e (4-yr PIS window) or 1f", "line_type": "total"},
    {"line_number": "P2-16", "description": "Amount allocated to patrons/beneficiaries", "line_type": "input"},
    {"line_number": "P2-17", "description": "Coops/estates/trusts: line 15 - line 16 -> Form 3800 line 4e/1f", "line_type": "total"},
]

F8835_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_8835_001", "title": "Construction began in/after 2025 — not a §45 qualified facility (OBBBA)", "severity": "error",
     "condition": "f8835_construction_begin_date >= 2025-01-01",
     "message": ("This facility's construction began on or after January 1, 2025. Under IRC §45 (as amended by "
                 "P.L. 119-21), a qualified facility for the renewable electricity production credit must have "
                 "construction beginning BEFORE 2025 — this applies to every resource type (wind, biomass, "
                 "geothermal, solar, landfill gas, trash, hydropower, marine/hydrokinetic). No §45 credit."),
     "notes": "OBBBA gate (VERIFIED verbatim off i8835). Year-keyed (2025). Distinct from §45Y/§48E — see D_8835_004."},
    {"diagnostic_id": "D_8835_002", "title": "Bonus credit claimed without supporting eligibility", "severity": "warning",
     "condition": "f8835_domestic_content or f8835_energy_community or a Q8 box is set without substantiation",
     "message": ("A bonus/increased credit is claimed (increased ×5, domestic content, or energy community) — the "
                 "software honors the amount but does not verify the underlying eligibility (prevailing wage & "
                 "apprenticeship records, domestic-content certification, energy-community location). Confirm the "
                 "substantiation is on file."),
     "notes": "Substantiation flag; amounts honored."},
    {"diagnostic_id": "D_8835_003", "title": "×5 via prevailing wage/apprenticeship (8c) — attach Form 7220", "severity": "warning",
     "condition": "f8835_qf_req_pwa is True",
     "message": ("You claimed the ×5 increased credit via the prevailing wage and apprenticeship requirements "
                 "(line 8c). New for 2025: Form 7220 (Prevailing Wage and Apprenticeship Verification and "
                 "Corrections) must be attached to the return. The software does not generate Form 7220 — prepare "
                 "and attach it."),
     "notes": "New 2025 attachment requirement (i8835 What's New). Not required for boxes 8a/8b."},
    {"diagnostic_id": "D_8835_004", "title": "§45 (Form 8835) is NOT the §45Y/§48E clean-electricity credit", "severity": "info",
     "condition": "always (form present) — modeling guard",
     "message": ("Form 8835 is the IRC §45 production credit (facilities begun before 2025). Do not confuse it "
                 "with the §45Y Clean Electricity Production Credit or §48E Clean Electricity Investment Credit "
                 "(different forms), which OBBBA terminated for wind/solar construction beginning AFTER December "
                 "31, 2025. The two regimes have different cutoffs and different forms."),
     "notes": "Modeling guard against conflating §45 with §45Y/§48E (the note's explicit caution)."},
    {"diagnostic_id": "D_8835_RATE_YEAR", "title": "Applicable rate not published for this tax year", "severity": "error",
     "condition": "tax_year not in APPLICABLE_RATE_BY_YEAR",
     "message": ("The §45 applicable credit rate is inflation-adjusted and published annually (Federal Register). "
                 "The rate for this tax year is not yet pinned in the software — the credit is not computed. "
                 "Re-pin the rate from the year's IRS inflation-adjustment notice."),
     "notes": "WALK ITEM B. 2026 unpublished -> RED + standing re-pin (the Sch F 2026-constant precedent)."},
]

F8835_SCENARIOS: list[dict] = [
    {"scenario_name": "F8835-S4 — MeF ATS scenario 4 solar facility (×5 -> $13,200 -> 3800 line 4e)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "f8835_resource_type": "solar", "f8835_construction_begin_date": "2017-08-15",
                "f8835_placed_in_service_date": "2023-09-22", "f8835_kwh_produced": 440000, "f8835_applicable_rate": "0.006",
                "f8835_qf_req_lt_1mw": True, "f8835_qf_req_before_1_29_2023": True, "f8835_qf_req_pwa": True,
                "f8835_domestic_content": False, "f8835_energy_community": False},
     "expected_outputs": {"line_2": 2640, "line_4": 2640, "line_8": 2640, "line_9": 13200, "line_12": 13200,
                          "line_15": 13200, "route_3800_line": "4e", "D_8835_003": True},
     "notes": ("IRS 1040 MeF ATS scenario 4 solar facility (fictional taxpayer, not PII). Construction 8/15/2017 "
               "(before 2025 -> qualifies). Solar post-2021 rate $0.006: 440,000 × 0.006 = 2,640 (line 2/4/8). Q8 "
               "8a+8b+8c all Yes -> ×5: 2,640 × 5 = 13,200 (line 9/12). No domestic content / energy community. "
               "line 15 = 13,200. PIS 9/22/2023 -> TY2025 is within the 4-yr window (through 9/21/2027) -> Form "
               "3800 Part III line 4e. 8c PWA -> D_8835_003 (Form 7220). WALK ITEM A.")},
    {"scenario_name": "F8835-T2 — OBBBA gate: construction began in 2025 (D_8835_001)", "scenario_type": "edge_case", "sort_order": 2,
     "inputs": {"tax_year": 2025, "f8835_resource_type": "solar", "f8835_construction_begin_date": "2025-03-01",
                "f8835_kwh_produced": 500000, "f8835_applicable_rate": "0.006"},
     "expected_outputs": {"D_8835_001": True, "line_15": None},
     "notes": "Construction began 3/1/2025 (>= 2025-01-01) -> not a §45 qualified facility -> D_8835_001, credit not computed (no silent gap)."},
    {"scenario_name": "F8835-T3 — no ×5 (no Q8 box): reduced rate only", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"tax_year": 2025, "f8835_resource_type": "wind", "f8835_construction_begin_date": "2022-06-01",
                "f8835_placed_in_service_date": "2024-01-10", "f8835_kwh_produced": 1000000, "f8835_applicable_rate": "0.006",
                "f8835_qf_req_lt_1mw": False, "f8835_qf_req_before_1_29_2023": False, "f8835_qf_req_pwa": False, "f8835_qf_req_none": True},
     "expected_outputs": {"line_2": 6000, "line_8": 6000, "line_9": 6000, "line_15": 6000, "route_3800_line": "4e"},
     "notes": "Wind post-2021 $0.006: 1,000,000 × 0.006 = 6,000. No Q8 box (8d) -> NO ×5 -> line 9 = line 8 = 6,000. PIS 1/10/2024 -> within 4-yr window at TY2025 -> 4e."},
    {"scenario_name": "F8835-T4 — pass-through-only inflow (line 14)", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"tax_year": 2025, "f8835_passthrough_credit": 8500, "f8835_placed_in_service_date": "2019-05-01"},
     "expected_outputs": {"line_14": 8500, "line_15": 8500, "route_3800_line": "1f"},
     "notes": "K-1 §45 credit 8,500 at line 14; no direct facility. line 15 = 13+14 = 8,500. PIS 5/1/2019 -> TY2025 is beyond the 4-yr window -> Form 3800 line 1f."},
    {"scenario_name": "F8835-T5 — +10% domestic content + +10% energy community", "scenario_type": "normal", "sort_order": 5,
     "inputs": {"tax_year": 2025, "f8835_resource_type": "solar", "f8835_construction_begin_date": "2023-01-01",
                "f8835_placed_in_service_date": "2024-06-01", "f8835_kwh_produced": 1000000, "f8835_applicable_rate": "0.006",
                "f8835_qf_req_pwa": True, "f8835_domestic_content": True, "f8835_energy_community": True},
     "expected_outputs": {"line_8": 6000, "line_9": 30000, "line_10": 3000, "line_11": 3000, "line_12": 36000, "route_3800_line": "4e"},
     "notes": "Solar $0.006 × 1,000,000 = 6,000 (line 8). ×5 (PWA) -> line 9 = 30,000. +10% domestic (3,000) + 10% energy community (3,000) on line 9 -> line 12 = 30,000+3,000+3,000 = 36,000."},
]

F8835_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-8835-OBBBA", "IRS_2025_8835_INSTR", "primary", "Qualified facilities — construction begins before 2025 (all resources)"),
    ("R-8835-OBBBA", "IRC_45", "primary", "§45(d) begin-construction-before-2025 qualified facility"),
    ("R-8835-RATE", "IRS_2025_8835_FORM", "primary", "Part II pre-printed rate table ($0.006 / $0.003)"),
    ("R-8835-RATE", "IRS_2025_8835_INSTR", "secondary", "Credit rates for calendar year 2025 (Fed. Reg. 2025-09366)"),
    ("R-8835-REDUCE", "IRS_2025_8835_FORM", "primary", "Lines 4-8: phaseout, tax-exempt bond (15%), wind phasedown"),
    ("R-8835-INCREASED", "IRS_2025_8835_INSTR", "primary", "Increased credit ×5 (<1MW / before 1/29/2023 / PWA)"),
    ("R-8835-INCREASED", "IRC_45", "secondary", "§45(b)(6) increased credit amount"),
    ("R-8835-BONUS", "IRS_2025_8835_INSTR", "primary", "Domestic content (+10%) / energy community (+10%) of line 9"),
    ("R-8835-BONUS", "IRC_45", "secondary", "§45(b)(9) domestic content / §45(b)(11) energy community"),
    ("R-8835-ROUTE", "IRS_2025_8835_FORM", "primary", "Line 15 -> Form 3800 line 4e (4-yr PIS window) or 1f"),
    ("R-8835-PASSTHROUGH", "IRS_2025_8835_INSTR", "primary", "Line 14 pass-through K-1 codes; pass-through-only -> 3800 directly"),
]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY FORM LINKS
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_8835_FORM", "8835", "governs"),
    ("IRS_2025_8835_INSTR", "8835", "informs"),
    ("IRC_45", "8835", "informs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORMS ROSTER
# ═══════════════════════════════════════════════════════════════════════════

FORMS: list[dict] = [
    {"identity": F8835_IDENTITY, "facts": F8835_FACTS, "rules": F8835_RULES, "lines": F8835_LINES,
     "diagnostics": F8835_DIAGNOSTICS, "scenarios": F8835_SCENARIOS, "rule_links": F8835_RULE_LINKS},
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-8835-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Form 8835 line 15 -> Form 3800 Part III line 4e (4-yr PIS window) or line 1f",
     "description": ("Validates R-8835-ROUTE. line 15 = line 13 + line 14 -> Form 3800 line 4e if electricity was "
                     "produced within the 4-year period beginning on the placed-in-service date, else line 1f. Bug "
                     "it catches: always routing to 1f, or ignoring the PIS window."),
     "definition": {"kind": "flow_assertion", "form": "8835", "source_line": "15",
                    "route": {"within_4yr_pis": "FORM_3800.4e", "else": "FORM_3800.1f"}},
     "sort_order": 1},
    {"assertion_id": "FA-1040-8835-02", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "Form 8835 OBBBA gate — construction before 2025 (all resources), else no credit",
     "description": ("Validates R-8835-OBBBA / D_8835_001. Every §45 resource requires construction beginning "
                     "before 2025; a begin date >= 2025-01-01 zeroes the credit and fires D_8835_001. Bug it "
                     "catches: applying a per-resource cutoff, or conflating with the §45Y/§48E after-12/31/2025 termination."),
     "definition": {"kind": "gating_check", "form": "8835",
                    "blocker": "construction_begin_on_or_after_2025", "expect": {"credit_zero": True, "diagnostic": "D_8835_001"}},
     "sort_order": 2},
    {"assertion_id": "FA-1040-8835-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Form 8835 line 9 = line 8 ×5 when a Part I question-8 box is checked",
     "description": ("Validates R-8835-INCREASED. line 9 = line 8 × 5 if 8a (<1MW) OR 8b (before 1/29/2023) OR 8c "
                     "(PWA); else line 9 = line 8. The $0.006 form rate is the REDUCED rate — the ×5 restores the "
                     "full credit. Bug it catches: applying the ×5 without a Q8 box, or missing it when one is set."),
     "definition": {"kind": "formula_check", "form": "8835",
                    "formula": "line_9 == (line_8 * 5 if (q8a or q8b or q8c) else line_8)"},
     "sort_order": 3},
    {"assertion_id": "FA-1040-8835-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Form 8835 bonuses — lines 10/11 are each 10% of the post-×5 line 9",
     "description": ("Validates R-8835-BONUS. line 10 (domestic content) and line 11 (energy community) are each "
                     "line 9 × 10% (computed on the POST-×5 amount, not line 8); line 12 = 9 + 10 + 11. Bug it "
                     "catches: computing the bonuses off line 8, or stacking them incorrectly."),
     "definition": {"kind": "formula_check", "form": "8835",
                    "formula": "line_10 == (line_9 * 0.10 if domestic_content else 0); line_11 == (line_9 * 0.10 if energy_community else 0); line_12 == line_9 + line_10 + line_11"},
     "sort_order": 4},
]


# ═══════════════════════════════════════════════════════════════════════════
# Command
# ═══════════════════════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = (
        "Load the Form 8835 spec into Rule Studio (creates 8835 — §45 renewable "
        "electricity production credit; routes to Form 3800 line 4e/1f). Refuses to "
        "seed until Ken sets READY_TO_SEED=True."
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()

        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad 8835 spec (Renewable Electricity Production Credit)\n"))

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
                "\nREFUSING TO SEED 8835: not cleared to seed.\n\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True to proceed)\n"
                f"Empty spec sections:\n  {still_empty}\n\n"
                "This spec encodes tax law (IRC §45; the OBBBA before-2025 begin-construction\n"
                "gate; the year-keyed 2025 rate table; the ×5 / +10% / +10% bonuses; the line-15\n"
                "4e-vs-1f Form 3800 routing). Ken reviews the packet, then sets READY_TO_SEED =\n"
                "True. Idempotent via update_or_create — safe to re-run after edits."
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
        self.stdout.write("DATABASE TOTALS (after load_1040_form_8835)")
        self.stdout.write("=" * 60)
        for label, model in (("TaxForms", TaxForm), ("FormFacts", FormFact), ("FormRules", FormRule),
                             ("FormLines", FormLine), ("FormDiagnostics", FormDiagnostic),
                             ("TestScenarios", TestScenario), ("AuthoritySources", AuthoritySource),
                             ("RuleAuthorityLinks", RuleAuthorityLink), ("FlowAssertions", FlowAssertion)):
            self.stdout.write(f"{label+':':20}{model.objects.count()}")
        for fn in ("8835",):
            uncited = [r for r in FormRule.objects.filter(tax_form__form_number=fn) if not r.authority_links.exists()]
            if uncited:
                self.stdout.write(self.style.WARNING(f"\n{fn} rules with ZERO authority links: {len(uncited)}"))
                for r in uncited[:20]:
                    self.stdout.write(_safe(f"  {r.rule_id}: {r.title}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"{fn}: all rules have authority links."))
