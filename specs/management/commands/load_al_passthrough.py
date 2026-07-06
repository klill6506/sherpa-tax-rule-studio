"""Load the AL pass-through entity specs — Form 65 (Partnership) + Form 20S (S-Corp) + Electing PTE (TY2025).
WO-13, the NC + AL pass-through batch (AL half). Completes the adjacent-state pass-through track.

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
Two AL pass-through returns in one loader (mirrors load_sc_passthrough.py):
  • AL_FORM_65 — Alabama Partnership/LLC Return of Income (federal 1065 start).
  • AL_FORM_20S — Alabama S-Corporation Return (federal 1120-S start).
THE HEADLINE: the Alabama Electing PTE tax (Act 2021-1). Unlike NC's 4.25%/deduction design, AL's is
5% and the owner-side is a REFUNDABLE CREDIT (Schedule EPT-C). The EPT tax is computed/paid on Form
EPT — the Form 65/20S Schedule K only REFERENCES it (Form 65 Sch K L23 / Form 20S Sch K L25). AL
CONFORMS to §168(k)/§179 (no depreciation add-back — the opposite of NC/SC/GA). Nonresident owners
are covered by the Form PTE-C composite (5%). Reuses the AL Form 20C conformity work.

Greenfield: no AL_FORM_65 / AL_FORM_20S at the 2026-07-05 gap-check.

═══════════════════════════════════════════════════════════════════════════
v1 SCOPE — LOCKED (Ken's Gate-1 walk 2026-07-05; DECISIONS D-15). See nc_al_passthrough_source_brief.md.
═══════════════════════════════════════════════════════════════════════════
COMPUTES (Q1 full + Q2 owner side): the Electing-PTE tax (5%, Form EPT) with the owner REFUNDABLE CREDIT;
the composite PTE-C (5%); single sales factor. AL conforms on depreciation (no add-back). Form 20S
non-electing entity taxes (LIFO/BIG/excess-passive, Line 32) = diagnostic + direct-entry (Q3).

requires_human_review WALK ITEMS (W4-W6):
W4. AL Electing PTE = 5% on AL taxable income (Form EPT); owner side = REFUNDABLE CREDIT (Sch EPT-C), NOT a
    deduction (contrast NC). Election = checkbox on Form 65/20S + Form EPT + >50% owner consent. CONFIRM.
W5. AL CONFORMS to §168(k)/§179 (no add-back; §179 flows from federal Sch K). Conformity item-by-item
    (§40-18-1.1), NOT blanket. Composite PTE-C = 5% on nonresidents' AL-source share. CONFIRM.
W6. Form 20S non-electing entity taxes (Line 32) = LIFO recapture §40-18-161 / built-in gains §40-18-174 /
    excess net passive income §40-18-175 — diagnostic + direct-entry (the federal S-corp-level taxes). BPT
    separate (Form PPT). Due Mar 15 (15th day of 3rd month), NOT the extra month. CONFIRM.

CARRIED [UNVERIFIED]: exact TY2025 Sch K line numbers (25f65instr/25f20sinstr when ALDOR posts; TY2024 rev
used); encode OBBBA conformity item-by-item. Re-verify at TY2026.

SAFETY GUARD — READY_TO_SEED stays False until Ken approves the review walk (W4-W6).
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

# FLIPPED 2026-07-05 — Ken APPROVED ("Approve — flip, seed, export"): W4 Electing PTE 5% +
# owner REFUNDABLE CREDIT, W5 AL conforms §168(k)/§179 + composite, W6 Form 20S Line 32 + BPT.
# Validated (scratchpad/validate_nc_al_pt.py, 47/0). Line-number [UNVERIFIED] noted for re-pull.
READY_TO_SEED = True

FORM_JURISDICTION = "AL"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"

# Verified constants (nc_al_passthrough_source_brief.md; 2025 ALDOR sources)
AL_PTET_RATE = "0.05"             # Electing PTE — 5% (top individual rate); Act 2021-1
AL_COMPOSITE_RATE = "0.05"       # PTE-C composite — 5% on nonresidents' AL-source share (§40-18-24.2)


def _al_ept(al_taxable_income) -> float:
    """AL Electing PTE tax = 5% of the entity's Alabama taxable income (Form EPT)."""
    return float(al_taxable_income) * float(AL_PTET_RATE)


