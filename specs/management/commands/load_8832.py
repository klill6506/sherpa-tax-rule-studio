"""Load the Form 8832 spec — Entity Classification Election ("check-the-box", Rev. December 2013).
WO-22, 9th item in the SPINE S-16 federal-forms queue. Greenfield.

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
Form 8832 is a structural ELECTION (Treas. Reg. §301.7701-3), not a tax computation. An eligible entity
elects its federal tax classification: (1) association taxable as a corporation, (2) partnership, or (3)
disregarded as separate from its owner (single owner only). If it does not file, it takes its DEFAULT
classification (domestic 2+ members -> partnership; 1 member -> disregarded). A per-se corporation (a
state-law corporation, §301.7701-2(b)) is NOT eligible. Distinct from Form 2553 (S-election, deemed to
also elect corp status -> no separate 8832).

Greenfield: 8832 not in the 118-form prod set at the 2026-07-06 gap-check (2553 also absent).

═══════════════════════════════════════════════════════════════════════════
v1 SCOPE — LOCKED (Ken's Gate-1 walk 2026-07-06; DECISIONS D-24). See f8832_source_brief.md.
═══════════════════════════════════════════════════════════════════════════
COMPUTES: (Q1) Part I decision tree -> is_eligible_to_elect + available classifications + stop-reasons. (Q2)
default classification (domestic member-count / foreign limited-liability) + don't-file-if-default TIP. (Q3) the
effective-date window clamp (75 days before / 12 months after) + 60-month gate + Rev. Proc. 2009-41 late-relief
diagnostic. (Q4) 2553 boundary + per-se-corp + attach/updated-address diagnostics. entity_types [1065,1120,1120S,1040].

requires_human_review WALK ITEMS (W1-W4):
W1. Eligibility: per-se corp ineligible; the 60-month block (change election + prior election within 60 months that
    was NOT a newly-formed initial election -> STOP). Available: >1 owner = partnership/corp; 1 owner = corp/disregarded.
W2. Default: domestic 2+ -> partnership, 1 -> disregarded; foreign all-limited-liability -> corp, else partnership/
    disregarded. A new entity using its default should NOT file.
W3. Effective date: no more than 75 days before / 12 months after filing (clamp to boundary; blank -> filing date).
    Late relief (Rev. Proc. 2009-41): within 3 years 75 days of the requested effective date + reasonable cause.
W4. S-election -> Form 2553 (not 8832); attach a copy to the entity's/owners' return; updated addresses Kansas City/Ogden.

CARRIED [UNVERIFIED]: none — verbatim vs current FINAL Form 8832 Rev. 12-2013 + §301.7701-3 + Rev. Proc. 2009-41.
Re-verify the FORM REVISION each season (reissues irregularly, not annually) + the filing addresses. No OBBBA impact.

SAFETY GUARD — READY_TO_SEED stays False until Ken approves the review walk (W1-W4).
FLIPPED 2026-07-06 — Ken APPROVED ("Approve — flip, seed, export"): W1 the eligibility tree (per-se corp
+ 60-month), W2 the default classification, W3 the effective-date window + Rev. Proc. 2009-41 late relief,
W4 the Form 2553 boundary + updated Kansas City/Ogden addresses. Validated (scratchpad/validate_8832.py, 31/0).
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
FORM_ENTITY_TYPES = ["1065", "1120", "1120S", "1040"]  # the classifications an 8832 election touches

# ── Verified constants (f8832_source_brief.md; Form 8832 Rev. 12-2013 + §301.7701-3 + Rev. Proc. 2009-41) ──
SIXTY_MONTH_LIMITATION = 60             # §301.7701-3(c)(1)(iv) — months before a changed classification can change again
EFF_DATE_DAYS_BEFORE = 75              # L8 — election effective no more than 75 days before filing
EFF_DATE_MONTHS_AFTER = 12             # L8 — nor later than 12 months after filing
LATE_RELIEF_YEARS = 3                  # Rev. Proc. 2009-41 — within 3 years ...
LATE_RELIEF_DAYS = 75                  # ... and 75 days of the requested effective date
# Updated filing addresses (supersede the printed Cincinnati addresses on p.5 of the instructions)
FILING_ADDRESSES = {
    "eastern": "Kansas City, MO 64999", "western": "Ogden, UT 84201", "foreign": "Ogden, UT 84201-0023",
}


def _is_eligible_to_elect(is_per_se_corp, election_type, prior_election_within_60mo, prior_was_newform_initial) -> tuple:
    """Part I: a per-se corporation is ineligible; a CHANGE election is blocked if a prior election took effect within
    the last 60 months and that prior election was NOT a newly-formed entity's initial election (§301.7701-3(c)(1)(iv))."""
    if is_per_se_corp:
        return (False, "per_se_corp")
    if election_type == "change" and prior_election_within_60mo and not prior_was_newform_initial:
        return (False, "sixty_month_block")
    return (True, "eligible")


