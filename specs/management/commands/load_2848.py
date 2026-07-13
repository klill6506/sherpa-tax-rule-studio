"""Load the Form 2848 spec — Power of Attorney and Declaration of Representative (Rev. January 2021).
WO-27, SPINE S-20c. Greenfield (gap re-confirmed 404 on 2026-07-12; first flagged alongside 2553/8832).

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
Form 2848 authorizes an individual ELIGIBLE TO PRACTICE before the IRS (Part II designations a-r) to
represent the taxpayer and inspect/receive confidential tax information. Administrative/structural — no
tax computation; print-first (mail/fax/online upload at IRS.gov/Submit2848; no MeF). Boundaries: Form
8821 = information only (no representation); Form 56 = fiduciary (stands AS the taxpayer); a non-IRS POA
rides Pub. 216 / 26 CFR 601.503(a) but is CAF-recordable only with a completed 2848 attached. One 2848
PER TAXPAYER — joint filers each file their own. The app value-add: line 2 autofills the preparer's
name/address/CAF/PTIN/phone/fax from the Preparer record (the BUILD_ORDER S-20c note).

v1 SCOPE — PROPOSED (Gate-1 walk W1-W4 AWAITING KEN; see f2848_source_brief.md):
W1. Line 3 validity + the future-period clock: matter/form/periods completeness; the general-reference
    ("All years") RETURN-the-POA error; the CAF future-period rule — recordable only through 3 years
    from Dec 31 of the receipt year.
W2. Representative constraints + Part II pairing: max 4 reps on the form (attach for more), max 2
    notice-copy designees, CAF/PTIN per rep ("None" allowed for first-timers), designation-specific
    jurisdiction/number entries, the unenrolled-return-preparer (h) representation-rights gate
    (PTIN + prepared-and-signed + AFSP both years; 8821 fallback).
W3. Signature mechanics: the 45/60-day representative-signature window (sequence-aware); handwritten
    required for mail/fax — electronic signatures ONLY via online submission; joint filers separate
    forms; entity signer/title rules as print guidance.
W4. CAF hygiene (the 08-Jul-2026 Recent Development) + revocation + filing scope: "modified"-CAF
    diagnostics (5a-other/5b limits block TDS + Tax Pro Account IAs; never check line 4 unless truly
    specific-use); the line-6 attach-to-retain error; REVOKE/WITHDRAW mechanics; the where-to-file
    chart (Memphis/Ogden/Philadelphia International, year-watched). entity_types
    ['1040','1120S','1065','1120','1041','709']; print-first, no MeF.

CARRIED [UNVERIFIED]: none — verbatim vs FINAL Form 2848 Rev. 1-2021 + i2848 Rev. 9-2021 + the
08-Jul-2026 "Items to consider" Recent Development (About page reviewed 09-Jul-2026). Year-watch: the
fax numbers ("may change without notice"), the online-submission login flow (the printed "Secure
Access" is superseded; the IRS.gov/Submit2848 URL stands), and the Recent Developments page.

SAFETY GUARD — READY_TO_SEED stays False until Ken approves the Gate-1 walk (W1-W4).
FLIPPED 2026-07-12 — Ken APPROVED (live Gate-1 walk, s68 conversation: "Approve" on the plain-English
W1-W4 summary): W1 line-3 validity + the future-period clock; W2 rep constraints + the preparer
L2-autofill value-add + the URP gate; W3 signature mechanics (45/60-day window; e-sign online-only);
W4 the 08-Jul-2026 modified-CAF/line-4 diagnostics + retention + all-six entity_types print-first.
Validated (scratchpad/validate_2848.py, 73/0).
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

READY_TO_SEED = True  # ⟨GATE 1⟩ Ken APPROVED 2026-07-12 (live walk, s68) — see the docstring.

FORM_JURISDICTION = "federal"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1040", "1120S", "1065", "1120", "1041", "709"]  # a POA can attach to any suite client

# ── Verified constants (f2848_source_brief.md) ──
MAX_REPS_ON_FORM = 4                # L2 has four blocks; more -> "See attached" + additional 2848s
MAX_NOTICE_COPY_REPS = 2            # "IRS sends notices and communications to only two representatives"
FUTURE_PERIOD_YEARS = 3             # CAF won't record future periods beyond 3 yrs from Dec 31 of receipt year
REP_SIGN_DAYS_DOMESTIC = 45         # rep must sign within 45 days when the taxpayer signs first
REP_SIGN_DAYS_ABROAD = 60           # 60 days for taxpayers residing abroad
STUDENT_CAF_PURGE_DAYS = 130        # CAF auto-purges a student (k) rep 130 days after the taxpayer signs
PPS_PHONE = "866-860-4259"          # Practitioner Priority Service (forgotten CAF numbers)
FILING_ADDRESSES = {                # i2848 Rev. 9-2021 chart (year-watched: "may change without notice")
    "memphis": "Internal Revenue Service, 5333 Getwell Road, Stop 8423, Memphis, TN 38118 (fax 855-214-7519)",
    "ogden": "Internal Revenue Service, 1973 Rulon White Blvd., MS 6737, Ogden, UT 84201 (fax 855-214-7522)",
    "international": "Internal Revenue Service, International CAF Team, 2970 Market Street, MS 4-H14.123, "
                     "Philadelphia, PA 19104 (fax 855-772-3156; outside the US 304-707-9785)",
}


def _future_period_recordable(receipt_year, period_year) -> bool:
    """L3: the CAF will not record future tax years/periods that exceed 3 years from December 31 of the
    year the IRS receives the power of attorney (received 2026 -> recordable through 2029)."""
    return int(period_year) <= int(receipt_year) + FUTURE_PERIOD_YEARS


def _rep_sign_deadline_days(taxpayer_abroad) -> int:
    """L7 note: when the taxpayer signs first, the representative must sign within 45 days of the
    taxpayer's signature date (60 days for authorizations from taxpayers residing abroad)."""
    return REP_SIGN_DAYS_ABROAD if taxpayer_abroad else REP_SIGN_DAYS_DOMESTIC


def _rep_signature_timely(days_after_taxpayer, taxpayer_abroad, rep_signed_first=False) -> bool:
    """If the representative signs first, the taxpayer has no required time limit; otherwise the
    representative's signature must land within the 45/60-day window."""
    if rep_signed_first:
        return True
    return int(days_after_taxpayer) <= _rep_sign_deadline_days(taxpayer_abroad)


def _urp_can_represent(has_ptin, prepared_and_signed, afsp_prep_year, afsp_rep_year) -> bool:
    """Designation h: an unenrolled return preparer may represent (exam-only, limited) ONLY with a valid
    active PTIN + they prepared and signed the return under exam (or prepared, if no signature space) +
    a valid AFSP Record of Completion for BOTH the preparation year and the representation year(s)
    (post-2015 returns). Otherwise: Form 8821 information access only."""
    return bool(has_ptin and prepared_and_signed and afsp_prep_year and afsp_rep_year)


def _notice_copy_ok(num_notice_copy_reps) -> bool:
    """L2: no more than two representatives may be designated to receive copies of notices."""
    return int(num_notice_copy_reps) <= MAX_NOTICE_COPY_REPS


def _rep_count_ok(num_representatives, more_reps_attached) -> bool:
    """L2 holds four blocks; naming more requires 'See attached for additional representatives' plus
    additional Form(s) 2848."""
    return int(num_representatives) <= MAX_REPS_ON_FORM or bool(more_reps_attached)


def _modified_caf(l5a_other_acts, l5b_any_limits) -> bool:
    """Recent Development 08-Jul-2026: the POA records as 'modified' on the CAF when line 5a contains
    authorizations other than disclosure / substitution / return-signing, or when line 5b limits the
    representative's authority in any way — blocking Transcript Delivery System access and Tax Pro
    Account installment agreements."""
    return bool(l5a_other_acts or l5b_any_limits)


def _filing_route(line4_specific_use, has_electronic_signature) -> str:
    """How To File: line 4 checked -> mail/fax to the IRS office handling the matter. Otherwise online
    (IRS.gov/Submit2848), fax, or mail per the chart — but an electronically signed 2848 may ONLY be
    submitted online (handwritten signatures required for mail/fax)."""
    if line4_specific_use:
        return "office_handling_matter"
    return "online_only" if has_electronic_signature else "online_fax_or_mail"


AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("poa_2848", "Form 2848 POA: designations a-r; L3 validity (no general references; 3-yr future "
     "clock); 4 reps / 2 notice copies; 45/60-day window; e-sign online-only; 'modified'-CAF hygiene; "
     "REVOKE/WITHDRAW; 8821/56 boundaries."),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_F2848", "source_type": "federal_form", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Form 2848 (Rev. 1-2021) — Power of Attorney and Declaration of Representative",
        "citation": "Form 2848 (Rev. January 2021), Cat. No. 11980J, OMB 1545-0150",
        "issuer": "Internal Revenue Service", "official_url": "https://www.irs.gov/pub/irs-pdf/f2848.pdf",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.5, "topics": ["poa_2848"],
        "excerpts": [{
            "excerpt_label": "Part I face L1-L7 (Rev. 1-2021 verbatim substance)",
            "excerpt_text": (
                "Caution: A separate Form 2848 must be completed for each taxpayer. Form 2848 will not be "
                "honored for any purpose other than representation before the IRS. L1 Taxpayer information "
                "(name/address, taxpayer identification number(s), daytime telephone, plan number if "
                "applicable). L2 four representative blocks: name and address, CAF No., PTIN, Telephone No., "
                "Fax No., 'Check if new: Address / Telephone No. / Fax No.'; blocks 1-2 carry 'Check if to be "
                "sent copies of notices and communications'; blocks 3-4 carry 'Note: IRS sends notices and "
                "communications to only two representatives.' L3 Acts authorized (you are required to complete "
                "line 3): Description of Matter (Income, Employment, Payroll, Excise, Estate, Gift, "
                "Whistleblower, Practitioner Discipline, PLR, FOIA, Civil Penalty, Sec. 4980H Shared "
                "Responsibility Payment, etc.) / Tax Form Number / Year(s) or Period(s). L4 Specific use not "
                "recorded on the CAF (checkbox). L5a Additional acts authorized: Access my IRS records via an "
                "Intermediate Service Provider; Authorize disclosure to third parties; Substitute or add "
                "representative(s); Sign a return; Other acts authorized. L5b Specific acts not authorized "
                "(representatives are never authorized to endorse or otherwise negotiate any government check "
                "or direct payment into their own accounts). L6 The filing of this power of attorney "
                "automatically revokes all earlier power(s) of attorney on file for the same matters and years "
                "or periods; check to retain and YOU MUST ATTACH A COPY OF ANY POWER OF ATTORNEY YOU WANT TO "
                "REMAIN IN EFFECT. L7 Taxpayer declaration and signature: IF NOT COMPLETED, SIGNED, AND DATED, "
                "THE IRS WILL RETURN THIS POWER OF ATTORNEY TO THE TAXPAYER."
            ),
            "summary_text": "Separate 2848 per taxpayer; 4 rep blocks (CAF/PTIN; 2 notice-copy max); L3 matter/form/periods required; L4 specific-use; L5a additional acts; L5b built-in check bar; L6 auto-revoke + attach-to-retain; L7 unsigned = returned.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "Part II Declaration of Representative — designations a-r (Rev. 1-2021 verbatim substance)",
            "excerpt_text": (
                "Under penalties of perjury: not currently suspended or disbarred from practice before the "
                "IRS; subject to Circular 230; authorized to represent the taxpayer; and one of: a Attorney "
                "(member in good standing of the bar of the highest court of the jurisdiction shown); b "
                "Certified Public Accountant (active license in the jurisdiction shown); c Enrolled Agent "
                "(per Circular 230); d Officer (bona fide officer of the taxpayer organization); e Full-Time "
                "Employee; f Family Member (spouse, parent, child, grandparent, grandchild, step-parent, "
                "step-child, brother, or sister); g Enrolled Actuary (authority limited by Circular 230 "
                "section 10.3(d)); h Unenrolled Return Preparer (must have prepared and signed the return, "
                "been eligible to sign, hold a valid PTIN, and possess the required Annual Filing Season "
                "Program Record(s) of Completion); k Qualifying Student or Law Graduate (LITC or STCP); r "
                "Enrolled Retirement Plan Agent (limited by section 10.3(e)). IF THIS DECLARATION OF "
                "REPRESENTATIVE IS NOT COMPLETED, SIGNED, AND DATED, THE IRS WILL RETURN THE POWER OF "
                "ATTORNEY. REPRESENTATIVES MUST SIGN IN THE ORDER LISTED IN PART I, LINE 2. Note: for "
                "designations d-f, enter your title, position, or relationship in the Licensing jurisdiction "
                "column. Column entries: a/b state abbreviation + bar/license number; c enrollment card "
                "number; g Joint Board enrollment number; h PTIN; k 'LITC' or 'STCP'; r Return Preparer "
                "Office enrollment number."
            ),
            "summary_text": "Designations a-r with per-designation jurisdiction/number column entries; representatives sign in line-2 order; unsigned Part II = POA returned.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "IRS_I2848", "source_type": "federal_form", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Instructions for Form 2848 (Rev. 9-2021)",
        "citation": "i2848 (Rev. September 2021), Cat. No. 11981U",
        "issuer": "Internal Revenue Service", "official_url": "https://www.irs.gov/pub/irs-pdf/i2848.pdf",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.5, "topics": ["poa_2848"],
        "excerpts": [{
            "excerpt_label": "Line 3 validity + the future-period CAF clock (i2848 9-2021 verbatim)",
            "excerpt_text": (
                "In order for the power of attorney to be valid, you must enter the description of the "
                "matter, the tax form number (where applicable), and the year(s) or period(s) (where "
                "applicable)... You may list consecutive multiple years or a series of inclusive periods, "
                "including quarterly periods, by using 'through,' 'thru,' or a hyphen. For example, '2018 "
                "thru 2020' or '2nd 2018-3rd 2019.' For fiscal years, enter the ending year and month, using "
                "the YYYYMM format. For a short tax period, enter the beginning and ending dates... Do not "
                "use a general reference such as 'All years,' 'All periods,' or 'All taxes.' The IRS will "
                "return any power of attorney with a general reference. ... You may also list future tax "
                "years or periods. However, the IRS will not record on the CAF system future tax years or "
                "periods listed that exceed 3 years from December 31 of the year that the IRS receives the "
                "power of attorney. ... If the matter relates to estate tax, enter the decedent's date of "
                "death instead of the year or period. For powers of attorney related to a return of "
                "partnership income or S corporation income [non-BBA], enter 'Income including pass-through "
                "items' in the Description of Matter column."
            ),
            "summary_text": "L3 must carry matter + form + periods; through/thru/hyphen ranges; fiscal YYYYMM; NO general references (IRS returns the POA); future periods recordable only through Dec 31 receipt-year + 3; estate tax = date of death; 1065/1120-S = 'Income including pass-through items'.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "Signature mechanics — handwritten vs electronic + the 45/60-day window (i2848 9-2021 verbatim)",
            "excerpt_text": (
                "You must handwrite your signature on Form 2848 if you file it by mail or by fax. Digital, "
                "electronic, or typed-font signatures are not valid signatures for Forms 2848 filed by mail "
                "or by fax. If you use an electronic signature (see Electronic Signatures, earlier), you must "
                "submit your Form 2848 online (IRS.gov/Submit2848). ... If you filed a joint return, your "
                "spouse must execute his or her own power of attorney on a separate Form 2848 to designate a "
                "representative. ... Note. Generally, the taxpayer signs first, granting the authority and "
                "then the representative signs, accepting the authority granted. In this situation, for "
                "domestic authorizations, the representative must sign within 45 days from the date the "
                "taxpayer signed (60 days for authorizations from taxpayers residing abroad). If the "
                "representative signs first, the taxpayer does not have a required time limit for signing. "
                "Corporations or associations: an officer with the legal authority to bind the corporation "
                "must sign and enter his or her exact title. Partnerships: all partners must sign... if one "
                "partner is authorized to act in the name of the partnership [state-law binding authority], "
                "only that partner is required to sign (attach a copy of the authorization). For matters "
                "related to the centralized partnership audit regime, the partnership representative (or "
                "designated individual) must sign; title 'Partnership Representative' or 'Designated "
                "Individual of [name of Partnership Representative]'. Estates: only one co-executor having "
                "the authority to bind the estate is required to sign (26 CFR 601.503(d))."
            ),
            "summary_text": "Handwritten signatures required for mail/fax (digital/typed INVALID there); e-signature = online submission only; joint filers separate 2848s; taxpayer-first sequence gives the rep 45 days (60 abroad), rep-first has no limit; entity signer/title rules.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "Unenrolled return preparers — limits + AFSP requirements (i2848 9-2021 verbatim)",
            "excerpt_text": (
                "Unenrolled return preparers may only represent taxpayers before revenue agents, customer "
                "service representatives, or similar officers and employees of the Internal Revenue Service "
                "(including the Taxpayer Advocate Service) during an examination of the tax period covered by "
                "the tax return they prepared and signed (or prepared if there is no signature space on the "
                "form). Unenrolled return preparers cannot represent taxpayers, regardless of the "
                "circumstances requiring representation, before appeals officers, revenue officers, attorneys "
                "from the Office of Chief Counsel, or similar officers or employees... cannot execute closing "
                "agreements, extend the statutory period for tax assessments or collection of tax, execute "
                "waivers, execute claims for refund, or sign any document on behalf of a taxpayer. "
                "[Requirements:] a valid and active Preparer Tax Identification Number (PTIN); eligible to "
                "sign the return or claim for refund under examination; and for returns prepared and signed "
                "after December 31, 2015, (1) a valid Annual Filing Season Program Record of Completion for "
                "the calendar year in which the tax return or claim for refund was prepared and signed, and "
                "(2) a valid Annual Filing Season Program Record of Completion for the year or years in which "
                "the representation occurs. If an unenrolled return preparer does not meet all of the "
                "representation requirements, you may authorize the unenrolled return preparer to inspect "
                "and/or receive your tax information by filing a Form 8821."
            ),
            "summary_text": "Designation h: exam-only representation of returns they prepared+signed, before agents/customer-service only (never appeals/collection/counsel); needs active PTIN + signing eligibility + AFSP Records for BOTH the prep year and representation year(s); else 8821 info-only.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "Line 4 specific-use list + line 5a sign-a-return authority (i2848 9-2021 verbatim substance)",
            "excerpt_text": (
                "A specific-use power of attorney is a one-time or specific-issue grant of authority... that "
                "the IRS does not record on the CAF. Examples: requests for a private letter ruling or "
                "technical advice; applications for an EIN; claims filed on Form 843; corporate dissolutions; "
                "Circular 230 Disciplinary Investigations and Proceedings; requests to change accounting "
                "methods or periods; applications for recognition of exemption (Forms 1023, 1024, or 1028); "
                "employee benefit plan determinations (Forms 5300, 5307, 5316, or 5310); Form W-7 ITIN "
                "applications; Form 4361; section 7623 whistleblower awards; EPCRS submissions; FOIA "
                "requests. If you check the box on line 4, the representative should mail or fax the power of "
                "attorney to the IRS office handling the matter. A specific-use power of attorney will not "
                "revoke any prior powers of attorney recorded on the CAF. Line 5a sign-a-return: Treasury "
                "Regulations section 1.6012-1(a)(5) permits another person to sign an income tax return for "
                "you only in these circumstances: (a) disease or injury, (b) continuous absence from the "
                "United States (including absence from Puerto Rico) for a period of at least 60 days prior to "
                "the date required by law for filing the return, or (c) specific permission is requested of "
                "and granted by the IRS for other good cause. Check the box on line 5a and include the "
                "prescribed 'This power of attorney is being filed pursuant to 26 CFR 1.6012-1(a)(5)...' "
                "statement on the lines provided."
            ),
            "summary_text": "L4 specific-use examples (PLR, EIN, 843, dissolutions, Circular 230 proceedings, method/period changes, exemption apps, plan determinations, W-7, 4361, 7623, EPCRS, FOIA) — goes to the office handling the matter; L5a sign-a-return only per §1.6012-1(a)(5) (disease/injury, 60-day absence, IRS permission) + the prescribed statement.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "Revocation/withdrawal + where-to-file chart (i2848 9-2021 verbatim substance)",
            "excerpt_text": (
                "Revocation: write 'REVOKE' across the top of the first page with a current signature and "
                "date below this annotation, then mail or fax a copy to the IRS using the Where To File "
                "Chart... Without a copy, send a statement of revocation listing the matters and years/"
                "periods and each representative (write 'revoke all years/periods' if revoking completely). "
                "Withdrawal by representative: write 'WITHDRAW' across the top of the first page with a "
                "current signature and date... Filing Form 2848 will not revoke any Form 8821 that is in "
                "effect. Where To File Chart: [AL AR CT DE DC FL GA IL IN KY LA ME MD MA MI MS NH NJ NY NC OH "
                "PA RI SC TN VT VA WV] -> Internal Revenue Service, 5333 Getwell Road, Stop 8423, Memphis, TN "
                "38118, fax 855-214-7519. [AK AZ CA CO HI ID IA KS MN MO MT NE NV NM ND OK OR SD TX UT WA WI "
                "WY] -> Internal Revenue Service, 1973 Rulon White Blvd., MS 6737, Ogden, UT 84201, fax "
                "855-214-7522. [APO/FPO, territories, foreign] -> International CAF Team, 2970 Market Street, "
                "MS: 4-H14.123, Philadelphia, PA 19104, fax 855-772-3156 (304-707-9785 outside the United "
                "States). These numbers may change without notice — check IRS.gov/Form2848 Recent "
                "Developments. Online: submit securely at IRS.gov/Submit2848. For faster processing of "
                "certain authorizations, use the all-digital Tax Pro Account at IRS.gov/TaxProAccount; most "
                "requests record immediately to the CAF."
            ),
            "summary_text": "REVOKE/WITHDRAW top-margin annotation + signature/date (statement alternative; 'revoke all years/periods' allowed there); 2848 never revokes an 8821; Memphis/Ogden/Philadelphia chart + faxes (year-watched); online at IRS.gov/Submit2848; Tax Pro Account records to CAF immediately.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "IRS_2848_RECDEV", "source_type": "official_guidance", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "IRS Recent Development — Items to consider while completing Form 2848 (08-Jul-2026)",
        "citation": "irs.gov/forms-pubs/items-to-consider-while-completing-form-2848 (posted 08-Jul-2026)",
        "issuer": "Internal Revenue Service",
        "official_url": "https://www.irs.gov/forms-pubs/items-to-consider-while-completing-form-2848",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.0, "topics": ["poa_2848"],
        "excerpts": [{
            "excerpt_label": "'Modified' CAF status + the line-4 caution (Recent Development 08-Jul-2026 verbatim substance)",
            "excerpt_text": (
                "A Form 2848 is classified as 'modified' when recorded on the Centralized Authorization File "
                "(CAF) when line 5a contains authorizations other than disclosure, representative "
                "substitution, or return signing, or when line 5b limits the representative's authority in "
                "any way. A 'modified' authorization prevents representatives from accessing the Transcript "
                "Delivery System to obtain IRS transcripts and from using IRS Tax Pro Account to establish "
                "installment agreements. To avoid these complications, forms should not contain entries in "
                "lines 5a or 5b that trigger 'modified' status. Checking the line 4 box prevents CAF "
                "recording entirely: taxpayers and representatives should never check line 4 unless Form 2848 "
                "is, in fact, a specific-use form."
            ),
            "summary_text": "5a entries beyond disclosure/substitution/return-signing OR any 5b limitation -> 'modified' CAF -> the rep loses TDS transcript access + Tax Pro Account installment agreements; never check line 4 unless truly specific-use.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "REG_601503", "source_type": "regulation", "source_rank": "controlling",
        "jurisdiction_code": "US", "title": "26 CFR 601.503 — requirements for a power of attorney (Conference & Practice)",
        "citation": "26 CFR 601.503(a)/(b)(2)/(c)(6)/(d); Pub. 216, Conference and Practice Requirements",
        "issuer": "U.S. Treasury",
        "official_url": "https://www.law.cornell.edu/cfr/text/26/601.503",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.2, "topics": ["poa_2848"],
        "excerpts": [{
            "excerpt_label": "Substitute POA + signer authority (via i2848, verbatim substance)",
            "excerpt_text": (
                "The IRS will accept a power of attorney other than Form 2848 provided the document satisfies "
                "the requirements for a power of attorney (Pub. 216; 26 CFR 601.503(a)). These alternative "
                "powers of attorney cannot, however, be recorded on the CAF unless you attach a completed "
                "Form 2848. You are not required to sign Form 2848 when you attach it to an alternative power "
                "of attorney that you have signed, but your representative must sign the form in Part II "
                "(26 CFR 601.503(b)(2)). Dissolved partnerships: see 26 CFR 601.503(c)(6). Estates: only one "
                "co-executor having the authority to bind the estate is required to sign (26 CFR 601.503(d)); "
                "dissolved corporations, deceased individuals, insolvents, and fiduciary appointments also "
                "ride 601.503(d)."
            ),
            "summary_text": "Non-IRS POAs acceptable per Pub. 216/601.503(a) but CAF-recordable only with a completed 2848 attached (taxpayer signature waived, rep still signs Part II); 601.503(c)(6)/(d) signer-authority rules.",
            "is_key_excerpt": True,
        }],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_F2848", "2848", "governs"), ("IRS_I2848", "2848", "governs"),
    ("IRS_2848_RECDEV", "2848", "governs"), ("REG_601503", "2848", "governs"),
]


F2848_FACTS: list[dict] = [
    {"fact_key": "plan_number", "label": "Plan number, if applicable (L1; employee plans enter the 3-digit number)", "data_type": "string", "required": False, "sort_order": 1},
    {"fact_key": "num_representatives", "label": "Representatives named (the form holds 4; more requires 'See attached' + additional 2848s)", "data_type": "integer", "required": False, "sort_order": 2},
    {"fact_key": "more_reps_attached", "label": "'See attached for additional representatives' + additional Form(s) 2848 attached", "data_type": "boolean", "required": False, "sort_order": 3},
    {"fact_key": "num_notice_copy_reps", "label": "Representatives checked to receive notice copies (max 2)", "data_type": "integer", "required": False, "sort_order": 4},
    {"fact_key": "rep_designation", "label": "Representative designation (Part II letter)", "data_type": "choice", "required": False, "sort_order": 5,
     "choices": ["a", "b", "c", "d", "e", "f", "g", "h", "k", "r"],
     "notes": "a attorney / b CPA / c EA / d officer / e employee / f family / g enrolled actuary / h unenrolled preparer / k student-LITC-STCP / r ERPA. Per-representative in the app; the fact carries the primary rep."},
    {"fact_key": "rep_caf_no", "label": "Representative CAF number (9-digit; 'None' for a first-timer — the IRS issues one)", "data_type": "string", "required": False, "sort_order": 6,
     "notes": "The app autofills from the Preparer record (the S-20c value-add). PPS 866-860-4259 retrieves forgotten CAF numbers."},
    {"fact_key": "rep_ptin", "label": "Representative PTIN ('applied for' if pending; REQUIRED for designation h)", "data_type": "string", "required": False, "sort_order": 7},
    {"fact_key": "matter_description", "label": "L3 Description of Matter (Income, Employment, Civil Penalty, etc.)", "data_type": "string", "required": False, "sort_order": 8},
    {"fact_key": "tax_form_number", "label": "L3 Tax Form Number (1040, 941, 720, ...; 'Not Applicable' when none)", "data_type": "string", "required": False, "sort_order": 9},
    {"fact_key": "periods_listed", "label": "L3 Year(s)/Period(s) (ranges via through/thru/hyphen; fiscal YYYYMM; short-period dates)", "data_type": "string", "required": False, "sort_order": 10},
    {"fact_key": "has_general_reference", "label": "L3 uses a general reference ('All years'/'All periods'/'All taxes') — the IRS RETURNS the POA", "data_type": "boolean", "required": False, "sort_order": 11},
    {"fact_key": "receipt_year", "label": "Year the IRS receives the POA (starts the future-period CAF clock)", "data_type": "integer", "required": False, "sort_order": 12},
    {"fact_key": "latest_future_period_year", "label": "Latest future tax year/period listed on L3", "data_type": "integer", "required": False, "sort_order": 13},
    {"fact_key": "line4_specific_use", "label": "L4 — specific use not recorded on the CAF (checkbox)", "data_type": "boolean", "required": False, "sort_order": 14},
    {"fact_key": "l5a_isp_access", "label": "L5a — access IRS records via an Intermediate Service Provider", "data_type": "boolean", "required": False, "sort_order": 15},
    {"fact_key": "l5a_disclose_third_party", "label": "L5a — authorize disclosure to third parties", "data_type": "boolean", "required": False, "sort_order": 16},
    {"fact_key": "l5a_substitute_add", "label": "L5a — substitute or add representative(s)", "data_type": "boolean", "required": False, "sort_order": 17},
    {"fact_key": "l5a_sign_return", "label": "L5a — sign a return (§1.6012-1(a)(5) reasons only + the prescribed statement)", "data_type": "boolean", "required": False, "sort_order": 18},
    {"fact_key": "sign_return_reason", "label": "Sign-a-return reason (§1.6012-1(a)(5))", "data_type": "choice", "required": False, "sort_order": 19,
     "choices": ["none", "disease_injury", "absent_60_days", "irs_permission"]},
    {"fact_key": "l5a_other_acts", "label": "L5a — other acts authorized (free text; ⚠ triggers 'modified' CAF status)", "data_type": "boolean", "required": False, "sort_order": 20},
    {"fact_key": "l5b_any_limits", "label": "L5b — any listed limitation on the representative's authority (⚠ triggers 'modified' CAF status)", "data_type": "boolean", "required": False, "sort_order": 21},
    {"fact_key": "line6_retain_prior", "label": "L6 — do NOT revoke prior POA(s) (checkbox)", "data_type": "boolean", "required": False, "sort_order": 22},
    {"fact_key": "prior_poa_attached", "label": "Copy of each retained prior POA attached (REQUIRED when L6 is checked)", "data_type": "boolean", "required": False, "sort_order": 23},
    {"fact_key": "taxpayer_signed", "label": "L7 taxpayer signature + date present", "data_type": "boolean", "required": False, "sort_order": 24},
    {"fact_key": "rep_signed_first", "label": "Representative signed before the taxpayer (no time limit applies)", "data_type": "boolean", "required": False, "sort_order": 25},
    {"fact_key": "days_rep_after_taxpayer", "label": "Days between the taxpayer's signature and the representative's (taxpayer-first sequence)", "data_type": "integer", "required": False, "sort_order": 26},
    {"fact_key": "taxpayer_abroad", "label": "Taxpayer resides abroad (extends the representative window to 60 days)", "data_type": "boolean", "required": False, "sort_order": 27},
    {"fact_key": "filing_channel", "label": "How the 2848 is filed", "data_type": "choice", "required": False, "sort_order": 28,
     "choices": ["online", "fax", "mail"]},
    {"fact_key": "has_electronic_signature", "label": "Any signature is electronic/digitized (valid ONLY via online submission)", "data_type": "boolean", "required": False, "sort_order": 29},
    {"fact_key": "is_joint_return_matter", "label": "The matter involves a jointly filed return (each spouse files a separate 2848)", "data_type": "boolean", "required": False, "sort_order": 30},
    {"fact_key": "urp_has_ptin", "label": "Unenrolled preparer: valid active PTIN", "data_type": "boolean", "required": False, "sort_order": 31},
    {"fact_key": "urp_prepared_signed", "label": "Unenrolled preparer: prepared AND signed the return under examination", "data_type": "boolean", "required": False, "sort_order": 32},
    {"fact_key": "urp_afsp_prep_year", "label": "Unenrolled preparer: AFSP Record of Completion for the preparation year", "data_type": "boolean", "required": False, "sort_order": 33},
    {"fact_key": "urp_afsp_rep_year", "label": "Unenrolled preparer: AFSP Record of Completion for the representation year(s)", "data_type": "boolean", "required": False, "sort_order": 34},
]

F2848_RULES: list[dict] = [
    {"rule_id": "R-2848-SCOPE", "title": "Purpose + boundaries (8821 / Form 56 / substitute POA / one per taxpayer)", "rule_type": "routing",
     "formula": "representation -> 2848 (eligible individual, designations a-r); inspect/receive only -> Form 8821; fiduciary stands AS the taxpayer -> Form 56; non-IRS POA acceptable (Pub. 216 / 601.503(a)) but CAF-recordable only with a completed 2848 attached (rep signs Part II; taxpayer signature waived); one 2848 PER taxpayer - joint filers file separately; 2848 never changes the last-known address (8822/8822-B)",
     "inputs": ["is_joint_return_matter"], "outputs": ["form_routing"], "sort_order": 1,
     "description": "W4. Form 2848 authorizes representation before the IRS by an individual eligible to practice (Part II a-r) and carries inspect/receive authority. Form 8821 grants information access WITHOUT representation. A fiduciary files Form 56 and stands in the taxpayer's shoes. A separate Form 2848 must be completed for each taxpayer; spouses on a joint return each execute their own. Address blocks never update the last-known address."},
    {"rule_id": "R-2848-REPS", "title": "Representative constraints (4 blocks / 2 notice copies / CAF+PTIN)", "rule_type": "validation",
     "formula": "num_representatives <= 4 OR more_reps_attached ('See attached' + additional 2848s); num_notice_copy_reps <= 2; each rep carries a 9-digit CAF number or 'None' (IRS issues one) + PTIN if applicable; representatives sign Part II in the order listed on line 2",
     "inputs": ["num_representatives", "more_reps_attached", "num_notice_copy_reps", "rep_caf_no", "rep_ptin"],
     "outputs": ["rep_count_ok", "notice_copy_ok"], "sort_order": 2,
     "description": "W2. The form holds four representative blocks; naming more requires writing 'See attached for additional representatives' and attaching additional Form(s) 2848. No more than TWO representatives may receive copies of notices and communications. The CAF number is the representative's unique nine-digit identifier (enter 'None' for a first-timer); PPS (866-860-4259) retrieves forgotten CAF numbers. The app autofills the preparer's name/address/CAF/PTIN/phone/fax from the Preparer record (the S-20c value-add)."},
    {"rule_id": "R-2848-MATTER", "title": "Line 3 validity (matter/form/periods; no general references)", "rule_type": "validation",
     "formula": "valid iff matter_description present AND tax_form_number present-or-'Not Applicable' AND periods present-or-'Not Applicable' AND NOT has_general_reference. Ranges via through/thru/hyphen; fiscal years YYYYMM; short periods begin-end dates; estate tax -> decedent's date of death; non-BBA 1065/1120-S -> 'Income including pass-through items'; BBA -> 'Centralized Partnership Audit Regime (BBA)'; non-return penalties -> 'Civil Penalty' (IRA: 'IRA Civil Penalty')",
     "inputs": ["matter_description", "tax_form_number", "periods_listed", "has_general_reference"],
     "outputs": ["line3_valid"], "sort_order": 3,
     "description": "W1. Line 3 must carry the description of the matter, the tax form number (where applicable), and the year(s)/period(s) (where applicable). 'Do not use a general reference such as All years, All periods, or All taxes. The IRS will return any power of attorney with a general reference.' Return-related penalties and interest ride the line-3 authorization by default unless deleted on 5b."},
    {"rule_id": "R-2848-FUTURE", "title": "Future-period CAF clock (Dec 31 receipt year + 3)", "rule_type": "calculation",
     "formula": "future period recordable iff period_year <= receipt_year + 3 (the CAF will not record future tax years/periods that exceed 3 years from December 31 of the year the IRS receives the POA)",
     "inputs": ["receipt_year", "latest_future_period_year"], "outputs": ["future_recordable"], "sort_order": 4,
     "description": "W1. Current and ended periods are always listable. Future periods are allowed, but the CAF records only those within 3 years of December 31 of the receipt year — a POA received in 2026 is recordable through 2029; later periods need a new POA filed closer in time."},
    {"rule_id": "R-2848-SIGNSEQ", "title": "Signature sequence — the 45/60-day representative window", "rule_type": "validation",
     "formula": "taxpayer signs first -> representative must sign within 45 days (60 if the taxpayer resides abroad); representative signs first -> no time limit for the taxpayer; unsigned or undated (either part) -> the IRS returns the POA",
     "inputs": ["taxpayer_signed", "rep_signed_first", "days_rep_after_taxpayer", "taxpayer_abroad"],
     "outputs": ["rep_signature_timely"], "sort_order": 5,
     "description": "W3. Generally the taxpayer signs first and the representative accepts: domestic authorizations give the representative 45 days from the taxpayer's signature date (60 days for taxpayers residing abroad). If the representative signs first, the taxpayer has no required time limit. Part I unsigned/undated or Part II unsigned/undated -> the IRS returns the power of attorney. Representatives sign in the order listed on line 2."},
    {"rule_id": "R-2848-FILE", "title": "Filing route (line 4 / e-signature channel rule)", "rule_type": "routing",
     "formula": "line4_specific_use -> mail/fax to the IRS office handling the matter. Otherwise: electronic signature -> ONLINE ONLY (IRS.gov/Submit2848); handwritten -> online, fax, or mail per the Memphis/Ogden/Philadelphia chart",
     "inputs": ["line4_specific_use", "has_electronic_signature", "filing_channel"], "outputs": ["filing_route"], "sort_order": 6,
     "description": "W3/W4. Handwritten signatures are required for mail/fax filings — digital, electronic, or typed-font signatures are NOT valid on mailed or faxed 2848s; an electronically signed 2848 may only be submitted online (with the remote-transaction identity-authentication duties). Line-4 (specific-use) POAs go directly to the office handling the matter. Chart (year-watched): Memphis fax 855-214-7519 (eastern incl. GA) / Ogden fax 855-214-7522 (western + WI) / Philadelphia International CAF Team fax 855-772-3156."},
    {"rule_id": "R-2848-AUTH", "title": "Authority granted + 'modified'-CAF hygiene (5a/5b; Rec. Dev. 08-Jul-2026)", "rule_type": "routing",
     "formula": "default authority = all acts for the listed matters EXCEPT check negotiation (always barred); ISP access / third-party disclosure / substitute-add / sign-a-return require their 5a boxes; sign-a-return only per §1.6012-1(a)(5) (disease_injury / absent_60_days / irs_permission) + the prescribed statement. modified_caf = l5a_other_acts OR l5b_any_limits -> blocks TDS transcript access + Tax Pro Account installment agreements",
     "inputs": ["l5a_isp_access", "l5a_disclose_third_party", "l5a_substitute_add", "l5a_sign_return", "sign_return_reason", "l5a_other_acts", "l5b_any_limits"],
     "outputs": ["modified_caf"], "sort_order": 7,
     "description": "W4. The POA grants all acts the taxpayer can perform for the listed matters except negotiating government checks (always barred) and the four enumerated acts that need their 5a boxes. Per the 08-Jul-2026 Recent Development: entries on 5a OTHER than disclosure/substitution/return-signing, or ANY 5b limitation, record the POA as 'modified' on the CAF — which blocks the representative's Transcript Delivery System access and Tax Pro Account installment agreements. Sign-a-return requires a §1.6012-1(a)(5) reason and the prescribed statement; Form 907 signing needs explicit 5a language."},
    {"rule_id": "R-2848-URP", "title": "Unenrolled return preparer (h) representation gate", "rule_type": "validation",
     "formula": "URP may represent iff: valid active PTIN AND prepared-and-signed the return under exam AND AFSP Record for the preparation year AND AFSP Record for the representation year(s). Scope even then: exam-only, before revenue agents / customer service / similar (incl. TAS); NEVER appeals, revenue officers, or Chief Counsel; no closing agreements, statute extensions, waivers, refund claims, or signing documents. Unmet -> Form 8821 information access only",
     "inputs": ["urp_has_ptin", "urp_prepared_signed", "urp_afsp_prep_year", "urp_afsp_rep_year"],
     "outputs": ["urp_can_represent"], "sort_order": 8,
     "description": "W2. Designation h carries LIMITED representation rights: only during an examination of the tax period covered by the return the preparer prepared and signed, only before revenue agents / customer service representatives / similar officers (including TAS). All four requirements must hold (PTIN, signing eligibility, AFSP for the prep year, AFSP for the representation years). Otherwise route the client to Form 8821 for information access."},
    {"rule_id": "R-2848-REVOKE", "title": "Line 6 retention / revocation + REVOKE/WITHDRAW mechanics", "rule_type": "routing",
     "formula": "default: CAF recording auto-revokes earlier POAs for the same matters and periods (specific-use POAs revoke only same-office/same-matter priors). line6_retain_prior -> a copy of EACH retained POA MUST be attached. 2848 never revokes a Form 8821. Standalone revocation = 'REVOKE' (rep withdrawal = 'WITHDRAW') across the top of page 1 + current signature/date, mailed/faxed per the chart; statement alternative allowed ('revoke all years/periods' permitted THERE). A new BBA PR files a NEW 2848 (does not check line 6)",
     "inputs": ["line6_retain_prior", "prior_poa_attached"], "outputs": ["retention_valid"], "sort_order": 9,
     "description": "W4. Filing automatically revokes earlier powers of attorney on file for the same matters and years/periods unless line 6 is checked — and a copy of any POA to remain in effect MUST be attached. Standalone revocation/withdrawal rides the top-margin annotation (or the signed statement listing matters/periods and representatives). Filing a 2848 does not revoke any Form 8821."},
]

F2848_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-2848-SCOPE", "IRS_I2848", "primary", "Purpose of Form + 8821/Form 56 boundaries"),
    ("R-2848-SCOPE", "REG_601503", "secondary", "Substitute POA (Pub. 216 / 601.503)"),
    ("R-2848-REPS", "IRS_F2848", "primary", "L2 four blocks + two-notice-copy note"),
    ("R-2848-REPS", "IRS_I2848", "secondary", "CAF number / PTIN / attach-for-more"),
    ("R-2848-MATTER", "IRS_I2848", "primary", "L3 validity + general-reference return rule"),
    ("R-2848-FUTURE", "IRS_I2848", "primary", "Future periods: Dec 31 receipt year + 3"),
    ("R-2848-SIGNSEQ", "IRS_I2848", "primary", "L7 45/60-day note + signer rules"),
    ("R-2848-SIGNSEQ", "IRS_F2848", "secondary", "L7/Part II return-if-unsigned banners"),
    ("R-2848-SIGNSEQ", "REG_601503", "secondary", "601.503(d) estate/fiduciary signers"),
    ("R-2848-FILE", "IRS_I2848", "primary", "How To File + where-to-file chart + e-sign rule"),
    ("R-2848-AUTH", "IRS_I2848", "primary", "Authority granted + L5a acts + §1.6012-1(a)(5)"),
    ("R-2848-AUTH", "IRS_2848_RECDEV", "primary", "'Modified' CAF (5a-other/5b) + line-4 caution"),
    ("R-2848-URP", "IRS_I2848", "primary", "URP special rules + AFSP requirements"),
    ("R-2848-URP", "IRS_F2848", "secondary", "Designation h conditions on the face"),
    ("R-2848-REVOKE", "IRS_I2848", "primary", "L6 + REVOKE/WITHDRAW mechanics"),
    ("R-2848-REVOKE", "IRS_F2848", "secondary", "L6 attach-to-retain banner"),
]

F2848_LINES: list[dict] = [
    # Part I
    {"line_number": "L1_NAME", "description": "L1 — Taxpayer name and address (entity variants: trustee+trust, executor+decedent, plan sponsor, BBA PR-for-partnership)", "line_type": "input", "sort_order": 1},
    {"line_number": "L1_TIN", "description": "L1 — Taxpayer identification number(s) (Sch-C sole proprietor: SSN + business EIN; BBA: the PARTNERSHIP TIN, never the PR's)", "line_type": "input", "sort_order": 2},
    {"line_number": "L1_PHONE", "description": "L1 — Daytime telephone number", "line_type": "input", "sort_order": 3},
    {"line_number": "L1_PLAN_NO", "description": "L1 — Plan number (employee plans; 3 digits)", "line_type": "input", "source_facts": ["plan_number"], "sort_order": 4},
    {"line_number": "L2_REP_NAME", "description": "L2 — Representative name and address (×4 blocks; app autofills from the Preparer record)", "line_type": "input", "sort_order": 5},
    {"line_number": "L2_REP_CAF", "description": "L2 — CAF No. (9-digit; 'None' for a first-timer)", "line_type": "input", "source_facts": ["rep_caf_no"], "sort_order": 6},
    {"line_number": "L2_REP_PTIN", "description": "L2 — PTIN", "line_type": "input", "source_facts": ["rep_ptin"], "sort_order": 7},
    {"line_number": "L2_REP_PHONE", "description": "L2 — Telephone / Fax (+ check-if-new boxes)", "line_type": "input", "sort_order": 8},
    {"line_number": "L2_NOTICES", "description": "L2 — Copies-of-notices checkboxes (blocks 1-2 only; max two designees)", "line_type": "input", "source_rules": ["R-2848-REPS"], "sort_order": 9},
    {"line_number": "L3_MATTER", "description": "L3 — Description of Matter (Income / Employment / Civil Penalty / BBA / 'Income including pass-through items' ...)", "line_type": "input", "source_facts": ["matter_description"], "sort_order": 10},
    {"line_number": "L3_FORM_NO", "description": "L3 — Tax Form Number (or 'Not Applicable')", "line_type": "input", "source_facts": ["tax_form_number"], "sort_order": 11},
    {"line_number": "L3_PERIODS", "description": "L3 — Year(s)/Period(s) (ranges; YYYYMM fiscal; short-period dates; NEVER 'All years')", "line_type": "input", "source_facts": ["periods_listed"], "source_rules": ["R-2848-MATTER"], "sort_order": 12},
    {"line_number": "L4_SPECIFIC", "description": "L4 — Specific use not recorded on CAF (⚠ never check unless truly specific-use — Rec. Dev. 08-Jul-2026)", "line_type": "input", "source_facts": ["line4_specific_use"], "sort_order": 13},
    {"line_number": "L5A_ISP", "description": "L5a — Access IRS records via an Intermediate Service Provider", "line_type": "input", "source_facts": ["l5a_isp_access"], "sort_order": 14},
    {"line_number": "L5A_DISCLOSE", "description": "L5a — Authorize disclosure to third parties", "line_type": "input", "source_facts": ["l5a_disclose_third_party"], "sort_order": 15},
    {"line_number": "L5A_SUBSTITUTE", "description": "L5a — Substitute or add representative(s)", "line_type": "input", "source_facts": ["l5a_substitute_add"], "sort_order": 16},
    {"line_number": "L5A_SIGN_RET", "description": "L5a — Sign a return (§1.6012-1(a)(5) + the prescribed statement)", "line_type": "input", "source_facts": ["l5a_sign_return", "sign_return_reason"], "sort_order": 17},
    {"line_number": "L5A_OTHER", "description": "L5a — Other acts authorized (⚠ records the POA as 'modified' on the CAF)", "line_type": "input", "source_facts": ["l5a_other_acts"], "sort_order": 18},
    {"line_number": "L5B_LIMITS", "description": "L5b — Specific acts not authorized (⚠ ANY entry records the POA as 'modified')", "line_type": "input", "source_facts": ["l5b_any_limits"], "sort_order": 19},
    {"line_number": "L6_RETAIN", "description": "L6 — Do-not-revoke checkbox (MUST attach a copy of each retained POA)", "line_type": "input", "source_facts": ["line6_retain_prior", "prior_poa_attached"], "source_rules": ["R-2848-REVOKE"], "sort_order": 20},
    {"line_number": "L7_SIGN", "description": "L7 — Taxpayer signature / date / title / print name (handwritten for mail/fax)", "line_type": "input", "source_facts": ["taxpayer_signed"], "sort_order": 21},
    # Part II
    {"line_number": "P2_DESIGNATION", "description": "Part II — Designation letter (a-r), per representative", "line_type": "input", "source_facts": ["rep_designation"], "sort_order": 22},
    {"line_number": "P2_JURISDICTION", "description": "Part II — Licensing jurisdiction (a/b state; d-f title/position/relationship; k 'LITC'/'STCP')", "line_type": "input", "sort_order": 23},
    {"line_number": "P2_LICENSE_NO", "description": "Part II — Bar/license/certification/registration/enrollment number (c EA card; g Joint Board; h PTIN; r RPO)", "line_type": "input", "sort_order": 24},
    {"line_number": "P2_SIGN", "description": "Part II — Representative signature + date (in line-2 order; unsigned = POA returned)", "line_type": "input", "source_rules": ["R-2848-SIGNSEQ"], "sort_order": 25},
    # Computed
    {"line_number": "CALC_L3VALID", "description": "Computed line-3 validity (completeness + no general reference)", "line_type": "calculated", "source_rules": ["R-2848-MATTER"], "sort_order": 26},
    {"line_number": "CALC_FUTURE", "description": "Computed future-period recordability (receipt year + 3)", "line_type": "calculated", "source_rules": ["R-2848-FUTURE"], "sort_order": 27},
    {"line_number": "CALC_SIGNWIN", "description": "Computed representative-signature window (45/60 days; sequence-aware)", "line_type": "calculated", "source_rules": ["R-2848-SIGNSEQ"], "sort_order": 28},
    {"line_number": "CALC_MODCAF", "description": "Computed 'modified'-CAF status (5a-other / any 5b)", "line_type": "calculated", "source_rules": ["R-2848-AUTH"], "sort_order": 29},
    {"line_number": "CALC_ROUTE", "description": "Computed filing route (office-handling-matter / online-only / online-fax-mail + the state chart)", "line_type": "calculated", "source_rules": ["R-2848-FILE"], "sort_order": 30},
]

F2848_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_2848_GENREF", "title": "General reference on line 3 — the IRS will return the POA", "severity": "error",
     "condition": "has_general_reference",
     "message": "Do not use a general reference such as 'All years,' 'All periods,' or 'All taxes' on line 3. The IRS will return any power of attorney with a general reference. List specific years/periods (ranges via 'through,' 'thru,' or a hyphen; fiscal years as YYYYMM; short periods as beginning-ending dates).", "notes": "W1."},
    {"diagnostic_id": "D_2848_L3REQ", "title": "Line 3 incomplete", "severity": "error",
     "condition": "matter_description blank, or tax_form_number/periods blank without 'Not Applicable'",
     "message": "For the power of attorney to be valid, line 3 must carry the description of the matter, the tax form number (where applicable), and the year(s) or period(s) (where applicable). For non-tax or period-less matters (penalties, PLRs, FOIA, EIN applications), describe the matter and enter 'Not Applicable' in the unused column(s).", "notes": "W1."},
    {"diagnostic_id": "D_2848_FUTURE3", "title": "Future period beyond the CAF's 3-year clock", "severity": "warning",
     "condition": "latest_future_period_year > receipt_year + 3",
     "message": "The IRS will not record on the CAF system future tax years or periods that exceed 3 years from December 31 of the year the IRS receives the power of attorney. Periods beyond that horizon will simply not be recorded — file a new Form 2848 closer in time instead.", "notes": "W1."},
    {"diagnostic_id": "D_2848_REP5", "title": "More than four representatives without the attachment", "severity": "error",
     "condition": "num_representatives > 4 and not more_reps_attached",
     "message": "Form 2848 holds four representative blocks. To name more, write 'See attached for additional representatives' in the space to the right of line 2 and attach additional Form(s) 2848.", "notes": "W2."},
    {"diagnostic_id": "D_2848_NOTICE2", "title": "More than two notice-copy designees", "severity": "error",
     "condition": "num_notice_copy_reps > 2",
     "message": "You may not designate more than two representatives on Form 2848 to receive copies of notices and communications sent to you by the IRS for the same matter(s). Only the first two representative blocks carry the checkbox; uncheck the extras.", "notes": "W2."},
    {"diagnostic_id": "D_2848_SIGN45", "title": "Representative signed outside the 45/60-day window", "severity": "error",
     "condition": "not rep_signed_first and days_rep_after_taxpayer > (60 if taxpayer_abroad else 45)",
     "message": "When the taxpayer signs first, the representative must sign within 45 days from the date the taxpayer signed (60 days for authorizations from taxpayers residing abroad). A late representative signature invalidates the authorization — have both parties re-execute. (If the representative signs first, the taxpayer has no required time limit.)", "notes": "W3."},
    {"diagnostic_id": "D_2848_ESIGN", "title": "Electronic signature on a mailed/faxed 2848", "severity": "error",
     "condition": "has_electronic_signature and filing_channel in (fax, mail)",
     "message": "Digital, electronic, or typed-font signatures are NOT valid on Forms 2848 filed by mail or by fax — handwrite the signatures, or submit the electronically signed form online at IRS.gov/Submit2848 (remote-transaction identity authentication applies).", "notes": "W3."},
    {"diagnostic_id": "D_2848_UNSIGNED", "title": "Missing signature/date — the IRS will return the POA", "severity": "error",
     "condition": "not taxpayer_signed (or Part II unsigned)",
     "message": "IF NOT COMPLETED, SIGNED, AND DATED, THE IRS WILL RETURN THIS POWER OF ATTORNEY TO THE TAXPAYER — and the same banner applies to the Part II Declaration of Representative. Representatives must sign in the order listed in Part I, line 2.", "notes": "W3."},
    {"diagnostic_id": "D_2848_URP", "title": "Unenrolled return preparer — representation requirements unmet", "severity": "warning",
     "condition": "rep_designation == h and not (urp_has_ptin and urp_prepared_signed and urp_afsp_prep_year and urp_afsp_rep_year)",
     "message": "An unenrolled return preparer (designation h) may represent a taxpayer ONLY with a valid active PTIN, only for a return they prepared and signed, and only holding AFSP Records of Completion for BOTH the preparation year and the representation year(s) — and even then only before revenue agents/customer service (exam of that period), never appeals, revenue officers, or Chief Counsel. If these aren't met, use Form 8821 for information access instead.", "notes": "W2."},
    {"diagnostic_id": "D_2848_SIGNRET", "title": "Sign-a-return box needs a §1.6012-1(a)(5) reason + statement", "severity": "warning",
     "condition": "l5a_sign_return and sign_return_reason == none",
     "message": "The authority to sign the taxpayer's income tax return may be granted only for: (a) disease or injury, (b) continuous absence from the United States (including Puerto Rico) for at least 60 days before the filing deadline, or (c) specific IRS permission for other good cause. Check the 5a box AND include the prescribed statement: 'This power of attorney is being filed pursuant to 26 CFR 1.6012-1(a)(5), which requires a power of attorney to be attached to a return if a return is signed by an agent by reason of [the specific reason].'", "notes": "W4."},
    {"diagnostic_id": "D_2848_MODCAF", "title": "'Modified' CAF status — TDS and Tax Pro Account blocked", "severity": "warning",
     "condition": "l5a_other_acts or l5b_any_limits",
     "message": "Per the IRS's 08-Jul-2026 guidance: a Form 2848 records as 'MODIFIED' on the CAF when line 5a contains authorizations other than disclosure, representative substitution, or return signing — or when line 5b limits the representative's authority in any way. A modified authorization prevents the representative from accessing the Transcript Delivery System and from using Tax Pro Account to establish installment agreements. Avoid 5a-other/5b entries unless the engagement genuinely requires them.", "notes": "W4. Recent Development 08-Jul-2026."},
    {"diagnostic_id": "D_2848_L4CAF", "title": "Line 4 prevents CAF recording — confirm truly specific-use", "severity": "warning",
     "condition": "line4_specific_use",
     "message": "Checking line 4 prevents the authorization from being recorded on the CAF entirely — 'taxpayers and representatives should never check line 4 unless Form 2848 is, in fact, a specific-use form' (IRS, 08-Jul-2026). Specific uses include PLR/technical advice requests, EIN applications, Form 843 claims, corporate dissolutions, Circular 230 proceedings, accounting method/period changes, exemption applications, plan determinations, W-7, §7623 awards, EPCRS, and FOIA. Line-4 POAs go to the IRS office handling the matter.", "notes": "W4. Recent Development 08-Jul-2026."},
    {"diagnostic_id": "D_2848_RETAIN", "title": "Line 6 checked without the prior-POA attachment", "severity": "error",
     "condition": "line6_retain_prior and not prior_poa_attached",
     "message": "Filing this power of attorney automatically revokes all earlier POAs on file for the same matters and years/periods. Because the do-not-revoke box on line 6 is checked, YOU MUST ATTACH A COPY OF ANY POWER OF ATTORNEY YOU WANT TO REMAIN IN EFFECT.", "notes": "W4."},
    {"diagnostic_id": "D_2848_REVOKEALL", "title": "Revocation / withdrawal mechanics", "severity": "info",
     "condition": "informational",
     "message": "To revoke without naming a new representative: write 'REVOKE' across the top of page 1 of the existing POA with a current signature and date, then mail/fax it per the Where To File chart (representatives write 'WITHDRAW' the same way). No copy available? Send a signed statement listing the matters, periods, and representatives — 'revoke all years/periods' is permitted in a revocation statement (unlike line 3). Filing a Form 2848 never revokes a Form 8821.", "notes": "W4."},
    {"diagnostic_id": "D_2848_JOINT", "title": "Joint return — each spouse files a separate 2848", "severity": "warning",
     "condition": "is_joint_return_matter",
     "message": "A separate Form 2848 must be completed for each taxpayer: spouses who filed a joint return must each execute their own power of attorney, even when appointing the same representative(s).", "notes": "W3."},
    {"diagnostic_id": "D_2848_ADDRESS", "title": "Filing channels + address hygiene", "severity": "info",
     "condition": "informational on print",
     "message": "File online at IRS.gov/Submit2848 (required for electronic signatures; Tax Pro Account records most authorizations to the CAF immediately), or fax/mail: Memphis (5333 Getwell Road, Stop 8423, Memphis, TN 38118; fax 855-214-7519) for AL AR CT DE DC FL GA IL IN KY LA ME MD MA MI MS NH NJ NY NC OH PA RI SC TN VT VA WV; Ogden (1973 Rulon White Blvd., MS 6737, Ogden, UT 84201; fax 855-214-7522) for the western states + WI; International CAF Team, Philadelphia (fax 855-772-3156; 304-707-9785 outside the US). Numbers may change without notice — check the Form 2848 Recent Developments page. Form 2848 never updates the last-known address: use Form 8822 (home) / 8822-B (business).", "notes": "W4. Year-watched."},
    {"diagnostic_id": "D_2848_STUDENT", "title": "Student/law-graduate representative (k) — letter + 130-day purge", "severity": "info",
     "condition": "rep_designation == k",
     "message": "A qualifying student or law graduate (LITC/STCP, Circular 230 §10.7(d)) must attach a copy of the Taxpayer Advocate Service authorization letter, list the lead attorney/CPA FIRST on line 2, and enter 'LITC' or 'STCP' in the licensing-jurisdiction column. The CAF automatically purges the student representative 130 days after the taxpayer's signature date.", "notes": "W2."},
]

F2848_SCENARIOS: list[dict] = [
    {"scenario_name": "2848-A — CPA representative, income 1040, two years, timely countersign", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"rep_designation": "b", "matter_description": "Income", "tax_form_number": "1040", "periods_listed": "2024-2025",
                "has_general_reference": False, "num_representatives": 1, "num_notice_copy_reps": 1,
                "rep_signed_first": False, "days_rep_after_taxpayer": 10, "taxpayer_abroad": False, "taxpayer_signed": True,
                "receipt_year": 2026, "latest_future_period_year": 2027, "line4_specific_use": False, "has_electronic_signature": False},
     "expected_outputs": {"rep_signature_timely": True, "future_recordable": True, "modified_caf": False, "filing_route": "online_fax_or_mail"},
     "notes": "The bread-and-butter POA: CPA (b), 'Income / 1040 / 2024-2025', rep countersigns at +10 days (within 45), future period 2027 well inside the 2026+3 clock, clean 5a/5b -> full CAF recording."},
    {"scenario_name": "2848-B — 'All years' general reference: the IRS returns the POA", "scenario_type": "failure", "sort_order": 2,
     "inputs": {"matter_description": "Income", "tax_form_number": "1040", "periods_listed": "All years", "has_general_reference": True},
     "expected_outputs": {"line3_valid": False, "diagnostic": "D_2848_GENREF"},
     "notes": "i2848 verbatim: 'The IRS will return any power of attorney with a general reference.'"},
    {"scenario_name": "2848-C — future period beyond receipt year + 3 not CAF-recorded", "scenario_type": "edge", "sort_order": 3,
     "inputs": {"receipt_year": 2026, "latest_future_period_year": 2030},
     "expected_outputs": {"future_recordable": False, "diagnostic": "D_2848_FUTURE3"},
     "notes": "Received 2026 -> the CAF records future periods only through 2029 (3 years from Dec 31, 2026); 2030 is silently not recorded — the diagnostic surfaces it."},
    {"scenario_name": "2848-D — representative countersigned on day 50 (domestic): invalid", "scenario_type": "failure", "sort_order": 4,
     "inputs": {"rep_signed_first": False, "days_rep_after_taxpayer": 50, "taxpayer_abroad": False, "taxpayer_signed": True},
     "expected_outputs": {"rep_signature_timely": False, "diagnostic": "D_2848_SIGN45"},
     "notes": "Taxpayer-first sequence gives the representative 45 days; day 50 is out. Re-execute."},
    {"scenario_name": "2848-E — taxpayer abroad: day 50 countersign is timely (60-day window)", "scenario_type": "edge", "sort_order": 5,
     "inputs": {"rep_signed_first": False, "days_rep_after_taxpayer": 50, "taxpayer_abroad": True, "taxpayer_signed": True},
     "expected_outputs": {"rep_signature_timely": True},
     "notes": "Authorizations from taxpayers residing abroad get 60 days; day 50 passes. (Rep-signs-first has no limit at all.)"},
    {"scenario_name": "2848-F — unenrolled preparer with full AFSP: limited representation OK", "scenario_type": "edge", "sort_order": 6,
     "inputs": {"rep_designation": "h", "urp_has_ptin": True, "urp_prepared_signed": True, "urp_afsp_prep_year": True, "urp_afsp_rep_year": True},
     "expected_outputs": {"urp_can_represent": True},
     "notes": "All four URP requirements met -> exam-only representation before agents/customer service for the prepared-and-signed period."},
    {"scenario_name": "2848-G — unenrolled preparer missing the representation-year AFSP", "scenario_type": "failure", "sort_order": 7,
     "inputs": {"rep_designation": "h", "urp_has_ptin": True, "urp_prepared_signed": True, "urp_afsp_prep_year": True, "urp_afsp_rep_year": False},
     "expected_outputs": {"urp_can_represent": False, "diagnostic": "D_2848_URP"},
     "notes": "The AFSP Record must cover BOTH the preparation year and the representation year(s); missing either kills representation -> route to Form 8821."},
    {"scenario_name": "2848-H — a 5b limitation records the POA as 'modified' (TDS blocked)", "scenario_type": "edge", "sort_order": 8,
     "inputs": {"l5a_other_acts": False, "l5b_any_limits": True},
     "expected_outputs": {"modified_caf": True, "diagnostic": "D_2848_MODCAF"},
     "notes": "Rec. Dev. 08-Jul-2026: ANY 5b limitation -> 'modified' CAF -> no Transcript Delivery System access, no Tax Pro Account installment agreements. Same for 5a entries beyond disclosure/substitution/return-signing."},
    {"scenario_name": "2848-I — e-signature faxed in / line 6 without the attachment", "scenario_type": "failure", "sort_order": 9,
     "inputs": {"has_electronic_signature": True, "filing_channel": "fax", "line4_specific_use": False,
                "line6_retain_prior": True, "prior_poa_attached": False},
     "expected_outputs": {"filing_route": "online_only", "retention_valid": False, "diagnostics": ["D_2848_ESIGN", "D_2848_RETAIN"]},
     "notes": "Electronic signatures ride ONLY the online channel (handwritten required for mail/fax); and a checked line 6 without the attached prior POA copies is invalid — YOU MUST ATTACH."},
]

FORMS: list[dict] = [
    {
        "identity": {"form_number": "2848", "form_title": "Form 2848 — Power of Attorney and Declaration of Representative (Rev. 1-2021)",
                     "notes": "WO-27 (SPINE S-20c). Administrative POA, print-first (mail/fax/online at IRS.gov/Submit2848 — no MeF). One 2848 PER taxpayer (joint filers separate). L2: four rep blocks (CAF 9-digit or 'None'; PTIN; max TWO notice-copy designees) — the app autofills from the Preparer record (the S-20c value-add). L3 validity: matter + form + periods, ranges through/thru/hyphen, fiscal YYYYMM, NO general references (IRS returns the POA); future periods CAF-recordable only through Dec 31 receipt-year + 3. Signatures: handwritten for mail/fax (e-sign = online only + remote authentication); taxpayer-first gives the rep 45 days (60 abroad); unsigned either part = returned. Designations a-r incl. the URP (h) gate (PTIN + prepared-signed + AFSP both years; exam-only) and the student (k) 130-day CAF purge. 5a acts (ISP/disclosure/substitute/sign-return per §1.6012-1(a)(5)); ⚠ Rec. Dev. 08-Jul-2026: 5a-other/any-5b -> 'MODIFIED' CAF (blocks TDS + Tax Pro Account IAs); never check L4 unless truly specific-use. L6 auto-revoke default + attach-to-retain; REVOKE/WITHDRAW margin mechanics; 8821/Form 56 boundaries. Chart: Memphis 855-214-7519 / Ogden 855-214-7522 / Philadelphia Intl 855-772-3156 (year-watched). Rev. 1-2021 + i2848 9-2021 current. entity_types ['1040','1120S','1065','1120','1041','709']."},
        "facts": F2848_FACTS, "rules": F2848_RULES, "rule_links": F2848_RULE_LINKS,
        "lines": F2848_LINES, "diagnostics": F2848_DIAGNOSTICS, "scenarios": F2848_SCENARIOS,
    },
]

# Staged DRAFT deliberately (the new-FAs-default-ACTIVE trap): the tts build leg activates + writes
# runners + refreshes the export-verbatim mirrors in ONE motion.
FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-2848-FUTURE", "title": "Future-period CAF recordability = receipt year + 3", "assertion_type": "reconciliation",
     "entity_types": ["1040", "1120S", "1065", "1120", "1041", "709"], "status": "draft", "sort_order": 1,
     "description": "future_recordable iff period_year <= receipt_year + 3 (3 years from December 31 of the year the IRS receives the POA). Pins: (2026, 2029) -> True; (2026, 2030) -> False.",
     "definition": {"rule": "R-2848-FUTURE", "check": "period_year <= receipt_year + 3"}},
    {"assertion_id": "FA-2848-SIGN45", "title": "Representative signature window: 45 domestic / 60 abroad / none when rep-first", "assertion_type": "reconciliation",
     "entity_types": ["1040", "1120S", "1065", "1120", "1041", "709"], "status": "draft", "sort_order": 2,
     "description": "rep_signature_timely = rep_signed_first OR days <= (60 if taxpayer_abroad else 45). Pins: (10, domestic) timely; (50, domestic) late; (50, abroad) timely.",
     "definition": {"rule": "R-2848-SIGNSEQ", "check": "days <= 45 (domestic) / 60 (abroad); rep-first = no limit"}},
    {"assertion_id": "FA-2848-CAFFILL", "title": "L2 preparer autofill carries a valid CAF/PTIN shape", "assertion_type": "reconciliation",
     "entity_types": ["1040", "1120S", "1065", "1120", "1041", "709"], "status": "draft", "sort_order": 3,
     "description": "The app-side value-add: line 2 autofilled from the Preparer record must carry a nine-digit CAF number or the literal 'None' (first-timer), plus the PTIN when the preparer holds one — never an SSN/EIN in the CAF box.",
     "definition": {"rule": "R-2848-REPS", "check": "rep_caf_no matches 9-digit or 'None'; PTIN present when held; sourced from the Preparer record"}},
]


class Command(BaseCommand):
    help = "Load the Form 2848 spec (Power of Attorney, Rev. 1-2021). Refuses to seed until READY_TO_SEED=True (Gate-1 W1-W4)."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad Form 2848 spec (Power of Attorney and Declaration of Representative)\n"))
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
                "\nREFUSING TO SEED FORM 2848: not cleared.\n\n"
                "Gated until Ken approves the Gate-1 walk (W1 line-3 validity + future clock; W2 rep\n"
                "constraints + URP gate; W3 signature mechanics; W4 CAF hygiene + revocation + scope)\n"
                "and flips the sentinel.\n\n"
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
        self.stdout.write(f"  {len(FLOW_ASSERTIONS)} flow assertions (staged DRAFT)")

    def _report(self):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("Form 2848 loaded.")
        self.stdout.write(f"  2848: facts {len(F2848_FACTS)} / rules {len(F2848_RULES)} / lines {len(F2848_LINES)} / diag {len(F2848_DIAGNOSTICS)} / tests {len(F2848_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}")
        self.stdout.write("=" * 60)
