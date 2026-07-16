"""Load the 8879 / 8878 e-file signature-authorization pair spec (8879 Rev. 01-2021 - 8878 2025).
WO-33 (tts s90 draft-to-gate). Greenfield (gaps confirmed 404 x4 on 2026-07-15:
lookup/{8879,FORM_8879,8878,FORM_8878}).

=============================================================================
WHAT THIS IS
=============================================================================
The e-file SIGNATURE AUTHORIZATION print pair. NEITHER FORM TRANSMITS - both faces say
"ERO Must Retain This Form - Don't Submit This Form to the IRS Unless Requested To Do So."
The electronic mirror is the Return Header signature block tts ALREADY e-files (PINTypeCd /
JuratDisclosureCd / PractitionerPINGrp / signature PINs - ATS-proven). The tts leg = a
persistent signature-input surface + two AcroForm print units + diagnostics tying the
printed authorization to the header PIN data + extract gating. The print-only V/ES recipe
(s87) with a HEADER tie instead of a payment tie.

The 8879 rides the RETURN (1040/1040-SR/1040-NR/1040-SS/1040-X, original AND amended);
the 8878 rides the EXTENSION (4868 with EFW, or 2350). The 8878's load-bearing negative:
a 4868 WITHOUT an electronic funds withdrawal NEVER needs an 8878 - the print-side mirror
of the s88 R0000-098 story (a no-payment e-filed 4868 carries no signature at all).

v1 SCOPE - PROPOSED (Gate-1 walk W1-W4 AWAITING KEN; see f8879_8878_source_brief.md):
W1. The 8879 need-gate (required iff Practitioner PIN method OR ERO enters/generates the
    taxpayer's PIN - the face's 4-row chart; Part III only on the PP rows) + Part I amounts
    off the 1040 face (whole dollars; 1040-SS = line 4 only, app boundary; 1040-X column-C
    arm - walk seam 2).
W2. Signature mechanics: 5-digit non-zero PINs; EFIN+PIN Part III (11 digits); sign-BEFORE-
    transmit; SID-after-filing or Form 9325 association; 3-year retention (Rev. Proc.
    97-22); MFJ split-authorization + the absent-spouse bar; corrected copy + the Pub-1345
    $50/$14 re-sign tolerance; the 3-day stockpiling clock; the under-16 + duplicate-SSN
    self-select bars; prior-year ORIGINALLY-FILED authentication for non-PP.
W3. The 8878 gate: EFW AND (PP OR ERO-entered) for the 4868; ERO-entered for the 2350;
    Part I one-box + the 4868-line-7 tie; Part III is "Form 4868 Only" - a 2350 never
    reaches it; the 2350 arm = stated APP BOUNDARY (no 2350 module in tts).
W4. Ties + print: entity_types ['1040']; print-only pair (NO MeF document BY DESIGN);
    extract-refusal recommendation when the required authorization lacks a signed date
    (walk seam 3); the e-signature/KBA framework recorded as FACTS (portal future);
    year-watch on the year-dated 8878 face.

CARRIED [UNVERIFIED]: none - verbatim vs Form 8879 (Rev. January 2021, Cat. 32778X,
self-contained instructions; About: Recent Developments none, 30-Mar-2026) + Form 8878
(2025, Cat. 32777M, Created 4/17/25; About: none) + Pub. 1345 signature chapter (current
PDF pp. 14-18) + efileTypes/ReturnHeader1040x XSDs 2025v5.3 + the 47 signature-family
Active rules in the 1040 Business Rules CSV 2025v5.3. Year-watch: the 8878 face is
YEAR-DATED (the Part II jurat embeds "December 31, 2025" verbatim); Pub 1345 reissues
carry the $50/$14 tolerance and the stockpiling clock.

SAFETY GUARD - READY_TO_SEED stayed False until Ken approves the Gate-1 walk.
APPROVED: Ken, 2026-07-15 (s94, "approve WO-33" - approve-all, the four walk seams adopted as
recommended: (a) 8879 Part I line 3 = 1040 line 25d total withholding, not the literal 25a+25b;
(b) the 1040-X arm carries the amended column-C world off the existing 1040-X unit; (c) the e-file
extract REFUSES when a required authorization lacks a signed date (D_8879/8878_UNSIGNED = error);
(d) the tts leg persists a SIGNED-AT Part I snapshot for the $50/$14 re-sign tolerance).
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

READY_TO_SEED = True  # FLIPPED 2026-07-15 - Ken approved Gate-1 in-session (s94, "approve WO-33"; four seams adopted as recommended).

FORM_JURISDICTION = "federal"
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_ENTITY_TYPES = ["1040"]

# -- Verified constants (f8879_8878_source_brief.md) --
PIN_LEN = 5                      # taxpayer + ERO self-selected PIN: five digits, never all zeros
EFIN_LEN = 6                     # Part III = EFIN (6) + ERO PIN (5) = 11 digits
SID_LEN = 20                     # Submission Identification Number
RESIGN_TOL_INCOME = 50           # Pub 1345: > $50 to 'Total income' or 'AGI' -> new signature
RESIGN_TOL_TAX = 14              # Pub 1345: > $14 to total tax / withholding / refund / owed
STOCKPILE_DAYS = 3               # Pub 1345: >3 calendar days holding a ready return = stockpiling
RETENTION_YEARS = 3              # 3 years from due date or IRS received date, whichever later
PIN_METHODS = ("practitioner", "self_select_practitioner")  # Self-Select On-Line = self-filer path, unreachable via an ERO


def _pin_valid(pin) -> bool:
    """Five digits, not all zeros (both faces, both taxpayer boxes and the ERO self-select half)."""
    s = str(pin or "")
    return len(s) == PIN_LEN and s.isdigit() and s != "0" * PIN_LEN


def _ero_efin_pin_valid(efin, pin) -> bool:
    """Part III: six-digit EFIN followed by the five-digit self-selected PIN - 'Don't enter all zeros'."""
    e = str(efin or "")
    return len(e) == EFIN_LEN and e.isdigit() and _pin_valid(pin)


def _f8879_needed(pin_method, ero_enters_any_pin) -> bool:
    """The 8879 4-row chart collapsed: required iff the Practitioner PIN method is used OR the
    ERO is authorized to enter/generate the taxpayer's PIN. The only no-8879 row is
    self-select + taxpayer keys their own PIN. (Pub 1345: PP taxpayers sign EVEN IF they
    enter their own PINs.)"""
    return pin_method == "practitioner" or bool(ero_enters_any_pin)


def _f8879_parts(pin_method, ero_enters_any_pin) -> tuple:
    """Parts by chart row: Part III exists ONLY on the Practitioner-PIN rows."""
    if not _f8879_needed(pin_method, ero_enters_any_pin):
        return ()
    return ("I", "II", "III") if pin_method == "practitioner" else ("I", "II")


def _f8878_needed(extension_form, efw_elected, pin_method, ero_enters_any_pin) -> bool:
    """The 8878 5-row chart collapsed. 4868: EFW AND (PP method OR ERO enters/generates) -
    NO EFW means NO 8878 ever (the s88 R0000-098 print mirror). 2350: ERO enters/generates
    (the PP method is 'Form 4868 Only' on the face, so it never creates a 2350 need)."""
    if extension_form == "4868":
        return bool(efw_elected) and (pin_method == "practitioner" or bool(ero_enters_any_pin))
    if extension_form == "2350":
        return bool(ero_enters_any_pin)
    return False


def _f8878_parts(extension_form, efw_elected, pin_method, ero_enters_any_pin) -> tuple:
    """Part III is 'Practitioner PIN Method for Form 4868 Only' - a 2350 NEVER reaches it."""
    if not _f8878_needed(extension_form, efw_elected, pin_method, ero_enters_any_pin):
        return ()
    if extension_form == "4868" and pin_method == "practitioner":
        return ("I", "II", "III")
    return ("I", "II")


def _resign_required(delta_income_or_agi, delta_tax_family) -> bool:
    """Pub 1345: a NEW declaration/signature only when the post-signing change exceeds $50 to
    'Total income' or 'AGI', or $14 to 'Total tax', 'Federal income tax withheld', 'Refund'
    or 'Amount you owe'. At the tolerance exactly -> no re-sign ('differ by MORE than')."""
    return abs(float(delta_income_or_agi or 0)) > RESIGN_TOL_INCOME or \
        abs(float(delta_tax_family or 0)) > RESIGN_TOL_TAX


def _self_select_barred(primary_under16_never_filed, secondary_under16_no_prior, ssn_duplicate_in_efile_db) -> bool:
    """Self-Select ineligibility (Pub 1345 + IND-674/675/679/680 + IND-664..667): these returns
    take the Practitioner PIN method (or paper) - the ERO path stays open."""
    return bool(primary_under16_never_filed or secondary_under16_no_prior or ssn_duplicate_in_efile_db)


def _stockpiling(days_held_after_ready) -> bool:
    """Pub 1345: waiting more than three calendar days to submit once the ERO has everything."""
    return float(days_held_after_ready or 0) > STOCKPILE_DAYS