def _default_classification(is_domestic, num_owners, all_members_limited_liability) -> str:
    """§301.7701-3(b) default: domestic 2+ -> partnership, 1 -> disregarded; foreign all-LL -> corporation, else
    partnership (2+) / disregarded (1 without limited liability)."""
    if is_domestic:
        return "partnership" if int(num_owners) >= 2 else "disregarded"
    if int(num_owners) >= 2:
        return "corporation" if all_members_limited_liability else "partnership"
    return "corporation" if all_members_limited_liability else "disregarded"


def _available_classifications(num_owners) -> list:
    """L3: more than one owner -> partnership or association-taxable-as-corp; one owner -> corp or disregarded."""
    return ["partnership", "corporation"] if int(num_owners) >= 2 else ["corporation", "disregarded"]


def _clamp_days_before(days_before_filing) -> float:
    """L8 effective date: an effective date more than 75 days before filing defaults to 75 days before (floor at 0)."""
    return float(min(max(0.0, float(days_before_filing)), EFF_DATE_DAYS_BEFORE))


AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("entity_classification_8832", "Form 8832 entity classification election (§301.7701-3): elect corp/partnership/"
     "disregarded; defaults (domestic 2+ = partnership, 1 = disregarded); 60-month limit; 75-day/12-month window; "
     "Rev. Proc. 2009-41 late relief; S-elections use Form 2553."),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_F8832", "source_type": "federal_form", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Form 8832 (Rev. 12-2013) — Entity Classification Election",
        "citation": "Form 8832 (Rev. December 2013), Cat. No. 22598R, OMB 1545-1516",
        "issuer": "Internal Revenue Service", "official_url": "https://www.irs.gov/pub/irs-pdf/f8832.pdf",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.5, "topics": ["entity_classification_8832"],
        "excerpts": [{
            "excerpt_label": "Part I decision tree L1-L8 (Rev. 12-2013 verbatim)",
            "excerpt_text": (
                "Part I Election Information: L1 type of election - 1a 'Initial classification by a newly-formed "
                "entity. Skip lines 2a and 2b and go to line 3.'; 1b 'Change in current classification. Go to line "
                "2a.' L2a 'Has the eligible entity previously filed an entity election that had an effective date "
                "within the last 60 months?' (Yes -> 2b; No -> line 3). L2b 'Was the eligible entity's prior "
                "election an initial classification election by a newly formed entity that was effective on the "
                "date of formation?' (Yes -> line 3; No -> Stop here. You generally are not currently eligible to "
                "make the election). L3 'Does the eligible entity have more than one owner?' (Yes -> partnership or "
                "association taxable as a corporation, skip L4 -> L5; No -> association taxable as a corporation or "
                "disregarded, go to L4). L6 type of entity: 6a domestic association taxable as a corporation; 6b "
                "domestic partnership; 6c domestic single-owner disregarded; 6d/6e/6f foreign equivalents. L8 "
                "'Election is to be effective beginning (month, day, year).'"
            ),
            "summary_text": "L1 initial(1a)/change(1b); L2a/2b 60-month gate; L3 >1 owner = partnership/corp, 1 owner = corp/disregarded; L6 6a-6f classification; L8 effective date.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "Defaults + 60-month + effective window + 2553 + relief (instructions verbatim substance)",
            "excerpt_text": (
                "Domestic default rule: a domestic eligible entity is a partnership if it has two or more members, "
                "or disregarded if it has a single owner. A new eligible entity should not file Form 8832 if it "
                "will be using its default classification. 60-month limitation: once an eligible entity elects to "
                "change its classification, it generally cannot change again during the 60 months after the "
                "effective date (exception: >50% ownership change by PLR; not applicable to a newly formed entity's "
                "initial election effective on formation). Line 8: an election can take effect no more than 75 days "
                "prior to the filing date, nor later than 12 months after; outside that range it defaults to the "
                "boundary; blank -> the date filed. An entity electing S-corporation status files Form 2553 (deemed "
                "§301.7701-3(c)(1)(v) association election) - do not file Form 8832. Part II late relief under Rev. "
                "Proc. 2009-41: file within 3 years and 75 days of the requested effective date with reasonable "
                "cause. Attach a copy of Form 8832 to the entity's (and owners') return; file at Kansas City, MO "
                "64999 / Ogden, UT 84201 (updated addresses)."
            ),
            "summary_text": "Default domestic 2+ = partnership / 1 = disregarded (don't file if using default). 60-month limit. 75-day/12-month window. S-election = Form 2553. Rev. Proc. 2009-41 = 3yr 75 days. Kansas City/Ogden.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "REG_7701_3", "source_type": "regulation", "source_rank": "controlling",
        "jurisdiction_code": "US", "title": "Treas. Reg. §301.7701-3 — classification of eligible entities (check-the-box)",
        "citation": "26 CFR §301.7701-3(b) defaults / (c)(1)(iv) 60-month / (c)(1)(v) S-election", "issuer": "U.S. Treasury",
        "official_url": "https://www.law.cornell.edu/cfr/text/26/301.7701-3",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.4, "topics": ["entity_classification_8832"],
        "excerpts": [{
            "excerpt_label": "§301.7701-3(b)/(c) defaults + 60-month + S-election (verbatim substance)",
            "excerpt_text": (
                "§301.7701-3(a): a business entity that is not a per-se corporation (an 'eligible entity') can "
                "elect its classification. §301.7701-3(b)(1) domestic default: (i) a partnership if it has two or "
                "more members; (ii) disregarded as an entity separate from its owner if it has a single owner. "
                "§301.7701-3(b)(2) foreign default: partnership if 2+ members and at least one lacks limited "
                "liability; association if all members have limited liability; disregarded if a single owner "
                "without limited liability. §301.7701-3(c)(1)(iv): if an eligible entity makes an election to change "
                "its classification, it cannot change its classification by election again during the sixty months "
                "succeeding the effective date of the election (with the >50% ownership-change exception). "
                "§301.7701-3(c)(1)(v): a timely S-corporation election (Form 2553) is treated as an election to be "
                "classified as an association."
            ),
            "summary_text": "§301.7701-3(b) defaults (domestic member-count / foreign limited-liability); (c)(1)(iv) 60-month change limit; (c)(1)(v) S-election = deemed association election.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "REVPROC_2009_41", "source_type": "official_guidance", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Rev. Proc. 2009-41 — late entity-classification election relief",
        "citation": "Rev. Proc. 2009-41 (3 years 75 days; reasonable cause)", "issuer": "Internal Revenue Service",
        "official_url": "https://www.irs.gov/irb/2009-39_IRB",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.0, "topics": ["entity_classification_8832"],
        "excerpts": [{
            "excerpt_label": "Rev. Proc. 2009-41 late-relief conditions (verbatim substance)",
            "excerpt_text": (
                "An eligible entity may obtain relief for a late classification election (Form 8832 Part II) if: "
                "(1) it failed to obtain its requested classification solely because Form 8832 was not filed "
                "timely; (2) it either has not yet filed a return for the first year, or it and all affected "
                "persons filed returns consistent with the requested classification; (3) it has reasonable cause "
                "for the failure; and (4) three years and 75 days from the requested effective date of the election "
                "have not passed. File Form 8832 with the applicable service center within that 3-year-75-day "
                "window. Otherwise, relief requires a private letter ruling."
            ),
            "summary_text": "Late relief if: failed solely due to untimely filing; return consistency; reasonable cause; within 3 years 75 days of the requested effective date. Else PLR.",
            "is_key_excerpt": True,
        }],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_F8832", "8832", "governs"), ("REG_7701_3", "8832", "governs"), ("REVPROC_2009_41", "8832", "governs"),
]


F8832_FACTS: list[dict] = [
    {"fact_key": "is_per_se_corp", "label": "A per-se corporation (state-law corporation, §301.7701-2(b))? -> NOT eligible to elect", "data_type": "boolean", "required": False, "sort_order": 1},
    {"fact_key": "election_type", "label": "Type of election (L1): initial (newly-formed) or change in current classification", "data_type": "choice", "required": False, "sort_order": 2,
     "choices": ["initial", "change"]},
    {"fact_key": "prior_election_within_60mo", "label": "Previously filed an election effective within the last 60 months? (L2a)", "data_type": "boolean", "required": False, "sort_order": 3},
    {"fact_key": "prior_was_newform_initial", "label": "Was the prior election a newly-formed entity's initial election effective on formation? (L2b)", "data_type": "boolean", "required": False, "sort_order": 4,
     "notes": "If yes, the 60-month limitation does not apply."},
    {"fact_key": "is_domestic", "label": "Domestic eligible entity? (else foreign)", "data_type": "boolean", "required": False, "sort_order": 5},
    {"fact_key": "num_owners", "label": "Number of owners/members (L3: more than one owner?)", "data_type": "integer", "required": False, "sort_order": 6},
    {"fact_key": "all_members_limited_liability", "label": "Foreign entity: do ALL members have limited liability? (drives the foreign default)", "data_type": "boolean", "required": False, "sort_order": 7},
    {"fact_key": "classification_elected", "label": "Classification elected on L6 (corporation / partnership / disregarded)", "data_type": "choice", "required": False, "sort_order": 8,
     "choices": ["corporation", "partnership", "disregarded"]},
    {"fact_key": "effective_days_before_filing", "label": "Requested effective date, days before the filing date (L8; >75 clamps to 75)", "data_type": "decimal", "required": False, "sort_order": 9},
    {"fact_key": "seeking_late_relief", "label": "Seeking late-election relief (Part II, Rev. Proc. 2009-41)?", "data_type": "boolean", "required": False, "sort_order": 10},
    {"fact_key": "is_s_election", "label": "Electing S-corporation status? -> file Form 2553, NOT Form 8832", "data_type": "boolean", "required": False, "sort_order": 11},
]

F8832_RULES: list[dict] = [
    {"rule_id": "R-8832-ELIG", "title": "Part I eligibility to elect (per-se corp / 60-month)", "rule_type": "routing",
     "formula": "if is_per_se_corp: (False, per_se_corp) ; elif election_type == change and prior_election_within_60mo and not prior_was_newform_initial: (False, sixty_month_block) ; else: (True, eligible)",
     "inputs": ["is_per_se_corp", "election_type", "prior_election_within_60mo", "prior_was_newform_initial"], "outputs": ["is_eligible_to_elect", "eligibility_reason"], "sort_order": 1,
     "description": "W1. A per-se corporation (a state-law corporation, §301.7701-2(b)) is not an eligible entity and cannot elect. A change-of-classification election is blocked when a prior election took effect within the last 60 months and that prior election was NOT a newly-formed entity's initial election (the L2a/L2b gate, §301.7701-3(c)(1)(iv))."},
    {"rule_id": "R-8832-DEFAULT", "title": "Default classification (§301.7701-3(b))", "rule_type": "calculation",
     "formula": "domestic: partnership if num_owners>=2 else disregarded ; foreign: (corporation if all_members_limited_liability else partnership) if num_owners>=2 else (corporation if all_members_limited_liability else disregarded)",
     "inputs": ["is_domestic", "num_owners", "all_members_limited_liability"], "outputs": ["default_classification"], "sort_order": 2,
     "description": "W2. The default if the entity does NOT file: a domestic eligible entity is a partnership (2+ members) or disregarded (1 member); a foreign eligible entity is an association/corporation if all members have limited liability, else a partnership (2+) or disregarded (single member without limited liability). A new entity intending to use its default should not file Form 8832."},
    {"rule_id": "R-8832-OPTIONS", "title": "Available classifications by owner count (L3)", "rule_type": "calculation",
     "formula": "available = [partnership, corporation] if num_owners >= 2 else [corporation, disregarded]",
     "inputs": ["num_owners"], "outputs": ["available_classifications"], "sort_order": 3,
     "description": "W1. L3: an entity with more than one owner can elect to be a partnership or an association taxable as a corporation; an entity with a single owner can elect to be an association taxable as a corporation or to be disregarded as a separate entity."},
    {"rule_id": "R-8832-EFFDATE", "title": "Effective-date window (75 days before / 12 months after)", "rule_type": "validation",
     "formula": "effective no more than 75 days before filing (else defaults to 75 before) nor later than 12 months after (else defaults to 12 months after); blank -> date filed",
     "inputs": ["effective_days_before_filing"], "outputs": ["clamped_days_before"], "sort_order": 4,
     "description": "W3. L8: the election can take effect no more than 75 days before the filing date, nor later than 12 months after. An effective date more than 75 days before filing defaults to 75 days before; more than 12 months after defaults to 12 months after; a blank line 8 defaults to the date filed."},
]

F8832_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-8832-ELIG", "IRS_F8832", "primary", "Part I L1-L2b"),
    ("R-8832-ELIG", "REG_7701_3", "primary", "§301.7701-3(c)(1)(iv) 60-month"),
    ("R-8832-DEFAULT", "REG_7701_3", "primary", "§301.7701-3(b) defaults"),
    ("R-8832-DEFAULT", "IRS_F8832", "secondary", "Domestic/foreign default rule"),
    ("R-8832-OPTIONS", "IRS_F8832", "primary", "L3 owner count"),
    ("R-8832-EFFDATE", "IRS_F8832", "primary", "L8 effective date window"),
]

F8832_LINES: list[dict] = [
    {"line_number": "P1_ELIG", "description": "Part I eligibility -> is_eligible_to_elect", "line_type": "calculated", "source_rules": ["R-8832-ELIG"], "sort_order": 1},
    {"line_number": "L3_OPTIONS", "description": "Available classifications by owner count", "line_type": "calculated", "source_rules": ["R-8832-OPTIONS"], "sort_order": 2},
    {"line_number": "DEFAULT", "description": "Default classification if not electing", "line_type": "calculated", "source_rules": ["R-8832-DEFAULT"], "sort_order": 3},
    {"line_number": "L8_EFF", "description": "Effective date (75-day/12-month window)", "line_type": "input", "source_rules": ["R-8832-EFFDATE"], "sort_order": 4},
]

F8832_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_8832_PERSE", "title": "A per-se corporation cannot make this election", "severity": "error",
     "condition": "is_per_se_corp",
     "message": "A corporation organized under a federal or state corporation statute (a 'per-se' corporation, Reg. §301.7701-2(b)) is NOT an eligible entity and cannot elect its classification on Form 8832. Only eligible entities (e.g., LLCs, partnerships, certain foreign entities) may elect.",
     "notes": "W1."},
    {"diagnostic_id": "D_8832_60MONTH", "title": "60-month limitation may block a change election", "severity": "warning",
     "condition": "election_type == change and prior_election_within_60mo and not prior_was_newform_initial",
     "message": "Once an eligible entity elects to change its classification, it generally cannot change again during the 60 months after the effective date (Reg. §301.7701-3(c)(1)(iv)). Because a prior election took effect within the last 60 months (and was not a newly-formed entity's initial election), you are generally not currently eligible - unless more than 50% of the ownership changed (available only by private letter ruling).",
     "notes": "W1."},
    {"diagnostic_id": "D_8832_DEFAULT", "title": "Default classification — don't file if you're using it", "severity": "info",
     "condition": "num_owners > 0",
     "message": "If you do not file Form 8832, a domestic eligible entity is a partnership (2+ members) or disregarded (single owner); a foreign eligible entity's default depends on whether all members have limited liability. A NEW entity that will use its default classification should NOT file Form 8832 - filing is only needed to elect a DIFFERENT classification.",
     "notes": "W2."},
    {"diagnostic_id": "D_8832_EFFDATE", "title": "Effective date: 75 days before / 12 months after filing", "severity": "warning",
     "condition": "effective_days_before_filing > 75",
     "message": "The election on line 8 can take effect no more than 75 days before the date it is filed, nor later than 12 months after. An effective date more than 75 days before filing will default to 75 days before the filing date (and more than 12 months after defaults to 12 months after). A blank line 8 defaults to the date filed.",
     "notes": "W3."},
    {"diagnostic_id": "D_8832_LATE", "title": "Late-election relief (Rev. Proc. 2009-41)", "severity": "info",
     "condition": "seeking_late_relief",
     "message": "If Form 8832 was not filed timely, you may still obtain relief under Rev. Proc. 2009-41 (Part II) if: the entity failed to get its classification solely because the form was not filed timely; the return-consistency condition is met; the entity has reasonable cause; and 3 years and 75 days from the requested effective date have NOT passed. File within that window; otherwise relief requires a private letter ruling.",
     "notes": "W3."},
    {"diagnostic_id": "D_8832_2553", "title": "Electing S-corp? Use Form 2553, not Form 8832", "severity": "warning",
     "condition": "is_s_election",
     "message": "Do not file Form 8832 to elect S-corporation status. A timely Form 2553 (S-corporation election) is deemed under Reg. §301.7701-3(c)(1)(v) to also elect classification as an association taxable as a corporation - so a separate Form 8832 is not required (or permitted) for the S election. File Form 2553.",
     "notes": "W4."},
    {"diagnostic_id": "D_8832_FILING", "title": "File + attach a copy to the return (updated addresses)", "severity": "info",
     "condition": "not is_per_se_corp",
     "message": "File Form 8832 with the IRS service center for your state and ATTACH a copy to the entity's federal return (or, if the entity files no return, to all direct/indirect owners' returns) for the election year. Failure to attach won't invalidate a valid election but may draw penalties. Use the UPDATED addresses: Kansas City, MO 64999 (eastern states) / Ogden, UT 84201 (western states) / Ogden, UT 84201-0023 (foreign) - the Cincinnati addresses in the printed instructions are superseded.",
     "notes": "W4. Addresses changed post-2013."},
    {"diagnostic_id": "D_8832_FOREIGN", "title": "Foreign entity default turns on limited liability", "severity": "info",
     "condition": "not is_domestic",
     "message": "A foreign eligible entity's default classification depends on member liability: a partnership if it has two or more members and at least one does NOT have limited liability; an association taxable as a corporation if ALL members have limited liability; disregarded if it has a single owner that does not have limited liability. Report the foreign country of organization on line 7.",
     "notes": "W2."},
]

