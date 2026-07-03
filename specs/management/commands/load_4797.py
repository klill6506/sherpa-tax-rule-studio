"""Load Form 4797 (Sales of Business Property) — Broad v1, modern-style loader.

REWRITTEN 2026-06-26 from the old "first form for validation" BaseCommand draft to the
modern loader pattern (load_1040_form_1116.py): a pure module-level ``compute_4797()``
the integrity gate re-types, a ``FORMS`` structure, and ``FLOW_ASSERTIONS``.

SHARED multi-entity form — form_number "4797", entity_types ['1120S','1065','1120','1040']
PRESERVED (amend by lookup, never clobber entity_types — the rs-amend-shared-form lesson).
The recapture MATH (Parts I-IV) is entity-agnostic; only the final destination lines differ
by entity. This rewrite encodes the 1040 routing (Ken's Broad-v1 build); the line
destination_forms note the other entities.

KEN'S BROAD-V1 SCOPE (chosen 2026-06-26, two AskUserQuestions): the full Form 4797, Parts
I-IV, for the 1040. Three tax-law judgment calls Ken approved in-session:
  1. §1231 5-yr lookback (line 8) = a preparer-asserted fact (default 0) + a diagnostic to
     check the prior 5 years; min(L7,L8) → Part II L12 ordinary, L9 = max(0,L7−L8) → Sch D.
  2. §1250 additional depreciation (line 26a) = preparer-entered (default 0 = the post-1986
     straight-line common case → §1250 ordinary 0, all depreciation-gain becomes unrecaptured
     §1250 @25%); a non-zero 26a computes the §1250 ordinary recapture (pre-1987/ACRS).
  3. Part IV §179/§280F recapture (line 35) → Schedule 1 line 4 (other income) + an INFO
     diagnostic re the i4797 SE-tax-on-§179-recapture note (the auto SE add-back RED-defers).

LAW VERIFIED 2026-06-26 against the actual 2025 Form 4797 PDF (resources/irs_forms/2025/
f4797.pdf, 182 AcroForm fields) + the 2025 Instructions for Form 4797 + IRC §1231/§1245/§1250/
§1252/§1254/§1255 + §1(h)(1)(E) + §179(d)(recapture) + §280F(b)(2). Part III structure read
directly off the PDF (the field-map COMMENTS were wrong): 25a/25b = §1245, 26a-g = §1250, 27 =
§1252, 28 = §1254, 29 = §1255; L31 → Part II L13, L32 (excess) → Part I L6 (casualty portion →
Form 4684 L33).

ROUTING (4797 → 1040):
  Part I L7 = net §1231 (combine 2-6). If loss → Part II L11 (ordinary), skip 8-9. If gain →
    L8 lookback; L12 = min(L7,L8) ordinary; L9 = max(0,L7−L8) → Schedule D line 11 (LTCG).
  Part II L17 = combine 10-16; L18a = income-producing-property loss → Schedule A L16 (v1=0,
    RED-defer 4684); L18b = L17 − L18a → Schedule 1 line 4.
  Part III recapture (L25b/26g/27c/28b/29b) → L31 → Part II L13; L32 excess → Part I L6.
  Unrecaptured §1250 gain is NOT on Form 4797 — compute_4797 EXPORTS it for the Schedule D
    "Unrecaptured Section 1250 Gain Worksheet" → the Schedule D Tax Worksheet (25% rate).
  Part IV L35 = §179/§280F recapture → Schedule 1 line 4 (Ken's call) + SE-nuance diagnostic.

Form 6252 installment sales are now SUPPORTED — compute_6252 feeds the §1231 gain to line 4,
  the ordinary gain to line 10, and the ordinary recapture to line 15 (closed 2026-06-28).
v1 RED-defers (each a no-silent-gap diagnostic): Form 4684 casualty/theft interplay (L3/L14/
  L18a/L33), Form 8824 like-kind (L5/L16). The §1252/§1255
  applicable percentages are preparer-entered (the IRS schedule documented), not encoded —
  consistent with the §1250-26a decision (no guessing on indexed/scheduled figures).

SAFETY GUARD: READY_TO_SEED stays False until Ken's review walk (the recapture arithmetic, the
1040 routing, the lookback mechanic, the unrecaptured-§1250 export, the §1252/1255 schedules).

═══ CLASSIFICATION LEG (2026-07-02, Ken Decisions C1-C3) ═══
Closes the CONFIRMED tts bug: resolve_recapture_type() classifies Improvements by RECOVERY
PERIOD (life <27.5 → §1245), so 15-yr QIP / land improvements sold at a gain take full §1245
ordinary recapture instead of §1250 treatment — and test_improvements_15yr_is_1245 pins it.
LAW VERIFIED 2026-07-02 verbatim (Cornell LII + the live 2025 i4797 PDF, pymupdf p.9-10):
  - §1250(c): §1250 property = "any real property (other than section 1245 property...)" —
    PROPERTY CHARACTER, not recovery period, is the classifier.
  - §1250(b)(1) + i4797 line 26a VERBATIM: additional depreciation = excess of actual
    "(including any special depreciation allowance)" over straight line — so BONUS on QIP IS
    additional depreciation → §1250 ordinary recapture to that extent (question resolved).
  - i4797 carve-out: only 27.5-yr residential + 22/31.5/39-yr nonresidential MACRS skip the
    line-26 computation — 15-yr property is NOT carved out (150DB land improvements + bonused
    QIP need it).
  - §1245(a)(3): the real-property exceptions — (C) §179-adjusted, (D) single-purpose
    agricultural/horticultural, (G) qualified production property (§168(n)(2), OBBBA 7/4/2025).
KEN'S DECISIONS (2026-07-02): C1 classifier = character-based defaults by asset group
(Buildings/Improvements → 1250, equipment → 1245) + per-asset override + D_4797_CLASS on
Improvements dispositions listing the §1245 exceptions. C2 line 26a stays preparer-entered
with a HARD ERROR (D_4797_ADDL) when a disposed §1250 asset used an accelerated method or
claimed bonus and 26a is blank; the i4797 carve-out classes stay auto-zero. C3 v1 edges =
diagnostics only (D_4797_179REAL warning, D_4797_QPP info) — no §1245/§1250 split engine.

═══ NUANCE LEG (2026-07-03, Ken Decisions 1-2 via AskUserQuestion) ═══
Closes the three depreciation nuances flagged when the classification leg was built.
LAW VERIFIED 2026-07-03 verbatim (Cornell LII + the 2025 i4797 instructions):
  - §1245(a)(3)(D)/(E)/(F): the real-property exceptions cross-reference §168 — (D) single-
    purpose ag/hort structure (§168(i)(13): a livestock enclosure or a commercial greenhouse),
    (E) petroleum-distribution storage facility, (F) railroad grading/tunnel bore (§168(e)(4)).
  - §1250(b)(1)+(b)(3): additional depreciation = actual adjustments over straight line; the
    (b)(3) carve-out excludes only the PRE-1976 §168, so current MACRS + §168(k) bonus ARE
    depreciation adjustments (nuance 3 now statutorily grounded, not just i4797).
  - §168(b)(2)(A): 15-yr land improvements use 150DB → actual > SL → §1250 additional depreciation.
  - i4797 line 26a verbatim: SL comparison uses the UNREDUCED basis ("do not reduce the basis...").
KEN'S DECISIONS (2026-07-03):
  Decision 1 (nuance 1) = a NEW per-asset classifier field f4797_section_1245_exception
    (none / single_purpose_ag / petroleum_storage / railroad_grading) auto-returns §1245 for the
    (D)/(E)/(F) real-property exceptions + a per-exception info diagnostic (D_4797_1245AG/PETRO/RRGR).
    (C) §179-realty stays via D_4797_179REAL; (G) QPP via is_qpp/D_4797_QPP.
  Decision 2 (nuances 2+3) = COMPUTE line 26a = max(0, actual accumulated depr incl. bonus − SL
    on the unreduced basis) in the tts engine where the disposed §1250 asset has the MACRS data
    (method/life/convention/dates) — one computation covering BOTH 150DB land improvements and
    bonused QIP; preparer-overridable. D_4797_ADDL becomes the FALLBACK gate (fires only when the
    engine cannot compute: pre-1987/ACRS, imported). Applicable % = 100%.
The RS spec encodes the rules/diagnostics/scenarios + authority; the SL-equivalent computation
itself is the tts build leg (engine + resolve_recapture_type + a section_1245_exception model
field + the D_4797_1245* diagnostics), verified there + in a DB stamp.
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


# Broad-v1 seeded 2026-06-27 ("Approve — seed it"). Classification leg FLIPPED 2026-07-02 —
# Ken approved the review walk ("approve and seed").
READY_TO_SEED = True


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
# v2 = the row the export serves (lookup returns order_by('-version').first()). The RS DB had
# TWO identical old-draft rows (v1 + v2); update v2 IN PLACE to the Broad-v1 content so the
# export reflects it. The stale v1 draft is harmless legacy (never served).
FORM_VERSION = 2
FORM_ENTITY_TYPES = ["1120S", "1065", "1120", "1040"]  # SHARED — preserved (do not clobber).
FORM_STATUS = "draft"


from decimal import ROUND_HALF_UP, Decimal  # noqa: E402


def _D(x):
    return Decimal(str(x if x is not None else 0))


def _r0(x):
    return int(_D(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


# ═══════════════════════════════════════════════════════════════════════════
# PURE COMPUTE (mirrors the tts compute leg; check_4797_integrity.py re-types it)
# ═══════════════════════════════════════════════════════════════════════════

# Recapture-bearing depreciable §1231 property types routed through Part III:
_PART3_TYPES = {"1245", "1250", "1252", "1254", "1255"}


def compute_property(*, sales_price=0, cost_basis=0, expense_of_sale=0, depreciation_allowed=0,
                     holding_period_months=0, property_type="1231",
                     additional_depreciation=0, applicable_pct_1250=1,
                     section_1252_deductions=0, section_1252_pct=0,
                     section_1254_costs=0,
                     section_1255_excluded=0, section_1255_pct=0,
                     used_accel_bonus=False, asset_group="",
                     section_1245_exception="none") -> dict:
    # used_accel_bonus / asset_group (classification leg 2026-07-02) and
    # section_1245_exception (nuance leg 2026-07-03) are diagnostic drivers
    # (D_4797_ADDL / D_4797_CLASS / D_4797_1245AG|PETRO|RRGR), not math inputs.
    # The classifier (tts resolve_recapture_type) maps a set section_1245_exception
    # to property_type "1245" UPSTREAM — the scenarios pass the resolved
    # property_type, and the math reads the preparer's line-26a additional_
    # depreciation (computed in tts where MACRS data is present) as before.
    """One disposed property. Returns its routing buckets:
      ordinary_recapture — Part III ordinary (→ Part II line 13), or short-term ordinary
      section_1231       — the §1231 gain/loss going to Part I (line 2 direct or line 6 via L32)
      unrecaptured_1250  — the 25% bucket WITHIN the §1231 capital gain (→ Sch D worksheet)
      bucket             — 'short_term' | 'part1' (non-recapture §1231) | 'part3' (recapture)
    L20 amount realized, L21 = cost+expense, L23 = L21−L22(depr), L24 = L20−L23 (total gain)."""
    l20 = _D(sales_price)
    l21 = _D(cost_basis) + _D(expense_of_sale)
    l22 = _D(depreciation_allowed)
    l23 = l21 - l22                                   # adjusted basis
    l24 = l20 - l23                                   # total gain (may be negative = loss)
    months = int(holding_period_months or 0)

    # Short-term (held ≤ 12 months): all ordinary → Part II line 10. No §1231/recapture.
    if months <= 12:
        return {"bucket": "short_term", "l24": l24, "ordinary_recapture": Decimal("0"),
                "section_1231": Decimal("0"), "unrecaptured_1250": Decimal("0"),
                "short_term_ordinary": l24}

    # Long-term loss, or non-depreciable §1231 gain → Part I (no recapture).
    if l24 <= 0 or property_type not in _PART3_TYPES:
        return {"bucket": "part1", "l24": l24, "ordinary_recapture": Decimal("0"),
                "section_1231": l24, "unrecaptured_1250": Decimal("0"),
                "short_term_ordinary": Decimal("0")}

    # Long-term gain on recapture property → Part III.
    ordinary = Decimal("0")
    unrecap_1250 = Decimal("0")
    if property_type == "1245":
        # L25b = smaller of line 24 or line 25a (all depreciation allowed/allowable).
        ordinary = min(l24, l22)
    elif property_type == "1250":
        # L26a additional depreciation after 1975 (preparer; 0 for post-1986 SL).
        # L26b = applicable% × smaller(L24, L26a); L26g (v1) = L26b. §291/pre-1976 = 0 for 1040.
        addl = _D(additional_depreciation)
        ordinary = _D(applicable_pct_1250) * min(l24, addl)
        # Unrecaptured §1250 = the depreciation-driven gain NOT recaptured as ordinary, max 25%.
        unrecap_1250 = max(Decimal("0"), min(l24, l22) - ordinary)
    elif property_type == "1252":
        # L27c = smaller of L24 or (L27a soil/water deductions × L27b applicable %).
        ordinary = min(l24, _D(section_1252_deductions) * _D(section_1252_pct))
    elif property_type == "1254":
        # L28b = smaller of L24 or L28a (IDC / depletion deducted).
        ordinary = min(l24, _D(section_1254_costs))
    elif property_type == "1255":
        # L29b = smaller of L24 or (L29a §126 excluded × applicable %).
        ordinary = min(l24, _D(section_1255_excluded) * _D(section_1255_pct))

    ordinary = max(Decimal("0"), ordinary)
    section_1231 = l24 - ordinary                     # L32 excess → Part I line 6
    return {"bucket": "part3", "l24": l24, "ordinary_recapture": ordinary,
            "section_1231": section_1231, "unrecaptured_1250": unrecap_1250,
            "short_term_ordinary": Decimal("0")}


def compute_4797(*, properties=None, nonrecaptured_1231_losses=0, part1_line2_direct=0,
                 part4_section_179_recapture=0, part4_section_280f_recapture=0,
                 # Form 6252 installment-sale feeds (close the 4797 RED-defer): line 4
                 # (§1231 gain → Part I netting), line 10 (ordinary "From Form 6252"),
                 # line 15 (ordinary recapture). compute_6252 is the single source.
                 installment_line4=0, installment_line10=0, installment_line15=0,
                 # Form 8824 like-kind feeds (close the D_4797_004 RED-defer): line 5
                 # (recognized §1231 gain → Part I netting), line 16 (ordinary recapture +
                 # ordinary gain), line 10 (§1043 ordinary). compute_8824 is the single source.
                 like_kind_line5=0, like_kind_line16=0, like_kind_line10=0,
                 # red-defer interplay flag (Form 4684 casualty still deferred)
                 has_form_4684=False,
                 **_ignored) -> dict:
    """Aggregate Form 4797 over its properties + return-level facts → the 1040 routing.

    Returns the key lines + the 1040 destinations:
      sch1_line4       — Part II L18b + Part IV recapture (ordinary other income)
      sch_d_line11     — Part I L9 (net §1231 LTCG after the 5-yr lookback)
      unrecaptured_1250 — Σ unrecaptured §1250 (→ Sch D Unrecaptured §1250 Gain Worksheet, 25%)
      sch_a_line16     — Part II L18a (income-producing-property loss; v1 = 0, RED-defer 4684)
    Or {'red_defer': [...]} when an unsupported interplay (4684 casualty) is present. Form
    6252 (installment, lines 4/10/15) and Form 8824 (like-kind, lines 5/16/10) are now
    SUPPORTED via their feeds (closed 2026-06-28)."""
    properties = properties or []

    reasons = []
    if has_form_4684:
        reasons.append("form_4684_casualty")
    if reasons:
        return {"red_defer": reasons, "sch1_line4": None, "sch_d_line11": None,
                "unrecaptured_1250": None}

    results = [compute_property(**p) for p in properties]

    short_term_ordinary = sum((r["short_term_ordinary"] for r in results), Decimal("0"))
    part3_line31 = sum((r["ordinary_recapture"] for r in results), Decimal("0"))  # → Part II L13
    part3_line32 = sum((r["section_1231"] for r in results if r["bucket"] == "part3"),
                       Decimal("0"))                                              # → Part I L6
    part1_line2 = sum((r["section_1231"] for r in results if r["bucket"] == "part1"),
                      Decimal("0")) + _D(part1_line2_direct)
    unrecaptured_1250 = sum((r["unrecaptured_1250"] for r in results), Decimal("0"))

    # ── Part I ──
    l4 = _D(installment_line4)                       # Form 6252 §1231 installment gain → line 4
    l5 = _D(like_kind_line5)                          # Form 8824 recognized §1231 like-kind gain → line 5
    l6 = part3_line32
    l7 = part1_line2 + l4 + l5 + l6                   # L3 (4684) = 0 in v1

    # ── §1231 5-year lookback (Part I L8 / Part II L9-L12) ──
    if l7 <= 0:                                      # net §1231 loss → ordinary (Part II L11)
        l8 = Decimal("0")
        l9 = Decimal("0")
        l11 = l7                                     # the loss (negative)
        l12 = Decimal("0")
    else:
        l8 = _D(nonrecaptured_1231_losses)
        recaptured = min(l7, l8)                     # → Part II line 12 (ordinary)
        l9 = max(Decimal("0"), l7 - l8)             # → Schedule D line 11 (LTCG)
        l11 = Decimal("0")
        l12 = recaptured

    # ── Part II ──
    l10 = (short_term_ordinary + _D(installment_line10)   # + Form 6252 ordinary/≤1yr → line 10
           + _D(like_kind_line10))                        # + Form 8824 §1043 ordinary → line 10
    l13 = part3_line31
    l15 = _D(installment_line15)                          # Form 6252 ordinary recapture → line 15
    l16 = _D(like_kind_line16)                            # Form 8824 ordinary recapture/gain → line 16
    l17 = l10 + l11 + l12 + l13 + l15 + l16               # L14 (4684) = 0 in v1
    l18a = Decimal("0")                              # income-producing-property loss (RED-defer)
    l18b = l17 - l18a                                # → Schedule 1 line 4

    # ── Part IV — §179 / §280F recapture ──
    part4 = max(Decimal("0"), _D(part4_section_179_recapture)) + \
        max(Decimal("0"), _D(part4_section_280f_recapture))

    sch1_line4 = l18b + part4                        # both ordinary "other income"
    return {"l4": l4, "l5": l5, "l6": l6, "l7": l7, "l8": l8, "l9": l9, "l10": l10, "l11": l11,
            "l12": l12, "l13": l13, "l15": l15, "l16": l16, "l17": l17, "l18a": l18a, "l18b": l18b,
            "l31": part3_line31, "l32": part3_line32, "part4_recapture": part4,
            "sch1_line4": sch1_line4, "sch_d_line11": l9,
            "unrecaptured_1250": unrecaptured_1250, "sch_a_line16": l18a}


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("4797", "Form 4797 — Sales of Business Property"),
    ("section_1231", "§1231 property — netting + the 5-year nonrecaptured-loss lookback"),
    ("depreciation_recapture", "Depreciation recapture (§1245/1250/1252/1254/1255) + §179/§280F"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    "IRS_2025_1040_FORM",
    "IRS_2025_1040_INSTR",
]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRC_1231",
        "source_type": "statute", "source_rank": "primary_official", "jurisdiction_code": "FED",
        "title": "IRC §1231 — Property Used in the Trade or Business",
        "citation": "26 U.S.C. §1231", "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:1231%20edition:prelim)",
        "current_status": "active", "is_substantive_authority": True, "is_filing_authority": False,
        "trust_score": 10.0, "requires_human_review": True,
        "notes": "Statutory text not fetched verbatim — excerpts paraphrased from Pub 544 / i4797. Ken to verify §1231(c) lookback language.",
        "topics": ["section_1231"],
        "excerpts": [
            {"excerpt_label": "§1231(a) netting; §1231(c) 5-year lookback",
             "location_reference": "§1231(a),(c)",
             "excerpt_text": (
                 "Net gain from section 1231 transactions (property used in a trade or business and held "
                 "more than 1 year) is treated as long-term capital gain; a net loss is ordinary. Under "
                 "§1231(c), net section 1231 gain is treated as ordinary income to the extent of the "
                 "'nonrecaptured net section 1231 losses' — net §1231 losses deducted in the 5 most recent "
                 "preceding tax years that have not yet been recaptured."),
             "summary_text": "Net §1231 gain = LTCG; net §1231 loss = ordinary; 5-yr lookback recaptures prior losses as ordinary.",
             "is_key_excerpt": True},
        ],
    },
    {
        "source_code": "IRC_1245",
        "source_type": "statute", "source_rank": "primary_official", "jurisdiction_code": "FED",
        "title": "IRC §1245 — Gain from Dispositions of Certain Depreciable Property",
        "citation": "26 U.S.C. §1245", "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:1245%20edition:prelim)",
        "current_status": "active", "is_substantive_authority": True, "is_filing_authority": False,
        "trust_score": 10.0, "requires_human_review": True,
        "notes": "§1245 recaptures ALL depreciation as ordinary (no SL/accelerated distinction). "
                 "CLASSIFICATION LEG (2026-07-02): (a)(3) quoted — §1245 property is personal property "
                 "PLUS specific real-property exceptions ((C) §179-adjusted, (D) single-purpose ag, "
                 "(G) OBBBA qualified production property). Recovery period is NOT a classifier.",
        "topics": ["depreciation_recapture"],
        "excerpts": [
            {"excerpt_label": "§1245(a)(1) — recapture of all depreciation",
             "location_reference": "§1245(a)(1)",
             "excerpt_text": (
                 "On the disposition of section 1245 property (generally tangible depreciable personal "
                 "property), gain is treated as ordinary income to the extent of the lower of the total "
                 "depreciation (and §179/amortization) allowed or allowable, or the gain realized. ALL "
                 "depreciation is recaptured — there is no excess-over-straight-line limit."),
             "summary_text": "§1245 ordinary recapture = smaller of total depreciation or gain (line 25b).",
             "is_key_excerpt": True},
            {"excerpt_label": "§1245(a)(3) — what IS §1245 property (the classification)",
             "location_reference": "26 U.S.C. §1245(a)(3) (verbatim chapeau + (A)/(D)/(G); verified 2026-07-02)",
             "excerpt_text": (
                 "For purposes of this section, the term 'section 1245 property' means any property which "
                 "is or has been property of a character subject to the allowance for depreciation provided "
                 "in section 167 and is either— (A) personal property, ... (C) real property adjusted for "
                 "amortization/expensing under enumerated sections including the section 179 expense "
                 "deduction, (D) a single purpose agricultural or horticultural structure (per section "
                 "168(i)(13)), (E) a petroleum-distribution storage facility (other than a building or its "
                 "structural components), (F) railroad grading or tunnel bore, or (G) any qualified "
                 "production property (as defined in section 168(n)(2))."),
             "summary_text": "§1245 = personal property + enumerated real-property exceptions: §179-adjusted "
                             "(C), single-purpose ag structures (D), petroleum storage (E), RR grading (F), "
                             "and OBBBA qualified production property (G, post-7/4/2025). NOT a "
                             "recovery-period test.",
             "is_key_excerpt": True},
        ],
    },
    {
        "source_code": "IRC_1250",
        "source_type": "statute", "source_rank": "primary_official", "jurisdiction_code": "FED",
        "title": "IRC §1250 — Gain from Dispositions of Certain Depreciable Realty",
        "citation": "26 U.S.C. §1250", "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:1250%20edition:prelim)",
        "current_status": "active", "is_substantive_authority": True, "is_filing_authority": False,
        "trust_score": 10.0, "requires_human_review": True,
        "notes": "§1250 recaptures only ADDITIONAL depreciation (excess over SL). CORRECTED 2026-07-02: "
                 "additional depreciation is 0 only for realty ACTUALLY depreciated straight-line "
                 "(27.5/39-yr MACRS) — NOT for 150DB land improvements or realty with a special "
                 "depreciation allowance (bonus), where additional depreciation is real. The prior "
                 "'post-1986 MACRS realty → 0' note overgeneralized (the tts bug's textual ancestor).",
        "topics": ["depreciation_recapture"],
        "excerpts": [
            {"excerpt_label": "§1250(a) — additional-depreciation recapture",
             "location_reference": "§1250(a)",
             "excerpt_text": (
                 "Section 1250 (depreciable real property) recaptures as ordinary income the 'additional "
                 "depreciation' — the excess of depreciation actually allowed over the amount that would "
                 "have been allowed under the straight line method — multiplied by the applicable "
                 "percentage. Zero only where the realty was actually depreciated straight-line with no "
                 "special depreciation allowance."),
             "summary_text": "§1250 ordinary = applicable% × additional depreciation (line 26a); zero only "
                             "for true-SL, no-bonus realty.",
             "is_key_excerpt": True},
            {"excerpt_label": "§1250(c) + (b)(1) — property definition + additional depreciation (verbatim)",
             "location_reference": "26 U.S.C. §1250(c), (b)(1) (verified 2026-07-02)",
             "excerpt_text": (
                 "(c) Section 1250 property: 'any real property (other than section 1245 property, as "
                 "defined in section 1245(a)(3)) which is or has been property of a character subject to "
                 "the allowance for depreciation provided in section 167.' (b)(1) Additional depreciation: "
                 "'the depreciation adjustments in respect of such property; except that, in the case of "
                 "property held more than one year, it means such adjustments only to the extent that they "
                 "exceed the amount of the depreciation adjustments which would have resulted if such "
                 "adjustments had been determined for each taxable year under the straight line method of "
                 "adjustment.'"),
             "summary_text": "§1250 property = depreciable REAL property not §1245 (character test, not "
                             "recovery period). Additional depreciation = actual adjustments over the "
                             "straight-line equivalent — bonus/150DB create it; true SL does not.",
             "is_key_excerpt": True},
        ],
    },
    {
        "source_code": "IRC_168",
        "source_type": "statute", "source_rank": "primary_official", "jurisdiction_code": "FED",
        "title": "IRC §168 — Accelerated Cost Recovery System (MACRS: the §1245(a)(3) cross-refs + 150DB)",
        "citation": "26 U.S.C. §168(i)(13), (e)(4), (b)(2)(A), (b)(3)(G)/(e)(6), (k)", "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:168%20edition:prelim)",
        "current_status": "active", "is_substantive_authority": True, "is_filing_authority": False,
        "trust_score": 10.0, "requires_human_review": True,
        "notes": "NUANCE LEG (2026-07-03): §1245(a)(3) cross-references §168 for the definitions of the "
                 "real-property exceptions ((D) single-purpose ag §168(i)(13), (F) railroad grading "
                 "§168(e)(4), (G) QPP §168(n)(2)) and for the MACRS methods that create §1250 additional "
                 "depreciation ((b)(2)(A) 150DB for 15/20-yr land improvements; (k) special allowance/bonus). "
                 "Verified verbatim 2026-07-03 (Cornell LII).",
        "topics": ["depreciation_recapture"],
        "excerpts": [
            {"excerpt_label": "§168(i)(13) — single purpose agricultural or horticultural structure",
             "location_reference": "26 U.S.C. §168(i)(13) (verified 2026-07-03)",
             "excerpt_text": (
                 "The term 'single purpose agricultural or horticultural structure' means (A) a single "
                 "purpose livestock structure, and (B) a single purpose horticultural structure. A single "
                 "purpose livestock structure is any enclosure or structure specifically designed, "
                 "constructed, and used for housing, raising, and feeding a particular type of livestock; a "
                 "single purpose horticultural structure is a greenhouse specifically designed, constructed, "
                 "and used for the commercial production of plants."),
             "summary_text": "Single-purpose ag/hort structure = a livestock enclosure or a commercial "
                             "greenhouse — §1245 property under §1245(a)(3)(D).",
             "is_key_excerpt": True},
            {"excerpt_label": "§168(e)(4) — railroad grading or tunnel bore",
             "location_reference": "26 U.S.C. §168(e)(4) (verified 2026-07-03)",
             "excerpt_text": (
                 "The term 'railroad grading or tunnel bore' means all improvements resulting from "
                 "excavations (including tunneling), construction of embankments, clearings, diversions of "
                 "roads and streams, sodding of slopes, and from similar work necessary to provide, "
                 "construct, reconstruct, alter, protect, improve, replace, or restore a roadbed or "
                 "right-of-way for railroad track."),
             "summary_text": "Railroad grading/tunnel bore (§168(e)(4)) — §1245 property under §1245(a)(3)(F).",
             "is_key_excerpt": True},
            {"excerpt_label": "§168(b)(2)(A) + (b)(3)/(e)(6) — 150DB for 15/20-yr; QIP is SL 15-yr",
             "location_reference": "26 U.S.C. §168(b)(2)(A), (b)(3)(G), (e)(6) (verified 2026-07-03)",
             "excerpt_text": (
                 "Paragraph (2) (the 150 percent declining balance method) applies to any 15-year or "
                 "20-year property not referred to in paragraph (3). Land improvements are 15-year property "
                 "→ 150DB, so their actual depreciation exceeds straight line and creates §1250 additional "
                 "depreciation. Qualified improvement property (§168(e)(6)) is depreciated under the "
                 "straight line method (§168(b)(3)(G)) over a 15-year recovery period, but is bonus-eligible "
                 "(§168(k)) — the bonus, not the method, creates its additional depreciation."),
             "summary_text": "15-yr land improvements = 150DB (> SL → additional depreciation exists); QIP = "
                             "SL 15-yr, additional depreciation only from bonus.",
             "is_key_excerpt": True},
            {"excerpt_label": "§168(k) special (bonus) allowance is a depreciation adjustment (§1250(b)(3))",
             "location_reference": "26 U.S.C. §168(k) (cf. §1250(b)(3), verified 2026-07-03)",
             "excerpt_text": (
                 "The §168(k) special depreciation allowance ('bonus depreciation') is an additional "
                 "first-year depreciation deduction. It is a depreciation adjustment reflected in adjusted "
                 "basis; §1250(b)(3) excludes from 'depreciation adjustments' only amortization under the "
                 "PRE-1976 section 168 (and §169/§185/§188/§190/§193), NOT the current §168(k). Bonus on "
                 "§1250 realty (e.g., QIP) is therefore additional depreciation to the extent it exceeds "
                 "straight line — confirming the i4797 line-26a 'including any special depreciation "
                 "allowance' instruction."),
             "summary_text": "§168(k) bonus IS a depreciation adjustment → §1250 additional depreciation "
                             "(the (b)(3) carve-out is pre-1976 §168 only).",
             "is_key_excerpt": True},
        ],
    },
    {
        "source_code": "IRC_1_H_1_E",
        "source_type": "statute", "source_rank": "primary_official", "jurisdiction_code": "FED",
        "title": "IRC §1(h)(1)(E) — Unrecaptured Section 1250 Gain (25% Rate)",
        "citation": "26 U.S.C. §1(h)(1)(E), §1(h)(6)", "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20section:1%20edition:prelim)",
        "current_status": "active", "is_substantive_authority": True, "is_filing_authority": False,
        "trust_score": 10.0, "requires_human_review": True,
        "notes": "Unrecaptured §1250 gain is computed on the Schedule D instructions worksheet, NOT on Form 4797; taxed at max 25%.",
        "topics": ["depreciation_recapture"],
        "excerpts": [
            {"excerpt_label": "Unrecaptured §1250 gain — max 25%",
             "location_reference": "§1(h)(1)(E), §1(h)(6)",
             "excerpt_text": (
                 "Unrecaptured section 1250 gain is the long-term capital gain (not otherwise ordinary "
                 "under §1250) attributable to depreciation on section 1250 property, taxed at a maximum "
                 "rate of 25%. It is identified on the Unrecaptured Section 1250 Gain Worksheet in the "
                 "Schedule D instructions and carried to the Schedule D Tax Worksheet — it is NOT a line "
                 "on Form 4797."),
             "summary_text": "Unrecaptured §1250 = min(gain, total depreciation) − §1250 ordinary; → Sch D worksheet, 25% rate.",
             "is_key_excerpt": True},
        ],
    },
    {
        "source_code": "IRC_1252_1254_1255",
        "source_type": "statute", "source_rank": "primary_official", "jurisdiction_code": "FED",
        "title": "IRC §1252 / §1254 / §1255 — Farmland, Oil-and-Gas, and §126-Cost-Sharing Recapture",
        "citation": "26 U.S.C. §1252, §1254, §1255", "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20edition:prelim)",
        "current_status": "active", "is_substantive_authority": True, "is_filing_authority": False,
        "trust_score": 10.0, "requires_human_review": True,
        "notes": "Specialty recapture. §1252 farmland soil/water (applic% by years held); §1254 IDC/depletion; §1255 §126 cost-sharing (applic% by years). v1 takes the applicable percentages as preparer input (the IRS schedule documented) rather than encoding the year tables.",
        "topics": ["depreciation_recapture"],
        "excerpts": [
            {"excerpt_label": "§1252 / §1254 / §1255 recapture — smaller-of pattern",
             "location_reference": "§1252(a), §1254(a), §1255(a)",
             "excerpt_text": (
                 "§1252 recaptures, as ordinary income, soil/water conservation and land-clearing "
                 "expenses on farmland held under 10 years, multiplied by an applicable percentage that "
                 "phases from 100% (years 1-5) down to 0% (10+ years). §1254 recaptures intangible "
                 "drilling costs and depletion previously deducted. §1255 recaptures §126 cost-sharing "
                 "payments excluded from income, by an applicable percentage based on years held. Each is "
                 "the smaller of the line-24 gain or the section's recapture amount."),
             "summary_text": "§1252/1254/1255 = smaller of gain or the section's recapture (with §1252/§1255 applicable percentages by years held).",
             "is_key_excerpt": True},
        ],
    },
    {
        "source_code": "IRC_179D_280F",
        "source_type": "statute", "source_rank": "primary_official", "jurisdiction_code": "FED",
        "title": "IRC §179(d)(10) and §280F(b)(2) — §179 / Listed-Property Recapture",
        "citation": "26 U.S.C. §179(d)(10), §280F(b)(2)", "issuer": "U.S. Congress",
        "official_url": "https://uscode.house.gov/view.xhtml?req=(title:26%20edition:prelim)",
        "current_status": "active", "is_substantive_authority": True, "is_filing_authority": False,
        "trust_score": 10.0, "requires_human_review": True,
        "notes": "Part IV recapture when business use of §179 / listed property drops to ≤50% before the end of the recovery period.",
        "topics": ["depreciation_recapture"],
        "excerpts": [
            {"excerpt_label": "§179(d)(10) / §280F(b)(2) — business-use-drop recapture",
             "location_reference": "§179(d)(10), §280F(b)(2)",
             "excerpt_text": (
                 "If business use of section 179 property (or §280F listed property) drops to 50% or less "
                 "before the end of the property's recovery period, the excess of the depreciation/§179 "
                 "deduction claimed over the depreciation that would have been allowable (without §179, "
                 "and using the §280F straight-line method) is recaptured as ordinary income (Form 4797 "
                 "Part IV, line 35) in that year."),
             "summary_text": "Part IV L35 = §179/§280F deduction claimed − depreciation that would have been allowable; ordinary income.",
             "is_key_excerpt": True},
        ],
    },
    {
        "source_code": "IRS_2025_4797_INSTR",
        "source_type": "official_instructions", "source_rank": "primary_official", "jurisdiction_code": "FED",
        "entity_type_code": "shared", "tax_year_start": 2025, "tax_year_end": 2025,
        "title": "Instructions for Form 4797 (2025) — Sales of Business Property",
        "citation": "Instructions for Form 4797 (2025)", "issuer": "IRS",
        "official_url": "https://www.irs.gov/instructions/i4797",
        "current_status": "active", "is_substantive_authority": False, "is_filing_authority": True,
        "trust_score": 9.5, "requires_human_review": False,
        "notes": "The Part I-IV routing + the 1040 destinations (Sch D line 11, Sch 1 line 4, Sch A line 16). Verified vs the actual 2025 f4797.pdf.",
        "topics": ["4797", "section_1231", "depreciation_recapture"],
        "excerpts": [
            {"excerpt_label": "Part I lines 7-9 — net §1231 + the 5-year lookback → Schedule D",
             "location_reference": "i4797 (2025), Part I + Part II lines 7-12",
             "excerpt_text": (
                 "Line 7 combines lines 2 through 6 (net section 1231 gain or loss). If line 7 is a gain, "
                 "enter on line 8 your nonrecaptured net section 1231 losses from the prior 5 years. Line "
                 "9 = line 7 minus line 8. If line 9 is zero, enter the line 7 gain on line 12 (ordinary). "
                 "If line 9 is more than zero, enter the line 8 amount on line 12 (ordinary recapture) and "
                 "enter the line 9 gain as a long-term capital gain on the Schedule D for your return. If "
                 "line 7 is a loss, it is ordinary (carried into Part II)."),
             "summary_text": "L12 ordinary = min(L7, L8); L9 = max(0, L7−L8) → Schedule D as LTCG; L7 loss → ordinary.",
             "is_key_excerpt": True},
            {"excerpt_label": "Part II line 18 — individuals' split → Sch 1 L4 / Sch A L16",
             "location_reference": "i4797 (2025), Part II line 18a/18b",
             "excerpt_text": (
                 "For individual returns: on line 18a enter the loss, if any, from income-producing "
                 "property on Schedule A (Form 1040), line 16 (identified as 'Form 4797, line 18a'). Line "
                 "18b = line 17 minus line 18a; enter it on Schedule 1 (Form 1040), line 4."),
             "summary_text": "Individuals: L18a (income-producing-property loss) → Schedule A L16; L18b = L17−L18a → Schedule 1 line 4.",
             "is_key_excerpt": True},
            {"excerpt_label": "Part III — recapture → Part II L13; excess → Part I L6",
             "location_reference": "i4797 (2025), Part III lines 19-32",
             "excerpt_text": (
                 "Part III computes recapture per property (4 columns). Line 24 = total gain (line 20 − "
                 "line 23). §1245: line 25b = smaller of line 24 or line 25a (all depreciation). §1250: "
                 "line 26g = ordinary from additional depreciation (line 26a); usually 0 for straight "
                 "line. §1252/§1254/§1255: lines 27c/28b/29b. Line 31 = total ordinary recapture → Part "
                 "II line 13. Line 32 = line 30 − line 31 (excess) → the casualty/theft portion to Form "
                 "4684 line 33 and the remainder to Part I line 6."),
             "summary_text": "Part III recapture L31 → Part II L13; excess L32 → Part I L6 (casualty portion → 4684).",
             "is_key_excerpt": True},
            {"excerpt_label": "Part IV — §179/§280F recapture; SE-tax note",
             "location_reference": "i4797 (2025), Part IV lines 33-35",
             "excerpt_text": (
                 "Part IV figures the recapture when business use of §179 or listed (§280F) property drops "
                 "to 50% or less: line 35 = line 33 (deduction claimed) minus line 34 (depreciation that "
                 "would have been allowable). Report the recapture as other income on the same form/"
                 "schedule on which the deduction was taken. If the property was used in a trade or "
                 "business reported on Schedule C or F, the recapture is subject to self-employment tax."),
             "summary_text": "Part IV L35 = deduction claimed − allowable depreciation → other income (SE tax if Sch C/F).",
             "is_key_excerpt": True},
            {"excerpt_label": "§1250 property + the line-26 carve-out classes (verbatim)",
             "location_reference": "i4797 (2025) p.9, 'Section 1250 property' (verified 2026-07-02, pymupdf)",
             "excerpt_text": (
                 "Section 1250 property is depreciable real property (other than section 1245 property). "
                 "Generally, section 1250 recapture applies if you used an accelerated depreciation method "
                 "or you claimed any special depreciation allowance, or the commercial revitalization "
                 "deduction. Section 1250 recapture does not apply to dispositions of the following MACRS "
                 "property placed in service after 1986 (or after July 31, 1986, if elected). You are not "
                 "required to calculate additional depreciation for these properties on line 26. • "
                 "27.5-year (30- or 40-year, if elected or required) residential rental property... • 22-, "
                 "31.5-, or 39-year (or 40-year, if elected or required) nonresidential real property..."),
             "summary_text": "The line-26 skip list is ONLY 27.5-yr residential + 22/31.5/39-yr "
                             "nonresidential MACRS — 15-yr property (land improvements, QIP) is NOT carved "
                             "out; accelerated method OR any special depreciation allowance triggers "
                             "§1250 recapture.",
             "is_key_excerpt": True},
            {"excerpt_label": "Line 26a — additional depreciation INCLUDES bonus (verbatim)",
             "location_reference": "i4797 (2025) p.10, Line 26a (verified 2026-07-02, pymupdf)",
             "excerpt_text": (
                 "Enter the additional depreciation for the period after 1975. Additional depreciation is "
                 "the excess of actual depreciation (including any special depreciation allowance, or "
                 "commercial revitalization deduction) over depreciation figured using the straight line "
                 "method. For this purpose, do not reduce the basis under section 50(c)(1) (or the "
                 "corresponding provision of prior law) to figure straight line depreciation."),
             "summary_text": "THE bonus-on-QIP answer: 'including any special depreciation allowance' — "
                             "§168(k) bonus on §1250 property IS additional depreciation; the straight-line "
                             "comparison uses the UNREDUCED basis (so the whole bonus excess over SL is "
                             "additional depreciation) → ordinary recapture to the extent of gain (line 26g).",
             "is_key_excerpt": True},
        ],
    },
    {
        "source_code": "IRS_PUB_544",
        "source_type": "official_publication", "source_rank": "primary_official", "jurisdiction_code": "FED",
        "tax_year_start": 2025, "tax_year_end": 2025,
        "title": "IRS Publication 544 — Sales and Other Dispositions of Assets",
        "citation": "Publication 544 (2025)", "issuer": "IRS",
        "official_url": "https://www.irs.gov/publications/p544",
        "current_status": "active", "is_substantive_authority": False, "is_filing_authority": False,
        "trust_score": 9.0, "requires_human_review": False,
        "notes": "Background on ordinary-vs-capital, holding period, and the recapture sections.",
        "topics": ["4797", "section_1231", "depreciation_recapture"],
        "excerpts": [
            {"excerpt_label": "Ordinary vs capital; holding period",
             "location_reference": "Pub 544 — Ordinary or Capital Gain and Loss",
             "excerpt_text": (
                 "Whether a gain or loss on business property is ordinary or capital depends on the "
                 "property type and the holding period (more than 1 year for §1231). §1245 recaptures all "
                 "depreciation as ordinary; §1250 recaptures only excess over straight line; the §1231 "
                 "netting rule then determines whether the remaining gain is capital or ordinary."),
             "summary_text": "Property type + >1-year holding drive §1231/recapture treatment.",
             "is_key_excerpt": True},
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRC_1231", "4797", "governs"),
    ("IRC_1245", "4797", "governs"),
    ("IRC_1250", "4797", "governs"),
    ("IRC_168", "4797", "informs"),
    ("IRC_1_H_1_E", "4797", "governs"),
    ("IRC_1252_1254_1255", "4797", "governs"),
    ("IRC_179D_280F", "4797", "governs"),
    ("IRS_2025_4797_INSTR", "4797", "governs"),
    ("IRS_PUB_544", "4797", "informs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM: 4797
# ═══════════════════════════════════════════════════════════════════════════

P_IDENTITY = {
    "form_number": "4797",
    "form_title": "Sales of Business Property",
    "notes": (
        "SHARED multi-entity form (1120S/1065/1120/1040). Broad-v1 1040 build (Ken 2026-06-26): "
        "the full Form 4797, Parts I-IV. Part I §1231 netting (L7) + the §1231(c) 5-year lookback "
        "(L8 preparer-asserted): L12 ordinary = min(L7,L8), L9 = max(0,L7−L8) → Schedule D line 11. "
        "Part II ordinary (L10 short-term + L13 recapture) → L18b → Schedule 1 line 4 (L18a income-"
        "producing-property loss → Schedule A line 16, v1=0). Part III recapture §1245 (L25), §1250 "
        "(L26, additional depreciation L26a preparer-entered, default 0), §1252 (L27), §1254 (L28), "
        "§1255 (L29) → L31 → Part II L13; excess L32 → Part I L6. Unrecaptured §1250 gain is NOT on "
        "4797 — exported to the Schedule D Unrecaptured §1250 Gain Worksheet (25%). Part IV §179/"
        "§280F recapture L35 → Schedule 1 line 4 (+ SE-tax note). Form 6252 installment sales feed "
        "lines 4/10/15 (supported). RED-defers (no silent gap): Form "
        "4684 casualty, Form 8824 like-kind. §1252/§1255 applicable "
        "percentages preparer-entered (not encoded)."
    ),
}

P_FACTS: list[dict] = [
    # ── per-property inputs (Part III lines 19-24 + the recapture sub-inputs) ──
    {"fact_key": "f4797_sales_price", "label": "Gross sales price / amount realized (line 20)",
     "data_type": "decimal", "default_value": "0", "sort_order": 1},
    {"fact_key": "f4797_cost_basis", "label": "Cost or other basis (line 21, before expense of sale)",
     "data_type": "decimal", "default_value": "0", "sort_order": 2},
    {"fact_key": "f4797_expense_of_sale", "label": "Expense of sale (added to line 21)",
     "data_type": "decimal", "default_value": "0", "sort_order": 3},
    {"fact_key": "f4797_depreciation_allowed", "label": "Depreciation/§179/amortization allowed or allowable (line 22)",
     "data_type": "decimal", "default_value": "0", "sort_order": 4},
    {"fact_key": "f4797_holding_period_months", "label": "Holding period (months) — >12 = long-term",
     "data_type": "integer", "default_value": "0", "sort_order": 5},
    {"fact_key": "f4797_property_type", "label": "Recapture type: 1245/1250/1252/1254/1255/1231/ordinary",
     "data_type": "string", "default_value": "1231", "sort_order": 6,
     "notes": "1231 = non-depreciable §1231 (no recapture); ordinary = dealer/short-term."},
    {"fact_key": "f4797_section_1245_exception",
     "label": "§1245(a)(3) real-property exception: none / single_purpose_ag (D) / petroleum_storage (E) / railroad_grading (F)",
     "data_type": "string", "default_value": "none", "sort_order": 6,
     "notes": "NUANCE LEG (2026-07-03, Decision 1): a per-asset classifier for the real property that IS "
              "§1245. When set, tts resolve_recapture_type returns §1245 for this depreciable REAL property "
              "(character override of the Buildings/Improvements → §1250 default) and fires the matching "
              "info diagnostic (D_4797_1245AG / D_4797_1245PETRO / D_4797_1245RRGR). The other two §1245(a)(3) "
              "real-property exceptions are already surfaced: (C) §179-adjusted realty via D_4797_179REAL; "
              "(G) qualified production property via is_qpp / D_4797_QPP. In tts a per-asset choice field, "
              "GREEN when the preparer sets it."},
    {"fact_key": "f4797_additional_depreciation", "label": "§1250 additional depreciation after 1975 (line 26a)",
     "data_type": "decimal", "default_value": "0", "sort_order": 7,
     "notes": "Excess of actual (INCLUDING any special depreciation allowance — i4797 verbatim) over "
              "straight-line, computed on the UNREDUCED basis (i4797 line 26a: 'do not reduce the basis... "
              "to figure straight line depreciation'). NUANCE LEG (2026-07-03, Decision 2): COMPUTED in tts "
              "(actual accumulated depreciation incl. bonus − SL-equivalent on the full cost basis over the "
              "same recovery period) for a disposed §1250 asset that has the MACRS data (method / life / "
              "convention / dates) — auto-handling 150DB land improvements AND bonused QIP; the computed "
              "value fills line 26a (YELLOW) and the preparer can override. When the engine LACKS the data "
              "(pre-1987 / ACRS, imported assets), it stays preparer-entered and D_4797_ADDL guards a blank. "
              "Auto-zero for the i4797 carve-out classes (27.5-yr residential / 22-31.5-39-yr nonresidential "
              "MACRS SL). §1250 applicable percentage = 100% (post-1975, non-low-income-housing)."},
    {"fact_key": "f4797_used_accel_bonus", "label": "§1250 property used accelerated method (150DB) or claimed bonus?",
     "data_type": "boolean", "default_value": "false", "sort_order": 7,
     "notes": "CLASSIFICATION LEG (Decision C2): drives the D_4797_ADDL gate. NUANCE LEG (2026-07-03): with "
              "26a now COMPUTED where the engine has the MACRS data, D_4797_ADDL is the FALLBACK gate — it "
              "fires only when this is true, 26a is 0/blank, AND the engine could not compute it (missing "
              "method/life/convention). Derived from the asset's method/bonus columns in tts."},
    {"fact_key": "f4797_applicable_pct_1250", "label": "§1250 applicable percentage (line 26b, default 100%)",
     "data_type": "decimal", "default_value": "1", "sort_order": 8},
    {"fact_key": "f4797_section_1252_deductions", "label": "§1252 soil/water/land-clearing deductions (line 27a)",
     "data_type": "decimal", "default_value": "0", "sort_order": 9},
    {"fact_key": "f4797_section_1252_pct", "label": "§1252 applicable % (line 27b; 100% yrs 1-5, then 80/60/40/20%)",
     "data_type": "decimal", "default_value": "0", "sort_order": 10,
     "notes": "Preparer-entered per the IRS schedule by years held (not encoded in v1)."},
    {"fact_key": "f4797_section_1254_costs", "label": "§1254 IDC / depletion deducted (line 28a)",
     "data_type": "decimal", "default_value": "0", "sort_order": 11},
    {"fact_key": "f4797_section_1255_excluded", "label": "§1255 §126 cost-sharing payments excluded (line 29a)",
     "data_type": "decimal", "default_value": "0", "sort_order": 12},
    {"fact_key": "f4797_section_1255_pct", "label": "§1255 applicable % (line 29a; by years held)",
     "data_type": "decimal", "default_value": "0", "sort_order": 13,
     "notes": "Preparer-entered per the IRS schedule (not encoded in v1)."},
    # ── return-level facts ──
    {"fact_key": "f4797_nonrecaptured_1231_losses", "label": "Nonrecaptured §1231 losses, prior 5 years (line 8)",
     "data_type": "decimal", "default_value": "0", "sort_order": 20,
     "notes": "§1231(c) 5-yr lookback. Preparer-asserted (no prior-year data in system) — check 2020-2024."},
    {"fact_key": "f4797_part1_line2_direct", "label": "Other §1231 gains/losses entered directly on Part I line 2",
     "data_type": "decimal", "default_value": "0", "sort_order": 21,
     "notes": "Long-term §1231 not routed through Part III (e.g., non-depreciable business land)."},
    {"fact_key": "f4797_part4_section_179_recapture", "label": "Part IV §179 recapture (line 35, col a)",
     "data_type": "decimal", "default_value": "0", "sort_order": 22,
     "notes": "§179 deduction claimed − depreciation that would have been allowable (business use ≤50%)."},
    {"fact_key": "f4797_part4_section_280f_recapture", "label": "Part IV §280F listed-property recapture (line 35, col b)",
     "data_type": "decimal", "default_value": "0", "sort_order": 23},
    # ── red-defer flags ──
    {"fact_key": "f4797_has_form_4684", "label": "Casualty/theft of business property (Form 4684)?",
     "data_type": "boolean", "default_value": "false", "sort_order": 30,
     "notes": "→ 4797 L3/L14/L18a/L33 interplay not modeled (RED-defer)."},
    {"fact_key": "f4797_has_form_6252", "label": "Installment sale (Form 6252)? (RETIRED — now supported)",
     "data_type": "boolean", "default_value": "false", "sort_order": 31,
     "notes": "RETIRED 2026-06-28 — the 6252 interplay is now supported (compute_6252 feeds Form "
              "4797 lines 4/10/15). Fact kept for the additive migration column; no longer RED-defers."},
    {"fact_key": "f4797_has_form_8824", "label": "Like-kind exchange (Form 8824)? (RETIRED — now supported)",
     "data_type": "boolean", "default_value": "false", "sort_order": 32,
     "notes": "RETIRED 2026-06-28 — the 8824 interplay is now supported (compute_8824 feeds Form "
              "4797 lines 5/16/10). Fact kept for the additive migration column; no longer RED-defers."},
    # ── outputs ──
    {"fact_key": "f4797_line7", "label": "Net §1231 gain or loss (line 7)", "data_type": "decimal",
     "sort_order": 50, "notes": "OUTPUT."},
    {"fact_key": "f4797_line9", "label": "Net §1231 LTCG after lookback (line 9) → Schedule D line 11",
     "data_type": "decimal", "sort_order": 51, "notes": "OUTPUT."},
    {"fact_key": "f4797_line18b", "label": "Ordinary gain/loss (line 18b) → Schedule 1 line 4",
     "data_type": "decimal", "sort_order": 52, "notes": "OUTPUT."},
    {"fact_key": "f4797_unrecaptured_1250", "label": "Unrecaptured §1250 gain → Sch D worksheet (25%)",
     "data_type": "decimal", "sort_order": 53, "notes": "OUTPUT — NOT a 4797 line; exported to Sch D."},
    {"fact_key": "f4797_sch1_line4", "label": "Schedule 1 line 4 = L18b + Part IV recapture",
     "data_type": "decimal", "sort_order": 54, "notes": "OUTPUT — the 1040 ordinary destination."},
]

P_RULES: list[dict] = [
    {"rule_id": "R-4797-GAIN", "title": "Per-property gain (lines 20-24)", "rule_type": "calculation",
     "precedence": 1, "sort_order": 1,
     "formula": "L23 = (cost_basis + expense_of_sale) − depreciation_allowed; L24 = sales_price − L23.",
     "inputs": ["f4797_sales_price", "f4797_cost_basis", "f4797_expense_of_sale", "f4797_depreciation_allowed"],
     "outputs": [],
     "description": "Adjusted basis = cost + expense − depreciation; total gain = amount realized − adjusted basis."},
    {"rule_id": "R-4797-ROUTE", "title": "Route each property (short-term / Part I / Part III)", "rule_type": "routing",
     "precedence": 2, "sort_order": 2,
     "formula": ("holding ≤12mo → Part II L10 (ordinary). Long-term loss OR non-depreciable §1231 gain "
                 "→ Part I L2. Long-term gain on §1245/1250/1252/1254/1255 → Part III."),
     "inputs": ["f4797_holding_period_months", "f4797_property_type"], "outputs": [],
     "description": "Holding period + property type drive the Part routing."},
    {"rule_id": "R-4797-RECAP", "title": "Part III recapture (§1245/1250/1252/1254/1255)", "rule_type": "calculation",
     "precedence": 3, "sort_order": 3,
     "formula": ("§1245 L25b = min(L24, depreciation). §1250 L26g = applicable% × min(L24, L26a additional "
                 "depr); unrecaptured §1250 = min(L24, depreciation) − L26g. §1252 L27c = min(L24, L27a×L27b%). "
                 "§1254 L28b = min(L24, L28a). §1255 L29b = min(L24, L29a×%). Ordinary = the section amount; "
                 "§1231 excess = L24 − ordinary."),
     "inputs": ["f4797_property_type", "f4797_depreciation_allowed", "f4797_additional_depreciation",
                "f4797_applicable_pct_1250", "f4797_section_1252_deductions", "f4797_section_1252_pct",
                "f4797_section_1254_costs", "f4797_section_1255_excluded", "f4797_section_1255_pct"],
     "outputs": ["f4797_unrecaptured_1250"],
     "description": "Per-section ordinary recapture; the excess is §1231 gain to Part I; §1250 leaves unrecaptured §1250."},
    {"rule_id": "R-4797-1231NET", "title": "Part I §1231 netting + 5-yr lookback (L7-L12)", "rule_type": "calculation",
     "precedence": 4, "sort_order": 4,
     "formula": ("L6 = ΣL32 (Part III excess); L7 = L2 + L6. If L7 ≤ 0 → L11 ordinary loss. If L7 > 0: "
                 "L8 = nonrecaptured §1231 losses; L12 = min(L7, L8) ordinary; L9 = max(0, L7 − L8) → "
                 "Schedule D line 11 (LTCG)."),
     "inputs": ["f4797_nonrecaptured_1231_losses", "f4797_part1_line2_direct"],
     "outputs": ["f4797_line7", "f4797_line9"],
     "description": "§1231(a) netting + §1231(c) 5-year nonrecaptured-loss lookback."},
    {"rule_id": "R-4797-ORD", "title": "Part II ordinary total → Schedule 1 line 4 (L17/L18b)", "rule_type": "calculation",
     "precedence": 5, "sort_order": 5,
     "formula": ("L17 = L10 + L11 + L12 + L13 (L14/15/16 = 0 v1); L18a = income-producing-property loss "
                 "(v1 = 0); L18b = L17 − L18a → Schedule 1 line 4."),
     "inputs": [], "outputs": ["f4797_line18b"],
     "description": "Part II combines short-term + §1231-recapture + Part III recapture → ordinary."},
    {"rule_id": "R-4797-PART4", "title": "Part IV §179/§280F recapture → Schedule 1 line 4 (L35)", "rule_type": "calculation",
     "precedence": 6, "sort_order": 6,
     "formula": "L35 = (deduction claimed) − (depreciation allowable); §179 (col a) + §280F (col b) → Schedule 1 line 4.",
     "inputs": ["f4797_part4_section_179_recapture", "f4797_part4_section_280f_recapture"],
     "outputs": ["f4797_sch1_line4"],
     "description": "Business-use-drop recapture; ordinary income (SE tax if Sch C/F — flagged)."},
    # ── CLASSIFICATION LEG (2026-07-02, Ken Decisions C1-C3) ──
    {"rule_id": "R-4797-CHARCLASS", "title": "§1245 vs §1250 by PROPERTY CHARACTER (not recovery period)", "rule_type": "classification",
     "precedence": 7, "sort_order": 7,
     "formula": ("§1250 property = depreciable REAL property that is not §1245 property (§1250(c)); §1245 "
                 "property = personal property PLUS the §1245(a)(3) real-property exceptions: (C) "
                 "§179-adjusted realty, (D) single-purpose agricultural/horticultural structures, (E) "
                 "petroleum storage, (F) RR grading/tunnel bore, (G) qualified production property "
                 "(§168(n)(2), OBBBA). RECOVERY PERIOD / LIFE IS NOT A CLASSIFIER: 15-yr land improvements "
                 "and 15-yr QIP are §1250. Implementation (Decision C1): character-based defaults by asset "
                 "group (Buildings → 1250; Improvements → 1250; Machinery/Furniture/Vehicles → 1245) + the "
                 "per-asset recapture_type override; every Improvements-group disposition at a gain fires "
                 "D_4797_CLASS listing the §1245 exceptions — surfaced, never silent. NUANCE LEG "
                 "(2026-07-03, Decision 1): the §1245(a)(3) real-property exceptions are now AUTO-classified "
                 "from a per-asset field (f4797_section_1245_exception) rather than left to the override — "
                 "single-purpose agricultural/horticultural structure (D, §168(i)(13)), petroleum storage "
                 "facility (E), and railroad grading/tunnel bore (F, §168(e)(4)) each return §1245 and fire "
                 "their info diagnostic. (C) §179-adjusted realty stays via D_4797_179REAL; (G) QPP via is_qpp."),
     "inputs": ["f4797_property_type", "f4797_section_1245_exception"], "outputs": [],
     "description": "Closes the recovery-period misclassification (tts resolve_recapture_type; the pinned "
                    "test_improvements_15yr_is_1245). §1250(c) verbatim; §1245(a)(3)(A)-(G) verbatim; the "
                    "(D)/(E)/(F) definitions per §168(i)(13)/§168(e)(4)."},
    {"rule_id": "R-4797-ADDLDEPR", "title": "Line 26a — additional depreciation computed (actual incl. bonus − SL); carve-out auto-zero", "rule_type": "calculation",
     "precedence": 8, "sort_order": 8,
     "formula": ("Additional depreciation = max(0, actual accumulated depreciation (INCLUDING any special "
                 "depreciation allowance — i4797 line 26a verbatim) − straight-line-equivalent accumulated "
                 "depreciation), the SL figured on the UNREDUCED basis over the same recovery period (i4797 "
                 "line 26a: 'do not reduce the basis... to figure straight line depreciation'; §1250(b)(1)). "
                 "NUANCE LEG (2026-07-03, Decision 2): COMPUTED in tts where the disposed §1250 asset has the "
                 "MACRS data (method/life/convention/dates) — auto-handling BOTH 150DB land improvements "
                 "(§168(b)(2)(A)) and bonused QIP; the computed value fills line 26a, preparer-overridable. "
                 "§1250 ordinary = applicable% (100%) × min(gain, line 26a). Auto-zero for the i4797 "
                 "carve-out classes (27.5-yr residential; 22/31.5/39-yr nonresidential MACRS SL). FALLBACK: "
                 "when the engine cannot compute (pre-1987/ACRS, imported), 26a stays preparer-entered and "
                 "D_4797_ADDL (ERROR) guards a blank on an accel/bonus asset — the no-silent-gap gate."),
     "inputs": ["f4797_used_accel_bonus", "f4797_additional_depreciation", "f4797_property_type"],
     "outputs": [],
     "description": "Bonus-on-QIP RESOLVED and now statutorily grounded: additional depreciation = actual "
                    "'including any special depreciation allowance' (i4797 2025 p.10) over SL on the "
                    "unreduced basis (§1250(b)(1)/(b)(3): the (b)(3) carve-out excludes only PRE-1976 §168, "
                    "so current MACRS/§168(k) bonus IS a depreciation adjustment). 150DB (§168(b)(2)(A)) > "
                    "SL → additional depreciation exists for 15-yr land improvements."},
]

P_LINES: list[dict] = [
    {"line_number": "2", "description": "Line 2 — long-term §1231 gains/losses not in Part III", "line_type": "input"},
    {"line_number": "6", "description": "Line 6 — gain from Part III line 32 (excess over recapture)", "line_type": "calculated"},
    {"line_number": "7", "description": "Line 7 — net §1231 gain or loss (combine lines 2-6)", "line_type": "calculated"},
    {"line_number": "8", "description": "Line 8 — nonrecaptured §1231 losses, prior 5 years (§1231(c) lookback)", "line_type": "input"},
    {"line_number": "9", "description": "Line 9 — line 7 minus line 8; the gain → Schedule D",
     "line_type": "total", "destination_form": "Schedule D (Form 1040) line 11 — LTCG (individuals)"},
    {"line_number": "10", "description": "Line 10 — ordinary gains/losses, property held ≤1 year", "line_type": "input"},
    {"line_number": "11", "description": "Line 11 — loss from line 7 (net §1231 loss is ordinary)", "line_type": "calculated"},
    {"line_number": "12", "description": "Line 12 — gain from line 7 recharacterized ordinary (= line 8 lookback)", "line_type": "calculated"},
    {"line_number": "13", "description": "Line 13 — gain from Part III line 31 (depreciation recapture)", "line_type": "calculated"},
    {"line_number": "17", "description": "Line 17 — combine lines 10 through 16", "line_type": "calculated"},
    {"line_number": "18a", "description": "Line 18a — loss from income-producing property (individuals)",
     "line_type": "total", "destination_form": "Schedule A (Form 1040) line 16 — v1 = 0 (RED-defer 4684)"},
    {"line_number": "18b", "description": "Line 18b — line 17 minus line 18a (ordinary gain/loss)",
     "line_type": "total", "destination_form": "Schedule 1 (Form 1040) line 4 (individuals)"},
    {"line_number": "20", "description": "Line 20 — gross sales price / amount realized (per property)", "line_type": "input"},
    {"line_number": "21", "description": "Line 21 — cost or other basis plus expense of sale", "line_type": "input"},
    {"line_number": "22", "description": "Line 22 — depreciation/§179/amortization allowed or allowable", "line_type": "input"},
    {"line_number": "23", "description": "Line 23 — adjusted basis (line 21 − line 22)", "line_type": "calculated"},
    {"line_number": "24", "description": "Line 24 — total gain (line 20 − line 23)", "line_type": "calculated"},
    {"line_number": "25a", "description": "Line 25a — §1245 depreciation allowed or allowable", "line_type": "input"},
    {"line_number": "25b", "description": "Line 25b — §1245 ordinary recapture (smaller of line 24 or 25a)", "line_type": "calculated"},
    {"line_number": "26a", "description": "Line 26a — §1250 additional depreciation after 1975", "line_type": "input"},
    {"line_number": "26g", "description": "Line 26g — §1250 ordinary recapture (applicable% × smaller(24,26a))", "line_type": "calculated"},
    {"line_number": "27a", "description": "Line 27a — §1252 soil/water/land-clearing deductions", "line_type": "input"},
    {"line_number": "27c", "description": "Line 27c — §1252 ordinary recapture (smaller of 24 or 27a×27b%)", "line_type": "calculated"},
    {"line_number": "28a", "description": "Line 28a — §1254 IDC / depletion deducted", "line_type": "input"},
    {"line_number": "28b", "description": "Line 28b — §1254 ordinary recapture (smaller of 24 or 28a)", "line_type": "calculated"},
    {"line_number": "29a", "description": "Line 29a — §1255 §126 cost-sharing × applicable %", "line_type": "input"},
    {"line_number": "29b", "description": "Line 29b — §1255 ordinary recapture (smaller of 24 or 29a)", "line_type": "calculated"},
    {"line_number": "30", "description": "Line 30 — total gains for all properties (Σ line 24)", "line_type": "calculated"},
    {"line_number": "31", "description": "Line 31 — total ordinary recapture (Σ 25b/26g/27c/28b/29b)",
     "line_type": "calculated", "destination_form": "Part II line 13"},
    {"line_number": "32", "description": "Line 32 — line 30 − line 31 (excess); casualty → 4684, rest → Part I line 6",
     "line_type": "calculated", "destination_form": "Part I line 6 (+ Form 4684 line 33 for casualty portion)"},
    {"line_number": "33", "description": "Line 33 — §179/§280F deduction claimed (Part IV)", "line_type": "input"},
    {"line_number": "34", "description": "Line 34 — depreciation that would have been allowable (Part IV)", "line_type": "input"},
    {"line_number": "35", "description": "Line 35 — §179/§280F recapture (line 33 − line 34)",
     "line_type": "total", "destination_form": "Schedule 1 (Form 1040) line 4 — other income (SE tax if Sch C/F)"},
    {"line_number": "ur1250", "description": "Unrecaptured §1250 gain (NOT a 4797 line) → Sch D worksheet (25%)",
     "line_type": "total", "destination_form": "Schedule D Unrecaptured §1250 Gain Worksheet → Schedule D Tax Worksheet"},
]

P_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_4797_001", "title": "Check the §1231 5-year lookback", "severity": "warning",
     "condition": "net §1231 gain (line 7 > 0) AND nonrecaptured_1231_losses == 0",
     "message": ("This return has a net §1231 gain. Verify whether there were net §1231 LOSSES in the "
                 "prior 5 years (2020-2024) that were deducted as ordinary — under §1231(c) those "
                 "'nonrecaptured' losses recharacterize this year's gain as ordinary income (line 8). "
                 "Enter them on line 8; the system has no prior-year §1231 history."),
     "notes": "§1231(c). Preparer-asserted (Ken's call) — the no-prior-year-data prompt."},
    {"diagnostic_id": "D_4797_002", "title": "Casualty/theft (Form 4684) interplay not modeled", "severity": "error",
     "condition": "has_form_4684",
     "message": ("A casualty or theft of business property (Form 4684) is indicated. The Form 4797 "
                 "interplay (lines 3, 14, 18a, and the Part III line 33 casualty split) is not modeled "
                 "in this version — prepare the 4684 ↔ 4797 flow manually."),
     "notes": "v1 RED-defer (no silent gap)."},
    {"diagnostic_id": "D_4797_003", "title": "Installment sale (Form 6252) interplay — RETIRED (now supported)", "severity": "error",
     "condition": "has_form_6252",
     "message": ("RETIRED 2026-06-28 — the Form 6252 installment interplay is now supported: "
                 "compute_6252 feeds the §1231 gain to Form 4797 line 4, the ordinary gain to line 10, "
                 "and the ordinary recapture to line 15. This diagnostic no longer fires."),
     "notes": "RETIRED 2026-06-28 — 6252 interplay closed. Deactivated in the tts diagnostics registry."},
    {"diagnostic_id": "D_4797_004", "title": "Like-kind exchange (Form 8824) interplay — RETIRED (now supported)", "severity": "error",
     "condition": "has_form_8824",
     "message": ("RETIRED 2026-06-28 — the Form 8824 like-kind interplay is now supported: compute_8824 "
                 "feeds the recognized §1231 gain to Form 4797 line 5, the ordinary recapture/gain to "
                 "line 16, and the §1043 ordinary to line 10. This diagnostic no longer fires."),
     "notes": "RETIRED 2026-06-28 — 8824 interplay closed. Deactivated in the tts diagnostics registry."},
    {"diagnostic_id": "D_4797_005", "title": "§179/§280F recapture may be subject to SE tax", "severity": "info",
     "condition": "Part IV recapture > 0",
     "message": ("Part IV §179/§280F recapture is reported as other income on Schedule 1 line 4. If the "
                 "property was used in a trade or business reported on Schedule C or F, this recapture is "
                 "subject to self-employment tax — the automatic SE-tax add-back is not modeled; verify "
                 "and add it on Schedule SE if applicable."),
     "notes": "Ken's call — Sch 1 L4 routing + SE-nuance flag (auto SE add-back RED-deferred)."},
    {"diagnostic_id": "D_4797_006", "title": "§1252/§1255 applicable percentage required", "severity": "warning",
     "condition": "property_type in (1252, 1255) AND applicable percentage == 0",
     "message": ("§1252 (farmland) and §1255 (§126 cost-sharing) recapture use an applicable percentage "
                 "based on years held (100% for the early years, phasing to 0%). Enter the percentage "
                 "from the IRS schedule — this version does not derive it from the holding period."),
     "notes": "Preparer-entered percentage (not encoded in v1)."},
    {"diagnostic_id": "D_4797_007", "title": "Depreciable property with zero depreciation", "severity": "warning",
     "condition": "property_type in (1245,1250) AND gain > 0 AND depreciation_allowed == 0",
     "message": ("This §1245/§1250 property shows a gain but no depreciation to recapture. Depreciation "
                 "'allowable' must be reported even if it was never claimed — verify the basis and "
                 "depreciation entries."),
     "notes": "§1245/§1250 'allowed or allowable'."},
    # ── CLASSIFICATION LEG (2026-07-02) ──
    {"diagnostic_id": "D_4797_CLASS", "title": "Improvements disposition — confirm §1245 vs §1250 character", "severity": "warning",
     "condition": "a disposed Improvements-group asset has a long-term gain with depreciation (Part III routing)",
     "message": ("Confirm this improvement's recapture character. Depreciable REAL property is §1250 "
                 "regardless of its recovery period — 15-year land improvements and qualified improvement "
                 "property (QIP) are §1250, NOT §1245. The §1245 exceptions for real property are: "
                 "§179-adjusted realty (§1245(a)(3)(C)), single-purpose agricultural or horticultural "
                 "structures ((D)), petroleum storage facilities ((E)), railroad grading/tunnel bore ((F)), "
                 "and qualified production property ((G), OBBBA, placed in service after 7/4/2025). The "
                 "character default has been set to §1250 — override recapture_type if this asset is one "
                 "of the exceptions."),
     "notes": "Decision C1. Fires once per Improvements-group disposition at a gain; the character "
              "default is applied (never silent)."},
    {"diagnostic_id": "D_4797_ADDL", "title": "§1250 accelerated/bonus asset — line 26a required", "severity": "error",
     "condition": "property_type == 1250 AND used_accel_bonus AND additional_depreciation == 0",
     "message": ("This §1250 property was depreciated with an accelerated method (e.g. 150DB land "
                 "improvements) or claimed a special depreciation allowance (bonus — e.g. QIP), so "
                 "additional depreciation exists and line 26a cannot be zero: additional depreciation is "
                 "the excess of actual depreciation (including any special depreciation allowance) over "
                 "straight line (i4797). With 26a blank the §1250 ordinary recapture is understated (and "
                 "on a 1065, box 14a self-employment earnings are misstated through the worksheet 1d/2 "
                 "adjustment). Enter the excess-over-straight-line amount on line 26a."),
     "notes": "Decision C2 hard gate; NUANCE LEG (2026-07-03, Decision 2): now the FALLBACK gate — with 26a "
              "computed where the engine has the MACRS data, this fires only when the engine could NOT "
              "compute it (missing method/life/convention: pre-1987/ACRS, imported) and 26a is left blank. "
              "The 27.5/39-yr MACRS carve-out classes stay auto-zero and never fire this."},
    {"diagnostic_id": "D_4797_179REAL", "title": "§179-expensed real property — §1245 recapture applies", "severity": "warning",
     "condition": "a disposed real-property asset carries §179 expensing",
     "message": ("This real property took a section 179 expense deduction. Under §1245(a)(3)(C), real "
                 "property adjusted for §179 is SECTION 1245 property to that extent — the §179 "
                 "adjustments recapture in full as ordinary income, not under the §1250 "
                 "additional-depreciation rule. The §1245/§1250 split for a partially-§179'd asset is not "
                 "computed in this version — figure the split manually (Part III lines 25/26)."),
     "notes": "Decision C3 (v1 diagnostic only; no split engine)."},
    {"diagnostic_id": "D_4797_QPP", "title": "Qualified production property is §1245 (OBBBA)", "severity": "info",
     "condition": "a disposed asset is qualified production property (§168(n)(2), placed in service after 7/4/2025)",
     "message": ("Qualified production property (§168(n)(2), added by OBBBA effective July 4, 2025) is "
                 "SECTION 1245 property under §1245(a)(3)(G) even though it is real property — its "
                 "expensed/depreciated amounts recapture in full as ordinary income on disposition. "
                 "Classify it 1245, not 1250."),
     "notes": "Decision C3 (v1 flag). New law — re-verify each season."},
    # ── NUANCE LEG (2026-07-03, Decision 1): the (D)/(E)/(F) §1245 real-property exceptions ──
    {"diagnostic_id": "D_4797_1245AG", "title": "Single-purpose ag/horticultural structure is §1245", "severity": "info",
     "condition": "a disposed asset has section_1245_exception == single_purpose_ag",
     "message": ("This asset is classified as a single purpose agricultural or horticultural structure "
                 "(a single purpose livestock structure or a greenhouse for commercial plant production, "
                 "§168(i)(13)). Under §1245(a)(3)(D) it is SECTION 1245 property even though it is a "
                 "structure — ALL depreciation recaptures as ordinary income on disposition (line 25), not "
                 "the §1250 additional-depreciation rule. It has been auto-classified §1245."),
     "notes": "Decision 1 (nuance leg). §1245(a)(3)(D) / §168(i)(13)."},
    {"diagnostic_id": "D_4797_1245PETRO", "title": "Petroleum storage facility is §1245", "severity": "info",
     "condition": "a disposed asset has section_1245_exception == petroleum_storage",
     "message": ("This asset is classified as a storage facility (other than a building or its structural "
                 "components) used in the distribution of petroleum or a primary petroleum product. Under "
                 "§1245(a)(3)(E) it is SECTION 1245 property — ALL depreciation recaptures as ordinary "
                 "income on disposition (line 25), not the §1250 rule. It has been auto-classified §1245."),
     "notes": "Decision 1 (nuance leg). §1245(a)(3)(E)."},
    {"diagnostic_id": "D_4797_1245RRGR", "title": "Railroad grading / tunnel bore is §1245", "severity": "info",
     "condition": "a disposed asset has section_1245_exception == railroad_grading",
     "message": ("This asset is classified as railroad grading or a tunnel bore (§168(e)(4) — improvements "
                 "from excavation, embankments, tunneling, and similar work for a railroad roadbed or "
                 "right-of-way). Under §1245(a)(3)(F) it is SECTION 1245 property — ALL depreciation "
                 "recaptures as ordinary income on disposition (line 25), not the §1250 rule. It has been "
                 "auto-classified §1245."),
     "notes": "Decision 1 (nuance leg). §1245(a)(3)(F) / §168(e)(4)."},
]

P_SCENARIOS: list[dict] = [
    {"scenario_name": "F4797-T1 — §1245 full recapture (gain < depreciation)", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"properties": [{"sales_price": 50000, "cost_basis": 100000, "depreciation_allowed": 60000,
                                "holding_period_months": 36, "property_type": "1245"}]},
     "expected_outputs": {"f4797_line18b": 10000, "f4797_sch1_line4": 10000, "f4797_line9": 0,
                          "f4797_unrecaptured_1250": 0},
     "notes": "adj basis 40000; gain 10000 < depr 60000 → all 10000 ordinary (L25b) → L13 → L18b → Sch 1 L4."},
    {"scenario_name": "F4797-T2 — §1245 gain exceeds depreciation → ordinary + §1231 LTCG", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"properties": [{"sales_price": 120000, "cost_basis": 100000, "depreciation_allowed": 30000,
                                "holding_period_months": 60, "property_type": "1245"}]},
     "expected_outputs": {"f4797_line18b": 30000, "f4797_line7": 20000, "f4797_line9": 20000,
                          "f4797_sch1_line4": 30000},
     "notes": "gain 50000; ordinary 30000 (L13); excess 20000 → Part I L6 → L7 → L9 → Sch D (no lookback)."},
    {"scenario_name": "F4797-T3 — §1231 loss is ordinary", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"properties": [{"sales_price": 30000, "cost_basis": 100000, "depreciation_allowed": 50000,
                                "holding_period_months": 48, "property_type": "1245"}]},
     "expected_outputs": {"f4797_line7": -20000, "f4797_line18b": -20000, "f4797_line9": 0,
                          "f4797_sch1_line4": -20000},
     "notes": "adj basis 50000; loss 20000 → Part I L2 → L7 loss → L11 ordinary → L18b → Sch 1 L4."},
    {"scenario_name": "F4797-T4 — short-term → all ordinary (Part II line 10)", "scenario_type": "edge_case", "sort_order": 4,
     "inputs": {"properties": [{"sales_price": 60000, "cost_basis": 80000, "depreciation_allowed": 40000,
                                "holding_period_months": 6, "property_type": "1245"}]},
     "expected_outputs": {"f4797_line18b": 20000, "f4797_line9": 0, "f4797_sch1_line4": 20000},
     "notes": "held 6mo → short-term bypasses §1231/recapture; gain 20000 → L10 → L18b → Sch 1 L4."},
    {"scenario_name": "F4797-T5 — §1250 post-1986 SL: unrecaptured §1250 @25%", "scenario_type": "edge_case", "sort_order": 5,
     "inputs": {"properties": [{"sales_price": 500000, "cost_basis": 400000, "depreciation_allowed": 100000,
                                "holding_period_months": 120, "property_type": "1250",
                                "additional_depreciation": 0}]},
     "expected_outputs": {"f4797_line18b": 0, "f4797_line7": 200000, "f4797_line9": 200000,
                          "f4797_unrecaptured_1250": 100000, "f4797_sch1_line4": 0},
     "notes": ("adj basis 300000; gain 200000; SL → 26a 0 → §1250 ordinary 0; §1231 excess 200000 → L9 "
               "→ Sch D; unrecaptured §1250 = min(200000,100000) − 0 = 100000 @25%.")},
    {"scenario_name": "F4797-T6 — §1231 5-year lookback recharacterizes gain", "scenario_type": "edge_case", "sort_order": 6,
     "inputs": {"properties": [{"sales_price": 120000, "cost_basis": 100000, "depreciation_allowed": 30000,
                                "holding_period_months": 60, "property_type": "1245"}],
                "nonrecaptured_1231_losses": 8000},
     "expected_outputs": {"f4797_line7": 20000, "f4797_line9": 12000, "f4797_line18b": 38000,
                          "f4797_sch1_line4": 38000},
     "notes": ("§1231 excess 20000; lookback L8 8000 → L12 ordinary 8000; L9 = 20000−8000 = 12000 → Sch "
               "D; L18b = 30000 (L13) + 8000 (L12) = 38000.")},
    {"scenario_name": "F4797-T7 — §1252 farmland recapture (preparer %)", "scenario_type": "normal", "sort_order": 7,
     "inputs": {"properties": [{"sales_price": 200000, "cost_basis": 150000, "depreciation_allowed": 0,
                                "holding_period_months": 84, "property_type": "1252",
                                "section_1252_deductions": 30000, "section_1252_pct": 0.6}]},
     "expected_outputs": {"f4797_line18b": 18000, "f4797_line7": 32000, "f4797_line9": 32000,
                          "f4797_sch1_line4": 18000},
     "notes": "gain 50000; §1252 ordinary = min(50000, 30000×0.60=18000) = 18000 → L13; excess 32000 → L9 Sch D."},
    {"scenario_name": "F4797-T8 — Part IV §179 recapture → Schedule 1 line 4", "scenario_type": "normal", "sort_order": 8,
     "inputs": {"properties": [], "part4_section_179_recapture": 7000},
     "expected_outputs": {"f4797_sch1_line4": 7000, "f4797_line18b": 0},
     "notes": "no dispositions; §179 recapture 7000 → Sch 1 L4 (D_4797_005 SE-tax info)."},
    {"scenario_name": "F4797-T9 — §1254 oil-and-gas IDC recapture", "scenario_type": "normal", "sort_order": 9,
     "inputs": {"properties": [{"sales_price": 90000, "cost_basis": 40000, "depreciation_allowed": 10000,
                                "holding_period_months": 48, "property_type": "1254",
                                "section_1254_costs": 25000}]},
     "expected_outputs": {"f4797_line18b": 25000, "f4797_line7": 35000, "f4797_line9": 35000,
                          "f4797_sch1_line4": 25000},
     "notes": "adj basis 30000; gain 60000; §1254 ordinary = min(60000,25000) = 25000 → L13; excess 35000 → L9 Sch D."},
    {"scenario_name": "F4797-G1 — casualty (Form 4684) → RED-defer", "scenario_type": "diagnostic", "sort_order": 10,
     "inputs": {"properties": [{"sales_price": 50000, "cost_basis": 80000, "depreciation_allowed": 20000,
                                "holding_period_months": 36, "property_type": "1245"}],
                "has_form_4684": True},
     "expected_outputs": {"D_4797_002": True},
     "notes": "Form 4684 present → RED-defer the 4684 ↔ 4797 interplay."},
    {"scenario_name": "F4797-G3 — net §1231 gain, no lookback entered → warn", "scenario_type": "diagnostic", "sort_order": 12,
     "inputs": {"properties": [{"sales_price": 120000, "cost_basis": 100000, "depreciation_allowed": 30000,
                                "holding_period_months": 60, "property_type": "1245"}],
                "nonrecaptured_1231_losses": 0},
     "expected_outputs": {"D_4797_001": True},
     "notes": "net §1231 gain 20000 with no line-8 entry → D_4797_001 (check prior-5-yr §1231 losses)."},
    # ── CLASSIFICATION LEG (2026-07-02, C-scenarios) ──
    {"scenario_name": "F4797-C1 — 15-yr land improvement (150DB): §1250 partial ordinary", "scenario_type": "normal", "sort_order": 13,
     "inputs": {"properties": [{"sales_price": 500000, "cost_basis": 400000, "depreciation_allowed": 100000,
                                "holding_period_months": 120, "property_type": "1250",
                                "additional_depreciation": 20000, "used_accel_bonus": True}]},
     "expected_outputs": {"f4797_line18b": 20000, "f4797_line7": 180000, "f4797_line9": 180000,
                          "f4797_unrecaptured_1250": 80000, "f4797_sch1_line4": 20000},
     "notes": "THE BUG SCENARIO, correctly classified: adj basis 300k; gain 200k. §1250 with 150DB → "
              "additional depr 20k (excess over SL, preparer) → L26g ordinary 20k (NOT the §1245 100k). "
              "Unrecap §1250 = min(200k,100k) − 20k = 80k @25%; §1231 excess 180k → Sch D."},
    {"scenario_name": "F4797-C2 — QIP straight-line, no bonus: zero ordinary, all unrecaptured", "scenario_type": "normal", "sort_order": 14,
     "inputs": {"properties": [{"sales_price": 500000, "cost_basis": 400000, "depreciation_allowed": 100000,
                                "holding_period_months": 120, "property_type": "1250",
                                "additional_depreciation": 0, "used_accel_bonus": False}]},
     "expected_outputs": {"f4797_line18b": 0, "f4797_line7": 200000, "f4797_line9": 200000,
                          "f4797_unrecaptured_1250": 100000, "f4797_sch1_line4": 0},
     "notes": "15-yr QIP actually depreciated SL with no bonus: additional depr 0 → L26g 0; the whole "
              "100k depreciation is unrecaptured §1250 @25%; §1231 200k → Sch D. (Old code got this "
              "right only by accident when classified 1250.)"},
    {"scenario_name": "F4797-C3 — QIP with 100% bonus: bonus IS additional depreciation", "scenario_type": "normal", "sort_order": 15,
     "inputs": {"properties": [{"sales_price": 350000, "cost_basis": 300000, "depreciation_allowed": 300000,
                                "holding_period_months": 60, "property_type": "1250",
                                "additional_depreciation": 280000, "used_accel_bonus": True}]},
     "expected_outputs": {"f4797_line18b": 280000, "f4797_line7": 70000, "f4797_line9": 70000,
                          "f4797_unrecaptured_1250": 20000, "f4797_sch1_line4": 280000},
     "notes": "THE RESOLVED QUESTION: QIP fully bonused (300k), SL-to-date 20k → additional depr 280k "
              "(i4797: 'including any special depreciation allowance'). adj basis 0; gain 350k; L26g = "
              "min(350k,280k) = 280k ordinary; unrecap = min(350k,300k) − 280k = 20k; §1231 70k → Sch D."},
    {"scenario_name": "F4797-C4 — §1250 accel/bonus with blank 26a → D_4797_ADDL", "scenario_type": "diagnostic", "sort_order": 16,
     "inputs": {"properties": [{"sales_price": 500000, "cost_basis": 400000, "depreciation_allowed": 100000,
                                "holding_period_months": 120, "property_type": "1250",
                                "additional_depreciation": 0, "used_accel_bonus": True}]},
     "expected_outputs": {"D_4797_ADDL": True},
     "notes": "Decision C2 hard gate: 150DB/bonus §1250 asset with line 26a zero → ERROR (ordinary "
              "recapture understated; on a 1065 the SE base is misstated too)."},
    {"scenario_name": "F4797-C5 — Improvements disposition → D_4797_CLASS character check", "scenario_type": "diagnostic", "sort_order": 17,
     "inputs": {"properties": [{"sales_price": 200000, "cost_basis": 150000, "depreciation_allowed": 50000,
                                "holding_period_months": 48, "property_type": "1250",
                                "asset_group": "Improvements"}]},
     "expected_outputs": {"D_4797_CLASS": True},
     "notes": "Decision C1: every Improvements-group disposition at a gain surfaces the §1245-exceptions "
              "checklist (single-purpose ag / §179-adjusted / QPP) with the §1250 character default applied."},
    # ── NUANCE LEG (2026-07-03, N-scenarios) ──
    {"scenario_name": "F4797-N1 — single-purpose ag structure is §1245 (full recapture, not §1250)", "scenario_type": "normal", "sort_order": 18,
     "inputs": {"properties": [{"sales_price": 300000, "cost_basis": 250000, "depreciation_allowed": 80000,
                                "holding_period_months": 84, "property_type": "1245",
                                "section_1245_exception": "single_purpose_ag"}]},
     "expected_outputs": {"f4797_line18b": 80000, "f4797_line7": 50000, "f4797_line9": 50000,
                          "f4797_unrecaptured_1250": 0, "f4797_sch1_line4": 80000},
     "notes": ("Decision 1: a single-purpose ag/hort structure (§168(i)(13)) is §1245 under §1245(a)(3)(D) "
               "even though it is a structure — resolve_recapture_type returns 1245. adj basis 170k; gain "
               "130k; §1245 ordinary = min(130k, 80k depr) = 80k → L13 → L18b (NOT the §1250 "
               "additional-depreciation rule, and NO unrecaptured §1250); excess 50k → §1231 → L9 Sch D.")},
    {"scenario_name": "F4797-N2 — single-purpose ag classification → D_4797_1245AG", "scenario_type": "diagnostic", "sort_order": 19,
     "inputs": {"properties": [{"sales_price": 300000, "cost_basis": 250000, "depreciation_allowed": 80000,
                                "holding_period_months": 84, "property_type": "1245",
                                "section_1245_exception": "single_purpose_ag"}]},
     "expected_outputs": {"D_4797_1245AG": True},
     "notes": "Decision 1: the single-purpose ag/hort structure auto-classified §1245 fires the info diagnostic (§1245(a)(3)(D))."},
    {"scenario_name": "F4797-N3 — petroleum storage classification → D_4797_1245PETRO", "scenario_type": "diagnostic", "sort_order": 20,
     "inputs": {"properties": [{"sales_price": 300000, "cost_basis": 250000, "depreciation_allowed": 80000,
                                "holding_period_months": 84, "property_type": "1245",
                                "section_1245_exception": "petroleum_storage"}]},
     "expected_outputs": {"D_4797_1245PETRO": True},
     "notes": "Decision 1: a petroleum-distribution storage facility (not a building) is §1245 under §1245(a)(3)(E)."},
    {"scenario_name": "F4797-N4 — railroad grading classification → D_4797_1245RRGR", "scenario_type": "diagnostic", "sort_order": 21,
     "inputs": {"properties": [{"sales_price": 300000, "cost_basis": 250000, "depreciation_allowed": 80000,
                                "holding_period_months": 84, "property_type": "1245",
                                "section_1245_exception": "railroad_grading"}]},
     "expected_outputs": {"D_4797_1245RRGR": True},
     "notes": "Decision 1: railroad grading/tunnel bore (§168(e)(4)) is §1245 under §1245(a)(3)(F)."},
]

P_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-4797-GAIN", "IRS_2025_4797_INSTR", "primary", "Part III lines 20-24 gain computation"),
    ("R-4797-ROUTE", "IRS_2025_4797_INSTR", "primary", "Part I/II/III routing by holding period + type"),
    ("R-4797-ROUTE", "IRC_1231", "secondary", "§1231 >1-year holding for Part I"),
    ("R-4797-RECAP", "IRC_1245", "primary", "§1245 all-depreciation recapture"),
    ("R-4797-RECAP", "IRC_1250", "primary", "§1250 additional-depreciation recapture"),
    ("R-4797-RECAP", "IRC_1_H_1_E", "secondary", "unrecaptured §1250 gain (25%)"),
    ("R-4797-RECAP", "IRC_1252_1254_1255", "primary", "§1252/1254/1255 specialty recapture"),
    ("R-4797-1231NET", "IRC_1231", "primary", "§1231(a) netting + §1231(c) 5-year lookback"),
    ("R-4797-1231NET", "IRS_2025_4797_INSTR", "secondary", "Part I lines 7-9 → Schedule D"),
    ("R-4797-ORD", "IRS_2025_4797_INSTR", "primary", "Part II lines 17-18b → Schedule 1 line 4"),
    ("R-4797-PART4", "IRC_179D_280F", "primary", "§179(d)(10)/§280F(b)(2) recapture"),
    ("R-4797-PART4", "IRS_2025_4797_INSTR", "secondary", "Part IV lines 33-35"),
    # Classification leg
    ("R-4797-CHARCLASS", "IRC_1250", "primary", "§1250(c): real property not §1245 — character, not recovery period"),
    ("R-4797-CHARCLASS", "IRC_1245", "primary", "§1245(a)(3): the enumerated real-property exceptions (C/D/E/F/G)"),
    ("R-4797-CHARCLASS", "IRC_168", "secondary", "§168(i)(13) single-purpose ag / §168(e)(4) railroad grading definitions"),
    ("R-4797-CHARCLASS", "IRS_2025_4797_INSTR", "secondary", "i4797 'Section 1250 property' definition (verbatim)"),
    ("R-4797-ADDLDEPR", "IRS_2025_4797_INSTR", "primary", "Line 26a verbatim: additional depr incl. special allowance; SL on unreduced basis"),
    ("R-4797-ADDLDEPR", "IRC_1250", "primary", "§1250(b)(1)/(b)(3) additional depreciation over straight line"),
    ("R-4797-ADDLDEPR", "IRC_168", "secondary", "§168(b)(2)(A) 150DB for 15-yr land improvements; §168(k) bonus is a depreciation adjustment"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-4797-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Part III §1245 recapture = smaller of gain or depreciation → Part II line 13",
     "description": "Validates R-4797-RECAP (§1245). Bug it catches: recapturing more than the gain, or excess-over-SL applied to §1245.",
     "definition": {"kind": "formula_check", "form": "4797",
                    "formula": "L25b = min(L24, depreciation_allowed); ordinary → L13"},
     "sort_order": 1},
    {"assertion_id": "FA-1040-4797-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "§1245 excess gain → Part I line 6 → net §1231 → Schedule D line 11",
     "description": "Validates R-4797-1231NET. Bug it catches: §1231 excess not flowing to Schedule D as LTCG.",
     "definition": {"kind": "flow_assertion", "form": "4797",
                    "checks": [{"source_line": "9", "must_write_to": ["SCH_D.11"]}]},
     "sort_order": 2},
    {"assertion_id": "FA-1040-4797-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "§1231 5-year lookback: L12 ordinary = min(L7,L8), L9 = max(0,L7−L8)",
     "description": "Validates the §1231(c) lookback. Bug it catches: gain not recharacterized to ordinary up to the prior-5-yr losses.",
     "definition": {"kind": "formula_check", "form": "4797",
                    "formula": "if L7>0: L12 = min(L7, L8); L9 = max(0, L7 − L8)"},
     "sort_order": 3},
    {"assertion_id": "FA-1040-4797-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Part II line 18b → Schedule 1 line 4",
     "description": "Validates R-4797-ORD + the flow target. Bug it catches: ordinary 4797 gain not landing on Schedule 1 line 4.",
     "definition": {"kind": "flow_assertion", "form": "4797",
                    "checks": [{"source_line": "18b", "must_write_to": ["SCH_1.4"]}]},
     "sort_order": 4},
    {"assertion_id": "FA-1040-4797-05", "assertion_type": "reconciliation", "entity_types": ["1040"],
     "title": "Unrecaptured §1250 gain = min(gain,depr) − §1250 ordinary → Sch D worksheet",
     "description": "Validates the unrecaptured-§1250 export. Bug it catches: the 25% bucket not exported to the Schedule D Tax Worksheet.",
     "definition": {"kind": "reconciliation", "form": "4797",
                    "formula": "unrecaptured_1250 = min(L24, depreciation) − L26g → SDTW"},
     "sort_order": 5},
    {"assertion_id": "FA-1040-4797-06", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Part IV §179/§280F recapture (L35) → Schedule 1 line 4",
     "description": "Validates R-4797-PART4. Bug it catches: business-use-drop recapture not reaching ordinary income.",
     "definition": {"kind": "flow_assertion", "form": "4797",
                    "checks": [{"source_line": "35", "must_write_to": ["SCH_1.4"]}]},
     "sort_order": 6},
    {"assertion_id": "FA-1040-4797-07", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Gates — 4684 casualty interplay RED-defers (6252 + 8824 now supported)",
     "description": "An unsupported interplay (casualty) fires a RED diagnostic and defers — never a silent wrong number. The Form 6252 installment interplay (feeds Form 4797 lines 4/10/15) and the Form 8824 like-kind interplay (feeds lines 5/16/10) are now supported.",
     "definition": {"kind": "gating_check", "form": "4797", "expect": {"red_fires": True},
                    "blockers": ["form_4684_casualty"]},
     "sort_order": 7},
]


FORMS: list[dict] = [
    {"identity": P_IDENTITY, "facts": P_FACTS, "rules": P_RULES, "lines": P_LINES,
     "diagnostics": P_DIAGNOSTICS, "scenarios": P_SCENARIOS, "rule_links": P_RULE_LINKS},
]


class Command(BaseCommand):
    help = "Load the Form 4797 spec (Sales of Business Property). Refuses until READY_TO_SEED=True."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad Form 4797 spec (Sales of Business Property)\n"))
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
                "\nREFUSING TO SEED Form 4797: not cleared to seed.\n\n"
                "Gated until Ken's review walk (the recapture arithmetic, the 1040 routing,\n"
                "the §1231(c) lookback, the unrecaptured-§1250 export, the §1252/1255 schedules).\n\n"
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
        form = TaxForm.objects.filter(form_number="4797").order_by("-version").first()
        if form:
            uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
            self.stdout.write("Form 4797: all rules cited" if not uncited
                              else self.style.WARNING(f"Form 4797 uncited rules: {len(uncited)}"))