def _part1_amounts(agi, total_tax, withholding, refund, owed, is_1040ss=False) -> dict:
    """The 8879 Part I mapping (whole dollars; zeros allowed). 1040: L1=AGI(11), L2=total
    tax(24), L3=federal withholding (WALK SEAM 1: recommend 25d; the face's literal reading
    is 25a+25b), L4=refund(35a), L5=owed(37). 1040-SS filers use LINE 4 ONLY (face note)."""
    if is_1040ss:
        return {"4": int(refund or 0)}
    return {"1": int(agi or 0), "2": int(total_tax or 0), "3": int(withholding or 0),
            "4": int(refund or 0), "5": int(owed or 0)}


AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("efile_signature_1040", "Forms 8879/8878 e-file signature authorizations: the need-gate charts, "
     "PIN mechanics, sign-before-transmit, the $50/$14 re-sign tolerance, retention, and the "
     "Return Header PIN elements they mirror."),
]

EXISTING_SOURCES_TO_REFERENCE: list[str] = []

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_F8879", "source_type": "federal_form", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Form 8879 (Rev. January 2021) - IRS e-file Signature Authorization",
        "citation": "Form 8879 (Rev. 01-2021), Cat. No. 32778X, OMB 1545-0074 (continuous use; self-contained instructions)",
        "issuer": "Internal Revenue Service", "official_url": "https://www.irs.gov/pub/irs-pdf/f8879.pdf",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.5, "topics": ["efile_signature_1040"],
        "excerpts": [{
            "excerpt_label": "Purpose + the when-and-how chart (Rev. 01-2021 verbatim substance)",
            "excerpt_text": (
                "Form 8879 is the declaration document and signature authorization for an e-filed return "
                "filed by an electronic return originator (ERO). Complete Form 8879 when the Practitioner "
                "PIN method is used or when the taxpayer authorizes the ERO to enter or generate the "
                "taxpayer's personal identification number (PIN) on his or her e-filed individual income "
                "tax return. Use this Form 8879 (Rev. January 2021) to authorize e-file of your Form 1040, "
                "1040-SR, 1040-NR, 1040-SS, or 1040-X, for tax years beginning with 2019. CAUTION: Don't "
                "send this form to the IRS. The ERO must retain Form 8879. When and How To Complete: [1] "
                "Not using the Practitioner PIN method and the taxpayer enters his or her own PIN -> Don't "
                "complete Form 8879. [2] Not using the Practitioner PIN method and is authorized to enter "
                "or generate the taxpayer's PIN -> Complete Form 8879, Parts I and II. [3] Using the "
                "Practitioner PIN method and is authorized to enter or generate the taxpayer's PIN -> "
                "Complete Form 8879, Parts I, II, and III. [4] Using the Practitioner PIN method and the "
                "taxpayer enters his or her own PIN -> Complete Form 8879, Parts I, II, and III. Part I "
                "(enter whole dollars only): 1 Adjusted gross income; 2 Total tax; 3 Federal income tax "
                "withheld from Form(s) W-2 and Form(s) 1099; 4 Amount you want refunded to you; 5 Amount "
                "you owe. Note: Form 1040-SS filers use line 4 only. Leave lines 1, 2, 3, and 5 blank. "
                "Taxpayer's PIN: check one box only - Enter five digits, but don't enter all zeros. "
                "Part III Certification and Authentication - Practitioner PIN Method Only: ERO's EFIN/PIN "
                "- enter your six-digit EFIN followed by your five-digit self-selected PIN; don't enter "
                "all zeros."
            ),
            "summary_text": "8879 required iff PP method OR ERO enters/generates the taxpayer PIN (the only skip row = self-select + taxpayer keys own). Part III = PP rows only. Part I = whole-dollar AGI/total tax/withholding/refund/owed; 1040-SS uses line 4 only. Covers 1040/-SR/-NR/-SS/-X original AND amended, TY2019+.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "ERO/taxpayer responsibilities + retention + authentication (Rev. 01-2021 verbatim substance)",
            "excerpt_text": (
                "You must receive the completed and signed Form 8879 from the taxpayer before the "
                "electronic return is transmitted (or released for transmission). Enter the 20-digit "
                "Submission Identification Number (SID) assigned to the tax return, or associate Form "
                "9325, Acknowledgement and General Information for Taxpayers Who File Returns "
                "Electronically, with Form 8879 after filing. If Form 9325 is used to provide the SID, it "
                "isn't required to be physically attached to Form 8879; however, it must be kept in "
                "accordance with published retention requirements for Form 8879. Taxpayers must sign Form "
                "8879 by handwritten signature, or electronic signature if supported by computer software. "
                "Don't send Form 8879 to the IRS unless requested to do so. Retain the completed Form 8879 "
                "for 3 years from the return due date or IRS received date, whichever is later. Form 8879 "
                "may be retained electronically in accordance with the recordkeeping guidelines in Rev. "
                "Proc. 97-22. If you aren't using the Practitioner PIN method, enter the taxpayer(s) date "
                "of birth and either the adjusted gross income or the PIN, or both, from the taxpayer's "
                "prior year ORIGINALLY FILED return in the Authentication Record of the taxpayer's "
                "electronically filed return. Don't use an amount from an amended return or a math error "
                "correction made by the IRS. If married filing jointly, it is acceptable for one spouse to "
                "authorize you to enter his or her PIN, and for the other spouse to enter his or her own "
                "PIN. It isn't acceptable for a taxpayer to select or enter the PIN of an absent spouse. "
                "Provide the taxpayer with a corrected copy of Form 8879 if changes are made to the return "
                "(for example, based on taxpayer review). EROs can sign the form using a rubber stamp, "
                "mechanical device (such as a signature pen), or computer software program (Notice "
                "2007-79)."
            ),
            "summary_text": "Signed 8879 in hand BEFORE transmission; SID (20-digit) after filing or associate Form 9325; retain 3 years from due date or received date (Rev. Proc. 97-22 electronic OK); never send unless requested. Non-PP authentication = DOB + prior-year AGI or PIN from the ORIGINALLY-FILED return. MFJ split-authorization OK; absent-spouse PIN forbidden. Corrected copy on changes. ERO may stamp; the taxpayer never may.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "IRS_F8878", "source_type": "federal_form", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Form 8878 (2025) - IRS e-file Signature Authorization for Form 4868 or Form 2350",
        "citation": "Form 8878 (2025), Cat. No. 32777M, OMB 1545-0074 (Created 4/17/25; YEAR-DATED face)",
        "issuer": "Internal Revenue Service", "official_url": "https://www.irs.gov/pub/irs-pdf/f8878.pdf",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.5, "topics": ["efile_signature_1040"],
        "excerpts": [{
            "excerpt_label": "Purpose + the five-row chart + Part I (2025 verbatim substance)",
            "excerpt_text": (
                "Complete Form 8878 (a) when Form 4868 is filed using the Practitioner PIN method, or (b) "
                "when the taxpayer authorizes the electronic return originator (ERO) to enter or generate "
                "the taxpayer's personal identification number (PIN) on Form 4868 or Form 2350. CAUTION: "
                "Form 8878 isn't an application for an extension of time to file. When and How To "
                "Complete: [1] Form 4868, and authorizing an electronic funds withdrawal, and the taxpayer "
                "is entering their own PIN, and the ERO isn't using the Practitioner PIN method -> Don't "
                "complete Form 8878. [2] Form 4868, and the taxpayer ISN'T authorizing an electronic funds "
                "withdrawal -> Don't complete Form 8878. [3] Form 4868, and authorizing an electronic "
                "funds withdrawal, and authorizing the ERO to enter or generate the taxpayer's PIN, and "
                "the ERO isn't using the Practitioner PIN method -> Complete Form 8878, Parts I and II. "
                "[4] Form 2350, and authorizing the ERO to enter or generate the taxpayer's PIN -> "
                "Complete Form 8878, Parts I and II. [5] Form 4868, and authorizing an electronic funds "
                "withdrawal, and the ERO is using the Practitioner PIN method -> Complete Form 8878, "
                "Parts I, II, and III. Part I - Information From Extension Form (whole dollars only); "
                "check the box and complete the line(s) for the form you authorize your ERO to sign and "
                "file; check only one box. 1 Form 4868: amount you are paying from Form 4868, line 7. "
                "2 Form 2350: 2a I request an extension of time until this date as shown on Form 2350, "
                "line 1; 2b amount you are paying from Form 2350, line 5. Part III Certification and "
                "Authentication - Practitioner PIN Method for FORM 4868 ONLY. Retain 3 years from the "
                "return due date or IRS received date, whichever is later (Rev. Proc. 97-22); don't send "
                "to the IRS unless requested. If the taxpayer is making a payment by electronic funds "
                "withdrawal for Form 4868 and the ERO isn't using the Practitioner PIN method, the ERO "
                "must enter the taxpayer's date of birth and either the adjusted gross income amount or "
                "the PIN, or both, from the taxpayer's originally filed prior year tax return."
            ),
            "summary_text": "8878 gate: 4868 -> EFW AND (PP method OR ERO enters/generates); NO EFW = NO 8878 ever (the s88 R0000-098 print mirror). 2350 -> ERO enters/generates (Parts I+II; Part III is 'Form 4868 Only' - a 2350 never reaches it). Part I = one box only; line 1 ties to 4868 line 7. Same PIN/retention/authentication mechanics as the 8879. YEAR-DATED face - year-watch.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "IRS_P1345_SIG", "source_type": "official_guidance", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Pub. 1345 - Handbook for Authorized IRS e-file Providers (signature chapter)",
        "citation": "Pub. 1345 (current revision, fetched 2026-07-15), 'Signing an Electronic Tax Return' through 'Electronic Signatures for EROs' (pp. 14-18)",
        "issuer": "Internal Revenue Service", "official_url": "https://www.irs.gov/pub/irs-pdf/p1345.pdf",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.5, "topics": ["efile_signature_1040"],
        "excerpts": [{
            "excerpt_label": "The two methods + the always-sign PP rule + the $50/$14 tolerance (verbatim substance)",
            "excerpt_text": (
                "There are two methods of signing individual income tax returns with an electronic "
                "signature: the Self-Select PIN and Practitioner PIN methods. The Self-Select PIN method "
                "requires taxpayers to provide their prior year Adjusted Gross Income (AGI) amount or "
                "prior year PIN for use by the IRS to authenticate the taxpayers. The Practitioner PIN "
                "method does not require the taxpayer to provide their prior year AGI amount or prior year "
                "PIN; instead, taxpayers must ALWAYS sign a completed signature authorization form. "
                "Taxpayers who use the Practitioner PIN method must sign the signature authorization form "
                "even if they enter their own PINs in the electronic return record using keystrokes. "
                "Anytime an ERO enters the taxpayer's PIN on the electronic return, the ERO must, prior to "
                "submission of the return, complete an IRS e-file Signature Authorization form which must "
                "be signed by the taxpayer. Note: Form 8878 is only needed for Forms 4868 when taxpayers "
                "are authorizing an electronic funds withdrawal and want an ERO to enter their PINs. "
                "Taxpayers must sign a new declaration if the electronic return data on individual income "
                "tax returns is changed after taxpayers signed the Declaration of Taxpayer and the amounts "
                "differ by more than either (i) $50 to 'Total income' or 'AGI,' or (ii) $14 to 'Total "
                "tax,' 'Federal income tax withheld,' 'Refund' or 'Amount you owe.' The following "
                "taxpayers are ineligible to sign with an electronic signature using the Self-Select PIN: "
                "primary taxpayers under age sixteen who have never filed; and secondary taxpayers under "
                "age sixteen who didn't file the prior tax year. The ERO must keep Forms 8878 and 8879 for "
                "three years from the return due date or the IRS received date, whichever is later; EROs "
                "must not send Forms 8878 and 8879 to the IRS unless the IRS requests they do so. An ERO "
                "must originate the electronic submission of a return as soon as possible; stockpiling "
                "refers to waiting more than three calendar days to submit the return to the IRS once the "
                "ERO has all necessary information for origination."
            ),
            "summary_text": "PP method = taxpayer ALWAYS signs the authorization (even keying their own PIN); ERO-entered PIN = authorization always. Re-sign tolerance: >$50 Total income/AGI or >$14 tax/withholding/refund/owed. Under-16 self-select bars. 3-year retention. 3-day stockpiling clock.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "Electronic-signature (e-sign) requirements for the 8878/8879 (verbatim substance)",
            "excerpt_text": (
                "Taxpayers have the choice of using electronic signatures for Forms 8878 and 8879 if the "
                "software provides the capability. The software must record: digital image of the signed "
                "form; date and time of the signature; taxpayer's computer IP address (remote transaction "
                "only); taxpayer's login identification (remote only); identity verification (KBA passed "
                "results; for in-person, government photo ID confirmed); and the method used to sign. "
                "Identity verification must accord with NIST SP 800-63 Level 2 assurance and "
                "knowledge-based authentication or higher. If the taxpayer fails the knowledge-based "
                "authentication questions after three attempts, the ERO must obtain a HANDWRITTEN "
                "signature. An electronic signature via remote transaction does NOT include handwritten "
                "signatures on Forms 8878 or 8879 sent to the ERO by hand delivery, U.S. mail, private "
                "delivery service, fax, email or an Internet website. EROs may sign Form 8878 and Form "
                "8879 by rubber stamp, mechanical device, or computer software program (Notice 2007-79); "
                "this does not alter the requirement that taxpayers must sign by handwritten or "
                "electronic signature."
            ),
            "summary_text": "E-signing the pair needs: image + timestamp + (remote: IP/login) + KBA identity verification (NIST 800-63 L2); 3 KBA failures -> handwritten required. Mailed/faxed/emailed handwritten forms are NOT e-signatures (no KBA needed). Recorded as FACTS - the office practice is in-person/handwritten; portal future.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "MEF_1040_SIG", "source_type": "official_guidance", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "MeF 1040 signature family - header XSDs + business rules (TY2025v5.3)",
        "citation": "efileTypes.xsd + ReturnHeader1040x.xsd 2025v5.3; 1040 Business Rules CSV 2025v5.3 (47 signature-family Active rules)",
        "issuer": "Internal Revenue Service (MeF)", "official_url": "https://www.irs.gov/e-file-providers/modernized-e-file-mef-schemas-and-business-rules",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.5, "topics": ["efile_signature_1040"],
        "excerpts": [{
            "excerpt_label": "The header elements + the rule set the printed pair mirrors (2025v5.3)",
            "excerpt_text": (
                "PINCodeType enumerates 'Practitioner', 'Self-Select Practitioner', 'Self-Select On-Line'. "
                "PINEnteredByType enumerates 'Taxpayer', 'ERO'. IND-672: if PINTypeCd is 'Practitioner' or "
                "'Self-Select Practitioner', PractitionerPINGrp (EFIN + PIN) must have a value; IND-673: "
                "with 'Self-Select On-Line' it must NOT (the self-filer path - unreachable via an ERO). "
                "IND-025/026 (+027/028 spouse): the Self-Select types with a birth date require "
                "PriorYearAGIAmt or PriorYearPIN or an IP PIN; IND-031/032: the prior-year value must "
                "match the e-File database. IND-056/057: a signature PIN requires PINEnteredByCd; "
                "IND-058/059: a signature PIN requires a signature DATE. IND-418: MFJ requires "
                "SpousePINEnteredByCd; IND-433: non-MFJ requires PrimarySignaturePIN; IND-054/F1040-405: "
                "MFS/HoH must not carry a spouse PIN. F1040-310 through F1040-318: MFJ requires both "
                "signature PINs with death/combat-zone/special-condition carve-outs. IND-664..667: an SSN "
                "appearing more than once in the e-File database bars both Self-Select types. "
                "IND-674/675/679/680: primary under 16 never-filed / spouse under 16 no-prior-year bar "
                "both Self-Select types. JuratDisclosureCd is REQUIRED in the header - the Part II "
                "declaration text on the 8879 face IS the jurat the code names."
            ),
            "summary_text": "The printed pair mirrors the header signature block tts already transmits: PINTypeCd + PINEnteredByCd decide the chart row; PractitionerPINGrp = Part III; SelfSelectPINGrp prior-year authentication = the non-PP Authentication Record; signature dates required per PIN (IND-058/059). No IRS8879/IRS8878 document exists anywhere in ReturnData - print-only BY DESIGN.",
            "is_key_excerpt": True,
        }],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_F8879", "8879", "governs"), ("IRS_F8878", "8878", "governs"),
    ("IRS_P1345_SIG", "8879", "governs"), ("IRS_P1345_SIG", "8878", "governs"),
    ("MEF_1040_SIG", "8879", "supports"), ("MEF_1040_SIG", "8878", "supports"),
]


# -- Form 8879 --
F79_FACTS: list[dict] = [
    {"fact_key": "pin_method", "label": "Signature method: 'practitioner' (house default) or 'self_select_practitioner' (Self-Select On-Line = self-filer, unreachable via an ERO)", "data_type": "string", "required": False, "sort_order": 1},
    {"fact_key": "primary_pin_entered_by", "label": "Who enters the primary taxpayer's PIN: 'taxpayer' or 'ero' (the chart-row selector; header PINEnteredByCd)", "data_type": "string", "required": False, "sort_order": 2},
    {"fact_key": "spouse_pin_entered_by", "label": "Who enters the spouse's PIN (MFJ; split authorization is allowed - absent-spouse entry is NOT)", "data_type": "string", "required": False, "sort_order": 3},
    {"fact_key": "primary_pin", "label": "Primary taxpayer 5-digit PIN (never all zeros)", "data_type": "string", "required": False, "sort_order": 4},
    {"fact_key": "spouse_pin", "label": "Spouse 5-digit PIN (never all zeros; MFJ)", "data_type": "string", "required": False, "sort_order": 5},
    {"fact_key": "ero_efin", "label": "ERO six-digit EFIN (Part III first half; from the Preparer record)", "data_type": "string", "required": False, "sort_order": 6},
    {"fact_key": "ero_self_selected_pin", "label": "ERO five-digit self-selected PIN (Part III second half; keep the same PIN all season per Pub 1345)", "data_type": "string", "required": False, "sort_order": 7},
    {"fact_key": "primary_signed_date", "label": "Date the primary taxpayer signed the 8879 (transmit gate: must exist BEFORE origination)", "data_type": "date", "required": False, "sort_order": 8},
    {"fact_key": "spouse_signed_date", "label": "Date the spouse signed (MFJ)", "data_type": "date", "required": False, "sort_order": 9},
    {"fact_key": "ero_signed_date", "label": "Date the ERO signed Part III (PP method; stamp/device/software OK per Notice 2007-79)", "data_type": "date", "required": False, "sort_order": 10},
    {"fact_key": "authorizing_return", "label": "What is being authorized: '1040' (original) or '1040X' (amended - Part I carries the column-C world; walk seam 2)", "data_type": "string", "required": False, "sort_order": 11},
    {"fact_key": "signed_agi", "label": "Part I line 1 snapshot at signing - AGI (1040 line 11; whole dollars)", "data_type": "decimal", "required": False, "sort_order": 12},
    {"fact_key": "signed_total_tax", "label": "Part I line 2 snapshot - total tax (1040 line 24)", "data_type": "decimal", "required": False, "sort_order": 13},
    {"fact_key": "signed_withholding", "label": "Part I line 3 snapshot - federal withholding (recommend 1040 line 25d; the literal face reading is 25a+25b - walk seam 1)", "data_type": "decimal", "required": False, "sort_order": 14},
    {"fact_key": "signed_refund", "label": "Part I line 4 snapshot - refund (1040 line 35a)", "data_type": "decimal", "required": False, "sort_order": 15},
    {"fact_key": "signed_owed", "label": "Part I line 5 snapshot - amount owed (1040 line 37)", "data_type": "decimal", "required": False, "sort_order": 16},
    {"fact_key": "sid", "label": "20-digit Submission Identification Number - entered AFTER filing (or associate Form 9325 with the retained form)", "data_type": "string", "required": False, "sort_order": 17},
    {"fact_key": "prior_year_agi", "label": "Prior-year AGI from the ORIGINALLY FILED return (non-PP authentication; never amended/math-error amounts)", "data_type": "decimal", "required": False, "sort_order": 18},
    {"fact_key": "prior_year_pin", "label": "Prior-year 5-digit PIN (non-PP authentication alternative)", "data_type": "string", "required": False, "sort_order": 19},
    {"fact_key": "primary_under16_never_filed", "label": "Self-select bar: primary under 16 who has never filed (IND-674/675)", "data_type": "boolean", "required": False, "sort_order": 20},
    {"fact_key": "secondary_under16_no_prior", "label": "Self-select bar: spouse under 16 who didn't file the prior year (IND-679/680)", "data_type": "boolean", "required": False, "sort_order": 21},
    {"fact_key": "ssn_duplicate_in_efile_db", "label": "Self-select bar: SSN appears more than once in the e-File database (IND-664..667; PP still flies)", "data_type": "boolean", "required": False, "sort_order": 22},
]

F79_RULES: list[dict] = [
    {"rule_id": "R-8879-NEED", "title": "The 8879 need-gate (the 4-row chart collapsed)", "rule_type": "routing",
     "formula": "needed iff pin_method == 'practitioner' OR any taxpayer PIN is entered/generated by the ERO. The ONLY skip row: self-select method + taxpayer keys their own PIN. Pub 1345: PP taxpayers must sign EVEN IF they enter their own PINs",
     "inputs": ["pin_method", "primary_pin_entered_by", "spouse_pin_entered_by"], "outputs": ["f8879_needed"], "sort_order": 1,
     "description": "W1. The house default is the Practitioner PIN method (tts header pin_type_cd) - in practice every e-filed 1040 prints an 8879."},
    {"rule_id": "R-8879-PARTS", "title": "Parts by chart row (Part III = Practitioner rows only)", "rule_type": "routing",
     "formula": "needed + PP method -> Parts I, II, III (ERO EFIN/PIN certification). needed + self-select-practitioner (ERO entered) -> Parts I and II only",
     "inputs": ["pin_method", "primary_pin_entered_by", "spouse_pin_entered_by"], "outputs": ["f8879_parts"], "sort_order": 2,
     "description": "W1. Part III's jurat cites Pub 1345 and the Practitioner PIN method by name."},
    {"rule_id": "R-8879-AMTS", "title": "Part I amounts off the return face (whole dollars; zeros allowed)", "rule_type": "calculation",
     "formula": "1040: L1 = AGI (1040 line 11); L2 = total tax (line 24); L3 = federal withholding - RECOMMEND line 25d, the literal face reading is 25a+25b (walk seam 1); L4 = refund (line 35a); L5 = amount owed (line 37). 1040-SS filers: LINE 4 ONLY (lines 1-3, 5 blank - face note; app boundary). 1040-X: the column-C world (AGI 1C, total tax 11C, refund 22, owed 20 - walk seam 2)",
     "inputs": ["authorizing_return", "signed_agi", "signed_total_tax", "signed_withholding", "signed_refund", "signed_owed"], "outputs": ["part1_amounts"], "sort_order": 3,
     "description": "W1. The ERO completes Part I from the return; the taxpayer's declaration swears the Part I amounts ARE the return's amounts."},
    {"rule_id": "R-8879-PINS", "title": "PIN hygiene + MFJ split authorization + the absent-spouse bar", "rule_type": "validation",
     "formula": "taxpayer PINs: exactly five digits, never all zeros. Part III: six-digit EFIN + five-digit self-selected non-zero ERO PIN (11 digits). MFJ: one spouse may authorize the ERO while the other self-enters (split OK); selecting/entering the PIN of an ABSENT spouse is forbidden. Header ties: IND-056/057 (PIN -> PINEnteredByCd), IND-418 (MFJ SpousePINEnteredByCd), IND-054/F1040-405 (MFS/HoH: no spouse PIN), F1040-310..318 (MFJ both PINs w/ death/combat-zone carve-outs)",
     "inputs": ["primary_pin", "spouse_pin", "ero_efin", "ero_self_selected_pin"], "outputs": ["pins_valid"], "sort_order": 4,
     "description": "W2. The five-digit/non-zero text appears verbatim next to every PIN box on the face."},
    {"rule_id": "R-8879-TIMING", "title": "Sign BEFORE transmit; SID after filing; the 3-day stockpiling clock", "rule_type": "validation",
     "formula": "the ERO must RECEIVE the completed, signed 8879 before the return is transmitted or released for transmission (the ERO may key PINs into the record earlier, but origination waits). After filing: enter the 20-digit SID on the retained form OR associate Form 9325 (not physically attached; inherits 8879 retention). Pub 1345: originate as soon as possible - holding a ready return more than 3 calendar days = stockpiling",
     "inputs": ["primary_signed_date", "spouse_signed_date", "sid"], "outputs": ["transmit_gate"], "sort_order": 5,
     "description": "W2. Walk seam 3: recommend the tts extract refuses when the required authorization lacks a signed date; revisit at S-17g transmit."},
    {"rule_id": "R-8879-RESIGN", "title": "Corrected copy + the Pub-1345 $50/$14 re-sign tolerance", "rule_type": "validation",
     "formula": "provide a corrected 8879 when the return changes after signing. A NEW signature is required only when the post-signing change exceeds $50 to Total income or AGI, OR $14 to total tax / federal withholding / refund / amount owed ('differ by MORE than' - at the tolerance exactly, no re-sign). Requires the signed-at Part I snapshot to compare against the live recompute (walk seam 4)",
     "inputs": ["signed_agi", "signed_total_tax", "signed_withholding", "signed_refund", "signed_owed"], "outputs": ["resign_required"], "sort_order": 6,
     "description": "W2. The tolerance lives in Pub 1345, not on the face - year-watch the handbook."},
    {"rule_id": "R-8879-AUTH", "title": "Non-PP authentication + the self-select bars", "rule_type": "validation",
     "formula": "self-select-practitioner ONLY: the Authentication Record needs taxpayer DOB + prior-year AGI or prior-year PIN (or both) from the ORIGINALLY FILED prior-year return - never an amended amount, never an IRS math-error correction (IND-025/026 accept an IP PIN as the third alternative; IND-031/032 match the e-File database). Barred from self-select entirely (PP or paper instead): primary under 16 never filed; spouse under 16 no prior-year filing; SSN appearing more than once in the e-File database (IND-664..667, IND-674..680). PP method requires NONE of this",
     "inputs": ["pin_method", "prior_year_agi", "prior_year_pin", "primary_under16_never_filed", "secondary_under16_no_prior", "ssn_duplicate_in_efile_db"], "outputs": ["auth_ok", "self_select_barred"], "sort_order": 7,
     "description": "W2. The PP method's whole selling point: no prior-year authentication, at the price of an always-printed 8879."},
    {"rule_id": "R-8879-RETAIN", "title": "3-year ERO retention; never sent to the IRS", "rule_type": "validation",
     "formula": "retain the completed 8879 for 3 years from the return due date or the IRS received date, whichever is later; electronic retention OK per Rev. Proc. 97-22; do NOT send to the IRS unless requested. The taxpayer signs handwritten or electronic (e-sign needs the Pub-1345 KBA framework - recorded as facts, portal future); the ERO may sign by rubber stamp / mechanical device / software (Notice 2007-79)",
     "inputs": ["primary_signed_date"], "outputs": ["retention_end"], "sort_order": 8,
     "description": "W2/W4. Print-only BY DESIGN - no IRS8879 document exists anywhere in ReturnData; the header PIN block is the transmitted signature."},
]

F79_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-8879-NEED", "IRS_F8879", "primary", "Purpose of Form + the When-and-How chart"),
    ("R-8879-NEED", "IRS_P1345_SIG", "supporting", "PP taxpayers always sign; ERO-entered PIN -> authorization required"),
    ("R-8879-PARTS", "IRS_F8879", "primary", "The chart's Parts column + Part III title"),
    ("R-8879-AMTS", "IRS_F8879", "primary", "Part I + the 1040-SS line-4-only note + ERO responsibility 2"),
    ("R-8879-PINS", "IRS_F8879", "primary", "PIN boxes + Part III EFIN/PIN + the absent-spouse note"),
    ("R-8879-PINS", "MEF_1040_SIG", "supporting", "IND-056/057/418/054, F1040-310..318, F1040-405"),
    ("R-8879-TIMING", "IRS_F8879", "primary", "The receive-before-transmit caution + SID/9325 note"),
    ("R-8879-TIMING", "IRS_P1345_SIG", "supporting", "Originate ASAP + the 3-day stockpiling definition"),
    ("R-8879-RESIGN", "IRS_P1345_SIG", "primary", "The $50/$14 new-declaration tolerance"),
    ("R-8879-RESIGN", "IRS_F8879", "supporting", "Provide a corrected copy on changes"),
    ("R-8879-AUTH", "IRS_F8879", "primary", "The Authentication Record paragraph (originally-filed amounts)"),
    ("R-8879-AUTH", "MEF_1040_SIG", "supporting", "IND-025..032, IND-664..667, IND-674..680"),
    ("R-8879-RETAIN", "IRS_F8879", "primary", "Important Notes for EROs: 3-year retention + Rev. Proc. 97-22"),
    ("R-8879-RETAIN", "IRS_P1345_SIG", "supporting", "E-signature framework + Notice 2007-79 ERO stamps"),
]

F79_LINES: list[dict] = [
    {"line_number": "SID", "description": "Submission Identification Number (20-digit; post-filing, or associate Form 9325)", "line_type": "input", "source_facts": ["sid"], "sort_order": 1},
    {"line_number": "1", "description": "Part I line 1 - Adjusted gross income (1040 line 11; whole dollars)", "line_type": "calculated", "source_rules": ["R-8879-AMTS"], "sort_order": 2},
    {"line_number": "2", "description": "Part I line 2 - Total tax (1040 line 24)", "line_type": "calculated", "source_rules": ["R-8879-AMTS"], "sort_order": 3},
    {"line_number": "3", "description": "Part I line 3 - Federal income tax withheld from Form(s) W-2 and Form(s) 1099 (mapping = walk seam 1)", "line_type": "calculated", "source_rules": ["R-8879-AMTS"], "sort_order": 4},
    {"line_number": "4", "description": "Part I line 4 - Amount you want refunded to you (1040 line 35a; the ONLY line a 1040-SS filer uses)", "line_type": "calculated", "source_rules": ["R-8879-AMTS"], "sort_order": 5},
    {"line_number": "5", "description": "Part I line 5 - Amount you owe (1040 line 37)", "line_type": "calculated", "source_rules": ["R-8879-AMTS"], "sort_order": 6},
    {"line_number": "TP_AUTH_BOX", "description": "Part II taxpayer PIN choice - 'I authorize [ERO firm name] to enter or generate my PIN' vs 'I will enter my PIN' (check ONE)", "line_type": "input", "source_facts": ["primary_pin_entered_by"], "sort_order": 7},
    {"line_number": "TP_PIN", "description": "Part II taxpayer 5-digit PIN (never all zeros)", "line_type": "input", "source_facts": ["primary_pin"], "source_rules": ["R-8879-PINS"], "sort_order": 8},
    {"line_number": "TP_SIGN_DT", "description": "Taxpayer signature + date (handwritten or qualifying electronic; BEFORE transmission)", "line_type": "input", "source_facts": ["primary_signed_date"], "source_rules": ["R-8879-TIMING"], "sort_order": 9},
    {"line_number": "SP_AUTH_BOX", "description": "Part II spouse PIN choice (MFJ; split authorization allowed)", "line_type": "input", "source_facts": ["spouse_pin_entered_by"], "sort_order": 10},
    {"line_number": "SP_PIN", "description": "Part II spouse 5-digit PIN (never all zeros)", "line_type": "input", "source_facts": ["spouse_pin"], "source_rules": ["R-8879-PINS"], "sort_order": 11},
    {"line_number": "SP_SIGN_DT", "description": "Spouse signature + date (MFJ)", "line_type": "input", "source_facts": ["spouse_signed_date"], "source_rules": ["R-8879-TIMING"], "sort_order": 12},
    {"line_number": "ERO_EFINPIN", "description": "Part III - ERO's EFIN/PIN (six-digit EFIN + five-digit self-selected PIN; PP method only)", "line_type": "calculated", "source_facts": ["ero_efin", "ero_self_selected_pin"], "source_rules": ["R-8879-PARTS", "R-8879-PINS"], "sort_order": 13},
    {"line_number": "ERO_SIGN_DT", "description": "Part III - ERO signature + date (stamp/device/software OK, Notice 2007-79)", "line_type": "input", "source_facts": ["ero_signed_date"], "sort_order": 14},
    {"line_number": "CALC_NEED", "description": "Computed need-gate (the 4-row chart; the self-select+own-PIN row is the only skip)", "line_type": "calculated", "source_rules": ["R-8879-NEED"], "sort_order": 15},
    {"line_number": "CALC_RESIGN", "description": "Computed re-sign flag (live return vs the signed-at Part I snapshot; the $50/$14 tolerance)", "line_type": "calculated", "source_rules": ["R-8879-RESIGN"], "sort_order": 16},
]

F79_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_8879_NEED", "title": "Form 8879 required for this e-filed return", "severity": "warning",
     "condition": "e-filing with the Practitioner PIN method, or the ERO enters/generates any taxpayer PIN",
     "message": "This return needs a Form 8879: the Practitioner PIN method (the house default) always requires one, and any ERO-entered or ERO-generated taxpayer PIN requires one under either method. Print it, obtain the taxpayer signature(s), and retain it - it is never mailed to the IRS.", "notes": "W1."},
    {"diagnostic_id": "D_8879_UNSIGNED", "title": "8879 not signed - transmission is blocked", "severity": "error",
     "condition": "f8879_needed and a required signed date is missing at extract/transmit",
     "message": "The ERO must RECEIVE the completed, signed Form 8879 before the return is transmitted or released for transmission (Form 8879 caution; Pub 1345). Record the taxpayer (and spouse, if MFJ) signature date(s) before building the e-file submission.", "notes": "W2. Walk seam 3: the extract refuses on this - revisit at S-17g."},
    {"diagnostic_id": "D_8879_PINZERO", "title": "PIN must be five digits, not all zeros", "severity": "error",
     "condition": "any PIN fails the 5-digit/non-zero test (taxpayer, spouse, or ERO self-selected)",
     "message": "Every PIN on Form 8879 must be exactly five digits and must not be all zeros - the taxpayer PIN boxes, the spouse PIN boxes, and the five-digit half of the ERO's Part III EFIN/PIN all carry the same rule on the face.", "notes": "W2."},
    {"diagnostic_id": "D_8879_AUTHGAP", "title": "Self-select method: prior-year authentication missing", "severity": "error",
     "condition": "pin_method = self_select_practitioner and neither prior-year AGI nor prior-year PIN (nor an IP PIN) is on the return",
     "message": "The Self-Select PIN method authenticates the taxpayer with date of birth plus prior-year AGI or prior-year PIN (or both) from the ORIGINALLY FILED prior-year return - never an amended amount or an IRS math-error correction (an IP PIN also satisfies IND-025/026). Supply it, or switch to the Practitioner PIN method, which needs none of this.", "notes": "W2. IND-025..032."},
    {"diagnostic_id": "D_8879_SSBAR", "title": "Self-select method barred for this taxpayer", "severity": "error",
     "condition": "primary under 16 never filed, spouse under 16 with no prior-year filing, or an SSN appearing more than once in the e-File database",
     "message": "This return cannot use the Self-Select PIN method: primary taxpayers under 16 who have never filed, secondary taxpayers under 16 who didn't file last year, and SSNs appearing more than once in the e-File database are all barred (IND-664..667, IND-674..680). Use the Practitioner PIN method.", "notes": "W2."},
    {"diagnostic_id": "D_8879_RESIGN", "title": "Return changed after signing - a new 8879 is required", "severity": "error",
     "condition": "post-signing change > $50 to Total income/AGI or > $14 to total tax/withholding/refund/owed",
     "message": "The return data changed after the taxpayer signed, beyond the Pub. 1345 tolerance (more than $50 of Total income or AGI, or more than $14 of total tax, federal withholding, refund, or amount owed). Print a corrected Form 8879 and obtain a NEW signature before transmitting. Changes inside the tolerance need only a corrected copy on request.", "notes": "W2. Walk seam 4: compares the live return against the signed-at snapshot."},
    {"diagnostic_id": "D_8879_STOCKPILE", "title": "Signed return held more than 3 calendar days", "severity": "warning",
     "condition": "signed authorization in hand + all origination info complete for more than 3 calendar days without transmission",
     "message": "Pub. 1345 requires the ERO to originate the electronic submission as soon as possible - waiting more than three calendar days once everything needed for origination is in hand is stockpiling. Transmit the return.", "notes": "W2."},
    {"diagnostic_id": "D_8879_SID", "title": "Post-filing: record the SID (or associate Form 9325)", "severity": "info",
     "condition": "return accepted and the retained 8879 carries no SID",
     "message": "After filing, enter the 20-digit Submission Identification Number on the retained Form 8879, or associate Form 9325 with it (9325 need not be physically attached but inherits the 8879's retention requirements).", "notes": "W2. Form 9325 itself = the S-22b triage item."},
    {"diagnostic_id": "D_8879_RETAIN", "title": "Retention: 3 years, never mailed to the IRS", "severity": "info",
     "condition": "informational on print",
     "message": "Retain the completed Form 8879 for 3 years from the return due date or the IRS received date, whichever is later (electronic retention OK per Rev. Proc. 97-22). Don't send it to the IRS unless requested. Provide the taxpayer a copy on request.", "notes": "W2/W4."},
]

F79_SCENARIOS: list[dict] = [
    {"scenario_name": "8879-A - Practitioner PIN, MFJ, ERO enters both PINs: Parts I, II, III", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"pin_method": "practitioner", "primary_pin_entered_by": "ero", "spouse_pin_entered_by": "ero",
                "primary_pin": "12345", "spouse_pin": "54321", "ero_efin": "612345", "ero_self_selected_pin": "98765"},
     "expected_outputs": {"f8879_needed": True, "f8879_parts": ["I", "II", "III"]},
     "notes": "The house case: the PP method always prints an 8879 with Part III (chart row 3)."},
    {"scenario_name": "8879-B - self-select + taxpayer keys own PIN: the ONLY no-8879 row", "scenario_type": "edge", "sort_order": 2,
     "inputs": {"pin_method": "self_select_practitioner", "primary_pin_entered_by": "taxpayer", "spouse_pin_entered_by": ""},
     "expected_outputs": {"f8879_needed": False},
     "notes": "Chart row 1: not using the PP method and the taxpayer enters their own PIN -> don't complete Form 8879."},
    {"scenario_name": "8879-C - self-select + ERO enters the PIN: Parts I and II only", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"pin_method": "self_select_practitioner", "primary_pin_entered_by": "ero"},
     "expected_outputs": {"f8879_needed": True, "f8879_parts": ["I", "II"]},
     "notes": "Chart row 2 - no Part III outside the PP method; the return still needs the prior-year authentication (D_8879_AUTHGAP watches)."},
    {"scenario_name": "8879-D - PP method + taxpayer keys own PIN: STILL Parts I, II, III", "scenario_type": "edge", "sort_order": 4,
     "inputs": {"pin_method": "practitioner", "primary_pin_entered_by": "taxpayer"},
     "expected_outputs": {"f8879_needed": True, "f8879_parts": ["I", "II", "III"]},
     "notes": "Chart row 4 + Pub 1345 verbatim: PP taxpayers must sign the authorization even entering their own PINs - the counter-intuitive row."},
    {"scenario_name": "8879-E - Part I amounts (refund return; whole dollars)", "scenario_type": "normal", "sort_order": 5,
     "inputs": {"authorizing_return": "1040", "signed_agi": 88450, "signed_total_tax": 9200,
                "signed_withholding": 11650, "signed_refund": 2450, "signed_owed": 0},
     "expected_outputs": {"part1_amounts": {"1": 88450, "2": 9200, "3": 11650, "4": 2450, "5": 0}},
     "notes": "L1-L3 explain L4/L5 (zeros may be entered when appropriate - face). The L3 source mapping is walk seam 1 (recommend 1040 line 25d)."},
    {"scenario_name": "8879-F - the $50/$14 re-sign tolerance, both directions", "scenario_type": "edge", "sort_order": 6,
     "inputs": {"delta_agi_case1": 50, "delta_tax_case1": 14, "delta_agi_case2": 51, "delta_tax_case3": 15},
     "expected_outputs": {"case1_resign": False, "case2_resign": True, "case3_resign": True},
     "notes": "Pub 1345 'differ by MORE than': exactly $50 AGI / $14 tax -> no re-sign; $51 AGI -> re-sign; $15 refund-family -> re-sign."},
    {"scenario_name": "8879-G - all-zero PIN refused", "scenario_type": "failure", "sort_order": 7,
     "inputs": {"primary_pin": "00000"},
     "expected_outputs": {"pins_valid": False, "diagnostic": "D_8879_PINZERO"},
     "notes": "'Enter five digits, but don't enter all zeros' - printed at every PIN box on the face, including the ERO's Part III half."},
    {"scenario_name": "8879-H - primary under 16, never filed: self-select barred", "scenario_type": "failure", "sort_order": 8,
     "inputs": {"pin_method": "self_select_practitioner", "primary_under16_never_filed": True},
     "expected_outputs": {"self_select_barred": True, "diagnostic": "D_8879_SSBAR"},
     "notes": "Pub 1345 + IND-674/675: the return takes the Practitioner PIN method (which conveniently always prints an 8879) or paper."},
]

