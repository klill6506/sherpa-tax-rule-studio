"""Load the Form 8814 spec — Parents' Election To Report Child's Interest and Dividends (2025, Created 3/19/25).
WO-19, 6th item in the SPINE S-16 federal-forms queue (after 8990 + Schedule H + 4684 + 4952 + 8379). Greenfield.

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
Form 8814 is the parents' election (§1(g)(7)) to report a child's interest, dividends, and capital gain
distributions on the PARENTS' Form 1040 instead of the child filing a separate return. Three tiers: the
first $1,350 is not taxed; the next $1,350 is taxed at 10% (max $135, a small tax on the parent's return);
everything over the $2,700 base is carried to the parent's return, split by character (qualified dividends
-> 1040 3a/3b, capital gain distributions -> Schedule D line 13, remaining ordinary -> Schedule 1 line 8z).

Sibling of the EXISTING `8615` (child's kiddie-tax form, in RS prod) — 8814 is the alternative where the
PARENT elects to report; 8615 is where the CHILD files. This closes the 8615 spec's D_8615_004 RED-defer.

Greenfield: 8814 not in the 115-form prod set at the 2026-07-06 gap-check (8615 = 200, present).

═══════════════════════════════════════════════════════════════════════════
v1 SCOPE — LOCKED (Ken's Gate-1 walk 2026-07-06; DECISIONS D-21). See f8814_source_brief.md.
═══════════════════════════════════════════════════════════════════════════
COMPUTES: (Q1) Part I L4-L12 — base subtraction, proportional QD (L9) / cap-gain-dist (L10) split of the excess,
parent carries (L9->1040 3a/3b, L10->Sch D L13, L12->Sch 1 L8z). (Q2) can_elect from the 8 conditions + the two
gates (L4<=$2,700 skip; L4>=$13,500 don't file) + the file-separately caution. (Q3) 8615 cross-ref cited to
§1(g)/Pub 929 (NOT i8814). (Q4) Part II tax L13 $1,350 / L15 ($135 flat-or-10%) -> 1040 L16; one 8814 [1040] + multi-child.

requires_human_review WALK ITEMS (W1-W4):
W1. Part I: L4 = 1a+2a+3; L6 = L4-$2,700; L7 = 2b/L4, L8 = 3/L4; L9 = L6*L7, L10 = L6*L8; L12 = L6-(L9+L10) -> Sch 1
    L8z. CONFIRM the proportional character split + carries.
W2. Eligibility: under 19 / under 24 student, income only int/div/cap-gain-dist, gross < $13,500, required to file,
    not joint, no estimated payments, no withholding, qualified parent. Gates: <=$2,700 Part II only; >=$13,500 don't file.
W3. 8615 = the alternative (child files); cite the §1(g) relationship to Pub 929, NOT i8814 (provenance caveat).
W4. Part II: L13 $1,350; L14 = L4-$1,350; L15 = $135 if L14>=$1,350 else L14*10% -> 1040 L16 (check box 1).

CARRIED [UNVERIFIED]: none from the 8814 sources. The 8615/§1(g) relationship is cited to §1(g)/Pub 929 (the 8814
form/instructions do not state it). All four 2025 figures verbatim (Form 8814 Created 3/19/25 + i8814). INDEXED —
re-verify every season ($2,700 / $1,350 / $135 / $13,500).

SAFETY GUARD — READY_TO_SEED stays False until Ken approves the review walk (W1-W4).
FLIPPED 2026-07-06 — Ken APPROVED ("Approve — flip, seed, export"): W1 the Part I proportional
allocation + parent carries, W2 the eligibility 8-conditions + the $2,700/$13,500 gates, W3 the 8615
cross-reference cited to §1(g)/Pub 929, W4 the Part II $135/10% tax. Validated (scratchpad/validate_8814.py, 26/0).
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

# ── Verified 2025 constants (f8814_source_brief.md; Form 8814 2025 Created 3/19/25 / i8814). INDEXED — re-verify each season. ──
BASE_AMOUNT = 2700              # L5 / Part II heading — base amount (2024: $2,600)
NOT_TAXED = 1350               # L13 — first tier not taxed (2024: $1,300)
SECOND_TIER_FLAT_TAX = 135     # L15 "No" — flat tax = 10% x $1,350 (2024: $130)
SECOND_TIER_RATE = "0.10"      # L15 "Yes" — 10% of line 14
DONT_FILE_CEILING = 13500      # L4 / eligibility — child gross-income upper limit (2024: $13,000)
CHILD_AGE_UNDER = 19           # under 19 (or under 24 if a full-time student) at year end


def _line4(taxable_interest, ordinary_dividends, cap_gain_distributions) -> float:
    """L4 = L1a taxable interest + L2a ordinary dividends + L3 capital gain distributions.
    (L1b tax-exempt interest and L2b qualified dividends are NOT added — 2b is a subset of 2a.)"""
    return round(float(taxable_interest) + float(ordinary_dividends) + float(cap_gain_distributions), 2)


def _part1_allocation(line4, qualified_dividends_2b, cap_gain_distributions_3) -> dict:
    """Part I L6-L12: excess over the $2,700 base, split by character to the parent's return.
    L6 = L4 - base; L7 = 2b/L4; L8 = 3/L4; L9 = L6*L7 (QD); L10 = L6*L8 (cap gain dist); L12 = L6 - (L9+L10)."""
    if float(line4) <= BASE_AMOUNT:
        return {"L6": 0.0, "L9": 0.0, "L10": 0.0, "L11": 0.0, "L12": 0.0}  # Part I skipped
    l6 = round(float(line4) - BASE_AMOUNT, 2)
    l7 = float(qualified_dividends_2b) / float(line4)
    l8 = float(cap_gain_distributions_3) / float(line4)
    l9 = round(l6 * l7, 2)      # qualified-dividend portion -> 1040 lines 3a/3b
    l10 = round(l6 * l8, 2)     # cap-gain-distribution portion -> Schedule D line 13
    l11 = round(l9 + l10, 2)
    l12 = round(l6 - l11, 2)    # remaining ordinary -> Schedule 1 line 8z ("Form 8814")
    return {"L6": l6, "L9": l9, "L10": l10, "L11": l11, "L12": l12}


def _part2_tax(line4) -> float:
    """Part II L13-L15: L14 = L4 - $1,350; L15 = $135 if L14 >= $1,350 else L14 x 10% -> Form 1040 line 16."""
    l14 = max(0.0, round(float(line4) - NOT_TAXED, 2))
    if l14 >= NOT_TAXED:
        return float(SECOND_TIER_FLAT_TAX)
    return round(l14 * float(SECOND_TIER_RATE), 2)


def _can_elect(under_age_limit, income_only_int_div, child_gross_income, required_to_file,
               not_joint, no_estimated_payments, no_withholding, qualified_parent) -> bool:
    """The 8 eligibility conditions — all must hold, and the child's gross income must be < $13,500."""
    return bool(under_age_limit and income_only_int_div and float(child_gross_income) < DONT_FILE_CEILING
                and required_to_file and not_joint and no_estimated_payments and no_withholding and qualified_parent)


AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("parents_election_8814", "Form 8814 parents' election (§1(g)(7)) to report a child's interest/dividends: 3 tiers "
     "($1,350 free / next $1,350 at 10% = $135 / over $2,700 to parent); proportional QD + cap-gain carry; don't-file "
     "over $13,500. Alternative to Form 8615."),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_F8814", "source_type": "federal_form", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Form 8814 (2025) — Parents' Election To Report Child's Interest and Dividends",
        "citation": "Form 8814 (2025), Cat. No. 10750J, Created 3/19/25, Attach. Seq. No. 40",
        "issuer": "Internal Revenue Service", "official_url": "https://www.irs.gov/pub/irs-pdf/f8814.pdf",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.6, "topics": ["parents_election_8814"],
        "excerpts": [{
            "excerpt_label": "Part I + Part II line map with 2025 figures (verbatim)",
            "excerpt_text": (
                "Part I: L1a child's taxable interest; L1b tax-exempt interest (do not include on 1a); L2a ordinary "
                "dividends (incl. Alaska Permanent Fund dividends); L2b qualified dividends included on 2a; L3 "
                "capital gain distributions; L4 'Add lines 1a, 2a, and 3. If the total is $2,700 or less, skip lines "
                "5 through 12 and go to line 13. If the total is $13,500 or more, do not file this form; your child "
                "must file his or her own return.' L5 base amount $2,700; L6 subtract L5 from L4; L7 divide L2b by "
                "L4; L8 divide L3 by L4; L9 multiply L6 by L7; L10 multiply L6 by L8; L11 add L9 and L10; L12 "
                "subtract L11 from L6 - include on Schedule 1 (Form 1040) line 8z, 'Form 8814'. Part II 'Tax on the "
                "First $2,700 of Child's Interest and Dividends': L13 amount not taxed $1,350; L14 subtract L13 from "
                "L4 (if zero or less, -0-); L15 'Is the amount on line 14 less than $1,350? No - enter $135. Yes - "
                "multiply line 14 by 10% (0.10)' -> include on Form 1040 line 16, check box 1."
            ),
            "summary_text": "L4 = 1a+2a+3 ($2,700 skip / $13,500 don't file); L6-L12 excess split (L9 QD->3a/3b, L10 capgain->Sch D 13, L12 ordinary->Sch1 8z); Part II L13 $1,350 / L15 $135-or-10% -> 1040 L16.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "Carries + caution + multiple children (verbatim substance)",
            "excerpt_text": (
                "Line 9 (qualified-dividend portion) is carried to Form 1040 lines 3a and 3b; line 10 (capital gain "
                "distribution portion) to Schedule D line 13 (or Form 1040 line 7 if Schedule D isn't required); "
                "line 12 (remaining ordinary) to Schedule 1 line 8z. Caution: 'The federal income tax on your "
                "child's income... may be less if you file a separate tax return for the child instead of making "
                "this election' (the election forfeits the child's blind additional standard deduction, the early-"
                "withdrawal penalty deduction, and the child's itemized deductions). 'A separate Form 8814 must be "
                "filed for each child whose income you choose to report'; check line C if more than one is attached."
            ),
            "summary_text": "Carries: L9->1040 3a/3b, L10->Sch D 13, L12->Sch1 8z. Caution: may be cheaper for the child to file separately. Separate 8814 per child (line C).",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "IRS_2025_I8814", "source_type": "official_instructions", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "2025 Instructions for Form 8814",
        "citation": "Instructions for Form 8814 (2025), reviewed 30-Apr-2026", "issuer": "Internal Revenue Service",
        "official_url": "https://www.irs.gov/instructions/i8814",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.5, "topics": ["parents_election_8814"],
        "excerpts": [{
            "excerpt_label": "Eligibility conditions (i8814 verbatim)",
            "excerpt_text": (
                "'Use this form if you elect to report your child's income on your return. If you do, your child "
                "will not have to file a return.' You can make the election only if ALL apply: the child was under "
                "age 19 (or under age 24 if a full-time student) at the end of 2025; the child's only income was "
                "from interest and dividends, including capital gain distributions and Alaska Permanent Fund "
                "dividends; the child's gross income for 2025 was less than $13,500; the child is required to file a "
                "2025 return; the child does not file a joint return for 2025; there were no estimated tax payments "
                "for the child for 2025 (including any 2024 overpayment applied to 2025); and there was no federal "
                "income tax withheld from the child's income. You qualify to make the election if you file Form "
                "1040/1040-SR/1040-NR and are the parent whose return must be used (MFJ; the higher-taxable-income "
                "spouse if MFS; or the custodial parent)."
            ),
            "summary_text": "Eligible if: under 19 (or 24 student), income only int/div/cap-gain-dist, gross < $13,500, required to file, not joint, no estimated payments, no withholding, qualified parent.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "IRC_1G", "source_type": "statute", "source_rank": "controlling",
        "jurisdiction_code": "US", "title": "IRC §1(g)(7) — parents' election; §1(g) kiddie tax (Pub 929)",
        "citation": "26 U.S.C. §1(g)(7); §1(g); IRS Pub. 929", "issuer": "U.S. Congress",
        "official_url": "https://www.law.cornell.edu/uscode/text/26/1",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.2, "topics": ["parents_election_8814"],
        "excerpts": [{
            "excerpt_label": "§1(g)(7) election + relationship to Form 8615 (cited to §1(g)/Pub 929, NOT i8814)",
            "excerpt_text": (
                "§1(g)(7): if a child's gross income is only from interest and dividends, is more than the floor and "
                "less than the ceiling amount, and no estimated payments/backup withholding are in the child's name, "
                "the PARENT may ELECT to include the child's gross income on the parent's return - the child is then "
                "treated as having no gross income and does not file. §1(g) otherwise imposes the 'kiddie tax' on a "
                "child's net unearned income at the parent's rate, computed on FORM 8615 when the parent does NOT "
                "make the 8814 election. NOTE: this 8814-vs-8615 relationship is cited to §1(g)/Pub 929 - the Form "
                "8814 face and instructions do not themselves mention Form 8615 or 'kiddie tax'."
            ),
            "summary_text": "§1(g)(7): parent elects to report the child's int/div income (child doesn't file); the no-election alternative is the child's Form 8615 kiddie tax. Relationship cited to §1(g)/Pub 929, not i8814.",
            "is_key_excerpt": True,
        }],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_F8814", "8814", "governs"), ("IRS_2025_I8814", "8814", "governs"),
    ("IRC_1G", "8814", "governs"), ("IRC_1G", "8615", "relates_to"),
]


F8814_FACTS: list[dict] = [
    # Eligibility
    {"fact_key": "child_under_age_limit", "label": "Child under 19 (or under 24 if a full-time student) at end of 2025?", "data_type": "boolean", "required": False, "sort_order": 1},
    {"fact_key": "income_only_int_div", "label": "Child's ONLY income was interest, dividends, and capital gain distributions?", "data_type": "boolean", "required": False, "sort_order": 2},
    {"fact_key": "child_gross_income", "label": "Child's gross income for 2025 (must be < $13,500 to elect)", "data_type": "decimal", "required": False, "sort_order": 3},
    {"fact_key": "child_required_to_file", "label": "Child is required to file a 2025 return?", "data_type": "boolean", "required": False, "sort_order": 4},
    {"fact_key": "child_not_joint", "label": "Child does NOT file a joint return for 2025?", "data_type": "boolean", "required": False, "sort_order": 5},
    {"fact_key": "no_estimated_payments", "label": "No estimated tax payments in the child's name (incl. prior-year overpayment applied)?", "data_type": "boolean", "required": False, "sort_order": 6},
    {"fact_key": "no_withholding", "label": "No federal income tax withheld from the child's income (no backup withholding)?", "data_type": "boolean", "required": False, "sort_order": 7},
    {"fact_key": "qualified_parent", "label": "You are the parent qualified to make the election (MFJ / higher-income MFS / custodial)?", "data_type": "boolean", "required": False, "sort_order": 8},
    # Part I income
    {"fact_key": "taxable_interest", "label": "Child's taxable interest (L1a)", "data_type": "decimal", "required": False, "sort_order": 9},
    {"fact_key": "tax_exempt_interest", "label": "Child's tax-exempt interest (L1b) — not included in L4", "data_type": "decimal", "required": False, "sort_order": 10},
    {"fact_key": "ordinary_dividends", "label": "Child's ordinary dividends, incl. Alaska Permanent Fund (L2a)", "data_type": "decimal", "required": False, "sort_order": 11},
    {"fact_key": "qualified_dividends", "label": "Child's qualified dividends included on L2a (L2b)", "data_type": "decimal", "required": False, "sort_order": 12},
    {"fact_key": "cap_gain_distributions", "label": "Child's capital gain distributions (L3)", "data_type": "decimal", "required": False, "sort_order": 13},
]

F8814_RULES: list[dict] = [
    {"rule_id": "R-8814-ELIG", "title": "Eligibility to make the election (can_elect)", "rule_type": "routing",
     "formula": "can_elect = child_under_age_limit and income_only_int_div and child_gross_income < 13500 and child_required_to_file and child_not_joint and no_estimated_payments and no_withholding and qualified_parent",
     "inputs": ["child_under_age_limit", "income_only_int_div", "child_gross_income", "child_required_to_file", "child_not_joint", "no_estimated_payments", "no_withholding", "qualified_parent"],
     "outputs": ["can_elect"], "sort_order": 1,
     "description": "W2. The parent may make the §1(g)(7) election only if ALL 8 conditions hold: child under 19 (or under 24 if a full-time student); income only interest/dividends/capital-gain-distributions; gross income < $13,500; required to file; not filing jointly; no estimated payments in the child's name; no federal income tax withheld; and you are the qualified parent."},
    {"rule_id": "R-8814-L4", "title": "Line 4 total + the two threshold gates", "rule_type": "calculation",
     "formula": "L4 = taxable_interest + ordinary_dividends + cap_gain_distributions ; if L4 <= 2700: skip Part I (Part II only) ; if L4 >= 13500: do not file (child files own return)",
     "inputs": ["taxable_interest", "ordinary_dividends", "cap_gain_distributions"], "outputs": ["line4"], "sort_order": 2,
     "description": "W2. L4 = L1a + L2a + L3 (tax-exempt interest L1b and qualified dividends L2b are not added). If L4 <= $2,700, skip Part I lines 5-12 and compute only the Part II tax. If L4 >= $13,500, do NOT file Form 8814 - the child must file their own return."},
    {"rule_id": "R-8814-ALLOC", "title": "Part I — excess over $2,700 split by character to the parent (L6-L12)", "rule_type": "calculation",
     "formula": "L6 = L4 - 2700 ; L7 = L2b/L4 ; L8 = L3/L4 ; L9 = L6*L7 (QD -> 1040 3a/3b) ; L10 = L6*L8 (cap gain dist -> Sch D L13) ; L12 = L6 - (L9+L10) (ordinary -> Sch 1 L8z)",
     "inputs": ["qualified_dividends", "cap_gain_distributions"], "outputs": ["l6_excess", "l9_qd", "l10_capgain", "l12_ordinary"], "sort_order": 3,
     "description": "W1. Part I: the excess of the child's income over the $2,700 base (L6) is carried to the parent's return, split by character - the qualified-dividend fraction (L7 = L2b/L4) becomes L9 (-> Form 1040 lines 3a/3b), the capital-gain-distribution fraction (L8 = L3/L4) becomes L10 (-> Schedule D line 13), and the remainder L12 (ordinary) goes to Schedule 1 line 8z labeled 'Form 8814.'"},
    {"rule_id": "R-8814-TAX", "title": "Part II — tax on the first $2,700 (L13-L15)", "rule_type": "calculation",
     "formula": "L13 = 1350 ; L14 = max(0, L4 - 1350) ; L15 = 135 if L14 >= 1350 else round(L14 * 0.10, 2)",
     "inputs": ["taxable_interest", "ordinary_dividends", "cap_gain_distributions"], "outputs": ["l15_tax"], "sort_order": 4,
     "description": "W4. Part II: L13 = $1,350 (not taxed); L14 = L4 - $1,350 (floored at 0); L15 = $135 if L14 >= $1,350, otherwise L14 x 10%. The line-15 tax is added on Form 1040 line 16 (check box 1). This is a small parent-level tax on the child's second income tier."},
]

F8814_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-8814-ELIG", "IRS_2025_I8814", "primary", "eligibility conditions"),
    ("R-8814-ELIG", "IRC_1G", "secondary", "§1(g)(7) election"),
    ("R-8814-L4", "IRS_2025_F8814", "primary", "L4 + $2,700/$13,500 gates"),
    ("R-8814-ALLOC", "IRS_2025_F8814", "primary", "Part I L5-L12 + carries"),
    ("R-8814-TAX", "IRS_2025_F8814", "primary", "Part II L13-L15"),
]

F8814_LINES: list[dict] = [
    {"line_number": "L4", "description": "Total child income (1a + 2a + 3); gate $2,700 / $13,500", "line_type": "subtotal", "source_rules": ["R-8814-L4"], "sort_order": 1},
    {"line_number": "L6", "description": "Excess over the $2,700 base", "line_type": "calculated", "source_rules": ["R-8814-ALLOC"], "sort_order": 2},
    {"line_number": "L9", "description": "Qualified-dividend portion -> Form 1040 lines 3a/3b", "line_type": "calculated", "source_rules": ["R-8814-ALLOC"], "sort_order": 3},
    {"line_number": "L10", "description": "Cap-gain-distribution portion -> Schedule D line 13", "line_type": "calculated", "source_rules": ["R-8814-ALLOC"], "sort_order": 4},
    {"line_number": "L12", "description": "Remaining ordinary -> Schedule 1 line 8z", "line_type": "calculated", "source_rules": ["R-8814-ALLOC"], "sort_order": 5},
    {"line_number": "L15", "description": "Tax on the first $2,700 -> Form 1040 line 16 (box 1)", "line_type": "calculated", "source_rules": ["R-8814-TAX"], "sort_order": 6},
]

F8814_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_8814_ELIG", "title": "Election eligibility — all 8 conditions must hold", "severity": "warning",
     "condition": "not (child_under_age_limit and income_only_int_div and child_gross_income < 13500 and child_required_to_file and child_not_joint and no_estimated_payments and no_withholding and qualified_parent)",
     "message": "You can make the Form 8814 election only if ALL apply: the child was under 19 (or under 24 if a full-time student) at year end; the child's only income was interest, dividends, and capital gain distributions; the child's gross income was less than $13,500; the child is required to file; does not file jointly; had no estimated tax payments in the child's name; had no federal income tax withheld; and you are the qualified parent. If any fails, the child must file their own return (Form 8615 if subject to the kiddie tax).",
     "notes": "W2."},
    {"diagnostic_id": "D_8814_DONTFILE", "title": "Child income >= $13,500 — do not file Form 8814", "severity": "error",
     "condition": "taxable_interest + ordinary_dividends + cap_gain_distributions >= 13500",
     "message": "The child's total interest, dividends, and capital gain distributions (line 4) is $13,500 or more. You cannot make this election - the child must file his or her own return (and figure any kiddie tax on Form 8615). Do not file Form 8814.",
     "notes": "W2. Year-keyed 2025 ceiling."},
    {"diagnostic_id": "D_8814_SKIP", "title": "Child income <= $2,700 — Part I skipped, Part II only", "severity": "info",
     "condition": "taxable_interest + ordinary_dividends + cap_gain_distributions <= 2700",
     "message": "The child's total (line 4) is $2,700 or less, so nothing is added to your income - skip Part I lines 5-12 and figure only the small Part II tax (line 15). Include that tax on Form 1040 line 16 (check box 1).",
     "notes": "W2."},
    {"diagnostic_id": "D_8814_CHEAPER", "title": "Filing a separate return for the child may cost less tax", "severity": "info",
     "condition": "child_gross_income > 0",
     "message": "The tax on the child's income may be LESS if you file a separate return for the child instead of making this election, because the election forfeits benefits the child could take on their own return: the additional standard deduction if the child is blind, the deduction for the penalty on early withdrawal of the child's savings, and the child's itemized deductions (e.g., charitable contributions). Compare both before electing.",
     "notes": "The form's own caution."},
    {"diagnostic_id": "D_8814_8615", "title": "No election -> the child files Form 8615 (kiddie tax)", "severity": "info",
     "condition": "not qualified_parent",
     "message": "Form 8814 is the parents' ELECTION to report the child's income. If you do NOT make this election, the child files their own return and figures the kiddie tax (a child's net unearned income taxed at the parent's rate) on Form 8615. (Relationship per IRC §1(g) / Pub. 929 - the Form 8814 instructions themselves do not reference Form 8615.)",
     "notes": "W3. Cited to §1(g)/Pub 929, NOT i8814 (provenance caveat). Closes the 8615 spec's D_8615_004 loop."},
    {"diagnostic_id": "D_8814_CARRY", "title": "Character carries to the parent's return", "severity": "info",
     "condition": "taxable_interest + ordinary_dividends + cap_gain_distributions > 2700",
     "message": "The child's income above $2,700 keeps its character on your return: line 9 (qualified-dividend portion) goes to Form 1040 lines 3a and 3b; line 10 (capital gain distribution portion) to Schedule D line 13 (or Form 1040 line 7 if Schedule D isn't required); and line 12 (remaining ordinary) to Schedule 1 line 8z with 'Form 8814' noted. The preferential rate on the qualified-dividend / capital-gain portion is preserved.",
     "notes": "W1."},
    {"diagnostic_id": "D_8814_MULTI", "title": "File a separate Form 8814 for each child", "severity": "info",
     "condition": "qualified_parent",
     "message": "A separate Form 8814 must be filed for each child whose income you choose to report. If more than one Form 8814 is attached, check the box on line C and combine the line-12 and line-15 amounts per the instructions.",
     "notes": "W4. Multiple-children (line C)."},
]

