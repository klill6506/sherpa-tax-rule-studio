"""Load the Form 4835 spec — Farm Rental Income and Expenses (1040 farm rental).

Creates ONE new TaxForm:

  - 4835 (Farm Rental Income and Expenses) — NEW. The landowner/sub-lessor's
    CROP-AND-LIVESTOCK-SHARE farm rental P&L, used when the owner did NOT materially
    participate. PER ACTIVITY (multiple Form 4835 per return; FK model — the Schedule
    C / Schedule F multi-instance precedent; QJV spouses each file a separate 4835).
    Part I income (lines 1-6) -> line 7 gross; Part II expenses (lines 8-30g) -> line
    31 total; line 32 net = line 7 - line 31.

    THE DEFINING TRAIT — NOT self-employment income. §1402(a)(1) excludes rentals from
    real estate from SE earnings; the form's own subtitle is "Income Not Subject to
    Self-Employment Tax." Contrast Schedule F (materially-participated farming) whose
    net DOES feed Schedule SE. This spec carries a HARD SE-EXCLUSION INVARIANT: 4835
    net (income OR loss) must NEVER reach the Schedule SE base (Ken decision, this
    session).

    CROSS-FORM FLOW (verified verbatim off the 2025 form face):
      - Line 7 gross farm rental income -> Schedule E (Form 1040) line 42 (the
        farming/fishing RECONCILIATION memo, NOT the income total).
      - Line 32 net income        -> Schedule E (Form 1040) line 40.
      - Line 34c deductible loss   -> Schedule E (Form 1040) line 40.
      - Line 12 depreciation/§179  <- the 4562 engine (the Schedule F line-14 reuse).

    LOSS PATH — FULLY COMPUTED (Ken decision, this session: "this is for MeF testing
    so I think we need to compute loss + 8582/6198"). A net loss on line 32 routes
    through the two existing RS limiter specs, in the verified order at-risk THEN
    passive:
      1. §465 AT-RISK (Form 6198) — only if box 34b ("some investment not at risk"):
         at_risk_allowed = min(|loss|, at_risk_amount). Existing spec: FORM_6198
         (authored in load_1120s_complete.py; §465(b) machinery, entity-agnostic).
         The 4835 instructions: "if you checked box 34b, you must complete Form 6198
         BEFORE going to Form 8582."
      2. §469 PASSIVE (Form 8582) — a 4835 farm rental is a rental activity for
         passive-loss purposes (form Purpose: "Use this form only if the activity was
         a rental activity for purposes of the passive activity loss limitations").
         With ACTIVE participation (Line A = Yes; §469(i), the 10%-interest test) it is
         eligible for the $25,000 special allowance (phases out 50% of MAGI over
         $100,000, zero at $150,000) — it plugs into the active-rental-RE bucket of the
         existing FORM_8582 spec (authored in load_1040_schedule_e.py, per-activity
         Parts IV-VIII). Without active participation -> the "all other passive" bucket
         (no special allowance). The 8582-allowed portion -> line 34c -> Schedule E
         line 40; the unallowed remainder is the activity's PAL carryforward.
    NOTE: this spec does NOT re-author 8582/6198 — the 4835 activity registers as an
    input activity into those shared computations and reads back its allocated allowed
    loss. The flow assertions are the cross-form contract; the tts build leg wires it.

    ELECTIONS — capture the $, flag the election (the Schedule F walk-item-C precedent):
      - CCC §77 loan-as-income (line 4a) -> D_4835_CCC_ELECT (amount still in line 7).
      - Crop-insurance §451(f)/(e) deferral (line 5c checkbox / 5d prior-year) ->
        D_4835_CROPINS_DEFER.
    §263A capitalized costs (line 30g, entered in parentheses, "263A" to the left) ->
    D_4835_263A (captured; reduces line 31 per the instructions).

    FORM-SELECTION GUARD (Ken decision, this session): if the taxpayer indicates they
    MATERIALLY participated, Form 4835 is the WRONG form -> D_4835_MATPART routes to
    Schedule F (the form Purpose: "materially participated ... instead use Schedule F").

Session 2026-07-04: spec-first probe found NO RS Form 4835 spec (a parallel tts
session hit a real 404 on GET /api/forms/lookup/4835/export/; RS server confirmed up).
Only an authority STUB existed (sources/federal_data/forms_supporting.py:
IRS_2025_4835_INSTR — instructions source + topic tags, no rules/facts/lines). Ken
ruled "start the 4835 spec." Authored by transcription from the primary source
verified the same day:

  - 2025 Form 4835 (f4835.pdf, Cat. No. 13117W, Attachment Seq. 37, Created 1/7/26) —
    the full 3-page face + General/Specific Instructions, read verbatim via the Read
    tool (pages 1-3). The line-7 right-column sum and the line-32/34c -> Sch E line 40
    routing verified directly off the face.
  - IRC §1402(a)(1) (SE exclusion), §469 / §469(i) (passive + special allowance),
    §465 (at-risk), §77 (CCC), §451(e)/(f) (crop-insurance/weather deferral), §263A
    (capitalization) — all already seeded RS sources (referenced, not re-created).

VERIFIED LINE-7 GROSS SUM (off the 2025 face — right-column entries only):
  L7 = L1 + L2b + L3b + L4a + L4c + L5b + L5d + L6.
  Mirrors the Schedule F line-9 pattern (4a CCC-elected + 4c CCC-forfeited-taxable
  BOTH included, NOT 4b; 5b crop-ins-taxable + 5d prior-year-deferral, NOT 5a/5c).

TOPIC SCOPE (Ken-locked 2026-07-04 via AskUserQuestion):
  IN: Part I income (1-6) -> L7; Part II expenses (8-30g) -> L31; L32 = L7 - L31;
      net income -> Sch E line 40; gross -> Sch E line 42; L12 depreciation via 4562;
      the FULL LOSS PATH (6198 at-risk before 8582 passive; active-participation $25k
      special allowance) -> L34c -> Sch E line 40; the SE-EXCLUSION hard invariant;
      elections captured+flagged; the material-participation form-selection guard;
      PER-ACTIVITY multi-instance.
  OUT / RED-defer-or-flag (no silent gap; each -> a D_4835_*):
      real-estate-professional non-passive treatment (D_4835_REPRO — the loss escapes
      §469 entirely; preparer-asserted); a single activity's losses reported on 2+
      forms / 28%-rate / §1231 separate-transaction 8582 edges (defer to the existing
      D_8582_MULTIFORM); the QJV spouse-split mechanics (each files a separate 4835 —
      modeled as separate instances, the split itself is preparer-driven).

requires_human_review WALK ITEMS (flagged for Ken's review walk):
  A. LOSS-PATH HAND-COMPUTATIONS — the 8582 $25k special-allowance figures in T3/T4/T5
     are hand-computed off the phaseout (25,000 - 50%*(MAGI-100,000)); confirm they
     match the FORM_8582 spec's Part IV/VI allocation before the tts build leg.
  B. 4835-as-rental-RE for §469(i) — the $25k special allowance is a "rental real
     estate" allowance; the 4835 instructions treat crop-share farm rental as rental
     real estate (Exception for Certain Rental Real Estate Activities / real-estate-
     professional cross-refs). Confirm the active-participation 4835 feeds the 8582
     ACTIVE-RENTAL-RE bucket (lines 1a-1d), not "all other passive" (2a-2d).
  C. SE-EXCLUSION INVARIANT scope — confirm the guard covers BOTH the standard method
     (line 1a/2) AND the farm optional method (a 4835 activity must never inflate
     gross farm income for the Sch SE Part II optional calc either).

Safety guard
------------
`READY_TO_SEED = False`. Content is authored; Ken reviews the packet (the verified
line-7 sum, the cross-form flow map incl. the line-42-vs-line-40 correction, the
computed loss-path numbers, the SE-exclusion invariant, the 3 walk items), flips the
sentinel, then we seed. Until then the command refuses to write to the DB. Idempotent
via update_or_create — safe to re-run after edits.

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
# SAFETY GUARD — flip ONLY after Ken's in-session review walk (the verified
# line-7 right-column sum, the cross-form flow map incl. the line-42-vs-line-40
# correction, the computed loss-path numbers with the 8582 $25k special
# allowance, the SE-exclusion hard invariant, the 3 requires_human_review walk
# items). Until then the command refuses to write to the DB (zero writes while
# False).
# ═══════════════════════════════════════════════════════════════════════════

# FLIPPED 2026-07-04 — Ken APPROVED the review walk in-session ("approve, flip and
# seed"): the verified line-7 right-column sum (1,2b,3b,4a,4c,5b,5d,6), the flow map
# (L7 -> Sch E line 42 reconciliation; L32/L34c -> Sch E line 40), the computed loss
# path (6198 at-risk BEFORE 8582 passive; T3/T4/T5/T6 special-allowance figures), the
# SE-exclusion hard invariant (§1402(a)(1); D_4835_SE_GUARD + FA-1040-4835-05), and
# the flag set (MATPART/CCC/CROPINS/263A/REPRO). Walk items A/B/C noted in the header.
READY_TO_SEED = True


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1040"]


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS (every value cited; never training memory)
# ═══════════════════════════════════════════════════════════════════════════

# §469(i) rental real-estate special allowance — verified off the FORM_8582 spec
# (load_1040_schedule_e.py) and §469(i)(2)/(3). NON-INDEXED (statutory).
PAL_SPECIAL_ALLOWANCE = 25000          # $12,500 if MFS living apart
PAL_PHASEOUT_START_MAGI = 100000       # allowance reduced 50% of MAGI over this
PAL_PHASEOUT_END_MAGI = 150000         # allowance = 0 at/above this


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY TOPICS
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("farm_rental_4835", "Form 4835 — farm rental (crop/livestock share, non-material-participation) income + expenses -> Sch E line 40; NOT SE income (§1402(a)(1))"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_4835_INSTR",    # the pre-existing authority stub (forms_supporting.py)
    "IRC_1402A1",             # §1402(a)(1) rentals-from-real-estate SE exclusion
    "IRC_469",                # §469 passive activity loss (+ §469(i) special allowance)
    "IRC_465",                # §465 at-risk
    "IRC_77",                 # §77 CCC loan-as-income election
    "IRC_451_EF",             # §451(e)/(f) crop-insurance / weather deferral
    "IRC_263A",               # §263A capitalization (line 30g)
    "IRC_199A",               # §199A QBI (rental only if it rises to a §162 trade/business)
    "IRS_2025_8582_INSTR",    # Form 8582 passive-loss limitation
    "IRS_2025_6198_INSTR",    # Form 6198 at-risk limitation
    "IRS_2025_SCHE_INSTR",    # Schedule E lines 40/42 (where 4835 lands)
    "IRS_PUB_225",            # Pub 225 farm income/expense + election narratives
]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY SOURCES (with embedded excerpts) — CREATE
# Transcribed 2026-07-04 from the fetched 2025 Form 4835 PDF (read verbatim).
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_4835_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Form 4835 — Farm Rental Income and Expenses",
        "citation": "Form 4835 (2025); f4835.pdf; Attachment Sequence No. 37; Cat. No. 13117W; Created 1/7/26",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f4835.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": "Full 3-page face + instructions transcribed 2026-07-04 (Read tool, pages 1-3). Real face; PER ACTIVITY. NOT SE income (subtitle).",
        "topics": ["farm_rental_4835"],
        "excerpts": [
            {
                "excerpt_label": "Header + Line A + Part I Gross Farm Rental Income (lines 1-7, verbatim)",
                "location_reference": "Form 4835 (2025), title + line A + Part I",
                "excerpt_text": (
                    "Farm Rental Income and Expenses. Crop and Livestock Shares (Not Cash) Received by "
                    "Landowner (or Sub-Lessor). Income Not Subject to Self-Employment Tax. "
                    "A Did you actively participate in the operation of this farm during 2025? "
                    "Part I Gross Farm Rental Income—Based on Production. "
                    "1 Income from production of livestock, produce, grains, and other crops. "
                    "2a Cooperative distributions (Form(s) 1099-PATR); 2b Taxable amount. "
                    "3a Agricultural program payments; 3b Taxable amount. "
                    "4 Commodity Credit Corporation (CCC) loans: 4a CCC loans reported under election; "
                    "4b CCC loans forfeited; 4c Taxable amount. "
                    "5 Crop insurance proceeds and federal crop disaster payments: 5a Amount received in "
                    "2025; 5b Taxable amount; 5c If election to defer to 2026 is attached, check here; "
                    "5d Amount deferred from 2024. "
                    "6 Other income, including federal and state gasoline or fuel tax credit or refund. "
                    "7 Gross farm rental income. Add amounts in the right column for lines 1 through 6. "
                    "Enter the total here and on Schedule E (Form 1040), line 42."
                ),
                "summary_text": (
                    "L7 (gross) = right-column sum of lines 1-6 = L1 + L2b + L3b + L4a + L4c + L5b + L5d "
                    "+ L6 (mirrors Sch F: 4a CCC-elected AND 4c CCC-forfeited-taxable, NOT 4b; 5b + 5d, "
                    "NOT 5a/5c). L7 -> Schedule E line 42 (farming/fishing RECONCILIATION memo). Line A "
                    "active participation = §469(i) special-allowance test (10% interest). Title: NOT SE income."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part II Expenses + line 31/32 net + line 34 at-risk/loss (lines 8-34c, verbatim)",
                "location_reference": "Form 4835 (2025), Part II",
                "excerpt_text": (
                    "Part II Expenses—Farm Rental Property. "
                    "8 Car and truck expenses (attach Form 4562). 9 Chemicals. 10 Conservation expenses. "
                    "11 Custom hire (machine work). 12 Depreciation and section 179 expense deduction not "
                    "claimed elsewhere. 13 Employee benefit programs other than on line 21. 14 Feed. 15 "
                    "Fertilizers and lime. 16 Freight and trucking. 17 Gasoline, fuel, and oil. 18 Insurance "
                    "(other than health). 19a Interest — Mortgage (paid to banks, etc.); 19b Other. 20 Labor "
                    "hired (less employment credits). 21 Pension and profit-sharing plans. 22a Rent or lease "
                    "— Vehicles, machinery, and equipment; 22b Other (land, animals, etc.). 23 Repairs and "
                    "maintenance. 24 Seeds and plants. 25 Storage and warehousing. 26 Supplies. 27 Taxes. 28 "
                    "Utilities. 29 Veterinary, breeding, and medicine. 30a-30g Other expenses (specify). 31 "
                    "Total expenses. Add lines 8 through 30g. 32 Net farm rental income or (loss). Subtract "
                    "line 31 from line 7. If the result is income, enter it here and on Schedule E (Form "
                    "1040), line 40. If the result is a loss, you must go to line 34. 33 Reserved for future "
                    "use. 34 If line 32 is a loss, check the box that describes your investment in this "
                    "activity: 34a All investment is at risk; 34b Some investment is not at risk. 34c You may "
                    "have to complete Form 8582 to determine your deductible loss, regardless of which box "
                    "you checked. If you checked box 34b, you must complete Form 6198 before going to Form "
                    "8582. In either case, enter the deductible loss here and on Schedule E (Form 1040), line 40."
                ),
                "summary_text": (
                    "L31 = Σ(lines 8-30f) reduced by 30g (§263A capitalized, entered in parentheses). "
                    "L32 = L7 - L31. Income -> Sch E line 40. Loss -> line 34: 34a all-at-risk / 34b some-"
                    "not-at-risk (Form 6198 BEFORE 8582); L34c deductible loss (after 8582/6198) -> Sch E "
                    "line 40. NO line feeds Schedule SE (§1402(a)(1))."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Purpose / who files — material participation & wrong-form routing (verbatim)",
                "location_reference": "Form 4835 (2025), page 2, Purpose of Form",
                "excerpt_text": (
                    "If you were the landowner (or sub-lessor) and did not materially participate (for "
                    "self-employment tax purposes) in the operation or management of the farm, use Form 4835 "
                    "to report farm rental income based on crops or livestock produced by the tenant. Use this "
                    "form only if the activity was a rental activity for purposes of the passive activity loss "
                    "limitations. If you have net income on line 32, your tax may be less if you figure it "
                    "using Schedule J (Form 1040). Do not use Form 4835 if you were a/an: Tenant — instead use "
                    "Schedule F; Landowner (or sub-lessor) and materially participated — instead use Schedule "
                    "F; Landowner and received cash rent for pasture or farmland based on a flat charge — "
                    "instead report on Schedule E, Part I; Estate or trust — Schedule E, Part I; Partnership "
                    "or S corporation — Form 8825."
                ),
                "summary_text": (
                    "Materially participated -> WRONG form, use Schedule F (D_4835_MATPART). Must be a rental "
                    "activity for §469 passive-loss purposes. Net income on line 32 -> Schedule J farm income "
                    "averaging available. Cash-flat-rent -> Sch E Part I; estate/trust -> Sch E Part I; "
                    "partnership/S-corp -> Form 8825 (all out of 1040 scope)."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
]

# No new excerpts on existing sources this unit.
NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []


# ═══════════════════════════════════════════════════════════════════════════
# FORM: 4835 (Farm Rental Income and Expenses)
# ═══════════════════════════════════════════════════════════════════════════

F4835_IDENTITY = {
    "form_number": "4835",
    "form_title": "Form 4835 — Farm Rental Income and Expenses (TY2025)",
    "notes": (
        "1040 farm-rental unit. Landowner/sub-lessor crop-and-livestock-share rental, "
        "NON-material-participation. PER ACTIVITY (multiple 4835 per return; FK model — "
        "the Sch C/Sch F precedent; QJV spouses each file a separate 4835). Part I income "
        "(1-6) -> L7 gross; Part II expenses (8-30g) -> L31; L32 = L7 - L31. Net income -> "
        "Sch E line 40; gross -> Sch E line 42 (reconciliation memo); L12 depreciation <- "
        "4562 engine. DEFINING TRAIT: NOT SE income (§1402(a)(1)) — HARD SE-EXCLUSION "
        "INVARIANT (contrast Sch F). LOSS PATH FULLY COMPUTED (MeF): L32 loss -> §465 "
        "at-risk (Form 6198, if 34b) BEFORE §469 passive (Form 8582; active participation "
        "-> $25k special allowance) -> L34c -> Sch E line 40; unallowed = PAL carryforward. "
        "Elections captured+flagged (CCC §77 4a; crop-ins §451(f) 5c/5d). §263A on 30g "
        "flagged. Material participation -> D_4835_MATPART (use Schedule F). Real-estate-"
        "professional non-passive escape RED-defer (D_4835_REPRO)."
    ),
}

F4835_FACTS: list[dict] = [
    # ── Header / identity (metadata; e-file structured fields) ──
    {"fact_key": "f4835_activity_name", "label": "Farm rental activity name/description", "data_type": "string", "sort_order": 1,
     "notes": "PER ACTIVITY. Metadata; each rental farm its own Form 4835."},
    {"fact_key": "f4835_ein", "label": "Employer ID number (EIN), if any", "data_type": "string", "sort_order": 2,
     "notes": "PER ACTIVITY. Format NN-NNNNNNN or blank (MeF rule). Needed only for a qualified plan / employment/excise/etc. return."},
    {"fact_key": "f4835_active_participation_A", "label": "Line A — Did you actively participate in the operation of this farm during 2025? (Y/N)", "data_type": "boolean", "sort_order": 3,
     "notes": "PER ACTIVITY. §469(i) ACTIVE-participation test (distinct from MATERIAL participation). Drives the Form 8582 $25,000 special-allowance eligibility. False if interest (incl. spouse) < 10% by value."},
    {"fact_key": "f4835_material_participation", "label": "Did the landowner MATERIALLY participate? (threshold form-selection question; Y/N)", "data_type": "boolean", "sort_order": 4,
     "notes": "PER ACTIVITY. NOT a numbered line — the Purpose-of-Form threshold. True -> WRONG form -> D_4835_MATPART (use Schedule F). Default False (4835 presupposes non-material participation)."},
    {"fact_key": "f4835_real_estate_professional", "label": "Real estate professional materially participating in THIS activity? (Y/N)", "data_type": "boolean", "sort_order": 5,
     "notes": "PER ACTIVITY. Page-3 exception: a real-estate-professional materially participating -> loss NOT subject to §469 -> escapes 8582 (D_4835_REPRO RED-defer; preparer-asserted)."},
    {"fact_key": "f4835_qbi_trade_or_business", "label": "Does this farm rental rise to a §162 trade/business for §199A QBI? (preparer determination; Y/N)", "data_type": "boolean", "default_value": "false", "sort_order": 6,
     "notes": ("PER ACTIVITY. §199A QBI determination — DEFAULT False (not QBI). 4835 crop-share rental is QBI "
               "ONLY if it (a) rises to a §162 trade/business, (b) is a self-rental to a commonly-controlled "
               "entity (§1.199A-1(b)(14)), or (c) meets the Rev. Proc. 2019-38 250-hour safe harbor. Facts-and-"
               "circumstances; preparer asserts. Drives R-4835-QBI / D_4835_QBI. Do NOT auto-feed 8995/8995-A.")},

    # ── Part I income inputs ──
    {"fact_key": "f4835_livestock_crops_1", "label": "Line 1 — Income from production of livestock, produce, grains, and other crops", "data_type": "decimal", "default_value": "0", "sort_order": 10, "notes": "PER ACTIVITY. Right column -> L7."},
    {"fact_key": "f4835_coop_distributions_2a", "label": "Line 2a — Cooperative distributions (Form(s) 1099-PATR, gross)", "data_type": "decimal", "default_value": "0", "sort_order": 11, "notes": "PER ACTIVITY. 2a gross (memo); 2b taxable feeds L7."},
    {"fact_key": "f4835_coop_distributions_taxable_2b", "label": "Line 2b — Cooperative distributions, taxable amount", "data_type": "decimal", "default_value": "0", "sort_order": 12, "notes": "PER ACTIVITY. Into L7."},
    {"fact_key": "f4835_ag_program_payments_3a", "label": "Line 3a — Agricultural program payments (gross)", "data_type": "decimal", "default_value": "0", "sort_order": 13, "notes": "PER ACTIVITY. 3a gross (memo); 3b taxable feeds L7."},
    {"fact_key": "f4835_ag_program_payments_taxable_3b", "label": "Line 3b — Agricultural program payments, taxable amount", "data_type": "decimal", "default_value": "0", "sort_order": 14, "notes": "PER ACTIVITY. Into L7."},
    {"fact_key": "f4835_ccc_loans_election_4a", "label": "Line 4a — CCC loans reported under election (§77)", "data_type": "decimal", "default_value": "0", "sort_order": 15, "notes": "PER ACTIVITY. §77 election -> D_4835_CCC_ELECT (flag election); amount STILL flows into L7."},
    {"fact_key": "f4835_ccc_loans_forfeited_4b", "label": "Line 4b — CCC loans forfeited (memo)", "data_type": "decimal", "default_value": "0", "sort_order": 16, "notes": "PER ACTIVITY. Memo; NOT in L7 (4c is)."},
    {"fact_key": "f4835_ccc_loans_taxable_4c", "label": "Line 4c — CCC loans forfeited, taxable amount", "data_type": "decimal", "default_value": "0", "sort_order": 17, "notes": "PER ACTIVITY. Into L7."},
    {"fact_key": "f4835_crop_insurance_received_5a", "label": "Line 5a — Crop insurance proceeds received in 2025 (memo)", "data_type": "decimal", "default_value": "0", "sort_order": 18, "notes": "PER ACTIVITY. 5a received (memo); 5b taxable feeds L7."},
    {"fact_key": "f4835_crop_insurance_taxable_5b", "label": "Line 5b — Crop insurance proceeds, taxable amount", "data_type": "decimal", "default_value": "0", "sort_order": 19, "notes": "PER ACTIVITY. Into L7."},
    {"fact_key": "f4835_crop_insurance_defer_election_5c", "label": "Line 5c — Election to defer crop insurance to 2026 attached (checkbox)", "data_type": "boolean", "sort_order": 20, "notes": "PER ACTIVITY. §451(f) deferral election -> D_4835_CROPINS_DEFER (flag election)."},
    {"fact_key": "f4835_crop_insurance_deferred_prior_5d", "label": "Line 5d — Amount deferred from 2024 (now recognized)", "data_type": "decimal", "default_value": "0", "sort_order": 21, "notes": "PER ACTIVITY. Prior-year deferral now taxable; into L7."},
    {"fact_key": "f4835_other_income_6", "label": "Line 6 — Other income (incl. federal/state gasoline or fuel tax credit/refund)", "data_type": "decimal", "default_value": "0", "sort_order": 22, "notes": "PER ACTIVITY. Into L7."},

    # ── Part II expense inputs ──
    {"fact_key": "f4835_car_truck_8", "label": "Line 8 — Car and truck expenses (attach Form 4562)", "data_type": "decimal", "default_value": "0", "sort_order": 30, "notes": "PER ACTIVITY."},
    {"fact_key": "f4835_chemicals_9", "label": "Line 9 — Chemicals", "data_type": "decimal", "default_value": "0", "sort_order": 31, "notes": "PER ACTIVITY."},
    {"fact_key": "f4835_conservation_10", "label": "Line 10 — Conservation expenses (≤25% gross farm income; §175)", "data_type": "decimal", "default_value": "0", "sort_order": 32, "notes": "PER ACTIVITY. Instruction: deduction cannot exceed 25% of gross farm income (limit preparer-verified in v1)."},
    {"fact_key": "f4835_custom_hire_11", "label": "Line 11 — Custom hire (machine work)", "data_type": "decimal", "default_value": "0", "sort_order": 33, "notes": "PER ACTIVITY."},
    {"fact_key": "f4835_depreciation_179_12", "label": "Line 12 — Depreciation and section 179 (from Form 4562)", "data_type": "decimal", "default_value": "0", "sort_order": 34, "notes": "PER ACTIVITY. CALCULATED via the 4562 engine (carried/YELLOW)."},
    {"fact_key": "f4835_employee_benefits_13", "label": "Line 13 — Employee benefit programs other than on line 21", "data_type": "decimal", "default_value": "0", "sort_order": 35, "notes": "PER ACTIVITY."},
    {"fact_key": "f4835_feed_14", "label": "Line 14 — Feed", "data_type": "decimal", "default_value": "0", "sort_order": 36, "notes": "PER ACTIVITY."},
    {"fact_key": "f4835_fertilizers_15", "label": "Line 15 — Fertilizers and lime", "data_type": "decimal", "default_value": "0", "sort_order": 37, "notes": "PER ACTIVITY."},
    {"fact_key": "f4835_freight_16", "label": "Line 16 — Freight and trucking", "data_type": "decimal", "default_value": "0", "sort_order": 38, "notes": "PER ACTIVITY."},
    {"fact_key": "f4835_gasoline_fuel_17", "label": "Line 17 — Gasoline, fuel, and oil", "data_type": "decimal", "default_value": "0", "sort_order": 39, "notes": "PER ACTIVITY."},
    {"fact_key": "f4835_insurance_18", "label": "Line 18 — Insurance (other than health)", "data_type": "decimal", "default_value": "0", "sort_order": 40, "notes": "PER ACTIVITY."},
    {"fact_key": "f4835_interest_mortgage_19a", "label": "Line 19a — Interest, mortgage (paid to banks, etc.)", "data_type": "decimal", "default_value": "0", "sort_order": 41, "notes": "PER ACTIVITY. §163 interest could be limited (Form 8990) — preparer-handled in v1."},
    {"fact_key": "f4835_interest_other_19b", "label": "Line 19b — Interest, other", "data_type": "decimal", "default_value": "0", "sort_order": 42, "notes": "PER ACTIVITY."},
    {"fact_key": "f4835_labor_20", "label": "Line 20 — Labor hired (less employment credits)", "data_type": "decimal", "default_value": "0", "sort_order": 43, "notes": "PER ACTIVITY."},
    {"fact_key": "f4835_pension_21", "label": "Line 21 — Pension and profit-sharing plans", "data_type": "decimal", "default_value": "0", "sort_order": 44, "notes": "PER ACTIVITY."},
    {"fact_key": "f4835_rent_lease_vehicles_22a", "label": "Line 22a — Rent or lease: vehicles, machinery, equipment", "data_type": "decimal", "default_value": "0", "sort_order": 45, "notes": "PER ACTIVITY. Lease-inclusion amount (30+ day vehicle) preparer-handled."},
    {"fact_key": "f4835_rent_lease_other_22b", "label": "Line 22b — Rent or lease: other (land, animals, etc.)", "data_type": "decimal", "default_value": "0", "sort_order": 46, "notes": "PER ACTIVITY."},
    {"fact_key": "f4835_repairs_23", "label": "Line 23 — Repairs and maintenance", "data_type": "decimal", "default_value": "0", "sort_order": 47, "notes": "PER ACTIVITY."},
    {"fact_key": "f4835_seeds_24", "label": "Line 24 — Seeds and plants", "data_type": "decimal", "default_value": "0", "sort_order": 48, "notes": "PER ACTIVITY."},
    {"fact_key": "f4835_storage_25", "label": "Line 25 — Storage and warehousing", "data_type": "decimal", "default_value": "0", "sort_order": 49, "notes": "PER ACTIVITY."},
    {"fact_key": "f4835_supplies_26", "label": "Line 26 — Supplies", "data_type": "decimal", "default_value": "0", "sort_order": 50, "notes": "PER ACTIVITY."},
    {"fact_key": "f4835_taxes_27", "label": "Line 27 — Taxes", "data_type": "decimal", "default_value": "0", "sort_order": 51, "notes": "PER ACTIVITY."},
    {"fact_key": "f4835_utilities_28", "label": "Line 28 — Utilities", "data_type": "decimal", "default_value": "0", "sort_order": 52, "notes": "PER ACTIVITY."},
    {"fact_key": "f4835_vet_29", "label": "Line 29 — Veterinary, breeding, and medicine", "data_type": "decimal", "default_value": "0", "sort_order": 53, "notes": "PER ACTIVITY."},
    {"fact_key": "f4835_other_expenses_30af", "label": "Lines 30a-30f — Other expenses (specify; sum of a-f)", "data_type": "decimal", "default_value": "0", "sort_order": 54, "notes": "PER ACTIVITY. Sum of the six 'other' specify lines 30a-30f (each a labeled input in the render leg)."},
    {"fact_key": "f4835_capitalized_263a_30g", "label": "Line 30g — §263A capitalized costs (entered in parentheses, negative)", "data_type": "decimal", "default_value": "0", "sort_order": 55, "notes": "PER ACTIVITY. §263A uniform-capitalization amount that REDUCES total expenses (parenthetical). -> D_4835_263A."},

    # ── At-risk / loss inputs ──
    {"fact_key": "f4835_all_at_risk_34a", "label": "Line 34a — All investment is at risk", "data_type": "boolean", "sort_order": 60, "notes": "PER ACTIVITY. Loss present + 34a -> skip Form 6198 (full loss goes to §469 passive step)."},
    {"fact_key": "f4835_some_not_at_risk_34b", "label": "Line 34b — Some investment is not at risk (Form 6198)", "data_type": "boolean", "sort_order": 61, "notes": "PER ACTIVITY. Loss + 34b -> §465 at-risk limit (Form 6198) BEFORE §469 passive (Form 8582)."},
    {"fact_key": "f4835_at_risk_amount", "label": "§465 at-risk amount (Form 6198 input; when 34b)", "data_type": "decimal", "default_value": "0", "sort_order": 62, "notes": "PER ACTIVITY. Amount at risk at year end (§465(b)) — caps the deductible loss when 34b checked."},
    {"fact_key": "f4835_prior_year_unallowed_pal", "label": "Prior-year unallowed passive activity loss for this activity (Form 8582 input)", "data_type": "decimal", "default_value": "0", "sort_order": 63, "notes": "PER ACTIVITY. Suspended §469 loss carried into this year; combined on Form 8582 (may reduce net income too)."},
    {"fact_key": "f4835_magi_for_pal", "label": "Modified AGI for the §469(i) $25k special-allowance phaseout", "data_type": "decimal", "default_value": "0", "sort_order": 64, "notes": "PER RETURN (read by 8582). Allowance = 25,000 - 50%*(MAGI - 100,000); zero at 150,000."},

    # ── Outputs (traceability) ──
    {"fact_key": "f4835_gross_income_l7", "label": "Line 7 — gross farm rental income (output -> Sch E line 42)", "data_type": "decimal", "sort_order": 80, "notes": "OUTPUT. = L1 + L2b + L3b + L4a + L4c + L5b + L5d + L6. -> Schedule E line 42 (reconciliation)."},
    {"fact_key": "f4835_total_expenses_l31", "label": "Line 31 — total expenses (output)", "data_type": "decimal", "sort_order": 81, "notes": "OUTPUT. = Σ(8..30f) - 30g(§263A)."},
    {"fact_key": "f4835_net_income_l32", "label": "Line 32 — net farm rental income or (loss) (output -> Sch E line 40 when income)", "data_type": "decimal", "sort_order": 82, "notes": "OUTPUT. = L7 - L31. Income -> Sch E line 40. Loss -> line 34 path. NEVER to Schedule SE (§1402(a)(1))."},
    {"fact_key": "f4835_deductible_loss_l34c", "label": "Line 34c — deductible loss after at-risk (6198) then passive (8582) (output -> Sch E line 40)", "data_type": "decimal", "sort_order": 83, "notes": "OUTPUT (negative). = the §465-then-§469-allowed portion of the L32 loss. -> Schedule E line 40."},
    {"fact_key": "f4835_suspended_pal", "label": "Suspended passive loss carryforward (output)", "data_type": "decimal", "sort_order": 84, "notes": "OUTPUT. The §469-unallowed remainder (this activity's PAL carryforward). At-risk-suspended (§465) tracked separately."},
]

F4835_RULES: list[dict] = [
    {"rule_id": "R-4835-GROSS", "title": "Line 7 — gross farm rental income (verified right-column sum)", "rule_type": "calculation", "precedence": 1, "sort_order": 1,
     "formula": "L7 = L1 + L2b + L3b + L4a + L4c + L5b + L5d + L6.",
     "inputs": ["f4835_livestock_crops_1", "f4835_coop_distributions_taxable_2b", "f4835_ag_program_payments_taxable_3b",
                "f4835_ccc_loans_election_4a", "f4835_ccc_loans_taxable_4c", "f4835_crop_insurance_taxable_5b",
                "f4835_crop_insurance_deferred_prior_5d", "f4835_other_income_6"],
     "outputs": ["7"],
     "description": ("PER ACTIVITY. VERIFIED verbatim against the 2025 face — 'Add amounts in the right column "
                     "for lines 1 through 6': (1, 2b, 3b, 4a, 4c, 5b, 5d, 6). Includes BOTH 4a (CCC elected) and "
                     "4c (CCC forfeiture taxable), NOT 4b; 5b (crop-ins taxable) and 5d (prior-year deferral), "
                     "NOT 5a/5c. -> Schedule E line 42 (farming/fishing reconciliation memo).")},
    {"rule_id": "R-4835-DEPR", "title": "Line 12 — depreciation and §179 (4562 engine reuse)", "rule_type": "routing", "precedence": 2, "sort_order": 2,
     "formula": "L12 = depreciation + §179 from the 4562 engine for this activity's assets (carried/YELLOW).",
     "inputs": [], "outputs": ["12"],
     "description": ("PER ACTIVITY. Reuse depreciation_engine.py (aggregate_depreciation flow_to=form_4835 — the "
                     "Schedule F line-14 / Schedule C line-13 precedent). Rental-farm assets attach to the 4835. Build-leg wiring.")},
    {"rule_id": "R-4835-EXPENSES", "title": "Line 31 — total expenses (reduced by §263A on 30g)", "rule_type": "calculation", "precedence": 3, "sort_order": 3,
     "formula": "L31 = (L8 + L9 + L10 + L11 + L12 + L13 + L14 + L15 + L16 + L17 + L18 + L19a + L19b + L20 + L21 + L22a + L22b + L23 + L24 + L25 + L26 + L27 + L28 + L29 + L30a..f) - L30g(§263A).",
     "inputs": [], "outputs": ["31"],
     "description": ("PER ACTIVITY. 'Add lines 8 through 30g.' Per the instructions, a §263A amount on 30g is "
                     "entered in parentheses and REDUCES the total: L31 = Σ(8..30f) - 30g. No home-office line.")},
    {"rule_id": "R-4835-NET", "title": "Line 32 — net farm rental income/(loss) -> Schedule E line 40", "rule_type": "calculation", "precedence": 4, "sort_order": 4,
     "formula": "L32 = L7 - L31. If income -> Schedule E line 40. If loss -> line 34 path (at-risk then passive).",
     "inputs": ["f4835_gross_income_l7", "f4835_total_expenses_l31"], "outputs": ["32"],
     "description": ("PER ACTIVITY. The topic's primary cross-form output. Net INCOME on line 32 flows to Schedule "
                     "E (Form 1040) line 40 ('Net farm rental income or (loss) from Form 4835'). A LOSS is NOT "
                     "entered directly on line 32 — it must run the line-34 at-risk/passive gauntlet first (R-4835-LOSS).")},
    {"rule_id": "R-4835-SE-EXCLUSION", "title": "SE-EXCLUSION INVARIANT — 4835 net NEVER enters the Schedule SE base (§1402(a)(1))", "rule_type": "routing", "precedence": 5, "sort_order": 5,
     "formula": "ASSERT: no part of L32 / L34c / any 4835 line is included in the Schedule SE base (line 1a, line 2, or the farm-optional gross farm income). Fires D_4835_SE_GUARD if violated.",
     "inputs": ["f4835_net_income_l32"], "outputs": [],
     "description": ("PER ACTIVITY. THE DEFINING TRAIT (Ken decision, this session). §1402(a)(1) excludes rentals "
                     "from real estate from self-employment earnings; the form subtitle is 'Income Not Subject to "
                     "Self-Employment Tax.' Contrast Schedule F (materially-participated farming) whose L34 DOES "
                     "feed Sch SE line 1a. Hard invariant: 4835 income AND loss both stay out of the SE base — "
                     "standard method (1a/2) AND the farm optional gross-farm-income (WALK ITEM C).")},
    {"rule_id": "R-4835-MATPART", "title": "Material participation -> WRONG form (use Schedule F)", "rule_type": "routing", "precedence": 6, "sort_order": 6,
     "formula": "If f4835_material_participation is True -> D_4835_MATPART; do not compute (the farm belongs on Schedule F).",
     "inputs": ["f4835_material_participation"], "outputs": [],
     "description": ("PER ACTIVITY. Form-selection guard (Ken decision, this session). Purpose of Form: a landowner "
                     "who MATERIALLY participated must use Schedule F, not Form 4835. Routes the preparer rather "
                     "than silently computing a return on the wrong form.")},
    {"rule_id": "R-4835-LOSS", "title": "Line 32 loss -> §465 at-risk (6198) BEFORE §469 passive (8582) -> line 34c", "rule_type": "calculation", "precedence": 7, "sort_order": 7,
     "formula": ("If L7 - L31 < 0 (tentative loss T = L31 - L7): "
                 "STEP 1 at-risk — if 34b: A = min(T, at_risk_amount) [§465, Form 6198]; else A = T. "
                 "STEP 2 passive — if real_estate_professional: allowed = A (escapes §469); "
                 "elif active_participation (Line A): allowance = max(0, 25000 - 0.5*max(0, MAGI - 100000)); "
                 "allowed = min(A, allowance + passive_income_offset); "
                 "else allowed = passive_income_offset (no special allowance). "
                 "L34c = -allowed -> Schedule E line 40; suspended_pal = A - allowed; at-risk-suspended = T - A."),
     "inputs": ["f4835_net_income_l32", "f4835_all_at_risk_34a", "f4835_some_not_at_risk_34b", "f4835_at_risk_amount",
                "f4835_active_participation_A", "f4835_real_estate_professional", "f4835_magi_for_pal",
                "f4835_prior_year_unallowed_pal"],
     "outputs": ["34a", "34b", "34c"],
     "description": ("PER ACTIVITY. Ken decision (this session): compute the FULL loss path for MeF, not RED-defer. "
                     "Order VERIFIED off the face: 'If you checked box 34b, you must complete Form 6198 BEFORE "
                     "going to Form 8582.' §465 caps the loss at the at-risk amount; §469 then applies the passive "
                     "limitation — the 4835 activity feeds the EXISTING FORM_8582 spec as a rental activity (active "
                     "participation -> the $25k special-allowance bucket, lines 1a-1d; else 'all other passive', "
                     "lines 2a-2d). The 8582-allowed portion -> line 34c -> Sch E line 40; the §469-unallowed "
                     "remainder is this activity's PAL carryforward; the §465-suspended remainder is a separate "
                     "at-risk carryforward. WALK ITEMS A/B: the special-allowance figures + the rental-RE bucket.")},
    {"rule_id": "R-4835-REPRO", "title": "Real estate professional (material participation) — §469 escape (RED-defer)", "rule_type": "routing", "precedence": 8, "sort_order": 8,
     "formula": "If f4835_real_estate_professional is True AND L32 < 0 -> D_4835_REPRO; the loss is not subject to §469 (fully deductible, enter on line 34c). v1 does not auto-assert REP status.",
     "inputs": ["f4835_real_estate_professional"], "outputs": [],
     "description": ("PER ACTIVITY. Page-3 exception: a real-estate professional who materially participated is NOT "
                     "subject to the passive-loss limitation. RED-defer: the REP determination (750-hour / >50% "
                     "tests) is preparer-asserted, not modeled — flag it (the loss is captured).")},
    {"rule_id": "R-4835-ELECTIONS", "title": "CCC §77 / crop-insurance §451(f) — capture income, flag the election", "rule_type": "routing", "precedence": 9, "sort_order": 9,
     "formula": "If L4a > 0 -> D_4835_CCC_ELECT; if 5c checked -> D_4835_CROPINS_DEFER. The dollar amounts STILL flow to line 7.",
     "inputs": ["f4835_ccc_loans_election_4a", "f4835_crop_insurance_defer_election_5c"], "outputs": [],
     "description": ("PER ACTIVITY. The Schedule F walk-item-C precedent: capture the dollar amounts where they land "
                     "(4a and 5b/5d into L7); the election machinery (attachments, multi-year binding effect of §77, "
                     "the §451(f) deferral statement) is preparer-handled.")},
    {"rule_id": "R-4835-263A", "title": "Line 30g — §263A capitalized costs (capture + flag)", "rule_type": "routing", "precedence": 10, "sort_order": 10,
     "formula": "If L30g != 0 -> D_4835_263A. The amount reduces L31 (parenthetical) per R-4835-EXPENSES.",
     "inputs": ["f4835_capitalized_263a_30g"], "outputs": [],
     "description": ("PER ACTIVITY. Instruction 'How to report': §263A uniform-capitalization amounts go on 30g in "
                     "parentheses with '263A' to the left; they reduce total expenses. Flag that the capitalization "
                     "determination is preparer-driven; the entered amount is honored.")},
    {"rule_id": "R-4835-SCHJ", "title": "Net income on line 32 -> Schedule J farm income averaging available (info)", "rule_type": "routing", "precedence": 11, "sort_order": 11,
     "formula": "If L32 > 0 -> D_4835_SCHJ (info): the tax may be lower using Schedule J farm income averaging.",
     "inputs": ["f4835_net_income_l32"], "outputs": [],
     "description": ("PER ACTIVITY. Purpose of Form: 'If you have net income on line 32, your tax may be less if you "
                     "figure it using Schedule J.' Informational routing (Schedule J is its own form unit).")},
    {"rule_id": "R-4835-QBI", "title": "§199A QBI — only if the rental rises to a §162 trade/business (preparer-asserted)", "rule_type": "routing", "precedence": 12, "sort_order": 12,
     "formula": ("If f4835_qbi_trade_or_business is True AND L32 > 0 -> the net (line 32) is QBI from a qualified "
                 "trade/business and may feed Form 8995/8995-A. Else (DEFAULT) -> NOT QBI; no 8995/8995-A feed. "
                 "Always -> D_4835_QBI (documents the determination)."),
     "inputs": ["f4835_qbi_trade_or_business", "f4835_net_income_l32"], "outputs": [],
     "description": ("PER ACTIVITY. §199A treats a rental as a trade/business ONLY if it (a) rises to a §162 "
                     "trade/business, (b) is a self-rental to a commonly-controlled entity (§1.199A-1(b)(14)), or "
                     "(c) meets the Rev. Proc. 2019-38 safe harbor. Non-material-participation crop-share rent is "
                     "NOT automatically QBI — the spec does NOT auto-feed the QBI base; the preparer asserts "
                     "f4835_qbi_trade_or_business. requires_human_review. The note's [VERIFY-QBI] item, resolved "
                     "to preparer-determination (default not-QBI).")},
]

F4835_LINES: list[dict] = [
    {"line_number": "A", "description": "Did you actively participate in the operation of this farm during 2025? (§469(i))", "line_type": "input"},
    # Part I — Gross Farm Rental Income (Based on Production)
    {"line_number": "1", "description": "Income from production of livestock, produce, grains, and other crops", "line_type": "input"},
    {"line_number": "2a", "description": "Cooperative distributions (Form(s) 1099-PATR)", "line_type": "input"},
    {"line_number": "2b", "description": "Cooperative distributions — taxable amount", "line_type": "input"},
    {"line_number": "3a", "description": "Agricultural program payments", "line_type": "input"},
    {"line_number": "3b", "description": "Agricultural program payments — taxable amount", "line_type": "input"},
    {"line_number": "4a", "description": "CCC loans reported under election (§77)", "line_type": "input"},
    {"line_number": "4b", "description": "CCC loans forfeited (memo)", "line_type": "input"},
    {"line_number": "4c", "description": "CCC loans forfeited — taxable amount", "line_type": "input"},
    {"line_number": "5a", "description": "Crop insurance proceeds — amount received in 2025 (memo)", "line_type": "input"},
    {"line_number": "5b", "description": "Crop insurance proceeds — taxable amount", "line_type": "input"},
    {"line_number": "5c", "description": "Election to defer crop insurance to 2026 attached (checkbox)", "line_type": "input"},
    {"line_number": "5d", "description": "Amount deferred from 2024 (now recognized)", "line_type": "input"},
    {"line_number": "6", "description": "Other income (incl. federal/state gasoline or fuel tax credit/refund)", "line_type": "input"},
    {"line_number": "7", "description": "Gross farm rental income. Add right column of 1-6 -> Sch E line 42", "line_type": "subtotal"},
    # Part II — Expenses (Farm Rental Property)
    {"line_number": "8", "description": "Car and truck expenses (attach Form 4562)", "line_type": "input"},
    {"line_number": "9", "description": "Chemicals", "line_type": "input"},
    {"line_number": "10", "description": "Conservation expenses (≤25% gross farm income)", "line_type": "input"},
    {"line_number": "11", "description": "Custom hire (machine work)", "line_type": "input"},
    {"line_number": "12", "description": "Depreciation and section 179 expense — from Form 4562", "line_type": "calculated"},
    {"line_number": "13", "description": "Employee benefit programs other than on line 21", "line_type": "input"},
    {"line_number": "14", "description": "Feed", "line_type": "input"},
    {"line_number": "15", "description": "Fertilizers and lime", "line_type": "input"},
    {"line_number": "16", "description": "Freight and trucking", "line_type": "input"},
    {"line_number": "17", "description": "Gasoline, fuel, and oil", "line_type": "input"},
    {"line_number": "18", "description": "Insurance (other than health)", "line_type": "input"},
    {"line_number": "19a", "description": "Interest — mortgage (paid to banks, etc.)", "line_type": "input"},
    {"line_number": "19b", "description": "Interest — other", "line_type": "input"},
    {"line_number": "20", "description": "Labor hired (less employment credits)", "line_type": "input"},
    {"line_number": "21", "description": "Pension and profit-sharing plans", "line_type": "input"},
    {"line_number": "22a", "description": "Rent or lease — vehicles, machinery, and equipment", "line_type": "input"},
    {"line_number": "22b", "description": "Rent or lease — other (land, animals, etc.)", "line_type": "input"},
    {"line_number": "23", "description": "Repairs and maintenance", "line_type": "input"},
    {"line_number": "24", "description": "Seeds and plants", "line_type": "input"},
    {"line_number": "25", "description": "Storage and warehousing", "line_type": "input"},
    {"line_number": "26", "description": "Supplies", "line_type": "input"},
    {"line_number": "27", "description": "Taxes", "line_type": "input"},
    {"line_number": "28", "description": "Utilities", "line_type": "input"},
    {"line_number": "29", "description": "Veterinary, breeding, and medicine", "line_type": "input"},
    {"line_number": "30a", "description": "Other expenses (specify) — a", "line_type": "input"},
    {"line_number": "30b", "description": "Other expenses (specify) — b", "line_type": "input"},
    {"line_number": "30c", "description": "Other expenses (specify) — c", "line_type": "input"},
    {"line_number": "30d", "description": "Other expenses (specify) — d", "line_type": "input"},
    {"line_number": "30e", "description": "Other expenses (specify) — e", "line_type": "input"},
    {"line_number": "30f", "description": "Other expenses (specify) — f", "line_type": "input"},
    {"line_number": "30g", "description": "Other expenses — §263A capitalized (parentheses; '263A' to the left)", "line_type": "input"},
    {"line_number": "31", "description": "Total expenses. Add lines 8 through 30g (30g reduces)", "line_type": "subtotal"},
    {"line_number": "32", "description": "Net farm rental income/(loss). Subtract line 31 from line 7 -> Sch E line 40 (income)", "line_type": "total"},
    {"line_number": "33", "description": "Reserved for future use", "line_type": "input"},
    {"line_number": "34a", "description": "All investment is at risk", "line_type": "input"},
    {"line_number": "34b", "description": "Some investment is not at risk (Form 6198 before Form 8582)", "line_type": "input"},
    {"line_number": "34c", "description": "Deductible loss (after 6198 at-risk, 8582 passive) -> Sch E line 40", "line_type": "total"},
]

F4835_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_4835_MATPART", "title": "Materially participated — wrong form (use Schedule F)", "severity": "error",
     "condition": "f4835_material_participation is True",
     "message": ("This activity is on Form 4835, but you indicated you materially participated in the farm's "
                 "operation or management. Form 4835 is only for landowners who did NOT materially participate — "
                 "materially-participated farming (and its self-employment tax) belongs on Schedule F (Form 1040). "
                 "Move this activity to Schedule F."),
     "notes": "Form-selection guard (Ken decision). Purpose of Form: materially participated -> Schedule F."},
    {"diagnostic_id": "D_4835_SE_GUARD", "title": "SE-exclusion invariant violated — 4835 income reached the SE base", "severity": "error",
     "condition": "any Form 4835 amount (line 32 / line 34c) is included in the Schedule SE base (line 1a, line 2, or farm-optional gross farm income)",
     "message": ("Form 4835 farm rental income is NOT subject to self-employment tax (IRC §1402(a)(1); the form's "
                 "own subtitle). It must never flow to Schedule SE. This diagnostic fires if any 4835 amount is "
                 "detected in the SE base — a wiring bug. Remove it from Schedule SE."),
     "notes": "THE DEFINING INVARIANT (Ken decision). Contrast Schedule F (which DOES feed Sch SE line 1a)."},
    {"diagnostic_id": "D_4835_CCC_ELECT", "title": "CCC loans reported as income (§77 election)", "severity": "warning",
     "condition": "f4835_ccc_loans_election_4a > 0",
     "message": ("You reported Commodity Credit Corporation loan proceeds as income (line 4a, IRC §77). The amount "
                 "is included in gross farm rental income (line 7), but the §77 election itself (and its binding "
                 "effect on later years) is not managed by the software — confirm the election is properly made."),
     "notes": "Capture-flag the election; the dollar amount flows to line 7."},
    {"diagnostic_id": "D_4835_CROPINS_DEFER", "title": "Crop insurance deferral to 2026 (§451(f) election)", "severity": "warning",
     "condition": "f4835_crop_insurance_defer_election_5c is True",
     "message": ("You checked the box to defer crop insurance proceeds to 2026 (line 5c, IRC §451(f)). The deferral "
                 "election and the required statement are not generated by the software — the taxable amount on line "
                 "5b is reported as entered; prepare the deferral election manually. Deferral of any eligible "
                 "proceeds defers ALL such proceeds (incl. federal crop disaster payments)."),
     "notes": "Capture-flag the election; line 5b flows to line 7 as entered."},
    {"diagnostic_id": "D_4835_263A", "title": "§263A capitalized costs on line 30g", "severity": "warning",
     "condition": "f4835_capitalized_263a_30g != 0",
     "message": ("You entered §263A uniform-capitalization costs on line 30g (in parentheses). These reduce total "
                 "expenses on line 31 as entered; the capitalization determination (which direct/indirect costs must "
                 "be capitalized vs. deducted) is preparer-driven and not computed by the software."),
     "notes": "Capture-flag; 30g reduces line 31 per the instructions."},
    {"diagnostic_id": "D_4835_REPRO", "title": "Real estate professional — §469 passive-loss escape (preparer-asserted)", "severity": "warning",
     "condition": "f4835_real_estate_professional is True AND line 32 < 0",
     "message": ("You indicated real-estate-professional status materially participating in this activity, so the "
                 "loss is not subject to the passive activity loss limitation (Form 8582 skipped). The software does "
                 "NOT verify the real-estate-professional tests (more than 750 hours AND more than half of personal "
                 "services in real property trades/businesses) — confirm the status; the loss is entered on line 34c."),
     "notes": "RED-defer the REP determination; the loss is captured/allowed per the assertion."},
    {"diagnostic_id": "D_4835_LOSS_LIMITED", "title": "Net loss limited by at-risk (§465) and/or passive (§469)", "severity": "info",
     "condition": "line 32 < 0 AND deductible loss (line 34c) < the tentative loss",
     "message": ("This farm rental shows a net loss. Part of it is limited: the at-risk rules (Form 6198, if some "
                 "investment is not at risk) cap the loss at your amount at risk, then the passive activity loss "
                 "rules (Form 8582) limit the remainder to your passive income plus (with active participation) the "
                 "$25,000 special allowance. The unallowed amounts carry forward."),
     "notes": "Info: documents that the computed loss path (6198 then 8582) limited the loss."},
    {"diagnostic_id": "D_4835_SCHJ", "title": "Net farm rental income — Schedule J may lower tax", "severity": "info",
     "condition": "line 32 > 0",
     "message": ("This activity shows net farm rental income on line 32. Your tax may be lower if you use Schedule J "
                 "(Form 1040) farm income averaging. Consider whether Schedule J applies."),
     "notes": "Info routing (Schedule J is a separate form unit). Verified off the Purpose of Form."},
    {"diagnostic_id": "D_4835_QBI", "title": "§199A QBI is a preparer determination for farm rental", "severity": "info",
     "condition": "always (form present) — routes on f4835_qbi_trade_or_business",
     "message": ("Form 4835 farm rental income is qualified business income (§199A) ONLY if this rental rises to a "
                 "§162 trade or business, is a self-rental to a commonly-controlled entity, or meets the Rev. Proc. "
                 "2019-38 250-hour safe harbor. Non-material-participation crop-share rent is not automatically QBI. "
                 "The software does not auto-include it in the QBI base — confirm the determination and set the QBI "
                 "flag if it qualifies."),
     "notes": "Info; the [VERIFY-QBI] note item. Default not-QBI; preparer asserts. requires_human_review."},
]

F4835_SCENARIOS: list[dict] = [
    {"scenario_name": "F4835-T1 — net income, simple (income -> Sch E line 40, NOT SE)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "line_1": 50000, "line_8": 12000, "line_27": 8000,
                "f4835_material_participation": False, "f4835_active_participation_A": True, "f4835_all_at_risk_34a": True},
     "expected_outputs": {"line_7": 50000, "line_31": 20000, "line_32": 30000, "writes_sche_line_40": True, "feeds_schse": False, "D_4835_SE_GUARD": False},
     "notes": "L7=50,000; L31=12,000+8,000=20,000; L32=30,000 income -> Sch E line 40. SE-exclusion holds (feeds_schse False)."},
    {"scenario_name": "F4835-T2 — multi-line income (2b/3b/4a/4c/5b/5d) verified L7 sum", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"tax_year": 2025, "line_1": 20000, "line_2b": 3000, "line_3b": 5000, "line_4a": 4000, "line_4c": 2000,
                "line_5b": 6000, "line_5d": 1000, "line_6": 500, "line_27": 10000,
                "f4835_material_participation": False, "f4835_active_participation_A": True, "f4835_all_at_risk_34a": True},
     "expected_outputs": {"line_7": 41500, "line_32": 31500},
     "notes": "L7 = 20,000+3,000+5,000+4,000+2,000+6,000+1,000+500 = 41,500 (right-column sum; excludes 2a/3a/4b/5a). L31=10,000; L32=31,500."},
    {"scenario_name": "F4835-T3 — net loss, all at risk, active participation, MAGI<100k (full $25k allowance -> full loss)", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"tax_year": 2025, "line_1": 30000, "line_27": 50000, "f4835_material_participation": False,
                "f4835_active_participation_A": True, "f4835_all_at_risk_34a": True, "f4835_magi_for_pal": 90000},
     "expected_outputs": {"line_32": -20000, "line_34c": -20000, "f4835_suspended_pal": 0, "D_4835_LOSS_LIMITED": False},
     "notes": ("Tentative loss 20,000; all at risk (skip 6198). MAGI 90,000 < 100,000 -> special allowance = 25,000; "
               "allowed = min(20,000, 25,000) = 20,000 -> L34c = -20,000 -> Sch E line 40. Nothing suspended.")},
    {"scenario_name": "F4835-T4 — net loss, active participation, MAGI phaseout (partial allowance, remainder suspended)", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"tax_year": 2025, "line_1": 10000, "line_27": 50000, "f4835_material_participation": False,
                "f4835_active_participation_A": True, "f4835_all_at_risk_34a": True, "f4835_magi_for_pal": 130000},
     "expected_outputs": {"line_32": -40000, "line_34c": -10000, "f4835_suspended_pal": 30000, "D_4835_LOSS_LIMITED": True},
     "notes": ("Tentative loss 40,000; all at risk. MAGI 130,000 -> allowance = 25,000 - 50%*(130,000-100,000) = "
               "25,000 - 15,000 = 10,000; allowed = min(40,000, 10,000) = 10,000 -> L34c = -10,000; suspended PAL = 30,000. WALK ITEM A.")},
    {"scenario_name": "F4835-T5 — net loss, some NOT at risk (6198 before 8582)", "scenario_type": "normal", "sort_order": 5,
     "inputs": {"tax_year": 2025, "line_1": 10000, "line_27": 50000, "f4835_material_participation": False,
                "f4835_active_participation_A": True, "f4835_some_not_at_risk_34b": True, "f4835_at_risk_amount": 25000,
                "f4835_magi_for_pal": 90000},
     "expected_outputs": {"line_32": -40000, "line_34c": -25000, "f4835_suspended_pal": 0, "D_4835_LOSS_LIMITED": True},
     "notes": ("Tentative loss 40,000. STEP 1 §465 at-risk (34b): min(40,000, 25,000) = 25,000 (15,000 at-risk-"
               "suspended). STEP 2 §469 passive: MAGI 90,000 -> allowance 25,000; allowed = min(25,000, 25,000) = "
               "25,000 -> L34c = -25,000 -> Sch E line 40. Order 6198-before-8582 (verified off the face).")},
    {"scenario_name": "F4835-T6 — net loss, NO active participation (no special allowance, no passive income -> fully suspended)", "scenario_type": "normal", "sort_order": 6,
     "inputs": {"tax_year": 2025, "line_1": 5000, "line_27": 25000, "f4835_material_participation": False,
                "f4835_active_participation_A": False, "f4835_all_at_risk_34a": True, "f4835_magi_for_pal": 90000},
     "expected_outputs": {"line_32": -20000, "line_34c": 0, "f4835_suspended_pal": 20000, "D_4835_LOSS_LIMITED": True},
     "notes": ("Tentative loss 20,000; all at risk. Line A = No -> NOT eligible for the $25k special allowance; with "
               "no other passive income, allowed = 0 -> L34c = 0; entire 20,000 suspended (§469 PAL carryforward).")},
    {"scenario_name": "F4835-T7 — material participation -> D_4835_MATPART (wrong form)", "scenario_type": "normal", "sort_order": 7,
     "inputs": {"tax_year": 2025, "line_1": 60000, "line_27": 20000, "f4835_material_participation": True},
     "expected_outputs": {"D_4835_MATPART": True, "line_32": None},
     "notes": "Materially participated -> Form 4835 is wrong; route to Schedule F. Line 32 not silently computed (no silent gap)."},
    {"scenario_name": "F4835-T8 — CCC §77 election (D_4835_CCC_ELECT), amount in L7", "scenario_type": "normal", "sort_order": 8,
     "inputs": {"tax_year": 2025, "line_1": 20000, "line_4a": 15000, "line_27": 10000,
                "f4835_material_participation": False, "f4835_active_participation_A": True, "f4835_all_at_risk_34a": True},
     "expected_outputs": {"line_7": 35000, "line_32": 25000, "D_4835_CCC_ELECT": True},
     "notes": "L4a=15,000 (CCC elected) flows into L7=20,000+15,000=35,000; D_4835_CCC_ELECT fires (election preparer-managed)."},
    {"scenario_name": "F4835-T9 — crop insurance deferral election (D_4835_CROPINS_DEFER)", "scenario_type": "normal", "sort_order": 9,
     "inputs": {"tax_year": 2025, "line_1": 30000, "line_5a": 12000, "line_5b": 12000, "f4835_crop_insurance_defer_election_5c": True,
                "line_27": 15000, "f4835_material_participation": False, "f4835_active_participation_A": True, "f4835_all_at_risk_34a": True},
     "expected_outputs": {"line_7": 42000, "line_32": 27000, "D_4835_CROPINS_DEFER": True},
     "notes": "5b=12,000 taxable flows into L7=30,000+12,000=42,000; 5c election -> D_4835_CROPINS_DEFER (deferral statement manual)."},
    {"scenario_name": "F4835-T10 — §263A capitalized on 30g reduces L31 (D_4835_263A)", "scenario_type": "normal", "sort_order": 10,
     "inputs": {"tax_year": 2025, "line_1": 40000, "line_27": 12000, "line_26": 8000, "line_30g": 3000,
                "f4835_material_participation": False, "f4835_active_participation_A": True, "f4835_all_at_risk_34a": True},
     "expected_outputs": {"line_31": 17000, "line_32": 23000, "D_4835_263A": True},
     "notes": "L31 = (12,000 + 8,000) - 3,000(§263A on 30g) = 17,000; L32 = 40,000 - 17,000 = 23,000; D_4835_263A fires."},
    {"scenario_name": "F4835-T11 — SE-exclusion invariant (net income NOT in SE base)", "scenario_type": "edge_case", "sort_order": 11,
     "inputs": {"tax_year": 2025, "line_1": 80000, "line_27": 30000, "f4835_material_participation": False,
                "f4835_active_participation_A": True, "f4835_all_at_risk_34a": True},
     "expected_outputs": {"line_32": 50000, "feeds_schse_line_1a": False, "feeds_schse_line_2": False, "feeds_farm_optional_gross": False, "D_4835_SE_GUARD": False},
     "notes": "L32=50,000 income. THE INVARIANT: none of it reaches Schedule SE (line 1a/2 or the farm-optional gross farm income). §1402(a)(1)."},
    {"scenario_name": "F4835-T12 — two 4835 activities, each nets to its own Sch E line 40 contribution", "scenario_type": "normal", "sort_order": 12,
     "inputs": {"tax_year": 2025, "activities": [{"line_32": 30000}, {"line_32": -12000, "f4835_all_at_risk_34a": True,
                "f4835_active_participation_A": True, "f4835_magi_for_pal": 80000}]},
     "expected_outputs": {"sche_line_40_total": 18000},
     "notes": "PER-ACTIVITY model: activity 1 +30,000, activity 2 loss -12,000 (allowed in full: at risk + active + MAGI<100k) -> Sch E line 40 = 30,000 - 12,000 = 18,000."},
    {"scenario_name": "F4835-S3 — MeF ATS scenario 3 (income case; the tts consuming vector)", "scenario_type": "normal", "sort_order": 13,
     "inputs": {"tax_year": 2025, "line_1": 17035, "line_9": 879, "line_14": 350, "line_17": 690, "line_23": 1355,
                "line_26": 2700, "f4835_active_participation_A": True, "f4835_material_participation": False,
                "f4835_all_at_risk_34a": True},
     "expected_outputs": {"line_7": 17035, "line_31": 5974, "line_32": 11061,
                          "writes_sche_line_40": 11061, "writes_sche_line_42": 17035, "feeds_schse": False},
     "notes": ("IRS 1040 MeF ATS scenario 3 Form 4835 (fictional taxpayer, not PII). L7=17,035; L31=879+350+690+"
               "1,355+2,700=5,974; L32=17,035-5,974=11,061 income -> Sch E line 40=11,061, Sch E line 42=17,035; "
               "NOTHING to Schedule SE (in S3 the SE tax comes only from the taxpayer's separate Schedule F). This "
               "is the exact vector the tts-tax-app S3 build must reproduce.")},
]

F4835_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-4835-GROSS", "IRS_2025_4835_FORM", "primary", "Line 7 right-column list (1, 2b, 3b, 4a, 4c, 5b, 5d, 6) -> Sch E line 42"),
    ("R-4835-DEPR", "IRS_2025_4835_FORM", "primary", "Line 12 depreciation/§179 (attach Form 4562)"),
    ("R-4835-DEPR", "IRS_2025_4835_INSTR", "secondary", "Line 12 — Form 4562 / Pub 225 chapter 7"),
    ("R-4835-EXPENSES", "IRS_2025_4835_FORM", "primary", "Line 31 = add 8 through 30g (30g §263A reduces)"),
    ("R-4835-EXPENSES", "IRC_263A", "secondary", "§263A capitalized costs on 30g reduce total expenses"),
    ("R-4835-NET", "IRS_2025_4835_FORM", "primary", "Line 32 = line 7 - line 31; income -> Sch E line 40"),
    ("R-4835-SE-EXCLUSION", "IRC_1402A1", "primary", "§1402(a)(1) — rentals from real estate excluded from SE earnings"),
    ("R-4835-SE-EXCLUSION", "IRS_2025_4835_FORM", "secondary", "Form subtitle: 'Income Not Subject to Self-Employment Tax'"),
    ("R-4835-MATPART", "IRS_2025_4835_FORM", "primary", "Purpose of Form: materially participated -> use Schedule F"),
    ("R-4835-MATPART", "IRS_2025_4835_INSTR", "secondary", "Material participation definition (Pub 225 ch. 12)"),
    ("R-4835-LOSS", "IRS_2025_4835_FORM", "primary", "Line 34: 6198 (if 34b) before 8582; line 34c -> Sch E line 40"),
    ("R-4835-LOSS", "IRC_465", "primary", "§465 at-risk limitation (Form 6198)"),
    ("R-4835-LOSS", "IRC_469", "primary", "§469 / §469(i) passive limitation + $25k special allowance (Form 8582)"),
    ("R-4835-LOSS", "IRS_2025_6198_INSTR", "secondary", "Form 6198 at-risk computation (§465(b))"),
    ("R-4835-LOSS", "IRS_2025_8582_INSTR", "secondary", "Form 8582 passive limitation + special allowance phaseout"),
    ("R-4835-REPRO", "IRS_2025_4835_INSTR", "primary", "Page 3: real-estate-professional §469 escape"),
    ("R-4835-REPRO", "IRC_469", "secondary", "§469(c)(7) real-estate-professional exception"),
    ("R-4835-ELECTIONS", "IRC_77", "primary", "Line 4a CCC §77 loan-as-income election"),
    ("R-4835-ELECTIONS", "IRC_451_EF", "primary", "Line 5c §451(f) crop-insurance deferral election"),
    ("R-4835-ELECTIONS", "IRS_PUB_225", "secondary", "Pub 225 CCC / crop-insurance election narratives"),
    ("R-4835-263A", "IRC_263A", "primary", "§263A uniform capitalization on line 30g"),
    ("R-4835-263A", "IRS_2025_4835_INSTR", "secondary", "'How to report' — 30g parentheses, '263A' to the left"),
    ("R-4835-SCHJ", "IRS_2025_4835_FORM", "secondary", "Purpose of Form: net income on line 32 -> Schedule J may lower tax"),
    ("R-4835-QBI", "IRC_199A", "primary", "§199A QBI = §162 trade/business; rental only if it rises to that / self-rental / RP 2019-38 safe harbor"),
    ("R-4835-QBI", "IRS_PUB_225", "secondary", "Pub 225 QBI-for-farm-rental narrative (facts-and-circumstances)"),
]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY FORM LINKS
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_4835_FORM", "4835", "governs"),
    ("IRS_2025_4835_INSTR", "4835", "informs"),
    ("IRC_1402A1", "4835", "informs"),
    ("IRC_469", "4835", "informs"),
    ("IRC_465", "4835", "informs"),
    ("IRC_77", "4835", "informs"),
    ("IRC_451_EF", "4835", "informs"),
    ("IRC_263A", "4835", "informs"),
    ("IRC_199A", "4835", "informs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORMS ROSTER
# ═══════════════════════════════════════════════════════════════════════════

FORMS: list[dict] = [
    {"identity": F4835_IDENTITY, "facts": F4835_FACTS, "rules": F4835_RULES, "lines": F4835_LINES,
     "diagnostics": F4835_DIAGNOSTICS, "scenarios": F4835_SCENARIOS, "rule_links": F4835_RULE_LINKS},
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS  (staged for the tts-tax-app assertions build leg)
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-4835-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Form 4835 line 7 gross = the verified right-column sum",
     "description": ("Validates R-4835-GROSS. L7 = 1 + 2b + 3b + 4a + 4c + 5b + 5d + 6 (VERIFIED verbatim off the "
                     "2025 face — includes 4a AND 4c, not 4b; 5b AND 5d, not 5a/5c). Bug it catches: summing 4b/5a/5c, "
                     "or dropping 4a or 5d."),
     "definition": {"kind": "formula_check", "form": "4835",
                    "formula": "line_7 == line_1+line_2b+line_3b+line_4a+line_4c+line_5b+line_5d+line_6"},
     "sort_order": 1},
    {"assertion_id": "FA-1040-4835-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Form 4835 line 31 total expenses (30g reduces) + line 32 = line 7 - line 31",
     "description": ("Validates R-4835-EXPENSES/R-4835-NET. L31 = Σ(8..30f) - 30g(§263A); L32 = L7 - L31. Bug it "
                     "catches: adding 30g instead of subtracting it, or omitting an expense line."),
     "definition": {"kind": "formula_check", "form": "4835",
                    "formula": "line_31 == sum(line_8..line_30f) - line_30g; line_32 == line_7 - line_31"},
     "sort_order": 2},
    {"assertion_id": "FA-1040-4835-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Form 4835 net income (line 32) -> Schedule E line 40",
     "description": ("Validates R-4835-NET. Net INCOME on line 32 flows to Schedule E (Form 1040) line 40 ('Net farm "
                     "rental income or (loss) from Form 4835'). Bug it catches: routing to line 42 (that is the "
                     "gross-income reconciliation) or to Schedule 1."),
     "definition": {"kind": "flow_assertion", "form": "4835",
                    "source_line": "32", "must_write_to": ["SCHEDULE_E.40"], "condition": "line_32 > 0"},
     "sort_order": 3},
    {"assertion_id": "FA-1040-4835-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Form 4835 line 7 gross -> Schedule E line 42 (farming/fishing reconciliation)",
     "description": ("Validates R-4835-GROSS' cross-form target. The GROSS amount (line 7) — not the net — flows to "
                     "Schedule E line 42, the farming-and-fishing reconciliation memo. Bug it catches: sending the "
                     "gross to line 40 (which takes the NET), or omitting the reconciliation entirely."),
     "definition": {"kind": "flow_assertion", "form": "4835",
                    "source_line": "7", "must_write_to": ["SCHEDULE_E.42"]},
     "sort_order": 4},
    {"assertion_id": "FA-1040-4835-05", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "SE-EXCLUSION INVARIANT — no Form 4835 amount reaches the Schedule SE base",
     "description": ("Validates R-4835-SE-EXCLUSION (THE defining trait; Ken decision). No 4835 line (32 income, 34c "
                     "loss) may appear in the Schedule SE base — line 1a, line 2, OR the farm-optional gross farm "
                     "income. §1402(a)(1). Bug it catches: a copy-paste from the Schedule F wiring (whose L34 DOES "
                     "feed Sch SE line 1a) that wrongly couples 4835 to SE."),
     "definition": {"kind": "negative_flow_assertion", "form": "4835",
                    "source_lines": ["32", "34c"],
                    "must_not_write_to": ["SCHEDULE_SE.1a", "SCHEDULE_SE.2", "SCHEDULE_SE.gross_farm_income"],
                    "expect": {"se_guard_fires_if_violated": "D_4835_SE_GUARD"}},
     "sort_order": 5},
    {"assertion_id": "FA-1040-4835-06", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Form 4835 line 12 depreciation <- Form 4562 engine",
     "description": ("Validates R-4835-DEPR. Line 12 depreciation + §179 is sourced from the 4562 engine "
                     "(aggregate_depreciation flow_to=form_4835), not hand-entered. Bug it catches: the rental farm's "
                     "4562 depreciation not flowing to line 12."),
     "definition": {"kind": "flow_assertion", "form": "4835",
                    "reads_from": "FORM_4562", "target_line": "12"},
     "sort_order": 6},
    {"assertion_id": "FA-1040-4835-07", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Form 4835 loss -> Form 6198 (at-risk, if 34b) BEFORE Form 8582 (passive) -> line 34c",
     "description": ("Validates R-4835-LOSS ordering. A line-32 loss runs §465 at-risk (Form 6198) only when box 34b "
                     "is checked, THEN §469 passive (Form 8582); line 34c = the allowed remainder -> Sch E line 40. "
                     "Bug it catches: applying 8582 before 6198, or skipping 6198 when 34b is checked."),
     "definition": {"kind": "ordered_flow_assertion", "form": "4835",
                    "source_line": "32", "condition": "line_32 < 0",
                    "ordered_limiters": ["6198", "FORM_8582"],
                    "at_risk_gate": "line_34b", "result_line": "34c", "then_write_to": ["SCHEDULE_E.40"]},
     "sort_order": 7},
    {"assertion_id": "FA-1040-4835-08", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Form 4835 loss -> the correct Form 8582 bucket (active-participation special allowance vs other passive)",
     "description": ("Validates R-4835-LOSS' 8582 routing. With active participation (Line A = Yes) the 4835 farm "
                     "rental is a rental-real-estate activity eligible for the $25k special allowance -> Form 8582 "
                     "lines 1a-1d (active rental RE). Without it -> lines 2a-2d ('all other passive'; no special "
                     "allowance). Bug it catches: a Line-A-No activity getting the special allowance, or vice versa. WALK ITEM B."),
     "definition": {"kind": "flow_assertion", "form": "4835",
                    "source_line": "32",
                    "route": {"active_participation_yes": "FORM_8582.1b", "active_participation_no": "FORM_8582.2b"}},
     "sort_order": 8},
    {"assertion_id": "FA-1040-4835-09", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "Form 4835 flag/RED-defer set each leaves a diagnostic (no silent gap)",
     "description": ("Validates the 4835 flag set: material participation (D_4835_MATPART, error -> Schedule F), CCC "
                     "§77 election (D_4835_CCC_ELECT), crop-insurance deferral (D_4835_CROPINS_DEFER), §263A on 30g "
                     "(D_4835_263A), real-estate-professional escape (D_4835_REPRO). Each fires rather than silently "
                     "computing a wrong number."),
     "definition": {"kind": "gating_check", "form": "4835",
                    "blockers": ["material_participation", "ccc_election", "cropins_defer", "capitalized_263a", "real_estate_professional"],
                    "expect": {"diagnostic_fires": True}},
     "sort_order": 9},
]


# ═══════════════════════════════════════════════════════════════════════════
# Command
# ═══════════════════════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = (
        "Load the Form 4835 spec into Rule Studio (creates 4835 — farm rental "
        "income/expenses; net -> Sch E line 40; NOT SE income; full loss path via the "
        "existing 6198/8582 specs). Refuses to seed until Ken sets READY_TO_SEED=True."
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()

        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad 4835 spec (Farm Rental Income and Expenses)\n"))

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
        """Refuse to write anything until Ken has reviewed AND flipped READY_TO_SEED."""
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
                "\n"
                "REFUSING TO SEED 4835: not cleared to seed.\n"
                "\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True to proceed)\n"
                f"Empty spec sections:\n  {still_empty}\n"
                "\n"
                "This spec encodes tax law (Form 4835 farm rental; §1402(a)(1) SE exclusion;\n"
                "the §465-then-§469 loss path). Ken reviews the packet (the verified line-7\n"
                "sum, the line-42-vs-line-40 flow correction, the computed 8582/6198 loss\n"
                "numbers, the SE-exclusion invariant, the 3 walk items), then sets\n"
                "READY_TO_SEED = True. Idempotent via update_or_create — safe to re-run."
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Authority
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
            else:
                self.stdout.write(self.style.WARNING(
                    f"  referenced source {code} NOT found — its rule/form links will be skipped"
                ))
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

    def _upsert_rules(self, form, rules_data) -> dict[str, FormRule]:
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
            source = sources.get(source_code) or AuthoritySource.objects.filter(
                source_code=source_code,
            ).first()
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

    # ─────────────────────────────────────────────────────────────────────────
    # Report
    # ─────────────────────────────────────────────────────────────────────────

    def _report_totals(self):
        def _safe(text):
            return text.encode("ascii", errors="replace").decode("ascii")

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("DATABASE TOTALS (after load_1040_form_4835)")
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

        for fn in ("4835",):
            all_rules = FormRule.objects.filter(tax_form__form_number=fn)
            uncited = [r for r in all_rules if not r.authority_links.exists()]
            if uncited:
                self.stdout.write(self.style.WARNING(
                    f"\n{fn} rules with ZERO authority links: {len(uncited)}"
                ))
                for r in uncited[:20]:
                    self.stdout.write(_safe(f"  {r.rule_id}: {r.title}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"{fn}: all rules have authority links."))