def _al_composite(nonres_al_source) -> float:
    """AL PTE-C composite = 5% of nonresidents' AL-source share."""
    return float(nonres_al_source) * float(AL_COMPOSITE_RATE)


AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("al_passthrough_ept", "AL pass-through returns (Form 65 partnership / Form 20S S-corp) + the Electing PTE "
     "tax (Act 2021-1): 5% on AL taxable income (Form EPT), owner-side REFUNDABLE CREDIT, AL conforms to "
     "§168(k)/§179, PTE-C 5% composite, Form 20S LIFO/BIG/excess-passive."),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "AL_2025_PTE_RETURNS", "source_type": "state_form", "source_rank": "primary_official",
        "jurisdiction_code": "AL", "title": "2025 Alabama Form 65 (Partnership) + Form 20S (S-Corporation) Returns",
        "citation": "Alabama Form 65 / Form 20S (2025); Form EPT", "issuer": "Alabama Department of Revenue",
        "official_url": "https://www.revenue.alabama.gov/",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.3, "topics": ["al_passthrough_ept"],
        "excerpts": [{
            "excerpt_label": "Form 65 / 20S structure + Electing PTE + composite (2025 substance)",
            "excerpt_text": (
                "Form 65 starts from federal Form 1065 (lines 1-22 from the federal return); Form 20S from "
                "federal 1120-S (lines 1-21). §179 flows straight from federal (Form 65 Sch K L12 / Form 20S Sch "
                "K L11) — AL conforms, no bonus/§179 add-back (only the historical 2008 Stimulus-Act decoupling "
                "on Schedule A). Single sales factor (Schedule C, 'Alabama Sales divided by total Everywhere "
                "Sales', Act 2021-1, four decimals). Electing PTE: check the Electing-PTE box on the timely-filed "
                "Form 65/20S + file Form EPT (the old Form PTE-E/MAT method is superseded); the EPT tax is "
                "computed/paid on Form EPT and REFERENCED on Form 65 Sch K L23 / Form 20S Sch K L25; it is added "
                "back as a non-deductible state tax on Schedule A. Composite: Form PTE-C, 5% on nonresidents' "
                "AL-source share (§40-18-24.2). Form 20S Line 32 entity-level tax on a NON-electing S-corp = only "
                "LIFO recapture (§40-18-161), built-in gains (§40-18-174), excess net passive income "
                "(§40-18-175). Business Privilege Tax is separate (Form PPT). Due 15th day of 3rd month (Mar 15, 2026)."
            ),
            "summary_text": "Form 65 from 1065 / 20S from 1120-S; §179 conforms; single sales factor; Electing PTE = checkbox + Form EPT (5%, referenced on Sch K L23/L25); PTE-C 5%; 20S L32 = LIFO/BIG/excess-passive; due Mar 15.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "AL_ACT_2021_1", "source_type": "statute", "source_rank": "controlling",
        "jurisdiction_code": "AL", "title": "Alabama Electing Pass-Through Entity Tax (Act 2021-1; §40-18-160 et seq.)",
        "citation": "Act 2021-1 (HB170); Code of Ala. §40-18-160 et seq.; §40-18-24.2 (composite)", "issuer": "Alabama Legislature",
        "official_url": "https://www.revenue.alabama.gov/individual-corporate/electing-pass-through-entities/",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.3, "topics": ["al_passthrough_ept"],
        "excerpts": [{
            "excerpt_label": "Electing PTE — 5% + owner REFUNDABLE CREDIT (ALDOR verbatim)",
            "excerpt_text": (
                "ALDOR: 'the tax rate is 5 percent, applied to the calculated Alabama taxable income.' Base = AL "
                "taxable income per §40-18-24 (partnerships) / §40-18-161-162 (S corps), apportioned, using Sch K "
                "Alabama-column lines 1-17 (incl. guaranteed payments). OWNER SIDE: 'The owner ... shall be "
                "entitled to a REFUNDABLE CREDIT in an amount equal to its pro rata or distributive share of the "
                "Alabama income tax paid by the electing pass-through entity' (Schedule EPT-C) — a credit, NOT a "
                "deduction (contrast NC). Election is annual, made by checking the Electing-PTE box on the "
                "timely-filed Form 65/20S + filing Form EPT, and requires a vote/consent of owners holding >50% "
                "of the voting control."
            ),
            "summary_text": "Electing PTE 5% of AL taxable income (Form EPT); owner = REFUNDABLE CREDIT (Sch EPT-C), not a deduction; annual checkbox + Form EPT + >50% consent.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "AL_CODE_40_18", "source_type": "statute", "source_rank": "controlling",
        "jurisdiction_code": "AL", "title": "Code of Ala. §40-18-1.1 (rolling conformity) · §40-18-15(a) (bonus/§179 tied to federal)",
        "citation": "Code of Ala. §40-18-1.1; §40-18-15(a)(8),(a)(21)", "issuer": "Alabama Legislature",
        "official_url": "https://law.justia.com/codes/alabama/title-40/",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.2, "topics": ["al_passthrough_ept"],
        "excerpts": [{
            "excerpt_label": "AL conforms to §168(k)/§179 — item-by-item (ALDOR OBBBA summary, re-declared)",
            "excerpt_text": (
                "§40-18-1.1: the IRC is defined as in effect from time to time (rolling conformity). ALDOR OBBBA "
                "Executive Summary (11/10/2025): §168(k) 100% bonus 'Tied to Federal: Yes' (§40-18-15(a)(8)); "
                "§179 $2.5M/$4M 'Tied to Federal: Yes' (§40-18-15(a)(21)) — AL CONFORMS, no bonus/§179 add-back "
                "on Form 65/20S (opposite of GA/SC/NC). Conformity is ITEM-BY-ITEM: several OBBBA items are "
                "'Tied to Federal: No' (§224 tips, §225 overtime, enhanced §199A, §174 R&E). Do not encode a "
                "blanket AL-conformity rule."
            ),
            "summary_text": "§40-18-1.1 rolling conformity; §168(k)/§179 tied to federal (AL conforms, no add-back); item-by-item — not blanket.",
            "is_key_excerpt": True,
        }],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("AL_2025_PTE_RETURNS", "AL_FORM_65", "governs"), ("AL_ACT_2021_1", "AL_FORM_65", "governs"),
    ("AL_CODE_40_18", "AL_FORM_65", "governs"),
    ("AL_2025_PTE_RETURNS", "AL_FORM_20S", "governs"), ("AL_ACT_2021_1", "AL_FORM_20S", "governs"),
    ("AL_CODE_40_18", "AL_FORM_20S", "governs"),
]

_AL_FACTS = [
    {"fact_key": "federal_income", "label": "Federal income (Form 65: 1065 / Form 20S: 1120-S)", "data_type": "decimal", "required": False, "sort_order": 1},
    {"fact_key": "federal_section_179", "label": "Federal §179 deduction (flows through — AL conforms, no add-back)", "data_type": "decimal", "required": False, "sort_order": 2},
    {"fact_key": "al_taxable_income", "label": "Alabama taxable income of the PTE — Sch K AL column L1-17, apportioned (Electing-PTE base)", "data_type": "decimal", "required": False, "sort_order": 3},
    {"fact_key": "is_multistate", "label": "Multistate entity (apportion)? — if no, AL ratio = 100%", "data_type": "boolean", "required": False, "sort_order": 4},
    {"fact_key": "sales_al", "label": "Sales within Alabama (single sales factor numerator)", "data_type": "decimal", "required": False, "sort_order": 5},
    {"fact_key": "sales_everywhere", "label": "Sales everywhere (denominator)", "data_type": "decimal", "required": False, "sort_order": 6},
    {"fact_key": "is_electing_pte", "label": "Electing PTE election made? (checkbox on Form 65/20S + Form EPT, >50% consent)", "data_type": "boolean", "required": False, "sort_order": 7},
    {"fact_key": "nonresident_al_source_share", "label": "Nonresidents' AL-source share (PTE-C composite base)", "data_type": "decimal", "required": False, "sort_order": 8},
    {"fact_key": "composite_exempt", "label": "Nonresident composite relieved (PTE-R / Schedule NRC-Exempt QIP)?", "data_type": "boolean", "required": False, "sort_order": 9},
]

_AL_APPORT = {
    "rule_id": None, "title": "Single sales factor apportionment (Schedule C)", "rule_type": "calculation",
    "formula": "al_ratio = 1.0 if not is_multistate else round(sales_al / sales_everywhere, 4)",
    "inputs": ["is_multistate", "sales_al", "sales_everywhere"], "outputs": ["al_ratio"], "sort_order": 1,
    "description": "W5. Alabama Sales / Everywhere Sales (Act 2021-1, single sales factor, four decimals).",
}
_AL_EPT = {
    "rule_id": None, "title": "AL Electing PTE tax — 5% (Form EPT), owner REFUNDABLE CREDIT", "rule_type": "calculation",
    "formula": ("if is_electing_pte: ept_tax = al_taxable_income * 0.05 (Form EPT) ; "
                "owner_side = each owner takes a REFUNDABLE CREDIT for its share of ept_tax (Schedule EPT-C)"),
    "inputs": ["is_electing_pte", "al_taxable_income"], "outputs": ["ept_tax"], "sort_order": 2,
    "description": "W4. Act 2021-1. Electing PTE tax = 5% of the entity's Alabama taxable income, computed/paid on Form EPT (referenced on Form 65 Sch K L23 / Form 20S Sch K L25). Owner side = a REFUNDABLE CREDIT for the owner's share (Schedule EPT-C), NOT a deduction (contrast NC).",
}
_AL_COMPOSITE = {
    "rule_id": None, "title": "AL composite PTE-C — 5% on nonresidents", "rule_type": "calculation",
    "formula": "if not composite_exempt: composite_tax = nonresident_al_source_share * 0.05 (Form PTE-C)",
    "inputs": ["composite_exempt", "nonresident_al_source_share"], "outputs": ["composite_tax"], "sort_order": 3,
    "description": "W5. §40-18-24.2. The PTE files Form PTE-C and pays 5% on nonresidents' AL-source share, unless relieved (PTE-R) or the nonresident opts out (Schedule NRC-Exempt / QIP).",
}


def _al_rules(prefix, entity_taxes=False):
    rules = []
    for base, suffix in ((_AL_APPORT, "APPORT"), (_AL_EPT, "EPT"), (_AL_COMPOSITE, "COMPOSITE")):
        r = dict(base)
        r["rule_id"] = f"{prefix}-{suffix}"
        rules.append(r)
    if entity_taxes:
        rules.append({
            "rule_id": f"{prefix}-ENTITY", "title": "Form 20S non-electing entity taxes (Line 32)", "rule_type": "calculation",
            "formula": "entity_tax = lifo_recapture + builtin_gains + excess_net_passive  (direct-entry; the federal S-corp-level taxes)",
            "inputs": ["lifo_recapture", "builtin_gains", "excess_net_passive"], "outputs": ["entity_tax"], "sort_order": 4,
            "description": "W6. Form 20S Line 32: the only AL entity-level tax on a NON-electing S-corp = LIFO recapture (§40-18-161) + built-in gains (§40-18-174) + excess net passive income (§40-18-175). Direct-entry (these are the federal S-corp-level taxes, not recomputed).",
        })
    return rules


def _al_links(prefix, entity_taxes=False):
    links = [
        (f"{prefix}-APPORT", "AL_2025_PTE_RETURNS", "primary", "single sales factor (Act 2021-1)"),
        (f"{prefix}-EPT", "AL_ACT_2021_1", "primary", "Electing PTE 5% + owner refundable credit"),
        (f"{prefix}-EPT", "AL_2025_PTE_RETURNS", "secondary", "Form EPT referenced on Sch K"),
        (f"{prefix}-COMPOSITE", "AL_2025_PTE_RETURNS", "primary", "PTE-C composite 5%"),
    ]
    if entity_taxes:
        links.append((f"{prefix}-ENTITY", "AL_2025_PTE_RETURNS", "primary", "Form 20S Line 32 LIFO/BIG/excess-passive"))
    return links


_EPT_DIAG = lambda who: {
    "diagnostic_id": None, "title": "AL Electing PTE — 5%, owner REFUNDABLE CREDIT (not a deduction)", "severity": "info",
    "condition": "is_electing_pte",
    "message": f"An electing {who} pays the Alabama Electing PTE tax at 5% of the entity's Alabama taxable income, computed on Form EPT. Each owner then takes a REFUNDABLE CREDIT for their pro-rata share of the tax (Schedule EPT-C) — a credit, NOT a deduction (contrast North Carolina). The election is annual, made by checking the Electing-PTE box on the timely-filed return + filing Form EPT, and requires consent of owners holding more than 50% of the voting control.",
    "notes": "W4.",
}
_DEPR_DIAG = {
    "diagnostic_id": None, "title": "AL conforms to §168(k)/§179 — no depreciation add-back", "severity": "info",
    "condition": "always (informational)",
    "message": "Alabama conforms to federal §168(k) bonus depreciation and §179 (rolling conformity, §40-18-1.1; OBBBA flows through — §179 $2.5M/$4M). §179 flows straight from the federal return; there is NO bonus/§179 add-back (opposite of GA/SC/NC). Only the historical 2008 Economic Stimulus Act basis difference decouples. Note: AL conformity is ITEM-BY-ITEM — several other OBBBA items (tips/overtime/§199A/§174) are NOT tied to federal.",
    "notes": "W5.",
}
_COMPOSITE_DIAG = {
    "diagnostic_id": None, "title": "AL composite PTE-C — 5% on nonresidents", "severity": "info",
    "condition": "nonresident_al_source_share > 0 and not composite_exempt",
    "message": "The PTE files Form PTE-C and pays a 5% composite tax on nonresident owners' Alabama-source share (§40-18-24.2), unless relieved (Form PTE-R filed ≥30 days before the due date) or the nonresident opts out (Schedule NRC-Exempt / qualified investment partnership).",
    "notes": "W5.",
}


# ── AL_FORM_65 (partnership) ──
F65_FACTS = [dict(f) for f in _AL_FACTS]
F65_RULES = _al_rules("R-AL65")
F65_LINKS = _al_links("R-AL65")
F65_LINES = [
    {"line_number": "F65-EPT", "description": "Form 65 Sch K L23 Electing PTE tax (Form EPT, × 5%)", "line_type": "calculated", "source_rules": ["R-AL65-EPT"], "sort_order": 1},
    {"line_number": "F65-PTEC", "description": "Form 65 composite PTE-C (× 5%)", "line_type": "calculated", "source_rules": ["R-AL65-COMPOSITE"], "sort_order": 2},
    {"line_number": "F65-APPT", "description": "Form 65 Schedule C apportionment ratio", "line_type": "calculated", "source_rules": ["R-AL65-APPORT"], "sort_order": 3},
]
def _named(d, did):
    d = dict(d); d["diagnostic_id"] = did; return d
F65_DIAG = [
    _named(_EPT_DIAG("partnership"), "D_AL65_EPT"),
    _named(_DEPR_DIAG, "D_AL65_DEPR"),
    _named(_COMPOSITE_DIAG, "D_AL65_COMPOSITE"),
]
F65_SCEN = [
    {"scenario_name": "F65-A — Electing PTE 5%", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"is_electing_pte": True, "al_taxable_income": 1000000},
     "expected_outputs": {"ept_tax": 50000}, "notes": "1,000,000 x 5% = 50,000 (Form EPT). Owners take a refundable credit for their share (Sch EPT-C)."},
    {"scenario_name": "F65-B — composite PTE-C 5%", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"nonresident_al_source_share": 300000},
     "expected_outputs": {"composite_tax": 15000}, "notes": "300,000 AL-source x 5% = 15,000 (PTE-C)."},
    {"scenario_name": "F65-C — §179 conforms (no add-back)", "scenario_type": "edge", "sort_order": 3,
     "inputs": {"federal_section_179": 2000000},
     "expected_outputs": {"diagnostic": "D_AL65_DEPR"}, "notes": "AL conforms — federal §179 $2M flows through, no add-back (D_AL65_DEPR)."},
    {"scenario_name": "F65-D — multistate single sales factor", "scenario_type": "edge", "sort_order": 4,
     "inputs": {"is_multistate": True, "sales_al": 400000, "sales_everywhere": 1000000},
     "expected_outputs": {"al_ratio": 0.4}, "notes": "Ratio 400,000/1,000,000 = 0.4000."},
]

# ── AL_FORM_20S (S-corp) ──
F20S_FACTS = [dict(f) for f in _AL_FACTS] + [
    {"fact_key": "lifo_recapture", "label": "LIFO recapture tax (§40-18-161) — Form 20S L32 (direct-entry)", "data_type": "decimal", "required": False, "sort_order": 10},
    {"fact_key": "builtin_gains", "label": "Built-in gains tax (§40-18-174) — Form 20S L32 (direct-entry)", "data_type": "decimal", "required": False, "sort_order": 11},
    {"fact_key": "excess_net_passive", "label": "Excess net passive income tax (§40-18-175) — Form 20S L32 (direct-entry)", "data_type": "decimal", "required": False, "sort_order": 12},
]
F20S_RULES = _al_rules("R-AL20S", entity_taxes=True)
F20S_LINKS = _al_links("R-AL20S", entity_taxes=True)
F20S_LINES = [
    {"line_number": "F20S-EPT", "description": "Form 20S Sch K L25 Electing PTE tax (Form EPT, × 5%)", "line_type": "calculated", "source_rules": ["R-AL20S-EPT"], "sort_order": 1},
    {"line_number": "F20S-L32", "description": "Form 20S L32 entity taxes (LIFO/BIG/excess-passive)", "line_type": "calculated", "source_rules": ["R-AL20S-ENTITY"], "sort_order": 2},
    {"line_number": "F20S-PTEC", "description": "Form 20S composite PTE-C (× 5%)", "line_type": "calculated", "source_rules": ["R-AL20S-COMPOSITE"], "sort_order": 3},
]
F20S_DIAG = [
    _named(_EPT_DIAG("S corporation"), "D_AL20S_EPT"),
    {"diagnostic_id": "D_AL20S_ENTITY", "title": "AL 20S entity taxes (Line 32) — LIFO / built-in gains / excess passive", "severity": "info",
     "condition": "lifo_recapture > 0 or builtin_gains > 0 or excess_net_passive > 0",
     "message": "The only Alabama entity-level tax on a non-electing S-corporation (Form 20S Line 32) is the sum of the federal S-corp-level taxes: LIFO recapture (§40-18-161), built-in gains (§40-18-174), and excess net passive income (§40-18-175). Enter these directly (they are computed on the federal 1120-S). All other income passes through to shareholders.",
     "notes": "W6."},
    _named(_DEPR_DIAG, "D_AL20S_DEPR"),
    {"diagnostic_id": "D_AL20S_BPT", "title": "AL Business Privilege Tax is a separate return (Form PPT)", "severity": "info",
     "condition": "always (informational)",
     "message": "The Alabama Business Privilege Tax is a separate filing (Form PPT for pass-throughs) and is not computed on Form 20S. The minimum BPT for pass-throughs was repealed for tax years beginning on/after Jan 1, 2024. Do not compute the privilege tax here.",
     "notes": "W6."},
]
F20S_SCEN = [
    {"scenario_name": "F20S-A — Electing PTE 5%", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"is_electing_pte": True, "al_taxable_income": 800000},
     "expected_outputs": {"ept_tax": 40000}, "notes": "800,000 x 5% = 40,000 (Form EPT); shareholders take a refundable credit (Sch EPT-C)."},
    {"scenario_name": "F20S-B — Line 32 entity taxes (LIFO/BIG/excess-passive)", "scenario_type": "edge", "sort_order": 2,
     "inputs": {"lifo_recapture": 10000, "builtin_gains": 5000, "excess_net_passive": 3000},
     "expected_outputs": {"entity_tax": 18000}, "notes": "10,000 + 5,000 + 3,000 = 18,000 (Line 32). The only entity-level AL tax on a non-electing S-corp."},
    {"scenario_name": "F20S-C — composite PTE-C 5%", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"nonresident_al_source_share": 200000},
     "expected_outputs": {"composite_tax": 10000}, "notes": "200,000 x 5% = 10,000 (PTE-C)."},
    {"scenario_name": "F20S-D — §179 conforms (no add-back)", "scenario_type": "edge", "sort_order": 4,
     "inputs": {"federal_section_179": 1500000},
     "expected_outputs": {"diagnostic": "D_AL20S_DEPR"}, "notes": "AL conforms — federal §179 flows through, no add-back."},
]

