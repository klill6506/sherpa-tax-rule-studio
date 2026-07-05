"""Load the Form 5227 spec — Split-Interest Trust Information Return (TY2025).
WO-10, spun off from the 1041 module (S-11). The §664 CRT / §642(c)(5) PIF / §4947(a)(2) family.

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
Form 5227 is the information return for split-interest trusts: charitable remainder
trusts (CRAT §664(d)(1) / CRUT §664(d)(2)), pooled income funds (§642(c)(5)), charitable
lead trusts, and other §4947(a)(2) trusts. It REPLACES Form 1041-A for these trusts. A CRT
is income-tax EXEMPT (§664(c)(1)) and files 5227 as its return (it files Form 1041 only in a
UBTI year). The heart is the §664(b) FOUR-TIER character ordering of the amount distributed to
the income beneficiary — which determines the character (ordinary / capital gain / other /
corpus) the beneficiary reports.

Greenfield: lookup/5227/ → 404 at the 2026-07-05 gap-check.

═══════════════════════════════════════════════════════════════════════════
v1 SCOPE — LOCKED (Ken's Gate-1 walk 2026-07-05; DECISIONS D-11). See f5227_source_brief.md.
═══════════════════════════════════════════════════════════════════════════
COMPUTES (v1) — CRAT + CRUT:
  • Part I income by category (Section A ordinary / B capital gains / C nontaxable / D deductions).
  • The §664(b) FOUR-TIER character ordering of the distribution (TIER-LEVEL, Dec Q2): worst-first —
    (1) ordinary → (2) capital gain → (3) other/tax-exempt → (4) corpus; each tier = current +
    undistributed prior years. Capital gain is ONE class (no within-Tier-2 ST/28%/§1250/regular split).
  • The Part II year-to-year undistributed ACCUMULATION carryforward by category, with the
    CATEGORY-ISOLATION netting (a loss in one category cannot reduce another; carries within-category).
  • §664(c)(2) UBTI EXCISE (Dec Q4): 100% of any UBTI (year-keyed post-2006 — the trust KEEPS its
    exemption and pays a Chapter 42 excise) → route to Form 4720.
STRUCTURE + DIAGNOSTIC (Dec Q1, Q3):
  • Pooled income fund (§642(c)(5)) — statement path, no Form 1041 Sch B; the highest-3-year-rate
    income-interest valuation is noted, not computed — D_5227_PIF.
  • Charitable lead trust — grantor (up-front §170(f)(2)(B) deduction) vs non-grantor (annual §642(c),
    ALSO files Form 1041) routing — D_5227_CLT. Other §4947(a)(2) = catch-all.
  • CRT qualification (5–50% payout / 10% minimum remainder / 5% probability-of-exhaustion) = diagnostics
    with the rule cited; NO §7520 / 2000CM-mortality actuarial compute (established at funding) — Dec Q3.
  • Part VIII §4941/§4943/§4944/§4945 chapter-42 screening → Form 4720 if triggered.

═══════════════════════════════════════════════════════════════════════════
requires_human_review WALK ITEMS (W1-W4)
═══════════════════════════════════════════════════════════════════════════
W1. FOUR-TIER ORDERING — §664(b)(1)-(4) worst-first (ordinary → capital gain → other → corpus),
    each = current + undistributed prior; Reg §1.664-1(d)(1). TIER-LEVEL (capital gain one class). CONFIRM.
W2. CATEGORY-ISOLATION NETTING (i5227 verbatim) — a loss in one of the three categories may not reduce
    another; it reduces prior undistributed gain in the SAME category and carries forward. CONFIRM.
W3. §664(c)(2) UBTI EXCISE = 100% of UBTI, year-keyed POST-2006 (trust keeps exemption; Chapter 42) →
    Form 4720. NOT the pre-2007 total loss of exemption. CONFIRM the year-keying.
W4. QUALIFICATION = DIAGNOSTIC (5–50% / 10% remainder / 5% exhaustion; Rev. Rul. 77-374; Rev. Proc.
    2016-42 safe harbor) — no §7520/mortality compute. STRUCTURE layout = flat Part I–IX + Schedule A
    (the old IV-A/IV-B layout is stale). CONFIRM.

═══════════════════════════════════════════════════════════════════════════
CARRIED [UNVERIFIED] (re-pull verbatim before any deeper compute leg): §1.664-1(d)(1)(iv) netting
clause; §642(c)(2)/(3); §4947(b)(3) 60% threshold; the "CRT files 1041 in a UBTI year" leg. The
Schedule A Part II SNIIC election is PROPOSED reg (§1.1411-3(d)(3)) — not built.
═══════════════════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════════════════
SAFETY GUARD — READY_TO_SEED stays False until Ken approves the review walk (W1-W4).
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
# SAFETY GUARD — flip ONLY after Ken's in-session review walk (W1-W4 above).
#
# FLIPPED 2026-07-05 — Ken APPROVED the review walk in-session ("Approve — flip,
# seed, export"): W1 the tier-level §664(b) four-tier ordering, W2 the category-
# isolation netting, W3 the §664(c)(2) 100% UBTI excise (year-keyed post-2006),
# W4 the qualification diagnostics + flat Part I-IX layout — all blessed. Validated
# on throwaway SQLite (scratchpad/validate_5227.py, 20 pass / 0 fail).
# ═══════════════════════════════════════════════════════════════════════════
READY_TO_SEED = True


FORM_JURISDICTION = "federal"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1041"]  # split-interest trusts (fiduciary family; form_number distinguishes)


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS (cited in f5227_source_brief.md; never memory)
# ═══════════════════════════════════════════════════════════════════════════

UBTI_EXCISE_RATE = "1.00"                       # §664(c)(2) — 100% of UBTI
UBTI_POST2006_YEAR = 2007                       # W3 — post-2006 keeps exemption (pre-2007 lost it)
CRT_PAYOUT_MIN = "0.05"                         # §664(d)(1)(A)/(d)(2)(A) — 5%
CRT_PAYOUT_MAX = "0.50"                         # 50%
CRT_MIN_REMAINDER = "0.10"                      # §664(d)(1)(D)/(d)(2)(D) — 10% (§7520 value)
CRT_EXHAUSTION_MAX = "0.05"                     # Rev. Rul. 77-374 — 5% probability of exhaustion


def _four_tier(dist, avail_ord, avail_cap, avail_nontax):
    """§664(b) worst-first tier ordering. Returns (t1_ord, t2_cap, t3_other, t4_corpus)."""
    d = max(0, dist)
    t1 = min(d, max(0, avail_ord)); d -= t1
    t2 = min(d, max(0, avail_cap)); d -= t2
    t3 = min(d, max(0, avail_nontax)); d -= t3
    t4 = d  # corpus (nontaxable return of principal)
    return t1, t2, t3, t4


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY TOPICS / SOURCES
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("split_interest_trust", "Form 5227 split-interest trusts: §664(b) four-tier distribution character "
     "(ordinary/capgain/other/corpus, worst-first), Part II accumulation + category netting, §664(d) "
     "CRAT/CRUT quals, §664(c)(2) 100% UBTI excise, §642(c)(5) PIF, §4947(a)(2)."),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_F5227",
        "source_type": "federal_form",
        "source_rank": "primary_official",
        "jurisdiction_code": "US",
        "title": "2025 Form 5227 — Split-Interest Trust Information Return",
        "citation": "Form 5227 (2025), Cat. No. 13227T, Created 5/7/25",
        "issuer": "Internal Revenue Service",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f5227.pdf",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.6,
        "topics": ["split_interest_trust"],
        "excerpts": [
            {
                "excerpt_label": "Entity types + part structure (2025 verbatim)",
                "excerpt_text": (
                    "Item C 'Type of Entity': (1) Charitable lead trust; (2) Charitable remainder annuity "
                    "trust (§664(d)(1)); (3) Charitable remainder unitrust (§664(d)(2)); (4) Pooled income "
                    "fund (§642(c)(5)); (5) Other. Parts (flat, 2025): Part I Income and Deductions "
                    "(Section A Ordinary income L1-8, Section B Capital gains L9-13, Section C Nontaxable "
                    "income L14-16, Section D Deductions L17-23 incl. L23 charitable §642(c), Section E "
                    "deductions allocable to categories — §664 trust only); Part II Schedule of "
                    "Distributable Income (§664 trust only); Part III Distributions of Principal for "
                    "Charitable Purposes; Part IV Balance Sheet; Part V CRAT Info; Part VI CRUT Info; Part "
                    "VII Statements Regarding Activities; Part VIII Statements re Activities for Which Form "
                    "4720 May Be Required (L7 UBTI); Part IX Questionnaire (CLT/PIF/CRT). Schedule A (NOT "
                    "open to public inspection): Part I Accumulation Schedule; Part II Simplified NII "
                    "Calculation; Part III Current Distributions Schedule (cols: (d) Ordinary, (e) ST cap "
                    "gain, (f) LT cap gain, (g) Nontaxable, (h) Corpus, (i) total, (j) NII); Part IV Current "
                    "Distributions (CLT/PIF); Part V Assets and Donor Information."
                ),
                "summary_text": "5227 (2025): 5 entity types (CLT/CRAT/CRUT/PIF/other); flat Part I-IX + non-public Schedule A. Four-tier character = Schedule A Part III (ordinary/ST/LT/nontaxable/corpus).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Part VIII L7 UBTI + category-isolation netting (i5227 verbatim)",
                "excerpt_text": (
                    "Part VIII Line 7: 'If a CRT has any unrelated business taxable income (within the "
                    "meaning of section 512...) for 2025, the trust is liable for a tax under section "
                    "664(c)(2), which is treated as a chapter 42 excise tax. The amount of the excise tax is "
                    "equal to the amount of the trust's unrelated business taxable income... answer Yes and "
                    "file Form 4720.' Category isolation (Part II): 'A loss in any one of the three "
                    "categories may not be used to reduce a gain in any other category. For example, a "
                    "capital loss may not be used to reduce ordinary income. However, a loss in any one "
                    "category may be used to reduce undistributed gain for earlier years within that same "
                    "category, and any excess may be carried forward to reduce gain in future years within "
                    "that same category.' Form 5227 replaces Form 1041-A for split-interest trusts. Due "
                    "April 15, 2026; Schedule A is NOT open to public inspection."
                ),
                "summary_text": "§664(c)(2) UBTI = 100% excise → Form 4720 (Part VIII L7). Category isolation: a loss can't cross categories; reduces same-category prior/future gain only. 5227 replaces 1041-A.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_664",
        "source_type": "statute",
        "source_rank": "controlling",
        "jurisdiction_code": "US",
        "title": "IRC §664 — Charitable remainder trusts (tiers, exemption, UBTI excise, CRAT/CRUT quals)",
        "citation": "26 U.S.C. §664(b), (c), (d)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/664",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.5,
        "topics": ["split_interest_trust"],
        "excerpts": [
            {
                "excerpt_label": "§664(b) four tiers; §664(c) exemption + UBTI; §664(d) quals (verbatim)",
                "excerpt_text": (
                    "§664(b): amounts distributed by a CRAT or CRUT have the characteristics, in order: "
                    "(1) ordinary income to the extent of the trust's such income for the year AND its "
                    "undistributed such income for prior years; (2) capital gain to the extent of the "
                    "capital gain of the trust for the year and the undistributed capital gain for prior "
                    "years; (3) other income (e.g., tax-exempt) current + undistributed prior; (4) "
                    "distribution of trust corpus. §664(c)(1): a CRAT/CRUT is 'not subject to any tax "
                    "imposed by this subtitle' for any taxable year. §664(c)(2)(A): if it has UBTI (§512) "
                    "there is an excise tax 'equal to the amount of such unrelated business taxable income' "
                    "(effective years beginning after Dec. 31, 2006; treated as a chapter 42 tax). §664(d)(1) "
                    "CRAT: a sum certain not less than 5% nor more than 50% of the initial net FMV, paid at "
                    "least annually; §664(d)(1)(D) the §7520 value of the remainder is at least 10% of "
                    "initial net FMV. §664(d)(2) CRUT: a fixed percentage (5%-50%) of net FMV valued "
                    "annually; §664(d)(2)(D) 10% minimum remainder per contribution. §664(d)(3): net-income "
                    "(NICRUT) and net-income-with-makeup (NIMCRUT) variants."
                ),
                "summary_text": "§664(b) tiers ordinary→capgain→other→corpus (current+undistributed prior). §664(c)(1) exempt; §664(c)(2) 100% UBTI excise (post-2006). §664(d) CRAT/CRUT 5-50% payout, 10% remainder.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "REG_1_664_1D",
        "source_type": "regulation",
        "source_rank": "controlling",
        "jurisdiction_code": "US",
        "title": "Treas. Reg. §1.664-1(d)(1) — Character of CRT distributions (category/class ordering)",
        "citation": "26 CFR §1.664-1(d)(1)",
        "issuer": "U.S. Department of the Treasury",
        "official_url": "https://www.law.cornell.edu/cfr/text/26/1.664-1",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.3,
        "topics": ["split_interest_trust"],
        "excerpts": [
            {
                "excerpt_label": "Category/class ordering (verbatim)",
                "excerpt_text": (
                    "Three categories: ordinary income; capital gains; other income. §1.664-1(d)(1)(ii)(a): "
                    "the character of the distribution is determined by treating it as made from each "
                    "category in the following order: (1) first, from ordinary income; (2) second, from "
                    "capital gain; (3) third, from other income; (4) finally, from trust corpus. Within a "
                    "category, distributions are treated as made from each class, in turn, until exhaustion "
                    "of the class, BEGINNING WITH THE CLASS SUBJECT TO THE HIGHEST FEDERAL INCOME TAX RATE "
                    "and ending with the lowest. [v1 = TIER-LEVEL: capital gain treated as one class; the "
                    "within-Tier-2 ST/28%/§1250/regular rate-group split is deferred (D-11 Q2). Order by "
                    "rate, never hardcode the numeric rates.]"
                ),
                "summary_text": "Reg §1.664-1(d)(1): distribute ordinary→capgain→other→corpus; within a category, highest-rate class first. v1 = tier-level (capgain one class).",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_642C_4947",
        "source_type": "statute",
        "source_rank": "controlling",
        "jurisdiction_code": "US",
        "title": "IRC §642(c) / §642(c)(5) / §4947(a)(2) — PIF, charitable deduction, split-interest excise regime",
        "citation": "26 U.S.C. §642(c), §642(c)(5); §4947(a)(2), (b)(3); §170(f)(2)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/4947",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.3,
        "topics": ["split_interest_trust"],
        "excerpts": [
            {
                "excerpt_label": "PIF / CLT / §4947(a)(2) excise regime (verbatim substance)",
                "excerpt_text": (
                    "§642(c)(5) pooled income fund: donors transfer an irrevocable remainder to a public "
                    "charity and retain a life income interest; commingled; maintained by the charity; the "
                    "income interest is valued using 'the highest rate of return earned by the fund for any "
                    "of the 3 taxable years immediately preceding.' §642(c)(1): deduction for gross income "
                    "PAID pursuant to the governing instrument for a §170(c) purpose; §642(c)(2) 'permanently "
                    "set aside' (estates + grandfathered trusts). §170(f)(2)(B): a charitable lead trust "
                    "grantor deduction requires a guaranteed-annuity or fixed-percentage (unitrust) lead "
                    "interest with the grantor treated as owner under §671. §4947(a)(2): a split-interest "
                    "trust is treated as a private foundation for §4941 (self-dealing), §4943 (excess "
                    "business holdings), §4944 (jeopardy investments), §4945 (taxable expenditures) — NOT "
                    "§4940; §4947(b)(3) carves §4943/§4944 for certain all-income-charitable trusts."
                ),
                "summary_text": "§642(c)(5) PIF (highest-3-yr-rate valuation, charity-maintained); §642(c) deduction paid vs set-aside; §170(f)(2)(B) grantor CLT; §4947(a)(2) applies §4941/4943/4944/4945 (not 4940).",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_I5227",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "US",
        "title": "2025 Instructions for Form 5227",
        "citation": "Instructions for Form 5227 (2025), Cat. No. 13228E, dated Dec 3, 2025",
        "issuer": "Internal Revenue Service",
        "official_url": "https://www.irs.gov/instructions/i5227",
        "current_status": "active",
        "is_substantive_authority": True,
        "trust_score": 9.6,
        "topics": ["split_interest_trust"],
        "excerpts": [
            {
                "excerpt_label": "Who must file + qualification tests (i5227 verbatim substance)",
                "excerpt_text": (
                    "'All CRTs described in section 664 must file Form 5227. All pooled income funds "
                    "described in section 642(c)(5) and all other trusts such as charitable lead trusts that "
                    "meet the definition of a split-interest trust under section 4947(a)(2) must file Form "
                    "5227.' A CRAT annuity / CRUT unitrust must be 5%-50%; the §7520 remainder must be at "
                    "least 10%; a lifetime CRAT must satisfy the 5% probability-of-exhaustion test (Rev. Rul. "
                    "77-374), with the Rev. Proc. 2016-42 sample early-termination provision as a safe harbor "
                    "(exempts the POE test). SNIIC (Schedule A Part II) is available under PROPOSED "
                    "Regulations §1.1411-3(d)(3). A PIF does not complete Form 1041 Schedule A or B (attach a "
                    "statement); it files Form 5227."
                ),
                "summary_text": "All CRTs/PIFs/CLTs/§4947(a)(2) file 5227. CRAT/CRUT: 5-50% payout, 10% remainder, CRAT 5% exhaustion (Rev Rul 77-374 / Rev Proc 2016-42 safe harbor). SNIIC = proposed reg.",
                "is_key_excerpt": True,
            },
        ],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_F5227", "5227", "governs"),
    ("IRS_2025_I5227", "5227", "governs"),
    ("IRC_664", "5227", "governs"),
    ("REG_1_664_1D", "5227", "governs"),
    ("IRC_642C_4947", "5227", "governs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM — Form 5227
# ═══════════════════════════════════════════════════════════════════════════

F5227_FACTS: list[dict] = [
    {"fact_key": "entity_type", "label": "Type of entity (Form 5227 Item C)", "data_type": "choice", "required": True, "sort_order": 1,
     "choices": ["crat", "crut", "pif", "clt_grantor", "clt_nongrantor", "other_4947"],
     "notes": "Dec Q1. CRAT/CRUT compute the §664(b) tier engine; PIF/CLT/other = structure + diagnostics."},
    # Part I Section A ordinary income
    {"fact_key": "ordinary_interest", "label": "Interest income (Part I §A L1)", "data_type": "decimal", "required": False, "sort_order": 10},
    {"fact_key": "ordinary_dividends", "label": "Ordinary dividends (Part I §A L2a)", "data_type": "decimal", "required": False, "sort_order": 11},
    {"fact_key": "ordinary_business", "label": "Business/rents/royalties/farm/other ordinary income (Part I §A L3-7)", "data_type": "decimal", "required": False, "sort_order": 12},
    # Part I Section B capital gains (tier-level: captured but treated as ONE class)
    {"fact_key": "capgain_short_term", "label": "Net short-term capital gain/(loss) (Part I §B L9)", "data_type": "decimal", "required": False, "sort_order": 20},
    {"fact_key": "capgain_long_term", "label": "Net long-term capital gain/(loss) — incl. §1250/28% (Part I §B L10-12)", "data_type": "decimal", "required": False, "sort_order": 21,
     "notes": "Dec Q2 = tier-level: the ST/28%/§1250/regular within-Tier-2 split is deferred; captured as one capital-gain class."},
    # Part I Section C nontaxable
    {"fact_key": "nontaxable_tax_exempt", "label": "Tax-exempt interest + other nontaxable income (Part I §C L14-15)", "data_type": "decimal", "required": False, "sort_order": 30},
    # Part I Section D deductions
    {"fact_key": "deductions_total", "label": "Total deductions — interest/taxes/trustee/attorney/other (Part I §D L17-22)", "data_type": "decimal", "required": False, "sort_order": 40},
    {"fact_key": "charitable_642c", "label": "Charitable deduction under §642(c) (Part I §D L23)", "data_type": "decimal", "required": False, "sort_order": 41,
     "notes": "PIF/CLT §642(c) deduction (paid, or set-aside for estates/grandfathered). Structure for PIF/CLT."},
    # Part II accumulation (undistributed prior-year by category)
    {"fact_key": "undist_ordinary_prior", "label": "Undistributed ordinary income — prior years (Part II)", "data_type": "decimal", "required": False, "sort_order": 50,
     "notes": "Dec Q2. Carried forward; tier 1 = current ordinary + this."},
    {"fact_key": "undist_capgain_prior", "label": "Undistributed capital gain — prior years (Part II)", "data_type": "decimal", "required": False, "sort_order": 51},
    {"fact_key": "undist_nontaxable_prior", "label": "Undistributed nontaxable/other income — prior years (Part II)", "data_type": "decimal", "required": False, "sort_order": 52},
    # Distribution
    {"fact_key": "distribution_amount", "label": "Amount distributed to the income beneficiary (annuity/unitrust)", "data_type": "decimal", "required": False, "sort_order": 60,
     "notes": "The §664(b) four-tier ordering assigns character to this amount."},
    # CRT qualification (diagnostic inputs, Dec Q3)
    {"fact_key": "payout_rate", "label": "Annuity/unitrust payout rate (fraction, e.g. 0.05)", "data_type": "decimal", "required": False, "sort_order": 70,
     "notes": "Dec Q3 diagnostic. Must be 5%-50% (§664(d)). No compute — flagged."},
    {"fact_key": "remainder_pct_7520", "label": "§7520 remainder value as % of contribution (fraction)", "data_type": "decimal", "required": False, "sort_order": 71,
     "notes": "Dec Q3 diagnostic. Must be >= 10% (§664(d)(1)(D)/(d)(2)(D)). Established at funding — no §7520 compute."},
    {"fact_key": "exhaustion_probability", "label": "CRAT 5% probability-of-exhaustion result (fraction)", "data_type": "decimal", "required": False, "sort_order": 72,
     "notes": "Dec Q3 diagnostic. Must be <= 5% (Rev. Rul. 77-374) unless the Rev. Proc. 2016-42 safe harbor applies."},
    {"fact_key": "rp2016_42_safe_harbor", "label": "Rev. Proc. 2016-42 early-termination safe harbor adopted?", "data_type": "boolean", "required": False, "sort_order": 73},
    # UBTI + §4947 screening (Dec Q4)
    {"fact_key": "ubti_amount", "label": "Unrelated business taxable income (§512) for the year", "data_type": "decimal", "required": False, "sort_order": 80,
     "notes": "Dec Q4. §664(c)(2) 100% excise on any UBTI → Form 4720."},
    {"fact_key": "has_self_dealing_4941", "label": "§4941 self-dealing during the year? (Part VIII)", "data_type": "boolean", "required": False, "sort_order": 81},
    {"fact_key": "has_excess_holdings_4943", "label": "§4943 excess business holdings? (Part VIII)", "data_type": "boolean", "required": False, "sort_order": 82},
    {"fact_key": "has_jeopardy_4944", "label": "§4944 jeopardizing investments? (Part VIII)", "data_type": "boolean", "required": False, "sort_order": 83},
    {"fact_key": "has_taxable_expenditure_4945", "label": "§4945 taxable expenditures? (Part VIII)", "data_type": "boolean", "required": False, "sort_order": 84},
    # PIF structure
    {"fact_key": "pif_highest_3yr_rate", "label": "PIF highest rate of return — prior 3 years (§642(c)(5), structure)", "data_type": "decimal", "required": False, "sort_order": 90,
     "notes": "PIF income-interest valuation input; structure/diagnostic only (D_5227_PIF)."},
]

F5227_RULES: list[dict] = [
    {"rule_id": "R-5227-ORDINC", "title": "Total ordinary income (Part I Section A)", "rule_type": "calculation",
     "formula": "ordinary_income = ordinary_interest + ordinary_dividends + ordinary_business",
     "inputs": ["ordinary_interest", "ordinary_dividends", "ordinary_business"], "outputs": ["ordinary_income"], "sort_order": 1,
     "description": "Part I §A Line 8 total ordinary income (Tier 1 source)."},
    {"rule_id": "R-5227-CAPGAIN", "title": "Total capital gain (Part I Section B)", "rule_type": "calculation",
     "formula": "capital_gain = capgain_short_term + capgain_long_term  (tier-level: ONE class, Dec Q2)",
     "inputs": ["capgain_short_term", "capgain_long_term"], "outputs": ["capital_gain"], "sort_order": 2,
     "description": "Part I §B Line 13 total capital gain (Tier 2 source). v1 does NOT split into ST/28%/§1250/regular rate groups."},
    {"rule_id": "R-5227-TIERS", "title": "§664(b) four-tier character ordering (worst-first)", "rule_type": "calculation",
     "formula": ("avail_ord = ordinary_income + undist_ordinary_prior ; avail_cap = capital_gain + undist_capgain_prior ; "
                 "avail_nontax = nontaxable_tax_exempt + undist_nontaxable_prior ; "
                 "t1_ordinary = min(distribution_amount, avail_ord) ; rem = distribution_amount - t1_ordinary ; "
                 "t2_capgain = min(rem, avail_cap) ; rem -= t2_capgain ; "
                 "t3_other = min(rem, avail_nontax) ; rem -= t3_other ; t4_corpus = rem"),
     "inputs": ["distribution_amount", "ordinary_income", "undist_ordinary_prior", "capital_gain",
                "undist_capgain_prior", "nontaxable_tax_exempt", "undist_nontaxable_prior"],
     "outputs": ["t1_ordinary", "t2_capgain", "t3_other", "t4_corpus"], "sort_order": 3,
     "description": "W1. §664(b)(1)-(4) / Reg §1.664-1(d)(1). The distribution carries out ordinary first (current + undistributed prior), then capital gain, then other/tax-exempt, then corpus (nontaxable). CRAT/CRUT only."},
    {"rule_id": "R-5227-ACCUM", "title": "Part II accumulation carryforward (category-isolation)", "rule_type": "calculation",
     "formula": ("carry_ordinary = max(0, avail_ord - t1_ordinary) ; carry_capgain = max(0, avail_cap - t2_capgain) ; "
                 "carry_nontax = max(0, avail_nontax - t3_other)  [each category carries forward independently; "
                 "a loss in one category reduces only prior/future gain in that SAME category, never another]"),
     "inputs": [], "outputs": ["carry_ordinary", "carry_capgain", "carry_nontax"], "sort_order": 4,
     "description": "W2. i5227 category-isolation: 'A loss in any one of the three categories may not be used to reduce a gain in any other category... may be used to reduce undistributed gain for earlier years within that same category... carried forward.'"},
    {"rule_id": "R-5227-UBTI", "title": "§664(c)(2) UBTI excise — 100% (Part VIII L7 → Form 4720)", "rule_type": "calculation",
     "formula": "if ubti_amount > 0 and tax_year >= 2007: ubti_excise = ubti_amount * 1.00 -> Form 4720 (trust KEEPS its §664(c)(1) exemption)",
     "inputs": ["ubti_amount"], "outputs": ["ubti_excise"], "sort_order": 5,
     "description": "W3. §664(c)(2)(A). A CRT with any UBTI (§512) owes an excise tax equal to 100% of the UBTI, treated as a chapter 42 tax (effective post-2006 — the trust keeps its exemption; pre-2007 it lost the exemption entirely). Reported Part VIII L7 = Yes; file Form 4720."},
    {"rule_id": "R-5227-4947", "title": "§4947 chapter-42 screening (Part VIII → Form 4720)", "rule_type": "routing",
     "formula": "if any(has_self_dealing_4941, has_excess_holdings_4943, has_jeopardy_4944, has_taxable_expenditure_4945): file Form 4720",
     "inputs": ["has_self_dealing_4941", "has_excess_holdings_4943", "has_jeopardy_4944", "has_taxable_expenditure_4945"],
     "outputs": ["file_4720"], "sort_order": 6,
     "description": "Dec Q4. §4947(a)(2) treats the split-interest trust as a private foundation for §4941/§4943/§4944/§4945 (NOT §4940). Part VIII screens these; Form 4720 computes any tax."},
    {"rule_id": "R-5227-QUAL", "title": "CRT qualification checks (diagnostic)", "rule_type": "validation",
     "formula": ("payout_ok = 0.05 <= payout_rate <= 0.50 ; remainder_ok = remainder_pct_7520 >= 0.10 ; "
                 "exhaustion_ok = (entity_type != crat) or rp2016_42_safe_harbor or exhaustion_probability <= 0.05"),
     "inputs": ["payout_rate", "remainder_pct_7520", "exhaustion_probability", "rp2016_42_safe_harbor", "entity_type"],
     "outputs": [], "sort_order": 7,
     "description": "W4 / Dec Q3. §664(d): 5%-50% payout, 10% §7520 remainder; CRAT 5% probability-of-exhaustion (Rev. Rul. 77-374; Rev. Proc. 2016-42 safe harbor). DIAGNOSTIC ONLY — established at funding; no §7520/2000CM compute."},
    {"rule_id": "R-5227-642C", "title": "§642(c) charitable deduction (Part I L23) — PIF/CLT structure", "rule_type": "calculation",
     "formula": "charitable_642c = amount PAID (or permanently set aside for estates/grandfathered) per the governing instrument for a §170(c) purpose",
     "inputs": ["charitable_642c"], "outputs": ["Part1_L23"], "sort_order": 8,
     "description": "§642(c)(1) paid / §642(c)(2) set-aside. Direct-entry; PIF and non-grantor CLT use this. Governing-instrument requirement; from gross income."},
]

F5227_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-5227-ORDINC", "IRS_2025_F5227", "primary", "Part I Section A ordinary income"),
    ("R-5227-CAPGAIN", "IRS_2025_F5227", "primary", "Part I Section B capital gains"),
    ("R-5227-TIERS", "IRC_664", "primary", "§664(b)(1)-(4) four-tier ordering"),
    ("R-5227-TIERS", "REG_1_664_1D", "secondary", "Reg §1.664-1(d)(1) category ordering"),
    ("R-5227-ACCUM", "IRS_2025_F5227", "primary", "Part II category-isolation netting (i5227)"),
    ("R-5227-ACCUM", "REG_1_664_1D", "secondary", "cumulative-net-basis within category"),
    ("R-5227-UBTI", "IRC_664", "primary", "§664(c)(2) 100% UBTI excise (post-2006)"),
    ("R-5227-UBTI", "IRS_2025_F5227", "secondary", "Part VIII L7 → Form 4720"),
    ("R-5227-4947", "IRC_642C_4947", "primary", "§4947(a)(2) PF excise regime §4941/4943/4944/4945"),
    ("R-5227-4947", "IRS_2025_F5227", "secondary", "Part VIII screening"),
    ("R-5227-QUAL", "IRC_664", "primary", "§664(d) 5-50% payout / 10% remainder"),
    ("R-5227-QUAL", "IRS_2025_I5227", "secondary", "Rev. Rul. 77-374 / Rev. Proc. 2016-42 safe harbor"),
    ("R-5227-642C", "IRC_642C_4947", "primary", "§642(c) charitable deduction (paid / set-aside)"),
]

F5227_LINES: list[dict] = [
    {"line_number": "I-8", "description": "Part I §A L8 Total ordinary income", "line_type": "subtotal", "source_rules": ["R-5227-ORDINC"], "sort_order": 1},
    {"line_number": "I-13", "description": "Part I §B L13 Total capital gains (tier-level, one class)", "line_type": "subtotal", "source_rules": ["R-5227-CAPGAIN"], "sort_order": 2},
    {"line_number": "I-16", "description": "Part I §C L16 Total nontaxable income", "line_type": "input", "source_facts": ["nontaxable_tax_exempt"], "sort_order": 3},
    {"line_number": "I-23", "description": "Part I §D L23 Charitable deduction (§642(c))", "line_type": "input", "source_facts": ["charitable_642c"], "sort_order": 4},
    {"line_number": "II-ord", "description": "Part II undistributed ordinary income (accumulation)", "line_type": "calculated", "source_rules": ["R-5227-ACCUM"], "sort_order": 5},
    {"line_number": "II-cap", "description": "Part II undistributed capital gain (accumulation)", "line_type": "calculated", "source_rules": ["R-5227-ACCUM"], "sort_order": 6},
    {"line_number": "II-nontax", "description": "Part II undistributed nontaxable income (accumulation)", "line_type": "calculated", "source_rules": ["R-5227-ACCUM"], "sort_order": 7},
    {"line_number": "SchA-III-d", "description": "Sch A Part III col (d) Ordinary income distributed (Tier 1)", "line_type": "calculated", "source_rules": ["R-5227-TIERS"], "sort_order": 8},
    {"line_number": "SchA-III-ef", "description": "Sch A Part III col (e)/(f) Capital gain distributed (Tier 2)", "line_type": "calculated", "source_rules": ["R-5227-TIERS"], "sort_order": 9},
    {"line_number": "SchA-III-g", "description": "Sch A Part III col (g) Nontaxable distributed (Tier 3)", "line_type": "calculated", "source_rules": ["R-5227-TIERS"], "sort_order": 10},
    {"line_number": "SchA-III-h", "description": "Sch A Part III col (h) Corpus distributed (Tier 4)", "line_type": "calculated", "source_rules": ["R-5227-TIERS"], "sort_order": 11},
    {"line_number": "VIII-7", "description": "Part VIII L7 UBTI → §664(c)(2) excise / Form 4720", "line_type": "calculated", "source_rules": ["R-5227-UBTI"], "sort_order": 12},
]

F5227_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_5227_TIERS", "title": "CRT distribution character is worst-first (§664(b) four tiers)", "severity": "info",
     "condition": "entity_type in (crat, crut) and distribution_amount > 0",
     "message": "The amount distributed carries out character in this order: (1) ordinary income, (2) capital gain, (3) other/tax-exempt income, (4) corpus — each to the extent of the current year PLUS undistributed prior-year amounts of that character. The beneficiary reports the resulting character mix. (v1 is tier-level: capital gain is one class; the ST/28%/§1250/regular within-Tier-2 detail is preparer-entered.)",
     "notes": "W1. Dec Q2."},
    {"diagnostic_id": "D_5227_NETTING", "title": "Category isolation — a loss cannot cross categories", "severity": "warning",
     "condition": "a category (ordinary / capital gain / nontaxable) is a net loss",
     "message": "A loss in any one of the three categories may NOT reduce a gain in another category (e.g., a capital loss cannot reduce ordinary income). It reduces undistributed gain for earlier years within the SAME category, with any excess carried forward within that category.",
     "notes": "W2. i5227 verbatim."},
    {"diagnostic_id": "D_5227_UBTI", "title": "§664(c)(2) — any UBTI triggers a 100% excise tax (Form 4720)", "severity": "error",
     "condition": "ubti_amount > 0",
     "message": "This CRT has unrelated business taxable income. Under §664(c)(2), the trust owes an excise tax equal to 100% of the UBTI (a chapter 42 tax) — the trust KEEPS its income-tax exemption (post-2006 rule), but must answer 'Yes' on Part VIII line 7 and file Form 4720 to report and pay the excise.",
     "notes": "W3. Dec Q4. Year-keyed post-2006."},
    {"diagnostic_id": "D_5227_4947", "title": "§4947 chapter-42 activity — file Form 4720", "severity": "warning",
     "condition": "any of §4941/§4943/§4944/§4945 activity present",
     "message": "As a §4947(a)(2) split-interest trust, this trust is treated as a private foundation for self-dealing (§4941), excess business holdings (§4943), jeopardizing investments (§4944), and taxable expenditures (§4945) — NOT the §4940 net-investment-income tax. Part VIII screens these; file Form 4720 to compute any excise tax.",
     "notes": "Dec Q4."},
    {"diagnostic_id": "D_5227_QUAL_PAY", "title": "CRT payout must be 5%–50% (§664(d))", "severity": "warning",
     "condition": "entity_type in (crat, crut) and (payout_rate < 0.05 or payout_rate > 0.50)",
     "message": "A CRAT annuity or CRUT unitrust amount must be at least 5% and not more than 50% of the initial (CRAT) or annually-valued (CRUT) net fair market value. A payout outside this range disqualifies the trust. (Established at funding — verify the trust instrument.)",
     "notes": "W4. Dec Q3 diagnostic."},
    {"diagnostic_id": "D_5227_QUAL_REM", "title": "CRT 10% minimum remainder (§7520)", "severity": "warning",
     "condition": "entity_type in (crat, crut) and remainder_pct_7520 < 0.10",
     "message": "The §7520 value of the charitable remainder must be at least 10% of the initial net FMV (CRAT) or of each contribution (CRUT). Below 10% the trust is not a qualified CRT. This is established at funding using the §7520 rate — not recomputed on the annual return.",
     "notes": "W4. Dec Q3 diagnostic."},
    {"diagnostic_id": "D_5227_QUAL_EXH", "title": "CRAT 5% probability-of-exhaustion test", "severity": "info",
     "condition": "entity_type == crat and not rp2016_42_safe_harbor and exhaustion_probability > 0.05",
     "message": "A lifetime CRAT must have no more than a 5% probability that the corpus is exhausted before the measuring life ends (Rev. Rul. 77-374, using the §7520 rate + the 2000CM mortality table). The Rev. Proc. 2016-42 sample early-termination provision is a safe harbor that exempts the trust from this test. Verify at funding; not computed here.",
     "notes": "W4. Dec Q3 diagnostic."},
    {"diagnostic_id": "D_5227_EXEMPT", "title": "A CRT is income-tax exempt — files 5227, not 1041 (except a UBTI year)", "severity": "info",
     "condition": "entity_type in (crat, crut)",
     "message": "Under §664(c)(1) a charitable remainder trust is exempt from income tax and files Form 5227 as its return (not Form 1041). It files Form 1041 only for a year in which it has UBTI. Form 5227 replaces Form 1041-A for split-interest trusts.",
     "notes": "§664(c)(1). UBTI-year 1041 leg is [UNVERIFIED] — confirm before encoding a both-returns rule."},
    {"diagnostic_id": "D_5227_PIF", "title": "Pooled income fund — statement path, no Form 1041 Sch B (structure)", "severity": "info",
     "condition": "entity_type == pif",
     "message": "A pooled income fund (§642(c)(5)) does NOT complete Form 1041 Schedule A or B — attach a statement (rate-of-return, distribution deduction, charitable deduction) and file Form 5227. The income interest is valued using the highest rate of return of the prior 3 years. v1 models the structure; the §642(c)(5)/(3) valuation is not computed (D-11 Q1).",
     "notes": "Dec Q1 structure."},
    {"diagnostic_id": "D_5227_CLT", "title": "Charitable lead trust — grantor vs non-grantor routing (structure)", "severity": "info",
     "condition": "entity_type in (clt_grantor, clt_nongrantor)",
     "message": "A grantor CLT gives the grantor an up-front §170(f)(2)(B) charitable deduction (guaranteed-annuity/unitrust lead interest; grantor is a §671 owner, so trust income is taxed back to the grantor). A non-grantor CLT takes an annual §642(c) deduction for amounts paid to charity and ALSO files Form 1041 as a complex trust. Neither files Form 1041-A. v1 models the routing (D-11 Q1).",
     "notes": "Dec Q1 structure."},
    {"diagnostic_id": "D_5227_SNIIC", "title": "SNIIC election is proposed reg only — not computed", "severity": "info",
     "condition": "the Simplified Net Investment Income Calculation (Schedule A Part II) is considered",
     "message": "The Simplified Net Investment Income Calculation (Schedule A Part II) is available only under PROPOSED Regulations §1.1411-3(d)(3). It is not built in v1 — do not rely on a computed SNIIC amount until the regulation is finalized.",
     "notes": "Proposed reg. Deferred."},
]

F5227_SCENARIOS: list[dict] = [
    {"scenario_name": "5227-T1 — CRUT distribution: ordinary first, then capital gain", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"entity_type": "crut", "ordinary_interest": 10000, "capgain_long_term": 20000, "distribution_amount": 25000},
     "expected_outputs": {"t1_ordinary": 10000, "t2_capgain": 15000, "t3_other": 0, "t4_corpus": 0, "carry_capgain": 5000},
     "notes": "§664(b): distribution 25,000 carries out ordinary 10,000 first, then 15,000 of the 20,000 capital gain; 5,000 capital gain accumulates (carryforward). Beneficiary reports 10,000 ordinary + 15,000 capital gain."},
    {"scenario_name": "5227-T2 — distribution reaches corpus (Tier 4)", "scenario_type": "edge", "sort_order": 2,
     "inputs": {"entity_type": "crat", "ordinary_interest": 5000, "capgain_long_term": 3000, "distribution_amount": 12000},
     "expected_outputs": {"t1_ordinary": 5000, "t2_capgain": 3000, "t3_other": 0, "t4_corpus": 4000},
     "notes": "5,000 ordinary + 3,000 capital gain exhaust income; the remaining 4,000 is a nontaxable distribution of corpus (Tier 4)."},
    {"scenario_name": "5227-T3 — accumulation: undistributed prior-year ordinary carries into Tier 1", "scenario_type": "edge", "sort_order": 3,
     "inputs": {"entity_type": "crut", "undist_ordinary_prior": 8000, "ordinary_interest": 4000, "distribution_amount": 10000},
     "expected_outputs": {"t1_ordinary": 10000, "carry_ordinary": 2000},
     "notes": "Tier 1 available = current 4,000 + undistributed prior 8,000 = 12,000; distribution 10,000 all ordinary; 2,000 ordinary carries forward. Prior undistributed income is distributed before corpus."},
    {"scenario_name": "5227-T4 — UBTI triggers the 100% excise (Form 4720)", "scenario_type": "failure", "sort_order": 4,
     "inputs": {"entity_type": "crut", "ubti_amount": 5000},
     "expected_outputs": {"ubti_excise": 5000, "diagnostic": "D_5227_UBTI"},
     "notes": "§664(c)(2): excise = 100% of UBTI 5,000 = 5,000 → Part VIII L7 Yes → Form 4720. The trust keeps its §664(c)(1) exemption (post-2006)."},
    {"scenario_name": "5227-T5 — payout out of range (3%) → qualification diagnostic", "scenario_type": "failure", "sort_order": 5,
     "inputs": {"entity_type": "crat", "payout_rate": 0.03},
     "expected_outputs": {"diagnostic": "D_5227_QUAL_PAY"},
     "notes": "A 3% payout is below the §664(d) 5% minimum → D_5227_QUAL_PAY (disqualifying; verify the instrument). Diagnostic only — no compute."},
    {"scenario_name": "5227-T6 — pooled income fund routes to structure diagnostic", "scenario_type": "normal", "sort_order": 6,
     "inputs": {"entity_type": "pif", "charitable_642c": 12000},
     "expected_outputs": {"diagnostic": "D_5227_PIF"},
     "notes": "A PIF does not use the §664 tier engine; it files a statement (no Form 1041 Sch B) and files 5227. D_5227_PIF fires. Structure only."},
]


# ═══════════════════════════════════════════════════════════════════════════
# FORMS registry + flow assertions
# ═══════════════════════════════════════════════════════════════════════════

FORMS: list[dict] = [
    {
        "identity": {"form_number": "5227", "form_title": "Form 5227 — Split-Interest Trust Information Return (TY2025)",
                     "notes": "WO-10 (spun off from S-11/D-10). The §664 CRT / §642(c)(5) PIF / §4947(a)(2) family. CRAT + CRUT compute the §664(b) four-tier character ordering (TIER-LEVEL: ordinary→capgain→other→corpus, current + undistributed prior; capital gain one class) + Part II accumulation carryforward with category-isolation netting; §664(c)(2) 100% UBTI excise (post-2006) → Form 4720; Part VIII §4941/4943/4944/4945 screening. PIF/CLT/other §4947(a)(2) = structure + diagnostics (PIF §642(c)(5) statement path; CLT grantor vs non-grantor). CRT qualification (5-50% payout / 10% remainder / 5% exhaustion) = diagnostics (funding-time, no §7520/mortality compute). A CRT is income-tax exempt (§664(c)(1)); 5227 replaces Form 1041-A. Layout = flat Part I-IX + Schedule A (2025)."},
        "facts": F5227_FACTS, "rules": F5227_RULES, "rule_links": F5227_RULE_LINKS,
        "lines": F5227_LINES, "diagnostics": F5227_DIAGNOSTICS, "scenarios": F5227_SCENARIOS,
    },
]

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-5227-TIERS", "title": "CRT distribution character = §664(b) worst-first ordering", "assertion_type": "reconciliation",
     "entity_types": ["1041"], "status": "draft", "sort_order": 1,
     "description": "The distribution carries out ordinary income (current + undistributed prior) first, then capital gain, then other/tax-exempt, then corpus. t1+t2+t3+t4 = distribution_amount.",
     "definition": {"rule": "R-5227-TIERS", "check": "t1=min(dist,avail_ord); t2=min(rem,avail_cap); t3=min(rem,avail_nontax); t4=rem; sum=dist"}},
    {"assertion_id": "FA-5227-ACCUM", "title": "Accumulation carryforward is category-isolated", "assertion_type": "reconciliation",
     "entity_types": ["1041"], "status": "draft", "sort_order": 2,
     "description": "Each category's undistributed carryforward = (current + prior undistributed) − amount distributed from that category. A loss stays within its category; it never reduces another category's gain.",
     "definition": {"rule": "R-5227-ACCUM", "check": "carry_c = max(0, avail_c - tier_c) per category; no cross-category offset"}},
    {"assertion_id": "FA-5227-UBTI", "title": "§664(c)(2) UBTI excise = 100% of UBTI", "assertion_type": "reconciliation",
     "entity_types": ["1041"], "status": "draft", "sort_order": 3,
     "description": "Any UBTI produces an excise tax equal to 100% of the UBTI (chapter 42), reported on Part VIII line 7 and Form 4720; the trust retains its §664(c)(1) exemption (post-2006).",
     "definition": {"rule": "R-5227-UBTI", "check": "ubti_excise = ubti_amount * 1.00 if ubti_amount > 0"}},
    {"assertion_id": "FA-5227-QUAL", "title": "CRT qualification is a diagnostic gate (5-50% / 10% / 5%)", "assertion_type": "flow_assertion",
     "entity_types": ["1041"], "status": "draft", "sort_order": 4,
     "description": "The 5-50% payout, 10% minimum remainder, and CRAT 5% probability-of-exhaustion are flagged as diagnostics with the rule cited; they are not computed via §7520/mortality (established at funding).",
     "definition": {"rule": "R-5227-QUAL", "check": "payout in [0.05,0.50]; remainder >= 0.10; CRAT exhaustion <= 0.05 or safe harbor"}},
]


# ═══════════════════════════════════════════════════════════════════════════
# Command
# ═══════════════════════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = (
        "Load the Form 5227 spec (Split-Interest Trust Information Return, TY2025). "
        "Refuses to seed until Ken sets READY_TO_SEED=True after the review walk (W1-W4)."
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad Form 5227 spec (Split-Interest Trust Information Return)\n"))
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
                "\nREFUSING TO SEED FORM 5227: not cleared to seed.\n\n"
                "Content is authored, but seeding is gated until Ken reviews the packet\n"
                "(W1 the four-tier ordering; W2 the category-isolation netting; W3 the\n"
                "§664(c)(2) 100% UBTI excise year-keying; W4 the qualification diagnostics +\n"
                "the flat Part I-IX layout) and flips the sentinel.\n\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True to proceed)\n\n"
                f"Currently empty / placeholder:\n  {still_empty}\n\n"
                "To proceed: review the module-level data lists (and f5227_source_brief.md),\n"
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
        self.stdout.write("Form 5227 loaded.")
        self.stdout.write(
            f"  5227: facts {len(F5227_FACTS)} / rules {len(F5227_RULES)} / lines {len(F5227_LINES)} / "
            f"diag {len(F5227_DIAGNOSTICS)} / tests {len(F5227_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}"
        )
        self.stdout.write("=" * 60)
