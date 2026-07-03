"""Load the FORM_7217 spec — Partner's Report of Property Distributed by a
Partnership (§732 basis of distributed property; §731 gain recognition).
Informational attachment to the partner's return — one Form 7217 PER
DISTRIBUTION DATE. No dollar flows to the 1040 in v1 (see boundaries).

Trigger: MeF ATS Scenario 12 (Sam Gardenia) — the next smallest-first 1040
ATS scenario per Ken's 2026-07-02 ruling. Every remaining scenario needs an
unbuilt tax-law form first (the DECISIONS sequencing rule); Form 7217 is
Scenario 12's form. ⚠️ S12's answer key OMITS QBI entirely and uses the
pre-OBBBA $15,000 standard deduction (the draft form face itself prints
$15,750) — enacted-law pins are hand-computed at the mapper leg per
[[ats-answer-keys-pre-obbba-stale]]. The key's OWN Form 7217 Part II is
internally inconsistent: col (e) total 4,000 contradicts its line 10 of
6,000, and it lists "CASH" as a Part II property when line 3 explicitly
EXCLUDES cash. The engine follows §732; scenario 7217-T1 pins it.

OBBBA / sunset check (SEASON_PLAN appendix 4, run at this spec leg as
required): Form 7217 is a REPORTING form for §732 basis — not a credit; no
termination provision exists. VERIFIED 2026-07-02: 26 U.S.C. §732's
amendment history runs only through P.L. 106-170 (1999) — P.L. 119-21
(OBBBA) did NOT touch §§731/732/733/737. The December 2024 revision of the
form + instructions remains current ("Use the December 2024 version ... for
tax years beginning in 2024 or later, until a later revision is issued").
One post-publication development found and encoded: the IRS 2026-04-27
update re-sourcing lines 3/5a/5b to NEW Schedule K-1 (1065) box 19 codes for
TY2025+ (codes B/C/G basis; A/D/F money; A/F securities statement) — carried
verbatim in the IRS_2024_7217_INSTR excerpts below; the instructions
revision carrying it is announced for December 2026.

Sources VERIFIED 2026-07-02 (all verbatim, fetched today):
  - 26 U.S.C. §732 (a)(1)/(a)(2)/(b)/(c)(1)-(3) — law.cornell.edu (USC_26_732).
  - 26 U.S.C. §731(a) incl. the character sentence ("gain or loss from the
    sale or exchange of the partnership interest") — law.cornell.edu (USC_26_731).
  - i7217 (Rev. December 2024) — who-must-file / don't-file, per-line rules,
    Example 1 (Jordan) + Example 2 (Alex — the full §732(c) waterfall with
    the IRS's own worked answer), the 731(c)(4) col-(e) exclusion.
  - Form 7217 face (Rev. 12-2024) — f7217.pdf fetched from irs.gov.
  - IRS 2026-04-27 update (box 19 codes, TY2025+) — irs.gov/forms-pubs.

JUDGMENT ITEMS FOR KEN (Authoritative-Source Rule #4 — review walk):
  J1. Line-7 gain flow — RULED 2026-07-02 (AskUserQuestion): Ken chose
      "Wire §731(a)(1) gain to Sch D now" over the recommended defer. The
      face-correct landing per the Partner's Instructions for Schedule K-1
      (Form 1065), box 19 (verbatim, fetched 2026-07-02): "the excess is
      treated as gain from the sale or exchange of your partnership
      interest. Generally, this gain is treated as gain from the sale of a
      capital asset and should be reported on Form 8949 and the Schedule D
      for your return." ENCODED: line 7 > 0 feeds a synthesized no-1099-B
      Form 8949 row (Part I box C short-term / Part II box F long-term per
      the holding-period preparer assertion; proceeds = line 5c, basis =
      line 6, gain = line 7) which then rides the existing 8949 → Schedule D
      machinery. Holding period UNASSERTED → the feed is WITHHELD +
      D_7217_011 RED (never silently default a character); asserted →
      D_7217_002 (info) reports the auto-feed. Reg §1.1223-3 split holding
      periods are out of scope (single ST/LT assertion — stated boundary).
      The §751 hot-asset ordinary-income attribution stays under the
      D_7217_001 §751(b) defer.
  J2. §731(a)(2) liquidating LOSS (money + receivables/inventory only):
      detected when Σ col (e) < line 10 on a liquidating distribution — the
      one case where the form face's "line 10 should equal Part II B(e)"
      tie breaks BY LAW. v1 = RED defer (D_7217_006, manual Schedule D).
  J3. §737 gain: line 4 EXCLUDES it, line 9 INCLUDES it (i7217 verbatim).
      Encoded literally: line 9 = max(0, line 4 − line 5a) + §737 gain (the
      floor applies before the add, per the face's own order of operations).
      The §737 gain's own income reporting is a RED defer (D_7217_009).
  J4. Rounding: §732(c) is silent on rounding proportional allocations.
      Encoded: exact-decimal waterfall, each col (e) rounded half-up to
      whole dollars, any residue applied to the largest-allocation row so
      Σ col (e) always equals line 10 (the K-1 allocator's convention).
  J5. Property classification (§751(c) unrealized receivable / §751(d)
      inventory vs other) is a PREPARER ASSERTION per row. Unclassified →
      D_7217_008 RED and the entire Part II allocation is WITHHELD (all
      col (e) = 0) — computing a wrong tier is worse than computing nothing.
  J6. Marketable securities (§731(c)): rows flagged is_security feed line 5b
      (YELLOW auto-total; direct-entry override GREEN — the house feeder
      convention) AND stay in Part II/line 3 (i7217: "other than cash, but
      including marketable securities"). Line 9 subtracts line 5a ONLY. The
      §731(c)(4) basis step-up is never computed (col (e) excludes it per
      i7217 — stated boundary tied to J1's gain defer).

v1 SCOPE BOUNDARIES (stated, not silent):
  - No outside-basis tracking: line 4 is the partner's own computation
    (i7217: "you are responsible for calculating this amount") — preparer
    input, nullable, RED when missing (D_7217_004). The 1065-side §704(d)
    basis machinery is explicitly out of scope (DECISIONS: K-1 flow-through).
  - §751(b) recharacterization: line 2 Yes → D_7217_001 RED (attach the
    Reg 1.751-1(b)(5) statement + compute manually). Face still computes.
  - Line-7 gain IS wired (J1, Ken 2026-07-02): a synthesized 8949 row per
    the holding-period assertion. §737 gain and the §731(a)(2) loss remain
    manual REDs (J2/J3 — Ken kept the defers).
  - §707(a)(1) service payments / §707(a)(2)(B) disguised sales: the
    don't-file screens are instruction notes on the form-level facts; no
    adjudication.
  - 732(d)/732(f)/734(b)/743(b): col (c) indicator checkboxes only — the
    adjusted col (b) amounts come from the K-1 19C statement / 732(d)
    statement as entered; the software does not compute the adjustments.

SAFETY GUARD: READY_TO_SEED=False — Ken has NOT approved. Do not seed.
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


READY_TO_SEED = False  # Ken's review walk pending — J1..J6 in the module docstring.


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1040"]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("pship_distributions",
     "Partnership property distributions — §732 basis of distributed property, §731 gain/loss, Form 7217"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "USC_26_732",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2024,
        "tax_year_end": 2026,
        "title": "26 U.S.C. §732 — Basis of distributed property other than money",
        "citation": "IRC §732 (amendment history through P.L. 106-170 (1999); NOT amended by P.L. 119-21)",
        "issuer": "US Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/732",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": True,
        "notes": (
            "Fetched 2026-07-02 (law.cornell.edu). The SEASON_PLAN appendix-4 sunset check for Form "
            "7217, run at this spec leg: §732 is a basis provision, not a credit — no termination "
            "exists, and the section's amendment notes run only through 1999 (OBBBA untouched). "
            "REQUIRES HUMAN REVIEW: Ken confirms the §732(c) waterfall encoding (tier-1 receivables/"
            "inventory at basis, never above; (c)(2) increase = appreciation-proportional capped then "
            "FMV-proportional, tier-2 only; (c)(3) decrease = depreciation-proportional capped then "
            "adjusted-basis-proportional) and the J4 rounding convention."
        ),
        "topics": ["pship_distributions"],
        "excerpts": [
            {
                "excerpt_label": "§732(a)(1)/(a)(2) — non-liquidating basis + limitation (verbatim)",
                "location_reference": "26 U.S.C. §732(a)",
                "excerpt_text": (
                    "(1) General rule. The basis of property (other than money) distributed by a "
                    "partnership to a partner other than in liquidation of the partner's interest "
                    "shall, except as provided in paragraph (2), be its adjusted basis to the "
                    "partnership immediately before such distribution. (2) Limitation. The basis to "
                    "the distributee partner of property to which paragraph (1) is applicable shall "
                    "not exceed the adjusted basis of such partner's interest in the partnership "
                    "reduced by any money distributed in the same transaction."
                ),
                "summary_text": (
                    "Non-liquidating: carryover basis, capped at outside basis minus money — the "
                    "form's line 9 / line 10 smaller-of mechanic."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§732(b) — liquidating distribution basis (verbatim)",
                "location_reference": "26 U.S.C. §732(b)",
                "excerpt_text": (
                    "The basis of property (other than money) distributed by a partnership to a "
                    "partner in liquidation of the partner's interest shall be an amount equal to "
                    "the adjusted basis of such partner's interest in the partnership reduced by any "
                    "money distributed in the same transaction."
                ),
                "summary_text": "Liquidating: substituted basis — line 10 = line 9 exactly, no smaller-of.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§732(c) — allocation of basis (verbatim, full waterfall)",
                "location_reference": "26 U.S.C. §732(c)(1)-(3)",
                "excerpt_text": (
                    "(1) In general. The basis of distributed properties to which subsection (a)(2) "
                    "or (b) is applicable shall be allocated— (A)(i) first to any unrealized "
                    "receivables (as defined in section 751(c)) and inventory items (as defined in "
                    "section 751(d)) in an amount equal to the adjusted basis of each such property "
                    "to the partnership, and (ii) if the basis to be allocated is less than the sum "
                    "of the adjusted bases of such properties to the partnership, then, to the "
                    "extent any decrease is required in order to have the adjusted bases of such "
                    "properties equal the basis to be allocated, in the manner provided in paragraph "
                    "(3), and (B) to the extent of any basis remaining after the allocation under "
                    "subparagraph (A), to other distributed properties— (i) first by assigning to "
                    "each such other property such other property's adjusted basis to the "
                    "partnership, and (ii) then, to the extent any increase or decrease in basis is "
                    "required in order to have the adjusted bases of such other distributed "
                    "properties equal such remaining basis, in the manner provided in paragraph (2) "
                    "or (3), whichever is appropriate. (2) Method of allocating increase. Any "
                    "increase required under paragraph (1)(B) shall be allocated among the "
                    "properties— (A) first to properties with unrealized appreciation in proportion "
                    "to their respective amounts of unrealized appreciation before such increase "
                    "(but only to the extent of each property's unrealized appreciation), and (B) "
                    "then, to the extent such increase is not allocated under subparagraph (A), in "
                    "proportion to their respective fair market values. (3) Method of allocating "
                    "decrease. Any decrease required under paragraph (1)(A) or (1)(B) shall be "
                    "allocated— (A) first to properties with unrealized depreciation in proportion "
                    "to their respective amounts of unrealized depreciation before such decrease "
                    "(but only to the extent of each property's unrealized depreciation), and (B) "
                    "then, to the extent such decrease is not allocated under subparagraph (A), in "
                    "proportion to their respective adjusted bases (as adjusted under subparagraph "
                    "(A))."
                ),
                "summary_text": (
                    "THE waterfall R-7217-ALLOC encodes: hot assets at basis first (decrease-only "
                    "tier), then other property at basis, then (c)(2) increase / (c)(3) decrease. "
                    "Note (c)(2) applies only to (1)(B) 'other' properties — tier-1 can never be "
                    "allocated above partnership basis, which is what creates the §731(a)(2) loss "
                    "edge on liquidating distributions (D_7217_006)."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "USC_26_731",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2024,
        "tax_year_end": 2026,
        "title": "26 U.S.C. §731 — Extent of recognition of gain or loss on distribution",
        "citation": "IRC §731(a)",
        "issuer": "US Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/731",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": True,
        "notes": (
            "Fetched 2026-07-02. Governs the form's line 7 (gain) and the D_7217_006 liquidating-"
            "loss edge. REQUIRES HUMAN REVIEW: Ken confirms J1 (gain → Schedule D RED defer, not a "
            "wired feed) and J2 (the §731(a)(2) loss defer)."
        ),
        "topics": ["pship_distributions"],
        "excerpts": [
            {
                "excerpt_label": "§731(a) — gain/loss recognition + character (verbatim)",
                "location_reference": "26 U.S.C. §731(a)",
                "excerpt_text": (
                    "In the case of a distribution by a partnership to a partner— (1) gain shall not "
                    "be recognized to such partner, except to the extent that any money distributed "
                    "exceeds the adjusted basis of such partner's interest in the partnership "
                    "immediately before the distribution, and (2) loss shall not be recognized to "
                    "such partner, except that upon a distribution in liquidation of a partner's "
                    "interest in a partnership where no property other than that described in "
                    "subparagraph (A) or (B) is distributed to such partner, loss shall be "
                    "recognized to the extent of the excess of the adjusted basis of such partner's "
                    "interest in the partnership over the sum of— (A) any money distributed, and "
                    "(B) the basis to the distributee, as determined under section 732, of any "
                    "unrealized receivables (as defined in section 751(c)) and inventory (as defined "
                    "in section 751(d)). Any gain or loss recognized under this subsection shall be "
                    "considered as gain or loss from the sale or exchange of the partnership "
                    "interest of the distributee partner."
                ),
                "summary_text": (
                    "Line 7 gain = money over outside basis (§731(a)(1)); the liquidating loss "
                    "arises only when nothing but money + hot assets is distributed (§731(a)(2)); "
                    "character = sale/exchange of the partnership interest (capital → Schedule D)."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2024_7217_INSTR",
        "source_type": "official_guidance",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2024,
        "tax_year_end": 2026,
        "title": "Instructions for Form 7217 (December 2024) — Partner's Report of Property Distributed by a Partnership",
        "citation": "i7217 (Rev. 12-2024), Catalog 94871V; + the IRS 2026-04-27 box-19-codes update (TY2025+)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i7217.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": (
            "Fetched 2026-07-02 (the current revision: 'Use the December 2024 version of Form 7217 "
            "for tax years beginning in 2024 or later, until a later revision is issued'). REQUIRES "
            "HUMAN REVIEW: Ken confirms J3 (the line-9 §737 literal reading), J5 (per-row hot/other "
            "preparer classification), and J6 (the securities 5b feeder + line-9 5a-only subtraction). "
            "The 2026-04-27 IRS update (new K-1 box 19 codes for TY2025+, instructions revision "
            "announced for December 2026) is excerpted verbatim below — it changes SOURCING notes "
            "(which K-1 codes feed lines 3/5a/5b), not the math."
        ),
        "topics": ["pship_distributions"],
        "excerpts": [
            {
                "excerpt_label": "Who must file / do NOT file (verbatim)",
                "location_reference": "i7217 (Rev. 12-2024), Who Must File",
                "excerpt_text": (
                    "File with your annual tax return a separate Form 7217 for each date during the "
                    "tax year that you received distributed property subject to section 732. If you "
                    "received distributed properties subject to section 732 on different days during "
                    "the tax year, even if part of the same transaction, file a separate Form 7217 "
                    "for each date that you received the properties. Do not file Form 7217 if the "
                    "distribution consisted only of money or marketable securities treated as money "
                    "under section 731(c). Also, do not file Form 7217 for payments to you for "
                    "services other than in your capacity as a partner under section 707(a)(1) or "
                    "for transfers that are treated as disguised sales under section 707(a)(2)(B)."
                ),
                "summary_text": (
                    "One form PER DATE (the tts model = one PartnershipDistribution row per date); "
                    "money-only / securities-only distributions never file (D_7217_003); §707 "
                    "payments and disguised sales are out (instruction notes, not adjudicated)."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Lines 3, 4, 5a — sourcing + exclusions (verbatim)",
                "location_reference": "i7217 (Rev. 12-2024), Lines 3/4/5a",
                "excerpt_text": (
                    "[Line 3] Enter the partnership's aggregate basis in the distributed property "
                    "(other than cash, but including marketable securities treated as money under "
                    "section 731(c)) immediately before the distribution, taking into account any "
                    "adjustments under sections 732(d), 734(b), or 743(b), as applicable. ... The "
                    "amount entered on line 3 should equal the total amount of Part II, line B, "
                    "column (b). [Line 4] Enter the adjusted basis of your interest in the "
                    "partnership (outside basis) immediately before the distribution. Do not include "
                    "any gain you recognized under section 737 as a result of the distribution ... "
                    "The basis of your interest in the partnership is not reported on the Schedule "
                    "K-1; you are responsible for calculating this amount. [Line 5a] Enter the "
                    "amount of money (other than marketable securities treated as money under "
                    "section 731(c)) you received or were deemed to receive in the distribution. "
                    "This amount includes deemed distributions of money under section 752(b)."
                ),
                "summary_text": (
                    "Line 3 EXCLUDES cash but INCLUDES §731(c) securities (they sit in Part II); "
                    "line 4 excludes §737 gain and is the partner's own computation (nullable input, "
                    "D_7217_004 when missing); line 5a includes §752(b) deemed money."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Lines 9, 10 — the allocable-basis mechanic (verbatim)",
                "location_reference": "i7217 (Rev. 12-2024), Lines 9/10",
                "excerpt_text": (
                    "[Line 9] Subtract line 5a from line 4. This is your outside basis reduced (but "
                    "not below zero) by money (including deemed distributions of money under section "
                    "752(b), but not including marketable securities treated as money under section "
                    "731(c)) you received or were deemed to receive in the distribution. Include any "
                    "gain you recognized under section 737 as a result of the distribution. [Line "
                    "10] For a non-liquidating distribution, enter the smaller of line 3 or line 9. "
                    "For a liquidating distribution, enter the amount from line 9. This is the "
                    "aggregate amount of basis to be allocated to the distributed property (other "
                    "than money). The amount entered on line 10 should equal the total amount of "
                    "Part II, line B, column (e)."
                ),
                "summary_text": (
                    "Line 9 subtracts 5a ONLY (never 5b securities), floors at zero, then ADDS §737 "
                    "gain (J3 literal reading); line 10 = min(3, 9) non-liquidating / 9 liquidating. "
                    "The B(e) tie breaks only in the §731(a)(2) loss edge (D_7217_006)."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Column (e) + the §731(c)(4) exclusion (verbatim)",
                "location_reference": "i7217 (Rev. 12-2024), Part II column (e)",
                "excerpt_text": (
                    "Enter your basis in each distributed property after the application of section "
                    "732. For a non-liquidating distribution where the section 732(a)(2) limitation "
                    "applies, enter your basis in each distributed property after the application of "
                    "sections 732(a)(2) and (c). For a liquidating distribution, enter your basis in "
                    "each distributed property after the application of sections 732(b) and (c). The "
                    "total amount (line B) in this column should equal the amount on Part I, line "
                    "10. Column (e) does not include any increase in the basis of distributed "
                    "marketable securities as a result of gain recognized under section 731(c)(4)."
                ),
                "summary_text": (
                    "Col (e) = the R-7217-ALLOC output. The §731(c)(4) securities step-up is "
                    "excluded from col (e) — the engine never computes it (stated boundary, J6)."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Example 1 — Jordan (non-liquidating §732(a)(2)) (verbatim)",
                "location_reference": "i7217 (Rev. 12-2024), Example 1",
                "excerpt_text": (
                    "Jordan is a partner of partnership Delta. Jordan has an outside basis of "
                    "$10,000. Jordan receives a non-liquidating distribution of cash of $4,000 and "
                    "property with an adjusted basis to the partnership of $8,000. Jordan's basis in "
                    "the distributed property is limited to $6,000 ($10,000, the adjusted basis of "
                    "Jordan's interest, reduced by $4,000, the cash distributed)."
                ),
                "summary_text": (
                    "Pinned EXACTLY by scenario 7217-T2. ATS Scenario 12 uses the same outside/cash "
                    "numbers (10,000 / 4,000 → 6,000) — 7217-T1."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Example 2 — Alex (liquidating, full §732(c) waterfall) (verbatim)",
                "location_reference": "i7217 (Rev. 12-2024), Example 2",
                "excerpt_text": (
                    "Alex is a one-fourth partner in partnership PRS and has an outside basis of "
                    "$750. PRS distributes inventory, asset X, asset Y, and $100 of cash to Alex in "
                    "liquidation of Alex's entire partnership interest. The partnership's basis in "
                    "the inventory is $100 and it has an FMV of $200. The partnership's basis in "
                    "asset X is $50, and it has an FMV of $400. The partnership's basis in asset Y "
                    "is $100 and it has an FMV of $100. ... The amount of basis to be allocated to "
                    "the distributed properties under section 732(c) is $650, Alex's outside basis "
                    "reduced by money distributed. The inventory is allocated its adjusted basis of "
                    "$100. The remaining basis, $550, is first allocated to the other distributed "
                    "properties in an amount equal to each property's adjusted basis to the "
                    "partnership. Asset X is allocated $50 and asset Y is allocated $100. The "
                    "remaining basis, $400, is allocated to other distributed properties in "
                    "proportion to, and to the extent of, unrealized appreciation. Asset X is then "
                    "allocated $350, the amount of unrealized appreciation in asset X. Finally, the "
                    "remaining basis, $50, is allocated to assets X and Y in proportion to their "
                    "FMVs: $40 to asset X (400/500 x $50), and $10 to asset Y (100/500 x $50). "
                    "Therefore, after the distribution, Alex has an adjusted basis of $100 in the "
                    "inventory, $440 in asset X, and $110 in asset Y."
                ),
                "summary_text": (
                    "The IRS's own worked waterfall — inventory 100 / X 440 / Y 110 from allocable "
                    "650. Pinned EXACTLY by scenario 7217-T3 (every (c)(1)(A)/(B), (c)(2)(A)/(B) "
                    "step)."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Box 19 codes update, TY2025+ (posted 2026-04-27, verbatim)",
                "location_reference": "IRS.gov 'Update to Instructions for Form 7217' (2026-04-27; December 2026 revision announced)",
                "excerpt_text": (
                    "For tax year 2025 and subsequent years, the data for reporting on certain lines "
                    "of Form 7217 come from new codes on box 19 of Schedule K-1 (Form 1065). ... "
                    "[Line 3] The partnership will report this information to you on your Schedule "
                    "K-1 (Form 1065), box 19, codes B, C, and G; or, if applicable, in a section "
                    "732(d) statement attached to your Schedule K-1 (Form 1065). For marketable "
                    "securities, amounts will be reported on the statement accompanying box 19, "
                    "codes A and F. [Line 5a] The partnership will report money distributed to you "
                    "on your Schedule K-1 (Form 1065), box 19, codes A, D, and F. In determining the "
                    "amount of money to report on line 5a, do not include any marketable securities "
                    "reported on your Schedule K-1 (Form 1065), box 19, codes A and F. [Line 5b] The "
                    "partnership will report this information to you on a statement attached to your "
                    "Schedule K-1 (Form 1065), box 19, codes A and F."
                ),
                "summary_text": (
                    "TY2025+ K-1 sourcing: line 3 ← box 19 B/C/G (+732(d) statement); line 5a ← "
                    "A/D/F excluding securities; line 5b ← the A/F statement. Changes SOURCING "
                    "hints (input labels + future K-1 import), not math. Caught at the spec leg via "
                    "the About-page Recent Developments check."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_K1P_INSTR",
        "source_type": "official_guidance",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "Partner's Instructions for Schedule K-1 (Form 1065) (2025) — box 19 Distributions",
        "citation": "2025 Partner's Instructions for Schedule K-1 (Form 1065), box 19",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i1065sk1.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": (
            "Fetched 2026-07-02 (the 2025 revision — carries OBBBA What's-New items). Governs WHERE "
            "the §731(a)(1) distribution-in-excess-of-basis gain lands on the partner's return: "
            "Form 8949 + Schedule D (the J1 wire's face authority). REQUIRES HUMAN REVIEW: Ken "
            "blessed the wire at the 2026-07-02 walk; the synthesized-row presentation (proceeds = "
            "line 5c, basis = line 6) is the encoded reading — the instructions name the forms, "
            "not the row layout."
        ),
        "topics": ["pship_distributions"],
        "excerpts": [
            {
                "excerpt_label": "Box 19 gain — reported on Form 8949 and Schedule D (verbatim)",
                "location_reference": "2025 Partner's Instructions for Schedule K-1 (Form 1065), box 19 (codes A/C), Gain",
                "excerpt_text": (
                    "Gain. To the extent the cash and the FMV of the securities (reduced by the "
                    "reduction amount) received exceed the adjusted basis of your partnership "
                    "interest immediately before the distribution, the excess is treated as gain "
                    "from the sale or exchange of your partnership interest. Generally, this gain "
                    "is treated as gain from the sale of a capital asset and should be reported on "
                    "Form 8949 and the Schedule D for your return. However, if you receive cash or "
                    "property in exchange for any part of a partnership interest, the amount of the "
                    "distribution attributable to your share of the partnership's unrealized "
                    "receivables or inventory items results in ordinary income."
                ),
                "summary_text": (
                    "The J1 wire's landing: Form 8949 + Schedule D, capital-asset character. The "
                    "'However' hot-asset ordinary-income arm is the §751 territory covered by the "
                    "D_7217_001 defer."
                ),
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Box 19 code B — §737 gain reporting (verbatim)",
                "location_reference": "2025 Partner's Instructions for Schedule K-1 (Form 1065), box 19 code B worksheet",
                "excerpt_text": (
                    "The type of gain (section 1231 gain, capital gain, etc.) generated is "
                    "determined by the type of gain you would have recognized if you sold the "
                    "property rather than contributing it to the partnership. However, to the "
                    "extent section 751(b) applies, the gain will be treated as ordinary income. "
                    "Accordingly, report the amount from line 7, above, on Form 4797 or Form 8949 "
                    "and the Schedule D of your tax return."
                ),
                "summary_text": (
                    "§737 gain's character follows the contributed property (4797 OR 8949/Sch D) — "
                    "exactly why J3 stays a preparer-routed RED defer rather than an auto-feed."
                ),
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2024_7217_FORM",
        "source_type": "official_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2024,
        "tax_year_end": 2026,
        "title": "Form 7217 (December 2024) — Partner's Report of Property Distributed by a Partnership",
        "citation": "Form 7217 (Rev. 12-2024), Cat. 94479B, Attachment Sequence No. 217",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f7217.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": False,
        "notes": (
            "Fetched 2026-07-02 from irs.gov (the posted current revision). Part II is a 30-row "
            "grid on the face with a line-A attached-totals row; the MeF IRS7217 XSD models Part II "
            "as an UNBOUNDED repeating group with no line-A element — the tts list model follows "
            "the XSD (rows unlimited; render overflows past 30 rows via the line-A convention at "
            "the render leg)."
        ),
        "topics": ["pship_distributions"],
        "excerpts": [
            {
                "excerpt_label": "Part I face — lines 1-10 (verbatim)",
                "location_reference": "Form 7217 (Rev. 12-2024), Part I",
                "excerpt_text": (
                    "1 Was this distribution in complete liquidation of the partner's interest in "
                    "the partnership? 2 Was any part of the distribution treated as a sale or "
                    "exchange under section 751(b)? 3 Partnership's aggregate basis in distributed "
                    "property (taking into account any basis adjustments under section 732(d), "
                    "734(b), or 743(b)) immediately before the distribution. This line should equal "
                    "the total of Part II, line B, column (b). 4 Adjusted basis of the partner's "
                    "interest in the partnership immediately before the distribution. 5a Cash "
                    "received in the distribution. b Fair market value of marketable securities (as "
                    "defined in section 731(c)) received in the distribution. c Add lines 5a and 5b. "
                    "6 Enter the smaller of line 4 or line 5c. 7 Gain recognized. Subtract line 6 "
                    "from line 5c. If zero, enter -0- and go to line 9. 8 Is U.S. tax required to be "
                    "paid on the gain entered on line 7? 9 Partner's basis in partnership interest "
                    "reduced by cash received in the distribution. Subtract line 5a from line 4. If "
                    "zero or less, enter -0-. See instructions if you recognized gain under section "
                    "737 as a result of the distribution. 10 Aggregate basis to be allocated to the "
                    "distributed property. For a non-liquidating distribution, enter the smaller of "
                    "line 3 or line 9. For a liquidating distribution, enter the amount from line 9. "
                    "Line 10 should equal the total of Part II, line B, column (e)."
                ),
                "summary_text": "The Part I arithmetic the engine reproduces line-for-line (R-7217-GAIN / R-7217-L9L10).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part I header — one form per distribution date (verbatim)",
                "location_reference": "Form 7217 (Rev. 12-2024), Part I heading",
                "excerpt_text": (
                    "Aggregate Basis of Distributed Property on Distribution Date. File a separate "
                    "form for each date a partner received distributed property."
                ),
                "summary_text": "The per-date model rule: one PartnershipDistribution row = one Form 7217.",
                "is_key_excerpt": True,
            },
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("USC_26_732", "FORM_7217", "governs"),
    ("USC_26_731", "FORM_7217", "governs"),
    ("IRS_2024_7217_INSTR", "FORM_7217", "governs"),
    ("IRS_2024_7217_FORM", "FORM_7217", "governs"),
    ("IRS_2025_K1P_INSTR", "FORM_7217", "governs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM: FORM_7217
# ═══════════════════════════════════════════════════════════════════════════

F7217_IDENTITY = {
    "form_number": "FORM_7217",
    "form_title": "Form 7217 — Partner's Report of Property Distributed by a Partnership (§732) (TY2025)",
    "notes": (
        "ATS Scenario 12's form (smallest-first, Ken 2026-07-02). One Form 7217 "
        "per DISTRIBUTION DATE (the tts model = a per-return PartnershipDistribution "
        "list row + DistributedProperty child rows — the InstallmentSale pattern, "
        "one level deeper). Part I is pure arithmetic over the distribution facts; "
        "Part II column (e) is the §732(c) allocation waterfall computed per "
        "property. §731(a)(1) gain (line 7) IS WIRED (Ken 2026-07-02): a "
        "synthesized no-1099-B Form 8949 row (box C/F, ST/LT per the holding-"
        "period assertion; proceeds = 5c, basis = 6) rides the existing 8949 → "
        "Schedule D machinery; an unasserted holding period WITHHOLDS the feed "
        "(D_7217_011 RED). §737 gain and the §731(a)(2) liquidating loss remain "
        "RED-deferred to manual entry (D_7217_009/006). Hot-asset classification "
        "(§751(c)/(d)) is a per-row preparer assertion; unanswered withholds the "
        "allocation (D_7217_008). §731(c) marketable-security rows auto-feed "
        "line 5b (YELLOW, override GREEN) and stay in Part II/line 3."
    ),
}

F7217_FACTS: list[dict] = [
    # ── Distribution-level inputs (one Form 7217 per distribution date) ──
    {"fact_key": "f7217_partnership_name", "label": "Header — distributing partnership's name",
     "data_type": "string", "sort_order": 1,
     "notes": "PER-DISTRIBUTION INPUT. MeF: BusinessNameType (IRS7217 DistributingPartnershipName)."},
    {"fact_key": "f7217_partnership_ein", "label": "Header — distributing partnership's EIN",
     "data_type": "string", "sort_order": 2,
     "notes": "PER-DISTRIBUTION INPUT. NN-NNNNNNN format (MeF EINType) — entry-level validation."},
    {"fact_key": "f7217_distribution_date", "label": "Header — date property was distributed to partner",
     "data_type": "date", "sort_order": 3,
     "notes": ("PER-DISTRIBUTION INPUT. One Form 7217 PER DATE (i7217 Who-Must-File verbatim). "
               "Year must equal the return tax year — D_7217_010.")},
    {"fact_key": "f7217_liquidating", "label": "Line 1 — distribution in complete liquidation of the partner's interest?",
     "data_type": "boolean", "sort_order": 4,
     "notes": ("PER-DISTRIBUTION PREPARER ASSERTION (nullable — the face requires Yes/No; unanswered "
               "-> D_7217_004). True -> §732(b) substituted basis (line 10 = line 9); False -> "
               "§732(a) carryover-with-cap (line 10 = min(3, 9)).")},
    {"fact_key": "f7217_sec751b", "label": "Line 2 — any part treated as a sale or exchange under §751(b)?",
     "data_type": "boolean", "sort_order": 5,
     "notes": ("PER-DISTRIBUTION PREPARER ASSERTION (nullable; unanswered -> D_7217_004). True -> "
               "D_7217_001 RED: attach the Reg §1.751-1(b)(5) statement + compute the §751(b) "
               "income/gain/loss manually (v1 boundary — recharacterization not modeled).")},
    {"fact_key": "f7217_outside_basis", "label": "Line 4 — adjusted basis of the partner's interest (outside basis) immediately before the distribution",
     "data_type": "decimal", "sort_order": 6,
     "notes": ("PER-DISTRIBUTION INPUT, nullable — 'you are responsible for calculating this amount' "
               "(i7217; NOT on the K-1). EXCLUDES §737 gain (i7217 line 4 verbatim). None -> "
               "D_7217_004 RED; 0 is a VALID entered value (fully depleted basis).")},
    {"fact_key": "f7217_cash_received", "label": "Line 5a — cash received in the distribution (incl. §752(b) deemed distributions)",
     "data_type": "decimal", "default_value": "0", "sort_order": 7,
     "notes": ("PER-DISTRIBUTION INPUT. Money OTHER THAN §731(c) marketable securities. TY2025+ K-1 "
               "sourcing: box 19 codes A, D, and F excluding securities (the 2026-04-27 update).")},
    {"fact_key": "f7217_securities_fmv_override", "label": "Line 5b override — FMV of §731(c) marketable securities received",
     "data_type": "decimal", "default_value": "0", "sort_order": 8,
     "notes": ("PER-DISTRIBUTION INPUT (GREEN override). Line 5b DEFAULTS to Σ FMV of property rows "
               "flagged is_marketable_security (YELLOW — the house feeder convention); a non-zero "
               "override wins. TY2025+ K-1 sourcing: the statement for box 19 codes A and F.")},
    {"fact_key": "f7217_gain_737", "label": "§737 gain recognized as a result of this distribution",
     "data_type": "decimal", "default_value": "0", "sort_order": 9,
     "notes": ("PER-DISTRIBUTION INPUT. EXCLUDED from line 4, INCLUDED in line 9 (i7217 verbatim, "
               "J3). K-1 box 19 code B reports §737 property. Presence -> D_7217_009 RED (the gain's "
               "own income reporting is manual v1).")},
    {"fact_key": "f7217_us_tax_on_gain", "label": "Line 8 — is U.S. tax required to be paid on the line-7 gain?",
     "data_type": "boolean", "sort_order": 10,
     "notes": ("PER-DISTRIBUTION PREPARER ASSERTION (nullable). Required only when line 7 > 0 — "
               "unanswered with a gain -> D_7217_007. (A No arises for e.g. treaty-exempt foreign "
               "partners — rare on a 1040.)")},
    {"fact_key": "f7217_interest_held_lt", "label": "Partnership interest held more than one year at the distribution date?",
     "data_type": "boolean", "sort_order": 11,
     "notes": ("PER-DISTRIBUTION PREPARER ASSERTION (nullable) — drives the ST/LT character of the "
               "line-7 §731(a)(1) gain feed (J1, Ken 2026-07-02). None with a gain -> D_7217_011 "
               "RED and the 8949 feed is WITHHELD (never silently default a character). Reg "
               "§1.1223-3 split holding periods out of scope (stated boundary). Irrelevant (and "
               "quiet) when line 7 = 0.")},
    # ── Property-level inputs (Part II — one row per distributed property) ──
    {"fact_key": "f7217_prop_description", "label": "Part II (a) — description of distributed property (+ Pub 946 App B code if applicable)",
     "data_type": "string", "sort_order": 20, "notes": "PER-PROPERTY INPUT."},
    {"fact_key": "f7217_prop_category", "label": "Part II — §751 classification: hot asset (unrealized receivable §751(c) / inventory item §751(d)) or other property",
     "data_type": "string", "sort_order": 21,
     "notes": ("PER-PROPERTY PREPARER ASSERTION (nullable; values 'hot' | 'other'). Drives the "
               "§732(c)(1)(A)-vs-(B) tier. Unanswered on any row -> D_7217_008 RED and the ENTIRE "
               "Part II allocation is withheld (all col (e) = 0) — never compute a wrong tier (J5). "
               "Security rows default 'other' at the input layer.")},
    {"fact_key": "f7217_prop_is_security", "label": "Part II — §731(c) marketable security?",
     "data_type": "boolean", "default_value": "false", "sort_order": 22,
     "notes": ("PER-PROPERTY INPUT. Security rows: FMV feeds the line-5b auto-total (YELLOW), the "
               "row stays in Part II/line 3 (i7217 line 3 verbatim), line 9 does NOT subtract them "
               "(5a only), and the §731(c)(4) step-up is never added to col (e) (J6).")},
    {"fact_key": "f7217_prop_pship_basis", "label": "Part II (b) — partnership's adjusted basis in the property immediately before the distribution",
     "data_type": "decimal", "default_value": "0", "sort_order": 23,
     "notes": ("PER-PROPERTY INPUT. Includes any §732(d)/734(b)/743(b) adjustments AS REPORTED "
               "(K-1 box 19 codes B/C/G statement or the §732(d) statement) — the software does not "
               "compute those adjustments (v1 boundary). Σ rows = line 3.")},
    {"fact_key": "f7217_prop_fmv", "label": "Part II (d) — FMV of distributed property",
     "data_type": "decimal", "default_value": "0", "sort_order": 24,
     "notes": "PER-PROPERTY INPUT (K-1 box 19 statement). Drives the (c)(2)/(c)(3) proportioning."},
    {"fact_key": "f7217_adj_732d", "label": "Part II (c)(i) — col (b) includes a §732(d) special basis adjustment",
     "data_type": "boolean", "default_value": "false", "sort_order": 25,
     "notes": "PER-PROPERTY INDICATOR (informational checkbox; no compute effect)."},
    {"fact_key": "f7217_adj_732f", "label": "Part II (c)(ii) — distributed property is §732(f) stock",
     "data_type": "boolean", "default_value": "false", "sort_order": 26,
     "notes": ("PER-PROPERTY INDICATOR. §732(f) applies to CORPORATE partners (80% control of a "
               "distributed corporation's stock) — near-impossible on a 1040; indicator only.")},
    {"fact_key": "f7217_adj_734b", "label": "Part II (c)(iii) — col (b) includes a §734(b) basis adjustment",
     "data_type": "boolean", "default_value": "false", "sort_order": 27,
     "notes": "PER-PROPERTY INDICATOR (informational checkbox; no compute effect)."},
    {"fact_key": "f7217_adj_743b", "label": "Part II (c)(iv) — col (b) includes a §743(b) basis adjustment",
     "data_type": "boolean", "default_value": "false", "sort_order": 28,
     "notes": "PER-PROPERTY INDICATOR ('checked only if YOU have a §743(b) adjustment' — i7217)."},
    # ── Outputs ──
    {"fact_key": "f7217_line3", "label": "Line 3 — partnership's aggregate basis in distributed property (Σ Part II col (b))",
     "data_type": "decimal", "sort_order": 40,
     "notes": "OUTPUT. Excludes cash by construction (cash is line 5a, never a Part II row); includes security rows."},
    {"fact_key": "f7217_line5b", "label": "Line 5b — FMV of §731(c) marketable securities (resolved: auto-total or override)",
     "data_type": "decimal", "sort_order": 41,
     "notes": "OUTPUT. Σ security-row FMVs (YELLOW) unless the override fact is non-zero (GREEN)."},
    {"fact_key": "f7217_line5c", "label": "Line 5c — add lines 5a and 5b",
     "data_type": "decimal", "sort_order": 42, "notes": "OUTPUT."},
    {"fact_key": "f7217_line6", "label": "Line 6 — smaller of line 4 or line 5c",
     "data_type": "decimal", "sort_order": 43, "notes": "OUTPUT."},
    {"fact_key": "f7217_line7", "label": "Line 7 — gain recognized (§731(a)(1))",
     "data_type": "decimal", "sort_order": 44,
     "notes": ("OUTPUT. line 5c − line 6 (≥ 0 by construction). > 0 -> D_7217_002 RED: capital gain "
               "from the sale/exchange of the partnership interest — Schedule D MANUAL entry v1 (J1).")},
    {"fact_key": "f7217_line9", "label": "Line 9 — outside basis reduced by cash (floor 0) + §737 gain",
     "data_type": "decimal", "sort_order": 45,
     "notes": "OUTPUT. max(0, line 4 − line 5a) + §737 gain (J3 literal reading; 5b NEVER subtracted)."},
    {"fact_key": "f7217_line10", "label": "Line 10 — aggregate basis to be allocated to the distributed property",
     "data_type": "decimal", "sort_order": 46,
     "notes": "OUTPUT. Non-liquidating: min(line 3, line 9). Liquidating: line 9. = Σ col (e) except the D_7217_006 loss edge."},
    {"fact_key": "f7217_prop_basis_after", "label": "Part II (e) — partner's basis in the property after §732 (per row)",
     "data_type": "decimal", "sort_order": 47,
     "notes": ("OUTPUT per property — the R-7217-ALLOC §732(c) waterfall result (rounded per J4). "
               "Excludes any §731(c)(4) step-up (i7217 col (e) verbatim).")},
    {"fact_key": "f7217_8949_st", "label": "Short-term §731(a)(1) gain fed to Form 8949 Part I (box C)",
     "data_type": "decimal", "sort_order": 48,
     "notes": ("OUTPUT (J1 wire). = line 7 when interest_held_lt is False; the synthesized 8949 row "
               "carries proceeds = line 5c, basis = line 6. 0 when no gain or the assertion is "
               "unanswered (withheld, D_7217_011).")},
    {"fact_key": "f7217_8949_lt", "label": "Long-term §731(a)(1) gain fed to Form 8949 Part II (box F)",
     "data_type": "decimal", "sort_order": 49,
     "notes": ("OUTPUT (J1 wire). = line 7 when interest_held_lt is True; proceeds = line 5c, basis "
               "= line 6. 0 when no gain or the assertion is unanswered (withheld, D_7217_011).")},
    {"fact_key": "f7217_loss_731a2", "label": "§731(a)(2) loss recognized on liquidating distribution (detected)",
     "data_type": "decimal", "sort_order": 50,
     "notes": ("OUTPUT. = line 10 − Σ col (e) when positive on a liquidating distribution (only "
               "arises when nothing but money + hot assets was distributed) -> D_7217_006 RED: "
               "capital loss — Schedule D MANUAL entry v1 (J2). NOT a form-face line.")},
]

F7217_RULES: list[dict] = [
    {"rule_id": "R-7217-FILE",
     "title": "Filing gates: one form per distribution date; money-only never files; §751(b) and claim-year screens",
     "rule_type": "routing", "precedence": 1, "sort_order": 1,
     "formula": (
         "One Form 7217 per (partnership, distribution_date) — 'file a separate Form 7217 for each "
         "date' (i7217 verbatim). A distribution with NO property rows, or whose only rows are "
         "§731(c) marketable securities, is a money-only distribution -> the form is NOT FILED "
         "(D_7217_003 error: remove it; i7217 'Do not file ... if the distribution consisted only "
         "of money or marketable securities treated as money under section 731(c)'). sec751b is "
         "True -> D_7217_001 RED (attach the Reg 1.751-1(b)(5) statement; recharacterization "
         "manual). distribution_date.year != tax_year -> D_7217_010. outside_basis is None OR "
         "liquidating is None OR sec751b is None -> D_7217_004 (required entries)."),
     "inputs": ["f7217_distribution_date", "f7217_liquidating", "f7217_sec751b", "f7217_outside_basis"],
     "outputs": [],
     "description": ("The who-must-file screens. §707(a)(1) service payments and §707(a)(2)(B) "
                     "disguised sales are excluded by instruction note only (not adjudicated — "
                     "stated v1 boundary).")},
    {"rule_id": "R-7217-GAIN",
     "title": "Lines 5a-8 — money + securities vs outside basis; §731(a)(1) gain -> Form 8949/Schedule D",
     "rule_type": "calculation", "precedence": 2, "sort_order": 2,
     "formula": (
         "line_5b = Σ FMV of property rows with is_security=True (YELLOW) unless "
         "securities_fmv_override > 0 (GREEN override wins). line_5c = line_5a + line_5b. "
         "line_6 = min(line_4, line_5c). line_7 = line_5c − line_6 (≥ 0 by construction — "
         "§731(a)(1): gain only to the extent money (incl. §731(c) securities) exceeds outside "
         "basis). GAIN FEED (J1, Ken 2026-07-02): line_7 > 0 AND interest_held_lt asserted -> a "
         "synthesized no-1099-B Form 8949 row (Part I box C when False / Part II box F when True; "
         "description names the partnership + '§731(a)(1) distribution in excess of basis'; "
         "proceeds = line_5c, basis = line_6, gain = line_7) riding the EXISTING 8949 -> Schedule "
         "D machinery (8949_st or 8949_lt output; K-1 instructions box 19 verbatim: 'reported on "
         "Form 8949 and the Schedule D'). line_7 > 0 with interest_held_lt None -> the feed is "
         "WITHHELD + D_7217_011 RED (no silent character). Feed made -> D_7217_002 info "
         "(transparency). line 8 must be answered when line_7 > 0 (None -> D_7217_007). The "
         "§731(c)(4) securities basis step-up that accompanies such gain is NOT computed (col (e) "
         "excludes it — i7217; the partner's outside record)."),
     "inputs": ["f7217_cash_received", "f7217_securities_fmv_override", "f7217_outside_basis",
                "f7217_prop_is_security", "f7217_prop_fmv", "f7217_us_tax_on_gain",
                "f7217_interest_held_lt"],
     "outputs": ["f7217_line5b", "f7217_line5c", "f7217_line6", "f7217_line7",
                 "f7217_8949_st", "f7217_8949_lt"],
     "description": ("Face arithmetic + the WIRED gain feed (Ken chose wire-now over the defer at "
                     "the 2026-07-02 review walk). Compute ordering: 7217 runs BEFORE the 8949/"
                     "Schedule D netting so the synthesized row joins the same pass.")},
    {"rule_id": "R-7217-L9L10",
     "title": "Lines 3, 9, 10 — the allocable-basis mechanic (§732(a)(2)/(b))",
     "rule_type": "calculation", "precedence": 3, "sort_order": 3,
     "formula": (
         "line_3 = Σ col (b) over ALL property rows (cash never a row; securities INCLUDED — i7217 "
         "line 3 verbatim). line_9 = max(0, line_4 − line_5a) + gain_737 (the floor applies BEFORE "
         "the §737 add — J3 literal reading; line 5b NEVER subtracted here). gain_737 > 0 -> "
         "D_7217_009 RED (its income reporting is manual v1). line_10 = line_9 if liquidating "
         "(§732(b) substituted basis) else min(line_3, line_9) (§732(a)(1) carryover capped by "
         "(a)(2)). Adjustment engaged (line_10 != line_3 with rows present) -> D_7217_005 info "
         "(transparency: the §732(a)(2)/(b) + (c) adjustment applied)."),
     "inputs": ["f7217_prop_pship_basis", "f7217_outside_basis", "f7217_cash_received",
                "f7217_gain_737", "f7217_liquidating"],
     "outputs": ["f7217_line3", "f7217_line9", "f7217_line10"],
     "description": "Line 10 is the §732(c) engine's input; equals Part II B(e) except the J2 loss edge."},
    {"rule_id": "R-7217-ALLOC",
     "title": "Part II column (e) — the §732(c) allocation waterfall",
     "rule_type": "calculation", "precedence": 4, "sort_order": 4,
     "formula": (
         "GATE: any property row with category None -> allocation WITHHELD (every col (e) = 0) + "
         "D_7217_008 RED (J5). Otherwise, with allocable = line_10: TIER 1 (§732(c)(1)(A)) — each "
         "'hot' row (unrealized receivable §751(c) / inventory item §751(d)) is assigned its col-(b) "
         "basis; if allocable < Σ hot bases, allocate the DECREASE among hot rows per (c)(3) [(A) "
         "first to rows with unrealized depreciation (fmv < basis) in proportion to their "
         "depreciation, capped at each row's depreciation; (B) then in proportion to their adjusted "
         "bases as adjusted under (A)] and every 'other' row gets 0. TIER 2 (§732(c)(1)(B)) — "
         "remaining = allocable − Σ hot bases; each 'other' row is assigned its col-(b) basis; if "
         "remaining > Σ other bases, allocate the INCREASE per (c)(2) [(A) first to rows with "
         "unrealized appreciation (fmv > basis) in proportion to their appreciation, capped at each "
         "row's appreciation; (B) then in proportion to their FMVs]; if remaining < Σ other bases, "
         "allocate the DECREASE per (c)(3) as above. ROUNDING (J4): waterfall in exact decimals; "
         "each col (e) rounds half-up to whole dollars; any residue (Σ rounded − line_10) lands on "
         "the row with the largest allocated amount (ties: first row) so Σ col (e) == line_10 "
         "whenever the law allows equality."),
     "inputs": ["f7217_prop_category", "f7217_prop_pship_basis", "f7217_prop_fmv"],
     "outputs": ["f7217_prop_basis_after"],
     "description": ("The heart of the form. Increases can only reach tier-2 'other' rows — §732(c)(2) "
                     "references (1)(B) only; a hot row is never allocated above partnership basis. "
                     "Pinned by the IRS's own Example 2 numbers (7217-T3) plus every branch scenario.")},
    {"rule_id": "R-7217-LOSS",
     "title": "§731(a)(2) liquidating-loss detection (the one lawful line-10 ≠ B(e) case)",
     "rule_type": "routing", "precedence": 5, "sort_order": 5,
     "formula": (
         "loss_731a2 = max(0, line_10 − Σ col (e)) on a LIQUIDATING distribution. It can be positive "
         "only when every distributed property is a hot asset (tier-1 caps at partnership basis and "
         "§732(c)(2) has no tier-1 increase arm) — exactly §731(a)(2)'s condition ('no property "
         "other than [money, unrealized receivables, inventory] is distributed'). loss_731a2 > 0 -> "
         "D_7217_006 RED: capital loss (sale/exchange character, §731(a) flush language) — Schedule "
         "D MANUAL entry v1 (J2). Non-liquidating distributions: Σ col (e) == line_10 always (no "
         "loss recognition — §731(a)(2) is liquidating-only)."),
     "inputs": ["f7217_liquidating", "f7217_prop_category"],
     "outputs": ["f7217_loss_731a2"],
     "description": ("The form face's 'Line 10 should equal the total of Part II, line B, column (e)' "
                     "breaks BY LAW here; the instructions are silent on it. Encoded as detection + "
                     "RED, never a silent mismatch.")},
]

F7217_LINES: list[dict] = [
    # ── Part I face ──
    {"line_number": "1", "description": "1 Distribution in complete liquidation of the partner's interest? (Yes/No)", "line_type": "input"},
    {"line_number": "2", "description": "2 Any part treated as a sale or exchange under section 751(b)? (Yes/No; Yes -> D_7217_001 RED)", "line_type": "input"},
    {"line_number": "3", "description": "3 Partnership's aggregate basis in distributed property (= Part II line B col (b); incl. 732(d)/734(b)/743(b) adjustments)", "line_type": "calculated"},
    {"line_number": "4", "description": "4 Adjusted basis of the partner's interest (outside basis) immediately before the distribution (partner-computed input)", "line_type": "input"},
    {"line_number": "5a", "description": "5a Cash received in the distribution (incl. §752(b) deemed distributions)", "line_type": "input"},
    {"line_number": "5b", "description": "5b FMV of marketable securities (§731(c)) received (auto Σ security rows, override direct-entry)", "line_type": "calculated"},
    {"line_number": "5c", "description": "5c Add lines 5a and 5b", "line_type": "subtotal"},
    {"line_number": "6", "description": "6 Smaller of line 4 or line 5c", "line_type": "calculated"},
    {"line_number": "7", "description": "7 Gain recognized (§731(a)(1)). Line 5c − line 6; if zero enter -0- (gain > 0 -> D_7217_002 RED, Schedule D manual v1)", "line_type": "calculated"},
    {"line_number": "8", "description": "8 Is U.S. tax required to be paid on the line-7 gain? (Yes/No; required when line 7 > 0)", "line_type": "input"},
    {"line_number": "9", "description": "9 Line 4 − line 5a, not below zero; include §737 gain (i7217)", "line_type": "calculated"},
    {"line_number": "10", "description": "10 Aggregate basis to allocate: non-liquidating min(line 3, line 9); liquidating line 9 (= Part II line B col (e))", "line_type": "total"},
    # ── Part II grid columns (one DistributedProperty row each) ──
    {"line_number": "II-a", "description": "Part II col (a) Description of distributed property (+ Pub 946 App B code if applicable)", "line_type": "input"},
    {"line_number": "II-b", "description": "Part II col (b) Partnership's basis in the property immediately before the distribution (incl. adjustments as reported)", "line_type": "input"},
    {"line_number": "II-c-i", "description": "Part II col (c)(i) 732(d) special basis adjustment included? (indicator)", "line_type": "input"},
    {"line_number": "II-c-ii", "description": "Part II col (c)(ii) section 732(f) stock? (indicator; corporate partners)", "line_type": "input"},
    {"line_number": "II-c-iii", "description": "Part II col (c)(iii) 734(b) basis adjustment included? (indicator)", "line_type": "input"},
    {"line_number": "II-c-iv", "description": "Part II col (c)(iv) 743(b) basis adjustment included? (indicator)", "line_type": "input"},
    {"line_number": "II-d", "description": "Part II col (d) FMV of distributed property", "line_type": "input"},
    {"line_number": "II-e", "description": "Part II col (e) Partner's basis after §732 (COMPUTED — the §732(c) waterfall; excludes any §731(c)(4) step-up)", "line_type": "calculated"},
    # ── Part II totals row ──
    {"line_number": "II-B-b", "description": "Part II line B total col (b) — equals Part I line 3", "line_type": "total"},
    {"line_number": "II-B-d", "description": "Part II line B total col (d) — total FMV of distributed property", "line_type": "total"},
    {"line_number": "II-B-e", "description": "Part II line B total col (e) — equals Part I line 10 (except the D_7217_006 §731(a)(2) loss edge)", "line_type": "total"},
]

F7217_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_7217_001", "title": "§751(b) sale-or-exchange part — statement + recharacterization not supported", "severity": "error",
     "condition": "line 2 (sec751b) is answered Yes on a distribution",
     "message": ("Not supported — prepare manually: part of this distribution is treated as a sale or "
                 "exchange under section 751(b) (hot assets exchanged for other property or vice "
                 "versa). Attach a statement showing the §751(b) income/gain/loss computation (Reg. "
                 "§1.751-1(b)(5)) and report the recharacterized amounts manually — the software "
                 "computes the Form 7217 face but does not model the §751(b) recharacterization."),
     "notes": "v1 RED-defer. The face arithmetic still renders (the form is still filed with the statement)."},
    {"diagnostic_id": "D_7217_002", "title": "§731(a)(1) gain auto-reported on Form 8949 / Schedule D", "severity": "info",
     "condition": "line 7 > 0 and the holding-period assertion is answered (the feed was made)",
     "message": ("Gain of the line-7 amount is recognized under §731(a)(1) (money distributed "
                 "exceeds outside basis) and has been reported automatically on Form 8949 (no-1099-B "
                 "box C/F) and Schedule D as short/long-term capital gain per the holding-period "
                 "answer — gain from the sale or exchange of the partnership interest (K-1 box 19 "
                 "instructions). Note: any §731(c)(4) marketable-security basis step-up is the "
                 "partner's outside record — it is not tracked here."),
     "notes": "J1 WIRED (Ken 2026-07-02). Transparency info, mirrors D_1116_001's auto-applied role."},
    {"diagnostic_id": "D_7217_011", "title": "Gain recognized but holding period unasserted — 8949 feed withheld", "severity": "error",
     "condition": "line 7 > 0 and the interest-held-more-than-one-year question is unanswered",
     "message": ("Gain is recognized on this distribution under §731(a)(1), but the holding period "
                 "of the partnership interest is not asserted — answer whether the interest was "
                 "held more than one year at the distribution date. Until answered, the gain is "
                 "NOT reported on Form 8949/Schedule D (the software never defaults a capital-gain "
                 "character). Split holding periods (Reg §1.1223-3) are not modeled — use the "
                 "predominant character or prepare the 8949 rows manually."),
     "notes": "The no-silent-character gate on the J1 wire (the 8911 census-tract assertion pattern)."},
    {"diagnostic_id": "D_7217_003", "title": "Money-only distribution — Form 7217 is not filed", "severity": "error",
     "condition": "a distribution has no property rows, or every property row is a §731(c) marketable security",
     "message": ("Form 7217 is not filed for a distribution consisting only of money or marketable "
                 "securities treated as money under section 731(c) (i7217, Who Must File). Remove "
                 "this Form 7217 entry — or add the distributed property rows if property other "
                 "than money was in fact received. (Any §731(a)(1) gain on a money-only "
                 "distribution is still reported on Schedule D manually.)"),
     "notes": "The don't-file screen. Securities-only = money-only per the verbatim rule."},
    {"diagnostic_id": "D_7217_004", "title": "Required Form 7217 entries missing", "severity": "error",
     "condition": "outside basis (line 4) is blank, or the line-1 / line-2 Yes-No questions are unanswered",
     "message": ("Form 7217 requires the partner's outside basis (line 4 — you are responsible for "
                 "calculating it; it is not on the Schedule K-1) and answers to line 1 (complete "
                 "liquidation?) and line 2 (§751(b)?). Complete the missing entries — the basis "
                 "allocation cannot be computed without them."),
     "notes": "Nullable-fact gate. An entered 0 outside basis is valid (fully depleted) and does not fire."},
    {"diagnostic_id": "D_7217_005", "title": "§732 basis adjustment applied to distributed property", "severity": "info",
     "condition": "line 10 differs from line 3 (property rows present)",
     "message": ("The basis of the distributed property in the partner's hands differs from the "
                 "partnership's basis: the §732(a)(2) limitation (non-liquidating) or §732(b) "
                 "substituted basis (liquidating) applied, and Part II column (e) reflects the "
                 "§732(c) allocation. Review the per-property results — depreciation schedules and "
                 "future dispositions use the column (e) basis."),
     "notes": "Transparency, mirrors D_8911_003's role. Fires on T1/T2/T3 etc.; quiet on the pass-through case."},
    {"diagnostic_id": "D_7217_006", "title": "Loss recognized on liquidating distribution (§731(a)(2)) — Schedule D entry is manual", "severity": "error",
     "condition": "liquidating distribution and line 10 exceeds the Part II column (e) total (only money + hot assets distributed)",
     "message": ("Not supported — prepare manually: this liquidating distribution consisted only of "
                 "money and unrealized receivables/inventory, and the allocable basis (line 10) "
                 "exceeds the §732(c) basis assigned to those assets — the excess is a recognized "
                 "LOSS under §731(a)(2) (capital, sale-or-exchange character). Enter the loss on "
                 "Schedule D manually. Note: in this one case the form face's rule that line 10 "
                 "equal Part II line B column (e) cannot hold; the instructions do not address it."),
     "notes": "J2 defer (Ken review). The one lawful line-10/B(e) divergence — detected, never silent."},
    {"diagnostic_id": "D_7217_007", "title": "Line 8 unanswered while gain is recognized", "severity": "error",
     "condition": "line 7 > 0 and the line-8 U.S.-tax question is unanswered",
     "message": ("Line 7 shows recognized gain, so line 8 (is U.S. tax required to be paid on the "
                 "gain?) must be answered Yes or No on the form face. For a U.S.-person partner the "
                 "answer is generally Yes."),
     "notes": "Preparer-assertion completeness gate; quiet when line 7 = 0 (the face skips to line 9)."},
    {"diagnostic_id": "D_7217_008", "title": "Distributed property not classified (§751 hot asset vs other) — allocation withheld", "severity": "error",
     "condition": "any property row's hot-asset/other classification is unanswered",
     "message": ("Each distributed property must be classified as a §751(c) unrealized receivable / "
                 "§751(d) inventory item ('hot asset') or as other property — the §732(c) allocation "
                 "order depends on it (hot assets absorb basis first, capped at the partnership's "
                 "basis). Until every property on this distribution is classified, Part II column "
                 "(e) is not computed (shown as 0) — classify each row from the Schedule K-1 box 19 "
                 "statement."),
     "notes": "J5 (Ken review): withhold-all beats computing a wrong tier. The 8911 census-tract assertion pattern."},
    {"diagnostic_id": "D_7217_009", "title": "§737 gain — income reporting is manual", "severity": "error",
     "condition": "a §737 gain amount is entered on the distribution",
     "message": ("Not supported — prepare manually: §737 gain (precontribution-gain property "
                 "distributed to the contributing partner within 7 years) is included in the line-9 "
                 "basis computation per the instructions, but its own income reporting (character "
                 "follows the §704(c) property) is not modeled — report the §737 gain on the return "
                 "manually (Schedule D / Form 4797 as applicable)."),
     "notes": "J3 defer. The line-9 ADD is computed (i7217 verbatim); only the income-side flow is manual."},
    {"diagnostic_id": "D_7217_010", "title": "Distribution date outside the return's tax year", "severity": "error",
     "condition": "a distribution's date falls outside the return tax year",
     "message": ("This Form 7217 distribution is dated outside the return's tax year. The form is "
                 "filed with the return FOR the tax year in which the property was received (i7217, "
                 "When To File) — move it to the correct year's return or fix the date."),
     "notes": "The claim-year trap (mirrors D_8911_006)."},
]

F7217_SCENARIOS: list[dict] = [
    {"scenario_name": "7217-T1 — ATS Scenario 12 (Gardenia) under enacted law", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"tax_year": 2025, "liquidating": False, "sec751b": False,
                "outside_basis": 10000, "cash_received": 4000, "gain_737": 0,
                "distribution_date": "2025-03-01",
                "properties": [{"description": "DISTRIBUTED PROPERTY", "category": "other",
                                "pship_basis": 32507, "fmv": 4000}]},
     "expected_outputs": {"f7217_line3": 32507, "f7217_line5b": 0, "f7217_line5c": 4000,
                          "f7217_line6": 4000, "f7217_line7": 0, "f7217_line9": 6000,
                          "f7217_line10": 6000, "col_e": [6000], "D_7217_005": True},
     "notes": ("HAND-COMPUTED from the ATS-12 scenario PDF facts. min(32,507, 10,000−4,000) = 6,000 "
               "to the single property; §732(c)(3)(A) absorbs the 26,507 decrease inside its 28,507 "
               "unrealized depreciation. ⚠️ The IRS answer key's own Part II shows col (e) total "
               "4,000 — contradicting ITS OWN line 10 of 6,000 — and labels the property 'CASH' "
               "(line 3 excludes cash by its verbatim text). The engine follows §732(a)(2)+(c); "
               "same outside/cash numbers as i7217 Example 1 -> 6,000. ATS acceptance is schema + "
               "business rules, not answer-key match ([[ats-answer-keys-pre-obbba-stale]]).")},
    {"scenario_name": "7217-T2 — i7217 Example 1 (Jordan) pinned exactly", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"tax_year": 2025, "liquidating": False, "sec751b": False,
                "outside_basis": 10000, "cash_received": 4000, "gain_737": 0,
                "distribution_date": "2025-06-01",
                "properties": [{"description": "PROPERTY", "category": "other",
                                "pship_basis": 8000, "fmv": 8000}]},
     "expected_outputs": {"f7217_line3": 8000, "f7217_line5c": 4000, "f7217_line6": 4000,
                          "f7217_line7": 0, "f7217_line9": 6000, "f7217_line10": 6000,
                          "col_e": [6000], "D_7217_005": True},
     "notes": ("THE INSTRUCTIONS' OWN Example 1, verbatim inputs -> the IRS's stated answer $6,000. "
               "Decrease 2,000 lands via (c)(3)(B) (no unrealized depreciation: fmv == basis).")},
    {"scenario_name": "7217-T3 — i7217 Example 2 (Alex, liquidating waterfall) pinned exactly", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"tax_year": 2025, "liquidating": True, "sec751b": False,
                "outside_basis": 750, "cash_received": 100, "gain_737": 0,
                "distribution_date": "2025-09-15",
                "properties": [{"description": "INVENTORY", "category": "hot", "pship_basis": 100, "fmv": 200},
                               {"description": "ASSET X", "category": "other", "pship_basis": 50, "fmv": 400},
                               {"description": "ASSET Y", "category": "other", "pship_basis": 100, "fmv": 100}]},
     "expected_outputs": {"f7217_line3": 250, "f7217_line5c": 100, "f7217_line6": 100,
                          "f7217_line7": 0, "f7217_line9": 650, "f7217_line10": 650,
                          "col_e": [100, 440, 110], "D_7217_005": True, "D_7217_006": False},
     "notes": ("THE INSTRUCTIONS' OWN Example 2 — the IRS's worked waterfall answer 100/440/110. "
               "Pins every step: tier-1 inventory at basis (100); tier-2 bases (50/100); (c)(2)(A) "
               "increase 400 all to X (its appreciation 350 caps... X gets 350, its full "
               "appreciation); (c)(2)(B) remaining 50 by FMV 400:100 -> +40/+10. No loss (other "
               "property present).")},
    {"scenario_name": "7217-T4 — §732(a)(1) pass-through (no limitation, mixed tiers)", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"tax_year": 2025, "liquidating": False, "sec751b": False,
                "outside_basis": 50000, "cash_received": 0, "gain_737": 0,
                "distribution_date": "2025-05-01",
                "properties": [{"description": "EQUIPMENT", "category": "other", "pship_basis": 8000, "fmv": 12000},
                               {"description": "INVENTORY", "category": "hot", "pship_basis": 2000, "fmv": 2000}]},
     "expected_outputs": {"f7217_line3": 10000, "f7217_line5c": 0, "f7217_line6": 0,
                          "f7217_line7": 0, "f7217_line9": 50000, "f7217_line10": 10000,
                          "col_e": [8000, 2000], "D_7217_005": False},
     "notes": ("HAND-COMPUTED. Ample outside basis: line 10 = min(10,000, 50,000) = 10,000 = line 3 "
               "-> every property keeps carryover basis (§732(a)(1)); no adjustment, D_005 quiet.")},
    {"scenario_name": "7217-T5 — (c)(3)(A)-then-(B) decrease with rounding residue", "scenario_type": "edge_case", "sort_order": 5,
     "inputs": {"tax_year": 2025, "liquidating": False, "sec751b": False,
                "outside_basis": 10000, "cash_received": 0, "gain_737": 0,
                "distribution_date": "2025-04-01",
                "properties": [{"description": "P1 (DEPRECIATED)", "category": "other", "pship_basis": 12000, "fmv": 4000},
                               {"description": "P2", "category": "other", "pship_basis": 8000, "fmv": 8000}]},
     "expected_outputs": {"f7217_line3": 20000, "f7217_line10": 10000,
                          "col_e": [3333, 6667], "D_7217_005": True},
     "notes": ("HAND-COMPUTED. Decrease 10,000: (3)(A) P1's unrealized depreciation 8,000 first -> "
               "P1 4,000 / P2 8,000; remaining 2,000 ∝ adjusted bases 4,000:8,000 -> P1 −666.67 = "
               "3,333.33, P2 −1,333.33 = 6,666.67; half-up rounding -> 3,333 + 6,667 = 10,000 (J4; "
               "residue rule not needed here — sums exactly).")},
    {"scenario_name": "7217-T6 — tier ordering: hot at basis first, decrease confined to tier 2", "scenario_type": "normal", "sort_order": 6,
     "inputs": {"tax_year": 2025, "liquidating": False, "sec751b": False,
                "outside_basis": 5000, "cash_received": 1000, "gain_737": 0,
                "distribution_date": "2025-07-15",
                "properties": [{"description": "INVENTORY", "category": "hot", "pship_basis": 3000, "fmv": 3500},
                               {"description": "EQUIPMENT", "category": "other", "pship_basis": 4000, "fmv": 3000}]},
     "expected_outputs": {"f7217_line3": 7000, "f7217_line5c": 1000, "f7217_line6": 1000,
                          "f7217_line7": 0, "f7217_line9": 4000, "f7217_line10": 4000,
                          "col_e": [3000, 1000], "D_7217_005": True},
     "notes": ("HAND-COMPUTED. Allocable 4,000: inventory takes its full 3,000 basis (§732(c)(1)(A) "
               "— allocable covers tier 1); equipment gets remaining 1,000 (decrease 3,000: (3)(A) "
               "its depreciation 1,000 first, (3)(B) the rest 2,000 — single row absorbs all).")},
    {"scenario_name": "7217-T7 — tier-1 decrease ((c)(1)(A)(ii)): hot bases exceed allocable, other rows zeroed", "scenario_type": "edge_case", "sort_order": 7,
     "inputs": {"tax_year": 2025, "liquidating": False, "sec751b": False,
                "outside_basis": 2500, "cash_received": 500, "gain_737": 0,
                "distribution_date": "2025-08-01",
                "properties": [{"description": "RECEIVABLES A", "category": "hot", "pship_basis": 1500, "fmv": 900},
                               {"description": "INVENTORY B", "category": "hot", "pship_basis": 1500, "fmv": 1500},
                               {"description": "EQUIPMENT C", "category": "other", "pship_basis": 1000, "fmv": 1000}]},
     "expected_outputs": {"f7217_line3": 4000, "f7217_line9": 2000, "f7217_line10": 2000,
                          "col_e": [750, 1250, 0], "D_7217_005": True},
     "notes": ("HAND-COMPUTED. Allocable 2,000 < hot bases 3,000 -> tier-1 decrease 1,000: (3)(A) "
               "A's depreciation 600 first -> A 900/B 1,500; (3)(B) remaining 400 ∝ 900:1,500 -> "
               "A −150 = 750, B −250 = 1,250. Tier-2 equipment gets ZERO (§732(c)(1)(B) 'to the "
               "extent of any basis remaining' — none remains).")},
    {"scenario_name": "7217-T8 — §737 gain included in line 9 (literal reading)", "scenario_type": "normal", "sort_order": 8,
     "inputs": {"tax_year": 2025, "liquidating": False, "sec751b": False,
                "outside_basis": 4000, "cash_received": 1000, "gain_737": 500,
                "distribution_date": "2025-10-01",
                "properties": [{"description": "LAND", "category": "other", "pship_basis": 6000, "fmv": 6000}]},
     "expected_outputs": {"f7217_line9": 3500, "f7217_line10": 3500, "col_e": [3500],
                          "D_7217_009": True, "D_7217_005": True},
     "notes": ("HAND-COMPUTED. line 9 = max(0, 4,000 − 1,000) + 500 = 3,500 (J3: floor before add; "
               "line 4 itself EXCLUDES the §737 gain per i7217). D_009 RED defers the gain's own "
               "income reporting.")},
    {"scenario_name": "7217-T9 — §731(c) marketable securities: 5b feeder, line-3 inclusion, line-9 5a-only", "scenario_type": "normal", "sort_order": 9,
     "inputs": {"tax_year": 2025, "liquidating": False, "sec751b": False,
                "outside_basis": 20000, "cash_received": 1000, "gain_737": 0,
                "securities_fmv_override": 0,
                "distribution_date": "2025-11-01",
                "properties": [{"description": "MARKETABLE SECURITIES", "category": "other",
                                "pship_basis": 3000, "fmv": 5000, "is_security": True},
                               {"description": "LAND", "category": "other", "pship_basis": 6000, "fmv": 6000}]},
     "expected_outputs": {"f7217_line3": 9000, "f7217_line5b": 5000, "f7217_line5c": 6000,
                          "f7217_line6": 6000, "f7217_line7": 0, "f7217_line9": 19000,
                          "f7217_line10": 9000, "col_e": [3000, 6000], "D_7217_005": False},
     "notes": ("HAND-COMPUTED (J6). 5b auto-totals the security row's FMV (5,000, YELLOW); line 3 "
               "INCLUDES the security's 3,000 basis; line 9 subtracts 5a ONLY (19,000 — securities "
               "never reduce it); line 10 = min(9,000, 19,000) = 9,000 = Σ bases -> carryover, no "
               "adjustment, no §731(c)(4) step-up computed.")},
    {"scenario_name": "7217-G1 — §731(a)(1) gain: money over basis, property basis zeroed", "scenario_type": "diagnostic", "sort_order": 10,
     "inputs": {"tax_year": 2025, "liquidating": False, "sec751b": False,
                "outside_basis": 3000, "cash_received": 5000, "gain_737": 0,
                "us_tax_on_gain": None,
                "distribution_date": "2025-03-20",
                "properties": [{"description": "EQUIPMENT", "category": "other", "pship_basis": 2000, "fmv": 2500}]},
     "expected_outputs": {"f7217_line5c": 5000, "f7217_line6": 3000, "f7217_line7": 2000,
                          "f7217_line9": 0, "f7217_line10": 0, "col_e": [0],
                          "f7217_8949_st": 0, "f7217_8949_lt": 0,
                          "D_7217_002": False, "D_7217_011": True, "D_7217_007": True,
                          "D_7217_005": True},
     "notes": ("HAND-COMPUTED. Cash 5,000 > outside 3,000 -> line 7 gain 2,000, but the holding "
               "period is UNASSERTED -> the 8949 feed is withheld (both feed outputs 0) + "
               "D_7217_011 RED + line 8 unanswered (D_007); D_002 info stays quiet (no feed made). "
               "Line 9 floors at 0 -> the distributed property takes ZERO basis (§732(a)(2) at its "
               "harshest).")},
    {"scenario_name": "7217-T10 — §731(a)(1) gain WIRED long-term (J1)", "scenario_type": "normal", "sort_order": 17,
     "inputs": {"tax_year": 2025, "liquidating": False, "sec751b": False,
                "outside_basis": 3000, "cash_received": 5000, "gain_737": 0,
                "us_tax_on_gain": True, "interest_held_lt": True,
                "distribution_date": "2025-03-20",
                "properties": [{"description": "EQUIPMENT", "category": "other", "pship_basis": 2000, "fmv": 2500}]},
     "expected_outputs": {"f7217_line7": 2000, "f7217_8949_st": 0, "f7217_8949_lt": 2000,
                          "D_7217_002": True, "D_7217_011": False, "D_7217_007": False},
     "notes": ("HAND-COMPUTED (the J1 wire). Same facts as G1 with the assertions answered: gain "
               "2,000 feeds Form 8949 Part II box F (LT — interest held > 1 year) as a synthesized "
               "no-1099-B row (proceeds 5,000 / basis 3,000), riding the existing 8949 -> Schedule "
               "D machinery; D_002 info reports the auto-feed.")},
    {"scenario_name": "7217-T11 — §731(a)(1) gain WIRED short-term (J1)", "scenario_type": "normal", "sort_order": 18,
     "inputs": {"tax_year": 2025, "liquidating": False, "sec751b": False,
                "outside_basis": 1000, "cash_received": 1600, "gain_737": 0,
                "us_tax_on_gain": True, "interest_held_lt": False,
                "distribution_date": "2025-08-15",
                "properties": [{"description": "SUPPLIES INVENTORY", "category": "hot", "pship_basis": 400, "fmv": 400}]},
     "expected_outputs": {"f7217_line7": 600, "f7217_8949_st": 600, "f7217_8949_lt": 0,
                          "f7217_line9": 0, "f7217_line10": 0, "col_e": [0],
                          "D_7217_002": True, "D_7217_011": False},
     "notes": ("HAND-COMPUTED. Interest held ≤ 1 year -> the 600 gain feeds 8949 Part I box C (ST; "
               "proceeds 1,600 / basis 1,000). Line 9 floors at 0 -> the inventory takes zero "
               "basis via the tier-1 (c)(3) decrease.")},
    {"scenario_name": "7217-G2 — §751(b) part answered Yes (RED defer, face still computes)", "scenario_type": "diagnostic", "sort_order": 11,
     "inputs": {"tax_year": 2025, "liquidating": False, "sec751b": True,
                "outside_basis": 10000, "cash_received": 0, "gain_737": 0,
                "distribution_date": "2025-06-30",
                "properties": [{"description": "BUILDING", "category": "other", "pship_basis": 5000, "fmv": 5000}]},
     "expected_outputs": {"f7217_line10": 5000, "col_e": [5000], "D_7217_001": True},
     "notes": "The §751(b) recharacterization defer — the statement + manual computation belong to the preparer."},
    {"scenario_name": "7217-G3 — money-only distribution: form not filed", "scenario_type": "diagnostic", "sort_order": 12,
     "inputs": {"tax_year": 2025, "liquidating": False, "sec751b": False,
                "outside_basis": 6000, "cash_received": 2000, "gain_737": 0,
                "distribution_date": "2025-02-10",
                "properties": []},
     "expected_outputs": {"f7217_line3": 0, "f7217_line10": 0, "D_7217_003": True},
     "notes": ("A cash-only distribution never files Form 7217 (i7217 verbatim don't-file rule); the "
               "entry itself is the error. Securities-only rows fire the same way.")},
    {"scenario_name": "7217-G4 — §731(a)(2) liquidating loss (hot assets only)", "scenario_type": "diagnostic", "sort_order": 13,
     "inputs": {"tax_year": 2025, "liquidating": True, "sec751b": False,
                "outside_basis": 5000, "cash_received": 1000, "gain_737": 0,
                "distribution_date": "2025-12-01",
                "properties": [{"description": "RECEIVABLES", "category": "hot", "pship_basis": 2500, "fmv": 2500}]},
     "expected_outputs": {"f7217_line3": 2500, "f7217_line9": 4000, "f7217_line10": 4000,
                          "col_e": [2500], "f7217_loss_731a2": 1500,
                          "D_7217_006": True, "D_7217_005": True},
     "notes": ("HAND-COMPUTED (J2). Liquidating, only money + receivables: tier-1 caps at basis "
               "2,500 < line 10 4,000 -> §731(a)(2) LOSS 1,500 (capital) — D_006 RED, Schedule D "
               "manual. The one lawful line-10 ≠ B(e) case; the face's equality rule cannot hold.")},
    {"scenario_name": "7217-G5 — property unclassified: allocation withheld", "scenario_type": "diagnostic", "sort_order": 14,
     "inputs": {"tax_year": 2025, "liquidating": False, "sec751b": False,
                "outside_basis": 8000, "cash_received": 0, "gain_737": 0,
                "distribution_date": "2025-05-05",
                "properties": [{"description": "MYSTERY ASSET", "category": None, "pship_basis": 2000, "fmv": 2000},
                               {"description": "LAND", "category": "other", "pship_basis": 1000, "fmv": 1000}]},
     "expected_outputs": {"f7217_line3": 3000, "f7217_line10": 3000, "col_e": [0, 0], "D_7217_008": True},
     "notes": ("J5: one unclassified row withholds the ENTIRE Part II allocation (all col (e) = 0) + "
               "RED — computing a wrong §732(c) tier is worse than computing nothing.")},
    {"scenario_name": "7217-G7 — outside basis unanswered (required-entry gate)", "scenario_type": "diagnostic", "sort_order": 16,
     "inputs": {"tax_year": 2025, "liquidating": False, "sec751b": False,
                "outside_basis": None, "cash_received": 0, "gain_737": 0,
                "distribution_date": "2025-03-01",
                "properties": [{"description": "EQUIPMENT", "category": "other", "pship_basis": 3000, "fmv": 3000}]},
     "expected_outputs": {"D_7217_004": True},
     "notes": ("Line 4 is the partner's OWN computation (not on the K-1) — unanswered (None) fires "
               "the required-entry RED. An entered 0 is valid (fully depleted basis) and does not "
               "fire; the nullable-fact distinction matters at the tts model leg.")},
    {"scenario_name": "7217-G6 — distribution date outside the return year", "scenario_type": "diagnostic", "sort_order": 15,
     "inputs": {"tax_year": 2025, "liquidating": False, "sec751b": False,
                "outside_basis": 9000, "cash_received": 0, "gain_737": 0,
                "distribution_date": "2024-06-01",
                "properties": [{"description": "TRUCK", "category": "other", "pship_basis": 4000, "fmv": 3000}]},
     "expected_outputs": {"D_7217_010": True},
     "notes": "The claim-year trap: a 2024 distribution belongs on the 2024 return (i7217 When To File)."},
]

F7217_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-7217-FILE", "IRS_2024_7217_INSTR", "primary", "Who Must File verbatim: per-date form; money-only/securities-only never file; §707 screens"),
    ("R-7217-FILE", "IRS_2024_7217_FORM", "secondary", "Part I heading: 'File a separate form for each date'"),
    ("R-7217-GAIN", "USC_26_731", "primary", "§731(a)(1) gain = money over outside basis; sale/exchange character"),
    ("R-7217-GAIN", "IRS_2025_K1P_INSTR", "primary", "Box 19 verbatim: the gain 'should be reported on Form 8949 and the Schedule D' — the J1 wire's landing"),
    ("R-7217-GAIN", "IRS_2024_7217_INSTR", "secondary", "Lines 5a/5b sourcing (§752(b) deemed money; §731(c) securities); col (e) §731(c)(4) exclusion"),
    ("R-7217-L9L10", "USC_26_732", "primary", "§732(a)(1)/(a)(2)/(b): carryover-capped vs substituted basis"),
    ("R-7217-L9L10", "IRS_2024_7217_INSTR", "secondary", "Lines 9/10 verbatim: 5a-only subtraction, floor, §737 include, smaller-of"),
    ("R-7217-ALLOC", "USC_26_732", "primary", "§732(c)(1)-(3) verbatim waterfall (tiers, increase, decrease)"),
    ("R-7217-ALLOC", "IRS_2024_7217_INSTR", "secondary", "Example 2 — the IRS's own worked waterfall (pinned by 7217-T3)"),
    ("R-7217-LOSS", "USC_26_731", "primary", "§731(a)(2): loss only on liquidation with money + hot assets only; capital character"),
    ("R-7217-LOSS", "USC_26_732", "secondary", "§732(c)(1)(A)/(c)(2): tier-1 capped at basis, no tier-1 increase arm — the loss mechanism"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS (loader-homed — the FA-needs-an-RS-home lesson)
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-7217-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Part I arithmetic chain: 5c = 5a + 5b; 6 = min(4, 5c); 7 = 5c − 6; 9 = max(0, 4 − 5a) + §737; 10 = liq ? 9 : min(3, 9)",
     "description": ("Validates R-7217-GAIN + R-7217-L9L10 against the form face. Bugs it catches: "
                     "line 9 subtracting 5b securities (it must subtract 5a ONLY), the §737 add "
                     "applied before the floor, or the liquidating branch using the smaller-of."),
     "definition": {"kind": "formula_check", "form": "FORM_7217",
                    "formula": ("line_5c == line_5a + line_5b; line_6 == min(line_4, line_5c); "
                                "line_7 == line_5c - line_6; line_9 == max(0, line_4 - line_5a) + gain_737; "
                                "line_10 == (line_9 if liquidating else min(line_3, line_9))")},
     "sort_order": 1},
    {"assertion_id": "FA-1040-7217-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Allocation invariant: Σ Part II col (e) == line 10, except the §731(a)(2) loss edge where D_7217_006 must fire",
     "description": ("Validates R-7217-ALLOC's conservation property + R-7217-LOSS's escape hatch. "
                     "Bug it catches: basis leaking in the waterfall (rounding drift, a dropped "
                     "row), or the liquidating hot-asset-only loss silently swallowed instead of "
                     "surfacing RED."),
     "definition": {"kind": "conditional_check", "form": "FORM_7217",
                    "checks": [{"when": "not (liquidating and all_properties_hot)",
                                "assert": "sum(col_e) == line_10"},
                               {"when": "liquidating and all_properties_hot and sum(col_e) < line_10",
                                "assert": "D_7217_006 fires and loss_731a2 == line_10 - sum(col_e)"}]},
     "sort_order": 2},
    {"assertion_id": "FA-1040-7217-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Tier discipline: a hot-asset row's col (e) never exceeds its col (b); tier-2 rows get 0 when tier-1 exhausts the allocable basis",
     "description": ("Validates the §732(c)(1)(A) cap (increases reach ONLY (1)(B) 'other' rows — "
                     "§732(c)(2)'s own text) and the tier ordering. Bug it catches: a liquidating "
                     "increase stepping up inventory/receivables above partnership basis (unlawful; "
                     "pinned by 7217-T3 inventory = 100 exactly) or hot assets and other property "
                     "sharing a decrease pro-rata across tiers (7217-T7 pins equipment = 0)."),
     "definition": {"kind": "invariant_check", "form": "FORM_7217",
                    "invariants": ["col_e[row] <= col_b[row] for every category='hot' row",
                                   "col_e[row] == 0 for every category='other' row when line_10 <= sum(col_b of hot rows)"]},
     "sort_order": 3},
    {"assertion_id": "FA-1040-7217-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "No silent flows: unasserted-holding-period gain / §737 gain / §731(a)(2) loss / §751(b) surface RED and feed NOTHING (v1 defers)",
     "description": ("Validates the J2/J3 + §751(b) defers and the J1 withhold arm: §737 gain and "
                     "the §731(a)(2) liquidating loss fire their REDs (D_7217_009/006) and never "
                     "land anywhere; a §751(b) Yes fires D_7217_001; and a line-7 gain with the "
                     "holding period UNASSERTED fires D_7217_011 with BOTH 8949 feed outputs zero. "
                     "Bug it catches: a feed leaking despite its gate (the gate-and-cascade-must-"
                     "agree lesson)."),
     "definition": {"kind": "gating_check", "form": "FORM_7217", "expect": {"red_fires": True},
                    "blockers": ["gain_737_no_income_feed", "loss_731a2_no_schd_feed",
                                 "sec751b_no_recharacterization", "gain_unasserted_holding_no_feed"]},
     "sort_order": 4},
    {"assertion_id": "FA-1040-7217-05", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "§731(a)(1) gain feed: line 7 -> a synthesized 8949 no-1099-B row (box C ST / box F LT per assertion) -> Schedule D netting",
     "description": ("Validates the J1 wire (Ken 2026-07-02): when line 7 > 0 and the holding "
                     "period is asserted, exactly one 8949 row per gaining distribution carries "
                     "proceeds = line 5c, basis = line 6, gain = line 7 into the EXISTING 8949 -> "
                     "Schedule D machinery (ST vs LT by the assertion), and D_7217_002 info "
                     "reports it. Bug it catches: the gain double-fed (a raw Sch D line write PLUS "
                     "the 8949 row), the character flipped, or proceeds/basis presented so the row "
                     "nets a different gain than line 7."),
     "definition": {"kind": "flow_assertion", "form": "FORM_7217",
                    "checks": [{"source_line": "7", "must_write_to": ["FORM_8949.row", "SCH_D.netting"],
                                "character": "st_or_lt_per_assertion",
                                "row_identity": "proceeds=line_5c, basis=line_6, gain=line_7"}]},
     "sort_order": 5},
]


FORMS: list[dict] = [
    {"identity": F7217_IDENTITY, "facts": F7217_FACTS, "rules": F7217_RULES, "lines": F7217_LINES,
     "diagnostics": F7217_DIAGNOSTICS, "scenarios": F7217_SCENARIOS, "rule_links": F7217_RULE_LINKS},
]


class Command(BaseCommand):
    help = "Load the FORM_7217 spec (§732 distributed-property basis, ATS Scenario 12). Refuses until READY_TO_SEED=True."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad FORM_7217 spec (§732 distributed property, ATS Scenario 12)\n"))
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
                "\nREFUSING TO SEED FORM_7217: not cleared to seed.\n\n"
                "Gated until Ken's review walk (J1 gain-flow defer; J2 §731(a)(2) loss defer; J3 the\n"
                "§737 line-9 literal reading; J4 the rounding convention; J5 the hot/other preparer\n"
                "classification withhold; J6 the securities 5b feeder — plus the T1 answer-key\n"
                "divergence documentation).\n\n"
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
        form = TaxForm.objects.filter(form_number="FORM_7217").first()
        if form:
            uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
            self.stdout.write("FORM_7217: all rules cited" if not uncited
                              else self.style.WARNING(f"FORM_7217 uncited rules: {len(uncited)}"))