# -- Form 8878 --
F78_FACTS: list[dict] = [
    {"fact_key": "extension_form", "label": "Which application is authorized: '4868' (the tts s88 unit) or '2350' (APP BOUNDARY - no 2350 module)", "data_type": "string", "required": False, "sort_order": 1},
    {"fact_key": "efw_elected", "label": "4868 EFW election (the s88 extension EFW) - WITHOUT it a 4868 NEVER needs an 8878 (chart row 2)", "data_type": "boolean", "required": False, "sort_order": 2},
    {"fact_key": "pin_method", "label": "Signature method ('practitioner' / 'self_select_practitioner'); the PP method is 'Form 4868 Only' on the 8878 face", "data_type": "string", "required": False, "sort_order": 3},
    {"fact_key": "primary_pin_entered_by", "label": "Who enters the primary PIN: 'taxpayer' or 'ero' (the chart-row selector)", "data_type": "string", "required": False, "sort_order": 4},
    {"fact_key": "spouse_pin_entered_by", "label": "Who enters the spouse PIN (MFJ; split authorization allowed, absent-spouse entry forbidden)", "data_type": "string", "required": False, "sort_order": 5},
    {"fact_key": "primary_pin", "label": "Primary taxpayer 5-digit PIN (never all zeros)", "data_type": "string", "required": False, "sort_order": 6},
    {"fact_key": "spouse_pin", "label": "Spouse 5-digit PIN (never all zeros)", "data_type": "string", "required": False, "sort_order": 7},
    {"fact_key": "amount_paying_l7", "label": "Part I line 1 - amount paying from Form 4868, LINE 7 (the tie to the s88 unit's face)", "data_type": "decimal", "required": False, "sort_order": 8},
    {"fact_key": "ero_efin", "label": "ERO six-digit EFIN (Part III; 4868 + PP method only)", "data_type": "string", "required": False, "sort_order": 9},
    {"fact_key": "ero_self_selected_pin", "label": "ERO five-digit self-selected PIN (Part III second half)", "data_type": "string", "required": False, "sort_order": 10},
    {"fact_key": "primary_signed_date", "label": "Date the primary taxpayer signed the 8878 (must exist BEFORE the extension transmits)", "data_type": "date", "required": False, "sort_order": 11},
    {"fact_key": "spouse_signed_date", "label": "Date the spouse signed (MFJ)", "data_type": "date", "required": False, "sort_order": 12},
    {"fact_key": "ero_signed_date", "label": "Date the ERO signed Part III (4868 + PP only)", "data_type": "date", "required": False, "sort_order": 13},
    {"fact_key": "sid", "label": "20-digit SID assigned to the EXTENSION - post-filing (or associate Form 9325)", "data_type": "string", "required": False, "sort_order": 14},
]

