"""Load the 8283 spec — Noncash Charitable Contributions (§170(f)(11)
substantiation/reporting; the deduction itself is figured on Schedule A).
AMENDS the existing shared "8283" TaxForm (1120S/1065/1040 — created as a
placeholder stub by load_1120s_complete.py) BY LOOKUP, preserving
entity_types (the rs-amend-shared-form lesson). The stub's 5 unnamed rules /
8 generic SA-*/SB-1 lines / D001-D003 / 2 placeholder tests are RETIRED
(deleted) by this loader — they were never Ken-approved, never seeded to
tts, and their generic ids would mislead an implementer next to the real
authored spec.

Trigger: MeF ATS Scenario 2 (John & Judy Jones) — the next smallest-first
1040 ATS scenario per Ken's 2026-07-02 ruling (S2 -> S3 -> S4). S2's Form
8283 is Section A only (Goodwill; clothes & toys; basis 3,470; FMV 700;
thrift-store value) feeding Schedule A line 12 = 700 with line 11 cash 250.
The scenario also carries return-level features OUTSIDE this form unit
(deceased spouse 9/11/2025, nonresident-spouse-election statement, spouse
IP PIN, former-spouse SSN on line 26, a statutory-employee Schedule C with
no SE tax, the EIC opt-out box 27c) — those are S2 MAPPER-leg gaps, tracked
in tts DEFERRAL_AUDIT, not specced here.

OBBBA / sunset check (SEASON_PLAN appendix 4, run at this spec leg as
required): Form 8283 is a REPORTING form under §170(f)(11) — not a credit;
no termination provision. VERIFIED 2026-07-03: the $500 / $5,000 / $500,000
tiers are statutory, non-indexed, and P.L. 119-21 (OBBBA) did not amend
§170(f)(11) or (f)(12). OBBBA's charitable changes (the TY2026+ 0.5%-AGI
floor; the non-itemizer deduction; the §68-style 35% limitation) live in the
SCHEDULE_A spec's R-SCHA-CHARITABLE/R-SCHA-68-DEFER — already year-keyed
there; nothing rides this form. The Rev. December 2025 form/instructions are
current (fetched 2026-07-03); the Dec-2025 revision's additions are the
family-pass-through-entity checkbox, the §170(h)(7) disallowance apparatus,
and the digital-assets type box (k).

Sources VERIFIED 2026-07-03 (all verbatim, fetched today):
  - 26 U.S.C. §170(f)(11)(A)-(G) — law.cornell.edu (USC_26_170F11):
    the >$500 description / >$5,000 qualified-appraisal / >$500,000
    attach-appraisal tiers, the readily-valued exceptions, the similar-items
    aggregation rule, and the pass-through entity-level application.
  - i8283 (Rev. December 2025) — irs.gov/pub/irs-pdf/i8283.pdf: Who Must
    File, Section A/B contents (incl. the over-$5,000 Section-A exceptions),
    column (h) carries the REDUCED amount, ordinary-income vs capital-gain
    property, vehicles (§170(f)(12) acknowledgment), clothing/household
    not-in-good-used-condition, art ≥ $20,000, Failure To File, the
    carryover-year re-attachment rule.
  - Form 8283 face (Rev. 12-2025) — resources/irs_forms/2025/f8283.pdf
    (already on disk, 117 AcroForm fields; matches the ATS scenario's form).

JUDGMENT ITEMS FOR KEN (Authoritative-Source Rule #4 — review walk):
  J1. Feeder convention: NoncashContribution rows auto-total into the
      Schedule A line-12 bucket inputs (YELLOW); the existing flat facts
      (scha_charitable_noncash_fmv / scha_charitable_capgain_50org) become
      the per-field GREEN overrides (non-zero wins) — the house convention
      (Sch A 5a / Roth tracker / §904(j)). RECOMMEND: yes.
  J2. Per-row ordinary-vs-capital-gain classification routes the 50% vs 30%
      AGI bucket. NULLABLE preparer assertion: None defaults to the 50%
      (ordinary) bucket and D_8283_008 WARNS only when the Schedule A
      charitable limitation actually binds (carryover_out > 0) — the mass
      case (used clothing/household, FMV < basis, nowhere near the limits)
      stays quiet. RECOMMEND: default-ordinary + bind-gated warning (a
      7217-style hard withhold would nag every Goodwill run).
  J3. §170(e)(1) reductions are PREPARER-APPLIED: column (h) carries the
      already-reduced amount (i8283 verbatim: "list the reduced amount of
      the contribution in Column (h)"; the form's own Note: "Figure the
      amount of your contribution deduction before completing this form").
      D_8283_009 warns when an ordinary-classified row shows FMV-style
      amount > basis (possible unapplied reduction). No auto-reduction.
  J4. Qualified conservation contributions (line 2 box b/b(1)) = RED-defer
      (D_8283_006) + the row's feed WITHHELD. §170(h)(7) 2.5×-relevant-basis
      disallowance, the three exceptions, NPS numbers, required statements —
      a specialist minefield with ~zero firm volume. RECOMMEND: defer.
  J5. Similar-items grouping (§170(f)(11)(F)): a "group of similar items"
      is entered as ONE row (the face itself works that way — S2's row is
      "Clothes & toys"); cross-row similarity is NOT adjudicated (an
      instruction note, no diagnostic). RECOMMEND: yes — similarity is a
      facts-and-circumstances preparer judgment.
  J6. Substantiation — RULED 2026-07-03 (AskUserQuestion): Ken chose "WARN
      ONLY, FEED ANYWAY" over the recommended withhold. A row missing its
      statutory substantiation assertion (Section B without
      appraisal_obtained §170(f)(11)(C); vehicle > $500 without the
      1098-C/CWA §170(f)(12)(A); attach-tier rows without
      appraisal_attached §170(f)(11)(D) / art ≥ $20k / not-good-condition
      clothing) fires its ERROR diagnostic but the amount STILL FEEDS
      Schedule A line 12 — the preparer stays in control; the RED is the
      flag, never a silent rewrite. The ONLY feed withhold on this form is
      the J4 conservation defer (the software can't compute that deduction
      at all). Do not re-litigate: encoded per Ken's explicit ruling.
  J7. Part IV (appraiser declaration) and Part V (donee acknowledgment) are
      data-entry render fields + completeness diagnostics; signatures are
      wet-ink. E-file: the SIGNED 8283 rides as a PDF binary attachment (or
      Form 8453) per i8283 — a mapper-leg + print-gate note, not compute.
      RECOMMEND: yes.

v1 SCOPE BOUNDARIES (stated, not silent):
  - Qualified conservation contributions: D_8283_006 RED, feed withheld
    (J4). The §170(h)(7) apparatus, Form 8283-V, NPS numbers not modeled.
  - Member-of-pass-through mechanics (attach the entity's 8283 + your own;
    the entity-name/EIN header line; the family-PTE checkbox): header
    fields render as entered; the multi-form attachment choreography is a
    D_8283_010 info note. K-1 box 12/13 charitable amounts already flow via
    the K-1 router as deduction dollars; a K-1-sourced 8283 row is entered
    manually like any other row.
  - Entity-side (1120S/1065) flow: this amendment authors the SHARED face
    (Sections A/B) for all three entity types; the 1040-scoped rules
    (R-8283-SCHA12) say so on their face. The entity side's charitable
    passthrough (Schedule K line 12a) is existing entity machinery — no
    change rides this unit.
  - Bargain sales: col (g) amount received renders as entered; the §1011(b)
    basis-allocation math is the preparer's (the contribution amount
    entered is already the gift portion).
  - Form 8282 recapture (donee disposes within 3 years), Form 8899 IP
    income, §170(e)(3)/(e)(4) C-corp enhanced deductions: out of scope.
  - Carryover-year re-attachment (a prior-year 8283 copy must ride a
    carryover year's return): D_8283_012 info when Schedule A line 13
    carryover-in > 0 — the attachment itself is manual.

SAFETY GUARD: READY_TO_SEED flipped 2026-07-03 — Ken approved the review walk
in-session (AskUserQuestion): J6 RULED "warn only, feed anyway" (substantiation
REDs fire, amounts still flow — the withhold recommendation was rejected);
J2 default-50%-bucket + bind-gated warning approved; J4 conservation RED-defer
WITH feed withhold approved; J1/J3/J5/J7 + the stub retirement approved;
flip-seed-build approved.
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


READY_TO_SEED = True  # FLIPPED 2026-07-03 — Ken approved the review walk in-session (AskUserQuestion): J6 RULED warn-only-feed-anyway; J2/J4 as recommended; J1/J3/J5/J7 + stub retirement approved.


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
# entity_types are PRESERVED from the existing shared row (1120S/1065/1040) —
# _upsert_form amends by lookup and never writes entity_types over an
# existing row (the rs-amend-shared-form lesson).
FORM_ENTITY_TYPES_IF_CREATING = ["1120S", "1065", "1040"]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("charitable_contributions",
     "Charitable contributions — §170 deduction, substantiation, Form 8283 noncash reporting"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_PUB526_2025",       # ordinary vs capital-gain property; 50%/30% buckets (Schedule A spec)
    "IRS_2025_SCHA_INSTR",   # Schedule A lines 11-14 (if present under this code; resolved at run)
]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "USC_26_170F11",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "tax_year_start": 2024,
        "tax_year_end": 2026,
        "title": "26 U.S.C. §170(f)(11) — Qualified appraisal and other documentation for certain contributions",
        "citation": "IRC §170(f)(11); §170(f)(12) (vehicles). NOT amended by P.L. 119-21 (OBBBA).",
        "issuer": "US Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/170",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": True,
        "notes": (
            "Fetched 2026-07-03 (law.cornell.edu). The SEASON_PLAN appendix-4 sunset check for Form "
            "8283, run at this spec leg: §170(f)(11) is a substantiation provision, not a credit — "
            "no termination exists; the $500/$5,000/$500,000 tiers are statutory and non-indexed; "
            "OBBBA did not touch (f)(11)/(f)(12). REQUIRES HUMAN REVIEW: Ken confirms the "
            "substantiation-withhold encoding (J6) — a row failing its statutory substantiation "
            "tier feeds nothing — and the J2 bucket-default convention."
        ),
        "topics": ["charitable_contributions"],
        "excerpts": [
            {
                "excerpt_label": "§170(f)(11)(A)(i) — denial of deduction absent substantiation (verbatim)",
                "location_reference": "26 U.S.C. §170(f)(11)(A)(i)",
                "excerpt_text": (
                    "In the case of an individual, partnership, or corporation, no deduction shall be "
                    "allowed under subsection (a) for any contribution of property for which a "
                    "deduction of more than $500 is claimed unless such person meets the requirements "
                    "of subparagraphs (B), (C), and (D), as the case may be, with respect to such "
                    "contribution."
                ),
                "summary_text": "The teeth: >$500 without the (B)/(C)/(D) tier met = NO deduction — the J6 withhold's legal basis.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§170(f)(11)(A)(ii) — readily-valued exceptions + reasonable cause (verbatim)",
                "location_reference": "26 U.S.C. §170(f)(11)(A)(ii)",
                "excerpt_text": (
                    "(I) Readily valued property. Subparagraphs (C) and (D) shall not apply to cash, "
                    "property described in subsection (e)(1)(B)(iii) or section 1221(a)(1), publicly "
                    "traded securities (as defined in section 6050L(a)(2)(B)), and any qualified "
                    "vehicle described in paragraph (12)(A)(ii) for which an acknowledgement under "
                    "paragraph (12)(B)(iii) is provided. (II) Reasonable cause. Clause (i) shall not "
                    "apply if it is shown that the failure to meet such requirements is due to "
                    "reasonable cause and not to willful neglect."
                ),
                "summary_text": (
                    "The Section-A-despite->$5,000 list (public securities, IP, inventory, "
                    "gross-proceeds vehicles) + the reasonable-cause escape (why D_8283_005 is an "
                    "error without a withhold)."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§170(f)(11)(B)/(C)/(D) — the $500 / $5,000 / $500,000 tiers (verbatim)",
                "location_reference": "26 U.S.C. §170(f)(11)(B)-(D)",
                "excerpt_text": (
                    "(B) Property description for contributions of more than $500 ... the individual, "
                    "partnership or corporation includes with the return for the taxable year in which "
                    "the contribution is made a description of such property and such other information "
                    "as the Secretary may require. ... (C) Qualified appraisal for contributions of "
                    "more than $5,000 ... obtains a qualified appraisal of such property and attaches "
                    "to the return ... such information regarding such property and such appraisal as "
                    "the Secretary may require. (D) Substantiation for contributions of more than "
                    "$500,000 ... attaches to the return for the taxable year a qualified appraisal of "
                    "such property."
                ),
                "summary_text": ">$500 describe (Form 8283); >$5,000 obtain appraisal (Section B); >$500,000 ATTACH appraisal.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§170(f)(11)(F)/(G) — similar-items aggregation; entity-level application (verbatim)",
                "location_reference": "26 U.S.C. §170(f)(11)(F)-(G)",
                "excerpt_text": (
                    "(F) Aggregation of similar items of property. For purposes of determining "
                    "thresholds under this paragraph, property and all similar items of property "
                    "donated to 1 or more donees shall be treated as 1 property. (G) Special rule for "
                    "pass-thru entities. In the case of a partnership or S corporation, this paragraph "
                    "shall be applied at the entity level, except that the deduction shall be denied "
                    "at the partner or shareholder level."
                ),
                "summary_text": "Similar items aggregate across donees for the tiers (J5: one row per group); PTE applies tiers at entity level.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§170(f)(12)(A) — vehicle >$500: no deduction without the CWA (verbatim)",
                "location_reference": "26 U.S.C. §170(f)(12)(A)",
                "excerpt_text": (
                    "In the case of a contribution of a qualified vehicle the claimed value of which "
                    "exceeds $500 — (i) paragraph (8) shall not apply and no deduction shall be allowed "
                    "under subsection (a) for such contribution unless the taxpayer substantiates the "
                    "contribution by a contemporaneous written acknowledgement of the contribution by "
                    "the donee organization that meets the requirements of subparagraph (B) and "
                    "includes the acknowledgement with the taxpayer's return of tax which includes the "
                    "deduction"
                ),
                "summary_text": "Vehicle >$500: the 1098-C/CWA must be INCLUDED WITH THE RETURN or no deduction — D_8283_003's withhold basis.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        # Re-declare the EXISTING source (created by load_1120s_complete.py with
        # paraphrased 2025 excerpts) — update_or_create on source_code refreshes it
        # to the Rev. December 2025 instructions with VERBATIM excerpts added below.
        "source_code": "IRS_2025_8283_INSTR",
        "source_type": "official_instruction",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "title": "Instructions for Form 8283 (Rev. December 2025) — Noncash Charitable Contributions",
        "citation": "Instructions for Form 8283 (Rev. 12-2025), Cat. No. 62730R",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i8283.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "requires_human_review": True,
        "trust_score": 9.0,
        "topics": ["charitable_contributions"],
        "notes": (
            "Refreshed 2026-07-03 to the Rev. December 2025 instructions, fetched from irs.gov and "
            "quoted VERBATIM (the prior excerpts on this source were 1120s-era paraphrases — kept, "
            "but superseded by the verbatim set). Matches the Rev. 12-2025 form face on disk."
        ),
        "excerpts": [
            {
                "excerpt_label": "Who Must File (Rev. 12-2025, verbatim)",
                "location_reference": "i8283 (Rev. 12-2025), General Instructions, Who Must File",
                "excerpt_text": (
                    "You must file one or more Forms 8283 if the amount of your deduction for each "
                    "noncash contribution is more than $500. You must also file Form 8283 if you have "
                    "a group of similar items for which a total deduction of over $500 is claimed. ... "
                    "For this purpose, “amount of your deduction” means your deduction before applying "
                    "any income limits that could result in a carryover. ... Make any required "
                    "reductions to the amount of the contributions before you determine if you must "
                    "file Form 8283."
                ),
                "summary_text": "File when any item/group deduction >$500 — measured BEFORE AGI limits, AFTER §170(e) reductions.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Section A contents incl. the over-$5,000 exceptions (Rev. 12-2025, verbatim)",
                "location_reference": "i8283 (Rev. 12-2025), Which Sections To Complete, Section A",
                "excerpt_text": (
                    "Include in Section A only the following items. 1. Items (or groups of similar "
                    "items as defined later) for which you claimed a deduction of more than $500 but "
                    "not more than $5,000 per item (or group of similar items). 2. The following items "
                    "even if the claimed value was more than $5,000 per item (or group of similar "
                    "items): a. Securities listed on an exchange in which quotations are published "
                    "daily, b. Securities regularly traded in national or regional over-the-counter "
                    "markets for which published quotations are available, c. Securities that are "
                    "shares of a mutual fund ... e. A vehicle (including a car, boat, or airplane) if "
                    "your deduction for the vehicle is limited to the gross proceeds from its sale and "
                    "you obtained a contemporaneous written acknowledgment, f. Intellectual property "
                    "(as defined later), or g. Inventory or property held primarily for sale to "
                    "customers in the ordinary course of your trade or business."
                ),
                "summary_text": "Section A: ≤$5,000 items PLUS public securities / gross-proceeds vehicles / IP / inventory at any amount.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Section B + appraisal; not-good-condition clothing (Rev. 12-2025, verbatim)",
                "location_reference": "i8283 (Rev. 12-2025), Which Sections To Complete, Section B",
                "excerpt_text": (
                    "Include in Section B only items (or groups of similar items) for which you "
                    "claimed a deduction of more than $5,000. Do not include items reportable in "
                    "Section A. Items reportable in Section B require a written qualified appraisal by "
                    "a qualified appraiser. Form 8283 is an appraisal summary. It is not an appraisal. "
                    "... You must file a separate Form 8283, Section B, for each donee organization "
                    "and each item of property (or group of similar items). You must file Form 8283, "
                    "Section B, if you are contributing a single article of clothing or household item "
                    "that is not in good used condition or better and for which you are claiming a "
                    "deduction of over $500."
                ),
                "summary_text": "Section B: >$5,000 items; separate form per donee per item; not-good-condition clothing >$500 lands here too.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Column (h) carries the REDUCED amount (Rev. 12-2025, verbatim)",
                "location_reference": "i8283 (Rev. 12-2025), Section A, Line 1, Column (h)",
                "excerpt_text": (
                    "Enter the FMV of the property on the date you donated it. However, if you were "
                    "required to reduce the amount of your contribution below the FMV, list the "
                    "reduced amount of the contribution in Column (h) rather than the FMV. In "
                    "addition, attach a statement listing the FMV and the computation of and reasons "
                    "for the reduction."
                ),
                "summary_text": "J3's basis: the preparer enters the ALREADY-REDUCED amount; the software never auto-reduces.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Ordinary income property vs capital gain property (Rev. 12-2025, verbatim)",
                "location_reference": "i8283 (Rev. 12-2025), Fair Market Value, Reductions to contribution",
                "excerpt_text": (
                    "Ordinary income property is property that would result in ordinary income or "
                    "short-term capital gain if it were sold at its FMV on the date it was "
                    "contributed. ... The deduction for a gift of ordinary income property is limited "
                    "to the FMV minus the amount that would be ordinary income or short-term capital "
                    "gain if the property were sold. Capital gain property is property that would "
                    "result in long-term capital gain if it were sold at its FMV on the date it was "
                    "contributed. ... However, to the extent of any gain from the property that must "
                    "be recaptured as ordinary income under section 1245, section 1250, or any other "
                    "code provision, the property is treated as ordinary income property."
                ),
                "summary_text": "The J2 classification axis — and D_8283_009's ordinary-property FMV>basis reduction check.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Column e/f/g requirements + the ≤$500 exception (Rev. 12-2025, verbatim)",
                "location_reference": "i8283 (Rev. 12-2025), Section A, Line 1, Columns (d)-(g)",
                "excerpt_text": (
                    "Note: If the amount you claimed as a deduction for the item is $500 or less, you "
                    "do not have to complete columns (e), (f), and (g). ... Column (g). For items over "
                    "$500, enter your cost or adjusted basis. Do not complete this column for publicly "
                    "traded securities held more than 12 months, unless you elect to limit your "
                    "deduction cost basis. ... Note: If you must complete columns (e), (f), and (g) "
                    "but have reasonable cause for not providing the information required, attach an "
                    "explanation."
                ),
                "summary_text": "e/f/g required only for rows >$500; public securities exempt from (g); reasonable-cause explanation escape.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Art $20,000+; deduction >$500,000 — ATTACH the appraisal (Rev. 12-2025, verbatim)",
                "location_reference": "i8283 (Rev. 12-2025), Section B Part I",
                "excerpt_text": (
                    "Art valued at $20,000 or more. If your deduction for art is $20,000 or more, you "
                    "must attach a complete copy of the signed appraisal to your return. ... Deduction "
                    "of more than $500,000. If you are claiming a deduction of more than $500,000 for "
                    "an item (or group of similar items) donated to one or more donees, you must "
                    "attach the qualified appraisal of the property to your return unless an exception "
                    "applies."
                ),
                "summary_text": "The attach-appraisal tier (D_8283_004): art ≥$20k; any item >$500k; (plus not-good clothing, historic easements).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "E-file: signed 8283 rides as PDF attachment or Form 8453 (Rev. 12-2025, verbatim)",
                "location_reference": "i8283 (Rev. 12-2025), How To Complete",
                "excerpt_text": (
                    "If you are electronically filing your tax return, you must include the Form 8283 "
                    "data in the electronic submission. Enter all information requested by a line of "
                    "the Form 8283 on the electronic Form 8283, except for the required signatures. "
                    "Caution: You must attach the completed Form 8283 with all the required signatures "
                    "to your tax return, either as a PDF attachment when electronically filed, or "
                    "mailed to the IRS with Form 8453."
                ),
                "summary_text": "J7 / mapper-leg note: XML data + a signed-copy binary attachment (or 8453 mail-in).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Failure To File Form 8283 (Rev. 12-2025, verbatim)",
                "location_reference": "i8283 (Rev. 12-2025), Failure To File Form 8283",
                "excerpt_text": (
                    "Your deduction generally will be disallowed if you fail to: Attach a required "
                    "Form 8283 to your return, Fully complete Form 8283 by omitting required "
                    "information or submitting non-responsive language, Get a required appraisal and "
                    "complete Section B of Form 8283, or Attach to your return a required appraisal of "
                    "clothing or household items not in good used condition, or Attach to your return "
                    "a required appraisal for an easement on a historically significant building, or "
                    "property for which you claimed a deduction of more than $500,000. ... Your "
                    "deduction will not be disallowed if your failure to submit the required "
                    "information was due to reasonable cause and not willful neglect."
                ),
                "summary_text": "Completeness = deduction survival — the D_8283_007 completeness error's basis.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Carryover to a later year — re-attach the prior 8283 (Rev. 12-2025, verbatim)",
                "location_reference": "i8283 (Rev. 12-2025), Noncash Contributions Carried Over to Later Year",
                "excerpt_text": (
                    "If your noncash contribution was subject to one or more limits based on your "
                    "adjusted gross income, and your unused charitable deduction from a previous year "
                    "may be claimed in the current year, you must attach to your current return a "
                    "completed copy of the Form 8283 from the previous year."
                ),
                "summary_text": "D_8283_012's basis: carryover-in > 0 needs the prior-year 8283 copy attached (manual).",
                "is_key_excerpt": True,
            },
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("USC_26_170F11", "8283", "governs"),
    ("IRS_2025_8283_INSTR", "8283", "governs"),
    ("IRS_PUB526_2025", "8283", "governs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM: 8283 (amend the shared stub)
# ═══════════════════════════════════════════════════════════════════════════

F8283_IDENTITY = {
    "form_number": "8283",
    "form_title": "Form 8283 — Noncash Charitable Contributions (Rev. 12-2025)",
    "notes": (
        "§170(f)(11) substantiation/reporting — the form computes NO deduction "
        "itself (its own Note: 'Figure the amount of your contribution deduction "
        "before completing this form'). tts model = a per-return NoncashContribution "
        "list row per donated item or per GROUP of similar items (J5) — the "
        "StateIncomeTaxPayment/InstallmentSale pattern. Section A/B routing is "
        "DERIVED per row (R-8283-SECTION); the row amounts auto-total into the "
        "Schedule A line-12 bucket inputs (50% ordinary / 30% capital-gain — "
        "YELLOW, flat facts as GREEN overrides, J1). Substantiation gaps "
        "(§170(f)(11)(C)/(D), §170(f)(12)) fire ERROR diagnostics but the feed "
        "flows anyway — Ken RULED warn-only 2026-07-03 (J6); the ONLY feed "
        "withhold is the conservation RED-defer (J4). Print "
        "gate: the form joins the packet when the total noncash deduction > $500; "
        "amounts feed Schedule A regardless. 1040-side unit built 2026-07 (ATS "
        "Scenario 2); entity-side (1120S/1065) K-line flow is existing machinery — "
        "the shared face spec serves all three entity types."
    ),
}

F8283_FACTS: list[dict] = [
    # ── Per-item inputs (one row per item or per group of similar items) ──
    {"fact_key": "f8283_donee_name", "label": "Col 1(a) / Part V — donee organization name",
     "data_type": "string", "sort_order": 1,
     "notes": "PER-ROW INPUT. Required (D_8283_007). MeF: BusinessNameType."},
    {"fact_key": "f8283_donee_street", "label": "Col 1(a) / Part V — donee street address",
     "data_type": "string", "sort_order": 2,
     "notes": "PER-ROW INPUT. MeF: USAddressType AddressLine1Txt."},
    {"fact_key": "f8283_donee_city", "label": "Col 1(a) / Part V — donee city",
     "data_type": "string", "sort_order": 3, "notes": "PER-ROW INPUT."},
    {"fact_key": "f8283_donee_state", "label": "Col 1(a) / Part V — donee state",
     "data_type": "string", "sort_order": 4, "notes": "PER-ROW INPUT. StateType enum."},
    {"fact_key": "f8283_donee_zip", "label": "Col 1(a) / Part V — donee ZIP",
     "data_type": "string", "sort_order": 5, "notes": "PER-ROW INPUT. ZIPCodeType."},
    {"fact_key": "f8283_is_vehicle", "label": "Col 1(b) — donated property is a qualified vehicle (car/boat/airplane)",
     "data_type": "boolean", "default_value": "false", "sort_order": 6,
     "notes": ("PER-ROW INPUT. Vehicle >$500: §170(f)(12) CWA/1098-C REQUIRED WITH THE RETURN "
               "(D_8283_003 + feed withhold, J6). Dealer inventory is NOT a qualified vehicle "
               "(use inventory_1221 instead).")},
    {"fact_key": "f8283_vin", "label": "Col 1(b) — vehicle identification number",
     "data_type": "string", "sort_order": 7,
     "notes": ("PER-ROW INPUT. Required when is_vehicle and the 1098-C is NOT attached; 17 chars, "
               "left-pad short VINs with 0 (i8283 verbatim).")},
    {"fact_key": "f8283_description", "label": "Col 1(c) / SB 3(a) — description (and condition) of donated property",
     "data_type": "string", "sort_order": 8,
     "notes": ("PER-ROW INPUT. Required (D_8283_007). Vehicles: year/make/model/condition/mileage. "
               "Securities: company, share count, kind, fund?, traded-where. Detail scales with value.")},
    {"fact_key": "f8283_condition", "label": "SB 3(b) — overall physical condition at time of gift (tangible/real property)",
     "data_type": "string", "sort_order": 9,
     "notes": "PER-ROW INPUT (Section B rows; also folds into Section A col (c) text)."},
    {"fact_key": "f8283_date_contributed", "label": "Col 1(d) — date of the contribution",
     "data_type": "date", "sort_order": 10,
     "notes": ("PER-ROW INPUT. Required. Contributions on various dates = separate rows (i8283 "
               "col (d) verbatim). Year must fall in the return tax year — D_8283_007.")},
    {"fact_key": "f8283_date_acquired", "label": "Col 1(e) / SB 3(d) — date acquired by donor (mo., yr.; 'Various' allowed)",
     "data_type": "string", "sort_order": 11,
     "notes": ("PER-ROW INPUT (string — the face takes 'Various' for similar-item groups held "
               "≥12 months). Required for rows >$500 except publicly traded securities held "
               "≤12 months rule (D_8283_005).")},
    {"fact_key": "f8283_how_acquired", "label": "Col 1(f) / SB 3(e) — how acquired (purchase/gift/inheritance/exchange)",
     "data_type": "string", "sort_order": 12,
     "notes": "PER-ROW INPUT. Required for rows >$500 (D_8283_005)."},
    {"fact_key": "f8283_cost_basis", "label": "Col 1(g) / SB 3(f) — donor's cost or adjusted basis",
     "data_type": "decimal", "sort_order": 13,
     "notes": ("PER-ROW INPUT, nullable. Required for rows >$500 EXCEPT publicly traded securities "
               "held >12 months (i8283 col (g) verbatim; D_8283_005 skips public_security rows). "
               "Drives the D_8283_009 §170(e)(1) reduction check.")},
    {"fact_key": "f8283_amount", "label": "Col 1(h) / SB 3(c)+(i) — amount of the contribution (FMV, or the §170(e)-REDUCED amount)",
     "data_type": "decimal", "default_value": "0", "sort_order": 14,
     "notes": ("PER-ROW INPUT — THE deduction amount for the row, before AGI limits. The preparer "
               "enters the ALREADY-REDUCED amount when §170(e) applies (i8283 col (h) verbatim; "
               "J3) and attaches the reduction statement. Bargain sales: enter the gift portion.")},
    {"fact_key": "f8283_valuation_method", "label": "Col 1(i) — method used to determine FMV",
     "data_type": "string", "sort_order": 15,
     "notes": ("PER-ROW INPUT. 'Appraisal', 'Thrift shop value', 'Catalog', 'Comparable sales' "
               "(i8283 examples). Required for rows >$500 where col (h) is completed.")},
    {"fact_key": "f8283_capgain_property", "label": "Row classification — capital gain property (LTCG-if-sold)? Routes the 30% vs 50% AGI bucket",
     "data_type": "boolean", "sort_order": 16,
     "notes": ("PER-ROW PREPARER ASSERTION (nullable — J2). True -> the 30% bucket "
               "(scha_charitable_capgain_50org); False -> the 50% bucket. None DEFAULTS to the 50% "
               "(ordinary) bucket; D_8283_008 warns only when the Schedule A charitable limitation "
               "actually binds (carryover_out > 0). §1245/§1250 recapture portions are ordinary "
               "by law (preparer splits the row if mixed).")},
    {"fact_key": "f8283_property_type", "label": "SB line 2 — type of donated property (a-l)",
     "data_type": "string", "sort_order": 17,
     "notes": ("PER-ROW INPUT (Section B rows; enum: art20k | conservation | historic | art_lt20k | "
               "real_estate | equipment | securities_nonpub | collectibles | intellectual | vehicles "
               "| clothing_household | digital | other | ''). ONE box per Form 8283 copy — the "
               "render leg emits one Section B copy per row (per-donee-per-item rule). "
               "conservation/historic -> D_8283_006 RED-defer + feed withheld (J4).")},
    {"fact_key": "f8283_public_security", "label": "Row — publicly traded security (§6050L(a)(2)(B))",
     "data_type": "boolean", "default_value": "false", "sort_order": 18,
     "notes": ("PER-ROW INPUT. Section A at ANY amount (§170(f)(11)(A)(ii)(I)); exempt from the "
               "col (g) basis requirement when held >12 months; no appraisal tier applies.")},
    {"fact_key": "f8283_intellectual", "label": "Row — intellectual property (§170(e)(1)(B)(iii))",
     "data_type": "boolean", "default_value": "false", "sort_order": 19,
     "notes": ("PER-ROW INPUT. Section A at any amount. Deduction is basis-limited (preparer applies "
               "per J3); Form 8899 later-year income deductions out of scope (stated boundary).")},
    {"fact_key": "f8283_inventory_1221", "label": "Row — inventory / property held primarily for sale (§1221(a)(1))",
     "data_type": "boolean", "default_value": "false", "sort_order": 20,
     "notes": "PER-ROW INPUT. Section A at any amount; ordinary income property by definition."},
    {"fact_key": "f8283_vehicle_fmv_exception", "label": "Vehicle row — deduction NOT limited to gross proceeds (significant use / material improvement / needy-individual transfer)",
     "data_type": "boolean", "default_value": "false", "sort_order": 21,
     "notes": ("PER-ROW INPUT. False (the usual case): deduction = smaller of FMV or gross proceeds "
               "-> Section A at any amount WITH the CWA. True: FMV rule -> Section B when >$5,000 "
               "(i8283 vehicles verbatim; the 1098-C box certifications drive this answer).")},
    {"fact_key": "f8283_ack_1098c", "label": "Vehicle row — Form 1098-C / contemporaneous written acknowledgment attached to the return",
     "data_type": "boolean", "default_value": "false", "sort_order": 22,
     "notes": ("PER-ROW PREPARER ASSERTION. Vehicle >$500 without it: §170(f)(12)(A) DENIES the "
               "deduction -> D_8283_003 RED + feed withheld (J6). E-file: binary attachment "
               "(mapper leg).")},
    {"fact_key": "f8283_not_good_condition", "label": "Clothing/household row — item NOT in good used condition or better",
     "data_type": "boolean", "default_value": "false", "sort_order": 23,
     "notes": ("PER-ROW INPUT. >$500 with this set -> Section B + qualified appraisal ATTACHED "
               "(i8283 verbatim); ≤$500 not-good-condition items are nondeductible by §170(f)(16) "
               "— D_8283_013 error.")},
    {"fact_key": "f8283_appraisal_obtained", "label": "Section B row — written qualified appraisal obtained (§170(f)(11)(C))",
     "data_type": "boolean", "default_value": "false", "sort_order": 24,
     "notes": ("PER-ROW PREPARER ASSERTION. Section B row without it: the statute DENIES the "
               "deduction -> D_8283_002 RED + feed withheld (J6). The reasonable-cause escape is "
               "the preparer's to assert by checking the box with documentation.")},
    {"fact_key": "f8283_appraisal_attached", "label": "Attach-tier row — qualified appraisal ATTACHED to the return",
     "data_type": "boolean", "default_value": "false", "sort_order": 25,
     "notes": ("PER-ROW PREPARER ASSERTION. Required (D_8283_004 + withhold) when: art ≥ $20,000; "
               "any row > $500,000; not-good-condition clothing/household > $500. E-file: binary "
               "attachment (mapper leg).")},
    {"fact_key": "f8283_bargain_sale", "label": "SB 3(g) — bargain sale: amount received",
     "data_type": "decimal", "default_value": "0", "sort_order": 26,
     "notes": "PER-ROW INPUT (render). §1011(b) allocation is the preparer's (J3 note)."},
    {"fact_key": "f8283_partial_interest", "label": "SB Part II — gave less than an entire interest in the property",
     "data_type": "boolean", "default_value": "false", "sort_order": 27,
     "notes": "PER-ROW INPUT. Engages lines 4a-4e (render + completeness)."},
    {"fact_key": "f8283_prior_year_ded", "label": "SB 4b(2) — amount claimed as a deduction in prior tax years",
     "data_type": "decimal", "default_value": "0", "sort_order": 28, "notes": "PER-ROW INPUT (render)."},
    {"fact_key": "f8283_tangible_location", "label": "SB 4d — where tangible property is located or kept",
     "data_type": "string", "sort_order": 29, "notes": "PER-ROW INPUT (render)."},
    {"fact_key": "f8283_possessor", "label": "SB 4e — person (other than donee) having actual possession",
     "data_type": "string", "sort_order": 30, "notes": "PER-ROW INPUT (render)."},
    {"fact_key": "f8283_restrict_use", "label": "SB 5a — restriction on donee's right to use or dispose?",
     "data_type": "boolean", "sort_order": 31,
     "notes": "PER-ROW INPUT (nullable Yes/No). Restricted-use rows engage Part II; statement attach is manual."},
    {"fact_key": "f8283_restrict_income", "label": "SB 5b — rights to income/possession/acquisition given to another?",
     "data_type": "boolean", "sort_order": 32, "notes": "PER-ROW INPUT (nullable Yes/No)."},
    {"fact_key": "f8283_restrict_particular", "label": "SB 5c — restriction limiting the property to a particular use?",
     "data_type": "boolean", "sort_order": 33, "notes": "PER-ROW INPUT (nullable Yes/No)."},
    {"fact_key": "f8283_part3_under500", "label": "SB Part III — item appraised at $500 or less (donor statement)",
     "data_type": "boolean", "default_value": "false", "sort_order": 34,
     "notes": "PER-ROW INPUT. Listed in the Part III declaration (relieves the donee's Form 8282 duty)."},
    # ── Part IV appraiser / Part V donee-acknowledgment blocks (render data) ──
    {"fact_key": "f8283_appraiser_name", "label": "Part IV — appraiser name",
     "data_type": "string", "sort_order": 40, "notes": "PER-ROW INPUT (render; Section B rows). Wet-ink signature (J7)."},
    {"fact_key": "f8283_appraiser_title", "label": "Part IV — appraiser title",
     "data_type": "string", "sort_order": 41, "notes": "PER-ROW INPUT (render)."},
    {"fact_key": "f8283_appraiser_address", "label": "Part IV — appraiser business address (street, city, state, ZIP)",
     "data_type": "string", "sort_order": 42, "notes": "PER-ROW INPUT (render)."},
    {"fact_key": "f8283_appraiser_id", "label": "Part IV — appraiser identifying number (SSN/EIN)",
     "data_type": "string", "sort_order": 43, "notes": "PER-ROW INPUT (render). D_8283_011 completeness."},
    {"fact_key": "f8283_appraisal_date", "label": "Part IV — appraisal signature date",
     "data_type": "date", "sort_order": 44,
     "notes": "PER-ROW INPUT (render). Timing rules (≥60 days before gift is INVALID; before return due date) are the preparer's — note only."},
    {"fact_key": "f8283_donee_ein", "label": "Part V — donee employer identification number",
     "data_type": "string", "sort_order": 45, "notes": "PER-ROW INPUT (render). D_8283_011 completeness for Section B rows."},
    {"fact_key": "f8283_ack_date", "label": "Part V — date the donee received the property",
     "data_type": "date", "sort_order": 46, "notes": "PER-ROW INPUT (render)."},
    {"fact_key": "f8283_unrelated_use", "label": "Part V — donee intends an unrelated use?",
     "data_type": "boolean", "sort_order": 47,
     "notes": "PER-ROW INPUT (nullable Yes/No, render). Yes on tangible personal property = the deduction should already be basis-limited (J3 note)."},
    # ── Header (member-of-pass-through) ──
    {"fact_key": "f8283_pte_name", "label": "Header — donating pass-through entity name (if contribution originally reported elsewhere)",
     "data_type": "string", "sort_order": 50,
     "notes": "RETURN-LEVEL INPUT (render). Member-of-PTE mechanics are a stated boundary (D_8283_010)."},
    {"fact_key": "f8283_pte_ein", "label": "Header — donating pass-through entity EIN",
     "data_type": "string", "sort_order": 51, "notes": "RETURN-LEVEL INPUT (render)."},
    {"fact_key": "f8283_family_pte", "label": "Header — family pass-through entity made the contribution (conservation only)",
     "data_type": "boolean", "default_value": "false", "sort_order": 52,
     "notes": "RETURN-LEVEL INPUT (render). Conservation apparatus is deferred (J4) — box renders; D_8283_010 notes the boundary."},
    # ── Outputs ──
    {"fact_key": "f8283_total", "label": "Total noncash deduction claimed (Σ non-withheld row amounts, before AGI limits)",
     "data_type": "decimal", "sort_order": 60,
     "notes": "OUTPUT. The Who-Must-File measure (i8283: before income limits, after §170(e) reductions)."},
    {"fact_key": "f8283_bucket_50", "label": "50%-bucket total (ordinary/other property) -> Schedule A line-12 noncash input (YELLOW)",
     "data_type": "decimal", "sort_order": 61,
     "notes": "OUTPUT. Σ non-withheld rows with capgain_property in (False, None). Feeds scha_charitable_noncash_fmv unless the flat fact is a non-zero GREEN override (J1)."},
    {"fact_key": "f8283_bucket_30", "label": "30%-bucket total (capital gain property) -> Schedule A line-12 capgain input (YELLOW)",
     "data_type": "decimal", "sort_order": 62,
     "notes": "OUTPUT. Σ non-withheld rows with capgain_property True. Feeds scha_charitable_capgain_50org unless the flat fact is a non-zero GREEN override (J1)."},
    {"fact_key": "f8283_engaged", "label": "Form 8283 files/prints (total noncash deduction > $500)",
     "data_type": "boolean", "sort_order": 63,
     "notes": ("OUTPUT. Per-item-or-group measure collapses to total > 500 under the one-row-per-"
               "group convention (J5): any single row > 500 -> total > 500; multiple ≤500 rows are "
               "conservatively treated as engaging when their total exceeds 500 (§170(f)(11)(F) "
               "aggregates SIMILAR items; filing an 8283 for dissimilar small items is harmless — "
               "never under-files). Feed to Schedule A flows regardless of engagement.")},
    {"fact_key": "f8283_row_section", "label": "Per-row derived section (A or B)",
     "data_type": "string", "sort_order": 64,
     "notes": "OUTPUT (R-8283-SECTION). Drives which face grid the row renders into; no preparer override (face-true routing)."},
    {"fact_key": "f8283_row_withheld", "label": "Per-row feed withhold flag (conservation defer ONLY)",
     "data_type": "boolean", "sort_order": 65,
     "notes": ("OUTPUT. True ONLY for J4 conservation-defer rows (D_8283_006) — the software "
               "cannot compute that deduction, so the row feeds nothing. Substantiation gaps "
               "(D_8283_002/003/004) NEVER withhold — Ken ruled warn-only-feed-anyway "
               "(2026-07-03, J6).")},
]

F8283_RULES: list[dict] = [
    {"rule_id": "R-8283-FILE",
     "title": "Who must file / print gate: total noncash deduction > $500; feed flows regardless",
     "rule_type": "routing", "precedence": 1, "sort_order": 1,
     "formula": (
         "f8283_total = Σ f8283_amount over rows NOT withheld (R-8283-SUBST). f8283_engaged = "
         "(f8283_total > 500) — the §170(f)(11)(B) threshold, measured BEFORE AGI limits and AFTER "
         "§170(e) reductions (i8283 Who-Must-File verbatim; amounts are entered already-reduced per "
         "J3). Engaged -> Form 8283 joins the print packet + the e-file submission; not engaged -> "
         "no form, but the row amounts STILL feed the Schedule A line-12 buckets (a $400 donation "
         "is deductible without an 8283). One row per item OR per group of similar items (J5; "
         "§170(f)(11)(F) aggregation is the preparer's grouping call — cross-row similarity is not "
         "adjudicated). GREEN-override-only returns (line 12 entered flat, no rows) with the entry "
         "> 500 -> D_8283_001 (an 8283 is required but cannot be produced from a bare total)."),
     "inputs": ["f8283_amount"],
     "outputs": ["f8283_total", "f8283_engaged"],
     "description": ("The filing gate. C-corp $5,000 variant (§170(f)(11)(B) last sentence) is out "
                     "of scope — no 1120 module. PTE entity-level application (G) is the entity "
                     "side's existing machinery.")},
    {"rule_id": "R-8283-SECTION",
     "title": "Per-row Section A/B routing (derived, face-true)",
     "rule_type": "routing", "precedence": 2, "sort_order": 2,
     "formula": (
         "Per row: section = 'B' when f8283_amount > 5000, UNLESS a §170(f)(11)(A)(ii)(I) "
         "readily-valued exception routes it to A at any amount: public_security, intellectual, "
         "inventory_1221, or (is_vehicle AND NOT vehicle_fmv_exception AND ack_1098c) — the "
         "gross-proceeds-limited vehicle with its CWA. ALSO 'B' regardless of the $5,000 test when "
         "not_good_condition AND amount > 500 (i8283 Section B verbatim: single article of "
         "clothing/household not in good used condition over $500). Otherwise 'A'. "
         "conservation/historic property_type -> Section B by definition AND the J4 defer "
         "(D_8283_006). Render: one Section B copy per row (separate form per donee per item — "
         "i8283 verbatim); Section A rows fill the 4-row grid with overflow copies."),
     "inputs": ["f8283_amount", "f8283_public_security", "f8283_intellectual", "f8283_inventory_1221",
                "f8283_is_vehicle", "f8283_vehicle_fmv_exception", "f8283_ack_1098c",
                "f8283_not_good_condition", "f8283_property_type"],
     "outputs": ["f8283_row_section"],
     "description": "No preparer override — the routing is mechanical once the row facts are asserted."},
    {"rule_id": "R-8283-SUBST",
     "title": "Substantiation tiers: ERROR diagnostics, feed flows anyway (Ken ruling 2026-07-03); conservation is the only withhold",
     "rule_type": "routing", "precedence": 3, "sort_order": 3,
     "formula": (
         "Per row, the matching ERROR fires — but the amount STILL FEEDS Schedule A line 12 "
         "(J6, Ken 2026-07-03: warn only, feed anyway — the RED is the flag, never a silent "
         "rewrite): "
         "(a) section B and NOT appraisal_obtained -> D_8283_002 (§170(f)(11)(C) denies absent "
         "the appraisal — the preparer must cure or expect disallowance); "
         "(b) is_vehicle and amount > 500 and NOT ack_1098c -> D_8283_003 (§170(f)(12)(A)); "
         "(c) attach-tier unmet -> D_8283_004: (art20k type OR (art_lt20k AND amount ≥ 20000)) OR "
         "amount > 500000 OR (not_good_condition AND amount > 500), each requiring "
         "appraisal_attached; "
         "(d) not_good_condition AND amount ≤ 500 -> D_8283_013 error (§170(f)(16): no deduction "
         "at all — remove or reflag the item; feed still follows the entry per the ruling). "
         "THE ONE WITHHOLD: conservation/historic type -> f8283_row_withheld = True + D_8283_006 "
         "(J4 defer — the software cannot compute a conservation deduction; feeds nothing). "
         "Completeness (no withhold): section A row with amount > 500 missing date_acquired / "
         "how_acquired / cost_basis (except public_security rows — col (g)/(e) exemptions) -> "
         "D_8283_005 error (reasonable-cause explanation escape, §170(f)(11)(A)(ii)(II)). "
         "Missing donee_name / description / date_contributed / amount ≤ 0 -> D_8283_007 error. "
         "Section B row missing donee_ein or appraiser identity -> D_8283_011 warning."),
     "inputs": ["f8283_row_section", "f8283_appraisal_obtained", "f8283_appraisal_attached",
                "f8283_is_vehicle", "f8283_ack_1098c", "f8283_amount", "f8283_not_good_condition",
                "f8283_property_type", "f8283_public_security", "f8283_date_acquired",
                "f8283_how_acquired", "f8283_cost_basis", "f8283_donee_name", "f8283_description",
                "f8283_date_contributed", "f8283_donee_ein", "f8283_appraiser_id"],
     "outputs": ["f8283_row_withheld"],
     "description": ("J6 RULED warn-only-feed-anyway (Ken 2026-07-03, AskUserQuestion — the "
                     "withhold recommendation was rejected; do not re-litigate). The diagnostics "
                     "and the feed read the same row helpers (bridge-gate).")},
    {"rule_id": "R-8283-TOTAL",
     "title": "Bucket totals: 50% (ordinary/other) vs 30% (capital gain property)",
     "rule_type": "calculation", "precedence": 4, "sort_order": 4,
     "formula": (
         "Over rows NOT withheld: f8283_bucket_30 = Σ amount where capgain_property is True; "
         "f8283_bucket_50 = Σ amount where capgain_property is False OR None (J2 default-ordinary). "
         "f8283_total = bucket_50 + bucket_30. Any row defaulted (capgain_property None) AND the "
         "Schedule A charitable limitation binds on the return (scha_charitable_carryover_out > 0) "
         "-> D_8283_008 warning (the bucket choice is changing the answer — classify the rows). "
         "Ordinary-classified (False/None) row with cost_basis present AND amount > cost_basis -> "
         "D_8283_009 warning (§170(e)(1): ordinary income property is deductible at basis — the "
         "entered amount may need reduction; J3 keeps the reduction preparer-applied)."),
     "inputs": ["f8283_amount", "f8283_capgain_property", "f8283_cost_basis", "f8283_row_withheld"],
     "outputs": ["f8283_total", "f8283_bucket_50", "f8283_bucket_30"],
     "description": "Bucket semantics match the SCHEDULE_A spec exactly (50% fifty-bucket / 30% capgain-bucket)."},
    {"rule_id": "R-8283-SCHA12",
     "title": "1040: Schedule A line-12 inputs default to the 8283 buckets (YELLOW); flat facts are per-field GREEN overrides",
     "rule_type": "calculation", "precedence": 5, "sort_order": 5,
     "formula": (
         "1040 ONLY. Runs BEFORE R-SCHA-CHARITABLE (it feeds line 12's inputs — the R-SCHA-5A-STATE "
         "sequencing pattern). scha_charitable_noncash_fmv defaults to f8283_bucket_50 (YELLOW) "
         "unless the flat fact is entered non-zero (GREEN override wins, per FIELD); "
         "scha_charitable_capgain_50org defaults to f8283_bucket_30 (YELLOW) unless its flat fact "
         "is non-zero (GREEN). No rows and no overrides -> both stay 0 (backward-compatible: "
         "existing returns with flat entries are untouched). R-SCHA-CHARITABLE then applies the "
         "Pub 526 bucket limits + carryover + the 2026 floor UNCHANGED. Carryover-in > 0 on "
         "Schedule A line 13 -> D_8283_012 info (attach the prior-year 8283 copy — manual)."),
     "inputs": ["f8283_bucket_50", "f8283_bucket_30"],
     "outputs": [],
     "description": ("J1 — the house feeder convention. The entity side (1120S/1065) never runs "
                     "this rule; its charitable flow is Schedule K machinery.")},
]

F8283_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-8283-FILE", "USC_26_170F11", "primary", "(A)(i)+(B): >$500 threshold; (F) similar-items aggregation"),
    ("R-8283-FILE", "IRS_2025_8283_INSTR", "primary", "Who Must File verbatim: before income limits, after reductions"),
    ("R-8283-SECTION", "IRS_2025_8283_INSTR", "primary", "Which Sections To Complete verbatim incl. the over-$5,000 Section-A exceptions and not-good-condition clothing"),
    ("R-8283-SECTION", "USC_26_170F11", "secondary", "(A)(ii)(I) readily-valued property list — the statutory home of the exceptions"),
    ("R-8283-SUBST", "USC_26_170F11", "primary", "(A)(i) denial absent (B)/(C)/(D); (f)(12)(A) vehicle CWA denial — the withhold's legal basis"),
    ("R-8283-SUBST", "IRS_2025_8283_INSTR", "primary", "Failure To File verbatim (disallowance list); attach-tier rules (art $20k, >$500k, not-good clothing)"),
    ("R-8283-TOTAL", "IRS_PUB526_2025", "primary", "Ordinary vs capital gain property; the 50%/30% AGI buckets the amounts route into"),
    ("R-8283-TOTAL", "IRS_2025_8283_INSTR", "secondary", "Reductions to contribution verbatim (ordinary income property basis limit — D_8283_009)"),
    ("R-8283-SCHA12", "IRS_PUB526_2025", "primary", "The line-12 bucket semantics (matches R-SCHA-CHARITABLE's inputs)"),
    ("R-8283-SCHA12", "IRS_2025_8283_INSTR", "secondary", "Carryover-year re-attachment rule (D_8283_012)"),
]

F8283_LINES: list[dict] = [
    # Header
    {"line_number": "HDR-name", "description": "Name(s) shown on your income tax return", "line_type": "input"},
    {"line_number": "HDR-id", "description": "Identifying number (SSN/ITIN; EIN for entities)", "line_type": "input"},
    {"line_number": "HDR-pte-name", "description": "Donating pass-through entity name (if originally reported elsewhere)", "line_type": "input"},
    {"line_number": "HDR-pte-ein", "description": "Donating pass-through entity identifying number", "line_type": "input"},
    {"line_number": "HDR-fampte", "description": "Family pass-through entity checkbox (conservation contributions)", "line_type": "input"},
    # Section A — Line 1 grid (rows A-D per copy; overflow = additional copies)
    {"line_number": "1(a)", "description": "Section A col (a) — name and address of the donee organization", "line_type": "input"},
    {"line_number": "1(b)", "description": "Section A col (b) — vehicle checkbox + VIN (17 chars, 0-padded)", "line_type": "input"},
    {"line_number": "1(c)", "description": "Section A col (c) — description and condition of donated property", "line_type": "input"},
    {"line_number": "1(d)", "description": "Section A col (d) — date of the contribution", "line_type": "input"},
    {"line_number": "1(e)", "description": "Section A col (e) — date acquired by donor (mo., yr.; 'Various') — rows >$500", "line_type": "input"},
    {"line_number": "1(f)", "description": "Section A col (f) — how acquired by donor — rows >$500", "line_type": "input"},
    {"line_number": "1(g)", "description": "Section A col (g) — donor's cost or adjusted basis — rows >$500 (public securities >12mo exempt)", "line_type": "input"},
    {"line_number": "1(h)", "description": "Section A col (h) — FMV / the §170(e)-reduced contribution amount", "line_type": "input"},
    {"line_number": "1(i)", "description": "Section A col (i) — method used to determine FMV", "line_type": "input"},
    # Section B Part I — line 2 type boxes
    {"line_number": "2a", "description": "SB P1 L2a — Art (contribution of $20,000 or more)", "line_type": "input"},
    {"line_number": "2b", "description": "SB P1 L2b — Qualified conservation contribution (v1 RED-defer D_8283_006)", "line_type": "input"},
    {"line_number": "2b1", "description": "SB P1 L2b(1) — Certified historic structure + NPS # (v1 RED-defer)", "line_type": "input"},
    {"line_number": "2c", "description": "SB P1 L2c — Art (contribution of less than $20,000)", "line_type": "input"},
    {"line_number": "2d", "description": "SB P1 L2d — Other real estate", "line_type": "input"},
    {"line_number": "2e", "description": "SB P1 L2e — Equipment", "line_type": "input"},
    {"line_number": "2f", "description": "SB P1 L2f — Securities (nonpublicly traded only)", "line_type": "input"},
    {"line_number": "2g", "description": "SB P1 L2g — Collectibles", "line_type": "input"},
    {"line_number": "2h", "description": "SB P1 L2h — Intellectual property", "line_type": "input"},
    {"line_number": "2i", "description": "SB P1 L2i — Vehicles", "line_type": "input"},
    {"line_number": "2j", "description": "SB P1 L2j — Clothing and household items", "line_type": "input"},
    {"line_number": "2k", "description": "SB P1 L2k — Digital assets", "line_type": "input"},
    {"line_number": "2l", "description": "SB P1 L2l — Other", "line_type": "input"},
    # Section B Part I — line 3 columns (rows A-C; one item per copy per donee)
    {"line_number": "3(a)", "description": "SB P1 L3(a) — description of donated property", "line_type": "input"},
    {"line_number": "3(b)", "description": "SB P1 L3(b) — overall physical condition (tangible/real)", "line_type": "input"},
    {"line_number": "3(c)", "description": "SB P1 L3(c) — appraised fair market value", "line_type": "input"},
    {"line_number": "3(d)", "description": "SB P1 L3(d) — date acquired by donor (mo., yr.)", "line_type": "input"},
    {"line_number": "3(e)", "description": "SB P1 L3(e) — how acquired by donor", "line_type": "input"},
    {"line_number": "3(f)", "description": "SB P1 L3(f) — donor's cost or adjusted basis", "line_type": "input"},
    {"line_number": "3(g)", "description": "SB P1 L3(g) — bargain sale: amount received", "line_type": "input"},
    {"line_number": "3(h)", "description": "SB P1 L3(h) — qualified conservation contribution relevant basis (v1 defer)", "line_type": "input"},
    {"line_number": "3(i)", "description": "SB P1 L3(i) — amount claimed as a deduction (PTE members)", "line_type": "input"},
    # Section B Part II
    {"line_number": "4a", "description": "SB P2 L4a — letter identifying the partial-interest property", "line_type": "input"},
    {"line_number": "4b1", "description": "SB P2 L4b(1) — deduction claimed for this tax year", "line_type": "input"},
    {"line_number": "4b2", "description": "SB P2 L4b(2) — deduction claimed for prior tax years", "line_type": "input"},
    {"line_number": "4c", "description": "SB P2 L4c — prior-year donee organization (if different)", "line_type": "input"},
    {"line_number": "4d", "description": "SB P2 L4d — where tangible property is located or kept", "line_type": "input"},
    {"line_number": "4e", "description": "SB P2 L4e — person (other than donee) having actual possession", "line_type": "input"},
    {"line_number": "5a", "description": "SB P2 L5a — restriction on donee's right to use or dispose? (Yes/No)", "line_type": "input"},
    {"line_number": "5b", "description": "SB P2 L5b — income/possession/acquisition rights given to another? (Yes/No)", "line_type": "input"},
    {"line_number": "5c", "description": "SB P2 L5c — restriction limiting to a particular use? (Yes/No)", "line_type": "input"},
    # Parts III-V
    {"line_number": "P3-stmt", "description": "SB P3 — taxpayer (donor) statement: items appraised ≤ $500 (identify by letter)", "line_type": "input"},
    {"line_number": "P4-name", "description": "SB P4 — appraiser name / title / address / identifying number", "line_type": "input"},
    {"line_number": "P4-date", "description": "SB P4 — appraiser signature date (wet-ink; J7)", "line_type": "input"},
    {"line_number": "P5-donee", "description": "SB P5 — donee acknowledgment: name, EIN, address, date received, unrelated-use Yes/No", "line_type": "input"},
]

F8283_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_8283_001", "title": "Noncash deduction over $500 with no Form 8283 items", "severity": "error",
     "condition": "Schedule A line-12 inputs (flat GREEN entries) total > $500 with NO NoncashContribution rows on the return",
     "message": ("Noncash charitable contributions over $500 are claimed on Schedule A line 12, but "
                 "no Form 8283 items are entered. §170(f)(11)(B) requires Form 8283 — enter the "
                 "donated items so the form can be produced (a bare total cannot populate the "
                 "form's required columns), or reduce the entry to $500 or less."),
     "notes": "Replaces stub D001. The rows-present path never fires this (the form auto-engages)."},
    {"diagnostic_id": "D_8283_002", "title": "Section B item without a qualified appraisal — deduction withheld", "severity": "error",
     "condition": "a row routed to Section B whose appraisal-obtained assertion is unchecked",
     "message": ("This item (or group) exceeds $5,000 — §170(f)(11)(C) allows NO deduction unless a "
                 "written qualified appraisal by a qualified appraiser is obtained. Check "
                 "'qualified appraisal obtained' once it is in hand (or correct the amount). The "
                 "amount is still claimed on Schedule A line 12 — expect disallowance on exam if "
                 "the appraisal is missing. Reasonable-cause relief exists but must be documented."),
     "notes": ("J6 RULED warn-only (Ken 2026-07-03): error fires, feed flows. Publicly traded "
               "securities / IP / inventory / gross-proceeds vehicles never route here.")},
    {"diagnostic_id": "D_8283_003", "title": "Vehicle over $500 without Form 1098-C / written acknowledgment — deduction withheld", "severity": "error",
     "condition": "a vehicle row with amount > $500 whose 1098-C/CWA-attached assertion is unchecked",
     "message": ("§170(f)(12)(A) allows NO deduction for a donated vehicle claimed over $500 unless "
                 "the contemporaneous written acknowledgment (Form 1098-C or equivalent) is included "
                 "with the return. Check the acknowledgment-attached box once it is in hand — the "
                 "amount is still claimed on Schedule A line 12 meanwhile. E-file: the 1098-C rides "
                 "as a binary attachment; paper: attach Copy B."),
     "notes": ("J6 RULED warn-only (Ken 2026-07-03): error fires, feed flows. Also enter the VIN "
               "when no 1098-C is attached (render requires it).")},
    {"diagnostic_id": "D_8283_004", "title": "Appraisal must be ATTACHED to the return — deduction withheld", "severity": "error",
     "condition": "an attach-tier row (art ≥ $20,000; any item > $500,000; not-good-condition clothing/household > $500) whose appraisal-attached assertion is unchecked",
     "message": ("This item requires the signed qualified appraisal to be ATTACHED to the return "
                 "(art of $20,000 or more; deductions over $500,000 per §170(f)(11)(D); clothing or "
                 "household items not in good used condition over $500). Check 'appraisal attached' "
                 "once it is included — the amount is still claimed on Schedule A line 12 "
                 "meanwhile. E-file: attach the appraisal PDF as a binary attachment."),
     "notes": ("J6 RULED warn-only (Ken 2026-07-03): error fires, feed flows. The "
               "appraisal-OBTAINED assertion (D_8283_002) is also required — both boxes.")},
    {"diagnostic_id": "D_8283_005", "title": "Section A columns (e)/(f)/(g) required for items over $500", "severity": "error",
     "condition": "a Section A row with amount > $500 missing date acquired, how acquired, or cost basis (publicly traded security rows exempt)",
     "message": ("Items over $500 in Section A must show the date acquired, how acquired, and the "
                 "donor's cost or adjusted basis (columns (e), (f), (g)). Complete the missing "
                 "entries — an incomplete Form 8283 can disallow the deduction. If the information "
                 "is genuinely unavailable with reasonable cause, attach an explanation statement "
                 "(the deduction then survives; the software still prints what is entered)."),
     "notes": "Error WITHOUT withhold (the §170(f)(11)(A)(ii)(II) reasonable-cause escape is statement-curable)."},
    {"diagnostic_id": "D_8283_006", "title": "Qualified conservation contribution — not supported, prepare manually", "severity": "error",
     "condition": "a row whose property type is qualified conservation contribution / certified historic structure",
     "message": ("Not supported — prepare manually: qualified conservation contributions (easements, "
                 "remainder interests, historic structures). The §170(h)(7) partnership/S-corp "
                 "disallowance apparatus, relevant-basis computations, NPS numbers, Form 8283-V "
                 "filing fees, and the required valuation statements are not modeled. The item's "
                 "amount is WITHHELD from Schedule A line 12 — compute the allowable deduction "
                 "manually and use the line-12 direct entry (GREEN override) with a manually "
                 "prepared Form 8283/attachments."),
     "notes": "J4 RED-defer. ~Zero firm volume; a specialist minefield (2.5×-basis, three exceptions)."},
    {"diagnostic_id": "D_8283_007", "title": "Form 8283 item incomplete (donee/description/date/amount)", "severity": "error",
     "condition": "a row missing donee name, description, date of contribution, a positive amount, or dated outside the return tax year",
     "message": ("Every Form 8283 item needs the donee organization's name and address, a "
                 "description of the property, the date of the contribution (within the return tax "
                 "year), and the contribution amount. An incomplete or non-responsive Form 8283 is "
                 "treated as not filed and the deduction can be disallowed (i8283, Failure To "
                 "File)."),
     "notes": "Completeness gate — no withhold (entry-level; the preparer is mid-entry)."},
    {"diagnostic_id": "D_8283_008", "title": "Unclassified rows while the charitable AGI limitation binds", "severity": "warning",
     "condition": "any row's capital-gain-property question is unanswered (defaulted to the 50% bucket) AND the Schedule A charitable limitation produced a carryover this year",
     "message": ("One or more donated items are not classified as ordinary vs capital gain "
                 "property (they defaulted to the 50% AGI bucket), and the charitable deduction "
                 "limitation is binding on this return — the bucket choice is changing the allowed "
                 "deduction and the carryover. Answer the capital-gain-property question on each "
                 "item (property held over a year that would produce long-term gain belongs in the "
                 "30% bucket)."),
     "notes": "J2 — quiet on the mass case (limits not binding); fires exactly when the default matters."},
    {"diagnostic_id": "D_8283_009", "title": "Ordinary income property entered above basis — §170(e)(1) reduction check", "severity": "warning",
     "condition": "a row classified (or defaulted) ordinary with cost basis entered and amount > basis",
     "message": ("This item is ordinary income property (or unclassified) and its contribution "
                 "amount exceeds the donor's basis. §170(e)(1) limits the deduction for ordinary "
                 "income property to basis (FMV minus the ordinary-income appreciation). Column (h) "
                 "must carry the REDUCED amount with a reduction statement attached — verify the "
                 "entered amount, or classify the item as capital gain property if it would produce "
                 "long-term gain."),
     "notes": "J3 — the reduction stays preparer-applied; this is the guardrail."},
    {"diagnostic_id": "D_8283_010", "title": "Pass-through-entity 8283 mechanics not modeled (stated boundary)", "severity": "info",
     "condition": "the donating-PTE header name/EIN or the family-PTE checkbox is filled",
     "message": ("A pass-through entity's Form 8283 is referenced. The member-of-PTE attachment "
                 "choreography (attach the donating entity's Form 8283 plus any intermediate "
                 "tier's, in addition to this one) is manual — include the copies as PDF "
                 "attachments (e-file) or with the paper return. Signature parts III-V are not "
                 "required on a member's own copy."),
     "notes": "Stated boundary. Header fields render as entered."},
    {"diagnostic_id": "D_8283_011", "title": "Section B appraiser / donee-acknowledgment block incomplete", "severity": "warning",
     "condition": "a Section B row missing the donee EIN, or the appraiser name/identifying number (conservation defers excluded)",
     "message": ("Section B requires the appraiser's declaration (Part IV — name, address, "
                 "identifying number, signature) and the donee's acknowledgment (Part V — EIN, "
                 "signature, date received) before filing. Signatures are wet-ink; the e-filed "
                 "return carries the SIGNED copy as a PDF attachment (or Form 8453). Complete the "
                 "blocks — if the donee's signature is impossible to get, attach a detailed "
                 "explanation instead."),
     "notes": "J7. Warning (not withhold): the appraisal assertions (D_8283_002/004) carry the statutory teeth."},
    {"diagnostic_id": "D_8283_012", "title": "Charitable carryover claimed — attach the prior-year Form 8283 copy", "severity": "info",
     "condition": "Schedule A line 13 (carryover from prior year) > 0",
     "message": ("A charitable contribution carryover is claimed. If the carried-over contribution "
                 "was noncash, attach a completed copy of the PRIOR year's Form 8283 (and its "
                 "appraisal, if one was required to be attached that year) to this return — one per "
                 "carried-over contribution (i8283, Noncash Contributions Carried Over)."),
     "notes": "Manual attachment; the proforma producer may automate the copy later."},
    {"diagnostic_id": "D_8283_013", "title": "Clothing/household item not in good used condition, $500 or less — not deductible", "severity": "error",
     "condition": "a row flagged not-in-good-used-condition with amount ≤ $500",
     "message": ("No deduction is allowed for clothing or household items that are not in good used "
                 "condition or better unless the claimed value exceeds $500 AND a qualified "
                 "appraisal is attached (§170(f)(16)). Remove the item, or correct the condition "
                 "flag if the item is in fact in good used condition — as entered, this amount is "
                 "not deductible."),
     "notes": ("J6-family: error fires, feed follows the entry (Ken 2026-07-03 warn-only ruling). "
               "The >$500 arm routes to Section B + D_8283_004 instead.")},
]

F8283_SCENARIOS: list[dict] = [
    {"scenario_name": "8283-T1 — ATS Scenario 2 (Jones): Section A clothes & toys, FMV under basis", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "rows": [
         {"donee_name": "Goodwill", "donee_city": "Charleston", "donee_state": "SC",
          "description": "Clothes & toys", "date_contributed": "2025-11-13",
          "date_acquired": "Various", "how_acquired": "Purchase", "cost_basis": 3470,
          "amount": 700, "valuation_method": "Thrift Store Value", "capgain_property": False}]},
     "expected_outputs": {"f8283_total": 700, "f8283_bucket_50": 700, "f8283_bucket_30": 0,
                          "f8283_engaged": True, "row_sections": ["A"],
                          "scha_line12_default": 700, "D_8283_009": False},
     "notes": ("THE S2 PIN — the scenario PDF's own 8283 verbatim (basis 3,470 / FMV 700 / thrift "
               "store value). FMV below basis: used clothing needs no §170(e) reduction; "
               "D_8283_009 quiet (700 < 3,470). Engaged (700 > 500), Section A, 50% bucket.")},
    {"scenario_name": "8283-T2 — below $500: feeds Schedule A, files no form", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"tax_year": 2025, "rows": [
         {"donee_name": "Church", "description": "Used furniture", "date_contributed": "2025-06-01",
          "amount": 400, "capgain_property": False}]},
     "expected_outputs": {"f8283_total": 400, "f8283_engaged": False, "scha_line12_default": 400,
                          "D_8283_001": False, "D_8283_005": False},
     "notes": ("A $400 donation is deductible WITHOUT Form 8283 (§170(f)(11)(B) threshold). The "
               "feed flows; the packet carries no 8283; cols e/f/g not required at ≤$500.")},
    {"scenario_name": "8283-T3 — Section B routing + the appraisal withhold", "scenario_type": "edge_case", "sort_order": 3,
     "inputs": {"tax_year": 2025, "rows": [
         {"donee_name": "Museum", "description": "Antique dining set", "date_contributed": "2025-05-15",
          "date_acquired": "06/2010", "how_acquired": "Inheritance", "cost_basis": 2000,
          "amount": 6000, "capgain_property": True, "appraisal_obtained": False}]},
     "expected_outputs": {"row_sections": ["B"], "f8283_row_withheld": [False], "D_8283_002": True,
                          "f8283_total": 6000, "f8283_bucket_30": 6000, "scha_line12_default": 6000},
     "notes": ("6,000 > 5,000 -> Section B; appraisal unasserted -> D_8283_002 ERROR fires but the "
               "6,000 still feeds the 30% bucket (J6 Ken ruling 2026-07-03: warn only, feed "
               "anyway). Flipping appraisal_obtained=True clears the error, numbers unchanged.")},
    {"scenario_name": "8283-T4 — publicly traded stock over $5,000 stays in Section A", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"tax_year": 2025, "rows": [
         {"donee_name": "University", "description": "AAPL, 40 shares, common, exchange-listed",
          "date_contributed": "2025-04-01", "date_acquired": "03/2019", "how_acquired": "Purchase",
          "amount": 8000, "capgain_property": True, "public_security": True}]},
     "expected_outputs": {"row_sections": ["A"], "f8283_total": 8000, "f8283_bucket_30": 8000,
                          "f8283_engaged": True, "D_8283_002": False, "D_8283_005": False},
     "notes": ("§170(f)(11)(A)(ii)(I): public securities are exempt from the appraisal tiers at any "
               "amount -> Section A; col (g) basis not required (held > 12 months); LT stock is "
               "capital gain property -> 30% bucket.")},
    {"scenario_name": "8283-T5 — vehicle over $500 without the 1098-C: withheld", "scenario_type": "edge_case", "sort_order": 5,
     "inputs": {"tax_year": 2025, "rows": [
         {"donee_name": "Kars4Kids", "description": "2018 Honda Civic, fair, 90,000 miles",
          "is_vehicle": True, "vin": "0001HGBH41JXMN10918", "date_contributed": "2025-08-20",
          "date_acquired": "05/2018", "how_acquired": "Purchase", "cost_basis": 22000,
          "amount": 3000, "capgain_property": False, "ack_1098c": False}]},
     "expected_outputs": {"row_sections": ["A"], "f8283_row_withheld": [False], "D_8283_003": True,
                          "scha_line12_default": 3000},
     "notes": ("§170(f)(12)(A): no CWA included = the deduction is legally denied, but per the J6 "
               "ruling the ERROR fires while 3,000 still feeds the 50% bucket — the preparer "
               "cures by checking ack_1098c. FMV-exception vehicle at 6,000 -> Section B instead. "
               "NOTE: without the CWA the row is Section A only because amount ≤ 5,000 (the "
               "gross-proceeds exception needs the ack).")},
    {"scenario_name": "8283-T6 — bucket routing matters: AGI limits bind", "scenario_type": "edge_case", "sort_order": 6,
     "inputs": {"tax_year": 2025, "agi": 10000, "scha_charitable_cash": 0, "scha_charitable_carryover_in": 0,
      "rows": [
         {"donee_name": "College", "description": "Appreciated land parcel", "date_contributed": "2025-03-01",
          "date_acquired": "01/2005", "how_acquired": "Purchase", "cost_basis": 1000,
          "amount": 4000, "capgain_property": True, "appraisal_obtained": False,
          "public_security": False, "note": "kept ≤5000 to stay Section A"},
         {"donee_name": "Goodwill", "description": "Household goods", "date_contributed": "2025-03-01",
          "date_acquired": "Various", "how_acquired": "Purchase", "cost_basis": 9000,
          "amount": 6000, "capgain_property": False, "appraisal_obtained": True}]},
     "expected_outputs": {"f8283_bucket_30": 4000, "f8283_bucket_50": 6000,
                          "scha_line14": 6000, "scha_charitable_carryover_out": 4000},
     "notes": ("HAND-COMPUTED against the SCHEDULE_A worksheet (R-SCHA-CHARITABLE, TY2025 — no "
               "floor): cash_lim 0; fifty-bucket lim = min(6000, 50%×10,000) = 5,000; capgain lim "
               "= min(4000, 30%×10,000) = 3,000; allowed = min(0+5,000+3,000, 60%×10,000) = 6,000; "
               "carryover_out = 10,000 − 6,000 = 4,000. The 4,000 land row is Section A (≤5,000) "
               "so no appraisal tier. Misrouting the land to the 50% bucket would give allowed = "
               "min(10,000 fifty-lim capped 5,000, 6,000) — a different, WRONG answer; this pins "
               "the routing.")},
    {"scenario_name": "8283-T7 — flat direct entry stays the GREEN override", "scenario_type": "normal", "sort_order": 7,
     "inputs": {"tax_year": 2025, "scha_charitable_noncash_fmv_entered": 650, "rows": [
         {"donee_name": "Goodwill", "description": "Clothing", "date_contributed": "2025-10-01",
          "date_acquired": "Various", "how_acquired": "Purchase", "cost_basis": 2000,
          "amount": 700, "capgain_property": False}]},
     "expected_outputs": {"f8283_bucket_50": 700, "scha_line12_noncash_input": 650},
     "notes": ("J1: the non-zero flat entry (GREEN) wins over the 700 auto-total (YELLOW) for its "
               "field. The capgain field, not overridden, still defaults to its bucket (0 here). "
               "Backward-compatible: existing flat-entry returns never move.")},
    {"scenario_name": "8283-T8 — clothing not in good used condition", "scenario_type": "edge_case", "sort_order": 8,
     "inputs": {"tax_year": 2025, "rows": [
         {"donee_name": "Shelter", "description": "Worn designer coat", "not_good_condition": True,
          "date_contributed": "2025-02-01", "date_acquired": "01/2020", "how_acquired": "Purchase",
          "cost_basis": 4000, "amount": 900, "capgain_property": False,
          "appraisal_obtained": True, "appraisal_attached": False}]},
     "expected_outputs": {"row_sections": ["B"], "f8283_row_withheld": [False], "D_8283_004": True,
                          "f8283_total": 900},
     "notes": ("Not-good-condition + >$500 -> Section B regardless of the $5,000 test AND the "
               "appraisal must be ATTACHED (i8283 verbatim). attached=False -> D_8283_004 ERROR, "
               "feed flows (J6 ruling). At ≤$500 not-good-condition the item is nondeductible "
               "outright (D_8283_013, 8283-T8b).")},
    {"scenario_name": "8283-T9 — conservation easement: RED defer, feed withheld", "scenario_type": "edge_case", "sort_order": 9,
     "inputs": {"tax_year": 2025, "rows": [
         {"donee_name": "Land Trust", "description": "Conservation easement, 40 acres",
          "property_type": "conservation", "date_contributed": "2025-09-01",
          "date_acquired": "07/1998", "how_acquired": "Purchase", "cost_basis": 50000,
          "amount": 25000, "capgain_property": True, "appraisal_obtained": True,
          "appraisal_attached": True}]},
     "expected_outputs": {"D_8283_006": True, "f8283_row_withheld": [True], "f8283_total": 0,
                          "scha_line12_default": 0},
     "notes": ("J4 — even fully-substantiated conservation rows are withheld v1 (the §170(h)(7) "
               "apparatus is unmodeled). The preparer computes manually and uses the GREEN "
               "override; the RED says exactly that.")},
    {"scenario_name": "8283-T10 — art at $22,000: attach tier", "scenario_type": "edge_case", "sort_order": 10,
     "inputs": {"tax_year": 2025, "rows": [
         {"donee_name": "Art Museum", "description": "Oil painting, excellent condition",
          "property_type": "art20k", "condition": "Excellent", "date_contributed": "2025-12-01",
          "date_acquired": "06/2001", "how_acquired": "Purchase", "cost_basis": 5000,
          "amount": 22000, "capgain_property": True, "appraisal_obtained": True,
          "appraisal_attached": False}]},
     "expected_outputs": {"row_sections": ["B"], "D_8283_004": True, "f8283_row_withheld": [False],
                          "f8283_bucket_30": 22000},
     "notes": ("Art ≥ $20,000: the signed appraisal must be ATTACHED (i8283 verbatim). The ERROR "
               "fires until attached; 22,000 feeds the 30% bucket throughout (J6 ruling).")},
    {"scenario_name": "8283-T11 — single item over $500,000: §170(f)(11)(D) attach tier", "scenario_type": "edge_case", "sort_order": 11,
     "inputs": {"tax_year": 2025, "rows": [
         {"donee_name": "Foundation", "description": "Commercial real property, 12 Main St",
          "property_type": "real_estate", "condition": "Good", "date_contributed": "2025-06-30",
          "date_acquired": "03/1995", "how_acquired": "Purchase", "cost_basis": 150000,
          "amount": 600000, "capgain_property": True, "appraisal_obtained": True,
          "appraisal_attached": False}]},
     "expected_outputs": {"row_sections": ["B"], "D_8283_004": True, "f8283_row_withheld": [False],
                          "f8283_bucket_30": 600000},
     "notes": ("> $500,000 -> the appraisal itself must be attached to the return "
               "(§170(f)(11)(D) verbatim). ERROR until attached; the feed flows (J6 ruling).")},
    {"scenario_name": "8283-T12 — Section A row over $500 with columns e/f/g missing", "scenario_type": "edge_case", "sort_order": 12,
     "inputs": {"tax_year": 2025, "rows": [
         {"donee_name": "Library", "description": "Book collection", "date_contributed": "2025-04-15",
          "date_acquired": "", "how_acquired": "", "cost_basis": None,
          "amount": 700, "capgain_property": False}]},
     "expected_outputs": {"row_sections": ["A"], "D_8283_005": True, "f8283_row_withheld": [False],
                          "f8283_total": 700, "scha_line12_default": 700},
     "notes": ("Error WITHOUT withhold: the (B)-tier completeness gap is curable by a "
               "reasonable-cause explanation statement (§170(f)(11)(A)(ii)(II)), so the feed "
               "flows while the preparer completes the row. Contrast the statutory-denial "
               "withholds (T3/T5/T8-T11).")},
    {"scenario_name": "8283-T13 — ordinary property above basis: §170(e)(1) guardrail", "scenario_type": "edge_case", "sort_order": 13,
     "inputs": {"tax_year": 2025, "rows": [
         {"donee_name": "Charity", "description": "Artist's own painting (self-created)",
          "date_contributed": "2025-07-04", "date_acquired": "01/2025", "how_acquired": "Self-created",
          "cost_basis": 300, "amount": 2500, "capgain_property": False}]},
     "expected_outputs": {"D_8283_009": True, "f8283_row_withheld": [False], "f8283_total": 2500},
     "notes": ("Self-created art is ordinary income property; entered amount 2,500 > basis 300 -> "
               "the warning fires (the deduction should be 300 — J3 keeps the reduction "
               "preparer-applied, so the feed follows the ENTERED amount; the warning is the "
               "guardrail, not a silent rewrite).")},
]

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-8283-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Bucket feed: non-withheld rows total into the Schedule A line-12 inputs (50% ordinary / 30% capgain) as YELLOW defaults; non-zero flat entries win per field (GREEN)",
     "description": ("Validates R-8283-TOTAL + R-8283-SCHA12 (J1/J2). Bugs it catches: withheld "
                     "rows leaking into a bucket, capgain rows landing in the 50% bucket (T6's "
                     "wrong-answer case), or the auto-total stomping a preparer's direct entry."),
     "definition": {"kind": "formula_check", "form": "8283",
                    "formula": ("bucket_30 == sum(amount where capgain_property is True and not withheld); "
                                "bucket_50 == sum(amount where capgain_property in (False, None) and not withheld); "
                                "scha_noncash_input == (flat_noncash if flat_noncash > 0 else bucket_50); "
                                "scha_capgain_input == (flat_capgain if flat_capgain > 0 else bucket_30)")},
     "sort_order": 1},
    {"assertion_id": "FA-1040-8283-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Engagement: form files/prints iff total > $500; the Schedule A feed flows regardless of engagement",
     "description": ("Validates R-8283-FILE. Bugs it catches: a sub-$500 donation losing its "
                     "deduction because the form didn't engage, or a $700 donation filing no 8283 "
                     "(the §170(f)(11)(B) disallowance)."),
     "definition": {"kind": "conditional_check", "form": "8283",
                    "checks": [{"when": "f8283_total > 500", "assert": "f8283_engaged and form_8283_in_packet"},
                               {"when": "f8283_total <= 500", "assert": "not f8283_engaged and feed_still_flows"}]},
     "sort_order": 2},
    {"assertion_id": "FA-1040-8283-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Section routing invariants: B iff >$5,000 per row, except the readily-valued Section-A list; not-good-condition clothing >$500 is always B",
     "description": ("Validates R-8283-SECTION against §170(f)(11)(A)(ii)(I) + i8283. Bugs it "
                     "catches: public securities forced into Section B (nagging for an appraisal "
                     "the statute doesn't require), or a gross-proceeds vehicle at $7,000 leaving "
                     "Section A."),
     "definition": {"kind": "invariant_check", "form": "8283",
                    "invariants": ["section[row] == 'B' iff (amount > 5000 and not readily_valued(row)) or (not_good_condition and amount > 500) or conservation(row)",
                                   "readily_valued = public_security or intellectual or inventory_1221 or (is_vehicle and not vehicle_fmv_exception and ack_1098c)"]},
     "sort_order": 3},
    {"assertion_id": "FA-1040-8283-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Diagnostic/feed split per the J6 ruling: substantiation gaps fire ERROR while the feed FLOWS; the conservation defer alone fires RED and feeds NOTHING",
     "description": ("Validates R-8283-SUBST as Ken RULED it (2026-07-03: warn only, feed anyway; "
                     "conservation is the single withhold). Bugs it catches: a later change "
                     "quietly re-introducing a substantiation withhold (re-litigating the "
                     "ruling), or the conservation row's amount leaking into a bucket while "
                     "D_8283_006 shows (the gate-and-cascade-must-agree lesson — diagnostic and "
                     "feed must read the same row helpers)."),
     "definition": {"kind": "gating_check", "form": "8283",
                    "expect": {"substantiation_errors_fire": True, "substantiation_feed_flows": True,
                               "conservation_red_fires": True, "conservation_feed_withheld": True},
                    "blockers": ["conservation_defer_no_feed"]},
     "sort_order": 4},
    {"assertion_id": "FA-1040-8283-05", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "End-to-end: 8283 rows -> Schedule A line 12 -> line 14 (bucket worksheet) -> line 17 -> 1040 line 12e (the S2 pin: 700)",
     "description": ("Validates the full chain through the UNCHANGED R-SCHA-CHARITABLE worksheet "
                     "(T1/T6 pins). Bug it catches: the feeder writing line 12's FACE directly "
                     "instead of the worksheet INPUTS (which would skip the AGI limits and the "
                     "2026 floor)."),
     "definition": {"kind": "flow_assertion", "form": "8283",
                    "checks": [{"source_line": "1(h)", "must_write_to": ["SCHEDULE_A.line12_inputs"],
                                "never_write_to": ["SCHEDULE_A.line14_face_direct"],
                                "chain": "8283 buckets -> Sch A 12 -> 14 (limits) -> 17 -> 1040 12e"}]},
     "sort_order": 5},
]


FORMS: list[dict] = [
    {"identity": F8283_IDENTITY, "facts": F8283_FACTS, "rules": F8283_RULES, "lines": F8283_LINES,
     "diagnostics": F8283_DIAGNOSTICS, "scenarios": F8283_SCENARIOS, "rule_links": F8283_RULE_LINKS},
]

# The load_1120s_complete.py placeholder content this loader RETIRES (deletes):
STUB_RULE_IDS = ["R001", "R002", "R003", "R004", "R005"]
STUB_LINE_NUMBERS = ["SA-1", "SA-2", "SA-3", "SA-4", "SA-5", "SA-6", "SA-7", "SB-1"]
STUB_DIAGNOSTIC_IDS = ["D001", "D002", "D003"]
STUB_FACT_KEYS = ["total_noncash_contributions", "section_a_items", "section_b_items",
                  "donee_organization", "property_description", "date_contributed",
                  "date_acquired", "donor_cost_or_basis", "fair_market_value", "fmv_method"]
STUB_SCENARIO_NAMES = ["Section A items — under $5K", "Section B items — over $5K with appraisal"]


class Command(BaseCommand):
    help = "Load the 8283 spec (noncash charitable contributions, ATS Scenario 2). Amends the shared stub by lookup. Refuses until READY_TO_SEED=True."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad 8283 spec (noncash charitable contributions, ATS Scenario 2)\n"))
        self._load_topics()
        sources = self._load_sources()
        self._load_new_excerpts_on_existing(sources)
        for spec in FORMS:
            form = self._upsert_form(spec["identity"])
            self._retire_stub(form)
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
                "\nREFUSING TO SEED 8283: not cleared to seed.\n\n"
                "Gated until Ken's review walk (J1 feeder convention; J2 bucket default +\n"
                "bind-gated warning; J3 preparer-applied §170(e) reductions; J4 conservation\n"
                "defer; J5 one-row-per-group; J6 substantiation withholds; J7 wet-ink parts\n"
                "IV/V + PDF-attachment e-file note — plus the stub retirement).\n\n"
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
        """Amend the SHARED 8283 row by lookup — never write entity_types over an
        existing row (the rs-amend-shared-form lesson: update_or_create with
        entity_types in defaults clobbered a multi-entity form once)."""
        form = TaxForm.objects.filter(
            form_number=identity["form_number"], jurisdiction=FORM_JURISDICTION,
            tax_year=FORM_TAX_YEAR, version=FORM_VERSION).first()
        if form:
            form.form_title = identity["form_title"]
            form.status = FORM_STATUS
            form.notes = identity["notes"]
            form.save(update_fields=["form_title", "status", "notes"])
            self.stdout.write(f"Amended {identity['form_number']} (entity_types preserved: {form.entity_types})")
        else:
            form = TaxForm.objects.create(
                form_number=identity["form_number"], jurisdiction=FORM_JURISDICTION,
                tax_year=FORM_TAX_YEAR, version=FORM_VERSION,
                form_title=identity["form_title"], entity_types=FORM_ENTITY_TYPES_IF_CREATING,
                status=FORM_STATUS, notes=identity["notes"])
            self.stdout.write(f"Created {identity['form_number']}")
        return form

    def _retire_stub(self, form: TaxForm):
        """Delete the load_1120s_complete.py placeholder content (unnamed rules,
        generic SA-*/SB-1 lines, D001-D003, 2 placeholder tests). Never seeded to
        tts; never Ken-approved; replaced by the authored spec below."""
        counts = {
            "facts": FormFact.objects.filter(tax_form=form, fact_key__in=STUB_FACT_KEYS).delete()[0],
            "rules": FormRule.objects.filter(tax_form=form, rule_id__in=STUB_RULE_IDS).delete()[0],
            "lines": FormLine.objects.filter(tax_form=form, line_number__in=STUB_LINE_NUMBERS).delete()[0],
            "diagnostics": FormDiagnostic.objects.filter(tax_form=form, diagnostic_id__in=STUB_DIAGNOSTIC_IDS).delete()[0],
            "tests": TestScenario.objects.filter(tax_form=form, scenario_name__in=STUB_SCENARIO_NAMES).delete()[0],
        }
        retired = ", ".join(f"{v} {k}" for k, v in counts.items() if v)
        self.stdout.write(f"  Stub retired: {retired or 'nothing to retire (already clean)'}")

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
        form = TaxForm.objects.filter(form_number="8283").first()
        if form:
            uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
            self.stdout.write("8283: all rules cited" if not uncited
                              else self.style.WARNING(f"8283 uncited rules: {len(uncited)}"))