FORMS: list[dict] = [
    {"identity": {"form_number": "AL_FORM_65", "entity_types": ["1065"],
                  "form_title": "Alabama Form 65 — Partnership/LLC Return of Income (TY2025)",
                  "notes": "WO-13 (DECISIONS D-15). AL partnership: federal 1065 start; AL conforms to §168(k)/§179 (no add-back); single sales factor (Act 2021-1); the Electing PTE tax (5% of AL taxable income on Form EPT, owner-side REFUNDABLE CREDIT via Sch EPT-C — NOT a deduction); composite PTE-C 5% on nonresidents. Due Mar 15."},
     "facts": F65_FACTS, "rules": F65_RULES, "rule_links": F65_LINKS, "lines": F65_LINES, "diagnostics": F65_DIAG, "scenarios": F65_SCEN},
    {"identity": {"form_number": "AL_FORM_20S", "entity_types": ["1120S"],
                  "form_title": "Alabama Form 20S — S Corporation Return (TY2025)",
                  "notes": "WO-13 (DECISIONS D-15). AL S-corp: federal 1120-S start; AL conforms to §168(k)/§179; single sales factor; the Electing PTE tax (5%, Form EPT, owner refundable credit); Line 32 non-electing entity taxes = LIFO recapture (§40-18-161) + built-in gains (§40-18-174) + excess net passive income (§40-18-175), direct-entry; composite PTE-C 5%; BPT separate (Form PPT). Due Mar 15."},
     "facts": F20S_FACTS, "rules": F20S_RULES, "rule_links": F20S_LINKS, "lines": F20S_LINES, "diagnostics": F20S_DIAG, "scenarios": F20S_SCEN},
]

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-AL65-EPT", "title": "AL Electing PTE tax = 5% of AL taxable income (owner credit)", "assertion_type": "reconciliation",
     "entity_types": ["1065"], "status": "draft", "sort_order": 1,
     "description": "Electing PTE tax (Form EPT) = AL taxable income × 5%; each owner takes a refundable credit for their share (Sch EPT-C).",
     "definition": {"rule": "R-AL65-EPT", "check": "ept_tax = al_taxable_income * 0.05"}},
    {"assertion_id": "FA-AL20S-ENTITY", "title": "AL 20S Line 32 = LIFO + built-in gains + excess passive", "assertion_type": "reconciliation",
     "entity_types": ["1120S"], "status": "draft", "sort_order": 2,
     "description": "The non-electing S-corp entity tax (Line 32) = LIFO recapture + built-in gains + excess net passive income.",
     "definition": {"rule": "R-AL20S-ENTITY", "check": "entity_tax = lifo + builtin_gains + excess_net_passive"}},
]