F78_RULES: list[dict] = [
    {"rule_id": "R-8878-NEED", "title": "The 8878 need-gate (the 5-row chart collapsed)", "rule_type": "routing",
     "formula": "4868: needed iff EFW elected AND (PP method OR the ERO enters/generates a taxpayer PIN). NO EFW -> NO 8878, ever (chart row 2 - the print mirror of R0000-098: a no-payment e-filed 4868 carries no signature at all, the tts s88 unit). 2350: needed iff the ERO enters/generates the PIN (the PP method is 'Form 4868 Only' and never creates a 2350 need)",
     "inputs": ["extension_form", "efw_elected", "pin_method", "primary_pin_entered_by", "spouse_pin_entered_by"], "outputs": ["f8878_needed"], "sort_order": 1,
     "description": "W3. The EFW election (the s88 extension EFW input) is the live trigger; the 2350 arm is a stated app boundary."},
    {"rule_id": "R-8878-PARTS", "title": "Parts by chart row - Part III is 'Form 4868 Only'", "rule_type": "routing",
     "formula": "needed + 4868 + PP method -> Parts I, II, III. needed otherwise (4868 non-PP ERO-entered, or 2350 ERO-entered) -> Parts I and II. A 2350 NEVER reaches Part III (both the continue-below banner and the Part III title say 'Practitioner PIN Method for Form 4868 Only')",
     "inputs": ["extension_form", "pin_method"], "outputs": ["f8878_parts"], "sort_order": 2,
     "description": "W3. Face verbatim, twice."},
    {"rule_id": "R-8878-AMT", "title": "Part I: check ONE box; line 1 ties to 4868 line 7", "rule_type": "calculation",
     "formula": "check the box for the ONE form being authorized (never both). Line 1 (4868): amount you are paying from Form 4868, LINE 7 - the same line the s88 4868 unit derives (components 25d+26+27..31 - L10, never line 33). Line 2 (2350): 2a = the extension-until date (2350 line 1), 2b = amount paying (2350 line 5) - app boundary. Whole dollars only. The 8878 is NOT itself an extension application (face caution): the 4868/2350 must still be filed",
     "inputs": ["extension_form", "amount_paying_l7"], "outputs": ["part1"], "sort_order": 3,
     "description": "W3. The one-box rule is the face's own bold instruction."},
    {"rule_id": "R-8878-MECH", "title": "Shared mechanics - identical to the 8879, verbatim", "rule_type": "validation",
     "formula": "5-digit non-zero PINs; EFIN(6)+PIN(5) Part III; sign BEFORE the extension transmits (or is released); SID after filing or associate Form 9325; retain 3 years from the return due date or IRS received date whichever is later (Rev. Proc. 97-22); never send unless requested; MFJ split authorization OK / absent-spouse PIN forbidden; corrected copy if the extension form changes; taxpayer signs handwritten-or-electronic, ERO may stamp (Notice 2007-79); non-PP + EFW: DOB + prior-year AGI or PIN from the ORIGINALLY FILED prior-year return",
     "inputs": ["primary_pin", "spouse_pin", "ero_efin", "ero_self_selected_pin", "primary_signed_date", "sid"], "outputs": ["mech_ok"], "sort_order": 4,
     "description": "W3. Every mechanic is word-for-word the 8879's - one implementation serves both prints."},
]