F8832_SCENARIOS: list[dict] = [
    {"scenario_name": "8832-A — domestic SMLLC elects corporation", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"is_per_se_corp": False, "election_type": "initial", "is_domestic": True, "num_owners": 1, "classification_elected": "corporation"},
     "expected_outputs": {"is_eligible_to_elect": True, "default_classification": "disregarded", "available_classifications": ["corporation", "disregarded"]},
     "notes": "A domestic single-member LLC (default disregarded) elects to be an association taxable as a corporation (L6c/6a); eligible; options = corp or disregarded."},
    {"scenario_name": "8832-B — domestic 2-member LLC (default partnership)", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"is_per_se_corp": False, "election_type": "initial", "is_domestic": True, "num_owners": 2, "classification_elected": "corporation"},
     "expected_outputs": {"is_eligible_to_elect": True, "default_classification": "partnership", "available_classifications": ["partnership", "corporation"]},
     "notes": "A domestic 2-member LLC (default partnership) can elect partnership or corporation; here it elects association-taxable-as-corp."},
    {"scenario_name": "8832-C — 60-month limitation blocks the change", "scenario_type": "failure", "sort_order": 3,
     "inputs": {"is_per_se_corp": False, "election_type": "change", "prior_election_within_60mo": True, "prior_was_newform_initial": False},
     "expected_outputs": {"is_eligible_to_elect": False, "eligibility_reason": "sixty_month_block", "diagnostic": "D_8832_60MONTH"},
     "notes": "A change election with a prior election within the last 60 months (not a newly-formed initial election) -> generally not currently eligible."},
    {"scenario_name": "8832-D — 60-month exception (prior was newly-formed initial)", "scenario_type": "edge", "sort_order": 4,
     "inputs": {"is_per_se_corp": False, "election_type": "change", "prior_election_within_60mo": True, "prior_was_newform_initial": True},
     "expected_outputs": {"is_eligible_to_elect": True, "eligibility_reason": "eligible"},
     "notes": "The 60-month limit does not apply when the prior election was a newly-formed entity's initial election effective on formation -> eligible."},
    {"scenario_name": "8832-E — per-se corporation is ineligible", "scenario_type": "failure", "sort_order": 5,
     "inputs": {"is_per_se_corp": True, "election_type": "initial"},
     "expected_outputs": {"is_eligible_to_elect": False, "eligibility_reason": "per_se_corp", "diagnostic": "D_8832_PERSE"},
     "notes": "A state-law corporation is a per-se corporation and cannot elect on Form 8832."},
    {"scenario_name": "8832-F — foreign all-limited-liability defaults to corporation", "scenario_type": "edge", "sort_order": 6,
     "inputs": {"is_per_se_corp": False, "election_type": "initial", "is_domestic": False, "num_owners": 2, "all_members_limited_liability": True, "classification_elected": "partnership"},
     "expected_outputs": {"default_classification": "corporation", "diagnostic": "D_8832_FOREIGN"},
     "notes": "A foreign 2-member entity where all members have limited liability defaults to an association (corporation); here it elects partnership instead."},
    {"scenario_name": "8832-G — effective-date clamp + S-election boundary", "scenario_type": "edge", "sort_order": 7,
     "inputs": {"is_per_se_corp": False, "election_type": "initial", "effective_days_before_filing": 100, "is_s_election": True},
     "expected_outputs": {"clamped_days_before": 75.0, "diagnostic": "D_8832_2553"},
     "notes": "An effective date 100 days before filing clamps to 75; and an S-election should be made on Form 2553, not Form 8832."},
]

