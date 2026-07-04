"""AMEND the Form 3800 spec — the 1040-side General Business Credit build (S4 arc).

AMEND-BY-LOOKUP (the shared-multi-entity-form rule): Form 3800 ALREADY EXISTS in RS
(the 1120-S-era draft — entity_types ["1120S","1065","1120","1040"], 4 rules R001-R004
oriented at S-corp K-1-box-13 pass-through, a 10-line generic line_map, 2 diagnostics,
2 entity tests). This loader LOOKS UP that form and ADDS the 1040 side:

  KEPT untouched: entity_types; R001 (S-corp passes credits through, no entity-level
    GBC), R002 (§39 carryback 1 / carryforward 20), R003 (K-1 box 13 type codes);
    D001/D002; the 2 entity pass-through test scenarios.
  UPDATED in place: R004 (the §38(c)(1) limitation) — restated against the REAL 2025
    face lines (11/13/14/15/16/17; the old text predates the redesigned form); the
    colliding line_map keys ("2".."7", "38") — overwritten with the 2025 face meanings.
  DELETED: the stale sketch lines "1a"/"1b"/"1c" (no 2025-face counterpart; the old
    10-line map was a generic pre-redesign sketch, wrong against any published face).

SCOPE (Ken's four rulings, AskUserQuestion 2026-07-04, all on the recommended options):
  J1 Part III rows = the BUILT FEEDERS + catch-alls: 1f/4e (Form 8835 Part II — routed
     by R-8835-ROUTE's §38(c)(4)(B)(iv) 4-year placed-in-service window), 1s (Form 8911
     Part I — retires tts D_8911_004), 1y/1aa (Form 8936 Parts II/V — softens tts
     D_8936_003 back to the spec's info), plus 1zz/4z "other credits" direct-entry
     catch-alls (K-1 GBC passthroughs land there, source form noted). NOT the full
     30-row catalog.
  J2 PASSIVE split = per-inflow preparer assertion (nullable; the 8911 census-tract
     convention): None/unanswered -> the inflow is EXCLUDED + D_3800_002 RED (never
     silently over-allow — the penalty-drawing direction); True/passive -> column (d),
     D_3800_003 RED (Form 8582-CR unbuilt), lines 3/33 stay direct-entry escape
     hatches; False/nonpassive -> column (e).
  J3 CARRYFORWARD = two direct-entry in-buckets (regular -> Part I line 4; specified ->
     Part II line 34; D_3800_006 verify-against-prior-return warning until the proforma
     producer exists) + a COMPUTED carryforward-out (D_3800_005 info + statement page
     with the regular/specified decomposition and the i3800 ordering note). The full
     Part IV per-credit/per-year FIFO grid is deferred to the proforma track. Lines
     5/35 (carrybacks FROM 2026) = 0 in v1 — a carryback is claimed on an AMENDED
     return, not computed here.
  J4 §6417 EPE / §6418 TRANSFERS = OUT (columns f/h/j blank; header question B unused;
     Parts V-VII not modeled); an asserted election fires D_3800_004 RED "prepare
     manually". The 8936 DEALER transfer (§30D(g)) is a different mechanism, already
     built on the 8936 spec.
  Also v1: Part II Section B (the §38(c)(2) empowerment-zone credit, lines 18-26)
     computes ZEROS (no Form 8844 anywhere in the engine; the face's own skip note
     governs); Section C is REQUIRED (the S4 8835 credit is specified via the 4-year
     window).

VERIFIED against primary sources fetched 2026-07-04 (never training memory):
  - 2025 Form 3800 (f3800.pdf, Cat. 12392F, Attach. Seq. 22, Created 8/19/25; sha256
    cdfb169a69206370955214883611058e5d31ec89542e14cb7dccebdb7feef555) — the full
    9-page face extracted; Parts I/II line texts + the Part III row labels below are
    verbatim transcriptions.
  - 2025 Instructions for Form 3800 (i3800.pdf, 13 pp) — the line-10b credit list,
    the lines-4a-4z specified note, and the carryback/carryforward ordering, verbatim.
  - 26 U.S.C. §38(c)(4)(A)-(B) — fetched verbatim (Cornell LII) incl. clause (iv):
    the §45 credit is "specified" for electricity produced "(I) at a facility which
    is originally placed in service after the date of the enactment of this
    paragraph, and (II) during the 4-year period beginning on the date that such
    facility was originally placed in service."

requires_human_review WALK ITEMS (present to Ken before flipping the sentinel):
  W1. The STALE-LINE REPLACEMENT: this loader deletes "1a"/"1b"/"1c" and overwrites
      "2".."7"/"38" with the 2025 face meanings — confirm replacing the 1120-S-era
      sketch is right (the entity RULES R001-R003 are kept; only the line grid turns
      face-real).
  W2. UNANSWERED passive assertion -> the inflow is EXCLUDED (+RED), not defaulted
      nonpassive — the no-silent-overstatement direction; every 3800 return answers
      one question per credit source.
  W3. The line-10b list mirrors the Form 8911 line-6b "Ken-approved ordering reading":
      1040 line 19 + Schedule 3 lines 2-4, 5a, 5b + the line-7 (6a-6z) components
      EXCLUDING 6a (the GBC itself), 6b (prior-year min tax), 6k (Form 8912 bonds) —
      i3800 verbatim below.
  W4. The S4 consequence (counterintuitive, worth blessing): Sarah's ~$2.2k tax is
      fully absorbed by the 8936 personal credit BEFORE the GBC (line 10b includes
      Schedule 3 line 6f), so line 11 = 0 and the ENTIRE $13,200 solar credit carries
      forward — Schedule 3 line 6a stays blank. That ordering is statutory, not
      elective (F3800-S4 pins it).

Safety guard
------------
`READY_TO_SEED = False`. Ken walks W1-W4 + the scope rulings, flips the sentinel,
then we seed. DO NOT relax the guard to silence the error.
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
# SAFETY GUARD — flip ONLY after Ken's in-session review walk (W1-W4 above).
# ═══════════════════════════════════════════════════════════════════════════

# FLIPPED 2026-07-04 — Ken approved the review walk in-session (AskUserQuestion,
# "Approve — flip, seed, build"): W1 the stale-grid replacement (entity rules
# R001-R003 kept), W2 unanswered-passive-excludes (+RED), W3 the line-10b list
# (the Form 8911 line-6b reading), W4 the S4 all-carries outcome (the 8936
# personal credit absorbs the tax first; Sch 3 6a blank; $13,200 carries).
# The J1-J4 scope was ruled the same session (all recommended options).
READY_TO_SEED = True


FORM_NUMBER = "3800"
FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1

# The stale 1120-S-era sketch lines with NO 2025-face counterpart — deleted.
STALE_LINES_TO_DELETE = ["1a", "1b", "1c"]


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS (every value cited; never training memory)
# ═══════════════════════════════════════════════════════════════════════════

SEC38C1_THRESHOLD = 25000     # §38(c)(1)(B): 25% of net regular tax over $25,000
SEC38C1_RATE = "0.25"
SEC38C2_TMT_FACTOR = "0.75"   # line 18 (Section B): 75% of TMT — v1 zeros anyway
CARRYBACK_YEARS = 1           # §39(a)(1)(A)
CARRYFORWARD_YEARS = 20       # §39(a)(1)(B)
# §38(c)(4)(B)(iv): the §45 credit is SPECIFIED for the PIS year + the 4-year
# window from original placed-in-service (facility PIS after 8/8/2005). The
# window MATH lives in R-8835-ROUTE (the source form decides 1f vs 4e); this
# spec consumes the routed row.
SEC45_SPECIFIED_WINDOW_YEARS = 4


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY TOPICS + SOURCES
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("form_3800", "Form 3800 — General Business Credit aggregation, §38(c) limitations, §39 carryovers"),
]

# Existing sources this amendment adds excerpts to / links against.
EXISTING_SOURCES_TO_REFERENCE: list[str] = ["IRS_2025_3800_INSTR", "IRC_38"]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_3800_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Form 3800 — General Business Credit",
        "citation": "Form 3800 (2025); f3800.pdf; Attachment Sequence No. 22; Cat. No. 12392F; Created 8/19/25",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f3800.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": "FINAL 2025 face (9 pages, post-IRA redesign). Parts I/II line texts + Part III row labels transcribed verbatim 2026-07-04. sha256 cdfb169a...f555.",
        "topics": ["form_3800"],
        "excerpts": [
            {
                "excerpt_label": "Part I + Part II Section A — the §38(c)(1) chain (verbatim)",
                "location_reference": "Form 3800 (2025), page 1",
                "excerpt_text": (
                    "Part I, Credits Not Allowed Against Tentative Minimum Tax (TMT). Complete applicable "
                    "portions of Parts III and IV before Parts I and II. 1 Credits not subject to the passive "
                    "activity limit from Part III, line 2: combine column (e) with non-passive amounts from "
                    "column (f). 2 Credits subject to the passive activity limit. Combine Part III, line 2, "
                    "column (d), and passive amounts included in line 2, column (f); and Part IV, line 6, "
                    "column (d). 3 Enter the portion of line 2 allowed for 2025. 4 Enter the portion of Part "
                    "IV, line 6, column (f), that is from carryforwards to 2025. 5 Enter the portion of Part "
                    "IV, line 6, column (f), that is from carrybacks from 2026. 6 Add lines 1, 3, 4, and 5. "
                    "Part II Section A: 7 Regular tax before credits: Individuals. Enter the sum of the "
                    "amounts from Form 1040, 1040-SR, or 1040-NR, line 16; and Schedule 2 (Form 1040), line "
                    "1z. 8 Alternative minimum tax: Individuals. Enter the amount from Form 6251, line 11. 9 "
                    "Add lines 7 and 8. 10a Foreign tax credit. 10b Certain allowable credits (see "
                    "instructions). 10c Add lines 10a and 10b. 11 Net income tax. Subtract line 10c from line "
                    "9. If zero, skip lines 12 through 15 and enter -0- on line 16. 12 Net regular tax. "
                    "Subtract line 10c from line 7. If zero or less, enter -0-. 13 Enter 25% (0.25) of the "
                    "excess, if any, of line 12 (line 11 for corporations) over $25,000. 14 Tentative minimum "
                    "tax: Individuals. Enter the amount from Form 6251, line 9. 15 Enter the greater of line "
                    "13 or line 14. 16 Subtract line 15 from line 11. If zero or less, enter -0-. 17 Enter "
                    "the smaller of line 6 or line 16. This is the amount of your credit allowed after the "
                    "limitation of section 38(c)(1)."
                ),
                "summary_text": (
                    "Part I: 1 nonpassive current-year, 2 passive, 3 passive allowed, 4 CF-in, 5 CB-in, "
                    "6 = 1+3+4+5. Section A: 7 = 1040 L16 + Sch 2 1z; 8 = AMT (6251 L11); 11 = 9 - 10c; "
                    "13 = 25% x (12 - 25,000)+; 14 = TMT (6251 L9); 15 = max(13,14); 16 = (11-15)+; "
                    "17 = min(6, 16)."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part II Sections B/C/D — Section B skip note, §38(c)(4) chain, line 38 destination (verbatim)",
                "location_reference": "Form 3800 (2025), page 2",
                "excerpt_text": (
                    "Section B: Note: If you are not required to report any amounts on line 22 or line 24 "
                    "below, skip lines 18 through 25 and enter -0- on line 26. Section C, Figuring the "
                    "Specified Credit Amount Allowed Under Section 38(c)(4): 27 Subtract line 13 from line "
                    "11. If zero or less, enter -0-. 28 Add lines 17 and 26. 29 Subtract line 28 from line "
                    "27. If zero or less, enter -0-. 30 Enter the general business credit from line 5 of Part "
                    "III: combine column (e) with non-passive amounts in column (f). 32 Passive activity "
                    "credits from line 5 of Part III ... 33 Enter the applicable passive activity credits "
                    "allowed for 2025. 34 Carryforward of business credit to 2025. 35 Carryback of business "
                    "credit from 2026. 36 Add lines 30, 33, 34, and 35. 37 Enter the smaller of line 29 or "
                    "line 36. This is the amount allowed for specified credits. Section D: 38 Credit allowed "
                    "for the current year. Add lines 28 and 37. Report the amount from line 38 ... as "
                    "indicated below or on the applicable line of your return. Individuals. Schedule 3 (Form "
                    "1040), line 6a. Corporations. Form 1120, Schedule J, line 5c. Estates and trusts. Form "
                    "1041, Schedule G, line 2b."
                ),
                "summary_text": (
                    "Section B zeros when no 8844/no line 22/24 amounts (skip note). Section C: 27 = 11-13 "
                    "(TMT zeroed for specified); 29 = 27-28; 36 = 30+33+34+35; 37 = min(29,36). Line 38 = "
                    "28+37 -> Schedule 3 line 6a (individuals)."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part III row labels — the built-feeder rows (verbatim)",
                "location_reference": "Form 3800 (2025), pages 3-4 (Part III)",
                "excerpt_text": (
                    "Part III, Current Year General Business Credits (GBCs). Columns: (a) No. of items; (b) "
                    "Elective payment or transfer registration number; (c) Pass-through or transferor credit "
                    "entity EIN; (d) Credits subject to the passive activity limit, before application of the "
                    "limit; (e) Credits not subject to the passive activity limits; (f) Credit transfer "
                    "election amount; (g) Combine columns (e) and (f) with the credit from column (d) allowed "
                    "after the passive activity limit; (h) Gross elective payment election (EPE) amount; (i) "
                    "Amount of column (g) applied against tax in Part II; (j) Net EPE amount. Rows: 1f Form "
                    "8835, Part II. 1s Form 8911, Part I. 1y Form 8936, Part II. 1aa Form 8936, Part V. 1zz "
                    "Other credits. 2 Add lines 1a-1zz. 3 Form 8844. 4 Specified credits: ... 4e Form 8835, "
                    "Part II. ... 4z Other specified credits. 5 Add lines 4a-4z. 6 Add lines 2, 3, and 5."
                ),
                "summary_text": (
                    "Part III rows verified: 1f/4e = 8835 Part II (regular vs specified); 1s = 8911 Part I; "
                    "1y = 8936 Part II; 1aa = 8936 Part V; 1zz/4z = other. Totals: 2 = sum 1a-1zz; 5 = sum "
                    "4a-4z; 6 = 2+3+5."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
]

# New excerpts ADDED to already-existing sources (amend, never recreate).
NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = [
    (
        "IRS_2025_3800_INSTR",
        {
            "excerpt_label": "Line 10b — the individuals' credit list (verbatim)",
            "location_reference": "2025 Instructions for Form 3800, Line 10b",
            "excerpt_text": (
                "Line 10b. Enter the total allowable credit, if any, from your tax return as follows. "
                "Individuals. Enter the amount from Form 1040, 1040-SR, or 1040-NR, line 19; and Schedule 3 "
                "(Form 1040), lines 2 through 4, 5a, 5b, and 7. Don't include any general business credit "
                "claimed on Form 3800, any credit for prior-year minimum tax, or any credit claimed on Form "
                "8912, Credit to Holders of Tax Credit Bonds."
            ),
            "summary_text": (
                "10b (individuals) = 1040 L19 + Sch 3 lines 2-4, 5a, 5b + line 7's 6a-6z components "
                "EXCLUDING 6a (the GBC itself), 6b (prior-year min tax), 6k (8912 bonds) — the same reading "
                "as Form 8911 line 6b."
            ),
            "is_key_excerpt": True,
        },
    ),
    (
        "IRS_2025_3800_INSTR",
        {
            "excerpt_label": "Carryback/carryforward ordering + the specified-credit carryover rows (verbatim)",
            "location_reference": "2025 Instructions for Form 3800, carryovers + Part IV line 4",
            "excerpt_text": (
                "In general, no unused credit for any year attributable to any credit can be carried back to "
                "any tax year before the first tax year for which that credit was first allowable. ... A "
                "'specified credit' listed in section 38(c)(4)(B) cannot be carried back to any tax year "
                "before the first tax year for which that specified credit was allowed against TMT unless it "
                "is a credit listed in section 6417(b). See Credit Ordering Rule ... Line 4. Lines 4a through "
                "4k are for carryforwards and carrybacks of specified credits identified in section "
                "38(c)(4)(B)."
            ),
            "summary_text": (
                "Carryovers keep their regular-vs-specified character (Part IV line 4 rows = specified "
                "carryovers); the credit ordering rule governs which credits apply first."
            ),
            "is_key_excerpt": True,
        },
    ),
    (
        "IRC_38",
        {
            "excerpt_label": "§38(c)(4)(A)-(B) — specified credits: TMT zeroed + the §45 4-year window (verbatim)",
            "location_reference": "26 U.S.C. §38(c)(4), fetched 2026-07-04 (Cornell LII)",
            "excerpt_text": (
                "(A) In the case of specified credits — (i) this section and section 39 shall be applied "
                "separately with respect to such credits, and (ii) in applying paragraph (1) to such credits "
                "— (I) the tentative minimum tax shall be treated as being zero, and (II) the limitation "
                "under paragraph (1) (as modified by subclause (I)) shall be reduced by the credit allowed "
                "under subsection (a) for the taxable year (other than the specified credits). (B) ... the "
                "term 'specified credits' means — ... (iv) the credit determined under section 45 to the "
                "extent that such credit is attributable to electricity or refined coal produced — (I) at a "
                "facility which is originally placed in service after the date of the enactment of this "
                "paragraph, and (II) during the 4-year period beginning on the date that such facility was "
                "originally placed in service ..."
            ),
            "summary_text": (
                "Specified credits: TMT treated as ZERO and the §38(c)(1) limit reduced by the non-specified "
                "credits allowed (= the face's lines 27/28/29). The §45 credit is specified for the 4-year "
                "window from original placed-in-service (drives the 8835 1f-vs-4e routing)."
            ),
            "is_key_excerpt": True,
        },
    ),
]


# ═══════════════════════════════════════════════════════════════════════════
# FACTS (1040-side; prefix f3800_)
# ═══════════════════════════════════════════════════════════════════════════

FORM_3800_FACTS: list[dict] = [
    {"fact_key": "f3800_ps_8835", "label": "Form 8835 credit passive? (Part III column d/e assertion)",
     "data_type": "boolean", "required": False, "default_value": None, "sort_order": 1,
     "notes": "PER RETURN. Nullable (the 8911 census-tract convention): None = UNANSWERED -> the 8835 "
              "inflow is EXCLUDED + D_3800_002 RED; True = passive -> column (d) + D_3800_003; False = "
              "nonpassive -> column (e). §469 posture of the taxpayer's §45 facility."},
    {"fact_key": "f3800_ps_8911", "label": "Form 8911 business credit passive? (column d/e assertion)",
     "data_type": "boolean", "required": False, "default_value": None, "sort_order": 2,
     "notes": "PER RETURN. Same tri-state convention; gates the 8911 Part I line 3 inflow on row 1s."},
    {"fact_key": "f3800_ps_8936_1y", "label": "Form 8936 business-new credit passive? (column d/e assertion)",
     "data_type": "boolean", "required": False, "default_value": None, "sort_order": 3,
     "notes": "PER RETURN. Same tri-state convention; gates the 8936 line 8 inflow on row 1y."},
    {"fact_key": "f3800_ps_8936_1aa", "label": "Form 8936 commercial credit passive? (column d/e assertion)",
     "data_type": "boolean", "required": False, "default_value": None, "sort_order": 4,
     "notes": "PER RETURN. Same tri-state convention; gates the 8936 line 21 inflow on row 1aa."},
    {"fact_key": "f3800_other_credits_1zz", "label": "Other current-year GBCs (Part III row 1zz, nonpassive)",
     "data_type": "decimal", "required": False, "default_value": "0", "sort_order": 5,
     "notes": "PER RETURN. Direct-entry catch-all (J1) — K-1 GBC passthroughs and unbuilt source forms "
              "land here, nonpassive; note the source form in the workpapers. Passive other credits "
              "belong on 1zz column (d) — v1 routes ALL of 1zz to column (e); a passive other credit "
              "needs the manual line-3 path."},
    {"fact_key": "f3800_other_specified_4z", "label": "Other specified credits (Part III row 4z)",
     "data_type": "decimal", "required": False, "default_value": "0", "sort_order": 6,
     "notes": "PER RETURN. Direct-entry catch-all for §38(c)(4)(B) specified credits not otherwise "
              "modeled (nonpassive)."},
    {"fact_key": "f3800_cf_regular_in", "label": "Carryforward to 2025 — regular GBCs (Part I line 4)",
     "data_type": "decimal", "required": False, "default_value": "0", "sort_order": 7,
     "notes": "PER RETURN (J3). One total, preparer-keyed from the prior-year Form 3800; D_3800_006 "
              "reminds to verify (no proforma yet). The Part IV per-credit/per-year grid is deferred."},
    {"fact_key": "f3800_cf_specified_in", "label": "Carryforward to 2025 — specified credits (line 34)",
     "data_type": "decimal", "required": False, "default_value": "0", "sort_order": 8,
     "notes": "PER RETURN (J3). Specified carryovers keep their character (i3800 Part IV line 4)."},
    {"fact_key": "f3800_passive_allowed_l3", "label": "Passive credits allowed for 2025 (Part I line 3)",
     "data_type": "decimal", "required": False, "default_value": "0", "sort_order": 9,
     "notes": "PER RETURN (J2 escape hatch). Form 8582-CR is NOT built — when a passive inflow exists "
              "the preparer computes 8582-CR manually and enters the allowed portion here (D_3800_003 "
              "explains). 0 while no passive credits."},
    {"fact_key": "f3800_passive_allowed_l33", "label": "Passive specified credits allowed (line 33)",
     "data_type": "decimal", "required": False, "default_value": "0", "sort_order": 10,
     "notes": "PER RETURN (J2 escape hatch). The Section C twin of line 3."},
    {"fact_key": "f3800_has_transfer_epe", "label": "§6417 elective payment / §6418 credit transfer elected? (Y/N)",
     "data_type": "boolean", "required": False, "default_value": "False", "sort_order": 11,
     "notes": "PER RETURN (J4). True -> D_3800_004 RED 'not supported - prepare manually' (columns "
              "f/h/j, header question B, Parts V-VII are out of v1)."},
    {"fact_key": "f3800_allowed_l38", "label": "Line 38 — credit allowed -> Schedule 3 line 6a (output)",
     "data_type": "decimal", "required": False, "default_value": None, "sort_order": 40,
     "notes": "OUTPUT. = line 28 + line 37."},
    {"fact_key": "f3800_cf_out", "label": "Carryforward to 2026 (output; statement + D_3800_005)",
     "data_type": "decimal", "required": False, "default_value": None, "sort_order": 41,
     "notes": "OUTPUT (J3). = (line 6 + line 36) - line 38, decomposed regular/specified on the "
              "statement; 20-year forward (§39). The 1-year carryback is an amended-return path."},
]


# ═══════════════════════════════════════════════════════════════════════════
# RULES (1040-side R-3800-*; R001-R003 entity rules KEPT; R004 UPDATED in place)
# ═══════════════════════════════════════════════════════════════════════════

FORM_3800_RULES: list[dict] = [
    {
        "rule_id": "R-3800-P3-INFLOW",
        "title": "Part III inflow map — the built feeders land on their face rows (J1/J2)",
        "description": (
            "The 1040 engine's GBC sources land on the 2025 face rows: Form 8835 line 15/17 -> row 1f OR "
            "row 4e per the 8835 spec's own R-8835-ROUTE (§38(c)(4)(B)(iv): specified when the tax year is "
            "within the 4-year window from the facility's original placed-in-service date, facility PIS "
            "after 8/8/2005); Form 8911 Part I line 3 -> row 1s; Form 8936 line 8 -> row 1y; Form 8936 "
            "line 21 -> row 1aa; other credits -> rows 1zz/4z (direct entry, nonpassive). Column split per "
            "inflow: the passive assertion (f3800_ps_*) routes column (d) [passive] vs column (e) "
            "[nonpassive]; an UNANSWERED assertion EXCLUDES the inflow + fires D_3800_002 (never a silent "
            "over-allowance). Columns (f)/(h)/(j) are blank in v1 (J4)."
        ),
        "rule_type": "routing", "conditions": {},
        "formula": (
            "row_1f_or_4e = f8835_total_l15 (per f8835_route_3800_line); row_1s = 8911 line 3; row_1y = "
            "8936 line 8; row_1aa = 8936 line 21; row_1zz = f3800_other_credits_1zz; row_4z = "
            "f3800_other_specified_4z. Per inflow: ps is None -> EXCLUDED + D_3800_002; ps True -> col "
            "(d); ps False -> col (e)."
        ),
        "inputs": ["f3800_ps_8835", "f3800_ps_8911", "f3800_ps_8936_1y", "f3800_ps_8936_1aa",
                   "f3800_other_credits_1zz", "f3800_other_specified_4z"],
        "outputs": ["P3-1f", "P3-1s", "P3-1y", "P3-1aa", "P3-1zz", "P3-4e", "P3-4z"],
        "precedence": 1, "exceptions": "", "notes": "",
    },
    {
        "rule_id": "R-3800-P3-TOTALS",
        "title": "Part III totals — line 2 = Σ1a-1zz; line 5 = Σ4a-4z; line 6 = 2 + 3 + 5",
        "description": "Face-verbatim totals. Line 3 (Form 8844 empowerment zone) = 0 in v1 (no 8844 anywhere in the engine).",
        "rule_type": "calculation", "conditions": {},
        "formula": "P3-2 = sum(rows 1a..1zz); P3-3 = 0 (v1); P3-5 = sum(rows 4a..4z); P3-6 = P3-2 + P3-3 + P3-5.",
        "inputs": [], "outputs": ["P3-2", "P3-3", "P3-5", "P3-6"],
        "precedence": 2, "exceptions": "", "notes": "",
    },
    {
        "rule_id": "R-3800-P1",
        "title": "Part I — nonpassive current-year (1), passive (2/3), carryforward-in (4)",
        "description": (
            "Face-verbatim: line 1 = Part III line 2 column (e) [no column-(f) transfer amounts in v1]; "
            "line 2 = Part III line 2 column (d); line 3 = the allowed portion of line 2 (v1: the "
            "preparer-entered f3800_passive_allowed_l3 — Form 8582-CR manual, D_3800_003); line 4 = "
            "f3800_cf_regular_in (J3; the Part IV grid is deferred); line 5 = 0 in v1 (a carryback from "
            "2026 is an amended-return event); line 6 = 1 + 3 + 4 + 5."
        ),
        "rule_type": "calculation", "conditions": {},
        "formula": "L1 = P3-2(e); L2 = P3-2(d); L3 = f3800_passive_allowed_l3; L4 = f3800_cf_regular_in; L5 = 0; L6 = L1 + L3 + L4 + L5.",
        "inputs": ["f3800_passive_allowed_l3", "f3800_cf_regular_in"],
        "outputs": ["1", "2", "3", "4", "5", "6"],
        "precedence": 3, "exceptions": "", "notes": "",
    },
    {
        "rule_id": "R-3800-P2-TAXLIM",
        "title": "Part II Section A — the §38(c)(1) limitation (lines 7-17)",
        "description": (
            "Face-verbatim for individuals: line 7 = 1040 line 16 + Schedule 2 line 1z; line 8 = AMT "
            "(Form 6251 line 11); line 9 = 7 + 8; line 10a = Schedule 3 line 1 (FTC); line 10b = the "
            "i3800 list — 1040 line 19 + Schedule 3 lines 2-4, 5a, 5b + the line-7 (6a-6z) components "
            "EXCLUDING 6a (the GBC itself), 6b (prior-year minimum tax), and 6k (Form 8912) — the same "
            "reading as Form 8911 line 6b (W3); line 10c = 10a + 10b; line 11 = max(0, 9 - 10c) (zero -> "
            "skip 12-15, line 16 = 0); line 12 = max(0, 7 - 10c); line 13 = 25% x max(0, line 12 - "
            "$25,000); line 14 = TMT (Form 6251 line 9, figured EVEN WHEN NO AMT IS OWED — the i8911 "
            "companion convention); line 15 = max(13, 14); line 16 = max(0, 11 - 15); line 17 = min(6, 16)."
        ),
        "rule_type": "calculation", "conditions": {},
        "formula": (
            "L7 = 1040_16 + SCH2_1z; L8 = 6251_11; L9 = L7 + L8; L10a = SCH3_1; L10b = 1040_19 + "
            "SCH3(2,3,4,5a,5b) + SCH3_6x excl (6a,6b,6k); L10c = L10a + L10b; L11 = max(0, L9 - L10c); "
            "L12 = max(0, L7 - L10c); L13 = 0.25 * max(0, L12 - 25000); L14 = 6251_9; L15 = max(L13, "
            "L14); L16 = max(0, L11 - L15); L17 = min(L6, L16)."
        ),
        "inputs": [], "outputs": ["7", "8", "9", "10a", "10b", "10c", "11", "12", "13", "14", "15", "16", "17"],
        "precedence": 4, "exceptions": "", "notes": "",
    },
    {
        "rule_id": "R-3800-P2-SECB",
        "title": "Part II Section B — §38(c)(2) empowerment zone: zeros in v1 (the face's skip note)",
        "description": (
            "Face-verbatim note: 'If you are not required to report any amounts on line 22 or line 24 "
            "below, skip lines 18 through 25 and enter -0- on line 26.' No Form 8844 exists anywhere in "
            "the engine, so lines 22/24 are structurally zero -> 18-25 skipped, line 26 = 0."
        ),
        "rule_type": "calculation", "conditions": {},
        "formula": "L18..L25 = blank (skipped); L26 = 0.",
        "inputs": [], "outputs": ["26"],
        "precedence": 5, "exceptions": "", "notes": "",
    },
    {
        "rule_id": "R-3800-P2-SECC",
        "title": "Part II Section C — the §38(c)(4) specified-credit allowance (TMT zeroed)",
        "description": (
            "§38(c)(4)(A) verbatim: for specified credits 'the tentative minimum tax shall be treated as "
            "being zero' and the §38(c)(1) limit 'shall be reduced by the credit allowed ... other than "
            "the specified credits' — exactly the face's lines 27/28/29. Line 27 = max(0, 11 - 13) [13, "
            "not 15 — TMT is out]; line 28 = 17 + 26; line 29 = max(0, 27 - 28); line 30 = Part III line "
            "5 column (e); line 32 = Part III line 5 column (d) [+ passive specified carryovers — v1 "
            "n/a]; line 33 = f3800_passive_allowed_l33 (the J2 escape hatch); line 34 = "
            "f3800_cf_specified_in; line 35 = 0 in v1; line 36 = 30 + 33 + 34 + 35; line 37 = min(29, 36)."
        ),
        "rule_type": "calculation", "conditions": {},
        "formula": (
            "L27 = max(0, L11 - L13); L28 = L17 + L26; L29 = max(0, L27 - L28); L30 = P3-5(e); L32 = "
            "P3-5(d); L33 = f3800_passive_allowed_l33; L34 = f3800_cf_specified_in; L35 = 0; L36 = L30 + "
            "L33 + L34 + L35; L37 = min(L29, L36)."
        ),
        "inputs": ["f3800_passive_allowed_l33", "f3800_cf_specified_in"],
        "outputs": ["27", "28", "29", "30", "32", "33", "34", "35", "36", "37"],
        "precedence": 6, "exceptions": "", "notes": "",
    },
    {
        "rule_id": "R-3800-ALLOWED",
        "title": "Line 38 = 28 + 37 -> Schedule 3 line 6a (individuals)",
        "description": (
            "Face-verbatim Section D: 'Credit allowed for the current year. Add lines 28 and 37. ... "
            "Individuals. Schedule 3 (Form 1040), line 6a.' The entity side never reaches Part II — "
            "S corporations pass the credits through (R001, kept)."
        ),
        "rule_type": "routing", "conditions": {},
        "formula": "L38 = L28 + L37 -> SCH_3.6a (1040). 1120: Sch J line 5c; 1041: Sch G line 2b.",
        "inputs": [], "outputs": ["38"],
        "precedence": 7, "exceptions": "", "notes": "",
    },
    {
        "rule_id": "R-3800-CF-OUT",
        "title": "Carryforward to 2026 = (6 + 36) - 38, by character (statement + D_3800_005)",
        "description": (
            "J3: the unused GBC carries forward 20 years (§39(a)(1)(B); R002 kept). v1 computes the "
            "TOTAL unused = (line 6 + line 36) - line 38 and decomposes regular vs specified on a "
            "statement page (carryovers keep their character — i3800 Part IV line 4). The i3800 ordering "
            "(carryforwards applied before current-year credits) is NOTED on the statement so next "
            "year's preparer consumes the in-buckets first. The 1-year carryback (§39(a)(1)(A)) is an "
            "amended-return election, not computed."
        ),
        "rule_type": "calculation", "conditions": {},
        "formula": "f3800_cf_out = (L6 + L36) - L38; decompose: regular_unused = L6 - L28-portion, specified_unused = L36 - L37.",
        "inputs": [], "outputs": [],
        "precedence": 8, "exceptions": "", "notes": "",
    },
    # UPDATED IN PLACE (the 1120-S-era R004 — restated against the real 2025 face).
    {
        "rule_id": "R004",
        "title": "Credit limitation formula (§38(c)(1)) — the 2025 face lines",
        "description": (
            "UPDATED 2026-07-04 (the 1040-side amendment): restated against the 2025 face. The GBC "
            "cannot exceed net income tax (line 11) minus the greater of tentative minimum tax (line 14) "
            "or 25% of net regular tax over $25,000 (line 13). Face: line 15 = max(13, 14); line 16 = "
            "max(0, 11 - 15); line 17 = min(line 6, line 16). See R-3800-P2-TAXLIM for the full chain."
        ),
        "rule_type": "calculation", "conditions": {},
        "formula": "credit_allowed_38c1 = min(L6, max(0, L11 - max(L13, L14))) — the face's L15/L16/L17.",
        "inputs": [], "outputs": [],
        "precedence": 3, "exceptions": "", "notes": "Kept rule id from the 1120-S-era draft; content refreshed.",
    },
]

RULE_AUTHORITY_LINKS: list[tuple[str, str, str, str]] = [
    ("R-3800-P3-INFLOW", "IRS_2025_3800_FORM", "primary", "Part III rows 1f/1s/1y/1aa/1zz/4e/4z + columns (d)/(e) — face verbatim"),
    ("R-3800-P3-INFLOW", "IRC_38", "secondary", "§38(c)(4)(B)(iv) — the §45 4-year specified window (consumed via R-8835-ROUTE)"),
    ("R-3800-P3-TOTALS", "IRS_2025_3800_FORM", "primary", "Part III lines 2/5/6 totals — face verbatim"),
    ("R-3800-P1", "IRS_2025_3800_FORM", "primary", "Part I lines 1-6 — face verbatim"),
    ("R-3800-P2-TAXLIM", "IRS_2025_3800_FORM", "primary", "Section A lines 7-17 — face verbatim"),
    ("R-3800-P2-TAXLIM", "IRS_2025_3800_INSTR", "primary", "Line 10b credit list — instructions verbatim"),
    ("R-3800-P2-TAXLIM", "IRC_38", "secondary", "§38(c)(1) — the limitation"),
    ("R-3800-P2-SECB", "IRS_2025_3800_FORM", "primary", "Section B skip note — face verbatim"),
    ("R-3800-P2-SECC", "IRS_2025_3800_FORM", "primary", "Section C lines 27-37 — face verbatim"),
    ("R-3800-P2-SECC", "IRC_38", "primary", "§38(c)(4)(A) — TMT zeroed + limit reduced by non-specified credits"),
    ("R-3800-ALLOWED", "IRS_2025_3800_FORM", "primary", "Section D line 38 destinations — face verbatim"),
    ("R-3800-CF-OUT", "IRS_2025_3800_INSTR", "primary", "Carryover ordering + specified-character rows"),
    ("R-3800-CF-OUT", "IRC_38", "secondary", "§39 via §38 — 1 back / 20 forward (R002 kept)"),
    ("R004", "IRC_38", "primary", "§38(c)(1) — the limitation formula (refreshed)"),
    ("R004", "IRS_2025_3800_FORM", "secondary", "Lines 13/14/15/16/17 — face verbatim"),
]


# ═══════════════════════════════════════════════════════════════════════════
# LINE MAP (2025 face; Part III rows prefixed P3- to avoid Part I/II collisions)
# ═══════════════════════════════════════════════════════════════════════════

_IN, _CALC, _SUB, _TOT = "input", "calculated", "subtotal", "total"

FORM_3800_LINES: list[dict] = [
    # --- Part I (lines "2".."6" overwrite the stale sketch keys) ------------
    {"line_number": "1", "description": "Credits not subject to the passive activity limit (Part III line 2, column (e))", "line_type": _CALC, "source_rules": ["R-3800-P1"]},
    {"line_number": "2", "description": "Credits subject to the passive activity limit (Part III line 2, column (d))", "line_type": _CALC, "source_rules": ["R-3800-P1"]},
    {"line_number": "3", "description": "Portion of line 2 allowed for 2025 (v1: preparer-entered — Form 8582-CR manual)", "line_type": _IN, "source_facts": ["f3800_passive_allowed_l3"], "source_rules": ["R-3800-P1"]},
    {"line_number": "4", "description": "Carryforward of general business credit to 2025 (regular; one total in v1)", "line_type": _IN, "source_facts": ["f3800_cf_regular_in"], "source_rules": ["R-3800-P1"]},
    {"line_number": "5", "description": "Carryback of general business credit from 2026 (v1: 0 — amended-return path)", "line_type": _CALC, "source_rules": ["R-3800-P1"]},
    {"line_number": "6", "description": "Add lines 1, 3, 4, and 5", "line_type": _SUB, "source_rules": ["R-3800-P1"]},
    # --- Part II Section A ---------------------------------------------------
    {"line_number": "7", "description": "Regular tax before credits (1040 line 16 + Schedule 2 line 1z)", "line_type": _CALC, "source_rules": ["R-3800-P2-TAXLIM"]},
    {"line_number": "8", "description": "Alternative minimum tax (Form 6251 line 11)", "line_type": _CALC, "source_rules": ["R-3800-P2-TAXLIM"]},
    {"line_number": "9", "description": "Add lines 7 and 8", "line_type": _SUB, "source_rules": ["R-3800-P2-TAXLIM"]},
    {"line_number": "10a", "description": "Foreign tax credit (Schedule 3 line 1)", "line_type": _CALC, "source_rules": ["R-3800-P2-TAXLIM"]},
    {"line_number": "10b", "description": "Certain allowable credits (1040 line 19 + Sch 3 lines 2-4, 5a, 5b + 6x excl. 6a/6b/6k)", "line_type": _CALC, "source_rules": ["R-3800-P2-TAXLIM"]},
    {"line_number": "10c", "description": "Add lines 10a and 10b", "line_type": _SUB, "source_rules": ["R-3800-P2-TAXLIM"]},
    {"line_number": "11", "description": "Net income tax (line 9 - line 10c; 0 -> skip 12-15, line 16 = 0)", "line_type": _CALC, "source_rules": ["R-3800-P2-TAXLIM"]},
    {"line_number": "12", "description": "Net regular tax (line 7 - line 10c, not < 0)", "line_type": _CALC, "source_rules": ["R-3800-P2-TAXLIM"]},
    {"line_number": "13", "description": "25% of the excess of line 12 over $25,000", "line_type": _CALC, "source_rules": ["R-3800-P2-TAXLIM"]},
    {"line_number": "14", "description": "Tentative minimum tax (Form 6251 line 9 — figured always)", "line_type": _CALC, "source_rules": ["R-3800-P2-TAXLIM"]},
    {"line_number": "15", "description": "Greater of line 13 or line 14", "line_type": _CALC, "source_rules": ["R-3800-P2-TAXLIM"]},
    {"line_number": "16", "description": "Line 11 - line 15 (not < 0)", "line_type": _CALC, "source_rules": ["R-3800-P2-TAXLIM"]},
    {"line_number": "17", "description": "Smaller of line 6 or line 16 — the §38(c)(1) allowed amount", "line_type": _CALC, "source_rules": ["R-3800-P2-TAXLIM", "R004"]},
    # --- Part II Section B (v1 zeros — the face's skip note) -----------------
    {"line_number": "26", "description": "Empowerment zone credit allowed (v1: 0 — no Form 8844; lines 18-25 skipped per the face note)", "line_type": _CALC, "source_rules": ["R-3800-P2-SECB"]},
    # --- Part II Section C ----------------------------------------------------
    {"line_number": "27", "description": "Line 11 - line 13 (not < 0) — §38(c)(4)(A): TMT treated as zero", "line_type": _CALC, "source_rules": ["R-3800-P2-SECC"]},
    {"line_number": "28", "description": "Add lines 17 and 26", "line_type": _SUB, "source_rules": ["R-3800-P2-SECC"]},
    {"line_number": "29", "description": "Line 27 - line 28 (not < 0)", "line_type": _CALC, "source_rules": ["R-3800-P2-SECC"]},
    {"line_number": "30", "description": "Specified credits from Part III line 5, column (e)", "line_type": _CALC, "source_rules": ["R-3800-P2-SECC"]},
    {"line_number": "32", "description": "Passive specified credits (Part III line 5, column (d))", "line_type": _CALC, "source_rules": ["R-3800-P2-SECC"]},
    {"line_number": "33", "description": "Passive specified credits allowed (v1: preparer-entered — 8582-CR manual)", "line_type": _IN, "source_facts": ["f3800_passive_allowed_l33"], "source_rules": ["R-3800-P2-SECC"]},
    {"line_number": "34", "description": "Carryforward of specified credits to 2025", "line_type": _IN, "source_facts": ["f3800_cf_specified_in"], "source_rules": ["R-3800-P2-SECC"]},
    {"line_number": "35", "description": "Carryback of specified credits from 2026 (v1: 0)", "line_type": _CALC, "source_rules": ["R-3800-P2-SECC"]},
    {"line_number": "36", "description": "Add lines 30, 33, 34, and 35", "line_type": _SUB, "source_rules": ["R-3800-P2-SECC"]},
    {"line_number": "37", "description": "Smaller of line 29 or line 36 — the specified-credit allowance", "line_type": _CALC, "source_rules": ["R-3800-P2-SECC"]},
    # --- Section D (overwrites the stale "38") --------------------------------
    {"line_number": "38", "description": "Credit allowed for the current year (28 + 37) -> Schedule 3 line 6a (1040) / 1120 Sch J 5c / 1041 Sch G 2b", "line_type": _TOT, "source_rules": ["R-3800-ALLOWED"], "destination_form": "SCH_3.6a (1040)"},
    # --- Part III (P3- prefix) -------------------------------------------------
    {"line_number": "P3-1f", "description": "Form 8835, Part II (regular — outside the §38(c)(4)(B)(iv) 4-year window)", "line_type": _CALC, "source_rules": ["R-3800-P3-INFLOW"]},
    {"line_number": "P3-1s", "description": "Form 8911, Part I (business/investment refueling credit)", "line_type": _CALC, "source_rules": ["R-3800-P3-INFLOW"]},
    {"line_number": "P3-1y", "description": "Form 8936, Part II (business/investment new clean vehicle)", "line_type": _CALC, "source_rules": ["R-3800-P3-INFLOW"]},
    {"line_number": "P3-1aa", "description": "Form 8936, Part V (qualified commercial clean vehicle)", "line_type": _CALC, "source_rules": ["R-3800-P3-INFLOW"]},
    {"line_number": "P3-1zz", "description": "Other current-year credits (direct entry; K-1 GBC passthroughs — nonpassive)", "line_type": _IN, "source_facts": ["f3800_other_credits_1zz"], "source_rules": ["R-3800-P3-INFLOW"]},
    {"line_number": "P3-2", "description": "Add lines 1a-1zz", "line_type": _SUB, "source_rules": ["R-3800-P3-TOTALS"]},
    {"line_number": "P3-3", "description": "Form 8844 (v1: 0 — not built)", "line_type": _CALC, "source_rules": ["R-3800-P3-TOTALS"]},
    {"line_number": "P3-4e", "description": "Form 8835, Part II (SPECIFIED — inside the 4-year PIS window; the S4 row)", "line_type": _CALC, "source_rules": ["R-3800-P3-INFLOW"]},
    {"line_number": "P3-4z", "description": "Other specified credits (direct entry)", "line_type": _IN, "source_facts": ["f3800_other_specified_4z"], "source_rules": ["R-3800-P3-INFLOW"]},
    {"line_number": "P3-5", "description": "Add lines 4a-4z", "line_type": _SUB, "source_rules": ["R-3800-P3-TOTALS"]},
    {"line_number": "P3-6", "description": "Add lines 2, 3, and 5", "line_type": _TOT, "source_rules": ["R-3800-P3-TOTALS"]},
]


# ═══════════════════════════════════════════════════════════════════════════
# DIAGNOSTICS (D001/D002 entity warnings KEPT; the 1040 family is D_3800_*)
# ═══════════════════════════════════════════════════════════════════════════

FORM_3800_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_3800_001", "title": "General business credit computed", "severity": "info",
     "condition": "line 38 > 0",
     "message": "Form 3800 computed a general business credit of line 38, landing on Schedule 3 line 6a. "
                "Any unused amount carries forward (see the carryforward statement)."},
    {"diagnostic_id": "D_3800_002", "title": "Passive/nonpassive assertion unanswered — credit excluded", "severity": "error",
     "condition": "an inflow exists whose f3800_ps_* assertion is None",
     "message": "A general business credit source has not been classified passive or nonpassive (the §469 "
                "passive activity credit limit applies through Form 8582-CR). Until answered, the credit "
                "is EXCLUDED from Form 3800 — answer the passive-activity question for each credit source."},
    {"diagnostic_id": "D_3800_003", "title": "Passive credits present — Form 8582-CR not supported", "severity": "error",
     "condition": "Part III column (d) total > 0",
     "message": "Not supported — prepare manually: passive-activity general business credits are limited "
                "by Form 8582-CR, which is not built. Compute Form 8582-CR manually and enter the allowed "
                "portion on Form 3800 line 3 (regular) / line 33 (specified); attach the 8582-CR."},
    {"diagnostic_id": "D_3800_004", "title": "§6417/§6418 election — not supported", "severity": "error",
     "condition": "f3800_has_transfer_epe is True",
     "message": "Not supported — prepare manually: an elective-payment (§6417) or credit-transfer (§6418) "
                "election was indicated. Form 3800 columns (f)/(h)/(j), the header question B statement "
                "count, and the Part V-VII breakdowns are not built."},
    {"diagnostic_id": "D_3800_005", "title": "Unused general business credit carries forward", "severity": "info",
     "condition": "(line 6 + line 36) > line 38",
     "message": "Part of the general business credit could not be used this year (the §38(c) limitation). "
                "The unused amount carries forward up to 20 years (§39) — see the carryforward statement "
                "for the regular/specified decomposition. A 1-year carryback is available only by amending "
                "the prior-year return."},
    {"diagnostic_id": "D_3800_006", "title": "Carryforward entered — verify against the prior-year Form 3800", "severity": "warning",
     "condition": "line 4 > 0 or line 34 > 0",
     "message": "A general business credit carryforward was entered (Part I line 4 / line 34). Verify the "
                "amount and its regular-vs-specified character against the prior-year Form 3800 and its "
                "carryforward statement (no automatic proforma yet)."},
]


# ═══════════════════════════════════════════════════════════════════════════
# TEST SCENARIOS (1040-side; the 2 entity pass-through scenarios are KEPT)
# ═══════════════════════════════════════════════════════════════════════════

FORM_3800_TESTS: list[dict] = [
    {"scenario_name": "F3800-S4 — the S4 shape: specified 8835 credit, tax fully absorbed upstream -> all carries",
     "scenario_type": "normal",
     "inputs": {"tax_year": 2025, "P3-4e": 13200, "line_7_regular_tax": 2193, "line_8_amt": 0,
                "line_10a_ftc": 0, "line_10b_other_credits": 2193, "f3800_ps_8835": False,
                "note": "the 8936 personal credit (Sch 3 6f, inside 10b) absorbs the whole tax FIRST"},
     "expected_outputs": {"line_11": 0, "line_16": 0, "line_17": 0, "line_27": 0, "line_29": 0,
                          "line_36": 13200, "line_37": 0, "line_38": 0, "f3800_cf_out": 13200,
                          "sch3_6a": 0, "D_3800_005": True}},
    {"scenario_name": "F3800-T2 — regular (1f-path) credit fully absorbed",
     "scenario_type": "normal",
     "inputs": {"tax_year": 2025, "P3-1f": 15000, "f3800_ps_8835": False, "line_7_regular_tax": 50000,
                "line_8_amt": 0, "line_10a_ftc": 0, "line_10b_other_credits": 0, "line_14_tmt": 0},
     "expected_outputs": {"line_1": 15000, "line_6": 15000, "line_11": 50000, "line_12": 50000,
                          "line_13": 6250, "line_15": 6250, "line_16": 43750, "line_17": 15000,
                          "line_38": 15000}},
    {"scenario_name": "F3800-T3 — the TMT binds a regular credit; the excess carries",
     "scenario_type": "normal",
     "inputs": {"tax_year": 2025, "P3-1s": 50000, "f3800_ps_8911": False, "line_7_regular_tax": 100000,
                "line_8_amt": 0, "line_10b_other_credits": 0, "line_14_tmt": 60000},
     "expected_outputs": {"line_11": 100000, "line_13": 18750, "line_15": 60000, "line_16": 40000,
                          "line_17": 40000, "line_38": 40000, "f3800_cf_out": 10000, "D_3800_005": True}},
    {"scenario_name": "F3800-T4 — §38(c)(4)(A) teeth: the SAME credit as SPECIFIED ignores the TMT",
     "scenario_type": "normal",
     "inputs": {"tax_year": 2025, "P3-4e": 50000, "f3800_ps_8835": False, "line_7_regular_tax": 100000,
                "line_8_amt": 0, "line_10b_other_credits": 0, "line_14_tmt": 60000,
                "note": "identical posture to T3 but the credit is specified — TMT treated as zero"},
     "expected_outputs": {"line_17": 0, "line_27": 81250, "line_28": 0, "line_29": 81250,
                          "line_36": 50000, "line_37": 50000, "line_38": 50000,
                          "delta_vs_T3": 10000}},
    {"scenario_name": "F3800-T5 — passive gates: unanswered excluded; asserted passive REDs + escape hatch",
     "scenario_type": "edge_case",
     "inputs": {"tax_year": 2025, "P3-1y": 8000, "f3800_ps_8936_1y": None,
                "then_asserted_passive": True, "f3800_passive_allowed_l3": 3000},
     "expected_outputs": {"unanswered": {"line_1": 0, "line_2": 0, "D_3800_002": True},
                          "asserted_passive": {"line_2": 8000, "line_3": 3000, "D_3800_003": True,
                                               "line_6_includes": 3000}}},
    {"scenario_name": "F3800-T6 — carryforward-in consumed; verify warning fires",
     "scenario_type": "normal",
     "inputs": {"tax_year": 2025, "f3800_cf_regular_in": 5000, "line_7_regular_tax": 50000,
                "line_10b_other_credits": 0, "line_14_tmt": 0},
     "expected_outputs": {"line_4": 5000, "line_6": 5000, "line_17": 5000, "line_38": 5000,
                          "D_3800_006": True}},
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-3800-01", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "Form 3800 §38(c)(1) chain — 11/12/13/15/16/17 hold at the boundaries",
     "description": ("Validates R-3800-P2-TAXLIM / R004. L11 = max(0, 9-10c); L13 = 25% x max(0, L12-25000); "
                     "L15 = max(13,14); L16 = max(0, 11-15); L17 = min(6, 16). Bug it catches: TMT ignored, "
                     "the $25,000 threshold dropped, or a negative line not floored."),
     "definition": {"kind": "formula_check", "form": "3800",
                    "formula": "L17 == min(L6, max(0, max(0, L9-L10c) - max(0.25*max(0, L12-25000), L14)))"},
     "sort_order": 1},
    {"assertion_id": "FA-1040-3800-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Form 3800 line 38 -> Schedule 3 line 6a; the built feeders land on their Part III rows",
     "description": ("Validates R-3800-ALLOWED + R-3800-P3-INFLOW. Line 38 (= 28+37) lands on Schedule 3 "
                     "line 6a; 8835 -> 1f/4e (per R-8835-ROUTE), 8911 line 3 -> 1s, 8936 line 8 -> 1y, "
                     "8936 line 21 -> 1aa. Retires the tts D_8911_004 RED-defer and softens D_8936_003 to "
                     "the spec's info. Bug it catches: a feeder skipping its row, or line 38 not reaching "
                     "Schedule 3."),
     "definition": {"kind": "flow_assertion", "form": "3800",
                    "must_write_to": {"38": "SCH_3.6a"},
                    "inflows": {"8835": "P3-1f|P3-4e", "8911.3": "P3-1s", "8936.8": "P3-1y", "8936.21": "P3-1aa"}},
     "sort_order": 2},
    {"assertion_id": "FA-1040-3800-03", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "Form 3800 constants — $25,000/25% (§38(c)(1)), 1-back/20-forward (§39), the §45 4-year window",
     "description": ("Validates the verified constants. Bug it catches: a drifted threshold/rate, or the "
                     "§38(c)(4)(B)(iv) window consumed differently than R-8835-ROUTE routes it."),
     "definition": {"kind": "constants_check", "form": "3800",
                    "constants": {"sec38c1_threshold": 25000, "sec38c1_rate": 0.25,
                                  "carryback_years": 1, "carryforward_years": 20,
                                  "sec45_specified_window_years": 4}},
     "sort_order": 3},
    {"assertion_id": "FA-1040-3800-04", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "Form 3800 §38(c)(4)(A) teeth — a specified credit ignores the TMT (Section C)",
     "description": ("Validates R-3800-P2-SECC. The same credit allowed at min(29,36) with line 27 using "
                     "line 13 ONLY (TMT treated as zero) must exceed the Section A result whenever the TMT "
                     "binds (the F3800-T3-vs-T4 pair). Bug it catches: line 27 built from line 15 instead "
                     "of line 13 (silently re-applying the TMT to specified credits)."),
     "definition": {"kind": "gating_check", "form": "3800",
                    "invariant": "specified_ignores_tmt", "expect": {"t4_allows_more_than_t3": True}},
     "sort_order": 4},
    {"assertion_id": "FA-1040-3800-05", "assertion_type": "table_invariant", "entity_types": ["1040"],
     "title": "Form 3800 passive gates — unanswered excluded + RED; passive REDs with the line-3/33 escape",
     "description": ("Validates R-3800-P3-INFLOW's J2 ruling. An unanswered f3800_ps_* assertion EXCLUDES "
                     "the inflow and fires D_3800_002; an asserted-passive inflow lands in column (d), "
                     "fires D_3800_003, and only the preparer-entered line 3/33 amount enters lines 6/36. "
                     "Bug it catches: an unclassified or passive credit silently flowing as nonpassive."),
     "definition": {"kind": "gating_check", "form": "3800",
                    "blockers": ["ps_unanswered_excluded", "passive_no_8582cr"],
                    "expect": {"red_fires": True, "escape_hatch": "lines 3/33"}},
     "sort_order": 5},
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_3800_FORM", "3800", "defines"),
]


# ═══════════════════════════════════════════════════════════════════════════
# COMMAND
# ═══════════════════════════════════════════════════════════════════════════


class Command(BaseCommand):
    help = ("AMEND the Form 3800 spec with the 1040-side GBC build (lookup — never "
            "recreate; preserves entity_types + the R001-R003 entity rules).")

    def handle(self, *args, **options):
        if not READY_TO_SEED:
            raise CommandError(
                "READY_TO_SEED is False — Ken has not approved the Form 3800 1040-side "
                "review packet (W1-W4 + the J1-J4 scope rulings). Walk the packet, flip "
                "the sentinel, then re-run."
            )
        with transaction.atomic():
            form = self._lookup_form()
            sources = self._load_sources()
            self._load_new_excerpts_on_existing(sources)
            self._delete_stale_lines(form)
            self._upsert_facts(form, FORM_3800_FACTS)
            rules = self._upsert_rules(form, FORM_3800_RULES)
            self._upsert_authority_links(rules, sources, RULE_AUTHORITY_LINKS)
            self._upsert_lines(form, FORM_3800_LINES)
            self._upsert_diagnostics(form, FORM_3800_DIAGNOSTICS)
            self._upsert_tests(form, FORM_3800_TESTS)
            self._upsert_form_links(sources)
            self._load_flow_assertions()
        self._report_totals()

    def _lookup_form(self) -> TaxForm:
        """AMEND BY LOOKUP — the form must already exist (the 1120-S-era draft).
        entity_types is PRESERVED verbatim; only the title/notes refresh."""
        form = TaxForm.objects.filter(
            form_number=FORM_NUMBER, jurisdiction=FORM_JURISDICTION,
            tax_year=FORM_TAX_YEAR, version=FORM_VERSION,
        ).first()
        if form is None:
            raise CommandError(
                "Form 3800 not found — this loader AMENDS the existing 1120-S-era spec "
                "and must never create it. Check form_number/tax_year/version."
            )
        form.form_title = "Form 3800 — General Business Credit"
        form.notes = (
            (form.notes or "") +
            "\n2026-07-04: 1040-side amendment (load_1040_form_3800) — Parts I/II/III per "
            "the 2025 face; entity rules R001-R003 kept; the pre-redesign line sketch "
            "replaced. Scope: J1 built feeders + catch-alls; J2 passive assert + RED-defer "
            "(8582-CR manual); J3 two CF in-buckets + computed CF-out; J4 no §6417/§6418."
        )
        form.save(update_fields=["form_title", "notes"])
        self.stdout.write(
            f"Amending {FORM_NUMBER} (entity_types preserved: {form.entity_types})")
        return form

    def _delete_stale_lines(self, form):
        deleted, _ = FormLine.objects.filter(
            tax_form=form, line_number__in=STALE_LINES_TO_DELETE).delete()
        self.stdout.write(
            f"  deleted {deleted} stale sketch line(s): {STALE_LINES_TO_DELETE}")

    def _load_sources(self):
        sources = {}
        for src in AUTHORITY_SOURCES:
            src = dict(src)
            topic_codes = src.pop("topics", [])
            excerpts = src.pop("excerpts", [])
            for code, name in AUTHORITY_TOPICS:
                AuthorityTopic.objects.update_or_create(
                    topic_code=code, defaults={"topic_name": name})
            source, _ = AuthoritySource.objects.update_or_create(
                source_code=src.pop("source_code"), defaults=src)
            sources[source.source_code] = source
            for exc in excerpts:
                AuthorityExcerpt.objects.update_or_create(
                    authority_source=source, excerpt_label=exc["excerpt_label"],
                    defaults=exc)
            for tc in topic_codes:
                topic = AuthorityTopic.objects.filter(topic_code=tc).first()
                if topic:
                    AuthoritySourceTopic.objects.get_or_create(
                        authority_source=source, authority_topic=topic)
        for code in EXISTING_SOURCES_TO_REFERENCE:
            src = AuthoritySource.objects.filter(source_code=code).first()
            if src:
                sources[code] = src
            else:
                self.stdout.write(self.style.WARNING(
                    f"  referenced source {code} NOT found — links skipped"))
        self.stdout.write(f"Sources ready: {len(sources)}")
        return sources

    def _load_new_excerpts_on_existing(self, sources):
        for code, exc in NEW_EXCERPTS_ON_EXISTING:
            src = sources.get(code) or AuthoritySource.objects.filter(
                source_code=code).first()
            if src:
                exc = dict(exc)
                AuthorityExcerpt.objects.update_or_create(
                    authority_source=src, excerpt_label=exc["excerpt_label"],
                    defaults=exc)

    def _upsert_facts(self, form, facts):
        for f in facts:
            f = dict(f)
            FormFact.objects.update_or_create(
                tax_form=form, fact_key=f.pop("fact_key"), defaults=f)
        self.stdout.write(f"  {len(facts)} facts")

    def _upsert_rules(self, form, rules_data) -> dict[str, FormRule]:
        created = {}
        for r in rules_data:
            r = dict(r)
            rule, _ = FormRule.objects.update_or_create(
                tax_form=form, rule_id=r.pop("rule_id"), defaults=r)
            created[rule.rule_id] = rule
        self.stdout.write(f"  {len(created)} rules (R004 refreshed in place)")
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
            ln.setdefault("calculation", "")
            ln.setdefault("source_facts", [])
            ln.setdefault("source_rules", [])
            ln.setdefault("destination_form", None)
            ln.setdefault("notes", "")
            FormLine.objects.update_or_create(
                tax_form=form, line_number=ln.pop("line_number"), defaults=ln)
        self.stdout.write(f"  {len(lines)} lines (stale sketch keys overwritten)")

    def _upsert_diagnostics(self, form, diagnostics):
        for d in diagnostics:
            d = dict(d)
            FormDiagnostic.objects.update_or_create(
                tax_form=form, diagnostic_id=d.pop("diagnostic_id"), defaults=d)
        self.stdout.write(f"  {len(diagnostics)} diagnostics")

    def _upsert_tests(self, form, scenarios):
        for t in scenarios:
            t = dict(t)
            TestScenario.objects.update_or_create(
                tax_form=form, scenario_name=t.pop("scenario_name"), defaults=t)
        self.stdout.write(f"  {len(scenarios)} test scenarios")

    def _upsert_form_links(self, sources):
        for source_code, form_code, link_type in AUTHORITY_FORM_LINKS:
            source = sources.get(source_code) or AuthoritySource.objects.filter(
                source_code=source_code).first()
            if source:
                AuthorityFormLink.objects.get_or_create(
                    authority_source=source, form_code=form_code,
                    link_type=link_type,
                    defaults={"note": f"{source_code} -> {form_code}"})

    def _load_flow_assertions(self):
        for a in FLOW_ASSERTIONS:
            a = dict(a)
            FlowAssertion.objects.update_or_create(
                assertion_id=a.pop("assertion_id"), defaults=a)
        self.stdout.write(f"  {len(FLOW_ASSERTIONS)} flow assertions")

    def _report_totals(self):
        def _safe(text):
            return text.encode("ascii", errors="replace").decode("ascii")
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("DATABASE TOTALS (after load_1040_form_3800)")
        self.stdout.write("=" * 60)
        for label, model in (("TaxForms", TaxForm), ("FormFacts", FormFact),
                             ("FormRules", FormRule), ("FormLines", FormLine),
                             ("FormDiagnostics", FormDiagnostic),
                             ("TestScenarios", TestScenario),
                             ("AuthoritySources", AuthoritySource),
                             ("RuleAuthorityLinks", RuleAuthorityLink),
                             ("FlowAssertions", FlowAssertion)):
            self.stdout.write(f"{label+':':20}{model.objects.count()}")
        uncited = [r for r in FormRule.objects.filter(tax_form__form_number="3800")
                   if not r.authority_links.exists()]
        if uncited:
            self.stdout.write(self.style.WARNING(
                f"\n3800 rules with ZERO authority links: {len(uncited)}"))
            for r in uncited[:20]:
                self.stdout.write(_safe(f"  {r.rule_id}: {r.title}"))
        else:
            self.stdout.write(self.style.SUCCESS(
                "3800: all rules have authority links."))