F78_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-8878-NEED", "IRS_F8878", "primary", "Purpose of Form + the five-row When-and-How chart"),
    ("R-8878-NEED", "IRS_P1345_SIG", "supporting", "'Form 8878 is only needed for Forms 4868 when taxpayers are authorizing an EFW...'"),
    ("R-8878-PARTS", "IRS_F8878", "primary", "Part III title: 'Practitioner PIN Method for Form 4868 Only'"),
    ("R-8878-AMT", "IRS_F8878", "primary", "Part I check-one-box + the 4868-line-7 / 2350-line-1/-5 ties"),
    ("R-8878-MECH", "IRS_F8878", "primary", "ERO/taxpayer responsibilities + Important Notes (retention, authentication, stamps)"),
    ("R-8878-MECH", "MEF_1040_SIG", "supporting", "The header PIN elements the print mirrors (the s88 4868 jurat ladder)"),
]

F78_LINES: list[dict] = [
    {"line_number": "SID", "description": "Submission Identification Number for the extension (post-filing, or associate Form 9325)", "line_type": "input", "source_facts": ["sid"], "sort_order": 1},
    {"line_number": "1", "description": "Part I box 1 + line 1 - Form 4868; amount paying from 4868 line 7 (whole dollars)", "line_type": "calculated", "source_facts": ["amount_paying_l7"], "source_rules": ["R-8878-AMT"], "sort_order": 2},
    {"line_number": "2A", "description": "Part I line 2a - Form 2350 extension-until date (2350 line 1) - APP BOUNDARY", "line_type": "input", "source_rules": ["R-8878-AMT"], "sort_order": 3},
    {"line_number": "2B", "description": "Part I line 2b - amount paying from 2350 line 5 - APP BOUNDARY", "line_type": "input", "source_rules": ["R-8878-AMT"], "sort_order": 4},
    {"line_number": "TP_AUTH_BOX", "description": "Part II taxpayer PIN choice (authorize-ERO vs I-will-enter; check ONE)", "line_type": "input", "source_facts": ["primary_pin_entered_by"], "sort_order": 5},
    {"line_number": "TP_PIN", "description": "Part II taxpayer 5-digit PIN (never all zeros)", "line_type": "input", "source_facts": ["primary_pin"], "source_rules": ["R-8878-MECH"], "sort_order": 6},
    {"line_number": "TP_SIGN_DT", "description": "Taxpayer signature + date (BEFORE the extension transmits)", "line_type": "input", "source_facts": ["primary_signed_date"], "source_rules": ["R-8878-MECH"], "sort_order": 7},
    {"line_number": "SP_AUTH_BOX", "description": "Part II spouse PIN choice (MFJ)", "line_type": "input", "source_facts": ["spouse_pin_entered_by"], "sort_order": 8},
    {"line_number": "SP_PIN", "description": "Part II spouse 5-digit PIN", "line_type": "input", "source_facts": ["spouse_pin"], "source_rules": ["R-8878-MECH"], "sort_order": 9},
    {"line_number": "SP_SIGN_DT", "description": "Spouse signature + date (MFJ)", "line_type": "input", "source_facts": ["spouse_signed_date"], "sort_order": 10},
    {"line_number": "ERO_EFINPIN", "description": "Part III - ERO's EFIN/PIN (4868 + Practitioner PIN method ONLY; a 2350 never reaches Part III)", "line_type": "calculated", "source_facts": ["ero_efin", "ero_self_selected_pin"], "source_rules": ["R-8878-PARTS"], "sort_order": 11},
    {"line_number": "ERO_SIGN_DT", "description": "Part III - ERO signature + date", "line_type": "input", "source_facts": ["ero_signed_date"], "sort_order": 12},
    {"line_number": "CALC_NEED", "description": "Computed need-gate (EFW AND (PP OR ERO-entered) for the 4868; ERO-entered for the 2350)", "line_type": "calculated", "source_rules": ["R-8878-NEED"], "sort_order": 13},
]