FORMS: list[dict] = [
    {
        "identity": {"form_number": "8832", "form_title": "Form 8832 — Entity Classification Election (Rev. 12-2013)",
                     "notes": "WO-22 (SPINE S-16, 9th; DECISIONS D-24). Structural election (Reg. §301.7701-3), not a tax computation. Part I decision tree -> is_eligible_to_elect (per-se corp ineligible; 60-month block at L2a/L2b) + available classifications (>1 owner = partnership/corp; 1 owner = corp/disregarded). Default: domestic 2+ = partnership / 1 = disregarded; foreign by limited liability. Effective date window 75 days before / 12 months after (clamp). Late relief Rev. Proc. 2009-41 (3 yrs 75 days + reasonable cause). S-election -> Form 2553 (not 8832). Attach a copy to the return; updated addresses Kansas City MO 64999 / Ogden UT 84201. entity_types [1065,1120,1120S,1040]. Rev. 12-2013 (no annual reissue); no OBBBA impact - re-verify the revision each season."},
        "facts": F8832_FACTS, "rules": F8832_RULES, "rule_links": F8832_RULE_LINKS,
        "lines": F8832_LINES, "diagnostics": F8832_DIAGNOSTICS, "scenarios": F8832_SCENARIOS,
    },
]

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-8832-ELIG", "title": "Eligibility follows the per-se-corp + 60-month gates", "assertion_type": "reconciliation",
     "entity_types": ["1065", "1120", "1120S", "1040"], "status": "draft", "sort_order": 1,
     "description": "is_eligible_to_elect is False for a per-se corporation, and for a change election with a prior election within 60 months that was not a newly-formed initial election; otherwise True.",
     "definition": {"rule": "R-8832-ELIG", "check": "is_eligible_to_elect = not is_per_se_corp and not (change and prior_within_60mo and not prior_newform_initial)"}},
    {"assertion_id": "FA-8832-DEFAULT", "title": "Default classification by member count / limited liability", "assertion_type": "reconciliation",
     "entity_types": ["1065", "1120", "1120S", "1040"], "status": "draft", "sort_order": 2,
     "description": "Domestic default = partnership (2+) / disregarded (1); foreign default = corporation (all limited liability) else partnership/disregarded.",
     "definition": {"rule": "R-8832-DEFAULT", "check": "domestic: partnership if owners>=2 else disregarded"}},
    {"assertion_id": "FA-8832-2553", "title": "An S-election uses Form 2553, not Form 8832", "assertion_type": "reconciliation",
     "entity_types": ["1120S"], "status": "draft", "sort_order": 3,
     "description": "A timely Form 2553 is deemed a §301.7701-3(c)(1)(v) association election, so no separate Form 8832 is filed for an S-corporation election.",
     "definition": {"rule": "R-8832-ELIG", "check": "is_s_election -> file Form 2553 (not 8832)"}},
]


class Command(BaseCommand):
    help = "Load the Form 8832 spec (Entity Classification Election, Rev. 12-2013). Refuses to seed until READY_TO_SEED=True (W1-W4)."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad Form 8832 spec (Entity Classification Election)\n"))
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
                "\nREFUSING TO SEED FORM 8832: not cleared.\n\n"
                "Gated until Ken reviews (W1 eligibility tree; W2 default classification; W3 effective\n"
                "window + late relief; W4 2553 boundary + addresses) and flips the sentinel.\n\n"
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
        self.stdout.write("Form 8832 loaded.")
        self.stdout.write(f"  8832: facts {len(F8832_FACTS)} / rules {len(F8832_RULES)} / lines {len(F8832_LINES)} / diag {len(F8832_DIAGNOSTICS)} / tests {len(F8832_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}")
        self.stdout.write("=" * 60)
