"""Load Form 8824 (Like-Kind Exchanges, and §1043 conflict-of-interest sales) — FULL v1.

Authored 2026-06-28 in the load_6252.py / load_4797.py / load_1040_form_1116.py modern pattern:
a pure module-level ``compute_8824()`` the integrity gate re-types, a ``FORMS`` structure, and
``FLOW_ASSERTIONS``.

KEN'S SCOPE (chosen 2026-06-28, AskUserQuestion): "Full incl. Part IV + computed recapture" — the
WHOLE Form 8824:
  Part I  (lines 1-7)   — exchange info + dates + related-party flag (data + 45-day/180-day diagnostics).
  Part II (lines 8-11)  — related-party exchange; the §1031(f) 2-year second-disposition acceleration
                          of the previously-deferred gain (line 24), with the line-11 exceptions.
  Part III (lines 12-25)— realized / recognized / deferred gain + basis carryover, with boot computed
                          from components (the §1.1031(d)-2 liability-netting rule), and the line-21
                          ordinary recapture COMPUTED via the §1245(b)(4) and §1250(d)(4) limits
                          (not preparer-asserted), plus the 25a/b/c proportional basis allocation.
  Part IV (lines 26-38) — §1043 conflict-of-interest divestitures (federal executive/judicial officers).

This CLOSES the live Form 4797 ``D_4797_004`` like-kind RED-defer: line 21 → Form 4797 line 16
(ordinary recapture); line 22 → Form 4797 line 5 (business §1231) or Schedule D (capital). (Same
pattern the 6252 unit used to retire the 4797↔6252 defer.)

LAW VERIFIED 2026-06-28 against the actual 2025 Form 8824 PDF (f8824.pdf, both pages, OMB 1545-0074,
"Created 8/19/25") + the 2025 Instructions for Form 8824 (i8824.pdf, all 7 pages — incl. the
§1.1031(d)-2 Taylor/Finley liability-netting example, the §1245(b)(4)/§1250(d)(4) recapture examples,
and the 25a/b/c allocation example) + IRC §1031 / §1031(f) / §1245(b)(4) / §1250(d)(4) / §1043. Every
line number and routing destination below is read directly off that PDF / those instructions.

CORE MODEL (Part III — §1031):
  Liability netting (§1.1031(d)-2): net_relief = liab_assumed_by_other − (liab_you_assumed +
    cash_you_paid + fmv_nonlike_you_gave_up). If > 0 it is boot to you (adds to L15); if < 0 the
    excess you pay adds to the basis given up (L18). Only one side is ever positive.
  L15 = max(0, cash_received + fmv_nonlike_received + max(0, net_relief) − exchange_expenses).
    Exchange expenses reduce L15 not below zero; any unused remainder moves to L18.
  L16 = FMV of like-kind property received. L17 = L15 + L16.
  L18 = basis of like-kind property given up + exchange-expenses-not-used-on-L15 + max(0, −net_relief).
  L19 = L17 − L18 (realized gain or loss; a LOSS is never recognized — it defers into basis).
  L20 = max(0, min(L15, L19)) (gain recognized to the extent of boot, before recapture).
  L21 = ordinary recapture → Form 4797 line 16, the SUM of:
        §1245(b)(4): min( min(depr_1245, max(0,L19)), L20 + (L16 − fmv_1245_lk_received) )
        §1250(d)(4): min( addl_depr_1250, max(L20, addl_depr_1250 − fmv_1250_lk_received) )
  L22 = max(0, L20 − L21) → Form 4797 line 5 (business §1231 >1yr) / line 16 (ordinary/≤1yr) /
        Schedule D (capital asset, ST or LT).
  L23 = L21 + L22 (recognized gain). L24 = L19 if L19 < 0 else L19 − L23 (deferred gain/loss).
  L25 = (L18 + L23) − L15 (basis of like-kind property received); 25a/25b/25c allocate L25
        proportionally to the FMV of like-kind §1250 / §1245+1252+1254+1255 / intangible received.
  L12-14: if NON-like-kind property was also given up, L14 = L12 − L13 is recognized as a sale
        (routed by character), separately from the like-kind computation.

PART II (§1031(f) related-party 2-year rule): if this is one of the 2 years after a related-party
  exchange and the related party (line 9) or you (line 10) disposed of the received property, and NO
  line-11 exception (death / involuntary conversion / no-tax-avoidance) applies, the previously
  DEFERRED gain (the original year's line 24, preparer-supplied) is recognized this year and routed
  by character. (The prior-year line 24 is preparer-asserted — the original 8824 is not necessarily
  in the system.)

PART IV (§1043 conflict-of-interest): L32 = L30 − L31 (realized gain); L34 = max(0, L30 − L33);
  L35 = ordinary recapture (from a Form 4797 Part III worksheet, preparer-asserted) → Form 4797 line
  10; L36 = max(0, L34 − L35) → Schedule D / Form 4797 by character; L37 = L32 − (L35 + L36)
  (deferred); L38 = L33 − L37 (basis of replacement). Gate: only if cost of replacement (L33) > basis
  of divested (L31) and the taxpayer elects; otherwise report the sale normally.

v1 RED-defers / no-silent-gap diagnostics: multi-asset exchange (>1 like-kind group — i8824 says
  skip lines 12-18 and attach a statement), §121 main-home/business mixed-use combo (two-worksheet
  method), and a PERSONAL-property "like-kind" exchange (post-2017 §1031 is real-property only).

SAFETY GUARD: READY_TO_SEED stays False until Ken's review walk (the liability-netting arithmetic,
the §1245(b)(4)/§1250(d)(4) computed recapture, the 4797 line-5/16 routing closure of D_4797_004, the
Part II §1031(f) acceleration, the Part IV §1043 mechanics, and the v1 RED-defer boundaries).
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


READY_TO_SEED = True  # FLIPPED 2026-06-28 — Ken approved the review walk ("Approve — seed it").


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1  # New form — no prior RS row (lookup returned 404).
FORM_ENTITY_TYPES = ["1040"]  # 1040 build. (8824 is filed by entities too; entity routing = future.)
FORM_STATUS = "draft"


from decimal import Decimal  # noqa: E402


def _D(x):
    return Decimal(str(x if x is not None else 0))


# ═══════════════════════════════════════════════════════════════════════════
# PURE COMPUTE (mirrors the tts compute leg; check_8824_integrity.py re-types it)
# ═══════════════════════════════════════════════════════════════════════════

def compute_8824(*,
                 # ── Part III — non-like-kind property given up (L12-14) ──
                 fmv_other_given_up=0, basis_other_given_up=0,
                 # ── Part III — boot received + liability netting (L15) ──
                 cash_received=0, fmv_nonlike_received=0, exchange_expenses=0,
                 liabilities_assumed_by_other=0, liabilities_you_assumed=0,
                 cash_you_paid=0, fmv_nonlike_given_up=0,
                 # ── Part III — like-kind received / basis given up (L16, L18) ──
                 fmv_likekind_received=0, basis_likekind_given_up=0,
                 # ── Part III — computed recapture (L21) inputs ──
                 depreciation_1245=0, fmv_1245_lk_received=0,
                 additional_depreciation_1250=0, fmv_1250_lk_received=0,
                 fmv_intangible_lk_received=0,
                 # ── character / holding period ──
                 property_character="capital", holding_period_months=0,
                 # ── Part II — related-party §1031(f) acceleration ──
                 related_party=False, is_followup_year=False, related_party_disposed=False,
                 rp_exception="", prior_year_deferred_gain=0,
                 # ── Part I — dates (for the deferred-exchange deadline diagnostics) ──
                 days_to_identify=None, days_to_receive=None,
                 # ── Part IV — §1043 conflict-of-interest ──
                 is_1043=False, sales_price_divested=0, basis_divested=0,
                 cost_replacement_60day=0, recapture_1043=0, character_1043="capital",
                 # ── red-defer flags ──
                 multi_asset=False, property_used_as_home=False, is_real_property=True,
                 **_ignored) -> dict:
    """One like-kind exchange (or one §1043 divestiture), one tax year → the 8824 lines + routing.

    Returns the key lines plus the destinations:
      l19 / l23 / l24      — realized gain, recognized gain, deferred gain (or loss)
      l25 / l25a/b/c       — basis of like-kind property received + the §1250/§1245/intangible split
      f4797_line16         — ordinary recapture (L21) → Form 4797 line 16
      f4797_line5          — recognized §1231 gain (L22) → Form 4797 line 5
      f4797_line10         — §1043 ordinary recapture (L35) → Form 4797 line 10
      sch_d_st / sch_d_lt  — recognized capital gain routed directly to Schedule D
      rp_accel_gain        — Part II §1031(f) accelerated deferred gain (routed by character)
    Or {'red_defer': [...]} for an unsupported path (multi-asset / §121-home / personal property)."""
    reasons = []
    if multi_asset:
        reasons.append("multi_asset_exchange")
    if property_used_as_home:
        reasons.append("section_121_home_use")
    if not is_real_property:
        reasons.append("personal_property_not_like_kind")  # post-2017 §1031 = real property only
    if reasons:
        return {"red_defer": reasons, "f4797_line5": None, "f4797_line16": None,
                "f4797_line10": None, "sch_d_lt": None, "l24": None, "l25": None}

    long_term = int(holding_period_months or 0) > 12

    # ════════════════ Part IV — §1043 conflict-of-interest divestiture ════════════════
    if is_1043:
        l30 = _D(sales_price_divested)                      # net of selling expenses
        l31 = _D(basis_divested)
        l32 = l30 - l31                                     # realized gain
        l33 = _D(cost_replacement_60day)
        l34 = max(Decimal("0"), l30 - l33)
        l35 = _D(recapture_1043)                            # → Form 4797 line 10
        l36 = max(Decimal("0"), l34 - l35)                  # → Schedule D / Form 4797 by character
        l37 = l32 - (l35 + l36)                             # deferred gain
        l38 = l33 - l37                                     # basis of replacement property
        gate_ok = l33 > l31                                 # Part IV only if replacement cost > divested basis
        f4797_line10 = l35
        sch_d_st = sch_d_lt = f4797_line2 = Decimal("0")
        if character_1043 == "capital":
            if long_term:
                sch_d_lt = l36
            else:
                sch_d_st = l36
        else:
            f4797_line2 = l36                               # business asset → Form 4797 line 2/10
        return {
            "l32": l32, "l34": l34, "l35": l35, "l36": l36, "l37": l37, "l38": l38,
            "f4797_line10": f4797_line10, "f4797_line2": f4797_line2,
            "sch_d_st": sch_d_st, "sch_d_lt": sch_d_lt,
            "is_1043": True, "section_1043_gate_ok": gate_ok,
            # null the §1031 keys so callers can treat the dict uniformly
            "l19": None, "l23": None, "l24": None, "l25": None,
            "f4797_line5": None, "f4797_line16": None,
        }

    # ════════════════ Part III — §1031 like-kind exchange ════════════════
    # L12-14 — gain/loss on NON-like-kind property given up (recognized as a sale, separate)
    l12 = _D(fmv_other_given_up)
    l13 = _D(basis_other_given_up)
    l14 = l12 - l13

    # L15 — boot received, with the §1.1031(d)-2 liability netting
    net_relief = (_D(liabilities_assumed_by_other)
                  - (_D(liabilities_you_assumed) + _D(cash_you_paid) + _D(fmv_nonlike_given_up)))
    net_liab_to_you = max(Decimal("0"), net_relief)         # boot to you (→ L15)
    net_paid_to_other = max(Decimal("0"), -net_relief)      # excess you paid (→ L18 basis given up)
    gross_15 = _D(cash_received) + _D(fmv_nonlike_received) + net_liab_to_you
    l15 = max(Decimal("0"), gross_15 - _D(exchange_expenses))
    exp_used_on_15 = gross_15 - l15                          # = min(exchange_expenses, gross_15)
    exp_remaining = _D(exchange_expenses) - exp_used_on_15   # unused expenses move to L18

    l16 = _D(fmv_likekind_received)
    l17 = l15 + l16
    l18 = _D(basis_likekind_given_up) + exp_remaining + net_paid_to_other
    l19 = l17 - l18                                          # realized gain or (loss)
    l20 = max(Decimal("0"), min(l15, l19))                   # recognized to the extent of boot

    # L21 — ordinary recapture, COMPUTED via the §1245(b)(4) and §1250(d)(4) limits
    recap_1245 = Decimal("0")
    if _D(depreciation_1245) > 0:
        nonlike1245_received = l16 - _D(fmv_1245_lk_received)   # FMV non-§1245 like-kind received
        test1 = min(_D(depreciation_1245), max(Decimal("0"), l19))
        test2 = l20 + nonlike1245_received
        recap_1245 = min(test1, test2)
    recap_1250 = Decimal("0")
    if _D(additional_depreciation_1250) > 0:
        addl = _D(additional_depreciation_1250)
        recap_1250 = min(addl, max(l20, addl - _D(fmv_1250_lk_received)))
    l21 = recap_1245 + recap_1250                            # → Form 4797 line 16

    l22 = max(Decimal("0"), l20 - l21)                       # → 4797 line 5 / Sch D
    l23 = l21 + l22                                          # recognized gain
    l24 = l19 if l19 < 0 else (l19 - l23)                    # deferred gain (a loss defers in full)

    # L25 — basis of like-kind property received + 25a/b/c proportional allocation
    l25 = (l18 + l23) - l15
    if l16 > 0:
        l25a = l25 * _D(fmv_1250_lk_received) / l16
        l25b = l25 * _D(fmv_1245_lk_received) / l16          # §1245, 1252, 1254, 1255
        l25c = l25 * _D(fmv_intangible_lk_received) / l16
    else:
        l25a = l25b = l25c = Decimal("0")

    # ── routing of the recognized like-kind gain ──
    f4797_line16 = l21                                       # ordinary recapture
    f4797_line5 = f4797_line16_gain = sch_d_st = sch_d_lt = Decimal("0")
    if property_character == "business_1231" and long_term:
        f4797_line5 = l22                                   # §1231 gain from like-kind exchanges
    elif property_character == "ordinary" or not long_term:
        f4797_line16_gain = l22                             # ordinary noncapital → 4797 line 16
    else:                                                    # capital asset
        if long_term:
            sch_d_lt = l22
        else:
            sch_d_st = l22
    f4797_line16_total = f4797_line16 + f4797_line16_gain    # recapture + any ordinary L22

    # ── Part II §1031(f): a related-party 2-year disposition accelerates the deferred gain ──
    rp_accel_gain = Decimal("0")
    rp_accel_fires = bool(related_party and is_followup_year and related_party_disposed
                          and not rp_exception)
    if rp_accel_fires:
        rp_accel_gain = max(Decimal("0"), _D(prior_year_deferred_gain))
        # routed by the same character as the original exchange property
        if property_character == "business_1231" and long_term:
            f4797_line5 += rp_accel_gain
        elif property_character == "ordinary" or not long_term:
            f4797_line16_total += rp_accel_gain
        elif long_term:
            sch_d_lt += rp_accel_gain
        else:
            sch_d_st += rp_accel_gain

    return {
        "l12": l12, "l13": l13, "l14": l14, "l15": l15, "l16": l16, "l17": l17, "l18": l18,
        "l19": l19, "l20": l20, "l21": l21, "l22": l22, "l23": l23, "l24": l24,
        "l25": l25, "l25a": l25a, "l25b": l25b, "l25c": l25c,
        "f4797_line5": f4797_line5, "f4797_line16": f4797_line16_total,
        "sch_d_st": sch_d_st, "sch_d_lt": sch_d_lt,
        "rp_accel_gain": rp_accel_gain, "rp_accel_fires": rp_accel_fires,
        "is_loss_deferred": l19 < 0, "is_1043": False,
        "net_liab_to_you": net_liab_to_you, "net_paid_to_other": net_paid_to_other,
    }


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("8824", "Form 8824 — Like-Kind Exchanges (and §1043 conflict-of-interest sales)"),
    ("like_kind_exchange", "§1031 like-kind exchange of real property — boot, realized/recognized/deferred gain, basis"),
    ("lke_recapture", "§1245(b)(4)/§1250(d)(4) — recapture limit in a like-kind exchange"),
    ("related_party_lke", "§1031(f) — related-party exchange + 2-year second-disposition acceleration"),
    ("section_1043", "§1043 — deferral of gain on conflict-of-interest divestitures"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_4797_INSTR",   # the recapture interplay (8824 L21→4797 L16, L22→4797 L5, L35→4797 L10)
]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRC_1031",
        "source_type": "statute", "source_rank": "primary_official", "jurisdiction_code": "FED",
        "title": "IRC §1031 — Exchange of Real Property Held for Productive Use or Investment",
        "citation": "26 U.S.C. §1031", "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:1031%20edition:prelim)",
        "current_status": "active", "is_substantive_authority": True, "is_filing_authority": False,
        "trust_score": 10.0, "requires_human_review": True,
        "notes": "Post-TCJA (2018+): nonrecognition applies ONLY to exchanges of real property held for business/investment. Gain recognized to the extent of boot; loss never recognized.",
        "topics": ["like_kind_exchange"],
        "excerpts": [
            {"excerpt_label": "§1031(a),(b),(c),(d) — nonrecognition, boot, basis",
             "location_reference": "§1031(a)-(d)",
             "excerpt_text": (
                 "No gain or loss is recognized on the exchange of real property held for productive use "
                 "in a trade or business or for investment if such property is exchanged solely for real "
                 "property of like kind to be so held (§1031(a); real property only for exchanges after "
                 "2017). If the taxpayer also receives money or non-like-kind property (boot), gain (but "
                 "not loss) is recognized to the extent of that money and the FMV of the other property "
                 "(§1031(b),(c)). The basis of the property received is the basis of the property given "
                 "up, decreased by money received and increased by gain (or decreased by loss) recognized "
                 "(§1031(d))."),
             "summary_text": "Real-property-only nonrecognition; gain recognized up to boot, no loss; substituted basis.",
             "is_key_excerpt": True},
        ],
    },
    {
        "source_code": "IRC_1031_F",
        "source_type": "statute", "source_rank": "primary_official", "jurisdiction_code": "FED",
        "title": "IRC §1031(f) — Special Rules for Exchanges Between Related Persons",
        "citation": "26 U.S.C. §1031(f)", "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:1031%20edition:prelim)",
        "current_status": "active", "is_substantive_authority": True, "is_filing_authority": False,
        "trust_score": 10.0, "requires_human_review": True,
        "notes": "A related party's (or your) disposition of the exchanged property within 2 years accelerates the previously-deferred gain, unless a §1031(f)(2) exception (death / involuntary conversion / no tax-avoidance) applies.",
        "topics": ["related_party_lke"],
        "excerpts": [
            {"excerpt_label": "§1031(f) — 2-year related-party rule",
             "location_reference": "§1031(f)(1),(2),(4)",
             "excerpt_text": (
                 "If a taxpayer exchanges property with a related person and before 2 years after the date "
                 "of the last transfer either the related person or the taxpayer disposes of the property "
                 "received, the nonrecognition does not apply and the gain is taken into account as of the "
                 "date of the disposition (§1031(f)(1)). Exceptions: a disposition after the death of "
                 "either party, a compulsory/involuntary conversion, or where it is established that "
                 "neither the exchange nor the disposition had tax avoidance as a principal purpose "
                 "(§1031(f)(2)). An exchange structured to avoid the related-party rules is not a "
                 "like-kind exchange (§1031(f)(4))."),
             "summary_text": "Disposition within 2 years (no exception) recognizes the previously-deferred gain.",
             "is_key_excerpt": True},
        ],
    },
    {
        "source_code": "IRC_1245_1250_LKE",
        "source_type": "statute", "source_rank": "primary_official", "jurisdiction_code": "FED",
        "title": "IRC §1245(b)(4) and §1250(d)(4) — Recapture Limit on Like-Kind Exchanges",
        "citation": "26 U.S.C. §1245(b)(4), §1250(d)(4)", "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:1245%20edition:prelim)",
        "current_status": "active", "is_substantive_authority": True, "is_filing_authority": False,
        "trust_score": 10.0, "requires_human_review": True,
        "notes": "Depreciation recapture is recognized in a like-kind exchange, limited to a lesser-of test involving the boot gain and the FMV of like-kind §1245/§1250 property received.",
        "topics": ["lke_recapture"],
        "excerpts": [
            {"excerpt_label": "§1245(b)(4)/§1250(d)(4) recapture-limit lesser-of tests",
             "location_reference": "§1245(b)(4), §1250(d)(4); Form 8824 line-21 instructions",
             "excerpt_text": (
                 "On a like-kind exchange of §1245 property, ordinary recapture is the smaller of (1) the "
                 "depreciation/amortization adjustments (up to the realized gain on line 19), or (2) the "
                 "gain recognized on line 20 plus the FMV of non-§1245 like-kind property received "
                 "(§1245(b)(4)). On a like-kind exchange of §1250 property, ordinary recapture is the "
                 "smaller of (1) the additional-depreciation ordinary income you would have on an outright "
                 "sale, or (2) the larger of (a) the line-20 gain or (b) the excess of (1) over the FMV of "
                 "the §1250 property received (§1250(d)(4)). §1252/1254/1255 follow the §1245 pattern."),
             "summary_text": "Recapture in an LKE = the §1245(b)(4)/§1250(d)(4) lesser-of limit; recognized even with little/no boot.",
             "is_key_excerpt": True},
        ],
    },
    {
        "source_code": "IRC_1043",
        "source_type": "statute", "source_rank": "primary_official", "jurisdiction_code": "FED",
        "title": "IRC §1043 — Sale of Property to Comply With Conflict-of-Interest Requirements",
        "citation": "26 U.S.C. §1043", "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:1043%20edition:prelim)",
        "current_status": "active", "is_substantive_authority": True, "is_filing_authority": False,
        "trust_score": 10.0, "requires_human_review": True,
        "notes": "An eligible federal officer/employee may elect to defer gain on a certificate-of-divestiture sale to the extent reinvested in permitted property within 60 days. Part IV of Form 8824.",
        "topics": ["section_1043"],
        "excerpts": [
            {"excerpt_label": "§1043 — conflict-of-interest divestiture deferral",
             "location_reference": "§1043(a),(b),(c)",
             "excerpt_text": (
                 "An eligible person who sells property pursuant to a certificate of divestiture recognizes "
                 "gain only to the extent the amount realized exceeds the cost of permitted replacement "
                 "property (any U.S. obligation or OGE-approved diversified investment fund) purchased "
                 "within the 60-day period beginning on the sale date (plus any ordinary recapture). The "
                 "basis of the replacement property is reduced by the deferred gain. Part IV is used only "
                 "if the cost of replacement property exceeds the basis of the divested property."),
             "summary_text": "Defer gain on a conflict-of-interest sale to the extent reinvested within 60 days; basis reduced by the deferral.",
             "is_key_excerpt": True},
        ],
    },
    {
        "source_code": "IRS_2025_8824_FORM",
        "source_type": "official_form", "source_rank": "primary_official", "jurisdiction_code": "FED",
        "tax_year_start": 2025, "tax_year_end": 2025,
        "title": "Form 8824 (2025) — Like-Kind Exchanges (with instructions)",
        "citation": "Form 8824 (2025), OMB 1545-0074", "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/f8824.pdf",
        "current_status": "active", "is_substantive_authority": False, "is_filing_authority": True,
        "trust_score": 9.5, "requires_human_review": False,
        "notes": "Verified line-by-line 2026-06-28 against the PDF (both pages) + the 2025 instructions (7 pages). The line-21/22 destinations to Form 4797 lines 16/5 and the line-35 destination to 4797 line 10 are quoted directly.",
        "topics": ["8824", "like_kind_exchange"],
        "excerpts": [
            {"excerpt_label": "Part III line-by-line (L12-L25) + boot / recapture / basis",
             "location_reference": "Form 8824 (2025), Part III",
             "excerpt_text": (
                 "L15 = cash received + FMV of other property received + net liabilities assumed by the "
                 "other party, reduced (not below 0) by exchange expenses. L16 = FMV of like-kind property "
                 "received. L17 = L15 + L16. L18 = adjusted basis of like-kind property given up + net "
                 "amount paid to the other party + exchange expenses not used on L15. L19 = L17 − L18 "
                 "(realized gain/loss). L20 = smaller of L15 or L19, not less than zero. L21 = ordinary "
                 "income under recapture rules → Form 4797 line 16. L22 = L20 − L21 (≥ 0) → Schedule D or "
                 "Form 4797. L23 = L21 + L22 (recognized gain). L24 = L19 − L23 (deferred gain/loss). "
                 "L25 = (L18 + L23) − L15 (basis of like-kind property received), allocated on 25a/25b/25c."),
             "summary_text": "Part III: realized (L19), recognized (L23), deferred (L24) gain + basis (L25); L21→4797 L16, L22→4797 L5/Sch D.",
             "is_key_excerpt": True},
            {"excerpt_label": "i8824 lines 15/18 liability-netting + lines 21/22 recapture & routing",
             "location_reference": "i8824 (2025), Lines 15, 18, 21, 22",
             "excerpt_text": (
                 "Line 15 net liabilities assumed by the other party = the excess of liabilities assumed "
                 "by the other party over the total of (a) liabilities you assumed, (b) cash you paid, and "
                 "(c) FMV of non-like-kind property you gave up. Line 18 net amount paid = the reverse "
                 "excess. Line 21 §1245 recapture = smaller of the depreciation adjustments (up to line 19) "
                 "or the line-20 gain plus the FMV of non-§1245 like-kind property received; §1250 = "
                 "smaller of the additional-depreciation ordinary income or the larger of the line-20 gain "
                 "or its excess over the FMV of §1250 property received. Line 22: a gain from business "
                 "property → Form 4797 line 5 or line 16; a capital-asset gain → Schedule D."),
             "summary_text": "Symmetric liability netting on L15/L18; computed §1245(b)(4)/§1250(d)(4) recapture; L22 routes to 4797 L5 or Sch D.",
             "is_key_excerpt": True},
            {"excerpt_label": "i8824 multi-asset / §121-home / Part IV §1043",
             "location_reference": "i8824 (2025), Multi-Asset Exchanges; Property Used as Home; Lines 30-38",
             "excerpt_text": (
                 "Multi-asset exchanges (more than one group of like-kind properties, or cash/other "
                 "property): don't complete lines 12-18; attach a statement and enter lines 19-25. Property "
                 "used as home: if the property given up was a main home, §121 may exclude gain using a "
                 "two-worksheet method. Part IV (§1043): L32 = L30 − L31 (realized gain); L34 = L30 − L33 "
                 "(≥ 0); L35 = ordinary recapture → Form 4797 line 10; L36 = L34 − L35 → Schedule D or "
                 "Form 4797; L37 = L32 − (L35 + L36) (deferred); L38 = L33 − L37 (basis of replacement)."),
             "summary_text": "Multi-asset & §121-home use special methods; Part IV §1043 lines 30-38; L35→4797 L10.",
             "is_key_excerpt": True},
        ],
    },
    {
        "source_code": "IRS_PUB_544",
        "source_type": "official_publication", "source_rank": "primary_official", "jurisdiction_code": "FED",
        "tax_year_start": 2025, "tax_year_end": 2025,
        "title": "IRS Publication 544 — Sales and Other Dispositions of Assets",
        "citation": "Publication 544 (2025)", "issuer": "IRS",
        "official_url": "https://www.irs.gov/pub/irs-pdf/p544.pdf",
        "current_status": "active", "is_substantive_authority": False, "is_filing_authority": False,
        "trust_score": 9.0, "requires_human_review": False,
        "notes": "Like-kind exchange mechanics, deferred-exchange 45/180-day rules, related-party 2-year holding period, qualified intermediaries / disqualified persons.",
        "topics": ["like_kind_exchange", "related_party_lke"],
        "excerpts": [
            {"excerpt_label": "Deferred-exchange 45-day / 180-day timing",
             "location_reference": "Pub 544, Like-Kind Exchanges — Deferred exchange",
             "excerpt_text": (
                 "For a deferred exchange to qualify, the replacement property must be identified in "
                 "writing within 45 days after you transfer the property given up, and must be received by "
                 "the earlier of 180 days after the transfer or the due date (with extensions) of your "
                 "return for the year of the transfer. Failure to meet these deadlines makes the "
                 "transaction taxable in the year of transfer."),
             "summary_text": "45-day written identification + 180-day receipt are hard deadlines for a deferred exchange.",
             "is_key_excerpt": True},
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRC_1031", "8824", "governs"),
    ("IRC_1031_F", "8824", "governs"),
    ("IRC_1245_1250_LKE", "8824", "governs"),
    ("IRC_1043", "8824", "governs"),
    ("IRS_2025_8824_FORM", "8824", "governs"),
    ("IRS_PUB_544", "8824", "informs"),
    ("IRS_2025_4797_INSTR", "8824", "informs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM: 8824
# ═══════════════════════════════════════════════════════════════════════════

P_IDENTITY = {
    "form_number": "8824",
    "form_title": "Like-Kind Exchanges (and section 1043 conflict-of-interest sales)",
    "notes": (
        "FULL-v1 1040 build (Ken 2026-06-28, AskUserQuestion 'Full incl. Part IV + computed "
        "recapture'): the whole Form 8824 — Part I (info + dates), Part II (related-party §1031(f) "
        "2-year acceleration), Part III (realized/recognized/deferred gain + basis with COMPUTED "
        "§1245(b)(4)/§1250(d)(4) recapture and the §1.1031(d)-2 liability netting), Part IV (§1043 "
        "conflict-of-interest). §1031 is REAL-PROPERTY ONLY for 2018+. Boot computed from components; "
        "L19 = L17 − L18; L20 = max(0, min(L15, L19)); L21 ordinary recapture → Form 4797 line 16; "
        "L22 = L20 − L21 → Form 4797 line 5 (business §1231 >1yr) / line 16 (ordinary) / Schedule D "
        "(capital); L23 = L21 + L22; L24 = L19 − L23 (a realized LOSS defers in full, never deducted); "
        "L25 = (L18 + L23) − L15 with 25a/b/c proportional allocation. Closes the Form 4797 line-5/16 "
        "RED-defer (D_4797_004). Part IV §1043: L35 → Form 4797 line 10; L37 deferred; L38 basis. "
        "RED-defers (no silent gap): multi-asset exchange, §121 main-home mixed-use combo, and a "
        "PERSONAL-property exchange (post-2017 §1031 is real-property only)."
    ),
}

P_FACTS: list[dict] = [
    # ── Part III — non-like-kind property given up (L12-14) ──
    {"fact_key": "f8824_fmv_other_given_up", "label": "FMV of other (non-like-kind) property given up (line 12)",
     "data_type": "decimal", "default_value": "0", "sort_order": 1},
    {"fact_key": "f8824_basis_other_given_up", "label": "Adjusted basis of other property given up (line 13)",
     "data_type": "decimal", "default_value": "0", "sort_order": 2},
    # ── Part III — boot received + liability netting (line 15 components) ──
    {"fact_key": "f8824_cash_received", "label": "Cash received from the other party (line 15)",
     "data_type": "decimal", "default_value": "0", "sort_order": 10},
    {"fact_key": "f8824_fmv_nonlike_received", "label": "FMV of other (non-like-kind) property received (line 15)",
     "data_type": "decimal", "default_value": "0", "sort_order": 11},
    {"fact_key": "f8824_exchange_expenses", "label": "Exchange expenses you incurred (reduce line 15, then line 18)",
     "data_type": "decimal", "default_value": "0", "sort_order": 12},
    {"fact_key": "f8824_liabilities_assumed_by_other", "label": "Liabilities assumed by the other party",
     "data_type": "decimal", "default_value": "0", "sort_order": 13,
     "notes": "Mortgages/debts on your property the other party took over (§1.1031(d)-2 netting)."},
    {"fact_key": "f8824_liabilities_you_assumed", "label": "Liabilities you assumed",
     "data_type": "decimal", "default_value": "0", "sort_order": 14},
    {"fact_key": "f8824_cash_you_paid", "label": "Cash you paid to the other party",
     "data_type": "decimal", "default_value": "0", "sort_order": 15},
    {"fact_key": "f8824_fmv_nonlike_given_up", "label": "FMV of other (non-like-kind) property you gave up (netting)",
     "data_type": "decimal", "default_value": "0", "sort_order": 16},
    # ── Part III — like-kind received / basis given up ──
    {"fact_key": "f8824_fmv_likekind_received", "label": "FMV of like-kind property you received (line 16)",
     "data_type": "decimal", "default_value": "0", "sort_order": 20},
    {"fact_key": "f8824_basis_likekind_given_up", "label": "Adjusted basis of like-kind property you gave up (line 18)",
     "data_type": "decimal", "default_value": "0", "sort_order": 21},
    # ── Part III — computed-recapture inputs ──
    {"fact_key": "f8824_depreciation_1245", "label": "§1245 depreciation/amortization adjustments (line 21 test)",
     "data_type": "decimal", "default_value": "0", "sort_order": 30,
     "notes": "Total deductions allowed/allowable; the §1245(b)(4) recapture test #1 (capped at line 19)."},
    {"fact_key": "f8824_fmv_1245_lk_received", "label": "FMV of like-kind §1245 property received",
     "data_type": "decimal", "default_value": "0", "sort_order": 31,
     "notes": "Used for the §1245(b)(4) 'non-§1245 like-kind received' test and the 25b allocation."},
    {"fact_key": "f8824_additional_depreciation_1250", "label": "§1250 additional depreciation (line 21 test)",
     "data_type": "decimal", "default_value": "0", "sort_order": 32,
     "notes": "§1250(a)(1)(A) ordinary income on an outright sale (i4797 line 26). Post-1986 SL = 0."},
    {"fact_key": "f8824_fmv_1250_lk_received", "label": "FMV of like-kind §1250 property received",
     "data_type": "decimal", "default_value": "0", "sort_order": 33,
     "notes": "Used for the §1250(d)(4) limit and the 25a allocation."},
    {"fact_key": "f8824_fmv_intangible_lk_received", "label": "FMV of like-kind intangible real property received",
     "data_type": "decimal", "default_value": "0", "sort_order": 34,
     "notes": "Used for the 25c allocation."},
    # ── character / holding period ──
    {"fact_key": "f8824_property_character", "label": "Character: capital / business_1231 / ordinary",
     "data_type": "string", "default_value": "capital", "sort_order": 40,
     "notes": "Drives line-22 routing (Sch D vs Form 4797 line 5/16)."},
    {"fact_key": "f8824_holding_period_months", "label": "Holding period of like-kind property given up (months)",
     "data_type": "integer", "default_value": "0", "sort_order": 41},
    # ── Part I — dates (deferred-exchange deadline diagnostics) ──
    {"fact_key": "f8824_related_party", "label": "Exchange made with a related party? (line 7)",
     "data_type": "boolean", "default_value": "false", "sort_order": 50},
    {"fact_key": "f8824_days_to_identify", "label": "Days from transfer (line 4) to written identification (line 5)",
     "data_type": "integer", "default_value": "0", "sort_order": 51,
     "notes": "Deferred-exchange 45-day test (Pub 544). Blank/None = not a deferred exchange."},
    {"fact_key": "f8824_days_to_receive", "label": "Days from transfer (line 4) to receipt (line 6)",
     "data_type": "integer", "default_value": "0", "sort_order": 52,
     "notes": "Deferred-exchange 180-day test (Pub 544)."},
    # ── Part II — related-party §1031(f) acceleration ──
    {"fact_key": "f8824_is_followup_year", "label": "Filing for one of the 2 years AFTER a related-party exchange?",
     "data_type": "boolean", "default_value": "false", "sort_order": 60},
    {"fact_key": "f8824_related_party_disposed", "label": "Related party (line 9) or you (line 10) disposed within 2 yrs?",
     "data_type": "boolean", "default_value": "false", "sort_order": 61},
    {"fact_key": "f8824_rp_exception", "label": "Line-11 exception (a death / b involuntary / c no-tax-avoidance)",
     "data_type": "string", "default_value": "", "sort_order": 62,
     "notes": "Non-empty → no §1031(f) acceleration."},
    {"fact_key": "f8824_prior_year_deferred_gain", "label": "Deferred gain from the original exchange (prior-year line 24)",
     "data_type": "decimal", "default_value": "0", "sort_order": 63,
     "notes": "Recognized this year if the §1031(f) 2-year rule fires. Preparer-asserted."},
    # ── Part IV — §1043 conflict-of-interest ──
    {"fact_key": "f8824_is_1043", "label": "§1043 conflict-of-interest divestiture (use Part IV)?",
     "data_type": "boolean", "default_value": "false", "sort_order": 70,
     "notes": "Federal executive-branch/judicial officers only."},
    {"fact_key": "f8824_sales_price_divested", "label": "Sales price of divested property, net of selling expenses (line 30)",
     "data_type": "decimal", "default_value": "0", "sort_order": 71},
    {"fact_key": "f8824_basis_divested", "label": "Basis of divested property (line 31)",
     "data_type": "decimal", "default_value": "0", "sort_order": 72},
    {"fact_key": "f8824_cost_replacement_60day", "label": "Cost of replacement property bought within 60 days (line 33)",
     "data_type": "decimal", "default_value": "0", "sort_order": 73},
    {"fact_key": "f8824_recapture_1043", "label": "§1043 ordinary recapture (4797 Part III worksheet, line 35)",
     "data_type": "decimal", "default_value": "0", "sort_order": 74,
     "notes": "Preparer-asserted from a Form 4797 Part III worksheet → Form 4797 line 10."},
    {"fact_key": "f8824_character_1043", "label": "§1043 divested-property character: capital / business",
     "data_type": "string", "default_value": "capital", "sort_order": 75},
    # ── red-defer flags ──
    {"fact_key": "f8824_multi_asset", "label": "Multi-asset exchange (>1 like-kind group or cash/other property)?",
     "data_type": "boolean", "default_value": "false", "sort_order": 80,
     "notes": "i8824 says skip lines 12-18 + attach a statement → RED-defer."},
    {"fact_key": "f8824_property_used_as_home", "label": "Property given up was used as a main home (§121 combo)?",
     "data_type": "boolean", "default_value": "false", "sort_order": 81,
     "notes": "Two-worksheet §121/§1031 method → RED-defer."},
    {"fact_key": "f8824_is_real_property", "label": "Is the exchanged property REAL property?",
     "data_type": "boolean", "default_value": "true", "sort_order": 82,
     "notes": "Post-2017 §1031 applies to real property only; personal property → RED-defer."},
    # ── outputs ──
    {"fact_key": "f8824_line19", "label": "Realized gain or (loss) (line 19)", "data_type": "decimal",
     "sort_order": 90, "notes": "OUTPUT."},
    {"fact_key": "f8824_line23", "label": "Recognized gain (line 23)", "data_type": "decimal",
     "sort_order": 91, "notes": "OUTPUT = L21 + L22."},
    {"fact_key": "f8824_line24", "label": "Deferred gain or (loss) (line 24)", "data_type": "decimal",
     "sort_order": 92, "notes": "OUTPUT = L19 − L23 (a loss defers in full)."},
    {"fact_key": "f8824_line25", "label": "Basis of like-kind property received (line 25)", "data_type": "decimal",
     "sort_order": 93, "notes": "OUTPUT = (L18 + L23) − L15."},
    {"fact_key": "f8824_f4797_line16", "label": "Ordinary recapture (line 21) → Form 4797 line 16",
     "data_type": "decimal", "sort_order": 94, "notes": "OUTPUT."},
    {"fact_key": "f8824_f4797_line5", "label": "Recognized §1231 gain (line 22) → Form 4797 line 5",
     "data_type": "decimal", "sort_order": 95, "notes": "OUTPUT — closes D_4797_004."},
    {"fact_key": "f8824_f4797_line10", "label": "§1043 ordinary recapture (line 35) → Form 4797 line 10",
     "data_type": "decimal", "sort_order": 96, "notes": "OUTPUT (Part IV)."},
]

P_RULES: list[dict] = [
    {"rule_id": "R-8824-BOOT", "title": "Boot received + liability netting (lines 15-18)", "rule_type": "calculation",
     "precedence": 1, "sort_order": 1,
     "formula": ("net_relief = liab_assumed_by_other − (liab_you_assumed + cash_you_paid + "
                 "fmv_nonlike_given_up); L15 = max(0, cash_received + fmv_nonlike_received + "
                 "max(0,net_relief) − exchange_expenses); L17 = L15 + L16; L18 = basis_likekind_given_up "
                 "+ unused_exchange_expenses + max(0,−net_relief)."),
     "inputs": ["f8824_cash_received", "f8824_fmv_nonlike_received", "f8824_exchange_expenses",
                "f8824_liabilities_assumed_by_other", "f8824_liabilities_you_assumed",
                "f8824_cash_you_paid", "f8824_fmv_nonlike_given_up", "f8824_fmv_likekind_received",
                "f8824_basis_likekind_given_up"],
     "outputs": [],
     "description": "§1.1031(d)-2 symmetric liability netting; boot (L15) and basis given up (L18)."},
    {"rule_id": "R-8824-GAIN", "title": "Realized / recognized / deferred gain (lines 19-24)", "rule_type": "calculation",
     "precedence": 2, "sort_order": 2,
     "formula": ("L19 = L17 − L18; L20 = max(0, min(L15, L19)); L22 = max(0, L20 − L21); "
                 "L23 = L21 + L22; L24 = L19 if L19 < 0 else L19 − L23."),
     "inputs": [],
     "outputs": ["f8824_line19", "f8824_line23", "f8824_line24"],
     "description": "Gain recognized to the extent of boot; a realized loss defers in full (never deducted)."},
    {"rule_id": "R-8824-RECAP", "title": "Ordinary recapture, computed (line 21)", "rule_type": "calculation",
     "precedence": 3, "sort_order": 3,
     "formula": ("§1245(b)(4): min( min(depr_1245, max(0,L19)), L20 + (L16 − fmv_1245_lk_received) ). "
                 "§1250(d)(4): min( addl_depr_1250, max(L20, addl_depr_1250 − fmv_1250_lk_received) ). "
                 "L21 = §1245 part + §1250 part."),
     "inputs": ["f8824_depreciation_1245", "f8824_fmv_1245_lk_received",
                "f8824_additional_depreciation_1250", "f8824_fmv_1250_lk_received"],
     "outputs": ["f8824_f4797_line16"],
     "description": "Depreciation recapture is recognized in an LKE, limited by the §1245(b)(4)/§1250(d)(4) lesser-of tests."},
    {"rule_id": "R-8824-BASIS", "title": "Basis of like-kind property received + 25a/b/c (line 25)", "rule_type": "calculation",
     "precedence": 4, "sort_order": 4,
     "formula": ("L25 = (L18 + L23) − L15; 25a = L25 × fmv_1250_received/L16; 25b = L25 × "
                 "fmv_1245_received/L16; 25c = L25 × fmv_intangible_received/L16."),
     "inputs": ["f8824_fmv_1250_lk_received", "f8824_fmv_1245_lk_received", "f8824_fmv_intangible_lk_received"],
     "outputs": ["f8824_line25"],
     "description": "Substituted basis carryover; allocated to §1250/§1245/intangible like-kind property received by FMV."},
    {"rule_id": "R-8824-ROUTE", "title": "Route L21/L22 to Form 4797 / Schedule D", "rule_type": "routing",
     "precedence": 5, "sort_order": 5,
     "formula": ("L21 → Form 4797 line 16. L22: business §1231 >1yr → Form 4797 line 5; ordinary/≤1yr → "
                 "Form 4797 line 16; capital → Schedule D (ST/LT)."),
     "inputs": ["f8824_property_character", "f8824_holding_period_months"],
     "outputs": ["f8824_f4797_line5", "f8824_f4797_line16"],
     "description": "Closes the Form 4797 D_4797_004 like-kind RED-defer (lines 5 and 16)."},
    {"rule_id": "R-8824-RELPARTY", "title": "§1031(f) related-party 2-year acceleration (Part II)", "rule_type": "calculation",
     "precedence": 6, "sort_order": 6,
     "formula": ("If related_party AND is_followup_year AND related_party_disposed AND no line-11 "
                 "exception: recognize the prior-year deferred gain (line 24) this year, routed by character."),
     "inputs": ["f8824_related_party", "f8824_is_followup_year", "f8824_related_party_disposed",
                "f8824_rp_exception", "f8824_prior_year_deferred_gain"],
     "outputs": [],
     "description": "A disposition within 2 years of a related-party exchange recognizes the deferred gain."},
    {"rule_id": "R-8824-1043", "title": "§1043 conflict-of-interest divestiture (Part IV)", "rule_type": "calculation",
     "precedence": 7, "sort_order": 7,
     "formula": ("L32 = L30 − L31; L34 = max(0, L30 − L33); L35 → Form 4797 line 10; L36 = max(0, L34 − "
                 "L35) → Sch D/4797; L37 = L32 − (L35 + L36); L38 = L33 − L37."),
     "inputs": ["f8824_is_1043", "f8824_sales_price_divested", "f8824_basis_divested",
                "f8824_cost_replacement_60day", "f8824_recapture_1043", "f8824_character_1043"],
     "outputs": ["f8824_f4797_line10"],
     "description": "Defer gain to the extent reinvested within 60 days; basis of replacement reduced by the deferral."},
]

P_LINES: list[dict] = [
    {"line_number": "3", "description": "Line 3 — date like-kind property given up was originally acquired", "line_type": "input"},
    {"line_number": "4", "description": "Line 4 — date you transferred your property to the other party", "line_type": "input"},
    {"line_number": "5", "description": "Line 5 — date replacement property identified (45-day written ID)", "line_type": "input"},
    {"line_number": "6", "description": "Line 6 — date you received the like-kind property (180-day rule)", "line_type": "input"},
    {"line_number": "7", "description": "Line 7 — exchange with a related party? (Yes → Part II)", "line_type": "input"},
    {"line_number": "9", "description": "Line 9 — related party disposed within 2 years?", "line_type": "input"},
    {"line_number": "10", "description": "Line 10 — you disposed within 2 years?", "line_type": "input"},
    {"line_number": "11", "description": "Line 11 — exception (a death / b involuntary / c no-tax-avoidance)", "line_type": "input"},
    {"line_number": "12", "description": "Line 12 — FMV of other (non-like-kind) property given up", "line_type": "input"},
    {"line_number": "13", "description": "Line 13 — adjusted basis of other property given up", "line_type": "input"},
    {"line_number": "14", "description": "Line 14 — gain/(loss) on other property given up (line 12 − line 13)",
     "line_type": "calculated", "destination_form": "Report as a sale by character (Schedule D / Form 4797)"},
    {"line_number": "15", "description": "Line 15 — cash + FMV non-like-kind received + net liabilities assumed, less expenses", "line_type": "calculated"},
    {"line_number": "16", "description": "Line 16 — FMV of like-kind property you received", "line_type": "input"},
    {"line_number": "17", "description": "Line 17 — add lines 15 and 16", "line_type": "calculated"},
    {"line_number": "18", "description": "Line 18 — adjusted basis of like-kind given up + net paid + unused expenses", "line_type": "calculated"},
    {"line_number": "19", "description": "Line 19 — realized gain or (loss) (line 17 − line 18)", "line_type": "calculated"},
    {"line_number": "20", "description": "Line 20 — smaller of line 15 or line 19, not less than zero", "line_type": "calculated"},
    {"line_number": "21", "description": "Line 21 — ordinary income under recapture rules",
     "line_type": "total", "destination_form": "Form 4797 line 16 (ordinary recapture)"},
    {"line_number": "22", "description": "Line 22 — line 20 minus line 21 (recognized capital/§1231 gain)",
     "line_type": "total", "destination_form": "Form 4797 line 5 (business §1231) or Schedule D (capital)"},
    {"line_number": "23", "description": "Line 23 — recognized gain (line 21 + line 22)", "line_type": "calculated"},
    {"line_number": "24", "description": "Line 24 — deferred gain or (loss) (line 19 − line 23)", "line_type": "calculated"},
    {"line_number": "25", "description": "Line 25 — basis of like-kind property received ((L18 + L23) − L15)", "line_type": "calculated"},
    {"line_number": "25a", "description": "Line 25a — basis allocated to like-kind §1250 property received", "line_type": "calculated"},
    {"line_number": "25b", "description": "Line 25b — basis allocated to like-kind §1245/1252/1254/1255 property", "line_type": "calculated"},
    {"line_number": "25c", "description": "Line 25c — basis allocated to like-kind intangible property", "line_type": "calculated"},
    {"line_number": "30", "description": "Line 30 — sales price of divested property (§1043), net of expenses", "line_type": "input"},
    {"line_number": "31", "description": "Line 31 — basis of divested property (§1043)", "line_type": "input"},
    {"line_number": "32", "description": "Line 32 — realized gain (line 30 − line 31) (§1043)", "line_type": "calculated"},
    {"line_number": "33", "description": "Line 33 — cost of replacement property within 60 days (§1043)", "line_type": "input"},
    {"line_number": "34", "description": "Line 34 — line 30 − line 33, if ≤ 0 enter 0 (§1043)", "line_type": "calculated"},
    {"line_number": "35", "description": "Line 35 — ordinary income under recapture rules (§1043)",
     "line_type": "total", "destination_form": "Form 4797 line 10"},
    {"line_number": "36", "description": "Line 36 — line 34 − line 35 (§1043)",
     "line_type": "total", "destination_form": "Schedule D or Form 4797 (by character)"},
    {"line_number": "37", "description": "Line 37 — deferred gain, line 32 − (line 35 + line 36) (§1043)", "line_type": "calculated"},
    {"line_number": "38", "description": "Line 38 — basis of replacement property, line 33 − line 37 (§1043)", "line_type": "calculated"},
    {"line_number": "rp_accel", "description": "§1031(f) Part II — prior-year deferred gain recognized this year (not a line)",
     "line_type": "total", "destination_form": "Schedule D or Form 4797 (by character)"},
]

P_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_8824_001", "title": "45-day identification deadline missed", "severity": "error",
     "condition": "days_to_identify > 45",
     "message": ("The replacement property was identified more than 45 days after you transferred the "
                 "property given up. A deferred exchange that misses the 45-day written-identification "
                 "deadline does not qualify under §1031 — the gain is generally taxable in the year of "
                 "transfer. Verify the dates on lines 4 and 5."),
     "notes": "Pub 544 deferred-exchange 45-day rule."},
    {"diagnostic_id": "D_8824_002", "title": "180-day receipt deadline missed", "severity": "error",
     "condition": "days_to_receive > 180",
     "message": ("The like-kind property was received more than 180 days after you transferred the "
                 "property given up (and the receipt must also be by your return due date including "
                 "extensions). A deferred exchange that misses the 180-day deadline does not qualify — "
                 "the gain is generally taxable in the year of transfer."),
     "notes": "Pub 544 deferred-exchange 180-day rule."},
    {"diagnostic_id": "D_8824_003", "title": "Related-party exchange — file for 2 years; watch §1031(f)", "severity": "warning",
     "condition": "related_party (line 7 = Yes)",
     "message": ("This exchange was made with a related party. You must file Form 8824 for this year and "
                 "the 2 following years. If either party disposes of the exchanged property within 2 "
                 "years (and no line-11 exception applies), the deferred gain becomes taxable in the year "
                 "of disposition (§1031(f))."),
     "notes": "§1031(f) reminder."},
    {"diagnostic_id": "D_8824_004", "title": "§1031(f) 2-year rule — deferred gain recognized now", "severity": "warning",
     "condition": "is_followup_year AND related_party_disposed AND no line-11 exception",
     "message": ("A related party (line 9) or you (line 10) disposed of the exchanged property within 2 "
                 "years of a related-party exchange, and no line-11 exception applies. The previously "
                 "deferred gain from the original Form 8824 line 24 is recognized this year and reported "
                 "by character (Schedule D or Form 4797). Confirm the prior-year deferred gain amount."),
     "notes": "§1031(f)(1) acceleration. Routed by character."},
    {"diagnostic_id": "D_8824_005", "title": "Like-kind realized LOSS is not deductible", "severity": "warning",
     "condition": "line 19 < 0",
     "message": ("Line 19 is a realized LOSS. A loss on a like-kind exchange is NOT recognized — it is "
                 "deferred into the basis of the property received (line 25), never deducted. If you want "
                 "to claim the loss, the transaction must not be reported as a like-kind exchange."),
     "notes": "§1031(c) — no loss recognized. No-silent-gap (prevents deducting a deferred loss)."},
    {"diagnostic_id": "D_8824_006", "title": "Depreciation recapture present — verify the line-21 limit", "severity": "warning",
     "condition": "depreciation_1245 > 0 OR additional_depreciation_1250 > 0",
     "message": ("This exchange involves §1245 or §1250 depreciable property. Ordinary recapture (line "
                 "21 → Form 4797 line 16) is computed via the §1245(b)(4)/§1250(d)(4) lesser-of limits. "
                 "Confirm the depreciation adjustments and the FMV of like-kind §1245/§1250 property "
                 "received that drive the limit."),
     "notes": "i8824 line 21. Computed (not preparer-asserted) per Ken's scope choice."},
    {"diagnostic_id": "D_8824_007", "title": "Multi-asset exchange not supported", "severity": "error",
     "condition": "multi_asset",
     "message": ("This is a multi-asset exchange (more than one group of like-kind properties, or cash/"
                 "other property requiring the special method). Per the instructions you skip lines 12-18 "
                 "and attach your own statement showing how you figured realized and recognized gain. "
                 "This is not modeled in this version — prepare Form 8824 manually."),
     "notes": "v1 RED-defer (Reg. §1.1031(j)-1)."},
    {"diagnostic_id": "D_8824_008", "title": "§121 main-home exclusion combo not supported", "severity": "error",
     "condition": "property_used_as_home",
     "message": ("The property given up was used as a main home, so the §121 exclusion may combine with "
                 "§1031 (the two-worksheet method in the instructions). This combination is not modeled "
                 "in this version — prepare Form 8824 manually (see Rev. Proc. 2005-14)."),
     "notes": "v1 RED-defer."},
    {"diagnostic_id": "D_8824_009", "title": "Personal property — §1031 no longer applies", "severity": "error",
     "condition": "NOT is_real_property",
     "message": ("For exchanges after 2017, §1031 like-kind treatment applies ONLY to real property held "
                 "for business or investment. An exchange of personal property (vehicles, equipment, "
                 "intangibles other than real property) is fully taxable — report it on Form 4797, Form "
                 "8949, or Schedule D, not on Form 8824."),
     "notes": "v1 RED-defer (TCJA §13303). No-silent-gap."},
    {"diagnostic_id": "D_8824_010", "title": "§1043 — eligible federal officers/employees only", "severity": "info",
     "condition": "is_1043",
     "message": ("Part IV (§1043 conflict-of-interest deferral) may be used ONLY by officers/employees of "
                 "the federal executive branch or judicial officers (and certain family/trustees) selling "
                 "under a certificate of divestiture. Complete Part IV only if the cost of the replacement "
                 "property exceeds the basis of the divested property and you elect to defer."),
     "notes": "§1043 eligibility reminder."},
]

P_SCENARIOS: list[dict] = [
    {"scenario_name": "F8824-T1 — pure like-kind, no boot, all deferred", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"basis_likekind_given_up": 100000, "fmv_likekind_received": 120000,
                "property_character": "business_1231", "holding_period_months": 60},
     "expected_outputs": {"f8824_line19": 20000, "f8824_line23": 0, "f8824_line24": 20000,
                          "f8824_line25": 100000, "f8824_f4797_line5": 0, "f8824_f4797_line16": 0},
     "notes": "L17 120000, L18 100000, L19 20000 realized; no boot → L20 0, recognized 0; L24 20000 deferred; basis carries 100000."},
    {"scenario_name": "F8824-T2 — boot (cash + mortgage relief), §1231, recognized to boot", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"cash_received": 40000, "fmv_likekind_received": 250000, "basis_likekind_given_up": 100000,
                "liabilities_assumed_by_other": 80000, "liabilities_you_assumed": 150000,
                "property_character": "business_1231", "holding_period_months": 60},
     "expected_outputs": {"f8824_line15": 40000, "f8824_line19": 120000, "f8824_line23": 40000,
                          "f8824_line24": 80000, "f8824_line25": 170000, "f8824_f4797_line5": 40000},
     "notes": ("i8824 Taylor example (no §1245): net_relief = 80000−150000 = −70000 → L18 = 100000+70000 = "
               "170000; L15 = 40000; L19 = 290000−170000 = 120000; L20 = 40000; no recapture; L23 40000 → "
               "4797 L5; L24 80000; basis 170000.")},
    {"scenario_name": "F8824-T3 — §1245 recapture computed (line 21 = 35000)", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"cash_received": 40000, "fmv_likekind_received": 250000, "basis_likekind_given_up": 100000,
                "liabilities_assumed_by_other": 80000, "liabilities_you_assumed": 150000,
                "depreciation_1245": 35000, "fmv_1245_lk_received": 0, "fmv_1250_lk_received": 250000,
                "property_character": "business_1231", "holding_period_months": 60},
     "expected_outputs": {"f8824_line19": 120000, "f8824_f4797_line16": 35000, "f8824_f4797_line5": 5000,
                          "f8824_line23": 40000, "f8824_line24": 80000},
     "notes": ("i8824 Taylor §1245 example: L21 = min(min(35000,120000), 40000+(250000−0)) = 35000 → 4797 "
               "L16; L22 = 40000−35000 = 5000 → 4797 L5; L23 40000; L24 80000.")},
    {"scenario_name": "F8824-T4 — §1250 recapture computed (Finley, line 21 = 30000)", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"cash_you_paid": 40000, "fmv_likekind_received": 220000, "basis_likekind_given_up": 175000,
                "liabilities_assumed_by_other": 150000, "liabilities_you_assumed": 80000,
                "additional_depreciation_1250": 35000, "fmv_1250_lk_received": 165000, "fmv_1245_lk_received": 55000,
                "property_character": "business_1231", "holding_period_months": 60},
     "expected_outputs": {"f8824_line15": 30000, "f8824_line19": 75000, "f8824_f4797_line16": 30000,
                          "f8824_line23": 30000, "f8824_line24": 45000, "f8824_line25": 175000,
                          "f8824_line25a": 131250, "f8824_line25b": 43750},
     "notes": ("i8824 Finley §1250 example: net_relief = 150000−(80000+40000) = 30000 → L15 30000; L18 175000; "
               "L19 75000; L20 30000; L21 = min(35000, max(30000, 35000−165000)) = 30000 → 4797 L16; L22 0; "
               "L23 30000; L24 45000; basis 175000 → 25a 131250, 25b 43750.")},
    {"scenario_name": "F8824-T5 — like-kind LOSS deferred (not deductible)", "scenario_type": "edge_case", "sort_order": 5,
     "inputs": {"basis_likekind_given_up": 120000, "fmv_likekind_received": 100000,
                "property_character": "capital", "holding_period_months": 60},
     "expected_outputs": {"f8824_line19": -20000, "f8824_line23": 0, "f8824_line24": -20000,
                          "f8824_line25": 120000, "D_8824_005": True},
     "notes": "L19 = 100000−120000 = −20000; loss not recognized; L24 −20000 deferred into basis 120000."},
    {"scenario_name": "F8824-T6 — capital asset, boot → Schedule D long-term", "scenario_type": "normal", "sort_order": 6,
     "inputs": {"cash_received": 30000, "fmv_likekind_received": 200000, "basis_likekind_given_up": 150000,
                "property_character": "capital", "holding_period_months": 60},
     "expected_outputs": {"f8824_line19": 80000, "f8824_line23": 30000, "f8824_line24": 50000,
                          "sch_d_lt": 30000, "f8824_line25": 150000},
     "notes": "L17 230000, L18 150000, L19 80000; L20 = min(30000,80000) = 30000 → Sch D LT; L24 50000; basis 150000."},
    {"scenario_name": "F8824-T7 — Part IV §1043 conflict-of-interest divestiture", "scenario_type": "edge_case", "sort_order": 7,
     "inputs": {"is_1043": True, "sales_price_divested": 200000, "basis_divested": 50000,
                "cost_replacement_60day": 180000, "recapture_1043": 0,
                "character_1043": "capital", "holding_period_months": 60},
     "expected_outputs": {"f8824_line32": 150000, "f8824_line34": 20000, "f8824_line37": 130000,
                          "f8824_line38": 50000, "sch_d_lt": 20000},
     "notes": "L32 150000; L34 = max(0, 200000−180000) = 20000; L35 0; L36 20000 → Sch D LT; L37 130000 deferred; L38 50000 basis."},
    {"scenario_name": "F8824-T8 — §1031(f) related-party 2-year acceleration", "scenario_type": "edge_case", "sort_order": 8,
     "inputs": {"related_party": True, "is_followup_year": True, "related_party_disposed": True,
                "prior_year_deferred_gain": 60000, "property_character": "business_1231",
                "holding_period_months": 60},
     "expected_outputs": {"f8824_f4797_line5": 60000, "D_8824_004": True},
     "notes": "Follow-up year, related party disposed, no exception → recognize the prior-year deferred gain 60000 → 4797 L5."},
    {"scenario_name": "F8824-G1 — multi-asset exchange → RED-defer", "scenario_type": "diagnostic", "sort_order": 9,
     "inputs": {"multi_asset": True, "fmv_likekind_received": 100000, "basis_likekind_given_up": 80000},
     "expected_outputs": {"D_8824_007": True},
     "notes": "Multi-asset → skip lines 12-18, attach statement → RED-defer."},
    {"scenario_name": "F8824-G2 — personal property → §1031 inapplicable (RED-defer)", "scenario_type": "diagnostic", "sort_order": 10,
     "inputs": {"is_real_property": False, "fmv_likekind_received": 50000, "basis_likekind_given_up": 30000},
     "expected_outputs": {"D_8824_009": True},
     "notes": "Post-2017 §1031 is real-property only; personal property is fully taxable → RED-defer."},
    {"scenario_name": "F8824-G3 — §121 main-home combo → RED-defer", "scenario_type": "diagnostic", "sort_order": 11,
     "inputs": {"property_used_as_home": True, "fmv_likekind_received": 300000, "basis_likekind_given_up": 100000},
     "expected_outputs": {"D_8824_008": True},
     "notes": "§121/§1031 two-worksheet method → RED-defer."},
]

P_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-8824-BOOT", "IRS_2025_8824_FORM", "primary", "Lines 15-18 boot + liability netting"),
    ("R-8824-BOOT", "IRC_1031", "secondary", "§1031(b) boot recognition"),
    ("R-8824-GAIN", "IRS_2025_8824_FORM", "primary", "Lines 19-24 realized/recognized/deferred gain"),
    ("R-8824-GAIN", "IRC_1031", "secondary", "§1031(a)-(c) nonrecognition + boot limit"),
    ("R-8824-RECAP", "IRC_1245_1250_LKE", "primary", "§1245(b)(4)/§1250(d)(4) recapture limit"),
    ("R-8824-RECAP", "IRS_2025_8824_FORM", "secondary", "Line 21 recapture computation"),
    ("R-8824-BASIS", "IRS_2025_8824_FORM", "primary", "Line 25 basis + 25a/b/c allocation"),
    ("R-8824-BASIS", "IRC_1031", "secondary", "§1031(d) substituted basis"),
    ("R-8824-ROUTE", "IRS_2025_8824_FORM", "primary", "Lines 21/22 destinations to Form 4797 lines 16/5"),
    ("R-8824-ROUTE", "IRS_2025_4797_INSTR", "secondary", "Form 4797 lines 5 and 16 receive the 8824 amounts"),
    ("R-8824-RELPARTY", "IRC_1031_F", "primary", "§1031(f) related-party 2-year acceleration"),
    ("R-8824-RELPARTY", "IRS_2025_8824_FORM", "secondary", "Part II lines 9-11"),
    ("R-8824-1043", "IRC_1043", "primary", "§1043 conflict-of-interest deferral"),
    ("R-8824-1043", "IRS_2025_8824_FORM", "secondary", "Part IV lines 30-38; L35 → 4797 line 10"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-8824-01", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "Realized gain L19 = L17 − L18 (with liability netting)",
     "description": "Validates R-8824-BOOT/GAIN. Bug it catches: not netting liabilities symmetrically into L15/L18.",
     "definition": {"kind": "reconciliation", "form": "8824",
                    "formula": "net_relief = liab_other − (liab_you + cash_you + fmv_nonlike_you); L19 = (L15+L16) − L18"},
     "sort_order": 1},
    {"assertion_id": "FA-1040-8824-02", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "Recognized gain L23 = L21 + L22; L20 = max(0, min(L15, L19))",
     "description": "Validates R-8824-GAIN. Bug it catches: recognizing gain beyond boot when there is no recapture.",
     "definition": {"kind": "reconciliation", "form": "8824",
                    "formula": "L20 = max(0, min(L15, L19)); L22 = max(0, L20 − L21); L23 = L21 + L22"},
     "sort_order": 2},
    {"assertion_id": "FA-1040-8824-03", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "Computed recapture L21 via §1245(b)(4)/§1250(d)(4)",
     "description": "Validates R-8824-RECAP. Bug it catches: omitting the recapture limit or the FMV-received offset.",
     "definition": {"kind": "reconciliation", "form": "8824",
                    "formula": ("§1245: min(min(depr,max(0,L19)), L20+(L16−fmv1245)); "
                                "§1250: min(addl, max(L20, addl−fmv1250))")},
     "sort_order": 3},
    {"assertion_id": "FA-1040-8824-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Ordinary recapture L21 → Form 4797 line 16 (closes D_4797_004)",
     "description": "Validates the 8824 ↔ 4797 ordinary leg. Bug it catches: like-kind recapture not feeding 4797 line 16.",
     "definition": {"kind": "flow_assertion", "form": "8824",
                    "checks": [{"source_line": "21", "must_write_to": ["F4797.16"]}]},
     "sort_order": 4},
    {"assertion_id": "FA-1040-8824-05", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Recognized §1231 gain L22 → Form 4797 line 5 (closes D_4797_004)",
     "description": "Validates the 8824 ↔ 4797 §1231 leg. Bug it catches: like-kind recognized gain not feeding 4797 line 5.",
     "definition": {"kind": "flow_assertion", "form": "8824",
                    "checks": [{"source_line": "22", "must_write_to": ["F4797.5"]}]},
     "sort_order": 5},
    {"assertion_id": "FA-1040-8824-06", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Capital-asset recognized gain L22 → Schedule D",
     "description": "Validates R-8824-ROUTE capital leg. Bug it catches: like-kind capital gain not reaching Schedule D.",
     "definition": {"kind": "flow_assertion", "form": "8824",
                    "checks": [{"source_line": "22", "must_write_to": ["SCH_D"]}]},
     "sort_order": 6},
    {"assertion_id": "FA-1040-8824-07", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "Deferred gain L24 = L19 − L23 (loss defers in full); basis L25 = (L18+L23) − L15",
     "description": "Validates R-8824-GAIN/BASIS. Bug it catches: deducting a like-kind loss, or wrong substituted basis.",
     "definition": {"kind": "reconciliation", "form": "8824",
                    "formula": "L24 = L19 if L19<0 else L19−L23; L25 = (L18+L23)−L15; 25a/b/c proportional to FMV"},
     "sort_order": 7},
    {"assertion_id": "FA-1040-8824-08", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "Part IV §1043: L35 → Form 4797 line 10; L37 deferred; L38 basis",
     "description": "Validates R-8824-1043. Bug it catches: wrong §1043 deferral or replacement basis.",
     "definition": {"kind": "reconciliation", "form": "8824",
                    "formula": "L32 = L30−L31; L34 = max(0,L30−L33); L37 = L32−(L35+L36); L38 = L33−L37"},
     "sort_order": 8},
    {"assertion_id": "FA-1040-8824-09", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Gates — multi-asset / §121-home / personal-property RED-defer",
     "description": "Unsupported paths fire a RED diagnostic and defer — never a silent wrong number.",
     "definition": {"kind": "gating_check", "form": "8824", "expect": {"red_fires": True},
                    "blockers": ["multi_asset_exchange", "section_121_home_use", "personal_property_not_like_kind"]},
     "sort_order": 9},
]


FORMS: list[dict] = [
    {"identity": P_IDENTITY, "facts": P_FACTS, "rules": P_RULES, "lines": P_LINES,
     "diagnostics": P_DIAGNOSTICS, "scenarios": P_SCENARIOS, "rule_links": P_RULE_LINKS},
]


class Command(BaseCommand):
    help = "Load the Form 8824 spec (Like-Kind Exchanges + §1043). Refuses until READY_TO_SEED=True."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad Form 8824 spec (Like-Kind Exchanges)\n"))
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
                "\nREFUSING TO SEED Form 8824: not cleared to seed.\n\n"
                "Gated until Ken's review walk (the §1.1031(d)-2 liability netting, the computed\n"
                "§1245(b)(4)/§1250(d)(4) recapture, the 4797 line-5/16 routing closure of D_4797_004,\n"
                "the Part II §1031(f) acceleration, the Part IV §1043 mechanics, and the RED-defer\n"
                "boundaries).\n\n"
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
        self.stdout.write(f"{'Created' if created else 'Updated'} Form {identity['form_number']}")
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
        form = TaxForm.objects.filter(form_number="8824").order_by("-version").first()
        if form:
            uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
            self.stdout.write("Form 8824: all rules cited" if not uncited
                              else self.style.WARNING(f"Form 8824 uncited rules: {len(uncited)}"))