F78_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_8878_NEED", "title": "Form 8878 required for this extension", "severity": "warning",
     "condition": "4868 with EFW elected and (PP method or ERO-entered PIN); or 2350 with ERO-entered PIN",
     "message": "This extension needs a Form 8878: the 4868 carries an electronic funds withdrawal and the signature comes through the ERO (Practitioner PIN method, or an ERO-entered/generated PIN). Print it, obtain the taxpayer signature(s) BEFORE transmitting the extension, and retain it 3 years - never mailed to the IRS.", "notes": "W3."},
    {"diagnostic_id": "D_8878_NOEFW", "title": "No EFW - no 8878 (and no signature at all)", "severity": "info",
     "condition": "4868 without an EFW election",
     "message": "A Form 4868 without an electronic funds withdrawal never needs a Form 8878 (chart row 2) - the e-filed extension itself carries no signature at all in that case (R0000-098, the s88 4868 unit). The 8878 requirement switches on ONLY with the EFW election.", "notes": "W3. The load-bearing negative."},
    {"diagnostic_id": "D_8878_UNSIGNED", "title": "8878 not signed - extension transmission blocked", "severity": "error",
     "condition": "f8878_needed and a required signed date is missing at extract/transmit",
     "message": "The ERO must receive the completed, signed Form 8878 from the taxpayer before the application for extension of time to file is transmitted (or released for transmission). Record the signature date(s) first.", "notes": "W3. Same extract-refusal recommendation as the 8879 (walk seam 3)."},
    {"diagnostic_id": "D_8878_ONEBOX", "title": "Check only one box in Part I", "severity": "error",
     "condition": "both the 4868 and 2350 boxes indicated",
     "message": "Part I authorizes exactly ONE extension form - check the Form 4868 box or the Form 2350 box, never both. (In tts only the 4868 path is live; the 2350 is out of scope.)", "notes": "W3."},
    {"diagnostic_id": "D_8878_L7TIE", "title": "Part I line 1 must equal Form 4868 line 7", "severity": "error",
     "condition": "printed line 1 differs from the 4868's computed line 7",
     "message": "Form 8878 Part I line 1 carries 'the amount you are paying from Form 4868, line 7' - it must match the 4868 the taxpayer is authorizing (the s88 unit's line 7, derived from components, override-respecting). Recompute or correct the authorization.", "notes": "W3. The cross-form tie the FA pins."},
    {"diagnostic_id": "D_8878_NOTEXT", "title": "The 8878 is not the extension", "severity": "info",
     "condition": "informational",
     "message": "Form 8878 isn't an application for an extension of time to file (face caution) - it only authorizes the e-filed Form 4868's signature and EFW. The 4868 itself must still be filed by the deadline.", "notes": "W3."},
    {"diagnostic_id": "D_8878_YEARWATCH", "title": "Year-dated face - verify the revision each season", "severity": "info",
     "condition": "informational at template update",
     "message": "Unlike the continuous-use 8879 (Rev. 01-2021), Form 8878 is YEAR-DATED - the Part II jurat embeds 'tax year ending December 31, 2025' verbatim. Pull the new-year face when published (the s48 face-drift class) before the next filing season.", "notes": "W4. Year-watch register, f8879_8878_source_brief.md."},
]

