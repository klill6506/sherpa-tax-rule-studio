"""Load the NC D-400 spec — North Carolina Individual Income Tax Return (TY2025).

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
North Carolina Form D-400 is the individual income tax return. LIKE GA Form 500
(and UNLIKE SC1040's federal-taxable-income start / AL Form 40's from-scratch
build), NC D-400 STARTS FROM FEDERAL ADJUSTED GROSS INCOME (line 6), applies a
FLAT 4.25% rate (TY2025), and handles federal conformity differences through
D-400 Schedule S: additions (Part A → line 7) and deductions (Part B → line 9).

NC's IRC conformity is FROZEN at January 1, 2023 — OBBBA does NOT apply for
TY2025. The signature depreciation feature: NC did not adopt IRC §168(k)/(n)
bonus or the increased §179, so it requires an 85% add-back of federal bonus
depreciation (Sch S Part A L3) and 85% of the §179 excess over NC's $25,000/
$200,000 limits (L4), recovered at 20%/year over the following five years.

4th STATE individual spec (GA Form 500, SC1040, AL Form 40 precede it;
load_sc1040.py + load_al_form40.py + load_ga500_form_500.py are the structural
precedents). Attaches to the child 1040 return in tts.

NO prior RS spec exists (lookup/NC_D400/ → 404). NEW form.

═══════════════════════════════════════════════════════════════════════════
v1 SCOPE — LOCKED (Ken's walk 2026-07-04, 4 AskUserQuestion decisions; DECISIONS D-7)
See nc_d400_source_brief.md §11.
═══════════════════════════════════════════════════════════════════════════
COMPUTES (v1):
  • Full-year RESIDENT D-400 (L6 → L34) + SCHEDULE PN part-year/nonresident        [Dec A]
    proration (Schedule PN line 24 decimal → D-400 L13; L14 = L12b × L13).
  • Federal-AGI start (L6) + Schedule S Part A additions → L7/L8; Part B
    deductions → L9; NC taxable income L12a/L12b.
  • THE DEPRECIATION ADD-BACK (Dec B): COMPUTE the current-year 85% bonus         [Dec B]
    add-back (L3) + 85% of the §179 excess over NC's $25,000/$200,000 limits
    (L4). DIRECT-ENTRY the 20% prior-year (2020-2024) recovery installments
    (L23a-e/L24a-e) — they need historical records the spec cannot reach.
  • STRUCTURED Schedule S Part B subtractions (Dec C): L18 US-obligation          [Dec C]
    interest, L19 SS/RR, L20 Bailey Settlement, L21 military retirement — each a
    modeled line item with an eligibility diagnostic, summed into the Part B total.
  • The child deduction AGI-banded table (L10; $3,000 → $0 by federal AGI and
    filing status); the NC standard-deduction election (L11; MFS $0 if spouse
    itemizes) + NC itemized deductions (Schedule A); the flat 4.25% tax (L14→L15);
    withholding/payments → refund/due.

DIRECT-ENTRY (line exists, diagnostic prompts):                                  [Dec D]
  • D-400TC tax credits (L16); consumer use tax (L18); contributions (L30-32);
    the 20% depreciation recovery installments (L23f/L24f); niche Schedule S
    Part A/B items not modeled (other_additions / other_deductions).

RED-DEFERS (each its own "prepare manually" RED — no silent gap):                [Dec D]
  • Schedule PN-1 (other additions/deductions without a dedicated PN line) — D_NCD400_PN1.
  • Amended-return lines L22/L24 + Schedule AM — D_NCD400_AMENDED.
  • Estimated-tax underpayment interest L26e (Form D-422) — D_NCD400_D422.
  • NC net operating loss L39 — D_NCD400_NOL.

═══════════════════════════════════════════════════════════════════════════
requires_human_review WALK ITEMS (for Ken's in-session review before seeding)
═══════════════════════════════════════════════════════════════════════════
W1. FLAT RATE 4.25% (0.0425) — year-keyed (NC_FLAT_RATE); form face + booklet p.7
    verbatim. The single most year-sensitive constant (TY2026 → 3.99%). CONFIRM.
W2. 85% ADD-BACK + $25,000/$200,000 NC §179 LIMITS — year-keyed; booklet p.17
    verbatim. Most legislation-sensitive numbers. The §179-excess add-back needs
    BOTH the federal §179 deduction AND the NC §179 (computed at NC limits) — the
    spec computes nc_sec179 = min(federal §179, $25,000) and flags the $200,000
    investment phaseout as a diagnostic (asset-level cost not always reachable).
    CONFIRM the add-back basis + that direct-entry of the prior-year 20%
    installments (L23f/L24f) is the right v1 boundary.
W3. CONFORMITY DATE = Jan 1, 2023 (OBBBA NOT adopted) — load-bearing for the
    depreciation add-back AND the std-deduction non-conformity. Booklet warns to
    "check the Department's website for any updates to federal conformity." CONFIRM.
W4. STANDARD DEDUCTION $12,750 / $25,500 / $19,125 (+ MFS $0 if spouse itemizes;
    no age-65/blind add-on) — booklet p.14 verbatim. CONFIRM.
W5. CHILD DEDUCTION AGI-banded table (3 status groups; breakpoint falls in the
    LOWER/higher-deduction band) — booklet p.13 verbatim. CONFIRM the bands.
W6. STATUTORY TEXT (§105-153.5/.6/.7) taken from the D-401 booklet's citations,
    not fetched verbatim from ncleg.gov (§10 flag 4). Numbers match what the forms
    enforce; pull statute text as a 2nd pass only if verbatim language is needed.

═══════════════════════════════════════════════════════════════════════════
VERIFIED STRUCTURE + CONSTANTS (READ 2026-07-04 from the FINAL 2025 NCDOR PDFs —
NOT memory: Form D-400 & Schedule S rev "Web-Fill 9-25"; D-401 Instructions 2025.
Full source brief: nc_d400_source_brief.md.)
═══════════════════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════════════════
SAFETY GUARD — READY_TO_SEED stays False until Ken approves the review walk
(W1-W6) in-session. Until then the command refuses to write to the DB.
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
# SAFETY GUARD — flip ONLY after Ken's in-session review walk (W1-W6 above).
#
# FLIPPED 2026-07-04 — Ken APPROVED the review walk in-session ("Approve — flip,
# seed, export"): W1 flat 4.25% rate (form face + booklet p.7), W2 the 85%
# bonus/§179 add-back + $25k/$200k limits (booklet p.17; §179-phaseout as a
# diagnostic), W3 conformity Jan 1 2023 (OBBBA not adopted), W4 the standard
# deduction (booklet p.14), W5 the child-deduction table (booklet p.13), W6 the
# statutory-text provenance — all blessed as in-spec re-verify flags. Validated
# on a throwaway SQLite DB (29 facts / 11 rules / 21 lines / 8 diag / 8 tests /
# 4 FA, every rule cited).
# ═══════════════════════════════════════════════════════════════════════════
READY_TO_SEED = True


FORM_JURISDICTION = "NC"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1040"]


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS (year-keyed; cited in nc_d400_source_brief.md; never memory)
# ═══════════════════════════════════════════════════════════════════════════

# Flat rate (§105-153.7 / D-400 line 15). W1 — TY2026 steps to 3.99%.
NC_FLAT_RATE: dict[int, str] = {2025: "0.0425"}

# NC standard deduction by filing status (booklet p.14). MFS → $0 if spouse itemizes.
# No age-65/blind add-on. QW/Surviving Spouse tracks MFJ. W4.
NC_STD_DED: dict[int, dict] = {2025: {
    "single": 12750, "MFJ": 25500, "QW": 25500, "MFS": 12750, "HOH": 19125,
}}

# NC §179 (booklet p.17). NC did NOT adopt the increased federal limits. W2.
NC_SEC179_LIMIT: dict[int, int] = {2025: 25000}
NC_SEC179_PHASEOUT: dict[int, int] = {2025: 200000}

# Depreciation add-back fraction — 85% of federal bonus AND of the §179 excess (booklet p.17). W2.
NC_DEPR_ADDBACK_PCT: dict[int, str] = {2025: "0.85"}

# Child deduction AGI-banded table (booklet p.13). Per status group: (federal_agi_ceiling, per_child).
# Breakpoint value falls in the LOWER band (higher deduction): use federal_agi <= ceiling. W5.
NC_CHILD_DEDUCTION: dict[int, dict] = {2025: {
    "MFJ": [(40000, 3000), (60000, 2500), (80000, 2000), (100000, 1500), (120000, 1000), (140000, 500), (None, 0)],
    "HOH": [(30000, 3000), (45000, 2500), (60000, 2000), (75000, 1500), (90000, 1000), (105000, 500), (None, 0)],
    "single": [(20000, 3000), (30000, 2500), (40000, 2000), (50000, 1500), (60000, 1000), (70000, 500), (None, 0)],
}}  # QW → MFJ table; MFS → single table (resolved at compute).

# NC itemized deduction caps (Schedule A, booklet p.20). W6 statute note.
NC_PROPERTY_TAX_CAP: dict[int, dict] = {2025: {"default": 10000, "MFS": 5000}}
NC_MORTGAGE_PLUS_PROPERTY_CAP: dict[int, int] = {2025: 20000}       # combined L1+L2 cap per return
NC_MEDICAL_AGI_FLOOR_PCT: dict[int, str] = {2025: "0.075"}          # medical reduced by 7.5% of federal AGI

# IRC conformity date (booklet p.17). OBBBA not adopted. W3.
NC_CONFORMITY_DATE = "2023-01-01"


def _yk(d: dict, year: int):
    return d.get(year) if d.get(year) is not None else d[2025]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY TOPICS / SOURCES
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("nc_income_tax", "North Carolina Form D-400 individual income tax: federal-AGI start, flat 4.25% "
     "rate, Schedule S bonus/§179 85% add-back + 20%/5-year recovery, child-deduction table, standard/"
     "itemized deductions, and Schedule PN part-year/nonresident proration."),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_1040_FORM",  # federal AGI (D-400 line 6) is the starting point
]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "NC_2025_FORM_D400",
        "source_type": "state_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "NC",
        "title": "2025 North Carolina Form D-400 — Individual Income Tax Return",
        "citation": "NC Form D-400 (2025), Web-Fill 9-25",
        "issuer": "North Carolina Department of Revenue",
        "official_url": "https://www.ncdor.gov/2025-d-400-web-filled-version/open",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["nc_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "Form D-400 face (2025) — verified line map",
                "excerpt_text": (
                    "6 Federal Adjusted Gross Income; 7 Additions to Federal AGI (Sch S Part A L16); 8 = "
                    "L6+L7; 9 Deductions from Federal AGI (Sch S Part B L41); 10a # qualifying children / "
                    "10b Child Deduction; 11 NC Standard OR NC Itemized Deduction; 12a = L9+L10b+L11, 12b "
                    "= L8−L12a; 13 Part-year/Nonresident Taxable Percentage (Sch PN L24, decimal); 14 NC "
                    "Taxable Income (full-year = L12b; PY/NR = L12b × L13); 15 NC Income Tax = L14 × 4.25% "
                    "(0.0425), if zero or less enter 0. 16 Tax Credits (D-400TC Part 3 L20); 17 = L15−L16; "
                    "18 Consumer Use Tax; 19 = L17+L18; 20a/20b NC tax withheld; 21a-d other payments; 23 "
                    "= Σ20a-22; 25 = L23−L24; 26a tax due / 26d penalties+interest / 26e est-tax "
                    "underpayment interest; 27 Amount Due = 26a+26d+26e; 28 Overpayment = L25−L19; 30-32 "
                    "contributions; 34 Refund = L28−L33."
                ),
                "summary_text": "D-400 (2025): federal AGI (L6) → Sch S additions/deductions → child deduction + std/itemized → NC taxable income (L14) → flat 4.25% (L15) → credits → refund/due.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Flat rate (line 15) + standard deduction chart (booklet p.14)",
                "excerpt_text": (
                    "Line 15: 'Multiply Line 14 by 4.25% (0.0425).' TY2025 rate = 4.25% (2024 was 4.50%; "
                    "after 2025 = 3.99%). NC Standard Deduction: Single $12,750; MFJ / Qualifying Widow(er) "
                    "/ Surviving Spouse $25,500; MFS $12,750 (or $0 if spouse claims itemized deductions); "
                    "Head of Household $19,125. No additional NC standard deduction for age 65+/blind. If "
                    "not eligible for the federal standard deduction, NC standard deduction is ZERO."
                ),
                "summary_text": "Flat 4.25% (0.0425) TY2025; std ded Single $12,750 / MFJ $25,500 / HOH $19,125 / MFS $12,750 or $0-if-spouse-itemizes; no 65+/blind add-on.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Child deduction AGI-banded table (booklet p.13)",
                "excerpt_text": (
                    "Per qualifying child (federal §24 child) × number of children (L10a) = L10b, by "
                    "federal AGI (L6) and filing status; breakpoint value falls in the lower (higher-"
                    "deduction) band. MFJ/QW/SS: ≤40,000 $3,000; 40,001-60,000 $2,500; 60,001-80,000 "
                    "$2,000; 80,001-100,000 $1,500; 100,001-120,000 $1,000; 120,001-140,000 $500; >140,000 "
                    "$0. HOH: ≤30,000 $3,000 … >105,000 $0. Single/MFS: ≤20,000 $3,000 … >70,000 $0."
                ),
                "summary_text": "Child deduction: $3,000/child down to $0, AGI-banded by filing status (MFJ ≤$40k→$3,000 … >$140k→$0).",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "NC_2025_SCHEDULE_S",
        "source_type": "state_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "NC",
        "title": "2025 NC D-400 Schedule S — Additions and Deductions",
        "citation": "NC D-400 Schedule S (2025), Web-Fill 9-25",
        "issuer": "North Carolina Department of Revenue",
        "official_url": "https://www.ncdor.gov/2025-d-400-schedule-s-web-fill-version/open",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["nc_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "Schedule S Part A additions + Part B deductions (2025 line map)",
                "excerpt_text": (
                    "PART A ADDITIONS (L1-16, total L16 → D-400 L7): L1 non-NC muni interest; L2 "
                    "opportunity-fund deferred gain; L3 BONUS DEPRECIATION; L4 IRC §179 EXPENSE; L5 S-corp "
                    "built-in gains tax; L7 federal NOL; L8 SALT deducted by a PTE; L13 discharged student "
                    "loan; L14 taxed-PTE loss; L16 Total. PART B DEDUCTIONS (L17-41, total L41 → D-400 L9): "
                    "L17 state/local tax refund; L18 U.S.-obligation interest; L19 SS/Railroad Retirement; "
                    "L20 Bailey Settlement retirement (vested NC state/local/federal retirees); L21 U.S. "
                    "Uniformed Services military retirement; L22 bonus asset basis; L23 (23a-e = 2020-2024, "
                    "total 23f) bonus depreciation 20% recovery; L24 (24a-e = 2020-2024, total 24f) §179 "
                    "20% recovery; L38 taxed-PTE income; L39 NC NOL; L41 Total."
                ),
                "summary_text": "Sch S Part A additions (L3 bonus, L4 §179) → D-400 L7; Part B deductions (L18-21 structured retirement/US-obligation; L23/24 20% depreciation recovery) → D-400 L9.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Bonus depreciation & §179 add-back mechanics (booklet p.17, p.19 verbatim)",
                "excerpt_text": (
                    "'North Carolina did not adopt the bonus depreciation provisions in IRC sections "
                    "168(k) or 168(n)... You must add 85% of the amount of bonus depreciation deducted on "
                    "your federal return.' §179: 'North Carolina did not conform to the increased federal "
                    "expense deduction or increased investment limitations... NC dollar and investment "
                    "limitations are $25,000 and $200,000, respectively. You must add 85% of the difference "
                    "between the IRC section 179 expense deduction using federal limitations and the "
                    "deduction using NC limitations.' Recovery (Part B L23/L24): 'deduct an amount equal to "
                    "20% of the [bonus / §179] deduction added ... on your 2020, 2021, 2022, 2023, and 2024 "
                    "state tax returns' — 5 installments beginning the year after the add-back. A TY2025 "
                    "add-back first recovers on the TY2026 return. IRC conformity frozen at Jan 1, 2023 "
                    "(OBBBA does NOT apply)."
                ),
                "summary_text": "Add back 85% of federal bonus (L3) + 85% of the §179 excess over NC's $25k/$200k limits (L4); recover 20%/yr over the following 5 years (L23/L24, referencing 2020-2024 add-backs on the 2025 form).",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "NC_2025_D401_INSTRUCTIONS",
        "source_type": "state_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "NC",
        "title": "2025 NC D-401 Individual Income Tax Instructions",
        "citation": "NC D-401 Instructions (2025)",
        "issuer": "North Carolina Department of Revenue",
        "official_url": "https://www.ncdor.gov/2025-d-401-individual-income-tax-instructions/open",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["nc_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "NC itemized deductions (Schedule A, booklet p.20)",
                "excerpt_text": (
                    "NC itemized deductions are a restricted subset of federal Schedule A, elected on "
                    "D-400 line 11: (1) qualified home mortgage interest (§163(h)); (2) real estate "
                    "property tax (§164), capped $10,000 (single/MFJ/HOH) / $5,000 (MFS); the combined "
                    "mortgage interest + property tax is capped at $20,000 per return (Line 5 = lesser of "
                    "L3 or $20,000); (6) charitable contributions (§170); (7) medical & dental (§213) "
                    "reduced by 7.5% of federal AGI; (8) repayment of claim-of-right income. No other "
                    "federal Schedule A items are allowed. Total → Schedule A line 10 → D-400 line 11."
                ),
                "summary_text": "NC itemized (Sch A): mortgage interest + property tax (capped $20k combined; property $10k/$5k MFS) + charitable + medical (less 7.5% AGI) + claim-of-right; nothing else.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Bailey / military retirement & Schedule PN proration (booklet p.13, p.21)",
                "excerpt_text": (
                    "Part B L20 Bailey Settlement: vested NC state/local/federal (incl. military) retirees "
                    "with 5+ years of creditable service as of Aug 12, 1989 fully deduct retirement "
                    "benefits (excludes local §457/§403(b)). L21 U.S. Uniformed Services: 20+ years (or "
                    "medical) retiree may deduct retirement pay + Survivor Benefit Plan, if not under L20 "
                    "(excludes §61 severance). L19 Social Security / Railroad Retirement fully deductible. "
                    "L18 U.S.-obligation interest deductible. Schedule PN: Line 24 = Column B ÷ Column A "
                    "(total income modified by NC adjustments), a 4-decimal fraction → D-400 line 13; D-400 "
                    "line 14 = line 12b × line 13. 'The resulting percentage may be greater than 100%, but "
                    "not less than 0%.'"
                ),
                "summary_text": "Bailey (L20, 5+ yrs svc @8/12/1989), military (L21, 20+ yrs), SS/RR (L19), US-obligation (L18) deductible; Schedule PN L24 = ColB/ColA (4-dec) → D-400 L13 → L14 = L12b × L13.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "NC_GS_105_153_7",
        "source_type": "state_statute",
        "source_rank": "controlling",
        "jurisdiction_code": "NC",
        "title": "N.C. Gen. Stat. §105-153.7 — Individual income tax imposed (flat rate)",
        "citation": "N.C. Gen. Stat. §105-153.7 (2025)",
        "issuer": "North Carolina General Assembly",
        "official_url": "https://www.ncleg.gov/EnactedLegislation/Statutes/HTML/BySection/Chapter_105/GS_105-153.7.html",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 8.8,
        "topics": ["nc_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "NC flat rate — statutory basis (per D-401 booklet citation, W6)",
                "excerpt_text": (
                    "§105-153.7 imposes the individual income tax at a single flat rate on North Carolina "
                    "taxable income. The TY2025 rate is 4.25% (0.0425) per the D-400 form face and D-401 "
                    "booklet p.7; the rate steps to 3.99% after 2025 (S.L. 2023-134, with further "
                    "trigger-based reductions possible TY2027+). Statute text taken from the booklet's "
                    "citation, not independently fetched from ncleg.gov (W6 / §10 flag 4)."
                ),
                "summary_text": "§105-153.7: flat individual rate; TY2025 = 4.25% (form + booklet), 3.99% after 2025.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "NC_GS_105_153_6",
        "source_type": "state_statute",
        "source_rank": "controlling",
        "jurisdiction_code": "NC",
        "title": "N.C. Gen. Stat. §105-153.6 — Adjustments for bonus depreciation and §179",
        "citation": "N.C. Gen. Stat. §105-153.6 (2025)",
        "issuer": "North Carolina General Assembly",
        "official_url": "https://www.ncleg.gov/EnactedLegislation/Statutes/HTML/BySection/Chapter_105/GS_105-153.6.html",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 8.8,
        "topics": ["nc_income_tax"],
        "excerpts": [
            {
                "excerpt_label": "Bonus/§179 depreciation adjustment — statutory basis (per D-401 booklet, W6)",
                "excerpt_text": (
                    "§105-153.6 requires the addback of 85% of the federal bonus depreciation deduction and "
                    "85% of the difference between the federal §179 expense and the §179 expense computed "
                    "under NC's $25,000 dollar / $200,000 investment limitations, and allows a deduction of "
                    "20% of each addback in each of the five taxable years following the addback year. "
                    "Constants per the D-401 booklet p.17/p.19; NC conformity date is Jan 1, 2023 (OBBBA "
                    "not adopted). Statute text taken from the booklet's citation, not fetched from "
                    "ncleg.gov (W6 / §10 flag 4)."
                ),
                "summary_text": "§105-153.6: 85% add-back of federal bonus + 85% of the §179 excess over $25k/$200k; 20%/5-year recovery beginning the following year.",
                "is_key_excerpt": True,
            },
        ],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("NC_2025_FORM_D400", "NC_D400", "governs"),
    ("NC_2025_SCHEDULE_S", "NC_D400", "governs"),
    ("NC_2025_D401_INSTRUCTIONS", "NC_D400", "governs"),
    ("NC_GS_105_153_7", "NC_D400", "governs"),
    ("NC_GS_105_153_6", "NC_D400", "governs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM — NC D-400
# ═══════════════════════════════════════════════════════════════════════════

NCD400_FACTS: list[dict] = [
    {"fact_key": "filing_status", "label": "Filing status", "data_type": "choice", "required": True, "sort_order": 1,
     "choices": ["single", "MFJ", "MFS", "HOH", "QW"], "notes": "QW/Surviving Spouse tracks MFJ for std ded + child deduction."},
    {"fact_key": "is_part_year_or_nr", "label": "Part-year resident or nonresident?", "data_type": "boolean", "required": False, "sort_order": 2,
     "notes": "If True, Schedule PN proration applies (L13/L14). Dec A."},
    {"fact_key": "federal_agi", "label": "Federal adjusted gross income (D-400 line 6)", "data_type": "decimal", "required": True, "sort_order": 3,
     "notes": "The NC starting point; also selects the child-deduction band."},
    # Schedule S Part A additions
    {"fact_key": "federal_bonus_depreciation", "label": "Federal bonus depreciation deducted (for the L3 add-back)", "data_type": "decimal", "required": False, "sort_order": 10,
     "notes": "Dec B. NC adds back 85%."},
    {"fact_key": "federal_sec179_deduction", "label": "Federal IRC §179 expense deducted (for the L4 add-back)", "data_type": "decimal", "required": False, "sort_order": 11,
     "notes": "Dec B. NC adds back 85% of (federal §179 − NC §179 at $25k limit)."},
    {"fact_key": "sec179_property_cost", "label": "Total §179 property placed in service (for the $200k NC phaseout check)", "data_type": "decimal", "required": False, "sort_order": 12,
     "notes": "W2. If > $200,000 the NC §179 limit phases down dollar-for-dollar; flagged as a diagnostic."},
    {"fact_key": "other_additions", "label": "Other Schedule S Part A additions (direct-entry, L1/L2/L5/L7/L8/L13/L14…)", "data_type": "decimal", "required": False, "sort_order": 13},
    # Schedule S Part B deductions (structured — Dec C)
    {"fact_key": "us_obligation_interest", "label": "U.S.-obligation interest (Sch S L18)", "data_type": "decimal", "required": False, "sort_order": 20},
    {"fact_key": "ss_rr_benefits", "label": "Taxable Social Security / Railroad Retirement (Sch S L19)", "data_type": "decimal", "required": False, "sort_order": 21},
    {"fact_key": "bailey_retirement", "label": "Bailey Settlement retirement benefits (Sch S L20)", "data_type": "decimal", "required": False, "sort_order": 22,
     "notes": "Vested NC state/local/federal (incl. military) retiree, 5+ yrs creditable service as of Aug 12, 1989."},
    {"fact_key": "military_retirement", "label": "U.S. Uniformed Services military retirement (Sch S L21)", "data_type": "decimal", "required": False, "sort_order": 23,
     "notes": "20+ yrs or medical retiree, if not already deducted under Bailey (L20)."},
    {"fact_key": "depr_recovery_bonus", "label": "Bonus depreciation 20% recovery installments (Sch S L23f, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 24,
     "notes": "Dec B. 20% of the 2020-2024 add-backs; needs historical records."},
    {"fact_key": "depr_recovery_179", "label": "§179 20% recovery installments (Sch S L24f, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 25,
     "notes": "Dec B. 20% of the 2020-2024 add-backs; needs historical records."},
    {"fact_key": "other_deductions", "label": "Other Schedule S Part B deductions (direct-entry, L17/L25-37/L38…)", "data_type": "decimal", "required": False, "sort_order": 26},
    # Child deduction
    {"fact_key": "num_qualifying_children", "label": "Number of qualifying children (D-400 line 10a)", "data_type": "integer", "required": False, "sort_order": 30},
    # Deduction election / itemized (Schedule A)
    {"fact_key": "deduction_election", "label": "Deduction election (L11)", "data_type": "choice", "required": True, "sort_order": 40, "choices": ["standard", "itemized"]},
    {"fact_key": "spouse_itemizes", "label": "MFS: does the spouse claim itemized deductions? (→ NC std ded $0)", "data_type": "boolean", "required": False, "sort_order": 41},
    {"fact_key": "mortgage_interest", "label": "Home mortgage interest (Sch A L1)", "data_type": "decimal", "required": False, "sort_order": 42},
    {"fact_key": "real_estate_property_tax", "label": "Real estate property tax (Sch A L2, capped $10k/$5k MFS)", "data_type": "decimal", "required": False, "sort_order": 43},
    {"fact_key": "charitable_contributions", "label": "Charitable contributions (Sch A L6)", "data_type": "decimal", "required": False, "sort_order": 44},
    {"fact_key": "medical_dental_expenses", "label": "Medical & dental expenses (Sch A L7, less 7.5% AGI)", "data_type": "decimal", "required": False, "sort_order": 45},
    {"fact_key": "claim_of_right_repayment", "label": "Repayment of claim-of-right income (Sch A L8)", "data_type": "decimal", "required": False, "sort_order": 46},
    # Schedule PN
    {"fact_key": "pn_col_a_total", "label": "Schedule PN Column A total income (all-source, L21)", "data_type": "decimal", "required": False, "sort_order": 50,
     "notes": "Dec A. Denominator of the PN taxable percentage."},
    {"fact_key": "pn_col_b_total", "label": "Schedule PN Column B total income (NC-source / while-resident, L21)", "data_type": "decimal", "required": False, "sort_order": 51,
     "notes": "Dec A. Numerator of the PN taxable percentage."},
    # Credits / payments
    {"fact_key": "tax_credits_d400tc", "label": "Tax credits (D-400TC Part 3 L20, L16, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 60},
    {"fact_key": "consumer_use_tax", "label": "Consumer use tax (L18, direct-entry)", "data_type": "decimal", "required": False, "sort_order": 61},
    {"fact_key": "nc_withholding", "label": "NC income tax withheld (L20a+L20b)", "data_type": "decimal", "required": False, "sort_order": 62},
    {"fact_key": "other_payments", "label": "Other payments — estimated/extension/PTE (L21a-d)", "data_type": "decimal", "required": False, "sort_order": 63},
    {"fact_key": "contributions", "label": "Contributions — wildlife/education/cancer funds (L30-32)", "data_type": "decimal", "required": False, "sort_order": 64},
]

NCD400_RULES: list[dict] = [
    {"rule_id": "R-NC-DEPR-ADDBACK", "title": "Depreciation add-back (Sch S Part A L3/L4) — 85% bonus + 85% §179 excess", "rule_type": "calculation",
     "formula": ("bonus_addback (L3) = round(0.85 * federal_bonus_depreciation) ; "
                 "nc_sec179 = min(federal_sec179_deduction, 25000) [phased down $-for-$ if sec179_property_cost > 200000] ; "
                 "sec179_addback (L4) = round(0.85 * max(0, federal_sec179_deduction - nc_sec179))"),
     "inputs": ["federal_bonus_depreciation", "federal_sec179_deduction", "sec179_property_cost"],
     "outputs": ["L3", "L4"], "sort_order": 10,
     "description": "Dec B / W2. NC did not adopt IRC §168(k)/(n) bonus or the increased §179 (limits $25k/$200k). 85% add-back of each; the 20% recovery of these first hits the TY2026 return (prior-year installments are direct-entry L23f/L24f)."},
    {"rule_id": "R-NC-ADDITIONS", "title": "Additions to federal AGI (L7) and total (L8)", "rule_type": "calculation",
     "formula": "L7 = L3 + L4 + other_additions  [Sch S Part A L16] ; L8 = federal_agi + L7",
     "inputs": ["other_additions", "federal_agi"], "outputs": ["L7", "L8"], "sort_order": 11},
    {"rule_id": "R-NC-DEDUCTIONS", "title": "Deductions from federal AGI (L9) — Sch S Part B total", "rule_type": "calculation",
     "formula": ("L9 = us_obligation_interest + ss_rr_benefits + bailey_retirement + military_retirement "
                 "+ depr_recovery_bonus + depr_recovery_179 + other_deductions  [Sch S Part B L41]"),
     "inputs": ["us_obligation_interest", "ss_rr_benefits", "bailey_retirement", "military_retirement",
                "depr_recovery_bonus", "depr_recovery_179", "other_deductions"], "outputs": ["L9"], "sort_order": 12,
     "description": "Dec C. Structured Part B subtractions (L18-21 retirement/US-obligation) + the direct-entry 20% depreciation recovery (L23f/L24f) + other Part B items."},
    {"rule_id": "R-NC-CHILD-DED", "title": "Child deduction (L10b) — AGI-banded per-child × count", "rule_type": "calculation",
     "formula": ("group = MFJ if status in {MFJ,QW} else (HOH if status==HOH else single[covers single,MFS]) ; "
                 "per_child = first per_child where federal_agi <= ceiling (breakpoint → lower/higher-deduction band) ; "
                 "L10b = per_child * num_qualifying_children ; "
                 "MFJ/QW: ≤40k 3000 / ≤60k 2500 / ≤80k 2000 / ≤100k 1500 / ≤120k 1000 / ≤140k 500 / else 0"),
     "inputs": ["filing_status", "federal_agi", "num_qualifying_children"], "outputs": ["L10a", "L10b"], "sort_order": 13,
     "description": "W5. §105-153.5(a1). Booklet p.13. Value exactly at a breakpoint falls in the higher-deduction band."},
    {"rule_id": "R-NC-SCHED-A", "title": "NC itemized deductions (Schedule A) — restricted subset", "rule_type": "calculation",
     "formula": ("prop_tax = min(real_estate_property_tax, 5000 if MFS else 10000) ; "
                 "mort_plus_prop = min(mortgage_interest + prop_tax, 20000) ; "
                 "medical = max(0, medical_dental_expenses - 0.075 * federal_agi) ; "
                 "itemized = mort_plus_prop + charitable_contributions + medical + claim_of_right_repayment  [Sch A L10]"),
     "inputs": ["mortgage_interest", "real_estate_property_tax", "charitable_contributions",
                "medical_dental_expenses", "claim_of_right_repayment", "filing_status", "federal_agi"],
     "outputs": ["itemized"], "sort_order": 14,
     "description": "Booklet p.20. Only mortgage interest + property tax (combined cap $20k; property $10k/$5k MFS) + charitable + medical (less 7.5% AGI) + claim-of-right."},
    {"rule_id": "R-NC-DED-ELECTION", "title": "NC standard OR itemized deduction (L11)", "rule_type": "calculation",
     "formula": ("std = {single:12750, MFJ:25500, QW:25500, HOH:19125, MFS:(0 if spouse_itemizes else 12750)}[status] ; "
                 "L11 = std if deduction_election==standard else R-NC-SCHED-A itemized"),
     "inputs": ["filing_status", "deduction_election", "spouse_itemizes"], "outputs": ["L11"], "sort_order": 15,
     "description": "W4. No age-65/blind add-on. MFS std ded $0 if spouse itemizes. If not eligible for the federal standard deduction, NC std ded is $0."},
    {"rule_id": "R-NC-TAXABLE", "title": "NC taxable base (L12a / L12b)", "rule_type": "calculation",
     "formula": "L12a = L9 + L10b + L11 ; L12b = max(0, L8 - L12a)",
     "inputs": [], "outputs": ["L12a", "L12b"], "sort_order": 16},
    {"rule_id": "R-NC-PN", "title": "Part-year/nonresident taxable percentage (L13) and NC taxable income (L14)", "rule_type": "calculation",
     "formula": ("if is_part_year_or_nr: L13 = round(pn_col_b_total / pn_col_a_total, 4)  [≥0, may exceed 1.0] ; "
                 "L14 = round(L12b * L13) ; else: L14 = L12b"),
     "inputs": ["is_part_year_or_nr", "pn_col_a_total", "pn_col_b_total"], "outputs": ["L13", "L14"], "sort_order": 17,
     "description": "Dec A. Schedule PN L24 = Col B ÷ Col A (4-decimal) → D-400 L13; L14 = L12b × L13. 'May be > 100%, never < 0%.'"},
    {"rule_id": "R-NC-TAX", "title": "NC income tax (L15) — flat 4.25%", "rule_type": "calculation",
     "formula": "L15 = max(0, round(L14 * 0.0425))",
     "inputs": ["is_part_year_or_nr"], "outputs": ["L15"], "sort_order": 18,
     "description": "W1. §105-153.7. Flat 4.25% (0.0425) on L14; if zero or less, 0."},
    {"rule_id": "R-NC-NET-TAX", "title": "Credits (L16), net tax (L17), and total after use tax (L19)", "rule_type": "calculation",
     "formula": "L17 = max(0, L15 - tax_credits_d400tc) ; L19 = L17 + consumer_use_tax",
     "inputs": ["tax_credits_d400tc", "consumer_use_tax"], "outputs": ["L17", "L19"], "sort_order": 19,
     "description": "Dec D: D-400TC credits + consumer use tax direct-entry."},
    {"rule_id": "R-NC-PAYMENTS", "title": "Total payments (L23) and refund/owe (L27/L34)", "rule_type": "calculation",
     "formula": ("L23 = nc_withholding + other_payments ; "
                 "if L19 > L23: L27 amount due = L19 - L23 ; "
                 "else: L28 overpayment = L23 - L19 ; L34 refund = L28 - contributions"),
     "inputs": ["nc_withholding", "other_payments", "contributions"], "outputs": ["L23", "L27", "L28", "L34"], "sort_order": 20},
]

NCD400_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-NC-DEPR-ADDBACK", "NC_2025_SCHEDULE_S", "primary", "bonus/§179 85% add-back mechanics, Sch S L3/L4"),
    ("R-NC-DEPR-ADDBACK", "NC_GS_105_153_6", "secondary", "statutory basis for the add-back + 20% recovery (W6)"),
    ("R-NC-ADDITIONS", "NC_2025_SCHEDULE_S", "primary", "Part A additions → D-400 L7"),
    ("R-NC-DEDUCTIONS", "NC_2025_SCHEDULE_S", "primary", "Part B deductions → D-400 L9"),
    ("R-NC-DEDUCTIONS", "NC_2025_D401_INSTRUCTIONS", "secondary", "Bailey/military/SS/US-obligation deduction eligibility"),
    ("R-NC-CHILD-DED", "NC_2025_FORM_D400", "primary", "child-deduction AGI-banded table, booklet p.13"),
    ("R-NC-SCHED-A", "NC_2025_D401_INSTRUCTIONS", "primary", "NC itemized deductions restricted subset, booklet p.20"),
    ("R-NC-DED-ELECTION", "NC_2025_FORM_D400", "primary", "standard deduction chart, booklet p.14"),
    ("R-NC-PN", "NC_2025_D401_INSTRUCTIONS", "primary", "Schedule PN L24 proration → D-400 L13/L14"),
    ("R-NC-TAX", "NC_GS_105_153_7", "primary", "flat 4.25% rate, §105-153.7 / D-400 L15"),
    ("R-NC-TAX", "NC_2025_FORM_D400", "secondary", "line 15 'multiply by 4.25% (0.0425)'"),
    ("R-NC-TAXABLE", "NC_2025_FORM_D400", "primary", "L12a = L9+L10b+L11; L12b = L8−L12a (form face arithmetic)"),
    ("R-NC-NET-TAX", "NC_2025_FORM_D400", "primary", "L17 = L15−L16; L19 = L17+L18 (form face arithmetic)"),
    ("R-NC-PAYMENTS", "NC_2025_FORM_D400", "primary", "L23 payments; L27 due / L28 overpayment / L34 refund (form face arithmetic)"),
]

NCD400_LINES: list[dict] = [
    {"line_number": "6", "description": "Federal adjusted gross income", "line_type": "input", "source_facts": ["federal_agi"], "sort_order": 1},
    {"line_number": "7", "description": "Additions to federal AGI (Schedule S Part A)", "line_type": "subtotal", "source_rules": ["R-NC-ADDITIONS"], "sort_order": 2},
    {"line_number": "8", "description": "Add lines 6 and 7", "line_type": "subtotal", "source_rules": ["R-NC-ADDITIONS"], "sort_order": 3},
    {"line_number": "9", "description": "Deductions from federal AGI (Schedule S Part B)", "line_type": "subtotal", "source_rules": ["R-NC-DEDUCTIONS"], "sort_order": 4},
    {"line_number": "10a", "description": "Number of qualifying children", "line_type": "input", "source_facts": ["num_qualifying_children"], "sort_order": 5},
    {"line_number": "10b", "description": "Child deduction", "line_type": "calculated", "calculation": "R-NC-CHILD-DED", "source_rules": ["R-NC-CHILD-DED"], "sort_order": 6},
    {"line_number": "11", "description": "NC standard or NC itemized deduction", "line_type": "calculated", "source_rules": ["R-NC-DED-ELECTION"], "sort_order": 7},
    {"line_number": "12a", "description": "Add lines 9, 10b, and 11", "line_type": "subtotal", "source_rules": ["R-NC-TAXABLE"], "sort_order": 8},
    {"line_number": "12b", "description": "Subtract line 12a from line 8", "line_type": "subtotal", "source_rules": ["R-NC-TAXABLE"], "sort_order": 9},
    {"line_number": "13", "description": "Part-year/nonresident taxable percentage (Schedule PN)", "line_type": "calculated", "source_rules": ["R-NC-PN"], "sort_order": 10},
    {"line_number": "14", "description": "North Carolina taxable income", "line_type": "calculated", "source_rules": ["R-NC-PN"], "sort_order": 11},
    {"line_number": "15", "description": "North Carolina income tax (4.25%)", "line_type": "calculated", "calculation": "R-NC-TAX", "source_rules": ["R-NC-TAX"], "sort_order": 12},
    {"line_number": "16", "description": "Tax credits (D-400TC) — direct-entry", "line_type": "input", "source_facts": ["tax_credits_d400tc"], "sort_order": 13},
    {"line_number": "17", "description": "Subtract line 16 from line 15", "line_type": "calculated", "source_rules": ["R-NC-NET-TAX"], "sort_order": 14},
    {"line_number": "18", "description": "Consumer use tax — direct-entry", "line_type": "input", "source_facts": ["consumer_use_tax"], "sort_order": 15},
    {"line_number": "19", "description": "Add lines 17 and 18", "line_type": "subtotal", "source_rules": ["R-NC-NET-TAX"], "sort_order": 16},
    {"line_number": "20", "description": "North Carolina income tax withheld", "line_type": "input", "source_facts": ["nc_withholding"], "sort_order": 17},
    {"line_number": "23", "description": "Total payments", "line_type": "subtotal", "source_rules": ["R-NC-PAYMENTS"], "sort_order": 18},
    {"line_number": "27", "description": "Amount due", "line_type": "total", "source_rules": ["R-NC-PAYMENTS"], "sort_order": 19},
    {"line_number": "28", "description": "Overpayment", "line_type": "subtotal", "source_rules": ["R-NC-PAYMENTS"], "sort_order": 20},
    {"line_number": "34", "description": "Amount to be refunded", "line_type": "total", "source_rules": ["R-NC-PAYMENTS"], "sort_order": 21},
]

NCD400_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_NCD400_DEPR", "title": "NC bonus/§179 depreciation add-back is 85% (NC decouples from federal)", "severity": "info",
     "condition": "federal bonus depreciation or excess §179 present", "message": "NC did not adopt IRC §168(k)/(n) bonus or the increased §179. Add back 85% of federal bonus (L3) and 85% of the §179 excess over NC's $25,000/$200,000 limits (L4). The 20% recovery of a TY2025 add-back begins on the TY2026 return; prior-year (2020-2024) installments are direct-entry (L23f/L24f).",
     "notes": "Dec B / W2. Ken's specialty. Conformity frozen at Jan 1, 2023."},
    {"diagnostic_id": "D_NCD400_179LIMIT", "title": "§179 investment exceeds NC's $200,000 threshold", "severity": "warning",
     "condition": "sec179_property_cost > 200000", "message": "NC's $25,000 §179 limit phases down dollar-for-dollar once §179 property placed in service exceeds $200,000. The spec uses min(federal §179, $25,000) for nc_sec179; verify the phased NC limit against the asset-level cost before locking the add-back.",
     "notes": "W2. Asset-level cost not always reachable; flagged not silently computed."},
    {"diagnostic_id": "D_NCD400_MFS_STDDED", "title": "MFS standard deduction is $0 if the spouse itemizes", "severity": "warning",
     "condition": "filing_status == MFS and deduction_election == standard", "message": "If married filing separately and your spouse claims NC itemized deductions, your NC standard deduction is $0. Confirm the spouse_itemizes flag.",
     "notes": "W4."},
    {"diagnostic_id": "D_NCD400_BAILEY", "title": "Bailey Settlement / military retirement deduction eligibility", "severity": "info",
     "condition": "bailey_retirement or military_retirement present", "message": "Bailey (L20): vested NC state/local/federal (incl. military) retiree with 5+ years creditable service as of Aug 12, 1989 — fully deductible. Military (L21): 20+ years (or medical) uniformed-services retiree, if not already under Bailey. Do not double-count L20 and L21.",
     "notes": "Dec C. Common NC retiree deductions."},
    {"diagnostic_id": "D_NCD400_PN1", "title": "Schedule PN-1 (other additions/deductions) — prepare manually", "severity": "info",
     "condition": "part-year/nonresident with Schedule S items lacking a PN line", "message": "Schedule PN-1 carries Schedule-S additions/deductions without a dedicated Schedule PN line (→ PN L17e/L19h). It is not computed in v1 — prepare Schedule PN-1 manually.",
     "notes": "Dec D RED-defer."},
    {"diagnostic_id": "D_NCD400_AMENDED", "title": "Amended return (lines 22/24, Schedule AM) — prepare manually", "severity": "info",
     "condition": "amended return", "message": "The amended-return additional-payments (L22) / previous-refunds (L24) lines and Schedule AM are not computed in v1 — prepare an amended return manually.",
     "notes": "Dec D RED-defer."},
    {"diagnostic_id": "D_NCD400_D422", "title": "Estimated-tax underpayment interest (L26e, Form D-422) — prepare manually", "severity": "info",
     "condition": "underpayment of estimated tax", "message": "The line 26e interest on the underpayment of estimated income tax (Form D-422) is not computed in v1 — prepare Form D-422 manually.",
     "notes": "Dec D RED-defer."},
    {"diagnostic_id": "D_NCD400_NOL", "title": "NC net operating loss (Schedule S L39) — prepare manually", "severity": "info",
     "condition": "NC NOL claimed", "message": "The NC net operating loss deduction (Schedule S Part B line 39) is not computed in v1 — prepare the NC NOL manually.",
     "notes": "Dec D RED-defer."},
]

NCD400_SCENARIOS: list[dict] = [
    {"scenario_name": "Single resident, standard deduction, no children", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"filing_status": "single", "federal_agi": 60000, "deduction_election": "standard", "num_qualifying_children": 0, "is_part_year_or_nr": False},
     "expected_outputs": {"L8": 60000, "L11": 12750, "L12b": 47250, "L14": 47250, "L15": 2008},
     "notes": "L8=60000; std ded single=12750; L12a=12750; L12b=47250; L14=47250; L15=round(47250×0.0425)=round(2008.125)=2008."},
    {"scenario_name": "MFJ with two children, standard deduction", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"filing_status": "MFJ", "federal_agi": 90000, "deduction_election": "standard", "num_qualifying_children": 2, "is_part_year_or_nr": False},
     "expected_outputs": {"L10b": 3000, "L11": 25500, "L12b": 61500, "L15": 2614},
     "notes": "MFJ AGI 90000 → child band 80,001-100,000 = $1,500/child × 2 = 3000; std ded 25500; L12a=0+3000+25500=28500; L12b=90000-28500=61500; L15=round(61500×0.0425)=round(2613.75)=2614."},
    {"scenario_name": "Bonus + §179 depreciation add-back (85%)", "scenario_type": "edge", "sort_order": 3,
     "inputs": {"filing_status": "single", "federal_agi": 200000, "federal_bonus_depreciation": 100000, "federal_sec179_deduction": 100000, "other_additions": 0, "deduction_election": "standard"},
     "expected_outputs": {"L3": 85000, "L4": 63750, "L7": 148750, "L8": 348750},
     "notes": "L3=round(0.85×100000)=85000; nc_sec179=min(100000,25000)=25000; L4=round(0.85×(100000−25000))=round(63750)=63750; L7=85000+63750=148750; L8=200000+148750=348750."},
    {"scenario_name": "Part-year resident — Schedule PN proration", "scenario_type": "edge", "sort_order": 4,
     "inputs": {"filing_status": "single", "federal_agi": 60000, "deduction_election": "standard", "is_part_year_or_nr": True, "pn_col_a_total": 100000, "pn_col_b_total": 40000},
     "expected_outputs": {"L12b": 47250, "L13": 0.4, "L14": 18900, "L15": 803},
     "notes": "L12b=47250 (as scenario 1); L13=40000/100000=0.4000; L14=round(47250×0.4)=18900; L15=round(18900×0.0425)=round(803.25)=803."},
    {"scenario_name": "NC itemized deductions (Schedule A cap)", "scenario_type": "edge", "sort_order": 5,
     "inputs": {"filing_status": "single", "federal_agi": 60000, "deduction_election": "itemized", "mortgage_interest": 12000, "real_estate_property_tax": 8000, "charitable_contributions": 5000, "medical_dental_expenses": 10000},
     "expected_outputs": {"L11": 30500},
     "notes": "prop_tax=min(8000,10000)=8000; mort+prop=min(12000+8000,20000)=20000; medical=max(0,10000−0.075×60000)=max(0,10000−4500)=5500; itemized=20000+5000+5500=30500 → L11=30500 (> 12750 std)."},
    {"scenario_name": "MFS, spouse itemizes → NC standard deduction $0", "scenario_type": "edge", "sort_order": 6,
     "inputs": {"filing_status": "MFS", "federal_agi": 50000, "deduction_election": "standard", "spouse_itemizes": True},
     "expected_outputs": {"L11": 0, "L12b": 50000},
     "notes": "MFS with spouse itemizing → NC std ded $0; L12a=0; L12b=50000−0=50000."},
    {"scenario_name": "Structured Schedule S Part B subtractions (Bailey/SS/US-obligation)", "scenario_type": "normal", "sort_order": 7,
     "inputs": {"filing_status": "MFJ", "federal_agi": 100000, "deduction_election": "standard", "bailey_retirement": 30000, "ss_rr_benefits": 20000, "us_obligation_interest": 1000},
     "expected_outputs": {"L9": 51000, "L8": 100000, "L12b": 23500},
     "notes": "L9=30000+20000+1000=51000; L8=100000; L12a=51000+0+25500=76500; L12b=100000−76500=23500."},
    {"scenario_name": "Child deduction breakpoint falls in the higher band (MFJ at $40,000)", "scenario_type": "edge", "sort_order": 8,
     "inputs": {"filing_status": "MFJ", "federal_agi": 40000, "deduction_election": "standard", "num_qualifying_children": 1},
     "expected_outputs": {"L10b": 3000},
     "notes": "MFJ AGI exactly 40000 → the '≤40,000' band = $3,000/child (breakpoint falls in the LOWER/higher-deduction band). L10b=3000×1=3000."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORMS registry + flow assertions
# ═══════════════════════════════════════════════════════════════════════════

FORMS: list[dict] = [
    {
        "identity": {"form_number": "NC_D400", "form_title": "NC D-400 — North Carolina Individual Income Tax Return (TY2025)",
                     "notes": "4th state individual spec. Federal-AGI start (like GA-500); flat 4.25% rate; Schedule S 85% bonus/§179 add-back + 20%/5-year recovery; child-deduction AGI table; structured Part B retirement subtractions; Schedule PN part-year/nonresident. v1 covers resident + part-year/nonresident."},
        "facts": NCD400_FACTS, "rules": NCD400_RULES, "rule_links": NCD400_RULE_LINKS,
        "lines": NCD400_LINES, "diagnostics": NCD400_DIAGNOSTICS, "scenarios": NCD400_SCENARIOS,
    },
]

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-NC-FEDAGI-START", "title": "NC D-400 starts from federal AGI (line 6)", "assertion_type": "flow_assertion",
     "entity_types": ["1040"], "status": "draft", "sort_order": 1,
     "description": "D-400 line 6 = federal AGI (1040). NC taxable income builds by Schedule S additions (L7) and deductions (L9), not a from-scratch income build.",
     "definition": {"rule": "R-NC-ADDITIONS", "check": "L6 = federal_agi ; L8 = L6 + Sch S Part A total"}},
    {"assertion_id": "FA-NC-DEPR-ADDBACK", "title": "NC adds back 85% of federal bonus + 85% of the §179 excess", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "draft", "sort_order": 2,
     "description": "Schedule S Part A L3 = 85% × federal bonus depreciation; L4 = 85% × (federal §179 − NC §179 at $25k/$200k). NC decouples from IRC §168(k)/(n) + the increased §179.",
     "definition": {"rule": "R-NC-DEPR-ADDBACK", "check": "L3 = round(0.85 * federal_bonus) ; L4 = round(0.85 * max(0, federal_179 - min(federal_179, 25000)))"}},
    {"assertion_id": "FA-NC-FLAT-RATE", "title": "NC income tax = NC taxable income × 4.25%", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "draft", "sort_order": 3,
     "description": "D-400 line 15 = line 14 × 4.25% (0.0425), floored at 0. Flat rate, §105-153.7.",
     "definition": {"rule": "R-NC-TAX", "check": "L15 = max(0, round(L14 * 0.0425))"}},
    {"assertion_id": "FA-NC-PN-PRORATION", "title": "Part-year/nonresident tax prorated by Schedule PN percentage", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "draft", "sort_order": 4,
     "description": "When is_part_year_or_nr, D-400 line 14 = line 12b × the Schedule PN line 24 decimal (Col B ÷ Col A, 4-decimal, ≥ 0, may exceed 1.0).",
     "definition": {"rule": "R-NC-PN", "check": "L14 = round(L12b * round(pn_col_b_total / pn_col_a_total, 4))"}},
]


# ═══════════════════════════════════════════════════════════════════════════
# Command
# ═══════════════════════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = (
        "Load the NC D-400 spec (North Carolina Individual Income Tax, TY2025). "
        "Refuses to seed until Ken sets READY_TO_SEED=True after the in-session review walk (W1-W6)."
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad NC D-400 spec (North Carolina Individual Income Tax)\n"))
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
                "\nREFUSING TO SEED NC D-400: not cleared to seed.\n\n"
                "Content is authored, but seeding is gated until Ken reviews the packet\n"
                "(W1 the flat 4.25% rate; W2 the 85% add-back + $25k/$200k §179 limits; W3\n"
                "the Jan 1 2023 conformity date; W4 the standard deduction; W5 the child-\n"
                "deduction table; W6 the statutory-text provenance) and flips the sentinel.\n\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True to proceed)\n\n"
                f"Currently empty / placeholder:\n  {still_empty}\n\n"
                "To proceed: review the module-level data lists (and nc_d400_source_brief.md),\n"
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
        self.stdout.write("NC D-400 loaded.")
        self.stdout.write(
            f"  NC_D400: facts {len(NCD400_FACTS)} / rules {len(NCD400_RULES)} / lines {len(NCD400_LINES)} / "
            f"diag {len(NCD400_DIAGNOSTICS)} / tests {len(NCD400_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}"
        )
        self.stdout.write("=" * 60)
