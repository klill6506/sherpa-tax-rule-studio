"""Load the Schedule F spec + amend Schedule SE (farm optional method) — 1040 farm.

Creates ONE new TaxForm and AMENDS one existing form (one idempotent command,
the load_1040_schedule_k1.py / load_1040_schedule_c.py precedent):

  - SCHEDULE_F (Profit or Loss From Farming) — NEW. The farm sole-proprietor P&L,
    CASH METHOD v1: Part I income (lines 1a-9) + Part II expenses (lines 10-33) ->
    line 34 net farm profit/(loss). PER FARM (multiple Schedule F per return; FK
    model — the Schedule C multi-business precedent). Net profit (line 34) feeds
    Schedule 1 line 6 (sum all farms) AND Schedule SE line 1a (sum per proprietor);
    the CRP portion of line 4b feeds Schedule SE line 1b (negative, the §1402(a)(1)
    exclusion). Line 14 depreciation reuses the mature 4562 engine; farm net feeds
    Form 8995 QBI (§199A). Accrual Part III (lines 37-50), the CCC/crop-insurance/
    weather deferral ELECTIONS, passive-loss (§469 / Form 8582), at-risk (Form
    6198), and §461(l) excess-farm-loss limits are RED-defer (no silent gap).

  - SCHEDULE_SE (Self-Employment Tax) — AMENDED additively. Topic 8 authored Part I
    standard method only and RED-deferred ALL of Part II. Ken (2026-06-21) put the
    FARM OPTIONAL METHOD in scope: this loader adds the Part II farm optional method
    (lines 14/15 -> line 4b), flips line 1a to a COMPUTED feeder from Schedule F
    line 34, and NARROWS R-SE-OPTIONAL / D_SE_003 so only the farm optional method
    is supported — the nonfarm optional method (lines 16/17), church-employee income
    (line 5), and Form 4361 clergy keep firing RED. Schedule J farm income averaging
    is its OWN form unit (the immediately-following spec) — NOT in this loader.

Session 2026-06-21: spec-first probe found NO RS Schedule F spec (SCHEDULE_F /
1040_SCHF / F / SCHF all 404; RS up, real 404s). Authored by transcription from
primary sources verified the same day (pymupdf dumps + the SE Part II text):

  - 2025 Schedule F (f1040sf.pdf, Attachment Seq 14) — Parts I-IV, server/.scratch/
    f1040sf_dump.txt (tts-tax-app). The line-9 right-column list verified verbatim.
  - 2025 Instructions for Schedule F (i1040sf).
  - IRS Pub 225 (Farmer's Tax Guide) — substantive farm income/expense definitions,
    §77 CCC election, §451(e)/(f) deferrals, the farm optional SE method.
  - 2025 Schedule SE (f1040sse.pdf) Part II — farm optional method (lines 14/15),
    server/.scratch/f1040sse_dump.txt. Constants verified verbatim off the face.
  - IRC §77, §451(e)/(f), §1402(a)(1).

Consolidated brief: tts-tax-app server/specs/_schedule_f_source_brief.md.

TOPIC SCOPE (Ken-locked 2026-06-21; STATUS.md "Schedule F KICKOFF"):
  IN: cash-method Part I income (1a-9) + Part II expenses (10-33) -> line 34 net;
      PER FARM (multi-Schedule-F, the ScheduleC FK precedent); line 34 -> Sch 1 L6 +
      per-proprietor Sch SE L1a; CRP -> SE L1b; line-14 depreciation via the 4562
      engine; farm net -> Form 8995 QBI; the FARM OPTIONAL SE METHOD (Sch SE Part II).
  OUT / RED-defer (no silent gap, never silently computed; each -> a D_SF_*/D_SE_*):
      accrual method (line C = Accrual / any Part III value); CCC loan-as-income §77
      election (line 5a — capture the $, flag the election); crop-insurance §451(f)
      deferral election (line 6c); weather-related livestock-sale §451(e) deferral;
      non-material-participation passive farm loss (line E = No, loss -> Form 8582);
      at-risk (line 36b -> Form 6198); §461(l) excess farm loss. Schedule J farm
      income averaging (separate form unit). The NONFARM optional SE method, church-
      employee SE income, and Form 4361 clergy (Schedule SE — stay RED-deferred).

YEAR-KEYED CONSTANTS (target-year policy: TY2026 product target, TY2025 verification
bed; verify each year independently):
  - Farm optional SE method amounts are SSA-INDEXED annually (NOT in RP 2025-32):
    2025 max optional income $7,240 (Sch SE line 14); eligibility gross-farm-income
    ceiling $10,860 / net-farm-profit floor $7,840. 2026 amounts are UNPUBLISHED
    (the 2026 Schedule SE is not yet released). v1 supports farm optional for 2025;
    a 2026 farm-optional election fires RED (D_SE_FARMOPT_2026) with a standing
    obligation to re-pin when the 2026 Sch SE publishes (the Tax-Table-interim
    precedent). WALK ITEM A.
  - STATUTORY / NON-INDEXED: the optional-method ⅔ fraction; the SE 92.35/12.4/2.9/50
    factors + $400 floor (already in the SCHEDULE_SE spec).

requires_human_review WALK ITEMS (flagged for Ken's review walk):
  A. 2026 farm-optional SE constants unpublished -> 2025 supported, 2026 RED + re-pin.
  B. Schedule J bundle-vs-fast-follow sequencing (the immediately-following unit).
  C. Pub 225 substantive definitions are narrative (requires_human_review=True); the
     line MATH is form-gated (verified vs the PDF face). Confirm the §77 / §451(e)/(f)
     RED-defer treatment (capture income, flag the election manual) matches intent.
  D. QBI farm reduction allocation when a proprietor has BOTH a Schedule C and a
     Schedule F (pro-rata by net SE earnings, the Topic 8 multi-business convention).

Safety guard
------------
`READY_TO_SEED = False`. Content is authored; Ken reviews the packet (the verified
line-9/line-33/line-34 formulas, the cross-form flow map, the farm-optional 2025
constants + the 2026 gap, the RED-defer enumeration), flips the sentinel, then we
seed. Until then the command refuses to write to the DB. Idempotent via
update_or_create — safe to re-run after edits.

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
# line formulas, the cross-form flow map, the farm-optional 2025 constants + the
# 2026 gap, the 4 requires_human_review walk items, the RED-defer enumeration).
# Until then the command refuses to write to the DB (zero writes while False).
#
# FLIPPED 2026-06-21 — Ken APPROVED the review walk in-session ("Approve & seed"):
# the verified line-9 right-column sum + line-33/34 formulas, the cross-form flow map
# (L34 -> Sch 1 L6 + Sch SE L1a, CRP -> SE 1b, depreciation <- 4562, farm net -> 8995
# QBI), the farm-optional 2025 constants ($7,240 / $10,860 / $7,840) + the 2026 RED,
# and walk items A (2026 RED + re-pin) / C (§77 §451 capture-income-flag-election) /
# D (pro-rata QBI). Schedule J = fast-follow (its own form unit).
# ═══════════════════════════════════════════════════════════════════════════
READY_TO_SEED = True


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1040"]


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS (brief §3 — every value cited; never training memory)
# ═══════════════════════════════════════════════════════════════════════════

# Schedule SE farm OPTIONAL method — SSA-INDEXED annually (verified off the 2025
# Schedule SE Part II face). 2026 UNPUBLISHED -> 2026 election fires RED.
FARM_OPT_MAX_INCOME: dict[int, int] = {2025: 7240}      # Sch SE line 14 ("Maximum income for optional methods")
FARM_OPT_GROSS_CEILING: dict[int, int] = {2025: 10860}  # eligibility: gross farm income not more than
FARM_OPT_PROFIT_FLOOR: dict[int, int] = {2025: 7840}    # eligibility: OR net farm profits less than
FARM_OPT_FRACTION = "2/3"                               # statutory (non-indexed): two-thirds of gross farm income


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY TOPICS
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("schedule_f_farming", "Schedule F — farm profit/loss (cash method), income (Part I) + expenses (Part II) -> Sch 1 L6 + Sch SE L1a"),
    ("farm_optional_se", "Schedule SE Part II — farm optional method (gross farm income x 2/3, capped) -> line 4b"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_SCHEDSE_FORM",  # Sch SE line 1a (farm) + Part II farm optional method (Topic 8 source)
    "IRS_2025_1040_FORM",     # 1040 line 8 (Schedule 1 total)
    "IRS_2025_1040_INSTR",    # Schedule 1 line 6 "Farm income or (loss)"
]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY SOURCES (with embedded excerpts) — CREATE
# Transcribed 2026-06-21 from the fetched PDFs (tts-tax-app server/.scratch/).
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_SCHEDF_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Schedule F (Form 1040) — Profit or Loss From Farming",
        "citation": "Schedule F (Form 1040) 2025; f1040sf.pdf; Attachment Sequence No. 14; Cat. No. 11346H",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f1040sf.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": "Parts I-IV transcribed 2026-06-21 (tts-tax-app server/.scratch/f1040sf_dump.txt). Real face; PER FARM.",
        "topics": ["schedule_f_farming"],
        "excerpts": [
            {
                "excerpt_label": "Header + Part I Farm Income — Cash Method (lines 1a-9, verbatim)",
                "location_reference": "Schedule F (2025), header A-G + Part I",
                "excerpt_text": (
                    "C Accounting method: Cash / Accrual. E Did you 'materially participate' in the "
                    "operation of this business during 2025? If 'No,' see instructions for limit on "
                    "passive losses. 1a Sales of purchased livestock and other resale items. 1b Cost "
                    "or other basis of purchased livestock or other items reported on line 1a. 1c "
                    "Subtract line 1b from line 1a. 2 Sales of livestock, produce, grains, and other "
                    "products you raised. 3a Cooperative distributions (Form(s) 1099-PATR); 3b Taxable "
                    "amount. 4a Agricultural program payments; 4b Taxable amount. 5a Commodity Credit "
                    "Corporation (CCC) loans reported under election; 5b CCC loans forfeited; 5c Taxable "
                    "amount. 6a Crop insurance proceeds and federal crop disaster payments — Amount "
                    "received in 2025; 6b Taxable amount; 6c If election to defer to 2026 is attached, "
                    "check here; 6d Amount deferred from 2024. 7 Custom hire (machine work) income. 8 "
                    "Other income, including federal and state gasoline or fuel tax credit or refund. 9 "
                    "Gross income. Add amounts in the right column (lines 1c, 2, 3b, 4b, 5a, 5c, 6b, 6d, "
                    "7, and 8). If you use the accrual method, enter the amount from Part III, line 50."
                ),
                "summary_text": (
                    "L1c = L1a - L1b. L9 (gross income) = 1c + 2 + 3b + 4b + 5a + 5c + 6b + 6d + 7 + 8 "
                    "(VERIFIED verbatim — includes BOTH 5a and 5c, not 5b). Line C cash/accrual drives "
                    "the accrual RED-defer; line E material participation drives the §469 passive RED-defer. "
                    "CCC §77 (5a) / crop-insurance §451(f) deferral (6c) = capture the $, RED-defer the election."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part II Farm Expenses + net profit (lines 10-36, verbatim)",
                "location_reference": "Schedule F (2025), Part II",
                "excerpt_text": (
                    "10 Car and truck expenses (also attach Form 4562). 11 Chemicals. 12 Conservation "
                    "expenses. 13 Custom hire (machine work). 14 Depreciation and section 179 expense. 15 "
                    "Employee benefit programs other than on line 23. 16 Feed. 17 Fertilizers and lime. 18 "
                    "Freight and trucking. 19 Gasoline, fuel, and oil. 20 Insurance (other than health). 21a "
                    "Interest — Mortgage (paid to banks, etc.); 21b Other. 22 Labor hired (less employment "
                    "credits). 23 Pension and profit-sharing plans. 24a Rent or lease — Vehicles, machinery, "
                    "equipment; 24b Other (land, animals, etc.). 25 Repairs and maintenance. 26 Seeds and "
                    "plants. 27 Storage and warehousing. 28 Supplies. 29 Taxes. 30 Utilities. 31 Veterinary, "
                    "breeding, and medicine. 32a-f Other expenses (specify). 33 Total expenses. Add lines 10 "
                    "through 32f. 34 Net farm profit or (loss). Subtract line 33 from line 9. 35 Reserved for "
                    "future use. 36 Check the box that describes your investment in this activity: a All "
                    "investment is at risk; b Some investment is not at risk."
                ),
                "summary_text": (
                    "L33 = sum(10..32f) [10,11,12,13,14,15,16,17,18,19,20,21a,21b,22,23,24a,24b,25,26,27,"
                    "28,29,30,31,32a-f]. L34 = L9 - L33 -> Sch 1 L6 + Sch SE L1a. NO home-office line (unlike "
                    "Sch C). L14 depreciation/§179 <- Form 4562 engine. L36b -> Form 6198 (RED-defer)."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part III Farm Income — Accrual Method (lines 37-50, verbatim) — RED-defer",
                "location_reference": "Schedule F (2025), Part III (page 2)",
                "excerpt_text": (
                    "37 Sales of livestock, produce, grains, and other products. 38a Cooperative distributions; "
                    "38b Taxable amount. 39a Agricultural program payments; 39b Taxable amount. 40a CCC loans "
                    "reported under election; 40b CCC loans forfeited; 40c Taxable amount. 41 Crop insurance "
                    "proceeds. 42 Custom hire (machine work) income. 43 Other income. 44 Add amounts in the "
                    "right column for lines 37 through 43 (lines 37, 38b, 39b, 40a, 40c, 41, 42, and 43). 45 "
                    "Inventory of livestock, produce, grains, and other products at beginning of the year. 46 "
                    "Cost of livestock, produce, grains, and other products purchased during the year. 47 Add "
                    "lines 45 and 46. 48 Inventory at end of year. 49 Cost of products sold. Subtract line 48 "
                    "from line 47. 50 Gross income. Subtract line 49 from line 44. Enter here and on Part I, line 9."
                ),
                "summary_text": (
                    "Accrual method = RED-defer in v1 (cash only). L44 = 37+38b+39b+40a+40c+41+42+43; "
                    "L47 = 45+46; L49 = 47-48; L50 = 44-49 -> Part I line 9. Lines seeded for render-skip only."
                ),
                "is_key_excerpt": False,
            },
        ],
    },
    {
        "source_code": "IRS_2025_SCHEDF_INSTR",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Schedule F (Form 1040)",
        "citation": "i1040sf (2025)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i1040sf.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": False,
        "trust_score": 9.00,
        "requires_human_review": False,
        "notes": "Line-9 right-column list, the at-risk routing, the passive-loss caution, the where-to-report cross-refs.",
        "topics": ["schedule_f_farming"],
        "excerpts": [
            {
                "excerpt_label": "Where to report + at-risk + passive loss (line 34/36 / line E, verbatim)",
                "location_reference": "i1040sf (2025), 'Where To Report' / lines 34, 36, E",
                "excerpt_text": (
                    "If you have a net profit on line 34, enter it on Schedule 1 (Form 1040), line 6, and on "
                    "Schedule SE, line 1a. If you have a net loss, the amount of loss you can deduct may be "
                    "limited by the at-risk rules (line 36 / Form 6198), the passive activity loss rules (if "
                    "you did not materially participate — line E 'No' — see Form 8582), and the excess business "
                    "loss limitation (§461(l) / Form 461). Conservation Reserve Program (CRP) payments are "
                    "included on line 4b; if you are receiving social security retirement or disability "
                    "benefits, CRP payments are excluded from self-employment tax (entered as a negative on "
                    "Schedule SE, line 1b)."
                ),
                "summary_text": (
                    "L34 profit -> Sch 1 L6 + Sch SE L1a. Loss limits: at-risk (Form 6198, line 36b), "
                    "passive (Form 8582, line E 'No'), §461(l) (Form 461) — all RED-defer. CRP (in line 4b) "
                    "-> Sch SE L1b negative (§1402(a)(1))."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_PUB_225",
        "source_type": "official_publication",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2024,
        "tax_year_end": 2025,
        "title": "IRS Publication 225 — Farmer's Tax Guide",
        "citation": "IRS Pub 225 (2024 ed.; 2025 ed. pending)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/p225.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 9.00,
        "requires_human_review": True,
        "notes": (
            "WALK ITEM C: substantive farm income/expense definitions are NARRATIVE; the line MATH is "
            "form-gated (verified vs the PDF face). The §77 CCC election + §451(e)/(f) deferrals + the "
            "farm optional SE method are the judgment items. requires_human_review=True."
        ),
        "topics": ["schedule_f_farming", "farm_optional_se"],
        "excerpts": [
            {
                "excerpt_label": "CCC loans (§77 election) + crop-insurance/weather deferrals + farm optional SE (narrative)",
                "location_reference": "Pub 225, 'Commodity Credit Loans' / 'Crop Insurance' / 'Optional Method'",
                "excerpt_text": (
                    "Commodity Credit Corporation loans: generally a CCC loan is not income; however, you may "
                    "ELECT to treat the loan proceeds as income in the year received (IRC §77). Once made, the "
                    "election applies to all later years unless the IRS approves a change. Crop insurance and "
                    "disaster payments: a cash-method farmer who receives crop insurance proceeds in the year "
                    "of damage may ELECT to defer reporting to the following year if the income from the crops "
                    "would normally have been reported in the following year (IRC §451(f)). Weather-related "
                    "sales of livestock: you may ELECT to postpone reporting the gain from the additional "
                    "animals sold because of weather-related conditions (IRC §451(e)). Optional method: a "
                    "farmer with low net profit or a loss may use the farm optional method to figure net "
                    "earnings from self-employment (to obtain Social Security coverage)."
                ),
                "summary_text": (
                    "§77 CCC election, §451(f) crop-insurance deferral, §451(e) weather livestock deferral = "
                    "ELECTIONS (RED-defer the election machinery; capture the dollar amounts where they land on "
                    "the face). Farm optional SE method per Pub 225 + the Sch SE Part II face."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_77",
        "source_type": "statute",
        "source_rank": "primary_authority",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2026,
        "title": "IRC §77 — Commodity Credit Corporation loans (income election)",
        "citation": "26 U.S.C. §77",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/77",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": "Authority for the Schedule F line 5a CCC-loan-as-income election (RED-defer the election).",
        "topics": ["schedule_f_farming"],
        "excerpts": [
            {
                "excerpt_label": "§77(a) election to treat CCC loans as income (verbatim)",
                "location_reference": "26 U.S.C. §77(a)",
                "excerpt_text": (
                    "Amounts received as loans from the Commodity Credit Corporation shall, at the election of "
                    "the taxpayer, be considered as income and shall be included in gross income for the taxable "
                    "year in which received."
                ),
                "summary_text": "Sch F line 5a = CCC loans elected as income. v1 captures the amount (-> line 9); the election is RED-defer.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_451_EF",
        "source_type": "statute",
        "source_rank": "primary_authority",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2026,
        "title": "IRC §451(e)/(f) — weather-related livestock sales / crop-insurance deferral",
        "citation": "26 U.S.C. §451(e), §451(f)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/451",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": "Authority for the Schedule F line 6c crop-insurance deferral + the weather-related livestock-sale deferral (RED-defer the elections).",
        "topics": ["schedule_f_farming"],
        "excerpts": [
            {
                "excerpt_label": "§451(e)/(f) deferral elections (summary)",
                "location_reference": "26 U.S.C. §451(e), §451(f)",
                "excerpt_text": (
                    "§451(e): a taxpayer whose principal trade or business is farming and who sells or exchanges "
                    "livestock in excess of the number that would normally be sold because of drought, flood, or "
                    "other weather-related conditions may ELECT to include the gain in the following taxable year. "
                    "§451(f): a cash-method farmer who receives insurance proceeds as a result of destruction or "
                    "damage to crops may ELECT to include the proceeds in income for the taxable year following "
                    "the taxable year of the destruction or damage."
                ),
                "summary_text": "Sch F line 6c crop-insurance deferral (§451(f)) + weather livestock deferral (§451(e)). v1 captures the income; the elections are RED-defer.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_1402A1",
        "source_type": "statute",
        "source_rank": "primary_authority",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2026,
        "title": "IRC §1402(a)(1) — CRP rental payments excluded from SE for SS retirees",
        "citation": "26 U.S.C. §1402(a)(1)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/1402",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": "Authority for the CRP -> Schedule SE line 1b (negative) exclusion for SS retirement/disability recipients.",
        "topics": ["schedule_f_farming"],
        "excerpts": [
            {
                "excerpt_label": "§1402(a)(1) CRP exclusion (summary)",
                "location_reference": "26 U.S.C. §1402(a)(1)",
                "excerpt_text": (
                    "There shall be excluded from net earnings from self-employment payments under the "
                    "Conservation Reserve Program (CRP) to an individual receiving social security benefits for "
                    "old-age, survivors, or disability insurance."
                ),
                "summary_text": "CRP payments (in Sch F line 4b) -> Sch SE line 1b negative for SS retirement/disability recipients.",
                "is_key_excerpt": True,
            },
        ],
    },
]


# No new excerpts on existing sources (Schedule SE Part II text lives in the
# existing IRS_2025_SCHEDSE_FORM source already; the farm-optional rule cites it).
NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []


# ═══════════════════════════════════════════════════════════════════════════
# FORM 1 — SCHEDULE_F (Profit or Loss From Farming) — NEW
# ═══════════════════════════════════════════════════════════════════════════

SCHEDF_IDENTITY = {
    "form_number": "SCHEDULE_F",
    "form_title": "Schedule F (Form 1040) — Profit or Loss From Farming (TY2025)",
    "notes": (
        "1040 farm unit (cash-method v1). Real IRS face, PER FARM (multiple Schedule "
        "F per return; FK model — the Schedule C precedent). Part I income (lines "
        "1a-9) + Part II expenses (lines 10-33) -> line 34 net farm profit/(loss). "
        "Net profit -> Schedule 1 line 6 (sum all farms) AND Schedule SE line 1a "
        "(sum per proprietor); CRP portion of line 4b -> Schedule SE line 1b "
        "(negative, §1402(a)(1)). Line 14 depreciation reuses the 4562 engine; farm "
        "net -> Form 8995 QBI. Accrual Part III (37-50), the CCC §77 / crop-insurance "
        "§451(f) / weather §451(e) deferral ELECTIONS, passive loss (§469 / Form "
        "8582), at-risk (Form 6198), and §461(l) excess farm loss are RED-defer (no "
        "silent gap)."
    ),
}

SCHEDF_FACTS: list[dict] = [
    # ── Header / identity (metadata; e-file structured fields) ──
    {"fact_key": "sf_proprietor", "label": "Proprietor (taxpayer or spouse) — which person owns this Schedule F",
     "data_type": "string", "sort_order": 1,
     "notes": "PER FARM. taxpayer|spouse. SE aggregates per proprietor; each farm its own Schedule F."},
    {"fact_key": "sf_principal_activity", "label": "Line A — Principal crop or activity", "data_type": "string", "sort_order": 2,
     "notes": "PER FARM. Metadata."},
    {"fact_key": "sf_activity_code", "label": "Line B — Principal agricultural activity code (Part IV, NAICS 6-digit)", "data_type": "string", "sort_order": 3,
     "notes": "PER FARM. Metadata (e-file structured)."},
    {"fact_key": "sf_accounting_method", "label": "Line C — Accounting method (cash|accrual)", "data_type": "string", "sort_order": 4,
     "notes": "PER FARM. cash|accrual. accrual -> D_SF_ACCRUAL RED-defer (v1 cash only)."},
    {"fact_key": "sf_ein", "label": "Line D — Employer ID number (EIN), if any", "data_type": "string", "sort_order": 5,
     "notes": "PER FARM. Format NN-NNNNNNN or blank (MeF rule)."},
    {"fact_key": "sf_material_participation", "label": "Line E — Did you materially participate in 2025? (Y/N)", "data_type": "boolean", "sort_order": 6,
     "notes": "PER FARM. False + net loss -> D_SF_PASSIVE (§469 passive loss -> Form 8582; RED-defer)."},
    {"fact_key": "sf_payments_require_1099", "label": "Line F — Did you make payments requiring Form 1099? (Y/N)", "data_type": "boolean", "sort_order": 7,
     "notes": "PER FARM. Metadata."},
    {"fact_key": "sf_filed_required_1099", "label": "Line G — Did/will you file the required Form(s) 1099? (Y/N)", "data_type": "boolean", "sort_order": 8,
     "notes": "PER FARM. Metadata."},
    # ── Part I income inputs ──
    {"fact_key": "sf_purchased_livestock_sales_1a", "label": "Line 1a — Sales of purchased livestock and other resale items", "data_type": "decimal", "default_value": "0", "sort_order": 10, "notes": "PER FARM."},
    {"fact_key": "sf_purchased_livestock_basis_1b", "label": "Line 1b — Cost or other basis of line 1a items", "data_type": "decimal", "default_value": "0", "sort_order": 11, "notes": "PER FARM. L1c = L1a - L1b."},
    {"fact_key": "sf_raised_products_sales_2", "label": "Line 2 — Sales of livestock, produce, grains, products you raised", "data_type": "decimal", "default_value": "0", "sort_order": 12, "notes": "PER FARM."},
    {"fact_key": "sf_coop_distributions_3a", "label": "Line 3a — Cooperative distributions (Form 1099-PATR, gross)", "data_type": "decimal", "default_value": "0", "sort_order": 13, "notes": "PER FARM. 3a gross; 3b taxable feeds line 9."},
    {"fact_key": "sf_coop_distributions_taxable_3b", "label": "Line 3b — Cooperative distributions, taxable amount", "data_type": "decimal", "default_value": "0", "sort_order": 14, "notes": "PER FARM. Into line 9."},
    {"fact_key": "sf_ag_program_payments_4a", "label": "Line 4a — Agricultural program payments (gross)", "data_type": "decimal", "default_value": "0", "sort_order": 15, "notes": "PER FARM. 4a gross; 4b taxable feeds line 9."},
    {"fact_key": "sf_ag_program_payments_taxable_4b", "label": "Line 4b — Agricultural program payments, taxable amount", "data_type": "decimal", "default_value": "0", "sort_order": 16, "notes": "PER FARM. Into line 9. CRP portion (sf_crp_payments) routes to Sch SE line 1b."},
    {"fact_key": "sf_ccc_loans_election_5a", "label": "Line 5a — CCC loans reported under election (§77)", "data_type": "decimal", "default_value": "0", "sort_order": 17, "notes": "PER FARM. §77 election -> D_SF_CCC_ELECTION (RED-defer the election); amount STILL flows into line 9."},
    {"fact_key": "sf_ccc_loans_forfeited_5b", "label": "Line 5b — CCC loans forfeited (memo)", "data_type": "decimal", "default_value": "0", "sort_order": 18, "notes": "PER FARM. Memo; NOT in line 9 (5c is)."},
    {"fact_key": "sf_ccc_loans_taxable_5c", "label": "Line 5c — CCC loans forfeited, taxable amount", "data_type": "decimal", "default_value": "0", "sort_order": 19, "notes": "PER FARM. Into line 9."},
    {"fact_key": "sf_crop_insurance_received_6a", "label": "Line 6a — Crop insurance proceeds received in 2025", "data_type": "decimal", "default_value": "0", "sort_order": 20, "notes": "PER FARM. 6a received; 6b taxable feeds line 9."},
    {"fact_key": "sf_crop_insurance_taxable_6b", "label": "Line 6b — Crop insurance proceeds, taxable amount", "data_type": "decimal", "default_value": "0", "sort_order": 21, "notes": "PER FARM. Into line 9."},
    {"fact_key": "sf_crop_insurance_defer_election_6c", "label": "Line 6c — Election to defer crop insurance to 2026 attached (checkbox)", "data_type": "boolean", "sort_order": 22, "notes": "PER FARM. §451(f) deferral election -> D_SF_CROPINS_DEFER (RED-defer the election)."},
    {"fact_key": "sf_crop_insurance_deferred_prior_6d", "label": "Line 6d — Amount deferred from 2024 (now recognized)", "data_type": "decimal", "default_value": "0", "sort_order": 23, "notes": "PER FARM. Prior-year deferral now taxable; into line 9."},
    {"fact_key": "sf_custom_hire_income_7", "label": "Line 7 — Custom hire (machine work) income", "data_type": "decimal", "default_value": "0", "sort_order": 24, "notes": "PER FARM. Into line 9."},
    {"fact_key": "sf_other_income_8", "label": "Line 8 — Other income (incl. fuel tax credit/refund)", "data_type": "decimal", "default_value": "0", "sort_order": 25, "notes": "PER FARM. Into line 9."},
    {"fact_key": "sf_crp_payments", "label": "CRP portion of line 4b (for Schedule SE line 1b exclusion)", "data_type": "decimal", "default_value": "0", "sort_order": 26, "notes": "PER FARM. CRP rental within line 4b; routes to Sch SE line 1b (negative) for SS retirement/disability recipients (§1402(a)(1))."},
    {"fact_key": "sf_weather_deferral_elected", "label": "Weather-related livestock-sale deferral elected (§451(e))", "data_type": "boolean", "sort_order": 27, "notes": "PER FARM. -> D_SF_WEATHER_DEFER (RED-defer the election); the sale income is captured normally."},
    # ── Part II at-risk ──
    {"fact_key": "sf_all_at_risk_36a", "label": "Line 36a — All investment is at risk", "data_type": "boolean", "sort_order": 30, "notes": "PER FARM. Loss allowed (v1 assumes all at risk)."},
    {"fact_key": "sf_some_not_at_risk_36b", "label": "Line 36b — Some investment is not at risk (Form 6198)", "data_type": "boolean", "sort_order": 31, "notes": "PER FARM. Loss + 36b -> D_SF_ATRISK (Form 6198 RED-defer)."},
    # ── Outputs (traceability) ──
    {"fact_key": "sf_gross_income_l9", "label": "Line 9 — gross income (output)", "data_type": "decimal", "sort_order": 40, "notes": "OUTPUT. = 1c+2+3b+4b+5a+5c+6b+6d+7+8."},
    {"fact_key": "sf_total_expenses_l33", "label": "Line 33 — total expenses (output)", "data_type": "decimal", "sort_order": 41, "notes": "OUTPUT. = sum(10..32f)."},
    {"fact_key": "sf_net_farm_profit_l34", "label": "Line 34 — net farm profit/(loss) (output -> Sch 1 L6 + Sch SE L1a)", "data_type": "decimal", "sort_order": 42, "notes": "OUTPUT. = L9 - L33. PER FARM; summed to Sch 1 L6 and per-proprietor Sch SE L1a."},
]

SCHEDF_RULES: list[dict] = [
    {"rule_id": "R-SF-L1C", "title": "Line 1c — purchased-livestock resale margin", "rule_type": "calculation", "precedence": 1, "sort_order": 1,
     "formula": "L1c = L1a - L1b.",
     "inputs": ["sf_purchased_livestock_sales_1a", "sf_purchased_livestock_basis_1b"], "outputs": ["1c"],
     "description": "PER FARM. Resale items: sales less cost/basis."},
    {"rule_id": "R-SF-GROSS", "title": "Line 9 — gross farm income (cash method)", "rule_type": "calculation", "precedence": 2, "sort_order": 2,
     "formula": "L9 = L1c + L2 + L3b + L4b + L5a + L5c + L6b + L6d + L7 + L8.",
     "inputs": [], "outputs": ["9"],
     "description": ("PER FARM. VERIFIED verbatim against the 2025 face — the right-column list is "
                     "(1c, 2, 3b, 4b, 5a, 5c, 6b, 6d, 7, 8): includes BOTH 5a (CCC elected) and 5c (CCC "
                     "forfeiture taxable), NOT 5b. Accrual returns instead pull line 50 — RED-defer (D_SF_ACCRUAL).")},
    {"rule_id": "R-SF-DEPR", "title": "Line 14 — depreciation and §179 (4562 engine reuse)", "rule_type": "routing", "precedence": 3, "sort_order": 3,
     "formula": "L14 = depreciation + §179 from the 4562 engine for this farm's assets (carried/YELLOW).",
     "inputs": [], "outputs": ["14"],
     "description": ("PER FARM. Reuse depreciation_engine.py (aggregate_depreciation flow_to=schedule_f — the "
                     "Schedule C line-13 precedent). Farm assets attach to the Schedule F. Build-leg wiring.")},
    {"rule_id": "R-SF-EXPENSES", "title": "Line 33 — total farm expenses", "rule_type": "calculation", "precedence": 4, "sort_order": 4,
     "formula": "L33 = sum(L10, L11, L12, L13, L14, L15, L16, L17, L18, L19, L20, L21a, L21b, L22, L23, L24a, L24b, L25, L26, L27, L28, L29, L30, L31, L32a, L32b, L32c, L32d, L32e, L32f).",
     "inputs": [], "outputs": ["33"],
     "description": "PER FARM. Add lines 10 through 32f. Schedule F has NO separate home-office line (unlike Schedule C line 30)."},
    {"rule_id": "R-SF-NETPROFIT", "title": "Line 34 — net farm profit/(loss) -> Sch 1 L6 + Sch SE L1a", "rule_type": "calculation", "precedence": 5, "sort_order": 5,
     "formula": "L34 = L9 - L33 -> sf_net_farm_profit_l34. Profit -> Schedule 1 line 6 (sum all farms) AND Schedule SE line 1a (sum per proprietor). CRP (sf_crp_payments) -> Schedule SE line 1b (negative).",
     "inputs": [], "outputs": ["34"],
     "description": ("PER FARM. The topic's primary cross-form output. Schedule 1 line 6 = SUM of all farms' "
                     "L34 (flips L6 from direct-entry to computed, the Schedule C line-3 precedent); Schedule SE "
                     "line 1a = SUM per proprietor; CRP portion of line 4b -> Schedule SE line 1b (§1402(a)(1)).")},
    {"rule_id": "R-SF-QBI", "title": "Farm net profit -> Form 8995 QBI (§199A)", "rule_type": "routing", "precedence": 6, "sort_order": 6,
     "formula": "8995 line 2 += per-farm QBI = max(0-aware) Sch F line 34 - attributable (1/2-SE-tax + SE-retirement + farm SEHI).",
     "inputs": [], "outputs": [],
     "description": ("PER FARM. Farming is a qualified trade/business under §199A. Net farm profit feeds Form "
                     "8995 line 2 (the Schedule C QBI precedent + the i8995 reduction rule). WALK ITEM D: pro-rata "
                     "allocation of the reductions when a proprietor has both a Schedule C and a Schedule F.")},
    {"rule_id": "R-SF-ACCRUAL", "title": "Accrual method (Part III) — RED-defer", "rule_type": "routing", "precedence": 7, "sort_order": 7,
     "formula": "If sf_accounting_method == 'accrual' OR any Part III line (37-50) is present -> D_SF_ACCRUAL; line 34 not computed.",
     "inputs": ["sf_accounting_method"], "outputs": [],
     "description": "PER FARM. v1 supports the CASH method only. Accrual (Part III inventory accounting) = RED-defer (no silent gap)."},
    {"rule_id": "R-SF-ELECTIONS", "title": "CCC §77 / crop-insurance §451(f) / weather §451(e) — capture income, RED-defer the election", "rule_type": "routing", "precedence": 8, "sort_order": 8,
     "formula": "If L5a > 0 -> D_SF_CCC_ELECTION; if 6c checked -> D_SF_CROPINS_DEFER; if sf_weather_deferral_elected -> D_SF_WEATHER_DEFER. The dollar amounts STILL flow to line 9.",
     "inputs": ["sf_ccc_loans_election_5a", "sf_crop_insurance_defer_election_6c", "sf_weather_deferral_elected"], "outputs": [],
     "description": ("PER FARM. The three farm income ELECTIONS (§77 CCC-loan-as-income, §451(f) crop-insurance "
                     "deferral, §451(e) weather livestock deferral) are RED-defer: capture the dollar amounts where "
                     "they land on the face; the election machinery (attachments, multi-year binding) is preparer-handled.")},
    {"rule_id": "R-SF-ATRISK", "title": "Line 36 — at-risk routing (RED-defer Form 6198)", "rule_type": "routing", "precedence": 9, "sort_order": 9,
     "formula": "If L34 < 0: require 36a XOR 36b. 36a -> loss allowed (v1 assumes all at risk). 36b -> D_SF_ATRISK RED-defer (Form 6198).",
     "inputs": ["sf_all_at_risk_36a", "sf_some_not_at_risk_36b"], "outputs": ["36a", "36b"],
     "description": "PER FARM. v1 supports the all-at-risk case only; 36b (Form 6198 at-risk limitation) is RED-defer."},
    {"rule_id": "R-SF-PASSIVE", "title": "Non-material participation passive farm loss — RED-defer (Form 8582)", "rule_type": "routing", "precedence": 10, "sort_order": 10,
     "formula": "If sf_material_participation is False AND L34 < 0 -> D_SF_PASSIVE; the passive loss is limited via Form 8582 (§469).",
     "inputs": ["sf_material_participation"], "outputs": [],
     "description": "PER FARM. Line E 'No' + a net farm loss -> §469 passive activity loss limitation (Form 8582) = RED-defer."},
    {"rule_id": "R-SF-461L", "title": "§461(l) excess business/farm loss — warning (limit manual)", "rule_type": "routing", "precedence": 11, "sort_order": 11,
     "formula": "If L34 is a large net loss -> D_SF_461L warning; the §461(l) excess business loss limitation (Form 461) is preparer-handled in v1.",
     "inputs": [], "outputs": [],
     "description": "PER FARM. Excess business loss limitation (§461(l) / Form 461) = RED-defer (warning; the loss is captured, the limit is manual)."},
]

SCHEDF_LINES: list[dict] = [
    # Part I — Farm Income (Cash Method)
    {"line_number": "1a", "description": "Sales of purchased livestock and other resale items", "line_type": "input"},
    {"line_number": "1b", "description": "Cost or other basis of purchased livestock/items on line 1a", "line_type": "input"},
    {"line_number": "1c", "description": "Subtract line 1b from line 1a", "line_type": "calculated"},
    {"line_number": "2", "description": "Sales of livestock, produce, grains, products you raised", "line_type": "input"},
    {"line_number": "3a", "description": "Cooperative distributions (Form 1099-PATR)", "line_type": "input"},
    {"line_number": "3b", "description": "Cooperative distributions — taxable amount", "line_type": "input"},
    {"line_number": "4a", "description": "Agricultural program payments", "line_type": "input"},
    {"line_number": "4b", "description": "Agricultural program payments — taxable amount", "line_type": "input"},
    {"line_number": "5a", "description": "CCC loans reported under election (§77)", "line_type": "input"},
    {"line_number": "5b", "description": "CCC loans forfeited (memo)", "line_type": "input"},
    {"line_number": "5c", "description": "CCC loans forfeited — taxable amount", "line_type": "input"},
    {"line_number": "6a", "description": "Crop insurance proceeds — amount received in 2025", "line_type": "input"},
    {"line_number": "6b", "description": "Crop insurance proceeds — taxable amount", "line_type": "input"},
    {"line_number": "6c", "description": "Election to defer crop insurance to 2026 attached (checkbox)", "line_type": "input"},
    {"line_number": "6d", "description": "Amount deferred from 2024 (now recognized)", "line_type": "input"},
    {"line_number": "7", "description": "Custom hire (machine work) income", "line_type": "input"},
    {"line_number": "8", "description": "Other income (incl. fuel tax credit/refund)", "line_type": "input"},
    {"line_number": "9", "description": "Gross income. Add 1c, 2, 3b, 4b, 5a, 5c, 6b, 6d, 7, 8", "line_type": "subtotal"},
    # Part II — Farm Expenses
    {"line_number": "10", "description": "Car and truck expenses (attach Form 4562)", "line_type": "input"},
    {"line_number": "11", "description": "Chemicals", "line_type": "input"},
    {"line_number": "12", "description": "Conservation expenses", "line_type": "input"},
    {"line_number": "13", "description": "Custom hire (machine work)", "line_type": "input"},
    {"line_number": "14", "description": "Depreciation and section 179 expense — from Form 4562", "line_type": "calculated"},
    {"line_number": "15", "description": "Employee benefit programs (other than on line 23)", "line_type": "input"},
    {"line_number": "16", "description": "Feed", "line_type": "input"},
    {"line_number": "17", "description": "Fertilizers and lime", "line_type": "input"},
    {"line_number": "18", "description": "Freight and trucking", "line_type": "input"},
    {"line_number": "19", "description": "Gasoline, fuel, and oil", "line_type": "input"},
    {"line_number": "20", "description": "Insurance (other than health)", "line_type": "input"},
    {"line_number": "21a", "description": "Interest — mortgage (paid to banks, etc.)", "line_type": "input"},
    {"line_number": "21b", "description": "Interest — other", "line_type": "input"},
    {"line_number": "22", "description": "Labor hired (less employment credits)", "line_type": "input"},
    {"line_number": "23", "description": "Pension and profit-sharing plans", "line_type": "input"},
    {"line_number": "24a", "description": "Rent or lease — vehicles, machinery, equipment", "line_type": "input"},
    {"line_number": "24b", "description": "Rent or lease — other (land, animals, etc.)", "line_type": "input"},
    {"line_number": "25", "description": "Repairs and maintenance", "line_type": "input"},
    {"line_number": "26", "description": "Seeds and plants", "line_type": "input"},
    {"line_number": "27", "description": "Storage and warehousing", "line_type": "input"},
    {"line_number": "28", "description": "Supplies", "line_type": "input"},
    {"line_number": "29", "description": "Taxes", "line_type": "input"},
    {"line_number": "30", "description": "Utilities", "line_type": "input"},
    {"line_number": "31", "description": "Veterinary, breeding, and medicine", "line_type": "input"},
    {"line_number": "32a", "description": "Other expenses (specify) — a", "line_type": "input"},
    {"line_number": "32b", "description": "Other expenses (specify) — b", "line_type": "input"},
    {"line_number": "32c", "description": "Other expenses (specify) — c", "line_type": "input"},
    {"line_number": "32d", "description": "Other expenses (specify) — d", "line_type": "input"},
    {"line_number": "32e", "description": "Other expenses (specify) — e", "line_type": "input"},
    {"line_number": "32f", "description": "Other expenses (specify) — f", "line_type": "input"},
    {"line_number": "33", "description": "Total expenses. Add lines 10 through 32f", "line_type": "subtotal"},
    {"line_number": "34", "description": "Net farm profit/(loss). Subtract line 33 from line 9 -> Sch 1 L6 + Sch SE L1a", "line_type": "total"},
    {"line_number": "35", "description": "Reserved for future use", "line_type": "input"},
    {"line_number": "36a", "description": "All investment is at risk", "line_type": "input"},
    {"line_number": "36b", "description": "Some investment is not at risk (Form 6198 — RED-defer)", "line_type": "input"},
    # Part III — Farm Income (Accrual Method) — RED-defer; seeded for render-skip
    {"line_number": "37", "description": "Accrual: Sales of products (RED-defer)", "line_type": "input"},
    {"line_number": "38a", "description": "Accrual: Cooperative distributions (RED-defer)", "line_type": "input"},
    {"line_number": "38b", "description": "Accrual: Cooperative distributions — taxable (RED-defer)", "line_type": "input"},
    {"line_number": "39a", "description": "Accrual: Agricultural program payments (RED-defer)", "line_type": "input"},
    {"line_number": "39b", "description": "Accrual: Agricultural program payments — taxable (RED-defer)", "line_type": "input"},
    {"line_number": "40a", "description": "Accrual: CCC loans reported under election (RED-defer)", "line_type": "input"},
    {"line_number": "40b", "description": "Accrual: CCC loans forfeited (RED-defer)", "line_type": "input"},
    {"line_number": "40c", "description": "Accrual: CCC loans forfeited — taxable (RED-defer)", "line_type": "input"},
    {"line_number": "41", "description": "Accrual: Crop insurance proceeds (RED-defer)", "line_type": "input"},
    {"line_number": "42", "description": "Accrual: Custom hire income (RED-defer)", "line_type": "input"},
    {"line_number": "43", "description": "Accrual: Other income (RED-defer)", "line_type": "input"},
    {"line_number": "44", "description": "Accrual: Add 37, 38b, 39b, 40a, 40c, 41, 42, 43 (RED-defer)", "line_type": "subtotal"},
    {"line_number": "45", "description": "Accrual: Beginning inventory (RED-defer)", "line_type": "input"},
    {"line_number": "46", "description": "Accrual: Cost of products purchased (RED-defer)", "line_type": "input"},
    {"line_number": "47", "description": "Accrual: Add lines 45 and 46 (RED-defer)", "line_type": "subtotal"},
    {"line_number": "48", "description": "Accrual: Ending inventory (RED-defer)", "line_type": "input"},
    {"line_number": "49", "description": "Accrual: Cost of products sold. 47 - 48 (RED-defer)", "line_type": "calculated"},
    {"line_number": "50", "description": "Accrual: Gross income. 44 - 49 -> Part I line 9 (RED-defer)", "line_type": "total"},
]

SCHEDF_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_SF_ACCRUAL", "title": "Accrual method (Part III) — not supported", "severity": "error",
     "condition": "sf_accounting_method == 'accrual' OR any Part III line (37-50) is present",
     "message": ("Not supported — prepare manually: the accrual method of farm accounting (Schedule F Part "
                 "III — inventory of livestock/produce, cost of goods sold) is not modeled this version. v1 "
                 "computes the CASH method only (Parts I and II)."),
     "notes": "RED-defer. v1 cash only (Ken-locked scope)."},
    {"diagnostic_id": "D_SF_CCC_ELECTION", "title": "CCC loans reported as income (§77 election)", "severity": "warning",
     "condition": "sf_ccc_loans_election_5a > 0",
     "message": ("You reported Commodity Credit Corporation loan proceeds as income (line 5a, IRC §77). The "
                 "amount is included in gross income, but the §77 election itself (and its binding effect on "
                 "later years) is not managed by the software — confirm the election is properly made/attached."),
     "notes": "RED-defer the election; the dollar amount flows to line 9."},
    {"diagnostic_id": "D_SF_CROPINS_DEFER", "title": "Crop insurance deferral to 2026 (§451(f) election)", "severity": "warning",
     "condition": "sf_crop_insurance_defer_election_6c is True",
     "message": ("You checked the box to defer crop insurance proceeds to 2026 (line 6c, IRC §451(f)). The "
                 "deferral election and the required statement are not generated by the software — the taxable "
                 "amount on line 6b is reported as entered; prepare the deferral election manually."),
     "notes": "RED-defer the election; line 6b flows to line 9 as entered."},
    {"diagnostic_id": "D_SF_WEATHER_DEFER", "title": "Weather-related livestock-sale deferral (§451(e))", "severity": "warning",
     "condition": "sf_weather_deferral_elected is True",
     "message": ("You indicated a weather-related livestock-sale deferral (IRC §451(e)). The deferral election "
                 "is not modeled — the sale income is reported normally; prepare the §451(e) postponement "
                 "election and statement manually."),
     "notes": "RED-defer the election; income captured normally."},
    {"diagnostic_id": "D_SF_PASSIVE", "title": "Non-material participation farm loss — passive loss limit (Form 8582)", "severity": "error",
     "condition": "sf_material_participation is False AND line 34 < 0",
     "message": ("Not supported — prepare manually: you did not materially participate (line E 'No') and this "
                 "farm shows a net loss. The passive activity loss limitation (IRC §469 / Form 8582) is not "
                 "modeled this version; the loss may be limited."),
     "notes": "RED-defer Form 8582 (§469 passive loss)."},
    {"diagnostic_id": "D_SF_ATRISK", "title": "Some investment not at risk (line 36b) — Form 6198 not supported", "severity": "error",
     "condition": "sf_some_not_at_risk_36b is True (with a net loss)",
     "message": ("Not supported — prepare manually: you indicated some investment is not at risk (line 36b), "
                 "which requires Form 6198 and may limit your loss. The at-risk limitation is not modeled; v1 "
                 "supports only the all-at-risk case (line 36a)."),
     "notes": "RED-defer Form 6198."},
    {"diagnostic_id": "D_SF_461L", "title": "Large net farm loss — verify §461(l) excess business loss limit", "severity": "warning",
     "condition": "line 34 is a large net loss",
     "message": ("This Schedule F shows a substantial net farm loss. Confirm whether the excess business loss "
                 "limitation (IRC §461(l) / Form 461) applies — it is not computed by the software this version. "
                 "The loss is captured; the §461(l) limit is preparer-handled."),
     "notes": "RED-defer Form 461 (warning; loss captured)."},
    {"diagnostic_id": "D_SF_LOSS", "title": "Net farm loss — verify at-risk and passive-activity boxes", "severity": "info",
     "condition": "line 34 < 0",
     "message": ("This Schedule F shows a net loss. Confirm the at-risk box (line 36a/36b) and material "
                 "participation (line E). v1 allows the full loss only when all investment is at risk and the "
                 "activity is non-passive."),
     "notes": "Routes the preparer to line 36 / line E."},
]

SCHEDF_SCENARIOS: list[dict] = [
    {"scenario_name": "SF-T1 — cash profit, raised products (simple)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "sf_accounting_method": "cash", "line_2": 180000, "line_33": 120000,
                "sf_material_participation": True, "sf_all_at_risk_36a": True},
     "expected_outputs": {"line_9": 180000, "line_34": 60000, "feeds_sch1_l6": True, "feeds_schse_l1a": True},
     "notes": "L9=180,000 (raised products); L33=120,000 -> L34=60,000 -> Sch 1 L6 + Sch SE L1a."},
    {"scenario_name": "SF-T2 — purchased-livestock resale (1a/1b/1c)", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"tax_year": 2025, "sf_accounting_method": "cash", "line_1a": 50000, "line_1b": 38000,
                "line_2": 90000, "line_33": 70000, "sf_material_participation": True, "sf_all_at_risk_36a": True},
     "expected_outputs": {"line_1c": 12000, "line_9": 102000, "line_34": 32000},
     "notes": "L1c=50,000-38,000=12,000; L9=12,000+90,000=102,000; L34=102,000-70,000=32,000."},
    {"scenario_name": "SF-T3 — net farm loss, material participation + all at risk (loss allowed)", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"tax_year": 2025, "sf_accounting_method": "cash", "line_2": 40000, "line_33": 65000,
                "sf_material_participation": True, "sf_all_at_risk_36a": True},
     "expected_outputs": {"line_9": 40000, "line_34": -25000, "D_SF_LOSS": True, "feeds_sch1_l6": True},
     "notes": "Loss -25,000; material participation + all at risk -> full loss allowed -> Sch 1 L6 + Sch SE L1a."},
    {"scenario_name": "SF-T4 — accrual method RED (D_SF_ACCRUAL)", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"tax_year": 2025, "sf_accounting_method": "accrual", "line_2": 100000, "line_33": 70000},
     "expected_outputs": {"D_SF_ACCRUAL": True, "line_34": None},
     "notes": "Accrual -> RED, line 34 not silently computed (no silent gap)."},
    {"scenario_name": "SF-T5 — CCC loan-as-income election (D_SF_CCC_ELECTION)", "scenario_type": "normal", "sort_order": 5,
     "inputs": {"tax_year": 2025, "sf_accounting_method": "cash", "line_5a": 30000, "line_2": 50000, "line_33": 40000,
                "sf_material_participation": True, "sf_all_at_risk_36a": True},
     "expected_outputs": {"line_9": 80000, "line_34": 40000, "D_SF_CCC_ELECTION": True},
     "notes": "L5a=30,000 (CCC elected) flows into L9=30,000+50,000=80,000; D_SF_CCC_ELECTION fires (election manual)."},
    {"scenario_name": "SF-T6 — crop insurance with deferral election (D_SF_CROPINS_DEFER)", "scenario_type": "normal", "sort_order": 6,
     "inputs": {"tax_year": 2025, "sf_accounting_method": "cash", "line_6a": 20000, "line_6b": 20000,
                "sf_crop_insurance_defer_election_6c": True, "line_2": 60000, "line_33": 50000,
                "sf_material_participation": True, "sf_all_at_risk_36a": True},
     "expected_outputs": {"line_9": 80000, "line_34": 30000, "D_SF_CROPINS_DEFER": True},
     "notes": "6b=20,000 taxable flows into L9=20,000+60,000=80,000; 6c election -> D_SF_CROPINS_DEFER (deferral manual)."},
    {"scenario_name": "SF-T7 — non-material participation loss RED (D_SF_PASSIVE)", "scenario_type": "normal", "sort_order": 7,
     "inputs": {"tax_year": 2025, "sf_accounting_method": "cash", "line_2": 20000, "line_33": 45000,
                "sf_material_participation": False, "sf_all_at_risk_36a": True},
     "expected_outputs": {"line_34": -25000, "D_SF_PASSIVE": True},
     "notes": "Line E 'No' + loss -> §469 passive loss (Form 8582) RED-defer."},
    {"scenario_name": "SF-T8 — some not at risk loss RED (D_SF_ATRISK)", "scenario_type": "normal", "sort_order": 8,
     "inputs": {"tax_year": 2025, "sf_accounting_method": "cash", "line_2": 15000, "line_33": 40000,
                "sf_material_participation": True, "sf_some_not_at_risk_36b": True},
     "expected_outputs": {"line_34": -25000, "D_SF_ATRISK": True},
     "notes": "Loss with 36b checked -> Form 6198 at-risk limitation RED-defer."},
    {"scenario_name": "SF-T9 — depreciation (line 14) reduces expenses", "scenario_type": "normal", "sort_order": 9,
     "inputs": {"tax_year": 2025, "sf_accounting_method": "cash", "line_2": 150000, "line_14": 35000, "line_33": 110000,
                "sf_material_participation": True, "sf_all_at_risk_36a": True},
     "expected_outputs": {"line_9": 150000, "line_34": 40000, "depreciation_in_l33": True},
     "notes": "Line 14 depreciation (35,000 from 4562) is part of L33=110,000; L34=150,000-110,000=40,000."},
    {"scenario_name": "SF-T10 — two farms, same proprietor (multi-Schedule-F aggregation)", "scenario_type": "normal", "sort_order": 10,
     "inputs": {"tax_year": 2025, "farms": [{"line_34": 40000}, {"line_34": 15000}], "proprietor": "taxpayer"},
     "expected_outputs": {"sch1_l6": 55000, "schse_l1a": 55000},
     "notes": "PER FARM model: Sch 1 L6 = 40,000+15,000=55,000; Sch SE L1a (same proprietor) = 55,000."},
]

SCHEDF_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-SF-L1C", "IRS_2025_SCHEDF_FORM", "primary", "Line 1c = 1a - 1b"),
    ("R-SF-GROSS", "IRS_2025_SCHEDF_FORM", "primary", "Line 9 right-column list (1c,2,3b,4b,5a,5c,6b,6d,7,8)"),
    ("R-SF-DEPR", "IRS_2025_SCHEDF_FORM", "primary", "Line 14 depreciation/§179 (attach Form 4562)"),
    ("R-SF-EXPENSES", "IRS_2025_SCHEDF_FORM", "primary", "Line 33 = sum(10..32f)"),
    ("R-SF-NETPROFIT", "IRS_2025_SCHEDF_FORM", "primary", "Line 34 = L9 - L33"),
    ("R-SF-NETPROFIT", "IRS_2025_SCHEDF_INSTR", "secondary", "L34 -> Sch 1 L6 + Sch SE L1a; CRP -> SE L1b"),
    ("R-SF-QBI", "IRS_2025_SCHEDF_INSTR", "secondary", "Farm net -> Form 8995 QBI (§199A trade/business)"),
    ("R-SF-ACCRUAL", "IRS_2025_SCHEDF_FORM", "primary", "Part III accrual method (lines 37-50) — RED-defer"),
    ("R-SF-ELECTIONS", "IRC_77", "primary", "Line 5a CCC §77 election"),
    ("R-SF-ELECTIONS", "IRC_451_EF", "primary", "Line 6c §451(f) / weather §451(e) deferrals"),
    ("R-SF-ELECTIONS", "IRS_PUB_225", "secondary", "Pub 225 election narratives"),
    ("R-SF-ATRISK", "IRS_2025_SCHEDF_INSTR", "primary", "Line 36 at-risk routing (Form 6198)"),
    ("R-SF-PASSIVE", "IRS_2025_SCHEDF_INSTR", "primary", "Line E material participation -> Form 8582 (§469)"),
    ("R-SF-461L", "IRS_2025_SCHEDF_INSTR", "secondary", "§461(l) excess business loss (Form 461)"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 2 — SCHEDULE_SE (Self-Employment Tax) — AMENDED (farm optional method)
# Additive: update_or_create only touches the items below; the existing Part I
# standard-method facts/rules/lines/diagnostics/scenarios (Topic 8) are untouched.
# ═══════════════════════════════════════════════════════════════════════════

SCHEDSE_IDENTITY = {
    "form_number": "SCHEDULE_SE",
    "form_title": "Schedule SE (Form 1040) — Self-Employment Tax (TY2025)",
    "notes": (
        "Topic 8 authored Part I standard method (per proprietor; SE tax line 12 -> "
        "Sch 2 L4; 1/2-SE line 13 -> Sch 1 L15; year-keyed SS wage base). AMENDED "
        "2026-06-21 (Schedule F unit): line 1a is now a COMPUTED feeder from Schedule "
        "F line 34 (sum per proprietor) + CRP -> line 1b; the Part II FARM OPTIONAL "
        "METHOD (lines 14/15 -> line 4b) is supported for 2025 (SSA-indexed amounts; "
        "2026 unpublished -> RED). The NONFARM optional method (lines 16/17), church-"
        "employee income (line 5), and Form 4361 clergy stay RED-deferred."
    ),
}

SCHEDSE_FACTS: list[dict] = [
    # Re-pointed existing facts (additive update of the notes only) ──
    {"fact_key": "se_net_farm_profit_l1a", "label": "Line 1a — net farm profit/(loss) (Sch F L34 / 1065 K-1 box 14 A)",
     "data_type": "decimal", "default_value": "0", "sort_order": 2,
     "notes": "PER PROPRIETOR. COMPUTED feeder: SUM of this proprietor's Schedule F line 34 (+ farm 1065 K-1 box 14 A)."},
    {"fact_key": "se_crp_payments_l1b", "label": "Line 1b — Conservation Reserve Program payments (negative)",
     "data_type": "decimal", "default_value": "0", "sort_order": 3,
     "notes": "PER PROPRIETOR. COMPUTED feeder: SUM of this proprietor's Schedule F CRP portion (sf_crp_payments), negative (§1402(a)(1))."},
    # Existing facts re-declared verbatim (R-SE-OPTIONAL reads them; keeps the
    # narrowed rule's inputs all-declared — content-identical update_or_create).
    {"fact_key": "se_minister_4361", "label": "Part I 'A' — minister/religious-order Form 4361 filer", "data_type": "boolean", "sort_order": 4,
     "notes": "PER PROPRIETOR. Clergy/4361 special handling -> RED-defer (D_SE_003); v1 standard method only."},
    {"fact_key": "se_church_employee_income_l5a", "label": "Line 5a — church employee income (W-2)", "data_type": "decimal", "default_value": "0", "sort_order": 5,
     "notes": "PER PROPRIETOR. Church-employee SE income -> RED-defer (D_SE_003); v1 line 5a/5b = 0."},
    # ── Farm optional method (new) ──
    {"fact_key": "se_farm_optional_elected", "label": "Part II — farm optional method elected (checkbox)", "data_type": "boolean", "sort_order": 40,
     "notes": "PER PROPRIETOR. Elective: report optional SE earnings to obtain/maintain SS coverage. 2026 -> D_SE_FARMOPT_2026 (constants unpublished)."},
    {"fact_key": "se_gross_farm_income", "label": "Gross farm income (Sch F line 9) — for the 2/3 optional calc", "data_type": "decimal", "default_value": "0", "sort_order": 41,
     "notes": "PER PROPRIETOR. = SUM of this proprietor's Schedule F line 9 (+ farm 1065 K-1 box 14 B). Footnote 1 on Sch SE Part II."},
    {"fact_key": "se_farm_optional_amount_l15", "label": "Line 15 — farm optional method amount (output -> line 4b)", "data_type": "decimal", "sort_order": 42,
     "notes": "OUTPUT. = min(round_down(2/3 x gross farm income), FARM_OPT_MAX_INCOME[year]). -> line 4b."},
    # ── Constants (traceability; year-keyed, SSA-indexed) ──
    {"fact_key": "se_farm_opt_max_l14", "label": "Line 14 — maximum income for optional methods (YEAR-KEYED)", "data_type": "decimal", "sort_order": 43,
     "notes": "CONSTANT (FARM_OPT_MAX_INCOME): 2025 $7,240. 2026 UNPUBLISHED -> RED. SSA-indexed (NOT in RP 2025-32)."},
    {"fact_key": "se_farm_opt_gross_ceiling", "label": "Farm optional eligibility — gross farm income ceiling (YEAR-KEYED)", "data_type": "decimal", "sort_order": 44,
     "notes": "CONSTANT (FARM_OPT_GROSS_CEILING): 2025 $10,860. Eligible if gross farm income <= this OR net farm profit < floor."},
    {"fact_key": "se_farm_opt_profit_floor", "label": "Farm optional eligibility — net farm profit floor (YEAR-KEYED)", "data_type": "decimal", "sort_order": 45,
     "notes": "CONSTANT (FARM_OPT_PROFIT_FLOOR): 2025 $7,840. Eligible if net farm profit < this OR gross farm income <= ceiling."},
]

SCHEDSE_RULES: list[dict] = [
    {"rule_id": "R-SE-FARMOPT", "title": "Part II — farm optional method (lines 14/15) -> line 4b", "rule_type": "calculation", "precedence": 13, "sort_order": 13,
     "formula": ("Eligible iff gross farm income <= FARM_OPT_GROSS_CEILING[year] OR net farm profit < "
                 "FARM_OPT_PROFIT_FLOOR[year]. L14 = FARM_OPT_MAX_INCOME[year]; L15 = min(floor(2/3 x gross "
                 "farm income), L14) -> line 4b. 2026 unpublished -> D_SE_FARMOPT_2026 (no compute)."),
     "inputs": ["se_farm_optional_elected", "se_gross_farm_income", "se_farm_opt_max_l14",
                "se_farm_opt_gross_ceiling", "se_farm_opt_profit_floor"],
     "outputs": ["14", "15", "4b"],
     "description": ("PER PROPRIETOR. Ken-IN-scope 2026-06-21. Farm optional method only (the nonfarm method, "
                     "church, clergy stay RED via R-SE-OPTIONAL). 2025 verified off the Sch SE face ($7,240 / "
                     "$10,860 / $7,840); 2026 amounts UNPUBLISHED -> RED + standing re-pin (WALK ITEM A).")},
    # Narrowed: farm optional REMOVED from the RED-defer set (nonfarm/church/clergy stay).
    {"rule_id": "R-SE-OPTIONAL", "title": "Part II nonfarm optional / church-employee / clergy — RED-defer", "rule_type": "routing", "precedence": 12, "sort_order": 12,
     "formula": "If se_minister_4361 OR se_church_employee_income_l5a > 0 OR the NONFARM optional method (lines 16/17) is elected -> D_SE_003 RED-defer. (The FARM optional method is now supported — R-SE-FARMOPT.)",
     "inputs": ["se_minister_4361", "se_church_employee_income_l5a"], "outputs": [],
     "description": "PER PROPRIETOR. NARROWED 2026-06-21: the farm optional method moved to R-SE-FARMOPT (supported). Nonfarm optional + church/clergy remain RED-defer."},
]

SCHEDSE_LINES: list[dict] = [
    {"line_number": "1a", "description": "Net farm profit/(loss) — COMPUTED feeder from Sch F line 34 (per proprietor)", "line_type": "calculated"},
    {"line_number": "1b", "description": "CRP payments (negative) — COMPUTED feeder from Sch F CRP portion", "line_type": "calculated"},
    {"line_number": "4b", "description": "Optional methods — COMPUTED from line 15 (farm optional supported; nonfarm RED-defer)", "line_type": "calculated"},
    {"line_number": "14", "description": "Part II — maximum income for optional methods ($7,240 2025; 2026 RED)", "line_type": "calculated"},
    {"line_number": "15", "description": "Part II — farm optional method = min(2/3 x gross farm income, line 14) -> line 4b", "line_type": "calculated"},
    {"line_number": "16", "description": "Part II — line 14 minus line 15 (nonfarm cap; RED-defer)", "line_type": "input"},
    {"line_number": "17", "description": "Part II — nonfarm optional method amount (RED-defer)", "line_type": "input"},
]

SCHEDSE_DIAGNOSTICS: list[dict] = [
    # Narrowed existing D_SE_003 (farm optional removed from the RED set).
    {"diagnostic_id": "D_SE_003", "title": "Nonfarm optional / church-employee / clergy SE — not supported", "severity": "error",
     "condition": "se_minister_4361 is True OR se_church_employee_income_l5a > 0 OR the NONFARM optional method is elected",
     "message": ("Not supported — prepare manually: the Schedule SE NONFARM optional method (Part II lines "
                 "16/17), church-employee income (line 5), and Form 4361 minister handling are not modeled. "
                 "(The FARM optional method IS supported.) v1 computes the Part I standard method + the farm "
                 "optional method only."),
     "notes": "NARROWED 2026-06-21: farm optional removed from the RED set (now supported via R-SE-FARMOPT)."},
    {"diagnostic_id": "D_SE_FARMOPT_2026", "title": "Farm optional method for 2026 — constants unpublished", "severity": "error",
     "condition": "se_farm_optional_elected is True AND tax_year not in FARM_OPT_MAX_INCOME",
     "message": ("Not supported for 2026 — prepare manually: the farm optional method amounts (maximum "
                 "income, eligibility thresholds) are SSA-indexed and the 2026 figures are not yet published. "
                 "Re-pin when the 2026 Schedule SE is released."),
     "notes": "WALK ITEM A. Standing obligation to re-pin the 2026 farm-optional constants."},
    {"diagnostic_id": "D_SE_FARMOPT_INELIG", "title": "Farm optional method elected but not eligible", "severity": "warning",
     "condition": "se_farm_optional_elected AND gross farm income > ceiling AND net farm profit >= floor",
     "message": ("You elected the farm optional method, but this proprietor does not appear eligible: gross "
                 "farm income exceeds the ceiling AND net farm profit is at or above the floor. The optional "
                 "method requires gross farm income at/below the ceiling OR net farm profit below the floor."),
     "notes": "Eligibility guard (no silent gap on a wrong optional-method election)."},
]

SCHEDSE_SCENARIOS: list[dict] = [
    {"scenario_name": "SE-FARMOPT-1 — eligible, low gross farm income (2/3 binds)", "scenario_type": "normal", "sort_order": 13,
     "inputs": {"tax_year": 2025, "se_farm_optional_elected": True, "se_gross_farm_income": 6000, "line_2": 0},
     "expected_outputs": {"line_14": 7240, "line_15": 4000, "line_4b": 4000},
     "notes": "Gross farm income 6,000 <= 10,860 (eligible). 2/3 x 6,000 = 4,000 < 7,240 -> L15=4,000 -> line 4b."},
    {"scenario_name": "SE-FARMOPT-2 — eligible, high gross farm income (cap binds at $7,240)", "scenario_type": "normal", "sort_order": 14,
     "inputs": {"tax_year": 2025, "se_farm_optional_elected": True, "se_gross_farm_income": 10860, "se_net_farm_profit": 5000, "line_2": 0},
     "expected_outputs": {"line_14": 7240, "line_15": 7240, "line_4b": 7240},
     "notes": "Gross 10,860 <= ceiling (eligible). 2/3 x 10,860 = 7,240 -> capped at the 7,240 max -> L15=7,240."},
    {"scenario_name": "SE-FARMOPT-3 — 2026 election RED (D_SE_FARMOPT_2026)", "scenario_type": "normal", "sort_order": 15,
     "inputs": {"tax_year": 2026, "se_farm_optional_elected": True, "se_gross_farm_income": 6000},
     "expected_outputs": {"D_SE_FARMOPT_2026": True, "line_15": None},
     "notes": "2026 farm-optional constants unpublished -> RED, no silent compute (WALK ITEM A)."},
    {"scenario_name": "SE-FARMOPT-4 — ineligible election (D_SE_FARMOPT_INELIG)", "scenario_type": "normal", "sort_order": 16,
     "inputs": {"tax_year": 2025, "se_farm_optional_elected": True, "se_gross_farm_income": 50000, "se_net_farm_profit": 12000},
     "expected_outputs": {"D_SE_FARMOPT_INELIG": True},
     "notes": "Gross 50,000 > 10,860 AND net profit 12,000 >= 7,840 -> not eligible for the farm optional method."},
]

SCHEDSE_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-SE-FARMOPT", "IRS_2025_SCHEDSE_FORM", "primary", "Part II farm optional method (lines 14/15; 2025 $7,240 / $10,860 / $7,840)"),
    ("R-SE-FARMOPT", "IRS_PUB_225", "secondary", "Pub 225 farm optional method narrative"),
    ("R-SE-OPTIONAL", "IRS_2025_SCHEDSE_FORM", "primary", "Part II nonfarm optional / church (RED-defer)"),
]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY FORM LINKS
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_SCHEDF_FORM", "SCHEDULE_F", "governs"),
    ("IRS_2025_SCHEDF_INSTR", "SCHEDULE_F", "informs"),
    ("IRS_PUB_225", "SCHEDULE_F", "informs"),
    ("IRC_77", "SCHEDULE_F", "informs"),
    ("IRC_451_EF", "SCHEDULE_F", "informs"),
    ("IRC_1402A1", "SCHEDULE_F", "informs"),
    ("IRS_2025_SCHEDSE_FORM", "SCHEDULE_SE", "governs"),
    ("IRS_PUB_225", "SCHEDULE_SE", "informs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORMS ROSTER
# ═══════════════════════════════════════════════════════════════════════════

FORMS: list[dict] = [
    {"identity": SCHEDF_IDENTITY, "facts": SCHEDF_FACTS, "rules": SCHEDF_RULES, "lines": SCHEDF_LINES,
     "diagnostics": SCHEDF_DIAGNOSTICS, "scenarios": SCHEDF_SCENARIOS, "rule_links": SCHEDF_RULE_LINKS},
    {"identity": SCHEDSE_IDENTITY, "facts": SCHEDSE_FACTS, "rules": SCHEDSE_RULES, "lines": SCHEDSE_LINES,
     "diagnostics": SCHEDSE_DIAGNOSTICS, "scenarios": SCHEDSE_SCENARIOS, "rule_links": SCHEDSE_RULE_LINKS},
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS  (staged in tts-tax-app until the assertions build leg)
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-SCHF-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Schedule F line 34 net profit -> Schedule 1 line 6 AND Schedule SE line 1a",
     "description": ("Validates R-SF-NETPROFIT. L34 = L9 - L33. The SAME L34 feeds Schedule 1 line 6 (sum all "
                     "farms) and Schedule SE line 1a (sum per proprietor). Bug it catches: feeding one but not "
                     "the other, or summing across proprietors on Schedule SE."),
     "definition": {"kind": "flow_assertion", "form": "SCHEDULE_F",
                    "source_line": "34", "must_write_to": ["SCH_1.6", "SCHEDULE_SE.1a"]},
     "sort_order": 1},
    {"assertion_id": "FA-1040-SCHF-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Schedule F line 9 gross income = the verified right-column sum",
     "description": ("Validates R-SF-GROSS. L1c = L1a - L1b; L9 = 1c+2+3b+4b+5a+5c+6b+6d+7+8 (VERIFIED verbatim "
                     "— includes BOTH 5a and 5c, not 5b). Bug it catches: dropping 5a or 6d, or summing 5b."),
     "definition": {"kind": "formula_check", "form": "SCHEDULE_F",
                    "formula": "line_1c == line_1a - line_1b; line_9 == line_1c+line_2+line_3b+line_4b+line_5a+line_5c+line_6b+line_6d+line_7+line_8"},
     "sort_order": 2},
    {"assertion_id": "FA-1040-SCHF-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Schedule F line 33 total expenses + line 34 = line 9 - line 33",
     "description": ("Validates R-SF-EXPENSES/R-SF-NETPROFIT. L33 = sum(10..32f); L34 = L9 - L33. Bug it "
                     "catches: omitting an expense line from the total, or a home-office line that does not exist "
                     "on Schedule F."),
     "definition": {"kind": "formula_check", "form": "SCHEDULE_F",
                    "formula": "line_33 == sum(line_10..line_32f); line_34 == line_9 - line_33"},
     "sort_order": 3},
    {"assertion_id": "FA-1040-SCHF-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Schedule F line 14 depreciation <- Form 4562 engine",
     "description": ("Validates R-SF-DEPR. Line 14 depreciation + §179 is sourced from the 4562 engine "
                     "(aggregate_depreciation flow_to=schedule_f), not hand-entered. Bug it catches: the farm's "
                     "4562 depreciation not flowing to line 14."),
     "definition": {"kind": "flow_assertion", "form": "SCHEDULE_F",
                    "reads_from": "FORM_4562", "target_line": "14"},
     "sort_order": 4},
    {"assertion_id": "FA-1040-SCHF-05", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Schedule F net farm profit -> Form 8995 line 2 (QBI)",
     "description": ("Validates R-SF-QBI. Net farm profit (line 34, reduced by attributable 1/2-SE-tax / "
                     "SE-retirement / farm SEHI) feeds Form 8995 line 2 QBI. Bug it catches: farm income not "
                     "treated as a §199A qualified trade/business, or using gross net profit as QBI."),
     "definition": {"kind": "flow_assertion", "form": "SCHEDULE_F",
                    "source_line": "34", "must_write_to": ["8995.2"]},
     "sort_order": 5},
    {"assertion_id": "FA-1040-SCHF-06", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Schedule F CRP portion -> Schedule SE line 1b (negative, §1402(a)(1))",
     "description": ("Validates the CRP exclusion. The CRP portion of line 4b (sf_crp_payments) feeds Schedule "
                     "SE line 1b as a negative, excluding it from SE for SS retirement/disability recipients. Bug "
                     "it catches: CRP taxed for SE, or CRP not reaching line 1b."),
     "definition": {"kind": "flow_assertion", "form": "SCHEDULE_F",
                    "source": "sf_crp_payments", "must_write_to": ["SCHEDULE_SE.1b"]},
     "sort_order": 6},
    {"assertion_id": "FA-1040-SCHF-07", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Schedule F RED-defers each leave a RED (no silent gap)",
     "description": ("Validates the Schedule F RED-defer set: accrual (D_SF_ACCRUAL), CCC §77 election "
                     "(D_SF_CCC_ELECTION), crop-insurance §451(f) deferral (D_SF_CROPINS_DEFER), weather §451(e) "
                     "(D_SF_WEATHER_DEFER), passive loss (D_SF_PASSIVE), at-risk (D_SF_ATRISK), §461(l) "
                     "(D_SF_461L). Each fires rather than silently computing a wrong number."),
     "definition": {"kind": "gating_check", "form": "SCHEDULE_F",
                    "blockers": ["accrual", "ccc_election", "cropins_defer", "weather_defer", "passive_loss", "some_not_at_risk", "excess_farm_loss"],
                    "expect": {"red_fires": True}},
     "sort_order": 7},
    {"assertion_id": "FA-1040-SCHF-08", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "SE farm optional method = min(2/3 x gross farm income, $7,240 2025) -> line 4b; 2026 RED",
     "description": ("Validates R-SE-FARMOPT. L15 = min(floor(2/3 x gross farm income), FARM_OPT_MAX_INCOME[year]) "
                     "-> line 4b; 2025 max $7,240, eligibility $10,860/$7,840. 2026 unpublished -> RED. Bug it "
                     "catches: a stale/guessed 2026 amount, or the 2/3 fraction year-keyed."),
     "definition": {"kind": "constants_check", "form": "SCHEDULE_SE",
                    "constants": {"max_2025": 7240, "gross_ceiling_2025": 10860, "profit_floor_2025": 7840,
                                  "fraction": "2/3", "supported_years": [2025], "year_2026": "unpublished_red"}},
     "sort_order": 8},
]


# ═══════════════════════════════════════════════════════════════════════════
# Command
# ═══════════════════════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = (
        "Load the Schedule F spec into Rule Studio (creates SCHEDULE_F; amends "
        "SCHEDULE_SE with the Part II farm optional method + line-1a computed "
        "feeder). Refuses to seed until Ken sets READY_TO_SEED=True."
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()

        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad SCHEDULE_F spec + SCHEDULE_SE farm-optional amendment\n"))

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
                "REFUSING TO SEED SCHEDULE_F / SCHEDULE_SE amendment: not cleared to seed.\n"
                "\n"
                "Content is authored, but seeding is gated until Ken reviews the packet\n"
                "(the verified line-9 right-column sum + line-33/line-34 formulas; the\n"
                "cross-form flow map — line 34 -> Sch 1 L6 + Sch SE L1a, CRP -> SE L1b,\n"
                "depreciation <- 4562, farm net -> 8995 QBI; the farm-optional 2025 constants\n"
                "($7,240 / $10,860 / $7,840) + the 2026 gap; the 4 requires_human_review walk\n"
                "items; and the RED-defer enumeration) and flips the sentinel.\n"
                "\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True to proceed)\n"
                "\n"
                "NOTE: this AMENDS SCHEDULE_SE additively (line 1a computed feeder + the Part\n"
                "II farm optional method); the existing Part I standard method is untouched.\n"
                "\n"
                "Currently empty / placeholder:\n"
                f"  {still_empty}\n"
                "\n"
                "To proceed: review the module-level data lists, then set READY_TO_SEED\n"
                "= True. Idempotent via update_or_create — safe to re-run after edits."
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Topics / sources (mirror load_1040_schedule_c.py exactly)
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
        self.stdout.write("DATABASE TOTALS (after load_1040_schedule_f)")
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

        for fn in ("SCHEDULE_F", "SCHEDULE_SE"):
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
