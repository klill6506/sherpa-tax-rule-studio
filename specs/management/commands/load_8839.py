"""Load the Form 8839 spec — Qualified Adoption Expenses (2025, Created 9/2/25).
WO-20, 7th item in the SPINE S-16 federal-forms queue (after 8990 + Schedule H + 4684 + 4952 + 8379 + 8814). Greenfield.

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
Form 8839 computes two things: (Part II) the §23 adoption CREDIT for qualified adoption expenses, and
(Part III) the §137 EXCLUSION for employer-provided adoption benefits. Both cap at $17,280/child (2025)
and share a MAGI phaseout ($259,190 -> $299,190 over $40,000).

★ THE 2025 HEADLINE (OBBBA, P.L. 119-21 §70402): the adoption credit is now PARTLY REFUNDABLE — up to
$5,000 per eligible child (new lines 11a/11b/11c -> line 13 -> Form 1040 line 30). The nonrefundable
remainder is tax-limited (-> Schedule 3 line 6c) and retains the 5-year carryforward; the refundable
portion is NOT carried forward, and a 2024 carryforward stays nonrefundable. §70403 added tribal-
government parity for special-needs determinations.

Greenfield: 8839 not in the 116-form prod set at the 2026-07-06 gap-check.

═══════════════════════════════════════════════════════════════════════════
v1 SCOPE — LOCKED (Ken's Gate-1 walk 2026-07-06; DECISIONS D-22). See f8839_source_brief.md.
═══════════════════════════════════════════════════════════════════════════
COMPUTES: (Q1) Part II L4-L18 — max/expenses (L6), MAGI phaseout, refundable split (L11b min $5,000 -> L13 -> 1040
L30), nonrefundable (+carryforward, tax-limited L17 -> Sch 3 6c). (Q2) Part III §137 exclusion + phaseout -> excluded
(L29) + taxable (L31 -> 1040 L1f). (Q3) special-needs full-credit override + §137/§23 / MFS / tribal-parity
diagnostics. (Q4) $5,000 refundable cap year-keyed (form=flat 2025, statute=indexing) + carryforward diagnostics.

requires_human_review WALK ITEMS (W1-W4):
W1. Part II: L6 = min($17,280-prior, expenses) (special needs -> full); phaseout fraction = (MAGI-$259,190)/$40,000;
    L11a = L6*(1-fraction); refundable L11b = min(L11a, $5,000) -> L13 -> 1040 L30. CONFIRM the refundable split.
W2. Nonrefundable: L14 = L12-L13; L16 = L14 + prior carryforward; L18 = min(L16, tax limit L17) -> Sch 3 6c; excess
    carries forward 5 yrs (refundable not carried; 2024 carryforward stays nonrefundable). CONFIRM.
W3. Part III: L24 = min($17,280-prior, benefits) (special needs -> full); phaseout; L29 excluded; L31 taxable -> 1040 L1f.
W4. Special-needs full $17,280 regardless of expenses; can't claim credit + exclusion for same expenses; MFS must
    file jointly (exception living apart); OBBBA §70403 tribal parity. CONFIRM the constants.

CARRIED [UNVERIFIED]: none from the form. ⚠ The $5,000 refundable-cap INDEXING is statutory (§36C/OBBBA §70402;
2026 = $5,120) but NOT stated in i8839 — cite the statute for indexing, the form for the flat 2025 $5,000. ALL
figures INDEXED — re-verify each season ($17,280 / $259,190 / $40,000 / $5,000).

SAFETY GUARD — READY_TO_SEED stays False until Ken approves the review walk (W1-W4).
FLIPPED 2026-07-06 — Ken APPROVED ("Approve — flip, seed, export"): W1 the credit base + MAGI phaseout
+ the OBBBA $5,000 refundable split, W2 the nonrefundable + tax-limit + 5-yr carryforward, W3 the Part III
§137 exclusion, W4 special-needs override + coordination + the $5,000-cap indexing provenance. Validated
(scratchpad/validate_8839.py, 30/0).
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
FORM_ENTITY_TYPES = ["1040"]

# ── Verified 2025 constants (f8839_source_brief.md; Form 8839 2025 Created 9/2/25 / i8839). ALL INDEXED — re-verify each season. ──
MAX_CREDIT = 17280             # L2 / L19 — max credit / exclusion per child (2024: $16,810)
PHASEOUT_START = 259190        # L8 / L26 — MAGI phaseout begins above this (2024: $252,150)
PHASEOUT_DIVISOR = 40000       # L9 / L27 — phaseout range
PHASEOUT_FULL = 299190         # fully phased out at $259,190 + $40,000
# ★ OBBBA 2025: up to $5,000 of the credit is refundable per child (L11b). Statute (§36C/OBBBA §70402) INDEXES it
# (2026 = $5,120) — the i8839 does NOT state the indexing. Flat 2025 figure = the form; indexing = the statute.
REFUNDABLE_CAP = 5000          # L11b — refundable portion cap per eligible child (2025)
CARRYFORWARD_YEARS = 5         # nonrefundable credit carryforward (refundable portion is NOT carried)


def _phaseout_fraction(magi) -> float:
    """MAGI phaseout fraction: (MAGI - $259,190) / $40,000, floored at 0, capped at 1.000 (form L9/L27)."""
    if float(magi) <= PHASEOUT_START:
        return 0.0
    return min(1.0, round((float(magi) - PHASEOUT_START) / PHASEOUT_DIVISOR, 3))


def _line6_credit_base(prior_year_expenses, qualified_expenses, is_special_needs) -> float:
    """L6 = smaller of (L4 = $17,280 - prior) or L5 qualified expenses. Special-needs U.S. child finalized
    in 2025 -> the full L4 amount regardless of expenses."""
    l4 = max(0.0, MAX_CREDIT - float(prior_year_expenses))
    if is_special_needs:
        return round(l4, 2)
    return round(min(l4, float(qualified_expenses)), 2)


def _credit_after_phaseout(base, magi) -> float:
    """L11a = L6 - L10 = L6 x (1 - phaseout fraction)."""
    return round(float(base) * (1.0 - _phaseout_fraction(magi)), 2)


def _refundable(l11a) -> float:
    """L11b = smaller of L11a or $5,000 (per eligible child) -> L13 -> Form 1040 line 30."""
    return round(min(float(l11a), float(REFUNDABLE_CAP)), 2)


def _nonrefundable(l12, l13, prior_carryforward, tax_limit) -> float:
    """L18 = min(L16, L17) where L16 = (L12 - L13) + prior carryforward; L17 = tax-liability limit -> Sch 3 6c."""
    l16 = max(0.0, float(l12) - float(l13)) + float(prior_carryforward)
    return round(min(l16, float(tax_limit)), 2)


def _exclusion_after_phaseout(l24, magi) -> float:
    """Part III L29 = L24 - L28 = L24 x (1 - phaseout fraction) (excluded employer benefits)."""
    return round(float(l24) * (1.0 - _phaseout_fraction(magi)), 2)


AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("adoption_expenses_8839", "Form 8839 qualified adoption expenses: §23 credit (max $17,280/child, MAGI phaseout "
     "$259,190-$299,190, OBBBA 2025 up to $5,000 REFUNDABLE + 5-yr nonrefundable carryforward) + §137 employer-"
     "benefit exclusion; special-needs full credit."),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_F8839", "source_type": "federal_form", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Form 8839 (2025) — Qualified Adoption Expenses",
        "citation": "Form 8839 (2025), Cat. No. 22843L, Created 9/2/25, Attach. Seq. No. 38",
        "issuer": "Internal Revenue Service", "official_url": "https://www.irs.gov/pub/irs-pdf/f8839.pdf",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.6, "topics": ["adoption_expenses_8839"],
        "excerpts": [{
            "excerpt_label": "Part II credit + refundable split (2025 verbatim)",
            "excerpt_text": (
                "Part II Adoption Credit: L2 maximum adoption credit per child, enter $17,280; L3 prior-year 8839 "
                "for same child; L4 = L2 - L3; L5 qualified adoption expenses; L6 smaller of L4 or L5; L7 modified "
                "AGI; L8 'Is line 7 more than $259,190? No - skip 8-9, enter -0- on line 10. Yes - subtract "
                "$259,190 from line 7'; L9 'Divide line 8 by $40,000' (decimal, at least 3 places, not more than "
                "1.000); L10 multiply L6 by L9; L11a subtract L10 from L6; L11b 'Enter the smaller of the amount on "
                "line 11a or $5,000'; L11c add L11b; L12 add L11a; L13 'Refundable adoption credit' = L11c, also on "
                "Form 1040 line 30; L14 = L12 - L13; L15 credit carryforward from prior years; L16 = L14 + L15; L17 "
                "amount from the Credit Limit Worksheet; L18 'Nonrefundable adoption credit' = smaller of L16 or "
                "L17, also on Schedule 3 line 6c."
            ),
            "summary_text": "Part II: L6 = min($17,280-prior, expenses); phaseout L8-10; L11a after phaseout; L11b min($5,000) refundable -> L13 -> 1040 L30; L18 = min(L16, tax limit) nonrefundable -> Sch 3 6c.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "What's New (OBBBA refundable + tribal parity) + Part III exclusion (2025 verbatim)",
            "excerpt_text": (
                "What's New: 'Up to $5,000 of adoption credit is refundable... The amount of the refundable credit "
                "portion is determined separately for each eligible child.' 'Parity for Indian tribal governments... "
                "state governments and Indian tribal government determinations of special needs are both recognized.' "
                "Line 13: 'Beginning in 2025, up to $5,000 of the adoption credit is refundable.' Part III Employer-"
                "Provided Adoption Benefits: L19 maximum exclusion $17,280; L20 prior-year benefits; L21 = L19 - "
                "L20; L22 employer benefits (W-2 box 12 code T); L23 add L22; L24 smaller of L21 or L22, but if "
                "special-needs child finalized in 2025 enter L21; L25 MAGI; L26 subtract $259,190; L27 divide by "
                "$40,000; L28 = L24 x L27; L29 excluded = L24 - L28; L30 add L29; L31 taxable = L23 - L30 (to Form "
                "1040 line 1f; negative if L30 > L23). Special needs: full credit even if you didn't pay any "
                "qualified adoption expenses. 'You can't claim both a credit and exclusion for the same expenses.'"
            ),
            "summary_text": "OBBBA: $5,000 refundable/child + tribal parity. Part III §137 exclusion: L24 min(max, benefits), phaseout, L29 excluded, L31 taxable -> 1040 L1f. Special-needs full credit. No double-dip.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "IRS_2025_I8839", "source_type": "official_instructions", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "2025 Instructions for Form 8839",
        "citation": "Instructions for Form 8839 (2025), reviewed 30-Apr-2026", "issuer": "Internal Revenue Service",
        "official_url": "https://www.irs.gov/instructions/i8839",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.5, "topics": ["adoption_expenses_8839"],
        "excerpts": [{
            "excerpt_label": "Carryforward + MFS + double-dip (i8839 verbatim substance)",
            "excerpt_text": (
                "Purpose of Form: 'Use Form 8839 to figure your adoption credit and any employer-provided adoption "
                "benefits you can exclude from your income... you can't claim both a credit and exclusion for the "
                "same expenses.' 'Any amount of the carryforward credit from 2024 remains a nonrefundable credit.' "
                "Line 18: 'you may have an unused nonrefundable credit to carry forward to the next 5 years or until "
                "used, whichever comes first.' Married Persons Not Filing Jointly: 'if you are married, you must "
                "file a joint return to take the credit or exclusion' unless legally separated or living apart "
                "meeting certain requirements. Special-needs: 'you may be able to take the credit even if you didn't "
                "pay any qualified adoption expenses' for a U.S. child with special needs whose adoption became "
                "final in 2025. The refundable portion (line 13) is not carried forward."
            ),
            "summary_text": "Can't double-dip credit + exclusion for same expenses. 5-yr carryforward of the nonrefundable credit only; refundable not carried; 2024 carryforward stays nonrefundable. MFS must file jointly (exception living apart). Special-needs full credit.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "IRC_23_137", "source_type": "statute", "source_rank": "controlling",
        "jurisdiction_code": "US", "title": "IRC §23/§36C (adoption credit + refundable) + §137 (employer exclusion); OBBBA §70402/§70403",
        "citation": "26 U.S.C. §23, §36C, §137; P.L. 119-21 §70402, §70403", "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/23",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.3, "topics": ["adoption_expenses_8839"],
        "excerpts": [{
            "excerpt_label": "§23/§36C refundable + indexing + §137 (verbatim substance; indexing NOT in i8839)",
            "excerpt_text": (
                "§23: nonrefundable credit for qualified adoption expenses, per-child dollar limit and MAGI "
                "phaseout, both inflation-indexed; unused credit carries forward 5 years. §137: exclusion from "
                "gross income for employer-provided adoption assistance, same dollar limit and phaseout. OBBBA "
                "(P.L. 119-21) §70402: for tax years beginning after Dec. 31, 2024, up to $5,000 of the adoption "
                "credit is REFUNDABLE (new §36C mechanics), and the $5,000 refundable cap is INFLATION-INDEXED "
                "(2026 = $5,120) — NOTE this indexing is statutory and is NOT stated in the 2025 Form 8839 "
                "instructions. §70403: parity for Indian tribal governments in determining special-needs status. "
                "You cannot claim both the §23 credit and the §137 exclusion for the same expenses."
            ),
            "summary_text": "§23 credit + §137 exclusion (indexed, 5-yr carryforward). OBBBA §70402: $5,000 refundable (post-2024), indexed ($5,120 for 2026, per statute not i8839). §70403 tribal parity. No double-dip.",
            "is_key_excerpt": True,
        }],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_F8839", "8839", "governs"), ("IRS_2025_I8839", "8839", "governs"), ("IRC_23_137", "8839", "governs"),
]


F8839_FACTS: list[dict] = [
    # Part II — credit
    {"fact_key": "qualified_adoption_expenses", "label": "Qualified adoption expenses for the child (L5) — net of employer-reimbursed amounts", "data_type": "decimal", "required": False, "sort_order": 1},
    {"fact_key": "prior_year_expenses_same_child", "label": "Adoption credit already claimed for this child in a prior year (L3)", "data_type": "decimal", "required": False, "sort_order": 2},
    {"fact_key": "is_special_needs", "label": "U.S. child with special needs whose adoption became final in 2025? -> full credit regardless of expenses", "data_type": "boolean", "required": False, "sort_order": 3,
     "notes": "OBBBA §70403: state AND Indian tribal government special-needs determinations both recognized."},
    {"fact_key": "magi", "label": "Modified adjusted gross income (L7/L25) — for the phaseout", "data_type": "decimal", "required": False, "sort_order": 4},
    {"fact_key": "prior_carryforward", "label": "Adoption credit carryforward from prior years (L15) — nonrefundable", "data_type": "decimal", "required": False, "sort_order": 5},
    {"fact_key": "tax_liability_limit", "label": "Tax-liability limit from the Credit Limit Worksheet (L17)", "data_type": "decimal", "required": False, "sort_order": 6,
     "notes": "Direct-entry — needs the full 1040 tax picture (line 18 tax minus certain other credits)."},
    # Part III — exclusion
    {"fact_key": "employer_benefits", "label": "Employer-provided adoption benefits received in 2025 (L22; W-2 box 12 code T)", "data_type": "decimal", "required": False, "sort_order": 7},
    {"fact_key": "prior_year_benefits_same_child", "label": "Employer benefits excluded for this child in a prior year (L20)", "data_type": "decimal", "required": False, "sort_order": 8},
    # Filing
    {"fact_key": "mfs_not_qualified", "label": "Married filing separately AND not living apart / legally separated? -> generally cannot claim", "data_type": "boolean", "required": False, "sort_order": 9},
]

F8839_RULES: list[dict] = [
    {"rule_id": "R-8839-CREDIT", "title": "Part II credit base + MAGI phaseout (L6/L11a)", "rule_type": "calculation",
     "formula": "L4 = 17280 - prior_year_expenses_same_child ; L6 = L4 if is_special_needs else min(L4, qualified_adoption_expenses) ; fraction = min(1, max(0, (magi - 259190)/40000)) ; L11a = L6 * (1 - fraction)",
     "inputs": ["qualified_adoption_expenses", "prior_year_expenses_same_child", "is_special_needs", "magi"], "outputs": ["l6_base", "l11a_after_phaseout"], "sort_order": 1,
     "description": "W1. Part II: L6 = smaller of ($17,280 max less prior-year) or qualified expenses (special-needs U.S. child finalized 2025 -> the full amount regardless of expenses). MAGI phaseout: fraction = (MAGI - $259,190) / $40,000 (0 below $259,190, 1.000 at/above $299,190); L11a = L6 x (1 - fraction)."},
    {"rule_id": "R-8839-REFUND", "title": "Refundable portion — up to $5,000/child (OBBBA 2025) (L11b/L13)", "rule_type": "calculation",
     "formula": "L11b = min(L11a, 5000) ; L13 = sum(L11b) -> Form 1040 line 30 (refundable)",
     "inputs": [], "outputs": ["l13_refundable"], "sort_order": 2,
     "description": "W1. NEW for 2025 (OBBBA §70402): up to $5,000 of the adoption credit is REFUNDABLE per eligible child. L11b = min(L11a, $5,000); L11c/L13 = the total, carried to Form 1040 line 30 as a refundable credit. The $5,000 cap is statutorily indexed ($5,120 for 2026) though the 2025 i8839 doesn't state it."},
    {"rule_id": "R-8839-NONREFUND", "title": "Nonrefundable portion + tax limit + 5-yr carryforward (L14-L18)", "rule_type": "calculation",
     "formula": "L14 = L12 - L13 ; L16 = L14 + prior_carryforward ; L18 = min(L16, tax_liability_limit) -> Schedule 3 line 6c ; carryforward = max(0, L16 - L17) (5 years)",
     "inputs": ["prior_carryforward", "tax_liability_limit"], "outputs": ["l18_nonrefundable", "carryforward_next"], "sort_order": 3,
     "description": "W2. Nonrefundable: L14 = L12 (total credit) - L13 (refundable); L16 = L14 + prior-year carryforward (L15); L18 = min(L16, the Credit Limit Worksheet tax limit L17) -> Schedule 3 line 6c. Any excess (L16 - L17) carries forward up to 5 years. The refundable portion is NOT carried forward; a 2024 carryforward remains nonrefundable."},
    {"rule_id": "R-8839-EXCLUDE", "title": "Part III §137 employer-benefit exclusion + taxable remainder (L24-L31)", "rule_type": "calculation",
     "formula": "L24 = (17280 - prior_year_benefits) if is_special_needs else min(17280 - prior_year_benefits, employer_benefits) ; fraction = (magi-259190)/40000 ; L29 = L24 * (1 - fraction) ; L31 = employer_benefits - L29 -> Form 1040 line 1f",
     "inputs": ["employer_benefits", "prior_year_benefits_same_child", "is_special_needs", "magi"], "outputs": ["l29_excluded", "l31_taxable"], "sort_order": 4,
     "description": "W3. Part III: L24 = smaller of ($17,280 max less prior) or employer benefits (special-needs -> full L21); same MAGI phaseout; L29 excluded = L24 x (1 - fraction); L31 taxable = employer benefits (L23) - excluded (L30) -> Form 1040 line 1f (negative if excluded > received). You can't exclude AND credit the same expenses."},
    {"rule_id": "R-8839-PHASEOUT", "title": "MAGI phaseout fraction (shared, L9/L27)", "rule_type": "calculation",
     "formula": "fraction = 0 if magi <= 259190 else min(1.000, round((magi - 259190) / 40000, 3))",
     "inputs": ["magi"], "outputs": ["phaseout_fraction"], "sort_order": 5,
     "description": "W1/W3. The shared MAGI phaseout used by both the credit (L8-L9) and the exclusion (L26-L27): fraction = (MAGI - $259,190) / $40,000, floored at 0 and capped at 1.000. Fully phased out at MAGI >= $299,190."},
]

F8839_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-8839-CREDIT", "IRS_2025_F8839", "primary", "Part II L2-L11a"),
    ("R-8839-CREDIT", "IRC_23_137", "secondary", "§23 credit + phaseout"),
    ("R-8839-REFUND", "IRS_2025_F8839", "primary", "L11b/L13 refundable -> 1040 L30"),
    ("R-8839-REFUND", "IRC_23_137", "primary", "§36C / OBBBA §70402 refundable"),
    ("R-8839-NONREFUND", "IRS_2025_F8839", "primary", "L14-L18 -> Sch 3 6c + 5-yr carryforward"),
    ("R-8839-EXCLUDE", "IRS_2025_F8839", "primary", "Part III L19-L31"),
    ("R-8839-EXCLUDE", "IRC_23_137", "secondary", "§137 employer exclusion"),
    ("R-8839-PHASEOUT", "IRS_2025_F8839", "primary", "L8-L9 / L26-L27 phaseout"),
]

F8839_LINES: list[dict] = [
    {"line_number": "L6", "description": "Credit base — smaller of $17,280-max or expenses (special needs = full)", "line_type": "calculated", "source_rules": ["R-8839-CREDIT"], "sort_order": 1},
    {"line_number": "L11a", "description": "Adoption credit after MAGI phaseout", "line_type": "calculated", "source_rules": ["R-8839-CREDIT"], "sort_order": 2},
    {"line_number": "L13", "description": "Refundable adoption credit (up to $5,000/child) -> Form 1040 line 30", "line_type": "calculated", "source_rules": ["R-8839-REFUND"], "sort_order": 3},
    {"line_number": "L18", "description": "Nonrefundable adoption credit -> Schedule 3 line 6c (5-yr carryforward)", "line_type": "calculated", "source_rules": ["R-8839-NONREFUND"], "sort_order": 4},
    {"line_number": "L29", "description": "Excluded employer-provided adoption benefits", "line_type": "calculated", "source_rules": ["R-8839-EXCLUDE"], "sort_order": 5},
    {"line_number": "L31", "description": "Taxable employer benefits -> Form 1040 line 1f", "line_type": "calculated", "source_rules": ["R-8839-EXCLUDE"], "sort_order": 6},
]

F8839_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_8839_REFUND", "title": "NEW 2025 — up to $5,000 of the adoption credit is refundable", "severity": "info",
     "condition": "l11a_after_phaseout > 0",
     "message": "Beginning in 2025 (OBBBA), up to $5,000 of the adoption credit is REFUNDABLE per eligible child - the first year this credit is partly refundable. The refundable portion (line 11b = smaller of line 11a or $5,000, totaled on line 13) goes to Form 1040 line 30 and is paid even if it exceeds your tax. The nonrefundable remainder is limited to your tax (Schedule 3 line 6c).",
     "notes": "W1. §36C / OBBBA §70402."},
    {"diagnostic_id": "D_8839_PHASEOUT", "title": "MAGI phaseout $259,190 -> $299,190", "severity": "warning",
     "condition": "magi > 259190",
     "message": "The adoption credit and the employer-benefit exclusion phase out for modified AGI over $259,190 and are fully phased out at $299,190 (2025). The reduction fraction = (MAGI - $259,190) / $40,000. Both the credit (lines 7-10) and the exclusion (lines 25-28) use this fraction.",
     "notes": "W1/W3. Year-keyed 2025."},
    {"diagnostic_id": "D_8839_SPECIALNEEDS", "title": "Special-needs child — full $17,280 regardless of expenses", "severity": "info",
     "condition": "is_special_needs",
     "message": "For a U.S. child with special needs whose adoption became final in 2025, you may claim the FULL $17,280 credit (and exclusion) even if you paid fewer or no qualified adoption expenses. OBBBA (§70403) added parity so that BOTH state and Indian tribal government determinations of special needs are recognized.",
     "notes": "W4."},
    {"diagnostic_id": "D_8839_BOTH", "title": "Can't claim both the credit and the exclusion for the same expenses", "severity": "warning",
     "condition": "qualified_adoption_expenses > 0 and employer_benefits > 0",
     "message": "You may claim both the §23 credit AND the §137 employer-benefit exclusion, but NOT for the same expenses. Reduce the qualified adoption expenses used for the credit (line 5) by any employer-reimbursed amounts you exclude in Part III. Double-counting the same dollars is not allowed.",
     "notes": "W4."},
    {"diagnostic_id": "D_8839_MFS", "title": "Married taxpayers generally must file jointly", "severity": "warning",
     "condition": "mfs_not_qualified",
     "message": "If you are married, you generally must file a joint return to take the adoption credit or the exclusion. You may take it on a separate return only if you are considered unmarried (legally separated, or living apart from your spouse for the last 6 months and meeting the other requirements). A married-filing-separately taxpayer may still claim a prior-year carryforward.",
     "notes": "W4."},
    {"diagnostic_id": "D_8839_CARRYFWD", "title": "5-year carryforward of the NONREFUNDABLE credit only", "severity": "info",
     "condition": "prior_carryforward > 0 or tax_liability_limit >= 0",
     "message": "Any nonrefundable adoption credit you can't use this year (line 16 over the tax-liability limit line 17) carries forward up to 5 years. The REFUNDABLE portion (line 13) is not carried forward - it's paid this year. A carryforward from 2024 remains a nonrefundable credit (it does not become refundable).",
     "notes": "W2."},
    {"diagnostic_id": "D_8839_EXCLUSION", "title": "Employer adoption benefits — exclusion + taxable remainder", "severity": "info",
     "condition": "employer_benefits > 0",
     "message": "Employer-provided adoption benefits (W-2 box 12, code T) are excluded up to $17,280 per child, subject to the same MAGI phaseout (Part III). The excluded amount is line 29; any benefits over the excludable amount are taxable (line 31) and go to Form 1040 line 1f. A special-needs child finalized in 2025 gets the full exclusion regardless of the benefit amount.",
     "notes": "W3."},
    {"diagnostic_id": "D_8839_INDEXED", "title": "The $5,000 refundable cap is statutorily indexed (not stated in i8839)", "severity": "info",
     "condition": "l11a_after_phaseout > 5000",
     "message": "The refundable cap is $5,000 for 2025. This cap is inflation-indexed by statute (IRC §36C / OBBBA §70402) - it rises to $5,120 for 2026 - but the 2025 Form 8839 instructions do NOT state the indexing. Use $5,000 for 2025; re-verify the indexed figure each season from the statute/COLA, not the form.",
     "notes": "W4. Provenance: form = flat 2025 $5,000; statute = the indexing."},
]

F8839_SCENARIOS: list[dict] = [
    {"scenario_name": "8839-A — credit, no phaseout, refundable split", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"qualified_adoption_expenses": 20000, "magi": 100000, "tax_liability_limit": 15000},
     "expected_outputs": {"l6_base": 17280.0, "l11a_after_phaseout": 17280.0, "l13_refundable": 5000.0, "l18_nonrefundable": 12280.0},
     "notes": "L6 = min(17,280, 20,000) = 17,280; MAGI 100k < 259,190 -> no phaseout; L11a 17,280; refundable min(17,280, 5,000) = 5,000 -> 1040 L30; nonrefundable 17,280-5,000 = 12,280 <= tax limit 15,000 -> Sch 3 6c."},
    {"scenario_name": "8839-B — MAGI phaseout 50%", "scenario_type": "edge", "sort_order": 2,
     "inputs": {"qualified_adoption_expenses": 20000, "magi": 279190, "tax_liability_limit": 15000},
     "expected_outputs": {"l6_base": 17280.0, "l11a_after_phaseout": 8640.0, "l13_refundable": 5000.0, "l18_nonrefundable": 3640.0},
     "notes": "fraction = (279,190-259,190)/40,000 = 0.5; L11a = 17,280 x 0.5 = 8,640; refundable min(8,640, 5,000) = 5,000; nonrefundable 3,640."},
    {"scenario_name": "8839-C — fully phased out", "scenario_type": "failure", "sort_order": 3,
     "inputs": {"qualified_adoption_expenses": 20000, "magi": 299190, "tax_liability_limit": 15000},
     "expected_outputs": {"l11a_after_phaseout": 0.0, "l13_refundable": 0.0, "l18_nonrefundable": 0.0, "diagnostic": "D_8839_PHASEOUT"},
     "notes": "MAGI 299,190 -> fraction 1.000 -> no credit."},
    {"scenario_name": "8839-D — special needs, no expenses", "scenario_type": "edge", "sort_order": 4,
     "inputs": {"is_special_needs": True, "qualified_adoption_expenses": 0, "magi": 100000, "tax_liability_limit": 20000},
     "expected_outputs": {"l6_base": 17280.0, "l11a_after_phaseout": 17280.0, "l13_refundable": 5000.0, "l18_nonrefundable": 12280.0, "diagnostic": "D_8839_SPECIALNEEDS"},
     "notes": "Special-needs U.S. child finalized 2025 -> full $17,280 even with $0 expenses; refundable 5,000; nonrefundable 12,280."},
    {"scenario_name": "8839-E — employer-benefit exclusion + taxable", "scenario_type": "normal", "sort_order": 5,
     "inputs": {"employer_benefits": 20000, "magi": 100000},
     "expected_outputs": {"l29_excluded": 17280.0, "l31_taxable": 2720.0, "diagnostic": "D_8839_EXCLUSION"},
     "notes": "L24 = min(17,280, 20,000) = 17,280; no phaseout -> excluded 17,280; taxable = 20,000 - 17,280 = 2,720 -> 1040 L1f."},
    {"scenario_name": "8839-F — tax-liability limit caps the nonrefundable credit", "scenario_type": "edge", "sort_order": 6,
     "inputs": {"qualified_adoption_expenses": 20000, "magi": 100000, "tax_liability_limit": 5000},
     "expected_outputs": {"l11a_after_phaseout": 17280.0, "l13_refundable": 5000.0, "l18_nonrefundable": 5000.0, "carryforward_next": 7280.0, "diagnostic": "D_8839_CARRYFWD"},
     "notes": "Refundable 5,000; nonrefundable L16 = 12,280 capped by tax limit 5,000 -> L18 5,000; carryforward = 12,280 - 5,000 = 7,280 (up to 5 years)."},
]

FORMS: list[dict] = [
    {
        "identity": {"form_number": "8839", "form_title": "Form 8839 — Qualified Adoption Expenses (2025)",
                     "notes": "WO-20 (SPINE S-16, 7th; DECISIONS D-22). Part II §23 credit: L6 = min($17,280-prior, expenses) (special-needs full) -> MAGI phaseout ($259,190-$299,190 / $40,000) -> L11a; ★ OBBBA 2025 REFUNDABLE split: L11b = min(L11a, $5,000)/child -> L13 -> 1040 L30; nonrefundable L14+carryforward -> min(tax limit L17) -> Sch 3 6c, 5-yr carryforward. Part III §137 exclusion: L24 min(max, employer benefits) -> phaseout -> L29 excluded / L31 taxable -> 1040 L1f. Special-needs full credit + OBBBA §70403 tribal parity; no credit+exclusion double-dip; MFS must file jointly. entity_types [1040]. ALL figures INDEXED - re-verify. ⚠ $5,000 refundable cap indexing is statutory (§36C, 2026 $5,120), NOT in i8839."},
        "facts": F8839_FACTS, "rules": F8839_RULES, "rule_links": F8839_RULE_LINKS,
        "lines": F8839_LINES, "diagnostics": F8839_DIAGNOSTICS, "scenarios": F8839_SCENARIOS,
    },
]

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-8839-REFUND", "title": "Up to $5,000/child is refundable (OBBBA 2025) -> 1040 line 30", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "draft", "sort_order": 1,
     "description": "Line 13 refundable adoption credit = sum of min(line 11a, $5,000) per child, carried to Form 1040 line 30; the nonrefundable remainder goes to Schedule 3 line 6c.",
     "definition": {"rule": "R-8839-REFUND", "check": "l13_refundable = min(l11a_after_phaseout, 5000)"}},
    {"assertion_id": "FA-8839-PHASEOUT", "title": "Credit + exclusion phase out $259,190 -> $299,190", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "draft", "sort_order": 2,
     "description": "Both the credit (L11a) and the exclusion (L29) are reduced by fraction = (MAGI - $259,190)/$40,000, floored at 0 and capped at 1.000.",
     "definition": {"rule": "R-8839-PHASEOUT", "check": "phaseout_fraction = min(1, max(0, (magi-259190)/40000))"}},
    {"assertion_id": "FA-8839-NOCARRY", "title": "5-yr carryforward is nonrefundable only", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "draft", "sort_order": 3,
     "description": "The nonrefundable credit over the tax-liability limit carries forward up to 5 years; the refundable portion (line 13) is not carried forward, and a 2024 carryforward stays nonrefundable.",
     "definition": {"rule": "R-8839-NONREFUND", "check": "l18_nonrefundable = min(l14 + prior_carryforward, tax_liability_limit)"}},
]


class Command(BaseCommand):
    help = "Load the Form 8839 spec (Qualified Adoption Expenses, 2025). Refuses to seed until READY_TO_SEED=True (W1-W4)."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad Form 8839 spec (Qualified Adoption Expenses)\n"))
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
                "\nREFUSING TO SEED FORM 8839: not cleared.\n\n"
                "Gated until Ken reviews (W1 credit + refundable split; W2 nonrefundable + carryforward;\n"
                "W3 Part III exclusion; W4 special-needs + coordination) and flips the sentinel.\n\n"
                f"READY_TO_SEED = {READY_TO_SEED}\n\nEmpty:\n  {still}\n"
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
        self.stdout.write("Form 8839 loaded.")
        self.stdout.write(f"  8839: facts {len(F8839_FACTS)} / rules {len(F8839_RULES)} / lines {len(F8839_LINES)} / diag {len(F8839_DIAGNOSTICS)} / tests {len(F8839_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}")
        self.stdout.write("=" * 60)