F8814_SCENARIOS: list[dict] = [
    {"scenario_name": "8814-A — income over base, full allocation", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"taxable_interest": 2000, "ordinary_dividends": 2000, "qualified_dividends": 1000, "cap_gain_distributions": 1000},
     "expected_outputs": {"line4": 5000.0, "l6_excess": 2300.0, "l9_qd": 460.0, "l10_capgain": 460.0, "l12_ordinary": 1380.0, "l15_tax": 135.0},
     "notes": "L4 = 2,000+2,000+1,000 = 5,000; L6 = 2,300; L7 = 1,000/5,000 = 0.2 -> L9 460; L8 = 0.2 -> L10 460; L12 = 1,380 -> Sch1 8z. Part II: L14 = 3,650 >= 1,350 -> L15 $135."},
    {"scenario_name": "8814-B — income <= $2,700, Part II only", "scenario_type": "edge", "sort_order": 2,
     "inputs": {"taxable_interest": 2000, "ordinary_dividends": 500, "cap_gain_distributions": 0},
     "expected_outputs": {"line4": 2500.0, "l6_excess": 0.0, "l15_tax": 115.0, "diagnostic": "D_8814_SKIP"},
     "notes": "L4 = 2,500 <= 2,700 -> skip Part I; L14 = 2,500 - 1,350 = 1,150 < 1,350 -> L15 = 1,150 x 10% = 115."},
    {"scenario_name": "8814-C — income >= $13,500, do not file", "scenario_type": "failure", "sort_order": 3,
     "inputs": {"taxable_interest": 14000, "ordinary_dividends": 0, "cap_gain_distributions": 0, "child_gross_income": 14000},
     "expected_outputs": {"line4": 14000.0, "diagnostic": "D_8814_DONTFILE"},
     "notes": "L4 = 14,000 >= 13,500 -> cannot elect; the child must file their own return (Form 8615 if kiddie tax applies)."},
    {"scenario_name": "8814-D — eligibility fails (withholding present)", "scenario_type": "failure", "sort_order": 4,
     "inputs": {"child_under_age_limit": True, "income_only_int_div": True, "child_gross_income": 5000, "child_required_to_file": True, "child_not_joint": True, "no_estimated_payments": True, "no_withholding": False, "qualified_parent": True},
     "expected_outputs": {"can_elect": False, "diagnostic": "D_8814_ELIG"},
     "notes": "Federal income tax was withheld from the child's income (no_withholding False) -> cannot make the election; the child must file to claim the withholding."},
    {"scenario_name": "8814-E — second tier under $1,350 (10% tax)", "scenario_type": "edge", "sort_order": 5,
     "inputs": {"taxable_interest": 2000, "ordinary_dividends": 0, "cap_gain_distributions": 0},
     "expected_outputs": {"line4": 2000.0, "l15_tax": 65.0, "diagnostic": "D_8814_SKIP"},
     "notes": "L4 = 2,000 <= 2,700; L14 = 650 < 1,350 -> L15 = 650 x 10% = 65."},
    {"scenario_name": "8814-F — all conditions met (can elect)", "scenario_type": "normal", "sort_order": 6,
     "inputs": {"child_under_age_limit": True, "income_only_int_div": True, "child_gross_income": 5000, "child_required_to_file": True, "child_not_joint": True, "no_estimated_payments": True, "no_withholding": True, "qualified_parent": True},
     "expected_outputs": {"can_elect": True},
     "notes": "All 8 conditions hold and gross income 5,000 < 13,500 -> the parent may make the election."},
]

