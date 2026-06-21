"""Load the SCHEDULE_K1 (recipient K-1 router) spec + amend SCHEDULE_E with its
page-2 (Parts II-V) line structure.  Effort #5 (UI Batch #2), 2026-06-21.

THE RECIPIENT-SIDE K-1: a 1040 taxpayer who is a partner (Form 1065 K-1),
S-corp shareholder (Form 1120-S K-1), or estate/trust beneficiary (Form 1041
K-1) routes each K-1 box to its destination form.  This is the TaxWise/Lacerte
"full router" model (Ken Decision 2, 2026-06-21): a per-entity K-1 screen that
routes EVERY box, not just the Schedule-E-bound amounts.

NOT to be confused with `k1_allocator.py` (tts-tax-app) — that is the ISSUER
side (allocates a partnership's Schedule K to its partners).  This spec is the
RECIPIENT side (the individual partner/shareholder/beneficiary's 1040).

CONSTANTS/CODES VERIFIED 2026-06-21 against the actual 2025 IRS PDFs + the 2025
K-1 instruction booklets (tts-tax-app `server/specs/_schedule_k1_source_brief.md`):
  - Schedule E page 2 (f1040se.pdf 2025): Part II line 28 cols (g) passive loss /
    (h) passive income / (i) nonpassive loss / (j) §179 / (k) nonpassive income;
    line 30 = (h)+(k), line 31 = (g)+(i)+(j), line 32 = 30+31.  Part III line 33
    cols (c) passive deduction-loss / (d) passive income / (e) deduction-loss /
    (f) other income; line 35 = (d)+(f), line 36 = (c)+(e), line 37 = 35+36.
    Part IV (REMIC) 38/39.  Part V: line 40 = Form 4835; **LINE 41 = combine 26,
    32, 37, 39, 40 → Schedule 1 line 5** (NOT line 40 — the brainstorm spec was
    wrong; the form face is authoritative).  Line 42 farm/fishing recon; 43 RE-pro.
  - 1065 K-1 (f1065sk1 + i1065sk1): box 14 **code A** = net SE earnings → Sch SE;
    box 20 **code Z** = §199A info → Form 8995.
  - 1120-S K-1 (f1120ssk + i1120ssk): box 17 **code V** = §199A info → Form 8995;
    "S corporation income … isn't subject to self-employment tax" (no SE flow).
  - 1041 K-1 (f1041sk1 codes table): box 1→1040 2b, 2a→3b, 2b→3a, 3→Sch D 5,
    4a→Sch D 12, box 5→Sch E line 33 (f), boxes 6/7/8→Sch E line 33 (d)/(f),
    box 14 **code I** = §199A info → Form 8995.
  - Schedule D K-1 lines: net ST → line 5; net LT → line 12 (1041 face + i1065sk1).
  - Form 8995: §199A QBI → line 2; §199A REIT div + PTP → line 6 (8995_spec.json).

KEN'S 6 SCOPE DECISIONS (2026-06-21, AskUserQuestion; DECISIONS.md):
  1. Schedule E page 2 (K-1) FIRST, Schedule F second (separate units).
  2. FULL ROUTER (route every box).
  3. Sources = 1065 partner + 1120-S shareholder + 1041 beneficiary; REMIC RED-defer.
  4. K-1 PASSIVE LOSSES RED-deferred in v1 (route passive income + all nonpassive;
     a passive loss → RED "limit via Form 8582 manually").
  5. §199A QBI → Form 8995 IN v1.
  6. Partnership SE (1065 box 14A) → Schedule SE IN v1; S-corp/1041 no SE.

ARCHITECTURE (my call — confirm nothing tax-law here):
  - Form 1 SCHEDULE_K1 (NEW): the recipient-K-1 router — per-K-1 box facts keyed by
    SEMANTIC role (the same destination across the three sources, per-source box noted),
    + owner + material-participation, + the box→destination routing rules + v1 RED-defer
    diagnostics + the cross-form routing flow assertions (Sch B / Sch D / Sch SE / 8995).
  - Form 2 SCHEDULE_E (AMENDED additively): add the page-2 lines (27-43) + the Part II/III
    aggregation rules + the **line 41 = 26+32+37+39+40 → Schedule 1 line 5** summary.  Part I
    (lines A-26) is untouched (update_or_create is additive); the form title/notes update to
    reflect Parts I-V.  The existing FA-1040-SCHE-01 (line 26 → SCH_1.5) is REPOINTED to line
    41 (line 26 now flows into line 41).

SAFETY GUARD: READY_TO_SEED stays False until Ken's review walk (the box→destination
routing table per source, the passive/nonpassive split, the line-41 summary correction,
the §199A/SE flows, and the complete v1 RED-defer list).
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


READY_TO_SEED = True  # FLIPPED 2026-06-21 — Ken approved the review walk ("Approve & seed as authored").


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_ENTITY_TYPES = ["1040"]
FORM_STATUS = "draft"


# ═══════════════════════════════════════════════════════════════════════════
# THE MATH (the integrity gate re-types this independently; they share no math).
#
# v1 simplification (Decision 4): K-1 passive LOSSES are RED-deferred, never
# placed in Schedule E col (g)/(c).  So in v1 the only passive amounts that reach
# a column are passive INCOME (cols (h)/(d)).  Nonpassive income/loss flow in
# full (cols (i)/(k) and (e)/(f)).  §179 is a deduction in col (j).
# No constants, no year keys (§61/§702/§1366/§652 character pass-through; the only
# year-sensitive number is the 8995 threshold, which lives in the 8995 spec).
# ═══════════════════════════════════════════════════════════════════════════


def _num(x) -> float:
    return float(x if x is not None else 0)


def route_part_ii(k1s) -> dict:
    """Schedule E Part II (partnerships + S corps) page-2 aggregation.
    Each k1: {source_type, material_participation(bool), ordinary, net_rental_re,
    other_rental, guaranteed_payments, section_179}.  Returns cols + lines 30/31/32
    and the list of passive-loss RED-defer flags.  v1: passive loss excluded (RED)."""
    col_g = col_h = col_i = col_j = col_k = 0.0
    passive_loss_deferred = []
    for k in k1s:
        if k.get("source_type") not in ("1065", "1120s"):
            continue
        s179 = _num(k.get("section_179"))
        col_j += s179
        # Guaranteed payments (1065) are ALWAYS nonpassive income → col (k).
        gp = _num(k.get("guaranteed_payments"))
        col_k += gp
        # The trade/business + rental net for this K-1 (ex-GP, ex-179).
        net = (_num(k.get("ordinary")) + _num(k.get("net_rental_re"))
               + _num(k.get("other_rental")))
        if k.get("material_participation"):          # nonpassive
            if net >= 0:
                col_k += net
            else:
                col_i += net                          # negative
        else:                                         # passive
            if net >= 0:
                col_h += net
            else:
                passive_loss_deferred.append(net)     # RED-defer; not placed in (g)
    line30 = col_h + col_k
    line31 = col_g + col_i + col_j                     # (col_i negative; col_j positive deduction)
    # Form: line 31 is "Add columns (g), (i), and (j)" — (j) §179 is a deduction
    # entered as a positive number, then line 31 is shown in parentheses (a
    # subtraction).  So the SIGNED contribution to line 32 is col_g + col_i − col_j.
    line31_signed = col_g + col_i - col_j
    line32 = line30 + line31_signed
    return {"g": col_g, "h": col_h, "i": col_i, "j": col_j, "k": col_k,
            "30": line30, "31": -line31_signed if line31_signed < 0 else line31_signed,
            "31_signed": line31_signed, "32": line32,
            "passive_loss_deferred": passive_loss_deferred}


def route_part_iii(k1s) -> dict:
    """Schedule E Part III (estates + trusts) page-2 aggregation.
    Each 1041 k1: {material_participation, business(=box6), net_rental_re(=box7),
    other_rental(=box8), other_portfolio(=box5)}.  Cols (c)/(d)/(e)/(f); lines
    35/36/37.  v1: passive loss → RED-defer (not placed in (c))."""
    col_c = col_d = col_e = col_f = 0.0
    passive_loss_deferred = []
    for k in k1s:
        if k.get("source_type") != "1041":
            continue
        # Box 5 other portfolio/nonbusiness income → col (f) (nonpassive, per the K-1 face).
        col_f += _num(k.get("other_portfolio"))
        net = (_num(k.get("business")) + _num(k.get("net_rental_re"))
               + _num(k.get("other_rental")))
        if k.get("material_participation"):           # nonpassive
            if net >= 0:
                col_f += net
            else:
                col_e += net                          # negative
        else:                                         # passive
            if net >= 0:
                col_d += net
            else:
                passive_loss_deferred.append(net)     # RED-defer
    line35 = col_d + col_f
    line36 = col_c + col_e                             # negative (loss/deduction)
    line37 = line35 + line36
    return {"c": col_c, "d": col_d, "e": col_e, "f": col_f,
            "35": line35, "36": line36, "37": line37,
            "passive_loss_deferred": passive_loss_deferred}


def schedule_e_line41(line26, line32, line37, line39=0.0, line40=0.0) -> float:
    """Schedule E line 41 = combine lines 26, 32, 37, 39, 40 → Schedule 1 line 5.
    line26 = Part I (rentals/royalties, already built); 39 = REMIC (v1 0);
    40 = Form 4835 (v1 0)."""
    return _num(line26) + _num(line32) + _num(line37) + _num(line39) + _num(line40)


def route_interest_dividends(k1s) -> dict:
    """K-1 interest/dividends → 1040 (Schedule B).  Source boxes: interest
    1065 b5 / 1120-S b4 / 1041 b1 → line 2b; ordinary div 6a/5a/2a → 3b; qualified
    div 6b/5b/2b → 3a."""
    return {
        "2b": sum(_num(k.get("interest")) for k in k1s),
        "3b": sum(_num(k.get("ordinary_dividends")) for k in k1s),
        "3a": sum(_num(k.get("qualified_dividends")) for k in k1s),
    }


def route_capital_gains(k1s) -> dict:
    """K-1 capital gains → Schedule D.  Net ST (1065 b8 / 1120-S b7 / 1041 b3) →
    line 5; net LT (1065 9a / 1120-S 8a / 1041 4a) → line 12."""
    return {
        "schd_5": sum(_num(k.get("net_st_capital_gain")) for k in k1s),
        "schd_12": sum(_num(k.get("net_lt_capital_gain")) for k in k1s),
    }


def route_se_and_qbi(k1s) -> dict:
    """1065 box 14A net SE earnings → Schedule SE line 2 (per proprietor; S-corp +
    1041 have NO SE).  §199A QBI (20Z/17V/14I) → Form 8995 line 2; §199A REIT div +
    PTP → 8995 line 6."""
    se = sum(_num(k.get("se_earnings")) for k in k1s if k.get("source_type") == "1065")
    qbi = sum(_num(k.get("section_199a_qbi")) for k in k1s)
    reit_ptp = sum(_num(k.get("section_199a_reit_ptp")) for k in k1s)
    return {"sch_se_2": se, "f8995_2": qbi, "f8995_6": reit_ptp}


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("k1_passthrough", "Recipient Schedule K-1 (partner / S-corp shareholder / estate-trust beneficiary) — box→destination routing to Schedule E page 2, Schedule B/D, Schedule SE, Form 8995"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_1040_FORM",
    "IRS_2025_1040_INSTR",
    "IRS_2025_SCHE_INSTR",     # from load_1040_schedule_e
    "IRS_2025_F8582_INSTR",    # passive loss limitation
    "IRC_469",                 # passive activity
]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_1065_K1_INSTR",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Partner's Instructions for Schedule K-1 (Form 1065)",
        "citation": "Partner's Instructions for Schedule K-1 (Form 1065) (2025); i1065sk1",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i1065sk1.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": "Partner K-1 box routing: box 1/2/3 → Sch E line 28 cols (g)/(h)/(i)/(k) by material participation; box 4a/4b guaranteed payments → col (k); box 5/6a/6b → Sch B; box 7 → Sch E Part I line 4; box 8/9a → Sch D line 5/12; box 12 §179 → col (j); box 14 code A net SE → Sch SE; box 20 code Z → §199A. REQUIRES HUMAN REVIEW: confirm box codes vs the 2025 K-1 (pinned from f1065sk1.pdf + i1065sk1 at the spec leg).",
        "topics": ["k1_passthrough"],
        "excerpts": [
            {
                "excerpt_label": "Box 1 → Sch E line 28 columns (passive vs material participation)",
                "location_reference": "i1065sk1 (2025), Box 1 Ordinary Business Income (Loss)",
                "excerpt_text": (
                    "1. Report box 1 income (loss) from partnership trade or business activities in which you "
                    "materially participated in column (i) or (k) of Schedule E (Form 1040), line 28. 2. … did not "
                    "materially participate … a. If income is reported in box 1, report the income in column (h) … "
                    "b. If a loss is reported in box 1, follow the Instructions for Form 8582 … column (g)."
                ),
                "summary_text": "Box 1 (and 2/3): material participation → col (i) loss / (k) income; passive income → (h); passive loss → (g) via Form 8582.",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Box 14 code A net SE earnings → Schedule SE; codes B/C optional methods",
                "location_reference": "i1065sk1 (2025), Box 14 Self-Employment Earnings (Loss)",
                "excerpt_text": (
                    "Code A. Net earnings (loss) from self-employment. If you're a general partner, reduce this "
                    "amount before entering it on Schedule SE (Form 1040) by any section 179 expense deduction "
                    "claimed, unreimbursed partnership expenses claimed, and depletion … Code B. Gross farming or "
                    "fishing income … Code C. Gross nonfarm income … nonfarm optional method on Schedule SE Part II."
                ),
                "summary_text": "Box 14 code A = net SE earnings → Schedule SE; codes B/C = gross farm/nonfarm for the optional methods (RED-defer in v1).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Box 20 code Z — Section 199A information",
                "location_reference": "i1065sk1 (2025), Box 20 code Z",
                "excerpt_text": (
                    "Code Z. Section 199A information. Generally, you may be allowed a deduction of up to 20% of "
                    "your net qualified business income (QBI) plus 20% of your qualified REIT dividends, also known "
                    "as section 199A dividends, and qualified PTP income from your partnership."
                ),
                "summary_text": "Box 20 code Z = §199A information (QBI + REIT dividends + PTP) → Form 8995 / 8995-A.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_1120S_K1_INSTR",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Shareholder's Instructions for Schedule K-1 (Form 1120-S)",
        "citation": "Shareholder's Instructions for Schedule K-1 (Form 1120-S) (2025); i1120ssk",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i1120ssk.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": "S-corp shareholder K-1: box 1/2/3 → Sch E line 28 (same passive/material logic); box 4/5a/5b → Sch B; box 6 royalties → Sch E Part I; box 7/8a → Sch D 5/12; box 11 §179 → col (j); box 17 code V → §199A. NO self-employment tax on the shareholder's share. REQUIRES HUMAN REVIEW: confirm vs the 2025 1120-S K-1.",
        "topics": ["k1_passthrough"],
        "excerpts": [
            {
                "excerpt_label": "S-corp share is not self-employment income",
                "location_reference": "i1120ssk (2025), General Information",
                "excerpt_text": (
                    "Your share of S corporation income isn't self-employment income and it isn't subject to "
                    "self-employment tax."
                ),
                "summary_text": "An S-corp shareholder's distributive share is NOT subject to SE tax (no Schedule SE flow).",
                "is_key_excerpt": True,
            },
            {
                "excerpt_label": "Box 17 code V — Section 199A information",
                "location_reference": "i1120ssk (2025), Box 17 code V",
                "excerpt_text": (
                    "Code V. Section 199A information. Generally, you may be allowed a deduction of up to 20% of "
                    "your net qualified business income (QBI) plus 20% of your qualified REIT dividends, also known "
                    "as section 199A dividends, and qualified publicly traded partnership (PTP) income."
                ),
                "summary_text": "Box 17 code V = §199A information → Form 8995 / 8995-A.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRS_2025_1041_K1_INSTR",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "2025 Schedule K-1 (Form 1041) for a Beneficiary — box layout + codes table",
        "citation": "Schedule K-1 (Form 1041) (2025) page-2 codes table; Instructions for Sch K-1 (Form 1041)",
        "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/i1041sk1.pdf",
        "current_status": "active",
        "is_substantive_authority": False,
        "is_filing_authority": True,
        "trust_score": 9.50,
        "requires_human_review": True,
        "notes": "1041 beneficiary K-1 (its own printed 'Report on' table): box 1→1040 2b; 2a→3b; 2b→3a; 3→Sch D 5; 4a→Sch D 12; box 5 other portfolio→Sch E line 33 (f); boxes 6/7/8→Sch E line 33 (d)/(f); box 14 code I→§199A; code F→Sch E line 42. REQUIRES HUMAN REVIEW: confirm vs the 2025 1041 K-1.",
        "topics": ["k1_passthrough"],
        "excerpts": [
            {
                "excerpt_label": "1041 K-1 'Report on' table (boxes 1-8, 14I)",
                "location_reference": "f1041sk1 (2025) page 2, codes/Report-on table",
                "excerpt_text": (
                    "1. Interest income → Form 1040 line 2b. 2a. Ordinary dividends → line 3b. 2b. Qualified "
                    "dividends → line 3a. 3. Net short-term capital gain → Schedule D, line 5. 4a. Net long-term "
                    "capital gain → Schedule D, line 12. 5. Other portfolio and nonbusiness income → Schedule E, "
                    "line 33, column (f). 6. Ordinary business income / 7. Net rental real estate income / 8. Other "
                    "rental income → Schedule E, line 33, column (d) or (f). 14 code I. Section 199A information."
                ),
                "summary_text": "1041 K-1: interest/dividends/cap-gains → 1040/Sch D; boxes 5/6/7/8 → Sch E Part III line 33 cols (d)/(f); box 14 code I = §199A.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_199A",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §199A — Qualified Business Income Deduction",
        "citation": "26 U.S.C. §199A (20% QBI deduction; §199A(b) combined amount; §199A(e)(3) qualified REIT dividends and PTP income)",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/199A",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "The 20% QBI deduction. A K-1's §199A info (QBI, REIT dividends, PTP income) is the recipient's input to Form 8995/8995-A. v1 routes QBI → 8995 line 2 and REIT/PTP → 8995 line 6 (the existing Topic-8 8995 engine).",
        "topics": ["k1_passthrough"],
        "excerpts": [
            {
                "excerpt_label": "§199A 20% deduction on QBI + REIT/PTP",
                "location_reference": "26 U.S.C. §199A(a),(b),(e)(3)",
                "excerpt_text": (
                    "There shall be allowed as a deduction an amount equal to … 20 percent of the qualified business "
                    "income … plus … 20 percent of the aggregate amount of the qualified REIT dividends and qualified "
                    "publicly traded partnership income."
                ),
                "summary_text": "§199A: 20% of QBI plus 20% of qualified REIT dividends and qualified PTP income.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_1402",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §1402 — Net Earnings From Self-Employment",
        "citation": "26 U.S.C. §1402(a) (a partner's distributive share of partnership trade-or-business income is SE earnings); §1402(a)(13) limited partner exclusion",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/1402",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "A general partner's distributive share + guaranteed payments are SE earnings (1065 box 14A) → Schedule SE. §1402(a)(13): a limited partner's share (other than guaranteed payments for services) is excluded. An S-corp shareholder's share is NOT SE income (§1402 covers partners, not S-corp shareholders).",
        "topics": ["k1_passthrough"],
        "excerpts": [
            {
                "excerpt_label": "§1402(a) partner's distributive share is SE earnings",
                "location_reference": "26 U.S.C. §1402(a), (a)(13)",
                "excerpt_text": (
                    "The term 'net earnings from self-employment' means … the distributive share (whether or not "
                    "distributed) of income or loss … from any trade or business carried on by a partnership of which "
                    "he is a member … there shall be excluded the distributive share of any item of income or loss "
                    "of a limited partner, as such, other than guaranteed payments … for services actually rendered."
                ),
                "summary_text": "Partner's trade/business distributive share = SE earnings (box 14A → Sch SE); a limited partner excludes all but guaranteed payments for services.",
                "is_key_excerpt": True,
            },
        ],
    },
    {
        "source_code": "IRC_PASSTHROUGH_CHARACTER",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED",
        "entity_type_code": "1040",
        "tax_year_start": 2025,
        "tax_year_end": 2025,
        "title": "IRC §702 / §1366 / §652 & §662 — Character pass-through to the recipient",
        "citation": "26 U.S.C. §702(b) (partner), §1366(b) (S-corp shareholder), §652(b)/§662(b) (trust/estate beneficiary) — each item retains its character in the recipient's hands",
        "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/702",
        "current_status": "active",
        "is_substantive_authority": True,
        "is_filing_authority": False,
        "trust_score": 10.00,
        "requires_human_review": False,
        "notes": "The conduit/character rule that makes the K-1 router work: each K-1 item keeps the character it had at the entity (interest stays interest, LT gain stays LT gain, etc.) when reported on the recipient's 1040. §702(b) partners; §1366(b) S-corp shareholders; §652(b)/§662(b) trust/estate beneficiaries.",
        "topics": ["k1_passthrough"],
        "excerpts": [
            {
                "excerpt_label": "Character retained in the recipient's hands",
                "location_reference": "26 U.S.C. §702(b); §1366(b); §652(b)/§662(b)",
                "excerpt_text": (
                    "The character of any item of income, gain, loss, deduction, or credit included in a partner's "
                    "distributive share … shall be determined as if such item were realized directly from the source "
                    "from which realized by the partnership, or incurred in the same manner."
                ),
                "summary_text": "Each K-1 item keeps its entity-level character on the recipient's return (the conduit rule).",
                "is_key_excerpt": True,
            },
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_1065_K1_INSTR", "SCHEDULE_K1", "governs"),
    ("IRS_2025_1120S_K1_INSTR", "SCHEDULE_K1", "governs"),
    ("IRS_2025_1041_K1_INSTR", "SCHEDULE_K1", "governs"),
    ("IRC_199A", "SCHEDULE_K1", "informs"),
    ("IRC_1402", "SCHEDULE_K1", "informs"),
    ("IRC_PASSTHROUGH_CHARACTER", "SCHEDULE_K1", "informs"),
    ("IRS_2025_SCHE_INSTR", "SCHEDULE_K1", "governs"),
    ("IRS_2025_SCHE_INSTR", "SCHEDULE_E", "governs"),
    ("IRC_469", "SCHEDULE_K1", "informs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 1: SCHEDULE_K1 (recipient K-1 router)
# ═══════════════════════════════════════════════════════════════════════════

K1_IDENTITY = {
    "form_number": "SCHEDULE_K1",
    "form_title": "Schedule K-1 (recipient) — Partner / S-corp Shareholder / Beneficiary pass-through router (TY2025)",
    "notes": (
        "Effort #5 (UI Batch #2), 2026-06-21. The RECIPIENT-side K-1: a 1040 taxpayer's "
        "share from a 1065 partnership, 1120-S S corporation, or 1041 estate/trust. A "
        "per-entity document (the ScheduleC / CapitalTransaction / RetirementDistribution "
        "precedent) routing every box to its destination form (Decision 2 full router). "
        "Schedule-E-bound amounts → Schedule E page 2 (Part II partnerships/S-corps line 28; "
        "Part III estates/trusts line 33) → line 41 → Schedule 1 line 5. Interest/dividends → "
        "Schedule B (1040 2b/3a/3b); capital gains → Schedule D 5/12; royalties → Schedule E "
        "Part I line 4; 1065 box 14A SE earnings → Schedule SE; §199A → Form 8995. Passive/"
        "nonpassive by preparer material-participation assertion (no §469 engine). v1 RED-defers "
        "K-1 passive LOSSES, §1231 (4797), 28%/§1250 (SDTW), AMT (6251), basis/at-risk (6198), "
        "REMIC, Form 4835, foreign/K-3/credits — each fires a RED, never a silent gap. NOT "
        "k1_allocator.py (issuer side)."
    ),
}

K1_FACTS: list[dict] = [
    # ── Document identity / classification (per K-1 row) ──
    {"fact_key": "k1_source_type", "label": "Source entity type (1065 / 1120s / 1041)",
     "data_type": "string", "default_value": "1065", "sort_order": 1,
     "notes": "Drives box→destination mapping + Part II (1065/1120-S) vs Part III (1041) + SE eligibility."},
    {"fact_key": "k1_owner", "label": "Owner (taxpayer / spouse / joint)",
     "data_type": "string", "default_value": "taxpayer", "sort_order": 2, "notes": "Per-document owner."},
    {"fact_key": "k1_entity_name", "label": "Entity name (partnership / S corp / estate-trust)",
     "data_type": "string", "sort_order": 3, "notes": "Sch E line 28(a)/33(a). Structured (e-file)."},
    {"fact_key": "k1_entity_ein", "label": "Entity EIN",
     "data_type": "string", "sort_order": 4, "notes": "Sch E line 28(d)/33(b). Structured (e-file)."},
    {"fact_key": "k1_material_participation", "label": "Materially participated (nonpassive)?",
     "data_type": "boolean", "default_value": "true", "sort_order": 5,
     "notes": "Preparer assertion (no §469 engine). true → nonpassive cols (i)/(k) / (e)/(f); false → passive (h)/(d), passive loss RED-defer."},
    {"fact_key": "k1_is_ptp", "label": "Publicly traded partnership (1065 item D)?",
     "data_type": "boolean", "default_value": "false", "sort_order": 6,
     "notes": "PTP passive rules differ (per-PTP netting). v1 flags a PTP loss (D_K1_PTP) — not auto-netted."},
    # ── Schedule-E-bound boxes (semantic; per-source box in the label) ──
    {"fact_key": "k1_ordinary", "label": "Ordinary business income/(loss) [1065 b1 / 1120-S b1 / 1041 b6]",
     "data_type": "decimal", "default_value": "0", "sort_order": 10, "notes": "→ Sch E p2 (Part II col (i)/(h)/(k); 1041 Part III col (d)/(e)/(f))."},
    {"fact_key": "k1_net_rental_re", "label": "Net rental real estate income/(loss) [1065 b2 / 1120-S b2 / 1041 b7]",
     "data_type": "decimal", "default_value": "0", "sort_order": 11, "notes": "→ Sch E p2 (passive per se unless RE-pro+material)."},
    {"fact_key": "k1_other_rental", "label": "Other net rental income/(loss) [1065 b3 / 1120-S b3 / 1041 b8]",
     "data_type": "decimal", "default_value": "0", "sort_order": 12, "notes": "→ Sch E p2."},
    {"fact_key": "k1_guaranteed_payments", "label": "Guaranteed payments [1065 b4c]",
     "data_type": "decimal", "default_value": "0", "sort_order": 13, "notes": "1065 only. Nonpassive → col (k). Also SE for a general partner."},
    {"fact_key": "k1_section_179", "label": "Section 179 deduction [1065 b12 / 1120-S b11]",
     "data_type": "decimal", "default_value": "0", "sort_order": 14, "notes": "→ Sch E col (j) (via Form 4562). Entered positive; a deduction."},
    {"fact_key": "k1_other_portfolio", "label": "Other portfolio & nonbusiness income [1041 b5]",
     "data_type": "decimal", "default_value": "0", "sort_order": 15, "notes": "1041 only → Sch E line 33 col (f)."},
    # ── Schedule B-bound ──
    {"fact_key": "k1_interest", "label": "Interest income [1065 b5 / 1120-S b4 / 1041 b1]",
     "data_type": "decimal", "default_value": "0", "sort_order": 20, "notes": "→ 1040 line 2b (Schedule B)."},
    {"fact_key": "k1_ordinary_dividends", "label": "Ordinary dividends [1065 6a / 1120-S 5a / 1041 2a]",
     "data_type": "decimal", "default_value": "0", "sort_order": 21, "notes": "→ 1040 line 3b."},
    {"fact_key": "k1_qualified_dividends", "label": "Qualified dividends [1065 6b / 1120-S 5b / 1041 2b]",
     "data_type": "decimal", "default_value": "0", "sort_order": 22, "notes": "→ 1040 line 3a (subset of 3b)."},
    {"fact_key": "k1_royalties", "label": "Royalties [1065 b7 / 1120-S b6]",
     "data_type": "decimal", "default_value": "0", "sort_order": 23, "notes": "→ Schedule E Part I line 4 (existing royalty machinery)."},
    # ── Schedule D-bound ──
    {"fact_key": "k1_net_st_capital_gain", "label": "Net short-term capital gain/(loss) [1065 b8 / 1120-S b7 / 1041 b3]",
     "data_type": "decimal", "default_value": "0", "sort_order": 30, "notes": "→ Schedule D line 5."},
    {"fact_key": "k1_net_lt_capital_gain", "label": "Net long-term capital gain/(loss) [1065 9a / 1120-S 8a / 1041 4a]",
     "data_type": "decimal", "default_value": "0", "sort_order": 31, "notes": "→ Schedule D line 12."},
    # ── Schedule SE / Form 8995 ──
    {"fact_key": "k1_se_earnings", "label": "Net self-employment earnings [1065 box 14 code A]",
     "data_type": "decimal", "default_value": "0", "sort_order": 40, "notes": "1065 only → Schedule SE line 2 (general partner; §1402)."},
    {"fact_key": "k1_section_199a_qbi", "label": "§199A QBI [1065 20Z / 1120-S 17V / 1041 14I]",
     "data_type": "decimal", "default_value": "0", "sort_order": 41, "notes": "→ Form 8995 line 2 (QBI component)."},
    {"fact_key": "k1_section_199a_reit_ptp", "label": "§199A REIT dividends + PTP income",
     "data_type": "decimal", "default_value": "0", "sort_order": 42, "notes": "→ Form 8995 line 6 (qualified REIT dividends + PTP)."},
    # ── RED-defer presence (v1 no-silent-gap flags) ──
    {"fact_key": "k1_section_1231", "label": "Net §1231 gain/(loss) [1065 b10 / 1120-S b9]",
     "data_type": "decimal", "default_value": "0", "sort_order": 50, "notes": "RED-defer → Form 4797 (no compute_4797 on 1040)."},
    {"fact_key": "k1_collectibles_28", "label": "Collectibles (28%) gain [1065 9b / 1120-S 8b / 1041 4b]",
     "data_type": "decimal", "default_value": "0", "sort_order": 51, "notes": "RED-defer → Schedule D Tax Worksheet (deferred)."},
    {"fact_key": "k1_unrecap_1250", "label": "Unrecaptured §1250 gain [1065 9c / 1120-S 8c / 1041 4c]",
     "data_type": "decimal", "default_value": "0", "sort_order": 52, "notes": "RED-defer → SDTW (deferred)."},
    {"fact_key": "k1_has_amt_items", "label": "AMT items present [1065 b17 / 1120-S b15 / 1041 b12]?",
     "data_type": "boolean", "default_value": "false", "sort_order": 53, "notes": "RED-defer → Form 6251 (AMT out of sprint)."},
    {"fact_key": "k1_basis_at_risk_limited", "label": "Basis / at-risk limited (6198 / basis wksht)?",
     "data_type": "boolean", "default_value": "false", "sort_order": 54, "notes": "RED-defer — preparer asserts the deductible amount; no §704(d)/§1366(d)/§465 engine."},
    {"fact_key": "k1_other_income", "label": "Other income/(loss) [1065 b11 / 1120-S b10]",
     "data_type": "decimal", "default_value": "0", "sort_order": 55, "notes": "RED-defer (statement-driven; varies by code)."},
    {"fact_key": "k1_foreign_taxes", "label": "Foreign taxes / K-3 attached [1065 b21/b16 / 1120-S b14]?",
     "data_type": "boolean", "default_value": "false", "sort_order": 56, "notes": "RED-defer → Form 1116 / Schedule K-3."},
    # ── Outputs (return-level aggregates) ──
    {"fact_key": "k1_sche_line32", "label": "Schedule E line 32 (Part II total)",
     "data_type": "decimal", "sort_order": 70, "notes": "OUTPUT. (h)+(k)+(i)−(j) over partnership/S-corp K-1s."},
    {"fact_key": "k1_sche_line37", "label": "Schedule E line 37 (Part III total)",
     "data_type": "decimal", "sort_order": 71, "notes": "OUTPUT. (d)+(f)+(c)+(e) over 1041 K-1s."},
    {"fact_key": "k1_sche_line41", "label": "Schedule E line 41 → Schedule 1 line 5",
     "data_type": "decimal", "sort_order": 72, "notes": "OUTPUT. line 26 (Part I) + 32 + 37 + 39 + 40."},
]

K1_RULES: list[dict] = [
    {"rule_id": "R-K1-PARTII-ROUTE", "title": "Partnership/S-corp K-1 → Schedule E Part II line 28 columns", "rule_type": "routing",
     "precedence": 1, "sort_order": 1,
     "formula": ("For 1065/1120-S K-1s: the trade-or-business + rental net (box 1 + 2 + 3) routes by the "
                 "preparer material-participation assertion. NONPASSIVE (materially participated, or RE-pro on "
                 "rental): income → col (k), loss → col (i). PASSIVE: income → col (h); a passive LOSS is "
                 "RED-deferred (D_K1_PASSIVE_LOSS), NOT placed in col (g). Guaranteed payments (1065 b4c) are "
                 "always nonpassive → col (k). §179 (b12/b11) → col (j) (a deduction)."),
     "inputs": ["k1_ordinary", "k1_net_rental_re", "k1_other_rental", "k1_guaranteed_payments", "k1_section_179", "k1_material_participation"],
     "outputs": [],
     "description": "Decision 2/4. i1065sk1 + i1120ssk box 1/2/3 column rules; passive loss bounded out of v1."},
    {"rule_id": "R-K1-PARTII-TOTAL", "title": "Schedule E lines 30/31/32 (Part II totals)", "rule_type": "calculation",
     "precedence": 2, "sort_order": 2,
     "formula": ("line 30 = Σcol(h) + Σcol(k); line 31 = Σcol(g) + Σcol(i) + Σcol(j) (shown in parentheses — "
                 "the (j) §179 and (i)/(g) losses subtract); line 32 = line 30 + signed line 31. v1: col(g)=0 "
                 "(passive losses deferred)."),
     "inputs": [], "outputs": ["k1_sche_line32"],
     "description": "Schedule E page 2 Part II aggregation (f1040se 2025)."},
    {"rule_id": "R-K1-PARTIII-ROUTE", "title": "1041 beneficiary K-1 → Schedule E Part III line 33 columns", "rule_type": "routing",
     "precedence": 3, "sort_order": 3,
     "formula": ("For 1041 K-1s: box 5 other portfolio income → col (f); boxes 6/7/8 (business / net rental RE / "
                 "other rental) net routes by material participation: NONPASSIVE income → col (f), loss → col (e); "
                 "PASSIVE income → col (d); a passive LOSS is RED-deferred (D_K1_PASSIVE_LOSS), NOT placed in "
                 "col (c). Box 9 directly-apportioned deductions are RED-deferred in v1."),
     "inputs": ["k1_other_portfolio", "k1_ordinary", "k1_net_rental_re", "k1_other_rental", "k1_material_participation"],
     "outputs": [],
     "description": "Decision 3. 1041 K-1 face 'Report on' table (boxes 5/6/7/8 → line 33 col (d)/(f))."},
    {"rule_id": "R-K1-PARTIII-TOTAL", "title": "Schedule E lines 35/36/37 (Part III totals)", "rule_type": "calculation",
     "precedence": 4, "sort_order": 4,
     "formula": ("line 35 = Σcol(d) + Σcol(f); line 36 = Σcol(c) + Σcol(e) (parentheses); line 37 = 35 + 36. "
                 "v1: col(c)=0 (passive losses deferred)."),
     "inputs": [], "outputs": ["k1_sche_line37"],
     "description": "Schedule E page 2 Part III aggregation (f1040se 2025)."},
    {"rule_id": "R-K1-SCHE-SUMMARY", "title": "Schedule E line 41 = 26 + 32 + 37 + 39 + 40 → Schedule 1 line 5", "rule_type": "routing",
     "precedence": 5, "sort_order": 5,
     "formula": ("Schedule E line 41 = line 26 (Part I rentals/royalties, already built) + line 32 (Part II) + "
                 "line 37 (Part III) + line 39 (REMIC, v1 0) + line 40 (Form 4835, v1 0). Line 41 → Schedule 1 "
                 "(Form 1040) line 5 → 1040 line 8. REPOINTS the existing Part-I-only line-26→Sch1-L5 write."),
     "inputs": ["k1_sche_line32", "k1_sche_line37"], "outputs": ["k1_sche_line41"],
     "description": "THE CORRECTION: the summary is line 41 (not line 40). f1040se 2025 line 41 verbatim."},
    {"rule_id": "R-K1-INTEREST-DIV", "title": "K-1 interest/dividends → 1040 2b/3a/3b (Schedule B)", "rule_type": "routing",
     "precedence": 6, "sort_order": 6,
     "formula": ("Σ K-1 interest (1065 b5 / 1120-S b4 / 1041 b1) → 1040 line 2b; Σ ordinary dividends "
                 "(6a/5a/2a) → 1040 line 3b; Σ qualified dividends (6b/5b/2b) → 1040 line 3a. Character pass-through "
                 "(§702(b)/§1366(b)/§652(b))."),
     "inputs": ["k1_interest", "k1_ordinary_dividends", "k1_qualified_dividends"], "outputs": [],
     "description": "Decision 2. Interest/dividend routing. Mechanism (owned rows vs roster addend) = build-leg open item."},
    {"rule_id": "R-K1-CAPGAIN", "title": "K-1 capital gains → Schedule D lines 5/12", "rule_type": "routing",
     "precedence": 7, "sort_order": 7,
     "formula": ("Σ net ST capital gain (1065 b8 / 1120-S b7 / 1041 b3) → Schedule D line 5; Σ net LT "
                 "capital gain (9a/8a/4a) → Schedule D line 12 (Topic-9 engine). Collectibles 28% + unrecap §1250 "
                 "RED-deferred (SDTW)."),
     "inputs": ["k1_net_st_capital_gain", "k1_net_lt_capital_gain"], "outputs": [],
     "description": "Decision 2. 1041 K-1 face + i1065sk1: Sch D line 5 (ST) / line 12 (LT)."},
    {"rule_id": "R-K1-ROYALTY", "title": "K-1 royalties → Schedule E Part I line 4", "rule_type": "routing",
     "precedence": 8, "sort_order": 8,
     "formula": "Σ K-1 royalties (1065 b7 / 1120-S b6) → Schedule E Part I line 4 (existing royalty machinery).",
     "inputs": ["k1_royalties"], "outputs": [],
     "description": "Decision 2. Royalties join the existing Part I line-4 royalty path."},
    {"rule_id": "R-K1-SE", "title": "Partnership SE earnings (1065 box 14A) → Schedule SE", "rule_type": "routing",
     "precedence": 9, "sort_order": 9,
     "formula": ("1065 box 14 code A net SE earnings → Schedule SE line 2 (per proprietor; the Topic-8 SE engine: "
                 "×0.9235, SS wage cap, ½-SE → Sch 1 L15, SE → Sch 2 L4). §1402(a). S-corp shareholders + 1041 "
                 "beneficiaries: NO SE flow. Codes B/C (gross farm/nonfarm optional methods) RED-deferred."),
     "inputs": ["k1_se_earnings", "k1_source_type"], "outputs": [],
     "description": "Decision 6. 1065 box 14A only; the existing SE engine auto-creates the per-proprietor row."},
    {"rule_id": "R-K1-199A", "title": "K-1 §199A → Form 8995 (QBI line 2; REIT/PTP line 6)", "rule_type": "routing",
     "precedence": 10, "sort_order": 10,
     "formula": ("§199A QBI (1065 20Z / 1120-S 17V / 1041 14I) → Form 8995 line 2 (QBI component); §199A REIT "
                 "dividends + qualified PTP income → Form 8995 line 6. The Topic-8 8995 engine applies the 20% + "
                 "the taxable-income threshold ($197,300 / $394,600 MFJ 2025)."),
     "inputs": ["k1_section_199a_qbi", "k1_section_199a_reit_ptp"], "outputs": [],
     "description": "Decision 5. §199A → the existing 8995 engine (line 2 / line 6)."},
    {"rule_id": "R-K1-RED-DEFER", "title": "v1 RED-defer routing (no silent gaps)", "rule_type": "routing",
     "precedence": 11, "sort_order": 11,
     "formula": ("Any nonzero amount in a deferred box fires a RED: K-1 passive LOSS (D_K1_PASSIVE_LOSS → 8582); "
                 "§1231 (D_K1_SEC1231 → 4797); collectibles 28% / unrecap §1250 (D_K1_SPECIAL_GAIN → SDTW); AMT "
                 "items (D_K1_AMT → 6251); basis/at-risk limited (D_K1_BASIS → 6198/basis wksht); other income / "
                 "other deductions (D_K1_OTHER); foreign/K-3 (D_K1_FOREIGN → 1116). The amount is NOT dropped "
                 "silently — the preparer is told to handle the named form manually."),
     "inputs": ["k1_section_1231", "k1_collectibles_28", "k1_unrecap_1250", "k1_has_amt_items", "k1_basis_at_risk_limited", "k1_other_income", "k1_foreign_taxes"],
     "outputs": [],
     "description": "Decision 4 + the no-silent-gap rule. Each deferred box has a matching D_K1_* RED."},
]

K1_LINES: list[dict] = [
    # Conceptual K-1 input "lines" (the routed boxes, semantic) + outputs.
    {"line_number": "k1_src", "description": "Source entity type (1065 / 1120-S / 1041)", "line_type": "input"},
    {"line_number": "k1_matpart", "description": "Materially participated (nonpassive)?", "line_type": "input"},
    {"line_number": "k1_ord", "description": "Ordinary business income/(loss) [1065 b1 / 1120-S b1 / 1041 b6]", "line_type": "input"},
    {"line_number": "k1_rental", "description": "Net rental real estate [1065 b2 / 1120-S b2 / 1041 b7]", "line_type": "input"},
    {"line_number": "k1_othrent", "description": "Other net rental [1065 b3 / 1120-S b3 / 1041 b8]", "line_type": "input"},
    {"line_number": "k1_gp", "description": "Guaranteed payments [1065 b4c]", "line_type": "input"},
    {"line_number": "k1_179", "description": "Section 179 deduction [1065 b12 / 1120-S b11]", "line_type": "input"},
    {"line_number": "k1_portfolio", "description": "Other portfolio & nonbusiness income [1041 b5]", "line_type": "input"},
    {"line_number": "k1_int", "description": "Interest income [1065 b5 / 1120-S b4 / 1041 b1] → 1040 2b", "line_type": "input"},
    {"line_number": "k1_div_ord", "description": "Ordinary dividends [1065 6a / 1120-S 5a / 1041 2a] → 1040 3b", "line_type": "input"},
    {"line_number": "k1_div_qual", "description": "Qualified dividends [1065 6b / 1120-S 5b / 1041 2b] → 1040 3a", "line_type": "input"},
    {"line_number": "k1_roy", "description": "Royalties [1065 b7 / 1120-S b6] → Sch E Part I line 4", "line_type": "input"},
    {"line_number": "k1_st", "description": "Net ST capital gain [1065 b8 / 1120-S b7 / 1041 b3] → Sch D line 5", "line_type": "input"},
    {"line_number": "k1_lt", "description": "Net LT capital gain [1065 9a / 1120-S 8a / 1041 4a] → Sch D line 12", "line_type": "input"},
    {"line_number": "k1_se", "description": "SE earnings [1065 box 14A] → Schedule SE", "line_type": "input"},
    {"line_number": "k1_qbi", "description": "§199A QBI [1065 20Z / 1120-S 17V / 1041 14I] → 8995 line 2", "line_type": "input"},
    {"line_number": "k1_reit", "description": "§199A REIT dividends + PTP → 8995 line 6", "line_type": "input"},
    {"line_number": "k1_1231", "description": "Net §1231 [1065 b10 / 1120-S b9] → Form 4797 (RED-defer)", "line_type": "input"},
    {"line_number": "out_32", "description": "Schedule E line 32 (Part II total)", "line_type": "calculated"},
    {"line_number": "out_37", "description": "Schedule E line 37 (Part III total)", "line_type": "calculated"},
    {"line_number": "out_41", "description": "Schedule E line 41 → Schedule 1 line 5", "line_type": "total"},
]

K1_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_K1_PASSIVE_LOSS", "title": "K-1 passive loss — limit via Form 8582 manually", "severity": "error",
     "condition": "a K-1 with material_participation=False has a net Sch-E loss (box 1+2+3 or 1041 6+7+8 < 0)",
     "message": ("Not supported in v1 — prepare manually: this K-1 reports a PASSIVE loss (you did not materially "
                 "participate). Passive losses are limited by Form 8582 (the passive activity loss rules, §469). "
                 "This software routes passive INCOME and all nonpassive amounts, but does not compute the 8582 "
                 "limitation for a K-1 passive loss. Figure the allowed loss on Form 8582 and enter it manually."),
     "notes": "Decision 4. The core v1 bound — no per-activity 8582 allocation-back."},
    {"diagnostic_id": "D_K1_SEC1231", "title": "K-1 §1231 gain/loss — Form 4797 not built on the 1040", "severity": "error",
     "condition": "k1_section_1231 != 0",
     "message": ("Not supported in v1 — prepare manually: this K-1 reports a net section 1231 gain/(loss) "
                 "[1065 box 10 / 1120-S box 9]. Section 1231 amounts flow through Form 4797, which is not yet built "
                 "on the 1040. Compute Form 4797 (and its Schedule D / ordinary-income split) manually."),
     "notes": "RED-defer — no compute_4797 on the 1040 side."},
    {"diagnostic_id": "D_K1_SPECIAL_GAIN", "title": "K-1 collectibles 28% / unrecaptured §1250 gain — not supported", "severity": "error",
     "condition": "k1_collectibles_28 != 0 OR k1_unrecap_1250 != 0",
     "message": ("Not supported in v1 — prepare manually: this K-1 reports a 28%-rate collectibles gain or "
                 "unrecaptured section 1250 gain. These require the Schedule D Tax Worksheet (28%-rate / §1250 lines), "
                 "which is deferred. Compute the Schedule D Tax Worksheet tax manually."),
     "notes": "RED-defer — the Schedule D Tax Worksheet is a deferred (post-sprint) item."},
    {"diagnostic_id": "D_K1_AMT", "title": "K-1 AMT items — Form 6251 not built", "severity": "error",
     "condition": "k1_has_amt_items is True",
     "message": ("Not supported in v1 — prepare manually: this K-1 reports alternative minimum tax (AMT) items "
                 "[1065 box 17 / 1120-S box 15 / 1041 box 12]. Form 6251 is not yet built. Figure the AMT "
                 "adjustment manually."),
     "notes": "RED-defer — AMT (6251) is out of the sprint."},
    {"diagnostic_id": "D_K1_BASIS", "title": "K-1 basis / at-risk limitation — preparer must verify", "severity": "warning",
     "condition": "k1_basis_at_risk_limited is True",
     "message": ("This K-1's losses/deductions may be limited by your basis (partner §704(d) / shareholder "
                 "§1366(d)) or the at-risk rules (§465, Form 6198). This software does not track K-1 basis or "
                 "at-risk amounts — it reports the K-1 figures as entered. Verify the deductible amount and reduce "
                 "the entries if limited."),
     "notes": "RED-defer (warning) — no basis/at-risk engine; preparer asserts the allowed amount."},
    {"diagnostic_id": "D_K1_OTHER", "title": "K-1 other income/(loss) — code-specific, handle manually", "severity": "error",
     "condition": "k1_other_income != 0",
     "message": ("Not auto-routed in v1 — prepare manually: this K-1 reports 'Other income (loss)' "
                 "[1065 box 11 / 1120-S box 10], which is code-specific (the entity attaches a statement). "
                 "Determine each item's character and report it on the correct line manually."),
     "notes": "RED-defer — box 11/10 is a multi-code grab bag."},
    {"diagnostic_id": "D_K1_FOREIGN", "title": "K-1 foreign taxes / Schedule K-3 — not routed", "severity": "warning",
     "condition": "k1_foreign_taxes is True",
     "message": ("This K-1 reports foreign taxes or has Schedule K-3 attached [1065 box 21/16 / 1120-S box 14]. "
                 "The foreign tax credit (Form 1116) / Schedule K-3 items are not routed in v1. Handle the foreign "
                 "tax credit or deduction manually."),
     "notes": "RED-defer (warning) — Form 1116 / K-3 out of scope."},
    {"diagnostic_id": "D_K1_PTP_LOSS", "title": "Publicly traded partnership — per-PTP passive rules", "severity": "warning",
     "condition": "k1_is_ptp is True AND a net loss is present",
     "message": ("This is a publicly traded partnership (PTP). PTP passive losses are limited on a per-PTP basis "
                 "(netted only against income from the SAME PTP, not the §469 special allowance). v1 does not apply "
                 "the per-PTP netting — verify the allowed PTP loss manually."),
     "notes": "PTP §469(k). v1 flags rather than nets."},
    {"diagnostic_id": "D_K1_SCORP_SE", "title": "S-corp share is not self-employment income", "severity": "info",
     "condition": "k1_source_type == '1120s' AND k1_se_earnings entered",
     "message": ("An S corporation shareholder's distributive share is not self-employment income and is not "
                 "subject to self-employment tax. No Schedule SE is generated from this K-1 (reasonable W-2 "
                 "compensation is the separate §1373 issue)."),
     "notes": "Decision 6. Info — guards against a stray SE entry on an 1120-S K-1."},
    {"diagnostic_id": "D_K1_FLOW", "title": "K-1 totals flow to Schedule E line 41 → Schedule 1 line 5", "severity": "info",
     "condition": "k1_sche_line41 != 0",
     "message": ("The Schedule E page-2 K-1 totals (Part II line 32 + Part III line 37) combine with Part I "
                 "(line 26) on line 41 and flow to Schedule 1 (Form 1040) line 5."),
     "notes": "The flow confirmation."},
]

K1_SCENARIOS: list[dict] = [
    {"scenario_name": "K1-T1 — 1065 nonpassive ordinary income → col (k) → line 32 → line 41", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"k1s": [{"source_type": "1065", "material_participation": True, "ordinary": 50000}], "line26": 0},
     "expected_outputs": {"k1_sche_line32": 50000, "k1_sche_line41": 50000},
     "notes": "Materially-participated ordinary income → col (k) 50,000; line 30=50,000; line 32=50,000; line 41=50,000 → Sch 1 L5."},
    {"scenario_name": "K1-T2 — 1065 nonpassive loss → col (i) (negative) → line 32", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"k1s": [{"source_type": "1065", "material_participation": True, "ordinary": -8000}], "line26": 0},
     "expected_outputs": {"k1_sche_line32": -8000, "k1_sche_line41": -8000},
     "notes": "Nonpassive loss is allowed in full → col (i) (8,000); line 31 = (8,000); line 32 = (8,000)."},
    {"scenario_name": "K1-T3 — 1065 passive income → col (h)", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"k1s": [{"source_type": "1065", "material_participation": False, "ordinary": 12000}], "line26": 0},
     "expected_outputs": {"k1_sche_line32": 12000, "k1_sche_line41": 12000},
     "notes": "Passive income is allowed → col (h) 12,000 → line 32 = 12,000."},
    {"scenario_name": "K1-G1 — 1065 passive LOSS → RED-defer (D_K1_PASSIVE_LOSS)", "scenario_type": "diagnostic", "sort_order": 4,
     "inputs": {"k1s": [{"source_type": "1065", "material_participation": False, "ordinary": -15000}], "line26": 0},
     "expected_outputs": {"k1_sche_line32": 0, "D_K1_PASSIVE_LOSS": True},
     "notes": "Passive loss is NOT placed in col (g); excluded from line 32 (=0) and D_K1_PASSIVE_LOSS fires."},
    {"scenario_name": "K1-T4 — 1065 guaranteed payments → col (k) + §179 col (j)", "scenario_type": "edge_case", "sort_order": 5,
     "inputs": {"k1s": [{"source_type": "1065", "material_participation": True, "ordinary": 40000, "guaranteed_payments": 10000, "section_179": 6000}], "line26": 0},
     "expected_outputs": {"k1_sche_line32": 44000},
     "notes": "col (k) = 40,000 ord + 10,000 GP = 50,000; col (j) §179 = 6,000; line 30=50,000, line 31=(6,000), line 32=44,000."},
    {"scenario_name": "K1-T5 — 1065 guaranteed payments + SE earnings → Schedule SE", "scenario_type": "normal", "sort_order": 6,
     "inputs": {"k1s": [{"source_type": "1065", "material_participation": True, "ordinary": 40000, "guaranteed_payments": 10000, "se_earnings": 50000}], "line26": 0},
     "expected_outputs": {"sch_se_2": 50000, "k1_sche_line32": 50000},
     "notes": "Box 14A 50,000 → Schedule SE line 2; the Sch E side is unaffected (col (k) = 50,000)."},
    {"scenario_name": "K1-T6 — 1065 §199A QBI → Form 8995 line 2", "scenario_type": "normal", "sort_order": 7,
     "inputs": {"k1s": [{"source_type": "1065", "material_participation": True, "ordinary": 80000, "section_199a_qbi": 80000}], "line26": 0},
     "expected_outputs": {"f8995_2": 80000, "k1_sche_line32": 80000},
     "notes": "Box 20Z QBI 80,000 → 8995 line 2; the 20% QBI deduction is computed by the 8995 engine."},
    {"scenario_name": "K1-T7 — 1120-S nonpassive income, NO SE", "scenario_type": "normal", "sort_order": 8,
     "inputs": {"k1s": [{"source_type": "1120s", "material_participation": True, "ordinary": 60000, "se_earnings": 60000}], "line26": 0},
     "expected_outputs": {"k1_sche_line32": 60000, "sch_se_2": 0},
     "notes": "S-corp ordinary income → col (k) 60,000; an S-corp share is NOT SE income → Schedule SE = 0 (D_K1_SCORP_SE)."},
    {"scenario_name": "K1-T8 — 1041 beneficiary business income → Part III line 37", "scenario_type": "normal", "sort_order": 9,
     "inputs": {"k1s": [{"source_type": "1041", "material_participation": False, "business": 9000, "other_portfolio": 1000}], "line26": 0},
     "expected_outputs": {"k1_sche_line37": 10000, "k1_sche_line41": 10000},
     "notes": "1041 box 5 portfolio → col (f) 1,000; box 6 passive business income → col (d) 9,000; line 35=10,000; line 37=10,000."},
    {"scenario_name": "K1-T9 — mixed: 1065 Part II + 1041 Part III + Part I → line 41", "scenario_type": "edge_case", "sort_order": 10,
     "inputs": {"k1s": [{"source_type": "1065", "material_participation": True, "ordinary": 30000},
                        {"source_type": "1041", "material_participation": False, "business": 5000}], "line26": 7000},
     "expected_outputs": {"k1_sche_line32": 30000, "k1_sche_line37": 5000, "k1_sche_line41": 42000},
     "notes": "line 41 = line 26 (7,000 Part I) + line 32 (30,000) + line 37 (5,000) = 42,000 → Sch 1 L5."},
    {"scenario_name": "K1-T10 — K-1 interest/dividends/cap-gains route off Schedule E", "scenario_type": "normal", "sort_order": 11,
     "inputs": {"k1s": [{"source_type": "1065", "material_participation": True, "interest": 200, "ordinary_dividends": 500, "qualified_dividends": 400, "net_lt_capital_gain": 3000}], "line26": 0},
     "expected_outputs": {"2b": 200, "3b": 500, "3a": 400, "schd_12": 3000, "k1_sche_line32": 0},
     "notes": "Portfolio K-1 items leave Schedule E entirely: interest→2b, dividends→3b/3a, LT gain→Sch D line 12."},
    {"scenario_name": "K1-G2 — 1065 §1231 → RED (Form 4797 not built)", "scenario_type": "diagnostic", "sort_order": 12,
     "inputs": {"k1s": [{"source_type": "1065", "material_participation": True, "ordinary": 10000, "section_1231": 4000}], "line26": 0},
     "expected_outputs": {"D_K1_SEC1231": True, "k1_sche_line32": 10000},
     "notes": "Box 10 §1231 4,000 fires D_K1_SEC1231 (prepare 4797 manually); the ordinary income still routes."},
]

K1_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-K1-PARTII-ROUTE", "IRS_2025_1065_K1_INSTR", "primary", "Box 1/2/3 → Sch E line 28 columns by material participation"),
    ("R-K1-PARTII-ROUTE", "IRS_2025_1120S_K1_INSTR", "primary", "S-corp box 1/2/3 column routing"),
    ("R-K1-PARTII-ROUTE", "IRC_469", "secondary", "§469 passive activity classification"),
    ("R-K1-PARTII-TOTAL", "IRS_2025_SCHE_INSTR", "primary", "Schedule E page 2 lines 30/31/32"),
    ("R-K1-PARTIII-ROUTE", "IRS_2025_1041_K1_INSTR", "primary", "1041 K-1 boxes 5/6/7/8 → line 33 cols (d)/(f)"),
    ("R-K1-PARTIII-TOTAL", "IRS_2025_SCHE_INSTR", "primary", "Schedule E page 2 lines 35/36/37"),
    ("R-K1-SCHE-SUMMARY", "IRS_2025_SCHE_INSTR", "primary", "Schedule E line 41 = 26+32+37+39+40 → Sch 1 L5"),
    ("R-K1-INTEREST-DIV", "IRC_PASSTHROUGH_CHARACTER", "primary", "§702(b)/§1366(b)/§652(b) character pass-through"),
    ("R-K1-INTEREST-DIV", "IRS_2025_1041_K1_INSTR", "secondary", "1041 K-1: box 1→2b, 2a→3b, 2b→3a"),
    ("R-K1-CAPGAIN", "IRS_2025_1041_K1_INSTR", "primary", "K-1 ST→Sch D 5 / LT→Sch D 12"),
    ("R-K1-CAPGAIN", "IRS_2025_1065_K1_INSTR", "secondary", "Net LT gain → Schedule D line 12"),
    ("R-K1-ROYALTY", "IRS_2025_1065_K1_INSTR", "primary", "Box 7 royalties → Schedule E Part I"),
    ("R-K1-SE", "IRC_1402", "primary", "§1402(a) partner SE; box 14A → Schedule SE"),
    ("R-K1-SE", "IRS_2025_1065_K1_INSTR", "secondary", "Box 14 code A net SE earnings"),
    ("R-K1-199A", "IRC_199A", "primary", "§199A 20% QBI + REIT/PTP"),
    ("R-K1-199A", "IRS_2025_1065_K1_INSTR", "secondary", "Box 20 code Z / 17V / 14I → Form 8995"),
    ("R-K1-RED-DEFER", "IRS_2025_F8582_INSTR", "secondary", "Passive loss → Form 8582 (deferred)"),
    ("R-K1-RED-DEFER", "IRS_2025_1065_K1_INSTR", "secondary", "Deferred boxes (10/11/17/etc.) — handle manually"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM 2: SCHEDULE_E (AMENDED — add page-2 lines 27-43 + Part II/III + line 41)
# ═══════════════════════════════════════════════════════════════════════════

SCHE_IDENTITY = {
    "form_number": "SCHEDULE_E",
    "form_title": "Schedule E (Form 1040) — Supplemental Income and Loss (Parts I-V, TY2025)",
    "notes": (
        "Part I (rentals & royalties) + Form 8582 built 2026-06-14 (load_1040_schedule_e). "
        "Effort #5 (2026-06-21) AMENDS page 2: Part II partnerships & S corporations (line 28 "
        "cols g/h/i/j/k → 30/31/32), Part III estates & trusts (line 33 cols c/d/e/f → 35/36/37), "
        "Part IV REMIC (38/39, v1 0), Part V summary — **line 41 = combine 26, 32, 37, 39, 40 → "
        "Schedule 1 line 5** (the Part-I-only line-26→Sch1-L5 write is repointed to line 41). The "
        "K-1 amounts that feed lines 28/33 come from the SCHEDULE_K1 recipient router. Part I "
        "lines A-26 are unchanged."
    ),
}

# Only the page-2 additions (Part I lines A-26 already seeded by load_1040_schedule_e).
SCHE_P2_LINES: list[dict] = [
    {"line_number": "27", "description": "27 Are you reporting any loss not allowed in a prior year (at-risk/basis), a prior-year unallowed passive loss, or unreimbursed partnership expenses?", "line_type": "input"},
    {"line_number": "28", "description": "28 (a) Name; (b) P/S; (c) foreign partnership; (d) EIN; (e) basis computation required; (f) any amount not at risk (per K-1)", "line_type": "input"},
    {"line_number": "29a", "description": "29a Totals — passive/nonpassive income columns (h) and (k)", "line_type": "calculated"},
    {"line_number": "29b", "description": "29b Totals — loss columns (g), (i), and §179 (j)", "line_type": "calculated"},
    {"line_number": "30", "description": "30 Add columns (h) and (k) of line 29a (Part II income)", "line_type": "calculated"},
    {"line_number": "31", "description": "31 Add columns (g), (i), and (j) of line 29b (Part II losses)", "line_type": "calculated"},
    {"line_number": "32", "description": "32 Total partnership and S corporation income or (loss) — combine lines 30 and 31", "line_type": "subtotal"},
    {"line_number": "33", "description": "33 (a) Name; (b) EIN (per estate/trust K-1)", "line_type": "input"},
    {"line_number": "34a", "description": "34a Totals — passive income (d) and other income (f)", "line_type": "calculated"},
    {"line_number": "34b", "description": "34b Totals — passive deduction/loss (c) and deduction/loss (e)", "line_type": "calculated"},
    {"line_number": "35", "description": "35 Add columns (d) and (f) of line 34a (Part III income)", "line_type": "calculated"},
    {"line_number": "36", "description": "36 Add columns (c) and (e) of line 34b (Part III losses)", "line_type": "calculated"},
    {"line_number": "37", "description": "37 Total estate and trust income or (loss) — combine lines 35 and 36", "line_type": "subtotal"},
    {"line_number": "38", "description": "38 REMIC residual holder — (c) excess inclusion; (d) taxable income (net loss); (e) income from Schedules Q (v1 RED-defer)", "line_type": "input"},
    {"line_number": "39", "description": "39 Combine columns (d) and (e) (REMIC) — include in line 41 (v1 = 0)", "line_type": "calculated"},
    {"line_number": "40", "description": "40 Net farm rental income or (loss) from Form 4835 (v1 RED-defer = 0)", "line_type": "calculated"},
    {"line_number": "41", "description": "41 Total income or (loss). Combine lines 26, 32, 37, 39, and 40. Enter here and on Schedule 1 (Form 1040), line 5", "line_type": "total"},
    {"line_number": "42", "description": "42 Reconciliation of farming and fishing income (1065 box 14 code B; 1120-S box 17 code AN; 1041 box 14 code F)", "line_type": "input"},
    {"line_number": "43", "description": "43 Reconciliation for real estate professionals (informational)", "line_type": "input"},
]

SCHE_P2_RULES: list[dict] = [
    {"rule_id": "R-SCHE-P2-PART2", "title": "Part II (partnerships & S corps) lines 30/31/32", "rule_type": "calculation",
     "precedence": 10, "sort_order": 10,
     "formula": ("Line 30 = Σ col (h) passive income + Σ col (k) nonpassive income; line 31 = Σ col (g) passive "
                 "loss + Σ col (i) nonpassive loss + Σ col (j) §179 (shown in parentheses); line 32 = combine 30 "
                 "and 31. Columns are filled by the SCHEDULE_K1 router (v1 col (g)=0, passive losses deferred)."),
     "inputs": [], "outputs": [],
     "description": "Schedule E page 2 Part II aggregation; fed by SCHEDULE_K1."},
    {"rule_id": "R-SCHE-P2-PART3", "title": "Part III (estates & trusts) lines 35/36/37", "rule_type": "calculation",
     "precedence": 11, "sort_order": 11,
     "formula": ("Line 35 = Σ col (d) passive income + Σ col (f) other income; line 36 = Σ col (c) passive "
                 "deduction/loss + Σ col (e) deduction/loss (parentheses); line 37 = combine 35 and 36. Fed by the "
                 "SCHEDULE_K1 router's 1041 rows (v1 col (c)=0)."),
     "inputs": [], "outputs": [],
     "description": "Schedule E page 2 Part III aggregation; fed by SCHEDULE_K1."},
    {"rule_id": "R-SCHE-P2-SUMMARY", "title": "Line 41 = 26 + 32 + 37 + 39 + 40 → Schedule 1 line 5", "rule_type": "routing",
     "precedence": 12, "sort_order": 12,
     "formula": ("Schedule E line 41 = line 26 (Part I) + line 32 (Part II) + line 37 (Part III) + line 39 "
                 "(REMIC, v1 0) + line 40 (Form 4835, v1 0). Line 41 → Schedule 1 (Form 1040) line 5 → 1040 line 8. "
                 "The existing line-26→Sch1-L5 write is REPOINTED to line 41 (line 26 now an addend within 41)."),
     "inputs": [], "outputs": [],
     "description": "THE CORRECTION (f1040se 2025): the summary that flows to Sch 1 L5 is line 41, not line 40."},
]

SCHE_P2_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_SCHE_REMIC", "title": "REMIC residual interest — not supported", "severity": "error",
     "condition": "Schedule E Part IV (REMIC) amounts present",
     "message": ("Not supported in v1 — prepare manually: Schedule E Part IV (REMIC residual holder, Schedules Q) "
                 "is not built. The excess inclusion and net REMIC income must be figured manually and included on "
                 "line 41."),
     "notes": "Decision 3. REMIC RED-defer."},
    {"diagnostic_id": "D_SCHE_4835", "title": "Form 4835 farm rental — not supported", "severity": "error",
     "condition": "Form 4835 net farm rental (line 40) present",
     "message": ("Not supported in v1 — prepare manually: net farm rental income (Form 4835, Schedule E line 40) "
                 "is not built. Compute Form 4835 and include its result on line 40/41 manually."),
     "notes": "Form 4835 RED-defer (paired with Schedule F's later topic)."},
]

SCHE_P2_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-SCHE-P2-PART2", "IRS_2025_SCHE_INSTR", "primary", "Part II lines 28-32"),
    ("R-SCHE-P2-PART3", "IRS_2025_SCHE_INSTR", "primary", "Part III lines 33-37"),
    ("R-SCHE-P2-SUMMARY", "IRS_2025_SCHE_INSTR", "primary", "Part V line 41 → Schedule 1 line 5"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS (cross-form: K-1 → Schedule E p2 / Sch B / Sch D / Sch SE / 8995)
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-K1-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Schedule E line 41 = 26 + 32 + 37 + 39 + 40 → Schedule 1 line 5",
     "description": "Validates R-K1-SCHE-SUMMARY / R-SCHE-P2-SUMMARY. Bug it catches: the K-1 totals not reaching Sch 1 L5, or the old line-26-only write surviving (the brainstorm's line-40 error).",
     "definition": {"kind": "flow_assertion", "form": "SCHEDULE_E",
                    "checks": [{"source_line": "41", "must_write_to": ["SCH_1.5"]}],
                    "formula": "line_41 == line_26 + line_32 + line_37 + line_39 + line_40"},
     "sort_order": 1},
    {"assertion_id": "FA-1040-K1-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Part II line 32 = (h)+(k) − [(i loss)+(j §179)] (passive loss excluded in v1)",
     "description": "Validates R-K1-PARTII-TOTAL. Bug it catches: a passive loss leaking into col (g) (should RED-defer), or §179 not subtracted.",
     "definition": {"kind": "formula_check", "form": "SCHEDULE_K1",
                    "formula": "line_32 == (col_h + col_k) + (col_i - col_j); col_g == 0 in v1"},
     "sort_order": 2},
    {"assertion_id": "FA-1040-K1-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Part III line 37 = (d)+(f) + (c)+(e) (1041 estates/trusts)",
     "description": "Validates R-K1-PARTIII-TOTAL. Bug it catches: 1041 box-5 portfolio income mis-columned, or a passive loss not deferred.",
     "definition": {"kind": "formula_check", "form": "SCHEDULE_K1",
                    "formula": "line_37 == (col_d + col_f) + (col_c + col_e); col_c == 0 in v1"},
     "sort_order": 3},
    {"assertion_id": "FA-1040-K1-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "K-1 interest/dividends → 1040 2b/3b/3a; capital gains → Schedule D 5/12",
     "description": "Validates R-K1-INTEREST-DIV + R-K1-CAPGAIN. Bug it catches: K-1 portfolio items mis-routed (e.g. interest landing on Schedule E instead of 1040 2b).",
     "definition": {"kind": "flow_assertion", "form": "SCHEDULE_K1",
                    "checks": [{"source_line": "k1_int", "must_write_to": ["1040.2b"]},
                               {"source_line": "k1_div_ord", "must_write_to": ["1040.3b"]},
                               {"source_line": "k1_div_qual", "must_write_to": ["1040.3a"]},
                               {"source_line": "k1_st", "must_write_to": ["SCHEDULE_D.5"]},
                               {"source_line": "k1_lt", "must_write_to": ["SCHEDULE_D.12"]}]},
     "sort_order": 4},
    {"assertion_id": "FA-1040-K1-05", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Partnership SE (1065 box 14A) → Schedule SE; S-corp/1041 no SE",
     "description": "Validates R-K1-SE. Bug it catches: an S-corp or 1041 K-1 generating SE tax, or a 1065 box-14A not reaching Schedule SE.",
     "definition": {"kind": "gating_check", "form": "SCHEDULE_K1", "expect": {"se_flows": "1065_only"},
                    "checks": [{"source_line": "k1_se", "must_write_to": ["SCHEDULE_SE.2"], "when": "source_type==1065"}]},
     "sort_order": 5},
    {"assertion_id": "FA-1040-K1-06", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "K-1 §199A → Form 8995 (QBI line 2; REIT/PTP line 6)",
     "description": "Validates R-K1-199A. Bug it catches: §199A QBI not reaching the 8995 engine, or REIT/PTP mis-routed to the QBI line.",
     "definition": {"kind": "flow_assertion", "form": "SCHEDULE_K1",
                    "checks": [{"source_line": "k1_qbi", "must_write_to": ["FORM_8995.2"]},
                               {"source_line": "k1_reit", "must_write_to": ["FORM_8995.6"]}]},
     "sort_order": 6},
    {"assertion_id": "FA-1040-K1-07", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "No silent gaps — every deferred box fires a RED",
     "description": "Validates R-K1-RED-DEFER. Bug it catches: a deferred box (passive loss / §1231 / 28%/§1250 / AMT / other income / foreign) silently dropping its amount with no diagnostic.",
     "definition": {"kind": "gating_check", "form": "SCHEDULE_K1", "expect": {"red_fires": True},
                    "blockers": ["passive_loss", "section_1231", "collectibles_28", "unrecap_1250", "amt_items", "other_income", "foreign_taxes"]},
     "sort_order": 7},
]


FORMS: list[dict] = [
    {"identity": K1_IDENTITY, "facts": K1_FACTS, "rules": K1_RULES, "lines": K1_LINES,
     "diagnostics": K1_DIAGNOSTICS, "scenarios": K1_SCENARIOS, "rule_links": K1_RULE_LINKS},
    {"identity": SCHE_IDENTITY, "facts": [], "rules": SCHE_P2_RULES, "lines": SCHE_P2_LINES,
     "diagnostics": SCHE_P2_DIAGNOSTICS, "scenarios": [], "rule_links": SCHE_P2_RULE_LINKS},
]


class Command(BaseCommand):
    help = "Load the SCHEDULE_K1 (recipient K-1 router) spec + amend SCHEDULE_E page 2. Refuses until READY_TO_SEED=True."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad SCHEDULE_K1 (recipient K-1 router) + amend SCHEDULE_E page 2\n"))
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
        # SCHEDULE_E is an additive amendment (no new facts/scenarios) — only require
        # its page-2 lines + rules; SCHEDULE_K1 must be fully populated.
        empty = []
        k1 = FORMS[0]
        for key in ("facts", "rules", "lines", "diagnostics", "scenarios", "rule_links"):
            if not k1[key]:
                empty.append(f"SCHEDULE_K1.{key}")
        sche = FORMS[1]
        for key in ("rules", "lines", "rule_links"):
            if not sche[key]:
                empty.append(f"SCHEDULE_E.{key}")
        if not FLOW_ASSERTIONS:
            empty.append("FLOW_ASSERTIONS")
        if not READY_TO_SEED or empty:
            still_empty = "\n  ".join(f"- {n}" for n in empty) or "(all populated)"
            raise CommandError(
                "\nREFUSING TO SEED SCHEDULE_K1 / SCHEDULE_E (page 2): not cleared to seed.\n\n"
                "Gated until Ken's review walk (the box→destination routing per source, the\n"
                "passive/nonpassive split, the line-41 summary correction, the §199A/SE flows,\n"
                "and the complete v1 RED-defer list).\n\n"
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
        for fn in ("SCHEDULE_K1", "SCHEDULE_E"):
            form = TaxForm.objects.filter(form_number=fn).first()
            if form:
                uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
                self.stdout.write(f"{fn}: all rules cited" if not uncited
                                  else self.style.WARNING(f"{fn} uncited rules: {len(uncited)}"))