class Command(BaseCommand):
    help = "Load the AL pass-through specs (Form 65 + Form 20S + Electing PTE, TY2025). Refuses to seed until READY_TO_SEED=True (W4-W6)."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad AL pass-through specs (Form 65 + Form 20S + Electing PTE)\n"))
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
                "\nREFUSING TO SEED AL pass-through: not cleared.\n\n"
                "Gated until Ken reviews (W4 Electing PTE 5% + owner credit; W5 AL conforms +\n"
                f"composite; W6 Form 20S Line 32 + BPT) and flips the sentinel.\n\nREADY_TO_SEED = {READY_TO_SEED}\n\nEmpty:\n  {still}\n"
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
            defaults={"form_title": identity["form_title"], "entity_types": identity["entity_types"], "status": FORM_STATUS, "notes": identity["notes"]},
        )
        self.stdout.write(f"{'Created' if created else 'Updated'} {identity['form_number']} {identity['entity_types']}")
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
        for spec in FORMS:
            fn = spec["identity"]["form_number"]
            self.stdout.write(f"  {fn}: facts {len(spec['facts'])} / rules {len(spec['rules'])} / lines {len(spec['lines'])} / diag {len(spec['diagnostics'])} / tests {len(spec['scenarios'])}")
        self.stdout.write(f"  flow assertions: {len(FLOW_ASSERTIONS)}")
        self.stdout.write("=" * 60)