FORMS: list[dict] = [
    {
        "identity": {"form_number": "8814", "form_title": "Form 8814 — Parents' Election To Report Child's Interest and Dividends (2025)",
                     "notes": "WO-19 (SPINE S-16, 6th; DECISIONS D-21). §1(g)(7) election: parent reports the child's interest/dividends/cap-gain-distributions instead of the child filing (Form 8615 is the no-election alternative - cited to §1(g)/Pub 929, NOT i8814). 3 tiers: first $1,350 not taxed; next $1,350 at 10% (max $135, L15 -> 1040 L16); over $2,700 (L6) carried to the parent split by character (L9 QD -> 1040 3a/3b, L10 cap gain dist -> Sch D L13, L12 ordinary -> Sch 1 L8z). Don't file if L4 >= $13,500; Part II only if L4 <= $2,700. Eligibility = 8 conditions. Separate 8814 per child (line C). entity_types [1040]. 2025 figures INDEXED - re-verify ($2,700/$1,350/$135/$13,500). No OBBBA impact."},
        "facts": F8814_FACTS, "rules": F8814_RULES, "rule_links": F8814_RULE_LINKS,
        "lines": F8814_LINES, "diagnostics": F8814_DIAGNOSTICS, "scenarios": F8814_SCENARIOS,
    },
]

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-8814-TIERS", "title": "Three-tier tax: $1,350 free / next $1,350 at 10% / over $2,700 to parent", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "draft", "sort_order": 1,
     "description": "Part II line 15 = $135 if line 14 >= $1,350 else line 14 x 10%; Part I carries the excess over $2,700 to the parent's return.",
     "definition": {"rule": "R-8814-TAX", "check": "l15_tax = 135 if (line4-1350) >= 1350 else max(0, line4-1350)*0.10"}},
    {"assertion_id": "FA-8814-CHAR", "title": "Excess keeps its character on the parent's return", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "draft", "sort_order": 2,
     "description": "The excess over $2,700 (L6) splits into L9 qualified-dividend (-> 1040 3a/3b), L10 cap-gain-distribution (-> Sch D 13), and L12 ordinary (-> Sch 1 8z); L9 + L10 + L12 = L6.",
     "definition": {"rule": "R-8814-ALLOC", "check": "l9_qd + l10_capgain + l12_ordinary == l6_excess"}},
    {"assertion_id": "FA-8814-ELIG", "title": "Election requires all 8 conditions + gross income < $13,500", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "draft", "sort_order": 3,
     "description": "can_elect is True only if all eligibility conditions hold and the child's gross income is under $13,500; otherwise the child files their own return (Form 8615 if kiddie tax applies).",
     "definition": {"rule": "R-8814-ELIG", "check": "can_elect = all(conditions) and child_gross_income < 13500"}},
]


class Command(BaseCommand):
    help = "Load the Form 8814 spec (Parents' Election To Report Child's Interest and Dividends, 2025). Refuses to seed until READY_TO_SEED=True (W1-W4)."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad Form 8814 spec (Parents' Election To Report Child's Interest and Dividends)\n"))
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
                "\nREFUSING TO SEED FORM 8814: not cleared.\n\n"
                "Gated until Ken reviews (W1 Part I allocation + carries; W2 eligibility + gates;\n"
                "W3 the 8615 relationship cited to §1(g)/Pub 929; W4 Part II tax) and flips the\n"
                f"sentinel.\n\nREADY_TO_SEED = {READY_TO_SEED}\n\nEmpty:\n  {still}\n"
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
        self.stdout.write("Form 8814 loaded.")
        self.stdout.write(f"  8814: facts {len(F8814_FACTS)} / rules {len(F8814_RULES)} / lines {len(F8814_LINES)} / diag {len(F8814_DIAGNOSTICS)} / tests {len(F8814_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}")
        self.stdout.write("=" * 60)
