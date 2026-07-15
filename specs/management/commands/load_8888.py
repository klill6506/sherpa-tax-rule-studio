"""Load the Form 8888 spec — Allocation of Refund (Rev. December 2025, continuous use).
Payment-cluster draft-to-gate batch order 2 (tts s77; plan filed tts REVIEW_QUEUE s76). Greenfield
(gap re-confirmed 404 on 2026-07-13).

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
Form 8888 splits a direct-deposit refund across two or three U.S. accounts. THE TITLE CHANGED
MEANING in the Rev. 12-2025 continuous-use revision: the savings-bond purchase program (TreasuryDirect
+ paper bonds) is DISCONTINUED — line 4 prints "Reserved for future use", the 2025v5.3 XSD dropped the
bond group entirely, every bond business rule is Disabled, and F8888-023 (Active) forbids a value in
the residual RefundByCheckAmt element. What remains: three DirectDepositInfoGroup rows and a total
that must tie BOTH ways (sum of rows == line 5 == the return's refund; F8888-001-04 / -002-03).
MeF: IRS8888 rides ReturnData1040 (~1958 slot); the 1040 line-35a face carries the 8888-attached
checkbox — the tts leg wires print + XML together.

v1 SCOPE — PROPOSED (Gate-1 walk W1-W4 AWAITING KEN; see f8888_source_brief.md):
W1. Allocation math: line 5 = 1a+2a+3a, must equal the return refund; each deposit >= $1; a
    single-account request routes to the return's own DD lines (don't file 8888); 2-3 accounts.
W2. Account hygiene: RTN 9-digit prefix 01-12/21-32; account <= 17 chars; exactly one type box;
    unique account numbers, never all zeros; in-the-taxpayer's-name (never the preparer's);
    the 3-deposits-per-account annual limit; Form 8379 bars the split.
W3. The retirement of the bond/check surface: line 4 reserved; bond asks REFUSE (program
    discontinued); no check amount ever emitted (F8888-023); EO 14247 paper-check wind-down info.
W4. Fallback/adjustment ordering as info diagnostics (the printed examples pinned): rejects and
    increases -> the LAST valid account; decreases and federal-tax offsets strip 3->2->1; OTHER
    (BFS) offsets hit the LOWEST routing number first; contribution-limit caution (IRA/HSA/MSA/
    ESA); IRA year-designation mechanics. entity_types ['1040']; print + MeF document.

CARRIED [UNVERIFIED]: none — verbatim vs Form 8888 Rev. 12-2025 (instructions included in the
3-page PDF; About page "None at this time" 2026-07-13) + the TY2025v5.3 business rules/XSD.
Year-watch: continuous-use revision (check the About page each season), the EO 14247 rollout.

SAFETY GUARD — READY_TO_SEED stayed False until Gate-1 approval. APPROVED: Ken, 2026-07-14 (s83 approve-all, WO-28/29/30/31/32 together; walk recommendations adopted as filed).
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

READY_TO_SEED = True  # FLIPPED 2026-07-14 — Ken approved Gate-1 in-session (s83 approve-all across WO-28/29/30/31/32; recommendations adopted as filed).

FORM_JURISDICTION = "federal"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1040"]

# ── Verified constants (f8888_source_brief.md) ──
MAX_ACCOUNTS = 3                 # DirectDepositInfoGroup maxOccurs=3 (face lines 1-3)
MIN_DEPOSIT = 1                  # "Each deposit must be at least $1"
MAX_ACCOUNT_CHARS = 17           # account number <= 17 characters
DEPOSITS_PER_ACCOUNT_YEAR = 3    # three refunds per account/prepaid card per year
RTN_PREFIX_RANGES = ((1, 12), (21, 32))  # routing number first two digits
AMENDED_TOTAL_CAP = 999_999_999  # F8888-020 (amended/superseded returns)


def _total_allocation(amounts) -> float:
    """Line 5 = the sum of lines 1a, 2a, and 3a (blank rows contribute nothing)."""
    return float(sum(float(a or 0) for a in amounts))


def _allocation_valid(amounts, return_refund) -> bool:
    """The two-way tie: every listed deposit >= $1 and the total equals the return's refund
    (F8888-001-04 sums the groups to line 5; F8888-002-03 ties line 5 to RefundAmt)."""
    listed = [float(a) for a in amounts if a not in (None, "", 0) and float(a) != 0]
    if any(a < MIN_DEPOSIT for a in listed):
        return False
    return _total_allocation(amounts) == float(return_refund)


def _split_appropriate(num_accounts) -> bool:
    """Form 8888 is only for splitting between two or more accounts — a single account belongs on
    the return's own direct-deposit lines ('don't complete this form')."""
    return int(num_accounts) >= 2


def _rtn_valid(rtn) -> bool:
    """Routing number: nine digits, first two 01-12 or 21-32."""
    s = str(rtn or "")
    if len(s) != 9 or not s.isdigit():
        return False
    prefix = int(s[:2])
    return any(lo <= prefix <= hi for lo, hi in RTN_PREFIX_RANGES)


def _accounts_unique_ok(account_numbers) -> bool:
    """F8888-015/-016: DepositorAccountNum unique across groups and never all zeros."""
    listed = [str(a) for a in account_numbers if a]
    if any(set(a) == {"0"} for a in listed):
        return False
    return len(listed) == len(set(listed))


def _decrease_ordering(amounts, decrease) -> list:
    """Math-error DECREASE (and past-due FEDERAL tax offsets): strip from line 3 first, then line 2,
    then line 1. Pins the printed example: 100/100/100 less 150 -> 100/50/0."""
    out = [float(a or 0) for a in amounts]
    remaining = float(decrease)
    for i in range(len(out) - 1, -1, -1):
        take = min(out[i], remaining)
        out[i] -= take
        remaining -= take
        if remaining <= 0:
            break
    return out


def _increase_target_index(amounts) -> int:
    """Math-error INCREASE (and reject fallbacks): the LAST listed account takes the change.
    Pins the printed example: 100/100/100 refund +50 -> line 3 receives it."""
    listed = [i for i, a in enumerate(amounts) if float(a or 0) > 0]
    return listed[-1] if listed else 0


def _bfs_offset_first_account(routing_numbers) -> int:
    """OTHER offsets (BFS: state tax, child/spousal support, student loans) hit the account with the
    LOWEST routing number first — a different ordering than the federal 3->2->1 strip."""
    listed = [(int(r), i) for i, r in enumerate(routing_numbers) if r]
    return min(listed)[1] if listed else 0


def _efile_blockers(amounts, return_refund, account_numbers, filed_8379, bond_request) -> list:
    """The MeF/e-file gate for the 8888 document. Empty list = transmittable."""
    blockers = []
    if _total_allocation(amounts) != float(return_refund):
        blockers.append("F8888-002-03")   # (001-04 collapses into the same tie on our one-writer build)
    if not _accounts_unique_ok(account_numbers):
        blockers.append("F8888-015")
    if filed_8379:
        blockers.append("8379-SPLIT-BAR")  # form text: no multi-account deposit with an 8379
    if bond_request:
        blockers.append("BONDS-RETIRED")   # program discontinued; no schema surface exists
    return blockers


AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("refund_8888", "Form 8888 refund splitting: 2-3 direct-deposit accounts, the two-way total tie, "
     "account hygiene, the discontinued bond/check surface (Rev. 12-2025), fallback/offset ordering."),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_F8888", "source_type": "federal_form", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Form 8888 (Rev. 12-2025) — Allocation of Refund (instructions included; continuous use)",
        "citation": "Form 8888 (Rev. December 2025), Cat. No. 21858A, OMB 1545-0074 — 3-page PDF with instructions",
        "issuer": "Internal Revenue Service", "official_url": "https://www.irs.gov/pub/irs-pdf/f8888.pdf",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.5, "topics": ["refund_8888"],
        "excerpts": [{
            "excerpt_label": "What's New + Reminders — bonds discontinued, continuous use, EO 14247 (Rev. 12-2025 verbatim)",
            "excerpt_text": (
                "Electronic payments: Executive Order 14247 requires all payments from the federal "
                "government, including the IRS, to be handled electronically. Starting in October 2025, the "
                "IRS will generally stop issuing paper checks for federal disbursements, including tax "
                "refunds, unless an exception applies (www.irs.gov/ModernPayments). Purchase of savings "
                "bonds discontinued: the program allowing for your refund to be deposited into your "
                "TreasuryDirect account to buy savings bonds, as well as the ability to buy paper bonds "
                "with your refund, has been discontinued. Form 8888 is now only used to split your direct "
                "deposit refund between two or more accounts. Continuous-use form: Form 8888 has been "
                "converted from annual revision to continuous use. [Face: line 4 'Reserved for future "
                "use'.] Purpose of Form: use Form 8888 if you want us to directly deposit your refund (or "
                "part of it) to either two or three accounts at a bank or other financial institution (such "
                "as a mutual fund, brokerage firm, or credit union) in the United States. An account can be "
                "a checking, savings, or other account, such as: a traditional individual retirement "
                "arrangement (IRA), Roth IRA, SEP IRA (but not a SIMPLE IRA); a health savings account "
                "(HSA); an Archer MSA; or a Coverdell education savings account (ESA). You can't have your "
                "refund deposited into more than one account if you file Form 8379, Injured Spouse "
                "Allocation. Deposit of refund to only one account: if you want your refund deposited to "
                "only one account, don't complete this form; instead, request direct deposit on your tax "
                "return."
            ),
            "summary_text": "Rev. 12-2025: bond purchases (TreasuryDirect + paper) DISCONTINUED — the form now ONLY splits a DD refund across 2-3 U.S. accounts (incl. IRA/Roth/SEP not SIMPLE, HSA, MSA, ESA); line 4 reserved; continuous use; EO 14247 ends most paper checks from Oct 2025; 8379 bars the split; one account = use the return's DD lines.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "Account rules + allocation lines (Rev. 12-2025 verbatim substance)",
            "excerpt_text": (
                "Account must be in your name: don't request a deposit of your refund to an account that "
                "isn't in your name, such as your tax return preparer's account. Although you may owe your "
                "tax return preparer a fee for preparing your return, don't have any part of your refund "
                "deposited into the preparer's account to pay the fee. The number of refunds that can be "
                "directly deposited to a single account or prepaid debit card is limited to three a year. "
                "Lines 1a, 2a, and 3a: enter the portion of your refund you want directly deposited to each "
                "account. Each deposit must be at least $1. If there are any delays in the processing of "
                "your return by the IRS, your entire refund will be deposited in the last valid account "
                "listed on Form 8888 — make sure the last account you list is an account you would want the "
                "entire refund deposited in if this happens. Lines 1b, 2b, and 3b: the routing number must "
                "be nine digits; the first two digits must be 01 through 12 or 21 through 32. Lines 1c, 2c, "
                "and 3c: check the appropriate box for the type of account — don't check more than one box "
                "for each line; if your deposit is to an account such as an IRA, HSA, brokerage account... "
                "ask your financial institution whether you should check the 'Checking' or 'Savings' box. "
                "Lines 1d, 2d, and 3d: the account number can be up to 17 characters (both numbers and "
                "letters); include hyphens but omit spaces and special symbols. Line 5: the total on line 5 "
                "must equal the total amount of the refund shown on your tax return; it must also equal the "
                "total of the amounts on lines 1a, 2a, and 3a. If the total on line 5 is different, your "
                "refund may be delayed. If your financial institution rejects one or two but not all of "
                "your direct deposit requests, the additional amount will be deposited to the last valid "
                "account listed. Don't file a Form 8888 on which you have crossed out or whited out any "
                "numbers or letters."
            ),
            "summary_text": "In-your-name only (never the preparer's); 3 deposits/account/year; each deposit >= $1; RTN 9-digit prefix 01-12/21-32; exactly one type box; account <= 17 chars; line 5 ties both ways; rejects and delays land in the LAST valid account; no cross-outs.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "Math-error / offset ordering + the IRA caution (Rev. 12-2025 verbatim substance)",
            "excerpt_text": (
                "Refund increased: if you made an error on your return and the amount of your refund is "
                "increased, the additional amount will be deposited to the last account listed. Example: "
                "your return shows a refund of $300 and you ask that the refund be split among three "
                "accounts with $100 to each account; due to an error the refund is increased to $350 — the "
                "additional $50 will be added to the deposit to the account on line 3. Refund decreased: "
                "the decrease will be taken first from any deposit to an account on line 3, next from the "
                "deposit to the account on line 2, and finally from the deposit to the account on line 1. "
                "Example: refund $300 split $100/$100/$100, decreased by $150 — you won't receive the $100 "
                "for line 3, and the line-2 deposit will be reduced by $50. Note: if you appeal the math "
                "error adjustment and your appeal is upheld, the resulting refund will be deposited to the "
                "account on line 1. Past-due federal tax offsets follow the same line-3-first ordering. "
                "Other offsets (state income tax, child support, spousal support, certain federal nontax "
                "debts such as student loans) subject to offset by the Treasury Department's Bureau of the "
                "Fiscal Service: the past-due amounts will be deducted first from the deposit to the "
                "account with the LOWEST routing number, then the next lowest, then the highest. Caution: "
                "if the deposit to one or more of your accounts is changed due to a math error or refund "
                "offset, and that account is subject to contribution limits (IRA, HSA, Archer MSA, "
                "Coverdell ESA), or the deposit was deducted as a contribution on your tax return, you may "
                "need to correct your contribution or file an amended return. IRA deposits: establish the "
                "IRA before you request direct deposit; notify the trustee or custodian of the year to "
                "which the deposit is to be applied; if you designate a prior-year deposit you must verify "
                "it was actually made by the due date of the return (not counting extensions) — otherwise "
                "you must file an amended return and reduce the IRA deduction and any retirement savings "
                "contributions credit."
            ),
            "summary_text": "Increases -> the LAST listed account (printed $300->$350 example); decreases + federal-tax offsets strip 3->2->1 (printed $150 example); BFS offsets hit the LOWEST routing number first; upheld appeals pay line 1; contribution-limited accounts may need corrective action; IRA year-designation mechanics.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "MEF_8888_BR", "source_type": "official_guidance", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "MeF 1040 Business Rules TY2025v5.3 — the F8888-* family + IRS8888 schema",
        "citation": "1040_Business_Rules_2025v5.3.csv + IRS8888.xsd (ReturnData1040 document; DirectDepositInfoGroup maxOccurs=3)",
        "issuer": "Internal Revenue Service",
        "official_url": "https://www.irs.gov/e-file-providers/modernized-e-file-mef-schemas-and-business-rules",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.0, "topics": ["refund_8888"],
        "excerpts": [{
            "excerpt_label": "F8888 Active rules + the retired bond surface (TY2025v5.3 verbatim substance)",
            "excerpt_text": (
                "F8888-001-04: on Form 8888, the sum of 'DirectDepositRefundAmt' in all "
                "'DirectDepositInfoGroup' must be equal to 'TotalAllocationOfRefundAmt'. F8888-002-03: "
                "Form 8888 'TotalAllocationOfRefundAmt' must be equal to 'RefundAmt' in the return. "
                "F8888-015: 'DepositorAccountNum' on Form 8888 must be unique. F8888-016: "
                "'DepositorAccountNum' on Form 8888 must not be all zeros. F8888-020: if "
                "'AmendedReturnInd'/'SupersededReturnInd' is checked and Form 8888 is present, "
                "'TotalAllocationOfRefundAmt' must not be greater than 999,999,999. F8888-023: Form 8888 "
                "'RefundByCheckAmt' must not have a value. [Schema: DirectDepositInfoGroup minOccurs=0 "
                "maxOccurs=3 {DirectDepositRefundAmt, RoutingTransitNum, BankAccountTypeCd "
                "(Checking/Savings), DepositorAccountNum}; the SavingsBondPurchaseInfoGrp of prior years "
                "NO LONGER EXISTS in the 2025v5.3 XSD, and every bond rule (F8888-005, -009 through -014, "
                "-017, -018) is Disabled.]"
            ),
            "summary_text": "Active set: group-sum == total (001-04), total == return RefundAmt (002-03), unique/non-zero account numbers (015/016), amended cap (020), NO check amount (023). The bond group is gone from the XSD; all bond rules Disabled — schema and face agree the program is over.",
            "is_key_excerpt": True,
        }],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_F8888", "8888", "governs"), ("MEF_8888_BR", "8888", "governs"),
]


F8888_FACTS: list[dict] = [
    {"fact_key": "acct1_amount", "label": "L1a — deposit to the first account (>= $1)", "data_type": "decimal", "required": False, "sort_order": 1},
    {"fact_key": "acct1_routing", "label": "L1b — first account routing number (9-digit, prefix 01-12/21-32)", "data_type": "string", "required": False, "sort_order": 2},
    {"fact_key": "acct1_type", "label": "L1c — first account type (exactly one box)", "data_type": "choice", "required": False, "sort_order": 3,
     "choices": ["checking", "savings"]},
    {"fact_key": "acct1_number", "label": "L1d — first account number (<= 17 chars; hyphens ok, no spaces/symbols)", "data_type": "string", "required": False, "sort_order": 4},
    {"fact_key": "acct2_amount", "label": "L2a — deposit to the second account", "data_type": "decimal", "required": False, "sort_order": 5},
    {"fact_key": "acct2_routing", "label": "L2b — second account routing number", "data_type": "string", "required": False, "sort_order": 6},
    {"fact_key": "acct2_type", "label": "L2c — second account type", "data_type": "choice", "required": False, "sort_order": 7,
     "choices": ["checking", "savings"]},
    {"fact_key": "acct2_number", "label": "L2d — second account number", "data_type": "string", "required": False, "sort_order": 8},
    {"fact_key": "acct3_amount", "label": "L3a — deposit to the third account", "data_type": "decimal", "required": False, "sort_order": 9},
    {"fact_key": "acct3_routing", "label": "L3b — third account routing number", "data_type": "string", "required": False, "sort_order": 10},
    {"fact_key": "acct3_type", "label": "L3c — third account type", "data_type": "choice", "required": False, "sort_order": 11,
     "choices": ["checking", "savings"]},
    {"fact_key": "acct3_number", "label": "L3d — third account number", "data_type": "string", "required": False, "sort_order": 12},
    {"fact_key": "return_refund_amount", "label": "The return's refund (1040 line 35a) — line 5 must equal it", "data_type": "decimal", "required": False, "sort_order": 13},
    {"fact_key": "filed_form_8379", "label": "Form 8379 (Injured Spouse) filed — bars the multi-account split", "data_type": "boolean", "required": False, "sort_order": 14},
    {"fact_key": "bond_purchase_requested", "label": "Legacy savings-bond ask (program DISCONTINUED — refuses; line 4 reserved)", "data_type": "boolean", "required": False, "sort_order": 15},
    {"fact_key": "is_amended_return", "label": "Amended/superseded return (caps the total at 999,999,999 — F8888-020)", "data_type": "boolean", "required": False, "sort_order": 16},
]

F8888_RULES: list[dict] = [
    {"rule_id": "R-8888-USE", "title": "Purpose + eligibility (2-3 accounts; single account uses the return)", "rule_type": "routing",
     "formula": "8888 = split the DD refund among 2-3 U.S. accounts (checking/savings/IRA-Roth-SEP (not SIMPLE)/HSA/Archer MSA/Coverdell ESA). ONE account -> the return's own DD lines, don't file 8888. Form 8379 filed -> no split. Accounts in the TAXPAYER'S name only (never the preparer's). <= 3 refunds per account/prepaid card per year",
     "inputs": ["acct1_amount", "acct2_amount", "acct3_amount", "filed_form_8379"], "outputs": ["form_routing"], "sort_order": 1,
     "description": "W1/W2. The Rev. 12-2025 purpose text — post-bond, the form is ONLY the splitter. The joint-return caution (spouse may get part of the refund) rides the print blurb."},
    {"rule_id": "R-8888-ALLOC", "title": "Allocation math: line 5 ties both ways; $1 minimum per deposit", "rule_type": "calculation",
     "formula": "L5 = L1a + L2a + L3a; L5 MUST equal the return's refund (F8888-002-03) and the group sum (F8888-001-04); each listed deposit >= $1; amended/superseded -> total <= 999,999,999 (F8888-020)",
     "inputs": ["acct1_amount", "acct2_amount", "acct3_amount", "return_refund_amount", "is_amended_return"],
     "outputs": ["total_allocation", "allocation_valid"], "sort_order": 2,
     "description": "W1. A different line-5 total 'may delay your refund' on paper and REJECTS in e-file — the tts extract refuses on mismatch rather than adjusting silently."},
    {"rule_id": "R-8888-ACCT", "title": "Account hygiene: RTN prefix, 17-char cap, one type box, unique numbers", "rule_type": "validation",
     "formula": "routing = 9 digits with the first two in 01-12 or 21-32; account number <= 17 chars (hyphens ok, no spaces/symbols); EXACTLY one of Checking/Savings per row (IRA/HSA/brokerage -> ask the institution); DepositorAccountNum unique across rows (F8888-015) and never all zeros (F8888-016); no crossed-out/whited-out entries",
     "inputs": ["acct1_routing", "acct2_routing", "acct3_routing", "acct1_number", "acct2_number", "acct3_number", "acct1_type", "acct2_type", "acct3_type"],
     "outputs": ["accounts_valid"], "sort_order": 3,
     "description": "W2. The same RTN prefix rule the suite already enforces on the S-17b direct-deposit inputs — one shared validator on the tts side."},
    {"rule_id": "R-8888-RETIRED", "title": "The bond/check surface is RETIRED (Rev. 12-2025)", "rule_type": "validation",
     "formula": "savings-bond purchases (TreasuryDirect + paper) DISCONTINUED -> any bond ask REFUSES with the program-ended message; face line 4 = 'Reserved for future use'; RefundByCheckAmt must NEVER carry a value (F8888-023; the 2025v5.3 XSD dropped the bond group, all bond rules Disabled). EO 14247: paper refund checks generally end October 2025 (irs.gov/ModernPayments)",
     "inputs": ["bond_purchase_requested"], "outputs": ["bond_refusal"], "sort_order": 4,
     "description": "W3. The structural catch of the revision — the spec records the discontinuation so no tts surface (input, print, XML) resurrects the old Part II. Refusal beats fabrication."},
    {"rule_id": "R-8888-FALLBACK", "title": "Reject/adjustment ordering (printed examples pinned)", "rule_type": "routing",
     "formula": "rejects + processing delays + math-error INCREASES -> the LAST valid account listed. math-error DECREASES + past-due FEDERAL tax offsets -> strip line 3, then 2, then 1. OTHER offsets (BFS: state tax, child/spousal support, student loans) -> the LOWEST routing number first, then ascending. upheld math-error appeal -> the line-1 account. contribution-limited targets (IRA/HSA/MSA/ESA) or deducted contributions -> corrective contribution or amend",
     "inputs": ["acct1_amount", "acct2_amount", "acct3_amount", "acct1_routing", "acct2_routing", "acct3_routing"],
     "outputs": ["fallback_ordering"], "sort_order": 5,
     "description": "W4. Print-guidance diagnostics: the preparer should make the LAST listed account the one the client would accept the ENTIRE refund in. Both printed $300 examples are pinned scenarios."},
    {"rule_id": "R-8888-IRA", "title": "IRA deposit mechanics (year designation + due-date verification)", "rule_type": "validation",
     "formula": "establish the IRA BEFORE requesting the deposit; notify the trustee/custodian of the target year (else it defaults to the filing year); a PRIOR-year designation must actually post by the un-extended due date — otherwise amend and reduce the IRA deduction + any Saver's Credit",
     "inputs": ["acct1_type", "acct2_type", "acct3_type"], "outputs": ["ira_guidance"], "sort_order": 6,
     "description": "W4. Print guidance (info diagnostic on the tts side); interacts with the existing IRA-deduction and Saver's-Credit legs only through the printed caution text."},
]

F8888_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-8888-USE", "IRS_F8888", "primary", "Purpose + one-account/8379/preparer-account/3-per-year rules"),
    ("R-8888-ALLOC", "IRS_F8888", "primary", "Lines 1a-3a $1 minimum + the line-5 two-way tie"),
    ("R-8888-ALLOC", "MEF_8888_BR", "primary", "F8888-001-04/-002-03/-020"),
    ("R-8888-ACCT", "IRS_F8888", "primary", "RTN prefix / 17-char / one-type-box rules"),
    ("R-8888-ACCT", "MEF_8888_BR", "secondary", "F8888-015/-016 uniqueness"),
    ("R-8888-RETIRED", "IRS_F8888", "primary", "Bonds-discontinued reminder + line 4 reserved + EO 14247"),
    ("R-8888-RETIRED", "MEF_8888_BR", "secondary", "F8888-023 + the dropped bond group"),
    ("R-8888-FALLBACK", "IRS_F8888", "primary", "Math-error/offset ordering + both printed examples"),
    ("R-8888-IRA", "IRS_F8888", "primary", "IRA year-designation + due-date verification caution"),
]

F8888_LINES: list[dict] = [
    {"line_number": "L1A", "description": "L1a — amount to the first account (>= $1)", "line_type": "input", "source_facts": ["acct1_amount"], "sort_order": 1},
    {"line_number": "L1B", "description": "L1b — routing number (9-digit, 01-12/21-32)", "line_type": "input", "source_facts": ["acct1_routing"], "sort_order": 2},
    {"line_number": "L1C", "description": "L1c — checking/savings (exactly one)", "line_type": "input", "source_facts": ["acct1_type"], "sort_order": 3},
    {"line_number": "L1D", "description": "L1d — account number (<= 17 chars)", "line_type": "input", "source_facts": ["acct1_number"], "sort_order": 4},
    {"line_number": "L2A", "description": "L2a — amount to the second account", "line_type": "input", "source_facts": ["acct2_amount"], "sort_order": 5},
    {"line_number": "L2B", "description": "L2b — routing number", "line_type": "input", "source_facts": ["acct2_routing"], "sort_order": 6},
    {"line_number": "L2C", "description": "L2c — checking/savings", "line_type": "input", "source_facts": ["acct2_type"], "sort_order": 7},
    {"line_number": "L2D", "description": "L2d — account number", "line_type": "input", "source_facts": ["acct2_number"], "sort_order": 8},
    {"line_number": "L3A", "description": "L3a — amount to the third account (the LAST account takes rejects/increases)", "line_type": "input", "source_facts": ["acct3_amount"], "sort_order": 9},
    {"line_number": "L3B", "description": "L3b — routing number", "line_type": "input", "source_facts": ["acct3_routing"], "sort_order": 10},
    {"line_number": "L3C", "description": "L3c — checking/savings", "line_type": "input", "source_facts": ["acct3_type"], "sort_order": 11},
    {"line_number": "L3D", "description": "L3d — account number", "line_type": "input", "source_facts": ["acct3_number"], "sort_order": 12},
    {"line_number": "L4_RESERVED", "description": "L4 — Reserved for future use (the retired bond line; never carries a value)", "line_type": "input", "source_rules": ["R-8888-RETIRED"], "sort_order": 13},
    {"line_number": "L5", "description": "L5 — total allocation (= 1a+2a+3a = the return's refund)", "line_type": "calculated", "source_rules": ["R-8888-ALLOC"], "sort_order": 14},
    {"line_number": "CALC_VALID", "description": "Computed allocation validity (two-way tie + $1 minimum + hygiene)", "line_type": "calculated", "source_rules": ["R-8888-ALLOC", "R-8888-ACCT"], "sort_order": 15},
    {"line_number": "CALC_EFILE", "description": "Computed e-file eligibility (empty blocker list = transmittable)", "line_type": "calculated", "source_rules": ["R-8888-ALLOC", "R-8888-RETIRED"], "sort_order": 16},
]

F8888_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_8888_TIE", "title": "Line 5 must equal the return's refund AND the account sum", "severity": "error",
     "condition": "sum(1a,2a,3a) != line 5, or line 5 != the return refund",
     "message": "The total on line 5 must equal the total of lines 1a, 2a, and 3a AND the refund amount shown on the tax return (MeF F8888-001-04 / F8888-002-03). A different total delays the refund on paper and rejects in e-file — adjust the split or the return before filing.", "notes": "W1."},
    {"diagnostic_id": "D_8888_MIN1", "title": "Each deposit must be at least $1", "severity": "error",
     "condition": "any listed deposit < 1",
     "message": "Each direct-deposit allocation on lines 1a, 2a, and 3a must be at least $1.", "notes": "W1."},
    {"diagnostic_id": "D_8888_SINGLE", "title": "Only one account — use the return's direct-deposit lines", "severity": "warning",
     "condition": "exactly one account listed",
     "message": "Form 8888 splits a refund between two or three accounts. For a single account, don't complete this form — request direct deposit on the tax return itself (the 1040 line-35 b/c/d fields).", "notes": "W1."},
    {"diagnostic_id": "D_8888_8379", "title": "Form 8379 bars the multi-account split", "severity": "error",
     "condition": "filed_form_8379",
     "message": "You can't have the refund deposited into more than one account when Form 8379, Injured Spouse Allocation, is filed. Remove Form 8888 or the 8379.", "notes": "W2."},
    {"diagnostic_id": "D_8888_DUPACCT", "title": "Account numbers must be unique and non-zero", "severity": "error",
     "condition": "duplicate DepositorAccountNum across rows, or an all-zeros number",
     "message": "Each account number on Form 8888 must be unique (MeF F8888-015) and must not be all zeros (F8888-016). To send more of the refund to the same account, combine the amounts on one line.", "notes": "W2."},
    {"diagnostic_id": "D_8888_RTN", "title": "Routing number fails the 9-digit/prefix rule", "severity": "error",
     "condition": "routing not 9 digits or prefix outside 01-12/21-32",
     "message": "The routing number must be nine digits and the first two digits must be 01 through 12 or 21 through 32. Verify against a check — and if the check is payable through a different institution, get the correct direct-deposit routing number from the bank.", "notes": "W2."},
    {"diagnostic_id": "D_8888_TYPE", "title": "Exactly one account-type box per line", "severity": "error",
     "condition": "checking/savings not exactly one per listed account",
     "message": "Check the appropriate box for the type of account and don't check more than one box for each line. For IRA, HSA, or brokerage deposits, ask the financial institution which box ensures the deposit is accepted.", "notes": "W2."},
    {"diagnostic_id": "D_8888_NAME", "title": "Accounts must be in the taxpayer's name (never the preparer's)", "severity": "warning",
     "condition": "informational at print/e-file",
     "message": "Don't request a deposit to an account that isn't in the taxpayer's name — and never to the tax return preparer's account, even to cover the preparation fee. Joint filers: either spouse's account is acceptable, and the spouse may receive at least part of the refund.", "notes": "W2."},
    {"diagnostic_id": "D_8888_LIMIT3", "title": "Three deposits per account per year", "severity": "info",
     "condition": "informational",
     "message": "No more than three tax refunds can be directly deposited to a single account or prepaid debit card in a year (irs.gov/Refunds/Direct-Deposit-Limits). A fourth lands as a check — or post-October-2025, per EO 14247, through an electronic alternative (irs.gov/ModernPayments).", "notes": "W2/W3."},
    {"diagnostic_id": "D_8888_BONDS", "title": "Savings-bond purchases are discontinued", "severity": "error",
     "condition": "bond_purchase_requested",
     "message": "The program allowing refunds to buy savings bonds (TreasuryDirect deposits and paper bonds) has been DISCONTINUED — Form 8888 is now only used to split a direct-deposit refund between two or more accounts (Rev. 12-2025 Reminders; line 4 is 'Reserved for future use'). Route the refund to accounts, and purchase bonds separately at treasurydirect.gov.", "notes": "W3."},
    {"diagnostic_id": "D_8888_LASTVALID", "title": "The last account takes rejects, delays, and increases", "severity": "info",
     "condition": "informational on print",
     "message": "If the IRS delays the return or an institution rejects some (not all) deposits, the affected amounts go to the LAST valid account listed — and any math-error refund increase lands there too. List last the account the client would accept the ENTIRE refund in. Decreases and past-due federal tax strip from line 3 up; other offsets (BFS — state tax, support, student loans) hit the lowest routing number first.", "notes": "W4. Both printed $300 examples are scenarios."},
    {"diagnostic_id": "D_8888_CONTRIB", "title": "Contribution-limited account adjusted — corrective action", "severity": "info",
     "condition": "IRA/HSA/MSA/ESA deposit changed by math error or offset",
     "message": "When a math error or offset changes a deposit to a contribution-limited account (IRA, HSA, Archer MSA, Coverdell ESA), or a deposit deducted as a contribution never posts, the client may need to correct the contribution from another source by the un-extended due date or file an amended return (the printed IRA example reduces the deduction and the Saver's Credit).", "notes": "W4."},
]

F8888_SCENARIOS: list[dict] = [
    {"scenario_name": "8888-A — three-way split ties both ways: e-files clean", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"acct1_amount": 1000, "acct2_amount": 2000, "acct3_amount": 500, "return_refund_amount": 3500,
                "acct1_routing": "061000104", "acct2_routing": "253177049", "acct3_routing": "061000104",
                "acct1_number": "111222333", "acct2_number": "444555666", "acct3_number": "777888999"},
     "expected_outputs": {"total_allocation": 3500, "allocation_valid": True, "efile_blockers": []},
     "notes": "Sum 3,500 == line 5 == the return refund; unique account numbers; the same routing number on two rows is fine (only DepositorAccountNum must be unique)."},
    {"scenario_name": "8888-B — line 5 off by $100: refuses", "scenario_type": "failure", "sort_order": 2,
     "inputs": {"acct1_amount": 1000, "acct2_amount": 2000, "acct3_amount": 400, "return_refund_amount": 3500,
                "acct1_number": "111", "acct2_number": "222", "acct3_number": "333"},
     "expected_outputs": {"allocation_valid": False, "efile_blockers": ["F8888-002-03"], "diagnostic": "D_8888_TIE"},
     "notes": "3,400 != 3,500 -> paper delay / e-file reject; the tts extract refuses rather than silently reallocating."},
    {"scenario_name": "8888-C — one account only: route to the return's DD lines", "scenario_type": "edge", "sort_order": 3,
     "inputs": {"acct1_amount": 3500, "return_refund_amount": 3500},
     "expected_outputs": {"split_appropriate": False, "diagnostic": "D_8888_SINGLE"},
     "notes": "'If you want your refund deposited to only one account, don't complete this form' — the suite already carries the 1040 35b/c/d direct-deposit fields (S-17b)."},
    {"scenario_name": "8888-D — duplicate account number: F8888-015", "scenario_type": "failure", "sort_order": 4,
     "inputs": {"acct1_amount": 1000, "acct2_amount": 500, "return_refund_amount": 1500,
                "acct1_number": "111222333", "acct2_number": "111222333"},
     "expected_outputs": {"accounts_unique": False, "efile_blockers": ["F8888-015"], "diagnostic": "D_8888_DUPACCT"},
     "notes": "Same DepositorAccountNum twice -> reject; combine the amounts on one line instead."},
    {"scenario_name": "8888-E — legacy bond ask: the program is over", "scenario_type": "failure", "sort_order": 5,
     "inputs": {"bond_purchase_requested": True},
     "expected_outputs": {"bond_refusal": True, "diagnostic": "D_8888_BONDS"},
     "notes": "Rev. 12-2025: TreasuryDirect + paper-bond purchases discontinued; line 4 reserved; the XSD dropped the bond group and F8888-023 forbids any check amount."},
    {"scenario_name": "8888-F — Form 8379 riding the return: no split", "scenario_type": "failure", "sort_order": 6,
     "inputs": {"acct1_amount": 1000, "acct2_amount": 500, "return_refund_amount": 1500, "filed_form_8379": True,
                "acct1_number": "111", "acct2_number": "222"},
     "expected_outputs": {"efile_blockers": ["8379-SPLIT-BAR"], "diagnostic": "D_8888_8379"},
     "notes": "Injured-spouse allocations can't multi-account. (Form 8379 itself is a stated boundary — unbuilt.)"},
    {"scenario_name": "8888-G — printed decrease example: $300 split less $150 -> 100/50/0", "scenario_type": "edge", "sort_order": 7,
     "inputs": {"acct1_amount": 100, "acct2_amount": 100, "acct3_amount": 100, "decrease": 150},
     "expected_outputs": {"adjusted": [100, 50, 0]},
     "notes": "The printed math-error example verbatim: line 3 loses its full $100, line 2 drops to $50, line 1 untouched. Federal-tax offsets follow the same 3->2->1 strip."},
    {"scenario_name": "8888-H — printed increase example: +$50 lands on line 3", "scenario_type": "edge", "sort_order": 8,
     "inputs": {"acct1_amount": 100, "acct2_amount": 100, "acct3_amount": 100, "increase": 50},
     "expected_outputs": {"increase_target": "line3"},
     "notes": "The printed $300->$350 example: the additional $50 is added to the LAST listed account. Two-account splits send increases to line 2."},
]

FORMS: list[dict] = [
    {
        "identity": {"form_number": "8888", "form_title": "Form 8888 — Allocation of Refund (Rev. 12-2025, continuous use)",
                     "notes": "Payment-cluster batch order 2 (tts s77). Rev. 12-2025 STRUCTURAL CATCH: savings-bond purchases DISCONTINUED (TreasuryDirect + paper) — the form now ONLY splits a DD refund among 2-3 U.S. accounts (IRA/Roth/SEP not SIMPLE, HSA, MSA, ESA allowed); line 4 'Reserved for future use'; F8888-023 forbids any check amount; the 2025v5.3 XSD dropped the bond group. EO 14247 ends most paper refund checks Oct 2025. Allocation: L5 = 1a+2a+3a = the return's RefundAmt (F8888-001-04/-002-03), each deposit >= $1, single-account requests use the return's own DD lines. Hygiene: RTN 9-digit prefix 01-12/21-32, account <= 17 chars, one type box, unique non-zero numbers (015/016), in-the-taxpayer's-name only, 3 deposits/account/year, 8379 bars the split. Fallback ordering (printed examples pinned): rejects/increases -> the LAST account; decreases + federal offsets strip 3->2->1; BFS offsets -> lowest routing number first. MeF: IRS8888 rides ReturnData1040 (~1958); the 1040 35a checkbox wires with it. entity_types ['1040']."},
        "facts": F8888_FACTS, "rules": F8888_RULES, "rule_links": F8888_RULE_LINKS,
        "lines": F8888_LINES, "diagnostics": F8888_DIAGNOSTICS, "scenarios": F8888_SCENARIOS,
    },
]

# ACTIVATED 2026-07-14 (tts s86 unit): the tts build leg landed — runners live in
# tts tests/test_flow_assertions.py (_run_8888_assertion, both dispatch chains) and the
# 1040 mirror was refreshed export-verbatim in the same motion (the staging note done).
FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-8888-TIE", "title": "Line 5 ties both ways (group sum == total == return refund)", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "active", "sort_order": 1,
     "description": "Sum of DirectDepositRefundAmt == TotalAllocationOfRefundAmt == the return's RefundAmt (F8888-001-04 + F8888-002-03). Pins: (1000, 2000, 500) vs refund 3500 -> valid; vs 3400 total -> refuses.",
     "definition": {"rule": "R-8888-ALLOC", "check": "sum(deposits) == line5 == RefundAmt; extract refuses on mismatch"}},
    {"assertion_id": "FA-8888-SPLIT", "title": "8888 only for 2-3 accounts; single account rides the return", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "active", "sort_order": 2,
     "description": "The document emits only when >= 2 accounts are listed (each >= $1, max 3 groups); a single-account refund uses the 1040's own 35 b/c/d direct-deposit fields (the S-17b inputs) with no 8888.",
     "definition": {"rule": "R-8888-USE", "check": "2 <= listed accounts <= 3 for the IRS8888 document; 1 account -> return DD path"}},
    {"assertion_id": "FA-8888-NOBOND", "title": "No bond/check surface survives (Rev. 12-2025)", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "active", "sort_order": 3,
     "description": "The extract never emits RefundByCheckAmt (F8888-023) or any bond element (the group left the XSD); a legacy bond ask refuses with the program-discontinued message; line 4 stays blank on the print.",
     "definition": {"rule": "R-8888-RETIRED", "check": "no RefundByCheckAmt, no bond group, bond asks refuse"}},
]


class Command(BaseCommand):
    help = "Load the Form 8888 spec (Allocation of Refund). Refuses to seed until READY_TO_SEED=True (Gate-1 W1-W4)."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad Form 8888 spec (Allocation of Refund)\n"))
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
                "\nREFUSING TO SEED FORM 8888: not cleared.\n\n"
                "Gated until Ken approves the Gate-1 walk (W1 allocation math + the single-account route;\n"
                "W2 account hygiene + 8379/3-per-year; W3 the retired bond/check surface;\n"
                "W4 fallback/offset ordering + IRA mechanics) and flips the sentinel.\n\n"
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
        for code in EXISTING_SOURCES_TO_REFERENCE:
            src = AuthoritySource.objects.filter(source_code=code).first()
            if src:
                sources[code] = src
            else:
                self.stdout.write(self.style.WARNING(f"  (existing source {code} not in this DB — links to it will skip)"))
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
        self.stdout.write(f"  {len(FLOW_ASSERTIONS)} flow assertions (staged DRAFT — the tts leg activates)")

    def _report(self):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("Form 8888 loaded.")
        self.stdout.write(f"  8888: facts {len(F8888_FACTS)} / rules {len(F8888_RULES)} / lines {len(F8888_LINES)} / diag {len(F8888_DIAGNOSTICS)} / tests {len(F8888_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}")
        self.stdout.write("=" * 60)
