"""Load the Form 709 spec — United States Gift (and GST) Tax Return (2025).
WO-21, 8th item in the SPINE S-16 federal-forms queue (the biggest module). Greenfield.

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
Form 709 reports (1) taxable GIFTS (gift tax) and (2) inter-vivos generation-skipping transfers (GST
tax); the donor files. The gift tax is UNIFIED + CUMULATIVE: tentative tax on ALL lifetime taxable
gifts (current + prior), minus tentative tax on prior gifts, so current gifts are taxed at the top
cumulative brackets (§2001(c), 40% top); the applicable (unified) credit shelters tax until cumulative
taxable gifts exceed the basic exclusion amount (BEA). Schedule A computes taxable gifts (annual
exclusion / marital / charitable); Schedule B is the prior-period cumulative base; Schedule C is DSUE
(portability); Schedule D is the GST tax.

★ 2025 applicable credit = $5,541,800 (tentative tax on the $13,990,000 BEA). OBBBA does NOT change
TY2025 (the permanent $15M BEA takes effect for gifts after 12/31/2025 — year-keyed here).

Greenfield: 709 not in the 117-form prod set at the 2026-07-06 gap-check.

═══════════════════════════════════════════════════════════════════════════
v1 SCOPE — LOCKED (Ken's Gate-1 walk 2026-07-06; DECISIONS D-23). See f709_source_brief.md.
═══════════════════════════════════════════════════════════════════════════
COMPUTES: (Q1) the §2001(c) tentative-tax schedule + the cumulative engine (Part 2 L3-L8) + the $5,541,800 credit ->
gift tax due. (Q2) Schedule A taxable gifts (annual exclusion $19,000/donee, gift-splitting $38,000, marital /
$190,000 noncitizen, charitable). (Q3) GST tax = 40% x inclusion ratio + DSUE -> Part 2 line 7. (Q4) year-keyed
constants + [UNVERIFIED] structural line-# flags + filing diagnostics. One `709` form.

requires_human_review WALK ITEMS (W1-W4):
W1. Cumulative engine: gift_tax = [tentative(current+prior) - tentative(prior)] - applicable_credit(limited).
    2025 credit $5,541,800 shelters until cumulative taxable gifts > $13,990,000 BEA. CONFIRM the $5,541,800.
W2. Schedule A: taxable gifts = gross - annual exclusions ($19,000/donee; $38,000 split) - marital (unlimited citizen
    / $190,000 noncitizen) - charitable. CONFIRM the 2025 exclusion + noncitizen figure.
W3. GST: 40% x inclusion ratio (1 - exemption/transfer), exemption = BEA $13,990,000; DSUE -> Sch C -> Part 2 L7.
W4. OBBBA does NOT change 2025 (BEA $13,990,000); the permanent $15M is 2026+. Year-key so $15M doesn't leak into 2025.

CARRIED [UNVERIFIED]: the raw f709.pdf face was unfetchable in research — all dollar figures + compute logic + Part 2
lines 1-8 are VERIFIED (i709 + statute), but the Part 1 (post-2025 restructure) / Schedule A reconciliation / Schedule
D sub-line NUMBERS are [UNVERIFIED]; re-verify the PDF face before the tts build (NC/AL line-# precedent, D-15). Also
the exact form "Created" date is [UNVERIFIED]. ALL figures INDEXED — re-verify each season; the OBBBA $15M BEA lands 2026.

SAFETY GUARD — READY_TO_SEED stays False until Ken approves the review walk (W1-W4).
FLIPPED 2026-07-06 — Ken APPROVED ("Approve — flip, seed, export"): W1 the cumulative engine + the
$5,541,800 applicable credit, W2 the Schedule A exclusions/deductions, W3 the GST 40%xinclusion-ratio +
DSUE, W4 the OBBBA $15M-2026 year-keying + the carried [UNVERIFIED] structural line-# flags (PDF face
unfetchable; re-verify before the tts build). Validated (scratchpad/validate_709.py, 32/0).
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from sources.models import (
    AuthorityExcerpt, AuthorityFormLink, AuthoritySource, AuthoritySourceTopic,
    AuthorityTopic, RuleAuthorityLink,
)
from specs.models import (
    FlowAssertion, FormDiagnostic, FormFact, FormLine, FormRule, TaxForm, TestScenario,
)

READY_TO_SEED = True

FORM_JURISDICTION = "federal"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["709"]  # its own gift-tax return, not a 1040 attachment

# ── Verified 2025 constants (f709_source_brief.md; 2025 i709 + §2001(c)). ALL INDEXED — re-verify each season. ──
ANNUAL_EXCLUSION = 19000               # §2503(b) per donee (2024: $18,000)
BEA = 13990000                         # §2010 basic exclusion amount / applicable exclusion (2024: $13,610,000)
APPLICABLE_CREDIT = 5541800            # tentative tax on the BEA = $345,800 + 40% x ($13,990,000 - $1,000,000) (2024: $5,389,800)
NONCITIZEN_SPOUSE_EXCLUSION = 190000   # §2523(i) annual exclusion for gifts to a noncitizen spouse (2024: $185,000)
GST_EXEMPTION = 13990000               # §2631 GST exemption = BEA
GST_RATE = "0.40"                      # §2641 maximum GST rate (= §2001(c) top rate)
# ★ OBBBA (P.L. 119-21 §70106): permanent $15,000,000 BEA for gifts AFTER 12/31/2025 (2026+), indexed. NOT for 2025.
BEA_2026_OBBBA = 15000000              # year-keyed guard — do NOT apply to 2025 (statutory 2026 floor; indexed figure TBD)

# §2001(c) rate schedule ("Table for Computing Gift Tax"); top collapsed to 40% over $1,000,000 (EGTRRA cap).
RATE_SCHEDULE: list[tuple[int, int, float]] = [
    (0, 0, 0.18), (10000, 1800, 0.20), (20000, 3800, 0.22), (40000, 8200, 0.24),
    (60000, 13000, 0.26), (80000, 18200, 0.28), (100000, 23800, 0.30), (150000, 38800, 0.32),
    (250000, 70800, 0.34), (500000, 155800, 0.37), (750000, 248300, 0.39), (1000000, 345800, 0.40),
]


def _tentative_tax(amount) -> float:
    """§2001(c) tentative tax: find the highest bracket whose 'over' <= amount; tax = tax_on_col_A + rate x excess."""
    amt = float(amount)
    if amt <= 0:
        return 0.0
    over, tax_at, rate = RATE_SCHEDULE[0]
    for lo, base, r in RATE_SCHEDULE:
        if amt > lo:
            over, tax_at, rate = lo, base, r
        else:
            break
    return round(tax_at + rate * (amt - over), 2)


def _taxable_gifts(total_gifts, annual_exclusions, marital_deduction, charitable_deduction) -> float:
    """Schedule A reconciliation: taxable gifts = total gifts - annual exclusions - marital - charitable, floored 0."""
    return round(max(0.0, float(total_gifts) - float(annual_exclusions) - float(marital_deduction) - float(charitable_deduction)), 2)


def _annual_exclusion(gift_value_per_donee, split) -> float:
    """Per-donee annual exclusion: $19,000 ($38,000 if gift-split with spouse under §2513), capped at the gift value."""
    cap = ANNUAL_EXCLUSION * (2 if split else 1)
    return round(min(float(gift_value_per_donee), cap), 2)


def _gift_tax_due(current_taxable, prior_taxable, dsue) -> float:
    """Part 2: L6 = tentative(current+prior) - tentative(prior); credit = $5,541,800 + DSUE, net of the portion
    used against prior gifts; gift tax = max(0, L6 - credit_this_period)."""
    l4 = _tentative_tax(float(current_taxable) + float(prior_taxable))
    l5 = _tentative_tax(prior_taxable)
    l6 = round(l4 - l5, 2)
    total_credit = APPLICABLE_CREDIT + float(dsue)
    prior_credit_used = min(l5, total_credit)
    credit_this = min(l6, max(0.0, total_credit - prior_credit_used))
    return round(max(0.0, l6 - credit_this), 2)


def _gst_tax(transfer, exemption_allocated) -> float:
    """Schedule D: inclusion ratio = 1 - min(1, exemption allocated / transfer); GST tax = transfer x (40% x inclusion ratio)."""
    t = float(transfer)
    if t <= 0:
        return 0.0
    inclusion_ratio = 1.0 - min(1.0, float(exemption_allocated) / t)
    return round(t * float(GST_RATE) * inclusion_ratio, 2)


AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("gift_gst_tax_709", "Form 709 gift + GST tax: unified cumulative gift-tax engine (§2001(c), top 40%), applicable "
     "credit $5,541,800 / BEA $13.99M (2025), annual exclusion $19,000/donee, gift-splitting, marital/charitable, "
     "DSUE, GST 40% x inclusion ratio."),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_F709", "source_type": "federal_form", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Form 709 (2025) — US Gift (and GST) Tax Return",
        "citation": "Form 709 (2025) — exact Created date [UNVERIFIED] (PDF face unfetchable); 2025 revision",
        "issuer": "Internal Revenue Service", "official_url": "https://www.irs.gov/pub/irs-pdf/f709.pdf",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.3, "topics": ["gift_gst_tax_709"],
        "excerpts": [{
            "excerpt_label": "Part 2 tax computation (lines 1-8, VERIFIED from i709; some sub-line #s [UNVERIFIED])",
            "excerpt_text": (
                "Part 2 Tax Computation: L1 amount from Schedule A (taxable gifts this period); L2 total taxable "
                "gifts for prior periods (from Schedule B); L3 = L1 + L2; L4 tentative tax on the amount on line 3 "
                "(Table for Computing Gift Tax); L5 tentative tax on the amount on line 2; L6 = L4 - L5; L7 "
                "applicable credit amount (2025 = $5,541,800; if DSUE and/or Restored Exclusion, from Schedule C "
                "line 5); L8 applicable credit allowable for all prior periods (Schedule B). Then the credit "
                "limitation, DSUE application, the total gift tax, the GST tax from Schedule D, and the balance "
                "due. NOTE: the 2025 form was restructured (Part I reorganized; former lines 12-18 moved to a new "
                "Part III); Schedule A reconciliation and Schedule D sub-line numbers are [UNVERIFIED] pending a "
                "raw-PDF-face check."
            ),
            "summary_text": "Part 2: L3 = L1(Sch A) + L2(Sch B prior); L4 = tentative(L3); L5 = tentative(L2); L6 = L4-L5; L7 applicable credit $5,541,800 (+DSUE from Sch C L5); L8 prior credit. -> gift tax + GST (Sch D).",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "Schedule A / B / C / D structure (VERIFIED labels; sub-line #s [UNVERIFIED])",
            "excerpt_text": (
                "Schedule A Computation of Taxable Gifts: Part 1 gifts subject only to gift tax; Part 2 direct "
                "skips (gift + GST); Part 3 indirect skips (§2632(c)). Reconciliation: total gifts - annual "
                "exclusions ($19,000/donee) - marital deduction (§2523) - charitable deduction (§2522) = taxable "
                "gifts -> Part 2 line 1. Schedule B Gifts From Prior Periods: prior-period taxable gifts + credit "
                "used (col (c) -> Part 2 line 8) — the cumulative base. Schedule C DSUE / Restored Exclusion: DSUE "
                "from predeceased spouse(s), line 5 -> Part 2 line 7. Schedule D GST Tax: allocate the GST exemption "
                "($13,990,000); GST tax = 40% (§2641 maximum rate) x inclusion ratio (1 - exemption allocated / "
                "transfer)."
            ),
            "summary_text": "Sch A: gross - annual excl - marital - charitable = taxable gifts. Sch B cumulative prior. Sch C DSUE -> Part 2 L7. Sch D GST = 40% x inclusion ratio, exemption = BEA.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "IRS_2025_I709", "source_type": "official_instructions", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "2025 Instructions for Form 709",
        "citation": "Instructions for Form 709 (2025), incl. What's New + Table for Computing Gift Tax", "issuer": "Internal Revenue Service",
        "official_url": "https://www.irs.gov/instructions/i709",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.5, "topics": ["gift_gst_tax_709"],
        "excerpts": [{
            "excerpt_label": "What's New + 2025 figures + who must file (i709 verbatim substance)",
            "excerpt_text": (
                "2025 figures: annual exclusion $19,000 per donee; basic exclusion amount $13,990,000; the basic "
                "credit amount for 2025 is $5,541,800; the annual exclusion for gifts to a noncitizen spouse is "
                "increased to $190,000; the GST exemption is $13,990,000. Who Must File: any donor who gave a "
                "person gifts totaling more than $19,000 (other than to a citizen spouse or qualified charity), any "
                "gift of a future interest (any amount), and spouses electing to split gifts — even if no tax is "
                "due after the applicable credit. Gift-splitting (§2513): spouses may consent to treat gifts to "
                "third parties as made one-half by each (both must sign). Marital deduction (§2523) unlimited for a "
                "U.S.-citizen spouse. Due April 15, 2026 (Form 8892 extends the filing deadline, not the payment). "
                "The unified rate schedule tops out at 40% over $1,000,000 ($345,800 + 40%)."
            ),
            "summary_text": "2025: annual excl $19,000; BEA $13,990,000; applicable credit $5,541,800; noncitizen-spouse $190,000; GST exemption $13,990,000. Must file if > $19,000/donee, future interest, or splitting. Due Apr 15.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "IRC_2001_2010", "source_type": "statute", "source_rank": "controlling",
        "jurisdiction_code": "US", "title": "IRC §2001(c)/§2010/§2503/§2523/§2631/§2641; OBBBA §70106 ($15M BEA 2026)",
        "citation": "26 U.S.C. §2001(c), §2010, §2503(b), §2523(i), §2631, §2641; P.L. 119-21 §70106", "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/2001",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.4, "topics": ["gift_gst_tax_709"],
        "excerpts": [{
            "excerpt_label": "§2001(c) schedule + unified/cumulative + OBBBA $15M 2026 (verbatim substance)",
            "excerpt_text": (
                "§2001(c): the unified rate schedule; over $1,000,000 the tax is $345,800 + 40% of the excess "
                "(EGTRRA capped the top rate at 40%). §2001(b): the gift/estate tax is computed on cumulative "
                "transfers, reduced by the tax attributable to prior taxable gifts. §2010/§2505: the applicable "
                "credit (unified credit) equals the tentative tax on the basic exclusion amount; §2503(b) annual "
                "exclusion (indexed, $19,000 for 2025); §2523(i) the noncitizen-spouse annual exclusion ($190,000 "
                "for 2025); §2631 GST exemption = BEA; §2641 maximum GST rate = the §2001(c) top rate (40%). OBBBA "
                "(P.L. 119-21) §70106 permanently sets the basic exclusion amount to $15,000,000 for gifts made "
                "and decedents dying AFTER December 31, 2025, indexed for inflation — this does NOT apply to 2025 "
                "(the 2025 BEA remains $13,990,000)."
            ),
            "summary_text": "§2001(c) 40% top over $1M ($345,800+40%); (b) cumulative; §2010 credit = tentative tax on BEA; §2503(b) $19,000; §2523(i) $190,000; §2631 GST exemption = BEA. OBBBA §70106: $15M BEA for 2026+, not 2025.",
            "is_key_excerpt": True,
        }],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_F709", "709", "governs"), ("IRS_2025_I709", "709", "governs"), ("IRC_2001_2010", "709", "governs"),
]


F709_FACTS: list[dict] = [
    # Schedule A — taxable gifts
    {"fact_key": "total_gifts", "label": "Total gifts this period (Schedule A, before exclusions/deductions)", "data_type": "decimal", "required": False, "sort_order": 1},
    {"fact_key": "annual_exclusions_total", "label": "Total annual exclusions ($19,000/donee; $38,000 if gift-split)", "data_type": "decimal", "required": False, "sort_order": 2},
    {"fact_key": "gift_splitting", "label": "Gift-splitting with spouse elected (§2513)? -> doubles the per-donee exclusion, both spouses sign", "data_type": "boolean", "required": False, "sort_order": 3},
    {"fact_key": "marital_deduction", "label": "Marital deduction (§2523) — unlimited to a U.S.-citizen spouse", "data_type": "decimal", "required": False, "sort_order": 4},
    {"fact_key": "noncitizen_spouse", "label": "Spouse is a noncitizen? -> no unlimited marital deduction; $190,000 annual exclusion instead (§2523(i))", "data_type": "boolean", "required": False, "sort_order": 5},
    {"fact_key": "charitable_deduction", "label": "Charitable deduction (§2522) — gifts to qualified charities", "data_type": "decimal", "required": False, "sort_order": 6},
    # Schedule B — prior periods
    {"fact_key": "prior_taxable_gifts", "label": "Total taxable gifts for prior periods (Schedule B) — the cumulative base", "data_type": "decimal", "required": False, "sort_order": 7},
    # Schedule C — DSUE
    {"fact_key": "dsue_amount", "label": "Deceased spousal unused exclusion (DSUE) / restored exclusion (Schedule C line 5)", "data_type": "decimal", "required": False, "sort_order": 8,
     "notes": "Increases the applicable credit at Part 2 line 7 (as tentative tax on the DSUE amount)."},
    # Schedule D — GST
    {"fact_key": "gst_transfer", "label": "Generation-skipping transfer value (Schedule D)", "data_type": "decimal", "required": False, "sort_order": 9},
    {"fact_key": "gst_exemption_allocated", "label": "GST exemption allocated to the transfer (Schedule D; total exemption $13,990,000)", "data_type": "decimal", "required": False, "sort_order": 10},
    # Filing
    {"fact_key": "has_future_interest", "label": "Any gift of a future interest? -> must file regardless of amount", "data_type": "boolean", "required": False, "sort_order": 11},
    {"fact_key": "gift_per_donee_max", "label": "Largest gift to any one donee (for the who-must-file $19,000 test)", "data_type": "decimal", "required": False, "sort_order": 12},
]

F709_RULES: list[dict] = [
    {"rule_id": "R-709-TENTATIVE", "title": "§2001(c) tentative-tax rate schedule (top 40%)", "rule_type": "calculation",
     "formula": "tentative_tax(x): find highest bracket 'over' <= x; tax = tax_on_col_A + rate*(x - over). Over $1,000,000: $345,800 + 40%",
     "inputs": [], "outputs": ["tentative_tax"], "sort_order": 1,
     "description": "W1. The unified rate schedule (§2001(c) 'Table for Computing Gift Tax'): 18% to 40%, with everything over $1,000,000 taxed at $345,800 + 40% of the excess. The tentative tax on the $13,990,000 BEA = $5,541,800 = the 2025 applicable credit."},
    {"rule_id": "R-709-SCHEDA", "title": "Schedule A — taxable gifts", "rule_type": "calculation",
     "formula": "taxable_gifts = max(0, total_gifts - annual_exclusions_total - marital_deduction - charitable_deduction)",
     "inputs": ["total_gifts", "annual_exclusions_total", "marital_deduction", "charitable_deduction"], "outputs": ["taxable_gifts"], "sort_order": 2,
     "description": "W2. Schedule A: taxable gifts = total gifts - annual exclusions ($19,000/donee; $38,000 if gift-split) - marital deduction (unlimited to a U.S.-citizen spouse; a noncitizen spouse gets the $190,000 annual exclusion instead) - charitable deduction. Flows to Part 2 line 1. [UNVERIFIED reconciliation line #s — re-verify PDF face.]"},
    {"rule_id": "R-709-CUMULATIVE", "title": "Part 2 cumulative computation (L3-L6)", "rule_type": "calculation",
     "formula": "L3 = taxable_gifts + prior_taxable_gifts ; L4 = tentative_tax(L3) ; L5 = tentative_tax(prior_taxable_gifts) ; L6 = L4 - L5",
     "inputs": ["prior_taxable_gifts"], "outputs": ["l4_tentative", "l6_current_tax"], "sort_order": 3,
     "description": "W1. Part 2: L3 = current taxable gifts + prior-period taxable gifts (Schedule B); L4 = tentative tax on L3; L5 = tentative tax on the prior gifts alone; L6 = L4 - L5 = the tax attributable to the current gifts (at the top cumulative brackets). This is the unified/cumulative mechanic (§2001(b))."},
    {"rule_id": "R-709-CREDIT", "title": "Applicable credit + gift tax due (L7/L8)", "rule_type": "calculation",
     "formula": "total_credit = 5541800 + tentative_tax(dsue) ; prior_credit_used = min(L5, total_credit) ; credit_this = min(L6, total_credit - prior_credit_used) ; gift_tax = max(0, L6 - credit_this)",
     "inputs": ["dsue_amount"], "outputs": ["gift_tax_due"], "sort_order": 4,
     "description": "W1. The 2025 applicable (unified) credit is $5,541,800 (tentative tax on the $13,990,000 BEA), increased by any DSUE (Schedule C line 5 -> Part 2 line 7). Net of the credit used against prior gifts, the remaining credit offsets the current tax (L6); gift tax due = L6 - credit applied. The credit fully shelters tax until cumulative taxable gifts exceed $13,990,000."},
    {"rule_id": "R-709-GST", "title": "Schedule D — GST tax (40% x inclusion ratio)", "rule_type": "calculation",
     "formula": "inclusion_ratio = 1 - min(1, gst_exemption_allocated / gst_transfer) ; gst_tax = gst_transfer * 0.40 * inclusion_ratio",
     "inputs": ["gst_transfer", "gst_exemption_allocated"], "outputs": ["gst_tax"], "sort_order": 5,
     "description": "W3. Schedule D: the GST tax = the taxable transfer x the applicable rate, where applicable rate = 40% (§2641 maximum) x the inclusion ratio (1 - GST exemption allocated / transfer). Allocating the full $13,990,000 GST exemption to a transfer drives the inclusion ratio to 0 (no GST tax). [UNVERIFIED Schedule D sub-line #s.]"},
    {"rule_id": "R-709-SPLIT", "title": "Gift-splitting doubles the annual exclusion (§2513)", "rule_type": "calculation",
     "formula": "per_donee_exclusion = min(gift_value, 19000 * (2 if gift_splitting else 1))  # $38,000 combined when split",
     "inputs": ["gift_splitting"], "outputs": ["annual_exclusion_per_donee"], "sort_order": 6,
     "description": "W2. §2513: married spouses may consent to treat each gift to a third party as made one-half by each, effectively doubling the per-donee annual exclusion to $38,000. Both spouses must sign the consent. Gift-splitting also splits the use of each spouse's lifetime exemption."},
]

F709_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-709-TENTATIVE", "IRC_2001_2010", "primary", "§2001(c) rate schedule"),
    ("R-709-TENTATIVE", "IRS_2025_I709", "secondary", "Table for Computing Gift Tax"),
    ("R-709-SCHEDA", "IRS_2025_F709", "primary", "Schedule A reconciliation"),
    ("R-709-SCHEDA", "IRC_2001_2010", "secondary", "§2503(b)/§2523/§2522"),
    ("R-709-CUMULATIVE", "IRS_2025_F709", "primary", "Part 2 L3-L6"),
    ("R-709-CUMULATIVE", "IRC_2001_2010", "primary", "§2001(b) cumulative"),
    ("R-709-CREDIT", "IRS_2025_I709", "primary", "applicable credit $5,541,800"),
    ("R-709-CREDIT", "IRC_2001_2010", "secondary", "§2010/§2505 unified credit"),
    ("R-709-GST", "IRS_2025_F709", "primary", "Schedule D GST"),
    ("R-709-GST", "IRC_2001_2010", "secondary", "§2631/§2641 GST exemption + rate"),
    ("R-709-SPLIT", "IRS_2025_I709", "primary", "§2513 gift-splitting"),
]

F709_LINES: list[dict] = [
    {"line_number": "SCHA_TG", "description": "Schedule A taxable gifts -> Part 2 line 1", "line_type": "subtotal", "source_rules": ["R-709-SCHEDA"], "sort_order": 1},
    {"line_number": "P2_L4", "description": "Tentative tax on cumulative gifts (L3)", "line_type": "calculated", "source_rules": ["R-709-CUMULATIVE"], "sort_order": 2},
    {"line_number": "P2_L6", "description": "Tax on current-period gifts (L4 - L5)", "line_type": "calculated", "source_rules": ["R-709-CUMULATIVE"], "sort_order": 3},
    {"line_number": "P2_TAX", "description": "Gift tax due after the applicable credit", "line_type": "calculated", "source_rules": ["R-709-CREDIT"], "sort_order": 4},
    {"line_number": "SCHD_GST", "description": "GST tax (Schedule D) = 40% x inclusion ratio", "line_type": "calculated", "source_rules": ["R-709-GST"], "sort_order": 5},
]

F709_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_709_MUSTFILE", "title": "Who must file Form 709", "severity": "info",
     "condition": "gift_per_donee_max > 19000 or has_future_interest or gift_splitting",
     "message": "You must file Form 709 if in 2025 you gave any one donee gifts totaling more than $19,000 (other than to a U.S.-citizen spouse or a qualified charity), you gave a gift of a future interest (any amount), or you and your spouse are electing to split gifts - even if the applicable credit eliminates any tax. Due April 15, 2026 (Form 8892 extends the filing deadline, not the payment).",
     "notes": "W2/W4."},
    {"diagnostic_id": "D_709_ANNUAL_EXCL", "title": "2025 annual exclusion is $19,000 per donee", "severity": "info",
     "condition": "total_gifts > 0",
     "message": "The 2025 gift-tax annual exclusion is $19,000 per donee (present-interest gifts only - a future interest does not qualify and must be reported regardless of amount). Gifts within the exclusion are not taxable and generally need not be reported (unless split).",
     "notes": "W2. Year-keyed 2025."},
    {"diagnostic_id": "D_709_SPLIT", "title": "Gift-splitting doubles the exclusion to $38,000 (§2513)", "severity": "info",
     "condition": "gift_splitting",
     "message": "By electing to split gifts (§2513), you and your spouse each treat gifts to third parties as made one-half by each - doubling the per-donee annual exclusion to $38,000 and splitting the use of each spouse's lifetime exemption. BOTH spouses must sign the consent, and generally both must file if either exceeds the exclusion.",
     "notes": "W2."},
    {"diagnostic_id": "D_709_MARITAL", "title": "Marital deduction: unlimited (citizen) vs $190,000 (noncitizen spouse)", "severity": "warning",
     "condition": "noncitizen_spouse",
     "message": "Gifts to a U.S.-citizen spouse qualify for the UNLIMITED marital deduction (§2523). But there is NO unlimited marital deduction for gifts to a NONCITIZEN spouse - instead a special annual exclusion of $190,000 (2025, §2523(i)) applies. Verify the spouse's citizenship before applying an unlimited marital deduction.",
     "notes": "W2. Year-keyed 2025."},
    {"diagnostic_id": "D_709_BEA", "title": "2025 applicable credit $5,541,800 / BEA $13.99M (OBBBA $15M is 2026)", "severity": "info",
     "condition": "taxable_gifts > 0 or prior_taxable_gifts > 0",
     "message": "The 2025 applicable (unified) credit is $5,541,800 - the tentative tax on the $13,990,000 basic exclusion amount - so no gift tax is due until cumulative lifetime taxable gifts exceed $13,990,000. OBBBA permanently raised the BEA to $15,000,000 for gifts made AFTER December 31, 2025 (2026 onward, indexed) - it does NOT apply to 2025.",
     "notes": "W1/W4. Year-keyed; OBBBA $15M lands 2026."},
    {"diagnostic_id": "D_709_GST", "title": "GST tax = 40% x inclusion ratio (Schedule D)", "severity": "info",
     "condition": "gst_transfer > 0",
     "message": "A generation-skipping transfer (a direct skip to a skip person) is subject to the GST tax = 40% (the §2641 maximum rate) x the inclusion ratio (1 - GST exemption allocated / transfer). The 2025 GST exemption is $13,990,000 (= the BEA). Allocating enough exemption to drive the inclusion ratio to 0 produces no GST tax. Direct skips are also reported in Schedule A Part 2.",
     "notes": "W3."},
    {"diagnostic_id": "D_709_DSUE", "title": "DSUE / portability increases the applicable credit", "severity": "info",
     "condition": "dsue_amount > 0",
     "message": "A deceased spousal unused exclusion (DSUE) amount elected on a predeceased spouse's estate return (portability) is computed on Schedule C and increases your applicable credit at Part 2 line 7 (as the tentative tax on the DSUE amount). This lets you shelter gifts above your own basic exclusion amount.",
     "notes": "W3."},
    {"diagnostic_id": "D_709_UNVERIFIED", "title": "Structural line numbers pending a raw-PDF-face re-verify", "severity": "warning",
     "condition": "total_gifts > 0",
     "message": "The 2025 Form 709 was restructured (Part I reorganized; former lines 12-18 moved to a new Part III). All 2025 DOLLAR figures and the compute logic (incl. Part 2 lines 1-8) are verified from the instructions + statute, but the Part 1 / Schedule A reconciliation / Schedule D SUB-LINE NUMBERS are [UNVERIFIED] (the raw f709.pdf face was unfetchable in research). Re-verify the exact line numbers against the PDF face before the tts app build.",
     "notes": "Provenance caveat — nothing guessed, only label positions flagged."},
]

F709_SCENARIOS: list[dict] = [
    {"scenario_name": "709-A — under the exclusion, no gift tax", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"total_gifts": 5019000, "annual_exclusions_total": 19000, "prior_taxable_gifts": 0},
     "expected_outputs": {"taxable_gifts": 5000000.0, "l6_current_tax": 1945800.0, "gift_tax_due": 0.0},
     "notes": "Taxable gifts 5,000,000; tentative tax = 345,800 + 40% x 4,000,000 = 1,945,800; applicable credit 5,541,800 fully shelters it -> $0 gift tax (but the return must be filed)."},
    {"scenario_name": "709-B — over the BEA, gift tax due", "scenario_type": "edge", "sort_order": 2,
     "inputs": {"total_gifts": 20019000, "annual_exclusions_total": 19000, "prior_taxable_gifts": 0},
     "expected_outputs": {"taxable_gifts": 20000000.0, "gift_tax_due": 2404000.0},
     "notes": "Taxable 20,000,000; tentative 7,945,800; credit 5,541,800 -> tax 2,404,000 (= (20M - 13.99M BEA) x 40%)."},
    {"scenario_name": "709-C — cumulative with prior gifts", "scenario_type": "edge", "sort_order": 3,
     "inputs": {"total_gifts": 5000000, "annual_exclusions_total": 0, "prior_taxable_gifts": 10000000},
     "expected_outputs": {"taxable_gifts": 5000000.0, "l6_current_tax": 2000000.0, "gift_tax_due": 404000.0},
     "notes": "L4 = tentative(15M) = 5,945,800; L5 = tentative(10M) = 3,945,800; L6 = 2,000,000; cumulative 15M - BEA 13.99M = 1.01M x 40% = 404,000."},
    {"scenario_name": "709-D — Schedule A reconciliation", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"total_gifts": 100000, "annual_exclusions_total": 38000, "marital_deduction": 0, "charitable_deduction": 0},
     "expected_outputs": {"taxable_gifts": 62000.0},
     "notes": "Gross 100,000 - annual exclusions 38,000 (two donees) = taxable gifts 62,000 -> Part 2 line 1."},
    {"scenario_name": "709-E — annual exclusion + gift-splitting", "scenario_type": "edge", "sort_order": 5,
     "inputs": {"total_gifts": 50000, "gift_splitting": True, "annual_exclusions_total": 38000},
     "expected_outputs": {"taxable_gifts": 12000.0, "diagnostic": "D_709_SPLIT"},
     "notes": "A $50,000 gift to one donee, split -> $38,000 combined exclusion -> $12,000 taxable (vs $31,000 if not split)."},
    {"scenario_name": "709-F — GST tax with partial exemption", "scenario_type": "edge", "sort_order": 6,
     "inputs": {"gst_transfer": 5000000, "gst_exemption_allocated": 3000000},
     "expected_outputs": {"gst_tax": 800000.0, "diagnostic": "D_709_GST"},
     "notes": "Inclusion ratio = 1 - 3,000,000/5,000,000 = 0.4; GST tax = 5,000,000 x 40% x 0.4 = 800,000. Full exemption allocation would give inclusion ratio 0 -> $0."},
]

FORMS: list[dict] = [
    {
        "identity": {"form_number": "709", "form_title": "Form 709 — United States Gift (and GST) Tax Return (2025)",
                     "notes": "WO-21 (SPINE S-16, 8th; DECISIONS D-23). Unified cumulative gift tax: §2001(c) rate schedule (top 40% over $1M = $345,800 + 40%); Part 2 L3 = current + prior taxable gifts, L4 = tentative(L3), L5 = tentative(prior), L6 = L4-L5; applicable credit $5,541,800 (= tentative tax on the $13,990,000 BEA, +DSUE Sch C) -> gift tax due (sheltered until cumulative taxable gifts > $13.99M). Schedule A: gross - annual exclusion ($19,000/donee; $38,000 split §2513) - marital (unlimited citizen / $190,000 noncitizen §2523(i)) - charitable = taxable gifts. Schedule D GST = 40% x inclusion ratio, exemption $13.99M. OBBBA $15M BEA is 2026+ (year-keyed, not 2025). entity_types [709]. ALL figures INDEXED. ⚠ [UNVERIFIED] Part 1/Sch A recon/Sch D sub-line #s (PDF face unfetchable) - re-verify before the tts build; Part 2 lines 1-8 verified."},
        "facts": F709_FACTS, "rules": F709_RULES, "rule_links": F709_RULE_LINKS,
        "lines": F709_LINES, "diagnostics": F709_DIAGNOSTICS, "scenarios": F709_SCENARIOS,
    },
]

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-709-CUMUL", "title": "Gift tax is cumulative: tentative(current+prior) - tentative(prior)", "assertion_type": "reconciliation",
     "entity_types": ["709"], "status": "draft", "sort_order": 1,
     "description": "Part 2 line 6 = tentative tax on cumulative taxable gifts (current + prior) minus tentative tax on prior gifts, taxing current gifts at the top cumulative brackets (§2001(b)).",
     "definition": {"rule": "R-709-CUMULATIVE", "check": "l6_current_tax = tentative(taxable_gifts + prior) - tentative(prior)"}},
    {"assertion_id": "FA-709-CREDIT", "title": "Applicable credit $5,541,800 shelters gifts up to the $13.99M BEA", "assertion_type": "reconciliation",
     "entity_types": ["709"], "status": "draft", "sort_order": 2,
     "description": "The 2025 applicable credit ($5,541,800 = tentative tax on the $13,990,000 BEA, + any DSUE) offsets the tax so no gift tax is due until cumulative taxable gifts exceed the BEA.",
     "definition": {"rule": "R-709-CREDIT", "check": "gift_tax_due = 0 while cumulative taxable gifts <= 13,990,000"}},
    {"assertion_id": "FA-709-GST", "title": "GST tax = 40% x inclusion ratio", "assertion_type": "reconciliation",
     "entity_types": ["709"], "status": "draft", "sort_order": 3,
     "description": "Schedule D GST tax = transfer x 40% x (1 - GST exemption allocated / transfer); full exemption allocation -> inclusion ratio 0 -> no GST tax.",
     "definition": {"rule": "R-709-GST", "check": "gst_tax = gst_transfer * 0.40 * (1 - min(1, exemption/transfer))"}},
]


class Command(BaseCommand):
    help = "Load the Form 709 spec (US Gift and GST Tax Return, 2025). Refuses to seed until READY_TO_SEED=True (W1-W4)."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad Form 709 spec (US Gift and GST Tax Return)\n"))
        self._load_topics()
        sources = self._load_sources()
        for spec in FORMS:
            form = self._upsert_form(spec["identity"])
            self._upsert_facts(form, spec["facts"])
            rules = self._upsert_rules(form, spec["rules"])
            self._upsert_links(rules, sources, spec["rule_links"])
            self._upsert_lines(form, spec["lines"])
            self._upsert_diag(form, spec["diagnostics"])
            self._upsert_tests(form, spec["scenarios"])
        self._upsert_form_links(sources)
        self._load_fa()
        self._report()

    def _guard(self):
        empty = []
        for spec in FORMS:
            fn = spec["identity"]["form_number"]
            for key in ("facts", "rules", "lines", "diagnostics", "scenarios", "rule_links"):
                if not spec[key]:
                    empty.append(f"{fn}.{key}")
        if not FLOW_ASSERTIONS:
            empty.append("FLOW_ASSERTIONS")
        if not READY_TO_SEED or empty:
            still = "\n  ".join(f"- {n}" for n in empty) or "(all populated)"
            raise CommandError(
                "\nREFUSING TO SEED FORM 709: not cleared.\n\n"
                "Gated until Ken reviews (W1 cumulative engine + $5,541,800 credit; W2 Schedule A\n"
                "exclusions; W3 GST + DSUE; W4 OBBBA year-keying + [UNVERIFIED] line #s) and flips\n"
                f"the sentinel.\n\nREADY_TO_SEED = {READY_TO_SEED}\n\nEmpty:\n  {still}\n"
            )

    def _load_topics(self):
        ct = 0
        for code, name in AUTHORITY_TOPICS:
            _, created = AuthorityTopic.objects.update_or_create(topic_code=code, defaults={"topic_name": name})
            ct += 1 if created else 0
        self.stdout.write(f"Topics: {ct} new")

    def _load_sources(self) -> dict:
        sources: dict = {}
        for sd in AUTHORITY_SOURCES:
            sd = dict(sd)
            exc = sd.pop("excerpts", [])
            tcs = sd.pop("topics", [])
            src, _ = AuthoritySource.objects.update_or_create(source_code=sd["source_code"], defaults=sd)
            sources[src.source_code] = src
            for e in exc:
                e = dict(e)
                AuthorityExcerpt.objects.update_or_create(authority_source=src, excerpt_label=e["excerpt_label"], defaults=e)
            for tc in tcs:
                t = AuthorityTopic.objects.filter(topic_code=tc).first()
                if t:
                    AuthoritySourceTopic.objects.get_or_create(authority_source=src, authority_topic=t)
        self.stdout.write(f"Sources ready: {len(sources)}")
        return sources

    def _upsert_form(self, identity: dict) -> TaxForm:
        form, created = TaxForm.objects.update_or_create(
            form_number=identity["form_number"], jurisdiction=FORM_JURISDICTION, tax_year=FORM_TAX_YEAR, version=FORM_VERSION,
            defaults={"form_title": identity["form_title"], "entity_types": FORM_ENTITY_TYPES, "status": FORM_STATUS, "notes": identity["notes"]},
        )
        self.stdout.write(f"{'Created' if created else 'Updated'} {identity['form_number']} {FORM_ENTITY_TYPES}")
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

    def _upsert_links(self, rules, sources, rule_links):
        ct = 0
        for rid, sc, lvl, note in rule_links:
            rule, src = rules.get(rid), sources.get(sc)
            if rule and src:
                RuleAuthorityLink.objects.get_or_create(form_rule=rule, authority_source=src, defaults={"support_level": lvl, "relevance_note": note})
                ct += 1
        self.stdout.write(f"  {ct} authority links")

    def _upsert_lines(self, form, lines):
        for ln in lines:
            ln = dict(ln)
            FormLine.objects.update_or_create(tax_form=form, line_number=ln.pop("line_number"), defaults=ln)
        self.stdout.write(f"  {len(lines)} lines")

    def _upsert_diag(self, form, diags):
        for d in diags:
            d = dict(d)
            FormDiagnostic.objects.update_or_create(tax_form=form, diagnostic_id=d.pop("diagnostic_id"), defaults=d)
        self.stdout.write(f"  {len(diags)} diagnostics")

    def _upsert_tests(self, form, scenarios):
        for t in scenarios:
            t = dict(t)
            TestScenario.objects.update_or_create(tax_form=form, scenario_name=t.pop("scenario_name"), defaults=t)
        self.stdout.write(f"  {len(scenarios)} test scenarios")

    def _upsert_form_links(self, sources):
        for sc, fc, lt in AUTHORITY_FORM_LINKS:
            src = sources.get(sc) or AuthoritySource.objects.filter(source_code=sc).first()
            if src:
                AuthorityFormLink.objects.get_or_create(authority_source=src, form_code=fc, link_type=lt, defaults={"note": f"{sc} -> {fc}"})

    def _load_fa(self):
        for a in FLOW_ASSERTIONS:
            a = dict(a)
            FlowAssertion.objects.update_or_create(assertion_id=a.pop("assertion_id"), defaults=a)
        self.stdout.write(f"  {len(FLOW_ASSERTIONS)} flow assertions")

    def _report(self):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("Form 709 loaded.")
        self.stdout.write(f"  709: facts {len(F709_FACTS)} / rules {len(F709_RULES)} / lines {len(F709_LINES)} / diag {len(F709_DIAGNOSTICS)} / tests {len(F709_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}")
        self.stdout.write("=" * 60)
