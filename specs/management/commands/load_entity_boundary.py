"""Load the ENTITY_BOUNDARY spec — Core boundary diagnostics for entity returns.

S-5 boundary diagnostics, WO-04. Authored 2026-07-05 through the WORK_ORDERS front door.
Scope = a SINGLE consolidated "completeness critic" form (Ken, Gate-1 walk 2026-07-05) that
DETECTS when a 1065/1120-S return crosses into module territory the software does not handle
this season, and throws a loud RED diagnostic naming what the return needs. PRODUCT_MAP §17:
"module boundaries are DIAGNOSTIC boundaries — Core never goes silent at a boundary."

Boundaries wired (verified 2026-07-05, boundary_diag_source_brief.md — NOT from memory):
  B1 Schedule M-3 threshold   — 1065: assets/adj-assets >=$10M OR receipts >=$35M OR REP >=50%;
                                 1120-S: total assets >=$10M.
  B2 K-2/K-3 Domestic Filing Exception — COMPUTE the 4-criteria gate; fire RED when DFE FAILS
                                 (the affirmative "why K-2/K-3 aren't required" is Core, PRODUCT_MAP).
  B3 §704(c) built-in gain/loss — indicator: contributed property FMV != basis, OR a book-up
                                 (reverse §704(c)).
  B4 §754 / §743(b) / §734(b)  — indicator: §754 election on file, OR >$250k substantial built-in
                                 loss (§743(d)), OR >$250k substantial basis reduction (§734(d)).
  B5 Multistate apportionment  — indicator: nexus/activity beyond the supported states
                                 (GA + SC/AL/NC/FL/TN), not fully P.L. 86-272 protected. State-specific.

These CONSOLIDATE the existing on-form flags (D_L_M3 on 1065_L, D_SCHK_K3 / D_SCHK_704C on
SCH_K_1065, Sch B Q10 §754) into one auditable season-one safety net with pinned thresholds; the
on-form flags remain. §461(l) boundary = the separate Form 461 (S-6). 1041 Sch I AMT = deferred to
S-11 (D-2). OBBBA changed NONE of these mechanics (verified).

SAFETY GUARD: READY_TO_SEED stays False until Ken's review walk (the M-3 thresholds + the DFE
4-criteria gate + the $250k §743/§734 triggers + the apportionment/P.L. 86-272 scope).
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


READY_TO_SEED = True  # FLIPPED 2026-07-05 — Ken approved the S-5 review walk ("Approve — flip, seed, export").


FORM_JURISDICTION = "FED"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_ENTITY_TYPES = ["1065", "1120S"]
FORM_STATUS = "draft"


# ═══════════════════════════════════════════════════════════════════════════
# VERIFIED CONSTANTS — boundary thresholds (2025)
# ═══════════════════════════════════════════════════════════════════════════

M3_ASSET_THRESHOLD = 10_000_000        # 1065 & 1120-S Schedule L total assets
M3_RECEIPTS_THRESHOLD_1065 = 35_000_000  # 1065 total receipts (no 1120-S receipts prong)
M3_REP_PCT = 50                        # 1065 reportable-entity-partner ownership %
DFE_FOREIGN_TAX_LIMIT = 300            # K-2/K-3 DFE: limited-foreign-activity foreign-tax ceiling
SUBSTANTIAL_250K = 250_000             # §743(d) built-in loss / §734(d) basis reduction


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY (boundary-owned sources — self-contained, distinct codes)
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("entity_boundary", "Entity return boundary diagnostics (M-3, K-2/K-3 DFE, §704(c), §754, multistate apportionment)"),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_2025_M3_1065",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED", "entity_type_code": "1065",
        "tax_year_start": 2025, "tax_year_end": 2025,
        "title": "Instructions for Schedule M-3 (Form 1065) — Who Must File",
        "citation": "Instructions for Schedule M-3 (Form 1065), Rev. 11/2023 (controlling for TY2025)",
        "issuer": "IRS", "official_url": "https://www.irs.gov/instructions/i1065sm3",
        "current_status": "active", "is_substantive_authority": False, "is_filing_authority": True,
        "trust_score": 9.40, "requires_human_review": True,
        "notes": "M-3 (1065) not annually reissued — Rev. 11/2023 controls TY2025; re-confirm each season. Thresholds $10M assets / $35M receipts / 50% REP unchanged.",
        "topics": ["entity_boundary"],
        "excerpts": [
            {"excerpt_label": "M-3 (1065) Who Must File", "location_reference": "Instr. Sch. M-3 (1065) Rev. 11/2023",
             "excerpt_text": ("A partnership must complete Schedule M-3 if any of: (1) total assets at year end "
                              "(Schedule L, line 14, col. (d)) are $10 million or more; (2) adjusted total assets "
                              "are $10 million or more; (3) total receipts are $35 million or more; or (4) a "
                              "reportable entity partner owns or is deemed to own, directly or indirectly, 50% or "
                              "more of the partnership's capital, profit, or loss on any day of the tax year. "
                              "Partnerships not required to file Schedule M-3 may file it voluntarily."),
             "summary_text": "M-3 (1065): assets>=$10M OR adj assets>=$10M OR receipts>=$35M OR REP>=50%.",
             "is_key_excerpt": True},
        ],
    },
    {
        "source_code": "IRS_2025_M3_1120S",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED", "entity_type_code": "1120S",
        "tax_year_start": 2025, "tax_year_end": 2025,
        "title": "Instructions for Schedule M-3 (Form 1120-S) — Who Must File",
        "citation": "Instructions for Schedule M-3 (Form 1120-S), Rev. 12/2019 (controlling for TY2025)",
        "issuer": "IRS", "official_url": "https://www.irs.gov/instructions/i1120ss3",
        "current_status": "active", "is_substantive_authority": False, "is_filing_authority": True,
        "trust_score": 9.40, "requires_human_review": True,
        "notes": "M-3 (1120-S) latest revision is 12/2019 (controls TY2025 — do NOT cite the 1120 June-2025 revision). Single $10M total-assets test; at >=$50M complete M-3 fully.",
        "topics": ["entity_boundary"],
        "excerpts": [
            {"excerpt_label": "M-3 (1120-S) Who Must File", "location_reference": "Instr. Sch. M-3 (1120-S) Rev. 12/2019",
             "excerpt_text": ("Any corporation required to file Form 1120-S that reports on Schedule L total "
                              "assets at the end of the tax year that equal or exceed $10 million must file "
                              "Schedule M-3. At $50 million or more the corporation must complete Schedule M-3 "
                              "entirely; between $10M and $50M it may complete Part I plus Schedule M-1."),
             "summary_text": "M-3 (1120-S): total assets>=$10M (single test).",
             "is_key_excerpt": True},
        ],
    },
    {
        "source_code": "IRS_2025_K2K3_1065",
        "source_type": "official_instructions",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED", "entity_type_code": "1065",
        "tax_year_start": 2025, "tax_year_end": 2025,
        "title": "2025 Partnership Instructions for Schedules K-2 and K-3 (Form 1065) — Domestic Filing Exception",
        "citation": "2025 Instructions for Schedules K-2/K-3 (Form 1065), 'Domestic filing exception'",
        "issuer": "IRS", "official_url": "https://www.irs.gov/instructions/i1065s23",
        "current_status": "active", "is_substantive_authority": False, "is_filing_authority": True,
        "trust_score": 9.50, "requires_human_review": True,
        "notes": "The four DFE criteria. The boundary fires when the DFE FAILS (K-2/K-3 then required). PRODUCT_MAP makes the DFE determination Core season one.",
        "topics": ["entity_boundary"],
        "excerpts": [
            {"excerpt_label": "Domestic filing exception — the four criteria", "location_reference": "i1065s23 (2025)",
             "excerpt_text": ("A domestic partnership need not complete or file Schedules K-2 and K-3, or furnish "
                              "a K-3 to a partner (except on request), if for the tax year ALL of: (1) No or "
                              "limited foreign activity — no foreign activity, or only passive-category foreign "
                              "income with not more than $300 of foreign taxes allowable as a credit and shown on "
                              "a payee statement; (2) all direct partners are specified U.S. persons (U.S.-citizen "
                              "or resident-alien individuals, certain domestic estates/trusts, an S corporation "
                              "with a sole shareholder, an SMLLC owned by such a person, or a domestic partnership "
                              "of such partners); (3) partner notification — by the date the partnership furnishes "
                              "the Schedule K-1, that partners will not receive Schedule K-3 unless requested; and "
                              "(4) no partner requests Schedule K-3 on or before the 1-month date (1 month before "
                              "the partnership files Form 1065)."),
             "summary_text": "DFE met iff all 4: no/limited foreign activity (<=$300 tax); only listed U.S. partners; K-1 notification; no K-3 request by the 1-month date. Fails => K-2/K-3 required.",
             "is_key_excerpt": True},
        ],
    },
    {
        "source_code": "TREAS_REG_704_3",
        "source_type": "regulation",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED", "entity_type_code": "1065",
        "tax_year_start": 2025, "tax_year_end": 2025,
        "title": "Treas. Reg. §1.704-3 — Contributed Property (§704(c) methods)",
        "citation": "26 CFR §1.704-3 (traditional / curative / remedial; (a)(6) reverse §704(c)); IRC §704(c)",
        "issuer": "U.S. Treasury / IRS", "official_url": "https://www.law.cornell.edu/cfr/text/26/1.704-3",
        "current_status": "active", "is_substantive_authority": True, "is_filing_authority": False,
        "trust_score": 10.00, "requires_human_review": False,
        "notes": "§704(c) applies to contributed property with FMV != tax basis (a reasonable method is mandatory) and to reverse §704(c) on book-ups. Method selection/tracking is Complex Entity Pro — boundary flag only.",
        "topics": ["entity_boundary"],
        "excerpts": [
            {"excerpt_label": "§704(c) — built-in gain/loss; methods", "location_reference": "26 CFR §1.704-3(a),(b),(c),(d); IRC §704(c)",
             "excerpt_text": ("Section 704(c) requires income, gain, loss, and deduction with respect to property "
                              "contributed to the partnership to be shared among the partners so as to take account "
                              "of the variation between the basis of the property to the partnership and its fair "
                              "market value at the time of contribution. A reasonable method must be used: the "
                              "traditional method (§1.704-3(b)), the traditional method with curative allocations "
                              "(§1.704-3(c)), or the remedial method (§1.704-3(d)). Reverse §704(c): revaluations "
                              "(book-ups) create disparities subject to the same principles (§1.704-3(a)(6))."),
             "summary_text": "§704(c): contributed property FMV != basis (mandatory method) or a book-up => track built-in gain/loss by a reasonable method.",
             "is_key_excerpt": True},
        ],
    },
    {
        "source_code": "IRC_754_743_734",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED", "entity_type_code": "1065",
        "tax_year_start": 2025, "tax_year_end": 2025,
        "title": "IRC §754 / §743(b),(d) / §734(b),(d) — optional basis adjustments",
        "citation": "26 U.S.C. §754 (election); §743(d) ($250k substantial built-in loss); §734(d) ($250k substantial basis reduction)",
        "issuer": "U.S. Congress", "official_url": "https://www.law.cornell.edu/uscode/text/26/754",
        "current_status": "active", "is_substantive_authority": True, "is_filing_authority": False,
        "trust_score": 10.00, "requires_human_review": False,
        "notes": "A §754 election applies to that year and all subsequent (revocable only with IRS consent). Even without it: §743(b) mandatory on a transfer with >$250k substantial built-in loss; §734(b) mandatory on a distribution with >$250k substantial basis reduction. Basis-adjust math is Complex Entity Pro — boundary flag only.",
        "topics": ["entity_boundary"],
        "excerpts": [
            {"excerpt_label": "§754 election + §743(d)/§734(d) mandatory triggers", "location_reference": "26 U.S.C. §754, §743(d), §734(d)",
             "excerpt_text": ("§754: a partnership may elect to adjust the basis of partnership property on a "
                              "distribution (§734) and on a transfer of an interest (§743); the election applies to "
                              "the year made and all subsequent years until revoked with IRS consent. §743(d): a "
                              "substantial built-in loss exists (mandatory §743(b) adjustment, even without a §754 "
                              "election) if the partnership's adjusted basis in its property exceeds its FMV by more "
                              "than $250,000 (or a transferee would be allocated a >$250,000 loss on a hypothetical "
                              "FMV sale). §734(d): a substantial basis reduction (mandatory §734(b) adjustment) "
                              "exists if the sum of the §734(b)(2) amounts exceeds $250,000."),
             "summary_text": "§754 on file => track §743(b)/§734(b). Mandatory even without: >$250k substantial built-in loss (§743(d)) / >$250k substantial basis reduction (§734(d)).",
             "is_key_excerpt": True},
        ],
    },
    {
        "source_code": "PL_86_272",
        "source_type": "statute",
        "source_rank": "primary_official",
        "jurisdiction_code": "FED", "entity_type_code": "1065",
        "tax_year_start": 2025, "tax_year_end": 2025,
        "title": "P.L. 86-272 (Interstate Income Act of 1959) — 15 U.S.C. §381",
        "citation": "15 U.S.C. §381 (net-income-tax immunity for mere solicitation of tangible-goods orders)",
        "issuer": "U.S. Congress", "official_url": "https://www.law.cornell.edu/uscode/text/15/381",
        "current_status": "active", "is_substantive_authority": True, "is_filing_authority": False,
        "trust_score": 9.00, "requires_human_review": True,
        "notes": "The one federal anchor for the multistate apportionment boundary. Shields net-income tax where the only in-state activity is solicitation of orders for tangible personal property filled from out of state. Does NOT cover services/digital, franchise/gross-receipts taxes; eroded for internet activity. Per-state apportionment thresholds VARY and are re-verified per state.",
        "topics": ["entity_boundary"],
        "excerpts": [
            {"excerpt_label": "P.L. 86-272 — solicitation immunity", "location_reference": "15 U.S.C. §381",
             "excerpt_text": ("No State shall have power to impose a net income tax on income derived within the "
                              "State from interstate commerce if the only business activities within the State are "
                              "the solicitation of orders for sales of tangible personal property, which orders are "
                              "sent outside the State for approval and are filled by shipment or delivery from a "
                              "point outside the State."),
             "summary_text": "P.L. 86-272 immunizes NET-INCOME tax where in-state activity is only solicitation of tangible-goods orders filled from out of state. Not franchise/gross-receipts/services/digital.",
             "is_key_excerpt": True},
        ],
    },
]

NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = []

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_2025_M3_1065", "ENTITY_BOUNDARY", "governs"),
    ("IRS_2025_M3_1120S", "ENTITY_BOUNDARY", "governs"),
    ("IRS_2025_K2K3_1065", "ENTITY_BOUNDARY", "governs"),
    ("TREAS_REG_704_3", "ENTITY_BOUNDARY", "governs"),
    ("IRC_754_743_734", "ENTITY_BOUNDARY", "governs"),
    ("PL_86_272", "ENTITY_BOUNDARY", "informs"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM: ENTITY_BOUNDARY (consolidated Core boundary diagnostics)
# ═══════════════════════════════════════════════════════════════════════════

EB_IDENTITY = {
    "form_number": "ENTITY_BOUNDARY",
    "form_title": "Entity Return Boundary Diagnostics (Core season-one safety net, TY2025)",
    "notes": (
        "S-5 (WO-04), authored 2026-07-05. A consolidated 'completeness critic' for 1065/1120-S "
        "returns: DETECTS when a return crosses into module territory not supported this season and "
        "throws a loud RED diagnostic (PRODUCT_MAP §17). Boundaries: M-3 threshold; K-2/K-3 DFE "
        "(the 4-criteria gate, COMPUTED — RED when the exception fails); §704(c) contributed-property/"
        "book-up indicator; §754/§743(b)/§734(b) (election or >$250k mandatory triggers); multistate "
        "apportionment beyond the supported states (P.L. 86-272 anchor). Thresholds verified "
        "(boundary_diag_source_brief.md). Consolidates the existing on-form flags (D_L_M3, D_SCHK_K3, "
        "D_SCHK_704C, Sch B Q10) into one auditable set; those remain in place. §461(l) = Form 461 "
        "(S-6); 1041 Sch I AMT deferred to S-11 (D-2). ⚠ M-3 instruction revisions are not annual "
        "(1065 Rev 11/2023, 1120-S Rev 12/2019 — controlling for TY2025); apportionment thresholds "
        "are state-specific and re-verified per state."
    ),
}

EB_FACTS: list[dict] = [
    {"fact_key": "eb_is_scorp", "label": "Entity is an 1120-S (S corp)? (else 1065 partnership)",
     "data_type": "boolean", "default_value": "false", "sort_order": 1,
     "notes": "Branches the M-3 test: 1120-S = $10M assets only; 1065 = 4-prong."},
    # ── B1 Schedule M-3 ──
    {"fact_key": "eb_total_assets", "label": "Schedule L line 14 — total assets (EOY)",
     "data_type": "decimal", "default_value": "0", "sort_order": 2, "notes": "M-3 test input."},
    {"fact_key": "eb_adj_total_assets", "label": "Adjusted total assets (M-3 worksheet, 1065)",
     "data_type": "decimal", "default_value": "0", "sort_order": 3, "notes": "1065 M-3 prong (anti-understatement)."},
    {"fact_key": "eb_total_receipts", "label": "Total receipts (1065)",
     "data_type": "decimal", "default_value": "0", "sort_order": 4, "notes": "1065 M-3 $35M prong."},
    {"fact_key": "eb_rep_50", "label": "A reportable entity partner owns/deemed-owns >=50% (1065)?",
     "data_type": "boolean", "default_value": "false", "sort_order": 5, "notes": "1065 M-3 REP prong."},
    {"fact_key": "eb_m3_required", "label": "Schedule M-3 required (OUTPUT)",
     "data_type": "boolean", "sort_order": 6, "notes": "OUTPUT of R-EB-M3."},
    # ── B2 K-2/K-3 Domestic Filing Exception ──
    {"fact_key": "eb_foreign_activity", "label": "Any foreign activity?",
     "data_type": "boolean", "default_value": "false", "sort_order": 7, "notes": "DFE criterion 1. Foreign taxes/income, foreign entity interest, branch/DE."},
    {"fact_key": "eb_foreign_tax_over_300", "label": "Foreign taxes > $300 (or non-passive foreign income)?",
     "data_type": "boolean", "default_value": "false", "sort_order": 8, "notes": "DFE criterion 1 disqualifier (>$300 FTC ceiling)."},
    {"fact_key": "eb_partners_all_listed", "label": "All direct partners are the listed U.S.-person types?",
     "data_type": "boolean", "default_value": "true", "sort_order": 9, "notes": "DFE criterion 2."},
    {"fact_key": "eb_dfe_notice_given", "label": "Partner K-3 notification given by the K-1 date?",
     "data_type": "boolean", "default_value": "true", "sort_order": 10, "notes": "DFE criterion 3."},
    {"fact_key": "eb_k3_requested_by_1mo", "label": "Any partner requested K-3 by the 1-month date?",
     "data_type": "boolean", "default_value": "false", "sort_order": 11, "notes": "DFE criterion 4 (a request DEFEATS the exception)."},
    {"fact_key": "eb_dfe_met", "label": "Domestic filing exception met (OUTPUT)",
     "data_type": "boolean", "sort_order": 12, "notes": "OUTPUT. All 4 criteria met."},
    {"fact_key": "eb_k2k3_required", "label": "K-2/K-3 required (DFE failed) (OUTPUT)",
     "data_type": "boolean", "sort_order": 13, "notes": "OUTPUT. NOT eb_dfe_met."},
    # ── B3 §704(c) ──
    {"fact_key": "eb_contributed_builtin", "label": "Property contributed with FMV != tax basis?",
     "data_type": "boolean", "default_value": "false", "sort_order": 14, "notes": "Forward §704(c)."},
    {"fact_key": "eb_capital_revaluation", "label": "Capital-account book-up/book-down (revaluation)?",
     "data_type": "boolean", "default_value": "false", "sort_order": 15, "notes": "Reverse §704(c)."},
    {"fact_key": "eb_704c_present", "label": "§704(c) built-in gain/loss present (OUTPUT)",
     "data_type": "boolean", "sort_order": 16, "notes": "OUTPUT of R-EB-704C."},
    # ── B4 §754 / §743(b) / §734(b) ──
    {"fact_key": "eb_754_on_file", "label": "§754 election in effect?",
     "data_type": "boolean", "default_value": "false", "sort_order": 17, "notes": "Every later transfer/distribution now adjusts basis."},
    {"fact_key": "eb_builtin_loss_250k", "label": "Interest transfer with >$250k substantial built-in loss (§743(d))?",
     "data_type": "boolean", "default_value": "false", "sort_order": 18, "notes": "Mandatory §743(b) even without a §754 election."},
    {"fact_key": "eb_basis_reduction_250k", "label": "Distribution with >$250k substantial basis reduction (§734(d))?",
     "data_type": "boolean", "default_value": "false", "sort_order": 19, "notes": "Mandatory §734(b) even without a §754 election."},
    {"fact_key": "eb_743_734_indicated", "label": "§743(b)/§734(b) basis adjustment indicated (OUTPUT)",
     "data_type": "boolean", "sort_order": 20, "notes": "OUTPUT of R-EB-754."},
    # ── B5 multistate apportionment ──
    {"fact_key": "eb_nexus_beyond_states", "label": "Nexus/activity in a state beyond GA + SC/AL/NC/FL/TN?",
     "data_type": "boolean", "default_value": "false", "sort_order": 21, "notes": "Property/payroll/sales in a non-supported state."},
    {"fact_key": "eb_pl86272_protected", "label": "Activity fully P.L. 86-272 protected (solicitation of tangible goods)?",
     "data_type": "boolean", "default_value": "false", "sort_order": 22, "notes": "Immunity from NET-income tax (not franchise/gross-receipts/services/digital)."},
    {"fact_key": "eb_apportionment_boundary", "label": "Multistate apportionment beyond scope (OUTPUT)",
     "data_type": "boolean", "sort_order": 23, "notes": "OUTPUT of R-EB-APPORTION."},
]

EB_RULES: list[dict] = [
    {"rule_id": "R-EB-M3", "title": "Schedule M-3 threshold (1065 4-prong / 1120-S $10M)", "rule_type": "calculation",
     "precedence": 1, "sort_order": 1,
     "formula": ("eb_m3_required = (eb_is_scorp AND eb_total_assets >= 10,000,000) OR (NOT eb_is_scorp AND "
                 "(eb_total_assets >= 10,000,000 OR eb_adj_total_assets >= 10,000,000 OR eb_total_receipts >= "
                 "35,000,000 OR eb_rep_50)). 1120-S = single $10M total-assets test; 1065 = assets / adjusted "
                 "assets $10M OR receipts $35M OR a >=50% reportable entity partner."),
     "inputs": ["eb_is_scorp", "eb_total_assets", "eb_adj_total_assets", "eb_total_receipts", "eb_rep_50"],
     "outputs": ["eb_m3_required"],
     "description": "B1. Pinned thresholds; fires D_EB_M3 (RED — M-3 not supported season one)."},
    {"rule_id": "R-EB-DFE", "title": "K-2/K-3 Domestic Filing Exception — 4-criteria gate", "rule_type": "calculation",
     "precedence": 2, "sort_order": 2,
     "formula": ("eb_dfe_met = (NOT eb_foreign_activity OR NOT eb_foreign_tax_over_300) AND eb_partners_all_listed "
                 "AND eb_dfe_notice_given AND (NOT eb_k3_requested_by_1mo). eb_k2k3_required = NOT eb_dfe_met. "
                 "Criterion 1 = no foreign activity, or foreign activity limited to passive income with <=$300 "
                 "foreign tax; criterion 2 = only listed U.S.-person direct partners; criterion 3 = K-3 "
                 "notification by the K-1 date; criterion 4 = no K-3 request by the 1-month date."),
     "inputs": ["eb_foreign_activity", "eb_foreign_tax_over_300", "eb_partners_all_listed",
                "eb_dfe_notice_given", "eb_k3_requested_by_1mo"],
     "outputs": ["eb_dfe_met", "eb_k2k3_required"],
     "description": "B2. The Core DFE determination — records WHY K-2/K-3 aren't required (D_EB_DFE_OK) and fires RED when the exception FAILS (D_EB_K2K3)."},
    {"rule_id": "R-EB-704C", "title": "§704(c) built-in gain/loss indicator", "rule_type": "routing",
     "precedence": 3, "sort_order": 3,
     "formula": ("eb_704c_present = eb_contributed_builtin OR eb_capital_revaluation. Property contributed with "
                 "FMV != adjusted tax basis (forward §704(c), a reasonable method mandatory) or a capital-account "
                 "book-up (reverse §704(c)) requires §704(c) method selection/tracking — Complex Entity Pro."),
     "inputs": ["eb_contributed_builtin", "eb_capital_revaluation"], "outputs": ["eb_704c_present"],
     "description": "B3. Indicator; fires D_EB_704C (RED)."},
    {"rule_id": "R-EB-754", "title": "§754 / §743(b) / §734(b) basis-adjustment indicator", "rule_type": "routing",
     "precedence": 4, "sort_order": 4,
     "formula": ("eb_743_734_indicated = eb_754_on_file OR eb_builtin_loss_250k OR eb_basis_reduction_250k. A "
                 "§754 election in effect makes every later interest transfer (§743(b)) and property distribution "
                 "(§734(b)) adjust basis; even without an election, a >$250k substantial built-in loss (§743(d)) "
                 "or >$250k substantial basis reduction (§734(d)) forces a mandatory adjustment."),
     "inputs": ["eb_754_on_file", "eb_builtin_loss_250k", "eb_basis_reduction_250k"], "outputs": ["eb_743_734_indicated"],
     "description": "B4. Indicator + $250k mandatory triggers; fires D_EB_754 (RED)."},
    {"rule_id": "R-EB-APPORTION", "title": "Multistate apportionment beyond supported states", "rule_type": "routing",
     "precedence": 5, "sort_order": 5,
     "formula": ("eb_apportionment_boundary = eb_nexus_beyond_states AND (NOT eb_pl86272_protected). Fire when the "
                 "entity has income-tax nexus/apportionable activity in a state beyond GA + SC/AL/NC/FL/TN and is "
                 "not fully shielded by P.L. 86-272 (net-income tax; mere solicitation of tangible-goods orders "
                 "filled from out of state). Per-state thresholds vary and are re-verified per state."),
     "inputs": ["eb_nexus_beyond_states", "eb_pl86272_protected"], "outputs": ["eb_apportionment_boundary"],
     "description": "B5. State-specific indicator; fires D_EB_APPORT (RED)."},
]

EB_LINES: list[dict] = [
    {"line_number": "M3", "description": "B1 Schedule M-3 threshold — 1065: assets/adj $10M | receipts $35M | REP 50%; 1120-S: assets $10M", "line_type": "calculated"},
    {"line_number": "K2K3-DFE", "description": "B2 K-2/K-3 domestic filing exception — 4-criteria gate; RED when it fails", "line_type": "calculated"},
    {"line_number": "704C", "description": "B3 §704(c) — contributed property FMV != basis, or a book-up (reverse §704(c))", "line_type": "calculated"},
    {"line_number": "754", "description": "B4 §754/§743(b)/§734(b) — election on file, or >$250k built-in loss / basis reduction", "line_type": "calculated"},
    {"line_number": "APPORT", "description": "B5 multistate apportionment beyond GA + SC/AL/NC/FL/TN (P.L. 86-272 anchor)", "line_type": "calculated"},
]

EB_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_EB_M3", "title": "Schedule M-3 required — not supported this season", "severity": "error",
     "condition": "eb_m3_required is True",
     "message": ("This return crosses the Schedule M-3 threshold (1065: total or adjusted assets >= $10M, or "
                 "receipts >= $35M, or a >=50% reportable entity partner; 1120-S: total assets >= $10M). "
                 "Schedule M-3 is required in lieu of Schedule M-1 and is not produced this season — prepare M-3 "
                 "separately."),
     "notes": "B1. PRODUCT_MAP boundary (RED)."},
    {"diagnostic_id": "D_EB_K2K3", "title": "K-2/K-3 required — domestic filing exception FAILS", "severity": "error",
     "condition": "eb_k2k3_required is True",
     "message": ("The partnership does NOT meet all four K-2/K-3 domestic filing exception criteria (no/limited "
                 "foreign activity with <=$300 foreign tax; only listed U.S.-person partners; K-3 notification; "
                 "no K-3 request by the 1-month date), so Schedules K-2/K-3 (international reporting) are required "
                 "and are not supported this season. Prepare K-2/K-3 separately."),
     "notes": "B2. The DFE-fail RED (PRODUCT_MAP Core determination)."},
    {"diagnostic_id": "D_EB_DFE_OK", "title": "K-2/K-3 not required — domestic filing exception met", "severity": "info",
     "condition": "eb_dfe_met is True",
     "message": ("The partnership meets all four domestic filing exception criteria, so Schedules K-2/K-3 are not "
                 "required (a partner may still request a Schedule K-3 after the 1-month date). This is the "
                 "recorded basis for not filing K-2/K-3."),
     "notes": "B2. The affirmative 'why not required' record PRODUCT_MAP requires."},
    {"diagnostic_id": "D_EB_704C", "title": "§704(c) built-in gain/loss — not supported this season", "severity": "error",
     "condition": "eb_704c_present is True",
     "message": ("Property was contributed with FMV different from tax basis, or capital accounts were revalued "
                 "(book-up) — §704(c) requires a reasonable allocation method (traditional / curative / remedial) "
                 "to be selected and tracked. This is not supported this season; handle the §704(c) allocations "
                 "separately."),
     "notes": "B3. PRODUCT_MAP boundary (RED)."},
    {"diagnostic_id": "D_EB_754", "title": "§754 / §743(b) / §734(b) basis adjustment — not supported", "severity": "error",
     "condition": "eb_743_734_indicated is True",
     "message": ("A §754 election is in effect, or a >$250,000 substantial built-in loss on an interest transfer "
                 "(§743(d)) or a >$250,000 substantial basis reduction on a distribution (§734(d)) forces a "
                 "mandatory basis adjustment. The §743(b)/§734(b) basis-adjustment computation is not supported "
                 "this season — compute it separately."),
     "notes": "B4. PRODUCT_MAP boundary (RED)."},
    {"diagnostic_id": "D_EB_APPORT", "title": "Multistate apportionment beyond licensed states", "severity": "error",
     "condition": "eb_apportionment_boundary is True",
     "message": ("The entity appears to have income-tax nexus or apportionable activity in a state beyond the "
                 "supported set (GA + SC/AL/NC/FL/TN) and is not fully protected by P.L. 86-272 (which shields only "
                 "net-income tax where the sole activity is soliciting tangible-goods orders filled from out of "
                 "state). Multistate apportionment for other states is not supported — determine the additional "
                 "state filing/apportionment separately. State thresholds vary; verify per state."),
     "notes": "B5. State-specific boundary (RED)."},
]

EB_SCENARIOS: list[dict] = [
    {"scenario_name": "EB-M3-1065 — partnership over the $35M receipts prong", "scenario_type": "diagnostic", "sort_order": 1,
     "inputs": {"tax_year": 2025, "is_scorp": False, "total_assets": 4_000_000, "total_receipts": 40_000_000},
     "expected_outputs": {"eb_m3_required": True, "D_EB_M3": True},
     "notes": "Assets < $10M but receipts $40M >= $35M → M-3 required (1065 prong 3)."},
    {"scenario_name": "EB-M3-1120S — S corp under $10M (no M-3)", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"tax_year": 2025, "is_scorp": True, "total_assets": 6_000_000, "total_receipts": 40_000_000},
     "expected_outputs": {"eb_m3_required": False},
     "notes": "1120-S single test: assets $6M < $10M → no M-3 (the $35M receipts prong does NOT apply to an S corp)."},
    {"scenario_name": "EB-DFE-met — purely domestic partnership", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"tax_year": 2025, "is_scorp": False, "foreign_activity": False, "partners_all_listed": True,
                "dfe_notice_given": True, "k3_requested_by_1mo": False},
     "expected_outputs": {"eb_dfe_met": True, "eb_k2k3_required": False, "D_EB_DFE_OK": True},
     "notes": "All 4 criteria met → DFE met; K-2/K-3 not required; D_EB_DFE_OK records the basis."},
    {"scenario_name": "EB-DFE-fail-partner — a partner requested K-3 by the 1-month date", "scenario_type": "diagnostic", "sort_order": 4,
     "inputs": {"tax_year": 2025, "is_scorp": False, "foreign_activity": False, "partners_all_listed": True,
                "dfe_notice_given": True, "k3_requested_by_1mo": True},
     "expected_outputs": {"eb_dfe_met": False, "eb_k2k3_required": True, "D_EB_K2K3": True},
     "notes": "Criterion 4 fails (K-3 requested by the 1-month date) → DFE fails → K-2/K-3 required (RED)."},
    {"scenario_name": "EB-DFE-fail-foreign — foreign taxes over $300", "scenario_type": "diagnostic", "sort_order": 5,
     "inputs": {"tax_year": 2025, "is_scorp": False, "foreign_activity": True, "foreign_tax_over_300": True,
                "partners_all_listed": True, "dfe_notice_given": True, "k3_requested_by_1mo": False},
     "expected_outputs": {"eb_dfe_met": False, "eb_k2k3_required": True, "D_EB_K2K3": True},
     "notes": "Criterion 1 fails (foreign tax > $300, beyond limited-activity) → DFE fails → K-2/K-3 required."},
    {"scenario_name": "EB-704C — contributed appreciated property", "scenario_type": "diagnostic", "sort_order": 6,
     "inputs": {"tax_year": 2025, "is_scorp": False, "contributed_builtin": True},
     "expected_outputs": {"eb_704c_present": True, "D_EB_704C": True},
     "notes": "Property contributed with FMV != basis → §704(c) method required (RED, not supported)."},
    {"scenario_name": "EB-754 — election on file", "scenario_type": "diagnostic", "sort_order": 7,
     "inputs": {"tax_year": 2025, "is_scorp": False, "election_754": True},
     "expected_outputs": {"eb_743_734_indicated": True, "D_EB_754": True},
     "notes": "§754 election in effect → §743(b)/§734(b) basis adjustments (RED, not supported)."},
    {"scenario_name": "EB-754-mandatory — >$250k built-in loss, no election", "scenario_type": "diagnostic", "sort_order": 8,
     "inputs": {"tax_year": 2025, "is_scorp": False, "election_754": False, "builtin_loss_250k": True},
     "expected_outputs": {"eb_743_734_indicated": True, "D_EB_754": True},
     "notes": "Substantial built-in loss > $250k on a transfer → mandatory §743(b) even without a §754 election."},
    {"scenario_name": "EB-APPORT — nexus in a non-supported state, no P.L. 86-272 shield", "scenario_type": "diagnostic", "sort_order": 9,
     "inputs": {"tax_year": 2025, "is_scorp": False, "nexus_beyond_states": True, "pl86272_protected": False},
     "expected_outputs": {"eb_apportionment_boundary": True, "D_EB_APPORT": True},
     "notes": "Activity beyond GA + SC/AL/NC/FL/TN and not P.L. 86-272 protected → apportionment boundary (RED)."},
    {"scenario_name": "EB-APPORT-shielded — solicitation-only, P.L. 86-272 protected", "scenario_type": "normal", "sort_order": 10,
     "inputs": {"tax_year": 2025, "is_scorp": False, "nexus_beyond_states": True, "pl86272_protected": True},
     "expected_outputs": {"eb_apportionment_boundary": False},
     "notes": "Only solicitation of tangible-goods orders filled out of state → P.L. 86-272 shields net-income tax → no boundary flag (verify the state doesn't impose a franchise/gross-receipts tax)."},
]

EB_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-EB-M3", "IRS_2025_M3_1065", "primary", "1065 M-3 Who Must File (4 prongs)"),
    ("R-EB-M3", "IRS_2025_M3_1120S", "primary", "1120-S M-3 $10M total-assets test"),
    ("R-EB-DFE", "IRS_2025_K2K3_1065", "primary", "the 4 domestic-filing-exception criteria"),
    ("R-EB-704C", "TREAS_REG_704_3", "primary", "§704(c) contributed property + reverse §704(c)"),
    ("R-EB-754", "IRC_754_743_734", "primary", "§754 election + §743(d)/§734(d) $250k triggers"),
    ("R-EB-APPORTION", "PL_86_272", "primary", "P.L. 86-272 net-income solicitation shield"),
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-ENT-BND-01", "assertion_type": "table_invariant", "entity_types": ["1065", "1120S"],
     "title": "Boundary thresholds pinned ($10M / $35M / 50% / $250k / $300)",
     "description": "Pins the verified 2025 boundary thresholds. Bug it catches: a drifted M-3/§743/§734/DFE figure.",
     "definition": {"kind": "constants_check", "form": "ENTITY_BOUNDARY",
                    "constants": {"m3_assets": 10000000, "m3_receipts_1065": 35000000, "m3_rep_pct": 50,
                                  "substantial_250k": 250000, "dfe_foreign_tax": 300}},
     "sort_order": 1},
    {"assertion_id": "FA-ENT-BND-02", "assertion_type": "flow_assertion", "entity_types": ["1065"],
     "title": "K-2/K-3 DFE gate: all 4 criteria met => not required; any fail => RED",
     "description": "Validates R-EB-DFE. Bug it catches: the DFE passing when a criterion fails (silent international gap), or firing when all four are met.",
     "definition": {"kind": "formula_check", "form": "ENTITY_BOUNDARY",
                    "formula": "dfe_met == ((not foreign_activity or not foreign_tax_over_300) and partners_all_listed and dfe_notice_given and not k3_requested_by_1mo); k2k3_required == not dfe_met"},
     "sort_order": 2},
    {"assertion_id": "FA-ENT-BND-03", "assertion_type": "flow_assertion", "entity_types": ["1065", "1120S"],
     "title": "Each boundary fires its RED diagnostic when crossed",
     "description": "Validates the M-3 / §704(c) / §754 / apportionment routing. Bug it catches: a boundary crossed but no RED thrown (Core going silent).",
     "definition": {"kind": "gating_check", "form": "ENTITY_BOUNDARY", "expect": {"red_fires": True},
                    "blockers": ["m3_required", "k2k3_required", "704c_present", "743_734_indicated", "apportionment_boundary"]},
     "sort_order": 3},
]


FORMS: list[dict] = [
    {"identity": EB_IDENTITY, "facts": EB_FACTS, "rules": EB_RULES, "lines": EB_LINES,
     "diagnostics": EB_DIAGNOSTICS, "scenarios": EB_SCENARIOS, "rule_links": EB_RULE_LINKS},
]


class Command(BaseCommand):
    help = "Load the ENTITY_BOUNDARY (Core boundary diagnostics) spec. Refuses until READY_TO_SEED=True."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard_against_hollow_seed()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad ENTITY_BOUNDARY (Core boundary diagnostics) spec\n"))
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
                "\nREFUSING TO SEED ENTITY_BOUNDARY: not cleared to seed.\n\n"
                "Gated until Ken's review walk (M-3 thresholds + the K-2/K-3 DFE 4-criteria gate +\n"
                "the $250k §743/§734 triggers + the apportionment / P.L. 86-272 scope).\n\n"
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
        form = TaxForm.objects.filter(form_number="ENTITY_BOUNDARY").first()
        if form:
            uncited = [r for r in FormRule.objects.filter(tax_form=form) if not r.authority_links.exists()]
            self.stdout.write("ENTITY_BOUNDARY: all rules cited" if not uncited
                              else self.style.WARNING(f"ENTITY_BOUNDARY uncited rules: {len(uncited)}"))
