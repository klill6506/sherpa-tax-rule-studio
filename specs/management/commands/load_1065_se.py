"""Load the 1065_SE spec — Form 1065 Schedule K / K-1 line 14a Self-Employment (SECA).

Authoring input: the LOCKED spec at
  D:\\dev\\tts-tax-app\\server\\specs\\1065_se_line14a_spec.md
(tax-law decisions locked by Ken 2026-07-01; authorities verified 2026-07-01 against
primary sources). This loader is a FAITHFUL TRANSLATION of that spec — no tax-law calls
are made here; the four §12 decisions were locked upstream.

WHAT THIS GOVERNS: Schedule K line 14a (net earnings/loss from self-employment) and its
per-partner allocation to K-1 box 14 code A. The single modernization vs. today's silent
compute: it substitutes a per-partner functional-analysis `se_classification`
(active / passive / undetermined) for the SE Worksheet's mechanical "limited partner"
label at lines 3b/4b — because post-*Soroban* an *active* "limited partner" is not a
"limited partner, as such" under §1402(a)(13). Everything else mirrors the IRS SE
Worksheet (i1065 2025, p.45).

DECISIONS — LOCKED (Ken 2026-07-01, spec §12):
  1. Safety-net default on `undetermined` → ACTIVE / INCLUDE (never silently understates SE).
  2. LLC members ride the active/passive axis (functional analysis), not fixed-active.
  3. Passive/limited guaranteed payment for CAPITAL → excluded from SE.
  4. General/active guaranteed payment for CAPITAL → included in SE.

AUTHORITY QUOTING (spec §7 + CLAUDE.md Authoritative-Source Rule): the three Treasury-reg
excerpts (Reg §1.1402(a)-1(a)(2), §1.1402(a)-1(b), §1.1402(a)-4) and the operative IRC
subsections (§1402(a)/(a)(1)/(a)(2)/(a)(3)/(a)(13), §707(c), §702(a)(8)/(b)) were read
DIRECTLY from the CFR / U.S. Code and quoted VERBATIM 2026-07-01 (Cornell LII mirror of the
official text) — not paraphrased from a web summary. The case-law group carries the
"verified 2026-07-01 / re-verify each season" note (developing circuit split).

SCOPE: this spec applies the §1402(a)(13) classification to the SE base; leg 1 did NOT
define the base. LEG 2 (2026-07-02, the §14.1 sub-spec) now DOES: the ordinary-income SE
base per the IRS Worksheet lines 1a-3a — the conditional rental-RE inclusion (1b,
dealer / services-to-occupants), the other-net-rental inclusion (1c = Sch K line 3c),
the Form 4797 Part II line 17 adjustment (1d add back losses / 2 back out gains), the
1e/3a composition, and the worksheet-3b/4b NON-INDIVIDUAL exclusion (estates, trusts,
corporations, exempt organizations, IRAs get no box 14a — K-1 instructions verbatim).
WORKSHEET TEXT VERIFIED 2026-07-02 against the live 2025 i1065 PDF (pymupdf dump of
printed p.44-45) — quoted VERBATIM in the excerpts, not paraphrased. Spec-first:
nothing in tts-tax-app is touched here.

COUPLED VERIFICATION (spec §4b warning): the 1d/2 adjustment makes box 14a depend on
Form 4797 Part II being classified correctly — the §1245-vs-§1250 recapture check for
15-yr improvements (QIP / land improvements) runs alongside this leg; findings go to
Ken for CPA review.
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


# Leg 1 (classification, T1-T10) seeded 2026-07-01 under Ken's locked spec.
# Leg 2 (the 14a SE-BASE sub-spec, B1-B7 — spec §4b/§14.1) authored 2026-07-02:
# gated FALSE pending Ken's review walk (the 1b dealer/services input shape, the
# 4797 1d/2 adjustment diagnostics, and the non-individual 3b/4b guard).
READY_TO_SEED = False


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_ENTITY_TYPES = ["1065"]
FORM_STATUS = "draft"


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("se_1402_partner",
     "Partner self-employment earnings (SECA) — §1402(a)(13) active/passive classification, "
     "guaranteed payments (services vs. capital), and Schedule K / K-1 line 14a."),
]

AUTHORITY_SOURCES: list[dict] = [
    # ── 1. IRC §1402 — the SE definition statute (distributive share + exclusions) ──
    {
        "source_code": "IRC_1402",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1065",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §1402 — Net Earnings From Self-Employment (partner distributive share; "
                 "rental/portfolio exclusions; limited-partner exclusion)",
        "citation": "26 U.S.C. §1402(a), (a)(1), (a)(2), (a)(3), (a)(13)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/1402",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "The controlling statute. §1402(a)(13) limited-partner exclusion is the classification "
                 "axis; resolved by functional analysis post-Soroban (see CASELAW_SE_LP). Text quoted "
                 "verbatim from the U.S. Code 2026-07-01.",
        "topics": ["se_1402_partner"],
        "excerpts": [
            {
                "excerpt_label": "§1402(a) — distributive share in the SE base",
                "location_reference": "26 U.S.C. §1402(a) (opening)",
                "excerpt_text": (
                    "the gross income derived by an individual from any trade or business carried on by "
                    "such individual, less the deductions allowed by this subtitle which are attributable "
                    "to such trade or business, plus his distributive share (whether or not distributed) "
                    "of income or loss described in section 702(a)(8)"
                ),
                "summary_text": "Net earnings from self-employment include the partner's distributive share "
                                "(income OR loss) of §702(a)(8) trade-or-business income.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§1402(a)(1) — rentals from real estate excluded",
                "location_reference": "26 U.S.C. §1402(a)(1)",
                "excerpt_text": (
                    "there shall be excluded rentals from real estate and from personal property leased "
                    "with the real estate (including such rentals paid in crop shares, and including "
                    "payments under section 1233(a)(2) of the Food Security Act of 1985 (16 U.S.C. "
                    "3833(a)(2)) to individuals receiving benefits under section 202 or 223 of the Social "
                    "Security Act) together with the deductions attributable thereto, unless such rentals "
                    "are received in the course of a trade or business as a real estate dealer"
                ),
                "summary_text": "Rental real estate (box 2) is excluded from SE unless received as a "
                                "real-estate dealer.",
                "is_key_excerpt": False,
            },
            {
                "excerpt_label": "§1402(a)(2)/(a)(3) — dividends, interest, and capital gains excluded",
                "location_reference": "26 U.S.C. §1402(a)(2), (a)(3)",
                "excerpt_text": (
                    "(2) there shall be excluded dividends on any share of stock, and interest on any bond, "
                    "debenture, note, or certificate, or other evidence of indebtedness, issued with interest "
                    "coupons or in registered form by any corporation (including one issued by a government "
                    "or political subdivision thereof), unless such dividends and interest are received in "
                    "the course of a trade or business as a dealer in stocks or securities; (3) there shall "
                    "be excluded any gain or loss— (A) which is considered as gain or loss from the sale or "
                    "exchange of a capital asset"
                ),
                "summary_text": "Portfolio interest/dividends (non-dealer) and capital gains (boxes 5/6/8/9) "
                                "are excluded from SE.",
                "is_key_excerpt": False,
            },
            {
                "excerpt_label": "§1402(a)(13) — limited-partner exclusion (services-only carve-back)",
                "location_reference": "26 U.S.C. §1402(a)(13)",
                "excerpt_text": (
                    "there shall be excluded the distributive share of any item of income or loss of a "
                    "limited partner, as such, other than guaranteed payments described in section 707(c) "
                    "to that partner for services actually rendered to or on behalf of the partnership to "
                    "the extent that those payments are established to be in the nature of remuneration for "
                    "those services"
                ),
                "summary_text": "A limited partner 'as such' excludes the distributive share, EXCEPT §707(c) "
                                "guaranteed payments for services — the carve-back is services-only "
                                "(so capital GP of a limited partner is excluded).",
                "is_key_excerpt": True,
            },
        ],
    },
    # ── 2. IRC §702 — distributive share + character ──
    {
        "source_code": "IRC_702",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1065",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §702 — Income and Credits of Partner (distributive share; character conduit)",
        "citation": "26 U.S.C. §702(a)(8), (b)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/702",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "§702(a)(8) is the trade-or-business distributive share that §1402(a) pulls into the SE "
                 "base; §702(b) is the character conduit. Quoted verbatim 2026-07-01.",
        "topics": ["se_1402_partner"],
        "excerpts": [
            {
                "excerpt_label": "§702(a)(8) — taxable income/loss distributive share",
                "location_reference": "26 U.S.C. §702(a)(8)",
                "excerpt_text": (
                    "taxable income or loss, exclusive of items requiring separate computation under other "
                    "paragraphs of this subsection."
                ),
                "summary_text": "§702(a)(8) is the residual trade-or-business income/loss distributive share "
                                "referenced by §1402(a).",
                "is_key_excerpt": False,
            },
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
                "summary_text": "Each item keeps its partnership-level character in the partner's hands "
                                "(rental stays rental, portfolio stays portfolio).",
                "is_key_excerpt": False,
            },
        ],
    },
    # ── 3. IRC §707(c) — guaranteed payments ──
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
        "notes": "Defines guaranteed payments for services OR use of capital — the two GP components the "
                 "classification splits for SE. Quoted verbatim 2026-07-01.",
        "topics": ["se_1402_partner"],
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
                "summary_text": "Guaranteed payments are for services OR the use of capital — the split that "
                                "drives R-SE-GPSVC (always SE) vs. R-SE-GPCAP (SE iff active).",
                "is_key_excerpt": True,
            },
        ],
    },
    # ── 4. Treas. Reg. §1.1402(a)-1 — CFR TEXT READ DIRECTLY, quoted verbatim ──
    {
        "source_code": "TREAS_REG_1402A1",
        "source_type": "regulation",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1065",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "Treas. Reg. §1.1402(a)-1 — Definition of net earnings from self-employment "
                 "(distributive share; guaranteed payments for services or use of capital)",
        "citation": "26 CFR §1.1402(a)-1(a)(2), (b)",
        "issuer": "U.S. Treasury (IRS)",
        "official_url": "https://www.law.cornell.edu/cfr/text/26/1.1402(a)-1",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "CFR text READ DIRECTLY and quoted VERBATIM 2026-07-01 (spec §7 quoting rule — no web "
                 "summary). (b) supports Decision 4: a guaranteed payment for the USE OF CAPITAL is trade-"
                 "or-business gross income (→ SE) for an active partner.",
        "topics": ["se_1402_partner"],
        "excerpts": [
            {
                "excerpt_label": "§1.1402(a)-1(a)(2) — distributive share of partnership trade/business",
                "location_reference": "26 CFR §1.1402(a)-1(a)(2)",
                "excerpt_text": (
                    "His distributive share (whether or not distributed), as determined under section 704, "
                    "of the income (or minus the loss), described in section 702(a)(9) and as computed under "
                    "section 703, from any trade or business carried on by any partnership of which he is a "
                    "member."
                ),
                "summary_text": "The partner's distributive share of partnership trade-or-business income "
                                "(or minus loss) is in the SE base.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§1.1402(a)-1(b) — payments for services or use of capital are business income",
                "location_reference": "26 CFR §1.1402(a)-1(b)",
                "excerpt_text": (
                    "Gross income derived by an individual from a trade or business includes payments "
                    "received by him from a partnership of which he is a member for services rendered to the "
                    "partnership or for the use of capital by the partnership, to the extent the payments are "
                    "determined without regard to the income of the partnership. However, such payments "
                    "received from a partnership not engaged in a trade or business within the meaning of "
                    "section 1402(c) and § 1.1402(c)-1 do not constitute gross income derived by an "
                    "individual from a trade or business."
                ),
                "summary_text": "Guaranteed payments for services OR for the use of capital are trade-or-"
                                "business gross income (→ SE) — the reg basis for Decision 4 (active capital "
                                "GP is SE).",
                "is_key_excerpt": True,
            },
        ],
    },
    # ── 5. Treas. Reg. §1.1402(a)-4 — CFR TEXT READ DIRECTLY, quoted verbatim ──
    {
        "source_code": "TREAS_REG_1402A4",
        "source_type": "regulation",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1065",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "Treas. Reg. §1.1402(a)-4 — Rentals from real estate (excluded from SE)",
        "citation": "26 CFR §1.1402(a)-4(a)",
        "issuer": "U.S. Treasury (IRS)",
        "official_url": "https://www.law.cornell.edu/cfr/text/26/1.1402(a)-4",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "CFR text READ DIRECTLY and quoted VERBATIM 2026-07-01 (spec §7 quoting rule). Basis for "
                 "R-SE-RENTAL: box 2 rental RE is excluded from SE for all partner types (non-dealer).",
        "topics": ["se_1402_partner"],
        "excerpts": [
            {
                "excerpt_label": "§1.1402(a)-4(a) — rentals from real estate excluded (general rule)",
                "location_reference": "26 CFR §1.1402(a)-4(a)",
                "excerpt_text": (
                    "Rentals from real estate and from personal property leased with the real estate "
                    "(including such rentals paid in crop shares) and the deductions attributable thereto, "
                    "unless such rentals are received by an individual in the course of a trade or business "
                    "as a real-estate dealer, are excluded."
                ),
                "summary_text": "Rental real estate is excluded from SE unless the individual is a "
                                "real-estate dealer.",
                "is_key_excerpt": True,
            },
        ],
    },
    # ── 6. Case-law line — the §1402(a)(13) functional-analysis split (HIGH CHURN) ──
    {
        "source_code": "CASELAW_SE_LP",
        "source_type": "case_law",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1065",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "Limited-partner SE functional-analysis case line (§1402(a)(13) 'limited partner, as such')",
        "citation": "Renkemeyer 136 T.C. 137 (2011); Soroban 161 T.C. No. 12 (2023) & T.C. Memo. 2025-52; "
                    "Denham T.C. Memo. 2024-114; contra Sirius No. 24-60240 (5th Cir. 2026)",
        "issuer": "U.S. Tax Court; U.S. Court of Appeals for the Fifth Circuit",
        "official_url": "https://www.ustaxcourt.gov/",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 8.50,
        "requires_human_review": True,
        "notes": "VERIFIED 2026-07-01 against primary sources — RE-VERIFY EACH FILING SEASON and on any "
                 "ruling in the pending appeals. Highest-churn part of the spec: a developing circuit split. "
                 "§1402(a)(13) 'limited partner, as such' is resolved by a functional-analysis inquiry (Tax "
                 "Court: Renkemeyer/Soroban/Denham) — a state-law 'limited partner' label is not dispositive. "
                 "CONTRA: 5th Cir. Sirius applies a state-law text test but binds LA/MS/TX only; the 11th "
                 "Circuit (GA) is UNRESOLVED, so Sirius does not bind GA clients. Pending appeals: Soroban "
                 "(2nd Cir.) / Denham (1st Cir.), decisions expected 2026 — outcome + timing pending.",
        "topics": ["se_1402_partner"],
        "excerpts": [
            {
                "excerpt_label": "Renkemeyer, 136 T.C. 137 (2011) — functional analysis established",
                "location_reference": "136 T.C. 137 (2011)",
                "excerpt_text": (
                    "Partners in a law-firm LLP were not 'limited partners, as such' under §1402(a)(13); "
                    "their distributive shares arising from performing legal services for the partnership "
                    "were net earnings from self-employment — the functional-analysis line."
                ),
                "summary_text": "Renkemeyer: a state-law limited-liability label does not exclude a partner "
                                "whose share derives from services rendered.",
                "is_key_excerpt": False,
            },
            {
                "excerpt_label": "Soroban I, 161 T.C. No. 12 (Nov 28 2023) — functional test required",
                "location_reference": "161 T.C. No. 12 (2023)",
                "excerpt_text": (
                    "§1402(a)(13)'s 'limited partner, as such' exclusion requires a functional-analysis "
                    "inquiry into the partner's role; a partner's state-law 'limited partner' status is not "
                    "dispositive of the exclusion."
                ),
                "summary_text": "Soroban I: the functional test is required — the label alone does not "
                                "control the §1402(a)(13) exclusion.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Soroban II, T.C. Memo. 2025-52 (May 28 2025) — test applied, LPs taxable",
                "location_reference": "T.C. Memo. 2025-52 (2025)",
                "excerpt_text": (
                    "Applying the functional test, the limited partners' distributive shares were held "
                    "includible (taxable) in net earnings from self-employment."
                ),
                "summary_text": "Soroban II: on the facts, the limited partners were active — shares included "
                                "in SE.",
                "is_key_excerpt": False,
            },
            {
                "excerpt_label": "Denham, T.C. Memo. 2024-114 (Dec 23 2024) — functional analysis applied",
                "location_reference": "T.C. Memo. 2024-114 (2024)",
                "excerpt_text": (
                    "The functional-analysis inquiry was applied to a private-equity fund's limited "
                    "partners under §1402(a)(13)."
                ),
                "summary_text": "Denham: extends the functional analysis to a PE-fund limited-partner "
                                "structure.",
                "is_key_excerpt": False,
            },
            {
                "excerpt_label": "Sirius (CONTRA), No. 24-60240 (5th Cir. Jan 16 2026) — state-law text test",
                "location_reference": "No. 24-60240 (5th Cir. 2026)",
                "excerpt_text": (
                    "Applies a state-law text test to §1402(a)(13); binds Louisiana, Mississippi, and Texas "
                    "only. The 11th Circuit (Georgia) is unresolved, so this holding does not bind GA clients."
                ),
                "summary_text": "Sirius (5th Cir.): contra authority; binds LA/MS/TX only — GA/11th Cir. "
                                "unresolved (drives the §6 include-on-undetermined default).",
                "is_key_excerpt": True,
            },
        ],
    },
    # ── 7. IRS SE Worksheet (i1065 2025, p.45) — the mechanical computation home ──
    {
        "source_code": "IRS_2025_1065_SEWKST",
        "source_type": "official_instructions",
        "source_rank": "implementation_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1065",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Instructions for Form 1065 — Worksheet for Figuring Net Earnings (Loss) From "
                 "Self-Employment (p.45)",
        "citation": "Instructions for Form 1065 (2025), SE Worksheet, lines 1a-5 (p.45)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i1065.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": "The IRS SE Worksheet already encodes Decisions 3 & 4 verbatim (line 3b removes limited "
                 "partners' distributive share; line 4b removes their capital GP; services GP retained on "
                 "4c; entity line 14a = worksheet line 5 = 3c + 4c). Our spec's ONE addition: substitute "
                 "the functional-analysis se_classification for the worksheet's mechanical 'limited "
                 "partner' label at 3b/4b. Worksheet + instruction text VERIFIED + quoted VERBATIM "
                 "2026-07-02 from the live 2025 i1065 PDF (printed p.44-45; pymupdf dump). "
                 "REQUIRES HUMAN REVIEW: re-verify against any i1065 revision each season.",
        "topics": ["se_1402_partner"],
        "excerpts": [
            {
                "excerpt_label": "SE Worksheet base (lines 1a-3a)",
                "location_reference": "i1065 (2025) p.45, SE Worksheet lines 1a-3a (verbatim)",
                "excerpt_text": (
                    "1a Ordinary business income (loss) (Schedule K, line 1) ... 1b Net income (loss) from "
                    "certain rental real estate activities (see instructions) ... 1c Other net rental income "
                    "(loss) (Schedule K, line 3c) ... 1d Net loss from Form 4797, Part II, line 17, included "
                    "on line 1a, above. Enter as a positive amount ... 1e Combine lines 1a through 1d ... "
                    "2 Net gain from Form 4797, Part II, line 17, included on line 1a, above ... 3a Subtract "
                    "line 2 from line 1e. If line 1e is a loss, increase the loss on line 1e by the amount "
                    "on line 2."
                ),
                "summary_text": "The ordinary-income SE base: 1e = 1a + 1b + 1c + 1d; 3a = 1e − 2. The 4797 "
                                "Part II line 17 net gain is backed out (2) and a net loss added back (1d), "
                                "each only to the extent included on line 1a.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "§1402(a)(13) split + entity 14a (lines 3b/4b/3c/4c → 14a)",
                "location_reference": "i1065 (2025) p.45, SE Worksheet lines 3b-5 (verbatim)",
                "excerpt_text": (
                    "3b Part of line 3a allocated to limited partners, estates, trusts, corporations, exempt "
                    "organizations, and IRAs ... 3c Subtract line 3b from line 3a. If line 3a is a loss, "
                    "reduce the loss on line 3a by the amount on line 3b. Include each general partner's "
                    "share of line 3c in box 14 of Schedule K-1 using code A ... 4a Guaranteed payments to "
                    "partners (Schedule K, line 4c) derived from a trade or business as defined in section "
                    "1402(c) (see instructions) ... 4b Part of line 4a allocated to limited partners for "
                    "other than services and to estates, trusts, corporations, exempt organizations, and "
                    "IRAs ... 4c Subtract line 4b from line 4a. Include each general partner's share and "
                    "each limited partner's share of line 4c in box 14 of Schedule K-1 using code A ... "
                    "5 Net earnings (loss) from self-employment. Combine lines 3c and 4c. Enter here and on "
                    "Schedule K, line 14a"
                ),
                "summary_text": "Entity 14a = line 5 = 3c + 4c; 3b/4b remove limited partners (the label "
                                "this spec replaces with se_classification) AND all non-individual partners "
                                "(estates, trusts, corporations, exempt organizations, IRAs).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Line 1b — dealer / services-to-occupants rentals (Worksheet Instructions)",
                "location_reference": "i1065 (2025) p.44, Worksheet Instructions, Line 1b (verbatim)",
                "excerpt_text": (
                    "Line 1b. Include on line 1b any part of the net income (loss) from rental real estate "
                    "activities from Schedule K, line 2, that is from: Rentals of real estate held for sale "
                    "to customers in the course of a trade or business as a real estate dealer, or Rentals "
                    "for which services were rendered to the occupants (other than services usually or "
                    "customarily rendered for the rental of space for occupancy only). The supplying of maid "
                    "service is such a service, but the furnishing of heat and light; the cleaning of public "
                    "entrances, exits, stairways, and lobbies; and trash collection, etc., aren't considered "
                    "services rendered to the occupants."
                ),
                "summary_text": "1b pulls INTO the SE base the K2 rental subset that is dealer inventory or "
                                "services-to-occupants (maid service yes; heat/light/common-area cleaning/"
                                "trash no). Fact-sensitive → preparer-entered with a nudge diagnostic.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "K-1 box 14 — no entry for non-individual partners (Code A instructions)",
                "location_reference": "i1065 (2025) p.44, Code A. Line 14a (verbatim)",
                "excerpt_text": (
                    "Schedule K. Enter on line 14a the amount from line 5 of the worksheet. Schedule K-1. "
                    "Don't complete this line for any partner that is an estate, a trust, a corporation, an "
                    "exempt organization, or an IRA. Enter in box 14 of Schedule K-1 each individual general "
                    "partner's share of the combined amounts shown on the worksheet, lines 3c and 4c; and "
                    "each individual limited partner's share of the amount shown on the worksheet, line 4c, "
                    "using code A."
                ),
                "summary_text": "Non-individual partners get NO box 14a entry (R-SE-NONIND / D_SE_NONIND); "
                                "individual general partners get 3c+4c shares, individual limited partners "
                                "4c only (pre-substitution mechanical labels).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Line 4a — GP from a §1402(c) trade or business; §179 partner-level",
                "location_reference": "i1065 (2025) p.44, Worksheet Instructions, Line 4a (verbatim)",
                "excerpt_text": (
                    "Line 4a. Include in the amount on line 4a any guaranteed payments to partners reported "
                    "on Schedule K, line 4c, and in box 4c of Schedule K-1, and derived from a trade or "
                    "business as defined in section 1402(c). Also include other ordinary business income and "
                    "expense items (other than expense items subject to separate limitations at the partner "
                    "level, such as the section 179 expense deduction) reported on Schedules K and K-1 that "
                    "are used to figure self-employment earnings under section 1402."
                ),
                "summary_text": "4a takes trade-or-business GP (§1402(c)); §179 is a PARTNER-level "
                                "adjustment (individual Schedule SE), NOT an entity 14a reduction — confirms "
                                "spec §4b's closure of the earlier 'reduce by §179' error.",
                "is_key_excerpt": False,
            },
        ],
    },
]

# (source_code, form_code, link_type)
AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRC_1402", "1065_SE", "governs"),
    ("IRC_702", "1065_SE", "informs"),
    ("IRC_707C", "1065_SE", "informs"),
    ("TREAS_REG_1402A1", "1065_SE", "governs"),
    ("TREAS_REG_1402A4", "1065_SE", "governs"),
    ("CASELAW_SE_LP", "1065_SE", "informs"),
    ("IRS_2025_1065_SEWKST", "1065_SE", "governs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM: 1065_SE
# ═══════════════════════════════════════════════════════════════════════════

FORM_IDENTITY = {
    "form_number": "1065_SE",
    "form_title": "Form 1065 Schedule K / K-1 Line 14a — Self-Employment Earnings (SECA) (TY2025)",
    "notes": (
        "Authored 2026-07-01 from the LOCKED spec 1065_se_line14a_spec.md (tts-tax-app "
        "server/specs). Governs Schedule K line 14a (net earnings/loss from self-employment) and its "
        "per-partner allocation to K-1 box 14 code A. Core principle: any SE inclusion that turns on "
        "§1402(a)(13) is a per-partner preparer determination surfaced with a diagnostic — never a "
        "silently computed number, in either direction. One per-partner se_classification "
        "(active/passive/undetermined) drives component treatment (§3 table). Decisions LOCKED "
        "(Ken 2026-07-01): (1) undetermined→active INCLUDE safety net; (2) LLC members on the "
        "active/passive axis; (3) passive capital GP excluded; (4) active capital GP included. Entity "
        "14a is derived BOTTOM-UP = Σ per-partner box 14a (replaces the independent K14a = K1 + K4c "
        "path). LEG 2 (2026-07-02, spec §14.1): the SE-base sub-spec — the i1065 2025 p.45 worksheet "
        "lines 1a-3a (WS1a-WS5 lines; R-SE-BASE-* rules; B1-B7 scenarios): conditional dealer/"
        "services rental inclusion (1b), other-net-rental inclusion (1c = K3c), the Form 4797 Part II "
        "line 17 adjustment (1d/2), the 1e/3a composition, and the non-individual 3b/4b exclusion "
        "(R-SE-NONIND — no box 14a for estates/trusts/corps/exempts/IRAs). Worksheet text verified + "
        "quoted verbatim 2026-07-02. STILL OUT OF SCOPE: K-1 14b/14c (spec §14.4)."
    ),
}

FACTS: list[dict] = [
    {"fact_key": "se_partner_type", "label": "Partner type (general / limited / llc_member)",
     "data_type": "choice", "default_value": "general", "sort_order": 1,
     "choices": ["general", "limited", "llc_member"],
     "notes": "Starting point: general → fixed active; limited / llc_member → classification required "
              "(Decision 2: LLC members ride the same active/passive axis)."},
    {"fact_key": "se_classification", "label": "SE classification (§1402(a)(13): active / passive / undetermined)",
     "data_type": "choice", "default_value": "undetermined", "sort_order": 2,
     "choices": ["active", "passive", "undetermined"],
     "notes": "The preparer's functional-analysis call. Drives every component (§3). Default undetermined "
              "on create; general is forced active."},
    {"fact_key": "se_classification_basis", "label": "Classification basis (functional-analysis note)",
     "data_type": "string", "required": False, "sort_order": 3,
     "notes": "Optional free-text audit trail supporting the characterization (Whittington defense)."},
    {"fact_key": "se_box1_ordinary", "label": "Distributive share of the ordinary-income SE base (worksheet 3a stage)",
     "data_type": "decimal", "default_value": "0", "sort_order": 10,
     "notes": "The partner's allocated share of the WORKSHEET-DEFINED base (se_ws_3a — leg 2), pre-3b split "
              "(the 3b removal is what R-SE-DSHARE's classification decides). May be negative. Leg 1 read "
              "raw box 1; the base leg adds the 1b/1c rental inclusions and the 4797 1d/2 adjustment."},
    {"fact_key": "se_gp_services", "label": "Guaranteed payment for services (§707(c))",
     "data_type": "decimal", "default_value": "0", "sort_order": 11,
     "notes": "SE for EVERY partner type (§1402(a)(13) services carve-back)."},
    {"fact_key": "se_gp_capital", "label": "Guaranteed payment for use of capital (§707(c))",
     "data_type": "decimal", "default_value": "0", "sort_order": 12,
     "notes": "SE iff active (Decision 4); excluded if passive/limited (Decision 3)."},
    {"fact_key": "se_box2_rental", "label": "Rental real estate income/(loss) (box 2)",
     "data_type": "decimal", "default_value": "0", "sort_order": 13,
     "notes": "NOT SE, all types (§1402(a)(1); Reg §1.1402(a)-4)."},
    {"fact_key": "se_portfolio", "label": "Portfolio income — interest/dividends/cap gains (boxes 5/6/8/9)",
     "data_type": "decimal", "default_value": "0", "sort_order": 14,
     "notes": "NOT SE, all types (§1402(a)(2)/(a)(3))."},
    {"fact_key": "se_is_individual", "label": "Individual partner? (non-individuals get no box 14a)",
     "data_type": "boolean", "default_value": "true", "sort_order": 15,
     "notes": "§14.5 guard: a non-individual partner (Partner.is_individual = False) generally gets no "
              "box 14a (full guard deferred to the implementation spec)."},
    # ── SE-base worksheet (leg 2 — entity-level, i1065 2025 p.45 lines 1a-3a) ──
    {"fact_key": "se_ws_1a_k1", "label": "Worksheet 1a — ordinary business income/(loss) (Schedule K, line 1)",
     "data_type": "decimal", "default_value": "0", "sort_order": 20,
     "notes": "YELLOW pull from Sch K line 1 (K1). The starting base."},
    {"fact_key": "se_ws_1b_rental_se", "label": "Worksheet 1b — K2 rental subset: dealer / services-to-occupants",
     "data_type": "decimal", "default_value": "0", "sort_order": 21,
     "notes": "PREPARER-ENTERED (GREEN): the part of Sch K line 2 rental RE that is dealer inventory or "
              "services-rendered-to-occupants (i1065 Line 1b instructions verbatim; maid service yes, "
              "heat/light/common-area/trash no). Fact-sensitive — D_SE_RENT1B nudges when K2 ≠ 0."},
    {"fact_key": "se_ws_1c_k3c", "label": "Worksheet 1c — other net rental income/(loss) (Schedule K, line 3c)",
     "data_type": "decimal", "default_value": "0", "sort_order": 22,
     "notes": "YELLOW pull from Sch K line 3c (K3c). IN the SE base per the worksheet — today's raw-box-1 "
              "compute omits it (spec §4b gap)."},
    {"fact_key": "se_ws_1d_4797_loss", "label": "Worksheet 1d — net LOSS from Form 4797 Part II line 17 in line 1a (positive)",
     "data_type": "decimal", "default_value": "0", "sort_order": 23,
     "notes": "Added back (entered positive). Only to the extent included on line 1a. YELLOW pull once the "
              "4797 engine feeds it; preparer-enterable until then. D_SE_4797ORD guards the unaddressed case."},
    {"fact_key": "se_ws_2_4797_gain", "label": "Worksheet 2 — net GAIN from Form 4797 Part II line 17 in line 1a",
     "data_type": "decimal", "default_value": "0", "sort_order": 24,
     "notes": "Backed out of the base (ordinary 4797 gains are not SE). Only to the extent included on "
              "line 1a. ⚠ Coupled with the 4797 §1245-vs-§1250 classification verification (spec §4b)."},
    {"fact_key": "se_ws_1e", "label": "Worksheet 1e — combine lines 1a through 1d",
     "data_type": "decimal", "sort_order": 25, "notes": "OUTPUT. 1e = 1a + 1b + 1c + 1d."},
    {"fact_key": "se_ws_3a", "label": "Worksheet 3a — the ordinary-income SE base (1e − 2)",
     "data_type": "decimal", "sort_order": 26,
     "notes": "OUTPUT. 3a = 1e − 2 (plain subtraction also realizes the face's 'if 1e is a loss, increase "
              "the loss by line 2'). Per-partner se_box1_ordinary = the partner's allocated share of this."},
    # ── Outputs ──
    {"fact_key": "se_k1_box14a", "label": "K-1 box 14a — partner net earnings/(loss) from self-employment",
     "data_type": "decimal", "sort_order": 40,
     "notes": "OUTPUT. Per-partner: (active? box1 with loss symmetry : 0) + gp_services + (active? gp_capital : 0)."},
    {"fact_key": "sched_k_line14a", "label": "Schedule K line 14a — entity total (Σ per-partner box 14a)",
     "data_type": "decimal", "sort_order": 41,
     "notes": "OUTPUT. Derived bottom-up = Σ per-partner K-1 box 14a (RECON-14A)."},
]

RULES: list[dict] = [
    {"rule_id": "R-SE-CLASS", "title": "Classification drives component treatment", "rule_type": "classification",
     "precedence": 1, "sort_order": 1,
     "formula": ("Per-partner se_classification ∈ {active, passive, undetermined} is the preparer's "
                 "§1402(a)(13) functional-analysis call (does the partner function as a general/active "
                 "partner or a limited/passive investor?). general → fixed active (settled). limited / "
                 "llc_member → classification required (Decision 2: LLC members ride the same active/"
                 "passive axis per Renkemeyer). The classification drives R-SE-DSHARE and R-SE-GPCAP "
                 "(§3 table)."),
     "inputs": ["se_partner_type", "se_classification"], "outputs": [],
     "description": "§3 determination model. §1402(a)(13) resolved by functional analysis (Soroban)."},
    {"rule_id": "R-SE-DSHARE", "title": "Distributive share (box 1) → SE per classification", "rule_type": "routing",
     "precedence": 2, "sort_order": 2,
     "formula": ("Distributive share of ordinary business income (box 1) is SE iff active (active/general, "
                 "or undetermined defaulted to active per R-SE-DEFAULT); excluded if passive/limited. "
                 "§1402(a) + §702(a)(8) + Reg §1.1402(a)-1(a)(2)."),
     "inputs": ["se_box1_ordinary", "se_classification"], "outputs": [],
     "description": "§4 component table, row 1. Contested (preparer) for limited/llc; auto for general."},
    {"rule_id": "R-SE-GPSVC", "title": "Guaranteed payment for services → SE (all partner types)", "rule_type": "calculation",
     "precedence": 3, "sort_order": 3,
     "formula": ("Guaranteed payment for services (§707(c)) → SE for EVERY partner type, automatic. The "
                 "§1402(a)(13) carve-back retains services GP even for a limited/passive partner. "
                 "Reg §1.1402(a)-1(b). Not reduced by a distributive-share loss (§4a)."),
     "inputs": ["se_gp_services"], "outputs": [],
     "description": "§4 component table, row 2. Automatic, always included."},
    {"rule_id": "R-SE-GPCAP", "title": "Guaranteed payment for capital → SE iff active", "rule_type": "conditional",
     "precedence": 4, "sort_order": 4,
     "formula": ("Guaranteed payment for the use of capital (§707(c)) → SE iff active; excluded if "
                 "passive/limited. Decision 4: active/general capital GP IS SE (Reg §1.1402(a)-1(b), use "
                 "of capital). Decision 3: passive/limited capital GP is EXCLUDED (§1402(a)(13) "
                 "services-only carve-back)."),
     "inputs": ["se_gp_capital", "se_classification"], "outputs": [],
     "description": "§4 component table, row 3. Decisions 3 & 4 (LOCKED)."},
    {"rule_id": "R-SE-DEFAULT", "title": "Undetermined → active safety net (Decision 1)", "rule_type": "conditional",
     "precedence": 5, "sort_order": 5,
     "formula": ("When se_classification = undetermined AND the partner has nonzero allocated ordinary "
                 "income: (a) fire D_SE_UNDET, and (b) apply the safety-net default = treat as ACTIVE "
                 "(INCLUDE) so the return computes. Rationale: GA is 11th Cir. (no controlling appellate "
                 "precedent) → the Tax Court functional posture is operative; include-on-undetermined "
                 "never silently understates SE (the penalty-drawing direction). A safety net, NOT a "
                 "substitute for the real call."),
     "inputs": ["se_classification", "se_box1_ordinary"], "outputs": [],
     "description": "§6 default & safety net (Decision 1, LOCKED)."},
    {"rule_id": "R-SE-RENTAL", "title": "Rental real estate (box 2) excluded from SE", "rule_type": "classification",
     "precedence": 6, "sort_order": 6,
     "formula": ("Rental real estate (box 2) is NOT SE for any partner type. §1402(a)(1); Reg "
                 "§1.1402(a)-4 (excluded unless received in the course of a trade or business as a "
                 "real-estate dealer)."),
     "inputs": ["se_box2_rental"], "outputs": [],
     "description": "§4 component table, row 4. Automatic exclusion (non-dealer)."},
    {"rule_id": "R-SE-PORT", "title": "Portfolio (boxes 5/6/8/9) excluded from SE", "rule_type": "classification",
     "precedence": 7, "sort_order": 7,
     "formula": ("Portfolio income — interest / dividends / capital gains (boxes 5/6/8/9) — is NOT SE for "
                 "any partner type. §1402(a)(2) (dividends/interest, non-dealer); §1402(a)(3) (capital "
                 "gains). Character conduit §702(b)."),
     "inputs": ["se_portfolio"], "outputs": [],
     "description": "§4 component table, row 5. Automatic exclusion."},
    {"rule_id": "R-SE-LOSS", "title": "Loss symmetry", "rule_type": "calculation",
     "precedence": 8, "sort_order": 8,
     "formula": ("§4a: an ACTIVE partner (incl. undetermined→active) with a negative distributive-share "
                 "base flows a NEGATIVE 14a (SE loss) — you cannot include gains but drop losses. A "
                 "PASSIVE partner's distributive share is excluded whether gain OR loss. Guaranteed "
                 "payments for services are NOT reduced by a distributive-share loss. Net per-partner "
                 "14a = (active? box1 : 0) + gp_services + (active? gp_capital : 0)."),
     "inputs": ["se_box1_ordinary", "se_classification", "se_gp_services", "se_gp_capital"],
     "outputs": ["se_k1_box14a"],
     "description": "§4a losses — explicit symmetry; writes the per-partner box 14a."},
    {"rule_id": "R-SE-14A-ENT", "title": "Entity Sch K 14a derived bottom-up = Σ per-partner", "rule_type": "calculation",
     "precedence": 9, "sort_order": 9,
     "formula": ("Entity Schedule K line 14a is derived BOTTOM-UP = Σ (per-partner K-1 box 14a), NOT "
                 "computed separately (replaces the independent K14a = K1 + K4c path). Matches the IRS SE "
                 "Worksheet (i1065 2025 p.45): entity line 14a = line 3c + line 4c. RECON-14A enforces "
                 "equality; a break fires D_SE_RECON."),
     "inputs": ["se_k1_box14a"], "outputs": ["sched_k_line14a"],
     "description": "§9 RECON-14A. Bottom-up derivation is the spec requirement."},
    # ── Leg 2 — the 14a SE-BASE sub-spec (i1065 2025 p.45 worksheet lines 1a-3a; spec §4b/§14.1).
    #    These rules DEFINE the base that R-SE-DSHARE's per-partner share splits; precedence 10-14
    #    is registry ordering only — definitionally they are upstream inputs to the leg-1 rules.
    {"rule_id": "R-SE-BASE-1B", "title": "Worksheet 1b — dealer / services-to-occupants rentals IN the base", "rule_type": "conditional",
     "precedence": 10, "sort_order": 10,
     "formula": ("The part of Sch K line 2 rental RE net income/(loss) that is (a) rentals of real estate "
                 "held for sale to customers as a real estate DEALER, or (b) rentals for which SERVICES "
                 "were rendered to the occupants beyond those usual/customary for occupancy-only (maid "
                 "service qualifies; heat/light, common-area cleaning, trash collection do NOT) — goes "
                 "INTO the SE base at worksheet 1b. PREPARER-ENTERED (fact-sensitive); ordinary K2 rentals "
                 "stay excluded (§1402(a)(1); Reg §1.1402(a)-4). D_SE_RENT1B nudges when K2 ≠ 0."),
     "inputs": ["se_ws_1b_rental_se"], "outputs": [],
     "description": "i1065 Line 1b instructions (verbatim excerpt). Closes the spec §4b conditional-rental gap."},
    {"rule_id": "R-SE-BASE-1C", "title": "Worksheet 1c — other net rental (Sch K 3c) IN the base", "rule_type": "calculation",
     "precedence": 11, "sort_order": 11,
     "formula": ("Other net rental income/(loss) (Schedule K line 3c — personal-property and other "
                 "non-real-estate rentals) is included in the SE base at worksheet 1c. YELLOW pull from "
                 "K3c. Today's raw-box-1 compute omits it — a base understatement this rule closes."),
     "inputs": ["se_ws_1c_k3c"], "outputs": [],
     "description": "Worksheet line 1c (verbatim excerpt). Closes the spec §4b other-net-rental gap."},
    {"rule_id": "R-SE-BASE-4797", "title": "Worksheet 1d/2 — Form 4797 Part II line 17 adjustment", "rule_type": "calculation",
     "precedence": 12, "sort_order": 12,
     "formula": ("Ordinary 4797 amounts are not SE: a net GAIN from Form 4797 Part II line 17 included on "
                 "line 1a is BACKED OUT (worksheet 2); a net LOSS so included is ADDED BACK as a positive "
                 "amount (worksheet 1d). Each applies only to the extent the amount is included on line 1a "
                 "(for a 1065, 4797 Part II line 17 → page 1 line 6 → line 22 → K1, so it is). ⚠ Depends "
                 "on 4797 Part II classification being right — the §1245-vs-§1250 recapture verification "
                 "is COUPLED to this rule (spec §4b)."),
     "inputs": ["se_ws_1d_4797_loss", "se_ws_2_4797_gain"], "outputs": [],
     "description": "Worksheet lines 1d and 2 (verbatim excerpt). Closes the spec §4b 4797-adjustment gap."},
    {"rule_id": "R-SE-BASE-3A", "title": "Worksheet 1e/3a — the base composition", "rule_type": "calculation",
     "precedence": 13, "sort_order": 13,
     "formula": ("1e = 1a + 1b + 1c + 1d (combine). 3a = 1e − 2 (subtract; the face's 'if line 1e is a "
                 "loss, increase the loss on line 1e by the amount on line 2' is the same arithmetic with "
                 "signs). 3a is THE ordinary-income SE base; each partner's se_box1_ordinary is their "
                 "allocated share of it (the 3b split is then R-SE-DSHARE's classification call, with "
                 "se_classification substituted for the worksheet's mechanical 'limited partner' label)."),
     "inputs": ["se_ws_1a_k1", "se_ws_1b_rental_se", "se_ws_1c_k3c", "se_ws_1d_4797_loss", "se_ws_2_4797_gain"],
     "outputs": ["se_ws_1e", "se_ws_3a"],
     "description": "Worksheet lines 1e/3a (verbatim excerpt). INV-SE-BASE asserts the composition."},
    {"rule_id": "R-SE-NONIND", "title": "Non-individual partners excluded (worksheet 3b/4b; no box 14a)", "rule_type": "classification",
     "precedence": 14, "sort_order": 14,
     "formula": ("A partner that is an estate, trust, corporation, exempt organization, or IRA is removed "
                 "at worksheet 3b (its share of the base) AND 4b (ALL of its guaranteed payments — services "
                 "included), and gets NO K-1 box 14a entry: 'Don't complete this line for any partner that "
                 "is an estate, a trust, a corporation, an exempt organization, or an IRA' (Code A "
                 "instructions, verbatim). Keyed on the existing se_is_individual fact. D_SE_NONIND (info) "
                 "surfaces the suppression."),
     "inputs": ["se_is_individual"], "outputs": [],
     "description": "Closes spec §14.5 (the non-individual guard) — now worksheet-grounded, not inferred."},
]

LINES: list[dict] = [
    {"line_number": "K14a", "description": "Schedule K, line 14a — Net earnings (loss) from self-employment "
                                          "(entity total = Σ per-partner K-1 box 14a)",
     "line_type": "total", "sort_order": 1,
     "source_rules": ["R-SE-14A-ENT"],
     "notes": "Derived bottom-up (RECON-14A). Replaces the independent K14a = K1 + K4c path."},
    {"line_number": "14a", "description": "Schedule K-1, box 14, code A — Partner's net earnings (loss) from "
                                          "self-employment",
     "line_type": "calculated", "sort_order": 2,
     "source_rules": ["R-SE-DSHARE", "R-SE-GPSVC", "R-SE-GPCAP", "R-SE-DEFAULT", "R-SE-LOSS", "R-SE-NONIND"],
     "destination_form": "SCHEDULE_SE",
     "notes": "Per-partner. Suppressed entirely for non-individual partners (R-SE-NONIND). 14b/14c (gross "
              "farming / nonfarm) are OUT OF SCOPE (§14). destination_form SCHEDULE_SE is the FUTURE "
              "flow-through gated by FLOW-14A-SE (inactive)."},
    # ── Leg 2 — the SE worksheet face (i1065 2025 p.45), lines 1a-5 ──
    {"line_number": "WS1a", "description": "Ordinary business income (loss) (Schedule K, line 1)", "line_type": "calculated",
     "sort_order": 10, "source_facts": ["se_ws_1a_k1"], "notes": "YELLOW pull from K1."},
    {"line_number": "WS1b", "description": "Net income (loss) from certain rental real estate activities (see instructions)", "line_type": "input",
     "sort_order": 11, "source_facts": ["se_ws_1b_rental_se"], "source_rules": ["R-SE-BASE-1B"],
     "notes": "Preparer-entered dealer / services-to-occupants subset of K2."},
    {"line_number": "WS1c", "description": "Other net rental income (loss) (Schedule K, line 3c)", "line_type": "calculated",
     "sort_order": 12, "source_facts": ["se_ws_1c_k3c"], "source_rules": ["R-SE-BASE-1C"], "notes": "YELLOW pull from K3c."},
    {"line_number": "WS1d", "description": "Net loss from Form 4797, Part II, line 17, included on line 1a, above. Enter as a positive amount", "line_type": "calculated",
     "sort_order": 13, "source_facts": ["se_ws_1d_4797_loss"], "source_rules": ["R-SE-BASE-4797"], "notes": "Added back (positive)."},
    {"line_number": "WS1e", "description": "Combine lines 1a through 1d", "line_type": "subtotal",
     "sort_order": 14, "source_rules": ["R-SE-BASE-3A"], "notes": "1e = 1a + 1b + 1c + 1d."},
    {"line_number": "WS2", "description": "Net gain from Form 4797, Part II, line 17, included on line 1a, above", "line_type": "calculated",
     "sort_order": 15, "source_facts": ["se_ws_2_4797_gain"], "source_rules": ["R-SE-BASE-4797"], "notes": "Backed out of the base."},
    {"line_number": "WS3a", "description": "Subtract line 2 from line 1e. If line 1e is a loss, increase the loss on line 1e by the amount on line 2", "line_type": "subtotal",
     "sort_order": 16, "source_rules": ["R-SE-BASE-3A"], "notes": "THE ordinary-income SE base."},
    {"line_number": "WS3b", "description": "Part of line 3a allocated to limited partners, estates, trusts, corporations, exempt organizations, and IRAs", "line_type": "calculated",
     "sort_order": 17, "source_rules": ["R-SE-DSHARE", "R-SE-NONIND"],
     "notes": "THE SUBSTITUTION: se_classification (passive) replaces the mechanical 'limited partner' label here; non-individuals always removed."},
    {"line_number": "WS3c", "description": "Subtract line 3b from line 3a (each general partner's share → box 14 code A)", "line_type": "subtotal",
     "sort_order": 18, "source_rules": ["R-SE-DSHARE"], "notes": "The retained (active individual) base."},
    {"line_number": "WS4a", "description": "Guaranteed payments to partners (Schedule K, line 4c) derived from a §1402(c) trade or business", "line_type": "calculated",
     "sort_order": 19, "source_rules": ["R-SE-GPSVC", "R-SE-GPCAP"], "notes": "GP pool entering SE."},
    {"line_number": "WS4b", "description": "Part of line 4a allocated to limited partners for other than services and to estates, trusts, corporations, exempt organizations, and IRAs", "line_type": "calculated",
     "sort_order": 20, "source_rules": ["R-SE-GPCAP", "R-SE-NONIND"],
     "notes": "Passive partners' capital GP out (Decision 3, with se_classification substituted); non-individuals' GP out entirely."},
    {"line_number": "WS4c", "description": "Subtract line 4b from line 4a (each general + limited partner's share → box 14 code A)", "line_type": "subtotal",
     "sort_order": 21, "source_rules": ["R-SE-GPSVC"], "notes": "Retained GP (services for passive; all for active)."},
    {"line_number": "WS5", "description": "Net earnings (loss) from self-employment. Combine lines 3c and 4c. Enter here and on Schedule K, line 14a", "line_type": "total",
     "sort_order": 22, "source_rules": ["R-SE-14A-ENT"],
     "notes": "= entity K14a. Identical to the bottom-up Σ per-partner box 14a (the two derivations agree by construction)."},
]

DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_SE_UNDET", "title": "SE classification undetermined — preparer determination required",
     "severity": "error",
     "condition": "se_partner_type in (limited, llc_member) AND se_box1_ordinary != 0 AND "
                  "se_classification == 'undetermined'",
     "message": ("Preparer determination required under §1402(a)(13): this partner's active/passive status "
                 "is unsettled and circuit-dependent (Renkemeyer / Soroban functional analysis; the 11th "
                 "Circuit / Georgia is unresolved). The safety-net default — treat as ACTIVE and INCLUDE "
                 "the distributive share — has been applied so the return computes. Confirm the "
                 "classification: a genuinely passive investor should be set to 'passive' so they are not "
                 "over-taxed."),
     "notes": "§8 hard error + §6 safety net. Fires WITH the active default (does not block compute)."},
    {"diagnostic_id": "D_SE_GPCHAR", "title": "Guaranteed-payment character — capital vs. services (Whittington risk)",
     "severity": "warning",
     "condition": "se_gp_capital > 0 AND se_gp_services == 0 for an active partner",
     "message": ("Confirm the capital/services split of this guaranteed payment is substantiated. The IRS "
                 "can recharacterize a 'capital' guaranteed payment as being for services (Whittington / "
                 "Seismic Support Services), which changes its SE treatment. Concrete threshold: capital "
                 "GP present with zero services GP for an active partner."),
     "notes": "§8 soft warning. Resolves the scaffold's undefined 'large relative to' with a concrete "
              "threshold."},
    {"diagnostic_id": "D_SE_RECON", "title": "Reconciliation break — entity 14a ≠ Σ per-partner 14a",
     "severity": "error",
     "condition": "entity Sch K line 14a != Σ per-partner K-1 box 14a",
     "message": ("Reconciliation break: entity Schedule K line 14a must equal the sum of the per-partner "
                 "K-1 box 14a amounts (RECON-14A). Entity 14a is derived bottom-up from the per-partner "
                 "determinations — it is not computed separately."),
     "notes": "§8 hard error, backs RECON-14A."},
    # ── Leg 2 — SE-base diagnostics ──
    {"diagnostic_id": "D_SE_RENT1B", "title": "Rental RE present — confirm the worksheet 1b determination",
     "severity": "warning",
     "condition": "Sch K line 2 (K2) != 0 AND se_ws_1b_rental_se == 0",
     "message": ("This partnership reports rental real estate (Schedule K line 2). Confirm whether any part "
                 "of it belongs IN the self-employment base at worksheet line 1b: rentals held for sale to "
                 "customers as a real estate DEALER, or rentals with SERVICES rendered to the occupants "
                 "beyond occupancy-only (maid service qualifies; heat/light, common-area cleaning, and "
                 "trash collection do not). Ordinary investment rentals are correctly excluded — if that is "
                 "all of line 2, no entry is needed."),
     "notes": "Leg 2. A nudge, not a block: zero IS the common right answer; the diagnostic forces the "
              "dealer/services question to be asked once per return."},
    {"diagnostic_id": "D_SE_4797ORD", "title": "Form 4797 Part II present — SE-base adjustment required",
     "severity": "error",
     "condition": "Form 4797 Part II line 17 != 0 AND se_ws_1d_4797_loss == 0 AND se_ws_2_4797_gain == 0",
     "message": ("Form 4797 Part II reports an ordinary gain/(loss) that flows into ordinary business "
                 "income (page 1 line 6 → line 22 → Schedule K line 1), but no worksheet 1d/2 adjustment "
                 "has been made. Ordinary 4797 amounts are NOT self-employment earnings: enter the Part II "
                 "line 17 net gain on worksheet line 2 (backed out) or the net loss on line 1d (added "
                 "back), to the extent included in line 1a — otherwise Schedule K line 14a is misstated."),
     "notes": "Leg 2 no-silent-gap error. Becomes a YELLOW auto-pull when the 4797 engine feeds 1d/2 "
              "(build leg); the diagnostic then guards only the disagreement case."},
    {"diagnostic_id": "D_SE_NONIND", "title": "Non-individual partner — no box 14a",
     "severity": "info",
     "condition": "se_is_individual is False",
     "message": ("This partner is an estate, trust, corporation, exempt organization, or IRA. Per the "
                 "Schedule K-1 Code A instructions, box 14a is not completed for a non-individual partner: "
                 "its share of the base is removed at worksheet line 3b and ALL of its guaranteed payments "
                 "at line 4b. No self-employment earnings are reported for this partner."),
     "notes": "Leg 2. Closes spec §14.5 — worksheet-grounded (3b/4b + Code A verbatim)."},
]

# (scenario_name, scenario_type, inputs, expected_outputs, notes)
SCENARIOS: list[dict] = [
    {"scenario_name": "T1 — general partner, all-in baseline", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"se_partner_type": "general", "se_classification": "active",
                "se_box1_ordinary": 100000, "se_gp_services": 20000, "se_gp_capital": 10000},
     "expected_outputs": {"se_k1_box14a": 130000},
     "notes": "General → active (fixed): box1 100k + svc 20k + cap 10k = 130k."},
    {"scenario_name": "T2 — active limited partner = general treatment", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"se_partner_type": "limited", "se_classification": "active",
                "se_box1_ordinary": 100000, "se_gp_services": 20000, "se_gp_capital": 10000},
     "expected_outputs": {"se_k1_box14a": 130000},
     "notes": "Active limited (Soroban) = general treatment: 100k + 20k + 10k = 130k."},
    {"scenario_name": "T3 — passive limited partner, services GP only", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"se_partner_type": "limited", "se_classification": "passive",
                "se_box1_ordinary": 100000, "se_gp_services": 20000, "se_gp_capital": 10000},
     "expected_outputs": {"se_k1_box14a": 20000},
     "notes": "Passive: box1 excluded, capital GP excluded (Decision 3), services GP kept = 20k."},
    {"scenario_name": "T4 — undetermined limited, safety-net default", "scenario_type": "edge", "sort_order": 4,
     "inputs": {"se_partner_type": "limited", "se_classification": "undetermined",
                "se_box1_ordinary": 100000, "se_gp_services": 20000, "se_gp_capital": 10000},
     "expected_outputs": {"se_k1_box14a": 130000, "D_SE_UNDET": True},
     "notes": "Undetermined + nonzero ordinary → default active (INCLUDE) = 130k AND D_SE_UNDET fires "
              "(Decision 1)."},
    {"scenario_name": "T5 — passive LLC member, fixes silent full-inclusion", "scenario_type": "normal", "sort_order": 5,
     "inputs": {"se_partner_type": "llc_member", "se_classification": "passive",
                "se_box1_ordinary": 50000, "se_gp_services": 15000, "se_gp_capital": 5000},
     "expected_outputs": {"se_k1_box14a": 15000},
     "notes": "LLC member on the active/passive axis (Decision 2): passive → box1 + capital GP excluded, "
              "services GP kept = 15k. Fixes today's silent fixed-active full-inclusion."},
    {"scenario_name": "T6 — rental excluded (box 2)", "scenario_type": "normal", "sort_order": 6,
     "inputs": {"se_partner_type": "limited", "se_classification": "passive",
                "se_box1_ordinary": 0, "se_box2_rental": 80000, "se_gp_services": 10000, "se_gp_capital": 0},
     "expected_outputs": {"se_k1_box14a": 10000},
     "notes": "Rental RE (box 2 = 80k) is NOT SE for any classification; only services GP 10k = 10k."},
    {"scenario_name": "T7 — RECON-14A: entity 14a = Σ per-partner box 14a", "scenario_type": "normal", "sort_order": 7,
     "inputs": {"partners": [{"se_k1_box14a": 130000}, {"se_k1_box14a": 20000}]},
     "expected_outputs": {"sched_k_line14a": 150000},
     "notes": "Entity Sch K 14a derived bottom-up = Σ(box 14a) = 130k + 20k = 150k (RECON-14A)."},
    {"scenario_name": "T8 — active capital GP only, Whittington flag", "scenario_type": "edge", "sort_order": 8,
     "inputs": {"se_partner_type": "limited", "se_classification": "active",
                "se_box1_ordinary": 0, "se_gp_services": 0, "se_gp_capital": 100000},
     "expected_outputs": {"se_k1_box14a": 100000, "D_SE_GPCHAR": True},
     "notes": "Active → capital GP included (Decision 4) = 100k AND D_SE_GPCHAR fires (capital GP with "
              "zero services GP)."},
    {"scenario_name": "T9 — general partner loss → negative 14a", "scenario_type": "edge", "sort_order": 9,
     "inputs": {"se_partner_type": "general", "se_classification": "active",
                "se_box1_ordinary": -25000, "se_gp_services": 20000, "se_gp_capital": 0},
     "expected_outputs": {"se_k1_box14a": -5000},
     "notes": "Active loss symmetry (§4a): box1 (25k) + services GP 20k = (5k) negative 14a (SE loss)."},
    {"scenario_name": "T10 — passive limited loss dropped (symmetry)", "scenario_type": "edge", "sort_order": 10,
     "inputs": {"se_partner_type": "limited", "se_classification": "passive",
                "se_box1_ordinary": -25000, "se_gp_services": 20000, "se_gp_capital": 0},
     "expected_outputs": {"se_k1_box14a": 20000},
     "notes": "Passive drops the distributive share whether gain OR loss (symmetry): the (25k) loss is "
              "excluded; services GP 20k kept = 20k."},
    # ── Leg 2 — SE-base worksheet scenarios (entity-level; i1065 2025 p.45 math) ──
    {"scenario_name": "B1 — 4797 Part II gain backed out (worksheet 2)", "scenario_type": "normal", "sort_order": 11,
     "inputs": {"se_ws_1a_k1": 100000, "se_ws_1b_rental_se": 0, "se_ws_1c_k3c": 0,
                "se_ws_1d_4797_loss": 0, "se_ws_2_4797_gain": 30000},
     "expected_outputs": {"se_ws_1e": 100000, "se_ws_3a": 70000},
     "notes": "K1 100k includes a 30k ordinary 4797 gain → 1e=100k, 3a=100k−30k=70k. The gain is not SE."},
    {"scenario_name": "B2 — 4797 Part II loss added back (worksheet 1d)", "scenario_type": "normal", "sort_order": 12,
     "inputs": {"se_ws_1a_k1": 50000, "se_ws_1b_rental_se": 0, "se_ws_1c_k3c": 0,
                "se_ws_1d_4797_loss": 20000, "se_ws_2_4797_gain": 0},
     "expected_outputs": {"se_ws_1e": 70000, "se_ws_3a": 70000},
     "notes": "K1 50k already absorbed a 20k ordinary 4797 loss → 1d adds it back (positive): 1e=70k, 3a=70k."},
    {"scenario_name": "B3 — dealer/services rental IN the base (worksheet 1b)", "scenario_type": "normal", "sort_order": 13,
     "inputs": {"se_ws_1a_k1": 0, "se_ws_1b_rental_se": 40000, "se_ws_1c_k3c": 0,
                "se_ws_1d_4797_loss": 0, "se_ws_2_4797_gain": 0},
     "expected_outputs": {"se_ws_1e": 40000, "se_ws_3a": 40000},
     "notes": "K2 rental that is dealer/services-to-occupants (preparer-entered 1b) IS SE base: 3a=40k."},
    {"scenario_name": "B4 — other net rental IN the base (worksheet 1c)", "scenario_type": "normal", "sort_order": 14,
     "inputs": {"se_ws_1a_k1": 60000, "se_ws_1b_rental_se": 0, "se_ws_1c_k3c": 15000,
                "se_ws_1d_4797_loss": 0, "se_ws_2_4797_gain": 0},
     "expected_outputs": {"se_ws_1e": 75000, "se_ws_3a": 75000},
     "notes": "Sch K line 3c (other net rental) joins the base: 1e=60k+15k=75k, 3a=75k. Today's raw-box-1 "
              "compute misses this."},
    {"scenario_name": "B5 — combined base (1a incl. gain + 1b + 1c)", "scenario_type": "edge", "sort_order": 15,
     "inputs": {"se_ws_1a_k1": 80000, "se_ws_1b_rental_se": 5000, "se_ws_1c_k3c": 15000,
                "se_ws_1d_4797_loss": 0, "se_ws_2_4797_gain": 10000},
     "expected_outputs": {"se_ws_1e": 100000, "se_ws_3a": 90000},
     "notes": "1e = 80k+5k+15k = 100k; 3a = 100k − 10k 4797 gain = 90k."},
    {"scenario_name": "B6 — loss base grows by the backed-out gain (3a sign rule)", "scenario_type": "edge", "sort_order": 16,
     "inputs": {"se_ws_1a_k1": -5000, "se_ws_1b_rental_se": 0, "se_ws_1c_k3c": 0,
                "se_ws_1d_4797_loss": 0, "se_ws_2_4797_gain": 10000},
     "expected_outputs": {"se_ws_1e": -5000, "se_ws_3a": -15000},
     "notes": "The face's 'if line 1e is a loss, increase the loss by line 2': 3a = −5k − 10k = (15k). "
              "Plain subtraction realizes it."},
    {"scenario_name": "B7 — non-individual partner: no box 14a (D_SE_NONIND)", "scenario_type": "edge", "sort_order": 17,
     "inputs": {"se_partner_type": "limited", "se_classification": "active", "se_is_individual": False,
                "se_box1_ordinary": 50000, "se_gp_services": 10000, "se_gp_capital": 0},
     "expected_outputs": {"se_k1_box14a": 0, "D_SE_NONIND": True},
     "notes": "An estate/trust/corp/exempt/IRA partner is removed at worksheet 3b/4b and gets NO box 14a "
              "even if functionally active — 'Don't complete this line...' (Code A, verbatim)."},
]

# (rule_id, source_code, support_level, relevance_note)
RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-SE-CLASS", "IRC_1402", "primary", "§1402(a)(13) 'limited partner, as such' — the classification axis"),
    ("R-SE-CLASS", "CASELAW_SE_LP", "primary", "Renkemeyer/Soroban functional analysis (active vs. limited 'as such')"),
    ("R-SE-DSHARE", "IRC_1402", "primary", "§1402(a) distributive share of §702(a)(8) income in the SE base"),
    ("R-SE-DSHARE", "IRC_702", "secondary", "§702(a)(8) distributive share; §702(b) character conduit"),
    ("R-SE-DSHARE", "TREAS_REG_1402A1", "primary", "Reg §1.1402(a)-1(a)(2) distributive share of trade/business"),
    ("R-SE-GPSVC", "IRC_707C", "primary", "§707(c) guaranteed payments for services"),
    ("R-SE-GPSVC", "IRC_1402", "secondary", "§1402(a)(13) carve-back retains services GP for all partner types"),
    ("R-SE-GPSVC", "TREAS_REG_1402A1", "secondary", "Reg §1.1402(a)-1(b) payments for services are business income"),
    ("R-SE-GPCAP", "TREAS_REG_1402A1", "primary", "Reg §1.1402(a)-1(b) use of capital → business income (Decision 4)"),
    ("R-SE-GPCAP", "IRC_1402", "secondary", "§1402(a)(13) services-only carve-back (capital GP excluded if passive)"),
    ("R-SE-DEFAULT", "CASELAW_SE_LP", "primary", "11th Cir. (GA) unresolved → Tax Court functional posture → active default"),
    ("R-SE-DEFAULT", "IRC_1402", "secondary", "§1402(a)(13) — the provision whose application is undetermined"),
    ("R-SE-RENTAL", "IRC_1402", "primary", "§1402(a)(1) rentals from real estate excluded"),
    ("R-SE-RENTAL", "TREAS_REG_1402A4", "primary", "Reg §1.1402(a)-4 rentals excluded unless real-estate dealer"),
    ("R-SE-PORT", "IRC_1402", "primary", "§1402(a)(2) dividends/interest; §1402(a)(3) capital gains excluded"),
    ("R-SE-LOSS", "IRC_1402", "secondary", "§1402(a) 'income OR loss' — symmetry for active partners"),
    ("R-SE-LOSS", "IRS_2025_1065_SEWKST", "secondary", "SE Worksheet line 1a base can be negative"),
    ("R-SE-14A-ENT", "IRS_2025_1065_SEWKST", "primary", "SE Worksheet: entity line 14a = line 3c + 4c (bottom-up)"),
    # Leg 2 — base rules
    ("R-SE-BASE-1B", "IRS_2025_1065_SEWKST", "primary", "Line 1b instructions: dealer / services-to-occupants rentals"),
    ("R-SE-BASE-1B", "IRC_1402", "secondary", "§1402(a)(1) rental exclusion + its real-estate-dealer exception"),
    ("R-SE-BASE-1B", "TREAS_REG_1402A4", "secondary", "Reg §1.1402(a)-4 rentals excluded unless dealer"),
    ("R-SE-BASE-1C", "IRS_2025_1065_SEWKST", "primary", "Worksheet line 1c: other net rental (Sch K 3c) in the base"),
    ("R-SE-BASE-4797", "IRS_2025_1065_SEWKST", "primary", "Worksheet lines 1d/2: Form 4797 Part II line 17 adjustment"),
    ("R-SE-BASE-3A", "IRS_2025_1065_SEWKST", "primary", "Worksheet lines 1e/3a: the base composition"),
    ("R-SE-NONIND", "IRS_2025_1065_SEWKST", "primary", "Worksheet 3b/4b + Code A: no box 14a for non-individual partners"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS (§9). FLOW-14A-SE is FUTURE → status 'disabled' (integrity gate skips it).
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "RECON-14A", "assertion_type": "reconciliation", "entity_types": ["1065"], "status": "active",
     "title": "Entity Sch K line 14a = Σ (per-partner K-1 box 14a)",
     "description": ("Entity Schedule K line 14a is derived BOTTOM-UP from the per-partner determinations, "
                     "not computed separately. Replaces the current independent K14a = K1 + K4c path "
                     "(compute.py:288). A break fires D_SE_RECON."),
     "definition": {"kind": "reconciliation", "form": "1065_SE",
                    "formula": "sched_k_line14a == sum(k1_box14a over partners)",
                    "note": "bottom-up derivation is the spec requirement (§9)"},
     "bug_reference": "compute.py:288 independent K14a = K1 + K4c path (computed separately from partners)",
     "sort_order": 1},
    {"assertion_id": "INV-CHAR", "assertion_type": "table_invariant", "entity_types": ["1065"], "status": "active",
     "title": "SE 14a excludes rental (box 2) and portfolio (boxes 5/6/8/9) for every partner",
     "description": ("Table invariant: for every partner, the SE box 14a excludes box 2 (rental real "
                     "estate) and boxes 5/6/8/9 (portfolio — interest/dividends/capital gains), regardless "
                     "of classification. §1402(a)(1)/(a)(2)/(a)(3)."),
     "definition": {"kind": "table_invariant", "form": "1065_SE",
                    "invariant": "for every partner, se_k1_box14a excludes se_box2_rental and se_portfolio"},
     "bug_reference": "",
     "sort_order": 2},
    {"assertion_id": "INV-SE-BASE", "assertion_type": "table_invariant", "entity_types": ["1065"], "status": "active",
     "title": "SE base composition: 1e = 1a+1b+1c+1d; 3a = 1e − 2",
     "description": ("Leg 2 (i1065 2025 p.45 worksheet). Bug it catches: the base reverting to raw box 1 "
                     "(dropping the 1b/1c rental inclusions or the 4797 1d/2 adjustment), or the 3a sign "
                     "rule mishandled when 1e is a loss."),
     "definition": {"kind": "table_invariant", "form": "1065_SE",
                    "invariant": "se_ws_1e == se_ws_1a_k1 + se_ws_1b_rental_se + se_ws_1c_k3c + se_ws_1d_4797_loss; "
                                 "se_ws_3a == se_ws_1e - se_ws_2_4797_gain"},
     "bug_reference": "tts compute reads raw k1_data['1'] as the SE base (spec §4b gaps)",
     "sort_order": 4},
    {"assertion_id": "FLOW-14A-SE", "assertion_type": "flow_assertion", "entity_types": ["1065"], "status": "disabled",
     "title": "K-1 box 14a → partner's Schedule SE (FUTURE — inactive)",
     "description": ("FUTURE / inactive. When the K-1→1040 flow-through is built, box 14a carries to the "
                     "partner's Schedule SE. Authored NOW (before wiring that flow-through) so the SE "
                     "determination is correct before it can propagate to individual returns. Marked "
                     "'disabled' so the integrity gate does not exercise it until the flow-through exists."),
     "definition": {"kind": "flow_assertion", "form": "1065_SE",
                    "checks": [{"source_line": "14a", "must_write_to": ["SCHEDULE_SE.2"]}],
                    "status_note": "FUTURE — gated on the K-1→1040 flow-through being built"},
     "bug_reference": "",
     "sort_order": 3},
]


class Command(BaseCommand):
    help = ("Load the 1065_SE spec (Form 1065 Schedule K / K-1 line 14a self-employment). "
            "Faithful translation of the LOCKED 1065_se_line14a_spec.md. Refuses until READY_TO_SEED=True.")

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad 1065_SE (Schedule K / K-1 line 14a — SECA)\n"))
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
                empty.append(f"1065_SE.{name}")
        if not READY_TO_SEED or empty:
            still_empty = "\n  ".join(f"- {n}" for n in empty) or "(all populated)"
            raise CommandError(
                "\nREFUSING TO SEED 1065_SE: not cleared to seed.\n\n"
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
        disabled = [a["assertion_id"] for a in FLOW_ASSERTIONS if a.get("status") == "disabled"]
        self.stdout.write(f"  {len(FLOW_ASSERTIONS)} flow assertions "
                          f"(disabled: {', '.join(disabled) or 'none'})")

    def _report_totals(self, form):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(f"TaxForms: {TaxForm.objects.count()} | FlowAssertions: {FlowAssertion.objects.count()}")
        uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
        self.stdout.write("1065_SE: all rules cited" if not uncited
                          else self.style.WARNING(f"1065_SE uncited rules: {len(uncited)}"))