F78_SCENARIOS: list[dict] = [
    {"scenario_name": "8878-A - 4868 + EFW + Practitioner PIN: Parts I, II, III", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"extension_form": "4868", "efw_elected": True, "pin_method": "practitioner",
                "primary_pin_entered_by": "ero", "amount_paying_l7": 3500},
     "expected_outputs": {"f8878_needed": True, "f8878_parts": ["I", "II", "III"], "part1_line1": 3500},
     "notes": "Chart row 5 - the house case when an extension pays by EFW; line 1 ties to the s88 4868's line 7."},
    {"scenario_name": "8878-B - 4868 with NO EFW: no 8878, ever", "scenario_type": "edge", "sort_order": 2,
     "inputs": {"extension_form": "4868", "efw_elected": False, "pin_method": "practitioner", "primary_pin_entered_by": "ero"},
     "expected_outputs": {"f8878_needed": False, "diagnostic": "D_8878_NOEFW"},
     "notes": "Chart row 2 beats every other condition - even the PP method + ERO-entered PIN. The print mirror of R0000-098 (a no-payment e-filed 4868 carries no signature at all)."},
    {"scenario_name": "8878-C - 4868 + EFW + taxpayer keys own PIN + non-PP: no 8878", "scenario_type": "edge", "sort_order": 3,
     "inputs": {"extension_form": "4868", "efw_elected": True, "pin_method": "self_select_practitioner", "primary_pin_entered_by": "taxpayer"},
     "expected_outputs": {"f8878_needed": False},
     "notes": "Chart row 1 - the self-select + own-PIN skip, same shape as the 8879's only skip row."},
    {"scenario_name": "8878-D - 4868 + EFW + ERO enters + non-PP: Parts I and II", "scenario_type": "normal", "sort_order": 4,
     "inputs": {"extension_form": "4868", "efw_elected": True, "pin_method": "self_select_practitioner", "primary_pin_entered_by": "ero"},
     "expected_outputs": {"f8878_needed": True, "f8878_parts": ["I", "II"]},
     "notes": "Chart row 3 - and the non-PP + EFW combination pulls the prior-year DOB/AGI/PIN authentication requirement."},
    {"scenario_name": "8878-E - 2350 + ERO enters: Parts I and II, NEVER Part III", "scenario_type": "edge", "sort_order": 5,
     "inputs": {"extension_form": "2350", "efw_elected": False, "pin_method": "practitioner", "primary_pin_entered_by": "ero"},
     "expected_outputs": {"f8878_needed": True, "f8878_parts": ["I", "II"]},
     "notes": "Chart row 4 + the Part III 'Form 4868 Only' title: even under the PP method a 2350 authorization stops at Part II. APP BOUNDARY - encoded, not built."},
    {"scenario_name": "8878-F - line 1 diverges from the 4868's line 7: blocked", "scenario_type": "failure", "sort_order": 6,
     "inputs": {"extension_form": "4868", "efw_elected": True, "pin_method": "practitioner",
                "amount_paying_l7": 3500, "printed_line1": 3000},
     "expected_outputs": {"diagnostic": "D_8878_L7TIE"},
     "notes": "The authorization must carry the 4868's own line 7 - a stale print after a recompute is the failure mode (the s88 CIRCULAR-DERIVE class made line 7 override-respecting; the 8878 snapshot must follow it)."},
]

