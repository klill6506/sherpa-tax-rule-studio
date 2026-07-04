"""Load the Schedule K-1 (Form 1065) + allocation-engine spec — form 2 of the 1065-core campaign.

Fresh-authored 2026-07-04 per D-1 (author fresh → Ken walk → reconcile → seed). Governs the
PER-PARTNER Schedule K-1 (Form 1065): Part I (partnership), Part II items E-N (partner /
ownership %, liabilities, capital account, §704(c)), Part III boxes 1-23 (the partner's
distributive share), AND the allocation engine that splits each Schedule K total (SCH_K_1065)
into the per-partner K-1 boxes.

Form number: `SCHEDULE_K1_1065` (the ENTITY-side per-partner allocation output for a 1065).
Distinct from the existing `SCHEDULE_K1` (entity=1040, the RECIPIENT side that aggregates a
received K-1 onto the partner's Schedule E).

RECONCILE TARGET (D-1, brief §2 — surveyed read-only 2026-07-04): `server/apps/returns/
k1_allocator.py` (`allocate_k1` / `allocate_all_k1s` / `resolve_se_classification` +
`get_allocation_pct`) and the `Partner` / `PartnerAllocation` models. The spec ENCODES what the
engine does and RED-DEFERS what it does not, per Ken Decision C. What the engine does (verbatim
from the survey):
  - Per-partner box = entity Schedule K line × `profit_pct` (amount ≥ 0) or `loss_pct` (amount < 0),
    OVERRIDABLE per-category by a `PartnerAllocation(category, percentage)` row (Lacerte-style
    special allocation). `capital_pct` EXISTS but is UNUSED in allocation.
  - Guaranteed payments (boxes 4a/4b/4c) = `partner.gp_services` / `gp_capital` / their sum —
    DIRECT per-partner, NOT ratio'd. Distributions (box 19a) = `partner.distributions` — DIRECT.
  - Box 9c (unrecaptured §1250 gain) = entity K9c × LT_CAPITAL ratio (`profit_pct`) — reads `K9c`,
    writes box `9c`. CONFIRMED correct (closes the STATUS box-9c pass-through verification at the
    code-path level; RECON-9C asserts Σ partner 9c = entity K9c).
  - Box 14a SE = the `1065_SE` spec's per-partner §1402(a)(13) classification (active/passive/
    undetermined→active). Cross-referenced, NOT recomputed here.
  - Items J (profit/loss/capital % + BOY), K (recourse / qualified-nonrecourse / nonrecourse
    liabilities) are MODELED on `Partner`. Item L capital-account FIELDS exist (BOY / contributed /
    current-year increase / withdrawals / EOY) but there is NO roll-forward computation — data-entry
    only, so Schedule M-2 line 1 cannot auto-derive (carried to the M-2 leg). Items M / N ABSENT.

RED-DEFERRED (engine absent; Ken Decision C — structure + cited authority + gating flags, MATH
deferred): §704(c) built-in-gain allocation (item M), §704(b) substantial-economic-effect testing
(item N), §706(d) varying-interest mid-year proration, and the item-L capital roll-forward. Each
is captured as a fact/flag + a RED/ warning diagnostic, not computed.

RECONCILE GAPS logged for the Ken walk (D-1 adjudications):
  - `capital_pct` is defined on `Partner` but UNUSED — nothing allocates by it. Distributions use
    direct per-partner entry (correct per the form). Confirm no capital-account-change item should
    ride capital_pct. (D_K1_CAPPCT.)
  - Item L capital roll-forward is not computed → M-2 line 1 (changes in partners' capital) cannot
    auto-derive. Carried to the M-2/L leg. (D_K1_ITEML.)
  - §706(d) mid-year interest change: all allocations are full-year pro-rata (no proration).

AUTHORITY QUOTING (CLAUDE.md Authoritative-Source Rule): §704(a)/(b), §706(d)(1), §752(a)/(b),
§705(a) were read DIRECTLY from the U.S. Code and quoted VERBATIM 2026-07-04 (Cornell LII mirror);
§702(b) / §707(c) are re-used from the vetted spine / 1065_SE loads. The 2025 Schedule K-1 (Form
1065) face + Partner's Instructions line/item/box structure is the brief §4.2 verbatim transcription
of the FINAL 2025 f1065sk1 (Cat. 11394R, form ID 651123, "Created 2/26/25") + i1065sk1 (filing
authority, requires_human_review — re-verify at the walk).

CODED BOXES (SCOPE — Ken to confirm at the walk): this leg encodes the box STRUCTURE (Part III
boxes 1-23) + the LOAD-BEARING codes (box 15 the S3/S4 pass-through credits; box 20 §199A code Z /
§704(c) AA / §751 AB / §163(j) N/AE/AF / §461(l) AJ; box 13 §181 code X; box 11 F / box 13 V =
§743(b)). The EXHAUSTIVE ~200-code enumeration (every letter A-ZZ within boxes 11/13/15/17/18/19/20)
is reference metadata not tied to the allocation math — flagged as a follow-up pending the Ken walk
(full transcription needs the i1065sk1 code tables re-fetched verbatim).
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


# FRESH-AUTHORED 2026-07-04 (Schedule K-1 + allocation leg). Per D-1: authored with
# READY_TO_SEED=False; Ken walks the reconcile findings + the coded-box scope question,
# THEN this flips to True and seeds. Held until the walk.
READY_TO_SEED = False


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1065"]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("partnership_1065_core",
     "Partnership return core (Form 1065) — the Schedule K distributive-share spine and the "
     "Schedule K-1 per-partner allocation (§704 allocations, §706(d) varying interest, §752 "
     "liabilities, §705 capital/basis)."),
    ("partner_k1_allocation",
     "Schedule K-1 (Form 1065) allocation — distributive share by the partnership agreement / "
     "partner's interest (§704(a)/(b)), special allocations, §704(c) built-in gain, §706(d) "
     "varying interest, item J/K/L/M/N reporting."),
]

AUTHORITY_SOURCES: list[dict] = [
    # ── IRC §704 — allocation (agreement; SEE fallback; §704(c) built-in gain) ──
    {
        "source_code": "IRC_704",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1065",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §704 — Partner's Distributive Share (agreement controls; substantial-economic-"
                 "effect fallback; §704(c) built-in gain)",
        "citation": "26 U.S.C. §704(a), (b), (c)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/704",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "The allocation statute the K-1 split follows. §704(a) agreement controls; §704(b) "
                 "partner's-interest fallback if silent or an allocation lacks substantial economic "
                 "effect; §704(c) built-in gain to the contributing partner (item M/N). tts "
                 "k1_allocator implements per-category pro-rata (profit/loss %) + PartnerAllocation "
                 "overrides; §704(b) SEE testing and §704(c) math are ABSENT → RED-deferred "
                 "(Decision C). §704(a)/(b) quoted verbatim 2026-07-04.",
        "topics": ["partnership_1065_core", "partner_k1_allocation"],
        "excerpts": [
            {
                "excerpt_label": "§704(a) — the partnership agreement controls",
                "location_reference": "26 U.S.C. §704(a)",
                "excerpt_text": (
                    "A partner's distributive share of income, gain, loss, deduction, or credit shall, "
                    "except as otherwise provided in this chapter, be determined by the partnership "
                    "agreement."
                ),
                "summary_text": "Distributive share = whatever the partnership agreement provides "
                                "(subject to §704(b)). The engine's profit/loss % + PartnerAllocation "
                                "overrides encode 'the agreement.'",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§704(b) — partner's-interest fallback (no substantial economic effect)",
                "location_reference": "26 U.S.C. §704(b)(1), (2)",
                "excerpt_text": (
                    "A partner's distributive share of income, gain, loss, deduction, or credit (or item "
                    "thereof) shall be determined in accordance with the partner's interest in the "
                    "partnership (determined by taking into account all facts and circumstances), if— "
                    "(1) the partnership agreement does not provide as to the partner's distributive "
                    "share of income, gain, loss, deduction, or credit (or item thereof), or (2) the "
                    "allocation to a partner under the agreement of income, gain, loss, deduction, or "
                    "credit (or item thereof) does not have substantial economic effect."
                ),
                "summary_text": "If the agreement is silent OR an allocation lacks substantial economic "
                                "effect, allocate by the partner's interest. SEE testing is RED-deferred "
                                "(D_K1_SPECIAL_ALLOC surfaces a PartnerAllocation override for review).",
                "is_key_excerpt": True,
            },
        ],
    },
    # ── IRC §706(d) — varying interest (mid-year interest change) ──
    {
        "source_code": "IRC_706D",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1065",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §706(d) — Determination of Distributive Share When a Partner's Interest Changes "
                 "(varying interests)",
        "citation": "26 U.S.C. §706(d)(1)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/706",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "When a partner's interest changes mid-year, the distributive share must reflect the "
                 "varying interests (interim closing of the books or proration). tts k1_allocator does "
                 "NOT prorate — all allocations are full-year pro-rata → RED-deferred (D_K1_706D). "
                 "Quoted verbatim 2026-07-04.",
        "topics": ["partner_k1_allocation"],
        "excerpts": [
            {
                "excerpt_label": "§706(d)(1) — varying interests general rule",
                "location_reference": "26 U.S.C. §706(d)(1)",
                "excerpt_text": (
                    "Except as provided in paragraphs (2) and (3), if during any taxable year of the "
                    "partnership there is a change in any partner's interest in the partnership, each "
                    "partner's distributive share of any item of income, gain, loss, deduction, or credit "
                    "of the partnership for such taxable year shall be determined by the use of any method "
                    "prescribed by the Secretary by regulations which takes into account the varying "
                    "interests of the partners in the partnership during such taxable year."
                ),
                "summary_text": "Mid-year interest changes require a method (interim closing / proration) "
                                "that reflects varying interests. Not modeled by the engine → RED-defer.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ── IRC §752 — partnership liabilities (item K) ──
    {
        "source_code": "IRC_752",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1065",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §752 — Treatment of Certain Liabilities (share of liabilities as contribution/"
                 "distribution of money)",
        "citation": "26 U.S.C. §752(a), (b)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/752",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "A partner's share of partnership liabilities (K-1 item K: recourse / qualified "
                 "nonrecourse / nonrecourse) is treated as a money contribution (increase) or "
                 "distribution (decrease) affecting outside basis. tts Partner models the three "
                 "liability buckets (data-entry). Quoted verbatim 2026-07-04.",
        "topics": ["partner_k1_allocation"],
        "excerpts": [
            {
                "excerpt_label": "§752(a) — increase in liabilities = contribution of money",
                "location_reference": "26 U.S.C. §752(a)",
                "excerpt_text": (
                    "Any increase in a partner's share of the liabilities of a partnership, or any "
                    "increase in a partner's individual liabilities by reason of the assumption by such "
                    "partner of partnership liabilities, shall be considered as a contribution of money "
                    "by such partner to the partnership."
                ),
                "summary_text": "An increase in a partner's liability share = a money contribution "
                                "(raises outside basis). Item K reports the shares.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§752(b) — decrease in liabilities = distribution of money",
                "location_reference": "26 U.S.C. §752(b)",
                "excerpt_text": (
                    "Any decrease in a partner's share of the liabilities of a partnership, or any "
                    "decrease in a partner's individual liabilities by reason of the assumption by the "
                    "partnership of such individual liabilities, shall be considered as a distribution of "
                    "money to the partner by the partnership."
                ),
                "summary_text": "A decrease in a partner's liability share = a money distribution "
                                "(reduces outside basis). Item K basis effect (why item L tax-basis "
                                "capital 'might not equal' outside basis).",
                "is_key_excerpt": False,
            },
        ],
    },
    # ── IRC §705 — partner's basis (item L tax-basis capital) ──
    {
        "source_code": "IRC_705",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1065",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §705 — Determination of Basis of Partner's Interest (transactional roll-forward)",
        "citation": "26 U.S.C. §705(a)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/705",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "The transactional roll-forward behind item L tax-basis capital: basis (from §722/§742) "
                 "increased by the distributive share of income (incl. tax-exempt) and decreased (not "
                 "below zero) by distributions (§733) and the share of losses / nondeductible "
                 "expenditures. tts stores item-L fields but does NOT compute the roll-forward → "
                 "RED-deferred (D_K1_ITEML); M-2 line 1 cannot auto-derive. Key phrases quoted 2026-07-04.",
        "topics": ["partner_k1_allocation"],
        "excerpts": [
            {
                "excerpt_label": "§705(a) — basis increased by income, decreased by distributions/losses",
                "location_reference": "26 U.S.C. §705(a)(1), (2)",
                "excerpt_text": (
                    "The adjusted basis of a partner's interest in a partnership shall, except as provided "
                    "in subsection (b), be the basis of such interest determined under section 722 "
                    "(relating to contributions to a partnership) or section 742 (relating to transfers of "
                    "partnership interests)— (1) increased by the sum of his distributive share for the "
                    "taxable year and prior taxable years of— (A) taxable income of the partnership as "
                    "determined under section 703(a), (B) income of the partnership exempt from tax, and "
                    "(C) the excess of the deductions for depletion over the basis of the property subject "
                    "to depletion; (2) decreased (but not below zero) by distributions by the partnership "
                    "as provided in section 733 and by the sum of his distributive share for the taxable "
                    "year and prior taxable years of— (A) losses of the partnership, and (B) expenditures "
                    "of the partnership not deductible in computing its taxable income and not properly "
                    "chargeable to capital account."
                ),
                "summary_text": "The item-L transactional roll-forward: BOY + income share (incl. "
                                "tax-exempt) − distributions − loss/nondeductible share = EOY. §733 "
                                "distributions; not below zero.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ── IRC §707(c) — guaranteed payments (boxes 4a/4b/4c, direct) ──
    {
        "source_code": "IRC_707C",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1065",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §707(c) — Guaranteed Payments (services or use of capital)",
        "citation": "26 U.S.C. §707(c)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/707",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "Guaranteed payments are per-partner amounts (not ratio-allocated): tts writes boxes "
                 "4a=gp_services, 4b=gp_capital, 4c=sum DIRECTLY from the Partner model. Re-used from "
                 "the vetted 1065_SE / spine loads; verbatim 2026-07-01.",
        "topics": ["partner_k1_allocation"],
        "excerpts": [
            {
                "excerpt_label": "§707(c) — guaranteed payments for services or use of capital",
                "location_reference": "26 U.S.C. §707(c)",
                "excerpt_text": (
                    "To the extent determined without regard to the income of the partnership, payments to "
                    "a partner for services or the use of capital shall be considered as made to one who is "
                    "not a member of the partnership, but only for the purposes of section 61(a) (relating "
                    "to gross income) and, subject to section 263, for purposes of section 162(a) (relating "
                    "to trade or business expenses)."
                ),
                "summary_text": "Guaranteed payments (services 4a / capital 4b, total 4c) are per-partner "
                                "direct amounts, not a pro-rata split of an entity total.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ── IRC §702(b) — character conduit (each box keeps character) ──
    {
        "source_code": "IRC_702",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1065",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §702 — Income and Credits of Partner (separately stated share; character conduit)",
        "citation": "26 U.S.C. §702(a), (b)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/702",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "The K-1 boxes ARE the §702(a) separately-stated items, each retaining partnership-level "
                 "character in the partner's hands (§702(b)). Re-used from the spine load; verbatim.",
        "topics": ["partner_k1_allocation"],
        "excerpts": [
            {
                "excerpt_label": "§702(b) — character determined at the partnership level",
                "location_reference": "26 U.S.C. §702(b)",
                "excerpt_text": (
                    "The character of any item of income, gain, loss, deduction, or credit included in a "
                    "partner's distributive share under paragraphs (1) through (7) of subsection (a) shall "
                    "be determined as if such item were realized directly from the source from which "
                    "realized by the partnership, or incurred in the same manner as incurred by the "
                    "partnership."
                ),
                "summary_text": "Each K-1 box keeps its partnership-level character (capital stays capital, "
                                "portfolio stays portfolio) — the reason boxes are separately stated.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ── 2025 Schedule K-1 (Form 1065) — the face (items J-N + Part III boxes) ──
    {
        "source_code": "IRS_2025_F1065SK1",
        "source_type": "official_form",
        "source_rank": "implementation_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1065",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "Schedule K-1 (Form 1065) (2025) — Partner's Share of Income, Deductions, Credits, etc. "
                 "(Part I / Part II items E-N / Part III boxes 1-23)",
        "citation": "Schedule K-1 (Form 1065) (2025), Cat. No. 11394R, form ID 651123 (\"Created 2/26/25\")",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f1065sk1.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": "The K-1 face structure (Part II items J profit/loss/capital %, K liabilities, L "
                 "tax-basis capital, M contributed built-in-gain property, N net unrecognized §704(c) "
                 "gain; Part III boxes 1-23) per the brief §4.2 verbatim transcription of the FINAL 2025 "
                 "f1065sk1. REQUIRES HUMAN REVIEW: re-verify at the Ken walk.",
        "topics": ["partner_k1_allocation"],
        "excerpts": [
            {
                "excerpt_label": "Part II items J-N (verbatim labels)",
                "location_reference": "Schedule K-1 (Form 1065) 2025, Part II items J-N",
                "excerpt_text": (
                    "J Partner's share of profit, loss, and capital: Beginning / Ending (%); check if "
                    "decrease is due to sale or exchange of partnership interest. K Partner's share of "
                    "liabilities: Nonrecourse / Qualified nonrecourse financing / Recourse (Beginning / "
                    "Ending); check if includes liabilities from lower-tier partnerships; check if any "
                    "amounts are subject to guarantees or other payment obligations. L Partner's capital "
                    "account analysis (TAX BASIS): Beginning capital account; Capital contributed during "
                    "the year; Current year net income (loss); Other increase (decrease); Withdrawals and "
                    "distributions; Ending capital account. M Did the partner contribute property with a "
                    "built-in gain or loss? Yes/No. N Partner's share of net unrecognized section 704(c) "
                    "gain or (loss): Beginning / Ending."
                ),
                "summary_text": "Part II: J ownership % (beg/end + sale flag); K liabilities (3 buckets); "
                                "L tax-basis capital roll-forward; M contributed built-in-gain property; "
                                "N net unrecognized §704(c) gain.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part III boxes 1-23 (verbatim labels)",
                "location_reference": "Schedule K-1 (Form 1065) 2025, Part III",
                "excerpt_text": (
                    "1 Ordinary business income (loss). 2 Net rental real estate income (loss). 3 Other "
                    "net rental income (loss). 4a Guaranteed payments for services. 4b Guaranteed payments "
                    "for capital. 4c Total guaranteed payments. 5 Interest income. 6a Ordinary dividends. "
                    "6b Qualified dividends. 6c Dividend equivalents. 7 Royalties. 8 Net short-term "
                    "capital gain (loss). 9a Net long-term capital gain (loss). 9b Collectibles (28%) gain "
                    "(loss). 9c Unrecaptured section 1250 gain. 10 Net section 1231 gain (loss). 11 Other "
                    "income (loss). 12 Section 179 deduction. 13 Other deductions. 14 Self-employment "
                    "earnings (loss). 15 Credits. 16 Schedule K-3 is attached if checked. 17 Alternative "
                    "minimum tax (AMT) items. 18 Tax-exempt income and nondeductible expenses. 19 "
                    "Distributions. 20 Other information. 21 Foreign taxes paid or accrued. 22 More than "
                    "one activity for at-risk purposes. 23 More than one activity for passive activity "
                    "purposes."
                ),
                "summary_text": "Part III boxes 1-10 map 1:1 from Schedule K; boxes 11/13/14/15/17/18/19/20 "
                                "are coded collapses; box 16 = K-3 checkbox; 22/23 are K-1-only "
                                "multi-activity flags.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ── 2025 Partner's Instructions (i1065sk1) — allocation mechanics + coded-box code lists ──
    {
        "source_code": "IRS_2025_I1065SK1",
        "source_type": "official_instructions",
        "source_rank": "implementation_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1065",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Partner's Instructions for Schedule K-1 (Form 1065) — coded-box code lists + "
                 "the K → K-1 correspondence",
        "citation": "Partner's Instructions for Schedule K-1 (Form 1065) (2025); Instructions for Form "
                    "1065 (2025) allocation mechanics (pp. 31/34)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i1065sk1.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": "The coded-box code lists (boxes 11/13/15/17/18/19/20, ~200 codes) + the K→K-1 "
                 "correspondence + allocation mechanics (special allocations on the applicable K-1 line; "
                 "§706(d) varying interest; §704(c) reasonable method) per the brief §4.2. LOAD-BEARING "
                 "codes encoded this leg; the exhaustive enumeration is a flagged follow-up "
                 "(requires_human_review — re-fetch the code tables verbatim at the walk).",
        "topics": ["partner_k1_allocation"],
        "excerpts": [
            {
                "excerpt_label": "Allocation mechanics + special allocations (verbatim)",
                "location_reference": "i1065 (2025) pp. 31/34, Analysis + Specific Instructions",
                "excerpt_text": (
                    "Allocate to each partner a proportionate share of each item reported on Schedule K "
                    "unless the partnership agreement provides for a special allocation. Specially "
                    "allocated items are reported on the applicable line of the partner's Schedule K-1 and "
                    "are included in the total on the corresponding line of Schedule K, not on the "
                    "numbered lines of page 1. If a partner's interest changed during the year, figure the "
                    "distributive share using the interim closing of the books method or, by agreement, "
                    "the proration method (section 706(d)). Allocations of contributed property with a "
                    "built-in gain or loss must be made under a reasonable method (section 704(c))."
                ),
                "summary_text": "Pro-rata by the agreement unless specially allocated; §706(d) mid-year; "
                                "§704(c) reasonable method. The engine models pro-rata + per-category "
                                "overrides; §706(d)/§704(c) are RED-deferred.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Load-bearing coded boxes (15/20/13) — notable codes",
                "location_reference": "i1065sk1 (2025), boxes 13/15/20 code lists (notable subset)",
                "excerpt_text": (
                    "Box 15 (Credits): includes AY (new clean vehicle credit, Form 8936), AZ (commercial "
                    "clean vehicle, 8936 Part V), AB (renewable electricity production, Form 8835), W "
                    "(clean electricity production, §45Y). Box 20 (Other information): Z (section 199A "
                    "information), AA (section 704(c) information), AB (section 751 gain/loss), N/AE/AF "
                    "(section 163(j) business interest expense / excess taxable income / excess business "
                    "interest income), AG (section 448(c) gross receipts), AJ (excess business loss, "
                    "section 461(l), partner-level). Box 13 (Other deductions): X (section 181 / section "
                    "179D and other elective deductions, incl. OBBBA qualified sound-recording); V "
                    "(section 743(b) negative adjustment). Box 11 code F / box 13 code V = section 743(b) "
                    "positive/negative adjustments (the §754 tie)."
                ),
                "summary_text": "The compute-relevant codes: box 15 S3/S4 pass-through credits (AY/AZ/AB/W); "
                                "box 20 §199A (Z), §704(c) (AA), §751 (AB), §163(j) (N/AE/AF), §461(l) EBL "
                                "(AJ); box 13 §181 (X), §743(b) (V). Full A-ZZ enumeration = follow-up.",
                "is_key_excerpt": True,
            },
        ],
    },
]

# (source_code, form_code, link_type)
AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRC_704", "SCHEDULE_K1_1065", "governs"),
    ("IRC_706D", "SCHEDULE_K1_1065", "governs"),
    ("IRC_752", "SCHEDULE_K1_1065", "informs"),
    ("IRC_705", "SCHEDULE_K1_1065", "informs"),
    ("IRC_707C", "SCHEDULE_K1_1065", "informs"),
    ("IRC_702", "SCHEDULE_K1_1065", "informs"),
    ("IRS_2025_F1065SK1", "SCHEDULE_K1_1065", "governs"),
    ("IRS_2025_I1065SK1", "SCHEDULE_K1_1065", "governs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM: SCHEDULE_K1_1065
# ═══════════════════════════════════════════════════════════════════════════

FORM_IDENTITY = {
    "form_number": "SCHEDULE_K1_1065",
    "form_title": "Schedule K-1 (Form 1065, 2025) — Partner's Distributive Share + Allocation Engine",
    "notes": (
        "FRESH-AUTHORED 2026-07-04 (1065-core campaign, form 2 of 6) — the per-partner allocation of "
        "the SCH_K_1065 spine into each partner's K-1. Reconciled against tts k1_allocator.py "
        "(read-only survey): per-partner box = entity Sch K line × profit_pct (≥0) / loss_pct (<0), "
        "overridable per-category by PartnerAllocation (Lacerte special allocations); GP (4a/4b/4c) + "
        "distributions (19a) are DIRECT per-partner; box 9c = LT_CAPITAL/profit_pct (CONFIRMED — closes "
        "the box-9c verification); box 14a = the 1065_SE spec (cross-ref). Part II items J (profit/loss/"
        "capital %) + K (§752 liabilities) modeled; item L capital FIELDS exist but NO roll-forward "
        "compute (M-2 line 1 can't auto-derive — M-2 leg); items M/N (§704(c)) ABSENT. RED-DEFERRED per "
        "Ken Decision C (structure + cited authority + gating flag, MATH deferred): §704(c) built-in "
        "gain (M/N), §704(b) SEE, §706(d) varying interest, item-L roll-forward. Primary IRC verbatim "
        "(§704(a)/(b), §706(d)(1), §752(a)/(b), §705(a); §702(b)/§707(c) reused). Coded boxes: STRUCTURE "
        "+ load-bearing codes (box 15 S3/S4 credits; box 20 §199A/§704(c)/§163(j)/§461(l); box 13 §181; "
        "§743(b)); exhaustive ~200-code enumeration flagged as a follow-up (Ken walk). READY_TO_SEED=False."
    ),
}

FACTS: list[dict] = [
    # ── Allocation inputs (Partner model) ──
    {"fact_key": "k1_partner_type", "label": "Partner type (general / limited / llc_member)",
     "data_type": "choice", "default_value": "general", "sort_order": 1,
     "choices": ["general", "limited", "llc_member"],
     "notes": "Drives SE classification (1065_SE) + item J general-vs-limited."},
    {"fact_key": "k1_profit_pct", "label": "Item J — profit-sharing % (allocates income/gain boxes)",
     "data_type": "decimal", "default_value": "0", "sort_order": 2,
     "notes": "The ratio applied when the entity Sch K amount is ≥ 0 (income/gain). tts profit_pct."},
    {"fact_key": "k1_loss_pct", "label": "Item J — loss-sharing % (allocates loss boxes)",
     "data_type": "decimal", "default_value": "0", "sort_order": 3,
     "notes": "The ratio applied when the entity Sch K amount is < 0 (loss). tts loss_pct."},
    {"fact_key": "k1_capital_pct", "label": "Item J — capital % (ending)",
     "data_type": "decimal", "default_value": "0", "sort_order": 4,
     "notes": "⚠ RECONCILE GAP: tts stores capital_pct but the allocator NEVER uses it (D_K1_CAPPCT). "
              "Reported on item J; not an allocation ratio in the engine."},
    {"fact_key": "k1_profit_pct_boy", "label": "Item J — profit % beginning of year",
     "data_type": "decimal", "required": False, "sort_order": 5},
    {"fact_key": "k1_special_alloc_category", "label": "Special allocation — category (PartnerAllocation)",
     "data_type": "string", "required": False, "sort_order": 6,
     "notes": "If set, the per-category override % replaces profit/loss_pct for that category "
              "(ordinary / lt_capital / etc.). §704(a) agreement; SEE (§704(b)) NOT tested (D_K1_SPECIAL_ALLOC)."},
    {"fact_key": "k1_special_alloc_pct", "label": "Special allocation — override %",
     "data_type": "decimal", "required": False, "sort_order": 7},
    {"fact_key": "k1_gp_services", "label": "Box 4a — guaranteed payments for services (direct)",
     "data_type": "decimal", "default_value": "0", "sort_order": 8,
     "notes": "Per-partner DIRECT (not ratio'd). §707(c)."},
    {"fact_key": "k1_gp_capital", "label": "Box 4b — guaranteed payments for capital (direct)",
     "data_type": "decimal", "default_value": "0", "sort_order": 9,
     "notes": "Per-partner DIRECT. §707(c). SE only if active (1065_SE Decision 4)."},
    {"fact_key": "k1_distributions", "label": "Box 19a — distributions (direct per-partner)",
     "data_type": "decimal", "default_value": "0", "sort_order": 10,
     "notes": "Per-partner DIRECT (partner.distributions). Feeds M-2 line 6 (M-2 leg)."},
    {"fact_key": "k1_se_classification", "label": "SE classification (§1402(a)(13) — from 1065_SE)",
     "data_type": "choice", "default_value": "undetermined", "sort_order": 11,
     "choices": ["active", "passive", "undetermined"],
     "notes": "Box 14a is governed by the 1065_SE spec; carried here as the allocation input."},
    {"fact_key": "k1_is_individual", "label": "Individual partner? (non-individuals: no box 14a)",
     "data_type": "boolean", "default_value": "true", "sort_order": 12},
    # ── Item K — liabilities (§752) ──
    {"fact_key": "k1_liability_recourse", "label": "Item K — recourse liabilities", "data_type": "decimal",
     "default_value": "0", "sort_order": 20, "notes": "§752 — share treated as money contribution/distribution."},
    {"fact_key": "k1_liability_qnr", "label": "Item K — qualified nonrecourse financing", "data_type": "decimal",
     "default_value": "0", "sort_order": 21},
    {"fact_key": "k1_liability_nonrecourse", "label": "Item K — nonrecourse liabilities", "data_type": "decimal",
     "default_value": "0", "sort_order": 22},
    # ── Item L — tax-basis capital (data-entry; roll-forward RED-deferred) ──
    {"fact_key": "k1_cap_boy", "label": "Item L — capital account beginning (tax basis)", "data_type": "decimal",
     "default_value": "0", "sort_order": 30, "notes": "§705/722 transactional. Ties to M-2 line 1 (Σ over partners)."},
    {"fact_key": "k1_cap_contributed", "label": "Item L — capital contributed during year", "data_type": "decimal",
     "default_value": "0", "sort_order": 31},
    {"fact_key": "k1_cap_current_year", "label": "Item L — current-year net income (loss)", "data_type": "decimal",
     "default_value": "0", "sort_order": 32, "notes": "Should = the partner's share of Analysis-of-Net-Income line 1."},
    {"fact_key": "k1_cap_other", "label": "Item L — other increase (decrease)", "data_type": "decimal",
     "default_value": "0", "sort_order": 33},
    {"fact_key": "k1_cap_withdrawals", "label": "Item L — withdrawals and distributions", "data_type": "decimal",
     "default_value": "0", "sort_order": 34},
    {"fact_key": "k1_cap_eoy", "label": "Item L — capital account ending (tax basis)", "data_type": "decimal",
     "sort_order": 35,
     "notes": "OUTPUT (spec): BOY + contributed + current-year + other − withdrawals. ⚠ tts stores this as "
              "data-entry and does NOT compute the roll-forward (D_K1_ITEML) — RED-deferred."},
    # ── Item M / N — §704(c) (structure only; RED-deferred) ──
    {"fact_key": "k1_item_m_builtin", "label": "Item M — contributed built-in-gain/loss property? (Y/N)",
     "data_type": "boolean", "default_value": "false", "sort_order": 40,
     "notes": "If Yes → §704(c) allocation required. NOT modeled by the engine → RED-defer (D_K1_704C)."},
    {"fact_key": "k1_item_n_704c_gain", "label": "Item N — net unrecognized §704(c) gain/(loss) (ending)",
     "data_type": "decimal", "required": False, "sort_order": 41,
     "notes": "§704(c) tracking — data-entry; the reasonable-method allocation math is RED-deferred."},
    {"fact_key": "k1_interest_changed_midyear", "label": "Partner's interest changed mid-year? (§706(d))",
     "data_type": "boolean", "default_value": "false", "sort_order": 42,
     "notes": "If Yes → §706(d) proration/interim-closing required. NOT modeled → RED-defer (D_K1_706D)."},
    # ── Part III box outputs (per-partner allocated) ──
    {"fact_key": "k1_box1_ordinary", "label": "Box 1 — ordinary business income (loss) (allocated)",
     "data_type": "decimal", "sort_order": 50, "notes": "OUTPUT = entity K1 × (profit_pct if ≥0 else loss_pct)."},
    {"fact_key": "k1_box9c_unrecap1250", "label": "Box 9c — unrecaptured §1250 gain (allocated)",
     "data_type": "decimal", "sort_order": 51,
     "notes": "OUTPUT = entity K9c × LT_CAPITAL ratio (profit_pct). CONFIRMED matches k1_allocator; "
              "RECON-9C: Σ partner 9c = entity K9c (closes the open verification)."},
    {"fact_key": "k1_box14a_se", "label": "Box 14a — self-employment earnings (from 1065_SE)",
     "data_type": "decimal", "sort_order": 52, "notes": "OUTPUT — governed by the 1065_SE spec (cross-ref)."},
]

RULES: list[dict] = [
    {"rule_id": "R-K1-ALLOC-PCT", "title": "Per-partner box = entity Sch K line × profit/loss % (override-able)",
     "rule_type": "calculation", "precedence": 1, "sort_order": 1,
     "formula": ("For each allocated Schedule K line, the partner's K-1 box = entity amount × the "
                 "allocation %: profit_pct when the entity amount ≥ 0 (income/gain), loss_pct when < 0 "
                 "(loss). A PartnerAllocation(category, %) row OVERRIDES that ratio for its category "
                 "(§704(a) agreement / special allocation). §704(b): if the agreement is silent or an "
                 "allocation lacks substantial economic effect, allocate by the partner's interest — the "
                 "SEE test itself is RED-deferred (D_K1_SPECIAL_ALLOC). Applies to boxes 1, 2, 3, 5, 6a, "
                 "6b, 7, 8, 9a, 9b, 9c, 10, 11, 12, 13a, 13d, and the coded credit/AMT/tax-exempt lines. "
                 "RECON: Σ per-partner box = entity Schedule K line (RECON-K1-K)."),
     "inputs": ["k1_profit_pct", "k1_loss_pct", "k1_special_alloc_category", "k1_special_alloc_pct"],
     "outputs": ["k1_box1_ordinary"],
     "description": "The core allocation. Matches k1_allocator.get_allocation_pct (profit/loss + override)."},
    {"rule_id": "R-K1-GP-DIRECT", "title": "Boxes 4a/4b/4c guaranteed payments — direct per-partner",
     "rule_type": "calculation", "precedence": 2, "sort_order": 2,
     "formula": ("Boxes 4a (services) = partner.gp_services, 4b (capital) = partner.gp_capital, 4c = 4a + "
                 "4b — assigned DIRECTLY per partner, NOT ratio-allocated (§707(c) payments are "
                 "determined without regard to partnership income). Σ per-partner 4c = entity Sch K line "
                 "4c (INV-GP-DIRECT)."),
     "inputs": ["k1_gp_services", "k1_gp_capital"], "outputs": [],
     "description": "Matches k1_allocator (direct gp_services/gp_capital)."},
    {"rule_id": "R-K1-DIST-DIRECT", "title": "Box 19a distributions — direct per-partner",
     "rule_type": "calculation", "precedence": 3, "sort_order": 3,
     "formula": ("Box 19a = partner.distributions — the actual per-partner distribution, assigned "
                 "DIRECTLY (not a pro-rata split; distributions are the real amounts each partner "
                 "received). Σ per-partner 19a → Schedule M-2 line 6 (M-2 leg)."),
     "inputs": ["k1_distributions"], "outputs": [],
     "description": "Matches k1_allocator (direct partner.distributions)."},
    {"rule_id": "R-K1-9C", "title": "Box 9c unrecaptured §1250 = entity K9c × LT-capital ratio",
     "rule_type": "calculation", "precedence": 4, "sort_order": 4,
     "formula": ("Box 9c = entity Schedule K line 9c × the LT_CAPITAL allocation % (profit_pct, since "
                 "§1250 gain is positive; or a PartnerAllocation 'lt_capital' override). CONFIRMED "
                 "matches k1_allocator (K9c → box 9c, LT_CAPITAL category). RECON-9C: Σ partner box 9c = "
                 "entity K9c — this CLOSES the open box-9c pass-through verification (STATUS Next-up): "
                 "e.g. entity 80,000 at 60/40 → 48,000 / 32,000, summing to 80,000."),
     "inputs": ["k1_box9c_unrecap1250", "k1_profit_pct"], "outputs": ["k1_box9c_unrecap1250"],
     "description": "The box-9c pass-through. Verified against k1_allocator this session."},
    {"rule_id": "R-K1-14A", "title": "Box 14a self-employment = the 1065_SE spec (cross-ref)",
     "rule_type": "routing", "precedence": 5, "sort_order": 5,
     "formula": ("Box 14a (net earnings/loss from self-employment) is governed by the 1065_SE spec "
                 "(the §1402(a)(13) functional-analysis classification over the SE-base worksheet). This "
                 "spec carries it as an output only and does NOT recompute it. Non-individual partners "
                 "get no box 14a (1065_SE R-SE-NONIND). Matches k1_allocator SE-earnings logic."),
     "inputs": ["k1_se_classification", "k1_is_individual"], "outputs": ["k1_box14a_se"],
     "description": "Cross-reference to 1065_SE. No duplication."},
    {"rule_id": "R-K1-CODED", "title": "Coded-box collapse (11/13/15/17/18/19/20) + box 16 K-3 checkbox",
     "rule_type": "routing", "precedence": 6, "sort_order": 6,
     "formula": ("K-1 boxes 1-10 map 1:1 from Schedule K; each Schedule K detail grouping (lines 11, "
                 "13a-e, 14a-c, 15a-f, 17a-f, 18a-c, 19a-b, 20a-c) COLLAPSES into one coded K-1 box "
                 "(11, 13, 14, 15, 17, 18, 19, 20) with a letter code (A-ZZ). Box 16 = Schedule K-3-"
                 "attached checkbox (international RED-deferred, Decision A). LOAD-BEARING codes encoded: "
                 "box 15 AY/AZ (8936) / AB (8835) / W (§45Y) — the S3/S4 pass-through credits; box 20 Z "
                 "(§199A) / AA (§704(c)) / AB (§751) / N,AE,AF (§163(j)) / AJ (§461(l) EBL, partner-level); "
                 "box 13 X (§181) / V (§743(b)); box 11 F (§743(b)). Exhaustive ~200-code enumeration = "
                 "flagged follow-up (Ken walk)."),
     "inputs": [], "outputs": [],
     "description": "i1065sk1 K→K-1 correspondence + code lists. Reconcile target for compute_schedule_k1."},
    {"rule_id": "R-K1-ITEM-K", "title": "Item K — partner's share of liabilities (§752)",
     "rule_type": "classification", "precedence": 7, "sort_order": 7,
     "formula": ("Item K reports the partner's share of partnership liabilities in three buckets — "
                 "recourse, qualified nonrecourse financing, nonrecourse. §752(a)/(b): an increase in a "
                 "partner's liability share is a money contribution (raises outside basis), a decrease is "
                 "a distribution. Data-entry on the Partner model (recourse/qnr/nonrecourse). Explains "
                 "why item-L tax-basis capital 'might not equal' the partner's outside basis (basis "
                 "includes the liability share)."),
     "inputs": ["k1_liability_recourse", "k1_liability_qnr", "k1_liability_nonrecourse"], "outputs": [],
     "description": "§752 item K. Modeled (data-entry) on tts Partner."},
    {"rule_id": "R-K1-ITEM-L", "title": "Item L — tax-basis capital roll-forward (§705; RED-deferred compute)",
     "rule_type": "calculation", "precedence": 8, "sort_order": 8,
     "formula": ("Item L (TAX BASIS): ending = beginning + capital contributed + current-year net income "
                 "(loss) + other increase (decrease) − withdrawals and distributions. Transactional "
                 "approach (§705/722/733): basis up by the income share (incl. tax-exempt), down by "
                 "distributions and the loss/nondeductible share. The current-year net income should = the "
                 "partner's share of Analysis-of-Net-Income line 1 (SCH_K_1065). ⚠ RECONCILE: tts stores "
                 "all item-L fields as DATA-ENTRY and does NOT compute the roll-forward — so Schedule M-2 "
                 "line 1 (Σ beginning capital) cannot auto-derive. RED-DEFERRED (D_K1_ITEML); the compute "
                 "lands with the M-2/L leg."),
     "inputs": ["k1_cap_boy", "k1_cap_contributed", "k1_cap_current_year", "k1_cap_other", "k1_cap_withdrawals"],
     "outputs": ["k1_cap_eoy"],
     "description": "§705 transactional roll-forward. Spec defines it; tts compute is RED-deferred (M-2 leg)."},
    {"rule_id": "R-K1-704C", "title": "Items M/N — §704(c) built-in gain (structure; MATH RED-deferred)",
     "rule_type": "conditional", "precedence": 9, "sort_order": 9,
     "formula": ("Item M: did the partner contribute property with a built-in gain/loss? Item N: net "
                 "unrecognized §704(c) gain/(loss), beginning/ending. §704(c): built-in gain/loss on "
                 "contributed property must be allocated to the CONTRIBUTING partner under a reasonable "
                 "method (traditional / curative / remedial; Reg. 1.704-3). SCOPE (Ken Decision C): "
                 "encode items M/N as facts + gating flag; the special-allocation MATH is RED-DEFERRED — "
                 "tts k1_allocator does NOT model §704(c) (no contributed-property FMV-vs-basis tracking). "
                 "When item M = Yes, D_K1_704C flags that the §704(c) allocation is out of engine scope."),
     "inputs": ["k1_item_m_builtin", "k1_item_n_704c_gain"], "outputs": [],
     "description": "§704(c) items M/N. Structure only (Decision C); engine absent → RED-defer."},
    {"rule_id": "R-K1-706D", "title": "§706(d) varying interest — mid-year change (RED-deferred)",
     "rule_type": "conditional", "precedence": 10, "sort_order": 10,
     "formula": ("If a partner's interest changed during the year, the distributive share must reflect "
                 "the varying interests via the interim-closing-of-the-books method or (by agreement) "
                 "proration (§706(d)(1)). tts k1_allocator applies FULL-YEAR pro-rata only — no proration. "
                 "SCOPE: RED-DEFERRED (D_K1_706D) when k1_interest_changed_midyear = Yes; the mid-year "
                 "split must be handled outside the engine this season."),
     "inputs": ["k1_interest_changed_midyear"], "outputs": [],
     "description": "§706(d)(1). Engine models full-year pro-rata only → RED-defer."},
    {"rule_id": "R-K1-RECON-K", "title": "Allocation sums back to the entity Schedule K", "rule_type": "validation",
     "precedence": 11, "sort_order": 11,
     "formula": ("For every allocated line, Σ over active partners of the per-partner K-1 box = the entity "
                 "Schedule K total (RECON-K1-K). With clean profit/loss %s summing to 100%, the split is "
                 "exact; a PartnerAllocation override set must also sum to 100% per category or the "
                 "reconciliation breaks (D_K1_RECON). Guaranteed payments (4c) and distributions (19a) "
                 "reconcile as the Σ of the direct per-partner amounts."),
     "inputs": ["k1_box1_ordinary"], "outputs": [],
     "description": "The allocation integrity invariant. Backs RECON-K1-K / INV-GP-DIRECT / RECON-9C."},
]

RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-K1-ALLOC-PCT", "IRC_704", "primary", "§704(a) agreement controls the distributive share; §704(b) fallback"),
    ("R-K1-ALLOC-PCT", "IRS_2025_I1065SK1", "secondary", "i1065 allocate proportionately unless specially allocated"),
    ("R-K1-GP-DIRECT", "IRC_707C", "primary", "§707(c) guaranteed payments — per-partner, not income-dependent"),
    ("R-K1-DIST-DIRECT", "IRS_2025_F1065SK1", "primary", "K-1 box 19 distributions (per-partner actual amounts)"),
    ("R-K1-9C", "IRS_2025_F1065SK1", "primary", "K-1 box 9c unrecaptured §1250 gain (LT-capital allocation)"),
    ("R-K1-9C", "IRC_704", "secondary", "§704 allocation by the partner's interest (LT-capital ratio)"),
    ("R-K1-14A", "IRS_2025_F1065SK1", "secondary", "K-1 box 14 self-employment (governed by the 1065_SE spec)"),
    ("R-K1-CODED", "IRS_2025_I1065SK1", "primary", "i1065sk1 coded-box code lists + K→K-1 correspondence"),
    ("R-K1-CODED", "IRS_2025_F1065SK1", "secondary", "K-1 Part III box structure (1-23; box 16 K-3 checkbox)"),
    ("R-K1-ITEM-K", "IRC_752", "primary", "§752(a)/(b) partner's share of liabilities → basis"),
    ("R-K1-ITEM-K", "IRS_2025_F1065SK1", "secondary", "K-1 item K (recourse / qualified nonrecourse / nonrecourse)"),
    ("R-K1-ITEM-L", "IRC_705", "primary", "§705(a) transactional basis roll-forward (item L tax-basis capital)"),
    ("R-K1-ITEM-L", "IRS_2025_F1065SK1", "secondary", "K-1 item L capital account analysis (tax basis)"),
    ("R-K1-704C", "IRC_704", "primary", "§704(c) built-in gain to the contributing partner (items M/N)"),
    ("R-K1-704C", "IRS_2025_F1065SK1", "secondary", "K-1 items M/N (contributed built-in-gain property; §704(c) gain)"),
    ("R-K1-706D", "IRC_706D", "primary", "§706(d)(1) varying-interest determination on a mid-year change"),
    ("R-K1-706D", "IRS_2025_I1065SK1", "secondary", "i1065 interim-closing / proration for mid-year changes"),
    ("R-K1-RECON-K", "IRC_704", "secondary", "§704 — the allocation must sum to the entity distributive total"),
    ("R-K1-RECON-K", "IRS_2025_F1065SK1", "secondary", "K-1 boxes tie to the Schedule K totals"),
]

LINES: list[dict] = [
    # Part II items
    {"line_number": "J", "description": "Partner's share of profit, loss, and capital % (beginning/ending)",
     "line_type": "input", "sort_order": 1, "source_facts": ["k1_profit_pct", "k1_loss_pct", "k1_capital_pct"],
     "source_rules": ["R-K1-ALLOC-PCT"]},
    {"line_number": "K", "description": "Partner's share of liabilities (recourse / qualified nonrecourse / nonrecourse)",
     "line_type": "input", "sort_order": 2,
     "source_facts": ["k1_liability_recourse", "k1_liability_qnr", "k1_liability_nonrecourse"],
     "source_rules": ["R-K1-ITEM-K"]},
    {"line_number": "L", "description": "Partner's capital account analysis (tax basis; BOY + contrib + income + other − withdrawals = EOY)",
     "line_type": "calculated", "sort_order": 3,
     "source_facts": ["k1_cap_boy", "k1_cap_contributed", "k1_cap_current_year", "k1_cap_other", "k1_cap_withdrawals"],
     "source_rules": ["R-K1-ITEM-L"], "notes": "Roll-forward RED-deferred in tts (data-entry); ties to M-2 line 1."},
    {"line_number": "M", "description": "Did the partner contribute built-in-gain/loss property? (Y/N)",
     "line_type": "input", "sort_order": 4, "source_facts": ["k1_item_m_builtin"], "source_rules": ["R-K1-704C"]},
    {"line_number": "N", "description": "Partner's share of net unrecognized §704(c) gain/(loss) (beginning/ending)",
     "line_type": "input", "sort_order": 5, "source_facts": ["k1_item_n_704c_gain"], "source_rules": ["R-K1-704C"]},
    # Part III boxes
    {"line_number": "1", "description": "Ordinary business income (loss) (allocated)", "line_type": "calculated",
     "sort_order": 10, "source_facts": ["k1_box1_ordinary"], "source_rules": ["R-K1-ALLOC-PCT"]},
    {"line_number": "4a", "description": "Guaranteed payments for services (direct)", "line_type": "calculated",
     "sort_order": 11, "source_facts": ["k1_gp_services"], "source_rules": ["R-K1-GP-DIRECT"]},
    {"line_number": "4b", "description": "Guaranteed payments for capital (direct)", "line_type": "calculated",
     "sort_order": 12, "source_facts": ["k1_gp_capital"], "source_rules": ["R-K1-GP-DIRECT"]},
    {"line_number": "4c", "description": "Total guaranteed payments (4a + 4b)", "line_type": "subtotal",
     "sort_order": 13, "source_rules": ["R-K1-GP-DIRECT"]},
    {"line_number": "9c", "description": "Unrecaptured section 1250 gain (allocated, LT-capital ratio)",
     "line_type": "calculated", "sort_order": 14, "source_facts": ["k1_box9c_unrecap1250"], "source_rules": ["R-K1-9C"]},
    {"line_number": "14a", "description": "Self-employment earnings (loss) (from the 1065_SE spec)",
     "line_type": "calculated", "sort_order": 15, "source_facts": ["k1_box14a_se"], "source_rules": ["R-K1-14A"]},
    {"line_number": "15", "description": "Credits (coded; box 15 — S3/S4 pass-through AY/AZ/AB/W)", "line_type": "calculated",
     "sort_order": 16, "source_rules": ["R-K1-ALLOC-PCT", "R-K1-CODED"]},
    {"line_number": "16", "description": "Schedule K-3 is attached (checkbox) — international (RED-defer)",
     "line_type": "input", "sort_order": 17, "source_rules": ["R-K1-CODED"]},
    {"line_number": "19a", "description": "Distributions (direct per-partner)", "line_type": "calculated",
     "sort_order": 18, "source_facts": ["k1_distributions"], "source_rules": ["R-K1-DIST-DIRECT"]},
    {"line_number": "20", "description": "Other information (coded; Z §199A / AA §704(c) / AJ §461(l))",
     "line_type": "input", "sort_order": 19, "source_rules": ["R-K1-CODED"]},
    {"line_number": "22", "description": "More than one activity for at-risk purposes (K-1-only flag)",
     "line_type": "input", "sort_order": 20},
    {"line_number": "23", "description": "More than one activity for passive activity purposes (K-1-only flag)",
     "line_type": "input", "sort_order": 21},
]

DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_K1_RECON", "title": "Allocation break — Σ per-partner box ≠ entity Schedule K line",
     "severity": "error",
     "condition": "sum over partners of an allocated K-1 box != the entity Sch K line for that box",
     "message": ("The per-partner K-1 amounts must sum to the entity Schedule K total for each allocated "
                 "line (RECON-K1-K). A break usually means the profit/loss %s (or a PartnerAllocation "
                 "override for a category) do not sum to 100%. Check that every active partner's shares "
                 "total 100% per category."),
     "notes": "Backs RECON-K1-K. The core allocation-integrity error."},
    {"diagnostic_id": "D_K1_SPECIAL_ALLOC", "title": "Special allocation present — confirm substantial economic effect",
     "severity": "warning",
     "condition": "a PartnerAllocation override (k1_special_alloc_category/pct) is set",
     "message": ("This partner has a special allocation (a category % that differs from the general "
                 "profit/loss %). §704(b) requires the allocation to have substantial economic effect "
                 "(or accord with the partner's interest) — the engine APPLIES the override % but does "
                 "NOT test SEE. Confirm the allocation is supported by the partnership agreement and has "
                 "economic effect (capital-account maintenance, deficit restoration/QIO)."),
     "notes": "§704(b) SEE testing RED-deferred; this surfaces the override for CPA review."},
    {"diagnostic_id": "D_K1_704C", "title": "Contributed built-in-gain property (item M) — §704(c) not modeled",
     "severity": "error",
     "condition": "k1_item_m_builtin is True",
     "message": ("This partner contributed property with a built-in gain/loss (item M = Yes), so §704(c) "
                 "requires the built-in gain/loss to be allocated to this (the contributing) partner under "
                 "a reasonable method (traditional / curative / remedial). The allocation engine does NOT "
                 "model §704(c) (Decision C RED-defer) — compute the §704(c) allocation and item N "
                 "outside the Rule Studio for this filing."),
     "notes": "Decision C RED-defer. Hard flag so the §704(c) scope boundary is explicit."},
    {"diagnostic_id": "D_K1_706D", "title": "Mid-year interest change (§706(d)) — proration not modeled",
     "severity": "error",
     "condition": "k1_interest_changed_midyear is True",
     "message": ("A partner's interest changed during the year, so §706(d) requires the distributive "
                 "share to reflect the varying interests (interim closing of the books or proration). "
                 "The engine allocates FULL-YEAR pro-rata only — the mid-year split is NOT modeled "
                 "(RED-defer). Compute the §706(d) proration outside the engine for this partner."),
     "notes": "§706(d) RED-defer. Engine models full-year pro-rata only."},
    {"diagnostic_id": "D_K1_ITEML", "title": "Item L capital roll-forward does not tie", "severity": "warning",
     "condition": "k1_cap_eoy != k1_cap_boy + k1_cap_contributed + k1_cap_current_year + k1_cap_other - k1_cap_withdrawals",
     "message": ("The item L tax-basis capital account should roll forward: ending = beginning + "
                 "contributed + current-year net income (loss) + other − withdrawals. tts stores these as "
                 "data-entry and does NOT compute the roll-forward, so confirm the ending capital ties "
                 "(and that current-year net income = this partner's share of Analysis-of-Net-Income line "
                 "1). Σ beginning capital over partners feeds Schedule M-2 line 1 (M-2 leg)."),
     "notes": "Item-L roll-forward RED-deferred; ties to M-2 line 1. D-1 reconcile gap."},
    {"diagnostic_id": "D_K1_CAPPCT", "title": "Capital % set but unused by the allocator", "severity": "info",
     "condition": "k1_capital_pct != 0 (reconcile note)",
     "message": ("Item J capital % is reported but the allocation engine does not allocate ANY box by "
                 "capital_pct (it uses profit_pct / loss_pct, and distributions are direct per-partner). "
                 "This is expected — distributions reflect actual per-partner amounts, not a capital-% "
                 "split. Confirm no capital-account-change item is intended to ride capital_pct."),
     "notes": "D-1 reconcile gap (capital_pct defined but unused). Informational."},
    {"diagnostic_id": "D_K1_9C", "title": "Box 9c allocated — confirm Σ = entity K9c", "severity": "info",
     "condition": "k1_box9c_unrecap1250 != 0",
     "message": ("Box 9c (unrecaptured §1250 gain) was allocated by the LT-capital ratio. Confirm the sum "
                 "of every partner's box 9c equals the entity Schedule K line 9c (RECON-9C) — e.g. an "
                 "entity 80,000 at 60/40 gives 48,000 / 32,000 = 80,000. (This is the previously-open "
                 "box-9c pass-through, now verified against k1_allocator.)"),
     "notes": "Closes the STATUS box-9c pass-through verification (code-path confirmed)."},
]

SCENARIOS: list[dict] = [
    {"scenario_name": "K1-1 — ordinary income 60/40 profit split", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"partners": [{"k1_profit_pct": 60, "entity_K1": 100000}, {"k1_profit_pct": 40, "entity_K1": 100000}]},
     "expected_outputs": {"partner_1_box1": 60000, "partner_2_box1": 40000},
     "notes": "Box 1 = 100k × 60% / 40% = 60k / 40k; Σ = 100k (RECON-K1-K)."},
    {"scenario_name": "K1-2 — loss uses loss_pct (differs from profit_pct)", "scenario_type": "edge", "sort_order": 2,
     "inputs": {"k1_profit_pct": 60, "k1_loss_pct": 50, "entity_K1": -20000},
     "expected_outputs": {"k1_box1_ordinary": -10000},
     "notes": "Entity ordinary LOSS 20k → uses loss_pct 50% = (10k), not profit_pct."},
    {"scenario_name": "K1-3 — special allocation override (PartnerAllocation)", "scenario_type": "edge", "sort_order": 3,
     "inputs": {"k1_profit_pct": 50, "k1_special_alloc_category": "lt_capital", "k1_special_alloc_pct": 80,
                "entity_K9a": 10000},
     "expected_outputs": {"partner_box9a": 8000, "D_K1_SPECIAL_ALLOC": True},
     "notes": "LT-capital specially allocated 80% (overrides the 50% profit %): 10k × 80% = 8k; "
              "D_K1_SPECIAL_ALLOC fires (confirm SEE)."},
    {"scenario_name": "K1-4 — guaranteed payments direct (not ratio'd)", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"k1_profit_pct": 25, "k1_gp_services": 60000, "k1_gp_capital": 15000},
     "expected_outputs": {"box_4a": 60000, "box_4b": 15000, "box_4c": 75000},
     "notes": "GP assigned DIRECTLY (60k/15k/75k), NOT × 25%. §707(c)."},
    {"scenario_name": "K1-5 — box 9c pass-through (closes the open verification)", "scenario_type": "edge",
     "sort_order": 5,
     "inputs": {"partners": [{"k1_profit_pct": 60, "entity_K9c": 80000}, {"k1_profit_pct": 40, "entity_K9c": 80000}]},
     "expected_outputs": {"partner_1_box9c": 48000, "partner_2_box9c": 32000, "sum_box9c": 80000},
     "notes": "THE C1 shape: entity K9c 80k at 60/40 → 48k / 32k, Σ = 80k (RECON-9C). Matches k1_allocator "
              "(LT_CAPITAL/profit_pct). Closes the box-9c verification."},
    {"scenario_name": "K1-6 — item M contributed built-in-gain → §704(c) RED-defer", "scenario_type": "edge",
     "sort_order": 6,
     "inputs": {"k1_item_m_builtin": True, "k1_profit_pct": 50, "entity_K1": 100000},
     "expected_outputs": {"k1_box1_ordinary": 50000, "D_K1_704C": True},
     "notes": "Ordinary income still allocates pro-rata (50k); item M → D_K1_704C (§704(c) math out of scope)."},
    {"scenario_name": "K1-7 — mid-year interest change → §706(d) RED-defer", "scenario_type": "edge", "sort_order": 7,
     "inputs": {"k1_interest_changed_midyear": True, "k1_profit_pct": 50, "entity_K1": 100000},
     "expected_outputs": {"k1_box1_ordinary": 50000, "D_K1_706D": True},
     "notes": "Engine allocates full-year pro-rata (50k); D_K1_706D flags the mid-year proration is not modeled."},
    {"scenario_name": "K1-8 — item L roll-forward ties", "scenario_type": "normal", "sort_order": 8,
     "inputs": {"k1_cap_boy": 100000, "k1_cap_contributed": 20000, "k1_cap_current_year": 30000,
                "k1_cap_other": 0, "k1_cap_withdrawals": 15000},
     "expected_outputs": {"k1_cap_eoy": 135000},
     "notes": "EOY = 100k + 20k + 30k − 15k = 135k (§705 transactional). tts stores this data-entry "
              "(roll-forward RED-deferred); the spec asserts the tie."},
]

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "RECON-K1-K", "assertion_type": "reconciliation", "entity_types": ["1065"], "status": "active",
     "title": "Σ per-partner K-1 box = entity Schedule K line (every allocated line)",
     "description": ("For each allocated Schedule K line, the sum over active partners of the per-partner "
                     "K-1 box equals the entity Schedule K total. The allocation must be conservative — "
                     "nothing created or lost in the split. A break fires D_K1_RECON."),
     "definition": {"kind": "reconciliation", "form": "SCHEDULE_K1_1065",
                    "formula": "for each allocated line L: sum(k1_box_L over partners) == SCH_K_1065.line_L",
                    "note": "profit/loss %s (and any category overrides) must sum to 100%"},
     "bug_reference": "", "sort_order": 1},
    {"assertion_id": "RECON-9C", "assertion_type": "reconciliation", "entity_types": ["1065"], "status": "active",
     "title": "Σ per-partner box 9c = entity Schedule K line 9c (the box-9c pass-through)",
     "description": ("The unrecaptured §1250 gain allocation: Σ per-partner K-1 box 9c = entity K9c. "
                     "Closes the previously-open box-9c verification — CONFIRMED against k1_allocator "
                     "(K9c → box 9c via the LT_CAPITAL ratio / profit_pct). e.g. entity 80,000 at 60/40 "
                     "→ 48,000 / 32,000, Σ = 80,000."),
     "definition": {"kind": "reconciliation", "form": "SCHEDULE_K1_1065",
                    "formula": "sum(k1_box9c over partners) == SCH_K_1065.k_9c_unrecap_1250",
                    "note": "the closed box-9c pass-through (tts f23dc54 fed K9c; allocator distributes it)"},
     "bug_reference": "the box-9c pass-through was the STATUS open item; verified this session", "sort_order": 2},
    {"assertion_id": "INV-GP-DIRECT", "assertion_type": "table_invariant", "entity_types": ["1065"], "status": "active",
     "title": "Guaranteed payments are direct per-partner (Σ 4c = entity Sch K 4c)",
     "description": ("Boxes 4a/4b/4c are the partner's actual guaranteed payments (gp_services/gp_capital), "
                     "assigned directly — not a pro-rata split. The Σ of per-partner 4c equals entity "
                     "Schedule K line 4c. Catches a GP being ratio-allocated by mistake."),
     "definition": {"kind": "table_invariant", "form": "SCHEDULE_K1_1065",
                    "invariant": "sum(k1_box4c over partners) == SCH_K_1065.k_4c_gp_total; boxes 4a/4b/4c "
                                 "are direct (not profit/loss %)"},
     "bug_reference": "", "sort_order": 3},
    {"assertion_id": "GATE-704C-706D-DEFER", "assertion_type": "gating_check", "entity_types": ["1065"],
     "status": "active",
     "title": "§704(c) (item M) / §706(d) (mid-year) → RED-defer gate",
     "description": ("Season-one scope gate (Ken Decision C): when item M (contributed built-in-gain "
                     "property) is Yes, D_K1_704C must fire; when a partner's interest changed mid-year, "
                     "D_K1_706D must fire. The engine allocates full-year pro-rata only; the §704(c) and "
                     "§706(d) math is out of scope and handled outside the studio."),
     "definition": {"kind": "gating_check", "form": "SCHEDULE_K1_1065", "expect": {"red_fires": True},
                    "when": "k1_item_m_builtin is True OR k1_interest_changed_midyear is True",
                    "note": "Decision C RED-defer boundary (§704(c) / §706(d))"},
     "bug_reference": "", "sort_order": 4},
]


class Command(BaseCommand):
    help = ("Load the Schedule K-1 (Form 1065) + allocation-engine spec (SCHEDULE_K1_1065). Fresh-authored "
            "from primary IRC (§704/§706(d)/§752/§705/§707(c) verbatim) + the FINAL-2025 f1065sk1/i1065sk1 "
            "structure, reconciled against tts k1_allocator. Refuses until READY_TO_SEED=True (awaits the "
            "Ken walk per D-1).")

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING(
            "\nLoad SCHEDULE_K1_1065 (Schedule K-1 + allocation engine)\n"))
        self._load_topics()
        sources = self._load_sources()
        form = self._upsert_form(FORM_IDENTITY)
        self._upsert_facts(form, FACTS)
        rules = self._upsert_rules(form, RULES)
        self._upsert_authority_links(rules, sources, RULE_LINKS)
        self._upsert_lines(form, LINES)
        self._upsert_diagnostics(form, DIAGNOSTICS)
        self._upsert_tests(form, SCENARIOS)
        self._upsert_form_links(sources)
        self._load_flow_assertions()
        self._report_totals(form)

    def _guard_against_hollow_seed(self):
        empty = []
        for name, seq in (("sources", AUTHORITY_SOURCES), ("facts", FACTS), ("rules", RULES),
                          ("lines", LINES), ("diagnostics", DIAGNOSTICS), ("scenarios", SCENARIOS),
                          ("rule_links", RULE_LINKS), ("flow_assertions", FLOW_ASSERTIONS)):
            if not seq:
                empty.append(f"SCHEDULE_K1_1065.{name}")
        if not READY_TO_SEED or empty:
            still_empty = "\n  ".join(f"- {n}" for n in empty) or "(all populated)"
            raise CommandError(
                "\nREFUSING TO SEED SCHEDULE_K1_1065: not cleared to seed.\n\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True — flip only after the Ken walk, D-1)\n\n"
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
        self.stdout.write(f"Sources ready: {len(sources)}")
        return sources

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

    def _report_totals(self, form):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(f"TaxForms: {TaxForm.objects.count()} | FlowAssertions: {FlowAssertion.objects.count()}")
        uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
        self.stdout.write("SCHEDULE_K1_1065: all rules cited" if not uncited
                          else self.style.WARNING(f"SCHEDULE_K1_1065 uncited rules: {len(uncited)}"))