FORMS: list[dict] = [
    {
        "identity": {"form_number": "8879", "form_title": "Form 8879 (Rev. 01-2021) - IRS e-file Signature Authorization",
                     "notes": "WO-33 (tts s90). ERO-RETAINED print artifact - NO MeF document (the Return Header PIN block is the transmitted signature; ATS-proven). Required iff the Practitioner PIN method is used OR the ERO enters/generates any taxpayer PIN (the 4-row chart; the only skip = self-select + taxpayer keys own). Parts I (whole-dollar AGI/total tax/withholding/refund/owed off the 1040 face; 1040-SS = line 4 only, app boundary; 1040-X column-C arm) / II (declaration + PIN boxes + signatures) / III (PP rows only: EFIN+PIN). Mechanics: 5-digit non-zero PINs; sign BEFORE transmit; SID-after-filing or Form 9325; 3-year retention (Rev. Proc. 97-22); MFJ split authorization / absent-spouse bar; corrected copy + the Pub-1345 $50/$14 re-sign tolerance; 3-day stockpiling clock; non-PP prior-year ORIGINALLY-FILED authentication; under-16 + duplicate-SSN self-select bars. Covers original AND amended, TY2019+. entity_types ['1040']."},
        "facts": F79_FACTS, "rules": F79_RULES, "rule_links": F79_RULE_LINKS,
        "lines": F79_LINES, "diagnostics": F79_DIAGNOSTICS, "scenarios": F79_SCENARIOS,
    },
    {
        "identity": {"form_number": "8878", "form_title": "Form 8878 (2025) - IRS e-file Signature Authorization for Form 4868 or Form 2350",
                     "notes": "WO-33 (tts s90). ERO-RETAINED print artifact - NO MeF document. The gate: 4868 -> EFW elected AND (PP method OR ERO enters/generates); NO EFW -> NO 8878 ever (the print mirror of the s88 R0000-098 no-payment-no-signature story). 2350 -> ERO enters/generates (Parts I+II; Part III is 'Practitioner PIN Method for Form 4868 Only' - a 2350 NEVER reaches it; 2350 = app boundary). Part I: check ONE box; line 1 = the 4868's line 7 verbatim (the s88 unit's derived line). All other mechanics identical to the 8879 (PIN hygiene, sign-before-transmit, SID/9325, 3-year retention, MFJ split, corrected copy, non-PP prior-year authentication). YEAR-DATED face (2025) - year-watch; the 8879 is continuous-use. entity_types ['1040']."},
        "facts": F78_FACTS, "rules": F78_RULES, "rule_links": F78_RULE_LINKS,
        "lines": F78_LINES, "diagnostics": F78_DIAGNOSTICS, "scenarios": F78_SCENARIOS,
    },
]

# ACTIVE - the tts build leg shipped (s94, tts `0346354`), so the FAs are activated
# alongside the runner _run_8879_8878_assertion in the same tts commit.
FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-8879-NEED", "title": "8879 emission matches the chart + the header PIN data", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "active", "sort_order": 1,
     "description": "The printed 8879 exists iff pin_method == 'practitioner' or any PINEnteredByCd == ERO - and Part III fills iff the PP method. Pins: (practitioner, taxpayer-entered) -> printed w/ Part III (the counter-intuitive row 4); (self_select_practitioner, taxpayer-entered) -> NOT printed; (self_select_practitioner, ero-entered) -> printed, Parts I-II only.",
     "definition": {"rule": "R-8879-NEED", "check": "f8879_needed == (pin_method == 'practitioner' or 'ero' in entered_by set); parts include 'III' iff practitioner"}},
    {"assertion_id": "FA-8879-RESIGN", "title": "The $50/$14 re-sign tolerance against the signed-at snapshot", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "active", "sort_order": 2,
     "description": "Post-signing recompute deltas: AGI +50 / tax-family +14 -> NO new signature (at the tolerance exactly); AGI +51 or tax-family +15 -> new 8879 required. The live return compares against the SIGNED-AT Part I snapshot, never against itself.",
     "definition": {"rule": "R-8879-RESIGN", "check": "resign iff abs(delta_income_or_agi) > 50 or abs(delta_tax_family) > 14"}},
    {"assertion_id": "FA-8878-EFW", "title": "8878 emission: EFW-gated for the 4868; line 1 == 4868 line 7", "assertion_type": "reconciliation",
     "entity_types": ["1040"], "status": "active", "sort_order": 3,
     "description": "A 4868 without an EFW election prints NO 8878 regardless of PIN method (the s88 R0000-098 mirror); with EFW + (PP or ERO-entered) it prints, and Part I line 1 equals the 4868's computed line 7 (the override-respecting s88 derivation). Pins: (4868, no-EFW, practitioner, ero) -> none; (4868, EFW, practitioner) -> printed w/ Part III, line1 == L7; (2350, ero) -> printed, Parts I-II only.",
     "definition": {"rule": "R-8878-NEED", "check": "f8878_needed per the 5-row chart; part1_line1 == f4868_line7"}},
]


class Command(BaseCommand):
    help = "Load the 8879/8878 signature-authorization pair spec. Refuses to seed until READY_TO_SEED=True (Gate-1 W1-W4)."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad the 8879 / 8878 signature-authorization pair spec\n"))
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
                "\nREFUSING TO SEED THE 8879/8878 PAIR: not cleared.\n\n"
                "Gated until Ken approves the Gate-1 walk (W1 the 8879 need-gate + Part I;\n"
                "W2 signature mechanics incl. the $50/$14 tolerance + the self-select bars;\n"
                "W3 the 8878 EFW gate + the 4868-line-7 tie + the 2350 boundary; W4 ties +\n"
                "print-only-by-design + the extract-gating recommendation) and flips the sentinel.\n\n"
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
                self.stdout.write(self.style.WARNING(f"  (existing source {code} not in this DB - links to it will skip)"))
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
        self.stdout.write(f"  {len(FLOW_ASSERTIONS)} flow assertions (staged DRAFT - the tts leg activates)")

    def _report(self):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("8879 / 8878 pair loaded.")
        self.stdout.write(f"  8879: facts {len(F79_FACTS)} / rules {len(F79_RULES)} / lines {len(F79_LINES)} / diag {len(F79_DIAGNOSTICS)} / tests {len(F79_SCENARIOS)}")
        self.stdout.write(f"  8878: facts {len(F78_FACTS)} / rules {len(F78_RULES)} / lines {len(F78_LINES)} / diag {len(F78_DIAGNOSTICS)} / tests {len(F78_SCENARIOS)}")
        self.stdout.write(f"  FA {len(FLOW_ASSERTIONS)}")
        self.stdout.write("=" * 60)
